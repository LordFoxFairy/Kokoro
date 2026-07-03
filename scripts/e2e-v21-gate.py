#!/usr/bin/env python3
"""v2.1 跨栈 e2e 门禁：真 redis+mongo，agent(LocalFake HITL 脚本)→session→SSE 全链断言。

覆盖：POST messages 幂等/409 准入、session.created/run.created 合成、ask_user respond、
write_file 审批 approve、decision_id 幂等、snapshot 暂停点恢复、Last-Event-ID 续传、
终态收口后可开新 run。前置：redis:6379 + mongo:27017 + 两仓依赖已装。
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
SESSION_PORT = int(os.environ.get("E2E_SESSION_PORT", "3901"))
BASE = f"http://127.0.0.1:{SESSION_PORT}"
REDIS_URL = os.environ.get("E2E_REDIS_URL", "redis://127.0.0.1:6379/14")
MONGO_URL = os.environ.get("E2E_MONGO_URL", "mongodb://127.0.0.1:27017")
MONGO_DB = "kokoro_e2e_v21"
SID = f"ses_e2e_{uuid.uuid4().hex[:8]}"

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    mark = "PASS" if ok else "FAIL"
    print(f"  [{mark}] {name}" + (f" — {detail}" if detail and not ok else ""))
    if not ok:
        FAILURES.append(f"{name}: {detail}")


def http(method: str, path: str, body: dict | None = None, headers: dict | None = None):
    req = urllib.request.Request(
        BASE + path,
        method=method,
        data=None if body is None else json.dumps(body).encode(),
        headers={"content-type": "application/json", **(headers or {})},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


class SseReader:
    """后台线程读 SSE，帧入队列；wait() 按谓词取帧。"""

    def __init__(self, path: str, last_event_id: str | None = None):
        self.q: queue.Queue[tuple[int, str, dict]] = queue.Queue()
        self.seen: list[tuple[int, str]] = []
        headers = {} if last_event_id is None else {"last-event-id": last_event_id}
        req = urllib.request.Request(BASE + path, headers=headers)
        self.resp = urllib.request.urlopen(req, timeout=60)
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
                    item = (int(frame.get("id", -1)), frame.get("event", "?"), json.loads(frame["data"]))
                    self.seen.append((item[0], item[1]))
                    self.q.put(item)
                    frame = {}
        except Exception:
            pass  # 连接收束即停

    def wait(self, pred, timeout: float = 30.0):
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                item = self.q.get(timeout=deadline - time.time())
            except queue.Empty:
                break
            if pred(item):
                return item
        return None


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


def main() -> int:
    scratch = Path(os.environ.get("TMPDIR", "/tmp")) / f"kokoro-e2e-{uuid.uuid4().hex[:6]}"
    scratch.mkdir(parents=True)
    subprocess.run(["redis-cli", "-u", REDIS_URL, "flushdb"], check=True, capture_output=True)
    subprocess.run(
        ["docker", "exec", "kokoro-e2e-mongo", "mongosh", "--quiet", "--eval",
         f'db.getSiblingDB("{MONGO_DB}").dropDatabase()'],
        check=False, capture_output=True,
    )

    session_env = {
        **os.environ,
        "KOKORO_SESSION_PORT": str(SESSION_PORT),
        "KOKORO_STREAM_BACKEND": "redis",
        "KOKORO_REDIS_URL": REDIS_URL,
        "KOKORO_MESSAGE_STORE_BACKEND": "mongo",
        "KOKORO_MESSAGE_STORE_MONGO_URL": MONGO_URL,
        "KOKORO_MESSAGE_STORE_MONGO_DB": MONGO_DB,
        # write_file 同时配 审批+审核：批参数 → 执行 → 审结果（串联双暂停，实证缓存防双跑）。
        "KOKORO_REVIEW_TOOLS": "write_file",
    }
    agent_env = {
        **os.environ,
        "KOKORO_STREAM_BACKEND": "redis",
        "KOKORO_REDIS_URL": REDIS_URL,
        "KOKORO_LOCAL_FAKE_MODEL": "1",
        "KOKORO_LOCAL_FAKE_SCRIPT": "hitl",
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
        time.sleep(1.5)  # worker 订阅请求流的启动窗口

        # 1. 发消息 + 幂等 + 409 准入
        k1 = f"idem_{uuid.uuid4().hex[:8]}"
        st, receipt = http("POST", f"/sessions/{SID}/messages", {"idempotency_key": k1, "content": "帮我写个文件然后总结"})
        check("POST messages → 202", st == 202, f"{st} {receipt}")
        run_id = receipt.get("run_id", "")
        st2, receipt2 = http("POST", f"/sessions/{SID}/messages", {"idempotency_key": k1, "content": "帮我写个文件然后总结"})
        check("同 idempotency_key 重放同 receipt", st2 == 202 and receipt2 == receipt, f"{st2} {receipt2}")

        sse = SseReader(f"/sessions/{SID}/events")
        check("SSE: session.created", sse.wait(lambda i: i[1] == "session.created") is not None)
        check("SSE: run.created", sse.wait(lambda i: i[1] == "run.created" and i[2]["payload"]["run_id"] == run_id) is not None)

        # 2. ask_user 暂停
        awaiting1 = sse.wait(lambda i: i[1] == "tool.awaiting_approval")
        check("SSE: ask_user awaiting", awaiting1 is not None and awaiting1[2]["payload"]["kind"] == "ask_user_question",
              json.dumps(awaiting1[2]["payload"] if awaiting1 else {}, ensure_ascii=False)[:200])
        st3, body3 = http("POST", f"/sessions/{SID}/messages", {"idempotency_key": f"idem_{uuid.uuid4().hex[:8]}", "content": "again"})
        check("活跃 run 期间新消息 → 409", st3 == 409 and body3.get("error") == "session_run_active", f"{st3} {body3}")

        st4, snap = http("GET", f"/sessions/{SID}")
        pending = [p for p in snap.get("pending_pauses", []) if p["status"] == "pending"]
        check("snapshot 暂停点可恢复", st4 == 200 and len(pending) == 1 and pending[0]["kind"] == "ask_user_question", f"{st4} pauses={len(pending)}")

        tool_id1 = awaiting1[2]["payload"]["tool_id"] if awaiting1 else "?"
        d1 = f"dec_{uuid.uuid4().hex[:8]}"
        resume1 = {"kind": "run.resume", "decision_id": d1, "decisions": [{"type": "respond", "tool_id": tool_id1, "response": "文件名叫 e2e.txt"}]}
        st5, _ = http("POST", f"/sessions/{SID}/runs/{run_id}/control", resume1)
        st5b, _ = http("POST", f"/sessions/{SID}/runs/{run_id}/control", resume1)
        check("respond 提交 + decision_id 幂等", st5 == 202 and st5b == 202, f"{st5}/{st5b}")
        ret1 = sse.wait(lambda i: i[1] == "tool.returned" and i[2]["payload"]["tool_id"] == tool_id1)
        check("SSE: ask_user 人工代答 responded", ret1 is not None and ret1[2]["payload"].get("responded") is True)

        # 3. write_file 审批
        awaiting2 = sse.wait(lambda i: i[1] == "tool.awaiting_approval" and i[2]["payload"]["tool_id"] != tool_id1)
        check("SSE: write_file 审批暂停", awaiting2 is not None and awaiting2[2]["payload"]["kind"] == "tool_approval"
              and awaiting2[2]["payload"]["name"] == "write_file",
              json.dumps(awaiting2[2]["payload"] if awaiting2 else {}, ensure_ascii=False)[:200])
        allowed = awaiting2[2]["payload"]["allowed_decisions"] if awaiting2 else []
        check("审批 allowed_decisions 无 respond", awaiting2 is not None and "respond" not in allowed and "approve" in allowed, str(allowed))
        tool_id2 = awaiting2[2]["payload"]["tool_id"] if awaiting2 else "?"
        # respond 用于非 ask_user 必须被 session 拒绝（400 族）
        st6, body6 = http("POST", f"/sessions/{SID}/runs/{run_id}/control",
                          {"kind": "run.resume", "decision_id": f"dec_{uuid.uuid4().hex[:8]}",
                           "decisions": [{"type": "respond", "tool_id": tool_id2, "response": "x"}]})
        check("respond 用于审批工具被拒", 400 <= st6 < 500, f"{st6} {body6}")
        st7, _ = http("POST", f"/sessions/{SID}/runs/{run_id}/control",
                      {"kind": "run.resume", "decision_id": f"dec_{uuid.uuid4().hex[:8]}",
                       "decisions": [{"type": "approve", "tool_id": tool_id2}]})
        check("approve 提交", st7 == 202, str(st7))

        # 3b. 结果审核：批准后工具执行，结果先经人审再回流（respond 替换）。
        review = sse.wait(lambda i: i[1] == "tool.awaiting_approval" and i[2]["payload"]["kind"] == "result_review")
        check("SSE: 结果审核暂停（带已执行结果）", review is not None
              and isinstance(review[2]["payload"].get("result"), str)
              and review[2]["payload"]["allowed_decisions"] == ["approve", "respond", "reject"],
              json.dumps(review[2]["payload"] if review else {}, ensure_ascii=False)[:200])
        st7b, _ = http("POST", f"/sessions/{SID}/runs/{run_id}/control",
                       {"kind": "run.resume", "decision_id": f"dec_{uuid.uuid4().hex[:8]}",
                        "decisions": [{"type": "respond", "tool_id": tool_id2, "response": "人工替换后的结果"}]})
        check("审核 respond 替换提交", st7b == 202, str(st7b))
        ret2 = sse.wait(lambda i: i[1] == "tool.returned" and i[2]["payload"]["tool_id"] == tool_id2)
        check("SSE: 裁决后 returned=替换文本（responded 标记）", ret2 is not None
              and ret2[2]["payload"].get("result") == "人工替换后的结果"
              and ret2[2]["payload"].get("responded") is True,
              json.dumps(ret2[2]["payload"] if ret2 else {}, ensure_ascii=False)[:160])

        # 4. 文本流与终态
        check("SSE: message.delta", sse.wait(lambda i: i[1] == "message.delta") is not None)
        done = sse.wait(lambda i: i[1] == "message.completed")
        check("SSE: message.completed", done is not None)
        terminal = sse.wait(lambda i: i[1] == "run.completed")
        check("SSE: run.completed(status=completed)", terminal is not None and terminal[2]["payload"]["status"] == "completed")
        term_seq = terminal[0] if terminal else -1

        st8, snap2 = http("GET", f"/sessions/{SID}")
        roles = [(m["role"], m["status"]) for m in snap2.get("messages", [])]
        check("终态 snapshot：activeRun 清零 + 无 pending + assistant completed",
              st8 == 200 and "active_run" not in snap2
              and not [p for p in snap2.get("pending_pauses", []) if p["status"] == "pending"]
              and ("assistant", "completed") in roles, f"{roles} {snap2.get('active_run')}")

        # 5. Last-Event-ID 续传：从中段续，只收后续事件
        mid = awaiting2[0] if awaiting2 else 0
        sse2 = SseReader(f"/sessions/{SID}/events", last_event_id=str(mid))
        tail = sse2.wait(lambda i: i[1] == "run.completed", timeout=10)
        check("SSE 续传：拿到终态且不重放水位前事件", tail is not None and tail[0] == term_seq
              and all(seq > mid for seq, _ in sse2.seen), f"seen={sse2.seen[:5]}")

        # 6. 终态后可开新 run
        st9, receipt3 = http("POST", f"/sessions/{SID}/messages", {"idempotency_key": f"idem_{uuid.uuid4().hex[:8]}", "content": "再来一轮"})
        check("终态后新 run 受理", st9 == 202 and receipt3.get("run_id") != run_id, f"{st9}")
        done2 = sse.wait(lambda i: i[1] == "run.completed" and i[2]["run_id"] == receipt3.get("run_id"), timeout=40)
        check("第二轮 run 终态", done2 is not None)

        kinds = {k for _, k in sse.seen}
        expected = {"session.created", "run.created", "tool.awaiting_approval", "tool.returned",
                    "message.delta", "message.completed", "run.completed"}
        check("事件面覆盖", expected <= kinds, f"missing={expected - kinds}")
    finally:
        session_proc.terminate()
        agent_proc.terminate()
        session_proc.wait(timeout=10)
        agent_proc.wait(timeout=10)
        print(f"  logs: {scratch}")

    if FAILURES:
        print(f"\nE2E FAIL ({len(FAILURES)}):")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print("\nE2E PASS — v2.1 跨栈全链绿")
    return 0


if __name__ == "__main__":
    sys.exit(main())
