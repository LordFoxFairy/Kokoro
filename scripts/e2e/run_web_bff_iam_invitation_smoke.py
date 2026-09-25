#!/usr/bin/env python3
"""Exercise invitations through test-owned HTTPS Web → BFF → IAM.

The default is an HTTP browser-cookie client; --browser chromium drives real forms.
Owned SMTP, PostgreSQL, Redis and HTTPS resources are cleaned up.
"""

from __future__ import annotations

import json
import http.client
import re
import secrets
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from email import policy
from email.parser import BytesParser
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qsl, unquote, urlsplit
from uuid import uuid4

import run_web_bff_iam_product_session_smoke as product
import run_web_chat_chromium_smoke as chromium_smoke

SmokeError = product.SmokeError
PAGE_PATH = "/iam/interactions/invitation"
UUID = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\Z"
)
EMAIL = re.compile(r"[^@\s]+@[^@\s]+\Z")
CHROMIUM_DRIVER = Path(__file__).resolve().parent / "web_invitation_chromium.mjs"
CHROMIUM_STAGES = frozenset(
    {
        "input",
        "browser",
        "invitation-entry",
        "issuer-sign-in",
        "invitation-decision",
        "product-login",
        "rejected-session",
        "iam-membership",
        "consumed-invitation",
    }
)


def chromium_failure_stage(stderr: bytes | str | None) -> str:
    """Report only controlled stage labels, never browser errors containing links."""
    if not isinstance(stderr, (bytes, str)):
        return "unknown"
    output = (
        stderr.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes)
        else stderr
    )
    for line in reversed(output.splitlines()):
        label = line.removeprefix("Chromium invitation failed at ")
        if label in CHROMIUM_STAGES and line.startswith(
            "Chromium invitation failed at "
        ):
            return label
    return "unknown"


@dataclass(frozen=True, slots=True)
class ChromiumInvitationEvidence:
    decision: str
    owner_post_count: int
    consumed_pending: bool
    product_login_started: bool
    product_authenticated: bool
    rejected_anonymous: bool
    membership_absent: bool


def chromium_invitation(
    *,
    node_bin: Path,
    web_origin: str,
    path: str,
    email: str,
    password: str,
    decision: str,
    screenshot: Path,
    tenant_id: str,
    iam_base_url: str,
    existing_tenant_id: str,
    observed: list[tuple[str, str]],
) -> ChromiumInvitationEvidence:
    """Drive the actual Web forms; the owner relay remains independently observed."""
    parsed = urlsplit(web_origin)
    if parsed.scheme != "https" or parsed.port is None or parsed.hostname is None:
        raise SmokeError("Chromium invitation origin invalid")
    invitation_id = path.rsplit("?id=", 1)[-1]
    if invitation_path(invitation_id) != path or decision not in {"accept", "reject"}:
        raise SmokeError("Chromium invitation target invalid")
    owner_path = f"/iam/v1/tenants/{tenant_id}/invitations/{invitation_id}/{decision}"
    before = observed.count(("POST", owner_path))
    try:
        completed = subprocess.run(
            [str(node_bin), str(CHROMIUM_DRIVER)],
            cwd=product.ROOT,
            text=True,
            input=json.dumps(
                {
                    "web_origin": web_origin,
                    "web_host": parsed.hostname,
                    "web_root": str(product.WEB),
                    "invitation_path": path,
                    "email": email,
                    "password": password,
                    "decision": decision,
                    "screenshot": str(screenshot),
                    "iam_base_url": iam_base_url,
                    "tenant_id": tenant_id,
                    "existing_tenant_id": existing_tenant_id,
                },
                separators=(",", ":"),
            ),
            capture_output=True,
            timeout=90,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        raise SmokeError(
            f"Chromium invitation timed out; stage={chromium_failure_stage(error.stderr)}"
        ) from None
    except (OSError, subprocess.SubprocessError):
        raise SmokeError("Chromium invitation process failed") from None
    if completed.returncode != 0:
        raise SmokeError(
            f"Chromium invitation failed at {chromium_failure_stage(completed.stderr)}"
        )
    try:
        evidence = json.loads(completed.stdout)
    except (TypeError, ValueError):
        raise SmokeError("Chromium invitation evidence malformed") from None
    if (
        not isinstance(evidence, dict)
        or set(evidence)
        != {
            "browser",
            "decision",
            "entry_form",
            "recipient_preview",
            "legacy_intermediary_absent",
            "decision_post_count",
            "consumed_pending",
            "product_login_started",
            "product_authenticated",
            "rejected_anonymous",
            "membership_absent",
            "screenshot",
        }
        or evidence["browser"] != "chromium"
        or evidence["decision"] != decision
        or evidence["entry_form"] is not True
        or evidence["recipient_preview"] is not True
        or evidence["legacy_intermediary_absent"] is not True
        or evidence["decision_post_count"] != 1
        or evidence["consumed_pending"] is not True
        or evidence["product_login_started"] is not (decision == "accept")
        or evidence["product_authenticated"] is not (decision == "accept")
        or evidence["rejected_anonymous"] is not (decision == "reject")
        or evidence["membership_absent"] is not (decision == "reject")
        or evidence["screenshot"] != str(screenshot)
        or not screenshot.is_file()
        or screenshot.stat().st_size == 0
        or observed.count(("POST", owner_path)) != before + 1
    ):
        raise SmokeError("Chromium invitation evidence or owner relay drift")
    return ChromiumInvitationEvidence(
        decision=decision,
        owner_post_count=1,
        consumed_pending=True,
        product_login_started=decision == "accept",
        product_authenticated=decision == "accept",
        rejected_anonymous=decision == "reject",
        membership_absent=decision == "reject",
    )


def configure_isolated_chromium_web(next_root: Path, tls_port: int) -> None:
    """Make only the test-owned Next copy reflect its reserved public TLS port."""
    if not 1 <= tls_port <= 65_535:
        raise SmokeError("Chromium Web TLS port invalid")
    server = next_root / "server.cjs"
    source = server.read_text()
    marker = "hostname: host, port: 443"
    if source.count(marker) != 1 or source.count("dev: true") != 1:
        raise SmokeError("isolated Chromium Next origin fixture drift")
    server.write_text(
        source.replace("dev: true", "dev: false").replace(
            marker, f"hostname: host, port: {tls_port}"
        )
    )
    config = next_root / "next.config.ts"
    config_source = config.read_text()
    output_marker = '  output: "standalone",\n'
    if config_source.count(output_marker) != 1:
        raise SmokeError("isolated Chromium Next output fixture drift")
    config.write_text(config_source.replace(output_marker, ""))


def invitation_path(invitation_id: str) -> str:
    if UUID.fullmatch(invitation_id) is None:
        raise SmokeError("IAM invitation identity invalid")
    return f"{PAGE_PATH}?id={invitation_id}"


def invitation_mail_path(message: bytes, web_origin: str, invitation_id: str) -> str:
    """Accept only the exact delivered owner link, never construct one as proof."""
    path = invitation_path(invitation_id)
    try:
        parsed = BytesParser(policy=policy.default).parsebytes(message)
        if parsed.get("Subject") != "Tenant invitation":
            raise SmokeError("IAM invitation mail subject invalid")
        body = parsed.get_body(preferencelist=("plain",))
        content = body.get_content() if body is not None else None
        if (
            not isinstance(content, str)
            or len(content) > 8192
            or content.strip() != web_origin + path
        ):
            raise SmokeError("IAM invitation mail link invalid")
        link = urlsplit(content.strip())
        if link.geturl() != web_origin + path or link.fragment:
            raise SmokeError("IAM invitation mail URL invalid")
    except (UnicodeError, ValueError, TypeError):
        raise SmokeError("IAM invitation mail malformed") from None
    return path


def delivered_invitation(
    mailbox: object, recipient: str, web_origin: str, invitation_id: str
) -> str:
    """Fixture actor creation may send one verification mail before its invite."""
    for _ in range(3):
        message = mailbox.for_recipient(recipient)
        try:
            subject = (
                BytesParser(policy=policy.default)
                .parsebytes(message, headersonly=True)
                .get("Subject")
            )
        except (UnicodeError, ValueError, TypeError):
            raise SmokeError("IAM invitation mail malformed") from None
        if subject == "Verify your email":
            continue
        if subject != "Tenant invitation":
            raise SmokeError(f"IAM invitation mail unexpected subject: {subject!r}")
        return invitation_mail_path(message, web_origin, invitation_id)
    raise SmokeError("IAM invitation mail absent")


def invitation_verification_path(
    message: bytes, web_origin: str, invitation_link: str
) -> str:
    """Require an actual verification mail returning to this exact invitation."""
    try:
        parsed = BytesParser(policy=policy.default).parsebytes(message)
        body = parsed.get_body(preferencelist=("plain",))
        content = body.get_content().strip() if body is not None else None
        if (
            parsed.get("Subject") != "Verify your email"
            or not isinstance(content, str)
            or len(content) > 8192
        ):
            raise SmokeError("invitation verification mail invalid")
        target = urlsplit(content)
        if (
            target.scheme != "https"
            or f"{target.scheme}://{target.netloc}" != web_origin
            or target.path != "/iam/verify-email"
            or target.fragment
            or not target.query
            or target.geturl() != content
        ):
            raise SmokeError("invitation verification link invalid")
        pairs = parse_qsl(target.query, keep_blank_values=True, strict_parsing=True)
        if (
            len(pairs) != 2
            or {key for key, _ in pairs} != {"token", "callbackURL"}
            or dict(pairs)["callbackURL"] != invitation_link
            or re.fullmatch(r"[A-Za-z0-9._-]{24,4096}", dict(pairs)["token"]) is None
        ):
            raise SmokeError("invitation verification callback invalid")
    except (UnicodeError, ValueError, TypeError):
        raise SmokeError("invitation verification mail malformed") from None
    return target.path + "?" + target.query


def request_invitation(
    process: subprocess.Popen[bytes], reader: object, email: str
) -> str:
    if len(email) > 320 or EMAIL.fullmatch(email) is None or email.lower() != email:
        raise SmokeError("IAM invitation recipient invalid")
    if process.poll() is not None or process.stdin is None:
        raise SmokeError("IAM invitation host unavailable")
    try:
        process.stdin.write(
            (json.dumps({"command": "invite-verified", "email": email}) + "\n").encode()
        )
        process.stdin.flush()
    except (BrokenPipeError, OSError):
        raise SmokeError("IAM invitation command failed") from None
    record = reader.record(timeout=30)
    if (
        not isinstance(record, dict)
        or set(record) != {"kind", "invitation_id"}
        or record["kind"] != "invitation"
    ):
        raise SmokeError("IAM invitation protocol invalid")
    return invitation_path(record["invitation_id"]).partition("?id=")[2]


class _SignInForm(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_form = False
        self.decision: str | None = None
        self.token: str | None = None
        self.action: str | None = None
        self.found = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "form":
            self.in_form = True
            self.decision = None
            self.token = None
            self.action = values.get("action")
        elif tag == "input" and self.in_form:
            if values.get("name") == "decision":
                self.decision = values.get("value")
            elif values.get("name") == "csrf_token":
                self.token = values.get("value")

    def handle_endtag(self, tag: str) -> None:
        if tag == "form" and self.in_form:
            if self.decision == "sign-in" and self.token and self.action:
                self.found += 1
                self.sign_in_action = self.action
                self.sign_in_token = self.token
            self.in_form = False


class _SignUpForm(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_form = False
        self.forms: list[tuple[str | None, str | None, dict[str, str | None]]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "form":
            if self.in_form:
                raise SmokeError("nested invitation registration form")
            self.in_form = True
            self.action = (
                values.get("action") if values.get("method") == "post" else None
            )
            self.inputs: dict[str, str | None] = {}
        elif tag == "input" and self.in_form:
            name = values.get("name")
            if name in {"decision", "csrf_token", "name", "email", "password"}:
                if name in self.inputs or "disabled" in values or "hidden" in values:
                    raise SmokeError(
                        "duplicate or hidden invitation registration input"
                    )
                self.inputs[name] = (
                    values.get("value")
                    if name in {"decision", "csrf_token"}
                    else values.get("type")
                )

    def handle_endtag(self, tag: str) -> None:
        if tag == "form" and self.in_form:
            self.forms.append((self.action, self.inputs.get("decision"), self.inputs))
            self.in_form = False


def sign_up_form(page: product.BrowserResponse, path: str) -> str:
    if (
        page.status != 200
        or page.headers.get("content-type", "").split(";", 1)[0] != "text/html"
        or "no-store" not in page.headers.get("cache-control", "")
        or page.headers.get("referrer-policy") != "same-origin"
    ):
        raise SmokeError("independent invitation registration form unavailable")
    try:
        parser = _SignUpForm()
        parser.feed(page.body.decode("utf-8", "strict"))
    except UnicodeError:
        raise SmokeError("invitation registration form encoding invalid") from None
    matches = [entry for entry in parser.forms if entry[1] == "sign-up"]
    if len(matches) != 1 or parser.in_form:
        raise SmokeError("invitation registration form missing or duplicated")
    action, _, inputs = matches[0]
    token = inputs.get("csrf_token")
    if (
        action != path
        or not isinstance(token, str)
        or re.fullmatch(r"[A-Za-z0-9_-]{43}", token) is None
        or inputs.get("name") != "text"
        or inputs.get("email") != "email"
        or inputs.get("password") != "password"
    ):
        raise SmokeError("invitation registration form invalid")
    return token


class _DecisionForm(HTMLParser):
    def __init__(self, decision: str) -> None:
        super().__init__()
        self.decision = decision
        self.in_form = False
        self.forms: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "form":
            self.in_form = True
            self.action = values.get("action")
            self.current_decision = None
            self.token = None
        elif tag == "input" and self.in_form:
            if values.get("name") == "decision":
                self.current_decision = values.get("value")
            elif values.get("name") == "csrf_token":
                self.token = values.get("value")

    def handle_endtag(self, tag: str) -> None:
        if tag == "form" and self.in_form:
            if self.current_decision == self.decision and self.action and self.token:
                self.forms.append((self.action, self.token))
            self.in_form = False


def decision_form(page: product.BrowserResponse, path: str, decision: str) -> str:
    if decision not in {"accept", "reject"} or page.status != 200:
        raise SmokeError("invitation decision page invalid")
    try:
        parser = _DecisionForm(decision)
        parser.feed(page.body.decode("utf-8", "strict"))
    except UnicodeError:
        raise SmokeError("invitation decision form encoding invalid") from None
    if (
        len(parser.forms) != 1
        or parser.forms[0][0] != path
        or not re.fullmatch(r"[A-Za-z0-9_-]{43}", parser.forms[0][1])
    ):
        raise SmokeError("invitation decision form missing or duplicated")
    return parser.forms[0][1]


def sign_in_form(page: product.BrowserResponse, path: str) -> tuple[str, str]:
    if (
        page.status != 200
        or page.headers.get("content-type", "").split(";", 1)[0] != "text/html"
    ):
        raise SmokeError("independent invitation form unavailable")
    if (
        "no-store" not in page.headers.get("cache-control", "")
        or page.headers.get("referrer-policy") != "same-origin"
    ):
        raise SmokeError("invitation form privacy headers missing")
    try:
        parser = _SignInForm()
        parser.feed(page.body.decode("utf-8", "strict"))
    except UnicodeError:
        raise SmokeError("invitation form encoding invalid") from None
    if parser.found != 1 or parser.sign_in_action != path:
        raise SmokeError("invitation sign-in form invalid")
    if b'name="password"' not in page.body or b'name="email"' not in page.body:
        raise SmokeError("invitation credential inputs absent")
    if (
        b"\xe8\xbf\x9e\xe6\x8e\xa5\xe4\xb8\xad" in page.body
        or b"\xe9\x87\x8d\xe8\xaf\x95\xe7\x99\xbb\xe5\xbd\x95" in page.body
    ):
        raise SmokeError("legacy visible intermediary remains")
    return parser.sign_in_action, parser.sign_in_token


def existing_account_entry(
    port: int,
    web_origin: str,
    path: str,
    email: str,
    password: str,
    tenant_id: str,
    credentials: product.previous.CredentialRegistry,
    observed: list[tuple[str, str]],
    decision: str,
    jar: product.BrowserCookies | None = None,
) -> product.BrowserCookies:
    jar = jar or product.BrowserCookies(credentials.add)

    def get() -> product.BrowserResponse:
        response = product.https_browser(
            port, path, web_origin, cookie=jar.header(PAGE_PATH)
        )
        jar.update(PAGE_PATH, response.set_cookies)
        return response

    first = get()
    form_action, csrf = sign_in_form(first, path)
    credentials.add(csrf)
    if jar.has_usable_session() or b"kokoro_product_session" in first.body:
        raise SmokeError("invitation entry created Product Session")
    signin_before = observed.count(("POST", "/iam/sign-in/email"))
    response = product.https_browser(
        port,
        form_action,
        web_origin,
        method="POST",
        form={
            "decision": "sign-in",
            "csrf_token": csrf,
            "email": email,
            "password": password,
        },
        cookie=jar.header(PAGE_PATH),
        origin=web_origin,
    )
    jar.update(PAGE_PATH, response.set_cookies)
    if response.status != 303 or response.location() != path or response.body:
        raise SmokeError("invitation issuer sign-in did not return to same page")
    if observed.count(("POST", "/iam/sign-in/email")) != signin_before + 1:
        raise SmokeError("invitation sign-in bypassed BFF owner relay")
    if any(
        cookie.startswith("kokoro_product_session=") for cookie in response.set_cookies
    ):
        raise SmokeError("invitation sign-in created Product Session")
    context_before = observed.count(
        (
            "GET",
            f"/iam/v1/tenants/{tenant_id}/invitations/{path.rsplit('=', 1)[-1]}/context",
        )
    )
    preview = get()
    context_after = observed.count(
        (
            "GET",
            f"/iam/v1/tenants/{tenant_id}/invitations/{path.rsplit('=', 1)[-1]}/context",
        )
    )
    if context_after != context_before + 1 or preview.status != 200:
        raise SmokeError("recipient invitation context not loaded through BFF")
    if b'name="password"' in preview.body or b"kokoro_product_session" in preview.body:
        raise SmokeError("invitation preview leaked credential or Product Session")
    if (
        "no-store" not in preview.headers.get("cache-control", "")
        or preview.headers.get("referrer-policy") != "same-origin"
    ):
        raise SmokeError("invitation preview privacy headers missing")
    if b"member" not in preview.body:
        raise SmokeError("recipient invitation role not visible")
    proof = decision_form(preview, path, decision)
    credentials.add(proof)
    owner_path = (
        f"/iam/v1/tenants/{tenant_id}/invitations/{path.rsplit('=', 1)[-1]}/{decision}"
    )
    before_write = observed.count(("POST", owner_path))
    decided = product.https_browser(
        port,
        path,
        web_origin,
        method="POST",
        form={"decision": decision, "csrf_token": proof},
        cookie=jar.header(PAGE_PATH),
        origin=web_origin,
    )
    jar.update(PAGE_PATH, decided.set_cookies)
    if observed.count(("POST", owner_path)) != before_write + 1:
        raise SmokeError("invitation decision bypassed BFF owner relay")
    if decision == "accept":
        if (
            decided.status != 303
            or decided.headers.get("location") != "/login"
            or decided.body
        ):
            raise SmokeError("accepted invitation did not start Product login")
        login = product.https_browser(
            port, "/login", web_origin, cookie=jar.header("/login")
        )
        if login.status != 302 or not product.browser_target(
            login.location(), web_origin
        ).startswith("/iam/oauth2/authorize?"):
            raise SmokeError("accepted invitation Product login entrance invalid")
    elif (
        decided.status != 200
        or decided.headers.get("location") is not None
        or "已拒绝邀请" not in decided.body.decode("utf-8", "strict")
    ):
        raise SmokeError("rejected invitation completion invalid")
    replay = product.https_browser(
        port,
        path,
        web_origin,
        method="POST",
        form={"decision": decision, "csrf_token": proof},
        cookie=jar.header(PAGE_PATH),
        origin=web_origin,
    )
    if replay.status != 403 or observed.count(("POST", owner_path)) != before_write + 1:
        raise SmokeError("invitation decision CSRF replay reached owner")
    context_path = (
        f"/iam/v1/tenants/{tenant_id}/invitations/{path.rsplit('=', 1)[-1]}/context"
    )
    context_reads = observed.count(("GET", context_path))
    terminal = get()
    if (
        terminal.status != 404
        or observed.count(("GET", context_path)) != context_reads + 1
    ):
        raise SmokeError("consumed invitation remained visible as pending")
    if decision == "reject":
        product.require_session_projection(
            product.https_browser(
                port,
                "/api/auth/session",
                web_origin,
                cookie=jar.header("/api/auth/session"),
            ),
            authenticated=False,
        )
    return jar


def require_rejected_membership_absent(
    iam_base_url: str,
    web_origin: str,
    jar: product.BrowserCookies,
    tenant_id: str,
    existing_tenant_id: str | None,
) -> None:
    """Read the issuer's own organization list; never infer membership from UI state."""
    parsed = urlsplit(iam_base_url)
    if (
        parsed.scheme != "http"
        or parsed.hostname not in {"127.0.0.1", "localhost"}
        or parsed.port is None
    ):
        raise SmokeError("IAM membership probe origin invalid")
    cookie = jar.header("/iam/organization/list")
    if not any(
        part.startswith(
            ("kokoro-issuer.session_token=", "__Secure-kokoro-issuer.session_token=")
        )
        for part in cookie.split("; ")
    ):
        raise SmokeError("IAM membership probe issuer session absent")
    connection = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=10)
    try:
        connection.request(
            "GET",
            "/iam/organization/list",
            headers={
                "Host": parsed.netloc,
                "Origin": web_origin,
                "Accept": "application/json",
                "Cookie": cookie,
            },
        )
        response = connection.getresponse()
        body = response.read(65_537)
        if (
            response.status != 200
            or len(body) > 65_536
            or response.getheader("content-type", "").split(";", 1)[0]
            != "application/json"
        ):
            raise SmokeError(
                f"IAM membership probe HTTP {response.status} or invalid envelope"
            )
    except (OSError, http.client.HTTPException):
        raise SmokeError("IAM membership probe request failed") from None
    finally:
        connection.close()
    try:
        organizations = json.loads(body)
    except (ValueError, UnicodeError):
        raise SmokeError("IAM membership probe body malformed") from None
    if not isinstance(organizations, list) or any(
        not isinstance(item, dict)
        or not isinstance(item.get("id"), str)
        or not item["id"]
        for item in organizations
    ):
        raise SmokeError("IAM membership probe organization list invalid")
    ids = {item["id"] for item in organizations}
    if tenant_id in ids or (
        existing_tenant_id is not None and existing_tenant_id not in ids
    ):
        raise SmokeError("rejected invitation changed IAM membership")


def new_account_registration(
    port: int,
    web_origin: str,
    path: str,
    email: str,
    password: str,
    mailbox: product.first_login.SmtpMailbox,
    credentials: product.previous.CredentialRegistry,
    observed: list[tuple[str, str]],
) -> product.BrowserCookies:
    """Sign up on Web, reject unverified login, then follow real SMTP verification."""
    jar = product.BrowserCookies(credentials.add)

    def get() -> product.BrowserResponse:
        response = product.https_browser(
            port, path, web_origin, cookie=jar.header(PAGE_PATH)
        )
        jar.update(PAGE_PATH, response.set_cookies)
        return response

    registration = get()
    proof = sign_up_form(registration, path)
    credentials.add(proof)
    if jar.has_usable_session() or b"kokoro_product_session" in registration.body:
        raise SmokeError("invitation registration entry created Product Session")
    before_signup = observed.count(("POST", "/iam/sign-up/email"))
    created = product.https_browser(
        port,
        path,
        web_origin,
        method="POST",
        form={
            "decision": "sign-up",
            "csrf_token": proof,
            "name": "New invited recipient",
            "email": email,
            "password": password,
        },
        cookie=jar.header(PAGE_PATH),
        origin=web_origin,
    )
    jar.update(PAGE_PATH, created.set_cookies)
    if (
        observed.count(("POST", "/iam/sign-up/email")) != before_signup + 1
        or created.status != 200
        or "请查收邮件" not in created.body.decode("utf-8", "strict")
        or created.headers.get("location") is not None
        or jar.has_usable_session()
        or any(
            "issuer.session_token=" in cookie
            or cookie.startswith("kokoro_product_session=")
            for cookie in created.set_cookies
        )
    ):
        raise SmokeError(
            "invitation Web registration or pending-verification state invalid"
        )
    replay = product.https_browser(
        port,
        path,
        web_origin,
        method="POST",
        form={
            "decision": "sign-up",
            "csrf_token": proof,
            "name": "New invited recipient",
            "email": email,
            "password": password,
        },
        cookie=jar.header(PAGE_PATH),
        origin=web_origin,
    )
    if (
        replay.status != 403
        or observed.count(("POST", "/iam/sign-up/email")) != before_signup + 1
    ):
        raise SmokeError("invitation registration CSRF replay reached owner")

    sign_in = get()
    sign_in_path, sign_in_proof = sign_in_form(sign_in, path)
    credentials.add(sign_in_proof)
    before_signin = observed.count(("POST", "/iam/sign-in/email"))
    denied = product.https_browser(
        port,
        sign_in_path,
        web_origin,
        method="POST",
        form={
            "decision": "sign-in",
            "csrf_token": sign_in_proof,
            "email": email,
            "password": password,
        },
        cookie=jar.header(PAGE_PATH),
        origin=web_origin,
    )
    jar.update(PAGE_PATH, denied.set_cookies)
    if (
        observed.count(("POST", "/iam/sign-in/email")) != before_signin + 1
        or denied.status != 200
        or b'role="alert"' not in denied.body
        or denied.headers.get("location") is not None
        or jar.has_usable_session()
        or any(
            "issuer.session_token=" in cookie
            or cookie.startswith("kokoro_product_session=")
            for cookie in denied.set_cookies
        )
    ):
        raise SmokeError("unverified invitation recipient admitted")

    verification = invitation_verification_path(
        mailbox.for_recipient(email), web_origin, web_origin + path
    )
    product.remember_sensitive_query(verification, credentials)
    before_verify = observed.count(("GET", "/iam/verify-email"))
    verified = product.https_browser(port, verification, web_origin)
    product.first_login.require_verified_relay(verified, web_origin + path)
    if observed.count(("GET", "/iam/verify-email")) != before_verify + 1:
        raise SmokeError("invitation verification bypassed BFF owner relay")
    return jar


def main(argv: list[str] | None = None) -> int:
    import argparse

    selector = argparse.ArgumentParser(add_help=False)
    selector.add_argument("--decision", choices=("accept", "reject"), default="accept")
    selector.add_argument("--account", choices=("existing", "new"), default="existing")
    selector.add_argument("--browser", choices=("http", "chromium"), default="http")
    selected, remaining = selector.parse_known_args(argv)
    if selected.browser == "chromium" and selected.account != "existing":
        selector.error("Chromium A covers only existing invitation recipients")
    args = product.parse_args(remaining)
    for repo, sha, label in (
        (product.IAM, args.expected_iam_sha, "apps/kokoro-iam"),
        (product.BFF, args.expected_bff_sha, "apps/kokoro-bff"),
        (product.WEB, args.expected_web_sha, "apps/kokoro-app"),
    ):
        product.session.verify_source(repo, sha, label)
    run_id = secrets.token_hex(12)
    iam_resource_id = str(uuid4())
    iam_identity = product.named_iam_identity(iam_resource_id)
    iam_owner_token = secrets.token_hex(16)
    tls_reservation = (
        chromium_smoke.OwnedTlsReservation.reserve()
        if selected.browser == "chromium"
        else None
    )
    web_origin = f"https://web-{run_id}.example.test"
    if tls_reservation is not None:
        web_origin += f":{tls_reservation.port}"
    host_name = urlsplit(web_origin).hostname
    resources = product.runtime.OwnedResources(
        args.postgres_admin_url, args.redis_url, run_id
    )
    iam_env = product.session.node_environment(
        args.iam_node_bin, "v24.20.0", args.bff_node_bin.parent
    )
    bff_env = product.session.node_environment(
        args.bff_node_bin, "v22.22.2", args.bff_node_bin.parent
    )
    web_env = product.session.node_environment(
        args.web_node_bin, "v22.22.2", args.web_node_bin.parent
    )
    credentials = product.previous.CredentialRegistry(
        args.postgres_admin_url, args.redis_url
    )
    credentials.add(iam_owner_token)
    for raw in (args.postgres_admin_url, args.redis_url):
        password = unquote(urlsplit(raw).password or "")
        if len(password) >= 12:
            credentials.add(password)
    processes: list[subprocess.Popen[bytes]] = []
    proxies: list[product.Proxy | chromium_smoke.OwnedBrowserTlsProxy] = []
    reader = None
    mailbox = None
    iam_attempted = False
    before_web: set[str] | None = None
    failures: list[str] = []
    stage = "preflight"
    with tempfile.TemporaryDirectory(
        prefix="kokoro-invitation-", dir=product.ROOT.parent
    ) as temp:
        directory = Path(temp)
        log_path = directory / "process.log"
        with log_path.open("w+b") as log:
            try:
                stage = "BFF build"
                if (
                    product.runtime.run_owned_command(
                        [str(args.bff_node_bin.parent / "corepack"), "pnpm", "build"],
                        cwd=product.BFF,
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
                before_web = product.web_redis_keys(
                    args.redis_url, web_origin, resources
                )
                stage = "BFF database"
                db_url = product.bff_owner_database_url(
                    resources.create_database("bff")
                )
                bff_env.update(
                    {
                        "KOKORO_BFF_POSTGRES_URL": db_url,
                        "KOKORO_BFF_REDIS_URL": args.redis_url,
                    }
                )
                product.runtime.install_schema(
                    "bff", product.BFF, str(args.bff_node_bin.parent), bff_env, log
                )
                stage = "IAM host"
                mailbox = product.first_login.SmtpMailbox()
                if product.iam_owned_inventory(resources, iam_identity) != (
                    set(),
                    set(),
                ):
                    raise SmokeError("IAM named resources already exist")
                iam_env.update(
                    {
                        "IAM_TEST_ADMIN_URL": args.postgres_admin_url,
                        "IAM_TEST_REDIS_URL": args.redis_url,
                        "IAM_TEST_WEB_ORIGIN": web_origin,
                        "IAM_TEST_RESOURCE_ID": iam_resource_id,
                        "IAM_TEST_RESOURCE_OWNER_TOKEN": iam_owner_token,
                        "IAM_TEST_SMTP_URL": mailbox.url,
                        "NODE_ENV": "test",
                    }
                )
                credentials.add(iam_owner_token)
                iam_attempted = True
                iam = subprocess.Popen(
                    [str(args.iam_node_bin), "--import", "tsx", str(product.HOST)],
                    cwd=product.IAM,
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
                reader = product.session.ProtocolReader(iam.stdout.fileno())
                ready = product.validate_ready(reader.record(), web_origin)
                if (ready.database_name, ready.redis_prefix) != (
                    iam_identity.database_name,
                    iam_identity.redis_prefix,
                ):
                    raise SmokeError("IAM named identity drift")
                credentials.add(ready.client_secret, ready.password)
                stage = f"{selected.account} recipient invitation"
                if selected.account == "existing":
                    actors = product.request_actor_matrix(
                        iam, reader, ready, credentials
                    )
                    email = actors.other_tenant_owner.email
                    password = actors.other_tenant_owner.password
                else:
                    email = f"new-{secrets.token_hex(8)}@example.test"
                    password = secrets.token_urlsafe(32)
                    credentials.add(password)
                invite_id = request_invitation(iam, reader, email)
                credentials.add(invite_id)
                path = delivered_invitation(mailbox, email, web_origin, invite_id)
                stage = "BFF startup"
                secret = secrets.token_urlsafe(32)
                credentials.add(secret)
                bff_port = product.runtime.free_port()
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
                bff = product.runtime.start_process(
                    args.bff_node_bin, product.BFF, bff_env, log
                )
                processes.append(bff)
                product.runtime.wait_ready(f"http://127.0.0.1:{bff_port}", bff)
                bff_proxy = product.Proxy(bff_port, credentials=credentials)
                proxies.append(bff_proxy)
                stage = "Web HTTPS startup"
                next_root = product.isolated_next(directory)
                if tls_reservation is not None:
                    configure_isolated_chromium_web(next_root, tls_reservation.port)
                next_port = product.runtime.free_port()
                web_env.update(
                    {
                        "KOKORO_WEB_ORIGIN": web_origin,
                        "KOKORO_DOMAIN": host_name,
                        "KOKORO_BFF_BASE_URL": f"http://127.0.0.1:{bff_proxy.server_port}",
                        "KOKORO_INTERNAL_SECRET_WEB_BFF": secret,
                        "KOKORO_WEB_REDIS_URL": args.redis_url,
                        "KOKORO_TENANT_ID": ready.tenant_id,
                        "KOKORO_OIDC_CLIENT_ID": ready.client_id,
                        "KOKORO_OIDC_CLIENT_SECRET": ready.client_secret,
                        "KOKORO_WEB_AUTH_SECRET": secrets.token_hex(32),
                        "NEXTAUTH_URL": web_origin + "/api/auth",
                    }
                )
                credentials.add(web_env["KOKORO_WEB_AUTH_SECRET"])
                if tls_reservation is not None:
                    stage = "test-owned Chromium Web production build"
                    if (
                        product.runtime.run_owned_command(
                            [
                                str(args.web_node_bin),
                                str(next_root / "node_modules/next/dist/bin/next"),
                                "build",
                            ],
                            cwd=next_root,
                            env=web_env,
                            log=log,
                            timeout=180,
                        )
                        != 0
                    ):
                        raise SmokeError("test-owned Chromium Web build failed")
                    web_env["NODE_ENV"] = "test"
                    stage = "Web HTTPS startup"
                web = subprocess.Popen(
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
                processes.append(web)
                certificate = product.certificate(directory, host_name)
                if tls_reservation is None:
                    web_proxy = product.Proxy(next_port, host_name, certificate)
                else:
                    web_proxy = chromium_smoke.OwnedBrowserTlsProxy.from_reservation(
                        tls_reservation,
                        next_port,
                        host_name,
                        urlsplit(web_origin).netloc,
                        certificate,
                    )
                proxies.append(web_proxy)
                stage = "Web HTTPS origin"
                deadline = time.monotonic() + 30
                while True:
                    try:
                        fixture = product.https_browser(
                            web_proxy.server_port, "/api/fixture-origin", web_origin
                        )
                        if fixture.status == 200:
                            break
                    except SmokeError:
                        pass
                    if time.monotonic() > deadline or web.poll() is not None:
                        raise SmokeError("Web HTTPS fixture unavailable")
                    time.sleep(0.1)
                if json.loads(fixture.body) != {
                    "origin": web_origin,
                    "host": urlsplit(web_origin).netloc,
                    "proto": "https",
                }:
                    raise SmokeError("Web HTTPS origin mismatch")
                browser_jar = None
                if selected.account == "new":
                    stage = "new recipient Web registration and verification"
                    browser_jar = new_account_registration(
                        web_proxy.server_port,
                        web_origin,
                        path,
                        email,
                        password,
                        mailbox,
                        credentials,
                        bff_proxy.observed,
                    )
                stage = f"{selected.account} recipient browser decision"
                if selected.browser == "chromium":
                    chromium_invitation(
                        node_bin=args.web_node_bin,
                        web_origin=web_origin,
                        path=path,
                        email=email,
                        password=password,
                        decision=selected.decision,
                        screenshot=directory / "invitation-entry.png",
                        tenant_id=ready.tenant_id,
                        iam_base_url=ready.base_url,
                        existing_tenant_id=actors.other_tenant_owner.tenant_id,
                        observed=bff_proxy.observed,
                    )
                else:
                    completed_jar = existing_account_entry(
                        web_proxy.server_port,
                        web_origin,
                        path,
                        email,
                        password,
                        ready.tenant_id,
                        credentials,
                        bff_proxy.observed,
                        selected.decision,
                        browser_jar,
                    )
                    if selected.decision == "reject":
                        stage = "rejected recipient IAM membership"
                        require_rejected_membership_absent(
                            ready.base_url,
                            web_origin,
                            completed_jar,
                            ready.tenant_id,
                            actors.other_tenant_owner.tenant_id
                            if selected.account == "existing"
                            else None,
                        )
                if selected.decision == "accept" and selected.browser == "http":
                    stage = "accepted recipient Product login"
                    from dataclasses import replace

                    product.run_browser(
                        web_proxy.server_port,
                        web_origin,
                        replace(ready, email=email, password=password),
                        bff_proxy.observed,
                        credentials,
                    )
            except (SmokeError, product.first_login.FirstLoginError) as error:
                failures.append(f"{stage}: {error}")
            except Exception:  # noqa: BLE001 - sanitize failures and continue owned-resource cleanup
                failures.append(stage)
            finally:
                for proxy in reversed(proxies):
                    try:
                        proxy.close()
                    except Exception:  # noqa: BLE001 - sanitize failures and continue owned-resource cleanup
                        failures.append("owned proxy cleanup")
                if tls_reservation is not None:
                    tls_reservation.close()
                processes_stopped = True
                for process in reversed(processes):
                    try:
                        product.runtime.stop_owned_process(process)
                    except Exception:  # noqa: BLE001 - sanitize failures and continue owned-resource cleanup
                        processes_stopped = False
                        failures.append("owned process cleanup")
                if reader is not None:
                    try:
                        reader.close()
                    except Exception:  # noqa: BLE001 - sanitize failures and continue owned-resource cleanup
                        failures.append("IAM protocol cleanup")
                if mailbox is not None:
                    try:
                        mailbox.close()
                    except Exception:  # noqa: BLE001 - sanitize failures and continue owned-resource cleanup
                        failures.append("owned SMTP cleanup")
                if before_web is not None:
                    try:
                        extras = (
                            product.web_redis_keys(
                                args.redis_url, web_origin, resources
                            )
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
                            product.web_redis_keys(
                                args.redis_url, web_origin, resources
                            )
                            != before_web
                        ):
                            failures.append("Web Redis cleanup")
                    except Exception:  # noqa: BLE001 - sanitize failures and continue owned-resource cleanup
                        failures.append("Web Redis cleanup")
                try:
                    resources.cleanup()
                    resources.verify_clean()
                except Exception:  # noqa: BLE001 - sanitize failures and continue owned-resource cleanup
                    failures.append("BFF resource cleanup")
                if iam_attempted and processes_stopped:
                    try:
                        product.reconcile_iam_identity(
                            resources, iam_identity, iam_owner_token
                        )
                    except Exception:  # noqa: BLE001 - sanitize failures and continue owned-resource cleanup
                        failures.append("IAM resource cleanup")
                elif iam_attempted:
                    failures.append(
                        "IAM resource cleanup deferred: process still running"
                    )
                try:
                    log.flush()
                    product.previous.assert_log_clean(log_path, credentials.values())
                except Exception:  # noqa: BLE001 - sanitize failures and continue owned-resource cleanup
                    failures.append("credential log scan")
    if failures:
        raise SmokeError("; ".join(sorted(set(failures))) + " failed")
    print(
        json.dumps(
            {
                "status": "passed",
                "flow": f"{selected.account}_email_invitation_decision",
                "smtp_invitation": "verified",
                "registration_verification": "verified"
                if selected.account == "new"
                else "not_run",
                "web_bff_iam_context": "invited_recipient_positive",
                "recipient_isolation": "not_run",
                "decision": selected.decision,
                "product_login": "verified"
                if selected.decision == "accept"
                else "not_attempted",
                "chromium": "verified" if selected.browser == "chromium" else "not_run",
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
        product.runtime.SmokeError,
        product.session.SmokeError,
    ) as error:
        print(f"Invitation smoke: {error}", file=sys.stderr)
        sys.exit(1)
