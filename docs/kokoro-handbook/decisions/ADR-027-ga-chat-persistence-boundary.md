# ADR-027 GA 聊天持久化与 LangGraph 原生状态隔离

状态：历史 GA/Session 设计，已被当前 `kokoro-bff` Chat 业务边界取代（2026-09-01）。本文仅保留数据归属讨论，不作为当前仓库拓扑或接口实现依据。

## 背景

GA 需要保存用户可见的聊天历史，并保证实时事件在 Redis/SSE 断线、消费失败或 Session 重启后仍可补发。
这部分数据不能写入或改造 DeepAgents/LangGraph 的 checkpoint 存储：checkpoint 中的 `messages`、
`Message.id`、`thread_id`、`checkpoint_id` 和 `tool_call_id` 是框架自己的执行协议。

此前把 `run_events`、`conversation_messages`、`event_outbox` 和 `checkpoints` 并列描述，混淆了三件事：
框架原生状态、GA 执行事实和用户聊天投影。首发只定义 GA 自己的聊天存储，不复制 LangChain 表，也不把
内部 raw AgentEvent 直接暴露给 Session/Web。

## 决策

### 1. LangChain/DeepAgents 存储完全由框架拥有

GA 只通过公开 checkpointer API 读写 native state，不读取其内部表结构，不增加字段，不替换 native message ID。

```text
DeepAgents/LangGraph checkpoint
  -> DeepAgents native state / official SwarmState
  -> Agent loop、resume、tool-call 关联、原生消息去重
```

外部 `user_message_id` 或 GA `chat_message_id` 不得直接赋值给 `HumanMessage.id`。如果需要排查关联，
只保存一个 opaque `native_message_ref`，它不参与恢复或排序。

### 2. GA 只新增两类聊天数据

```text
chat_messages
  用户可见的完整消息，Chat history 的来源

chat_events
  用户可见的有序增量/状态事件，实时流和断线 replay 的来源
```

`chat_messages` 是逻辑消息记录，保存 user/assistant 的最终内容和状态；`chat_events` 是 append-only 的安全
聊天事件记录，保存 `started`、`delta`、`completed`、`activity`、`terminal` 等产品事件。raw thinking、
raw tool args/results、subagent 内文和 sandbox 细节不进入这两类数据。

最小字段：

```text
chat_messages:
  chat_message_id, session_id, run_id, role, content, status, seq, created_at, updated_at

chat_events:
  chat_event_id, session_id, run_id, chat_message_id?, seq, event_type, payload, created_at,
  （不携带 Redis publish 状态；发布/重放由 durable event 查询游标和 transport 负责）
```

GA 自己生成 `chat_message_id`、`chat_event_id` 和 `seq`；它们与 LangChain 的 native ID 完全分离。

### 3. `chat_events` 同时承担 durable outbox 语义

`event_outbox` 不是新的业务表。GA 先把安全 `chat_event` durable 写入，再通过 Redis 广播；广播失败时，
按 `(session_id, seq)` 从 `chat_events` replay。Redis publish 状态不写回聊天事实；重试/水位由
GA/Session transport 的游标和幂等键负责，避免把传输状态混入用户历史模型。

```text
Agent output
  -> GA chat_events durable write
  -> Redis live publish
  -> chat_messages projection/update
```

Redis 只负责低延迟传输，不承担历史真相。Session/Web 断线重连使用 `after_seq` 或 Last-Event-ID 读取 GA
聊天事件；不会因为页面断开而创建新 Run、修改 checkpoint 或重复 provider 调用。

### 4. Session 是产品 API 与权限门，不是聊天事实源

Session 仍拥有 ProductSession、Feature admission、当前 actor 授权和 Chat API；但消息历史和聊天事件由 GA
保存。Session 可以做轻量缓存或 UI projection，但不能形成第二份 canonical message/event store。

```text
Session Chat API
  -> GA chat_messages / chat_events query contract

GA ProductEvent/raw execution
  -> 只按允许的聊天语义写 chat_events
```

已有 Root `kokoro.chat.v1` 的 `Message`、`BrowserSessionEvent`、snapshot 和 stream DTO 可以继续作为跨仓
接口类型；契约文档需要明确这些是 GA chat store 的读取/投影结果，而不是 LangGraph checkpoint 的镜像。

### 5. 不新增重复数据面

首发不定义以下并列存储：

```text
conversation_messages
run_events
event_outbox
Session canonical messages
LangChain message mirror
```

GA 的 RunLedger 继续保存 Run、租约、控制、计费和 effect 事实；它不替代 `chat_messages`，也不保存 raw
聊天流。框架 checkpoint 继续保存 native execution state；它不替代聊天历史。

## 链路不变量

```text
LangChain native IDs never become GA chat IDs.
GA chat_messages is the only canonical user-visible history source.
GA chat_events is the only canonical user-visible live/replay source.
Redis is transport only; a Redis loss never deletes chat history.
Session may authorize/query/project, but never creates a second canonical chat store.
Raw AgentEvent and native checkpoint payload are never returned by the Chat contract.
```

## 子仓库落点

```text
Root contract/
  定义 Chat Message、Chat Event、history/query、stream/replay 的跨仓契约

kokoro-agent/
  写 chat_messages/chat_events；将 native agent output 转成安全聊天事件

kokoro-session/
  保留产品 Session、鉴权和 Chat API facade；从 GA 读取 history/replay，不再作为消息事实源

kokoro-web/
  只消费 Session/AG-UI 投影，不读取 checkpoint 或 raw AgentEvent
```
