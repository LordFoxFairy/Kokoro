---
artifact: product-requirements-document
prdId: PRD-11
version: "1.0"
created: 2026-07-25
status: internal-review-active
scope: user-support-center-case-lifecycle-evidence-sla-escalation-recovery-compensation
accountableProductRole: Operations & Support PM
mandatoryCosigners: [Security, Finance, Risk, Data Governance, Commerce, Identity, Runtime, QA]
engineeringOwner: team:support-platform-engineering
qaOwner: team:support-quality
supportOperationsOwner: team:core-support-operations
namedOwnerAssignmentStatus: assigned-team-responsibility-ids
implementationAuthorized: false
---

# PRD-11：Support、Recovery 与 Appeals

## 1. Overview

### Problem

生产系统不能把“联系支持”当一个邮箱链接，也不能让 Support 直接改数据库解决卡密、积分或 Job 问题。
Kokoro 的 Redemption、Credit、Run、Job、Artifact、Moderation 和 Data Rights 都存在异步、unknown、人工审核
或法定保留状态；没有正式 Case 生命周期、身份核验、SLA、Evidence、升级、补偿和用户确认，就无法称为
完整业务闭环。

### Solution

建立 Site-scoped User Support Center 与 Operator Case Console。SupportCase 只拥有支持协作状态和 opaque
领域 refs，不复制或修改业务真源；所有恢复、补偿、撤销、补发、申诉都路由到领域 command，并将 receipt
回写 Case timeline。Case 关闭前必须有明确 Resolution、用户通知和高风险场景的用户确认/到期规则。

### Users and stories

| ID | User story | Priority |
|---|---|---|
| SUP-US-01 | 用户能从错误或账户中心提交 Case 并安全携带上下文 | P0 |
| SUP-US-02 | 用户能看到谁需要行动、SLA、消息、证据和最终结果 | P0 |
| SUP-US-03 | 坐席能在 Site scope 内诊断 Redemption/Credit/Run/Job/Artifact 时间线 | P0 |
| SUP-US-04 | 高风险补偿经过领域工作流、step-up 和 maker-checker，而不是直接改表 | P0 |
| SUP-US-05 | 用户可以申诉 moderation/risk/reversal 决定并获得新 Decision | P0 |
| SUP-US-06 | Support 搜索不会泄漏其他 Site 是否存在同邮箱用户 | P0 |

## 2. Goals、Metrics and Non-Goals

### Goals

- 用户入口、身份核验、消息/Evidence、SLA、分派、升级、Resolution 和 reopen 全闭环。
- 每个 Case kind 有标准 intake、required evidence、允许命令、禁止动作、runbook 和 notification。
- Support 无业务数据库写权限；补偿、reversal、replacement、retry 都有领域 receipt。
- Site isolation、PII masking、break-glass 和审计达到生产标准。

### Metrics

| Metric | Target |
|---|---:|
| P0 security/cross-site/duplicate charge/data loss acknowledgement | ≤ 15m，24×7 |
| core-standard 普通 Case 首次响应 | p90 ≤ 4 support hours |
| core-standard 普通 Case 解决 | p90 ≤ 2 business days |
| 无 Resolution receipt 关闭的高风险 Case | 0 |
| Support 直接数据库写或非审计补偿 | 0 |
| 跨 Site 搜索/PII 泄漏 | 0 |
| reopen rate | 按 Case kind 监控；高于冻结阈值自动质量 review |
| compensation/reversal error | 0 duplicate；100% 可追踪 source/approval |

### Non-Goals

- SupportCase 不拥有 Redemption、Credit、Run、Job、Artifact、Risk 或 Deletion 状态。
- 不提供任意 impersonation 或“以用户身份执行全部操作”。
- 不允许上传卡密原文、Provider secret、完整支付敏感数据或未脱敏日志。
- 不用通用 ResourceTable 替代专用 Case workflow。
- 不承诺所有问题都可恢复；无法恢复时必须给出事实、保留项、申诉/补救和最终说明。

## 3. Case Model

```text
SupportCase
  siteId / caseId / caseKind / severity
  requesterSubjectGeneration / subjectRefs / correlationRefs
  status / priority / queue / assignee
  verificationState / slaRevision
  createdAt / updatedAt / nextActionDueAt

CaseMessage
  public_user | public_support | internal_note | system_fact

CaseEvidenceRef
  immutable evidence/provenance/classification/sanitized derivative/domain receipt refs

CaseTimelineProjection
  immutable domain facts + support actions

Escalation
  target team / reason / SLA / acknowledgement

Resolution
  resolutionKind / domainReceiptRefs / userImpact
  notificationRef / confirmationPolicy / closedBy
```

CaseMessage 和 Timeline 不复制敏感业务 payload；使用安全摘要与 opaque refs。Domain owner API 决定可向该
Operator/Site 返回哪些字段。SupportCase 的租户 owner 永远是 `siteId`，用户可见 ownership 只绑定
`requesterSubjectGeneration`；subjectRefs、Workspace/Project ownership、相同 email 或 operator assignment 都
不授予用户访问权，额外参与者必须通过显式 `CaseParticipantGrant`。Membership/Workspace owner 变化和 Project
删除不得隐式转移或删除 Case。

## 4. Case Kinds

| Kind | Intake | Domain owner/action |
|---|---|---|
| identity_access | re-auth/device/session/email evidence | Identity recovery/revoke/change workflow |
| redeem_invalid_or_unavailable | safe fingerprint/correlation，不收 Code 原文 | Redeem status/support-safe lookup |
| redeem_not_received | Redemption/idempotency receipt refs | Fulfillment recovery/reconciliation |
| redeem_wrong_binding | identity verification + Redemption ref | source reversal + replacement；不转移 owner |
| compromised_batch | Campaign/Redemption refs | scoped reversal/replacement/appeal |
| credit_balance_dispute | Grant/Hold/Usage/Settlement refs | usage-rating/Credit reconciliation/correction |
| payment_refund_dispute | Payment/Refund/Dispute refs | Payment domain original-route workflow |
| run_or_job_unknown | Run/Job/Attempt/correlation refs | GA/Job/Gateway reconciler，禁止 blind retry |
| artifact_missing_or_export | Artifact/Blob/export refs | Artifact repair/rendition/export/GC check |
| content_moderation_appeal | decision/artifact/policy refs | new Appeal → new Risk/Moderation Decision |
| account_export_deletion | governance request/participant refs | Data Governance workflow |
| site_or_security_incident | SiteRelease/incident/security refs | Security/SRE incident command；P0 escalation |

新增 Case kind 必须声明 owner、safe intake、allowed commands、SLA、notification 和 retention；未知 kind 进入
triage，不允许坐席自由执行高风险命令。

Case kind 同时受 SiteRelease/Profile 和历史 domain fact 约束。从未存在 Payment Fact 的 redeem-only Site 不展示
且拒绝创建 `payment_refund_dispute`，也不创建零金额或虚构的 Order、Payment、Invoice 或 Refund；若 Site 历史上
存在 Payment Fact，只允许引用原 Payment 与原 ProviderAccount 的 refund/dispute/reconciliation。外部售卡资金
退款只保存外部 reference，不生成 Platform Payment/Refund Fact。

## 5. User Support Center

### Entry

- 每个可解释错误提供稳定 error code、correlation ref、RecoveryAction 和适用 Case deep link。
- Account 中有 Case 列表、状态、SLA、谁需行动、public messages、Evidence、Resolution 和 reopen/appeal。
- 系统预填安全 refs，不预填 prompt、Code 原文、secret 或其他 Site 数据。
- 未登录安全事件通过 Site-bound recovery flow 建立 provisional requester，完成核验后才能查看 Case。

### Submission

用户选择问题类型、影响、描述并上传允许的 Evidence。提交前展示隐私/禁止上传信息、预计响应和紧急安全
渠道。重复提交按 subject/correlation/time 提示关联现有 Case，但不自动合并不同用户/安全事件。

### User-visible states

```text
draft
submitted
verification_required
triaged
in_progress
waiting_user
waiting_internal
escalated
resolved
closed
reopened
```

每个状态显示 next actor、due time、最新 public update 和 CTA。`resolved` 表示 Domain receipt 已存在且已通知；
`closed` 表示确认政策满足。内部 `unknown/reconciliation` 映射为 waiting_internal，不误称 failed/succeeded。

## 6. Operator Workflow

```text
intake → verify Site/requester/subject → classify/severity
→ assign queue/owner/SLA
→ inspect safe cross-domain timeline
→ request user evidence or execute allowed domain command
→ wait for authoritative receipt
→ publish Resolution + notification
→ user confirms or confirmation window expires
→ close / reopen
```

### Triage and queues

Queues 至少区分 Identity、Commerce/Redeem、Finance、Runtime、Artifact/Trust、Data Governance、Site/Security。
自动 routing 只建议，不改变 accountable owner；unassigned/aging/SLA breach 有 alert/escalation。

### Identity verification

核验强度按动作风险：一般状态查询用已认证 session；账号恢复/owner transfer/财务补偿/数据导出需要 re-auth、
MFA、额外 Evidence 或 Security approval。Support 不询问密码、MFA code、卡密原文或 secret。

任何 high-risk domain command 必须携带不可转移、单次消费的
`VerificationGrant(caseId, siteId, requesterSubjectGeneration, verifiedSubjectRef, assuranceLevel,
allowedActionDigest, methods, identity/restrictionEpoch, issuedAt, expiresAt, verifierRef)`。领域 owner 在 effect point
校验 audience、subject、action/parameter digest、TTL 与当前 epoch，并以 CAS 消费。email knowledge、已登录但
过期 session、Case ownership 或坐席判断不能替代该 Grant，也不能把一次低 assurance 核验复用于另一动作。

### Timeline

按 correlation refs 聚合 User/Workspace/Redemption/Fulfillment/Grant/Hold/Run/Job/Attempt/Artifact/Decision/
Notification 的安全投影，显示 source owner、revision、时间和状态新鲜度。投影不可用不授权直接查 DB。
Run/Job 投影在 Platform/Session 上游按 opaque refs 授权解析；任何 GA request/manifest/event contract 都不得包含
`siteId/userId/ownerId/workspaceId/projectId`，普通坐席和用户也不得看到 namespace。

## 7. Domain Commands and Compensation

Support 只能选择 Case kind 注册的 typed command：

- 赠送：`IssueAdminGrantAcquisition`，含 reason、scope、amount、expiry、approval；不是 Journal 直写。
- 账务纠错：`CreateCorrectionTransaction` 引用原交易；append-only reversal/correction。
- 卡密误绑：`RevokeRedemption` + `IssueReplacementCode`，不能转移已兑 Code owner。
- 运行恢复：trigger owner reconciler/query/reproject；unknown effect 禁止 retry。
- Artifact：rebuild rendition/export 或 restore within retention；不伪造 Blob。
- Risk/Moderation：创建 Appeal 和新 Decision，不覆盖历史决定。
- Identity/Workspace：调用 recovery/transfer/revoke workflow，不直接改 credential/owner。

高风险命令携带 caseId、reason、expectedVersion、idempotency、OperatorPrincipal、Site/Global scope、step-up 和
approvalRef。结果必须返回 domain receipt；timeout 先查询同 identity。

Reopen 只重开 Support 协作；Appeal 是 domain-owned 新 aggregate。每个 appealable decision kind 必须冻结
eligibility、filing window、required evidence、reviewer separation、SLA、allowed outcomes 与 exhaustion policy；
Appeal 总是创建新 Decision/Resolution fact，原决定不可覆盖，原 maker/assignee 不得独自作为最终 checker。

## 8. Maker-Checker、Break-Glass and Impersonation

- maker-checker 适用于财务/Grant、Redemption mass action、GlobalScope incident、owner recovery、删除例外、
  secret/security。
- checker 必须是不同 Operator，权限与 step-up 独立验证；自批、过期批准、参数 digest 变化拒绝。
- BreakGlassGrant 单次、短 TTL、scope/resource/action bound、必须 incident/case reason、实时 page 和事后 review。
- BreakGlassGrant 不得把 Site Case 升格为跨 Site identity search，也不得合并相同 email、FederatedIdentity、
  Workspace、Credit 或历史。多 Site 安全事件创建独立 `GlobalScopeIncident`，显式列出允许的 siteIds/resources/
  fields/actions，逐 Site 返回隔离投影；禁止任意查询、direct DB、secret/credential 读取和绕过 domain command。
- 默认无 impersonation。确有用户 UI 诊断时使用只读、红色 banner、短期、禁止敏感/财务 mutation 的
  SupportViewGrant；所有读取审计，用户按 policy 通知。

## 9. Evidence、Privacy and Retention

- Upload 走 Asset scan/quarantine、type/size allowlist、encryption、Site scope 和 retention。
- Code 只接受 safe fingerprint/Redemption ref；检测到疑似明文立即 redact/quarantine/security event。
- Payment 只接受内部 refs和 Provider-safe identifiers，不收 PAN/CVC。
- prompt/content 默认不展示；只有明确 consent、need-to-know 和 ContentAccessGrant 才可查看最小片段。
- internal notes 不对用户显示，但受 Export/Retention/LegalHold 分类；不得写歧视/无关 PII。
- Case 删除随 Data Governance participant 执行；强制 Audit/Financial/Security facts 去标识后保留。
- CaseEvidenceRef 保存 immutable evidenceId、siteId、uploader principal、capturedAt、content hash、media/type、
  scan-policy revision/result、classification、retention/legalHold refs、sanitizedDerivativeRef 与 provenance。原件与
  派生件访问都需短期 need-to-know ContentAccessGrant 并逐次审计；编辑创建新 revision，不覆盖原证据。

## 10. SLA、Escalation and Notifications

SupportTierRevision 冻结 business calendar、severity、first response、update cadence、resolution target、escalation
chain 和 breach communication。`core-standard`：P0 24×7/15m acknowledgement；普通 Case 5×9、p90 4h first
response、p90 2 business days resolution。

该 revision 还必须冻结 acknowledgement/first-response/update/resolution 的 clockStart、calendar timezone、
pauseable states、maximum waiting-user pause、severity-change recalculation、merge/reopen inheritance 与 breach
action；`waiting_internal` 不暂停 SLA。p90 是组合 SLO，不替代每个 Case 固化的 dueAt 与 breach timeline。

Notification mandatory events：submitted、verification required、support reply、waiting user、escalated、SLA breach、
resolved、compensation/reversal/replacement、closed/reopened。Delivery failure 不改变 Case status，但进入 retry/DLQ
并在 Support Center 保持可见。

高风险 Case 关闭要求 durable NotificationRequest receipt、Support Center 可见 Resolution，并满足 confirmation/
appeal policy；外部 channel delivery failure 本身不阻止关闭，但必须完成冻结的 retry/fallback/breach-notice policy
并保留 Delivery timeline。缺 NotificationRequest receipt，或仍在有效 confirmation/appeal window 时不得关闭。

## 11. Edge Cases

| Scenario | Expected behavior |
|---|---|
| 用户用相同邮箱在两 Site 搜索 Case | 每 Site 只返回本地 Case，不泄漏另站存在性 |
| 重复提交同一问题 | 提示/关联现有 Case；不丢新 Evidence，不跨 requester 自动 merge |
| Case merge 后原链接 | 保留 alias/timeline，权限分别校验，不删除原审计 |
| 用户在 waiting_user 期间不响应 | 到期提醒/自动 resolve-close policy；可 reopen，不伪造解决 |
| Domain command timeout | 查询同 idempotency receipt；不再次补偿/退款/重跑 effect |
| Operator 权限在处理中被撤销 | 后续读取/命令拒绝，重新分派；已提交 command 由领域收口 |
| P0 Case Notification 失败 | Case/incident 继续，切备用渠道并 page owner |
| Evidence 扫描失败 | quarantine，Case 可继续但不能下载/用于执行 |
| 已消费 Grant 的 mass reversal | 独立 RecoveryCase/appeal，不扣其他 source，不伪造负余额 |
| Account 删除中收到 Dispute | mandatory fact/Case 接收并以 surrogate subject 处理 |
| Case resolved 后用户否认结果 | reopen 或 Appeal，保留原 Resolution，不覆盖历史 |
| Workspace ownership 或 Membership 变化 | 不改变 Case requester/access；额外用户需要 CaseParticipantGrant |
| 低 assurance verification 被用于高风险命令 | domain owner 因 assurance/action digest/TTL 不匹配拒绝 |
| redeem-only Site 无 Payment history 创建 Payment Case | unsupported kind；Order/Payment/Invoice/Refund 写入均为零 |
| Site Case 使用 BreakGlass 搜索同邮箱其他 Site | 拒绝；只能由显式 GlobalScopeIncident 访问列明资源 |

## 12. Acceptance Criteria

### AC-SUP-01 — Site-private search

```gherkin
Given Site A and Site B contain users with the same email
When a Site A Support operator searches that email
Then only Site A authorized subjects and Cases are returned
And no count, error or timing signal reveals Site B existence
```

### AC-SUP-02 — No direct compensation

```gherkin
Given a user disputes Credit balance
When Support approves a correction
Then a typed CorrectionTransaction command with maker-checker creates an append-only domain receipt
And Support never updates CreditJournal or balance tables directly
```

### AC-SUP-03 — Unknown Job safety

```gherkin
Given a Job provider outcome is unknown
When Support investigates or the user retries
Then the Case invokes owner reconciliation/query
And no new Provider attempt is created until the original outcome is resolved or safely voided
```

### AC-SUP-04 — Redemption replacement

```gherkin
Given a verified wrong-binding Redemption
When an approved remedy executes
Then the original source is reversed under its own lineage
And a replacement is issued through secure single-use delivery
And no other Payment/Redemption/Admin Grant is changed
```

### AC-SUP-05 — Case closure

```gherkin
Given a high-risk Case has an approved domain action
When the action completes
Then the Case stores the authoritative receipt and public Resolution
And the user is notified and can confirm or appeal
And the Case cannot close while receipt or mandatory notification state is missing
```

### AC-SUP-06 — Break-glass

```gherkin
Given an incident requires exceptional cross-scope access
When a BreakGlassGrant is issued
Then it is action/resource/TTL bound, paged and fully audited
And expiry immediately denies further access
And a post-incident review is required before closure
```

### AC-SUP-07 — Action-bound verification

```gherkin
Given a requester completed low-assurance verification for a status query
When an operator reuses it for owner transfer, Grant, export or another parameter digest
Then the domain owner rejects the command without mutation
And only a current single-use VerificationGrant with sufficient assurance and exact action digest can proceed
```

### AC-SUP-08 — Redeem-only payment boundary

```gherkin
Given a Site is redeem_only and has never produced a Payment Fact
When a user or operator creates payment_refund_dispute
Then the Case kind is rejected as unavailable
And no Order, Payment, Invoice or Refund fact is created
When a Site has a historical Payment Fact
Then only that original Payment and ProviderAccount workflow remains available while new Checkout stays disabled
```

### AC-SUP-09 — Case ownership isolation

```gherkin
Given a requester loses Workspace membership or Workspace ownership transfers
When another member or the new owner opens the requester's personal security Case
Then access is denied unless an explicit CaseParticipantGrant exists
And the Case is not deleted by Project deletion
```

### AC-SUP-10 — Appeal preserves history

```gherkin
Given an appealable moderation, risk or reversal Decision exists
When a valid Appeal is filed
Then a new Appeal and later Decision are created by an independent reviewer
And the original Decision, Evidence, maker and timestamp remain immutable
```

### AC-SUP-11 — Checker independence and parameter integrity

```gherkin
Given a maker requests a high-risk correction, Grant, reversal or replacement
When the same operator, an expired checker session, or approval for a different parameter digest attempts execution
Then approval is rejected and no domain command is emitted
And a different currently authorized checker must approve the exact immutable request
```

### AC-SUP-12 — Domain command timeout is idempotent

```gherkin
Given a compensation, reversal or replacement command times out after submission
When Support retries the workflow
Then it queries the same idempotency identity and request digest
And no second Grant, reversal, replacement Code, Payment or Provider effect is created
```

### AC-SUP-13 — Evidence chain of custody

```gherkin
Given uploaded evidence contains a possible Code, payment identifier or sensitive prompt
When intake completes
Then the original is quarantined and hashed, a provenance-linked sanitized derivative is created
And ordinary operators can read only the allowed derivative through an audited short-lived ContentAccessGrant
```

### AC-SUP-14 — Notification failure and closure

```gherkin
Given an authoritative Resolution and NotificationRequest receipt exist but external email delivery remains unknown
When the confirmation window expires
Then the Resolution stays visible in Support Center and closure follows the frozen fallback policy
And delivery remains unknown rather than being rewritten as delivered
```

### AC-SUP-15 — External card seller refund remains external

```gherkin
Given a user obtained a Code from an external seller and no Platform Payment Fact exists
When wrong-binding remedy or seller refund is recorded
Then Platform appends only Redemption reversal/replacement and an external refund reference
And it does not create a Platform Order, Payment, Invoice or Refund
```

## 13. Analytics、Risks and Milestones

Metrics：Case creation/contact rate per 1k Journey、first response/resolution、waiting user/internal aging、SLA breach、
reopen/escalation、CSAT、self-serve recovery、compensation count/error、notification failure、break-glass、PII access。
按 Site/Profile/Case kind/severity 切分，不把 message 内容作 metric label。
每个指标引用 `ProductMetricRevision`，冻结 numerator、denominator、exclusions、window、dimensions、event source、
owner、target/guardrail、alert threshold 和 mandatory action。

| Risk | Mitigation |
|---|---|
| Support 变成万能业务层 | Case 只拥有协作状态；命令回领域 owner，receipt 收口 |
| 为效率扩大 PII/impersonation | safe projections、ContentAccessGrant、只读 SupportView、审计/通知 |
| 补偿重复或串 source | domain idempotency/source lineage/maker-checker/receipt query |
| SLA 只写文档不执行 | durable timers、queue owner、alert/escalation、用户可见 due time |
| Case 与 Data Rights/LegalHold 冲突 | participant classification、deidentify、mandatory fact intake |

Wave 1 冻结 Case/Notification/identity verification 最小 contract；2A/3/4 等领域同波注册 Case kind 和 recovery
commands；Wave 7 交付完整 User Support Center/Operator Console/SLA；Wave 9 真实 redeem/run/data-rights Case UAT。

本文不授权实现，也不修改 GA runtime。
