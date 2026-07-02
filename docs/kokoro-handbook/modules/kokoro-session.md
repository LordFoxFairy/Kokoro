# kokoro-session 技术方案

三仓 V1 运行时总方案见：
[Agent / Session / Web V1 标准运行时方案](../technical/11-agent-session-web-v1-runtime.md)。
HIL、pending pause 和 control 方案见：
[Agent HIL 与工具拦截标准方案](../technical/12-agent-hitl-tool-interception.md)。
三仓通用聊天链路见：
[Agent / Session / Web 通用聊天运行链路](../business-flows/agent-session-web-general-chat-runtime.md)。

## 定位

`kokoro-session` 是三仓运行时的会话事实源。它拥有聊天窗口、消息、
run、session events、snapshot、SSE replay/live 和 active run admission。

它只做会话编排，不执行 agent，不渲染 UI，不读取 agent checkpoint。

## 业务职责

### Owns

```text
ChatSession。
ChatMessage。
AgentRun。
SessionEvent。
RunRequest 构建和投递。
同 session 单 active run。
Agent raw event strict parse。
Browser-facing event normalization。
Mongo DB-first 持久化。
SSE replay/live。
HITL/cancel control 入口。
Redis queue/live/control/lease。
```

### Does not own

```text
LangChain/LangGraph 执行。
Tool / Skill / MCP 实际执行。
Agent checkpoint/memory。
Web reducer 和 UI。
Skill/MCP Hub 的公开运营能力。
账务、支付、价格、模型最终定价。
```

## 上游和下游

```text
上游：
  kokoro-web HTTP/SSE。
  SiteContext/policy/runtime resolver。

下游：
  kokoro-agent Redis run request/control/raw events。
  MongoDB session collections。
  Redis streams/live bus/locks。
```

## 核心对象

```text
ChatSession
  聊天窗口。

ChatMessage
  用户和 assistant 的产品消息历史。

AgentRun
  一次 agent 执行状态。

SessionEvent
  浏览器事件事实，用于 replay/live/audit。

RunRequest
  Session 发给 Agent 的执行请求。

RuntimeConfig
  已解析的 model/tools/skills/MCP/backend/permissions。
```

## 数据模型

Mongo：

```text
kokoro_session.sessions
  siteId, sessionId, ownerUserId, workspaceId, projectId,
  title, status, activeRunId, createdAt, updatedAt, version

kokoro_session.messages
  siteId, sessionId, messageId, runId,
  role, content, parts, attachments, status, createdAt, updatedAt

kokoro_session.runs
  siteId, sessionId, runId,
  inputMessageId, assistantMessageId,
  threadId, status, runtimeConfigId,
  error, startedAt, completedAt

kokoro_session.session_events
  siteId, sessionId, runId,
  eventId, sseId, event, payload, createdAt

kokoro_session.run_requests
  runId, threadId, input, context, runtimeConfigId, trace, createdAt

kokoro_session.runtime_configs
  runtimeConfigId, runId, model, tools, skills, mcp,
  subagents, backend, permissions, interrupt_on, createdAt

kokoro_session.outbox
  可选；DB commit 后可靠 publish live。
```

Redis：

```text
kokoro:runs:requests
kokoro:run:{runId}:events
kokoro:run:{runId}:control
kokoro:session:{sessionId}:live
lease keys
```

MySQL：

```text
Session 不把聊天消息写 MySQL。
结构化业务配置由上游 SiteContext/policy/runtime resolver 提供。
```

SQLite：

```text
Session runtime 不使用 SQLite。
测试可使用 memory fake，但 Mongo 行为必须有集成测试。
```

## API / RPC / Events

### HTTP

```text
POST /sessions/:sessionId/messages
GET  /sessions/:sessionId
GET  /sessions/:sessionId/events
POST /sessions/:sessionId/runs/:runId/control
```

删除旧入口：

```text
POST /sessions/:sessionId/runs
GET  /sessions/:sessionId/stream
```

### Agent request

```text
run.request -> RunRequest
run.resume  -> Command(resume=...) 所需 decisions
run.cancel  -> cancel signal
```

### Browser events

```text
session.created
run.created
message.delta
message.completed
thinking.delta
tool.invoked
tool.awaiting_approval
tool.returned
todo.updated
subagent.started
subagent.finished
run.completed
run.failed
```

幂等：

```text
POST /messages: idempotencyKey
session event: eventId
run: runId
```

错误码：

```text
session_run_active
session_not_found
run_not_found
runtime_config_failed
agent_enqueue_failed
control_not_allowed
```

## RunRequest 构建

Session 是产品上下文到 Agent runtime 的边界。

输入来源：

```text
SiteContext
当前 session messages 窗口和摘要
用户消息 content/contentRef/attachments
用户选择或系统解析的 model
已启用 skills
已授权 MCP servers/tools
可用 built-in tools
subagent 配置
backend/sandbox policy
permission policy
trace context
```

输出：

```text
RunRequest {
  runId
  threadId = sessionId
  input
  runtime
  context
  trace
}
```

Session 不把全量历史和全量 Hub 列表塞给 Agent。大上下文用摘要、窗口和 refs。

## SSE / Replay

实时路径必须 DB-first：

```text
agent raw event
  -> session strict parse
  -> normalize browser event
  -> Mongo session_events + messages/runs projection commit
  -> Redis live publish
  -> SSE
```

恢复路径：

```text
GET /sessions/:sessionId snapshot
EventSource /sessions/:sessionId/events
session 捕获 Redis live tail id
Mongo replay 水位之后的 events
tail Redis live
Web eventId 去重
```

不轮询 Mongo 追 token。Mongo 是 replay/snapshot 真源，Redis live 是短期实时通道。

## 排序和幂等

```text
V1 同 session 单 active run。
Session relay 串行消费 raw events。
Mongo append order 是 replay 内部排序真源。
SSE 单连接发送顺序是 Web 渲染顺序。
eventId 只做去重，不排序。
SSE id 只做 Last-Event-ID replay anchor。
```

禁止暴露：

```text
seq
cursor
eventPosition
lastResumeId
```

## HITL Control

Session 只做权限和归属校验：

```text
run 属于 session。
用户能控制该 session。
run 处于 awaiting / running 可控制状态。
decision 对应当前 interrupt frame。
```

然后写 Redis control stream。Agent 负责恢复 `Command(resume=...)`。

`respond` 仅允许 `ask_user` 场景；其它危险工具拒绝必须是 `reject`。

## 运行时管理

Session V1 可提供诊断面：

```text
查看 session/messages/runs/session_events。
查看 active run。
取消 active run。
重放 SSE。
查看 RunRequest/RuntimeConfig 摘要。
```

不在 session 内做 Hub 运营审核和账务管理。

## 部署

```text
服务名        kokoro-session
运行时        Node.js + TypeScript
包管理        pnpm 或 npm
端口          3001
环境变量      KOKORO_SESSION_PORT
              KOKORO_REDIS_URL
              KOKORO_SESSION_MONGO_URL
              KOKORO_SESSION_MONGO_DB
              KOKORO_WEB_ORIGIN
多 Pod        Mongo 条件写 + Redis lease
```

V1 不使用 Bun 作为标准运行约束。

## 测试

```text
单测：
  API schema、RunRequest builder、normalizer、event idempotency、
  active run admission、control validation。

集成：
  POST message -> Mongo -> Redis run.request。
  raw event -> Mongo DB-first -> live SSE。
  snapshot refresh。
  Last-Event-ID replay。
  HITL control -> Redis control stream。

反例：
  同 session 并发提交只允许一个 active run。
  duplicate eventId 只落一次。
  malformed raw event 不污染 Mongo。
  Redis live 被裁剪后仍能 snapshot/replay。
  Session 不读取 agent checkpoint。
```

## 风险和边界

```text
禁止 session 执行 agent。
禁止 session 读取 agent checkpoint。
禁止把 Redis 当长期历史。
禁止 Web 业务 cursor 泄漏到 contract。
禁止 messages 只作为 events 临时投影。
禁止未设计排序就开放同 session 多 active run。
```

## 后续任务

```text
P0  删除旧 /runs 和 /stream。
    ChatSession/ChatMessage/AgentRun/SessionEvent 建模。
    RunRequest builder。
    RuntimeConfig 持久化。
    Snapshot API。
    DB-first relay + outbox。
    active run admission。

P1  replay 性能优化。
    SSE 诊断工具。
    RunRequest/RuntimeConfig 审计展示。

P2  多 active run 设计评审后再开放。
    更复杂专业 agent 编排入口。
```
