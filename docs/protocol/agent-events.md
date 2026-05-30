---
status: 🟡 draft
version: 0.2.0
producer: kokoro-agent
consumers:
  - kokoro-session
transport: Redis Stream / PubSub（可插拔 StreamPort，开发期可用内存适配器）
backward-compatibility: Additive fields and additive event types are allowed in minor updates; renaming or removing fields requires a new major version.
---

# Agent Events

> 定义 `kokoro-agent -> kokoro-session` 的**上游原始事件**契约。这是 agent 吐出的“执行侧”事件，**不是**浏览器看到的 AGUI 流。
> `kokoro-session` 负责把这里的原始事件**归一化**成 `session-stream.md` 的 AGUI 信封，再经 SSE 发给 `kokoro-web`（见 session-stream.md 第 133 行）。

## 设计原则

- **agent 保持纯粹**：只描述“执行发生了什么”，不分配 `event_id` / `cursor`，不填 `owner_id` / `title` 等会话归属字段——那些是 session 的业务职责。
- **session 拥有归一化**：cursor、事件去重、AGUI 字段补全、replay 落库都在 session。
- **传输可插拔**：本协议不绑定具体中间件。运行时通过 `StreamPort` 选择后端（`memory` 单进程/测试，`redis` 跨语言端到端）。

## Transport / 命名

通过 `StreamPort` 抽象，后端由 `KOKORO_STREAM_BACKEND=memory|redis` 选择。

| 用途 | 逻辑流名 | 写入方 | 读取方 |
|---|---|---|---|
| run 请求队列 | `kokoro:runs:requests` | kokoro-session | kokoro-agent（consumer group） |
| run 事件流 | `kokoro:run:{run_id}:events` | kokoro-agent | kokoro-session |

- `redis` 后端：用 Redis Streams（`XADD` / `XREADGROUP`），entry id 即天然游标。
- `memory` 后端：进程内 append-only 列表 + 单调序号，仅在**单进程**内有效（无法跨 Python↔TS）。

## Run request envelope（session -> agent）

写入 `kokoro:runs:requests`：

```json
{
  "kind": "run.request",
  "run_id": "run_01J...",
  "session_id": "ses_01J...",
  "conversation_id": "conv_01J...",
  "input": "hello kokoro",
  "execution_style": "fast"
}
```

- **Required:** `kind`, `run_id`, `session_id`, `conversation_id`, `input`
- **Optional:** `execution_style`(默认 `fast`)
- `run_id` 由 session 生成并拥有；agent 不自造 run_id。

## Agent event envelope（agent -> session）

写入 `kokoro:run:{run_id}:events`。agent 只填执行语义字段：

```json
{
  "kind": "text.delta",
  "run_id": "run_01J...",
  "seq": 12,
  "payload": {}
}
```

- **Required:** `kind`, `run_id`, `seq`（agent 侧单调序号，session 据此排序/去重）
- agent **不**产生 `event_id` / `cursor` / `timestamp`（由 session 归一化时分配）。

### Agent event kinds

| `kind` | payload required | 含义 | session 映射到 AGUI |
|---|---|---|---|
| `run.started` | — | 一次执行开始 | `run.created`（+ `session.created` 若会话首次出现） |
| `thinking.delta` | `text` | 思考过程增量（仅 `execution_style="thinking"`） | 累加，run 结束/思考结束时归一成一条 `thinking.summary`（`summary`=可展示文本，不是原始 chain-of-thought） |
| `text.delta` | `message_ref`, `text` | assistant 文本增量 | `message.delta`（`message_id`=映射后的稳定 id, `delta`=text） |
| `text.completed` | `message_ref`, `text` | 文本消息完结 | `message.completed`（`content`=text） |
| `tool.invoked` | `tool_call_ref`, `tool_name` | 工具调用开始 | `tool.started` |
| `tool.returned` | `tool_call_ref`, `tool_name`, `status` | 工具调用结束 | `tool.completed` |
| `run.completed` | `status` | 执行成功收尾 | `run.completed` |
| `run.failed` | `error_kind`, `message` | 执行失败 | `run.failed` |

> `thinking.delta` 是 v0.2.0 新增（additive，向后兼容）。`tool.*`/`thinking.*` 的产出受 `execution_style` 与是否配置工具控制：`fast` 不产 thinking；无工具不产 tool.*。
> **顺序约束**：同一 run 内，`tool.invoked` 必先于对应 `tool.returned`（按 `tool_call_ref` 配对）；`thinking.delta` 出现在 `text.delta` 之前。session 按 `seq` 排序后再归一化。

- `message_ref` / `tool_call_ref` 是 agent 侧的局部引用；session 负责映射成对外稳定的 `message_id` / `tool_call_id`。

## 归一化职责（session 侧，规范约束）

1. 为每个对外事件分配 `event_id`、`cursor`(`{run_id}:{递增}`)、`timestamp`。
2. 补全 AGUI 信封必填字段（`session_id` / `conversation_id` / `owner_id` / `title` 等会话归属信息）。
3. 按 `seq` 幂等收敛（重复消费同一 `(run_id, seq)` 不得产生重复 AGUI 事件）。
4. 富结果落 `artifact.available` 或结构化槽位，不塞进 `message.delta`。

## 边界条件（实现必须覆盖）

- 缺 `kind` / `run_id` / `seq` 的事件：Pydantic/Zod strict 拒绝，不得污染流。
- 重复 `seq`：幂等丢弃。
- 空流 / 中途断连：session 按已落 replay 继续，不崩。
- `run.failed` 之后不应再有该 run 的事件；若有，session 忽略并记日志。

## 与现有代码的差异（清理项）

当前 `kokoro-agent/run_agent.py` 直接产出 `session.created` / `message.delta` 等 **AGUI 信封事件**并自填 `owner_id="kokoro-agent"`——这违反本协议（越权进入 session 的归属/归一化职责）。改造后 agent 只产出上表的原始 `kind`。
