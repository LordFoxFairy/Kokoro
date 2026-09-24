#!/usr/bin/env python3
"""Exercise real Web → BFF → IAM Product Session on a test-owned HTTPS origin.

Only the exact pinned, clean three-repository source and test-owned infrastructure
may run. This S1 gate proves RP, Web session, refresh and issuer logout, not the
ordinary Product /v1 Bearer adapter (S2).
"""

from __future__ import annotations

import argparse
from collections.abc import Callable
from dataclasses import dataclass
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
import tempfile
import time
from typing import Protocol
from urllib.parse import unquote, urlsplit
from uuid import uuid4

import run_web_bff_iam_oidc_smoke as old


ROOT = old.ROOT
WEB = old.WEB
BFF = old.BFF
IAM = old.IAM
HOST = old.HOST
runtime = old.runtime
session = old.session
previous = old.previous
SmokeError = old.SmokeError
BrowserCookies = old.BrowserCookies
BrowserResponse = old.BrowserResponse
bff_owner_database_url = old.bff_owner_database_url
browser_target = old.browser_target
https_browser = old.https_browser
remember_sensitive_query = old.remember_sensitive_query
require_status = old.require_status
navigation_location = old.navigation_location
single_query_values = old.single_query_values
form_inputs = old.form_inputs
safe_error_code = old.safe_error_code
named_iam_identity = old.named_iam_identity
iam_owned_inventory = old.iam_owned_inventory
reconcile_iam_identity = old.reconcile_iam_identity
validate_ready = old.validate_ready
isolated_next = old.isolated_next
certificate = old.certificate
Proxy = old.Proxy

PRODUCT_COOKIE = "kokoro_product_session"
CONFIRM_PATH = "/iam/oauth2/end-session/confirm"
CONFIRM_COOKIE_NAMES = frozenset(
    {
        "kokoro-issuer.session_token.oauth_logout_confirmation",
        "__Secure-kokoro-issuer.session_token.oauth_logout_confirmation",
    }
)
PUBLIC_LOGOUT_ERROR_CODES = frozenset(
    {
        "invalid_request",
        "invalid_client",
        "invalid_token",
        "access_denied",
        "server_error",
    }
)


class AuthenticatedRequest(Protocol):
    def __call__(
        self,
        path: str,
        *,
        method: str = "GET",
        form: dict | None = None,
        json_body: dict | None = None,
        origin: str | None = None,
        authorization: str | None = None,
        idempotency_key: str | None = None,
        accept: str | None = None,
    ) -> BrowserResponse: ...


AuthenticatedAction = Callable[[AuthenticatedRequest], str]


def _run_authenticated_action(
    action: AuthenticatedAction | None,
    request: AuthenticatedRequest,
    *,
    authenticated: bool,
) -> str | None:
    if action is not None and authenticated:
        session_id = action(request)
        if not isinstance(session_id, str) or not session_id:
            raise SmokeError("authenticated action session identity missing")
        return session_id
    return None


def require_expected_chat_sessions(body: dict, expected_session_id: str | None) -> None:
    sessions = body.get("sessions")
    if not isinstance(sessions, list):
        raise SmokeError("Product Chat list sessions invalid")
    if expected_session_id is None:
        if sessions:
            raise SmokeError("new Product tenant unexpectedly has Chat sessions")
        return
    if (
        len(sessions) != 1
        or not isinstance(sessions[0], dict)
        or sessions[0].get("session_id") != expected_session_id
    ):
        raise SmokeError("authenticated action Chat session list drift")


def _cookie_parts(cookie: str) -> tuple[str, dict[str, str]]:
    items = [item.strip() for item in cookie.split(";")]
    name, marker, value = items[0].partition("=")
    if not marker or not name or not value:
        raise SmokeError("Product cookie invalid")
    attributes: dict[str, str] = {}
    for item in items[1:]:
        key, _, content = item.partition("=")
        key = key.lower()
        if key in attributes:
            raise SmokeError("cookie duplicate attribute")
        attributes[key] = content
    return name, attributes


def require_product_callback(response: old.BrowserResponse) -> None:
    if (
        response.status != 303
        or response.headers.get("location") != "/app"
        or response.body
    ):
        raise SmokeError("verified RP did not establish Product Session")
    products = [
        cookie
        for cookie in response.set_cookies
        if cookie.startswith(PRODUCT_COOKIE + "=")
    ]
    if len(products) != 1:
        raise SmokeError("Product Session cookie missing or duplicate")
    _, attributes = _cookie_parts(products[0])
    if (
        attributes.get("path") != "/"
        or attributes.get("samesite", "").lower() != "lax"
        or "httponly" not in attributes
        or "secure" not in attributes
        or not attributes.get("max-age", "").isdigit()
        or int(attributes["max-age"]) <= 0
    ):
        raise SmokeError("Product Session cookie attributes invalid")
    if any(
        (
            re.fullmatch(
                r"(?:(?:__Secure-|__Host-))?(?:next-auth|authjs)\.session-token(?:\.\d+)?",
                cookie.split("=", 1)[0],
            )
            or cookie.startswith("kokoro_session=")
        )
        and not re.search(r"(?:^|;)\s*Max-Age=0(?:;|$)", cookie, re.IGNORECASE)
        for cookie in response.set_cookies
    ):
        raise SmokeError("legacy or Auth.js session cookie escaped")


def require_session_projection(
    response: old.BrowserResponse, *, authenticated: bool
) -> dict:
    if response.status != 200 or "no-store" not in response.headers.get(
        "cache-control", ""
    ):
        raise SmokeError("Product Session projection response invalid")
    try:
        body = json.loads(response.body)
    except (ValueError, UnicodeError):
        raise SmokeError("Product Session projection malformed") from None
    if not isinstance(body, dict) or body.get("authenticated") is not authenticated:
        raise SmokeError("Product Session projection state invalid")
    if authenticated:
        if (
            set(body) != {"authenticated", "subject", "expires_at"}
            or not isinstance(body["subject"], str)
            or not body["subject"]
            or type(body["expires_at"]) is not int
            or not (
                int(time.time() * 1_000)
                < body["expires_at"]
                <= int(time.time() * 1_000) + 3_630_000
            )
        ):
            raise SmokeError("Product Session projection leaked fields")
    elif set(body) != {"authenticated"}:
        raise SmokeError("anonymous Product Session projection leaked fields")
    return body


def require_refreshed_projection(initial: dict, refreshed: dict) -> None:
    if (
        refreshed["subject"] != initial["subject"]
        or refreshed["expires_at"] != initial["expires_at"]
    ):
        raise SmokeError("Product refresh changed subject or fixed session expiry")


def _product_chat_response_body(response: BrowserResponse, status: int) -> dict:
    if response.status != status:
        raise SmokeError(
            f"Product Chat proxy HTTP {response.status}, expected {status}"
        )
    if (
        response.headers.get("content-type", "").split(";", 1)[0].strip()
        != "application/json"
    ):
        raise SmokeError("Product Chat proxy content type invalid")
    cache_directives = {
        directive.strip().lower()
        for directive in response.headers.get("cache-control", "").split(",")
    }
    if (
        not {"private", "no-store"}.issubset(cache_directives)
        or "public" in cache_directives
    ):
        raise SmokeError("Product Chat proxy cache policy invalid")
    request_id = response.headers.get("x-request-id", "")
    if re.fullmatch(r"[A-Za-z0-9_-]{1,128}", request_id) is None:
        raise SmokeError("Product Chat proxy request ID invalid")
    try:
        body = json.loads(response.body)
    except (ValueError, UnicodeError):
        raise SmokeError("Product Chat proxy JSON invalid") from None
    if not isinstance(body, dict):
        raise SmokeError("Product Chat proxy body invalid")
    return body


def require_product_chat_list(response: BrowserResponse) -> dict:
    body = _product_chat_response_body(response, 200)
    if (
        set(body) != {"sessions", "next_cursor"}
        or not isinstance(body["sessions"], list)
        or any(not isinstance(item, dict) for item in body["sessions"])
        or (
            body["next_cursor"] is not None and not isinstance(body["next_cursor"], str)
        )
    ):
        raise SmokeError("Product Chat list projection invalid")
    return body


def require_product_chat_rejection(response: BrowserResponse) -> None:
    body = _product_chat_response_body(response, 401)
    error = body.get("error")
    meta = body.get("meta")
    if (
        set(body) != {"error", "meta"}
        or not isinstance(error, dict)
        or set(error) != {"code", "message"}
        or error["code"] != "unauthenticated"
        or not isinstance(error["message"], str)
        or not error["message"]
        or not isinstance(meta, dict)
        or set(meta) != {"request_id"}
        or meta["request_id"] != response.headers["x-request-id"]
    ):
        raise SmokeError("Product Chat rejection envelope invalid")


@dataclass(frozen=True)
class ConfirmationForm:
    action: str
    fields: dict[str, str]


class _ConfirmParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.forms: list[dict[str, str]] = []
        self.buttons: list[dict[str, str]] = []
        self.hidden: dict[str, str] = {}
        self.inside = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        if tag == "form":
            self.forms.append(values)
            self.inside = True
        elif self.inside and tag == "button":
            self.buttons.append(values)
        elif self.inside and tag == "input" and values.get("type") == "hidden":
            name = values.get("name", "")
            if name in self.hidden:
                raise SmokeError("duplicate logout confirmation input")
            self.hidden[name] = values.get("value", "")

    def handle_endtag(self, tag: str) -> None:
        if tag == "form":
            self.inside = False


def require_logout_confirmation(
    response: old.BrowserResponse, web_origin: str
) -> ConfirmationForm:
    if (
        response.status != 200
        or response.headers.get("content-type", "").split(";", 1)[0] != "text/html"
    ):
        try:
            failure = json.loads(response.body)
            wire_error = failure.get("error") if isinstance(failure, dict) else None
            if not isinstance(wire_error, str):
                wire_error = safe_error_code(response)
            if wire_error not in PUBLIC_LOGOUT_ERROR_CODES:
                wire_error = "unknown"
        except (ValueError, UnicodeError):
            wire_error = "unknown"
        media_type = response.headers.get("content-type", "").split(";", 1)[0]
        if media_type not in {"text/html", "application/json"}:
            media_type = "other"
        raise SmokeError(
            "IAM issuer confirmation page absent: "
            f"HTTP {response.status}, "
            f"content-type {media_type}, "
            f"code {wire_error}"
        )
    parser = _ConfirmParser()
    try:
        parser.feed(response.body.decode("utf-8"))
    except UnicodeError:
        raise SmokeError("IAM issuer confirmation malformed") from None
    expected = web_origin + CONFIRM_PATH
    if (
        len(parser.forms) != 1
        or parser.forms[0].get("method", "").lower() != "post"
        or parser.forms[0].get("action") not in {expected, CONFIRM_PATH}
        or len(parser.buttons) != 1
        or parser.buttons[0].get("name") != "action"
        or parser.buttons[0].get("value") != "confirm"
        or set(parser.hidden) - {"csrf_token", "csrfToken"}
        or len(parser.hidden) > 1
    ):
        raise SmokeError("IAM issuer confirmation form invalid")
    cookies = [
        cookie
        for cookie in response.set_cookies
        if cookie.split("=", 1)[0] in CONFIRM_COOKIE_NAMES
    ]
    if len(cookies) != 1:
        raise SmokeError("IAM confirmation cookie missing")
    name, attributes = _cookie_parts(cookies[0])
    if (
        attributes.get("path") != CONFIRM_PATH
        or attributes.get("samesite", "").lower() != "lax"
        or "httponly" not in attributes
        or (name.startswith("__Secure-") and "secure" not in attributes)
    ):
        raise SmokeError("IAM confirmation cookie attributes invalid")
    return ConfirmationForm(CONFIRM_PATH, {**parser.hidden, "action": "confirm"})


@dataclass(frozen=True)
class IssuerIdentity:
    session_id: str
    user_id: str


def require_issuer_session(
    response: old.BrowserResponse,
    *,
    active: bool,
    expected_subject: str | None = None,
) -> IssuerIdentity | None:
    if response.status != 200:
        raise SmokeError("IAM issuer session query unavailable")
    try:
        body = json.loads(response.body)
    except (ValueError, UnicodeError):
        raise SmokeError("IAM issuer session response malformed") from None
    if active:
        if (
            not isinstance(body, dict)
            or not isinstance(body.get("session"), dict)
            or not isinstance(body.get("user"), dict)
        ):
            raise SmokeError("IAM issuer session shape invalid")
        owner = body["user"].get("id")
        session_id = body["session"].get("id")
        session_user = body["session"].get("userId")
        if (
            not isinstance(owner, str)
            or not owner
            or len(owner) > 256
            or not isinstance(session_id, str)
            or not session_id
            or len(session_id) > 256
            or session_user != owner
            or (expected_subject is not None and owner != expected_subject)
        ):
            raise SmokeError("IAM issuer identity does not match Product subject")
        return IssuerIdentity(session_id, owner)
    if body is not None:
        raise SmokeError("IAM issuer session survived logout")
    return None


def require_signout_handoff(
    response: old.BrowserResponse, web_origin: str, ready: previous.Ready
) -> str:
    if response.status != 200 or "no-store" not in response.headers.get(
        "cache-control", ""
    ):
        raise SmokeError("Product logout response invalid")
    try:
        body = json.loads(response.body)
    except (ValueError, UnicodeError):
        raise SmokeError("Product logout response malformed") from None
    if (
        not isinstance(body, dict)
        or body.get("status") != "signed_out"
        or body.get("remote_revocation") != "confirmed"
        or body.get("issuer_session") != "pending_browser_confirmation"
        or set(body)
        != {"status", "remote_revocation", "issuer_session", "issuer_end_session_url"}
        or not isinstance(body["issuer_end_session_url"], str)
    ):
        raise SmokeError("Product logout handoff invalid")
    if not any(
        cookie.startswith(PRODUCT_COOKIE + "=") and "max-age=0" in cookie.lower()
        for cookie in response.set_cookies
    ):
        raise SmokeError("Product logout did not clear browser cookie")
    target = browser_target(body["issuer_end_session_url"], web_origin)
    if urlsplit(target).path != "/iam/oauth2/end-session":
        raise SmokeError("issuer logout target invalid")
    query = single_query_values(target, {"client_id", "post_logout_redirect_uri"})
    if query != {
        "client_id": ready.client_id,
        "post_logout_redirect_uri": ready.post_logout_redirect_uri,
    }:
        raise SmokeError("issuer logout target not bound to registered client")
    return target


def require_stale_signout(response: old.BrowserResponse) -> None:
    if response.status != 200 or "no-store" not in response.headers.get(
        "cache-control", ""
    ):
        raise SmokeError("stale Product logout response invalid")
    try:
        body = json.loads(response.body)
    except (ValueError, UnicodeError):
        raise SmokeError("stale Product logout response malformed") from None
    if body != {"status": "stale_session", "remote_revocation": "not_required"}:
        raise SmokeError("stale Product logout changed current session or issuer")
    if any(cookie.startswith(PRODUCT_COOKIE + "=") for cookie in response.set_cookies):
        raise SmokeError("stale Product logout could overwrite current cookie")


def require_foreign_confirmation_rejected(
    request: Callable[..., BrowserResponse],
    form: ConfirmationForm,
    issuer_session: Callable[[], BrowserResponse],
    observed: list[tuple[str, str]],
    identity: IssuerIdentity,
) -> None:
    operation = ("POST", CONFIRM_PATH)
    before = observed.count(operation)
    hostile = request(
        form.action,
        method="POST",
        form=form.fields,
        origin="https://evil.example.test",
    )
    if hostile.status < 400 or hostile.status >= 500:
        raise SmokeError("foreign issuer logout confirmation was not rejected")
    if observed.count(operation) != before:
        raise SmokeError("foreign issuer logout confirmation reached BFF")
    current = require_issuer_session(
        issuer_session(), active=True, expected_subject=identity.user_id
    )
    if current != identity:
        raise SmokeError("foreign confirmation changed IAM issuer session")


def web_redis_keys(
    redis_url: str, web_origin: str, resources: runtime.OwnedResources
) -> set[str]:
    digest = hashlib.sha256(web_origin.encode()).hexdigest()
    keys = old.web_redis_keys(redis_url, web_origin, resources)
    keys.update(
        resources.command(
            [
                "redis-cli",
                "-e",
                "-u",
                redis_url,
                "--scan",
                "--pattern",
                f"kokoro:web:product-session:{digest}:*",
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
    authenticated_action: AuthenticatedAction | None = None,
) -> None:
    jar = BrowserCookies(credentials.add)

    def request(
        path: str,
        *,
        method: str = "GET",
        form: dict | None = None,
        json_body: dict | None = None,
        origin: str | None = None,
        authorization: str | None = None,
        idempotency_key: str | None = None,
        accept: str | None = None,
    ) -> BrowserResponse:
        target = browser_target(path, web_origin)
        response = https_browser(
            port,
            target,
            web_origin,
            method=method,
            form=form,
            json_body=json_body,
            cookie=jar.header(urlsplit(target).path),
            origin=origin,
            authorization=authorization,
            idempotency_key=idempotency_key,
            accept=accept,
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
    chat_operation = ("GET", "/v1/sessions")
    chat_calls = observed.count(chat_operation)
    require_product_chat_rejection(request("/api/session/sessions?limit=1"))
    if observed.count(chat_operation) != chat_calls:
        raise SmokeError("anonymous Product Chat request reached BFF")
    _run_authenticated_action(authenticated_action, request, authenticated=False)
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
    wrong_csrf = request(
        "/api/auth/signin/kokoro-iam",
        method="POST",
        form={"csrfToken": "wrong"},
        origin=web_origin,
    )
    require_status(wrong_csrf, 303, "wrong RP CSRF")
    if wrong_csrf.location() != "/login?auth=sign_in_failed":
        raise SmokeError("wrong RP CSRF: retry target invalid")
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
        raise SmokeError(
            f"IAM sign-in: HTTP {login.status}, code {old.safe_error_code(login)}, expected redirect"
        )
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
    require_product_callback(callback)
    if not any(
        part.startswith(PRODUCT_COOKIE + "=")
        for part in jar.header("/api/auth/session").split("; ")
    ):
        raise SmokeError("browser did not retain Product Session")
    if (
        callback.body.find(code.encode()) >= 0
        or callback.body.find(ready.client_secret.encode()) >= 0
    ):
        raise SmokeError("RP callback leaked credential")
    for operation in (
        ("POST", "/iam/oauth2/token"),
        ("GET", "/iam/oauth2/userinfo"),
        ("GET", "/iam/jwks"),
    ):
        if operation not in observed:
            raise SmokeError("Web to BFF RP backchannel entrance absent")
    initial_token_calls = observed.count(("POST", "/iam/oauth2/token"))
    initial_userinfo_calls = observed.count(("GET", "/iam/oauth2/userinfo"))
    replay = request(callback_path)
    require_status(replay, 403, "RP callback replay")
    if (
        observed.count(("POST", "/iam/oauth2/token")) != initial_token_calls
        or observed.count(("GET", "/iam/oauth2/userinfo")) != initial_userinfo_calls
    ):
        raise SmokeError("RP replay reached IAM backchannel")

    first_projection = request("/api/auth/session")
    initial_product = require_session_projection(first_projection, authenticated=True)
    live_chat = request(
        "/api/session/sessions?limit=1",
        authorization="Bearer browser-supplied-invalid",
    )
    if require_product_chat_list(live_chat)["sessions"]:
        raise SmokeError("new Product tenant unexpectedly has Chat sessions")
    if observed.count(chat_operation) != chat_calls + 1:
        raise SmokeError("Product Chat request did not cross Web to BFF exactly once")
    chat_calls += 1
    authenticated_session_id = _run_authenticated_action(
        authenticated_action, request, authenticated=True
    )
    old_product_cookie = jar.header("/api/auth/session")
    issuer_cookie = "; ".join(
        pair
        for pair in jar.header("/iam/get-session").split("; ")
        if pair.startswith(("kokoro-issuer.", "__Secure-kokoro-issuer."))
    )
    if not issuer_cookie:
        raise SmokeError("issuer cookie absent before logout")
    initial_issuer = require_issuer_session(
        request("/iam/get-session"),
        active=True,
        expected_subject=initial_product["subject"],
    )
    if initial_issuer is None:
        raise SmokeError("IAM issuer identity absent before logout")
    wrong_refresh = request(
        "/api/auth/session",
        method="POST",
        form={"csrfToken": "wrong"},
        origin=web_origin,
    )
    require_status(wrong_refresh, 403, "RP refresh CSRF")
    if observed.count(("POST", "/iam/oauth2/token")) != initial_token_calls:
        raise SmokeError("rejected refresh reached IAM")
    refresh = request(
        "/api/auth/session",
        method="POST",
        form={"csrfToken": csrf_token},
        origin=web_origin,
    )
    refreshed_product = require_session_projection(refresh, authenticated=True)
    require_refreshed_projection(initial_product, refreshed_product)
    if observed.count(("POST", "/iam/oauth2/token")) != initial_token_calls + 1:
        raise SmokeError("Product refresh did not rotate exactly once")
    stale = https_browser(
        port, "/api/auth/session", web_origin, cookie=old_product_cookie
    )
    require_session_projection(stale, authenticated=False)
    require_product_chat_rejection(
        https_browser(
            port, "/api/session/sessions?limit=1", web_origin, cookie=old_product_cookie
        )
    )
    if observed.count(chat_operation) != chat_calls:
        raise SmokeError("stale Product Chat request reached BFF")
    current_product_cookie = jar.header("/api/auth/session")
    if current_product_cookie == old_product_cookie:
        raise SmokeError("Product Session generation cookie did not rotate")
    refreshed_chat = require_product_chat_list(request("/api/session/sessions?limit=1"))
    require_expected_chat_sessions(refreshed_chat, authenticated_session_id)
    if observed.count(chat_operation) != chat_calls + 1:
        raise SmokeError(
            "refreshed Product Chat request did not cross BFF exactly once"
        )
    chat_calls += 1
    before_stale_revoke = observed.count(("POST", "/iam/oauth2/revoke"))
    require_stale_signout(
        https_browser(
            port,
            "/api/auth/signout",
            web_origin,
            method="POST",
            form={"csrfToken": csrf_token},
            cookie=old_product_cookie,
            origin=web_origin,
        )
    )
    if observed.count(("POST", "/iam/oauth2/revoke")) != before_stale_revoke:
        raise SmokeError("stale Product logout revoked current refresh")
    if (
        require_session_projection(request("/api/auth/session"), authenticated=True)
        != refreshed_product
    ):
        raise SmokeError("Product Session projection changed after refresh")
    before_revoke = observed.count(("POST", "/iam/oauth2/revoke"))
    signout = request(
        "/api/auth/signout",
        method="POST",
        form={"csrfToken": csrf_token},
        origin=web_origin,
    )
    issuer_end_session = require_signout_handoff(signout, web_origin, ready)
    if observed.count(("POST", "/iam/oauth2/revoke")) != before_revoke + 1:
        raise SmokeError("Product logout did not revoke current refresh once")
    require_session_projection(request("/api/auth/session"), authenticated=False)
    require_product_chat_rejection(request("/api/session/sessions?limit=1"))
    require_product_chat_rejection(
        https_browser(
            port,
            "/api/session/sessions?limit=1",
            web_origin,
            cookie=current_product_cookie,
        )
    )
    if observed.count(chat_operation) != chat_calls:
        raise SmokeError("signed-out Product Chat request reached BFF")
    require_session_projection(
        https_browser(
            port, "/api/auth/session", web_origin, cookie=current_product_cookie
        ),
        authenticated=False,
    )

    confirmation = request(issuer_end_session)
    form = require_logout_confirmation(confirmation, web_origin)
    if not any(
        pair.split("=", 1)[0] in CONFIRM_COOKIE_NAMES
        for pair in jar.header(CONFIRM_PATH).split("; ")
    ):
        raise SmokeError("signed issuer confirmation cookie not retained")
    for value in form.fields.values():
        if len(value) >= 12:
            credentials.add(value)
    require_foreign_confirmation_rejected(
        request,
        form,
        lambda: https_browser(
            port, "/iam/get-session", web_origin, cookie=issuer_cookie
        ),
        observed,
        initial_issuer,
    )
    confirmed = request(form.action, method="POST", form=form.fields, origin=web_origin)
    post_logout = navigate(
        navigation_location(confirmed, "issuer logout confirmation"), "post logout"
    )
    if post_logout != browser_target(ready.post_logout_redirect_uri, web_origin):
        raise SmokeError("issuer post-logout navigation invalid")
    # Send the old issuer cookie, not the jar after Set-Cookie deletion, to
    # distinguish server-side invalidation from browser-only cookie clearing.
    require_issuer_session(
        https_browser(port, "/iam/get-session", web_origin, cookie=issuer_cookie),
        active=False,
    )
    if observed.count(("POST", "/iam/oauth2/end-session/confirm")) != 1:
        raise SmokeError("issuer confirmation did not cross BFF once")
    # Signout is checked by require_signout_handoff against an exact public
    # client_id and registered redirect. A generic substring scan there would
    # misclassify the public URL-encoded Web origin as a credential.
    if any(
        secret.encode() in response.body
        for response in (callback, first_projection, live_chat, refresh, confirmed)
        for secret in credentials.values()
        if len(secret) >= 12
    ):
        raise SmokeError("Product Session response leaked credential")


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
                run_browser(
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
                "flow": "web_bff_iam_product_session",
                "web_bff_backchannel_entrance_observed": True,
                "product_chat_proxy": "verified",
                "product_session": "active_then_ended",
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
        print(f"Web-BFF-IAM Product Session smoke failed: {error}", file=sys.stderr)
        sys.exit(1)
