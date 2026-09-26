"""Focused guards for the local, real three-owner login launcher."""

import importlib.util
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import socket
import sys
from threading import Thread
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
