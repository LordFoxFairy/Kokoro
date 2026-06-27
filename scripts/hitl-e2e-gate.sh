#!/usr/bin/env bash
# HITL ① 真·跨进程 e2e 门禁：真实 redis + agent worker + session 三进程联调，验证「同帧多工具
# HITL」反向通道端到端——门控工具暂停 → SSE 浮现 awaiting → resume/cancel 经 session 控制端点回流
# 到 agent worker。MemoryStream 单测覆盖不到的整合面（如真 redis 游标格式）只有这里能抓。
#
# 自包含：起一个一次性 redis(docker) + worker + session，跑完即拆。
# 前置：docker；agent deps(uv sync 过)；session deps(bun install 过)。
#   run:  bash scripts/hitl-e2e-gate.sh
set -uo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REDIS_PORT="${HITL_REDIS_PORT:-6399}"
SESSION_PORT="${HITL_SESSION_PORT:-3011}"
REDIS_URL="redis://127.0.0.1:$REDIS_PORT/14"
SESSION_PID=""; WORKER_PID=""

cleanup() {
  # 杀子壳 PID 不够：bun/uv 真正的 server/worker 子进程会幸存 → 按端口/进程名兜底杀，绝不留孤儿。
  [ -n "$SESSION_PID" ] && kill "$SESSION_PID" 2>/dev/null
  [ -n "$WORKER_PID" ] && kill "$WORKER_PID" 2>/dev/null
  lsof -ti ":$SESSION_PORT" 2>/dev/null | xargs kill 2>/dev/null
  pkill -f kokoro-agent-worker 2>/dev/null
  pkill -f "src/main.ts" 2>/dev/null
  docker rm -f kokoro-hitl-redis >/dev/null 2>&1
  rm -f /tmp/hitl-e2e-sse.txt
}
trap cleanup EXIT

echo "[setup] redis (docker, host :$REDIS_PORT)"
docker rm -f kokoro-hitl-redis >/dev/null 2>&1
docker run -d --name kokoro-hitl-redis -p "$REDIS_PORT:6379" redis:7 >/dev/null
for _ in $(seq 1 20); do docker exec kokoro-hitl-redis redis-cli ping 2>/dev/null | grep -q PONG && break; sleep 0.5; done

echo "[setup] session (:$SESSION_PORT) + worker (LocalFake, gate write_todos, memory backends)"
( cd "$REPO_ROOT/kokoro-session" && KOKORO_STREAM_BACKEND=redis KOKORO_REDIS_URL="$REDIS_URL" \
    KOKORO_SESSION_PORT="$SESSION_PORT" bun run src/main.ts ) >/tmp/hitl-e2e-session.log 2>&1 &
SESSION_PID=$!
# memory backends → 单 worker 内完成 注册/暂停/resume（无需跨 pod 共享存储）。
( cd "$REPO_ROOT/kokoro-agent" && KOKORO_STREAM_BACKEND=redis KOKORO_REDIS_URL="$REDIS_URL" \
    KOKORO_LOCAL_FAKE_MODEL=1 KOKORO_REQUIRES_APPROVAL_TOOLS=write_todos \
    KOKORO_CHECKPOINT_BACKEND=memory KOKORO_RUN_STATE_BACKEND=memory \
    uv run --no-sync kokoro-agent-worker ) >/tmp/hitl-e2e-worker.log 2>&1 &
WORKER_PID=$!

for _ in $(seq 1 40); do
  curl -s -o /dev/null --max-time 1 -X POST "http://127.0.0.1:$SESSION_PORT/sessions/probe/runs?input=x" && break
  sleep 0.5
done
sleep 3

HITL_BASE="http://127.0.0.1:$SESSION_PORT" python3 - <<'PYEOF'
import json, os, subprocess, sys, time, urllib.request
BASE = os.environ["HITL_BASE"]; SID = "hitl_" + str(int(time.time())); SSE = "/tmp/hitl-e2e-sse.txt"
DB = ["docker", "exec", "kokoro-hitl-redis", "redis-cli", "-n", "14"]

def post(path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    hdr = {"content-type": "application/json"} if body is not None else {}
    with urllib.request.urlopen(urllib.request.Request(BASE + path, data=data, method="POST", headers=hdr), timeout=10) as r:
        return r.status, json.loads(r.read().decode() or "{}")

def events():
    out, cur = [], None
    try:
        for line in open(SSE):
            line = line.rstrip("\n")
            if line.startswith("event:"): cur = line[6:].strip()
            elif line.startswith("data:"):
                try: out.append((json.loads(line[5:].strip()).get("event") or cur, json.loads(line[5:].strip())))
                except Exception: pass
    except FileNotFoundError: pass
    return out

def wait_for(pred, timeout=15):
    end = time.time() + timeout
    while time.time() < end:
        for ev, d in events():
            if pred(ev, d): return d
        time.sleep(0.3)
    return None

def xlen(rid):
    return int(subprocess.run(DB + ["xlen", f"kokoro:run:{rid}:events"], capture_output=True, text=True).stdout.strip() or 0)

open(SSE, "w").close()
_, res = post(f"/sessions/{SID}/runs?input=hi&permission_mode=default")
run_id = res["runId"]; print("run_id:", run_id)
sse = subprocess.Popen(["curl", "-sN", "--max-time", "30", f"{BASE}/sessions/{SID}/stream"],
                       stdout=open(SSE, "w"), stderr=subprocess.DEVNULL)
fails = []
try:
    aw = wait_for(lambda ev, d: ev == "tool.awaiting_approval", 15)
    if aw and aw.get("payload", {}).get("name") == "write_todos" and aw.get("payload", {}).get("tool_id"):
        tid = aw["payload"]["tool_id"]; print(f"[1] AWAITING via SSE ok  name=write_todos tool_id={tid}")
    else:
        fails.append("awaiting"); tid = None; print("[1] AWAITING FAIL", aw)
    before = xlen(run_id)
    st, _ = post(f"/sessions/{SID}/runs/{run_id}/control",
                 body={"kind": "run.resume", "decisions": [{"type": "approve", "tool_id": tid}]})
    print(f"[2] RESUME(approve) -> HTTP {st} " + ("ok" if st == 202 else "FAIL"))
    if st != 202: fails.append("resume-202")
    grew = any(xlen(run_id) > before or time.sleep(0.5) for _ in range(20))
    print(f"[3] RESUME delivered to worker (run events {before}->{xlen(run_id)}) " + ("ok" if grew else "FAIL"))
    if not grew: fails.append("resume-delivered")
    st, _ = post(f"/sessions/{SID}/runs/{run_id}/control", body={"kind": "run.cancel"})
    print(f"[4] CANCEL -> HTTP {st}")
    term = wait_for(lambda ev, d: ev in ("run.completed", "run.failed"), 12)
    print(f"[4] TERMINAL via SSE " + (f"ok  {term.get('event')}" if term else "FAIL"))
    if not term: fails.append("terminal")
finally:
    sse.terminate()
print("\n" + ("PASS" if not fails else "FAIL " + str(fails)) + " — HITL ① cross-process e2e")
sys.exit(0 if not fails else 1)
PYEOF
