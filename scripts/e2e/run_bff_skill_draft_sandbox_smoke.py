#!/usr/bin/env python3
"""Owned IAM -> BFF -> Platform Skill draft pre-activation smoke.

The process launcher is intentionally gated on clean Root-pinned owner sources.  The
pure protocol functions in this module are exercised while the IAM and BFF
candidates are still moving; no shared service is started by importing the module.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import argparse
from datetime import datetime, timedelta, timezone
import getpass
from enum import Enum
import hashlib
import http.client
import io
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import signal
import socket
import stat
import subprocess
import tempfile
import threading
import time
import zipfile
from typing import Callable, Iterator, Protocol
from uuid import uuid4
from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit


ROOT = Path(__file__).resolve().parents[2]
OWNERS = {
    "iam": ROOT / "apps/kokoro-iam",
    "bff": ROOT / "apps/kokoro-bff",
    "platform": ROOT / "apps/kokoro-capability",
    "storage": ROOT / "apps/kokoro-storage",
}
LOCAL_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})


class SmokeError(RuntimeError):
    """A bounded diagnostic that contains no credential material."""


class TerminationRequested(SmokeError):
    """SIGTERM requested bounded owned-resource cleanup."""


class Phase(str, Enum):
    IAM_READY = "iam_ready"
    SCHEMA = "schema"
    OWNER_START = "owner_start"
    DEFAULT_OFF = "default_off"
    CANDIDATE_CREATE = "candidate_create"
    CANDIDATE_REPLAY_CONFLICT = "candidate_replay_conflict"
    CANDIDATE_PACKAGE_GET = "candidate_package_get"
    CANDIDATE_PACKAGE_BEGIN = "candidate_package_begin"
    CANDIDATE_SIGNED_PUT = "candidate_signed_put"
    CANDIDATE_PACKAGE_COMPLETE = "candidate_package_complete"
    CANDIDATE_PACKAGE_VALIDATE = "candidate_package_validate"
    PACKAGE_REFERENCE = "package_reference"
    INVENTORY = "inventory"
    REVOKE = "revoke"
    CLEANUP = "cleanup"


@dataclass(frozen=True, slots=True)
class CatalogCredential:
    client_id: str
    client_secret: str


@dataclass(frozen=True, slots=True)
class SandboxReady:
    base_url: str
    database_name: str
    redis_prefix: str
    tenant_id: str
    subject_id: str
    access_token: str
    catalog: CatalogCredential
    resource_server: CatalogCredential
    execution_authorization: CatalogCredential
    web_client_secret: str
    user_password: str

    @property
    def secrets(self) -> tuple[str, ...]:
        return (
            self.access_token,
            self.catalog.client_secret,
            self.resource_server.client_secret,
            self.execution_authorization.client_secret,
            self.web_client_secret,
            self.user_password,
        )


def _nonempty(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise SmokeError(f"IAM ready {label} invalid")
    return value


def _credential(value: object, label: str) -> CatalogCredential:
    if not isinstance(value, dict) or set(value) != {"client_id", "client_secret"}:
        raise SmokeError(f"IAM ready {label} invalid")
    return CatalogCredential(
        _nonempty(value["client_id"], f"{label} client id"),
        _nonempty(value["client_secret"], f"{label} client secret"),
    )


def require_sandbox_ready(record: object) -> SandboxReady:
    """Strictly accept the IAM opt-in protocol without copying owner policy."""
    base = {
        "kind",
        "base_url",
        "database_name",
        "redis_prefix",
        "issuer_url",
        "client_id",
        "client_secret",
        "redirect_uri",
        "post_logout_redirect_uri",
        "email",
        "password",
        "tenant_id",
        "skill_sandbox",
    }
    if (
        not isinstance(record, dict)
        or set(record) != base
        or record.get("kind") != "ready"
    ):
        raise SmokeError("IAM skill sandbox ready protocol invalid")
    sandbox = record.get("skill_sandbox")
    if not isinstance(sandbox, dict) or set(sandbox) != {
        "access_token",
        "subject_id",
        "catalog_client",
        "resource_server_basic",
        "execution_authorization_client",
    }:
        raise SmokeError("IAM skill sandbox evidence invalid")
    execution = sandbox["execution_authorization_client"]
    if not isinstance(execution, dict) or set(execution) != {
        "client_id",
        "client_secret",
    }:
        raise SmokeError("IAM execution authorization client invalid")
    base_url = _nonempty(record["base_url"], "base URL")
    parsed = urlsplit(base_url)
    if (
        parsed.scheme != "http"
        or parsed.hostname not in LOCAL_HOSTS
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise SmokeError("IAM ready base URL must be loopback HTTP origin")
    if parsed.port in {None, 3310}:
        raise SmokeError("IAM ready port missing or reserved")
    database = _nonempty(record["database_name"], "database name")
    if re.fullmatch(r"[a-z][a-z0-9_]{2,62}", database) is None:
        raise SmokeError("IAM ready database name invalid")
    return SandboxReady(
        base_url,
        database,
        _nonempty(record["redis_prefix"], "Redis prefix"),
        _nonempty(record["tenant_id"], "tenant id"),
        _nonempty(sandbox["subject_id"], "subject id"),
        _nonempty(sandbox["access_token"], "access token"),
        _credential(sandbox["catalog_client"], "catalog client"),
        _credential(sandbox["resource_server_basic"], "resource server"),
        _credential(execution, "execution authorization client"),
        _nonempty(record["client_secret"], "Web client secret"),
        _nonempty(record["password"], "user password"),
    )


def require_revoke_result(record: object) -> None:
    if record != {"kind": "result", "command": "revoke-user-session", "status": "ok"}:
        raise SmokeError("IAM session revoke protocol invalid")


@contextmanager
def credential_file(payload: dict[str, object]) -> Iterator[Path]:
    """Write the BFF owner-only credential using create-exclusive mode 0600."""
    directory = Path(tempfile.mkdtemp(prefix="kokoro-skill-draft-"))
    path = directory / "platform-credential.json"
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, separators=(",", ":"), sort_keys=True)
            stream.write("\n")
        if stat.S_IMODE(path.stat().st_mode) != 0o600:
            raise SmokeError("credential file mode invalid")
        yield path
    finally:
        try:
            path.unlink(missing_ok=True)
            directory.rmdir()
        except OSError:
            pass


def frozen_sources(
    run: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict[str, str]:
    """Reject dirty or non-gitlink candidates before any infrastructure side effect."""
    result: dict[str, str] = {}
    for name, path in OWNERS.items():
        status = run(
            ["git", "-C", str(path), "status", "--porcelain"],
            text=True,
            capture_output=True,
            check=True,
        ).stdout
        if status:
            raise SmokeError(f"{name} source is not frozen")
        sha = run(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            text=True,
            capture_output=True,
            check=True,
        ).stdout.strip()
        tree = run(
            ["git", "-C", str(ROOT), "ls-tree", "HEAD", f"apps/{path.name}"],
            text=True,
            capture_output=True,
            check=True,
        ).stdout
        if not tree.startswith(f"160000 commit {sha}\t"):
            raise SmokeError(f"{name} source is not pinned by Root HEAD")
        result[name] = sha
    return result


class JsonRequest(Protocol):
    def __call__(
        self, *, body: dict[str, object], key: str, token: str
    ) -> tuple[int, dict[str, object]]: ...


class CountingTcpProxy:
    """Count BFF's Platform TCP connections while transparently forwarding bytes."""

    def __init__(self, target_port: int) -> None:
        self._target = target_port
        self._listener = socket.socket()
        self._listener.bind(("127.0.0.1", 0))
        self._listener.listen()
        self._listener.settimeout(0.2)
        self.port = int(self._listener.getsockname()[1])
        if self.port == 3310:
            self._listener.close()
            raise SmokeError("owned proxy selected reserved port")
        self.count = 0
        self._closed = threading.Event()
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    def _serve(self) -> None:
        while not self._closed.is_set():
            try:
                client, _ = self._listener.accept()
            except (TimeoutError, OSError):
                continue
            self.count += 1
            threading.Thread(target=self._bridge, args=(client,), daemon=True).start()

    def _bridge(self, client: socket.socket) -> None:
        try:
            upstream = socket.create_connection(("127.0.0.1", self._target), timeout=3)
        except OSError:
            client.close()
            return

        def copy(source: socket.socket, destination: socket.socket) -> None:
            try:
                while data := source.recv(65536):
                    destination.sendall(data)
            except OSError:
                pass
            finally:
                try:
                    destination.shutdown(socket.SHUT_WR)
                except OSError:
                    pass

        a = threading.Thread(target=copy, args=(client, upstream), daemon=True)
        a.start()
        copy(upstream, client)
        a.join(timeout=1)
        client.close()
        upstream.close()

    def close(self) -> None:
        self._closed.set()
        self._listener.close()
        self._thread.join(timeout=2)


def install_sigterm_cleanup_handler() -> Callable[[], None]:
    """Raise once into the runner finally and restore the caller's handler later."""
    previous = signal.getsignal(signal.SIGTERM)

    def terminate(_signum: int, _frame: object) -> None:
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        raise TerminationRequested("runner termination requested")

    signal.signal(signal.SIGTERM, terminate)

    def restore() -> None:
        signal.signal(signal.SIGTERM, previous)

    return restore


def local_http_origin(value: str, label: str) -> str:
    parsed = urlsplit(value)
    try:
        port = parsed.port
    except ValueError:
        raise SmokeError(f"{label} origin invalid") from None
    if (
        parsed.scheme != "http"
        or parsed.hostname not in LOCAL_HOSTS
        or port in {None, 3310}
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise SmokeError(f"{label} must be a local non-3310 HTTP origin")
    return value.rstrip("/")


def _draft(
    body: dict[str, object], expected_status: int
) -> tuple[str | None, str | None, bool | None, str | None]:
    if expected_status == 201:
        if set(body) != {"data"} or not isinstance(body["data"], dict):
            raise SmokeError("BFF Skill draft success response invalid")
        data = body["data"]
        if (
            set(data) != {"skill_id", "series_id", "revision", "status", "replayed"}
            or not isinstance(data["skill_id"], str)
            or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,190}", data["skill_id"])
            is None
            or not isinstance(data["series_id"], str)
            or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,190}", data["series_id"])
            is None
            or data["revision"] != 1
            or data["status"] != "draft"
            or type(data["replayed"]) is not bool
        ):
            raise SmokeError("BFF Skill draft projection invalid")
        return data["skill_id"], data["series_id"], data["replayed"], None
    error = body.get("error")
    if not isinstance(error, dict) or not isinstance(error.get("code"), str):
        raise SmokeError("BFF Skill draft error response invalid")
    return None, None, None, error["code"]


def public_error_code(value: object) -> str:
    """Bound diagnostics to a stable non-secret error-code alphabet."""
    if isinstance(value, str) and re.fullmatch(r"[a-z][a-z0-9_]{0,63}", value):
        return value
    return "unknown"


def require_public_package_get(status: int, body: object, skill_id: str) -> None:
    """The fresh draft has no package attempt; reject stale or expanded public data."""
    if status != 200 or body != {
        "data": {"skill_id": skill_id, "attempt_epoch": "0", "phase": "none"}
    }:
        raise SmokeError("BFF current Skill package GET projection invalid")


def require_public_package_pending(
    status: int,
    body: object,
    skill_id: str,
    attempt_id: str,
    upload_id: str,
    attempt_epoch: str,
) -> None:
    """Observe the same owner attempt through BFF's non-signing recovery read."""
    if status != 200 or body != {
        "data": {
            "skill_id": skill_id,
            "attempt_epoch": attempt_epoch,
            "phase": "upload_pending",
            "attempt_id": attempt_id,
            "upload_id": upload_id,
        }
    }:
        raise SmokeError("BFF current Skill package pending projection invalid")


def require_public_package_uploaded(
    status: int,
    body: object,
    skill_id: str,
    attempt_id: str,
    upload_id: str,
    attempt_epoch: str,
) -> None:
    if status != 200 or body != {
        "data": {
            "skill_id": skill_id,
            "attempt_epoch": attempt_epoch,
            "phase": "uploaded",
            "attempt_id": attempt_id,
            "upload_id": upload_id,
        }
    }:
        raise SmokeError("BFF current Skill package uploaded projection invalid")


def require_public_package_validated(
    status: int,
    body: object,
    skill_id: str,
    attempt_id: str,
    upload_id: str,
    attempt_epoch: str,
) -> None:
    if status != 200 or body != {
        "data": {
            "skill_id": skill_id,
            "attempt_epoch": attempt_epoch,
            "phase": "validated",
            "attempt_id": attempt_id,
            "upload_id": upload_id,
        }
    }:
        raise SmokeError("BFF current Skill package validated projection invalid")


def require_public_package_aborted(
    status: int,
    body: object,
    skill_id: str,
    attempt_id: str,
    upload_id: str,
    attempt_epoch: str,
) -> None:
    if status != 200 or not isinstance(body, dict) or set(body) != {"data"}:
        raise SmokeError("BFF current Skill package aborted projection invalid")
    data = body["data"]
    if not isinstance(data, dict) or set(data) not in (
        {"skill_id", "attempt_epoch", "phase", "attempt_id"},
        {"skill_id", "attempt_epoch", "phase", "attempt_id", "upload_id"},
    ):
        raise SmokeError("BFF current Skill package aborted fields invalid")
    if (
        data["skill_id"] != skill_id
        or data["attempt_epoch"] != attempt_epoch
        or data["phase"] != "aborted"
        or data["attempt_id"] != attempt_id
        or (
            "upload_id" in data
            and (
                not isinstance(data["upload_id"], str)
                or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,190}", data["upload_id"])
                is None
                or data["upload_id"] != upload_id
            )
        )
    ):
        raise SmokeError("BFF current Skill package aborted state invalid")


def require_public_package_begin(
    status: int, body: object, skill_id: str, approved_origin: str
) -> dict[str, object]:
    """Reject expanded or off-origin owner references before a real signed PUT."""
    if status != 201 or not isinstance(body, dict) or set(body) != {"data"}:
        raise SmokeError("BFF Skill package Begin response invalid")
    data = body["data"]
    if not isinstance(data, dict) or set(data) != {
        "skill_id",
        "attempt_id",
        "attempt_epoch",
        "upload_id",
        "transfer_reference",
        "replayed",
    }:
        raise SmokeError("BFF Skill package Begin data invalid")
    typed_id = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,190}\Z")
    if (
        data["skill_id"] != skill_id
        or any(
            not isinstance(data[name], str) or typed_id.fullmatch(data[name]) is None
            for name in ("attempt_id", "upload_id")
        )
        or not isinstance(data["attempt_epoch"], str)
        or re.fullmatch(r"[1-9][0-9]{0,19}", data["attempt_epoch"]) is None
        or int(data["attempt_epoch"]) > 18_446_744_073_709_551_615
        or type(data["replayed"]) is not bool
    ):
        raise SmokeError("BFF Skill package Begin attempt invalid")
    reference = data["transfer_reference"]
    if not isinstance(reference, dict) or set(reference) != {
        "url",
        "method",
        "required_headers",
        "expires_at",
    }:
        raise SmokeError("BFF Skill package Begin transfer invalid")
    if (
        reference["method"] != "PUT"
        or reference["required_headers"] != {"content-type": "application/zip"}
        or not isinstance(reference["url"], str)
        or not isinstance(reference["expires_at"], str)
    ):
        raise SmokeError("BFF Skill package Begin signed PUT invalid")
    try:
        parsed = urlsplit(reference["url"])
        expected = urlsplit(approved_origin)
        expires_at = datetime.fromisoformat(
            reference["expires_at"].replace("Z", "+00:00")
        )
    except (TypeError, ValueError):
        raise SmokeError("BFF Skill package Begin reference invalid") from None
    if (
        parsed.scheme != expected.scheme
        or parsed.netloc != expected.netloc
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
        or not parsed.path.startswith("/")
        or not parsed.query
        or expires_at.tzinfo is None
    ):
        raise SmokeError("BFF Skill package Begin reference origin invalid")
    remaining = expires_at - datetime.now(timezone.utc)
    if not timedelta(0) < remaining <= timedelta(minutes=15):
        raise SmokeError("BFF Skill package Begin reference expiry invalid")
    return data


def require_public_package_complete(
    status: int,
    body: object,
    skill_id: str,
    attempt_id: str,
    upload_id: str,
    attempt_epoch: str,
    content_sha256: str,
) -> dict[str, object]:
    """Complete may expose scan status, but never owner Asset or signed URL."""
    if status != 200 or not isinstance(body, dict) or set(body) != {"data"}:
        raise SmokeError("BFF Skill package Complete response invalid")
    data = body["data"]
    if not isinstance(data, dict) or set(data) != {
        "skill_id",
        "attempt_id",
        "attempt_epoch",
        "upload_id",
        "phase",
        "replayed",
        "content_sha256",
        "scan_state",
    }:
        raise SmokeError("BFF Skill package Complete data invalid")
    if (
        data["skill_id"] != skill_id
        or data["attempt_id"] != attempt_id
        or data["upload_id"] != upload_id
        or data["attempt_epoch"] != attempt_epoch
        or re.fullmatch(r"[1-9][0-9]{0,19}", attempt_epoch) is None
        or int(attempt_epoch) > 18_446_744_073_709_551_615
        or data["content_sha256"] != content_sha256
        or data["phase"] != "uploaded"
        or data["scan_state"] not in {"clean", "pending", "unknown"}
        or type(data["replayed"]) is not bool
    ):
        raise SmokeError("BFF Skill package Complete projection invalid")
    return data


def require_public_skill_validate(
    status: int,
    body: object,
    skill_id: str,
    series_id: str,
    content_sha256: str,
) -> dict[str, object]:
    """Validate projects an owner-verified ZIP result, never a publication."""
    if status != 200 or not isinstance(body, dict) or set(body) != {"data"}:
        raise SmokeError("BFF Skill Validate response invalid")
    data = body["data"]
    if not isinstance(data, dict) or set(data) != {
        "skill_id",
        "series_id",
        "valid",
        "content_digest",
        "manifest_identity",
        "replayed",
    }:
        raise SmokeError("BFF Skill Validate data invalid")
    if (
        data["skill_id"] != skill_id
        or data["series_id"] != series_id
        or data["valid"] is not True
        or data["content_digest"] != content_sha256
        or not isinstance(data["manifest_identity"], str)
        or re.fullmatch(r"zip-v1:sha256:[a-f0-9]{64}", data["manifest_identity"])
        is None
        or type(data["replayed"]) is not bool
    ):
        raise SmokeError("BFF Skill Validate projection invalid")
    return data


def require_package_response_headers(
    headers: list[tuple[str, str]], request_id: str, operation: str
) -> None:
    """A response must correlate to this request, not merely contain an ID."""
    values = [value for name, value in headers if name.lower() == "x-request-id"]
    cache = [value for name, value in headers if name.lower() == "cache-control"]
    if values != [request_id] or cache != ["no-store"]:
        raise SmokeError(f"BFF package {operation} response headers invalid")


def signed_reference_secrets(url: str) -> tuple[str, ...]:
    """Keep short-lived URL/query material in the in-memory redaction inventory."""
    query = urlsplit(url).query
    values = [url, query]
    for name, value in parse_qsl(query, keep_blank_values=True):
        if any(
            marker in name.lower() for marker in ("signature", "credential", "token")
        ):
            values.append(f"{name}={value}")
            if len(value) >= 8:
                values.append(value)
    return tuple(value for value in values if value)


def exercise_http_contract(
    request: JsonRequest,
    ready: SandboxReady,
    observe: Callable[[Phase], None] = lambda _phase: None,
) -> dict[str, object]:
    """Exercise replay/conflict/revoke ordering through injected real HTTP calls."""
    command = {
        "display_name": "Sandbox skill",
        "summary": "sandbox draft",
        "tags": ["sandbox"],
    }
    key = "skill-draft-sandbox-key"
    observe(Phase.CANDIDATE_CREATE)
    status, body = request(body=command, key=key, token=ready.access_token)
    first, series, replayed, code = _draft(body, status)
    if status != 201 or replayed is not False:
        raise SmokeError(
            f"first Skill draft was not created (status={status}, code={public_error_code(code)})"
        )
    observe(Phase.CANDIDATE_REPLAY_CONFLICT)
    status, body = request(body=command, key=key, token=ready.access_token)
    second, replay_series, replayed, _ = _draft(body, status)
    if (
        status != 201
        or second != first
        or replay_series != series
        or replayed is not True
    ):
        raise SmokeError("Skill draft replay drift")
    status, body = request(
        body={**command, "summary": "different"}, key=key, token=ready.access_token
    )
    _, _, _, code = _draft(body, status)
    if status != 409 or code != "skill_idempotency_conflict":
        raise SmokeError("Skill draft conflict drift")
    return {"skill_id": first, "series_id": series, "key": key, "body": command}


def safe_summary(
    error: BaseException | None, secrets: tuple[str, ...] = ()
) -> dict[str, object]:
    if error is None:
        return {
            "status": "PASS",
            "resources": "clean",
            "platform_skill_count": 2,
            "platform_receipt_count": 30,
            "platform_publish_event_count": 1,
            "platform_package_begin": "PASS",
            "platform_package_complete": "PASS",
            "platform_package_infected": "PASS",
            "platform_package_validate": "PASS",
            "platform_package_bad_zip": "PASS",
            "platform_publish": "PASS",
            "platform_publish_replay": "PASS",
            "platform_publish_negative": "PASS",
            "bff_skill_package_get": "PASS",
            "bff_skill_package_get_published": "PASS",
            "bff_skill_package_get_revoked": "PASS",
            "bff_skill_package_begin": "PASS",
            "bff_skill_package_begin_replay": "PASS",
            "bff_skill_package_begin_replace": "PASS",
            "bff_skill_package_signed_put": "PASS",
            "bff_skill_package_begin_revoked": "PASS",
            "bff_skill_package_complete": "PASS",
            "bff_skill_package_complete_replay": "PASS",
            "bff_skill_package_complete_infected": "PASS",
            "bff_skill_package_complete_recovery": "PASS",
            "bff_skill_package_complete_revoked": "PASS",
            "bff_skill_validate": "PASS",
            "bff_skill_validate_bad_zip": "PASS",
            "bff_skill_validate_recovery": "PASS",
            "bff_skill_validate_replay": "PASS",
            "bff_skill_validate_stale_attempt": "PASS",
            "bff_skill_validate_revoked": "PASS",
        }
    detail = str(error) if isinstance(error, SmokeError) else "smoke execution failed"
    if any(secret and secret in detail for secret in secrets):
        detail = "smoke execution failed"
    return {"status": "FAIL", "error": detail}


def platform_package_probe_env(
    base: dict[str, str],
    platform_node: Path,
    storage_base: str,
    platform_base: str,
    iam_base: str,
    service_secret: str,
    ready: SandboxReady,
    skill_id: str,
) -> dict[str, str]:
    """Give the owner probe only current Skill and short-lived owner boundary inputs."""
    if not skill_id or skill_id != skill_id.strip():
        raise SmokeError("current Skill id invalid for Storage package probe")
    return {
        **base,
        "PATH": f"{platform_node.parent}:{base['PATH']}",
        "KOKORO_STORAGE_URL": storage_base,
        "KOKORO_PLATFORM_STORAGE_SERVICE_CREDENTIAL": service_secret,
        "KOKORO_SMOKE_PLATFORM_URL": platform_base,
        "KOKORO_SMOKE_IAM_URL": iam_base,
        "KOKORO_SMOKE_CATALOG_CLIENT_ID": ready.catalog.client_id,
        "KOKORO_SMOKE_CATALOG_CLIENT_SECRET": ready.catalog.client_secret,
        "KOKORO_SMOKE_TENANT_ID": ready.tenant_id,
        "KOKORO_SMOKE_SUBJECT_ID": ready.subject_id,
        "KOKORO_SMOKE_SKILL_ID": skill_id,
    }


def owner_database_url(admin_url: str, database: str, schema: str) -> str:
    parsed = urlsplit(admin_url)
    if (
        parsed.scheme not in {"postgres", "postgresql"}
        or parsed.hostname not in LOCAL_HOSTS
    ):
        raise SmokeError("local PostgreSQL admin URL required")
    if re.fullmatch(r"[a-z][a-z0-9_]{2,62}", database) is None or schema not in {
        "kokoro_bff",
        "kokoro_platform",
        "kokoro_storage",
    }:
        raise SmokeError("owned database or schema invalid")
    from urllib.parse import urlunsplit

    return urlunsplit(
        (parsed.scheme, parsed.netloc, f"/{database}", f"schema={schema}", "")
    )


def normalized_postgres_admin_url(
    raw: str, os_user: Callable[[], str] = getpass.getuser
) -> str:
    """Add the current OS user only when the local URL omitted a database user."""
    parsed = urlsplit(raw)
    if (
        parsed.scheme not in {"postgres", "postgresql"}
        or parsed.hostname not in LOCAL_HOSTS
    ):
        raise SmokeError("local PostgreSQL admin URL required")
    if parsed.username is not None:
        if not parsed.username:
            raise SmokeError("PostgreSQL user invalid")
        return raw
    user = os_user()
    if (
        not isinstance(user, str)
        or not user
        or len(user) > 128
        or any(ord(character) < 0x21 or ord(character) == 0x7F for character in user)
    ):
        raise SmokeError("current OS user is not a valid PostgreSQL user")
    return urlunsplit(
        (
            parsed.scheme,
            f"{quote(user, safe='')}@{parsed.netloc}",
            parsed.path,
            parsed.query,
            parsed.fragment,
        )
    )


def platform_credential_payloads(
    ready: SandboxReady,
) -> tuple[dict[str, object], list[dict[str, object]], list[dict[str, object]]]:
    """Project IAM handles into the three owner-defined credential snapshots."""
    common = {"generation": 1, "credentialRefVersion": "sandbox-v1"}
    resource = {
        **common,
        "clientId": ready.resource_server.client_id,
        "clientSecret": ready.resource_server.client_secret,
    }
    execution = [
        {
            **common,
            "tenantId": ready.tenant_id,
            "clientId": ready.execution_authorization.client_id,
            "clientSecret": ready.execution_authorization.client_secret,
            "resource": "https://kokoro.dev/resources/iam-internal",
            "scope": "iam:execution-authorization.verify",
        }
    ]
    catalog = [
        {
            **common,
            "tenantId": ready.tenant_id,
            "clientId": ready.catalog.client_id,
            "clientSecret": ready.catalog.client_secret,
            "resource": "https://kokoro.dev/resources/platform-internal",
            "scope": "platform:skill-catalog.manage",
        }
    ]
    return resource, execution, catalog


@contextmanager
def credential_files(directory: Path, ready: SandboxReady) -> Iterator[dict[str, Path]]:
    payloads = platform_credential_payloads(ready)
    names = ("resource-server.json", "tenant-execution.json", "bff-catalog.json")
    paths: dict[str, Path] = {}
    try:
        for name, payload in zip(names, payloads, strict=True):
            path = directory / name
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(payload, stream, separators=(",", ":"), sort_keys=True)
            paths[name] = path
        yield paths
    finally:
        for path in paths.values():
            path.unlink(missing_ok=True)


def _http_json(
    base: str, path: str, *, token: str, secret: str, key: str, body: dict[str, object]
) -> tuple[int, dict[str, object]]:
    parsed = urlsplit(base)
    connection = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=8)
    encoded = json.dumps(body, separators=(",", ":")).encode()
    request_id = "skill-sandbox-" + secrets.token_hex(8)
    try:
        connection.request(
            "POST",
            path,
            body=encoded,
            headers={
                "authorization": "Bearer " + token,
                "x-kokoro-service": "web-bff",
                "x-kokoro-internal-secret": secret,
                "x-kokoro-request-id": request_id,
                "idempotency-key": key,
                "content-type": "application/json",
            },
        )
        response = connection.getresponse()
        raw = response.read(1_048_577)
        headers = response.getheaders()
    finally:
        connection.close()
    if len(raw) > 1_048_576:
        raise SmokeError("BFF response too large")
    if path.endswith(("/package-upload", "/package-upload/complete", "/validate")):
        require_package_response_headers(
            headers,
            request_id,
            "Validate"
            if path.endswith("/validate")
            else "Complete"
            if path.endswith("/complete")
            else "Begin",
        )
    try:
        value = json.loads(raw)
    except (ValueError, UnicodeError):
        raise SmokeError("BFF response is not JSON") from None
    if not isinstance(value, dict):
        raise SmokeError("BFF response envelope invalid")
    return response.status, value


def _http_get_json(
    base: str, path: str, *, token: str, secret: str
) -> tuple[int, dict[str, object]]:
    parsed = urlsplit(base)
    connection = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=8)
    request_id = "skill-sandbox-" + secrets.token_hex(8)
    try:
        connection.request(
            "GET",
            path,
            headers={
                "authorization": "Bearer " + token,
                "x-kokoro-service": "web-bff",
                "x-kokoro-internal-secret": secret,
                "x-kokoro-request-id": request_id,
            },
        )
        response = connection.getresponse()
        raw = response.read(1_048_577)
        headers = response.getheaders()
    finally:
        connection.close()
    if len(raw) > 1_048_576:
        raise SmokeError("BFF package GET response too large")
    require_package_response_headers(headers, request_id, "GET")
    try:
        value = json.loads(raw)
    except (ValueError, UnicodeError):
        raise SmokeError("BFF package GET response is not JSON") from None
    if not isinstance(value, dict):
        raise SmokeError("BFF package GET response envelope invalid")
    return response.status, value


def upload_zip_bytes(skill_id: str, revision: int) -> bytes:
    """A bounded owner ZIP V1 bound to the fresh draft's identity."""
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,190}", skill_id) or revision < 1:
        raise SmokeError("ZIP fixture Skill identity invalid")
    manifest = json.dumps(
        {
            "schema_version": 1,
            "skill_id": skill_id,
            "revision": revision,
            "entry": "SKILL.md",
        },
        separators=(",", ":"),
    )
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", manifest)
        archive.writestr("SKILL.md", "# Sandbox\n\nOwned signed PUT smoke.\n")
    return stream.getvalue()


def signed_put(reference: dict[str, object], payload: bytes) -> None:
    """Send bytes only to the already-validated signed origin, without IAM headers."""
    transfer = reference["transfer_reference"]
    if not isinstance(transfer, dict):
        raise SmokeError("BFF signed PUT transfer missing")
    parsed = urlsplit(str(transfer["url"]))
    connection = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=12)
    try:
        connection.request(
            "PUT",
            urlunsplit(("", "", parsed.path, parsed.query, "")),
            body=payload,
            headers={"content-type": "application/zip"},
        )
        response = connection.getresponse()
        response.read(1024)
        if response.status not in {200, 204}:
            raise SmokeError("signed package PUT was rejected")
    finally:
        connection.close()


def _wait_ready(
    base: str, process: subprocess.Popen[bytes], path: str = "/readyz"
) -> None:
    deadline = time.monotonic() + 40
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise SmokeError("owned process exited before readiness")
        parsed = urlsplit(base)
        connection = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=1)
        try:
            connection.request("GET", path)
            response = connection.getresponse()
            response.read(1024)
            if response.status == 200:
                return
        except OSError:
            pass
        finally:
            connection.close()
        time.sleep(0.15)
    raise SmokeError("owned process readiness deadline exceeded")


def _stop(process: subprocess.Popen[bytes] | None) -> None:
    if process is None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
        if process.poll() is None:
            process.wait(timeout=10)
    except ProcessLookupError:
        if process.poll() is None:
            process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        if process.poll() is None:
            process.wait(timeout=5)


def _start(
    command: list[str], cwd: Path, env: dict[str, str], log
) -> subprocess.Popen[bytes]:
    return subprocess.Popen(
        command,
        cwd=cwd,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=log,
        stderr=log,
        start_new_session=True,
    )


def stop_owned_processes(
    consumers: list[object],
    iam: object | None,
    reader: object | None,
    stop: Callable[[object | None], None] = _stop,
) -> list[str]:
    """Attempt every process cleanup; IAM is always last and gets its owner protocol."""
    failures: list[str] = []
    for process in reversed(consumers):
        try:
            stop(process)
        except BaseException:
            failures.append("owned consumer process cleanup failed")
    if iam is not None and getattr(iam, "poll")() is None:
        try:
            stream = getattr(iam, "stdin")
            if stream is None or reader is None:
                raise RuntimeError("protocol absent")
            stream.write(b'{"command":"stop"}\n')
            stream.flush()
            if getattr(reader, "record")(timeout=30) != {
                "kind": "result",
                "command": "stop",
                "status": "ok",
            }:
                raise RuntimeError("protocol drift")
            getattr(iam, "wait")(timeout=30)
        except BaseException:
            failures.append("IAM stop protocol cleanup failed")
    try:
        stop(iam)
    except BaseException:
        failures.append("IAM process cleanup failed")
    return failures


def _safe_log_tail(log, secrets: tuple[str, ...]) -> str:
    """Return one bounded, credential-redacted diagnostic line."""
    log.flush()
    position = log.tell()
    log.seek(max(0, position - 8192))
    raw = log.read(8192).decode("utf-8", "replace")
    log.seek(position)
    for secret in sorted((value for value in secrets if value), key=len, reverse=True):
        raw = raw.replace(secret, "[REDACTED]")
    raw = re.sub(
        r"(?i)(postgres(?:ql)?|redis|https?)://[^\s]+", r"\1://[REDACTED]", raw
    )
    lines = [
        re.sub(r"\s+", " ", line).strip() for line in raw.splitlines() if line.strip()
    ]
    if not lines:
        return "no diagnostic"
    preferred = [
        line
        for line in lines
        if re.search(r"(?i)\b(error|message|detail|fatal)\b", line)
    ]
    selected = preferred[-12:] if preferred else lines[-25:]
    diagnostic = " | ".join(selected)
    return diagnostic[-2000:]


def _run(
    command: list[str],
    cwd: Path,
    env: dict[str, str],
    log,
    label: str,
    secrets: tuple[str, ...] = (),
) -> None:
    process: subprocess.Popen[bytes] | None = None
    try:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=log,
            start_new_session=True,
        )
        returncode = process.wait(timeout=120)
    except subprocess.TimeoutExpired:
        _stop(process)
        raise SmokeError(f"{label} deadline exceeded") from None
    except BaseException:
        _stop(process)
        raise
    if returncode != 0:
        _stop(process)
        raise SmokeError(f"{label} failed: {_safe_log_tail(log, secrets)}")


def platform_inventory_connection_url(database_url: str) -> str:
    """Remove only Prisma's owner schema selector before a libpq connection."""
    parsed = urlsplit(database_url)
    pairs = parse_qsl(parsed.query, keep_blank_values=True)
    schemas = [value for key, value in pairs if key == "schema"]
    if (
        parsed.scheme not in {"postgres", "postgresql"}
        or parsed.hostname not in LOCAL_HOSTS
        or parsed.port == 3310
        or parsed.fragment
        or schemas != ["kokoro_platform"]
        or any(key.lower() in {"options", "search_path"} for key, _value in pairs)
    ):
        raise SmokeError(
            "Platform inventory URL must select the exact local owner schema"
        )
    query = urlencode([(key, value) for key, value in pairs if key != "schema"])
    return urlunsplit(
        (parsed.scheme, parsed.netloc, parsed.path, query, parsed.fragment)
    )


def platform_inventory(
    database_url: str, tenant: str, skill_id: str
) -> tuple[int, int, int, int]:
    """Read only Platform-owned tables; never join or mutate another owner."""
    import psycopg

    with (
        psycopg.connect(
            platform_inventory_connection_url(database_url), connect_timeout=5
        ) as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute(
            'SELECT count(*) FROM "kokoro_platform"."skill" WHERE tenant_id = %s',
            (tenant,),
        )
        skills = int(cursor.fetchone()[0])
        cursor.execute(
            'SELECT count(*) FROM "kokoro_platform"."command_receipt" WHERE tenant_id = %s',
            (tenant,),
        )
        receipts = int(cursor.fetchone()[0])
        cursor.execute(
            'SELECT count(*) FROM "kokoro_platform"."outbox_event" '
            "WHERE tenant_id = %s AND event_type = %s",
            (tenant, "skill.published"),
        )
        publish_events = int(cursor.fetchone()[0])
        cursor.execute(
            'SELECT count(*) FROM "kokoro_platform"."skill" '
            "WHERE tenant_id = %s AND skill_id = %s AND status::text = %s "
            "AND package_phase::text = %s AND package_attempt_epoch = %s",
            (tenant, skill_id, "active", "validated", 6),
        )
        active_validated = int(cursor.fetchone()[0])
    return skills, receipts, publish_events, active_validated


def _redis_keys(url: str, pattern: str) -> set[str]:
    if not pattern or pattern == "*":
        raise SmokeError("unbounded Redis inventory forbidden")
    result = subprocess.run(
        ["redis-cli", "-e", "-u", url, "--scan", "--pattern", pattern],
        text=True,
        capture_output=True,
        timeout=10,
        check=True,
    )
    return {line for line in result.stdout.splitlines() if line}


def _database_exists(admin_url: str, name: str) -> bool:
    result = subprocess.run(
        [
            "psql",
            admin_url,
            "-X",
            "-v",
            "ON_ERROR_STOP=1",
            "-Atc",
            "SELECT 1 FROM pg_database WHERE datname = '" + name + "'",
        ],
        text=True,
        capture_output=True,
        timeout=10,
        check=True,
    )
    return result.stdout.strip() == "1"


def verify_cleanup(
    *,
    before_redis: set[str],
    redis_snapshot: Callable[[], set[str]],
    database_name: str | None,
    database_exists: Callable[[str], bool],
) -> list[str]:
    """Attempt every independent cleanup assertion and return bounded failures."""
    failures: list[str] = []
    try:
        if redis_snapshot() != before_redis:
            failures.append("owned Redis resources were not restored")
    except BaseException:
        failures.append("Redis cleanup verification failed")
    try:
        if database_name is not None and database_exists(database_name):
            failures.append("IAM owned database was not removed")
    except BaseException:
        failures.append("database cleanup verification failed")
    return failures


def create_owned_bucket(
    s3: object, bucket: str, region: str, owned: Callable[[], None] = lambda: None
) -> None:
    """Create a random bucket with the exact lifecycle required by Storage."""
    arguments: dict[str, object] = {
        "Bucket": bucket,
        "ObjectLockEnabledForBucket": True,
    }
    if region != "us-east-1":
        arguments["CreateBucketConfiguration"] = {"LocationConstraint": region}
    s3.create_bucket(**arguments)
    owned()
    s3.put_bucket_versioning(
        Bucket=bucket, VersioningConfiguration={"Status": "Enabled"}
    )


def delete_owned_bucket(s3: object, bucket: str, storage_helper: object) -> None:
    """Delete only a bucket this run successfully created, including exact versions."""
    del storage_helper
    key_marker = version_marker = None
    while True:
        arguments = {"Bucket": bucket, "Prefix": "", "MaxKeys": 1000}
        if key_marker is not None:
            arguments["KeyMarker"] = key_marker
        if version_marker is not None:
            arguments["VersionIdMarker"] = version_marker
        page = s3.list_object_versions(**arguments)
        for item in [*page.get("Versions", []), *page.get("DeleteMarkers", [])]:
            key, version = item.get("Key"), item.get("VersionId")
            if (
                not isinstance(key, str)
                or not isinstance(version, str)
                or not key
                or not version
            ):
                raise SmokeError("owned bucket version identity invalid")
            s3.delete_object(Bucket=bucket, Key=key, VersionId=version)
        if not page.get("IsTruncated"):
            break
        key_marker, version_marker = (
            page.get("NextKeyMarker"),
            page.get("NextVersionIdMarker"),
        )
        if not isinstance(key_marker, str) or not isinstance(version_marker, str):
            raise SmokeError("owned bucket pagination identity invalid")
    remaining = s3.list_object_versions(Bucket=bucket, Prefix="", MaxKeys=1000)
    if (
        remaining.get("IsTruncated")
        or remaining.get("Versions")
        or remaining.get("DeleteMarkers")
    ):
        raise SmokeError("owned bucket inventory remained after cleanup")
    s3.delete_bucket(Bucket=bucket)
    try:
        s3.head_bucket(Bucket=bucket)
    except Exception as exc:
        if (
            getattr(exc, "response", {})
            .get("ResponseMetadata", {})
            .get("HTTPStatusCode")
            != 404
        ):
            raise SmokeError("owned bucket deletion unconfirmed") from None
    else:
        raise SmokeError("owned bucket remained after deletion")


def require_bucket_absent(s3: object, bucket: str) -> None:
    """Independent post-cleanup inventory check, separate from delete execution."""
    try:
        s3.head_bucket(Bucket=bucket)
    except Exception as exc:
        if (
            getattr(exc, "response", {})
            .get("ResponseMetadata", {})
            .get("HTTPStatusCode")
            != 404
        ):
            raise SmokeError("owned bucket absence verification failed") from None
        return
    raise SmokeError("owned bucket still exists after cleanup")


@dataclass(frozen=True, slots=True)
class RunArguments:
    postgres_admin_url: str
    redis_url: str
    iam_node: Path
    bff_node: Path
    platform_node: Path
    storage_node: Path
    bucket: str


def owned_bucket_name(prefix: str, run_id: str) -> str:
    base = prefix.rstrip(".-")[: 63 - len(run_id) - 1].rstrip(".-")
    if not base or re.fullmatch(r"[a-z0-9][a-z0-9.-]*", base) is None:
        raise SmokeError("exclusive bucket prefix invalid")
    return f"{base}-{run_id}"


def execute(args: RunArguments, env: dict[str, str] | None = None) -> dict[str, object]:
    """Run the real composition. Source freezing happens before all side effects."""
    frozen_sources()
    source_env = dict(os.environ if env is None else env)
    admin_url = normalized_postgres_admin_url(args.postgres_admin_url)
    postgres = urlsplit(admin_url)
    redis = urlsplit(args.redis_url)
    if (
        postgres.scheme not in {"postgres", "postgresql"}
        or postgres.hostname not in LOCAL_HOSTS
        or postgres.port == 3310
    ):
        raise SmokeError("local PostgreSQL admin URL required")
    if (
        redis.scheme not in {"redis", "rediss"}
        or redis.hostname not in LOCAL_HOSTS
        or redis.port == 3310
    ):
        raise SmokeError("local non-3310 Redis URL required")
    if any(
        not path.is_absolute()
        for path in (
            args.iam_node,
            args.bff_node,
            args.platform_node,
            args.storage_node,
        )
    ):
        raise SmokeError("absolute Node paths required")
    if re.fullmatch(r"[a-z0-9][a-z0-9.-]{2,62}", args.bucket) is None:
        raise SmokeError("exclusive bucket name invalid")
    for name in (
        "KOKORO_OBJECT_STORE_ENDPOINT",
        "KOKORO_OBJECT_STORE_PUBLIC_ENDPOINT",
        "KOKORO_OBJECT_STORE_REGION",
        "KOKORO_OBJECT_STORE_ACCESS_KEY_ID",
        "KOKORO_OBJECT_STORE_SECRET_ACCESS_KEY",
        "KOKORO_SCANNER_HOST",
        "KOKORO_SCANNER_PORT",
    ):
        if not source_env.get(name):
            raise SmokeError(f"{name} is required")
    if (
        source_env.get("KOKORO_OBJECT_STORE_PROFILE") != "custom"
        or source_env.get("KOKORO_OBJECT_STORE_FORCE_PATH_STYLE") != "true"
    ):
        raise SmokeError("custom path-style ObjectStore configuration required")
    if source_env["KOKORO_SCANNER_HOST"] not in LOCAL_HOSTS:
        raise SmokeError("local scanner required")
    try:
        scanner_port = int(source_env["KOKORO_SCANNER_PORT"])
    except ValueError:
        raise SmokeError("scanner port invalid") from None
    if scanner_port == 3310 or not 1 <= scanner_port <= 65535:
        raise SmokeError("scanner port invalid or reserved")
    source_env["KOKORO_OBJECT_STORE_ENDPOINT"] = local_http_origin(
        source_env["KOKORO_OBJECT_STORE_ENDPOINT"], "ObjectStore internal"
    )
    source_env["KOKORO_OBJECT_STORE_PUBLIC_ENDPOINT"] = local_http_origin(
        source_env["KOKORO_OBJECT_STORE_PUBLIC_ENDPOINT"], "ObjectStore public"
    )
    # Reuse audited Root lifecycle helpers without changing their ownership.
    import run_agent_storage_artifact_smoke as storage_helper
    import run_web_bff_iam_oidc_smoke as oidc
    import run_bff_iam_session_smoke as session

    run_id = secrets.token_hex(12)
    directory = Path(tempfile.mkdtemp(prefix="kokoro-skill-sandbox-"))
    os.chmod(directory, 0o700)
    processes: list[subprocess.Popen[bytes]] = []
    reader = None
    proxy: CountingTcpProxy | None = None
    ready: SandboxReady | None = None
    secret_values: tuple[str, ...] = tuple(
        value
        for value in {
            source_env["KOKORO_OBJECT_STORE_ACCESS_KEY_ID"],
            source_env["KOKORO_OBJECT_STORE_SECRET_ACCESS_KEY"],
            urlsplit(admin_url).password or "",
            urlsplit(args.redis_url).password or "",
        }
        if value
    )
    database_name: str | None = None
    redis_prefix: str | None = None
    bucket_state = {"created": False}
    owned_bucket = owned_bucket_name(args.bucket, run_id)
    s3 = None
    error: BaseException | None = None
    summary: dict[str, object] | None = None
    phase = Phase.IAM_READY
    log_path = directory / "owners.log"
    restore_sigterm = install_sigterm_cleanup_handler()
    try:
        with log_path.open("x+b") as log:
            os.chmod(log_path, 0o600)
            iam_resource_id = str(uuid4())
            iam_owner_token = secrets.token_hex(16)
            secret_values += (iam_owner_token,)
            expected_database = "iam_web_oidc_" + iam_resource_id.replace("-", "")
            expected_redis_prefix = f"iam:test:web-oidc-flow-host:{iam_resource_id}:"
            if _database_exists(admin_url, expected_database) or _redis_keys(
                args.redis_url, expected_redis_prefix + "*"
            ):
                raise SmokeError("IAM owned identity already exists")
            iam_env = session.node_environment(
                args.iam_node, "v24.20.0", args.bff_node.parent
            )
            iam_env.update(
                {
                    "IAM_TEST_ADMIN_URL": admin_url,
                    "IAM_TEST_REDIS_URL": args.redis_url,
                    "IAM_TEST_WEB_ORIGIN": f"https://skill-{run_id}.example.test",
                    "IAM_TEST_ALLOW_HTTP_LOOPBACK": "0",
                    "IAM_TEST_SKILL_SANDBOX_MODE": "1",
                    "IAM_TEST_RESOURCE_ID": iam_resource_id,
                    "IAM_TEST_RESOURCE_OWNER_TOKEN": iam_owner_token,
                    "NODE_ENV": "test",
                }
            )
            database_name = expected_database
            redis_prefix = expected_redis_prefix
            iam = subprocess.Popen(
                [
                    str(args.iam_node),
                    "--import",
                    "tsx",
                    str(OWNERS["iam"] / "test/fixtures/web-oidc-flow-host.ts"),
                ],
                cwd=OWNERS["iam"],
                env=iam_env,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=log,
                start_new_session=True,
                bufsize=0,
            )
            processes.append(iam)
            if iam.stdout is None:
                raise SmokeError("IAM host protocol absent")
            reader = session.ProtocolReader(iam.stdout.fileno())
            ready = require_sandbox_ready(reader.record(timeout=60))
            if (
                ready.database_name != expected_database
                or ready.redis_prefix != expected_redis_prefix
            ):
                raise SmokeError("IAM ready identity differs from runner ownership")
            urls = {
                schema: owner_database_url(admin_url, ready.database_name, schema)
                for schema in ("kokoro_bff", "kokoro_platform", "kokoro_storage")
            }
            storage_port, platform_port, bff_port = (
                oidc.runtime.free_port() for _ in range(3)
            )
            storage_base = f"http://127.0.0.1:{storage_port}"
            platform_base = f"http://127.0.0.1:{platform_port}"
            bff_base = f"http://127.0.0.1:{bff_port}"
            storage_secret = secrets.token_hex(32)
            storage_agent_secret = secrets.token_hex(32)
            storage_platform_secret = secrets.token_hex(32)
            web_secret = secrets.token_hex(32)
            secret_values = tuple(
                {
                    *secret_values,
                    *ready.secrets,
                    storage_secret,
                    storage_agent_secret,
                    storage_platform_secret,
                    web_secret,
                }
                - {""}
            )
            base = {
                "PATH": source_env.get("PATH", ""),
                "HOME": source_env.get("HOME", ""),
                "NODE_ENV": "development",
                "TMPDIR": str(directory),
            }
            storage_input = {
                **source_env,
                "KOKORO_W2_POSTGRES_ADMIN_URL": admin_url,
                "KOKORO_W2_REDIS_URL": args.redis_url,
                "KOKORO_W2_STORAGE_NODE_BIN": str(args.storage_node),
                "KOKORO_W2_TEST_BUCKET": owned_bucket,
            }
            s3 = storage_helper._s3(storage_input)
            create_owned_bucket(
                s3,
                owned_bucket,
                source_env["KOKORO_OBJECT_STORE_REGION"],
                lambda: bucket_state.__setitem__("created", True),
            )
            storage_helper.preflight_bucket(
                s3, owned_bucket, f"skill-sandbox-{run_id}/"
            )
            if storage_helper._list_versions(s3, owned_bucket, ""):
                raise SmokeError("new owned bucket was not empty")
            phase = Phase.SCHEMA
            storage_env = storage_helper._storage_env(
                storage_input,
                ready.database_name,
                storage_agent_secret,
                storage_secret,
                storage_port,
            )
            storage_env["KOKORO_STORAGE_SERVICE_CREDENTIALS"] += (
                f",kokoro-platform={storage_platform_secret}"
            )
            fixture = storage_helper._storage_schema_fixture(directory)
            _run(
                [
                    str(args.storage_node),
                    str(OWNERS["storage"] / "node_modules/tsx/dist/cli.mjs"),
                    "scripts/apply-schema.ts",
                ],
                fixture,
                storage_env,
                log,
                "Storage schema installation",
                secret_values,
            )
            platform_env = {
                **base,
                "PATH": f"{args.platform_node.parent}:{base['PATH']}",
                "KOKORO_POSTGRES_URL": urls["kokoro_platform"],
                "KOKORO_REDIS_URL": args.redis_url,
                "KOKORO_STORAGE_URL": storage_base,
                "KOKORO_PLATFORM_STORAGE_SERVICE_CREDENTIAL": storage_platform_secret,
                "KOKORO_IAM_BASE_URL": ready.base_url,
                "KOKORO_PLATFORM_HOST": "127.0.0.1",
                "KOKORO_PLATFORM_PORT": str(platform_port),
                "KOKORO_PLATFORM_SURFACES": "skill-catalog",
            }
            bff_env = {
                **base,
                "PATH": f"{args.bff_node.parent}:{base['PATH']}",
                "KOKORO_BFF_POSTGRES_URL": urls["kokoro_bff"],
                "KOKORO_BFF_REDIS_URL": args.redis_url,
                "KOKORO_BFF_HOST": "127.0.0.1",
                "KOKORO_BFF_PORT": str(bff_port),
                "KOKORO_BFF_MODE": "live",
                "KOKORO_BFF_SHARED_SECRET": web_secret,
                "KOKORO_TENANT_ID": ready.tenant_id,
                "KOKORO_DOMAIN": f"{run_id}.smoke.localhost",
                "KOKORO_IAM_BASE_URL": ready.base_url,
                "KOKORO_AGENT_ENABLED": "false",
                "KOKORO_STORAGE_OBJECT_ORIGIN": source_env[
                    "KOKORO_OBJECT_STORE_PUBLIC_ENDPOINT"
                ],
            }
            _run(
                [
                    str(args.platform_node.parent / "corepack"),
                    "pnpm",
                    "db:apply-schema",
                ],
                OWNERS["platform"],
                platform_env,
                log,
                "Platform schema installation",
                secret_values,
            )
            _run(
                [str(args.bff_node.parent / "corepack"), "pnpm", "db:apply-schema"],
                OWNERS["bff"],
                bff_env,
                log,
                "BFF schema installation",
                secret_values,
            )
            with credential_files(directory, ready) as files:
                phase = Phase.OWNER_START
                platform_env.update(
                    {
                        "KOKORO_PLATFORM_IAM_RESOURCE_SERVER_CREDENTIAL_FILE": str(
                            files["resource-server.json"]
                        ),
                        "KOKORO_PLATFORM_IAM_TENANT_CREDENTIALS_FILE": str(
                            files["tenant-execution.json"]
                        ),
                    }
                )
                storage = _start(
                    [str(args.storage_node), str(OWNERS["storage"] / "dist/main.js")],
                    OWNERS["storage"],
                    storage_env,
                    log,
                )
                processes.append(storage)
                _wait_ready(storage_base, storage)
                platform = _start(
                    [str(args.platform_node), str(OWNERS["platform"] / "dist/main.js")],
                    OWNERS["platform"],
                    platform_env,
                    log,
                )
                processes.append(platform)
                _wait_ready(platform_base, platform)
                proxy = CountingTcpProxy(platform_port)
                # First boot proves the production default remains closed.
                phase = Phase.DEFAULT_OFF
                proxied_platform = f"http://127.0.0.1:{proxy.port}"
                bff_env.update(
                    {
                        "KOKORO_PLATFORM_BASE_URL": proxied_platform,
                        "KOKORO_BFF_PLATFORM_CATALOG_CREDENTIALS_FILE": str(
                            files["bff-catalog.json"]
                        ),
                        "KOKORO_SKILL_DRAFT_CANDIDATE_ENABLED": "false",
                    }
                )
                closed = _start(
                    [str(args.bff_node), str(OWNERS["bff"] / "dist/main.js")],
                    OWNERS["bff"],
                    bff_env,
                    log,
                )
                processes.append(closed)
                _wait_ready(bff_base, closed, "/healthz")
                status, body = _http_json(
                    bff_base,
                    "/v1/skills/drafts",
                    token=ready.access_token,
                    secret=web_secret,
                    key="closed",
                    body={"display_name": "Closed", "summary": "", "tags": []},
                )
                if (
                    status != 503
                    or body.get("error", {}).get("code")
                    != "skill_dependency_unavailable"
                ):
                    raise SmokeError("default-off BFF candidate did not fail closed")
                get_path = "/v1/skills/sandbox-closed/package-upload"
                status, body = _http_get_json(
                    bff_base,
                    get_path,
                    token=ready.access_token,
                    secret=web_secret,
                )
                if (
                    status != 503
                    or body.get("error", {}).get("code")
                    != "skill_dependency_unavailable"
                ):
                    raise SmokeError("default-off BFF package GET did not fail closed")
                status, body = _http_json(
                    bff_base,
                    get_path,
                    token=ready.access_token,
                    secret=web_secret,
                    key="closed-begin",
                    body={
                        "filename": "closed.zip",
                        "mime_type": "application/zip",
                        "size_bytes": 1,
                        "content_sha256": "0" * 64,
                    },
                )
                if (
                    status != 503
                    or body.get("error", {}).get("code")
                    != "skill_dependency_unavailable"
                ):
                    raise SmokeError(
                        "default-off BFF package Begin did not fail closed"
                    )
                status, body = _http_json(
                    bff_base,
                    get_path + "/complete",
                    token=ready.access_token,
                    secret=web_secret,
                    key="closed-complete",
                    body={
                        "attempt_id": "attempt-closed",
                        "upload_id": "upload-closed",
                        "content_sha256": "0" * 64,
                        "size_bytes": 1,
                    },
                )
                if (
                    status != 503
                    or body.get("error", {}).get("code")
                    != "skill_dependency_unavailable"
                ):
                    raise SmokeError(
                        "default-off BFF package Complete did not fail closed"
                    )
                status, body = _http_json(
                    bff_base,
                    "/v1/skills/sandbox-closed/validate",
                    token=ready.access_token,
                    secret=web_secret,
                    key="closed-validate",
                    body={"attempt_id": "attempt-closed"},
                )
                if (
                    status != 503
                    or body.get("error", {}).get("code")
                    != "skill_dependency_unavailable"
                ):
                    raise SmokeError("default-off BFF Validate did not fail closed")
                if proxy.count != 0:
                    raise SmokeError("default-off BFF opened a Platform socket")
                _stop(closed)
                processes.remove(closed)
                bff_env["KOKORO_SKILL_DRAFT_CANDIDATE_ENABLED"] = "true"
                active = _start(
                    [str(args.bff_node), str(OWNERS["bff"] / "dist/main.js")],
                    OWNERS["bff"],
                    bff_env,
                    log,
                )
                processes.append(active)
                _wait_ready(bff_base, active, "/healthz")

                def observe(next_phase: Phase) -> None:
                    nonlocal phase
                    phase = next_phase

                result = exercise_http_contract(
                    lambda **kw: _http_json(
                        bff_base, "/v1/skills/drafts", secret=web_secret, **kw
                    ),
                    ready,
                    observe,
                )
                phase = Phase.CANDIDATE_PACKAGE_GET
                get_path = (
                    "/v1/skills/"
                    + quote(str(result["skill_id"]), safe="")
                    + "/package-upload"
                )
                status, body = _http_get_json(
                    bff_base,
                    get_path,
                    token=ready.access_token,
                    secret=web_secret,
                )
                require_public_package_get(status, body, str(result["skill_id"]))
                phase = Phase.PACKAGE_REFERENCE
                _run(
                    [
                        str(args.platform_node),
                        str(OWNERS["platform"] / "scripts/smoke-storage-package.mjs"),
                    ],
                    OWNERS["platform"],
                    platform_package_probe_env(
                        base,
                        args.platform_node,
                        storage_base,
                        platform_base,
                        ready.base_url,
                        storage_platform_secret,
                        ready,
                        str(result["skill_id"]),
                    ),
                    log,
                    "Platform real Storage v2 Complete, ZIP Validate and Publish",
                    secret_values,
                )
                phase = Phase.INVENTORY
                if platform_inventory(
                    urls["kokoro_platform"], ready.tenant_id, str(result["skill_id"])
                ) != (
                    1,
                    16,
                    1,
                    1,
                ):
                    raise SmokeError("Platform Publish inventory is not unique")
                status, body = _http_get_json(
                    bff_base,
                    get_path,
                    token=ready.access_token,
                    secret=web_secret,
                )
                if (
                    status != 412
                    or body.get("error", {}).get("code") != "skill_precondition_failed"
                ):
                    raise SmokeError(
                        "published Skill package GET did not reject non-draft"
                    )
                # Keep the owner CLI's published fixture intact; a second fresh
                # draft proves the BFF public Begin and direct data plane.
                phase = Phase.CANDIDATE_PACKAGE_BEGIN
                status, body = _http_json(
                    bff_base,
                    "/v1/skills/drafts",
                    token=ready.access_token,
                    secret=web_secret,
                    key="package-begin-draft-" + run_id,
                    body={
                        "display_name": "Signed PUT sandbox skill",
                        "summary": "public Begin probe",
                        "tags": ["sandbox"],
                    },
                )
                begin_skill_id, begin_series_id, replayed, _ = _draft(body, status)
                if status != 201 or replayed is not False or begin_skill_id is None:
                    raise SmokeError("BFF Begin fixture draft was not created")
                begin_path = (
                    "/v1/skills/" + quote(begin_skill_id, safe="") + "/package-upload"
                )
                payload = upload_zip_bytes(begin_skill_id, 1)
                begin_body = {
                    "filename": "sandbox.zip",
                    "mime_type": "application/zip",
                    "size_bytes": len(payload),
                    "content_sha256": hashlib.sha256(payload).hexdigest(),
                }
                begin_key = "package-begin-" + run_id
                status, body = _http_json(
                    bff_base,
                    begin_path,
                    token=ready.access_token,
                    secret=web_secret,
                    key=begin_key,
                    body=begin_body,
                )
                first_begin = require_public_package_begin(
                    status,
                    body,
                    begin_skill_id,
                    source_env["KOKORO_OBJECT_STORE_PUBLIC_ENDPOINT"],
                )
                secret_values += signed_reference_secrets(
                    str(first_begin["transfer_reference"]["url"])
                )
                if (
                    first_begin["replayed"] is not False
                    or first_begin["attempt_epoch"] != "1"
                ):
                    raise SmokeError("BFF initial Begin did not create attempt one")
                status, body = _http_get_json(
                    bff_base,
                    begin_path,
                    token=ready.access_token,
                    secret=web_secret,
                )
                require_public_package_pending(
                    status,
                    body,
                    begin_skill_id,
                    str(first_begin["attempt_id"]),
                    str(first_begin["upload_id"]),
                    "1",
                )
                phase = Phase.CANDIDATE_SIGNED_PUT
                signed_put(first_begin, payload)
                status, body = _http_json(
                    bff_base,
                    begin_path,
                    token=ready.access_token,
                    secret=web_secret,
                    key=begin_key,
                    body=begin_body,
                )
                repeated_begin = require_public_package_begin(
                    status,
                    body,
                    begin_skill_id,
                    source_env["KOKORO_OBJECT_STORE_PUBLIC_ENDPOINT"],
                )
                secret_values += signed_reference_secrets(
                    str(repeated_begin["transfer_reference"]["url"])
                )
                if (
                    repeated_begin["replayed"] is not True
                    or repeated_begin["attempt_id"] != first_begin["attempt_id"]
                    or repeated_begin["upload_id"] != first_begin["upload_id"]
                ):
                    raise SmokeError("BFF Begin same-command replay drift")
                status, body = _http_json(
                    bff_base,
                    begin_path,
                    token=ready.access_token,
                    secret=web_secret,
                    key=begin_key,
                    body={**begin_body, "filename": "different.zip"},
                )
                if (
                    status != 409
                    or body.get("error", {}).get("code") != "skill_idempotency_conflict"
                ):
                    raise SmokeError("BFF Begin same-key conflict drift")
                status, body = _http_json(
                    bff_base,
                    begin_path,
                    token=ready.access_token,
                    secret=web_secret,
                    key="package-begin-replace-" + run_id,
                    body={
                        **begin_body,
                        "replaces_attempt_id": first_begin["attempt_id"],
                    },
                )
                replacement = require_public_package_begin(
                    status,
                    body,
                    begin_skill_id,
                    source_env["KOKORO_OBJECT_STORE_PUBLIC_ENDPOINT"],
                )
                secret_values += signed_reference_secrets(
                    str(replacement["transfer_reference"]["url"])
                )
                if (
                    replacement["replayed"] is not False
                    or replacement["attempt_id"] == first_begin["attempt_id"]
                    or replacement["attempt_epoch"] != "2"
                ):
                    raise SmokeError("BFF Begin replacement did not advance attempt")
                status, body = _http_get_json(
                    bff_base,
                    begin_path,
                    token=ready.access_token,
                    secret=web_secret,
                )
                require_public_package_pending(
                    status,
                    body,
                    begin_skill_id,
                    str(replacement["attempt_id"]),
                    str(replacement["upload_id"]),
                    "2",
                )
                phase = Phase.CANDIDATE_PACKAGE_COMPLETE
                signed_put(replacement, payload)
                complete_path = begin_path + "/complete"
                complete_body = {
                    "attempt_id": replacement["attempt_id"],
                    "upload_id": replacement["upload_id"],
                    "content_sha256": begin_body["content_sha256"],
                    "size_bytes": len(payload),
                }
                complete_key = "package-complete-" + run_id
                status, body = _http_json(
                    bff_base,
                    complete_path,
                    token=ready.access_token,
                    secret=web_secret,
                    key=complete_key,
                    body=complete_body,
                )
                completed = require_public_package_complete(
                    status,
                    body,
                    begin_skill_id,
                    str(replacement["attempt_id"]),
                    str(replacement["upload_id"]),
                    "2",
                    str(begin_body["content_sha256"]),
                )
                if completed["replayed"] is not False:
                    raise SmokeError("BFF first Complete was unexpectedly replayed")
                deadline = time.monotonic() + 25
                while (
                    completed["scan_state"] != "clean" and time.monotonic() < deadline
                ):
                    time.sleep(0.25)
                    status, body = _http_json(
                        bff_base,
                        complete_path,
                        token=ready.access_token,
                        secret=web_secret,
                        key=complete_key,
                        body=complete_body,
                    )
                    completed = require_public_package_complete(
                        status,
                        body,
                        begin_skill_id,
                        str(replacement["attempt_id"]),
                        str(replacement["upload_id"]),
                        "2",
                        str(begin_body["content_sha256"]),
                    )
                if completed["scan_state"] != "clean":
                    raise SmokeError("BFF Complete did not observe current CLEAN scan")
                status, body = _http_json(
                    bff_base,
                    complete_path,
                    token=ready.access_token,
                    secret=web_secret,
                    key=complete_key,
                    body=complete_body,
                )
                repeated_complete = require_public_package_complete(
                    status,
                    body,
                    begin_skill_id,
                    str(replacement["attempt_id"]),
                    str(replacement["upload_id"]),
                    "2",
                    str(begin_body["content_sha256"]),
                )
                if repeated_complete["replayed"] is not True:
                    raise SmokeError("BFF Complete replay drift")
                status, body = _http_json(
                    bff_base,
                    complete_path,
                    token=ready.access_token,
                    secret=web_secret,
                    key=complete_key,
                    body={**complete_body, "content_sha256": "0" * 64},
                )
                if (
                    status != 412
                    or body.get("error", {}).get("code") != "skill_precondition_failed"
                ):
                    raise SmokeError(
                        "BFF Complete current descriptor precondition drift "
                        f"(status={status}, code={public_error_code(body.get('error', {}).get('code'))})"
                    )
                status, body = _http_get_json(
                    bff_base,
                    begin_path,
                    token=ready.access_token,
                    secret=web_secret,
                )
                require_public_package_uploaded(
                    status,
                    body,
                    begin_skill_id,
                    str(replacement["attempt_id"]),
                    str(replacement["upload_id"]),
                    "2",
                )
                # EICAR is the Storage scanner's test fixture. It deliberately
                # is not a valid ZIP and proves rejection before ZIP validation.
                infected_payload = (
                    b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-"
                    b"ANTIVIRUS-TEST-FILE!$H+H*"
                )
                infected_body = {
                    **begin_body,
                    "filename": "scanner-fixture.zip",
                    "size_bytes": len(infected_payload),
                    "content_sha256": hashlib.sha256(infected_payload).hexdigest(),
                    "replaces_attempt_id": replacement["attempt_id"],
                }
                status, body = _http_json(
                    bff_base,
                    begin_path,
                    token=ready.access_token,
                    secret=web_secret,
                    key="package-infected-begin-" + run_id,
                    body=infected_body,
                )
                infected = require_public_package_begin(
                    status,
                    body,
                    begin_skill_id,
                    source_env["KOKORO_OBJECT_STORE_PUBLIC_ENDPOINT"],
                )
                secret_values += signed_reference_secrets(
                    str(infected["transfer_reference"]["url"])
                )
                if (
                    infected["replayed"] is not False
                    or infected["attempt_epoch"] != "3"
                ):
                    raise SmokeError("BFF infected Begin attempt drift")
                signed_put(infected, infected_payload)
                infected_complete_body = {
                    "attempt_id": infected["attempt_id"],
                    "upload_id": infected["upload_id"],
                    "content_sha256": infected_body["content_sha256"],
                    "size_bytes": len(infected_payload),
                }
                infected_complete_key = "package-infected-complete-" + run_id
                for _ in range(2):
                    status, body = _http_json(
                        bff_base,
                        complete_path,
                        token=ready.access_token,
                        secret=web_secret,
                        key=infected_complete_key,
                        body=infected_complete_body,
                    )
                    if (
                        status != 412
                        or body.get("error", {}).get("code")
                        != "skill_precondition_failed"
                    ):
                        raise SmokeError("BFF infected Complete did not reject")
                    status, body = _http_get_json(
                        bff_base,
                        begin_path,
                        token=ready.access_token,
                        secret=web_secret,
                    )
                    require_public_package_aborted(
                        status,
                        body,
                        begin_skill_id,
                        str(infected["attempt_id"]),
                        str(infected["upload_id"]),
                        "3",
                    )
                status, body = _http_json(
                    bff_base,
                    begin_path,
                    token=ready.access_token,
                    secret=web_secret,
                    key="package-recover-begin-" + run_id,
                    body={**begin_body, "replaces_attempt_id": infected["attempt_id"]},
                )
                recovered = require_public_package_begin(
                    status,
                    body,
                    begin_skill_id,
                    source_env["KOKORO_OBJECT_STORE_PUBLIC_ENDPOINT"],
                )
                secret_values += signed_reference_secrets(
                    str(recovered["transfer_reference"]["url"])
                )
                if (
                    recovered["replayed"] is not False
                    or recovered["attempt_epoch"] != "4"
                ):
                    raise SmokeError("BFF infected attempt recovery drift")
                status, body = _http_json(
                    bff_base,
                    complete_path,
                    token=ready.access_token,
                    secret=web_secret,
                    key=infected_complete_key,
                    body=infected_complete_body,
                )
                if (
                    status != 412
                    or body.get("error", {}).get("code") != "skill_precondition_failed"
                ):
                    raise SmokeError("stale infected Complete reached new attempt")
                status, body = _http_get_json(
                    bff_base,
                    begin_path,
                    token=ready.access_token,
                    secret=web_secret,
                )
                require_public_package_pending(
                    status,
                    body,
                    begin_skill_id,
                    str(recovered["attempt_id"]),
                    str(recovered["upload_id"]),
                    "4",
                )
                signed_put(recovered, payload)
                recovered_complete_body = {
                    **complete_body,
                    "attempt_id": recovered["attempt_id"],
                    "upload_id": recovered["upload_id"],
                }
                status, body = _http_json(
                    bff_base,
                    complete_path,
                    token=ready.access_token,
                    secret=web_secret,
                    key="package-recover-complete-" + run_id,
                    body=recovered_complete_body,
                )
                recovered_complete = require_public_package_complete(
                    status,
                    body,
                    begin_skill_id,
                    str(recovered["attempt_id"]),
                    str(recovered["upload_id"]),
                    "4",
                    str(begin_body["content_sha256"]),
                )
                if recovered_complete["replayed"] is not False:
                    raise SmokeError("BFF recovered Complete was unexpectedly replayed")
                deadline = time.monotonic() + 25
                while (
                    recovered_complete["scan_state"] != "clean"
                    and time.monotonic() < deadline
                ):
                    time.sleep(0.25)
                    status, body = _http_json(
                        bff_base,
                        complete_path,
                        token=ready.access_token,
                        secret=web_secret,
                        key="package-recover-complete-" + run_id,
                        body=recovered_complete_body,
                    )
                    recovered_complete = require_public_package_complete(
                        status,
                        body,
                        begin_skill_id,
                        str(recovered["attempt_id"]),
                        str(recovered["upload_id"]),
                        "4",
                        str(begin_body["content_sha256"]),
                    )
                if recovered_complete["scan_state"] != "clean":
                    raise SmokeError("BFF recovered Complete was not CLEAN")
                phase = Phase.CANDIDATE_PACKAGE_VALIDATE
                bad_payload = b"CLEAN scan is not ZIP validation"
                bad_begin_body = {
                    **begin_body,
                    "content_sha256": hashlib.sha256(bad_payload).hexdigest(),
                    "size_bytes": len(bad_payload),
                    "replaces_attempt_id": recovered["attempt_id"],
                }
                status, body = _http_json(
                    bff_base,
                    begin_path,
                    token=ready.access_token,
                    secret=web_secret,
                    key="package-bad-zip-begin-" + run_id,
                    body=bad_begin_body,
                )
                bad_begin = require_public_package_begin(
                    status,
                    body,
                    begin_skill_id,
                    source_env["KOKORO_OBJECT_STORE_PUBLIC_ENDPOINT"],
                )
                secret_values += signed_reference_secrets(
                    str(bad_begin["transfer_reference"]["url"])
                )
                if (
                    bad_begin["replayed"] is not False
                    or bad_begin["attempt_epoch"] != "5"
                ):
                    raise SmokeError("BFF bad ZIP Begin attempt drift")
                signed_put(bad_begin, bad_payload)
                bad_complete_body = {
                    "attempt_id": bad_begin["attempt_id"],
                    "upload_id": bad_begin["upload_id"],
                    "content_sha256": bad_begin_body["content_sha256"],
                    "size_bytes": len(bad_payload),
                }
                bad_complete_key = "package-bad-zip-complete-" + run_id
                status, body = _http_json(
                    bff_base,
                    complete_path,
                    token=ready.access_token,
                    secret=web_secret,
                    key=bad_complete_key,
                    body=bad_complete_body,
                )
                bad_complete = require_public_package_complete(
                    status,
                    body,
                    begin_skill_id,
                    str(bad_begin["attempt_id"]),
                    str(bad_begin["upload_id"]),
                    "5",
                    str(bad_begin_body["content_sha256"]),
                )
                deadline = time.monotonic() + 25
                while (
                    bad_complete["scan_state"] != "clean"
                    and time.monotonic() < deadline
                ):
                    time.sleep(0.25)
                    status, body = _http_json(
                        bff_base,
                        complete_path,
                        token=ready.access_token,
                        secret=web_secret,
                        key=bad_complete_key,
                        body=bad_complete_body,
                    )
                    bad_complete = require_public_package_complete(
                        status,
                        body,
                        begin_skill_id,
                        str(bad_begin["attempt_id"]),
                        str(bad_begin["upload_id"]),
                        "5",
                        str(bad_begin_body["content_sha256"]),
                    )
                if bad_complete["scan_state"] != "clean":
                    raise SmokeError("BFF bad ZIP did not reach CLEAN scan")
                validate_path = (
                    "/v1/skills/" + quote(begin_skill_id, safe="") + "/validate"
                )
                bad_validate_body = {"attempt_id": bad_begin["attempt_id"]}
                bad_validate_key = "package-bad-zip-validate-" + run_id
                for _ in range(2):
                    status, body = _http_json(
                        bff_base,
                        validate_path,
                        token=ready.access_token,
                        secret=web_secret,
                        key=bad_validate_key,
                        body=bad_validate_body,
                    )
                    if (
                        status != 412
                        or body.get("error", {}).get("code")
                        != "skill_precondition_failed"
                    ):
                        raise SmokeError("BFF CLEAN bad ZIP Validate did not reject")
                    status, body = _http_get_json(
                        bff_base,
                        begin_path,
                        token=ready.access_token,
                        secret=web_secret,
                    )
                    require_public_package_aborted(
                        status,
                        body,
                        begin_skill_id,
                        str(bad_begin["attempt_id"]),
                        str(bad_begin["upload_id"]),
                        "5",
                    )
                status, body = _http_json(
                    bff_base,
                    begin_path,
                    token=ready.access_token,
                    secret=web_secret,
                    key="package-zip-recover-begin-" + run_id,
                    body={**begin_body, "replaces_attempt_id": bad_begin["attempt_id"]},
                )
                zip_recovered = require_public_package_begin(
                    status,
                    body,
                    begin_skill_id,
                    source_env["KOKORO_OBJECT_STORE_PUBLIC_ENDPOINT"],
                )
                secret_values += signed_reference_secrets(
                    str(zip_recovered["transfer_reference"]["url"])
                )
                if (
                    zip_recovered["replayed"] is not False
                    or zip_recovered["attempt_epoch"] != "6"
                ):
                    raise SmokeError("BFF bad ZIP recovery attempt drift")
                signed_put(zip_recovered, payload)
                zip_complete_body = {
                    **complete_body,
                    "attempt_id": zip_recovered["attempt_id"],
                    "upload_id": zip_recovered["upload_id"],
                }
                zip_complete_key = "package-zip-recover-complete-" + run_id
                status, body = _http_json(
                    bff_base,
                    complete_path,
                    token=ready.access_token,
                    secret=web_secret,
                    key=zip_complete_key,
                    body=zip_complete_body,
                )
                zip_complete = require_public_package_complete(
                    status,
                    body,
                    begin_skill_id,
                    str(zip_recovered["attempt_id"]),
                    str(zip_recovered["upload_id"]),
                    "6",
                    str(begin_body["content_sha256"]),
                )
                deadline = time.monotonic() + 25
                while (
                    zip_complete["scan_state"] != "clean"
                    and time.monotonic() < deadline
                ):
                    time.sleep(0.25)
                    status, body = _http_json(
                        bff_base,
                        complete_path,
                        token=ready.access_token,
                        secret=web_secret,
                        key=zip_complete_key,
                        body=zip_complete_body,
                    )
                    zip_complete = require_public_package_complete(
                        status,
                        body,
                        begin_skill_id,
                        str(zip_recovered["attempt_id"]),
                        str(zip_recovered["upload_id"]),
                        "6",
                        str(begin_body["content_sha256"]),
                    )
                if zip_complete["scan_state"] != "clean":
                    raise SmokeError("BFF ZIP recovery Complete was not CLEAN")
                validate_body = {"attempt_id": zip_recovered["attempt_id"]}
                validate_key = "package-zip-validate-" + run_id
                status, body = _http_json(
                    bff_base,
                    validate_path,
                    token=ready.access_token,
                    secret=web_secret,
                    key=validate_key,
                    body=validate_body,
                )
                validation = require_public_skill_validate(
                    status,
                    body,
                    begin_skill_id,
                    str(begin_series_id),
                    str(begin_body["content_sha256"]),
                )
                if validation["replayed"] is not False:
                    raise SmokeError("BFF first Validate was unexpectedly replayed")
                status, body = _http_json(
                    bff_base,
                    validate_path,
                    token=ready.access_token,
                    secret=web_secret,
                    key=validate_key,
                    body=validate_body,
                )
                validation = require_public_skill_validate(
                    status,
                    body,
                    begin_skill_id,
                    str(begin_series_id),
                    str(begin_body["content_sha256"]),
                )
                if validation["replayed"] is not True:
                    raise SmokeError("BFF Validate replay drift")
                status, body = _http_get_json(
                    bff_base,
                    begin_path,
                    token=ready.access_token,
                    secret=web_secret,
                )
                require_public_package_validated(
                    status,
                    body,
                    begin_skill_id,
                    str(zip_recovered["attempt_id"]),
                    str(zip_recovered["upload_id"]),
                    "6",
                )
                status, body = _http_json(
                    bff_base,
                    validate_path,
                    token=ready.access_token,
                    secret=web_secret,
                    key="package-stale-validate-" + run_id,
                    body={"attempt_id": bad_begin["attempt_id"]},
                )
                if (
                    status != 412
                    or body.get("error", {}).get("code") != "skill_precondition_failed"
                ):
                    raise SmokeError("BFF stale Validate attempt did not reject")
                if platform_inventory(
                    urls["kokoro_platform"], ready.tenant_id, str(result["skill_id"])
                ) != (2, 30, 1, 1):
                    raise SmokeError("Platform public Validate inventory is not unique")
                if iam.stdin is None:
                    raise SmokeError("IAM command pipe absent")
                phase = Phase.REVOKE
                iam.stdin.write(b'{"command":"revoke-user-session"}\n')
                iam.stdin.flush()
                require_revoke_result(reader.record(timeout=30))
                before_revoked = proxy.count
                status, body = _http_json(
                    bff_base,
                    "/v1/skills/drafts",
                    token=ready.access_token,
                    secret=web_secret,
                    key=str(result["key"]),
                    body=result["body"],
                )
                if status != 401:
                    raise SmokeError("revoked IAM session was not rejected")
                status, body = _http_get_json(
                    bff_base,
                    get_path,
                    token=ready.access_token,
                    secret=web_secret,
                )
                if (
                    status != 401
                    or body.get("error", {}).get("code") != "session_invalid"
                ):
                    raise SmokeError("revoked IAM session reached BFF package GET")
                status, body = _http_json(
                    bff_base,
                    begin_path,
                    token=ready.access_token,
                    secret=web_secret,
                    key=begin_key,
                    body=begin_body,
                )
                if (
                    status != 401
                    or body.get("error", {}).get("code") != "session_invalid"
                ):
                    raise SmokeError("revoked IAM session reached BFF package Begin")
                status, body = _http_json(
                    bff_base,
                    complete_path,
                    token=ready.access_token,
                    secret=web_secret,
                    key=complete_key,
                    body=complete_body,
                )
                if (
                    status != 401
                    or body.get("error", {}).get("code") != "session_invalid"
                ):
                    raise SmokeError("revoked IAM session reached BFF package Complete")
                status, body = _http_json(
                    bff_base,
                    validate_path,
                    token=ready.access_token,
                    secret=web_secret,
                    key=validate_key,
                    body=validate_body,
                )
                if (
                    status != 401
                    or body.get("error", {}).get("code") != "session_invalid"
                ):
                    raise SmokeError("revoked IAM session reached BFF Skill Validate")
                time.sleep(0.2)
                if proxy.count != before_revoked:
                    raise SmokeError("revoked request opened a Platform socket")
                summary = safe_summary(None)
                summary["storage_v2_package_reference"] = "PASS"
    except BaseException as exc:
        error = (
            exc
            if isinstance(exc, SmokeError)
            else SmokeError(f"{phase.value} failed ({type(exc).__name__})")
        )
    finally:
        phase = Phase.CLEANUP
        if proxy is not None:
            try:
                proxy.close()
            except BaseException:
                if error is None:
                    error = SmokeError("owned proxy cleanup failed")
                else:
                    error = SmokeError(
                        "smoke execution failed; owned proxy cleanup failed"
                    )
        iam_process = processes[0] if processes else None
        process_failures = stop_owned_processes(processes[1:], iam_process, reader)
        if process_failures and error is None:
            error = SmokeError(process_failures[0])
        elif process_failures:
            error = SmokeError("smoke execution failed; " + process_failures[0])
        if reader is not None:
            try:
                reader.close()
            except Exception:
                pass
        try:
            log_bytes = log_path.read_bytes()
            if any(secret and secret.encode() in log_bytes for secret in secret_values):
                error = SmokeError(
                    "smoke execution failed; owner logs contain credential material"
                )
        except OSError:
            if error is None:
                error = SmokeError("owner log verification failed")
        try:
            shutil.rmtree(directory)
            if directory.exists():
                raise OSError("directory remained")
        except OSError:
            if error is None:
                error = SmokeError("temporary credential directory cleanup failed")
            else:
                error = SmokeError(
                    "smoke execution failed; temporary credential directory cleanup failed"
                )
    if bucket_state["created"] and s3 is not None:
        try:
            delete_owned_bucket(s3, owned_bucket, storage_helper)
            require_bucket_absent(s3, owned_bucket)
        except BaseException:
            if error is None:
                error = SmokeError("owned bucket cleanup failed")
            else:
                error = SmokeError(
                    "smoke execution failed; owned bucket cleanup failed"
                )
    cleanup_failures = verify_cleanup(
        before_redis=set(),
        redis_snapshot=lambda: (
            set()
            if redis_prefix is None
            else (
                _redis_keys(args.redis_url, redis_prefix + "*")
                | _redis_keys(args.redis_url, "*" + run_id + "*")
                | (
                    set()
                    if ready is None
                    else _redis_keys(args.redis_url, "*" + ready.tenant_id + "*")
                )
            )
        ),
        database_name=database_name,
        database_exists=lambda name: _database_exists(admin_url, name),
    )
    if cleanup_failures and error is None:
        error = SmokeError(cleanup_failures[0])
    elif cleanup_failures:
        error = SmokeError("smoke execution failed; " + cleanup_failures[0])
    restore_sigterm()
    return (
        summary
        if error is None and summary is not None
        else safe_summary(error, secret_values)
    )


def main() -> int:
    class SafeParser(argparse.ArgumentParser):
        def error(self, _message: str) -> None:
            raise SmokeError("invalid runner arguments")

    parser = SafeParser(description=__doc__, add_help=False)
    parser.add_argument("--postgres-admin-url", required=True)
    parser.add_argument("--redis-url", required=True)
    parser.add_argument("--iam-node", required=True, type=Path)
    parser.add_argument("--bff-node", required=True, type=Path)
    parser.add_argument("--platform-node", required=True, type=Path)
    parser.add_argument("--storage-node", required=True, type=Path)
    parser.add_argument("--exclusive-bucket", required=True)
    try:
        ns = parser.parse_args()
        result = execute(
            RunArguments(
                ns.postgres_admin_url,
                ns.redis_url,
                ns.iam_node,
                ns.bff_node,
                ns.platform_node,
                ns.storage_node,
                ns.exclusive_bucket,
            )
        )
    except BaseException as exc:
        result = safe_summary(exc)
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
