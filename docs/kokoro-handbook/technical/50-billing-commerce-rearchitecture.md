# Kokoro 商业系统重构版最终技术架构

状态：**当前唯一目标架构**，2026-08-24。

本文从 Kokoro 的真实产品重新建模，不以现有 `kokoro-billing` V1 的表或 service 作为设计前提。
实现级字段、状态和事务契约见 [Billing 目标 API 与 SQL 契约](51-billing-target-api-and-sql-contract.md)。
现有 V1 尚未上线，直接废弃其旧实现；不做历史数据迁移、不保留旧 writer、不做双轨运行。本文解决的是：AI 产品商城如何把商品、订单、支付、权益、积分、
用量、订阅、优惠和退款组织成一条可解释、可恢复、可对账的闭环。

## 1. 先固定产品事实

Kokoro 不是传统实物电商，也不是单纯 Stripe Checkout：

```text
产品入口(App/Feature/Studio)
  -> 用户/项目产生可计费能力使用
  -> 价格策略决定应扣多少
  -> 预付积分/订阅权益/免费额度决定从哪里扣
  -> provider / Agent / Studio Job 执行
  -> 成功结算或释放预留
  -> 产物与账务分别落自己的事实
```

商业上同时存在三类交易：

1. **购买交易**：用户购买套餐、订阅、积分包或兑换权益；
2. **使用交易**：Feature、ModelInvocation、Studio Job 消耗权益/积分；
3. **运营交易**：优惠、赠送、撤销、退款、过期、调账和对账。

不能用一张 `payment_checkout` 或一张 `credit_balance` 表表达这三类不同交易。

## 2. 最终边界：一个 repo，三个 bounded context

### 2.1 Git repo 与运行单元

```text
kokoro-billing/                         一个 Git repository
├── commerce context                    商品、报价、订单、优惠、兑换入口
├── payment context                     Provider、支付集合、支付尝试、退款
└── entitlement context                 订阅、权益、积分、用量、账本

runtime processes:
  billing-api                           Storefront/Admin/Internal/Webhook API
  payment-worker                        Provider event / payment retry
  entitlement-worker                   fulfillment / subscription / expiry
  reconciliation-worker                drift detection / repair command
  schema-job                            fresh database schema application
```

一个 repo 不是一个万能 service。三个 context 各自拥有语言、表、application service、repository port 和状态机；
先共用 MySQL 与发布生命周期，未来满足团队/吞吐/数据 owner 独立条件再拆 repo。

### 2.2 Commerce Context：卖什么、订单是什么

拥有：

- Product/Package/Offer/Price/Benefit definition；
- immutable published revision；
- Cart、Quote、Order、OrderLine；
- Promotion/Coupon、Adjustment、RedeemCampaign/Code；
- Order fulfillment intent（不拥有实际权益账本）；
- Storefront 与 Commerce Admin API。

Commerce 不拥有 provider payment 状态，不直接写 CreditJournal。

### 2.3 Payment Context：钱如何被授权、捕获、退款

拥有：

- ProviderAccount、PaymentCustomer；
- PaymentCollection、PaymentSession、PaymentAttempt；
- ProviderEventInbox、PaymentSettlement、PaymentRefund、Dispute；
- Payment outbox、重试和 provider reconciliation。

Payment 不决定购买后发什么权益，不直接写 Entitlement/Credit 表。

### 2.4 Entitlement Context：买到什么、使用什么

拥有：

- BillingSubject、PayerAccount、BillingCustomerBinding；
- Subscription、SubscriptionPeriod、EntitlementGrant；
- CreditAccount、CreditGrant、CreditHold、HoldAllocation、CreditJournal；
- UsagePriceRevision、BillingAdmission、UsageEvent、UsageSettlement；
- Fulfillment、Reversal、expiry、usage reconciliation。

Entitlement 不决定商品售价，不调用 provider，不接收任意 caller 传入金额。

### 2.5 外部 owner

```text
IAM       identity / tenant / user / team / authorization
Model     model catalog / provider cost hint / routing
GA        feature admission / execution / invocation identity
Studio    project / job / provider execution / artifact relation
Storage   asset / artifact / object lifecycle
Billing   commercial price / payment / entitlement / credit facts
```

Agent、Model、Studio 只能使用 Billing 的 quote/admission/hold/capture/release contract。

## 3. 身份与账户：三个概念必须分离

```text
IAM subject
  -> BillingSubject(tenantId, kind, opaqueRef)
  -> BillingCustomerBinding
  -> PayerAccount(personal | project | organization)
  -> CreditAccount / PaymentCustomer
```

- `BillingSubject`：谁产生 usage；
- `PayerAccount`：谁承担费用；
- `CreditAccount`：payer 可消费的积分 projection；
- `RuntimeNamespace`、`ownerId`、`workspaceId`、`userId` 不能被 caller 当作 Billing 账户选择器；
- 同一 tenant 可有多个 subject 归属同一 payer；跨 tenant 永不自动合并；
- 对外统一使用 `tenantId`；数据库同样使用 `tenant_id`，不保留 `site_id` 兼容列。

## 4. 商品与价格模型

```text
Product/Offer (稳定业务 key)
  -> OfferRevision (immutable)
    -> Price (currency, amount, interval)
    -> BenefitDefinition
      -> GrantTemplate (credit / feature / quota / expiry / priority)
```

### 4.1 四种商品

| 商品 | 购买结果 |
|---|---|
| Subscription plan | SubscriptionPeriod + recurring entitlement/credit grant |
| One-time credit pack | 一次性 CreditGrant lot |
| Feature entitlement pack | FeatureGrant / quota grant |
| Bundle | 多个 Benefit 的 revision snapshot |

Model 成本、provider 价格、用户售价、Promotion discount 是四个不同概念：Model 只提供成本/能力参考；Commerce Price 决定售价；
Promotion 生成 adjustment；Entitlement GrantTemplate 决定到账。

### 4.2 版本不变量

- 已发布 revision 不可更新，只能发布新 revision；
- Quote、OrderLine、SubscriptionPeriod、Grant 都要保存 revision/snapshot；
- 修改价格不重算历史订单；
- 修改 grant expiry/priority 不影响已发放 grant；
- offer 下架不撤销已购买权益。

### 4.3 价格解析与价格快照

价格解析只能由 Commerce/Entitlement 的 published `PricePolicyRevision` 完成，不能由 Model、Agent、浏览器或 provider 决定：

```text
tenant + payer + active subscription
  + product/offer + featureKey + surface
  + controlled model tier (optional)
  + quantity / job size
  -> PricePolicyRevision
  -> Quote(lines, adjustments, currency, total, grant policy, expiresAt)
```

解析优先级固定为：tenant 发布的 feature/product policy → payer 当前生效的 subscription policy → offer/feature 默认 policy；
没有匹配 policy 就拒绝，不自动猜价格。`modelId`、provider、token 成本只进入内部 cost metadata，不直接成为用户价格键。
Quote 必须保存 policy revision、price、currency、grant policy、promotion adjustment 和过期时间；Order/Admission 只能使用该 snapshot。

## 5. 订单与支付：完整商城闭环

### 5.1 订单状态机

```text
draft
  -> quoted
  -> awaiting_payment
  -> partially_paid
  -> paid
  -> fulfillment_pending
  -> fulfilled

draft/quoted/awaiting_payment -> expired | cancelled
paid/fulfilled -> refund_pending -> partially_refunded | refunded
```

订单状态不代替支付状态或 fulfillment 状态；订单只表达商业购买生命周期。

### 5.2 Payment 状态机

```text
PaymentCollection: open -> requires_action -> authorized -> captured
                  -> partially_refunded -> refunded
                  -> failed | cancelled | unknown

PaymentAttempt: created -> authorization_pending -> authorized
              -> capture_pending -> captured
              -> voided | failed | unknown
```

Provider webhook 可以乱序、重复和延迟；本地状态只允许合法前向迁移。`unknown` 必须进入 reconcile，不可猜成功。

### 5.3 购买事务

```text
Storefront
  -> create Quote (read/calculation)
  -> create Order + OrderLine + Adjustment snapshot
  -> create PaymentCollection
  -> create PaymentSession (outside DB tx)
  -> provider authorization/capture
  -> signed ProviderEventInbox
  -> PaymentSettlement
  -> Commerce marks payment status
  -> Entitlement Fulfillment
  -> CreditGrant / FeatureGrant / SubscriptionTerm
```

Payment 成功不等于权益已经发放；权益发放失败必须有 durable outbox/retry/reconcile。

### 5.4 订单金额不变量

```text
line_subtotal = SUM(quantity * unit_price)
adjustment_total = SUM(order_adjustment.amount_signed)
order_total = line_subtotal + adjustment_total
payment_collection.amount_due = order_total - captured_total
captured_total - refunded_total <= order_total
```

所有金额使用订单 currency，不能跨币种相加。金额快照在 order、collection、attempt、refund 中重复保存，以便 provider 对账和历史解释；
重复保存不是第二个 owner，真正的事实 owner 仍是对应 bounded context。

## 6. Promotion、Coupon、Redeem 与 Adjustment

### 6.1 Promotion

```text
PromotionCampaign
  -> PromotionRevision
    -> Conditions (date, tenant, payer, product, minimum amount)
    -> Actions (percent/fixed/free entitlement)
    -> UsagePolicy (global/per payer/per subject/budget)
```

Promotion 评估后写入 `OrderAdjustment`，不能只在 order 上保存 `discount_total`。
同一 payer 的使用次数、预算占用、code redemption 必须在 MySQL transaction 内唯一化。

### 6.2 折扣与权益的边界

Promotion 可以减少现金订单金额，但不能直接改变已发布 GrantTemplate。购买后的权益由 OrderLine 的 benefit snapshot 生成；
赠送积分必须使用明确的 `source_kind=promotion|admin|campaign` grant fact。Promotion 退款时按 adjustment 和 grant source 分别逆向，
不以“把订单总价加回去”替代权益撤销。

### 6.3 Redeem Code

Redeem code 不是 Promotion code：

```text
Promotion Code      -> OrderAdjustment
Entitlement Code    -> Fulfillment/Grant
Prepaid Credit Code -> Fulfillment/CreditGrant
```

保存 `HMAC(normalized_code)`，不保存明文；兑换事务：

```text
command receipt
 -> lock code
 -> validate tenant/campaign/payer/expiry/limit
 -> mark redeemed
 -> create acquisition
 -> create fulfillment
 -> create grant/journal
 -> outbox
 -> commit
```

## 7. Entitlement 与 Credit：账务不是余额

### 7.1 Credit 事实

```text
CreditAccount projection
CreditGrant lot                来源/过期/优先级/剩余量
CreditHold reservation         预留但未消费
HoldAllocation                 预留来自哪个 grant
CreditJournal                  append-only signed facts
UsageEvent                     外部执行事实
UsageSettlement                一次 usage 的结算事实
```

### 7.2 扣减生命周期

```text
Quote/Admission
  -> Hold(active)
  -> provider/GA/Studio execution
  -> accepted -> Capture + allocation + journal
  -> confirmed failure -> Release
  -> unknown -> hold active -> reconcile
```

### 7.3 扣减顺序

```text
free quota
  -> promotional grant
  -> expiring prepaid grant
  -> paid grant
  -> pay-as-you-go / reject
```

具体顺序必须由 published burn policy 决定并写入 hold allocation；不能在代码中隐式排序。

### 7.4 不变量

```text
available = gross - held
gross = SUM(grant.remaining)
hold = captured + released + active_remainder
每个 usage/invocation/hold 只能有一个 capture 或 release 终态
每个 source acquisition 只能产生一份 fulfillment
```

### 7.5 Feature、ModelInvocation 与 Studio Job 的计费单位

```text
Feature admission
  -> zero_rated | included | separate

separate + Model provider call
  -> one ModelInvocation(invocationId)
  -> one BillingAdmission/hold
  -> accepted capture OR confirmed rejection release

Studio Job
  -> either job-level fixed-price admission
  -> or child ModelInvocation admissions
  -> never both for the same billable effect
```

每一次实际 provider send 都必须有稳定 `invocationId`；重试同一个 provider operation 使用同一 invocation identity，
真正的新 provider send 才创建新 invocation。Studio Job 的 job-level 与 child-invocation 模式在创建时确定并固化，避免双扣。
Billing 不接收 token 数量决定用户价格；token 仅作为 provider cost/usage analytics。`accepted` 必须来自受信 GA/Studio service，
不能由浏览器、Agent prompt 或不可信 provider 字段直接触发 capture。

## 8. 退款、撤销、过期、拒付

```text
PaymentRefund / Chargeback fact
  -> Order refund allocation
  -> Fulfillment reversal
  -> CreditJournal reversal/adjustment
  -> exposure if already consumed
```

- Payment refund 是钱的事实；Credit reversal 是权益事实；两者不可混为一张 refund 表；
- 已消费额度不能静默恢复或把余额改成负数；生成 `reversal_exposure`；
- 过期生成 expiry journal，不删除 grant；
- chargeback 复用 reversal pipeline，但保留 provider dispute source；
- partial refund 必须关联 order line、payment settlement 和已发放 grant 的比例/固定分配规则。

退款策略在产品配置中明确为 `proportional` 或 `line_specific`；创建 refund 时锁定原始 order/settlement/fulfillment，
禁止根据当前 catalog 或当前余额重新计算历史退款。

## 9. SQL 目标模型

### 9.1 Commerce owner tables

```text
commerce_product
commerce_offer
commerce_offer_revision
commerce_offer_benefit
commerce_price_revision
commerce_cart
commerce_quote
commerce_order
commerce_order_line
commerce_order_adjustment
commerce_promotion
commerce_promotion_revision
commerce_promotion_redemption
commerce_redeem_campaign
commerce_redeem_code_batch
commerce_redeem_code
commerce_command_receipt
commerce_outbox
```

### 9.2 Payment owner tables

```text
payment_provider_account
payment_customer_binding
payment_collection
payment_session
payment_attempt
payment_provider_event
payment_settlement
payment_refund
payment_dispute
payment_command_receipt
payment_outbox
```

### 9.3 Entitlement owner tables

```text
entitlement_payer_account
entitlement_subject_binding
entitlement_subscription
entitlement_subscription_period
entitlement_fulfillment
entitlement_grant
entitlement_credit_account
entitlement_credit_grant
entitlement_credit_hold
entitlement_credit_hold_allocation
entitlement_credit_journal
entitlement_usage_price_revision
entitlement_billing_admission
entitlement_usage_event
entitlement_usage_settlement
entitlement_fulfillment_reversal
entitlement_command_receipt
entitlement_outbox
```

### 9.4 SQL 规则

- 每张表只有一个 context owner；跨 context 通过 source fact / outbox / application port；
- 所有 tenant-owned FK 使用 `(tenant_id, id)` lineage；外部 API 使用 `tenantId`；
- 业务状态使用 `VARCHAR + CHECK`，不使用 MySQL ENUM；
- 金额使用 `BIGINT` + 明确单位，API 使用十进制字符串；
- 历史价格、权益和折扣写 snapshot，不依赖可变 JSON 作为唯一可查询事实；
- provider event、attempt、settlement、refund、journal、redemption append-only；
- 幂等使用 `(tenant, context, command, idempotency_key)` 唯一约束，Redis 不作为最终唯一键；
- 不使用 `billing_history` 万能表；分别提供 Order/Payment/Credit/Usage/Reconcile read model；
- schema versioning 只服务全新数据库的可重复建库和未来正常 schema 演进；不包含旧数据导入、双读、双写或兼容字段。

## 10. API 契约

### 10.1 通用边界

```json
{
  "data": {},
  "meta": {"request_id": "req_TARGET"}
}
```

错误响应与 IAM v1、Manus API v2 的共同原则保持一致：

```json
{
  "error": {
    "code": "billing.invalid_request",
    "message": "stable human-readable message",
    "request_id": "req_TARGET",
    "retryable": false,
    "details": {}
  }
}
```

首发 Billing HTTP JSON 使用 `snake_case` 字段，和 IAM v1 的 `{data, meta}` / `error.request_id` 约定统一；Header 继续使用
HTTP 规范的 `X-Kokoro-Request-Id`、`X-Kokoro-Tenant-Id` 和 `Idempotency-Key`。领域内部 TypeScript 可以使用 camelCase，
但只能在 v1 adapter 内完成映射，不能泄漏到 wire contract。

Mutation 必须带 `Idempotency-Key`；服务端把 `(tenantId, api_surface, command, key, payload_hash)` 写入 owner receipt。
相同 key 和相同 hash 返回首次结果；相同 key 不同 hash 返回 `billing.idempotency_conflict`。
金额、积分、数量、余额、退款金额全部使用十进制字符串；cursor、orderId、paymentId、grantId、holdId、invocationId 都是 opaque。

统一错误类别：

```text
billing.invalid_request
billing.unauthorized
billing.forbidden
billing.tenant_mismatch
billing.not_found
billing.idempotency_conflict
billing.command_in_progress
billing.insufficient_credit
billing.price_unavailable
billing.order_not_payable
billing.payment_action_required
billing.provider_event_invalid
billing.reconciliation_required
```

### 10.2 API 版本策略

Manus 使用 `/v2/task.create` 这种显式版本路径；Kokoro 采用同一类“版本属于 transport contract”的原则，但使用资源型 REST 路径：

```text
/v1/commerce/...
/v1/billing/...
/v1/admin/...
/v1/internal/...
/v1/webhooks/...
```

- 版本按整个 API contract 发布，不按每张表、每个 service 或每个 endpoint 单独编号；
- `/v1` 是首发 clean-build 契约，破坏性变更创建 `/v2`，不在 `/v1` 内静默改变 required 字段、状态含义或金额单位；
- v2 与 v1 可以在未来短期并存，但当前未上线，不预留兼容实现、不做双写；
- `healthz`、`readyz`、`metrics` 属于运维探针，不进入业务版本；
- Manus 的 `task.create` 点号动作命名适合其 RPC-like API；Kokoro 的业务资源使用 REST 名称，命令动作只作为明确的子资源，例如
  `/v1/internal/billing/admissions/{admission_id}/capture`，不把点号命名混入数据库或领域对象；
- OpenAPI `info.version`、文档标题、客户端 SDK namespace 和路由前缀必须同一发布版本，contract test 校验四者一致。

### Storefront/User

```text
GET  /v1/commerce/catalog
POST /v1/commerce/quotes
POST /v1/commerce/orders
GET  /v1/commerce/orders/{orderId}
POST /v1/commerce/orders/{orderId}/checkout
POST /v1/commerce/orders/{orderId}/redeem
GET  /v1/billing/me/payer
GET  /v1/billing/me/entitlements
GET  /v1/billing/me/credit-account
GET  /v1/billing/me/credit-ledger
GET  /v1/billing/me/usage
```

### Admin

```text
GET/POST /v1/admin/commerce/offers
POST     /v1/admin/commerce/offers/{id}/publish
GET/POST /v1/admin/commerce/promotions
GET/POST /v1/admin/commerce/redeem-campaigns
POST     /v1/admin/billing/grants
POST     /v1/admin/billing/refunds
POST     /v1/admin/billing/disputes/{id}/resolve
GET      /v1/admin/billing/reconcile
GET      /v1/admin/billing/audit
```

### Internal

```text
POST /v1/internal/entitlement/admissions
POST /v1/internal/entitlement/admissions/{id}/capture
POST /v1/internal/entitlement/admissions/{id}/release
POST /v1/internal/payment/settlements/accept
POST /v1/internal/payment/refunds/accept
```

### Provider Webhook

```text
POST /v1/webhooks/payment/{provider}
```

所有 mutation 要求 idempotency key、payload hash、tenant binding、明确 error code 和 audit request id。

### 10.3 Manus API 参考裁决：执行契约可以复用，账务状态不能复用

已核对 Manus API v2 的官方文档。它对 Kokoro 有直接参考价值，但参考边界必须锁死：

| Manus 做得好的部分 | Kokoro 的落地 | 明确不复用的部分 |
|---|---|---|
| 统一成功/失败 envelope、`request_id`、稳定机器错误码 | 所有 User/Admin/Internal/Webhook API 统一 `data`、`meta.request_id`、`error`；补充 `trace_id` 只用于观测 | 不把 `ok` 当作领域状态；业务结果由资源状态和事实表表达 |
| Task 异步生命周期 `running / waiting / stopped / error` | GA/Studio 的 `FeatureExecution` / `StudioJob` 使用自己的执行状态机；Billing 只接收 typed `invocationId` 与受信 execution receipt | 不把 `stopped` 当作 paid，不把 `error` 当作自动 release；Payment/Credit 仍使用各自状态机 |
| `waiting` 携带 event id/type、描述和 JSON Schema | 执行需要用户确认时，Execution 保存 `waitingForEventId` 和 schema；已有 Credit Hold 继续保持 `active`，直到 execution receipt 明确 `accepted` 或 `rejected` | `waiting` 不是支付 pending 的别名，也不是 Redis lock；hold 不因超时轮询自动 capture |
| Webhook 推送 + cursor 查询 | 外部执行结果走签名 webhook inbox；查询 API 采用 cursor；重复/乱序事件由 provider/event id 唯一键与状态机处理 | 不用轮询作为扣费触发器；不把 webhook 到达视为成功事实 |
| endpoint-specific rate limit、429 + backoff/jitter | API Gateway/Redis 做租户/主体/endpoint 限流，返回 `billing.rate_limited` 和 `Retry-After`；MySQL 账务正确性不依赖限流 | 限流不是余额保护；限流失败不能跳过 admission 或改变价格 |
| Structured Output 使用严格 JSON Schema | 对 `ExecutionReceipt`、`ProviderReceipt`、`Admission` 输入使用版本化 schema，服务端二次校验后才允许 capture | LLM 输出、prompt、structured output 不能直接产生金额、grant、capture 或退款 |

#### 执行与计费的正式链路

```text
GA/Studio create execution
  -> Billing admission (idempotent by tenant_id + invocation_id)
  -> active CreditHold / included entitlement reservation
  -> execution running | waiting
  -> execution webhook/event inbox (signed, deduplicated)
  -> accepted + provider receipt -> capture exactly once
  -> confirmed rejected/failed -> release exactly once
  -> timeout/unknown -> keep hold active -> reconciliation
```

`waiting` 场景允许用户确认高成本动作、选择质量档位或补充输入；确认动作本身必须是显式 API command，带
`Idempotency-Key`，并且不能绕过原 admission 重新定价。若确认改变了计费档位，必须创建新的 quote/admission revision，不能修改已存在的 hold 金额。

#### Kokoro 执行契约最小字段

```text
CreateExecution:
  tenantId, billingSubjectRef, payerRef, featureKey, surface,
  invocationId, executionMode, inputSchemaVersion?, requestedModelTier?

ExecutionEvent:
  tenantId, executionId, invocationId, eventId, eventType,
  executionStatus, occurredAt, receiptSchemaVersion, receipt?

AcceptedReceipt:
  invocationId, executionId, providerOperationRef, acceptedAt,
  resultDigest, usageMetadata, signature
```

Billing 仅信任已注册的 GA/Studio service identity、`tenantId` lineage、稳定 `invocationId`、事件签名和 receipt schema；
不信任浏览器、prompt、任意 `amount`、任意 `accountId` 或 provider 原始文本。`usageMetadata` 只用于成本与分析，除非对应的已发布
`PricePolicyRevision` 明确声明，否则不能改变用户应付金额。

#### API 公共规范新增约束

- list/detail API 使用 opaque cursor，并返回 `next_cursor`；不使用 page number 作为账务遍历依据；
- 429 必须包含稳定错误码、`error.request_id`、`Retry-After`，客户端采用指数退避加 jitter；
- webhook 接收先验签、落 inbox、返回 2xx，再异步处理；业务处理失败不能让 provider 无限重推替代 reconcile；
- schema 是 contract version 的一部分，禁止在同一版本静默改变 required 字段；未知 event type 进入 inbox/dead-letter，不得丢弃；
- User/Admin/Internal 继续分离权限和路由，执行确认不提升为 Admin 权限。

### 10.4 关键 schema 约束

```text
CreateQuote:
  tenant_id, payer_ref, product_key/offer_key, feature_key?, quantity, promotion_code?
  -> quote_id, quote_revision, lines[], adjustments[], currency, total, expires_at

CreateOrder:
  quote_id, payer_ref, idempotency_key
  -> order_id, order_number, status, total, payment_collection_id

AuthorizeAdmission:
  invocation_id, billing_ref, billing_subject, feature_key, surface, requested_model_tier?
  -> admission_id, hold_id?, price_revision, amount, mode

CaptureAdmission:
  invocation_id, admission_id, accepted_provider_ref, accepted_at, service_receipt

ReleaseAdmission:
  invocation_id, admission_id, reason, service_receipt
```

任何 caller 不得传 `accountId` 选择任意 payer，不得传最终金额，不得传 RuntimeNamespace，不得传 `siteId`。

## 11. Service / Repository 目标拓扑

```text
kokoro-billing/
├── contract/openapi/v1/                 # 首发 HTTP contract；未来破坏性版本才新增 v2/
├── src/interfaces/http/v1/              # v1 route、DTO、schema、auth adapter
├── src/interfaces/admin/v1/             # v1 Admin manifest/DTO
├── src/application/                     # 不分 v1/v2；用例和事务编排是领域能力
├── src/domain/                          # 不分 v1/v2；状态机、不变量、领域事实
├── src/ports/                           # 不分 v1/v2；repository/provider/outbox ports
├── src/adapters/                        # MySQL、Redis、provider adapter
└── database/schema/                     # 业务表不按 API 版本复制

interfaces/
  http/v1/storefront/ admin/ internal/ webhook/
application/
  commerce/ payment/ entitlement/ reconciliation/
domain/
  commerce/ payment/ entitlement/
ports/
  repositories/ providers/ clock/ idempotency/ outbox/
adapters/
  mysql/ redis/ stripe/ webhook/
```

依赖只允许：

```text
interface -> application -> domain + ports -> adapters
```

当前 V1 service 直接持有 `mysql2.Connection` 的代码不作为目标设计；新实现直接按 ports/UoW 和垂直业务切片构建，不为旧 service 增加兼容适配层。

### 11.1 版本目录规则

- `v1` 只表示 HTTP/JSON、OpenAPI、Admin manifest 和未来 SDK 的外部传输契约；它不是业务领域版本。
- `application`、`domain`、`ports`、`repository`、`database` 不建立 `v1` 子目录，不复制两套业务逻辑。
- 同一资源的 v2 若只是字段适配，可新增 `interfaces/http/v2`，复用同一个 application use case；若业务语义也变化，先建立新的领域能力和 ADR，再决定是否拆分。
- 数据库 schema 使用正常 migration/versioning，不使用 `database/v1`、`database/v2` 表副本；历史事实必须由表结构和 immutable snapshot 表达。
- OpenAPI 文件唯一按 `contract/openapi/v1/openapi.yaml` 组织，不保留平行的迁移期间文件名。
- 首发只创建 `v1`；不创建空的 `v2` 目录、不注册未使用的 v2 route、不做 v1/v2 双写。

## 12. MySQL 与 Redis

### MySQL

- 关键 mutation 使用独立 transaction connection；
- 锁顺序固定：receipt → order/payment source → payer/account → grant/hold → journal → outbox；
- provider 网络调用不在 transaction 内；
- outbox 使用 MySQL lease + `SKIP LOCKED`；
- deadlock 按完整 transaction 有限重试；
- reconcile 可以生成修复 command，但不能直接 UPDATE balance。

### Redis

- 幂等 hint、短租约、缓存、限流、worker coordination；
- Redis down/eviction 时回源 MySQL；
- 不保存余额、redeem 已消费真相、支付成功真相；
- Redis lock 永远不能替代 MySQL row lock/unique key/transaction。

### 12.1 故障处理矩阵

| 故障 | 同步 API | Worker | 数据结果 |
|---|---|---|---|
| MySQL 不可用 | mutation fail closed，query 返回明确不可用 | 不 ack、不丢事件 | 无部分提交 |
| Redis 不可用 | 回源 MySQL，限流可降级 | 使用 MySQL lease/退避 | 正确性不变 |
| Provider timeout | 返回 pending/unknown | 重试或 reconcile | 不猜 capture/refund |
| Webhook 重复 | 返回已接收/已处理 | unique inbox + receipt | 不重复 settlement |
| Fulfillment 失败 | Order 保持 paid/fulfillment_pending | outbox retry | 不重复 grant |
| Deadlock | 可重试完整 transaction | 指数退避 | 不重试单条副作用 SQL |
| Reconcile drift | Admin 返回 drift | 生成受控 repair command | 禁止直接修 projection |

### 12.2 权限与安全边界

```text
User        IAM JWT + tenant match + payer/subject ownership
Admin       operator identity + billing permission + reason + audit
Internal    service identity + typed billingRef/subject binding
Webhook     provider signature + timestamp + provider-account registry
```

- `tenantId` 从受信 IAM/gateway context 得到，不能由 body、query 或 provider payload 选择；
- Admin 的 grant、refund、promotion budget、redeem batch、manual adjustment 都必须记录 operator、reason、request_id 和 before/after snapshot；
- provider raw payload 原样保存但脱敏，签名验证在 JSON parse 前完成；
- redeem code 明文只存在于生成/import 请求和一次性返回，不进入日志、trace、outbox、metrics；
- User 只能读自己的 payer/order/entitlement/credit；Internal 只能执行明确 command，不能调用 Admin mutation；
- 所有跨 tenant lookup 必须在 SQL where 和复合 FK 同时限制 `tenant_id`。

### 12.3 可观测性与运营

必须按 `tenant_id`、context、request_id、order_id、payment_collection_id、fulfillment_id、hold_id、invocation_id` 关联：

- API latency/error/command conflict；
- provider event lag、attempt unknown、refund pending；
- outbox age/dead-letter/retry count；
- active hold age、grant expiry、credit projection drift；
- fulfillment pending、subscription period failure、promotion budget exhaustion；
- MySQL deadlock retry、Redis fallback、reconcile drift。

日志不得包含 payment secret、完整 provider token、redeem code 明文或用户 prompt/产物内容。

## 13. 完整验收矩阵

| 链路 | 必须证明 |
|---|---|
| 购买 | revision snapshot、order totals、payment event、settlement、fulfillment、grant 只发生一次 |
| 多次支付 | collection/attempt 状态可重试，partial/multiple provider attempts 不重复结算 |
| 优惠 | condition、adjustment、usage limit、budget 在并发下不超发 |
| 兑换 | code 不可枚举、单次 redeem、grant 来源可追踪 |
| 使用 | admission/hold/capture/release 与 provider accepted receipt 绑定 |
| 退款 | payment refund、order allocation、entitlement reversal、exposure 可对账 |
| 订阅 | period 乱序/重复/失败续费不重复发放 |
| 过期 | grant/hold expiry 产生事实，余额 projection 可重建 |
| 租户 | tenant mismatch 无法读写；数据库和外部 contract 都使用 tenant 语义 |
| Redis 故障 | 结果与 Redis 是否命中无关 |

## 14. Clean Build 实施顺序

1. 冻结本目标模型、API、SQL 命名和状态机；
2. 为全新数据库创建 Commerce/Payment/Entitlement schema，不创建旧 `payment_checkout`、`subject_id` 兼容字段或旧 route；
3. 直接实现 Commerce Order/Line/Adjustment/Quote；
4. 实现 Payment Collection/Session/Attempt/Refund/Settlement；
5. 实现 Payer/Subject binding、Subscription、Fulfillment、Credit；
6. 实现 Promotion/Redeem、GA/Studio typed admission 和完整 reconcile；
7. 完成 API、SQL、集成、故障恢复和架构测试后，再进行未来部署准备。

当前工作不包含部署、上线、切流、旧 writer 停写或历史数据导入；因为系统尚未上线，也没有需要保留的旧业务事实。

## 15. 最终设计判断

Kokoro Billing 的正确目标不是“Payment + Credit 两个模块再不断加表”，而是：

```text
Commerce：卖什么、订单如何形成、优惠如何解释
Payment：钱如何授权、捕获、退款、拒付
Entitlement：购买后得到什么、如何预留、消耗、过期和撤销
```

三个上下文共用一个 `kokoro-billing` repo，但不共享业务模型、不共享 repository、不互相直写表。
现有 V1 是未上线的探索性实现，不是迁移切片；本文是从零构建时唯一的设计前提。

## 16. 参考实现

- [Medusa Commerce Modules](https://docs.medusajs.com/resources/commerce-modules)
- [Medusa Payment Collection](https://docs.medusajs.com/resources/commerce-modules/payment/payment-collection)
- [Spree Order](https://spreecommerce.org/docs/developer/core-concepts/orders)
- [Spree Adjustments](https://spreecommerce.org/docs/developer/core-concepts/adjustments)
- [Vendure Promotions](https://docs.vendure.io/current/core/user-guide/promotions)
- [Lago](https://github.com/getlago/lago)
- [Kill Bill](https://github.com/killbill/killbill)
- [OpenMeter](https://github.com/openmeterio/openmeter)
- [Manus API v2 Introduction](https://open.manus.ai/docs/v2/)
- [Manus API v2 Task Lifecycle](https://open.manus.ai/docs/v2/task-lifecycle)
- [Manus API v2 Rate Limits](https://open.manus.ai/docs/v2/rate-limits)
- [Manus API v2 Structured Output](https://open.manus.ai/docs/v2/structured-output)
