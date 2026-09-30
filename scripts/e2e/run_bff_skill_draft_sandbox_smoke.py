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
import base64
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
from uuid import UUID, uuid4
from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit


try:
    from scripts.e2e import agent_skill_source_smoke as source_helper
    from scripts.e2e import product_skill_installation_smoke as product_helper
except ModuleNotFoundError:
    import agent_skill_source_smoke as source_helper
    import product_skill_installation_smoke as product_helper


ROOT = Path(__file__).resolve().parents[2]
OWNERS = {
    "iam": ROOT / "apps/kokoro-iam",
    "bff": ROOT / "apps/kokoro-bff",
    "platform": ROOT / "apps/kokoro-capability",
    "storage": ROOT / "apps/kokoro-storage",
}
LOCAL_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})
# Keep stdin/protocol handles alive after a failed drain: GC/EOF can otherwise
# make IAM tear down its DB while a Source executor still uses it. No new work
# is scheduled; these exceptional resources need explicit operator cleanup.
_RETAINED_SOURCE_RESOURCES: list[tuple[object, ...]] = []


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
    CANDIDATE_PUBLISH = "candidate_publish"
    PROJECTION_READ = "projection_read"
    PACKAGE_REFERENCE = "package_reference"
    AGENT_SOURCE = "agent_source"
    PRODUCT_INSTALLATION = "product_installation"
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
    projection: CatalogCredential
    resource_server: CatalogCredential
    execution_authorization: CatalogCredential
    web_client_secret: str
    user_password: str
    tenant_execution: CatalogCredential | None = None

    @property
    def secrets(self) -> tuple[str, ...]:
        values = (
            self.access_token,
            self.catalog.client_secret,
            self.projection.client_secret,
            self.resource_server.client_secret,
            self.execution_authorization.client_secret,
            self.web_client_secret,
            self.user_password,
        )
        if self.tenant_execution is not None:
            values += (self.tenant_execution.client_secret,)
        return values


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


def require_sandbox_ready(
    record: object, *, agent_source: bool = False
) -> SandboxReady:
    """Strictly accept the IAM opt-in protocol without copying owner policy."""
    if type(agent_source) is not bool:
        raise SmokeError("IAM Agent source mode must be an explicit boolean")
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
    sandbox_fields = {
        "access_token",
        "subject_id",
        "catalog_client",
        "projection_client",
        "resource_server_basic",
        "execution_authorization_client",
    }
    if agent_source:
        sandbox_fields.add("tenant_execution_client")
    if not isinstance(sandbox, dict) or set(sandbox) != sandbox_fields:
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
        _credential(sandbox["projection_client"], "projection client"),
        _credential(sandbox["resource_server_basic"], "resource server"),
        _credential(execution, "execution authorization client"),
        _nonempty(record["client_secret"], "Web client secret"),
        _nonempty(record["password"], "user password"),
        _credential(sandbox["tenant_execution_client"], "Agent execution client")
        if agent_source
        else None,
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


def require_public_skill_publish(
    status: int, body: object, skill_id: str
) -> dict[str, object]:
    """Accept only the owner-backed active publication and public fields."""
    if status != 200 or not isinstance(body, dict) or set(body) != {"data"}:
        raise SmokeError("BFF Skill Publish response invalid")
    data = body["data"]
    if not isinstance(data, dict) or set(data) != {
        "source_ref",
        "revision",
        "status",
        "event_id",
        "replayed",
    }:
        raise SmokeError("BFF Skill Publish data invalid")
    revision = data["revision"]
    event_id = data["event_id"]
    if (
        data["source_ref"] != "skill:" + skill_id
        or not isinstance(revision, str)
        or len(revision) > 20
        or re.fullmatch(r"[1-9][0-9]*", revision) is None
        or int(revision) > 18_446_744_073_709_551_615
        or data["status"] != "active"
        or not isinstance(event_id, str)
        or type(data["replayed"]) is not bool
    ):
        raise SmokeError("BFF Skill Publish projection invalid")
    try:
        if str(UUID(event_id)) != event_id:
            raise ValueError("noncanonical UUID")
    except ValueError:
        raise SmokeError("BFF Skill Publish event invalid") from None
    return data


def require_platform_published_skill_absent(status: int, body: object) -> None:
    """A draft, foreign or non-active Skill is indistinguishable from missing."""
    if status != 404 or body != {
        "error": {
            "code": "capability.route_not_found",
            "message": "Capability BFF route was not found",
            "retryable": False,
        }
    }:
        raise SmokeError("Platform unpublished Skill read was not private 404")


def require_platform_guard_denial(
    status: int, body: object, code: str, message: str
) -> None:
    allowed = {
        (401, "capability.service_auth_failed", "BFF workload bearer is required"),
        (401, "capability.service_auth_failed", "BFF workload authentication failed"),
        (403, "capability.tenant_mismatch", "BFF tenant does not match IAM"),
    }
    if (status, code, message) not in allowed or body != {
        "error": {"code": code, "message": message, "retryable": False}
    }:
        observed_code = (
            body.get("error", {}).get("code")
            if isinstance(body, dict) and isinstance(body.get("error"), dict)
            else None
        )
        safe_code = (
            observed_code
            if isinstance(observed_code, str)
            and re.fullmatch(r"[a-z][a-z0-9_.]{0,63}", observed_code)
            else "unknown"
        )
        raise SmokeError(
            "Platform projection guard did not fail closed: "
            f"observed status={status} code={safe_code}"
        )


def require_platform_published_skill_read(
    status: int, body: object, skill_id: str, revision: str
) -> None:
    """Accept only the public-safe owner projection, never package metadata."""
    if status != 200 or not isinstance(body, dict) or set(body) != {"data"}:
        raise SmokeError("Platform published Skill response invalid")
    data = body["data"]
    if not isinstance(data, dict) or set(data) != {
        "skill_id",
        "source_ref",
        "revision",
        "status",
        "name",
        "summary",
        "tags",
    }:
        raise SmokeError("Platform published Skill fields invalid")
    if (
        data["skill_id"] != skill_id
        or data["source_ref"] != "skill:" + skill_id
        or data["revision"] != revision
        or not isinstance(revision, str)
        or re.fullmatch(r"[1-9][0-9]{0,19}", revision) is None
        or int(revision) > 18_446_744_073_709_551_615
        or data["status"] != "active"
        or not isinstance(data["name"], str)
        or not isinstance(data["summary"], str)
        or not isinstance(data["tags"], list)
        or any(not isinstance(tag, str) for tag in data["tags"])
    ):
        raise SmokeError("Platform published Skill projection invalid")


def require_bff_projection_revoked(status: int, body: object) -> None:
    """A revoked Product session must not return any Skill projection bytes."""
    if status != 401 or not isinstance(body, dict) or set(body) != {"error"}:
        raise SmokeError("revoked IAM session exposed BFF Skill projection")
    error = body["error"]
    if (
        not isinstance(error, dict)
        or set(error) != {"code", "message", "retryable"}
        or error["code"] != "session_invalid"
        or error["message"] != "BFF user admission failed"
        or error["retryable"] is not False
    ):
        raise SmokeError("revoked IAM session exposed BFF Skill projection")


def require_bff_personal_skill_list(
    status: int, body: object, skill_id: str, revision: str
) -> None:
    """Validate the entire public page, not only one matching reference."""
    if status != 200 or not isinstance(body, dict) or set(body) != {"data"}:
        raise SmokeError("BFF personal Skill list envelope invalid")
    page = body["data"]
    if not isinstance(page, dict) or not {"skills"} <= set(page) <= {
        "skills",
        "next_cursor",
    }:
        raise SmokeError("BFF personal Skill list page invalid")
    if (
        not isinstance(page["skills"], list)
        or len(page["skills"]) > 100
        or (
            "next_cursor" in page
            and page["next_cursor"] is not None
            and (not isinstance(page["next_cursor"], str) or not page["next_cursor"])
        )
    ):
        raise SmokeError("BFF personal Skill list page invalid")
    required = {
        "source_ref",
        "name",
        "description",
        "content_hash",
        "scope",
        "revision",
        "enabled",
        "categories",
    }
    matches = 0
    for item in page["skills"]:
        if not isinstance(item, dict) or not required <= set(item) <= required | {
            "installed"
        }:
            raise SmokeError("BFF personal Skill list item invalid")
        item_revision = item["revision"]
        if (
            not isinstance(item["source_ref"], str)
            or not item["source_ref"].startswith("skill:")
            or any(
                not isinstance(item[key], str)
                for key in ("name", "description", "content_hash")
            )
            or item["scope"] != "personal"
            or not isinstance(item_revision, str)
            or re.fullmatch(r"[1-9][0-9]{0,19}", item_revision) is None
            or int(item_revision) > 18_446_744_073_709_551_615
            or not isinstance(item["enabled"], bool)
            or not isinstance(item["categories"], list)
            or any(not isinstance(category, str) for category in item["categories"])
            or ("installed" in item and not isinstance(item["installed"], bool))
        ):
            raise SmokeError("BFF personal Skill list item invalid")
        if item["source_ref"] == "skill:" + skill_id:
            matches += 1
            if item_revision != revision:
                raise SmokeError("BFF personal Skill list revision drift")
    if matches != 1:
        raise SmokeError("BFF personal Skill list lost published Skill")


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
            "platform_receipt_count": 31,
            "platform_publish_event_count": 2,
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
            "bff_skill_publish": "PASS",
            "bff_skill_publish_replay": "PASS",
            "bff_skill_publish_conflict": "PASS",
            "bff_skill_publish_event_durable": "PASS",
            "bff_skill_publish_revoked": "PASS",
            "platform_published_by_id": "PASS",
            "platform_published_private": "PASS",
            "bff_published_before_publish": "PASS",
            "bff_published_after_publish": "PASS",
            "bff_personal_skill_list": "PASS",
            "bff_published_read_revoked": "PASS",
            "bff_personal_list_revoked": "PASS",
        }
    detail = (
        str(error)
        if isinstance(
            error, (SmokeError, source_helper.SourceError, product_helper.ProductError)
        )
        else "smoke execution failed"
    )
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
) -> tuple[
    dict[str, object],
    list[dict[str, object]],
    list[dict[str, object]],
    list[dict[str, object]],
]:
    """Project IAM handles into owner-defined, scope-separated snapshots."""
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
    projection = [
        {
            **common,
            "tenantId": ready.tenant_id,
            "clientId": ready.projection.client_id,
            "clientSecret": ready.projection.client_secret,
            "resource": "https://kokoro.dev/resources/platform-internal",
            "scope": "platform:projection.read",
        }
    ]
    return resource, execution, catalog, projection


@contextmanager
def credential_files(directory: Path, ready: SandboxReady) -> Iterator[dict[str, Path]]:
    payloads = platform_credential_payloads(ready)
    names = (
        "resource-server.json",
        "tenant-execution.json",
        "bff-catalog.json",
        "bff-projection.json",
    )
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


def _http_publish_empty(
    base: str, path: str, *, token: str, secret: str, key: str
) -> tuple[int, dict[str, object]]:
    """Send exactly zero body bytes for the fixed PERSONAL Publish command."""
    parsed = urlsplit(base)
    connection = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=8)
    request_id = "skill-sandbox-" + secrets.token_hex(8)
    try:
        connection.request(
            "POST",
            path,
            body=b"",
            headers={
                "authorization": "Bearer " + token,
                "x-kokoro-service": "web-bff",
                "x-kokoro-internal-secret": secret,
                "x-kokoro-request-id": request_id,
                "idempotency-key": key,
                "content-length": "0",
            },
        )
        response = connection.getresponse()
        raw = response.read(1_048_577)
        headers = response.getheaders()
    finally:
        connection.close()
    if len(raw) > 1_048_576:
        raise SmokeError("BFF Publish response too large")
    require_package_response_headers(headers, request_id, "Publish")
    try:
        value = json.loads(raw)
    except (ValueError, UnicodeError):
        raise SmokeError("BFF Publish response is not JSON") from None
    if not isinstance(value, dict):
        raise SmokeError("BFF Publish response envelope invalid")
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


def issue_projection_token(ready: SandboxReady) -> str:
    """Exchange only IAM's BFF projection client for its exact workload scope."""
    parsed = urlsplit(local_http_origin(ready.base_url, "IAM"))
    connection = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=8)
    credential = base64.b64encode(
        f"{ready.projection.client_id}:{ready.projection.client_secret}".encode()
    ).decode("ascii")
    body = urlencode(
        {
            "grant_type": "client_credentials",
            "scope": "platform:projection.read",
            "resource": "https://kokoro.dev/resources/platform-internal",
        }
    ).encode("ascii")
    try:
        connection.request(
            "POST",
            "/iam/oauth2/token",
            body=body,
            headers={
                "authorization": "Basic " + credential,
                "content-type": "application/x-www-form-urlencoded",
            },
        )
        response = connection.getresponse()
        raw = response.read(16_385)
    finally:
        connection.close()
    if response.status != 200 or len(raw) > 16_384:
        raise SmokeError("IAM projection token exchange failed")
    try:
        value = json.loads(raw)
    except (ValueError, UnicodeError):
        raise SmokeError("IAM projection token response invalid") from None
    if (
        not isinstance(value, dict)
        or value.get("token_type") != "Bearer"
        or not isinstance(value.get("access_token"), str)
        or not value["access_token"]
    ):
        raise SmokeError("IAM projection token response invalid")
    return value["access_token"]


def platform_published_skill_get(
    base: str,
    skill_id: str,
    token: str,
    ready: SandboxReady,
    *,
    subject: str | None = None,
    tenant_assertion: str | None = None,
) -> tuple[int, dict[str, object]]:
    """Probe Platform HTTP through its real IAM workload guard, not BFF SQL."""
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,190}", skill_id) is None:
        raise SmokeError("Platform published Skill ID invalid")
    tenant = ready.tenant_id if tenant_assertion is None else tenant_assertion
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,190}", tenant) is None:
        raise SmokeError("Platform tenant assertion invalid")
    parsed = urlsplit(local_http_origin(base, "Platform"))
    connection = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=8)
    request_id = "skill-sandbox-" + secrets.token_hex(8)
    try:
        connection.request(
            "GET",
            "/v1/skills/" + quote(skill_id, safe=""),
            headers={
                "authorization": "Bearer " + token,
                "x-kokoro-tenant-id": tenant,
                "x-kokoro-subject": ready.subject_id if subject is None else subject,
                "x-kokoro-request-id": request_id,
            },
        )
        response = connection.getresponse()
        raw = response.read(1_048_577)
        headers = response.getheaders()
    finally:
        connection.close()
    if len(raw) > 1_048_576:
        raise SmokeError("Platform published Skill response too large")
    returned_id = [
        value for name, value in headers if name.lower() == "x-kokoro-request-id"
    ]
    cache = [value for name, value in headers if name.lower() == "cache-control"]
    if returned_id != [request_id] or cache != ["no-store"]:
        raise SmokeError("Platform by-ID response headers invalid")
    try:
        value = json.loads(raw)
    except (ValueError, UnicodeError):
        raise SmokeError("Platform published Skill response not JSON") from None
    if not isinstance(value, dict):
        raise SmokeError("Platform published Skill response envelope invalid")
    return response.status, value


def upload_zip_bytes(
    skill_id: str, revision: int, *, agent_source: bool = False
) -> bytes:
    """A bounded owner ZIP V1 bound to the fresh draft's identity."""
    if type(agent_source) is not bool:
        raise SmokeError("ZIP Source mode must be explicit")
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
        archive.writestr(
            "SKILL.md",
            source_helper.SKILL_BYTES
            if agent_source
            else b"# Sandbox\n\nOwned signed PUT smoke.\n",
        )
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


def platform_publish_event(
    database_url: str,
    tenant: str,
    skill_id: str,
    event_id: str,
    revision: str,
    attempt_id: str,
) -> int:
    """Read only the owner outbox row bound to this public Publish result."""
    import psycopg

    with (
        psycopg.connect(
            platform_inventory_connection_url(database_url), connect_timeout=5
        ) as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute(
            'SELECT count(*) FROM "kokoro_platform"."outbox_event" '
            "WHERE tenant_id = %s AND event_id = %s AND event_type = %s "
            "AND aggregate_type = %s AND aggregate_id = %s "
            "AND payload_json ->> 'source_ref' = %s "
            "AND payload_json ->> 'revision' = %s "
            "AND payload_json -> 'package' ->> 'attempt_id' = %s",
            (
                tenant,
                event_id,
                "skill.published",
                "skill",
                skill_id,
                "skill:" + skill_id,
                revision,
                attempt_id,
            ),
        )
        return int(cursor.fetchone()[0])


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
    agent_source: bool = False
    agent_redis_url: str | None = None
    product_installation: bool = False


def platform_surfaces(args: RunArguments) -> str:
    product_helper.preflight(args.product_installation, args.agent_source)
    base = "skill-catalog,skill-source"
    if args.product_installation:
        return base + ",skill-installation-product"
    if args.agent_source:
        return base + ",skill-installation"
    return base


def owned_bucket_name(prefix: str, run_id: str) -> str:
    base = prefix.rstrip(".-")[: 63 - len(run_id) - 1].rstrip(".-")
    if not base or re.fullmatch(r"[a-z0-9][a-z0-9.-]*", base) is None:
        raise SmokeError("exclusive bucket prefix invalid")
    return f"{base}-{run_id}"


def execute(args: RunArguments, env: dict[str, str] | None = None) -> dict[str, object]:
    """Run the real composition. Source freezing happens before all side effects."""
    product_helper.preflight(args.product_installation, args.agent_source)
    source_helper.preflight(args.agent_source, args.agent_redis_url, args.redis_url)
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
    agent_source = None
    source_cleanup_failures: list[str] = []
    source_dependencies_retained = False
    source_execution_error: str | None = None
    source_result = None
    product_installation = None
    product_result = None
    product_inventory = None
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
            # Never inherit opt-in mode or a JWKS target from the caller environment.
            iam_env["IAM_TEST_AGENT_SKILL_SOURCE_MODE"] = "0"
            iam_env.pop("IAM_TEST_AGENT_JWKS_URL", None)
            if args.agent_source:
                agent_source = source_helper.AgentSourceDriver(
                    directory,
                    source_helper.database_url(admin_url, expected_database),
                    args.agent_redis_url,
                    run_id,
                )
                secret_values += (
                    agent_source.secret,
                    urlsplit(args.agent_redis_url).password or "",
                )
                agent_source.start_http()
                iam_env["IAM_TEST_AGENT_SKILL_SOURCE_MODE"] = "1"
                iam_env["IAM_TEST_AGENT_JWKS_URL"] = agent_source.jwks_url
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
            ready = require_sandbox_ready(
                reader.record(timeout=60), agent_source=args.agent_source
            )
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
                "KOKORO_PLATFORM_SURFACES": platform_surfaces(args),
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
                        "KOKORO_PLATFORM_PROJECTION_CREDENTIAL_FILE": str(
                            files["bff-projection.json"]
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
                status, body = _http_publish_empty(
                    bff_base,
                    "/v1/skills/sandbox-closed/publish",
                    token=ready.access_token,
                    secret=web_secret,
                    key="closed-publish",
                )
                if (
                    status != 503
                    or body.get("error", {}).get("code")
                    != "skill_dependency_unavailable"
                ):
                    raise SmokeError("default-off BFF Publish did not fail closed")
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
                if args.product_installation:
                    phase = Phase.PRODUCT_INSTALLATION
                    product_installation = product_helper.ProductInstallationSmoke(
                        product_helper.PublicInstallationHttp(
                            bff_base, ready.access_token, web_secret
                        ),
                        run_id,
                    )
                    product_installation.before_publish("skill:" + begin_skill_id)
                phase = Phase.PROJECTION_READ
                published_path = "/v1/skills/" + quote(begin_skill_id, safe="")
                status, body = _http_get_json(
                    bff_base,
                    published_path,
                    token=ready.access_token,
                    secret=web_secret,
                )
                if status != 404 or body != {
                    "error": {
                        "code": "skill_not_found",
                        "message": "Skill was not found",
                        "retryable": False,
                    }
                }:
                    raise SmokeError("BFF unpublished Skill read was not private 404")
                projection_token = issue_projection_token(ready)
                secret_values += (projection_token,)
                status, body = platform_published_skill_get(
                    platform_base,
                    begin_skill_id,
                    projection_token,
                    ready,
                )
                require_platform_published_skill_absent(status, body)
                phase = Phase.CANDIDATE_PACKAGE_BEGIN
                begin_path = (
                    "/v1/skills/" + quote(begin_skill_id, safe="") + "/package-upload"
                )
                payload = upload_zip_bytes(
                    begin_skill_id, 1, agent_source=args.agent_source
                )
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
                phase = Phase.CANDIDATE_PUBLISH
                publish_path = (
                    "/v1/skills/" + quote(begin_skill_id, safe="") + "/publish"
                )
                publish_key = "package-publish-" + run_id
                status, body = _http_publish_empty(
                    bff_base,
                    publish_path,
                    token=ready.access_token,
                    secret=web_secret,
                    key=publish_key,
                )
                publication = require_public_skill_publish(status, body, begin_skill_id)
                if publication["replayed"] is not False:
                    raise SmokeError("BFF first Publish was unexpectedly replayed")
                event_id = publication["event_id"]
                revision = publication["revision"]
                phase = Phase.PROJECTION_READ
                status, body = platform_published_skill_get(
                    platform_base,
                    begin_skill_id,
                    "",
                    ready,
                )
                require_platform_guard_denial(
                    status,
                    body,
                    "capability.service_auth_failed",
                    "BFF workload bearer is required",
                )
                status, body = platform_published_skill_get(
                    platform_base,
                    begin_skill_id,
                    "invalid-projection-token",
                    ready,
                )
                require_platform_guard_denial(
                    status,
                    body,
                    "capability.service_auth_failed",
                    "BFF workload authentication failed",
                )
                status, body = platform_published_skill_get(
                    platform_base,
                    begin_skill_id,
                    projection_token,
                    ready,
                    tenant_assertion="other-tenant",
                )
                require_platform_guard_denial(
                    status,
                    body,
                    "capability.tenant_mismatch",
                    "BFF tenant does not match IAM",
                )
                status, body = platform_published_skill_get(
                    platform_base,
                    begin_skill_id,
                    projection_token,
                    ready,
                )
                require_platform_published_skill_read(
                    status, body, begin_skill_id, str(revision)
                )
                if body["data"] != {
                    "skill_id": begin_skill_id,
                    "source_ref": "skill:" + begin_skill_id,
                    "revision": revision,
                    "status": "active",
                    "name": "Signed PUT sandbox skill",
                    "summary": "public Begin probe",
                    "tags": ["sandbox"],
                }:
                    raise SmokeError("Platform published Skill content drift")
                status, public_read = _http_get_json(
                    bff_base,
                    published_path,
                    token=ready.access_token,
                    secret=web_secret,
                )
                require_platform_published_skill_read(
                    status, public_read, begin_skill_id, str(revision)
                )
                if public_read != body:
                    raise SmokeError(
                        "BFF published Skill projection drifted from owner"
                    )
                status, public_list = _http_get_json(
                    bff_base,
                    "/v1/skills?scope_kind=personal&limit=100",
                    token=ready.access_token,
                    secret=web_secret,
                )
                require_bff_personal_skill_list(
                    status, public_list, begin_skill_id, str(revision)
                )
                status, body = platform_published_skill_get(
                    platform_base,
                    begin_skill_id,
                    projection_token,
                    ready,
                    subject="other-user",
                )
                require_platform_published_skill_absent(status, body)
                phase = Phase.CANDIDATE_PUBLISH
                status, body = _http_publish_empty(
                    bff_base,
                    publish_path,
                    token=ready.access_token,
                    secret=web_secret,
                    key=publish_key,
                )
                publication = require_public_skill_publish(status, body, begin_skill_id)
                if (
                    publication["replayed"] is not True
                    or publication["event_id"] != event_id
                    or publication["revision"] != revision
                ):
                    raise SmokeError("BFF Publish replay changed the owner event")
                status, body = _http_publish_empty(
                    bff_base,
                    publish_path,
                    token=ready.access_token,
                    secret=web_secret,
                    key="package-publish-second-" + run_id,
                )
                if (
                    status != 412
                    or body.get("error", {}).get("code") != "skill_precondition_failed"
                ):
                    raise SmokeError("BFF second Publish on active Skill was accepted")
                status, body = _http_get_json(
                    bff_base,
                    begin_path,
                    token=ready.access_token,
                    secret=web_secret,
                )
                if (
                    status != 412
                    or body.get("error", {}).get("code") != "skill_precondition_failed"
                ):
                    raise SmokeError("BFF published Skill package GET stayed draft")
                if platform_inventory(
                    urls["kokoro_platform"], ready.tenant_id, begin_skill_id
                ) != (2, 31, 2, 1):
                    raise SmokeError("Platform public Publish inventory is not unique")
                if (
                    platform_publish_event(
                        urls["kokoro_platform"],
                        ready.tenant_id,
                        begin_skill_id,
                        str(event_id),
                        str(revision),
                        str(zip_recovered["attempt_id"]),
                    )
                    != 1
                ):
                    raise SmokeError("Platform public Publish event was not durable")
                if iam.stdin is None:
                    raise SmokeError("IAM command pipe absent")
                if product_installation is not None:
                    phase = Phase.PRODUCT_INSTALLATION
                    # Catalog probes and Product reads share IAM's resource-client
                    # window. Yield before exercising the full public sequence.
                    source_helper.wait_for_iam_window(args.product_installation)
                    product_result = product_installation.exercise(
                        ("skill:" + str(result["skill_id"]), "skill:" + begin_skill_id)
                    )
                    product_inventory = platform_inventory(
                        urls["kokoro_platform"], ready.tenant_id, begin_skill_id
                    )
                    if product_inventory[0] != 2 or product_inventory[2:] != (2, 1):
                        raise SmokeError(
                            "Product installation changed publication facts"
                        )
                if agent_source is not None:
                    phase = Phase.AGENT_SOURCE
                    before_source = platform_inventory(
                        urls["kokoro_platform"], ready.tenant_id, begin_skill_id
                    )

                    def revoke_execution() -> object:
                        iam.stdin.write(b'{"command":"revoke-agent-execution"}\n')
                        iam.stdin.flush()
                        return reader.record(timeout=30)

                    with zipfile.ZipFile(io.BytesIO(payload)) as original_package:
                        expected_skill = original_package.read("SKILL.md")
                    # Prior catalog/projection probes share IAM's resource-client
                    # quota. Yield its full window before creating any Agent lease.
                    source_helper.wait_for_iam_window(args.agent_source)
                    source_result = agent_source.exercise(
                        ready,
                        platform_base,
                        source_env["KOKORO_OBJECT_STORE_PUBLIC_ENDPOINT"],
                        begin_skill_id,
                        int(revision),
                        expected_skill,
                        revoke_execution,
                    )
                    source_helper.require_inventory(
                        before_source,
                        platform_inventory(
                            urls["kokoro_platform"], ready.tenant_id, begin_skill_id
                        ),
                    )
                phase = Phase.REVOKE
                iam.stdin.write(b'{"command":"revoke-user-session"}\n')
                iam.stdin.flush()
                require_revoke_result(reader.record(timeout=30))
                before_revoked = proxy.count
                if product_installation is not None:
                    product_installation.require_revoked("skill:" + begin_skill_id)
                status, body = _http_get_json(
                    bff_base,
                    published_path,
                    token=ready.access_token,
                    secret=web_secret,
                )
                require_bff_projection_revoked(status, body)
                status, body = _http_get_json(
                    bff_base,
                    "/v1/skills?scope_kind=personal&limit=100",
                    token=ready.access_token,
                    secret=web_secret,
                )
                require_bff_projection_revoked(status, body)
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
                status, body = _http_publish_empty(
                    bff_base,
                    publish_path,
                    token=ready.access_token,
                    secret=web_secret,
                    key=publish_key,
                )
                if (
                    status != 401
                    or body.get("error", {}).get("code") != "session_invalid"
                ):
                    raise SmokeError("revoked IAM session reached BFF Skill Publish")
                time.sleep(0.2)
                if proxy.count != before_revoked:
                    raise SmokeError("revoked request opened a Platform socket")
                summary = safe_summary(None)
                summary["storage_v2_package_reference"] = "PASS"
                if source_result is not None:
                    summary["agent_source"] = source_result
                    summary["platform_source_final_receipt_count"] = 34
                if product_result is not None and product_inventory is not None:
                    summary["product_installation"] = {
                        **product_result,
                        "unpublished_own_source_precondition": True,
                        "missing_source_private_not_found": True,
                        "revoked_five_operations_before_owner": True,
                    }
                    summary["platform_receipt_count"] = product_inventory[1]
                    summary["product_execution_boundary"] = (
                        "Agent disabled; no SourceDriver (structural, not Run-store observation)"
                    )
    except BaseException as exc:
        error = (
            exc
            if isinstance(
                exc,
                (SmokeError, source_helper.SourceError, product_helper.ProductError),
            )
            else SmokeError(f"{phase.value} failed ({type(exc).__name__})")
        )
        source_execution_error = str(error)
    finally:
        phase = Phase.CLEANUP
        # Agent pools/HTTP/owned Redis close before IAM drops the shared temporary DB.
        if agent_source is not None:
            source_cleanup_failures = agent_source.close()
            source_dependencies_retained = not agent_source.dependencies_quiescent
            if source_dependencies_retained:
                _RETAINED_SOURCE_RESOURCES.append(
                    (agent_source, tuple(processes), reader, proxy, s3)
                )
            if source_cleanup_failures:
                original = "" if error is None else str(error) + "; "
                error = SmokeError(original + "; ".join(source_cleanup_failures))
        # A timed-out executor may still be using IAM/HTTP/DB/object resources.
        # Preserve them for explicit operator cleanup, rather than deleting under it.
        if not source_dependencies_retained:
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
            if not source_cleanup_failures:
                shutil.rmtree(directory)
            if not source_cleanup_failures and directory.exists():
                raise OSError("directory remained")
        except OSError:
            if error is None:
                error = SmokeError("temporary credential directory cleanup failed")
            else:
                error = SmokeError(
                    "smoke execution failed; temporary credential directory cleanup failed"
                )
    if not source_dependencies_retained and bucket_state["created"] and s3 is not None:
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
    result = (
        summary
        if error is None and summary is not None
        else safe_summary(error, secret_values)
    )
    if source_dependencies_retained:
        result["agent_source_dependencies"] = "retained: activity not quiescent"
        result["agent_source_retained_process_ids"] = [
            process.pid for process in processes
        ]
    if source_cleanup_failures:
        result["agent_source_cleanup"] = source_cleanup_failures
        result["agent_source_evidence_directory"] = str(directory)
        if source_execution_error is not None:
            result["agent_source_execution_error"] = safe_summary(
                SmokeError(source_execution_error), secret_values
            )["error"]
    return result


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
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--agent-source", action="store_true")
    modes.add_argument("--product-installation", action="store_true")
    parser.add_argument("--agent-redis-url")
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
                ns.agent_source,
                ns.agent_redis_url,
                ns.product_installation,
            )
        )
    except BaseException as exc:
        result = safe_summary(exc)
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
