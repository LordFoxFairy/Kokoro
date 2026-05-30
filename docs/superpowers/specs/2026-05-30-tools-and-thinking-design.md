# Tools & Thinking Design（工具调用 + 思考，全栈 + ChatGPT/Gemini 式 UX）

- **Date:** 2026-05-30
- **Status:** approved-by-user-delegation（"全做 + 完成后通知我"）
- **Scope:** 点亮 `tool.invoked/returned` 与思考（`thinking.delta`→`thinking.summary`）两个事件族，端到端贯穿 agent→session→web，web 按 **ChatGPT/Gemini 对话**的方式渲染**可折叠工具卡 + 可折叠思考块**。agent 脑保持本地确定性/离线可测（含一个 `scripted` 脑供无 key 浏览器演示）。
- **Repos:** `Kokoro`(协议)、`kokoro-agent`、`kokoro-session`、`kokoro-web`
- **Related:** `docs/protocol/agent-events.md`（v0.2.0，本轮加 `thinking.delta`）、`docs/protocol/session-stream.md`（v1.0.0，`tool.started/completed`/`thinking.summary` 已定义，不改）、`docs/superpowers/specs/2026-05-30-agent-real-llm-brain-design.md`

---

## 1. Goal

让一次 run 能产生「思考 → 调工具 → 出答案」的完整事件序列，并在浏览器里以 ChatGPT/Gemini 的对话形态呈现：折叠思考块、运行中→完成的工具卡、流式正文。**全程离线可测、无需 API key**（fake / scripted 脑）。

**实现切片：** 先工具端到端，再 thinking 端到端，最后一起在浏览器验证。

## 2. 架构：Brain 抽象 + 工具注册表（DeepAgents-ready）

agent 内引入 `Brain`：输入 `RunRequest` + 注入的 chat model，输出 `AsyncIterator[AgentEvent]`。**Brain 自己跑工具循环并自埋点 `tool.invoked/returned`**（不依赖 langgraph 内部 on_tool_start/end——经验证 fake model 不支持 agent executor；但 `ainvoke` 能返回 `tool_calls`）。

- **工具注册表** `tools.py`：`name -> (schema, callable)`。起步给 1-2 个确定性工具（如 `echo_search(query)`、`now()`）。新增工具=注册一项，零散改动隔离。
- **可插拔脑**（呼应 `KOKORO_MODEL` / `KOKORO_STREAM_BACKEND`）：
  - `KOKORO_MODEL=<provider>:<model>` → 真实模型（`make_chat_model` 负责 `bind_tools`）。
  - `KOKORO_MODEL=scripted` → 一个本地确定性脚本脑，产出固定的 thinking→tool→text 序列，**供无 key 的离线浏览器演示**与默认启用。
- DeepAgents 留作未来引擎：在同一 `Brain` 接口背后把"手写循环"换成 `create_deep_agent`，churn 最小。

## 3. 各层改动

### 协议（已改）
`agent-events.md` v0.2.0 加 `thinking.delta {text}`；`tool.*` 已有。顺序约束已写入。

### kokoro-agent
- `tools.py`：工具注册表 + 1-2 个确定性工具。
- `brain.py`（或扩 `run_agent.py`）：工具循环——
  1. `run.started`
  2. 模型回合：若 `execution_style=="thinking"`，从 content 的 `{"type":"thinking"}` block → `thinking.delta`。
  3. 若返回 `tool_calls`：逐个 `tool.invoked{tool_call_ref,tool_name}` → 执行注册表工具 → `tool.returned{...,status}`，回填 ToolMessage，继续循环。
  4. 最终文本回合 → `text.delta`* → `text.completed`。
  5. `run.completed`；任何异常 → `run.failed`。`asyncio.timeout` 锁挂起。
- `make_chat_model()`：加 `scripted` 分支（返回脚本脑）；真实分支 `bind_tools(registry.tools)`。
- 全部 Pydantic strict；seq 单调；只产原始 kind。

### kokoro-session
- Zod schema 加 `tool.invoked/returned`、`thinking.delta`（discriminated union，strict）。
- Normalizer 加映射：`tool.invoked→tool.started`、`tool.returned→tool.completed`（按 `tool_call_ref` 映射成稳定 `tool_call_id`）；`thinking.delta` 累加 → run/思考结束时发 **一条** `thinking.summary{run_id, summary}`。幂等按 `(run_id, seq)` 不变。

### kokoro-web（ChatGPT/Gemini 式）
- 事件域 + 协议解析加 `tool-started`、`tool-completed`、`thinking-summary`。
- **reducer 升级为有序时间线**：`timeline: TimelineItem[]`，item 类型 = `message | tool | thinking`，按到达（cursor）顺序；`tool` item 有 `running|done` 态（started→running，completed→done）；`thinking` item 持 summary 文本。保留 eventId 幂等。`messages[]` 视图可由 timeline 派生或保留兼容。
- **SessionShell 渲染**：
  - 思考块：`💭 思考 ▸`（默认折叠，展开显示 summary）。
  - 工具卡：`🔧 {tool_name} ⟳→✓`（running 转圈，done 收成一行摘要，可展开看 input/output 摘要）。
  - 正文：assistant 消息流式（现有）。
  - 暖色 Kokoro 风格，贴合现有设计语言；新增小组件 `ThinkingBlock`、`ToolCard`。

## 4. 数据流

```
web POST ─▶ session run.request ─▶ agent Brain：
   run.started → [thinking.delta]* → [tool.invoked→exec→tool.returned]* → text.delta* → text.completed → run.completed
        └─ StreamPort ─▶ session 归一化(tool.*→tool.started/completed; thinking.delta→1×thinking.summary) ─▶ SSE ─▶ web 时间线渲染
```

## 5. 错误 / 边界
- 工具执行抛错 → `tool.returned{status:"error"}`（run 不必失败，除非致命）。
- 未知工具名 → `tool.returned{status:"error"}` + 日志，不崩。
- thinking 在 `fast` 风格下不产；无工具时不产 tool.*。
- session：缺字段 strict 拒绝；`tool.returned` 找不到配对 `tool.invoked` → 日志、忽略或补一个 started（择一，测试锁定）。
- web：工具卡 done 前 run 结束 → 卡停在 running 但不阻塞；thinking summary 缺失 → 不渲染思考块。

## 6. 测试（离线、无 key、确定性）
- **agent**：fake model 脚本（returns tool_calls then text；content 带 thinking block）→ 断言事件序列 `run.started→thinking.delta*→tool.invoked→tool.returned→text.delta*→text.completed→run.completed`；工具错误→`tool.returned{error}`；`fast` 不产 thinking；seq 单调；幂等。`scripted` 脑单测。
- **session**：normalize 映射单测（tool 配对成稳定 id、thinking 累加成 1 条 summary、原始思考不外泄超出 summary）；幂等。
- **web**：reducer 时间线单测（交错顺序、tool running→done、thinking 折叠数据）；**Playwright 截图**：用 `KOKORO_MODEL=scripted` 起三进程（memory 或 redis 后端），浏览器看到思考块+工具卡+正文，截图。
- DoD：四仓 LSP/linter 全绿、测试 100% pass（含 schema 崩塌/幂等/工具错误/顺序边界）、浏览器截图存档。无真实 LLM 调用。

## 7. 留待后续
- 真实 LLM 下的 tool/thinking（需 key）；DeepAgents 完整 loop 作为 Brain 引擎；thinking.summary 的真实「摘要化」（当前 summary==思考全文）；session-stream.md 增量 thinking（如需 live "thinking…"）。
