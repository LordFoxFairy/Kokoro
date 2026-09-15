# Kokoro codebase map

状态：2026-09-08 · 以 [`REPOSITORY_STATUS.md`](REPOSITORY_STATUS.md) 为仓库拓扑权威

> System 合入分支采用 [ADR-031](kokoro-handbook/decisions/ADR-031-system-http-nestjs-convergence.md)：
> 五个业务模块统一 Nest HTTP；旧 Model 不再列为活动服务，checkout/remote 保留作历史源。
> 完整 runtime/live 验收仍看 System CURRENT/IMPLEMENTATION_PLAN；`kokoro-capability` → `kokoro-platform`
> 是另一个尚未实施的重命名切换，本表不提前更名。

## Root：`Kokoro`

Root 不是业务运行时。它只保存：

- Root 不保留业务数据库 schema；各正式业务仓和 `kokoro-agent` 各自拥有唯一 canonical schema，V1 不保留历史 migration 链；旧集成 SQL fixture 已移到 Root 外历史归档；
- [`deploy/`](../deploy/)：Phase 1 三仓本地/生产入口和历史迁移夹具；
- [`docs/`](./)：跨仓架构、Developer API 门户索引、ADR、验收与报告；
- [`scripts/`](../scripts/)：当前 BFF HTTP E2E/smoke、拓扑和治理工具；不生成子仓 API。

Root 不应加入 Web、BFF、Agent 或 Goal 2 业务实现源码。

## 正式运行仓

| 仓库 | 本地目录 | 唯一职责 | 入口 |
|---|---|---|---|
| Web | `kokoro/` → `LordFoxFairy/kokoro-app` | UI、同源 `/api/*` route adapter | `kokoro/src/app/` |
| BFF | `kokoro-bff/` | Conversation/Message/Share/Project/ScheduledTask、公开 Product API、durable AG-UI projection | `kokoro-bff/src/main.ts`（组合根） |
| Agent | `kokoro-agent/` | Run/Checkpoint/Lease/Tool Journal、执行事件、HITL、Evidence | `kokoro-agent/src/kokoro_agent/` |

Web → BFF → 业务仓/Agent/Scheduler 是唯一业务调用方向。浏览器只访问 Web 同源 adapter，不直连 BFF、
Agent 或业务仓。AG-UI 是 Web/BFF 唯一 Agent 网络事件协议；Vercel AI SDK 只作 Web 内部 UI adapter。

## Goal 2 正式业务仓

本文件中的“子仓”是独立 Git 仓库，不是 Root 的普通源码目录。当前工作区把它们物理放在 `Kokoro/` 下面便于统一
导航，但每个目录都有自己的 `.git`、分支和提交边界；Root 不通过 `git add` 收纳子仓源码。跨仓变更先在事实 owner
子仓提交，再由 Root 记录拓扑或验收证据。

| 仓库 | Owner | 存储边界 | 语言 |
|---|---|---|---|
| `kokoro-iam` | Tenant/User/Auth/AuthZ/Role/Permission/Audit/ExecutionIdentity | PostgreSQL + Redis cache/coordination | TypeScript（contract-first） |
| `kokoro-system` | Sites/Workspaces/Products/Runtime Manifest/Model Catalog | PostgreSQL + Redis cache | TypeScript |
| `kokoro-billing` | Payment/Subscription/Checkout/Refund/Credit/Ledger | PostgreSQL + Redis idempotency/lease/cache | TypeScript |
| `kokoro-capability` | Skill + MCP Connector control plane | PostgreSQL + Redis admission/cache | TypeScript |
| `kokoro-storage` | Upload/Asset/Artifact metadata + ObjectStore refs | PostgreSQL + Redis + S3-compatible ObjectStore | TypeScript |
| `kokoro-scheduler` | Generic ScheduleJob/trigger/lease/retry/misfire | PostgreSQL 保存 Schedule/Occurrence/Receipt/Outbox 权威事实；Redis 仅协调 lease/通知/缓存 | Go |

Goal 2 的仓库清单和归属以 [`REPOSITORY_STATUS.md`](REPOSITORY_STATUS.md) 为准。每个业务仓库必须在本仓内完成自己的 API、Schema、实现、测试和 Docker/CI；Root 只维护拓扑、架构规则和验证入口，不发布跨仓契约。

当前九个正式运行仓只有 `kokoro-agent` 通过 Root gitlink 声明；其余活动仓仍是同目录独立 checkout。目标 `apps/` 部署容器及其 Git 路径尚未实施，当前 Web 仍位于 `kokoro/`。

本地基础设施固定复用一个 PostgreSQL 和一个 Redis。Redis logical DB：IAM=1、System=2、
Billing=4、Capability=5、Storage=6、Scheduler=7、BFF=8、Agent=9，DB 0 与退出后的 DB 3 保留空置；Web 无 Redis/数据库。

## 已归档仓

`kokoro-session`、`kokoro-gateway`、旧 `kokoro-platform`、`kokoro-web`（旧 monorepo）、`kokoro-credit` 和旧 Site
占位目录均已退出当前拓扑。ADR-029 重新采用 `kokoro-platform` 作为 Capability 的目标新名称，但不恢复历史
platform 实现。Chat 属于 BFF 内部模块；Credit 属于 Billing。

历史资料仍可在 handbook/reports 中查阅，但必须以“历史/迁移材料”理解，不能作为当前实现入口。

## 工作规则

1. 修改前先读 [`CURRENT.md`](CURRENT.md) 和本文件；
2. 变更单个子仓时只在该子仓内部闭环，不把另一个仓的源码复制进来；
3. 跨仓变更先在事实 owner 仓库更新本仓 contract，再由消费者通过本仓 typed client 或 HTTP 文档对接；
4. 普通 push/PR 只跑 CI；`v*.*.*` tag 才发布 GHCR 镜像；
5. `scripts/e2e/run_stage2_bff_mock.py` 是 Stage 2 BFF mock 入口，只通过 loopback HTTP 启动并验证 BFF，不代表完整系统 E2E；`scripts/verify-ten-repository-full.sh` 仍暂停；
6. 完成前在 Root 重新跑 topology/architecture/E2E 验证，不能只引用子代理结果。
