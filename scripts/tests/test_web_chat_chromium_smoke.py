"""Focused guards for the real-Chromium Web/IAM milestone."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import socket
import ssl
import tempfile
from threading import Thread

import pytest

from scripts.e2e import run_web_chat_chromium_smoke as chromium_smoke
from scripts.e2e import run_web_chat_worker_smoke as worker_smoke


ROOT = Path(__file__).resolve().parents[2]


def test_owned_tls_reservation_is_exclusive_and_single_transfer() -> None:
    reservation = chromium_smoke.OwnedTlsReservation.reserve()
    port = reservation.port
    competing = socket.socket()
    try:
        with pytest.raises(OSError):
            competing.bind(("127.0.0.1", port))
        transferred = reservation.transfer_socket()
        with pytest.raises(chromium_smoke.SmokeError):
            reservation.transfer_socket()
        assert transferred.getsockname()[1] == port
        transferred.close()
    finally:
        competing.close()
        reservation.close()


def test_owned_tls_reservation_closes_on_exception() -> None:
    port = 0
    with pytest.raises(RuntimeError):
        with chromium_smoke.OwnedTlsReservation.reserve() as reservation:
            port = reservation.port
            raise RuntimeError("injected")
    replacement = socket.socket()
    try:
        replacement.bind(("127.0.0.1", port))
    finally:
        replacement.close()


def test_browser_origin_mode_uses_exact_reserved_port() -> None:
    mode = worker_smoke.BrowserOriginMode(
        tls_port=43123,
        proxy_factory=lambda *_args: None,
        before_cookiejar=lambda *_args: None,
    )

    origin, host = worker_smoke._web_origin("a" * 24, mode)

    assert host == "web-aaaaaaaaaaaaaaaaaaaaaaaa.example.test"
    assert origin == f"https://{host}:43123"


def test_browser_proxy_rejects_port_drift() -> None:
    class WrongProxy:
        server_port = 43124

    mode = worker_smoke.BrowserOriginMode(
        tls_port=43123,
        proxy_factory=lambda *_args: WrongProxy(),
        before_cookiejar=lambda *_args: None,
    )

    with pytest.raises(worker_smoke.SmokeError, match="TLS port"):
        worker_smoke._create_web_proxy(
            mode,
            upstream_port=32100,
            host_name="web.example.test",
            authority="web.example.test:43123",
            certificate=(Path("certificate"), Path("key")),
        )


def test_browser_mode_changes_only_test_owned_next_external_port(tmp_path) -> None:
    server = tmp_path / "server.cjs"
    config = tmp_path / "next.config.ts"
    original = "const app = next({ dev: true, hostname: host, port: 443 })\n"
    server.write_text(original)
    config.write_text('const config = {\n  output: "standalone",\n}\n')
    mode = worker_smoke.BrowserOriginMode(
        tls_port=43123,
        proxy_factory=lambda *_args: None,
        before_cookiejar=lambda *_args: None,
    )

    worker_smoke._configure_next_browser_port(tmp_path, mode)

    assert server.read_text() == original.replace("dev: true", "dev: false").replace(
        "port: 443", "port: 43123"
    )
    assert 'output: "standalone"' not in config.read_text()


def test_default_mode_keeps_test_owned_next_server_bytes(tmp_path) -> None:
    server = tmp_path / "server.cjs"
    original = "const app = next({ dev: true, hostname: host, port: 443 })\n"
    server.write_text(original)

    worker_smoke._configure_next_browser_port(tmp_path, None)

    assert server.read_text() == original


def test_owned_browser_proxy_forwards_actual_authority_and_port() -> None:
    observed: list[tuple[str | None, str | None, str | None]] = []

    class UpstreamHandler(BaseHTTPRequestHandler):
        def log_message(self, _format, *_args) -> None:
            pass

        def do_GET(self) -> None:
            observed.append(
                (
                    self.headers.get("host"),
                    self.headers.get("x-forwarded-host"),
                    self.headers.get("x-forwarded-port"),
                )
            )
            payload = b"ok"
            self.send_response(200)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    upstream = ThreadingHTTPServer(("127.0.0.1", 0), UpstreamHandler)
    upstream_thread = Thread(target=upstream.serve_forever, daemon=True)
    upstream_thread.start()
    reservation = chromium_smoke.OwnedTlsReservation.reserve()
    port = reservation.port
    authority = f"web-browser.example.test:{port}"
    with tempfile.TemporaryDirectory() as directory:
        certificate = worker_smoke.product.certificate(
            Path(directory), "web-browser.example.test"
        )
        proxy = chromium_smoke.OwnedBrowserTlsProxy.from_reservation(
            reservation,
            upstream.server_port,
            "web-browser.example.test",
            authority,
            certificate,
        )
        try:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            with socket.create_connection(("127.0.0.1", port), timeout=2) as raw:
                with context.wrap_socket(
                    raw, server_hostname="web-browser.example.test"
                ) as client:
                    client.sendall(
                        b"GET / HTTP/1.1\r\n"
                        + f"Host: {authority}\r\n".encode()
                        + b"Connection: close\r\n\r\n"
                    )
                    response = bytearray()
                    while chunk := client.recv(4096):
                        response.extend(chunk)
            assert bytes(response).startswith(b"HTTP/1.1 200 ")
            assert observed == [(authority, authority, str(port))]
        finally:
            proxy.close()
            reservation.close()
            upstream.shutdown()
            upstream.server_close()
            upstream_thread.join(timeout=5)


def test_chromium_driver_does_not_mock_authentication_or_network() -> None:
    source = (ROOT / "scripts/e2e/web_chat_chromium.mjs").read_text()
    for forbidden in (
        "addCookies",
        "route.fulfill",
        "storageState",
        "document.cookie",
        "page.evaluate",
    ):
        assert forbidden not in source
    assert "--host-resolver-rules=" in source
    assert "ignoreHTTPSErrors: true" in source
