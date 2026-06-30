# Kokoro（こころ）

一个有人格的通用 AI agent。主战场是把「想法」一起做成可分享的产物，
气质柔、温、内观。
当前主线是**三仓 stream 聊天系统**：对话 + agent 活动流，
边生成边流式呈现，可中断可续传。

> 这份 README 面向新贡献者。产品需求看
> [`docs/requirements/`](docs/requirements/)；架构与决策细节看
> [`docs/superpowers/specs/`](docs/superpowers/specs/) 与
> [`docs/decisions/`](docs/decisions/)。

## 架构一图

三层，仅经 **redis stream + SSE** 协议耦合，各自独立部署：

```text
kokoro-agent
  -> redis run-events
  -> kokoro-session
  -> Mongo replay + SSE
  -> kokoro-web

agent:   DeepAgents/LangChain 执行侧，产原始 AgentEvent。
session: DB-first 归一化，Redis 只做队列与 live fanout。
web:     strict parse，eventId 去重，按 session 发送顺序 append。
```

- **[kokoro-agent](kokoro-agent/)** — DeepAgents/LangChain worker，
  产出原始 `AgentEvent`，写 redis。
- **[kokoro-session](kokoro-session/)** — 归一化 AGUI 信封，
  Mongo session_events 持久化，SSE replay/live fan-out。不执行 agent。
- **[kokoro-web](kokoro-web/)** — Next.js 聊天壳，消费 SSE，
  按 session 发送顺序 append thread 并渲染。

当前三仓仍有 P0 收口项：session `agent_run_input` manifest 与 agent Python `RunRequest`
尚未合流，web 尚未完成 snapshot-first hydrate；以
[`docs/kokoro-handbook/technical/11-agent-session-web-v1-runtime.md`](docs/kokoro-handbook/technical/11-agent-session-web-v1-runtime.md)
为准。

三仓统一四层 DDD：`domain` / `application` / `infrastructure` /
`interfaces`。上层只依赖抽象，依赖倒置。

## 跨仓契约（单源生成）

浏览器侧 AGUI/render 事件契约的**单一真理来源**是
[`contract/events.yaml`](contract/events.yaml)；agent 原始 wire 事件的单一真理来源是
[`interfaces/envelope.py`](kokoro-agent/src/kokoro_agent/interfaces/envelope.py)。

- `python3 contract/generate.py` —— 从 `events.yaml` 生成 session/web AGUI
  镜像，并从 agent `envelope.py` 生成 session 入站 Zod 镜像。
- `python3 contract/generate.py --check` —— CI 门禁：yaml 改了忘重生成即非零退出。
- `python3 contract/verify.py` —— 名集漂移门禁（与 --check 互补）。

详见 [契约 codegen 设计](docs/superpowers/specs/2026-06-14-contract-codegen-design.md)。

## 本地起栈（开发）

前置：`redis`、`uv`（Python）、`bun`（TS）。使用隔离的 redis db，
例如 db10，不要碰生产 db0。

```bash
# 1. session（SSE/replay 桥，:3001）
cd kokoro-session
KOKORO_STREAM_BACKEND=redis KOKORO_REDIS_URL=redis://127.0.0.1:6379/10 bun run src/main.ts

# 2. agent worker（凭据无关的本地假模型，便于离线试玩）
cd kokoro-agent
KOKORO_STREAM_BACKEND=redis KOKORO_REDIS_URL=redis://127.0.0.1:6379/10 \
  KOKORO_LOCAL_FAKE_MODEL=1 uv run kokoro-agent-worker

# 3. web（:3000）
cd kokoro-web
bun run dev
```

接真实模型：去掉 `KOKORO_LOCAL_FAKE_MODEL`，按 `kokoro-agent` 的
`.env` 配置 `KOKORO_MODEL` 和 provider 凭据。

## 门禁（提交前跑）

- agent: `cd kokoro-agent && uv run pytest && uv run pyright`
- agent lint: `cd kokoro-agent && uv run ruff check src tests`
- session: `cd kokoro-session && bun test && bun run typecheck && bun run lint`
- web: `cd kokoro-web && bun run test && bun run typecheck && bun run lint`
- 契约: `python3 contract/verify.py && python3 contract/generate.py --check`
- SSE 回环 e2e: `scripts/sse-loopback-gate.sh`

CI：四仓各有 `.github/workflows`（agent/session/web 各自门禁 + root 跨仓契约）。

## 可观测性

agent 执行可经 [Langfuse](https://langfuse.com) 追踪 LLM、工具和子代理。
这是 opt-in 能力：配置 `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY`
即可开启；未配置即关闭、零影响。
详见 [kokoro-agent README](kokoro-agent/README.md#可观测性langfuseopt-in)。

## 文档地图

- [`docs/requirements/`](docs/requirements/)：产品需求手册。
- [`docs/superpowers/specs/`](docs/superpowers/specs/)：工程设计 spec。
- [`docs/protocol/`](docs/protocol/)：跨仓协议契约。
- [`docs/decisions/`](docs/decisions/)：ADR 决策记录。

> 注：`docs/product/` 是原型时代的产品设计，与当前真实系统有别。
> 以 [`scope-and-boundary.md`](docs/requirements/00-product/scope-and-boundary.md)
> 的「已建 / 已设计 / 已规划」三态分界为准。
