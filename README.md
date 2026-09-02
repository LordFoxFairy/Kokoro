# Kokoro（こころ）

一个有人格的通用 AI agent。主战场是把「想法」一起做成可分享的产物，气质柔、温、内观。
当前阶段 1 的真实闭环是 **kokoro Web + kokoro-bff + kokoro-agent**：Web 只负责界面与同源代理，BFF 负责 Chat/业务编排，Agent 负责 Run 执行、HITL、恢复和 worker。对话 + agent 活动流边生成边呈现，可中断可续传。

> 这份 README 面向新贡献者。稳定总设计先看 [`docs/kokoro-handbook/`](docs/kokoro-handbook/)；
> 仓库与文档归属看 [`docs/REPOSITORY_STATUS.md`](docs/REPOSITORY_STATUS.md) 和 [`docs/CODEBASE_MAP.md`](docs/CODEBASE_MAP.md)；过程方案看
> [`docs/superpowers/specs/`](docs/superpowers/specs/)。

## 架构一图

三仓，经 **BFF Chat v1 + Redis transport + PostgreSQL durable facts + SSE** 协议耦合，各自独立部署：

```
kokoro-agent ──business/transport contract──▶ kokoro-bff ──same-origin v1──▶ kokoro Web
 (Python worker)                              (Node BFF Chat/业务层)          (Next.js UI)
 PostgreSQL 执行事实 + Redis worker          鉴权/幂等/错误/SSE/业务投影        严格解析 → reducer → 渲染
 Run/control/HITL/recovery                    `/v1/sessions/*`                  `/api/session/*`
```

- **[kokoro-agent](kokoro-agent/)** — DeepAgents/LangChain worker，产出安全执行事实（text/tool/todo/subagent/thinking/run.*），写 PostgreSQL；Redis 只承担 worker stream、lease、recovery 和 wakeup。
- **[kokoro-bff](kokoro-bff/)** — Web-facing Chat 与业务 BFF，负责会话/消息/SSE/control/share、鉴权、幂等、错误归一和上游 adapter；阶段 1 默认 mock。
- **[kokoro](kokoro/)** — 独立 Web 子仓库，浏览器只访问同源 `/api/*`，Chat 统一转到 BFF。

阶段 2 的正式业务拓扑见 [`docs/REPOSITORY_STATUS.md`](docs/REPOSITORY_STATUS.md)：Chat 位于 `kokoro-bff 的 Chat 内部业务边界`，Credit 位于 `kokoro-billing`；不再维护独立 Session、Gateway、Platform、Credit 或旧 Web monorepo。基础设施统一为 PostgreSQL + Redis，Storage 对象字节使用 S3-compatible ObjectStore。

架构按仓库形态收敛：每个正式仓库独立测试、构建、Docker 与 CI；Root 只维护契约、文档、部署和跨仓验证，不复制任何子仓源码。

## 跨仓契约（单源生成）

Slice A 的**单一机器真源**是 [`contract/slice-a-contract-manifest.yaml`](contract/slice-a-contract-manifest.yaml)。Root 从它确定性生成九份 Protobuf、Web BFF OpenAPI，并按 [`contract/consumers.yaml`](contract/consumers.yaml) 为每个子仓生成最小 Connect/gRPC closure。

- `uv run python scripts/contract/render_slice_a.py --manifest contract/slice-a-contract-manifest.yaml --check` —— 校验 Proto/OpenAPI 与机器真源逐字节一致。
- `pnpm exec buf lint contract && pnpm exec buf breaking contract --against contract/breaking/slice-a-v1.binpb` —— Protobuf lint/breaking 门禁。
- `pnpm exec redocly lint contract/openapi/slice-a-web-v1.yaml` —— 浏览器 HTTP/SSE contract 门禁。
- `uv run python contract/generate.py --source-root ROOT --source-commit SHA --consumer NAME --repo PATH --check` —— 从指定 clean Root commit 校验一个 consumer；无隐式当前目录或浮动 source。
- `uv run --frozen python scripts/e2e/run_stage2_bff_mock.py --evidence /tmp/kokoro-stage2-bff-mock-e2e.json` —— 启动真实 BFF 子仓进程，以 mock 数据闭环验证当前 Web-facing Business API v1。

旧 `contract/spec/*.yaml` 已在事件/control payload parity 证明后硬删除，不再形成第二权威。

## 本地起栈（开发）

前置：`postgres`、`redis`、`uv`（Python）、`pnpm`（TS）。**用隔离的 Redis db（如 db10），别碰生产 db0。**

```bash
# 1. 可选：agent worker（PostgreSQL durable facts + Redis transport）
cd kokoro-agent
KOKORO_REDIS_URL=redis://127.0.0.1:6379/10 \
  KOKORO_AGENT_DATABASE_URL=postgresql://kokoro:CHANGE_ME@127.0.0.1:5432/kokoro \
  uv run kokoro-agent-worker

# 2. BFF Chat（:4300，阶段 1 mock）
cd kokoro-bff
KOKORO_BFF_MODE=mock KOKORO_BFF_HOST=127.0.0.1 pnpm dev

# 3. Web（:3000）
cd kokoro
pnpm dev
```

三仓容器方式默认只启动 Web+BFF；需要完整执行时再按 [`deploy/README.md`](deploy/README.md) 开启 Agent
profile，同时启动 HTTP ingress 和 worker。`cp deploy/.env.phase1.example deploy/.env.phase1.local`，填入
PostgreSQL 密码后执行 `bash deploy/provision-phase1.sh deploy/.env.phase1.local`。生产部署只使用生产镜像；Cloudflare 直连 Web 或
Docker 部署均通过 `KOKORO_DOMAIN` 和 BFF runtime env 配置，不把数据库连接放进浏览器。

Root 当前只保留这条 Phase 1 Compose/provision 入口；阶段 2 七个正式业务仓由各自仓库发布，BFF 通过 Root
contract 接入，不从 Root Compose 拼接业务实现。

模型服务 `kokoro-model` 独立提供目录与解析，不执行 provider 调用；LiteLLM 是可选的外部
OpenAI-compatible gateway。Agent 默认不启用 LiteLLM，只有同时设置 `KOKORO_LITELLM_ENABLED=1`、
`KOKORO_LITELLM_BASE_URL`、`KOKORO_LITELLM_API_KEY` 时才使用对应 route。

## 门禁（提交前跑）

| 层 | 命令 |
|---|---|
| agent | `cd kokoro-agent && uv run pytest && uv run pyright && uv run ruff check src tests` |
| bff | `cd kokoro-bff && pnpm check` |
| web | `cd kokoro && pnpm check` |
| 契约 | `uv run python scripts/contract/render_slice_a.py --manifest contract/slice-a-contract-manifest.yaml --check && pnpm exec buf lint contract && pnpm exec buf breaking contract --against contract/breaking/slice-a-v1.binpb && pnpm exec redocly lint contract/openapi/slice-a-web-v1.yaml` |
| Chat mock smoke | `KOKORO_WEB_URL=http://127.0.0.1:3000 KOKORO_DOMAIN=dev.kokoro.localhost pnpm --dir kokoro smoke:first-site` |
| Stage 2 BFF HTTP E2E | `uv run --frozen python scripts/e2e/run_stage2_bff_mock.py --evidence /tmp/kokoro-stage2-bff-mock-e2e.json` |
| Stage 2 owner health | `uv run --frozen python scripts/e2e/run_stage2_owner_health.py` |

CI：正式仓库各自维护 `.github/workflows`；普通 push/PR 只做质量检查，`v*.*.*` tag 才触发 GHCR 生产镜像发布。

## 可观测性

agent 执行可经 [Langfuse](https://langfuse.com) 追踪(LLM/工具/子代理),**opt-in**:配
`LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY`(+ 自托管设 `LANGFUSE_HOST`)即开,未配置即关、零影响。
详见 [kokoro-agent README](kokoro-agent/README.md#可观测性langfuseopt-in)。

## 文档地图

| 目录 | 内容 |
|---|---|
| [`docs/kokoro-handbook/`](docs/kokoro-handbook/) | 跨仓权威手册：产品、技术、模块、业务链路、运营、ADR |
| [`docs/CODEBASE_MAP.md`](docs/CODEBASE_MAP.md) | 根仓/子仓地图、文档归属、验证入口、并行派工上下文 |
| [`docs/REPOSITORY_STATUS.md`](docs/REPOSITORY_STATUS.md) | 正式仓库、GitHub 映射、归属和归档清单 |
| [`docs/requirements/`](docs/requirements/) | 产品需求手册（愿景 → 能力 → 流程 → 契约映射，可验收） |
| [`docs/superpowers/specs/`](docs/superpowers/specs/) | 有日期的工程设计 spec；稳定后要沉淀回 handbook |
| [`docs/handoffs/`](docs/handoffs/) | 短期派工交接稿，不是长期权威 |
| [`docs/protocol/`](docs/protocol/) | 跨仓协议契约 |
| [`docs/decisions/`](docs/decisions/) | ADR 决策记录 |

> 注：`docs/product/` 是**原型时代**的产品设计（canvas 创作矩阵，仅静态原型），与当前真实系统有别——以 [`docs/requirements/00-product/scope-and-boundary.md`](docs/requirements/00-product/scope-and-boundary.md) 的「已建 / 已设计 / 已规划」三态分界为准。
