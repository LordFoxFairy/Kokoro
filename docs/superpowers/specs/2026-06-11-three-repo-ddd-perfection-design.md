# Three-Repo DDD Perfection — Design Spec

> Goal: 100% perfect-quality architecture across kokoro-agent / kokoro-web / kokoro-session. Behavior-preserving. Source: a 4-agent read-only Workflow audit (`wf_a0d614dc-5de`) + adversarial cross-repo critic, every dead-code claim grep-verified by me.

## Non-negotiable values (user)
- **Code cleanliness / zero pollution**: re-export compatibility shims ARE pollution; dead code, inconsistent/ugly names, layer violations, cross-module private leaks, decorative comment lines, speculative abstraction — all pollution.
- **Rather delete & rewrite than be polluted**: no kept old names / old paths / shims "to minimize churn".
- **Stream caution**: the stream pipeline is the interactive core; a regression there is high-blast-radius. Stream behaviour and cleanliness must NEVER share a commit.

## Target trees (authoritative blueprint)
Per-repo `targetTree` + full `moves` + `importUpdates` live in the workflow result (`tasks/w68znkzwi.output`). Summary:

### kokoro-agent (needs-restructure: flat → 4 layers)
- `domain/`: `events.py` (AgentEvent+AgentKind, output contract), `run_request.py` (RunRequest+ExecutionStyle, input contract — split out of events.py), `subagent.py` (RegisteredSubagent+SubagentSource — split out of subagents.py)
- `application/run_agent.py`: run_agent + drive_agent_events + _build_agent — **stream-critical, MOVE WHOLE, no split**
- `infrastructure/`: `chat_model.py` (←model.py), `local_fake_model.py`, `stream_port.py`, `stream_translator.py` (←event_translator.py, stream-sensitive), `message_extractors.py` (←content_extractors.py, stream-sensitive), `subagent_registry.py` (←subagents.py registry/materialize)
- `interfaces/worker.py` (←worker.py); update `pyproject [project.scripts]` → `kokoro_agent.interfaces.worker:main`

### kokoro-web (needs-restructure: clean 4-layer, but real pollution)
- Kill 2 re-export shims: `session-stream-preview.ts` (~16 symbols) + `session-stream-reducer.ts` (schema). Consumers import DIRECTLY from real files.
- Rename: `session-stream-stream.ts`→`session-stream-transport.ts`, `session-stream-simulate.ts`→`session-stream-simulator.ts`, `session-stream-preview.ts`→`session-reply.ts` (orchestrator only).
- Delete dead: `lib/utils.ts` (cn) + empty `lib/`; `artifact-preview.tsx` (never imported); dead `isStreamingAssistant` prop (always-false); `components.json` (dead aliases + dead `lucide` iconLibrary); 4 npm deps `@a2ui/react`,`@a2ui/web_core`,`clsx`,`tailwind-merge`.
- Move test `tests/domain/shared/session-event.test.ts` → `tests/infrastructure/protocol/` (mirror source layer).

### kokoro-session (minor-cleanup)
- Delete `domain/sessions.ts` (dead re-export shim + layer violation: domain→application).
- Delete dead `RunRequest` type export in `agent-events.ts`; inline `RunIdFactory` from `ports.ts` into `start-run.ts` (it's a test seam, not a port).
- Rename for symmetry: `events.ts`→`session-event.ts`, `agent-events.ts`→`agent-event.ts` (+ test files).
- Delete `stream-port.ts` box-drawing decorative comment lines; wash `stream-port.ts:160` `as unknown` via Zod parse.

## Critic's adversarial additions (audits missed)
- **P0 cross-repo (separate workstream)**: the 13-kind event contract is hand-maintained in THREE places (agent `events.py` Literal → session Zod ×2 → web TS union), violating the "contract must be codegen single-source" rule. Build a **contract-consistency assertion test first** as the regression net; the codegen single-source is a separate P0, NOT this round's file-shuffle.
- **agent stream files** carry 30+ `cast` / 6 `# pyright: ignore` / 2 `TYPE_CHECKING` / a function-local deferred import / a `# type: ignore` — violate rule 7. Most are the untyped-langchain real boundary (defensible) → **do NOT touch this round** (move whole); address when contract codegen lands.
- web `session-event.ts` (447 lines, codec + mapper dual-responsibility) — evaluate split (deferred unless trivial).
- session `ReplayStore.read` + `mirror` in-memory map = test-only parallel-truth → tests should read `StreamPort.readAll(replayStream(id))`; delete read+mirror (this round if low-risk).
- comment-noise is systemic (reducer 39, conversation-store 17, simulate 20) → per-file PASS/ISSUES, not "fixed two lines".

## Execution strategy (critic's streamRisk neutralization — MANDATORY)
1. **P0 regression net**: write a cross-repo contract-consistency test (diff the 4 kind-sets; red on mismatch) BEFORE any move. Human-designed assertion.
2. **Per-repo order**: delete shims + dead code FIRST (unblocks renames; grep old paths → zero after). 
3. **Stream/contract files = `git mv` + import-path-only, ZERO content edit, OWN commit**; `git diff -w` must show only import lines. Three repos **serial**, each fully green before the next. Never parallel-edit contract files.
4. **Behaviour vs cleanliness NEVER same commit**: commit A = moves/imports only; commit B = comment compaction (stream-file `cast` untouched this round).
5. Verify gate per repo (paste output): agent `uv run pytest`(74)+ruff+pyright + `import kokoro_agent`, then `git restore uv.lock`; session `bun typecheck`+`lint`+`test`(56); web `tsc`+`eslint`+`vitest`(178). Plus **real SSE main path (live send + reattach/reload)** via Playwright — not unit tests alone.

## Scope this round vs separate
- **This round**: 4-layer agent restructure, web naming + de-shim + dead-code, session cleanup, comment compaction (non-stream files), contract regression net, lucide/components.json, session mirror removal.
- **Separate P0 workstream (own spec)**: contract codegen single-source; agent stream-file `cast` convergence (after codegen); web `session-event.ts` split (evaluate); artifact discard-listener removal (decoupled, when artifact feature lands).

## Cross-repo naming convention (critic, unified)
File name = the singular noun phrase of its main export; kebab(TS)/snake(Py); no verbs, no generic plurals, no word-repetition (`session-stream-stream`✗), no redundancy with the dir name. Same logical event stream → one root name across repos: `agent-event` (inbound, agent-produced) / `session-event` (outbound, session-produced). Factories `make*/create*`; pure fns verb-first; ports noun+`Port/Store`; Zod `*Schema`.
