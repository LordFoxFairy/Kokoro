#!/usr/bin/env python3
"""真实模型盲区验证：glm-5（openai-compat + reasoning）跨栈压实 thinking 通道与 subagent 事件。

场景 A：明令经 task 工具委派 researcher 子代理 → 断言 subagent.started/finished（+文本流）。
场景 B：普通提问 → 断言 thinking.delta ≥ 1 且 message.completed 非空。
前置：redis:6379 + mongo:27017 + kokoro-agent/.env 真实凭据（OPENAI_BASE_URL/OPENAI_API_KEY）。
"""

from __future__ import annotations

import json
import os
import queue
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SESSION_PORT = int(os.environ.get("RMV_SESSION_PORT", "3902"))
BASE = f"http://127.0.0.1:{SESSION_PORT}"
REDIS_URL = os.environ.get("RMV_REDIS_URL", "redis://127.0.0.1:6379/13")
MONGO_URL = os.environ.get("RMV_MONGO_URL", "mongodb://127.0.0.1:27017")
MONGO_DB = "kokoro_real_model_verify"

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    mark = "PASS" if ok else "FAIL"
    print(f"  [{mark}] {name}" + (f" — {detail}" if detail and not ok else ""))
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


class SseReader:
    def __init__(self, path: str):
        self.q: queue.Queue[tuple[int, str, dict]] = queue.Queue()
        req = urllib.request.Request(BASE + path)
        self.resp = urllib.request.urlopen(req, timeout=240)
        threading.Thread(target=self._pump, daemon=True).start()

    def _pump(self) -> None:
        frame: dict[str, str] = {}
        try:
            for raw in self.resp:
                line = raw.decode().rstrip("\n")
                if line.startswith("id: "):
                    frame["id"] = line[4:]
                elif line.startswith("event: "):
                    frame["event"] = line[7:]
                elif line.startswith("data: "):
                    frame["data"] = line[6:]
                elif line == "" and "data" in frame:
                    self.q.put(
                        (int(frame.get("id", -1)), frame.get("event", "?"), json.loads(frame["data"]))
                    )
                    frame = {}
        except Exception:
            pass


def collect_run(sse: SseReader, timeout: float = 210.0) -> list[tuple[str, dict]]:
    """收流直到终态事件；返回 (kind, payload) 序列。真实模型慢，超时给足。"""
    out: list[tuple[str, dict]] = []
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            _, kind, event = sse.q.get(timeout=max(0.1, deadline - time.time()))
        except queue.Empty:
            break
        out.append((kind, event.get("payload", {})))
        if kind in ("run.completed", "run.failed"):
            break
    return out


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


def load_agent_env() -> dict[str, str]:
    env_file = ROOT / "kokoro-agent" / ".env"
    creds: dict[str, str] = {}
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            creds[key] = value
    for required in ("OPENAI_BASE_URL", "OPENAI_API_KEY"):
        if not creds.get(required):
            raise SystemExit(f"missing {required} in kokoro-agent/.env")
    return creds


def main() -> int:
    scratch = Path(os.environ.get("TMPDIR", "/tmp")) / f"kokoro-rmv-{uuid.uuid4().hex[:6]}"
    scratch.mkdir(parents=True)
    subprocess.run(["redis-cli", "-u", REDIS_URL, "flushdb"], check=True, capture_output=True)
    subprocess.run(
        ["docker", "exec", "kokoro-e2e-mongo", "mongosh", "--quiet", "--eval",
         f'db.getSiblingDB("{MONGO_DB}").dropDatabase()'],
        check=False, capture_output=True,
    )
    (scratch / "namespaces.json").write_text(json.dumps({
        "namespaces": {
            "team-rmv": {
                "model_policy": {"default": {"provider": "openai", "name": "glm-5"}},
            }
        }
    }))

    creds = load_agent_env()
    session_env = {
        **os.environ,
        "KOKORO_SESSION_PORT": str(SESSION_PORT),
        "KOKORO_STREAM_BACKEND": "redis",
        "KOKORO_REDIS_URL": REDIS_URL,
        "KOKORO_MESSAGE_STORE_BACKEND": "mongo",
        "KOKORO_MESSAGE_STORE_MONGO_URL": MONGO_URL,
        "KOKORO_MESSAGE_STORE_MONGO_DB": MONGO_DB,
        "KOKORO_NAMESPACE": "team-rmv",
        "KOKORO_NAMESPACES_FILE": str(scratch / "namespaces.json"),
    }
    agent_env = {
        **{k: v for k, v in os.environ.items() if k != "KOKORO_DISABLE_STREAMING"},
        "OPENAI_BASE_URL": creds["OPENAI_BASE_URL"],
        "OPENAI_API_KEY": creds["OPENAI_API_KEY"],
        # thinking 通道验证需要流式 + reasoning 抽取包装（ChatDeepSeek）。
        "KOKORO_OPENAI_REASONING": "1",
        "KOKORO_STREAM_BACKEND": "redis",
        "KOKORO_REDIS_URL": REDIS_URL,
        "KOKORO_RUN_STATE_BACKEND": "sqlite",
        "KOKORO_RUN_STATE_DB": str(scratch / "run-state.db"),
        "KOKORO_CHECKPOINT_BACKEND": "sqlite",
        "KOKORO_CHECKPOINT_DB": str(scratch / "checkpoints.db"),
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

        # 场景 B：thinking 通道（先跑短的）。
        sid_b = f"ses_rmv_{uuid.uuid4().hex[:8]}"
        sse_b = SseReader(f"/sessions/{sid_b}/events")
        st, receipt = http("POST", f"/sessions/{sid_b}/messages", {
            "idempotency_key": f"idem_{uuid.uuid4().hex[:8]}",
            "content": "为什么天空是蓝色的？认真想清楚再用两句话回答。",
        })
        check("B: POST messages → 202", st == 202, f"{st} {receipt}")
        events_b = collect_run(sse_b)
        kinds_b = [k for k, _ in events_b]
        thinking = sum(1 for k in kinds_b if k == "thinking.delta")
        completed_b = [p for k, p in events_b if k == "message.completed"]
        check("B: thinking.delta ≥ 1", thinking >= 1, f"kinds={kinds_b}")
        check("B: message.completed 非空", bool(completed_b and completed_b[-1].get("content")))
        check("B: run.completed 收尾", kinds_b[-1:] == ["run.completed"], f"kinds={kinds_b}")
        usage = next((p.get("token_usage") for k, p in events_b if k == "run.completed"), None)
        check("B: token_usage 上 wire", isinstance(usage, dict) and usage.get("input_tokens", 0) > 0,
              str(usage))

        # 场景 A：subagent 委派事件。
        sid_a = f"ses_rmv_{uuid.uuid4().hex[:8]}"
        sse_a = SseReader(f"/sessions/{sid_a}/events")
        st, receipt = http("POST", f"/sessions/{sid_a}/messages", {
            "idempotency_key": f"idem_{uuid.uuid4().hex[:8]}",
            "content": "请务必使用 task 工具把这个问题委派给 researcher 子代理来回答（不要自己直接回答）："
                       "二分查找的时间复杂度是多少？子代理返回后你用一句话总结。",
        })
        check("A: POST messages → 202", st == 202, f"{st} {receipt}")
        events_a = collect_run(sse_a)
        kinds_a = [k for k, _ in events_a]
        started = [p for k, p in events_a if k == "subagent.started"]
        finished = [p for k, p in events_a if k == "subagent.finished"]
        check("A: subagent.started 出现", bool(started), f"kinds={kinds_a}")
        check("A: subagent.finished 出现且未失败",
              bool(finished) and not finished[-1].get("failed"), str(finished[-1:] or kinds_a))
        check("A: subagent 归属 built-in researcher",
              bool(started) and started[0].get("name") == "researcher"
              and started[0].get("source") == "built-in", str(started[:1]))
        subtext = sum(1 for k in kinds_a if k.startswith("subagent.text"))
        check("A: subagent 文本流出现", subtext >= 1, f"kinds={kinds_a}")
        check("A: run.completed 收尾", kinds_a[-1:] == ["run.completed"], f"kinds={kinds_a}")

        print(f"  logs: {scratch}")
        if FAILURES:
            print(f"\nREAL-MODEL VERIFY FAIL — {len(FAILURES)} 项：")
            for f in FAILURES:
                print(f"  - {f}")
            return 1
        print("\nREAL-MODEL VERIFY PASS — thinking 通道 + subagent 事件真栈全绿")
        return 0
    finally:
        session_proc.terminate()
        agent_proc.terminate()


if __name__ == "__main__":
    sys.exit(main())
