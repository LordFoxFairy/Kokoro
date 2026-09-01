# Session 生命周期

状态：当前产品会话链路，2026-08-23。状态归属见
[ADR-015](../decisions/ADR-015-agent-state-and-feature-context.md)，运行细节见
[42 GA 核心架构](../technical/42-ga-core-architecture.md)，fork/archive/delete 与 workbench/Artifact cleanup 边界见
[ADR-018](../decisions/ADR-018-ga-thread-context-compaction-and-memory.md)。

## Session 保存什么

```text
Session
  immutable tenant_ref + subject / app_key / feature_key / message projection / active run admission / SSE/read model / lifecycle
  Job card projection keyed by JobRef (safe display state, Studio replay cursor, last revision)

not Session
  namespace / thread_id / Agent / prompt / Feature definition / Skill/MCP snapshot / Tool / model provider / sandbox / checkpoint
```

Session 的 `feature_key` 与 immutable `tenant_ref + subject(kind, opaque_ref)` 是已经由 Entry 验证的产品上下文；二者都不是 Agent 选择。
tenant + subject 在创建后不变；每次 Launch 由 IAM/Session 重新确认当前 actor 可代表该 scope，再给出可信的
`ExecutionIdentity(tenant_ref, actor, subject, identity_assertion_ref)`。GA 只在首次 target bootstrap（普通 Launch claim 或 fork `ForkConversation` prepare） 从 tenant + subject 在内部派生并固化 `RuntimeNamespace`；后续新 Launch 用 current identity 验证 ThreadLocator 后复用，Cleanup 用已接受 delete 的 durable tenant-subject lifecycle envelope 验证 locator/fence，已 claim run 仅以 ledger/locator 恢复。GA `ConversationState` 按
`runtime_namespace:session_id` 持久化执行状态；其 DeepAgent 实现为 `DeepAgents native state`，swarm 实现以同键的 official
`SwarmState` 持久化 `active_agent`。

## 一个 Session、一个 ConversationState、一个 active Run

`session_id` 是产品会话 identity；GA 只把同一个值作为 LangGraph `thread_id`。因此，同一 Session 的“复用”是继续读取
同一份 GA checkpoint/state，不是 Session 再存一份 Agent、binding 或 graph 选择。

`run_id` 则是一次执行 identity。它有两种明确路径：

| Session / Run 状态 | 接收到的动作 | Session → GA | Run 与 checkpoint 语义 |
|---|---|---|---|
| 无 active Run，或上一 Run 已 terminal | 正常用户消息 | `LaunchRunRequest` | 分配新的 `run_id`；在同一 `thread_id=session_id` checkpoint 上继续。 |
| allocated、尚未 GA claim | delete / cancel | `ApplyControlRequest(cancel, same run_id)` | GA preclaim-cancel receipt 与 Launch 线性化；cancel 先到则只得到一次 `cancelled_before_claim` terminal。 |
| `running` | 后续普通用户消息 | 不投递 Root command | 返回 `run_active`；不排队、不写 checkpoint，不发送第二个 Launch，不创建第二个 graph/state。 |
| `awaiting_control` | 命中当前 interrupt frame 的 decide/respond/reject/cancel | `ApplyControlRequest` | 保持同一 active `run_id`；只以 native resume 恢复、拒绝或取消当前 HITL frame。 |
| `deleting` / 已删除 | 任意新消息或 control | 不投递 | Session 拒绝输入；先 cancel/await active Run，再 cleanup。 |
| 普通新 Session | 首条正常用户消息 | `LaunchRunRequest` | 新 `session_id`、新 `run_id`、空 checkpoint/workbench；沿用 verified `feature_key` 与 immutable tenant + subject，首次 actor/assertion 重新受理。 |
| `fork_preparing` target | 普通消息 | 不分配 `run_id`，不投递 `LaunchRunRequest` | Session 只重投同一 `ForkConversation(request_id)`；target 未收到 `ForkPrepared` 前不可作为 message-admissible Session。 |
| fork target Session | `ForkPrepared` 后的首条正常消息 | `ForkConversation`，随后 `LaunchRunRequest` | 新 `session_id`、fresh checkpoint/workbench；GA 从 source terminal boundary 写 private `ConversationSeed`，首个 Run 原子消费为 visible-text fresh state。source native state/workbench/HITL/effect 不复制。 |

Session 以原子 admission 保证单 active Run；GA 再用 `runtime_namespace:thread_id` gate 保护 checkpoint 写入。两层一起保证：新
输入既不会和进行中的 graph 并发，也不会因为普通续聊而切换 Agent/模板。

## 生命周期

```text
create
  Entry validates App/Feature/permission + IAM subject admission
  -> Session(feature_key, immutable tenant + subject) -> first LaunchRunRequest(fresh ExecutionIdentity) -> GA bootstrap

terminal continuation
  same feature_key + no active Run -> next user message -> new run_id + same thread_id/checkpoint

active running
  subsequent ordinary user message -> run_active (no Root command or queue)

awaiting native interrupt
  matching decide/respond/reject/cancel -> ApplyControlRequest(same run_id)

HITL
  Session validates current interrupt/control -> ApplyControlRequest(decide/respond/reject/cancel, same run_id)
  -> GA resume or terminate on same checkpoint

new Session
  Session creates a new session_id with product feature_key + immutable tenant + subject
  first new Run -> fresh actor admission -> empty checkpoint/workbench -> entry Agent and default capabilities bootstrap anew

fork
  Session atomically creates target with lifecycle=fork_preparing, writes durable ForkConversation(request_id)
  target ordinary input -> fork_preparing; no run_id / no LaunchRunRequest
  current actor admission -> ForkConversation(source terminal Run, target)
  GA -> target locator + private ConversationSeed from source visible text only -> idempotent ForkPrepared
  Session marks target message-admissible only after ForkPrepared; transport timeout only retries same request_id
  first target Run -> atomically applies seed + new input to a fresh native state; workbench/default capabilities bootstrap anew

archive
  Session changes product visibility/read model only; GA/Storage state remains under its own retention policy

delete / retention expiry
  Session atomically enters deleting / rejects new input -> cancel/await active run
  -> durable CleanupThread(ExecutionIdentity, session_id, cleanup_id, reason)
  -> GA writes ThreadCleanupFence before resolving/removing thread payload
  -> late/replayed Launch -> thread_closed (no namespace/claim/graph)
  -> GA ThreadLocator resolves internal RuntimeNamespace, removes checkpoint/workbench/thread lock
  -> ThreadCleaned ack -> Session tombstones product projection; late GA/Studio events ack/drop
```

同一 Session 带不同 Feature 或不同 subject 的请求创建新 Session，绝不改写原 thread 的产品能力/归属边界。fork 保留原 subject/key，但从 source terminal boundary 由 GA 准备一次性 visible-text `ConversationSeed`；普通续聊不 clone 图，也不重新选择 Agent。`fork_preparing` 只是 target ProductSession 的短生命周期门，不是 Agent 配置、Session selection、graph binding 或新的执行状态：它只阻止 seed 未 durable 前的首个 Launch。若 target 在 `ForkPrepared` 前进入 delete，Session 走同一 CleanupThread 路径；GA 的 cleanup fence 与 ForkConversation 对同一 target 线性化，已关闭 target 不产生 locator、seed 或 Launch。

### Studio Job 卡片：`JobRef` 投影，不是 Agent 状态

GA 的已声明 `CreateJob` effect 以稳定 `effect_id` 调用 Studio `CreateJob` 并得到 opaque `JobRef`；GA durable outbox 只发
`StudioJobLinked(JobRef)`。Session 以 `(session_id, job_ref)` 建立/补全以 JobRef 为键的 card projection，先读 Studio `ReadJobSnapshot(JobRef)`，
再按 `job_ref + event_id` 去重、按 Studio `revision` 只前进地消费/replay安全 `StudioJobEvent`。这使 Job event 与 link 无论先后到达都由
snapshot/replay 收敛为一张卡片。

Studio owns Job、provider、snapshot/event ordering 和 Artifact relation；GA 不订阅状态，也不持有 callback/watcher。Run terminal 后
Studio event 仍可刷新相同 JobRef 的卡片，但不能重开 `active_run_id`、写 assistant 文本、恢复 ConversationState 或产生模型调用。
Session delete/retention 只 tombstone card 与 Job event cursor；Studio Job/Storage Artifact 继续按各自 lifecycle 处理。Feature 的
`detached | request_cancel` 行为是 GA `studio_job_policy`：前者不影响 Job，后者仅以幂等 effect 请求 Studio cancel。

## 恢复与投影

- Session 消息、run projection、SSE cursor 是产品 read model；GA checkpoint、ledger、HITL 和 effect 是执行事实。
- Session 不读取 GA checkpoint，不推断 `active_agent`，不以 Browser 状态重建 Agent runtime。
- Browser 刷新从 Session snapshot/SSE 恢复；Job card 从 Studio snapshot/JobEvent cursor 补齐；worker restart 从 GA durable canonical request/ledger/checkpoint 恢复。
- active Run 的 matching HITL/cancel 以稳定 command identity 幂等处理；`running` 的普通文本不进入 GA，也不重复已结算
  invocation/effect。terminal 后才允许下一条普通消息创建新 Run。
- fork 不复制动态 Skill、workbench、native messages、RunScope、effect journal、HITL、outbox 或 billing identity；它保留 FeatureKey 与 immutable tenant + subject，并由 GA 从 source terminal boundary 的 own request/safe final reply facts准备 private `ConversationSeed`。seed 只含可展示 user/final-assistant text，首个 target Run 原子消费；它不携带 caller history，也不调用 graph/checkpoint clone。
- `CleanupThread` 只以可信 ExecutionIdentity/session identity 与 GA 内部 ThreadLocator 定位 state；GA 先写私有 `ThreadCleanupFence`
  拦住晚到 Launch，再从 `session_id` 派生 LangGraph `thread_id`。它不携带 Agent、Feature、Skill、checkpoint path 或 object key；Storage Artifact 保持 Storage lifecycle，不因会话删除递归清除。
- Session `deleting` 只接收 matching active Run 的 terminal 来推进 cleanup，停止 Browser 投影；`tombstoned` lifecycle row 覆盖
  outbox/Studio/redrive retention。所有晚到 ProductEvent/StudioJobEvent 都 ack/drop，条件 transaction 不得复活消息、Run、card、cursor 或 SSE。

## 验收

```text
Session record 不出现 agent/runtime/capability snapshot/namespace 字段。
同一 Session 的 tenant + subject 不可改变；每个**新 Launch**的 current `ExecutionIdentity.tenant_ref + subject` 必须匹配它，Cleanup 则用已接受 delete 的 durable tenant-subject lifecycle envelope 匹配 locator/fence；项目会话可由不同已授权 actor 继续。
terminal 后的普通续聊创建新 run_id，但持续使用同一 checkpoint；普通 new Session 与 fork 都得到新 ConversationState，fork 的首个 Run 仅以 GA private visible-text seed 初始化它。
active Run 的普通输入、HITL 决定和取消只控制原 run_id，绝不产生第二个 Launch、graph 或 checkpoint writer；未 claim run 只有 cancel 可产生 preclaim terminal。
不同 Feature 不会写入同一 thread。
fork target 在 `ForkPrepared` 前不分配 run_id、不受理普通消息；它只重投同一 ForkConversation。fork 不产生 checkpoint clone：仅 source terminal visible text 经 GA private ConversationSeed 写入 fresh target state；delete 在 active run terminal 后先写 ThreadCleanupFence 再清理 GA state，并以 cleanup_id 幂等；晚到 Launch 不复活 thread，晚到 GA/Studio event 不复活 Session projection。
Session relay 或 Browser 离线不会阻止已有 GA run 恢复。
CreateJob effect 重试只返回同一 JobRef；link/event 反序、重复 Studio event 或 revision 倒退均不产生第二张或回滚的 card；delete 不复活 card/Run。
```
