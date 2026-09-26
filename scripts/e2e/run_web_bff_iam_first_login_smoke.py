"""Isolated real-SMTP first-login slice for the Web/BFF/IAM HTTPS smoke.

Registration and fixed-tenant invitation setup are test-only IAM loopback calls; the verification
link and subsequent OIDC/Product login traverse the real Web/BFF/IAM chain.
"""

from __future__ import annotations

from dataclasses import replace
from email import policy
from email.parser import BytesParser
import http.client
from html.parser import HTMLParser
import json
from queue import Empty, Queue
import re
import secrets
import socketserver
from threading import Thread
import time
from typing import Callable
from urllib.parse import parse_qs, quote, urlsplit

import run_web_bff_iam_oidc_smoke as web_smoke


class FirstLoginError(RuntimeError):
    """A sanitized first-login failure without credential-bearing URLs."""


class _CredentialForm(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_form = False
        self.inputs: dict[str, str] = {}

    def handle_starttag(self, tag, attrs) -> None:
        if tag == "form":
            self.in_form = True
        if tag != "input" or not self.in_form:
            return
        values = dict(attrs)
        name = values.get("name")
        if name not in {"email", "password"}:
            return
        if name in self.inputs or "hidden" in values or "disabled" in values:
            raise FirstLoginError("formal credential input hidden or duplicated")
        self.inputs[name] = values.get("type", "")

    def handle_endtag(self, tag) -> None:
        if tag == "form":
            self.in_form = False


def require_credential_inputs(document: bytes) -> None:
    try:
        page = _CredentialForm()
        page.feed(document.decode("utf-8", "strict"))
    except UnicodeError:
        raise FirstLoginError("formal credential form encoding invalid") from None
    if page.inputs != {"email": "email", "password": "password"}:
        raise FirstLoginError("formal credential inputs absent")


def has_cache_directive(value: str, directive: str) -> bool:
    return directive in {part.strip().lower() for part in value.split(",")}


def require_verified_relay(response, callback: str) -> None:
    if (
        response.status != 302
        or response.headers.get("location") != callback
        or not has_cache_directive(
            response.headers.get("cache-control", ""), "no-store"
        )
        or response.headers.get("referrer-policy") != "no-referrer"
        or response.set_cookies
    ):
        raise FirstLoginError("Web/BFF/IAM verification relay failed")


class _SmtpHandler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        self.connection.settimeout(10)
        self.wfile.write(b"220 kokoro-test ESMTP ready\r\n")
        recipient = ""
        data: list[bytes] = []
        collecting = False
        while True:
            line = self.rfile.readline(8193)
            if not line or len(line) > 8192:
                return
            line = line.rstrip(b"\r\n")
            if collecting:
                if line == b".":
                    self.server.mailbox.put((recipient, b"\r\n".join(data)))  # type: ignore[attr-defined]
                    self.wfile.write(b"250 2.0.0 queued\r\n")
                    collecting = False
                    data = []
                else:
                    data.append(line[1:] if line.startswith(b"..") else line)
                    if sum(map(len, data)) > 65_536:
                        return
                continue
            upper = line.upper()
            if upper.startswith((b"EHLO ", b"HELO ")):
                self.wfile.write(b"250-kokoro-test\r\n250 PIPELINING\r\n")
            elif upper.startswith(b"MAIL FROM:"):
                recipient = ""
                self.wfile.write(b"250 2.1.0 sender ok\r\n")
            elif upper.startswith(b"RCPT TO:"):
                recipient = line[8:].decode("ascii", "strict").strip(" <>").lower()
                self.wfile.write(b"250 2.1.5 recipient ok\r\n")
            elif upper == b"DATA" and recipient:
                collecting = True
                self.wfile.write(b"354 end with dot\r\n")
            elif upper == b"QUIT":
                self.wfile.write(b"221 2.0.0 bye\r\n")
                return
            else:
                self.wfile.write(b"502 5.5.1 unsupported\r\n")


class _SmtpServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = False
    daemon_threads = True
    mailbox: Queue[tuple[str, bytes]]


class SmtpMailbox:
    def __init__(self) -> None:
        self.server = _SmtpServer(("127.0.0.1", 0), _SmtpHandler)
        self.server.mailbox = Queue()
        self.thread = Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    @property
    def url(self) -> str:
        return f"smtp://127.0.0.1:{self.server.server_address[1]}"

    def for_recipient(self, address: str) -> bytes:
        deadline = time.monotonic() + 12
        for _ in range(12):
            try:
                recipient, body = self.server.mailbox.get(
                    timeout=max(0.01, deadline - time.monotonic())
                )
            except Empty:
                raise FirstLoginError("verification email absent") from None
            if recipient == address:
                return body
        raise FirstLoginError("verification email recipient mismatch")

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)


def verification_path(message: bytes, web_origin: str) -> str:
    parsed = BytesParser(policy=policy.default).parsebytes(message)
    if parsed.get("Subject") != "Verify your email":
        raise FirstLoginError("verification subject invalid")
    body = parsed.get_body(preferencelist=("plain",))
    if body is None:
        raise FirstLoginError("verification text absent")
    content = body.get_content().strip()
    if not isinstance(content, str) or len(content) > 8192:
        raise FirstLoginError("verification URL invalid")
    target = urlsplit(content)
    if (
        content != target.geturl()
        or target.scheme != "https"
        or f"{target.scheme}://{target.netloc}" != web_origin
        or target.path != "/iam/verify-email"
        or target.fragment
        or not target.query
    ):
        raise FirstLoginError("verification URL origin or path invalid")
    query = parse_qs(target.query, keep_blank_values=True, strict_parsing=True)
    if set(query) != {"token", "callbackURL"} or any(
        len(v) != 1 for v in query.values()
    ):
        raise FirstLoginError("verification URL query invalid")
    if not re.fullmatch(r"[A-Za-z0-9._-]{24,4096}", query["token"][0]):
        raise FirstLoginError("verification token invalid")
    if query["callbackURL"][0] != web_origin + "/auth/sign-in":
        raise FirstLoginError("verification callback invalid")
    return target.path + "?" + target.query


def remember_secret_query(path: str, credentials, names: set[str]) -> None:
    query = parse_qs(urlsplit(path).query, keep_blank_values=True)
    for name in names:
        values = query.get(name, [])
        if len(values) != 1 or not values[0]:
            raise FirstLoginError("sensitive query field missing")
        credentials.add(values[0])


def _iam_json(
    base_url: str, path: str, body: dict, *, cookie: str = "", origin: str
) -> tuple[int, dict, list[str]]:
    base = urlsplit(base_url)
    if base.scheme != "http" or base.hostname != "127.0.0.1" or base.port is None:
        raise FirstLoginError("IAM loopback base invalid")
    connection = http.client.HTTPConnection("127.0.0.1", base.port, timeout=12)
    try:
        headers = {"content-type": "application/json", "origin": origin}
        if cookie:
            headers["cookie"] = cookie
        connection.request("POST", path, json.dumps(body).encode(), headers)
        response = connection.getresponse()
        payload = response.read(65_537)
        if len(payload) > 65_536:
            raise FirstLoginError("IAM response oversized")
        try:
            decoded = json.loads(payload) if payload else {}
        except (ValueError, UnicodeError):
            raise FirstLoginError("IAM response malformed") from None
        if not isinstance(decoded, dict):
            raise FirstLoginError("IAM response shape invalid")
        cookies = [
            value
            for name, value in response.getheaders()
            if name.lower() == "set-cookie"
        ]
        return response.status, decoded, cookies
    except (OSError, http.client.HTTPException):
        raise FirstLoginError("IAM loopback request failed") from None
    finally:
        connection.close()


def probe_formal_login_entry(
    web_port: int,
    web_origin: str,
    credentials,
    *,
    browser_request: Callable[..., web_smoke.BrowserResponse] = web_smoke.https_browser,
) -> None:
    """Require /login to lead straight to the issuer's real credential form."""
    jar = web_smoke.BrowserCookies(credentials.add)

    def get(path: str):
        response = browser_request(
            web_port,
            path,
            web_origin,
            cookie=jar.header(urlsplit(path).path),
        )
        jar.update(urlsplit(path).path, response.set_cookies)
        return response

    entrance = get("/login")
    if entrance.status != 302 or entrance.body:
        raise FirstLoginError(f"formal /login entry HTTP {entrance.status}")
    authorize = web_smoke.browser_target(entrance.location(), web_origin)
    if not authorize.startswith("/iam/oauth2/authorize?"):
        raise FirstLoginError("formal /login did not start OIDC")
    remember_secret_query(authorize, credentials, {"state", "nonce"})
    interaction = get(authorize)
    form_path = web_smoke.browser_target(
        web_smoke.navigation_location(interaction, "formal IAM authorize"), web_origin
    )
    if not form_path.startswith("/auth/sign-in?"):
        raise FirstLoginError("formal IAM credential form not reached")
    remember_secret_query(form_path, credentials, {"state", "nonce"})
    page = get(form_path)
    proof = web_smoke.form_inputs(page, form_path)
    credentials.add(proof.hidden["csrf_token"])
    require_credential_inputs(page.body)
    if page.body.find(b"Retry") >= 0 or page.body.find(b"Connecting") >= 0:
        raise FirstLoginError("legacy intermediate UI remains")


def enroll_in_fixed_tenant(
    ready,
    address: str,
    member_cookie: str,
    web_origin: str,
    credentials,
    *,
    invite: Callable[[str], str],
) -> None:
    """Use IAM's existing invitation lifecycle; the Product tenant never changes."""
    invitation_id = invite(address)
    if re.fullmatch(r"[A-Za-z0-9_-]{1,128}", invitation_id) is None:
        raise FirstLoginError("fixed tenant invitation identity invalid")
    credentials.add(invitation_id)
    status, accepted, cookies = _iam_json(
        ready.base_url,
        f"/iam/v1/tenants/{quote(ready.tenant_id, safe='')}/invitations/{quote(invitation_id, safe='')}/accept",
        {},
        cookie=member_cookie,
        origin=web_origin,
    )
    data = accepted.get("data")
    if (
        status != 200
        or not isinstance(data, dict)
        or set(data) != {"invitation_id", "member_id", "status"}
        or data.get("invitation_id") != invitation_id
        or data.get("status") != "accepted"
        or not isinstance(data.get("member_id"), str)
        or not data["member_id"]
    ):
        raise FirstLoginError(f"fixed tenant invitation accept failed HTTP {status}")
    for issued in cookies:
        credentials.add(issued.split(";", 1)[0].partition("=")[2])


def prepare_first_login(
    ready,
    mailbox: SmtpMailbox,
    web_origin: str,
    web_port: int,
    observed: list[tuple[str, str]],
    credentials,
    *,
    invite: Callable[[str], str],
):
    """Return a newly verified user/tenant identity for the existing OIDC browser flow."""
    address = f"first-{secrets.token_hex(8)}@example.test"
    password = secrets.token_urlsafe(32)
    credentials.add(password)
    callback = web_origin + "/auth/sign-in"
    status, _, cookies = _iam_json(
        ready.base_url,
        "/iam/sign-up/email",
        {
            "email": address,
            "name": "First login smoke",
            "password": password,
            "callbackURL": callback,
        },
        origin=web_origin,
    )
    if status != 200 or cookies:
        raise FirstLoginError(f"registration HTTP {status} or unexpected cookie")
    status, _, cookies = _iam_json(
        ready.base_url,
        "/iam/sign-in/email",
        {
            "email": address,
            "password": password,
        },
        origin=web_origin,
    )
    if status != 403 or cookies:
        raise FirstLoginError("unverified account admitted")
    path = verification_path(mailbox.for_recipient(address), web_origin)
    remember_secret_query(path, credentials, {"token"})
    before = observed.count(("GET", "/iam/verify-email"))
    verified = web_smoke.https_browser(web_port, path, web_origin)
    require_verified_relay(verified, callback)
    if observed.count(("GET", "/iam/verify-email")) != before + 1:
        raise FirstLoginError("Web/BFF/IAM verification relay failed")
    status, _, cookies = _iam_json(
        ready.base_url,
        "/iam/sign-in/email",
        {
            "email": address,
            "password": password,
        },
        origin=web_origin,
    )
    if status != 200 or len(cookies) != 1:
        raise FirstLoginError("verified account credential login failed")
    pair = cookies[0].split(";", 1)[0]
    if not pair.startswith("kokoro-issuer.session_token="):
        raise FirstLoginError("issuer session cookie missing")
    credentials.add(pair.split("=", 1)[1])
    enroll_in_fixed_tenant(ready, address, pair, web_origin, credentials, invite=invite)
    return replace(ready, email=address, password=password)
