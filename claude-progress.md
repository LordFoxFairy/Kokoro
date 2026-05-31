# Claude Progress

- Date: 2026-05-31
- Active stream: **permission interruption closed loop — DONE (synthetic-first)**. `kokoro-session` 现在拥有 replayable permission lifecycle：`fixture=permission` 直接 append synthetic `permission.required` ask，`POST /sessions/{session_id}/permissions/{request_id}/decision` 负责把同一 `request_id` 原地收敛为 resolved；并已补强两类边界：malformed JSON 返回 `400`，同一个 `sessionId + request_id` 的并发重复提交通过队列串行化，避免双写 resolved 事件。`kokoro-web` 新增 timeline `PermissionCard`、decision helper 与主聊天壳 `?fixture=permission` 透传；agent 仍保持不动。
- Verification passed:
  - `kokoro-session`: `bun test tests/http.test.ts` → 9 pass / 0 fail
  - `kokoro-session`: `bun x tsc --noEmit && bun x eslint . && bun test` → 89 pass / 2 skip / 0 fail
  - `kokoro-web`: `bun run test src/application/__tests__/a2ui-session.test.ts src/interfaces/a2ui/__tests__/permission-card.test.tsx src/interfaces/chat/__tests__/chat-page.test.tsx` → 8 pass / 0 fail
  - `kokoro-web`: `bun x tsc --noEmit && bun run lint && bun run test && bun run build` → all green
  - Browser e2e: `http://127.0.0.1:3000/?fixture=permission` → send message → ask card appears → click `Allow once` → same card resolves to `这一步已经允许继续了。`; console errors = 0; screenshot `permission-card-e2e-resolved.png`
- Session-end handoff (2026-05-31 late night):
  - Fresh reruns before stop: `kokoro-session` focused/full verification re-run green; `kokoro-web` focused/full verification re-run green.
  - Local read-only web quality review: PASS. Remote retry failed twice with infrastructure `504`, so do not treat that as a code verdict.
  - Correction after handoff review: I previously omitted the fourth repo check. Next agent must use a 4-repo checklist (`parent` / `kokoro-agent` / `kokoro-session` / `kokoro-web`) and explicitly verify `kokoro-agent` status even if this permission slice likely did not modify it.
  - Not completed yet: parent repo docs commit+push / `kokoro-agent` status check and possible push / `kokoro-session` / `kokoro-web` permission-slice commits and pushes are still pending.
  - Next agent: if diff boundary is still the same, re-run browser e2e once when Playwright action tools are healthy, then split into repo-scoped commits and push the existing branches.

- Date: 2026-05-31
- Active stream: **agent DeepAgents engine + planning(todo) — DONE end-to-end**. Swapped kokoro-agent's hand-rolled loop for **DeepAgents** (`==0.6.6`, langgraph) behind the Brain interface; `run_agent` is now an `astream_events`→raw-event mapper, fully GENERIC (write_todos flows as an ordinary tool with `args`; agent has no "plan" concept). **Planning lit up end-to-end** via the harness pattern (mirrors Claude Code): **session normalizer recognizes `tool_name==write_todos`** → internal `plan.updated` → A2UI `Plan` component; **web is a pure renderer** (just added a Plan catalog component). Branches `feat/agent-deepagents-planning` on agent+session+web (NOT pushed); parent docs `docs/agent-deepagents-planning`.

## agent DeepAgents + planning (2026-05-31) — DONE
- **Design correction (important):** first draft special-cased `plan.updated` in the AGENT; user pushed back ("isn't todo a frontend concern? backend shouldn't special-case"). Researched Claude Code (TodoWrite/Task are tools; the *harness* recognizes+renders them). Settled on B-refined: **agent generic** (tool.invoked carries `args`), **session(harness) recognizes write_todos→Plan** (one place), **web pure renders**. See spec/plan.
- A (agent): `make_agent()` builds `create_deep_agent` (HarnessProfile excludes FS/execute/sub-agent → todo-only); `run_agent` maps astream_events generically; **offline fake** (`_scripted.py`, bind_tools-override) drives it no-key. 27 pass/2 skip, ruff/pyright green. **DeepAgents facts locked in A1 spike** (0.6.6 not 0.6.7; HarnessProfile key = resolved ls_provider; astream_events shapes).
- B (protocol): agent-events v0.3.0 — tool.invoked optional `args`.
- C (session harness): normalize recognizes write_todos→internal plan.updated{plan_id:"{run}:plan",todos} + suppresses its tool card; projector plan.updated→`Plan{todosPath:{path:"/plans/{id}"}}` (in-place). 79 pass/2 skip. session-stream.md catalog +Plan.
- D (web): `Plan` catalog component (CC/Gemini todo checklist ○/◐/✓, pure render, binds the todos array via `todosPath`). 16 pass, build green.
- E (offline e2e, redis+scripted+Playwright): Plan card (2 todos ✓) + 🔧echo_search✓ + AI text rendered; **0 console errors; Plan stable, no remount** (last round's SSE cursor fix holds). Screenshot `kokoro-web/.playwright-mcp/agent-planning-e2e.png`. Title `📋 计划` was missing (review miss) — fixed post-e2e.
- Spec `docs/superpowers/specs/2026-05-31-agent-deepagents-planning-design.md`; Plan `.../plans/2026-05-31-agent-deepagents-planning.md`.
- Cleanup candidate: `kokoro-agent/tools.py:run_tool` is now dead (DeepAgents executes tools; echo_search/clock still used via TOOL_OBJECTS). Deferred.
- Deferred (next slices): sub-agents (DeepAgents subagents/task), real creation tools (7 generators), FS/sandbox, permissions, Plan interactivity; scripted fake is single-use per worker (rebuild per run — future).

---

## (prev) chat shell × A2UI — DONE (incl. an E2E-found SSE reconnect bug, now fixed + regression-tested)**. Redo kokoro-web chat shell per variant-a-mi-mu + adopt Google A2UI: session emits A2UI v0_9 op stream, web renders via official `@a2ui/react`+`@a2ui/web_core` (v0.10.0, already installed) + custom `kokoro/chat/v1` catalog. Branches pushed + PR'd: kokoro-session#2 (→main), kokoro-web#2 (→feat/bootstrap-shell, web's default), parent Kokoro#4 (→main). All stack on the still-unmerged tools-and-thinking round, so each PR's diff includes that round too. agent unchanged this round; its prior feat/tools-and-thinking now PR'd (kokoro-agent#4 → main). All 4 PRs open: agent#4, session#2, web#2, parent Kokoro#4.

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
