"""Local IAM admission wire fixture; not a real IAM service or identity source."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import re
import socket
from datetime import datetime, timedelta, timezone
from threading import Thread
from types import MappingProxyType
from typing import Any
from urllib.parse import urlsplit
from uuid import uuid4


_PATH = "/internal/v1/session-authorizations/verify"
_REQUEST_ID = re.compile(r"[A-Za-z0-9_-]{1,128}\Z")


@dataclass(frozen=True, slots=True)
class AdmissionIdentity:
    tenant_id: str
    user_id: str
    session_id: str
    client_id: str

    def __post_init__(self) -> None:
        if not all((self.tenant_id, self.user_id, self.session_id, self.client_id)):
            raise ValueError("IAM fixture identities must be nonempty")


class _Server(ThreadingHTTPServer):
    daemon_threads = False
    block_on_close = True
    allow_reuse_address = False

    def __init__(
        self,
        identities: Mapping[str, AdmissionIdentity],
        service_tokens: set[str] | frozenset[str] = frozenset(),
    ) -> None:
        self.identities = MappingProxyType(dict(identities))
        self.service_tokens = frozenset(service_tokens)
        super().__init__(("127.0.0.1", 0), _Handler)

    def get_request(self) -> tuple[socket.socket, object]:
        connection, address = super().get_request()
        connection.settimeout(2)
        return connection, address


class _Handler(BaseHTTPRequestHandler):
    server: _Server
    protocol_version = "HTTP/1.1"

    def log_message(self, _format: str, *_args: object) -> None:
        # Bearer tokens are deliberately never written to fixture logs.
        return

    def _respond(self, status: int, payload: dict[str, Any] | None) -> None:
        raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        request_id = self.headers.get("x-request-id", "")
        if not _REQUEST_ID.fullmatch(request_id):
            request_id = str(uuid4())
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("cache-control", "no-store")
        self.send_header("x-request-id", request_id)
        self.send_header("content-length", str(len(raw)))
        self.send_header("connection", "close")
        self.end_headers()
        self.wfile.write(raw)
        self.close_connection = True

    def _error(self, status: int, code: str) -> None:
        self._respond(
            status,
            {
                "error": {
                    "code": code,
                    "message": "IAM admission fixture rejected request",
                    "retryable": False,
                    "details": [],
                }
            },
        )

    def do_POST(self) -> None:
        if self.path == "/internal/v1/authorization/check":
            self._authorization_check()
            return
        if self.path != _PATH:
            self._error(404, "NOT_FOUND")
            return
        if (
            self.headers.get("content-length") != "0"
            or self.headers.get("transfer-encoding") is not None
        ):
            self._error(400, "INVALID_ARGUMENT")
            return
        values = self.headers.get_all("authorization", [])
        if len(values) != 1 or not values[0].startswith("Bearer "):
            self._error(401, "UNAUTHENTICATED")
            return
        token = values[0][7:]
        if not token or any(character.isspace() for character in token) or "," in token:
            self._error(401, "UNAUTHENTICATED")
            return
        identity = self.server.identities.get(token)
        if identity is None:
            self._error(401, "UNAUTHENTICATED")
            return
        self._respond(
            200,
            {
                "data": {
                    "allowed": True,
                    "tenant_id": identity.tenant_id,
                    "user_id": identity.user_id,
                    "session_id": identity.session_id,
                    "client_id": identity.client_id,
                }
            },
        )

    def _authorization_check(self) -> None:
        authorization = self.headers.get("authorization", "")
        actor = self.headers.get("x-kokoro-actor-id", "")
        if (
            not authorization.startswith("Bearer ")
            or authorization[7:] not in self.server.service_tokens
        ):
            self._error(401, "UNAUTHENTICATED")
            return
        identity = next(
            (
                identity
                for identity in self.server.identities.values()
                if identity.user_id == actor
            ),
            None,
        )
        if identity is None:
            self._error(403, "PERMISSION_DENIED")
            return
        length = self.headers.get("content-length")
        if length is None or self.headers.get("transfer-encoding") is not None:
            self._error(400, "INVALID_ARGUMENT")
            return
        try:
            body = self.rfile.read(int(length))
            request = json.loads(body)
        except (ValueError, json.JSONDecodeError):
            self._error(400, "INVALID_ARGUMENT")
            return
        if (
            not isinstance(request, dict)
            or request.get("resource") != "tenant"
            or request.get("action") != "read"
        ):
            self._error(400, "INVALID_ARGUMENT")
            return
        self._respond(
            200,
            {
                "data": {
                    "allowed": True,
                    "tenant_id": identity.tenant_id,
                    "subject_id": identity.user_id,
                    "decision_source": "current_membership",
                }
            },
        )

    def do_GET(self) -> None:
        if urlsplit(self.path).path != "/iam/get-session":
            self._error(405, "INVALID_ARGUMENT")
            return
        cookie = self.headers.get("cookie", "")
        match = re.fullmatch(
            r"(?:__Secure-)?kokoro-issuer\.session_token=([^;\s]+)", cookie
        )
        identity = self.server.identities.get(match.group(1)) if match else None
        if identity is None:
            self._respond(200, None)
            return
        now = datetime.now(timezone.utc)
        created = now - timedelta(minutes=1)
        expires = now + timedelta(hours=1)
        self._respond(
            200,
            {
                "session": {
                    "id": identity.session_id,
                    "expiresAt": expires.isoformat().replace("+00:00", "Z"),
                    "token": match.group(1),
                    "createdAt": created.isoformat().replace("+00:00", "Z"),
                    "updatedAt": created.isoformat().replace("+00:00", "Z"),
                    "ipAddress": None,
                    "userAgent": None,
                    "userId": identity.user_id,
                    "activeOrganizationId": identity.tenant_id,
                },
                "user": {
                    "id": identity.user_id,
                    "name": identity.user_id,
                    "email": identity.user_id + "@scheduler-smoke.local",
                    "emailVerified": True,
                    "image": None,
                    "createdAt": created.isoformat().replace("+00:00", "Z"),
                    "updatedAt": created.isoformat().replace("+00:00", "Z"),
                    "platformAdmin": False,
                },
            },
        )


@contextmanager
def iam_admission_stub(
    identities: Mapping[str, AdmissionIdentity],
    *,
    service_tokens: set[str] | frozenset[str] = frozenset(),
) -> Iterator[str]:
    """Serve an immutable token map on loopback and join every owned thread."""
    if not identities or any(
        not token or not isinstance(identity, AdmissionIdentity)
        for token, identity in identities.items()
    ):
        raise ValueError("IAM fixture requires a nonempty fixed token map")
    server = (
        _Server(identities, service_tokens) if service_tokens else _Server(identities)
    )
    thread = Thread(target=server.serve_forever, name="bff-iam-admission-stub")
    try:
        thread.start()
    except BaseException:
        if thread.is_alive():
            server.shutdown()
            thread.join(timeout=5)
        server.server_close()
        raise
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        if thread.is_alive():
            raise RuntimeError("IAM admission fixture thread did not stop")
