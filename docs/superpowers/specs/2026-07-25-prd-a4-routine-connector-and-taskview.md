---
artifact: product-requirements-document
prdId: PRD-A4
version: "1.0"
created: 2026-07-25
status: internal-review-active
scope: routine-builder-trigger-schedule-dst-misfire-concurrency-connector-oauth-wait-notification-taskview
accountableProductRole: Automation Product Lead
mandatoryCosigners: [Automation Runtime, Capability, Identity, Platform, GA Owner, Notification, Accessibility, Support, SRE, QA]
engineeringOwner: team:automation-runtime-engineering
qaOwner: team:automation-quality
supportOperationsOwner: team:automation-operations
namedOwnerAssignmentStatus: assigned-team-responsibility-ids
implementationAuthorized: false
gaRuntimeSemanticChangeAuthorized: false
---

# PRD-A4：Routine、Connector 与 TaskView

## 1. Overview

### Problem

周期任务、webhook和事件触发如果直接保存一段prompt并让cron调用GA，会绕过SiteRelease、Plan/Credit、权限、Connector OAuth、
ExecutionTarget、Trust、等待交互和幂等恢复。浏览器关闭后仍执行的任务还需要用户能看见每次运行、费用、错误、产物和下一动作，
而不是一个长期“running”状态或隐藏daemon。

### Solution

Routine是版本化自动化定义，Trigger/Schedule只负责原子创建RoutineRun；每个RoutineRun随后通过正常Platform Admission创建新的
Run/Operation/Job和ExecutionBudget。Connection/Connector提供可撤销能力，credential仅以短期lease进入effect。TaskView是各真源
事件形成的只读聚合，mutation永远路由回RoutineRun/Run/Job/Interaction owner。

### User stories

| ID | User story | Priority |
|---|---|---|
| AUT-US-01 | 用户可创建一次性、周期、webhook或事件Routine并预览下一次触发 | P0 advanced |
| AUT-US-02 | 用户可选择Project、Agent/Profile、Connector、Target、预算和并发策略 | P0 |
| AUT-US-03 | 用户可查看每次RoutineRun的状态、费用、交互、结果和通知 | P0 |
| AUT-US-04 | OAuth/Target/权限失效时Routine安全暂停并请求修复，不从头重放effect | P0 |
| AUT-US-05 | 用户可暂停、恢复、手动触发、更新或删除Routine，不改写历史Run | P0 |
| AUT-US-06 | Web/CLI/Desktop/Mobile可从同一TaskView查看和继续 | P0 |

## 2. Goals、Metrics and Non-Goals

### Goals

1. Routine定义、Trigger、RoutineRun、Run/Operation/Job、TaskView概念不混合。
2. 每次触发只有一个RoutineRun identity，duplicate/replay不创建第二执行。
3. DST、timezone、misfire、jitter、calendar和并发有冻结且用户可理解的语义。
4. 每次RoutineRun重新Admission；长期定义不持有永久CreditHold、token或permission。
5. Connector/OAuth revoke、waiting interaction和unknown effect可安全恢复。
6. TaskView可重建、不写回真源、不成为万能Task aggregate。

### Success metrics

| Metric | Target |
|---|---:|
| 同trigger occurrence重复RoutineRun/Run/Job/effect | 0 |
| Scheduler直连GA/Provider或写Credit/Session真源 | 0 |
| DST/misfire造成未声明双跑或漏跑 | 0 certification failures |
| Routine长期保存raw OAuth/secret或永久Hold | 0 |
| waiting/reconnect从头重复已完成effect | 0 |
| TaskView mutation或投影被当授权依据 | 0 |
| mandatory notification/interaction丢失仍标完成 | 0 |

### Non-goals

- Routine不是daemon、ServiceInstance、ApplicationDeployment、Job或GA Run。
- 不提供任意cron脚本、未审计webhook代码、inbound local device端口或永久browser automation session。
- 不允许Routine创建Payment、跨Siteeffect、secret export或高风险public publish的预授权旁路。
- TaskView不是业务真源，不拥有状态、budget、permission或`current_task` grant。
- 本PRD不修改GA graph/tool/Handoff/checkpoint/cancel/terminal。

## 3. Canonical objects

```text
Routine
  immutable siteId / routineId / projectRef / owner subject generation / lifecycle

RoutineRevision
  routineId / intent+OperationSpec template / Agent+ModelOption refs
  ProjectContextRevision / Connector+Target assignment refs
  TriggerSetRevision / concurrency+misfire policies
  budget+interaction+notification policies / effective window / revision

TriggerRevision
  immutable siteId / triggerId / kind=once|schedule|webhook|domain_event
  schedule/event/webhook schema / dedupe policy / active window / revision

ScheduleRevision
  timezone IANA ID / local calendar rule / DST gap+overlap policy
  business calendar? / jitter / next-fire algorithm revision / expiry

TriggerOccurrence
  immutable siteId / trigger+revision / occurrenceId / nominal+actual fire time
  source event/webhook identity / dedupe digest / observedAt

RoutineRun
  immutable siteId / routineRunId / routine+revision / occurrenceRef
  state / admission+execution root refs / interaction refs / terminal receipts

ConnectionRevision
  immutable siteId / connectionId / capability+provider account safe refs
  subject/project scope / OAuth grant ref / allowed actions / connectionEpoch / state

TaskViewProjection
  immutable siteId / taskAnchor kind+id / source aggregate refs
  status+progress+interaction+cost+artifact summaries / freshness+watermarks
```

## 4. Routine builder and publish

- draft分step配置intent、Project context、Agent/Profile、Connector、Target、trigger、budget、interaction、notification和retention。
- builder只引用已发布Site inventory/Option/Capability；不接受Provider、raw model、secret、arbitrary workflow或unregistered action。
- preview显示未来occurrences、timezone/DST、misfire/concurrency示例、maximum budget、required Connections/permissions和可能通知。
- publish使用expectedVersion、server validation和maker-checker（高风险/mass/system Routine）；创建immutableRevision。
- 更新Routine创建新revision；已产生RoutineRun始终引用旧revision，新revision只影响未来occurrence。
- pause阻止新RoutineRun，不cancel已启动执行；resume重新计算next fire并按frozen misfire policy处理。
- delete先pause并走Data Governance；历史Run/Usage/Artifact/notification/receipts不删除或重写。

## 5. Schedule、timezone、DST and misfire

- schedule存IANA timezone和local calendar intent，不把server/browser当前offset当长期规则。
- DST gap policy固定`skip|shift_forward|run_at_next_valid`；overlap固定`run_once_first|run_once_second|run_twice`，默认不猜。
- occurrence identity由Routine/Trigger revision+nominal local occurrence+fold/calendar revision确定；时钟回拨不重复identity。
- once trigger有exact instant和expiry；用户timezone显示变化不改authority instant。
- jitter在稳定occurrence identity上deterministic bounded计算，不能跨deadline/blackout/window。
- misfire冻结`skip|run_once_now|catch_up_bounded`和maximum age/count；不允许服务恢复后无界补跑。
- schedule update不回写旧occurrence；near-boundary使用publish cutoff/expectedVersion保证一个revision拥有该occurrence。
- scheduler clock skew、leader failover和region failover通过single writer/fence和dedupe transaction验证。

## 6. Webhook and domain event triggers

- webhook endpoint使用Site/trigger-specific secretRef/signature scheme、timestamp/replay window、size/content-type/schema和rate limit。
- secret不出现在URL、logs或builder；rotation支持overlap/revoke和old-secret negative tests。
- verified webhook先持久化InboxFact，再在同dedupe transaction创建TriggerOccurrence/RoutineRun；HTTP timeout不重复Run。
- domain event只消费owner outbox事实与registered event type/version；TaskView/analytics/projection event不能触发业务effect。
- event filter使用有限typed predicates，不执行用户code/regex DoS/SQL。
- cross-Site event/trigger、late beyond policy、duplicate、out-of-order和poison payload进入typed reject/DLQ/Support，不猜。

## 7. Admission and execution

```text
TriggerOccurrence
→ create one RoutineRun
→ resolve current SiteRelease/Entitlement/Connection/Target/Restriction
→ compile exact Run or OperationSpec from frozen RoutineRevision + occurrence input
→ Quote + user/published policy budget authorization
→ create new ExecutionRoot/root Hold
→ dispatch Run/Operation/Job through normal owner
→ project progress/interaction/cost/Artifact into TaskView
```

- RoutineRun不复用上次Run、Hold、Model authorization、Target permission或Connector credential。
- routine execution input只来自frozen template和validated occurrence fields；webhook不能覆盖Agent/Target/budget/secret/price。
- admission deny/insufficient credit/expiredPlan/Connection/Target形成terminal或waiting state和notification，不silent drop。
- Scheduler只创建RoutineRun，不调用GA/Provider、写Session Message、扣Credit或生成Artifact。
- Retry user action创建明确新manual occurrence/RoutineRun或继续same owner reconciliation；unknown effect不可new run绕过。

## 8. Concurrency policies

每个RoutineRevision选择：

- `forbid_overlap`：active Run存在时新occurrence记`skipped_overlap`或按policy queued，保留receipt。
- `queue_bounded`：按occurrence顺序排队，冻结max depth/age；overflow有typed outcome和notification。
- `allow_bounded`：最多N个active，各自独立ExecutionRoot/Target/budget。
- `replace`：新occurrence请求旧RoutineRun cancel，但只有旧owner canonical cancel/terminal后才按policy启动；不把request当成功。

concurrency decision和RoutineRun创建同一dedupe transaction；多scheduler不能各自看到空位后双跑。unknown/submitted旧effect计active，
不能被replace释放预算或忽略。

## 9. Connector and OAuth lifecycle

- Connection是Site/subject/Project/purpose/action-scoped，不因同email/provider account跨Site复用。
- OAuth使用server-side provider adapter、PKCE/state/nonce（适用）、exact redirect和encrypted secretRef；token不进Web/GA/TaskView。
- Routine publish验证Connection支持required actions，但每次effect仍获取短期CredentialLease并重验connectionEpoch/restriction。
- scope增权、account切换、provider policy、refresh failure或revoke创建新ConnectionRevision/state，不原地偷偷扩权。
- `reauth_required`保存RoutineRun/Action identity和已完成receipts；恢复只推进未执行step，不从头跑。
- connector callback绑定provider tenant/account/event ID→siteId/connection/action；unresolved/mismatch quarantine。
- provider rate limit/outage不自动换另一个用户Connection；fallback必须Definition认证且重新授权。

## 10. Waiting interaction and managed autonomy

- Routine可声明`interactionPolicy=deny_unattended|pause_and_notify|managed_allowlist`。
- unattended只允许预发布managed policy内exact action/resource envelope；managed deny始终优先。
- Payment、secret reveal、cross-Site、security recovery、high-risk publication、rights/consent和unknown retry不能预授权。
- 需要输入/approval/reauth/Target时RoutineRun进入waiting_interaction，冻结owner、deadline、safe prompt和resume token。
- Notification是用户触达，不是Decision；deep link到sameSite currentInteraction并重新auth。
- interaction timeout按policycancel future work/fail/expire；不默认allow，也不回滚已完成effect。
- resume使用sameRoutineRun/Run/Action identities和checkpoint owner；不得重新提交已完成Provider/Connector action。

## 11. TaskView and multidevice

- 每个用户intent只有一个TaskAnchor：Session、Direct Operation、RoutineRun或AgentTeamRun；Routine history中每次Run有自己的anchor。
- TaskView从Run/Job/Artifact/Interaction/Cost/Notification等owner facts异步构建，包含source watermarks/freshness/partial markers。
- mutation endpoint只路由到真实owner并携带ownerRef/expectedVersion；不存在generic UpdateTaskStatus。
- projection丢失可从owner facts/outbox rebuild；rebuild不触发effect或notification delivery。
- Web/CLI/Desktop/Mobile attach同TaskView，使用owner receipt/cursor；attach不新建Run/Hold/Action。
- fork/new run遵循Client Access contract，创建新ExecutionRoot和lineage；不能用来绕过unknown RoutineRun。
- restricted content/secret/PII使用safe projection；跨Site task ID/cursor不泄漏存在性。

## 12. Cost、notification and history

- 每个RoutineRun独立Quote/Hold/Usage/settlement；RoutineDefinition不长期reserve Credit。
- builder可设置per-run ceiling、period guardrail和max concurrent exposure；period guardrail只阻止新Admission，不改余额。
- cost_pending与execution terminal正交；Rating outage不阻塞合格Artifact，但Hold保持。
- notifications至少覆盖created/published/paused、run started（可选）、waiting action、failed/partial/unknown、completed summary、
  budget/Connection/Target blocked和schedule expiring。
- mandatory security/financial/action notification不被marketing preference关闭；delivery unknown不重复业务effect。
- history显示RoutineRevision、occurrence/nominal time、admission、execution/cost、Interactions、Artifacts和receipts，可export/delete按policy。

## 13. User-visible states

### Routine

`draft | validating | active | paused | restricted | expired | deleting | deleted`

### RoutineRun

| State | Meaning | Recovery |
|---|---|---|
| triggered / admission_pending | occurrence已接收/资格处理中 | wait/query same identity |
| skipped_misfire / skipped_overlap | 按冻结policy未执行 | inspect/change future revision |
| queued / running | 已排队/执行 | leave/cancel request |
| waiting_interaction / reauth_required / target_required | 需用户/连接/环境 | respond/reauth/select before deadline |
| cancel_requested | owner未确认cancel | wait/query；not canceled yet |
| unknown / reconciling | effect/outcome不确定 | no retry；support/reconcile |
| completed / partial / failed / canceled / expired | canonical terminal | inspect result/new manual occurrence |
| cost_pending | execution可terminal、费用未最终 | wait/view receipt |

## 14. Admin and support

- Automation Console显示Routine/Revision/Trigger/Occurrence/RoutineRun/Connection/Interaction/TaskView freshness和cost safe timeline。
- typed commands：PauseRoutine、RestrictTrigger、RebuildScheduleProjection、ReconcileTriggerOccurrence、RequeueDefinitelyNotStarted、
  ReconcileUnknownRoutineRun、RevokeConnection、RetryTaskProjection、ExpireWaitingInteraction。
- 禁止直接mark completed/canceled、改next fire跳过receipt、重发webhook、复制OAuth token、改Usage/Credit或直接调用GA。
- mass pause/restrict、Connection revoke和schedule migration使用dry-run/maker-checker/per-item receipt。

## 15. Acceptance criteria

### AC-AUT-01 — Trigger replay creates one RoutineRun

```gherkin
Given scheduler, webhook or event delivery repeats the same occurrence
When trigger intake processes duplicates concurrently
Then exactly one TriggerOccurrence and RoutineRun identity commits
And no second Run, Operation, Hold, Connector or Provider effect is created
```

### AC-AUT-02 — DST behavior is explicit

```gherkin
Given a local schedule falls in a DST gap or overlap
When next occurrences are calculated and fired
Then the published gap/overlap/fold policy determines exact occurrence identities
And clock rollback, leader failover or timezone display cannot create an undeclared second run
```

### AC-AUT-03 — Scheduler never executes business work

```gherkin
Given a valid occurrence is due
When Scheduler handles it
Then it only persists the occurrence and RoutineRun for Platform Admission
And it never calls GA, Provider, Connector, Credit or Artifact owner directly
```

### AC-AUT-04 — Every run has new current authorization

```gherkin
Given Plan, Credit, SiteRelease, Connection, Target or restriction changed after the prior run
When the next occurrence is admitted
Then current facts produce a new ExecutionRoot, Hold and bounded grants or a visible blocked state
And no token, permission, budget or model authorization is reused from the prior run
```

### AC-AUT-05 — Reauth resumes without replay

```gherkin
Given a Connector action completed before OAuth refresh later failed
When the user reauthorizes
Then the same RoutineRun and action receipts resume at the next unfinished step
And completed external effects are not rerun from the beginning
```

### AC-AUT-06 — Replace does not fabricate cancel

```gherkin
Given an old RoutineRun has a submitted or unknown effect
When a new occurrence arrives under replace policy
Then replacement waits for canonical cancel/terminal or follows the published conflict policy
And the old budget, effect and output are not discarded or reused
```

### AC-AUT-07 — TaskView is rebuildable and read-only

```gherkin
Given TaskView loses events or is rebuilt from zero
When owner facts and outboxes replay
Then the same status, interaction, cost and Artifact navigation converges without effects
And no mutation writes a generic Task state instead of routing to the real owner
```

### AC-AUT-08 — Waiting interaction is accessible and safe

```gherkin
Given an unattended Routine requires a decision not covered by managed policy
When it pauses and notifies the user
Then every supported client can present exact scope, deadline, cost and safe choices accessibly
And timeout, notification failure or browser closure never defaults to allow
```

## 16. Verification and release gates

- schedule：IANA timezone、DST gap/overlap/fold、jitter、misfire/catchup、clock skew、leader/region failover。
- trigger：webhook signature/replay/rotation/size/schema、event duplicate/out-of-order/late/DLQ和cross-Site。
- concurrency：forbid/queue/allow/replace、atomic slot、unknown active、cancel race和bounded backlog。
- auth：Connection/OAuth scope/refresh/revoke/callback mapping、CredentialLease、Target/permission和Site isolation。
- recovery：waiting/reauth/offline/unknown、projection rebuild、notification outage、Rating outage和DR restore。
- UX/a11y：builder/preview/history/interaction/TaskView在Web/CLI/Desktop/Mobile、locale/RTL和WCAG A/AA。

No-Go：cron直连GA；Routine永久Hold/token；trigger重复Run；DST猜测；无界catchup；webhook覆盖Agent/budget；replace=cancel成功；
reauth重跑；TaskView写真源；notification=approval；unattended高风险allow；Connection跨Site；Analytics/event projection触发effect。

## 17. Related documents and approval boundary

- [Client Access Plane](2026-07-25-client-access-plane-developer-client-design.md)
- [PRD-A2 ExecutionTarget](2026-07-25-prd-a2-target-device-permission-and-interaction.md)
- [Execution Budget Protocol](2026-07-25-execution-budget-allocation-protocol-design.md)
- [PRD-15 Notification/Data Rights](2026-07-25-prd-15-notification-preferences-and-data-rights.md)

本文批准不授权实现、创建真实Routine或Connector。Scheduler/Automation所有变化保持在Platform/Job/Capability/Session projection边界；
任何GA graph/tool/Handoff/checkpoint/cancel/terminal/namespace修改必须专项与用户对齐。
