"""Guards for the browser-facing, three-process OIDC smoke harness."""

import importlib.util
import base64
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
import tempfile
from threading import Thread
import unittest
from unittest.mock import patch

PATH = Path(__file__).resolve().parents[1] / "e2e" / "run_web_bff_iam_oidc_smoke.py"
sys.path.insert(0, str(PATH.parent))
spec = importlib.util.spec_from_file_location("web_bff_iam_oidc_smoke", PATH)
smoke = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = smoke
spec.loader.exec_module(smoke)


class BrowserGuards(unittest.TestCase):
    def test_https_browser_supports_authenticated_json_request_headers(self):
        captured = []

        class Response:
            status = 202

            def read(self, _limit):
                return b"{}"

            def getheaders(self):
                return [("content-type", "application/json")]

        class Connection:
            def __init__(self, *args, **kwargs):
                pass

            def request(self, method, target, body=None, headers=None):
                captured.append((method, target, body, headers))

            def getresponse(self):
                return Response()

            def close(self):
                pass

        with patch.object(smoke.http.client, "HTTPSConnection", Connection):
            response = smoke.https_browser(
                443,
                "/api/session/sessions/conv/messages",
                "https://web.example.test",
                method="POST",
                json_body={"content": "hello"},
                idempotency_key="message-1",
                accept="application/json",
            )
        self.assertEqual(response.status, 202)
        self.assertEqual(
            captured,
            [
                (
                    "POST",
                    "/api/session/sessions/conv/messages",
                    b'{"content":"hello"}',
                    {
                        "Host": "web.example.test",
                        "Accept": "application/json",
                        "Content-Type": "application/json",
                        "Idempotency-Key": "message-1",
                    },
                )
            ],
        )

    def test_https_browser_rejects_form_and_json_together(self):
        with self.assertRaisesRegex(smoke.SmokeError, "form and JSON"):
            smoke.https_browser(
                443,
                "/api/session/sessions/conv/messages",
                "https://web.example.test",
                method="POST",
                form={"content": "form"},
                json_body={"content": "json"},
            )

    def test_cookie_path_and_deletion(self):
        jar = smoke.BrowserCookies()
        jar.update(
            "/iam/sign-in/email",
            [
                "kokoro-issuer.session_token=issuer; Path=/iam; HttpOnly; SameSite=Lax",
                "next-auth.state=state; Path=/; HttpOnly; SameSite=Lax",
                "interaction=proof; Path=/auth/sign-in; HttpOnly; SameSite=Lax",
            ],
        )
        self.assertIn(
            "kokoro-issuer.session_token=issuer", jar.header("/iam/oauth2/authorize")
        )
        self.assertNotIn(
            "interaction=proof", jar.header("/api/auth/callback/kokoro-iam")
        )
        self.assertNotIn(
            "kokoro-issuer.session_token", jar.header("/api/auth/callback/kokoro-iam")
        )
        self.assertIn(
            "next-auth.state=state", jar.header("/api/auth/callback/kokoro-iam")
        )
        jar.update(
            "/iam/sign-in/email",
            [
                "kokoro-issuer.session_token=; Path=/iam; Max-Age=0; HttpOnly; SameSite=Lax",
            ],
        )
        self.assertNotIn(
            "kokoro-issuer.session_token", jar.header("/iam/oauth2/authorize")
        )

    def test_cookie_rejects_domain_and_duplicate(self):
        jar = smoke.BrowserCookies()
        with self.assertRaises(smoke.SmokeError):
            jar.update("/", ["session=bad; Domain=evil.test; Path=/"])
        with self.assertRaises(smoke.SmokeError):
            jar.update("/", ["a=1; Path=/", "a=2; Path=/"])

    def test_navigation_stays_on_canonical_web_origin(self):
        self.assertEqual(
            smoke.browser_target("/iam/oauth2/authorize?x=1"),
            "/iam/oauth2/authorize?x=1",
        )
        self.assertEqual(
            smoke.browser_target("https://web.example.test/auth/consent?sig=x"),
            "/auth/consent?sig=x",
        )
        for target in (
            "https://evil.test/",
            "http://web.example.test/",
            "//evil.test/",
            "/foo#fragment",
            "/%2f/other",
        ):
            with self.subTest(target=target), self.assertRaises(smoke.SmokeError):
                smoke.browser_target(target)

    def test_native_authorize_redirect_has_exact_wire_shape(self):
        target = "https://web.example.test/auth/sign-in?sig=signed"
        native = smoke.BrowserResponse(
            200,
            {"content-type": "application/json; charset=utf-8"},
            [],
            ('{"redirect":true,"url":"' + target + '"}').encode(),
        )
        self.assertEqual(smoke.navigation_location(native, "authorize"), target)
        self.assertEqual(
            smoke.browser_target(smoke.navigation_location(native, "authorize")),
            "/auth/sign-in?sig=signed",
        )
        for body in (
            b'{"redirect":true,"url":"/auth/sign-in?sig=x","extra":1}',
            b'{"redirect":"true","url":"/auth/sign-in?sig=x"}',
            b'{"redirect":true,"url":1}',
        ):
            with self.subTest(body=body), self.assertRaises(smoke.SmokeError):
                smoke.navigation_location(
                    smoke.BrowserResponse(200, native.headers, [], body), "authorize"
                )

    def test_callback_never_establishes_product_session(self):
        good = smoke.BrowserResponse(
            503,
            {"content-type": "application/json"},
            ["next-auth.session-token=; Path=/; Max-Age=0"],
            b'{"error":{"code":"product_session_unavailable"}}',
        )
        smoke.require_unavailable_session(good)
        for response in (
            smoke.BrowserResponse(302, {"location": "/app"}, [], b""),
            smoke.BrowserResponse(
                503,
                {"content-type": "application/json"},
                ["next-auth.session-token=secret; Path=/"],
                good.body,
            ),
            smoke.BrowserResponse(
                503,
                {"content-type": "application/json"},
                ["__Secure-next-auth.session-token.0=secret; Path=/"],
                good.body,
            ),
            smoke.BrowserResponse(
                503,
                {"content-type": "application/json"},
                [],
                b'{"error":{"code":"something_else"}}',
            ),
        ):
            with self.assertRaises(smoke.SmokeError):
                smoke.require_unavailable_session(response)
        jar = smoke.BrowserCookies()
        jar.update(
            "/", ["__Secure-next-auth.session-token.1=secret; Path=/; Secure; HttpOnly"]
        )
        self.assertTrue(jar.has_usable_session())

    def test_cookie_expiry_precedence_empty_and_chunked_session(self):
        jar = smoke.BrowserCookies()
        jar.update(
            "/",
            [
                "a=old; Path=/",
                "empty=; Path=/",
                "__Secure-next-auth.session-token.0=chunk; Path=/",
            ],
        )
        self.assertIn("empty=", jar.header("/"))
        self.assertTrue(jar.has_usable_session())
        jar.update(
            "/",
            [
                "a=new; Path=/; Max-Age=10; Expires=Thu, 01 Jan 1970 00:00:00 GMT",
                "__Secure-next-auth.session-token.0=; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT",
            ],
        )
        self.assertIn("a=new", jar.header("/"))
        self.assertFalse(jar.has_usable_session())
        jar.update("/", ["a=gone; Path=/; Max-Age=-1"])
        self.assertNotIn("a=", jar.header("/"))
        jar.update("/", ["next-auth.session-token=; Path=/"])
        self.assertFalse(jar.has_usable_session())

    def test_form_validates_post_method_and_exact_action(self):
        body = b'<form method="post" action="/auth/sign-in?sig=x&amp;ba_param=y"><input type="hidden" name="csrf_token" value="proof"></form>'
        response = smoke.BrowserResponse(
            200, {"content-type": "text/html; charset=utf-8"}, [], body
        )
        self.assertEqual(
            smoke.form_inputs(response, "/auth/sign-in?sig=x&ba_param=y").hidden[
                "csrf_token"
            ],
            "proof",
        )
        for bad in (
            body.replace(b'method="post"', b'method="get"'),
            body.replace(b"/auth/sign-in?", b"https://evil.test/auth/sign-in?"),
            body.replace(b"/auth/sign-in?", b"/auth/consent?"),
        ):
            with self.subTest(body=bad), self.assertRaises(smoke.SmokeError):
                smoke.form_inputs(
                    smoke.BrowserResponse(200, response.headers, [], bad),
                    "/auth/sign-in?sig=x&ba_param=y",
                )

    def test_query_registry_captures_nonce_and_signed_interaction(self):
        registry = smoke.previous.CredentialRegistry()
        smoke.remember_sensitive_query(
            "/iam/oauth2/authorize?nonce=nonce-secret-123456&state=state-secret-123456",
            registry,
        )
        smoke.remember_sensitive_query(
            "/auth/consent?sig=signed-secret-123456&ba_param=opaque-secret-123456",
            registry,
        )
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "log"
            for secret in (
                "nonce-secret-123456",
                "signed-secret-123456",
                "opaque-secret-123456",
            ):
                log.write_text("diagnostic " + secret)
                with (
                    self.subTest(secret=secret),
                    self.assertRaises(smoke.previous.SmokeError),
                ):
                    smoke.previous.assert_log_clean(log, registry.values())

    def test_token_proxy_registry_catches_dynamic_response_and_basic(self):
        registry = smoke.previous.CredentialRegistry()
        basic = base64.b64encode(b"client:secret-generated-at-runtime").decode()
        tokens = {
            "access_token": "access-generated-at-runtime",
            "refresh_token": "refresh-generated-at-runtime",
            "id_token": "identity-generated-at-runtime",
        }
        smoke.capture_token_response(
            registry,
            "Basic " + basic,
            200,
            "application/json; charset=utf-8",
            json.dumps(tokens).encode(),
        )
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "log"
            for secret in (*tokens.values(), basic):
                with self.subTest(secret=secret):
                    log.write_text("process diagnostic " + secret)
                    with self.assertRaises(smoke.previous.SmokeError):
                        smoke.previous.assert_log_clean(log, registry.values())
        other = smoke.previous.CredentialRegistry()
        smoke.capture_token_response(
            other,
            "Basic " + basic,
            503,
            "application/json",
            json.dumps(tokens).encode(),
        )
        self.assertEqual(other.values(), ())

    def test_proxy_registers_only_exact_bff_token_success(self):
        secret = "dynamic-token-from-exact-path"

        class Upstream(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def do_POST(self):
                payload = json.dumps({"access_token": secret}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

        upstream = ThreadingHTTPServer(("127.0.0.1", 0), Upstream)
        worker = Thread(target=upstream.serve_forever, daemon=True)
        worker.start()
        registry = smoke.previous.CredentialRegistry()
        proxy = smoke.Proxy(upstream.server_port, credentials=registry)
        try:
            for path in ("/other", "/iam/oauth2/token?extra=1"):
                connection = http.client.HTTPConnection("127.0.0.1", proxy.server_port)
                connection.request("POST", path)
                self.assertEqual(connection.getresponse().status, 200)
                connection.close()
            self.assertEqual(registry.values(), ())
            connection = http.client.HTTPConnection("127.0.0.1", proxy.server_port)
            connection.request("POST", "/iam/oauth2/token")
            self.assertEqual(connection.getresponse().status, 200)
            connection.close()
            self.assertIn(secret, registry.values())
        finally:
            proxy.close()
            upstream.shutdown()
            upstream.server_close()
            worker.join(timeout=5)

    def test_oidc_query_requires_exact_single_values(self):
        expected = {"code", "state", "iss"}
        self.assertEqual(
            smoke.single_query_values("/callback?code=x&state=y&iss=z", expected),
            {"code": "x", "state": "y", "iss": "z"},
        )
        for query in (
            "code=x&code=q&state=y&iss=z",
            "code=x&state=y",
            "code=x&state=y&iss=",
            "code=x&state=y&iss=z&other=a",
        ):
            with self.subTest(query=query), self.assertRaises(smoke.SmokeError):
                smoke.single_query_values("/callback?" + query, expected)

    def test_iam_inventory_uses_only_ready_identity(self):
        commands = []
        ready = smoke.previous.Ready(
            "http://127.0.0.1:1234",
            "iam_web_oidc_" + "a" * 32,
            "iam:test:web-oidc-flow-host:12345678-1234-1234-1234-123456789abc:",
            "https://web.example.test/iam",
            "client",
            "secret",
            "https://web.example.test/api/auth/callback/kokoro-iam",
            "https://web.example.test/auth/sign-in",
            "user@example.test",
            "password",
            "tenant",
        )

        def command(args):
            commands.append(args)
            return (
                ready.database_name if args[0] == "psql" else ready.redis_prefix + "key"
            )

        resources = smoke.runtime.OwnedResources(
            "postgresql://localhost/postgres",
            "redis://localhost:6379",
            "a" * 24,
            command=command,
        )
        databases, keys = smoke.iam_owned_inventory(resources, ready)
        self.assertEqual(databases, {ready.database_name})
        self.assertEqual(keys, {ready.redis_prefix + "key"})
        self.assertTrue(
            all("iam_web_oidc_%" not in " ".join(args) for args in commands)
        )
        self.assertTrue(
            all(
                "iam:test:web-oidc-flow-host:*" not in " ".join(args)
                for args in commands
            )
        )

    def test_named_iam_identity_is_deterministic(self):
        identity = smoke.named_iam_identity("12345678-1234-4234-8234-123456789abc")
        self.assertEqual(
            identity.database_name, "iam_web_oidc_12345678123442348234123456789abc"
        )
        self.assertEqual(
            identity.redis_prefix,
            "iam:test:web-oidc-flow-host:12345678-1234-4234-8234-123456789abc:",
        )
        with self.assertRaises(smoke.SmokeError):
            smoke.named_iam_identity("12345678-1234-4234-8234-123456789ABC")

    def test_pre_ready_owned_cleanup_and_foreign_collision(self):
        identity = smoke.named_iam_identity("12345678-1234-4234-8234-123456789abc")
        marker = identity.redis_prefix + "fixture-owner"
        token = "a" * 32

        def fixture(owner):
            commands = []
            database = {identity.database_name}
            keys = {marker: owner, identity.redis_prefix + "state": "value"}

            def command(args):
                commands.append(args)
                if args[0] == "psql":
                    if "DROP DATABASE" in args[-1]:
                        database.clear()
                        return ""
                    return identity.database_name if database else ""
                if "--scan" in args:
                    return "\n".join(keys)
                if "GET" in args:
                    return keys.get(args[-1], "")
                if "UNLINK" in args:
                    for key in args[args.index("UNLINK") + 1 :]:
                        keys.pop(key, None)
                return ""

            resources = smoke.runtime.OwnedResources(
                "postgresql://localhost/postgres",
                "redis://localhost:6379",
                "b" * 24,
                command=command,
            )
            return resources, commands, database, keys

        resources, commands, database, keys = fixture(token)
        smoke.reconcile_iam_identity(resources, identity, token)
        self.assertEqual((database, keys), (set(), {}))
        self.assertLess(
            next(i for i, args in enumerate(commands) if "DROP DATABASE" in args[-1]),
            next(
                i
                for i, args in enumerate(commands)
                if "UNLINK" in args and marker in args
            ),
        )
        resources, commands, database, keys = fixture("foreign-owner")
        with self.assertRaises(smoke.SmokeError):
            smoke.reconcile_iam_identity(resources, identity, token)
        self.assertEqual(database, {identity.database_name})
        self.assertIn(marker, keys)
        self.assertFalse(
            any("DROP DATABASE" in args[-1] or "UNLINK" in args for args in commands)
        )
        resources, commands, database, keys = fixture("")
        with self.assertRaises(smoke.SmokeError):
            smoke.reconcile_iam_identity(resources, identity, token)
        self.assertEqual(database, {identity.database_name})
        self.assertFalse(
            any("DROP DATABASE" in args[-1] or "UNLINK" in args for args in commands)
        )

    def test_named_iam_drop_failure_retains_owner_marker(self):
        identity = smoke.named_iam_identity("12345678-1234-4234-8234-123456789abc")
        marker = identity.redis_prefix + "fixture-owner"
        token = "a" * 32
        commands = []

        def command(args):
            commands.append(args)
            if args[0] == "psql":
                if "DROP DATABASE" in args[-1]:
                    raise smoke.runtime.SmokeError("injected drop failure")
                return identity.database_name
            if "--scan" in args:
                return marker
            if "GET" in args:
                return token
            return ""

        resources = smoke.runtime.OwnedResources(
            "postgresql://localhost/postgres",
            "redis://localhost:6379",
            "b" * 24,
            command=command,
        )
        with self.assertRaises(smoke.runtime.SmokeError):
            smoke.reconcile_iam_identity(resources, identity, token)
        self.assertFalse(any("UNLINK" in args for args in commands))

    def test_database_cleanup_runs_after_create_readback_failure(self):
        # The ownership helper records a request before create/readback; cleanup must not depend on a returned URL.
        source = PATH.read_text()
        self.assertNotIn("if created_db:", source)
        self.assertIn("resources.cleanup()", source)

    def test_no_premature_passed_status(self):
        source = PATH.read_text()
        self.assertNotIn('"stage": stage, "status": "passed"', source)

    def test_isolated_next_keeps_turbopack_root_inside_fixture_parent(self):
        with tempfile.TemporaryDirectory(
            prefix="web-smoke-unit-", dir=smoke.ROOT.parent
        ) as directory:
            next_root = smoke.isolated_next(Path(directory))
            self.assertTrue((next_root / "node_modules").is_symlink())
            config = (next_root / "next.config.ts").read_text()
            self.assertIn(f'root: "{smoke.ROOT.parent}"', config)
            self.assertNotIn("root: process.cwd()", config)


if __name__ == "__main__":
    unittest.main()
