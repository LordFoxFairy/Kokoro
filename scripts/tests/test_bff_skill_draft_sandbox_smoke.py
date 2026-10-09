"""Protocol and isolation guards for the Skill draft composition runner."""

import base64
import importlib.util
import json
from datetime import datetime, timedelta, timezone
from io import StringIO
from io import BytesIO
from pathlib import Path
import stat
import sys
import tempfile
import unittest
import zipfile
from unittest.mock import patch


PATH = Path(__file__).resolve().parents[1] / "e2e/run_bff_skill_draft_sandbox_smoke.py"
spec = importlib.util.spec_from_file_location("skill_draft_sandbox", PATH)
smoke = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = smoke
spec.loader.exec_module(smoke)


def ready():
    return {
        "kind": "ready",
        "base_url": "http://127.0.0.1:4401",
        "database_name": "kokoro_skill_abc",
        "redis_prefix": "owned:abc",
        "issuer_url": "https://web.example.test/iam",
        "client_id": "web",
        "client_secret": "web-secret",
        "redirect_uri": "https://web.example.test/callback",
        "post_logout_redirect_uri": "https://web.example.test/logout",
        "email": "owner@example.test",
        "password": "password",
        "tenant_id": "tenant-one",
        "skill_sandbox": {
            "access_token": "user-token",
            "subject_id": "user-one",
            "catalog_client": {
                "client_id": "catalog",
                "client_secret": "catalog-secret",
            },
            "projection_client": {
                "client_id": "projection",
                "client_secret": "projection-secret",
            },
            "resource_server_basic": {
                "client_id": "resource",
                "client_secret": "resource-secret",
            },
            "execution_authorization_client": {
                "client_id": "execution",
                "client_secret": "execution-secret",
            },
        },
    }


class SkillDraftSandboxGuards(unittest.TestCase):
    def test_platform_guard_denials_are_exact_and_do_not_return_data(self):
        for status, code, message in (
            (401, "capability.service_auth_failed", "BFF workload bearer is required"),
            (
                401,
                "capability.service_auth_failed",
                "BFF workload authentication failed",
            ),
            (403, "capability.tenant_mismatch", "BFF tenant does not match IAM"),
        ):
            body = {"error": {"code": code, "message": message, "retryable": False}}
            with self.subTest(status=status, message=message):
                smoke.require_platform_guard_denial(status, body, code, message)
                with self.assertRaises(smoke.SmokeError):
                    smoke.require_platform_guard_denial(
                        status, {**body, "data": {"skill_id": "private"}}, code, message
                    )
                with self.assertRaisesRegex(
                    smoke.SmokeError,
                    "observed status=404 code=capability.route_not_found",
                ):
                    smoke.require_platform_guard_denial(
                        404,
                        {
                            "error": {
                                "code": "capability.route_not_found",
                                "message": "Not found",
                                "retryable": False,
                            }
                        },
                        code,
                        message,
                    )

    def test_iam_projection_token_uses_only_dedicated_client_and_scope(self):
        sent = []

        class Response:
            status = 200

            def read(self, _limit):
                return b'{"access_token":"projection-token","token_type":"Bearer"}'

        class Connection:
            def __init__(self, *_args, **_kwargs):
                pass

            def request(self, *args, **kwargs):
                sent.append((args, kwargs))

            def getresponse(self):
                return Response()

            def close(self):
                pass

        with patch.object(smoke.http.client, "HTTPConnection", Connection):
            token = smoke.issue_projection_token(smoke.require_sandbox_ready(ready()))
        self.assertEqual(token, "projection-token")
        args, kwargs = sent[0]
        self.assertEqual(args, ("POST", "/iam/oauth2/token"))
        credential = kwargs["headers"]["authorization"].removeprefix("Basic ")
        self.assertEqual(base64.b64decode(credential), b"projection:projection-secret")
        self.assertIn(b"scope=platform%3Aprojection.read", kwargs["body"])
        self.assertIn(
            b"resource=https%3A%2F%2Fkokoro.dev%2Fresources%2Fplatform-internal",
            kwargs["body"],
        )

    def test_platform_by_id_http_sends_trusted_bff_projection_and_checks_headers(self):
        sent = []

        class Response:
            status = 404

            def read(self, _limit):
                return b'{"error":{"code":"capability.route_not_found","message":"Capability BFF route was not found","retryable":false}}'

            def getheaders(self):
                return [
                    ("x-kokoro-request-id", "skill-sandbox-abc"),
                    ("cache-control", "no-store"),
                ]

        class Connection:
            def __init__(self, *_args, **_kwargs):
                pass

            def request(self, *args, **kwargs):
                sent.append((args, kwargs))

            def getresponse(self):
                return Response()

            def close(self):
                pass

        with (
            patch.object(smoke.http.client, "HTTPConnection", Connection),
            patch.object(smoke.secrets, "token_hex", return_value="abc"),
        ):
            status, body = smoke.platform_published_skill_get(
                "http://127.0.0.1:4402",
                "skill-current",
                "projection-token",
                smoke.require_sandbox_ready(ready()),
            )
        smoke.require_platform_published_skill_absent(status, body)
        args, kwargs = sent[0]
        self.assertEqual(args, ("GET", "/v1/skills/skill-current"))
        self.assertEqual(kwargs["headers"]["authorization"], "Bearer projection-token")
        self.assertEqual(kwargs["headers"]["x-kokoro-tenant-id"], "tenant-one")
        self.assertEqual(kwargs["headers"]["x-kokoro-subject"], "user-one")
        self.assertNotIn("x-kokoro-internal-secret", kwargs["headers"])
        with (
            patch.object(smoke.http.client, "HTTPConnection", Connection),
            patch.object(smoke.secrets, "token_hex", return_value="abc"),
        ):
            smoke.platform_published_skill_get(
                "http://127.0.0.1:4402",
                "skill-current",
                "projection-token",
                smoke.require_sandbox_ready(ready()),
                tenant_assertion="other-tenant",
            )
        self.assertEqual(sent[1][1]["headers"]["x-kokoro-tenant-id"], "other-tenant")

    def test_platform_published_read_accepts_only_exact_safe_owner_projection(self):
        data = {
            "skill_id": "skill-current",
            "source_ref": "skill:skill-current",
            "revision": "1",
            "status": "active",
            "name": "Sandbox skill",
            "summary": "sandbox draft",
            "tags": ["sandbox"],
            "product": formal_product(),
            "example_prompts": [],
            "category_keys": [],
            "skill_updated_at": "2026-10-08T01:00:00.000Z",
        }
        smoke.require_platform_published_skill_read(
            200, {"data": data}, "skill-current", "1"
        )
        for mutation in (
            {"skill_id": "skill-other"},
            {"source_ref": "skill:skill-other"},
            {"revision": "0"},
            {"revision": "2"},
            {"status": "draft"},
            {"tags": "sandbox"},
            {"package_asset_ref": "private"},
        ):
            with self.subTest(mutation=mutation), self.assertRaises(smoke.SmokeError):
                smoke.require_platform_published_skill_read(
                    200, {"data": {**data, **mutation}}, "skill-current", "1"
                )

    def test_platform_published_read_requires_not_found_before_publish(self):
        smoke.require_platform_published_skill_absent(
            404,
            {
                "error": {
                    "code": "capability.route_not_found",
                    "message": "Capability BFF route was not found",
                    "retryable": False,
                }
            },
        )
        with self.assertRaises(smoke.SmokeError):
            smoke.require_platform_published_skill_absent(200, {"data": {}})

    def test_bff_published_read_revocation_does_not_leak_data(self):
        denied = {
            "error": {
                "code": "session_invalid",
                "message": "BFF user admission failed",
                "retryable": False,
            }
        }
        smoke.require_bff_projection_revoked(401, denied)
        for status, body in (
            (200, denied),
            (401, {**denied, "data": {"name": "private"}}),
            (401, {"error": {"code": "session_invalid"}}),
            (401, {"error": {**denied["error"], "retryable": True}}),
            (401, {"error": {**denied["error"], "message": "Bearer leaked"}}),
        ):
            with (
                self.subTest(status=status, body=body),
                self.assertRaises(smoke.SmokeError),
            ):
                smoke.require_bff_projection_revoked(status, body)

    def test_bff_personal_list_rejects_mixed_scope_or_private_fields(self):
        item = {
            "source_ref": "skill:skill-current",
            "name": "Sandbox skill",
            "description": "sandbox draft",
            "content_hash": "sha256:public",
            "scope": "personal",
            "revision": "1",
            "enabled": True,
            "product": formal_product(),
            "example_prompts": [],
            "category_keys": [],
            "skill_updated_at": "2026-10-08T01:00:00.000Z",
            "publisher_profile": {
                "kind": "user",
                "id": "user-one",
                "status": "missing",
            },
        }
        page = {"data": {"skills": [item], "next_cursor": None}}
        smoke.require_bff_personal_skill_list(200, page, "skill-current", "1")
        smoke.require_bff_personal_skill_list(
            200,
            {"data": {"skills": [{**item, "description": ""}], "next_cursor": None}},
            "skill-current",
            "1",
        )
        for mutation in (
            {"scope": "organization"},
            {"package_asset_ref": "private"},
            {"revision": "0"},
        ):
            with self.subTest(mutation=mutation), self.assertRaises(smoke.SmokeError):
                smoke.require_bff_personal_skill_list(
                    200,
                    {"data": {"skills": [{**item, **mutation}], "next_cursor": None}},
                    "skill-current",
                    "1",
                )

    def test_public_publish_requires_exact_active_owner_event_projection(self):
        valid = {
            "data": {
                "source_ref": "skill:skill-current",
                "revision": "1",
                "status": "active",
                "event_id": "123e4567-e89b-12d3-a456-426614174000",
                "replayed": False,
                "state_version": "1",
            }
        }
        self.assertFalse(
            smoke.require_public_skill_publish(200, valid, "skill-current")["replayed"]
        )
        self.assertFalse(
            smoke.require_public_skill_publish(
                200,
                {
                    "data": {
                        **valid["data"],
                        "revision": "18446744073709551615",
                    }
                },
                "skill-current",
            )["replayed"]
        )
        for mutation in (
            {"source_ref": "skill:other"},
            {"revision": "0"},
            {"revision": "01"},
            {"revision": "18446744073709551616"},
            {"revision": "9" * 21},
            {"status": "validated"},
            {"event_id": "NOT-UUID"},
            {"replayed": "false"},
            {"asset_id": "private"},
        ):
            with self.subTest(mutation=mutation), self.assertRaises(smoke.SmokeError):
                smoke.require_public_skill_publish(
                    200,
                    {"data": {**valid["data"], **mutation}},
                    "skill-current",
                )

    def test_publish_request_sends_zero_bytes_without_json_content_type(self):
        sent = []

        class Response:
            status = 200

            def read(self, _limit):
                return b'{"data":{"source_ref":"skill:skill-current","revision":"1","status":"active","event_id":"123e4567-e89b-12d3-a456-426614174000","replayed":false}}'

            def getheaders(self):
                return [
                    ("x-request-id", "skill-sandbox-abc"),
                    ("cache-control", "no-store"),
                ]

        class Connection:
            def __init__(self, *_args, **_kwargs):
                pass

            def request(self, *args, **kwargs):
                sent.append((args, kwargs))

            def getresponse(self):
                return Response()

            def close(self):
                pass

        with (
            patch.object(smoke.http.client, "HTTPConnection", Connection),
            patch.object(smoke.secrets, "token_hex", return_value="abc"),
        ):
            status, body = smoke._http_publish_empty(
                "http://127.0.0.1:4401",
                "/v1/skills/skill-current/publish",
                token="TOKEN",
                secret="SECRET",
                key="publish-key",
            )
        self.assertEqual(status, 200)
        self.assertEqual(body["data"]["status"], "active")
        self.assertEqual(len(sent), 1)
        args, kwargs = sent[0]
        self.assertEqual(args, ("POST", "/v1/skills/skill-current/publish"))
        self.assertEqual(kwargs["body"], b"")
        self.assertEqual(kwargs["headers"]["content-length"], "0")
        self.assertNotIn("content-type", kwargs["headers"])

    def test_signed_put_zip_fixture_uses_strict_v2_manifest_without_embedded_identity(
        self,
    ):
        payload = smoke.upload_zip_bytes("skill-current", 1)
        with zipfile.ZipFile(BytesIO(payload)) as archive:
            self.assertEqual(archive.namelist(), ["manifest.json", "SKILL.md"])
            self.assertEqual(
                json.loads(archive.read("manifest.json")),
                {
                    "schema_version": 2,
                    "entry": "SKILL.md",
                },
            )
            self.assertIn(b"# Sandbox", archive.read("SKILL.md"))
        with self.assertRaises(smoke.SmokeError):
            smoke.upload_zip_bytes("../other", 1)
        with self.assertRaises(smoke.SmokeError):
            smoke.upload_zip_bytes("skill-current", 0)

    def test_public_validate_requires_exact_owner_verified_zip_projection(self):
        valid = {
            "data": {
                "skill_id": "skill-current",
                "series_id": "series-current",
                "valid": True,
                "content_digest": "a" * 64,
                "manifest_identity": "zip-v2:sha256:" + "b" * 64,
                "replayed": False,
                "state_version": "1",
            }
        }
        self.assertFalse(
            smoke.require_public_skill_validate(
                200, valid, "skill-current", "series-current", "a" * 64
            )["replayed"]
        )
        for mutation in (
            {"skill_id": "other"},
            {"series_id": "other"},
            {"valid": False},
            {"content_digest": "A" * 64},
            {"manifest_identity": "zip-v2:sha256:INVALID"},
            {"manifest_identity": "zip-v1:sha256:" + "b" * 64},
            {"replayed": "false"},
            {"asset_id": "private"},
        ):
            with self.subTest(mutation=mutation), self.assertRaises(smoke.SmokeError):
                smoke.require_public_skill_validate(
                    200,
                    {"data": {**valid["data"], **mutation}},
                    "skill-current",
                    "series-current",
                    "a" * 64,
                )

    def test_public_complete_requires_current_uploaded_projection(self):
        valid = {
            "data": {
                "skill_id": "skill-current",
                "attempt_id": "attempt-current",
                "attempt_epoch": "2",
                "upload_id": "upload-current",
                "phase": "uploaded",
                "replayed": False,
                "content_sha256": "a" * 64,
                "scan_state": "clean",
                "state_version": "1",
            }
        }
        for scan in ("clean", "pending", "unknown"):
            smoke.require_public_package_complete(
                200,
                {"data": {**valid["data"], "scan_state": scan}},
                "skill-current",
                "attempt-current",
                "upload-current",
                "2",
                "a" * 64,
            )
        mutations = (
            {"skill_id": "other"},
            {"attempt_id": "old"},
            {"attempt_epoch": "0"},
            {"upload_id": "other"},
            {"content_sha256": "b" * 64},
            {"phase": "validated"},
            {"scan_state": "infected"},
            {"scan_state": "scanning"},
            {"replayed": "false"},
            {"asset_id": "internal"},
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation), self.assertRaises(smoke.SmokeError):
                smoke.require_public_package_complete(
                    200,
                    {"data": {**valid["data"], **mutation}},
                    "skill-current",
                    "attempt-current",
                    "upload-current",
                    "2",
                    "a" * 64,
                )

    def test_public_begin_requires_exact_current_signed_put_projection(self):
        expires = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
        response = {
            "data": {
                "skill_id": "skill-current",
                "attempt_id": "attempt-one",
                "attempt_epoch": "1",
                "upload_id": "upload-one",
                "transfer_reference": {
                    "url": "http://127.0.0.1:39190/owned/key?X-Amz-Signature=abc",
                    "method": "PUT",
                    "required_headers": {"content-type": "application/zip"},
                    "expires_at": expires,
                },
                "replayed": False,
                "state_version": "1",
            }
        }
        reference = smoke.require_public_package_begin(
            201, response, "skill-current", "http://127.0.0.1:39190"
        )
        self.assertEqual(reference["attempt_id"], "attempt-one")
        self.assertFalse(reference["replayed"])
        mutations = (
            {"attempt_epoch": "0"},
            {"replayed": "false"},
            {"secret": "leak"},
            {
                "transfer_reference": {
                    **response["data"]["transfer_reference"],
                    "method": "POST",
                }
            },
            {
                "transfer_reference": {
                    **response["data"]["transfer_reference"],
                    "required_headers": {"authorization": "secret"},
                }
            },
            {
                "transfer_reference": {
                    **response["data"]["transfer_reference"],
                    "url": "http://other.example/key",
                }
            },
            {
                "transfer_reference": {
                    **response["data"]["transfer_reference"],
                    "expires_at": (
                        datetime.now(timezone.utc) - timedelta(minutes=1)
                    ).isoformat(),
                }
            },
            {
                "transfer_reference": {
                    **response["data"]["transfer_reference"],
                    "expires_at": (
                        datetime.now(timezone.utc) + timedelta(minutes=16)
                    ).isoformat(),
                }
            },
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation), self.assertRaises(smoke.SmokeError):
                smoke.require_public_package_begin(
                    201,
                    {"data": {**response["data"], **mutation}},
                    "skill-current",
                    "http://127.0.0.1:39190",
                )

    def test_package_response_request_id_must_match_exactly_once(self):
        request_id = "skill-sandbox-exact"
        headers = [("x-request-id", request_id), ("cache-control", "no-store")]
        smoke.require_package_response_headers(headers, request_id, "Begin")
        for invalid in (
            headers + [("X-Request-Id", request_id)],
            [("x-request-id", "stale"), ("cache-control", "no-store")],
            [("x-request-id", request_id), ("cache-control", "public")],
            [("cache-control", "no-store")],
        ):
            with self.subTest(invalid=invalid), self.assertRaises(smoke.SmokeError):
                smoke.require_package_response_headers(invalid, request_id, "Begin")

    def test_signed_reference_is_added_to_log_secret_inventory(self):
        url = "http://127.0.0.1:39190/bucket/key?X-Amz-Signature=long-signature-value&X-Amz-Credential=long-credential-value"
        values = smoke.signed_reference_secrets(url)
        self.assertIn(url, values)
        self.assertIn("X-Amz-Signature=long-signature-value", values)
        self.assertIn("long-signature-value", values)
        self.assertIn("long-credential-value", values)

    def test_public_get_requires_current_pending_after_begin(self):
        pending = {
            "data": {
                "skill_id": "skill-current",
                "attempt_epoch": "1",
                "phase": "upload_pending",
                "attempt_id": "attempt-one",
                "upload_id": "upload-one",
                "state_version": "1",
            }
        }
        smoke.require_public_package_pending(
            200, pending, "skill-current", "attempt-one", "upload-one", "1"
        )
        with self.assertRaises(smoke.SmokeError):
            smoke.require_public_package_pending(
                200,
                {"data": {**pending["data"], "phase": "uploaded"}},
                "skill-current",
                "attempt-one",
                "upload-one",
                "1",
            )

    def test_public_get_uploaded_and_aborted_remain_current_and_minimal(self):
        uploaded = {
            "data": {
                "skill_id": "skill-current",
                "attempt_epoch": "2",
                "phase": "uploaded",
                "attempt_id": "attempt-two",
                "upload_id": "upload-two",
                "state_version": "1",
            }
        }
        smoke.require_public_package_uploaded(
            200, uploaded, "skill-current", "attempt-two", "upload-two", "2"
        )
        smoke.require_public_package_validated(
            200,
            {"data": {**uploaded["data"], "phase": "validated"}},
            "skill-current",
            "attempt-two",
            "upload-two",
            "2",
        )
        with self.assertRaises(smoke.SmokeError):
            smoke.require_public_package_validated(
                200,
                {
                    "data": {
                        **uploaded["data"],
                        "phase": "validated",
                        "asset_id": "leak",
                    }
                },
                "skill-current",
                "attempt-two",
                "upload-two",
                "2",
            )
        aborted = {
            "data": {
                "skill_id": "skill-current",
                "attempt_epoch": "3",
                "phase": "aborted",
                "attempt_id": "attempt-three",
                "upload_id": "upload-three",
                "state_version": "1",
            }
        }
        smoke.require_public_package_aborted(
            200, aborted, "skill-current", "attempt-three", "upload-three", "3"
        )
        with self.assertRaises(smoke.SmokeError):
            smoke.require_public_package_uploaded(
                200,
                {"data": {**uploaded["data"], "asset_id": "leak"}},
                "skill-current",
                "attempt-two",
                "upload-two",
                "2",
            )
        with self.assertRaises(smoke.SmokeError):
            smoke.require_public_package_aborted(
                200,
                {"data": {**aborted["data"], "phase": "uploaded"}},
                "skill-current",
                "attempt-three",
                "upload-three",
                "3",
            )
        with self.assertRaises(smoke.SmokeError):
            smoke.require_public_package_aborted(
                200,
                {"data": {**aborted["data"], "upload_id": "upload-other"}},
                "skill-current",
                "attempt-three",
                "upload-three",
                "3",
            )

    def test_success_summary_requires_complete_receipt_inventory(self):
        self.assertEqual(
            smoke.safe_summary(None),
            {
                "status": "PASS",
                "resources": "clean",
                "platform_skill_count": 2,
                "platform_receipt_count": 31,
                "platform_publish_event_count": 2,
                "platform_package_begin": "PASS",
                "platform_package_complete": "PASS",
                "platform_package_infected": "PASS",
                "platform_package_validate": "PASS",
                "platform_package_bad_zip": "PASS",
                "platform_publish": "PASS",
                "platform_publish_replay": "PASS",
                "platform_publish_negative": "PASS",
                "bff_skill_package_get": "PASS",
                "bff_skill_package_get_published": "PASS",
                "bff_skill_package_get_revoked": "PASS",
                "bff_skill_package_begin": "PASS",
                "bff_skill_package_begin_replay": "PASS",
                "bff_skill_package_begin_replace": "PASS",
                "bff_skill_package_signed_put": "PASS",
                "bff_skill_package_begin_revoked": "PASS",
                "bff_skill_package_complete": "PASS",
                "bff_skill_package_complete_replay": "PASS",
                "bff_skill_package_complete_infected": "PASS",
                "bff_skill_package_complete_recovery": "PASS",
                "bff_skill_package_complete_revoked": "PASS",
                "bff_skill_validate": "PASS",
                "bff_skill_validate_bad_zip": "PASS",
                "bff_skill_validate_recovery": "PASS",
                "bff_skill_validate_replay": "PASS",
                "bff_skill_validate_stale_attempt": "PASS",
                "bff_skill_validate_revoked": "PASS",
                "bff_skill_publish": "PASS",
                "bff_skill_publish_replay": "PASS",
                "bff_skill_publish_conflict": "PASS",
                "bff_skill_publish_event_durable": "PASS",
                "bff_skill_publish_revoked": "PASS",
                "platform_published_by_id": "PASS",
                "platform_published_private": "PASS",
                "bff_published_before_publish": "PASS",
                "bff_published_after_publish": "PASS",
                "bff_personal_skill_list": "PASS",
                "bff_published_read_revoked": "PASS",
                "bff_personal_list_revoked": "PASS",
            },
        )

    def test_public_get_requires_exact_current_none_state(self):
        expected = {
            "data": {
                "skill_id": "skill-current",
                "attempt_epoch": "0",
                "phase": "none",
                "state_version": "1",
            }
        }
        smoke.require_public_package_get(200, expected, "skill-current")
        for body in (
            {"data": {**expected["data"], "attempt_id": "attempt-old"}},
            {"data": {**expected["data"], "attempt_epoch": "1"}},
            {"data": {**expected["data"], "phase": "uploaded"}},
            {"data": {**expected["data"], "secret": "leak"}},
            {"data": {**expected["data"], "skill_id": "other"}},
        ):
            with self.subTest(body=body), self.assertRaises(smoke.SmokeError):
                smoke.require_public_package_get(200, body, "skill-current")

    def test_package_probe_receives_only_storage_boundary_and_current_skill(self):
        parsed = smoke.require_sandbox_ready(ready())
        env = smoke.platform_package_probe_env(
            {"PATH": "/usr/bin", "NODE_ENV": "development"},
            Path("/opt/node24/bin/node"),
            "http://127.0.0.1:4402",
            "http://127.0.0.1:4403",
            "http://127.0.0.1:4404",
            "platform-secret",
            parsed,
            "skill-current",
        )
        self.assertEqual(env["KOKORO_SMOKE_TENANT_ID"], "tenant-one")
        self.assertEqual(env["KOKORO_SMOKE_SUBJECT_ID"], "user-one")
        self.assertEqual(env["KOKORO_SMOKE_SKILL_ID"], "skill-current")
        self.assertEqual(env["KOKORO_STORAGE_URL"], "http://127.0.0.1:4402")
        self.assertEqual(env["KOKORO_SMOKE_PLATFORM_URL"], "http://127.0.0.1:4403")
        self.assertEqual(env["KOKORO_SMOKE_IAM_URL"], "http://127.0.0.1:4404")
        self.assertEqual(env["KOKORO_SMOKE_CATALOG_CLIENT_ID"], "catalog")
        self.assertEqual(env["KOKORO_SMOKE_CATALOG_CLIENT_SECRET"], "catalog-secret")
        self.assertEqual(env["PATH"], "/opt/node24/bin:/usr/bin")
        self.assertNotIn("KOKORO_PLATFORM_IAM_TENANT_CREDENTIALS_FILE", env)
        with self.assertRaises(smoke.SmokeError):
            smoke.platform_package_probe_env(
                {"PATH": "/usr/bin"},
                Path("/opt/node24/bin/node"),
                "http://127.0.0.1:4402",
                "http://127.0.0.1:4403",
                "http://127.0.0.1:4404",
                "platform-secret",
                parsed,
                " ",
            )

    def test_ready_protocol_is_exact_and_loopback(self):
        value = smoke.require_sandbox_ready(ready())
        self.assertEqual(value.tenant_id, "tenant-one")
        self.assertEqual(value.projection.client_id, "projection")
        self.assertEqual(len(value.secrets), 7)
        self.assertIn("web-secret", value.secrets)
        self.assertIn("password", value.secrets)
        for mutation in (
            {**ready(), "unexpected": "x"},
            {**ready(), "base_url": "http://127.0.0.1:3310"},
            {**ready(), "base_url": "https://public.example.test"},
            {
                **ready(),
                "skill_sandbox": {**ready()["skill_sandbox"], "access_token": ""},
            },
        ):
            with self.subTest(mutation=mutation), self.assertRaises(smoke.SmokeError):
                smoke.require_sandbox_ready(mutation)

    def test_agent_source_ready_requires_explicit_mode_and_exact_credential(self):
        record = ready()
        record["skill_sandbox"]["tenant_execution_client"] = {
            "client_id": "agent-source",
            "client_secret": "agent-source-secret",
        }
        with self.assertRaises(smoke.SmokeError):
            smoke.require_sandbox_ready(record)
        parsed = smoke.require_sandbox_ready(record, agent_source=True)
        self.assertEqual(parsed.tenant_execution.client_id, "agent-source")
        self.assertIn("agent-source-secret", parsed.secrets)
        self.assertEqual(len(parsed.secrets), 8)
        self.assertIsNone(smoke.require_sandbox_ready(ready()).tenant_execution)
        for invalid_mode in ("1", "0", 1, 0, None):
            with self.subTest(mode=invalid_mode), self.assertRaises(smoke.SmokeError):
                smoke.require_sandbox_ready(record, agent_source=invalid_mode)
        for invalid in (
            None,
            {},
            {"client_id": "agent"},
            {
                "client_id": "agent",
                "client_secret": "secret",
                "private_key": "forbidden",
            },
            {"client_id": "agent", "client_secret": " "},
        ):
            changed = ready()
            changed["skill_sandbox"]["tenant_execution_client"] = invalid
            with self.subTest(invalid=invalid), self.assertRaises(smoke.SmokeError):
                smoke.require_sandbox_ready(changed, agent_source=True)
        with self.assertRaises(smoke.SmokeError):
            smoke.require_sandbox_ready(ready(), agent_source=True)

    def test_agent_source_credentials_are_redacted_from_diagnostics(self):
        record = ready()
        record["skill_sandbox"]["tenant_execution_client"] = {
            "client_id": "agent-source",
            "client_secret": "agent-source-secret",
        }
        parsed = smoke.require_sandbox_ready(record, agent_source=True)
        summary = smoke.safe_summary(
            smoke.SmokeError("failure agent-source-secret"), parsed.secrets
        )
        self.assertNotIn("agent-source-secret", json.dumps(summary))

    def test_revoke_protocol_is_exact(self):
        smoke.require_revoke_result(
            {"kind": "result", "command": "revoke-user-session", "status": "ok"}
        )
        with self.assertRaises(smoke.SmokeError):
            smoke.require_revoke_result(
                {
                    "kind": "result",
                    "command": "revoke-user-session",
                    "status": "ok",
                    "token": "leak",
                }
            )

    def test_credential_file_is_0600_and_removed(self):
        with smoke.credential_file(
            {"client_id": "catalog", "client_secret": "secret"}
        ) as path:
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            self.assertEqual(
                json.loads(path.read_text()),
                {"client_id": "catalog", "client_secret": "secret"},
            )
            parent = path.parent
        self.assertFalse(path.exists())
        self.assertFalse(parent.exists())

    def test_owner_credential_projections_are_exact(self):
        parsed = smoke.require_sandbox_ready(ready())
        resource, execution, catalog, projection = smoke.platform_credential_payloads(
            parsed
        )
        self.assertEqual(
            resource,
            {
                "generation": 1,
                "credentialRefVersion": "sandbox-v1",
                "clientId": "resource",
                "clientSecret": "resource-secret",
            },
        )
        self.assertEqual(catalog[0]["tenantId"], "tenant-one")
        self.assertEqual(
            catalog[0]["resource"], "https://kokoro.dev/resources/platform-internal"
        )
        self.assertEqual(catalog[0]["scope"], "platform:skill-catalog.manage")
        self.assertEqual(
            projection,
            [
                {
                    "generation": 1,
                    "credentialRefVersion": "sandbox-v1",
                    "tenantId": "tenant-one",
                    "clientId": "projection",
                    "clientSecret": "projection-secret",
                    "resource": "https://kokoro.dev/resources/platform-internal",
                    "scope": "platform:projection.read",
                }
            ],
        )
        self.assertEqual(
            execution[0]["resource"], "https://kokoro.dev/resources/iam-internal"
        )
        self.assertEqual(execution[0]["scope"], "iam:execution-authorization.verify")
        self.assertEqual(execution[0]["clientId"], "execution")
        self.assertEqual(execution[0]["clientSecret"], "execution-secret")

    def test_projection_credential_file_is_owned_and_removed(self):
        parsed = smoke.require_sandbox_ready(ready())
        with tempfile.TemporaryDirectory() as owned:
            directory = Path(owned)
            with smoke.credential_files(directory, parsed) as paths:
                projection = paths["bff-projection.json"]
                self.assertEqual(projection.stat().st_mode & 0o777, 0o600)
                self.assertEqual(
                    json.loads(projection.read_text()),
                    smoke.platform_credential_payloads(parsed)[3],
                )
            self.assertFalse(projection.exists())

    def test_cleanup_verification_attempts_every_inventory_after_failures(self):
        calls = []

        def redis():
            calls.append("redis")
            raise RuntimeError("secret")

        def database(_name):
            calls.append("database")
            return True

        failures = smoke.verify_cleanup(
            before_redis=set(),
            redis_snapshot=redis,
            database_name="owned_database",
            database_exists=database,
        )
        self.assertEqual(calls, ["redis", "database"])
        self.assertEqual(
            failures,
            [
                "Redis cleanup verification failed",
                "IAM owned database was not removed",
            ],
        )

    def test_process_cleanup_attempts_all_consumers_then_iam_after_failure(self):
        events = []

        class Input:
            def write(self, value):
                events.append(("write", value))

            def flush(self):
                events.append("flush")

        class Process:
            def __init__(self, name):
                self.name, self.stdin = name, Input()

            def poll(self):
                return None

            def wait(self, timeout):
                events.append(("wait", self.name, timeout))

        class Reader:
            def record(self, timeout):
                events.append(("record", timeout))
                return {"kind": "result", "command": "stop", "status": "ok"}

        def stop(process):
            events.append(("stop", None if process is None else process.name))
            if process is not None and process.name == "second":
                raise RuntimeError("boom")

        failures = smoke.stop_owned_processes(
            [Process("first"), Process("second")], Process("iam"), Reader(), stop
        )
        self.assertEqual(failures, ["owned consumer process cleanup failed"])
        self.assertLess(
            events.index(("stop", "first")),
            events.index(("write", b'{"command":"stop"}\n')),
        )
        self.assertEqual(events[-1], ("stop", "iam"))

    def test_owned_bucket_is_created_versioned_and_deleted_only_after_creation(self):
        class Missing(Exception):
            response = {"ResponseMetadata": {"HTTPStatusCode": 404}}

        class S3:
            def __init__(self):
                self.calls = []

            def create_bucket(self, **kw):
                self.calls.append(("create", kw))

            def put_bucket_versioning(self, **kw):
                self.calls.append(("version", kw))

            def list_object_versions(self, **kw):
                self.calls.append(("list", kw))
                return {"Versions": [], "DeleteMarkers": []}

            def delete_bucket(self, **kw):
                self.calls.append(("delete", kw))

            def head_bucket(self, **kw):
                self.calls.append(("head", kw))
                raise Missing()

        class Helper:
            @staticmethod
            def _list_versions(_s3, _bucket, _prefix):
                return []

        s3 = S3()
        smoke.create_owned_bucket(s3, "owned-bucket", "us-east-1")
        smoke.delete_owned_bucket(s3, "owned-bucket", Helper)
        smoke.require_bucket_absent(s3, "owned-bucket")
        self.assertEqual(s3.calls[0][0], "create")
        self.assertTrue(s3.calls[0][1]["ObjectLockEnabledForBucket"])
        self.assertEqual(
            [call[0] for call in s3.calls][-3:], ["delete", "head", "head"]
        )

    def test_bucket_absence_rejects_a_still_visible_bucket(self):
        class S3:
            def head_bucket(self, **_kw):
                return {}

        with self.assertRaisesRegex(smoke.SmokeError, "still exists"):
            smoke.require_bucket_absent(S3(), "owned-bucket")

    def test_owned_bucket_name_always_preserves_random_run_identity(self):
        run_id = "a" * 24
        name = smoke.owned_bucket_name("x" * 63, run_id)
        self.assertLessEqual(len(name), 63)
        self.assertTrue(name.endswith("-" + run_id))

    def test_owned_bucket_cleanup_removes_delete_markers(self):
        class Missing(Exception):
            response = {"ResponseMetadata": {"HTTPStatusCode": 404}}

        class S3:
            def __init__(self):
                self.deleted = []
                self.calls = 0

            def list_object_versions(self, **_kw):
                self.calls += 1
                if self.calls == 1:
                    return {
                        "Versions": [],
                        "DeleteMarkers": [{"Key": "marker", "VersionId": "v1"}],
                    }
                return {"Versions": [], "DeleteMarkers": []}

            def delete_object(self, **kw):
                self.deleted.append(kw)

            def delete_bucket(self, **_kw):
                pass

            def head_bucket(self, **_kw):
                raise Missing()

        s3 = S3()
        smoke.delete_owned_bucket(s3, "owned-bucket", object())
        self.assertEqual(
            s3.deleted, [{"Bucket": "owned-bucket", "Key": "marker", "VersionId": "v1"}]
        )

    def test_formal_missing_catalog_dependency_remains_closed_without_flag(self):
        import ast

        tree = ast.parse(PATH.read_text())
        execute = next(
            n
            for n in tree.body
            if isinstance(n, ast.FunctionDef) and n.name == "execute"
        )
        code = ast.unparse(execute)
        self.assertNotIn("KOKORO_SKILL_DRAFT_CANDIDATE_ENABLED", code)
        credential = "bff_env['KOKORO_BFF_PLATFORM_CATALOG_CREDENTIALS_FILE'] = str(files['bff-catalog.json'])"
        self.assertLess(code.index("closed = _start("), code.index(credential))
        self.assertLess(code.index(credential), code.index("active = _start("))
        self.assertIn("if proxy.count != 0:", code)
        self.assertIn(
            "'KOKORO_PLATFORM_PROJECTION_CREDENTIAL_FILE': str(files['bff-projection.json'])",
            code,
        )

    def test_redis_inventory_requires_an_owned_pattern(self):
        with self.assertRaises(smoke.SmokeError):
            smoke._redis_keys("redis://127.0.0.1/5", "*")

    def test_main_parameter_and_source_failures_emit_safe_json_without_traceback(self):
        output = StringIO()
        with patch.object(sys, "argv", [str(PATH)]), patch("sys.stdout", output):
            self.assertEqual(smoke.main(), 1)
        self.assertEqual(
            json.loads(output.getvalue()),
            {"status": "FAIL", "error": "invalid runner arguments"},
        )
        self.assertNotIn("Traceback", output.getvalue())

    def test_database_urls_bind_only_the_three_owner_schemas(self):
        admin = "postgresql://app@127.0.0.1:5432/postgres"
        self.assertEqual(
            smoke.owner_database_url(admin, "sandbox_abc", "kokoro_platform"),
            "postgresql://app@127.0.0.1:5432/sandbox_abc?schema=kokoro_platform",
        )
        with self.assertRaises(smoke.SmokeError):
            smoke.owner_database_url(admin, "sandbox_abc", "public")

    def test_platform_inventory_removes_only_prisma_schema_selector(self):
        self.assertEqual(
            smoke.platform_inventory_connection_url(
                "postgresql://app@127.0.0.1:5432/db?sslmode=disable&schema=kokoro_platform"
            ),
            "postgresql://app@127.0.0.1:5432/db?sslmode=disable",
        )
        for invalid in (
            "postgresql://app@127.0.0.1/db",
            "postgresql://app@127.0.0.1/db?schema=kokoro_bff",
            "postgresql://app@127.0.0.1/db?schema=kokoro_platform&schema=kokoro_platform",
            "postgresql://app@db.example.test/db?schema=kokoro_platform",
            "postgresql://app@127.0.0.1/db?schema=kokoro_platform&options=-csearch_path%3Dpublic",
        ):
            with self.subTest(invalid=invalid), self.assertRaises(smoke.SmokeError):
                smoke.platform_inventory_connection_url(invalid)

    def test_postgres_admin_url_adds_encoded_os_user_only_when_missing(self):
        self.assertEqual(
            smoke.normalized_postgres_admin_url(
                "postgresql://127.0.0.1:5432/postgres?sslmode=disable",
                lambda: "local+user",
            ),
            "postgresql://local%2Buser@127.0.0.1:5432/postgres?sslmode=disable",
        )
        existing = "postgresql://explicit:secret@127.0.0.1:5432/postgres"
        self.assertEqual(
            smoke.normalized_postgres_admin_url(existing, lambda: "ignored"), existing
        )

    def test_postgres_admin_url_rejects_invalid_or_nonlocal_identity(self):
        for raw, user in (
            ("postgresql://db.example.test/postgres", "local"),
            ("postgresql://127.0.0.1/postgres", ""),
            ("postgresql://127.0.0.1/postgres", "bad\nuser"),
        ):
            with self.subTest(raw=raw, user=user), self.assertRaises(smoke.SmokeError):
                smoke.normalized_postgres_admin_url(raw, lambda: user)

    def test_counting_proxy_observes_connections_without_payload_inspection(self):
        import socket
        import threading

        server = socket.socket()
        server.bind(("127.0.0.1", 0))
        server.listen()
        port = server.getsockname()[1]

        def echo():
            client, _ = server.accept()
            client.sendall(client.recv(1024))
            client.close()

        worker = threading.Thread(target=echo)
        worker.start()
        proxy = smoke.CountingTcpProxy(port)
        client = socket.create_connection(("127.0.0.1", proxy.port))
        request = b"GET / HTTP/1.1\r\nHost: owner\r\nContent-Length: 0\r\n\r\n"
        client.sendall(request)
        self.assertEqual(client.recv(len(request)), request)
        client.close()
        worker.join()
        server.close()
        proxy.close()
        self.assertEqual(proxy.count, 1)
        self.assertEqual(proxy.request_count, 1)

    def test_counting_proxy_counts_fragmented_keepalive_requests_without_treating_body_as_headers(
        self,
    ):
        import socket
        import threading

        server = socket.socket()
        server.bind(("127.0.0.1", 0))
        server.listen()
        received = bytearray()
        complete = threading.Event()
        first = b"POST /one HTTP/1.1\r\nHost: owner\r\nContent-Length: 5\r\n\r\nabcde"
        second = b"POST /two HTTP/1.1\r\nHost: owner\r\nContent-Length: 3\r\n\r\nxyz"
        expected = first + second

        def consume():
            client, _ = server.accept()
            client.settimeout(2)
            try:
                while len(received) < len(expected):
                    chunk = client.recv(1024)
                    if not chunk:
                        break
                    received.extend(chunk)
                complete.set()
            finally:
                client.close()

        worker = threading.Thread(target=consume)
        worker.start()
        proxy = smoke.CountingTcpProxy(server.getsockname()[1])
        client = socket.create_connection(("127.0.0.1", proxy.port))
        try:
            for fragment in (
                expected[:7],
                expected[7:53],
                expected[53:61],
                expected[61:95],
                expected[95:],
            ):
                client.sendall(fragment)
            self.assertTrue(complete.wait(2))
            self.assertEqual(bytes(received), expected)
            self.assertEqual(proxy.request_count, 2)
            self.assertEqual(proxy.protocol_failure_count, 0)
        finally:
            client.close()
            worker.join(timeout=2)
            server.close()
            proxy.close()

    def test_counting_proxy_counts_fragmented_chunked_keepalive_requests_with_bounded_trailers(
        self,
    ):
        import socket
        import threading

        server = socket.socket()
        server.bind(("127.0.0.1", 0))
        server.listen()
        first = b"POST /one HTTP/1.1\r\nHost: owner\r\nTransfer-Encoding: chunked\r\n\r\n2\r\nab\r\n3\r\ncde\r\n0\r\nX-Proof: one\r\n\r\n"
        second = b"POST /two HTTP/1.1\r\nHost: owner\r\nTransfer-Encoding: chunked\r\n\r\n1\r\nx\r\n0\r\n\r\n"
        expected = first + second
        received = bytearray()
        complete = threading.Event()

        def consume():
            client, _ = server.accept()
            client.settimeout(2)
            try:
                while len(received) < len(expected):
                    chunk = client.recv(1024)
                    if not chunk:
                        break
                    received.extend(chunk)
                complete.set()
            finally:
                client.close()

        worker = threading.Thread(target=consume)
        worker.start()
        proxy = smoke.CountingTcpProxy(server.getsockname()[1])
        client = socket.create_connection(("127.0.0.1", proxy.port))
        try:
            cuts = (9, 51, 69, 73, 81, 97, 121, len(expected))
            offset = 0
            for end in cuts:
                client.sendall(expected[offset:end])
                offset = end
            self.assertTrue(complete.wait(2))
            self.assertEqual(bytes(received), expected)
            self.assertEqual(proxy.request_count, 2)
            self.assertEqual(proxy.protocol_failure_count, 0)
        finally:
            client.close()
            worker.join(timeout=2)
            server.close()
            proxy.close()

    def test_counting_proxy_fails_closed_on_malformed_chunk_or_oversized_request_headers(
        self,
    ):
        import socket
        import threading

        def rejected(payload):
            server = socket.socket()
            server.bind(("127.0.0.1", 0))
            server.listen()
            upstream_closed = threading.Event()

            def consume():
                client, _ = server.accept()
                client.settimeout(2)
                try:
                    while client.recv(1024):
                        pass
                    upstream_closed.set()
                finally:
                    client.close()

            worker = threading.Thread(target=consume)
            worker.start()
            proxy = smoke.CountingTcpProxy(server.getsockname()[1])
            client = socket.create_connection(("127.0.0.1", proxy.port))
            client.settimeout(2)
            try:
                client.sendall(payload)
                self.assertEqual(client.recv(1), b"")
                self.assertTrue(upstream_closed.wait(2))
                self.assertEqual(proxy.request_count, 0)
                self.assertEqual(proxy.protocol_failure_count, 1)
                self.assertTrue(proxy.protocol_failed)
            finally:
                client.close()
                worker.join(timeout=2)
                server.close()
                proxy.close()

        rejected(
            b"POST / HTTP/1.1\r\nHost: owner\r\nTransfer-Encoding: chunked\r\n\r\nnot-hex\r\nx\r\n0\r\n\r\n"
        )
        rejected(b"GET / HTTP/1.1\r\nHost: " + b"a" * 65_536)

    def test_http_counter_accepts_empty_chunk_trailer_coalesced_with_next_request(self):
        counter = smoke._HttpRequestCounter()
        counter.feed(
            b"POST /one HTTP/1.1\r\nHost: owner\r\nTransfer-Encoding: chunked\r\n\r\n"
            b"1\r\nx\r\n0\r\n\r\n"
            b"GET /two HTTP/1.1\r\nHost: owner\r\nContent-Length: 0\r\n\r\n"
        )
        self.assertEqual(counter.completed, 2)

    def test_http_counter_rejects_closed_header_section_larger_than_limit(self):
        counter = smoke._HttpRequestCounter()
        with self.assertRaises(ValueError):
            counter.feed(
                b"GET / HTTP/1.1\r\nHost: "
                + b"a" * smoke._HttpRequestCounter.MAX_SECTION
                + b"\r\n\r\n"
            )
        self.assertEqual(counter.completed, 0)

    def test_http_contract_requires_create_replay_and_conflict(self):
        calls = []
        responses = [
            (
                201,
                {
                    "data": {
                        "skill_id": "skill-one",
                        "series_id": "series-one",
                        "revision": 1,
                        "status": "draft",
                        "replayed": False,
                        "state_version": "1",
                    }
                },
            ),
            (
                201,
                {
                    "data": {
                        "skill_id": "skill-one",
                        "series_id": "series-one",
                        "revision": 1,
                        "status": "draft",
                        "replayed": True,
                        "state_version": "1",
                    }
                },
            ),
            (409, {"error": {"code": "skill_idempotency_conflict"}}),
        ]

        def request(**kwargs):
            calls.append(kwargs)
            return responses.pop(0)

        result = smoke.exercise_http_contract(
            request, smoke.require_sandbox_ready(ready())
        )
        self.assertEqual(result["skill_id"], "skill-one")
        self.assertEqual(len(calls), 3)
        self.assertEqual({call["key"] for call in calls}, {"skill-draft-sandbox-key"})
        self.assertTrue(all(call["token"] == "user-token" for call in calls))

    def test_http_contract_rejects_unrelated_409_code(self):
        responses = [
            (
                201,
                {
                    "data": {
                        "skill_id": "s",
                        "series_id": "ss",
                        "revision": 1,
                        "status": "draft",
                        "replayed": False,
                        "state_version": "1",
                    }
                },
            ),
            (
                201,
                {
                    "data": {
                        "skill_id": "s",
                        "series_id": "ss",
                        "revision": 1,
                        "status": "draft",
                        "replayed": True,
                        "state_version": "1",
                    }
                },
            ),
            (409, {"error": {"code": "other_conflict"}}),
        ]
        with self.assertRaisesRegex(smoke.SmokeError, "conflict drift"):
            smoke.exercise_http_contract(
                lambda **_kw: responses.pop(0), smoke.require_sandbox_ready(ready())
            )

    def test_first_draft_failure_reports_only_status_and_whitelisted_code(self):
        with self.assertRaises(smoke.SmokeError) as known:
            smoke.exercise_http_contract(
                lambda **_kw: (
                    401,
                    {
                        "error": {
                            "code": "bff_session_invalid",
                            "message": "token-secret",
                        }
                    },
                ),
                smoke.require_sandbox_ready(ready()),
            )
        self.assertEqual(
            str(known.exception),
            "first Skill draft was not created (status=401, code=bff_session_invalid)",
        )
        with self.assertRaises(smoke.SmokeError) as unknown:
            smoke.exercise_http_contract(
                lambda **_kw: (503, {"error": {"code": "secret/value?token=leak"}}),
                smoke.require_sandbox_ready(ready()),
            )
        self.assertEqual(
            str(unknown.exception),
            "first Skill draft was not created (status=503, code=unknown)",
        )
        self.assertNotIn("secret", str(unknown.exception))
        self.assertNotIn("leak", str(unknown.exception))

    def test_source_gate_rejects_dirty_owner_before_tree_lookup(self):
        calls = []

        class Result:
            def __init__(self, stdout):
                self.stdout = stdout

        def run(argv, **_kwargs):
            calls.append(argv)
            return Result(" M candidate.ts\n")

        with self.assertRaisesRegex(smoke.SmokeError, "source is not frozen"):
            smoke.frozen_sources(run)
        self.assertEqual(len(calls), 1)
        self.assertIn("status", calls[0])

    def test_execute_source_failure_has_no_infrastructure_side_effect(self):
        args = smoke.RunArguments(
            "postgresql://app@127.0.0.1/postgres",
            "redis://127.0.0.1/5",
            Path("/node24"),
            Path("/node22"),
            Path("/node24"),
            Path("/node24"),
            "owned-bucket",
        )
        with (
            patch.object(
                smoke, "frozen_sources", side_effect=smoke.SmokeError("not frozen")
            ),
            patch.object(smoke, "_redis_keys") as redis,
            patch.object(smoke.subprocess, "Popen") as popen,
            self.assertRaisesRegex(smoke.SmokeError, "not frozen"),
        ):
            smoke.execute(args, {})
        redis.assert_not_called()
        popen.assert_not_called()

    def test_summary_redacts_registered_secret_and_never_lists_credentials(self):
        secret = "top-secret-value"
        summary = smoke.safe_summary(smoke.SmokeError("failed " + secret), (secret,))
        encoded = json.dumps(summary)
        self.assertNotIn(secret, encoded)
        self.assertEqual(summary, {"status": "FAIL", "error": "smoke execution failed"})

    def test_phase_failure_reports_class_without_exception_message(self):
        malicious = RuntimeError("token-secret https://user:pass@example.test/path")
        phase_error = smoke.SmokeError(
            f"{smoke.Phase.CANDIDATE_CREATE.value} failed ({type(malicious).__name__})"
        )
        summary = smoke.safe_summary(phase_error, ("token-secret", "pass"))
        self.assertEqual(
            summary,
            {
                "status": "FAIL",
                "error": "candidate_create failed (RuntimeError)",
            },
        )
        self.assertNotIn("token-secret", json.dumps(summary))
        self.assertNotIn("example.test", json.dumps(summary))

    def test_schema_failure_diagnostic_is_bounded_and_redacts_urls_and_secrets(self):
        class Log(BytesIO):
            def flush(self):
                pass

        log = Log(
            b"Prisma failed secret-value at postgresql://user:password@127.0.0.1/db\n"
        )
        log.seek(0, 2)
        tail = smoke._safe_log_tail(log, ("secret-value", "password"))
        self.assertIn("Prisma failed", tail)
        self.assertNotIn("secret-value", tail)
        self.assertNotIn("password", tail)
        self.assertNotIn("user", tail)

    def test_schema_failure_diagnostic_prefers_early_postgres_message(self):
        class Log(BytesIO):
            def flush(self):
                pass

        content = [b"error: unsupported startup parameter: schema\n"]
        content.extend(f"field{index}: undefined\n".encode() for index in range(40))
        log = Log(b"".join(content))
        log.seek(0, 2)
        tail = smoke._safe_log_tail(log, ())
        self.assertIn("unsupported startup parameter: schema", tail)
        self.assertLessEqual(len(tail), 2000)

    def test_real_exclusive_binary_log_is_readable_after_failed_owned_command(self):
        class Process:
            def wait(self, timeout):
                self.timeout = timeout
                return 1

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "owners.log"
            with path.open("x+b") as log:
                path.chmod(0o600)

                def failed_process(*_args, **_kwargs):
                    log.write(
                        b"schema error token-secret postgresql://user:pass@127.0.0.1/db\n"
                    )
                    return Process()

                with (
                    patch.object(smoke.subprocess, "Popen", failed_process),
                    patch.object(smoke, "_stop") as stop,
                    self.assertRaises(smoke.SmokeError) as raised,
                ):
                    smoke._run(
                        ["node", "schema"],
                        Path(directory),
                        {},
                        log,
                        "Storage schema installation",
                        ("token-secret", "pass"),
                    )
                message = str(raised.exception)
                self.assertIn("schema error", message)
                self.assertNotIn("token-secret", message)
                self.assertNotIn("user", message)
                self.assertNotIn("pass", message)
                stop.assert_called_once()
                self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)

    def test_schema_timeout_stops_the_owned_process_group(self):
        class Process:
            def wait(self, timeout):
                raise smoke.subprocess.TimeoutExpired("schema", timeout)

        process = Process()
        with (
            patch.object(smoke.subprocess, "Popen", return_value=process),
            patch.object(smoke, "_stop") as stop,
            self.assertRaisesRegex(smoke.SmokeError, "deadline exceeded"),
        ):
            smoke._run(["schema"], Path("/tmp"), {}, BytesIO(), "schema")
        stop.assert_called_once_with(process)

    def test_object_store_origins_are_strict_local_http(self):
        self.assertEqual(
            smoke.local_http_origin("http://127.0.0.1:9000/", "store"),
            "http://127.0.0.1:9000",
        )
        for value in (
            "https://127.0.0.1:9000",
            "http://example.test:9000",
            "http://127.0.0.1:3310",
            "http://127.0.0.1",
            "http://127.0.0.1:9000/path",
            "http://127.0.0.1:9000?query=1",
            "http://user@127.0.0.1:9000",
        ):
            with self.subTest(value=value), self.assertRaises(smoke.SmokeError):
                smoke.local_http_origin(value, "store")

    def test_sigterm_handler_raises_once_and_restores_previous_handler(self):
        previous = smoke.signal.getsignal(smoke.signal.SIGTERM)
        restore = smoke.install_sigterm_cleanup_handler()
        installed = smoke.signal.getsignal(smoke.signal.SIGTERM)
        try:
            with self.assertRaises(smoke.TerminationRequested):
                installed(smoke.signal.SIGTERM, None)
            self.assertEqual(
                smoke.signal.getsignal(smoke.signal.SIGTERM), smoke.signal.SIG_IGN
            )
        finally:
            restore()
        self.assertEqual(smoke.signal.getsignal(smoke.signal.SIGTERM), previous)

    def test_proxy_cleanup_failure_does_not_prevent_process_cleanup(self):
        events = []

        class Proxy:
            def close(self):
                events.append("proxy")
                raise RuntimeError("secret")

        class Process:
            name = "consumer"

        try:
            Proxy().close()
        except BaseException:
            events.append("recorded")
        failures = smoke.stop_owned_processes(
            [Process()],
            None,
            None,
            lambda process: (
                events.append(process.name) if process is not None else None
            ),
        )
        self.assertEqual(failures, [])
        self.assertEqual(events, ["proxy", "recorded", "consumer"])

    def test_skill_projection_requires_valid_nonempty_ids_and_stable_series(self):
        base = {
            "revision": 1,
            "status": "draft",
            "replayed": False,
            "series_id": "series_1",
            "state_version": "1",
        }
        for skill_id in ("", "bad/id", "x" * 192):
            with self.subTest(skill_id=skill_id), self.assertRaises(smoke.SmokeError):
                smoke._draft({"data": {**base, "skill_id": skill_id}}, 201)
        responses = [
            (201, {"data": {**base, "skill_id": "skill_1"}}),
            (
                201,
                {
                    "data": {
                        **base,
                        "skill_id": "skill_1",
                        "series_id": "series_2",
                        "replayed": True,
                        "state_version": "1",
                    }
                },
            ),
        ]
        with self.assertRaisesRegex(smoke.SmokeError, "replay drift"):
            smoke.exercise_http_contract(
                lambda **_kwargs: responses.pop(0),
                smoke.require_sandbox_ready(ready()),
            )


class AgentSourceOptInTests(unittest.TestCase):
    def test_unquiet_source_retains_owner_processes_database_and_bucket(self):
        from contextlib import ExitStack
        from dataclasses import replace
        from types import SimpleNamespace
        from unittest.mock import Mock
        from uuid import UUID

        storage_helper = SimpleNamespace(_s3=Mock(), preflight_bucket=Mock())
        oidc = SimpleNamespace(runtime=SimpleNamespace(free_port=Mock()))
        session = SimpleNamespace(node_environment=Mock(), ProtocolReader=Mock())

        resource_id = UUID("11111111-1111-1111-1111-111111111111")
        args = smoke.RunArguments(
            "postgresql://user@127.0.0.1/db",
            "redis://127.0.0.1/0",
            *(Path("/node") for _ in range(4)),
            "test-bucket",
            True,
            "redis://127.0.0.1/15",
        )
        env = {
            "KOKORO_OBJECT_STORE_ENDPOINT": "http://127.0.0.1:9000",
            "KOKORO_OBJECT_STORE_PUBLIC_ENDPOINT": "http://127.0.0.1:9000",
            "KOKORO_OBJECT_STORE_REGION": "us-east-1",
            "KOKORO_OBJECT_STORE_ACCESS_KEY_ID": "private-key",
            "KOKORO_OBJECT_STORE_SECRET_ACCESS_KEY": "private-secret",
            "KOKORO_OBJECT_STORE_PROFILE": "custom",
            "KOKORO_OBJECT_STORE_FORCE_PATH_STYLE": "true",
            "KOKORO_SCANNER_HOST": "127.0.0.1",
            "KOKORO_SCANNER_PORT": "3311",
        }
        current = replace(
            smoke.require_sandbox_ready(ready()),
            database_name="iam_web_oidc_" + resource_id.hex,
            redis_prefix=f"iam:test:web-oidc-flow-host:{resource_id}:",
        )
        for quiescent in (False, True):
            with (
                self.subTest(quiescent=quiescent),
                tempfile.TemporaryDirectory() as directory,
                ExitStack() as stack,
            ):
                stack.enter_context(
                    patch.dict(
                        sys.modules,
                        {
                            "run_agent_storage_artifact_smoke": storage_helper,
                            "run_web_bff_iam_oidc_smoke": oidc,
                            "run_bff_iam_session_smoke": session,
                        },
                    )
                )
                driver = SimpleNamespace(
                    secret="private-agent",
                    jwks_url="http://127.0.0.1:4400/v1/execution-proof/jwks",
                    start_http=Mock(),
                    dependencies_quiescent=quiescent,
                    close=Mock(
                        return_value=["Agent source executor thread drain timed out"]
                        if not quiescent
                        else ["Agent source runtime/Redis cleanup failed"]
                    ),
                )
                process = Mock(pid=43210)
                reader = Mock()

                def stub(target, name, **kwargs):
                    return stack.enter_context(patch.object(target, name, **kwargs))

                retained = []
                stack.enter_context(
                    patch.object(smoke, "_RETAINED_SOURCE_RESOURCES", retained)
                )
                stub(smoke.source_helper, "preflight")
                stub(smoke.source_helper, "AgentSourceDriver", return_value=driver)
                stub(smoke, "frozen_sources")
                stub(smoke, "uuid4", return_value=resource_id)
                stub(smoke.tempfile, "mkdtemp", return_value=directory)
                stub(smoke, "_database_exists", return_value=False)
                stub(smoke, "_redis_keys", return_value=set())
                stub(session, "node_environment", return_value={})
                stub(smoke.subprocess, "Popen", return_value=process)
                stub(session, "ProtocolReader", return_value=reader)
                stub(smoke, "require_sandbox_ready", return_value=current)
                stub(oidc.runtime, "free_port", return_value=4400)
                stub(storage_helper, "_s3", return_value=object())
                stub(
                    smoke,
                    "create_owned_bucket",
                    side_effect=lambda _s3, _bucket, _region, claim: claim(),
                )
                stub(
                    storage_helper,
                    "preflight_bucket",
                    side_effect=smoke.TerminationRequested(
                        "runner termination requested"
                    ),
                )
                stop = stub(smoke, "stop_owned_processes", return_value=[])
                delete = stub(smoke, "delete_owned_bucket")
                absent = stub(smoke, "require_bucket_absent")
                stub(smoke, "verify_cleanup", return_value=[])
                result = smoke.execute(args, env)
                self.assertEqual(result["status"], "FAIL")
                self.assertEqual(
                    result["agent_source_execution_error"],
                    "runner termination requested",
                )
                self.assertEqual(result["agent_source_evidence_directory"], directory)
                self.assertTrue(Path(directory).exists())
                if quiescent:
                    self.assertEqual(retained, [])
                    stop.assert_called_once()
                    delete.assert_called_once()
                    absent.assert_called_once()
                    reader.close.assert_called_once()
                    self.assertNotIn("agent_source_retained_process_ids", result)
                else:
                    self.assertIs(retained[0][0], driver)
                    self.assertEqual(retained[0][1], (process,))
                    self.assertIs(retained[0][2], reader)
                    stop.assert_not_called()
                    delete.assert_not_called()
                    absent.assert_not_called()
                    reader.close.assert_not_called()
                    self.assertEqual(
                        result["agent_source_retained_process_ids"], [43210]
                    )
                    self.assertEqual(
                        result["agent_source_dependencies"],
                        "retained: activity not quiescent",
                    )
                self.assertNotIn("private", json.dumps(result))

    def test_default_zip_unchanged_and_source_frontmatter_explicit(self):
        for enabled in (False, True):
            with zipfile.ZipFile(
                BytesIO(smoke.upload_zip_bytes("skill-one", 1, agent_source=enabled))
            ) as archive:
                content = archive.read("SKILL.md")
                self.assertEqual(
                    content,
                    smoke.source_helper.SKILL_BYTES
                    if enabled
                    else b"# Sandbox\n\nOwned signed PUT smoke.\n",
                )
                self.assertEqual(
                    json.loads(archive.read("manifest.json")),
                    {"schema_version": 2, "entry": "SKILL.md"},
                )
        for enabled in ("1", 1, None):
            with self.subTest(enabled=enabled), self.assertRaises(smoke.SmokeError):
                smoke.upload_zip_bytes("skill-one", 1, agent_source=enabled)

    def test_mode_preflight_before_frozen_sources_and_resources(self):
        args = smoke.RunArguments(
            "postgresql://user@127.0.0.1/db",
            "redis://127.0.0.1/0",
            *(Path("/node") for _ in range(4)),
            "test-bucket",
            True,
            "redis://127.0.0.1/15",
        )
        with (
            patch.object(
                smoke.source_helper,
                "preflight",
                side_effect=smoke.source_helper.SourceError("missing installation"),
            ),
            patch.object(smoke, "frozen_sources") as frozen,
            patch.object(smoke.tempfile, "mkdtemp") as directory,
        ):
            with self.assertRaises(smoke.source_helper.SourceError):
                smoke.execute(args, {})
            frozen.assert_not_called()
            directory.assert_not_called()

    def test_product_mode_is_explicit_and_disjoint_before_source_resources(self):
        self.assertIn("product_installation", smoke.RunArguments.__dataclass_fields__)
        args = smoke.RunArguments(
            "postgresql://user@127.0.0.1/db",
            "redis://127.0.0.1/0",
            *(Path("/node") for _ in range(4)),
            "test-bucket",
            agent_source=True,
            product_installation=True,
        )
        with (
            patch.object(smoke, "frozen_sources") as frozen,
            patch.object(smoke.tempfile, "mkdtemp") as directory,
        ):
            with self.assertRaisesRegex(smoke.product_helper.ProductError, "mode"):
                smoke.execute(args, {})
            frozen.assert_not_called()
            directory.assert_not_called()

    def test_personal_lifecycle_mode_requires_product_without_agent(self):
        from dataclasses import replace

        base = smoke.RunArguments(
            "postgresql://user@127.0.0.1/db",
            "redis://127.0.0.1/0",
            *(Path("/node") for _ in range(4)),
            "test-bucket",
        )
        smoke.platform_surfaces(
            replace(
                base,
                product_installation=True,
                personal_skill_lifecycle=True,
            )
        )
        for invalid in (
            replace(base, personal_skill_lifecycle=True),
            replace(
                base,
                agent_source=True,
                product_installation=True,
                personal_skill_lifecycle=True,
            ),
            replace(base, personal_skill_lifecycle=1),
        ):
            with (
                self.subTest(invalid=invalid),
                self.assertRaises(
                    (smoke.SmokeError, smoke.product_helper.ProductError)
                ),
            ):
                smoke.platform_surfaces(invalid)

    def test_lifecycle_success_error_and_replay_envelopes_are_closed(self):
        created = (
            201,
            {
                "data": {
                    "skill_id": "skill-two",
                    "series_id": "series-one",
                    "revision": "2",
                    "status": "draft",
                    "replayed": False,
                    "state_version": "1",
                },
                "meta": {"request_id": "request"},
            },
        )
        self.assertEqual(
            smoke.require_personal_skill_version(
                created,
                base_skill_id="skill-one",
                series_id="series-one",
                replayed=False,
            )["skill_id"],
            "skill-two",
        )
        withdrawn = (
            200,
            {
                "data": {
                    "source_ref": "skill:skill-one",
                    "status": "withdrawn",
                    "event_id": "evt:" + "a" * 64,
                    "replayed": True,
                    "state_version": "1",
                },
                "meta": {"request_id": "request"},
            },
        )
        smoke.require_personal_skill_withdraw(
            withdrawn, skill_id="skill-one", replayed=True
        )
        smoke.require_lifecycle_error(
            (
                409,
                {
                    "error": {
                        "code": "skill_idempotency_conflict",
                        "message": "closed",
                    },
                    "meta": {"request_id": "request"},
                },
            ),
            409,
            "skill_idempotency_conflict",
        )

    def test_product_mode_hooks_use_both_real_published_sources_and_existing_revoke(
        self,
    ):
        import ast

        tree = ast.parse(PATH.read_text())
        code = ast.unparse(tree)
        self.assertIn(
            "product_helper.preflight(args.product_installation, args.agent_source)",
            code,
        )
        self.assertIn("platform_surfaces(args)", code)
        self.assertIn(
            "product_installation.before_publish('skill:' + begin_skill_id)", code
        )
        self.assertIn(
            "product_installation.exercise(('skill:' + str(result['skill_id']), 'skill:' + begin_skill_id))",
            code,
        )
        self.assertIn(
            "product_installation.require_revoked('skill:' + begin_skill_id)", code
        )
        self.assertLess(
            code.index("product_installation.exercise("),
            code.index('iam.stdin.write(b\'{"command":"revoke-user-session"}\\n\')'),
        )
        self.assertIn("parser.add_mutually_exclusive_group()", code)
        self.assertIn("summary['product_execution_boundary']", code)

    def test_product_mode_selects_its_own_registered_rpc_surface_not_execution(self):
        from dataclasses import replace

        args = smoke.RunArguments(
            "postgresql://user@127.0.0.1/db",
            "redis://127.0.0.1/0",
            *(Path("/node") for _ in range(4)),
            "test-bucket",
        )
        self.assertEqual(smoke.platform_surfaces(args), "skill-catalog,skill-source")
        self.assertEqual(
            smoke.platform_surfaces(replace(args, agent_source=True)),
            "skill-catalog,skill-source,skill-installation",
        )
        self.assertEqual(
            smoke.platform_surfaces(replace(args, product_installation=True)),
            "skill-catalog,skill-source,skill-installation-product",
        )
        with self.assertRaises(smoke.product_helper.ProductError):
            smoke.platform_surfaces(
                replace(args, agent_source=True, product_installation=True)
            )

    def test_source_hooks_preserve_default_gate_and_cleanup_order(self):
        import ast

        tree = ast.parse(PATH.read_text())
        code = ast.unparse(tree)
        self.assertIn("iam_env['IAM_TEST_AGENT_SKILL_SOURCE_MODE'] = '0'", code)
        self.assertIn("iam_env.pop('IAM_TEST_AGENT_JWKS_URL', None)", code)
        self.assertIn("(2, 31, 2, 1)", code)
        execute = next(
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "execute"
        )
        body = ast.unparse(execute)
        source_branch = next(
            node
            for node in ast.walk(execute)
            if isinstance(node, ast.If)
            and ast.unparse(node.test) == "agent_source is not None"
            and "source_result = agent_source.exercise(" in ast.unparse(node)
        )
        source_body = ast.unparse(source_branch)
        wait_call = "source_helper.wait_for_iam_window(args.agent_source)"
        self.assertEqual(body.count(wait_call), 1)
        self.assertLess(
            source_body.index(wait_call),
            source_body.index("source_result = agent_source.exercise("),
        )
        self.assertLess(
            body.index("source_result = agent_source.exercise("),
            body.index("phase = Phase.REVOKE"),
        )
        self.assertLess(
            body.index("source_cleanup_failures = agent_source.close()"),
            body.index("process_failures = stop_owned_processes("),
        )
        self.assertIn(
            "require_sandbox_ready(reader.record(timeout=60), agent_source=args.agent_source)",
            body,
        )


if __name__ == "__main__":
    unittest.main()


# R356 formal source and HTTP wire regressions; no real resources are used here.
def formal_product():
    return {
        "publication_audience": "owner",
        "state_version": "7",
        "source_kind": "personal",
        "presentation_kind": "first_party",
        "creator_ref": {"kind": "user", "id": "user-one"},
        "publisher": {"kind": "iam", "iam": {"kind": "user", "id": "user-one"}},
        "creation_provenance": {"kind": "local"},
    }


def test_r356_formal_state_version_closed_and_signed_range():
    data = {
        "skill_id": "skill-one",
        "series_id": "series-one",
        "revision": 1,
        "status": "draft",
        "replayed": False,
        "state_version": "1",
    }
    assert smoke._draft({"data": data}, 201)[:3] == ("skill-one", "series-one", False)
    for bad in (None, "0", "01", "9223372036854775808", True, 1, "-1"):
        with unittest.TestCase().assertRaises(smoke.SmokeError):
            smoke._draft({"data": {**data, "state_version": bad}}, 201)
    with unittest.TestCase().assertRaises(smoke.SmokeError):
        smoke._draft(
            {"data": {k: v for k, v in data.items() if k != "state_version"}}, 201
        )


def test_r356_signed_put_returns_only_exact_opaque_ack_and_closes():
    sent, closed = [], []

    class Response:
        status = 200

        def getheaders(self):
            return [("x-amz-version-id", "opaque+/Version=7")]

        def read(self, _limit):
            return b""

    class Connection:
        def __init__(self, *_args, **_kwargs):
            pass

        def request(self, *args, **kwargs):
            sent.append((args, kwargs))

        def getresponse(self):
            return Response()

        def close(self):
            closed.append(True)

    reference = {
        "transfer_reference": {
            "url": "http://127.0.0.1:4400/key?sig=SECRET",
            "method": "PUT",
            "required_headers": {"content-type": "application/zip"},
        }
    }
    with patch.object(smoke.http.client, "HTTPConnection", Connection):
        assert smoke.signed_put(reference, b"zip") == "opaque+/Version=7"
    assert closed == [True]
    assert sent[0][1]["headers"] == {"content-type": "application/zip"}
    for headers in (
        [],
        [("etag", "hash")],
        [("x-amz-version-id", "null")],
        [("x-amz-version-id", " v")],
        [("x-amz-version-id", "v"), ("X-Amz-Version-Id", "v")],
    ):
        with (
            patch.object(smoke.http.client, "HTTPConnection", Connection),
            patch.object(Response, "getheaders", return_value=headers),
        ):
            with unittest.TestCase().assertRaises(smoke.SmokeError):
                smoke.signed_put(reference, b"zip")
    assert len(closed) == 6


def test_r356_owner_mapping_is_local_immutable_and_logical():
    selected = smoke.owner_sources(
        Path("/formal/bff-worktree"), Path("/formal/storage-worktree")
    )
    assert selected["bff"] == Path("/formal/bff-worktree")
    assert selected["storage"] == Path("/formal/storage-worktree")
    assert smoke.OWNERS["bff"] == smoke.ROOT / "apps/kokoro-bff"
    with unittest.TestCase().assertRaises(TypeError):
        selected["bff"] = Path("/bad")
    with unittest.TestCase().assertRaises(smoke.SmokeError):
        smoke.owner_sources(Path("relative"), None)


def test_r356_source_gate_checks_full_pin_root_logical_gitlink_and_common_git_dir():
    selected = {"bff": Path("/formal/not-the-submodule-basename")}
    calls = []

    def run(argv, **_kwargs):
        calls.append(argv)
        if "status" in argv:
            value = ""
        elif "ls-tree" in argv:
            value = f"160000 commit {smoke.FORMAL_PINS['bff']}\tapps/kokoro-bff\n"
        elif "--git-common-dir" in argv:
            value = "/root/modules/bff\n"
        else:
            value = smoke.FORMAL_PINS["bff"] + "\n"
        return type("Result", (), {"stdout": value})()

    assert smoke.frozen_sources(run, owners=selected) == {
        "bff": smoke.FORMAL_PINS["bff"]
    }
    assert any(x[-1] == "apps/kokoro-bff" for x in calls if "ls-tree" in x)
    assert len([x for x in calls if "--git-common-dir" in x]) == 2
    for failure in ("wrong_pin", "wrong_common", "wrong_root"):

        def invalid(argv, **kw):
            result = run(argv, **kw)
            if failure == "wrong_pin" and argv[-1] == "HEAD" and "rev-parse" in argv:
                result.stdout = "0" * 40
            if failure == "wrong_root" and "ls-tree" in argv:
                result.stdout = ""
            if (
                failure == "wrong_common"
                and "--git-common-dir" in argv
                and str(selected["bff"]) in argv
            ):
                result.stdout = "/unrelated/git"
            return result

        with unittest.TestCase().assertRaises(smoke.SmokeError):
            smoke.frozen_sources(invalid, owners=selected)


def test_r356_public_owner_and_iam_enriched_projection_are_distinct():
    data = {
        "skill_id": "skill-one",
        "source_ref": "skill:skill-one",
        "revision": "1",
        "status": "active",
        "name": "Sandbox",
        "summary": "",
        "tags": [],
        "example_prompts": [],
        "category_keys": [],
        "skill_updated_at": "2026-10-08T01:00:00.000Z",
        "product": formal_product(),
    }
    smoke.require_platform_published_skill_read(200, {"data": data}, "skill-one", "1")
    enriched = {
        **data,
        "publisher_profile": {
            "kind": "user",
            "id": "user-one",
            "status": "found",
            "display_name": "User",
            "image_url": None,
        },
    }
    smoke.require_public_published_skill_read(200, {"data": enriched}, "skill-one", "1")
    with unittest.TestCase().assertRaises(smoke.SmokeError):
        smoke.require_platform_published_skill_read(
            200, {"data": enriched}, "skill-one", "1"
        )
    for bad in ({"id": "other"}, {"status": "missing", "display_name": "Invented"}):
        with unittest.TestCase().assertRaises(smoke.SmokeError):
            smoke.require_public_published_skill_read(
                200,
                {
                    "data": {
                        **enriched,
                        "publisher_profile": {**enriched["publisher_profile"], **bad},
                    }
                },
                "skill-one",
                "1",
            )


def test_r356_owned_queries_preserve_full_pages_and_literal_cursor_filters():
    from urllib.parse import parse_qs, urlsplit

    rows = []
    for index in ("one", "two"):
        rows.append(
            {
                "skill_id": "skill-" + index,
                "source_ref": "skill:skill-" + index,
                "series_id": "series-" + index,
                "revision": "1",
                "name": "Sandbox " + index,
                "summary": "",
                "tags": [],
                "status": "active",
                "example_prompts": [],
                "category_keys": [],
                "skill_updated_at": "2026-10-08T01:00:00.000Z",
                "product": formal_product(),
                "publisher_profile": {
                    "kind": "user",
                    "id": "user-one",
                    "status": "missing",
                },
            }
        )
    calls = []

    def request(path):
        calls.append(path)
        q = parse_qs(urlsplit(path).query, keep_blank_values=True)
        text = q.get("query", ["sandbox"])[0].strip()
        source = q.get("source_kind", ["personal"])[0]
        if (
            any(len(v) != 1 for v in q.values())
            or source not in {"personal", "official", "third_party"}
            or not text
            or len(text) > 1024
            or ("cursor" in q and (text != "sandbox" or source != "personal"))
        ):
            return 400, {
                "error": {"code": "invalid_skill_request", "message": "Invalid"},
                "meta": {"request_id": "owned"},
            }
        current = rows if source == "personal" and text.casefold() == "sandbox" else []
        cursor = None
        if current and q.get("limit") == ["1"]:
            if "cursor" in q:
                current = [rows[1]]
            else:
                current = [rows[0]]
                cursor = "page_2"
        return 200, {
            "data": {"skills": current, "next_cursor": cursor},
            "meta": {"request_id": "owned"},
        }

    assert (
        smoke.exercise_owned_queries(request, ("skill:skill-one", "skill:skill-two"))
        is True
    )
    assert any("query=%25_%5C" in x for x in calls)
    assert any("cursor=page_2" in x and "query=changed" in x for x in calls)
    bad = {
        **rows[0],
        "publisher_profile": {"kind": "user", "id": "other", "status": "missing"},
    }
    with unittest.TestCase().assertRaises(smoke.SmokeError):
        smoke.require_managed_page(
            (
                200,
                {
                    "data": {"skills": [bad], "next_cursor": None},
                    "meta": {"request_id": "owned"},
                },
            )
        )


def test_r356_storage_schema_fixture_uses_only_mapped_formal_source():
    with tempfile.TemporaryDirectory() as directory:
        base = Path(directory)
        source = base / "formal-storage"
        output = base / "owned"
        (source / "scripts").mkdir(parents=True)
        (source / "prisma").mkdir()
        output.mkdir()
        for path in (
            "package.json",
            "prisma.config.ts",
            "prisma/schema.prisma",
            "scripts/apply-schema.ts",
        ):
            (source / path).write_text("FORMAL:" + path)
        fixture = smoke.storage_schema_fixture(output, source)
        assert (
            fixture / "prisma/schema.prisma"
        ).read_text() == "FORMAL:prisma/schema.prisma"
        assert (fixture / "node_modules").readlink() == source / "node_modules"


def test_r356_actual_execute_wiring_all_put_acks_and_local_owner_paths():
    import ast

    module = ast.parse(PATH.read_text())
    execute = next(
        n for n in module.body if isinstance(n, ast.FunctionDef) and n.name == "execute"
    )
    text = ast.unparse(execute)
    assert "OWNERS[" not in text and "KOKORO_SKILL_DRAFT_CANDIDATE_ENABLED" not in text
    assert "storage_schema_fixture(directory, owners['storage'])" in text
    assert "frozen_sources(owners=owners)" in text
    assert "'KOKORO_STORAGE_RPC_BASE_URL': storage_base" in text
    assert "'KOKORO_BFF_STORAGE_SECRET': storage_secret" in text
    for name in ("replacement", "infected", "recovered", "bad_begin", "zip_recovered"):
        assert name + "_version = signed_put(" + name in text
        assert "'source_version_id': " + name + "_version" in text
    assert "exercise_owned_queries(" in text


def test_r356_state_version_is_consumed_in_cas_not_only_displayed():
    import ast

    tree = ast.parse(PATH.read_text())
    execute = next(
        n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "execute"
    )
    code = ast.unparse(execute)
    for binding in (
        "'expected_state_version': begin_state_version",
        "'expected_state_version': replacement['state_version']",
        "'expected_state_version': infected['state_version']",
        "'expected_state_version': recovered['state_version']",
        "'expected_state_version': bad_begin['state_version']",
        "'expected_state_version': zip_recovered['state_version']",
    ):
        assert binding in code


def test_r356_default_owner_locations_are_immutable():
    with unittest.TestCase().assertRaises(TypeError):
        smoke.OWNERS["bff"] = Path("/unapproved")


def test_r356_cli_requires_both_explicit_absolute_source_options():
    import ast
    import inspect

    tree = ast.parse(inspect.getsource(smoke.main))
    required = {
        n.args[0].value: any(
            keyword.arg == "required"
            and isinstance(keyword.value, ast.Constant)
            and keyword.value.value is True
            for keyword in n.keywords
        )
        for n in ast.walk(tree)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
        and n.func.attr == "add_argument"
        and n.args
        and isinstance(n.args[0], ast.Constant)
    }
    assert required["--bff-source"] and required["--storage-source"]


def test_r356_formal_901_pin():
    assert smoke.FORMAL_PINS["bff"] == "46ed4ef9ab29714da63cb43596c0062560671ba0"
    assert smoke.FORMAL_PINS["platform"] == "43005cca5f8a09f4646de87a790b26c0685d7927"
    assert smoke.FORMAL_PINS["storage"] == "a1206d0194c1b1e405834f4c4548168fddbb5d52"
    assert smoke.FORMAL_PINS["iam"] == "61ccdbb059f8eb3ff62fb27f6cc56f11999aaa9a"


def test_r356_formal_901_optional_get_locator_identity():
    functions = [
        (
            smoke.require_public_package_get,
            ("skill-current",),
            {"phase": "none", "attempt_epoch": "0"},
        ),
        (
            smoke.require_public_package_pending,
            ("skill-current", "attempt-two", "upload-two", "2"),
            {
                "phase": "upload_pending",
                "attempt_epoch": "2",
                "attempt_id": "attempt-two",
                "upload_id": "upload-two",
            },
        ),
        (
            smoke.require_public_package_uploaded,
            ("skill-current", "attempt-two", "upload-two", "2"),
            {
                "phase": "uploaded",
                "attempt_epoch": "2",
                "attempt_id": "attempt-two",
                "upload_id": "upload-two",
            },
        ),
        (
            smoke.require_public_package_validated,
            ("skill-current", "attempt-two", "upload-two", "2"),
            {
                "phase": "validated",
                "attempt_epoch": "2",
                "attempt_id": "attempt-two",
                "upload_id": "upload-two",
            },
        ),
        (
            smoke.require_public_package_aborted,
            ("skill-current", "attempt-two", "upload-two", "2"),
            {
                "phase": "aborted",
                "attempt_epoch": "2",
                "attempt_id": "attempt-two",
                "upload_id": "upload-two",
            },
        ),
    ]
    for function, args, state in functions:
        data = {"skill_id": "skill-current", "state_version": "1", **state}
        function(200, {"data": data}, *args)
        for locator in ("opaque+/=", "Null", "x" * 1024):
            function(200, {"data": {**data, "source_version_id": locator}}, *args)
        for invalid in (None, "", "null", "x y", "é", "x" * 1025, [], 1):
            with unittest.TestCase().assertRaises(smoke.SmokeError):
                function(200, {"data": {**data, "source_version_id": invalid}}, *args)
        for leak in ("asset_id", "transfer_reference"):
            with unittest.TestCase().assertRaises(smoke.SmokeError):
                function(200, {"data": {**data, leak: "private"}}, *args)
        function(
            200,
            {"data": {**data, "source_version_id": "opaque+/="}},
            *args,
            expected_source_version="opaque+/=",
        )
        with unittest.TestCase().assertRaises(smoke.SmokeError):
            function(
                200,
                {"data": {**data, "source_version_id": "other-version"}},
                *args,
                expected_source_version="opaque+/=",
            )
        # The contract does not invent phase-dependent mandatory locator presence.
        function(200, {"data": data}, *args, expected_source_version="opaque+/=")
