# Agent / Session / Web 通用聊天运行链路

本文只描述 `kokoro-web`、`kokoro-session`、`kokoro-agent`
三仓内部运行链路。账务、支付、模型目录、站点解析和后台运营
只作为外部前置条件，不在本文展开。

## 目标

用户在 Web 里发送一条消息后，系统创建一个可恢复、可审计、
可取消的 agent run，并把最终回复沉淀为 session messages。

## 参与模块

```text
kokoro-web
  输入消息、展示 snapshot、消费 SSE、渲染 thread/activity、提交 HITL control。

kokoro-session
  拥有 session/messages/runs/events，构建 AgentRunInput，
  投递 run request，归一化 raw events，SSE replay/live。

kokoro-agent
  claim run，使用 DeepAgents/LangChain/LangGraph 执行模型、tools、
  Skills、MCP、subagents、sandbox，输出 raw events。
```

## 前置条件

```text
SiteContext 已由上游解析并传入 session 请求。
用户有访问 session 的权限。
本次 run 的 model、skills、MCP、tools、backend policy 已可解析。
kokoro-session 连接 Mongo + Redis。
kokoro-agent 连接 Redis + agent checkpoint/memory backend。
同 session 没有 active run，或本请求命中 idempotencyKey。
```

## 主流程

1. 用户在 `kokoro-web` composer 输入消息并提交。
2. Web 生成 `idempotencyKey`，调用 `POST /sessions/:sessionId/messages`。
3. Session 先检查 idempotencyKey 是否命中旧请求。
4. 未命中时，Session 校验 session 权限和 active run。
5. Session 在 Mongo 中写入 user `ChatMessage`。
6. Session 创建 assistant placeholder `ChatMessage`。
7. Session 创建 `AgentRun`，设置 `ChatSession.activeRunId`。
8. Session 构建 `AgentRunInput`。
9. `AgentRunInput` 包含本次 run 可用 model、skills、MCP、tools、
   backend/sandbox 和 permission policy。
10. Session 把 manifest 写入 Redis `kokoro:runs:requests`。
11. Web 收到 `runId` 后，调用 `GET /sessions/:sessionId` 拉取 snapshot。
12. Web 打开 `GET /sessions/:sessionId/events` EventSource。
13. Agent worker 从 Redis 消费 run request。
14. Agent 使用 `runId` lease 防重复执行。
15. Agent 使用 `sessionId` lease 做同 session 串行防御。
16. Agent 根据 manifest 创建 DeepAgents runtime。
17. Agent 构建 run-scoped tool registry。
18. Agent 根据 backend config 创建 DeepAgents backend instance。
19. Agent 开始执行 LangChain/LangGraph streaming loop。
20. Agent 把模型 delta、thinking、tool、todo、subagent、HITL、terminal 转成 raw events。
21. Agent 写 Redis `kokoro:run:{runId}:events`。
22. Session relay 串行读取该 run raw events。
23. Session strict parse raw event，非法事件丢弃并记录诊断，不污染 Mongo。
24. Session normalize 成 browser-facing `SessionEvent`。
25. Session DB-first 写 Mongo `session_events`，同步更新 projections。
26. Terminal event 同 commit 更新 run terminal，清 `activeRunId`。
27. Session commit 后 publish 到 Redis `kokoro:session:{sessionId}:live`。
28. SSE endpoint 把事件推给 Web。
29. Web strict parse transport event，按 `eventId` 去重。
30. Web 按 SSE 到达顺序应用 reducer。
31. `message.delta` 更新 assistant 临时显示。
32. `tool.awaiting_approval` 显示 HITL 控件。
33. 用户 approve/reject/cancel 时，Web 调用 control API。
34. Session 校验 run 归属和权限，写 Redis control stream。
35. Agent 恢复 DeepAgents/LangGraph interrupt，继续执行或终止。
36. `message.completed` 到达时，Session 写最终 assistant message content。
37. Web 用最终内容覆盖 delta。
38. Terminal event 到达时，Web 关闭 streaming 状态。

## 刷新和断线恢复

```text
页面刷新：
  Web -> GET /sessions/:sessionId
  Web 用 snapshot 重建 thread，并获得 eventWatermark。
  如果 activeRun 存在，Web -> GET /sessions/:sessionId/events。

EventSource 瞬断：
  浏览器可使用标准 Last-Event-ID 自动重连。
  Session 用 Last-Event-ID 作为内部 replay anchor。
  Web domain 不保存 lastResumeId。

Last-Event-ID 缺失、过期或未知：
  Session 可从 snapshot eventWatermark 之后开始 replay。
  Web 用 eventId 去重。
  必要时用户刷新页面，snapshot 是最终权威。
```

Mongo replay 到 Redis live tail 的无缝衔接由 session 服务端处理：

```text
先读取 Redis live tail id。
再从 Mongo replay 水位之后的事件。
最后从 captured live tail id 之后开始 tail live。
重叠事件由 eventId 去重。
```

不允许通过轮询 Mongo 追 token。Mongo 是 replay/snapshot 真源，
不是高频 live polling 机制。

## 异常流程

```text
同 session 已有 active run
  若不是同 idempotencyKey 重试，POST /messages 返回 session_run_active。

idempotencyKey 重试
  先于 active-run gate，返回首次创建的 messageId/runId。
  不重复写消息。

Redis run request 投递失败
  run 标记 enqueue_failed，清 activeRunId，Web 显示可重试。

Agent worker 崩溃
  run lease 过期后可由 worker 重新 claim。
  raw event + session event 通过 eventId 幂等收敛。

Session relay 崩溃
  已 DB commit 的事件可 replay。
  未 DB commit 的 live event 不允许已经发给 Web；因此必须 DB-first。

Malformed raw event
  Session 记录诊断并跳过该 event。
  terminal event 仍应能落地，避免 run 永远 running。

HITL 超时
  Agent 产出 run.completed(status=timeout) 或 run.failed。
  Session 清 activeRunId。

用户取消
  Web -> session control cancel。
  Agent 收到 control 后中止，输出 run.completed(status=cancelled) 或 run.failed。
```

## 数据变化

### Mongo: `kokoro_session`

```text
sessions
  activeRunId 从 null -> runId -> null。

messages
  新增 user message。
  新增 assistant placeholder。
  delta 期间可节流更新 assistant draft。
  completed 时写最终 assistant content。

runs
  新增 run。
  running / awaiting_approval / completed / failed / cancelled 状态变化。

session_events
  写 browser-facing events，用于 replay/live/audit。

outbox
  可选；DB commit 后可靠 publish live。
```

### Redis

```text
kokoro:runs:requests
  新增 run.request manifest。

kokoro:run:{runId}:events
  agent raw events。

kokoro:session:{sessionId}:live
  session live events，有界窗口。

kokoro:run:{runId}:control
  HITL/cancel control。

lease keys
  run/session 执行锁。
```

### Web 本地

```text
localStorage/sessionStorage
  可保存 draft、activeSessionId、UI collapsed state。
  不保存权威 run terminal status。
  不保存业务 cursor。
```

## 幂等和一致性

```text
POST message
  idempotencyKey + sessionId + userId。

Run claim
  runId lease。

同 session 串行
  Mongo activeRunId 条件写 + Redis session lease 防御。

Session event
  eventId 唯一索引去重，且 retry/reclaim 后必须稳定。

Replay anchor
  SSE id / Last-Event-ID 是传输层内部值，不排序、不展示。

排序
  V1 依赖单 active run + session relay 串行。
  Replay 用 Mongo append order，渲染用 SSE 单连接发送顺序。
```

## 用户可见结果

```text
消息发送后立即出现用户消息和 assistant 占位。
流式回复稳定显示。
Thinking/tool/todo/subagent 活动在 activity UI 展示。
需要审批时出现明确 approve/reject/cancel 控件。
刷新后不会丢消息，不会重复显示同一个 event。
失败时 assistant turn 进入失败态，可重试。
```

## 验收标准

```text
同 session 并发提交两条消息，只允许一个 active run。
刷新 active run 页面后，snapshot 正确，SSE 可继续。
断开 live bus 后，历史仍能从 Mongo snapshot/replay 恢复。
eventId 重复投递不重复渲染、不重复落库。
Web 不读取 seq/cursor/order 字段。
Agent 不写 session Mongo。
Session 不读 agent checkpoint。
Production session 不存在 SQLite runtime。
Production agent 不默认 local_shell。
```
