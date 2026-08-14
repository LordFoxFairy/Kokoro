from __future__ import annotations

import argparse
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

import psycopg
import pytest
from psycopg import errors


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))

from pg18 import apply_sql, run_pg18_case, segment_prefix  # noqa: E402


SITE_A = "00000000-0000-0000-0000-000000000101"
SITE_B = "00000000-0000-0000-0000-000000000102"
PRINCIPAL_A = "00000000-0000-0000-0000-000000000201"
PRINCIPAL_B = "00000000-0000-0000-0000-000000000202"
OPERATOR = "00000000-0000-0000-0000-000000000203"
PRINCIPAL_C = "00000000-0000-0000-0000-000000000204"
ORG_A = "00000000-0000-0000-0000-000000000301"
ORG_B = "00000000-0000-0000-0000-000000000302"
ORG_C = "00000000-0000-0000-0000-000000000303"
MEMBERSHIP_A = "00000000-0000-0000-0000-000000000401"
MEMBERSHIP_B = "00000000-0000-0000-0000-000000000402"
ROLE_A = "00000000-0000-0000-0000-000000000501"
ROLE_B = "00000000-0000-0000-0000-000000000502"
PERMISSION = "00000000-0000-0000-0000-000000000601"


def _database_url() -> str:
    return os.environ["KOKORO_TEST_DATABASE_URL"]


def _seed_sites(connection: psycopg.Connection[tuple[object, ...]]) -> None:
    connection.execute(
        """
        INSERT INTO site_site(site_id, key, name, status, default_locale, timezone)
        VALUES (%s, 'site-a', 'Site A', 'active', 'en-US', 'UTC'),
               (%s, 'site-b', 'Site B', 'active', 'en-US', 'UTC')
        """,
        (SITE_A, SITE_B),
    )


def _seed_principals(connection: psycopg.Connection[tuple[object, ...]]) -> None:
    connection.execute(
        """
        INSERT INTO iam_principal(
          principal_id, principal_scope, site_id, kind, status
        ) VALUES
          (%s, 'site', %s, 'user', 'active'),
          (%s, 'site', %s, 'user', 'active'),
          (%s, 'control_plane', NULL, 'operator', 'active')
        """,
        (PRINCIPAL_A, SITE_A, PRINCIPAL_B, SITE_B, OPERATOR),
    )


def _seed_organizations(connection: psycopg.Connection[tuple[object, ...]]) -> None:
    connection.execute(
        """
        INSERT INTO iam_organization(
          organization_id, site_id, kind, personal_owner_principal_id,
          name, status
        ) VALUES
          (%s, %s, 'team', NULL, 'Organization A', 'active'),
          (%s, %s, 'team', NULL, 'Organization B', 'active')
        """,
        (ORG_A, SITE_A, ORG_B, SITE_B),
    )


def _assert_deferred_failure(
    connection: psycopg.Connection[tuple[object, ...]], constraint: str
) -> None:
    with pytest.raises(errors.CheckViolation) as raised:
        connection.commit()
    assert raised.value.diag.constraint_name == constraint, raised.value.diag.constraint_name
    connection.rollback()


def _case_exact_catalog() -> None:
    expected = {
        "site_site",
        "site_domain",
        "iam_principal",
        "iam_user",
        "iam_identity",
        "iam_contact",
        "iam_magic_link",
        "iam_auth_session",
        "iam_command_receipt",
        "iam_organization",
        "iam_membership",
        "iam_role",
        "iam_permission",
        "iam_role_permission",
        "iam_membership_role",
        "iam_security_event",
    }
    with psycopg.connect(_database_url()) as connection:
        actual = {
            row[0]
            for row in connection.execute(
                "SELECT tablename FROM pg_tables WHERE schemaname = 'kokoro'"
            ).fetchall()
        }
        definitions = dict(
            connection.execute(
                """
                SELECT conname, pg_get_constraintdef(oid)
                FROM pg_constraint
                WHERE connamespace = 'kokoro'::regnamespace
                """
            ).fetchall()
        )
    assert actual == expected
    assert definitions["iam_principal_principal_site_key"] == "UNIQUE (principal_id, site_id)"
    assert definitions["iam_organization_organization_site_key"] == "UNIQUE (organization_id, site_id)"
    assert definitions["iam_membership_membership_organization_key"] == "UNIQUE (membership_id, organization_id)"
    assert definitions["iam_role_role_site_key"] == "UNIQUE (role_id, site_id)"
    assert definitions["iam_role_role_organization_key"] == "UNIQUE (role_id, organization_id)"


def _case_membership_rejects_cross_site_principal() -> None:
    with psycopg.connect(_database_url()) as connection:
        _seed_sites(connection)
        _seed_principals(connection)
        _seed_organizations(connection)
        connection.commit()
        with pytest.raises(errors.ForeignKeyViolation) as raised:
            connection.execute(
                """
                INSERT INTO iam_membership(
                  membership_id, site_id, organization_id, principal_id, status
                ) VALUES (%s, %s, %s, %s, 'active')
                """,
                (MEMBERSHIP_B, SITE_A, ORG_A, PRINCIPAL_B),
            )
            connection.commit()
        assert raised.value.diag.constraint_name == "iam_membership_principal_site_fk"
        connection.rollback()
        count = connection.execute(
            "SELECT count(*) FROM iam_membership WHERE membership_id = %s",
            (MEMBERSHIP_B,),
        ).fetchone()[0]
        assert count == 0


def _case_membership_role_rejects_cross_organization() -> None:
    with psycopg.connect(_database_url()) as connection:
        _seed_sites(connection)
        _seed_principals(connection)
        _seed_organizations(connection)
        connection.execute(
            """
            INSERT INTO iam_organization(
              organization_id, site_id, kind, personal_owner_principal_id,
              name, status
            ) VALUES (%s, %s, 'team', NULL, 'Organization C', 'active')
            """,
            (ORG_C, SITE_A),
        )
        connection.execute(
            """
            INSERT INTO iam_membership(
              membership_id, site_id, organization_id, principal_id, status
            ) VALUES
              (%s, %s, %s, %s, 'active'),
              (%s, %s, %s, %s, 'active')
            """,
            (
                MEMBERSHIP_A,
                SITE_A,
                ORG_A,
                PRINCIPAL_A,
                MEMBERSHIP_B,
                SITE_B,
                ORG_B,
                PRINCIPAL_B,
            ),
        )
        connection.execute(
            """
            INSERT INTO iam_role(
              role_id, site_id, organization_id, key, name, role_kind, status
            ) VALUES
              (%s, %s, %s, 'member-a', 'Member A', 'organization', 'active'),
              (%s, %s, %s, 'member-b', 'Member B', 'organization', 'active')
            """,
            (ROLE_A, SITE_A, ORG_A, ROLE_B, SITE_A, ORG_C),
        )
        connection.execute(
            """
            INSERT INTO iam_membership_role(organization_id, membership_id, role_id)
            VALUES (%s, %s, %s)
            """,
            (ORG_A, MEMBERSHIP_A, ROLE_A),
        )
        connection.commit()
        with pytest.raises(errors.ForeignKeyViolation) as raised:
            connection.execute(
                """
                INSERT INTO iam_membership_role(organization_id, membership_id, role_id)
                VALUES (%s, %s, %s)
                """,
                (ORG_A, MEMBERSHIP_A, ROLE_B),
            )
            connection.commit()
        assert (
            raised.value.diag.constraint_name
            == "iam_membership_role_role_organization_fk"
        )
        connection.rollback()
        roles = connection.execute(
            """
            SELECT role_id::text FROM iam_membership_role
            WHERE membership_id = %s ORDER BY role_id
            """,
            (MEMBERSHIP_A,),
        ).fetchall()
        assert roles == [(ROLE_A,)]


def _case_identity_and_contact_scope_triggers() -> None:
    with psycopg.connect(_database_url()) as connection:
        _seed_sites(connection)
        _seed_principals(connection)
        connection.commit()
        connection.execute(
            """
            INSERT INTO iam_identity(
              identity_id, principal_scope, site_id, principal_id,
              issuer, subject, status
            ) VALUES (%s, 'site', %s, %s, 'fixture', 'operator', 'active')
            """,
            ("00000000-0000-0000-0000-000000000701", SITE_A, OPERATOR),
        )
        _assert_deferred_failure(connection, "iam_identity_principal_scope_ck")
        connection.execute(
            """
            INSERT INTO iam_identity(
              identity_id, principal_scope, site_id, principal_id,
              issuer, subject, status
            ) VALUES (%s, 'site', %s, %s, 'fixture', 'wrong-site', 'active')
            """,
            ("00000000-0000-0000-0000-000000000703", SITE_B, PRINCIPAL_A),
        )
        _assert_deferred_failure(connection, "iam_identity_principal_scope_ck")
        connection.execute(
            """
            INSERT INTO iam_contact(
              contact_id, principal_scope, site_id, principal_id,
              kind, normalized_value, status
            ) VALUES (%s, 'control_plane', NULL, %s, 'email', 'a@example.com', 'active')
            """,
            ("00000000-0000-0000-0000-000000000702", PRINCIPAL_A),
        )
        _assert_deferred_failure(connection, "iam_contact_principal_scope_ck")
        assert connection.execute("SELECT count(*) FROM iam_identity").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM iam_contact").fetchone()[0] == 0


def _case_security_event_rejects_cross_site_actor() -> None:
    with psycopg.connect(_database_url()) as connection:
        _seed_sites(connection)
        _seed_principals(connection)
        connection.commit()
        connection.execute(
            """
            INSERT INTO iam_security_event(
              event_id, principal_scope, site_id, principal_id,
              kind, request_id, payload
            ) VALUES (%s, 'site', %s, %s, 'fixture', %s, '{"schemaVersion":1}')
            """,
            (
                "00000000-0000-0000-0000-000000000711",
                SITE_A,
                PRINCIPAL_B,
                "00000000-0000-0000-0000-000000000712",
            ),
        )
        _assert_deferred_failure(
            connection, "iam_security_event_principal_scope_ck"
        )
        assert connection.execute("SELECT count(*) FROM iam_security_event").fetchone()[0] == 0


def _case_parent_updates_preserve_live_auth_invariants() -> None:
    with psycopg.connect(_database_url()) as connection:
        _seed_sites(connection)
        _seed_principals(connection)
        _seed_organizations(connection)
        connection.execute(
            """
            INSERT INTO iam_identity(
              identity_id, principal_scope, site_id, principal_id,
              issuer, subject, status
            ) VALUES (%s, 'control_plane', NULL, %s, 'fixture', 'operator', 'active')
            """,
            ("00000000-0000-0000-0000-000000000721", OPERATOR),
        )
        connection.execute(
            """
            INSERT INTO iam_membership(
              membership_id, site_id, organization_id, principal_id, status
            ) VALUES (%s, %s, %s, %s, 'active')
            """,
            (MEMBERSHIP_A, SITE_A, ORG_A, PRINCIPAL_A),
        )
        session_id = "00000000-0000-0000-0000-000000000722"
        connection.execute(
            """
            INSERT INTO iam_auth_session(
              auth_session_id, principal_scope, site_id, organization_id,
              principal_id, family_ref, family_generation, token_hash, expires_at
            ) VALUES (%s, 'site', %s, %s, %s, %s, 1, decode('21','hex'), now() + interval '1 hour')
            """,
            (
                session_id,
                SITE_A,
                ORG_A,
                PRINCIPAL_A,
                "00000000-0000-0000-0000-000000000723",
            ),
        )
        connection.commit()

        with pytest.raises(errors.CheckViolation) as principal_change:
            connection.execute(
                """
                UPDATE iam_principal
                SET principal_scope = 'site', site_id = %s, kind = 'user'
                WHERE principal_id = %s
                """,
                (SITE_A, OPERATOR),
            )
        assert (
            principal_change.value.diag.constraint_name
            == "iam_principal_identity_immutable_ck"
        )
        connection.rollback()

        connection.execute(
            "UPDATE iam_membership SET status = 'inactive' WHERE membership_id = %s",
            (MEMBERSHIP_A,),
        )
        _assert_deferred_failure(
            connection, "iam_membership_live_auth_session_ck"
        )
        connection.execute(
            "UPDATE iam_auth_session SET revoked_at = now() WHERE auth_session_id = %s",
            (session_id,),
        )
        connection.execute(
            "UPDATE iam_membership SET status = 'inactive' WHERE membership_id = %s",
            (MEMBERSHIP_A,),
        )
        connection.commit()
        assert connection.execute(
            "SELECT status FROM iam_membership WHERE membership_id = %s",
            (MEMBERSHIP_A,),
        ).fetchone()[0] == "inactive"


def _case_membership_deactivation_races_session_creation() -> None:
    with psycopg.connect(_database_url()) as connection:
        _seed_sites(connection)
        _seed_principals(connection)
        _seed_organizations(connection)
        connection.execute(
            """
            INSERT INTO iam_membership(
              membership_id, site_id, organization_id, principal_id, status
            ) VALUES (%s, %s, %s, %s, 'active')
            """,
            (MEMBERSHIP_A, SITE_A, ORG_A, PRINCIPAL_A),
        )
        connection.commit()

    barrier = Barrier(2)

    def deactivate() -> str:
        with psycopg.connect(_database_url()) as connection:
            connection.execute(
                """
                UPDATE iam_membership SET status = 'inactive'
                WHERE membership_id = %s
                """,
                (MEMBERSHIP_A,),
            )
            barrier.wait()
            try:
                connection.commit()
            except errors.CheckViolation as error:
                connection.rollback()
                return error.diag.constraint_name or "unnamed"
            return "committed"

    def create_session() -> str:
        with psycopg.connect(_database_url()) as connection:
            connection.execute(
                """
                INSERT INTO iam_auth_session(
                  auth_session_id, principal_scope, site_id, organization_id,
                  principal_id, family_ref, family_generation, token_hash, expires_at
                ) VALUES (%s, 'site', %s, %s, %s, %s, 1, decode('22','hex'), now() + interval '1 hour')
                """,
                (
                    "00000000-0000-0000-0000-000000000724",
                    SITE_A,
                    ORG_A,
                    PRINCIPAL_A,
                    "00000000-0000-0000-0000-000000000725",
                ),
            )
            barrier.wait()
            try:
                connection.commit()
            except errors.CheckViolation as error:
                connection.rollback()
                return error.diag.constraint_name or "unnamed"
            return "committed"

    with ThreadPoolExecutor(max_workers=2) as executor:
        deactivate_result = executor.submit(deactivate)
        session_result = executor.submit(create_session)
        outcomes = [deactivate_result.result(), session_result.result()]
    assert outcomes.count("committed") == 1
    assert set(outcomes) <= {
        "committed",
        "iam_auth_session_organization_scope_ck",
        "iam_membership_live_auth_session_ck",
    }
    with psycopg.connect(_database_url()) as connection:
        membership_status = connection.execute(
            "SELECT status FROM iam_membership WHERE membership_id = %s",
            (MEMBERSHIP_A,),
        ).fetchone()[0]
        live_sessions = connection.execute(
            "SELECT count(*) FROM iam_auth_session WHERE revoked_at IS NULL",
        ).fetchone()[0]
    assert (membership_status, live_sessions) in {("inactive", 0), ("active", 1)}


def _case_auth_session_scope_and_membership() -> None:
    with psycopg.connect(_database_url()) as connection:
        _seed_sites(connection)
        _seed_principals(connection)
        _seed_organizations(connection)
        connection.execute(
            """
            INSERT INTO iam_membership(
              membership_id, site_id, organization_id, principal_id, status
            ) VALUES (%s, %s, %s, %s, 'active')
            """,
            (MEMBERSHIP_A, SITE_A, ORG_A, PRINCIPAL_A),
        )
        connection.commit()
        connection.execute(
            """
            INSERT INTO iam_auth_session(
              auth_session_id, principal_scope, site_id, organization_id,
              principal_id, family_ref, family_generation, token_hash, expires_at
            ) VALUES (%s, 'site', %s, %s, %s, %s, 1, decode('01','hex'), now() + interval '1 hour')
            """,
            (
                "00000000-0000-0000-0000-000000000801",
                SITE_A,
                ORG_A,
                OPERATOR,
                "00000000-0000-0000-0000-000000000901",
            ),
        )
        _assert_deferred_failure(connection, "iam_auth_session_principal_scope_ck")
        connection.execute(
            """
            INSERT INTO iam_auth_session(
              auth_session_id, principal_scope, site_id, organization_id,
              principal_id, family_ref, family_generation, token_hash, expires_at
            ) VALUES (%s, 'control_plane', NULL, NULL, %s, %s, 1, decode('02','hex'), now() + interval '1 hour')
            """,
            (
                "00000000-0000-0000-0000-000000000802",
                PRINCIPAL_A,
                "00000000-0000-0000-0000-000000000902",
            ),
        )
        _assert_deferred_failure(connection, "iam_auth_session_principal_scope_ck")
        connection.execute(
            """
            INSERT INTO iam_auth_session(
              auth_session_id, principal_scope, site_id, organization_id,
              principal_id, family_ref, family_generation, token_hash, expires_at
            ) VALUES (%s, 'site', %s, NULL, %s, %s, 1, decode('06','hex'), now() + interval '1 hour')
            """,
            (
                "00000000-0000-0000-0000-000000000806",
                SITE_A,
                PRINCIPAL_A,
                "00000000-0000-0000-0000-000000000906",
            ),
        )
        _assert_deferred_failure(
            connection, "iam_auth_session_organization_scope_ck"
        )
        connection.execute(
            """
            INSERT INTO iam_auth_session(
              auth_session_id, principal_scope, site_id, organization_id,
              principal_id, family_ref, family_generation, token_hash, expires_at
            ) VALUES (%s, 'control_plane', NULL, %s, %s, %s, 1, decode('07','hex'), now() + interval '1 hour')
            """,
            (
                "00000000-0000-0000-0000-000000000807",
                ORG_A,
                OPERATOR,
                "00000000-0000-0000-0000-000000000907",
            ),
        )
        _assert_deferred_failure(
            connection, "iam_auth_session_organization_scope_ck"
        )
        connection.execute(
            "UPDATE iam_membership SET status = 'inactive' WHERE membership_id = %s",
            (MEMBERSHIP_A,),
        )
        connection.commit()
        connection.execute(
            """
            INSERT INTO iam_auth_session(
              auth_session_id, principal_scope, site_id, organization_id,
              principal_id, family_ref, family_generation, token_hash, expires_at
            ) VALUES (%s, 'site', %s, %s, %s, %s, 1, decode('03','hex'), now() + interval '1 hour')
            """,
            (
                "00000000-0000-0000-0000-000000000803",
                SITE_A,
                ORG_A,
                PRINCIPAL_A,
                "00000000-0000-0000-0000-000000000903",
            ),
        )
        _assert_deferred_failure(
            connection, "iam_auth_session_organization_scope_ck"
        )
        assert connection.execute("SELECT count(*) FROM iam_auth_session").fetchone()[0] == 0
        connection.execute(
            "UPDATE iam_membership SET status = 'active' WHERE membership_id = %s",
            (MEMBERSHIP_A,),
        )
        connection.commit()
        connection.execute(
            """
            INSERT INTO iam_auth_session(
              auth_session_id, principal_scope, site_id, organization_id,
              principal_id, family_ref, family_generation, token_hash, expires_at
            ) VALUES
              (%s, 'site', %s, %s, %s, %s, 1, decode('04','hex'), now() + interval '1 hour'),
              (%s, 'control_plane', NULL, NULL, %s, %s, 1, decode('05','hex'), now() + interval '1 hour')
            """,
            (
                "00000000-0000-0000-0000-000000000804",
                SITE_A,
                ORG_A,
                PRINCIPAL_A,
                "00000000-0000-0000-0000-000000000904",
                "00000000-0000-0000-0000-000000000805",
                OPERATOR,
                "00000000-0000-0000-0000-000000000905",
            ),
        )
        connection.commit()
        assert connection.execute("SELECT count(*) FROM iam_auth_session").fetchone()[0] == 2


def _case_personal_organization_race() -> None:
    with psycopg.connect(_database_url()) as connection:
        _seed_sites(connection)
        _seed_principals(connection)
        connection.commit()
    candidates = [
        "00000000-0000-0000-0000-000000000311",
        "00000000-0000-0000-0000-000000000312",
    ]
    barrier = Barrier(2)

    def claim(organization_id: str) -> tuple[str | None, str]:
        with psycopg.connect(_database_url()) as connection:
            barrier.wait()
            inserted = connection.execute(
                """
                INSERT INTO iam_organization(
                  organization_id, site_id, kind, personal_owner_principal_id,
                  name, status
                ) VALUES (%s, %s, 'personal', %s, 'Personal', 'active')
                ON CONFLICT DO NOTHING
                RETURNING organization_id::text
                """,
                (organization_id, SITE_A, PRINCIPAL_A),
            ).fetchone()
            connection.commit()
            winner = connection.execute(
                """
                SELECT organization_id::text FROM iam_organization
                WHERE site_id = %s AND personal_owner_principal_id = %s
                """,
                (SITE_A, PRINCIPAL_A),
            ).fetchone()[0]
            return (None if inserted is None else inserted[0], winner)

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(claim, candidates))
    inserted = [row for row, _winner in results if row is not None]
    winners = {_winner for _row, _winner in results}
    assert len(inserted) == 1
    assert winners == {inserted[0]}


class DigestConflict(Exception):
    pass


def _case_command_receipt_replay_and_drift() -> None:
    command_id = "00000000-0000-0000-0000-000000001001"
    receipt_id = "00000000-0000-0000-0000-000000001002"

    with psycopg.connect(_database_url()) as connection:
        _seed_sites(connection)
        _seed_principals(connection)
        connection.commit()

    effect_id = "00000000-0000-0000-0000-000000001003"

    def claim(digest_hex: str) -> tuple[str, dict[str, str]]:
        with psycopg.connect(_database_url()) as connection:
            row = connection.execute(
                """
                INSERT INTO iam_command_receipt(
                  receipt_id, command_id, command_kind, request_digest,
                  status, result_payload
                ) VALUES (%s, %s, 'CreatePersonalOrganization', decode(%s,'hex'),
                          'processing', NULL)
                ON CONFLICT (command_id) DO NOTHING
                RETURNING receipt_id::text
                """,
                (receipt_id, command_id, digest_hex),
            ).fetchone()
            if row is not None:
                connection.execute(
                    """
                    INSERT INTO iam_organization(
                      organization_id, site_id, kind, personal_owner_principal_id,
                      name, status
                    ) VALUES (%s, %s, 'personal', %s, 'Personal', 'active')
                    """,
                    (effect_id, SITE_A, PRINCIPAL_A),
                )
                row = connection.execute(
                    """
                    UPDATE iam_command_receipt
                    SET status = 'completed',
                        result_payload = jsonb_build_object('organizationId', %s::text)
                    WHERE receipt_id = %s
                    RETURNING receipt_id::text, result_payload
                    """,
                    (effect_id, receipt_id),
                ).fetchone()
                connection.commit()
                return row
            existing = connection.execute(
                """
                SELECT receipt_id::text, result_payload,
                       encode(request_digest, 'hex')
                FROM iam_command_receipt
                WHERE command_id = %s
                """,
                (command_id,),
            ).fetchone()
            if existing[2] != digest_hex:
                raise DigestConflict(command_id)
            connection.commit()
            return existing[0], existing[1]

    first = claim("aa")
    replay = claim("aa")
    assert replay == first
    with pytest.raises(DigestConflict):
        claim("bb")
    with psycopg.connect(_database_url()) as connection:
        with pytest.raises(errors.CheckViolation) as immutable:
            connection.execute(
                """
                UPDATE iam_command_receipt
                SET request_digest = decode('bb','hex')
                WHERE command_id = %s
                """,
                (command_id,),
            )
        assert (
            immutable.value.diag.constraint_name
            == "iam_command_receipt_claim_immutable_ck"
        )
        connection.rollback()
        rows = connection.execute(
            """
            SELECT receipt_id::text, encode(request_digest, 'hex'), result_payload
            FROM iam_command_receipt WHERE command_id = %s
            """,
            (command_id,),
        ).fetchall()
        effect_count = connection.execute(
            "SELECT count(*) FROM iam_organization WHERE organization_id = %s",
            (effect_id,),
        ).fetchone()[0]
    assert rows == [(receipt_id, "aa", {"organizationId": effect_id})]
    assert effect_count == 1


def _case_auth_session_family_constraints() -> None:
    with psycopg.connect(_database_url()) as connection:
        _seed_sites(connection)
        _seed_principals(connection)
        _seed_organizations(connection)
        connection.execute(
            """
            INSERT INTO iam_principal(
              principal_id, principal_scope, site_id, kind, status
            ) VALUES (%s, 'site', %s, 'user', 'active')
            """,
            (PRINCIPAL_C, SITE_A),
        )
        connection.execute(
            """
            INSERT INTO iam_membership(
              membership_id, site_id, organization_id, principal_id, status
            ) VALUES (%s, %s, %s, %s, 'active')
            """,
            (MEMBERSHIP_A, SITE_A, ORG_A, PRINCIPAL_A),
        )
        connection.execute(
            """
            INSERT INTO iam_membership(
              membership_id, site_id, organization_id, principal_id, status
            ) VALUES (%s, %s, %s, %s, 'active')
            """,
            (MEMBERSHIP_B, SITE_A, ORG_A, PRINCIPAL_C),
        )
        session_id = "00000000-0000-0000-0000-000000001101"
        family_ref = "00000000-0000-0000-0000-000000001102"
        connection.execute(
            """
            INSERT INTO iam_auth_session(
              auth_session_id, principal_scope, site_id, organization_id,
              principal_id, family_ref, family_generation, token_hash, expires_at
            ) VALUES (%s, 'site', %s, %s, %s, %s, 1, decode('11','hex'), now() + interval '1 hour')
            """,
            (session_id, SITE_A, ORG_A, PRINCIPAL_A, family_ref),
        )
        connection.commit()
        with pytest.raises(errors.CheckViolation) as immutable:
            connection.execute(
                "UPDATE iam_auth_session SET family_generation = 2 WHERE auth_session_id = %s",
                (session_id,),
            )
        assert (
            immutable.value.diag.constraint_name
            == "iam_auth_session_family_generation_immutable_ck"
        )
        connection.rollback()
        with pytest.raises(errors.UniqueViolation) as duplicate:
            connection.execute(
                """
                INSERT INTO iam_auth_session(
                  auth_session_id, principal_scope, site_id, organization_id,
                  principal_id, family_ref, family_generation, token_hash, expires_at
                ) VALUES (%s, 'site', %s, %s, %s, %s, 1, decode('12','hex'), now() + interval '1 hour')
                """,
                (
                    "00000000-0000-0000-0000-000000001103",
                    SITE_A,
                    ORG_A,
                    PRINCIPAL_A,
                    family_ref,
                ),
            )
        assert duplicate.value.diag.constraint_name == "iam_auth_session_family_generation_key"
        connection.rollback()
        with pytest.raises(errors.CheckViolation) as family_change:
            connection.execute(
                """
                UPDATE iam_auth_session SET family_ref = %s
                WHERE auth_session_id = %s
                """,
                ("00000000-0000-0000-0000-000000001109", session_id),
            )
        assert (
            family_change.value.diag.constraint_name
            == "iam_auth_session_identity_immutable_ck"
        )
        connection.rollback()
        successor_id = "00000000-0000-0000-0000-000000001104"
        connection.execute(
            """
            INSERT INTO iam_auth_session(
              auth_session_id, principal_scope, site_id, organization_id,
              principal_id, family_ref, family_generation, token_hash, expires_at
            ) VALUES (%s, 'site', %s, %s, %s, %s, 2, decode('13','hex'), now() + interval '1 hour')
            """,
            (successor_id, SITE_A, ORG_A, PRINCIPAL_A, family_ref),
        )
        _assert_deferred_failure(
            connection, "iam_auth_session_rotation_monotonic_ck"
        )
        connection.execute(
            """
            INSERT INTO iam_auth_session(
              auth_session_id, principal_scope, site_id, organization_id,
              principal_id, family_ref, family_generation, token_hash, expires_at
            ) VALUES (%s, 'site', %s, %s, %s, %s, 2, decode('15','hex'), now() + interval '1 hour')
            """,
            (successor_id, SITE_A, ORG_A, PRINCIPAL_C, family_ref),
        )
        connection.execute(
            "UPDATE iam_auth_session SET rotated_to = %s WHERE auth_session_id = %s",
            (successor_id, session_id),
        )
        _assert_deferred_failure(
            connection, "iam_auth_session_rotation_monotonic_ck"
        )
        connection.execute(
            """
            INSERT INTO iam_auth_session(
              auth_session_id, principal_scope, site_id, organization_id,
              principal_id, family_ref, family_generation, token_hash, expires_at
            ) VALUES (%s, 'site', %s, %s, %s, %s, 2, decode('14','hex'), now() + interval '1 hour')
            """,
            (successor_id, SITE_A, ORG_A, PRINCIPAL_A, family_ref),
        )
        connection.execute(
            "UPDATE iam_auth_session SET rotated_to = %s WHERE auth_session_id = %s",
            (successor_id, session_id),
        )
        connection.commit()
        rotated_to = connection.execute(
            "SELECT rotated_to::text FROM iam_auth_session WHERE auth_session_id = %s",
            (session_id,),
        ).fetchone()[0]
        assert rotated_to == successor_id
        with pytest.raises(errors.CheckViolation) as unlink:
            connection.execute(
                """
                UPDATE iam_auth_session SET rotated_to = NULL
                WHERE auth_session_id = %s
                """,
                (session_id,),
            )
        assert (
            unlink.value.diag.constraint_name
            == "iam_auth_session_rotation_link_immutable_ck"
        )
        connection.rollback()
        assert connection.execute(
            "SELECT rotated_to::text FROM iam_auth_session WHERE auth_session_id = %s",
            (session_id,),
        ).fetchone()[0] == successor_id


def _case_disabled_permission_denies_without_deleting_bindings() -> None:
    with psycopg.connect(_database_url()) as connection:
        _seed_sites(connection)
        _seed_principals(connection)
        _seed_organizations(connection)
        connection.execute(
            """
            INSERT INTO iam_membership(
              membership_id, site_id, organization_id, principal_id, status
            ) VALUES (%s, %s, %s, %s, 'active')
            """,
            (MEMBERSHIP_A, SITE_A, ORG_A, PRINCIPAL_A),
        )
        connection.execute(
            """
            INSERT INTO iam_role(
              role_id, site_id, organization_id, key, name, role_kind, status
            ) VALUES (%s, %s, %s, 'member', 'Member', 'organization', 'active')
            """,
            (ROLE_A, SITE_A, ORG_A),
        )
        connection.execute(
            """
            INSERT INTO iam_permission(permission_id, key, description, status)
            VALUES (%s, 'conversation.read', 'Read conversations', 'active')
            """,
            (PERMISSION,),
        )
        connection.execute(
            "INSERT INTO iam_role_permission(role_id, permission_id) VALUES (%s, %s)",
            (ROLE_A, PERMISSION),
        )
        connection.execute(
            """
            INSERT INTO iam_membership_role(organization_id, membership_id, role_id)
            VALUES (%s, %s, %s)
            """,
            (ORG_A, MEMBERSHIP_A, ROLE_A),
        )
        connection.commit()

        def effective() -> list[str]:
            return [
                row[0]
                for row in connection.execute(
                    """
                    SELECT p.key
                    FROM iam_membership m
                    JOIN iam_membership_role mr ON mr.membership_id = m.membership_id
                    JOIN iam_role r ON r.role_id = mr.role_id
                    JOIN iam_role_permission rp ON rp.role_id = r.role_id
                    JOIN iam_permission p ON p.permission_id = rp.permission_id
                    WHERE m.membership_id = %s
                      AND m.status = 'active'
                      AND r.status = 'active'
                      AND p.status = 'active'
                    """,
                    (MEMBERSHIP_A,),
                ).fetchall()
            ]

        assert effective() == ["conversation.read"]
        connection.execute(
            "UPDATE iam_permission SET status = 'disabled' WHERE permission_id = %s",
            (PERMISSION,),
        )
        connection.commit()
        assert effective() == []
        assert connection.execute("SELECT count(*) FROM iam_role_permission").fetchone()[0] == 1
        assert connection.execute("SELECT count(*) FROM iam_membership_role").fetchone()[0] == 1


def _case_site_has_one_active_primary_domain() -> None:
    with psycopg.connect(_database_url()) as connection:
        _seed_sites(connection)
        connection.execute(
            """
            INSERT INTO site_domain(
              domain_id, site_id, normalized_host, status, is_primary, verified_at
            ) VALUES (%s, %s, 'a.example.com', 'active', true, now())
            """,
            ("00000000-0000-0000-0000-000000001201", SITE_A),
        )
        connection.commit()
        with pytest.raises(errors.UniqueViolation) as raised:
            connection.execute(
                """
                INSERT INTO site_domain(
                  domain_id, site_id, normalized_host, status, is_primary, verified_at
                ) VALUES (%s, %s, 'b.example.com', 'active', true, now())
                """,
                ("00000000-0000-0000-0000-000000001202", SITE_A),
            )
        assert raised.value.diag.constraint_name == "site_domain_one_active_primary_uidx"
        connection.rollback()
        assert connection.execute("SELECT count(*) FROM site_domain").fetchone()[0] == 1


CASES = {
    "exact-catalog": _case_exact_catalog,
    "membership-cross-site": _case_membership_rejects_cross_site_principal,
    "membership-role-cross-org": _case_membership_role_rejects_cross_organization,
    "identity-contact-scope": _case_identity_and_contact_scope_triggers,
    "security-event-scope": _case_security_event_rejects_cross_site_actor,
    "parent-reverse-invariants": _case_parent_updates_preserve_live_auth_invariants,
    "auth-membership-race": _case_membership_deactivation_races_session_creation,
    "auth-session-scope": _case_auth_session_scope_and_membership,
    "personal-org-race": _case_personal_organization_race,
    "command-receipt": _case_command_receipt_replay_and_drift,
    "auth-family": _case_auth_session_family_constraints,
    "disabled-permission": _case_disabled_permission_denies_without_deleting_bindings,
    "site-primary-domain": _case_site_has_one_active_primary_domain,
}


@pytest.mark.parametrize("case", list(CASES))
def test_site_iam_pg18(case: str) -> None:
    run_pg18_case(Path(__file__).resolve(), case)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", required=True, choices=CASES)
    arguments = parser.parse_args()
    apply_sql(_database_url(), segment_prefix("10-site", "20-iam"))
    CASES[arguments.case]()
