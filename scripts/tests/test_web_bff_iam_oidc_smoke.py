"""Guards for the browser-facing, three-process OIDC smoke harness."""

import importlib.util
from contextlib import contextmanager
import base64
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
import socket
import ssl
import tempfile
import time
from threading import Event, Thread
import unittest
from unittest.mock import patch

PATH = Path(__file__).resolve().parents[1] / "e2e" / "run_web_bff_iam_oidc_smoke.py"
sys.path.insert(0, str(PATH.parent))
spec = importlib.util.spec_from_file_location("web_bff_iam_oidc_smoke", PATH)
smoke = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = smoke
spec.loader.exec_module(smoke)


class HmrProxyTests(unittest.TestCase):
    REQUEST = (
        b"GET /_next/webpack-hmr?session=fixture HTTP/1.1\r\n"
        b"Host: web.example.test\r\nConnection: keep-alive, Upgrade\r\n"
        b"Upgrade: websocket\r\nSec-WebSocket-Version: 13\r\n"
        b"Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n\r\n"
    )
    RESPONSE = (
        b"HTTP/1.1 101 Switching Protocols\r\n"
        b"Connection: Upgrade\r\nUpgrade: websocket\r\n"
        b"Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=\r\n\r\n"
    )

    @staticmethod
    def read_head(client):
        head = bytearray()
        while not head.endswith(b"\r\n\r\n"):
            part = client.recv(1)
            if not part:
                break
            head.extend(part)
        return bytes(head)

    @contextmanager
    def fixture(self, respond, *, enabled=True):
        observed = []
        errors = []

        class Upstream(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *_args):
                pass

            def do_GET(self):
                self.connection.settimeout(3)
                self.close_connection = True
                observed.append(self.path)
                try:
                    respond(self)
                except Exception as error:
                    errors.append(error)

            do_POST = do_GET

        upstream = ThreadingHTTPServer(("127.0.0.1", 0), Upstream)
        worker = Thread(target=upstream.serve_forever, daemon=True)
        worker.start()
        proxy = None
        try:
            with tempfile.TemporaryDirectory() as directory:
                proxy = smoke.Proxy(
                    upstream.server_port,
                    "web.example.test",
                    smoke.certificate(Path(directory), "web.example.test"),
                    hmr_websocket=enabled,
                )
                yield proxy, observed
        finally:
            if proxy is not None:
                proxy.close()
            upstream.shutdown()
            upstream.server_close()
            worker.join(timeout=5)
        self.assertFalse(worker.is_alive())
        self.assertEqual(errors, [])

    @contextmanager
    def client(self, proxy):
        with socket.create_connection(
            ("127.0.0.1", proxy.server_port), timeout=3
        ) as raw:
            with ssl._create_unverified_context().wrap_socket(
                raw, server_hostname="web.example.test"
            ) as client:
                yield client

    def test_enabled_proxy_keeps_ordinary_read_budget_separate_from_hmr_connect(self):
        def respond(handler):
            Event().wait(0.1)
            handler.connection.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n")

        with patch.object(smoke, "HMR_CONNECT_SECONDS", 0.02):
            with self.fixture(respond) as (proxy, _):
                with self.client(proxy) as client:
                    client.sendall(b"GET /ordinary HTTP/1.1\r\nHost: fixture\r\n\r\n")
                    self.assertTrue(self.read_head(client).startswith(b"HTTP/1.1 200 "))

    def test_enabled_proxy_preserves_ordinary_fragmented_post_body(self):
        payload = bytes(range(256)) * 1024
        received = []

        def respond(handler):
            received.append(handler.rfile.read(int(handler.headers["Content-Length"])))
            handler.connection.sendall(
                b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nOK"
            )

        with self.fixture(respond) as (proxy, _):
            with self.client(proxy) as client:
                client.sendall(
                    f"POST /ordinary HTTP/1.1\r\nHost: fixture\r\nContent-Length: {len(payload)}\r\n\r\n".encode()
                    + payload[:1]
                )
                # Send the body across multiple TLS records, not one raw read.
                client.sendall(payload[1:65536])
                client.sendall(payload[65536:])
                self.assertTrue(self.read_head(client).startswith(b"HTTP/1.1 200 "))
                self.assertEqual(client.recv(2), b"OK")
        self.assertEqual(received, [payload])

    def test_enabled_proxy_rejects_truncated_body_before_opening_upstream(self):
        with self.fixture(lambda _: None) as (proxy, observed):
            with self.client(proxy) as client:
                client.sendall(
                    b"POST /ordinary HTTP/1.1\r\nHost: fixture\r\nContent-Length: 100\r\n\r\nx"
                )
            proxy.close()
            self.assertEqual(observed, [])

    def test_hmr_connection_limit_rejects_excess_without_spawning_handler(self):
        with patch.object(smoke, "HMR_MAX_CONNECTIONS", 1):
            with self.fixture(lambda _: None) as (proxy, _):
                with socket.create_connection(
                    ("127.0.0.1", proxy.server_port), timeout=2
                ):
                    deadline = time.monotonic() + 1
                    while not proxy.hmr_threads and time.monotonic() < deadline:
                        time.sleep(0.01)
                    self.assertEqual(len(proxy.hmr_threads), 1)
                    with socket.create_connection(
                        ("127.0.0.1", proxy.server_port), timeout=2
                    ) as excess:
                        self.assertEqual(excess.recv(1), b"")
                    self.assertEqual(len(proxy.hmr_threads), 1)

    def test_hmr_client_header_bytes_and_time_are_bounded(self):
        for request in (b"GET /" + b"x" * 1024, b"GET /"):
            with (
                patch.object(smoke, "HMR_HEADER_BYTES", 512),
                patch.object(smoke, "HMR_HEADER_SECONDS", 0.2),
            ):
                with self.fixture(lambda _: None) as (proxy, observed):
                    with self.client(proxy) as client:
                        client.sendall(request)
                        self.assertEqual(client.recv(1), b"")
                        self.assertEqual(observed, [])

    def test_enabled_proxy_preserves_sse_streaming_before_upstream_finishes(self):
        release = Event()

        def respond(handler):
            handler.connection.sendall(
                b"HTTP/1.1 200 OK\r\nContent-Type: text/event-stream\r\n"
                b"Transfer-Encoding: chunked\r\n\r\n9\r\ndata: 1\n\n\r\n"
            )
            release.wait(2)
            handler.connection.sendall(b"0\r\n\r\n")

        with self.fixture(respond) as (proxy, _):
            proxy.stream_sse = True
            try:
                with self.client(proxy) as client:
                    client.sendall(
                        b"GET /api/session/sessions/fixture/events HTTP/1.1\r\nHost: fixture\r\n\r\n"
                    )
                    self.assertTrue(self.read_head(client).startswith(b"HTTP/1.1 200 "))
                    body = bytearray()
                    while b"data: 1" not in body:
                        part = client.recv(4096)
                        self.assertTrue(part)
                        body.extend(part)
                    release.set()
                    while part := client.recv(4096):
                        body.extend(part)
                    self.assertTrue(body.endswith(b"0\r\n\r\n"))
            finally:
                release.set()

    def test_enabled_proxy_keeps_ordinary_body_limit(self):
        with self.fixture(lambda _: None) as (proxy, observed):
            with self.client(proxy) as client:
                client.sendall(
                    f"POST /ordinary HTTP/1.1\r\nHost: fixture\r\nContent-Length: {smoke.MAX_BODY + 1}\r\n\r\n".encode()
                )
                self.assertTrue(self.read_head(client).startswith(b"HTTP/1.1 413 "))
            self.assertEqual(observed, [])

    def test_hmr_nonreading_client_is_closed_at_total_budget(self):
        disconnected = Event()

        def respond(handler):
            handler.connection.sendall(self.RESPONSE)
            try:
                # Exceeds socket windows; the proxy must not buffer without limit.
                for _ in range(512):
                    handler.connection.sendall(b"x" * 65536)
            except (BrokenPipeError, ConnectionResetError):
                disconnected.set()

        with patch.object(smoke, "HMR_TOTAL_SECONDS", 0.2):
            with self.fixture(respond) as (proxy, _):
                with self.client(proxy) as client:
                    client.sendall(self.REQUEST)
                    self.assertTrue(self.read_head(client).startswith(b"HTTP/1.1 101 "))
                    self.assertTrue(disconnected.wait(2))
                proxy.close()
                self.assertFalse(any(thread.is_alive() for thread in proxy.hmr_threads))

    def test_hmr_disabled_retains_http_response_and_no_connection_upgrade(self):
        connections = []

        def respond(handler):
            connections.append(handler.headers.get("Connection"))
            handler.connection.sendall(
                b"HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\n\r\n"
            )

        with self.fixture(respond, enabled=False) as (proxy, observed):
            with self.client(proxy) as client:
                client.sendall(self.REQUEST)
                self.assertTrue(self.read_head(client).startswith(b"HTTP/1.1 404 "))
        self.assertEqual(connections, [None])
        self.assertEqual(len(observed), 1)

    def test_hmr_rejects_wrong_path_method_and_invalid_client_handshake_before_upstream(
        self,
    ):
        invalid = [
            self.REQUEST.replace(b"/_next/webpack-hmr?session=fixture", path)
            for path in (
                b"/_next/webpack-hmr/",
                b"/other",
                b"//_next/webpack-hmr",
                b"/_next/%77ebpack-hmr",
            )
        ] + [
            self.REQUEST.replace(b"GET ", b"POST ", 1),
            self.REQUEST.replace(b"HTTP/1.1", b"HTTP/1.0", 1),
            self.REQUEST.replace(b"keep-alive, Upgrade", b"keep-alive"),
            self.REQUEST.replace(b"Upgrade: websocket", b"Upgrade: h2c"),
            self.REQUEST.replace(
                b"Sec-WebSocket-Version: 13", b"Sec-WebSocket-Version: 12"
            ),
            self.REQUEST.replace(b"dGhlIHNhbXBsZSBub25jZQ==", b"invalid"),
            self.REQUEST.replace(
                b"\r\n\r\n", b"\r\nSec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n\r\n"
            ),
            self.REQUEST.replace(b"\r\n\r\n", b"\r\nContent-Length: 1\r\n\r\nx"),
            self.REQUEST.replace(
                b"\r\n\r\n", b"\r\nTransfer-Encoding: chunked\r\n\r\n"
            ),
        ]
        with self.fixture(lambda _: None) as (proxy, observed):
            for request in invalid:
                with (
                    self.subTest(request=request.split(b"\r\n")[0]),
                    self.client(proxy) as client,
                ):
                    client.sendall(request)
                    self.assertTrue(self.read_head(client).startswith(b"HTTP/1.1 400 "))
            self.assertEqual(observed, [])

    def test_hmr_rejects_invalid_upstream_without_committing_101(self):
        responses = [
            self.RESPONSE.replace(b"101 Switching Protocols", b"200 OK"),
            self.RESPONSE.replace(b"Upgrade: websocket", b"Upgrade: h2c"),
            self.RESPONSE.replace(b"Connection: Upgrade", b"Connection: close"),
            self.RESPONSE.replace(b"s3pPLMBiTxaQ9kYGzzhZRbK+xOo=", b"invalid"),
            self.RESPONSE.replace(
                b"\r\n\r\n", b"\r\nSec-WebSocket-Accept: duplicate\r\n\r\n"
            ),
            self.RESPONSE.replace(
                b"\r\n\r\n", b"\r\nSec-WebSocket-Extensions: permessage-deflate\r\n\r\n"
            ),
            self.RESPONSE.replace(b"\r\n\r\n", b"\r\nContent-Length: 0\r\n\r\n"),
            b"HTTP/1.1 101 Switching Protocols\r\nBroken\r\n\r\n",
        ]
        for response in responses:
            with self.subTest(response=response.split(b"\r\n")[0]):
                with self.fixture(
                    lambda handler: handler.connection.sendall(response)
                ) as (proxy, _):
                    with self.client(proxy) as client:
                        client.sendall(self.REQUEST)
                        head = self.read_head(client)
                        self.assertTrue(head.startswith(b"HTTP/1.1 502 "), head)
                        self.assertNotIn(b"101 Switching", head)

    def test_hmr_tls_pending_and_backpressure_preserve_large_binary_transfer(self):
        payload = bytes(range(256)) * 1024
        received = []

        def respond(handler):
            handler.connection.sendall(self.RESPONSE)
            received.append(handler.rfile.read(len(payload)))
            handler.connection.sendall(payload)

        with self.fixture(respond) as (proxy, _):
            with self.client(proxy) as client:
                client.sendall(self.REQUEST + payload)
                self.assertTrue(self.read_head(client).startswith(b"HTTP/1.1 101 "))
                result = bytearray()
                while part := client.recv(4096):
                    result.extend(part)
                self.assertEqual(result, payload)
        self.assertEqual(received, [payload])

    def test_hmr_client_disconnect_releases_upstream_and_handler(self):
        disconnected = Event()

        def respond(handler):
            handler.connection.sendall(self.RESPONSE)
            if not handler.rfile.read(1):
                disconnected.set()

        with self.fixture(respond) as (proxy, _):
            with self.client(proxy) as client:
                client.sendall(self.REQUEST)
                self.assertTrue(self.read_head(client).startswith(b"HTTP/1.1 101 "))
            self.assertTrue(disconnected.wait(2))
            proxy.close()
            self.assertFalse(any(thread.is_alive() for thread in proxy.hmr_threads))
            self.assertEqual(proxy.hmr_sockets, set())

    def test_hmr_proxy_close_reaps_open_tunnel_and_upstream_handshake(self):
        for handshake in (True, False):
            accepted = Event()
            disconnected = Event()

            def respond(handler):
                if handshake:
                    handler.connection.sendall(self.RESPONSE)
                accepted.set()
                if not handler.rfile.read(1):
                    disconnected.set()

            with self.subTest(handshake=handshake), self.fixture(respond) as (proxy, _):
                with self.client(proxy) as client:
                    client.sendall(self.REQUEST)
                    self.assertTrue(accepted.wait(1))
                    if handshake:
                        self.assertTrue(
                            self.read_head(client).startswith(b"HTTP/1.1 101 ")
                        )
                    proxy.close()
                    self.assertEqual(client.recv(1), b"")
                    self.assertTrue(disconnected.wait(1))
                    self.assertEqual(proxy.hmr_sockets, set())
                    self.assertFalse(
                        any(thread.is_alive() for thread in proxy.hmr_threads)
                    )

    def test_enabled_proxy_close_reaps_stalled_ordinary_http_upstream(self):
        accepted = Event()
        disconnected = Event()

        def respond(handler):
            accepted.set()
            if not handler.rfile.read(1):
                disconnected.set()

        with self.fixture(respond) as (proxy, _):
            with self.client(proxy) as client:
                client.sendall(b"GET /ordinary HTTP/1.1\r\nHost: fixture\r\n\r\n")
                self.assertTrue(accepted.wait(1))
                proxy.close()
                self.assertEqual(client.recv(1), b"")
                self.assertTrue(disconnected.wait(1))
                self.assertFalse(any(thread.is_alive() for thread in proxy.hmr_threads))
                self.assertEqual(proxy.hmr_sockets, set())

    def test_hmr_proxy_close_reaps_unfinished_tls_handshake(self):
        with self.fixture(lambda _: None) as (proxy, observed):
            with socket.create_connection(
                ("127.0.0.1", proxy.server_port), timeout=2
            ) as client:
                deadline = time.monotonic() + 1
                while not proxy.hmr_threads and time.monotonic() < deadline:
                    time.sleep(0.01)
                self.assertTrue(proxy.hmr_threads)
                proxy.close()
                self.assertEqual(client.recv(1), b"")
                self.assertFalse(any(thread.is_alive() for thread in proxy.hmr_threads))
                self.assertEqual(observed, [])

    def test_hmr_idle_and_total_budgets_close_real_upstream(self):
        for name in ("HMR_IDLE_SECONDS", "HMR_TOTAL_SECONDS"):
            disconnected = Event()

            def respond(handler):
                handler.connection.sendall(self.RESPONSE)
                if not handler.rfile.read(1):
                    disconnected.set()

            with self.subTest(budget=name), patch.object(smoke, name, 0.1):
                with self.fixture(respond) as (proxy, _):
                    with self.client(proxy) as client:
                        client.sendall(self.REQUEST)
                        self.assertTrue(
                            self.read_head(client).startswith(b"HTTP/1.1 101 ")
                        )
                        self.assertEqual(client.recv(1), b"")
                        self.assertTrue(disconnected.wait(1))

    def test_hmr_upstream_header_bytes_and_time_are_bounded(self):
        for response in (b"HTTP/1.1 101 " + b"x" * 1024, b"HTTP/1.1 101 "):
            disconnected = Event()

            def respond(handler):
                handler.connection.sendall(response)
                try:
                    self.assertEqual(handler.rfile.read(1), b"")
                except ConnectionResetError:
                    pass
                disconnected.set()

            with (
                patch.object(smoke, "HMR_HEADER_BYTES", 512),
                patch.object(smoke, "HMR_HEADER_SECONDS", 0.2),
            ):
                with self.fixture(respond) as (proxy, _):
                    with self.client(proxy) as client:
                        client.sendall(self.REQUEST)
                        self.assertTrue(
                            self.read_head(client).startswith(b"HTTP/1.1 502 ")
                        )
                        self.assertTrue(disconnected.wait(1))

    def test_enabled_web_proxy_tunnels_hmr_tls_binary_and_upstream_eof(self):
        """A real Upgrade preserves frames coalesced with both HTTP handshakes."""
        client_frame = b"\x82\x84\x01\x02\x03\x04\x01\xfd\x03\x84"
        server_frame = b"\x82\x04\x00\xff\x00\x80"
        received = []

        def respond(handler):
            if "upgrade" not in handler.headers.get("Connection", "").lower():
                handler.send_error(404)
                return
            # One write deliberately coalesces the first frame with the 101.
            handler.connection.sendall(self.RESPONSE + server_frame)
            received.append(handler.rfile.read(len(client_frame)))
            handler.connection.sendall(received[-1])

        with self.fixture(respond) as (proxy, observed):
            with self.client(proxy) as client:
                client.sendall(self.REQUEST + client_frame)
                head = self.read_head(client)
                self.assertTrue(head.startswith(b"HTTP/1.1 101 "), head)
                body = bytearray()
                while part := client.recv(4096):
                    body.extend(part)
                self.assertEqual(body, server_frame + client_frame)
                self.assertEqual(observed, ["/_next/webpack-hmr?session=fixture"])
        self.assertEqual(received, [client_frame])


class BrowserGuards(unittest.TestCase):
    def test_rp_csrf_rejection_has_no_retry_page_navigation(self):
        accepted = smoke.BrowserResponse(
            403,
            {"content-type": "application/json", "cache-control": "no-store"},
            [],
            b'{"error":{"code":"rp_signin_rejected"}}',
        )
        smoke.require_rejected_rp_signin(accepted)
        smoke.require_rejected_rp_signin(
            smoke.BrowserResponse(
                403,
                {**accepted.headers, "cache-control": "private, no-store, max-age=0"},
                [],
                accepted.body,
            )
        )
        for rejected in (
            smoke.BrowserResponse(303, {"location": "/login"}, [], b""),
            smoke.BrowserResponse(403, {"location": "/login"}, [], accepted.body),
            smoke.BrowserResponse(403, accepted.headers, ["retry=1"], accepted.body),
            smoke.BrowserResponse(
                403, accepted.headers, [], b'{"error":{"code":"other"}}'
            ),
            smoke.BrowserResponse(
                403,
                {**accepted.headers, "cache-control": "private, max-age=60"},
                [],
                accepted.body,
            ),
        ):
            with self.subTest(rejected=rejected), self.assertRaises(smoke.SmokeError):
                smoke.require_rejected_rp_signin(rejected)

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

    def test_proxy_forwards_delete_without_turning_it_into_501(self):
        observed = []

        class Upstream(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def do_DELETE(self):
                observed.append((self.command, self.path))
                payload = b'{"error":{"code":"session_not_found"}}'
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

        upstream = ThreadingHTTPServer(("127.0.0.1", 0), Upstream)
        worker = Thread(target=upstream.serve_forever, daemon=True)
        worker.start()
        proxy = smoke.Proxy(
            upstream.server_port,
            credentials=smoke.previous.CredentialRegistry(),
        )
        try:
            connection = http.client.HTTPConnection("127.0.0.1", proxy.server_port)
            connection.request("DELETE", "/v1/sessions/conv-a")
            response = connection.getresponse()
            self.assertEqual(response.status, 404)
            self.assertEqual(
                json.loads(response.read()),
                {"error": {"code": "session_not_found"}},
            )
            self.assertEqual(observed, [("DELETE", "/v1/sessions/conv-a")])
            connection.close()
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
