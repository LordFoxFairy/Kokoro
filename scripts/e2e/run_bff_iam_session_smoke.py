"""Shared Root IAM fixture and BFF smoke helpers; the historical CLI is retired."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import selectors
import subprocess
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import ProxyHandler, Request, build_opener

if __package__:
    from . import capability_bff_smoke_runtime as runtime
else:
    import capability_bff_smoke_runtime as runtime

ROOT = Path(__file__).resolve().parents[2]
MAX_LINE = 16_384


class SmokeError(RuntimeError):
    pass


@dataclass(frozen=True)
class Ready:
    base_url: str
    access_token: str
    tenant_id: str
    user_id: str


def verify_source(repo: Path, expected: str, gitlink: str, allow_unpublished: bool = False) -> dict[str, object]:
    actual = runtime.command_output(["git", "-C", str(repo), "rev-parse", "HEAD"]).strip()
    clean = runtime.command_output(["git", "-C", str(repo), "status", "--porcelain", "--untracked-files=all"]).strip() == ""
    tree = runtime.command_output(["git", "-C", str(ROOT), "ls-tree", "HEAD", gitlink]).strip().split()
    published = len(tree) >= 3 and tree[2] == actual
    if actual != expected or not clean or (not published and not allow_unpublished):
        raise SmokeError(f"{repo.name} source identity, cleanliness, or Root gitlink mismatch")
    return {"sha": actual, "clean": clean, "root_gitlink_matches": published}


def validate_ready(record):
    if not isinstance(record, dict) or set(record) != {"kind", "base_url", "access_token", "tenant_id", "user_id"} or record["kind"] != "ready":
        raise SmokeError("IAM host ready protocol drift")
    if any(not isinstance(record[key], str) or not record[key] for key in ("base_url", "access_token", "tenant_id", "user_id")):
        raise SmokeError("IAM host ready identity missing")
    try:
        url = urlsplit(record["base_url"])
        valid = url.scheme == "http" and url.hostname in {"127.0.0.1", "localhost"} and url.port is not None and not url.username and not url.password and url.path in {"", "/"} and not url.query and not url.fragment
    except ValueError:
        valid = False
    if not valid:
        raise SmokeError("IAM host ready origin invalid")
    return Ready(record["base_url"].rstrip("/"), record["access_token"], record["tenant_id"], record["user_id"])


def validate_result(record, command):
    if record != {"kind": "result", "command": command, "status": "ok"}:
        raise SmokeError("IAM host command protocol drift")


def node_environment(node: Path, expected: str, package_bin: Path) -> dict[str, str]:
    version = subprocess.run([str(node), "--version"], capture_output=True, text=True, timeout=5, check=True).stdout.strip()
    if version != expected:
        raise SmokeError(f"Node {expected} required")
    env = {name: os.environ[name] for name in ("HOME", "USER", "LOGNAME", "TMPDIR", "LANG", "LC_ALL", "COREPACK_HOME") if name in os.environ}
    env["PATH"] = os.pathsep.join((str(node.parent), str(package_bin), "/opt/homebrew/bin", "/usr/local/bin", "/usr/bin", "/bin"))
    return env


class ProtocolReader:
    """Read NDJSON with one absolute deadline and a retained, bounded buffer."""

    def __init__(self, fd: int):
        self.fd = fd
        self.buffer = bytearray()
        self.was_blocking = os.get_blocking(fd)
        os.set_blocking(fd, False)
        self.selector = selectors.DefaultSelector()
        self.selector.register(fd, selectors.EVENT_READ)

    def close(self) -> None:
        self.selector.close()
        os.set_blocking(self.fd, self.was_blocking)

    def record(self, timeout: float = 90) -> dict:
        deadline = time.monotonic() + timeout
        while True:
            newline = self.buffer.find(b"\n")
            if newline >= 0:
                if newline > MAX_LINE:
                    raise SmokeError("IAM host protocol oversized")
                line = bytes(self.buffer[:newline])
                del self.buffer[: newline + 1]
                try:
                    value = json.loads(line)
                except (UnicodeError, json.JSONDecodeError):
                    raise SmokeError("IAM host protocol malformed") from None
                if not isinstance(value, dict):
                    raise SmokeError("IAM host protocol object required")
                return value
            if len(self.buffer) > MAX_LINE:
                raise SmokeError("IAM host protocol oversized")
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not self.selector.select(remaining):
                raise SmokeError("IAM host protocol deadline exceeded")
            try:
                chunk = os.read(self.fd, 4096)
            except BlockingIOError:
                continue
            if not chunk:
                raise SmokeError("IAM host protocol closed")
            self.buffer.extend(chunk)


def host_command(process: subprocess.Popen[bytes], reader: ProtocolReader, command: str) -> None:
    if command not in {"signout", "remove_member", "reset", "stop"} or process.stdin is None:
        raise SmokeError("IAM host command invalid")
    process.stdin.write((json.dumps({"command": command}) + "\n").encode())
    process.stdin.flush()
    validate_result(reader.record(), command)


def request(base: str, path: str, *, method: str = "GET", headers: dict[str, str] | None = None, body: dict | None = None) -> tuple[int, dict]:
    req = Request(base + path, method=method, headers=headers or {}, data=None if body is None else json.dumps(body).encode())
    try:
        response = build_opener(ProxyHandler({}), runtime.NoRedirect()).open(req, timeout=8)
    except HTTPError as error:
        response = error
    except (URLError, TimeoutError, OSError):
        raise SmokeError("BFF HTTP request failed") from None
    with response:
        raw = response.read(1_048_577)
        status = response.status
    if len(raw) > 1_048_576:
        raise SmokeError("BFF HTTP response oversized")
    try:
        parsed = json.loads(raw)
    except (UnicodeError, json.JSONDecodeError):
        raise SmokeError("BFF HTTP response malformed") from None
    if not isinstance(parsed, dict):
        raise SmokeError("BFF HTTP response object required")
    return status, parsed


def require_status(actual: int, expected: int, case: str) -> None:
    if actual != expected:
        raise SmokeError(f"{case}: HTTP {actual}, expected {expected}")


def _valid_meta(body: dict) -> bool:
    meta = body.get("meta")
    return isinstance(meta, dict) and set(meta) == {"request_id"} and isinstance(meta["request_id"], str) and bool(meta["request_id"])


def require_success(status: int, body: dict, case: str) -> dict:
    require_status(status, 200, case)
    if set(body) != {"data", "meta"} or not isinstance(body["data"], dict) or not _valid_meta(body):
        raise SmokeError(f"{case}: success envelope drift")
    return body["data"]


def require_error(status: int, body: dict, expected_status: int, expected_code: str, case: str) -> None:
    require_status(status, expected_status, case)
    error = body.get("error")
    if set(body) != {"error", "meta"} or not isinstance(error, dict) or set(error) != {"code", "message"} or error["code"] != expected_code or not isinstance(error["message"], str) or not _valid_meta(body):
        raise SmokeError(f"{case}: error envelope or code drift")


def headers(ready: Ready, secret: str, *, bearer: bool = True, malicious: bool = False) -> dict[str, str]:
    values = {"x-kokoro-service": "web-bff", "x-kokoro-internal-secret": secret, "content-type": "application/json"}
    if bearer:
        values["authorization"] = "Bearer " + ready.access_token
    if malicious:
        values.update({"x-kokoro-namespace": "forged-tenant", "x-kokoro-principal-id": "forged-user"})
    return values


if __name__ == "__main__":
    raise SystemExit(
        "Historical IAM session smoke CLI retired. "
        "Use python3 scripts/e2e/run_web_native_session_smoke.py --help."
    )
