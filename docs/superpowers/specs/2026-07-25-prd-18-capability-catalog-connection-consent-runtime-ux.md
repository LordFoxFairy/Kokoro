---
artifact: product-requirements-document
prdId: PRD-18
version: "1.0"
created: 2026-07-25
status: internal-review-active
scope: capability-catalog-skill-mcp-connection-consent-runtime-operations
accountableProductRole: Capability Product Lead
mandatoryCosigners: [Platform, Security, Privacy, Agent, Session, Credit, Trust, Admin, Support, SRE, QA]
engineeringOwner: team:capability-platform
qaOwner: team:capability-quality
supportOperationsOwner: team:capability-operations
namedOwnerAssignmentStatus: assigned-team-responsibility-ids
implementationAuthorized: false
gaRuntimeSemanticChangeAuthorized: false
---

# PRD-18：Capability Catalog、Connection、Consent 与 Runtime UX

## 1. Overview

### 1.1 Problem

Kokoro 已有 Skill/MCP 能力中台和 GA 装配底座，但“能被系统调用”不等于“用户可以安全、可理解、可恢复地使用”。
一个 production-ready Capability 必须同时回答：谁发布并审核了哪个不可变版本、哪个 Site/套餐/Agent 可以使用、谁为
哪个 Workspace/User 连接了什么外部账号、当前操作会读取或写入什么、是否需要单次确认、失败或结果未知后如何处理、
产生了多少 usage/cost，以及版本出问题时怎样撤销、回滚和支持用户。

若 Catalog、Assignment、Connection、Permission 与 Runtime Call 混为一个 `enabled`，会出现安装即永久授权、OAuth token
进入浏览器或 GA、升级静默扩权、Routine 延用过期授权、MCP 副作用超时后盲目重试、Site A 连接泄漏到 Site B，以及
运营人员直接改表伪造恢复等风险。

### 1.2 Solution

建立面向 Skill/MCP 的统一产品闭环，并明确五层独立门：

```text
CapabilityRevision qualification
  → SiteRelease assortment + Plan entitlement
  → Workspace/User assignment
  → Connection + consent/SecretRef
  → Admission-frozen CapabilityGrant
  → operation-specific permission/approval
  → CapabilityCall effect journal + usage/cost + receipt
```

Catalog 负责发现与解释；Capability Control Plane 负责不可变版本、审核、包、assignment、connection metadata、撤销与
运营命令；Secret Manager 保存凭据；Capability Runtime 负责 discovery、credential lease、调用、interaction、effect
receipt 和 revocation enforcement。Platform Admission 解析 Site/Plan/Agent/subject 并签发有界 Grant；Session 仅投影
interaction；GA 只消费 opaque namespace、不可变 Skill 内容和受限调用端口，不获得 Site/Plan/price/secret。

### 1.3 Users and Stories

| ID | User story | Priority |
|---|---|---|
| CAP-US-01 | 用户能按任务、风险、数据访问和价格发现当前 Site 真正可用的 Skill/MCP | P0 |
| CAP-US-02 | Workspace Owner 能审阅权限后安装、分配、连接和撤销，不把一个人的账号误给全团队 | P0 |
| CAP-US-03 | Member 能在 Chat 中知道 Agent 为什么请求能力、将做什么，并只批准本次或合规的有限范围 | P0 |
| CAP-US-04 | Routine Owner 能在发布前验证连接、scope、预算和 unattended eligibility，失效后安全暂停 | P0 |
| CAP-US-05 | Package reviewer 能审核 provenance、权限 diff、兼容性和风险后 canary/发布/回滚 | P0 |
| CAP-US-06 | Admin/on-call 能冻结 revision/connection、reconcile unknown call、观察影响面且不查看 secret | P0 |
| CAP-US-07 | Support 能解释 disabled/reauth/denied/unknown/cost_pending 并给出安全恢复路径 | P0 |
| CAP-US-08 | Site Release Owner 能证明每个开放 Capability 有 Qualification、journey、runbook、dashboard 和回滚证据 | P0 |

## 2. Goals、Metrics and Non-Goals

### 2.1 Goals

1. 从 Catalog 发现到首次成功调用、撤销、故障恢复和运营审计形成闭环。
2. 将可见、可安装、可分配、已连接、可调用和已批准建模为不同状态，任何一层缺失均 fail closed。
3. 所有外部副作用具有稳定 identity、可验证 receipt 和 unknown reconciliation，禁止 blind retry。
4. 凭据永不进入浏览器、Session、GA Manifest、prompt、event、analytics 或普通日志。
5. Skill/MCP 的 usage、预算和 customer charge 与统一 Credit/Rating 主链对接，但 Capability 不定价、不改余额。
6. package/revision 支持 review、canary、live revoke、rollback 和已运行任务的诚实处置。

### 2.2 Success Metrics

| Metric | Target |
|---|---:|
| 跨 Site Catalog/Assignment/Connection/Call 泄漏 | 0 |
| 未 Qualification 或未纳入 active SiteRelease 的 Capability 被调用 | 0 |
| secret/token 出现在浏览器、GA、Session event、日志或 analytics | 0 |
| 权限扩大升级未重新 consent 仍生效 | 0 |
| 高风险外部 effect 缺 approval/effect receipt | 0 |
| unknown effect 被自动重试或被误写成 failed/succeeded | 0 |
| revoke commit 后产生新的未授权 effect | 0 |
| Catalog → connection start conversion | 建立 baseline；RC 后按 Site/category 周监控 |
| connection flow completion p95 | ≤ 3 分钟（不含外部 Provider 人工审核） |
| 首次成功调用率 | ≥ 95%，并按 capability/provider revision 分层 |
| token refresh 可自动恢复且不要求重复授权 | ≥ 99%（Provider 支持范围内） |
| critical revision revoke enforcement | command commit 后 effect point 100% 拒绝；告警 p95 ≤ 60s |
| runtime terminal/unknown 有 owner 与 deadline | 100% |
| usage receipt 与 Credit settlement 可关联 | 100%；允许 `cost_pending`，不允许丢事实 |

可用率不得掩盖 deny、用户取消、Provider policy deny、unknown 或降级；每个分母按 Site、kind、revision、operation、
provider、risk tier、interactive/unattended 单独定义。

### 2.3 Non-Goals

- V1 Catalog 只正式开放 `skill` 与 `mcp`；Connector/Plugin/Hook/Command 延续同一治理骨架但需独立 PRD/qualification。
- 不在本文改变 GA graph、assembly、prompt、tools/skills/MCP 装配、checkpoint、Handoff、effect journal 或事件顺序。
- 不允许终端用户上传任意代码后直接在生产执行；custom Skill/MCP 必须走受控 intake 与 qualification。
- 不把 Marketplace 排名、广告或分成结算作为 V1 上线条件。
- 不由 Capability Runtime 解释套餐、定价、余额、退款或 customer-facing charge。
- 不承诺所有第三方 OAuth Provider 都支持细粒度 scope、token revoke 或可靠查询；差异必须在 adapter contract 显示。

## 3. Product Model and Authority

### 3.1 Canonical objects

```text
CapabilityDefinition
  capabilityId / kind=skill|mcp / publisherRef / riskTier / lifecycle

CapabilityRevision
  immutable revision / package+content digest / manifest / schemas / permissions
  dataClasses / operations / effectClass / retrySafety / costSignals / compatibility

CapabilityQualificationAttestation
  revision+scope / PRD+contract+test+runbook digests / signer set / expiry+revocation

CatalogListingRevision
  locale content / categories / screenshots / disclosure / support+privacy links

CapabilityAssignmentRevision
  siteId / workspace|agent|subject scope / capability revision/range / allowed operations
  policy+permission refs / assignmentEpoch / actor / effective window

Connection
  siteId / workspace|user scope / capability+provider account safe refs
  granted scopes / subject / consent revision / status / connectionEpoch

SecretRef
  opaque vault reference / credential class / owner / rotation metadata

CapabilityGrant
  signed short-lived Admission output / opaque namespace / revision+operation allowlist
  assignment+connection+restriction epochs / budget allocation ref / audience / expiry

CapabilityCall
  callId / executionRoot+parent refs / logicalOperationId / stable effectKey
  revision+operation / grant ref / connection ref / permission decision ref
  attempt+effect state / usage facts / result+receipt refs
```

### 3.2 Authority separation

| Concern | Canonical owner | Must not own |
|---|---|---|
| Catalog/revision/package/review/assignment/connection metadata | Capability Control Plane | raw secret、customer price、GA graph |
| OAuth/API credential bytes | Secret Manager | Assignment、Call outcome |
| Site/Plan/subject/Agent eligibility and root budget | Platform Admission | credential bytes、runtime effect |
| credential lease、discovery、MCP call、effect receipt | Capability Runtime | Plan interpretation、Credit Journal |
| interaction projection and browser transport | Session | permission authority、connection resolution |
| Agent reasoning and use of granted capability | GA | Site identity、secret、pricing、Connection DB |
| usage rating and settlement | Usage/Credit owner | Provider effect execution |
| user/admin UX | Site Web/Admin Web | business truth、direct database mutation |

`visible != installable != assigned != connected != admitted != approved != invoked`。Catalog Listing 不是授权；安装不创建
credential；Connection 不自动分配给所有 Agent；Assignment 不绕过 Plan；Grant 不等于永久 approval；一次成功调用不证明
未来仍有资格。

### 3.3 Site and subject isolation

- 除 Platform-wide public definition/qualification 外，Assignment、Connection、Consent、Grant、Call、Usage 和审计都带
  immutable `siteId`；effect point 对每个 reference 重验同 Site。
- 同一个外部账号可分别连接多个 Site，但每个 Site 创建独立 Connection、consent、epoch 和 SecretRef；不得因邮箱或
  provider subject 相同自动关联。
- Workspace-scoped Connection 需要 Owner/Admin 创建并明确 allowed members/agents；user-scoped Connection 不可被
  Workspace 其他成员使用。成员离开或权限降低后，新 call 立即因 authorization epoch 失效。
- GA 只看到 opaque `namespace`；Web 与 Support 不展示 namespace，任何地方不得推导 `namespace == owner`。

## 4. Catalog Discovery and Evaluation

### 4.1 Catalog availability

用户只看到当前 SiteRelease 暴露、Plan 允许展示且 jurisdiction/age/policy 合规的 listing。不可用条目可在产品策略允许时
以“了解更多”展示，但必须明确 `not_available_here`，且连接/调用端点仍拒绝；不能仅靠隐藏 UI 实现关闭。

Catalog 支持：任务/category 搜索、kind、read/write、risk tier、data class、price treatment、publisher、verified、locale、
accessibility 和 compatibility filters。排序必须标注 sponsored/curated，不能把 entitlement 或安全资格当推荐分数。

### 4.2 Listing and detail requirements

每个详情至少显示：

- 解决什么问题、输入/输出示例、Skill 与 MCP 的差异、适用 Surface（Chat/Routine/Studio）。
- publisher、当前 revision、last reviewed、Qualification scope/expiry、support/privacy/terms、data residency（适用）。
- 所需数据类别、读/写动作、外部副作用、network destinations、retention、第三方处理方和风险提示。
- 安装主体、Connection scope、需要的 OAuth/API key、是否支持 unattended Routine、是否每次确认。
- 计费方式：free/included/metered/estimated only；只显示 Admission/Rating 发布的用户价格或估算，不直接显示 provider cost。
- compatibility、known limitations、health/degraded、被撤销/下架/迁移状态和替代路径。

Catalog 搜索结果不得泄漏 private/custom Capability 的存在；unlisted/private listing 只能通过 Site-scoped authorized ref 访问。

### 4.3 Progressive discovery at runtime

- 小型已授权 MCP 工具集可在 Run binding 中冻结 exact typed schema。
- 大型工具集先暴露受限 discovery；选中 operation 后将 exact revision/schema/permission/effect class 固定到调用绑定。
- discovery 结果只包含当前 Grant 允许的 operation；不能用搜索猜测未授权 tool 或其他 Site 资源。
- schema 在 Run 中途变化不得静默替换；兼容升级也要创建新 binding/segment，旧 call 按原 revision finalize。
- `mcp_call(server, tool, dict)` 仅为受控兼容面，不能成为绕过 typed schema、permission 或审计的万能入口。

## 5. Qualification、Package and Release Lifecycle

### 5.1 Intake and review

Revision intake 固定执行 provenance/signature、SBOM/license、malware/secret scan、manifest/schema validation、dependency pin、
network allowlist、sandbox/egress、data classification、prompt injection/tool poisoning、安全/隐私/法务、usage metering、
timeout/cancel/retry、unknown/reconciliation、a11y/localization 和 support/runbook 检查。

Skill package 的 prompt/instruction/tool declaration 与 MCP 的 server/tool/resource schemas 分别审核；review 不能把
“能连接”当成“每个 operation 都安全”。动态返回的 tool/schema 必须受 manifest policy 和运行时 schema limits 约束。

### 5.2 Lifecycle

```text
draft → submitted → scanning → review_required → qualified → candidate
      → canary → active → deprecated → retired
                     ↘ rejected | suspended | revoked | rolled_back
```

- Qualification 是 revision+scope 的签名证明，发生在具体 SiteRelease compile 前；不能使用自由 `approved=true`。
- SiteRelease compile 只引用有效 Qualification；compile/build/preview 后另行生成 `ReleaseCertificationInstance`，禁止
  placeholder、自引用或跨 Site/candidate 复用。
- 发布后 revision/package 不可变；任何内容、schema、permission、dependency 或 destination 变化都创建新 revision。
- 权限减少且兼容的升级仍需明确 release diff；权限、数据类别、外部写动作、retention 或 destination 扩大必须重新 consent/
  approval，不得自动升级。

### 5.3 Canary、rollback and revoke

- canary 按明确 Site/Workspace/Agent cohort 和 revision assignment 分流，保留 deterministic assignment、指标与停止条件。
- rollback 只将未来 Admission/Call 指向已 Qualification 且与当前 contracts/policy 兼容的 revision；不改写历史 Call。
- live revoke 增加 capability/assignment/connection/restriction epoch。commit 后新 effect point 必须拒绝；已不可逆提交的 call
  只能 finalize/quarantine/reconcile，不能伪装 canceled。
- package compromise 启动 impact campaign：冻结新调用、列出 affected Site/Assignment/Connection/Call/Artifact、通知、凭据轮换、
  managed output restriction 和 completion receipts。扫描/通知 partial 或 unknown 必须 page，不能宣称已全部清除。

## 6. Install、Assignment and Connection UX

### 6.1 Install and assignment journey

```text
Catalog detail
→ choose subject scope
→ review revision + permissions + data/cost/risk
→ entitlement and role check
→ create assignment draft
→ connect prerequisite (if any)
→ test connection/read-only probe
→ publish CapabilityAssignmentRevision
→ available to next Admission
```

- `Install` 表示建立受治理 assignment，不是复制 package、发永久 token 或立即调用。
- 用户必须选择 `only me`、特定 Workspace/Project/Agent 等允许范围；不以最大范围为默认值。
- 自定义 MCP 接入需明确 endpoint ownership、TLS/SSRF/DNS rebinding、redirect、schema/response limits、egress 和 secret capture。
- 删除 assignment 与 revoke Connection 分开：移除使用权不必立即删除用户凭据；revoke 凭据也不改写历史 assignment。

### 6.2 OAuth and SecretRef

- OAuth 使用 server-side adapter、state/nonce/PKCE（适用）、exact redirect URI、single-use callback correlation 和 step-up。
- 浏览器只接触短期 flow handle；callback 后 token 直接进入 Secret Manager，Control Plane 仅保存 opaque SecretRef。
- API key/manual secret 通过受控 one-time capture，提交后永不回显；复制、日志、analytics、Support screenshot 均禁止。
- scope escalation、provider subject 改变或 Workspace→User scope 转换创建新 consent/revision，不能覆盖原事实。
- Runtime 每次调用获取 audience/operation/TTL-bound `CredentialLease`；lease 不进入 GA，过期后不可继续新 effect。

### 6.3 Connection states and recovery

```text
draft | authorization_pending | testing | active | degraded | reauth_required
revoking | revoked | suspended | failed | unknown
```

| State | User meaning | Allowed action |
|---|---|---|
| authorization_pending | 正在等待第三方授权 | resume/cancel |
| testing | 正在验证最小能力 | wait；不启动业务 effect |
| active | 当前可用于允许的 operation | manage/test/revoke |
| degraded | 部分 operation/Provider health 异常 | 查看影响、使用安全子集或等待 |
| reauth_required | token/scope/subject 不再满足 | reconnect；旧 token 不继续尝试写操作 |
| revoking | revoke 已提交，外部确认处理中 | wait；Kokoro 立即拒绝新 effect |
| revoked | 本地授权已失效 | reconnect as new revision/delete metadata |
| suspended | 风险/运营临时冻结 | appeal/contact owner；禁止绕过创建副本 |
| unknown | 外部授权结果不确定 | query/reconcile/Support；禁止重新提交授权或业务 effect |

OAuth callback duplicate/out-of-order、用户关闭 tab、Provider 授权成功但本地 timeout、refresh 成功但响应丢失，都使用稳定 flow/
connection identity 查询和 reconcile；不能创建第二个 Connection 猜结果。

## 7. Consent、Permission and Elicitation

### 7.1 Three distinct decisions

1. `ConnectionConsent`：允许 Kokoro 代表某主体持有特定 Provider scopes。
2. `PermissionPolicyDecision`：当前 subject/Agent/Surface 是否可以请求某类 operation。
3. `ApprovalGrant`：对准确参数摘要、目标、effect class、预算和时间窗批准本次或受限重复操作。

三者不能互相替代。OAuth 同意不等于允许发邮件/删除文件；Workspace assignment 不等于每个 Member 可使用；用户说“以后都
可以”也不能覆盖 Platform mandatory approval 或扩大到未知参数。

### 7.2 Approval UX

调用前确认卡展示 capability+revision、operation、作用对象、读取/发送/修改/删除范围、外部接收方、可逆性、参数 safe diff、
预计 usage/charge ceiling、是否可重试、Connection identity safe label 和“为什么现在需要”。敏感 payload 默认遮蔽，用户可
按字段选择披露；不能用笼统“允许所有工具”。

Approval scope 可为 `once`、`this_run`、`bounded_routine_revision` 或 policy 明确允许的窄范围；绑定 parameter digest、resource/
destination constraint、max count/cost、expiry、actor/subject generation、assignment/connection/restriction epochs。payment、secret
reveal、security recovery、cross-Site、高风险发布、rights/consent 和 unknown retry 不可预授权。

拒绝不触发 effect；可选择修改参数、换只读 operation、断开连接或继续不使用该能力。审批等待不能占用无限 lease/budget，
过期后重新 Admission 或建立新 Segment，不复用旧 approval。

### 7.3 MCP elicitation

- pre-call elicitation 可通过 Session Interaction 请求缺失字段/选择；响应只返回 Capability Runtime 所需字段。
- mid-call elicitation 必须保持同一 `CapabilityCall/ExternalCall` identity 和 provider session（若支持）。
- 在 elicitation 前可能已产生外部副作用时，不允许从头重跑；无法证明 outcome 或恢复 context 时进入 `unknown`。
- MCP server 请求的额外 scope、任意 URL、secret、文件或高风险动作必须重新经过 Kokoro policy，server 文本不能自行授权。
- Session 只投影 proposal/interaction 状态；Permission authority 和 Call lifecycle 仍在 Platform/Capability owners。

### 7.4 Revoke semantics

- 用户可撤销 Approval、Assignment 或 Connection，并在 UI 中看到三者影响不同。
- revoke commit 是新 effect 的线性化点；缓存传播不能延迟 effect point 拒绝。
- 已提交的不可逆 effect 仍记录真实 outcome、usage 和 cost；撤销不删除审计或伪造退款。
- Routine/queued Run 在下一 effect 前重验 epoch，失效后进入 `waiting_prerequisite`/`paused` 并提供 reconnect/reapprove。

## 8. Runtime Call、Usage and Cost

### 8.1 Call lifecycle

```text
proposed → permission_pending → admitted → claimed → invoking
         → waiting_elicitation | submitted | result_received
         → completed | denied | failed_no_effect | partial | canceled | unknown
```

- 每个 Call 使用稳定 `callId/logicalOperationId/effectKey`；Runtime 先持久化 effect claim，再触发外部 effect。
- retry 由 operation manifest 声明：pure/read/idempotent-with-key 可按边界重试；non-idempotent/unknown 必须 query/reconcile。
- timeout 不等于失败；submitted 后无 canonical receipt 即 `unknown`，保留 committed budget allocation。
- cancel 仅表示请求中止；只有 Runtime/Provider receipt 证明未执行或停止后才能 terminal canceled。
- result schema validation、content/trust evaluation、Artifact promotion（适用）和 usage evidence 各自有状态；一个成功响应不能
  覆盖另一个环节的 partial/unknown。

### 8.2 Budget and settlement

- Platform 创建 ExecutionRoot 的 root Hold，并由 Credit owner 原子分配有界 Capability child allocation；Capability 不能获得
  root 全部 ceiling，也不能自行 reserve 第二份完整预算。
- Admission 冻结 RatingPolicy/price presentation；Capability Runtime 只记录原始 `AttemptUsageFact` 和 provider cost signal。
- Call 交付可为 `completed + cost_pending`；Rating outage 不阻止可安全交付的结果，但 committed allocation 不释放。
- duplicate usage 以 stable attempt/effect identity 去重；correction 使用 append-only receipt，不回写原 usage/ledger。
- 用户视图区分 estimate、reserved ceiling、observed usage、cost_pending、settled 和 reconciliation_required；不得把 provider cost
  或未结算估值称为最终扣费。

### 8.3 Result presentation

Chat tool card 至少显示 proposed/awaiting/started/result/partial/unknown、Capability safe name、operation、Connection safe label、
elapsed、usage/cost status、receipt/correlation 和恢复动作。返回内容按 MessagePart/Artifact contract 渲染；未知版本显示
unsupported card，不丢弃同一 Message 的其他内容。

错误分类固定为 user_action_required、policy_denied、connection_expired、provider_unavailable、failed_no_effect、partial、unknown、
cost_pending；“重试”只在 owner 明确证明安全时出现。

## 9. Surface Journeys

### 9.1 Chat

1. Composer/Agent 根据 frozen Grant 发现能力，不展示未授权工具。
2. 如果未连接，Run 进入 `waiting_prerequisite`，Web 打开 Site-bound connection flow；不把 token 回传 GA。
3. 高风险 operation 创建 approval card；接受后以 same Run/Call identity 继续。
4. streaming tool card 投影 progress/result/unknown；重连使用 Session snapshot+SSE，不从浏览器事件重建真相。
5. Connection revoke 后只阻止新 effect；已有 unknown call 继续 owner reconciliation。

### 9.2 Routine

- 创建/发布 preview 必须列出 required revision、Connection、scope、unattended eligibility、approval policy、maximum budget、
  misfire/concurrency 和失败通知。
- 每次 RoutineRun 重新 Admission，签发新 Grant/allocation；不得保存 raw token、永久 Hold 或复用上次 approval。
- 需要每次交互批准的 operation 默认不可 unattended；若等待用户，RoutineRun 进入 waiting action 并按 deadline pause/expire。
- reauth/revoke/degraded/unknown 时暂停未来 effect，通知 owner；Scheduler 不直接调用 GA 或 Capability Runtime。

### 9.3 Admin and package operations

- 专用视图覆盖 definitions/revisions/packages/qualification/listings/assignments/connections/calls/health/revocation campaigns。
- typed command 包含 expectedVersion、reason、risk、step-up、maker-checker、idempotency、parameter digest 和 receipt。
- publish、rollback、emergency revoke、mass assignment、custom endpoint allow、secret rotation campaign 为高风险命令；Admin Web
  只调用 owner API，不直连数据库或 Secret Manager。
- operator 只能看到 credential type、last validated、expiry 和 safe provider subject label；永不显示 token/key。
- unknown call 只能调用 owner query/reconcile；不能 mark completed、改 usage、释放 Hold 或 blind retry。

### 9.4 Support

- Support projection 提供 Site-safe Catalog/Assignment/Connection/Call timeline、safe reason、freshness、owner、deadline、usage/cost
  状态和允许 CTA。
- Support 可以引导 reconnect、提交 consent/connection dispute、请求 owner reconciliation；不能代用户授权、查看 secret、扩大
  assignment、批准 effect、伪造 receipt 或跨 Site 搜索 provider subject。
- 用户报告“工具做了两次”时，Support 以 logicalOperationId/effectKey/canonical receipt 核查；unknown 保持 unknown 并升级。

## 10. State and Recovery Matrix

| Failure/race | Required behavior |
|---|---|
| install commit 成功但 Web timeout | 查询同 assignment command identity；不创建第二条 assignment |
| OAuth provider success、本地 callback timeout | 使用 flow handle/provider query reconcile；不重复 authorize |
| token refresh response lost | 同 refresh identity/query；旧 lease 到期，禁止猜测新 token |
| CapabilityCall claim 后 worker crash | lease/epoch 接管；读取 effect journal，未证明 no-effect 不重发 |
| provider accepted、result timeout | `unknown`；保留 allocation，query/reconcile same identity |
| revoke 与 call 并发 | effect point 比较 epoch；revoke commit 后未提交 effect拒绝，已提交者 truthful finalize |
| assignment upgrade 扩大权限 | 新 consent/approval；旧 revision 继续或被安全撤销，不静默扩权 |
| canary revision 故障 | 停止新 cohort、回滚 future assignments；active/unknown calls按冻结 revision 收口 |
| Catalog/health projection stale | 显示 observedAt/freshness；关键连接/调用动作向 owner read/command，不把 stale 视为 active |
| Rating outage | 结果可 `completed + cost_pending`；usage durable，allocation 不释放，后续 settlement |
| Session disconnect during approval | snapshot 恢复 pending Interaction；过期/已用 grant 不能重放 |
| Routine owner 被移除 | authorization epoch 失效；未来 run暂停，不转移其 user-scoped Connection |
| Secret Manager unavailable | 新 lease fail closed；不从 cache/log/旧 token 绕过；已提交 call按 effect state reconcile |
| package compromise with active Sites | emergency revoke + impact campaign + credential rotation + truthful partial/unknown receipts |

所有 projection 可从 canonical revisions/events/receipts 重建；retention 删除不得移除未完成 reconciliation、财务、审计、legal hold
或 active revoke campaign 所需事实。DR restore 后 epoch/call/effect/usage dedupe identity 保持单调且不回退。

## 11. Notifications、Analytics and Operations

### 11.1 Notifications

至少覆盖 connection created/scope changed/reauth/revoked、new high-risk assignment、permission request、Routine waiting、revision
deprecated/revoked、suspected compromise、unknown resolved 和 settlement correction。安全/财务/待行动通知不受 marketing preference
关闭；delivery unknown 不触发第二次业务 effect。

### 11.2 Product events

```text
capability.catalog.viewed|searched|detail_viewed
capability.assignment.draft_created|published|removed|upgrade_reviewed
capability.connection.started|authorized|tested|active|reauth_required|revoked|unknown
capability.permission.requested|approved|denied|expired|revoked
capability.call.proposed|claimed|submitted|completed|partial|failed_no_effect|unknown|reconciled
capability.usage.observed|rating_pending|settled|corrected
capability.revision.qualified|canary_started|activated|rolled_back|revoked
```

analytics 只包含 Site-local pseudonymous refs、kind/category/risk/revision、status/reason category、latency 和 usage class；不得含
prompt、tool arguments/result、resource name、OAuth subject、token、SecretRef、external identifier 或未脱敏 error body。

### 11.3 Dashboards and alerts

Dashboard 必须按 Site/kind/revision/operation/provider/risk/interactivity 展示 Catalog funnel、connection health、scope drift、call
latency/error/unknown、approval aging、revocation propagation、usage settlement、schema validation、canary guardrail 和 Support volume。

Critical alerts：cross-Site denial anomaly、secret leakage signal、unqualified revision call、revoke 后 effect、unknown aging、duplicate
effect、usage receipt gap、CredentialLease issuance failure、schema/prompt-injection anomaly、canary regression 和 impact campaign overdue。
每项有 named owner、SLO、page route、runbook、safe diagnostic fields 与 resolution receipt。

## 12. Functional Requirements

- FR-CAP-001：Catalog 仅返回 active SiteRelease/Plan/policy 范围内的 listing，private listing 不泄漏存在性。
- FR-CAP-002：详情完整展示 revision、publisher、权限、数据、effect、计费、风险、支持和 qualification freshness。
- FR-CAP-003：Assignment 是版本化 Site-scoped 事实，安装、升级、移除均使用 typed command 和审计。
- FR-CAP-004：Connection 明确 user/workspace scope、provider subject、granted scopes、consent 和 monotonic epoch。
- FR-CAP-005：OAuth/API secret 只进入 Secret Manager；Web、Session、GA、Admin、Support 不得获取明文。
- FR-CAP-006：Platform Admission 编译短期 signed CapabilityGrant；Session/GA 不自行 resolve Site/Plan/Assignment。
- FR-CAP-007：Runtime discovery 仅返回 Grant 允许的 exact typed schema，并冻结 revision。
- FR-CAP-008：高风险 operation 在 effect 前需要 parameter-bound ApprovalGrant，mandatory approval 不可预授权。
- FR-CAP-009：MCP elicitation 维持同一 Call/ExternalCall identity；可能已有 effect 时禁止从头重跑。
- FR-CAP-010：每次 effect 先 durable claim，稳定 identity、retry safety、receipt 和 unknown recovery 必须完整。
- FR-CAP-011：revocation epoch 在 effect point 强制；缓存只用于展示，不得延迟拒绝。
- FR-CAP-012：Capability Runtime 只写 AttemptUsageFact，不报价、不写 Credit Journal、不自行释放 committed allocation。
- FR-CAP-013：Package/revision immutable，permission expansion 必须重新 review/consent，支持 canary/rollback/revoke。
- FR-CAP-014：Chat、Routine、Admin、Support 使用同一 truth 状态但仅拥有各自允许的 projection/commands。
- FR-CAP-015：所有 P0 state 有 owner、deadline、notification、reconcile、projection rebuild、retention 和 DR 行为。
- FR-CAP-016：本 PRD 不授权任何 GA runtime semantic change；发现必须修改 GA 语义时停止并请求用户批准。

## 13. Acceptance Criteria

### AC-CAP-01 — Catalog is not authorization

```gherkin
Given a Capability is visible in the current Site catalog but is not assigned or entitled
When a user or Agent attempts discovery or invocation
Then Admission or Runtime rejects before any credential lease or external effect
And the response reveals no Capability or Connection data from another Site
```

### AC-CAP-02 — Qualification precedes release certification

```gherkin
Given a CapabilityRevision has complete PRD, contract, test and runbook evidence
When a SiteRelease candidate compiles
Then it may consume a valid CapabilityQualificationAttestation for that revision and scope
And ReleaseCertificationInstance is created only after candidate build and preview evidence exists
And neither artifact uses placeholder, self-reference or another Site's digest
```

### AC-CAP-03 — OAuth secret containment

```gherkin
Given a user authorizes an MCP provider through the Site connection flow
When the OAuth callback succeeds
Then credential bytes are written directly to Secret Manager and only an opaque SecretRef is retained
And Web, Session, GA, analytics, logs, Admin and Support never receive the token
```

### AC-CAP-04 — Scope and subject isolation

```gherkin
Given Site A has a Workspace Connection and Site B has the same provider subject
When Site B or a non-member of Site A tries to use Site A's connectionRef
Then the request is denied before discovery, lease issuance or Provider effect
And the response does not reveal whether that provider subject or Connection exists
```

### AC-CAP-05 — Permission expansion requires consent

```gherkin
Given an active revision only reads calendar events
When a candidate revision adds event creation or a broader data scope
Then automatic upgrade is blocked and the exact permission diff is displayed
And no new write operation is granted until required owner consent and approval are committed
```

### AC-CAP-06 — Approval is operation-bound

```gherkin
Given a user approves one email send to one recipient with a frozen parameter digest and cost ceiling
When the Agent requests another recipient, modified body, later Run or higher count
Then the old ApprovalGrant is rejected
And a new explicit approval is required before any external effect
```

### AC-CAP-07 — Mid-call elicitation cannot replay effects

```gherkin
Given an MCP call may have created an external record before requesting more input
When the elicitation context cannot be resumed or the Provider outcome cannot be queried
Then the same CapabilityCall becomes unknown with a reconciliation owner
And the system does not restart the call or create a second record
```

### AC-CAP-08 — Revocation is enforced at the effect point

```gherkin
Given an Assignment, Connection or Capability revision is revoked while calls are queued
When a queued call reaches the external effect point after the revoke commit
Then epoch validation rejects the effect even if a cache or Run snapshot is stale
And an effect submitted before the commit only finalizes or reconciles under its original identity
```

### AC-CAP-09 — Unknown outcome preserves liability

```gherkin
Given a non-idempotent Provider operation was submitted and the response timed out
When Runtime cannot prove success or no effect
Then CapabilityCall is unknown, its committed allocation is retained and Support shows reconciliation pending
And Retry, Regenerate and reconnect do not create a new external operation
```

### AC-CAP-10 — Usage and price authority remain separate

```gherkin
Given a CapabilityCall completes while Rating is unavailable
When the result is safe to deliver
Then Runtime durably records AttemptUsageFact and the UI shows completed with cost_pending
And Capability Runtime neither calculates customer price nor writes or releases Credit Journal entries
```

### AC-CAP-11 — Routine re-admits every occurrence

```gherkin
Given a published Routine references an active Connection and Capability revision
When its next occurrence starts after a Plan, membership, scope or connection epoch change
Then a new Admission evaluates current eligibility and issues a new bounded Grant and allocation or pauses safely
And no token, approval, Hold or Grant from the prior occurrence is reused
```

### AC-CAP-12 — Canary rollback preserves history

```gherkin
Given a canary CapabilityRevision breaches its guardrail
When an operator rolls future assignment resolution back to the prior qualified revision
Then new eligible calls use the prior revision while existing calls retain their frozen revision and receipts
And unknown calls are reconciled rather than rewritten or replayed
```

### AC-CAP-13 — Support is not an authority bypass

```gherkin
Given a user asks Support to reconnect, broaden access or mark an unknown call successful
When Support opens the case timeline
Then only safe status, freshness, owner and approved recovery commands are available
And Support cannot view secrets, approve effects, mutate assignment truth, settle usage or fabricate receipts
```

### AC-CAP-14 — Compromise campaign is truthful

```gherkin
Given an active package revision is found compromised across multiple Sites
When emergency revoke commits
Then new effects are denied and a durable impact, notification and credential-rotation campaign begins
And partial or unknown target receipts remain visible and paged instead of claiming complete remediation
```

### AC-CAP-15 — Session reconnect does not duplicate approval

```gherkin
Given a browser disconnects while a Capability approval is pending or being consumed
When it reconnects through snapshot and SSE
Then it observes the canonical Interaction and ApprovalGrant consumption state
And it cannot submit the same approval twice or replay the CapabilityCall from client events
```

### AC-CAP-16 — Dynamic discovery remains bounded

```gherkin
Given a large MCP server exposes dynamic tools or changes a schema during a Run
When the Agent performs discovery and selects an operation
Then Runtime returns only Grant-allowed tools and freezes the exact qualified revision and typed schema
And later schema changes or server text cannot add scope, destination or permission to that binding
```

## 14. Edge and Negative Test Matrix

| Scenario | Expected result |
|---|---|
| Hidden UI but direct invoke API | deny at owner boundary; no effect |
| unknown/extra manifest field | schema reject; no qualification |
| package digest differs from reviewed digest | signature/provenance reject |
| MCP returns an unexpected tool or schema bomb | bounded validation reject, quarantine health signal |
| endpoint resolves to loopback/private metadata after DNS change | egress/SSRF enforcement rejects every connect/call |
| OAuth state replay or callback bound to other Site | reject without revealing valid flow |
| user-scoped Connection used by Workspace Routine | deny; require eligible Workspace connection |
| member removed while approval dialog open | subject epoch invalidates approval before effect |
| approval double-click/out-of-order response | one CAS consume; duplicate gets canonical state |
| tool returns secret in result/error | redact/quarantine by field policy; never stream/log raw value |
| provider rate limit with safe idempotent read | bounded retry under frozen policy; usage dedupe |
| non-idempotent write timeout | unknown; query/reconcile, no blind retry |
| revoke arrives during CredentialLease | effect point epoch check rejects post-commit use |
| canary and active revision both receive same logical operation | deterministic assignment; effect identity prevents duplicate |
| old Run resumes after revision retired | frozen revision may only continue if policy permits; otherwise safe stop/segment |
| Connection test mutates external resource | qualification failure; test probe must be declared and non-destructive |
| Rating callback duplicated/late | stable usage identity, append-only correction, no double charge |
| projection rebuild loses `unknown` marker | contract/DR test fails; source receipt remains canonical |
| two Sites use identical namespace/connection input | namespace issuance/reference validation rejects collision/leakage |
| Support searches raw external account ID | command unavailable; only Site-safe correlation refs accepted |
| Routine needs interactive mandatory approval | waiting action/pause, never silently preapprove |

Required verification suites:

- schema/contract：TS/Python generated fixtures、unknown fields、revision mismatch、typed discovery、compatibility。
- security：OAuth state/PKCE/redirect、CSRF/SSRF/DNS rebinding、secret leak scanning、scope escalation、cross-Site/subject negative。
- concurrency：duplicate install/callback/approval/call、epoch race、lease takeover、late response、cancel/revoke race。
- effect recovery：no-effect retry、idempotent same-key replay、non-idempotent unknown、query/reconcile、irreconcilable outcome。
- commercial：allocation conservation、usage dedupe、Rating outage、cost_pending、late settlement/correction。
- package ops：malicious package、permission diff、canary regression、rollback、emergency revoke、impact campaign partial/DR restore。
- surfaces：Chat snapshot/SSE reconnect、Routine every-occurrence Admission、Admin maker-checker、Support least privilege。
- UX/a11y/i18n：keyboard/screen reader/focus、safe diff、long scope list、mobile truncation、locale/RTL、Provider redirect return。

No-Go：未 Qualification 调用；secret 出边界；跨 Site/subject 使用；安装即永久授权；静默权限扩大；通配 approval；
unknown 自动重试；Capability 自行定价/改账；Admin/Support 直改真相；只靠 UI 隐藏；revoke 后新 effect；未绑定 owner/runbook/
dashboard/evidence 的 SiteRelease activation。

## 15. Dependencies、Risks and Milestones

### 15.1 Dependencies

| Dependency | Owner | Required evidence |
|---|---|---|
| Launch Profile、Qualification、ReleaseCertification | Site/Release | active revision、digest DAG、negative compile |
| Identity/Workspace/Membership | Identity/Workspace | role、subject generation、removal epoch、cross-Site denial |
| Plan/Credit/Usage | Commerce/Credit | entitlement、allocation conservation、rating/settlement/correction |
| Session Interaction/SSE | Session | proposal lifecycle、snapshot/replay、single consumption |
| GA immutable skill/call port | Agent | boundary compatibility evidence；无语义变化 |
| Secret Manager/OAuth adapters | Security/Capability | containment、rotation、revoke、DR and provider matrix |
| Trust/Policy | Trust | input/output/tool-result policy、restriction epoch、safe explanation |
| Routine | Automation | per-occurrence Admission、waiting action、connection invalidation |
| Admin/Support | Operations | command matrix、JIT access、queue/SLA/runbook |
| Projection/Event/DR | Data/SRE | rebuild、retention、epoch monotonicity、effect/usage dedupe |

### 15.2 Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| 一个 `enabled` 再次吞并多层授权 | high | critical | 独立对象/状态/API、negative contracts、UI wording gate |
| MCP 动态 schema 或 prompt injection 扩权 | high | critical | qualified manifest、bounded discovery、typed freeze、runtime policy |
| OAuth provider 差异导致错误恢复 | high | high | adapter capability matrix、stable flow、query/reconcile、unknown |
| package supply-chain compromise | medium | critical | signed immutable package、SBOM、canary、live revoke、impact campaign |
| 过度确认造成用户疲劳 | medium | high | risk-tier policy、准确 once/run/bounded scope、可解释 diff；不放宽 mandatory gate |
| revoke 传播竞态 | medium | critical | monotonic epoch + effect-point validation + alert |
| usage 与 effect 去重 identity 漂移 | medium | critical | canonical logicalOperation/effect/attempt IDs 和 cross-owner fixtures |
| GA 适配被误当作可自由重构 | medium | critical | `gaRuntimeSemanticChangeAuthorized=false`；需变更立即停下对齐 |
| Support 为解决投诉越权 | medium | high | safe projection、typed recovery commands、JIT/SoD/audit |

### 15.3 Milestones and gates

1. Product review：Catalog、Assignment、Connection、Consent、Approval、Call、Routine 和 Support journeys签署。
2. Architecture child spec：owners、contracts、state machines、SecretRef/CredentialLease、effect/usage identity、RPC/event、migration。
3. Security/Privacy/Trust review：OAuth、custom endpoint、data classes、retention、secret containment 和 abuse cases。
4. QA review：AC/negative matrix、provider adapter certification、two-Site isolation、DR/rebuild 和 24h soak。
5. User approval：只有完整设计包批准后才能进入 `writing-plans`；涉及 GA runtime semantic change 单独批准。
6. Implementation waves：Control Plane/Catalog → Connection/Secret → Runtime/Interaction → Usage/Operations → Site canary/launch。

本文当前仅供内部评审，不授权实现。任何 graph/assembly/prompt/tool/skill/MCP 装配、checkpoint、Handoff、effect journal、
HITL、cancel/terminal/event ordering 或 namespace 语义变化，必须停止并取得用户明确批准。

## 16. Open Review Questions

- [ ] Capability/Product：V1 首发官方 Skill/MCP 清单、risk tier 和每项 owner 是否冻结？
- [ ] Security/Privacy：首发 OAuth Provider、custom endpoint policy、Secret Manager、retention/residency matrix 是否批准？
- [ ] Commerce：每个 operation 的 featureKey、estimate/ceiling、allocation 和 Rating evidence 是否冻结？
- [ ] Agent/Session：当前 immutable Skill read 与 MCP call/interaction contract 是否可无 GA 语义变化满足本文？
- [ ] Automation：哪些 operation 可 `bounded_routine_revision`，哪些必须每次 interaction 是否冻结？
- [ ] SRE/Support：unknown/revoke/compromise queue、deadline、page、runbook 和 irreconcilable policy 是否可演练？
- [ ] QA/Release：两 Site、两 subject、permission upgrade、revoke race、unknown effect、canary rollback 和 DR evidence 是否批准？

## 17. Related Documents

- [PRD-00 Launch Profile 与 Journey Contract](2026-07-25-prd-00-launch-profile-and-journey-contract.md)
- [PRD-03 Account、Plan、Redeem 与 Credit](2026-07-25-prd-03-account-plan-redeem-and-credit.md)
- [PRD-05 Chat Conversation、Run 与 Interaction](2026-07-25-prd-05-chat-conversation-run-and-interaction.md)
- [PRD-10 Admin Operating Console](2026-07-25-prd-10-admin-operating-console.md)
- [PRD-11 Support、Recovery 与 Appeals](2026-07-25-prd-11-support-recovery-and-appeals.md)
- [PRD-A4 Routine、Connector 与 TaskView](2026-07-25-prd-a4-routine-connector-and-taskview.md)
- [Platform/Web/Session Target Architecture](2026-07-25-platform-web-session-target-architecture-design.md)
- [Platform/Web/Session P0 Contract Closure](2026-07-25-platform-web-session-p0-contract-closure-design.md)
- [Capability Control、Runtime、Connection 与 Effect](2026-07-25-capability-control-runtime-connection-effect-architecture-design.md)
- [Execution Budget Allocation Protocol](2026-07-25-execution-budget-allocation-protocol-design.md)
- [Session HTTP/SSE Production Transport](2026-07-25-session-http-sse-production-transport-design.md)
- [Capability Hub 正式册](../../kokoro-handbook/technical/22-capability-hub.md)
- [Skill Hub 与 MCP Hub 产品手册](../../kokoro-handbook/product/06-skill-hub-and-mcp-hub.md)

## 18. Revision History

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-07-25 | 首版；闭合 Skill/MCP Catalog、Qualification、Assignment、Connection、Consent、Runtime、Usage 与运营恢复 |
