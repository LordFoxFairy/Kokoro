"""Returned ingress configuration boundary; no owner services or private env are read."""

import importlib.util
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "e2e/run_platform_local_skill_import_storage_smoke.py"
spec = importlib.util.spec_from_file_location("platform_local_import_smoke", SCRIPT)
smoke = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smoke)


class IngressConfigurationTests(unittest.TestCase):
    def prepare(self, runtime):
        result = subprocess.CompletedProcess(
            args=[], returncode=0,
            stdout=json.dumps({"tenantId": "tenant-one", "runtime": runtime}), stderr="",
        )
        with patch.object(smoke.subprocess, "run", return_value=result):
            return smoke.prepare_ingress(
                Path("/fixture/bff"), "/fixture/node", Path("/fixture/run"), issue=False
            )

    def runtime(self):
        return {
            "KOKORO_IAM_BASE_URL": "http://127.0.0.1:4401",
            "KOKORO_REDIS_URL": "redis://127.0.0.1:6379/0",
            "KOKORO_PLATFORM_IAM_TENANT_CREDENTIALS_FILE": "/fixture/tenant-execution.json",
        }

    def test_accepts_current_configuration_without_retired_resource_server_key(self):
        runtime = self.runtime()
        self.assertEqual(
            self.prepare(runtime),
            {**runtime, "KOKORO_SMOKE_TRUSTED_TENANT_ID": "tenant-one"},
        )

    def test_rejects_unknown_or_retired_configuration_keys(self):
        for key in (
            "UNKNOWN_RUNTIME_KEY",
            "KOKORO_PLATFORM_IAM_RESOURCE_SERVER_CREDENTIAL_FILE",
        ):
            with self.subTest(key=key), self.assertRaises(smoke.QualificationError):
                self.prepare({**self.runtime(), key: "/fixture/obsolete.json"})
