from __future__ import annotations

import getpass
import asyncio
import hashlib
import json
import os
import threading
import time
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from psycopg import errors
from psycopg.conninfo import conninfo_to_dict, make_conninfo
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver


ROOT = Path(__file__).resolve().parents[2]
SEGMENTS = (
    "00-foundation",
    "10-site",
    "20-iam",
    "30-chat",
    "40-agent",
    "45-langgraph-checkpointer",
    "50-capability",
    "60-model",
    "99-cross-capability-relations",
)

SITE_ID = "10000000-0000-0000-0000-000000000001"
PRINCIPAL_ID = "20000000-0000-0000-0000-000000000001"
ORG_ID = "30000000-0000-0000-0000-000000000001"
RUN_ID = "70000000-0000-0000-0000-000000000001"
RUN_2_ID = "70000000-0000-0000-0000-000000000002"
MANIFEST_ID = "71000000-0000-0000-0000-000000000001"
SNAPSHOT_ID = "72000000-0000-0000-0000-000000000001"
PROVIDER_ID = "73000000-0000-0000-0000-000000000001"
MODEL_ID = "74000000-0000-0000-0000-000000000001"
DRAFT_REVISION_ID = "75000000-0000-0000-0000-000000000001"
PUBLISHED_REVISION_ID = "75000000-0000-0000-0000-000000000002"
POLICY_ID = "76000000-0000-0000-0000-000000000001"


def _admin_url() -> str:
    return os.environ.get(
        "KOKORO_LOCAL_POSTGRES_ADMIN_URL",
        f"postgresql://{getpass.getuser()}@127.0.0.1:5432/postgres",
    )


def _database_url(admin_url: str, database: str) -> str:
    parts = conninfo_to_dict(admin_url)
    parts["dbname"] = database
    return make_conninfo(**parts)


@pytest.fixture
def database_url() -> Iterator[str]:
    admin_url = _admin_url()
    database = f"kokoro_agent_{uuid4().hex[:12]}"
    try:
        with psycopg.connect(admin_url, autocommit=True) as connection:
            version = connection.execute("SHOW server_version_num").fetchone()[0]
            assert int(version) // 10000 == 18
            connection.execute(f'CREATE DATABASE "{database}"')
    except psycopg.OperationalError as exc:
        pytest.fail(f"native PostgreSQL 18 is required for local backend tests: {exc}")

    url = _database_url(admin_url, database)
    try:
        with psycopg.connect(url, autocommit=True) as connection:
            for segment in SEGMENTS:
                path = ROOT / "database/schema" / f"{segment}.sql"
                if path.exists():
                    connection.execute(path.read_text())
        yield url
    finally:
        with psycopg.connect(admin_url, autocommit=True) as connection:
            connection.execute(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname=%s",
                (database,),
            )
            connection.execute(f'DROP DATABASE IF EXISTS "{database}"')


def _seed_tenant(connection: psycopg.Connection[tuple[object, ...]]) -> None:
    connection.execute(
        """
        INSERT INTO site_site(site_id,key,name,status,default_locale,timezone)
        VALUES (%s,'site-a','Site A','active','en-US','UTC')
        ON CONFLICT DO NOTHING
        """,
        (SITE_ID,),
    )
    connection.execute(
        """
        INSERT INTO iam_principal(principal_id,principal_scope,site_id,kind,status)
        VALUES (%s,'site',%s,'user','active') ON CONFLICT DO NOTHING
        """,
        (PRINCIPAL_ID, SITE_ID),
    )
    connection.execute(
        """
        INSERT INTO iam_organization(
          organization_id,site_id,kind,personal_owner_principal_id,name,status
        ) VALUES (%s,%s,'personal',%s,'Owner','active') ON CONFLICT DO NOTHING
        """,
        (ORG_ID, SITE_ID, PRINCIPAL_ID),
    )


def _seed_published_model(
    connection: psycopg.Connection[tuple[object, ...]],
    *,
    revision_id: str = PUBLISHED_REVISION_ID,
) -> None:
    connection.execute(
        """
        INSERT INTO model_provider(provider_id,key,display_name,status,generation)
        VALUES (%s,'litellm-default','LiteLLM Default','active',1)
        """,
        (PROVIDER_ID,),
    )
    connection.execute(
        """
        INSERT INTO model_definition(model_id,key,display_name,status,generation)
        VALUES (%s,'default','Default','active',1)
        """,
        (MODEL_ID,),
    )
    connection.execute(
        """
        INSERT INTO model_revision(
          model_revision_id,model_id,revision,provider_id,provider_model_name,
          transport,modalities,context_window,published_at
        ) VALUES (%s,%s,1,%s,'published','litellm','["text"]',8192,now())
        """,
        (revision_id, MODEL_ID, PROVIDER_ID),
    )


def _insert_run(
    connection: psycopg.Connection[tuple[object, ...]],
    run_id: str = RUN_ID,
    *,
    launch_id: str | None = None,
    state: str = "preparing",
) -> None:
    connection.execute(
        """
        INSERT INTO agent_run(
          agent_run_id,launch_id,launch_request_digest,namespace,state
        ) VALUES (%s,%s,decode('aa','hex'),'org/a',%s)
        """,
        (run_id, launch_id or str(uuid4()), state),
    )


def _append_event(
    connection: psycopg.Connection[tuple[object, ...]],
    *,
    run_id: str = RUN_ID,
    epoch: int,
    seq: int,
) -> None:
    connection.execute(
        "UPDATE agent_run SET next_event_seq=%s WHERE agent_run_id=%s",
        (seq + 1, run_id),
    )
    connection.execute(
        """
        INSERT INTO agent_event_outbox(
          event_id,agent_run_id,epoch,seq,kind,schema_version,payload
        ) VALUES (%s,%s,%s,%s,'run.progress',1,'{}')
        """,
        (str(uuid4()), run_id, epoch, seq),
    )


def _publish_event(
    connection: psycopg.Connection[tuple[object, ...]],
    *,
    run_id: str = RUN_ID,
    seq: int,
) -> None:
    connection.execute(
        """
        UPDATE agent_event_outbox SET published_at=now()
        WHERE agent_run_id=%s AND seq=%s
        """,
        (run_id, seq),
    )


def test_exact_agent_capability_model_and_checkpointer_catalog(database_url: str) -> None:
    expected = {
        "agent_run", "agent_execution_manifest", "agent_run_lease",
        "agent_control_inbox", "agent_event_outbox", "agent_dispatch_outbox",
        "agent_projection_ack", "agent_tool_effect", "agent_run_usage",
        "agent_run_usage_line", "agent_sandbox_binding", "agent_memory",
        "agent_dispatch_dlq", "capability_runtime_snapshot",
        "capability_command_receipt", "model_provider", "model_definition",
        "model_revision", "model_routing_policy", "model_provider_health_state",
        "checkpoints", "checkpoint_blobs", "checkpoint_writes",
        "checkpoint_migrations",
    }
    with psycopg.connect(database_url) as connection:
        actual = {
            row[0]
            for row in connection.execute(
                """
                SELECT tablename FROM pg_tables
                WHERE schemaname='kokoro'
                  AND (tablename LIKE 'agent_%'
                    OR tablename LIKE 'capability_%'
                    OR tablename LIKE 'model_%'
                    OR tablename LIKE 'checkpoint%')
                """
            )
        }
        event_constraints = "\n".join(
            row[0]
            for row in connection.execute(
                """
                SELECT pg_get_constraintdef(oid)
                FROM pg_constraint
                WHERE conrelid='kokoro.agent_event_outbox'::regclass
                """
            )
        )
    assert actual == expected
    assert "UNIQUE (agent_run_id, seq)" in event_constraints

    manifest = json.loads((ROOT / "database/slices/slice-a.json").read_text())
    manifest_tables = {
        table for tables in manifest["tables"].values() for table in tables
    }
    with psycopg.connect(database_url) as connection:
        all_tables = {
            row[0]
            for row in connection.execute(
                "SELECT tablename FROM pg_tables WHERE schemaname='kokoro'"
            )
        }
    assert all_tables == manifest_tables
    assert len(all_tables) == manifest["ownerTableCount"] + manifest["checkpointerTableCount"]


def _checkpointer_signature(
    database_url: str,
) -> tuple[
    list[tuple[object, ...]],
    list[tuple[object, ...]],
    list[tuple[object, ...]],
    list[int],
]:
    with psycopg.connect(database_url) as connection:
        columns = list(
            connection.execute(
                """
                SELECT table_name,column_name,data_type,is_nullable,column_default,ordinal_position
                FROM information_schema.columns
                WHERE table_schema='kokoro' AND table_name LIKE 'checkpoint%'
                ORDER BY table_name,ordinal_position
                """
            )
        )
        migrations = [
            row[0]
            for row in connection.execute(
                "SELECT v FROM kokoro.checkpoint_migrations ORDER BY v"
            )
        ]
        constraints = list(
            connection.execute(
                """
                SELECT c.relname,con.conname,pg_get_constraintdef(con.oid)
                FROM pg_constraint con
                JOIN pg_class c ON c.oid=con.conrelid
                JOIN pg_namespace n ON n.oid=c.relnamespace
                WHERE n.nspname='kokoro' AND c.relname LIKE 'checkpoint%'
                ORDER BY c.relname,con.conname
                """
            )
        )
        indexes = list(
            connection.execute(
                """
                SELECT tablename,indexname,indexdef
                FROM pg_indexes
                WHERE schemaname='kokoro' AND tablename LIKE 'checkpoint%'
                ORDER BY tablename,indexname
                """
            )
        )
    return columns, constraints, indexes, migrations


def test_checkpointer_segment_matches_pinned_3_1_0_setup(database_url: str) -> None:
    admin_url = _admin_url()
    official_database = f"kokoro_lg_official_{uuid4().hex[:12]}"
    with psycopg.connect(admin_url, autocommit=True) as connection:
        connection.execute(f'CREATE DATABASE "{official_database}"')
    official_url = _database_url(admin_url, official_database)

    async def setup_official() -> None:
        with psycopg.connect(official_url, autocommit=True) as connection:
            connection.execute("CREATE SCHEMA kokoro")
        configured_url = official_url + " options=-csearch_path=kokoro,pg_catalog"
        async with AsyncPostgresSaver.from_conn_string(configured_url) as saver:
            await saver.setup()

    try:
        asyncio.run(setup_official())
        assert _checkpointer_signature(database_url) == _checkpointer_signature(official_url)
    finally:
        with psycopg.connect(admin_url, autocommit=True) as connection:
            connection.execute(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname=%s",
                (official_database,),
            )
            connection.execute(f'DROP DATABASE IF EXISTS "{official_database}"')


def test_vendor_checkpointer_evidence_is_byte_identical_and_hash_fenced() -> None:
    vendor = ROOT / "database/vendor/langgraph-checkpoint-postgres-3.1.0.sql"
    segment = ROOT / "database/schema/45-langgraph-checkpointer.sql"
    assert vendor.read_bytes() == segment.read_bytes()
    lines = vendor.read_bytes().splitlines(keepends=True)
    declared = lines[0].decode().removeprefix("-- Normalized body SHA-256: ").strip()
    assert hashlib.sha256(b"".join(lines[1:])).hexdigest() == declared


def test_launch_identity_is_unique_and_manifest_is_required_before_queued(
    database_url: str,
) -> None:
    launch_id = str(uuid4())
    with psycopg.connect(database_url) as connection:
        _insert_run(connection, launch_id=launch_id)
        with pytest.raises(errors.UniqueViolation):
            connection.execute(
                """
                INSERT INTO agent_run(
                  agent_run_id,launch_id,launch_request_digest,namespace,state
                ) VALUES (%s,%s,decode('bb','hex'),'org/a','preparing')
                """,
                (RUN_2_ID, launch_id),
            )
        connection.rollback()

        _insert_run(connection, run_id=RUN_2_ID)
        connection.execute(
            "UPDATE agent_run SET state='queued' WHERE agent_run_id=%s",
            (RUN_2_ID,),
        )
        with pytest.raises(errors.CheckViolation):
            connection.commit()


def test_control_command_uniqueness_preserves_the_first_claim(database_url: str) -> None:
    command_id = str(uuid4())
    with psycopg.connect(database_url) as connection:
        _insert_run(connection)
        connection.execute(
            """
            INSERT INTO agent_control_inbox(
              control_id,agent_run_id,command_id,request_digest,
              command_schema_version,command_payload,status
            ) VALUES (%s,%s,%s,decode('aa','hex'),1,'{"control_kind":"cancel"}','pending')
            """,
            (str(uuid4()), RUN_ID, command_id),
        )
        connection.commit()
        with pytest.raises(errors.UniqueViolation):
            connection.execute(
                """
                INSERT INTO agent_control_inbox(
                  control_id,agent_run_id,command_id,request_digest,
                  command_schema_version,command_payload,status
                ) VALUES (%s,%s,%s,decode('bb','hex'),1,'{"control_kind":"cancel"}','pending')
                """,
                (str(uuid4()), RUN_ID, command_id),
            )
        connection.rollback()
        row = connection.execute(
            """
            SELECT encode(request_digest,'hex'),status
            FROM agent_control_inbox
            WHERE agent_run_id=%s AND command_id=%s
            """,
            (RUN_ID, command_id),
        ).fetchone()
        assert row == ("aa", "pending")


def test_control_claim_persists_an_immutable_canonical_command_body(
    database_url: str,
) -> None:
    command_id = str(uuid4())
    control_id = str(uuid4())
    canonical_body = {
        "control_kind": "decide",
        "decisions": [
            {"target_id": "tool-1", "kind": "approve", "payload": {}}
        ],
    }
    with psycopg.connect(database_url) as connection:
        _insert_run(connection)
        connection.execute(
            """
            INSERT INTO agent_control_inbox(
              control_id,agent_run_id,command_id,request_digest,
              command_schema_version,command_payload,interrupt_fingerprint,status
            ) VALUES (%s,%s,%s,decode('aa','hex'),1,%s,
                      decode(repeat('bb',32),'hex'),'pending')
            """,
            (control_id, RUN_ID, command_id, json.dumps(canonical_body)),
        )
        stored = connection.execute(
            """
            SELECT command_schema_version,command_payload,
                   encode(interrupt_fingerprint,'hex')
            FROM agent_control_inbox WHERE control_id=%s
            """,
            (control_id,),
        ).fetchone()
        assert stored == (1, canonical_body, "bb" * 32)

    with psycopg.connect(database_url) as connection:
        with pytest.raises(errors.CheckViolation):
            connection.execute(
                """
                UPDATE agent_control_inbox
                SET command_payload='{"control_kind":"cancel"}'::jsonb
                WHERE control_id=%s
                """,
                (control_id,),
            )

    for mutation in (
        "command_schema_version=2",
        "command_payload='{}'::jsonb",
        "interrupt_fingerprint=NULL",
    ):
        with psycopg.connect(database_url) as connection:
            with pytest.raises(errors.CheckViolation):
                connection.execute(
                    f"UPDATE agent_control_inbox SET {mutation} WHERE control_id=%s",
                    (control_id,),
                )


@pytest.mark.parametrize(
    ("schema_version", "payload"),
    [(0, {}), (1, []), (1, {"body": "x" * 65537})],
)
def test_control_claim_rejects_an_invalid_or_unbounded_command_body(
    database_url: str,
    schema_version: int,
    payload: object,
) -> None:
    with psycopg.connect(database_url) as connection:
        _insert_run(connection)
        with pytest.raises(errors.CheckViolation):
            connection.execute(
                """
                INSERT INTO agent_control_inbox(
                  control_id,agent_run_id,command_id,request_digest,
                  command_schema_version,command_payload,status
                ) VALUES (%s,%s,%s,decode('aa','hex'),%s,%s,'pending')
                """,
                (str(uuid4()), RUN_ID, str(uuid4()), schema_version, json.dumps(payload)),
            )


@pytest.mark.parametrize("fingerprint_size", [0, 31, 33])
def test_control_claim_rejects_a_non_sha256_interrupt_fingerprint(
    database_url: str,
    fingerprint_size: int,
) -> None:
    with psycopg.connect(database_url) as connection:
        _insert_run(connection)
        with pytest.raises(errors.CheckViolation):
            connection.execute(
                """
                INSERT INTO agent_control_inbox(
                  control_id,agent_run_id,command_id,request_digest,
                  command_schema_version,command_payload,interrupt_fingerprint,status
                ) VALUES (%s,%s,%s,decode('aa','hex'),1,
                          '{"control_kind":"decide"}',%s,'pending')
                """,
                (str(uuid4()), RUN_ID, str(uuid4()), b"x" * fingerprint_size),
            )


def test_event_sequence_is_run_global_and_epoch_fenced(database_url: str) -> None:
    with psycopg.connect(database_url) as connection:
        _insert_run(connection)
        for seq in range(1, 11):
            connection.execute(
                "UPDATE agent_run SET next_event_seq=%s WHERE agent_run_id=%s",
                (seq + 1, RUN_ID),
            )
            connection.execute(
                """
                INSERT INTO agent_event_outbox(
                  event_id,agent_run_id,epoch,seq,kind,schema_version,payload
                ) VALUES (%s,%s,1,%s,'run.progress',1,'{}')
                """,
                (str(uuid4()), RUN_ID, seq),
            )
        connection.execute("UPDATE agent_run SET epoch=2,next_event_seq=12 WHERE agent_run_id=%s", (RUN_ID,))
        connection.execute(
            """
            INSERT INTO agent_event_outbox(
              event_id,agent_run_id,epoch,seq,kind,schema_version,payload
            ) VALUES (%s,%s,2,11,'run.progress',1,'{}')
            """,
            (str(uuid4()), RUN_ID),
        )
        with pytest.raises((errors.UniqueViolation, errors.CheckViolation)):
            connection.execute(
                """
                INSERT INTO agent_event_outbox(
                  event_id,agent_run_id,epoch,seq,kind,schema_version,payload
                ) VALUES (%s,%s,2,10,'run.progress',1,'{}')
                """,
                (str(uuid4()), RUN_ID),
            )
        connection.rollback()

    with psycopg.connect(database_url) as connection:
        _insert_run(connection)
        connection.execute("UPDATE agent_run SET epoch=2,next_event_seq=2 WHERE agent_run_id=%s", (RUN_ID,))
        with pytest.raises(errors.CheckViolation):
            connection.execute(
                """
                INSERT INTO agent_event_outbox(
                  event_id,agent_run_id,epoch,seq,kind,schema_version,payload
                ) VALUES (%s,%s,1,1,'run.progress',1,'{}')
                """,
                (str(uuid4()), RUN_ID),
            )


def test_event_sequence_rejects_gaps_even_in_current_epoch(database_url: str) -> None:
    with psycopg.connect(database_url) as connection:
        _insert_run(connection)
        connection.execute("UPDATE agent_run SET next_event_seq=2 WHERE agent_run_id=%s", (RUN_ID,))
        with pytest.raises(errors.CheckViolation):
            connection.execute(
                """
                INSERT INTO agent_event_outbox(
                  event_id,agent_run_id,epoch,seq,kind,schema_version,payload
                ) VALUES (%s,%s,1,2,'run.progress',1,'{}')
                """,
                (str(uuid4()), RUN_ID),
            )


def test_run_cursor_allocation_cannot_skip_values(database_url: str) -> None:
    with psycopg.connect(database_url) as connection:
        _insert_run(connection)
        with pytest.raises(errors.CheckViolation):
            connection.execute(
                "UPDATE agent_run SET next_event_seq=3 WHERE agent_run_id=%s",
                (RUN_ID,),
            )


def test_run_cursor_allocation_requires_the_event_in_the_same_transaction(
    database_url: str,
) -> None:
    with psycopg.connect(database_url) as connection:
        _insert_run(connection)
        connection.execute(
            "UPDATE agent_run SET next_event_seq=2 WHERE agent_run_id=%s",
            (RUN_ID,),
        )
        with pytest.raises(errors.CheckViolation):
            connection.commit()


def test_concurrent_run_event_allocators_commit_contiguous_sequences(
    database_url: str,
) -> None:
    with psycopg.connect(database_url) as connection:
        _insert_run(connection)
        connection.commit()

    def allocate(_: int) -> int:
        with psycopg.connect(database_url) as connection:
            row = connection.execute(
                """
                UPDATE agent_run
                SET next_event_seq=next_event_seq+1
                WHERE agent_run_id=%s
                RETURNING epoch,next_event_seq-1
                """,
                (RUN_ID,),
            ).fetchone()
            epoch, seq = int(row[0]), int(row[1])
            connection.execute(
                """
                INSERT INTO agent_event_outbox(
                  event_id,agent_run_id,epoch,seq,kind,schema_version,payload
                ) VALUES (%s,%s,%s,%s,'run.progress',1,'{}')
                """,
                (str(uuid4()), RUN_ID, epoch, seq),
            )
            connection.commit()
            return seq

    with ThreadPoolExecutor(max_workers=2) as pool:
        sequences = sorted(pool.map(allocate, range(2)))
    assert sequences == [1, 2]


@pytest.mark.parametrize(
    "mutation",
    [
        "UPDATE agent_event_outbox SET event_id=gen_random_uuid() WHERE agent_run_id=%s",
        f"UPDATE agent_event_outbox SET agent_run_id='{RUN_2_ID}' WHERE agent_run_id=%s",
        "UPDATE agent_event_outbox SET epoch=2 WHERE agent_run_id=%s",
        "UPDATE agent_event_outbox SET seq=2 WHERE agent_run_id=%s",
        "UPDATE agent_event_outbox SET kind='rewritten' WHERE agent_run_id=%s",
        "UPDATE agent_event_outbox SET schema_version=2 WHERE agent_run_id=%s",
        "UPDATE agent_event_outbox SET payload='{\"rewritten\":true}' WHERE agent_run_id=%s",
        "UPDATE agent_event_outbox SET created_at=created_at + interval '1 second' WHERE agent_run_id=%s",
    ],
)
def test_committed_event_evidence_identity_and_payload_are_immutable(
    database_url: str,
    mutation: str,
) -> None:
    with psycopg.connect(database_url) as connection:
        _insert_run(connection)
        _insert_run(connection, run_id=RUN_2_ID)
        _append_event(connection, epoch=1, seq=1)
        connection.commit()
    with psycopg.connect(database_url) as connection:
        with pytest.raises(errors.CheckViolation):
            connection.execute(mutation, (RUN_ID,))


def test_event_publish_and_ack_timestamps_only_advance_once(database_url: str) -> None:
    with psycopg.connect(database_url) as connection:
        _insert_run(connection)
        _append_event(connection, epoch=1, seq=1)
        connection.commit()
    with psycopg.connect(database_url) as connection:
        _publish_event(connection, seq=1)
        connection.commit()
    with psycopg.connect(database_url) as connection:
        with pytest.raises(errors.CheckViolation):
            connection.execute(
                "UPDATE agent_event_outbox SET published_at=NULL WHERE agent_run_id=%s",
                (RUN_ID,),
            )
    with psycopg.connect(database_url) as connection:
        connection.execute(
            """
            INSERT INTO agent_projection_ack(
              agent_run_id,consumer,projected_epoch,projected_seq
            ) VALUES (%s,'chat',1,1)
            """,
            (RUN_ID,),
        )
        connection.execute(
            "UPDATE agent_event_outbox SET acked_at=now() WHERE agent_run_id=%s",
            (RUN_ID,),
        )
        connection.commit()
    with psycopg.connect(database_url) as connection:
        with pytest.raises(errors.CheckViolation):
            connection.execute(
                "UPDATE agent_event_outbox SET acked_at=NULL WHERE agent_run_id=%s",
                (RUN_ID,),
            )


@pytest.mark.parametrize(
    "timestamps",
    [
        "now(),NULL",
        "NULL,now()",
        "now(),now()",
    ],
)
def test_event_insert_must_start_unpublished_and_unacknowledged(
    database_url: str,
    timestamps: str,
) -> None:
    with psycopg.connect(database_url) as connection:
        _insert_run(connection)
        connection.execute(
            "UPDATE agent_run SET next_event_seq=2 WHERE agent_run_id=%s",
            (RUN_ID,),
        )
        with pytest.raises(errors.CheckViolation):
            connection.execute(
                f"""
                INSERT INTO agent_event_outbox(
                  event_id,agent_run_id,epoch,seq,kind,schema_version,payload,
                  published_at,acked_at
                ) VALUES (%s,%s,1,1,'run.progress',1,'{{}}',{timestamps})
                """,
                (str(uuid4()), RUN_ID),
            )


def test_event_retention_requires_publish_ack_and_chat_watermark(
    database_url: str,
) -> None:
    with psycopg.connect(database_url) as connection:
        _insert_run(connection)
        _append_event(connection, epoch=1, seq=1)
        connection.commit()

    with psycopg.connect(database_url) as connection:
        with pytest.raises(errors.CheckViolation):
            connection.execute(
                "DELETE FROM agent_event_outbox WHERE agent_run_id=%s",
                (RUN_ID,),
            )

    with psycopg.connect(database_url) as connection:
        _publish_event(connection, seq=1)
        connection.commit()
    with psycopg.connect(database_url) as connection:
        with pytest.raises(errors.CheckViolation):
            connection.execute(
                "DELETE FROM agent_event_outbox WHERE agent_run_id=%s",
                (RUN_ID,),
            )

    with psycopg.connect(database_url) as connection:
        connection.execute(
            """
            INSERT INTO agent_projection_ack(
              agent_run_id,consumer,projected_epoch,projected_seq
            ) VALUES (%s,'chat',1,1)
            """,
            (RUN_ID,),
        )
        connection.execute(
            "UPDATE agent_event_outbox SET acked_at=now() WHERE agent_run_id=%s",
            (RUN_ID,),
        )
        connection.commit()
    with psycopg.connect(database_url) as connection:
        connection.execute(
            "DELETE FROM agent_event_outbox WHERE agent_run_id=%s",
            (RUN_ID,),
        )
        connection.commit()


def test_projection_ack_rejects_epoch_and_sequence_regression(database_url: str) -> None:
    with psycopg.connect(database_url) as connection:
        _insert_run(connection)
        for seq in range(1, 11):
            _append_event(connection, epoch=1, seq=seq)
        connection.execute("UPDATE agent_run SET epoch=2 WHERE agent_run_id=%s", (RUN_ID,))
        _append_event(connection, epoch=2, seq=11)
        _publish_event(connection, seq=11)
        connection.execute(
            """
            INSERT INTO agent_projection_ack(
              agent_run_id,consumer,projected_epoch,projected_seq
            ) VALUES (%s,'chat',2,11)
            """,
            (RUN_ID,),
        )
        with pytest.raises(errors.CheckViolation):
            connection.execute(
                """
                UPDATE agent_projection_ack SET projected_epoch=1,projected_seq=10
                WHERE agent_run_id=%s AND consumer='chat'
                """,
                (RUN_ID,),
            )


def test_projection_ack_insert_rejects_stale_epoch_and_future_sequence(
    database_url: str,
) -> None:
    with psycopg.connect(database_url) as connection:
        _insert_run(connection)
        connection.execute("UPDATE agent_run SET epoch=2 WHERE agent_run_id=%s", (RUN_ID,))
        with pytest.raises(errors.CheckViolation):
            connection.execute(
                """
                INSERT INTO agent_projection_ack(
                  agent_run_id,consumer,projected_epoch,projected_seq
                ) VALUES (%s,'chat',1,999999)
                """,
                (RUN_ID,),
            )


def test_projection_ack_requires_an_existing_run_global_event(database_url: str) -> None:
    with psycopg.connect(database_url) as connection:
        _insert_run(connection)
        with pytest.raises(errors.CheckViolation):
            connection.execute(
                """
                INSERT INTO agent_projection_ack(
                  agent_run_id,consumer,projected_epoch,projected_seq
                ) VALUES (%s,'chat',1,1)
                """,
                (RUN_ID,),
            )


def test_projection_ack_accepts_current_epoch_and_existing_sequence(
    database_url: str,
) -> None:
    with psycopg.connect(database_url) as connection:
        _insert_run(connection)
        for seq in range(1, 11):
            _append_event(connection, epoch=1, seq=seq)
        connection.execute("UPDATE agent_run SET epoch=2 WHERE agent_run_id=%s", (RUN_ID,))
        _append_event(connection, epoch=2, seq=11)
        _publish_event(connection, seq=11)
        connection.execute(
            """
            INSERT INTO agent_projection_ack(
              agent_run_id,consumer,projected_epoch,projected_seq
            ) VALUES (%s,'chat',2,11)
            """,
            (RUN_ID,),
        )
        connection.commit()


def test_projection_ack_cannot_relabel_an_old_epoch_event(database_url: str) -> None:
    with psycopg.connect(database_url) as connection:
        _insert_run(connection)
        _append_event(connection, epoch=1, seq=1)
        _publish_event(connection, seq=1)
        connection.execute("UPDATE agent_run SET epoch=2 WHERE agent_run_id=%s", (RUN_ID,))
        with pytest.raises(errors.CheckViolation):
            connection.execute(
                """
                INSERT INTO agent_projection_ack(
                  agent_run_id,consumer,projected_epoch,projected_seq
                ) VALUES (%s,'chat',2,1)
                """,
                (RUN_ID,),
            )


def test_projection_ack_rejects_an_unpublished_event(database_url: str) -> None:
    with psycopg.connect(database_url) as connection:
        _insert_run(connection)
        _append_event(connection, epoch=1, seq=1)
        with pytest.raises(errors.CheckViolation):
            connection.execute(
                """
                INSERT INTO agent_projection_ack(
                  agent_run_id,consumer,projected_epoch,projected_seq
                ) VALUES (%s,'chat',1,1)
                """,
                (RUN_ID,),
            )


@pytest.mark.parametrize("terminal", ["admission_failed", "completed", "failed", "cancelled"])
def test_terminal_run_cannot_revive(database_url: str, terminal: str) -> None:
    with psycopg.connect(database_url) as connection:
        _insert_run(connection, state=terminal)
        with pytest.raises(errors.CheckViolation):
            connection.execute("UPDATE agent_run SET state='preparing' WHERE agent_run_id=%s", (RUN_ID,))


def test_terminal_event_is_committed_before_terminal_state_in_one_transaction(
    database_url: str,
) -> None:
    with psycopg.connect(database_url) as connection:
        _insert_run(connection)
        _append_event(connection, epoch=1, seq=1)
        connection.execute(
            "UPDATE agent_run SET state='admission_failed',terminal_at=now() WHERE agent_run_id=%s",
            (RUN_ID,),
        )
        connection.commit()


def test_terminal_run_rejects_new_event_and_tool_effect_claim(database_url: str) -> None:
    with psycopg.connect(database_url) as connection:
        _insert_run(connection, state="admission_failed")
        connection.commit()

    with psycopg.connect(database_url) as connection:
        with pytest.raises(errors.CheckViolation):
            connection.execute(
                "UPDATE agent_run SET next_event_seq=2 WHERE agent_run_id=%s",
                (RUN_ID,),
            )

    with psycopg.connect(database_url) as connection:
        with pytest.raises(errors.CheckViolation):
            connection.execute(
                """
                INSERT INTO agent_tool_effect(
                  effect_id,agent_run_id,tool_call_id,effect_kind,request_digest,status
                ) VALUES (%s,%s,'late-call','http',decode('aa','hex'),'claimed')
                """,
                (str(uuid4()), RUN_ID),
            )


@pytest.mark.parametrize(
    ("source", "target"),
    [("preparing", "running"), ("queued", "awaiting_input"), ("running", "preparing")],
)
def test_run_state_machine_rejects_skipped_or_backward_transitions(
    database_url: str, source: str, target: str
) -> None:
    with psycopg.connect(database_url) as connection:
        _insert_run(connection, state=source)
        with pytest.raises(errors.CheckViolation):
            connection.execute(
                "UPDATE agent_run SET state=%s WHERE agent_run_id=%s",
                (target, RUN_ID),
            )


def test_run_usage_requires_terminal_run(database_url: str) -> None:
    with psycopg.connect(database_url) as connection:
        _insert_run(connection)
        connection.execute(
            """
            INSERT INTO agent_run_usage(
              run_usage_id,agent_run_id,digest,input_tokens,output_tokens,
              cached_tokens,call_count,finalized_at
            ) VALUES (%s,%s,decode('aa','hex'),1,2,0,1,now())
            """,
            (str(uuid4()), RUN_ID),
        )
        with pytest.raises(errors.CheckViolation):
            connection.commit()


def test_finalized_run_usage_and_lines_are_immutable(database_url: str) -> None:
    usage_id = str(uuid4())
    line_id = str(uuid4())
    with psycopg.connect(database_url) as connection:
        _seed_published_model(connection)
        _insert_run(connection, state="admission_failed")
        connection.execute(
            """
            INSERT INTO agent_run_usage(
              run_usage_id,agent_run_id,digest,input_tokens,output_tokens,
              cached_tokens,call_count,finalized_at
            ) VALUES (%s,%s,decode('aa','hex'),1,2,0,1,now())
            """,
            (usage_id, RUN_ID),
        )
        connection.execute(
            """
            INSERT INTO agent_run_usage_line(
              usage_line_id,run_usage_id,model_revision_id,feature_key,
              input_tokens,output_tokens,cached_tokens,call_count
            ) VALUES (%s,%s,%s,'chat',1,2,0,1)
            """,
            (line_id, usage_id, PUBLISHED_REVISION_ID),
        )
        connection.commit()

    mutations = (
        ("UPDATE agent_run_usage SET input_tokens=999 WHERE run_usage_id=%s", (usage_id,)),
        ("DELETE FROM agent_run_usage WHERE run_usage_id=%s", (usage_id,)),
        ("UPDATE agent_run_usage_line SET input_tokens=999 WHERE usage_line_id=%s", (line_id,)),
        ("DELETE FROM agent_run_usage_line WHERE usage_line_id=%s", (line_id,)),
    )
    for statement, parameters in mutations:
        with psycopg.connect(database_url) as connection:
            with pytest.raises(errors.CheckViolation):
                connection.execute(statement, parameters)

    with psycopg.connect(database_url) as connection:
        with pytest.raises(errors.CheckViolation):
            connection.execute(
                """
                INSERT INTO agent_run_usage_line(
                  usage_line_id,run_usage_id,model_revision_id,feature_key,
                  input_tokens,output_tokens,cached_tokens,call_count
                ) VALUES (%s,%s,%s,'subagent',3,4,0,1)
                """,
                (str(uuid4()), usage_id, PUBLISHED_REVISION_ID),
            )


def test_tool_effect_claim_identity_and_terminal_result_are_immutable(
    database_url: str,
) -> None:
    effect_id = str(uuid4())
    with psycopg.connect(database_url) as connection:
        _insert_run(connection)
        connection.execute(
            """
            INSERT INTO agent_tool_effect(
              effect_id,agent_run_id,tool_call_id,effect_kind,request_digest,status
            ) VALUES (%s,%s,'call-1','http',decode('aa','hex'),'claimed')
            """,
            (effect_id, RUN_ID),
        )
        connection.execute(
            """
            UPDATE agent_tool_effect
            SET status='completed',result_digest=decode('bb','hex')
            WHERE effect_id=%s
            """,
            (effect_id,),
        )
        connection.commit()

    mutations = (
        "UPDATE agent_tool_effect SET tool_call_id='call-2' WHERE effect_id=%s",
        "UPDATE agent_tool_effect SET request_digest=decode('cc','hex') WHERE effect_id=%s",
        "UPDATE agent_tool_effect SET status='claimed',result_digest=NULL WHERE effect_id=%s",
        "UPDATE agent_tool_effect SET result_digest=decode('dd','hex') WHERE effect_id=%s",
        "DELETE FROM agent_tool_effect WHERE effect_id=%s",
    )
    for statement in mutations:
        with psycopg.connect(database_url) as connection:
            with pytest.raises(errors.CheckViolation):
                connection.execute(statement, (effect_id,))


def test_tool_effect_reconcile_allows_unknown_to_terminal(database_url: str) -> None:
    effect_id = str(uuid4())
    with psycopg.connect(database_url) as connection:
        _insert_run(connection)
        connection.execute(
            """
            INSERT INTO agent_tool_effect(
              effect_id,agent_run_id,tool_call_id,effect_kind,request_digest,status
            ) VALUES (%s,%s,'call-1','http',decode('aa','hex'),'claimed')
            """,
            (effect_id, RUN_ID),
        )
        connection.execute(
            "UPDATE agent_tool_effect SET status='unknown' WHERE effect_id=%s",
            (effect_id,),
        )
        connection.execute(
            """
            UPDATE agent_tool_effect
            SET status='completed',result_digest=decode('bb','hex')
            WHERE effect_id=%s
            """,
            (effect_id,),
        )
        connection.commit()


def test_control_terminal_receipt_cannot_revert_or_be_deleted(database_url: str) -> None:
    control_id = str(uuid4())
    command_id = str(uuid4())
    with psycopg.connect(database_url) as connection:
        _insert_run(connection)
        connection.execute(
            """
            INSERT INTO agent_control_inbox(
              control_id,agent_run_id,command_id,request_digest,
              command_schema_version,command_payload,status
            ) VALUES (%s,%s,%s,decode('aa','hex'),1,'{"control_kind":"cancel"}','pending')
            """,
            (control_id, RUN_ID, command_id),
        )
        connection.execute(
            """
            UPDATE agent_control_inbox SET status='applied',applied_at=now()
            WHERE control_id=%s
            """,
            (control_id,),
        )
        connection.commit()

    for statement in (
        "UPDATE agent_control_inbox SET status='pending',applied_at=NULL WHERE control_id=%s",
        "DELETE FROM agent_control_inbox WHERE control_id=%s",
    ):
        with psycopg.connect(database_url) as connection:
            with pytest.raises(errors.CheckViolation):
                connection.execute(statement, (control_id,))

    with psycopg.connect(database_url) as connection:
        with pytest.raises(errors.UniqueViolation):
            connection.execute(
                """
                INSERT INTO agent_control_inbox(
                  control_id,agent_run_id,command_id,request_digest,
                  command_schema_version,command_payload,status
                ) VALUES (%s,%s,%s,decode('bb','hex'),1,'{"control_kind":"cancel"}','pending')
                """,
                (str(uuid4()), RUN_ID, command_id),
            )


@pytest.mark.parametrize("terminal_state", ["completed", "failed", "cancelled", "admission_failed"])
def test_terminal_run_rejects_a_new_control_claim(
    database_url: str,
    terminal_state: str,
) -> None:
    with psycopg.connect(database_url) as connection:
        _insert_run(connection, state=terminal_state)
        with pytest.raises(errors.CheckViolation):
            connection.execute(
                """
                INSERT INTO agent_control_inbox(
                  control_id,agent_run_id,command_id,request_digest,
                  command_schema_version,command_payload,status
                ) VALUES (%s,%s,%s,decode('aa','hex'),1,
                          '{"control_kind":"cancel"}','pending')
                """,
                (str(uuid4()), RUN_ID, str(uuid4())),
            )


def test_terminal_transition_serializes_before_a_concurrent_control_claim(
    database_url: str,
) -> None:
    with psycopg.connect(database_url) as connection:
        _insert_run(connection)
        connection.commit()

    terminal_row_locked = threading.Event()
    release_terminal = threading.Event()

    def terminalize() -> None:
        with psycopg.connect(database_url) as connection:
            connection.execute(
                "UPDATE agent_run SET state='admission_failed' WHERE agent_run_id=%s",
                (RUN_ID,),
            )
            terminal_row_locked.set()
            assert release_terminal.wait(timeout=5)
            connection.commit()

    def claim_control() -> str:
        assert terminal_row_locked.wait(timeout=5)
        with psycopg.connect(database_url) as connection:
            try:
                connection.execute(
                    """
                    INSERT INTO agent_control_inbox(
                      control_id,agent_run_id,command_id,request_digest,
                      command_schema_version,command_payload,status
                    ) VALUES (%s,%s,%s,decode('aa','hex'),1,
                              '{"control_kind":"cancel"}','pending')
                    """,
                    (str(uuid4()), RUN_ID, str(uuid4())),
                )
                connection.commit()
                return "committed"
            except errors.CheckViolation:
                connection.rollback()
                return "terminal-rejected"

    with ThreadPoolExecutor(max_workers=2) as pool:
        terminal_future = pool.submit(terminalize)
        claim_future = pool.submit(claim_control)
        assert terminal_row_locked.wait(timeout=5)
        time.sleep(0.05)
        assert not claim_future.done()
        release_terminal.set()
        terminal_future.result(timeout=5)
        assert claim_future.result(timeout=5) == "terminal-rejected"

    with psycopg.connect(database_url) as connection:
        assert connection.execute(
            "SELECT count(*) FROM agent_control_inbox WHERE agent_run_id=%s",
            (RUN_ID,),
        ).fetchone()[0] == 0


def test_control_status_and_applied_at_must_match(database_url: str) -> None:
    with psycopg.connect(database_url) as connection:
        _insert_run(connection)
        with pytest.raises(errors.CheckViolation):
            connection.execute(
                """
                INSERT INTO agent_control_inbox(
                  control_id,agent_run_id,command_id,request_digest,
                  command_schema_version,command_payload,status,applied_at
                ) VALUES (%s,%s,%s,decode('aa','hex'),1,
                          '{"control_kind":"cancel"}','pending',now())
                """,
                (str(uuid4()), RUN_ID, str(uuid4())),
            )


def test_execution_manifest_binds_run_namespace_published_model_and_snapshot(
    database_url: str,
) -> None:
    with psycopg.connect(database_url) as connection:
        _seed_tenant(connection)
        connection.execute(
            """
            INSERT INTO model_provider(provider_id,key,display_name,status,generation)
            VALUES (%s,'litellm-default','LiteLLM Default','active',1)
            """,
            (PROVIDER_ID,),
        )
        connection.execute(
            """
            INSERT INTO model_definition(model_id,key,display_name,status,generation)
            VALUES (%s,'default','Default','active',1)
            """,
            (MODEL_ID,),
        )
        connection.execute(
            """
            INSERT INTO model_revision(
              model_revision_id,model_id,revision,provider_id,provider_model_name,
              transport,modalities,context_window,published_at
            ) VALUES (%s,%s,1,%s,'published','litellm','["text"]',8192,now())
            """,
            (PUBLISHED_REVISION_ID, MODEL_ID, PROVIDER_ID),
        )
        connection.execute(
            """
            INSERT INTO capability_runtime_snapshot(
              snapshot_id,organization_id,scope_key,digest
            ) VALUES (%s,%s,'org/a',decode('aa','hex'))
            """,
            (SNAPSHOT_ID, ORG_ID),
        )
        _insert_run(connection)
        connection.execute(
            """
            INSERT INTO agent_execution_manifest(
              execution_manifest_id,agent_run_id,namespace,digest,
              agent_preset_key,agent_preset_digest,model_revision_id,
              capability_snapshot_id,usage_mode,usage_policy_digest,payload
            ) VALUES (
              %s,%s,'org/a',decode('aa','hex'),'general',decode('bb','hex'),
              %s,%s,'unmetered',decode('cc','hex'),'{}'
            )
            """,
            (MANIFEST_ID, RUN_ID, PUBLISHED_REVISION_ID, SNAPSHOT_ID),
        )
        connection.execute(
            """
            UPDATE agent_run
            SET execution_manifest_id=%s,state='queued'
            WHERE agent_run_id=%s
            """,
            (MANIFEST_ID, RUN_ID),
        )
        connection.commit()

    with psycopg.connect(database_url) as connection:
        assert connection.execute(
            "SELECT state FROM agent_run WHERE agent_run_id=%s", (RUN_ID,)
        ).fetchone()[0] == "queued"


def test_capability_empty_snapshot_converges_without_project_axis(database_url: str) -> None:
    digest = bytes.fromhex("ab" * 32)

    with psycopg.connect(database_url) as connection:
        _seed_tenant(connection)

    def insert_once() -> str:
        with psycopg.connect(database_url) as connection:
            snapshot_id = str(uuid4())
            row = connection.execute(
                """
                INSERT INTO capability_runtime_snapshot(
                  snapshot_id,organization_id,scope_key,digest
                ) VALUES (%s,%s,'org/default',%s)
                ON CONFLICT (organization_id,scope_key,digest)
                DO UPDATE SET digest=EXCLUDED.digest
                RETURNING snapshot_id
                """,
                (snapshot_id, ORG_ID, digest),
            ).fetchone()
            connection.commit()
            return str(row[0])

    with ThreadPoolExecutor(max_workers=2) as pool:
        ids = list(pool.map(lambda _: insert_once(), range(2)))
    assert ids[0] == ids[1]

    with psycopg.connect(database_url) as connection:
        columns = {
            row[0]
            for row in connection.execute(
                """
                SELECT column_name FROM information_schema.columns
                WHERE table_schema='kokoro' AND table_name='capability_runtime_snapshot'
                """
            )
        }
        assert "project_id" not in columns
        assert connection.execute(
            "SELECT to_regclass('kokoro.capability_runtime_snapshot_item')"
        ).fetchone()[0] is None


def test_model_routing_is_published_litellm_only(database_url: str) -> None:
    with psycopg.connect(database_url) as connection:
        _seed_tenant(connection)
        connection.execute(
            """
            INSERT INTO model_provider(provider_id,key,display_name,status,generation)
            VALUES (%s,'litellm-default','LiteLLM Default','active',1)
            """,
            (PROVIDER_ID,),
        )
        connection.execute(
            """
            INSERT INTO model_definition(model_id,key,display_name,status,generation)
            VALUES (%s,'default','Default','active',1)
            """,
            (MODEL_ID,),
        )
        connection.execute(
            """
            INSERT INTO model_revision(
              model_revision_id,model_id,revision,provider_id,provider_model_name,
              transport,modalities,context_window,published_at
            ) VALUES
              (%s,%s,1,%s,'draft','litellm','["text"]',8192,NULL),
              (%s,%s,2,%s,'published','litellm','["text"]',8192,now())
            """,
            (DRAFT_REVISION_ID, MODEL_ID, PROVIDER_ID, PUBLISHED_REVISION_ID, MODEL_ID, PROVIDER_ID),
        )
        connection.execute(
            """
            INSERT INTO model_routing_policy(
              routing_policy_id,site_id,label,model_revision_id,priority,status,generation
            ) VALUES (%s,%s,'default',%s,1,'active',1)
            """,
            (POLICY_ID, SITE_ID, DRAFT_REVISION_ID),
        )
        with pytest.raises(errors.CheckViolation):
            connection.commit()

    with psycopg.connect(database_url) as connection:
        _seed_tenant(connection)
        connection.execute(
            """
            INSERT INTO model_provider(provider_id,key,display_name,status,generation)
            VALUES (%s,'litellm-default','LiteLLM Default','active',1)
            """,
            (PROVIDER_ID,),
        )
        connection.execute(
            """
            INSERT INTO model_definition(model_id,key,display_name,status,generation)
            VALUES (%s,'default','Default','active',1)
            """,
            (MODEL_ID,),
        )
        connection.execute(
            """
            INSERT INTO model_revision(
              model_revision_id,model_id,revision,provider_id,provider_model_name,
              transport,modalities,context_window,published_at
            ) VALUES (%s,%s,1,%s,'published','litellm','["text"]',8192,now())
            """,
            (PUBLISHED_REVISION_ID, MODEL_ID, PROVIDER_ID),
        )
        connection.execute(
            """
            INSERT INTO model_routing_policy(
              routing_policy_id,site_id,label,model_revision_id,priority,status,generation
            ) VALUES (%s,%s,'default',%s,1,'active',1)
            """,
            (POLICY_ID, SITE_ID, PUBLISHED_REVISION_ID),
        )
        with pytest.raises(errors.CheckViolation):
            connection.execute(
                "UPDATE model_revision SET transport='direct' WHERE model_revision_id=%s",
                (PUBLISHED_REVISION_ID,),
            )


def test_provider_health_starts_unknown_without_observation_table(database_url: str) -> None:
    with psycopg.connect(database_url) as connection:
        _seed_tenant(connection)
        connection.execute(
            """
            INSERT INTO model_provider(provider_id,key,display_name,status,generation)
            VALUES (%s,'unknown-health','Unknown Health','active',1)
            """,
            (PROVIDER_ID,),
        )
        connection.execute(
            """
            INSERT INTO model_provider_health_state(provider_id,status,generation)
            VALUES (%s,'unknown',1)
            """,
            (PROVIDER_ID,),
        )
        assert connection.execute(
            "SELECT to_regclass('kokoro.model_provider_health_observation')"
        ).fetchone()[0] is None
        columns = {
            row[0]
            for row in connection.execute(
                """
                SELECT column_name FROM information_schema.columns
                WHERE table_schema='kokoro' AND table_name='model_provider_health_state'
                """
            )
        }
        assert "last_observation_id" not in columns


def test_model_current_revision_requires_published_litellm(database_url: str) -> None:
    with psycopg.connect(database_url) as connection:
        connection.execute(
            """
            INSERT INTO model_provider(provider_id,key,display_name,status,generation)
            VALUES (%s,'litellm-default','LiteLLM Default','active',1)
            """,
            (PROVIDER_ID,),
        )
        connection.execute(
            """
            INSERT INTO model_definition(model_id,key,display_name,status,generation)
            VALUES (%s,'default','Default','active',1)
            """,
            (MODEL_ID,),
        )
        connection.execute(
            """
            INSERT INTO model_revision(
              model_revision_id,model_id,revision,provider_id,provider_model_name,
              transport,modalities,context_window,published_at
            ) VALUES (%s,%s,1,%s,'draft','litellm','["text"]',8192,NULL)
            """,
            (DRAFT_REVISION_ID, MODEL_ID, PROVIDER_ID),
        )
        connection.execute(
            "UPDATE model_definition SET current_revision_id=%s WHERE model_id=%s",
            (DRAFT_REVISION_ID, MODEL_ID),
        )
        with pytest.raises(errors.CheckViolation):
            connection.commit()


def test_published_model_revision_cannot_be_deleted_but_draft_can(
    database_url: str,
) -> None:
    with psycopg.connect(database_url) as connection:
        _seed_published_model(connection)
        connection.execute(
            """
            INSERT INTO model_revision(
              model_revision_id,model_id,revision,provider_id,provider_model_name,
              transport,modalities,context_window,published_at
            ) VALUES (%s,%s,2,%s,'draft','litellm','["text"]',8192,NULL)
            """,
            (DRAFT_REVISION_ID, MODEL_ID, PROVIDER_ID),
        )
        connection.execute(
            "DELETE FROM model_revision WHERE model_revision_id=%s",
            (DRAFT_REVISION_ID,),
        )
        with pytest.raises(errors.CheckViolation):
            connection.execute(
                "DELETE FROM model_revision WHERE model_revision_id=%s",
                (PUBLISHED_REVISION_ID,),
            )
