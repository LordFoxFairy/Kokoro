# Session 架构

三仓 V1 运行时总方案见：
[Agent / Session / Web V1 运行时技术方案](11-agent-session-web-v1-runtime.md)。
三仓通用聊天链路见：
[Agent / Session / Web 通用聊天运行链路](../business-flows/agent-session-web-general-chat-runtime.md)。

## 定位

`kokoro-session` 是三仓里的会话域服务。它拥有聊天窗口、消息、run、
浏览器事件、SSE 和 replay 语义。

它不执行 agent，不渲染 UI，不读取 agent checkpoint。

## V1 能力范围

V1 session 必须支持：

- sessions / messages / runs / session_events。
- 同 session 单 active run。
- 创建 `AgentRunInput` 并投递给 agent。
- 接收 agent raw events 并归一化为 browser-facing session events。
- Mongo 长期持久化。
- 不使用 SQLite runtime。
- Redis run queue、raw event stream、live fanout、locks。
- SSE live + replay。
- HITL control 透传。

V1 不要求：

- 复杂多 run 并发队列。
- 在 session 内执行 LLM/tool。
- Web 本地状态持久化。
- 读取 agent checkpoint/memory。

## 核心对象

```text
ChatSession
  siteId / sessionId / ownerUserId / title / activeRunId / status

ChatMessage
  siteId / sessionId / messageId / runId / role
  content / parts / attachments / status

AgentRun
  siteId / sessionId / runId / inputMessageId / assistantMessageId
  status / modelRef / execution / approvalPolicy / backendPolicy

SessionEvent
  siteId / sessionId / runId / eventId / sseId / event / payload / createdAt
```

Session 的聊天展示主数据是 `messages`，不是从 events 每次现折。
`session_events` 用于 live/replay/audit/debug。

## API

### `POST /sessions/:sessionId/messages`

发送用户消息并启动 run。

流程：

1. 先按 `(userId, sessionId, idempotencyKey)` 查重试命中。
2. 校验 SiteContext 和权限。
3. 校验同 session 无 active run。
4. 写 user message。
5. 创建 run，设置 `activeRunId`。
6. 构建 `AgentRunInput`。
7. XADD run request。
8. 返回 `runId`、`inputMessageId`、session 状态。

### `GET /sessions/:sessionId`

返回 session snapshot：

- session metadata
- messages
- activeRun
- 最近 activity projection
- eventWatermark

刷新、切换会话、SSE 失败恢复都先走 snapshot。
`eventWatermark` 是 snapshot 已包含的内部事件水位，只给服务端 attach
去重使用，Web 不把它保存成业务 cursor。

### `GET /sessions/:sessionId/stream`

SSE active run events。

规则：

- JSON payload 不暴露 `cursor`、`resumeId`、`eventPosition`。
- SSE `id:` 可以作为内部传输续点。
- EventSource 瞬断可自动使用 `Last-Event-ID`。
- 页面刷新不要求 web 带 `?after=`；刷新走 snapshot + attach。

当前实际路径是 `/stream`。如果将来改名为 `/events`，必须 session/web
一次性改净，不保留双路径兼容。

### `POST /sessions/:sessionId/runs/:runId/control`

HITL 控制：

- approve
- reject
- cancel
- respond/edit 以后按工具类型逐步开放

Session 只校验权限和 run 归属，然后写 Redis control stream。真正恢复执行由 agent 处理。

## Manifest 构建

Session 是产品上下文到 agent manifest 的边界。

Manifest 来源：

- SiteContext
- 当前 session messages 摘要或 context refs
- 用户选择的 model/mode
- 已启用 skills
- 已授权 MCP servers/tools
- storageBackend / executionSandbox policy
- execution/tool mode 和 approval policy
- trace context

Session 不应把所有历史全文无限塞给 agent；大上下文用摘要、窗口和 refs。

## 存储

Mongo:

- `kokoro_session.sessions`
- `kokoro_session.messages`
- `kokoro_session.runs`
- `kokoro_session.session_events`
- `kokoro_session.outbox`，可选，用于后续可靠投递

Redis:

- run request queue
- raw run events
- live bus
- control stream
- run request queue lease
- agent session lease

SQLite:

- V1 runtime 不支持。
- 测试使用 memory fake；Mongo 行为用集成测试覆盖。

MySQL:

- session runtime 不写聊天消息到 MySQL。
- 只在需要读取 SiteContext、权限、entitlement、model policy 等结构化
  业务上下文时通过上游服务使用。

## 排序和幂等

V1 简化规则：

- 同一 session 同时只有一个 active run。
- Session relay 串行消费该 run 的 raw events。
- Session 写 Mongo 的追加顺序是 replay 内部排序真源。
- SSE 单连接发送顺序就是 Web 渲染顺序。
- `eventId` 只做幂等去重，不排序。
- 不新增 `eventPosition` 字段。

Mongo ObjectId 通常可作为内部追加锚点，但不要把它暴露成产品 API。
`sseId` 是传输 replay anchor，`eventId` 是幂等去重锚。

如果未来开放同 session 多 active run 或并行 agent handoff，需要重新
设计排序模型，不能偷偷复用 V1 规则。

## SSE 和 Replay

实时路径：

1. agent 写 Redis raw event。
2. session relay 阻塞读取。
3. session 写 Mongo session_event，并更新 messages/runs 投影。
4. terminal event 同 commit 更新 run terminal，清 activeRunId。
5. session 写 Redis live bus。
6. SSE 推给 web。

恢复路径：

1. web `GET /sessions/:sessionId` 读取 snapshot。
2. 若有 active run，web 打开 SSE。
3. session 先捕获 Redis live stream tail id。
4. session 从 Mongo replay snapshot 水位或 Last-Event-ID 之后的事件。
5. session 再从 captured tail id 之后 tail live bus。
6. web 按 `eventId` 去重。

系统不靠轮询 Mongo 追 token。

## 与 Skills/MCP 的关系

Session 不执行 skill/MCP，但负责把“本次 run 可用什么”写入 manifest：

- 哪些 skills 已启用。
- 哪些 MCP server 已授权。
- 哪些 MCP tools 可用。
- 这些能力在当前 site/workspace/project 是否可见。

Session 不保存 MCP 凭据明文；只传安全引用或短期 token。

## 性能

- messages 投影按 delta 节流更新，completed 时写完整内容。
- session_events 可以记录 micro-batch 后的 delta，不按每字符写。
- live bus bounded，历史由 Mongo 补。
- snapshot 分页加载 messages，避免大 session 一次性读全量。

## 风险

- 把 events 当唯一聊天历史，导致展示和查询都要重放。
- Web 自己维护业务 resume cursor。
- Session 读取 agent checkpoint。
- Redis 变成长期消息库。
- 同 session 多 active run 未设计排序就开放。
