"""Focused guards for the real IAM/BFF composition runner."""

import importlib.util
import os
from pathlib import Path
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
    def test_explicit_inputs_required(self):
        with self.assertRaises(SystemExit):
            smoke.parse_args([])

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

    def test_owned_cleanup_stops_all_before_database_cleanup(self):
        events = []
        class Process:
            pid = 1
        smoke.cleanup_owned([Process(), Process()], lambda _: events.append("stop"), lambda: events.append("database"))
        self.assertEqual(events, ["stop", "stop", "database"])

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

    def test_finalization_checks_inventory_even_if_cleanup_fails(self):
        events = []
        class Process:
            pid = 1
        def stop(_):
            events.append("stop")
            raise RuntimeError("stop")
        def cleanup():
            events.append("database")
            raise RuntimeError("database")
        def verify():
            events.append("verify")
        def inventory():
            events.append("inventory")
            return ({"unchanged"}, set())
        with self.assertRaises(smoke.SmokeError):
            smoke.finalize_owned([Process(), Process()], stop, cleanup, verify, inventory, ({"unchanged"}, set()))
        self.assertEqual(events, ["stop", "stop", "database", "verify", "inventory"])

    def test_envelope_codes_are_checked(self):
        smoke.require_success(200, {"data": {"projects": []}, "meta": {"request_id": "r"}}, "list")
        smoke.require_error(401, {"error": {"code": "session_invalid", "message": "expired"}, "meta": {"request_id": "r"}}, 401, "session_invalid", "expired")
        with self.assertRaises(smoke.SmokeError):
            smoke.require_error(401, {"error": {"code": "wrong", "message": "expired"}, "meta": {"request_id": "r"}}, 401, "session_invalid", "expired")


if __name__ == "__main__":
    unittest.main()
