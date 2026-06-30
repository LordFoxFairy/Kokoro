# Kokoro（こころ）

一个有人格的通用 AI agent。主战场是把「想法」一起做成可分享的产物，气质柔、温、内观。
当前真实在跑的是**三仓 stream 聊天系统**：对话 + agent 活动流（计划 / 工具 / 子代理 / 思考），边生成边流式呈现，可中断可续传。

> 这份 README 面向新贡献者。产品需求看 [`docs/requirements/`](docs/requirements/)；架构与决策细节看 [`docs/superpowers/specs/`](docs/superpowers/specs/) 与 [`docs/decisions/`](docs/decisions/)。

## 架构一图

三层，仅经 **redis stream + SSE** 协议耦合，各自独立部署：

```
kokoro-agent ──redis run-events──▶ kokoro-session ──Mongo replay + SSE──▶ kokoro-web
 (Python worker)                    (TS session/replay 桥)                 (Next.js UI)
 产原始执行事件                       DB-first 归一化 + opaque event_id       严格解析 → eventId 去重 → append 渲染
 LangChain/DeepAgents 执行侧          Redis 只做队列与 live fanout            Last-Event-ID 使用 event_id
```

- **[kokoro-agent](kokoro-agent/)** — DeepAgents/LangChain worker，产出原始执行事件（text/tool/todo/subagent/thinking/run.*），写 redis。
- **[kokoro-session](kokoro-session/)** — 消费 → 归一化 AGUI 信封 → Mongo session_events 持久化 → SSE replay/live fan-out + `Last-Event-ID` 续订。不执行 agent，不渲染。
- **[kokoro-web](kokoro-web/)** — Next.js 聊天壳，消费 SSE，折叠成有序 thread 并渲染。

三仓统一四层 DDD：`domain`（纯实体/契约）/ `application`（编排，依赖抽象）/ `infrastructure`（redis/sse/model 实现）/ `interfaces`（worker/http/React）。上层只依赖抽象，依赖倒置。

## 跨仓契约（单源生成）

浏览器侧 AGUI/render 事件契约的**单一真理来源**是 [`contract/events.yaml`](contract/events.yaml)；
agent 原始 wire 事件的单一真理来源是 [`kokoro-agent/src/kokoro_agent/interfaces/envelope.py`](kokoro-agent/src/kokoro_agent/interfaces/envelope.py)。

- `python3 contract/generate.py` —— 从 `events.yaml` 生成 session/web AGUI 镜像，并从 agent `envelope.py` 生成 session 入站 Zod 镜像。**镜像文件带 `DO NOT EDIT` 头；改契约后必须重生成。**
- `python3 contract/generate.py --check` —— CI 门禁：yaml 改了忘重生成即非零退出。
- `python3 contract/verify.py` —— 名集漂移门禁（与 --check 互补）。

详见 [契约 codegen 设计](docs/superpowers/specs/2026-06-14-contract-codegen-design.md)。

## 本地起栈（开发）

前置：`redis`、`uv`（Python）、`bun`（TS）。**用隔离的 redis db（如 db10），别碰生产 db0。**

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

接真实模型：去掉 `KOKORO_LOCAL_FAKE_MODEL`，按 `kokoro-agent` 的 `.env`（`KOKORO_MODEL` + provider 凭据）配置。

## 门禁（提交前跑）

| 层 | 命令 |
|---|---|
| agent | `cd kokoro-agent && uv run pytest && uv run pyright && uv run ruff check src tests` |
| session | `cd kokoro-session && bun test && bun run typecheck && bun run lint` |
| web | `cd kokoro-web && bun run test && bun run typecheck && bun run lint` |
| 契约 | `python3 contract/verify.py && python3 contract/generate.py --check` |
| SSE 回环 e2e | `scripts/sse-loopback-gate.sh`（需 redis + session + 假模型 worker） |

CI：四仓各有 `.github/workflows`（agent/session/web 各自门禁 + root 跨仓契约）。

## 可观测性

agent 执行可经 [Langfuse](https://langfuse.com) 追踪(LLM/工具/子代理),**opt-in**:配
`LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY`(+ 自托管设 `LANGFUSE_HOST`)即开,未配置即关、零影响。
详见 [kokoro-agent README](kokoro-agent/README.md#可观测性langfuseopt-in)。

## 文档地图

| 目录 | 内容 |
|---|---|
| [`docs/requirements/`](docs/requirements/) | 产品需求手册（愿景 → 能力 → 流程 → 契约映射，可验收） |
| [`docs/superpowers/specs/`](docs/superpowers/specs/) | 工程设计 spec（stream 架构 / 测试总目录 / codegen / 连续性 / 质量评估） |
| [`docs/protocol/`](docs/protocol/) | 跨仓协议契约 |
| [`docs/decisions/`](docs/decisions/) | ADR 决策记录 |

> 注：`docs/product/` 是**原型时代**的产品设计（canvas 创作矩阵，仅静态原型），与当前真实系统有别——以 [`docs/requirements/00-product/scope-and-boundary.md`](docs/requirements/00-product/scope-and-boundary.md) 的「已建 / 已设计 / 已规划」三态分界为准。
