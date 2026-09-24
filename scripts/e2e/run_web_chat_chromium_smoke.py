#!/usr/bin/env python3
"""Prove the real Chromium login handoff inside the R2b owned stack."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import socket
import ssl
import subprocess
import sys
from threading import Thread
from urllib.parse import urlsplit

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
    ) -> OwnedBrowserTlsProxy:
        listener = reservation.transfer_socket()
        try:
            server = cls(
                ("127.0.0.1", reservation.port),
                worker_smoke.product.old.ProxyHandler,
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


@dataclass(slots=True)
class ChromiumLoginMilestone:
    node_bin: Path
    headed: bool
    hold_seconds: float
    timeout: float
    result: dict[str, object] | None = None

    def __call__(
        self,
        tls_port: int,
        web_origin: str,
        ready: worker_smoke.product.previous.Ready,
        _temporary_path: Path,
    ) -> None:
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
                        "tenant_id": ready.tenant_id,
                    },
                    separators=(",", ":"),
                ),
                capture_output=True,
                timeout=self.timeout,
                check=False,
            )
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
            "tenant_form",
            "consent_form",
            "app_page",
            "product_session",
            "app_screenshot",
        }
        if (
            not isinstance(result, dict)
            or set(result) != expected_fields
            or result.get("browser") != "chromium"
            or result.get("entry_url") != web_origin + "/login"
            or result.get("iam_page") != web_origin + "/auth/sign-in"
            or result.get("email_field") is not True
            or result.get("password_field") is not True
            or result.get("csrf_requests") != 1
            or result.get("signin_requests") != 1
            or result.get("tenant_form") is not True
            or result.get("consent_form") is not True
            or result.get("app_page") is not True
            or result.get("product_session") is not True
            or result.get("screenshot") != str(screenshot)
            or not screenshot.is_file()
            or screenshot.stat().st_size == 0
            or result.get("app_screenshot") != str(app_screenshot)
            or not app_screenshot.is_file()
            or app_screenshot.stat().st_size == 0
        ):
            raise SmokeError("Chromium milestone evidence drift")
        self.result = result


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    browser_parser = argparse.ArgumentParser(add_help=False)
    browser_parser.add_argument("--headed", action="store_true")
    browser_parser.add_argument("--hold-seconds", type=float, default=0)
    browser_args, worker_argv = browser_parser.parse_known_args(argv)
    args = worker_smoke.parse_args(worker_argv)
    if not 0 <= browser_args.hold_seconds <= args.timeout:
        browser_parser.error("hold-seconds must be bounded by timeout")
    args.headed = browser_args.headed
    args.hold_seconds = browser_args.hold_seconds
    return args


def run_smoke(args: argparse.Namespace) -> dict[str, object]:
    milestone = ChromiumLoginMilestone(
        node_bin=args.node22_bin,
        headed=args.headed,
        hold_seconds=args.hold_seconds,
        timeout=args.timeout,
    )
    with OwnedTlsReservation.reserve() as reservation:
        mode = worker_smoke.BrowserOriginMode(
            tls_port=reservation.port,
            proxy_factory=lambda upstream, host, authority, certificate: (
                OwnedBrowserTlsProxy.from_reservation(
                    reservation, upstream, host, authority, certificate
                )
            ),
            before_cookiejar=milestone,
        )
        base = worker_smoke.run_smoke(args, browser_mode=mode)
    if milestone.result is None:
        raise SmokeError("Chromium login milestone did not run")
    return {
        **base,
        "browser_boundary": "real Chromium login milestone; CookieJar post-check",
        "chromium": milestone.result,
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
