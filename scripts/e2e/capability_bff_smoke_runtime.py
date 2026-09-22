"""Owned process, infrastructure, and readiness lifecycle for Capability smoke."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
import errno
import getpass
import json
import os
from pathlib import Path
import re
import signal
import socket
import subprocess
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Lock, Thread
from typing import BinaryIO, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[2]
MAX_HTTP_BYTES = 1_048_576


class SmokeError(RuntimeError):
    """Controlled failure whose message is safe to summarize."""


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
    for sig, seconds in ((signal.SIGTERM, 15.0), (signal.SIGKILL, 5.0)):
        process.poll()
        if not process_group_exists(process.pid):
            return
        try:
            os.killpg(process.pid, sig)
        except ProcessLookupError:
            return
        except PermissionError:
            if process_group_exists(process.pid):
                raise SmokeError("Owned process group termination was denied") from None
            return
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            process.poll()
            if not process_group_exists(process.pid):
                return
            time.sleep(0.05)
    raise SmokeError("Owned process group still exists after forced cleanup")


def run_owned_command(
    command: list[str], *, cwd: Path, env: dict[str, str], log: BinaryIO, timeout: float
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
    """Track only databases and the Redis prefix owned by this run."""

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
        self.redis_reconciliation = False
        self.redis_preexisting = False
        self.created_databases: list[str] = []
        self.database_names: list[str] = []
        self.database_reconciliation: set[str] = set()
        self.preexisting_databases: set[str] = set()
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
        if self._database_exists(name):
            self.preexisting_databases.add(name)
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
                    f'CREATE DATABASE "{name}"',
                ]
            )
        except BaseException:
            try:
                if self._database_exists(name):
                    self.created_databases.append(name)
            except (SmokeError, subprocess.SubprocessError, OSError):
                self.database_reconciliation.add(name)
            raise
        self.created_databases.append(name)
        return self._database_url(name)

    def _database_exists(self, name: str) -> bool:
        found = self._run(
            [
                "psql",
                self.postgres_admin_url,
                "-X",
                "-v",
                "ON_ERROR_STOP=1",
                "-Atc",
                "SELECT datname FROM pg_database WHERE datname = " + _sql_literal(name),
            ]
        ).strip()
        if found not in {"", name}:
            raise SmokeError("PostgreSQL inventory returned an unexpected identity")
        return found == name

    def _database_url(self, name: str) -> str:
        parts = urlsplit(self.postgres_admin_url)
        netloc = parts.netloc
        if parts.username is None and parts.hostname is not None:
            host = parts.hostname
            if ":" in host:
                host = f"[{host}]"
            port = "" if parts.port is None else f":{parts.port}"
            netloc = f"{quote(getpass.getuser(), safe='')}@{host}{port}"
        query = [
            (name, value)
            for name, value in parse_qsl(parts.query, keep_blank_values=True)
            if name.lower() != "options"
        ]
        return urlunsplit((parts.scheme, netloc, f"/{name}", urlencode(query), ""))

    def _redis_owner(self) -> str:
        return self._run(
            [
                "redis-cli",
                "-e",
                "-u",
                self.redis_url,
                "GET",
                self.redis_prefix + "ownership",
            ]
        ).strip()

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
        if self._redis_keys():
            self.redis_preexisting = True
            raise SmokeError("Owned Redis prefix already exists")
        if self._redis_owner():
            self.redis_preexisting = True
            raise SmokeError("Owned Redis prefix already exists")
        try:
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
        except BaseException:
            try:
                owner = self._redis_owner()
                if owner == self.run_id:
                    self.redis_claimed = self.redis_was_claimed = True
                elif owner:
                    self.redis_preexisting = True
            except (SmokeError, subprocess.SubprocessError, OSError):
                self.redis_reconciliation = True
            raise
        if result != "OK":
            if self._redis_owner():
                self.redis_preexisting = True
                raise SmokeError("Owned Redis prefix already exists")
            raise SmokeError("Owned Redis prefix could not be claimed")
        self.redis_claimed = True
        self.redis_was_claimed = True

    def cleanup(self) -> None:
        failures: list[str] = []
        for name in self.database_reconciliation.copy():
            try:
                if self._database_exists(name):
                    self.created_databases.append(name)
                self.database_reconciliation.remove(name)
            except (SmokeError, subprocess.SubprocessError, OSError):
                failures.append("owned PostgreSQL reconciliation failed")
        if self.redis_reconciliation:
            try:
                owner = self._redis_owner()
                if owner == self.run_id:
                    self.redis_claimed = self.redis_was_claimed = True
                elif owner:
                    self.redis_preexisting = True
                self.redis_reconciliation = False
            except (SmokeError, subprocess.SubprocessError, OSError):
                failures.append("owned Redis reconciliation failed")
        if self.redis_claimed:
            try:
                owner = self._redis_owner()
                if owner == self.run_id:
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
                elif not owner:
                    self.redis_claimed = False
                else:
                    failures.append("owned Redis ownership changed")
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
        if self.database_reconciliation:
            raise SmokeError("Owned PostgreSQL reconciliation was incomplete")
        if self.redis_reconciliation:
            raise SmokeError("Owned Redis reconciliation was incomplete")
        if self.created_databases:
            raise SmokeError("Owned PostgreSQL cleanup was incomplete")
        if self.redis_was_claimed and self._redis_keys():
            raise SmokeError("Owned Redis cleanup was incomplete")
        for name in self.database_names:
            if name not in self.preexisting_databases and self._database_exists(name):
                raise SmokeError("Owned PostgreSQL cleanup was incomplete")


def _sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


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


def _close_socket(owned_socket: socket.socket) -> None:
    try:
        owned_socket.shutdown(socket.SHUT_RDWR)
    except OSError:
        pass
    try:
        owned_socket.close()
    except OSError:
        pass


class OwnedHTTPServer(ThreadingHTTPServer):
    """Track accepted sockets so handler threads can be drained on context exit."""

    daemon_threads = False
    block_on_close = True

    def __init__(self, address: tuple[str, int], handler: type[BaseHTTPRequestHandler]):
        super().__init__(address, handler)
        self._connections: set[socket.socket] = set()
        self._connections_lock = Lock()
        self._tearing_down = False

    def get_request(self) -> tuple[socket.socket, object]:
        connection, address = super().get_request()
        connection.settimeout(2)
        with self._connections_lock:
            self._connections.add(connection)
        return connection, address

    def shutdown_request(self, request: socket.socket) -> None:
        try:
            super().shutdown_request(request)
        finally:
            with self._connections_lock:
                self._connections.discard(request)

    def close_owned_connections(self) -> None:
        with self._connections_lock:
            self._tearing_down = True
            connections = tuple(self._connections)
        for connection in connections:
            _close_socket(connection)

    def handle_error(self, request: object, client_address: object) -> None:
        error = sys.exception()
        with self._connections_lock:
            tearing_down = self._tearing_down
        expected_errnos = {
            errno.EBADF,
            errno.ECONNABORTED,
            errno.ECONNRESET,
            errno.ENOTCONN,
            errno.EPIPE,
        }
        if (
            tearing_down
            and isinstance(error, OSError)
            and error.errno in expected_errnos
        ):
            return
        super().handle_error(request, client_address)


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
    server = OwnedHTTPServer(("127.0.0.1", 0), _DependencyHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.close_owned_connections()
        server.server_close()
        thread.join(timeout=5)
        if thread.is_alive():
            raise SmokeError("Owned readiness fixture did not stop")


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
    if result != 0:
        raise SmokeError(f"{owner} canonical schema installation failed")


def start_process(
    node: Path, repo: Path, env: dict[str, str], log: BinaryIO
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
