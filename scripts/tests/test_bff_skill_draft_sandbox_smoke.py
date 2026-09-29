"""Protocol and isolation guards for the Skill draft composition runner."""

import importlib.util
import json
from io import StringIO
from io import BytesIO
from pathlib import Path
import stat
import sys
import tempfile
import unittest
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
    def test_success_summary_requires_complete_receipt_inventory(self):
        self.assertEqual(
            smoke.safe_summary(None),
            {
                "status": "PASS",
                "resources": "clean",
                "platform_skill_count": 1,
                "platform_receipt_count": 16,
                "platform_publish_event_count": 1,
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
            },
        )

    def test_public_get_requires_exact_current_none_state(self):
        expected = {
            "data": {"skill_id": "skill-current", "attempt_epoch": "0", "phase": "none"}
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
        self.assertEqual(len(value.secrets), 6)
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
        resource, execution, catalog = smoke.platform_credential_payloads(parsed)
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
            execution[0]["resource"], "https://kokoro.dev/resources/iam-internal"
        )
        self.assertEqual(execution[0]["scope"], "iam:execution-authorization.verify")
        self.assertEqual(execution[0]["clientId"], "execution")
        self.assertEqual(execution[0]["clientSecret"], "execution-secret")

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

    def test_disabled_and_enabled_bff_differ_only_by_activation_flag(self):
        base = {
            "KOKORO_PLATFORM_BASE_URL": "http://127.0.0.1:4400",
            "KOKORO_BFF_PLATFORM_CATALOG_CREDENTIALS_FILE": "/owned/catalog.json",
            "KOKORO_SKILL_DRAFT_CANDIDATE_ENABLED": "false",
        }
        active = {**base, "KOKORO_SKILL_DRAFT_CANDIDATE_ENABLED": "true"}
        self.assertEqual(
            {
                key: value
                for key, value in base.items()
                if key != "KOKORO_SKILL_DRAFT_CANDIDATE_ENABLED"
            },
            {
                key: value
                for key, value in active.items()
                if key != "KOKORO_SKILL_DRAFT_CANDIDATE_ENABLED"
            },
        )
        self.assertNotIn("KOKORO_PLATFORM_CATALOG_CREDENTIAL_FILE", active)

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
            client.sendall(client.recv(16))
            client.close()

        worker = threading.Thread(target=echo)
        worker.start()
        proxy = smoke.CountingTcpProxy(port)
        client = socket.create_connection(("127.0.0.1", proxy.port))
        client.sendall(b"ok")
        self.assertEqual(client.recv(2), b"ok")
        client.close()
        worker.join()
        server.close()
        proxy.close()
        self.assertEqual(proxy.count, 1)

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
                    }
                },
            ),
        ]
        with self.assertRaisesRegex(smoke.SmokeError, "replay drift"):
            smoke.exercise_http_contract(
                lambda **_kwargs: responses.pop(0),
                smoke.require_sandbox_ready(ready()),
            )


if __name__ == "__main__":
    unittest.main()
