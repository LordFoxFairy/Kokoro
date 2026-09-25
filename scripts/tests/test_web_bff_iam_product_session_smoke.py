"""Focused guards for the HTTPS Product Session composition runner."""

import importlib.util
import inspect
from io import BytesIO
import json
from pathlib import Path
import sys
import time
import unittest


PATH = (
    Path(__file__).resolve().parents[1]
    / "e2e"
    / "run_web_bff_iam_product_session_smoke.py"
)
sys.path.insert(0, str(PATH.parent))
spec = importlib.util.spec_from_file_location("product_session_smoke", PATH)
smoke = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = smoke
spec.loader.exec_module(smoke)


class ProductSessionGuards(unittest.TestCase):
    def test_fixed_tenant_continuation_is_get_only_and_has_no_visible_selection(self):
        observed = []
        calls = []
        signed = "?sig=opaque"

        def request(path, *, method="GET"):
            calls.append((method, path))
            if path == "/auth/select-tenant" + signed:
                return smoke.BrowserResponse(
                    302,
                    {"location": "/iam/interactions/select-tenant" + signed},
                    [],
                    b"",
                )
            if path == "/iam/interactions/select-tenant" + signed:
                observed.append(("POST", "/iam/organization/set-active"))
                return smoke.BrowserResponse(
                    303,
                    {"location": "/auth/consent" + signed + "&scope=openid"},
                    [],
                    b"",
                )
            self.fail(f"unexpected browser request: {path}")

        def navigate(value, _stage):
            return smoke.browser_target(value, "https://web.example.test")

        result = smoke.continue_fixed_tenant(
            request,
            navigate,
            "/auth/select-tenant" + signed,
            observed,
        )
        self.assertEqual(result, "/auth/consent" + signed + "&scope=openid")
        self.assertEqual(
            calls,
            [
                ("GET", "/auth/select-tenant" + signed),
                ("GET", "/iam/interactions/select-tenant" + signed),
            ],
        )
        self.assertNotIn(("GET", "/iam/organization/list"), observed)
        self.assertEqual(
            smoke.continue_fixed_tenant(request, navigate, result, observed),
            result,
        )

    def test_actor_matrix_requires_distinct_real_identity_and_tenant_membership(self):
        ready = type(
            "Ready", (), {"tenant_id": "tenant-a", "email": "a@example.test"}
        )()
        record = {
            "kind": "actors",
            "same_tenant_member": {
                "email": "b@example.test",
                "password": "password-b",
                "user_id": "user-b",
                "tenant_id": "tenant-a",
            },
            "other_tenant_owner": {
                "email": "c@example.test",
                "password": "password-c",
                "user_id": "user-c",
                "tenant_id": "tenant-c",
            },
        }
        actors = smoke.require_actor_matrix(record, ready)
        self.assertEqual(actors.same_tenant_member.user_id, "user-b")
        self.assertEqual(actors.other_tenant_owner.tenant_id, "tenant-c")
        for invalid in (
            {**record, "unexpected": "leak"},
            {**record, "kind": "ready"},
            {
                **record,
                "same_tenant_member": {
                    **record["same_tenant_member"],
                    "tenant_id": "tenant-x",
                },
            },
            {
                **record,
                "other_tenant_owner": {
                    **record["other_tenant_owner"],
                    "tenant_id": "tenant-a",
                },
            },
            {
                **record,
                "other_tenant_owner": {
                    **record["other_tenant_owner"],
                    "user_id": "user-b",
                },
            },
        ):
            with self.subTest(invalid=invalid), self.assertRaises(smoke.SmokeError):
                smoke.require_actor_matrix(invalid, ready)

    def test_authenticated_probe_is_opt_in_and_gated(self):
        calls = []

        def probe(request, projection):
            calls.append((request, projection))
            return 1

        request = object()
        projection = {"subject": "user-b"}
        self.assertEqual(
            smoke._run_authenticated_probe(
                probe, request, projection, authenticated=False
            ),
            0,
        )
        self.assertEqual(calls, [])
        self.assertEqual(
            smoke._run_authenticated_probe(
                probe, request, projection, authenticated=True
            ),
            1,
        )
        self.assertEqual(calls, [(request, projection)])

    def test_actor_command_is_one_bounded_host_protocol_exchange(self):
        ready = type(
            "Ready", (), {"tenant_id": "tenant-a", "email": "a@example.test"}
        )()
        record = {
            "kind": "actors",
            "same_tenant_member": {
                "email": "b@example.test",
                "password": "secret-b",
                "user_id": "user-b",
                "tenant_id": "tenant-a",
            },
            "other_tenant_owner": {
                "email": "c@example.test",
                "password": "secret-c",
                "user_id": "user-c",
                "tenant_id": "tenant-c",
            },
        }

        class Process:
            stdin = BytesIO()

            def poll(self):
                return None

        class Reader:
            def record(self, timeout):
                self.timeout = timeout
                return record

        class Credentials:
            def __init__(self):
                self.values = []

            def add(self, *values):
                self.values.extend(values)

        process = Process()
        reader = Reader()
        credentials = Credentials()
        smoke.request_actor_matrix(process, reader, ready, credentials)
        self.assertEqual(process.stdin.getvalue(), b'{"command":"actors"}\n')
        self.assertEqual(reader.timeout, 60)
        self.assertEqual(credentials.values, ["secret-b", "secret-c"])

    def test_authenticated_request_exposes_only_needed_chat_wire_options(self):
        parameters = set(
            inspect.signature(smoke.AuthenticatedRequest.__call__).parameters
        )
        self.assertEqual(
            parameters,
            {
                "self",
                "path",
                "method",
                "form",
                "json_body",
                "origin",
                "authorization",
                "idempotency_key",
                "accept",
            },
        )

    def test_authenticated_action_is_gated_and_called_once(self):
        request = object()
        calls = []

        def action(received):
            calls.append(received)
            return "session-one"

        self.assertIsNone(
            smoke._run_authenticated_action(action, request, authenticated=False)
        )
        self.assertEqual(calls, [])
        self.assertEqual(
            smoke._run_authenticated_action(action, request, authenticated=True),
            "session-one",
        )
        self.assertEqual(calls, [request])

    def test_authenticated_action_failure_propagates_through_cleanup(self):
        events = []

        def action(_request):
            events.append("action")
            raise RuntimeError("probe failed")

        with self.assertRaisesRegex(RuntimeError, "probe failed"):
            try:
                smoke._run_authenticated_action(action, object(), authenticated=True)
            finally:
                events.append("cleanup")
        self.assertEqual(events, ["action", "cleanup"])

    def test_refreshed_chat_list_is_exact_for_default_and_action_paths(self):
        smoke.require_expected_chat_sessions(
            {"sessions": [], "next_cursor": None}, None
        )
        smoke.require_expected_chat_sessions(
            {
                "sessions": [{"session_id": "session-one", "title": "New chat"}],
                "next_cursor": None,
            },
            "session-one",
        )
        for body, expected in (
            ({"sessions": [{"session_id": "unexpected"}]}, None),
            ({"sessions": []}, "session-one"),
            (
                {
                    "sessions": [
                        {"session_id": "session-one"},
                        {"session_id": "extra"},
                    ]
                },
                "session-one",
            ),
            ({"sessions": [{"session_id": "other"}]}, "session-one"),
        ):
            with (
                self.subTest(body=body, expected=expected),
                self.assertRaises(smoke.SmokeError),
            ):
                smoke.require_expected_chat_sessions(body, expected)

    def test_product_chat_list_requires_live_private_web_projection(self):
        headers = {
            "content-type": "application/json; charset=utf-8",
            "cache-control": "private, no-store",
            "x-request-id": "chat-request-1",
        }
        good = smoke.old.BrowserResponse(
            200, headers, [], b'{"sessions":[],"next_cursor":null}'
        )
        smoke.require_product_chat_list(good)
        for changed in (
            smoke.old.BrowserResponse(401, headers, [], good.body),
            smoke.old.BrowserResponse(
                200, {**headers, "cache-control": "public"}, [], good.body
            ),
            smoke.old.BrowserResponse(
                200, {**headers, "cache-control": "no-store"}, [], good.body
            ),
            smoke.old.BrowserResponse(
                200, {**headers, "cache-control": "private, x-no-store"}, [], good.body
            ),
            smoke.old.BrowserResponse(
                200, {**headers, "x-request-id": "bad request id"}, [], good.body
            ),
            smoke.old.BrowserResponse(
                200, headers, [], b'{"data":{"sessions":[]},"meta":{}}'
            ),
            smoke.old.BrowserResponse(
                200, headers, [], b'{"sessions":[],"next_cursor":0}'
            ),
        ):
            with (
                self.subTest(status=changed.status, body=changed.body),
                self.assertRaises(smoke.SmokeError),
            ):
                smoke.require_product_chat_list(changed)

    def test_product_chat_list_rejection_has_stable_error_and_request_id(self):
        headers = {
            "content-type": "application/json; charset=utf-8",
            "cache-control": "private, no-store",
            "x-request-id": "chat-request-1",
        }
        good = smoke.old.BrowserResponse(
            401,
            headers,
            [],
            b'{"error":{"code":"unauthenticated","message":"unauthenticated"},"meta":{"request_id":"chat-request-1"}}',
        )
        smoke.require_product_chat_rejection(good)
        for changed in (
            smoke.old.BrowserResponse(200, headers, [], good.body),
            smoke.old.BrowserResponse(
                401,
                headers,
                [],
                b'{"error":{"code":"wrong","message":"wrong"},"meta":{"request_id":"chat-request-1"}}',
            ),
            smoke.old.BrowserResponse(
                401,
                headers,
                [],
                b'{"error":{"code":"unauthenticated","message":"unauthenticated"},"meta":{"request_id":"other"}}',
            ),
            smoke.old.BrowserResponse(
                401, {**headers, "content-type": "text/plain"}, [], good.body
            ),
        ):
            with (
                self.subTest(status=changed.status, body=changed.body),
                self.assertRaises(smoke.SmokeError),
            ):
                smoke.require_product_chat_rejection(changed)

    def test_foreign_confirmation_after_signed_get_preserves_issuer(self):
        events = []
        observed = []
        signed_get = smoke.old.BrowserResponse(
            200,
            {"content-type": "text/html; charset=utf-8"},
            [
                "kokoro-issuer.session_token.oauth_logout_confirmation=signed; Path=/iam/oauth2/end-session/confirm; HttpOnly; SameSite=Lax; Secure"
            ],
            b'<form method="post" action="https://web.example.test/iam/oauth2/end-session/confirm"><button name="action" value="confirm">Confirm</button></form>',
        )
        form = smoke.require_logout_confirmation(signed_get, "https://web.example.test")
        events.append("signed-get")

        def request(path, *, method, form, origin):
            events.append("foreign-post")
            self.assertEqual(path, smoke.CONFIRM_PATH)
            self.assertEqual(
                (method, form, origin),
                ("POST", {"action": "confirm"}, "https://evil.example.test"),
            )
            return smoke.old.BrowserResponse(403, {}, [], b"")

        def issuer():
            events.append("issuer-check")
            return smoke.old.BrowserResponse(
                200,
                {},
                [],
                b'{"session":{"id":"live","userId":"user-one"},"user":{"id":"user-one"}}',
            )

        identity = smoke.IssuerIdentity("live", "user-one")
        smoke.require_foreign_confirmation_rejected(
            request, form, issuer, observed, identity
        )
        self.assertEqual(events, ["signed-get", "foreign-post", "issuer-check"])
        self.assertEqual(observed, [])
        with self.assertRaises(smoke.SmokeError):
            smoke.require_foreign_confirmation_rejected(
                request,
                form,
                lambda: smoke.old.BrowserResponse(200, {}, [], b"null"),
                observed,
                identity,
            )

        def forwarded(path, *, method, form, origin):
            observed.append((method, path))
            return smoke.old.BrowserResponse(403, {}, [], b"")

        with self.assertRaises(smoke.SmokeError):
            smoke.require_foreign_confirmation_rejected(
                forwarded, form, issuer, observed, identity
            )

    def test_issuer_shape_and_public_subject_must_match(self):
        good = smoke.old.BrowserResponse(
            200,
            {},
            [],
            b'{"session":{"id":"session-one","userId":"user-one"},"user":{"id":"user-one"}}',
        )
        self.assertEqual(
            smoke.require_issuer_session(
                good, active=True, expected_subject="user-one"
            ),
            smoke.IssuerIdentity("session-one", "user-one"),
        )
        for document in (
            {},
            {"session": {}, "user": {"id": "user-one"}},
            {"session": {"id": "session-one"}, "user": {"id": "user-one"}},
            {
                "session": {"id": "session-one", "userId": "other"},
                "user": {"id": "user-one"},
            },
            {
                "session": {"id": "session-one", "userId": "user-one"},
                "user": {"id": "other"},
            },
        ):
            with self.subTest(document=document), self.assertRaises(smoke.SmokeError):
                smoke.require_issuer_session(
                    smoke.old.BrowserResponse(
                        200, {}, [], json.dumps(document).encode()
                    ),
                    active=True,
                    expected_subject="user-one",
                )

    def test_logout_handoff_is_returned_by_response_and_exactly_registered(self):
        ready = smoke.previous.Ready(
            "http://127.0.0.1:1234",
            "iam_web_oidc_" + "a" * 32,
            "iam:test:web-oidc-flow-host:12345678-1234-4234-8234-123456789abc:",
            "https://web.example.test/iam",
            "client-one",
            "secret",
            "https://web.example.test/api/auth/callback/kokoro-iam",
            "https://web.example.test/auth/sign-in",
            "user@example.test",
            "password",
            "tenant",
        )
        target = "/iam/oauth2/end-session?client_id=client-one&post_logout_redirect_uri=https%3A%2F%2Fweb.example.test%2Fauth%2Fsign-in"
        body = {
            "status": "signed_out",
            "remote_revocation": "confirmed",
            "issuer_session": "pending_browser_confirmation",
            "issuer_end_session_url": target,
        }
        response = smoke.old.BrowserResponse(
            200,
            {"cache-control": "private, no-store"},
            [
                "kokoro_product_session=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax; Secure"
            ],
            json.dumps(body).encode(),
        )
        self.assertEqual(
            smoke.require_signout_handoff(response, "https://web.example.test", ready),
            target,
        )
        for bad in (
            "https://evil.example.test/iam/oauth2/end-session",
            target + "&id_token_hint=secret",
            target.replace("client-one", "other"),
        ):
            with self.subTest(bad=bad), self.assertRaises(smoke.SmokeError):
                smoke.require_signout_handoff(
                    smoke.old.BrowserResponse(
                        200,
                        response.headers,
                        response.set_cookies,
                        json.dumps({**body, "issuer_end_session_url": bad}).encode(),
                    ),
                    "https://web.example.test",
                    ready,
                )

    def test_stale_signout_does_not_overwrite_current_cookie_or_handoff_issuer(self):
        good = smoke.old.BrowserResponse(
            200,
            {"cache-control": "private, no-store"},
            [],
            b'{"status":"stale_session","remote_revocation":"not_required"}',
        )
        smoke.require_stale_signout(good)
        with self.assertRaises(smoke.SmokeError):
            smoke.require_stale_signout(
                smoke.old.BrowserResponse(
                    200,
                    good.headers,
                    ["kokoro_product_session=; Path=/; Max-Age=0"],
                    good.body,
                )
            )
        for bad in (
            {"status": "signed_out", "remote_revocation": "confirmed"},
            {
                "status": "stale_session",
                "remote_revocation": "not_required",
                "issuer_end_session_url": "/iam/oauth2/end-session",
            },
        ):
            with self.subTest(bad=bad), self.assertRaises(smoke.SmokeError):
                smoke.require_stale_signout(
                    smoke.old.BrowserResponse(
                        200, good.headers, good.set_cookies, json.dumps(bad).encode()
                    )
                )

    def test_callback_cookie_must_be_secure_httponly_and_distinct(self):
        good = smoke.old.BrowserResponse(
            303,
            {"location": "/app"},
            [
                "kokoro_product_session=encrypted; Path=/; Max-Age=3600; HttpOnly; SameSite=Lax; Secure",
                "next-auth.state=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax; Secure",
            ],
            b"",
        )
        smoke.require_product_callback(good)
        smoke.require_product_callback(
            smoke.old.BrowserResponse(
                303,
                good.headers,
                [
                    *good.set_cookies,
                    "__Secure-next-auth.session-token=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax; Secure",
                ],
                b"",
            )
        )
        for bad in (
            good.set_cookies[0].replace("; HttpOnly", ""),
            good.set_cookies[0].replace("; Secure", ""),
            good.set_cookies[0].replace("Path=/", "Path=/iam"),
            good.set_cookies[0].replace("SameSite=Lax", "SameSite=None"),
        ):
            with self.subTest(bad=bad), self.assertRaises(smoke.SmokeError):
                smoke.require_product_callback(
                    smoke.old.BrowserResponse(303, good.headers, [bad], b"")
                )
        with self.assertRaises(smoke.SmokeError):
            smoke.require_product_callback(smoke.old.BrowserResponse(503, {}, [], b""))
        with self.assertRaises(smoke.SmokeError):
            smoke.require_product_callback(
                smoke.old.BrowserResponse(
                    303,
                    good.headers,
                    [
                        *good.set_cookies,
                        "__Secure-next-auth.session-token=live; Path=/; HttpOnly; SameSite=Lax; Secure",
                    ],
                    b"",
                )
            )
        for name in (
            "authjs.session-token",
            "__Secure-authjs.session-token",
            "__Host-authjs.session-token.0",
        ):
            with self.subTest(name=name), self.assertRaises(smoke.SmokeError):
                smoke.require_product_callback(
                    smoke.old.BrowserResponse(
                        303,
                        good.headers,
                        [
                            *good.set_cookies,
                            f"{name}=live; Path=/; HttpOnly; SameSite=Lax; Secure",
                        ],
                        b"",
                    )
                )

    def test_projection_never_accepts_credentials_or_extra_fields(self):
        valid_expiry = time.time_ns() // 1_000_000 + 3_500_000
        good = smoke.old.BrowserResponse(
            200,
            {"cache-control": "private, no-store", "content-type": "application/json"},
            [],
            json.dumps(
                {
                    "authenticated": True,
                    "subject": "subject",
                    "expires_at": valid_expiry,
                }
            ).encode(),
        )
        smoke.require_session_projection(good, authenticated=True)
        for body in (
            {
                "authenticated": True,
                "subject": "subject",
                "expires_at": valid_expiry,
                "access_token": "secret",
            },
            {
                "authenticated": True,
                "subject": "subject",
                "expires_at": valid_expiry,
                "refresh_token": "secret",
            },
            {
                "authenticated": True,
                "subject": "subject",
                "expires_at": valid_expiry,
                "id_token": "secret",
            },
        ):
            with self.subTest(body=body), self.assertRaises(smoke.SmokeError):
                smoke.require_session_projection(
                    smoke.old.BrowserResponse(
                        200, good.headers, [], json.dumps(body).encode()
                    ),
                    authenticated=True,
                )
        for expiry in (123, valid_expiry + 10_000_000, float(valid_expiry), True):
            with self.subTest(expiry=expiry), self.assertRaises(smoke.SmokeError):
                smoke.require_session_projection(
                    smoke.old.BrowserResponse(
                        200,
                        good.headers,
                        [],
                        json.dumps(
                            {
                                "authenticated": True,
                                "subject": "subject",
                                "expires_at": expiry,
                            }
                        ).encode(),
                    ),
                    authenticated=True,
                )
        false = smoke.old.BrowserResponse(
            200, good.headers, [], b'{"authenticated":false}'
        )
        smoke.require_session_projection(false, authenticated=False)

    def test_refresh_keeps_subject_and_fixed_expiry(self):
        initial = {"authenticated": True, "subject": "user-one", "expires_at": 123}
        smoke.require_refreshed_projection(initial, dict(initial))
        for changed in (
            {**initial, "subject": "other"},
            {**initial, "expires_at": 124},
        ):
            with self.subTest(changed=changed), self.assertRaises(smoke.SmokeError):
                smoke.require_refreshed_projection(initial, changed)

    def test_confirmation_form_has_exact_action_and_single_confirm(self):
        response = smoke.old.BrowserResponse(
            200,
            {"content-type": "text/html; charset=utf-8"},
            [
                "kokoro-issuer.session_token.oauth_logout_confirmation=signed; Path=/iam/oauth2/end-session/confirm; HttpOnly; SameSite=Lax; Secure"
            ],
            b'<main><form method="post" data-oidc-logout-confirmation action="https://web.example.test/iam/oauth2/end-session/confirm"><button type="submit" name="action" value="confirm">Confirm logout</button></form></main>',
        )
        smoke.require_logout_confirmation(response, "https://web.example.test")
        with self.assertRaises(smoke.SmokeError) as rejected:
            smoke.require_logout_confirmation(
                smoke.old.BrowserResponse(
                    400,
                    {"content-type": "application/private-token; charset=utf-8"},
                    [],
                    b'{"error":"invalid_request"}',
                ),
                "https://web.example.test",
            )
        self.assertIn("content-type other", str(rejected.exception))
        self.assertNotIn("private-token", str(rejected.exception))
        with self.assertRaises(smoke.SmokeError) as secret_code:
            smoke.require_logout_confirmation(
                smoke.old.BrowserResponse(
                    400,
                    {"content-type": "application/json"},
                    [],
                    b'{"error":"abcdef1234567890"}',
                ),
                "https://web.example.test",
            )
        self.assertIn("code unknown", str(secret_code.exception))
        self.assertNotIn("abcdef1234567890", str(secret_code.exception))
        smoke.require_logout_confirmation(
            smoke.old.BrowserResponse(
                200,
                response.headers,
                [response.set_cookies[0].replace("; Secure", "")],
                response.body,
            ),
            "https://web.example.test",
        )
        with self.assertRaises(smoke.SmokeError):
            smoke.require_logout_confirmation(
                smoke.old.BrowserResponse(
                    200,
                    response.headers,
                    [
                        response.set_cookies[0]
                        .replace("kokoro-issuer.", "__Secure-kokoro-issuer.")
                        .replace("; Secure", "")
                    ],
                    response.body,
                ),
                "https://web.example.test",
            )
        for name in (
            "evil.session_token.oauth_logout_confirmation",
            "kokoro-issuer.other.oauth_logout_confirmation",
        ):
            with self.subTest(name=name), self.assertRaises(smoke.SmokeError):
                smoke.require_logout_confirmation(
                    smoke.old.BrowserResponse(
                        200,
                        response.headers,
                        [
                            response.set_cookies[0].replace(
                                "kokoro-issuer.session_token.oauth_logout_confirmation",
                                name,
                            )
                        ],
                        response.body,
                    ),
                    "https://web.example.test",
                )
        for body in (
            response.body.replace(
                b'action="https://web.example.test/iam',
                b'action="https://evil.test/iam',
            ),
            response.body.replace(b'value="confirm"', b'value="cancel"'),
        ):
            with self.subTest(body=body), self.assertRaises(smoke.SmokeError):
                smoke.require_logout_confirmation(
                    smoke.old.BrowserResponse(
                        200, response.headers, response.set_cookies, body
                    ),
                    "https://web.example.test",
                )

    def test_product_redis_inventory_is_origin_scoped(self):
        patterns = []

        class Resources:
            def command(self, command):
                patterns.append(command[-1])
                return ""

        smoke.web_redis_keys(
            "redis://localhost:6379", "https://web.example.test", Resources()
        )
        self.assertEqual(len(patterns), 3)
        self.assertTrue(all(pattern.endswith(":*") for pattern in patterns))
        self.assertTrue(
            any(
                pattern.startswith("kokoro:web:product-session:")
                for pattern in patterns
            )
        )
        self.assertFalse(any(pattern == "*" for pattern in patterns))


if __name__ == "__main__":
    unittest.main()
