#!/usr/bin/env python3
"""一键起环（dev 闭环）：infra → migrations → platform 四服务 + litellm → session + agent → 种子 → smoke。

    python3 scripts/closure-up.py up      # 起环并 smoke（幂等,可重复跑）
    python3 scripts/closure-up.py down    # 收环（只杀本脚本起的进程,infra 容器保留）
    python3 scripts/closure-up.py status  # 各口健康态

布局（dev canonical）：mysql 3307 / mongo 27017 / redis 6379 / minio 9100 / litellm 4000
platform: site 4201 user 4211 model 4221 credit 4231 / session 3900(billing=shadow) / agent worker
凭据全为 dev 明显假值；生产部署走各自 secret 注入,与本脚本无关。
"""

from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAT = ROOT / "kokoro-platform"
STATE = ROOT / "tmp" / "closure"
DB = "mysql://root:kokoro_root@127.0.0.1:3307/kokoro"
AUTH_SECRET = os.environ.get("KOKORO_AUTH_JWT_SECRET", "dev-secret-not-real")
LITELLM_KEY = "dev-master-key-not-real"
PORTS = {"site": 4201, "user": 4211, "model": 4221, "credit": 4231}
BASE = {k: f"http://127.0.0.1:{v}" for k, v in PORTS.items()}
SESSION_PORT = 3900


def port_open(port: int) -> bool:
    with socket.socket() as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def wait_port(port: int, timeout: float = 60.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if port_open(port):
            return True
        time.sleep(0.5)
    return False


def http(method: str, url: str, body: dict | None = None, headers: dict | None = None):
    req = urllib.request.Request(url, method=method,
                                 data=None if body is None else json.dumps(body).encode(),
                                 headers={"content-type": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read() or b"{}")
        except Exception:
            return e.code, {}
    except Exception:
        return 0, {}


def step(name: str, ok: bool, detail: str = "") -> None:
    print(f"  [{'OK' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail and not ok else ""))
    if not ok:
        print("closure-up 失败,先修上面这项再重跑。")
        sys.exit(1)


def spawn(cmd: list[str], cwd: Path, env: dict[str, str], log: Path) -> int:
    log.parent.mkdir(parents=True, exist_ok=True)
    with open(log, "ab") as fh:
        proc = subprocess.Popen(cmd, cwd=cwd, env=env, stdout=fh, stderr=fh,
                                start_new_session=True)
    return proc.pid


def ensure_infra() -> None:
    # mysql：kokoro-platform 根 compose 管；mongo/redis/minio：dev 机常驻容器,不在则拉起提示。
    if not port_open(3307):
        subprocess.run(["docker", "compose", "up", "-d"], cwd=PLAT, check=True, capture_output=True)
    step("mysql 3307", wait_port(3307), "kokoro-platform docker compose 启动失败,看 docker 日志")
    for name, port, hint in (
        ("mongo", 27017, "docker start kokoro-dev-mongo"),
        ("redis", 6379, "docker start <redis 容器> 或本机 redis-server"),
        ("minio", 9100, "docker start kokoro-minio"),
    ):
        if not port_open(port):
            subprocess.run(["docker", "start", f"kokoro-dev-{name}" if name == "mongo" else f"kokoro-{name}"],
                           check=False, capture_output=True)
        step(f"{name} {port}", wait_port(port, 15), hint)
    if not port_open(4000):
        subprocess.run(["docker", "compose", "-f", "docker-compose.dev.yml", "up", "-d"],
                       cwd=PLAT / "kokoro-litellm", check=True, capture_output=True)
    step("litellm 4000（dev mock 档）", wait_port(4000))


def migrate() -> None:
    for m, envkey in (("site", "DATABASE_URL_SITE"), ("user", "DATABASE_URL_USER"),
                      ("model", "DATABASE_URL_MODEL"), ("credit", "DATABASE_URL_CREDIT"),
                      ("payment", "DATABASE_URL_PAYMENT")):
        r = subprocess.run(["npx", "prisma", "migrate", "deploy"], cwd=PLAT / f"kokoro-{m}",
                           env={**os.environ, envkey: DB}, capture_output=True, text=True)
        step(f"migrate {m}", r.returncode == 0, r.stdout[-200:] + r.stderr[-200:])


def boot() -> dict[str, int]:
    pids: dict[str, int] = {}
    penv = {
        "site": {"DATABASE_URL_SITE": DB, "KOKORO_SITE_PORT": str(PORTS["site"])},
        "user": {"DATABASE_URL_USER": DB, "KOKORO_USER_PORT": str(PORTS["user"]),
                 "KOKORO_AUTH_JWT_SECRET": AUTH_SECRET},
        "model": {"DATABASE_URL_MODEL": DB, "KOKORO_MODEL_PORT": str(PORTS["model"])},
        "credit": {"DATABASE_URL_CREDIT": DB, "KOKORO_CREDIT_PORT": str(PORTS["credit"]),
                   "KOKORO_USER_BASE_URL": BASE["user"], "KOKORO_SITE_BASE_URL": BASE["site"],
                   "KOKORO_MODEL_BASE_URL": BASE["model"]},
    }
    for name, extra in penv.items():
        if not port_open(PORTS[name]):
            pids[name] = spawn(["pnpm", "run", "start"], PLAT / f"kokoro-{name}",
                               {**os.environ, **extra}, STATE / f"{name}.log")
        step(f"platform {name} {PORTS[name]}", wait_port(PORTS[name]))
    session_env = {
        **os.environ,
        "KOKORO_SESSION_PORT": str(SESSION_PORT),
        "KOKORO_REDIS_URL": "redis://127.0.0.1:6379/0",
        "KOKORO_MESSAGE_STORE_MONGO_URL": "mongodb://127.0.0.1:27017",
        "KOKORO_MESSAGE_STORE_MONGO_DB": "kokoro_dev",
        "KOKORO_WORKSPACE_ROOT": str(STATE / "workspace"),
        "KOKORO_AUTH_JWT_SECRET": AUTH_SECRET,
        # shadow：计费全链打点但不拒绝——dev 默认不挡人;enforce 用 E2E-40/生产档。
        "KOKORO_BILLING_MODE": os.environ.get("KOKORO_BILLING_MODE", "shadow"),
        "KOKORO_CREDIT_BASE_URL": BASE["credit"],
        "KOKORO_MODEL_BASE_URL": BASE["model"],
        "KOKORO_SITE_ID": "site-site-dev",
    }
    agent_env = {
        **os.environ,
        "KOKORO_REDIS_URL": "redis://127.0.0.1:6379/0",
        "KOKORO_MONGO_URL": "mongodb://127.0.0.1:27017",
        "KOKORO_MONGO_DB": "kokoro_dev",
        "KOKORO_AGENT_LOCAL_SHELL_ROOT": str(STATE / "workspace"),
        # dev 缺省离线模型;接真模型改 env(litellm 档已配好网关对)。
        "KOKORO_LOCAL_FAKE_MODEL": os.environ.get("KOKORO_LOCAL_FAKE_MODEL", "1"),
        "KOKORO_LITELLM_BASE_URL": "http://127.0.0.1:4000/v1",
        "KOKORO_LITELLM_API_KEY": LITELLM_KEY,
    }
    if not port_open(SESSION_PORT):
        pids["session"] = spawn(["npm", "run", "start"], ROOT / "kokoro-session", session_env,
                                STATE / "session.log")
    step(f"session {SESSION_PORT}", wait_port(SESSION_PORT))
    pids["agent"] = spawn(["uv", "run", "kokoro-agent-worker"], ROOT / "kokoro-agent", agent_env,
                          STATE / "agent.log")
    step("agent worker", True)
    return pids


def seed() -> None:
    st, resp = http("POST", f"{BASE['site']}/sites/upsert",
                    {"key": "site-dev", "name": "Dev 闭环站", "status": "active"})
    site_id = str((resp.get("data") or {}).get("id", ""))
    step("seed site", st == 200 and site_id != "", f"{st} {resp}")
    hdr = {"x-kokoro-site-id": site_id}
    st, acc = http("POST", f"{BASE['model']}/provider-accounts/ensure",
                   {"provider": "litellm", "key": "dev-gateway", "label": "dev 网关",
                    "secretRef": "env:LITELLM_MASTER_KEY", "transportKind": "litellm"}, hdr)
    acc_id = str((acc.get("data") or {}).get("id", ""))
    st2, _ = http("POST", f"{BASE['model']}/model-bindings/ensure",
                  {"providerAccountId": acc_id, "modelName": "kokoro-dev-mock",
                   "displayName": "Dev mock（litellm 网关）", "featureKey": "chat",
                   "labelKeys": ["kokoro-dev-mock", "claude-sonnet-4-6"],
                   "transportKind": "litellm", "gatewayModelName": "kokoro-dev-mock"}, hdr)
    step("seed model binding（litellm 档）", st == 200 and st2 == 200, f"{st}/{st2}")
    for unit, price in (("input_token", 20), ("output_token", 60)):
        stp, _ = http("POST", f"{BASE['credit']}/credit/pricing-rules",
                      {"featureKey": "chat", "unit": unit, "amountMicros": price}, hdr)
        step(f"seed 计价 {unit}", stp == 200, str(stp))


def smoke() -> None:
    st, resp = http("POST", f"{BASE['user']}/auth/sessions",
                    {"site_id": "site-site-dev", "external_user_id": "dev-smoke"})
    tok = str((resp.get("data") or {}).get("token", ""))
    step("smoke: user 签发", st == 200 and tok != "", f"{st} {str(resp)[:120]}")
    st, snap = http("GET", f"http://127.0.0.1:{SESSION_PORT}/sessions/ses_dev_smoke",
                    headers={"authorization": f"Bearer {tok}"})
    step("smoke: session 验签（真签发 token 直通）", st in (200, 404), f"{st} {snap}")
    st, _ = http("POST", "http://127.0.0.1:4000/v1/chat/completions",
                 {"model": "kokoro-dev-mock", "messages": [{"role": "user", "content": "ping"}]},
                 {"authorization": f"Bearer {LITELLM_KEY}"})
    step("smoke: litellm 网关", st == 200, str(st))


def cmd_up() -> None:
    STATE.mkdir(parents=True, exist_ok=True)
    print("== infra"); ensure_infra()
    print("== migrations"); migrate()
    print("== services"); pids = boot()
    (STATE / "pids.json").write_text(json.dumps(pids))
    print("== seed"); seed()
    print("== smoke"); smoke()
    print(f"\n闭环已就绪：session http://127.0.0.1:{SESSION_PORT} / litellm :4000 / platform {PORTS}")
    print(f"日志与 pid: {STATE}/ ；收环: python3 scripts/closure-up.py down")


def cmd_down() -> None:
    pids_file = STATE / "pids.json"
    if pids_file.exists():
        for name, pid in json.loads(pids_file.read_text()).items():
            try:
                os.killpg(os.getpgid(pid), signal.SIGTERM)
                print(f"  stopped {name} ({pid})")
            except ProcessLookupError:
                print(f"  {name} 已不在 ({pid})")
        pids_file.unlink()
    print("infra 容器保留（mysql/mongo/redis/minio/litellm）;要停 litellm:")
    print("  docker compose -f kokoro-platform/kokoro-litellm/docker-compose.dev.yml down")


def cmd_status() -> None:
    for name, port in {**PORTS, "session": SESSION_PORT, "litellm": 4000,
                       "mysql": 3307, "mongo": 27017, "redis": 6379, "minio": 9100}.items():
        print(f"  {'UP  ' if port_open(port) else 'DOWN'} {name}:{port}")


if __name__ == "__main__":
    {"up": cmd_up, "down": cmd_down, "status": cmd_status}.get(
        sys.argv[1] if len(sys.argv) > 1 else "status", cmd_status)()
