# kokoro-session 技术方案

## 定位

`kokoro-session` 是 Kokoro 三仓运行时的会话域服务。它拥有聊天窗口、消息、run、session events、SSE、replay 和 active run admission。

它只编排，不执行 agent，不渲染 UI。

## 业务职责

### Owns

```text
ChatSession。
ChatMessage。
AgentRun。
SessionEvent。
同 session 单 active run。
AgentExecutionManifest 构建和投递。
Agent raw event 归一化。
SSE live + replay。
HITL control 入口。
Mongo session 持久化。
Redis run queue / live fanout / locks。
```

### Does not own

```text
LangChain/LangGraph 执行。
Skills/MCP tool 真实执行。
Agent checkpoint/memory。
Web reducer 和 UI。
三仓运行时之外的业务管理模块。
```

## 上游和下游

```text
上游：
  kokoro-web 通过 HTTP/SSE 调用。

下游：
  kokoro-agent 通过 Redis run request/control/raw events。
  MongoDB session collections。
  Redis streams/live bus/locks。
  SiteContext/model/skill/MCP 配置服务（通过上游已解析上下文或明确接口）。
```

## 核心对象

```text
ChatSession
  聊天窗口。

ChatMessage
  用户和 assistant 的产品消息历史。

AgentRun
  一次执行状态。

SessionEvent
  浏览器事件事实，用于 replay/live/audit。

AgentExecutionManifest
  Session 发送给 agent 的执行清单。
```

## 数据模型

Mongo：

```text
kokoro_session.sessions
kokoro_session.messages
kokoro_session.runs
kokoro_session.session_events
kokoro_session.outbox（可选）
```

Redis：

```text
kokoro:runs:requests
kokoro:run:{runId}:events
kokoro:session:{sessionId}:live
kokoro:run:{runId}:control
kokoro:session:{sessionId}:lock
```

MySQL：

```text
Session 不把聊天消息写 MySQL。
需要结构化业务信息时通过 SiteContext/model/skill/MCP 配置服务读取。
```

## API / RPC / Events

### HTTP

```text
POST /sessions/:sessionId/messages
GET  /sessions/:sessionId
GET  /sessions/:sessionId/events
POST /sessions/:sessionId/runs/:runId/control
```

### Agent request

```text
run.request -> AgentExecutionManifest
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

幂等 key：

- `POST /messages`: `idempotencyKey`
- session event: `eventId`
- run: `runId`

错误码：

- `session_run_active`
- `session_not_found`
- `run_not_found`
- `manifest_build_failed`
- `agent_enqueue_failed`

## 运行时管理

Session 自身只需要运行时诊断面：

```text
查看 session。
查看 messages。
查看 runs 和 terminal status。
查看 session events。
取消 active run。
重放/诊断 SSE。
```

不在 session 里做三仓运行时之外的业务管理和审核。

## 业务链路

`kokoro-session` 只参与三仓运行链路：

```text
kokoro-web 提交用户消息。
kokoro-session 写 ChatMessage / AgentRun，校验同 session 单 active run。
kokoro-session 构建 AgentExecutionManifest 并投递给 kokoro-agent。
kokoro-session 接收 agent raw events，写 messages / runs / session_events。
kokoro-session 通过 SSE 把 browser-facing events 推给 kokoro-web。
```

Session 不维护通用产品业务链路文档；涉及平台、账务、市场、后台的链路不在本文维护。

## 部署

```text
服务名        kokoro-session
运行时        Bun + TypeScript
端口          3001
环境变量      KOKORO_SESSION_PORT
              KOKORO_REDIS_URL
              KOKORO_SESSION_MONGO_URL
              KOKORO_SESSION_MONGO_DB
              KOKORO_WEB_ORIGIN
多 Pod        Mongo unique index + Redis lease。
```

V1 runtime 不使用 SQLite 策略。测试可以保留 memory fake，但生产走 Mongo。

## 测试

```text
单测：
  API schema、manifest builder、normalizer、event idempotency、active run admission。

集成：
  POST message -> Redis run request。
  raw event -> Mongo messages/runs/session_events -> SSE。
  HITL control -> Redis control stream。
  snapshot refresh。

反例：
  同 session 并发 POST 只允许一个 active run。
  malformed raw event 不污染 session。
  duplicate eventId 只落一次。
  Redis live bus 清空后仍可从 Mongo snapshot 恢复。
```

## 风险和边界

```text
禁止 session 执行 agent。
禁止 session 读取 agent checkpoint。
禁止把 Redis 当长期历史。
禁止 Web 业务 cursor 泄漏到 session contract。
禁止同 session 多 active run 未设计排序就开放。
禁止把 messages 只作为 events 的临时投影。
```

## 后续任务

```text
P0  Mongo session store 替代 SQLite runtime 策略。
    ChatSession/ChatMessage/AgentRun/SessionEvent 明确建模。
    AgentExecutionManifest builder。
    Snapshot API。
    active run admission。

P1  session event replay 优化。
    outbox/retry。
    session admin diagnosis。

P2  多 run 队列或并行策略重新设计。
    跨设备协同 cursor-free recovery。
```
