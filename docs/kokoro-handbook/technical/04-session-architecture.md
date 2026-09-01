# Session 架构

> **状态：V1 物理会话记录，不是当前 GA target。**本页保留当前 `sessions/messages/runs/SSE` 的实现事实；其中
> `RunRequest.runtime`、Session 构造 `RuntimeConfig`、CapabilitySnapshot 或 Session 选择 Agent 的段落均不得作为
> 新实现输入。目标 Session 只拥有产品对话投影、admission、可信 `feature_key` 和安全 ProductEvent 投影；同一 thread 的
> Agent 会话执行态由 GA checkpoint 中的 DeepAgents 原生 state 或 official `SwarmState` 持有。先读
> [36 GA 总体方案](36-ga-final-agent-technical-plan.md)、[38 公共运行契约](38-ga-public-runtime-contract.md)、
> [ADR-015](../decisions/ADR-015-agent-state-and-feature-context.md)、
> [ADR-018](../decisions/ADR-018-ga-thread-context-compaction-and-memory.md) 和
> [kokoro-session 目标模块](../modules/kokoro-session.md)。

三仓 V1 运行时总方案见：
[Agent / Session / Web V1 标准运行时方案](11-agent-session-web-v1-runtime.md)。
三仓通用聊天链路见：
[Agent / Session / Web 通用聊天运行链路](../business-flows/agent-session-web-general-chat-runtime.md)。

## 定位

`kokoro-session` 的下列内容是 V1 物理实现，不代表当前目标 owner。目标架构中，GA 新增独立的
`chat_messages/chat_events`，作为用户聊天历史与实时 replay 的 canonical 来源；Session 只拥有 ProductSession、
鉴权、Chat API facade、snapshot 和 AG-UI/SSE 投影。

它不执行 agent，不渲染 UI，不读取 agent checkpoint。

## 目标能力范围

```text
ProductSession / active run admission。
通过 Root generated contract 发送 Launch/Control/Fork/Cleanup。
从 GA chat_messages 读取历史，从 GA chat_events 读取 replay/live。
AG-UI/SSE 鉴权、cursor 与产品投影。
Studio Job/Artifact 的 JobRef-keyed 卡片投影。
```

不支持 session SQLite runtime；同一 Session 只允许一个 active Run。

## 核心对象

```text
ProductSession
  session_id / tenant_ref / subject / feature_key / active_run_id / lifecycle

SessionRunView (GA Run 的产品投影)
  session_id / run_id / state / projected_seq / terminal

ChatHistoryView / ChatEventView
  由 GA chat_messages/chat_events 查询结果映射而来；不是 Session canonical store
```

Session 的聊天展示来自 GA `chat_messages`；实时/replay 来自 GA `chat_events`。
Session 自己只保留产品投影和 cursor，不再维护第二份 canonical 消息/事件表。

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

## Launch 请求

Session 只构建 Root `LaunchRunRequest` 的产品输入与可信身份：

```text
feature_key + session_id
ExecutionIdentity (tenant_ref + actor + subject + assertion)
用户输入 content + Storage AssetRef[]
可选 requested_model_label / billing_ref / trace_ref
```

GA 自己把 `session_id` 映射为 LangGraph `thread_id`；Session 不传 thread/namespace selector。

## 存储

Session DB（仅产品元数据与投影）:

```text
sessions
session_run_views
session_message_views (可选缓存，不是 canonical)
session_event_cursors
```

上表仅保留历史代码考古。目标实现不把 `messages/session_events` 作为 canonical 聊天事实，也不读取或修改
LangChain/DeepAgents checkpoint 表；GA 自己的 `chat_messages/chat_events` 归 `kokoro-agent` 的 GA 存储边界。

Redis:

```text
live publish / replay hint
control forwarding
projection lease keys
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
