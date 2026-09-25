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
    def test_verified_user_joins_existing_fixed_product_tenant(self):
        ready = SimpleNamespace(
            base_url="http://127.0.0.1:4211",
            email="owner@example.test",
            password="owner-password",
            tenant_id="fixed-tenant",
        )
        calls = []

        def iam(base_url, path, body, *, cookie="", origin):
            calls.append((base_url, path, body, cookie, origin))
            if path == "/iam/sign-in/email":
                return (
                    200,
                    {},
                    ["kokoro-issuer.session_token=owner; Path=/iam; HttpOnly"],
                )
            if path == "/iam/organization/invite-member":
                return 200, {"id": "invite-one", "organizationId": "fixed-tenant"}, []
            if path == "/iam/organization/accept-invitation":
                return 200, {"member": {"organizationId": "fixed-tenant"}}, []
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
            )
        self.assertEqual(
            [call[1] for call in calls],
            [
                "/iam/sign-in/email",
                "/iam/organization/invite-member",
                "/iam/organization/accept-invitation",
            ],
        )
        self.assertEqual(
            calls[1][2],
            {
                "email": "new@example.test",
                "role": "member",
                "organizationId": "fixed-tenant",
            },
        )
        self.assertEqual(calls[1][3], "kokoro-issuer.session_token=owner")
        self.assertEqual(calls[2][2], {"invitationId": "invite-one"})
        self.assertEqual(calls[2][3], "kokoro-issuer.session_token=new")

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
