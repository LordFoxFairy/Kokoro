#!/usr/bin/env python3
"""Exercise the real Web native-session path through BFF and IAM."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import select
import shutil
import signal
import socket
import socketserver
import subprocess
import sys
import tempfile
import time
from threading import BoundedSemaphore, Event, Lock, Thread
from urllib.parse import quote, quote_plus, unquote, urlsplit
from uuid import uuid4

import capability_bff_smoke_runtime as runtime
from bff_owner_schema import bff_owner_database_url
import run_bff_iam_session_smoke as session
import run_web_bff_iam_oidc_smoke as web

ROOT = Path(__file__).resolve().parents[2]
IAM = ROOT / "apps/kokoro-iam"
BFF = ROOT / "apps/kokoro-bff"
APP = ROOT / "apps/kokoro-app"
ADMIN = ROOT / "apps/kokoro-admin"
IAM_HOST = IAM / "test/fixtures/bff-session-admission-host.ts"
EVIDENCE_ROOT = ROOT / "var/dev/web-native-session-smoke"
REQUIRED_NODE_VERSIONS = {"iam": "24.20.0", "bff": "24.20.0", "app": "22.23.4"}
ADMIN_NODE_VERSION = "22.23.4"


class SmokeError(RuntimeError):
    pass


@dataclass(frozen=True)
class NativeReceipt:
    cookie: str
    bff_user_context_credential_file: str
    account_session_credential_file: str
    iam_web_origin: str


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in (
        "postgres-admin-url",
        "redis-url",
        "iam-node-bin",
        "bff-node-bin",
        "web-node-bin",
    ):
        parser.add_argument("--" + name, required=True)
    for name in ("expected-iam-sha", "expected-bff-sha", "expected-app-sha"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--expected-admin-sha")
    parser.add_argument("--allow-unpublished-iam-gitlink", action="store_true")
    parser.add_argument("--browser-journeys", action="store_true")
    args = parser.parse_args(argv)
    if args.browser_journeys and args.allow_unpublished_iam_gitlink:
        parser.error(
            "browser journeys require all source commits to match Root gitlinks"
        )
    if urlsplit(args.postgres_admin_url).scheme != "postgresql" or urlsplit(
        args.redis_url
    ).scheme not in {"redis", "rediss"}:
        parser.error("explicit PostgreSQL and Redis URLs required")
    for name in ("iam_node_bin", "bff_node_bin", "web_node_bin"):
        node = Path(getattr(args, name)).expanduser().resolve()
        if not node.is_file() or not os.access(node, os.X_OK):
            parser.error(f"{name} must be executable")
        setattr(args, name, node)
    for name in ("expected_iam_sha", "expected_bff_sha", "expected_app_sha"):
        if not re.fullmatch(r"[a-f0-9]{40}", getattr(args, name)):
            parser.error("expected source SHA must be full commit")
    if (args.browser_journeys or args.expected_admin_sha is not None) and (
        not isinstance(args.expected_admin_sha, str)
        or not re.fullmatch(r"[a-f0-9]{40}", args.expected_admin_sha)
    ):
        parser.error("browser journeys require an exact expected Admin SHA")
    return args


class _AdminConnectHandler(socketserver.BaseRequestHandler):
    def reject(self, status: int) -> None:
        self.request.sendall(
            f"HTTP/1.1 {status} Rejected\r\nContent-Length: 0\r\nConnection: close\r\n\r\n".encode()
        )

    def handle(self) -> None:
        server = self.server
        upstream = None
        try:
            deadline = time.monotonic() + server.HEADER_SECONDS
            data = b""
            while b"\r\n\r\n" not in data:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    self.reject(408)
                    return
                self.request.settimeout(remaining)
                try:
                    part = self.request.recv(
                        min(1024, server.HEADER_BYTES + 1 - len(data))
                    )
                except TimeoutError:
                    self.reject(408)
                    return
                if not part:
                    return
                data += part
                if len(data) > server.HEADER_BYTES:
                    self.reject(431)
                    return
            head, _, pending = data.partition(b"\r\n\r\n")
            lines = head.decode("ascii", "strict").split("\r\n")
            if lines[0] != f"CONNECT {server.authority} HTTP/1.1":
                self.reject(403)
                return
            headers: dict[str, list[str]] = {}
            for line in lines[1:]:
                name, separator, value = line.partition(":")
                if (
                    not separator
                    or not re.fullmatch(r"[!#$%&'*+.^_`|~0-9A-Za-z-]+", name)
                    or any(ord(char) < 32 or ord(char) > 126 for char in value)
                ):
                    self.reject(403)
                    return
                headers.setdefault(name.lower(), []).append(value.strip())
            if (
                # Node's native CONNECT omits the default HTTPS port in Host.
                headers.get("host") not in ([server.authority], [server.hostname])
                or "transfer-encoding" in headers
                or "expect" in headers
                or headers.get("content-length", ["0"]) != ["0"]
                or server.stopping.is_set()
                or time.monotonic() >= deadline
            ):
                self.reject(403)
                return
            upstream = socket.create_connection(
                ("127.0.0.1", server.upstream_port), timeout=server.CONNECT_SECONDS
            )
            with server.upstream_lock:
                if server.stopping.is_set():
                    return
                server.upstreams.add(upstream)
            self.request.settimeout(server.IDLE_SECONDS)
            upstream.settimeout(server.IDLE_SECONDS)
            deadline = time.monotonic() + server.TOTAL_SECONDS
            self.request.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
            if pending:
                upstream.settimeout(
                    min(server.IDLE_SECONDS, max(0.001, deadline - time.monotonic()))
                )
                upstream.sendall(pending)
            idle = time.monotonic() + server.IDLE_SECONDS
            while not server.stopping.is_set():
                remaining = min(deadline, idle) - time.monotonic()
                if remaining <= 0:
                    return
                readable, _, _ = select.select(
                    [self.request, upstream], [], [], min(remaining, 0.1)
                )
                for source in readable:
                    part = source.recv(65_536)
                    if not part:
                        return
                    remaining = min(deadline, idle) - time.monotonic()
                    if remaining <= 0:
                        return
                    target = upstream if source is self.request else self.request
                    target.settimeout(remaining)
                    target.sendall(part)
                    idle = time.monotonic() + server.IDLE_SECONDS
        except (OSError, UnicodeError, ValueError):
            # Neither CONNECT headers nor exception payloads are diagnostics.
            return
        finally:
            if upstream is not None:
                with server.upstream_lock:
                    server.upstreams.discard(upstream)
                try:
                    upstream.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                upstream.close()


class AdminConnectProxy(runtime.OwnedHTTPServer):
    """Private Node transport: one authority, one owned TLS target, no general proxy."""

    HEADER_BYTES = 8192
    HEADER_SECONDS = 2
    CONNECT_SECONDS = 2
    IDLE_SECONDS = 10
    TOTAL_SECONDS = 30
    MAX_CONNECTIONS = 8

    def __init__(self, origin: str, upstream_port: int):
        parsed = urlsplit(origin)
        if (
            parsed.scheme != "https"
            or parsed.netloc != parsed.hostname
            or not re.fullmatch(r"[a-z0-9][a-z0-9.-]{0,252}", parsed.hostname or "")
            or parsed.path
            or parsed.query
            or parsed.fragment
            or type(upstream_port) is not int
            or not 1 <= upstream_port <= 65_535
        ):
            raise SmokeError("Admin CONNECT configuration invalid")
        self.hostname = parsed.hostname
        self.authority = self.hostname + ":443"
        self.upstream_port = upstream_port
        self.upstreams: set[socket.socket] = set()
        self.upstream_lock = Lock()
        self.stopping = Event()
        self.slots = BoundedSemaphore(self.MAX_CONNECTIONS)
        super().__init__(("127.0.0.1", 0), _AdminConnectHandler)
        self.thread = Thread(
            target=self.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True
        )
        try:
            self.thread.start()
        except BaseException:
            self.server_close()
            raise

    def process_request(self, request, address):
        if not self.slots.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, address)
        except BaseException:
            self.slots.release()
            raise

    def process_request_thread(self, request, address):
        try:
            super().process_request_thread(request, address)
        finally:
            self.slots.release()

    def handle_error(self, *_):
        # Transport failures are closed without reflecting private request bytes.
        return

    def close(self):
        self.stopping.set()
        self.shutdown()
        self.close_owned_connections()
        with self.upstream_lock:
            connections = tuple(self.upstreams)
        for connection in connections:
            try:
                connection.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            connection.close()
        self.server_close()
        self.thread.join(timeout=5)
        with self.upstream_lock, self._connections_lock:
            if self.thread.is_alive() or self.upstreams or self._connections:
                raise SmokeError("Admin CONNECT cleanup failed")


def admin_runtime_preflight(node: Path, env: dict) -> dict:
    """Inspect the existing isolated installation; never install or relink it."""
    try:
        modules = json.loads((ADMIN / "node_modules/.modules.yaml").read_text())
        next_package = json.loads(
            (ADMIN / "node_modules/next/package.json").read_text()
        )
        if (
            modules.get("packageManager") != "pnpm@12.3.4"
            or next_package.get("version") != "16.2.6"
        ):
            raise SmokeError("Admin installed toolchain mismatch")
        result = subprocess.run(
            [
                str(node),
                "-e",
                "process.stdout.write(JSON.stringify({env_proxy:process.allowedNodeEnvironmentFlags.has('--use-env-proxy')}))",
            ],
            env=env,
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )
        if not exact_browser_fact(json.loads(result.stdout), {"env_proxy": True}):
            raise SmokeError("Admin Node env proxy unsupported")
    except (OSError, ValueError, TypeError, subprocess.SubprocessError):
        raise SmokeError("Admin runtime preflight failed") from None
    return {"pnpm": "12.3.4", "next": "16.2.6", "env_proxy": True}


def isolated_admin_next(directory: Path) -> Path:
    """Copy only Admin inputs; its installed dependencies and owner output stay untouched."""
    root = directory / "admin-next"
    root.mkdir(mode=0o700)
    for source in ("app", "components", "lib", "patches", "public"):
        if (ADMIN / source).is_dir():
            shutil.copytree(ADMIN / source, root / source)
    for source in (
        "package.json",
        "tsconfig.json",
        "next-env.d.ts",
        "next.config.ts",
        "postcss.config.mjs",
        "pnpm-lock.yaml",
        "pnpm-workspace.yaml",
        "proxy.ts",
    ):
        shutil.copy2(ADMIN / source, root / source)
    config = root / "next.config.ts"
    original = config.read_text()
    marker = "const nextConfig: NextConfig = {"
    if original.count(marker) != 1:
        raise SmokeError("Admin isolated Next configuration drift")
    config.write_text(
        original.replace(
            marker,
            marker + "\n  turbopack: { root: " + json.dumps(str(ROOT.parent)) + " },",
        )
    )
    (root / "server.cjs").write_text(
        'const http = require("node:http")\nconst next = require("next")\n'
        "const [port, host] = process.argv.slice(2)\n"
        "const app = next({ dev: false, dir: __dirname, hostname: host, port: 443 })\n"
        'app.prepare().then(() => http.createServer(app.getRequestHandler()).listen(Number(port), "127.0.0.1"))'
        ".catch(() => { process.exitCode = 1 })\n"
    )
    (root / "node_modules").symlink_to(ADMIN / "node_modules", target_is_directory=True)
    return root


def wait_admin_ready(proxy_port: int, origin: str, process) -> None:
    deadline = time.monotonic() + 30
    while True:
        try:
            response = web.https_browser(proxy_port, "/manage/api/v1/me", origin)
            if response.status == 401 and exact_browser_fact(
                json.loads(response.body), {"authenticated": False}
            ):
                return
        except (SmokeError, web.SmokeError, OSError, ValueError):
            pass
        if process.poll() is not None or time.monotonic() >= deadline:
            raise SmokeError("Admin HTTPS entry not ready")
        time.sleep(0.1)


def verify_source(
    repo: Path, expected: str, gitlink: str, allow_unpublished: bool = False
) -> dict[str, object]:
    actual = runtime.command_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD"]
    ).strip()
    clean = (
        runtime.command_output(
            ["git", "-C", str(repo), "status", "--porcelain", "--untracked-files=all"]
        ).strip()
        == ""
    )
    tree = (
        runtime.command_output(["git", "-C", str(ROOT), "ls-tree", "HEAD", gitlink])
        .strip()
        .split()
    )
    published = len(tree) >= 3 and tree[2] == actual
    if actual != expected or not clean or (not published and not allow_unpublished):
        raise SmokeError(
            f"{repo.name} source identity, cleanliness, or Root gitlink mismatch"
        )
    return {"sha": actual, "clean": clean, "root_gitlink_matches": published}


def purpose_credential_paths(user_context, account_sessions, *, run_dir: Path):
    if any(
        not isinstance(value, str) or not value
        for value in (user_context, account_sessions)
    ):
        raise SmokeError("IAM credential file missing")
    try:
        paths = (Path(user_context).resolve(), Path(account_sessions).resolve())
        missing = not all(path.is_file() for path in paths)
        escaped = not all(path.is_relative_to(run_dir.resolve()) for path in paths)
        same_file = not missing and paths[0].samefile(paths[1])
    except (OSError, RuntimeError, ValueError):
        raise SmokeError("IAM credential file invalid") from None
    if missing:
        raise SmokeError("IAM credential file missing")
    if escaped:
        raise SmokeError("IAM credential escaped run directory")
    if same_file:
        raise SmokeError("IAM purpose credential files must be distinct")
    return paths


def native_command(
    process: subprocess.Popen[bytes], reader: session.ProtocolReader, *, run_dir: Path
) -> NativeReceipt:
    if process.stdin is None:
        raise SmokeError("IAM host stdin unavailable")
    process.stdin.write(b'{"command":"native"}\n')
    process.stdin.flush()
    record = reader.record()
    if (
        not isinstance(record, dict)
        or set(record)
        != {
            "kind",
            "cookie",
            "bff_user_context_credential_file",
            "account_session_credential_file",
            "web_origin",
        }
        or record.get("kind") != "native"
    ):
        raise SmokeError("native receipt protocol drift")
    cookie = record.get("cookie")
    user_context_file = record["bff_user_context_credential_file"]
    account_session_file = record["account_session_credential_file"]
    web_origin = record.get("web_origin")
    if not isinstance(web_origin, str) or urlsplit(web_origin).scheme not in {
        "http",
        "https",
    }:
        raise SmokeError("IAM Web origin invalid")
    cookie_name = (
        "__Secure-kokoro-issuer.session_token"
        if urlsplit(web_origin).scheme == "https"
        else "kokoro-issuer.session_token"
    )
    if not isinstance(cookie, str):
        raise SmokeError("native cookie missing")
    cookie_names = [pair.partition("=")[0].strip() for pair in cookie.split(";")]
    session_cookie_names = [
        name
        for name in cookie_names
        if name
        in {"kokoro-issuer.session_token", "__Secure-kokoro-issuer.session_token"}
    ]
    if session_cookie_names != [cookie_name] or not re.search(
        rf"(?:^|; ){re.escape(cookie_name)}=[^;]+", cookie
    ):
        raise SmokeError("native cookie missing")
    purpose_credential_paths(user_context_file, account_session_file, run_dir=run_dir)
    return NativeReceipt(cookie, user_context_file, account_session_file, web_origin)


BROWSER_JOURNEYS = {
    "shared_admin": {
        "initial_owner": {"enabled": False, "version": 0, "succeeded_audits": 0},
        "granted_owner": {"enabled": True, "version": 1, "succeeded_audits": 1},
        "shared_issuer_cookie": True,
        "additional_sign_in_requests": 0,
        "admin_me_status": 200,
        "admin_identity_matches": True,
        "admin_shell_visible": True,
        "revoked_owner": {"enabled": False, "version": 2, "succeeded_audits": 2},
        "revoked_admin_me_status": 403,
        "revoked_admin_error_code": "admin_access_denied",
        "private_ui_retired": True,
        "product_session_status": 200,
        "product_authenticated": True,
        "projects_status": 200,
        "product_owner": {
            "exists": True,
            "unexpired": True,
            "member": True,
            "active_tenant": "fixed",
        },
    },
    "cold_login": {
        "initial_issuer_cookies": 0,
        "sign_in_status": 303,
        "session_status": 200,
        "authenticated": True,
        "projects_status": 200,
        "profile_status": 200,
        "profile_visible": True,
        "owner": {
            "exists": True,
            "unexpired": True,
            "member": True,
            "active_tenant": "fixed",
        },
    },
    "tenant_rejection_recovery": {
        "foreign_owner": {
            "exists": True,
            "unexpired": True,
            "member": True,
            "active_tenant": "other",
        },
        "pre_mutation_profile_visible": True,
        "session_status": 403,
        "session_error_code": "product_tenant_forbidden",
        "projects_status": 403,
        "projects_error_code": "product_tenant_forbidden",
        "private_ui_retired": True,
        "relogin_status": 303,
        "recovered_session_status": 200,
        "recovered_authenticated": True,
        "recovered_projects_status": 200,
        "recovered_profile_status": 200,
        "recovered_profile_visible": True,
        "recovered_owner": {
            "exists": True,
            "unexpired": True,
            "member": True,
            "active_tenant": "fixed",
        },
    },
    "ui_logout": {
        "clicked": True,
        "sign_out_status": 200,
        "owner": {
            "exists": True,
            "unexpired": False,
            "member": True,
            "active_tenant": "fixed",
        },
        "issuer_cookies": 0,
        "session_status": 200,
        "authenticated": False,
        "projects_status": 401,
        "projects_error_code": "session_authentication_required",
        "old_cookie_projects_status": 401,
        "old_cookie_projects_error_code": "session_invalid",
    },
    "independent_revocation": {
        "a_owner": {
            "exists": False,
            "unexpired": False,
            "member": True,
            "active_tenant": "none",
        },
        "a_session_status": 200,
        "a_authenticated": False,
        "a_projects_status": 401,
        "a_projects_error_code": "session_authentication_required",
        "a_private_ui_retired": True,
        "b_session_status_before_membership": 200,
        "b_authenticated_before_membership": True,
        "b_owner_before_membership": {
            "exists": True,
            "unexpired": True,
            "member": True,
            "active_tenant": "fixed",
        },
        "b_owner_after_membership": {
            "exists": True,
            "unexpired": True,
            "member": False,
            "active_tenant": "fixed",
        },
        "b_session_status": 403,
        "b_session_error_code": "session_forbidden",
        "b_projects_status": 403,
        "b_projects_error_code": "session_forbidden",
        "private_ui_retired": True,
    },
}


def exact_browser_fact(value, expected) -> bool:
    """Reject unknown fields and Python bool/int equivalence at the boundary."""
    if type(value) is not type(expected):
        return False
    if isinstance(expected, dict):
        return value.keys() == expected.keys() and all(
            exact_browser_fact(value[key], expected[key]) for key in expected
        )
    return value == expected


def validate_browser_receipt(record: dict) -> dict:
    if not isinstance(record, dict) or set(record) != {"kind", "journeys", "race"}:
        raise SmokeError("browser receipt shape invalid")
    if record["kind"] != "browser_result" or not exact_browser_fact(
        record["journeys"], BROWSER_JOURNEYS
    ):
        raise SmokeError("browser journey facts incomplete or failed")
    race = record["race"]
    if not isinstance(race, dict) or race.get("observation") not in (
        "cancelled",
        "delivered_and_retired",
    ):
        raise SmokeError("browser race observation missing")
    if not exact_browser_fact(
        race,
        {
            "upstream_profile_status": 200,
            "observation": race["observation"],
            "private_ui_retired": True,
            "cross_tab_focus": True,
        },
    ):
        raise SmokeError("browser race facts incomplete or failed")
    return record


def private_json_write(stream, record: dict, timeout: float) -> None:
    """Bounded nonblocking private-pipe write, never a log or command argument."""
    payload = (json.dumps(record, separators=(",", ":")) + "\n").encode()
    if len(payload) > 16_384 or timeout <= 0 or stream is None:
        raise SmokeError("private protocol write invalid")
    fd = stream.fileno()
    was_blocking = os.get_blocking(fd)
    deadline = time.monotonic() + timeout
    try:
        os.set_blocking(fd, False)
        while payload:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not select.select([], [fd], [], remaining)[1]:
                raise SmokeError("private protocol write deadline exceeded")
            try:
                count = os.write(fd, payload)
            except BlockingIOError:
                continue
            if count <= 0:
                raise SmokeError("private protocol write closed")
            payload = payload[count:]
    except (OSError, ValueError):
        raise SmokeError("private protocol write failed") from None
    finally:
        os.set_blocking(fd, was_blocking)


class BrowserBroker:
    """Fixed IAM fixture operations; no arbitrary owner command relay."""

    def __init__(self, process, reader, *, credentials, run_dir: Path, timeout=10):
        self.process = process
        self.reader = reader
        self.credentials = credentials
        self.run_dir = run_dir
        self.timeout = timeout

    def dispatch(self, request: dict, *, timeout=None) -> dict:
        if not isinstance(request, dict):
            raise SmokeError("browser command invalid")
        command = request.get("command")
        fields = {
            "browser_fixture": {"command"},
            "bind_browser_session": {"command", "slot", "cookie"},
            "activate_browser_tenant": {"command", "slot", "tenant"},
            "inspect_browser_session": {"command", "slot"},
            "revoke_browser_session": {"command", "slot"},
            "revoke_browser_membership": {"command"},
            "grant_browser_platform_admin": {"command"},
            "revoke_browser_platform_admin": {"command"},
            "inspect_browser_platform_admin": {"command"},
        }
        if (
            not isinstance(command, str)
            or command not in fields
            or set(request) != fields[command]
        ):
            raise SmokeError("browser command invalid")
        if "slot" in request and request["slot"] not in ("primary", "secondary"):
            raise SmokeError("browser slot invalid")
        if command == "activate_browser_tenant" and request["tenant"] not in (
            "fixed",
            "other",
        ):
            raise SmokeError("browser tenant invalid")
        if command == "bind_browser_session":
            cookie = request["cookie"]
            if not isinstance(cookie, str) or not re.fullmatch(
                r"(?:__Secure-)?kokoro-issuer\.session_token=[^;\s\x00-\x1f\x7f]{1,4096}",
                cookie,
            ):
                raise SmokeError("browser cookie invalid")
            self.credentials.add(cookie, cookie.partition("=")[2])
        budget = min(self.timeout, self.timeout if timeout is None else timeout)
        deadline = time.monotonic() + budget
        private_json_write(self.process.stdin, request, budget)
        try:
            record = self.reader.record(timeout=max(0, deadline - time.monotonic()))
        except Exception:
            raise SmokeError("browser owner protocol failed") from None
        if not isinstance(record, dict):
            raise SmokeError("browser owner response invalid")
        if command in {
            "grant_browser_platform_admin",
            "revoke_browser_platform_admin",
            "inspect_browser_platform_admin",
        }:
            if (
                set(record)
                != {"kind", "command", "enabled", "version", "succeeded_audits"}
                or record.get("kind") != "browser_platform_admin"
                or record.get("command") != command
                or type(record.get("enabled")) is not bool
                or any(
                    type(record.get(key)) is not int
                    or not 0 <= record[key] <= 2_147_483_647
                    for key in ("version", "succeeded_audits")
                )
            ):
                raise SmokeError("browser administrator observation invalid")
            return record
        if command == "browser_fixture":
            fields = {
                "kind",
                "email",
                "password",
                "tenant_id",
                "bff_user_context_credential_file",
                "account_session_credential_file",
                "web_origin",
            }
            if set(record) != fields or record.get("kind") != "browser_fixture":
                raise SmokeError("browser fixture response invalid")
            if any(
                not isinstance(record[key], str)
                or not record[key]
                or len(record[key]) > 4096
                for key in fields - {"kind"}
            ):
                raise SmokeError("browser fixture value invalid")
            purpose_credential_paths(
                record["bff_user_context_credential_file"],
                record["account_session_credential_file"],
                run_dir=self.run_dir,
            )
            if urlsplit(record["web_origin"]).scheme != "https":
                raise SmokeError("browser fixture configuration invalid")
            self.credentials.add(record["password"], record["email"])
            return record
        if command == "inspect_browser_session":
            if (
                set(record)
                != {"kind", "slot", "exists", "unexpired", "member", "active_tenant"}
                or record.get("kind") != "browser_session"
                or record.get("slot") != request["slot"]
                or type(record.get("exists")) is not bool
                or type(record.get("unexpired")) is not bool
                or type(record.get("member")) is not bool
                or record.get("active_tenant") not in ("fixed", "other", "none")
            ):
                raise SmokeError("browser session observation invalid")
            return record
        if record != {"kind": "result", "command": command, "status": "ok"}:
            raise SmokeError("browser owner mutation rejected")
        return record


def validate_browser_failure(record) -> dict:
    fields = {"kind", "stage", "error_type", "driver_line", "driver_column"}
    stages = (
        "config",
        "cold_login",
        "shared_admin",
        "tenant_rejection_recovery",
        "ui_logout",
        "independent_revocation",
        "browser_close",
    )
    if (
        not isinstance(record, dict)
        or set(record) != fields
        or record.get("kind") != "browser_failure"
        or record.get("stage") not in stages
        or record.get("error_type") not in ("Error", "TimeoutError")
    ):
        raise SmokeError("browser failure diagnostic invalid")
    line, column = record["driver_line"], record["driver_column"]
    if not (
        (line is None and column is None)
        or (
            type(line) is int
            and type(column) is int
            and 1 <= line <= 100_000
            and 1 <= column <= 100_000
        )
    ):
        raise SmokeError("browser failure frame invalid")
    return record


class BrowserJourneyError(SmokeError):
    def __init__(self, record):
        self.diagnostic = dict(validate_browser_failure(record))
        self.stage = self.diagnostic["stage"]
        super().__init__("browser " + self.stage + " failed")


def run_browser_journeys(
    *,
    node,
    env,
    broker,
    web_origin,
    proxy_port,
    processes,
    browser_processes,
    log,
    work_dir,
    timeout=180,
) -> dict:
    deadline = time.monotonic() + timeout
    reader = None
    # Do not inherit inspector/debug flags that could log private protocol input.
    driver_env = {
        key: value
        for key, value in env.items()
        if key in {"PATH", "HOME", "TMPDIR", "LANG", "LC_ALL", "TZ"}
    }
    process = subprocess.Popen(
        [str(node), str(Path(__file__).with_name("web_native_session_chromium.mjs"))],
        cwd=ROOT,
        env=driver_env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=log,
        start_new_session=True,
        bufsize=0,
    )
    processes.append(process)
    browser_processes.append(process)
    try:
        if process.stdout is None:
            raise SmokeError("browser protocol unavailable")
        reader = session.ProtocolReader(process.stdout.fileno())
        private_json_write(
            process.stdin,
            {
                "kind": "config",
                "app": str(APP),
                "origin": web_origin,
                "port": proxy_port,
                "work_dir": str(work_dir),
            },
            deadline - time.monotonic(),
        )
        for _ in range(64):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise SmokeError("browser deadline exceeded")
            message = reader.record(timeout=remaining)
            if not isinstance(message, dict):
                raise SmokeError("browser protocol invalid")
            if (
                set(message) == {"kind", "request"}
                and message["kind"] == "owner_command"
            ):
                response = broker.dispatch(
                    message["request"], timeout=deadline - time.monotonic()
                )
                private_json_write(process.stdin, response, deadline - time.monotonic())
            elif message.get("kind") == "browser_failure":
                raise BrowserJourneyError(message)
            elif message.get("kind") == "browser_result":
                result = validate_browser_receipt(message)
                if process.wait(timeout=max(0.001, deadline - time.monotonic())) != 0:
                    raise SmokeError("browser driver failed")
                return result
            else:
                raise SmokeError("browser protocol invalid")
        raise SmokeError("browser command limit exceeded")
    except BrowserJourneyError:
        raise
    except Exception:
        raise SmokeError("browser journeys failed") from None
    finally:
        if reader is not None:
            reader.close()


class NativeCleanupError(SmokeError):
    def __init__(self, failures: list[str], quiescent: bool):
        self.failures = failures
        self.quiescent = quiescent
        super().__init__("; ".join(failures))


def native_web_redis_keys(resources: runtime.OwnedResources, origin: str) -> set[str]:
    """The current App owns login-flow and CSRF keys, scoped by public origin."""
    digest = hashlib.sha256(origin.encode()).hexdigest()
    keys: set[str] = set()
    for name in ("iam-signin-flow", "iam-csrf"):
        prefix = f"kokoro:web:{name}:{digest}:"
        found = set(
            resources.command(
                [
                    "redis-cli",
                    "-e",
                    "-u",
                    resources.redis_url,
                    "--scan",
                    "--pattern",
                    prefix + "*",
                ]
            ).splitlines()
        )
        if any(not key.startswith(prefix) for key in found):
            raise SmokeError("Web Redis inventory outside run namespace")
        keys.update(found)
    return keys


def cleanup_web_redis(
    resources: runtime.OwnedResources, origin: str, before: set[str]
) -> None:
    if before:
        raise SmokeError("Web Redis namespace was preexisting")
    keys = sorted(native_web_redis_keys(resources, origin))
    for start in range(0, len(keys), 100):
        resources.command(
            [
                "redis-cli",
                "-e",
                "-u",
                resources.redis_url,
                "UNLINK",
                *keys[start : start + 100],
            ]
        )
    if native_web_redis_keys(resources, origin):
        raise SmokeError("Web Redis namespace remains")


def close_native_resources(
    processes,
    proxies,
    reader,
    resources,
    *,
    iam_process=None,
    browser_process=None,
    iam_identity=None,
    iam_before=None,
    iam_owner_token=None,
    web_origin=None,
    web_before=None,
) -> None:
    """Close independent resources; retain dependencies when producers may live.

    The IAM host's graceful shutdown removes its DB and credentials. Avoid that
    path while a Web/BFF consumer may still be using those resources.
    Error text is deliberately allowlisted, never copied from an exception.
    """
    failures: list[str] = []
    quiescent = True
    if browser_process is not None:
        try:
            runtime.stop_owned_process(browser_process)
            browser_process.wait(timeout=5)
            if runtime.process_group_exists(browser_process.pid):
                raise SmokeError("browser process group remains")
        except Exception:
            failures.append("browser process cleanup failed")
            quiescent = False
    for proxy in reversed(proxies):
        try:
            proxy.close()
            thread = getattr(proxy, "thread", None)
            if thread is not None and thread.is_alive():
                raise SmokeError("proxy thread remains")
        except Exception:
            failures.append("owned proxy cleanup failed")
            quiescent = False
    for process in reversed(processes):
        if process is browser_process:
            continue
        if process is iam_process and not quiescent:
            # Leaving stdin open only delays EOF until this runner exits. Kill
            # this owned group without invoking IAM's DB/credential teardown.
            try:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait(timeout=5)
                if runtime.process_group_exists(process.pid):
                    raise SmokeError("IAM process group remains")
            except Exception:
                failures.append("IAM forced process cleanup failed")
            failures.append("IAM resource cleanup deferred: consumers not quiescent")
            continue
        try:
            runtime.stop_owned_process(process)
        except Exception:
            failures.append("owned process cleanup failed")
            quiescent = False
    if reader is not None:
        try:
            reader.close()
        except Exception:
            failures.append("IAM protocol cleanup failed")
    if quiescent:
        for process in reversed(processes):
            for name in ("stdin", "stdout", "stderr"):
                stream = getattr(process, name, None)
                if stream is not None:
                    try:
                        stream.close()
                    except Exception:
                        failures.append("owned pipe cleanup failed")
    if not quiescent:
        failures.append("dependency cleanup deferred: runtime not quiescent")
    else:
        if resources is not None:
            if web_before is not None:
                try:
                    cleanup_web_redis(resources, web_origin, web_before)
                except Exception:
                    failures.append("Web Redis cleanup failed")
            for label, action in (
                ("owned database cleanup", resources.cleanup),
                ("owned resource cleanup verification", resources.verify_clean),
            ):
                try:
                    action()
                except Exception:
                    failures.append(label + " failed")
            if iam_before is not None:
                try:
                    if iam_before != (set(), set()):
                        raise SmokeError("IAM namespace was preexisting")
                    after = web.iam_owned_inventory(resources, iam_identity)
                    if after != iam_before and iam_owner_token is not None:
                        web.reconcile_iam_identity(
                            resources, iam_identity, iam_owner_token
                        )
                        after = web.iam_owned_inventory(resources, iam_identity)
                    if after != iam_before:
                        raise SmokeError("IAM resources remain")
                except Exception:
                    failures.append("IAM resource cleanup failed")
    if failures:
        raise NativeCleanupError(failures, quiescent)


def run_native_command(command, *, cwd, env, log, processes) -> None:
    """Track build/install children as well as service children for failed stops."""
    process = subprocess.Popen(
        command,
        cwd=cwd,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=log,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    processes.append(process)
    try:
        if process.wait(timeout=90) != 0:
            raise SmokeError("owned command failed")
    except subprocess.TimeoutExpired:
        raise SmokeError("owned command deadline exceeded") from None
    # Keep the handle registered even if termination fails. The final cleanup
    # retries and refuses to drop data while this process group still exists.
    runtime.stop_owned_process(process)
    processes.remove(process)


def observe_node_version(node: Path) -> str:
    result = subprocess.run(
        [str(node), "--version"], capture_output=True, text=True, timeout=5, check=True
    ).stdout.strip()
    if not re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+", result):
        raise SmokeError("Node version response invalid")
    return result.removeprefix("v")


def require_json(response: web.BrowserResponse, status: int, label: str) -> dict:
    if response.status != status:
        raise SmokeError(f"{label}: HTTP {response.status}, expected {status}")
    try:
        body = json.loads(response.body)
    except (ValueError, UnicodeError):
        raise SmokeError(f"{label}: JSON response invalid") from None
    if not isinstance(body, dict):
        raise SmokeError(f"{label}: JSON object required")
    return body


def _project_write_facts(resources: runtime.OwnedResources, db_url: str) -> dict:
    sql = """
        SELECT json_build_object(
          'projects', COALESCE((
            SELECT json_agg(json_build_array(project_id, tenant_id, owner_id, name)
                            ORDER BY project_id)
            FROM kokoro_bff.bff_project
          ), '[]'::json),
          'receipts', COALESCE((
            SELECT json_agg(row_to_json(receipt) ORDER BY scope)
            FROM kokoro_bff.bff_idempotency_receipt AS receipt
          ), '[]'::json)
        )
    """
    result = resources.command(
        ["psql", db_url, "-X", "-v", "ON_ERROR_STOP=1", "-Atc", sql]
    )
    try:
        facts = json.loads(result)
    except (ValueError, UnicodeError):
        raise SmokeError("BFF Project owner facts malformed") from None
    if (
        not isinstance(facts, dict)
        or set(facts) != {"projects", "receipts"}
        or not all(isinstance(value, list) for value in facts.values())
    ):
        raise SmokeError("BFF Project owner facts malformed")
    return facts


def exercise_project_write_admission(
    resources: runtime.OwnedResources,
    db_url: str,
    bff_base: str,
    secret: str,
    ready: session.Ready,
    receipt: NativeReceipt,
    iam: subprocess.Popen[bytes],
    reader: session.ProtocolReader,
) -> None:
    """Verify real native Project ownership and fail-closed receipt replay."""
    if _project_write_facts(resources, db_url) != {"projects": [], "receipts": []}:
        raise SmokeError("BFF Project qualification requires an empty owned database")

    key = "native-project-" + secrets.token_hex(12)
    name = "Native IAM owned Project"
    headers = {
        "content-type": "application/json",
        "x-kokoro-service": "web-bff",
        "x-kokoro-internal-secret": secret,
        "origin": receipt.iam_web_origin,
        "cookie": receipt.cookie,
        "x-kokoro-namespace": "forged-tenant",
        "x-kokoro-principal-id": "forged-user",
    }

    def post(command_key: str, *, with_cookie: bool = True) -> tuple[int, dict]:
        outgoing = {**headers, "idempotency-key": command_key}
        if not with_cookie:
            del outgoing["cookie"]
        return session.request(
            bff_base,
            "/v1/projects",
            method="POST",
            headers=outgoing,
            body={"name": name},
        )

    status, body = post(key)
    data = session.require_success(status, body, "native Project create")
    project = data.get("project")
    if (
        not isinstance(project, dict)
        or not isinstance(project.get("id"), str)
        or not project["id"]
    ):
        raise SmokeError("BFF Project create identity missing")
    before_denials = _project_write_facts(resources, db_url)
    if before_denials["projects"] != [
        [project["id"], ready.tenant_id, ready.user_id, name]
    ]:
        raise SmokeError(
            "BFF Project persisted owner differs from the native IAM identity"
        )
    receipts = before_denials["receipts"]
    if len(receipts) != 1 or not isinstance(receipts[0], dict):
        raise SmokeError("BFF Project create did not persist exactly one receipt")
    committed = receipts[0]
    scope = json.dumps(
        [ready.tenant_id, ready.user_id, "POST", "/projects", key],
        separators=(",", ":"),
    )
    if (
        committed.get("scope") != scope
        or committed.get("status") != 200
        or committed.get("response_body") != body
    ):
        raise SmokeError("BFF Project receipt differs from the admitted command")

    def deny(
        command_key: str,
        expected_status: int,
        code: str,
        label: str,
        *,
        with_cookie: bool = True,
    ) -> None:
        status, body = post(command_key, with_cookie=with_cookie)
        session.require_error(status, body, expected_status, code, label)
        if _project_write_facts(resources, db_url) != before_denials:
            raise SmokeError(
                label + ": denied request changed Project or receipt facts"
            )

    deny(
        key + "-anonymous",
        401,
        "session_authentication_required",
        "native Project without Cookie",
        with_cookie=False,
    )
    session.host_command(iam, reader, "remove_member")
    deny(key, 403, "session_forbidden", "native Project replay after member removal")
    deny(
        key + "-revoked",
        403,
        "session_forbidden",
        "native Project create after member removal",
    )
    session.host_command(iam, reader, "signout")
    deny(key, 401, "session_invalid", "native Project replay after signout")


def _register_native_credentials(
    credentials: web.previous.CredentialRegistry,
    receipt: NativeReceipt,
    *,
    run_dir: Path,
) -> None:
    credentials.add(receipt.cookie)
    for pair in receipt.cookie.split(";"):
        credentials.add(pair.partition("=")[2].strip())
    for path in purpose_credential_paths(
        receipt.bff_user_context_credential_file,
        receipt.account_session_credential_file,
        run_dir=run_dir,
    ):
        document = json.loads(path.read_text())
        credentials.add(*(entry["secret"] for entry in document["entries"]))


def exercise_project_cross_identity_and_outage(
    resources: runtime.OwnedResources,
    db_url: str,
    bff_base: str,
    secret: str,
    ready: session.Ready,
    receipt: NativeReceipt,
    iam: subprocess.Popen[bytes],
    reader: session.ProtocolReader,
    *,
    bff: subprocess.Popen[bytes],
    bff_env: dict[str, str],
    bff_node: Path,
    processes: list[subprocess.Popen[bytes]],
    run_dir: Path,
    credentials: web.previous.CredentialRegistry,
    log,
) -> None:
    """Prove a fresh native principal cannot read A's Project, even during IAM outage."""
    facts = _project_write_facts(resources, db_url)
    projects = facts["projects"]
    if (
        len(projects) != 1
        or len(facts["receipts"]) != 1
        or not isinstance(projects[0], list)
        or len(projects[0]) != 4
        or not isinstance(projects[0][0], str)
        or not projects[0][0]
        or projects[0][1:3] != [ready.tenant_id, ready.user_id]
    ):
        raise SmokeError("BFF Project A owner facts absent before identity reset")
    project_id = projects[0][0]

    # Quiesce the old BFF before resetting the IAM resources it used.
    # Retain its place in the final teardown order when registering the new BFF.
    index = processes.index(bff)
    runtime.stop_owned_process(bff)
    if runtime.process_group_exists(bff.pid):
        raise SmokeError("old BFF process group remains after stop")
    processes.pop(index)

    session.host_command(iam, reader, "reset")
    next_ready = session.validate_ready(reader.record(timeout=60))
    credentials.add(next_ready.access_token)
    next_receipt = native_command(iam, reader, run_dir=run_dir)
    _register_native_credentials(credentials, next_receipt, run_dir=run_dir)
    if (
        next_ready.tenant_id == ready.tenant_id
        or next_ready.user_id == ready.user_id
        or next_receipt.cookie == receipt.cookie
        or next_receipt.iam_web_origin != receipt.iam_web_origin
    ):
        raise SmokeError("IAM reset did not produce an independent native identity")

    replacement_env = {
        **bff_env,
        "KOKORO_IAM_BASE_URL": next_ready.base_url,
        "KOKORO_TENANT_ID": next_ready.tenant_id,
        "KOKORO_BFF_IAM_USER_CONTEXT_SERVICE_CREDENTIAL_FILE": next_receipt.bff_user_context_credential_file,
        "KOKORO_BFF_IAM_ACCOUNT_SESSIONS_SERVICE_CREDENTIAL_FILE": next_receipt.account_session_credential_file,
    }
    replacement = runtime.start_process(bff_node, BFF, replacement_env, log)
    processes.insert(index, replacement)
    runtime.wait_ready(bff_base, replacement)
    headers = {
        "x-kokoro-service": "web-bff",
        "x-kokoro-internal-secret": secret,
        "cookie": next_receipt.cookie,
        "origin": next_receipt.iam_web_origin,
    }
    status, body = session.request(bff_base, "/v1/projects", headers=headers)
    if session.require_success(status, body, "native identity B Projects") != {
        "projects": []
    }:
        raise SmokeError("independent native identity could list the original Project")
    status, body = session.request(
        bff_base, "/v1/projects/" + quote(project_id, safe=""), headers=headers
    )
    session.require_error(
        status, body, 404, "project_not_found", "native identity B direct Project read"
    )
    if _project_write_facts(resources, db_url) != facts:
        raise SmokeError("independent native reads changed the original Project facts")

    # This intentional outage stops only the owned IAM fixture and waits for its
    # terminal ACK and process exit before probing the still-live replacement BFF.
    session.host_command(iam, reader, "stop")
    if iam.wait(timeout=30) != 0 or runtime.process_group_exists(iam.pid):
        raise SmokeError("owned IAM did not exit cleanly before outage probe")
    status, body = session.request(bff_base, "/v1/projects", headers=headers)
    session.require_error(
        status, body, 503, "iam_admission_unavailable", "native IAM outage"
    )
    if _project_write_facts(resources, db_url) != facts:
        raise SmokeError("native IAM outage changed the original Project facts")


def main(argv=None) -> int:
    args = parse_args(argv)
    run_id = secrets.token_hex(12)
    web_origin = f"https://web-native-{run_id}.example.test"
    host_name = urlsplit(web_origin).hostname
    iam_resource_id = str(uuid4())
    iam_identity = web.IamOwnedIdentity(
        "iam_web_oidc_" + iam_resource_id.replace("-", ""),
        f"iam:test:bff-session-admission-host:{iam_resource_id}:",
    )
    iam_owner_token = secrets.token_hex(16)
    evidence = EVIDENCE_ROOT / run_id
    evidence.mkdir(parents=True, mode=0o700)
    evidence.chmod(0o700)
    directory = Path(tempfile.mkdtemp(prefix="work-", dir=evidence))
    resources = None
    processes: list[subprocess.Popen[bytes]] = []
    proxies: list[web.Proxy] = []
    reader = iam = None
    browser_processes = []
    browser_receipt = None
    browser_failure = None
    credential_log_check = "not_run"
    browser_mode = args.browser_journeys
    required_node_versions = dict(REQUIRED_NODE_VERSIONS)
    if browser_mode:
        required_node_versions["admin"] = ADMIN_NODE_VERSION
    iam_before = web_before = None
    recovery_path = directory / "iam-recovery.json"
    node_versions: dict[str, str | None] = dict.fromkeys(required_node_versions)
    admin_runtime = None
    cases = 0
    stage = "source preflight"
    expected_sources = {
        "iam": args.expected_iam_sha,
        "bff": args.expected_bff_sha,
        "app": args.expected_app_sha,
    }
    if browser_mode:
        expected_sources["admin"] = args.expected_admin_sha
    sources: dict[str, object] = {}
    failures: list[str] = []
    cleanup_failures: list[str] = []
    quiescent = True
    credentials = web.previous.CredentialRegistry(
        args.postgres_admin_url, args.redis_url, iam_owner_token
    )
    for raw in (args.postgres_admin_url, args.redis_url):
        credentials.add(unquote(urlsplit(raw).password or ""))
    # Raw diagnostics are anonymous, never retained or copied to the receipt.
    with tempfile.TemporaryFile(mode="w+b") as log:
        try:
            source_inputs = [
                ("iam", IAM, args.allow_unpublished_iam_gitlink),
                ("bff", BFF, False),
                ("app", APP, False),
            ]
            if browser_mode:
                source_inputs.append(("admin", ADMIN, False))
            for owner, repo, allow_unpublished in source_inputs:
                sources[owner] = verify_source(
                    repo,
                    expected_sources[owner],
                    f"apps/kokoro-{owner}",
                    allow_unpublished,
                )
            stage = "runtime preflight"
            # Current owner engines: IAM/BFF >=24 <25; App >=22 <23.
            environments = {}
            runtime_inputs = [
                ("iam", args.iam_node_bin, args.bff_node_bin.parent),
                ("bff", args.bff_node_bin, args.bff_node_bin.parent),
                ("app", args.web_node_bin, args.web_node_bin.parent),
            ]
            if browser_mode:
                runtime_inputs.append(
                    ("admin", args.web_node_bin, args.web_node_bin.parent)
                )
            for owner, node, package_bin in runtime_inputs:
                node_versions[owner] = observe_node_version(node)
                environments[owner] = session.node_environment(
                    node, "v" + required_node_versions[owner], package_bin
                )
            if browser_mode:
                admin_runtime = admin_runtime_preflight(
                    args.web_node_bin, environments["admin"]
                )
            iam_env, bff_env, web_env = (
                environments[owner] for owner in ("iam", "bff", "app")
            )
            stage = "resource allocation"
            resources = runtime.OwnedResources(
                args.postgres_admin_url, args.redis_url, run_id
            )
            stage = "BFF build"
            run_native_command(
                [str(args.bff_node_bin.parent / "corepack"), "pnpm", "build"],
                cwd=BFF,
                env=bff_env,
                log=log,
                processes=processes,
            )
            stage = "infrastructure preflight"
            resources.command(
                [
                    "psql",
                    args.postgres_admin_url,
                    "-X",
                    "-v",
                    "ON_ERROR_STOP=1",
                    "-Atc",
                    "SELECT 1",
                ]
            )
            if (
                resources.command(
                    ["redis-cli", "-e", "-u", args.redis_url, "PING"]
                ).strip()
                != "PONG"
            ):
                raise SmokeError("Redis unavailable")
            web_before = native_web_redis_keys(resources, web_origin)
            if web_before:
                raise SmokeError("Web Redis namespace already exists")
            iam_inventory = web.iam_owned_inventory(resources, iam_identity)
            if iam_inventory != (set(), set()):
                raise SmokeError("IAM named resources already exist")
            db_url = resources.create_database("bff")
            bff_env.update(
                {
                    "KOKORO_BFF_POSTGRES_URL": bff_owner_database_url(db_url),
                    "KOKORO_BFF_REDIS_URL": args.redis_url,
                }
            )
            stage = "BFF schema installation"
            run_native_command(
                [str(args.bff_node_bin.parent / "corepack"), "pnpm", "db:apply-schema"],
                cwd=BFF,
                env=bff_env,
                log=log,
                processes=processes,
            )
            stage = "IAM host"
            iam_env.update(
                {
                    "IAM_TEST_ADMIN_URL": args.postgres_admin_url,
                    "IAM_TEST_REDIS_URL": args.redis_url,
                    "IAM_TEST_WEB_ORIGIN": web_origin,
                    "NODE_ENV": "test",
                    "TMPDIR": str(directory),
                    "IAM_TEST_RESOURCE_ID": iam_resource_id,
                    "IAM_TEST_RESOURCE_OWNER_TOKEN": iam_owner_token,
                }
            )
            # Keep the exact claim durable before the host can allocate anything.
            # This private file is not a receipt and never contains service URLs.
            with open(
                recovery_path,
                "x",
                opener=lambda path, flags: os.open(path, flags, 0o600),
            ) as recovery:
                json.dump(
                    {
                        "resource_id": iam_resource_id,
                        "database_name": iam_identity.database_name,
                        "redis_prefix": iam_identity.redis_prefix,
                        "owner_token": iam_owner_token,
                    },
                    recovery,
                )
                recovery.flush()
                os.fsync(recovery.fileno())
            iam = subprocess.Popen(
                [str(args.iam_node_bin), "--import", "tsx", str(IAM_HOST)],
                cwd=IAM,
                env=iam_env,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=log,
                start_new_session=True,
                bufsize=0,
            )
            processes.append(iam)
            iam_before = iam_inventory
            if iam.stdout is None:
                raise SmokeError("IAM host protocol absent")
            reader = session.ProtocolReader(iam.stdout.fileno())
            ready = session.validate_ready(reader.record())
            credentials.add(ready.access_token)
            receipt = native_command(iam, reader, run_dir=directory)
            _register_native_credentials(credentials, receipt, run_dir=directory)
            if receipt.iam_web_origin != web_origin:
                raise SmokeError("IAM and Web origins diverged")
            secret = secrets.token_urlsafe(32)
            credentials.add(secret)
            bff_port = runtime.free_port()
            bff_env.update(
                {
                    "KOKORO_BFF_HOST": "127.0.0.1",
                    "KOKORO_BFF_PORT": str(bff_port),
                    "KOKORO_BFF_MODE": "live",
                    "KOKORO_BFF_SHARED_SECRET": secret,
                    "KOKORO_IAM_BASE_URL": ready.base_url,
                    "KOKORO_IAM_WEB_ORIGIN": web_origin,
                    "KOKORO_IAM_ISSUER_URL": web_origin + "/iam",
                    "KOKORO_IAM_WEB_CALLBACK_URI": web_origin
                    + "/api/auth/callback/kokoro-iam",
                    "KOKORO_IAM_WEB_POST_LOGOUT_URI": web_origin + "/auth/sign-in",
                    "KOKORO_BFF_IAM_USER_CONTEXT_SERVICE_CREDENTIAL_FILE": receipt.bff_user_context_credential_file,
                    "KOKORO_BFF_IAM_ACCOUNT_SESSIONS_SERVICE_CREDENTIAL_FILE": receipt.account_session_credential_file,
                    "KOKORO_AGENT_ENABLED": "false",
                    "KOKORO_TENANT_ID": ready.tenant_id,
                    "KOKORO_DOMAIN": f"{run_id}.smoke.localhost",
                }
            )
            stage = "BFF startup"
            bff = runtime.start_process(args.bff_node_bin, BFF, bff_env, log)
            processes.append(bff)
            runtime.wait_ready(f"http://127.0.0.1:{bff_port}", bff)
            bff_proxy = web.Proxy(bff_port)
            proxies.append(bff_proxy)
            stage = "Web startup"
            next_root = web.isolated_next(directory)
            next_port = runtime.free_port()
            web_env.update(
                {
                    "NEXT_PUBLIC_SESSION_PREVIEW": "0",
                    "KOKORO_WEB_ORIGIN": web_origin,
                    "KOKORO_DOMAIN": host_name,
                    "KOKORO_BFF_BASE_URL": f"http://127.0.0.1:{bff_proxy.server_port}",
                    "KOKORO_INTERNAL_SECRET_WEB_BFF": secret,
                    "KOKORO_WEB_REDIS_URL": args.redis_url,
                    "KOKORO_TENANT_ID": ready.tenant_id,
                }
            )
            if browser_mode:
                stage = "Admin isolated build"
                admin_root = isolated_admin_next(directory)
                admin_port = runtime.free_port()
                admin_env = dict(environments["admin"])
                admin_env.update(
                    {
                        "NODE_ENV": "production",
                        "KOKORO_ADMIN_WEB_ORIGIN": web_origin,
                        "KOKORO_TENANT_ID": ready.tenant_id,
                    }
                )
                run_native_command(
                    [
                        str(args.web_node_bin),
                        str(admin_root / "node_modules/next/dist/bin/next"),
                        "build",
                    ],
                    cwd=admin_root,
                    env=dict(admin_env),
                    log=log,
                    processes=processes,
                )
                web_env["KOKORO_ADMIN_INTERNAL_ORIGIN"] = (
                    f"http://127.0.0.1:{admin_port}"
                )
            stage = "Web startup"
            next_process = subprocess.Popen(
                [
                    str(args.web_node_bin),
                    str(next_root / "server.cjs"),
                    str(next_port),
                    host_name,
                ],
                cwd=next_root,
                env=web_env,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=log,
                start_new_session=True,
            )
            processes.append(next_process)
            tls_certificate = web.certificate(directory, host_name)
            web_proxy = web.Proxy(
                next_port,
                host_name,
                tls_certificate,
                hmr_websocket=browser_mode,
            )
            proxies.append(web_proxy)
            stage = "Web HTTPS preflight"
            deadline = time.monotonic() + 30
            while True:
                try:
                    fixture = web.https_browser(
                        web_proxy.server_port, "/api/fixture-origin", web_origin
                    )
                    if fixture.status == 200:
                        break
                except (SmokeError, web.SmokeError, OSError):
                    pass
                if time.monotonic() >= deadline or next_process.poll() is not None:
                    raise SmokeError("Next origin fixture not ready")
                time.sleep(0.1)
            if browser_mode:
                stage = "Admin startup"
                admin_connect = AdminConnectProxy(web_origin, web_proxy.server_port)
                proxies.append(admin_connect)
                admin_env.update(
                    {
                        "HTTPS_PROXY": f"http://127.0.0.1:{admin_connect.server_port}",
                        "NO_PROXY": "",
                        "NODE_EXTRA_CA_CERTS": str(tls_certificate[0]),
                    }
                )
                admin_process = subprocess.Popen(
                    [
                        str(args.web_node_bin),
                        "--use-env-proxy",
                        str(admin_root / "server.cjs"),
                        str(admin_port),
                        host_name,
                    ],
                    cwd=admin_root,
                    env=admin_env,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=log,
                    start_new_session=True,
                )
                processes.append(admin_process)
                stage = "Admin HTTPS preflight"
                wait_admin_ready(web_proxy.server_port, web_origin, admin_process)
                stage = "browser journeys"
                broker = BrowserBroker(
                    iam, reader, credentials=credentials, run_dir=directory
                )
                browser_receipt = validate_browser_receipt(
                    run_browser_journeys(
                        node=args.web_node_bin,
                        env=web_env,
                        broker=broker,
                        web_origin=web_origin,
                        proxy_port=web_proxy.server_port,
                        processes=processes,
                        browser_processes=browser_processes,
                        log=log,
                        work_dir=directory,
                    )
                )
            else:
                stage = "native session"
                session_response = web.https_browser(
                    web_proxy.server_port,
                    "/api/auth/session",
                    web_origin,
                    cookie=receipt.cookie,
                )
                body = require_json(session_response, 200, "native Web session")
                data = body.get("data")
                if not isinstance(data, dict):
                    raise SmokeError("native Web session response drift")
                expires_at = data.get("expires_at")
                if not isinstance(expires_at, str) or not expires_at.endswith("Z"):
                    raise SmokeError("native Web session expiry invalid")
                try:
                    expiry = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
                except ValueError:
                    raise SmokeError("native Web session expiry invalid") from None
                if not exact_browser_fact(
                    body,
                    {
                        "data": {
                            "authenticated": True,
                            "subject": ready.user_id,
                            "tenant_id": ready.tenant_id,
                            "expires_at": expires_at,
                        }
                    },
                ) or expiry <= datetime.now(timezone.utc):
                    raise SmokeError("native Web session response drift")
                cases += 1
                projects = web.https_browser(
                    web_proxy.server_port,
                    "/api/session/projects",
                    web_origin,
                    cookie=receipt.cookie,
                )
                project_body = require_json(projects, 200, "native Web BFF projects")
                if project_body != {"projects": []}:
                    raise SmokeError("native Web BFF project response drift")
                cases += 1
                stage = "native Project write admission"
                exercise_project_write_admission(
                    resources,
                    db_url,
                    f"http://127.0.0.1:{bff_port}",
                    secret,
                    ready,
                    receipt,
                    iam,
                    reader,
                )
                stage = "native session"
                signed_out = web.https_browser(
                    web_proxy.server_port,
                    "/api/auth/session",
                    web_origin,
                    cookie=receipt.cookie,
                )
                out_body = require_json(
                    signed_out, 200, "native Web signed-out session"
                )
                if not exact_browser_fact(out_body, {"data": {"authenticated": False}}):
                    raise SmokeError("native logout was not enforced")
                stage = "native Project cross-identity and IAM outage"
                exercise_project_cross_identity_and_outage(
                    resources,
                    db_url,
                    f"http://127.0.0.1:{bff_port}",
                    secret,
                    ready,
                    receipt,
                    iam,
                    reader,
                    bff=bff,
                    bff_env=bff_env,
                    bff_node=args.bff_node_bin,
                    processes=processes,
                    run_dir=directory,
                    credentials=credentials,
                    log=log,
                )
                stage = "native session"
                cases += 1
        except (Exception, KeyboardInterrupt) as error:
            if isinstance(error, BrowserJourneyError):
                stage = "browser " + error.stage
                browser_failure = error.diagnostic
            failures.append(stage + " failed")
        finally:
            try:
                close_native_resources(
                    processes,
                    proxies,
                    reader,
                    resources,
                    iam_process=iam,
                    browser_process=browser_processes[0] if browser_processes else None,
                    iam_identity=iam_identity,
                    iam_before=iam_before,
                    iam_owner_token=iam_owner_token,
                    web_origin=web_origin,
                    web_before=web_before,
                )
            except NativeCleanupError as error:
                cleanup_failures.extend(error.failures)
                quiescent = error.quiescent
            try:
                log.flush()
                log.seek(0)
                diagnostics = log.read()
                if any(
                    variant.encode() in diagnostics
                    for value in credentials.values()
                    for variant in {
                        value,
                        quote(value, safe=""),
                        quote_plus(value, safe=""),
                    }
                ):
                    raise SmokeError("credential log scan failed")
                credential_log_check = "passed"
                if not failures and not browser_mode:
                    cases += 1
            except Exception:
                credential_log_check = "failed"
                failures.append("credential log scan failed")
            if quiescent and not cleanup_failures:
                try:
                    shutil.rmtree(directory)
                except OSError:
                    cleanup_failures.append("owned files cleanup failed")
            report = {
                "status": "failed" if failures or cleanup_failures else "passed",
                "mode": "browser_journeys" if browser_mode else "minimal_http",
                "scope": (
                    "four native authentication journeys and shared Admin eligibility; not full product acceptance"
                    if browser_mode
                    else "minimal native HTTP smoke; not browser authentication journeys; Admin not exercised"
                ),
                "completed_journeys": len(BROWSER_JOURNEYS)
                if browser_receipt is not None
                else 0,
                "admin_verified": browser_receipt is not None,
                "admin_runtime": admin_runtime,
                "browser": browser_receipt,
                "browser_failure": browser_failure,
                "credential_log_check": credential_log_check,
                "expected_sources": expected_sources,
                "sources": sources,
                "required_node_versions": required_node_versions,
                "node_versions": node_versions,
                "stage": stage,
                "completed_checks": cases,
                "failures": failures,
                "cleanup": {
                    "status": "failed" if cleanup_failures else "passed",
                    "quiescent": quiescent,
                    "failures": cleanup_failures,
                    "owned_files_retained": directory.exists(),
                    "recovery_record": (
                        str(recovery_path.relative_to(evidence))
                        if recovery_path.is_file()
                        else None
                    ),
                },
            }
            receipt_path = evidence / "receipt.json"
            with open(
                receipt_path,
                "x",
                opener=lambda path, flags: os.open(path, flags, 0o600),
            ) as output:
                json.dump(report, output, indent=2)
                output.write("\n")
    print(
        json.dumps(
            {
                "status": report["status"],
                "completed_checks": cases,
                "receipt": str(receipt_path),
            }
        ),
        flush=True,
    )
    if failures or cleanup_failures:
        raise SmokeError("; ".join(failures + cleanup_failures))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (SmokeError, runtime.SmokeError, subprocess.SubprocessError, OSError):
        print("native smoke failed; inspect the sanitized run receipt", file=sys.stderr)
        sys.exit(1)
