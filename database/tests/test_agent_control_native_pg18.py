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
    kind: str = "run.progress",
    wire_metadata: bool = True,
) -> None:
    connection.execute(
        "UPDATE agent_run SET next_event_seq=%s WHERE agent_run_id=%s",
        (seq + 1, run_id),
    )
    connection.execute(
        """
        INSERT INTO agent_event_outbox(
          event_id,agent_run_id,epoch,seq,stream_index,stream_timestamp_ms,
          kind,schema_version,payload
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,1,'{}')
        """,
        (
            str(uuid4()),
            run_id,
            epoch,
            seq,
            seq - 1 if wire_metadata else None,
            1_700_000_000_000 + seq if wire_metadata else None,
            kind,
        ),
    )


def _publish_event(
    connection: psycopg.Connection[tuple[object, ...]],
    *,
    run_id: str = RUN_ID,
    seq: int,
) -> None:
    connection.execute(
        """
        UPDATE agent_event_outbox
        SET published_at=transaction_timestamp(),
            last_publish_attempt_at=transaction_timestamp(),publish_attempt=1
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
                  event_id,agent_run_id,epoch,seq,stream_index,stream_timestamp_ms,
                  kind,schema_version,payload
                ) VALUES (%s,%s,1,%s,%s,%s,'run.progress',1,'{}')
                """,
                (str(uuid4()), RUN_ID, seq, seq - 1, 1_700_000_000_000 + seq),
            )
        connection.execute("UPDATE agent_run SET epoch=2,next_event_seq=12 WHERE agent_run_id=%s", (RUN_ID,))
        connection.execute(
            """
            INSERT INTO agent_event_outbox(
              event_id,agent_run_id,epoch,seq,stream_index,stream_timestamp_ms,
              kind,schema_version,payload
            ) VALUES (%s,%s,2,11,10,1700000000011,'run.progress',1,'{}')
            """,
            (str(uuid4()), RUN_ID),
        )
        with pytest.raises((errors.UniqueViolation, errors.CheckViolation)):
            connection.execute(
                """
                INSERT INTO agent_event_outbox(
                  event_id,agent_run_id,epoch,seq,stream_index,stream_timestamp_ms,
                  kind,schema_version,payload
                ) VALUES (%s,%s,2,10,9,1700000000010,'run.progress',1,'{}')
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
                  event_id,agent_run_id,epoch,seq,stream_index,stream_timestamp_ms,
                  kind,schema_version,payload
                ) VALUES (%s,%s,1,1,0,1700000000001,'run.progress',1,'{}')
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
                  event_id,agent_run_id,epoch,seq,stream_index,stream_timestamp_ms,
                  kind,schema_version,payload
                ) VALUES (%s,%s,1,2,1,1700000000002,'run.progress',1,'{}')
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
                  event_id,agent_run_id,epoch,seq,stream_index,stream_timestamp_ms,
                  kind,schema_version,payload
                ) VALUES (%s,%s,%s,%s,%s,%s,'run.progress',1,'{}')
                """,
                (str(uuid4()), RUN_ID, epoch, seq, seq - 1, 1_700_000_000_000 + seq),
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
        "UPDATE agent_event_outbox SET stream_index=99 WHERE agent_run_id=%s",
        "UPDATE agent_event_outbox SET stream_timestamp_ms=99 WHERE agent_run_id=%s",
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


def test_event_restart_replay_preserves_exact_stream_metadata(database_url: str) -> None:
    event_id = str(uuid4())
    with psycopg.connect(database_url) as connection:
        _insert_run(connection)
        connection.execute(
            "UPDATE agent_run SET next_event_seq=2 WHERE agent_run_id=%s",
            (RUN_ID,),
        )
        connection.execute(
            """
            INSERT INTO agent_event_outbox(
              event_id,agent_run_id,epoch,seq,stream_index,stream_timestamp_ms,
              kind,schema_version,payload
            ) VALUES (%s,%s,1,1,47,1735689600123,'run.progress',1,'{}')
            """,
            (event_id, RUN_ID),
        )
        connection.commit()

    with psycopg.connect(database_url) as connection:
        assert connection.execute(
            """
            SELECT stream_index,stream_timestamp_ms
            FROM agent_event_outbox WHERE event_id=%s
            """,
            (event_id,),
        ).fetchone() == (47, 1_735_689_600_123)


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
                  event_id,agent_run_id,epoch,seq,stream_index,stream_timestamp_ms,
                  kind,schema_version,payload,
                  published_at,acked_at
                ) VALUES (%s,%s,1,1,0,1700000000001,
                          'run.progress',1,'{{}}',{timestamps})
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


def test_admission_failure_commits_without_runtime_evidence_and_replays(
    database_url: str,
) -> None:
    launch_id = str(uuid4())
    with psycopg.connect(database_url) as connection:
        _insert_run(connection, launch_id=launch_id)
        connection.execute(
            """
            UPDATE agent_run
            SET state='admission_failed',terminal_at=transaction_timestamp()
            WHERE agent_run_id=%s
            """,
            (RUN_ID,),
        )
        connection.commit()

    with psycopg.connect(database_url) as connection:
        assert connection.execute(
            """
            SELECT state,execution_manifest_id,terminal_claim_id,next_event_seq
            FROM agent_run WHERE agent_run_id=%s
            """,
            (RUN_ID,),
        ).fetchone() == ("admission_failed", None, None, 1)
        for table in (
            "agent_run_lease",
            "agent_event_outbox",
            "agent_run_usage",
        ):
            assert connection.execute(
                f"SELECT count(*) FROM {table} WHERE agent_run_id=%s",
                (RUN_ID,),
            ).fetchone()[0] == 0
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

    with psycopg.connect(database_url) as connection:
        assert connection.execute(
            "SELECT state FROM agent_run WHERE launch_id=%s",
            (launch_id,),
        ).fetchone()[0] == "admission_failed"
        with pytest.raises(errors.CheckViolation):
            connection.execute(
                """
                INSERT INTO agent_run_lease(
                  agent_run_id,worker_id,lease_token_hash,leased_until,generation
                ) VALUES (%s,'late-worker',decode(repeat('31',32),'hex'),
                          now() + interval '5 minutes',1)
                """,
                (RUN_ID,),
            )


def test_terminal_run_rejects_new_event_and_tool_effect_claim(database_url: str) -> None:
    with psycopg.connect(database_url) as connection:
        _seed_manifested_running_run(connection)
        _finalize_seeded_run(connection, terminal_state="completed")
        connection.commit()

    with psycopg.connect(database_url) as connection:
        with pytest.raises(errors.CheckViolation):
            connection.execute(
                "UPDATE agent_run SET next_event_seq=3 WHERE agent_run_id=%s",
                (RUN_ID,),
            )

    with psycopg.connect(database_url) as connection:
        with pytest.raises(errors.CheckViolation):
            connection.execute(
                """
                INSERT INTO agent_tool_effect(
                  effect_id,agent_run_id,tool_call_id,effect_kind,request_digest,status,
                  claim_epoch,claim_lease_generation
                ) VALUES (%s,%s,'late-call','http',decode('aa','hex'),'claimed',1,7)
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
            ) VALUES (%s,%s,decode(repeat('aa',32),'hex'),1,2,0,1,now())
            """,
            (str(uuid4()), RUN_ID),
        )
        with pytest.raises(errors.CheckViolation):
            connection.commit()


def test_finalized_run_usage_and_lines_are_immutable(database_url: str) -> None:
    usage_id = str(uuid4())
    line_id = str(uuid4())
    with psycopg.connect(database_url) as connection:
        _seed_manifested_running_run(connection)
        connection.execute(
            """
            UPDATE agent_run
            SET usage_input_tokens=1,usage_output_tokens=2,usage_call_count=1
            WHERE agent_run_id=%s
            """,
            (RUN_ID,),
        )
        _finalize_seeded_run(
            connection,
            terminal_state="completed",
            usage_id=usage_id,
            line_id=line_id,
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
        _seed_manifested_running_run(connection)
        connection.execute(
            """
            INSERT INTO agent_tool_effect(
              effect_id,agent_run_id,tool_call_id,effect_kind,request_digest,status,
              claim_epoch,claim_lease_generation
            ) VALUES (%s,%s,'call-1','http',decode('aa','hex'),'claimed',1,7)
            """,
            (effect_id, RUN_ID),
        )
        connection.execute(
            """
            UPDATE agent_tool_effect
            SET status='completed',result_digest=decode(repeat('bb',32),'hex'),
                result_schema_version=1,result_payload='"first"'::jsonb,
                result_is_error=false
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
        _seed_manifested_running_run(connection)
        connection.execute(
            """
            INSERT INTO agent_tool_effect(
              effect_id,agent_run_id,tool_call_id,effect_kind,request_digest,status,
              claim_epoch,claim_lease_generation
            ) VALUES (%s,%s,'call-1','http',decode('aa','hex'),'claimed',1,7)
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
            SET status='completed',result_digest=decode(repeat('bb',32),'hex'),
                result_schema_version=1,result_payload='"reconciled"'::jsonb,
                result_is_error=true
            WHERE effect_id=%s
            """,
            (effect_id,),
        )
        connection.commit()


def test_tool_journal_interrupt_clear_allows_the_same_call_to_reclaim(
    database_url: str,
) -> None:
    with psycopg.connect(database_url) as connection:
        _seed_manifested_running_run(connection)
        first_effect_id = str(uuid4())
        connection.execute(
            """
            INSERT INTO agent_tool_effect(
              effect_id,agent_run_id,tool_call_id,tool_name,effect_kind,request_digest,status,
              claim_epoch,claim_lease_generation
            ) VALUES (%s,%s,'interrupt-call','search','tool_journal',
                      decode(repeat('aa',32),'hex'),'claimed',1,7)
            """,
            (first_effect_id, RUN_ID),
        )
        connection.execute(
            "DELETE FROM agent_tool_effect WHERE effect_id=%s",
            (first_effect_id,),
        )
        second_effect_id = str(uuid4())
        connection.execute(
            """
            INSERT INTO agent_tool_effect(
              effect_id,agent_run_id,tool_call_id,tool_name,effect_kind,request_digest,status,
              claim_epoch,claim_lease_generation
            ) VALUES (%s,%s,'interrupt-call','search','tool_journal',
                      decode(repeat('aa',32),'hex'),'claimed',1,7)
            """,
            (second_effect_id, RUN_ID),
        )
        connection.commit()

    with psycopg.connect(database_url) as connection:
        assert connection.execute(
            """
            SELECT effect_id::text,status,tool_name FROM agent_tool_effect
            WHERE agent_run_id=%s AND tool_call_id='interrupt-call'
              AND effect_kind='tool_journal'
            """,
            (RUN_ID,),
        ).fetchone() == (second_effect_id, "claimed", "search")
        external_effect_id = str(uuid4())
        connection.execute(
            """
            INSERT INTO agent_tool_effect(
              effect_id,agent_run_id,tool_call_id,effect_kind,request_digest,status,
              claim_epoch,claim_lease_generation
            ) VALUES (%s,%s,'external-call','http',decode(repeat('ab',32),'hex'),
                      'claimed',1,7)
            """,
            (external_effect_id, RUN_ID),
        )
        connection.commit()

    with psycopg.connect(database_url) as connection:
        with pytest.raises(errors.CheckViolation):
            connection.execute(
                "DELETE FROM agent_tool_effect WHERE effect_id=%s",
                (external_effect_id,),
            )


def test_tool_effect_rollover_fences_stale_claimant_and_adopts_unknown(
    database_url: str,
) -> None:
    journal_id = str(uuid4())
    claimed_id = str(uuid4())
    unknown_id = str(uuid4())
    with psycopg.connect(database_url) as connection:
        _seed_manifested_running_run(connection)
        connection.execute(
            """
            INSERT INTO agent_tool_effect(
              effect_id,agent_run_id,tool_call_id,tool_name,effect_kind,
              request_digest,status,claim_epoch,claim_lease_generation
            ) VALUES (%s,%s,'journal-stale','search','tool_journal',
                      decode(repeat('a1',32),'hex'),'claimed',1,7)
            """,
            (journal_id, RUN_ID),
        )
        for effect_id, call_id in ((claimed_id, "claimed-stale"), (unknown_id, "unknown-adopt")):
            connection.execute(
                """
                INSERT INTO agent_tool_effect(
                  effect_id,agent_run_id,tool_call_id,effect_kind,request_digest,status,
                  claim_epoch,claim_lease_generation
                ) VALUES (%s,%s,%s,'http',decode(repeat('a2',32),'hex'),
                          'claimed',1,7)
                """,
                (effect_id, RUN_ID, call_id),
            )
        connection.execute(
            "UPDATE agent_tool_effect SET status='unknown' WHERE effect_id=%s",
            (unknown_id,),
        )
        connection.commit()

    with psycopg.connect(database_url) as connection:
        connection.execute(
            """
            UPDATE agent_run_lease
            SET worker_id='worker-b',generation=8,
                lease_token_hash=decode(repeat('32',32),'hex'),
                leased_until=now() + interval '5 minutes'
            WHERE agent_run_id=%s
            """,
            (RUN_ID,),
        )
        connection.execute(
            "UPDATE agent_run SET epoch=2 WHERE agent_run_id=%s",
            (RUN_ID,),
        )
        connection.commit()

    with psycopg.connect(database_url) as connection:
        with pytest.raises(errors.CheckViolation):
            connection.execute(
                "DELETE FROM agent_tool_effect WHERE effect_id=%s",
                (journal_id,),
            )
    with psycopg.connect(database_url) as connection:
        with pytest.raises(errors.CheckViolation):
            connection.execute(
                """
                UPDATE agent_tool_effect
                SET status='completed',result_digest=decode(repeat('b1',32),'hex'),
                    result_schema_version=1,result_payload='"stale"'::jsonb,
                    result_is_error=false
                WHERE effect_id=%s
                """,
                (claimed_id,),
            )

    with psycopg.connect(database_url) as connection:
        connection.execute(
            """
            UPDATE agent_tool_effect
            SET claim_epoch=2,claim_lease_generation=8
            WHERE effect_id=%s AND status='unknown'
              AND claim_epoch=1 AND claim_lease_generation=7
            """,
            (unknown_id,),
        )
        connection.commit()
    with psycopg.connect(database_url) as connection:
        connection.execute(
            """
            UPDATE agent_tool_effect
            SET status='completed',result_digest=decode(repeat('b2',32),'hex'),
                result_schema_version=1,result_payload='"recovered"'::jsonb,
                result_is_error=false
            WHERE effect_id=%s AND claim_epoch=2 AND claim_lease_generation=8
            """,
            (unknown_id,),
        )
        connection.commit()

    with psycopg.connect(database_url) as connection:
        assert connection.execute(
            "SELECT result_payload,result_is_error FROM agent_tool_effect WHERE effect_id=%s",
            (unknown_id,),
        ).fetchone() == ("recovered", False)


def test_tool_effect_rollover_serializes_and_rejects_inflight_stale_finalize(
    database_url: str,
) -> None:
    effect_id = str(uuid4())
    with psycopg.connect(database_url) as connection:
        _seed_manifested_running_run(connection)
        connection.execute(
            """
            INSERT INTO agent_tool_effect(
              effect_id,agent_run_id,tool_call_id,effect_kind,request_digest,status,
              claim_epoch,claim_lease_generation
            ) VALUES (%s,%s,'race-stale','http',decode(repeat('a3',32),'hex'),
                      'claimed',1,7)
            """,
            (effect_id, RUN_ID),
        )
        connection.commit()

    rollover_locked = threading.Event()
    release_rollover = threading.Event()

    def rollover() -> None:
        with psycopg.connect(database_url) as connection:
            connection.execute(
                """
                UPDATE agent_run_lease
                SET worker_id='worker-b',generation=8,
                    lease_token_hash=decode(repeat('32',32),'hex'),
                    leased_until=now() + interval '5 minutes'
                WHERE agent_run_id=%s
                """,
                (RUN_ID,),
            )
            connection.execute(
                "UPDATE agent_run SET epoch=2 WHERE agent_run_id=%s",
                (RUN_ID,),
            )
            rollover_locked.set()
            assert release_rollover.wait(timeout=5)
            connection.commit()

    def stale_finalize() -> str:
        assert rollover_locked.wait(timeout=5)
        with psycopg.connect(database_url) as connection:
            try:
                connection.execute(
                    """
                    UPDATE agent_tool_effect
                    SET status='completed',result_digest=decode(repeat('b3',32),'hex'),
                        result_schema_version=1,result_payload='"stale"'::jsonb,
                        result_is_error=false
                    WHERE effect_id=%s
                    """,
                    (effect_id,),
                )
                connection.commit()
                return "committed"
            except errors.CheckViolation:
                connection.rollback()
                return "stale-rejected"

    with ThreadPoolExecutor(max_workers=2) as pool:
        rollover_future = pool.submit(rollover)
        stale_future = pool.submit(stale_finalize)
        assert rollover_locked.wait(timeout=5)
        time.sleep(0.05)
        assert not stale_future.done()
        release_rollover.set()
        rollover_future.result(timeout=5)
        assert stale_future.result(timeout=5) == "stale-rejected"

    with psycopg.connect(database_url) as connection:
        assert connection.execute(
            "SELECT status,claim_epoch,claim_lease_generation FROM agent_tool_effect WHERE effect_id=%s",
            (effect_id,),
        ).fetchone() == ("claimed", 1, 7)


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
                """
                UPDATE agent_run
                SET state='admission_failed',terminal_at=transaction_timestamp()
                WHERE agent_run_id=%s
                """,
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


def _seed_manifested_running_run(
    connection: psycopg.Connection[tuple[object, ...]],
    *,
    run_id: str = RUN_ID,
    manifest_id: str = MANIFEST_ID,
    lease_generation: int = 7,
    launch_id: str | None = None,
    start_running: bool = True,
) -> None:
    _seed_tenant(connection)
    _seed_published_model(connection)
    connection.execute(
        """
        INSERT INTO capability_runtime_snapshot(
          snapshot_id,organization_id,scope_key,digest
        ) VALUES (%s,%s,'org/a',decode(repeat('12',32),'hex'))
        """,
        (SNAPSHOT_ID, ORG_ID),
    )
    _insert_run(connection, run_id=run_id, launch_id=launch_id)
    connection.execute(
        """
        INSERT INTO agent_execution_manifest(
          execution_manifest_id,agent_run_id,namespace,digest,
          agent_preset_key,agent_preset_digest,model_revision_id,
          capability_snapshot_id,usage_mode,usage_policy_digest,payload
        ) VALUES (
          %s,%s,'org/a',decode(repeat('21',32),'hex'),
          'general',decode(repeat('22',32),'hex'),%s,%s,
          'unmetered',decode(repeat('23',32),'hex'),'{}'
        )
        """,
        (manifest_id, run_id, PUBLISHED_REVISION_ID, SNAPSHOT_ID),
    )
    connection.execute(
        """
        UPDATE agent_run SET execution_manifest_id=%s,state='queued'
        WHERE agent_run_id=%s
        """,
        (manifest_id, run_id),
    )
    if start_running:
        connection.execute(
            "UPDATE agent_run SET state='running' WHERE agent_run_id=%s",
            (run_id,),
        )
        connection.execute(
            """
            INSERT INTO agent_run_lease(
              agent_run_id,worker_id,lease_token_hash,leased_until,generation
            ) VALUES (%s,'worker-a',decode(repeat('31',32),'hex'),
                      now() + interval '5 minutes',%s)
            """,
            (run_id, lease_generation),
        )


def _finalize_seeded_run(
    connection: psycopg.Connection[tuple[object, ...]],
    *,
    terminal_state: str,
    lease_generation: int = 7,
    usage_id: str | None = None,
    line_id: str | None = None,
    reserve: bool = True,
) -> tuple[str, str | None]:
    usage_id = usage_id or str(uuid4())
    if reserve:
        connection.execute(
            """
            UPDATE agent_run
            SET terminal_claim_id=%s,terminal_claim_epoch=epoch,
                terminal_claim_lease_generation=%s,
                terminal_claimed_at=transaction_timestamp()
            WHERE agent_run_id=%s
            """,
            (str(uuid4()), lease_generation, RUN_ID),
        )
    run = connection.execute(
        """
        SELECT execution_manifest_id,usage_input_tokens,usage_output_tokens,
               usage_cached_tokens,usage_call_count,epoch,next_event_seq
        FROM agent_run WHERE agent_run_id=%s
        """,
        (RUN_ID,),
    ).fetchone()
    assert run is not None
    manifest_id, input_tokens, output_tokens, cached_tokens, call_count, epoch, seq = run
    connection.execute(
        """
        INSERT INTO agent_run_usage(
          run_usage_id,agent_run_id,digest,input_tokens,output_tokens,
          cached_tokens,call_count,finalized_at
        ) VALUES (%s,%s,decode(repeat('51',32),'hex'),%s,%s,%s,%s,
                  transaction_timestamp())
        """,
        (usage_id, RUN_ID, input_tokens, output_tokens, cached_tokens, call_count),
    )
    if manifest_id is not None:
        line_id = line_id or str(uuid4())
        connection.execute(
            """
            INSERT INTO agent_run_usage_line(
              usage_line_id,run_usage_id,model_revision_id,feature_key,
              input_tokens,output_tokens,cached_tokens,call_count
            )
            SELECT %s,%s,m.model_revision_id,m.usage_feature_key,%s,%s,%s,%s
            FROM agent_execution_manifest m
            WHERE m.execution_manifest_id=%s
            """,
            (
                line_id,
                usage_id,
                input_tokens,
                output_tokens,
                cached_tokens,
                call_count,
                manifest_id,
            ),
        )
    terminal_kind = (
        "run.completed"
        if terminal_state in ("completed", "cancelled")
        else "run.failed"
    )
    has_rejection_fence = connection.execute(
        """
        SELECT EXISTS(
          SELECT 1 FROM agent_projection_ack
          WHERE agent_run_id=%s AND consumer='chat' AND rejected_seq=%s
        )
        """,
        (RUN_ID, seq - 1),
    ).fetchone()[0]
    _append_event(
        connection,
        epoch=epoch,
        seq=seq,
        kind=terminal_kind,
        wire_metadata=not has_rejection_fence,
    )
    connection.execute(
        """
        UPDATE agent_run SET state=%s,terminal_at=transaction_timestamp()
        WHERE agent_run_id=%s
        """,
        (terminal_state, RUN_ID),
    )
    return usage_id, line_id


@pytest.mark.parametrize(
    ("terminal_state", "terminal_kind"),
    [
        ("completed", "run.completed"),
        ("cancelled", "run.completed"),
        ("failed", "run.failed"),
    ],
)
def test_terminal_state_uses_only_frozen_agent_event_kinds(
    database_url: str,
    terminal_state: str,
    terminal_kind: str,
) -> None:
    usage_id = str(uuid4())
    with psycopg.connect(database_url) as connection:
        _seed_manifested_running_run(connection)
        connection.execute(
            """
            UPDATE agent_run
            SET terminal_claim_id=%s,terminal_claim_epoch=epoch,
                terminal_claim_lease_generation=7,
                terminal_claimed_at=transaction_timestamp()
            WHERE agent_run_id=%s
            """,
            (str(uuid4()), RUN_ID),
        )
        connection.execute(
            """
            INSERT INTO agent_run_usage(
              run_usage_id,agent_run_id,digest,input_tokens,output_tokens,
              cached_tokens,call_count,finalized_at
            ) VALUES (%s,%s,decode(repeat('51',32),'hex'),0,0,0,0,
                      transaction_timestamp())
            """,
            (usage_id, RUN_ID),
        )
        connection.execute(
            """
            INSERT INTO agent_run_usage_line(
              usage_line_id,run_usage_id,model_revision_id,feature_key,
              input_tokens,output_tokens,cached_tokens,call_count
            ) VALUES (%s,%s,%s,'agent',0,0,0,0)
            """,
            (str(uuid4()), usage_id, PUBLISHED_REVISION_ID),
        )
        _append_event(connection, epoch=1, seq=1, kind=terminal_kind)
        connection.execute(
            """
            UPDATE agent_run SET state=%s,terminal_at=transaction_timestamp()
            WHERE agent_run_id=%s
            """,
            (terminal_state, RUN_ID),
        )
        connection.commit()

    with psycopg.connect(database_url) as connection:
        assert connection.execute(
            """
            SELECT r.state,e.kind
            FROM agent_run r JOIN agent_event_outbox e USING (agent_run_id)
            WHERE r.agent_run_id=%s
            """,
            (RUN_ID,),
        ).fetchone() == (terminal_state, terminal_kind)


def test_terminal_runtime_compaction_is_idempotent_and_retains_facts(
    database_url: str,
) -> None:
    launch_id = str(uuid4())
    effect_id = str(uuid4())
    with psycopg.connect(database_url) as connection:
        _seed_manifested_running_run(connection, launch_id=launch_id)
        connection.execute(
            """
            INSERT INTO agent_tool_effect(
              effect_id,agent_run_id,tool_call_id,effect_kind,request_digest,status,
              claim_epoch,claim_lease_generation
            ) VALUES (%s,%s,'compact-call','http',decode(repeat('aa',32),'hex'),
                      'claimed',1,7)
            """,
            (effect_id, RUN_ID),
        )
        connection.execute(
            """
            UPDATE agent_tool_effect
            SET status='completed',result_digest=decode(repeat('bb',32),'hex'),
                result_schema_version=1,result_payload='"retained"'::jsonb,
                result_is_error=false
            WHERE effect_id=%s
            """,
            (effect_id,),
        )
        _finalize_seeded_run(connection, terminal_state="completed")
        connection.commit()

    with psycopg.connect(database_url) as connection:
        _publish_event(connection, seq=1)
        connection.execute(
            """
            INSERT INTO agent_projection_ack(
              agent_run_id,consumer,projected_epoch,projected_seq
            ) VALUES (%s,'chat',1,1)
            """,
            (RUN_ID,),
        )
        connection.execute(
            "UPDATE agent_event_outbox SET acked_at=transaction_timestamp() WHERE agent_run_id=%s",
            (RUN_ID,),
        )
        connection.execute(
            "DELETE FROM agent_event_outbox WHERE agent_run_id=%s",
            (RUN_ID,),
        )
        first = connection.execute(
            """
            UPDATE agent_run
            SET runtime_compacted_at=transaction_timestamp(),
                runtime_compaction_policy_version=1
            WHERE agent_run_id=%s AND runtime_compacted_at IS NULL
            RETURNING agent_run_id
            """,
            (RUN_ID,),
        ).fetchall()
        replay = connection.execute(
            """
            UPDATE agent_run
            SET runtime_compacted_at=transaction_timestamp(),
                runtime_compaction_policy_version=1
            WHERE agent_run_id=%s AND runtime_compacted_at IS NULL
            RETURNING agent_run_id
            """,
            (RUN_ID,),
        ).fetchall()
        connection.commit()
    assert len(first) == 1
    assert replay == []

    with psycopg.connect(database_url) as connection:
        assert connection.execute(
            "SELECT count(*) FROM agent_run WHERE agent_run_id=%s",
            (RUN_ID,),
        ).fetchone()[0] == 1
        assert connection.execute(
            "SELECT count(*) FROM agent_execution_manifest WHERE agent_run_id=%s",
            (RUN_ID,),
        ).fetchone()[0] == 1
        assert connection.execute(
            "SELECT count(*) FROM agent_run_usage WHERE agent_run_id=%s",
            (RUN_ID,),
        ).fetchone()[0] == 1
        assert connection.execute(
            "SELECT result_payload FROM agent_tool_effect WHERE effect_id=%s",
            (effect_id,),
        ).fetchone()[0] == "retained"

    for mutation in (
        "runtime_compacted_at=NULL,runtime_compaction_policy_version=NULL",
        "runtime_compaction_policy_version=2",
    ):
        with psycopg.connect(database_url) as connection:
            with pytest.raises(errors.CheckViolation):
                connection.execute(
                    f"UPDATE agent_run SET {mutation} WHERE agent_run_id=%s",
                    (RUN_ID,),
                )

    with psycopg.connect(database_url) as connection:
        with pytest.raises(errors.UniqueViolation):
            connection.execute(
                """
                INSERT INTO agent_run(
                  agent_run_id,launch_id,launch_request_digest,namespace,state
                ) VALUES (%s,%s,decode('cc','hex'),'org/a','preparing')
                """,
                (RUN_2_ID, launch_id),
            )


def test_tool_effect_completed_result_is_exactly_replayable_and_immutable(
    database_url: str,
) -> None:
    effect_id = str(uuid4())
    payload = "first\nsecond"
    with psycopg.connect(database_url) as connection:
        _seed_manifested_running_run(connection)
        connection.execute(
            """
            INSERT INTO agent_tool_effect(
              effect_id,agent_run_id,tool_call_id,effect_kind,request_digest,status,
              claim_epoch,claim_lease_generation
            ) VALUES (%s,%s,'call-ga','http',decode(repeat('41',32),'hex'),
                      'claimed',1,7)
            """,
            (effect_id, RUN_ID),
        )
        connection.execute(
            """
            UPDATE agent_tool_effect
            SET status='completed',result_digest=decode(repeat('42',32),'hex'),
                result_schema_version=1,result_payload=%s,result_is_error=true
            WHERE effect_id=%s
            """,
            (json.dumps(payload), effect_id),
        )
        connection.commit()

    with psycopg.connect(database_url) as connection:
        restored = connection.execute(
            """
            SELECT result_schema_version,result_payload,result_is_error
            FROM agent_tool_effect WHERE effect_id=%s
            """,
            (effect_id,),
        ).fetchone()
        assert restored == (1, payload, True)

    mutations = (
        "result_schema_version=2",
        "result_payload='{}'::jsonb",
        "result_is_error=false",
        "result_digest=decode(repeat('43',32),'hex')",
    )
    for mutation in mutations:
        with psycopg.connect(database_url) as connection:
            with pytest.raises(errors.CheckViolation):
                connection.execute(
                    f"UPDATE agent_tool_effect SET {mutation} WHERE effect_id=%s",
                    (effect_id,),
                )


@pytest.mark.parametrize("status", ["claimed", "unknown"])
def test_tool_effect_nonterminal_state_rejects_result_payload(
    database_url: str,
    status: str,
) -> None:
    effect_id = str(uuid4())
    with psycopg.connect(database_url) as connection:
        _seed_manifested_running_run(connection)
        connection.execute(
            """
            INSERT INTO agent_tool_effect(
              effect_id,agent_run_id,tool_call_id,effect_kind,request_digest,status,
              claim_epoch,claim_lease_generation
            ) VALUES (%s,%s,'call-ga','http',decode(repeat('41',32),'hex'),
                      'claimed',1,7)
            """,
            (effect_id, RUN_ID),
        )
        if status == "unknown":
            connection.execute(
                "UPDATE agent_tool_effect SET status='unknown' WHERE effect_id=%s",
                (effect_id,),
            )
        with pytest.raises(errors.CheckViolation):
            connection.execute(
                """
                UPDATE agent_tool_effect
                SET result_digest=decode(repeat('42',32),'hex'),
                    result_schema_version=1,result_payload='"unexpected"'::jsonb,
                    result_is_error=false
                WHERE effect_id=%s
                """,
                (effect_id,),
            )


def test_tool_effect_result_payload_is_bounded(database_url: str) -> None:
    effect_id = str(uuid4())
    with psycopg.connect(database_url) as connection:
        _seed_manifested_running_run(connection)
        connection.execute(
            """
            INSERT INTO agent_tool_effect(
              effect_id,agent_run_id,tool_call_id,effect_kind,request_digest,status,
              claim_epoch,claim_lease_generation
            ) VALUES (%s,%s,'call-ga','http',decode(repeat('41',32),'hex'),
                      'claimed',1,7)
            """,
            (effect_id, RUN_ID),
        )
        with pytest.raises(errors.CheckViolation):
            connection.execute(
                """
                UPDATE agent_tool_effect
                SET status='completed',result_digest=decode(repeat('42',32),'hex'),
                    result_schema_version=1,result_payload=%s,result_is_error=false
                WHERE effect_id=%s
                """,
                (json.dumps("x" * 65537), effect_id),
            )


def test_terminal_reservation_requires_current_lease_and_atomic_terminal_evidence(
    database_url: str,
) -> None:
    claim_id = str(uuid4())
    with psycopg.connect(database_url) as connection:
        _seed_manifested_running_run(connection)
        connection.execute(
            """
            UPDATE agent_run
            SET terminal_claim_id=%s,terminal_claim_epoch=epoch,
                terminal_claim_lease_generation=7,
                terminal_claimed_at=transaction_timestamp()
            WHERE agent_run_id=%s
            """,
            (claim_id, RUN_ID),
        )
        connection.commit()

    with psycopg.connect(database_url) as connection:
        connection.execute(
            """
            INSERT INTO agent_run_usage(
              run_usage_id,agent_run_id,digest,input_tokens,output_tokens,
              cached_tokens,call_count,finalized_at
            ) VALUES (%s,%s,decode(repeat('51',32),'hex'),0,0,0,0,
                      transaction_timestamp())
            """,
            (str(uuid4()), RUN_ID),
        )
        connection.execute(
            """
            UPDATE agent_run SET state='completed',terminal_at=transaction_timestamp()
            WHERE agent_run_id=%s
            """,
            (RUN_ID,),
        )
        with pytest.raises(errors.CheckViolation):
            connection.commit()

    with psycopg.connect(database_url) as connection:
        assert connection.execute(
            "SELECT state,terminal_claim_id::text FROM agent_run WHERE agent_run_id=%s",
            (RUN_ID,),
        ).fetchone() == ("running", claim_id)


def test_terminal_reservation_race_and_stale_claimant_are_fenced(
    database_url: str,
) -> None:
    with psycopg.connect(database_url) as connection:
        _seed_manifested_running_run(connection)
        connection.commit()

    barrier = threading.Barrier(2)

    def reserve(claim_id: str) -> str:
        with psycopg.connect(database_url) as connection:
            barrier.wait(timeout=5)
            row = connection.execute(
                """
                UPDATE agent_run
                SET terminal_claim_id=%s,terminal_claim_epoch=epoch,
                    terminal_claim_lease_generation=7,
                    terminal_claimed_at=transaction_timestamp()
                WHERE agent_run_id=%s AND terminal_claim_id IS NULL
                RETURNING terminal_claim_id::text
                """,
                (claim_id, RUN_ID),
            ).fetchone()
            connection.commit()
            return "won" if row else "lost"

    claim_ids = [str(uuid4()), str(uuid4())]
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(reserve, claim_ids))
    assert sorted(outcomes) == ["lost", "won"]

    winner = claim_ids[outcomes.index("won")]
    with psycopg.connect(database_url) as connection:
        connection.execute(
            """
            UPDATE agent_run_lease
            SET worker_id='worker-b',generation=8,
                lease_token_hash=decode(repeat('32',32),'hex'),
                leased_until=now() + interval '5 minutes'
            WHERE agent_run_id=%s
            """,
            (RUN_ID,),
        )
        connection.execute(
            "UPDATE agent_run SET epoch=2 WHERE agent_run_id=%s",
            (RUN_ID,),
        )
        connection.execute(
            """
            UPDATE agent_run
            SET terminal_claim_id=%s,terminal_claim_epoch=2,
                terminal_claim_lease_generation=8,
                terminal_claimed_at=transaction_timestamp()
            WHERE agent_run_id=%s
            """,
            (str(uuid4()), RUN_ID),
        )
        connection.commit()

    with psycopg.connect(database_url) as connection:
        assert connection.execute(
            """
            UPDATE agent_run SET state='completed',terminal_at=transaction_timestamp()
            WHERE agent_run_id=%s AND terminal_claim_id=%s
            RETURNING agent_run_id
            """,
            (RUN_ID, winner),
        ).fetchone() is None


def test_terminal_finalization_race_commits_one_event_and_usage_record(
    database_url: str,
) -> None:
    with psycopg.connect(database_url) as connection:
        _seed_manifested_running_run(connection)
        connection.commit()

    barrier = threading.Barrier(2)

    def finalize(claim_id: str) -> str:
        with psycopg.connect(database_url) as connection:
            barrier.wait(timeout=5)
            reserved = connection.execute(
                """
                UPDATE agent_run
                SET terminal_claim_id=%s,terminal_claim_epoch=epoch,
                    terminal_claim_lease_generation=7,
                    terminal_claimed_at=transaction_timestamp()
                WHERE agent_run_id=%s AND terminal_claim_id IS NULL
                RETURNING terminal_claim_id
                """,
                (claim_id, RUN_ID),
            ).fetchone()
            if reserved is None:
                connection.commit()
                return "lost"
            _finalize_seeded_run(
                connection,
                terminal_state="completed",
                reserve=False,
            )
            connection.commit()
            return "finalized"

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(finalize, (str(uuid4()), str(uuid4()))))
    assert sorted(outcomes) == ["finalized", "lost"]

    with psycopg.connect(database_url) as connection:
        assert connection.execute(
            """
            SELECT r.state,count(DISTINCT e.event_id),count(DISTINCT u.run_usage_id)
            FROM agent_run r
            LEFT JOIN agent_event_outbox e USING (agent_run_id)
            LEFT JOIN agent_run_usage u USING (agent_run_id)
            WHERE r.agent_run_id=%s GROUP BY r.state
            """,
            (RUN_ID,),
        ).fetchone() == ("completed", 1, 1)


def test_usage_accumulator_is_monotonic_and_terminal_finalization_is_exact(
    database_url: str,
) -> None:
    usage_id = str(uuid4())
    with psycopg.connect(database_url) as connection:
        _seed_manifested_running_run(connection)
        connection.execute(
            """
            UPDATE agent_run
            SET usage_input_tokens=11,usage_output_tokens=7,
                usage_cached_tokens=3,usage_call_count=2
            WHERE agent_run_id=%s
            """,
            (RUN_ID,),
        )
        connection.commit()

    with psycopg.connect(database_url) as connection:
        with pytest.raises(errors.CheckViolation):
            connection.execute(
                "UPDATE agent_run SET usage_input_tokens=10 WHERE agent_run_id=%s",
                (RUN_ID,),
            )

    with psycopg.connect(database_url) as connection:
        connection.execute(
            """
            UPDATE agent_run
            SET terminal_claim_id=%s,terminal_claim_epoch=epoch,
                terminal_claim_lease_generation=7,
                terminal_claimed_at=transaction_timestamp()
            WHERE agent_run_id=%s
            """,
            (str(uuid4()), RUN_ID),
        )
        connection.execute(
            """
            INSERT INTO agent_run_usage(
              run_usage_id,agent_run_id,digest,input_tokens,output_tokens,
              cached_tokens,call_count,finalized_at
            ) VALUES (%s,%s,decode(repeat('51',32),'hex'),11,7,3,2,
                      transaction_timestamp())
            """,
            (usage_id, RUN_ID),
        )
        connection.execute(
            """
            INSERT INTO agent_run_usage_line(
              usage_line_id,run_usage_id,model_revision_id,feature_key,
              input_tokens,output_tokens,cached_tokens,call_count
            ) VALUES (%s,%s,%s,'agent',11,7,3,2)
            """,
            (str(uuid4()), usage_id, PUBLISHED_REVISION_ID),
        )
        _append_event(connection, epoch=1, seq=1, kind="run.completed")
        connection.execute(
            """
            UPDATE agent_run SET state='completed',terminal_at=transaction_timestamp()
            WHERE agent_run_id=%s
            """,
            (RUN_ID,),
        )
        connection.commit()

    with psycopg.connect(database_url) as connection:
        with pytest.raises(errors.CheckViolation):
            connection.execute(
                "UPDATE agent_run SET usage_call_count=3 WHERE agent_run_id=%s",
                (RUN_ID,),
            )

    with psycopg.connect(database_url) as connection:
        with pytest.raises(errors.CheckViolation):
            connection.execute(
                "UPDATE agent_run SET budget_tokens_used=1 WHERE agent_run_id=%s",
                (RUN_ID,),
            )


def test_budget_and_usage_accumulators_survive_hitl_as_independent_totals(
    database_url: str,
) -> None:
    with psycopg.connect(database_url) as connection:
        _seed_manifested_running_run(connection)
        connection.execute(
            """
            UPDATE agent_run
            SET budget_tokens_used=100,usage_input_tokens=10,
                usage_output_tokens=1,usage_call_count=1,
                state='awaiting_input'
            WHERE agent_run_id=%s
            """,
            (RUN_ID,),
        )
        connection.commit()

    with psycopg.connect(database_url) as connection:
        connection.execute(
            """
            UPDATE agent_run
            SET state='running',budget_tokens_used=150,
                usage_input_tokens=30,usage_output_tokens=3,usage_call_count=2
            WHERE agent_run_id=%s
            """,
            (RUN_ID,),
        )
        connection.commit()

    with psycopg.connect(database_url) as connection:
        assert connection.execute(
            """
            SELECT state,budget_tokens_used,usage_input_tokens,
                   usage_output_tokens,usage_cached_tokens,usage_call_count
            FROM agent_run WHERE agent_run_id=%s
            """,
            (RUN_ID,),
        ).fetchone() == ("running", 150, 30, 3, 0, 2)

    with psycopg.connect(database_url) as connection:
        _finalize_seeded_run(connection, terminal_state="completed")
        connection.commit()
    with psycopg.connect(database_url) as connection:
        assert connection.execute(
            """
            SELECT r.budget_tokens_used,u.input_tokens,u.output_tokens,
                   u.cached_tokens,u.call_count
            FROM agent_run r JOIN agent_run_usage u USING (agent_run_id)
            WHERE r.agent_run_id=%s
            """,
            (RUN_ID,),
        ).fetchone() == (150, 30, 3, 0, 2)


def test_terminal_usage_mismatch_rolls_back_state_event_and_usage(
    database_url: str,
) -> None:
    with psycopg.connect(database_url) as connection:
        _seed_manifested_running_run(connection)
        connection.execute(
            """
            UPDATE agent_run
            SET usage_input_tokens=5,usage_call_count=1,
                terminal_claim_id=%s,terminal_claim_epoch=epoch,
                terminal_claim_lease_generation=7,
                terminal_claimed_at=transaction_timestamp()
            WHERE agent_run_id=%s
            """,
            (str(uuid4()), RUN_ID),
        )
        connection.commit()

    with psycopg.connect(database_url) as connection:
        usage_id = str(uuid4())
        connection.execute(
            """
            INSERT INTO agent_run_usage(
              run_usage_id,agent_run_id,digest,input_tokens,output_tokens,
              cached_tokens,call_count,finalized_at
            ) VALUES (%s,%s,decode(repeat('51',32),'hex'),4,0,0,1,
                      transaction_timestamp())
            """,
            (usage_id, RUN_ID),
        )
        connection.execute(
            """
            INSERT INTO agent_run_usage_line(
              usage_line_id,run_usage_id,model_revision_id,feature_key,
              input_tokens,output_tokens,cached_tokens,call_count
            ) VALUES (%s,%s,%s,'agent',4,0,0,1)
            """,
            (str(uuid4()), usage_id, PUBLISHED_REVISION_ID),
        )
        _append_event(connection, epoch=1, seq=1, kind="run.completed")
        connection.execute(
            """
            UPDATE agent_run SET state='completed',terminal_at=transaction_timestamp()
            WHERE agent_run_id=%s
            """,
            (RUN_ID,),
        )
        with pytest.raises(errors.CheckViolation):
            connection.commit()

    with psycopg.connect(database_url) as connection:
        assert connection.execute(
            "SELECT state,next_event_seq FROM agent_run WHERE agent_run_id=%s",
            (RUN_ID,),
        ).fetchone() == ("running", 1)
        assert connection.execute(
            "SELECT count(*) FROM agent_run_usage WHERE agent_run_id=%s",
            (RUN_ID,),
        ).fetchone()[0] == 0


def test_terminal_usage_line_must_match_manifest_feature(
    database_url: str,
) -> None:
    with psycopg.connect(database_url) as connection:
        _seed_manifested_running_run(connection)
        connection.execute(
            """
            UPDATE agent_run
            SET terminal_claim_id=%s,terminal_claim_epoch=epoch,
                terminal_claim_lease_generation=7,
                terminal_claimed_at=transaction_timestamp()
            WHERE agent_run_id=%s
            """,
            (str(uuid4()), RUN_ID),
        )
        connection.commit()
        usage_id = str(uuid4())
        connection.execute(
            """
            INSERT INTO agent_run_usage(
              run_usage_id,agent_run_id,digest,input_tokens,output_tokens,
              cached_tokens,call_count,finalized_at
            ) VALUES (%s,%s,decode(repeat('51',32),'hex'),0,0,0,0,
                      transaction_timestamp())
            """,
            (usage_id, RUN_ID),
        )
        connection.execute(
            """
            INSERT INTO agent_run_usage_line(
              usage_line_id,run_usage_id,model_revision_id,feature_key,
              input_tokens,output_tokens,cached_tokens,call_count
            ) VALUES (%s,%s,%s,'wrong-feature',0,0,0,0)
            """,
            (str(uuid4()), usage_id, PUBLISHED_REVISION_ID),
        )
        _append_event(connection, epoch=1, seq=1, kind="run.completed")
        connection.execute(
            """
            UPDATE agent_run SET state='completed',terminal_at=transaction_timestamp()
            WHERE agent_run_id=%s
            """,
            (RUN_ID,),
        )
        with pytest.raises(errors.CheckViolation):
            connection.commit()

    with psycopg.connect(database_url) as connection:
        assert connection.execute(
            "SELECT state,next_event_seq FROM agent_run WHERE agent_run_id=%s",
            (RUN_ID,),
        ).fetchone() == ("running", 1)


def test_projection_first_nack_is_epoch_fenced_and_one_way(database_url: str) -> None:
    with psycopg.connect(database_url) as connection:
        _insert_run(connection)
        _append_event(connection, epoch=1, seq=1)
        _publish_event(connection, seq=1)
        connection.execute(
            """
            INSERT INTO agent_projection_ack(
              agent_run_id,consumer,projected_epoch,projected_seq
            ) VALUES (%s,'chat',1,0)
            """,
            (RUN_ID,),
        )
        connection.execute(
            """
            UPDATE agent_projection_ack
            SET rejected_seq=1,rejection_code='unsupported_schema',
                rejected_at=transaction_timestamp(),generation=2
            WHERE agent_run_id=%s AND consumer='chat' AND generation=1
            """,
            (RUN_ID,),
        )
        connection.commit()

    for mutation in (
        "projected_seq=1,generation=3",
        "rejected_seq=2,generation=3",
        "rejection_code='rewritten',generation=3",
        "rejected_at=rejected_at + interval '1 second',generation=3",
    ):
        with psycopg.connect(database_url) as connection:
            with pytest.raises(errors.CheckViolation):
                connection.execute(
                    f"""
                    UPDATE agent_projection_ack SET {mutation}
                    WHERE agent_run_id=%s AND consumer='chat'
                    """,
                    (RUN_ID,),
                )

    with psycopg.connect(database_url) as connection:
        connection.execute(
            """
            UPDATE agent_projection_ack
            SET producer_close_requested=true,generation=3
            WHERE agent_run_id=%s AND consumer='chat'
            """,
            (RUN_ID,),
        )
        connection.execute(
            """
            UPDATE agent_projection_ack
            SET consumer_closed=true,generation=4
            WHERE agent_run_id=%s AND consumer='chat'
            """,
            (RUN_ID,),
        )
        connection.commit()


def test_projection_first_nack_cannot_skip_an_unacknowledged_sequence(
    database_url: str,
) -> None:
    with psycopg.connect(database_url) as connection:
        _insert_run(connection)
        _append_event(connection, epoch=1, seq=1)
        _append_event(connection, epoch=1, seq=2)
        _publish_event(connection, seq=1)
        _publish_event(connection, seq=2)
        connection.execute(
            """
            INSERT INTO agent_projection_ack(
              agent_run_id,consumer,projected_epoch,projected_seq
            ) VALUES (%s,'chat',1,0)
            """,
            (RUN_ID,),
        )
        with pytest.raises(errors.CheckViolation):
            connection.execute(
                """
                UPDATE agent_projection_ack
                SET rejected_seq=2,rejection_code='unsupported_schema',
                    rejected_at=transaction_timestamp(),generation=2
                WHERE agent_run_id=%s AND consumer='chat' AND generation=1
                """,
                (RUN_ID,),
            )


def test_projection_ack_vs_nack_generation_race_has_one_winner(
    database_url: str,
) -> None:
    with psycopg.connect(database_url) as connection:
        _insert_run(connection)
        _append_event(connection, epoch=1, seq=1)
        _publish_event(connection, seq=1)
        connection.execute(
            """
            INSERT INTO agent_projection_ack(
              agent_run_id,consumer,projected_epoch,projected_seq
            ) VALUES (%s,'chat',1,0)
            """,
            (RUN_ID,),
        )
        connection.commit()

    barrier = threading.Barrier(2)

    def advance(kind: str) -> str:
        with psycopg.connect(database_url) as connection:
            barrier.wait(timeout=5)
            if kind == "ack":
                row = connection.execute(
                    """
                    UPDATE agent_projection_ack
                    SET projected_seq=1,generation=2
                    WHERE agent_run_id=%s AND consumer='chat' AND generation=1
                      AND rejected_seq IS NULL
                    RETURNING generation
                    """,
                    (RUN_ID,),
                ).fetchone()
            else:
                row = connection.execute(
                    """
                    UPDATE agent_projection_ack
                    SET rejected_seq=1,rejection_code='unsupported_schema',
                        rejected_at=transaction_timestamp(),generation=2
                    WHERE agent_run_id=%s AND consumer='chat' AND generation=1
                      AND projected_seq=0
                    RETURNING generation
                    """,
                    (RUN_ID,),
                ).fetchone()
            connection.commit()
            return kind if row else "lost"

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(advance, ("ack", "nack")))
    assert outcomes.count("lost") == 1
    assert ("ack" in outcomes) != ("nack" in outcomes)


def test_projection_nack_binds_run_global_poison_seq_across_epoch(
    database_url: str,
) -> None:
    with psycopg.connect(database_url) as connection:
        _insert_run(connection)
        _append_event(connection, epoch=1, seq=1)
        _publish_event(connection, seq=1)
        connection.execute(
            """
            INSERT INTO agent_projection_ack(
              agent_run_id,consumer,projected_epoch,projected_seq
            ) VALUES (%s,'chat',1,1)
            """,
            (RUN_ID,),
        )
        connection.execute(
            "UPDATE agent_run SET epoch=2 WHERE agent_run_id=%s",
            (RUN_ID,),
        )
        _append_event(connection, epoch=2, seq=2)
        _publish_event(connection, seq=2)
        connection.execute(
            """
            UPDATE agent_projection_ack
            SET rejected_seq=2,rejection_code='unsupported_schema',
                rejected_at=transaction_timestamp(),generation=2
            WHERE agent_run_id=%s AND consumer='chat' AND generation=1
            """,
            (RUN_ID,),
        )
        connection.commit()

    with psycopg.connect(database_url) as connection:
        assert connection.execute(
            """
            SELECT projected_epoch,projected_seq,rejected_seq
            FROM agent_projection_ack WHERE agent_run_id=%s AND consumer='chat'
            """,
            (RUN_ID,),
        ).fetchone() == (1, 1, 2)


def test_projection_late_ack_keeps_the_event_epoch_after_lease_rollover(
    database_url: str,
) -> None:
    with psycopg.connect(database_url) as connection:
        _insert_run(connection)
        _append_event(connection, epoch=1, seq=1)
        _publish_event(connection, seq=1)
        connection.execute(
            """
            INSERT INTO agent_projection_ack(
              agent_run_id,consumer,projected_epoch,projected_seq
            ) VALUES (%s,'chat',1,0)
            """,
            (RUN_ID,),
        )
        connection.execute(
            "UPDATE agent_run SET epoch=2 WHERE agent_run_id=%s",
            (RUN_ID,),
        )
        connection.execute(
            """
            UPDATE agent_projection_ack SET projected_seq=1,generation=2
            WHERE agent_run_id=%s AND consumer='chat' AND generation=1
            """,
            (RUN_ID,),
        )
        connection.commit()

    with psycopg.connect(database_url) as connection:
        assert connection.execute(
            """
            SELECT projected_epoch,projected_seq
            FROM agent_projection_ack WHERE agent_run_id=%s AND consumer='chat'
            """,
            (RUN_ID,),
        ).fetchone() == (1, 1)


def test_projection_late_nack_binds_the_old_epoch_poison_event(
    database_url: str,
) -> None:
    with psycopg.connect(database_url) as connection:
        _insert_run(connection)
        _append_event(connection, epoch=1, seq=1)
        _publish_event(connection, seq=1)
        connection.execute(
            """
            INSERT INTO agent_projection_ack(
              agent_run_id,consumer,projected_epoch,projected_seq
            ) VALUES (%s,'chat',1,0)
            """,
            (RUN_ID,),
        )
        connection.execute(
            "UPDATE agent_run SET epoch=2 WHERE agent_run_id=%s",
            (RUN_ID,),
        )
        connection.execute(
            """
            UPDATE agent_projection_ack
            SET rejected_seq=1,rejection_code='unsupported_schema',
                rejected_at=transaction_timestamp(),generation=2
            WHERE agent_run_id=%s AND consumer='chat' AND generation=1
            """,
            (RUN_ID,),
        )
        connection.commit()

    with psycopg.connect(database_url) as connection:
        assert connection.execute(
            "SELECT rejected_seq FROM agent_projection_ack WHERE agent_run_id=%s",
            (RUN_ID,),
        ).fetchone()[0] == 1


def test_projection_nack_terminalizes_with_unpublished_internal_evidence(
    database_url: str,
) -> None:
    with psycopg.connect(database_url) as connection:
        _seed_manifested_running_run(connection)
        _append_event(connection, epoch=1, seq=1)
        _publish_event(connection, seq=1)
        connection.execute(
            """
            INSERT INTO agent_projection_ack(
              agent_run_id,consumer,projected_epoch,projected_seq
            ) VALUES (%s,'chat',1,0)
            """,
            (RUN_ID,),
        )
        connection.execute(
            """
            UPDATE agent_projection_ack
            SET rejected_seq=1,rejection_code='unsupported_schema',
                rejected_at=transaction_timestamp(),generation=2
            WHERE agent_run_id=%s AND consumer='chat' AND generation=1
            """,
            (RUN_ID,),
        )
        connection.commit()

    with psycopg.connect(database_url) as connection:
        _finalize_seeded_run(connection, terminal_state="failed")
        connection.commit()

    with psycopg.connect(database_url) as connection:
        assert connection.execute(
            """
            SELECT r.state,e.seq,e.kind,e.published_at,
                   e.stream_index,e.stream_timestamp_ms
            FROM agent_run r JOIN agent_event_outbox e USING (agent_run_id)
            WHERE r.agent_run_id=%s AND e.kind='run.failed'
            """,
            (RUN_ID,),
        ).fetchone() == ("failed", 2, "run.failed", None, None, None)
        with pytest.raises(errors.CheckViolation):
            connection.execute(
                """
                UPDATE agent_event_outbox SET published_at=transaction_timestamp()
                WHERE agent_run_id=%s AND kind='run.failed'
                """,
                (RUN_ID,),
            )


def test_dispatch_dlq_deduplicates_raw_frame_and_preserves_evidence(
    database_url: str,
) -> None:
    raw_hash = hashlib.sha256(b"bad-frame").digest()
    first_id = str(uuid4())
    with psycopg.connect(database_url) as connection:
        for dlq_id in (first_id, str(uuid4())):
            returned = connection.execute(
                """
                INSERT INTO agent_dispatch_dlq(
                  dlq_id,source_key,raw_hash,request_digest,error_code,payload,retry_status
                ) VALUES (%s,'redis:dispatch',%s,decode(repeat('61',32),'hex'),
                          'malformed_frame','{"raw":"YmFkLWZyYW1l"}','pending')
                ON CONFLICT (source_key,raw_hash) DO UPDATE
                SET request_digest=EXCLUDED.request_digest,
                    error_code=EXCLUDED.error_code,payload=EXCLUDED.payload
                RETURNING dlq_id::text
                """,
                (dlq_id, raw_hash),
            ).fetchone()[0]
            assert returned == first_id
        connection.commit()

    with psycopg.connect(database_url) as connection:
        with pytest.raises(errors.CheckViolation):
            connection.execute(
                """
                INSERT INTO agent_dispatch_dlq(
                  dlq_id,source_key,raw_hash,request_digest,error_code,payload,retry_status
                ) VALUES (%s,'redis:dispatch',%s,decode(repeat('61',32),'hex'),
                          'malformed_frame','{"raw":"different"}','pending')
                ON CONFLICT (source_key,raw_hash) DO UPDATE
                SET payload=EXCLUDED.payload
                """,
                (str(uuid4()), raw_hash),
            )

    with psycopg.connect(database_url) as connection:
        with pytest.raises(errors.CheckViolation):
            connection.execute(
                """
                UPDATE agent_dispatch_dlq SET payload='{}',claim_generation=2
                WHERE dlq_id=%s
                """,
                (first_id,),
            )


def test_dispatch_dlq_claim_and_resolution_are_cas_and_one_way(
    database_url: str,
) -> None:
    dlq_id = str(uuid4())
    with psycopg.connect(database_url) as connection:
        connection.execute(
            """
            INSERT INTO agent_dispatch_dlq(
              dlq_id,source_key,raw_hash,request_digest,error_code,payload,retry_status
            ) VALUES (%s,'redis:dispatch',%s,decode(repeat('61',32),'hex'),
                      'malformed_frame','{"raw":"YmFk"}','pending')
            """,
            (dlq_id, hashlib.sha256(b"bad").digest()),
        )
        connection.commit()

    barrier = threading.Barrier(2)

    def claim(worker: str) -> str:
        with psycopg.connect(database_url) as connection:
            barrier.wait(timeout=5)
            row = connection.execute(
                """
                UPDATE agent_dispatch_dlq
                SET retry_status='retrying',claim_generation=2,
                    claimed_by=%s,claimed_at=transaction_timestamp(),
                    claim_expires_at=transaction_timestamp() + interval '5 minutes'
                WHERE dlq_id=%s AND retry_status='pending' AND claim_generation=1
                RETURNING claimed_by
                """,
                (worker, dlq_id),
            ).fetchone()
            connection.commit()
            return worker if row else "lost"

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(claim, ("repair-a", "repair-b")))
    assert outcomes.count("lost") == 1
    winner = next(item for item in outcomes if item != "lost")

    with psycopg.connect(database_url) as connection:
        connection.execute(
            """
            UPDATE agent_dispatch_dlq
            SET retry_status='resolved',resolved_at=transaction_timestamp(),
                claim_generation=3
            WHERE dlq_id=%s AND retry_status='retrying'
              AND claim_generation=2 AND claimed_by=%s
            """,
            (dlq_id, winner),
        )
        connection.commit()

    for statement in (
        "UPDATE agent_dispatch_dlq SET retry_status='retrying',resolved_at=NULL,claim_generation=4 WHERE dlq_id=%s",
        "DELETE FROM agent_dispatch_dlq WHERE dlq_id=%s",
    ):
        with psycopg.connect(database_url) as connection:
            with pytest.raises(errors.CheckViolation):
                connection.execute(statement, (dlq_id,))


def test_dispatch_dlq_expired_claim_is_recovered_and_old_worker_is_fenced(
    database_url: str,
) -> None:
    dlq_id = str(uuid4())
    with psycopg.connect(database_url) as connection:
        connection.execute(
            """
            INSERT INTO agent_dispatch_dlq(
              dlq_id,source_key,raw_hash,request_digest,error_code,payload,retry_status
            ) VALUES (%s,'redis:dispatch',%s,decode(repeat('61',32),'hex'),
                      'malformed_frame','{"raw":"Y3Jhc2g="}','pending')
            """,
            (dlq_id, hashlib.sha256(b"crash").digest()),
        )
        connection.execute(
            """
            UPDATE agent_dispatch_dlq
            SET retry_status='retrying',claim_generation=2,
                claimed_by='repair-old',claimed_at=transaction_timestamp(),
                claim_expires_at=transaction_timestamp() + interval '100 milliseconds'
            WHERE dlq_id=%s AND retry_status='pending' AND claim_generation=1
            """,
            (dlq_id,),
        )
        connection.commit()

    time.sleep(0.2)
    barrier = threading.Barrier(2)

    def reclaim(worker: str) -> str:
        with psycopg.connect(database_url) as connection:
            barrier.wait(timeout=5)
            row = connection.execute(
                """
                UPDATE agent_dispatch_dlq
                SET claim_generation=3,claimed_by=%s,
                    claimed_at=transaction_timestamp(),
                    claim_expires_at=transaction_timestamp() + interval '5 minutes'
                WHERE dlq_id=%s AND retry_status='retrying'
                  AND claim_generation=2
                RETURNING claimed_by
                """,
                (worker, dlq_id),
            ).fetchone()
            connection.commit()
            return worker if row else "lost"

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(reclaim, ("repair-new-a", "repair-new-b")))
    assert outcomes.count("lost") == 1
    winner = next(item for item in outcomes if item != "lost")

    with psycopg.connect(database_url) as connection:
        assert connection.execute(
            """
            UPDATE agent_dispatch_dlq
            SET retry_status='resolved',resolved_at=transaction_timestamp(),
                claim_generation=3
            WHERE dlq_id=%s AND claim_generation=2 AND claimed_by='repair-old'
            RETURNING dlq_id
            """,
            (dlq_id,),
        ).fetchone() is None
        connection.execute(
            """
            UPDATE agent_dispatch_dlq
            SET retry_status='resolved',resolved_at=transaction_timestamp(),
                claim_generation=4
            WHERE dlq_id=%s AND retry_status='retrying'
              AND claim_generation=3 AND claimed_by=%s
            """,
            (dlq_id, winner),
        )
        connection.commit()

    with psycopg.connect(database_url) as connection:
        assert connection.execute(
            """
            SELECT retry_status,claim_generation,claimed_by
            FROM agent_dispatch_dlq WHERE dlq_id=%s
            """,
            (dlq_id,),
        ).fetchone() == ("resolved", 4, winner)


def test_control_superseded_is_persisted_as_existing_rejected_semantics(
    database_url: str,
) -> None:
    with psycopg.connect(database_url) as connection:
        comment = connection.execute(
            """
            SELECT obj_description('kokoro.agent_control_inbox'::regclass,'pg_class')
            """
        ).fetchone()[0]
        constraint = connection.execute(
            """
            SELECT pg_get_constraintdef(oid)
            FROM pg_constraint
            WHERE conrelid='kokoro.agent_control_inbox'::regclass
              AND conname='agent_control_inbox_status_ck'
            """
        ).fetchone()[0]
    assert "superseded" in comment
    assert "rejected" in comment
    assert "agent_run_lease" in comment
    assert "superseded" not in constraint


def test_run_lease_is_the_single_dispatch_and_control_owner_with_crash_reclaim(
    database_url: str,
) -> None:
    control_id = str(uuid4())
    with psycopg.connect(database_url) as connection:
        _seed_manifested_running_run(connection, start_running=False)
        connection.execute(
            """
            INSERT INTO agent_control_inbox(
              control_id,agent_run_id,command_id,request_digest,
              command_schema_version,command_payload,status
            ) VALUES (%s,%s,%s,decode('aa','hex'),1,
                      '{"control_kind":"cancel"}','pending')
            """,
            (control_id, RUN_ID, str(uuid4())),
        )
        connection.commit()

    barrier = threading.Barrier(2)

    def claim_dispatch(worker: str) -> bool:
        with psycopg.connect(database_url) as connection:
            barrier.wait(timeout=5)
            claimed = connection.execute(
                """
                UPDATE agent_run SET state='running'
                WHERE agent_run_id=%s AND state='queued'
                RETURNING agent_run_id
                """,
                (RUN_ID,),
            ).fetchone()
            if claimed is not None:
                connection.execute(
                    """
                    INSERT INTO agent_run_lease(
                      agent_run_id,worker_id,lease_token_hash,leased_until,generation
                    ) VALUES (%s,%s,decode(repeat('31',32),'hex'),
                              transaction_timestamp()+interval '1 millisecond',1)
                    """,
                    (RUN_ID, worker),
                )
            connection.commit()
            return claimed is not None

    with ThreadPoolExecutor(max_workers=2) as pool:
        winners = list(pool.map(claim_dispatch, ("worker-a", "worker-b")))
    assert winners.count(True) == 1
    time.sleep(0.01)

    reclaim_barrier = threading.Barrier(2)

    def reclaim(worker: str) -> bool:
        with psycopg.connect(database_url) as connection:
            reclaim_barrier.wait(timeout=5)
            row = connection.execute(
                """
                UPDATE agent_run_lease
                SET worker_id=%s,lease_token_hash=decode(repeat('41',32),'hex'),
                    leased_until=transaction_timestamp()+interval '1 minute',
                    generation=2
                WHERE agent_run_id=%s AND generation=1
                  AND leased_until <= transaction_timestamp()
                RETURNING worker_id
                """,
                (worker, RUN_ID),
            ).fetchone()
            connection.commit()
            return row is not None

    with ThreadPoolExecutor(max_workers=2) as pool:
        reclaimed = list(pool.map(reclaim, ("worker-c", "worker-d")))
    assert reclaimed.count(True) == 1

    with psycopg.connect(database_url) as connection:
        owner = connection.execute(
            "SELECT worker_id FROM agent_run_lease WHERE agent_run_id=%s",
            (RUN_ID,),
        ).fetchone()[0]
        assert connection.execute(
            """
            UPDATE agent_control_inbox c
            SET status='applied',applied_at=transaction_timestamp()
            FROM agent_run_lease l
            WHERE c.control_id=%s AND c.status='pending'
              AND l.agent_run_id=c.agent_run_id AND l.worker_id='stale-worker'
              AND l.generation=1 AND l.leased_until>transaction_timestamp()
            RETURNING c.control_id
            """,
            (control_id,),
        ).fetchone() is None
        applied = connection.execute(
            """
            UPDATE agent_control_inbox c
            SET status='applied',applied_at=transaction_timestamp()
            FROM agent_run_lease l
            WHERE c.control_id=%s AND c.status='pending'
              AND l.agent_run_id=c.agent_run_id AND l.worker_id=%s
              AND l.generation=2 AND l.leased_until>transaction_timestamp()
            RETURNING c.control_id
            """,
            (control_id, owner),
        ).fetchone()
        assert applied is not None and str(applied[0]) == control_id


def test_dispatch_publish_attempt_is_a_pre_io_cas_and_recovers_after_deadline(
    database_url: str,
) -> None:
    outbox_id = str(uuid4())
    with psycopg.connect(database_url) as connection:
        _insert_run(connection)
        connection.execute(
            """
            INSERT INTO agent_dispatch_outbox(outbox_id,agent_run_id,manifest_digest)
            VALUES (%s,%s,decode(repeat('aa',32),'hex'))
            """,
            (outbox_id, RUN_ID),
        )
        connection.commit()

    barrier = threading.Barrier(2)

    def publish_claim(expected: int, lease: str) -> int | None:
        with psycopg.connect(database_url) as connection:
            barrier.wait(timeout=5)
            row = connection.execute(
                """
                UPDATE agent_dispatch_outbox
                SET attempt=attempt+1,
                    next_attempt_at=transaction_timestamp()+(%s)::interval
                WHERE outbox_id=%s AND dispatched_at IS NULL
                  AND attempt=%s AND next_attempt_at<=transaction_timestamp()
                RETURNING attempt
                """,
                (lease, outbox_id, expected),
            ).fetchone()
            connection.commit()
            return None if row is None else row[0]

    with ThreadPoolExecutor(max_workers=2) as pool:
        attempts = list(pool.map(lambda _: publish_claim(0, "1 millisecond"), range(2)))
    assert sorted(a for a in attempts if a is not None) == [1]
    time.sleep(0.01)

    barrier = threading.Barrier(2)
    with ThreadPoolExecutor(max_workers=2) as pool:
        retries = list(pool.map(lambda _: publish_claim(1, "1 minute"), range(2)))
    assert sorted(a for a in retries if a is not None) == [2]

    with psycopg.connect(database_url) as connection:
        assert connection.execute(
            """
            UPDATE agent_dispatch_outbox SET dispatched_at=transaction_timestamp()
            WHERE outbox_id=%s AND attempt=2 AND dispatched_at IS NULL
            RETURNING attempt
            """,
            (outbox_id,),
        ).fetchone() == (2,)
        connection.commit()
        table_comment = connection.execute(
            "SELECT obj_description('kokoro.agent_dispatch_outbox'::regclass,'pg_class')"
        ).fetchone()[0]
        lease_comment = connection.execute(
            "SELECT obj_description('kokoro.agent_run_lease'::regclass,'pg_class')"
        ).fetchone()[0]
    assert "before I/O" in table_comment
    assert "sole durable worker claim" in lease_comment


def test_event_republish_attempt_clock_is_monotonic_and_stops_after_ack(
    database_url: str,
) -> None:
    with psycopg.connect(database_url) as connection:
        _insert_run(connection)
        _append_event(connection, epoch=1, seq=1)
        _publish_event(connection, seq=1)
        connection.commit()

    with psycopg.connect(database_url) as connection:
        connection.execute(
            """
            UPDATE agent_event_outbox
            SET last_publish_attempt_at=transaction_timestamp(),publish_attempt=2
            WHERE agent_run_id=%s AND seq=1
            """,
            (RUN_ID,),
        )
        connection.commit()
        assert connection.execute(
            """
            SELECT publish_attempt,published_at,last_publish_attempt_at
            FROM agent_event_outbox WHERE agent_run_id=%s AND seq=1
            """,
            (RUN_ID,),
        ).fetchone()[0] == 2

        connection.execute(
            """
            INSERT INTO agent_projection_ack(
              agent_run_id,consumer,projected_epoch,projected_seq
            ) VALUES (%s,'chat',1,1)
            """,
            (RUN_ID,),
        )
        connection.execute(
            """
            UPDATE agent_event_outbox SET acked_at=transaction_timestamp()
            WHERE agent_run_id=%s AND seq=1
            """,
            (RUN_ID,),
        )
        connection.commit()

    with psycopg.connect(database_url) as connection:
        with pytest.raises(errors.CheckViolation):
            connection.execute(
                """
                UPDATE agent_event_outbox
                SET last_publish_attempt_at=transaction_timestamp(),publish_attempt=3
                WHERE agent_run_id=%s AND seq=1
                """,
                (RUN_ID,),
            )


def test_event_republish_attempt_clock_stops_at_the_first_nack(
    database_url: str,
) -> None:
    with psycopg.connect(database_url) as connection:
        _insert_run(connection)
        _append_event(connection, epoch=1, seq=1)
        _publish_event(connection, seq=1)
        connection.execute(
            """
            INSERT INTO agent_projection_ack(
              agent_run_id,consumer,projected_epoch,projected_seq,
              rejected_seq,rejection_code,rejected_at
            ) VALUES (%s,'chat',1,0,1,'poison',transaction_timestamp())
            """,
            (RUN_ID,),
        )
        connection.commit()

    with psycopg.connect(database_url) as connection:
        with pytest.raises(errors.CheckViolation):
            connection.execute(
                """
                UPDATE agent_event_outbox
                SET last_publish_attempt_at=transaction_timestamp(),publish_attempt=2
                WHERE agent_run_id=%s AND seq=1
                """,
                (RUN_ID,),
            )


def test_admission_failure_rejects_late_or_precreated_execution_manifest(
    database_url: str,
) -> None:
    with psycopg.connect(database_url) as connection:
        _seed_tenant(connection)
        _seed_published_model(connection)
        connection.execute(
            """
            INSERT INTO capability_runtime_snapshot(
              snapshot_id,organization_id,scope_key,digest
            ) VALUES (%s,%s,'org/a',decode(repeat('12',32),'hex'))
            """,
            (SNAPSHOT_ID, ORG_ID),
        )
        _insert_run(connection)
        connection.execute(
            """
            UPDATE agent_run
            SET state='admission_failed',terminal_at=transaction_timestamp()
            WHERE agent_run_id=%s
            """,
            (RUN_ID,),
        )
        connection.commit()

    manifest_sql = """
        INSERT INTO agent_execution_manifest(
          execution_manifest_id,agent_run_id,namespace,digest,
          agent_preset_key,agent_preset_digest,model_revision_id,
          capability_snapshot_id,usage_mode,usage_policy_digest,payload
        ) VALUES (%s,%s,'org/a',decode(repeat('21',32),'hex'),
          'general',decode(repeat('22',32),'hex'),%s,%s,
          'unmetered',decode(repeat('23',32),'hex'),'{}')
    """
    with psycopg.connect(database_url) as connection:
        with pytest.raises(errors.CheckViolation):
            connection.execute(
                manifest_sql,
                (MANIFEST_ID, RUN_ID, PUBLISHED_REVISION_ID, SNAPSHOT_ID),
            )

    with psycopg.connect(database_url) as connection:
        _insert_run(connection, run_id=RUN_2_ID)
        second_manifest_id = str(uuid4())
        connection.execute(
            manifest_sql,
            (second_manifest_id, RUN_2_ID, PUBLISHED_REVISION_ID, SNAPSHOT_ID),
        )
        connection.execute(
            """
            UPDATE agent_run
            SET state='admission_failed',terminal_at=transaction_timestamp()
            WHERE agent_run_id=%s
            """,
            (RUN_2_ID,),
        )
        with pytest.raises(errors.CheckViolation):
            connection.commit()


@pytest.mark.parametrize(
    "counter",
    [
        "usage_input_tokens",
        "usage_output_tokens",
        "usage_cached_tokens",
        "usage_call_count",
        "budget_tokens_used",
    ],
)
def test_admission_failure_rejects_preterminal_usage_or_budget(
    database_url: str,
    counter: str,
) -> None:
    with psycopg.connect(database_url) as connection:
        _insert_run(connection)
        connection.execute(
            f"UPDATE agent_run SET {counter}=1 WHERE agent_run_id=%s",
            (RUN_ID,),
        )
        connection.execute(
            """
            UPDATE agent_run
            SET state='admission_failed',terminal_at=transaction_timestamp()
            WHERE agent_run_id=%s
            """,
            (RUN_ID,),
        )
        with pytest.raises(errors.CheckViolation):
            connection.commit()


def test_agent_run_identity_cannot_be_deleted_and_recreated(database_url: str) -> None:
    launch_id = str(uuid4())
    with psycopg.connect(database_url) as connection:
        _insert_run(connection, launch_id=launch_id)
        connection.commit()
        with pytest.raises(errors.CheckViolation):
            connection.execute(
                "DELETE FROM agent_run WHERE agent_run_id=%s",
                (RUN_ID,),
            )
        connection.rollback()
        stored_launch = connection.execute(
            "SELECT launch_id FROM agent_run WHERE agent_run_id=%s",
            (RUN_ID,),
        ).fetchone()
        assert stored_launch is not None and str(stored_launch[0]) == launch_id


def test_projection_first_nack_cannot_be_deleted_to_reopen_publication(
    database_url: str,
) -> None:
    with psycopg.connect(database_url) as connection:
        _insert_run(connection)
        _append_event(connection, epoch=1, seq=1)
        _publish_event(connection, seq=1)
        connection.execute(
            """
            INSERT INTO agent_projection_ack(
              agent_run_id,consumer,projected_epoch,projected_seq,
              rejected_seq,rejection_code,rejected_at
            ) VALUES (%s,'chat',1,0,1,'poison',transaction_timestamp())
            """,
            (RUN_ID,),
        )
        connection.commit()

    with psycopg.connect(database_url) as connection:
        with pytest.raises(errors.CheckViolation):
            connection.execute(
                """
                DELETE FROM agent_projection_ack
                WHERE agent_run_id=%s AND consumer='chat'
                """,
                (RUN_ID,),
            )


def test_projection_zero_watermark_cannot_be_relabelled_to_a_new_epoch(
    database_url: str,
) -> None:
    with psycopg.connect(database_url) as connection:
        _insert_run(connection)
        _append_event(connection, epoch=1, seq=1)
        _publish_event(connection, seq=1)
        connection.execute(
            """
            INSERT INTO agent_projection_ack(
              agent_run_id,consumer,projected_epoch,projected_seq
            ) VALUES (%s,'chat',1,0)
            """,
            (RUN_ID,),
        )
        connection.execute(
            "UPDATE agent_run SET epoch=2 WHERE agent_run_id=%s",
            (RUN_ID,),
        )
        connection.commit()

    with psycopg.connect(database_url) as connection:
        with pytest.raises(errors.CheckViolation):
            connection.execute(
                """
                UPDATE agent_projection_ack
                SET projected_epoch=2,generation=2
                WHERE agent_run_id=%s AND consumer='chat' AND generation=1
                """,
                (RUN_ID,),
            )
        connection.rollback()
        assert connection.execute(
            """
            UPDATE agent_projection_ack
            SET projected_seq=1,generation=2
            WHERE agent_run_id=%s AND consumer='chat' AND generation=1
            RETURNING projected_epoch,projected_seq
            """,
            (RUN_ID,),
        ).fetchone() == (1, 1)
