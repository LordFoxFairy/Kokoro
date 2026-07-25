---
artifact: product-requirements-document
prdId: PRD-A2
version: "1.0"
created: 2026-07-25
status: internal-review-active
scope: execution-target-device-pairing-trust-assignment-selection-lease-permission-approval-takeover-revoke
accountableProductRole: Agent Product Lead
mandatoryCosigners: [Execution Runtime, Device Security, Identity, Platform, GA Owner, Accessibility, Support, SRE, QA]
engineeringOwner: team:execution-target-engineering
qaOwner: team:execution-target-quality
supportOperationsOwner: team:execution-target-operations
namedOwnerAssignmentStatus: assigned-team-responsibility-ids
implementationAuthorized: false
gaRuntimeSemanticChangeAuthorized: false
---

# PRD-A2：ExecutionTarget、Device、Permission 与 Interaction

## 1. Overview

### Problem

Claude Code/Manus类产品需要在临时云环境、持久云电脑、本地电脑或浏览器执行文件、命令和交互，但“用户登录了”不等于
“Agent可控制设备”。如果Target、Connection、Lease、Permission和Takeover合成一个在线布尔值，断线、旧worker、复制approval、
symlink/worktree变化或多端接管会造成越权和重复effect。

### Solution

建立GA外部的ExecutionTarget产品域：Target是稳定环境identity，Assignment描述Project允许使用什么Target，Connection表示设备
当前channel，Lease决定哪个execution可推进，TargetAuthorization/PermissionDecision约束具体action，Takeover只转移控制权而不
重放动作。所有Action以稳定identity、exact digest、effect receipt和三重epoch收口。

### User stories

| ID | User story | Priority |
|---|---|---|
| TGT-US-01 | 用户可创建、配对并识别自己的cloud/local/browser target | P0 advanced |
| TGT-US-02 | 用户可为Project选择本次Run使用的Target并看到费用、权限和在线状态 | P0 |
| TGT-US-03 | Agent请求文件/命令/浏览器动作时，用户看到exact影响并允许、拒绝或限定范围 | P0 |
| TGT-US-04 | 用户可在另一设备接管交互，不重复已提交action | P0 |
| TGT-US-05 | 用户可暂停、撤销、下线或删除Target，并理解运行中effect的真实状态 | P0 |
| TGT-US-06 | 键盘、屏幕阅读器和移动用户可完成配对、审批、接管和撤销 | P0 |

## 2. Goals、Metrics and Non-Goals

### Goals

1. Target、Assignment、Connection、Lease和Permission各有唯一owner与独立状态。
2. 每个action绑定immutable siteId、Project、TargetRevision、resource set、digest、deadline和permission lease。
3. stale connection/lease/permission任一epoch都不能提交新effect。
4. 用户approval不因参数、path、worktree、network或target变化被扩大。
5. disconnect/revoke/takeover不伪造cancel，也不重放unknown action。
6. cloud/local/browser共享产品语义，adapter能力和sandbox分别认证。

### Success metrics

| Metric | Target |
|---|---:|
| 跨Site/Project/Target grant或channel复用成功 | 0 |
| stale connection/lease/permission epoch提交effect | 0 |
| approval digest变化后仍执行 | 0 |
| disconnect/takeover导致重复action | 0 |
| Target revoke后新effect或credential lease继续可用 | 0 |
| UI显示canceled但本地/Provider effect仍unknown | 0 |
| complete process适用WCAG 2.2 A/AA failure | 0 |

### Non-goals

- ExecutionTarget不是Workspace、Project、Worktree、Deployment、Routine、Job或Device本身。
- 不提供任意远控/RDP、隐藏daemon、永久root shell、bucket-wide credential或跨Site设备共享。
- Worktree是Developer Workspace资源，不是第五种Target kind。
- Target不拥有OAuth/Provider secret明文、Credit、GA checkpoint或Session Message。
- 本PRD不修改GA graph/tool/checkpoint/Handoff/cancel/terminal；只定义外围typed action contract。

## 3. Canonical objects

```text
ExecutionTarget
  immutable siteId / targetId / kind=cloud_ephemeral|cloud_persistent|local_device|local_browser
  owner subject generation / trust+capability profile / lifecycle

ExecutionTargetRevision
  targetId / environment+region / runtime+OS facts / filesystem+network+browser capabilities
  sandbox policy / connector revision / attestation+freshness

ExecutionTargetAssignmentRevision
  immutable siteId / projectRef / targetRef / allowed workloads+actions
  policy+quota+cost refs / assignedBy / effective window / revision

TargetConnection
  immutable siteId / targetRef / device or worker ref / channel identity
  connectionEpoch / observed capabilities / online+freshness / opened+closed

ExecutionTargetLease
  immutable siteId / targetRef / executionRoot+run/job ref
  leaseEpoch / holder workload / scope / issued+heartbeat+expiry / state

TargetAuthorization
  immutable siteId / target+assignment revisions / executionRoot
  allowed action classes+resource bounds / environment+network policy
  authorizationEpoch / issued+expiry / budget allocation ref

TargetActionIntent
  immutable siteId / actionId / target+connection+lease+authorization epochs
  action kind / exact resource set / canonical parameter digest
  cwd/path/worktree revision / deadline / idempotency / expected state

PermissionDecisionRevision
  immutable siteId / action intent / decision=allow_once|allow_bounded|deny
  exact digest+resources / actor+device / auth strength / issued+expiry / consumedAt?

TargetActionReceipt
  actionId / connector outcome / effect certainty / output artifact refs
  started+completed / observed target revision / error+usage refs

TakeoverRevision
  immutable siteId / interaction or control ref / from+to device/session
  reason / expectedVersion / controlEpoch / receipt
```

## 4. Target onboarding and pairing

- Cloud ephemeral按Operation/Run创建并有TTL；persistent target有独立lifecycle、idle/cost和patch policy。
- Local device/browser通过Client Access Plane OAuth grant和device-bound key注册，不共享Site workload secret。
- pairing code短期、single-use、Site/subject/client-bound，不出现在日志/analytics；确认页显示exact Site、设备、capabilities和风险。
- connector只建立outbound authenticated channel，默认不开放公网listen；channel认证不替代action permission。
- capability observation是evidence，不能让device自报“支持shell/root/network”后自动扩权。
- attestation过期、connector低于minimum、安全状态异常时Target restricted；已有effect按certainty收口，新lease/action fail closed。

## 5. Assignment and selection

- Target存在不表示任何Project可用；AssignmentRevision由Project/Platform owner显式创建。
- assignment冻结workload/action classes、data region、network、sandbox、cost/idle、allowed Agent/Profile和effective window。
- Run/Operation提交review显示Target kind/name、online/freshness、filesystem/network、estimated cost、permission mode和fallback policy。
- target selection由用户或published Project default完成；客户端不能传任意targetId绕过Assignment。
- target unavailable时只可等待、reselect并重新Quote/authorize，或按预先认证equivalence选择；submitted unknown action不能fallback。
- local/persistent Target不得因“最近使用”跨Project/Site自动成为default。

## 6. Connection、lease and fencing

- `connectionEpoch`每次reconnect/credential rotation递增；旧channel无法ack新Action。
- `leaseEpoch`每次acquire/takeover/recovery递增；同Target互斥/共享策略由capability profile冻结。
- `authorizationEpoch`在Assignment/permission/restriction/revoke变化时递增。
- connector接受Action前同时验证三个epoch、target revision、action digest、deadline和permission。
- heartbeat丢失只表示holder不再可信，不证明Action未执行；lease recovery先查询receipt/local journal。
- stale holder不能写receipt、Artifact、Usage或terminal；late事实进入owner reducer而非丢弃或重放。
- multi-region writer先fence旧region/epoch；Target不能同时被两个control plane写入。

## 7. Permission and interaction

### 7.1 Action taxonomy

- filesystem：list/read/search、create/edit patch、move/delete（独立风险）。
- command：exact argv/cwd/env classes、timeout、network/sandbox和output budget。
- browser：navigate/click/type/upload/download，绑定origin/frame/selector semantics和credential policy。
- git：status/diff/branch/worktree/commit/push/PR，逐类授权；push/PR不是普通filesystem write。
- secret/credential：只通过non-persistable、audience/resource-bound lease，不显示raw value。

未知action或任意remote code envelope拒绝；不能把shell字符串包装成“generic tool”绕过taxonomy。

### 7.2 Approval UX

- 展示Agent/Run、Target/Project/worktree、action、exact resources、diff/argv、network/secret need、费用和可恢复性。
- `allow_once`原子消费；`allow_bounded`冻结action class、path/origin/resource pattern、max uses/time和deny precedence。
- destructive、credential、external publish、git push、production browser等高风险动作需要fresh step-up或managed policy。
- path、symlink、worktree、argv/env、redirect/origin、target revision或cost ceiling变化使approval失效。
- “approve plan”不批量批准未来未知Actions；每项必须落在可审计bounded policy。
- timeout/关闭页面=未决定，不等于deny/cancel；Run进入waiting_interaction并通知。

## 8. Local filesystem and command safety

- WorkspaceBinding冻结canonical root、repository/worktree revision和symlink/mount policy；effect point重新resolve real path。
- `..`、symlink escape、case-fold/Unicode alias、junction、mount crossing、nested repo与TOCTOU均进入negative matrix。
- read/search遵守ignore、size/binary/secret policy；write只应用canonical patch或typed file operation。
- command使用argv数组而非未解析shell字符串；若需要shell，明确shell/profile并作为更高风险action。
- env默认最小allowlist；credential lease不写workspace、checkpoint、event、log、TaskView或command history。
- output有size/time/redaction budget；ANSI/links/terminal control不可信并安全渲染。
- sandbox/network policy在connector和cloud runtime双重执行；target自报结果只是evidence。

## 9. Takeover and multidevice

- Takeover转移Interaction/control presenter，不改变Run/Action identity、TargetLease holder或GA active state。
- 新设备必须拥有同Site/subject/Project/Task权限并完成所需step-up；旧设备controlEpoch立即失效。
- 已提交Action继续由原Target/connector收口；新设备只attach/query，不重新POST。
- pending approval可在新设备重新呈现exact digest；若approval已消费/expired/事实变化则不可复用。
- 两设备并发决定同Interaction使用expectedVersion/CAS，只有一个canonical Decision；loser刷新结果。
- mobile无法完整展示diff/argv/risk时只允许ack/read/deny，不截断后批准。

## 10. Revoke、offline and lifecycle

- pause阻止新lease/action；revoke推进Target/Assignment/Authorization/Connection epoch并撤销credential leases。
- delete是Data Governance lifecycle：先停止新Assignment，处理active execution、Artifact/receipts、retention和audit，再删除可删配置。
- disconnect/offline不cancel Run/Job；Task显示waiting_target/offline和deadline，用户可等待、rebind或显式新Operation。
- cloud ephemeral TTL只回收证明无committed/unknown action且receipts已durable的环境；否则reconciliation。
- persistent target patch/reboot创建maintenance state；不在active Action中静默更新connector/runtime。
- local device重新上线先re-auth、feature/capability/target revision验证，再resume；不flush未授权offline action queue。

## 11. Cost and usage

- cloud runtime、browser provider、command compute和external capability Usage绑定ExecutionBudget child allocation。
- local device可zero-rated但仍有Usage/receipt/provenance；不因“本地免费”跳过授权和effect identity。
- Target不能计算customer price；Platform冻结Quote/RatingPolicy，Usage producer只写dimensions/evidence。
- unknown action保持committed allocation；revoke/offline/lease expiry不自动refund。
- persistent target idle/storage成本以独立Offering/Operation授权，不从某个Run无限扣费。

## 12. User-visible states

| State | Meaning | Recovery |
|---|---|---|
| unpaired / pairing / ready | 尚未连接、正在配对、可选择 | pair/cancel/select |
| restricted / update_required | trust/capability/release不满足 | update/re-auth/support |
| offline / reconnecting | channel不可用 | wait/reconnect/rebind |
| assigned / assignment_expired | Project可用或已到期 | use/renew/remove |
| lease_pending / leased / lease_conflict | 等待、已占用或冲突 | wait/takeover if allowed/new target |
| permission_required / denied / expired | Action等待或不可执行 | decide/change/re-request |
| action_running / action_unknown | effect进行或结果不明 | observe/query/reconcile；no retry |
| paused / revoked / deleting | 新effect关闭或生命周期处理 | resume if allowed/export/support |

## 13. Admin and support

- Target Console显示safe identity/revision、Assignment、Connection/Lease/Authorization epochs、Action receipts、Usage和lifecycle。
- typed commands：RestrictTarget、RevokeConnection、FenceLease、RebuildTargetProjection、ReconcileUnknownAction、
  RotateConnectorTrust、RetireAssignment、StartTargetDeletionPlan。
- 禁止直接mark online/succeeded/canceled、改Action output/Usage、复制permission、远程执行任意shell或读取用户文件。
- raw output/file/evidence访问需JIT field/action/TTL grant；Support不能扩大permission或接管Target。

## 14. Acceptance criteria

### AC-TGT-01 — Pairing never grants Project actions

```gherkin
Given a local device is paired to one Site and user
When it becomes online
Then no Project, Run, filesystem, command or browser action is authorized without current Assignment and TargetAuthorization
And pairing code or channel identity cannot act as a permission grant
```

### AC-TGT-02 — Three epochs fence stale actors

```gherkin
Given connection, lease or authorization changes while an old worker remains alive
When the worker submits an Action or receipt
Then any stale epoch rejects before effect or authoritative state mutation
And late external facts reconcile without reviving the stale holder
```

### AC-TGT-03 — Approval digest cannot widen

```gherkin
Given a user approved one action, resource set, target and worktree revision
When path resolution, symlink, argv, network, secret, cost or target revision changes
Then the approval is invalid and a new exact decision is required
And no parameter expansion or generic shell wrapper reuses it
```

### AC-TGT-04 — Takeover does not replay action

```gherkin
Given an Action may have executed before the original client disconnects
When another device takes over the interaction
Then it attaches and queries the same Action identity and receipt
And it does not create a new lease, command or Provider effect to obtain an answer
```

### AC-TGT-05 — Revocation is truthful

```gherkin
Given a Target is revoked with submitted and unknown Actions
When revocation propagates
Then no new lease, permission, credential or Action is accepted
And existing effects reconcile without claiming cancellation or automatic refund
```

### AC-TGT-06 — Target unavailable does not silently fallback

```gherkin
Given the selected local or cloud Target becomes unavailable
When a Run needs another Action
Then it waits or requests explicit re-selection and current authorization
And it does not switch environment, copy workspace or execute on Platform/GA hosts implicitly
```

### AC-TGT-07 — Local secret never becomes durable context

```gherkin
Given an Action needs a repository or external-service credential
When a credential lease is issued and consumed
Then the secret is materialized only for the bounded target action and then revoked
And no workspace, checkpoint, event, log, TaskView, Artifact or Support projection contains its value
```

### AC-TGT-08 — Accessible approval is complete

```gherkin
Given a keyboard, screen-reader or mobile user reviews an Action
When the complete exact diff, argv, scope or risk cannot be presented
Then approval remains disabled while safe read/deny/handoff remains available
And no truncated or pointer-only interaction can authorize the effect
```

## 15. Verification and release gates

- identity：pairing/device key/OAuth/Site/subject revoke、connector update和cross-Site channel negative。
- fencing：connection/lease/authorization epoch races、stale worker、multi-region failover、late receipt。
- permissions：action taxonomy、digest/CAS/once、managed deny、TOCTOU、path/symlink/worktree/argv/env/origin/network。
- resilience：offline/reconnect/takeover、unknown local effect、cloud TTL、credential rotation和DR restore。
- UX/a11y：desktop/mobile/CLI/IDE、approval/takeover/revoke、keyboard/screen-reader/reflow和timeout。
- cost：ExecutionBudget slice、local zero-rated evidence、unknown Hold、persistent idle Offering和correction。

No-Go：pairing即授权；Target=Worktree；sharedSite secret；inbound public daemon；generic remote shell；single online flag；
stale epoch写入；approval wildcard；disconnect retry；takeover新建effect；revoke伪造cancel；secret写入durable context；GA持有device identity。

## 16. Related documents and approval boundary

- [Client Access Plane](2026-07-25-client-access-plane-developer-client-design.md)
- [Execution Budget Protocol](2026-07-25-execution-budget-allocation-protocol-design.md)
- [PRD-02 Workspace/Project](2026-07-25-prd-02-workspace-membership-and-project.md)
- [PRD-05 Chat](2026-07-25-prd-05-chat-conversation-run-and-interaction.md)

本文批准不授权实现或设备控制。它不修改GA；GA只能通过已存在/另行批准的typed tool boundary提交TargetActionIntent并接收receipt。
任何tool schema、checkpoint、cancel、terminal、Handoff或namespace变化必须专项与用户对齐。
