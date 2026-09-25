"""Focused guards for the local, real three-owner login launcher."""

import importlib.util
from pathlib import Path
import socket
import sys
import tempfile
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
    def test_origin_is_https_non_loopback_on_local_port(self):
        self.assertEqual(
            launcher.web_origin("a" * 24),
            "https://web-aaaaaaaaaaaaaaaaaaaaaaaa.example.test:3310",
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

    def test_https_proxy_binds_exact_port_and_chrome_is_isolated(self):
        host = "web-" + "a" * 24 + ".example.test"
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with socket.socket() as reservation:
                reservation.bind(("127.0.0.1", 0))
                port = reservation.getsockname()[1]
            with patch.object(launcher, "WEB_PORT", port):
                proxy = launcher.LocalWebProxy(
                    65534, host, launcher.web_smoke.certificate(root, host)
                )
                try:
                    self.assertEqual(proxy.server_port, port)
                    self.assertEqual(proxy.web_host, host + f":{port}")
                    self.assertEqual(proxy.web_port, port)
                    self.assertTrue(proxy.tls_web)
                finally:
                    proxy.close()
            command = launcher.chromium_command(
                Path("/chrome"),
                root / "profile",
                host,
                launcher.web_origin("a" * 24),
                launcher.certificate_spki_sha256(root / "web.crt"),
            )
            self.assertIn("--user-data-dir=" + str(root / "profile"), command)
            self.assertIn("--host-resolver-rules=MAP " + host + " 127.0.0.1", command)
            self.assertIn("--no-proxy-server", command)
            self.assertNotIn("--ignore-certificate-errors", command)
            self.assertTrue(
                any(
                    arg.startswith("--ignore-certificate-errors-spki-list=")
                    for arg in command
                )
            )
            self.assertEqual(command[-1], launcher.web_origin("a" * 24) + "/login")

    def test_database_endpoints_are_read_from_environment_without_password(self):
        paths = {
            "--iam-node-bin": "/bin/echo",
            "--bff-node-bin": "/bin/echo",
            "--web-node-bin": "/bin/echo",
            "--chromium-bin": "/bin/echo",
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
