---
status: 🟢 accepted
version: 1.0.0
producer: kokoro-session
consumers:
  - kokoro-web
upstream-producer:
  - kokoro-agent
backward-compatibility: Additive fields and additive event types are allowed in minor updates; renaming or removing fields requires a new major version.
---

# Session Stream

> 定义 `kokoro-session -> kokoro-web` 的标准事件流。浏览器看到的不是 agent 原始内部状态，而是整理后的会话事件。

## Event envelope

每个 SSE event 都必须带统一 envelope：

```json
{
  "event": "message.delta",
  "event_id": "evt_01J...",
  "session_id": "ses_01J...",
  "conversation_id": "conv_01J...",
  "run_id": "run_01J...",
  "cursor": "1748428800-000012",
  "timestamp": "2026-05-28T12:00:00.000Z",
  "payload": {}
}
```

## Event families

### `session.created`
- **Purpose:** 会话壳创建成功，可用于挂载历史、标题、owner 等基础元信息
- **Required fields:** `session_id`, `conversation_id`, `owner_id`, `title`
- **Optional fields:** `workspace_id`, `created_by`, `initial_mode`
- **Producer repo:** `kokoro-session`
- **Consumer repo:** `kokoro-web`
- **Replay behavior:** 必须参与 replay，作为会话流起点

### `run.created`
- **Purpose:** 一次用户触发的执行开始
- **Required fields:** `run_id`, `session_id`, `input_message_id`
- **Optional fields:** `parent_run_id`, `trigger`
- **Producer repo:** `kokoro-session`
- **Consumer repo:** `kokoro-web`
- **Replay behavior:** 必须 replay

### `run.mode.selected`
- **Purpose:** 记录本次 run 的执行风格 / 信任档位
- **Required fields:** `run_id`, `execution_style`
- **Optional fields:** `product_mode`, `reason`
- **Producer repo:** `kokoro-session`
- **Consumer repo:** `kokoro-web`
- **Replay behavior:** 必须 replay；用于恢复 UI 标签和提示语

### `message.delta`
- **Purpose:** assistant 文本增量输出
- **Required fields:** `message_id`, `delta`, `role`
- **Optional fields:** `format`, `segment`
- **Producer repo:** `kokoro-session`
- **Consumer repo:** `kokoro-web`
- **Replay behavior:** 必须 replay；客户端按 `message_id` 归并

### `message.completed`
- **Purpose:** assistant 或 user message 完结
- **Required fields:** `message_id`, `role`, `content`
- **Optional fields:** `citations`, `token_usage`
- **Producer repo:** `kokoro-session`
- **Consumer repo:** `kokoro-web`
- **Replay behavior:** 必须 replay；用于幂等收敛最终内容

### `thinking.summary`
- **Purpose:** 暴露可给用户看的思考摘要，而不是原始 chain-of-thought
- **Required fields:** `run_id`, `summary`
- **Optional fields:** `stage`, `progress_label`
- **Producer repo:** `kokoro-session`
- **Consumer repo:** `kokoro-web`
- **Replay behavior:** 在 `thinking` 风格下 replay；`fast` 风格可缺省

### `tool.started`
- **Purpose:** 某个工具调用开始
- **Required fields:** `tool_call_id`, `tool_name`
- **Optional fields:** `display_label`, `input_summary`
- **Producer repo:** `kokoro-session`
- **Consumer repo:** `kokoro-web`
- **Replay behavior:** 必须 replay；用于折叠摘要块进入 loading 态

### `tool.completed`
- **Purpose:** 某个工具调用结束
- **Required fields:** `tool_call_id`, `tool_name`, `status`
- **Optional fields:** `result_summary`, `duration_ms`
- **Producer repo:** `kokoro-session`
- **Consumer repo:** `kokoro-web`
- **Replay behavior:** 必须 replay；用于折叠摘要块收敛成完成态

### `artifact.available`
- **Purpose:** 某个结构化产物已经可展示
- **Required fields:** `artifact_id`, `artifact_kind`, `title`
- **Optional fields:** `preview`, `open_target`, `share_target`
- **Producer repo:** `kokoro-session`
- **Consumer repo:** `kokoro-web`
- **Replay behavior:** 必须 replay；用于 AGUI / A2UI 卡片槽位

### `permission.required`
- **Purpose:** 当前 run 因权限问题挂起，等待用户决策
- **Required fields:** `request_id`, `decision_kind`, `message`
- **Optional fields:** `scope`, `suggested_default`
- **Producer repo:** `kokoro-session`
- **Consumer repo:** `kokoro-web`
- **Replay behavior:** 必须 replay；刷新后仍能复原挂起态

### `run.completed`
- **Purpose:** run 已完成，可安全收尾
- **Required fields:** `run_id`, `status`
- **Optional fields:** `final_message_id`, `artifact_ids`
- **Producer repo:** `kokoro-session`
- **Consumer repo:** `kokoro-web`
- **Replay behavior:** 必须 replay；客户端以此关闭 loading / streaming 状态

### `run.failed`
- **Purpose:** run 已失败
- **Required fields:** `run_id`, `error_kind`, `message`
- **Optional fields:** `retryable`, `request_id`
- **Producer repo:** `kokoro-session`
- **Consumer repo:** `kokoro-web`
- **Replay behavior:** 必须 replay；让错误态可恢复展示

## Notes

- `kokoro-agent` 的内部事件必须先被 `kokoro-session` 归一化，再转成以上流事件
- 富结果必须落到 `artifact.available` 或 message 内的结构化槽位，不能把所有东西都塞进 `message.delta`
