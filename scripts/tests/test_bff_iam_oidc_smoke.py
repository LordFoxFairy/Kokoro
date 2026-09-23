"""Protocol and cleanup guards for real IAM → BFF first-login smoke."""

import importlib.util
import base64
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

PATH = Path(__file__).resolve().parents[1] / "e2e" / "run_bff_iam_oidc_smoke.py"
sys.path.insert(0, str(PATH.parent))
spec = importlib.util.spec_from_file_location("bff_iam_oidc_smoke", PATH)
smoke = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = smoke
spec.loader.exec_module(smoke)


class OidcGuards(unittest.TestCase):
    class Headers:
        def __init__(self, values=None, cookies=None):
            self.values = {key.lower(): value for key, value in (values or {}).items()}
            self.cookies = list(cookies or [])

        def get(self, name):
            return self.values.get(name.lower())

        def get_all(self, name):
            return self.cookies if name.lower() == "set-cookie" else None

    @staticmethod
    def jwt(claims):
        encoded = base64.urlsafe_b64encode(json.dumps(claims).encode()).decode().rstrip("=")
        return "header." + encoded + ".signature"

    @classmethod
    def token_fixture(cls):
        issuer = "https://web.example.test/iam"
        subject = "user-1"
        nonce = "nonce-1"
        access = cls.jwt({
            "iss": issuer,
            "aud": [smoke.RESOURCE, issuer + "/oauth2/userinfo"],
            "sub": subject,
            "client_id": "client",
            "scope": smoke.SCOPES,
            smoke.TOKEN_KIND_CLAIM: "user_delegated",
            smoke.TENANT_CLAIM: "tenant",
        })
        identity = cls.jwt({
            "iss": issuer,
            "aud": "client",
            "sub": subject,
            "nonce": nonce,
        })
        return {
            "access_token": access,
            "refresh_token": "refresh-token",
            "id_token": identity,
            "scope": smoke.SCOPES,
        }, nonce

    @staticmethod
    def ready():
        return smoke.Ready(
            base_url="http://127.0.0.1:1234",
            database_name="iam_web_oidc_" + "a" * 32,
            redis_prefix="iam:test:web-oidc-flow-host:12345678-1234-1234-1234-123456789abc:",
            issuer_url="https://web.example.test/iam",
            client_id="client",
            client_secret="secret",
            redirect_uri="https://web.example.test/api/auth/callback/kokoro-iam",
            post_logout_redirect_uri="https://web.example.test/auth/sign-in",
            email="user@example.test",
            password="pass",
            tenant_id="tenant",
        )

    def test_ready_has_exact_owned_resource_and_client_shape(self):
        good = dict(kind="ready", base_url="http://127.0.0.1:1234",
                    database_name="iam_web_oidc_" + "a" * 32,
                    redis_prefix="iam:test:web-oidc-flow-host:12345678-1234-1234-1234-123456789abc:",
                    issuer_url="https://web.example.test/iam", client_id="client",
                    client_secret="secret", redirect_uri="https://web.example.test/api/auth/callback/kokoro-iam",
                    post_logout_redirect_uri="https://web.example.test/auth/sign-in", email="user@example.test",
                    password="pass", tenant_id="tenant")
        self.assertEqual(smoke.validate_ready(good).client_id, "client")
        for changed in ({"extra": "bad"}, {"base_url": "https://outside.test"},
                        {"database_name": "postgres"}, {"issuer_url": "http://web.example.test/iam"},
                        {"client_secret": ""}, {"post_logout_redirect_uri": "https://evil.test/"}):
            with self.subTest(changed=changed), self.assertRaises(smoke.SmokeError):
                smoke.validate_ready({**good, **changed})

    def test_signed_interaction_preserves_raw_query(self):
        raw = "https://web.example.test/auth/select-tenant?sig=abc&ba_param=x&ba_param=y&ba_iat=123"
        self.assertEqual(smoke.interaction(raw), ("select-tenant", "sig=abc&ba_param=x&ba_param=y&ba_iat=123"))
        for bad in ("https://evil.test/auth/consent?sig=x", "https://web.example.test/auth/consent",
                    "https://web.example.test/auth/consent?sig=x#frag"):
            with self.assertRaises(smoke.SmokeError):
                smoke.interaction(bad)

    def test_first_grant_starts_unsigned_session_only_after_signed_login_interaction(self):
        ready = self.ready()
        raw_query = "sig=signed-value&ba_param=opaque&ba_iat=123"
        calls = []
        responses = iter(
            (
                smoke.HttpResponse(
                    302,
                    self.Headers({"location": "https://web.example.test/auth/sign-in?" + raw_query}),
                    b"",
                ),
                smoke.HttpResponse(
                    200,
                    self.Headers(
                        {"content-type": "application/json"},
                        ["kokoro-issuer.session_token=session-secret; Path=/iam; HttpOnly; SameSite=Lax"],
                    ),
                    b'{"user":{"id":"user-1"}}',
                ),
                smoke.HttpResponse(
                    200,
                    self.Headers({"content-type": "application/json; charset=utf-8"}),
                    b'{"redirect":true,"url":"https://web.example.test/auth/select-tenant?sig=next"}',
                ),
            )
        )

        def fake_http(base, path, secret, **kwargs):
            calls.append((path, kwargs))
            return next(responses)

        jar = smoke.IssuerCookies()
        with patch.object(smoke, "http", side_effect=fake_http):
            target, seen, case_count = smoke.start_first_grant(
                "http://127.0.0.1:9999",
                "service-secret",
                ready,
                jar,
                "oauth-query",
                lambda *_: None,
            )

        self.assertEqual([path for path, _ in calls], [
            "/iam/oauth2/authorize?oauth-query",
            "/iam/sign-in/email",
            "/iam/oauth2/continue",
        ])
        self.assertEqual(calls[0][1].get("cookie", ""), "")
        self.assertEqual(calls[1][1]["payload"], {"email": ready.email, "password": ready.password})
        self.assertEqual(calls[2][1]["payload"], {"postLogin": True, "oauth_query": raw_query})
        self.assertEqual(calls[2][1]["cookie"], "kokoro-issuer.session_token=session-secret")
        self.assertEqual(target, "https://web.example.test/auth/select-tenant?sig=next")
        self.assertEqual(seen, ["sign-in"])
        self.assertEqual(case_count, 3)

    def test_interaction_sequence_requires_sign_in_then_tenant_then_consent(self):
        smoke.validate_interaction_sequence(["sign-in", "select-tenant", "consent"])
        for changed in (
            ["select-tenant", "consent"],
            ["sign-in", "consent", "select-tenant"],
            ["sign-in", "select-tenant"],
            ["sign-in", "select-tenant", "consent", "consent"],
        ):
            with self.subTest(changed=changed), self.assertRaises(smoke.SmokeError):
                smoke.validate_interaction_sequence(changed)

    def test_callback_requires_exact_registered_uri_and_state(self):
        self.assertEqual(smoke.authorization_code("https://web.example.test/api/auth/callback/kokoro-iam?state=s&code=c",
                                                   "https://web.example.test/api/auth/callback/kokoro-iam", "s"), "c")
        for bad in ("https://evil.test/api/auth/callback/kokoro-iam?state=s&code=c",
                    "https://web.example.test/api/auth/callback/kokoro-iam?state=x&code=c",
                    "https://web.example.test/api/auth/callback/kokoro-iam?state=s&code=c&code=d"):
            with self.assertRaises(smoke.SmokeError):
                smoke.authorization_code(bad, "https://web.example.test/api/auth/callback/kokoro-iam", "s")

    def test_logout_redirect_requires_exact_registered_uri_and_state(self):
        redirect = "https://web.example.test/auth/sign-in?state=logout-state"
        smoke.validate_logout_redirect(redirect, "https://web.example.test/auth/sign-in", "logout-state")
        for bad in (
            "https://web.example.test/auth/sign-in",
            "https://web.example.test/auth/sign-in?state=wrong",
            "https://web.example.test/auth/sign-in?state=logout-state&extra=1",
            "https://evil.test/auth/sign-in?state=logout-state",
            "https://web.example.test/auth/sign-in?state=logout-state#fragment",
        ):
            with self.subTest(url=bad), self.assertRaises(smoke.SmokeError):
                smoke.validate_logout_redirect(bad, "https://web.example.test/auth/sign-in", "logout-state")

    def test_logout_response_classifies_native_json_redirect_without_html_headers(self):
        response = smoke.HttpResponse(
            200,
            self.Headers({"content-type": "application/json"}),
            b'{"redirect":true,"url":"https://web.example.test/auth/sign-in?state=logout-state"}',
        )
        self.assertEqual(
            smoke.classify_logout_response(response, self.ready(), "logout-state"),
            ("redirect", "https://web.example.test/auth/sign-in?state=logout-state"),
        )
        changed = smoke.HttpResponse(200, response.headers, b'{"redirect":true,"url":"https://evil.test/"}')
        with self.assertRaises(smoke.SmokeError):
            smoke.classify_logout_response(changed, self.ready(), "logout-state")

    def test_logout_response_accepts_only_exact_hardened_confirmation_snapshot(self):
        ready = self.ready()
        headers = {
            "content-type": "text/html; charset=utf-8",
            "content-security-policy": smoke.LOGOUT_CSP,
            "x-content-type-options": "nosniff",
            "cache-control": "no-store",
            "pragma": "no-cache",
        }
        response = smoke.HttpResponse(
            200,
            self.Headers(headers),
            smoke.expected_logout_confirmation_body(ready),
        )
        self.assertEqual(smoke.classify_logout_response(response, ready, "logout-state"), ("confirmation", None))
        for change in (
            {"content-security-policy": "default-src *"},
            {"x-content-type-options": ""},
            {"content-type": "text/html"},
        ):
            with self.subTest(change=change), self.assertRaises(smoke.SmokeError):
                smoke.classify_logout_response(
                    smoke.HttpResponse(200, self.Headers({**headers, **change}), response.body), ready, "logout-state"
                )
        with self.assertRaises(smoke.SmokeError):
            smoke.classify_logout_response(
                smoke.HttpResponse(200, self.Headers(headers), response.body.replace(b"confirm", b"approve", 1)),
                ready,
                "logout-state",
            )

    def test_logout_header_evidence_never_contains_cookie_values(self):
        response = smoke.HttpResponse(
            200,
            self.Headers(
                {"content-type": "text/html; charset=utf-8", "content-security-policy": smoke.LOGOUT_CSP,
                 "x-content-type-options": "nosniff"},
                ["kokoro-issuer.session_token=secret; Path=/iam; HttpOnly; SameSite=Lax"],
            ),
            b"",
        )
        evidence = smoke.logout_header_evidence(response)
        self.assertEqual(evidence["set_cookie_count"], 1)
        self.assertEqual(evidence["content_type"], "html-utf8")
        self.assertTrue(evidence["content_security_policy_matches"])
        self.assertTrue(evidence["x_content_type_options_nosniff"])
        self.assertNotIn("secret", json.dumps(evidence))

    def test_logout_header_evidence_never_echoes_malicious_header_values(self):
        token = "header-bearer-token-should-never-print"
        response = smoke.HttpResponse(
            200,
            self.Headers({
                "content-type": "text/html; " + token,
                "content-security-policy": "default-src 'none'; report-uri /" + token,
                "x-content-type-options": token,
            }),
            b"",
        )
        rendered = json.dumps(smoke.logout_header_evidence(response))
        self.assertNotIn(token, rendered)
        self.assertEqual(json.loads(rendered), {
            "content_type": "other",
            "content_security_policy_matches": False,
            "x_content_type_options_nosniff": False,
            "set_cookie_count": 0,
        })

    def test_token_bundle_matches_scope_tenant_and_oidc_identity(self):
        issued, nonce = self.token_fixture()
        bundle = smoke.validate_token_bundle(issued, self.ready(), nonce)
        self.assertEqual(bundle.subject, "user-1")
        smoke.validate_userinfo({"sub": "user-1"}, bundle)

    def test_token_bundle_rejects_mutated_scope_and_access_claims(self):
        issued, nonce = self.token_fixture()
        cases = []
        cases.append({**issued, "scope": "openid"})
        access_claims = smoke.jwt_claims(issued["access_token"])
        for change in (
            {"iss": "https://evil.test/iam"},
            {"aud": "https://evil.test/resource"},
            {"sub": ""},
            {"client_id": "other-client"},
            {"scope": "openid"},
            {smoke.TOKEN_KIND_CLAIM: "machine"},
            {smoke.TENANT_CLAIM: "other-tenant"},
        ):
            cases.append({**issued, "access_token": self.jwt({**access_claims, **change})})
        for changed in cases:
            with self.subTest(changed=changed), self.assertRaises(smoke.SmokeError):
                smoke.validate_token_bundle(changed, self.ready(), nonce)

    def test_token_bundle_rejects_mutated_id_token_binding(self):
        issued, nonce = self.token_fixture()
        identity_claims = smoke.jwt_claims(issued["id_token"])
        for change in (
            {"iss": "https://evil.test/iam"},
            {"aud": "other-client"},
            {"aud": ["client", "other-client"]},
            {"nonce": "wrong"},
            {"sub": "other-user"},
        ):
            changed = {**issued, "id_token": self.jwt({**identity_claims, **change})}
            with self.subTest(change=change), self.assertRaises(smoke.SmokeError):
                smoke.validate_token_bundle(changed, self.ready(), nonce)

    def test_userinfo_is_bound_to_both_tokens(self):
        issued, nonce = self.token_fixture()
        bundle = smoke.validate_token_bundle(issued, self.ready(), nonce)
        for info in ({}, {"sub": "other-user"}, {"sub": ["user-1"]}):
            with self.subTest(info=info), self.assertRaises(smoke.SmokeError):
                smoke.validate_userinfo(info, bundle)

    def test_revoked_refresh_reuse_requires_exact_invalid_grant(self):
        good = smoke.HttpResponse(400, self.Headers({"content-type": "application/json"}), b'{"error":"invalid_grant"}')
        smoke.require_revoked_refresh_rejected(good)
        for response in (
            smoke.HttpResponse(200, self.Headers({"content-type": "application/json"}), b'{"access_token":"unexpected"}'),
            smoke.HttpResponse(400, self.Headers({"content-type": "application/json"}), b'{"error":"invalid_token"}'),
            smoke.HttpResponse(401, self.Headers({"content-type": "application/json"}), b'{"error":"invalid_grant"}'),
            smoke.HttpResponse(400, self.Headers({"content-type": "text/plain"}), b'{"error":"invalid_grant"}'),
        ):
            with self.subTest(status=response.status), self.assertRaises(smoke.SmokeError):
                smoke.require_revoked_refresh_rejected(response)

    def test_logout_requires_old_cookie_invalidation_even_without_cookie_deletion(self):
        self.assertEqual(smoke.logout_effect(False, True), "set-cookie-cleared")
        self.assertEqual(smoke.logout_effect(False, False), "server-session-invalidated")
        with self.assertRaises(smoke.SmokeError):
            smoke.logout_effect(True, True)
        with self.assertRaises(smoke.SmokeError):
            smoke.logout_effect(True, False)

    def test_cookie_jar_only_persists_issuer_and_rejects_malformed(self):
        jar = smoke.IssuerCookies()
        jar.update(["kokoro-issuer.session_token=abc; Path=/iam; HttpOnly; SameSite=Lax"])
        self.assertEqual(jar.header(), "kokoro-issuer.session_token=abc")
        with self.assertRaises(smoke.SmokeError):
            jar.update(["product-session=leak; Path=/; HttpOnly"])
        with self.assertRaises(smoke.SmokeError):
            jar.update(["kokoro-issuer.session_token=bad; Domain=evil.test; Path=/iam; HttpOnly; SameSite=Lax"])

    def test_finalize_stops_processes_before_scan_and_preserves_all_failure_labels(self):
        events = []
        def scan():
            events.append("scan")
            self.assertEqual(events[:2], ["stop", "stop"])
            raise smoke.SmokeError("Credential appeared in process log")

        failures = smoke.finalize(
            [Mock(), Mock()], lambda _: events.append("stop"),
            lambda: (_ for _ in ()).throw(RuntimeError("database secret")),
            lambda: events.append("verify"),
            lambda: events.append("inventory") or "snapshot", "snapshot",
            (("credential log scan", scan),),
        )
        self.assertEqual(events, ["stop", "stop", "scan", "verify", "inventory"])
        self.assertEqual(failures, ("credential log scan", "BFF database cleanup"))

    def test_primary_and_finalization_failures_are_aggregated_without_sensitive_values(self):
        secret = "sensitive-primary-or-cleanup-token"
        with self.assertRaises(smoke.SmokeError) as caught:
            smoke.raise_for_failures(
                "OAuth first grant",
                ("credential log scan", "BFF database cleanup"),
            )
        rendered = str(caught.exception)
        self.assertIn("primary: OAuth first grant", rendered)
        self.assertIn("finalize: credential log scan", rendered)
        self.assertIn("finalize: BFF database cleanup", rendered)
        self.assertNotIn(secret, rendered)
        with self.assertRaises(smoke.SmokeError) as unknown:
            smoke.raise_for_failures(secret, ("attacker=" + secret,))
        self.assertEqual(str(unknown.exception), "primary: unknown; finalize: unknown failed")

    def test_credential_registry_keeps_dynamic_values_and_cookie_history(self):
        credentials = smoke.CredentialRegistry("static-secret")
        jar = smoke.IssuerCookies(credentials.add)
        jar.update(["kokoro-issuer.session_token=cookie-secret; Path=/iam; HttpOnly; SameSite=Lax"])
        jar.update(["kokoro-issuer.session_token=; Max-Age=0; Path=/iam; HttpOnly; SameSite=Lax"])
        credentials.add("authorization-code", "verifier", "Basic encoded", "access", "refresh", "identity")
        self.assertEqual(
            set(credentials.values()),
            {"static-secret", "cookie-secret", "authorization-code", "verifier", "Basic encoded", "access", "refresh", "identity"},
        )

    def test_log_scan_reports_no_credential_value(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "process.log"
            path.write_text("ordinary diagnostic")
            smoke.assert_log_clean(path, ("sensitive-token", "authorization/code"))
            path.write_text("ordinary diagnostic sensitive-token")
            with self.assertRaises(smoke.SmokeError) as caught:
                smoke.assert_log_clean(path, ("sensitive-token",))
            self.assertNotIn("sensitive-token", str(caught.exception))
            path.write_text("ordinary diagnostic authorization%2Fcode")
            with self.assertRaises(smoke.SmokeError):
                smoke.assert_log_clean(path, ("authorization/code",))

    def test_native_session_and_error_are_classified_without_payload_logging(self):
        response = lambda status, body, content_type="application/json": smoke.HttpResponse(
            status, self.Headers({"content-type": content_type}), body
        )
        self.assertTrue(smoke.session_present(response(200, b'{"user":{"id":"u"}}')))
        self.assertFalse(smoke.session_present(response(200, b"null")))
        self.assertEqual(smoke.native_error_code(response(401, b'{"error":"invalid_token"}')), "invalid_token")
        self.assertIsNone(smoke.native_error_code(response(401, b'{"error":"secret value with spaces"}')))
        with self.assertRaises(smoke.SmokeError):
            smoke.session_present(response(401, b"null"))
        for content_type in ("text/plain", "application/problem+json", "application/json; profile=token"):
            with self.subTest(content_type=content_type), self.assertRaises(smoke.SmokeError):
                smoke.session_present(response(200, b"null", content_type))
            with self.subTest(content_type=content_type), self.assertRaises(smoke.SmokeError):
                smoke.native_error_code(response(401, b'{"error":"invalid_token"}', content_type))

    def test_all_native_json_parsers_require_exact_json_content_type(self):
        ready = self.ready()
        good_headers = self.Headers({"content-type": "application/json; charset=utf-8"})
        self.assertEqual(smoke.HttpResponse(200, good_headers, b'{"ok":true}').json(), {"ok": True})
        self.assertEqual(
            smoke.redirect_result(
                smoke.HttpResponse(
                    200,
                    good_headers,
                    b'{"redirect":true,"url":"https://web.example.test/auth/consent?sig=x"}',
                ),
                "continuation",
            ),
            "https://web.example.test/auth/consent?sig=x",
        )
        for content_type in (None, "text/plain", "application/problem+json", "application/json; profile=secret"):
            headers = self.Headers({} if content_type is None else {"content-type": content_type})
            with self.subTest(content_type=content_type), self.assertRaises(smoke.SmokeError):
                smoke.HttpResponse(200, headers, b'{"ok":true}').json()
            with self.subTest(content_type=content_type), self.assertRaises(smoke.SmokeError):
                smoke.classify_logout_response(
                    smoke.HttpResponse(
                        200,
                        headers,
                        b'{"redirect":true,"url":"https://web.example.test/auth/sign-in?state=logout-state"}',
                    ),
                    ready,
                    "logout-state",
                )


if __name__ == "__main__":
    unittest.main()
