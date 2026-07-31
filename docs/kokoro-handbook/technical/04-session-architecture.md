# Session 架构

> 历史局部说明。当前 Session 的 PostgreSQL owner、HTTP/SSE、durable Agent transport 与 Platform Connect 边界以
> technical/24、ADR-012 和实际 contract registry 为准；本文旧 MySQL/Mongo/V1 描述不得作为当前事实。

三仓 V1 运行时总方案见：
[Agent / Session / Web V1 标准运行时方案](11-agent-session-web-v1-runtime.md)。
三仓通用聊天链路见：
[Agent / Session / Web 通用聊天运行链路](../business-flows/agent-session-web-general-chat-runtime.md)。

## 定位

`kokoro-session` 是三仓里的会话事实源。它拥有聊天窗口、消息、run、
浏览器事件、snapshot、SSE 和 replay 语义。

它不执行 agent，不渲染 UI，不读取 agent checkpoint。

## V1 能力范围

```text
sessions / messages / runs / session_events。
同 session 单 active run。
构建 RunRequest 并投递给 agent。
接收 agent raw events 并归一化为 browser-facing session events。
Mongo 长期持久化。
Redis run queue、raw event stream、live fanout、locks。
SSE live + replay。
HITL control 透传。
```

V1 不支持 session SQLite runtime，不开放同 session 多 active run。

## 核心对象

```text
ChatSession
  siteId / sessionId / ownerUserId / title / activeRunId / status

ChatMessage
  siteId / sessionId / messageId / runId / role / content / parts / status

AgentRun
  siteId / sessionId / runId / threadId
  inputMessageId / assistantMessageId / status

SessionEvent
  siteId / sessionId / runId / eventId / sseId / event / payload / createdAt

RunRequest
  runId / threadId / input / runtime / context / trace
```

Session 的聊天展示主数据是 `messages`，不是每次从 events 重放。
`session_events` 用于 replay/live/audit/debug。

## API

```text
POST /sessions/:sessionId/messages
GET  /sessions/:sessionId
GET  /sessions/:sessionId/events
POST /sessions/:sessionId/runs/:runId/control
```

删除：

```text
POST /sessions/:sessionId/runs
GET  /sessions/:sessionId/stream
```

## Snapshot

`GET /sessions/:sessionId` 返回：

```text
session metadata
messages page
activeRun
recent activity
eventWatermark
```

`eventWatermark` 是服务端内部 replay 水位，不是 Web 业务 cursor。

## RunRequest 构建

Session 从以下来源构建 RuntimeConfig 和 RuntimeContext：

```text
SiteContext
消息窗口和 summary
用户输入 content/contentRef/attachments
model policy
skills enablement
MCP server/tool grants
built-in tools
subagents
backend/sandbox policy
permissions and interrupt_on
trace context
```

`threadId = sessionId`，但只在 Agent/LangGraph 边界使用 `threadId` 命名。

## 存储

Mongo:

```text
sessions
messages
runs
session_events
run_requests
runtime_configs
outbox
```

Redis:

```text
run request queue
raw run events
live bus
control stream
lease keys
```

MySQL:

```text
Session 不把聊天消息写 MySQL。
结构化业务上下文由上游服务解析后传入。
```

## 排序和幂等

```text
同一 session 同时只有一个 active run。
Session relay 串行消费 raw events。
Mongo append order 是 replay 内部排序真源。
SSE 单连接发送顺序是 Web 渲染顺序。
eventId 只做幂等去重，不排序。
SSE id 只做 Last-Event-ID replay anchor。
```

禁止新增或暴露：

```text
seq
cursor
eventPosition
lastResumeId
```

## SSE 和 Replay

实时路径：

```text
agent raw event
  -> strict parse
  -> normalize
  -> Mongo commit session_event + projections
  -> Redis live publish
  -> SSE
```

恢复路径：

```text
snapshot
capture Redis live tail
Mongo replay
tail live
eventId 去重
```

不允许通过轮询 Mongo 追 token。

## HITL Control

Session 校验 run 归属、用户权限、run 状态和 decision 合法性，然后写 control stream。
真正恢复由 Agent 调用 `Command(resume=...)`。

`respond` 只允许 `ask_user_question`。

## 性能

```text
message.delta 可 micro-batch。
messages draft 更新可节流。
completed 写最终内容。
live bus bounded。
snapshot messages 分页。
```

## 风险

```text
把 events 当唯一聊天历史。
Web 自己维护业务 cursor。
Session 读取 agent checkpoint。
Redis 变成长期消息库。
同 session 多 active run 未设计排序就开放。
DB commit 前 publish live。
```
