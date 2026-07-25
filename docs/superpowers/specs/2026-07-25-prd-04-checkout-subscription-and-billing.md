---
artifact: product-requirements-document
prdId: PRD-04
version: "1.0"
created: 2026-07-25
status: internal-review-active
scope: checkout-order-payment-subscription-renewal-refund-dispute-reconciliation
accountableProductRole: Commerce Product Lead
mandatoryCosigners: [Finance, Tax, Legal, Risk, Security, Support, Catalog, Credit, QA]
engineeringOwner: team:payment-billing-engineering
qaOwner: team:payment-billing-quality
supportOperationsOwner: team:finance-operations
namedOwnerAssignmentStatus: assigned-team-responsibility-ids
implementationAuthorized: false
---

# PRD-04：Checkout、Subscription 与 Billing

## 1. Overview

### Problem

真实支付是成熟但高风险的异步领域：浏览器 redirect 不等于付款成功，webhook 可能重复、乱序或丢失，同一
Order 的 late success 可能形成重复履约，退款期间用户可能继续消费对应 Credit，dispute 又是本地系统不能拒收
的外部资金事实。若把 Provider PaymentIntent 或一个万能 status 当业务真源，会产生重复收费、重复 Grant、
退款与权益竞态以及无法对账的问题。

### Solution

Payment 作为可选 acquisition adapter 接入 PRD-03 的统一 Fulfillment 后半链。Kokoro 分离 Quote、Order、
SettlementObligation、CheckoutSession、PaymentAttempt、ProviderFact、PaymentAllocation、Fulfillment、Refund、
Dispute、Payout/Settlement 与 Subscription cycle。V1 仅允许一个 Order obligation 对应一笔 exact automatic
capture；所有 Provider 事实原样追加，但只有分配到 obligation 的 capture 能触发一次 Fulfillment。退款在调用
Provider 前同时预留 money 与 source Grant reversal，防止继续消费。

### Users and stories

| ID | User story | Priority |
|---|---|---|
| PAY-US-01 | 用户能看到准确 Quote，完成 Checkout/3DS/redirect，并在失联后恢复真实 Payment 状态 | P0 if-enabled |
| PAY-US-02 | 用户不会因 duplicate/late webhook 或重试收到重复收费/权益 | P0 |
| SUB-US-01 | 用户能理解 trial、renewal、upgrade/downgrade、cancel、grace、past_due 的生效时间和权益 | P0 |
| REF-US-01 | 用户能看到退款资格、来源、金额、权益影响、pending/failed/succeeded 和原路退款 | P0 |
| DSP-US-01 | 用户/Finance 能追踪 dispute、evidence、won/lost/late outcome 与权益处理 | P0 |
| OPS-US-01 | Operator 能对账和恢复 unknown，而不改 Provider Fact、Journal 或直接重放 IO | P0 |

## 2. Enablement、Goals and Non-Goals

### Enablement gate

PRD-04 默认 `not_enableable`。一个 Site 只有同时发布以下 revision/evidence 后才能从 redeem-only 切换：

```text
SalesJurisdictionPolicyRevision
MerchantAccount + PaymentProviderAccount production binding
currency/tax/rounding/invoice/refund/dispute policies
Offering/Quote/Subscription policy revisions
provider sandbox + production certification
Finance/Support/Reconciliation runbooks and owner
payment/refund/dispute notification and data-retention policies
```

具体销售国家/地区、税务责任、credit-pack 税务分类不能从 Stripe/Lago/其他项目类推，由 Legal/Tax 对目标 Site
发布。缺任一项时 route/bootstrap/API/Admin/secret dependency 四层关闭。

### Goals and metrics

| Metric | Target |
|---|---:|
| duplicate capture/Payment allocation/Fulfillment/Grant | 0 |
| redirect success 被写 paid | 0 |
| unknown Attempt 期间发起第二次可能收费 IO | 0 |
| source Grant 未 encumber 即提交 refund | 0 |
| webhook duplicate/乱序导致状态回退或重复 effect | 0 |
| refund/dispute external fact 被本地余额 invariant 拒绝 | 0 |
| Payment→Fulfillment→Grant 与 Usage/Refund 双向追踪 | 100% |
| reconciliation variance 无 owner/SLA | 0 |

### Non-Goals

- V1 不支持 split tender、multiple provider payments、partial/manual/incremental capture、authorization-only、
  stored-value cash-out 或跨 currency netting。
- V1 一个 Order 只有一个 exact automatic capture obligation；超出部分进入 overpayment reconciliation。
- 不自建完整会计总账、税引擎、Payout 银行系统或发卡系统。
- Payment 不复制 Catalog、Subscription、Entitlement、Credit、Rating 或 Redemption 后半链。
- Provider downtime 不允许静默切换 Merchant/ProviderAccount 继续旧 Checkout/Refund。

## 3. Product Model and Ownership

```text
MerchantAccount
PaymentProvider / PaymentProviderAccount
OfferingQuote
Order
OrderSettlementObligation(orderId,purpose,cycleKey,amountDue,currency)
CheckoutSession
PaymentAttempt
ProviderWebhookInbox / ProviderObjectMap / ProviderFact
Payment                 // confirmed capture facts projection
PaymentAllocation       // successful capture → obligation allocation
FulfillmentTransaction  // unique order/purpose/cycle
Invoice / InvoiceLine / Receipt
Subscription / SubscriptionBillingBinding / RenewalIntent / FulfillmentCycle
RefundRequest / RefundReservation / FulfillmentReversalReservation / RefundFact
DisputeFact / DisputeCase / RecoveryExposure
ProviderBalanceTransaction / Payout / Settlement / ReconciliationCase
```

- Payment module 独占 Provider IO/facts、money reservation/allocation/refund/dispute/settlement。
- Catalog owns Offering/Price；Commerce core owns Order/Fulfillment/Subscription；Credit owns Grant/Journal/Hold。
- Payment 是一个或多个 confirmed capture facts 的投影，不复制 Provider PaymentIntent state。
- Provider secret 只存 Secret Manager；领域保存 ref、key/account metadata、environment 和 revocation epoch。

## 4. Quote、Order and Checkout

### 4.1 OfferingQuote

Quote 冻结 SiteRelease、BillingAccount、Offering/Price、ISO currency+integer minor unit、Merchant、eligible provider
accounts、routing policy、FulfillmentProgram、RefundAllocationPolicy、tax inclusive/exclusive、rounding snapshot、
experiment decision、expiry 和 digest。Price/Offering effective intervals 不重叠；过期或 current kill switch 拒绝，
不自动换 Merchant/货币/价格。

### 4.2 Order and obligation

- Order 保存用户购买意图；paymentStatus、fulfillmentStatus、disputeStatus 为正交 projection，不用万能 status。
- V1 创建一个 `OrderSettlementObligation(amountDue=Order total,purpose,cycleKey)`。
- `PaymentAllocation` 在锁内分配 successful capture；硬不变量：
  `sum(allocated captures) <= obligation.amountDue`，且 `FulfillmentTransaction(orderId,purpose,cycleKey)` 唯一。
- 每个成功 ProviderFact 都保存，但未分配部分只能 `overpayment/reconciliation_required`，不能触发第二 Grant。

### 4.3 Checkout and attempts

- CheckoutSession 冻结 exact Quote/Order/Merchant/ProviderAccount/client return intent；Site Web 不提交自由 account。
- PaymentAttempt ordinal 串行；存在 processing/unknown Attempt 时禁止新 charge Attempt。
- requires_action/3DS/redirect 只推进 attempt 状态；浏览器 return page 轮询本地 Order/Payment receipt，不写 paid。
- user retry 在明确 failed/canceled 后创建下一 ordinal；同 attempt provider IO key 永远稳定。

## 5. Provider Integration and Facts

### 5.1 Webhook inbox

- endpoint 由 PaymentProviderAccount/environment 精确绑定，验证签名、timestamp/replay policy 和 body limits；快速
  durable persist 后 ack，再异步 normalize/reduce。
- Inbox unique `(providerAccountId,environment,providerEventId)`；原始 payload 加密、PII classified、短 retention、
  JIT audited access。Admin 默认只看 normalized whitelist。
- ProviderObjectMap unique `(providerAccountId,environment,objectType,externalId)`，禁止仅按 provider 字符串去重。

### 5.2 Retrieval and reducer

- adapter 不依赖 webhook 顺序；使用 event identity、canonical object retrieval、occurred/received time、object
  version/priority、本地 aggregate version 归约。无法确定进入 unknown/reconciliation，不猜 terminal。
- ProviderFact append-only；late success/failure/refund/dispute 创建新 fact/projection，不覆盖历史。
- Risk/Restriction 在 IO 后不能拒收 ProviderFact。已付款但风险阻断履约显示 paid + fulfillment review，并走正式
  refund/review，不伪装 failed。

### 5.3 Successful capture allocation

```text
normalized successful capture fact
→ lock Order + OrderSettlementObligation + existing PaymentAllocations
→ allocate up to exact outstanding amount
→ if obligation becomes satisfied, create unique FulfillmentTransaction
→ otherwise overpayment/variance ReconciliationCase
```

late double-success、duplicate Provider objects 和 operator recovery 都必须经过同一 allocation constraint。

## 6. Subscription Lifecycle

### 6.1 Billing authority and cycles

- `SubscriptionBillingBinding.authority = payment_provider | platform | none`，provider account/schedule/revision 精确
  冻结；同 period 只有一个 authority 能创建 RenewalIntent/charge。
- 每个 cycle 唯一 `(subscriptionId,periodStart,periodEnd,authorityRevision)`，产生独立 Invoice/obligation/
  Payment/Fulfillment source provenance。
- authority migration 是显式 workflow：停止旧 schedule、证明无 pending/unknown cycle、发布新 binding；不能
  因 provider health 直接 fallback。

### 6.2 User-visible policies

- trial：开始/结束、是否需 payment method、转 paid 时间和未成功后行为由 TrialPolicy 冻结。
- upgrade：immediate 或 next-term；即时方案先展示 proration Quote/Entitlement/Credit change，再确认。
- downgrade：默认 next-term，当前权益到 period end；无法兼容的 Project/feature 提前解释。
- cancel-at-period-end：停止 renewal，不提前删除已取得 term/grant；允许在 cutoff 前 resume。
- payment failure：processing→past_due→grace/paused/canceled 由 Dunning/Grace revision；邮件失败不改变状态。
- Plan/Price revision 变化只影响明确的 future cycle，需 notice/cutoff/consent policy；不改旧 Invoice/Grant。
- payment method management 通过 provider tokenized flow；Kokoro 不接触 PAN/CVC。

## 7. Refund and Entitlement Reversal

### 7.1 Eligibility and exposure

主动 refundable amount 至少扣除：

```text
alreadyCapturedUsage
+ activeCommittedAllocationMaximum
+ unknownAttemptExposure
+ successfulRefund
+ activeRefundReservation
+ knownDisputeExposure
```

不能只看当前 BalanceProjection。Policy 冻结 partial allocation、cooldown、non-refundable fee/tax（依法）、
Subscription/term effect 和 user explanation。

### 7.2 Dual reservation transaction

提交 Provider refund 前，同一 PlatformUnitOfWork：

```text
lock Payment/source Fulfillment/Grant/HoldAllocation
→ compute available/reserved/committed/unknown source exposure
→ create RefundReservation(money)
→ create FulfillmentReversalReservation(source rights)
→ journal available source amount: available → reversal_reserved
→ mark committed/unknown allocation as outstanding RecoveryExposure
→ persist provider refund intent/idempotency/outbox
→ commit
→ call original ProviderAccount/ref
```

- pending/unknown 继续 encumber，禁止同 amount 再 refund 或消费。
- succeeded：reversal_reserved→revoked；Term/Entitlement/Credit source-specific reversal，exposure reconcile。
- failed：释放 reservation，按 Grant 当前 expiry/revocation 状态回 available/expired/revoked，不能复活。
- refund 只能原路；原 account unavailable 进入 unknown/reconciliation，不切其他 provider。
- refund pending 与 dispute 并发时保留两个事实和统一 exposure，不将一个覆盖另一个。

## 8. Dispute、Settlement and Reconciliation

- Dispute states：open、under_review、won、lost、late_won、closed；withdrawn 不自动等于 won。
- open 时按 `DisputeEncumbrancePolicy` 冻结剩余 source Grant/term；won 释放或恢复至当前有效目的账户；lost 执行
  source reversal；late outcome 追加新 fact/correction。
- 外部 DisputeFact 无论本地 refundable/余额是否足够都必须入账；超额形成 RecoveryExposure/RiskCase，不扣
  其他 source、不伪造负余额。
- Finance evidence submission、deadline、representment、user communication 与 data retention 由 provider/jurisdiction
  policy 冻结。
- ProviderBalanceTransaction/Payout/Settlement 与 Order 状态分离；ReconciliationCase 保存 expected/observed、
  variance、owner、SLA、evidence、append-only Resolution/adjustment refs。

## 9. User-visible States and Recovery

| Surface | States | Recovery |
|---|---|---|
| Checkout | ready、requires_action、processing、succeeded、failed、canceled、expired、unknown | complete action/wait/query/new attempt only after safe terminal/Support |
| Payment | pending、paid、overpayment_review、refund_pending、partially_refunded、refunded、reconciliation_required | receipt/wait/Support |
| Subscription | pending、trialing、active、change_scheduled、past_due、grace、paused、cancel_scheduled、canceled、expired | pay/update method/resume/cancel/view date/Support |
| Refund | requested、reserved、submitted、pending、succeeded、failed、canceled、unknown | wait/query/repair original route/Support |
| Dispute | open、under_review、won、lost、late_won、closed | provide evidence/wait/appeal or Support where allowed |

每个状态显示 money、rights/Credit effect、是否可重试、freshness、deadline、owner；Order paid 不代表 Fulfillment
succeeded，Refund request 不代表 funds returned。

## 10. Admin、Support and Controls

- 专用 surfaces：Merchant/ProviderAccount certification、Quote/Order/Payment timeline、Subscription cycles、Refund/
  Dispute、Settlement/Reconciliation。普通 ResourceTable 不执行 money mutation。
- refund、manual reconciliation adjustment、provider binding/migration、mass action 要 reason、step-up、immutable
  parameter digest、maker-checker；request/approve/execute 不能同一 operator。
- Support 通过 safe projection 和 typed command；不能 mark paid/refunded、创建假 Payment/Refund、改 Grant/Journal、
  重放 webhook 或调用另一 Provider。
- BreakGlass 不能绕过 allocation/refund reservation/domain command；Provider raw payload/PII 需 JIT field grant。

## 11. Edge Cases

| Scenario | Expected behavior |
|---|---|
| redirect success、webhook 未到 | processing/unknown，轮询 receipt，不履约 |
| webhook duplicated/out of order | one Inbox/facts reducer，no state regression/effect duplicate |
| first Attempt unknown，user retries | block new charge，retrieve/reconcile original |
| two late successful captures | allocate only obligation outstanding；one Fulfillment，excess reconciliation |
| paid but Fulfillment transient failure | paid + fulfillment pending_retry；retry fulfillment, not charge |
| refund reserved then user starts Run | source available already encumbered，Admission cannot spend it |
| provider refund unknown | reservations remain；no second refund/reversal |
| dispute exceeds remaining Grant | accept external fact，RecoveryExposure，no other-source debit |
| Site switches redeem-only | new Checkout disabled；historical Refund/Dispute/Reconcile remains |

## 12. Acceptance Criteria

### AC-PAY-01 — Redirect is not payment proof

```gherkin
Given a user returns from Provider with a success-looking redirect
When no normalized successful capture fact has been allocated
Then Order remains processing or unknown and Fulfillment does not start
```

### AC-PAY-02 — Late double success allocates once

```gherkin
Given two distinct successful Provider facts arrive for one exact Order obligation
When reducer and allocation run concurrently or out of order
Then at most the amount due is allocated and exactly one FulfillmentTransaction succeeds
And excess money creates overpayment reconciliation without a second Grant
```

### AC-PAY-03 — Unknown blocks duplicate charge

```gherkin
Given PaymentAttempt ordinal one has unknown Provider outcome
When browser or operator requests another charge attempt
Then the request is denied until canonical retrieval/reconciliation proves a safe terminal
And the original provider operation key is never blindly replayed
```

### AC-REF-01 — Refund reserves rights before IO

```gherkin
Given a Payment source has available Credit plus committed and unknown allocations
When a refund is accepted
Then money and source-right reversal reservations commit before Provider IO
And reserved available Credit cannot fund a new Hold
And committed/unknown exposure is included in eligibility and RecoveryExposure
```

### AC-REF-02 — Failed/unknown refund handling

```gherkin
Given Provider refund is unknown or later fails
When reconciliation runs
Then unknown remains encumbered without duplicate refund
And confirmed failure releases source amount only to its current available/expired/revoked destination
```

### AC-DSP-01 — External dispute cannot be rejected

```gherkin
Given a signed dispute fact exceeds local refundable amount or remaining source Grant
When webhook is reduced
Then the fact is persisted and projected
And excess becomes RecoveryExposure/RiskCase without debiting unrelated sources or creating fake balance
```

### AC-SUB-01 — One billing authority per cycle

```gherkin
Given Subscription authority migrates from provider to platform
When a cycle boundary occurs
Then only the active binding revision can create RenewalIntent/charge
And pending/unknown old-authority operations block migration or enter reconciliation
```

### AC-PAY-04 — Redeem-only disable with historical duties

```gherkin
Given a Site disables new Payment acquisition after historical Payment facts exist
When users invoke new Checkout and a historical refund/dispute arrives
Then new Checkout fails closed without Provider IO
And the historical original-account refund/dispute/reconciliation workflow remains operational
```

## 13. Provider Certification and Launch Gate

每个 ProviderAccount/environment 必须在 sandbox/production-like 环境证明：signature/replay、duplicate/乱序 webhook、
object retrieval、3DS/redirect lost response、timeout/late success、refund pending/failed/unknown、partial refund、
dispute open/won/lost/late、secret rotation/revocation、rate limit、provider outage、settlement variance。证据绑定 adapter/
SDK/API version、merchant/account、currency/capture capability、source/image/config digest 和有效期。

No-Go：依赖 webhook 顺序、redirect 写 paid、late success 重复 Fulfillment、refund 未冻结 source Grant、unknown
自动重试、税务/地区/capture mode 未冻结、无真实 Provider certification、或 Payment/Redemption 复制后半链。

## 14. Dependencies、Risks and Milestones

| Risk/Dependency | Mitigation |
|---|---|
| Provider object 被当领域状态 | append-only normalized facts + retrieval reducer + local projections |
| late success 重复履约 | obligation/payment allocation + unique fulfillment cycle |
| refund 与 Credit 消费竞态 | money + source reversal dual reservation transaction |
| dispute 打破本地 invariant | always ingest external fact + RecoveryExposure |
| tax/legal scope 未知 | not-enableable until Site SalesJurisdictionPolicy approved |
| 多 Provider 复杂度过早 | V1 exact automatic capture, one obligation/account, unsupported modes fail closed |

Wave 2B 在 PRD-03/Wave 2A 后实现；启用前完成真实 Provider、Finance、Support、Security、Legal/Tax 与 profile delta
certification。未启用 Site 不依赖 Provider secret/runtime。参考成熟系统的 Payment/Capture/Refund 分离、wallet
traceability 和 webhook reducer 思想，但 Kokoro 的法律/产品 policy 只来自自身已批准 revision。

## 15. External Design References

- [Stripe webhook guidance](https://docs.stripe.com/webhooks)：事件可能重复/乱序，入口快速持久化后异步处理；
  Kokoro 进一步要求 canonical retrieval + append-only ProviderFact reducer。
- [Stripe refunds](https://docs.stripe.com/refunds) 与
  [disputes](https://docs.stripe.com/disputes/how-disputes-work)：参考 pending/failed/unknown、原路退款与 dispute
  独立事实；本地 Grant reservation/reversal 是 Kokoro 自己的闭环。
- [Medusa Payment](https://docs.medusajs.com/resources/commerce-modules/payment/payment)、
  [Payment Collection](https://docs.medusajs.com/resources/commerce-modules/payment/payment-collection) 和
  [Order Transactions](https://docs.medusajs.com/resources/commerce-modules/order/transactions)：参考 Payment/
  Capture/Refund 与 Order balance 分离；Kokoro V1 有意收窄为一笔 exact automatic capture obligation。
- [Lago prepaid credit traceability](https://getlago.com/docs/guide/wallet-and-prepaid-credits/traceability)：用于验证
  Payment source→Grant→Consumption→Refund 的双向可解释性。

外部产品不是 Kokoro 的法律、税务或状态 authority；具体销售地区、Merchant、税务与 Provider 能力必须由
Site 自己的已批准 policy/certification 冻结。

本文批准不授权实现，也不修改 GA runtime。
