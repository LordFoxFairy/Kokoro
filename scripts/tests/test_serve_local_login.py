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

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/dev/serve_local_login.py"
sys.path.insert(0, str(ROOT / "scripts/e2e"))
spec = importlib.util.spec_from_file_location("serve_local_login", SCRIPT)
launcher = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = launcher
spec.loader.exec_module(launcher)


class LocalLoginGuards(unittest.TestCase):
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
                    launcher.web_smoke,
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
