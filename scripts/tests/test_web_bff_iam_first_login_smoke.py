"""Focused first-login SMTP and verification-link guards."""

import importlib.util
from email.message import EmailMessage
from pathlib import Path
import smtplib
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch


PATH = (
    Path(__file__).resolve().parents[1] / "e2e" / "run_web_bff_iam_first_login_smoke.py"
)
sys.path.insert(0, str(PATH.parent))
spec = importlib.util.spec_from_file_location("first_login_smoke", PATH)
smoke = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = smoke
spec.loader.exec_module(smoke)


class FirstLoginGuards(unittest.TestCase):
    def test_browser_start_form_posts_csrf_with_the_issued_cookie(self):
        origin = "https://web.example.test"
        token = "a" * 64
        response = smoke.web_smoke.BrowserResponse
        document = f'<meta name="referrer" content="no-referrer"><form method="post" action="/api/auth/signin/kokoro-iam"><input type="hidden" name="csrfToken" value="{token}"></form>'.encode()
        replies = iter([
            response(200, {"content-type": "text/html; charset=utf-8", "cache-control": "no-store", "referrer-policy": "strict-origin-when-cross-origin"}, ["next-auth.csrf-token=proof; Path=/"], document),
            response(302, {"location": origin + "/iam/oauth2/authorize?state=state-secret&nonce=nonce-secret"}, [], b""),
            response(302, {"location": origin + "/auth/sign-in?state=state-secret&nonce=nonce-secret"}, [], b""),
            response(200, {"content-type": "text/html; charset=utf-8"}, [], b'<form method="post" action="/auth/sign-in?state=state-secret&amp;nonce=nonce-secret"><input type="hidden" name="csrf_token" value="issuer-proof"><input name="email" type="email"><input name="password" type="password"></form>'),
        ])
        calls, secrets = [], []

        def request(port, path, observed_origin, **kwargs):
            calls.append((port, path, observed_origin, kwargs))
            return next(replies)

        smoke.probe_formal_login_entry(443, origin, SimpleNamespace(add=secrets.append), browser_request=request)
        self.assertEqual(len(calls), 4)
        self.assertEqual(calls[1], (443, "/api/auth/signin/kokoro-iam", origin, {"method": "POST", "form": {"csrfToken": token}, "origin": origin, "cookie": "next-auth.csrf-token=proof"}))
        self.assertIn(token, secrets)
        self.assertIn("issuer-proof", secrets)

    def test_invalid_browser_start_forms_fail_before_any_post(self):
        origin = "https://web.example.test"
        token = "a" * 64
        response = smoke.web_smoke.BrowserResponse
        document = f'<form method="post" action="/api/auth/signin/kokoro-iam"><input type="hidden" name="csrfToken" value="{token}"></form>'.encode()
        headers = {"content-type": "text/html; charset=utf-8", "cache-control": "private, no-store", "referrer-policy": "no-referrer"}
        variants = [
            ({**headers, "content-type": "text/plain"}, document),
            ({**headers, "cache-control": "no-store=false"}, document),
            ({**headers, "referrer-policy": "origin"}, document),
            (headers, document.replace(b'/api/auth/signin/kokoro-iam', b'https://SECRET.test/SECRET')),
            (headers, document.replace(b'method="post"', b'method="get"')),
            (headers, document.replace(b'csrfToken', b'csrf_token')),
            (headers, document.replace(token.encode(), b'SECRET')),
            (headers, document.replace(b'</form>', b'<input type="hidden" name="csrfToken" value="SECRET"></form>')),
            (headers, document.replace(b'</form>', b'<input type="hidden" name="callbackUrl" value="SECRET"></form>')),
            (headers, document + document),
            (headers, document.replace(b'</form>', b'')),
            (headers, b'\xffSECRET'),
            (headers, b'<meta name="referrer" content="origin">' + document),
            (headers, b'<meta name="referrer" content="no-referrer"><meta name="referrer" content="origin">' + document),
            (headers, b'<meta name="referrer" content="no-referrer"><meta name="REFERRER" content="origin">' + document),
            (headers, b'<meta name="REFERRER" content="origin">' + document),
        ]
        for header, body in variants:
            calls = []

            def request(*args, **kwargs):
                calls.append((args, kwargs))
                return response(200, header, [], body)

            with self.subTest(header=header, body=body):
                with self.assertRaises(smoke.FormalLoginNavigationError) as raised:
                    smoke.probe_formal_login_entry(443, origin, SimpleNamespace(add=lambda *_: None), browser_request=request)
                self.assertEqual(len(calls), 1)
                self.assertEqual(raised.exception.safe_category(), "login_navigation_entry_form_200")
                self.assertNotIn("SECRET", str(raised.exception))

    def test_formal_navigation_reports_each_safe_hop(self):
        origin = "https://web.example.test"
        response = smoke.web_smoke.BrowserResponse
        good_login = response(302, {"location": origin + "/iam/oauth2/authorize?state=SECRET&nonce=SECRET"}, [], b"")
        good_authorize = response(302, {"location": origin + "/auth/sign-in?state=SECRET&nonce=SECRET"}, [], b"")
        for hop, replies, expected in [
            ("entry", [response(503, {}, [], b"SECRET")], "login_navigation_entry_http_503"),
            ("authorize", [good_login, response(400, {}, [], b"SECRET")], "login_navigation_authorize_redirect_400"),
            ("form", [good_login, good_authorize, response(200, {}, [], b"SECRET")], "login_navigation_form_form_200"),
            ("cross_origin", [response(302, {"location": "https://SECRET.test/SECRET?token=SECRET"}, [], b"")], "login_navigation_entry_target_302"),
        ]:
            with self.subTest(hop=hop):
                iterator = iter(replies)
                with self.assertRaises(smoke.FormalLoginNavigationError) as raised:
                    smoke.probe_formal_login_entry(443, origin, SimpleNamespace(add=lambda *_: None), browser_request=lambda *_a, **_k: next(iterator))
                self.assertEqual(raised.exception.safe_category(), expected)
                self.assertNotIn("SECRET", str(raised.exception))

    def test_formal_request_exceptions_never_escape_or_expose_text(self):
        origin = "https://web.example.test"
        response = smoke.web_smoke.BrowserResponse
        replies = [
            response(302, {"location": origin + "/iam/oauth2/authorize?state=SECRET&nonce=SECRET"}, [], b""),
            response(302, {"location": origin + "/auth/sign-in?state=SECRET&nonce=SECRET"}, [], b""),
        ]
        class SecretError(Exception):
            def __str__(self):
                raise AssertionError("must not render an untrusted error")
        for index, hop in enumerate(("entry", "authorize", "form")):
            calls = iter(replies[:index])
            def request(*_args, **_kwargs):
                try:
                    return next(calls)
                except StopIteration:
                    raise SecretError("SECRET cookie body query")
            with self.subTest(hop=hop), self.assertRaises(smoke.FormalLoginNavigationError) as raised:
                smoke.probe_formal_login_entry(443, origin, SimpleNamespace(add=lambda *_: None), browser_request=request)
            self.assertEqual(str(raised.exception), f"login_navigation_{hop}_request_unknown")

    def test_verified_user_joins_existing_fixed_product_tenant(self):
        ready = SimpleNamespace(
            base_url="http://127.0.0.1:4211",
            email="owner@example.test",
            password="owner-password",
            tenant_id="fixed-tenant",
        )
        calls = []
        invited = []

        def iam(base_url, path, body, *, cookie="", origin):
            calls.append((base_url, path, body, cookie, origin))
            if path == "/iam/v1/tenants/fixed-tenant/invitations/invite-one/accept":
                return (
                    200,
                    {
                        "data": {
                            "invitation_id": "invite-one",
                            "member_id": "member-one",
                            "status": "accepted",
                        }
                    },
                    [],
                )
            self.fail(f"unexpected IAM request: {path}")

        class Credentials:
            values = []

            def add(self, value):
                self.values.append(value)

        with patch.object(smoke, "_iam_json", side_effect=iam):
            smoke.enroll_in_fixed_tenant(
                ready,
                "new@example.test",
                "kokoro-issuer.session_token=new",
                "https://web.example.test",
                Credentials(),
                invite=lambda email: invited.append(email) or "invite-one",
            )
        self.assertEqual(
            [call[1] for call in calls],
            ["/iam/v1/tenants/fixed-tenant/invitations/invite-one/accept"],
        )
        self.assertEqual(invited, ["new@example.test"])
        self.assertEqual(calls[0][3], "kokoro-issuer.session_token=new")
        self.assertEqual(calls[0][2], {})

    def test_visible_form_requires_both_credential_inputs(self):
        good = b'<form><input name="email" type="email"><input name="password" type="password"></form>'
        smoke.require_credential_inputs(good)
        for bad in (
            b'<form><input name="email" type="email"></form>',
            b'<form><input name="email" type="email" hidden><input name="password" type="password"></form>',
            b'<form><input name="email" type="email"><input name="password" type="text"></form>',
        ):
            with self.subTest(bad=bad), self.assertRaises(smoke.FirstLoginError):
                smoke.require_credential_inputs(bad)

    def test_cache_no_store_requires_a_complete_directive(self):
        self.assertTrue(
            smoke.has_cache_directive("private, no-store, max-age=0", "no-store")
        )
        for value in ("x-no-store", "no-store=false", "max-age=0"):
            with self.subTest(value=value):
                self.assertFalse(smoke.has_cache_directive(value, "no-store"))

    def test_verification_relay_never_issues_a_login_cookie(self):
        response = smoke.web_smoke.BrowserResponse(
            302,
            {
                "location": "https://web.example.test/auth/sign-in",
                "cache-control": "private, no-store, max-age=0",
                "referrer-policy": "no-referrer",
            },
            [],
            b"",
        )
        callback = "https://web.example.test/auth/sign-in"
        smoke.require_verified_relay(response, callback)
        for bad in (
            smoke.web_smoke.BrowserResponse(
                response.status,
                response.headers,
                ["kokoro-issuer.session_token=bad"],
                b"",
            ),
            smoke.web_smoke.BrowserResponse(
                response.status,
                {**response.headers, "cache-control": "no-store=false"},
                [],
                b"",
            ),
            smoke.web_smoke.BrowserResponse(
                response.status,
                {**response.headers, "referrer-policy": "strict-origin"},
                [],
                b"",
            ),
        ):
            with self.subTest(bad=bad), self.assertRaises(smoke.FirstLoginError):
                smoke.require_verified_relay(bad, callback)

    def test_leak_scan_tracks_only_secret_query_fields(self):
        class Credentials:
            values = []

            def add(self, value):
                self.values.append(value)

        credentials = Credentials()
        smoke.remember_secret_query(
            "/iam/verify-email?token=secret-token&callbackURL=https%3A%2F%2Fweb.example.test%2Fauth%2Fsign-in",
            credentials,
            {"token"},
        )
        self.assertEqual(credentials.values, ["secret-token"])

    def test_smtp_mailbox_receives_only_requested_recipient(self):
        mailbox = smoke.SmtpMailbox()
        try:
            host, port = "127.0.0.1", mailbox.server.server_address[1]
            message = EmailMessage()
            message["From"] = "iam@example.test"
            message["To"] = "new@example.test"
            message["Subject"] = "Verify your email"
            message.set_content(
                "https://web.example.test/iam/verify-email?token="
                + "a" * 32
                + "&callbackURL=https%3A%2F%2Fweb.example.test%2Fauth%2Fsign-in"
            )
            with smtplib.SMTP(host, port, timeout=5) as client:
                client.send_message(message)
            body = mailbox.for_recipient("new@example.test")
            self.assertIn(b"Verify your email", body)
            self.assertEqual(
                smoke.verification_path(body, "https://web.example.test"),
                "/iam/verify-email?token="
                + "a" * 32
                + "&callbackURL=https%3A%2F%2Fweb.example.test%2Fauth%2Fsign-in",
            )
        finally:
            mailbox.close()

    def test_verification_rejects_other_origin_and_query_alias(self):
        for url in (
            "https://evil.example.test/iam/verify-email?token="
            + "a" * 32
            + "&callbackURL=https%3A%2F%2Fweb.example.test%2Fauth%2Fsign-in",
            "https://web.example.test/iam/verify-email?token="
            + "a" * 32
            + "&token=b&callbackURL=https%3A%2F%2Fweb.example.test%2Fauth%2Fsign-in",
            "https://web.example.test/iam/verify-email?token="
            + "a" * 32
            + "&callbackURL=https%3A%2F%2Fevil.example.test%2Fauth%2Fsign-in",
        ):
            with self.subTest(url=url), self.assertRaises(smoke.FirstLoginError):
                smoke.verification_path(
                    (
                        "Subject: Verify your email\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n"
                        + url
                    ).encode(),
                    "https://web.example.test",
                )


if __name__ == "__main__":
    unittest.main()
