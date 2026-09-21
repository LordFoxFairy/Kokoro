#!/usr/bin/env python3
"""Run the isolated real-process Capability-to-BFF acceptance smoke."""

from __future__ import annotations

import argparse
from collections.abc import Callable, Iterator
from contextlib import contextmanager, ExitStack
import getpass
import json
import os
from pathlib import Path
import re
import secrets
import signal
import socket
import subprocess
import sys
import tempfile
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from typing import BinaryIO, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[2]
BFF = ROOT / "apps" / "kokoro-bff"
CAPABILITY = ROOT / "apps" / "kokoro-capability"
BFF_RELEASE = "2ed792586e89c035155938078d9b07f33af95abd"
CAPABILITY_RELEASE = "7f89a267d745cbb9870f52d6edb23dec1a3c469b"
MAX_HTTP_BYTES = 1_048_576


class SmokeError(RuntimeError):
    """A controlled failure whose message contains no endpoint or credential."""


class ProcessLike(Protocol):
    pid: int

    def poll(self) -> int | None: ...


Command = Callable[..., str]


def process_group_exists(pgid: int) -> bool:
    try:
        result = subprocess.run(
            ["ps", "-axo", "pgid="],
            capture_output=True,
            text=True,
            timeout=3,
            check=True,
        )
    except (subprocess.SubprocessError, OSError):
        raise SmokeError("Owned process inventory failed") from None
    return str(pgid) in result.stdout.split()


def stop_owned_process(process: ProcessLike) -> None:
    """Drain with TERM and force with KILL while tracking the entire group."""

    for sig, seconds in ((signal.SIGTERM, 15.0), (signal.SIGKILL, 5.0)):
        process.poll()
        if not process_group_exists(process.pid):
            return
        try:
            os.killpg(process.pid, sig)
        except ProcessLookupError:
            process.poll()
            return
        except PermissionError:
            if not process_group_exists(process.pid):
                return
            raise SmokeError("Owned process group termination was denied") from None
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            process.poll()
            if not process_group_exists(process.pid):
                return
            time.sleep(0.05)
    raise SmokeError("Owned process group still exists after forced cleanup")


def run_owned_command(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    log: BinaryIO,
    timeout: float,
) -> int:
    process = subprocess.Popen(
        command,
        cwd=cwd,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=log,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    try:
        return process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        raise SmokeError("Owned command exceeded its deadline") from None
    finally:
        stop_owned_process(process)


def command_output(
    command: list[str],
    *,
    timeout: float = 30,
    cwd: Path = ROOT,
    env: dict[str, str] | None = None,
) -> str:
    process = subprocess.Popen(
        command,
        cwd=cwd,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=True,
    )
    try:
        output, _ = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        stop_owned_process(process)
        process.communicate()
        raise SmokeError("Owned command exceeded its deadline") from None
    finally:
        if process.poll() is None:
            stop_owned_process(process)
    if process.returncode != 0:
        raise SmokeError(
            f"{Path(command[0]).name} command failed (exit {process.returncode})"
        )
    return output


class OwnedResources:
    """Track only databases and Redis keys successfully owned by this run."""

    def __init__(
        self,
        postgres_admin_url: str,
        redis_url: str,
        run_id: str,
        *,
        command: Command = command_output,
    ) -> None:
        if re.fullmatch(r"[a-f0-9]{24}", run_id) is None:
            raise SmokeError("Invalid smoke run identity")
        if urlsplit(postgres_admin_url).scheme not in {"postgres", "postgresql"}:
            raise SmokeError("Explicit PostgreSQL and Redis endpoints required")
        if urlsplit(redis_url).scheme not in {"redis", "rediss"}:
            raise SmokeError("Explicit PostgreSQL and Redis endpoints required")
        self.postgres_admin_url = postgres_admin_url
        self.redis_url = redis_url
        self.run_id = run_id
        self.redis_prefix = f"kokoro:w0b:capability:{run_id}:"
        self.redis_claimed = False
        self.redis_was_claimed = False
        self.created_databases: list[str] = []
        self.database_names: list[str] = []
        self.command = command

    def _run(self, command: list[str]) -> str:
        return self.command(command)

    def create_database(self, owner: str) -> str:
        if owner not in {"capability", "bff"}:
            raise SmokeError("Invalid smoke database owner")
        name = f"w0b_cap_{self.run_id}_{owner}"
        if name in self.database_names:
            raise SmokeError("Database already requested by this run")
        self.database_names.append(name)
        try:
            self._run(
                [
                    "psql",
                    self.postgres_admin_url,
                    "-X",
                    "-v",
                    "ON_ERROR_STOP=1",
                    "-Atc",
                    f'CREATE DATABASE "{name}"',
                ]
            )
        except BaseException:
            self.database_names.remove(name)
            raise
        self.created_databases.append(name)
        parts = urlsplit(self.postgres_admin_url)
        netloc = parts.netloc
        if parts.username is None and parts.hostname is not None:
            host = parts.hostname
            if ":" in host:
                host = f"[{host}]"
            port = "" if parts.port is None else f":{parts.port}"
            netloc = f"{quote(getpass.getuser(), safe='')}@{host}{port}"
        return urlunsplit((parts.scheme, netloc, f"/{name}", parts.query, ""))

    def _redis_keys(self) -> list[str]:
        keys = self._run(
            [
                "redis-cli",
                "-e",
                "-u",
                self.redis_url,
                "--scan",
                "--pattern",
                f"{self.redis_prefix}*",
            ]
        ).splitlines()
        if any(not key.startswith(self.redis_prefix) for key in keys):
            raise SmokeError("Redis scan returned a key outside this run")
        return keys

    def claim_redis_prefix(self) -> None:
        result = self._run(
            [
                "redis-cli",
                "-e",
                "-u",
                self.redis_url,
                "SET",
                f"{self.redis_prefix}ownership",
                self.run_id,
                "NX",
                "EX",
                "600",
            ]
        ).strip()
        if result != "OK":
            raise SmokeError("Owned Redis prefix could not be claimed")
        self.redis_claimed = True
        self.redis_was_claimed = True

    def cleanup(self) -> None:
        failures: list[str] = []
        if self.redis_claimed:
            try:
                keys = self._redis_keys()
                for start in range(0, len(keys), 100):
                    self._run(
                        [
                            "redis-cli",
                            "-e",
                            "-u",
                            self.redis_url,
                            "UNLINK",
                            *keys[start : start + 100],
                        ]
                    )
                self.redis_claimed = False
            except (SmokeError, subprocess.SubprocessError, OSError):
                failures.append("owned Redis cleanup failed")

        for name in reversed(self.created_databases.copy()):
            try:
                self._run(
                    [
                        "psql",
                        self.postgres_admin_url,
                        "-X",
                        "-v",
                        "ON_ERROR_STOP=1",
                        "-Atc",
                        f'DROP DATABASE "{name}" WITH (FORCE)',
                    ]
                )
                self.created_databases.remove(name)
            except (SmokeError, subprocess.SubprocessError, OSError):
                failures.append("owned PostgreSQL cleanup failed")
        if failures:
            raise SmokeError("; ".join(failures))

    def verify_clean(self) -> None:
        if self.created_databases:
            raise SmokeError("Owned PostgreSQL cleanup was incomplete")
        if self.redis_was_claimed and self._redis_keys():
            raise SmokeError("Owned Redis cleanup was incomplete")
        for name in self.database_names:
            found = self._run(
                [
                    "psql",
                    self.postgres_admin_url,
                    "-X",
                    "-v",
                    "ON_ERROR_STOP=1",
                    "-Atc",
                    f"SELECT datname FROM pg_database WHERE datname = '{name}'",
                ]
            ).strip()
            if found:
                raise SmokeError("Owned PostgreSQL cleanup was incomplete")


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *_: object) -> None:
        return None


def http_json(
    base: str,
    path: str,
    *,
    headers: dict[str, str] | None = None,
    expected: int = 200,
) -> tuple[dict[str, object], dict[str, str]]:
    request = Request(base + path, method="GET", headers=headers or {})
    try:
        response = build_opener(ProxyHandler({}), NoRedirect()).open(request, timeout=8)
    except HTTPError as error:
        response = error
    except (URLError, TimeoutError, OSError):
        raise SmokeError("HTTP request did not complete") from None
    with response:
        status = response.status
        raw = response.read(MAX_HTTP_BYTES + 1)
        response_headers = {
            key.lower(): value for key, value in response.headers.items()
        }
    if status != expected:
        raise SmokeError(
            f"GET {path.split('?')[0]} returned {status}, expected {expected}"
        )
    if len(raw) > MAX_HTTP_BYTES:
        raise SmokeError("HTTP response exceeded smoke limit")
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise SmokeError("HTTP response was not valid JSON") from None
    if not isinstance(value, dict):
        raise SmokeError("HTTP object response required")
    return value, response_headers


def wait_ready(
    base: str,
    process: ProcessLike,
    *,
    timeout: float = 30,
    poll: float = 0.2,
) -> None:
    deadline = time.monotonic() + timeout
    malformed = False
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise SmokeError("Owned process exited before readiness")
        try:
            body, _headers = http_json(base, "/readyz")
            if body == {"status": "ready"} or body == {
                "status": "ok",
                "service": "kokoro-bff",
                "mode": "live",
            }:
                return
            malformed = True
        except SmokeError:
            pass
        time.sleep(poll)
    if malformed:
        raise SmokeError("Owned process returned malformed readiness")
    raise SmokeError("Owned process did not become ready in 30s")


def free_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def distinct_ports(count: int) -> list[int]:
    ports: set[int] = set()
    while len(ports) < count:
        ports.add(free_port())
    return list(ports)


def node_environment(
    directory: str, expected_version: str
) -> tuple[Path, dict[str, str]]:
    node_directory = Path(directory).expanduser().resolve()
    node = node_directory / "node"
    corepack = node_directory / "corepack"
    if not node.is_file() or not corepack.is_file():
        raise SmokeError(f"Node {expected_version} toolchain is missing")
    path = os.pathsep.join(
        [
            str(node_directory),
            "/usr/local/bin",
            "/usr/bin",
            "/bin",
            "/usr/sbin",
            "/sbin",
        ]
    )
    env = {"PATH": path}
    for name in ("HOME", "TMPDIR", "LANG", "LC_ALL", "COREPACK_HOME"):
        value = os.environ.get(name)
        if value:
            env[name] = value
    version = command_output([str(node), "--version"], env=env).strip()
    if version != expected_version:
        raise SmokeError(f"Node {expected_version} required for this owner")
    return node, env


class _DependencyHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/readyz":
            body = b'{"status":"ready"}'
            self.send_response(200)
            self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_response(404)
        self.end_headers()

    def log_message(self, *_: object) -> None:
        return


@contextmanager
def dependency_readiness_fixture() -> Iterator[str]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _DependencyHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        if thread.is_alive():
            raise SmokeError("Owned readiness fixture did not stop")


def owner_request_count(
    log_path: Path,
    request_id: str | None = None,
    operation: str | None = None,
) -> int:
    try:
        lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except FileNotFoundError:
        return 0
    total = 0
    for line in lines:
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict) or event.get("event") != "request.completed":
            continue
        event_operation = event.get("operation")
        if not isinstance(event_operation, str) or not event_operation.startswith(
            "GET /v1/"
        ):
            continue
        if request_id is not None and event.get("trace_id") != request_id:
            continue
        if operation is not None and event_operation != operation:
            continue
        total += 1
    return total


def wait_for_owner_request(log_path: Path, request_id: str, operation: str) -> None:
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        if owner_request_count(log_path, request_id, operation) == 1:
            return
        time.sleep(0.02)
    raise SmokeError("Capability owner request evidence was not observed")


def require(condition: bool, detail: str) -> None:
    if not condition:
        raise SmokeError(detail)


def error_code(body: dict[str, object]) -> str | None:
    error = body.get("error")
    return error.get("code") if isinstance(error, dict) else None


def assert_success_envelope(body: dict[str, object]) -> None:
    require(set(body) == {"data", "meta"}, "BFF success envelope drift")
    require(isinstance(body.get("data"), dict), "BFF success data drift")
    require(isinstance(body.get("meta"), dict), "BFF success metadata drift")


def bff_headers(
    web_token: str, tenant: str, subject: str, request_id: str
) -> dict[str, str]:
    return {
        "x-kokoro-service": "web-bff",
        "x-kokoro-internal-secret": web_token,
        "x-kokoro-namespace": tenant,
        "x-kokoro-principal-id": subject,
        "x-kokoro-request-id": request_id,
    }


def verify_good_bff_cases(
    bff_base: str,
    web_token: str,
    tenant: str,
    subject: str,
    run_id: str,
    capability_log: Path,
) -> list[str]:
    cases: list[str] = []
    query_marker = f"canonical-{run_id}"
    query_request_id = f"w0b-query-{run_id}"
    headers = bff_headers(web_token, tenant, subject, query_request_id)
    body, _ = http_json(
        bff_base,
        "/v1/skills?" + urlencode({"query": query_marker}),
        headers=headers,
    )
    assert_success_envelope(body)
    wait_for_owner_request(capability_log, query_request_id, "GET /v1/skills")
    cases.append("canonical_query_forwarded_to_owner")

    for name, path in (
        ("skill_pool", "/v1/skills/pool"),
        ("skill_catalog", "/v1/skills/catalog"),
        ("mcp_servers", "/v1/mcp/servers"),
    ):
        request_id = f"w0b-{name}-{run_id}"
        result, _ = http_json(
            bff_base,
            path,
            headers=bff_headers(web_token, tenant, subject, request_id),
        )
        assert_success_envelope(result)
        wait_for_owner_request(capability_log, request_id, f"GET {path}")
        cases.append(name)

    before = owner_request_count(capability_log)
    legacy, _ = http_json(
        bff_base,
        "/v1/skills?" + urlencode({"q": query_marker}),
        headers=bff_headers(web_token, tenant, subject, f"w0b-q-{run_id}"),
        expected=400,
    )
    require(error_code(legacy) == "invalid_query_parameter", "legacy q error drift")
    time.sleep(0.1)
    require(owner_request_count(capability_log) == before, "legacy q reached owner")
    cases.append("legacy_q_rejected_without_owner_io")

    missing_auth, _ = http_json(
        bff_base,
        "/v1/skills",
        headers={
            "x-kokoro-service": "web-bff",
            "x-kokoro-namespace": tenant,
            "x-kokoro-principal-id": subject,
        },
        expected=403,
    )
    require(error_code(missing_auth) == "service_auth_failed", "BFF auth error drift")
    cases.append("missing_bff_auth")

    invalid_cursor_id = f"w0b-invalid-cursor-{run_id}"
    invalid_cursor, _ = http_json(
        bff_base,
        "/v1/skills?" + urlencode({"cursor": "invalid"}),
        headers=bff_headers(web_token, tenant, subject, invalid_cursor_id),
        expected=400,
    )
    require(
        error_code(invalid_cursor) == "invalid_query_parameter",
        "invalid cursor error drift",
    )
    wait_for_owner_request(capability_log, invalid_cursor_id, "GET /v1/skills")
    cases.append("invalid_cursor")
    return cases


def verify_bad_owner_token_case(
    bff_base: str,
    web_token: str,
    tenant: str,
    subject: str,
    run_id: str,
    capability_log: Path,
) -> str:
    request_id = f"w0b-bad-owner-token-{run_id}"
    body, _ = http_json(
        bff_base,
        "/v1/skills",
        headers=bff_headers(web_token, tenant, subject, request_id),
        expected=503,
    )
    require(error_code(body) == "capability_unavailable", "owner auth mapping drift")
    wait_for_owner_request(capability_log, request_id, "GET /v1/skills")
    return "bad_owner_token_mapped"


def success_summary(cases: list[str]) -> dict[str, object]:
    if len(cases) != 8 or len(set(cases)) != 8:
        raise SmokeError("Smoke must complete exactly eight distinct cases")
    return {
        "status": "PASS",
        "cases": 8,
        "case_names": cases,
        "bff_auth_missing_status": 403,
        "processes": "exact dist/main.js",
        "cleanup": {
            "postgres_databases": "removed",
            "redis_prefix": "empty",
            "process_groups": "absent",
            "temporary_logs": "removed",
        },
        "releases": {
            "kokoro-bff": BFF_RELEASE,
            "kokoro-capability": CAPABILITY_RELEASE,
        },
    }


def failure_summary(error: BaseException, sensitive: list[str]) -> dict[str, str]:
    if isinstance(error, SmokeError):
        detail = str(error)
        if detail and not any(secret and secret in detail for secret in sensitive):
            return {"status": "FAIL", "error": detail}
    return {"status": "FAIL", "error": "smoke execution failed"}


def verify_release(repo: Path, expected: str) -> None:
    actual = command_output(["git", "-C", str(repo), "rev-parse", "HEAD"]).strip()
    if actual != expected:
        raise SmokeError(f"{repo.name} release does not match the frozen smoke input")
    if not (repo / "dist" / "main.js").is_file():
        raise SmokeError(f"{repo.name} exact production build is missing")


def install_schema(
    owner: str,
    repo: Path,
    node_directory: str,
    env: dict[str, str],
    log: BinaryIO,
) -> None:
    result = run_owned_command(
        [
            str(Path(node_directory).expanduser().resolve() / "corepack"),
            "pnpm",
            "db:apply-schema",
        ],
        cwd=repo,
        env=env,
        log=log,
        timeout=90,
    )
    require(result == 0, f"{owner} canonical schema installation failed")


def start_process(
    node: Path,
    repo: Path,
    env: dict[str, str],
    log: BinaryIO,
) -> subprocess.Popen[bytes]:
    return subprocess.Popen(
        [str(node), str(repo / "dist" / "main.js")],
        cwd=repo,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=log,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )


def run_smoke(
    args: argparse.Namespace,
    *,
    fault_injection: Callable[[str], None] | None = None,
) -> int:
    verify_release(BFF, BFF_RELEASE)
    verify_release(CAPABILITY, CAPABILITY_RELEASE)
    bff_node, bff_base_env = node_environment(args.bff_node_bin, "v22.22.2")
    capability_node, capability_base_env = node_environment(
        args.capability_node_bin, "v24.20.0"
    )
    run_id = secrets.token_hex(12)
    resources = OwnedResources(args.postgres_admin_url, args.redis_url, run_id)
    processes: list[subprocess.Popen[bytes]] = []
    cleanup_failures: list[str] = []
    cases: list[str] = []
    tenant = f"tenant-{run_id}"
    subject = f"subject-{run_id}"
    owner_token = secrets.token_hex(32)
    wrong_owner_token = secrets.token_hex(32)
    capability_rpc_token = secrets.token_hex(32)
    web_token = secrets.token_hex(32)
    capability_port, bff_port, bad_bff_port = distinct_ports(3)
    capability_base = f"http://127.0.0.1:{capability_port}"
    bff_base = f"http://127.0.0.1:{bff_port}"
    bad_bff_base = f"http://127.0.0.1:{bad_bff_port}"
    with (
        tempfile.TemporaryDirectory(prefix="kokoro-w0b-capability-") as temporary,
        ExitStack() as files,
        dependency_readiness_fixture() as dependency_base,
    ):
        capability_log_path = Path(temporary) / "kokoro-capability.log"
        capability_log = files.enter_context(capability_log_path.open("wb"))
        bff_log = files.enter_context((Path(temporary) / "kokoro-bff.log").open("wb"))
        bad_bff_log = files.enter_context(
            (Path(temporary) / "kokoro-bff-bad-owner-token.log").open("wb")
        )
        try:
            resources.command(
                [
                    "psql",
                    resources.postgres_admin_url,
                    "-X",
                    "-v",
                    "ON_ERROR_STOP=1",
                    "-Atc",
                    "SELECT 1",
                ]
            )
            require(
                resources.command(
                    ["redis-cli", "-e", "-u", resources.redis_url, "PING"]
                ).strip()
                == "PONG",
                "Shared Redis unavailable",
            )
            resources.claim_redis_prefix()
            capability_database_url = resources.create_database("capability")
            bff_database_url = resources.create_database("bff")
            capability_env = {
                **capability_base_env,
                "KOKORO_POSTGRES_URL": capability_database_url,
                "KOKORO_REDIS_URL": args.redis_url,
                "KOKORO_CAPABILITY_PORT": str(capability_port),
                "KOKORO_CAPABILITY_SERVICE_TOKEN": capability_rpc_token,
                "KOKORO_CAPABILITY_BFF_SERVICE_TOKEN": owner_token,
                "KOKORO_CAPABILITY_SURFACES": "skill-catalog,skill-source,mcp-server",
                "KOKORO_STORAGE_URL": dependency_base,
                "KOKORO_IAM_ATTESTATION_VERIFIER_URL": (
                    dependency_base + "/iam/attestation/verify"
                ),
                "KOKORO_MCP_CONNECTOR_PROVIDER_CATALOG_JSON": "[]",
                "KOKORO_CAPABILITY_READINESS_TIMEOUT_MS": "5000",
                "KOKORO_STORAGE_READINESS_TIMEOUT_MS": "5000",
                "PGOPTIONS": "-c search_path=public,pg_catalog -c timezone=UTC",
            }
            common_bff_env = {
                **bff_base_env,
                "KOKORO_BFF_POSTGRES_URL": bff_database_url,
                "KOKORO_BFF_REDIS_URL": args.redis_url,
                "KOKORO_BFF_HOST": "127.0.0.1",
                "KOKORO_BFF_MODE": "live",
                "KOKORO_BFF_SHARED_SECRET": web_token,
                "KOKORO_CAPABILITY_BASE_URL": capability_base,
                "KOKORO_AGENT_ENABLED": "false",
                "KOKORO_TENANT_ID": tenant,
                "KOKORO_DOMAIN": f"{run_id}.smoke.localhost",
                "PGOPTIONS": "-c search_path=public,pg_catalog -c timezone=UTC",
            }
            good_bff_env = {
                **common_bff_env,
                "KOKORO_BFF_PORT": str(bff_port),
                "KOKORO_INTERNAL_SECRET_BFF": owner_token,
            }
            bad_bff_env = {
                **common_bff_env,
                "KOKORO_BFF_PORT": str(bad_bff_port),
                "KOKORO_INTERNAL_SECRET_BFF": wrong_owner_token,
            }
            install_schema(
                "kokoro-capability",
                CAPABILITY,
                args.capability_node_bin,
                capability_env,
                capability_log,
            )
            install_schema(
                "kokoro-bff",
                BFF,
                args.bff_node_bin,
                good_bff_env,
                bff_log,
            )

            capability_process = start_process(
                capability_node, CAPABILITY, capability_env, capability_log
            )
            processes.append(capability_process)
            wait_ready(capability_base, capability_process)

            bff_process = start_process(bff_node, BFF, good_bff_env, bff_log)
            processes.append(bff_process)
            wait_ready(bff_base, bff_process)
            if fault_injection is not None:
                fault_injection("after-processes-started")
            cases.extend(
                verify_good_bff_cases(
                    bff_base,
                    web_token,
                    tenant,
                    subject,
                    run_id,
                    capability_log_path,
                )
            )
            stop_owned_process(bff_process)
            processes.remove(bff_process)

            bad_bff_process = start_process(bff_node, BFF, bad_bff_env, bad_bff_log)
            processes.append(bad_bff_process)
            wait_ready(bad_bff_base, bad_bff_process)
            cases.append(
                verify_bad_owner_token_case(
                    bad_bff_base,
                    web_token,
                    tenant,
                    subject,
                    run_id,
                    capability_log_path,
                )
            )
        finally:
            for process in reversed(processes):
                try:
                    stop_owned_process(process)
                except (SmokeError, OSError):
                    cleanup_failures.append("owned process shutdown failed")
            try:
                resources.cleanup()
            except SmokeError:
                cleanup_failures.append("owned infrastructure cleanup failed")
            if not cleanup_failures:
                try:
                    resources.verify_clean()
                except SmokeError:
                    cleanup_failures.append("owned resource residue detected")
            if cleanup_failures:
                raise SmokeError("; ".join(cleanup_failures))

    print(json.dumps(success_summary(cases), ensure_ascii=False, indent=2))
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--postgres-admin-url", required=True)
    result.add_argument("--redis-url", required=True)
    result.add_argument("--bff-node-bin", required=True)
    result.add_argument("--capability-node-bin", required=True)
    return result


def main() -> int:
    args = parser().parse_args()
    sensitive = [args.postgres_admin_url, args.redis_url]
    try:
        return run_smoke(args)
    except Exception as error:
        print(
            json.dumps(failure_summary(error, sensitive), ensure_ascii=False),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
