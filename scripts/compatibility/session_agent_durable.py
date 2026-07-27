#!/usr/bin/env python3
"""Live Session↔Agent durable transport scenario using only public HTTP/SSE observations."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import queue
import shutil
import signal
import socket
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Final

ROOT: Final = Path(__file__).resolve().parents[2]
AUTH_SECRET: Final = "compatibility-hs256-not-real"
NAMESPACE: Final = "namespace-compatibility"
ASSERTIONS: Final = [
    "session-agent:admission-idempotency",
    "session-agent:durable-request-event",
    "session-agent:hitl-response",
    "session-agent:tool-approval",
    "session-agent:terminal",
    "session-agent:sse-replay",
]
PROCESSES: list[subprocess.Popen[bytes]] = []


def _b64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def sign_token(subject: str) -> str:
    header = _b64url(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    body = _b64url(json.dumps({"sub": subject, "exp": int(time.time()) + 3_600}).encode())
    signature = _b64url(hmac.new(AUTH_SECRET.encode(), f"{header}.{body}".encode(), hashlib.sha256).digest())
    return f"{header}.{body}.{signature}"


def _validate_lease(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("compatibility_scope_invalid")
    mongo = value.get("mongo")
    redis = value.get("redis")
    run_id = value.get("runId")
    if (
        not isinstance(run_id, str)
        or not run_id.startswith("run_")
        or not isinstance(mongo, dict)
        or not isinstance(mongo.get("database"), str)
        or not str(mongo["database"]).startswith("kokoro_test_")
        or not isinstance(redis, dict)
        or not isinstance(redis.get("database"), int)
        or not 8 <= int(redis["database"]) <= 15
    ):
        raise ValueError("compatibility_scope_invalid")
    return value


def _redis_url(lease: dict[str, object]) -> str:
    redis = lease["redis"]
    assert isinstance(redis, dict)
    return f"redis://127.0.0.1:6379/{redis['database']}"


def _mongo_database(lease: dict[str, object]) -> str:
    mongo = lease["mongo"]
    assert isinstance(mongo, dict)
    return str(mongo["database"])


def build_session_environment(
    lease: dict[str, object],
    *,
    session_port: int,
    hub_base_url: str,
    scratch: Path,
) -> dict[str, str]:
    return {
        "KOKORO_SESSION_PORT": str(session_port),
        "KOKORO_REDIS_URL": _redis_url(lease),
        "KOKORO_MESSAGE_STORE_MONGO_URL": "mongodb://127.0.0.1:27017",
        "KOKORO_MESSAGE_STORE_MONGO_DB": _mongo_database(lease),
        "KOKORO_WEB_ORIGIN": "http://127.0.0.1",
        "KOKORO_AUTH_MODE": "hs256",
        "KOKORO_AUTH_JWT_SECRET": AUTH_SECRET,
        "KOKORO_HUB_BASE_URL": hub_base_url,
        "KOKORO_INTERNAL_SECRET_SESSION": "compatibility-session-not-real",
        "KOKORO_BILLING_MODE": "off",
        "KOKORO_DEFAULT_BACKEND": "local_shell",
        "KOKORO_WORKSPACE_CONFIG": str(scratch / "storage.yaml"),
        "KOKORO_WORKSPACE_ROOT": str(scratch / "workspace"),
    }


def build_agent_environment(lease: dict[str, object], *, scratch: Path) -> dict[str, str]:
    return {
        "KOKORO_REDIS_URL": _redis_url(lease),
        "KOKORO_MONGO_URL": "mongodb://127.0.0.1:27017",
        "KOKORO_MONGO_DB": _mongo_database(lease),
        "KOKORO_LOCAL_FAKE_MODEL": "1",
        "KOKORO_LOCAL_FAKE_SCRIPT": "hitl",
        "KOKORO_AGENT_LOCAL_SHELL_ROOT": str(scratch / "workspace"),
        "KOKORO_WORKSPACE_CONFIG": str(scratch / "storage.yaml"),
        "KOKORO_SKILLS_DIR": str(scratch / "skills"),
        "KOKORO_PERSONAS_DIR": str(scratch / "personas"),
        "KOKORO_MCP_EGRESS_MODE": "off",
        "KOKORO_DRAIN_TIMEOUT_S": "5",
    }


def build_result(passed: bool, *, duration_ms: int) -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "scenarioId": "session-agent-durable-localfake",
        "outcome": "pass" if passed else "fail",
        "reasonCode": "ok" if passed else "session_agent_live_failed",
        "assertionIds": ASSERTIONS,
        "durationMs": max(0, duration_ms),
    }


class _HubHandler(BaseHTTPRequestHandler):
    seen_namespaces: list[str] = []

    def log_message(self, _format: str, *_args: object) -> None:
        return

    def do_GET(self) -> None:  # noqa: N802
        marker = "namespace="
        if marker in self.path:
            self.seen_namespaces.append(self.path.split(marker, 1)[1].split("&", 1)[0])
        payload = json.dumps({"data": {"skills": [], "mcp_servers": []}}).encode()
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


class SseReader:
    def __init__(self, url: str, token: str, last_event_id: int | None = None) -> None:
        headers = {"authorization": f"Bearer {token}", "accept": "text/event-stream"}
        if last_event_id is not None:
            headers["last-event-id"] = str(last_event_id)
        self.response = urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=60)
        self.events: queue.Queue[tuple[int, str, dict[str, object]]] = queue.Queue()
        self.error: BaseException | None = None
        threading.Thread(target=self._pump, daemon=True).start()

    def _pump(self) -> None:
        frame: dict[str, str] = {}
        try:
            for raw in self.response:
                line = raw.decode().rstrip("\n")
                if line.startswith("id: "):
                    frame["id"] = line[4:]
                elif line.startswith("event: "):
                    frame["event"] = line[7:]
                elif line.startswith("data: "):
                    frame["data"] = line[6:]
                elif line == "" and "data" in frame:
                    self.events.put((int(frame["id"]), frame["event"], json.loads(frame["data"])))
                    frame = {}
        except BaseException as error:  # surfaced by wait(), never treated as success
            self.error = error

    def wait(self, kind: str, timeout: float = 45.0) -> tuple[int, str, dict[str, object]]:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                event = self.events.get(timeout=min(0.5, deadline - time.monotonic()))
            except queue.Empty:
                if self.error is not None:
                    raise RuntimeError("compatibility_sse_read_failed") from self.error
                continue
            if event[1] == kind:
                return event
        raise TimeoutError(f"compatibility_sse_timeout:{kind}")

    def close(self) -> None:
        self.response.close()


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_port(port: int, timeout: float = 45.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with socket.socket() as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(("127.0.0.1", port)) == 0:
                return
        time.sleep(0.2)
    raise TimeoutError("compatibility_service_not_ready")


def _start(command: list[str], *, cwd: Path, env: dict[str, str]) -> subprocess.Popen[bytes]:
    process = subprocess.Popen(
        command,
        cwd=cwd,
        env={**os.environ, **env},
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    PROCESSES.append(process)
    return process


def _stop_all() -> None:
    for process in reversed(PROCESSES):
        if process.poll() is not None:
            continue
        try:
            os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=5)
        except (ProcessLookupError, subprocess.TimeoutExpired):
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
    PROCESSES.clear()


def _request(
    base_url: str,
    token: str,
    method: str,
    path: str,
    body: dict[str, object] | None = None,
) -> tuple[int, dict[str, object]]:
    request = urllib.request.Request(
        base_url + path,
        method=method,
        data=None if body is None else json.dumps(body).encode(),
        headers={
            "authorization": f"Bearer {token}",
            "content-type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return response.status, json.loads(response.read() or b"{}")
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read() or b"{}")


def run() -> dict[str, object]:
    started = time.monotonic()
    hub: ThreadingHTTPServer | None = None
    readers: list[SseReader] = []
    scratch: Path | None = None
    try:
        scope_file = os.environ.get("KOKORO_COMPAT_SCOPE_FILE")
        if not scope_file:
            raise ValueError("compatibility_scope_missing")
        lease = _validate_lease(json.loads(Path(scope_file).read_text()))
        (ROOT / "tmp").mkdir(exist_ok=True)
        scratch = Path(tempfile.mkdtemp(prefix="session-agent-", dir=ROOT / "tmp"))
        for directory in ["workspace", "hub", "skills", "personas"]:
            (scratch / directory).mkdir()
        (scratch / "storage.yaml").write_text(
            "workspace:\n"
            "  type: local\n"
            f"  root: {scratch / 'workspace'}\n"
            "hub:\n"
            "  type: local\n"
            f"  root: {scratch / 'hub'}\n",
        )

        hub = ThreadingHTTPServer(("127.0.0.1", 0), _HubHandler)
        threading.Thread(target=hub.serve_forever, daemon=True).start()
        hub_port = int(hub.server_address[1])
        session_port = _free_port()
        session = _start(
            ["npm", "run", "start"],
            cwd=ROOT / "kokoro-session",
            env=build_session_environment(
                lease,
                session_port=session_port,
                hub_base_url=f"http://127.0.0.1:{hub_port}",
                scratch=scratch,
            ),
        )
        _wait_port(session_port)
        agent = _start(
            ["uv", "run", "--locked", "kokoro-agent-worker"],
            cwd=ROOT / "kokoro-agent",
            env=build_agent_environment(lease, scratch=scratch),
        )
        if session.poll() is not None or agent.poll() is not None:
            raise RuntimeError("compatibility_child_exited")

        base_url = f"http://127.0.0.1:{session_port}"
        token = sign_token(NAMESPACE)
        session_id = f"ses_compat_{os.urandom(5).hex()}"
        idempotency_key = f"idem_{os.urandom(6).hex()}"
        status, receipt = _request(
            base_url,
            token,
            "POST",
            f"/sessions/{session_id}/messages",
            {"idempotency_key": idempotency_key, "content": "compatibility durable run"},
        )
        if status != 202 or not isinstance(receipt.get("run_id"), str):
            raise RuntimeError("compatibility_admission_failed")
        replay_status, replayed_receipt = _request(
            base_url,
            token,
            "POST",
            f"/sessions/{session_id}/messages",
            {"idempotency_key": idempotency_key, "content": "compatibility durable run"},
        )
        if replay_status != 202 or replayed_receipt != receipt:
            raise RuntimeError("compatibility_idempotency_failed")

        reader = SseReader(f"{base_url}/sessions/{session_id}/events", token)
        readers.append(reader)
        reader.wait("session.created")
        run_created = reader.wait("run.created")
        message_user = reader.wait("message.user")
        replay_reader = SseReader(
            f"{base_url}/sessions/{session_id}/events",
            token,
            last_event_id=run_created[0],
        )
        readers.append(replay_reader)
        replay_event = replay_reader.wait("message.user")
        if replay_event[0] != message_user[0]:
            raise RuntimeError("compatibility_replay_failed")

        first_pause = reader.wait("tool.awaiting_approval", timeout=60)
        first_payload = first_pause[2].get("payload")
        if not isinstance(first_payload, dict) or first_payload.get("kind") != "ask_user_question":
            raise RuntimeError("compatibility_hitl_question_missing")
        run_id = str(receipt["run_id"])
        resume_status, _ = _request(
            base_url,
            token,
            "POST",
            f"/sessions/{session_id}/runs/{run_id}/control",
            {
                "kind": "run.resume",
                "decision_id": f"dec_{os.urandom(6).hex()}",
                "decisions": [{
                    "type": "respond",
                    "tool_id": first_payload.get("tool_id"),
                    "response": "continue",
                }],
            },
        )
        if resume_status != 202:
            raise RuntimeError("compatibility_hitl_response_failed")

        second_pause = reader.wait("tool.awaiting_approval", timeout=60)
        second_payload = second_pause[2].get("payload")
        if not isinstance(second_payload, dict) or second_payload.get("kind") != "tool_approval":
            raise RuntimeError("compatibility_tool_approval_missing")
        approve_status, _ = _request(
            base_url,
            token,
            "POST",
            f"/sessions/{session_id}/runs/{run_id}/control",
            {
                "kind": "run.resume",
                "decision_id": f"dec_{os.urandom(6).hex()}",
                "decisions": [{"type": "approve", "tool_id": second_payload.get("tool_id")}],
            },
        )
        if approve_status != 202:
            raise RuntimeError("compatibility_tool_approve_failed")
        completed = reader.wait("run.completed", timeout=60)
        completed_payload = completed[2].get("payload")
        if not isinstance(completed_payload, dict) or completed_payload.get("status") != "completed":
            raise RuntimeError("compatibility_terminal_failed")
        if NAMESPACE not in _HubHandler.seen_namespaces:
            raise RuntimeError("compatibility_namespace_failed")
        return build_result(True, duration_ms=int((time.monotonic() - started) * 1000))
    except BaseException:
        return build_result(False, duration_ms=int((time.monotonic() - started) * 1000))
    finally:
        for reader in readers:
            reader.close()
        _stop_all()
        if hub is not None:
            hub.shutdown()
            hub.server_close()
        if scratch is not None:
            shutil.rmtree(scratch, ignore_errors=True)


def main() -> int:
    result = run()
    with os.fdopen(3, "w", encoding="utf-8", closefd=False) as machine:
        machine.write(json.dumps(result, separators=(",", ":")) + "\n")
        machine.flush()
    return 0 if result["outcome"] == "pass" else 1


def _terminate(_signal: int, _frame: object) -> None:
    _stop_all()
    raise SystemExit(143)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, _terminate)
    signal.signal(signal.SIGTERM, _terminate)
    raise SystemExit(main())
