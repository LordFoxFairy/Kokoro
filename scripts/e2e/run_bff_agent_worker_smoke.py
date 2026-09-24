#!/usr/bin/env python3
"""Run a frozen BFF -> real Agent HTTP/CLI worker -> durable AG-UI smoke.

System model resolution and the OpenAI-compatible model endpoint are strict,
test-owned deterministic fixtures.  The Agent HTTP process, worker process,
PostgreSQL repositories, Redis stream consumer and BFF projector are the real
release code pinned below; this runner never describes its model fixture as a
real provider.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
from threading import Thread
import time
from types import MappingProxyType
from typing import Any, BinaryIO, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit
from urllib.request import ProxyHandler, Request, build_opener
from uuid import uuid4

if __package__:
    from .bff_iam_admission_stub import AdmissionIdentity, iam_admission_stub
    from .bff_owner_schema import bff_owner_database_url
    from . import scheduler_bff_smoke_runtime as runtime
else:
    from bff_iam_admission_stub import AdmissionIdentity, iam_admission_stub
    from bff_owner_schema import bff_owner_database_url
    import scheduler_bff_smoke_runtime as runtime


ROOT = Path(__file__).resolve().parents[2]
BFF = ROOT / "apps" / "kokoro-bff"
AGENT = ROOT / "apps" / "kokoro-agent"
EXPECTED_RELEASES = {
    "kokoro-bff": "84a560abeac5b7a63f32d7064abdde849ab33cf9",
    "kokoro-agent": "520ec181a101298b4f336aad273ce003b2735955",
}
MAX_HTTP_BYTES = 2 * 1024 * 1024
MAX_DIAGNOSTIC_CHARS = 4_000
_RUN_ID = re.compile(r"[a-f0-9]{24}\Z")
_REDIS_KEY_ID = re.compile(r"[A-Za-z0-9_.:-]+\Z")
_REDIS_OWNERSHIP_TTL_SECONDS = 7_200
_REDIS_CLAIM_SCRIPT = """
if redis.call('DBSIZE') ~= 0 then
  return 'NOT_EMPTY'
end
local result = redis.call('SET', KEYS[1], ARGV[1], 'NX', 'EX', ARGV[2])
if result then
  return 'OK'
end
return 'CLAIM_FAILED'
""".strip()
_REDIS_CLEANUP_SCRIPT = """
if redis.call('GET', KEYS[1]) ~= ARGV[1] then
  return 'OWNERSHIP_LOST'
end
local allowed = {}
for index = 1, #KEYS do
  allowed[KEYS[index]] = true
end
local present = redis.call('KEYS', '*')
for _, key in ipairs(present) do
  if not allowed[key] then
    return 'UNEXPECTED_KEY'
  end
end
if #present > 0 then
  redis.call('UNLINK', unpack(present))
end
return 'OK'
""".strip()


class SmokeError(RuntimeError):
    """Sanitized composition failure; messages must not contain credentials."""


class ProcessLike(Protocol):
    pid: int

    def poll(self) -> int | None: ...


Command = Callable[..., str]


def command_output(
    command: list[str],
    *,
    cwd: Path = ROOT,
    env: Mapping[str, str] | None = None,
    timeout: float = 30,
) -> str:
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            env=None if env is None else dict(env),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        raise SmokeError(f"{Path(command[0]).name} command could not run") from None
    if result.returncode != 0:
        raise SmokeError(
            f"{Path(command[0]).name} command failed (exit {result.returncode})"
        )
    return result.stdout


def run_owned_command(
    command: list[str],
    *,
    cwd: Path,
    env: Mapping[str, str],
    log: BinaryIO,
    timeout: float,
) -> int:
    try:
        return runtime.run_owned_command(
            command, cwd=cwd, env=dict(env), log=log, timeout=timeout
        )
    except runtime.SmokeError as error:
        raise SmokeError(str(error)) from None


def redis_database_number(raw_url: str) -> int:
    try:
        parsed = urlsplit(raw_url)
        if (
            parsed.scheme not in {"redis", "rediss"}
            or parsed.hostname is None
            or parsed.fragment
            or parsed.path in {"", "/"}
            or re.fullmatch(r"/[0-9]+", parsed.path) is None
        ):
            raise ValueError
        database = int(parsed.path[1:])
    except (TypeError, ValueError):
        raise SmokeError("Redis URL must select an explicit logical database") from None
    if not 0 <= database <= 15:
        raise SmokeError("Redis logical database must be between 0 and 15")
    return database


def _sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _database_url(admin_url: str, database: str) -> str:
    parsed = urlsplit(admin_url)
    query = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if key.lower() not in {"schema", "search_path", "options"}
    ]
    query.append(("options", "-csearch_path=public,pg_catalog -ctimezone=UTC"))
    return urlunsplit(
        (
            parsed.scheme,
            parsed.netloc,
            "/" + quote(database, safe=""),
            urlencode(query),
            "",
        )
    )


class OwnedResources:
    """Own one temporary PostgreSQL database and two initially empty Redis DBs."""

    def __init__(
        self,
        postgres_admin_url: str,
        bff_redis_url: str,
        agent_redis_url: str,
        run_id: str,
        *,
        command: Command = command_output,
    ) -> None:
        if urlsplit(postgres_admin_url).scheme not in {"postgres", "postgresql"}:
            raise SmokeError("Explicit PostgreSQL admin URL required")
        if _RUN_ID.fullmatch(run_id) is None:
            raise SmokeError("Invalid smoke run identity")
        bff_db = redis_database_number(bff_redis_url)
        agent_db = redis_database_number(agent_redis_url)
        if bff_db == agent_db:
            raise SmokeError("BFF and Agent Redis logical databases must be distinct")
        self.postgres_admin_url = postgres_admin_url
        self.bff_redis_url = bff_redis_url
        self.agent_redis_url = agent_redis_url
        self.run_id = run_id
        self.command = command
        self.created_database: str | None = None
        self.database_name = f"bff_agent_smoke_{run_id}"
        self.redis_claimed: set[int] = set()
        self.redis_claimed_ever: set[int] = set()
        self._redis_urls = {bff_db: bff_redis_url, agent_db: agent_redis_url}
        self._agent_db = agent_db
        self._markers = {
            database: f"kokoro:root:bff-agent-smoke:{run_id}:ownership"
            for database in self._redis_urls
        }
        self._owned_keys = {
            database: {self._markers[database]} for database in self._redis_urls
        }

    def _run(self, command: list[str]) -> str:
        try:
            return self.command(command).strip()
        except TypeError:
            return self.command(command, cwd=ROOT).strip()

    def _database_exists(self) -> bool:
        value = self._run(
            [
                "psql",
                self.postgres_admin_url,
                "-X",
                "-v",
                "ON_ERROR_STOP=1",
                "-Atc",
                "SELECT datname FROM pg_database WHERE datname = "
                + _sql_literal(self.database_name),
            ]
        )
        if value not in {"", self.database_name}:
            raise SmokeError("PostgreSQL inventory returned an unexpected identity")
        return value == self.database_name

    def create_database(self) -> str:
        if self.created_database is not None:
            raise SmokeError("Smoke database was already created")
        if self._database_exists():
            raise SmokeError("Smoke database already exists")
        try:
            self._run(
                [
                    "psql",
                    self.postgres_admin_url,
                    "-X",
                    "-v",
                    "ON_ERROR_STOP=1",
                    "-Atc",
                    f'CREATE DATABASE "{self.database_name}"',
                ]
            )
        except BaseException:
            # A client-side interruption can hide a committed CREATE. Reconcile
            # before propagating so finalization may still drop only this name.
            try:
                if self._database_exists():
                    self.created_database = self.database_name
            except Exception:
                pass
            raise
        self.created_database = self.database_name
        return _database_url(self.postgres_admin_url, self.database_name)

    def _redis(self, database: int, *arguments: str) -> str:
        return self._run(
            ["redis-cli", "-e", "-u", self._redis_urls[database], *arguments]
        )

    def _keys(self, database: int) -> list[str]:
        keys = self._redis(database, "--scan").splitlines()
        return [key for key in keys if key]

    def claim_redis(self) -> None:
        if self.redis_claimed:
            raise SmokeError("Redis ownership was already claimed")
        try:
            for database in self._redis_urls:
                result = self._redis(
                    database,
                    "EVAL",
                    _REDIS_CLAIM_SCRIPT,
                    "1",
                    self._markers[database],
                    self.run_id,
                    str(_REDIS_OWNERSHIP_TTL_SECONDS),
                )
                if result != "OK":
                    if result == "NOT_EMPTY":
                        raise SmokeError(
                            "Redis logical database must be empty before the smoke"
                        )
                    raise SmokeError("Redis logical database ownership claim failed")
                self.redis_claimed.add(database)
                self.redis_claimed_ever.add(database)
        except BaseException:
            self._cleanup_redis()
            raise

    def register_agent_keys(self, conversation_id: str, run_id: str) -> None:
        if self._agent_db not in self.redis_claimed:
            raise SmokeError(
                "Agent Redis database must be claimed before key registration"
            )
        if (
            _REDIS_KEY_ID.fullmatch(conversation_id) is None
            or _REDIS_KEY_ID.fullmatch(run_id) is None
        ):
            raise SmokeError("Invalid Agent Redis key identity")
        self._owned_keys[self._agent_db].update(
            {
                "kokoro:runs:requests",
                f"kokoro:run:{run_id}:events",
                f"kokoro:run:{run_id}:control",
                f"kokoro:session:{conversation_id}:live",
                f"kokoro:agent:lease:{run_id}",
            }
        )

    def _cleanup_redis(self) -> list[str]:
        failures: list[str] = []
        for database in tuple(self.redis_claimed):
            try:
                marker = self._markers[database]
                owned_keys = [
                    marker,
                    *sorted(self._owned_keys[database] - {marker}),
                ]
                result = self._redis(
                    database,
                    "EVAL",
                    _REDIS_CLEANUP_SCRIPT,
                    str(len(owned_keys)),
                    *owned_keys,
                    self.run_id,
                )
                if result == "OWNERSHIP_LOST":
                    failures.append("owned Redis identity changed")
                    continue
                if result == "UNEXPECTED_KEY":
                    failures.append(
                        "unexpected Redis key in exclusive logical database"
                    )
                    continue
                if result != "OK":
                    failures.append("owned Redis cleanup failed")
                    continue
                self.redis_claimed.discard(database)
            except (SmokeError, OSError, subprocess.SubprocessError):
                failures.append("owned Redis cleanup failed")
        return failures

    def cleanup(self) -> None:
        failures = self._cleanup_redis()
        if self.created_database is not None:
            try:
                self._run(
                    [
                        "psql",
                        self.postgres_admin_url,
                        "-X",
                        "-v",
                        "ON_ERROR_STOP=1",
                        "-Atc",
                        f'DROP DATABASE "{self.created_database}" WITH (FORCE)',
                    ]
                )
                self.created_database = None
            except (SmokeError, OSError, subprocess.SubprocessError):
                failures.append("owned PostgreSQL cleanup failed")
        if failures:
            raise SmokeError("; ".join(dict.fromkeys(failures)))

    def verify_clean(self) -> None:
        failures: list[str] = []
        if self.created_database is not None or self._database_exists():
            failures.append("owned PostgreSQL database remains")
        for database in self.redis_claimed_ever:
            keys = self._keys(database)
            if any(key in self._owned_keys[database] for key in keys):
                failures.append("owned Redis key remains")
            if any(key not in self._owned_keys[database] for key in keys):
                failures.append("unexpected Redis key remains")
        if failures:
            raise SmokeError("; ".join(dict.fromkeys(failures)))


@dataclass(frozen=True, slots=True)
class FixtureIdentity:
    tenant_id: str
    system_secret: str = field(repr=False)
    model_secret: str = field(repr=False)
    reply: str


@dataclass(slots=True)
class FixtureObservation:
    system_requests: int = 0
    model_requests: int = 0
    streaming_model_requests: int = 0
    real_provider: bool = False


@dataclass(frozen=True, slots=True)
class FixtureEndpoints:
    system_url: str
    model_url: str
    observation: FixtureObservation


class _OwnedHTTPServer(ThreadingHTTPServer):
    daemon_threads = False
    block_on_close = True
    allow_reuse_address = False

    def get_request(self) -> tuple[socket.socket, object]:
        connection, address = super().get_request()
        connection.settimeout(3)
        return connection, address


def _read_json(handler: BaseHTTPRequestHandler) -> dict[str, object] | None:
    if handler.headers.get("transfer-encoding") is not None:
        return None
    try:
        length = int(handler.headers.get("content-length", ""))
    except ValueError:
        return None
    if not 0 < length <= MAX_HTTP_BYTES:
        return None
    try:
        value = json.loads(handler.rfile.read(length))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _send_json(
    handler: BaseHTTPRequestHandler, status: int, value: Mapping[str, object]
) -> None:
    body = json.dumps(value, separators=(",", ":")).encode()
    handler.send_response(status)
    handler.send_header("content-type", "application/json")
    handler.send_header("cache-control", "no-store")
    handler.send_header("content-length", str(len(body)))
    handler.send_header("connection", "close")
    handler.end_headers()
    handler.wfile.write(body)
    handler.close_connection = True


def _fixture_error(handler: BaseHTTPRequestHandler, status: int, code: str) -> None:
    _send_json(
        handler,
        status,
        {
            "error": {
                "code": code,
                "message": "fixture rejected request",
                "retryable": False,
            }
        },
    )


def _system_handler(
    identity: FixtureIdentity, observation: FixtureObservation
) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, _format: str, *_args: object) -> None:
            return

        def do_POST(self) -> None:  # noqa: N802
            body = _read_json(self)
            if self.path != "/v1/system/model-catalog/resolve":
                _fixture_error(self, 404, "ROUTE_NOT_FOUND")
                return
            if (
                self.headers.get("authorization") != f"Bearer {identity.system_secret}"
                or self.headers.get("x-kokoro-service") != "kokoro-agent"
            ):
                _fixture_error(self, 401, "service_auth_failed")
                return
            if self.headers.get("x-kokoro-tenant-id") != identity.tenant_id:
                _fixture_error(self, 403, "FORBIDDEN")
                return
            if (
                body is None
                or set(body) - {"feature_key", "label_key"}
                or body.get("feature_key") != "chat"
            ):
                _fixture_error(self, 400, "INVALID_ARGUMENT")
                return
            label = body.get("label_key", "smoke")
            if not isinstance(label, str) or not label:
                _fixture_error(self, 400, "INVALID_ARGUMENT")
                return
            observation.system_requests += 1
            _send_json(
                self,
                200,
                {
                    "data": {
                        "model_id": "11111111-1111-4111-8111-111111111111",
                        "provider_id": "22222222-2222-4222-8222-222222222222",
                        "revision_id": "33333333-3333-4333-8333-333333333333",
                        "revision": 1,
                        "digest": "a" * 64,
                        "generation": "1",
                        "tenant_generation": "1",
                        "provider_model_name": "fixture-model",
                        "gateway_model_name": "smoke-model",
                        "feature_key": "chat",
                        "label_key": label,
                        "transport": "litellm",
                    }
                },
            )

    return Handler


def _model_handler(
    identity: FixtureIdentity, observation: FixtureObservation
) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, _format: str, *_args: object) -> None:
            return

        def do_POST(self) -> None:  # noqa: N802
            body = _read_json(self)
            if self.path != "/v1/chat/completions":
                _fixture_error(self, 404, "not_found")
                return
            if self.headers.get("authorization") != f"Bearer {identity.model_secret}":
                _fixture_error(self, 401, "unauthorized")
                return
            if (
                body is None
                or body.get("model") != "smoke-model"
                or not isinstance(body.get("messages"), list)
                or not body["messages"]
            ):
                _fixture_error(self, 400, "invalid_request")
                return
            observation.model_requests += 1
            if body.get("stream") is True:
                observation.streaming_model_requests += 1
                self._stream()
                return
            _send_json(
                self,
                200,
                {
                    "id": "chatcmpl-kokoro-fixture",
                    "object": "chat.completion",
                    "created": 1_700_000_000,
                    "model": "smoke-model",
                    "choices": [
                        {
                            "index": 0,
                            "message": {"role": "assistant", "content": identity.reply},
                            "finish_reason": "stop",
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 7,
                        "completion_tokens": 3,
                        "total_tokens": 10,
                    },
                },
            )

        def _stream(self) -> None:
            chunks = [
                {
                    "id": "chatcmpl-kokoro-fixture",
                    "object": "chat.completion.chunk",
                    "created": 1_700_000_000,
                    "model": "smoke-model",
                    "choices": [
                        {
                            "index": 0,
                            "delta": {"role": "assistant", "content": identity.reply},
                            "finish_reason": None,
                        }
                    ],
                },
                {
                    "id": "chatcmpl-kokoro-fixture",
                    "object": "chat.completion.chunk",
                    "created": 1_700_000_000,
                    "model": "smoke-model",
                    "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                },
                {
                    "id": "chatcmpl-kokoro-fixture",
                    "object": "chat.completion.chunk",
                    "created": 1_700_000_000,
                    "model": "smoke-model",
                    "choices": [],
                    "usage": {
                        "prompt_tokens": 7,
                        "completion_tokens": 3,
                        "total_tokens": 10,
                    },
                },
            ]
            payload = (
                b"".join(
                    b"data: "
                    + json.dumps(chunk, separators=(",", ":")).encode()
                    + b"\n\n"
                    for chunk in chunks
                )
                + b"data: [DONE]\n\n"
            )
            self.send_response(200)
            self.send_header("content-type", "text/event-stream")
            self.send_header("cache-control", "no-store")
            self.send_header("content-length", str(len(payload)))
            self.send_header("connection", "close")
            self.end_headers()
            self.wfile.write(payload)
            self.close_connection = True

    return Handler


@contextmanager
def system_model_fixtures(identity: FixtureIdentity) -> Iterator[FixtureEndpoints]:
    observation = FixtureObservation()
    system = _OwnedHTTPServer(("127.0.0.1", 0), _system_handler(identity, observation))
    model = _OwnedHTTPServer(("127.0.0.1", 0), _model_handler(identity, observation))
    servers = (system, model)
    threads = [
        Thread(target=server.serve_forever, name=f"bff-agent-fixture-{index}")
        for index, server in enumerate(servers)
    ]
    try:
        for thread in threads:
            thread.start()
        yield FixtureEndpoints(
            system_url=f"http://127.0.0.1:{system.server_port}",
            model_url=f"http://127.0.0.1:{model.server_port}",
            observation=observation,
        )
    finally:
        for server in servers:
            server.shutdown()
            server.server_close()
        for thread in threads:
            thread.join(timeout=5)
        if any(thread.is_alive() for thread in threads):
            raise SmokeError("Owned HTTP fixture thread did not stop")


def verify_release_inputs() -> dict[str, dict[str, object]]:
    result: dict[str, dict[str, object]] = {}
    for name, repo, gitlink in (
        ("kokoro-bff", BFF, "apps/kokoro-bff"),
        ("kokoro-agent", AGENT, "apps/kokoro-agent"),
    ):
        expected = EXPECTED_RELEASES[name]
        actual = command_output(["git", "-C", str(repo), "rev-parse", "HEAD"]).strip()
        clean = (
            command_output(
                [
                    "git",
                    "-C",
                    str(repo),
                    "status",
                    "--porcelain",
                    "--untracked-files=all",
                ]
            ).strip()
            == ""
        )
        tree = command_output(
            ["git", "-C", str(ROOT), "ls-tree", "HEAD", gitlink]
        ).split()
        published = len(tree) >= 3 and tree[2] == actual
        if actual != expected or not clean or not published:
            raise SmokeError(
                f"{name} source identity, cleanliness, or Root gitlink mismatch"
            )
        result[name] = {
            "sha": actual,
            "clean": clean,
            "root_gitlink_matches": published,
        }
    return result


def _base_environment(path_entries: list[Path]) -> dict[str, str]:
    environment = {
        key: os.environ[key]
        for key in (
            "HOME",
            "USER",
            "LOGNAME",
            "TMPDIR",
            "LANG",
            "LC_ALL",
            "COREPACK_HOME",
        )
        if key in os.environ
    }
    environment["PATH"] = os.pathsep.join(
        [
            *(str(entry) for entry in path_entries),
            "/opt/homebrew/bin",
            "/usr/local/bin",
            "/usr/bin",
            "/bin",
        ]
    )
    return environment


def _agent_environment(path_entries: list[Path]) -> dict[str, str]:
    environment = _base_environment(path_entries)
    # Agent entry points call load_dotenv(); keep ignored child-repository .env
    # files from changing this test-owned boundary or enabling external sinks.
    environment["PYTHON_DOTENV_DISABLED"] = "1"
    return environment


def _node_environment(node: Path) -> dict[str, str]:
    version = command_output([str(node), "--version"]).strip()
    if version != "v22.22.2":
        raise SmokeError("Node v22.22.2 is required for the frozen BFF release")
    corepack = node.parent / "corepack"
    if not corepack.is_file():
        raise SmokeError("Node 22 corepack is missing")
    return _base_environment([node.parent])


def _start_process(
    command: list[str], *, cwd: Path, env: Mapping[str, str], log: BinaryIO
) -> subprocess.Popen[bytes]:
    return subprocess.Popen(
        command,
        cwd=cwd,
        env=dict(env),
        stdin=subprocess.DEVNULL,
        stdout=log,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )


def _request(
    base: str,
    path: str,
    *,
    method: str = "GET",
    headers: Mapping[str, str] | None = None,
    body: Mapping[str, object] | None = None,
    timeout: float = 10,
) -> tuple[int, dict[str, object], Mapping[str, str]]:
    request = Request(
        base + path,
        method=method,
        headers={"accept": "application/json", **dict(headers or {})},
        data=None if body is None else json.dumps(body).encode(),
    )
    try:
        response = build_opener(ProxyHandler({})).open(request, timeout=timeout)
    except HTTPError as error:
        response = error
    except (URLError, TimeoutError, OSError):
        raise SmokeError("HTTP request did not complete") from None
    with response:
        raw = response.read(MAX_HTTP_BYTES + 1)
        status = response.status
        response_headers = MappingProxyType(
            {key.lower(): value for key, value in response.headers.items()}
        )
    if len(raw) > MAX_HTTP_BYTES:
        raise SmokeError("HTTP response exceeded smoke limit")
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise SmokeError("HTTP response was not valid JSON") from None
    if not isinstance(value, dict):
        raise SmokeError("HTTP response object required")
    return status, value, response_headers


def _wait_ready(
    base: str,
    process: ProcessLike,
    *,
    headers: Mapping[str, str] | None = None,
    path: str = "/readyz",
    timeout: float = 30,
) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise SmokeError("Owned process exited before readiness")
        try:
            status, body, _ = _request(base, path, headers=headers, timeout=2)
            if status == 200 and body.get("status") in {"ready", "ok"}:
                return
        except SmokeError:
            pass
        time.sleep(0.2)
    raise SmokeError("Owned process did not become ready before deadline")


def _bff_headers(
    token: str, shared_secret: str, key: str | None = None
) -> dict[str, str]:
    headers = {
        "authorization": f"Bearer {token}",
        "x-kokoro-service": "web-bff",
        "x-kokoro-internal-secret": shared_secret,
        "content-type": "application/json",
    }
    if key is not None:
        headers["idempotency-key"] = key
    return headers


def _agent_headers(secret: str, tenant: str, subject: str) -> dict[str, str]:
    return {
        "authorization": f"Bearer {secret}",
        "x-kokoro-tenant-ref": tenant,
        "x-kokoro-subject-kind": "user",
        "x-kokoro-subject-ref": subject,
        "x-kokoro-actor-kind": "user",
        "x-kokoro-actor-ref": subject,
        "x-kokoro-identity-assertion-ref": f"fixture-session:{subject}",
    }


def _data(
    status: int, body: Mapping[str, object], expected: int, case: str
) -> dict[str, object]:
    if (
        status != expected
        or set(body) != {"data", "meta"}
        or not isinstance(body.get("data"), dict)
    ):
        raise SmokeError(f"{case} success envelope drift")
    return body["data"]  # type: ignore[return-value]


def _error(
    status: int, body: Mapping[str, object], expected: int, code: str, case: str
) -> None:
    error = body.get("error")
    if status != expected or not isinstance(error, dict) or error.get("code") != code:
        raise SmokeError(f"{case} error envelope drift")


def _psql(resources: OwnedResources, database_url: str, query: str) -> str:
    return resources._run(
        ["psql", database_url, "-X", "-v", "ON_ERROR_STOP=1", "-Atc", query]
    )


def _first_turn_facts(
    resources: OwnedResources, database_url: str, conversation_id: str
) -> dict[str, object]:
    raw = _psql(
        resources,
        database_url,
        "SELECT json_build_object("
        "'conversation_count',(SELECT count(*) FROM kokoro_bff.bff_conversation WHERE conversation_id="
        + _sql_literal(conversation_id)
        + "),"
        "'message_count',(SELECT count(*) FROM kokoro_bff.bff_message WHERE conversation_id="
        + _sql_literal(conversation_id)
        + "),"
        "'assistant_status',(SELECT status FROM kokoro_bff.bff_message WHERE conversation_id="
        + _sql_literal(conversation_id)
        + " AND role='assistant'),"
        "'outbox_count',(SELECT count(*) FROM kokoro_bff.bff_agent_dispatch_outbox WHERE conversation_id="
        + _sql_literal(conversation_id)
        + "),"
        "'outbox_status',(SELECT status FROM kokoro_bff.bff_agent_dispatch_outbox WHERE conversation_id="
        + _sql_literal(conversation_id)
        + "),"
        "'expected_run',(SELECT expected_run_id FROM kokoro_bff.bff_agui_stream WHERE session_id="
        + _sql_literal(conversation_id)
        + ")"
        ")::text",
    )
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        raise SmokeError("BFF first-turn SQL evidence was invalid") from None
    return value if isinstance(value, dict) else {}


def _final_sql_evidence(
    resources: OwnedResources, database_url: str, conversation_id: str, run_id: str
) -> dict[str, object]:
    raw = _psql(
        resources,
        database_url,
        "SELECT json_build_object("
        "'bff_outbox_status',(SELECT status FROM kokoro_bff.bff_agent_dispatch_outbox WHERE run_id="
        + _sql_literal(run_id)
        + "),"
        "'bff_assistant_status',(SELECT status FROM kokoro_bff.bff_message WHERE conversation_id="
        + _sql_literal(conversation_id)
        + " AND role='assistant'),"
        "'bff_agui_frames',(SELECT count(*) FROM kokoro_bff.bff_agui_event WHERE session_id="
        + _sql_literal(conversation_id)
        + "),"
        "'bff_source_events',(SELECT count(*) FROM kokoro_bff.bff_agui_source_event WHERE session_id="
        + _sql_literal(conversation_id)
        + "),"
        "'agent_terminal',(SELECT terminal FROM kokoro_agent.kokoro_agent_run WHERE run_id="
        + _sql_literal(run_id)
        + "),"
        "'agent_dispatch_status',(SELECT status FROM kokoro_agent.kokoro_agent_run_dispatch WHERE run_id="
        + _sql_literal(run_id)
        + "),"
        "'agent_chat_events',(SELECT count(*) FROM kokoro_agent.kokoro_agent_chat_event WHERE run_id="
        + _sql_literal(run_id)
        + "),"
        "'agent_event_summary',(SELECT coalesce(json_agg(json_build_object('type',event_type,'payload',payload_json) ORDER BY source_index),'[]'::json) FROM kokoro_agent.kokoro_agent_chat_event WHERE run_id="
        + _sql_literal(run_id)
        + "),"
        "'agent_completed_assistants',(SELECT count(*) FROM kokoro_agent.kokoro_agent_chat_message WHERE run_id="
        + _sql_literal(run_id)
        + " AND role='assistant' AND status='completed')"
        ")::text",
    )
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        raise SmokeError("Final worker SQL evidence was invalid") from None
    return value if isinstance(value, dict) else {}


def _wait_snapshot(
    base: str,
    conversation_id: str,
    headers: Mapping[str, str],
    expected_reply: str,
    timeout: float,
) -> dict[str, object]:
    deadline = time.monotonic() + timeout
    last_status = 0
    while time.monotonic() < deadline:
        status, body, _ = _request(
            base, f"/v1/sessions/{conversation_id}", headers=headers
        )
        last_status = status
        if status == 200:
            data = _data(status, body, 200, "terminal snapshot")
            messages = data.get("messages")
            if isinstance(messages, list):
                assistants = [
                    message
                    for message in messages
                    if isinstance(message, dict) and message.get("role") == "assistant"
                ]
                if (
                    len(assistants) == 1
                    and assistants[0].get("status") == "completed"
                    and assistants[0].get("content") == expected_reply
                    and isinstance(data.get("event_watermark"), str)
                ):
                    return data
        time.sleep(0.25)
    raise SmokeError(
        f"terminal BFF snapshot did not converge (last status {last_status})"
    )


def _read_sse(
    base: str, path: str, headers: Mapping[str, str]
) -> list[dict[str, object]]:
    request = Request(base + path, headers=dict(headers))
    try:
        response = build_opener(ProxyHandler({})).open(request, timeout=15)
    except (HTTPError, URLError, TimeoutError, OSError):
        raise SmokeError("AG-UI replay request failed") from None
    with response:
        if response.status != 200 or not response.headers.get(
            "content-type", ""
        ).startswith("text/event-stream"):
            raise SmokeError("AG-UI replay response drift")
        raw = response.read(MAX_HTTP_BYTES + 1)
    if len(raw) > MAX_HTTP_BYTES:
        raise SmokeError("AG-UI replay exceeded smoke limit")
    frames: list[dict[str, object]] = []
    for block in raw.decode().split("\n\n"):
        values: dict[str, str] = {}
        for line in block.splitlines():
            name, separator, value = line.partition(":")
            if separator and name in {"id", "data"}:
                values[name] = value.lstrip()
        if "id" in values and "data" in values:
            try:
                event = json.loads(values["data"])
            except json.JSONDecodeError:
                raise SmokeError("AG-UI frame JSON was invalid") from None
            if not isinstance(event, dict):
                raise SmokeError("AG-UI event object required")
            frames.append({"id": values["id"], "event": event})
    if not frames or len({frame["id"] for frame in frames}) != len(frames):
        raise SmokeError("AG-UI replay cursor evidence was incomplete")
    return frames


def safe_log_excerpt(path: Path, secrets_to_redact: set[str]) -> str:
    try:
        text = path.read_text(errors="replace")
    except OSError:
        return "process log unavailable"
    for value in sorted(
        (item for item in secrets_to_redact if item), key=len, reverse=True
    ):
        text = text.replace(value, "[REDACTED]")
    if len(text) <= MAX_DIAGNOSTIC_CHARS:
        return text
    lines = text.splitlines()
    interesting: list[str] = []
    for index, line in enumerate(lines):
        if any(
            marker in line
            for marker in (
                "ERROR",
                "Traceback",
                "Exception",
                " failed",
                "Error:",
            )
        ):
            interesting.extend(lines[max(0, index - 1) : min(len(lines), index + 4)])
    middle = "\n".join(dict.fromkeys(interesting))[: MAX_DIAGNOSTIC_CHARS // 2]
    quarter = MAX_DIAGNOSTIC_CHARS // 4
    return (
        text[:quarter]
        + "\n... selected errors ...\n"
        + middle
        + "\n... log excerpt truncated ...\n"
        + text[-quarter:]
    )[:MAX_DIAGNOSTIC_CHARS]


def finalize_owned(
    processes: list[ProcessLike],
    resources: Any,
    *,
    stop: Callable[[ProcessLike], None] = runtime.stop_owned_process,
) -> None:
    failures: list[str] = []
    for process in reversed(processes):
        try:
            stop(process)
        except Exception:
            failures.append("owned process cleanup failed")
    for label, action in (
        ("owned resource cleanup failed", resources.cleanup),
        ("owned resource verification failed", resources.verify_clean),
    ):
        try:
            action()
        except Exception:
            failures.append(label)
    if failures:
        raise SmokeError("; ".join(dict.fromkeys(failures)))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--postgres-admin-url", required=True)
    parser.add_argument("--bff-redis-url", required=True)
    parser.add_argument("--agent-redis-url", required=True)
    parser.add_argument("--node22-bin", required=True)
    parser.add_argument("--uv-bin", default="uv")
    parser.add_argument("--timeout", type=float, default=120.0)
    args = parser.parse_args(argv)
    node = Path(args.node22_bin).expanduser().resolve()
    uv_value = (
        str(Path(args.uv_bin).expanduser().resolve())
        if os.path.sep in args.uv_bin
        else shutil.which(args.uv_bin)
    )
    uv = Path(uv_value) if uv_value is not None else Path("")
    if not node.is_file() or not os.access(node, os.X_OK):
        parser.error("node22-bin must be an executable Node binary")
    if not uv.is_file() or not os.access(uv, os.X_OK):
        parser.error("uv-bin must resolve to an executable")
    if args.timeout < 20 or args.timeout > 600:
        parser.error("timeout must be between 20 and 600 seconds")
    redis_database_number(args.bff_redis_url)
    redis_database_number(args.agent_redis_url)
    args.node22_bin = node
    args.uv_bin = uv
    return args


def run_smoke(args: argparse.Namespace) -> dict[str, object]:
    sources = verify_release_inputs()
    node_env = _node_environment(args.node22_bin)
    agent_env = _agent_environment([args.uv_bin.parent])
    run_id = secrets.token_hex(12)
    resources = OwnedResources(
        args.postgres_admin_url,
        args.bff_redis_url,
        args.agent_redis_url,
        run_id,
    )
    processes: list[subprocess.Popen[bytes]] = []
    stage = "preflight"
    owner_token = secrets.token_urlsafe(24)
    other_token = secrets.token_urlsafe(24)
    bff_secret = secrets.token_urlsafe(32)
    agent_secret = secrets.token_urlsafe(32)
    model_secret = secrets.token_urlsafe(32)
    credentials = {
        owner_token,
        other_token,
        bff_secret,
        agent_secret,
        model_secret,
        args.postgres_admin_url,
        args.bff_redis_url,
        args.agent_redis_url,
    }
    for connection_url in (
        args.postgres_admin_url,
        args.bff_redis_url,
        args.agent_redis_url,
    ):
        password = urlsplit(connection_url).password
        if password:
            credentials.add(password)
    tenant = f"tenant_{run_id}"
    owner = f"owner_{run_id}"
    other = f"other_{run_id}"
    reply = f"Durable worker reply {run_id}."
    database_url: str | None = None
    observation: FixtureObservation | None = None
    final_evidence: dict[str, object] = {}
    with tempfile.TemporaryDirectory(prefix="kokoro-bff-agent-worker-") as temporary:
        temporary_path = Path(temporary)
        log_path = temporary_path / "process.log"
        workspace = temporary_path / "workspace"
        workspace.mkdir()
        with log_path.open("w+b") as log:
            try:
                stage = "dependency preflight"
                command_output(
                    ["psql", args.postgres_admin_url, "-X", "-Atc", "SELECT 1"]
                )
                resources.claim_redis()
                database_url = resources.create_database()

                stage = "BFF exact-source build"
                if (
                    run_owned_command(
                        [str(args.node22_bin.parent / "corepack"), "pnpm", "build"],
                        cwd=BFF,
                        env=node_env,
                        log=log,
                        timeout=120,
                    )
                    != 0
                ):
                    raise SmokeError("BFF current-source build failed")

                bff_env = {
                    **node_env,
                    "KOKORO_BFF_POSTGRES_URL": bff_owner_database_url(database_url),
                    "KOKORO_BFF_REDIS_URL": args.bff_redis_url,
                }
                stage = "BFF schema install"
                if (
                    run_owned_command(
                        [
                            str(args.node22_bin.parent / "corepack"),
                            "pnpm",
                            "db:apply-schema",
                        ],
                        cwd=BFF,
                        env=bff_env,
                        log=log,
                        timeout=90,
                    )
                    != 0
                ):
                    raise SmokeError("BFF schema installation failed")

                common_agent_env = {
                    **agent_env,
                    "KOKORO_REDIS_URL": args.agent_redis_url,
                    "KOKORO_AGENT_DATABASE_URL": database_url,
                    "KOKORO_AGENT_DATABASE_SCHEMA": "kokoro_agent",
                    "KOKORO_INTERNAL_SECRET_AGENT": agent_secret,
                }
                stage = "Agent schema install"
                if (
                    run_owned_command(
                        [str(args.uv_bin), "run", "kokoro-agent-db-apply-schema"],
                        cwd=AGENT,
                        env=common_agent_env,
                        log=log,
                        timeout=90,
                    )
                    != 0
                ):
                    raise SmokeError("Agent schema installation failed")

                ports: set[int] = set()
                while len(ports) < 2:
                    with socket.socket() as listener:
                        listener.bind(("127.0.0.1", 0))
                        ports.add(int(listener.getsockname()[1]))
                bff_port, agent_port = tuple(ports)
                bff_base = f"http://127.0.0.1:{bff_port}"
                agent_base = f"http://127.0.0.1:{agent_port}"
                identities = {
                    owner_token: AdmissionIdentity(
                        tenant, owner, f"session_{owner}", "web"
                    ),
                    other_token: AdmissionIdentity(
                        tenant, other, f"session_{other}", "web"
                    ),
                }
                # Agent owns one workload credential for both its ingress and
                # authenticated calls to System; do not invent a second secret.
                fixture_identity = FixtureIdentity(
                    tenant, agent_secret, model_secret, reply
                )
                with (
                    iam_admission_stub(identities) as iam_base,
                    system_model_fixtures(fixture_identity) as fixtures,
                ):
                    observation = fixtures.observation
                    bff_runtime = {
                        **bff_env,
                        "KOKORO_BFF_HOST": "127.0.0.1",
                        "KOKORO_BFF_PORT": str(bff_port),
                        "KOKORO_BFF_MODE": "live",
                        "KOKORO_BFF_SHARED_SECRET": bff_secret,
                        "KOKORO_IAM_BASE_URL": iam_base,
                        "KOKORO_AGENT_ENABLED": "true",
                        "KOKORO_AGENT_BASE_URL": agent_base,
                        "KOKORO_INTERNAL_SECRET_BFF": agent_secret,
                        "KOKORO_TENANT_ID": tenant,
                        "KOKORO_DOMAIN": f"{run_id}.smoke.localhost",
                        "KOKORO_UPSTREAM_TIMEOUT_MS": "5000",
                    }
                    stage = "BFF startup before Agent"
                    bff_process = _start_process(
                        [str(args.node22_bin), str(BFF / "dist" / "main.js")],
                        cwd=BFF,
                        env=bff_runtime,
                        log=log,
                    )
                    processes.append(bff_process)
                    _wait_ready(bff_base, bff_process)

                    conversation_id = f"conv_{uuid4()}"
                    idempotency_key = f"worker-smoke:{run_id}"
                    owner_headers = _bff_headers(
                        owner_token, bff_secret, idempotency_key
                    )
                    stage = "durable first-message admission"
                    status, body, _ = _request(
                        bff_base,
                        f"/v1/sessions/{conversation_id}/messages",
                        method="POST",
                        headers=owner_headers,
                        body={"content": "Run the deterministic worker smoke."},
                    )
                    receipt = _data(status, body, 202, "first message")
                    run_id_value = receipt.get("run_id")
                    if not isinstance(run_id_value, str) or not run_id_value:
                        raise SmokeError("first message receipt run identity missing")
                    # Register the only production Redis keys this run may create
                    # before either Agent process starts. Cleanup rejects every
                    # other key, even when it matches an Agent naming pattern.
                    resources.register_agent_keys(conversation_id, run_id_value)
                    initial = _first_turn_facts(
                        resources, database_url, conversation_id
                    )
                    if (
                        initial.get("conversation_count") != 1
                        or initial.get("message_count") != 2
                        or initial.get("assistant_status") != "pending"
                        or initial.get("outbox_count") != 1
                        or initial.get("outbox_status") not in {"pending", "retryable"}
                        or initial.get("expected_run") != run_id_value
                    ):
                        raise SmokeError("BFF first-turn transaction evidence drift")

                    replay_status, replay_body, _ = _request(
                        bff_base,
                        f"/v1/sessions/{conversation_id}/messages",
                        method="POST",
                        headers=owner_headers,
                        body={"content": "Run the deterministic worker smoke."},
                    )
                    if (
                        _data(replay_status, replay_body, 202, "idempotent replay")
                        != receipt
                    ):
                        raise SmokeError("same-key replay changed the receipt")
                    changed_status, changed_body, _ = _request(
                        bff_base,
                        f"/v1/sessions/{conversation_id}/messages",
                        method="POST",
                        headers=owner_headers,
                        body={"content": "Changed content must conflict."},
                    )
                    _error(
                        changed_status,
                        changed_body,
                        409,
                        "idempotency_conflict",
                        "changed replay",
                    )
                    replay_facts = _first_turn_facts(
                        resources, database_url, conversation_id
                    )
                    for name, expected in (
                        ("conversation_count", 1),
                        ("message_count", 2),
                        ("assistant_status", "pending"),
                        ("outbox_count", 1),
                        ("expected_run", run_id_value),
                    ):
                        if replay_facts.get(name) != expected:
                            raise SmokeError(
                                "idempotency replay changed durable BFF facts"
                            )
                    other_status, other_body, _ = _request(
                        bff_base,
                        f"/v1/sessions/{conversation_id}",
                        headers=_bff_headers(other_token, bff_secret),
                    )
                    _error(
                        other_status,
                        other_body,
                        404,
                        "session_not_found",
                        "same-tenant other subject",
                    )
                    other_write_status, other_write_body, _ = _request(
                        bff_base,
                        f"/v1/sessions/{conversation_id}/messages",
                        method="POST",
                        headers=_bff_headers(
                            other_token, bff_secret, f"foreign:{run_id}"
                        ),
                        body={"content": "Must not cross the owner boundary."},
                    )
                    _error(
                        other_write_status,
                        other_write_body,
                        404,
                        "session_not_found",
                        "same-tenant other-subject write",
                    )

                    agent_http_env = {
                        **common_agent_env,
                        "KOKORO_AGENT_HTTP_HOST": "127.0.0.1",
                        "KOKORO_AGENT_HTTP_PORT": str(agent_port),
                    }
                    worker_env = {
                        **common_agent_env,
                        "KOKORO_SYSTEM_BASE_URL": fixtures.system_url,
                        "KOKORO_LITELLM_ENABLED": "1",
                        "KOKORO_LITELLM_BASE_URL": fixtures.model_url + "/v1",
                        "KOKORO_LITELLM_API_KEY": model_secret,
                        "KOKORO_DISABLE_STREAMING": "1",
                        "KOKORO_AGENT_LOCAL_SHELL_ROOT": str(workspace),
                        "KOKORO_MCP_EGRESS_MODE": "deny",
                    }
                    stage = "Agent HTTP startup"
                    agent_http = _start_process(
                        [str(args.uv_bin), "run", "kokoro-agent-http"],
                        cwd=AGENT,
                        env=agent_http_env,
                        log=log,
                    )
                    processes.append(agent_http)
                    # The launch was deliberately committed before Agent startup.
                    # Use the unauthenticated liveness probe only to sequence process
                    # startup; the following real launch replay, worker claim and PG
                    # projections are the dependency/readiness evidence for this run.
                    _wait_ready(
                        agent_base,
                        agent_http,
                        path="/healthz",
                    )
                    stage = "Agent CLI worker startup"
                    agent_worker = _start_process(
                        [str(args.uv_bin), "run", "kokoro-agent-worker"],
                        cwd=AGENT,
                        env=worker_env,
                        log=log,
                    )
                    processes.append(agent_worker)

                    stage = "worker execution and BFF projection"
                    try:
                        snapshot = _wait_snapshot(
                            bff_base,
                            conversation_id,
                            _bff_headers(owner_token, bff_secret),
                            reply,
                            args.timeout,
                        )
                    except SmokeError as error:
                        stalled = _final_sql_evidence(
                            resources, database_url, conversation_id, run_id_value
                        )
                        raise SmokeError(
                            f"{error}; stalled_sql={json.dumps(stalled, sort_keys=True)}; "
                            f"fixture_requests=system:{observation.system_requests},model:{observation.model_requests}"
                        ) from None
                    messages = snapshot.get("messages")
                    if not isinstance(messages, list) or len(messages) != 2:
                        raise SmokeError(
                            "reloaded BFF snapshot did not contain exactly one turn"
                        )
                    reload_status, reload_body, _ = _request(
                        bff_base,
                        f"/v1/sessions/{conversation_id}",
                        headers=_bff_headers(owner_token, bff_secret),
                    )
                    reloaded = _data(
                        reload_status, reload_body, 200, "reopened terminal snapshot"
                    )
                    if reloaded.get("messages") != messages or reloaded.get(
                        "event_watermark"
                    ) != snapshot.get("event_watermark"):
                        raise SmokeError(
                            "reopened BFF snapshot duplicated or lost durable facts"
                        )
                    frames = _read_sse(
                        bff_base,
                        f"/v1/sessions/{conversation_id}/events",
                        _bff_headers(owner_token, bff_secret),
                    )
                    frame_types = [
                        frame["event"].get("type")
                        for frame in frames
                        if isinstance(frame.get("event"), dict)
                    ]
                    if (
                        "RUN_STARTED" not in frame_types
                        or "RUN_FINISHED" not in frame_types
                        or snapshot.get("event_watermark") != frames[-1]["id"]
                    ):
                        raise SmokeError("durable AG-UI terminal replay evidence drift")

                    negative_status, negative_body, _ = _request(
                        agent_base,
                        f"/v1/sessions/{conversation_id}/events?after_seq=0&limit=200",
                        headers=_agent_headers(agent_secret, tenant, other),
                    )
                    negative_data = _data(
                        negative_status,
                        negative_body,
                        200,
                        "Agent other-subject replay",
                    )
                    if (
                        negative_data.get("events") != []
                        or negative_data.get("watermark") != 0
                    ):
                        raise SmokeError("Agent replay crossed the subject namespace")

                    final_evidence = _final_sql_evidence(
                        resources, database_url, conversation_id, run_id_value
                    )
                    if (
                        final_evidence.get("bff_outbox_status") != "succeeded"
                        or final_evidence.get("bff_assistant_status") != "completed"
                        or not isinstance(final_evidence.get("bff_agui_frames"), int)
                        or final_evidence["bff_agui_frames"] < 1
                        or final_evidence.get("agent_terminal") is not True
                        or final_evidence.get("agent_dispatch_status") != "claimed"
                        or not isinstance(final_evidence.get("agent_chat_events"), int)
                        or final_evidence["agent_chat_events"] < 1
                        or final_evidence.get("agent_completed_assistants") != 1
                    ):
                        raise SmokeError("real worker durable SQL evidence drift")
                    if (
                        observation.system_requests < 1
                        or observation.model_requests < 1
                    ):
                        raise SmokeError(
                            "real worker did not traverse both strict HTTP fixtures"
                        )
                    if observation.real_provider:
                        raise SmokeError(
                            "test fixture was incorrectly classified as a real provider"
                        )

                    log.flush()
                    diagnostic = log_path.read_text(errors="replace")
                    if any(secret in diagnostic for secret in credentials):
                        raise SmokeError("credential appeared in owned process log")
            except BaseException as error:
                log.flush()
                excerpt = safe_log_excerpt(log_path, credentials)
                if isinstance(error, (SmokeError, runtime.SmokeError)):
                    raise SmokeError(
                        f"{stage}: {error}\nowned log tail:\n{excerpt}"
                    ) from None
                raise
            finally:
                finalize_owned(processes, resources)

    if observation is None:
        raise SmokeError("fixture observation was unavailable")
    return {
        "status": "PASS",
        "sources": sources,
        "agent_worker": "real independent CLI process",
        "system_model_boundary": "strict deterministic fixtures; not a real provider",
        "system_requests": observation.system_requests,
        "model_requests": observation.model_requests,
        "sql_evidence": final_evidence,
        "owned_postgres_databases_remaining": 0,
        "owned_redis_keys_remaining": 0,
        "owned_processes_remaining": 0,
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = run_smoke(args)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        SmokeError,
        runtime.SmokeError,
        OSError,
        subprocess.SubprocessError,
    ) as error:
        print(f"smoke failed: {error}", file=sys.stderr)
        raise SystemExit(1)
