# Todo

## kokoro-web bootstrap (done 2026-05-29)
- [x] Create `kokoro-web/` as an independent Git repository.
- [x] Scaffold Bun + Next.js + Tailwind + shadcn/ui baseline.
- [x] Add DDD folders and dependency boundaries.
- [x] Add strict protocol schemas with failing tests first.
- [x] Add replay reducer with failing tests first.
- [x] Render the minimal chat shell using seed events.
- [x] Run test, lint, typecheck, and build.

## three-repo demo slice
- [x] Initialize kokoro-agent repository and push first checkpoint.
- [x] Initialize kokoro-session repository and push first checkpoint.
- [x] Align kokoro-web with the demo chat shell.
- [x] Wire agent->session SSE bridge in code (commits present in all three repos).
- [x] Verify deps install + unit tests green in all three repos (2026-05-30).
- [x] Verify backend e2e via curl: agent->session->SSE replay flows real events (2026-05-30).
- [x] Run the browser leg: web -> session -> live SSE in a real browser + screenshot (2026-05-30, redis backend).
- [x] Add real start commands (console_script `kokoro-agent-worker`; session `bun run start`/`dev`).

## pluggable event loop (done 2026-05-30) — plan: docs/superpowers/plans/2026-05-30-pluggable-event-loop.md
- [x] Protocol: add `docs/protocol/agent-events.md` (agent->session raw contract, v0.1.0).
- [x] agent: strict pydantic raw events + StreamPort(memory/redis) + deterministic worker; drop legacy HTTP echo. ruff/pyright/pytest green (15 pass, 2 redis skip).
- [x] session: zod strict schemas + StreamPort(memory/redis) + Normalizer(raw->AGUI) + relay + SSE server + main.ts. tsc/eslint/bun test green (39 pass, 2 redis skip).
- [x] web: consume live session SSE into reducer. tsc/lint/test/build green (11 pass).
- [x] Real cross-language e2e over redis: Python worker -> Redis -> TS session normalize -> AGUI SSE -> browser render. curl + Playwright screenshot verified.

## agent real-llm brain (done 2026-05-30) — plan: docs/superpowers/plans/2026-05-30-agent-real-llm-brain.md
- [x] `make_chat_model()` provider-pluggable factory (`KOKORO_MODEL`, default anthropic:claude-sonnet-4-6).
- [x] `run_agent` async streaming generator: text.delta (streamed) + text.completed + run.failed; asyncio.timeout; robust str/list content extraction.
- [x] worker awaits the async brain with injected model; idempotency preserved.
- [x] Offline verification only (GenericFakeChatModel) — no real LLM, no API key, no network. ruff/pyright(strict)/pytest green (22 pass, 2 redis skip).
- branch `feat/real-llm-brain` (kokoro-agent PR #2, stacked on #1).

## tools & thinking (done 2026-05-30) — plan: docs/superpowers/plans/2026-05-30-tools-and-thinking.md
- [x] Protocol agent-events v0.2.0: add `thinking.delta` + ordering constraints.
- [x] agent: tool registry + Brain tool-calling loop (self-emits tool.invoked/returned via ainvoke; fake `bind_tools` unsupported so real models bound in make_chat_model) + thinking.delta (gated on execution_style=thinking) + `KOKORO_MODEL=scripted` offline brain. ruff/pyright/pytest green (31 pass, 2 redis skip).
- [x] session: zod schemas + normalize tool.*→tool.started/completed (stable tool_call_id) + thinking.delta→one thinking.summary. tsc/eslint/bun test green (55 tests).
- [x] web: parse new AGUI events + ordered timeline reducer (message/tool/thinking) + ChatGPT/Gemini-style ThinkingBlock + ToolCard. tsc/lint/test/build green (23 tests).
- [x] Offline browser e2e (redis + KOKORO_MODEL=scripted): full family thinking.summary→tool.started→tool.completed→message rendered; collapsible 💭思考 + 🔧echo_search✓ cards; screenshots in kokoro-web/.playwright-mcp/ (gitignored). No real LLM/key.
- branches `feat/tools-and-thinking` on all 3 child repos (PUSHED). NOTE: web branched off `feat/bootstrap-shell`.

## chat shell × A2UI (2026-05-30) — impl done, 1 defect — plan: docs/superpowers/plans/2026-05-30-chat-shell-a2ui.md
- [x] A (session): A2UI op domain + A2uiProjector + SSE a2ui.op wiring. reviewed, 70 pass/2 skip.
- [x] B (web): custom kokoro/chat/v1 catalog (Thread/Message/ThinkingBlock/ToolCard via @a2ui createComponentImplementation) + op SSE consumer + useA2uiSurface. reviewed, green.
- [x] C (web): Sidebar IA + input-pill Composer + ChatPage; deleted legacy session-stream shell. reviewed, 14 tests + build green.
- [x] D (protocol): session-stream.md v2.0.0 (A2UI op stream wire format).
- [x] E (e2e): redis+scripted 3-proc + Playwright — op stream renders 思考/工具/正文 in variant-a-mi-mu style, 0 console errors, screenshots captured.
- [x] **DEFECT fixed (commit 7de7450):** A2uiSurface idle-remount loop was a session SSE bug (subscribe resumed from normalizer cursor, not backend stream cursor → redis XREAD threw → SSE closed → browser reconnect+re-replay loop). Fixed: resume from native StreamItem.cursor + dedicated redis conn per subscribe. Regression test added (verified fails under old cursor). Re-verified in prod browser: stable, thinking expand persists, 0 reconnects.
- [ ] branches `feat/chat-shell-a2ui` (session+web) NOT pushed; no PRs yet. parent docs on `docs/chat-shell-a2ui`.
- [ ] (minor, next) scripted brain iterator is single-use per worker; rebuild per run in make_chat_model so offline e2e can fire multiple runs without worker restart.

## agent DeepAgents + planning (2026-05-31) — DONE — plan: docs/superpowers/plans/2026-05-31-agent-deepagents-planning.md
- [x] A (agent): DeepAgents engine (==0.6.6, todo-only via HarnessProfile) + run_agent astream_events generic mapper + offline scripted fake. 27 pass/2 skip green. (design: agent generic, NO plan event)
- [x] B (protocol): agent-events v0.3.0 — tool.invoked optional args.
- [x] C (session harness): normalize recognizes write_todos→internal plan.updated + suppresses tool card; projector→Plan component (in-place). 79 pass/2 skip. session-stream.md +Plan.
- [x] D (web): Plan catalog component (CC/Gemini ○/◐/✓, pure render). 16 pass, build green. (+ 📋 计划 title fix post-e2e)
- [x] E (offline e2e): Plan card + tool + text rendered, 0 console errors, Plan stable (no remount). Screenshot in kokoro-web/.playwright-mcp/.
- [ ] branches `feat/agent-deepagents-planning` (agent+session+web) NOT pushed; no PRs. parent docs `docs/agent-deepagents-planning`.
- [ ] (cleanup) kokoro-agent tools.py run_tool is now dead (DeepAgents executes tools); remove it + its test next pass.

## next round (not started)
- [ ] agent: sub-agents (DeepAgents subagents/task) end-to-end (mirror Claude Code Task) — next agent slice.
- [ ] agent: real creation tools (image/doc/site generators) behind DeepAgents; scripted fake → rebuild per run.
- [ ] canvas / 产物面板 (artifact.available rendering, 三栏布局).
- [ ] session/SSE 断连中点续传 + replay 硬化 (kill Redis mid-run).
- [ ] Real LLM tool/thinking/planning (needs API key).
- [ ] permissions (safety-and-permission-envelope) wired through agent.
- [ ] web → main trunk question (web work lives on feat/bootstrap-shell lineage, not main).
