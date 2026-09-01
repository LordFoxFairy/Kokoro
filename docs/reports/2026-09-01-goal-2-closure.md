# Goal 2：七个正式子仓库闭环对齐报告

日期：2026-09-01

## 最终运行时子仓库

| 子仓库 | Owner 边界 | 运行时事实源 |
|---|---|---|
| `kokoro-iam` | 用户、Tenant、认证、授权、Role/Permission、OAuth、Passkey、审计、ExecutionIdentity | PostgreSQL + Redis 短 TTL/限流/协调 |
| `kokoro-system` | Site、Workspace、Runtime Manifest、系统配置和站点策略 | PostgreSQL + Redis cache/协调 |
| `kokoro-model` | Model Catalog、Provider、Availability、模型能力公开契约 | PostgreSQL + Redis cache/协调 |
| `kokoro-billing` | Payment、Subscription、Checkout、Refund、Credit、Ledger | PostgreSQL + Redis lease/cache/idempotency hint |
| `kokoro-capability` | Skill 与 MCP Connector 子域的 catalog、安装、启停、版本、权限 | PostgreSQL + Redis；包体经 Storage API |
| `kokoro-storage` | File、Upload、Artifact、ObjectStore、Download、生命周期 | PostgreSQL metadata + S3-compatible ObjectStore + Redis |
| `kokoro-scheduler` | 通用 ScheduleJob、触发、租约、并发、重试、退避、pause/resume、misfire、回执 | Go + Redis coordination；业务回执由目标业务仓库拥有 |

`Connector` 收敛为 Capability 内的 MCP 子域；Agent 负责 live MCP session/handshake/invoke。Credit 已合并进
Billing；Chat 保留在 BFF 内部；不新增 `kokoro-platform`、`kokoro-gateway`、Chat/Session 业务实现。

## Manus API 参考核对

本轮按 Manus 官方 API v2 文档做了设计核对：
[Introduction](https://open.manus.im/docs/v2/introduction)、
[task.list](https://open.manus.im/docs/v2/task.list)、
[task.listMessages](https://open.manus.im/docs/v2/task.listMessages) 和
[Task Lifecycle](https://open.manus.im/docs/v2/task-lifecycle)。吸收的只有成熟的通用模式：
版本化 surface、稳定 opaque ID、统一 `ok/request_id/error` envelope、`has_more/next_cursor`
游标以及异步执行的状态/事件读取边界。Kokoro 不复制 Manus 的 URL、Token、OAuth、字段或业务
资源：Kokoro 仍使用 Root `ErrorDetail`、IAM-derived trusted service context、标准
`Forwarded`、`x-kokoro-request-id` 和 `Idempotency-Key`，Model/Capability/Storage/Billing/
Scheduler 继续按各自 owner 边界实现。

## 本轮落地

- 七仓均补齐本仓 API contract、资源模型/状态机、运行说明、BFF 接入说明、验收说明和风险记录。
- 七仓统一遵守 PostgreSQL + Redis 基线；Scheduler v1 是配置驱动服务，仅在多实例时使用 Redis lease，
  不伪造业务 PostgreSQL schema；Storage 的对象字节不进入 PostgreSQL，使用 S3-compatible ObjectStore。
- 根仓新增 `contract/goal2-repository-contract-manifest.json`，登记七个 owner、Root wire 文件、
  owner API/技术/接入/验收/风险文档，并由 `scripts/goal2/mock_cross_repository_closure.py` 校验。
- IAM 增加 PostgreSQL lock bucket seed、实时 replay authorization、PostgreSQL integration 修复和启动 readiness。
- Billing 增加 PostgreSQL mixed-placeholder normalization、provider-scoped external identity、tenant lineage
  FK、PostgreSQL JSONB/锁语义和全量 integration 修复；Credit 保持 Billing 内部 bounded context。
- Scheduler 使用 Go，显式实现 retry/backoff、misfire、pause/resume、request_id 和 Idempotency-Key 传递。
- Root contract 继续作为跨仓 wire authority；各仓只保留本仓实现契约和 generated/client facade。

## Mock 跨仓联调

```bash
python3 scripts/goal2/mock_cross_repository_closure.py
pnpm contract:format
pnpm contract:lint
pnpm contract:check
```

Mock fixture 覆盖 BFF→IAM/System/Model/Billing/Capability/Storage、Capability→Storage artifact ref 和
Billing→Scheduler generic task 边界；验证 request_id、幂等、cursor 和数据库不共享标记。

## 验收结果

- `kokoro-iam`：PG18 + Redis fixture 下 `pnpm test`：63 files passed、225 tests passed、1 contract shutdown test skipped（显式 opt-in）。`pnpm typecheck`、`pnpm lint`、`pnpm build`、`pnpm proto:check` 通过。
- `kokoro-system`：typecheck/lint/test/build、SDK 三项通过；8 files/28 tests，SDK 11 tests；真实 `runtime-smoke` PASS（tenant isolation、precedence、cache identity、HTTP errors）。
- `kokoro-model`：contract/typecheck/lint/architecture/unit/build/standalone 通过；125 unit tests、1 architecture test；
  fresh PostgreSQL migration 下 6 个 integration files/33 tests 通过；真实 PostgreSQL 与 Redis smoke PASS。
- `kokoro-billing`：lint/typecheck/build/SQL/OpenAPI 通过；58 个无依赖 unit/http/architecture tests，52 个带本地依赖的 integration tests 全部通过，含真实 PostgreSQL migration 和 Redis lease/idempotency。
- `kokoro-capability`：contract/typecheck/test/lint/build 通过；26 files/114 tests。
- `kokoro-storage`：contract/typecheck/test/lint/build 通过；21 files/69 tests。
- `kokoro-scheduler`：`gofmt`、`go test ./...`、`go test -race ./...`、`go vet ./...`、`go build ./cmd/scheduler` 和启动检查通过。
- `kokoro-bff`（只读联调验收，未修改）：`pnpm check` 通过，18 个 v1 mock contract subtests 通过。

真实启动验收覆盖 IAM、System、Model、Billing、Capability、Storage、Scheduler：各服务的
health/readiness 或空配置启停 fixture 均通过；其中 Model、Billing 使用 fresh PostgreSQL
migration + Redis，Capability/Storage 使用同一轮 PostgreSQL + Redis + local ObjectStore
边界 fixture。该结果证明 owner runtime 可以独立启动并满足依赖 readiness，不把它表述为生产
环境密钥、provider 或外部 ObjectStore 的验收。

## 未完成项与风险

1. BFF/Web/Agent 的七仓真实网络编排尚未作为本 Goal 的写入项；本轮提供的是 Root contract + owner mock gate，
   并对现有 BFF v1 做了只读 `pnpm check` 验收，不修改 BFF/Web/Agent。
2. 生产 PostgreSQL/Redis/S3 endpoint、密钥、JWKS 和 provider webhook secret 仍由部署环境注入；本地 fixture 不替代生产 secret。
3. IAM shutdown contract test 默认跳过，需在 CI 的真实 listener lifecycle 环境中以 `IAM_RUN_SHUTDOWN_TESTS=1` 单独验收。
4. Root 既有 `docker-compose.app.yml` 的历史基础设施配置未作为业务实现目标修改；七个目标仓的运行说明已不引用 MySQL/Mongo。
