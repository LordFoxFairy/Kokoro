#!/usr/bin/env python3
"""Run the first unconsented IAM OIDC Code+S256 grant through the real BFF relay.

All HTTP uses BFF /iam; IAM is touched only through its test-owned NDJSON host.
"""

from __future__ import annotations

import argparse
import base64
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
import tempfile
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote, quote_plus, unquote, urlencode, urlsplit
from urllib.request import ProxyHandler, Request, build_opener

import capability_bff_smoke_runtime as runtime
from bff_owner_schema import bff_owner_database_url
import run_bff_iam_session_smoke as session

ROOT = Path(__file__).resolve().parents[2]
IAM = ROOT / "apps/kokoro-iam"
BFF = ROOT / "apps/kokoro-bff"
HOST = IAM / "test/fixtures/web-oidc-flow-host.ts"
WEB_ORIGIN = "https://web.example.test"
RESOURCE = "https://kokoro.dev/resources/iam-internal"
SCOPES = "openid profile email offline_access iam:session-authorization.verify iam:member.read iam:invitation.read iam:role.read"
TENANT_CLAIM = "https://kokoro.dev/tenant_id"
TOKEN_KIND_CLAIM = "https://kokoro.dev/token_kind"
LOGOUT_CSP = "default-src 'none'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'"
MAX_BODY = 1_048_576
JSON_CONTENT_TYPES = frozenset({"application/json", "application/json; charset=utf-8"})
PRIMARY_STAGE_LABELS = frozenset({
    "preflight",
    "BFF current-source build",
    "infrastructure preflight",
    "BFF database create",
    "BFF schema install",
    "IAM test host startup",
    "BFF startup",
    "OAuth first grant",
})
FINALIZATION_LABELS = frozenset({
    "owned process cleanup",
    "credential log scan",
    "IAM protocol reader cleanup",
    "BFF database cleanup",
    "BFF resource verification",
    "IAM host resource cleanup",
    "IAM host resource inventory",
})


class SmokeError(RuntimeError):
    """Sanitized failure; do not append URL, body, cookie, token, or exception."""


@dataclass(frozen=True)
class Ready:
    base_url: str
    database_name: str
    redis_prefix: str
    issuer_url: str
    client_id: str
    client_secret: str
    redirect_uri: str
    post_logout_redirect_uri: str
    email: str
    password: str
    tenant_id: str


@dataclass(frozen=True)
class TokenBundle:
    access_token: str
    refresh_token: str
    id_token: str
    subject: str


class CredentialRegistry:
    """Retain every observed credential value until the final process-log scan."""

    def __init__(self, *values: str):
        self._values: set[str] = set()
        self.add(*values)

    def add(self, *values: str) -> None:
        self._values.update(value for value in values if isinstance(value, str) and value)

    def values(self) -> tuple[str, ...]:
        return tuple(sorted(self._values, key=lambda value: (-len(value), value)))


def validate_ready(record: object) -> Ready:
    names = set(Ready.__dataclass_fields__)
    if not isinstance(record, dict) or record.get("kind") != "ready" or set(record) != names | {"kind"}:
        raise SmokeError("IAM host ready protocol drift")
    if any(not isinstance(record[k], str) or not record[k] for k in names):
        raise SmokeError("IAM host ready identity missing")
    try:
        origin = urlsplit(record["base_url"])
        local = (origin.scheme == "http" and origin.hostname in {"127.0.0.1", "localhost"}
                 and origin.port is not None and not origin.username and not origin.password
                 and origin.path in {"", "/"} and not origin.query and not origin.fragment)
    except ValueError:
        local = False
    if not local or not re.fullmatch(r"iam_web_oidc_[a-f0-9]{32}", record["database_name"]):
        raise SmokeError("IAM host resource identity invalid")
    if not re.fullmatch(r"iam:test:web-oidc-flow-host:[0-9a-f-]{36}:", record["redis_prefix"]):
        raise SmokeError("IAM host Redis identity invalid")
    if (record["issuer_url"] != WEB_ORIGIN + "/iam"
            or record["redirect_uri"] != WEB_ORIGIN + "/api/auth/callback/kokoro-iam"
            or record["post_logout_redirect_uri"] != WEB_ORIGIN + "/auth/sign-in"
            or "@" not in record["email"]):
        raise SmokeError("IAM host Web OIDC contract invalid")
    return Ready(**{key: record[key] for key in names})


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("postgres-admin-url", "redis-url", "iam-node-bin", "bff-node-bin", "expected-iam-sha", "expected-bff-sha"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args(argv)
    if urlsplit(args.postgres_admin_url).scheme != "postgresql" or urlsplit(args.redis_url).scheme not in {"redis", "rediss"}:
        parser.error("explicit PostgreSQL and Redis URLs required")
    for name in ("iam_node_bin", "bff_node_bin"):
        node = Path(getattr(args, name)).expanduser().resolve()
        if not node.is_file() or not os.access(node, os.X_OK):
            parser.error(f"{name} must be executable")
        setattr(args, name, node)
    for name in ("expected_iam_sha", "expected_bff_sha"):
        if not re.fullmatch(r"[a-f0-9]{40}", getattr(args, name)):
            parser.error("expected source SHA must be full commit")
    return args


def interaction(url: str) -> tuple[str, str]:
    try:
        parts = urlsplit(url)
        kind = {"/auth/sign-in": "sign-in", "/auth/select-tenant": "select-tenant", "/auth/consent": "consent"}[parts.path]
    except (ValueError, KeyError):
        raise SmokeError("OAuth interaction target invalid") from None
    if (parts.scheme + "://" + parts.netloc != WEB_ORIGIN or parts.username or parts.password
            or parts.fragment or not parts.query or len(parts.query.encode()) > 8192):
        raise SmokeError("OAuth interaction target invalid")
    return kind, parts.query


def authorization_code(url: str, callback: str, state: str) -> str:
    try:
        parts = urlsplit(url)
        query = parse_qs(parts.query, keep_blank_values=True)
        exact = parts.scheme + "://" + parts.netloc + parts.path == callback
        if (not exact or parts.fragment or query.get("state") != [state]
                or len(query.get("code", [])) != 1 or not query["code"][0] or "error" in query):
            raise ValueError()
        return query["code"][0]
    except (ValueError, KeyError):
        raise SmokeError("OAuth callback code/state invalid") from None


def validate_logout_redirect(url: str, callback: str, state: str) -> None:
    try:
        parts = urlsplit(url)
        expected = urlsplit(callback)
        query = parse_qs(parts.query, keep_blank_values=True)
        if (parts.scheme, parts.netloc, parts.path) != (expected.scheme, expected.netloc, expected.path):
            raise ValueError()
        if expected.query or expected.fragment or parts.fragment or query != {"state": [state]}:
            raise ValueError()
    except ValueError:
        raise SmokeError("logout redirect URI/state invalid") from None


def expected_logout_confirmation_body(ready: Ready) -> bytes:
    action = ready.issuer_url + "/oauth2/end-session/confirm"
    return (
        '<!doctype html><html><head><meta charset="utf-8"><title>Confirm logout</title></head><body>'
        '<main><h1>Confirm logout</h1><p>Do you want to log out of this account?</p>'
        f'<form method="post" data-oidc-logout-confirmation action="{action}">'
        '<button type="submit" name="action" value="confirm">Confirm logout</button></form>'
        '</main></body></html>'
    ).encode()


def classify_logout_response(response: HttpResponse, ready: Ready, state: str) -> tuple[str, str | None]:
    if response.status == 302:
        target = response.location()
        validate_logout_redirect(target, ready.post_logout_redirect_uri, state)
        return "redirect", target
    content_type = response.headers.get("content-type")
    if response.status == 200 and content_type in {"application/json", "application/json; charset=utf-8"}:
        payload = response.json()
        if set(payload) != {"redirect", "url"} or payload.get("redirect") is not True or not isinstance(payload.get("url"), str):
            raise SmokeError("logout native redirect response invalid")
        target = payload["url"]
        validate_logout_redirect(target, ready.post_logout_redirect_uri, state)
        return "redirect", target
    if (response.status == 200
            and content_type == "text/html; charset=utf-8"
            and response.headers.get("content-security-policy") == LOGOUT_CSP
            and response.headers.get("x-content-type-options") == "nosniff"
            and response.headers.get("cache-control") == "no-store"
            and response.headers.get("pragma") == "no-cache"
            and response.body == expected_logout_confirmation_body(ready)):
        return "confirmation", None
    raise SmokeError("logout response contract invalid")


def logout_header_evidence(response: HttpResponse) -> dict[str, object]:
    content_type = response.headers.get("content-type")
    content_type_kind = {
        "application/json": "json",
        "application/json; charset=utf-8": "json-utf8",
        "text/html; charset=utf-8": "html-utf8",
    }.get(content_type, "missing" if content_type is None else "other")
    return {
        "content_type": content_type_kind,
        "content_security_policy_matches": response.headers.get("content-security-policy") == LOGOUT_CSP,
        "x_content_type_options_nosniff": response.headers.get("x-content-type-options") == "nosniff",
        "set_cookie_count": len(response.headers.get_all("set-cookie") or []),
    }


class IssuerCookies:
    ALLOWED = frozenset({"session_token", "session_data", "dont_remember",
                         "session_token.oauth_logout_confirmation"})

    def __init__(self, remember=None):
        self.values: dict[str, str] = {}
        self.remember = remember or (lambda *_: None)

    def update(self, cookies: list[str]) -> None:
        for raw in cookies:
            parts = [part.strip() for part in raw.split(";")]
            name, separator, value = parts[0].partition("=")
            attrs = {part.partition("=")[0].lower(): part.partition("=")[2] for part in parts[1:]}
            if name.startswith("kokoro-issuer.") and name.removeprefix("kokoro-issuer.") in self.ALLOWED:
                self.remember(value)
                path = "/iam/oauth2/end-session/confirm" if name.endswith(".oauth_logout_confirmation") else "/iam"
                deletion = attrs.get("max-age") == "0"
                if (not separator or (not value and not deletion) or attrs.get("path") != path or "httponly" not in attrs
                        or attrs.get("samesite", "").lower() != "lax" or "domain" in attrs):
                    raise SmokeError("Issuer Set-Cookie contract invalid")
                if deletion:
                    self.values.pop(name, None)
                else:
                    self.values[name] = value
            else:
                raise SmokeError("Non-issuer Set-Cookie leaked")

    def header(self, *, confirmation: bool = False) -> str:
        return "; ".join(f"{k}={v}" for k, v in self.values.items()
                         if confirmation or not k.endswith(".oauth_logout_confirmation"))


@dataclass(frozen=True)
class HttpResponse:
    status: int
    headers: object
    body: bytes

    def json(self) -> dict:
        require_json_content_type(self)
        try:
            result = json.loads(self.body)
        except (UnicodeError, json.JSONDecodeError):
            raise SmokeError("Native IAM JSON malformed") from None
        if not isinstance(result, dict):
            raise SmokeError("Native IAM JSON object required")
        return result

    def location(self) -> str:
        value = self.headers.get("location")
        if not isinstance(value, str) or not value:
            raise SmokeError("Native IAM Location missing")
        return value


def require_json_content_type(response: HttpResponse) -> None:
    if response.headers.get("content-type") not in JSON_CONTENT_TYPES:
        raise SmokeError("Native IAM JSON content type invalid")


def http(base: str, path: str, secret: str, *, method: str = "GET", payload: dict | None = None,
         form: dict | None = None, cookie: str = "", auth: str = "", origin: bool = False,
         accept: str = "application/json") -> HttpResponse:
    if not path.startswith("/iam/") or "#" in path:
        raise SmokeError("Runner HTTP target invalid")
    headers = {"x-kokoro-service": "web-bff", "x-kokoro-internal-secret": secret, "accept": accept}
    if cookie:
        headers["cookie"] = cookie
    if auth:
        headers["authorization"] = auth
    if origin:
        headers["origin"] = WEB_ORIGIN
    data = None
    if payload is not None:
        data = json.dumps(payload).encode()
        headers["content-type"] = "application/json"
    elif form is not None:
        data = urlencode(form).encode()
        headers["content-type"] = "application/x-www-form-urlencoded"
    request = Request(base + path, method=method, headers=headers, data=data)
    try:
        response = build_opener(ProxyHandler({}), runtime.NoRedirect()).open(request, timeout=8)
    except HTTPError as error:
        response = error
    except (URLError, TimeoutError, OSError):
        raise SmokeError("BFF relay HTTP transport failed") from None
    with response:
        body = response.read(MAX_BODY + 1)
        if len(body) > MAX_BODY:
            raise SmokeError("Native IAM response oversized")
        return HttpResponse(response.status, response.headers, body)


def require(response: HttpResponse, status: int, stage: str) -> dict:
    if response.status != status:
        raise SmokeError(f"{stage}: HTTP {response.status}, expected {status}")
    return response.json()


def redirect_result(response: HttpResponse, stage: str) -> str:
    if response.status == 302:
        return response.location()
    if response.status == 200:
        data = response.json()
        if data.get("redirect") is True and isinstance(data.get("url"), str):
            return data["url"]
    raise SmokeError(f"{stage}: HTTP {response.status}, expected native redirect")


def session_present(response: HttpResponse) -> bool:
    if response.status != 200:
        raise SmokeError(f"get-session: HTTP {response.status}, expected 200")
    require_json_content_type(response)
    try:
        value = json.loads(response.body)
    except (UnicodeError, json.JSONDecodeError):
        raise SmokeError("get-session native JSON malformed") from None
    if value is not None and not isinstance(value, dict):
        raise SmokeError("get-session native body drift")
    return value is not None


def native_error_code(response: HttpResponse) -> str | None:
    require_json_content_type(response)
    try:
        value = json.loads(response.body)
    except (UnicodeError, json.JSONDecodeError):
        return None
    if not isinstance(value, dict):
        return None
    code = value.get("error", value.get("code"))
    return code if isinstance(code, str) and re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]{0,63}", code) else None


def require_revoked_refresh_rejected(response: HttpResponse) -> None:
    if response.status != 400 or native_error_code(response) != "invalid_grant":
        raise SmokeError("revoked refresh token reuse did not return 400 invalid_grant")


def logout_effect(session_still_present: bool, cookie_cleared: bool) -> str:
    if session_still_present:
        raise SmokeError("issuer Session persisted after logout")
    return "set-cookie-cleared" if cookie_cleared else "server-session-invalidated"


def jwt_claims(token: str) -> dict:
    try:
        encoded = token.split(".")[1]
        claims = json.loads(base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)))
    except (IndexError, ValueError, UnicodeError, json.JSONDecodeError):
        raise SmokeError("OAuth token is not JWT") from None
    if not isinstance(claims, dict):
        raise SmokeError("OAuth token claims invalid")
    return claims


def _space_values(value: object, label: str) -> tuple[str, ...]:
    if not isinstance(value, str):
        raise SmokeError(f"{label} invalid")
    values = tuple(value.split(" "))
    if not values or any(not item for item in values) or len(values) != len(set(values)):
        raise SmokeError(f"{label} invalid")
    return values


def _audiences(value: object, label: str) -> tuple[str, ...]:
    if isinstance(value, str):
        values = (value,)
    elif isinstance(value, list) and all(isinstance(item, str) and item for item in value):
        values = tuple(value)
    else:
        raise SmokeError(f"{label} audience invalid")
    if len(values) != len(set(values)):
        raise SmokeError(f"{label} audience invalid")
    return values


def validate_token_bundle(issued: object, ready: Ready, nonce: str) -> TokenBundle:
    if not isinstance(issued, dict):
        raise SmokeError("OIDC token response invalid")
    access = issued.get("access_token")
    refresh = issued.get("refresh_token")
    identity = issued.get("id_token")
    if not all(isinstance(value, str) and value for value in (access, refresh, identity)):
        raise SmokeError("OIDC token response missing credential")
    expected_scopes = set(_space_values(SCOPES, "configured scope"))
    if set(_space_values(issued.get("scope"), "OIDC response scope")) != expected_scopes:
        raise SmokeError("OIDC response scope mismatch")

    access_claims = jwt_claims(access)
    subject = access_claims.get("sub")
    expected_access_audiences = {RESOURCE, ready.issuer_url + "/oauth2/userinfo"}
    if (access_claims.get("iss") != ready.issuer_url
            or set(_audiences(access_claims.get("aud"), "access token")) != expected_access_audiences
            or not isinstance(subject, str) or not subject
            or access_claims.get("client_id") != ready.client_id
            or access_claims.get(TOKEN_KIND_CLAIM) != "user_delegated"
            or set(_space_values(access_claims.get("scope"), "access token scope")) != expected_scopes
            or access_claims.get(TENANT_CLAIM) != ready.tenant_id):
        raise SmokeError("OIDC access token claims invalid")

    identity_claims = jwt_claims(identity)
    if (identity_claims.get("iss") != ready.issuer_url
            or set(_audiences(identity_claims.get("aud"), "ID token")) != {ready.client_id}
            or identity_claims.get("nonce") != nonce
            or identity_claims.get("sub") != subject):
        raise SmokeError("OIDC ID token claims invalid")
    return TokenBundle(access, refresh, identity, subject)


def validate_userinfo(info: object, tokens: TokenBundle) -> None:
    if not isinstance(info, dict) or info.get("sub") != tokens.subject:
        raise SmokeError("userinfo subject mismatch")


def inventory(resources: runtime.OwnedResources) -> tuple[set[str], set[str]]:
    databases = set(resources.command(["psql", resources.postgres_admin_url, "-X", "-v", "ON_ERROR_STOP=1", "-Atc",
                                       "SELECT datname FROM pg_database WHERE datname LIKE 'iam_web_oidc_%'"]).splitlines())
    keys = set(resources.command(["redis-cli", "-e", "-u", resources.redis_url, "--scan", "--pattern",
                                  "iam:test:web-oidc-flow-host:*"]).splitlines())
    return databases, keys


def assert_log_clean(log_path: Path, credentials: tuple[str, ...]) -> None:
    diagnostics = log_path.read_bytes()
    for value in credentials:
        if not value:
            continue
        variants = {value, quote(value, safe=""), quote_plus(value, safe="")}
        if any(variant.encode() in diagnostics for variant in variants):
            raise SmokeError("Credential appeared in process log")


def finalize(processes, stop, cleanup, verify, take_inventory, before, final_checks=()) -> tuple[str, ...]:
    failures = []
    for process in reversed(processes):
        try:
            stop(process)
        except Exception:
            failures.append("owned process cleanup")
    for label, operation in final_checks:
        try:
            operation()
        except Exception:
            failures.append(label if label in FINALIZATION_LABELS else "unknown")
    if before is not None:
        for label, operation in (("BFF database cleanup", cleanup), ("BFF resource verification", verify)):
            try:
                operation()
            except Exception:
                failures.append(label)
        try:
            if take_inventory() != before:
                failures.append("IAM host resource cleanup")
        except Exception:
            failures.append("IAM host resource inventory")
    return tuple(failures)


def raise_for_failures(primary_stage: str | None, finalization_failures: tuple[str, ...]) -> None:
    failures = []
    if primary_stage is not None:
        failures.append("primary: " + (primary_stage if primary_stage in PRIMARY_STAGE_LABELS else "unknown"))
    failures.extend(
        "finalize: " + (label if label in FINALIZATION_LABELS else "unknown")
        for label in finalization_failures
    )
    if failures:
        raise SmokeError("; ".join(failures) + " failed")


def remember_interaction_query(raw_query: str, remember) -> None:
    parsed = parse_qs(raw_query)
    remember(
        raw_query,
        *[
            value
            for key, values in parsed.items()
            if key == "sig" or "token" in key or "code" in key
            for value in values
            if len(value) >= 12
        ],
    )


def start_first_grant(base: str, secret: str, ready: Ready, jar: IssuerCookies, query: str,
                      evidence, remember=lambda *_: None) -> tuple[str, list[str], int]:
    authorized = http(base, "/iam/oauth2/authorize?" + query, secret, accept="text/html")
    jar.update(authorized.headers.get_all("set-cookie") or [])
    target = redirect_result(authorized, "first authorize")
    kind, raw_query = interaction(target)
    if kind != "sign-in":
        raise SmokeError("first OAuth grant omitted sign-in")
    remember_interaction_query(raw_query, remember)
    evidence("first unconsented authorize", authorized.status)

    signed_in = http(base, "/iam/sign-in/email", secret, method="POST", origin=True,
                     payload={"email": ready.email, "password": ready.password})
    require(signed_in, 200, "sign-in/email")
    jar.update(signed_in.headers.get_all("set-cookie") or [])
    if "kokoro-issuer.session_token" not in jar.values:
        raise SmokeError("issuer Session cookie missing")
    evidence("sign-in/email", signed_in.status)

    continued = http(base, "/iam/oauth2/continue", secret, method="POST", origin=True,
                     cookie=jar.header(), payload={"postLogin": True, "oauth_query": raw_query})
    jar.update(continued.headers.get_all("set-cookie") or [])
    target = redirect_result(continued, "sign-in continuation")
    evidence("sign-in continuation", continued.status)
    return target, [kind], 3


def validate_interaction_sequence(seen: list[str]) -> None:
    if seen != ["sign-in", "select-tenant", "consent"]:
        raise SmokeError("first OAuth interaction order invalid")


def run_flow(base: str, secret: str, ready: Ready, credentials: CredentialRegistry) -> int:
    def evidence(step: str, status: int) -> None:
        print(json.dumps({"http_step": step, "status": status}), flush=True)

    cases = 0
    jar = IssuerCookies(credentials.add)
    discovery = require(http(base, "/iam/.well-known/openid-configuration", secret), 200, "discovery")
    if discovery.get("issuer") != ready.issuer_url:
        raise SmokeError("discovery issuer drift")
    evidence("discovery", 200)
    cases += 1
    state = secrets.token_urlsafe(24)
    nonce = secrets.token_urlsafe(24)
    verifier = secrets.token_urlsafe(48)
    credentials.add(state, nonce, verifier)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    query = urlencode({"client_id": ready.client_id, "redirect_uri": ready.redirect_uri,
                       "response_type": "code", "scope": SCOPES, "resource": RESOURCE,
                       "state": state, "nonce": nonce, "code_challenge": challenge,
                       "code_challenge_method": "S256"})
    target, seen_interactions, first_grant_cases = start_first_grant(
        base, secret, ready, jar, query, evidence, credentials.add
    )
    cases += first_grant_cases
    for _ in range(4):
        if target.startswith(ready.redirect_uri + "?"):
            break
        kind, raw_query = interaction(target)
        remember_interaction_query(raw_query, credentials.add)
        seen_interactions.append(kind)
        if kind == "select-tenant":
            response = http(base, "/iam/organization/set-active", secret, method="POST", origin=True,
                            cookie=jar.header(), payload={"organizationId": ready.tenant_id, "oauth_query": raw_query})
        elif kind == "consent":
            response = http(base, "/iam/oauth2/consent", secret, method="POST", origin=True,
                            cookie=jar.header(), payload={"accept": True, "scope": SCOPES, "oauth_query": raw_query})
        else:
            raise SmokeError("first OAuth interaction order invalid")
        jar.update(response.headers.get_all("set-cookie") or [])
        target = redirect_result(response, kind + " continuation")
        evidence(kind + " continuation", response.status)
        cases += 1
    validate_interaction_sequence(seen_interactions)
    code = authorization_code(target, ready.redirect_uri, state)
    credentials.add(code)
    cases += 1
    basic = "Basic " + base64.b64encode(f"{ready.client_id}:{ready.client_secret}".encode()).decode()
    credentials.add(basic)
    token_response = http(base, "/iam/oauth2/token", secret, method="POST", auth=basic,
                          form={"grant_type": "authorization_code", "code": code,
                                "redirect_uri": ready.redirect_uri, "code_verifier": verifier,
                                "resource": RESOURCE})
    issued = require(token_response, 200, "Code+S256 token")
    credentials.add(*[issued.get(name) for name in ("access_token", "refresh_token", "id_token")
                      if isinstance(issued.get(name), str)])
    tokens = validate_token_bundle(issued, ready, nonce)
    evidence("Code+S256 token", token_response.status)
    cases += 1
    info = require(http(base, "/iam/oauth2/userinfo", secret,
                        auth="Bearer " + tokens.access_token), 200, "userinfo")
    validate_userinfo(info, tokens)
    evidence("userinfo", 200)
    cases += 1
    current = session_present(http(base, "/iam/get-session", secret, cookie=jar.header()))
    print(json.dumps({"http_step": "get-session before logout", "status": 200,
                      "session_present": current}), flush=True)
    if not current:
        raise SmokeError("issuer Session missing before logout")
    cases += 1

    revoked = http(base, "/iam/oauth2/revoke", secret, method="POST", auth=basic,
                   form={"token": tokens.refresh_token, "token_type_hint": "refresh_token"})
    if revoked.status != 200:
        raise SmokeError(f"revoke: HTTP {revoked.status}, expected 200")
    evidence("revoke", 200)
    cases += 1
    reused = http(base, "/iam/oauth2/token", secret, method="POST", auth=basic,
                  form={"grant_type": "refresh_token", "refresh_token": tokens.refresh_token,
                        "resource": RESOURCE})
    require_revoked_refresh_rejected(reused)
    evidence("revoked refresh token reuse", reused.status)
    cases += 1

    logout_state = secrets.token_urlsafe(12)
    credentials.add(logout_state)
    stale_cookie = jar.header()
    session_cookie_names = {name for name in jar.values if not name.endswith(".oauth_logout_confirmation")}
    logout_query = urlencode({"id_token_hint": tokens.id_token, "client_id": ready.client_id,
                              "post_logout_redirect_uri": ready.post_logout_redirect_uri, "state": logout_state})
    logout = http(base, "/iam/oauth2/end-session?" + logout_query, secret, cookie=jar.header(), accept="text/html")
    evidence("end-session", logout.status)
    print(json.dumps({"http_step": "end-session response headers",
                      **logout_header_evidence(logout)}), flush=True)
    logout_kind, _ = classify_logout_response(logout, ready, logout_state)
    jar.update(logout.headers.get_all("set-cookie") or [])
    cases += 1
    if logout_kind == "confirmation":
        confirmation_name = "kokoro-issuer.session_token.oauth_logout_confirmation"
        if confirmation_name not in jar.values:
            raise SmokeError("logout confirmation cookie missing")
        confirmed = http(base, "/iam/oauth2/end-session/confirm", secret, method="POST", origin=True,
                         cookie=jar.header(confirmation=True), form={"action": "confirm"}, accept="text/html")
        evidence("end-session confirmation", confirmed.status)
        print(json.dumps({"http_step": "end-session confirmation response headers",
                          **logout_header_evidence(confirmed)}), flush=True)
        confirmed_kind, _ = classify_logout_response(confirmed, ready, logout_state)
        if confirmed_kind != "redirect":
            raise SmokeError("logout confirmation did not complete")
        jar.update(confirmed.headers.get_all("set-cookie") or [])
        if confirmation_name in jar.values:
            raise SmokeError("logout confirmation cookie persisted")
        cases += 1
    cookie_cleared = any(name not in jar.values for name in session_cookie_names)
    after_logout = session_present(http(base, "/iam/get-session", secret, cookie=stale_cookie))
    effect = logout_effect(after_logout, cookie_cleared)
    print(json.dumps({"http_step": "get-session after logout", "status": 200,
                      "session_present": after_logout, "logout_effect": effect}), flush=True)
    cases += 1
    return cases


def main(argv=None) -> int:
    args = parse_args(argv)
    bff_source = session.verify_source(BFF, args.expected_bff_sha, "apps/kokoro-bff")
    iam_source = session.verify_source(IAM, args.expected_iam_sha, "apps/kokoro-iam")
    if not HOST.is_file():
        raise SmokeError("IAM OIDC host missing")
    print(json.dumps({"bff_source": bff_source, "iam_source": iam_source}), flush=True)
    iam_env = session.node_environment(args.iam_node_bin, "v24.20.0", args.bff_node_bin.parent)
    bff_env = session.node_environment(args.bff_node_bin, "v22.22.2", args.bff_node_bin.parent)
    run_id = secrets.token_hex(12)
    resources = runtime.OwnedResources(args.postgres_admin_url, args.redis_url, run_id)
    processes = []
    reader = None
    ready = None
    service_secret = None
    postgres_identity = urlsplit(args.postgres_admin_url)
    redis_identity = urlsplit(args.redis_url)
    database_passwords = tuple(
        value
        for value in (
            unquote(postgres_identity.password or ""),
            unquote(redis_identity.password or ""),
        )
        if len(value) >= 12
    )
    credentials = CredentialRegistry(
        args.postgres_admin_url,
        args.redis_url,
        *database_passwords,
    )
    stage = "preflight"
    cases = 0
    with tempfile.TemporaryDirectory(prefix="kokoro-bff-iam-oidc-") as directory:
        log_path = Path(directory) / "process.log"
        with log_path.open("w+b") as log:
            before = None
            primary_failure_stage = None
            finalization_failures: tuple[str, ...] = ()
            try:
                stage = "BFF current-source build"
                built = runtime.run_owned_command([str(args.bff_node_bin.parent / "corepack"), "pnpm", "build"],
                                                  cwd=BFF, env=bff_env, log=log, timeout=90)
                if built != 0 or not (BFF / "dist/main.js").is_file():
                    raise SmokeError("BFF current-source build failed")
                stage = "infrastructure preflight"
                resources.command(["psql", args.postgres_admin_url, "-X", "-v", "ON_ERROR_STOP=1", "-Atc", "SELECT 1"])
                if resources.command(["redis-cli", "-e", "-u", args.redis_url, "PING"]).strip() != "PONG":
                    raise SmokeError("Shared Redis unavailable")
                before = inventory(resources)
                stage = "BFF database create"
                db_url = bff_owner_database_url(resources.create_database("bff"))
                bff_env.update({"KOKORO_BFF_POSTGRES_URL": db_url, "KOKORO_BFF_REDIS_URL": args.redis_url})
                stage = "BFF schema install"
                runtime.install_schema("bff", BFF, str(args.bff_node_bin.parent), bff_env, log)
                iam_env.update({"IAM_TEST_ADMIN_URL": args.postgres_admin_url, "IAM_TEST_REDIS_URL": args.redis_url,
                                "IAM_TEST_WEB_ORIGIN": WEB_ORIGIN, "NODE_ENV": "test"})
                stage = "IAM test host startup"
                host = subprocess.Popen([str(args.iam_node_bin), "--import", "tsx", str(HOST)], cwd=IAM,
                                        env=iam_env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=log,
                                        start_new_session=True, bufsize=0)
                processes.append(host)
                if host.stdout is None:
                    raise SmokeError("IAM host protocol pipe absent")
                reader = session.ProtocolReader(host.stdout.fileno())
                ready = validate_ready(reader.record())
                service_secret = secrets.token_urlsafe(32)
                credentials.add(ready.client_secret, ready.password, service_secret)
                port = runtime.free_port()
                base = f"http://127.0.0.1:{port}"
                bff_env.update({"KOKORO_BFF_HOST": "127.0.0.1", "KOKORO_BFF_PORT": str(port),
                                "KOKORO_BFF_MODE": "live", "KOKORO_BFF_SHARED_SECRET": service_secret,
                                "KOKORO_IAM_BASE_URL": ready.base_url, "KOKORO_IAM_ISSUER_URL": ready.issuer_url,
                                "KOKORO_IAM_WEB_ORIGIN": WEB_ORIGIN, "KOKORO_IAM_WEB_CALLBACK_URI": ready.redirect_uri,
                                "KOKORO_IAM_WEB_POST_LOGOUT_URI": ready.post_logout_redirect_uri,
                                "KOKORO_AGENT_ENABLED": "false", "KOKORO_TENANT_ID": ready.tenant_id,
                                "KOKORO_DOMAIN": f"{run_id}.smoke.localhost"})
                stage = "BFF startup"
                bff = runtime.start_process(args.bff_node_bin, BFF, bff_env, log)
                processes.append(bff)
                runtime.wait_ready(base, bff)
                stage = "OAuth first grant"
                cases = run_flow(base, service_secret, ready, credentials)
                cases += 1
            except Exception:
                primary_failure_stage = stage
            finally:
                def scan_final_log() -> None:
                    log.flush()
                    assert_log_clean(log_path, credentials.values())

                def close_reader() -> None:
                    if reader is not None:
                        reader.close()

                finalization_failures = finalize(
                    processes,
                    runtime.stop_owned_process,
                    resources.cleanup,
                    resources.verify_clean,
                    lambda: inventory(resources),
                    before,
                    (("credential log scan", scan_final_log),
                     ("IAM protocol reader cleanup", close_reader)),
                )
            raise_for_failures(primary_failure_stage, finalization_failures)
    print(json.dumps({"status": "passed", "cases": cases, "owned_resources_remaining": 0}), flush=True)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (SmokeError, runtime.SmokeError, session.SmokeError, subprocess.SubprocessError, OSError) as error:
        print(f"smoke failed: {error}", file=sys.stderr)
        sys.exit(1)
