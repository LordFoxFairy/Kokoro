"""Owned Billing lifecycle for the existing isolated login composition.

Billing installs its own empty schema in the caller-owned application database.
No credit accounts, balances, ledger entries or payment providers are seeded.
"""

from __future__ import annotations

import json
import re
import secrets
import socket
import subprocess
import time
from http.client import HTTPConnection, HTTPException
from pathlib import Path
from threading import Lock, Timer
from typing import BinaryIO
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import capability_bff_smoke_runtime as runtime
import local_chat_runtime
import run_bff_iam_oidc_smoke as oidc

BILLING = Path(__file__).resolve().parents[2] / "apps/kokoro-billing"
BILLING_AUDIENCE = "https://kokoro.dev/resources/billing"
READY_TIMEOUT_SECONDS = 30.0
READY = {
    "data": {
        "module": "kokoro-billing",
        "status": "ready",
        "dependencies": {"postgres": "ok"},
    }
}


class BillingRuntimeError(RuntimeError):
    """Sanitized Billing lifecycle failure, never an environment or endpoint."""


def billing_owner_database_url(application_database_url: str) -> str:
    """Select only Billing's schema without widening the sandbox schema whitelist."""
    try:
        parsed = urlsplit(application_database_url)
        if (
            parsed.scheme not in {"postgres", "postgresql"}
            or not parsed.hostname
            or not parsed.path.removeprefix("/")
            or parsed.fragment
        ):
            raise ValueError
        _ = parsed.port
        query = [
            (name, value)
            for name, value in parse_qsl(parsed.query, keep_blank_values=True)
            if name.lower() not in {"schema", "options", "search_path"}
        ]
        query.append(("schema", "kokoro_billing"))
        return urlunsplit(
            (parsed.scheme, parsed.netloc, parsed.path, urlencode(query), "")
        )
    except ValueError:
        raise BillingRuntimeError(
            "Billing application database identity invalid"
        ) from None


def _billing_ready_body(base: str, deadline: float) -> object:
    """One owner request; a watchdog closes its socket even during slow body reads."""
    parsed = urlsplit(base)
    if parsed.scheme != "http" or parsed.hostname != "127.0.0.1":
        raise ValueError("Billing probe requires owned numeric loopback")
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError
    connection = HTTPConnection(parsed.hostname, parsed.port, timeout=remaining)
    lock = Lock()
    owned_socket: socket.socket | None = None
    expired = False

    def expire() -> None:
        nonlocal expired
        with lock:
            expired = True
            current = owned_socket
        if current is not None:
            try:
                current.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            current.close()

    timer = Timer(remaining, expire)
    timer.start()
    response = None
    try:
        # Numeric loopback from the owned launcher: no unbounded DNS resolution.
        connection.connect()
        with lock:
            owned_socket = connection.sock
            already_expired = expired
        if already_expired:
            expire()
            raise TimeoutError
        connection.request("GET", "/readyz")
        response = connection.getresponse()
        payload = response.read(16_385)
        if expired or time.monotonic() >= deadline:
            raise TimeoutError
        if response.status != 200 or len(payload) > 16_384:
            return None
        return json.loads(payload)
    finally:
        timer.cancel()
        timer.join()
        if response is not None:
            response.close()
        connection.close()


def wait_billing_ready(base: str, process: subprocess.Popen[bytes]) -> None:
    """Poll only the owner probe, with bounded HTTP and a finite startup budget."""
    deadline = time.monotonic() + READY_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise BillingRuntimeError("Billing process exited before readiness")
        try:
            body = _billing_ready_body(base, deadline)
            if body == READY and time.monotonic() < deadline:
                if process.poll() is not None:
                    raise BillingRuntimeError("Billing process exited before readiness")
                return
        except (HTTPException, OSError, ValueError):
            pass
        time.sleep(max(0, min(0.2, deadline - time.monotonic())))
    raise BillingRuntimeError("Billing readiness deadline exceeded")


class LocalBillingRuntime:
    def __init__(
        self,
        *,
        node: Path,
        node_environment: dict[str, str],
        credentials: oidc.CredentialRegistry,
        log: BinaryIO,
    ) -> None:
        self.node = node
        self.node_environment = node_environment
        self.log = log
        self.credentials = credentials
        self.internal_secret = ""
        self.service_token = ""
        self.operator_secret = ""
        self.process: subprocess.Popen[bytes] | None = None
        self.quiescent = True
        self._attempted = False
        self._closed = False

    def start(
        self,
        application_database_url: str,
        ready: oidc.Ready,
        *,
        bff_internal_secret: str | None = None,
    ) -> dict[str, str]:
        if self._attempted or self._closed:
            raise BillingRuntimeError("Billing runtime cannot be started again")
        self._attempted = True
        if (
            bff_internal_secret is not None
            and re.fullmatch(r"[!-~]{32,4096}", bff_internal_secret) is None
        ):
            raise BillingRuntimeError("Billing BFF internal identity invalid")
        values = []
        for provided in (bff_internal_secret, None, None):
            value = provided if provided is not None else secrets.token_hex(32)
            self.credentials.add(value)
            values.append(value)
        if len(set(values)) != 3:
            raise BillingRuntimeError("Billing service credentials are not distinct")
        self.internal_secret, self.service_token, self.operator_secret = values
        database_url = billing_owner_database_url(application_database_url)
        port = runtime.free_port()
        environment = {
            **self.node_environment,
            "NODE_ENV": "development",
            "DATABASE_URL": database_url,
            "BILLING_HOST": "127.0.0.1",
            "BILLING_PORT": str(port),
            "BILLING_AUTH_MODE": "jwks",
            "BILLING_AUTH_JWKS_URL": ready.base_url + "/iam/jwks",
            "BILLING_AUTH_JWT_ISSUER": ready.issuer_url,
            "BILLING_AUTH_JWT_AUDIENCE": BILLING_AUDIENCE,
            "INTERNAL_SERVICE_SECRET": self.internal_secret,
            "BILLING_BFF_SERVICE_TOKEN": self.service_token,
            "BILLING_OPERATOR_PROXY_SECRET": self.operator_secret,
            "BILLING_ENABLED_PROVIDERS": "",
        }
        try:
            for task, timeout in (("build", 120), ("db:apply-schema", 180)):
                # A failed command cleanup cannot be claimed quiescent merely
                # because no long-lived owner process was registered yet.
                self.quiescent = False
                result = runtime.run_owned_command(
                    [str(self.node.parent / "corepack"), "pnpm", task],
                    cwd=BILLING,
                    env=environment,
                    log=self.log,
                    timeout=timeout,
                )
                self.quiescent = True
                if result != 0:
                    raise BillingRuntimeError(
                        "Billing build or owner installation failed"
                    )
            with local_chat_runtime.registration_guard():
                self.process = subprocess.Popen(
                    [str(self.node), str(BILLING / "dist/src/main.js")],
                    cwd=BILLING,
                    env=environment,
                    stdin=subprocess.DEVNULL,
                    stdout=self.log,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
                self.quiescent = False
            base = f"http://127.0.0.1:{port}"
            wait_billing_ready(base, self.process)
        except BillingRuntimeError:
            raise
        except Exception:  # noqa: BLE001 -- sanitize foreign lifecycle errors and preserve uncertain resources.
            raise BillingRuntimeError("Billing startup failed") from None
        return {
            "KOKORO_BILLING_BASE_URL": base,
            "KOKORO_INTERNAL_SECRET_BFF": self.internal_secret,
            "KOKORO_BILLING_BFF_SERVICE_TOKEN": self.service_token,
        }

    def require_alive(self) -> None:
        if self.process is None or self.process.poll() is not None:
            raise BillingRuntimeError("Owned Billing process exited")

    def close(self) -> list[str]:
        if self._closed:
            return []
        if self.process is not None:
            try:
                runtime.stop_owned_process(self.process)
                self.quiescent = self.process.poll() is not None
            except Exception:  # noqa: BLE001 -- sanitize foreign lifecycle errors and preserve uncertain resources.
                self.quiescent = False
            if not self.quiescent:
                return ["Billing process cleanup", "Billing dependencies preserved"]
        elif not self.quiescent:
            return ["Billing command cleanup requires reconciliation"]
        self._closed = True
        return []
