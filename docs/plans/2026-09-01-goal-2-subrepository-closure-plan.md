# Kokoro 阶段 2：全仓库与跨仓闭环计划

日期：2026-09-01
范围：Root、Web、BFF、Agent、七个阶段 2 owner 仓库。
目标：在不重新引入废弃仓库、不跨仓复制实现、不共享业务数据库的前提下，把 Kokoro 从“契约与 mock 已对齐”推进到“真实业务链路可验收”。

## 1. 固定架构裁决

```text
kokoro-app (Web)
    -> same-origin /api/*
kokoro-bff (Chat + business BFF)
    -> explicit owner adapters
kokoro-agent (execution worker)

Goal 2 owners:
  IAM / System / Model / Billing / Capability / Storage / Scheduler
```

- Root 只保留跨仓 API 契约、Protobuf/OpenAPI 生成、拓扑索引、文档、部署入口和验证工具。
- 每个正式仓库独立维护源码、测试、Dockerfile、CI、API contract、迁移和 runbook；子仓之间只经 HTTP/OpenAPI/Protobuf/内部 command 交互。
- Web 不直连任何业务 owner、Agent、PostgreSQL 或 Redis；浏览器不提交自定义 `X-Domain` 作为信任依据。
- Chat 是 BFF 的内部业务模块；Session 是 BFF v1 API 概念，不创建独立 Session/Chat 服务。
- Credit 是 Billing 的 bounded context；Model 独立于 System；IAM 独立于 System；Scheduler 独立于 Billing。
- 正式业务仓统一 PostgreSQL + Redis。PostgreSQL 保存业务事实，Redis 只做 cache、stream、queue、lease、限流和协调；对象字节归 Storage 的 S3-compatible ObjectStore。
- 废弃的 `kokoro-session`、`kokoro-gateway`、`kokoro-platform`、旧 `kokoro-web`、独立 `kokoro-credit` 和旧 Site 不得重新加入 Root、Compose、CI、manifest 或新代码。

## 2. 仓库责任矩阵

| 仓库 | GitHub | 责任 | 当前阶段 | 下一步唯一重点 |
|---|---|---|---|---|
| `kokoro` | `LordFoxFairy/kokoro-app` | Next.js Web、同源 `/api/*`、页面状态与 SSE reducer | active | 只消费 BFF v1，补真实联调与性能证据 |
| `kokoro-bff` | `LordFoxFairy/kokoro-bff` | Chat、业务适配、鉴权、幂等、错误、SSE | active / mock 已闭环 | 用显式 adapter 替换 generic live path，保持 Web envelope 稳定 |
| `kokoro-agent` | `LordFoxFairy/kokoro-agent` | Run 执行、HITL、恢复、事件事实与 worker | active / HTTP ingress 已闭环 | 由 BFF 显式接入 Agent business port |
| `kokoro-iam` | `LordFoxFairy/kokoro-iam` | Principal、Tenant、Auth、Authorization、Audit、ExecutionIdentity | contract-first baseline | 在本仓按 API contract 分批补业务端点 |
| `kokoro-system` | `LordFoxFairy/kokoro-system` | Site、Workspace、Runtime Manifest、Policy、Release | HTTP health + control surface | 将 BFF projects/site/workspace 映射到稳定 owner ingress |
| `kokoro-model` | `LordFoxFairy/kokoro-model` | Catalog、Provider、Availability、Policy、Resolve | HTTP resolve + PG/Redis health | 暴露/固化 BFF 所需的 read adapter contract |
| `kokoro-billing` | `LordFoxFairy/kokoro-billing` | Payment、Subscription、Checkout、Refund、Credit、Ledger | Fastify routes + PG/Redis health | 对齐 BFF billing envelope、幂等和 webhook 回执 |
| `kokoro-capability` | `LordFoxFairy/kokoro-capability` | Skill、MCP Connector 控制面 | Connect RPC + health | 提供 BFF adapter 所需的 HTTP/Connect 映射与授权证据 |
| `kokoro-storage` | `LordFoxFairy/kokoro-storage` | Upload、Asset、Artifact、ObjectStore 引用 | Connect RPC + health | 接通 BFF library/upload/artifact read model |
| `kokoro-scheduler` | `LordFoxFairy/kokoro-scheduler` | Go schedule、lease、retry、misfire、pause/resume | config/dispatch worker | 固化 internal command，供 Billing/业务 owner 触发，不做公开 CRUD |

## 3. 已完成的阶段 2 基线

- Root 拓扑已只保留 10 个正式本地 Git root；仅 `kokoro-agent` 是 Root gitlink，其余正式仓库是同目录独立 checkout。
- 10 个正式仓库均已关联自己的 GitHub 仓库，当前 `origin/main` 与本地 HEAD 一致，工作树 clean；每个仓库保留独立 CI、Dockerfile 和发布文档。
- `kokoro-session`、`kokoro-gateway`、`kokoro-platform`、旧 `kokoro-web` 已在 GitHub archived；旧独立 Credit/Site 无正式远程仓，不在当前本地工作区。
- 本机旧仓源码、旧全栈 Compose、旧 k8s、旧 MySQL/Mongo 运行时和历史归档目录已清除；GitHub archived 仓库保留提交历史。
- Root contract manifest、9 个 consumer 生成物、Buf/Redocly/pytest、拓扑门禁、architecture 门禁和 Goal 2 mock closure 已通过。
- BFF mock HTTP E2E 43/43 通过；owner health 16/16、10/10 进程通过（包含 Agent HTTP ingress）；临时 PostgreSQL/Redis/ObjectStore 在 finally 清理。
- Docker 只保留当前 Model 本地开发栈的 PostgreSQL 16 + Redis 7 容器；阶段 1 生产入口仍由 Root Compose，阶段 2 owner 部署由各自仓库负责。
- 镜像发布规则已统一：普通 push/PR 只做质量门禁，`v*.*.*` tag 才触发 GHCR 生产镜像；Dockerfile 只使用生产启动命令，本地开发直接运行 `dev`。

证据索引：

- [`REPOSITORY_STATUS.md`](../REPOSITORY_STATUS.md)
- [`CODEBASE_MAP.md`](../CODEBASE_MAP.md)
- [`2026-09-01-stage2-repository-audit.md`](../reports/2026-09-01-stage2-repository-audit.md)
- [`2026-09-01-stage2-repository-closure.md`](../reports/2026-09-01-stage2-repository-closure.md)
- [`2026-09-01-stage2-bff-mock-e2e.json`](../reports/2026-09-01-stage2-bff-mock-e2e.json)
- [`2026-09-01-stage2-owner-health.json`](../reports/2026-09-01-stage2-owner-health.json)

## 4. 尚未完成的真实闭环

当前以下内容仍需真实网络证据：

1. **BFF live adapter**：`/v1/projects`、`/v1/skills`、`/v1/mcp/*`、`/v1/billing/*`、`/v1/library`、`/v1/scheduled-tasks` 和 `/v1/sessions/*` 必须分别映射到真实 owner ingress；每条映射都要有成功、错误、超时、request ID、幂等和权限测试。
2. **Agent ingress**：`kokoro-agent` 已在自身仓库提供版本化 HTTP ingress、durable admission、control、evidence 和安全 Chat history/replay，并通过本仓测试。BFF 尚未完成 live adapter 接入；接入仍必须只经 Agent business port，不读 Redis/PG。
3. **Capability/Storage RPC bridge**：Capability/Storage 当前核心入口是 Connect/RPC；BFF 需要在自己的 adapter 中使用 typed client 或经 owner 提供的 HTTP projection，不复制 proto 实现、不直连数据库。
4. **Scheduler command**：Scheduler 不拥有公开 scheduled-task CRUD；业务定义和回执归业务 owner，Scheduler 只持有通用调度与 lease。BFF 不直接访问 Scheduler/Billing 数据库。
5. **真实 Web 联调**：需要从 Web 页面出发，经过同源 API、BFF、owner、Agent/Scheduler，验证状态转换、SSE、刷新/重连、幂等重放和故障恢复，并保存逐用例报告。

## 5. 执行顺序

### Wave A：契约与入口（先接口，后 SQL）

1. Root 冻结 Web-facing v1 envelope 和 error/request-id/idempotency 规则。
2. 每个 owner 在自身仓库确定 inbound/outbound contract、权限、超时、重试和兼容矩阵；先写 contract test，再改 SQL/adapter。
3. Agent 在自身仓库先完成 HTTP ingress 与事件模型，明确 `conversation`、`run`、`event`、`control`、`share` 和 delete 语义。
4. Scheduler 在自身仓库固化 `ScheduleJob` dispatch command、occurrence identity、lease 和 execution receipt。

### Wave B：BFF 业务适配

1. 在 `kokoro-bff` 内按 owner 建立 `adapters/system`、`adapters/model`、`adapters/billing`、`adapters/capability`、`adapters/storage`、`adapters/agent` 的 typed boundary。
2. 删除或限制依赖 generic path pass-through 的 live 路由；没有 owner ingress 的路由明确返回可观测的 `upstream_not_ready`，不返回伪造成功。
3. 对 mutation 强制 durable idempotency receipt；对 SSE 使用 bounded timeout、Last-Event-ID、断线重连和上游错误映射。
4. 补 BFF live integration test：每个 adapter 使用独立 disposable owner fixture，不引用 sibling source 或数据库。

### Wave C：Web 真联调

1. `kokoro` 只配置 BFF same-origin `/api/*` 和 `KOKORO_DOMAIN`，不恢复浏览器 `X-Domain` 信任路径。
2. 走通登录/身份上下文 → 项目/Workspace → Chat/Run → Skill/MCP → Asset/Artifact → Billing/Credit → Scheduled task。
3. 验证刷新、会话切换、SSE replay、HITL、取消/恢复、删除、权限拒绝和网络错误；保存 Playwright 截图与 JSON evidence。

### Wave D：发布与部署

1. 每个 active 仓库先独立通过自身 CI、生产 build、Docker build 和 smoke。
2. 只创建 `v*.*.*` tag 验证 GHCR 发布；普通 push 不发布镜像。
3. 部署环境使用生产镜像；本地直接 `dev` 启动，生产不使用 `preview` 镜像。
4. Cloudflare/Web 入口与 BFF/owner 内网服务分离；PostgreSQL、Redis、ObjectStore、JWKS、provider 和 webhook 凭据仅由部署环境注入。

## 6. 每波验收命令

```bash
# Root gates
python3 scripts/verify-repository-topology.py
python3 scripts/verify-backend-design.py
python3 scripts/goal2/mock_cross_repository_closure.py
uv run --frozen pytest contract/tests scripts/contract/tests -q
uv run --frozen python contract/generate.py --source-root . \
  --source-commit afd367db387e11172150e64b8c5278918c47cd24 \
  --all --check --repo-map /tmp/kokoro-consumer-repo-map.json

# Cross-repository evidence
uv run --frozen python scripts/e2e/run_stage2_bff_mock.py \
  --evidence docs/reports/2026-09-01-stage2-bff-mock-e2e.json
uv run --frozen python scripts/e2e/run_stage2_owner_health.py

# Current child gates
(cd kokoro && pnpm check)
(cd kokoro-bff && pnpm check)
(cd kokoro-agent && uv run pytest && uv run pyright && uv run ruff check src tests)
(cd kokoro-iam && pnpm verify)
(cd kokoro-system && pnpm verify)
(cd kokoro-model && pnpm verify:release)
(cd kokoro-billing && pnpm verify)
(cd kokoro-capability && npm run verify)
(cd kokoro-storage && npm run verify)
(cd kokoro-scheduler && go test ./... && go test -race ./... && go vet ./...)
```

## 7. 完成定义

阶段 2 真实闭环只有同时满足以下条件才可标记完成：

- Root 与 10 个 active repositories 的本地 HEAD、GitHub `main`、CI run 和工作树状态均有记录。
- 6 个历史 GitHub 仓库仍 archived；本地不存在同名 active checkout、旧 Compose、旧 deployment 或旧基础设施容器。
- Root contract 与 7 个 owner contract 逐字节/兼容性检查通过；所有 consumer provenance 可追溯。
- BFF 每个公开 v1 route 都有显式 owner adapter 或明确的 BFF-owned Chat implementation；没有静默 generic pass-through。
- Agent、Scheduler、Capability、Storage 的真实 ingress/command 均有各自仓库内的单元、集成和 contract tests。
- Web → BFF → owner → Agent/Scheduler 的真实网络 E2E 覆盖成功、错误、权限、幂等、重试、SSE replay、故障恢复和数据隔离。
- 最终报告列出测试用例、实际命令、CI 链接、镜像/tag、部署配置和已知风险；报告状态才改为 `complete`。
