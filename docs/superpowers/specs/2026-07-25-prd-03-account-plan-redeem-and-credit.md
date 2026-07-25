---
artifact: product-requirements-document
prdId: PRD-03
version: "1.0"
created: 2026-07-25
status: internal-review-active
scope: account-plan-catalog-redeem-subscription-entitlement-credit-usage
accountableProductRole: Commerce Product Lead
mandatoryCosigners: [Finance, Risk, Security, Legal, Support, Catalog, Credit, Usage, QA]
engineeringOwner: team:commerce-core-engineering
qaOwner: team:commerce-quality
supportOperationsOwner: team:commerce-support-operations
namedOwnerAssignmentStatus: assigned-team-responsibility-ids
implementationAuthorized: false
---

# PRD-03：Account、Plan、Redeem 与 Credit

## 1. Overview

### Problem

首发 Site 可以不接真实支付，通过 Card Code 让用户取得与购买相同的 Subscription、Entitlement 和 Credit。
当前三桶实现虽能完成 daily/period/permanent 扣减，却把 mutable balance 当 authority，无法精确回答积分来自哪次
兑换、某次消费使用哪些 Grant、撤销/退款应影响哪一来源，也无法安全处理第二张订阅卡并发叠加、unknown
Provider Attempt、长期 Hold 和失联恢复。

### Solution

建立标准 Catalog→Fulfillment→Subscription/EntitlementGrant/CreditGrant 后半链。Payment 和 Redemption 保持
不同 acquisition fact；Redemption 不制造 Order/Payment/Invoice/Refund。Credit authority clean replace 为
`CreditGrant + append-only CreditJournal + CreditHold/HoldAllocation`，三桶只作为用户读模型。Account 页面统一
解释套餐、有效期、权益、余额来源、预留、待结算和收据；所有 mutation 使用统一 idempotency、固定锁 DAG 和
来源级撤销。

### Users and stories

| ID | User story | Priority |
|---|---|---|
| AC-US-01 | 用户能看到当前套餐、取得方式、有效期、续期 authority、权益和积分来源 | P0 |
| RD-US-01 | 用户能预览 Code 将获得什么、叠加规则和条款后安全兑换 | P0 |
| RD-US-02 | 网络响应丢失后用户能恢复同一 Redemption receipt，而不是再次兑换 | P0 |
| RD-US-03 | Code 审核、撤销、误绑、泄漏和 replacement 有完整用户/Support 路径 | P0 |
| CR-US-01 | 用户能区分 available、reserved、cost_pending、settled、expired、reversed | P0 |
| CR-US-02 | 用户和 Support 可以双向追踪 Grant→消费与消费→Grant | P0 |
| ADM-US-01 | Operator 能安全管理 Program/Batch/availability/export/reversal/correction，不直接改余额 | P0 |

## 2. Goals、Metrics and Non-Goals

### Goals

1. 合法 Code 从 claim 到 Subscription/Grant/receipt 在一个 PlatformUnitOfWork 原子提交。
2. 每个 term、Entitlement、Credit 和 Usage 都能追溯唯一 acquisition source。
3. 并发 Code stacking 不丢 term、不超过 max expiry、不生成重复 Grant。
4. Hold reserve/capture/release、expiry、revoke、correction 全部 journal-balanced、可重建。
5. redeem-only Profile 在 UI、route、API、Admin、secret dependency 四层禁用新 Payment acquisition。

### Success Metrics

| Metric | Target |
|---|---:|
| 合法且符合资格 Code Redemption 成功率 | ≥ 99.9%，排除用户取消/policy deny |
| lost response 恢复同一 receipt | 100% |
| Code claimed 但 Fulfillment/Grant 不完整 | 0 |
| duplicate Redemption/Fulfillment/Term/Grant | 0 |
| 并发 stacking 丢失 term 或超 max expiry | 0 |
| Journal 不平衡、负 available、无 source entry | 0 |
| committed Hold 被 TTL 释放 | 0 |
| redeem-only 新 Payment/Provider IO | 0 |
| Support direct DB/balance mutation | 0 |

指标引用 ProductMetricRevision，按 Site/Profile/Program/Plan/Credit unit/Journey revision 切分。

### Non-Goals

- PRD-03 不接真实 Payment Provider；Checkout、refund money IO 和 dispute 属于 PRD-04/Wave 2B。
- 不支持跨 Site Credit、转让、提现或法币化。
- V1 一个 ExecutionRoot 不跨多个 liability account；multi-Hold 延后。
- 不支持不同 Plan 的隐式覆盖/合并；使用显式 ChangePlan workflow。
- 不保留 mutable 三桶 authority、直接 grant/reset/spend 生产入口或兼容 adapter。

## 3. User-facing Concepts and Catalog

用户可统称“套餐”，领域必须区分：

```text
Product / ProductVersion = free | credit_pack | subscription | bundle
Plan / PlanVersion = 周期、权益、renewal/upgrade/grace/dunning 模板
OfferingVersion = 可售组合
FulfillmentProgramVersion = 实际签发模板
EntitlementTemplateVersion / CreditProgramVersion
SiteOfferingAssignment / AssortmentRevision
```

- Catalog 全局定义；SiteRelease 通过 immutable assignment/revision 选择可见组合，不复制 Catalog。
- Product/Plan 是稳定 identity；Version 发布后不可修改，变更创建新 revision。
- Account 显示产品名、当前有效 Plan、acquisition source 类别、term、renewal authority、下一变化、权益、Credit
  unit、余额来源和历史 receipt；不显示内部 ledger account。
- 免费、Code、Payment、Admin、daily/period Program 只在 acquisition/source 不同，不能复制后半链。
- 同 `(billingAccountId, serviceScope)` 最多一个 effective base Subscription；credit pack 只签 CreditGrant，不建
  Subscription。

## 4. Account and Plan Experience

### 4.1 Overview

- `AccountProductProjection` 聚合 SubscriptionTermAllocation、EntitlementGrant、Credit BalanceProjection 和
  acquisition receipt，标注 freshness/owner；它不是 write authority。
- 用户可展开每个 source：取得时间、Program/Product/Plan revision、有效期、original/available/reserved/
  consumed/expired/revoked 和关联 consumption。
- `renewalAuthority = none` 的 Card Code term 明确“不自动续期”；不能展示 Payment method 或“即将扣款”。
- pending/reconciliation 显示 deadline、后台 owner 和 Support deep link，不猜成功/失败。

### 4.2 Term stacking preview

Code preview 冻结：Product/Plan/Fulfillment revisions、duration、anchor、
`termApplicationPolicy = new_subscription | extend_from_max(now,currentPeriodEnd) | reject_if_active`、Plan mismatch、
stacking count/max expiry、Entitlement/Credit templates、liability Merchant、expiry 和 request digest。

- 相同 Plan 默认从 `max(now,currentPeriodEnd)` 延长。
- 不同 Plan 默认拒绝并引导 ChangePlan；Redeem handler 不能临时 upgrade/downgrade。
- preview 不是 claim/reservation；确认时重新校验 Program/Batch/Code/Subscription/Risk epoch。
- concurrent preview 可以不同；commit 以锁内 current state 计算并返回最终 receipt。

## 5. Redeem Journey

### 5.1 Secure input and preview

- 仅可信 SiteContext、已登录 BillingAccount、CSRF-protected command；无匿名试码。
- Code 至少 128-bit entropy，human format 含 public selector/checksum；DB 只存 versioned keyed HMAC/fingerprint。
- error 不区分不存在、其他 Site、已使用、过期/撤销等可枚举事实；rate limit 维度覆盖 Site/account/IP/device/
  Program/Batch/velocity。Risk/velocity dependency unavailable 时 fail closed，Code 不 claim。
- preview 展示获得内容、term/stacking、Credit expiry、重要条款和确认，不显示 Code 原文或内部 fingerprint。

### 5.2 Atomic confirmation

```text
verify SiteContext/User/BillingAccount/CSRF/idempotency digest
→ lock source prefix: ProgramAvailability → BatchAvailability → Code
→ common lock suffix:
   BillingAccount → Subscription(serviceScope) → SubscriptionTermAllocation
   → CreditAccount → eligible CreditGrant(burn order) → relevant CreditHold/HoldAllocation
→ recheck SalesPolicy/Program/Batch/Code/Risk/term limits
→ CAS claim Code
→ immutable Redemption
→ unique FulfillmentTransaction(source=redemption,purpose,cycleKey)
→ Subscription/TermAllocation + EntitlementGrant + CreditGrant
→ idempotency receipt + Audit/Outbox/NotificationRequest
→ commit
```

任一步失败全部回滚。固定锁 DAG 适用于 Redeem、Program/Batch availability、Fulfillment、Subscription change、
Grant materialization、Hold、reversal；serialization/deadlock retry 复用相同 idempotency key/digest。

### 5.3 Idempotency and receipt

统一 `IdempotencyRecord(scope,key,requestDigest,commandVersion,status,resultRef)`：同 key+digest 返回原结果；同 key
不同 digest 返回 `IDEMPOTENCY_CONFLICT`。Receipt 展示 Redemption、Fulfillment、Subscription term、Entitlement、
CreditGrant 和通知 refs；响应丢失由 receipt query 恢复，不重复提交另一 Code。

### 5.4 Review、reversal and replacement

- pending review 只创建 RedemptionAttempt/RiskCase，不 claim/hold Code。批准生成 single-use、action-bound
  RedeemApprovalGrant；继续时完整重校验，Code 可能已不可用。
- 已兑换 Code 永不恢复 available。误绑/泄漏/compromised 使用
  `RedemptionRevocationFact → source-specific FulfillmentReversalTransaction`，只撤销该 source 的未使用 term/
  Entitlement/Credit；committed/unknown exposure 进入 RecoveryCase。
- replacement 创建新 Code/Grant source，引用原 revocation，maker-checker，一次性 SecretDelivery；不转 owner。
- 外部售卡资金退款只保存审计 external reference，不生成 Platform Order/Payment/Invoice/Refund。

## 6. Program、Batch and Secret Delivery

- RedeemProgramVersion 冻结 Product/Plan/Fulfillment、Site/subject eligibility、liability Merchant、term policy、
  stacking/limits/window；发布后不可变。Availability 独立、单调 epoch，可 active/suspend/retire。
- Batch 生成 HMAC inventory 与一次性 encrypted `BatchExportArtifact`。Batch activate 前必须证明 delivery artifact
  已 delivered/destroyed as policy requires，并校验 HMAC inventory count/hash 与 Batch manifest 一致。
- plaintext 只在隔离生成进程到 recipient-public-key/KMS envelope encrypted artifact 的内存路径存在；DB/log/
  event/trace/Admin/Support/Data Export 中命中数为 0。
- claimed delivery 只允许同一 claim 在 TTL 内恢复；unknown 自动 suspend Batch，不能从 HMAC/backup 重构原文。
- Program/Batch suspend commit 之后不得有新 Redemption success；cache 只加速 UI，transaction locks 决定正确性。
- compromised campaign 以 durable cursor 按 RedemptionId 幂等执行，允许 pause/resume/partial result，不用大事务。

## 7. Subscription and Entitlement

- Subscription 稳定保存 subject、Plan identity、billing binding；每个 FulfillmentCycle/TermAllocation 保存完整
  Plan/Fulfillment/source revision。
- Code fixed term 使用 `SubscriptionBillingBinding(authority=none)`；不由 cron 自动续期。
- cancel/expire/stack/change 不原地改历史 allocation；effective term 是 allocations/reversal/time 的 projection。
- `SubscriptionTermAllocation(sourceRef,serviceScope)` 唯一；同 BillingAccount/serviceScope effective base
  Subscription 互斥；owner transfer 不改 source/liability facts。
- EntitlementGrant issuance immutable；revocation/correction 追加新 fact。Admission 解析 current effective grants，
  只向 GA 传业务无关的窄执行授权，不传 Plan/Price/Site/User。

## 8. Credit Authority and UX

### 8.1 Objects and invariants

```text
CreditAccount(BillingAccount, unit, liabilityMerchantAccount)
CreditGrant(sourceRef, originalAmount, effective/expires, burnPriority, scopePolicy, uxBucketClass)
CreditJournalTransaction / CreditJournalEntry
CreditHold / HoldAllocation
AuthorizationSegment / RatedUsage / BalanceProjection
```

Journal account type 明确区分 `grant_issuance_source`、`customer_available`、`customer_reserved`、
`customer_consumed`、`expired`、`revoked`、`adjustment` 与 `recovery_exposure`；法律 liability 是 CreditAccount/
Grant 的独立维度，不使用一个 `source_or_liability` 类型同时表达来源与责任。

- JournalTransaction 同 unit 借贷和为零；历史 entry 不更新，纠错是 reversal + correction。
- 唯一约束：FulfillmentTransaction(sourceType,sourceId,purpose,cycleKey)、TermAllocation(source,scope)、
  CreditGrant(source,template,window)、ProgramWindowAcquisition(program,subject,window)、
  JournalTransaction(businessOperationKey)、HoldAllocation(hold,grant)。
- BalanceProjection 可从 Grant/Journal/HoldAllocation 重建；projection 差异进入 reconciliation，不反写 authority。
- burn order：`expiresAt ASC NULLS LAST → burnPriority ASC → issuedAt ASC → grantId ASC`。

### 8.2 Daily、period、permanent

- 三桶只是 `uxBucketClass` 聚合；daily/period 通过唯一 ProgramWindowAcquisition 懒 materialize 当前窗口 Grant，
  不重置 mutable 数字、不全量 cron。
- Welcome/free/daily/period 都必须先形成 ProgramWindow/Admin acquisition + unique FulfillmentTransaction，再签
  CreditGrant；注册、登录、定时器和 read API 不得直接增加 customer_available。
- Program 冻结 calendar zone、anchor、rollover、amount、scope、expiry；默认 UTC 只是 policy 选择，不误称用户时区。
- UI 显示可用、预留、待结算、即将过期和来源，不展示 legal liability/account type。

### 8.3 Hold and execution

- 一个 ExecutionRoot/AuthorizationSegment 对一个 liability account 只有一个 root Hold；GA Model/Capability 和
  delegated Job 从其 allocation 消费，不创建第二 Hold。Direct Studio 是新 ExecutionRoot。
- reserve 过账 available→reserved，并记录 exact Grant allocation。Finalize 前 `reserved` 可 TTL release；
  Finalize 后 `committed` 永不被普通 TTL 释放。
- committed unknown 进入 reconciliation_required；Grant 后续到期/撤销不阻止已 committed allocation capture，
  未使用释放按当前 Grant 状态进入 available/expired/revoked。
- insufficient credit 只能拒绝、截断或经用户确认新 segment；禁止负余额、静默透支或换 liability。

### 8.4 Traceability and notification

- Grant detail 列出资助的 Hold/RatedUsage；Usage detail列出消耗的 Grant allocation，形成双向图。
- notification：余额阈值、即将过期、Hold reconciliation aging、source reversal/correction；它们是 UX，不是
  Credit authority，也不能触发自动 top-up，除非未来独立 PRD。

## 9. User-visible States and Recovery

| Surface | States | Recovery |
|---|---|---|
| Account/Plan | active、change_scheduled、past_due_external、expired、reconciliation_required | view source/change workflow/wait/Support |
| Redeem | validating、review_pending、succeeded、safe_rejected、temporarily_unavailable、reversed、replacement_pending | retry same identity/provide evidence/wait/Support |
| Credit | available、reserved、cost_pending、settled、expired、reversed、reconciliation_required | view receipt/wait/query/Support；不盲 retry |

每个状态标明是否 Code 已消耗、权益是否到账、可否安全重试、费用/余额影响、freshness、deadline 和 owner。

## 10. Admin and Support

- 专用 Admin surfaces：Catalog/Plan revision diff、Program/Batch、one-time export、availability、Redemption timeline、
  Fulfillment/Term/Grant/Journal/Hold reconciliation、campaign/replacement/correction。
- high-risk Program publish、Batch export/activate、mass reversal、AdminGrant、Journal correction 要 step-up、参数
  digest、maker-checker；maker/checker/executor 不能为同一 operator。
- Support 只调用 typed correction/reversal/replacement/reconciler command，并保存 authoritative receipt；不能
  直接改 Code、Subscription、Grant、Journal、balance、Hold 或 GA state。
- Code 原文、HMAC、secret、provider credential 永不显示；按 safe fingerprint/correlation ref 检索。

## 11. Edge Cases

| Scenario | Expected behavior |
|---|---|
| 两张同 Plan Code 并发 | Subscription row/version + TermAllocation unique 串行叠加，不丢 term/超 max expiry |
| 不同 Plan Code | safe reject + ChangePlan，不 claim Code |
| response lost after commit | receipt query 返回同 Redemption/Grant，不再次 claim |
| Risk down | temporarily_unavailable，Code 保持 available |
| review approved but Code used | full recheck safe reject，approval 不保证成功 |
| Grant expires while Hold committed | known Usage 可 capture；unused release→expired，不复活 |
| committed outcome unknown | no TTL release/no retry effect，reconciliation owner |
| Batch export unknown | suspend/revoke unused inventory，不能再展示/重构 plaintext |
| redeem-only stale checkout client | channel disabled，Order/Provider IO 为零 |

## 12. Acceptance Criteria

### AC-RD-01 — Atomic redeem

```gherkin
Given a valid eligible Code and BillingAccount
When any claim, Fulfillment, Subscription, Entitlement, Credit, receipt or outbox write fails
Then the entire transaction rolls back and Code remains available
When all writes succeed
Then exactly one immutable Redemption and complete source-linked result exist
```

### AC-RD-02 — Lost-response recovery

```gherkin
Given Redemption committed but the HTTP response was lost
When the same idempotency key and request digest is queried or retried
Then the same receipt and refs are returned
And no second Code claim, term or Grant is created
```

### AC-RD-03 — Concurrent stacking

```gherkin
Given two Codes extend the same Plan concurrently
When both transactions execute under the global lock order
Then each source creates one unique TermAllocation
And final period end applies both durations without exceeding max expiry
```

### AC-RD-04 — No fake payment

```gherkin
Given acquisitionMode is redeem_only
When Code succeeds, reverses, is replaced or references an external seller refund
Then no Order, Payment, Invoice, Refund or Provider IO is created
And new checkout routes and commands remain disabled
```

### AC-CR-01 — Journal and reconstruction

```gherkin
Given arbitrary Grant, reserve, capture, release, expiry, revoke and correction operations
When Journal is replayed
Then every transaction balances per unit and BalanceProjection is reconstructed exactly
And no available balance is negative
```

### AC-CR-02 — Committed hold safety

```gherkin
Given a Hold finalized as committed and execution outcome is unknown
When admission TTL or Grant expiry passes
Then the Hold enters or remains reconciliation_required rather than releasing
And no duplicate execution starts from the same retry
```

### AC-CR-03 — Source-specific reversal

```gherkin
Given one account has Payment, Redemption, Admin and Program-window Grants
When one Redemption is revoked
Then only its unused Term/Entitlement/Credit is reversed
And committed/unknown exposure becomes a RecoveryCase without consuming another source
```

### AC-CR-04 — Bidirectional traceability

```gherkin
Given one Usage allocation burns multiple Grants
When user or authorized Support opens either the Usage or a Grant
Then both views resolve the exact allocations and source receipts
And neither view relies on mutable bucket totals
```

### AC-ADM-01 — Secret delivery

```gherkin
Given a generated Batch has HMAC inventory but its encrypted export is missing, corrupt or unknown
When activation is requested
Then Batch cannot activate and plaintext cannot be regenerated
And security workflow revokes unused Codes or creates a new Batch with complete delivery evidence
```

## 13. Dependencies、Risks and Milestones

| Risk/Dependency | Mitigation |
|---|---|
| 旧三桶继续当 authority | Wave 2A clean rebuild、single cutover、删除旧 columns/APIs/tests |
| 并发 source 锁不同对象 | global lock DAG + unique constraints + same-id retry |
| Session/GA 自行扣费 | Platform Admission/Hold allocation only；contract/import negative tests |
| Support 补偿串 source | typed source refs、maker-checker、append-only receipts |
| redeem-only 被当 mock payment | distinct Redemption fact、four-layer Payment disable evidence |
| liability 切换虚增余额 | one account per execution、SiteRelease compile、explicit transfer workflow only |

Wave 2A 先固定旧行为 corpus，只迁 fixture/seed；若发现真实需保留数据则停止并另写 migration Spec。随后建立
PostgreSQL Catalog/Fulfillment/Subscription/Grant/Journal/Hold schema，原子切换所有调用方，并在同 Wave 删除旧
bucket、creditBack、direct grant/reset/spend、namespace→team billing 映射、welcome env 和旧 sweeper。Wave 7
完成 Admin/Support，Wave 9 运行 concurrency/property/chaos/reconciliation/redeem-only certification。

## 14. External Design References

- [Lago wallet/prepaid credit overview](https://getlago.com/docs/guide/wallet-and-prepaid-credits/overview)：参考
  wallet priority、expiration 与可解释余额，但 Kokoro 不采用 mutable wallet 作为最终 authority。
- [Lago wallet traceability](https://getlago.com/docs/guide/wallet-and-prepaid-credits/traceability)：参考 funding 与
  consumption 双向追踪，Kokoro 映射为 Grant/HoldAllocation/RatedUsage provenance。
- [Stripe Billing credits](https://docs.stripe.com/billing/subscriptions/usage-based/billing-credits)：参考 credit grant/
  applicability 的产品分离，不复制 Stripe ledger 或税务结论。
- [Medusa payment architecture](https://docs.medusajs.com/resources/commerce-modules/payment/payment)：参考 payment/
  capture/refund 事实分离；Redemption 仍是 Kokoro 独立 acquisition fact。

上述映射属于 Kokoro 架构推断；owner、锁序、Journal、Card Code 和法律 liability 以本文及 architecture child
Spec 为唯一裁决。

本文批准不授权实现，也不修改 GA runtime。
