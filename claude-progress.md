# Claude Progress

- Date: 2026-05-30
- Active stream: agent real-llm brain — DONE this session (see below)
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
