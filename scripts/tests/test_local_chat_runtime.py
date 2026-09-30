"""Pure local Chat composition checks; no provider or infrastructure access."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
import importlib
import json
import os
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/dev"))


def health_receipt(body, generation="2"):
    """System's complete health shape, echoing the observation it persisted."""
    return {
        "data": {
            **body,
            "provider_id": "provider",
            "generation": generation,
            "updated_at": body["observed_at"],
        }
    }


class ExternalModelBoundaryTests(unittest.TestCase):
    def module(self):
        return importlib.import_module("model_provider")

    def credential(self, directory, **changes):
        path = Path(directory) / "provider.json"
        value = {
            "base_url": "https://provider.example/v1",
            "model": "gpt-5.6-luna",
            "api_key": "test-private-provider-key",
        }
        value.update(changes)
        path.write_text(json.dumps(value))
        path.chmod(0o600)
        return path

    def test_private_config_hides_key_and_has_exact_explicit_model(self):
        m = self.module()
        with tempfile.TemporaryDirectory() as directory:
            config = m.load_external(self.credential(directory))
        self.assertEqual(config.base_url, "https://provider.example/v1")
        self.assertEqual(config.model, "gpt-5.6-luna")
        self.assertNotIn("test-private-provider-key", repr(config))

    def test_invalid_json_oversize_and_relative_file_are_rejected(self):
        m = self.module()
        with tempfile.TemporaryDirectory() as directory:
            path = self.credential(directory)
            for raw in (
                b"\xff",
                b"not-json",
                b"x" * 16_385,
                b'{"base_url":"https://provider.example/v1","model":"other","model":"gpt-5.6-luna","api_key":"test-private-provider-key"}',
            ):
                path.write_bytes(raw)
                with self.subTest(size=len(raw)), self.assertRaises(m.ProviderError):
                    m.load_external(path)
        with self.assertRaises(m.ProviderError):
            m.load_external(Path("relative.json"))

    def test_credential_file_rejects_permission_symlink_and_owner(self):
        m = self.module()
        with tempfile.TemporaryDirectory() as directory:
            path = self.credential(directory)
            path.chmod(0o644)
            with self.assertRaises(m.ProviderError):
                m.load_external(path)
            path.chmod(0o600)
            link = Path(directory) / "alias.json"
            link.symlink_to(path)
            with self.assertRaises(m.ProviderError):
                m.load_external(link)
            with patch.object(m.os, "getuid", return_value=os.getuid() + 1):
                with self.assertRaises(m.ProviderError):
                    m.load_external(path)

    def test_invalid_profiles_never_expose_secret(self):
        m = self.module()
        with tempfile.TemporaryDirectory() as directory:
            cases = [
                {"base_url": value}
                for value in (
                    "http://provider.example/v1",
                    "https://user:pass@provider.example/v1",
                    "https://provider.example/v1?key=secret",
                    "https://provider.example/v1#fragment",
                    "https://provider.example/v1?",
                    "https://provider.example/v1#",
                    "https://@provider.example/v1",
                    "https://provider.example/other",
                    "https://provider.example:444/v1",
                )
            ]
            cases += [
                {"model": ""},
                {"model": "bad\nmodel"},
                {"extra": True},
                {"api_key": ""},
            ]
            for value in cases:
                with (
                    self.subTest(value=value),
                    self.assertRaises(m.ProviderError) as caught,
                ):
                    m.load_external(self.credential(directory, **value))
                self.assertNotIn("test-private-provider-key", str(caught.exception))

    def test_provider_inventory_request_is_bounded_tls_and_no_redirect(self):
        m = self.module()
        response = Mock(status=200)
        response.read.return_value = b'{"data":[{"id":"gpt-5.6-luna"}]}'
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        opener = Mock()
        opener.open.return_value = response
        with tempfile.TemporaryDirectory() as directory:
            config = m.load_external(self.credential(directory))
        with patch.object(m, "build_opener", return_value=opener) as build:
            m.provider_preflight(config)
        request = opener.open.call_args.args[0]
        self.assertEqual(request.full_url, "https://provider.example/v1/models")
        self.assertEqual(request.get_method(), "GET")
        self.assertEqual(
            request.get_header("Authorization"), "Bearer test-private-provider-key"
        )
        self.assertEqual(opener.open.call_args.kwargs["timeout"], 10)
        response.read.assert_called_once_with(1_048_577)
        handlers = build.call_args.args
        self.assertTrue(any(isinstance(handler, m.NoRedirect) for handler in handlers))
        self.assertTrue(
            any(
                isinstance(handler, m.ProxyHandler) and handler.proxies == {}
                for handler in handlers
            )
        )
        self.assertIsNone(
            m.NoRedirect().redirect_request(
                None, None, 302, "redirect", {}, "https://other.example"
            )
        )

    def test_inventory_missing_duplicate_or_oversized_never_publishes_healthy(self):
        m = self.module()
        with tempfile.TemporaryDirectory() as directory:
            config = m.load_external(self.credential(directory))
        for raw in (
            b'{"data":[]}',
            b'{"data":[{"id":"gpt-5.6-luna"},{"id":"gpt-5.6-luna"}]}',
            b"x" * 1_048_577,
            b'{"data":[{"id":"other"}]}',
        ):
            response = Mock(status=200)
            response.read.return_value = raw
            response.__enter__ = Mock(return_value=response)
            response.__exit__ = Mock(return_value=False)
            opener = Mock()
            opener.open.return_value = response
            with (
                self.subTest(size=len(raw)),
                patch.object(m, "build_opener", return_value=opener),
            ):
                with self.assertRaises(m.ProviderError):
                    m.provider_preflight(config)

    def test_upstream_error_body_and_key_never_escape_boundary(self):
        m = self.module()
        with tempfile.TemporaryDirectory() as directory:
            config = m.load_external(self.credential(directory))
        for error in (
            TimeoutError("test-private-provider-key"),
            OSError("secret upstream body"),
        ):
            opener = Mock()
            opener.open.side_effect = error
            with patch.object(m, "build_opener", return_value=opener):
                with self.assertRaises(m.ProviderError) as caught:
                    m.provider_preflight(config)
                self.assertNotIn("test-private-provider-key", str(caught.exception))
                self.assertNotIn("secret upstream body", str(caught.exception))

    def test_expected_inventory_failures_have_a_distinct_sanitized_type(self):
        from http.client import IncompleteRead
        from urllib.error import HTTPError, URLError

        m = self.module()
        config = m.ExternalModelConfig(
            base_url="https://provider.example/v1", model="selected", api_key="SECRET"
        )
        cases = [
            TimeoutError("SECRET"),
            OSError("SECRET"),
            URLError("SECRET"),
            IncompleteRead(b"SECRET"),
            *(
                HTTPError("SECRET", status, "SECRET", {}, None)
                for status in (302, 403, 429, 503)
            ),
            b"not-json SECRET",
            b"\xff",
            b'{"data":[],"data":[]}',
            b"{}",
            b'{"data":[null]}',
            b'{"data":[]}',
            b'{"data":[{"id":"other"}]}',
            b'{"data":[{"id":"selected"},{"id":"selected"}]}',
            b"x" * (m.MAX_INVENTORY_BYTES + 1),
        ]
        for index, value in enumerate(cases):
            with self.subTest(case=index):
                response = Mock(status=200)
                response.__enter__ = Mock(return_value=response)
                response.__exit__ = Mock(return_value=False)
                response.read.return_value = value
                opener = Mock()
                opener.open.return_value = response
                if isinstance(value, Exception):
                    opener.open.side_effect = value
                with patch.object(m, "build_opener", return_value=opener):
                    with self.assertRaises(m.ProviderObservationError) as caught:
                        m.provider_preflight(config)
                self.assertNotIn("SECRET", str(caught.exception))
                self.assertTrue(caught.exception.__suppress_context__)
                opener.open.assert_called_once()

    def test_http_client_state_error_is_not_a_provider_observation(self):
        from http.client import CannotSendRequest

        m = self.module()
        config = m.ExternalModelConfig(
            base_url="https://provider.example/v1", model="selected", api_key="SECRET"
        )
        error = CannotSendRequest("SECRET local state defect")
        opener = Mock()
        opener.open.side_effect = error
        with (
            patch.object(m, "build_opener", return_value=opener),
            self.assertRaises(CannotSendRequest) as caught,
        ):
            m.provider_preflight(config)
        self.assertIs(caught.exception, error)

    def test_inventory_programming_errors_are_not_observation_failures(self):
        m = self.module()
        config = m.ExternalModelConfig(
            base_url="https://provider.example/v1", model="selected", api_key="SECRET"
        )
        for phase in ("setup", "request", "parse"):
            with self.subTest(phase=phase):
                error = TypeError("SECRET programming defect")
                response = Mock(status=200)
                response.__enter__ = Mock(return_value=response)
                response.__exit__ = Mock(return_value=False)
                response.read.return_value = b'{"data":[{"id":"selected"}]}'
                opener = Mock()
                opener.open.return_value = response
                if phase == "request":
                    opener.open.side_effect = error
                with (
                    patch.object(
                        m,
                        "build_opener",
                        side_effect=error if phase == "setup" else None,
                        return_value=opener,
                    ),
                    patch.object(
                        m.json,
                        "loads",
                        side_effect=error if phase == "parse" else None,
                        return_value={"data": [{"id": "selected"}]},
                    ),
                    self.assertRaises(TypeError) as caught,
                ):
                    m.provider_preflight(config)
                self.assertIs(caught.exception, error)


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
                patch.object(
                    m.runtime, "free_port", side_effect=[4100, 4200, 4300, 4400]
                )
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

            provider = importlib.import_module("model_provider")
            config = provider.ExternalModelConfig(
                base_url="https://provider.example/v1",
                model="gpt-5.6-luna",
                api_key="test-private-provider-key",
            )
            external_directory = Path(temp) / "external"
            external_directory.mkdir()
            credentials = Mock()
            external = m.LocalChatRuntime(
                config=config,
                uv=Path("/uv"),
                node=Path("/node"),
                node_env={"NODE_OPTIONS": "--import=guard"},
                directory=external_directory,
                resources=resources,
                credentials=credentials,
                log=Mock(),
                tenant="tenant",
                agent_redis_url="redis://localhost/10",
            )
            with patch.object(provider, "provider_preflight") as check:
                external.start("postgresql://localhost/owned")
            check.assert_called_once_with(config)
            system_env, http_env, worker_env = [
                call.kwargs["env"] for call in popen.call_args_list[-3:]
            ]
            self.assertEqual(
                worker_env["KOKORO_LITELLM_BASE_URL"], "https://provider.example/v1"
            )
            self.assertEqual(
                worker_env["KOKORO_LITELLM_API_KEY"], "test-private-provider-key"
            )
            self.assertEqual(
                http_env["KOKORO_LITELLM_API_KEY"], "test-private-provider-key"
            )
            self.assertNotIn("test-private-provider-key", str(system_env))
            self.assertEqual(
                m.system.seed_control_plane.call_args.kwargs["provider"],
                "openai-compatible",
            )
            self.assertEqual(
                m.system.seed_control_plane.call_args.kwargs["model_name"],
                "gpt-5.6-luna",
            )
            self.assertNotIn(
                "test-private-provider-key", str(m.system.seed_control_plane.call_args)
            )
            self.assertTrue(
                any(
                    "test-private-provider-key" in call.args
                    for call in credentials.add.call_args_list
                )
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
                    events.append(k) or health_receipt(k["body"])
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


class TickDiagnosticTests(unittest.TestCase):
    def runtime(self):
        import io

        m = importlib.import_module("local_chat_runtime")
        obj = m.LocalChatRuntime.__new__(m.LocalChatRuntime)
        obj.processes = [("worker", Mock())]
        obj.processes[0][1].poll.return_value = None
        obj.next_refresh, obj.config = 0, object()
        obj.ownership = SimpleNamespace(url="redis://local/10", marker="SECRET_MARKER")
        obj.resources = Mock(
            redis_url="redis://local/0",
            redis_prefix="SECRET_PREFIX",
            run_id="SECRET_RUN",
        )
        obj.resources.command.return_value = "1"
        obj.system_base, obj._token, obj.health_generation = (
            "http://local",
            "SECRET_TOKEN",
            "1",
        )
        obj.route = {"provider_id": "provider"}
        obj.log = io.BytesIO()
        return m, obj

    def test_each_failure_stage_logs_only_fixed_label_and_preserves_original(self):
        stages = [
            "process",
            "provider",
            "agent_ownership",
            "application_ownership",
            "health_request",
            "health_receipt",
        ]
        for stage in stages:
            with self.subTest(stage=stage):
                m, obj = self.runtime()
                events = []

                def no_render(_self):
                    raise AssertionError("exception must not be rendered")

                error = type(
                    "SECRET_DYNAMIC_CLASS", (Exception,), {"__str__": no_render}
                )("SECRET_KEY PASSWORD BODY URL?SECRET")

                def visit(name, value):
                    events.append(name)
                    if name == stage:
                        raise error
                    return value

                renewals = iter(["agent_ownership", "application_ownership"])
                obj.processes[0][1].poll.side_effect = lambda: visit("process", None)
                obj.resources.command.side_effect = lambda *_: visit(
                    next(renewals), "1"
                )
                with (
                    patch.object(
                        m,
                        "provider_preflight",
                        side_effect=lambda *_: visit("provider", None),
                    ),
                    patch.object(
                        m.system,
                        "http_json",
                        side_effect=lambda *a, **k: visit("health_request", {}),
                    ),
                    patch.object(
                        m.system,
                        "data_of",
                        side_effect=lambda *_: visit("health_receipt", {}),
                    ),
                    self.assertRaises(Exception) as raised,
                ):
                    obj.tick()
                self.assertIs(raised.exception, error)
                self.assertEqual(events, stages[: stages.index(stage) + 1])
                self.assertEqual(
                    obj.log.getvalue(),
                    f"Local Chat tick failed: stage={stage}\n".encode(),
                )
                self.assertEqual(obj.health_generation, "1")
                self.assertEqual(obj.next_refresh, 0)

    def test_existing_guard_rejections_have_stage_without_weakening_checks(self):
        cases = [
            ("process", "process"),
            ("agent_ownership", "agent_ownership"),
            ("application_ownership", "application_ownership"),
            ("wrong_provider", "health_receipt"),
            ("invalid_generation", "health_receipt"),
        ]
        for failure, stage in cases:
            with self.subTest(failure=failure):
                m, obj = self.runtime()
                if failure == "process":
                    obj.processes[0][1].poll.return_value = 1
                if failure == "agent_ownership":
                    obj.resources.command.side_effect = ["0"]
                if failure == "application_ownership":
                    obj.resources.command.side_effect = ["1", "0"]
                result = {
                    "provider_id": "other"
                    if failure == "wrong_provider"
                    else "provider",
                    "generation": "0" if failure == "invalid_generation" else "2",
                }
                with (
                    patch.object(m, "provider_preflight") as provider,
                    patch.object(
                        m.system,
                        "http_json",
                        side_effect=lambda *a, **k: {
                            "data": {**health_receipt(k["body"])["data"], **result}
                        },
                    ) as http,
                    self.assertRaises(m.ChatError),
                ):
                    obj.tick()
                self.assertEqual(
                    obj.log.getvalue(),
                    f"Local Chat tick failed: stage={stage}\n".encode(),
                )
                self.assertEqual(obj.next_refresh, 0)
                self.assertEqual(obj.health_generation, "1")
                if failure == "process":
                    provider.assert_not_called()
                    obj.resources.command.assert_not_called()
                if stage != "health_receipt":
                    http.assert_not_called()

    def test_missing_or_broken_log_never_replaces_original_failure(self):
        for failure in ("missing", "write", "flush"):
            with self.subTest(log=failure):
                m, obj = self.runtime()
                if failure == "missing":
                    del obj.log
                else:
                    obj.log = Mock()
                    getattr(obj.log, failure).side_effect = OSError("SECRET_LOG_ERROR")
                error = m.ChatError("SECRET_ORIGINAL_ERROR")
                with (
                    patch.object(m, "provider_preflight", side_effect=error),
                    self.assertRaises(m.ChatError) as raised,
                ):
                    obj.tick()
                self.assertIs(raised.exception, error)

    def test_success_and_not_due_ticks_do_not_log_or_change_frequency(self):
        m, obj = self.runtime()
        with (
            patch.object(m, "provider_preflight") as provider,
            patch.object(
                m.system,
                "http_json",
                side_effect=lambda *a, **k: health_receipt(k["body"]),
            ) as http,
            patch.object(m.time, "monotonic", return_value=100),
        ):
            obj.tick()
            self.assertEqual(obj.next_refresh, 160)
            self.assertEqual(obj.health_generation, "2")
            self.assertEqual(obj.resources.command.call_count, 2)
            self.assertEqual(http.call_args.kwargs["headers"]["if-match"], '"1"')
            obj.tick()
            provider.assert_called_once()
            http.assert_called_once()
            self.assertEqual(obj.resources.command.call_count, 2)
        self.assertEqual(obj.log.getvalue(), b"")

    def test_external_observation_unknown_then_healthy_preserves_cas_and_interval(self):
        m, obj = self.runtime()
        obj.config = m.model_provider.ExternalModelConfig(
            base_url="https://provider.example/v1", model="selected", api_key="SECRET"
        )

        def no_render(_self):
            raise AssertionError("observation exception must not be rendered")

        error = type(
            "SECRET_DYNAMIC_CLASS",
            (m.model_provider.ProviderObservationError,),
            {"__str__": no_render},
        )("SECRET body")
        generations = iter(("2", "3"))
        with (
            patch.object(
                m.model_provider, "provider_preflight", side_effect=[error, None]
            ) as probe,
            patch.object(
                m.system,
                "http_json",
                side_effect=lambda *a, **k: health_receipt(
                    k["body"], next(generations)
                ),
            ) as http,
            patch.object(m.time, "monotonic", return_value=100) as clock,
        ):
            obj.tick()
            self.assertEqual(http.call_args.kwargs["body"]["status"], "unknown")
            self.assertEqual(http.call_args.kwargs["headers"]["if-match"], '"1"')
            self.assertEqual(obj.resources.command.call_count, 2)
            self.assertEqual(obj.health_generation, "2")
            self.assertEqual(obj.next_refresh, 160)
            obj.tick()
            probe.assert_called_once()
            http.assert_called_once()
            self.assertEqual(obj.resources.command.call_count, 2)
            clock.return_value = 160
            obj.tick()
            self.assertEqual(http.call_args.kwargs["body"]["status"], "healthy")
            self.assertEqual(http.call_args.kwargs["headers"]["if-match"], '"2"')
            self.assertEqual(obj.resources.command.call_count, 4)
            self.assertEqual(obj.health_generation, "3")
            self.assertEqual(obj.next_refresh, 220)
        self.assertEqual(
            obj.log.getvalue(),
            b"Local Chat provider observation unavailable; health=unknown\n",
        )

    def test_unknown_observation_does_not_hide_ownership_http_or_receipt_failure(self):
        for stage in (
            "agent_ownership",
            "application_ownership",
            "health_request",
            "health_receipt",
        ):
            with self.subTest(stage=stage):
                m, obj = self.runtime()
                if stage == "agent_ownership":
                    obj.resources.command.side_effect = ["0"]
                elif stage == "application_ownership":
                    obj.resources.command.side_effect = ["1", "0"]
                error = m.ChatError("SECRET CAS or transport")
                with (
                    patch.object(
                        m,
                        "provider_preflight",
                        side_effect=m.model_provider.ProviderObservationError("SECRET"),
                    ),
                    patch.object(
                        m.system,
                        "http_json",
                        side_effect=error if stage == "health_request" else None,
                        return_value={
                            "data": {"provider_id": "wrong", "generation": "0"}
                        },
                    ) as http,
                    self.assertRaises(m.ChatError),
                ):
                    obj.tick()
                if stage.endswith("ownership"):
                    http.assert_not_called()
                self.assertEqual(obj.health_generation, "1")
                self.assertEqual(obj.next_refresh, 0)
                self.assertTrue(
                    obj.log.getvalue().endswith(
                        f"Local Chat tick failed: stage={stage}\n".encode()
                    )
                )
                self.assertNotIn(b"SECRET", obj.log.getvalue())

    def test_observation_log_failure_is_safe_and_generic_errors_still_fatal(self):
        for log_failure in ("missing", "write", "flush"):
            with self.subTest(log=log_failure):
                m, obj = self.runtime()
                if log_failure == "missing":
                    del obj.log
                else:
                    obj.log = Mock()
                    getattr(obj.log, log_failure).side_effect = OSError("SECRET")
                with (
                    patch.object(
                        m,
                        "provider_preflight",
                        side_effect=m.model_provider.ProviderObservationError("SECRET"),
                    ),
                    patch.object(
                        m.system,
                        "http_json",
                        side_effect=lambda *a, **k: health_receipt(k["body"]),
                    ),
                ):
                    obj.tick()
                self.assertEqual(obj.health_generation, "2")
        m, obj = self.runtime()
        for error in (
            TypeError("SECRET"),
            m.ChatError("SECRET"),
            m.model_provider.ProviderError("SECRET"),
        ):
            with (
                self.subTest(error=type(error)),
                patch.object(m, "provider_preflight", side_effect=error),
                patch.object(m.system, "http_json") as http,
                self.assertRaises(type(error)) as caught,
            ):
                obj.tick()
            self.assertIs(caught.exception, error)
            obj.resources.command.assert_not_called()
            http.assert_not_called()

    def test_external_wrapper_preserves_observation_type_but_startup_still_raises(self):
        m, _ = self.runtime()
        config = m.model_provider.ExternalModelConfig(
            base_url="https://provider.example/v1", model="selected", api_key="SECRET"
        )
        error = m.model_provider.ProviderObservationError("sanitized")
        with (
            patch.object(m.model_provider, "provider_preflight", side_effect=error),
            patch.object(m.runtime, "command_output", return_value="a" * 40),
            patch.object(m.owned, "_verify_source"),
            patch.object(m.runtime, "run_owned_command") as command,
            self.assertRaises(m.model_provider.ProviderObservationError) as caught,
        ):
            m.preflight(Path("/unused/uv"), "unused", "unused", Mock(), config)
        self.assertIs(caught.exception, error)
        command.assert_not_called()

    def test_second_startup_observation_failure_never_seeds_health_or_agent(self):
        m, obj = self.runtime()
        obj.config = m.model_provider.ExternalModelConfig(
            base_url="https://provider.example/v1", model="selected", api_key="SECRET"
        )
        obj.node_env, obj.node, obj.directory, obj.tenant = (
            {},
            Path("/unused/node"),
            Path("/unused"),
            "tenant",
        )
        obj.ownership = Mock()
        error = m.model_provider.ProviderObservationError("sanitized")
        with (
            patch.object(
                m.owned, "_isolated_owner", return_value=Path("/unused/system")
            ),
            patch.object(m.runtime, "free_port", return_value=4100),
            patch.object(obj, "_command") as command,
            patch.object(obj, "_start") as start,
            patch.object(m.system, "wait_ready"),
            patch.object(m.model_provider, "provider_preflight", side_effect=error),
            patch.object(m.system, "seed_control_plane") as seed,
            self.assertRaises(m.model_provider.ProviderObservationError) as caught,
        ):
            obj.start("postgresql://unused")
        self.assertIs(caught.exception, error)
        seed.assert_not_called()
        start.assert_called_once()
        self.assertEqual(start.call_args.args[0], "system")
        self.assertEqual(command.call_count, 2)

    def test_health_receipt_must_confirm_sent_status_and_exact_utc_observation(self):
        cases = (
            "wrong_status",
            "missing_status",
            "wrong_time",
            "missing_time",
            "invalid_time",
            "naive_time",
            "non_millisecond_time",
            "non_utc_time",
        )
        for status in ("healthy", "unknown"):
            for failure in cases:
                with self.subTest(status=status, failure=failure):
                    m, obj = self.runtime()

                    def reply(*_args, **kwargs):
                        result = {
                            **kwargs["body"],
                            "provider_id": "provider",
                            "generation": "2",
                            "updated_at": kwargs["body"]["observed_at"],
                        }
                        if failure == "wrong_status":
                            result["status"] = (
                                "healthy" if status == "unknown" else "unknown"
                            )
                        elif failure == "missing_status":
                            del result["status"]
                        elif failure == "missing_time":
                            del result["observed_at"]
                        else:
                            result["observed_at"] = {
                                "wrong_time": "2000-01-01T00:00:00.000Z",
                                "invalid_time": "2026-99-99T25:99:99.999Z",
                                "naive_time": kwargs["body"]["observed_at"][:-1],
                                "non_millisecond_time": kwargs["body"]["observed_at"][
                                    :-1
                                ]
                                + "000Z",
                                "non_utc_time": kwargs["body"]["observed_at"][:-1]
                                + "+01:00",
                            }[failure]
                        return {"data": result}

                    with (
                        patch.object(
                            m,
                            "provider_preflight",
                            side_effect=(
                                m.model_provider.ProviderObservationError("sanitized")
                                if status == "unknown"
                                else None
                            ),
                        ),
                        patch.object(m.system, "http_json", side_effect=reply) as http,
                    ):
                        with self.assertRaises(m.ChatError):
                            obj.tick()
                        self.assertEqual(obj.health_generation, "1")
                        self.assertEqual(obj.next_refresh, 0)
                        self.assertEqual(obj.resources.command.call_count, 2)
                        http.assert_called_once()
                        self.assertTrue(
                            obj.log.getvalue().endswith(
                                b"Local Chat tick failed: stage=health_receipt\n"
                            )
                        )
