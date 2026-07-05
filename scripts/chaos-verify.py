#!/usr/bin/env python3
"""崩溃混沌验证。场景一：认领 worker 在 HITL 暂停期间被 SIGKILL，另一 worker 心跳收养其
control 流并接续 resume 到终态。场景二：session 进程在暂停期间被 SIGKILL，重启后从持久层
收敛恢复（snapshot 暂停现场完好，resume/审批续走到终态）。场景三：双 session 实例跨读跨控。
前置：redis:6379 + mongo:27017。

关键点：ledger/checkpoint 走 mongo（生产跨 pod 形态——双 worker 无共享文件系统假设）；
sqlite 单机档语义由 tests/test_storage.py 的同语义矩阵覆盖。
KOKORO_LEASE_HEARTBEAT_S=2 让收养在秒级发生。
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

from procutil import ensure_port_free, spawn, stop

ROOT = Path(__file__).resolve().parents[1]
SESSION_PORT = int(os.environ.get("CHV_SESSION_PORT", "3904"))
BASE = f"http://127.0.0.1:{SESSION_PORT}"
REDIS_URL = os.environ.get("CHV_REDIS_URL", "redis://127.0.0.1:6379/10")
MONGO_URL = os.environ.get("CHV_MONGO_URL", "mongodb://127.0.0.1:27017")
MONGO_DB = "kokoro_chaos_verify"

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail and not ok else ""))
    if not ok:
        FAILURES.append(f"{name}: {detail}")


def http(method: str, path: str, body: dict | None = None, base: str | None = None):
    req = urllib.request.Request(
        (base or BASE) + path,
        method=method,
        data=None if body is None else json.dumps(body).encode(),
        headers={"content-type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


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


def wait_run_done(sid: str, timeout: float = 90.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        _, snap = http("GET", f"/sessions/{sid}")
        if "active_run" not in snap:
            return True
        time.sleep(0.5)
    return False


def spawn_worker(scratch: Path, tag: str) -> subprocess.Popen:
    env = {
        **os.environ,
        "KOKORO_LOCAL_FAKE_MODEL": "1",
        "KOKORO_LOCAL_FAKE_SCRIPT": "hitl",
        "KOKORO_STREAM_BACKEND": "redis",
        "KOKORO_REDIS_URL": REDIS_URL,
        "KOKORO_LEDGER_BACKEND": "mongo",
        "KOKORO_CHECKPOINT_BACKEND": "mongo",
        "KOKORO_MONGO_URL": MONGO_URL,
        "KOKORO_MONGO_DB": MONGO_DB,
        # 秒级心跳：收养窗口从默认 30s 压到 2s，混沌验证不用干等。
        "KOKORO_LEASE_HEARTBEAT_S": "2",
    }
    return spawn(["uv", "run", "kokoro-agent-worker"], cwd=ROOT / "kokoro-agent", env=env,
                 log=scratch / f"agent-{tag}.log")


def main() -> int:
    scratch = Path(os.environ.get("TMPDIR", "/tmp")) / f"kokoro-chv-{uuid.uuid4().hex[:6]}"
    scratch.mkdir(parents=True)
    subprocess.run(["redis-cli", "-u", REDIS_URL, "flushdb"], check=True, capture_output=True)
    subprocess.run(
        ["docker", "exec", "kokoro-e2e-mongo", "mongosh", "--quiet", "--eval",
         f'db.getSiblingDB("{MONGO_DB}").dropDatabase()'],
        check=False, capture_output=True,
    )
    (scratch / "namespaces.json").write_text(json.dumps({"namespaces": {"team-chv": {}}}))
    session_env: dict[str, str] = {
        **os.environ,
        "KOKORO_SESSION_PORT": str(SESSION_PORT),
        "KOKORO_STREAM_BACKEND": "redis",
        "KOKORO_REDIS_URL": REDIS_URL,
        "KOKORO_MESSAGE_STORE_BACKEND": "mongo",
        "KOKORO_MESSAGE_STORE_MONGO_URL": MONGO_URL,
        "KOKORO_MESSAGE_STORE_MONGO_DB": MONGO_DB,
        "KOKORO_NAMESPACE": "team-chv",
        "KOKORO_NAMESPACES_FILE": str(scratch / "namespaces.json"),
    }
    def spawn_session(tag: str) -> subprocess.Popen:
        return spawn(["npm", "run", "start"], cwd=ROOT / "kokoro-session", env=session_env,
                     log=scratch / f"session-{tag}.log")

    ensure_port_free(SESSION_PORT)
    ensure_port_free(SESSION_PORT + 7)  # S3 的 B 实例端口
    session_proc = spawn_session("1")
    worker_a = spawn_worker(scratch, "a")
    worker_b: subprocess.Popen | None = None
    try:
        check("session 端口就绪", wait_port(SESSION_PORT))
        time.sleep(1.5)
        sid = f"ses_chv_{uuid.uuid4().hex[:8]}"
        st, receipt = http("POST", f"/sessions/{sid}/messages", {
            "idempotency_key": f"idem_{uuid.uuid4().hex[:8]}", "content": "帮我写个文件"})
        check("POST messages → 202", st == 202, f"{st} {receipt}")
        run_id = receipt.get("run_id", "")

        seen: set[str] = set()
        pause1 = wait_pause(sid, seen)
        check("ask_user 暂停出现（worker A 认领）", pause1 is not None, str(pause1))
        if pause1 is None:
            return 1

        # 混沌注入：SIGKILL 认领 worker 全进程组——uv 包装层和真 worker 一个都不留。
        stop(worker_a, sig=signal.SIGKILL)
        check("worker A 已被 SIGKILL", worker_a.returncode is not None)

        worker_b = spawn_worker(scratch, "b")
        time.sleep(4)  # ≥1 个心跳周期：B 扫描暂停 run 并收养 control 监听

        # 用户此刻才作答：resume 必须被 B 接住。
        http("POST", f"/sessions/{sid}/runs/{run_id}/control", {
            "kind": "run.resume", "decision_id": f"dec_{uuid.uuid4().hex[:8]}",
            "decisions": [{"type": "respond", "tool_id": pause1["tool_id"], "response": "chaos.txt"}]})
        pause2 = wait_pause(sid, seen)
        check("B 接住 resume 并推进到审批暂停", pause2 is not None and pause2["kind"] == "tool_approval",
              str(pause2))
        if pause2 is None:
            return 1
        http("POST", f"/sessions/{sid}/runs/{run_id}/control", {
            "kind": "run.resume", "decision_id": f"dec_{uuid.uuid4().hex[:8]}",
            "decisions": [{"type": "approve", "tool_id": pause2["tool_id"]}]})
        check("run 在 B 上走到终态", wait_run_done(sid))

        # 场景二：session 进程崩溃后从持久层收敛恢复。
        sid2 = f"ses_chv_{uuid.uuid4().hex[:8]}"
        st, receipt2 = http("POST", f"/sessions/{sid2}/messages", {
            "idempotency_key": f"idem_{uuid.uuid4().hex[:8]}", "content": "帮我写个文件"})
        check("S2: POST messages → 202", st == 202, f"{st} {receipt2}")
        run2 = receipt2.get("run_id", "")
        seen2: set[str] = set()
        pause_s1 = wait_pause(sid2, seen2)
        check("S2: ask_user 暂停出现", pause_s1 is not None, str(pause_s1))
        if pause_s1 is None:
            return 1
        # SIGKILL 全进程组：只杀 npm 包装层的话 tsx 子进程仍在服务，混沌注入等于没发生。
        stop(session_proc, sig=signal.SIGKILL)
        check("S2: session 已被 SIGKILL", session_proc.returncode is not None)
        ensure_port_free(SESSION_PORT)
        session_proc = spawn_session("2")
        check("S2: session 重启就绪", wait_port(SESSION_PORT))
        time.sleep(1.0)
        _, snap = http("GET", f"/sessions/{sid2}")
        recovered = [p for p in snap.get("pending_pauses", []) if p["status"] == "pending"]
        check("S2: 重启后 snapshot 暂停现场完好", len(recovered) == 1
              and recovered[0]["pause_id"] == pause_s1["pause_id"], str(recovered))
        http("POST", f"/sessions/{sid2}/runs/{run2}/control", {
            "kind": "run.resume", "decision_id": f"dec_{uuid.uuid4().hex[:8]}",
            "decisions": [{"type": "respond", "tool_id": pause_s1["tool_id"], "response": "s2.txt"}]})
        pause_s2 = wait_pause(sid2, seen2)
        check("S2: resume 续走到审批暂停", pause_s2 is not None and pause_s2["kind"] == "tool_approval",
              str(pause_s2))
        if pause_s2 is None:
            return 1
        http("POST", f"/sessions/{sid2}/runs/{run2}/control", {
            "kind": "run.resume", "decision_id": f"dec_{uuid.uuid4().hex[:8]}",
            "decisions": [{"type": "approve", "tool_id": pause_s2["tool_id"]}]})
        check("S2: run 走到终态", wait_run_done(sid2))

        print(f"  logs: {scratch}")
        # 场景三：双 session 实例（多 pod 形态）——B 实例跨读/跨控同一 run，mongo 为一致性真源。
        port_b = SESSION_PORT + 7
        base_b = f"http://127.0.0.1:{port_b}"
        env_b = {**session_env, "KOKORO_SESSION_PORT": str(port_b)}
        session_b = spawn(["npm", "run", "start"], cwd=ROOT / "kokoro-session", env=env_b,
                          log=scratch / "session-b.log")
        try:
            check("S3: session B 端口就绪", wait_port(port_b))
            sid3 = f"ses_chv_{uuid.uuid4().hex[:8]}"
            st, receipt3 = http("POST", f"/sessions/{sid3}/messages", {
                "idempotency_key": f"idem_{uuid.uuid4().hex[:8]}", "content": "帮我写个文件"})
            check("S3: A 受理 → 202", st == 202, f"{st} {receipt3}")
            run3 = receipt3.get("run_id", "")
            seen3: set[str] = set()
            pause3 = wait_pause(sid3, seen3)
            check("S3: 暂停出现（A 侧）", pause3 is not None, str(pause3))
            # 跨实例读：B 的 snapshot 从 mongo 看到同一活跃 run 与暂停点。
            st, snap_b = http("GET", f"/sessions/{sid3}", base=base_b)
            pending_b = [x for x in snap_b.get("pending_pauses", []) if x["status"] == "pending"]
            check("S3: B 跨读 snapshot（活跃 run + 暂停点）",
                  st == 200 and (snap_b.get("active_run") or {}).get("run_id") == run3
                  and len(pending_b) == 1, f"{st} pauses={len(pending_b)}")
            # 跨实例插话：经 B 对活跃 run POST → 202 转 steer。
            st, steer_b = http("POST", f"/sessions/{sid3}/messages", {
                "idempotency_key": f"idem_{uuid.uuid4().hex[:8]}", "content": "顺便注意编码"},
                base=base_b)
            check("S3: B 跨发插话 → 202 归属同 run", st == 202 and steer_b.get("run_id") == run3,
                  f"{st} {steer_b}")
            # 跨实例控制：经 B 提交 resume，worker 经 redis control 流接单。
            assert pause3 is not None
            st, _ = http("POST", f"/sessions/{sid3}/runs/{run3}/control", {
                "kind": "run.resume", "decision_id": f"dec_{uuid.uuid4().hex[:8]}",
                "decisions": [{"type": "respond", "tool_id": pause3["tool_id"],
                               "response": "文件名 chaos-b.txt"}]}, base=base_b)
            check("S3: B 跨发 resume → 202", st == 202, str(st))
            pause3b = wait_pause(sid3, seen3)
            if pause3b is not None:
                http("POST", f"/sessions/{sid3}/runs/{run3}/control", {
                    "kind": "run.resume", "decision_id": f"dec_{uuid.uuid4().hex[:8]}",
                    "decisions": [{"type": "approve", "tool_id": pause3b["tool_id"]}]},
                    base=base_b)
            check("S3: run 收敛终态（A 侧落库）", wait_run_done(sid3))
        finally:
            stop(session_b, sig=signal.SIGKILL)

        # 终判必须在全部场景之后：S3 的失败绝不允许被提前 return 吞掉。
        if FAILURES:
            print(f"\nCHAOS VERIFY FAIL — {len(FAILURES)} 项")
            for f in FAILURES:
                print(f"  - {f}")
            return 1
        print("\nCHAOS VERIFY PASS — worker 崩溃收养 + session 崩溃恢复 + 双 session 实例 三场景全绿")
        return 0
    finally:
        stop(session_proc)
        for proc in (worker_a, worker_b):
            if proc is not None:
                stop(proc)


if __name__ == "__main__":
    sys.exit(main())
