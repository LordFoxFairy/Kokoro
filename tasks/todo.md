# Todo

- [x] Create `kokoro-web/` as an independent Git repository.
- [x] Scaffold Bun + Next.js + Tailwind + shadcn/ui baseline.
- [x] Add DDD folders and dependency boundaries.
- [x] Add strict protocol schemas with failing tests first.
- [x] Add replay reducer with failing tests first.
- [x] Render the minimal chat shell using seed events.
- [x] Run test, lint, typecheck, and build.

## Documentation alignment

- [x] Add a durable three-primary-runtime architecture overview.
- [x] Record the main-agent/user-alignment lesson and defensive rule.
- [x] Persist the DeepAgents/LangChain orchestration reuse preference in project memory.
- [x] Clarify the protocol docs so the current minimal session-stream closed loop is distinct from browser-reserved parse-and-ignore event families.

## First-screen shell redesign (staged)

- [x] Add `run.created` to the protocol union as a parse-and-ignore family (maps to null) with red→green tests.
- [x] Replace the two-card protocol demo with the approved minimal first-screen shell (rail + hero + static composer).
- [x] Rework `globals.css` for the first-screen layout.
- [x] Keep the SSE reducer wired but surfaced via `data-*` while message rendering is deferred to the chat-view slice.
- [x] Gitignore local agent/MCP scratch dirs (`.playwright-mcp/`, `.superpowers/`).
- [x] Land the first-screen slice (commits `2d0cf08`, `bf0dde3`).

## Conversation view slice (in progress)

Design: `docs/superpowers/specs/2026-06-03-conversation-view-design.md`. Goal: complete multi-turn streaming conversation, demonstrable standalone via graceful local-simulation fallback. Artifact lane deferred (reserved) per the more recent refinement + protocol downgrade.

- [x] application: `appendUserMessage(state, {id, content})` pure helper + tests (multi-turn accumulation, immutability, ordering, survives run fold).
- [x] application: `consumeLiveSession` gains optional `initialState` + `onSettled`; all existing preview tests still green.
- [x] application: `buildSimulatedReplyEvents` (pure, deterministic, terminates) + `simulateAssistantReply` driver + `startSessionReply` orchestrator (live→fallback) + tests.
- [x] interfaces: `SessionShell` rewritten into empty/active conversation — controlled textarea composer (Enter sends, disabled while streaming), thread rendering, calm streaming indicator, inline failed state; injectable `startReply`.
- [x] styles: extended `globals.css` with thread/bubble/active-layout classes.
- [x] tests: shell test covers empty first screen, user msg render, assistant reply, streaming-disabled input, multi-turn history, inline failed error (29 tests pass).
- [x] verify: lint + typecheck + test + build green; Playwright visual pass over a real multi-turn conversation.
- [x] UI feedback pass (2026-06-03): scaled the whole UI to compact/conventional sizes; switched to comfortable left/right bubble layout (assistant left+avatar, user right); removed composer hover layout-shift. Re-verified all gates + visually.
- [x] Committed the conversation-view base (kokoro-web `7aada7e`).

## Production-usable polish (2026-06-03, via workflow + subagents)

Ran a multi-agent workflow (audit → plan → [implement → per-round QA gate] ×6 → 4-lens review) with a hard zero-cruft rule and a quality gate after every workstream.

- [x] Foundation cleanup: removed dead exports (createPreviewSessionState/startDemoSession/openDemoSessionStream/previewEvents); reducer dedups session-created + pins role-per-messageId; explicit parse-and-ignore listeners.
- [x] Stop/cancel generation + calm streaming indicator (reduced-motion aware).
- [x] SSR-safe single-conversation persistence (localStorage), 新对话 reset+refocus, retry-on-failure, double-send guard.
- [x] Composer auto-grow + focus return + input length cap.
- [x] Scroll stickiness + jump-to-latest; inline failed state.
- [x] A11y/visual polish: lang=zh-CN, aria-live/atomic, focus-visible (no reflow), WCAG contrast bumps, message/pulse animations.
- [x] Verified in main: lint+typecheck+test(79)+build green; Playwright pass (empty → send → reply → reload-persists → 新对话 resets). Review: production-ready, 0 blockers. Committed kokoro-web `7aada7e`.
- [ ] (deferred) artifact lane promotion.

## Follow-up roadmap (recorded 2026-06-04)

Design source of truth = `docs/prototypes/variant-a-mi-mu/` (serve + screenshot before any UI work). Pin one anchor, confirm with user, then proceed. Don't over-reach: change only what's asked.

### A. Chat polish (kokoro-web)
- [x] Stop/cancel button design: it already exists (send→wood ■ "停止生成" during streaming, cancel semantics). Made the local preview stream slower (stepMs 28→60) so the stop is visible/usable. Decision: stop/cancel, NOT pause/resume (not meaningful for one-shot LLM replies).
- [x] Starter chips on the empty screen (海报/落地页/课件/写信/想法可视化), matching the prototype `.chip--template` row. Click prefills the composer with a continuable starter prompt (caret at end), does NOT send; chips confined to the empty hero. kokoro-web `ce291bf`, lint/typecheck/test(82)/build green + Playwright-verified. (Dropped the prototype's `更多…` chip — it linked to a non-existent gallery; add when templates/gallery exists.)
- [x] Wire the Fast/Thinking mode to the run's `execution_style` end-to-end. Completed on the locked baseline branches: `kokoro-web` now threads the selected `fast | thinking` mode into the live run request and surfaces contract failures as explicit failed runs; `kokoro-session` restricts `execution_style` to `fast | thinking` and rejects invalid values with HTTP 400; `kokoro-agent` resolves model/runtime config per run instead of using a worker-global model instance, and the current `openai:glm-5` path verifies a distinct `thinking` runtime (`reasoning_effort="high"`) versus `fast`.
- [ ] Attach menu (上传图片/文件/拍照) → real native file picker, then backend upload when available. Current baseline status: menu entries exist in `composer.tsx`, but there is no real file input / camera / upload flow wired yet.

### B. Close the three-repo live loop (the real "production" gap) — DONE 2026-06-04
- [x] kokoro-session: fixed lint (`sessionEventNames` → `SessionEventName` derived from the Zod schema) + landed the Zod migration. Branch `feat/three-repo-loop` (8c9428f).
- [x] kokoro-agent: added `from collections.abc import Mapping` + tightened the payload TypeGuard for pyright --strict; committed the local-fake-model. Branch `feat/three-repo-loop` (673ee61).
- [x] Ran all three together over Redis (existing shared container, isolated db 15) with `KOKORO_LOCAL_FAKE_MODEL=1`. **Found + fixed a real Redis-only SSE cursor bug** (session resumed XREAD from the domain `envelope.cursor` as if it were a Redis stream id → silent empty `/stream`; MemoryStreamPort masked it). Verified end-to-end via curl (session.created→deltas→message.completed→run.completed) AND in the browser via Playwright: real agent reply rendered ("Local fallback active…"), transport label "实时 · http://localhost:3001" (live path, not the preview fallback). See lessons 2026-06-04.
- [ ] Optional: verify and use real provider credentials for the live worker path. Current baseline status: `kokoro-agent` already includes `langchain-openai`, `python-dotenv`, `load_dotenv()`, and env-based `KOKORO_MODEL` / `OPENAI_BASE_URL` / `OPENAI_API_KEY` model bootstrapping; what remains is operational verification / choosing the provider credentials for the live worker path.

### C. Design-direction decision (needs user call)
- [ ] How much of the richer prototype to adopt vs the approved 06-02 minimal shell: serif hero accent, rail nav sections (创作/进阶/发现), warm send button. (06-02 chose minimal; prototype is richer — surface as a decision, don't silently pick.)

### D. Housekeeping
- [ ] Investigate/remove the stray sibling `~/WebstormProjects/kokoro-web` (duplicate of `Kokoro/kokoro-web`).

## E. Agent activity rendering (ACTIVE GOAL, set 2026-06-05)

Goal: display real agent activity end-to-end — thinking, tool calls, subagents, CC-style live todo — plus 中断恢复 and a left-rail sessions list. User-chosen: **backend-first with real DeepAgents**, **todo aligned to Claude Code**. Memory: [[kokoro-agent-activity-goal]]. Crux: the pipeline currently DROPS thinking/tools/subagents (agent strips them; protocol doesn't model them) — cross-repo vertical: agent emits → AgentEvent contract → session protocol (Pydantic+Zod, synced) → relay → web reducer+UI.

Key finding: `deepagents 0.6.6` `create_deep_agent(model, tools, system_prompt=, subagents=)` → LangGraph, with built-in `write_todos` (CC todo), `task` (subagents), file ops, `execute`. Reuse it; stream via `astream_events` → map to our events. Tool loops need a tool-calling model: support real (`ANTHROPIC_API_KEY`) AND a scripted tool-calling fake (key-free, deterministic, test-friendly).

- [ ] E1 (agent contract): extend `AgentEvent` kinds — add `thinking.delta`, `todo.updated`, `subagent.started`, `subagent.finished` (`tool.invoked/returned` already exist); document payload shapes; boundary tests (Schema崩塌/空值/序列). Keep agent events loose; strict normalization stays at the session boundary.
- [x] E2 (agent runtime) DONE (agent 63c6031): `run_agent` builds `create_deep_agent` + streams `astream_events(v2)` → pure `translate_stream_event` mapper + `drive_agent_events` envelope. Scripted tool-calling `LocalFakeChatModel` (GenericFakeChatModel can't bind_tools) restores the credential-free path. `KOKORO_DISABLE_STREAMING` for streaming-averse gateways. pytest(44)/ruff/pyright green. **Verified end-to-end with real gpt-5.4: 4× todo.updated evolving pending→in_progress→completed (live CC checklist) + markdown answer.**
  - **Model enabled (1f5da32):** test model via an OpenAI-compatible gateway, configured in `.env` (gitignored — never committed): `KOKORO_MODEL=openai:<model>`, `OPENAI_BASE_URL=<gateway>/v1` (the `/v1` suffix is required), `OPENAI_API_KEY=<key>`. langchain-openai + python-dotenv added; worker load_dotenv().
  - **Gateway constraint:** rejects STREAMING ("concurrency limit exceeded"). Must build the model `disable_streaming=True`. Consequence: no token-level deltas — emit full text per `on_chat_model_end` (one text.delta or text.completed). Token streaming later if the gateway supports it.
  - **Empirical astream_events(version="v2") shapes** (probed): emit on these, skip the rest:
    - `on_tool_start::write_todos` → `todo.updated`, payload `{"todos": data.input["todos"]}` — input.todos IS the CC list `[{content, status: pending|in_progress|completed}]`.
    - `on_tool_start::<name>` (name != write_todos/task) → `tool.invoked` {tool_id, name, args=data.input}; `on_tool_end::<name>` → `tool.returned` {tool_id, name, result=str(data.output)}. (tool_id: data.run_id of the tool event correlates start/end.)
    - `on_tool_start::task` → `subagent.started`; subagent's nested events arrive with metadata identifying it; `on_tool_end::task` → `subagent.finished`. (Handle nesting in a later pass if complex.)
    - `on_chat_model_end::ChatOpenAI` → the AIMessage: if it has tool_calls it's an intermediate turn (skip text); the final one (no tool_calls) → text. (reasoning/thinking content block → thinking.delta when present.)
    - Skip internal graph nodes: `on_chain_*::{LangGraph, model, tools, TodoListMiddleware*, PatchToolCallsMiddleware*}`.
    - Terminal: after the stream ends → `run.completed`; wrap the whole loop and emit `run.failed` on exception (mirror current run_agent's boundary).
- [x] E3 (session protocol) DONE (session 1d58ed5): mirrored the new families in `events.ts` (Zod) + `normalize.ts` (relay into replay/SSE), and fixed a tool-payload drift (inbound expected {tool,input} the agent never sent → now {tool_id,name,args/result}). typecheck/lint/test(51) green.
- [x] E4 (web) DONE (web 7271578): parse + reducer-accumulate the activity families (todos replaced wholesale, toolCalls timeline, subagents, thinking; legacy persist via .default(); per-turn reset). ActivityPanel renders the CC-style todo checklist + tools + subagents + collapsible thinking. lint/typecheck/test(92)/build green.
- [x] **MINIMAL CLOSED LOOP VERIFIED END-TO-END (2026-06-05)** with real gpt-5.4: web→session→agent(DeepAgents)→Redis→normalize→web. Browser showed the live CC-style todo checklist (3 items → completed) beside the markdown answer; transport "实时". tools/subagents/thinking are fully wired + unit-tested but only render when the agent produces them (needs a registered domain tool / subagent spawn / a reasoning model — none triggered by this prompt+gpt-5.4).
- [x] E5 (中断恢复) DONE (web 7e1555c, session 712a34b): on reload/disconnect the web re-subscribes to the in-flight run's SSE and continues (per-conversation backend session id; pendingInput marks in-flight, set on onLive/cleared on settle/stop; 90s fallback). **Fixed a real session bug**: RedisStreamPort shared ONE blocking connection for all BLOCK xreads → dispatch + relays + concurrent SSE starved each other and /stream wedged; now each subscribe uses its own connection (712a34b). Browser-verified: after reloading mid-run the todo checklist progressed (events continued) and the terminal event was handled (the run itself then failed only due to the gateway's concurrency cap — external; the failed state shows 重试). lint/typecheck/test(105 web, 51 session)/build green.
- [x] Floating + collapsible activity panel (web f07f79c): ActivityPanel hovers top-right of the conversation, collapses to a "计划 N/M" pill — real-time progress without scrolling away.
- [x] E6 (sessions list) DONE (web 2876bdf): conversation-store (pure, Zod) replaces single-thread persistence; multi-conversation under `kokoro:conversations`; rail renders the history list (active highlight, hover delete, auto-title from first message), switch/new/delete; switching/deleting aborts an in-flight reply. lint/typecheck/test(103)/build green; browser-verified switching between two conversations.
- [ ] stream_port.py polish (transport foundation, folds in): `_BLOCK_MS` → constructor param; document `_CURSOR_WIDTH`/`_REDIS_FIELD` as cross-language contract constants (NOT .env — would silently break the loop). Filename mirrors `stream-port.ts` (rename both or neither). This is the main remaining engineering cleanup item under the agent-activity / three-repo transport line.

## F. Stream perfection + ordered-parts + turn lifecycle (DONE 2026-06-10)

- [x] Real token streaming (agent `bc316d7`): LangChain `on_chat_model_stream` (`_TEXT_STREAM_INTENT`, `streamed_text`/`sub_streamed_text`) → char-by-char answers; verified live (77 glm-5 deltas, 42 message.delta). Fixed segment-attachment: tool now attaches to the FOLLOWING segment (`active_message_ref is None OR segment_completed`), killing the "tool→text→tool collapses into one bubble" defect.
- [x] Ordered-parts model (web `61715b6`): reducer rewritten around `SessionStep` union (`thinking|tool|subagent|text`, each with `seq`+`messageId`) in `stepsByRun` keyed by runId; `seq` from envelope cursor → render order == emission order. `buildThreadItems` groups consecutive assistant msgs by runId. Layout: ONE avatar/turn + vertical spine of segments, each = bubble ABOVE its process (user overrode research's process-above-text). Spec: `docs/superpowers/plans/2026-06-09-ordered-parts-stream-rewrite.md`. Design panel = 3 cross-validating agents.
- [x] Turn lifecycle affordances (web `9c82c69`): submitted-no-token scaffold (no blank frame); forming bubble (`正在思考` in the bubble slot when process precedes text, never an empty bubble); collapse-on-settle (`open = manualOpen ?? live`, no remount, manual override wins); reconnect anchor (`isReconnecting` → 「重连中…」warm-wood capsule). Single live anchor preserved. 178 vitest + tsc + eslint green; Playwright in-page recorder captured forming→text+caret→collapsed-settle deterministically.
- [ ] REAL-backend e2e (next phase): start kokoro-session (:3001, Redis db15) + kokoro-agent worker (gateway `.env`, `disable_streaming=True`) and Playwright a REAL DeepAgents run — tools/subagents/thinking only render when the agent PRODUCES them; preview can't exercise real subagent nesting. (Only web :3000 currently up.)
- [ ] DDD architecture refactor (deferred): panel cross-validated a session→web→agent ordering — god-file splits, kebab-case, application-owned ports, dead-file deletion across all three repos.

## G. 测试体系 + 真实效果 + 扩展性(DONE 2026-06-13)

- [x] 《测试用例总目录》:62 流程 × 三层矩阵 + 10 缺口全部清账(4 行为修复 + 6 组测试;基数 80/66/175 → 88/74/189)。
- [x] 真实 LLM e2e 实证:完整回答(修 translator 中间叙述丢弃)、刷新中断恢复、todo 4/4、4 张截图。
- [x] 《能力扩展架构设计》:工具/workspace/teams/HITL 分期 + 新 kind SOP。
- [ ] (后续可选)X1 自定义工具首落地;T1a 双 run 并发幂等 e2e;web lint 警告保持零。

## H. HITL/chatbot 缺陷打磨 (设计 2026-06-14,用户全选 + 分层指令)

设计原则(用户定):**各层各管自己的**——agent=执行+自己的 LLM 上下文记忆(可压缩);
session=传输/relay/replay(不碰会话记忆);web=UI+完整展示历史+发 input/决定/取消。

### 控制协议统一(支撑 #2/#3/#8)
control 消息(非 codegen,手定): `{kind:"control", decision:"approve"|"reject"|"cancel", tool_id?}`
- approve/reject 带 tool_id → gate 按自己的 tool_id 匹配(废弃 DecisionCursor 顺序游标);
  reject 不带 tool_id = 广播(放弃 run 时 reject 全部待批)。
- cancel = 取消整个 run(worker 取消该 run 的 task)。
- web: 审批按钮带 toolId;stop/放弃 发 reject(广播) + cancel;session control 端点透传 decision+tool_id;agent gate/worker 消费。

### 增量(逐个 TDD + 门禁绿 + 真机验证)
- [x] #1 worker 并发化(agent only,无契约) DONE(agent 05514b2,8+160 pytest):`_serve` 每 run 一个 asyncio task + 有上限 Semaphore;processed 去重在 spawn 前同步;task 异常不崩 loop。修「awaiting 冻结全局」。
- [x] #8 取消 DONE(agent 9b1002d/session 5d6054d/web d1de82a+c9465be):control 加 cancel;worker 每 run cancel-watcher→task.cancel()→run.completed(cancelled);web stop/放弃发 cancel + 本地 markRunCancelled 收口。真机验证(awaiting→stop→redis cancelled,无 ghost)。
- [x] #3 放弃解阻塞全部 DONE:由 #8 cancel 覆盖(取消整个 run→所有待批门随 task 一起死)。
- [~] #2 并行 tool_id 精确匹配 DEFERRED:探针证实门控工具协程拿不到自己的 tool run_id(run_manager 不注入/config.run_id 为 None),不 hack langchain 内部就无法精确匹配;顺序执行(常态)无此问题,留记录。
- [ ] #7 记忆(agent only,各管各的):create_deep_agent(checkpointer=持久 saver);run_agent 传 config thread_id=conversation_id;agent 跨 run 记上文(后续加压缩 middleware)。web/session 不变。
- [ ] #4 超时文案:区分「审批超时」vs「用户拒绝」(rejected 仍 true,reason 不同)。
- [ ] #5 control POST 错误处理(web):fetch 失败不静默。
- [ ] #6 plan 模式语义:厘清/文档化交互审批 vs 只读。
- [ ] #9 worker processed set 有界(LRU/按完成清理)。
