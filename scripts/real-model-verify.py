#!/usr/bin/env python3
"""真实模型盲区验证：glm-5（openai-compat + reasoning）跨栈压实 thinking 通道与 subagent 事件。

场景 A：明令经 task 工具委派 researcher 子代理 → 断言 subagent.started/finished（+文本流）。
场景 B：普通提问 → 断言 thinking.delta ≥ 1 且 message.completed 非空。
场景 C：web_search 真调用（searxng 可达才跑，否则 SKIP）→ 断言 tool.invoked/returned。
场景 D：skills 库按名挂载（启动即锁）→ 断言模型遵循 skill 输出标记。
场景 E：backend=local_shell 下 execute 审批 → 真 shell 输出回流。
全程 profile.backend=local_shell（沙箱=真文件系统，root 圈定 scratch/workspace）。
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
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

from procutil import ensure_port_free, spawn, stop

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
    skill_dir = scratch / "skills" / "kokoro-style"
    skill_dir.mkdir(parents=True)  # 库形态：KOKORO_SKILLS_DIR/<name>/SKILL.md，配置只引名称
    skill_md = (
        "---\nname: kokoro-style\ndescription: 自我介绍风格约定\n---\n\n"
        "# Kokoro 自我介绍风格\n\n当用户要求你自我介绍时：\n"
        "1. 用一句话介绍自己。\n2. 最后单独一行输出字面量：via-skill:kokoro-style-v1\n"
    )
    (skill_dir / "SKILL.md").write_text(skill_md)
    (scratch / "namespaces.json").write_text(json.dumps({
        "namespaces": {
            "team-rmv": {
                "model_policy": {"default": {"provider": "openai", "name": "glm-5"}},
                "backend": "local_shell",
                "skills": ["kokoro-style"],
                # 委派验证走产品正道：researcher 是 namespace 预设（内建目录按原则为空）。
                "agents": {
                    "researcher": {
                        "description": "研究并回答技术问题，返回简洁结论。",
                        "system_prompt": "你是研究型子智能体：直接回答问题，简洁中文。",
                    }
                },
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
        # 工作区同根约定：session 直读 agent 的 local_shell 目录。
        "KOKORO_WORKSPACE_ROOT": str(scratch / "workspace"),
    }
    searxng_url = os.environ.get("RMV_SEARXNG_URL", "http://127.0.0.1:8888")
    try:
        with urllib.request.urlopen(f"{searxng_url}/search?q=ping&format=json", timeout=5) as r:
            searxng_ok = r.status == 200
    except Exception:
        searxng_ok = False
    search_env = (
        {"KOKORO_WEB_SEARCH_PROVIDER": "searxng", "KOKORO_WEB_SEARCH_URL": searxng_url}
        if searxng_ok
        else {}
    )
    agent_env = {
        **{k: v for k, v in os.environ.items() if k != "KOKORO_DISABLE_STREAMING"},
        **search_env,
        "OPENAI_BASE_URL": creds["OPENAI_BASE_URL"],
        "OPENAI_API_KEY": creds["OPENAI_API_KEY"],
        # thinking 通道验证需要流式 + reasoning 抽取包装（ChatDeepSeek）。
        "KOKORO_OPENAI_REASONING": "1",
        "KOKORO_STREAM_BACKEND": "redis",
        "KOKORO_REDIS_URL": REDIS_URL,
        "KOKORO_LEDGER_BACKEND": "sqlite",
        "KOKORO_LEDGER_DB": str(scratch / "ledger.db"),
        "KOKORO_CHECKPOINT_BACKEND": "sqlite",
        "KOKORO_CHECKPOINT_DB": str(scratch / "checkpoints.db"),
        "KOKORO_AGENT_LOCAL_SHELL_ROOT": str(scratch / "workspace"),
        "KOKORO_SKILLS_DIR": str(scratch / "skills"),
    }
    (scratch / "workspace").mkdir()
    ensure_port_free(SESSION_PORT)
    session_proc = spawn(["npm", "run", "start"], cwd=ROOT / "kokoro-session", env=session_env,
                         log=scratch / "session.log")
    agent_proc = spawn(["uv", "run", "kokoro-agent-worker"], cwd=ROOT / "kokoro-agent", env=agent_env,
                       log=scratch / "agent.log")
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
            "content": "请务必使用 task 工具把任务委派给 researcher 子代理（不要自己直接回答）："
                       "让它用 web_search 工具搜索\"二分查找 时间复杂度\"并给出一句话结论。"
                       "子代理返回后你用一句话总结。",
        })
        check("A: POST messages → 202", st == 202, f"{st} {receipt}")
        events_a = collect_run(sse_a)
        kinds_a = [k for k, _ in events_a]
        started = [p for k, p in events_a if k == "subagent.started"]
        finished = [p for k, p in events_a if k == "subagent.finished"]
        check("A: subagent.started 出现", bool(started), f"kinds={kinds_a}")
        check("A: subagent.finished 出现且未失败",
              bool(finished) and not finished[-1].get("failed"), str(finished[-1:] or kinds_a))
        check("A: subagent 归属 namespace 预设 researcher",
              bool(started) and started[0].get("name") == "researcher"
              and started[0].get("source") == "runtime-custom", str(started[:1]))
        subtext = sum(1 for k in kinds_a if k.startswith("subagent.text"))
        check("A: subagent 文本流出现", subtext >= 1, f"kinds={kinds_a}")
        inner_invoked = [p for k, p in events_a if k == "subagent.tool.invoked"]
        inner_returned = [p for k, p in events_a if k == "subagent.tool.returned"]
        check("A: 子代理内工具事件上 wire（invoked+returned 成对）",
              bool(inner_invoked) and bool(inner_returned), f"kinds={kinds_a}")
        check("A: 子代理内工具事件带 subagent_id 归属",
              bool(inner_invoked) and bool(inner_invoked[0].get("subagent_id"))
              and inner_invoked[0].get("subagent_id") == (started[0].get("subagent_id") if started else None),
              str(inner_invoked[:1]))
        check("A: run.completed 收尾", kinds_a[-1:] == ["run.completed"], f"kinds={kinds_a}")

        # 场景 C：web_search 真调用（searxng 自托管，无 key）。
        if not searxng_ok:
            print("  [SKIP] C: searxng 不可达，web_search 场景跳过")
        else:
            sid_c = f"ses_rmv_{uuid.uuid4().hex[:8]}"
            sse_c = SseReader(f"/sessions/{sid_c}/events")
            st, receipt = http("POST", f"/sessions/{sid_c}/messages", {
                "idempotency_key": f"idem_{uuid.uuid4().hex[:8]}",
                "content": "用 web_search 搜索 langchain deepagents，用一句话告诉我它是什么。",
            })
            check("C: POST messages → 202", st == 202, f"{st} {receipt}")
            events_c = collect_run(sse_c)
            kinds_c = [k for k, _ in events_c]
            invoked = [p for k, p in events_c if k == "tool.invoked" and p.get("name") == "web_search"]
            returned = [p for k, p in events_c if k == "tool.returned" and p.get("name") == "web_search"]
            check("C: web_search 被调用", bool(invoked), f"kinds={kinds_c}")
            check("C: web_search 结果回流且非错误",
                  bool(returned) and returned[-1].get("is_error") is False, str(returned[-1:] or kinds_c))
            check("C: run.completed 收尾", kinds_c[-1:] == ["run.completed"], f"kinds={kinds_c}")

        # 场景 D：skill 挂载生效（全文注入 system prompt → 模型遵循标记约定）。
        sid_d = f"ses_rmv_{uuid.uuid4().hex[:8]}"
        sse_d = SseReader(f"/sessions/{sid_d}/events")
        st, receipt = http("POST", f"/sessions/{sid_d}/messages", {
            "idempotency_key": f"idem_{uuid.uuid4().hex[:8]}",
            "content": "请自我介绍一下。",
        })
        check("D: POST messages → 202", st == 202, f"{st} {receipt}")
        events_d = collect_run(sse_d)
        kinds_d = [k for k, _ in events_d]
        finals = [p.get("content", "") for k, p in events_d if k == "message.completed"]
        check("D: 模型遵循 skill 标记", any("via-skill:kokoro-style-v1" in str(c) for c in finals),
              (finals[-1][:200] if finals else f"kinds={kinds_d}"))
        check("D: run.completed 收尾", kinds_d[-1:] == ["run.completed"], f"kinds={kinds_d}")

        # 场景 E：execute 审批 → 真 shell 输出回流（local_shell backend）。
        sid_e = f"ses_rmv_{uuid.uuid4().hex[:8]}"
        sse_e = SseReader(f"/sessions/{sid_e}/events")
        st, receipt = http("POST", f"/sessions/{sid_e}/messages", {
            "idempotency_key": f"idem_{uuid.uuid4().hex[:8]}",
            "content": "请用 execute 工具运行这条命令并把输出原样告诉我：echo kokoro-exec-ok",
        })
        check("E: POST messages → 202", st == 202, f"{st} {receipt}")
        run_e = receipt.get("run_id", "")
        awaiting = None
        deadline = time.time() + 210
        while time.time() < deadline and awaiting is None:
            try:
                _, kind, event = sse_e.q.get(timeout=max(0.1, deadline - time.time()))
            except queue.Empty:
                break
            if kind == "tool.awaiting_approval" and event.get("payload", {}).get("name") == "execute":
                awaiting = event["payload"]
        check("E: execute 审批暂停出现", awaiting is not None, "no awaiting")
        if awaiting is not None:
            http("POST", f"/sessions/{sid_e}/runs/{run_e}/control", {
                "kind": "run.resume", "decision_id": f"dec_{uuid.uuid4().hex[:8]}",
                "decisions": [{"type": "approve", "tool_id": awaiting["tool_id"]}]})
            events_e = collect_run(sse_e)
            kinds_e = [k for k, _ in events_e]
            returned = [p for k, p in events_e if k == "tool.returned" and p.get("name") == "execute"]
            check("E: 真 shell 输出回流", bool(returned) and "kokoro-exec-ok" in str(returned[-1].get("result")),
                  str(returned[-1:] or kinds_e)[:200])
            check("E: run.completed 收尾", kinds_e[-1:] == ["run.completed"], f"kinds={kinds_e}")

        # 场景 F：运行中插话（steering）——首个模型轮消费工具期间 POST 第二条消息，
        # 产出必须反映插话要求（下一模型轮注入实证）。
        sid_f = f"ses_rmv_{uuid.uuid4().hex[:8]}"
        sse_f = SseReader(f"/sessions/{sid_f}/events")
        st, receipt_f = http("POST", f"/sessions/{sid_f}/messages", {
            "idempotency_key": f"idem_{uuid.uuid4().hex[:8]}",
            "content": "请用 web_search 搜索\"二分查找\"，然后用一句话总结它是什么。",
        })
        check("F: POST messages → 202", st == 202, f"{st} {receipt_f}")
        run_f = receipt_f.get("run_id", "")
        # 受理即插话：首个模型轮尚在进行（真模型秒级延迟），信箱必然赶上后续任一模型轮；
        # 等 tool.invoked 再发会与末轮开跑竞速（时序脆弱，已实测偶发错过）。
        st_s, steer_receipt = http("POST", f"/sessions/{sid_f}/messages", {
            "idempotency_key": f"idem_{uuid.uuid4().hex[:8]}",
            "content": "补充要求：最终总结那句话必须以「转向确认」四个字开头。",
        })
        check("F: 运行中插话 → 202 归属同 run",
              st_s == 202 and steer_receipt.get("run_id") == run_f, f"{st_s} {steer_receipt}")
        events_f = collect_run(sse_f)
        kinds_f = [k for k, _ in events_f]
        finals_f = [p.get("content", "") for k, p in events_f if k == "message.completed"]
        check("F: 产出反映插话（下一模型轮注入生效）",
              any("转向确认" in str(c) for c in finals_f),
              (str(finals_f[-1])[:200] if finals_f else f"kinds={kinds_f}"))
        check("F: run.completed 收尾", kinds_f[-1:] == ["run.completed"], f"kinds={kinds_f}")

        # 场景 G：工作区文件面——真模型 write_file 落盘 → snapshot 清单 → files 端点直读。
        sid_g = f"ses_rmv_{uuid.uuid4().hex[:8]}"
        sse_g = SseReader(f"/sessions/{sid_g}/events")
        st, receipt_g = http("POST", f"/sessions/{sid_g}/messages", {
            "idempotency_key": f"idem_{uuid.uuid4().hex[:8]}",
            "content": "请用 write_file 工具把这句话写入 /note.md 文件：Kokoro 产物面已上线。写完告诉我文件名。",
        })
        check("G: POST messages → 202", st == 202, f"{st} {receipt_g}")
        run_g = receipt_g.get("run_id", "")
        # write_file 属默认审批集：等 awaiting → approve → 再收流。
        awaiting_g = None
        deadline = time.time() + 210
        while time.time() < deadline and awaiting_g is None:
            try:
                _, kind, event = sse_g.q.get(timeout=max(0.1, deadline - time.time()))
            except queue.Empty:
                break
            if kind == "tool.awaiting_approval" and event.get("payload", {}).get("name") == "write_file":
                awaiting_g = event["payload"]
        check("G: write_file 审批暂停出现", awaiting_g is not None, "no awaiting")
        if awaiting_g is not None:
            st_c, body_c = http("POST", f"/sessions/{sid_g}/runs/{run_g}/control", {
                "kind": "run.resume", "decision_id": f"dec_{uuid.uuid4().hex[:8]}",
                "decisions": [{"type": "approve", "tool_id": awaiting_g["tool_id"]}]})
            check("G: approve → 202", st_c == 202, f"{st_c} {body_c}")
        events_g = collect_run(sse_g)
        kinds_g = [k for k, _ in events_g]
        check("G: run.completed 收尾", kinds_g[-1:] == ["run.completed"], f"kinds={kinds_g}")
        # 工作区直读：snapshot 清单含 note.md，files 端点回读字节含原文（零产物机制）。
        st, snap_g = http("GET", f"/sessions/{sid_g}")
        gfiles = {f["path"]: f for f in snap_g.get("files", [])}
        check("G: snapshot.files 含 note.md", st == 200 and "note.md" in gfiles, str(list(gfiles)))
        try:
            req = urllib.request.Request(f"{BASE}/sessions/{sid_g}/files/note.md")
            with urllib.request.urlopen(req, timeout=10) as resp:
                body = resp.read()
                check("G: files 端点回读（MIME+字节含原文）",
                      resp.status == 200 and resp.headers["content-type"] == "text/markdown"
                      and "产物面已上线" in body.decode("utf-8"),
                      f"{resp.status} {resp.headers.get('content-type')} {body[:60]!r}")
        except urllib.error.HTTPError as e:
            check("G: files 端点回读（MIME+字节含原文）", False, f"HTTP {e.code}")

        print(f"  logs: {scratch}")
        if FAILURES:
            print(f"\nREAL-MODEL VERIFY FAIL — {len(FAILURES)} 项：")
            for f in FAILURES:
                print(f"  - {f}")
            return 1
        print("\nREAL-MODEL VERIFY PASS — thinking/subagent/web_search/skills/execute/steering/artifact 真栈全绿")
        return 0
    finally:
        stop(session_proc)
        stop(agent_proc)


if __name__ == "__main__":
    sys.exit(main())
