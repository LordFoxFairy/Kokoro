"""Returned ingress configuration boundary; no owner services or private env are read."""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "e2e/run_platform_local_skill_import_storage_smoke.py"
)
spec = importlib.util.spec_from_file_location("platform_local_import_smoke", SCRIPT)
smoke = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smoke)


class IngressConfigurationTests(unittest.TestCase):
    def prepare(self, runtime):
        result = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=json.dumps({"tenantId": "tenant-one", "runtime": runtime}),
            stderr="",
        )
        with patch.object(smoke.subprocess, "run", return_value=result):
            return smoke.prepare_ingress(
                Path("/fixture/bff"), "/fixture/node", Path("/fixture/run"), issue=False
            )

    def runtime(self):
        return {
            "KOKORO_IAM_BASE_URL": "http://127.0.0.1:4401",
            "KOKORO_REDIS_URL": "redis://127.0.0.1:6379/0",
            "KOKORO_PLATFORM_IAM_EXECUTION_SERVICE_CREDENTIAL_FILE": "/fixture/tenant-execution.json",
            "KOKORO_PLATFORM_SERVICE_CREDENTIALS_FILE": "/fixture/run/platform-service-credentials.json",
        }

    def test_accepts_exact_native_runtime_and_run_owned_receiver(self):
        runtime = self.runtime()
        self.assertEqual(
            self.prepare(runtime),
            {**runtime, "KOKORO_SMOKE_TRUSTED_TENANT_ID": "tenant-one"},
        )

    def test_rejects_unknown_or_retired_configuration_keys(self):
        for key in (
            "UNKNOWN_RUNTIME_KEY",
            "KOKORO_PLATFORM_IAM_RESOURCE_SERVER_CREDENTIAL_FILE",
            "KOKORO_PLATFORM_IAM_TENANT_CREDENTIALS_FILE",
        ):
            with self.subTest(key=key), self.assertRaises(smoke.QualificationError):
                self.prepare({**self.runtime(), key: "/fixture/obsolete.json"})

    def test_rejects_external_receiver_file_even_if_returned_by_preflight(self):
        with self.assertRaises(smoke.QualificationError):
            self.prepare(
                {
                    **self.runtime(),
                    "KOKORO_PLATFORM_SERVICE_CREDENTIALS_FILE": "/fixture/shared/receiver.json",
                }
            )

    def test_ingress_uses_explicit_owner_env_paths_for_dry_run_and_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            config = root / "storage.json"
            config.write_text(
                json.dumps(
                    {
                        "storage": dict.fromkeys(
                            (
                                "KOKORO_POSTGRES_URL",
                                "KOKORO_REDIS_URL",
                                "KOKORO_OBJECT_STORE_REGION",
                                "KOKORO_OBJECT_STORE_ENDPOINT",
                                "KOKORO_OBJECT_STORE_PUBLIC_ENDPOINT",
                                "KOKORO_OBJECT_STORE_ACCESS_KEY_ID",
                                "KOKORO_OBJECT_STORE_SECRET_ACCESS_KEY",
                                "KOKORO_SCANNER_HOST",
                                "KOKORO_SCANNER_PORT",
                            ),
                            "fixture",
                        )
                    }
                )
            )
            bff_env = root / "bff.env"
            platform_env = root / "platform.env"
            argv = [
                str(SCRIPT),
                "--node",
                "/fixture/node",
                "--platform",
                str(root),
                "--storage",
                str(root),
                "--bff",
                str(root),
                "--runtime-config",
                str(config),
                "--case",
                smoke.INGRESS_CASE,
                "--bff-env",
                str(bff_env),
                "--platform-env",
                str(platform_env),
            ]
            for dry in (False, True):
                with (
                    self.subTest(dry=dry),
                    patch.object(sys, "argv", [*argv, *(["--dry-run"] if dry else [])]),
                    patch.object(smoke, "node24"),
                    patch.object(smoke, "harness_source"),
                    patch.object(smoke, "validate_harness_syntax"),
                    patch.object(smoke, "validate_harness_load"),
                    patch.object(smoke, "prepare_ingress") as prepare,
                    patch.object(smoke, "run_case") as run_case,
                    patch("builtins.print"),
                ):
                    self.assertEqual(smoke.main(), 0)
                    selected, other = (
                        (prepare, run_case) if dry else (run_case, prepare)
                    )
                    selected.assert_called_once()
                    other.assert_not_called()
                    self.assertEqual(selected.call_args.kwargs["bff_env"], bff_env)
                    self.assertEqual(
                        selected.call_args.kwargs["platform_env"], platform_env
                    )

    def test_removes_native_material_if_preparation_fails_before_storage_starts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "evidence"
            evidence.mkdir()
            scratch = root / "credentials"
            scratch.mkdir(mode=0o700)

            def prepare(_bff, _node, directory, *, issue, bff_env, platform_env):
                self.assertEqual(bff_env, smoke.DEFAULT_BFF_ENV)
                self.assertEqual(platform_env, smoke.DEFAULT_PLATFORM_ENV)
                self.assertEqual(directory, scratch)
                self.assertTrue(issue)
                (directory / "receiver.json").write_text("test-only-secret")
                raise smoke.QualificationError("fixture failure")

            with (
                patch.object(smoke.tempfile, "mkdtemp", return_value=str(evidence)),
                patch.object(smoke.tempfile, "TemporaryDirectory") as material,
                patch.object(smoke, "harness_source", return_value="fixture"),
                patch.object(
                    smoke, "case_environment", return_value=({}, "storage-fixture")
                ),
                patch.object(smoke, "prepare_ingress", side_effect=prepare),
                patch.object(smoke.subprocess, "Popen") as start,
                patch("builtins.print"),
                self.assertRaisesRegex(smoke.QualificationError, "fixture failure"),
            ):
                material.return_value.name = str(scratch)
                material.return_value.cleanup.side_effect = lambda: smoke.shutil.rmtree(
                    scratch
                )
                smoke.run_case(root, root, "/fixture/node", {}, smoke.INGRESS_CASE)

            start.assert_not_called()
            material.return_value.cleanup.assert_called_once_with()
            self.assertFalse(scratch.exists())
            self.assertTrue(evidence.is_dir())
