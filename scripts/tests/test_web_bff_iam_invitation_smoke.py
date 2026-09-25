"""Focused guards for the run-owned invitation browser journey."""

import importlib.util
import io
import sys
import tempfile
import unittest
from email.message import EmailMessage
from pathlib import Path
from subprocess import CompletedProcess
from types import SimpleNamespace
from unittest.mock import Mock, patch

PATH = (
    Path(__file__).resolve().parents[1] / "e2e" / "run_web_bff_iam_invitation_smoke.py"
)
sys.path.insert(0, str(PATH.parent))
spec = importlib.util.spec_from_file_location("invitation_smoke", PATH)
smoke = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = smoke
spec.loader.exec_module(smoke)

ORIGIN = "https://web-a.example.test"
INVITATION_ID = "01234567-89ab-4cde-8f01-23456789abcd"
LINK = f"{ORIGIN}/iam/interactions/invitation?id={INVITATION_ID}"


def message(subject: str, body: str) -> bytes:
    email = EmailMessage()
    email["From"] = "Kokoro <hello@example.test>"
    email["To"] = "recipient@example.test"
    email["Subject"] = subject
    email.set_content(body)
    return email.as_bytes()


class InvitationSmokeGuards(unittest.TestCase):
    def test_new_chromium_reaps_process_group_when_node_exits_before_checkpoint(self):
        child = SimpleNamespace(
            stdin=io.StringIO(),
            stdout=io.StringIO(),
            stderr=Mock(),
            poll=lambda: 1,
        )
        with (
            patch.object(smoke.subprocess, "Popen", return_value=child),
            patch.object(smoke.select, "select", return_value=([child.stdout], [], [])),
            patch.object(smoke.product.runtime, "stop_owned_process") as stop,
        ):
            with self.assertRaisesRegex(smoke.SmokeError, "checkpoint invalid"):
                smoke.run_new_account_chromium(
                    node_bin=Path("/node"),
                    payload="{}\n",
                    mailbox=object(),
                    email="new@example.test",
                    web_origin=ORIGIN,
                    path=smoke.invitation_path(INVITATION_ID),
                    credentials=object(),
                )
        stop.assert_called_once_with(child)
        child.stderr.read.assert_not_called()

    def test_chromium_new_recipient_reaches_owned_preflight(self):
        with (
            patch.object(
                smoke.product,
                "parse_args",
                return_value=SimpleNamespace(
                    expected_iam_sha="a",
                    expected_bff_sha="b",
                    expected_web_sha="c",
                ),
            ),
            patch.object(
                smoke.product.session,
                "verify_source",
                side_effect=RuntimeError("preflight"),
            ),
        ):
            with self.assertRaisesRegex(RuntimeError, "preflight"):
                smoke.main(["--browser", "chromium", "--account", "new"])

    def test_chromium_evidence_requires_one_real_owner_decision(self):
        import json

        observed = []
        owner = f"/iam/v1/tenants/tenant/invitations/{INVITATION_ID}/accept"
        with tempfile.TemporaryDirectory() as temporary:
            screenshot = Path(temporary) / "entry.png"
            evidence = {
                "browser": "chromium",
                "decision": "accept",
                "entry_form": True,
                "recipient_preview": True,
                "legacy_intermediary_absent": True,
                "decision_post_count": 1,
                "consumed_pending": True,
                "product_login_started": True,
                "product_authenticated": True,
                "rejected_anonymous": False,
                "membership_absent": False,
                "screenshot": str(screenshot),
                "account": "existing",
                "registration_verified": False,
                "unverified_login_denied": False,
                "verification_returned": False,
            }

            def browser_run(*_args, **_kwargs):
                screenshot.write_bytes(b"png")
                observed.append(("POST", owner))
                return CompletedProcess([], 0, json.dumps(evidence), "")

            with patch.object(smoke.subprocess, "run", side_effect=browser_run):
                result = smoke.chromium_invitation(
                    node_bin=Path("/node"),
                    web_origin=ORIGIN + ":12345",
                    path=smoke.invitation_path(INVITATION_ID),
                    email="recipient@example.test",
                    password="example-password",
                    decision="accept",
                    screenshot=screenshot,
                    tenant_id="tenant",
                    iam_base_url="http://127.0.0.1:1234",
                    existing_tenant_id="other-tenant",
                    observed=observed,
                )
            self.assertEqual(result.owner_post_count, 1)
            observed.clear()
            rejected = {
                **evidence,
                "decision": "reject",
                "product_login_started": False,
                "product_authenticated": False,
                "rejected_anonymous": True,
                "membership_absent": True,
            }
            reject_owner = f"/iam/v1/tenants/tenant/invitations/{INVITATION_ID}/reject"

            def reject_run(*_args, **_kwargs):
                observed.append(("POST", reject_owner))
                return CompletedProcess([], 0, json.dumps(rejected), "")

            with patch.object(smoke.subprocess, "run", side_effect=reject_run):
                rejected_result = smoke.chromium_invitation(
                    node_bin=Path("/node"),
                    web_origin=ORIGIN + ":12345",
                    path=smoke.invitation_path(INVITATION_ID),
                    email="recipient@example.test",
                    password="example-password",
                    decision="reject",
                    screenshot=screenshot,
                    tenant_id="tenant",
                    iam_base_url="http://127.0.0.1:1234",
                    existing_tenant_id="other-tenant",
                    observed=observed,
                )
            self.assertTrue(rejected_result.membership_absent)
            observed.clear()
            rejected["membership_absent"] = False
            with patch.object(smoke.subprocess, "run", side_effect=reject_run):
                with self.assertRaisesRegex(
                    smoke.SmokeError, "evidence or owner relay drift"
                ):
                    smoke.chromium_invitation(
                        node_bin=Path("/node"),
                        web_origin=ORIGIN + ":12345",
                        path=smoke.invitation_path(INVITATION_ID),
                        email="recipient@example.test",
                        password="example-password",
                        decision="reject",
                        screenshot=screenshot,
                        tenant_id="tenant",
                        iam_base_url="http://127.0.0.1:1234",
                        existing_tenant_id="other-tenant",
                        observed=observed,
                    )
            observed.clear()
            with patch.object(
                smoke.subprocess,
                "run",
                return_value=CompletedProcess([], 0, json.dumps(evidence), ""),
            ):
                with self.assertRaisesRegex(
                    smoke.SmokeError, "evidence or owner relay drift"
                ):
                    smoke.chromium_invitation(
                        node_bin=Path("/node"),
                        web_origin=ORIGIN + ":12345",
                        path=smoke.invitation_path(INVITATION_ID),
                        email="recipient@example.test",
                        password="example-password",
                        decision="accept",
                        screenshot=screenshot,
                        tenant_id="tenant",
                        iam_base_url="http://127.0.0.1:1234",
                        existing_tenant_id="other-tenant",
                        observed=observed,
                    )

    def test_chromium_failure_exposes_only_controlled_stage(self):
        secret = "https://web.example.test/iam/interactions/invitation?id=secret"
        self.assertEqual(
            smoke.chromium_failure_stage(f"Playwright failed at {secret}"), "unknown"
        )
        self.assertEqual(
            smoke.chromium_failure_stage(
                f"Playwright failed at {secret}\nChromium invitation failed at iam-membership"
            ),
            "iam-membership",
        )

    def test_new_chromium_requires_registration_verification_and_owner_relays(self):
        import json

        owner = f"/iam/v1/tenants/tenant/invitations/{INVITATION_ID}/reject"
        observed = []
        with tempfile.TemporaryDirectory() as temporary:
            screenshot = Path(temporary) / "entry.png"
            screenshot.write_bytes(b"png")
            evidence = {
                "browser": "chromium",
                "decision": "reject",
                "account": "new",
                "entry_form": True,
                "recipient_preview": True,
                "legacy_intermediary_absent": True,
                "decision_post_count": 1,
                "consumed_pending": True,
                "product_login_started": False,
                "product_authenticated": False,
                "rejected_anonymous": True,
                "membership_absent": True,
                "screenshot": str(screenshot),
                "registration_verified": True,
                "unverified_login_denied": True,
                "verification_returned": True,
            }

            def run_browser(**_kwargs):
                observed.extend(
                    [
                        ("POST", "/iam/sign-up/email"),
                        ("POST", "/iam/sign-in/email"),
                        ("GET", "/iam/verify-email"),
                        ("POST", "/iam/sign-in/email"),
                        ("POST", owner),
                    ]
                )
                return CompletedProcess([], 0, json.dumps(evidence), "")

            kwargs = dict(
                node_bin=Path("/node"),
                web_origin=ORIGIN + ":12345",
                path=smoke.invitation_path(INVITATION_ID),
                email="new@example.test",
                password="example-password",
                decision="reject",
                screenshot=screenshot,
                tenant_id="tenant",
                iam_base_url="http://127.0.0.1:1234",
                existing_tenant_id="none",
                observed=observed,
                account="new",
                mailbox=object(),
                credentials=object(),
            )
            with patch.object(
                smoke, "run_new_account_chromium", side_effect=run_browser
            ):
                self.assertTrue(
                    smoke.chromium_invitation(**kwargs).verification_returned
                )
            for missing in (
                "registration_verified",
                "unverified_login_denied",
                "verification_returned",
            ):
                observed.clear()
                evidence[missing] = False
                with patch.object(
                    smoke, "run_new_account_chromium", side_effect=run_browser
                ):
                    with (
                        self.subTest(missing=missing),
                        self.assertRaisesRegex(
                            smoke.SmokeError, "evidence or owner relay drift"
                        ),
                    ):
                        smoke.chromium_invitation(**kwargs)
                evidence[missing] = True

    def test_new_recipient_verification_is_bound_to_exact_invitation(self):
        from urllib.parse import quote

        verification = (
            ORIGIN
            + "/iam/verify-email?token=0123456789abcdef0123456789abcdef"
            + "&callbackURL="
            + quote(LINK, safe="")
        )
        self.assertEqual(
            smoke.invitation_verification_path(
                message("Verify your email", verification), ORIGIN, LINK
            ),
            verification.removeprefix(ORIGIN),
        )
        for bad in (
            verification.replace(
                quote(LINK, safe=""), quote(ORIGIN + "/auth/sign-in", safe="")
            ),
            verification + "&callbackURL=" + quote(LINK, safe=""),
            verification.replace("token=", "token=bad&token="),
            verification.replace(ORIGIN, "https://evil.example.test", 1),
            verification + "#fragment",
        ):
            with self.subTest(bad=bad), self.assertRaises(smoke.SmokeError):
                smoke.invitation_verification_path(
                    message("Verify your email", bad), ORIGIN, LINK
                )

    def test_new_recipient_signup_form_has_one_scoped_csrf(self):
        from types import SimpleNamespace

        page = SimpleNamespace(
            status=200,
            headers={
                "content-type": "text/html; charset=utf-8",
                "cache-control": "no-store",
                "referrer-policy": "same-origin",
            },
            body=(
                '<form method="post" action="/iam/interactions/invitation?id='
                + INVITATION_ID
                + '"><input name="decision" value="sign-up">'
                + '<input name="csrf_token" value="'
                + "A" * 43
                + '"><input name="name" type="text">'
                + '<input name="email" type="email">'
                + '<input name="password" type="password"></form>'
            ).encode(),
        )
        self.assertEqual(smoke.sign_up_form(page, LINK.removeprefix(ORIGIN)), "A" * 43)
        page.body += page.body
        with self.assertRaises(smoke.SmokeError):
            smoke.sign_up_form(page, LINK.removeprefix(ORIGIN))

    def test_accepts_only_the_owner_delivered_exact_invitation_link(self):
        self.assertEqual(
            smoke.invitation_mail_path(
                message("Tenant invitation", LINK), ORIGIN, INVITATION_ID
            ),
            f"/iam/interactions/invitation?id={INVITATION_ID}",
        )
        for subject, link in (
            ("Verify your email", LINK),
            ("Tenant invitation", LINK + "&error=INVALID_TOKEN"),
            ("Tenant invitation", LINK.replace(ORIGIN, "https://evil.example.test")),
            ("Tenant invitation", LINK.replace(INVITATION_ID, INVITATION_ID.upper())),
            ("Tenant invitation", LINK + "#fragment"),
            ("Tenant invitation", LINK + "\nhttps://evil.example.test"),
        ):
            with (
                self.subTest(subject=subject, link=link),
                self.assertRaises(smoke.SmokeError),
            ):
                smoke.invitation_mail_path(
                    message(subject, link), ORIGIN, INVITATION_ID
                )

    def test_actor_invitation_command_is_bounded_and_does_not_reuse_first_login_helper(
        self,
    ):
        import json
        from io import BytesIO

        class Input(BytesIO):
            def flush(self):
                pass

        class Process:
            stdin = Input()

            def poll(self):
                return None

        class Reader:
            def record(self, timeout):
                assert timeout == 30
                return {"kind": "invitation", "invitation_id": INVITATION_ID}

        process = Process()
        self.assertEqual(
            smoke.request_invitation(process, Reader(), "recipient@example.test"),
            INVITATION_ID,
        )
        self.assertEqual(
            json.loads(process.stdin.getvalue()),
            {"command": "invite-verified", "email": "recipient@example.test"},
        )
        with self.assertRaises(smoke.SmokeError):
            smoke.request_invitation(process, Reader(), "Recipient@example.test")

    def test_fixture_verification_mail_does_not_mask_real_invitation(self):
        class Mailbox:
            def __init__(self, messages):
                self.messages = iter(messages)
                self.calls = 0

            def for_recipient(self, address):
                assert address == "recipient@example.test"
                self.calls += 1
                return next(self.messages)

        mailbox = Mailbox(
            [
                message(
                    "Verify your email", ORIGIN + "/iam/verify-email?token=fixture"
                ),
                message("Tenant invitation", LINK),
            ]
        )
        self.assertEqual(
            smoke.delivered_invitation(
                mailbox, "recipient@example.test", ORIGIN, INVITATION_ID
            ),
            smoke.invitation_path(INVITATION_ID),
        )
        self.assertEqual(mailbox.calls, 2)
        missing = Mailbox([message("Verify your email", "fixture") for _ in range(3)])
        with self.assertRaises(smoke.SmokeError):
            smoke.delivered_invitation(
                missing, "recipient@example.test", ORIGIN, INVITATION_ID
            )
        self.assertEqual(missing.calls, 3)

    def test_invitation_path_requires_one_canonical_uuid(self):
        self.assertEqual(
            smoke.invitation_path(INVITATION_ID),
            "/iam/interactions/invitation?id=" + INVITATION_ID,
        )
        for bad in ("", "../other", INVITATION_ID.upper(), INVITATION_ID + "&id=other"):
            with self.subTest(bad=bad), self.assertRaises(smoke.SmokeError):
                smoke.invitation_path(bad)


if __name__ == "__main__":
    unittest.main()
