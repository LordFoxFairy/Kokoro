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

## next round (not started)
- [ ] Tools: `tool.invoked/returned` via astream_events on_tool_start/end (+ optionally DeepAgents loop).
- [ ] `thinking.summary`: execution_style=thinking → Anthropic thinking budget.
- [ ] Boundary: kill Redis mid-run, confirm web recoverable + replay restore.
