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
PORTS = {"site": 4201, "user": 4211, "model": 4221, "credit": 4231, "payment": 4241}
BASE = {k: f"http://127.0.0.1:{v}" for k, v in PORTS.items()}
# dev mock 支付网关 webhook 签名密钥（仅 dev；payment 验签 + web BFF 签发 mock 支付回调共用）。
MOCK_WEBHOOK_SECRET = "dev-mock-webhook-secret-not-real"
# 能力中台 hub（HUB-CONSIST）：session 建会话经 /hub/runtime/resolve 取 skills+McpGrant[]，dev 必起。
HUB_PORT = 4251
HUB_BASE = f"http://127.0.0.1:{HUB_PORT}"
SESSION_PORT = 3900
WEB_PORT = 3000
# web BFF 会话信封 dev 密钥（明显假值；生产走 secret 注入）。逗号分隔即双钥轮换（current 在前）。
WEB_SESSION_SECRET = "dev-web-session-secret-not-real"
# dev 站点 id：session/smoke/web BFF 全用此常量（与 seed 的站点解析一致）。
SITE_ID = "site-site-dev"

# TRUST-ROUTES：platform 服务 default-internal，按 per-caller secret 校验。dev 全用明显假值；
# 生产走各自 secret 注入。全服务共用同一注册表，各自据 x-kokoro-service 定位期望 secret。
INTERNAL_SECRETS = {
    "KOKORO_INTERNAL_SECRET_SESSION": "dev-internal-session-not-real",
    "KOKORO_INTERNAL_SECRET_WEB_BFF": "dev-internal-web-bff-not-real",
    "KOKORO_INTERNAL_SECRET_ADMIN": "dev-internal-admin-not-real",
    "KOKORO_INTERNAL_SECRET_HUB": "dev-internal-hub-not-real",
    "KOKORO_INTERNAL_SECRET_PAYMENT": "dev-internal-payment-not-real",
    "KOKORO_INTERNAL_SECRET_CREDIT": "dev-internal-credit-not-real",
}
# 脚本直调 user/site/model/credit 的 runtime-internal 路由：冒充 runtime caller=session。
RUNTIME_HDR = {
    "x-kokoro-service": "session",
    "x-kokoro-internal-secret": INTERNAL_SECRETS["KOKORO_INTERNAL_SECRET_SESSION"],
}


def load_glm_creds() -> dict[str, str]:
    """从 gitignored 的 kokoro-agent/.env 取 GLM(openai 兼容)凭据 → GLM_API_KEY/GLM_BASE_URL。
    只运行时读、注入子进程 env(litellm 容器据此以 claude-code 别名调 GLM),绝不落任何提交文件;
    缺任一返回 {}(→ 回落假模型,dev chat 不受影响)。"""
    env_file = ROOT / "kokoro-agent" / ".env"
    if not env_file.exists():
        return {}
    creds: dict[str, str] = {}
    for raw in env_file.read_text().splitlines():
        line = raw.strip()
        if line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        creds[k.strip()] = v.strip().strip('"').strip("'")
    key, base = creds.get("OPENAI_API_KEY", ""), creds.get("OPENAI_BASE_URL", "")
    return {"GLM_API_KEY": key, "GLM_BASE_URL": base} if key and base else {}


def claude_code_reachable() -> bool:
    """经本地 litellm 网关探 claude-code 别名是否真能出文(200)。后端由 resolve_claude_code_backend
    定(GLM/ollama);任一探通=真档,否则回落假模型。不阻塞起环。"""
    try:
        body = json.dumps({"model": "claude-code",
                           "messages": [{"role": "user", "content": "ping"}],
                           "max_tokens": 8}).encode()
        req = urllib.request.Request(
            "http://127.0.0.1:4000/v1/chat/completions", data=body,
            headers={"authorization": f"Bearer {LITELLM_KEY}", "content-type": "application/json"})
        with urllib.request.urlopen(req, timeout=90) as r:
            return r.status == 200
    except Exception:
        return False


def ollama_available() -> str | None:
    """本机 ollama 在跑且有模型 → 返回 openai/<tag>(优先 qwen3:8b);否则 None。
    GLM 不可用时的本地真模型回落源——保证 dev 真人始终能看到真实(非 fake)输出。
    放宽超时 + 两次重试:docker 重建 IO 高峰期短暂不可达不误判为无。"""
    for attempt in range(2):
        try:
            with urllib.request.urlopen("http://127.0.0.1:11434/v1/models", timeout=6) as r:
                models = [m["id"] for m in json.loads(r.read()).get("data", [])]
            if models:
                return f"openai/{next((m for m in models if 'qwen3:8b' in m), models[0])}"
            return None
        except Exception:
            if attempt == 0:
                time.sleep(2)
    return None


def litellm_ready() -> bool:
    """litellm health/liveliness 200。force-recreate 后端口先开、~20s 才就绪,故等 health 而非端口。"""
    for _ in range(40):
        try:
            with urllib.request.urlopen("http://127.0.0.1:4000/health/liveliness", timeout=2) as r:
                if r.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(1)
    return False


def _recreate_litellm(extra_env: dict[str, str]) -> None:
    """按选中的 claude-code 后端 env 重建 litellm 网关(凭据只经进程 env,不落文件),等其真就绪。"""
    subprocess.run(["docker", "compose", "-f", "docker-compose.dev.yml", "up", "-d", "--force-recreate"],
                   cwd=PLAT / "kokoro-litellm", check=True, capture_output=True,
                   env={**os.environ, **extra_env})
    litellm_ready()


def resolve_claude_code_backend() -> dict[str, str]:
    """决定 claude-code 别名的真后端并重建网关,三级回落:
      ① GLM 凭据探通 → GLM(生产意图);② 否则本机 ollama 在 → 本地真模型;③ 都不行 → mock-only(上游 fake)。
    「对外 claude-code 名不变、网关侧一处换后端」——返回选中的 CLAUDE_CODE_* env(空={}=无真后端)。"""
    glm = load_glm_creds()
    if glm:
        env = {"CLAUDE_CODE_MODEL": "openai/glm-5",
               "CLAUDE_CODE_BASE_URL": glm["GLM_BASE_URL"], "CLAUDE_CODE_API_KEY": glm["GLM_API_KEY"]}
        _recreate_litellm(env)
        if claude_code_reachable():
            step("模型: claude-code → GLM(凭据探通)", True)
            return env
    # 本地 ollama 回落默认关(opt-in KOKORO_DEV_LOCAL_FALLBACK=1)：小模型(如 qwen3:8b)能应付
    # 简单补全,但驱动不了完整 deepagents 编排(多步工具/结构化输出),run 会失败——默认宁可 fake 兜底文案。
    # 有能力的本地模型(30B+/工具能力强)可显式开启,或用 KOKORO_DEV_LOCAL_MODEL 指定 tag。
    if os.environ.get("KOKORO_DEV_LOCAL_FALLBACK") == "1":
        tag = os.environ.get("KOKORO_DEV_LOCAL_MODEL") or ollama_available()
        if tag:
            env = {"CLAUDE_CODE_MODEL": tag if tag.startswith(("openai/", "ollama/")) else f"openai/{tag}",
                   "CLAUDE_CODE_BASE_URL": "http://host.docker.internal:11434/v1", "CLAUDE_CODE_API_KEY": "ollama"}
            _recreate_litellm(env)
            if claude_code_reachable():
                step(f"模型: claude-code → 本地 {env['CLAUDE_CODE_MODEL']}(opt-in 本地回落)", True)
                return env
    _recreate_litellm({})
    step("模型: 无真后端(GLM 失效且无 ollama)→ 假模型回落", True)
    return {}


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
    # litellm 网关由 resolve_claude_code_backend() 起（需按 GLM/ollama 探测结果注入后端 env）。


def migrate() -> None:
    for m, envkey in (("site", "DATABASE_URL_SITE"), ("user", "DATABASE_URL_USER"),
                      ("model", "DATABASE_URL_MODEL"), ("credit", "DATABASE_URL_CREDIT"),
                      ("payment", "DATABASE_URL_PAYMENT")):
        r = subprocess.run(["npx", "prisma", "migrate", "deploy"], cwd=PLAT / f"kokoro-{m}",
                           env={**os.environ, envkey: DB}, capture_output=True, text=True)
        step(f"migrate {m}", r.returncode == 0, r.stdout[-200:] + r.stderr[-200:])


def boot(real_model: bool) -> dict[str, int]:
    pids: dict[str, int] = {}
    # 包体/工作区存储配置：session/agent 取 workspace+deliveries，hub 取 hub 节（skills 包体权威源）。
    # 必须在 hub/session spawn 前落盘（服务启动即读 KOKORO_WORKSPACE_CONFIG）——缺 hub 节=上传 confirm 503。
    (STATE / "storage.yaml").write_text(
        f"workspace:\n  type: local\n  root: {STATE / 'workspace'}\n"
        f"deliveries:\n  type: local\n  root: {STATE / 'deliveries'}\n"
        f"hub:\n  type: local\n  root: {STATE / 'hub-packages'}\n"
    )
    penv = {
        "site": {"DATABASE_URL_SITE": DB, "KOKORO_SITE_PORT": str(PORTS["site"])},
        "user": {"DATABASE_URL_USER": DB, "KOKORO_USER_PORT": str(PORTS["user"]),
                 "KOKORO_AUTH_JWT_SECRET": AUTH_SECRET,
                 # dev：magic-link 原文 token 回响应体，web BFF 据此生成可点开发链（生产走邮件）。
                 "KOKORO_AUTH_MAGIC_DELIVERY": "response",
                 # dev 会话 24h（默认 1h，反复测试易过期致 401 加载失败）；生产用默认。
                 "KOKORO_AUTH_JWT_TTL_SECONDS": "86400"},
        "model": {"DATABASE_URL_MODEL": DB, "KOKORO_MODEL_PORT": str(PORTS["model"])},
        "credit": {"DATABASE_URL_CREDIT": DB, "KOKORO_CREDIT_PORT": str(PORTS["credit"]),
                   "KOKORO_USER_BASE_URL": BASE["user"], "KOKORO_SITE_BASE_URL": BASE["site"],
                   "KOKORO_MODEL_BASE_URL": BASE["model"]},
        # 支付：用户自助购买积分包 → 支付成功到账 credit（payment→credit grant 已 wired，恰一次）。
        # mock provider 恒挂,webhookSecretRef 指向下面这个 env 名,dev 用它验签模拟支付回调。
        "payment": {"DATABASE_URL_PAYMENT": DB, "KOKORO_PAYMENT_PORT": str(PORTS["payment"]),
                    "KOKORO_CREDIT_BASE_URL": BASE["credit"], "KOKORO_USER_BASE_URL": BASE["user"],
                    "KOKORO_MODEL_BASE_URL": BASE["model"],
                    "KOKORO_PAYMENT_MOCK_WEBHOOK_SECRET": MOCK_WEBHOOK_SECRET},
    }
    for name, extra in penv.items():
        if not port_open(PORTS[name]):
            pids[name] = spawn(["pnpm", "run", "start"], PLAT / f"kokoro-{name}",
                               {**os.environ, **INTERNAL_SECRETS, **extra}, STATE / f"{name}.log")
        step(f"platform {name} {PORTS[name]}", wait_port(PORTS[name]))
    # 能力中台 hub（HUB-CONSIST）：与 session/agent 同库（kokoro_dev，读写分离）。
    # dev 默认开 MCP mutation 门（自服务注册可用，可 KOKORO_HUB_MCP_MUTATION=off 关）。
    if not port_open(HUB_PORT):
        pids["hub"] = spawn(
            ["pnpm", "run", "start"], PLAT / "kokoro-hub",
            {**os.environ, **INTERNAL_SECRETS,
             "KOKORO_HUB_PORT": str(HUB_PORT),
             "KOKORO_HUB_MONGO_URL": "mongodb://127.0.0.1:27017",
             "KOKORO_HUB_MONGO_DB": "kokoro_dev",
             "KOKORO_USER_BASE_URL": BASE["user"],
             # 包体存储：hub 取 storage.yaml 的 hub 节（local），skills 上传 confirm 据此落包。
             "KOKORO_WORKSPACE_CONFIG": str(STATE / "storage.yaml"),
             "KOKORO_HUB_MCP_MUTATION": os.environ.get("KOKORO_HUB_MCP_MUTATION", "on")},
            STATE / "hub.log")
    step(f"hub {HUB_PORT}", wait_port(HUB_PORT))
    session_env = {
        **os.environ,
        # session 出站 caller 头由主控合流 kokoro-session 改动后启用；此处先备好 caller secret。
        **INTERNAL_SECRETS,
        "KOKORO_SESSION_PORT": str(SESSION_PORT),
        "KOKORO_REDIS_URL": "redis://127.0.0.1:6379/0",
        "KOKORO_MESSAGE_STORE_MONGO_URL": "mongodb://127.0.0.1:27017",
        "KOKORO_MESSAGE_STORE_MONGO_DB": "kokoro_dev",
        # 能力中台 hub 基址（HUB-CONSIST）：buildSnapshot 经此取 skills + McpGrant[] 定死会话快照。
        "KOKORO_HUB_BASE_URL": HUB_BASE,
        "KOKORO_WORKSPACE_ROOT": str(STATE / "workspace"),
        "KOKORO_WORKSPACE_CONFIG": str(STATE / "storage.yaml"),
        "KOKORO_AUTH_JWT_SECRET": AUTH_SECRET,
        # shadow：计费全链打点但不拒绝——dev 默认不挡人;enforce 用 E2E-40/生产档。
        "KOKORO_BILLING_MODE": os.environ.get("KOKORO_BILLING_MODE", "shadow"),
        "KOKORO_CREDIT_BASE_URL": BASE["credit"],
        "KOKORO_MODEL_BASE_URL": BASE["model"],
        "KOKORO_SITE_ID": SITE_ID,
        # 直连档保留：浏览器直连 session 时的 CORS 白名单（session 原生单源开关）。AUTH-P0 起
        # 默认走同源 web BFF，浏览器同源不再依赖此项；生产按真实站点域名配置。
        "KOKORO_WEB_ORIGIN": os.environ.get("KOKORO_WEB_ORIGIN", f"http://127.0.0.1:{WEB_PORT}"),
    }
    agent_env = {
        **os.environ,
        "KOKORO_WORKSPACE_CONFIG": str(STATE / "storage.yaml"),
        "KOKORO_REDIS_URL": "redis://127.0.0.1:6379/0",
        "KOKORO_MONGO_URL": "mongodb://127.0.0.1:27017",
        "KOKORO_MONGO_DB": "kokoro_dev",
        "KOKORO_AGENT_LOCAL_SHELL_ROOT": str(STATE / "workspace"),
        # MCP egress 防线放行环回：本地 127.0.0.1 MCP fixture（strict 缺省会拒 loopback）。
        "KOKORO_MCP_EGRESS_MODE": "off",
        # 真档(GLM 凭据探通)=关离线假模型,chat 走 litellm→GLM(claude-code);否则回落假模型
        # (dev 照常可用)。显式 env 覆盖优先。
        "KOKORO_LOCAL_FAKE_MODEL": os.environ.get("KOKORO_LOCAL_FAKE_MODEL", "0" if real_model else "1"),
        "KOKORO_LITELLM_BASE_URL": "http://127.0.0.1:4000/v1",
        "KOKORO_LITELLM_API_KEY": LITELLM_KEY,
    }
    if not port_open(SESSION_PORT):
        pids["session"] = spawn(["npm", "run", "start"], ROOT / "kokoro-session", session_env,
                                STATE / "session.log")
    step(f"session {SESSION_PORT}", wait_port(SESSION_PORT))
    # 双 worker 守卫:残留 worker 同组消费制造 control/replay 竞争(P0.5 实录主嫌)。
    # SIGTERM 触发 agent 优雅停机(drain 可达 drain_timeout_s=60s),与新 worker 重叠成 60s 竞争窗——
    # 重启后几秒内的 run 会被还在 drain 的旧 worker 抢走(错模型/错档)。故用 SIGKILL 立即清,
    # 并轮询等旧 worker 真正退场再起新的,彻底消除重启期双 worker。
    subprocess.run(["pkill", "-9", "-f", "kokoro-agent-worker"], check=False, capture_output=True)
    for _ in range(30):
        if subprocess.run(["pgrep", "-f", "kokoro-agent-worker"], capture_output=True).returncode != 0:
            break  # 无匹配进程=旧 worker 已退场
        time.sleep(0.3)
    pids["agent"] = spawn(["uv", "run", "kokoro-agent-worker"], ROOT / "kokoro-agent", agent_env,
                          STATE / "agent.log")
    step("agent worker(独占)", True)
    return pids


def web_bff_env() -> dict[str, str]:
    # 浏览器同源走 web BFF 代理（AUTH-P0），不再直连 session 3900。以下是 web dev 的**服务端** env
    # （非 NEXT_PUBLIC，浏览器读不到）：user/session 地址、站点 id、信封密钥、web-bff 出站凭据全留服务端。
    return {
        "KOKORO_WEB_SESSION_SECRET": WEB_SESSION_SECRET,
        "KOKORO_USER_BASE_URL": BASE["user"],
        "KOKORO_SESSION_BASE_URL": f"http://127.0.0.1:{SESSION_PORT}",
        "KOKORO_SITE_ID": SITE_ID,
        # hub 基址：缺则 web BFF 的 /api/hub 代理回 503、设置中心技能/连接 tab 不可用。
        "KOKORO_HUB_BASE_URL": HUB_BASE,
        # 支付：缺则 web 价格页/充值诚实「支付暂未开通」。mock secret 供 dev 模拟收银台 BFF 签发支付回调。
        "KOKORO_PAYMENT_BASE_URL": BASE["payment"],
        "KOKORO_PAYMENT_MOCK_WEBHOOK_SECRET": MOCK_WEBHOOK_SECRET,
        "KOKORO_INTERNAL_SECRET_WEB_BFF": INTERNAL_SECRETS["KOKORO_INTERNAL_SECRET_WEB_BFF"],
    }


def write_web_bff_env() -> Path:
    # 落一个 env 文件，web dev 可直接吃：`set -a; source tmp/closure/web-bff.env; set +a; pnpm --dir kokoro-web dev`。
    path = STATE / "web-bff.env"
    path.write_text("".join(f"{k}={v}\n" for k, v in web_bff_env().items()))
    return path


def seed() -> None:
    st, resp = http("POST", f"{BASE['site']}/sites/upsert",
                    {"key": "site-dev", "name": "Dev 闭环站", "status": "active"}, RUNTIME_HDR)
    site_id = str((resp.get("data") or {}).get("id", ""))
    step("seed site", st == 200 and site_id != "", f"{st} {resp}")
    hdr = {"x-kokoro-site-id": site_id, **RUNTIME_HDR}
    # 平台内置默认目录（claude-code 门面 = provider gateway + claude-code binding + label）：
    # 定义在 kokoro-model 单一真源，此处只触发其 seed:builtin，编排层不再硬编码内置目录内容。
    r = subprocess.run(["pnpm", "run", "seed:builtin"], cwd=PLAT / "kokoro-model",
                       env={**os.environ, "DATABASE_URL_MODEL": DB},
                       capture_output=True, text=True)
    step("seed 内置默认目录（kokoro-model seed:builtin）", r.returncode == 0,
         (r.stdout + r.stderr).strip().splitlines()[-1] if (r.stdout or r.stderr) else str(r.returncode))
    # dev-only：离线假模型档（kokoro-dev-mock），GLM 缺时 /models 仍有可选项。自有 dev provider，
    # 不进平台内置目录（生产不该出现「Dev Mock」）。label.key ∈ binding.labelKeys 才不被可用性过滤剔除。
    st, acc = http("POST", f"{BASE['model']}/provider-accounts/ensure",
                   {"provider": "litellm", "key": "dev-fake", "label": "dev 假模型网关",
                    "secretRef": "env:LITELLM_MASTER_KEY", "transportKind": "litellm"}, hdr)
    acc_id = str((acc.get("data") or {}).get("id", ""))
    st2, mock = http("POST", f"{BASE['model']}/model-bindings/ensure",
                     {"providerAccountId": acc_id, "modelName": "kokoro-dev-mock",
                      "displayName": "Dev mock（litellm 网关）", "featureKey": "chat",
                      "labelKeys": ["kokoro-dev-mock", "claude-sonnet-4-6"],
                      "transportKind": "litellm", "gatewayModelName": "kokoro-dev-mock"}, hdr)
    mock_bid = str((mock.get("data") or {}).get("id", ""))
    stl, _ = http("POST", f"{BASE['model']}/model-labels/ensure",
                  {"key": "kokoro-dev-mock", "displayName": "Dev Mock（离线）", "featureKey": "chat",
                   "tier": "mock", "description": "离线假模型档，无需真凭据", "defaultBindingId": mock_bid}, hdr)
    step("seed dev 离线假模型（dev-only）", st == 200 and st2 == 200 and stl == 200, f"{st}/{st2}/{stl}")
    # 计价（PRD 2026-07-17-credit-pricing-strategy §7 内置默认档 dev 加价值）：
    # 售价 = 真成本 × margin(≥4×)；chat input 40 / output 120 micros/token。1 积分=10000 micros。
    # 典型 500+500 token 对话 ≈ (500×40+500×120)/10000 = 8 积分 ≈ ¥0.08。
    for unit, price in (("input_token", 40), ("output_token", 120)):
        stp, _ = http("POST", f"{BASE['credit']}/credit/pricing-rules",
                      {"featureKey": "chat", "unit": unit, "amountMicros": price}, hdr)
        step(f"seed 计价 {unit}", stp == 200, str(stp))
    # 支付 seed：积分包目录 + mock 支付网关。payment 只收 admin/payment caller,seed 用 admin 头。
    phdr = {"x-kokoro-site-id": site_id, "x-kokoro-service": "admin",
            "x-kokoro-internal-secret": INTERNAL_SECRETS["KOKORO_INTERNAL_SECRET_ADMIN"]}
    # 积分包（PRD §2 量折扣：¥0.01/积分,大包更省;1 积分=10000 micros）。billingInterval=once。
    packs = (
        ("pack-100", "入门包 100 积分", 100, 1_000_000),
        ("pack-500", "标准包 500 积分", 450, 5_000_000),
        ("pack-1000", "超值包 1000 积分", 850, 10_000_000),
        ("pack-3000", "尊享包 3000 积分", 2400, 30_000_000),
    )
    pok = True
    for key, name, amount_minor, credit_micros in packs:
        stp, _ = http("POST", f"{BASE['payment']}/plans/upsert",
                      {"key": key, "name": name, "currency": "CNY",
                       "amountMinor": str(amount_minor), "creditMicros": str(credit_micros),
                       "billingInterval": "once"}, phdr)
        pok = pok and stp == 200
    step("seed 积分包目录", pok, f"{len(packs)} plans")
    # mock 支付网关：webhookSecretRef 指向 payment env KOKORO_PAYMENT_MOCK_WEBHOOK_SECRET（验签用）。
    stp, _ = http("POST", f"{BASE['payment']}/admin/payments/providers/upsert",
                  {"key": "mock", "kind": "mock",
                   "webhookSecretRef": "KOKORO_PAYMENT_MOCK_WEBHOOK_SECRET", "enabled": True}, phdr)
    step("seed mock 支付网关", stp == 200, str(stp))


def smoke() -> None:
    # /auth/sessions 收编 runtime-internal（纲领 §5.1）：带 runtime caller 头调用。
    st, resp = http("POST", f"{BASE['user']}/auth/sessions",
                    {"site_id": "site-site-dev", "external_user_id": "dev-smoke"}, RUNTIME_HDR)
    tok = str((resp.get("data") or {}).get("token", ""))
    step("smoke: user 签发", st == 200 and tok != "", f"{st} {str(resp)[:120]}")
    st, snap = http("GET", f"http://127.0.0.1:{SESSION_PORT}/sessions/ses_dev_smoke",
                    headers={"authorization": f"Bearer {tok}"})
    step("smoke: session 验签（真签发 token 直通）", st in (200, 404), f"{st} {snap}")
    st, _ = http("POST", "http://127.0.0.1:4000/v1/chat/completions",
                 {"model": "kokoro-dev-mock", "messages": [{"role": "user", "content": "ping"}]},
                 {"authorization": f"Bearer {LITELLM_KEY}"})
    step("smoke: litellm 网关", st == 200, str(st))


def _record_pid(name: str, pid: int) -> None:
    # 把独立起的进程（如 web）pid 并入 pids.json，供 down 一并收环。
    f = STATE / "pids.json"
    pids: dict[str, int] = json.loads(f.read_text()) if f.exists() else {}
    pids[name] = pid
    f.write_text(json.dumps(pids))


def boot_web() -> int | None:
    # 纳管 web dev：注入同源 BFF env 后台起 next dev；已在跑则跳过。pid 记入 pids.json 供 down 清。
    if port_open(WEB_PORT):
        print(f"  [OK] web {WEB_PORT}（已在跑，跳过）")
        return None
    pid = spawn(["pnpm", "run", "dev"], ROOT / "kokoro-web",
                {**os.environ, **web_bff_env()}, STATE / "web.log")
    step(f"web dev {WEB_PORT}（首次编译稍慢，≤90s）", wait_port(WEB_PORT, 90),
         "web 启动失败，看 tmp/closure/web.log")
    _record_pid("web", pid)
    return pid


def chat_smoke() -> None:
    # 端到端对话真验：签发 token → POST 首消息（隐式建会话）→ 轮询 snapshot 至 run 终态
    # → 断言 assistant 完成。这是"对话是否跑通"的可重复回归探针（防 activeId 越权类前端断链复发）。
    st, resp = http("POST", f"{BASE['user']}/auth/sessions",
                    {"site_id": SITE_ID, "external_user_id": "dev-chat-smoke"}, RUNTIME_HDR)
    tok = str((resp.get("data") or {}).get("token", ""))
    step("chat: user 签发 token", st == 200 and tok != "", f"{st} {str(resp)[:120]}")
    auth = {"authorization": f"Bearer {tok}"}
    sid = "ses_chat_smoke"
    st, rec = http("POST", f"http://127.0.0.1:{SESSION_PORT}/sessions/{sid}/messages",
                   {"idempotency_key": f"idem-chat-{int(time.time())}",
                    "content": "ping，请用一句话确认你在线。"}, auth)
    run_id = str(rec.get("run_id", ""))
    # 202 Accepted：消息已受理、run 异步开跑（session 的正常回执码）。
    step("chat: 发首条消息（隐式建会话）", st in (200, 201, 202) and run_id != "",
         f"{st} {str(rec)[:160]}")
    # 终态以事件流为权威：snapshot 不含 messages（历史走 SSE 回放）。回放 last-event-id=0
    # 逐帧读，抓 run.completed（成功）/ run.failed（失败）。fake 模型不走 delta，回复在 message.completed。
    ereq = urllib.request.Request(
        f"http://127.0.0.1:{SESSION_PORT}/sessions/{sid}/events",
        headers={**auth, "accept": "text/event-stream", "last-event-id": "0"})
    kinds: list[str] = []
    reply = ""
    outcome = ""
    try:
        with urllib.request.urlopen(ereq, timeout=25) as stream:
            for raw in stream:
                s = raw.decode(errors="replace").strip()
                if not s.startswith("data:"):
                    continue
                try:
                    ev = json.loads(s[len("data:"):].strip())
                except json.JSONDecodeError:
                    continue
                kind = str(ev.get("kind", ""))
                kinds.append(kind)
                if kind == "message.completed":
                    reply = str((ev.get("payload") or {}).get("content", ""))[:70]
                if kind in ("run.completed", "run.failed"):
                    outcome = kind
                    break
    except Exception as exc:  # noqa: BLE001 — 探针：任何流异常都视作未跑通并如实报出
        outcome = f"stream_error:{type(exc).__name__}"
    step("chat: run 端到端跑完（事件流见 run.completed）", outcome == "run.completed",
         f"未见 run.completed（收到 {outcome or '无终态'}；kinds={kinds}）——对话链路可能断裂")
    print(f"  [OK] 对话跑通 — 事件序列：{kinds}")
    if reply:
        print(f"       assistant 回复片段：{reply}")


def cmd_up() -> None:
    STATE.mkdir(parents=True, exist_ok=True)
    print("== infra"); ensure_infra()
    # claude-code 真后端三级回落(GLM→ollama→fake)+ 据此定真/假档。
    print("== 模型后端"); real_model = bool(resolve_claude_code_backend())
    print("== migrations"); migrate()
    print("== services"); pids = boot(real_model)
    (STATE / "pids.json").write_text(json.dumps(pids))
    print("== seed"); seed()
    print("== smoke"); smoke()
    write_web_bff_env()
    print("== web"); boot_web()
    print(f"\n闭环已就绪：web http://127.0.0.1:{WEB_PORT} / session :{SESSION_PORT} / "
          f"litellm :4000 / platform {PORTS}")
    print(f"日志与 pid: {STATE}/")
    print("  收环: python3 scripts/closure-up.py down")
    print("  重启: python3 scripts/closure-up.py restart")
    print("  测对话(端到端): python3 scripts/closure-up.py chat")


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
    for name, port in {**PORTS, "hub": HUB_PORT, "session": SESSION_PORT, "web": WEB_PORT,
                       "litellm": 4000, "mysql": 3307, "mongo": 27017, "redis": 6379,
                       "minio": 9100}.items():
        print(f"  {'UP  ' if port_open(port) else 'DOWN'} {name}:{port}")


def cmd_restart() -> None:
    # 快速重起本脚本起的进程栈（infra 容器保留）：先收后起。
    cmd_down()
    print()
    cmd_up()


def cmd_web() -> None:
    # 只起/纳管 web dev（其余栈需已 up）。
    STATE.mkdir(parents=True, exist_ok=True)
    write_web_bff_env()
    print("== web"); boot_web()


def cmd_chat() -> None:
    # 端到端对话回归探针（栈需已 up）。
    print("== chat 端到端"); chat_smoke()


if __name__ == "__main__":
    {"up": cmd_up, "down": cmd_down, "status": cmd_status,
     "restart": cmd_restart, "web": cmd_web, "chat": cmd_chat}.get(
        sys.argv[1] if len(sys.argv) > 1 else "status", cmd_status)()
