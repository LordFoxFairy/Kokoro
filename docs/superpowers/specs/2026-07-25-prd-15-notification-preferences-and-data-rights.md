---
artifact: product-requirements-document
prdId: PRD-15
version: "1.0"
created: 2026-07-25
status: internal-review-active
scope: notification-delivery-preferences-consent-export-deletion-retention-legal-hold
accountableProductRole: Privacy & Notification Product Lead
mandatoryCosigners: [Privacy, Legal, Security, Identity, Commerce, Support, Data Governance, QA]
engineeringOwner: team:notification-data-governance-engineering
qaOwner: team:privacy-notification-quality
supportOperationsOwner: team:data-rights-operations
namedOwnerAssignmentStatus: assigned-team-responsibility-ids
implementationAuthorized: false
---

# PRD-15：Notification、Preferences 与 Data Rights

## 1. Overview

### Problem

Identity、Redeem、Payment、Run/Job、Support、Trust 与删除都会产生必须通知用户的异步事实。若各模块直接发邮件，
将出现重复、错误 Site 品牌、无法重试、用户偏好绕过和“邮件已接受=用户已收到”的假状态。数据导出与删除若
只是 Admin 脚本，则会漏掉 Session、Artifact、账务、Support、LegalHold 与对象存储，也无法证明完成或解释
依法保留内容。

### Solution

Notification 模块独占 canonical request、模板、偏好、fanout、delivery attempt 和 receipt；领域事务只在自身
存储中原子写入版本化 `SourceNotificationIntent` 与本地 outbox，Notification 以 at-least-once consumer 幂等物化
唯一 `NotificationRequest`，不要求跨库事务。Data Governance 模块独占 Data Rights、Product Closure、Retention 与
LegalHold workflow，领域 owner 以 participant plan/receipt 响应，不允许 coordinator 直接删业务表。所有 Notification
对象携带 immutable `siteId`；相同邮箱跨 Site 的身份与偏好独立，transport safety suppression 另按 Provider/Sender/
legal entity policy 管理且不得泄漏跨 Site 账户存在性。

### Users and stories

| ID | User story | Priority |
|---|---|---|
| NOT-US-01 | 用户能收到安全、兑换、运行、Case 和数据权利的准确 Site 通知并回到正确状态 | P0 |
| NOT-US-02 | 用户能管理可选通知，但不能误关安全、财务和法定义务通知 | P0 |
| DR-US-01 | 用户能导出本站账户与内容，看到范围、进度、失败和安全下载 | P0 |
| DR-US-02 | 用户能请求删除、重新认证、在窗口内取消并看到依法保留项 | P0 |
| DR-US-03 | Support/Data operator 能恢复卡住 workflow，但不能直接查密钥或删表 | P0 |

## 2. Goals、Metrics and Non-Goals

### Goals

1. 领域事实与消息投递分离，所有 mandatory request 可追踪、可恢复、不可被偏好关闭。
2. 用户只收到当前 Site/locale/brand/legal revision 的通知，deep link 不串站。
3. Export/Delete 覆盖所有 enabled/历史 participant、Blob 和法定保留事实，有完整 receipt。
4. 删除不抹除 Payment/Dispute/Audit/Usage 等 mandatory facts，也不让 deleted subject 重新复活。

### Success Metrics

| Metric | Target |
|---|---:|
| domain fact + SourceNotificationIntent 原子入本域 outbox 覆盖 | 100% |
| 跨 Site recipient/brand/deep-link 泄漏 | 0 |
| Notification Center 同一 logical request/channel 重复行 | 0 |
| provider accepted 被误报 delivered | 0 |
| Export manifest/part 缺失或 hash 不一致 | 0 |
| Delete 完成但缺 participant/GC/retention receipt | 0 |
| LegalHold 数据被删除 | 0 |
| 用户偏好关闭 mandatory event | 0 |

指标引用 ProductMetricRevision，并按 Site/Profile/event kind/channel/provider/workflow revision 切分。

### Non-Goals

- Notification 不拥有 Identity、Payment、Redemption、Run、Job、Case 或 Delete 的业务状态。
- 不保证外部 email/push provider 能证明人类阅读；只报告可证实 receipt。
- 不把删除解释为抹除所有法律、财务、安全与审计事实。
- 不跨 Site 合并邮箱偏好、退订、导出或删除请求。
- V1 Core 只要求 in-app + email；SMS/push/webhook 是 if-enabled channel。

## 3. Product Objects and Ownership

```text
SourceNotificationIntent
  siteId / sourceDomain / sourceAggregateRef+version / eventKind
  recipientSubjectGeneration / mandatoryClass / sourceOutboxRef

NotificationRequest
  siteId / requestId / sourceDomain / sourceAggregateRef+version / eventKind
  recipientRef / recipientAddressSnapshotRef / locale/template/brand/legal revisions
  deepLinkIntentRef / priority / mandatoryClass / materializationIdentity

NotificationFanout
  siteId / requestId / channel / preferenceDecisionRef / deliveryPolicyRevision

DeliveryAttempt
  siteId / providerTenant/account/revision / ordinal / requestDigest / state / providerFactRefs

DeliveryReceipt
  siteId / queued | provider_accepted | delivered | bounced | complained | failed | unknown | suppressed

NotificationPreference
  siteId / subjectGeneration / category / channel / state / policyRevision
ConsentPreferenceEvidence
  siteId / controller/legalEntity / subjectGeneration / purpose/legalBasis/policyRevision
  affirmativeAction / noticeDigest+locale / ageOrGuardianEvidence / collectionRegion
  processingRecipients / capturedAt/source / expiresAt / withdrawnAt
RecipientAddressSnapshot
  siteId / encrypted address ref / address generation / verifiedAt / audit classification

SiteChannelHealth / ProviderSuppressionFact
  siteId+subjectGeneration+channel / pseudonymousAddressKey+providerOrSenderScope

DataRightsRequest
  kind=access|portability|erasure|restriction|objection
  siteId / requesterSubjectGeneration / dataSubjectRef / controllerDecisionRef
  status / jurisdictionPolicy / verificationGrantRef / scopeSnapshot / dueAt

ProductClosureRequest
  kind=account_closure|project_deletion / siteId / requesterSubjectGeneration
  targetResourceRef / requesterAuthoritySnapshot / ownershipRevision / cancelUntil

DataRightsJurisdictionDecision
  legalEntity / requester location evidence / law/policy revisions
  requestReceivedAt / statutory clock / decision rationale

ParticipantPlan / ParticipantReceipt / ObjectGcReceipt
DataSubjectDisclosureDecision / ExportManifest / ExportPart / SecureDeliveryArtifact
RetentionPolicyRevision / LegalHold / DeletionTombstone
```

- Source domain owns event truth and transaction-local intent/outbox；Notification owns canonical request、rendering、fanout
  与 delivery facts。稳定物化 identity 为 `(siteId, sourceDomain, sourceAggregateRef, sourceVersion, eventKind,
  recipientSubjectGeneration, mandatoryClass)`；重复消费只能得到同一 request。
- 所有 Notification request/fanout/attempt/receipt/preference/consent/address 对象都携带 immutable `siteId`；fanout
  唯一键是 `(siteId, requestId, channel)`。
- Data Governance owns workflow only；Identity/Workspace/Commerce/Session/Job/Artifact/Support 等各自拥有 participant
  decision 与 mutation receipt。
- analytics/open tracking 不是 Delivery authority；敏感/mandatory email 默认不使用隐形 tracking pixel。
- Notification 是 at-least-once processing，不承诺外部 Provider/邮箱世界 exactly-once；Kokoro 通过稳定
  request/channel identity、provider idempotency 与用户 Center dedupe 使重复可控。任何 duplicate 仍保留事实并
  进入质量指标，不能通过覆盖 DeliveryAttempt 隐藏。

## 4. Notification Requirements

### 4.1 Mandatory and optional classes

Mandatory event、不允许用户阻止其生成和 durable in-app availability：email verification、password/MFA/recovery/security/session events、acquisition/
Redemption/Payment/Refund/Dispute receipts、Subscription material changes、Credit reversal/correction、Run/Job unknown
达到用户行动阈值、Case reply/escalation/resolution、moderation/appeal、export/delete/retention、Site closure。
是否必须使用 email 等外部 channel，由 event risk、legal basis、urgency、channel health 与版本化 DeliveryPolicy
分别决定；mandatory event 不等于每个外部 channel 都 mandatory。

Optional：product tips、completion summaries（若不承担唯一结果）、marketing、growth experiment。Marketing consent
独立、默认关闭、撤回立即影响未来 fanout；不能以关闭 marketing 抑制 transaction/security message。

### 4.2 Request、render and fanout

- source transaction 原子写 `SourceNotificationIntent` + 本域 outbox；delivery failure 不回滚业务事实，source
  transaction 不写 Notification-owned storage。Notification 重复或中断消费时按稳定 materialization identity 恢复
  同一 canonical request。
- request 冻结 source version、审计用 recipient address snapshot、Site/locale/template/brand/legal revision 与
  deep-link intent；文案 retry 使用原 revision，但 address snapshot 本身不是持续发送授权。
- optional/consent fanout 在创建和 provider submit 前都重新验证 consent；withdrawal 抑制尚未 provider-accepted 的
  queued/retry/digest。Transactional notification 默认解析 current verified address；仅版本化
  `SecurityDeliveryPolicy` 可明确要求 pre-event/old address。
- recovery start/failure/completion 只向 pre-recovery trusted snapshot 发安全提醒；恢复期间新增 channel 在 challenge
  与 cooldown 满足前不得收到 token、recovery link 或 sensitive evidence。
- address snapshot 加密、generation-bound、最小 retention；普通营销/产品通知不得借历史 snapshot 发送到已撤回/
  失效地址。
- template 只接受 typed variables/formatter；禁止 arbitrary HTML/URL。security token 使用单独 purpose-bound secret，
  不写入 request、日志或 analytics。
- 一个 request/channel 只有一个 active fanout identity；provider retry 使用同 request digest，切 provider 也保留 lineage。
- provider submit 时原子保存 immutable callback mapping：`(providerTenantRef, providerAccountRevision,
  providerMessageId) -> (siteId, fanoutId, attemptId)`。callback payload 不得提供或扩大 Site scope；unresolved/mismatch
  callback 隔离并报警。

### 4.3 Delivery states and recovery

- `queued`、`provider_accepted`、`delivered`、`bounced`、`complained`、`failed`、`unknown`、`suppressed` 分开；只有
  provider 明确证据才能标 delivered，accepted/timeout 不能猜测。
- receipt reducer 按 provider/account/message identity、occurred/received time 与状态 precedence 追加事实；late/
  duplicate callback 不覆盖历史或把 bounced/complained 回退为 delivered。
- unknown 查询 provider 或等待 callback，不盲发第二封高风险 secret；可安全重复内容由 DeliveryPolicy 定义。
- hard bounce/complaint 更新 `SiteChannelHealth`。独立的 `ProviderSuppressionFact` 可按已发布 policy 在 provider
  account、sender domain 或 legal entity scope 使用 pseudonymous address key 生效；它不得合并 Site identity/
  preference 或泄漏另一个 Site 的账户存在。optional send 被抑制，mandatory event 使用 in-app 或 policy 允许的安全替代。
- mandatory delivery 超 SLA page owner，并在 in-app center 保持可见；可选通知遵守 frequency cap/digest。

### 4.4 Deep link and Notification Center

- deepLinkIntent 由 Web BFF 按当前 Site/AuthSession 解析成 allowlisted path；邮件不携任意 return URL。
- 未登录时先 re-auth，再回到签名 intent；Site/subject/resource mismatch 返回安全首页/Support，不泄漏对象。
- Center 显示 source status、freshness 和 CTA，不把 Notification receipt 冒充 domain terminal。

## 5. Data Export

- 创建 request 要 current Site AuthSession + action-bound VerificationGrant；高风险恢复 cooldown 内默认禁止导出。
- 丢失账户访问时提供 PRD-01/11 的高保证 recovery/Support path；不能为了核验收集超出请求所需的 KBA、交易
  secrets 或第三方数据，也不能让核验失败重置法定接收时间。
- scope snapshot 列出 Identity、Workspace/Project、Session/Message、Asset/Artifact、Acquisition/Subscription/Credit/
  Usage、Support、Consent/Preference 与适用 operator/security data categories。
- 每个 participant 返回 `included/omitted/retained/not_applicable/failed` 和 part digest；coordinator 不直查数据库。
- shared Workspace/Project、多人 Session/Message、SupportCase 和 collaboration Evidence 由版本化
  `DataSubjectDisclosureDecision` 决定，不以 product ownership 或 current ACL 直接决定。每个 field/part 记录
  requester nexus、data-subject category、third-party interests、confidentiality/security restriction、redaction
  transform 与 decision basis。current read access 不自动授予第三方内容；membership 结束也不自动剥夺 requester-
  authored/requester-related data rights。Manifest 必须解释 omitted/redacted category。
- ExportManifest 列出 schema version、part、size/hash、time range、omission/retention reason 和 source owner；完成前
  校验所有 mandatory participant 与 object receipt。
- archive 加密、短时、single-use/limited-download、Site/subject/audience bound，不作为 email attachment 或 bearer URL。
  每次下载重新验证 Site、subject generation、AuthSession、action-bound VerificationGrant、security/deletion epoch、
  TTL 与 download budget；account recovery/suspend/deletion epoch 变化立即撤销 artifact。secret、password verifier、
  token、provider credential、内部安全检测规则不导出。
- 下载过期不重跑 export；用户可请求新 workflow。响应丢失查询同 request receipt。

## 6. Data Rights Erasure and Product Closure

法定 `DataRightsRequest(kind=erasure)` 与产品 `ProductClosureRequest(kind=account_closure|project_deletion)` 是不同
authority、target、clock、decision 和 receipt。一个 workflow 可显式关联两者并复用 participant，但 Project owner
发起产品删除不自动成为法定 erasure request，成员的 account closure 也不得被解释成 shared Project 级联删除。

### 6.1 Request and cooling window

- 重新认证并展示影响：登录、Workspace/Project、active Run/Job、Subscription renewal、Credit、Artifact/Share、
  Support、external Payment/Dispute、export、Retention/LegalHold。
- 删除个人账户不等于删除 Workspace-owned/shared content。participant 依据 owner、membership、共同作者、合同和
  LegalHold 决定 delete/deidentify/unlink/retain；历史 actor 可替换为 non-identifying surrogate，不能把其他成员的
  Artifact/Session/Case 一并删除，也不能让新 Workspace owner读取原用户私人 Case。
- Request commit 在 cooling window 只把 subject generation 标为 `deletion_pending`，停止新 acquisition/admission/
  execution/share 和敏感变更；不关闭 credential/generation，不执行 irreversible participant mutation。受限 session
  或 action-bound grant 仅允许 status、export、cancel 与 Support；active effect 只允许 finalization/reconcile，不伪造
  terminal 或丢 Usage。
- 可取消窗口、不可逆点与 dueAt 由 jurisdiction/Site policy revision 冻结；取消也需 re-auth，并在不可逆点后拒绝。
- destructive phase 只能在 `cancelUntil` 后、重新检查 current participant/hold/policy plan version 后开始；Identity 在
  进入不可逆 phase 时才关闭 generation 并撤销剩余 credentials。

### 6.2 Participant workflow

- Identity 在 cooling window 仅标记 deletion_pending 并提供受限授权；不可逆 phase 才 revoke remaining sessions/
  credentials 并关闭 subject generation。
- Workspace/Project freeze new writes，detach/deidentify/retain resources per ownership/LegalHold。
- Commerce stops renewal/new acquisition，但继续接收并处理 Refund/Dispute/chargeback/financial retention facts。
- Session/GA/Job 不接受新 execution；已提交 effect 只 finalization/reconcile。GA 不接收 deletion 业务身份。
- Artifact/Object Storage execute retain/deidentify/delete/GC with checksum receipts；DB completion 不代替 Blob GC。
- Support 保留 Case/Audit 最小事实，移除非必要 PII；Notification 保留 request/receipt 必要证明。
- 新 LegalHold/restriction/Payment dispute/participant revision 使 plan 失效并重编译，不执行 stale destructive plan。

### 6.3 Completion and future registration

- 只有所有 mandatory participant、object GC、retention classification、durable NotificationRequest materialization
  receipt 与仍可访问主体的 in-app availability 齐全才 completed。external delivery 的 unknown/failed 不阻塞删除完成，
  继续按独立 Delivery SLA/fallback 处理。
- 保留 `DeletionTombstone(siteId, oldSubjectGeneration, completion, retainedClassRefs, securityEpoch)`；旧 token、link、
  invitation 和 grant 永久不能复活该 generation。
- 相同 email 未来注册创建新 subject generation，不自动关联旧 Workspace、Credit、history、Case 或 entitlement。

## 7. Preferences、Consent and Admin

- preference category/channel matrix 由 policy revision 发布；用户修改保存 receipt 并立即作用于未来 fanout。
- preference/consent 分开：preference 表达用户体验选择，ConsentPreferenceEvidence 记录适用 purpose/legal basis/
  notice revision；consent 还必须固定 Site/controller/legal entity、subject generation、purpose、affirmative action、
  notice digest/locale、适用的 age/guardian evidence、collection region、expiry 与 processing recipient。拒绝、撤回和
  重新同意均 append-only；不得从 silence、bundled terms 或普通 preference toggle 推导 consent。撤回 consent 不改写
  历史 evidence，立即阻止未来依赖该 consent 的 processing。contract/legal
  obligation/legitimate-interest 等非 consent basis 必须在 policy 中单独说明，不能伪装成“用户无法关闭的偏好”。
- mandatory/optional 标识、为什么不能关闭、当前 channel health 和最近变更对用户可见。
- Admin 使用 typed command 管理模板、provider、retry、LegalHold、workflow recovery；每个命令登记 role、Site/resource
  scope、risk level、reason、expectedVersion、idempotency key、PII masking、queue/SLA、audit、user notification 与
  recovery。高风险命令执行 step-up/maker-checker；禁止同一 operator request+approve+execute，禁止改 delivery/domain
  terminal、伪造 consent、直接删表/Blob、查看 secret、下载用户 export 或 impersonate。
- LegalHold 创建/释放需 reason、scope、authority、effective interval、step-up、maker-checker 与通知政策；release 不
  自动删除，需重新编译 deletion plan。
- LegalHold 必须 resource/data-class 精确、必要最小、定期 review、owner、expiry/reviewDueAt 和 legal authority
  evidence；禁止 `all data forever` 默认范围。到期/authority撤销进入 checker review，不能无审计自动续期。
- Support 只能查看安全投影、delivery state、participant aging 和 receipt，不能下载 export archive 或 impersonate。
- DataRightsJurisdictionDecision 在 request received 时冻结法律实体、适用 policy、statutory clock 和 owner；身份
  核验、澄清、复杂延期、第三方 redaction 和 rejection 的 pause/extension/notice 规则由 revision 明确。每个 request
  显示 dueAt；内部 queue、participant failure 或 Support 转派不能无声重置时钟。
- 任一目标 legal entity/jurisdiction 没有 Legal 发布的 launch matrix（覆盖 request kind、clock start、verification
  effect、允许的 pause/extension、notice deadline、rejection/appeal、deletion timing 与 retention basis）时，
  `SiteRelease` fail closed；Site policy 只能缩短期限或增加权利，不能弱化适用 baseline。
- LegalHold 可使 participant disposition 变为 retain/restrict，但不能静默暂停 data-rights response clock；request 必须
  按时形成 partial/denied/completed disposition。用户可见 retained class/reason 经 disclosure filter；法律禁止披露
  hold existence、authority 或 investigation scope 时，只显示批准的通用理由。

## 8. User-visible States and Recovery

| Surface | States | Recovery |
|---|---|---|
| Notification | queued、provider_accepted、delivered、bounced、complained、failed、unknown、suppressed | wait/query、repair channel、view in-app；不盲 resend secret |
| Export | verification_required、preparing、ready、ready_with_omissions、ready_with_redactions、failed_recovering、expired | verify、wait、download、new request、Support |
| Deletion | verification_required、cooling_off、in_progress、blocked_retention、blocked_external_fact、completed、canceled | verify、cancel before point、wait、view retained classes、Support |

## 9. Edge Cases

| Scenario | Expected behavior |
|---|---|
| Site A hard bounce，同邮箱 Site B 正常 | Site identity/preference 仍隔离；仅已发布 provider/sender/legal-entity suppression 可用 pseudonymous key 抑制 transport，不泄漏 Site B 账户存在 |
| provider accepted 后 callback 丢失 | 保持 accepted/unknown，按 policy query；不写 delivered |
| recovery 中新增攻击者邮箱 | security notification 仍发恢复开始前 address snapshot |
| 删除中收到 Payment dispute | 接收 mandatory fact，重编译/保留 Commerce participant |
| Project 删除试图删除 SupportCase/Journal | participant retain/deidentify/unlink；拒绝 direct cascade |
| export part 成功、manifest 写失败 | query existing parts/hash，恢复同 workflow，不重复泄漏 archive |
| LegalHold 在 GC 前创建 | 删除暂停，旧 plan invalidated |
| deleted email 再注册 | new subject generation，无旧数据/权益链接 |
| requester 导出 shared Workspace | DisclosureDecision 逐 field/part 判断 requester nexus；当前 ACL 不导出无关第三方内容，离职不自动排除本人相关数据 |
| account deletion owns shared Artifact | unlink/deidentify requester；保留其他 owner/member rights，不级联删除 |
| LegalHold 无 owner/expiry/review | create/renew/compile 拒绝；有效 hold 也不暂停 response clock，用户解释经 disclosure filter |
| provider late delivered after bounce/complaint | append fact, no harmful state regression; channel policy remains protected |

## 10. Acceptance Criteria

### AC-NOT-01 — Atomic source intent, idempotent materialization

```gherkin
Given a password reset or Redemption commits
When the mail provider is unavailable
Then the domain fact and one SourceNotificationIntent commit atomically in the source store
And duplicate or interrupted outbox delivery materializes exactly one canonical NotificationRequest
And no cross-store transaction or source-owned NotificationRequest is required
```

### AC-NOT-02 — Mandatory preference boundary

```gherkin
Given a user disables every optional channel/category
When a security, financial, Support or data-rights event occurs
Then its mandatory NotificationRequest is still created under policy
And it remains durably available in-app
And external mandatory channels are selected separately by DeliveryPolicy
And no marketing notification is submitted without current consent revalidation
```

### AC-NOT-03 — Site-bound deep link

```gherkin
Given a Site A notification intent is opened with a Site B session or domain
When BFF resolves the link
Then it rejects the resource intent without revealing existence
And it never redirects to an arbitrary URL or Site B resource
```

### AC-DR-01 — Complete export manifest

```gherkin
Given an export includes every applicable enabled and historical participant
When any required part/hash/retention decision is missing
Then the workflow cannot become ready
When all receipts exist
Then a short-lived encrypted archive and manifest are delivered to the verified Site-local subject
```

### AC-DR-02 — Deletion freezes new work and preserves mandatory facts

```gherkin
Given deletion epoch committed for a subject
When a stale client starts acquisition, Session, Run, Operation or Share and a signed dispute webhook arrives
Then every new user effect is denied
And the external financial fact is accepted, retained and reconciled
```

### AC-DR-03 — LegalHold invalidates stale plan

```gherkin
Given a deletion plan is ready but object GC has not crossed its irreversible point
When a LegalHold or participant epoch changes
Then the plan pauses and recompiles
And no protected object or fact is deleted under the stale plan
```

### AC-DR-04 — Deleted generation cannot revive

```gherkin
Given subject generation one completed deletion
When an old token, invitation, recovery link or runtime grant is replayed
Then it is rejected permanently
When the same email registers again
Then generation two has no implicit link to generation one's Workspace, Credit, Case or history
```

### AC-NOT-04 — At-least-once receipt reduction

```gherkin
Given duplicate and out-of-order accepted, delivered, bounced and complained callbacks arrive
When Notification reduces provider facts
Then every unique fact remains auditable and user Center shows one coherent notification
And late callbacks cannot erase bounce/complaint or fabricate exactly-once delivery
```

### AC-NOT-06 — Provider callback Site isolation

```gherkin
Given Site A and Site B have colliding provider message identifiers
When a callback arrives through Site A's immutable provider-account mapping
Then only Site A's attempt and channel health may change
And unresolved or mismatched callbacks are quarantined without revealing or mutating Site B
```

### AC-NOT-07 — Consent withdrawal and recovery-safe recipient

```gherkin
Given optional consent is withdrawn after fanout is queued but before provider acceptance
When the worker attempts submission or retry
Then the fanout becomes suppressed with withdrawal evidence
And no provider request is made

Given recovery adds a new verified channel during cooldown
When recovery security events are delivered
Then pre-recovery trusted channels receive the alert
And the new channel receives no actionable secret or prohibited evidence
```

### AC-NOT-05 — Consent and preference separation

```gherkin
Given a user withdraws marketing consent while mandatory transaction notices remain legally required
When future events fan out
Then no processing relying on withdrawn consent sends
And mandatory notices use their explicit non-marketing policy basis without changing historical consent evidence
```

### AC-DR-05 — Shared-data export privacy

```gherkin
Given a requester participated in a shared Workspace, conversation and SupportCase
When personal export is compiled
Then DataSubjectDisclosureDecision evaluates every field/part independently of current product ACL
And requester-authored or requester-related data remains eligible after membership ends
And unrelated third-party PII, private Case ownership, operator notes, reporter identity and security detections are redacted or omitted with reasons
```

### AC-DR-06 — Personal deletion preserves other owners

```gherkin
Given a departing user contributed to Workspace-owned Artifacts and shared Sessions
When account deletion completes
Then requester identity is deleted, deidentified or unlinked according to policy
And other owners' content and access remain intact without exposing the requester's private Cases
```

### AC-DR-07 — LegalHold is bounded

```gherkin
Given a LegalHold lacks exact resources/data classes, authority evidence, owner, expiry or reviewDueAt
When creation, renewal or deletion-plan compilation occurs
Then the hold is rejected as invalid
And no broad indefinite hold can silently stop the data-rights clock
When a valid hold prevents erasure
Then the request still reaches a timely disclosure-filtered partial, denied or completed disposition
```

### AC-DR-08 — Statutory clock continuity

```gherkin
Given a data-rights request was received and later needs verification, clarification or participant recovery
When workflow ownership changes or a participant fails
Then original receivedAt and the policy-defined statutory clock remain auditable
And any permitted pause/extension produces timely user notice rather than silently resetting dueAt
```

### AC-DR-09 — Cooling-off remains cancelable

```gherkin
Given a verified account-closure or erasure request is inside its cooling window
When the subject re-authenticates and cancels through the restricted session
Then no irreversible participant or Blob mutation has occurred
And the generation returns to its prior lifecycle with a durable cancellation receipt
```

### AC-DR-10 — Secure export authorization is revalidated

```gherkin
Given an encrypted export artifact is ready
When download is requested after recovery, suspension, deletion-epoch change, TTL expiry or download-budget exhaustion
Then Site, subject generation, AuthSession, VerificationGrant and every epoch/budget are revalidated
And the archive is denied without exposing a bearer URL or email attachment
```

### AC-DR-11 — Data right and product closure remain distinct

```gherkin
Given a member requests account closure and a Project owner requests Project deletion
When workflows compile participants
Then each request preserves its own target, authority, clock, decision and receipts
And neither request cascades into the other's legal or shared-resource scope without an explicit linked request
```

### AC-DR-12 — Jurisdiction launch gate

```gherkin
Given a SiteRelease targets a legal entity or jurisdiction
When Legal has not published every required request-kind, clock, notice, appeal, deletion and retention policy revision
Then the data-rights Surface and dependent SiteRelease fail closed
And no generic Site default may weaken or invent the missing legal baseline
```

## 11. Dependencies、Risks and Milestones

| Risk/Dependency | Mitigation |
|---|---|
| 各模块自行发通知 | architecture dependency gate + outbox contract + direct-provider import ban |
| accepted 被误当 delivered | explicit receipt state machine、provider reducer、unknown reconciliation |
| 删除 coordinator 成为万能数据层 | participant owner APIs、receipts、no direct DB/Blob access |
| 历史未启用模块被漏掉 | scope snapshot includes enabled + historical fact inventory |
| 法律保留与用户承诺冲突 | jurisdiction policy、category explanation、deidentify/minimize、Legal review |
| export archive 泄漏 | action-bound verification、encryption、short TTL、limited download、audit |
| 未发布法域政策却开放数据权利 | SiteRelease jurisdiction matrix fail-closed + Legal cosign |

Wave 1 冻结 SourceNotificationIntent/NotificationRequest、preference/consent、DataRightsRequest、
ProductClosureRequest、DisclosureDecision、participant 和 tombstone contract；各领域在自身
Wave 注册 event/participant；Wave 7 完成用户/Admin 面；Wave 9 演练 provider outage、partial export、LegalHold、
dispute-during-deletion 和 Blob GC。具体法定期限由目标 Site/地区法律评审发布，不在本文臆定。

本文批准不授权实现，也不修改 GA runtime。
