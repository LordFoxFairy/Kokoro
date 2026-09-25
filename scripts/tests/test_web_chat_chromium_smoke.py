"""Focused guards for the real-Chromium Web/IAM milestone."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace
import subprocess
import socket
import ssl
import tempfile
from threading import Event, Thread

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
        execute_turn=lambda *_args: {},
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
        execute_turn=lambda *_args: {},
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
        execute_turn=lambda *_args: {},
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


def test_owned_browser_tls_proxy_flushes_live_sse_before_completion() -> None:
    release = Event()
    first_sent = Event()

    class UpstreamHandler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, _format, *_args) -> None:
            pass

        def do_GET(self) -> None:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Content-Length", "21")
            self.end_headers()
            self.wfile.write(b"id: 1\ndata: a\n\n")
            self.wfile.flush()
            first_sent.set()
            release.wait(3)
            self.wfile.write(b"id: 2\n\n")
            self.wfile.flush()

    upstream = ThreadingHTTPServer(("127.0.0.1", 0), UpstreamHandler)
    upstream_thread = Thread(target=upstream.serve_forever, daemon=True)
    upstream_thread.start()
    reservation = chromium_smoke.OwnedTlsReservation.reserve()
    with tempfile.TemporaryDirectory() as directory:
        certificate = worker_smoke.product.certificate(
            Path(directory), "web-browser.example.test"
        )
        proxy = chromium_smoke.OwnedBrowserTlsProxy.from_reservation(
            reservation,
            upstream.server_port,
            "web-browser.example.test",
            f"web-browser.example.test:{reservation.port}",
            certificate,
        )
        try:
            context = ssl._create_unverified_context()
            with socket.create_connection(
                ("127.0.0.1", proxy.server_port), timeout=2
            ) as raw:
                with context.wrap_socket(
                    raw, server_hostname="web-browser.example.test"
                ) as client:
                    client.settimeout(1)
                    client.sendall(
                        b"GET /api/session/sessions/session_one/events HTTP/1.1\r\n"
                        b"Host: web-browser.example.test\r\n"
                        b"Accept: text/event-stream\r\n\r\n"
                    )
                    assert first_sent.wait(1)
                    first = bytearray()
                    while b"id: 1" not in first:
                        first.extend(client.recv(4096))
                    assert b"HTTP/1.1 200" in first
                    assert b"Transfer-Encoding: chunked" in first
                    assert b"Content-Length:" not in first
                    release.set()
                    remaining = bytearray()
                    while part := client.recv(4096):
                        remaining.extend(part)
                    assert b"id: 2" in remaining
                    assert remaining.endswith(b"0\r\n\r\n")
        finally:
            release.set()
            proxy.close()
            reservation.close()
            upstream.shutdown()
            upstream.server_close()
            upstream_thread.join(timeout=5)


def test_owned_browser_tls_proxy_cuts_only_first_complete_agui_frame_and_forwards_resume() -> (
    None
):
    observed: list[str | None] = []

    class UpstreamHandler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, _format, *_args) -> None:
            pass

        def do_GET(self) -> None:
            observed.append(self.headers.get("Last-Event-ID"))
            non_agui = b": heartbeat\n\n"
            first = b'id: cursor-1\ndata: {"type":"RUN_STARTED"}\n\n'
            second = b'id: cursor-2\ndata: {"type":"RUN_FINISHED"}\n\n'
            payload = non_agui + first + second if len(observed) == 1 else second
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            # Both frames intentionally occupy one upstream write/read chunk.
            self.wfile.write(payload)
            self.wfile.flush()

    upstream = ThreadingHTTPServer(("127.0.0.1", 0), UpstreamHandler)
    upstream_thread = Thread(target=upstream.serve_forever, daemon=True)
    upstream_thread.start()
    reservation = chromium_smoke.OwnedTlsReservation.reserve()
    authority = f"web-browser.example.test:{reservation.port}"
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
            drop_first_agui_frame=True,
        )
        try:
            context = ssl._create_unverified_context()

            def request(cursor: str | None) -> bytes:
                with socket.create_connection(
                    ("127.0.0.1", proxy.server_port), timeout=2
                ) as raw:
                    with context.wrap_socket(
                        raw, server_hostname="web-browser.example.test"
                    ) as client:
                        client.settimeout(2)
                        headers = (
                            "GET /api/session/sessions/session_one/events HTTP/1.1\r\n"
                            f"Host: {authority}\r\n"
                            "Accept: text/event-stream\r\n"
                            + (f"Last-Event-ID: {cursor}\r\n" if cursor else "")
                            + "Connection: close\r\n\r\n"
                        )
                        client.sendall(headers.encode())
                        output = bytearray()
                        while chunk := client.recv(4096):
                            output.extend(chunk)
                        return bytes(output)

            first = request(None)
            assert b'id: cursor-1\ndata: {"type":"RUN_STARTED"}\n\n' in first
            assert b"heartbeat" not in first
            assert b"cursor-2" not in first
            assert not first.endswith(b"0\r\n\r\n")
            second = request("cursor-1")
            assert b'id: cursor-2\ndata: {"type":"RUN_FINISHED"}\n\n' in second
            assert observed == [None, "cursor-1"]
            assert proxy.first_agui_cursor == "cursor-1"
            assert proxy.controlled_disconnects == 1
            assert proxy.agui_resume_headers == ["cursor-1"]
            assert proxy.assert_recovery(
                "/api/session/sessions/session_one/events"
            ) == {
                "controlled_disconnects": 1,
                "first_cursor": "cursor-1",
                "resumed_last_event_id": "cursor-1",
                "same_event_path": True,
            }
            with pytest.raises(chromium_smoke.SmokeError, match="cursor recovery"):
                proxy.assert_recovery("/api/session/sessions/another_session/events")
            proxy.agui_request_headers[1] = (
                "/api/session/sessions/session_one/events",
                "wrong-cursor",
            )
            with pytest.raises(chromium_smoke.SmokeError, match="cursor recovery"):
                proxy.assert_recovery("/api/session/sessions/session_one/events")
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
    ):
        assert forbidden not in source
    assert "--host-resolver-rules=" in source
    assert "ignoreHTTPSErrors: true" in source


def test_chromium_driver_submits_real_iam_forms_without_argv_credentials() -> None:
    source = (ROOT / "scripts/e2e/web_chat_chromium.mjs").read_text()
    runner = (ROOT / "scripts/e2e/run_web_chat_chromium_smoke.py").read_text()

    assert 'readFileSync(0, "utf8")' in source
    assert "input=json.dumps(" in runner
    assert "email.fill(input.email)" in source
    assert "password.fill(input.password)" in source
    assert 'name: "Select tenant"' not in source
    assert "selectOption(input.tenant_id)" not in source
    assert 'name: "Review requested access"' in source
    assert "fixed_tenant_continuation: true" in source
    assert '"fixed_tenant_continuation"' in runner
    assert '"tenant_form"' not in runner
    assert 'name: "Agree and continue"' in source
    assert 'url.pathname === "/app"' in source
    assert 'fetch("/api/auth/session"' in source
    assert "context.cookies(input.web_origin)" in source


def test_chromium_driver_submits_dom_composer_and_checks_durable_reload() -> None:
    source = (ROOT / "scripts/e2e/web_chat_chromium.mjs").read_text()
    assert 'data-slot="composer-input"' in source
    assert 'data-composer-action="send"' in source
    assert "response.status() === 202" in source
    assert 'data-slot="user-message-body"' in source
    assert 'data-slot="markdown-message"' in source
    assert "await page.reload(" in source
    assert "event_watermark" in source


def test_chromium_driver_requires_exact_five_unique_agui_frames() -> None:
    source = (ROOT / "scripts/e2e/web_chat_chromium.mjs").read_text()
    runner = (ROOT / "scripts/e2e/run_web_chat_chromium_smoke.py").read_text()
    assert (
        'const expectedTypes = ["RUN_STARTED", "TEXT_MESSAGE_START", "TEXT_MESSAGE_CONTENT", "TEXT_MESSAGE_END", "RUN_FINISHED"]'
        in source
    )
    assert "JSON.stringify(frameTypes) !== JSON.stringify(expectedTypes)" in source
    assert (
        "new Set(replay.frames.map((frame) => frame.id)).size !== replay.frames.length"
        in source
    )
    assert "agui_frame_ids: replay.frames.map((frame) => frame.id)" in source
    assert 'result["agui_frame_ids"][0] != recovery["first_cursor"]' in runner
    assert 'sql_evidence.get("bff_agui_frames") != 5' in runner
    assert "owned_proxy.assert_recovery(expected_event_path)" in runner
    assert (
        "observedAguiResponses.filter((response) => response.status === 200" in source
    )


def test_chromium_assistant_wait_reports_owner_snapshot_and_dom_state() -> None:
    source = (ROOT / "scripts/e2e/web_chat_chromium.mjs").read_text()
    assert "Browser assistant DOM did not converge" in source
    assert "snapshot_status" in source
    assert "dom_users" in source
    assert "dom_assistants" in source
    assert "web_view" in source
    assert "visible_alerts" in source
    assert "sse_attempts" in source


def test_failure_injection_option_is_scoped_to_browser_runner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        chromium_smoke.worker_smoke,
        "parse_args",
        lambda argv: SimpleNamespace(timeout=120, node22_bin=Path("/fixture/node")),
    )

    args = chromium_smoke.parse_args(["--fail-after-chat-receipt"])

    assert args.fail_after_chat_receipt is True


def test_chromium_timeout_reports_only_last_controlled_stage(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def timed_out(*_args: object, **_kwargs: object) -> None:
        raise subprocess.TimeoutExpired(
            ["node", "driver"], 180, stderr=b"MILESTONE:receipt\nsecret=do-not-echo\n"
        )

    monkeypatch.setattr(chromium_smoke.subprocess, "run", timed_out)
    milestone = chromium_smoke.ChromiumLoginMilestone(
        node_bin=Path("/fixture/node"),
        headed=False,
        hold_seconds=0,
        timeout=120,
        fail_after_chat_receipt=False,
    )
    ready = SimpleNamespace(
        redirect_uri="https://web.example.test:443/api/auth/callback/kokoro-iam",
        email="user@example.test",
        password="do-not-echo",
        tenant_id="tenant_1",
    )
    turn = worker_smoke.BrowserTurnContext(
        start_worker=lambda: None, expected_reply="reply", timeout=120
    )

    with pytest.raises(chromium_smoke.SmokeError, match="stage=receipt") as error:
        milestone(443, "https://web.example.test:443", ready, tmp_path, turn)

    assert "do-not-echo" not in str(error.value)
