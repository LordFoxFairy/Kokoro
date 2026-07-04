#!/usr/bin/env python3
"""Langfuse trace 连续性验证：HITL 暂停/恢复的各执行段 trace 可按 session/run 归组。

前置：redis:6379 + mongo:27017 + 自托管 langfuse（:3310，headless init 密钥）。
agent 用 LocalFake HITL 脚本（确定性双暂停），断言 Langfuse API 上：
① 该 session 的 trace ≥ 2（暂停切段）；② 全部携带同一 kokoro_run_id 元数据。
"""

from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SESSION_PORT = int(os.environ.get("TRV_SESSION_PORT", "3903"))
BASE = f"http://127.0.0.1:{SESSION_PORT}"
REDIS_URL = os.environ.get("TRV_REDIS_URL", "redis://127.0.0.1:6379/11")
MONGO_URL = os.environ.get("TRV_MONGO_URL", "mongodb://127.0.0.1:27017")
MONGO_DB = "kokoro_trace_verify"
LANGFUSE_HOST = os.environ.get("TRV_LANGFUSE_HOST", "http://127.0.0.1:3310")
LANGFUSE_PUBLIC = os.environ.get("TRV_LANGFUSE_PUBLIC", "pk-lf-kokoro-local")
LANGFUSE_SECRET = os.environ.get("TRV_LANGFUSE_SECRET", "sk-lf-kokoro-local")

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail and not ok else ""))
    if not ok:
        FAILURES.append(f"{name}: {detail}")


def http(method: str, path: str, body: dict | None = None):
    req = urllib.request.Request(
        BASE + path,
        method=method,
        data=None if body is None else json.dumps(body).encode(),
        headers={"content-type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def langfuse_traces(session_id: str) -> list[dict]:
    token = base64.b64encode(f"{LANGFUSE_PUBLIC}:{LANGFUSE_SECRET}".encode()).decode()
    req = urllib.request.Request(
        f"{LANGFUSE_HOST}/api/public/traces?sessionId={session_id}&limit=50",
        headers={"authorization": f"Basic {token}"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read()).get("data", [])


def wait_port(port: int, timeout: float = 30.0) -> bool:
    import socket

    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket() as s:
            s.settimeout(0.5)
            if s.connect_ex(("127.0.0.1", port)) == 0:
                return True
        time.sleep(0.3)
    return False


def wait_pause(sid: str, seen: set[str], timeout: float = 60.0) -> dict | None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        _, snap = http("GET", f"/sessions/{sid}")
        for pause in snap.get("pending_pauses", []):
            if pause["status"] == "pending" and pause["pause_id"] not in seen:
                seen.add(pause["pause_id"])
                return pause
        time.sleep(0.5)
    return None


def wait_run_done(sid: str, timeout: float = 60.0) -> bool:
    # snapshot 契约：active_run 缺席 = run 已终态（RunStatus 只有 active|terminal）。
    deadline = time.time() + timeout
    while time.time() < deadline:
        _, snap = http("GET", f"/sessions/{sid}")
        if "active_run" not in snap:
            return True
        time.sleep(0.5)
    return False


def main() -> int:
    scratch = Path(os.environ.get("TMPDIR", "/tmp")) / f"kokoro-trv-{uuid.uuid4().hex[:6]}"
    scratch.mkdir(parents=True)
    subprocess.run(["redis-cli", "-u", REDIS_URL, "flushdb"], check=True, capture_output=True)
    subprocess.run(
        ["docker", "exec", "kokoro-e2e-mongo", "mongosh", "--quiet", "--eval",
         f'db.getSiblingDB("{MONGO_DB}").dropDatabase()'],
        check=False, capture_output=True,
    )
    (scratch / "namespaces.json").write_text(json.dumps({"namespaces": {"team-trv": {}}}))

    session_env = {
        **os.environ,
        "KOKORO_SESSION_PORT": str(SESSION_PORT),
        "KOKORO_STREAM_BACKEND": "redis",
        "KOKORO_REDIS_URL": REDIS_URL,
        "KOKORO_MESSAGE_STORE_BACKEND": "mongo",
        "KOKORO_MESSAGE_STORE_MONGO_URL": MONGO_URL,
        "KOKORO_MESSAGE_STORE_MONGO_DB": MONGO_DB,
        "KOKORO_NAMESPACE": "team-trv",
        "KOKORO_NAMESPACES_FILE": str(scratch / "namespaces.json"),
    }
    agent_env = {
        **os.environ,
        "KOKORO_LOCAL_FAKE_MODEL": "1",
        "KOKORO_LOCAL_FAKE_SCRIPT": "hitl",
        "KOKORO_STREAM_BACKEND": "redis",
        "KOKORO_REDIS_URL": REDIS_URL,
        "KOKORO_LEDGER_BACKEND": "sqlite",
        "KOKORO_LEDGER_DB": str(scratch / "ledger.db"),
        "KOKORO_CHECKPOINT_BACKEND": "sqlite",
        "KOKORO_CHECKPOINT_DB": str(scratch / "checkpoints.db"),
        "LANGFUSE_PUBLIC_KEY": LANGFUSE_PUBLIC,
        "LANGFUSE_SECRET_KEY": LANGFUSE_SECRET,
        "LANGFUSE_HOST": LANGFUSE_HOST,
    }
    session_proc = subprocess.Popen(
        ["npm", "run", "start"], cwd=ROOT / "kokoro-session", env=session_env,
        stdout=(scratch / "session.log").open("w"), stderr=subprocess.STDOUT,
    )
    agent_proc = subprocess.Popen(
        ["uv", "run", "kokoro-agent-worker"], cwd=ROOT / "kokoro-agent", env=agent_env,
        stdout=(scratch / "agent.log").open("w"), stderr=subprocess.STDOUT,
    )
    try:
        check("session 端口就绪", wait_port(SESSION_PORT))
        time.sleep(1.5)
        sid = f"ses_trv_{uuid.uuid4().hex[:8]}"
        st, receipt = http("POST", f"/sessions/{sid}/messages", {
            "idempotency_key": f"idem_{uuid.uuid4().hex[:8]}", "content": "帮我写个文件"})
        check("POST messages → 202", st == 202, f"{st} {receipt}")
        run_id = receipt.get("run_id", "")

        seen: set[str] = set()
        pause1 = wait_pause(sid, seen)
        check("ask_user 暂停出现", pause1 is not None and pause1["kind"] == "ask_user_question",
              str(pause1))
        if pause1 is None:
            return 1
        http("POST", f"/sessions/{sid}/runs/{run_id}/control", {
            "kind": "run.resume", "decision_id": f"dec_{uuid.uuid4().hex[:8]}",
            "decisions": [{"type": "respond", "tool_id": pause1["tool_id"], "response": "trace.txt"}]})
        pause2 = wait_pause(sid, seen)
        check("write_file 审批暂停出现", pause2 is not None and pause2["kind"] == "tool_approval",
              str(pause2))
        if pause2 is None:
            return 1
        http("POST", f"/sessions/{sid}/runs/{run_id}/control", {
            "kind": "run.resume", "decision_id": f"dec_{uuid.uuid4().hex[:8]}",
            "decisions": [{"type": "approve", "tool_id": pause2["tool_id"]}]})
        check("run 到达终态（active_run 释放）", wait_run_done(sid))

        # SDK 异步批量上报：轮询 Langfuse 直到该 session 的 trace 齐（暂停切段 ≥2）。
        traces: list[dict] = []
        deadline = time.time() + 90
        while time.time() < deadline:
            traces = langfuse_traces(sid)
            if len(traces) >= 2:
                break
            time.sleep(3)
        check("trace ≥ 2（暂停切段各自成 trace）", len(traces) >= 2, f"got {len(traces)}")
        run_ids = {str((t.get("metadata") or {}).get("kokoro_run_id")) for t in traces}
        check("全部 trace 携带同一 kokoro_run_id", run_ids == {run_id}, str(run_ids))
        sessions = {t.get("sessionId") for t in traces}
        check("全部 trace 归于同一 langfuse session", sessions == {sid}, str(sessions))

        print(f"  traces: {len(traces)}  logs: {scratch}")
        if FAILURES:
            print(f"\nTRACE VERIFY FAIL — {len(FAILURES)} 项")
            return 1
        print("\nTRACE VERIFY PASS — HITL 暂停/恢复 trace 连续性达成")
        return 0
    finally:
        session_proc.terminate()
        agent_proc.terminate()


if __name__ == "__main__":
    sys.exit(main())
