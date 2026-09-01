# Billing Repository / Service 分层加固实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在不改变当前 Billing API 和账务语义的前提下，把 `kokoro-billing` 从“模块内直接 SQL service”渐进收敛为可验证的 DDD + Hexagonal 模块化单体，并为套餐/积分/Promotion/Redeem 扩展提供稳定边界。

**Architecture:** 一个 Git repository 保持 Payment 与 Entitlement 两个 bounded context；API、Payment Worker、Credit Sweeper、Migrator 是独立 runtime process。Application handlers 编排事务和用例，Domain 保存规则，Repository ports 隔离持久化，MySQL adapters 持有 SQL，Redis/Provider 只通过 infrastructure adapters 接入。

**Tech Stack:** Node.js 22、TypeScript、Fastify、MySQL 8.4、Redis 7、mysql2、Zod、Vitest、OpenAPI、Prometheus。

## Global Constraints

- MySQL 是余额、grant、hold、journal、settlement、redemption 和 command receipt 的最终事实源。
- Redis 只作 hint、短租约、缓存和协调，不作最终锁、余额、兑换次数或幂等事实。
- 所有跨租户 FK 和 mutation 查询必须包含 `site_id`；外部 API 使用 `tenantId`。
- Payment 不直接写 Entitlement/Credit 表；跨 bounded context 只用 application port、source fact 和 outbox。
- 不引入第二个数据库、Kafka、通用 Repository<T> 或每张表一个微服务。
- 每个 vertical slice 必须通过 lint、typecheck、OpenAPI、unit、真实 MySQL/Redis integration 和 architecture tests。

## Task 1: 建立架构边界测试与事务 port

**Files:**
- Create: `kokoro-billing/src/bounded-contexts/entitlement/application/ports/billing-unit-of-work.ts`
- Create: `kokoro-billing/src/bounded-contexts/entitlement/application/ports/repositories.ts`
- Create: `kokoro-billing/src/bounded-contexts/payment/application/ports/repositories.ts`
- Create: `kokoro-billing/test/architecture/import-boundaries.test.ts`
- Modify: `kokoro-billing/tsconfig.json`

**Interfaces:**
- `BillingUnitOfWork.run<T>(task: (tx: BillingTransaction) => Promise<T>): Promise<T>`。
- Ports 只暴露 aggregate/fact 业务操作，不暴露 SQL、mysql2 packet 或 Redis client。

- [ ] **Step 1:** 为禁止 import 关系写 architecture test：domain/application 不能 import `mysql2`、`redis`、`fastify`；interfaces 不能包含 SQL；Payment 不能 import Entitlement concrete repository。
- [ ] **Step 2:** 运行 `pnpm exec vitest run test/architecture --no-file-parallelism`，确认旧结构按预期标记为待迁移，而不是静默绕过。
- [ ] **Step 3:** 新增 UoW port 与 MySQL adapter 的最小实现，复用现有 `connection.ts` transaction context。
- [ ] **Step 4:** 运行 `pnpm typecheck && pnpm lint && pnpm test`。

## Task 2: 迁移 Credit mutation vertical slice

**Files:**
- Create: `kokoro-billing/src/bounded-contexts/entitlement/domain/credit/credit-grant.ts`
- Create: `kokoro-billing/src/bounded-contexts/entitlement/domain/credit/credit-hold.ts`
- Create: `kokoro-billing/src/bounded-contexts/entitlement/application/commands/authorize-usage-handler.ts`
- Create: `kokoro-billing/src/bounded-contexts/entitlement/infrastructure/mysql/credit-grant-repository.ts`
- Create: `kokoro-billing/src/bounded-contexts/entitlement/infrastructure/mysql/credit-hold-repository.ts`
- Modify: `kokoro-billing/src/modules/metering/usage-settlement-service.ts`
- Test: `kokoro-billing/test/domain/credit/*.test.ts`
- Test: `kokoro-billing/test/integration/usage-settlement.test.ts`

**Interfaces:**
- `CreditGrantRepository.listEligibleForUpdate(...)` returns deterministic grant lots.
- `CreditHoldRepository.create/lock/capture/release(...)` enforces one-way status transitions.
- `AuthorizeUsageHandler.execute(command)` returns an opaque hold reference and frozen price reference.

- [ ] **Step 1:** 把 grant allocation 顺序、hold 状态和 amount invariants 写成 domain tests。
- [ ] **Step 2:** 将当前 SQL 移到 repository adapter，并让 handler 通过 UoW 调用 ports。
- [ ] **Step 3:** 保留现有 HTTP DTO 和 error codes，只替换 composition root wiring。
- [ ] **Step 4:** 运行 usage、Redis outage、lease 和 reconciliation integration tests。

## Task 3: 设计并实现 Package/Promotion/Redeem slice

**Files:**
- Create: `kokoro-billing/src/bounded-contexts/entitlement/domain/catalog/package-revision.ts`
- Create: `kokoro-billing/src/bounded-contexts/entitlement/domain/promotion/promotion-eligibility.ts`
- Create: `kokoro-billing/src/bounded-contexts/entitlement/domain/redeem/redeem-code.ts`
- Create: `kokoro-billing/src/bounded-contexts/entitlement/application/commands/redeem-code-handler.ts`
- Create: `kokoro-billing/src/bounded-contexts/entitlement/application/commands/quote-checkout-handler.ts`
- Create: `kokoro-billing/src/bounded-contexts/entitlement/infrastructure/mysql/redeem-code-repository.ts`
- Create: `kokoro-billing/database/migrations/0030-package-benefit-redeem-foundation.sql`
- Create: `kokoro-billing/contract/openapi/billing-v2-redeem.yaml`
- Create: `kokoro-billing/test/domain/redeem/*.test.ts`
- Create: `kokoro-billing/test/integration/redeem/*.test.ts`

**Interfaces:**
- `RedeemCodeHandler.execute({ tenantId, subject, normalizedCode, idempotencyKey })` performs one MySQL transaction and returns `redemptionId` plus benefit summary.
- `PromotionEligibility.evaluate(context, promotionSnapshot)` is pure and deterministic.
- Code repository stores HMAC hash only; no plaintext code enters SQL/logs/events.

- [ ] **Step 1:** 先冻结 Package/Price/Benefit、Promotion、Redeem 的 OpenAPI examples 和 error matrix。
- [ ] **Step 2:** 写同码并发、同 recipient quota、过期、disabled、payload conflict、Redis outage 的 failing tests。
- [ ] **Step 3:** 实现 batch/template/code schema 与 composite tenant FK。
- [ ] **Step 4:** 实现 redemption transaction：receipt → code lock → eligibility → source fact → fulfillment → grant/journal/outbox。
- [ ] **Step 5:** 运行 fresh migration、unit、integration、architecture 和 secret-leak scan。

## Task 4: 迁移 Payment repositories 与 cross-context ports

**Files:**
- Create: `kokoro-billing/src/bounded-contexts/payment/infrastructure/mysql/checkout-repository.ts`
- Create: `kokoro-billing/src/bounded-contexts/payment/infrastructure/mysql/settlement-repository.ts`
- Create: `kokoro-billing/src/cross-context/payment-entitlement/payment-settlement-port.ts`
- Create: `kokoro-billing/src/cross-context/payment-entitlement/payment-entitlement-acl.ts`
- Modify: `kokoro-billing/src/modules/payment/provider-event-processor.ts`
- Test: `kokoro-billing/test/integration/payment-fulfillment.test.ts`

- [ ] **Step 1:** 为 provider event、checkout、settlement、reversal 定义 repository ports 和 source-fact uniqueness。
- [ ] **Step 2:** 把 provider adapter 的外部 DTO 映射为 Payment domain event，不让 Stripe DTO 穿透 Application 层。
- [ ] **Step 3:** 用 outbox/ACL 调用 Entitlement `AcceptPaymentSettlement` 和 `ReverseFulfillment`。
- [ ] **Step 4:** 验证 webhook replay、provider unknown、partial refund、cross-tenant FK 和 outbox retry。

## Task 5: 拆 runtime composition roots 与 query/read model

**Files:**
- Create: `kokoro-billing/src/runtime/api.ts`
- Create: `kokoro-billing/src/runtime/payment-worker.ts`
- Create: `kokoro-billing/src/runtime/credit-sweeper.ts`
- Create: `kokoro-billing/src/runtime/migrator.ts`
- Modify: `kokoro-billing/src/main.ts`
- Modify: `kokoro-billing/package.json`
- Modify: `kokoro-billing/Dockerfile`
- Modify: `kokoro-billing/.github/workflows/ci.yml`

- [ ] **Step 1:** API、worker、sweeper、migrator 分别只负责 composition 和 lifecycle，不重复 domain logic。
- [ ] **Step 2:** 为 admin/user ledger/stats 建专用 query service；query 可直接读 read model，但必须统一 tenant predicates。
- [ ] **Step 3:** 为每个 runtime 增加 health、metrics、graceful shutdown 和独立 container command。
- [ ] **Step 4:** 在干净 MySQL/Redis 上运行完整 CI：`pnpm verify`、`pnpm test:integration`、Docker build、audit、backend design audit。

## 完成标准

- 所有 mutation SQL 只存在于 bounded-context infrastructure repository 或 migration。
- 每个 aggregate root 有明确 repository port；没有 GenericRepository<T> 逃逸口。
- API、worker、sweeper、migrator 可独立启动，但共用同一 repo/domain/application 版本。
- Package/Promotion/Redeem 的需求、状态机、API、SQL、审计、失败恢复和测试证据互相一致。
- MySQL/Redis 故障、重复请求、并发同码、跨租户 ID、provider unknown 都有自动化验证。
- 文档中的 planned/implemented 状态与代码和 migration 事实一致。
