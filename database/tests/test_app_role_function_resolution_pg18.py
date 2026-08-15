from __future__ import annotations

import os
from uuid import uuid4

import psycopg
import pytest
from psycopg import errors


pytestmark = pytest.mark.skipif(
    "DATABASE_URL_KOKORO_APP" not in os.environ,
    reason="requires the isolated native PostgreSQL 18 app-role fixture",
)

HARDENED_SEARCH_PATH = "search_path=pg_catalog, kokoro, pg_temp"


def test_every_production_plpgsql_function_is_invoker_and_search_path_hardened() -> None:
    with psycopg.connect(os.environ["DATABASE_URL_KOKORO_APP"]) as connection:
        functions = connection.execute(
            """
            SELECT p.proname,p.prosecdef,p.proconfig
            FROM pg_catalog.pg_proc p
            JOIN pg_catalog.pg_namespace n ON n.oid=p.pronamespace
            JOIN pg_catalog.pg_language l ON l.oid=p.prolang
            WHERE n.nspname='kokoro' AND l.lanname='plpgsql'
            ORDER BY p.proname
            """
        ).fetchall()
    assert len(functions) == 42
    assert all(not security_definer for _, security_definer, _ in functions)
    assert all(config == [HARDENED_SEARCH_PATH] for _, _, config in functions)


def _seed_chat_decide(
    connection: psycopg.Connection[tuple[object, ...]], *, interaction: bool
) -> tuple[str, str]:
    site_id = str(uuid4())
    principal_id = str(uuid4())
    organization_id = str(uuid4())
    conversation_id = str(uuid4())
    user_message_id = str(uuid4())
    assistant_message_id = str(uuid4())
    launch_id = str(uuid4())
    agent_run_id = str(uuid4())
    interaction_id = str(uuid4())
    receipt_id = str(uuid4())
    control_id = str(uuid4())
    connection.execute(
        """
        INSERT INTO kokoro.site_site(
          site_id,key,name,status,default_locale,timezone
        ) VALUES (%s,%s,'App Role Site','active','en-US','UTC')
        """,
        (site_id, f"site-{site_id}"),
    )
    connection.execute(
        """
        INSERT INTO kokoro.iam_principal(
          principal_id,principal_scope,site_id,kind,status
        ) VALUES (%s,'site',%s,'user','active')
        """,
        (principal_id, site_id),
    )
    connection.execute(
        """
        INSERT INTO kokoro.iam_organization(
          organization_id,site_id,kind,name,status
        ) VALUES (%s,%s,'team','App Role Org','active')
        """,
        (organization_id, site_id),
    )
    connection.execute(
        """
        INSERT INTO kokoro.chat_conversation(
          conversation_id,organization_id,site_id,created_by_principal_id,
          title,agent_namespace,state
        ) VALUES (%s,%s,%s,%s,'App Role',%s,'active')
        """,
        (conversation_id, organization_id, site_id, principal_id, f"namespace/{conversation_id}"),
    )
    connection.execute(
        """
        INSERT INTO kokoro.chat_message(
          message_id,conversation_id,role,status,ordinal
        ) VALUES (%s,%s,'user','complete',1),(%s,%s,'assistant','complete',2)
        """,
        (user_message_id, conversation_id, assistant_message_id, conversation_id),
    )
    connection.execute(
        """
        INSERT INTO kokoro.chat_run_launch(
          launch_id,conversation_id,user_message_id,assistant_message_id,
          state,agent_run_id
        ) VALUES (%s,%s,%s,%s,'accepted',%s)
        """,
        (launch_id, conversation_id, user_message_id, assistant_message_id, agent_run_id),
    )
    connection.execute(
        """
        INSERT INTO kokoro.chat_run_view(
          agent_run_id,launch_id,conversation_id,epoch,state
        ) VALUES (%s,%s,%s,1,'paused')
        """,
        (agent_run_id, launch_id, conversation_id),
    )
    if interaction:
        connection.execute(
            """
            INSERT INTO kokoro.chat_interaction(
              interaction_id,agent_run_id,conversation_id,kind,action_digest,
              schema_version,payload,status
            ) VALUES (%s,%s,%s,'approval',decode(repeat('aa',32),'hex'),1,'{}','pending')
            """,
            (interaction_id, agent_run_id, conversation_id),
        )
    connection.execute(
        """
        INSERT INTO kokoro.chat_command_receipt(
          receipt_id,site_id,organization_id,conversation_id,command_id,
          command_kind,request_digest,status
        ) VALUES (%s,%s,%s,%s,%s,'DecideInteraction',
                  decode(repeat('bb',32),'hex'),'processing')
        """,
        (receipt_id, site_id, organization_id, conversation_id, str(uuid4())),
    )
    connection.execute(
        """
        INSERT INTO kokoro.chat_control_command(
          control_id,receipt_id,conversation_id,organization_id,interaction_id,
          expected_generation,decisions,status
        ) VALUES (%s,%s,%s,%s,%s,1,'[{"kind":"approve"}]','pending')
        """,
        (
            control_id,
            receipt_id,
            conversation_id,
            organization_id,
            interaction_id if interaction else None,
        ),
    )
    return control_id, receipt_id


def test_app_role_default_public_search_path_commits_valid_decide_control() -> None:
    with psycopg.connect(os.environ["DATABASE_URL_KOKORO_APP"]) as connection:
        assert connection.execute("SHOW search_path").fetchone()[0] == '"$user", public'
        control_id, receipt_id = _seed_chat_decide(connection, interaction=True)
        connection.commit()
        stored = connection.execute(
            """
            SELECT control_id,receipt_id FROM kokoro.chat_control_command
            WHERE control_id=%s
            """,
            (control_id,),
        ).fetchone()
        assert stored is not None
        assert (str(stored[0]), str(stored[1])) == (control_id, receipt_id)


def test_app_role_deferred_decide_requirement_and_temp_injection_fences() -> None:
    with psycopg.connect(os.environ["DATABASE_URL_KOKORO_APP"]) as connection:
        assert connection.execute("SHOW search_path").fetchone()[0] == '"$user", public'
        with pytest.raises(errors.InsufficientPrivilege):
            connection.execute(
                """
                CREATE TEMP TABLE chat_command_receipt(
                  receipt_id uuid,conversation_id uuid,organization_id uuid,
                  command_kind text
                )
                """
            )
        connection.rollback()
        _control_id, _receipt_id = _seed_chat_decide(connection, interaction=False)
        with pytest.raises(errors.CheckViolation) as raised:
            connection.commit()
        assert raised.value.diag.constraint_name == "chat_control_command_decide_interaction_ck"


def test_app_role_cross_surface_deferred_functions_and_negative_mutations() -> None:
    site_id = str(uuid4())
    principal_id = str(uuid4())
    organization_id = str(uuid4())
    provider_id = str(uuid4())
    model_id = str(uuid4())
    revision_id = str(uuid4())
    snapshot_id = str(uuid4())
    run_id = str(uuid4())
    manifest_id = str(uuid4())
    with psycopg.connect(os.environ["DATABASE_URL_KOKORO_APP"]) as connection:
        assert connection.execute("SHOW search_path").fetchone()[0] == '"$user", public'
        connection.execute(
            """
            INSERT INTO kokoro.site_site(site_id,key,name,status,default_locale,timezone)
            VALUES (%s,%s,'Cross Surface','active','en-US','UTC')
            """,
            (site_id, f"site-{site_id}"),
        )
        connection.execute(
            """
            INSERT INTO kokoro.iam_principal(
              principal_id,principal_scope,site_id,kind,status
            ) VALUES (%s,'site',%s,'user','active')
            """,
            (principal_id, site_id),
        )
        connection.execute(
            """
            INSERT INTO kokoro.iam_identity(
              identity_id,principal_scope,site_id,principal_id,issuer,subject,status
            ) VALUES (%s,'site',%s,%s,'fixture',%s,'active')
            """,
            (str(uuid4()), site_id, principal_id, f"subject-{principal_id}"),
        )
        connection.execute(
            """
            INSERT INTO kokoro.iam_organization(
              organization_id,site_id,kind,name,status
            ) VALUES (%s,%s,'team','Cross Surface','active')
            """,
            (organization_id, site_id),
        )
        connection.execute(
            """
            INSERT INTO kokoro.model_provider(
              provider_id,key,display_name,status
            ) VALUES (%s,%s,'Provider','active')
            """,
            (provider_id, f"provider-{provider_id}"),
        )
        connection.execute(
            """
            INSERT INTO kokoro.model_definition(model_id,key,display_name,status)
            VALUES (%s,%s,'Model','active')
            """,
            (model_id, f"model-{model_id}"),
        )
        connection.execute(
            """
            INSERT INTO kokoro.model_revision(
              model_revision_id,model_id,revision,provider_id,provider_model_name,
              transport,modalities,context_window,published_at
            ) VALUES (%s,%s,1,%s,'fixture/model','litellm','["text"]',8192,
                      transaction_timestamp())
            """,
            (revision_id, model_id, provider_id),
        )
        connection.execute(
            """
            UPDATE kokoro.model_definition SET current_revision_id=%s
            WHERE model_id=%s
            """,
            (revision_id, model_id),
        )
        connection.execute(
            """
            INSERT INTO kokoro.model_routing_policy(
              routing_policy_id,site_id,label,model_revision_id,priority,status
            ) VALUES (%s,%s,'default',%s,0,'active')
            """,
            (str(uuid4()), site_id, revision_id),
        )
        connection.execute(
            """
            INSERT INTO kokoro.capability_runtime_snapshot(
              snapshot_id,organization_id,scope_key,digest
            ) VALUES (%s,%s,%s,decode(repeat('31',32),'hex'))
            """,
            (snapshot_id, organization_id, f"scope/{run_id}"),
        )
        connection.execute(
            """
            INSERT INTO kokoro.agent_run(
              agent_run_id,launch_id,launch_request_digest,namespace,state
            ) VALUES (%s,%s,decode(repeat('41',32),'hex'),%s,'preparing')
            """,
            (run_id, str(uuid4()), f"scope/{run_id}"),
        )
        connection.execute(
            """
            INSERT INTO kokoro.agent_execution_manifest(
              execution_manifest_id,agent_run_id,namespace,digest,
              agent_preset_key,agent_preset_digest,model_revision_id,
              capability_snapshot_id,usage_mode,usage_policy_digest,payload
            ) VALUES (%s,%s,%s,decode(repeat('51',32),'hex'),'general',
                      decode(repeat('52',32),'hex'),%s,%s,'unmetered',
                      decode(repeat('53',32),'hex'),'{}')
            """,
            (manifest_id, run_id, f"scope/{run_id}", revision_id, snapshot_id),
        )
        connection.execute(
            """
            UPDATE kokoro.agent_run SET execution_manifest_id=%s,state='queued'
            WHERE agent_run_id=%s
            """,
            (manifest_id, run_id),
        )
        connection.commit()

    with psycopg.connect(os.environ["DATABASE_URL_KOKORO_APP"]) as connection:
        with pytest.raises(errors.CheckViolation) as iam_scope:
            connection.execute(
                """
                INSERT INTO kokoro.iam_identity(
                  identity_id,principal_scope,site_id,principal_id,issuer,subject,status
                ) VALUES (%s,'control_plane',NULL,%s,'fixture','wrong-scope','active')
                """,
                (str(uuid4()), principal_id),
            )
            connection.commit()
        assert iam_scope.value.diag.constraint_name == "iam_identity_principal_scope_ck"
        connection.rollback()
        with pytest.raises(errors.CheckViolation) as published_model:
            connection.execute(
                """
                UPDATE kokoro.model_revision SET provider_model_name='mutated'
                WHERE model_revision_id=%s
                """,
                (revision_id,),
            )
        assert published_model.value.diag.constraint_name == "model_revision_published_immutable_ck"
        connection.rollback()
        with pytest.raises(errors.CheckViolation) as snapshot:
            connection.execute(
                """
                UPDATE kokoro.capability_runtime_snapshot
                SET digest=decode(repeat('ff',32),'hex') WHERE snapshot_id=%s
                """,
                (snapshot_id,),
            )
        assert snapshot.value.diag.constraint_name == "capability_runtime_snapshot_immutable_ck"
