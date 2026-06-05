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
- [ ] (deferred) markdown rendering for assistant text; multi-conversation history list; artifact lane promotion.

## Follow-up roadmap (recorded 2026-06-04)

Design source of truth = `docs/prototypes/variant-a-mi-mu/` (serve + screenshot before any UI work). Pin one anchor, confirm with user, then proceed. Don't over-reach: change only what's asked.

### A. Chat polish (kokoro-web)
- [x] Stop/cancel button design: it already exists (send→wood ■ "停止生成" during streaming, cancel semantics). Made the local preview stream slower (stepMs 28→60) so the stop is visible/usable. Decision: stop/cancel, NOT pause/resume (not meaningful for one-shot LLM replies).
- [x] Starter chips on the empty screen (海报/落地页/课件/写信/想法可视化), matching the prototype `.chip--template` row. Click prefills the composer with a continuable starter prompt (caret at end), does NOT send; chips confined to the empty hero. kokoro-web `ce291bf`, lint/typecheck/test(82)/build green + Playwright-verified. (Dropped the prototype's `更多…` chip — it linked to a non-existent gallery; add when templates/gallery exists.)
- [ ] Wire the Fast/Thinking mode to the run's `execution_style` (currently display-only). DESIGN (user, 2026-06-04): Fast/Thinking are the **`chat` business_type**'s bound model options — each a `{label, value=litellm model_name}` pair (the composer mode dropdown IS the chat model selector). Belongs with the deferred model-management platform; see provider/gateway memory.
- [ ] Attach menu (上传图片/文件/拍照) → real native file picker, then backend upload when available (currently placeholder).
- [ ] Markdown rendering for assistant messages (real LLM output is markdown) — needs a sanitized renderer.
- [ ] Multi-conversation history list in the rail (currently single persisted conversation).

### B. Close the three-repo live loop (the real "production" gap) — DONE 2026-06-04
- [x] kokoro-session: fixed lint (`sessionEventNames` → `SessionEventName` derived from the Zod schema) + landed the Zod migration. Branch `feat/three-repo-loop` (8c9428f).
- [x] kokoro-agent: added `from collections.abc import Mapping` + tightened the payload TypeGuard for pyright --strict; committed the local-fake-model. Branch `feat/three-repo-loop` (673ee61).
- [x] Ran all three together over Redis (existing shared container, isolated db 15) with `KOKORO_LOCAL_FAKE_MODEL=1`. **Found + fixed a real Redis-only SSE cursor bug** (session resumed XREAD from the domain `envelope.cursor` as if it were a Redis stream id → silent empty `/stream`; MemoryStreamPort masked it). Verified end-to-end via curl (session.created→deltas→message.completed→run.completed) AND in the browser via Playwright: real agent reply rendered ("Local fallback active…"), transport label "实时 · http://localhost:3001" (live path, not the preview fallback). See lessons 2026-06-04.
- [ ] Optional: real LLM via `ANTHROPIC_API_KEY` (set on the worker; everything else unchanged).

### C. Design-direction decision (needs user call)
- [ ] How much of the richer prototype to adopt vs the approved 06-02 minimal shell: serif hero accent, rail nav sections (创作/进阶/发现), warm send button. (06-02 chose minimal; prototype is richer — surface as a decision, don't silently pick.)

### D. Housekeeping
- [ ] Investigate/remove the stray sibling `~/WebstormProjects/kokoro-web` (duplicate of `Kokoro/kokoro-web`).

## E. Agent activity rendering (ACTIVE GOAL, set 2026-06-05)

Goal: display real agent activity end-to-end — thinking, tool calls, subagents, CC-style live todo — plus 中断恢复 and a left-rail sessions list. User-chosen: **backend-first with real DeepAgents**, **todo aligned to Claude Code**. Memory: [[kokoro-agent-activity-goal]]. Crux: the pipeline currently DROPS thinking/tools/subagents (agent strips them; protocol doesn't model them) — cross-repo vertical: agent emits → AgentEvent contract → session protocol (Pydantic+Zod, synced) → relay → web reducer+UI.

Key finding: `deepagents 0.6.6` `create_deep_agent(model, tools, system_prompt=, subagents=)` → LangGraph, with built-in `write_todos` (CC todo), `task` (subagents), file ops, `execute`. Reuse it; stream via `astream_events` → map to our events. Tool loops need a tool-calling model: support real (`ANTHROPIC_API_KEY`) AND a scripted tool-calling fake (key-free, deterministic, test-friendly).

- [ ] E1 (agent contract): extend `AgentEvent` kinds — add `thinking.delta`, `todo.updated`, `subagent.started`, `subagent.finished` (`tool.invoked/returned` already exist); document payload shapes; boundary tests (Schema崩塌/空值/序列). Keep agent events loose; strict normalization stays at the session boundary.
- [x] E2 (agent runtime) DONE (agent 63c6031): `run_agent` builds `create_deep_agent` + streams `astream_events(v2)` → pure `translate_stream_event` mapper + `drive_agent_events` envelope. Scripted tool-calling `LocalFakeChatModel` (GenericFakeChatModel can't bind_tools) restores the credential-free path. `KOKORO_DISABLE_STREAMING` for streaming-averse gateways. pytest(44)/ruff/pyright green. **Verified end-to-end with real gpt-5.4: 4× todo.updated evolving pending→in_progress→completed (live CC checklist) + markdown answer.**
  - **Model enabled (1f5da32):** test model = `gpt-5.4` via OpenAI-compatible gateway (`.env`, gitignored: KOKORO_MODEL=openai:gpt-5.4, OPENAI_BASE_URL=`https://coding-llm.hixdevs.com/v1` (needs `/v1`), OPENAI_API_KEY). langchain-openai + python-dotenv added; worker load_dotenv().
  - **Gateway constraint:** rejects STREAMING ("concurrency limit exceeded"). Must build the model `disable_streaming=True`. Consequence: no token-level deltas — emit full text per `on_chat_model_end` (one text.delta or text.completed). Token streaming later if the gateway supports it.
  - **Empirical astream_events(version="v2") shapes** (probed): emit on these, skip the rest:
    - `on_tool_start::write_todos` → `todo.updated`, payload `{"todos": data.input["todos"]}` — input.todos IS the CC list `[{content, status: pending|in_progress|completed}]`.
    - `on_tool_start::<name>` (name != write_todos/task) → `tool.invoked` {tool_id, name, args=data.input}; `on_tool_end::<name>` → `tool.returned` {tool_id, name, result=str(data.output)}. (tool_id: data.run_id of the tool event correlates start/end.)
    - `on_tool_start::task` → `subagent.started`; subagent's nested events arrive with metadata identifying it; `on_tool_end::task` → `subagent.finished`. (Handle nesting in a later pass if complex.)
    - `on_chat_model_end::ChatOpenAI` → the AIMessage: if it has tool_calls it's an intermediate turn (skip text); the final one (no tool_calls) → text. (reasoning/thinking content block → thinking.delta when present.)
    - Skip internal graph nodes: `on_chain_*::{LangGraph, model, tools, TodoListMiddleware*, PatchToolCallsMiddleware*}`.
    - Terminal: after the stream ends → `run.completed`; wrap the whole loop and emit `run.failed` on exception (mirror current run_agent's boundary).
- [ ] E3 (session protocol): mirror the new families in `events.ts` (Zod) + `normalize.ts`; relay into replay/SSE. Keep TS/Python in lockstep ([[project-protocol-drift-guard]]).
- [ ] E4 (web): reducer accumulates the new event types; UI renders thinking (collapsible), tools (cards), subagents (nested), todo (live checklist). Transport-agnostic; "use client" stays minimal.
- [ ] E5 (中断恢复): re-attach to an in-flight run via the replay stream is already enabled by the SSE-from-head fix; add resume-generation (continue after stop) if the agent/session can support it.
- [ ] E6 (sessions list): multi-conversation persistence + left-rail list + switch/new/delete.
- [ ] stream_port.py polish (transport foundation, folds in): `_BLOCK_MS` → constructor param; document `_CURSOR_WIDTH`/`_REDIS_FIELD` as cross-language contract constants (NOT .env — would silently break the loop). Filename mirrors `stream-port.ts` (rename both or neither).
