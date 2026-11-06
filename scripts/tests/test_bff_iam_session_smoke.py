"""Focused guards for shared IAM/BFF smoke helpers and the retired CLI."""

import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import time
import unittest


PATH = Path(__file__).resolve().parents[1] / "e2e" / "run_bff_iam_session_smoke.py"
sys.path.insert(0, str(PATH.parent))
spec = importlib.util.spec_from_file_location("bff_iam_session_smoke", PATH)
smoke = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = smoke
spec.loader.exec_module(smoke)


class RunnerGuards(unittest.TestCase):
    def test_retired_cli_help_exits_nonzero_and_names_native_runner(self):
        result = subprocess.run(
            [sys.executable, str(PATH), "--help"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertIn("scripts/e2e/run_web_native_session_smoke.py", result.stderr)

    def test_ready_record_requires_local_origin_and_identity(self):
        good = {"kind": "ready", "base_url": "http://127.0.0.1:4321", "access_token": "secret", "tenant_id": "t", "user_id": "u"}
        self.assertEqual(smoke.validate_ready(good).tenant_id, "t")
        for patch in ({"access_token": ""}, {"base_url": "https://elsewhere.test"}, {"kind": "result"}, {"extra": "x"}):
            with self.subTest(patch=patch), self.assertRaises(smoke.SmokeError):
                smoke.validate_ready({**good, **patch})

    def test_command_result_must_match(self):
        smoke.validate_result({"kind": "result", "command": "signout", "status": "ok"}, "signout")
        for bad in ({"kind": "result", "command": "reset", "status": "ok"}, {"kind": "result", "command": "signout", "status": "failed"}):
            with self.assertRaises(smoke.SmokeError):
                smoke.validate_result(bad, "signout")

    def test_partial_protocol_line_obeys_absolute_deadline(self):
        read_fd, write_fd = os.pipe()
        reader = smoke.ProtocolReader(read_fd)
        cleanup = []
        try:
            os.write(write_fd, b'{"kind":"ready"')
            started = time.monotonic()
            with self.assertRaises(smoke.SmokeError):
                try:
                    reader.record(timeout=0.1)
                finally:
                    cleanup.append("reached")
            self.assertLess(time.monotonic() - started, 0.5)
            self.assertEqual(cleanup, ["reached"])
        finally:
            reader.close()
            os.close(read_fd)
            os.close(write_fd)

    def test_consecutive_protocol_records_are_retained(self):
        read_fd, write_fd = os.pipe()
        reader = smoke.ProtocolReader(read_fd)
        try:
            os.write(write_fd, b'{"kind":"result"}\n{"kind":"ready"}\n')
            self.assertEqual(reader.record(timeout=0.1)["kind"], "result")
            self.assertEqual(reader.record(timeout=0.1)["kind"], "ready")
        finally:
            reader.close()
            os.close(read_fd)
            os.close(write_fd)

    def test_envelope_codes_are_checked(self):
        smoke.require_success(200, {"data": {"projects": []}, "meta": {"request_id": "r"}}, "list")
        smoke.require_error(401, {"error": {"code": "session_invalid", "message": "expired"}, "meta": {"request_id": "r"}}, 401, "session_invalid", "expired")
        with self.assertRaises(smoke.SmokeError):
            smoke.require_error(401, {"error": {"code": "wrong", "message": "expired"}, "meta": {"request_id": "r"}}, 401, "session_invalid", "expired")


if __name__ == "__main__":
    unittest.main()
