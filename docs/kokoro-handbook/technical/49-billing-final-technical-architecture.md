# Kokoro Billing 最终业务与技术架构方案（历史版本）

> 本文已由 [50-billing-commerce-rearchitecture.md](50-billing-commerce-rearchitecture.md) 重构并取代。保留用于审计，后续设计不得继续在本文上追加表或服务。

状态：**当前目标架构权威总方案**，2026-08-24。

本文把 31、46、47、48、SQL 规范、API 契约和成熟开源项目复核结果合并为一份可执行的总体方案。
它定义目标边界与实现门禁；“方案已确定”不等于“代码已实现”，当前实现状态以第 14 节为准。

## 1. 设计目标

Billing 必须让以下链路可重试、可审计、可对账、可恢复：

```text
catalog -> quote -> checkout -> provider payment
  -> provider event -> settlement -> acquisition -> fulfillment
  -> entitlement / credit grant -> hold -> capture/release -> journal
  -> refund/reversal -> reconciliation
```

目标不是把支付金额和积分余额放在一张表，而是保存每个业务事实的来源、版本、状态和反向操作。

## 2. 架构裁决

| 决策 | 结论 |
|---|---|
| Git repository | 一个 `kokoro-billing`，Payment 与 Entitlement/Credit 两个 bounded context |
| Runtime process | Billing API、Payment worker、Credit sweeper、Reconcile job、Migration job |
| 业务事实 | MySQL 8.4 + InnoDB；所有关键 mutation 以 MySQL transaction 提交 |
| 协调基础设施 | Redis：幂等 hint、短 lease、缓存、限流辅助、worker coordination |
| 对外租户 | `tenantId` / `X-Kokoro-Tenant-Id`；`site_id` 仅为内部历史物理列 |
| 外部支付 | Provider adapter + inbox/outbox；provider 网络调用不在 MySQL transaction 内 |
| 账务模式 | Prepaid credit 为 V1 主模式；Invoice/tax/accounting 为后续独立扩展，不混入 credit journal |
| 拆仓条件 | 只有数据库 owner、团队、发布生命周期、吞吐/隔离确实独立时才拆 repo/service |

### 2.1 腾讯云与阿里云的复用结论

腾讯云和阿里云的费用中心比单纯的 Stripe Checkout 更接近 Kokoro 要构建的“产品套餐 + 预付资源 + 按量消费 + 多账户运营”体系，
但不应整体照搬云厂商的资源编排和财务系统。两者提供了四个值得直接吸收的成熟概念：

| 云厂商实践 | Kokoro 采用方式 |
|---|---|
| Alibaba Billing Account 独立于登录 Account，并支持一个 billing account 为多个 account 结算 | 正式引入 `PayerAccount/BillingCustomerBinding`；IAM identity 不直接等于 CreditAccount |
| Alibaba 现金余额、credit limit、coupon、voucher 分层，自动/手工 write-off 有财务权限 | Credit grant、promotion、refund exposure 分层；Admin financial permission 与 User API 分离 |
| Tencent 资源包优先按有效期扣减，免费额度/资源包用完后回落按量计费 | `CreditGrant` 使用 expiry/burn priority；允许未来增加 `free -> prepaid grant -> payg` fallback |
| Tencent 明确区分冻结、扣除、解冻，并允许冻结期间暂不返还 | `Hold -> Capture/Release`；provider unknown 保留 active hold，不提前释放 |
| 两者都提供订单、账单、用量明细、资源包/优惠券明细，而不是只显示余额 | Billing read model 分为 order/payment、credit ledger、usage detail、reconcile report，不用余额替代账单 |

Kokoro 的裁决是：

1. **必须增加 `PayerAccount` 这一业务概念**，不能继续让 `subject_id` 同时承担登录主体、用量主体和付款主体；
2. **必须把 hold 当作一等事实**，冻结金额不是已收款、已扣费或已退款；
3. **必须把 grant/优惠/现金支付拆开**。Cash payment 由 Payment provider fact 表示，Kokoro credit 由 CreditGrant 表示，Promotion 只减价；
4. **必须提供可解释的扣减顺序和用量明细**，用户可以知道哪一批 grant 被消耗、何时过期、为什么转入 pay-as-you-go；
5. **必须把账单、订单、付款、用量、资源包视为不同查询模型**，不做一个万能 `billing_history` 表。

参考：[Alibaba Billing Account](https://www.alibabacloud.com/help/en/user-center/fund-account-overview)、
[Alibaba billing methods](https://www.alibabacloud.com/help/en/user-center/product-overview/quickly-understand-the-billing-modes-of-alibaba-cloud-products)、
[Alibaba voucher management](https://www.alibabacloud.com/help/en/user-center/voucher-management)、
[Tencent resource package](https://cloud.tencent.com/document/product/436/36523)、
[Tencent account balance/freeze](https://cloud.tencent.cn/document/faq/555/7442)。

## 3. 业务主体模型

这是整个方案最重要的身份分层：

```text
IAM ExecutionIdentity.subject
  -> BillingSubject(tenantId, kind, opaqueRef)
  -> BillingCustomerBinding
  -> PayerAccount(personal | project | organization)
  -> CreditAccount / PaymentCustomer
```

- **BillingSubject**：产生 usage 的主体，例如用户、项目、Agent run 的计费主体；不等于支付账户。
- **PayerAccount**：实际承担购买和扣费的账户；多个 subject 可以绑定到同一 payer。
- **CreditAccount**：payer 在 Billing 内的积分账户；其余额是 projection。
- **PaymentCustomer**：provider 侧 customer reference 的映射；只保存 opaque external reference。
- **RuntimeNamespace**：GA 执行隔离键，不参与 Billing account selector。

所有绑定都必须包含 tenant lineage。跨 tenant 的同名 opaque ref 不得相互可见。

## 4. Bounded Context 与数据 owner

### 4.1 Payment Context

拥有：

- ProviderAccount、PaymentCustomerBinding；
- CheckoutIntent、ProviderPaymentSession；
- ProviderEventInbox、PaymentSettlement；
- Subscription、SubscriptionPeriod；
- PaymentReversal、Refund、Dispute/Chargeback（目标扩展）；
- PaymentCommandReceipt、PaymentOutbox。

Payment 只产生 money facts，不直接 INSERT/UPDATE CreditGrant、CreditHold 或 CreditJournal。

### 4.2 Entitlement/Credit Context

拥有：

- Package/Offer、immutable Revision、Benefit/GrantTemplate；
- Promotion/Coupon、RedeemCampaign、RedeemCode；
- Acquisition、Fulfillment、EntitlementGrant；
- CreditAccount、CreditGrant lot、CreditHold、HoldAllocation、CreditJournal；
- UsagePriceRevision、BillingAdmission、UsageEvent、UsageSettlement；
- EntitlementCommandReceipt、EntitlementOutbox、Audit、Reconciliation。

Entitlement 接收 PaymentSettlement/PaymentReversal source facts，通过 application port 完成发放/逆向。

### 4.3 不能成为 owner 的模块

IAM 不拥有 Billing balance；Model 不决定最终价格；Agent/Session 不直接扣积分；Web/Gateway 不绕过 Billing API；
Provider 不选择 tenant；Redis 不拥有任何业务事实。

## 5. 核心领域模型

### 5.1 Catalog 与商业配置

```text
Package/Offer (stable key)
  -> PackageRevision (immutable published version)
    -> Price (currency, amount, interval)
    -> Benefit (credit / feature / period)
    -> GrantTemplate (amount, expiry, burn priority, source policy)
```

已发布 revision 不可原地修改。管理员修改套餐必须创建新 revision；checkout、subscription period、grant 都保存 snapshot/ref。

Promotion 只影响交易价格；Benefit/Grant 决定购买后得到什么，禁止用 promotion 伪造积分发放。

### 5.2 Payment、Fulfillment 与 Credit

```text
CheckoutIntent
  -> ProviderPaymentSession
  -> ProviderEventInbox
  -> PaymentSettlement
  -> Acquisition(source_kind, source_ref)
  -> Fulfillment
  -> CreditGrant / EntitlementGrant
  -> CreditJournal + CreditAccount projection
```

`PaymentSettlement` 是“钱已由 provider 确认”的本地事实；`Fulfillment` 是“权益已发放”的独立事实。
两者不能用一个 `paid=true` 字段替代。

### 5.3 Credit 模型

- `CreditGrant` 是可过期、可撤销、按来源隔离的 credit lot；
- `CreditAccount.available` 是可消费 projection；`held` 是 reservation projection；
- `CreditHold` 在 provider send 前预留；
- `HoldAllocation` 记录预留来自哪些 grant；
- `CreditJournal` 记录 grant、debit、release、reversal、expiry、adjustment；
- 消耗顺序默认 `expires_at -> burn_priority -> issued_at -> grant_id`，并由 policy 固化。

核心不变量：

```text
gross = available + held
gross = SUM(active grant.remaining)
hold = captured + released + active_remainder
每个 source fact / hold / invocation 只能产生一次终态 mutation
```

### 5.4 Subscription

Provider subscription 是外部状态映射，不是权益本身：

```text
provider subscription
  -> subscription period
  -> entitlement subscription term
  -> period grant
```

必须显式处理：首次购买、续期、past_due、暂停、取消立即生效、周期结束取消、升级、降级、重试和未知状态。
同一 provider period 只能发放一次；provider 乱序事件不能回退本地已确认终态。

### 5.5 Promotion 与 Redeem

三种 code 分开：

1. Promotion Code：checkout 折扣，不发 grant；
2. Entitlement Redeem Code：按 campaign revision 发放权益；
3. Prepaid Credit Code：redeem code + credit grant template。

code 生成使用 CSPRNG；数据库仅保存 `HMAC(server_secret, normalized_code)`。兑换事务必须锁定 code、校验 campaign/tenant/user 限制、
原子标记 redeemed、创建 acquisition/fulfillment/grant/journal/outbox。Redis 只能做 rate limit/fast path。

### 5.6 商城 Order 与 Payment Collection

商城项目给出的最重要修正是：**Checkout 不是 Order，Payment 不是 Settlement，Promotion 不是一个订单总价字段**。
Spree 把 Order 作为连接 line item、payment、shipment、adjustment 的中心；Medusa 把 PaymentCollection、PaymentSession、Payment
和 Refund 分开，并允许一个 collection 关联多个 payment session/payment。Kokoro 是数字商品商城，虽然暂时没有库存/物流，仍采用同一事实分层：

```text
Order
  -> OrderLine (offer revision + benefit snapshot)
  -> OrderAdjustment (promotion/tax/manual, signed amount)
  -> PaymentCollection (amount due)
    -> PaymentSession (provider authorization surface)
    -> PaymentAttempt/Transaction (authorized/captured/voided/refunded)
  -> Settlement
  -> Fulfillment
```

目标 SQL 表：

```text
payment_order
payment_order_line
payment_order_adjustment
payment_collection
payment_session
payment_attempt
payment_refund
payment_settlement
```

关键规则：

- `payment_order_line` 锁定 offer revision、数量、单价、币种和 benefit snapshot；后续目录改价不影响历史订单；
- `payment_order_adjustment` 保存 promotion/tax/manual 的来源、scope、金额和计算快照，金额可正可负；
- `payment_collection.amount_due` 必须等于 order total，所有 provider attempt 都关联 collection；
- `payment_settlement` 只表示已 capture/settled 的 money fact，不能代替 authorization、void、refund；
- partial payment、multiple attempts、3DS/action required、失败重试和 partial refund 都由 collection/attempt/refund 表表达；
- V1 可以把现有 `payment_checkout` 映射为“一单一行、一 collection、一 provider session”的 compatibility slice，但不能把该切片当成最终商城模型。

参考：[Spree Order model](https://spreecommerce.org/docs/developer/core-concepts/orders)、[Spree adjustments](https://spreecommerce.org/docs/developer/core-concepts/adjustments)、
[Medusa Payment Collection](https://docs.medusajs.com/resources/commerce-modules/payment/payment-collection)、
[Medusa Cart module](https://docs.medusajs.com/resources/commerce-modules/cart)。

## 6. 业务流程与故障语义

### 6.1 Checkout

1. User 请求使用 `tenantId + idempotencyKey`；
2. Billing 读取 published revision，校验 promotion，生成 quote snapshot；
3. MySQL 创建 CheckoutIntent；
4. provider session 在事务外创建，并把 provider ref 回写为可重试状态；
5. 相同 key + 相同 payload 返回原 checkout；不同 payload 返回 conflict；
6. checkout 过期不代表 provider 已退款，必须由 provider event/reconcile 决定最终支付状态。

### 6.2 Webhook / Settlement / Fulfillment

```text
raw body -> signature verify -> provider event inbox
  -> dedupe(provider, external_event_id)
  -> processor
  -> settlement/reversal source fact
  -> outbox
  -> entitlement application service
```

Webhook 处理必须可重复、可乱序、可重放；未知事件保存并标记 ignored/failed，不根据未知 payload 猜测发放。

### 6.3 Model Invocation

```text
AuthorizeModelInvocation
  -> fixed price revision + holdRef
  -> provider call
  -> ModelInvocationAccepted -> capture
  -> confirmed reject -> release
  -> unknown -> hold remains active -> reconcile
```

目标 contract 不接受 caller 传入 `amountMicros`、token 数量、账户 ID 或 RuntimeNamespace。

### 6.4 Refund / Reversal / Chargeback

退款先生成 PaymentReversal；Entitlement 根据原始 acquisition/fulfillment 计算可逆 grant。已消费额度形成
`reversal_exposure`，不能静默把余额改成负数。Dispute/chargeback 未来复用同一 source/reversal 模型，不另造一套 credit mutation。

## 7. Service 与代码架构

```text
src/
  modules/
    catalog/{domain,application,infrastructure,interfaces}
    payment/{domain,application,infrastructure,interfaces}
    fulfillment/{domain,application,infrastructure,interfaces}
    credit/{domain,application,infrastructure,interfaces}
    metering/{domain,application,infrastructure,interfaces}
    promotion/{domain,application,infrastructure,interfaces}
    redeem/{domain,application,infrastructure,interfaces}
    reconcile/{application,infrastructure,interfaces}
  infrastructure/{mysql,redis,providers,observability}
  interfaces/http/{user,admin,internal,webhook}
  bootstrap/
```

依赖方向：

```text
HTTP/Worker/Provider Adapter
  -> Application Service / Command Handler
  -> Domain Policy / Aggregate
  -> Repository Port + UnitOfWork
  -> MySQL/Redis/Provider Adapter
```

规则：

- Controller、worker、provider adapter 不直接写业务表；
- Payment 不 import Entitlement concrete repository；
- Domain/Application 不依赖 Fastify、mysql2、redis、Stripe SDK；
- Repository 按 aggregate/fact 定义窄接口；禁止 `GenericRepository<T>`；
- Query 可以使用专用 read service，但不得绕过 tenant/policy；
- 当前直接持有 `mysql2 Connection` 的代码视为 V1 实现债务，按 Credit→Catalog/Redeem→Payment 渐进迁移。

## 8. API 契约

### User/Storefront

```text
GET  /billing/plans
POST /billing/quotes
POST /billing/checkouts
GET  /billing/checkouts/{checkoutId}
GET  /billing/me/credit-account
GET  /billing/me/credit-ledger
POST /billing/me/redeems
GET  /billing/me/orders
```

### Admin/Operations

```text
GET/POST /admin/billing/packages
POST     /admin/billing/packages/{id}/publish
GET/POST /admin/billing/promotions
GET/POST /admin/billing/redeem-campaigns
POST     /admin/billing/grants
POST     /admin/billing/refunds/{settlementId}
POST     /admin/billing/provider-events/{id}/retry
GET      /admin/billing/reconcile
GET      /admin/billing/audit
```

### Internal

```text
POST /internal/billing/model-invocations/authorize
POST /internal/billing/model-invocations/accepted
POST /internal/billing/model-invocations/{invocationId}/release
POST /internal/billing/payment-settlements/accept
POST /internal/billing/payment-reversals/accept
```

### Webhook

```text
POST /webhooks/billing/{provider}
```

每个 mutation 都要求稳定 idempotency key、payload hash、明确 error code、审计 actor/reason/requestId；金额和积分对外为十进制字符串。

## 9. MySQL 与 Redis 正确性模型

### MySQL

- 每个 application transaction 独占一个物理 connection；
- 行锁顺序固定：receipt/source fact → account → grants → holds/allocations → journal → outbox；
- 余额、hold、allocation、journal 在同一 transaction；
- 事实 append-only，撤销/过期用新事实；
- 外键包含 `(site_id, id)` tenant lineage；
- unique key 保护 provider event、source fact、command、redeem、promotion redemption；
- deadlock 只按有限次数重试整个 transaction，不重试单条 SQL。

### Redis

- 命中：提前返回已知 command result 或减少竞争；
- miss/eviction/down：回源 MySQL；
- lease 只防止 worker 重复工作，不决定业务状态；
- Redis lock 不能替代 MySQL row lock；
- 不在 Redis 保存余额、扣费结果、redeem 真相或不可恢复唯一事实。

### 9.1 目标商城 SQL 形状

以下是目标字段关系，不是要求一次性执行的 migration；每张事实表仍按 expand/backfill/contract 进入 numbered migration：

```sql
payment_order(
  order_id, site_id, order_number, payer_account_id,
  currency, status, subtotal_minor, discount_minor, total_minor,
  quote_snapshot_json, created_at, updated_at,
  UNIQUE(site_id, order_number)
)

payment_order_line(
  order_line_id, site_id, order_id, offer_revision_id,
  quantity, unit_amount_minor, line_subtotal_minor,
  benefit_snapshot_json, created_at,
  FOREIGN KEY(site_id, order_id) REFERENCES payment_order(site_id, order_id)
)

payment_order_adjustment(
  adjustment_id, site_id, order_id, order_line_id NULL,
  source_kind, source_ref, amount_minor_signed, calculation_snapshot_json,
  created_at,
  UNIQUE(site_id, order_id, source_kind, source_ref)
)

payment_collection(
  payment_collection_id, site_id, order_id, amount_due_minor,
  currency, status, created_at, updated_at,
  UNIQUE(site_id, order_id)
)

payment_session(
  payment_session_id, site_id, payment_collection_id, provider,
  external_session_ref, amount_minor, currency, status,
  UNIQUE(site_id, provider, external_session_ref)
)

payment_attempt(
  payment_attempt_id, site_id, payment_session_id, provider,
  external_payment_ref, kind, amount_minor, status, provider_payload_hash,
  UNIQUE(site_id, provider, external_payment_ref, kind)
)
```

SQL 规则：

- `quantity` 使用无符号整数；金额使用带单位的 `BIGINT`，折扣/税/附加费使用有符号 `BIGINT`；
- `total_minor = subtotal_minor + discount_minor + tax_minor + surcharge_minor` 由 application service 计算，并在 order snapshot 中固化；
- 不能用数据库跨行 CHECK 代替 transaction；金额一致性由同一 UoW + reconcile 双重验证；
- `payment_attempt`、`payment_refund`、`payment_settlement` 是不可覆盖的 provider facts，状态投影可以更新但不能删除原事实；
- order line 不复制可变 catalog row 的引用而不保存 snapshot；只存 `offer_revision_id` 不足以解释历史价格/权益。

## 10. 对账、审计与可观测性

Reconcile 至少覆盖：

1. provider event → settlement/refund/dispute；
2. settlement → acquisition → fulfillment；
3. fulfillment → grant/entitlement；
4. grant remaining ↔ allocation/consumption；
5. account projection ↔ journal；
6. active hold ↔ allocation；
7. subscription period ↔ subscription term/grant；
8. promotion budget/redemption count；
9. redeem code state ↔ redeem fact。

所有 drift 生成可定位报告，不允许 Admin 直接改 balance 绕过 journal。Metrics 观察 API latency、provider event lag、outbox age、
dead letter、hold age、reconcile drift、Redis fallback 和 MySQL deadlock retry。

## 11. 安全与权限

- User：IAM JWT + tenant match，只能访问自己的 payer/account/order；
- Admin：独立 operator principal、角色权限、reason、audit；
- Internal：service identity + typed subject/billingRef binding；
- Webhook：raw body timestamped HMAC + provider account registry；payload tenant 只做一致性校验；
- redeem/promotion：枚举防护、速率限制、失败审计、明文 code 不入日志；
- provider secret：只保存 secret reference，不保存明文；
- 所有 API schema 默认拒绝未知字段，禁止 caller 自带 `siteId` 选择租户。

## 12. 非功能门禁

### 正确性

- 同一 source/command/invocation/redeem 100 次重放只产生一个业务结果；
- Redis 全部 key 丢失时，账务结果不变化；
- provider 乱序/重复/延迟事件可最终收敛；
- 任意 grant/hold/journal drift 可定位到 tenant、source、requestId。

### 性能与可用性

- API 与 worker 分离扩展；
- outbox 使用 MySQL lease + `SKIP LOCKED`，不使用 Redis 全局锁串行化；
- 大查询使用 tenant 前导索引和 cursor 分页；
- provider 网络故障不阻塞数据库事务；
- MySQL 不可用时 mutation fail closed，不能返回虚假的成功。

### 运营

- 所有失败状态可重试或进入 reconcile；
- Admin mutation 必须可审计、可追踪、可回放；
- migration 只前进，expand/backfill/contract；
- 每个新增领域能力必须同时提交 schema、OpenAPI、application service、integration test、reconcile 规则和文档。

## 13. 实施阶段

### Phase 0：契约与模型冻结

冻结 Customer/Payer/Subject binding、Package/Benefit、Promotion/Redeem、Subscription 状态和 source fact 命名；不先写代码。

### Phase 1：Repository/Service hardening

建立 UnitOfWork、Repository ports、architecture import tests；先迁移 Credit mutation，确保行为不变。

### Phase 2：Catalog/Promotion/Redeem

增加目标 migration、OpenAPI、campaign budget、redemption fact、HMAC code、兑换事务和 admin/user integration tests。

### Phase 3：Payment lifecycle

补齐 subscription transition、invoice/receipt 边界、refund/dispute source fact、provider reconciliation 和 payment repository ports。

### Phase 4：Feature-first invocation metering

实现 `Authorize → Accepted/Capture → Release`，再删除 GA 对 legacy `subjectId/quantityMicros` usage API 的依赖。

### Phase 5：发布前门禁

只在真正上线前执行旧 writer shadow audit、consumer readiness、rollback exercise、operator sign-off 和切流；这些不是当前本地方案工作。

## 14. 当前状态矩阵

| 能力 | 状态 | 证据 |
|---|---|---|
| MySQL/Redis 基础与 V1 Credit hold/settle/release | 已实现 | `kokoro-billing` tests/integration |
| Payment webhook/settlement/fulfillment/reversal V1 | 已实现 | provider/payment integration |
| User/Admin/Internal/Webhook V1 API | 已实现部分 | OpenAPI parity 与 HTTP tests |
| Repository ports 全量分层 | 未完成 | 47 的 hardening plan |
| Subject→Payer binding | 目标模型，V1 仍以 subject 直连 account | 需 Phase 0/1 migration |
| Promotion/Redeem | 目标方案，未实现 | 46、Phase 2 |
| Order/OrderLine/Adjustment/PaymentCollection 完整商城模型 | 目标方案，V1 仍为 Checkout compatibility slice | 本节、Phase 3 |
| Invoice/tax/accounting | 明确后续边界，未实现 | 本方案第 5.2/12 节 |
| Subscription 完整 lifecycle/dispute | 部分实现，扩展待做 | 现有 provider period + Phase 3 |
| Feature-first invocation contract | 目标方案，未实现 | 38/Phase 4 |
| 部署/旧 writer 停写/真实切流 | 未执行 | 发布前门禁，不是当前实现缺口 |

## 15. 最终判断

当且仅当某能力同时具备：业务旅程、领域 owner、状态机、不变量、SQL migration、API contract、幂等/并发策略、审计/对账、
integration test 和恢复语义，才算 Billing 的“实现闭环”。当前 `kokoro-billing` 的 V1 已具备基础 Payment/Credit 闭环；
完整成熟体系还必须按 Phase 0–4 补齐 Subject/Payer、Promotion/Redeem、Subscription lifecycle、Invoice boundary 和
Feature-first invocation contract，不能用现有 V1 测试替代这些目标能力。

成熟方案参考：

- [Lago](https://github.com/getlago/lago)
- [Kill Bill](https://github.com/killbill/killbill)
- [OpenMeter](https://github.com/openmeterio/openmeter)
- [Medusa promotion/payment concurrency issue](https://github.com/medusajs/medusa/issues/16012)
