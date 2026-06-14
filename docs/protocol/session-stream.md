---
status: 🟢 accepted
version: 1.0.0
producer: kokoro-session
consumers:
  - kokoro-web
upstream-producer:
  - kokoro-agent
backward-compatibility: Additive optional payload fields and additive event types require synchronized spec and consumer updates; removing or renaming fields requires a new major version.
---

# Session Stream

> 定义 `kokoro-session -> kokoro-web` 的最小标准事件流。浏览器看到的不是 `kokoro-agent` 的原始内部状态，而是 `kokoro-session` 归一化后的会话事件。

## Current minimal closed loop

当前 `v1.0.0` 的最小闭环只要求以下事件族，并且它们是今天由 `kokoro-session` 发出、由 `kokoro-web` 收敛到浏览器可见状态的主干：

- `session.created`
- `run.created`
- `message.delta`
- `message.completed`
- `run.completed`
- `run.failed`

## Reserved browser-facing families

浏览器传输层当前还可以为前向兼容而 parse-and-ignore 以下事件族：

- `artifact.available`
- `permission.required`

它们现在是**已保留但未升格**的浏览器侧扩展名：`kokoro-web` 可以接受并忽略，`kokoro-session` 的当前最小 producer contract 不要求发出，也不应被贡献者当作当前闭环能力依赖。

如果后续要把这些保留族升格为当前合同的一部分，或新增 `tool.*` / thinking 一类事件，必须先同步更新 spec、`kokoro-session` producer schema/tests、以及 `kokoro-web` consumer schema/tests，再把它们写进这份契约。

## Event envelope

每个 SSE event 都必须带统一 envelope：

```json
{
  "event": "message.delta",
  "event_id": "evt_0003",
  "session_id": "ses_01",
  "conversation_id": "conv_01",
  "run_id": "run_01",
  "cursor": "run_01:0003",
  "timestamp": "2026-05-30T00:00:00.000Z",
  "payload": {}
}
```

### Envelope notes

- `session_id` / `conversation_id` / `run_id` 始终放在 envelope 顶层。
- `payload` 只承载事件自身字段；当前最小合同里仍允许少量边界 ID 在 payload 中重复出现，只要 producer 与 consumer 继续按这份 spec 保持一致。
- `cursor` 由 `kokoro-session` 生成并保证单调递增，用于 replay / resume 收敛。

## Event families

### `session.created`
- **Purpose:** 会话壳创建成功，可用于挂载标题和基础 owner 元信息。
- **Required payload fields:** `session_id`, `conversation_id`, `owner_id`, `title`
- **Current producer behavior:** 当前最小实现会在该 session 首次 `run.started` 被归一化时发出一次。
- **Replay behavior:** 必须参与 replay，作为会话流起点。
- **Guardrail:** `title` 是必填字段；当前实现若没有更丰富标题，会先用 `conversation_id` 填充，不能省略。

### `run.created`
- **Purpose:** 标记一次 run 已经开始。
- **Required payload fields:** `run_id`
- **Optional payload fields:** none in the current minimal contract
- **Current producer behavior:** 当前最小实现会为每次被接受的 `run.started` 发出 `run.created`。
- **Replay behavior:** 必须 replay。
- **Guardrail:** `session_id` / `conversation_id` / `run_id` 已在 envelope 顶层出现；当前 payload 不再要求 `input_message_id`、`parent_run_id` 或 `trigger`。

### `message.delta`
- **Purpose:** assistant 文本增量输出。
- **Required payload fields:** `message_id`, `delta`, `role`
- **Optional payload fields:** none in the current minimal contract
- **Current producer behavior:** 当前最小实现只发 `assistant` role。
- **Replay behavior:** 必须 replay；客户端按 `message_id` 归并。

### `message.completed`
- **Purpose:** 一条 message 收敛为最终内容。
- **Required payload fields:** `message_id`, `role`, `content`
- **Optional payload fields:** none in the current minimal contract
- **Replay behavior:** 必须 replay；用于幂等收敛最终内容。

### `run.completed`
- **Purpose:** run 已完成，可安全收尾。
- **Required payload fields:** `run_id`, `status`
- **Current value in minimal contract:** `status` 当前按 `"completed"` 收敛给 web consumer。
- **Replay behavior:** 必须 replay；客户端以此关闭 streaming 状态。

### `run.failed`
- **Purpose:** run 已失败。
- **Required payload fields:** `run_id`, `error_kind`, `message`
- **Optional payload fields:** none in the current minimal contract
- **Replay behavior:** 必须 replay；让错误态可恢复展示。

## Notes

- `kokoro-agent` 的原始执行事件先进入 `kokoro-session`，再由 `kokoro-session` 归一化成这份浏览器契约。
- 浏览器侧最先要对齐的是 `kokoro-web` 的传输层 schema 和 replay reducer，而不是直接消费 agent 事件。
- 这份文档区分两层：一层是当前已落地并被测试覆盖的最小闭环；另一层是浏览器当前已保留、可 parse-and-ignore 的事件族。
- 未列入“Current minimal closed loop”的事件，不应被视为今天必须由 producer 发出的保证。
