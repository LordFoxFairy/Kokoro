#!/usr/bin/env python3
"""Real IAM session-admission to BFF HTTP smoke; all data is run-owned."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import secrets
import selectors
import subprocess
import sys
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import ProxyHandler, Request, build_opener

if __package__:
    from . import capability_bff_smoke_runtime as runtime
    from .bff_owner_schema import bff_owner_database_url
else:
    import capability_bff_smoke_runtime as runtime
    from bff_owner_schema import bff_owner_database_url

ROOT = Path(__file__).resolve().parents[2]
IAM = ROOT / "apps" / "kokoro-iam"
BFF = ROOT / "apps" / "kokoro-bff"
IAM_HOST = IAM / "test" / "fixtures" / "bff-session-admission-host.ts"
MAX_LINE = 16_384


class SmokeError(RuntimeError):
    pass


@dataclass(frozen=True)
class Ready:
    base_url: str
    access_token: str
    tenant_id: str
    user_id: str


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("postgres-admin-url", "redis-url", "iam-node-bin", "bff-node-bin"):
        parser.add_argument("--" + name, required=True)
    for name in ("expected-bff-sha", "expected-iam-sha"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--allow-unpublished-iam-gitlink", action="store_true")
    args = parser.parse_args(argv)
    if urlsplit(args.postgres_admin_url).scheme != "postgresql" or urlsplit(args.redis_url).scheme not in {"redis", "rediss"}:
        parser.error("explicit PostgreSQL and Redis URLs required")
    for label in ("iam_node_bin", "bff_node_bin"):
        node = Path(getattr(args, label)).expanduser().resolve()
        if not node.is_file() or not os.access(node, os.X_OK):
            parser.error(f"{label} must be an executable Node binary")
        setattr(args, label, node)
    if any(re.fullmatch(r"[a-f0-9]{40}", getattr(args, name)) is None for name in ("expected_bff_sha", "expected_iam_sha")):
        parser.error("expected source SHA must be a full commit identity")
    return args


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


def cleanup_owned(processes, stop, cleanup):
    failures = []
    for process in reversed(processes):
        try:
            stop(process)
        except Exception:
            failures.append("owned process cleanup failed")
    try:
        cleanup()
    except Exception:
        failures.append("owned database cleanup failed")
    if failures:
        raise SmokeError("; ".join(failures))


def finalize_owned(processes, stop, cleanup, verify, inventory, before):
    failures = []
    for label, action in (("owned cleanup", lambda: cleanup_owned(processes, stop, cleanup)), ("owned verification", verify)):
        try:
            action()
        except Exception:
            failures.append(label + " failed")
    after = None
    if before is not None:
        try:
            after = inventory()
            if after != before:
                failures.append("IAM host resources changed after cleanup")
        except Exception:
            failures.append("IAM resource inventory failed")
    if failures:
        raise SmokeError("; ".join(failures))
    return after


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


def database_count(resources: runtime.OwnedResources, db_url: str, table: str) -> int:
    if table not in {"bff_project", "bff_idempotency_receipt"}:
        raise SmokeError("Database assertion table not allowed")
    value = resources.command(["psql", db_url, "-X", "-v", "ON_ERROR_STOP=1", "-Atc", f"SELECT count(*) FROM kokoro_bff.{table}"]).strip()
    if not re.fullmatch(r"[0-9]+", value):
        raise SmokeError("BFF fact count malformed")
    return int(value)


def snapshot(resources: runtime.OwnedResources, db_url: str) -> tuple[int, int]:
    return (database_count(resources, db_url, "bff_project"), database_count(resources, db_url, "bff_idempotency_receipt"))


def iam_resource_snapshot(resources: runtime.OwnedResources) -> tuple[set[str], set[str]]:
    databases = set(resources.command(["psql", resources.postgres_admin_url, "-X", "-v", "ON_ERROR_STOP=1", "-Atc", "SELECT datname FROM pg_database WHERE datname LIKE 'iam_hardening_%'"]).splitlines())
    keys = set(resources.command(["redis-cli", "-e", "-u", resources.redis_url, "--scan", "--pattern", "iam:test:bff-session-admission-host:*"]).splitlines())
    return databases, keys


def headers(ready: Ready, secret: str, *, bearer: bool = True, malicious: bool = False) -> dict[str, str]:
    values = {"x-kokoro-service": "web-bff", "x-kokoro-internal-secret": secret, "content-type": "application/json"}
    if bearer:
        values["authorization"] = "Bearer " + ready.access_token
    if malicious:
        values.update({"x-kokoro-namespace": "forged-tenant", "x-kokoro-principal-id": "forged-user"})
    return values


def main(argv=None) -> int:
    args = parse_args(argv)
    bff_source = verify_source(BFF, args.expected_bff_sha, "apps/kokoro-bff")
    iam_source = verify_source(IAM, args.expected_iam_sha, "apps/kokoro-iam", args.allow_unpublished_iam_gitlink)
    print(json.dumps({"bff_source": bff_source, "iam_source": iam_source}), flush=True)
    iam_env = node_environment(args.iam_node_bin, "v24.20.0", args.bff_node_bin.parent)
    bff_env = node_environment(args.bff_node_bin, "v22.22.2", args.bff_node_bin.parent)
    if not IAM_HOST.is_file():
        raise SmokeError("IAM host missing")
    run_id = secrets.token_hex(12)
    resources = runtime.OwnedResources(args.postgres_admin_url, args.redis_url, run_id)
    processes: list[subprocess.Popen[bytes]] = []
    cases = 0
    stage = "preflight"
    iam_before = None
    iam_after = None
    reader = None
    with tempfile.TemporaryDirectory(prefix="kokoro-bff-iam-") as temporary:
        log_path = Path(temporary) / "process.log"
        with log_path.open("w+b") as log:
            try:
                stage = "BFF current-source build"
                result = runtime.run_owned_command([str(args.bff_node_bin.parent / "corepack"), "pnpm", "build"], cwd=BFF, env=bff_env, log=log, timeout=90)
                if result != 0 or not (BFF / "dist" / "main.js").is_file():
                    raise SmokeError("BFF current-source build failed")
                stage = "preflight"
                resources.command(["psql", args.postgres_admin_url, "-X", "-v", "ON_ERROR_STOP=1", "-Atc", "SELECT 1"])
                if resources.command(["redis-cli", "-e", "-u", args.redis_url, "PING"]).strip() != "PONG":
                    raise SmokeError("Shared Redis unavailable")
                iam_before = iam_resource_snapshot(resources)
                stage = "BFF database create"
                db_url = resources.create_database("bff")
                bff_env.update({"KOKORO_BFF_POSTGRES_URL": bff_owner_database_url(db_url), "KOKORO_BFF_REDIS_URL": args.redis_url})
                stage = "BFF schema install"
                runtime.install_schema("bff", BFF, str(args.bff_node_bin.parent), bff_env, log)
                iam_env.update({"IAM_TEST_ADMIN_URL": args.postgres_admin_url, "IAM_TEST_REDIS_URL": args.redis_url, "NODE_ENV": "test"})
                host = subprocess.Popen([str(args.iam_node_bin), "--import", "tsx", str(IAM_HOST)], cwd=IAM, env=iam_env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=log, start_new_session=True, bufsize=0)
                processes.append(host)
                if host.stdout is None:
                    raise SmokeError("IAM host protocol pipe absent")
                reader = ProtocolReader(host.stdout.fileno())
                stage = "IAM host startup"
                ready = validate_ready(reader.record())
                secret = secrets.token_urlsafe(32)
                port = runtime.free_port()
                base = f"http://127.0.0.1:{port}"

                def start_bff(current: Ready) -> subprocess.Popen[bytes]:
                    env = {**bff_env, "KOKORO_BFF_HOST": "127.0.0.1", "KOKORO_BFF_PORT": str(port), "KOKORO_BFF_MODE": "live", "KOKORO_BFF_SHARED_SECRET": secret, "KOKORO_IAM_BASE_URL": current.base_url, "KOKORO_AGENT_ENABLED": "false", "KOKORO_TENANT_ID": current.tenant_id, "KOKORO_DOMAIN": f"{run_id}.smoke.localhost"}
                    process = runtime.start_process(args.bff_node_bin, BFF, env, log)
                    processes.append(process)
                    runtime.wait_ready(base, process)
                    return process

                stage = "BFF startup"
                bff = start_bff(ready)
                key = "iam-bff-" + run_id
                good = headers(ready, secret, malicious=True)
                good["idempotency-key"] = key
                stage = "create project"
                status, body = request(base, "/v1/projects", method="POST", headers=good, body={"name": "IAM owned project"})
                project = require_success(status, body, "real session project create").get("project", {})
                project_id = project.get("id")
                if not isinstance(project_id, str) or not project_id:
                    raise SmokeError("BFF project envelope drift")
                if database_count(resources, db_url, "bff_project") != 1:
                    raise SmokeError("Expected exactly one BFF project fact")
                stage = "owner SQL assertion"
                owner = resources.command(["psql", db_url, "-X", "-v", "ON_ERROR_STOP=1", "-Atc", "SELECT tenant_id || '|' || owner_id FROM kokoro_bff.bff_project LIMIT 1"]).strip()
                if owner != f"{ready.tenant_id}|{ready.user_id}":
                    raise SmokeError("Legacy identity headers changed BFF fact owner")
                cases += 1
                stage = "fact snapshot"
                before = snapshot(resources, db_url)
                status, body = request(base, "/v1/projects", method="POST", headers={**headers(ready, secret, bearer=False), "idempotency-key": "missing-" + run_id}, body={"name": "Denied"})
                require_error(status, body, 401, "session_authentication_required", "missing bearer")
                if snapshot(resources, db_url) != before:
                    raise SmokeError("Missing bearer mutated BFF facts")
                cases += 1
                host_command(host, reader, "signout")
                status, body = request(base, "/v1/projects", method="POST", headers=good, body={"name": "IAM owned project"})
                require_error(status, body, 401, "session_invalid", "signed out same-key replay")
                if snapshot(resources, db_url) != before:
                    raise SmokeError("Signed out replay mutated BFF facts")
                cases += 1
                host_command(host, reader, "reset")
                new_ready = validate_ready(reader.record())
                if new_ready.user_id == ready.user_id or new_ready.access_token == ready.access_token:
                    raise SmokeError("IAM reset did not issue a distinct identity")
                runtime.stop_owned_process(bff)
                processes.remove(bff)
                bff = start_bff(new_ready)
                status, body = request(base, "/v1/projects", headers=headers(new_ready, secret))
                if require_success(status, body, "new session list").get("projects") != []:
                    raise SmokeError("New IAM identity can see original resource")
                cases += 1
                host_command(host, reader, "remove_member")
                before = snapshot(resources, db_url)
                status, body = request(base, "/v1/projects", method="POST", headers={**headers(new_ready, secret), "idempotency-key": "removed-" + run_id}, body={"name": "Denied"})
                require_error(status, body, 403, "session_forbidden", "removed member")
                if snapshot(resources, db_url) != before:
                    raise SmokeError("Removed member mutated BFF facts")
                cases += 1
                host_command(host, reader, "stop")
                host.wait(timeout=15)
                status, body = request(base, "/v1/projects", headers=headers(new_ready, secret))
                require_error(status, body, 503, "iam_admission_unavailable", "IAM stopped")
                cases += 1
                log.flush()
                diagnostic = log_path.read_bytes()
                for value in (ready.access_token, new_ready.access_token, secret):
                    if value.encode() in diagnostic:
                        raise SmokeError("Credential appeared in process log")
                cases += 1
            except runtime.SmokeError as error:
                raise SmokeError(f"{stage}: {error}") from None
            finally:
                try:
                    iam_after = finalize_owned(processes, runtime.stop_owned_process, resources.cleanup, resources.verify_clean, lambda: iam_resource_snapshot(resources), iam_before)
                finally:
                    if reader is not None:
                        reader.close()
    print(json.dumps({"status": "passed", "cases": cases, "owned_bff_databases_remaining": 0, "owned_processes_remaining": 0, "iam_databases_before_after": [len(iam_before[0]), len(iam_after[0])], "iam_redis_keys_before_after": [len(iam_before[1]), len(iam_after[1])]}))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (SmokeError, runtime.SmokeError, subprocess.SubprocessError, OSError) as error:
        print(f"smoke failed: {error}", file=sys.stderr)
        sys.exit(1)
