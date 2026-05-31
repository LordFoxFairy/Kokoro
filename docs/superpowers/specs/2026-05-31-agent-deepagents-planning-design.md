# Agent 引擎选型(DeepAgents)+ 核心循环 + 规划(todo)端到端设计

- **Date:** 2026-05-31
- **Status:** approved-by-user（"端到端做了，agent 发 plan、session 归一化、web 加 Plan 卡片"）
- **Scope:** 把 kokoro-agent 的核心引擎从"手写单轮工具循环"换成 **DeepAgents**(对标 Claude Code / Manus 的 agent 机制),并点亮**规划(todo)**这一能力端到端:agent 通用产出(write_todos 当普通工具) → session(harness)识别并归一化 → web 渲染 Plan 卡片(CC/Gemini 式 todo 清单)。
- **Repos:** `kokoro-agent`(DeepAgents 引擎+核心循环+tool args,全通用)、`kokoro-session`(harness 识别 write_todos+归一化+投影)、`kokoro-web`(Plan catalog 组件,纯渲染)、`Kokoro`(协议+spec)。
- **Related:**
  - 引擎调研结论(本文件第 2 节);DeepAgents `deepagents==0.6.7`(langchain-ai,基于 langgraph)。
  - 现有 `kokoro-agent/src/kokoro_agent/run_agent.py`(手写循环,将被替换)、`infrastructure/model.py`(`make_chat_model`)、`worker.py`、`events.py`。
  - 契约 `docs/protocol/agent-events.md`(→ v0.3.0,`tool.invoked` 加可选 `args`)、`docs/protocol/session-stream.md`(v2.0.0 A2UI op 流,本片加 Plan 组件 + write_todos→Plan 识别约定)。
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
on_tool_start（所有工具，含 write_todos）→ tool.invoked{tool_call_ref, tool_name, args}
on_tool_end  （所有工具，含 write_todos）→ tool.returned{tool_call_ref, tool_name, status}
on_chain_end(顶层) / 正常收尾   → run.completed{status:"completed"}
任何异常 / 超时                 → run.failed{error_kind, message}
```

- **agent 完全通用,不认识 "plan"/"todo"**:`write_todos` 与 `echo_search` 一视同仁,都走 `tool.invoked/returned`。"识别 write_todos 渲染成清单"是 harness 职责,放 session(见 §5)——对标 Claude Code:`TodoWrite`/`Task` 本质都是工具,由 harness 识别并特殊渲染,模型层不特殊化。
- **唯一通用增强**:`tool.invoked` 带上入参 `args`(`event.data.input`),让下游 harness 能拿到工具数据(对所有工具有用,非给 todo 开后门)。
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

**不新增事件 kind**(agent 通用)。唯一改动(additive,向后兼容):`tool.invoked` payload 加**可选 `args`**:

| `kind` | payload | 含义 |
|---|---|---|
| `tool.invoked` | `tool_call_ref`, `tool_name`, **`args`(可选,新增)** | 工具调用开始;`args` = 工具入参(`event.data.input`),供 session harness 识别/取数据 |

- `args` 是任意 JSON 对象(工具入参原样);对 `write_todos` 即 `{todos:[{content,status}]}`,但 agent 不关心其语义。
- **无 plan.updated agent 事件**:planning 的 todo 列表通过 `write_todos` 这个普通工具的 `args` 流出,由 session 识别(§5)。

## 5. session(harness 识别)+ web(纯渲染)端到端

**特殊化只发生在 session 这一层**(业务/harness 层),agent 通用、web 纯渲染。识别逻辑只在 session 的归一化器里一处。

### kokoro-session
- `domain/agent-events.ts`:`tool.invoked` 变体 payload 加**可选 `args`**(任意对象);其余不变。**不加 plan.updated inbound 事件**。
- `application/normalize.ts`(harness 识别):处理 `tool.invoked` 时按 `tool_name` 分流——
  - `tool_name == "write_todos"` → **不**产 `tool.started`,而是产**内部会话事件** `plan.updated{plan_id:"{run_id}:plan", todos: args.todos}`;并把该 `tool_call_ref` 记入"write_todos 集合"。
  - 其它工具 → 照旧 `tool.started{tool_call_id, tool_name}`。
  - 对应的 `tool.returned`:若 `tool_call_ref` 在 write_todos 集合 → **吞掉**(Plan 已在 invoke 时更新),不产 `tool.completed`;否则照旧。
  - 幂等按 `(run_id, seq)`。
- `domain/events.ts`:`sessionEventNames` 加 `"plan.updated"`(**session 内部 AGUI 表示**,非 agent 协议)。
- `application/a2ui-projector.ts`:`plan.updated` SessionEvent → mount `Plan` 组件(id=`{plan_id}`,只 mount 一次 + push root.children 一次)+ `updateDataModel(/plans/{id}=todos)`;后续 `plan.updated` 仅 `updateDataModel`(原地整列替换)。空 `todos` 且未 mount → 不产(§8)。projector **不认识 write_todos**——它只处理抽象的 `plan.updated`(识别已在 normalizer 完成,职责分离)。
- `protocol/session-stream.md`:catalog `kokoro/chat/v1` 加 `Plan` 组件;记"session 识别 write_todos→Plan"的 harness 约定。

### kokoro-web(catalog `kokoro/chat/v1` 加 Plan,纯渲染)
> 注意:上轮(chat shell × A2UI)已删除 web 的 AGUI 解析层(`session-event.ts`/`session-stream-event.ts`)——web **只消费 A2UI op**,通过 catalog 组件渲染。故本片 web **只需加一个 Plan catalog 组件**,无任何"解析 plan 事件"的代码。
- 新组件 `interfaces/a2ui/components/plan.tsx`:`Plan{todos:[{content,status}]}` via `createComponentImplementation`(按上轮锁定的 `{props,buildChild,context}` 签名),渲染 CC/Gemini 式 todo 清单——`pending ○` / `in_progress ◐`(强调色)/ `completed ✓`(淡化/划掉)。暖色 Kokoro 风格,复用现有 token。注册进 `catalog.ts`。
- Plan 是时间线里一个**原地更新**的 item(session 全量重发 todo → 整列替换)。

## 6. 离线测试(无 key、确定性)

照搬 DeepAgents 官方测试的 fake model 范式(`bind_tools` 覆写返回 self + scripted `AIMessage`)。`KOKORO_MODEL=scripted` → `create_deep_agent(model=fake)`,fake scripted 出能驱动图走完:**①一轮 `write_todos`(建 3 条 todo)→ ②一轮 `echo_search` 工具 → ③改 todo 状态 → ④最终 text**。

- **agent 测试**:断言 `run_agent` 映射出的事件序列含 `run.started → tool.invoked(write_todos, args.todos)/tool.returned → tool.invoked(echo_search)/returned → text.delta*/text.completed → run.completed`;**所有工具(含 write_todos)都走 tool.* 且 tool.invoked 带 args**;agent **不产** plan.updated(它不认识 plan);`thinking` 风格下 thinking.delta 出现且不漏进 text;seq 单调;幂等。
- **session 识别测试**:喂 `tool.invoked{tool_name:"write_todos", args:{todos}}` → 产内部 `plan.updated{plan_id, todos}`、**不**产 tool.started;其 `tool.returned` 被吞、不产 tool.completed;`echo_search` 仍产 tool.started/completed。
- **scripted fake 注意**:fake 的 scripted 消息是一次性迭代器,且要精确匹配 DeepAgents 图的回合数 → 这是本片**最高风险点**,需 **spike**(对照 DeepAgents `tests/unit_tests/chat_model.py` 与 `test_graph.py` 把 scripted 序列调通)。worker 进程级复用 fake 会耗尽迭代器(前轮已知)→ 离线 e2e 每 run 重启 worker,或让 `make_agent` 每 run 重建(本片记为改进项)。
- **session 测试**:`plan.updated` 归一化 + 投影成 Plan mount + dataModel 更新;原地更新;幂等。
- **web 测试**:Plan 组件渲染(三状态)+ reducer/processor 喂 plan op 整列替换;集成测试。
- **离线浏览器 e2e**:`KOKORO_STREAM_BACKEND=redis KOKORO_MODEL=scripted` 三进程 + Playwright——看到 Plan 卡片(todo 从 pending→in_progress→completed)+ 工具卡 + 正文;截图。0 console error。无真实 LLM。

## 7. 数据流(端到端)

```
web 发送 ─▶ session run.request ─▶ agent: create_deep_agent.astream_events（全通用）
   run.started → tool.invoked(write_todos, args=todos v1)→tool.returned → [thinking.delta]
              → tool.invoked(echo_search)→tool.returned
              → tool.invoked(write_todos, args=todos v2 改状态)→tool.returned
              → text.delta* → text.completed → run.completed
        └─ StreamPort ─▶ session 归一化(harness 识别 write_todos→内部 plan.updated{plan_id,todos}、吞掉其 tool 卡;
                          echo_search→tool.started/completed; A2uiProjector: plan.updated→Plan mount+dataModel)
        ─ A2UI op 流(SSE)─▶ web kokoro/chat/v1 + Plan 组件:时间线里原地更新的 todo 清单
```

## 8. 错误 / 边界

- DeepAgents 图抛错 / 超时 → `run.failed`(boundary except,不再抛)。
- agent:`tool.invoked` 的 `args` 取不到(工具无入参)→ 省略 `args`,不崩;agent 不校验 args 语义。
- session 识别:`tool_name=="write_todos"` 但 `args.todos` 缺失/非数组 → 容错:记日志、不产 plan.updated(降级为忽略),不崩。
- session inbound:`tool.invoked` 的 `args` 是可选任意对象(zod 宽松);内部 `plan.updated` 出站走 `parseSessionEvent` 自检。Plan dataModel 缺失 → web 渲染空清单不崩。
- 空 todo 列表(`todos:[]`)→ 合法,渲染空 Plan(或不 mount,二选一并测试锁定:**选不 mount,直到首个非空**)。
- 多次 plan.updated → 同一 Plan 原地替换,不重复 mount / 不重复 push child。
- FS/execute/子agent 若被库强制注入并被模型误调 → 本片不映射其事件(容忍,不渲染),system_prompt 引导不使用。

## 9. 完成门槛(DoD)

- 四仓 LSP/linter/test 全绿;离线无 key。
- agent 引擎为 DeepAgents(pin 0.6.7),核心循环走 `astream_events` 映射;真·token 流式 text;**agent 完全通用**(write_todos 当普通工具,tool.invoked 带 args,不产 plan 事件)。
- planning 端到端:agent 发 write_todos 工具 → **session harness 识别** → 内部 plan.updated → Plan 组件 → web 渲染 CC/Gemini 式 todo 清单(三状态原地更新),浏览器 e2e 截图。
- agent 只产通用原始 kind;web 只消费 A2UI op 纯渲染;**特殊化(write_todos→Plan)只在 session 一处**。无跨仓 import。
- Staff Engineer 视角:引擎可插拔(DeepAgents 在 Brain 接口后)、agent/web 保持纯粹、识别策略集中在业务层(对标 CC harness)、协议 additive 向后兼容。

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
- **scripted fake 驱动 deep agent**(最高风险):spike 对照官方测试调通;失败则降级——先用 fake 驱动一个 thinner 配置(仅 todo + 一个工具),保证离线 e2e 能让 agent 发出 write_todos 工具(→ session 识别成 Plan)。
- **过度工程**:严格限定本片只引擎+循环+todo;子agent/工具/权限一律不做。
