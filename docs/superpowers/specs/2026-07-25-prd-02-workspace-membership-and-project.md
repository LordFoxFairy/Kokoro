---
artifact: product-requirements-document
prdId: PRD-02
version: "1.0"
created: 2026-07-25
status: internal-review-active
scope: workspace-membership-invitation-billing-account-project-lifecycle
accountableProductRole: Identity & Collaboration PM
mandatoryCosigners: [Security, Privacy, Commerce, Support, Web, Workspace Engineering, QA]
engineeringOwner: team:workspace-engineering
qaOwner: team:workspace-quality
supportOperationsOwner: team:workspace-support-operations
namedOwnerAssignmentStatus: assigned-team-responsibility-ids
implementationAuthorized: false
---

# PRD-02：Workspace、Membership 与 Project

## 1. Overview

### 1.1 Problem Statement

Kokoro 不能继续把 User ID 当作 Workspace、BillingAccount、Project 或 GA namespace。即使首发只有个人用户，
Commerce、Artifact、Session、未来协作和 Developer Workspace 都需要稳定的权限/计费/作品容器。若只建表
而不冻结 bootstrap、邀请、角色、所有权和删除旅程，将出现孤儿 BillingAccount、最后 Owner 被移除、Project
跨计费主体漂移以及跨 Site 邀请泄漏。

### 1.2 Solution Summary

每个 Site-local User 激活时创建 personal Workspace、Owner Membership、BillingAccount、默认 Project 和
opaque ExecutionSpace mapping。协作作为 `if-enabled` Surface，在同一模型上增加邀请和成员生命周期；不开
第二套 Team 账户。Project 是用户可见作品/会话容器，ExecutionSpace 是 Platform 到 GA namespace 的映射，
二者与物理 ExecutionTarget 分离。

### 1.3 Users

- Personal user：管理自己的 Project、Session、Artifact 和套餐积分。
- Workspace Owner/Admin/Member/Viewer：在启用协作的 Site 中共享资源。
- Site/Platform Commerce Operator（OperatorPrincipal）：查看 BillingAccount 权限与来源，不直接修改账务；其权限
  只来自 OperatorCommandMatrix，绝不来自 Membership role。
- Support/Data Governance：处理邀请、所有权、删除和保留问题。

### 1.4 User Stories

| ID | User story | Priority |
|---|---|---|
| WS-US-01 | 新用户验证后自动得到可用的个人 Workspace、BillingAccount 和首个 Project | P0 |
| WS-US-02 | 用户可以创建、重命名、归档、恢复和删除 Project | P0 |
| WS-US-03 | Owner 可以安全邀请、撤回、重发、改角色和移除成员 | P0 if-enabled |
| WS-US-04 | 最后一个 Owner 不会因离开或误操作让 Workspace 失去管理者 | P0 if-enabled |
| WS-US-05 | 用户在 Site A/B 使用相同邮箱时，Workspace 和邀请完全独立 | P0 |
| WS-US-06 | 删除/离开时运行中任务、作品、账务和 LegalHold 有确定处理 | P0 |

## 2. Goals、Metrics 与 Non-Goals

### 2.1 Goals

1. 每个 active User 都有且仅有一个有效 personal bootstrap result。
2. Workspace 是权限主体，BillingAccount 是计费主体，Project 是用户内容容器，ExecutionSpace 是 opaque
   runtime mapping；四者不互相冒充。
3. 协作邀请、角色、所有权和删除全程 Site-scoped、可审计、可恢复。
4. 任意 membership 变化在所有 API、cache、active client 和新 Admission 上及时生效。

### 2.2 Success Metrics

| Metric | Target |
|---|---:|
| active User 缺 personal Workspace/BillingAccount/default Project | 0 |
| duplicate personal bootstrap | 0 |
| last-owner violation | 0 |
| 跨 Site invite/account/project 泄漏 | 0 |
| invite 接受后首次共享操作成功率 | ≥ 99.5% |
| membership revoke 到新受保护请求拒绝传播 | p99 ≤ 30s，Critical revoke 可实时 epoch 覆盖 |
| Project lifecycle mutation 重复/丢失 | 0 |

### 2.3 Non-Goals

- V1 不支持跨 Site Workspace、Membership、Project 或 Credit 共享。
- 不把 email domain 自动当组织所有权；企业 domain claim/SCIM/SAML 属于后续独立能力。
- V1 不支持把 Project 直接 move 到另一 Workspace；使用显式 export/import/clone 后续方案。
- 不在 Workspace role 中编码每个 Product Feature；Entitlement 与 SiteRelease 仍独立。
- 不把 Worktree、ExecutionTarget 或 GA namespace 暴露为用户可编辑 Project identity。

## 3. Product Model and Ownership

| Object | Product meaning | Owner |
|---|---|---|
| Workspace | 权限、协作和资源归属主体 | Platform workspace module |
| Membership | User 在 Workspace 中的角色和状态 | workspace module |
| Invitation | 加入某 Site-local Workspace 的单次意图 | workspace module |
| OwnershipTransfer | last-owner 安全的显式转移流程 | workspace module |
| BillingAccount | Commerce/Credit 计费主体；V1 每 Workspace 一个 active default | Commerce module；Workspace 只拥有 immutable default binding |
| Project | Session、Asset、Artifact、默认产品设置的用户可见容器 | workspace module |
| ExecutionSpace | Project 到 opaque namespace 的逻辑执行隔离 mapping | workspace module |

V1 明确采用 Workspace-wide Project access：所有 active Membership 按 role 获得 Workspace 内全部 Project 的固定
权限矩阵，不存在隐式或临时 Project ACL。若 Site 需要 Project 子集授权，必须先发布版本化
`ProjectAuthorizationPolicyRevision` 与 assignment，并纳入 Profile、Admission、Support 和删除验收；发布前
不得使用未定义的“获授权 Project”。其他 Context 只保存 opaque refs。Session/Artifact/Job/Developer Workspace
不自行查询 Workspace 表决定权限；最终 mutation 通过 RequestSecurityContext 和 owner API 重新验证
membership/authorization revision。

## 4. Personal Bootstrap

### 4.1 Trigger and transaction

Email verification 或被批准的 OAuth first-login 使 User 进入 active 时，同一 PlatformUnitOfWork：

```text
activate User
→ create PersonalWorkspace
→ create Owner Membership
→ create BillingAccount
→ create Default Project
→ create ExecutionSpace with opaque namespace
→ write bootstrap idempotency receipt + Outbox
```

任一步失败全部回滚；verification token 不被消费成“账号已验证但无 Workspace”的半状态。重试同一 activation
identity 返回相同 bootstrap refs。Commerce 是 BillingAccount aggregate/status 唯一 write owner；PlatformUnitOfWork
只通过 identity/workspace/commerce transaction-scoped interface 协调。以
`(siteId,userSubjectGeneration,bootstrapKind)` receipt，以及 personal Workspace、active owner Membership、default
BillingAccount、default Project、Project ExecutionSpace 的数据库唯一约束，保证 email verification/OAuth 并发只
产生一份完整结果。

### 4.2 First experience

- 默认 Workspace/Project 名称使用 Site locale 安全生成，用户可立即重命名。
- 首次进入展示 Site Profile 对应的 Chat/Studio onboarding，不展示“组织设置”噪音。
- bootstrap 正在恢复时显示 `workspace_preparing`，客户端只查询同一 receipt，不创建第二套资源。
- personal Workspace 不允许删除最后 Owner；账户删除走 Data Governance，而不是普通 leave。

## 5. Collaboration Surface（if-enabled）

### 5.1 Roles

首批角色：

```text
owner   全部 Workspace 管理、所有权转移和删除请求
admin   成员/Project 管理，不可转移所有权或执行 owner-only 财务动作
member  创建和修改获授权 Project 内容
viewer  只读获授权内容，不发起计费执行
```

Billing、Finance、Support 等后台权限不塞进 Membership role；它们属于 OperatorCommandMatrix。未来细粒度
Project permission 通过版本化 policy 添加，不修改角色历史语义。

### 5.2 Invitation lifecycle

```text
draft → pending → accepted
             ├→ declined
             ├→ expired
             ├→ revoked
             └→ superseded
```

- Invitation 绑定 Site、Workspace、normalized target email/identity hint、role、inviter、expiry、single-use token
  digest 和 redirect intent；邮件/链接/品牌全部 Site-bound。
- 对未注册邮箱，接受流程先完成同 Site 注册/验证，再回到原邀请；不自动关联其他 Site User。
- 同 Workspace/email/role 的有效邀请重发复用或 supersede 原邀请，不产生无限有效 token。
- API/错误不得泄漏目标邮箱是否在其他 Site 注册。
- Workspace seat/Plan policy 在创建邀请和接受时都重新校验；邀请存在不保证最终可接受。

### 5.3 Membership lifecycle

```text
active ↔ role_change_pending
active → removal_pending → removed
active → left
```

- role change/removal 使用 expectedVersion、reason、step-up policy 和审计。
- 不能移除/降级最后 Owner；Owner leave 前必须完成 OwnershipTransfer 或删除 Workspace workflow。
- Membership removal commit 是授权线性化点：commit 后所有新 Admission、AuthorizationSegment、ModelAttempt、
  CapabilityCall、ChildRun、JobAttempt 和 Artifact publish 必须因新的 `membershipAuthorizationEpoch` 被拒绝；
  仅线性化点前已不可逆提交的 Provider effect 可以完成、记录 Usage 并结算。缓存传播 p99 ≤ 30s 只用于读投影
  刷新，不得延迟写命令或副作用点拒绝。移除成员不伪造 Run/Job terminal；unknown effect 只 reconcile，不重试。
- 结果访问按当前 Membership 与 retention policy 判断；被移除用户不能读取最终 Artifact，除非独立导出/法定
  权利明确授权。

### 5.4 Ownership transfer

```text
requested → recipient_pending → accepted → completed
          ├→ declined/expired/canceled
          └→ failed
```

发起者和接收者均需 recent re-auth；接收者必须是 active member。高风险/企业策略可要求 maker-checker。
completed 在一个 UoW 中新增 recipient owner、降级/保留原 owner、写 expectedVersion/audit/outbox，任何失败不
产生无 Owner 窗口。所有 leave/remove/role-change/transfer/delete 命令锁定同一 Workspace ownership aggregate
或使用同一 `ownershipVersion` CAS，并在提交约束验证 `activeOwnerCount >= 1`；并发 loser 返回
`VERSION_CONFLICT` 并重新 preview，不能依赖缓存计数或异步补偿。

## 6. Project Lifecycle

```text
active ↔ archived
active/archived → deletion_pending → retained | deleted
```

### 6.1 Core actions

- Create：选择 Workspace，按 Profile 赋默认设置和独立 ExecutionSpace；幂等 key + body digest。
- Rename：不改变 namespace、Session、Artifact 或 URL identity。
- Archive：阻止新默认入口，可继续读取；running Run/Job 不自动取消。
- Restore：重新验证 Workspace、Site/Profile 和 retention，不恢复已撤销权限。
- Delete：先 preview 影响并 re-auth；创建 Data Governance participant request，不直接级联删表/Blob。
- `RequestProjectDeletion` commit 推进 Project deletion epoch，并立即拒绝所有新 Session、Admission、Operation、
  Share、Routine 和 Connector binding。已开始 effect 仅按冻结 deletion policy 完成 finalization、Usage 与
  Artifact retention；旧 tab、缓存或旧 grant 不能产生新 participant 漏项。

### 6.2 Project settings

Project 可以保存用户可见默认 Agent/ModelOption、locale、Studio 参数和 context refs，但每次 Run/Operation 仍
由当前 SiteRelease/Entitlement/Risk Admission 重新授权。Project setting 不是 permission 或 pricing authority。

### 6.3 Delete and retention

Delete preview 至少列出 Session、active Run/Job、Artifact/Share、Routine、Connection、SupportCase、LegalHold
和导出状态。存在 active operation 时由冻结 `ProjectDeletionPolicyRevision` 决定 wait/cancel/finalize，不能临场
选择。SupportCase、Audit、Usage、Journal、Payment/Redemption 与 LegalHold 不是 Project-owned 可删资源；各
领域 participant 只返回 retain/deidentify/unlink/GC receipt，coordinator 不直接级联删表或 Blob。执行期间新增
LegalHold 或 participant epoch 时必须暂停并重编译计划，不能沿旧计划继续不可逆删除。

## 7. BillingAccount and Commerce Rules

- BillingAccount 属于一个 Site-scoped Workspace；V1 一个 active default，不能在 UI 随意切换 liability。
- Subscription、Entitlement、Credit、Payment/Redemption facts 引用 BillingAccount 和 origin Site。
- Membership role 不直接授予消费权；execution admission 同时检查 Project permission、BillingAccount policy、
  Entitlement 和 budget。
- Owner transfer 不转移法律交易事实；它改变 Workspace 管理权，历史 actor/source 永久保留。
- Workspace 删除前必须先处理 Subscription renewal、Payment/Dispute、Credit liability 和 RecoveryCase。

## 8. User-visible States and Recovery

| Surface | States | Recovery/CTA |
|---|---|---|
| personal bootstrap | preparing、ready、failed_recovering | 自动查询同 receipt；达到 SLA 后创建 SupportCase |
| invitation | pending、accepted、declined、expired、revoked、membership_conflict | accept/decline、request resend、sign in/register、Support |
| membership | active、role_change_pending、removal_pending、removed | refresh authorization、contact owner、appeal/support |
| ownership transfer | recipient_pending、completed、declined、expired、failed | accept/decline/cancel/retry same identity |
| Project | active、archived、deletion_pending、retained、deleted | archive/restore/cancel deletion（窗口内）/export/support |

内部 authorization propagation、outbox 或 deletion participant 状态不直接暴露；映射为稳定状态、更新时间和
下一动作。personal bootstrap、ownership transfer 和 Project deletion 的状态必须先登记 UserVisibleStateCatalog
revision；本 PRD 只引用 stateRef，不创建未版本化同义词。

## 9. Admin and Support

- Admin 只能通过 typed Workspace/Identity/Data Governance commands，不直接改 Membership/Project 表。
- Support 可按 Site-scoped User/Workspace/Project refs 查看安全时间线，不通过 email 搜索泄漏其他 Site。
- invitation 误发：revoke/supersede，不删除审计。
- owner 丢失设备：走 Identity recovery + high-assurance OwnershipTransfer/BreakGlass Case，不能数据库改 owner。
- member removal dispute：Case 保存 Evidence 和权限 revision；恢复必须创建新 Membership fact，不改旧 removed。
- manual Project restore 受 retention/LegalHold/Object GC receipt 限制，无法恢复时明确说明。

## 10. Security、Privacy and Abuse

- 所有 link/token 只存 digest，single-use、Site/audience/expiry bound；浏览器自报 workspaceId 不可信。
- Invite/Member list 对普通成员的 PII 按角色最小化；Analytics 不记录完整邮箱。
- rate limit 按 Site、actor、target、IP/device 和失败速度；依赖不可用时高风险邀请/转移 fail closed。
- CSRF/Origin 保护所有浏览器 mutation；ownership/删除/高风险 role change 要 recent re-auth。
- Workspace/Project object key、cache、search index、idempotency 均包含可信 Site/Workspace scope。
- 所有 GA request/manifest/event schema 的负向 contract test 必须断言不存在
  `siteId/userId/ownerId/workspaceId/projectId`；GA 只接收 opaque namespace。Support/Session 投影通过上游
  opaque Run/Job ref 授权解析，既不向 GA 传业务身份，也不向用户或普通坐席显示 namespace。

## 11. Acceptance Criteria

### AC-WS-01 — Atomic personal bootstrap

```gherkin
Given a pending user verifies a valid Site-bound email token
When any bootstrap write fails
Then User activation, Workspace, Membership, BillingAccount, Project and ExecutionSpace all roll back
And retrying the same activation identity creates exactly one complete bootstrap result
```

### AC-WS-02 — Cross-Site invitation isolation

```gherkin
Given Site A and Site B have users with the same normalized email
When Site A sends and accepts a Workspace invitation
Then only the Site A local User can receive Site A membership
And no response reveals whether Site B has that email
```

### AC-WS-03 — Last owner protection

```gherkin
Given a Workspace has one active owner
When that owner tries to leave, remove themselves or become a non-owner
Then the command is rejected with an OwnershipTransfer recovery action
And the Workspace never has zero owners
```

### AC-WS-04 — Member revoke during execution

```gherkin
Given a member has a running Job and is removed
When new Project or Artifact commands arrive
Then they are rejected under the new membership revision
And the existing Job follows its frozen cancel/completion policy without duplicating effects
And result visibility follows current authorization
```

### AC-WS-05 — Safe Project deletion

```gherkin
Given a Project has Sessions, Artifacts, an active Job and a LegalHold
When the owner requests deletion
Then the preview lists affected and retained resources
And no Attempt, Usage, Journal or held data is directly deleted
And completion waits for all mandatory participant and object GC receipts
```

### AC-WS-06 — No cross-workspace billing

```gherkin
Given two Workspaces have different BillingAccounts
When a Project execution is admitted
Then the Hold and Usage settlement reference only the Project Workspace's authorized BillingAccount
And no membership or Project move can silently change liability
```

### AC-WS-07 — Concurrent bootstrap

```gherkin
Given email verification and OAuth first-login concurrently activate the same Site-local subject generation
When both bootstrap commands commit
Then exactly one complete User/Workspace/Membership/BillingAccount/Project/ExecutionSpace set exists
And both callers resolve the same idempotency receipt and refs
And a failed child write leaves no active User or orphan resource
```

### AC-WS-08 — Concurrent last-owner safety

```gherkin
Given a Workspace has exactly two owners
When both concurrently leave, remove or downgrade an owner
Then at most one ownership command succeeds
And the committed active owner count is always at least one
```

### AC-WS-09 — Revoke stops future effects

```gherkin
Given a Run began before Membership removal but has not started its next Model, Capability or Job attempt
When removal commits and advances membershipAuthorizationEpoch
Then the next effect is denied or paused without consuming new Credit
And any earlier unknown Provider effect is reconciled without a second Attempt
```

### AC-WS-10 — Deletion freezes new writes

```gherkin
Given a Project entered deletion_pending
When a stale tab or grant starts a Session, Operation, Share, Routine or Connector binding
Then every new write is denied by the deletion epoch
And SupportCase, Audit, Usage, Journal, Payment/Redemption and LegalHold return retain/deidentify/unlink receipts instead of being deleted
```

### AC-WS-11 — Invitation identity binding

```gherkin
Given an Invitation is bound to Site A, one Workspace, audience and a verified target identity hint
When its token is opened on Site B or by a different signed-in subject
Then Membership is not created and no account existence is revealed
And the user is asked to authenticate the exact Site-local target identity or request a new invitation
```

### AC-WS-12 — New LegalHold invalidates deletion plan

```gherkin
Given a Project deletion plan was compiled
When a new LegalHold or participant epoch appears before an irreversible delete
Then execution pauses and recompiles against the new epoch
And no stale plan deletes the newly retained data
```

### AC-WS-13 — Commerce owns BillingAccount writes

```gherkin
Given Workspace attempts to create or mutate BillingAccount state outside the transaction-scoped Commerce interface
When dependency and authorization gates run
Then the write is rejected
And only the immutable Workspace to default BillingAccount binding may be stored by Workspace
```

### AC-WS-14 — GA identity-negative contract

```gherkin
Given an authorized Project maps to an opaque ExecutionSpace namespace
When a GA request, manifest or event is serialized
Then it contains no siteId, userId, ownerId, workspaceId or projectId
And Support and user projections do not reveal namespace
```

## 12. Analytics and Metrics

Events：personal bootstrap started/completed/failed、Project create/archive/restore/delete、invite sent/accepted/
declined/expired/revoked、membership role changed/removed/left、ownership transfer requested/completed、authorization
denied reason。所有事件 Site-scoped、PII minimized、consent/retention governed。

Product dashboards：bootstrap failure/recovery、invite funnel、time to first shared action、role/removal errors、orphan
resource invariant、last-owner rejection、Project active/archived/deletion aging、Support contact per 1k mutations。
每项 Success Metric 必须引用 `ProductMetricRevision`，包含 numerator、denominator、exclusions、window、
Site/Profile/SurfaceRevision dimensions、event source、owner、guardrail、alert threshold 与 mandatory action。

## 13. Dependencies, Risks and Milestones

| Dependency/Risk | Mitigation |
|---|---|
| Identity activation 与 Workspace UoW 顺序 | Wave 1 Spec 冻结同 Platform transaction 和 idempotency receipt |
| 协作能力阻塞 Core | Reference Profile 只启用 personal bootstrap；invite route/API/Admin 四层关闭 |
| Role 过度粗糙或过度细化 | 首批四角色；新增 permission policy 用 revision，不改历史角色语义 |
| Member removal 与 active effect | restriction/authorization revision + frozen execution policy，不盲 cancel/retry |
| Project 删除跨多个 Context | Data Governance participant workflow + LegalHold/GC receipts |
| Workspace move 引发账务/namespace 漂移 | V1 明确禁止；未来独立 migration/import workflow |

Milestones：Wave 1 交付 personal bootstrap 和 Project lifecycle；协作 Surface 只有进入 Profile 才实现 invitation/
membership/ownership E2E；各后续 Context 在自身 Wave 接入 ProjectRef 和 deletion participant；Wave 7 完成
Admin/Support UAT；Wave 9 profile certification。

本文批准不授权实现。字段、constraint、API、migration、authorization revision 和 cache invalidation 在 Wave 1
architecture child Spec 冻结；不涉及 GA runtime 改动。
