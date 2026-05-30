# Agent 引擎选型(DeepAgents)+ 核心循环 + 规划(todo)端到端设计

- **Date:** 2026-05-31
- **Status:** approved-by-user（"端到端做了，agent 发 plan、session 归一化、web 加 Plan 卡片"）
- **Scope:** 把 kokoro-agent 的核心引擎从"手写单轮工具循环"换成 **DeepAgents**(对标 Claude Code / Manus 的 agent 机制),并点亮**规划(todo)**这一能力端到端:agent 发 `plan.updated` → session 归一化 → web 渲染 Plan 卡片(CC/Gemini 式 todo 清单)。
- **Repos:** `kokoro-agent`(引擎+循环+plan 事件)、`kokoro-session`(归一化+投影)、`kokoro-web`(Plan catalog 组件)、`Kokoro`(协议+spec)。
- **Related:**
  - 引擎调研结论(本文件第 2 节);DeepAgents `deepagents==0.6.7`(langchain-ai,基于 langgraph)。
  - 现有 `kokoro-agent/src/kokoro_agent/run_agent.py`(手写循环,将被替换)、`infrastructure/model.py`(`make_chat_model`)、`worker.py`、`events.py`。
  - 契约 `docs/protocol/agent-events.md`(→ v0.3.0,加 `plan.updated`)、`docs/protocol/session-stream.md`(v2.0.0 A2UI op 流,本片加 Plan 组件)。
  - 前轮 spec `docs/superpowers/specs/2026-05-30-chat-shell-a2ui-design.md`(A2UI 渲染管线,本片复用)。

---

## 1. Goal

让 kokoro-agent 具备 CC/Manus 级的 agent 机制的**第一块地基**:用 DeepAgents 作引擎(自带 todo 规划/工具循环,后续可扩子agent/FS/sandbox),并把**规划(todo)**端到端点亮——一次 run 能在浏览器看到 agent 边规划边执行的 todo 清单(pending→in_progress→completed)。**全程离线可测、无需 API key**(照搬 DeepAgents 官方测试的 fake model)。

**本片定位**:kokoro-agent 是**创作任务编排器**(不是 coding agent)。对标 CC/Manus 取其**机制**(规划/工具循环/自主/产出),应用于 Kokoro 的创作域。本片只做引擎选型 + 核心循环 + 规划;子agent、真实创作工具、FS/sandbox、权限留后续片。

## 2. 引擎选型(DeepAgents,已决)

- `create_deep_agent(model, tools, system_prompt, subagents, middleware, ...) -> CompiledStateGraph`(标准 langgraph 图)。调用 `astream_events(input={"messages":[...]}, version="v2")`。
- 内置 todo 规划:`TodoListMiddleware`,state 键 `todos`,每项 `{content, status: "pending"|"in_progress"|"completed"}`;工具 `write_todos`(模型每次传**完整 todo 列表**,快照语义,非增量;一条 AIMessage 内不可并行多次调用)。
- 模型注入:传 `BaseChatModel` 实例原样用,或字符串走 `init_chat_model`。兼容我们的 `KOKORO_MODEL`,不绑 Gemini/OpenAI。
- 离线可测:DeepAgents 官方测试用一个**覆写 `bind_tools` 返回 self** 的 `GenericFakeChatModel`(支持 scripted `AIMessage` 含 `tool_calls`、`stream_delimiter` 分块流),无 key 端到端驱动 `create_deep_agent(model=fake)`,绕开 `create_react_agent`+fake 的 `NotImplementedError`。
- **否决的替代**:① 保留手写循环——要重造 todo/子agent,且偏离"对标 CC/Manus"取现成机制的意图;② langgraph 裸 `create_react_agent`/手搭 StateGraph——控制力强但同样重造规划,且无现成离线测试范式。
- **风险**:0.x 会 breaking → **pin `deepagents==0.6.7`**;默认强插 FS/`execute`/`task` 中间件 → 本片需裁剪到只剩 todo 规划(见 §3 裁剪);内置 `BASE_AGENT_PROMPT` 会拼到我们 prompt 之后(接受,system_prompt 里给创作域约束)。

## 3. 架构:run_agent 改为 DeepAgents 事件映射器

`run_agent(req, agent) -> AsyncIterator[AgentEvent]` 不再手写循环,而是单趟消费 `agent.astream_events(...)`,把 langgraph 事件映射成我们的**原始事件族**(agent 保持纯生产,不自填 cursor/owner)。

```
on_chain_start(顶层图)        → run.started（seq=1，仅首个顶层 chain）
on_chat_model_stream          → text.delta（content chunk，真·token 流，message_ref="m1"）
                              → thinking.delta（reasoning/thinking chunk；仅 execution_style=="thinking"）
on_chat_model_end             → text.completed（该消息累计全文）
on_tool_start name=="write_todos" → plan.updated{todos}（从 event.data.input 取完整 todo 列表）★拦截，不产 tool.invoked
on_tool_end   name=="write_todos" → （吞掉，不产 tool.returned）
on_tool_start（其它工具）       → tool.invoked{tool_call_ref, tool_name}
on_tool_end  （其它工具）       → tool.returned{tool_call_ref, tool_name, status}
on_chain_end(顶层) / 正常收尾   → run.completed{status:"completed"}
任何异常 / 超时                 → run.failed{error_kind, message}
```

- `write_todos` 被**拦截**成 `plan.updated`(规划信号,非用户可见工具),其 on_tool_start/end 不映射成 tool.*。
- `tool_call_ref`/`tool_name` 取自 langgraph 事件的 `run_id`/`name`;`status` 由 on_tool_end 有无异常决定(`ok`/`error`)。
- `asyncio.timeout(ASTREAM_TIMEOUT_S=120)`;langgraph `recursion_limit` 兜底防失控循环 → 超限归为 `run.failed`。
- seq 单调自增,保持现有契约。

### 引擎构造(`infrastructure/model.py` → `make_agent`)
- `make_agent() -> CompiledStateGraph`:
  - `spec = KOKORO_MODEL`(默认 `anthropic:claude-sonnet-4-6`)。
  - `spec=="scripted"` → `model = <scripted fake>`(§6);否则 `model = init_chat_model(spec)`。
  - `create_deep_agent(model=model, tools=[echo_search, clock], system_prompt=KOKORO_AGENT_PROMPT, <裁剪为仅 todo 规划>)`。
  - **裁剪**:本片只要 todo 规划,不暴露 FS/`execute`/子agent。实现期 **spike** 确认 DeepAgents 0.6.7 的裁剪开关(可能是 `middleware=[TodoListMiddleware()]` 显式集、或 `builtin_tools=`、或不传 subagents + 不注册 FS 工具)。若库强制注入 FS/execute,则在 system_prompt 里禁用 + 不在事件映射中转发它们(降级为容忍),并记为已知限制。
- worker:`make_agent()` 在 `_serve` 建一次(注:scripted fake 单次性,见 §6 注意)。

### Brain 接口变化
- `run_agent` 的第二参数从 `BrainModel = Runnable[LanguageModelInput, BaseMessage]`(chat model)改为 `Agent = CompiledStateGraph`(deep agent 图)。`run_agent` 内部不再 `ainvoke`+读 tool_calls,而是 `astream_events` 映射。
- `tools.py` 不变(`echo_search`/`clock` 仍作为传给 `create_deep_agent` 的 tools;`run_tool` 不再被 run_agent 直接调用——工具执行由 DeepAgents 图内部完成,我们只观测 on_tool_start/end)。保留 `TOOL_OBJECTS` 供 `create_deep_agent(tools=...)`。

## 4. 协议:agent-events.md v0.3.0

新增(additive,向后兼容):

| `kind` | payload required | 含义 | session 映射到 AGUI |
|---|---|---|---|
| `plan.updated` | `todos` | 规划/todo 列表更新(完整快照,非增量) | `plan.updated`(会话事件,携带 todos) |

- `todos`: `[{content: str, status: "pending"|"in_progress"|"completed"}]`(数组,strict)。
- 语义:**快照**——每次携带当前完整 todo 列表(对应 DeepAgents `write_todos` 全量传入)。同一 run 内可多次出现。
- 顺序:`plan.updated` 可穿插在 thinking/tool/text 之间;session 按 seq 排序后归一化。

## 5. session + web 端到端

### kokoro-session
- `domain/agent-events.ts`:inbound zod union 加 `plan.updated{todos:[{content,status(enum)}]}`(`.strict()`)。
- `application/normalize.ts`:`plan.updated` → 出站会话事件 `plan.updated{plan_id, todos}`(`plan_id` = 稳定 id,如 `{run_id}:plan`,同一 run 复用)。幂等按 `(run_id, seq)`。
- `domain/events.ts`:`sessionEventNames` 加 `plan.updated`。
- `application/a2ui-projector.ts`:`plan.updated` → mount 一个 `Plan` 组件(id=`plan_{run}`,只 mount 一次、push 进 root.children 一次)+ `updateDataModel(/plans/{id} = todos)`;后续 `plan.updated` 仅 `updateDataModel`(原地更新,像 message 累计但是整列替换)。
- `protocol/session-stream.md`:catalog `kokoro/chat/v1` 加 `Plan` 组件;记 `plan.updated` 会话事件。

### kokoro-web(catalog `kokoro/chat/v1` 加 Plan)
- `domain/shared/session-stream-event.ts` + `infrastructure/protocol/session-event.ts`:加 `plan-updated{planId, todos}` 解析(strict)。
- 新组件 `interfaces/a2ui/components/plan.tsx`:`Plan{todos:[{content,status}]}` via `createComponentImplementation`,渲染 CC/Gemini 式 todo 清单——`pending ○` / `in_progress ◐`(强调色)/ `completed ✓`(划掉/淡化)。暖色 Kokoro 风格,复用现有 token。注册进 `catalog.ts`。
- Plan 是时间线里一个**原地更新**的 item(DeepAgents 全量重发 todo → 整列替换)。

## 6. 离线测试(无 key、确定性)

照搬 DeepAgents 官方测试的 fake model 范式(`bind_tools` 覆写返回 self + scripted `AIMessage`)。`KOKORO_MODEL=scripted` → `create_deep_agent(model=fake)`,fake scripted 出能驱动图走完:**①一轮 `write_todos`(建 3 条 todo)→ ②一轮 `echo_search` 工具 → ③改 todo 状态 → ④最终 text**。

- **agent 测试**:断言 `run_agent` 映射出的事件序列含 `run.started → plan.updated(×N,todos 状态推进) → tool.invoked/returned(echo_search) → text.delta*/text.completed → run.completed`;`thinking` 风格下 thinking.delta 出现且不漏进 text;seq 单调;幂等。
- **scripted fake 注意**:fake 的 scripted 消息是一次性迭代器,且要精确匹配 DeepAgents 图的回合数 → 这是本片**最高风险点**,需 **spike**(对照 DeepAgents `tests/unit_tests/chat_model.py` 与 `test_graph.py` 把 scripted 序列调通)。worker 进程级复用 fake 会耗尽迭代器(前轮已知)→ 离线 e2e 每 run 重启 worker,或让 `make_agent` 每 run 重建(本片记为改进项)。
- **session 测试**:`plan.updated` 归一化 + 投影成 Plan mount + dataModel 更新;原地更新;幂等。
- **web 测试**:Plan 组件渲染(三状态)+ reducer/processor 喂 plan op 整列替换;集成测试。
- **离线浏览器 e2e**:`KOKORO_STREAM_BACKEND=redis KOKORO_MODEL=scripted` 三进程 + Playwright——看到 Plan 卡片(todo 从 pending→in_progress→completed)+ 工具卡 + 正文;截图。0 console error。无真实 LLM。

## 7. 数据流(端到端)

```
web 发送 ─▶ session run.request ─▶ agent: create_deep_agent.astream_events
   run.started → plan.updated(todos v1) → [thinking.delta] → tool.invoked(echo_search)→tool.returned
              → plan.updated(todos v2: 改状态) → text.delta* → text.completed → run.completed
        └─ StreamPort ─▶ session 归一化(plan.updated→plan.updated{plan_id,todos}; A2uiProjector→Plan mount+dataModel)
        ─ A2UI op 流(SSE)─▶ web kokoro/chat/v1 + Plan 组件:时间线里原地更新的 todo 清单
```

## 8. 错误 / 边界

- DeepAgents 图抛错 / 超时 → `run.failed`(boundary except,不再抛)。
- `write_todos` args 缺 `todos` / 格式非法 → 容错:记日志、跳过该 plan.updated,不崩。
- session:`plan.updated` 缺 `todos` strict 拒绝;Plan dataModel 缺失 → web 渲染空清单不崩。
- 空 todo 列表(`todos:[]`)→ 合法,渲染空 Plan(或不 mount,二选一并测试锁定:**选不 mount,直到首个非空**)。
- 多次 plan.updated → 同一 Plan 原地替换,不重复 mount / 不重复 push child。
- FS/execute/子agent 若被库强制注入并被模型误调 → 本片不映射其事件(容忍,不渲染),system_prompt 引导不使用。

## 9. 完成门槛(DoD)

- 四仓 LSP/linter/test 全绿;离线无 key。
- 事件族 `plan.updated` agent→session→web 贯通;web 渲染 CC/Gemini 式 todo 清单(三状态原地更新),浏览器 e2e 截图。
- agent 引擎为 DeepAgents(pin 0.6.7),核心循环走 `astream_events` 映射;真·token 流式 text。
- agent 只产原始 kind;web 只消费 A2UI op;session 拥有归一化+投影。无跨仓 import。
- Staff Engineer 视角:引擎可插拔(DeepAgents 在 Brain 接口后)、裁剪明确、离线可测、协议 additive 向后兼容。

## 10. 本片明确不做(YAGNI / 留后续片)

- 子agent 委派(DeepAgents `subagents`/`task`)。
- 真实创作工具(7 类生成器)、FS/sandbox/execute 落地。
- 权限(`safety-and-permission-envelope.md`)接入。
- 上下文/记忆 compaction、长程。
- 真实 LLM 下的 plan/tool/thinking(需 key)。
- Plan 卡片的交互(用户改 todo、点开步骤详情)——本片只读展示。

## 11. 风险与缓解

- **DeepAgents 不稳定(0.x breaking)**:pin `deepagents==0.6.7`;引擎隔离在 `make_agent` + `run_agent` 映射两处。
- **裁剪开关不明 / 强制注入 FS**:实现期 spike 确认;退路是容忍内置工具存在但不暴露/不映射,system_prompt 抑制。
- **scripted fake 驱动 deep agent**(最高风险):spike 对照官方测试调通;失败则降级——先用 fake 驱动一个 thinner 配置(仅 todo + 一个工具),保证离线 e2e 能产出 plan.updated。
- **过度工程**:严格限定本片只引擎+循环+todo;子agent/工具/权限一律不做。
