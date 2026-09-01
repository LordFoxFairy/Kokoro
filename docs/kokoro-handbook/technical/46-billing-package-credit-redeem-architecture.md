# Billing 套餐、积分与卡密兑换码目标技术方案

> 历史讨论稿。当前 clean-build 领域模型与实现顺序以 [50-billing-commerce-rearchitecture.md](50-billing-commerce-rearchitecture.md) 为准；本文不要求保留旧模型或迁移数据。

状态：目标方案，2026-08-24。本文冻结领域模型、状态机、事务边界、API 契约和演进顺序；当前
`kokoro-billing` 已落地卡密生成/规范化/HMAC 基础，campaign/code persistence、兑换事务和 API 仍未宣称完成。

## 1. 结论先行

`套餐`、`优惠码`、`卡密/兑换码`、`积分钱包` 是四类不同对象，不能使用一张“plan”表或一张“code”表混合：

```text
Package / Offer       = 卖什么
Price                 = 收多少钱
Benefit Grant         = 买到什么权益/积分
Promotion             = 价格优惠，不增加积分
Redeem Code           = 兑换凭证，兑换后产生权益/积分
Credit Wallet/Ledger  = 积分事实、冻结、消费和审计
```

目标归属仍是一个 `kokoro-billing` 仓库、两个 bounded context：

```text
Payment Context       = Checkout / Provider / Settlement / Subscription / Reversal
Entitlement Context   = Package / Price / Benefit / Subscription Term / Redeem / Credit / Metering
```

Payment 只确认钱和退款事实；Entitlement 决定发放什么。任何兑换、赠送、订阅周期发放和购买发放最终都收敛到同一套
`Acquisition -> Fulfillment -> Grant -> Journal` 事实链路。

## 2. 成熟方案调研后的复用裁决

### 2.1 Lago：借鉴 prepaid wallet 与 credit transaction

Lago 将 prepaid wallet、paid/granted credits、top-up、void 和 expiration 分开；付费 credit 只有支付成功后才进入
wallet，free grant 不产生支付。我们采用其核心原则：`paid` 与 `granted` 必须能从来源和账务事实区分，不能由调用方直接修改余额。

不直接复制 Lago 的 Rails/PostgreSQL/ClickHouse 部署；Kokoro 保持 MySQL + Redis，并把 credit lot、allocation、journal
作为 MySQL 事实。

### 2.2 Stripe：借鉴 Coupon 与 Promotion Code 两层模型

Stripe 明确区分 Coupon（折扣规则）和 Promotion Code（用户输入的代码），并支持客户限制、首次交易限制、最低订单金额、
过期时间和 redemption limit。Kokoro 采用同样的两层关系：

```text
PromotionRule (优惠规则) <- PromotionCode (可输入代码)
```

Promotion code 只改变 checkout 的应付金额，不直接发积分、不绕过 payment settlement。

### 2.3 Kill Bill：借鉴 catalog、subscription、credit 与 wallet 的分层

Kill Bill 的成熟边界是 catalog/plan/subscription/payment/credit/wallet 分层，并将 credit 作为 account 级可审计事实。
Kokoro 采用其领域分层，但不引入完整 invoice engine：当前 AI 产品的核心结算单位是 credit grant 和 invocation usage，
不是传统发票行项目。

### 2.4 OpenMeter/Lago/Open-source usage billing：借鉴 ingestion 与 transactional state 分离

usage event 可以未来通过 CloudEvents-compatible ingestion 接入高吞吐事件系统，但 CreditGrant、HoldAllocation、
CreditJournal、Redeem 和 command receipt 仍由 MySQL 掌握。高吞吐事件分析不能成为钱包最终事实。

## 3. 领域对象模型

### 3.1 Package：套餐不是一行可变 Plan

```text
Package                    产品展示和销售聚合
PackageRevision             不可变发布版本
PackagePrice                货币、金额、周期、税价策略
PackageBenefit              revision 绑定的权益条目
BenefitGrantTemplate        兑换/购买后产生什么 grant 的模板
SubscriptionTerm            某租户/主体取得的周期权益
```

`PackageRevision` 发布后不可修改；管理员修改名称、价格、积分量或权益时创建新 revision。既有 checkout、subscription term、
redemption 不回读最新 revision。

一个套餐可以同时包含：

```text
credit: 1,000,000 credit_micros, expires_at = period_end
feature: studio.pro, quantity = 1, expires_at = period_end
quota: model_invocation, quantity = 100, period = subscription_period
```

其中 Credit 是一种 benefit，不把所有权益都硬编码成 `creditMicros`。现有 V1 的 `offer_revision.credit_micros` 保留为
兼容投影；目标扩展以 revision + benefit template 为权威。

### 3.2 Credit：lot、wallet projection、journal 三层

```text
CreditAccount             当前主体/项目的钱包 projection
CreditGrant               一笔可追踪的额度 lot
CreditGrantAllocation     一笔 hold 对 grant 的冻结/消费分配
CreditHold                一次预授权
CreditJournal              append-only 正负分录
```

`CreditAccount` 不是账本，`available_micros`/`held_micros` 可由事实重建。每个 Grant 必须记录：

- `source_kind`：payment、subscription、redeem、promotion、admin、refund_reversal、expiry；
- `source_ref`：稳定来源事实 ID；
- `program_key`：产品/活动用途；
- `original_micros`、`remaining_micros`；
- `burn_priority`、`effective_at`、`expires_at`；
- `revocable`、`metadata_snapshot`。

消耗顺序固定为 `expires_at ASC NULLS LAST -> burn_priority ASC -> issued_at ASC -> grant_id ASC`，不允许前端选择
消耗哪一笔 grant。

### 3.3 三类 Code 必须分开

#### A. Promotion Code：打折码

```text
输入代码 -> 校验限制 -> 锁定/应用 promotion redemption -> checkout quote snapshot
```

结果是 `discount_amount_minor` 或 `discount_percent`，不会产生 CreditGrant。支付失败时不能消耗最终 redemption；
支付成功后才把 redemption 标记为 committed。

#### B. Entitlement Redeem Code：权益兑换码

```text
输入卡密 -> 校验并锁定 code -> 兑换事务 -> Acquisition(source=redeem) -> Fulfillment -> Grant/Feature -> Journal
```

它可以发放积分、套餐周期、feature entitlement 或组合礼包，不需要支付 provider。兑换成功后不可再次兑换；失败事务必须
释放 reservation 或保持可重试状态。

#### C. Gift/Prepaid Credit Code：预付积分卡

这是 Redeem Code 的一种 benefit 模板，而不是另一套钱包：卡密本身只携带兑换凭证，兑换后创建 `source_kind=redeem` 的
CreditGrant。卡面金额、币种、积分量和有效期均来自不可变 batch/template snapshot，不能由客户端提交。

## 4. 卡密生命周期与安全模型

### 4.1 Batch 与单码

```text
RedeemCampaign       活动、适用 tenant/package/segment、预算和时间窗口
RedeemGrantTemplate  兑换成功后发放的 benefit bundle
RedeemCodeBatch      批次、生成策略、总量、失效时间、导出审计
RedeemCode           单个 code 的 hash、状态、batch、归属和 redemption 次数
RedeemAttempt        每次尝试，append-only 审计
Redeem               成功兑换事实，唯一绑定 recipient 和 acquisition
```

数据库不保存可逆明文卡密。生成时只返回/导出一次明文；表内保存 `HMAC(server_secret, normalized_code)`，并使用唯一键
`(tenant_id, code_hash)`。卡密输入先做大小写、空格和连字符规范化，再计算 hash；响应永远不回显完整卡密。

状态：

```text
issued -> reserved -> redeemed
issued -> disabled
issued -> expired
reserved -> issued       # reservation TTL 到期且未提交
reserved -> redeemed     # 同一 redemption transaction
```

`redeemed`、`disabled`、`expired` 是终态；管理员禁用不能撤销已经发放的 CreditGrant，必须走独立 revoke/reversal 命令并
留下原因和审计。

### 4.2 兑换限制

所有限制在同一 MySQL transaction 内读取并锁定：

- campaign `starts_at`/`ends_at`；
- code/batch 最大兑换次数；
- recipient 每人/每 tenant/每 campaign 次数；
- 首次兑换、指定主体、指定 team/segment；
- package/feature 适用范围；
- campaign 总预算（credit micros 或 redemption count）；
- 账户状态和主体 membership；
- 同一 `Idempotency-Key` 与 payload hash。

Redis 可以提前挡住暴力尝试，但不能决定 code 是否可兑换；MySQL row lock、唯一键和 receipt 才是最终依据。

### 4.3 防暴力与运营安全

- User API 只返回统一错误，不泄露 code 是否存在、属于哪个 batch 或剩余库存；
- 边缘层对 IP/subject/tenant/code hash 做 rate limit；Redis 做短 TTL counter；
- Admin 批量生成使用异步 job、一次性下载、operator reason 和审计；不把明文 code 写日志；
- 导出文件使用短期 signed URL/受控 Storage，下载行为可审计；
- code batch 生成使用 CSPRNG，不用 UUID 顺序值或可猜序列；
- 兑换成功事件 payload 只含 redemption ID 和 benefit summary，不含明文 code。

## 5. 推荐 SQL 模型（目标扩展，不立即迁移）

所有表继续使用 `site_id` 内部列名，但跨租户引用使用 `(site_id, id)` 复合键。建议新增：

```text
entitlement_package
entitlement_package_revision
entitlement_package_price
entitlement_package_benefit
entitlement_benefit_grant_template
entitlement_promotion
entitlement_promotion_code
entitlement_promotion_redemption
entitlement_redeem_campaign
entitlement_redeem_grant_template
entitlement_redeem_code_batch
entitlement_redeem_code
entitlement_redeem_attempt
entitlement_redeem
entitlement_redeem_benefit
```

关键约束：

```sql
UNIQUE (site_id, package_key, revision)
UNIQUE (site_id, promotion_code_normalized)       -- 全局公开码
UNIQUE (site_id, code_hash)
UNIQUE (site_id, redeem_code_id)                  -- 防重复兑换事实
UNIQUE (site_id, recipient_kind, recipient_ref, campaign_id)
UNIQUE (site_id, source_kind, source_ref, program_key)
```

敏感 code 的唯一键可以使用 `code_hash BINARY(32)`；不存明文。所有引用 `package_revision_id`、`campaign_id`、`batch_id`、
`redeem_code_id` 的关系都必须包含 `site_id` 复合 FK。

### 5.1 价格与权益快照

Checkout 创建时保存：

```json
{
  "packageRevisionId": "...",
  "priceId": "...",
  "currency": "USD",
  "listAmountMinor": "1999",
  "discountAmountMinor": "500",
  "payableAmountMinor": "1499",
  "promotionCode": "WELCOME25",
  "benefitSnapshot": [{"kind":"credit","amountMicros":"1000000","expiresAt":"..."}]
}
```

Provider 只接受 `payableAmountMinor`；成功 webhook 只引用 checkout/settlement，Entitlement 按 snapshot 或 immutable revision
发放，不能重新根据当前套餐计算。

## 6. 事务闭环

### 6.1 购买套餐

```text
User -> quote(package revision, optional promotion code)
     -> reserve promotion redemption (可选)
     -> create checkout + immutable quote snapshot
     -> provider payment
     -> signed webhook inbox
     -> settlement succeeded
     -> commit promotion redemption
     -> Acquisition(payment settlement)
     -> Fulfillment(package benefits)
     -> CreditGrant + Journal + Outbox
```

若支付失败/checkout 过期，promotion reservation 释放；若 provider 结果 unknown，优惠 reservation 和权益都不能自行
确定为成功，进入 reconciliation。

### 6.2 兑换卡密

```text
POST /billing/redeem
  1. authenticate User + tenant context
  2. normalize code, compute HMAC hash
  3. INSERT redeem_attempt / command receipt
  4. SELECT redeem_code, campaign, recipient counters FOR UPDATE
  5. validate window, quota, eligibility, status
  6. mark code redeemed
  7. create Redeem(source fact)
  8. create Acquisition/Fulfillment
  9. create CreditGrant/FeatureGrant + Journal + Outbox
 10. commit; return redemption result
```

所有步骤在一个 MySQL transaction 内完成；不在 transaction 内调用 Redis、provider、邮件或外部 webhook。

### 6.3 退款、撤销和兑换码

- 支付退款：只逆向未消耗的 payment grant；已消费部分形成 reconciliation exposure；不能直接把 account balance 改成 0；
- 管理员撤销兑换权益：创建 `revoke` fact 和负 journal，按 grant remaining 与 active hold 规则处理；
- 禁用未兑换 code：只改变 code 状态，不影响历史 redemption；
- campaign 结束：禁止新兑换，不删除 code、attempt、redemption 和 grant；
- 兑换发放失败：整个事务回滚；如果未来拆成异步发放，必须用 durable fulfillment 状态和 reconciliation，不将 code 标记为
  redeemed 后再依赖普通 HTTP 补偿。

## 7. API 面设计

### User

```text
POST /billing/redeem
GET  /billing/me/redemptions
POST /billing/checkout/quote       # 可选 promotionCode，纯计算/短期 quote
```

User 不可提交 `tenantId`、accountId、grant amount、package benefit 或 code batch；这些来自认证上下文和服务端模板。

### Admin

```text
POST /admin/billing/packages
POST /admin/billing/packages/{packageId}/revisions
POST /admin/billing/promotions
POST /admin/billing/promotion-codes
POST /admin/billing/redeem-campaigns
POST /admin/billing/redeem-campaigns/{campaignId}/batches
POST /admin/billing/redeem-codes/{codeId}/disable
GET  /admin/billing/redemptions
GET  /admin/billing/redeem-campaigns/{campaignId}/stats
POST /admin/billing/grants/{grantId}/revoke
```

批量生成接口默认异步：返回 `generationJobId`，明文导出只在受控一次性下载流程提供。所有高风险动作要求
`Idempotency-Key`、operator、reason、requestId 和 audit event。

### Internal

```text
POST /internal/billing/entitlements/resolve
POST /internal/billing/credits/authorize
POST /internal/billing/credits/capture
POST /internal/billing/credits/release
```

这些是对现有 usage/model-invocation 目标 contract 的领域命名整理；不允许 Model/Agent 直接创建 grant 或修改 ledger。

## 8. 幂等、并发与状态不变量

1. 同一 code 只能有一个 committed redemption。
2. 同一 `(tenant, recipient, campaign)` 的 recipient quota 在数据库锁内判断。
3. 同一 purchase/redeem source 最多一个 Acquisition/Fulfillment。
4. 同一 grant 的 remaining、allocation、journal 变化必须在一个 transaction 内提交。
5. 同一 promotion code 的 redemption count 不可超过 promotion/coupon max；数据库条件更新或锁定行负责最终限制。
6. 任何失败重试都比较 payload hash；同 key 不同 payload 返回 conflict。
7. Redis 故障只能降低吞吐或增加数据库竞争，不得造成重复兑换、超发积分或折扣绕过。
8. outbox 至少一次投递，消费者按 source fact 幂等；不通过发布事件作为权益成功的唯一证据。
9. 兑换码明文永不进入 MySQL、日志、metrics、trace 或 outbox payload。
10. 所有跨租户 FK 都必须包含 `site_id`，schema integration test 自动枚举校验。

## 9. 实施阶段与门禁

### Phase A：先冻结模型（当前）

- 保留 V1 `entitlement_offer`/`entitlement_offer_revision` 兼容读取；
- 确定 Package/Price/Benefit 的 target OpenAPI 与 JSON snapshot；
- 确定 promotion 与 redeem 的错误码、状态机和 recipient identity；
- 不新增只有表没有完整 command/API/test 的“占位实现”。

### Phase B：Package/Benefit expansion

- 新增 package revision 与 benefit template；
- checkout quote 支持多个 benefit，现有 `credit_micros` 变为兼容投影；
- payment fulfillment 按 immutable snapshot 发放；
- 完成跨租户 FK、replay、refund/revoke 对账。

### Phase C：Promotion

- 先实现服务端 quote 校验和 checkout snapshot；
- 再接 Stripe provider promotion code（若实际 provider 能力足够），但本地 Promotion 事实仍由 Billing 保存；
- 支付成功前 reservation，支付终态后 commit/release；
- 不允许 provider 返回的折扣金额成为唯一账务证据。

### Phase D：Redeem Code

- 先做 single-use entitlement code，再做 batch generation；
- 先做信用积分礼包，再扩展 feature/套餐周期礼包；
- 完成暴力保护、一次性明文导出、admin 审计、quota、撤销和 reconciliation；
- 最后再评估 gift/prepaid code 是否需要外部销售库存或财务对账适配器。

### Phase E：成熟度门禁

- MySQL fresh migration；
- User/Admin/Internal OpenAPI parity；
- 并发兑换压力测试（同码、同 campaign、同 recipient、Redis 故障）；
- property/invariant test：不超发、不重复、不跨租户、不泄露明文；
- 退款、撤销、过期、provider unknown 的 source-level reconciliation；
- 只有上述证据齐全后，才将扩展从 planned 标记为 implemented。

## 10. 明确不做的错误设计

- 不用 `plan.credit_micros` 继续承载所有未来权益；
- 不把 promotion code 当成 credit code；
- 不把卡密明文存库或用可逆加密代替 hash；
- 不在 Redis 中扣积分、计 redemption 最终次数或保存唯一成功事实；
- 不让客户端传 `amountMicros`、benefit 数量、accountId 作为发放依据；
- 不用删除 code、grant 或 redemption 来实现撤销；
- 不把 Stripe/Lago/Kill Bill 的整套基础设施直接引入当前首发栈；
- 不在当前只有方案阶段提前宣称兑换码能力已上线。

## 11. 参考资料

- Lago GitHub：<https://github.com/getlago/lago>
- Lago wallet/prepaid credits：<https://getlago.com/docs/guide/wallet-and-prepaid-credits/wallet-top-up-and-void>
- Kill Bill GitHub：<https://github.com/killbill/killbill>
- Kill Bill Credit API：<https://apidocs.killbill.io/credit>
- Kill Bill architecture/docs：<https://killbill.github.io/killbill-docs/>
- Stripe Coupons and Promotion Codes：<https://docs.stripe.com/billing/subscriptions/coupons>
- Stripe Promotion Code API：<https://docs.stripe.com/api/promotion_codes>
- OpenMeter：<https://github.com/openmeterio/openmeter>
