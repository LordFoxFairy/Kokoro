"""Focused guards for the Web/IAM/BFF/Agent worker composition runner."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from pathlib import Path
import socket
from threading import Thread

import pytest

from scripts.e2e import run_web_chat_worker_smoke as smoke


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "scripts" / "e2e" / "run_web_chat_worker_smoke.py"


def test_runner_exists_as_a_narrow_composer() -> None:
    assert RUNNER.is_file()


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
