#!/usr/bin/env python3
"""Exercise real Web → BFF → IAM RP-only OIDC through a test-owned HTTPS origin.

This runner proves verification and controlled Product Session unavailability; it
does not claim Product Session, refresh, or logout has been implemented in Web.
The test-owned HTTPS front and custom Next host/port prove the public browser
origin; they do not independently prove the internal authority-mismatch guard.
"""

from __future__ import annotations

import argparse
import base64
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import hashlib
from html.parser import HTMLParser
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import ssl
import subprocess
import sys
import tempfile
from threading import Thread
import time
from urllib.parse import parse_qsl, urlencode, urlsplit, unquote
from uuid import UUID, uuid4

import capability_bff_smoke_runtime as runtime
from bff_owner_schema import bff_owner_database_url
import run_bff_iam_oidc_smoke as previous
import run_bff_iam_session_smoke as session

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "apps/kokoro-app"
BFF = ROOT / "apps/kokoro-bff"
IAM = ROOT / "apps/kokoro-iam"
HOST = IAM / "test/fixtures/web-oidc-flow-host.ts"
DEFAULT_WEB_ORIGIN = "https://web.example.test"
MAX_BODY = 1_048_576


class SmokeError(RuntimeError):
    """A failure with no credential-bearing request/response detail."""


@dataclass(frozen=True)
class BrowserResponse:
    status: int
    headers: dict[str, str]
    set_cookies: list[str]
    body: bytes

    def location(self) -> str:
        value = self.headers.get("location")
        if value is None:
            raise SmokeError("browser navigation missing")
        return value


@dataclass(frozen=True)
class IamOwnedIdentity:
    database_name: str
    redis_prefix: str


class BrowserCookies:
    """Small strict jar: name and Path, never global cookie forwarding."""

    def __init__(self, remember=lambda *_: None):
        self._cookies: dict[tuple[str, str], str] = {}
        self._remember = remember

    def update(self, request_path: str, values: list[str]) -> None:
        seen: set[tuple[str, str]] = set()
        for raw in values:
            parts = [part.strip() for part in raw.split(";")]
            name, separator, value = parts[0].partition("=")
            if not separator or not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", name):
                raise SmokeError("browser Set-Cookie invalid")
            attributes: dict[str, str] = {}
            for item in parts[1:]:
                key, _, content = item.partition("=")
                key = key.lower()
                if key in attributes:
                    raise SmokeError("browser Set-Cookie duplicate attribute")
                attributes[key] = content
            if "domain" in attributes:
                raise SmokeError("browser Set-Cookie domain rejected")
            path = attributes.get("path", request_path.rsplit("/", 1)[0] or "/")
            if not path.startswith("/") or path.startswith("//"):
                raise SmokeError("browser Set-Cookie path invalid")
            key = (name, path)
            if key in seen:
                raise SmokeError("browser Set-Cookie duplicate")
            seen.add(key)
            if "max-age" in attributes:
                try:
                    expired = int(attributes["max-age"]) <= 0
                except ValueError:
                    raise SmokeError("browser Set-Cookie Max-Age invalid") from None
            elif "expires" in attributes:
                try:
                    expires = parsedate_to_datetime(attributes["expires"])
                    if expires.tzinfo is None:
                        expires = expires.replace(tzinfo=timezone.utc)
                    expired = expires <= datetime.now(timezone.utc)
                except (TypeError, ValueError, OverflowError):
                    raise SmokeError("browser Set-Cookie Expires invalid") from None
            else:
                expired = False
            if expired:
                self._cookies.pop(key, None)
            else:
                if value:
                    self._remember(value)
                self._cookies[key] = value

    def header(self, path: str) -> str:
        pairs = [
            f"{name}={value}"
            for (name, cookie_path), value in self._cookies.items()
            if path == cookie_path or (path.startswith(cookie_path.rstrip("/") + "/"))
        ]
        return "; ".join(pairs)

    def has_usable_session(self) -> bool:
        return any(
            value
            and (
                re.fullmatch(
                    r"(?:__Secure-)?next-auth\.session-token(?:\.[0-9]+)?", name
                )
                or name == "kokoro_session"
            )
            for (name, _), value in self._cookies.items()
        )


def browser_target(value: str, web_origin: str = DEFAULT_WEB_ORIGIN) -> str:
    if (
        not value
        or len(value) > 8192
        or "\\" in value
        or "#" in value
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise SmokeError("browser target invalid")
    if value.startswith("//"):
        raise SmokeError("browser target invalid")
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc:
        if (
            parsed.scheme + "://" + parsed.netloc != web_origin
            or parsed.username
            or parsed.password
        ):
            raise SmokeError("browser target outside Web origin")
    if not parsed.path.startswith("/") or "%" in parsed.path or "//" in parsed.path:
        raise SmokeError("browser target path invalid")
    return parsed.path + ("?" + parsed.query if parsed.query else "")


def require_unavailable_session(response: BrowserResponse) -> None:
    if (
        response.status != 503
        or response.headers.get("content-type", "").split(";", 1)[0]
        != "application/json"
    ):
        raise SmokeError("verified RP did not fail closed at Product Session boundary")
    try:
        body = json.loads(response.body)
    except (ValueError, UnicodeError):
        raise SmokeError("RP callback response invalid") from None
    if (
        not isinstance(body, dict)
        or body.get("error", {}).get("code") != "product_session_unavailable"
    ):
        raise SmokeError("RP callback did not reach verified boundary")
    jar = BrowserCookies()
    jar.update("/api/auth/callback/kokoro-iam", response.set_cookies)
    if jar.has_usable_session():
        raise SmokeError("RP callback established an unapproved Product Session")


class HiddenInputs(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hidden: dict[str, str] = {}
        self.options: list[str] = []
        self.action: str | None = None
        self.in_form = False
        self.forms = 0

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "form":
            self.forms += 1
            if (
                self.forms != 1
                or self.in_form
                or values.get("method", "").lower() != "post"
            ):
                raise SmokeError("interaction form method invalid")
            self.action = values.get("action")
            self.in_form = True
        if not self.in_form:
            return
        if tag == "input" and values.get("type") == "hidden" and values.get("name"):
            if values["name"] in self.hidden:
                raise SmokeError("duplicate interaction form input")
            self.hidden[values["name"]] = values.get("value", "")
        if tag == "option" and values.get("value"):
            self.options.append(values["value"])

    def handle_endtag(self, tag):
        if tag == "form":
            self.in_form = False


def form_inputs(response: BrowserResponse, expected_action: str) -> HiddenInputs:
    if (
        response.status != 200
        or response.headers.get("content-type") != "text/html; charset=utf-8"
    ):
        raise SmokeError("interaction page unavailable")
    parser = HiddenInputs()
    try:
        parser.feed(response.body.decode("utf-8"))
    except UnicodeError:
        raise SmokeError("interaction page encoding invalid") from None
    if (
        parser.forms != 1
        or parser.in_form
        or parser.action != expected_action
        or not parser.hidden.get("csrf_token")
    ):
        raise SmokeError("interaction CSRF proof absent")
    return parser


def remember_sensitive_query(
    path: str, credentials: previous.CredentialRegistry
) -> None:
    for _, value in parse_qsl(urlsplit(path).query, keep_blank_values=True):
        if len(value) >= 12:
            credentials.add(value)


def single_query_values(path: str, expected: set[str]) -> dict[str, str]:
    try:
        pairs = parse_qsl(
            urlsplit(path).query, keep_blank_values=True, strict_parsing=True
        )
    except ValueError:
        raise SmokeError("OIDC query fields invalid") from None
    if len(pairs) != len(expected) or {name for name, _ in pairs} != expected:
        raise SmokeError("OIDC query fields invalid")
    values = dict(pairs)
    if any(not value for value in values.values()):
        raise SmokeError("OIDC query value missing")
    return values


def named_iam_identity(resource_id: str) -> IamOwnedIdentity:
    try:
        parsed = UUID(resource_id)
    except ValueError:
        raise SmokeError("IAM named resource identity invalid") from None
    if str(parsed) != resource_id:
        raise SmokeError("IAM named resource identity invalid")
    return IamOwnedIdentity(
        "iam_web_oidc_" + parsed.hex,
        f"iam:test:web-oidc-flow-host:{resource_id}:",
    )


def capture_token_response(
    credentials: previous.CredentialRegistry,
    authorization: str,
    status: int,
    content_type: str,
    payload: bytes,
) -> None:
    """Register only real BFF token-exchange secrets; never record their values."""
    if (
        status != 200
        or content_type.split(";", 1)[0].strip().lower() != "application/json"
    ):
        return
    if authorization.startswith("Basic "):
        encoded = authorization.removeprefix("Basic ")
        try:
            base64.b64decode(encoded, validate=True)
        except (ValueError, base64.binascii.Error):
            raise SmokeError("BFF token authorization invalid") from None
        credentials.add(encoded)
    try:
        document = json.loads(payload)
    except (ValueError, UnicodeError):
        raise SmokeError("BFF token response invalid") from None
    if not isinstance(document, dict):
        raise SmokeError("BFF token response invalid")
    for name in ("access_token", "refresh_token", "id_token"):
        value = document.get(name)
        if isinstance(value, str) and value:
            credentials.add(value)


def iam_owned_inventory(
    resources: runtime.OwnedResources, ready: previous.Ready | IamOwnedIdentity
) -> tuple[set[str], set[str]]:
    database = resources.command(
        [
            "psql",
            resources.postgres_admin_url,
            "-X",
            "-v",
            "ON_ERROR_STOP=1",
            "-Atc",
            "SELECT datname FROM pg_database WHERE datname = '"
            + ready.database_name
            + "'",
        ]
    ).strip()
    if database not in {"", ready.database_name}:
        raise SmokeError("IAM owned database inventory invalid")
    keys = set(
        resources.command(
            [
                "redis-cli",
                "-e",
                "-u",
                resources.redis_url,
                "--scan",
                "--pattern",
                ready.redis_prefix + "*",
            ]
        ).splitlines()
    )
    if any(not key.startswith(ready.redis_prefix) for key in keys):
        raise SmokeError("IAM owned Redis inventory invalid")
    return ({database} if database else set()), keys


def reconcile_iam_identity(
    resources: runtime.OwnedResources,
    identity: IamOwnedIdentity,
    owner_token: str,
) -> None:
    """Clean only a prefix whose exact IAM NX marker matches this runner."""
    marker = identity.redis_prefix + "fixture-owner"
    owner = resources.command(
        ["redis-cli", "-e", "-u", resources.redis_url, "GET", marker]
    ).strip()
    databases, keys = iam_owned_inventory(resources, identity)
    if owner != owner_token:
        if databases or keys:
            raise SmokeError("IAM named resource ownership unproven")
        return
    if marker not in keys:
        raise SmokeError("IAM named resource marker inventory invalid")
    if databases:
        resources.command(
            [
                "psql",
                resources.postgres_admin_url,
                "-X",
                "-v",
                "ON_ERROR_STOP=1",
                "-Atc",
                f'DROP DATABASE "{identity.database_name}" WITH (FORCE)',
            ]
        )
    remaining = sorted(keys - {marker})
    for start in range(0, len(remaining), 100):
        resources.command(
            [
                "redis-cli",
                "-e",
                "-u",
                resources.redis_url,
                "UNLINK",
                *remaining[start : start + 100],
            ]
        )
    if iam_owned_inventory(resources, identity) != (set(), {marker}):
        raise SmokeError("IAM named resource cleanup incomplete")
    if (
        resources.command(
            ["redis-cli", "-e", "-u", resources.redis_url, "GET", marker]
        ).strip()
        != owner_token
    ):
        raise SmokeError("IAM named resource ownership changed")
    resources.command(["redis-cli", "-e", "-u", resources.redis_url, "UNLINK", marker])
    if iam_owned_inventory(resources, identity) != (set(), set()):
        raise SmokeError("IAM named resource cleanup incomplete")


class ProxyHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, _format, *_args):
        pass

    def do_GET(self):
        self.forward()

    def do_POST(self):
        self.forward()

    def forward(self):
        if len(self.path) > 8192 or not self.path.startswith("/"):
            self.send_error(400)
            return
        try:
            length = int(self.headers.get("content-length", "0"))
            if length < 0 or length > MAX_BODY or self.headers.get("transfer-encoding"):
                self.send_error(413)
                return
            body = self.rfile.read(length) if length else None
            headers = {
                name: value
                for name, value in self.headers.items()
                if name.lower()
                not in {
                    "host",
                    "connection",
                    "transfer-encoding",
                    "x-forwarded-proto",
                    "x-forwarded-host",
                    "x-forwarded-port",
                }
            }
            if self.server.tls_web:
                headers.update(
                    {
                        "Host": self.server.web_host,
                        "X-Forwarded-Proto": "https",
                        "X-Forwarded-Host": self.server.web_host,
                        "X-Forwarded-Port": "443",
                    }
                )
            else:
                headers["Host"] = f"127.0.0.1:{self.server.upstream_port}"
                self.server.observed.append((self.command, self.path.split("?", 1)[0]))
            upstream = http.client.HTTPConnection(
                "127.0.0.1", self.server.upstream_port, timeout=10
            )
            try:
                upstream.request(self.command, self.path, body=body, headers=headers)
                response = upstream.getresponse()
                payload = response.read(MAX_BODY + 1)
                if len(payload) > MAX_BODY:
                    raise SmokeError("proxied response oversized")
                if (
                    self.server.credentials is not None
                    and self.command == "POST"
                    and self.path == "/iam/oauth2/token"
                ):
                    capture_token_response(
                        self.server.credentials,
                        next(
                            (
                                value
                                for name, value in headers.items()
                                if name.lower() == "authorization"
                            ),
                            "",
                        ),
                        response.status,
                        response.getheader("content-type", ""),
                        payload,
                    )
                self.send_response_only(response.status)
                for name, value in response.getheaders():
                    if name.lower() not in {
                        "connection",
                        "transfer-encoding",
                        "content-length",
                    }:
                        self.send_header(name, value)
                self.send_header("Content-Length", str(len(payload)))
                self.send_header("Connection", "close")
                self.end_headers()
                self.wfile.write(payload)
                self.close_connection = True
            finally:
                upstream.close()
        except (OSError, ValueError, SmokeError):
            self.send_error(502)


class Proxy(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(
        self,
        upstream_port: int,
        web_host: str | None = None,
        certificate: tuple[Path, Path] | None = None,
        credentials: previous.CredentialRegistry | None = None,
    ):
        super().__init__(("127.0.0.1", 0), ProxyHandler)
        self.upstream_port = upstream_port
        self.web_host = web_host
        self.tls_web = web_host is not None
        self.observed: list[tuple[str, str]] = []
        self.credentials = credentials
        if certificate is not None:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(str(certificate[0]), str(certificate[1]))
            self.socket = context.wrap_socket(self.socket, server_side=True)
        self.thread = Thread(target=self.serve_forever, daemon=True)
        self.thread.start()

    def close(self):
        self.shutdown()
        self.server_close()
        self.thread.join(timeout=5)


def https_browser(
    port: int,
    path: str,
    web_origin: str,
    *,
    method: str = "GET",
    form: dict | None = None,
    cookie: str = "",
    origin: str | None = None,
    authorization: str | None = None,
) -> BrowserResponse:
    target = browser_target(path, web_origin)
    body = urlencode(form).encode() if form is not None else None
    headers = {
        "Host": urlsplit(web_origin).netloc,
        "Accept": "text/html,application/json",
    }
    if body is not None:
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    if cookie:
        headers["Cookie"] = cookie
    if origin is not None:
        headers["Origin"] = origin
    if authorization is not None:
        headers["Authorization"] = authorization
    connection = http.client.HTTPSConnection(
        "127.0.0.1", port, context=ssl._create_unverified_context(), timeout=12
    )
    try:
        connection.request(method, target, body=body, headers=headers)
        response = connection.getresponse()
        payload = response.read(MAX_BODY + 1)
        if len(payload) > MAX_BODY:
            raise SmokeError("browser response oversized")
        return BrowserResponse(
            response.status,
            {
                name.lower(): value
                for name, value in response.getheaders()
                if name.lower() != "set-cookie"
            },
            [
                value
                for name, value in response.getheaders()
                if name.lower() == "set-cookie"
            ],
            payload,
        )
    except (OSError, http.client.HTTPException):
        raise SmokeError("browser HTTPS request failed") from None
    finally:
        connection.close()


def require_status(response: BrowserResponse, expected: int, stage: str) -> None:
    if response.status != expected:
        raise SmokeError(f"{stage}: HTTP {response.status}, expected {expected}")


def safe_error_code(response: BrowserResponse) -> str:
    try:
        body = json.loads(response.body)
        code = body.get("error", {}).get("code")
    except (ValueError, UnicodeError, AttributeError):
        return "unknown"
    return (
        code
        if isinstance(code, str) and re.fullmatch(r"[a-z][a-z0-9_]{0,79}", code)
        else "unknown"
    )


def navigation_location(response: BrowserResponse, stage: str) -> str:
    if response.status in (302, 303):
        return response.location()
    if (
        response.status == 200
        and response.headers.get("content-type", "").split(";", 1)[0]
        == "application/json"
    ):
        try:
            payload = json.loads(response.body)
        except (ValueError, UnicodeError):
            raise SmokeError(f"{stage}: native redirect malformed") from None
        if (
            isinstance(payload, dict)
            and set(payload) == {"redirect", "url"}
            and payload["redirect"] is True
            and isinstance(payload["url"], str)
        ):
            return payload["url"]
    raise SmokeError(f"{stage}: HTTP {response.status}, expected redirect")


def validate_ready(record: object, web_origin: str) -> previous.Ready:
    if not isinstance(record, dict) or record.get("kind") != "ready":
        raise SmokeError("IAM host ready protocol drift")
    fields = set(previous.Ready.__dataclass_fields__)
    if set(record) != fields | {"kind"} or any(
        not isinstance(record[name], str) or not record[name] for name in fields
    ):
        raise SmokeError("IAM host ready fields invalid")
    if (
        record["issuer_url"] != web_origin + "/iam"
        or record["redirect_uri"] != web_origin + "/api/auth/callback/kokoro-iam"
        or record["post_logout_redirect_uri"] != web_origin + "/auth/sign-in"
    ):
        raise SmokeError("IAM host Web origin mismatch")
    if not re.fullmatch(r"iam_web_oidc_[a-f0-9]{32}", record["database_name"]):
        raise SmokeError("IAM host database identity invalid")
    if not re.fullmatch(
        r"iam:test:web-oidc-flow-host:[0-9a-f-]{36}:", record["redis_prefix"]
    ):
        raise SmokeError("IAM host Redis identity invalid")
    parsed = urlsplit(record["base_url"])
    if parsed.scheme != "http" or parsed.hostname != "127.0.0.1" or parsed.port is None:
        raise SmokeError("IAM host base URL invalid")
    return previous.Ready(**{name: record[name] for name in fields})


def isolated_next(directory: Path) -> Path:
    root = directory / "next"
    root.mkdir()
    for source in ("src", "public"):
        shutil.copytree(WEB / source, root / source)
    for source in (
        "package.json",
        "tsconfig.json",
        "next.config.ts",
        "postcss.config.mjs",
    ):
        shutil.copy2(WEB / source, root / source)
    # The isolated copy and Web's symlinked node_modules must share a Turbopack
    # filesystem root. Keep the copy outside every owner checkout, but under
    # their common parent; the override changes only this test-owned copy.
    config = root / "next.config.ts"
    original = config.read_text()
    marker = "root: process.cwd()"
    if original.count(marker) != 1:
        raise SmokeError("Web Turbopack test fixture config drift")
    config.write_text(original.replace(marker, f"root: {json.dumps(str(ROOT.parent))}"))
    fixture = root / "src/app/api/fixture-origin/route.ts"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        'import { NextRequest } from "next/server"\n'
        "export function GET(request: NextRequest): Response {\n"
        '  return Response.json({ origin: request.nextUrl.origin, host: request.headers.get("host"), '
        'proto: request.headers.get("x-forwarded-proto") })\n}\n'
    )
    (root / "server.cjs").write_text(
        'const http = require("node:http")\n'
        'const next = require("next")\n'
        "const [port, host] = process.argv.slice(2)\n"
        "const app = next({ dev: true, dir: __dirname, hostname: host, port: 443 })\n"
        "app.prepare().then(() => http.createServer(app.getRequestHandler()).listen("
        'Number(port), "127.0.0.1")).catch(() => { process.exitCode = 1 })\n'
    )
    (root / "node_modules").symlink_to(WEB / "node_modules", target_is_directory=True)
    return root


def certificate(directory: Path, host: str) -> tuple[Path, Path]:
    crt, key = directory / "web.crt", directory / "web.key"
    result = subprocess.run(
        [
            "openssl",
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-days",
            "1",
            "-keyout",
            str(key),
            "-out",
            str(crt),
            "-subj",
            f"/CN={host}",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=10,
        check=False,
    )
    if result.returncode != 0:
        raise SmokeError("test-owned TLS certificate creation failed")
    key.chmod(0o600)
    return crt, key


def web_redis_keys(
    redis_url: str, web_origin: str, resources: runtime.OwnedResources
) -> set[str]:
    digest = hashlib.sha256(web_origin.encode()).hexdigest()
    keys: set[str] = set()
    for prefix in ("kokoro:web:oidc-state:", "kokoro:web:iam-csrf:"):
        keys.update(
            resources.command(
                [
                    "redis-cli",
                    "-e",
                    "-u",
                    redis_url,
                    "--scan",
                    "--pattern",
                    prefix + digest + ":*",
                ]
            ).splitlines()
        )
    return keys


def run_browser(
    port: int,
    web_origin: str,
    ready: previous.Ready,
    observed: list[tuple[str, str]],
    credentials: previous.CredentialRegistry,
) -> int:
    jar = BrowserCookies(credentials.add)

    def request(
        path: str,
        *,
        method: str = "GET",
        form: dict | None = None,
        origin: str | None = None,
        authorization: str | None = None,
    ) -> BrowserResponse:
        target = browser_target(path, web_origin)
        response = https_browser(
            port,
            target,
            web_origin,
            method=method,
            form=form,
            cookie=jar.header(urlsplit(target).path),
            origin=origin,
            authorization=authorization,
        )
        jar.update(urlsplit(target).path, response.set_cookies)
        return response

    def navigate(location: str, stage: str) -> str:
        path = browser_target(location, web_origin)
        if len(path) > 8192:
            raise SmokeError(f"{stage}: oversized navigation")
        remember_sensitive_query(path, credentials)
        return path

    # Fail closed before any OAuth transaction and before BFF traffic.
    for endpoint in ("/iam/oauth2/token", "/iam/oauth2/userinfo"):
        require_status(
            request(endpoint, authorization="Bearer browser-probe"),
            404,
            "browser backchannel",
        )
    csrf = request("/api/auth/csrf")
    require_status(csrf, 200, "RP CSRF")
    try:
        csrf_token = json.loads(csrf.body)["csrfToken"]
    except (KeyError, ValueError, TypeError):
        raise SmokeError("RP CSRF proof missing") from None
    credentials.add(csrf_token)
    require_status(
        request(
            "/api/auth/signin/kokoro-iam",
            method="POST",
            form={"csrfToken": csrf_token},
            origin="https://evil.example.test",
        ),
        403,
        "foreign Origin",
    )
    require_status(
        request(
            "/api/auth/signin/kokoro-iam",
            method="POST",
            form={"csrfToken": "wrong"},
            origin=web_origin,
        ),
        403,
        "wrong RP CSRF",
    )
    signin = request(
        "/api/auth/signin/kokoro-iam",
        method="POST",
        form={"csrfToken": csrf_token},
        origin=web_origin,
    )
    require_status(signin, 302, "RP signin")
    authorize_path = navigate(signin.location(), "RP authorization")
    if not authorize_path.startswith("/iam/oauth2/authorize?"):
        raise SmokeError("RP authorization path invalid")
    authorize_query = single_query_values(
        authorize_path,
        {
            "client_id",
            "redirect_uri",
            "response_type",
            "scope",
            "resource",
            "state",
            "nonce",
            "code_challenge",
            "code_challenge_method",
        },
    )
    if (
        authorize_query["client_id"] != ready.client_id
        or authorize_query["redirect_uri"] != ready.redirect_uri
        or authorize_query["response_type"] != "code"
        or authorize_query["scope"] != previous.SCOPES
        or authorize_query["resource"] != previous.RESOURCE
        or authorize_query["code_challenge_method"] != "S256"
        or not re.fullmatch(r"[A-Za-z0-9_-]{16,256}", authorize_query["state"])
        or not re.fullmatch(r"[A-Za-z0-9_-]{16,256}", authorize_query["nonce"])
        or not re.fullmatch(r"[A-Za-z0-9_-]{43}", authorize_query["code_challenge"])
    ):
        raise SmokeError("RP authorization contract drift")
    state = authorize_query["state"]
    credentials.add(state)
    authorize = request(authorize_path)
    path = navigate(
        navigation_location(authorize, "first IAM authorize"), "first IAM interaction"
    )
    if not path.startswith("/auth/sign-in?"):
        raise SmokeError("first IAM interaction was not sign-in")
    page = request(path)
    login_form = form_inputs(page, path)
    credentials.add(login_form.hidden["csrf_token"])
    login = request(
        login_form.action,
        method="POST",
        form={
            "csrf_token": login_form.hidden["csrf_token"],
            "email": ready.email,
            "password": ready.password,
        },
        origin=web_origin,
    )
    if login.status not in (302, 303):
        raise SmokeError(f"IAM sign-in: HTTP {login.status}, expected redirect")
    path = navigate(login.location(), "tenant navigation")
    if not path.startswith("/auth/select-tenant?"):
        raise SmokeError("IAM tenant interaction missing")
    outer_tenant = request(path)
    require_status(outer_tenant, 302, "tenant outer redirect")
    path = navigate(outer_tenant.location(), "tenant page")
    tenant_page = request(path)
    tenant_action = "/iam/interactions/select-tenant?" + urlsplit(path).query
    tenant_form = form_inputs(tenant_page, tenant_action)
    credentials.add(tenant_form.hidden["csrf_token"])
    if ready.tenant_id not in tenant_form.options:
        raise SmokeError("IAM fixture tenant absent")
    tenant = request(
        tenant_form.action,
        method="POST",
        form={
            "csrf_token": tenant_form.hidden["csrf_token"],
            "tenant_ids": tenant_form.hidden.get("tenant_ids", ""),
            "organization_id": ready.tenant_id,
        },
        origin=web_origin,
    )
    if tenant.status not in (302, 303):
        raise SmokeError(
            f"IAM tenant continuation: HTTP {tenant.status}, expected redirect"
        )
    path = navigate(tenant.location(), "consent navigation")
    if not path.startswith("/auth/consent?"):
        raise SmokeError("IAM consent interaction missing")
    outer_consent = request(path)
    require_status(outer_consent, 302, "consent outer redirect")
    path = navigate(outer_consent.location(), "consent page")
    consent_page = request(path)
    consent_action = "/iam/interactions/consent?" + urlsplit(path).query
    consent_form = form_inputs(consent_page, consent_action)
    credentials.add(consent_form.hidden["csrf_token"])
    consent = request(
        consent_form.action,
        method="POST",
        form={"csrf_token": consent_form.hidden["csrf_token"], "decision": "agree"},
        origin=web_origin,
    )
    if consent.status not in (302, 303):
        raise SmokeError(
            f"IAM consent continuation: HTTP {consent.status}, code {safe_error_code(consent)}, expected redirect"
        )
    callback_path = navigate(consent.location(), "RP callback")
    if not callback_path.startswith("/api/auth/callback/kokoro-iam?"):
        raise SmokeError("RP callback path invalid")
    callback_query = single_query_values(callback_path, {"code", "state", "iss"})
    if callback_query["state"] != state or callback_query["iss"] != ready.issuer_url:
        raise SmokeError("RP callback contract drift")
    code = callback_query["code"]
    credentials.add(code)
    callback = request(callback_path)
    require_unavailable_session(callback)
    if jar.has_usable_session():
        raise SmokeError("browser retained usable Product Session")
    if (
        callback.body.find(code.encode()) >= 0
        or callback.body.find(ready.client_secret.encode()) >= 0
    ):
        raise SmokeError("RP callback leaked credential")
    if (
        ("POST", "/iam/oauth2/token") not in observed
        or ("GET", "/iam/oauth2/userinfo") not in observed
        or ("GET", "/iam/jwks") not in observed
    ):
        raise SmokeError("Web to BFF RP backchannel entrance was not observed")
    counts = {
        operation: observed.count(operation)
        for operation in (
            ("POST", "/iam/oauth2/token"),
            ("GET", "/iam/oauth2/userinfo"),
        )
    }
    replay = request(callback_path)
    require_status(replay, 403, "RP callback replay")
    if any(observed.count(operation) != count for operation, count in counts.items()):
        raise SmokeError("RP replay reached IAM backchannel")
    return 14


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in (
        "postgres-admin-url",
        "redis-url",
        "iam-node-bin",
        "bff-node-bin",
        "web-node-bin",
        "expected-iam-sha",
        "expected-bff-sha",
        "expected-web-sha",
    ):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args(argv)
    if urlsplit(args.postgres_admin_url).scheme != "postgresql" or urlsplit(
        args.redis_url
    ).scheme not in {"redis", "rediss"}:
        parser.error("explicit PostgreSQL and Redis URLs required")
    for name in ("iam_node_bin", "bff_node_bin", "web_node_bin"):
        node = Path(getattr(args, name)).expanduser().resolve()
        if not node.is_file() or not os.access(node, os.X_OK):
            parser.error(f"{name} must be executable")
        setattr(args, name, node)
    for name in ("expected_iam_sha", "expected_bff_sha", "expected_web_sha"):
        if not re.fullmatch(r"[a-f0-9]{40}", getattr(args, name)):
            parser.error("expected source SHA must be full commit")
    return args


def main(argv=None) -> int:
    args = parse_args(argv)
    for repo, sha, label in (
        (IAM, args.expected_iam_sha, "apps/kokoro-iam"),
        (BFF, args.expected_bff_sha, "apps/kokoro-bff"),
        (WEB, args.expected_web_sha, "apps/kokoro-app"),
    ):
        session.verify_source(repo, sha, label)
    run_id = secrets.token_hex(12)
    iam_resource_id = str(uuid4())
    iam_identity = named_iam_identity(iam_resource_id)
    iam_owner_token = secrets.token_hex(16)
    web_origin = f"https://web-{run_id}.example.test"
    host_name = urlsplit(web_origin).hostname
    resources = runtime.OwnedResources(args.postgres_admin_url, args.redis_url, run_id)
    iam_env = session.node_environment(
        args.iam_node_bin, "v24.20.0", args.bff_node_bin.parent
    )
    bff_env = session.node_environment(
        args.bff_node_bin, "v22.22.2", args.bff_node_bin.parent
    )
    web_env = session.node_environment(
        args.web_node_bin, "v22.22.2", args.web_node_bin.parent
    )
    credentials = previous.CredentialRegistry(args.postgres_admin_url, args.redis_url)
    credentials.add(iam_owner_token)
    for raw in (args.postgres_admin_url, args.redis_url):
        password = unquote(urlsplit(raw).password or "")
        if len(password) >= 12:
            credentials.add(password)
    processes = []
    proxies: list[Proxy] = []
    reader = None
    ready = None
    during_iam = None
    iam_attempted = False
    before_web = None
    stage = "preflight"
    failures: list[str] = []
    with tempfile.TemporaryDirectory(
        prefix="kokoro-web-bff-iam-", dir=ROOT.parent
    ) as temp:
        directory = Path(temp)
        log_path = directory / "process.log"
        with log_path.open("w+b") as log:
            try:
                stage = "BFF build"
                if (
                    runtime.run_owned_command(
                        [str(args.bff_node_bin.parent / "corepack"), "pnpm", "build"],
                        cwd=BFF,
                        env=bff_env,
                        log=log,
                        timeout=90,
                    )
                    != 0
                ):
                    raise SmokeError("BFF build failed")
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
                before_web = web_redis_keys(args.redis_url, web_origin, resources)
                stage = "BFF database"
                db_url = bff_owner_database_url(resources.create_database("bff"))
                bff_env.update(
                    {
                        "KOKORO_BFF_POSTGRES_URL": db_url,
                        "KOKORO_BFF_REDIS_URL": args.redis_url,
                    }
                )
                runtime.install_schema(
                    "bff", BFF, str(args.bff_node_bin.parent), bff_env, log
                )
                stage = "IAM host"
                if iam_owned_inventory(resources, iam_identity) != (set(), set()):
                    raise SmokeError("IAM named resources already exist")
                iam_env.update(
                    {
                        "IAM_TEST_ADMIN_URL": args.postgres_admin_url,
                        "IAM_TEST_REDIS_URL": args.redis_url,
                        "IAM_TEST_WEB_ORIGIN": web_origin,
                        "IAM_TEST_RESOURCE_ID": iam_resource_id,
                        "IAM_TEST_RESOURCE_OWNER_TOKEN": iam_owner_token,
                        "NODE_ENV": "test",
                    }
                )
                iam_attempted = True
                iam = subprocess.Popen(
                    [str(args.iam_node_bin), "--import", "tsx", str(HOST)],
                    cwd=IAM,
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
                ready = validate_ready(reader.record(), web_origin)
                if (ready.database_name, ready.redis_prefix) != (
                    iam_identity.database_name,
                    iam_identity.redis_prefix,
                ):
                    raise SmokeError("IAM ready identity differs from runner ownership")
                during_iam = iam_owned_inventory(resources, ready)
                if ready.database_name not in during_iam[0]:
                    raise SmokeError("IAM owned database absent after host ready")
                credentials.add(ready.client_secret, ready.password)
                stage = "BFF startup"
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
                        "KOKORO_IAM_ISSUER_URL": ready.issuer_url,
                        "KOKORO_IAM_WEB_ORIGIN": web_origin,
                        "KOKORO_IAM_WEB_CALLBACK_URI": ready.redirect_uri,
                        "KOKORO_IAM_WEB_POST_LOGOUT_URI": ready.post_logout_redirect_uri,
                        "KOKORO_AGENT_ENABLED": "false",
                        "KOKORO_TENANT_ID": ready.tenant_id,
                        "KOKORO_DOMAIN": f"{run_id}.smoke.localhost",
                    }
                )
                bff = runtime.start_process(args.bff_node_bin, BFF, bff_env, log)
                processes.append(bff)
                runtime.wait_ready(f"http://127.0.0.1:{bff_port}", bff)
                bff_proxy = Proxy(bff_port, credentials=credentials)
                proxies.append(bff_proxy)
                stage = "Web HTTPS startup"
                next_root = isolated_next(directory)
                next_port = runtime.free_port()
                web_env.update(
                    {
                        "KOKORO_WEB_ORIGIN": web_origin,
                        "KOKORO_DOMAIN": host_name,
                        "KOKORO_BFF_BASE_URL": f"http://127.0.0.1:{bff_proxy.server_port}",
                        "KOKORO_INTERNAL_SECRET_WEB_BFF": secret,
                        "KOKORO_WEB_REDIS_URL": args.redis_url,
                        "KOKORO_OIDC_CLIENT_ID": ready.client_id,
                        "KOKORO_OIDC_CLIENT_SECRET": ready.client_secret,
                        "KOKORO_WEB_AUTH_SECRET": secrets.token_hex(32),
                        "NEXTAUTH_URL": web_origin + "/api/auth",
                    }
                )
                credentials.add(web_env["KOKORO_WEB_AUTH_SECRET"])
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
                    # Next dev stdout contains request URLs with OAuth secrets.
                    # IAM/BFF logs and Next stderr remain subject to the scan.
                    stdout=subprocess.DEVNULL,
                    stderr=log,
                    start_new_session=True,
                )
                processes.append(next_process)
                web_proxy = Proxy(
                    next_port, host_name, certificate(directory, host_name)
                )
                proxies.append(web_proxy)
                stage = "Web HTTPS origin preflight"
                deadline = time.monotonic() + 30
                last_status = None
                while True:
                    try:
                        fixture = https_browser(
                            web_proxy.server_port, "/api/fixture-origin", web_origin
                        )
                        last_status = fixture.status
                        if fixture.status == 200:
                            break
                    except SmokeError:
                        pass
                    if time.monotonic() >= deadline or next_process.poll() is not None:
                        raise SmokeError(
                            f"Next origin fixture not ready (HTTP {last_status})"
                        )
                    time.sleep(0.1)
                try:
                    origin_readback = json.loads(fixture.body)
                except (ValueError, UnicodeError):
                    raise SmokeError("Next origin fixture malformed") from None
                if origin_readback != {
                    "origin": web_origin,
                    "host": host_name,
                    "proto": "https",
                }:
                    raise SmokeError(
                        f"Next origin readback rejected: {origin_readback}"
                    )
                csrf = https_browser(
                    web_proxy.server_port, "/api/auth/csrf", web_origin
                )
                if csrf.status != 200:
                    raise SmokeError(f"Next RP CSRF HTTPS preflight HTTP {csrf.status}")
                stage = "real browser OIDC"
                cases = run_browser(
                    web_proxy.server_port,
                    web_origin,
                    ready,
                    bff_proxy.observed,
                    credentials,
                )
            except SmokeError as error:
                failures.append(f"{stage}: {error}")
            except Exception:
                failures.append(stage)
            finally:
                for proxy in reversed(proxies):
                    try:
                        proxy.close()
                    except Exception:
                        failures.append("owned proxy cleanup")
                owned_processes_stopped = True
                for process in reversed(processes):
                    try:
                        runtime.stop_owned_process(process)
                    except Exception:
                        owned_processes_stopped = False
                        failures.append("owned process cleanup")
                if reader is not None:
                    try:
                        reader.close()
                    except Exception:
                        failures.append("IAM protocol cleanup")
                if before_web is not None:
                    try:
                        extras = (
                            web_redis_keys(args.redis_url, web_origin, resources)
                            - before_web
                        )
                        if extras:
                            resources.command(
                                [
                                    "redis-cli",
                                    "-e",
                                    "-u",
                                    args.redis_url,
                                    "UNLINK",
                                    *sorted(extras),
                                ]
                            )
                        if (
                            web_redis_keys(args.redis_url, web_origin, resources)
                            != before_web
                        ):
                            failures.append("Web Redis cleanup")
                    except Exception:
                        failures.append("Web Redis cleanup")
                try:
                    resources.cleanup()
                    resources.verify_clean()
                except Exception:
                    failures.append("BFF database cleanup")
                if iam_attempted and owned_processes_stopped:
                    try:
                        reconcile_iam_identity(resources, iam_identity, iam_owner_token)
                    except Exception:
                        failures.append("IAM resource cleanup")
                elif iam_attempted:
                    failures.append(
                        "IAM resource cleanup deferred: process still running"
                    )
                try:
                    log.flush()
                    previous.assert_log_clean(log_path, credentials.values())
                except Exception:
                    failures.append("credential log scan")
    if failures:
        raise SmokeError("; ".join(sorted(set(failures))) + " failed")
    print(
        json.dumps(
            {
                "status": "passed",
                "cases": cases,
                "web_bff_backchannel_entrance_observed": True,
                "product_session": "unavailable",
                "owned_resources_remaining": 0,
            }
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (
        SmokeError,
        runtime.SmokeError,
        session.SmokeError,
        subprocess.SubprocessError,
        OSError,
    ) as error:
        print(f"Web-BFF-IAM smoke failed: {error}", file=sys.stderr)
        sys.exit(1)
