"""Owned loopback HTTP fixtures for the Scheduler/BFF smoke."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from http.client import HTTPConnection, HTTPException
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from ipaddress import IPv4Address, IPv4Network, ip_address
import json
import socket
from threading import Event, Lock, Thread, Timer
import time
from urllib.parse import urlsplit

if __package__:
    from .scheduler_bff_smoke_runtime import SmokeError
else:
    from scheduler_bff_smoke_runtime import SmokeError

MAX_HTTP_BYTES = 1_048_576
FIXTURE_IO_TIMEOUT = 2.0
FIXTURE_OPERATION_TIMEOUT = 3.0
DEADLINE_THREAD_NAME = "scheduler-bff-http-deadline"


def _close_socket(owned_socket: socket.socket) -> None:
    try:
        owned_socket.shutdown(socket.SHUT_RDWR)
    except OSError:
        pass
    try:
        owned_socket.close()
    except OSError:
        pass


class OwnedHTTPServer(ThreadingHTTPServer):
    """Track and close every accepted fixture connection before joining handlers."""

    daemon_threads = False
    block_on_close = True

    def __init__(self, address: tuple[str, int], handler: type[BaseHTTPRequestHandler]):
        super().__init__(address, handler)
        self._connections: set[socket.socket] = set()
        self._connections_lock = Lock()

    def get_request(self) -> tuple[socket.socket, object]:
        connection, address = super().get_request()
        connection.settimeout(FIXTURE_IO_TIMEOUT)
        with self._connections_lock:
            self._connections.add(connection)
        return connection, address

    def shutdown_request(self, request: socket.socket) -> None:
        try:
            super().shutdown_request(request)
        finally:
            with self._connections_lock:
                self._connections.discard(request)

    def close_owned_connections(self) -> None:
        with self._connections_lock:
            connections = tuple(self._connections)
        for connection in connections:
            _close_socket(connection)


def _read_request_body(handler: BaseHTTPRequestHandler) -> bytes | None:
    try:
        length = int(handler.headers.get("content-length", "0"))
    except ValueError:
        return None
    if length < 0 or length > MAX_HTTP_BYTES:
        return None
    try:
        body = handler.rfile.read(length)
    except (TimeoutError, OSError):
        return None
    return body if len(body) == length else None


def _stop_http_fixture(
    server: OwnedHTTPServer,
    thread: Thread,
    label: str,
    cancel_outbound: Callable[[], None] | None = None,
) -> None:
    server.shutdown()
    server.close_owned_connections()
    if cancel_outbound is not None:
        cancel_outbound()
    server.server_close()
    thread.join(timeout=5)
    if thread.is_alive():
        raise SmokeError(f"Owned {label} listener did not stop")


@dataclass(frozen=True)
class AgentCall:
    run_id: str
    request_id: str
    body: dict[str, object]


class AgentReceiptState:
    is_real_agent = False

    def __init__(self) -> None:
        self.calls: list[AgentCall] = []
        self.lock = Lock()
        self.base_url = ""

    def count(self, run_id: str) -> int:
        with self.lock:
            return sum(call.run_id == run_id for call in self.calls)

    def snapshot(self) -> tuple[AgentCall, ...]:
        with self.lock:
            return tuple(
                AgentCall(
                    call.run_id,
                    call.request_id,
                    json.loads(json.dumps(call.body, separators=(",", ":"))),
                )
                for call in self.calls
            )


def _agent_handler(state: AgentReceiptState) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            raw_body = _read_request_body(self)
            if raw_body is None:
                self.close_connection = True
                return
            try:
                body = json.loads(raw_body)
            except (UnicodeDecodeError, json.JSONDecodeError):
                body = None
            run_id = body.get("run_id") if isinstance(body, dict) else None
            request_id = self.headers.get("x-request-id", "")
            if self.path != "/v1/runs" or not isinstance(run_id, str) or not run_id:
                self.send_response(400)
                self.end_headers()
                return
            with state.lock:
                state.calls.append(AgentCall(run_id, request_id, body))
            payload = json.dumps(
                {"data": {"run_id": run_id}, "meta": {"request_id": request_id}},
                separators=(",", ":"),
            ).encode()
            self.send_response(202)
            self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *_: object) -> None:
            return

    return Handler


@contextmanager
def agent_receipt_stub() -> Iterator[AgentReceiptState]:
    state = AgentReceiptState()
    server = OwnedHTTPServer(("127.0.0.1", 0), _agent_handler(state))
    state.base_url = f"http://127.0.0.1:{server.server_port}"
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield state
    finally:
        _stop_http_fixture(server, thread, "Agent stub")


@dataclass(frozen=True)
class ProxyCall:
    path: str
    method: str
    headers: dict[str, str]
    body: bytes
    upstream_status: int

    @property
    def schedule(self) -> str:
        return self.headers.get("x-kokoro-scheduler-schedule", "")

    @property
    def occurrence(self) -> str:
        return self.headers.get("x-kokoro-scheduler-occurrence", "")

    @property
    def idempotency_key(self) -> str:
        return self.headers.get("idempotency-key", "")


class ResponseDropState:
    def __init__(self, upstream: str) -> None:
        self.upstream = upstream
        self.base_url = ""
        self.target_base = ""
        self.calls: list[ProxyCall] = []
        self.lock = Lock()
        self.drop_count = 0
        self.dropped = Event()
        self.upstream_sockets: set[socket.socket] = set()
        self._upstreams_cancelled = False

    def set_target_host(self, host: str) -> None:
        self.target_base = f"http://{host}:{self.base_url.rsplit(':', 1)[1]}"

    def register_upstream(self, owned_socket: socket.socket) -> None:
        with self.lock:
            cancelled = self._upstreams_cancelled
            if not cancelled:
                self.upstream_sockets.add(owned_socket)
        if cancelled:
            _close_socket(owned_socket)

    def unregister_upstream(self, owned_socket: socket.socket) -> None:
        with self.lock:
            self.upstream_sockets.discard(owned_socket)

    def cancel_upstreams(self) -> None:
        with self.lock:
            self._upstreams_cancelled = True
            sockets = tuple(self.upstream_sockets)
        for owned_socket in sockets:
            _close_socket(owned_socket)

    def drop_next_accepted_response(self) -> None:
        with self.lock:
            self.drop_count += 1
            self.dropped.clear()

    def wait_for_drop(self, timeout: float) -> bool:
        return self.dropped.wait(timeout)

    def wait_for_schedule(
        self, schedule: str, *, after: int = 0, timeout: float = 30
    ) -> ProxyCall:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            with self.lock:
                found = next(
                    (call for call in self.calls[after:] if call.schedule == schedule),
                    None,
                )
            if found is not None:
                return found
            time.sleep(0.05)
        raise SmokeError("Real Scheduler callback was not observed")


class _OperationDeadline:
    def __init__(self, state: ResponseDropState) -> None:
        self._state = state
        self._lock = Lock()
        self._socket: socket.socket | None = None
        self._expired = False
        self._timer = Timer(FIXTURE_OPERATION_TIMEOUT, self._expire)
        self._timer.name = DEADLINE_THREAD_NAME

    def __enter__(self) -> _OperationDeadline:
        self._timer.start()
        return self

    def __exit__(self, *_: object) -> None:
        self._timer.cancel()
        self._timer.join(timeout=1)
        timer_alive = self._timer.is_alive()
        with self._lock:
            owned_socket = self._socket
            self._socket = None
        if owned_socket is not None:
            self._state.unregister_upstream(owned_socket)
        if timer_alive:
            raise SmokeError("Owned HTTP deadline timer did not stop")

    @property
    def expired(self) -> bool:
        with self._lock:
            return self._expired

    def register_socket(self, owned_socket: socket.socket) -> None:
        with self._lock:
            self._socket = owned_socket
            expired = self._expired
        self._state.register_upstream(owned_socket)
        if expired:
            _close_socket(owned_socket)

    def check(self) -> None:
        if self.expired:
            raise TimeoutError("upstream operation deadline exceeded")

    def _expire(self) -> None:
        with self._lock:
            self._expired = True
            owned_socket = self._socket
        if owned_socket is not None:
            _close_socket(owned_socket)


def _loopback_upstream(raw_url: str) -> tuple[str, int, str]:
    parsed = urlsplit(raw_url)
    if parsed.scheme != "http" or parsed.hostname is None:
        raise SmokeError("Response-drop proxy requires an HTTP loopback upstream")
    try:
        address = ip_address(parsed.hostname)
    except ValueError:
        raise SmokeError(
            "Response-drop proxy requires a numeric loopback upstream"
        ) from None
    if not address.is_loopback:
        raise SmokeError("Response-drop proxy requires an HTTP loopback upstream")
    return parsed.hostname, parsed.port or 80, parsed.path


def _proxy_upstream(
    state: ResponseDropState,
    path: str,
    method: str,
    headers: dict[str, str],
    body: bytes,
) -> tuple[int, bytes, dict[str, str]]:
    host, port, base_path = _loopback_upstream(state.upstream)
    connection = HTTPConnection(host, port, timeout=FIXTURE_IO_TIMEOUT)
    response = None
    with _OperationDeadline(state) as deadline:
        try:
            connection.connect()
            if connection.sock is None:
                raise SmokeError("Upstream connection did not provide a socket")
            deadline.register_socket(connection.sock)
            deadline.check()
            upstream_path = base_path.rstrip("/") + path
            connection.request(method, upstream_path, body=body, headers=headers)
            deadline.check()
            response = connection.getresponse()
            deadline.check()
            chunks: list[bytes] = []
            size = 0
            while size <= MAX_HTTP_BYTES:
                chunk = response.read1(min(65_536, MAX_HTTP_BYTES + 1 - size))
                deadline.check()
                if not chunk:
                    break
                chunks.append(chunk)
                size += len(chunk)
            payload = b"".join(chunks)
            if len(payload) > MAX_HTTP_BYTES:
                raise SmokeError("Upstream response exceeded fixture limit")
            response_headers = {
                key.lower(): value for key, value in response.getheaders()
            }
            return response.status, payload, response_headers
        except (HTTPException, TimeoutError, OSError):
            if deadline.expired:
                raise TimeoutError("upstream operation deadline exceeded") from None
            raise
        finally:
            if response is not None:
                response.close()
            connection.close()


def _proxy_handler(state: ResponseDropState) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def _handle(self) -> None:
            body = _read_request_body(self)
            if body is None:
                self.close_connection = True
                return
            headers = {
                key.lower(): value
                for key, value in self.headers.items()
                if key.lower() != "host"
            }
            try:
                status, payload, response_headers = _proxy_upstream(
                    state, self.path, self.command, headers, body
                )
            except (HTTPException, SmokeError, TimeoutError, OSError):
                try:
                    self.send_response(502)
                    self.end_headers()
                except OSError:
                    pass
                return
            call = ProxyCall(self.path, self.command, headers, body, status)
            with state.lock:
                state.calls.append(call)
                drop = 200 <= status < 300 and state.drop_count > 0
                if drop:
                    state.drop_count -= 1
            if drop:
                state.dropped.set()
                self.close_connection = True
                try:
                    self.connection.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                return
            self.send_response(status)
            for key in ("content-type", "x-request-id"):
                if key in response_headers:
                    self.send_header(key, response_headers[key])
            self.send_header("content-length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        do_POST = _handle  # noqa: N815
        do_PUT = _handle  # noqa: N815

        def log_message(self, *_: object) -> None:
            return

    return Handler


@contextmanager
def response_drop_proxy(
    upstream: str, *, bind_address: str = "127.0.0.1"
) -> Iterator[ResponseDropState]:
    _loopback_upstream(upstream)
    try:
        parsed_bind = IPv4Address(bind_address)
    except ValueError:
        raise SmokeError(
            "Response-drop proxy bind address must be exact IPv4"
        ) from None
    private = any(
        parsed_bind in network
        for network in (
            IPv4Network("10.0.0.0/8"),
            IPv4Network("172.16.0.0/12"),
            IPv4Network("192.168.0.0/16"),
        )
    )
    if bind_address != "127.0.0.1" and not private:
        raise SmokeError("Response-drop proxy bind address must be loopback or RFC1918")
    state = ResponseDropState(upstream)
    server = OwnedHTTPServer((bind_address, 0), _proxy_handler(state))
    state.base_url = f"http://{bind_address}:{server.server_port}"
    state.target_base = state.base_url
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield state
    finally:
        _stop_http_fixture(
            server, thread, "response-drop proxy", state.cancel_upstreams
        )
