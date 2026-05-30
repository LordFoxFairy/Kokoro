# Tools & Thinking Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development or superpowers:executing-plans. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Light up `tool.invoked/returned` and thinking (`thinking.delta`→`thinking.summary`) end-to-end (agent→session→web), rendering ChatGPT/Gemini-style collapsible tool cards + thinking blocks. Offline-only verification (fake / scripted brain, no API key).

**Architecture:** agent gains a `Brain` that runs its own tool-calling loop (emits `tool.invoked/returned` itself; fake model's `ainvoke` returns `tool_calls`) + a tool registry, plus a `scripted` brain (`KOKORO_MODEL=scripted`) for offline browser demos. session normalizes tool/thinking raw events into the AGUI envelope. web reducer becomes an ordered timeline (message | tool | thinking) and renders collapsible cards/blocks.

**Tech Stack:** Python (LangChain `ainvoke`/`astream`, fake_chat_models, Pydantic strict, pytest-asyncio); TS (Bun, Zod strict, vitest); Next.js/React (Playwright for screenshot). Tests: `GenericFakeChatModel` — no real LLM/key/network.

**Contracts:** `agent-events.md` v0.2.0 (thinking.delta added), `session-stream.md` v1.0.0 (tool.started/completed, thinking.summary — unchanged). Spec: `docs/superpowers/specs/2026-05-30-tools-and-thinking-design.md`.

**Conventions:** strict schemas, no bare print/except (boundary except → run.failed/tool error only), asyncio.timeout, surgical changes, TDD red→green, frequent commits, end LSP+linter+tests green per repo.

**Verified facts (de-risked):** `GenericFakeChatModel.ainvoke(...)` returns an `AIMessage` carrying `.tool_calls` ✓. `bind_tools` raises `NotImplementedError` on the fake → Brain must NOT bind on the injected (test) model; real models are bound inside `make_chat_model`. Tests inject a fake pre-scripted with tool_calls / thinking content blocks.

---

## Chunk A: kokoro-agent — tool loop + thinking + scripted brain

Dir `kokoro-agent/`. Branch off `main` (e.g. `feat/tools-and-thinking`). Tests: `uv run pytest`.

### Task A1: tool registry
- Create `src/kokoro_agent/tools.py`: a registry mapping `tool_name -> Callable[[dict], str]` + the LangChain `@tool` objects for binding. Provide deterministic tools: `echo_search(query: str) -> str` (returns `f"results for {query}"`), `clock() -> str` (returns a fixed stamp injected for determinism, NOT real time). Expose `TOOL_CALLABLES: dict[str, Callable]`, `TOOL_OBJECTS: list` (for bind_tools), and `run_tool(name, args) -> tuple[str, str]` returning `(status, output)` where status ∈ `{"ok","error"}` (unknown name / raising tool → `("error", msg)`).
- Test `tests/test_tools.py`: known tool returns ok+output; unknown → error; raising tool → error (no crash).
- Commit `feat(agent): deterministic tool registry`.

### Task A2: Brain tool-calling loop (emits tool.invoked/returned)
- Modify `run_agent.py` (or new `brain.py` imported by worker) — keep `run_agent(req, model) -> AsyncIterator[AgentEvent]`, now a loop:
  1. `run.started` (seq=1).
  2. Loop: `ai = await model.ainvoke(messages)` (messages seeded `[("user", req.input)]`).
     - If `req.execution_style == "thinking"`: extract thinking text from `ai.content` list `{"type":"thinking"}` blocks → `thinking.delta{text}` (use the same robust block-walk as `_text_of`; add `_thinking_of`).
     - If `ai.tool_calls`: for each → `tool.invoked{tool_call_ref=tc["id"], tool_name=tc["name"]}`; `status, output = run_tool(tc["name"], tc["args"])`; `tool.returned{tool_call_ref, tool_name, status}`; append `ToolMessage(output, tool_call_id=tc["id"])` + the assistant `ai` to messages; continue loop.
     - Else (final text): emit `text.delta` for the text (you may stream via `model.astream` for the final turn, or split `ai.content` text into one delta — keep robust `_text_of`), then `text.completed{message_ref:"m1", text:full}`; break.
  3. `run.completed{status:"completed"}`. Wrap loop in `try/except` → `run.failed`. `asyncio.timeout(120)`.
  - Guard against infinite tool loops: cap iterations (e.g. 8) → on exceed, `run.failed{error_kind:"ToolLoopLimit"}`.
- Tests `tests/test_run_agent.py` (extend): fake model scripted `[AIMessage(content="", tool_calls=[echo_search...]), AIMessage(content="Final")]` → assert order `run.started, tool.invoked, tool.returned, text.delta*, text.completed, run.completed`, seq monotonic, tool_call_ref matches. `thinking` style with content `[{"type":"thinking","thinking":"reasoning"},{"type":"text","text":"Final"}]` → assert `thinking.delta` emitted before text, thinking text not leaked into text.delta. `fast` style → no thinking.delta. Tool error path → `tool.returned{status:"error"}`.
- Commit `feat(agent): brain tool-calling loop with tool + thinking events`.

### Task A3: scripted brain + make_chat_model branch
- Modify `infrastructure/model.py`: `KOKORO_MODEL=scripted` → return a `GenericFakeChatModel`-based scripted model that yields, deterministically, one thinking block + one tool_call(echo_search) + a final text — so an offline run produces the full event family. Real branch: `init_chat_model(spec).bind_tools(TOOL_OBJECTS)`.
- Worker: still `make_chat_model()` in `_serve`; pass execution_style through (already on RunRequest).
- Test `tests/test_model.py`: `KOKORO_MODEL=scripted` build returns a model whose run (through `run_agent` with execution_style="thinking") yields thinking + tool + text events. No network.
- Commit `feat(agent): scripted offline brain (KOKORO_MODEL=scripted)`.

### Task A4: green gate
- `uv run ruff check . && uv run pyright && uv run pytest -q` green. Commit `chore(agent): tools/thinking lint/type/test green`.

---

## Chunk B: kokoro-session — normalize tool + thinking

Dir `kokoro-session/`. Branch `feat/tools-and-thinking`. Tests: `bun test`.

### Task B1: inbound zod schemas
- `src/domain/agent-events.ts`: add `tool.invoked`, `tool.returned`, `thinking.delta` variants to the discriminated union (`.strict()`; payload required per contract).
- Test `tests/agent-events.test.ts`: strict accept/reject for the new kinds.
- Commit `feat(session): zod schemas for tool/thinking agent events`.

### Task B2: normalizer mapping
- `src/application/normalize.ts`: map `tool.invoked → tool.started{tool_call_id, tool_name}` and `tool.returned → tool.completed{tool_call_id, tool_name, status}` (stable `tool_call_ref → tool_call_id` map, like message_ref). Accumulate `thinking.delta` text; on `run.completed`/`run.failed` (or first non-thinking event after thinking) emit ONE `thinking.summary{run_id, summary}` with the accumulated text. Keep `(run_id, seq)` idempotency. Output validated against the AGUI `eventSchema` (extend it if `tool.started/completed`/`thinking.summary` weren't modeled in `domain/events.ts` — add them per session-stream.md).
- Test `tests/normalize.test.ts`: tool pair → started/completed with stable id; thinking deltas → single summary; raw thinking beyond summary not emitted; ordering + idempotency.
- Commit `feat(session): normalize tool/thinking into AGUI envelope`.

### Task B3: green gate
- `bunx tsc --noEmit && bunx eslint . && bun test` green. Commit `chore(session): tools/thinking lint/type/test green`.

---

## Chunk C: kokoro-web — timeline reducer + ChatGPT/Gemini UI

Dir `kokoro-web/`. Branch `feat/tools-and-thinking`. Tests: `bun run test`.

### Task C1: event domain + parser
- `src/domain/shared/session-stream-event.ts`: add `tool-started{toolCallId, toolName}`, `tool-completed{toolCallId, toolName, status}`, `thinking-summary{runId, summary}` to the union.
- `src/infrastructure/protocol/session-event.ts`: strict-parse the new AGUI events (`tool.started`/`tool.completed`/`thinking.summary`) → domain kinds.
- Test: parser accepts new events, rejects malformed.
- Commit `feat(web): parse tool/thinking AGUI events`.

### Task C2: timeline reducer
- `src/application/session-stream-reducer.ts`: introduce `TimelineItem = {type:"message",...} | {type:"tool", toolCallId, toolName, status:"running"|"done"} | {type:"thinking", summary}` and `timeline: TimelineItem[]` ordered by arrival. `tool-started` pushes a running tool item; `tool-completed` flips it to done; `thinking-summary` pushes a thinking item; message-delta/completed fold messages as today but as timeline items. Keep eventId idempotency. Preserve existing `messages`/`runStatus` (derive messages from timeline or keep both).
- Test `tests/application/session-stream-reducer.test.ts`: interleaved sequence (thinking → tool started → tool completed → message delta×2 → completed → run completed) yields the expected ordered timeline with tool flipping running→done; idempotent replay.
- Commit `feat(web): ordered timeline reducer (message/tool/thinking)`.

### Task C3: ChatGPT/Gemini-style rendering
- New components `src/interfaces/session-stream/thinking-block.tsx` (collapsible `💭 思考 ▸`, expands to summary) and `tool-card.tsx` (`🔧 {toolName}` with running spinner → done check; expandable). Update `session-shell.tsx` to render the timeline in order. Match the warm Kokoro design language (reuse existing card styles/tokens). No `any`.
- Test: component/render tests asserting collapsed-by-default, expand reveals content, tool running vs done states.
- Commit `feat(web): chatgpt/gemini-style thinking block + tool card`.

### Task C4: green gate
- `bunx tsc --noEmit && bun run lint && bun run test && bun run build` green. Commit `chore(web): tools/thinking lint/type/test/build green`.

---

## Chunk D: integrated offline browser verification (controller)

- [ ] Start redis (`redis-server --daemonize yes`) OR use `KOKORO_STREAM_BACKEND=memory` is single-process — for 3-process demo use redis.
- [ ] `KOKORO_STREAM_BACKEND=redis KOKORO_MODEL=scripted` start agent worker + session + web dev.
- [ ] Playwright: load web, trigger the scripted run, observe the thinking block + tool card(s) + streamed answer; expand the thinking block and a tool card; screenshot (collapsed and expanded).
- [ ] Stop processes/redis; tidy.

## Done criteria
- 4 repos LSP/linter/tests green; offline only (fake/scripted brain, no key/network).
- Event families `tool.invoked/returned` + `thinking.delta` flow agent→session→web; session emits `tool.started/completed` + one `thinking.summary`; web renders ordered timeline with collapsible ChatGPT/Gemini-style thinking block + tool cards (screenshot captured).
- agent raw kinds only; web consumes AGUI only; session owns normalization. No cross-repo imports.
