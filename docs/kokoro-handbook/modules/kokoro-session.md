# kokoro-session 模块边界（历史归档）

状态：**历史迁移材料**，2026-09-01。`kokoro-session` 已从当前拓扑移除；Session 是
`kokoro-bff` 内 Chat 业务边界的资源概念，不是独立仓库或当前运行服务。本页只保留旧原型考古，
不作为当前实现、CI、Docker 或部署依据。当前 Chat 契约见
[`kokoro/docs/integration/chat-bff-contract-v1.md`](../../../kokoro/docs/integration/chat-bff-contract-v1.md)。

本页是根仓对 `kokoro-session` 的模块级说明；实现细节保留在 Root 外的归档副本，
跨仓 wire 契约只认根仓 [`contract/`](../../../contract/README.md)，不再从当前工作区链接已归档子仓路径。

## 定位

`kokoro-session` 是产品会话与交付 facade，不是 Agent runtime。它把浏览器请求转成 Root
`LaunchRunRequest`，向 GA 投递；再把 GA 的安全 `ProductEvent` 投影为历史查询、AG-UI 和 SSE。

当前物理实现仍是 `kokoro-session`（没有独立运行的 `kokoro-chat`）。Root consumer registry
中的 `kokoro-chat` 是待统一的 consumer 名称；Session 现阶段用严格 Redis internal
transport adapter（Root 顶层 `message_id/content` 在 Redis envelope 中位于 `input`），
generated consumer 接入需要和 Root manifest、生成器、CI 同步完成。

```text
Browser / Site
  -> Session + IAM admission
  -> Root LaunchRunRequest
  -> GA Redis ingress
  -> GA chat_messages/chat_events
  -> Session query / authorization / projection
  -> History API + AG-UI/SSE
```

## Owns

- `ProductSession`：`session_id`、`feature_key`、不可变 `tenant_ref + subject` 与生命周期。
- 当前 actor 的 IAM admission，以及 Launch、control、fork、cleanup 的授权闸门。
- 同一 Session 的单 active Run admission；前一 Run terminal 后才接受普通下一条消息。
- Chat facade：history、事件 replay、AG-UI/SSE envelope、cursor 与连接生命周期。
- Studio `JobRef` 的产品卡片投影；Studio Job 与 Storage Artifact 事实归各自 owner。

## Does not own

- Agent、Workflow、Skill/MCP/Tool 组装或执行。
- `RuntimeNamespace`、LangGraph `thread_id`、DeepAgents state、checkpoint、RunLedger、effect。
- GA `chat_messages/chat_events` 的 canonical 写入；Session 只查询、鉴权和投影。
- Capability Skill CRUD/path、Storage bytes/Artifact、Studio Job、Billing 账务。
- Root API/AIP Proto、manifest、字段编号和生成器。

## Session 与 GA 的边界

```text
ProductSession
  session_id
  feature_key
  tenant_ref + subject
  lifecycle

GA
  run_id / CanonicalRunRequest
  RuntimeNamespace (GA 内部派生)
  native state/checkpoint
```

Session 不保存 Agent、Feature 组装、graph、模型、Skill/MCP snapshot 或 namespace selector。
`feature_key` 是产品入口，不是用户可写的 Agent 选择器；GA 依据它取得已装配 Agent。
浏览器和 Session 都不传 `namespace`、`thread_id`、Agent 或 graph 配方。

同一 Session 的普通消息在前一 Run terminal 后创建新的 `run_id`，继续同一 GA native outer
checkpoint。fork 创建新的 Session 和新的 checkpoint/workbench root；GA 只用受限可见文本 seed
初始化，不复制 source checkpoint、native message、Skill mount 或 effect。

## 聊天历史与实时事件

```text
GA chat_messages  -> 用户可见历史唯一来源
GA chat_events    -> 用户可见 replay/live 唯一来源
Session           -> query + authorization + projection
Redis             -> 低延迟 transport，不是长期事实源
LangChain         -> native messages/checkpoint，仅 GA 内部
```

GA 先 durable 写 `chat_events`，再发布 Redis。Session 以 `chat_event_id + seq` 幂等投影；断线、
Redis 清空或 Session 重启时按 `seq` replay，不创建新 Run、不重复 provider invocation。GA
`chat_message_id/chat_event_id` 与 LangChain `Message.id/thread_id/checkpoint_id` 完全分离。

对外只投影安全 `ProductEvent`：`run_phase`、`assistant_delta/final`、`activity`、
`approval_request`、`plan_snapshot`、`artifact_ready`、`studio_job_linked`、`terminal`。
raw thinking、tool args/results、subagent text、sandbox path、object key、prompt 和 secret
永不进入 Session API、AG-UI 或浏览器。

## API/AIP 契约同步

Root `contract/proto` + manifest 是唯一 wire authority。子仓只消费生成物：

```text
Root contract
  -> contract generator
  -> kokoro-session/src/contract/ strict adapter（generated consumer 接入后替换）
  -> Session adapter / projection tests
```

Session 可以维护契约摘录和实现说明，但不得复制 Proto/OpenAPI、修改字段编号或手写平行 DTO。
契约变更先在根仓完成并通过 Root contract gate，再重新生成本仓 consumer；详见子仓
[`docs/session/api-contract.md`](../../../kokoro-session/docs/session/api-contract.md)。

## 与其他 owner 的调用

Session 只通过 public contract 调用 GA、IAM 与 Studio；Capability/Storage 的 Skill 与 Artifact
运行时调用归 GA，Billing 通过既有回执关联。Session 不读取任何 owner 的私有数据库；外部 owner
缺失不影响历史读取与 default-only GA 能力，只有对应产品操作需要时才建立调用。

## 验收不变量

- Browser 不选择 Agent、Workflow、namespace 或 provider。
- 每个 Session 至多一个 active Run。
- durable history/event 先于 live broadcast，replay 按 `seq` 幂等。
- Redis、SSE 或 Session 重启不会引起重复执行或重复扣费。
- Root contract 变更可追溯到生成命令、consumer provenance 和 projection/contract tests。

## 1. 定位、目标与非目标

Session 是产品侧的 facade。`ProductSession` 固化 `feature_key`、`executionSubjectKind`、`executionSubjectRef`；
同一 Session 的 `tenantRef + executionSubject` 不可变。Session 不存 RuntimeNamespace/threadId，也不保存 Agent、Workflow、
成员、图或模型配方。

GA 在唯一 ingress normalizer 中仅为首次 target bootstrap（普通 Launch claim 或 fork `ForkConversation` prepare） 由
ExecutionIdentity 派生 RuntimeNamespace；后续新 Launch 验证后复用 ThreadLocator。`RuntimeNamespace` 不是 Session 字段。

## 2. 输入、输出与公开契约

### `LaunchRunRequest` 构建

```text
Session -> LaunchRunRequest -> GA ingress
-> CanonicalRunRequest  # only no-active/terminal admission
```

Session 只发送 Root generated contract 的输入、附件引用、`feature_key` 与
`ExecutionIdentity`。Browser events：仅安全产品语义；Session relay 串行消费安全 ProductEvent。

### ProductEvent

`ProductEvent` 是 GA durable source fact 的安全投影。`plan_snapshot` 只接受 parent-run-scoped 的安全 presentation item；
Session 也不读取 native `todos` 或把前端计划写回 GA。Browser
只能展示、不能按 plan item 控制任务。StudioJobLinked(JobRef) 只更新 Job card projection，Session 不拥有 Studio Job。

## 3. 生命周期与正确性不变量

一个 Session、一个 native Agent state、一个 active Run。Feature availability 与既有 Run 不共用一个状态机：System 禁用
Feature 时不写 `run_requests`、不发送 `LaunchRunRequest`；紧急停止由显式 cancel procedure 实现。active `running` 时普通
文本返回 `run_active`；terminal 后的下一条普通消息才创建新的 Run。

每次**新 Launch**的 actor/assertion 由 IAM 当前确认；Cleanup 的 delete-time tenant-subject lifecycle envelope 则来自
已接受 delete 的 durable effect。项目协作不等于同一 Session 多写者：成员 B 在 awaiting_control 内回答当前问题 -> same run 的
matching HITL respond；并行探索使用各自 fork/new Session。

删除栅栏由 GA `ThreadCleanupFence` 收口，包含 preclaim-cancel receipt 与 allocated-but-unclaimed cancel；晚到或重放的 Launch
不能复活已清理 thread。tombstone 是 Session 投影的最终写入门，不让晚到事件复活产品会话；仅 matching `activeRunId` 的
`Terminal` 更新终态，其余事件 ack/drop，条件失败后按最新状态处理。

## 4. 实际目录与职责

```text
src/contract/  Root generated consumer（只读）
src/session/   ProductSession 与 lifecycle
src/relay/     Launch/control/fork/cleanup 与 ProductEvent 投影
src/store/     产品元数据与 projection store
src/http/      IAM、history、AG-UI/SSE
src/deliveries/ Studio Job card projection
src/transport/ Redis live transport
```

## 5. 一次 run 的装配语义

Session 只做 admission 和投递，不装配 Agent。`feature_key` 由产品入口确认后原样写入 Root request；GA 用它取得已装配 Agent，
并在内部生成 `CanonicalRunRequest`、ThreadLocator 和 native checkpoint。Session 不传 namespace、Agent 或 `RuntimeConfig`。

## 6. 数据 owner、唯一 writer 与当前原型边界

GA `chat_messages` 是历史唯一来源，GA `chat_events` 是 replay/live 唯一来源；Session 是 query/projection writer，不创建
第二份 chat truth。GA durable safe ProductEvent outbox + private evidence + terminal claim 由 GA 负责，Session 只接收安全
投影。LangChain native Message ID 与 GA chat ID 不互换。

`ControlAudit(actor, decision_ref, action)` 在 Session admission transaction 写入；`control_audit_ref` 只关联刚写入的
Session `ControlAudit`，不产生第二个 namespace 或 payer。Billing 以同一 subject（以及可选 `billingRef`）定位 payer；
`billingRef` 与该 tenant + subject 不匹配均在投递/结算前拒绝。

## 7. Sandbox workspace 与 S3-compatible 边界

Session 不读写 GA workbench。GA 的 S3Workspace / WorkbenchPersistence 是 deployment adapter，不把它们解释成 Agent/Feature
配置；Storage 仍拥有 Asset/Artifact bytes 与生命周期。Session 只展示 ArtifactRef 和 Studio JobRef。

## 8. 失败语义与安全边界

Session 对失效 actor、scope mismatch、active Run、tombstone 和不合法 cursor fail-closed。晚到 ProductEvent 不得 resurrect
Session projection；Browser 不接收 raw thinking、tool args/results、sandbox path、object key、prompt 或 secret。

## 9. 可观测性、诊断与无 client 行为

观测只记录脱敏 request/run/event cursor。GA 无 Capability、Storage、Studio 或 Billing client 时，Session 的 history/replay
仍可用；GA default-only Agent 仍可运行。Session 不把 client 缺失转换为 Agent selector，也不改变 Feature/Agent 组合。

## 10. 验收矩阵（设计 100 分）

```text
Root generated contract provenance       pass
ExecutionIdentity / subject boundary    pass
single active Run + terminal gate        pass
chat_messages/chat_events replay         pass
ProductEvent redaction + idempotency     pass
StudioJobLinked(JobRef) projection       pass
fork/cleanup fence + tombstone gate      pass
AG-UI/SSE reconnect without new Run      pass
```

## 11. 验证命令与变更门禁

```bash
npm test
npm run typecheck
npm run lint
```

Root contract 变更必须先通过 Root gate，再生成 Session consumer 并运行 projection tests；不得在子仓直接编辑 generated
contract。Session 的技术方案和 [API/AIP 契约摘录](../../../kokoro-session/docs/session/api-contract.md) 只解释消费方式，
不成为第二份跨仓 schema。
