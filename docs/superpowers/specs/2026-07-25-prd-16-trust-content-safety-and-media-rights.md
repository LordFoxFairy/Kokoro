---
artifact: product-requirements-document
prdId: PRD-16
version: "1.0"
created: 2026-07-25
status: internal-review-active
scope: trust-content-safety-upload-generation-media-rights-moderation-appeal-publication
accountableProductRole: Trust & Safety Product Lead
mandatoryCosigners: [Legal, Privacy, Security, Content Operations, Model, Artifact, Support, QA]
engineeringOwner: team:trust-safety-engineering
qaOwner: team:trust-safety-quality
supportOperationsOwner: team:content-operations
namedOwnerAssignmentStatus: assigned-team-responsibility-ids
implementationAuthorized: false
---

# PRD-16：Trust、Content Safety 与 Media Rights

## 1. Overview

### Problem

Chat、上传、Image、Music/Voice、Video/Likeness、Code/Execution 和 Public Share 面临不同的安全、版权、隐私、
未成年人、声音/肖像同意与违法内容风险。若只依赖模型 Provider 的拒绝，Site 无法形成一致政策、解释、申诉、
人工复核和发布控制；若只在输入前拦截，又会漏掉模型输出、Artifact、Share、remix 和后续导出。

### Solution

建立 Platform 最低线之上的版本化 `ContentPolicyProfile`、`RightsBasisRevision`、`ConsentEvidence`、
`DecisionRevision/DecisionHead`、`Appeal` 与 `PublicationAuthorization`。Trust Decision Service 独占 canonical
decision authority；Model/Provider
adapter 只提供信号和执行能力。每个 Operation/Run/Artifact/Share 绑定准确 policy/model/provider revision，
在 input、pre-provider、post-output、artifact/publication 等适用关口执行。用户获得安全、有限披露的原因和恢复
路径；appeal 创建新 Decision，不覆盖历史。

### Users and stories

| ID | User story | Priority |
|---|---|---|
| SAF-US-01 | 用户的输入/上传被限制时能理解原因类别、修正方式和是否可申诉 | P0 |
| SAF-US-02 | 创作者可以记录自己拥有文本、图片、声音、肖像和素材的使用权或同意 | P0 if-enabled |
| SAF-US-03 | 用户只会下载/分享满足当前发布政策的 Artifact，且看到必要披露 | P0 |
| SAF-US-04 | Content operator 能安全复核、下架、处理举报和申诉，而不直接改表或泄漏敏感内容 | P0 |
| SAF-US-05 | Site owner 可以收紧内容范围，但不能低于 Platform 法律/安全底线 | P0 |

## 2. Goals、Metrics and Non-Goals

### Goals

1. 所有 enabled modality 都有 input→execution→output→artifact→publication 的明确安全链。
2. Provider safety 结果不成为 Kokoro policy authority，也不能被另一个 provider 路由绕过。
3. 声音克隆、肖像、深伪和受版权素材有可验证 consent/rights evidence 与撤销路径。
4. Moderation、举报、下架、appeal、通知、Support 和 retention 形成闭环。

### Success Metrics

| Metric | Target |
|---|---:|
| enabled Surface 缺 ContentPolicyProfile/owner/evidence | 0 |
| policy-denied request 仍触发 Provider effect | 0 |
| restricted Artifact 被公开 Share/SEO/export bypass | 0 |
| voice/likeness operation 缺 required ConsentEvidence | 0 |
| Decision 被原地覆盖或 appeal 无新 Decision | 0 |
| cross-Site policy/content/evidence leakage | 0 |
| Critical illegal-content escalation 超 SLA | 0 |
| stale PublicationAuthorization 命中或 consent/rights epoch 后继续 mint | 0 |
| minor/age-unknown 高风险 operation 绕过 deny/review | 0 |
| origin revoke、managed-edge purge、rights/appeal/report SLA 超时未 page | 0 |
| 未授权 evidence access 或 cross-Site Trust reference | 0 |

False-positive、appeal overturn/restoration、review/rights-dispute aging、report timeliness/duplicate、purge partial/unknown、
minor coverage、reviewer exposure/access anomaly、charge correction、user abandonment、provider disagreement 单独按
Site/Profile/modality/policy revision 监控并绑定 alert/action，不能为降低投诉而放宽 Platform 最低线。

### Non-Goals

- 不在本文给出特定司法辖区的法律意见；上线地区由 Legal 发布 policy revision。
- 不承诺检测器完美识别版权、年龄、身份或违法内容。
- 不把所有用户内容默认暴露给人工审核。
- 不允许 Site 配置关闭 Platform mandatory deny、reporting、retention 或 escalation。
- 不把普通模型错误、低质量输出和安全处罚混成一个 Decision。

## 3. Policy and Product Objects

```text
PlatformBaselinePolicy
  scopeKind=platform / revision / modality / jurisdiction/age scope

ContentPolicyProfile
  scopeKind=site / immutable siteId / revision / modality / jurisdiction/age scope
  input/output/publication rules / classifier/provider requirements
  rights/consent/disclosure/watermark/retention/appeal policies

RightsBasisRevision
  siteId / asset+version / rightType / claimant+authority / territory / use / term
  sublicense+remix+publication+transferability / evidence refs / epoch / revokedAt

ConsentEvidence
  siteId / represented party / capturing actor / actor authority+relationship
  verification method / notice digest+locale+a11y / allowed purpose+product+model+public+remix+training scope
  voice/likeness opaque subject ref / expiry / revocation epoch

AgeEligibilityDecision / GuardianAuthorityEvidence
  siteId / subject generation / ageBand|unknown / evidence class / jurisdiction+policy revision / expiry+epoch

DecisionKey
  siteId / targetRef / targetVersion / purpose / stage

DecisionRevision / DecisionHead
  decisionKey / revision / allow|allow_with_restrictions|needs_review|deny|quarantine|takedown
  reasonCategory / safeExplanation / authority / maker / expectedVersion / supersedesRef

SafetyEvaluation
  siteId / target+version / stage / policy+classifier+provider revisions / signals / confidence / encrypted evidence refs

OperationAuthorization / PublicationAuthorization
  siteId / target+version / purpose / audience / decision+policy+rights+consent+restriction epochs / short TTL

Appeal / AbuseReport / RightsDispute / TakedownCase / IllegalContentIncident
ProviderSafetyFact / ContentAccessGrant / EvidencePreservation
```

- 除 `PlatformBaselinePolicy(scopeKind=platform)` 外，所有 Trust 业务对象都携带 immutable `siteId`；所有 target/
  evidence/parent reference 在 command effect point 校验同 Site。跨 Site 复用 consent/rights 必须创建 Site-local
  authorization，不因同邮箱、subject 或 asset hash 继承。global incident 只能使用显式 `GlobalScopeIncident(siteIds)`，
  不合并各 Site 内容或业务对象。
- Platform baseline ∩ Site overlay ∩ provider contractual floor 以 fail-closed 规则编译；Site overlay 只能缩小 allow
  集合或增加 review/disclosure，规则 precedence、unknown 与冲突结果固定在 CompiledPolicyRevision。
- Policy/Decision 发布后不可变；SafetyEvaluation、ProviderSafetyFact、AbuseReport 都只是 facts。只有 Trust Decision
  Service typed command 可用 `DecisionHead` CAS 发布新 `DecisionRevision`；stale expectedVersion 失败，deny/restriction
  precedence 与 purpose/stage 隔离明确，历史均保留。
- Operation/Publication authorization 绑定 current decision/policy/rights/consent/restriction epochs；任一 epoch 变化
  立即失效。
- Content Policy 不保存 Provider secret；模型/分类器 deployment 通过 Model Gateway assignment 引用。
- prompt/content/biometric-like evidence 默认最小化、加密、短 retention、need-to-know；analytics 只用低敏原因类别。
- jurisdiction/age policy 明确 allowed/deny/review/reporting、evidence retention、law-enforcement/legal escalation 和
  user-notice restrictions；Site 不得通过选择宽松地区/Provider 绕过 Platform baseline。`AgeEligibilityDecision` 是
  Site-local、可过期事实，不从脸/声音推断真实年龄作为唯一 authority，也不建立跨 Site 未成年人档案。age unknown
  走目标地区最保护性路径；guardian consent 不能放宽 Platform absolute deny。

## 4. Stage Gates

### 4.1 Input and asset intake

- 文本、URL、文件 metadata/type/size、malware、known-hash 和适用 classifier 先于 Run/Operation admission。
- 可修正的 format/policy 问题保留 draft 并给 `change_parameters`；unsafe/illegal signal fail closed。
- Asset quarantine 时不得进入 model context、share、download 或另一个 Operation；误报走 Appeal/Review。
- rights assertion 不自动证明真实权利；高风险 modality 需要额外 ConsentEvidence 或人工 review。
- known-hash/illegal-content signal 进入专用 IllegalContentIncident：立即隔离、最小必要保存、严格 field access、
  jurisdiction-specific reporting/notification 和 trained reviewer workflow；普通 Support/Content operator 不可查看，
  也不能通过普通 Appeal 恢复法律禁止内容。
- illegal signal 不是法律结论。Incident 状态机固定为 `signal_received -> isolated -> specialist_triage ->
  confirmed_false|confirmed_policy_violation|report_required -> report_submitted|report_unknown|retry_due|escalated ->
  acknowledged -> preservation_review -> closed`。JurisdictionPolicyRevision 冻结 signal threshold、qualified reviewer、
  reporting clock/authority、minimal fields、duplicate identity、preservation 与 notice embargo。report submit 使用稳定
  identity 幂等 reconcile；chain-of-custody receipt 和 restricted evidence vault 每次访问双审/审计。
- suspected/false-positive 有 specialized redress；只有 specialist confirmed legally prohibited content 不可被普通
  Appeal 恢复。Data Rights participant 返回 disclosure-filtered omission/retention，不暴露或删除受保护 evidence。

### 4.2 Before Provider effect

- Admission/OperationAuthorization 冻结 ContentPolicyProfile、rights/consent refs、allowed model/capability、output/
  publication restrictions 和 evaluation requirements。
- 每个 Provider Attempt 前重新验证 policy/restriction/consent epoch；撤销后禁止新 effect。已不可逆提交的 effect
  只 finalization/quarantine/reconcile，不发布。
- Provider adapter 不得通过改模型、关闭 safety setting 或 fallback 绕过 Kokoro Decision；route 只能选择满足
  policy capability 的 certified deployment。
- Provider 返回的 safety/filter/rejection 记录为 `ProviderSafetyFact`，是输入信号和 observed outcome，不直接等于
  canonical Kokoro Decision；Provider 拒绝也不能由 retry 另一 Provider 自动绕过。

### 4.3 Output、Artifact and publication

- output evaluation 与 AttemptUsageFact/Artifact provenance 分开保存；classifier failure 按 policy fail closed 或
  quarantine，不把未知写成 allow。
- ArtifactVersion 记录 parent/source Operation、model/provider/prompt-policy digests、rights/consent refs、Decision
  与 required disclosure/provenance metadata。
- private view/download、export、public Share、SEO、remix 和 external deployment 是不同 eligibility；private allow
  不等于 public allow。
- Decision/restriction 变化可撤销 Share/download 或要求新 review，但不改写历史 Artifact provenance。
- public takedown 要撤销 application authorization，并 purge CDN/cache/search/SEO signed links；各分发点返回 receipt，
  不能只改 DB `shared=false`。第三方已下载副本不能宣称已删除，按 policy 说明和追踪。
- Share/export/signed download/external deploy 每次 mint/refresh/origin fetch 都校验短 TTL
  `PublicationAuthorization` 与 epochs；revocation 立即拒绝 origin 和新 token。takedown 分开记录
  `authorization_revoked`、`purge_in_progress`、`purge_partial|unknown`、`purged_managed_edges`、
  `externally_uncontrolled`。各 managed target 由 outbox 幂等重试、deadline/page/runbook 管理；search request accepted
  不等于 deindexed，第三方副本不宣称删除。

## 5. Modality Rules

### 5.1 Text and Chat

- 区分用户寻求帮助、转换已有内容和生成新内容；安全 explanation 不泄漏检测规则或他人数据。
- tools/URLs/files 的权限与内容安全同时成立；模型说“可以”不能授权外部 effect。

### 5.2 Image

- reference image、face/likeness、minor、sexual content、graphic violence、public figure、logo/copyright 等规则按
  policy revision；inpaint/outpaint 不绕过原 asset restriction。
- mask/crop/upscale/variation 继承 parent lineage 与最低限制，不能通过派生洗掉 Decision。
- minor/age-unknown 的 sexualized likeness、voice clone、deepfake、public/remix 与高风险 training material 按 Platform
  baseline deny 或 specialist review；guardian evidence 不能覆盖 absolute deny。儿童安全 illegal signal 进入专线 Incident。

### 5.3 Music、voice and audio

- lyrics rights、reference audio、voice clone/impersonation、artist/style policy、sample/stem/export 分开。
- 需要 ConsentEvidence 的 voice/likeness 在 training/reference/generation/publication 各 stage 重新验证 scope；
  撤销后禁止新生成与新公开，历史处置由 policy/Legal 决定。
- player/export 显示适用 disclosure、usage restrictions 和来源信息。
- Music 权利按 composition、master、performance、sample/stem、voice/likeness、territory、term、public/remix use 分拆；
  发布前所有 required `RightsBasisRevision` 都必须满足，不能用一个“拥有所有权” assertion 覆盖权利束。

### 5.4 Video and likeness

- storyboard、reference assets、face/voice、minor、sexual/deepfake、public figure 与 election-sensitive scope 单独评估。
- 多 shot/batch 任一 candidate 可 partial quarantine；不能因其他 candidate 成功把受限输出打包发布。

### 5.5 Code、execution and browser

- 内容政策与 Permission/ExecutionTarget security 分离；安全内容不等于允许 shell/network/browser effect。
- malware、credential theft、unauthorized access 等 high-risk category 触发 deny/escalation，不将危险 payload 写入
 普通 logs/Support。

## 6. Rights、Consent and Disclosure

- assertion/consent capture 展示准确用途、Site/product、是否 public/remix、模型/Provider 类别、retention 与撤销。
- 禁止预选、捆绑或用宽泛“拥有所有权”覆盖 voice/likeness 等高风险授权。
- evidence 可能包括 platform challenge、signed release、verified account flow 或经批准 provider；普通上传文件名、
  email knowledge、checkbox 单独不足以满足高风险 consent。
- ConsentEvidence 有 purpose/scope/expiry/epoch；operation authorization 与 publication 都绑定 snapshot。
- agent/guardian/representative authority、主体异议与冲突 evidence 不能 last-write-wins，进入专用 Consent/Rights
  dispute。guardian authority 到期、撤销或 subject 成年产生新 revision，不改写历史，也不覆盖 absolute deny。
- `RightsDispute/TakedownCase` 固定 `received -> identity_authority_check -> temporary_restriction(if policy) ->
  owner_notice -> response|counter_evidence -> legal_reviewer_decision -> territorial_takedown|restore|remain_restricted ->
  appeal|exhausted`，并冻结 clock、notice embargo、misrepresentation/repeat-infringer policy。overturn 后必须发布新
  Decision 和 current-epoch PublicationAuthorization；旧 URL/token 不复活。
- 对适用 Surface，watermark/disclosure/provenance metadata 缺失时 export/share fail；具体 C2PA 或其他标准 adapter
  由 architecture Spec 决定，Kokoro 保留自己的 canonical provenance。

## 7. User Experience、Appeal and Reporting

- 用户只看到 safe reason category、影响范围（input/run/artifact/share）、是否收费、可否修改、review ETA、Appeal
  eligibility 和 Support path；不展示 classifier threshold、举报人身份或敏感 evidence。
- 每个 stage 冻结 `ChargeTreatmentPolicy`：pre-provider deny 通常 capture=0 并释放 reservation；post-effect deny/
  quarantine 可产生 ProviderCostFact，但是否向用户收费由 Admission RatingPolicy 明确，不能由 classifier/Gateway
  临场决定。partial batch逐 candidate解释交付与 charge，不把受限内容暴露在 receipt。
- ChargeTreatmentPolicy 对 pre-effect、provider-submitted、post-effect quarantine、partial delivery、unknown、takedown
  与 appeal overturn 分别冻结 Hold release/capture/cost_pending/settlement/correction；Provider cost 不等于 customer
  charge。unknown 不释放 committed Hold；overturn 后补交付或 Credit correction 以 append-only receipt 引用原
  Usage/Hold，不回写原事实。
- `needs_review`/`quarantine` 显示 owner、freshness、deadline；客户端不能 retry 另一 provider 绕过。
- Appeal 绑定原 Decision/policy/evidence snapshot，允许新 evidence；reviewer separation、SLA、allowed outcomes 与
  exhaustion policy 由 revision 冻结，并包含 filing window、standing、实际通知/embargo、语言/无障碍、evidence
  intake、原 maker 隔离、conflict-of-interest、aging escalation 与 external remedy。结果产生新 Decision 和通知；
  overturn 先恢复适用 private 权限，再重新计算 public/export/remix eligibility，不自动公开。
- public Share 有 report abuse；紧急 takedown 立即撤流量，后续保留 evidence、通知 owner 并开放适用 Appeal。
- AbuseReport 可由未登录访问者提交 Site-bound、rate-limited safe intake；不向被举报者泄漏 reporter identity。
  malicious/duplicate reports 有 abuse control，但不能因 report volume 自动处罚；urgent illegal signal走专用通道。
- Abuse intake 只接受 canonical Site shareRef，不抓任意 URL；附件先进入 Asset scan/quarantine，CSRF/bot/rate-limit
  使用 Site-local pseudonymous key。duplicate clustering 保留每一条 report fact；trusted flagger 只影响优先级，
  reporter receipt/status 不泄露 owner/action，被举报者 export/Support projection 永不含 reporter identity/network/evidence。

## 8. Admin、Support and Operations

- Content Operations 使用专用 queues：automated review、user appeal、abuse report、urgent illegal-content、rights/
  consent dispute、takedown。普通 Admin ResourceTable 不执行 Decision。
- 查看原内容需 action/resource/field/TTL-bound ContentAccessGrant、reason、审计；默认使用 redacted preview。
- high-risk allow/takedown、mass action、policy publish 和 retention exception 要 step-up/maker-checker。
- Support 只看 safe Decision timeline/CTA，不能改 classifier、Decision、rights evidence 或直接解除 quarantine。
- emergency policy kill switch 可阻止新 effect/share；历史 Artifact 扫描和通知由 durable campaign workflow 执行。
- policy lifecycle 为 `compile -> simulation -> candidate -> canary -> active -> superseded|rolled_back`；rollback 不得低于
  current Platform minimum。queued Attempt、existing Artifact/Share 的 reevaluation 使用 durable campaign，记录
  snapshot/cursor/checkpoint/coverage、partial/unknown/backpressure、通知与 completion receipt；kill switch failure page。
- Reviewer wellness policy 提供 exposure minimization、blur/redaction、task rotation、break/escalation 和 access logging；
  不以生产效率要求普通 operator 暴露于未最小化的高危内容。
- 最高危 queue 使用专门 clearance、双人或专岗；viewer watermarked、默认 blur/mute/frame-sample/redacted transcript，
  禁止 download/copy，session TTL 与 operator/access epoch 每次查看重验并可即时撤销。assignment 避免连续暴露和
  跨站信息；wellness break 不扣 reviewer SLA。

### 8.1 OperatorCommandMatrix annex

下列 typed command 均登记 role、Site/Global scope、risk、reason、step-up、maker-checker、expectedVersion、
idempotency/parameter digest、PII masking、audit、user notification、SLA、receipt 与 recovery runbook：

| Command | Authority and invariant |
|---|---|
| `PublishPolicyRevision` | Trust Policy Publisher；必须 simulation/canary，不能低于 Platform baseline |
| `IssueOrSupersedeDecision` | Trust Decision Service/reviewer；DecisionHead CAS，fact producer 无权调用 |
| `GrantContentAccess` / `RevokeContentAccess` | Security-scoped JIT；grant 不授予 Decision 权且每次查看重验 |
| `RevokePublication` | Site-scoped immediate restriction；同步 revoke origin authorization |
| `StartOrRetryPurgeCampaign` | Distribution operator；不得把 accepted/deindexed 或 partial/complete 混写 |
| `ResolveAppeal` | 与原 maker 隔离；不能越过 independent rights/consent restriction |
| `ResolveRightsDispute` | Rights specialist/Legal；按 territory/use 输出新 restriction/decision |
| `CreateOrSubmitIllegalContentReport` | qualified specialist；stable report identity、clock、dual control |
| `ApplyOrReleaseEvidencePreservation` | Legal/Data Governance；bounded scope，release 只触发重编译 |
| `RunHistoricalRescan` | campaign authority；snapshot/cursor/coverage/receipt 必填 |
| `EmergencyRestrict` | 允许单人短 TTL 立即收紧并 page/事后 checker；任何命令都不能紧急放宽 baseline |

所有命令禁止 ResourceTable/direct DB mutation；同一 operator 不得 request+approve+execute 高风险命令。

### 8.2 Evidence and provider-fact governance

- `ProviderSafetyFact` 固定 siteId、invocation/attempt、provider tenant/account/deployment revision、provider fact ID、
  occurred/receivedAt、payload digest、signature verification、raw evidence ref。duplicate/out-of-order/late 合法 facts
  append/reduce；unmatched/wrong-Site/invalid-signature callback quarantine，不改变 Decision 或 charge。
- evaluation raw content、derived signal、Decision rationale、appeal、rights、illegal incident 与 access audit 分别绑定
  retention class、start event、expiry、region、LegalHold/preservation、deidentify/delete 与 destruction receipt。
  consent revoke 不删除 mandatory evidence；account deletion 不破坏已发布/已报告审计链。

## 9. User-visible States and Recovery

| State | Meaning | Recovery |
|---|---|---|
| allowed | 当前用途允许 | continue |
| allowed_with_restrictions | 允许但限制 export/share/remix 或需 disclosure | accept/continue/change parameters |
| needs_review | 等待人工/增强检查 | wait/provide evidence/Support |
| review_overdue / specialist_review | 已超普通 review SLA 或进入专线 | wait/escalated owner/safe notice；不暴露 evidence |
| denied | 当前请求不允许 | safe explanation/change parameters/appeal if eligible |
| quarantined | Artifact/Asset 不可使用或发布 | wait/appeal/delete where allowed |
| authorization_revoked / purge_pending / purge_partial | origin 已拒绝新访问，managed edges 尚在清退 | view truthful scope/wait/appeal；不声称全部副本删除 |
| rights_dispute_pending | 独立权利争议处理中 | submit counter-evidence/wait；不由 moderation appeal 绕过 |
| appeal_pending / appeal_exhausted | 新 review 进行中或内部救济结束 | provide evidence/wait/external remedy where applicable |
| notice_restricted | 专门法律流程限制可披露通知 | safe generic status/specialist path |

## 10. Edge Cases

| Scenario | Expected behavior |
|---|---|
| Provider allow、Kokoro deny | deny；Provider 不覆盖 policy |
| classifier timeout | 按 stage policy quarantine/fail closed，不猜 allow |
| consent 在 queued Job 中撤销 | 新 Attempt 拒绝；已提交 effect finalizes into quarantine |
| batch 4 个成功、1 个 restricted | partial result只交付合格 candidate，restricted candidate quarantine 且费用解释 |
| private Artifact 后来 public Share | 重新做 PublicationEligibility，不复用 private allow |
| parent restricted、派生 variation | 继承 restriction/lineage，不能洗白 |
| Site policy 比 Platform 更宽松 | compile/publish 拒绝 |
| Appeal overturn 但 rights/consent restriction 仍在 | 新 Decision supersedes 原 moderation restriction；只恢复当前所有 gate 允许的 surface，不自动 republish |
| illegal-content mandatory handling | specialized incident/reporting/retention; ordinary Appeal/Support cannot restore |
| public takedown with CDN/search outage | origin authorization 立即 revoke；其余 target 继续，失败 target retry/page，UI 保持 purge_partial/unknown |
| Provider safety deny followed by fallback | canonical policy/reconciliation; no automatic alternate-provider bypass |
| anonymous abuse report flood | canonical Site shareRef + safe attachment intake/rate-limit/dedupe/triage；volume 不成为 Decision |
| Site B 引用 Site A consent/Decision | effect 前拒绝且不泄漏 Site A 是否存在 |
| minor/age unknown 请求 voice/public remix | Platform most-protective deny/review；checkbox/guardian 不能覆盖 absolute deny |

## 11. Acceptance Criteria

### AC-SAF-01 — Policy before effect

```gherkin
Given input is denied or required ConsentEvidence is absent
When a Run or Operation is submitted
Then Admission denies before Model, Capability or Job Provider effect
And no Hold capture occurs beyond documented validation cost policy
```

### AC-SAF-02 — Site cannot weaken Platform baseline

```gherkin
Given a Site policy candidate allows content denied by the Platform minimum revision
When SiteRelease compiles
Then policy compatibility fails and the candidate cannot publish
```

### AC-SAF-03 — Consent revocation during execution

```gherkin
Given a media Job is queued with valid consent
When consent epoch revokes before the next Provider Attempt
Then no new Attempt starts
And an already irreversible Attempt may only finalize into quarantine/reconciliation, not publication
```

### AC-SAF-04 — Separate private and public eligibility

```gherkin
Given an Artifact is allowed for private viewing but not yet certified for public use
When a user creates Share, SEO, remix or external deployment
Then PublicationEligibility evaluates current policy, rights, consent and disclosure
And no public URL or export is created without an allow decision
```

### AC-SAF-05 — Appeal preserves decisions

```gherkin
Given a deny or takedown Decision exists
When an eligible Appeal with new evidence succeeds
Then a new Decision supersedes the old one and applicable access is restored
And the original Decision, evidence, reviewer and timestamp remain immutable
```

### AC-SAF-06 — Cross-provider fallback cannot bypass safety

```gherkin
Given the preferred model deployment is unavailable and fallback exists
When Model Gateway resolves a route
Then every candidate satisfies the frozen policy capability and safety certification
And an uncertified deployment is excluded even if technically healthy
```

### AC-SAF-07 — Batch partial isolation

```gherkin
Given one candidate in a batch is quarantined and others are allowed
When Job finalization completes
Then only allowed candidates produce user-visible ArtifactVersions
And the restricted candidate, Usage and Decision retain separate provenance without leaking content
```

### AC-SAF-08 — Provider safety is not policy authority

```gherkin
Given one Provider returns a safety deny or filter fact
When another deployment is otherwise available
Then Kokoro records the ProviderSafetyFact and applies canonical policy/reconciliation
And it does not automatically retry another Provider to bypass the observed restriction
```

### AC-SAF-09 — Charge treatment is frozen

```gherkin
Given content is denied before Provider effect or quarantined after a paid Provider Attempt
When settlement runs
Then pre-effect denial captures no user usage beyond the published validation policy
And post-effect customer charge follows the Admission-frozen RatingPolicy rather than classifier or Gateway discretion
```

### AC-SAF-10 — Public takedown reaches distribution edges

```gherkin
Given an Artifact has CDN, Share, search, SEO and signed-download distribution
When an urgent takedown commits
Then new origin authorization is denied immediately and every managed target enters an idempotent receipt-tracked purge workflow
And any missing or unknown target receipt keeps the truthful state purge_partial or purge_unknown with retry and paging
And the system does not claim third-party downloaded copies were deleted
```

### AC-SAF-11 — Illegal-content incident isolation

```gherkin
Given a mandatory illegal-content signal matches the current jurisdiction policy
When intake or output evaluation processes it
Then content is isolated with minimum necessary evidence and specialized access/reporting workflow
And ordinary Support, Content operators and normal Appeal cannot expose or restore prohibited content
```

### AC-SAF-12 — Abuse reports do not become votes

```gherkin
Given many duplicate or malicious anonymous reports target one public Artifact
When abuse controls and triage run
Then reports are rate-limited, deduplicated and risk-ranked without revealing reporters
And report volume alone cannot create a final deny/takedown Decision
```

### AC-SAF-13 — Cross-Site Trust isolation

```gherkin
Given Site A owns ConsentEvidence, Decision and Artifact references
When Site B submits an Operation or operator command using those references
Then authorization rejects before evidence disclosure or Provider effect
And no existence, timing, policy or content signal from Site A is returned
```

### AC-SAF-14 — Deterministic concurrent Decision

```gherkin
Given policy, Provider and reviewer facts arrive concurrently for one DecisionKey
When Trust reduces facts and publishes the head
Then exactly one DecisionHead version commits by expectedVersion
And every stale writer re-evaluates rather than overwriting the current head
```

### AC-SAF-15 — Illegal signal is not legal confirmation

```gherkin
Given an unconfirmed classifier or hash signal marks content as potentially reportable
When intake processes the signal
Then content is isolated and routed to specialist triage
And no statutory report or ordinary reviewer disclosure occurs without the required authority decision
```

### AC-SAF-16 — Reporting outage is reconciled

```gherkin
Given a confirmed reportable incident has a running reporting clock
When the authority endpoint times out
Then the same report identity is reconciled, retried and paged without duplicate submission
And the incident remains report_unknown or retry_due until a verifiable receipt arrives
```

### AC-SAF-17 — Minor or age-unknown high-risk media

```gherkin
Given represented-subject age is minor or unknown
When voice clone, sexualized likeness, deepfake or public remix is requested
Then the Platform baseline denies or requires the frozen specialist route
And Site overlay, ordinary checkbox or guardian evidence cannot override an absolute deny
```

### AC-SAF-18 — Rights bundle and counter-decision

```gherkin
Given a Music Artifact has master rights but lacks required composition, sample or publication scope
When export or Share is requested
Then no PublicationAuthorization is issued and a safe missing-right category is shown
When a later takedown dispute is overturned
Then restoration requires a new Rights Decision and current epochs, while old URLs remain invalid
```

### AC-SAF-19 — Publication epoch race

```gherkin
Given a PublicationAuthorization was minted before consent or restriction revocation
When a new token, origin fetch or controlled download is requested
Then current epochs reject the stale authorization
And purge progress remains an independent truthful workflow state
```

### AC-SAF-20 — Partial edge purge

```gherkin
Given origin authorization is revoked but one managed CDN or search target is unavailable
When takedown reconciliation runs
Then available targets continue, the failed target retries and pages its owner
And the system remains purge_partial or purge_unknown without claiming full purge or deindexing
```

### AC-SAF-21 — Appeal cannot bypass independent restriction

```gherkin
Given a moderation denial is overturned while a rights or consent restriction remains active
When restoration is evaluated
Then the moderation Decision is superseded
And publication, export and remix remain blocked until every current eligibility gate allows them
```

### AC-SAF-22 — Append-only charge correction

```gherkin
Given a post-effect quarantined result was settled under its frozen ChargeTreatmentPolicy
When Appeal later overturns or confirms the restriction
Then delivery or Credit correction appends a receipt referencing the original Usage and Hold
And no original Usage, ProviderCostFact or settlement fact is rewritten or exposes restricted content
```

### AC-SAF-23 — ContentAccessGrant confinement

```gherkin
Given an operator holds a ContentAccessGrant for one Site, field set, action and evidence revision
When another Site, raw derivative, expired TTL or unlisted action is requested
Then access is denied and audited
And Support cannot widen or reuse the grant
```

### AC-SAF-24 — Evidence preservation wins deletion race

```gherkin
Given account deletion and legal EvidencePreservation arrive concurrently
When a destructive participant plan executes
Then a fresh plan and epoch check protects only scoped evidence with a retention receipt
And unrelated data continues deletion while exports reveal only a safe omission category
```

## 12. Dependencies、Risks and Milestones

| Risk/Dependency | Mitigation |
|---|---|
| Provider policy 被当最终 authority | canonical Kokoro policy/Decision + adapter signal only |
| 用户声明被当充分证据 | modality/risk-specific evidence policy、review、revocation epoch |
| 内容审核扩大内部可见性 | redacted projections、JIT ContentAccessGrant、audit、retention |
| policy update 破坏在途执行 | frozen authorization + effect-point epoch + quarantine finalization |
| 派生/导出洗掉限制 | Artifact lineage inheritance + separate publication eligibility |
| false positive 无救济 | state/CTA/SLA/Appeal/new Decision/support metrics |

Wave 1 冻结 policy/decision/evidence/appeal contracts；Wave 3/4 接入 Chat/Asset/Operation/Artifact stage gates；
Wave 7 完成 Content Ops/Admin/Support；Wave 9 使用真实 provider/classifier failure、consent revoke、appeal、takedown
和 public Share negative matrix 认证。媒体专项 PRD-08I/M/V 必须细化参数和用户体验，但不能弱化本文不变量。

内部批准前，全部 P0/P1 必须关闭；Legal 必须为每个 launch jurisdiction 发布 illegal reporting、minor、rights/
takedown、notice/retention matrix，缺失时 SiteRelease fail closed。认证必须覆盖 cross-Site negative matrix、Decision
CAS/replay、Provider callback spoof/late、illegal-report outage/false positive、minor high-risk、rights counter-evidence、
origin revoke + partial purge、appeal aging、reviewer access revoke、Data Rights/Preservation race 与 charge correction。
上述边界均属于 Platform Trust/Asset/Artifact/Job/Gateway/Admin/Data Governance；不要求改变 GA graph、assembly、tool、
checkpoint、effect、Handoff、namespace 或 terminal semantics。

本文批准不授权实现，也不修改 GA runtime。
