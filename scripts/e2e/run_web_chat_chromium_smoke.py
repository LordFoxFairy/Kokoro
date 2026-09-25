#!/usr/bin/env python3
"""Prove the real Chromium login handoff inside the R2b owned stack."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import http.client
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import re
import select
import socket
import ssl
import subprocess
import sys
from threading import Event, Lock, Thread
import time
from urllib.parse import quote, urlsplit

E2E = Path(__file__).resolve().parent
if str(E2E) not in sys.path:
    sys.path.insert(0, str(E2E))

if __package__:
    from . import run_web_chat_worker_smoke as worker_smoke
else:
    import run_web_chat_worker_smoke as worker_smoke


SmokeError = worker_smoke.SmokeError
ROOT = worker_smoke.ROOT
WEB = worker_smoke.WEB
DRIVER = E2E / "web_chat_chromium.mjs"
ARTIFACT_ROOT = ROOT / "output" / "playwright" / "r2c-login"
_BROWSER_STAGES = frozenset({"iam", "app", "receipt", "assistant", "replay", "reload"})


def _last_browser_stage(stderr: bytes | str | None) -> str:
    if not isinstance(stderr, (bytes, str)):
        return "unknown"
    output = (
        stderr.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes)
        else stderr
    )
    stages = [
        line.removeprefix("MILESTONE:")
        for line in output.splitlines()
        if line.startswith("MILESTONE:")
    ]
    return stages[-1] if stages and stages[-1] in _BROWSER_STAGES else "unknown"


@dataclass(slots=True)
class OwnedTlsReservation:
    """Hold one loopback TCP listener until the HTTPS proxy adopts it."""

    _socket: socket.socket | None
    port: int

    @classmethod
    def reserve(cls) -> OwnedTlsReservation:
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            listener.bind(("127.0.0.1", 0))
            listener.listen(128)
            return cls(listener, listener.getsockname()[1])
        except BaseException:
            listener.close()
            raise

    def transfer_socket(self) -> socket.socket:
        listener = self._socket
        if listener is None:
            raise SmokeError("Owned TLS listener was already transferred")
        self._socket = None
        return listener

    def close(self) -> None:
        if self._socket is not None:
            self._socket.close()
            self._socket = None

    def __enter__(self) -> OwnedTlsReservation:
        return self

    def __exit__(self, *_error: object) -> None:
        self.close()


class OwnedBrowserTlsProxy(ThreadingHTTPServer):
    """TLS proxy that atomically adopts the run-owned listener."""

    daemon_threads = True

    @classmethod
    def from_reservation(
        cls,
        reservation: OwnedTlsReservation,
        upstream_port: int,
        host_name: str,
        authority: str,
        certificate: tuple[Path, Path],
        drop_first_agui_frame: bool = False,
    ) -> OwnedBrowserTlsProxy:
        listener = reservation.transfer_socket()
        try:
            server = cls(
                ("127.0.0.1", reservation.port),
                BrowserRecoveryProxyHandler,
                bind_and_activate=False,
            )
            server.socket.close()
            server.socket = listener
            server.server_address = listener.getsockname()
            server.server_name = socket.getfqdn(server.server_address[0])
            server.server_port = server.server_address[1]
            server.upstream_port = upstream_port
            server.web_host = authority
            server.web_port = reservation.port
            server.tls_web = True
            server.observed: list[tuple[str, str]] = []
            server.credentials = None
            server.stream_sse = True
            server.drop_first_agui_frame = drop_first_agui_frame
            server.recovery_lock = Lock()
            server.recovery_claimed = False
            server.controlled_disconnects = 0
            server.first_agui_cursor = None
            server.first_agui_path = None
            server.agui_request_headers = []
            server.agui_resume_headers = []
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(str(certificate[0]), str(certificate[1]))
            server.socket = context.wrap_socket(server.socket, server_side=True)
            server.thread = Thread(target=server.serve_forever, daemon=True)
            server.thread.start()
            return server
        except BaseException:
            listener.close()
            raise

    def close(self) -> None:
        self.shutdown()
        self.server_close()
        self.thread.join(timeout=5)

    def assert_recovery(self, expected_event_path: str) -> dict[str, object]:
        with self.recovery_lock:
            first_cursor = self.first_agui_cursor
            first_path = self.first_agui_path
            requests = list(self.agui_request_headers)
            resumes = list(self.agui_resume_headers)
            cuts = self.controlled_disconnects
        if (
            cuts != 1
            or not isinstance(first_cursor, str)
            or not first_cursor
            or not isinstance(first_path, str)
            or first_path != expected_event_path
            or len(requests) < 2
            or requests[0] != (first_path, None)
            or requests[1] != (first_path, first_cursor)
            or not resumes
            or resumes[0] != first_cursor
        ):
            raise SmokeError("Chromium AG-UI controlled cursor recovery drift")
        return {
            "controlled_disconnects": cuts,
            "first_cursor": first_cursor,
            "resumed_last_event_id": resumes[0],
            "same_event_path": True,
        }


class BrowserRecoveryProxyHandler(worker_smoke.product.old.ProxyHandler):
    """One test-owned SSE cut after exactly one complete upstream AG-UI event."""

    def forward(self) -> None:
        if self.command == "GET" and worker_smoke.product.old._SSE_PATH.fullmatch(
            self.path.split("?", 1)[0]
        ):
            cursor = self.headers.get("Last-Event-ID")
            with self.server.recovery_lock:
                self.server.agui_request_headers.append((self.path, cursor))
                if cursor is not None:
                    self.server.agui_resume_headers.append(cursor)
        super().forward()

    def _stream_sse(
        self, response: http.client.HTTPResponse, upstream: http.client.HTTPConnection
    ) -> None:
        with self.server.recovery_lock:
            truncate = (
                self.server.drop_first_agui_frame and not self.server.recovery_claimed
            )
            if truncate:
                self.server.recovery_claimed = True
        if not truncate:
            super()._stream_sse(response, upstream)
            return

        self.send_response_only(200)
        for name, value in response.getheaders():
            if name.lower() not in {
                "connection",
                "content-length",
                "transfer-encoding",
                "trailer",
                "keep-alive",
                "proxy-connection",
                "upgrade",
                "te",
            }:
                self.send_header(name, value)
        self.send_header("Transfer-Encoding", "chunked")
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.flush()
        self.close_connection = True
        response_socket = upstream.sock or getattr(
            getattr(response.fp, "raw", None), "_sock", None
        )
        if response_socket is None:
            return
        watcher_stop = Event()

        def close_upstream_on_disconnect() -> None:
            while not watcher_stop.is_set():
                try:
                    if select.select([self.connection], [], [], 0.1)[0]:
                        response_socket.shutdown(socket.SHUT_RDWR)
                        return
                except (OSError, ValueError):
                    return

        watcher = Thread(target=close_upstream_on_disconnect, daemon=True)
        watcher.start()
        pending = bytearray()
        total = 0
        deadline = time.monotonic() + worker_smoke.product.old.SSE_TOTAL_SECONDS
        try:
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return
                response_socket.settimeout(
                    min(worker_smoke.product.old.SSE_IDLE_SECONDS, remaining)
                )
                chunk = response.read1(4096)
                if not chunk:
                    return
                total += len(chunk)
                if total > worker_smoke.product.old.MAX_SSE_BODY:
                    return
                pending.extend(chunk)
                while match := re.search(rb"\r?\n\r?\n", pending):
                    frame = bytes(pending[: match.end()])
                    del pending[: match.end()]
                    id_match = re.search(rb"^id: ?([^\r\n]+)$", frame, re.MULTILINE)
                    if id_match is None or not re.search(
                        rb"^data:", frame, re.MULTILINE
                    ):
                        continue
                    try:
                        cursor = id_match.group(1).decode("utf-8")
                    except UnicodeDecodeError:
                        return
                    self.wfile.write(f"{len(frame):x}\r\n".encode("ascii"))
                    self.wfile.write(frame)
                    self.wfile.write(b"\r\n")
                    self.wfile.flush()
                    with self.server.recovery_lock:
                        self.server.first_agui_cursor = cursor
                        self.server.first_agui_path = self.path
                        self.server.controlled_disconnects += 1
                    # Deliberately omit the terminating HTTP chunk. Any remaining
                    # events in the same upstream read are not sent to Chromium.
                    return
        except (OSError, ValueError, http.client.HTTPException):
            return
        finally:
            watcher_stop.set()
            watcher.join(timeout=0.5)


@dataclass(slots=True)
class ChromiumLoginMilestone:
    node_bin: Path
    headed: bool
    hold_seconds: float
    timeout: float
    fail_after_chat_receipt: bool = False
    result: dict[str, object] | None = None

    def __call__(
        self,
        tls_port: int,
        web_origin: str,
        ready: worker_smoke.product.previous.Ready,
        _temporary_path: Path,
        turn: worker_smoke.BrowserTurnContext,
    ) -> dict[str, object]:
        parsed = urlsplit(web_origin)
        if (
            parsed.scheme != "https"
            or parsed.hostname is None
            or parsed.port != tls_port
            or ready.redirect_uri != web_origin + "/api/auth/callback/kokoro-iam"
        ):
            raise SmokeError("Chromium Web/IAM origin drift")
        ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
        screenshot = ARTIFACT_ROOT / f"iam-login-{parsed.hostname}.png"
        app_screenshot = ARTIFACT_ROOT / f"app-{parsed.hostname}.png"
        command = [
            str(self.node_bin),
            str(DRIVER),
        ]
        turn.start_worker()
        try:
            completed = subprocess.run(
                command,
                cwd=ROOT,
                text=True,
                input=json.dumps(
                    {
                        "web_origin": web_origin,
                        "web_host": parsed.hostname,
                        "web_root": str(WEB),
                        "screenshot": str(screenshot),
                        "headed": self.headed,
                        "hold_seconds": self.hold_seconds,
                        "email": ready.email,
                        "password": ready.password,
                        "chat_content": "Run the deterministic Web worker smoke.",
                        "expected_reply": turn.expected_reply,
                        "chat_timeout_ms": int(turn.timeout * 1000),
                        "fail_after_chat_receipt": self.fail_after_chat_receipt,
                    },
                    separators=(",", ":"),
                ),
                capture_output=True,
                # The driver's chat timeout starts only after IAM navigation.
                timeout=self.timeout + 60,
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            raise SmokeError(
                f"Chromium milestone timed out; stage={_last_browser_stage(error.stderr)}"
            ) from None
        except (OSError, subprocess.SubprocessError):
            raise SmokeError("Chromium milestone process failed") from None
        if completed.returncode != 0:
            diagnostic = completed.stderr.strip()[-2_000:]
            raise SmokeError(
                "Chromium login milestone failed"
                + (f": {diagnostic}" if diagnostic else "")
            )
        try:
            result = json.loads(completed.stdout)
        except (TypeError, ValueError):
            raise SmokeError("Chromium milestone evidence malformed") from None
        expected_fields = {
            "browser",
            "entry_url",
            "iam_page",
            "password_field",
            "email_field",
            "screenshot",
            "csrf_requests",
            "signin_requests",
            "fixed_tenant_continuation",
            "consent_form",
            "app_page",
            "product_session",
            "app_screenshot",
            "conversation_id",
            "run_id",
            "message_post_status",
            "agui_first_status",
            "agui_frame_types",
            "agui_frame_ids",
            "event_watermark",
            "reload_user_count",
            "reload_assistant_count",
            "reload_reply_visible",
        }
        if (
            not isinstance(result, dict)
            or set(result) != expected_fields
            or result.get("browser") != "chromium"
            or result.get("entry_url") != web_origin + "/login"
            or result.get("iam_page") != web_origin + "/auth/sign-in"
            or result.get("email_field") is not True
            or result.get("password_field") is not True
            or result.get("csrf_requests") != 0
            or result.get("signin_requests") != 0
            or result.get("fixed_tenant_continuation") is not True
            or result.get("consent_form") is not True
            or result.get("app_page") is not True
            or result.get("product_session") is not True
            or result.get("screenshot") != str(screenshot)
            or not screenshot.is_file()
            or screenshot.stat().st_size == 0
            or result.get("app_screenshot") != str(app_screenshot)
            or not app_screenshot.is_file()
            or app_screenshot.stat().st_size == 0
            or not isinstance(result.get("conversation_id"), str)
            or not result["conversation_id"].startswith("conv_")
            or not isinstance(result.get("run_id"), str)
            or not result["run_id"]
            or result.get("message_post_status") != 202
            or result.get("agui_first_status") != 200
            or not isinstance(result.get("agui_frame_types"), list)
            or result["agui_frame_types"]
            != [
                "RUN_STARTED",
                "TEXT_MESSAGE_START",
                "TEXT_MESSAGE_CONTENT",
                "TEXT_MESSAGE_END",
                "RUN_FINISHED",
            ]
            or not isinstance(result.get("agui_frame_ids"), list)
            or len(result["agui_frame_ids"]) != 5
            or any(
                not isinstance(cursor, str) or not cursor
                for cursor in result["agui_frame_ids"]
            )
            or len(set(result["agui_frame_ids"])) != 5
            or not isinstance(result.get("event_watermark"), str)
            or not result["event_watermark"]
            or result.get("reload_user_count") != 1
            or result.get("reload_assistant_count") != 1
            or result.get("reload_reply_visible") is not True
        ):
            raise SmokeError("Chromium milestone evidence drift")
        self.result = result
        return {
            "conversation_id": result["conversation_id"],
            "run_id": result["run_id"],
            "event_watermark": result["event_watermark"],
            "agui_frame_types": result["agui_frame_types"],
            "agui_frame_ids": result["agui_frame_ids"],
            "reload_user_count": result["reload_user_count"],
            "reload_assistant_count": result["reload_assistant_count"],
        }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    browser_parser = argparse.ArgumentParser(add_help=False)
    browser_parser.add_argument("--headed", action="store_true")
    browser_parser.add_argument("--hold-seconds", type=float, default=0)
    browser_parser.add_argument("--fail-after-chat-receipt", action="store_true")
    browser_args, worker_argv = browser_parser.parse_known_args(argv)
    args = worker_smoke.parse_args(worker_argv)
    if not 0 <= browser_args.hold_seconds <= args.timeout:
        browser_parser.error("hold-seconds must be bounded by timeout")
    args.headed = browser_args.headed
    args.hold_seconds = browser_args.hold_seconds
    args.fail_after_chat_receipt = browser_args.fail_after_chat_receipt
    return args


def run_smoke(args: argparse.Namespace) -> dict[str, object]:
    milestone = ChromiumLoginMilestone(
        node_bin=args.node22_bin,
        headed=args.headed,
        hold_seconds=args.hold_seconds,
        timeout=args.timeout,
        fail_after_chat_receipt=args.fail_after_chat_receipt,
    )
    owned_proxy: OwnedBrowserTlsProxy | None = None
    with OwnedTlsReservation.reserve() as reservation:

        def create_proxy(
            upstream: int, host: str, authority: str, certificate: tuple[Path, Path]
        ) -> OwnedBrowserTlsProxy:
            nonlocal owned_proxy
            owned_proxy = OwnedBrowserTlsProxy.from_reservation(
                reservation,
                upstream,
                host,
                authority,
                certificate,
                drop_first_agui_frame=True,
            )
            return owned_proxy

        mode = worker_smoke.BrowserOriginMode(
            tls_port=reservation.port,
            proxy_factory=create_proxy,
            execute_turn=milestone,
        )
        base = worker_smoke.run_smoke(args, browser_mode=mode)
    if milestone.result is None or owned_proxy is None:
        raise SmokeError("Chromium login milestone did not run")
    result = milestone.result
    expected_event_path = (
        "/api/session/sessions/" + quote(result["conversation_id"], safe="") + "/events"
    )
    recovery = owned_proxy.assert_recovery(expected_event_path)
    sql_evidence = base.get("chat", {}).get("sql_evidence", {})
    if (
        result["agui_frame_ids"][0] != recovery["first_cursor"]
        or sql_evidence.get("bff_agui_frames") != 5
    ):
        raise SmokeError("Chromium AG-UI five-frame recovery evidence drift")
    return {
        **base,
        "browser_boundary": "same Chromium Context login, DOM message, AG-UI and reload",
        "chromium": result,
        "agui_recovery": recovery,
    }


def main(argv: list[str] | None = None) -> int:
    print(json.dumps(run_smoke(parse_args(argv)), sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SmokeError as error:
        print(f"FAIL: {error}", file=sys.stderr)
        raise SystemExit(1) from None
