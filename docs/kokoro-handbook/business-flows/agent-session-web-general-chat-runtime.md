# Agent / Session / Web 通用聊天运行链路

本文只描述 `kokoro-web`、`kokoro-session`、`kokoro-agent`
三仓内部运行链路。账务、支付、模型目录、站点解析、公开 Hub 和后台运营
只作为外部前置条件，不在本文展开。

## 目标

用户在 Web 中发送一条消息后，系统创建一个可恢复、可审计、可取消的
agent run，并把最终回复沉淀为 session messages。

## 参与模块

```text
kokoro-web
  输入消息、加载 snapshot、消费 EventSource、渲染 thread/activity、
  提交 HITL control 和 ask_user_question 回答。

kokoro-session
  拥有 session/messages/runs/events，构建 RunRequest，
  投递 run request，归一化 raw events，SSE replay/live。

kokoro-agent
  claim run，使用 DeepAgents/LangChain/LangGraph 执行模型、tools、
  Skills、MCP、subagents、backend/sandbox，输出 raw events。
```

## 前置条件

```text
SiteContext 已由上游解析并传入 session 请求。
用户有访问 session 的权限。
本次 run 的 model、skills、MCP、tools、subagents、backend、permissions 已可解析。
kokoro-session 连接 Mongo + Redis。
kokoro-agent 连接 Redis + agent checkpoint/memory backend。
同 session 没有 active run，或本请求命中 idempotencyKey。
```

## 主流程

1. 用户在 `kokoro-web` composer 输入消息并提交。
2. Web 生成 `idempotencyKey`。
3. Web 调用 `POST /sessions/:sessionId/messages`。
4. Session 先按 `idempotencyKey` 查重试命中。
5. 未命中时，Session 校验 SiteContext、用户权限和 active run。
6. Session 在 Mongo 中写入 user `ChatMessage`。
7. Session 创建 assistant placeholder `ChatMessage`。
8. Session 创建 `AgentRun`，设置 `ChatSession.activeRunId = runId`。
9. Session 解析本次 `RuntimeConfig`：model、tools、skills、MCP、subagents、backend、permissions、interrupt_on。
10. Session 构建 `RuntimeContext`：site/user/workspace/project/session、消息窗口、summary、refs。
11. Session 构建 `RunRequest`。
12. Session 持久化 `run_requests` 和 `runtime_configs`。
13. Session 写 Redis `kokoro:runs:requests`。
14. Web 收到 `runId`、`inputMessageId`、`assistantMessageId`。
15. Web 调用 `GET /sessions/:sessionId` 拉取权威 snapshot。
16. Web 打开 `GET /sessions/:sessionId/events` EventSource。
17. Agent worker 从 Redis 消费 `run.request`。
18. Agent 使用 `runId` lease 防重复执行。
19. Agent 使用 `threadId` 作为 LangGraph `configurable.thread_id`。
20. Agent 根据 `RuntimeConfig` 调用 `create_deep_agent(...)`。
21. Agent 加载 tools、skills、MCP tool wrappers、subagents、backend、permissions、interrupt_on。
22. Agent 开始 LangGraph streaming loop。
23. Agent 把模型 delta、thinking、tool、todo、subagent、HITL、terminal 转成 raw events。
24. Agent 写 Redis `kokoro:run:{runId}:events`。
25. Session relay 串行读取该 run raw events。
26. Session strict parse raw event；非法事件记录诊断并跳过。
27. Session normalize 成 browser-facing `SessionEvent`。
28. Session DB-first 写 Mongo `session_events`，同步更新 messages/runs projection。
29. Terminal event 同 commit 更新 run terminal，清 `activeRunId`。
30. Mongo commit 成功后，Session publish 到 Redis `kokoro:session:{sessionId}:live`。
31. SSE endpoint 把事件推给 Web。
32. Web strict parse transport event。
33. Web 按 `eventId` 去重，按 SSE 到达顺序应用 reducer。
34. `message.delta` 更新 assistant 临时显示。
35. `message.completed` 用最终内容覆盖 delta。
36. `run.completed(status=completed|cancelled|timeout)` 或 `run.failed`
    到达时，Web 收束 streaming 状态。

## HITL 流程

1. Agent 运行时命中 `interrupt_on`。
2. LangGraph 产生 interrupt，包含 `action_requests` 和 `review_configs`。
3. Agent 映射为 raw `tool.awaiting_approval`，保留：

```text
tool name
arguments
description
allowed_decisions
```

1. Session DB-first 写 `SessionEvent` 并 SSE 推给 Web。
2. Web 展示 approve/reject/edit/cancel。
3. 用户提交后，Web 调用 `POST /sessions/:sessionId/runs/:runId/control`。
4. Session 校验 run 归属、权限和状态。
5. Session 写 Redis `kokoro:run:{runId}:control`。
6. Agent 读取 control，构造：

```python
Command(resume={"decisions": [...]})
```

1. Agent 用同一个 `threadId` 恢复 LangGraph 执行。

`respond` 只用于 `ask_user_question`。普通危险工具拒绝必须是 `reject`。

## ask_user_question 流程

1. 模型调用 `ask_user_question`。
2. Agent 触发 HITL-style interrupt。
3. Web 渲染为问题卡片，而不是审批卡片。
4. 用户填写答案或选择选项。
5. Web 通过 control 提交 `respond`。
6. Agent 把用户回答作为 ask_user_question 工具结果继续执行。

## Subagent 流程

配置型或默认子代理：

```text
RuntimeConfig.subagents
  -> create_deep_agent(subagents=...)
  -> DeepAgents task tool
```

临时 delegate：

```text
模型提出 name/description/system_prompt/task
  -> permissions.subagent_create
  -> ask/allow/deny
  -> 仅授予 RuntimeConfig 子集能力
  -> 执行并返回 summary
```

临时子代理不能默认继承全部工具，不能默认再创建子代理。

## 刷新和断线恢复

页面刷新：

```text
Web -> GET /sessions/:sessionId
Web 用 snapshot 重建 thread/activity。
如果 activeRun 存在，Web -> GET /sessions/:sessionId/events。
```

EventSource 瞬断：

```text
浏览器使用标准 Last-Event-ID 自动重连。
Session 用 Last-Event-ID 作为内部 replay anchor。
Web domain 不保存 lastResumeId。
```

Last-Event-ID 缺失、过期或未知：

```text
Session 可从 snapshot eventWatermark 之后开始 replay。
Web 用 eventId 去重。
必要时用户刷新页面，snapshot 是最终权威。
```

Mongo replay 到 Redis live tail：

```text
1. Session 捕获 Redis live stream tail id。
2. 从 Mongo replay 水位之后的事件。
3. 从 captured tail id 之后 tail live bus。
4. 重叠事件由 eventId 去重。
```

不允许通过轮询 Mongo 追 token。

## 异常流程

```text
同 session 已有 active run
  若不是同 idempotencyKey 重试，POST /messages 返回 session_run_active。

idempotencyKey 重试
  返回首次创建的 messageId/runId，不重复写消息。

Redis run request 投递失败
  run 标记 enqueue_failed，清 activeRunId，Web 显示可重试。

Agent worker 崩溃
  run lease 过期后可重新 claim。
  eventId 保证重复 raw/session event 幂等收敛。

Session relay 崩溃
  已 DB commit 的事件可 replay。
  未 DB commit 的事件不能已经发给 Web；因此必须 DB-first。

Malformed raw event
  Session 记录诊断并跳过该 event。
  后续 terminal event 仍应落地。

HITL 超时
  Agent 产出 run.completed(status=timeout) 或 run.failed。
  Session 清 activeRunId。

用户取消
  Web -> session control cancel。
  Agent 中止，输出 run.completed(status=cancelled) 或 run.failed。
```

## 数据变化

### Mongo: `kokoro_session`

```text
sessions
  activeRunId: null -> runId -> null

messages
  新增 user message
  新增 assistant placeholder
  delta 期间可节流更新 assistant draft
  completed 时写最终 assistant content

runs
  新增 run
  running / awaiting_approval / completed / failed / cancelled / timeout

run_requests
  持久化本次 RunRequest

runtime_configs
  持久化本次已解析 RuntimeConfig

session_events
  写 browser-facing events，用于 replay/live/audit

outbox
  可选；DB commit 后可靠 publish live
```

### Redis

```text
kokoro:runs:requests
kokoro:run:{runId}:events
kokoro:session:{sessionId}:live
kokoro:run:{runId}:control
lease keys
```

### Web 本地

```text
可保存 draft、activeSessionId、UI collapsed state。
不保存权威 run terminal status。
不保存业务 cursor 或 lastResumeId；seq 只作为 session 事件里的 render order 随事件折叠。
```

## 幂等和一致性

```text
POST message
  idempotencyKey + sessionId + userId

Run claim
  runId lease

同 session 串行
  Mongo activeRunId 条件写 + Redis session lease

Session event
  eventId 唯一索引去重

Replay anchor
  SSE id / Last-Event-ID 是传输层内部值

排序
  V1 依赖单 active run + session relay 串行
  Replay 用 Mongo append order
  Web 渲染用 SSE 单连接发送顺序
```

## 用户可见结果

```text
消息发送后出现用户消息和 assistant 占位。
流式回复稳定显示。
Thinking/tool/todo/subagent 活动在 activity UI 展示。
需要审批时出现明确 approve/reject/edit/cancel 控件。
ask_user_question 时出现问题输入卡片。
刷新后不丢消息，不重复显示同一个 event。
失败时 assistant turn 进入失败态，可重试。
```

## 验收标准

```text
同 session 并发提交两条消息，只允许一个 active run。
刷新 active run 页面后，snapshot 正确，EventSource 可继续。
断开 live bus 后，历史仍能从 Mongo snapshot/replay 恢复。
eventId 重复投递不重复渲染、不重复落库。
Web 不读取 cursor/order 字段；seq 只作同一 run 内 UI 交错。
Agent 不写 session Mongo。
Session 不读 agent checkpoint。
run.completed.status 在 Web 可见。
tool.awaiting_approval 包含 description 和 allowed_decisions。
Production session 不存在 SQLite runtime。
Production agent 不默认 local_shell。
```
