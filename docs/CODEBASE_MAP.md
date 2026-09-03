# Kokoro codebase map

状态：2026-09-02 · 以 [`REPOSITORY_STATUS.md`](REPOSITORY_STATUS.md) 为仓库拓扑权威

## Root：`Kokoro`

Root 不是业务运行时。它只保存：

- Root 不保留业务数据库 schema；各正式业务仓和 `kokoro-agent` 各自拥有唯一 canonical schema，V1 不保留历史 migration 链；旧集成 SQL fixture 已移到 Root 外历史归档；
- [`deploy/`](../deploy/)：Phase 1 三仓本地/生产入口和历史迁移夹具；
- [`docs/`](./)：跨仓架构、API 索引、ADR、验收与报告；
- [`scripts/`](../scripts/)：当前 BFF HTTP E2E/smoke、拓扑和治理工具；不生成子仓 API。

Root 不应加入 Web、BFF、Agent 或 Goal 2 业务实现源码。

## 正式运行仓

| 仓库 | 本地目录 | 唯一职责 | 入口 |
|---|---|---|---|
| Web | `kokoro/` → `LordFoxFairy/kokoro-app` | UI、同源 `/api/*` route adapter | `kokoro/src/app/` |
| BFF | `kokoro-bff/` | Chat 与业务 BFF、鉴权/幂等/错误归一 | `kokoro-bff/src/main.ts`（组合根）、`kokoro-bff/src/http/routes/` |
| Agent | `kokoro-agent/` | Worker 执行、HITL、恢复、产品事件投影 | `kokoro-agent/src/kokoro_agent/worker/` |

Web → BFF → 业务仓是唯一业务调用方向。浏览器不直连 BFF、Agent 或业务仓。

## Goal 2 正式业务仓

| 仓库 | Owner | 存储边界 | 语言 |
|---|---|---|---|
| `kokoro-iam` | Tenant/User/Auth/AuthZ/Role/Permission/Audit/ExecutionIdentity | PostgreSQL + Redis cache/coordination | TypeScript（contract-first） |
| `kokoro-system` | Site/Workspace/Runtime Manifest/System Config/Policy | PostgreSQL + Redis cache | TypeScript |
| `kokoro-model` | Model Catalog/Provider/Availability/Policy | PostgreSQL + Redis cache/invalidation | TypeScript |
| `kokoro-billing` | Payment/Subscription/Checkout/Refund/Credit/Ledger | PostgreSQL + Redis idempotency/lease/cache | TypeScript |
| `kokoro-capability` | Skill + MCP Connector control plane | PostgreSQL + Redis admission/cache | TypeScript |
| `kokoro-storage` | Upload/Asset/Artifact metadata + ObjectStore refs | PostgreSQL + Redis + S3-compatible ObjectStore | TypeScript |
| `kokoro-scheduler` | Generic ScheduleJob/trigger/lease/retry/misfire | Optional Redis occurrence lease; no business DB | Go |

Goal 2 的仓库清单和归属以 [`REPOSITORY_STATUS.md`](REPOSITORY_STATUS.md) 为准。每个业务仓库必须在本仓内完成自己的 API、Schema、实现、测试和 Docker/CI；Root 只维护拓扑、架构规则和验证入口，不发布跨仓契约。

## 已归档仓

`kokoro-session`、`kokoro-gateway`、`kokoro-platform`、`kokoro-web`（旧 monorepo）、`kokoro-credit` 和旧 Site 占位目录均已退出当前拓扑。Chat 属于 BFF 内部模块；Credit 属于 Billing；不再创建这些独立业务仓。

历史资料仍可在 handbook/reports 中查阅，但必须以“历史/迁移材料”理解，不能作为当前实现入口。

## 工作规则

1. 修改前先读 [`CURRENT.md`](CURRENT.md) 和本文件；
2. 变更单个子仓时只在该子仓内部闭环，不把另一个仓的源码复制进来；
3. 跨仓变更先在事实 owner 仓库更新本仓 contract，再由消费者通过本仓 typed client 或 HTTP 文档对接；
4. 普通 push/PR 只跑 CI；`v*.*.*` tag 才发布 GHCR 镜像；
5. 当前跨仓 E2E 入口是 `scripts/e2e/run_stage2_bff_mock.py`，只通过 loopback HTTP 启动并验证 BFF，不复制子仓源码；
6. 完成前在 Root 重新跑 topology/architecture/E2E 验证，不能只引用子代理结果。
