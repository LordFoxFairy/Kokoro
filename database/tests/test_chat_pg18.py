from __future__ import annotations

import argparse
import os
import sys
from uuid import UUID
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

import psycopg
import pytest
from psycopg import errors

sys.path.insert(0, str(Path(__file__).parent))
from pg18 import apply_sql, run_pg18_case, segment_prefix  # noqa: E402

SITE_A = "10000000-0000-0000-0000-000000000001"
SITE_B = "10000000-0000-0000-0000-000000000002"
PRINCIPAL_A = "20000000-0000-0000-0000-000000000001"
PRINCIPAL_B = "20000000-0000-0000-0000-000000000002"
PRINCIPAL_C = "20000000-0000-0000-0000-000000000003"
ORG_A = "30000000-0000-0000-0000-000000000001"
ORG_B = "30000000-0000-0000-0000-000000000002"
ORG_C = "30000000-0000-0000-0000-000000000003"
CONV_A = "40000000-0000-0000-0000-000000000001"
CONV_B = "40000000-0000-0000-0000-000000000002"
CONV_C = "40000000-0000-0000-0000-000000000003"
CONV_D = "40000000-0000-0000-0000-000000000004"
MSG_A = "50000000-0000-0000-0000-000000000001"
MSG_B = "50000000-0000-0000-0000-000000000002"
LAUNCH_A = "60000000-0000-0000-0000-000000000001"
LAUNCH_B = "60000000-0000-0000-0000-000000000002"
RUN_A = "70000000-0000-0000-0000-000000000001"
RUN_B = "70000000-0000-0000-0000-000000000002"
INTERACTION_A = "80000000-0000-0000-0000-000000000001"
INTERACTION_B = "80000000-0000-0000-0000-000000000002"
INTERACTION_C = "80000000-0000-0000-0000-000000000003"


def db_url() -> str:
    return os.environ["KOKORO_TEST_DATABASE_URL"]


def seed_tenants(connection: psycopg.Connection[tuple[object, ...]]) -> None:
    connection.execute(
        """
        INSERT INTO site_site(site_id,key,name,status,default_locale,timezone)
        VALUES (%s,'a','A','active','en-US','UTC'),
               (%s,'b','B','active','en-US','UTC')
        """,
        (SITE_A, SITE_B),
    )
    connection.execute(
        """
        INSERT INTO iam_principal(principal_id,principal_scope,site_id,kind,status)
        VALUES (%s,'site',%s,'user','active'),
               (%s,'site',%s,'user','active'),
               (%s,'site',%s,'user','active')
        """,
        (PRINCIPAL_A, SITE_A, PRINCIPAL_B, SITE_A, PRINCIPAL_C, SITE_B),
    )
    connection.execute(
        """
        INSERT INTO iam_organization(organization_id,site_id,kind,name,status)
        VALUES (%s,%s,'team','A','active'),
               (%s,%s,'team','B','active'),
               (%s,%s,'team','C','active')
        """,
        (ORG_A, SITE_A, ORG_B, SITE_A, ORG_C, SITE_B),
    )


def seed_conversations(connection: psycopg.Connection[tuple[object, ...]]) -> None:
    seed_tenants(connection)
    connection.execute(
        """
        INSERT INTO chat_conversation(
          conversation_id,organization_id,site_id,created_by_principal_id,
          title,agent_namespace,state
        ) VALUES
          (%s,%s,%s,%s,'A','org/a/conversation/a','active'),
          (%s,%s,%s,%s,'B','org/b/conversation/b','active'),
          (%s,%s,%s,%s,'C','org/c/conversation/c','active')
        """,
        (
            CONV_A, ORG_A, SITE_A, PRINCIPAL_A,
            CONV_B, ORG_B, SITE_A, PRINCIPAL_B,
            CONV_C, ORG_C, SITE_B, PRINCIPAL_C,
        ),
    )


def insert_message(connection: psycopg.Connection[tuple[object, ...]], message: str, conversation: str, ordinal: int) -> None:
    connection.execute(
        """
        INSERT INTO chat_message(message_id,conversation_id,role,status,ordinal)
        VALUES (%s,%s,'user','complete',%s)
        """,
        (message, conversation, ordinal),
    )


def insert_launch(connection: psycopg.Connection[tuple[object, ...]], launch: str, conversation: str, message: str) -> None:
    assistant = str(UUID(int=(UUID(launch).int + 0x1000) % (1 << 128)))
    ordinal = connection.execute(
        "SELECT coalesce(max(ordinal),0)+1 FROM chat_message WHERE conversation_id=%s",
        (conversation,),
    ).fetchone()[0]
    connection.execute(
        """
        INSERT INTO chat_message(message_id,conversation_id,role,status,ordinal)
        VALUES (%s,%s,'assistant','complete',%s)
        """,
        (assistant, conversation, ordinal),
    )
    connection.execute(
        """
        INSERT INTO chat_run_launch(
          launch_id,conversation_id,user_message_id,assistant_message_id,state
        ) VALUES (%s,%s,%s,%s,'submitted')
        """,
        (launch, conversation, message, assistant),
    )


def case_exact_catalog() -> None:
    expected = {
        "chat_conversation", "chat_message", "chat_message_part",
        "chat_command_receipt", "chat_run_launch", "chat_active_run",
        "chat_run_view", "chat_interaction", "chat_control_command",
        "chat_control_outbox", "chat_launch_outbox", "chat_projection_inbox",
        "chat_projection_dlq", "chat_stream_event",
    }
    with psycopg.connect(db_url()) as connection:
        actual = {row[0] for row in connection.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname='kokoro' AND tablename LIKE 'chat_%'"
        )}
        definitions = dict(connection.execute(
            "SELECT conname,pg_get_constraintdef(oid) FROM pg_constraint WHERE connamespace='kokoro'::regnamespace"
        ).fetchall())
    assert actual == expected
    assert definitions["chat_conversation_conversation_organization_key"] == "UNIQUE (conversation_id, organization_id)"
    assert definitions["chat_conversation_conversation_site_key"] == "UNIQUE (conversation_id, site_id)"
    assert definitions["chat_message_message_conversation_key"] == "UNIQUE (message_id, conversation_id)"
    assert definitions["chat_run_launch_launch_conversation_key"] == "UNIQUE (launch_id, conversation_id)"
    assert definitions["chat_command_receipt_organization_command_key"] == "UNIQUE (organization_id, command_id)"
    assert definitions["chat_stream_event_conversation_seq_key"] == "UNIQUE (conversation_id, seq)"
    assert definitions["chat_stream_event_conversation_event_key"] == "UNIQUE (conversation_id, event_id)"


def case_message_parent_scope() -> None:
    with psycopg.connect(db_url()) as connection:
        seed_conversations(connection)
        insert_message(connection, MSG_A, CONV_A, 1)
        connection.commit()
        with pytest.raises(errors.ForeignKeyViolation) as raised:
            connection.execute(
                """
                INSERT INTO chat_message(message_id,conversation_id,parent_message_id,role,status,ordinal)
                VALUES (%s,%s,%s,'assistant','complete',1)
                """,
                (MSG_B, CONV_B, MSG_A),
            )
        assert raised.value.diag.constraint_name == "chat_message_parent_conversation_fk"
        connection.rollback()
        assert connection.execute("SELECT count(*) FROM chat_message WHERE message_id=%s", (MSG_B,)).fetchone()[0] == 0


def case_conversation_tenant_scope() -> None:
    with psycopg.connect(db_url()) as connection:
        seed_tenants(connection)
        connection.commit()
        with pytest.raises(errors.ForeignKeyViolation) as organization_scope:
            connection.execute(
                """
                INSERT INTO chat_conversation(
                  conversation_id,organization_id,site_id,created_by_principal_id,
                  title,agent_namespace,state
                ) VALUES (%s,%s,%s,%s,'bad','bad/org','active')
                """,
                (CONV_A, ORG_A, SITE_B, PRINCIPAL_C),
            )
        assert organization_scope.value.diag.constraint_name == "chat_conversation_organization_site_fk"
        connection.rollback()
        with pytest.raises(errors.ForeignKeyViolation) as principal_scope:
            connection.execute(
                """
                INSERT INTO chat_conversation(
                  conversation_id,organization_id,site_id,created_by_principal_id,
                  title,agent_namespace,state
                ) VALUES (%s,%s,%s,%s,'bad','bad/principal','active')
                """,
                (CONV_A, ORG_A, SITE_A, PRINCIPAL_C),
            )
        assert principal_scope.value.diag.constraint_name == "chat_conversation_principal_site_fk"
        connection.rollback()
        assert connection.execute("SELECT count(*) FROM chat_conversation").fetchone()[0] == 0

        connection.execute(
            """
            INSERT INTO chat_conversation(
              conversation_id,organization_id,site_id,created_by_principal_id,
              title,agent_namespace,state
            ) VALUES (%s,%s,%s,%s,'A','immutable/conversation/a','active'),
                     (%s,%s,%s,%s,'B','immutable/conversation/b','active')
            """,
            (CONV_A, ORG_A, SITE_A, PRINCIPAL_A, CONV_B, ORG_B, SITE_A, PRINCIPAL_B),
        )
        insert_message(connection, MSG_A, CONV_A, 1)
        connection.commit()
        with pytest.raises(errors.CheckViolation) as conversation_identity:
            connection.execute(
                """
                UPDATE chat_conversation
                SET organization_id=%s,site_id=%s,created_by_principal_id=%s
                WHERE conversation_id=%s
                """,
                (ORG_C, SITE_B, PRINCIPAL_C, CONV_A),
            )
        assert conversation_identity.value.diag.constraint_name == "chat_conversation_identity_immutable_ck"
        connection.rollback()
        with pytest.raises(errors.CheckViolation) as message_identity:
            connection.execute(
                "UPDATE chat_message SET conversation_id=%s WHERE message_id=%s",
                (CONV_B, MSG_A),
            )
        assert message_identity.value.diag.constraint_name == "chat_message_identity_immutable_ck"


def case_launch_message_scope() -> None:
    with psycopg.connect(db_url()) as connection:
        seed_conversations(connection)
        insert_message(connection, MSG_A, CONV_A, 1)
        insert_message(connection, MSG_B, CONV_B, 1)
        connection.commit()
        with pytest.raises(errors.ForeignKeyViolation) as raised:
            connection.execute(
                """
                INSERT INTO chat_run_launch(launch_id,conversation_id,user_message_id,assistant_message_id,state)
                VALUES (%s,%s,%s,%s,'submitted')
                """,
                (LAUNCH_A, CONV_A, MSG_B, MSG_A),
            )
        assert raised.value.diag.constraint_name == "chat_run_launch_user_message_conversation_fk"
        connection.rollback()
        with pytest.raises(errors.ForeignKeyViolation) as assistant:
            connection.execute(
                """
                INSERT INTO chat_run_launch(launch_id,conversation_id,user_message_id,assistant_message_id,state)
                VALUES (%s,%s,%s,%s,'submitted')
                """,
                (LAUNCH_A, CONV_A, MSG_A, MSG_B),
            )
        assert assistant.value.diag.constraint_name == "chat_run_launch_assistant_message_conversation_fk"
        connection.rollback()
        assert connection.execute("SELECT count(*) FROM chat_run_launch").fetchone()[0] == 0
        assistant_id = "50000000-0000-0000-0000-000000000003"
        connection.execute(
            """
            INSERT INTO chat_message(message_id,conversation_id,role,status,ordinal)
            VALUES (%s,%s,'assistant','complete',2)
            """,
            (assistant_id, CONV_A),
        )
        connection.execute(
            """
            INSERT INTO chat_run_launch(
              launch_id,conversation_id,user_message_id,assistant_message_id,
              requested_model_ref,state
            ) VALUES (%s,%s,%s,%s,'model-a','accepted')
            """,
            (LAUNCH_A, CONV_A, MSG_A, assistant_id),
        )
        connection.commit()
        with pytest.raises(errors.CheckViolation) as immutable:
            connection.execute(
                "UPDATE chat_run_launch SET requested_model_ref='model-b' WHERE launch_id=%s",
                (LAUNCH_A,),
            )
        assert immutable.value.diag.constraint_name == "chat_run_launch_accepted_immutable_ck"


def case_required_assistant_and_state_transitions() -> None:
    with psycopg.connect(db_url()) as connection:
        seed_conversations(connection)
        insert_message(connection, MSG_A, CONV_A, 1)
        connection.commit()
        with pytest.raises(errors.NotNullViolation) as missing_assistant:
            connection.execute(
                """
                INSERT INTO chat_run_launch(launch_id,conversation_id,user_message_id,state)
                VALUES (%s,%s,%s,'submitted')
                """,
                (LAUNCH_A, CONV_A, MSG_A),
            )
        assert missing_assistant.value.diag.column_name == "assistant_message_id"
        connection.rollback()
        assistant_id = "50000000-0000-0000-0000-000000000004"
        connection.execute(
            """
            INSERT INTO chat_message(message_id,conversation_id,role,status,ordinal)
            VALUES (%s,%s,'assistant','complete',2)
            """,
            (assistant_id, CONV_A),
        )
        connection.execute(
            """
            INSERT INTO chat_run_launch(
              launch_id,conversation_id,user_message_id,assistant_message_id,state
            ) VALUES (%s,%s,%s,%s,'accepted')
            """,
            (LAUNCH_A, CONV_A, MSG_A, assistant_id),
        )
        connection.commit()
        with pytest.raises(errors.CheckViolation) as launch_resurrection:
            connection.execute(
                "UPDATE chat_run_launch SET state='submitted' WHERE launch_id=%s",
                (LAUNCH_A,),
            )
        assert launch_resurrection.value.diag.constraint_name == "chat_run_launch_accepted_immutable_ck"
        connection.rollback()
        connection.execute(
            """
            INSERT INTO chat_run_view(
              agent_run_id,launch_id,conversation_id,epoch,state,received_seq,projected_seq
            ) VALUES (%s,%s,%s,1,'paused',1,1)
            """,
            (RUN_A, LAUNCH_A, CONV_A),
        )
        connection.execute(
            """
            INSERT INTO chat_interaction(
              interaction_id,agent_run_id,conversation_id,kind,action_digest,
              schema_version,payload,status
            ) VALUES (%s,%s,%s,'approval',decode('aa','hex'),1,'{}','resolved')
            """,
            (INTERACTION_A, RUN_A, CONV_A),
        )
        connection.commit()
        with pytest.raises(errors.CheckViolation) as interaction_resurrection:
            connection.execute(
                "UPDATE chat_interaction SET status='pending' WHERE interaction_id=%s",
                (INTERACTION_A,),
            )
        assert interaction_resurrection.value.diag.constraint_name == "chat_interaction_terminal_immutable_ck"
        connection.rollback()
        rejected_assistant = "50000000-0000-0000-0000-000000000005"
        connection.execute(
            """
            INSERT INTO chat_message(message_id,conversation_id,role,status,ordinal)
            VALUES (%s,%s,'assistant','complete',3)
            """,
            (rejected_assistant, CONV_A),
        )
        connection.execute(
            """
            INSERT INTO chat_run_launch(
              launch_id,conversation_id,user_message_id,assistant_message_id,
              requested_model_ref,state
            ) VALUES (%s,%s,%s,%s,'model-a','rejected')
            """,
            (LAUNCH_B, CONV_A, MSG_A, rejected_assistant),
        )
        connection.commit()
        with pytest.raises(errors.CheckViolation) as rejected_identity:
            connection.execute(
                """
                UPDATE chat_run_launch SET requested_model_ref='model-b'
                WHERE launch_id=%s
                """,
                (LAUNCH_B,),
            )
        assert rejected_identity.value.diag.constraint_name == "chat_run_launch_accepted_immutable_ck"


def case_active_run_race() -> None:
    with psycopg.connect(db_url()) as connection:
        seed_conversations(connection)
        insert_message(connection, MSG_A, CONV_A, 1)
        insert_launch(connection, LAUNCH_A, CONV_A, MSG_A)
        insert_launch(connection, LAUNCH_B, CONV_A, MSG_A)
        connection.commit()
    barrier = Barrier(2)

    def claim(launch: str) -> str:
        with psycopg.connect(db_url()) as connection:
            connection.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
            barrier.wait()
            try:
                connection.execute(
                    "INSERT INTO chat_active_run(conversation_id,launch_id) VALUES (%s,%s)",
                    (CONV_A, launch),
                )
                connection.commit()
                return "committed"
            except (errors.UniqueViolation, errors.SerializationFailure) as error:
                constraint = error.diag.constraint_name
                connection.rollback()
                return constraint or "serialization_conflict"

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(claim, (LAUNCH_A, LAUNCH_B)))
    assert outcomes.count("committed") == 1
    assert set(outcomes) <= {"committed", "chat_active_run_pk", "serialization_conflict"}
    with psycopg.connect(db_url()) as connection:
        assert connection.execute("SELECT count(*) FROM chat_active_run").fetchone()[0] == 1


class DigestConflict(Exception):
    pass


def case_receipt_scope_replay_and_effect() -> None:
    command = "90000000-0000-0000-0000-000000000001"
    with psycopg.connect(db_url()) as connection:
        seed_conversations(connection)
        connection.commit()

    def claim(org: str, site: str, conversation: str, receipt: str, effect: str, digest: str) -> tuple[str, str]:
        with psycopg.connect(db_url()) as connection:
            inserted = connection.execute(
                """
                INSERT INTO chat_command_receipt(
                  receipt_id,site_id,organization_id,conversation_id,command_id,
                  command_kind,request_digest,status
                ) VALUES (%s,%s,%s,%s,%s,'AppendMessage',decode(%s,'hex'),'processing')
                ON CONFLICT (organization_id,command_id) DO NOTHING
                RETURNING receipt_id::text
                """,
                (receipt, site, org, conversation, command, digest),
            ).fetchone()
            if inserted:
                ordinal = connection.execute(
                    "SELECT count(*)+1 FROM chat_message WHERE conversation_id=%s", (conversation,)
                ).fetchone()[0]
                insert_message(connection, effect, conversation, ordinal)
                row = connection.execute(
                    """
                    UPDATE chat_command_receipt SET status='completed',result_ref=%s
                    WHERE receipt_id=%s RETURNING receipt_id::text,result_ref
                    """,
                    (effect, receipt),
                ).fetchone()
                connection.commit()
                return row
            existing = connection.execute(
                """
                SELECT receipt_id::text,result_ref,encode(request_digest,'hex')
                FROM chat_command_receipt WHERE organization_id=%s AND command_id=%s
                """,
                (org, command),
            ).fetchone()
            if existing[2] != digest:
                raise DigestConflict(command)
            connection.commit()
            return existing[0], existing[1]

    receipt_a = "90000000-0000-0000-0000-000000000011"
    effect_a = "90000000-0000-0000-0000-000000000012"
    first = claim(ORG_A, SITE_A, CONV_A, receipt_a, effect_a, "aa")
    assert claim(ORG_A, SITE_A, CONV_A, receipt_a, effect_a, "aa") == first
    with pytest.raises(DigestConflict):
        claim(ORG_A, SITE_A, CONV_A, receipt_a, effect_a, "bb")
    claim(
        ORG_B, SITE_A, CONV_B,
        "90000000-0000-0000-0000-000000000013",
        "90000000-0000-0000-0000-000000000014", "cc",
    )
    with psycopg.connect(db_url()) as connection:
        assert connection.execute("SELECT count(*) FROM chat_command_receipt WHERE command_id=%s", (command,)).fetchone()[0] == 2
        assert connection.execute("SELECT count(*) FROM chat_message").fetchone()[0] == 2
        with pytest.raises(errors.CheckViolation) as immutable:
            connection.execute(
                "UPDATE chat_command_receipt SET request_digest=decode('dd','hex') WHERE receipt_id=%s",
                (receipt_a,),
            )
        assert immutable.value.diag.constraint_name == "chat_command_receipt_claim_immutable_ck"


def case_global_sequence_allocation() -> None:
    with psycopg.connect(db_url()) as connection:
        seed_conversations(connection)
        connection.commit()
        rolled_back = connection.execute(
            "UPDATE chat_conversation SET next_stream_seq=next_stream_seq+1 WHERE conversation_id=%s RETURNING next_stream_seq-1",
            (CONV_A,),
        ).fetchone()[0]
        assert rolled_back == 1
        connection.rollback()
    barrier = Barrier(2)

    def allocate(event: str) -> int:
        with psycopg.connect(db_url()) as connection:
            barrier.wait()
            seq = connection.execute(
                "UPDATE chat_conversation SET next_stream_seq=next_stream_seq+1 WHERE conversation_id=%s RETURNING next_stream_seq-1",
                (CONV_A,),
            ).fetchone()[0]
            connection.execute(
                """
                INSERT INTO chat_stream_event(stream_event_id,conversation_id,seq,event_id,kind,schema_version,payload)
                VALUES (gen_random_uuid(),%s,%s,%s,'message',1,'{}')
                """,
                (CONV_A, seq, event),
            )
            connection.commit()
            return seq

    events = ("91000000-0000-0000-0000-000000000001", "91000000-0000-0000-0000-000000000002")
    with ThreadPoolExecutor(max_workers=2) as executor:
        allocated = list(executor.map(allocate, events))
    assert sorted(allocated) == [1, 2]
    with psycopg.connect(db_url()) as connection:
        assert connection.execute("SELECT next_stream_seq FROM chat_conversation WHERE conversation_id=%s", (CONV_A,)).fetchone()[0] == 3
        assert [r[0] for r in connection.execute("SELECT seq FROM chat_stream_event ORDER BY seq")] == [1, 2]
        connection.execute(
            """
            INSERT INTO chat_projection_inbox(inbox_id,producer,agent_run_id,epoch,producer_seq,event_id,schema_version,payload,status)
            VALUES (%s,'agent',%s,1,7,%s,1,'{}','pending')
            """,
            ("91000000-0000-0000-0000-000000000011", RUN_A, "91000000-0000-0000-0000-000000000012"),
        )
        connection.commit()
        with pytest.raises(errors.UniqueViolation) as duplicate:
            connection.execute(
                """
                INSERT INTO chat_projection_inbox(inbox_id,producer,agent_run_id,epoch,producer_seq,event_id,schema_version,payload,status)
                VALUES (%s,'agent',%s,2,7,%s,1,'{}','pending')
                """,
                ("91000000-0000-0000-0000-000000000013", RUN_A, "91000000-0000-0000-0000-000000000014"),
            )
        assert duplicate.value.diag.constraint_name == "chat_projection_inbox_producer_run_seq_key"
        connection.rollback()
        with pytest.raises(errors.CheckViolation) as claim_immutable:
            connection.execute(
                """
                UPDATE chat_projection_inbox SET epoch=2,producer_seq=8
                WHERE agent_run_id=%s
                """,
                (RUN_A,),
            )
        assert claim_immutable.value.diag.constraint_name == "chat_projection_inbox_claim_immutable_ck"
        connection.rollback()
        with pytest.raises(errors.CheckViolation) as regressed:
            connection.execute(
                "UPDATE chat_conversation SET next_stream_seq=2 WHERE conversation_id=%s",
                (CONV_A,),
            )
        assert regressed.value.diag.constraint_name == "chat_conversation_stream_seq_monotonic_ck"


def case_retention_snapshot() -> None:
    with psycopg.connect(db_url()) as connection:
        seed_conversations(connection)
        insert_message(connection, MSG_A, CONV_A, 1)
        connection.execute(
            """
            INSERT INTO chat_message_part(part_id,message_id,ordinal,kind,schema_version,payload,status)
            VALUES (%s,%s,1,'text',1,'{"text":"hello"}','complete')
            """,
            ("92000000-0000-0000-0000-000000000001", MSG_A),
        )
        insert_launch(connection, LAUNCH_A, CONV_A, MSG_A)
        connection.execute(
            """
            INSERT INTO chat_run_view(agent_run_id,launch_id,conversation_id,epoch,state,received_seq,projected_seq)
            VALUES (%s,%s,%s,1,'running',3,3)
            """,
            (RUN_A, LAUNCH_A, CONV_A),
        )
        connection.execute(
            """
            INSERT INTO chat_interaction(interaction_id,agent_run_id,conversation_id,kind,action_digest,schema_version,payload,status)
            VALUES (%s,%s,%s,'approval',decode('aa','hex'),1,'{"question":"continue"}','pending')
            """,
            (INTERACTION_A, RUN_A, CONV_A),
        )
        for seq in (1, 2, 3):
            connection.execute(
                """
                INSERT INTO chat_stream_event(stream_event_id,conversation_id,seq,event_id,kind,schema_version,payload)
                VALUES (gen_random_uuid(),%s,%s,gen_random_uuid(),'delta',1,'{}')
                """,
                (CONV_A, seq),
            )
        connection.execute("UPDATE chat_conversation SET next_stream_seq=4 WHERE conversation_id=%s", (CONV_A,))
        connection.execute(
            "INSERT INTO chat_active_run(conversation_id,launch_id) VALUES (%s,%s)",
            (CONV_A, LAUNCH_A),
        )
        connection.commit()
        connection.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
        watermark = connection.execute("SELECT next_stream_seq-1 FROM chat_conversation WHERE conversation_id=%s", (CONV_A,)).fetchone()[0]
        with psycopg.connect(db_url()) as cleanup:
            cleanup.execute("DELETE FROM chat_stream_event WHERE conversation_id=%s AND seq<=%s", (CONV_A, watermark))
            cleanup.commit()
        snapshot = (
            connection.execute("SELECT title,next_stream_seq-1 FROM chat_conversation WHERE conversation_id=%s", (CONV_A,)).fetchone(),
            connection.execute("SELECT role,status FROM chat_message WHERE conversation_id=%s ORDER BY ordinal", (CONV_A,)).fetchall(),
            connection.execute("SELECT payload FROM chat_message_part WHERE message_id=%s", (MSG_A,)).fetchall(),
            connection.execute("SELECT state,projected_seq FROM chat_run_view WHERE conversation_id=%s", (CONV_A,)).fetchall(),
            connection.execute("SELECT launch_id::text FROM chat_active_run WHERE conversation_id=%s", (CONV_A,)).fetchall(),
            connection.execute("SELECT status,payload FROM chat_interaction WHERE conversation_id=%s AND status='pending'", (CONV_A,)).fetchall(),
        )
        connection.commit()
        assert connection.execute("SELECT count(*) FROM chat_stream_event").fetchone()[0] == 0
        with pytest.raises(errors.CheckViolation) as immutable:
            connection.execute(
                "UPDATE chat_interaction SET payload='{}' WHERE interaction_id=%s",
                (INTERACTION_A,),
            )
        assert immutable.value.diag.constraint_name == "chat_interaction_payload_immutable_ck"
        connection.rollback()
    assert snapshot == (("A", 3), [("user", "complete"), ("assistant", "complete")], [({"text": "hello"},)], [("running", 3)], [(LAUNCH_A,)], [("pending", {"question": "continue"})])


def case_control_interaction_scope() -> None:
    with psycopg.connect(db_url()) as connection:
        seed_conversations(connection)
        connection.execute(
            """
            INSERT INTO chat_conversation(
              conversation_id,organization_id,site_id,created_by_principal_id,
              title,agent_namespace,state
            ) VALUES (%s,%s,%s,%s,'D','org/a/conversation/d','active')
            """,
            (CONV_D, ORG_A, SITE_A, PRINCIPAL_A),
        )
        for message, conversation, launch, run, interaction in (
            (MSG_A, CONV_A, LAUNCH_A, RUN_A, INTERACTION_A),
            (MSG_B, CONV_D, LAUNCH_B, RUN_B, INTERACTION_B),
            ("93000000-0000-0000-0000-000000000001", CONV_C, "93000000-0000-0000-0000-000000000002", "93000000-0000-0000-0000-000000000003", INTERACTION_C),
        ):
            insert_message(connection, message, conversation, 1)
            insert_launch(connection, launch, conversation, message)
            connection.execute(
                "INSERT INTO chat_run_view(agent_run_id,launch_id,conversation_id,epoch,state,received_seq,projected_seq) VALUES (%s,%s,%s,1,'paused',1,1)",
                (run, launch, conversation),
            )
            connection.execute(
                """
                INSERT INTO chat_interaction(interaction_id,agent_run_id,conversation_id,kind,action_digest,schema_version,payload,status)
                VALUES (%s,%s,%s,'approval',decode('aa','hex'),1,'{}','pending')
                """,
                (interaction, run, conversation),
            )
        receipt = "93000000-0000-0000-0000-000000000011"
        connection.execute(
            """
            INSERT INTO chat_command_receipt(receipt_id,site_id,organization_id,conversation_id,command_id,command_kind,request_digest,status)
            VALUES (%s,%s,%s,%s,%s,'DecideInteraction',decode('bb','hex'),'processing')
            """,
            (receipt, SITE_A, ORG_A, CONV_A, "93000000-0000-0000-0000-000000000012"),
        )
        connection.commit()
        with pytest.raises(errors.CheckViolation) as missing_interaction:
            connection.execute(
                """
                INSERT INTO chat_control_command(control_id,receipt_id,conversation_id,organization_id,interaction_id,expected_generation,decisions,status)
                VALUES (%s,%s,%s,%s,NULL,1,'[{"decision":"approve"}]','pending')
                """,
                ("93000000-0000-0000-0000-000000000020", receipt, CONV_A, ORG_A),
            )
            connection.commit()
        assert missing_interaction.value.diag.constraint_name == "chat_control_command_decide_interaction_ck"
        connection.rollback()
        with pytest.raises(errors.ForeignKeyViolation) as within_org:
            connection.execute(
                """
                INSERT INTO chat_control_command(control_id,receipt_id,conversation_id,organization_id,interaction_id,expected_generation,decisions,status)
                VALUES (%s,%s,%s,%s,%s,1,'[{"decision":"approve"}]','pending')
                """,
                ("93000000-0000-0000-0000-000000000021", receipt, CONV_A, ORG_A, INTERACTION_B),
            )
        assert within_org.value.diag.constraint_name == "chat_control_command_interaction_conversation_fk"
        connection.rollback()
        with pytest.raises(errors.ForeignKeyViolation) as cross_org:
            connection.execute(
                """
                INSERT INTO chat_control_command(control_id,receipt_id,conversation_id,organization_id,interaction_id,expected_generation,decisions,status)
                VALUES (%s,%s,%s,%s,%s,1,'[{"decision":"approve"}]','pending')
                """,
                ("93000000-0000-0000-0000-000000000022", receipt, CONV_C, ORG_C, INTERACTION_C),
            )
        assert cross_org.value.diag.constraint_name == "chat_control_command_receipt_scope_fk"
        connection.rollback()
        assert connection.execute("SELECT count(*) FROM chat_control_command").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM chat_control_outbox").fetchone()[0] == 0


CASES = {
    "exact-catalog": case_exact_catalog,
    "conversation-tenant": case_conversation_tenant_scope,
    "message-parent": case_message_parent_scope,
    "launch-message": case_launch_message_scope,
    "required-assistant-state": case_required_assistant_and_state_transitions,
    "active-run-race": case_active_run_race,
    "receipt-scope-effect": case_receipt_scope_replay_and_effect,
    "global-sequence": case_global_sequence_allocation,
    "retention-snapshot": case_retention_snapshot,
    "control-interaction-scope": case_control_interaction_scope,
}


@pytest.mark.parametrize("case", list(CASES))
def test_chat_pg18(case: str) -> None:
    run_pg18_case(Path(__file__).resolve(), case)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", required=True, choices=CASES)
    args = parser.parse_args()
    apply_sql(db_url(), segment_prefix("10-site", "20-iam", "30-chat"))
    CASES[args.case]()
