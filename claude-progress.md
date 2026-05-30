# Claude Progress

- Date: 2026-05-30
- Active stream: **chat shell × A2UI — DONE (incl. an E2E-found SSE reconnect bug, now fixed + regression-tested)**. Redo kokoro-web chat shell per variant-a-mi-mu + adopt Google A2UI: session emits A2UI v0_9 op stream, web renders via official `@a2ui/react`+`@a2ui/web_core` (v0.10.0, already installed) + custom `kokoro/chat/v1` catalog. Branches pushed + PR'd: kokoro-session#2 (→main), kokoro-web#2 (→feat/bootstrap-shell, web's default), parent Kokoro#4 (→main). All stack on the still-unmerged tools-and-thinking round, so each PR's diff includes that round too. agent unchanged this round; its prior feat/tools-and-thinking now PR'd (kokoro-agent#4 → main). All 4 PRs open: agent#4, session#2, web#2, parent Kokoro#4.

## chat shell × A2UI (2026-05-30) — impl done, 1 known defect
- **Done + reviewed + green (subagent-driven, spec+quality each):**
  - A (session): `domain/a2ui.ts` op types + `application/a2ui-projector.ts` (SessionEvent→A2UI op; role→author; run.failed idempotent) + SSE `toA2uiSseChunk` + http.ts per-connection projector. 70 pass/2 skip green.
  - B (web): custom `kokoro/chat/v1` catalog + 4 components via `createComponentImplementation` (real @a2ui sig: RenderComponent gets `{props,buildChild,context}`; DynamicString→string, ChildList→`{id,basePath}[]`) + `a2ui-session.ts` + `use-a2ui-surface.ts`. green.
  - C (web): Sidebar IA + input-pill Composer + ChatPage; deleted legacy session-stream shell (8 src + 6 tests). 14 tests, build green.
  - D (protocol): `session-stream.md` v2.0.0 (A2UI op stream wire format).
- **E2E (redis + scripted, 3 procs + Playwright):** ✅ full op stream agent→session→web; rendered 💭思考(folded) + 🔧echo_search✓ + AI msg left-aligned no-bubble, order correct (thread 3 children), variant-a-mi-mu look, **0 console errors**. Shot: `kokoro-web/.playwright-mcp/chat-a2ui-e2e.png` (gitignored).
- **✅ DEFECT FOUND IN E2E → ROOT-CAUSED → FIXED (commit 7de7450):** `<A2uiSurface>` was continuously remounting while idle (thinking `<details>` wouldn't stay expanded + CPU churn). NOT an @a2ui bug — it was OUR session SSE: `streamSession` passed `SessionEvent.cursor` (normalizer cursor `run_id:NNNN`) to `StreamPort.subscribe` as the resume position, but that namespace ≠ backend stream cursor (redis stream id / memory seq). Redis XREAD threw on the bad id (memory adapter filtered live events out) → SSE `res.end()` → browser reconnected every ~2-3s → re-replayed the full op snapshot each time → remount. The live tail had in fact never worked over redis; masked because a completed run's full re-replay looks complete. Fix: read snapshot via `readAll` and resume from native `StreamItem.cursor`; also RedisStreamPort.subscribe now uses a dedicated connection per call (blocking XREAD must not share a connection). Regression test (memory, always-runs) asserts post-connect live ops are delivered; verified to fail under the old cursor. **Re-verified in prod browser e2e: `stillSameDomNode:true`, thinking expand persists (click expand/collapse both stick), 0 reconnects.** Screenshots `kokoro-web/.playwright-mcp/chat-a2ui-{collapsed,expanded}.png`.
- Note (test harness, not a product bug): scripted brain `GenericFakeChatModel(messages=iter(...))` is single-use per worker process (iterator exhausts → 2nd run RuntimeError); restart the worker between offline e2e runs (or make make_chat_model rebuild the iterator per run — future).
- Spec `specs/2026-05-30-chat-shell-a2ui-design.md` (renderer revised to official @a2ui). Plan `plans/2026-05-30-chat-shell-a2ui.md`.

---
## Tools & thinking (completed 2026-05-30)
- Lit up `tool.invoked/returned` + thinking (`thinking.delta`→`thinking.summary`) end-to-end. agent has a tool registry + Brain tool-calling loop (self-emits tool events via `ainvoke`; thinking gated on execution_style=thinking) + `KOKORO_MODEL=scripted` offline brain. session normalizes to tool.started/completed + one thinking.summary. web renders an ordered timeline (message/tool/thinking) with ChatGPT/Gemini-style collapsible ThinkingBlock + ToolCard.
- Verified: 3 repos green offline (no key); redis + scripted browser e2e shows 💭思考 + 🔧echo_search✓ + answer (screenshots in kokoro-web/.playwright-mcp/, gitignored).
- Protocol: agent-events v0.2.0 (+thinking.delta). session-stream.md unchanged (tool.*/thinking.summary already defined).
- Spec: docs/superpowers/specs/2026-05-30-tools-and-thinking-design.md ; Plan: docs/superpowers/plans/2026-05-30-tools-and-thinking.md.
- HANDOFF TODO: open PRs for the 3 child branches + parent docs branch; (base main for agent/session, feat/bootstrap-shell for web).

---
- Branches/PRs: pluggable-event-loop pushed + PR'd (Kokoro#1, kokoro-agent#1, kokoro-session#1, kokoro-web#1). real-llm-brain on `feat/real-llm-brain` (kokoro-agent#2, stacked on #1).

## Agent real-llm brain (completed 2026-05-30)
- `kokoro-agent` brain is now a real streaming LLM (was deterministic echo). Provider-pluggable via `KOKORO_MODEL` (default `anthropic:claude-sonnet-4-6`) through LangChain `init_chat_model` — same shape as the `KOKORO_STREAM_BACKEND` transport axis. `run_agent` is async; streams `astream_events` → text.delta, finishes text.completed + run.completed, errors → run.failed.
- session / web / StreamPort UNCHANGED — brain swap is isolated (normalizer folds deltas by message_id, web renders incrementally).
- Verified OFFLINE only with GenericFakeChatModel — no real LLM, no API key, no network (user's explicit policy). ruff/pyright(strict)/pytest green (22 pass, 2 redis skip).
- Deferred (interface ready): tool.invoked/returned, thinking.summary, DeepAgents loop.
- Spec: docs/superpowers/specs/2026-05-30-agent-real-llm-brain-design.md ; Plan: docs/superpowers/plans/2026-05-30-agent-real-llm-brain.md.

---

## Pluggable event loop (completed 2026-05-30)
- Architecture corrected to ADR-009: agent=pure producer -> Redis Stream -> session=business layer (normalize raw agent events into AGUI envelope + replay) -> SSE -> web=pure renderer. Transport is a pluggable `StreamPort` (memory|redis via `KOKORO_STREAM_BACKEND`); in-memory for tests/single-process, redis for real cross-language (Python<->TS).
- Spec: docs/superpowers/specs/2026-05-30-pluggable-event-loop-design.md ; Plan: docs/superpowers/plans/2026-05-30-pluggable-event-loop.md ; new contract: docs/protocol/agent-events.md (v0.1.0).
- Verified: 3 repos lint/type/test green (memory backend, zero infra); real redis cross-process e2e via curl AND Playwright browser screenshot (kokoro-web/.playwright-mcp/kokoro-e2e-redis-demo.png). Brain kept deterministic this round.
- Redis was installed via `brew install redis` (docker daemon was off). Stopped after the run.
- Not yet: redis-kill-mid-run boundary test; real LLM; pushing branches/PRs.

---
## (history) three-repo demo slice (verification pass)
- Repos (nested clones under parent, gitignored): `kokoro-web`, `kokoro-session`, `kokoro-agent`

- Completed & verified (2026-05-30):
  - All three child repos cloned locally from GitHub (LordFoxFairy/kokoro-{web,session,agent}).
  - Dependencies install clean: `bun install` (web, 459 pkgs), `uv sync` (agent), session has no deps.
  - Unit tests green: web `bun run test` = 7 pass / 3 files; session `bun test` = 3 pass; agent `uv run pytest` = 1 pass.
  - Backend end-to-end chain proven via curl: started agent SSE server (127.0.0.1:8001) + session bridge (127.0.0.1:3001), then POST `/sessions/ses_demo/runs` -> session called agent -> GET `/sessions/ses_demo/stream` replayed real SSE events (session.created -> message.delta -> message.completed -> run.completed) with correct cursors/event_ids/timestamps.

- Known gaps / not yet verified:
  - No process entry points: neither agent (`runner.run()`) nor session (`buildServer().listen()`) has a console-script / npm start. Servers were booted via one-liners for the test. A documented start command is still missing.
  - Browser leg NOT run: web `next dev` (:3000) -> session (:3001) not exercised in a real browser; no screenshot of the chat shell consuming live SSE. Web shell unit tests pass but live consumption is unverified.
  - Agent emits a stubbed echo ("Kokoro received: ...") — DeepAgents/LangChain are dependencies but not yet wired into a real model call.
  - web `bun run lint` / `typecheck` / `build` not re-run this pass (were green at 2026-05-29 bootstrap).

- Next step:
  - Run the browser leg: boot agent + session, `next dev` web, drive the demo in a browser, capture a screenshot. Then add real start commands (console_script for agent, a start script for session).
