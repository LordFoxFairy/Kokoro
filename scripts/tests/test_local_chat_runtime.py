"""Pure local Chat composition checks; no provider or infrastructure access."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
import importlib
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/dev"))


class LocalChatRuntimeTests(unittest.TestCase):
    def module(self):
        return importlib.import_module("local_chat_runtime")

    def test_explicit_redis_db_and_provider_boundary(self):
        m = self.module()
        m.validate_options(
            "redis://127.0.0.1:6379/0",
            "redis://127.0.0.1:6379/10",
            "http://127.0.0.1:11434",
            "qwen3:8b",
        )
        for redis in (
            "redis://127.0.0.1:6379/0",
            "redis://127.0.0.1:6379",
            "redis://127.0.0.1:6379/10?x=1",
            "redis://user:SECRET@127.0.0.1:6379/10",
        ):
            with self.subTest(redis=redis), self.assertRaises(m.ChatError):
                m.validate_options(
                    "redis://127.0.0.1:6379/0",
                    redis,
                    "http://127.0.0.1:11434",
                    "qwen3:8b",
                )
        with self.assertRaises(m.ChatError):
            m.validate_options(
                "redis://127.0.0.1:6379/0",
                "redis://127.0.0.1:6379/10",
                "https://remote.example",
                "qwen3:8b",
            )

    def test_command_is_frozen_standard_cli(self):
        m = self.module()
        self.assertEqual(
            m.agent_command(Path("/tool/uv"), "worker"),
            ["/tool/uv", "run", "--frozen", "--no-sync", "kokoro-agent-worker"],
        )
        with self.assertRaises(m.ChatError):
            m.agent_command(Path("/tool/uv"), "embedded")

    def test_run_cleanup_accepts_multiple_owned_runs_not_unknown_keys(self):
        m = self.module()
        ownership = Mock()
        resources = Mock()
        resources.command.return_value = (
            '[{"session":"c1","run":"r1"},{"session":"c1","run":"r2"}]'
        )
        m.register_owned_runs(resources, "postgresql://local/app", ownership)
        self.assertEqual(ownership.register_run.call_count, 2)
        self.assertIn(
            "kokoro_agent.kokoro_agent_run", resources.command.call_args.args[0][-1]
        )
        resources.command.return_value = '[{"session":"bad\n","run":"r1"}]'
        with self.assertRaises(m.ChatError):
            m.register_owned_runs(resources, "postgresql://local/app", ownership)

    def test_close_drains_worker_before_http_system_and_redis(self):
        m = self.module()
        obj = m.LocalChatRuntime.__new__(m.LocalChatRuntime)
        obj.processes = [("system", Mock()), ("http", Mock()), ("worker", Mock())]
        obj.agent_installed = True
        obj.resources = Mock()
        obj.database_url = "postgresql://local/owned"
        obj.ownership = Mock()
        obj.quiescent = False
        events = []
        with (
            patch.object(
                m,
                "stop_chat_process",
                side_effect=lambda p, grace: events.append(grace),
            ),
            patch.object(
                m, "register_owned_runs", side_effect=lambda *a: events.append("runs")
            ),
        ):
            obj.ownership.cleanup.side_effect = lambda: events.append("redis")
            self.assertEqual(obj.close(), [])
        self.assertEqual(events, [70, 15, 15, "runs", "redis"])
        self.assertTrue(obj.quiescent)

    def test_failed_stop_preserves_dependencies_and_redis(self):
        m = self.module()
        obj = m.LocalChatRuntime.__new__(m.LocalChatRuntime)
        obj.processes = [("system", Mock()), ("http", Mock()), ("worker", Mock())]
        obj.ownership = Mock()
        obj.quiescent = False
        with patch.object(
            m, "stop_chat_process", side_effect=m.ChatError("stop")
        ) as stop:
            self.assertEqual(obj.close(), ["Chat worker shutdown"])
        self.assertEqual(stop.call_count, 1)
        obj.ownership.cleanup.assert_not_called()
        self.assertFalse(obj.quiescent)


class LocalChatCompositionTests(unittest.TestCase):
    def test_start_real_owner_and_two_standard_clis_same_database(self):
        import tempfile
        from contextlib import ExitStack

        m = importlib.import_module("local_chat_runtime")
        with tempfile.TemporaryDirectory() as temp, ExitStack() as patches:
            for name in ("_run_owner_command", "_isolated_owner"):
                patches.enter_context(
                    patch.object(m.owned, name, return_value=Path(temp))
                )
            patches.enter_context(patch.object(m.real_model, "provider_preflight"))
            patches.enter_context(patch.object(m.system, "wait_ready"))
            patches.enter_context(
                patch.object(
                    m.system,
                    "seed_control_plane",
                    return_value={"provider_id": "p", "revision_id": "r"},
                )
            )
            patches.enter_context(patch.object(m.agent_runtime, "_wait_ready"))
            patches.enter_context(patch.object(m.LocalChatRuntime, "_command"))
            patches.enter_context(
                patch.object(m.runtime, "free_port", side_effect=[4100, 4200])
            )
            ownership = Mock(claimed=True)
            ownership._call.return_value = "1"
            patches.enter_context(
                patch.object(m.owned, "AgentRedisOwnership", return_value=ownership)
            )
            process = Mock()
            process.poll.return_value = None
            popen = patches.enter_context(
                patch.object(m.subprocess, "Popen", return_value=process)
            )
            resources = SimpleNamespace(
                run_id="a" * 24,
                redis_url="redis://localhost/0",
                redis_prefix="own:",
                claim_redis_prefix=Mock(),
            )
            obj = m.LocalChatRuntime(
                config=SimpleNamespace(
                    endpoint="http://127.0.0.1:11434", model="qwen3:8b"
                ),
                uv=Path("/uv"),
                node=Path("/node"),
                node_env={"NODE_OPTIONS": "--import=guard"},
                directory=Path(temp),
                resources=resources,
                credentials=Mock(),
                log=Mock(),
                tenant="tenant",
                agent_redis_url="redis://localhost/10",
            )
            result = obj.start("postgresql://localhost/owned")
            self.assertEqual(result["KOKORO_AGENT_ENABLED"], "true")
            self.assertEqual(result["KOKORO_SYSTEM_BASE_URL"], "http://127.0.0.1:4100")
            self.assertEqual(
                [call.args[0][-1] for call in popen.call_args_list],
                [
                    str(Path(temp) / "dist/main.js"),
                    "kokoro-agent-http",
                    "kokoro-agent-worker",
                ],
            )
            system_env, http_env, worker_env = [
                call.kwargs["env"] for call in popen.call_args_list
            ]
            self.assertEqual(
                system_env["DATABASE_URL"], http_env["KOKORO_AGENT_DATABASE_URL"]
            )
            self.assertEqual(
                http_env["KOKORO_AGENT_DATABASE_URL"],
                worker_env["KOKORO_AGENT_DATABASE_URL"],
            )
            self.assertEqual(system_env["NODE_OPTIONS"], "--import=guard")
            self.assertEqual(
                worker_env["KOKORO_LITELLM_BASE_URL"], "http://127.0.0.1:11434/v1"
            )
            self.assertEqual(worker_env["PYTHON_DOTENV_DISABLED"], "1")
            self.assertFalse(
                any("STORAGE" in key or "PLATFORM" in key for key in worker_env)
            )
            self.assertEqual(
                [label for label, _ in obj.processes], ["system", "http", "worker"]
            )

    def test_health_failure_does_not_publish_or_silently_continue(self):
        m = importlib.import_module("local_chat_runtime")
        obj = m.LocalChatRuntime.__new__(m.LocalChatRuntime)
        obj.processes, obj.next_refresh, obj.config = [], 0, object()
        with (
            patch.object(
                m.real_model,
                "provider_preflight",
                side_effect=m.ChatError("provider unavailable"),
            ),
            patch.object(m.system, "http_json") as http,
        ):
            with self.assertRaises(m.ChatError):
                obj.tick()
            http.assert_not_called()

    def test_process_creation_signal_is_delivered_after_registration(self):
        import os
        import signal

        m = importlib.import_module("local_chat_runtime")
        events = []
        previous = signal.getsignal(signal.SIGTERM)

        def terminate(_signum, _frame):
            events.append("terminated")
            raise KeyboardInterrupt

        signal.signal(signal.SIGTERM, terminate)
        try:
            with self.assertRaises(KeyboardInterrupt):
                with m.registration_guard():
                    os.kill(os.getpid(), signal.SIGTERM)
                    events.append("registered")
            self.assertEqual(events, ["registered", "terminated"])
        finally:
            signal.signal(signal.SIGTERM, previous)

    def test_python_guard_normal_exit_and_parent_death(self):
        import os
        import subprocess
        import tempfile
        import time

        m = importlib.import_module("local_chat_runtime")
        with tempfile.TemporaryDirectory() as temp:
            env = dict(os.environ)
            m.install_python_parent_guard(Path(temp), env, grace=0.3)
            normal = subprocess.run(
                [sys.executable, "-c", 'print("done")'],
                env=env,
                capture_output=True,
                timeout=3,
            )
            self.assertEqual(normal.returncode, 0)
            self.assertEqual(normal.stdout, b"done\n")
            # Missing launcher simulates death while a uv parent still survives.
            env["KOKORO_LOCAL_CHAT_PARENT_PID"] = "2147483647"
            dead = subprocess.run(
                [sys.executable, "-c", "import time; time.sleep(10)"],
                env=env,
                capture_output=True,
                timeout=3,
            )
            self.assertEqual(dead.returncode, -15)
            # A real parent/child pair lets the child install SIGTERM handling
            # before the parent dies, proving the bounded force-stop branch.
            ready = Path(temp) / "ready"
            parent = subprocess.Popen(
                [
                    sys.executable,
                    "-c",
                    'import os,subprocess,sys,time; os.environ["KOKORO_LOCAL_CHAT_PARENT_PID"]=str(os.getpid()); subprocess.Popen([sys.executable,"-c",sys.argv[1]],env=os.environ); time.sleep(10)',
                    "import signal,pathlib,time; signal.signal(signal.SIGTERM,lambda *_: None); pathlib.Path("
                    + repr(str(ready))
                    + ').write_text("ready"); time.sleep(10)',
                ],
                env={**env, "KOKORO_LOCAL_CHAT_PARENT_PID": str(os.getpid())},
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            try:
                deadline = time.monotonic() + 3
                while not ready.exists() and time.monotonic() < deadline:
                    time.sleep(0.02)
                self.assertTrue(ready.exists())
                parent.kill()
                parent.communicate(
                    timeout=3
                )  # inherited pipes close only after child dies
            finally:
                if parent.poll() is None:
                    parent.kill()
                    parent.communicate(timeout=3)


class LocalChatFailureTests(unittest.TestCase):
    def test_every_started_process_is_available_to_failure_cleanup(self):
        import tempfile
        from contextlib import ExitStack

        m = importlib.import_module("local_chat_runtime")
        for fail_at, expected in [
            ("claim", []),
            ("system", ["system"]),
            ("seed", ["system"]),
            ("installer", ["system"]),
            ("http", ["system", "http"]),
            ("worker", ["system", "http", "worker"]),
        ]:
            with (
                self.subTest(stage=fail_at),
                tempfile.TemporaryDirectory() as temp,
                ExitStack() as patches,
            ):
                ownership = Mock(claimed=False)
                ownership._call.return_value = ""

                def claim():
                    if fail_at == "claim":
                        raise m.ChatError("claim rejected")
                    ownership.claimed = True

                ownership.claim.side_effect = claim
                patches.enter_context(
                    patch.object(m.owned, "AgentRedisOwnership", return_value=ownership)
                )
                patches.enter_context(
                    patch.object(m.owned, "_isolated_owner", return_value=Path(temp))
                )
                patches.enter_context(patch.object(m.owned, "_run_owner_command"))
                patches.enter_context(patch.object(m.real_model, "provider_preflight"))
                patches.enter_context(
                    patch.object(
                        m.system,
                        "wait_ready",
                        side_effect=m.ChatError("startup")
                        if fail_at == "system"
                        else None,
                    )
                )
                patches.enter_context(
                    patch.object(
                        m.system,
                        "seed_control_plane",
                        side_effect=m.ChatError("seed") if fail_at == "seed" else None,
                        return_value={"provider_id": "p"},
                    )
                )
                patches.enter_context(
                    patch.object(
                        m.LocalChatRuntime,
                        "_command",
                        side_effect=lambda label, *a, **k: (
                            (_ for _ in ()).throw(m.ChatError("installer"))
                            if fail_at == "installer" and label == "Agent schema"
                            else None
                        ),
                    )
                )
                patches.enter_context(
                    patch.object(
                        m.agent_runtime,
                        "_wait_ready",
                        side_effect=m.ChatError("http") if fail_at == "http" else None,
                    )
                )
                process = Mock()
                process.poll.return_value = 1
                patches.enter_context(
                    patch.object(m.subprocess, "Popen", return_value=process)
                )
                patches.enter_context(
                    patch.object(m.runtime, "free_port", side_effect=[4100, 4200])
                )
                obj = m.LocalChatRuntime(
                    config=SimpleNamespace(
                        endpoint="http://127.0.0.1:11434", model="qwen3:8b"
                    ),
                    uv=Path("/uv"),
                    node=Path("/node"),
                    node_env={},
                    directory=Path(temp),
                    resources=SimpleNamespace(
                        run_id="a" * 24,
                        redis_url="redis://localhost/0",
                        redis_prefix="own:",
                        claim_redis_prefix=Mock(),
                    ),
                    credentials=Mock(),
                    log=Mock(),
                    tenant="tenant",
                    agent_redis_url="redis://localhost/10",
                )
                with self.assertRaises(m.ChatError):
                    obj.start("postgresql://localhost/owned")
                self.assertEqual([label for label, _ in obj.processes], expected)
                with (
                    patch.object(m, "stop_chat_process") as stop,
                    patch.object(m, "register_owned_runs"),
                ):
                    self.assertEqual(obj.close(), [])
                    self.assertEqual(stop.call_count, len(expected))
                ownership.cleanup.assert_called_once()

    def test_foreground_health_uses_real_probe_and_cas_then_renews(self):
        m = importlib.import_module("local_chat_runtime")
        obj = m.LocalChatRuntime.__new__(m.LocalChatRuntime)
        obj.processes, obj.next_refresh, obj.config = [], 0, object()
        obj.ownership = SimpleNamespace(url="redis://local/10", marker="agent-marker")
        obj.resources = Mock(
            redis_url="redis://local/0", redis_prefix="own:", run_id="a" * 24
        )
        obj.resources.command.return_value = "1"
        obj.system_base, obj._token, obj.health_generation = (
            "http://local",
            "SECRET",
            "1",
        )
        obj.route = {"provider_id": "provider"}
        events = []
        with (
            patch.object(
                m.real_model,
                "provider_preflight",
                side_effect=lambda *_: events.append("probe"),
            ),
            patch.object(
                m.system,
                "http_json",
                side_effect=lambda *a, **k: (
                    events.append(k)
                    or {"data": {"provider_id": "provider", "generation": "2"}}
                ),
            ),
        ):
            obj.tick()
        self.assertEqual(events[0], "probe")
        self.assertEqual(events[1]["headers"]["if-match"], '"1"')
        self.assertEqual(events[1]["body"]["status"], "healthy")
        self.assertEqual(obj.health_generation, "2")
        self.assertEqual(obj.resources.command.call_count, 2)
        self.assertGreater(obj.next_refresh, 0)

    def test_existing_redis_is_never_adopted_or_flushed(self):
        m = importlib.import_module("local_chat_runtime")
        owner = m.owned.AgentRedisOwnership("redis://127.0.0.1:6379/10", "a" * 24)
        with patch.object(owner, "_call", return_value="NOT_EMPTY") as call:
            with self.assertRaises(m.owned.SmokeError):
                owner.claim()
            owner.cleanup()
        self.assertEqual(call.call_count, 1)
        self.assertNotIn("FLUSH", repr(call.call_args))


class ShortCommandRegistrationTests(unittest.TestCase):
    def test_sigterm_between_short_command_spawn_and_return_is_registered(self):
        import os
        import signal
        import tempfile
        from contextlib import ExitStack

        m = importlib.import_module("local_chat_runtime")
        for interrupted_spawn in (1, 2, 4):
            with (
                self.subTest(spawn=interrupted_spawn),
                tempfile.TemporaryDirectory() as temp,
                ExitStack() as patches,
            ):
                ownership = Mock(claimed=True)
                patches.enter_context(
                    patch.object(m.owned, "AgentRedisOwnership", return_value=ownership)
                )
                patches.enter_context(
                    patch.object(m.owned, "_isolated_owner", return_value=Path(temp))
                )
                patches.enter_context(
                    patch.object(m.runtime, "free_port", return_value=4100)
                )
                patches.enter_context(patch.object(m.system, "wait_ready"))
                patches.enter_context(
                    patch.object(
                        m.system,
                        "seed_control_plane",
                        return_value={"provider_id": "p"},
                    )
                )
                patches.enter_context(patch.object(m.real_model, "provider_preflight"))
                patches.enter_context(patch.object(m, "stop_chat_process"))
                patches.enter_context(patch.object(m.runtime, "stop_owned_process"))
                obj = m.LocalChatRuntime(
                    config=SimpleNamespace(
                        endpoint="http://127.0.0.1:11434", model="qwen3:8b"
                    ),
                    uv=Path("/uv"),
                    node=Path("/node"),
                    node_env={},
                    directory=Path(temp),
                    resources=SimpleNamespace(
                        run_id="a" * 24,
                        redis_url="redis://localhost/0",
                        redis_prefix="own:",
                        claim_redis_prefix=Mock(),
                    ),
                    credentials=Mock(),
                    log=Mock(),
                    tenant="tenant",
                    agent_redis_url="redis://localhost/10",
                )
                created = []

                def popen(*_args, **_kwargs):
                    process = Mock()
                    process.wait.return_value = 0
                    process.poll.return_value = 0
                    created.append(process)
                    if len(created) == interrupted_spawn:
                        os.kill(os.getpid(), signal.SIGTERM)
                    return process

                patches.enter_context(
                    patch.object(m.subprocess, "Popen", side_effect=popen)
                )
                previous = signal.getsignal(signal.SIGTERM)

                def terminate(*_):
                    raise KeyboardInterrupt

                signal.signal(signal.SIGTERM, terminate)
                try:
                    with self.assertRaises(KeyboardInterrupt):
                        obj.start("postgresql://localhost/owned")
                    self.assertIn(
                        created[-1], [process for _, process in obj.processes]
                    )
                    self.assertFalse(obj.quiescent)
                    ownership.cleanup.assert_not_called()
                    self.assertEqual(obj.close(), [])
                finally:
                    signal.signal(signal.SIGTERM, previous)

    def test_short_command_wait_is_interruptible_and_removes_only_stopped_handle(self):
        import os
        import signal

        m = importlib.import_module("local_chat_runtime")
        obj = m.LocalChatRuntime.__new__(m.LocalChatRuntime)
        obj.processes, obj.quiescent, obj.log = [], True, Mock()
        process = Mock()

        def wait(**_kwargs):
            self.assertIn(("installer", process), obj.processes)
            os.kill(os.getpid(), signal.SIGTERM)

        process.wait.side_effect = wait
        previous = signal.getsignal(signal.SIGTERM)

        def terminate(*_):
            raise KeyboardInterrupt

        signal.signal(signal.SIGTERM, terminate)
        try:
            with (
                patch.object(m.subprocess, "Popen", return_value=process),
                patch.object(m, "stop_chat_process") as stop,
            ):
                with self.assertRaises(KeyboardInterrupt):
                    obj._command("installer", ["unused"], cwd=ROOT, env={}, timeout=120)
                stop.assert_called_once_with(process, 15)
                self.assertEqual(obj.processes, [])
                self.assertTrue(obj.quiescent)
        finally:
            signal.signal(signal.SIGTERM, previous)

    def test_short_command_timeout_keeps_handle_if_stop_fails(self):
        import subprocess

        m = importlib.import_module("local_chat_runtime")
        obj = m.LocalChatRuntime.__new__(m.LocalChatRuntime)
        obj.processes, obj.quiescent, obj.log = [], True, Mock()
        process = Mock()
        process.wait.side_effect = subprocess.TimeoutExpired("unused", 120)
        with (
            patch.object(m.subprocess, "Popen", return_value=process),
            patch.object(
                m, "stop_chat_process", side_effect=m.ChatError("stop incomplete")
            ),
        ):
            with self.assertRaises(m.ChatError):
                obj._command("installer", ["unused"], cwd=ROOT, env={}, timeout=120)
        self.assertEqual(obj.processes, [("installer", process)])
        self.assertFalse(obj.quiescent)
