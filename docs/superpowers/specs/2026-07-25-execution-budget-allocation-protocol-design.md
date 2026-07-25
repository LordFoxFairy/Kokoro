---
artifact: architecture-design
version: "1.0"
created: 2026-07-25
status: internal-review-active
scope: execution-root-credit-hold-delegated-budget-allocation-usage-settlement-conservation
implementationAuthorized: false
gaRuntimeSemanticChangeAuthorized: false
---

# Execution Budget Allocation Protocol

## 1. Purpose

本文冻结Chat、GA Model/Capability调用、detached Job、Direct Studio和未来Agent Team共享Credit root Hold时的预算守恒协议。
目标是确保并发consumer不能各自把root ceiling当成完整额度，也不能因retry、unknown、late usage或delegation产生第二Hold、
重复capture或跨Grant错误归还。

Credit authority仍是`CreditGrant + append-only CreditJournal + CreditHold/HoldAllocation`。GA、Session、Job、Gateway、Capability
只消费授权与上报Usage evidence，不计算customer price、不修改余额、不写Journal。

## 2. Invariants

1. 一个`ExecutionRoot + liabilityAccount`至多一个root CreditHold。
2. V1一个ExecutionRoot只使用一个liability account；multi-liability不做隐式拆分。
3. 每个consumer只能消费Platform原子签发给其audience的Allocation。
4. 任一allocation满足：`reserved = unassigned + child_reserved + committed + captured + released_or_returned`，所有量非负。
5. 同parent所有active child ceilings与parent已消费事实总和永不超过parent reserved ceiling。
6. allocation不可重parent、跨Site、跨BillingAccount、跨ExecutionRoot、跨RatingPolicy或跨liability复用。
7. unknown effect对应额度保持committed/reconciling，不能归还后再被其他effect消费。
8. Usage/settlement/correction追加事实；不更新原Usage、HoldAllocation、Journal entry或source Grant。

## 3. Canonical objects

```text
ExecutionBudgetRoot
  immutable siteId / executionRootId / billingAccountRef / liabilityAccountRef
  rootHoldRef / authorizationBudgetRef / ratingPolicyRevisionRef
  currencyOrCreditUnit / reservedCeiling / state / revision

BudgetAllocationRevision
  allocationId / immutable parentAllocationRef? / rootRef
  audience=model_gateway|capability_runtime|job|agent_team|target_runtime
  purpose+surface+operation+agent refs
  creditCeiling / optional dimension ceilings
  unassigned / childReserved / committed / captured / returned
  issuedAt / expiresAt / allocationEpoch / revision / state

AllocationReservationReceipt
  parent+child refs / request identity+digest / amount / parent expectedVersion
  resulting revisions / journal-or-hold linkage / committedAt

EffectBudgetCommit
  allocationRef / logicalEffectId / attempt or operation ref
  maximumCredit / dimension envelope / requestDigest
  state=planned|committed|outcome_unknown|usage_recorded|settled

AttemptUsageEvidence
  immutable siteId / allocationRef / logicalEffect+attempt refs
  evidence revision / dimensions+units / evidence grade / source digest
  occurred+observed times / correctionOf?

AllocationSettlementReceipt
  allocation+effect+usage refs / rated amount / capture+release refs
  policy revision / outcome / resulting revision

AllocationReturnReceipt
  child+parent refs / exact unused amount / fence epoch / reason
  child terminal revision / parent resulting revision
```

`BudgetAllocationRevision`是Credit/Admission owner事实；consumer可持有signed/opaque authorization handle，但不能自行创建或扩容。

## 4. Root admission

```text
trusted Site/Billing/Entitlement/Operation intent
→ compile Quote + RatingPolicy + maximum customer ceiling
→ select eligible CreditGrants and exact HoldAllocations
→ reserve available → reserved in one Journal transaction
→ create ExecutionBudgetRoot + root Allocation
→ return opaque execution authorization handles
```

- 同submit identity+digest只创建一个ExecutionRoot/root Hold；不同digest冲突并要求reconfirmation。
- root Hold冻结Grant source allocations、burn order、expiry/revocation treatment和liability account。
- Quote ceiling不是Provider cost estimate的无约束提示，而是customer可承担的最大Credit reservation。
- 余额不足时Admission拒绝或返回显式较小方案，不透支、不切换liability、不从别的Site/Account借用。
- Grant在Hold committed后到期/撤销不取消既有可结算liability；未committed剩余按原Grant规则release/expire/revoke。

## 5. Allocation tree operations

### 5.1 Reserve child allocation

`ReserveChildAllocation(parent, audience, purpose, ceiling, requestKey, digest, expectedParentRevision)`在Credit authority内原子：

1. 验证Site/Billing/root/liability/RatingPolicy、parent active、audience/purpose和expiry。
2. 验证`ceiling <= parent.unassigned`及dimension envelope不扩大。
3. parent `unassigned -= ceiling`、`childReserved += ceiling`。
4. 创建immutable child revision与receipt/outbox。

相同requestKey+digest返回同child；不同digest拒绝。consumer不因RPC timeout再申请新slice，而是查询receipt。

### 5.2 Resize

- 增加child ceiling是新的CAS command，从parent unassigned再切片；旧revision保留。
- 降低ceiling只能归还未分配且无committed effect的额度。
- 已committed/unknown额度不能通过resize消失。
- resize后旧authorization epoch不能创建新effect，已committedeffect仍按其frozen revision结算。

### 5.3 Delegate

- GA发起Job时，Platform/Admission从GA可用parent allocation切出`audience=job` child；Job不走Direct Studio root admission。
- AgentTeam `ChildBudgetSlice`是同一BudgetAllocationRevision的purpose subtype，不是第二账本。
- delegated child只能继续委派Definition允许的audience/depth；最大depth和fanout由AuthorizationBudget冻结。
- child不能访问parent其他Usage、Grant细节或可用余额，只获得opaque handle和自身ceiling/freshness。

### 5.4 Return

- child只有在所有descendants terminal、无committed/unknown effect且consumer fence关闭后才能归还unused。
- ReturnReceipt与child terminal CAS原子；parent在receipt durable后增加unassigned。
- consumer lease expiry、worker crash、browser disconnect不证明可归还。
- detached Job完成后未用额度可归parent；若parent execution已terminal，按root finalization策略release到原Grant/终结账户。

## 6. Consumer-local admission

### Model Gateway

- Gateway从其预物化authorization record读取bounded allocation，原子派生per-logical-invocation commit。
- 每个logicalModelCallId先reserve maximumCredit/dimensions，再做Provider I/O。
- Route retry/fallback Attempts共享同logical effect envelope；是否向客户计费由frozen RatingPolicy决定，不能每Attempt拿完整root ceiling。
- Gateway本地ledger/outbox和Platform allocation receipt需可对账；Gateway不能在allocation store不可用时直接Provider effect。

### Capability Runtime

- 每个tool/capability effect按OperationDefinition声明worst-case或step ceiling。
- read-only/zero-rated仍创建effect identity与Usage evidence policy，但可使用zero credit commit。
- external connector unknown不释放commit，也不切另一个connector重试。

### Job

- Job DAG在dispatch前为required stages/outputs创建stable allocation plan或按有界动态policy切片。
- candidate/track/stage的Usage绑定自己的effect allocation；partial成功不吸收unknown slot额度。
- finalizer不消费Provider-effect预算，只允许Definition声明的bounded storage/rendition/validation allocation。

### ExecutionTarget

- 本地command可能产生Credit/Provider或平台成本时使用独立target child allocation。
- user permission lease与budget allocation都有效才执行；批准文件/command不代表批准费用，反之亦然。

## 7. Effect commit and unknown

```text
planned
→ budget_committed_before_effect
→ definitely_not_submitted | submitted | submission_unknown
→ usage_recorded | reconciliation_required
→ rated
→ captured/released/corrected
```

- Provider/connector I/O前持久化EffectBudgetCommit、logical identity、request digest和operation key。
- 只有`definitely_not_submitted`可释放commit并按policy选择新Attempt。
- `submission_unknown`保持额度锁定；reconciler查询Provider operation/billing/callback，禁止自动retry/fallback。
- 达到maximum reconciliation window后进入`irreconcilable`，使用发布的customer charge、Provider exposure、Support/Finance与
  allocation disposition policy；不能无限占Hold，也不能假定0 usage。
- late success/failure/usage追加Outcome/Usage revision并对同effect settle一次，不创建新allocation或Artifact/charge。

## 8. Usage、rating and settlement

- producer在Attempt terminal/outcome同一local transaction持久化AttemptUsageEvidence+outbox。
- finalizer等待local evidence receipt，不等待canonical ingest/rating；作品可completed/cost_pending。
- Usage Rating验证siteId、billing/root/allocation/effect、units、evidence revision和RatingPolicy后计算customer amount。
- rated amount不得超过effect committed maximum；Provider异常overage进入platform cost exposure/review，不能静默扣parent remainder。
- capture按root HoldAllocation的原Grant来源精确过账reserved→consumed；unused按原source规则release/expire/revoke。
- correction引用原Usage/Settlement，创建reversal/correction JournalTransaction；不把费用转到其他Allocation/Site/Account。
- zero/unavailable usage必须有typed evidence reason；terminal Attempt缺Usage evidence不是0，而是reconciliation_required。

## 9. Concurrency and fencing

- Allocation authority使用row/aggregate expectedVersion、serializable invariant或等价原子conditional update。
- `SUM(active child reserved + committed/captured) <= parent ceiling`在单transaction内验证，不靠异步projection。
- consumer authorization包含allocationEpoch和audience；resize/revoke后旧epoch不能commit新effect。
- worker lease/runEpoch只决定谁推进Job，不决定预算owner；stale worker无法用旧fence提交allocation/Usage。
- callback必须映射到siteId+effect+attempt+allocation；mismatch/unresolved进入quarantine。
- multi-region V1为single-writer allocation authority；failover先fence old writer/epoch再提升，禁止双主切片。

## 10. User and operator experience

- 用户看到root estimate/ceiling、reserved、cost_pending、settled和可解释的Job/Run breakdown，不暴露内部Grant/account secrets。
- nested Agent/Job只展示有意义的阶段/作品费用；内部allocation tree供Admin/Support safe projection。
- Credit页面从Grant/Journal/HoldAllocation重建source→usage双向追踪。
- cancel说明哪些额度可立即release、哪些submitted/unknown仍pending；不承诺“点击停止即全额返还”。
- Admin typed commands：ReconcileAllocation、CloseIrreconcilableEffect、CreateCreditCorrection、ReturnFencedUnusedAllocation、
  RebuildBudgetProjection。禁止直接改remaining/balance、移动allocation、mark usage zero或跨source归还。

## 11. Failure matrix

| Failure | Required behavior |
|---|---|
| child reserve response lost | query same request receipt；no second slice |
| two consumers reserve concurrently | one/both按真实unassigned原子成功；sum never exceeds parent |
| consumer crashes before effect | prove no submission + fence before return |
| Provider submitted then timeout | committed/reconciling；no retry or return |
| Rating down | result may complete cost_pending；allocation remains committed |
| Usage duplicate/out-of-order | evidence revision reducer；one settlement |
| Grant expires after commit | settle committed amount；unused followssource expiry policy |
| Site suspended | no new commits/delegation；submitted facts reconcile |
| allocation authority failover | fence old region/epoch before new writer |
| Provider reports over ceiling | quarantine variance/platform exposure；no silent extra customer capture |

## 12. Acceptance criteria

### AC-BUD-01 — Concurrent child allocations conserve parent

```gherkin
Given Gateway, Capability and Job concurrently request slices from one parent
When requests commit under the same and stale parent revisions
Then successful child ceilings plus parent consumed facts never exceed the parent ceiling
And rejected callers receive conflict or insufficient-budget without a partial slice
```

### AC-BUD-02 — Delegated Job has no second Hold

```gherkin
Given a GA Run delegates a media Operation to Job
When Job admission succeeds
Then one child allocation references the original ExecutionRoot and root Hold
And no Direct Studio root, second Hold, second liability or duplicate reservation is created
```

### AC-BUD-03 — Unknown cannot release and reuse budget

```gherkin
Given a Provider may have accepted an effect before timeout
When another model, capability, Job or user action requests the same committed amount
Then the unknown allocation remains unavailable until canonical reconciliation or irreconcilable disposition
And no new effect bypasses it through fallback, retry, resize or delegation
```

### AC-BUD-04 — Return requires fenced descendants

```gherkin
Given a child worker lease expired while descendant effects may still run
When unused allocation is returned
Then every descendant is terminal with no committed or unknown effect and the old allocation epoch is fenced
And a stale worker cannot later consume the returned amount
```

### AC-BUD-05 — Usage settles once to exact sources

```gherkin
Given one effect uses Credit reserved from several eligible Grants
When duplicate, late or corrected Usage evidence arrives
Then the canonical evidence revision settles the allocation exactly once against original HoldAllocations
And correction appends reversal/correction facts without moving charge to another source, Site or account
```

### AC-BUD-06 — Provider overage is not silent customer debt

```gherkin
Given Provider usage exceeds the effect maximum authorized customer ceiling
When rating and reconciliation run
Then customer capture remains bounded by frozen authorization and policy
And the variance becomes explicit platform exposure/review with Support and Finance receipts
```

## 13. Verification and release gates

- model/property：random allocation trees、resize/return/delegate、concurrent CAS、non-negative fields和sum invariants。
- journal：multi-Grant HoldAllocation、expiry/revoke/capture/release/correction、projection rebuild和double-entry balance。
- chaos：response loss、consumer crash、unknown Provider、late callback、Rating outage、allocation failover和stale worker。
- cross-context：Gateway/Capability/Job/Target audience、Site/Billing/root/Rating拼接负向矩阵。
- operations：Hold/allocation aging、irreconcilable deadlines、Admin correction maker-checker、DR restore和two-Site isolation。

No-Go：consumer拿root完整ceiling；child sum超parent；第二Hold；allocation reparent/crossSite；unknown释放；lease expiry归还；
terminal缺Usage当0；Provider overage静默扣款；correction改历史；Gateway/Job/GA计算customer price或写Credit Journal。

## 14. Related documents and approval boundary

- [PRD-03 Account、Redeem 与 Credit](2026-07-25-prd-03-account-plan-redeem-and-credit.md)
- [PRD-07 Studio Job/Cost](2026-07-25-prd-07-studio-common-job-and-cost-ux.md)
- [Model Gateway](2026-07-25-model-control-gateway-litellm-architecture-design.md)
- [Platform/Web/Session target architecture](2026-07-25-platform-web-session-target-architecture-design.md)

本文批准不授权实现。GA只接收opaque allocation/authorization handle；任何为预算切片而修改GA checkpoint、graph、tool、Handoff、
cancel、terminal或namespace的方案必须专项对齐。预算守恒应由Platform Credit authority和外围adapter完成。
