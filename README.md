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
- **[kokoro-bff](kokoro-bff/)** — Web-facing Chat 与业务 BFF，负责会话/消息/SSE/control/share、鉴权、幂等、错误归一和上游 adapter；运行模式为 live。
- **[kokoro](kokoro/)** — 独立 Web 子仓库，浏览器只访问同源 `/api/*`，Chat 统一转到 BFF。

阶段 2 的正式业务拓扑见 [`docs/REPOSITORY_STATUS.md`](docs/REPOSITORY_STATUS.md)：Chat 位于 `kokoro-bff 的 Chat 内部业务边界`，Credit 位于 `kokoro-billing`；不再维护独立 Session、Gateway、Platform、Credit 或旧 Web monorepo。基础设施统一为 PostgreSQL + Redis，Storage 对象字节使用 S3-compatible ObjectStore。

架构按仓库形态收敛：每个正式仓库独立测试、构建、Docker、CI 和本仓 API contract；Root 只维护架构决策、仓库地图、部署编排和验证入口，不复制任何子仓源码或 API 定义。

### Root 与子仓的目录关系

当前目录名为 `Kokoro` 的仓库是**工作区/治理 Root**，不是把所有服务源码合并在一起的单一 monorepo。目录下面的
`kokoro/`、`kokoro-iam/`、`kokoro-bff/` 等目录各自拥有独立的 `.git`、分支、提交、依赖、构建和发布边界：

```text
Kokoro/                         # Root：拓扑、规范、任务板、编排
  kokoro/                       # 独立 Web 仓
  kokoro-iam/                   # 独立 IAM 仓；当前 canonical 工作目录
  kokoro-bff/                   # 独立 BFF 仓
  kokoro-agent/                 # 当前由 Root 以 git submodule 记录
  ...
```

因此，`Kokoro/kokoro-iam` 在文件系统上位于 Root 下面，但 Root 不直接跟踪它的源码；修改 IAM 时必须进入
`Kokoro/kokoro-iam` 自己的 Git 仓提交，Root 只记录跨仓拓扑和验收事实。Agent 临时 worktree 以及工作区外的同名 clone
不属于当前 canonical 工作目录，不能与当前 IAM 分支混用。

## 契约归属

Root 不保存跨仓 API、Proto、OpenAPI、JSON Schema 或生成器。每个运行仓库只维护自己拥有的边界：

- `kokoro`：Web 同源 API 与 AG-UI 客户端解析契约；
- `kokoro-bff`：公开 BFF v1、Chat、SSE 与 AG-UI 投影契约；
- `kokoro-agent`：Agent ingress、Redis command/event protocol 与执行事实契约；
- `kokoro-iam`、`kokoro-system`（含 model-catalog）、`kokoro-billing`、`kokoro-capability`、
  `kokoro-storage`、`kokoro-scheduler`：分别维护各自 owner 的 API、Schema、测试和发布配置。

Root 的验证脚本只检查仓库拓扑、文档索引和 loopback E2E，不定义或生成子仓协议。跨仓变更在相关 owner 仓库内完成，
再由消费者通过本仓 typed client 或 HTTP contract 对接。

## 本地起栈（开发）

前置：`postgres`、`redis`、`uv`（Python）、`pnpm`（TS）。本地只复用一个 PostgreSQL 和一个 Redis；
各服务使用固定的 Redis logical DB（Agent=9、BFF=8、IAM=1、System=2、Billing=4、
Capability=5、Storage=6、Scheduler=7），DB0/已退出 Model 的 DB3 保留空置。验证脚本会探测并复用已有依赖，不会重复启动容器。

各仓环境变量先按本仓 README 配置；System 与 BFF 分别使用 Node 24 和 Node 22，不复用业务数据库。

```bash
# System 控制面（站点/产品配置及模型目录）；另开终端
cd kokoro-system && pnpm dev

# BFF（已配置自身数据库、Redis、服务凭据与 System URL）；另开终端
cd kokoro-bff && pnpm dev

# 可选 Agent worker；先配置下述 System/LiteLLM 及 Agent 自有 PG/Redis
cd kokoro-agent && uv run kokoro-agent-worker

# Web；另开终端
cd kokoro && pnpm dev
```

三仓容器方式默认只启动 Web+BFF；需要完整执行时再按 [`deploy/README.md`](deploy/README.md) 开启 Agent
profile，同时启动 HTTP ingress 和 worker。`cp deploy/.env.phase1.example deploy/.env.phase1.local`，填入
PostgreSQL 密码后执行 `bash deploy/provision-phase1.sh deploy/.env.phase1.local`。生产部署只使用生产镜像；Cloudflare 直连 Web 或
Docker 部署均通过 `KOKORO_DOMAIN` 和 BFF runtime env 配置，不把数据库连接放进浏览器。

Root 当前只保留这条 Phase 1 Compose/provision 入口；阶段 2 六个正式业务仓由各自仓库发布，BFF 通过各 owner 仓库的本地 v1 contract 接入，不从 Root Compose 拼接业务实现。

模型目录与路由统一归 `kokoro-system/modules/model-catalog`，只提供元数据，不执行推理。
Agent worker 通过 System HTTP resolve 选择模型；启动执行链需配置 `KOKORO_SYSTEM_BASE_URL`、
`KOKORO_INTERNAL_SECRET_AGENT` 和 LiteLLM 的 enabled/base-url/api-key。没有本地默认模型 fallback。
LiteLLM 仍是外部网关，不打包进 System 或 Agent 镜像；Web+BFF 不执行任务时可不启动它。
旧 `kokoro-model` checkout/remote 保留作为历史源，不再从 active clone/运行/镜像清单启动。
System 合入的完整 runtime 验收状态见 [System CURRENT](kokoro-system/docs/CURRENT.md)，不以本入口替代证据。

## 门禁（提交前跑）

| 层 | 命令 |
|---|---|
| agent | `cd kokoro-agent && uv run pytest && uv run pyright && uv run ruff check src tests` |
| bff | `cd kokoro-bff && pnpm check` |
| web | `cd kokoro && pnpm check` |
| 契约 | 在对应 owner 仓库运行本仓 `contract:check`、类型检查和 contract tests |
| Chat mock smoke | `KOKORO_WEB_URL=http://127.0.0.1:3000 KOKORO_DOMAIN=dev.kokoro.localhost pnpm --dir kokoro smoke:first-site` |
| Stage 2 BFF HTTP E2E | `uv run --frozen python scripts/e2e/run_stage2_bff_mock.py --evidence /tmp/kokoro-stage2-bff-mock-e2e.json` |
| System 跨仓隔离 smoke | `python3 scripts/e2e/run_system_owner_smoke.py --help`（配置共享端点及各 Node 路径后执行） |

旧 owner-health/full runner 已暂停：危险的共享状态清理实现已移出工作区，原命令只输出
`VERIFICATION_ENTRY_PAUSED` 并退出 2，不访问基础设施。旧跳过/清理参数已失效。
Root 后续负责重建隔离的九仓完整编排；当前逐仓执行各 owner 自有门禁。System 跨仓验收使用上面的独立 smoke，
不把它计作全仓浏览器、外部存储、真实推理或候选镜像的发布证据。

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
| 各 owner 仓 `contract/` | 版本化协议事实源；Root 不另建协议中心 |
| [`docs/decisions/`](docs/decisions/) | ADR 决策记录 |

> 注：`docs/product/` 是**原型时代**的产品设计（canvas 创作矩阵，仅静态原型），与当前真实系统有别——以 [`docs/requirements/00-product/scope-and-boundary.md`](docs/requirements/00-product/scope-and-boundary.md) 的「已建 / 已设计 / 已规划」三态分界为准。
