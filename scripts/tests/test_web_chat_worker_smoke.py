"""Focused guards for the Web/IAM/BFF/Agent worker composition runner."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from pathlib import Path
import socket
from threading import Event, Thread

import pytest

from scripts.e2e import run_web_chat_worker_smoke as smoke


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "scripts" / "e2e" / "run_web_chat_worker_smoke.py"


def test_runner_exists_as_a_narrow_composer() -> None:
    assert RUNNER.is_file()


def test_private_actor_probe_uses_own_product_session_for_all_foreign_paths() -> None:
    calls: list[tuple[str, dict[str, object]]] = []
    conversation_id = "conv_12345678-1234-1234-1234-123456789abc"
    run_id = "run_12345678-1234-1234-1234-123456789abc"
    headers = {
        "content-type": "application/json",
        "cache-control": "private, no-store",
        "x-request-id": "req-private-1",
    }

    def request(path: str, **kwargs: object) -> smoke.product.BrowserResponse:
        calls.append((path, kwargs))
        if path == "/api/session/sessions?limit=1":
            return smoke.product.BrowserResponse(
                200, headers, [], b'{"sessions":[],"next_cursor":null}'
            )
        return smoke.product.BrowserResponse(
            404,
            headers,
            [],
            b'{"error":{"code":"session_not_found","message":"Session was not found"},"meta":{"request_id":"req-private-1"}}',
        )

    probe = smoke.PrivateActorProbe(
        actor_name="same_tenant_member",
        user_id="user-b",
        conversation_id=conversation_id,
        run_id=run_id,
        web_origin="https://web.example.test",
    )
    probe(request, {"authenticated": True, "subject": "user-b", "expires_at": 1})

    assert probe.calls == 1
    assert calls == [
        ("/api/session/sessions?limit=1", {}),
        (f"/api/session/sessions/{conversation_id}", {}),
        (f"/api/session/sessions/{conversation_id}/messages?limit=1", {}),
        (
            f"/api/session/sessions/{conversation_id}/events",
            {"accept": "text/event-stream"},
        ),
        (
            f"/api/session/sessions/{conversation_id}/messages",
            {
                "method": "POST",
                "json_body": {
                    "content": "Foreign actor must not mutate this conversation."
                },
                "origin": "https://web.example.test",
                "idempotency_key": "privacy:same_tenant_member:conv_12345678-1234-1234-1234-123456789abc",
            },
        ),
        (
            f"/api/session/sessions/{conversation_id}",
            {
                "method": "DELETE",
                "origin": "https://web.example.test",
                "idempotency_key": "privacy:delete:same_tenant_member:conv_12345678-1234-1234-1234-123456789abc",
            },
        ),
        (
            f"/api/session/sessions/{conversation_id}/runs/{run_id}/control",
            {
                "method": "POST",
                "json_body": {"kind": "run.cancel"},
                "origin": "https://web.example.test",
                "idempotency_key": "privacy:control:same_tenant_member:conv_12345678-1234-1234-1234-123456789abc",
            },
        ),
    ]


def test_private_actor_probe_rejects_wrong_subject_and_leaked_resource() -> None:
    probe = smoke.PrivateActorProbe(
        actor_name="other_tenant_owner",
        user_id="user-c",
        conversation_id="conv-a",
        run_id="run-a",
        web_origin="https://web.example.test",
    )
    with pytest.raises(smoke.SmokeError, match="subject"):
        probe(lambda *_a, **_k: None, {"subject": "user-a"})
    assert probe.calls == 0

    calls: list[str] = []
    headers = {
        "content-type": "application/json",
        "cache-control": "private, no-store",
        "x-request-id": "req-private-1",
    }

    def leaked_list(path: str, **_kwargs: object) -> smoke.product.BrowserResponse:
        calls.append(path)
        return smoke.product.BrowserResponse(
            200,
            headers,
            [],
            b'{"sessions":[{"session_id":"conv-a"}],"next_cursor":null}',
        )

    with pytest.raises(smoke.SmokeError, match="discovered"):
        probe(leaked_list, {"subject": "user-c"})
    assert calls == ["/api/session/sessions?limit=1"]


def test_privacy_sql_evidence_uses_separate_owner_local_queries(monkeypatch) -> None:
    queries: list[str] = []

    def psql(_resources: object, _url: str, query: str) -> str:
        queries.append(query)
        if "kokoro_bff." in query:
            return json.dumps(
                {
                    "conversations": 1,
                    "messages": 2,
                    "outbox": 1,
                    "agui_events": 5,
                    "idempotency_receipts": 1,
                    "cancellation_outbox": 0,
                    "shares": 0,
                    "agui_source_events": 4,
                    "agui_streams": 1,
                }
            )
        return json.dumps(
            {"runs": 1, "dispatches": 1, "chat_events": 4, "chat_messages": 2}
        )

    monkeypatch.setattr(smoke.worker, "_psql", psql)
    monkeypatch.setattr(smoke.worker, "_first_turn_facts", lambda *_args: {"count": 1})
    monkeypatch.setattr(
        smoke.worker, "_final_sql_evidence", lambda *_args: {"terminal": True}
    )

    evidence = smoke._privacy_sql_evidence(
        object(), "postgresql://owned", "conv-a", "run-a"
    )
    assert evidence["bff"]["conversations"] == 1
    assert evidence["bff"]["idempotency_receipts"] == 1
    assert evidence["bff"]["cancellation_outbox"] == 0
    assert evidence["bff"]["shares"] == 0
    assert evidence["bff"]["agui_source_events"] == 4
    assert evidence["bff"]["agui_streams"] == 1
    assert evidence["agent"]["runs"] == 1
    assert len(queries) == 2
    assert "kokoro_bff." in queries[0] and "kokoro_agent." not in queries[0]
    assert "kokoro_agent." in queries[1] and "kokoro_bff." not in queries[1]
    for table in (
        "bff_idempotency_receipt",
        "bff_agent_cancellation_outbox",
        "bff_share",
        "bff_agui_source_event",
        "bff_agui_stream",
    ):
        assert f"kokoro_bff.{table}" in queries[0]


def test_privacy_browser_boundary_keeps_bc_distinct_from_a_chromium() -> None:
    assert smoke._privacy_browser_boundary(None) == (
        "A/B/C: independent Python CookieJar HTTPS Product Sessions"
    )
    mode = smoke.BrowserOriginMode(443, lambda *_args: None, lambda *_args: {})
    assert smoke._privacy_browser_boundary(mode) == (
        "A: Chromium DOM/SSE; B/C: independent Python CookieJar HTTPS Product Sessions"
    )


def test_browser_turn_context_exposes_only_owned_worker_start_and_fixture_reply() -> (
    None
):
    starts: list[str] = []
    context = smoke.BrowserTurnContext(
        start_worker=lambda: starts.append("started"),
        expected_reply="fixture reply",
        timeout=45.0,
    )

    context.start_worker()

    assert starts == ["started"]
    assert context.expected_reply == "fixture reply"
    assert context.timeout == 45.0


def test_failed_browser_after_post_registers_only_owner_sql_runs_before_cleanup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    actions: list[object] = []

    class Owned:
        def register_agent_keys(self, conversation_id: str, run_id: str) -> None:
            actions.append((conversation_id, run_id))

        def cleanup(self) -> None:
            actions.append("cleanup")

        def verify_clean(self) -> None:
            actions.append("verify_clean")

    def query(_resources: object, _url: str, _sql: str) -> str:
        actions.append("owner_sql")
        return json.dumps(
            [{"conversation_id": "conv_committed", "run_id": "run_committed"}]
        )

    monkeypatch.setattr(smoke.worker, "_psql", query)
    smoke._cleanup_browser_resources(Owned(), "postgresql://owned")

    assert actions == [
        "owner_sql",
        ("conv_committed", "run_committed"),
        "cleanup",
        "verify_clean",
    ]


@pytest.mark.parametrize(
    "inventory",
    [
        "not-json",
        "{}",
        '[{"conversation_id":"conv_ok"}]',
        '[{"conversation_id":1,"run_id":"run_ok"}]',
    ],
)
def test_browser_cleanup_rejects_untrusted_owner_inventory_without_deleting(
    monkeypatch: pytest.MonkeyPatch, inventory: str
) -> None:
    actions: list[str] = []

    class Owned:
        def register_agent_keys(self, _conversation_id: str, _run_id: str) -> None:
            actions.append("register")

        def cleanup(self) -> None:
            actions.append("cleanup")

    monkeypatch.setattr(smoke.worker, "_psql", lambda *_args: inventory)
    with pytest.raises(smoke.SmokeError, match="cleanup inventory malformed"):
        smoke._cleanup_browser_resources(Owned(), "postgresql://owned")
    assert actions == []


def test_bounded_chunked_proxy_body_is_normalized() -> None:
    stream = BytesIO(b"4\r\nWiki\r\n5\r\npedia\r\n0\r\n\r\n")
    assert smoke._read_bounded_chunked(stream, max_bytes=9) == b"Wikipedia"


def test_bounded_chunked_proxy_body_rejects_malformed_and_oversized() -> None:
    for raw, maximum in (
        (b"x\r\nbad\r\n0\r\n\r\n", 100),
        (b"4\r\nWikiX\r\n0\r\n\r\n", 100),
        (b"5\r\nlarge\r\n0\r\n\r\n", 4),
        (b"1\r\na\r\n0\r\nx-trailer: no\r\n\r\n", 100),
    ):
        with pytest.raises(smoke.SmokeError):
            smoke._read_bounded_chunked(BytesIO(raw), max_bytes=maximum)


def _exercise_proxy(raw_request: bytes) -> tuple[bytes, list[bytes]]:
    received: list[bytes] = []

    class UpstreamHandler(BaseHTTPRequestHandler):
        def log_message(self, _format, *_args) -> None:
            pass

        def do_POST(self) -> None:
            length = int(self.headers.get("content-length", "0"))
            received.append(self.rfile.read(length))
            self.send_response(204)
            self.send_header("Content-Length", "0")
            self.end_headers()

    upstream = ThreadingHTTPServer(("127.0.0.1", 0), UpstreamHandler)
    upstream_thread = Thread(target=upstream.serve_forever, daemon=True)
    upstream_thread.start()
    proxy = smoke.BoundedObservingProxy(
        upstream.server_port,
        credentials=smoke.product.previous.CredentialRegistry(),
    )
    try:
        with socket.create_connection(
            ("127.0.0.1", proxy.server_port), timeout=2
        ) as client:
            client.sendall(raw_request)
            client.shutdown(socket.SHUT_WR)
            response = bytearray()
            while chunk := client.recv(4096):
                response.extend(chunk)
        return bytes(response), received
    finally:
        proxy.close()
        upstream.shutdown()
        upstream.server_close()
        upstream_thread.join(timeout=5)


@pytest.mark.parametrize(
    "framing",
    [
        b"Content-Length: 4\r\nContent-Length: 4\r\n",
        b"Content-Length: nope\r\n",
        b"Content-Length: -1\r\n",
        b"Content-Length: " + (b"9" * 5_000) + b"\r\n",
        b"Content-Length: 4\r\nTransfer-Encoding: chunked\r\n",
        b"Transfer-Encoding: gzip\r\n",
    ],
)
def test_bounded_proxy_rejects_ambiguous_or_invalid_http_framing(
    framing: bytes,
) -> None:
    response, received = _exercise_proxy(
        b"POST /messages HTTP/1.1\r\nHost: fixture\r\n"
        + framing
        + b"Connection: close\r\n\r\n4\r\ntest\r\n0\r\n\r\n"
    )

    assert response.startswith(b"HTTP/1.1 413 ")
    assert received == []


def test_bounded_proxy_normalizes_valid_chunked_body_at_handler_boundary() -> None:
    response, received = _exercise_proxy(
        b"POST /messages HTTP/1.1\r\n"
        b"Host: fixture\r\n"
        b"Transfer-Encoding: chunked\r\n"
        b"Connection: close\r\n\r\n"
        b"4\r\ntest\r\n0\r\n\r\n"
    )

    assert response.startswith(b"HTTP/1.1 204 ")
    assert received == [b"test"]


def test_bff_proxy_streams_decoded_sse_before_upstream_finishes() -> None:
    release = Event()
    first_sent = Event()
    observed_cursors: list[str | None] = []

    class UpstreamHandler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, _format, *_args) -> None:
            pass

        def do_GET(self) -> None:
            observed_cursors.append(self.headers.get("last-event-id"))
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Transfer-Encoding", "chunked")
            self.end_headers()
            self.wfile.write(b"b\r\nid: 1\n\ndata\r\n")
            self.wfile.flush()
            first_sent.set()
            release.wait(3)
            self.wfile.write(b"6\r\n: end\n\r\n0\r\n\r\n")
            self.wfile.flush()

    upstream = ThreadingHTTPServer(("127.0.0.1", 0), UpstreamHandler)
    upstream_thread = Thread(target=upstream.serve_forever, daemon=True)
    upstream_thread.start()
    proxy = smoke.BoundedObservingProxy(
        upstream.server_port,
        credentials=smoke.product.previous.CredentialRegistry(),
    )
    try:
        with socket.create_connection(
            ("127.0.0.1", proxy.server_port), timeout=2
        ) as client:
            client.settimeout(1)
            client.sendall(
                b"GET /v1/sessions/session_one/events HTTP/1.1\r\n"
                b"Host: fixture\r\nAccept: text/event-stream\r\n"
                b"Last-Event-ID: agui_cursor\r\n\r\n"
            )
            assert first_sent.wait(1)
            first = bytearray()
            while b"id: 1" not in first:
                first.extend(client.recv(4096))
            assert b"HTTP/1.1 200" in first
            assert b"Transfer-Encoding: chunked" in first
            assert b"id: 1" in first
            assert b"Content-Length:" not in first
            release.set()
            remaining = bytearray()
            while part := client.recv(4096):
                remaining.extend(part)
            assert b": end\n" in remaining
            assert remaining.endswith(b"0\r\n\r\n")
            assert observed_cursors == ["agui_cursor"]
    finally:
        release.set()
        proxy.close()
        upstream.shutdown()
        upstream.server_close()
        upstream_thread.join(timeout=5)


@pytest.mark.parametrize("limit_name", ["SSE_IDLE_SECONDS", "SSE_TOTAL_SECONDS"])
def test_bff_proxy_bounds_stalled_sse_and_closes_upstream(
    monkeypatch, limit_name
) -> None:
    upstream_closed = Event()
    monkeypatch.setattr(smoke.product.old, limit_name, 0.2)

    class UpstreamHandler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, _format, *_args) -> None:
            pass

        def do_GET(self) -> None:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Transfer-Encoding", "chunked")
            self.end_headers()
            self.wfile.write(b"7\r\nid: 1\n\n\r\n")
            self.wfile.flush()
            if not self.connection.recv(1):
                upstream_closed.set()

    upstream = ThreadingHTTPServer(("127.0.0.1", 0), UpstreamHandler)
    upstream_thread = Thread(target=upstream.serve_forever, daemon=True)
    upstream_thread.start()
    proxy = smoke.BoundedObservingProxy(
        upstream.server_port,
        credentials=smoke.product.previous.CredentialRegistry(),
    )
    try:
        with socket.create_connection(
            ("127.0.0.1", proxy.server_port), timeout=2
        ) as client:
            client.settimeout(2)
            client.sendall(
                b"GET /v1/sessions/session_one/events HTTP/1.1\r\nHost: fixture\r\n\r\n"
            )
            response = bytearray()
            while part := client.recv(4096):
                response.extend(part)
            assert b"HTTP/1.1 200" in response
            assert b"id: 1" in response
            assert b"502" not in response
            assert not response.endswith(b"0\r\n\r\n")
        assert upstream_closed.wait(1)
    finally:
        proxy.close()
        upstream.shutdown()
        upstream.server_close()
        upstream_thread.join(timeout=5)


def test_bff_proxy_caps_sse_bytes_without_second_status(monkeypatch) -> None:
    monkeypatch.setattr(smoke.product.old, "MAX_SSE_BODY", 5)

    class UpstreamHandler(BaseHTTPRequestHandler):
        def log_message(self, _format, *_args) -> None:
            pass

        def do_GET(self) -> None:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Content-Length", "7")
            self.end_headers()
            self.wfile.write(b"id: 1\n\n")

    upstream = ThreadingHTTPServer(("127.0.0.1", 0), UpstreamHandler)
    upstream_thread = Thread(target=upstream.serve_forever, daemon=True)
    upstream_thread.start()
    proxy = smoke.BoundedObservingProxy(
        upstream.server_port,
        credentials=smoke.product.previous.CredentialRegistry(),
    )
    try:
        with socket.create_connection(
            ("127.0.0.1", proxy.server_port), timeout=2
        ) as client:
            client.settimeout(2)
            client.sendall(
                b"GET /v1/sessions/session_one/events HTTP/1.1\r\nHost: fixture\r\n\r\n"
            )
            response = bytearray()
            while part := client.recv(4096):
                response.extend(part)
            assert b"HTTP/1.1 200" in response
            assert b"id: 1" not in response
            assert b"502" not in response
            assert not response.endswith(b"0\r\n\r\n")
    finally:
        proxy.close()
        upstream.shutdown()
        upstream.server_close()
        upstream_thread.join(timeout=5)


def test_bff_proxy_closes_upstream_on_downstream_disconnect(monkeypatch) -> None:
    upstream_closed = Event()
    monkeypatch.setattr(smoke.product.old, "SSE_IDLE_SECONDS", 3)

    class UpstreamHandler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, _format, *_args) -> None:
            pass

        def do_GET(self) -> None:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Transfer-Encoding", "chunked")
            self.end_headers()
            self.wfile.write(b"7\r\nid: 1\n\n\r\n")
            self.wfile.flush()
            if not self.connection.recv(1):
                upstream_closed.set()

    upstream = ThreadingHTTPServer(("127.0.0.1", 0), UpstreamHandler)
    upstream_thread = Thread(target=upstream.serve_forever, daemon=True)
    upstream_thread.start()
    proxy = smoke.BoundedObservingProxy(
        upstream.server_port,
        credentials=smoke.product.previous.CredentialRegistry(),
    )
    try:
        with socket.create_connection(
            ("127.0.0.1", proxy.server_port), timeout=2
        ) as client:
            client.settimeout(1)
            client.sendall(
                b"GET /v1/sessions/session_one/events HTTP/1.1\r\nHost: fixture\r\n\r\n"
            )
            first = bytearray()
            while b"id: 1" not in first:
                first.extend(client.recv(4096))
        assert upstream_closed.wait(1)
    finally:
        proxy.close()
        upstream.shutdown()
        upstream.server_close()
        upstream_thread.join(timeout=5)


@pytest.mark.parametrize(
    ("path", "status", "content_type"),
    [
        ("/v1/sessions/session_one/events", 200, "application/json"),
        ("/v1/sessions/session_one/events", 403, "text/event-stream"),
        ("/iam/oauth2/token", 200, "text/event-stream"),
    ],
)
def test_bff_proxy_keeps_nonmatching_responses_buffered(
    path: str, status: int, content_type: str
) -> None:
    release = Event()
    first_sent = Event()

    class UpstreamHandler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, _format, *_args) -> None:
            pass

        def do_GET(self) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", "7")
            self.end_headers()
            self.wfile.write(b"first")
            self.wfile.flush()
            first_sent.set()
            release.wait(3)
            self.wfile.write(b"!!")
            self.wfile.flush()

    upstream = ThreadingHTTPServer(("127.0.0.1", 0), UpstreamHandler)
    upstream_thread = Thread(target=upstream.serve_forever, daemon=True)
    upstream_thread.start()
    proxy = smoke.BoundedObservingProxy(
        upstream.server_port,
        credentials=smoke.product.previous.CredentialRegistry(),
    )
    try:
        with socket.create_connection(
            ("127.0.0.1", proxy.server_port), timeout=2
        ) as client:
            client.settimeout(0.3)
            client.sendall(f"GET {path} HTTP/1.1\r\nHost: fixture\r\n\r\n".encode())
            assert first_sent.wait(1)
            with pytest.raises(TimeoutError):
                client.recv(4096)
            release.set()
            client.settimeout(2)
            response = bytearray()
            while part := client.recv(4096):
                response.extend(part)
            assert bytes(response).startswith(f"HTTP/1.1 {status} ".encode())
            assert b"Content-Length: 7" in response
            assert b"Transfer-Encoding: chunked" not in response
            assert response.endswith(b"first!!")
    finally:
        release.set()
        proxy.close()
        upstream.shutdown()
        upstream.server_close()
        upstream_thread.join(timeout=5)


def test_process_stop_failure_defers_every_owned_data_cleanup(monkeypatch) -> None:
    first = object()
    second = object()
    stopped = []
    cleaned = []

    def stop(process) -> None:
        stopped.append(process)
        if process is first:
            raise smoke.SmokeError("injected stop failure")

    monkeypatch.setattr(smoke.worker.runtime, "stop_owned_process", stop)

    failures = smoke._stop_processes_then_cleanup_data(
        [first, second],
        [
            ("Web Redis cleanup", lambda: cleaned.append("web")),
            ("IAM resource cleanup", lambda: cleaned.append("iam")),
            ("BFF/Agent resource cleanup", lambda: cleaned.append("worker")),
        ],
    )

    assert stopped == [second, first]
    assert cleaned == []
    assert failures == [
        "owned process cleanup failed; all owned data cleanup deferred; "
        "ownership retained"
    ]


def test_owned_data_cleanup_runs_only_after_all_processes_stop(monkeypatch) -> None:
    stopped = []
    cleaned = []
    monkeypatch.setattr(
        smoke.worker.runtime,
        "stop_owned_process",
        lambda process: stopped.append(process),
    )

    failures = smoke._stop_processes_then_cleanup_data(
        ["one", "two"],
        [
            ("Web Redis cleanup", lambda: cleaned.append("web")),
            ("IAM resource cleanup", lambda: cleaned.append("iam")),
            ("BFF/Agent resource cleanup", lambda: cleaned.append("worker")),
        ],
    )

    assert failures == []
    assert stopped == ["two", "one"]
    assert cleaned == ["web", "iam", "worker"]


def test_authenticated_chat_action_uses_web_adapter_and_durable_replay(
    monkeypatch,
) -> None:
    response_headers = {
        "content-type": "application/json",
        "cache-control": "private, no-store",
        "x-request-id": "request-1",
    }
    receipt = {
        "run_id": "run_one",
        "user_message_id": "message-user",
        "assistant_message_id": "message-assistant",
    }
    snapshot = {
        "messages": [
            {"role": "user", "status": "completed", "content": "hello"},
            {"role": "assistant", "status": "completed", "content": "reply"},
        ],
        "event_watermark": "5",
    }
    calls = []
    lifecycle = []

    def response(status: int, body: dict):
        return smoke.product.BrowserResponse(
            status,
            response_headers,
            [],
            json.dumps(body).encode(),
        )

    def request(path: str, **kwargs):
        calls.append((path, kwargs))
        if kwargs.get("method") == "POST":
            if kwargs["json_body"] == {"content": "changed"}:
                return response(
                    409,
                    {
                        "error": {
                            "code": "idempotency_conflict",
                            "message": "conflict",
                        },
                        "meta": {"request_id": "request-1"},
                    },
                )
            return response(
                202,
                receipt,
            )
        if path.endswith("/events"):
            return smoke.product.BrowserResponse(
                200,
                {
                    "content-type": "text/event-stream",
                    "cache-control": "private, no-store",
                    "x-request-id": "request-1",
                },
                [],
                b'id: 1\ndata: {"type":"RUN_STARTED"}\n\nid: 5\ndata: {"type":"RUN_FINISHED"}\n\n',
            )
        return response(
            200,
            snapshot,
        )

    class Resources:
        def __init__(self) -> None:
            self.registered = []

        def register_agent_keys(self, conversation_id: str, run_id: str) -> None:
            lifecycle.append("register")
            self.registered.append((conversation_id, run_id))

    resources = Resources()
    monkeypatch.setattr(
        smoke.worker,
        "_first_turn_facts",
        lambda *_args: (
            lifecycle.append("facts")
            or {
                "conversation_count": 1,
                "message_count": 2,
                "assistant_status": "pending",
                "outbox_count": 1,
                "outbox_status": "pending",
                "expected_run": "run_one",
            }
        ),
    )
    monkeypatch.setattr(
        smoke.worker,
        "_final_sql_evidence",
        lambda *_args: {
            "bff_outbox_status": "succeeded",
            "bff_assistant_status": "completed",
            "bff_agui_frames": 5,
            "bff_source_events": 4,
            "agent_terminal": True,
            "agent_dispatch_status": "claimed",
            "agent_chat_events": 4,
            "agent_event_summary": [],
            "agent_completed_assistants": 1,
        },
    )
    action = smoke.AuthenticatedChatAction(
        resources=resources,
        start_worker=lambda: lifecycle.append("worker"),
        database_url="postgresql://local/test",
        web_origin="https://web.example.test",
        conversation_id="conv_one",
        idempotency_key="message-one",
        content="hello",
        changed_content="changed",
        expected_reply="reply",
        timeout=1,
    )

    action(request)

    assert resources.registered == [("conv_one", "run_one")]
    assert lifecycle == ["register", "facts", "worker"]
    posts = [kwargs for _path, kwargs in calls if kwargs.get("method") == "POST"]
    assert [post["json_body"] for post in posts] == [
        {"content": "hello"},
        {"content": "hello"},
        {"content": "changed"},
    ]
    assert {post["idempotency_key"] for post in posts} == {"message-one"}
    assert calls[-1][0] == "/api/session/sessions/conv_one/events"
    assert calls[-1][1]["accept"] == "text/event-stream"
    assert action.result["run_id"] == "run_one"
    assert action.result["event_watermark"] == "5"
    assert action.result["agui_frame_types"] == ["RUN_STARTED", "RUN_FINISHED"]
