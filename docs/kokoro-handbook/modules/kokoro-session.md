# kokoro-session 技术方案

本文只约束 `kokoro-session` 子仓。三仓总链路见
[Agent / Session / Web V1 运行时技术方案](../technical/11-agent-session-web-v1-runtime.md)，
聊天链路见
[Agent / Session / Web 通用聊天运行链路](../business-flows/agent-session-web-general-chat-runtime.md)。

## 定位

`kokoro-session` 是会话域服务。它拥有聊天窗口、消息、run、浏览器事件、
SSE replay 和同 session 单 active run admission。

它只编排，不执行 agent，不渲染 UI，不拥有模型/tool/MCP 的实际执行。

## 当前实现状态

已实现：

```text
HTTP:
  POST /sessions/:sessionId/messages
  GET  /sessions/:sessionId
  GET  /sessions/:sessionId/stream
  POST /sessions/:sessionId/runs/:runId/control

SessionStore:
  startRun
  appendEvent
  getSession
  listMessages
  listRuns
  listEvents

MongoSessionStore:
  sessions
  messages
  runs
  session_events
  outbox collection placeholder

Redis:
  kokoro:runs:requests
  kokoro:run:{runId}:events
  kokoro:session:{sessionId}:live

Normalizer:
  agent wire event -> browser-facing SessionEvent
  event_id deterministic opaque id
  no seq
```

尚未完整实现，不能写成已完成：

```text
session -> agent run.request 与 agent Python 入站契约完全合流。
可靠 outbox publish/retry。
GET snapshot 的正式 DTO 分层和分页。
Session event projection 对 assistant message content 的完整写回。
多 pod session 级 lease 的完整实现。
外部 SiteContext/policy/model/skill/MCP 服务集成。
```

## 业务职责

### Owns

```text
ChatSession。
ChatMessage。
AgentRun。
SessionEvent。
POST message idempotency。
同 session 单 active run admission。
AgentRunInput manifest 构建。
agent raw event strict parse。
browser-facing event normalization。
DB-first event append。
SSE replay/live。
HITL control HTTP 入口和转发。
```

### Does Not Own

```text
LangChain / DeepAgents 执行。
工具、skills、MCP 的真实调用。
agent checkpoint / run_state。
Web reducer / UI 状态。
积分、支付、价格、后台管理。
```

## 上游和下游

```text
上游：
  kokoro-web 通过 HTTP/SSE 调用。

下游：
  kokoro-agent 通过 Redis 请求流、run event 流、control 消息通信。
  MongoDB 存储 session/messages/runs/session_events。
  Redis 用于队列、短期 raw stream、live fanout。
```

Session 不读取 agent checkpoint，不直连 model provider，不执行 MCP tool。

## 核心对象

```text
ChatSession
  siteId, sessionId, ownerUserId, activeRunId, status, createdAt, updatedAt。

ChatMessage
  siteId, messageId, sessionId, runId, role, content, status, createdAt, updatedAt。

AgentRun
  siteId, runId, sessionId, userMessageId, assistantMessageId,
  idempotencyKey, status, createdAt, updatedAt。

SessionEventLogEntry
  siteId, eventId, sessionId, conversationId, runId, type, timestamp,
  status?, payload, createdAt。

AgentRunInput
  session 目标态的 run manifest。当前 session 已构建，但 agent 尚未完全消费。
```

## 数据模型

### Mongo

Production session 真源是 Mongo。

```text
sessions
  unique(siteId, sessionId)
  activeRunId 做 admission gate。

messages
  unique(siteId, sessionId, messageId)
  按 createdAt + _id 展示聊天消息。

runs
  unique(siteId, runId)
  unique(siteId, sessionId, idempotencyKey)

session_events
  unique(siteId, sessionId, eventId)
  按 _id 追加顺序 replay。

outbox
  已建 collection/index，占位；可靠 publish/retry 仍是 P0/P1。
```

### Redis

Redis 不是长期事实源。

```text
kokoro:runs:requests
  run.request / run.resume / run.cancel。

kokoro:run:{runId}:events
  agent raw events。

kokoro:session:{sessionId}:live
  session live fanout，有界窗口。
```

### MySQL

Session 不把聊天消息写 MySQL。核心管理/账务数据归平台域，session 只消费
上游传入的 site/user/workspace/policy 结果。

## API / RPC / Events

### HTTP

```text
POST /sessions/:sessionId/messages
  body:
    idempotencyKey
    content
    attachments?
    executionStyle?
    permissionMode?
    selectedSkillIds?
    selectedMcpServerIds?
    selectedToolNames?

GET /sessions/:sessionId
  returns:
    session
    messages
    runs
    events
    eventWatermark

GET /sessions/:sessionId/stream
  EventSource SSE。当前实际路径是 /stream，不是 /events。

POST /sessions/:sessionId/runs/:runId/control
  body:
    run.cancel
    run.resume(decisions)
```

`permissionMode` 是当前代码入参。目标态不继续扩展这个字段，而是由
session 把 Web 预设编译成 `execution.toolMode` 与 `approvalPolicy` 后放入
`AgentRunInput`。

### Session -> Agent

目标设计是 manifest-first：

```text
run.request:
  kind
  site_id
  run_id
  session_id
  agent_run_input
```

当前 agent Python 仍接受旧扁平 `RunRequest`。这是 P0 契约差距。

### Agent -> Session

agent 原始 wire event：

```text
event / request_id / timestamp / data
```

Session strict parse 后归一化为 browser-facing events：

```text
session.created
run.created
thinking.delta
message.delta
message.completed
tool.invoked
tool.awaiting_approval
tool.returned
todo.updated
subagent.started
subagent.finished
subagent.text.delta
subagent.text.completed
run.completed
run.failed
```

## event_id / replay / SSE

```text
event_id
  opaque idempotency key。
  由 raw stream id + request_id + agent event + session event + data 稳定派生。
  不排序，不展示，不作为业务 cursor。

SSE id
  当前使用 event_id。
  浏览器同一 EventSource 自动重连时会带 Last-Event-ID。

listEvents(afterEventId)
  找到 anchor eventId 后按 Mongo _id > anchor._id replay。
  未找到 anchor 时当前实现会退化为全量 replay。

Web 去重
  web reducer 按 eventId 去重。
```

Session 不能轮询 Mongo 追 token。实时通过 Redis live fanout；Mongo 用于 snapshot、
replay、audit 和故障恢复。

## Admin 管理

Session 自身只应提供运行诊断能力：

```text
查看 session。
查看 messages。
查看 runs。
查看 session_events。
取消 active run。
诊断 SSE replay。
```

不在 session 做 skill/MCP/price/credit/payment 管理。

## 业务链路

```text
1. Web POST /sessions/:id/messages。
2. Session 用 idempotencyKey 查重。
3. Session 用 activeRunId 做同 session admission。
4. Session 写 user message、assistant placeholder、run。
5. Session 构建 AgentRunInput。
6. Session 写 Redis kokoro:runs:requests。
7. Agent 写 raw events。
8. Session relay 消费 raw events。
9. Session normalize。
10. Session appendEvent 先写 Mongo。
11. append 成功后 publish live。
12. Web SSE 消费并按 eventId 去重。
```

终态：

```text
run.completed(status=completed|cancelled|timeout)
run.failed(error_kind, message)
```

终态 append 必须在同一事务内更新 run status 并清 activeRunId。

## 部署

```text
服务名        kokoro-session
运行时        Bun + TypeScript
端口          KOKORO_SESSION_PORT，默认 3001
Mongo         KOKORO_SESSION_MONGO_URL
              KOKORO_SESSION_MONGO_DB
Redis         KOKORO_STREAM_BACKEND=redis
              KOKORO_REDIS_URL
CORS          KOKORO_WEB_ORIGIN
```

Production：

```text
必须使用 MongoSessionStore。
必须使用真实 Redis。
不能使用 SQLite runtime。
memory store 只允许测试。
```

## 测试

必须覆盖：

```text
POST /messages idempotency。
同 session active run 冲突。
GET /sessions snapshot DTO。
SSE Last-Event-ID replay。
unknown Last-Event-ID 全量 replay + eventId 去重。
agent malformed event skip-and-continue。
DB-first append 后 publish live。
terminal event 清 activeRunId。
control endpoint run ownership 校验。
session -> agent run.request 与 agent Python 入站模型一致。
```

## 风险和边界

必须明确禁止：

```text
重新引入 seq。
把 Redis 当聊天历史。
session 执行 agent 或 tool。
session 读取 agent checkpoint。
Web 自定义 after/lastResumeId 协议绕过 SSE 标准机制。
同 session 多 active run 在未重新设计排序模型前开放。
为了旧本地测试保留旧 /runs 启动接口。
```

## 后续任务

### P0

```text
把 agent Python RunRequest 改成消费 agent_run_input manifest。
把 permissionMode 拆成 execution.toolMode + approvalPolicy。
GET /sessions snapshot DTO 正式化，避免直接泄漏内部 events 全量结构。
appendEvent 同步更新 assistant message completed content。
startRun publish 失败时标记 enqueue_failed 并清 activeRunId。
control endpoint 校验 run 属于 session/site/user。
明确 /stream 是否保留，若改为 /events 必须一次性跨 web/session 改净。
```

### P1

```text
outbox + retry 实现。
SSE replay limit/page。
session event 诊断 API。
Mongo 事务异常恢复测试。
```

### P2

```text
多 run 队列策略。
跨设备协同体验。
更完整 admin diagnostics。
```
