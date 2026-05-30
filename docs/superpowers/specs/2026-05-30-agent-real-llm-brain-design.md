# Agent Real-LLM Brain Design（流式脑 + provider 可插拔）

- **Date:** 2026-05-30
- **Status:** approved-by-user-delegation
- **Scope:** 把 `kokoro-agent` 的确定性 echo 脑换成真实 LLM 的**流式**产出（`text.delta`/`text.completed` + `run.failed`），provider 可插拔、默认启用一个。脑切换隔离在 agent 仓；`kokoro-session` / `kokoro-web` / `StreamPort` 不动。**工具调用 / 扩展思考 / DeepAgents 完整 loop 本轮不实现，但架构为其预留接口。**
- **Verification policy（用户明确）:** 不接真实 LLM 做测试，不需要 API key——全部用 LangChain `GenericFakeChatModel` 离线确定性验证。
- **Related:** `docs/protocol/agent-events.md`（v0.1.0，本轮无需改）、`docs/protocol/session-stream.md`、`docs/superpowers/specs/2026-05-30-pluggable-event-loop-design.md`

---

## 1. Goal

`kokoro-agent` 用真实 LLM **流式**产出原始 agent 事件，端到端能在已建链路上跑（agent → Redis → session 归一化 → SSE → web 逐 token 渲染）。本轮只点亮 `text.delta`/`text.completed`/`run.failed` 三个事件族；脑切换是 agent 仓内的隔离手术，下游零改动。

**本轮不做：** `tool.invoked/returned`、`thinking.summary`、DeepAgents 完整 agentic loop、真实 LLM 调用测试。

## 2. 架构：两个同构的可插拔轴

| 轴 | 选择器 | 适配 |
|---|---|---|
| 传输 | `KOKORO_STREAM_BACKEND=memory\|redis` | StreamPort（已建） |
| 脑 | `KOKORO_MODEL=<provider>:<model>` | ChatModel（本轮新增） |

- provider 可插拔靠 LangChain `init_chat_model("<provider>:<model>")`，天然支持 anthropic / openai / google 等。换 provider = 改 `KOKORO_MODEL` + 对应 `*_API_KEY`。
- 默认 `KOKORO_MODEL=anthropic:claude-sonnet-4-6`（默认启用一个）。

## 3. 组件改动（全在 kokoro-agent）

### 新增 `infrastructure/model.py`
- `make_chat_model() -> BaseChatModel`：读 `KOKORO_MODEL`（默认 `anthropic:claude-sonnet-4-6`）→ `init_chat_model(...)`。
- fail loud：provider 包缺失 / model 串非法 → 启动期抛明确错误，不静默退化。
- 测试不走这里——直接注入 `GenericFakeChatModel`。

### 改造 `run_agent.py`（唯一动的逻辑核心）
- 签名：`async def run_agent(req: RunRequest, model: BaseChatModel) -> AsyncIterator[AgentEvent]`（同步生成器 → 异步生成器；模型注入，便于 fake）。
- 流程：
  1. `yield run.started(seq=1)`
  2. `seq` 累加计数器；单一 `message_ref`（如 `"m1"`）。
  3. `async for ev in model.astream_events([("user", req.input)])`：
     - `ev["event"] == "on_chat_model_stream"` → 取 `ev["data"]["chunk"].content` 的**文本部分**。`content` 可能是 `str` 或 `list[dict]`（thinking/tool 时）——稳健提取：str 直接用；list 取 `{"type":"text"}` block 的文本，其它（thinking/tool_use block）本轮忽略。非空文本 → `yield text.delta(seq++, message_ref, text=<chunk>)`，并累加到完整文本。
  4. 流结束 → `yield text.completed(seq++, message_ref, text=<累加全文>)` → `yield run.completed(seq++, status="completed")`。
- 错误：整段包 `try/except`，任何异常（含 `asyncio.timeout` 超时）→ `yield run.failed(seq++, error_kind=<类名>, message=<str>)`，**不抛穿**。用 `asyncio.timeout(N)` 锁最长挂起（N 可配，默认如 120s）。

### 改造 `worker.py`
- `_handle_request`：`for event in run_agent(req)` → `async for event in run_agent(req, model)`。
- 模型来源：`_serve(port)` 启动时 `model = make_chat_model()` 注入；保持 worker 对脑的注入式依赖（不在 worker 里硬造模型，便于测试替换）。

### `pyproject.toml`
- 显式声明 `langchain-anthropic`（当前仅作 deepagents 传递依赖落在 .venv，须显式化，否则重锁可能丢）。保留 deepagents/langchain（下一轮用）。

## 4. 数据流（变的只有最左一格）

```
web POST ─▶ session 发 run.request ─▶ agent 真实模型 astream → N×text.delta ─▶ Redis
                                                                                  │
web 逐 token 渲染 ◀─ SSE ◀─ session 归一化(message.delta 按 message_id 流式归并) ◀─┘
```

`session` 的 Normalizer 本就把多个 `text.delta` 按 `message_id` 流式归并、幂等；`web` reducer 本就渲染增量 delta。**两者一行不改。**

## 5. 协议

本轮**不改协议**。`text.delta`（多 seq）、`text.completed`、`run.failed` 在 `agent-events.md` v0.1.0 已定义。`tool.*`/`thinking.summary` 也已在契约里，待后续点亮。

## 6. 错误处理

- 模型/网络异常、超时 → `run.failed{error_kind, message}` → session 映射 `run.failed` → web 可恢复错误态。
- 启动期缺 provider 包 / 非法 model 串 → fail loud 抛错。
- malformed run.request → 沿用现有 worker 逻辑（丢弃 + 日志），不崩。

## 7. 测试（离线、零 key、确定性）

统一用 `langchain_core.language_models.fake_chat_models.GenericFakeChatModel` 注入：
- **流式序列**：fake model 逐 token 产出 `["Hello", " ", "world"]` → 断言事件序列 `run.started → text.delta×N → text.completed(text=="Hello world") → run.completed`，seq 单调。
- **content 为 list**：构造 chunk.content 为 `[{"type":"text","text":...}]` 与混入 `{"type":"thinking"...}` → 断言只提取 text、忽略非文本 block。
- **空流**：fake model 产空 → 仍 `run.started → text.completed(text=="") → run.completed`，不崩。
- **错误路径**：注入一个 `astream_events` 抛异常的 fake → 断言产出 `run.failed{error_kind, message}` 且不抛穿。
- **worker 集成**：MemoryStreamPort + fake model，投 run.request → events 流出现完整流式序列；重复 run_id 幂等。
- **边界（CLAUDE.md 矩阵）**：超长文本、空字符串、单 token、异常类型分级。
- 维持「memory 后端 + fake model = 零基础设施跑通全部测试」。

DoD：`ruff check` / `pyright`（strict）/ `pytest` 全绿（含上述全部边界），无真实 LLM 调用、无 key、无网络。

## 8. 显式留下一轮（架构已就位，无需返工）

- `tool.invoked/returned`：`astream_events` 的 `on_tool_start`/`on_tool_end` 是现成钩子，给 agent 配工具即点亮。
- `thinking.summary`：`execution_style=="thinking"` → `ChatAnthropic(thinking={...})`，从 content 的 thinking block 映射。
- DeepAgents 完整 loop：在 `astream_events` 接口背后把"单模型调用"替换成 `create_deep_agent(...)` 图，churn 最小。
