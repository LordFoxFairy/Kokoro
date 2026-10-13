"""Focused guards for the local, real three-owner login launcher."""

import importlib.util
import os
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import signal
import socket
import subprocess
import sys
import tempfile
from threading import Thread
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/dev/serve_local_login.py"
sys.path.insert(0, str(ROOT / "scripts/e2e"))
spec = importlib.util.spec_from_file_location("serve_local_login", SCRIPT)
launcher = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = launcher
spec.loader.exec_module(launcher)


class LocalLoginGuards(unittest.TestCase):
    def test_platform_is_explicit_and_requires_storage(self):
        argv = [
            "--iam-node-bin",
            "/bin/echo",
            "--bff-node-bin",
            "/bin/echo",
            "--web-node-bin",
            "/bin/echo",
            "--platform-node-bin",
            "/bin/echo",
        ]
        with patch.dict(
            "os.environ",
            {
                "KOKORO_LOCAL_POSTGRES_URL": "postgresql://user@127.0.0.1/postgres",
                "KOKORO_LOCAL_REDIS_URL": "redis://127.0.0.1:6379/0",
            },
            clear=True,
        ):
            with self.assertRaises(SystemExit):
                launcher.parse_args(argv)

    def test_explicit_web_port_controls_origin_and_isolated_server(self):
        self.assertEqual(
            launcher.web_origin("ignored", 43110), "http://127.0.0.1:43110"
        )

    def test_storage_profile_projects_only_public_origin_to_web(self):
        self.assertEqual(
            launcher.web_local_upload_origin(
                {
                    "KOKORO_OBJECT_STORE_PUBLIC_ENDPOINT": (
                        "http://127.0.0.1:39190/object-prefix"
                    ),
                    "KOKORO_OBJECT_STORE_ACCESS_KEY_ID": "must-not-project",
                }
            ),
            "http://127.0.0.1:39190",
        )
        for value in (
            "https://user:secret@127.0.0.1:39190/path",
            "http://object.example.test:39190/path",
            "http://127.0.0.1:39190/path?secret=value",
        ):
            with self.subTest(value=value), self.assertRaises(launcher.LaunchError):
                launcher.web_local_upload_origin(
                    {"KOKORO_OBJECT_STORE_PUBLIC_ENDPOINT": value}
                )
        source = "const app = next({ port: 443 })"
        self.assertEqual(
            launcher.local_next_server(source, 43110),
            "const app = next({ port: 43110 })",
        )

    def test_platform_composition_uses_current_platform_names_only(self):
        source = SCRIPT.read_text()
        platform_source = (ROOT / "scripts/dev/local_platform_runtime.py").read_text()
        self.assertIn('"IAM_TEST_SKILL_SANDBOX_MODE"', source)
        self.assertIn('"KOKORO_PLATFORM_BASE_URL"', platform_source)
        self.assertIn(
            '"KOKORO_PLATFORM_SURFACES": "skill-catalog,skill-source,skill-installation-product"',
            platform_source,
        )
        self.assertIn(
            '"KOKORO_SKILL_DRAFT_CANDIDATE_ENABLED": "true"', platform_source
        )
        self.assertNotIn("KOKORO_CAPABILITY", source + platform_source)

    def test_default_ready_path_does_not_strip_unrequested_sandbox_fields(self):
        import ast

        tree = ast.parse(SCRIPT.read_text())
        guards = [
            node.test
            for node in ast.walk(tree)
            if isinstance(node, ast.If)
            and any(
                isinstance(child, ast.Constant)
                and child.value == "skill_sandbox"
                for child in ast.walk(node.test)
            )
        ]
        self.assertEqual(len(guards), 1)
        names = {
            child.id for child in ast.walk(guards[0]) if isinstance(child, ast.Name)
        }
        self.assertIn("platform_env", names)

    def test_platform_cleanup_preserves_credentials_after_stop_failure(self):
        from unittest.mock import Mock

        registry = Mock()
        owned = launcher.platform_runtime.LocalPlatformRuntime(
            node=Path(sys.executable),
            node_environment={},
            directory=Path(tempfile.gettempdir()),
            credentials=registry,
            log=None,
        )
        owned.process = SimpleNamespace(poll=lambda: 1)
        owned.quiescent = False
        owned._files = Mock()
        with patch.object(
            launcher.platform_runtime.runtime,
            "stop_owned_process",
            side_effect=RuntimeError("stop failed"),
        ):
            self.assertEqual(
                owned.close(),
                [
                    "Platform process cleanup",
                    "Platform credentials preserved for active process",
                ],
            )
        owned._files.close.assert_not_called()
        self.assertFalse(owned.quiescent)

    def test_cleanup_uses_product_session_aware_redis_inventory(self):
        import ast

        tree = ast.parse(SCRIPT.read_text())
        calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "web_redis_keys"
        ]
        self.assertEqual(len(calls), 3)
        self.assertTrue(
            all(
                isinstance(call.func.value, ast.Name)
                and call.func.value.id == "product_session"
                for call in calls
            )
        )

    def wait_for_process_exit(self, pid: int, timeout: float = 5.0) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            result = subprocess.run(
                ["ps", "-o", "stat=", "-p", str(pid)],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0 or result.stdout.strip().startswith("Z"):
                return True
            time.sleep(0.05)
        return False

    def test_launcher_requests_fixed_product_web_trusted_policy(self):
        """Source guard only; actual IAM and browser acceptance are separate."""
        import ast

        tree = ast.parse(SCRIPT.read_text())
        values = [
            value
            for node in ast.walk(tree)
            if isinstance(node, ast.Dict)
            for key, value in zip(node.keys, node.values)
            if isinstance(key, ast.Constant)
            and key.value == "IAM_TEST_PRODUCT_WEB_TRUSTED_POLICY"
        ]
        self.assertEqual(len(values), 1)
        self.assertIsInstance(values[0], ast.Constant)
        self.assertEqual(values[0].value, "1")

    def test_node_parent_guard_does_not_keep_normal_process_alive(self):
        with tempfile.TemporaryDirectory(prefix="node guard with spaces ") as directory:
            environment = os.environ.copy()
            launcher.install_node_parent_guard(Path(directory), environment)
            completed = subprocess.run(
                ["node", "-e", "process.stdout.write('normal-exit')"],
                env=environment,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(completed.stdout, "normal-exit")
        self.assertEqual(completed.stderr, "")

    def test_node_parent_guard_stops_child_after_hard_parent_exit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            environment = os.environ.copy()
            launcher.install_node_parent_guard(root, environment)
            pid_file = root / "child.pid"
            parent = subprocess.Popen(
                [
                    sys.executable,
                    "-c",
                    (
                        "import pathlib, subprocess, sys, time; "
                        "child=subprocess.Popen(['node','-e','setInterval(()=>{}, 1000)']); "
                        "pathlib.Path(sys.argv[1]).write_text(str(child.pid)); "
                        "time.sleep(30)"
                    ),
                    str(pid_file),
                ],
                env=environment,
                start_new_session=True,
            )
            child_pid = 0
            try:
                deadline = time.monotonic() + 5
                while time.monotonic() < deadline and not pid_file.exists():
                    time.sleep(0.05)
                self.assertTrue(pid_file.exists())
                child_pid = int(pid_file.read_text())
                os.kill(parent.pid, signal.SIGKILL)
                parent.wait(timeout=5)
                self.assertTrue(self.wait_for_process_exit(child_pid))
            finally:
                if parent.poll() is None:
                    os.kill(parent.pid, signal.SIGKILL)
                    parent.wait(timeout=5)
                if child_pid and not self.wait_for_process_exit(child_pid, 0.1):
                    os.kill(child_pid, signal.SIGKILL)

    def test_node_parent_guard_force_kills_child_that_ignores_sigterm(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            environment = os.environ.copy()
            launcher.install_node_parent_guard(root, environment)
            pid_file = root / "child.pid"
            ready_file = root / "child.ready"
            node_script = (
                "process.on('SIGTERM',()=>{});"
                "require('node:fs').writeFileSync(process.argv[1],'ready');"
                "setInterval(()=>{},1000);"
            )
            parent = subprocess.Popen(
                [
                    sys.executable,
                    "-c",
                    (
                        "import pathlib, subprocess, sys, time; "
                        "child=subprocess.Popen(['node','-e',sys.argv[2],sys.argv[3]]); "
                        "pathlib.Path(sys.argv[1]).write_text(str(child.pid)); "
                        "time.sleep(30)"
                    ),
                    str(pid_file),
                    node_script,
                    str(ready_file),
                ],
                env=environment,
                start_new_session=True,
            )
            child_pid = 0
            try:
                deadline = time.monotonic() + 5
                while time.monotonic() < deadline and not (
                    pid_file.exists() and ready_file.exists()
                ):
                    time.sleep(0.05)
                self.assertTrue(pid_file.exists())
                self.assertTrue(ready_file.exists())
                child_pid = int(pid_file.read_text())
                os.kill(parent.pid, signal.SIGKILL)
                parent.wait(timeout=5)
                self.assertTrue(self.wait_for_process_exit(child_pid, 7))
            finally:
                if parent.poll() is None:
                    os.kill(parent.pid, signal.SIGKILL)
                    parent.wait(timeout=5)
                if child_pid and not self.wait_for_process_exit(child_pid, 0.1):
                    os.kill(child_pid, signal.SIGKILL)

    def test_node_parent_guard_stops_child_after_normal_parent_exit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            environment = os.environ.copy()
            launcher.install_node_parent_guard(root, environment)
            pid_file = root / "child.pid"
            parent = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    (
                        "import pathlib, subprocess, sys; "
                        "child=subprocess.Popen(['node','-e','setInterval(()=>{}, 1000)']); "
                        "pathlib.Path(sys.argv[1]).write_text(str(child.pid))"
                    ),
                    str(pid_file),
                ],
                env=environment,
                start_new_session=True,
                timeout=5,
                check=False,
            )
            self.assertEqual(parent.returncode, 0)
            self.assertTrue(pid_file.exists())
            child_pid = int(pid_file.read_text())
            try:
                self.assertTrue(self.wait_for_process_exit(child_pid))
            finally:
                if not self.wait_for_process_exit(child_pid, 0.1):
                    os.kill(child_pid, signal.SIGKILL)

    def test_inherited_guard_tracks_each_node_actual_parent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            environment = os.environ.copy()
            launcher.install_node_parent_guard(root, environment)
            pid_file = root / "grandchild.pid"
            script = (
                "const {spawn}=require('node:child_process');"
                "const fs=require('node:fs');"
                "const child=spawn(process.execPath,['-e','setInterval(()=>{},1000)'],{stdio:'ignore'});"
                "fs.writeFileSync(process.argv[1],String(child.pid));"
                "setInterval(()=>{},1000);"
            )
            parent = subprocess.Popen(
                ["node", "-e", script, str(pid_file)],
                env=environment,
                start_new_session=True,
            )
            child_pid = 0
            try:
                deadline = time.monotonic() + 5
                while time.monotonic() < deadline and not pid_file.exists():
                    time.sleep(0.05)
                self.assertTrue(pid_file.exists())
                child_pid = int(pid_file.read_text())
                self.assertFalse(self.wait_for_process_exit(child_pid, 0.35))
                os.kill(parent.pid, signal.SIGKILL)
                parent.wait(timeout=5)
                self.assertTrue(self.wait_for_process_exit(child_pid))
            finally:
                if parent.poll() is None:
                    os.kill(parent.pid, signal.SIGKILL)
                    parent.wait(timeout=5)
                if child_pid and not self.wait_for_process_exit(child_pid, 0.1):
                    os.kill(child_pid, signal.SIGKILL)

    def test_process_death_fails_the_owned_stack_monitor(self):
        running = SimpleNamespace(poll=lambda: None)
        exited = SimpleNamespace(poll=lambda: 1)
        launcher.require_owned_stack_alive([running])
        with self.assertRaisesRegex(launcher.LaunchError, "owned service exited"):
            launcher.require_owned_stack_alive([running, exited])

    def test_next_normalized_origin_is_not_used_as_browser_authority(self):
        origin = "http://127.0.0.1:3310"
        self.assertTrue(
            launcher.fixture_origin_matches(
                {
                    "origin": "http://localhost:3310",
                    "host": "127.0.0.1:3310",
                    "proto": "http",
                },
                origin,
            )
        )
        self.assertFalse(
            launcher.fixture_origin_matches(
                {
                    "origin": "http://localhost:3310",
                    "host": "localhost:3310",
                    "proto": "http",
                },
                origin,
            )
        )

    def test_origin_is_the_visible_http_loopback_on_local_port(self):
        self.assertEqual(
            launcher.web_origin("a" * 24),
            "http://127.0.0.1:3310",
        )
        self.assertEqual(launcher.WEB_PORT, 3310)

    def test_occupied_port_is_not_reused_or_terminated(self):
        with socket.socket() as occupied:
            occupied.bind(("127.0.0.1", 0))
            occupied.listen()
            port = occupied.getsockname()[1]
            with patch.object(launcher, "WEB_PORT", port):
                with self.assertRaises(launcher.LaunchError):
                    launcher.require_free_web_port()
            self.assertEqual(occupied.getsockname()[1], port)

    def test_next_copy_is_adjusted_only_in_temp_directory(self):
        original = "const app = next({ dev: true, dir: __dirname, hostname: host, port: 443 })\n"
        self.assertEqual(
            launcher.local_next_server(original),
            original.replace("port: 443", "port: 3310"),
        )
        with self.assertRaises(launcher.LaunchError):
            launcher.local_next_server("unexpected Next server template")

    def test_plain_http_transport_preserves_form_navigation_and_cookies(self):
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(302)
                self.send_header("Location", "/iam/oauth2/authorize?state=abc")
                self.send_header("Set-Cookie", "next-auth.state=abc; Path=/")
                self.end_headers()

            def log_message(self, *_args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = Thread(target=server.serve_forever)
        thread.start()
        try:
            port = server.server_address[1]
            response = launcher.http_browser(port, "/login", f"http://127.0.0.1:{port}")
            self.assertEqual(response.status, 302)
            self.assertEqual(response.location(), "/iam/oauth2/authorize?state=abc")
            self.assertEqual(response.set_cookies, ["next-auth.state=abc; Path=/"])
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_database_endpoints_are_read_from_environment_without_password(self):
        paths = {
            "--iam-node-bin": "/bin/echo",
            "--bff-node-bin": "/bin/echo",
            "--web-node-bin": "/bin/echo",
        }
        argv = [item for pair in paths.items() for item in pair]
        with patch.dict(
            "os.environ",
            {
                "KOKORO_LOCAL_POSTGRES_URL": "postgresql://user@127.0.0.1/postgres",
                "KOKORO_LOCAL_REDIS_URL": "redis://127.0.0.1:6379/0",
            },
        ):
            args = launcher.parse_args(argv)
            self.assertEqual(
                args.postgres_admin_url, "postgresql://user@127.0.0.1/postgres"
            )
            self.assertEqual(args.redis_url, "redis://127.0.0.1:6379/0")
        with patch.dict(
            "os.environ",
            {
                "KOKORO_LOCAL_POSTGRES_URL": "postgresql://user:secret@127.0.0.1/postgres",
                "KOKORO_LOCAL_REDIS_URL": "redis://127.0.0.1:6379/0",
            },
        ):
            with self.assertRaises(SystemExit):
                launcher.parse_args(argv)


if __name__ == "__main__":
    unittest.main()


class ExplicitChatOptions(unittest.TestCase):
    def test_external_model_private_file_is_explicit_and_exclusive(self):
        import contextlib
        import io
        import json

        with tempfile.TemporaryDirectory() as directory:
            credential = Path(directory) / "provider.json"
            credential.write_text(
                json.dumps(
                    {
                        "base_url": "https://provider.example/v1",
                        "model": "gpt-5.6-luna",
                        "api_key": "test-private-provider-key",
                    }
                )
            )
            credential.chmod(0o600)
            argv = [
                "--iam-node-bin",
                "/bin/echo",
                "--bff-node-bin",
                "/bin/echo",
                "--web-node-bin",
                "/bin/echo",
                "--chat",
                "--uv-bin",
                "/bin/echo",
                "--agent-redis-url",
                "redis://127.0.0.1:6379/10",
                "--external-model-credential-file",
                str(credential),
            ]
            with patch.dict(
                os.environ,
                {
                    "KOKORO_LOCAL_POSTGRES_URL": "postgresql://localhost/postgres",
                    "KOKORO_LOCAL_REDIS_URL": "redis://127.0.0.1:6379/0",
                },
            ):
                args = launcher.parse_args(argv)
                self.assertEqual(args.external_model.model, "gpt-5.6-luna")
                for extra in (
                    ["--model-origin", "http://127.0.0.1:11434"],
                    ["--model", "qwen3:8b"],
                ):
                    with (
                        self.subTest(extra=extra),
                        self.assertRaises(SystemExit),
                        contextlib.redirect_stderr(io.StringIO()),
                    ):
                        launcher.parse_args(argv + extra)
                without_chat = [arg for arg in argv if arg != "--chat"]
                with (
                    self.assertRaises(SystemExit),
                    contextlib.redirect_stderr(io.StringIO()),
                ):
                    launcher.parse_args(without_chat)
                credential.chmod(0o644)
                output = io.StringIO()
                with self.assertRaises(SystemExit), contextlib.redirect_stderr(output):
                    launcher.parse_args(argv)
                self.assertNotIn("test-private-provider-key", output.getvalue())

    def test_default_is_login_only_even_with_inherited_agent_configuration(self):
        argv = [
            "--iam-node-bin",
            "/bin/echo",
            "--bff-node-bin",
            "/bin/echo",
            "--web-node-bin",
            "/bin/echo",
        ]
        with patch.dict(
            os.environ,
            {
                "KOKORO_LOCAL_POSTGRES_URL": "postgresql://user@127.0.0.1/postgres",
                "KOKORO_LOCAL_REDIS_URL": "redis://127.0.0.1:6379/0",
                "KOKORO_AGENT_ENABLED": "true",
            },
        ):
            args = launcher.parse_args(argv)
        self.assertFalse(args.chat)
        self.assertEqual(args.agent_redis_url, "")

    def test_chat_missing_resources_does_not_fall_back_to_login(self):
        argv = [
            "--iam-node-bin",
            "/bin/echo",
            "--bff-node-bin",
            "/bin/echo",
            "--web-node-bin",
            "/bin/echo",
            "--chat",
        ]
        with patch.dict(
            os.environ,
            {
                "KOKORO_LOCAL_POSTGRES_URL": "postgresql://user@127.0.0.1/postgres",
                "KOKORO_LOCAL_REDIS_URL": "redis://127.0.0.1:6379/0",
            },
        ):
            with self.assertRaises(SystemExit):
                launcher.parse_args(argv)
            args = launcher.parse_args(
                argv
                + [
                    "--agent-redis-url",
                    "redis://127.0.0.1:6379/10",
                    "--uv-bin",
                    "/bin/echo",
                ]
            )
        self.assertTrue(args.chat)


class FailedShutdownRedisTests(unittest.TestCase):
    def test_failed_owned_process_stop_preserves_web_sessions(self):
        from contextlib import ExitStack
        from unittest.mock import Mock

        args = SimpleNamespace(
            chat=False,
            postgres_admin_url="postgresql://local/postgres",
            redis_url="redis://local/0",
            iam_node_bin=Path("/node24"),
            bff_node_bin=Path("/node22"),
            web_node_bin=Path("/node22"),
        )
        resources = Mock()
        resources.command.return_value = "PONG"
        resources.create_database.return_value = "postgresql://local/owned"
        ready = SimpleNamespace(
            database_name="owned-iam",
            redis_prefix="own-iam:",
            client_secret="secret-iam",
            password="password-iam",
            base_url="http://local/iam",
            issuer_url="http://local/issuer",
            redirect_uri="http://local/callback",
            post_logout_redirect_uri="http://local/logout",
            tenant_id="tenant",
        )
        process = Mock()
        process.poll.return_value = None
        signals = {
            sig: signal.getsignal(sig)
            for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)
        }
        with tempfile.TemporaryDirectory() as directory, ExitStack() as patches:
            _r57_login_git_inputs(patches, directory)
            patches.enter_context(
                patch.object(launcher, "parse_args", return_value=args)
            )
            patches.enter_context(patch.object(launcher, "require_free_web_port"))
            # Keep the launcher's evidence within this test-owned temporary tree.
            from contextlib import nullcontext

            patches.enter_context(
                patch.object(
                    launcher.tempfile,
                    "TemporaryDirectory",
                    return_value=nullcontext(directory),
                )
            )
            patches.enter_context(
                patch.object(launcher.runtime, "OwnedResources", return_value=resources)
            )
            patches.enter_context(
                patch.object(launcher.session, "node_environment", return_value={})
            )
            patches.enter_context(
                patch.object(launcher.runtime, "run_owned_command", return_value=0)
            )
            patches.enter_context(patch.object(launcher.runtime, "install_schema"))
            patches.enter_context(
                patch.object(
                    launcher.web_smoke, "named_iam_identity", return_value=ready
                )
            )
            patches.enter_context(
                patch.object(
                    launcher.web_smoke,
                    "iam_owned_inventory",
                    side_effect=[(set(), set()), ({"owned-iam"}, set())],
                )
            )
            patches.enter_context(
                patch.object(launcher.web_smoke, "validate_ready", return_value=ready)
            )
            patches.enter_context(
                patch.object(
                    launcher.product_session,
                    "web_redis_keys",
                    side_effect=[set(), {"owned-session"}, set()],
                )
            )
            patches.enter_context(patch.object(launcher.session, "ProtocolReader"))
            patches.enter_context(
                patch.object(launcher.subprocess, "Popen", return_value=process)
            )
            patches.enter_context(
                patch.object(launcher.runtime, "start_process", return_value=process)
            )
            patches.enter_context(
                patch.object(
                    launcher.runtime,
                    "wait_ready",
                    side_effect=launcher.LaunchError("startup"),
                )
            )
            patches.enter_context(
                patch.object(
                    launcher.runtime,
                    "stop_owned_process",
                    side_effect=launcher.LaunchError("still active"),
                )
            )
            patches.enter_context(patch.object(launcher.previous, "assert_log_clean"))
            try:
                with self.assertRaises(launcher.LaunchError):
                    launcher.main([])
                self.assertFalse(
                    any(
                        "UNLINK" in call.args[0]
                        for call in resources.command.call_args_list
                    )
                )
                resources.cleanup.assert_not_called()
            finally:
                for sig, handler in signals.items():
                    signal.signal(sig, handler)


class PrivateCredentialFileTests(unittest.TestCase):
    def test_real_private_file_is_exclusive_0600_and_never_logged(self):
        import io
        import json
        import stat
        from contextlib import redirect_stdout, redirect_stderr

        with tempfile.TemporaryDirectory() as directory:
            output, errors = io.StringIO(), io.StringIO()
            old_umask = os.umask(0o022)
            try:
                with redirect_stdout(output), redirect_stderr(errors):
                    path = launcher.write_private_credentials(
                        Path(directory), "local@example.test", "SECRET_SENTINEL"
                    )
            finally:
                os.umask(old_umask)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            self.assertEqual(
                json.loads(path.read_text()),
                {"email": "local@example.test", "password": "SECRET_SENTINEL"},
            )
            self.assertEqual(output.getvalue(), "")
            self.assertEqual(errors.getvalue(), "")

    def test_existing_target_is_not_overwritten_or_chmodded(self):
        import stat

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "login-credentials.json"
            path.write_text("original")
            path.chmod(0o640)
            with self.assertRaises(FileExistsError):
                launcher.write_private_credentials(
                    Path(directory), "other@example.test", "NEW_SECRET"
                )
            self.assertEqual(path.read_text(), "original")
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o640)

    def test_credential_failure_has_dedicated_stage_before_advertising_ready(self):
        import ast

        tree = ast.parse(SCRIPT.read_text())
        main = next(
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "main"
        )
        for node in ast.walk(main):
            if isinstance(node, ast.Try):
                for index, statement in enumerate(node.body):
                    if isinstance(statement, ast.Assign) and any(
                        isinstance(child, ast.Call)
                        and isinstance(child.func, ast.Name)
                        and child.func.id == "write_private_credentials"
                        for child in ast.walk(statement)
                    ):
                        self.assertEqual(
                            ast.literal_eval(node.body[index - 1].value),
                            "private credential setup",
                        )
                        self.assertIn("Local login:", ast.unparse(node.body[index + 1]))
                        return
        self.fail("main must create private credentials in a dedicated stage")


class DirectBffConnectionTests(unittest.TestCase):
    def test_web_environment_uses_real_bff_listener_not_observer(self):
        import ast

        tree = ast.parse(SCRIPT.read_text())
        updates = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "web_env"
            and node.func.attr == "update"
        ]
        self.assertEqual(len(updates), 1)
        settings = updates[0].args[0]
        expression = next(
            value
            for key, value in zip(settings.keys, settings.values)
            if isinstance(key, ast.Constant) and key.value == "KOKORO_BFF_BASE_URL"
        )
        url = eval(
            compile(ast.Expression(expression), str(SCRIPT), "eval"),
            {},
            {"bff_port": 41234, "bff_proxy": SimpleNamespace(server_port=41235)},
        )
        self.assertEqual(url, "http://127.0.0.1:41234")

    def test_launcher_constructs_no_bff_observer_proxy(self):
        import ast

        calls = [
            node
            for node in ast.walk(ast.parse(SCRIPT.read_text()))
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "Proxy"
        ]
        self.assertEqual(calls, [])


class SafeLaunchDiagnosticTests(unittest.TestCase):
    def test_formal_login_category_is_closed_and_preserves_safe_hop(self):
        error = launcher.first_login.FormalLoginNavigationError("authorize", "redirect", 400)
        self.assertEqual(launcher.failure_category(error), "login_navigation_authorize_redirect_400")
        error.hop = "SECRET"
        self.assertEqual(launcher.failure_category(error), "owner_smoke")

    def test_categories_never_render_messages_or_dynamic_class_names(self):
        secret = "KEY_PASSWORD_RAW_MESSAGE_SENTINEL"

        def forbidden_string(_self):
            raise AssertionError("exception rendering is forbidden")

        unknown = type(
            "DYNAMIC_SECRET_CLASS_SENTINEL", (Exception,), {"__str__": forbidden_string}
        )(secret)
        cases = [
            (launcher.LaunchError(secret), "launcher"),
            (launcher.chat_runtime.ChatError(secret), "chat"),
            (launcher.model_provider.ProviderError(secret), "provider"),
            (OSError(secret), "io"),
            (FileNotFoundError(secret), "io"),
            (subprocess.CalledProcessError(1, [secret], output=secret), "subprocess"),
            (subprocess.TimeoutExpired([secret], 1, stderr=secret), "subprocess"),
            (launcher.runtime.SmokeError(secret), "owner_smoke"),
            (launcher.session.SmokeError(secret), "owner_smoke"),
            (launcher.web_smoke.SmokeError(secret), "owner_smoke"),
            (launcher.previous.SmokeError(secret), "owner_smoke"),
            (launcher.first_login.FirstLoginError(secret), "owner_smoke"),
            (unknown, "unexpected"),
        ]
        for error, expected in cases:
            with self.subTest(category=expected):
                self.assertEqual(launcher.failure_category(error), expected)

    def test_serving_stages_keep_fixed_category_and_cleanup_without_secret(self):
        import io
        from contextlib import ExitStack, nullcontext, redirect_stderr, redirect_stdout
        from unittest.mock import Mock

        secret = "KEY_PASSWORD_RAW_MESSAGE_SENTINEL"
        unknown = type("DYNAMIC_SECRET_CLASS_SENTINEL", (Exception,), {})(secret)
        cases = [
            ("stack", launcher.LaunchError(secret), "serving stack guard (launcher)"),
            (
                "chat",
                launcher.chat_runtime.ChatError(secret),
                "serving chat tick (chat)",
            ),
            (
                "chat",
                launcher.model_provider.ProviderError(secret),
                "serving chat tick (provider)",
            ),
            ("wait", OSError(secret), "serving wait (io)"),
            ("wait", unknown, "serving wait (unexpected)"),
        ]
        for operation, error, expected in cases:
            with self.subTest(operation=operation, expected=expected):
                with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
                    _r57_login_git_inputs(stack, directory)
                    args = SimpleNamespace(
                        chat=True,
                        postgres_admin_url="postgresql://local/postgres",
                        redis_url="redis://local/0",
                        agent_redis_url="redis://local/10",
                        iam_node_bin=Path("/node24"),
                        bff_node_bin=Path("/node22"),
                        web_node_bin=Path("/node22"),
                        uv_bin=Path("/uv"),
                        model_origin="http://local",
                        model="fixture",
                    )
                    ready = SimpleNamespace(
                        database_name="owned-iam",
                        redis_prefix="own-iam:",
                        client_secret=secret,
                        password=secret,
                        email="owner@example.test",
                        base_url="http://local/iam",
                        issuer_url="http://local/issuer",
                        redirect_uri="http://local/callback",
                        post_logout_redirect_uri="http://local/logout",
                        tenant_id="tenant",
                        client_id="client",
                    )
                    resources, process, chat = Mock(), Mock(), Mock()
                    resources.command.return_value = "PONG"
                    resources.create_database.return_value = "postgresql://local/owned"
                    process.poll.return_value = None
                    chat.start.return_value = {}
                    chat.close.return_value = []
                    chat.quiescent = True
                    root = Path(directory)
                    (root / "server.cjs").write_text("port: 443")
                    patches = [
                        (launcher, "parse_args", {"return_value": args}),
                        (launcher, "require_free_web_port", {}),
                        (launcher, "wait_for_web", {}),
                        (
                            launcher.tempfile,
                            "TemporaryDirectory",
                            {"return_value": nullcontext(directory)},
                        ),
                        (
                            launcher.runtime,
                            "OwnedResources",
                            {"return_value": resources},
                        ),
                        (launcher.runtime, "run_owned_command", {"return_value": 0}),
                        (launcher.runtime, "install_schema", {}),
                        (launcher.runtime, "free_port", {"return_value": 12345}),
                        (launcher.runtime, "start_process", {"return_value": process}),
                        (launcher.runtime, "wait_ready", {}),
                        (launcher.runtime, "stop_owned_process", {}),
                        (launcher.session, "node_environment", {"return_value": {}}),
                        (launcher.session, "ProtocolReader", {}),
                        (launcher.subprocess, "Popen", {"return_value": process}),
                        (
                            launcher.web_smoke,
                            "named_iam_identity",
                            {"return_value": ready},
                        ),
                        (launcher.web_smoke, "validate_ready", {"return_value": ready}),
                        (
                            launcher.web_smoke,
                            "iam_owned_inventory",
                            {"side_effect": [(set(), set()), ({"owned-iam"}, set())]},
                        ),
                        (
                            launcher.product_session,
                            "web_redis_keys",
                            {"return_value": set()},
                        ),
                        (launcher.web_smoke, "isolated_next", {"return_value": root}),
                        (launcher.web_smoke, "reconcile_iam_identity", {}),
                        (launcher.previous, "assert_log_clean", {}),
                        (launcher.first_login, "probe_formal_login_entry", {}),
                        (launcher.chat_runtime, "preflight", {}),
                        (
                            launcher.chat_runtime,
                            "LocalChatRuntime",
                            {"return_value": chat},
                        ),
                        (launcher.signal, "signal", {}),
                    ]
                    for target, name, kwargs in patches:
                        stack.enter_context(patch.object(target, name, **kwargs))
                    guard = stack.enter_context(
                        patch.object(launcher, "require_owned_stack_alive")
                    )
                    wait = stack.enter_context(patch.object(launcher.time, "sleep"))
                    {"stack": guard, "chat": chat.tick, "wait": wait}[
                        operation
                    ].side_effect = error
                    output = io.StringIO()
                    with redirect_stdout(output), redirect_stderr(output):
                        with self.assertRaises(launcher.LaunchError) as raised:
                            launcher.main([])
                    self.assertEqual(str(raised.exception), expected + " failed")
                    self.assertNotIn(secret, output.getvalue() + str(raised.exception))
                    self.assertNotIn(
                        "DYNAMIC_SECRET_CLASS_SENTINEL",
                        output.getvalue() + str(raised.exception),
                    )
                    resources.cleanup.assert_called_once()
                    chat.close.assert_called_once()
                    self.assertEqual(launcher.runtime.stop_owned_process.call_count, 3)
                    if operation == "stack":
                        chat.tick.assert_not_called()
                    if operation != "wait":
                        wait.assert_not_called()


def _r55_login_source_probe(
    monkeypatch, tmp_path, dirty_owner=None, dirty_status="", *,
    moving_root_head=False, release_trace=None,
):
    from contextlib import nullcontext
    from unittest.mock import Mock

    releases = {
        "kokoro-app": "5f2ab341d5fc5ddee5e08d785dc7aaf391b7e9d8",
        "kokoro-iam": "e3c035b99cf9479ac8357c7d38147f1541dcbcac",
        "kokoro-bff": "759bfe0a8c521946cae31a74b6426f43b063bae1",
    }
    root_sha = "c" * 40
    later_root_sha = "d" * 40
    later_releases = {owner: str(index) * 40 for index, owner in enumerate(releases, 1)}
    live_root_sha = root_sha
    trace = release_trace if release_trace is not None else {}
    trace.update(root_reads=[], gitlinks=[], at_build=None)
    apps = tmp_path / "apps"
    apps.mkdir()
    for owner in releases:
        (apps / owner).mkdir()
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    observed_statuses = []

    def git(command, *, cwd=None, **_kwargs):
        nonlocal live_root_sha
        assert command[0] == "git"
        if command[1:2] == ["-C"]:
            repo, args = Path(command[2]), command[3:]
        else:
            repo, args = Path(cwd), command[1:]
        if repo == tmp_path:
            if args == ["rev-parse", "HEAD"]:
                resolved = live_root_sha
                trace["root_reads"].append(resolved)
                if moving_root_head:
                    live_root_sha = later_root_sha
                return resolved + "\n"
            if len(args) == 2 and args[0] == "rev-parse":
                revision, path = args[1].split(":", 1)
                assert revision in ("HEAD", root_sha, later_root_sha)
                resolved = live_root_sha if revision == "HEAD" else revision
                pins = releases if resolved == root_sha else later_releases
                sha = pins[path.removeprefix("apps/")]
                trace["gitlinks"].append((revision, resolved, path, sha))
                return sha + "\n"
            if args[0] == "ls-tree":
                revision = args[1]
                assert revision in ("HEAD", root_sha, later_root_sha)
                resolved = live_root_sha if revision == "HEAD" else revision
                path = args[-1]
                pins = releases if resolved == root_sha else later_releases
                sha = pins[path.removeprefix("apps/")]
                trace["gitlinks"].append((revision, resolved, path, sha))
                return f"160000 commit {sha}\t{path}\n"
            if args[:3] == ["ls-files", "--stage", "--"]:
                path = args[-1]
                return f"160000 {releases[path.removeprefix('apps/')]} 0\t{path}\n"
        assert repo.parent == apps and repo.name in releases
        if args == ["rev-parse", "HEAD"]:
            return releases[repo.name] + "\n"
        if args[:2] == ["status", "--porcelain"]:
            assert args[2:] in (
                ["--untracked-files=normal"],
                ["--untracked-files=all"],
            )
            status = dirty_status if repo.name == dirty_owner else ""
            observed_statuses.append((repo.name, status))
            return status
        raise AssertionError(f"unexpected source command: {command}")

    args = SimpleNamespace(
        chat=False,
        postgres_admin_url="postgresql://local/owned",
        redis_url="redis://local/8",
        iam_node_bin=Path("/unused/node24/node"),
        bff_node_bin=Path("/unused/node22/node"),
        web_node_bin=Path("/unused/node22/node"),
    )
    for module in (launcher.web_smoke, launcher.session):
        monkeypatch.setattr(module, "ROOT", tmp_path)
    for label, owner in (
        ("WEB", "kokoro-app"), ("IAM", "kokoro-iam"), ("BFF", "kokoro-bff")
    ):
        monkeypatch.setattr(launcher.web_smoke, label, apps / owner)
    monkeypatch.setattr(launcher.runtime, "command_output", git)
    monkeypatch.setattr(launcher, "parse_args", lambda _argv: args)
    monkeypatch.setattr(launcher, "require_free_web_port", Mock())
    monkeypatch.setattr(launcher.session, "node_environment", Mock(return_value={}))
    monkeypatch.setattr(
        launcher.tempfile, "TemporaryDirectory", Mock(return_value=nullcontext(evidence))
    )
    monkeypatch.setattr(launcher.signal, "signal", Mock())
    monkeypatch.setattr(launcher.previous, "assert_log_clean", Mock())
    resources = Mock()
    monkeypatch.setattr(launcher.runtime, "OwnedResources", Mock(return_value=resources))

    def bounded_build(*_args, **_kwargs):
        trace["at_build"] = {
            "root_reads": list(trace["root_reads"]),
            "gitlinks": list(trace["gitlinks"]),
            "statuses": list(observed_statuses),
        }
        return 1

    effects = {
        # A bounded build failure proves the clean control reaches the next stage.
        # It also prevents any real resource or process access on today's RED path.
        "build": Mock(side_effect=bounded_build),
        "infrastructure": resources.command,
        "database": resources.create_database,
        "schema": Mock(),
        "owner_process": Mock(),
        "iam_or_web_process": Mock(),
        "chat_preflight": Mock(),
    }
    for module, name, effect in (
        (launcher.runtime, "run_owned_command", "build"),
        (launcher.runtime, "install_schema", "schema"),
        (launcher.runtime, "start_process", "owner_process"),
        (launcher.subprocess, "Popen", "iam_or_web_process"),
        (launcher.chat_runtime, "preflight", "chat_preflight"),
    ):
        monkeypatch.setattr(module, name, effects[effect])
    error = None
    try:
        launcher.main([])
    except (
        launcher.LaunchError, launcher.session.SmokeError,
        launcher.runtime.SmokeError, launcher.web_smoke.SmokeError,
    ) as caught:
        error = caught
    return error, effects, observed_statuses


def test_r55_login_clean_published_sources_reach_bounded_build(monkeypatch, tmp_path):
    error, effects, _statuses = _r55_login_source_probe(monkeypatch, tmp_path)

    assert isinstance(error, launcher.LaunchError)
    assert "BFF build" in str(error)
    effects["build"].assert_called_once()
    for name, effect in effects.items():
        if name != "build":
            effect.assert_not_called()


@pytest.mark.parametrize("owner", ["kokoro-app", "kokoro-iam", "kokoro-bff"])
@pytest.mark.parametrize(
    "dirty_status",
    [" M src/main.ts\n", " M docs/CURRENT.md\n", "?? unpublished-source.ts\n"],
    ids=["source", "documentation", "untracked"],
)
def test_r55_login_dirty_owner_rejected_before_every_startup_effect(
    monkeypatch, tmp_path, owner, dirty_status
):
    error, effects, statuses = _r55_login_source_probe(
        monkeypatch, tmp_path, owner, dirty_status
    )

    calls = {name: effect.call_count for name, effect in effects.items()}
    assert calls == dict.fromkeys(effects, 0), (
        "dirty login-only owner must be rejected before build/infra/process: "
        f"{owner} {dirty_status!r}; observed effects={calls}"
    )
    assert (owner, dirty_status) in statuses, "the real source guard must inspect dirtiness"
    assert error is not None, "dirty source admission must fail, not advertise readiness"


def test_r56_login_freezes_one_root_commit_for_all_sources_before_build(
    monkeypatch, tmp_path
):
    trace = {}
    error, effects, _statuses = _r55_login_source_probe(
        monkeypatch, tmp_path, moving_root_head=True, release_trace=trace
    )

    assert isinstance(error, launcher.LaunchError)
    assert "BFF build" in str(error)
    effects["build"].assert_called_once()
    for name, effect in effects.items():
        if name != "build":
            effect.assert_not_called()
    at_build = trace["at_build"]
    assert at_build is not None
    assert at_build["root_reads"] == ["c" * 40], (
        "login-only must read Root HEAD once and freeze it before build; "
        f"observed={at_build['root_reads']}"
    )
    assert trace["root_reads"] == at_build["root_reads"]
    expected = {
        "apps/kokoro-app": "5f2ab341d5fc5ddee5e08d785dc7aaf391b7e9d8",
        "apps/kokoro-iam": "e3c035b99cf9479ac8357c7d38147f1541dcbcac",
        "apps/kokoro-bff": "759bfe0a8c521946cae31a74b6426f43b063bae1",
    }
    assert {record[2] for record in at_build["gitlinks"]} == set(expected)
    for revision, resolved, path, sha in at_build["gitlinks"]:
        assert (revision, resolved, sha) == ("c" * 40, "c" * 40, expected[path]), (
            "every login-only gitlink must bind to the first Root commit, "
            "not the later HEAD or index"
        )
    assert set(at_build["statuses"]) == {
        (path.removeprefix("apps/"), "") for path in expected
    }, "all three clean owner guards must complete before build"


def _r57_login_git_inputs(patches, directory):
    """Supply clean published Git inputs to pre-existing startup/cleanup fixtures."""
    root = Path(directory)
    apps = root / "apps"
    apps.mkdir()
    pins = {
        "kokoro-app": "1" * 40,
        "kokoro-iam": "2" * 40,
        "kokoro-bff": "3" * 40,
    }
    root_commit = "e" * 40
    for owner in pins:
        (apps / owner).mkdir()

    def git(command, **_kwargs):
        repo, args = Path(command[2]), command[3:]
        if command[:2] != ["git", "-C"]:
            raise AssertionError(command)
        if repo == root:
            if args == ["rev-parse", "HEAD"]:
                return root_commit + "\n"
            if args[:2] == ["ls-tree", root_commit]:
                path = args[-1]
                return f"160000 commit {pins[path.removeprefix('apps/')]}\t{path}\n"
            if args[:3] == ["ls-files", "--stage", "--"]:
                path = args[-1]
                return f"160000 {pins[path.removeprefix('apps/')]} 0\t{path}\n"
        if repo.parent == apps and repo.name in pins:
            if args == ["rev-parse", "HEAD"]:
                return pins[repo.name] + "\n"
            if args == ["status", "--porcelain", "--untracked-files=all"]:
                return ""
        raise AssertionError(command)

    for module in (launcher.web_smoke, launcher.session):
        patches.enter_context(patch.object(module, "ROOT", root))
    for label, owner in (
        ("WEB", "kokoro-app"), ("IAM", "kokoro-iam"), ("BFF", "kokoro-bff")
    ):
        patches.enter_context(patch.object(launcher.web_smoke, label, apps / owner))
    patches.enter_context(patch.object(launcher.runtime, "command_output", side_effect=git))


class StorageProfileGuards(unittest.TestCase):
    def environment(self):
        return {
            "KOKORO_LOCAL_POSTGRES_URL": "postgresql://127.0.0.1/postgres",
            "KOKORO_LOCAL_REDIS_URL": "redis://127.0.0.1:6379/9",
            "KOKORO_OBJECT_STORE_ENDPOINT": "http://127.0.0.1:39190",
            "KOKORO_OBJECT_STORE_PUBLIC_ENDPOINT": "http://127.0.0.1:39190",
            "KOKORO_OBJECT_STORE_REGION": "us-east-1",
            "KOKORO_OBJECT_STORE_ACCESS_KEY_ID": "fixture-access",
            "KOKORO_OBJECT_STORE_SECRET_ACCESS_KEY": "fixture-private-object-secret",
            "KOKORO_SCANNER_HOST": "127.0.0.1",
            "KOKORO_SCANNER_PORT": "43310",
            "KOKORO_OBJECT_STORE_PROFILE": "custom",
            "KOKORO_OBJECT_STORE_FORCE_PATH_STYLE": "true",
        }

    def arguments(self):
        return [
            "--iam-node-bin", sys.executable,
            "--bff-node-bin", sys.executable,
            "--web-node-bin", sys.executable,
            "--storage-node-bin", sys.executable,
        ]

    def test_explicit_storage_profile_keeps_its_existing_owner_inputs(self):
        # Launcher configuration guard, not Storage or user-business acceptance.
        with patch.dict(os.environ, self.environment(), clear=True):
            args = launcher.parse_args(self.arguments())
        self.assertEqual(args.storage_node_bin, Path(sys.executable).resolve())
        self.assertEqual(args.storage_environment["KOKORO_SCANNER_PORT"], "43310")
        self.assertEqual(args.storage_environment["KOKORO_OBJECT_STORE_PROFILE"], "custom")
        self.assertNotIn("KOKORO_LOCAL_POSTGRES_URL", args.storage_environment)

    def test_unselected_storage_profile_does_not_admit_inherited_configuration(self):
        args_list = self.arguments()[:-2]
        with patch.dict(os.environ, self.environment(), clear=True):
            args = launcher.parse_args(args_list)
        self.assertIsNone(args.storage_node_bin)
        self.assertIsNone(args.storage_environment)


    def test_storage_profile_rejects_missing_remote_and_emulated_inputs(self):
        for changes in (
            {"KOKORO_OBJECT_STORE_ENDPOINT": ""},
            {"KOKORO_OBJECT_STORE_ENDPOINT": "https://other.example:9000"},
            {"KOKORO_OBJECT_STORE_PUBLIC_ENDPOINT": "http://user:pass@127.0.0.1:39190"},
            {"KOKORO_SCANNER_HOST": "other.example"},
            {"KOKORO_SCANNER_PORT": "3310"},
            {"KOKORO_SCANNER_PORT": "65536"},
            {"KOKORO_OBJECT_STORE_PROFILE": "local"},
            {"KOKORO_OBJECT_STORE_FORCE_PATH_STYLE": "false"},
        ):
            environment = {**self.environment(), **changes}
            with self.subTest(changes=changes), patch.dict(os.environ, environment, clear=True):
                with self.assertRaises(SystemExit) as rejected:
                    launcher.parse_args(self.arguments())
                self.assertEqual(rejected.exception.code, 2)

    def test_storage_unknown_bucket_creation_is_not_claimed_clean(self):
        environment = self.environment()
        owned = launcher.storage_runtime.LocalStorageRuntime(
            node=Path(sys.executable), environment=environment,
            node_environment={}, directory=Path(tempfile.gettempdir()),
            credentials=None, log=None,
        )
        owned.bucket_attempted = True
        self.assertEqual(owned.close(), ["Storage bucket creation outcome requires reconciliation"])
        self.assertFalse(owned.bucket_created)


    def test_storage_release_preflight_checks_the_fourth_owner_on_the_frozen_root(self):
        from contextlib import ExitStack
        for violation in (None, "dirty", "head", "index"):
            with self.subTest(violation=violation), tempfile.TemporaryDirectory() as directory, ExitStack() as patches:
                root = Path(directory)
                apps = root / "apps"
                pins = {"kokoro-app": "1" * 40, "kokoro-iam": "2" * 40,
                        "kokoro-bff": "3" * 40, "kokoro-storage": "4" * 40}
                for name in pins:
                    (apps / name).mkdir(parents=True)
                observed = []
                def git(command, **_kwargs):
                    observed.append(command)
                    repo, arguments = Path(command[2]), command[3:]
                    if repo == root:
                        if arguments == ["rev-parse", "HEAD"]:
                            return "a" * 40
                        name = arguments[-1].removeprefix("apps/")
                        if arguments[:2] == ["ls-tree", "a" * 40]:
                            return f"160000 commit {pins[name]}\tapps/{name}"
                        if arguments[:3] == ["ls-files", "--stage", "--"]:
                            sha = "b" * 40 if name == "kokoro-storage" and violation == "index" else pins[name]
                            return f"160000 {sha} 0\tapps/{name}"
                    if repo.parent == apps:
                        if arguments == ["rev-parse", "HEAD"]:
                            return "b" * 40 if repo.name == "kokoro-storage" and violation == "head" else pins[repo.name]
                        if arguments == ["status", "--porcelain", "--untracked-files=all"]:
                            return " M src/main.ts" if repo.name == "kokoro-storage" and violation == "dirty" else ""
                    raise AssertionError(command)
                patches.enter_context(patch.object(launcher.web_smoke, "ROOT", root))
                for label, name in (("WEB", "kokoro-app"), ("IAM", "kokoro-iam"), ("BFF", "kokoro-bff")):
                    patches.enter_context(patch.object(launcher.web_smoke, label, apps / name))
                patches.enter_context(patch.object(launcher.runtime, "command_output", side_effect=git))
                if violation is None:
                    launcher.verify_login_release_inputs(storage=True)
                else:
                    with self.assertRaises(launcher.LaunchError):
                        launcher.verify_login_release_inputs(storage=True)
                self.assertEqual(sum(command[3:] == ["rev-parse", "HEAD"] and Path(command[2]) == root for command in observed), 1)
                self.assertTrue(any(Path(command[2]) == apps / "kokoro-storage" for command in observed))
