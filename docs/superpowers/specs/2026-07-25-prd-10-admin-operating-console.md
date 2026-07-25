---
artifact: product-requirements-document
prdId: PRD-10
version: "1.0"
created: 2026-07-25
status: internal-review-active
scope: admin-operating-console-operator-identity-scope-command-approval-queues-audit-reconciliation
accountableProductRole: Operations & Support PM
mandatoryCosigners: [Security, Finance, Risk, Data Governance, Site Fleet, SRE, Support, QA]
engineeringOwner: team:admin-platform-engineering
qaOwner: team:admin-quality
supportOperationsOwner: team:core-operations
namedOwnerAssignmentStatus: assigned-team-responsibility-ids
implementationAuthorized: false
gaRuntimeSemanticChangeAuthorized: false
---

# PRD-10：Admin Operating Console

## 1. Overview

### Problem

生产运营不能依赖通用数据表、数据库脚本、共享管理员账号或散落在各服务的隐藏入口。Site Fleet、身份安全、
Commerce、Credit、Redeem、Model、Session、Job、Artifact、Trust、Notification 与 Data Rights 都有不同的真源、
风险、幂等、审批、恢复和通知语义。若 Admin 直接读取或修改业务表，运营者会绕过领域不变量，超时后可能重复
退款、赠送或 Provider effect，跨 Site 查询会泄漏身份存在性，审计也无法证明“谁以什么权限批准了哪组参数”。

同时，领域能力不能等到 Wave 7 才获得运营入口。没有随领域 Wave 一起交付的安全投影、typed command、队列、
SLA、审计事件、receipt 与 runbook，该领域就不具备生产可运营性。

### Solution

建立面向生产运营的标准 Admin Operating Console：以独立 `OperatorPrincipal`、抗钓鱼认证、显式
`SiteScope | GlobalScope | BreakGlassScope` 为信任入口；以统一壳承载导航、scope bar、搜索、队列、审批、审计、
reconciliation 与 Support handoff；以每个领域拥有的 annex 提供 safe projection 和 typed command。

Admin 是 application façade：只组合授权后的 read model，并把 mutation 路由给领域 owner。每条命令由
`OperatorCommandRegistry` 冻结角色、scope、风险、理由、step-up、maker-checker、版本、幂等、PII masking、
队列、SLA、审计、用户通知、receipt 和恢复 runbook。任何操作都不得由浏览器或 Admin BFF 直接 mutation
业务数据库。

Wave 7 只交付和聚合统一壳、跨领域导航/搜索、队列与审批工作台、审计体验、Support handoff 和领域 annex
装配；各领域必须在自身 Wave 交付并认证 annex contract、projection、command、effect-point authorization、
reconciliation 和 runbook。Wave 7 不得成为补做领域安全控制或直接数据库 mutation 的理由。

### Target users and stories

| ID | User story | Priority |
|---|---|---|
| ADM-US-01 | Site 运营者能在明确 Site scope 内定位问题，不泄漏其他 Site 的存在性 | P0 |
| ADM-US-02 | 专业运营者能执行其角色允许的 typed command，并在提交前理解影响与恢复路径 | P0 |
| ADM-US-03 | maker 与独立 checker 能审阅完全相同的不可变参数、证据和风险摘要 | P0 |
| ADM-US-04 | on-call 能从告警进入 reconciliation 队列，恢复 unknown/partial，而不盲目重放副作用 | P0 |
| ADM-US-05 | Support 能把 Case 安全交给领域队列并接收 authoritative receipt，不复制业务真源 | P0 |
| ADM-US-06 | Auditor 能重建一次读取、审批、执行、通知和恢复的完整因果链 | P0 |
| ADM-US-07 | Global/Security operator 能处理明确列举的跨 Site incident，而不获得任意全局浏览权 | P0 |
| ADM-US-08 | 移动端值班人员能安全完成 acknowledgement、只读诊断和受限审批 | P1 |

## 2. Goals、Metrics and Non-Goals

### Goals

1. 为所有生产 operator 建立独立、可撤销、抗钓鱼的身份与设备信任链。
2. 让 scope、role、step-up、approval 与 restriction epoch 在每个读取、命令提交和最终 effect point 重验。
3. 以 safe projection 和 typed command 替代直接表访问、任意字段编辑与脚本式补偿。
4. 让 queue、SLA、reconciliation、Support handoff、notification、audit 和 runbook 形成可恢复运营闭环。
5. 用统一壳降低跨领域认知成本，同时保留领域 owner 对状态、命令与不变量的唯一 authority。
6. 让每个领域在自身 Wave 达到“可运营”，Wave 7 仅负责聚合，不延迟安全与恢复能力。

### Success metrics

| Metric | Baseline | Target / guardrail | Window and action |
|---|---:|---:|---|
| Admin 直接业务 DB mutation | 当前遗留能力待盘点 | 0 | 每次 build/release；发现即阻断并触发 Security review |
| 未登记 Admin command | 当前未统一 | 0 | 每个 release inventory；缺 registry ref 阻断 |
| 高风险命令缺有效 step-up/maker-checker | 当前覆盖不一致 | 0 | 持续；任一事件 page Security |
| 跨 Site 非授权读取或存在性泄漏 | 未统一量化 | 0 | 持续；任一事件按 P0 incident |
| 命令 receipt 与审计闭环覆盖率 | 当前未统一 | 100% | 每个 release；缺 receipt 不得显示 succeeded |
| 超时重试导致重复领域/Provider effect | 当前未统一 | 0 | 持续；触发 reconcile 与 release freeze |
| P0 queue acknowledgement | 按领域分散 | p90 ≤ 15m，24×7 | 超时 page queue owner 与 incident commander |
| 普通 core-standard queue 首次处理 | 按领域分散 | p90 ≤ 4 support hours | 超阈值自动 escalation |
| stale/unknown projection 有明确 freshness 与 recovery | 当前不一致 | 100% | RC 抽样 + 自动 contract test |
| JIT 敏感 evidence grant 越权/过期访问 | 当前未统一 | 0 | 实时 revoke；任一命中 Security review |
| break-glass 事后 review 完成率 | 当前未统一 | 100%，≤ 1 business day | 未完成禁止 incident closure |
| enabled domain annex certification | 当前未统一 | 100% | SiteRelease/Wave exit blocker |
| WCAG 2.2 AA P0 Admin journey failure | 当前待测 | 0 | 每个 RC；阻断发布 |

所有指标引用版本化 `ProductMetricRevision`，冻结 numerator、denominator、exclusions、window、dimensions、
event source、owner、target/guardrail、alert 和 mandatory action；至少按 Site/Profile/domain/command/risk class 切分。
不得以全局平均掩盖单 Site、单 queue 或单角色失败，label 不得包含用户标识、prompt、Code fingerprint、原始
Provider error 或其他高基数敏感值。

### Non-Goals

- 不成为新的业务真源，不拥有 Payment、Credit、Run、Job、Artifact、Decision、Notification 或 Data Rights 状态。
- 不提供万能 ResourceTable、SQL console、任意 JSON mutation、任意 HTTP replay 或生产 shell。
- 不以 UI 隐藏代替 API/effect-point authorization。
- 不复用终端用户身份、Cookie、MFA session、Workspace role 或 Site workload credential 作为 operator 权限。
- 不把 GlobalScope 当“超级管理员”，也不允许 BreakGlassScope 绕过 typed command 和领域不变量。
- 不复制 raw Provider payload、secret、credential、完整 Code、支付敏感字段或默认展示 prompt/content。
- 不修改 GA graph、assembly、tool、checkpoint、effect、Handoff、namespace 或 terminal semantics。
- 不要求所有低风险查询在 Wave 7 前拥有同一视觉实现；contract 与安全行为必须同领域 Wave 交付。

## 3. Product model and trust boundary

```text
OperatorIdentity
  operatorId / workforceSubjectRef / status / assurancePolicyRef
  roleGrantRefs / deviceTrustRefs / operatorEpoch / restrictionEpoch

OperatorSession
  sessionId / audience=admin / authTime / factorRefs / deviceRef
  activeScopeRef / environment+region / issuedAt / expiresAt / sessionEpoch

OperatorScopeGrant
  SiteScope(environment, region, siteId)
  GlobalScope(environment, regionSet, incidentOrDutyRef, allowedSiteIds, resources, fields, actions)
  BreakGlassScope(environment, region, incidentRef, exact resource/action/field digest, short TTL)

OperatorCommandDefinition
  commandId / revision / domainOwner / inputSchemaRef / outputSchemaRef
  roles / allowedScopes / riskClass / reasonPolicy / stepUpPolicy
  approvalPolicy / expectedVersionPolicy / idempotencyPolicy
  projectionRefs / piiPolicy / queue+SLA / audit+notification policy
  receiptSchemaRef / reconciliationRef / recoveryRunbookRef

OperatorCommandRequest
  requestId / commandRevision / actor / immutable environment+region / scopeGrantRef / reason
  parameterDigest / expectedVersion / idempotencyKey / correlationId
  evidenceRefs / approvalState / createdAt / expiresAt

OperatorCommandReceipt
  requestId / authoritativeDomainReceiptRef / outcome
  committedVersion / effectSummary / notificationRef / completedAt

OperatorAccessGrant
  immutable environment+region+siteId / resource+revision / fields / purpose / caseOrIncidentRef
  approver / operator+restriction epochs / issuedAt / expiresAt / singleUse
```

Admin Web 只通过 Admin BFF 调用 Admin API/RPC。BFF 不 import 领域 repository/schema client，不持有能够绕过领域
API 的数据库角色。Admin API 每次解析 `OperatorPrincipal` 和 scope grant，并在命令 effect point 由领域 owner 再次
校验 audience、role、scope、operator/restriction epoch、step-up、approval digest、expectedVersion 和 idempotency。
environment/region不是UI筛选项，而是每个session、scope、request、approval、JIT grant、receipt与effect point的不可变授权轴；
production grant不能在staging复用，反之亦然，跨region操作必须由Definition显式允许。

## 4. Operator identity and phishing-resistant authentication

### 4.1 Identity lifecycle

- Operator identity 来自受管 workforce identity，和终端用户 Account 完全分离；相同 email 不建立关联。
- joiner/mover/leaver 流程必须有 owner、审批、到期和自动回收；离职、停用、风险 restriction 或职责变化推进
  `operatorEpoch`，已签 session、scope、approval、JIT grant 立即失效。
- 禁止共享账号、通用 on-call 账号和不可归因 API key。自动化使用 audience-bound `WorkloadPrincipal` 与单独的
  machine command allowlist，不伪装 Operator。
- 角色 grant 使用最小权限、职责分离和定期 access review；临时 duty grant 自动到期。

### 4.2 Authentication and session

- privileged operator 登录与高风险 step-up 必须使用 phishing-resistant factor，例如硬件绑定公钥凭据；TOTP、
  SMS、email link、knowledge question 单独不满足该要求。
- 登录校验受管 IdP/session、设备合规、operator status 与 risk signal；异常设备、地域或会话风险进入额外 challenge
  或 deny，不静默降级为较弱 factor。
- Admin session 使用独立 audience、Cookie/storage、CSRF 与 origin policy；不得与用户面共享 session。
- idle、absolute 与 step-up TTL 按风险等级冻结。返回认证后恢复原 scope 和 command draft，但必须重新读取当前
  projection、版本和审批状态，禁止自动执行旧 intent。
- session、device、role 或 scope 撤销在下一次读取和 effect point fail closed；长页面不得依赖首次加载时的权限快照。

### 4.3 Scope semantics

| Scope | Entry and limits | Mandatory evidence |
|---|---|---|
| `SiteScope` | 默认 scope；固定一个 siteId；搜索、队列、投影和命令均自动限定该 Site | active role grant、Site assignment、审计 |
| `GlobalScope` | 仅明确跨 Site duty/incident；显式列举 siteIds/resources/fields/actions；分 Site 返回隔离结果 | reason、duty/incident ref、step-up、时间边界、完整审计；高风险需 checker |
| `BreakGlassScope` | 单个紧急事件的最窄临时提升；默认只读；不能创建开放式搜索能力 | P0 incident/case、exact digest、短 TTL、实时 page、独立批准或事后 checker、强制 review |

scope 切换是显式用户动作：顶部持久显示当前 scope、Site/incident、到期时间和视觉风险状态；Global/BreakGlass
不能跨 tab 隐式继承。进入更宽 scope 清空旧搜索结果、选择、bulk action 与 command draft。Global 结果逐 Site
分区，不能按相同 email、subject、workspace、payment 或 asset hash 合并对象。

BreakGlass 不能读取 secret/credential、直接查数据库、放宽 Platform baseline、跳过领域 command、跳过
maker-checker 后永久执行高风险 mutation，或把 Site Case 升格为跨 Site identity search。若紧急安全动作允许
单人先收紧，必须短 TTL、立即 page、只允许 deny/revoke/suspend 类动作，并在冻结时限内补独立 review。

## 5. Unified shell and information architecture

### 5.1 Shell

```text
Overview / My Duty
Scope switcher and persistent risk banner
Global safe search and correlation timeline
Queues / SLA / Escalations
Approvals / My requests
Reconciliation / Campaigns
Audit / Access history
Support handoffs
Domain annex navigation
System health / runbooks
```

统一壳负责 operator session、scope、导航、搜索框架、工作列表、通知、draft/selection 恢复、审批和审计体验；
领域 annex 负责结果字段、状态解释、命令、风险摘要、receipt 和恢复。壳不能推断领域状态、拼装 mutation payload、
直接写业务表或把多个领域事实压成新的 authority。

### 5.2 Safe projection

- 每个 projection 由领域 owner 发布版本化 schema，携带 `siteId` 或明确 platform scope、source owner、source
  revision、observedAt、freshness SLA、partial/unknown markers、field classification 和 allowed action refs。
- 默认只返回完成任务所需的 normalized whitelist。PII、原内容、原始 Provider payload、金融细节和安全 evidence
  使用 redaction、tokenization 或安全摘要；“无权限”和“其他 Site 不存在”返回不可区分结果。
- projection stale/partial/unknown 时如实显示最后更新时间、缺失 owner 和恢复 CTA；不可用不授权直查数据库。
- correlation timeline 保留来源与时序，不把 projection 当 business fact；每项可跳转回 owner annex。
- export/copy/print 根据 classification 单独授权和审计；高敏字段默认禁止批量导出。
- 搜索只接受 canonical refs 或该 Site 内获准的 lookup key。前缀、模糊搜索、相同 email 搜索不得扩展 scope。

### 5.3 Product states and state restoration

| State | Operator meaning | Required recovery |
|---|---|---|
| fresh | projection 在 freshness SLO 内 | 可依据当前 version 准备命令 |
| stale | 数据可能已变化 | refresh/reproject；提交前重读 version |
| partial | 已知缺少一个或多个 participant | 展示缺失 owner，保留已知事实，不猜终态 |
| unknown | effect/outcome 未证实 | reconcile/query same identity，禁止 blind retry |
| approval_pending | immutable request 等待 checker | 查看 digest/diff/expiry；不得编辑原 request |
| executing | owner 已接受 command | 查询同 request/idempotency receipt |
| succeeded | authoritative receipt 已提交 | 展示 receipt、影响、notification 与 next state |
| rejected | auth/version/policy/approval 拒绝 | 精确原因；必要时重新建 request，不复用失效批准 |
| reconciliation_required | timeout、callback、projection 或 participant 不一致 | 转入 owner queue/runbook，保留 stable identity |
| expired | session/scope/approval/JIT grant 到期 | re-auth/re-request；返回 draft 但重新校验所有事实 |

刷新、断网、tab crash 或设备切换后，壳可恢复非敏感 filter、queue position 与未提交 draft；不得持久化 raw PII、
evidence、secret 或 step-up token。已提交 command 只通过 requestId 查询，不重新 POST。scope/role/epoch 变化时清除
不再授权的缓存，并将 draft 标记为需重新验证。

## 6. Typed command registry and execution contract

### 6.1 Registry requirements

每个可执行 operator command 必须在 `OperatorCommandRegistry` 唯一登记：

```text
commandId / revision / domain owner / owning Wave
input and receipt runtime schemas / stable parameter digest rules
allowed roles / Site|Global|BreakGlass scope / resource binding
read|write and low|medium|high|critical risk class
reason taxonomy and minimum free-text policy
phishing-resistant step-up and freshness
maker-checker policy and prohibited role combinations
expectedVersion/CAS and conflict behavior
idempotency identity, TTL and duplicate-query behavior
PII/evidence field policy and JIT grant requirement
queue owner, SLA revision, escalation and capacity policy
audit event set and retention class
user/operator notification policy
authoritative receipt schema
timeout/unknown reconciliation and recovery runbook
feature/Profile/SiteRelease eligibility
```

未知 command/revision、未注册入口、disabled Profile、scope 不匹配、缺 owner/SLA/runbook、schema/digest 不一致均
fail closed。UI command availability 只作提示，API 和领域 effect point 独立授权。registry revision 发布不可原地改
语义；在途 request 固定原 revision，执行前仍重验 current restriction/operator epochs 和 release eligibility。

### 6.2 Command lifecycle

```text
select current safe projection
→ choose registered command
→ enter reason and typed parameters
→ preview immutable diff, affected scope and recovery plan
→ fresh step-up where required
→ submit request with expectedVersion + idempotency identity
→ checker independently reviews exact parameter digest where required
→ domain owner validates again and commits command/intent
→ external effect progresses asynchronously where applicable
→ authoritative receipt / unknown / reconciliation_required
→ notification, audit closure and Support resolution
```

- 浏览器生成的 digest、role、scope 或 risk class 不可信；服务端依据 registry revision 重算。
- timeout 后查询同 requestId/idempotencyKey；不得复制 request 以“再试一次”。
- expectedVersion 冲突展示新旧 diff，旧 approval 作废；maker 必须基于新事实创建新 request。
- 外部 Provider effect 不放在数据库事务内；先记录 durable intent/inbox/fact，再由 owner worker 推进与 reconcile。
- bulk/mass command 必须 dry-run，冻结 selection snapshot、estimated impact、exclusions 与 per-item identity，支持
  pause/resume/cancel-future-work、逐项 receipt、partial/unknown 和可恢复 campaign；不得用一条 SQL 更新替代。

### 6.3 Maker-checker

- financial adjustment、Grant、refund/reversal、mass action、GlobalScope mutation、release/policy/model publish、
  owner/security recovery、retention/legal hold、secret/provider account 与高风险 allow/takedown 必须 maker-checker。
- maker、checker 和 executor 的职责组合由 command policy 冻结；至少 maker 与 checker 是不同 Operator，checker
  必须以自身当前 role、scope、device 和 phishing-resistant step-up 完成批准。
- checker 看到 exact immutable parameters、diff、scope、reason、evidence 安全摘要、risk、blast radius、expiry、
  notification 与 rollback/recovery；不能批准 wildcard 或执行后补参数。
- 自批、代理批、过期批准、撤销角色、stale version、digest 变化和已用 approval 全部拒绝并审计。
- 允许紧急先收紧的命令必须明确列入 registry，自动到期并触发实时 page 与事后 checker；不允许紧急放宽。

## 7. JIT evidence and sensitive data access

- 默认 projection 不展示 raw evidence。operator 从 Case/Incident/command purpose 请求 `OperatorAccessGrant`，指定
  Site、resource+revision、字段、动作、reason 和 TTL；领域 owner 在每次 view/download/copy 时重验 operator/
  restriction epoch。
- 普通查询使用 redacted/sanitized derivative；只有 need-to-know 才提升到更敏感 derivative。raw content、支付
  provider payload、identity evidence、rights/consent、illegal-content 与 legal evidence 使用不同 clearance。
- grant 不赋予 mutation/Decision 权，不可跨资源、字段、Site、revision、tab 或 action 复用；过期、撤销或 scope
  切换立即拒绝。
- 最高危 evidence 默认 blur/mute/frame-sample/redacted transcript、watermarked viewer、禁止下载/复制；使用专门
  clearance 和双人/专岗策略，审计每次 access，并执行 reviewer wellness 与 exposure minimization。
- Evidence chain-of-custody 保留 provenance、hash、capture/scan/classification、derivative、retention/LegalHold 与
  access receipt；Admin 不复制 evidence payload 到 Case note、audit message、clipboard history 或 analytics。

## 8. Queues、SLA、reconciliation and Support handoff

### 8.1 Queue contract

每个领域 annex 至少登记 queueId、accepted work kinds、severity、routing attributes、accountable owner、backup、
business calendar、capacity policy、acknowledgement/update/resolution clocks、pause rules、aging threshold、escalation、
breach communication 和 runbook。`waiting_internal`、provider unknown、approval pending 不得被默认视为 SLA 暂停。

统一壳提供 My Queue、unassigned、aging、breached、waiting user/internal、escalated、campaign 与 reconciliation 视图。
自动路由只建议或按冻结 policy 分派，不改变 accountable owner。队列移动保留原 SLA timeline、reason 与 audit，
不得通过反复转队重置时钟。

### 8.2 Reconciliation

- reconciliation 是 owner command/read model，不是 Admin 自行修表。入口来自 timeout、unknown Provider outcome、
  inbox/outbox/DLQ、projection lag、missing receipt、stale lease、settlement mismatch 或 participant partial。
- 每项有 stable identity、last authoritative fact、attempt history、next safe action、deadline、owner 和 user impact。
- `retry` 仅在 registry/runbook 证明 no effect 或同一幂等 identity 可安全重放时可用；否则 query、wait、void、
  compensate 或人工决策。
- reconcile 结果返回 authoritative receipt，并推动 projection、notification、Case resolution 和 audit；不得把
  “worker accepted”写成业务 completed。

### 8.3 Support handoff

SupportCase 与 Admin command 双向引用但不互相拥有状态：

```text
Support Case safe timeline
→ HandoffRequest(caseId, siteId, domain, command/queue kind, verification grant, evidence refs)
→ domain queue acknowledges with owner and dueAt
→ operator executes typed command / reconciliation
→ authoritative domain receipt
→ CaseTimelineProjection + public Resolution + NotificationRequest
```

- handoff 保留 Case SLA 与领域 queue SLA，两者分别可见；接收领域必须 acknowledgement，不能静默“转交”。
- Case verification grant 是 subject/action/digest/TTL bound，领域 effect point 单次消费；Case ownership 或 Support
  judgment 不替代高 assurance verification。
- Support 只能看到 safe projection 和允许 CTA；不能扩大 JIT access、直接执行未注册命令或把 internal note 当证据。
- 财务/安全/数据权利 Case 只有在 authoritative receipt、用户可见 Resolution、mandatory NotificationRequest 和
  confirmation/appeal policy满足后才能关闭。

## 9. Audit and accountability

Audit 是追加事实，至少覆盖：login/logout/challenge、role/device/scope grant、scope switch、search/read/export、
JIT request/grant/view/revoke、command draft/submit/approve/reject/execute/outcome、version conflict、reconcile、queue
assignment/escalation、Support handoff、notification、break-glass page/review 和 policy/registry release。

每个事件包含 eventId、occurredAt/receivedAt、operator/workload principal、session/device、trusted scope、domain/
resource refs、command/request/approval/receipt/correlation refs、reason category、parameter digest、policy revisions、
outcome 和 source service；敏感参数只保留 digest/安全摘要。audit 写入失败时，高风险读取/mutation fail closed；
低风险读取的降级策略必须显式登记并 page，不能静默丢审计。

Auditor 默认只能读审计投影，不能因此获得业务 PII/evidence。审计查询、导出和 LegalHold 自身也被审计。任何
receipt 都能反向定位 maker、checker、scope、registry revision、输入 digest、领域事实与 notification；任何 audit
mutation 入口、覆盖历史或“管理员删除日志”均为 release blocker。

## 10. Domain annex contract and Wave ownership

### 10.1 Mandatory annex template

每个领域在自身 Wave 必须发布版本化 annex，至少包含：

1. domain owner、owning Wave、enabled Profiles 与 release dependency；
2. operator roles、Site/Global/BreakGlass 适用边界和 prohibited combinations；
3. safe projections、字段分类、freshness、搜索键和 cross-Site negative behavior；
4. queues、Case kinds、SLA、escalation 和 on-call mapping；
5. typed command matrix、runtime schemas、risk/step-up/maker-checker、CAS/idempotency；
6. audit、user/operator notification、authoritative receipt 和 Support handoff；
7. unknown/partial/timeout/DLQ reconciliation 与 recovery runbook；
8. mobile/a11y/i18n 状态、negative tests、metrics、dashboard 和 alert；
9. direct DB mutation/import 的静态与运行时负向证据；
10. Wave exit evidence 与向统一壳注册的 annex manifest revision。

缺 annex 不表示等到 Wave 7 再补；它表示该领域 Wave 不能退出、对应 Surface 不能进入 SiteRelease。

### 10.2 Domain operating contracts

| Domain / owning Wave | Safe projections and queues | Required typed workflows and invariants |
|---|---|---|
| Identity & operator security / Wave 1 | operator/account security timeline、device/session/recovery queue；secret 与 recovery code 永不投影 | revoke sessions/devices、lock/unlock by Decision、recovery/ownership transfer；高 assurance verification，不能设临时密码、mark verified 或改 credential 表 |
| Site lifecycle & Fleet / Wave 1 contract, Wave 7 shell | Site/Domain/Certificate/Release/DeploymentObservation、drift/failed rollout queues | provision、verify domain、compile/preview/canary/promote/rollback/suspend/decommission；immutable release、compatibility、traffic/rollback receipts |
| Catalog/Offering/Commerce / Wave 2A/2B | revision diff、Order/Subscription/Fulfillment/Payment Fact timeline、webhook/reconciliation queues | publish catalog/offering、refund/dispute/original-route recovery、fulfillment reconcile；历史 fact append-only，redeem-only Site 禁止新 Payment acquisition |
| Credit/Usage / Wave 2A | Grant provenance、Journal/Hold/Usage/Settlement safe ledger、aging/mismatch queues | IssueAdminGrantAcquisition、CreateCorrectionTransaction、revoke source、reconcile Hold/Settlement；不得直接改余额/Journal，不得跨 source 扣减 |
| Redeem / Wave 2A | Program→Batch→fingerprint→Redemption→Fulfillment→Grant timeline，pending-review/compromise queues；永不显示 Code 原文 | publish Program、generate/export/activate/suspend Batch、review、source reversal、replacement、mass revocation campaign；single-use delivery、dry-run/maker-checker/per-item receipt |
| Payment / Wave 2B if enabled | Provider-safe Payment/Refund/Dispute/Inbox facts、unknown webhook/settlement queues | refund、dispute response、webhook reconcile、provider-account routing；只走原 Payment/ProviderAccount，raw payload JIT，不能伪造 success 或提前撤销权益 |
| Session/Run / Wave 3 | Session/Message/Branch/Run projection、stream/control/reprojection queues；不向普通 operator 暴露 namespace | cancel/control/reproject/query terminal receipt；Run 真源仍在 owner，unknown effect 不 restart，Admin 不写 Session message |
| Job/Operation / Wave 4 | Operation/Job/Attempt/lease/progress/cost/artifact lineage、stuck/unknown/DLQ queues | cancel、retry-no-effect、reconcile provider、requeue safe attempt、finalize partial；epoch fencing、stable identity、不可盲重试 Provider |
| Artifact/Library / Wave 4 | ArtifactVersion/Blob/lineage/rendition/share/moderation/retention、missing/rendition/GC queues | rebuild rendition、restore within retention、revoke Share、retry export/GC；不伪造 Blob、不按 content hash 合并 identity、publication 单独授权 |
| Model control / Wave 5A | Definition/Deployment/Pool/Route/Assignment/health/cost revision、health/cooldown/fallback queues | publish deployment/profile/route、routing dry-run、Site assignment、cooldown/emergency restrict；secretRef-only、certified route、在途 authorization 不漂移 |
| Agent/Capability / Wave 5A/5B/6C | revision/package/connection/permission/health projection、revocation/connection queues | publish/revoke revision、connection/OAuth recovery、permission/assignment；不暴露 secret，不以本 PRD 授权 GA runtime semantic change |
| Trust/Risk / Wave 1 contract, Wave 3/4 enforcement, Wave 7 shell | Decision/Restriction/Appeal/report/rights/consent/purge safe timelines；专用 review、appeal、illegal-content、rights queues | publish policy、Decision CAS、grant content access、revoke publication、purge、appeal/rights resolution、emergency restrict；Site 不放宽 baseline，原 Decision/evidence 不覆盖 |
| Notification / Wave 1 contract, Wave 6C/7 | Request/Delivery/preference/template/provider safe status、retry/DLQ/unknown queues | publish template/provider revision、retry same identity、suppress under policy、reconcile callback；provider accepted 不等于 delivered，mandatory event 不被偏好关闭 |
| Data Rights / Wave 1 contract, participant per Wave, Wave 7 coordinator | Export/Deletion/Retention/LegalHold plan + participant/GC receipts、partial/blocked queues | verify/plan/execute/retry participant、apply/release hold、complete only with all mandatory receipts；epoch race 重算，coordinator 不跨库删除 |
| Support / Wave 1 contract, domain annex per Wave, Wave 7 shell | Case/timeline/SLA/verification/handoff projection、triage/escalation queues | verify、assign、handoff、resolve/reopen；补偿回领域 command，Case 不复制业务事实或扩大 scope |

### 10.3 Wave 7 aggregation boundary

Wave 7 可交付：统一 Admin shell、operator UX、scope switcher、跨域 safe search/correlation timeline、queue/approval/
reconciliation 聚合、Support handoff、Audit viewer、Site Fleet 与治理领域自身的 Wave 7 annex、annex manifest
装配、移动/无障碍 UAT。

Wave 7 不可交付为补丁：前序领域缺失的 effect-point auth、typed command、idempotency/CAS、领域 receipt、
RestrictionEpoch、Data Governance participant、notification event、reconciliation owner 或 audit emission。任何领域
annex 未在其 Wave 达标，必须阻断该领域/Surface，而不是允许 Wave 7 用 direct DB、脚本、通用 ResourceTable、
万能 proxy 或 shadow table 代偿。

## 11. Mobile、accessibility、localization and safety UX

- 全球最低 WCAG 2.2 AA，完整 P0 operator process、状态、错误、审批和 timeout 均适用；Site 只能收紧。
- 所有流程支持 keyboard、可见 focus、正确 focus return、screen reader name/role/state、live region、error
  association、200% zoom、reflow、contrast、reduced motion、timeout extension 与 non-color risk indicators。
- tables 在窄屏变为有语义的 cards/list，不丢字段 label、scope 或 version；大型 diff、timeline、ledger 与 campaign
  提供线性/文本等价视图，不能只依赖图表、hover、颜色或横向拖动。
- 移动端优先支持 acknowledgement、只读诊断、page 响应、低风险 action 和明确允许的 approval；critical bulk
  execution、raw evidence、policy/release diff 若无法安全展示完整参数则必须只读并引导受管桌面，不做截断审批。
- 触屏 destructive action 不能仅靠滑动；需要清晰标签、影响摘要和确认。step-up 后恢复原 intent 但重新校验。
- locale、timezone、business calendar、数字/Credit/金额和日期按 SiteRelease/SupportTier revision；audit 同时保留
  canonical timestamp。reason taxonomy 稳定，用户通知使用冻结模板 revision。
- 高风险模式使用一致 banner 和退出动作，不制造“红色即可以忽略”的告警疲劳；scope、Site、environment、
  dry-run/live、maker/checker 状态在关键确认区重复显示。

## 12. Edge cases

| Scenario | Expected behavior |
|---|---|
| Operator 在两个 Site 使用相同搜索值 | 每次只返回 active SiteScope 结果；无 count/timing 泄漏 |
| GlobalScope tab 被复制或恢复 | 必须重新验证 scope grant；不继承 results、selection 或 command draft |
| checker 审批后参数或 expectedVersion 变化 | approval 作废；新 request 与新 digest 重新审批 |
| command timeout after owner accepted | 查询同 request/idempotency receipt；不创建第二 effect |
| projection stale but mutation button cached | effect point 以 current version 拒绝；UI 显示新 diff |
| operator role/session 在 campaign 中撤销 | 后续 action 和访问拒绝；owner worker安全收口已提交 items，重新分派 |
| break-glass 到期时 evidence viewer 打开 | 下一次 fetch/segment 立即拒绝并清除敏感缓存 |
| audit sink unavailable | 高风险 read/write fail closed并 page；不得本地无审计执行 |
| queue 被转派多次 | 原 clock 与 breach history 保留，不因转队重置 SLA |
| provider outcome unknown | 进入 reconciliation；retry 仅在证明 no effect 或同 identity safe 时可用 |
| disabled Payment Surface 有历史 Payment Fact | 只开放原事实 refund/dispute/reconcile；禁止新 Checkout/Provider IO |
| partial Data Rights participant outage | request 保持 partial/blocked；不得标 completed 或跨库手删 |
| Support Case 与 domain receipt scope 不同 | handoff/receipt 拒绝并触发 security audit，不更新 Case Resolution |
| raw content accidentally pasted into reason | 客户端/服务端检测并阻止或 redact/quarantine；不写 audit/analytics |
| mobile viewport truncates approval diff | execution disabled；提供完整可访问视图后才可批准 |

## 13. Acceptance criteria

### AC-ADM-01 — Phishing-resistant operator authentication

```gherkin
Given an operator has only password, TOTP, SMS or email authentication
When the operator opens a privileged Admin session or performs required step-up
Then access is denied until an approved phishing-resistant factor succeeds
And the resulting session is bound to the Admin audience, operator and managed device policy
```

### AC-ADM-02 — Site-private search

```gherkin
Given Site A and Site B contain subjects with the same email or external reference
When a Site A operator searches within SiteScope
Then only Site A authorized safe projections are returned
And no count, error, latency or field reveals Site B existence
```

### AC-ADM-03 — Explicit GlobalScope

```gherkin
Given an operator has a global incident duty
When the operator requests cross-Site projections
Then the grant explicitly lists allowed Sites, resources, fields, actions and expiry
And results remain partitioned by Site with reason and access audit
```

### AC-ADM-04 — Break-glass confinement

```gherkin
Given a P0 incident requires exceptional access
When BreakGlassScope is activated
Then it is incident, resource, field, action and short-TTL bound and pages the accountable owner
And it cannot access secrets, direct databases, arbitrary identity search or unregistered commands
And closure requires independent post-incident review
```

### AC-ADM-05 — Registered command only

```gherkin
Given a UI, API caller or operator submits an unknown or disabled command revision
When Admin API and the domain effect point authorize it
Then the request fails closed without mutation
And the release inventory records no callable unregistered command path
```

### AC-ADM-06 — Maker-checker independence

```gherkin
Given a high-risk command request has an immutable parameter digest
When the maker self-approves, the checker lacks current scope, or parameters change after approval
Then execution is rejected without a domain command
And a different authorized checker must approve the exact current digest using fresh step-up
```

### AC-ADM-07 — Expected-version conflict

```gherkin
Given a checker approved a command against resource version 12
When the domain resource advances to version 13 before execution
Then the owner rejects the stale expectedVersion
And the console shows a safe diff and requires a new request and approval
```

### AC-ADM-08 — Timeout does not duplicate effect

```gherkin
Given a refund, Grant, reversal, publish or Provider command times out after submission
When the operator resumes or retries the workflow
Then the console queries the same request and idempotency identity
And no second financial, publication or Provider effect is created
```

### AC-ADM-09 — Safe projection failure

```gherkin
Given a domain projection is stale, partial or unavailable
When an operator opens its timeline
Then the UI shows source, freshness, missing owner and the registered recovery action
And it neither guesses a terminal state nor queries the business database directly
```

### AC-ADM-10 — JIT evidence confinement

```gherkin
Given an operator has a ContentAccessGrant for one Site, resource revision and field set
When another Site, raw derivative, expired TTL, copy or unlisted action is requested
Then access is denied and audited
And the grant confers no Decision or mutation authority
```

### AC-ADM-11 — Credit correction preserves ledger

```gherkin
Given a verified balance dispute requires correction
When Finance approves the remedy
Then the console emits a typed append-only correction or Admin Grant acquisition command
And no balance, Journal row or unrelated source lineage is directly rewritten
```

### AC-ADM-12 — Redeem secrecy and campaign safety

```gherkin
Given a compromised Redemption Batch requires mass action
When an authorized campaign is approved and executed
Then the UI never reveals complete Codes and records dry-run scope, per-item identity, progress and receipts
And partial failure can resume without repeating completed reversals or replacements
```

### AC-ADM-13 — Payment disabled boundary

```gherkin
Given a redeem-only Site has no historical Payment Fact
When an operator attempts Checkout, Refund, Dispute or Provider IO mutation
Then the command is unavailable and rejected at the API and domain effect point
And no Order, Payment, Invoice or Refund fact is created
```

### AC-ADM-14 — Job unknown reconciliation

```gherkin
Given a Job Provider outcome is unknown
When an operator opens recovery
Then the owner reconciler queries the original attempt and stable identity
And no new Provider attempt begins until the original effect is resolved or proven safely void
```

### AC-ADM-15 — Trust decision authority

```gherkin
Given a Trust fact, appeal or urgent report requires action
When a Content operator uses the console
Then only registered Trust commands can append a new Decision or restriction with CAS and required separation
And ResourceTable, Support and direct database access cannot overwrite the prior Decision or evidence
```

### AC-ADM-16 — Data Rights completion truth

```gherkin
Given an Export or Deletion workflow has one missing participant or object-GC receipt
When an operator reviews or retries the request
Then status remains partial, blocked or failed with the accountable owner
And the console cannot mark completed or delete participant data directly
```

### AC-ADM-17 — Support handoff closure

```gherkin
Given Support hands a verified high-risk Case to a domain queue
When the domain action completes
Then the Case receives the authoritative domain receipt, public Resolution and mandatory NotificationRequest
And the Case cannot close while confirmation or appeal policy remains unsatisfied
```

### AC-ADM-18 — Audit failure is fail-closed

```gherkin
Given the durable audit path is unavailable
When an operator attempts a high-risk read, approval, JIT evidence access or mutation
Then the action is denied and the accountable owner is paged
And no local-only or delayed unaudited bypass is offered
```

### AC-ADM-19 — Mobile approval integrity

```gherkin
Given a mobile viewport cannot present the full immutable diff, scope and risk summary accessibly
When a checker opens a critical or bulk request
Then approval and execution remain disabled while acknowledgement and safe read-only diagnosis remain available
And the operator is directed to a supported complete view
```

### AC-ADM-20 — Wave annex enforcement

```gherkin
Given a domain Surface is proposed for SiteRelease before Wave 7
When its owning Wave lacks a certified Admin annex, command registry entries or recovery receipts
Then the Surface and Wave exit are blocked
And Wave 7 cannot substitute a direct database mutation, script or generic ResourceTable
```

### AC-ADM-21 — Environment and region are authorization axes

```gherkin
Given an Operator has a valid SiteScope, approval or JIT grant for one environment and region
When the same identity or request is replayed against another environment or an unlisted region
Then Admin and the domain effect point reject before read, mutation or evidence disclosure
And UI switching, copied tabs or matching Site IDs cannot widen the immutable scope
```

## 14. Dependencies and risks

### Dependencies

| Dependency | Owner | Impact if delayed |
|---|---|---|
| RequestSecurityContext、OperatorPrincipal、restriction/operator epochs | Identity/Security, Wave 1 | 无法可信认证 scope 与即时撤销 |
| SiteRelease/Profile/EnabledSurfaceInventory | Site Fleet/Product Governance | 无法证明 command 随 Surface 启停和版本绑定 |
| 领域 application interfaces 与 receipt schemas | each domain owner | Admin 会退化为表访问或无法恢复 |
| Audit、Notification、SupportCase 最小 contract | Wave 1 owners | 高风险命令无法形成责任和用户闭环 |
| Data Governance participant contract | Wave 1 + each domain Wave | Export/Deletion 无法真实收口 |
| Annex manifest 与 contract generation/coverage gate | Foundation owner | registry、UI、API 和证据可能漂移 |

### Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| 统一壳变成万能业务层 | medium | high | façade only；projection/command/receipt 归领域；依赖与 DB import gate |
| Global/BreakGlass 扩权失控 | medium | critical | explicit lists、short TTL、step-up、page、review、negative tests |
| maker-checker 只做 UI 确认 | medium | high | server-side immutable digest、independent auth、effect-point validation |
| 为排障过度暴露 PII/content | high | high | safe projection、JIT grants、field policy、wellness、access audit |
| unknown 被运营者重复执行 | high | high | stable identity、receipt query、reconciliation owner、禁止 blind retry |
| 队列转派掩盖 SLA | medium | medium | immutable clock/breach timeline、owner acknowledgement、escalation |
| Wave 7 承担前序领域欠债 | high | high | annex-per-Wave exit gate；缺 annex 禁用 Surface，不允许 DB shortcut |
| 移动端截断高风险信息 | medium | high | capability-tiered responsive UX；无法完整展示即只读 |

## 15. Milestones and release gates

### Milestones

1. Wave 0：冻结 registry/annex/evidence schema、stable IDs、generation/coverage gate 和 no-DB-import boundary。
2. Wave 1：交付 operator identity/auth/scope/audit/notification/Support/Data Governance 基础 contract；Identity、Site、
   Trust enforcement annex 同波成立。
3. Waves 2A/2B：Commerce、Credit、Redeem、Payment annex、财务 maker-checker 与 reconciliation 认证。
4. Waves 3/4：Session、Run、Job、Artifact、Studio/Trust stage annex 与 unknown/partial recovery 认证。
5. Waves 5A/5B/6：Model、Agent/Capability、Execution/Automation/Notification annex 按各 cut 认证；不隐式授权 GA
   runtime semantic change。
6. Wave 7：聚合统一壳、Fleet、queue/approval/reconciliation/Audit/Support handoff、Risk/Data Rights 专业工作台，
   完成 cross-domain Operations UAT；不补前序领域 effect contract。
7. Waves 8/9：删除遗留直连/万能表/隐藏入口，完成 profile-scoped security、load、soak、DR、access review、
   break-glass、reconciliation、mobile/a11y 与 on-call certification。

### Release gates

以下任一失败均阻断对应 Wave、SiteRelease 或生产 promote：

- operator privileged auth/step-up 非 phishing-resistant，或 operator/user session 未隔离；
- enabled Surface 缺 owner、certified annex、safe projection、registered command、queue/SLA、audit、notification、
  receipt 或 runbook；
- Admin Web/BFF import 业务 repository/ORM、拥有业务 DB role，或存在 direct DB/SQL/script/generic mutation bypass；
- Site/Global/BreakGlass scope negative matrix、operator/role/device/restriction epoch revoke 测试失败；
- 高风险 command 可自批、批准 wildcard/变更参数、跳过 fresh step-up 或绕过 expectedVersion；
- timeout/replay/duplicate/callback/lease/partial campaign 产生重复 effect，或 unknown 被标成 succeeded；
- JIT evidence 越 scope/field/revision/action/TTL，或 raw sensitive data 进入 log/audit/analytics/Case note；
- audit 事件、领域 receipt、notification、Support Resolution 任一无法端到端关联；
- queue owner/on-call 不可路由、P0 page 或 SLA breach escalation 演练失败；
- WCAG 2.2 AA、keyboard/screen reader/reflow、移动安全降级、locale/timezone/business-calendar UAT 失败；
- enabled domain 的 Wave annex 延迟到 Wave 7，或 Wave 7 试图用 shadow truth、万能 proxy/ResourceTable 代替；
- GA graph/checkpoint/effect/Handoff/namespace/terminal semantics 发生未单独授权的变化。

RC evidence 至少包含 registry/inventory diff、static DB-boundary scan、API/effect-point negative matrix、maker-checker
separation、scope revoke、audit/receipt trace、JIT access revoke、unknown/replay/reconciliation、queue/SLA/page、Support
handoff、break-glass drill、Data Rights partial、mobile/a11y/browser 和 two-Site isolation 测试。

## 16. Review questions and authorization boundary

- [ ] Security：phishing-resistant factor、device policy、scope/epoch revoke、break-glass 与 audit fail-closed 是否批准？
- [ ] Finance：Grant/refund/correction/reversal、maker-checker、source lineage 与 reconciliation 是否批准？
- [ ] Risk/Legal：Trust Decision、evidence access、illegal/rights queues 与 emergency restrict 是否批准？
- [ ] Data Governance：participant、LegalHold epoch、partial completion 与 audit retention 是否批准？
- [ ] Site Fleet/SRE：annex-per-Wave、queue/on-call/SLA、Wave 7 aggregation 与 release evidence 是否批准？
- [ ] Support：verification grant、handoff、Resolution/notification/confirmation 闭环是否批准？
- [ ] QA/A11y：cross-Site negative、replay/unknown、mobile/browser、WCAG 2.2 AA matrix 是否批准？

本文处于内部评审，`implementationAuthorized: false`。批准本文也不授权业务实现、数据迁移或生产变更。
`gaRuntimeSemanticChangeAuthorized: false`：本文仅定义 Admin 产品与领域控制面契约，不授权修改 GA runtime 语义。
