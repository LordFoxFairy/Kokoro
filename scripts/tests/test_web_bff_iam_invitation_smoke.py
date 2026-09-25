"""Focused guards for the run-owned invitation browser journey."""

from email.message import EmailMessage
import importlib.util
from pathlib import Path
import sys
import unittest


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
        from io import BytesIO
        import json

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
