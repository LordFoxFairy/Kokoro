# DDD Cleanup — Three Repos Implementation Plan

> **For agentic workers:** Surgical DDD cleanup. Behavior-preserving only. Every task verifies green before the next. Steps use checkbox (`- [ ]`).

**Goal:** Tidy the DDD architecture of kokoro-session / kokoro-web / kokoro-agent — delete dead code, fix naming, fix the one layering violation, and split god-files into focused collaborators — without changing any behavior.

**Architecture:** Each repo already follows domain/application/infrastructure/interfaces. This pass removes cruft and right-sizes files; it does NOT redesign. Order: session (cleanest, low-risk warm-up) → web (most god-files) → agent (god-file split). Every change is guarded by the existing test suites.

**Tech Stack:** kokoro-session (TS/bun/Zod, kebab-case), kokoro-web (TS/Next/Vitest, kebab-case), kokoro-agent (Python/uv/Pydantic v2, snake_case).

**Source:** 3-agent read-only DDD audit (2026-06-10) + my own grep re-verification. Audit corrections recorded below — do NOT trust the raw audit blindly.

---

## Audit corrections (verified by grep, override the raw audit)

- ❌ **`createConversationStore` is NOT dead** — `tests/application/conversation-store.test.ts` references it 13×. KEEP it. (Audit missed the test file.)
- ⚠️ `activeEntry` (conversation-store.ts), `parseCursorSeq` (session-event.ts) — used internally only; the fix is **drop the `export`** (lower visibility), NOT delete the function.
- ✅ Truly zero-reference, safe to delete: session `memory_store.ts`; web `components/ui/card.tsx`, `sessionEventSchema` + `SessionTransportEvent` exports.
- ✅ agent `ExecutionStyle` is duplicated in `events.py` (domain) and `infrastructure/model.py` (infra). infra importing the domain contract is the CORRECT dependency direction.

---

## Phase 1 — kokoro-session (low-risk, do first, inline)

Verify gate each task: `cd kokoro-session && bun run typecheck && bun run lint && bun test`.

### Task 1.1: Delete dead file `infrastructure/memory_store.ts`
**Files:** Delete `kokoro-session/src/infrastructure/memory_store.ts`
- [ ] Re-confirm zero refs: `grep -rn "memory_store\|appendEvents\|readEvents" src tests` → only the file itself
- [ ] `git rm src/infrastructure/memory_store.ts`
- [ ] Gate green → commit `refactor(session): delete unused memory_store`

### Task 1.2: kebab-case the two snake_case source files
**Files:** `application/start_run.ts` → `start-run.ts`; `infrastructure/replay_store.ts` → `replay-store.ts`; update importers (`main.ts`, `interfaces/http.ts`, tests)
- [ ] `git mv` each; grep importers and fix import paths
- [ ] Gate green → commit `refactor(session): kebab-case start-run / replay-store`

### Task 1.3: Move port contracts into application (dependency inversion)
**Files:** `application/ports.ts` (own the interfaces), `infrastructure/stream-port.ts` + `infrastructure/replay-store.ts` (implement them, type-only import from ports)
- [ ] Read all three; move `StreamPort` + `ReplayStore` *interface* definitions into `application/ports.ts`
- [ ] Infrastructure classes (`MemoryStreamPort`, `RedisStreamPort`, replay-store factory) stay put; `import type` the contracts from `../application/ports`
- [ ] Consumers (`start-run.ts`, `interfaces/http.ts`) import the types from `../application/ports`, not infrastructure
- [ ] Gate green → commit `refactor(session): application owns port contracts`

---

## Phase 2 — kokoro-web (most god-files)

Verify gate each task: `cd kokoro-web && npx tsc --noEmit && npx eslint src && npx vitest run`.

### Task 2.1: Delete dead code (3 sites)
**Files:** `components/ui/card.tsx` (delete file), `infrastructure/protocol/session-event.ts` (drop `sessionEventSchema`, `SessionTransportEvent` exports + `export` on `parseCursorSeq`), `application/conversation-store.ts` (drop `export` on `activeEntry`)
- [ ] Per symbol: re-grep to confirm classification (delete vs un-export). **KEEP `createConversationStore`.**
- [ ] Gate green → commit `refactor(web): remove dead exports + orphan card`

### Task 2.2: Extract persistence schema from `session-stream-reducer.ts` (618→~460)
**Files:** new `application/session-stream-state.schema.ts` (the `.strict()` Zod schemas + `parseStoredSessionState`); reducer keeps `applySessionEvent`/`buildThreadItems`/`computeActivityVersion`/`deriveRunPhase` + types
- [ ] Move schemas, re-export `parseStoredSessionState` so callers are unchanged; Gate green → commit

### Task 2.3: Split `session-stream-preview.ts` (530→~3 files)
**Files:** new `session-stream-simulate.ts` (buildSimulatedReplyEvents/simulateAssistantReply/chunkText/chunkPauseMs), new `session-stream-stream.ts` (openSessionStream/consumeLiveSession/reattachLiveSession + resolveSessionBaseUrl), keep `session-stream-preview.ts` as the `startSessionReply` orchestrator. Public exports unchanged.
- [ ] Move in two commits (simulate, then stream); Gate green after each

### Task 2.4: Split `use-conversation.ts` (631→facade + focused hooks)
**Files:** new hooks `use-persistent-store.ts`, `use-stream-transport.ts`, `use-mode-management.ts`, `use-conversation-list.ts`; `use-conversation.ts` becomes the composing facade returning the same `Conversation` type.
- [ ] **High-risk** — extract one hook at a time, Gate green after EACH (guarded by `session-shell.test.tsx`). Keep the public `Conversation` shape byte-identical.
- [ ] Commit per extracted hook

### Task 2.5 (optional, low priority): Split `composer.tsx` (355)
Only if time permits; extract `use-composer-expand.ts` + mode/controls subcomponents. Skip if it risks visual drift without Playwright budget.

---

## Phase 3 — kokoro-agent (god-file split)

Verify gate each task: `cd kokoro-agent && uv run pytest && uv run ruff check . && uv run pyright`. **After every `uv run`: `git restore uv.lock`** (aliyun mirror churn).

### Task 3.1: Single-source `ExecutionStyle`
**Files:** `infrastructure/model.py` (delete local `ExecutionStyle = Literal[...]`, `from kokoro_agent.events import ExecutionStyle`)
- [ ] Gate green → commit `refactor(agent): single-source ExecutionStyle from domain`

### Task 3.2: Extract content extractors from `run_agent.py`
**Files:** new `content_extractors.py` (`_text_of`, `_reasoning_of`, `_result_text`, `_as_ai_message`, `_is_tool_call_only_chunk`); `run_agent.py` imports them
- [ ] These are pure functions — mechanical move. Gate green → commit

### Task 3.3: Extract event translator from `run_agent.py`
**Files:** new `event_translator.py` (`translate_stream_event`, `RuntimeSubagentToolInput`, `_build_runtime_custom_subagent_tool`, the `_*_TOOL` / `_*_INTENT` constants it needs); `run_agent.py` keeps `drive_agent_events` + `run_agent` + `_build_agent`
- [ ] Heavily tested by `test_run_agent.py` — keep signatures identical. Gate green → commit

---

## Self-review notes
- normalize.ts (session, 209) and composer.tsx (web, 355) are NOT split aggressively — below the pain threshold; splitting risks churn for marginal gain. normalize is a cohesive event mapper.
- Python files stay snake_case — do NOT kebab them.
- Each repo is committed independently on its own branch (session/agent: `feat/three-repo-loop`; web: `feat/bootstrap-shell`).
- The running backends (session :3001, worker, web :3000) will go stale during session/agent edits — restart + re-Playwright the real e2e after Phase 1 and Phase 3 to confirm no behavior drift.

---

## Execution outcome (2026-06-10) — DONE

- **Phase 1 (session):** ✅ all 3 tasks — `e66f4e9` delete memory_store, `0e41095` kebab, `f9a9d8c` ports ownership. 56 bun tests green; restarted + real e2e green.
- **Phase 2 (web):** ✅ 2.1 dead-code/visibility `8b1ace0`, 2.2 schema extract `18d5f83` (618→517), 2.3 preview split `bead691` (531→99 + 273 + 199), 2.4 **partial** `cb524cf` — only `usePersistentStore` extracted (631→579); transport/mode/list conservatively kept (shared state machine, stale-closure hazard). 2.5 composer split — SKIPPED (low priority). 178 vitest green throughout.
- **Phase 3 (agent):** ✅ both tasks — `5c352fe` single-source ExecutionStyle, `4d08d27` split run_agent (535→243 + 78 + 241). 74 pytest, pyright 0, uv.lock un-churned.
- **Final regression:** web+session+agent all split → restarted worker on new code → real e2e green (实时会话已连接 + real todo + answer, zero drift).
- **Audit corrections caught by my grep re-check:** `createConversationStore` NOT dead (tests use it); 4 "dead exports" were internal-only → un-export not delete; `SessionTransportEvent` kept (types public fns).
- **Remaining (future, fresh context):** the use-conversation transport/mode/list hooks split (high-risk, deferred on purpose); composer.tsx split; agent events.py:7 ruff E402 (pre-existing).
