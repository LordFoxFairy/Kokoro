---
status: 🟢 accepted
version: 2.0.0
producer: kokoro-session
consumers:
  - kokoro-web
upstream-producer:
  - kokoro-agent
wire-format: A2UI v0_9 operation stream（自 v2.0.0 起；catalog `kokoro/chat/v1`）
backward-compatibility: v2.0.0 是 major 变更——线上格式由自研 AGUI envelope 改为 A2UI op 流。下方 AGUI 事件族降级为 session 内部表示（`SessionEvent`），不再是浏览器看到的线上格式。
---

# Session Stream

> 定义 `kokoro-session -> kokoro-web` 的事件流。浏览器看到的不是 agent 原始内部状态，而是整理后的会话事件。

## v2.0.0 — A2UI op 流（当前线上格式）

自 v2.0.0 起，`kokoro-session -> kokoro-web` 的**线上格式**是 **Google A2UI v0_9 的 operation 流**（agent 驱动 UI：服务端吐 UI 描述，客户端用白名单 catalog 组件渲染）。详见 spec `docs/superpowers/specs/2026-05-30-chat-shell-a2ui-design.md`。

- **op 子集**：`createSurface{surfaceId, catalogId}`、`updateComponents{surfaceId, components:[{id, component, ...}]}`、`updateDataModel{surfaceId, path?, value}`。每个 op 形如 `{"version":"v0.9", <opKey>:{...}}`。
- **catalog `kokoro/chat/v1`** 组件白名单：
  - `Thread{children:[id...]}` — 对话滚动容器，按 children 顺序竖排。
  - `Message{author:"user"|"ai", text:{path}}` — 用户右气泡 / AI 左无气泡叙述流（ADR-008）。文本走 dataModel 绑定。
  - `ThinkingBlock{summary:{path}}` — 可折叠思考块。
  - `ToolCard{toolName, status:"running"|"ok"|"error"}` — 工具卡，running→done。
  - `Plan{todosPath:{path}}` — CC/Gemini 式 todo 清单（`pending ○` / `in_progress ◐` / `completed ✓`）；原地更新（dataModel 整列替换）。todos = `[{content, status}]`。
- **harness 约定（write_todos→Plan）**：session 归一化器识别 agent 的 `tool.invoked{tool_name:"write_todos"}`（agent 通用、不认识 plan）→ 取 `args.todos` 产**内部** `plan.updated{plan_id:"{run_id}:plan", todos}` 会话事件、并**吞掉**该工具的工具卡（不发 `tool.started/completed`）；projector 把 `plan.updated` 投影成上面的 `Plan` 组件。对标 Claude Code：TodoWrite/Task 是工具，由 harness 识别并特殊渲染。
- **SSE 封装**：沿用 `/sessions/{id}/stream`；每条 SSE 行 `event: a2ui.op`，`data:` 为单条 op JSON，`id:` = `{cursor}:{opSeq}`（来源 SessionEvent 游标 + 该事件产出的 op 序号）。
- **流式文本**：用 `updateDataModel` 覆盖累计值（renderer 显示最新值），不做字符级 patch。
- **谁渲染**：`kokoro-web` 用 `@a2ui/react` + `@a2ui/web_core` + 自定义 `kokoro/chat/v1` catalog（组件用自家 BEM/设计 token 实现）；`MessageProcessor.processMessages()` 增量喂 op，`<A2uiSurface>` 内置 signals 自动增量重渲染。

### 内部表示与归一化职责（不变）

session 内部仍由 `Normalizer` 把 agent 原始事件（见 `agent-events.md`）归一化成下方的 **AGUI `SessionEvent`**（内部表示，落 replay）；再由 `A2uiProjector` 把有序 `SessionEvent` 流**投影**成 A2UI op 流发到 SSE。即：

```
agent 原始事件 ─▶ Normalizer ─▶ SessionEvent（内部, 见下方事件族）─▶ A2uiProjector ─▶ A2UI op 流 ─▶ SSE ─▶ web
```

- replay 仍存 `SessionEvent`；重连时每个连接 new 一个 projector，按序重放 snapshot+tail → 确定性重建 op 流（**重连从头重放；断连中点续传留后轮**）。
- 幂等仍按 `(run_id, seq)` 在 Normalizer 收敛。

> 下面「Event envelope / Event families」描述的是 **v2.0.0 的内部 `SessionEvent` 表示**（v1.0.0 时它曾是线上格式，现 superseded-by A2UI op 流）。`A2uiProjector` 的事件→op 映射见 spec 第 7 节。

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
- **Required fields:** `request_id`, `decision`, `message`
- **Optional fields:** `scope`, `suggested_default`, `options`, `kind`, `danger_level`
- **Producer repo:** `kokoro-session`
- **Consumer repo:** `kokoro-web`
- **Replay behavior:** 必须 replay；刷新后仍能复原挂起态
- **UI contract:** `kokoro-web` 将其渲染为 timeline 中的 `PermissionCard`，它是 specialized ask card / constrained decision form，而不是通用问答表单或 composer 邻近 banner

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

- `kokoro-agent` 的内部事件必须先被 `kokoro-session` 归一化成上述 `SessionEvent`（内部表示），再由 `A2uiProjector` 投影成 A2UI op 流发到 web（见本文件 v2.0.0 节）
- 富结果必须落到 `artifact.available` 或 message 内的结构化槽位，不能把所有东西都塞进 `message.delta`
- 当前 `kokoro/chat/v1` catalog 尚未覆盖 `artifact.available` / `permission.required` 的对外渲染（canvas 产物面板、权限交互留后轮）；这些 `SessionEvent` 仍会 replay，但本轮投影器不产对应 op
