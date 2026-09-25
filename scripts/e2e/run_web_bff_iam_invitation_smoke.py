#!/usr/bin/env python3
"""Exercise a delivered invitation through real HTTPS Web → BFF → IAM.

The first slice proves an existing foreign-tenant account can open the actual
SMTP invitation, sign in at the independent Web interaction, and view only its
recipient-scoped pending context. Decision, new-account and Chromium legs are
not counted as passed by this runner until they have their own assertions.
"""

from __future__ import annotations

from email import policy
from email.parser import BytesParser
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import secrets
import subprocess
import sys
import tempfile
import time
from urllib.parse import unquote, urlsplit
from uuid import uuid4

import run_web_bff_iam_product_session_smoke as product


SmokeError = product.SmokeError
PAGE_PATH = "/iam/interactions/invitation"
UUID = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\Z"
)
EMAIL = re.compile(r"[^@\s]+@[^@\s]+\Z")


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
        or page.headers.get("referrer-policy") != "no-referrer"
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
    actor: product.ActorIdentity,
    tenant_id: str,
    credentials: product.previous.CredentialRegistry,
    observed: list[tuple[str, str]],
    decision: str,
) -> None:
    jar = product.BrowserCookies(credentials.add)

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
            "email": actor.email,
            "password": actor.password,
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
        or preview.headers.get("referrer-policy") != "no-referrer"
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


def main(argv: list[str] | None = None) -> int:
    import argparse

    selector = argparse.ArgumentParser(add_help=False)
    selector.add_argument("--decision", choices=("accept", "reject"), default="accept")
    selected, remaining = selector.parse_known_args(argv)
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
    web_origin = f"https://web-{run_id}.example.test"
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
    proxies: list[product.Proxy] = []
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
                stage = "existing actor and invitation"
                actors = product.request_actor_matrix(iam, reader, ready, credentials)
                actor = actors.other_tenant_owner
                invite_id = request_invitation(iam, reader, actor.email)
                credentials.add(invite_id)
                path = delivered_invitation(mailbox, actor.email, web_origin, invite_id)
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
                web_proxy = product.Proxy(
                    next_port, host_name, product.certificate(directory, host_name)
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
                    "host": host_name,
                    "proto": "https",
                }:
                    raise SmokeError("Web HTTPS origin mismatch")
                stage = "existing recipient browser entry"
                existing_account_entry(
                    web_proxy.server_port,
                    web_origin,
                    path,
                    actor,
                    ready.tenant_id,
                    credentials,
                    bff_proxy.observed,
                    selected.decision,
                )
                if selected.decision == "accept":
                    stage = "accepted recipient Product login"
                    from dataclasses import replace

                    product.run_browser(
                        web_proxy.server_port,
                        web_origin,
                        replace(ready, email=actor.email, password=actor.password),
                        bff_proxy.observed,
                        credentials,
                    )
            except (SmokeError, product.first_login.FirstLoginError) as error:
                failures.append(f"{stage}: {error}")
            except Exception:
                failures.append(stage)
            finally:
                for proxy in reversed(proxies):
                    try:
                        proxy.close()
                    except Exception:
                        failures.append("owned proxy cleanup")
                processes_stopped = True
                for process in reversed(processes):
                    try:
                        product.runtime.stop_owned_process(process)
                    except Exception:
                        processes_stopped = False
                        failures.append("owned process cleanup")
                if reader is not None:
                    try:
                        reader.close()
                    except Exception:
                        failures.append("IAM protocol cleanup")
                if mailbox is not None:
                    try:
                        mailbox.close()
                    except Exception:
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
                    except Exception:
                        failures.append("Web Redis cleanup")
                try:
                    resources.cleanup()
                    resources.verify_clean()
                except Exception:
                    failures.append("BFF resource cleanup")
                if iam_attempted and processes_stopped:
                    try:
                        product.reconcile_iam_identity(
                            resources, iam_identity, iam_owner_token
                        )
                    except Exception:
                        failures.append("IAM resource cleanup")
                elif iam_attempted:
                    failures.append(
                        "IAM resource cleanup deferred: process still running"
                    )
                try:
                    log.flush()
                    product.previous.assert_log_clean(log_path, credentials.values())
                except Exception:
                    failures.append("credential log scan")
    if failures:
        raise SmokeError("; ".join(sorted(set(failures))) + " failed")
    print(
        json.dumps(
            {
                "status": "passed",
                "flow": "existing_email_invitation_decision",
                "smtp_invitation": "verified",
                "web_bff_iam_context": "invited_recipient_positive",
                "recipient_isolation": "not_run",
                "decision": selected.decision,
                "product_login": "verified"
                if selected.decision == "accept"
                else "not_attempted",
                "chromium": "not_run",
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
