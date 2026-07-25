---
artifact: product-requirements-document
prdId: PRD-07
version: "1.0"
created: 2026-07-25
status: internal-review-active
scope: studio-common-draft-quote-operation-job-attempt-progress-partial-cost-artifact-export
accountableProductRole: Studio Platform Product Lead
mandatoryCosigners: [Image, Music, Video, Job Runtime, Artifact, Model Platform, Usage Rating, Trust, Web, Support, SRE, QA]
engineeringOwner: team:operation-job-artifact-engineering
qaOwner: team:studio-runtime-quality
supportOperationsOwner: team:studio-operations
namedOwnerAssignmentStatus: assigned-team-responsibility-ids
implementationAuthorized: false
gaRuntimeSemanticChangeAuthorized: false
---

# PRD-07：Studio Common、Job 与 Cost UX

## 1. Overview

### Problem

Image、Music、Video 都需要草稿、参数、素材、报价、提交、排队、进度、取消、Provider callback、partial result、
重试、Artifact 与导出。若每个 Studio 自己实现一套，或把这些能力塞进 GA/Session，会出现三套 Job 状态、
重复 Provider effect、浏览器断开即失败、unknown 被误重试、生成成功但 Artifact/Usage 丢失、费用与结果混为一谈，
以及 Direct Studio 和 Agent tool 产生不同作品/积分链。用户把 “生成” 点两次，也可能获得两个不可解释的扣费。

### Solution

建立一个通用的 Studio product contract 和 GA 外部 Job Runtime：专业 Studio 拥有参数与编辑体验，Project/Studio
Draft 拥有可变草稿，Platform Admission 拥有资格、policy、quote snapshot 与 root Hold，Job Runtime 拥有
Operation/Job/JobAttempt/lease/progress/finalization，Model Gateway/Capability Runtime 拥有 Provider Attempt，Artifact
拥有 ArtifactVersion，Usage Rating 拥有客户结算。Direct Web 与 GA tool 只在 Admission 前入口不同，之后调用同一
`SubmitOperation` facade 与完全相同的 Job/Artifact/Usage 状态机。

Job 是同一 Kokoro 后端代码库中的独立 bounded context 和可独立部署 process role，通过内部 RPC/event 被 Web BFF、
GA 与 Admin 调用；不为 Image/Music/Video 或每个 Provider 新建子仓/服务，也不把 Job 放进 GA。

### Users and stories

| ID | User story | Priority |
|---|---|---|
| ST-US-01 | 用户能创建、自动保存、恢复和显式命名草稿，不因断网或多 Tab 覆盖新版本 | P0 if-enabled |
| ST-US-02 | 用户提交前看到当前参数、素材、模型选项、预计积分范围和限制，确认后重复点击不重复生成 | P0 |
| ST-US-03 | 用户可以离开页面并持续查看 queue/progress/finalizing/partial/unknown，而浏览器不是 Job owner | P0 |
| ST-US-04 | 用户能取消、重试失败候选、比较结果、保存版本和导出，并理解每一步是否产生新费用 | P0 |
| ST-US-05 | Agent 调用同一能力时，用户在 Chat/Studio/Library 看到同一个 Job 与 Artifact lineage | P0 |
| ST-US-06 | Support/Operations 可以恢复 stuck finalization、unknown callback 和 settlement，不直接重跑 Provider 或改库 | P0 |

## 2. Goals、Metrics and Non-Goals

### Goals

1. 一个提交 identity 至多创建一个 Operation、一个 root Hold 和确定的 Job DAG。
2. Provider effect、Job progress、Artifact finalization、Usage/Cost 四条状态正交且可独立恢复。
3. Direct Studio 与 GA tool 使用同一 OperationSpec、JobAttempt、ArtifactVersion、AttemptUsageFact 与 charge policy。
4. retry/fallback 只有在“确定未提交 effect”或用户明确创建新 attempt/operation 时发生；unknown 永不自动重放。
5. partial candidate 是可保留结果，不被其他 candidate 失败覆盖；每个 candidate 有 provenance/usage/decision。
6. 所有 enabled Studio full page/state/complete process 满足 PRD-14，并满足 PRD-16 modality/rights policy。

### Success Metrics

| Metric | Target |
|---|---:|
| 同 submit identity 重复 Operation/root Hold/Provider logical effect | 0 |
| Provider outcome unknown 自动 retry/fallback | 0 |
| terminal Attempt 缺 AttemptUsageEvidence/outbox | 0 |
| required result Job completed 但缺 ArtifactVersion receipt | 0 |
| finalizer retry 导致 Provider rerun、重复 Artifact 或重复 capture | 0 |
| browser close/refresh 导致 accepted Job 丢失 | 0 |
| lease steal 后旧 epoch 写入成功 | 0 |
| partial candidate provenance/charge/Decision 串位 | 0 |
| queue/progress/unknown/cost state 无 owner或 RecoveryAction | 0 |
| enabled Studio WCAG 2.2 A/AA failure | 0；任一失败阻断 SiteRelease |

### Non-Goals

- 不在本文定义 Image/Music/Video 的全部专业参数；分别由 PRD-08I/M/V 冻结。
- Job 不拥有 Product/Plan、Model catalog、Provider secret、customer price、Credit Journal 或 Artifact binary。
- 不把短同步模型轮、普通工具、LangGraph node、UI loading 或 Session projection 建成 Job。
- 不把 Job 当通用业务流程引擎替代 Payment、Redemption、Data Rights、Notification 或 Routine state machine。
- 不允许 Web/GA 直接选择 ProviderAccount/Deployment、操作 lease 或写 terminal。
- 不承诺 Provider 原生 progress 精确；只展示 evidence class 与 freshness。
- V1 不做 speculative/hedged parallel Provider attempts、split Hold、跨 Site Job、用户自定义 workflow graph。
- 本 PRD 不授权修改 GA graph/checkpoint/tool/Handoff/effect/namespace/terminal。

## 3. Product Objects and Ownership

```text
StudioDraft
  siteId / projectRef / surfaceKind / title / currentRevisionRef / lifecycle

StudioDraftRevision
  draftId / revision / parentRevisionRef / typed parameter set / ordered AssetVersion refs
  selected ModelOption / prompt-assistant snapshot / client+server schema revisions / createdBy+at

OperationQuote
  siteId / draftRevisionRef or canonical spec digest / estimate dimensions+range
  currency=CreditUnit / ratingPolicyRef / assumptions / expiresAt / nonBindingReasons

OperationSpec
  immutable surface+operation kind / typed parameters / Asset grants / output contract
  Model/Capability roles / candidate count / policy+rights+consent / delivery+cancel policy

Operation
  siteId / operationId / source=direct|agent / sourceRef / specDigest
  admission+authorization refs / rootHoldRef / state / idempotency key+digest

Job / JobDependency
  jobId / operationId / jobKind / dependency refs / priority class / state / expectedVersion
  queue/deadline/cancel/finalization policy / current attempt ref

JobAttempt
  attemptId / jobId / ordinal / leaseEpoch / providerOrWorker invocation ref
  effect state / outcome / progress observations / usage+cost evidence refs

CandidateResult
  candidateId / attemptId / output slot / state / Blob/Artifact refs
  policy Decision / usage allocation / provenance

FinalizationReceiptSet
  provider outcome / Blob / ArtifactVersion / AttemptUsageEvidence / notification refs

ExportRequest / RenditionJob
  source ArtifactVersion / output profile / delivery policy / independent usage+receipt
```

Ownership：

- Project/Studio module owns Draft and immutable DraftRevision；draft 不是 executable Operation。
- Platform Admission owns OperationAuthorization、entitlement/risk/content constraints、root Hold、RatingPolicy snapshot。
- Job Runtime owns Operation execution projection、Job/Dependency/Attempt lease、dispatch、progress、cancel intent、finalizer。
- Model Gateway/Capability Runtime own each external Provider effect/Attempt/outcome/ProviderCost/AttemptUsageFact。
- Artifact owns stable Artifact、immutable ArtifactVersion、Blob refs、lineage、rendition/export artifacts。
- Usage Rating owns canonical usage、customer rating、settlement/correction；Job只投影 `costState`。
- Trust owns canonical content/publish Decision；Job/Artifact不能把 ProviderSafetyFact 或 scanner result直接变成 allow。
- Session only owns Job/Artifact cards and RunJobLink projection；GA receives/returns opaque Job handles。

## 4. Draft and Quote

### 4.1 Draft lifecycle

```text
active → archived → restored
active/archived → deletion_pending → deleted|retained
```

- 创建空 Draft 不 reserve Credit、不创建 Operation/Job。每次 autosave 写 immutable `StudioDraftRevision`，用
  `(draftId, baseRevision, clientMutationId, requestDigest)` CAS；同 ID同 digest返回同 revision，不同 digest冲突。
- 多 Tab/多设备并发不 last-write-wins：基于不同 base 的 revision 形成 conflict，UI 展示字段/Asset diff，用户选择
  keep current、fork draft 或显式 merge。禁止静默覆盖 prompt/seed/素材/mask/lyrics/storyboard。
- local draft 只作离线便利缓存；服务器 revision 是跨端真源。离线编辑恢复时生成新 candidate revision，不能覆盖
  已在其他设备提交的 spec。
- schema upgrade 使用版本化 migration preview；不能解析的旧参数保持 read-only snapshot，允许 duplicate/fork with
  explicit repair，禁止静默丢字段。
- Draft archive/delete 不 cancel 已提交 Operation/Job，也不删除 Artifact/Usage；关联对象单独解释。

### 4.2 Quote semantics

- Quote 输入是 canonical DraftRevision 或完整 OperationSpec candidate，不接受客户端 price/quantity micros。
- Quote 冻结 Plan/Rating/ModelOption/parameter/asset/media dimensions 与 assumptions，输出 estimated range、最大 reservation
  ceiling、可能的 post-effect charge policy、有效期和非确定原因。
- Quote 是用户确认用 estimate，不 reserve Credit，也不保证 Provider availability。Submit 必须重新 Admission/Rating，
  若 price ceiling、material parameter、policy、entitlement 或 model compatibility 变化，返回 `reconfirmation_required`
  并展示 diff；不能静默用更贵/不同 spec。
- 纯 deterministically priced operation 可以显示 exact quote；Provider metered/unknown output显示范围和最大 Hold。
- Credit unit 与法币分开；Redeem-only Site 不显示假 Order/Payment。Quote/Rating error 不泄漏 provider cost/secret。

## 5. Submit and Admission

### 5.1 Direct and agent entries

```text
Direct Studio
Web → Site BFF → SubmitOperation façade
  → Platform PrepareOperation
  → persist Operation(admission_pending) + Job plan
  → Platform FinalizeOperationAuthorization + root Hold commit
  → Job CAS queued + dispatch outbox

Agent Tool
GA → SubmitOperation façade with delegated execution grant
  → same Prepare/persist/Finalize/queue sequence
```

- 两入口生成相同 canonical OperationSpec/schema；source 只影响 provenance和用户入口，不复制业务逻辑。
- Agent delegated allocation 是 execution root Hold 的受限 child allocation；Job不创建第二账户 Hold。Direct Operation
  由 Platform创建唯一 root Hold。
- Admission 失败不得创建 executable queued Job；若为审计保存 rejected request，必须与 Job aggregate/queue隔离。
- `SubmitOperation` identity 为 `(siteId, billingAccountRef, sourceAudience, idempotencyKey)` + canonical spec digest。
  同 key同 digest返回同 Operation/Job/authorization；不同 digest冲突，重复点击不新建。
- Prepare 后持久 Operation plan，Finalize 前再次检查 SiteRelease/Plan/Option/Asset/rights/consent/restriction/quote ceiling。
- Finalize 成功但 queue CAS/outbox 失败：reconciler用同 identity完成 queue；只有证明无 Attempt/effect开始时，Platform
  reconciliation才可撤销 authorization/release root Hold。禁止创建第二 Operation。
- Browser/GA 不传 Site/Billing/price/provider扩权；trusted context与signed grants编译。

### 5.2 Job formation

只有满足至少一个条件才建 Job：跨连接/进程恢复、Provider async/callback、queue/priority/progress/retry/reconcile、
结果晚于 Run、独立 cancel/timeout/lease。短同步 step 使用 RunActivity/ModelInvocation/CapabilityCall，不建 Job。

一个 Operation 可编译 Job DAG，但 V1 只允许由发布的 OperationDefinitionRevision 生成，用户/Prompt 不提交任意 graph。
Dependency 必须 acyclic、role/cost/Artifact contract完整；SiteRelease compile证明每个 node owner、timeout、retry policy。

## 6. Job、Lease and Attempt State Machines

### 6.1 Operation and Job states

```text
Operation:
admission_pending → authorized → active → finalizing → completed|partial|failed|canceled|unknown

Job:
waiting_dependency|waiting_interaction|queued|leased|running|provider_async|
cancel_requested|reconciling|finalizing|completed|partial|failed|canceled|unknown
```

- Operation terminal是 Job结果的产品 aggregate，不覆盖每个 Job/Attempt事实；required job未闭合不能completed。
- queue accepted/leased/running/provider_async/progress 都不等于 Provider submitted/succeeded。
- Job lease 使用 `(jobId, leaseEpoch, workerId, expiresAt)` fencing；claim/renew/complete/cancel/progress写入都验证 epoch。
  lease expiry 只说明 worker ownership丢失，不证明 Provider未提交，不能直接 rerun effect。
- Worker steal 后先读取 persisted Attempt/provider operation identity：只有 `definitely_not_submitted` 可开始安全新 Attempt；
  `submitted|submission_unknown|outcome_unknown` 必须 attach/query/reconcile。
- queue delivery是 at-least-once；Job/Attempt唯一键与 effect ledger提供业务幂等，不能宣传 queue exactly-once。

### 6.2 Attempt effect states

```text
planned → dispatching
→ definitely_not_submitted | submitted | submission_unknown
submitted → running|provider_async
→ succeeded|failed|canceled|outcome_unknown
unknown → reconciliation_required
→ reconciled_succeeded|reconciled_failed|irreconcilable
```

- provider operation key在 I/O 前持久化，绑定 site/account/deployment/spec/attempt/request digest。
- internal transport retry只允许能证明 effect未提交的错误。Provider unknown禁止自动 retry/fallback或新 Operation。
- ProviderCertification冻结 idempotency、retrieval、callback、cancel certainty、billing source和maximum reconciliation
  window；到期进入irreconcilable，执行已发布customer charge/Provider exposure/Support/Finance/allocation policy，不无限占Hold。
- late callback/fact append-only reducer；本地先标 failed/canceled后late success仍记录并reconcile，不能重复Artifact/Usage/charge。
- manual “Retry”根据安全分类：same-attempt attach/query；definitely-not-submitted可同Operation next attempt；已有确定失败/
  partial结果的用户retry默认新Operation或发布policy允许的新JobAttempt，并明确新费用/lineage。

## 7. Progress、Queue and Interaction UX

- ProgressObservation 记录 source=worker|provider|derived、value/range/stage、occurred/receivedAt、revision/freshness；
  Provider percent不可信时显示阶段/indeterminate，不插值成精确完成时间。
- progress单调投影只在同 stage/revision内；Provider callback倒序保留事实但UI不回退有害状态。terminal绝不由100%推断。
- queue显示priority class、enteredAt、freshness、estimated range与max queue age。用户级priority不能绕过Site fairness/
  safety/capacity；interactive与batch按发布fair scheduling。
- ETA是模型化estimate，显示range/updatedAt/confidence，不承诺deadline。超过max queue/attempt/reconciliation age自动
  page owner并显示delayed/recovering，而不是无限spinner。
- `waiting_interaction`用于登录/MFA/consent/rights/参数补充/外部接管；InteractionRequest有owner、deadline、safe
  action、reauth return intent。完成interaction重新Finalize current authorization，不重放已完成effect。
- Web disconnect/background不cancel Job；Notification/Center可在完成、interaction、unknown aging时提醒并返回正确Site。

## 8. Cancel、Retry and Unknown

- `CancelOperation`、`CancelJob`、`CancelAttempt`分层。用户操作默认请求Operation policy允许的pending/running jobs，
  但每个 owner返回receipt；Job Runtime不伪造Provider canceled。
- queued/waiting且无effect可确定canceled并释放未commit allocation；dispatching/submitted时进入cancel_requested，调用
  Provider cancel/query。只有canonical outcome证明未执行/取消才释放未用allocation。
- cancel timeout保持reconciling/unknown；late Usage/ProviderCost/Artifact仍处理。已完成candidate不因取消其他candidate删除。
- Agent-attached Job：Run cancel可按冻结policy发送Job cancel intent；detached Job默认继续。Job terminal不直接改GA
  Run terminal；GA tool handle按现有语义等待/返回。
- user Retry/Regenerate/Variation/Extend是专业PRD定义的新visible intent，必须显示会复用哪些Asset/parameter、创建何种
  Operation/Attempt和费用，不作为隐藏auto-retry。
- unknown状态只允许wait/query/Support；不能通过换ModelOption/Provider绕过同effect uncertainty。

## 9. Candidate、Partial and Finalization

### 9.1 Candidate identity

- batch每个output slot在Provider前分配stable candidateId；CandidateResult独立记录state、decision、blob、usage allocation。
- 一个candidate成功不把其他candidate unknown/denied写failed；Operation投影可partial且逐candidate说明。
- 相同bytes只允许Blob物理去重；不同candidate/Operation仍创建不同ArtifactVersion/provenance，不按contentHash合并作品。
- restricted/quarantined candidate内容不出现在普通receipt/notification/Support；safe reason和appeal route来自Trust。

### 9.2 Finalization saga

```text
persist ProviderOutcomeFact + terminal Model/Capability Attempt + AttemptUsageFact/outbox
→ JobAttempt canonical terminal
→ Job finalizing
→ validate Trust publishability + Blob checksum/storage receipt
→ CreateArtifactVersion(operationId,jobId,attemptId,candidateId,idempotency)
→ persist AttemptUsageEvidenceReceipt / canonical ingest tracking
→ persist FinalizationReceiptSet
→ Job completed|partial + cost_pending|cost_final
```

- required output没有Artifact receipt不得completed；Artifact创建失败只retry finalizer，不rerun Provider。
- finalizer等待durable AttemptUsageEvidenceReceipt和committed allocation，不等待异步Rating/Settlement；usage-rating outage
  允许结果completed/cost_pending。
- Provider outcome unknown不得进入finalizing。Blob/Artifact/Usage每个receipt独立幂等；所有齐全才收口。
- finalizer crash/replay、duplicate callback、late moderation均追加事实/新Decision；不覆盖Provider/Artifact历史。
- SiteRelease回滚后，已authorized Operation按冻结spec完成；新Share/export仍按current policy/authorization检查。

## 10. Artifact、Compare and Export

- Artifact是稳定作品identity；ArtifactVersion不可变并引用parent/version/Operation/Job/Attempt/Candidate/Blob/
  parameters/model/policy/rights/consent/provenance。
- Studio compare只改变read selection，不修改版本。comparison set保存用户偏好ref，可重建；metrics不泄漏内容。
- “Use as input/Edit/Extend/Remix/Upscale”创建新DraftRevision/OperationSpec并保留parent lineage；不能原地改ArtifactVersion。
- preview、private download、export、Share、SEO/remix是不同authorization。生成成功不等于可export/share。
- ExportRequest固定source ArtifactVersion、format/profile、locale/a11y metadata、rights/disclosure/watermark、delivery与费用。
  小型同步rendition可直接receipt；跨连接/worker/provider则建RenditionJob，遵循相同attempt/unknown/finalization。
- download每次重新验证Site/subject/project/authorization/epoch/TTL；不把storage URL当长期Asset/Artifact ref。
- export response丢失查询同request/Artifact，不重新生成source；archive/rendition过期可新建delivery，不改source version。

## 11. Cost UX and Settlement

```text
executionState = draft|admission_pending|queued|running|waiting_interaction|cancel_requested|
                 reconciling|finalizing|completed|partial|failed|canceled|unknown

costState = none|estimated|reconfirmation_required|reserved|committed|
            cost_pending|settled|released|correction_pending|reconciliation_required
```

- execution与cost正交：completed/cost_pending可交付，failed/settled可能因Provider已产生可收费effect，canceled也可能收费。
- submit前显示Quote范围/ceiling；authorized后显示reserved/committed，不把Hold叫“已消费”。
- customer charge由Admission冻结RatingPolicy按AttemptUsageFact/candidate delivery/ChargeTreatmentPolicy计算；Job、Gateway、
  ProviderCostFact不决定客户价。
- partial batch逐candidate显示delivered/restricted/unknown与charge category，不在账单暴露受限内容。
- unknown不释放committed allocation；irreconcilable按发布policy形成append-onlysettlement/correction/Support receipt。
- Appeal/takedown/late usage/invoice correction均append correction引用原Usage/Hold/Rating，不回写原fact。
- 用户可打开安全cost breakdown：operation kind、usage dimensions、Quote vs final、Grant bucket projection、settlement/
  correction refs和Support/dispute入口；不显示Provider contract cost。

## 12. User-visible States and Recovery

| State | Meaning | Recovery |
|---|---|---|
| draft_saved / draft_conflict | server revision已保存或并发分叉 | continue/fork/compare/explicit merge |
| quote_ready / reconfirmation_required | estimate有效或提交条件material change | confirm/change parameters/requote |
| admission_pending | 正在校验并reserve，尚未Provider effect | wait/query same identity/cancel if proven safe |
| waiting_dependency | 等上游Job/Asset | view dependency/cancel according policy |
| waiting_interaction | 需登录/consent/rights/input | complete interaction/change/cancel |
| queued / delayed | 已接受排队或超正常age | leave page/wait/cancel/page owner after SLA |
| running / provider_async | effect可能已提交 | view progress/leave/cancel request |
| cancel_requested | cancel intent已记录，outcome未确认 | wait/query；不重复或宣称canceled |
| reconciling / unknown | effect/outcome无法确认 | wait/Support；Retry/fallback disabled |
| finalizing | Provider已结束，正在创建Artifact/Usage receipts | wait；只重试finalizer |
| completed / partial | 全部或部分合格结果可用 | compare/open/export/new explicit operation |
| failed / canceled | canonical owner确认 | safe retry/new operation/Support，显示cost事实 |
| cost_pending / correction_pending | 结果与usage已有，结算/纠错未完 | use result where allowed/wait/view receipt |

## 13. Admin、Support and Operations

- 专用Job Console展示OperationSpec digest、Admission/rootHold、Job DAG、lease epochs、Attempt/effect ledger、Provider facts、
  Candidate/Trust/Blob/Artifact/Usage/finalization/cost timeline；默认mask prompt/asset/content/provider secret。
- typed commands：`CancelOperation`、`RetryDefinitelyNotSubmittedAttempt`、`ReconcileUnknownAttempt`、
  `StealExpiredLease`、`RetryFinalization`、`RebuildJobProjection`、`QuarantineCandidate`、`OpenFinanceExposureCase`。
  每项登记role、Site/resource、reason、risk/step-up/maker-checker、expectedVersion/idempotency、audit/notification/runbook。
- 禁止Admin直接mark Provider succeeded、Job completed、Artifact created、Usage settled或Credit released；禁止direct DB/queue
  mutation。Emergency restrict只能收紧publication/effect，不允许放宽Trust baseline。
- Support只看safe parameters/category、state freshness、quote/cost、owner、receipts与next action；不能下载restricted content、
  查看secret/provider raw body或触发unsafe retry。
- SLO/alerts：admission、queue age/fairness、lease renewal/steal、attempt duration、callback/reconciliation、finalization、
  Artifact/Usage lag、Hold age、notification和cross-Sitedeny spike。每个alert绑定page/ticket、user impact和typed recovery。

## 14. Edge Cases

| Scenario | Expected behavior |
|---|---|
| autosave两设备并发 | baseRevision conflict，fork/merge；不last-write-wins |
| Quote后价格/Option/policy变化 | submit返回reconfirmation diff；不静默涨价/换spec |
| 双击Submit/响应丢失 | same identity返回同Operation/Job/rootHold |
| Finalize authorization成功、queue outbox失败 | reconciler推进同Job或证明无effect后释放；不建第二Operation |
| worker lease过期但Provider已收到 |新workerattach/reconcile；不能按stalled直接rerun |
| callback duplicated/out-of-order | append/reducer幂等；一个Attempt/candidate/finalization |
| cancel与success callback竞态 | 两facts保留，canonical reducer决定；late success仍Artifact/Usage/charge policy |
| batch 4成功1restricted | Operation partial；4个Artifact/usage，restricted独立Decision且不泄漏内容 |
| Provider 100%后timeout | progress不terminal；保持unknown/reconcile |
| Artifact API outage | Job finalizing；retryArtifact receipt，不rerunProvider |
| Usage Rating outage | completed/cost_pending；rootHold committed，async settle |
| Site rollback mid-Job | 冻结spec完成；新download/share按current policy |
| Agent Run结束detached Job继续 | Job独立完成并更新Chat/Library；不改GA terminal |
| retry with different ModelOption | 明确新Operation/Attempt policy和费用；旧unknown不能绕过 |
| same bytes two candidates | Blob可去重，ArtifactVersion/lineage不合并 |

## 15. Acceptance Criteria

### AC-ST-01 — Draft conflict preserves work

```gherkin
Given two devices edit one Draft from the same base revision
When both autosave different parameters or Asset refs
Then one CAS path advances current revision and the other becomes an explicit conflict/fork candidate
And no prompt, mask, lyrics, storyboard, seed or Asset is silently overwritten
```

### AC-ST-02 — Quote requires reconfirmation on material change

```gherkin
Given a user confirmed a Quote range and reservation ceiling
When price, entitlement, ModelOption, policy or a material parameter changes before submit
Then Admission returns reconfirmation_required with a safe diff
And no Operation, Hold or Provider effect starts until the user confirms the new terms
```

### AC-ST-03 — Submit is idempotent across crash boundaries

```gherkin
Given one canonical OperationSpec is retried before and after Prepare, persistence, Finalize and queue outbox
When every retry uses the same key and digest
Then exactly one Operation, root Hold and Job plan exist
And a different digest conflicts without replacing the original receipt
```

### AC-ST-04 — Direct and Agent paths converge

```gherkin
Given Direct Studio and an Agent tool submit equivalent certified OperationSpecs
When both are admitted
Then they use the same Job/Attempt/Artifact/Usage contracts and differ only in source provenance and allocation parent
And GA does not own Job state or create a second billing path
```

### AC-ST-05 — Lease loss cannot duplicate effect

```gherkin
Given a worker loses its lease after persisting a Provider operation key
When another worker claims a higher lease epoch
Then stale writes are fenced and the new worker checks the canonical effect state
And a new Attempt starts only with proof that the prior effect was definitely_not_submitted
```

### AC-ST-06 — Unknown disables retry and fallback

```gherkin
Given Provider submission or outcome is unknown
When automatic policy, user Retry or another worker evaluates the Job
Then no alternate Provider, ModelOption, Attempt or Operation replays the uncertain effect
And the same provider identity is queried until reconciled or irreconcilable under the published deadline
```

### AC-ST-07 — Cancel remains an intent until proven

```gherkin
Given cancel races a submitted Provider Attempt and later success callback
When Job reduces both facts
Then UI remains cancel_requested until canonical outcome is known
And late success, Artifact, Usage and charge facts are processed without claiming the Provider was canceled
```

### AC-ST-08 — Partial candidates stay isolated

```gherkin
Given a batch has allowed, restricted, failed and unknown candidates
When finalization and user projection run
Then every candidate keeps a stable ID, provenance, Decision and usage allocation
And allowed results remain usable without leaking or mislabeling restricted/unknown results
```

### AC-ST-09 — Finalizer replay never reruns Provider

```gherkin
Given Provider outcome and AttemptUsageFact are durable but Blob, Artifact or receipt persistence crashes repeatedly
When finalization resumes
Then each missing receipt is created idempotently and exactly one ArtifactVersion per candidate exists
And no Provider effect, candidate, Usage or customer capture is duplicated
```

### AC-ST-10 — Execution and cost stay orthogonal

```gherkin
Given an Operation completes while Rating is unavailable and another fails after billable Provider effect
When results and costs are rendered
Then the first is completed/cost_pending and remains usable
And the second is failed with its published settled or pending charge facts
And neither execution state is rewritten to make cost easier to explain
```

### AC-ST-11 — Export is separately authorized

```gherkin
Given an ArtifactVersion is privately viewable but lacks current export, rights, disclosure or accessibility eligibility
When export is requested
Then generation success is preserved but no export delivery is issued
And the user receives the exact safe remediation/appeal action without a new generation Provider effect
```

### AC-ST-12 — Cross-Site and callback isolation

```gherkin
Given two Sites share Provider accounts and colliding provider operation identifiers
When callback or internal refs arrive
Then immutable provider-account mapping updates only the matching Site/Attempt
And crossed Operation, Job, Artifact, Hold or callback refs are quarantined without existence disclosure
```

### AC-ST-13 — Browser independence and projection repair

```gherkin
Given an accepted long Job continues while the browser closes and projection events are lost
When the user returns from Chat, Studio or Library
Then owner receipts rebuild the same Job/Candidate/Artifact/cost view
And no Provider, finalizer or settlement action is triggered by browser reconnect
```

### AC-ST-14 — Accessible professional workflow

```gherkin
Given a keyboard, screen-reader, magnification, speech or mobile user uses every common Studio state
When they edit, quote, confirm, monitor, cancel, compare, recover partial/unknown and export
Then every applicable WCAG 2.2 A/AA criterion and PRD-14 output/media contract passes
And progress, cost, candidate and recovery semantics never depend only on pointer, color, motion or canvas
```

## 16. Verification and Release Gates

- Static/contract：Web/GA禁止Provider/lease/Job DB；Job禁止Catalog price/Credit Journal/Artifact DB/Trust Decision writes；
  generated schemas strict、versioned、unknown-field policy明确。
- Property：submit uniqueness、Job DAG acyclic、lease fencing、Attempt reducer、cancel/success race、candidate isolation、
  finalization receipts、Usage/capture correction。
- Integration：PostgreSQL/outbox/queue/object storage/fake Provider/Model Gateway/Artifact/Usage真实边界，不只mock。
- Chaos：每个Prepare/Finalize/queue/lease/I/O/callback/usage/blob/artifact/terminal点crash；duplicate/out-of-order/late fact；
  queue/Provider/Artifact/Rating outage；Site rollback/revocation；browser disconnect。
- E2E：两个独立Site的Direct+Agent同链、long Job离开/返回、partial compare、unknown Support、export authorization、
  mobile/Browser-AT matrix。
- Operational：queue fairness/load/soak、lease saturation、reconciliation deadline、backup/restore、rolling deploy、rollback、
  orphan/finalization/Hold aging runbook。

No-Go：存在duplicate Operation/root Hold/effect；unknown auto retry；lease expiry直接rerun；Job completed缺Artifact或Usage
evidence；Session/GA/Provider决定customer price；浏览器断线影响Job；Admin可mark terminal/direct DB；enabled Surface
缺专业PRD/Trust/a11y/Support evidence。

Wave 4 child architecture Spec 冻结数据库、RPC/event、Job queue/lease/reducer/finalizer、Artifact/Usage接口与clean cut；
PRD-08I/M/V 冻结专业参数和候选UX；PRD-09 冻结Library/Share；Wave 9按每个enabled Site/Profile认证。

## 17. External References and Design Rationale

- [Temporal architecture](https://github.com/temporalio/temporal/blob/main/docs/architecture/README.md)：参考 durable history、
  deterministic orchestration 与“side-effect activity 必须幂等或不可重试”的边界；Kokoro 不因此直接选定Temporal实现。
- [BullMQ stalled-job semantics](https://github.com/taskforcesh/bullmq/issues/439)：其维护者明确说明worker lock丢失会让Job
  再次处理，证明queue/lease不能提供exactly-once Provider effect；Kokoro以Attempt ledger和effect identity兜底。
- [Inngest durable functions](https://github.com/inngest/inngest)：参考step、flow control、priority/concurrency与durable recovery
  产品能力；Kokoro仍保留自己的Operation/Job/Usage/Artifact authority。

外部项目用于模式校准，不预先决定采用Temporal/Inngest/BullMQ。Wave 4 architecture Spec必须以Kokoro状态机、团队
运维成熟度、PostgreSQL/queue需求、license与failure certification做技术选型，不允许“用了工作流框架”替代领域幂等。

## 18. Related Documents

- [Platform、Web、Session 目标架构](2026-07-25-platform-web-session-target-architecture-design.md)
- [PRD-05 Chat](2026-07-25-prd-05-chat-conversation-run-and-interaction.md)
- [PRD-06 Asset](2026-07-25-prd-06-asset-intake-and-attachment-safety.md)
- [Model Control/Gateway](2026-07-25-model-control-gateway-litellm-architecture-design.md)
- [PRD-14 Accessibility](2026-07-25-prd-14-localization-and-accessibility.md)
- [PRD-16 Trust](2026-07-25-prd-16-trust-content-safety-and-media-rights.md)

本文批准不授权实现，也不修改 GA runtime。
