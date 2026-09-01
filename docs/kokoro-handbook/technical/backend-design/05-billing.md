# kokoro-billing 设计卡

## 定位

`kokoro-billing` 是一个代码子仓库，内部包含三个 bounded context：Commerce、Payment 与 Entitlement/Credit。
Payment 拥有外部 money facts；Entitlement 拥有 Fulfillment、SubscriptionTerm、CreditGrant、Hold 和
Journal。该设计卡 supersede `03-credit.md` 与 `04-payment.md` 的“两个独立业务仓库”目标，但保留两者
作为历史审阅证据。

## API 版本与目录

首发 HTTP contract 固定为 `v1`，版本只存在于 transport boundary：

```text
contract/openapi/v1/openapi.yaml
src/interfaces/http/v1/
src/interfaces/admin/v1/
```

`application/`、`domain/`、`ports/`、`adapters/`、`database/` 不建立 v1/v2 副本。HTTP 采用资源导向路径：
`/v1/commerce/...`、`/v1/billing/...`、`/v1/admin/...`、`/v1/internal/...`、`/v1/webhooks/...`。
capture、release 等领域动作使用明确的 action 子资源，不复制 Manus 的点号 operation URL。

版本、幂等、RequestId、Webhook、cursor、429 和异步执行规则以 [ADR-027](../../decisions/ADR-027-billing-api-versioning-and-transport-boundary.md)
及 [Billing 目标 API 与 SQL 契约](../51-billing-target-api-and-sql-contract.md) 为准。

## 模块规则

```text
entitlement.catalog       Offer/Price/Benefit revision
entitlement.fulfillment   Acquisition/Fulfillment/SubscriptionTerm/EntitlementGrant
entitlement.credit        CreditAccount/CreditGrant/Hold/HoldAllocation/CreditJournal
entitlement.metering      InvocationPriceRevision/BillingAdmission/AuthorizeModelInvocation/CaptureOrReleaseInvocation
payment.checkout          Checkout/command receipt/provider session
payment.facts             ProviderEvent/Settlement/SubscriptionPeriod/Reversal
payment.outbox             Provider and Entitlement effect retry
shared.outbox              only transport primitives; no shared business repository
```

模块不得直接读取其他模块的 repository implementation 或 SQL row；跨模块只调用 application port。

## 明确修正

旧 Credit 的 `recordUsage` 不能继续表达“已结算但不扣余额”的模糊语义。GA target 不以 token 用量作为用户计费单位；
新方案只保留：

- `AuthorizeModelInvocation`：在 provider send 前，以 `invocationId + billingRef + billingSubject + featureKey` 校验固定每调用
  价格和余额，创建只绑定该 invocation 的 `holdRef`；拒绝时 GA 不发送 provider；
- `CaptureModelInvocation`：只接受 GA durable 的 provider-accepted receipt；以 `invocationId` 幂等，在同一 PostgreSQL transaction
  完成 hold capture、allocation、ledger、settled usage；
- `ReleaseModelInvocationHold`：只接受 confirmed rejection/reconciliation-not-accepted 的 durable receipt；以同一 `invocationId`
  幂等释放该 `holdRef`；
- `RecordUsageFailure`：写失败原因和可重试状态，不产生扣款。

## GA 模型调用结算入口

GA 不用 `RuntimeNamespace` 找账单账户。它在 provider 接受一个模型调用后，通过 Internal Metering API 提交一条
`ModelInvocationAccepted` 使用回执：

```text
invocationId                         # Billing 唯一幂等键
billingSubject(kind, opaqueRef)      # ExecutionIdentity.subject 的最小投影
billingRef                           # Billing admission context, bound to tenant/subject/Feature
holdRef / priceRef                   # Billing creates the per-invocation reservation and fixed price
featureKey / acceptedProviderRef / acceptedAt
gaReceiptId + authenticated GA issuer
```

Billing 验证 GA service identity、回执完整性、`billingRef ↔ billingSubject` 与 `holdRef ↔ invocationId` 绑定；再由 Entitlement/Credit
context 把 subject 映射到个人或项目 payer，执行一次 hold capture、allocation 和 CreditJournal 写入。provider confirmed rejection 走同一
`invocationId` 的 durable hold release；unknown 在 provider reconciliation 前维持 hold。
原始 `actor` 只属于审计，`RuntimeNamespace`、checkpoint key、短时 `RunExecutionAttestation` 与 IAM assertion 都不进入
Billing 的 payer/account selector。用户价格只读 `meter_kind=model_invocation` 的 fixed `invocationMicros`，不读 token 数量；token
可保留为 provider 成本、预算和诊断。回执是 durable outbox fact，故不能依赖短时 attestation 在延迟投递时仍有效。

## 对外契约与租户边界

- 用户、内部服务和 Admin API 的外部租户上下文统一使用 `tenantId`，通过
  `X-Kokoro-Tenant-Id` 或 IAM JWT 的 `tenant_id` 进入 Billing。
- clean-build Billing 统一使用 `tenantId` / `tenant_id`；不新增 `siteId` / `site_id` 兼容字段或第二套租户标识。
- Provider webhook 的租户权威来自 provider-account registry。签名 payload 中的 `tenantId`
  只做一致性校验；历史 payload 中的 `siteId` 也只做同一项校验，二者都不能选择授权租户。
- PostgreSQL 是账务与权益事实源；Redis 只负责幂等提示、短租约、缓存和协调，不替代 PostgreSQL
  transaction、ledger 或状态机。

## 数据 owner、公开入口与验证证据

| 领域 | owner / writer | 公开入口 | 主要证据 |
|---|---|---|---|
| Payment facts | `kokoro-billing` Payment context | `/v1/billing/checkout`、Webhook、Admin payment routes | provider event、checkout、settlement、refund integration tests |
| Entitlement/Credit | `kokoro-billing` Entitlement context | `/v1` User/Internal/Admin routes | hold/capture/release/grant/expiry/reconciliation tests |
| GA 模型 usage | Billing Internal Metering application port | `AuthorizeModelInvocation` + `ModelInvocationAccepted` + release | subject/billingRef/holdRef binding、invocationId 幂等、GA service receipt、token-free price integration tests |
| Schema | Billing migration runner | `database/migrations/0001..0029` | fresh PostgreSQL migration test、SQL naming gate |
| Contract | Billing OpenAPI | `contract/openapi/v1/openapi.yaml`（目标） | route parity / OpenAPI verification |

## 100 分证据

- 业务边界：Payment 与 Entitlement/Credit 在同一仓库内保持 bounded context 隔离。
- 数据 owner：每张 Billing 业务表由 Billing 唯一写入，跨租户关系由 PostgreSQL 复合外键保护。
- 并发正确性：PostgreSQL transaction/row lock 保护余额、hold、ledger；Redis 仅作为可丢失协调层。
- 外部契约：User、Internal、Admin、Webhook 四面 API 及 provider-specific signature 规则有 OpenAPI。
- 幂等与重放：command receipt、provider event、outbox、usage event、grant/reversal 均有冲突与 replay 测试。
- 基础设施：PostgreSQL + Redis 的真实集成测试、readyz、leader lease、outbox lease 和 Docker 构建均有证据。
- 迁移治理：当前尚未上线，旧 `kokoro-credit` / `kokoro-payment` 只是工作区中的历史代码；未来决定上线时，才按
  `billing-legacy-cutover-runbook.md` 执行旧 writer 停写和消费者切换。
- **GA target 落地门：**`billing-v1.yaml`、当前 29 个 migration 与 route parity 是 token/generic-usage V1 证据，不能替代
  `AuthorizeModelInvocation / ModelInvocationAccepted / ReleaseModelInvocationHold` 的 target OpenAPI、schema migration、
  per-invocation idempotency/reconciliation integration tests；这些完成前，Feature-first GA 不得调用 V1 `usage/events` / `usage/settle`。

## 当前落地证据与迁移门禁

- 代码：`kokoro-billing/src/`、`kokoro-billing/database/migrations/`、`kokoro-billing/test/`。
- 契约：`kokoro-billing/contract/openapi/billing-v1.yaml`。
- 文档：`31-billing-subrepository-architecture.md`、`billing-api-contract-v1.md`、
  `billing-mysql-schema-v1.md`、`billing-closure-evidence.md`。
- 当前验证基线（V1）：`pnpm verify` 46 passed；真实 PostgreSQL/Redis 集成 50 passed；29 migrations fresh run；
  Docker build、production dependency audit 和 `git diff --check` 通过。
- 上线前才需要完成旧 writer 停止、consumer contract 切换、source-level reconcile、回滚窗口和旧入口删除；这些是发布操作，不是当前代码实现缺口。

## 迁移顺序

1. 建立 `kokoro-billing` contract、schema owner inventory 和 SQL migration runner。
2. 迁移 Entitlement catalog/fulfillment/credit/metering，先建立 CreditGrant、HoldAllocation、Journal。
3. 迁移 Payment provider/checkout/settlement/subscription/reversal，保留 provider webhook evidence。
4. 建立 PaymentSettlement → Acquisition → Fulfillment 的 outbox contract，不再直接跨仓 HTTP grant。
5. Payment/legacy Model/Agent/Session 切换到 User/Internal/Admin/Webhook 四面 Billing V1 contract。
6. 单独执行 Feature-first GA 的 invocation-metering expand/shadow/cutover：新增 target route/schema/migration，验证
   `billingRef + holdRef + invocationId` binding、unknown reconciliation 和无 token user pricing，再删除 GA 的 V1 usage route 权限。
7. 双写校验与 source-level reconcile 稳定后，停止旧 writer。
8. 删除旧 writer、旧 registry、旧跨仓 credit client。
