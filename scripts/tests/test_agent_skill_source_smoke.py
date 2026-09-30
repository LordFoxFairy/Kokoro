"""Source driver boundaries run without Agent packages or shared services."""

import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

PATH = Path(__file__).resolve().parents[1] / "e2e/agent_skill_source_smoke.py"
spec = importlib.util.spec_from_file_location("agent_source_driver", PATH)
source = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = source
spec.loader.exec_module(source)


class SourceBoundaries(unittest.TestCase):
    def test_iam_window_wait_is_source_only_and_precedes_business(self):
        import threading

        events = []

        def wait(seconds):
            self.assertIs(threading.current_thread(), threading.main_thread())
            events.append(("wait", seconds))

        source.wait_for_iam_window(False, wait=wait)
        self.assertEqual(events, [])
        source.wait_for_iam_window(True, wait=wait)
        events.append("business")
        self.assertEqual(events, [("wait", 60), "business"])
        for invalid in (1, "true", None):
            with self.subTest(invalid=invalid), self.assertRaises(source.SourceError):
                source.wait_for_iam_window(invalid, wait=wait)
        self.assertEqual(events, [("wait", 60), "business"])

    def test_sigterm_during_iam_window_never_starts_run_and_closes_resources(self):
        import asyncio
        import os
        import signal
        import tempfile

        class Interrupted(RuntimeError):
            pass

        def terminate(_signum, _frame):
            raise Interrupted("termination requested")

        def wait(seconds):
            self.assertEqual(seconds, 60)
            os.kill(os.getpid(), signal.SIGTERM)

        with tempfile.TemporaryDirectory() as directory:
            driver = source.AgentSourceDriver(
                Path(directory), "db", "redis://localhost/15", "window"
            )
            driver.runner = asyncio.Runner()
            secret = Path(directory) / "owned-secret"
            secret.write_text("private")
            driver._files.append(secret)
            previous = signal.signal(signal.SIGTERM, terminate)
            try:
                with patch.object(driver, "exercise") as business:
                    with self.assertRaises(Interrupted):
                        try:
                            source.wait_for_iam_window(True, wait=wait)
                            business(None, "", "", "", 1, b"", lambda: None)
                        finally:
                            failures = driver.close()
                    business.assert_not_called()
                self.assertEqual(failures, [])
                self.assertIsNone(driver._exercise_task)
                self.assertEqual(driver._blocking_futures, {})
                self.assertTrue(driver.dependencies_quiescent)
                self.assertFalse(secret.exists())
            finally:
                signal.signal(signal.SIGTERM, previous)
                driver.runner.close()

    def test_setup_failure_category_is_exact_allowlist_without_raw_messages(self):
        cases = {
            "IAM Platform introspection failed": "iam_ingress",
            "IAM outbound credential is unavailable": "iam_outbound_token",
            "IAM execution authorization failed": "iam_execution",
            "IAM execution authorization identity mismatch": "iam_identity",
            "transaction admission is unavailable": "transaction_admission",
            "skill installation receipt claim outcome is unknown": "receipt_claim_unknown",
            "skill installation command outcome is unknown": "command_outcome_unknown",
            "Capability runtime dependency is unavailable": "runtime_dependency",
        }
        for message, label in cases.items():
            with self.subTest(label=label):
                self.assertEqual(source.setup_failure_category(message), label)
                self.assertEqual(
                    source.setup_failure_category(message + " PRIVATE_SENTINEL"),
                    "unclassified",
                )
        for unknown in ("PRIVATE_SENTINEL", "", None, {}, ["SECRET"]):
            with self.subTest(kind=type(unknown).__name__):
                self.assertEqual(source.setup_failure_category(unknown), "unclassified")

    def test_import_does_not_load_agent(self):
        self.assertNotIn("kokoro_agent.worker.platform", sys.modules)

    def test_default_mode_is_explicit_and_dependency_free(self):
        with patch.object(source, "require_agent_environment") as check:
            source.preflight(False, None, "redis://127.0.0.1:6379/0")
            check.assert_not_called()
        for mode in ("1", 1, None):
            with self.subTest(mode=mode), self.assertRaises(source.SourceError):
                source.preflight(mode, None, "redis://127.0.0.1:6379/0")
        with self.assertRaises(source.SourceError):
            source.preflight(
                False, "redis://127.0.0.1:6379/15", "redis://127.0.0.1:6379/0"
            )

    def test_source_requires_same_instance_distinct_explicit_database(self):
        with patch.object(source, "require_agent_environment") as check:
            for url in (
                None,
                "redis://127.0.0.1:6379/0",
                "redis://127.0.0.1:6379/",
                "redis://127.0.0.1:3310/15",
                "redis://127.0.0.1:6380/15",
                "redis://remote/15",
                "redis://127.0.0.1:6379/16",
            ):
                with self.subTest(url=url), self.assertRaises(source.SourceError):
                    source.preflight(True, url, "redis://127.0.0.1:6379/0")
            source.preflight(
                True, "redis://127.0.0.1:6379/15", "redis://127.0.0.1:6379/0"
            )
            check.assert_called_once()

    def test_owner_install_command_vector(self):
        document = source.command_document(
            "tenant-1",
            "InstallSkill",
            {
                "source_ref": {"present": True, "value": "skill:skill-1"},
                "target_owner_scope": {
                    "present": True,
                    "value": {"kind": "user", "id": "user-1"},
                },
            },
        )
        self.assertEqual(
            source.command_digest(document),
            "c6f34828b59ee4bf90039884da0ac16bd47d227708b9310e7881e4af5e906199",
        )
        self.assertNotIn("request_id", document)
        with self.assertRaises(source.SourceError):
            source.command_document("tenant-1", "Unknown", {})

    def test_revoke_exact_protocol(self):
        record = {"kind": "result", "command": "revoke-agent-execution", "status": "ok"}
        source.require_revoke_result(record)
        for invalid in (
            {**record, "extra": True},
            {**record, "command": "revoke-user-session"},
            {**record, "status": "failed"},
            None,
        ):
            with self.subTest(record=invalid), self.assertRaises(source.SourceError):
                source.require_revoke_result(invalid)

    def test_inventory_keeps_old_gate_and_exact_new_receipts(self):
        source.require_inventory((2, 31, 2, 1), (2, 34, 2, 1))
        for before, after in (
            ((2, 32, 2, 1), (2, 35, 2, 1)),
            ((2, 31, 2, 1), (2, 35, 2, 1)),
            ((2, 31, 2, 1), (3, 34, 2, 1)),
        ):
            with self.subTest(after=after), self.assertRaises(source.SourceError):
                source.require_inventory(before, after)

    def test_agent_database_url_has_no_prisma_schema_argument(self):
        self.assertEqual(
            source.database_url(
                "postgresql://a:b@127.0.0.1:5432/postgres?sslmode=disable",
                "iam_web_oidc_abc",
            ),
            "postgresql://a:b@127.0.0.1:5432/iam_web_oidc_abc?sslmode=disable",
        )
        with self.assertRaises(source.SourceError):
            source.database_url(
                "postgresql://a:b@127.0.0.1:5432/postgres?schema=public",
                "iam_web_oidc_abc",
            )

    def test_cleanup_attempts_all_steps_and_reports_each_failure(self):
        calls = []

        def fail():
            calls.append("http")
            raise RuntimeError("private data")

        failures = source.close_steps(
            [("http", fail), ("runtime", lambda: calls.append("runtime"))]
        )
        self.assertEqual(calls, ["http", "runtime"])
        self.assertEqual(failures, ["Agent source http cleanup failed"])
        self.assertNotIn("private", json.dumps(failures))


class SourceSignalTests(unittest.TestCase):
    def test_sigterm_during_executor_submission_registers_started_thread(self):
        import asyncio
        import os
        import signal
        import threading

        for label in ("launch", "revoke"):
            with self.subTest(label=label):
                driver = source.AgentSourceDriver(
                    Path("/tmp"), "db", "redis://localhost/15", "registration"
                )
                driver.runner = asyncio.Runner()
                loop = driver.runner.get_loop()
                submit = loop.run_in_executor
                started, release = threading.Event(), threading.Event()
                events, registered_at_signal = [], []

                class Interrupted(RuntimeError):
                    pass

                def terminate(signum, _frame):
                    self.assertEqual(signum, signal.SIGTERM)
                    registered_at_signal.append(len(driver._blocking_futures))
                    raise Interrupted("termination requested")

                def blocking():
                    events.append("thread-start")
                    started.set()
                    if not release.wait(2):
                        raise AssertionError("test release missing")
                    events.append("thread-end")

                def interrupted_submit(*args):
                    future = submit(*args)
                    self.assertTrue(started.wait(1))
                    # Deterministic injection after actual thread start but before
                    # run_in_executor returns its Future to the driver.
                    os.kill(os.getpid(), signal.SIGTERM)
                    return future

                async def business(*_args):
                    await driver._blocking_call(label, blocking)
                    events.append("business-after-signal")

                async def close_resources():
                    events.append("resource-close")

                previous = signal.signal(signal.SIGTERM, terminate)
                try:
                    with (
                        patch.object(loop, "run_in_executor", interrupted_submit),
                        patch.object(driver, "_exercise", business),
                    ):
                        with self.assertRaises((Interrupted, source.SourceError)):
                            driver.exercise(None, "", "", "", 1, b"", lambda: None)
                    self.assertEqual(registered_at_signal, [1])
                    self.assertEqual(len(driver._blocking_futures), 1)
                    self.assertIs(signal.getsignal(signal.SIGTERM), terminate)
                    loop.call_soon(release.set)
                    with patch.object(driver, "_close_async", close_resources):
                        self.assertEqual(driver.close(), [])
                    self.assertEqual(
                        events, ["thread-start", "thread-end", "resource-close"]
                    )
                finally:
                    signal.signal(signal.SIGTERM, previous)
                    release.set()
                    driver.close()
                    driver.runner.close()

    def test_sigterm_during_task_creation_registers_task_before_propagation(self):
        import asyncio
        import os
        import signal

        driver = source.AgentSourceDriver(
            Path("/tmp"), "db", "redis://localhost/15", "task-registration"
        )
        driver.runner = asyncio.Runner()
        loop = driver.runner.get_loop()
        create = loop.create_task
        events, registered_at_signal = [], []

        class Interrupted(RuntimeError):
            pass

        def terminate(_signum, _frame):
            registered_at_signal.append(driver._exercise_task is not None)
            raise Interrupted("termination requested")

        def interrupted_create(*args, **kwargs):
            task = create(*args, **kwargs)
            os.kill(os.getpid(), signal.SIGTERM)
            return task

        async def business(*_args):
            events.append("business-after-signal")

        async def close_resources():
            events.append("resource-close")

        previous = signal.signal(signal.SIGTERM, terminate)
        try:
            with (
                patch.object(loop, "create_task", interrupted_create),
                patch.object(driver, "_exercise", business),
            ):
                with self.assertRaises(Interrupted):
                    driver.exercise(None, "", "", "", 1, b"", lambda: None)
            self.assertEqual(registered_at_signal, [True])
            self.assertIs(signal.getsignal(signal.SIGTERM), terminate)
            with patch.object(driver, "_close_async", close_resources):
                self.assertEqual(driver.close(), [])
            self.assertEqual(events, ["resource-close"])
        finally:
            signal.signal(signal.SIGTERM, previous)
            driver.close()
            driver.runner.close()

    def test_registration_restores_handler_when_creation_fails(self):
        import signal

        observed = []

        def handler(signum, _frame):
            observed.append(signum)

        previous = signal.signal(signal.SIGTERM, handler)
        try:
            with self.assertRaisesRegex(RuntimeError, "creation failed"):
                with source._registering_activity():
                    raise RuntimeError("creation failed")
            self.assertIs(signal.getsignal(signal.SIGTERM), handler)
            self.assertEqual(observed, [])
        finally:
            signal.signal(signal.SIGTERM, previous)

    def test_unfinished_future_survives_non_cancellation_await_error(self):
        import asyncio
        import threading

        driver = source.AgentSourceDriver(
            Path("/tmp"), "db", "redis://localhost/15", "await-error"
        )
        driver.runner = asyncio.Runner()
        release = threading.Event()
        events = []

        def blocking():
            if not release.wait(2):
                raise AssertionError("test release missing")
            events.append("thread-end")

        async def close_resources():
            events.append("resource-close")

        try:
            with patch.object(
                source.asyncio, "shield", side_effect=RuntimeError("interrupted await")
            ):
                with self.assertRaises(RuntimeError):
                    driver.runner.run(driver._blocking_call("launch", blocking))
            self.assertEqual(len(driver._blocking_futures), 1)
            driver.runner.get_loop().call_soon(release.set)
            with patch.object(driver, "_close_async", close_resources):
                self.assertEqual(driver.close(), [])
            self.assertEqual(events, ["thread-end", "resource-close"])
        finally:
            release.set()
            driver.close()
            driver.runner.close()

    def test_sigterm_cancels_business_before_any_resource_teardown(self):
        import asyncio
        import os
        import signal
        import threading

        events = []
        driver = source.AgentSourceDriver(
            Path("/tmp"), "db", "redis://localhost/15", "signal"
        )
        driver.runner = asyncio.Runner()

        class TerminationRequested(RuntimeError):
            pass

        def terminate(_signum, _frame):
            raise TerminationRequested("termination requested")

        async def exercise(*_args):
            threading.Timer(0.01, os.kill, args=(os.getpid(), signal.SIGTERM)).start()
            try:
                await asyncio.sleep(0.04)
                events.append("exercise-side-effect-after-termination")
            finally:
                events.append("business-finished")

        async def close_resources():
            events.append("resource-close-start")
            await asyncio.sleep(0.06)
            events.append("resource-close-end")

        previous = signal.signal(signal.SIGTERM, terminate)
        try:
            with (
                patch.object(driver, "_exercise", exercise),
                patch.object(driver, "_close_async", close_resources),
            ):
                with self.assertRaises(TerminationRequested):
                    driver.exercise(None, "", "", "", 1, b"", lambda: None)
                failures = driver.close()
        finally:
            signal.signal(signal.SIGTERM, previous)
            driver.runner.close()
        self.assertEqual(failures, [])
        self.assertEqual(
            events, ["business-finished", "resource-close-start", "resource-close-end"]
        )

    def test_cancelled_launch_and_revoke_threads_finish_before_resources_close(self):
        import asyncio
        import threading

        for label in ("launch", "revoke"):
            for fails in (False, True):
                with self.subTest(label=label, fails=fails):
                    events = []
                    release = threading.Event()
                    started = threading.Event()
                    driver = source.AgentSourceDriver(
                        Path("/tmp"), "db", "redis://localhost/15", "thread"
                    )
                    driver.runner = asyncio.Runner()

                    def blocking():
                        started.set()
                        if not release.wait(2):
                            raise AssertionError("test release missing")
                        events.append("thread-finished")
                        if fails:
                            raise RuntimeError("private credential")
                        return "result"

                    async def business():
                        await driver._blocking_call(label, blocking)
                        events.append("business-side-effect")

                    async def start():
                        driver._exercise_task = asyncio.create_task(business())
                        while not started.is_set():
                            await asyncio.sleep(0.001)

                    async def close_resources():
                        events.append("resource-close-start")

                    driver.runner.run(start())
                    timer = threading.Timer(0.03, release.set)
                    timer.start()
                    try:
                        with patch.object(driver, "_close_async", close_resources):
                            failures = driver.close()
                    finally:
                        release.set()
                        timer.join()
                        driver.runner.close()
                    self.assertEqual(
                        events, ["thread-finished", "resource-close-start"]
                    )
                    self.assertTrue(driver.dependencies_quiescent)
                    self.assertEqual(
                        failures,
                        [f"Agent source {label} thread failed during drain"]
                        if fails
                        else [],
                    )
                    self.assertNotIn("private", str(failures))
                    self.assertEqual(driver._blocking_futures, {})

    def test_thread_timeout_preserves_resources_and_can_retry_after_completion(self):
        import asyncio
        import tempfile
        import threading
        import time

        with tempfile.TemporaryDirectory() as directory:
            driver = source.AgentSourceDriver(
                Path(directory), "db", "redis://localhost/15", "timeout"
            )
            secret = Path(directory) / "key"
            secret.write_text("private")
            driver._files.append(secret)
            driver.runner = asyncio.Runner()
            release, started = threading.Event(), threading.Event()

            def blocking():
                started.set()
                release.wait(2)

            async def start():
                driver._exercise_task = asyncio.create_task(
                    driver._blocking_call("revoke", blocking)
                )
                while not started.is_set():
                    await asyncio.sleep(0.001)

            driver.runner.run(start())
            try:
                with (
                    patch.object(source, "THREAD_DRAIN_SECONDS", 0.02),
                    patch.object(driver, "_close_http") as http_close,
                    patch.object(driver, "_close_async") as runtime_close,
                ):
                    before = time.monotonic()
                    self.assertEqual(
                        driver.close(), ["Agent source executor thread drain timed out"]
                    )
                    self.assertLess(time.monotonic() - before, 0.5)
                    self.assertFalse(driver.dependencies_quiescent)
                    self.assertTrue(secret.exists())
                    http_close.assert_not_called()
                    runtime_close.assert_not_called()
                    self.assertFalse(driver.runner.get_loop().is_closed())
                    with self.assertRaises(source.SourceError):
                        driver.exercise(None, "", "", "", 1, b"", lambda: None)
                release.set()
                self.assertEqual(driver.close(), [])
                self.assertTrue(driver.dependencies_quiescent)
                self.assertFalse(secret.exists())
            finally:
                release.set()
                driver.runner.close()

    def test_cancellation_resistant_business_timeout_prevents_teardown(self):
        import asyncio

        driver = source.AgentSourceDriver(
            Path("/tmp"), "db", "redis://localhost/15", "task"
        )
        driver.runner = asyncio.Runner()
        release = asyncio.Event()

        async def business():
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                await release.wait()

        async def start():
            driver._exercise_task = asyncio.create_task(business())
            await asyncio.sleep(0)

        driver.runner.run(start())
        try:
            with (
                patch.object(source, "TASK_DRAIN_SECONDS", 0.01),
                patch.object(driver, "_close_http") as close,
            ):
                self.assertEqual(
                    driver.close(), ["Agent source business task drain timed out"]
                )
                self.assertFalse(driver.dependencies_quiescent)
                close.assert_not_called()
            release.set()
            self.assertEqual(driver.close(), [])
        finally:
            release.set()
            driver.runner.close()

    def test_cancel_finalizer_error_is_reported_without_unobserved_task_exception(self):
        import asyncio
        import os
        import signal
        import threading

        driver = source.AgentSourceDriver(
            Path("/tmp"), "db", "redis://localhost/15", "finalizer"
        )
        driver.runner = asyncio.Runner()
        loop_errors = []
        driver.runner.get_loop().set_exception_handler(
            lambda _loop, context: loop_errors.append(context)
        )

        class Interrupted(BaseException):
            pass

        def terminate(_signum, _frame):
            raise Interrupted()

        async def business(*_args):
            threading.Timer(0.01, os.kill, args=(os.getpid(), signal.SIGTERM)).start()
            try:
                await asyncio.sleep(0.05)
            finally:
                raise RuntimeError("private finalizer failure")

        previous = signal.signal(signal.SIGTERM, terminate)
        try:
            with patch.object(driver, "_exercise", business):
                with self.assertRaises(Interrupted):
                    driver.exercise(None, "", "", "", 1, b"", lambda: None)
                self.assertEqual(
                    driver.close(), ["Agent source business task failed during drain"]
                )
                self.assertTrue(driver.dependencies_quiescent)
        finally:
            signal.signal(signal.SIGTERM, previous)
            driver.runner.close()
        self.assertEqual(loop_errors, [])

    def test_http_close_error_after_handlers_drain_is_not_active_work(self):
        from unittest.mock import Mock

        driver = source.AgentSourceDriver(
            Path("/tmp"), "db", "redis://localhost/15", "http"
        )
        driver.server = Mock()
        driver.server.wait_for_active_handlers.return_value = True
        driver.server.server_close.side_effect = OSError("private")
        self.assertEqual(driver.close(), ["Agent source HTTP cleanup failed"])
        self.assertTrue(driver.dependencies_quiescent)

    def test_http_active_handlers_keep_dependencies_until_operator_cleanup(self):
        from unittest.mock import Mock

        driver = source.AgentSourceDriver(
            Path("/tmp"), "db", "redis://localhost/15", "http"
        )
        driver.server = Mock()
        driver.server.wait_for_active_handlers.return_value = False
        self.assertEqual(driver.close(), ["Agent source HTTP cleanup failed"])
        self.assertFalse(driver.dependencies_quiescent)
        self.assertGreaterEqual(source.THREAD_DRAIN_SECONDS, 30)

    def test_normal_thread_return_and_error_are_observed_by_business(self):
        import asyncio

        driver = source.AgentSourceDriver(
            Path("/tmp"), "db", "redis://localhost/15", "normal"
        )
        driver.runner = asyncio.Runner()

        def fail():
            raise ValueError("private")

        async def run():
            self.assertEqual(
                await driver._blocking_call("launch", lambda value: value, 7), 7
            )
            with self.assertRaises(ValueError):
                await driver._blocking_call("revoke", fail)
            self.assertEqual(driver._blocking_futures, {})

        driver.runner.run(run())
        self.assertEqual(driver.close(), [])


class SourceCleanupTests(unittest.TestCase):
    def test_partial_startup_closes_http_and_retains_failed_cleanup_evidence(self):
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            driver = source.AgentSourceDriver(
                Path(directory),
                "postgresql://localhost/db",
                "redis://localhost/15",
                "abc",
            )
            path = Path(directory) / "owned.pem"
            path.write_text("secret")
            driver._files.append(path)
            with patch.object(
                driver, "_close_http", side_effect=RuntimeError("sensitive")
            ) as close:
                first = driver.close()
                second = driver.close()
            self.assertEqual(first, ["Agent source HTTP cleanup failed"])
            self.assertEqual(second, first)
            close.assert_called_once()
            self.assertTrue(path.exists())

    def test_async_cleanup_preserves_foreign_redis_and_closes_pool_after_runtime_failure(
        self,
    ):
        import asyncio

        events = []

        class Stack:
            async def aclose(self):
                events.append("runtime")
                raise RuntimeError("secret")

        class Redis:
            async def eval(self, script, count, *arguments):
                events.append(("eval", count, arguments))
                return "OWNERSHIP_LOST"

            async def aclose(self):
                events.append("redis-close")

        driver = source.AgentSourceDriver(
            Path("/tmp"), "db", "redis://localhost/15", "abc"
        )
        driver.stack, driver.redis, driver.claimed = Stack(), Redis(), True
        with self.assertRaises(source.SourceError):
            asyncio.run(driver._close_async())
        self.assertTrue(driver.claimed)
        self.assertEqual(events[0], "runtime")
        self.assertEqual(events[-1], "redis-close")
        self.assertEqual(
            events[1][1:], (2, (driver.marker, "kokoro:runs:requests", "abc"))
        )
        self.assertIn("'UNEXPECTED_KEY'", source.CLEAN)
        self.assertIn("'OWNERSHIP_LOST'", source.CLEAN)
        self.assertNotIn("FLUSH", source.CLEAN)

    def test_ascii_command_domain_rejects_non_jcs_shortcuts(self):
        for value in (1, 1.5, None, ["x"], {"x": "é"}, {"x": "\n"}):
            with self.subTest(value=value), self.assertRaises(source.SourceError):
                source.command_digest({"command": value})


@unittest.skipUnless(
    importlib.util.find_spec("kokoro_agent") is not None,
    "native component requires Agent .venv Python",
)
class SourceNativeComponentTests(unittest.TestCase):
    def test_setup_rpc_reports_only_standard_code_and_owned_stage(self):
        import asyncio
        from types import SimpleNamespace
        from unittest.mock import AsyncMock
        from connectrpc.code import Code
        from connectrpc.errors import ConnectError
        from kokoro_agent.generated.kokoro.platform.v1 import platform_runtime_pb as pb
        from kokoro_agent.execution import execution_proof_supplier

        from pyqwest import ConnectTimeout, RemoteProtocolError, StreamError

        class PRIVATE_UNKNOWN_SENTINEL(ValueError):
            pass

        causes = [
            (ValueError("PRIVATE_SENTINEL"), "value_error"),
            (TypeError("PRIVATE_SENTINEL"), "type_error"),
            (ConnectionError("PRIVATE_SENTINEL"), "connection_error"),
            (OSError("PRIVATE_SENTINEL"), "os_error"),
            (RemoteProtocolError("PRIVATE_SENTINEL"), "remote_protocol_error"),
            (StreamError("PRIVATE_SENTINEL", 7), "stream_error"),
            (ConnectTimeout("PRIVATE_SENTINEL"), "connect_timeout"),
            (RuntimeError("PRIVATE_SENTINEL"), "unknown"),
            (PRIVATE_UNKNOWN_SENTINEL("PRIVATE_SENTINEL"), "unknown"),
        ]
        cases = [(code, None, "none") for code in (*Code, "PRIVATE_CODE_SENTINEL")]
        cases.extend((Code.UNAVAILABLE, cause, kind) for cause, kind in causes)
        for enabled in (False, True):
            for code, cause, cause_kind in cases:
                label = code.name if isinstance(code, Code) else "UNKNOWN"
                with self.subTest(enabled=enabled, code=label):
                    driver = source.AgentSourceDriver(
                        Path("/tmp"), "db", "redis://localhost/15", "diagnostic"
                    )
                    driver.phase = (
                        "installation disable"
                        if not enabled
                        else "installation re-enable"
                    )
                    driver.runtime = SimpleNamespace(
                        tokens=SimpleNamespace(
                            token=AsyncMock(return_value="TOKEN_SENTINEL")
                        ),
                        lease_reader=object(),
                        signer=object(),
                    )
                    error = ConnectError(
                        code,
                        "IAM execution authorization failed"
                        if enabled
                        else "PRIVATE_MESSAGE TOKEN_SENTINEL PROOF_SENTINEL",
                    )
                    error.__cause__ = cause
                    rpc = AsyncMock(side_effect=error)
                    driver.installer = SimpleNamespace(
                        set_skill_installation_enabled=rpc
                    )
                    supplier = SimpleNamespace(
                        issue=AsyncMock(return_value="PROOF_SENTINEL")
                    )
                    request = pb.SetSkillInstallationEnabledRequest(
                        installation_id=pb.SkillInstallationId(value="installation-1"),
                        enabled=enabled,
                    )
                    with patch.object(
                        execution_proof_supplier,
                        "create_execution_proof_supplier",
                        return_value=supplier,
                    ):
                        with self.assertRaises(source.SourceError) as captured:
                            asyncio.run(
                                driver._command(
                                    SimpleNamespace(tenant_id="tenant-1"),
                                    object(),
                                    "SetSkillInstallationEnabled",
                                    {
                                        "installation_id": {
                                            "present": True,
                                            "value": "installation-1",
                                        },
                                        "enabled": enabled,
                                    },
                                    request,
                                )
                            )
                    self.assertEqual(
                        str(captured.exception),
                        f"Agent source {driver.phase} SetSkillInstallationEnabled failed ({label}; "
                        f"cause={str(cause is not None).lower()}; cause_type={cause_kind}; "
                        f"category={'iam_execution' if enabled else 'unclassified'})",
                    )
                    self.assertIsNone(captured.exception.__context__)
                    rpc.assert_awaited_once()
                    self.assertEqual(
                        rpc.await_args.kwargs["headers"],
                        {"authorization": "Bearer TOKEN_SENTINEL"},
                    )
                    self.assertEqual(rpc.await_args.kwargs["timeout_ms"], 10_000)
                    self.assertEqual(request.execution_proof, "PROOF_SENTINEL")
                    self.assertEqual(request.enabled, enabled)
                    self.assertNotIn("SENTINEL", str(captured.exception))
                    self.assertNotIn("PRIVATE", str(captured.exception))

    def test_real_native_metadata_and_original_bytes_without_services(self):
        import asyncio
        from kokoro_agent.clients.skills import ResolvedSkill
        from kokoro_agent.skills.backend import TypedSkillBackend

        skill = ResolvedSkill(
            source_ref="skill:source-fixture",
            skill_id="source-fixture",
            revision=1,
            asset_ref="asset",
            content_digest="a" * 64,
            manifest_identity="zip-v1:sha256:" + "b" * 64,
        )

        class Reader:
            calls = 0

            async def load_package(self, resolved):
                self.calls += 1
                return {"SKILL.md": source.SKILL_BYTES}

        reader = Reader()
        backend = TypedSkillBackend((skill,), reader)

        async def run():
            await source.verify_native_metadata(backend, skill.path_segment)
            from deepagents.backends.protocol import PERMISSION_DENIED

            self.assertEqual(
                (
                    await backend.awrite(f"/{skill.path_segment}/SKILL.md", "forbidden")
                ).error,
                PERMISSION_DENIED,
            )
            result = (
                await backend.adownload_files([f"/{skill.path_segment}/SKILL.md"])
            )[0]
            self.assertEqual(result.content, source.SKILL_BYTES)
            self.assertGreaterEqual(reader.calls, 2)

        asyncio.run(run())

    def test_native_parser_rejects_old_no_frontmatter_fixture(self):
        import asyncio
        from kokoro_agent.clients.skills import ResolvedSkill
        from kokoro_agent.skills.backend import TypedSkillBackend

        skill = ResolvedSkill(
            source_ref="skill:source-fixture",
            skill_id="source-fixture",
            revision=1,
            asset_ref="asset",
            content_digest="a" * 64,
            manifest_identity="zip-v1:sha256:" + "b" * 64,
        )

        class Reader:
            async def load_package(self, resolved):
                return {"SKILL.md": b"# Sandbox\n\nOwned signed PUT smoke.\n"}

        with self.assertRaises(source.SourceError):
            asyncio.run(
                source.verify_native_metadata(
                    TypedSkillBackend((skill,), Reader()), skill.path_segment
                )
            )


class SourceOwnerContractTests(unittest.TestCase):
    def test_both_setup_digests_match_fixed_owner_wire_vectors(self):
        path = (
            source.AGENT
            / "contract/platform/v1/execution-operations/v4/vectors/command-projection.json"
        )
        vectors = json.loads(path.read_text())["vectors"]
        checked = set()
        for vector in vectors:
            if vector["name"] not in {
                "skill.install.wire.valid",
                "skill.set_installation_enabled.wire.valid",
            }:
                continue
            document = vector["projection"]
            method = document["fq_method"].split("/")[-1]
            actual = source.command_document(
                document["tenant_ref"], method, document["command"]
            )
            self.assertEqual(source.command_digest(actual), vector["sha256"])
            checked.add(method)
        self.assertEqual(checked, {"InstallSkill", "SetSkillInstallationEnabled"})

    def test_unknown_claim_ack_is_cleaned_only_when_marker_matches(self):
        import asyncio

        for marker_matches in (False, True):
            events = []

            class Redis:
                async def get(self, key):
                    events.append("get")
                    return "abc" if marker_matches else None

                async def eval(self, *args):
                    events.append("cleanup")
                    return "OK"

                async def aclose(self):
                    events.append("close")

            driver = source.AgentSourceDriver(
                Path("/tmp"), "db", "redis://localhost/15", "abc"
            )
            driver.redis = Redis()
            driver.claim_attempted = True
            asyncio.run(driver._close_async())
            self.assertEqual(
                events,
                ["get", "cleanup", "close"] if marker_matches else ["get", "close"],
            )
