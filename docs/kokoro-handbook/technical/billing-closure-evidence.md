# Billing 实现闭环证据清单

状态：本地 **V1** 实现与验证范围已验收，2026-08-22。当前项目尚未上线，也没有正在运行的旧 writer；本文只证明 V1 代码、契约、数据库和测试闭环。
未来决定上线时，才需要按 [`billing-legacy-cutover-runbook.md`](billing-legacy-cutover-runbook.md) 执行旧仓库停写、真实环境观察窗口和 operator sign-off；这不是当前实现缺口。

> **Feature-first GA target 尚未由本证据验收。**当前 OpenAPI/schema/`UsageSettlementService` 仍按 token/generic usage 运行。
> GA 的 `AuthorizeModelInvocation → ModelInvocationAccepted → ReleaseModelInvocationHold`、`meter_kind=model_invocation`、
> typed tenant+subject 和 unknown reconciliation hold，必须在同一个新 contract/schema/caller/test 切换中实现；在此之前不应把
> “V1 计量闭环”表述为“GA 按调用次数扣积分已完成”。

## 1. 业务链路

| 链路 | 目标事实 | 代码/契约证据 | 验证证据 |
|---|---|---|---|
| 套餐与购买 | immutable offer revision → quote snapshot → checkout | `catalog/*`, `checkout-service.ts`, `/billing/plans`, `/billing/checkout` | checkout、catalog integration |
| 支付成功 | provider session → signed inbox → outbox → worker → settlement | provider adapters、`ProviderEventInboxService`、`ProviderEventProcessor` | mock checkout worker E2E、provider webhook integration |
| 权益发放 | settlement → acquisition → fulfillment → grant → journal → account projection | `BillingSettlementService`、Credit application services | payment fulfillment、reconciliation integration |
| 退款 | durable refund command → reversal → grant reversal → negative journal | `BillingReversalService`、`payment_command_receipt` | payment reversal、mock refund integration |
| 订阅 | provider period → entitlement term → period grant | `SubscriptionGrantService`、subscription processor | subscription period replay integration |
| 用量（V1） | quote → usage event → hold/allocation → capture/release → journal | metering services、hold allocation tables | usage settlement、pricing integration |
| 价格运营 | Admin publish → immutable usage price revision → quote/hold snapshot | `UsagePricingAdminService`、`/admin/billing/usage-pricing`、`entitlement_command_receipt` | usage pricing admin integration |
| 首次配置 | 受保护 seed → catalog/pricing revision → 可重放 bootstrap | `scripts/seed-billing.ts`、`db:seed`、`provision.sh` | 同一 JSON 两次执行保持同一 revision、无重复行 |
| 过期释放 | MySQL active hold/grant → Redis leader lease → expiry mutation | `expire-credit-holds.ts`、`GrantExpiryService`、`RedisLease` | Redis lease、usage/grant expiry integration |
| 对账与运营 | projection、journal、grant、settlement、reversal、provider failure drift | `ReconciliationService`、Admin routes | reconciliation、admin HTTP/integration |

## 2. 横切门禁

- **事实源**：MySQL 8.4/InnoDB；Redis 只做 fast-path、lease 和异步协调，不承载余额或最终幂等；通用限流由平台边缘层负责。
- **并发**：application transaction 独占 MySQL pool session；outbox 使用 `SKIP LOCKED + lease_token`；Payment
  worker 不用 Redis 全局锁串行化吞吐。
- **幂等**：Redis hint 过期后仍由 MySQL receipt/source fact 返回原结果；payload 变化返回冲突。
- **计量关联**：settle 不仅校验 hold/usage event ID，还校验同一 tenant、subject、feature，跨主体或跨 feature 事件返回 `billing.usage_event_mismatch`。
- **订阅有效期**：subscription period grant 复制 provider `currentPeriodEnd` 为 grant `expires_at`，过期周期不会发放永久额度。
- **租户安全**：生产 User 面使用 IAM RS256/JWKS Bearer JWT，`tenant_id` 必须与 `x-kokoro-tenant-id` 一致；Provider
  webhook 通过 `(provider, external_account_ref)` 映射 tenant，direct-account endpoint 使用显式配置的 provider account ref，
  新 metadata 使用 `tenantId`，历史 payload 的 `siteId` 仅作为一致性校验。
- **Fixture 隔离**：`header-fixture` 仅用于本地 mock webhook；生产 JWKS 模式才启用 provider-account registry 作为 webhook 租户权威。
- **API 隔离**：User、Internal、Admin、Provider Webhook 独立认证和路由；Internal 使用 service secret，Admin 使用
  独立 operator proxy secret，并强制 `x-kokoro-service=admin`；Manifest 读取使用 gateway principal，Admin mutation
  透传真实 operator/role、reason、audit。
- **契约**：OpenAPI 与实际 Fastify 路由 parity 当前为 30/30；CI 强制 `pnpm sql:check` 与 `pnpm contract:check`。
- **可观测性**：API、Payment worker、Credit sweeper 分别暴露 Prometheus metrics；provider queue pending age 不混入 integration outbox。
- **运行时**：Docker runtime 仅安装 production dependencies；migration/worker 由 `dist/scripts` 编译入口运行。
- **旧 writer 默认关闭**：Compose 旧 Payment/Credit 使用 `legacy` profile；Kubernetes base 不包含旧 writer，
  rollback/shadow 只能通过显式 legacy overlay/runtime 开启。
- **跨仓认证**：两个 User BFF 在 Billing target 分支透传 sealed session 中的 IAM runtime JWT；旧 Payment
  fallback 才保留 legacy subject header；Platform Admin gateway 对 Billing 注入 operator proxy secret。

## 3. 当前可复现实证

```bash
pnpm install --frozen-lockfile --ignore-scripts --no-optional
pnpm verify
DATABASE_URL=TARGET REDIS_TEST_URL=REDIS_TARGET pnpm test:integration
pnpm audit --prod --audit-level=high
docker build -t kokoro-billing:verify .
DATABASE_URL=TARGET node dist/scripts/apply-migrations.js
```

最近一次本地证据：`pnpm verify` 通过（46 tests passed）；真实 MySQL/Redis integration 为 50 passed、0 skipped；29 migrations fresh run；OpenAPI
route parity 30/30，并由 contract gate 检查外部 schema 不暴露 `siteId` property、租户上下文固定为
`X-Kokoro-Tenant-Id`；全新 MySQL 数据库 29 个 migration 从零应用成功；Provider account tenant mapping integration 通过；Billing bootstrap 重放保持 1 个 catalog revision
和 1 个 pricing revision；Docker `/healthz` 与 `/readyz` 均通过，
readyz 同时确认 MySQL、Redis；Dockerfile 使用固定 Node 22 Bookworm digest；生产依赖审计无 high 级已知漏洞，CI
也会强制执行该 audit。

Kubernetes 运行拓扑已纳入 `deploy/k8s/base/billing.yaml`：`billing-migrate`、Billing API、Payment worker
和 Credit sweeper 分离部署；`kubectl kustomize` 与 client dry-run 均通过，生产认证固定使用 JWKS。

## 4. 明确不混淆的发布门禁

以下事项不属于本地实现缺口，但必须在真实切流前完成：

1. `kokoro-payment` 与 `kokoro-credit` 旧 writer 停止写入并保留只读回滚窗口；
2. 真实 legacy source shadow audit 连续零 drift；
3. 所有消费者切换到 Billing contract；
4. 运营人员完成 webhook、refund、usage、worker crash/retry 和 rollback exercise；
5. release manifest 记录 writer stop 时间和 operator sign-off。

## 5. V1 范围边界

V1 已验收范围是套餐/checkout、支付、订阅、退款、Admin grant、usage hold/settle/release、journal、outbox、
对账和切流门禁。兑换码/活动码与 dispute/chargeback 需要额外的 code/campaign/provider-dispute 事实模型，
当前明确列为后续扩展，不将未定义的表或接口伪装成已完成能力。

GA target 的按调用计费也属于本节的**未完成迁移**，不是 V1 extension 的别名：它要新增 per-invocation Billing admission/hold、
provider-accepted receipt/release、`(tenant_id, invocation_id)` 幂等事实和 token-free user price，并替换 GA 对 V1 usage endpoint 的依赖。
