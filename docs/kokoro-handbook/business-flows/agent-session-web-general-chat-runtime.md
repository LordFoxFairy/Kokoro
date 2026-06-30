# Agent / Session / Web 通用聊天运行链路

本文只描述 `kokoro-web`、`kokoro-session`、`kokoro-agent` 三仓内部运行链路。
账务、支付、模型目录、站点解析和后台运营只作为外部前置条件，不在本文展开。

P0 字段模型、权限拆分、snapshot DTO、HITL control 和 runtime subagent gate
见 [Agent / Session / Web P0 实施设计](../technical/12-agent-session-web-p0-implementation-design.md)。

## 目标

用户在 Web 发送一条消息后，系统创建一个可恢复、可审计、可取消的
agent run，并把最终回复沉淀为 session messages。

## 当前状态

当前代码不是完整闭环，必须先处理 P0 阻断：

```text
1. session 已发布 agent_run_input manifest，但 agent 仍接受旧扁平 RunRequest。
2. session 已有 GET /sessions/:id snapshot，但 web 尚未 snapshot-first hydrate。
3. agent 尚未完整实现 MCP/skills/backendPolicy/sandbox manifest。
```

本文下面描述的是 V1 目标链路；实现时不得把上述阻断当作已完成。

## 参与模块

```text
kokoro-web
  用户输入、POST message、snapshot hydrate、EventSource、render reducer、HITL UI。

kokoro-session
  session/messages/runs/events 事实源，active run admission，
  AgentRunInput 构建，raw event normalize，SSE replay/live。

kokoro-agent
  consume run.request，DeepAgents/LangChain 执行模型、tools、HITL、subagents，
  输出 AgentEvent。
```

## 前置条件

```text
SiteContext 已由上游解析并传入 session。
用户有访问 session 的权限。
Session 连接 Mongo + Redis。
Agent 连接 Redis。
Production agent checkpoint/run_state 使用可共享后端。
同 session 没有 active run，或本请求命中同 idempotencyKey。
session 与 agent 的 run.request 契约已合流。
```

## 主流程

1. 用户在 `kokoro-web` composer 输入消息并提交。
2. Web 生成 `idempotencyKey`。
3. Web 调用 `POST /sessions/:sessionId/messages`。
4. Session 校验 SiteContext/user/session 权限。
5. Session 先检查 `idempotencyKey` 是否命中旧请求。
6. 未命中时，Session 用 `activeRunId` 做同 session 单 active run admission。
7. Session 在 Mongo 中写 user `ChatMessage`。
8. Session 创建 assistant placeholder `ChatMessage`。
9. Session 创建 `AgentRun`，设置 `ChatSession.activeRunId`。
10. Session 构建 `AgentRunInput` manifest。
11. Session 严格校验 `run.request`。
12. Session 把 `run.request` 写入 Redis `kokoro:runs:requests`。
13. Web 收到 `runId` 和 message ids。
14. Web 目标态调用 `GET /sessions/:sessionId`，用 snapshot hydrate 本地 state。
15. Web 打开 `GET /sessions/:sessionId/stream` EventSource。
16. Agent worker 从 Redis 消费 `run.request`。
17. Agent 用 run_state `try_register(runId)` 防重复执行。
18. Agent 根据 `AgentRunInput` 构造 DeepAgents runtime。
19. Agent 使用 LangGraph checkpoint 记录运行态。
20. Agent 把模型 delta、thinking、tool、todo、subagent、HITL、terminal 转成 AgentEvent。
21. Agent 写 Redis `kokoro:run:{runId}:events`。
22. Session relay 串行读取该 run raw events。
23. Session strict parse AgentEvent；非法事件记录诊断并跳过。
24. Session normalize 成 browser-facing `SessionEvent`。
25. Session DB-first 写 Mongo `session_events`。
26. 若是 `message.completed`，Session 更新 assistant message final content。
27. 若是 terminal event，Session 同事务更新 run terminal status 并清 `activeRunId`。
28. DB commit 成功后，Session publish 到 Redis `kokoro:session:{sessionId}:live`。
29. SSE endpoint 把事件推给 Web。
30. Web strict parse transport event；单条 malformed event skip-and-continue。
31. Web mapper 转成 render event。
32. Web reducer 按 `eventId` 去重。
33. Web 按接收顺序 append step 或就地更新 tool/subagent step。
34. `message.completed` 到达时，Web 用最终内容覆盖 delta。
35. 本轮 `run.completed` / `run.failed` 到达时，Web 关闭本轮 live handle。

## HITL 流程

```text
1. Agent 通过 HumanInTheLoopMiddleware 产生 interrupt/action_requests。
2. Agent 输出 tool_call_awaiting，保留 action_requests 原始顺序。
3. Session normalize 为 tool.awaiting_approval。
4. tool.awaiting_approval 带 approvalBatchId、ordinal、actionName、args
   preview、allowedDecisions。
5. Web 渲染 approve/reject/cancel 控件。
6. 用户决策后，Web POST /sessions/:sessionId/runs/:runId/control。
   resume body 只表达结构化 decisions，不伪装成普通用户消息。
7. 同一批多个 decision 必须按 ordinal 升序提交。
8. Session 校验 run 属于该 session/site/user。
9. Session 转发 run.resume 或 run.cancel 到 Redis 请求流。
10. Agent 从 checkpoint 恢复同一 LangGraph thread。
11. Agent 按 action_requests 原始顺序恢复 decisions。
12. Agent 输出 tool resolution 或 cancelled/failed terminal event。
```

当前 web UI 只实现 approve/reject/cancel；edit/respond 是 wire 能力，UI 仍未完成。

## 刷新和断线恢复

目标态：

```text
页面刷新：
  Web -> GET /sessions/:sessionId
  Web 用 snapshot 重建 thread/activity。
  若 activeRun 存在，Web -> EventSource /sessions/:sessionId/stream。

EventSource 瞬断：
  浏览器使用标准 Last-Event-ID 自动重连。
  Session 用 Last-Event-ID 作为 replay anchor。
  Web domain 不保存 lastResumeId。

Last-Event-ID 缺失或未知：
  Session 可全量 replay。
  Web 用 eventId 去重。
```

当前 web 仍是直接 reattach `/stream`，snapshot-first hydrate 是 P0。

不允许：

```text
Web 拼 ?after=<lastResumeId> 自定义续传协议。
Web 保存业务 cursor。
Session 轮询 Mongo 追 token。
```

## 数据变化

### Mongo: `kokoro_session`

```text
sessions
  activeRunId: null -> runId -> null。

messages
  新增 user message。
  新增 assistant placeholder。
  completed 时写最终 assistant content。

runs
  queued/running/awaiting/completed/failed/cancelled/timeout。

session_events
  写 browser-facing events，用于 replay/live/audit。

outbox
  目标态用于 DB commit 后可靠 publish live；当前仍是 placeholder。
```

### Redis

```text
kokoro:runs:requests
  run.request / run.resume / run.cancel。

kokoro:run:{runId}:events
  AgentEvent raw stream。

kokoro:session:{sessionId}:live
  session live events，有界窗口。
```

### Web 本地

```text
localStorage/sessionStorage
  draft、activeId、本地 conversation cache、pendingRunId、UI 状态。
```

Web 本地状态可丢弃，不能作为事实源。

## 幂等和一致性

```text
POST message:
  sessionId + userId + idempotencyKey。

Run claim:
  runId via agent run_state。

同 session 串行:
  session activeRunId admission。

Session event:
  eventId unique index。

Replay:
  Last-Event-ID / SSE id 是传输层续点。
  eventId 是去重锚点。

排序:
  V1 单 active run。
  session replay 用 Mongo append order。
  web render 用 SSE 单连接发送顺序。
```

## 异常流程

```text
同 session 已有 active run:
  返回 session_run_active / HTTP 409。

idempotencyKey 重试:
  返回首次创建的 messageId/runId，不重复写消息。

run.request 投递失败:
  run 标记 enqueue_failed，清 activeRunId。

agent worker 崩溃:
  run_state/checkpoint 支撑恢复或重新 claim。

session relay 崩溃:
  已落 Mongo 的 event 可 replay。
  未落 Mongo 的 event 不应已发送给 Web。

malformed raw event:
  记录诊断，跳过，不污染 Mongo。

用户取消:
  Web -> session control cancel -> agent run.cancel -> run.completed(status=cancelled)
  或 run.failed。
```

## 用户可见结果

```text
用户消息立即出现在 thread。
assistant delta 流式出现。
thinking/tool/todo/subagent 出现在 activity/assistant turn 内。
待审批工具显示 approve/reject。
取消后 pending tools 本地收口，并等待权威 terminal event。
最终 assistant message 由 message.completed 覆盖。
```

## 验收标准

```text
1. session 发出的 run.request 能被 agent Python strict parse。
2. POST /messages -> agent raw events -> session Mongo -> SSE -> web reducer 端到端通过。
3. 刷新后 web 先 snapshot hydrate，再 attach active run。
4. 不存在 seq、lastResumeId、?after= 的产品协议。
5. Redis 清掉 live 窗口后，snapshot/replay 仍能恢复历史。
6. 同 session 并发消息只允许一个 active run。
7. malformed event 不污染 thread，不杀服务循环。
```
