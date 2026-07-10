#!/usr/bin/env python3
"""v2.1 跨栈 e2e 门禁：真 redis+mongo，agent(LocalFake HITL 脚本)→session→SSE 全链断言。

覆盖：POST messages 幂等/活跃 run 转 steer、session.created/run.created/message.user 合成、
ask_user respond、write_file 审批 approve、decision_id 幂等、snapshot 暂停点恢复、
Last-Event-ID 续传、seq=0 全量回放（web 刷新水合语义）、工作区文件面（snapshot.files +
files 端点直读）、终态收口后可开新 run。前置：redis:6379 + mongo:27017 + 两仓依赖已装。
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

from procutil import ensure_port_free, spawn, stop

ROOT = Path(__file__).resolve().parents[1]
SESSION_PORT = int(os.environ.get("E2E_SESSION_PORT", "3901"))
BASE = f"http://127.0.0.1:{SESSION_PORT}"
REDIS_URL = os.environ.get("E2E_REDIS_URL", "redis://127.0.0.1:6379/14")
MONGO_URL = os.environ.get("E2E_MONGO_URL", "mongodb://127.0.0.1:27017")
MONGO_DB = "kokoro_e2e_v21"
SID = f"ses_e2e_{uuid.uuid4().hex[:8]}"
# 文件面底座：local（默认，目录直读）| s3（ADR-009 归档档，经 minio 全链）。断言两档同一套。
WORKSPACE_BACKEND = os.environ.get("E2E_WORKSPACE_BACKEND", "local")
MINIO_URL = os.environ.get("E2E_MINIO_URL", "http://127.0.0.1:9100")
# 执行沙箱：local_shell（默认）| docker（ADR-009 执行隔离档，文件面语义不变）。
SANDBOX_BACKEND = os.environ.get("E2E_SANDBOX_BACKEND", "local_shell")
AUTH_SECRET = "e2e-secret"


def _b64url(data: bytes) -> str:
    import base64
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def sign_token(sub: str, secret: str = AUTH_SECRET) -> str:
    """gate 全程在鉴权强制模式下跑：HS256 手签（与 session/http/auth.ts 同规格）。"""
    import hashlib
    import hmac as hmac_mod
    head = _b64url(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    body = _b64url(json.dumps({"sub": sub}).encode())
    sig = _b64url(hmac_mod.new(secret.encode(), f"{head}.{body}".encode(), hashlib.sha256).digest())
    return f"{head}.{body}.{sig}"


AUTH_HEADER = {"authorization": f"Bearer {sign_token('e2e-user')}"}

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
        headers={"content-type": "application/json", **AUTH_HEADER, **(headers or {})},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def http_raw(path: str) -> tuple[int, bytes, str]:
    """非 JSON 端点（文件字节）：返回 (status, body, content-type)。"""
    try:
        req = urllib.request.Request(BASE + path, headers=AUTH_HEADER)
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, resp.read(), resp.headers.get("content-type", "")
    except urllib.error.HTTPError as e:
        return e.code, e.read(), e.headers.get("content-type", "")


class SseReader:
    """后台线程读 SSE，帧入队列；wait() 按谓词取帧。"""

    def __init__(self, path: str, last_event_id: str | None = None):
        self.q: queue.Queue[tuple[int, str, dict]] = queue.Queue()
        self.seen: list[tuple[int, str]] = []
        headers = dict(AUTH_HEADER) if last_event_id is None else {"last-event-id": last_event_id, **AUTH_HEADER}
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
    skill_dir = scratch / "skills" / "e2e-style"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: e2e-style\ndescription: e2e 渐进披露样例\n---\n\n正文 GATE-SKILL-BODY\n"
    )
    (scratch / "namespaces.json").write_text(json.dumps({
        "namespaces": {
            "team-e2e": {
                # local_shell/docker：write_file 真落盘（docker 档文件面同宿主），文件面断言同一套。
                "backend": SANDBOX_BACKEND,
                # wire 只传 names：prompt 定义住 agent 侧（prompts/<name>.md），profile 不再内联。
                "agents": {
                    "poet": {"description": "诗歌创作专家"},
                    "coder": {"description": "代码专家"},
                }
            }
        }
    }))
    subprocess.run(
        ["docker", "exec", "kokoro-e2e-mongo", "mongosh", "--quiet", "--eval",
         f'db.getSiblingDB("{MONGO_DB}").dropDatabase()'],
        check=False, capture_output=True,
    )

    session_env = {
        **os.environ,
        "KOKORO_SESSION_PORT": str(SESSION_PORT),
        "KOKORO_REDIS_URL": REDIS_URL,
        "KOKORO_MESSAGE_STORE_MONGO_URL": MONGO_URL,
        "KOKORO_MESSAGE_STORE_MONGO_DB": MONGO_DB,
        # write_file 同时配 审批+审核：批参数 → 执行 → 审结果（串联双暂停，实证缓存防双跑）。
        "KOKORO_REVIEW_TOOLS": "write_file",
        "KOKORO_NAMESPACE": "team-e2e",
        "KOKORO_NAMESPACES_FILE": str(scratch / "namespaces.json"),
        # 与 agent 同根：session files 端点按 {root}/{namespace:session_id} 直读。
        "KOKORO_WORKSPACE_ROOT": str(scratch / "workspace"),
        # 鉴权强制模式：gate 全部 26+ 断言在 auth-on 下跑（M2-P1 真栈证据）。
        "KOKORO_AUTH_JWT_SECRET": AUTH_SECRET,
    }
    if WORKSPACE_BACKEND == "s3":
        bucket = f"kokoro-e2e-{uuid.uuid4().hex[:8]}"
        # 复用 agent venv 的 boto3 预建桶：生产桶由部署预建，脚本对齐该前置。
        subprocess.run(
            ["uv", "run", "python", "-c",
             "import boto3, sys; from botocore.config import Config; "
             "boto3.client('s3', endpoint_url=sys.argv[1], region_name='us-east-1', "
             "aws_access_key_id='kokoro', aws_secret_access_key='kokoro-secret', "
             "config=Config(s3={'addressing_style':'path'}, connect_timeout=2, retries={'max_attempts':1})"
             ").create_bucket(Bucket=sys.argv[2])",
             MINIO_URL, bucket],
            cwd=ROOT / "kokoro-agent", check=True, capture_output=True,
        )
        # deliveries 冻结件同桶（key 前缀 deliveries/… 与归档 {ns:sid}/… 不同 keyspace）。
        (scratch / "workspace.yaml").write_text(
            f"workspace:\n  type: s3\n  endpoint: {MINIO_URL}\n  bucket: {bucket}\n"
            f"deliveries:\n  type: s3\n  endpoint: {MINIO_URL}\n  bucket: {bucket}\n"
        )
        storage_env = {
            "KOKORO_WORKSPACE_CONFIG": str(scratch / "workspace.yaml"),
            "KOKORO_WORKSPACE_S3_ACCESS_KEY": "kokoro",
            "KOKORO_WORKSPACE_S3_SECRET_KEY": "kokoro-secret",
        }
    else:
        # local 档也走显式 storage yaml：workspace 节与 env 根同值（行为不变），deliveries 节启用交付链。
        (scratch / "workspace.yaml").write_text(
            f"workspace:\n  type: local\n  root: {scratch / 'workspace'}\n"
            f"deliveries:\n  type: local\n  root: {scratch / 'deliveries'}\n"
        )
        storage_env = {"KOKORO_WORKSPACE_CONFIG": str(scratch / "workspace.yaml")}
    session_env.update(storage_env)
    agent_env = {
        **os.environ,
        "KOKORO_REDIS_URL": REDIS_URL,
        "KOKORO_LOCAL_FAKE_MODEL": "1",
        "KOKORO_LOCAL_FAKE_SCRIPT": "hitl",
        # ledger/checkpoint 走 mongo（唯一真后端）；与 session 同 db 隔离，run 后随 dropDatabase 清扫。
        "KOKORO_MONGO_URL": MONGO_URL,
        "KOKORO_MONGO_DB": MONGO_DB,
        "KOKORO_AGENT_LOCAL_SHELL_ROOT": str(scratch / "workspace"),
        "KOKORO_SKILLS_DIR": str(scratch / "skills"),
        "KOKORO_DOCKER_IMAGE": os.environ.get("E2E_DOCKER_IMAGE", "busybox"),
    }
    agent_env.update(storage_env)  # 双侧读同一 storage yaml：workspace 归档 + deliveries 冻结件
    ensure_port_free(SESSION_PORT)
    session_proc = spawn(["npm", "run", "start"], cwd=ROOT / "kokoro-session", env=session_env,
                         log=scratch / "session.log")
    agent_proc = spawn(["uv", "run", "kokoro-agent-worker"], cwd=ROOT / "kokoro-agent", env=agent_env,
                       log=scratch / "agent.log")
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
        mu1 = sse.wait(lambda i: i[1] == "message.user")
        check("SSE: message.user 合成（event_id=user_message_id，事件史即线程真源）",
              mu1 is not None and mu1[2]["payload"]["content"] == "帮我写个文件然后总结"
              and mu1[2]["event_id"] == receipt.get("user_message_id"),
              json.dumps(mu1[2] if mu1 else {}, ensure_ascii=False)[:200])

        # 2. ask_user 暂停
        awaiting1 = sse.wait(lambda i: i[1] == "tool.awaiting_approval")
        check("SSE: ask_user awaiting", awaiting1 is not None and awaiting1[2]["payload"]["kind"] == "ask_user_question",
              json.dumps(awaiting1[2]["payload"] if awaiting1 else {}, ensure_ascii=False)[:200])
        ks = f"idem_{uuid.uuid4().hex[:8]}"
        st3, body3 = http("POST", f"/sessions/{SID}/messages", {"idempotency_key": ks, "content": "顺便注意编码"})
        check("活跃 run 期间新消息 → 202 转 steer（归属活跃 run）",
              st3 == 202 and body3.get("run_id") == run_id
              and body3.get("assistant_message_id") == receipt.get("assistant_message_id"),
              f"{st3} {body3}")
        st3b, body3b = http("POST", f"/sessions/{SID}/messages", {"idempotency_key": ks, "content": "顺便注意编码"})
        check("steer 幂等：同 key 重发同 receipt", st3b == 202 and body3b == body3, f"{st3b} {body3b}")
        mu2 = sse.wait(lambda i: i[1] == "message.user" and i[2]["payload"]["content"] == "顺便注意编码")
        check("SSE: steer 消息也进事件史（message.user）",
              mu2 is not None and mu2[2]["event_id"] == body3.get("user_message_id"),
              json.dumps(mu2[2] if mu2 else {}, ensure_ascii=False)[:200])

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

        # 4b. 工作区文件面：write_file 已真落盘（审核 respond 只替换回流文本，不撤销执行）。
        files = snap2.get("files", [])
        plan = next((f for f in files if f["path"] == "plan.md"), None)
        check("snapshot.files 含 plan.md（真目录 walk）",
              plan is not None and plan["mime"] == "text/markdown" and plan["bytes"] > 0, str(files))
        stf, body_f, mime_f = http_raw(f"/sessions/{SID}/files/plan.md")
        check("files 端点直读字节", stf == 200 and body_f.decode() == "# 计划\n本地预览"
              and mime_f == "text/markdown", f"{stf} {mime_f} {body_f[:40]!r}")
        stf2, _, _ = http_raw(f"/sessions/{SID}/files/..%2F..%2Fetc%2Fpasswd")
        check("files 端点路径穿越 → 404", stf2 == 404, str(stf2))

        # 5. Last-Event-ID 续传：从中段续，只收后续事件
        mid = awaiting2[0] if awaiting2 else 0
        sse2 = SseReader(f"/sessions/{SID}/events", last_event_id=str(mid))
        tail = sse2.wait(lambda i: i[1] == "run.completed", timeout=10)
        check("SSE 续传：拿到终态且不重放水位前事件", tail is not None and tail[0] == term_seq
              and all(seq > mid for seq, _ in sse2.seen), f"seen={sse2.seen[:5]}")

        # 5b. seq=0 全量回放（web 刷新水合语义）：线程可完全由事件史重建。
        sse0 = SseReader(f"/sessions/{SID}/events", last_event_id="0")
        check("seq=0 回放：拿到终态", sse0.wait(lambda i: i[1] == "run.completed", timeout=10) is not None)
        replay_kinds = [k for _, k in sse0.seen]
        check("seq=0 回放：message.user ×2（user+steer）+ 全事件面",
              replay_kinds.count("message.user") == 2
              and {"session.created", "run.created", "tool.awaiting_approval", "tool.returned",
                   "message.delta", "message.completed", "run.completed"} <= set(replay_kinds),
              str(replay_kinds[:12]))

        # 6. 终态后可开新 run
        st9, receipt3 = http("POST", f"/sessions/{SID}/messages", {"idempotency_key": f"idem_{uuid.uuid4().hex[:8]}", "content": "再来一轮"})
        check("终态后新 run 受理", st9 == 202 and receipt3.get("run_id") != run_id, f"{st9}")
        # 6b. 成果交付（E2E-31，块D）：第二轮脚本 deliver plan.md → 事件 → 读模型 → 下载 → 冻结证明。
        # SseReader.wait 是消费型游标：delivery.created 先于 run.completed，必须先等它再等终态。
        run2 = receipt3.get("run_id", "")
        dc = sse.wait(lambda i: i[1] == "delivery.created" and i[2]["run_id"] == run2, timeout=40)
        done2 = sse.wait(lambda i: i[1] == "run.completed" and i[2]["run_id"] == run2, timeout=40)
        check("第二轮 run 终态", done2 is not None)
        check("E2E-31 SSE: delivery.created（tool.returned 追发）", dc is not None
              and dc[2]["payload"]["path"] == "/plan.md"
              and dc[2]["payload"]["title"] == "执行计划"
              and dc[2]["payload"]["size"] > 0,
              json.dumps(dc[2]["payload"] if dc else {}, ensure_ascii=False)[:200])
        dhash = dc[2]["payload"]["content_hash"] if dc else "?"
        st22, snap22 = http("GET", f"/sessions/{SID}")
        entry = next((d for d in snap22.get("deliveries", []) if d["content_hash"] == dhash), None)
        check("E2E-31 snapshot.deliveries 投影", st22 == 200 and entry is not None
              and entry["run_id"] == run2 and entry["mime"] == "text/markdown",
              str(snap22.get("deliveries"))[:200])
        st23, body23, mime23 = http_raw(f"/sessions/{SID}/deliveries/{dhash}")
        check("E2E-31 下载冻结副本（mime+字节）", st23 == 200 and body23.decode() == "# 计划\n本地预览"
              and mime23 == "text/markdown", f"{st23} {mime23} {body23[:40]!r}")
        # 冻结的跨栈证明：改掉工作区源文件后，下载字节不变（内容寻址，成果与工作区解耦）。
        src_plan = scratch / "workspace" / f"e2e-user:{SID}" / "plan.md"
        if src_plan.is_file():
            src_plan.write_text("源文件已被改写")
            st24, body24, _ = http_raw(f"/sessions/{SID}/deliveries/{dhash}")
            check("E2E-31 改源文件后下载不变（交付即冻结）",
                  st24 == 200 and body24.decode() == "# 计划\n本地预览", f"{st24} {body24[:40]!r}")
        stbad, _, _ = http_raw(f"/sessions/{SID}/deliveries/{'0' * 64}")
        check("E2E-31 未知 hash → 404", stbad == 404, str(stbad))

        # 7. 具名 agent：agent=poet 作主，wire 只传 names（无内联 prompt/定义/凭据）。
        sid2 = f"ses_agent_{uuid.uuid4().hex[:8]}"
        st10, receipt4 = http("POST", f"/sessions/{sid2}/messages",
                              {"idempotency_key": f"idem_{uuid.uuid4().hex[:8]}", "content": "写首诗", "agent": "poet"})
        check("agent=poet 受理", st10 == 202, f"{st10} {receipt4}")
        st11, body11 = http("POST", f"/sessions/ses_ghost_{uuid.uuid4().hex[:6]}/messages",
                            {"idempotency_key": f"idem_{uuid.uuid4().hex[:8]}", "content": "x", "agent": "ghost"})
        check("agent 未知（新会话）→ 400", st11 == 400 and body11.get("error") == "unknown_agent", f"{st11} {body11}")
        st11b, body11b = http("POST", f"/sessions/{sid2}/messages",
                              {"idempotency_key": f"idem_{uuid.uuid4().hex[:8]}", "content": "x", "agent": "coder"})
        check("同会话改 agent → 400 能力锁", st11b == 400 and body11b.get("error") == "session_capabilities_locked",
              f"{st11b} {body11b}")
        raw = subprocess.run(["redis-cli", "-u", REDIS_URL, "XRANGE", "kokoro:runs:requests", "-", "+"],
                             capture_output=True, text=True, check=True).stdout
        wire_ok = False
        for line in raw.splitlines():
            line = line.strip()
            if not line.startswith("{"):
                continue
            req = json.loads(line)
            if req.get("run_id") == receipt4.get("run_id"):
                rt = req["runtime"]
                wire_ok = (rt.get("agent") == "poet"
                           and rt["subagents"] == ["coder"]
                           and "system_prompt" not in rt  # 契约负向：wire 恒无内联 prompt
                           and req["context"]["namespace"] == "e2e-user")  # namespace=token sub（块1 语义）
        check("wire: agent 名 + names 下属 + 无内联 prompt + namespace=sub", wire_ok)
        sse3 = SseReader(f"/sessions/{sid2}/events")
        pause3 = sse3.wait(lambda i: i[1] == "tool.awaiting_approval")
        check("agent run 启动并到达首个暂停", pause3 is not None)
        st12, _ = http("POST", f"/sessions/{sid2}/runs/{receipt4['run_id']}/control",
                       {"kind": "run.cancel", "decision_id": f"dec_{uuid.uuid4().hex[:8]}"})
        cancelled = sse3.wait(lambda i: i[1] == "run.completed")
        check("cancel 收束 → run.completed(status=cancelled)", st12 == 202 and cancelled is not None
              and cancelled[2]["payload"]["status"] == "cancelled",
              f"{st12} {cancelled[2]['payload'] if cancelled else {}}")

        kinds = {k for _, k in sse.seen}
        expected = {"session.created", "run.created", "message.user", "tool.awaiting_approval",
                    "tool.returned", "message.delta", "message.completed", "run.completed"}
        check("事件面覆盖", expected <= kinds, f"missing={expected - kinds}")

        # 8. 会话软删除（technical/16）——E2E-27 终态会话 / E2E-28 暂停中会话。
        st13, del_body = http("DELETE", f"/sessions/{SID}")
        check("E2E-27 DELETE → 202 {status:deleted}", st13 == 202 and del_body.get("status") == "deleted",
              f"{st13} {del_body}")
        st14, body14 = http("GET", f"/sessions/{SID}")
        check("E2E-27 deleted snapshot → 410 session_deleted",
              st14 == 410 and body14.get("error") == "session_deleted", f"{st14} {body14}")
        st15, body15 = http("POST", f"/sessions/{SID}/messages",
                            {"idempotency_key": f"idem_{uuid.uuid4().hex[:8]}", "content": "x"})
        check("E2E-27 deleted 新消息 → 410", st15 == 410 and body15.get("error") == "session_deleted",
              f"{st15} {body15}")
        st16, del2 = http("DELETE", f"/sessions/{SID}")
        check("E2E-27 重复 DELETE 幂等 202", st16 == 202 and del2.get("status") == "deleted", f"{st16}")
        if WORKSPACE_BACKEND == "local" and SANDBOX_BACKEND == "local_shell":
            # 软删不动产物：agent 侧零变化的显式断言（文件仍在磁盘）。
            plan = scratch / "workspace" / f"e2e-user:{SID}" / "plan.md"
            check("E2E-27 软删保留工作区文件", plan.is_file(), str(plan))

        sid3 = f"ses_del_{uuid.uuid4().hex[:8]}"
        st17, receipt5 = http("POST", f"/sessions/{sid3}/messages",
                              {"idempotency_key": f"idem_{uuid.uuid4().hex[:8]}", "content": "暂停中删除"})
        sse4 = SseReader(f"/sessions/{sid3}/events")
        pause4 = sse4.wait(lambda i: i[1] == "tool.awaiting_approval")
        check("E2E-28 到达暂停", st17 == 202 and pause4 is not None)
        st18, del3 = http("DELETE", f"/sessions/{sid3}")
        cancelled2 = sse4.wait(lambda i: i[1] == "run.completed", timeout=40)
        check("E2E-28 暂停中删除 → cancel 收敛 + 202",
              st18 == 202 and del3.get("status") == "deleted" and cancelled2 is not None
              and cancelled2[2]["payload"]["status"] == "cancelled",
              f"{st18} {cancelled2[2]['payload'] if cancelled2 else {}}")
        st19, body19 = http("GET", f"/sessions/{sid3}")
        check("E2E-28 删除后 snapshot → 410", st19 == 410 and body19.get("error") == "session_deleted",
              f"{st19}")

        # 9a. 鉴权负例（E2E-30）：无 token 401；他人 token 探测他人会话 403。
        bare_req = urllib.request.Request(f"{BASE}/sessions/{SID}", method="GET")
        try:
            with urllib.request.urlopen(bare_req, timeout=10) as resp:
                st_bare = resp.status
        except urllib.error.HTTPError as e:
            st_bare = e.code
        check("E2E-30 无 token → 401", st_bare == 401, str(st_bare))
        st_bob, body_bob = http("GET", f"/sessions/{SID}",
                                headers={"authorization": f"Bearer {sign_token('bob')}"})
        check("E2E-30 他人 token → 403 session_forbidden",
              st_bob == 403 and body_bob.get("error") == "session_forbidden", f"{st_bob} {body_bob}")

        # 9. Skills（E2E-29，渐进披露）：挂载=逻辑授权——纯正文技能（无附件）永不物化；
        # 正文走 skill 工具直返（单测覆盖），有附件的包才由装配期 reconcile 按账本物化（块C）。
        if WORKSPACE_BACKEND == "local":
            skills_dir = scratch / "workspace" / f"e2e-user:{SID}" / ".skills"
            check("E2E-29 装配期零物化（/.skills 不存在）", not skills_dir.exists(), str(skills_dir))
            # 点前缀=能力供给不进用户文件面：snapshot.files 不得列出 skills。
            st21, snap21 = http("GET", f"/sessions/{SID}")
            listed = [f["path"] for f in snap21.get("files", [])] if st21 == 200 else []
            check("E2E-29 skills 不进 snapshot.files", all(".skills" not in p for p in listed),
                  str(listed[:5]))
    finally:
        stop(session_proc)
        stop(agent_proc)
        if SANDBOX_BACKEND == "docker":
            # run 容器有 TTL 自清兜底；gate 收尾即时清理不留半小时残留。
            cids = subprocess.run(
                ["docker", "ps", "-q", "--filter", "label=kokoro-run"],
                capture_output=True, text=True, check=False,
            ).stdout.split()
            if cids:
                subprocess.run(["docker", "rm", "-f", *cids], capture_output=True, check=False)
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
