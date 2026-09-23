from __future__ import annotations

import json
import socket
import threading
from threading import Event, Thread
import time
from urllib.error import URLError
from urllib.request import Request, urlopen

import pytest

from scripts.e2e import scheduler_bff_smoke_http as http


def test_agent_stub_returns_deterministic_receipt_and_records_once() -> None:
    with http.agent_receipt_stub() as stub:
        body = json.dumps({"run_id": "run-1", "request_id": "launch-1"}).encode()
        request = Request(
            stub.base_url + "/v1/runs",
            data=body,
            method="POST",
            headers={"content-type": "application/json", "x-request-id": "transport-1"},
        )
        with urlopen(request, timeout=2) as response:
            first = json.loads(response.read())
        assert response.status == 202
        assert first["data"]["run_id"] == "run-1"
        assert stub.count("run-1") == 1
        assert stub.calls[0].request_id == "transport-1"
        assert stub.is_real_agent is False


def test_response_drop_proxy_records_acceptance_then_passes_same_request() -> None:
    with http.agent_receipt_stub() as target:
        with http.response_drop_proxy(target.base_url) as proxy:
            proxy.drop_next_accepted_response()
            request = Request(
                proxy.base_url + "/v1/runs",
                data=json.dumps({"run_id": "run-drop"}).encode(),
                method="POST",
                headers={
                    "content-type": "application/json",
                    "idempotency-key": "same-key",
                },
            )
            with pytest.raises((URLError, ConnectionError, OSError)):
                urlopen(request, timeout=2)
            assert proxy.wait_for_drop(2)
            with urlopen(request, timeout=2) as response:
                assert response.status == 202
            assert [call.idempotency_key for call in proxy.calls] == [
                "same-key",
                "same-key",
            ]


def test_proxy_exposes_configured_dns_target_separately_from_listen_address() -> None:
    with http.response_drop_proxy("http://127.0.0.1:1") as proxy:
        port = proxy.base_url.rsplit(":", 1)[1]
        proxy.set_target_host("fixture-host.local")
        assert proxy.target_base == f"http://fixture-host.local:{port}"


def test_proxy_binds_only_the_exact_requested_private_interface(monkeypatch) -> None:
    actual = "192.168.1.9"
    captured: list[tuple[str, int]] = []
    original = http.OwnedHTTPServer

    class RecordingServer(original):
        def __init__(self, address, handler):
            captured.append(address)
            super().__init__(("127.0.0.1", address[1]), handler)

    monkeypatch.setattr(http, "OwnedHTTPServer", RecordingServer)
    with http.response_drop_proxy("http://127.0.0.1:1", bind_address=actual):
        assert captured == [(actual, 0)]


@pytest.mark.parametrize("address", ["0.0.0.0", "8.8.8.8", "198.18.1.2", "::1"])
def test_proxy_rejects_non_private_bind_address(address: str) -> None:
    with pytest.raises(http.SmokeError, match="bind"):
        with http.response_drop_proxy("http://127.0.0.1:1", bind_address=address):
            pass


def _request_threads_after(baseline: set[int]) -> list[Thread]:
    return [
        thread
        for thread in threading.enumerate()
        if thread.ident not in baseline and "process_request_thread" in thread.name
    ]


def _wait_for_request_thread(baseline: set[int]) -> None:
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        if _request_threads_after(baseline):
            return
        time.sleep(0.01)
    raise AssertionError("fixture request handler did not start")


@pytest.mark.parametrize("fixture", ["agent", "proxy"])
def test_http_fixture_drains_partial_body_handler_on_exit(fixture: str) -> None:
    baseline = {thread.ident for thread in threading.enumerate()}
    client: socket.socket | None = None
    manager = (
        http.agent_receipt_stub()
        if fixture == "agent"
        else http.response_drop_proxy("http://127.0.0.1:1")
    )
    path = "/v1/runs" if fixture == "agent" else "/dispatch"
    try:
        with manager as state:
            port = int(state.base_url.rsplit(":", 1)[1])
            client = socket.create_connection(("127.0.0.1", port), timeout=2)
            client.sendall(
                f"POST {path} HTTP/1.0\r\nContent-Length: 100\r\n\r\n{{".encode()
            )
            _wait_for_request_thread(baseline)
        assert _request_threads_after(baseline) == []
    finally:
        if client is not None:
            client.close()
        for thread in _request_threads_after(baseline):
            thread.join(timeout=2)


def _start_proxy_request(base_url: str, timeout: float) -> Thread:
    request = Request(
        base_url + "/dispatch",
        data=b"{}",
        method="POST",
        headers={"content-type": "application/json"},
    )

    def send() -> None:
        try:
            urlopen(request, timeout=timeout).read()
        except (URLError, TimeoutError, OSError):
            pass

    thread = Thread(target=send, daemon=True)
    thread.start()
    return thread


def test_proxy_fixture_bounds_stalled_upstream_handler_shutdown() -> None:
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen()
    accepted = Event()
    release = Event()
    upstream_connections: list[socket.socket] = []

    def stall() -> None:
        connection, _ = listener.accept()
        upstream_connections.append(connection)
        accepted.set()
        release.wait(5)

    upstream_thread = Thread(target=stall, daemon=True)
    upstream_thread.start()
    baseline = {thread.ident for thread in threading.enumerate()}
    request_thread: Thread | None = None
    started = time.monotonic()
    try:
        with http.response_drop_proxy(
            f"http://127.0.0.1:{listener.getsockname()[1]}"
        ) as proxy:
            request_thread = _start_proxy_request(proxy.base_url, 5)
            assert accepted.wait(2)
            _wait_for_request_thread(baseline)
        assert time.monotonic() - started < 4
        assert _request_threads_after(baseline) == []
    finally:
        release.set()
        for connection in upstream_connections:
            connection.close()
        listener.close()
        upstream_thread.join(timeout=2)
        if request_thread is not None:
            request_thread.join(timeout=2)


def test_proxy_fixture_cancels_trickling_upstream_body_before_handler_join() -> None:
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen()
    response_started = Event()
    release = Event()
    proxy_exited = Event()
    failures: list[BaseException] = []
    request_threads: list[Thread] = []
    upstream_connections: list[socket.socket] = []
    baseline = {thread.ident for thread in threading.enumerate()}

    def trickle() -> None:
        connection, _ = listener.accept()
        upstream_connections.append(connection)
        try:
            connection.recv(4096)
            connection.sendall(
                b"HTTP/1.0 202 Accepted\r\nContent-Length: 100000\r\n"
                b"Content-Type: application/json\r\n\r\n"
            )
            response_started.set()
            while not release.wait(0.1):
                connection.sendall(b"{")
        except OSError:
            pass

    upstream_thread = Thread(target=trickle, daemon=True)
    upstream_thread.start()

    def use_proxy() -> None:
        try:
            with http.response_drop_proxy(
                f"http://127.0.0.1:{listener.getsockname()[1]}"
            ) as proxy:
                request_thread = _start_proxy_request(proxy.base_url, 6)
                request_threads.append(request_thread)
                if not response_started.wait(2):
                    raise AssertionError("trickling upstream did not start")
        except BaseException as error:
            failures.append(error)
        finally:
            proxy_exited.set()

    fixture_thread = Thread(target=use_proxy, daemon=True)
    fixture_thread.start()
    try:
        assert response_started.wait(2)
        assert proxy_exited.wait(4), (
            "proxy context exceeded its total shutdown deadline"
        )
        assert failures == []
        assert _request_threads_after(baseline) == []
    finally:
        release.set()
        for connection in upstream_connections:
            connection.close()
        listener.close()
        upstream_thread.join(timeout=2)
        fixture_thread.join(timeout=2)
        for request_thread in request_threads:
            request_thread.join(timeout=2)


def test_upstream_deadline_interrupts_trickling_response_headers() -> None:
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen()
    response_started = Event()
    release = Event()
    operation_finished = Event()
    connections: list[socket.socket] = []
    result: list[BaseException] = []
    baseline_timers = {
        thread.ident
        for thread in threading.enumerate()
        if thread.name.startswith("scheduler-bff-http-deadline")
    }

    def trickle_headers() -> None:
        connection, _ = listener.accept()
        connections.append(connection)
        try:
            connection.recv(4096)
            connection.sendall(b"HTTP/1.1 202 Accepted\r\nX-Trickle: ")
            response_started.set()
            while not release.wait(0.1):
                connection.sendall(b"x")
        except OSError:
            pass

    upstream_thread = Thread(target=trickle_headers, daemon=True)
    upstream_thread.start()
    state = http.ResponseDropState(f"http://127.0.0.1:{listener.getsockname()[1]}")

    def call_upstream() -> None:
        try:
            http._proxy_upstream(state, "/dispatch", "POST", {}, b"{}")
        except BaseException as error:
            result.append(error)
        finally:
            operation_finished.set()

    operation_thread = Thread(target=call_upstream, daemon=True)
    operation_thread.start()
    try:
        assert response_started.wait(2)
        assert operation_finished.wait(http.FIXTURE_OPERATION_TIMEOUT + 1), (
            "trickling response headers exceeded the total operation deadline"
        )
        assert len(result) == 1
        assert isinstance(result[0], TimeoutError)
        operation_thread.join(timeout=1)
        upstream_thread.join(timeout=1)
        assert not operation_thread.is_alive()
        assert not upstream_thread.is_alive()
        assert state.upstream_sockets == set()
        assert {
            thread.ident
            for thread in threading.enumerate()
            if thread.name.startswith("scheduler-bff-http-deadline")
        } == baseline_timers
    finally:
        state.cancel_upstreams()
        release.set()
        for connection in connections:
            connection.close()
        listener.close()
        operation_thread.join(timeout=2)
        upstream_thread.join(timeout=2)
