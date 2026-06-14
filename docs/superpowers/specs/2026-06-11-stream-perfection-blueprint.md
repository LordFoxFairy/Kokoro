# Stream Perfection Blueprint — Three Repos

> Source: top-architect deep-audit Workflow (`wf_615794d0-e13`, 4 agents: stream-design + architecture + code-quality + adversarial critic), every claim grep-verified. This is the authoritative execution blueprint for the "全面打磨到极致" pass.

## Perfect end-state (4 invariants × 3 repos)
1. **Single-source contract** — the 13 event kinds + payload shapes + transport constants (CURSOR_WIDTH=20/REDIS_FIELD/BLOCK_MS) + run.completed.status enum live in ONE `/Kokoro/contract/events.yaml`, a deterministic (no-model) generator emits the 6 mirrors (agent events.py, session agent-event.ts + session-event.ts, web protocol union + domain SessionStreamEvent) with `@generated` banners; CI runs generator + `git diff --exit-code`. Replaces `check-contract-kinds.sh` (whose equality premise is already FALSE — the repos carry different kind subsets — and which isn't wired to CI).
2. **Zero speculation** — delete dead/speculative kinds with no emitter: `artifact.available`, `permission.required`, web-side `run.created` transit (session emits, web maps to null), `run.completed.artifact_ids`, domain `artifactIds`, and `deriveRunPhase`/`RunPhase`/`lastAssistantRunId` (consumed only by their own tests).
3. **Total order** — `seq` becomes a first-class integer field on the envelope (session Normalizer writes agent's seq); web deletes `parseCursorSeq` regex; ordering is total, no malformed-cursor→seq=0 degradation.
4. **Pure structural layering** — `message_ref↔message_id↔messageId` collapses to one agent-assigned `segment_id`; `drive_agent_events`' 3 nonlocals + two byte-identical `ref_for_segment_*` fns collapse into an explicit `Segmenter`; `seenEventIds` array→Set; god-files split; flat dirs get concern subdirs (≥3 same-prefix files).

## P0 gate (DONE)
`scripts/sse-loopback-gate.sh` — real agent→session→Redis→session SSE main-path, scripts the kind-sequence assertion. The critic's #1 blind spot: the "real SSE e2e" the audits assumed as a gate did NOT exist (web only had vitest). **Run this after every stream-pipeline change.** Prereqs: Redis db14 + session :3001 + worker (LOCAL_FAKE_MODEL).

## Execution order (behavior vs cleanliness STRICTLY separated; 3 repos serial; stream files structural-only + gate after each)
1. ✅ P0 SSE loopback gate (`scripts/sse-loopback-gate.sh`).
2. baseline green (web vitest+tsc / session bun+tsc / agent pytest+ruff+pyright) — oracle.
3. **web** delete speculative dead code (artifact/permission/run.created-on-web/artifact_ids/artifactIds + deriveRunPhase trio). Zero emitter (grep-proven), zero behavior. HIGH leverage, lowest risk — harvest first.
4. **web** delete deriveRunPhase/RunPhase/lastAssistantRunId (only reducer.test consumes) + their tests.
5. **web** `seenEventIds` array→Set (Set in memory O(1), disk stays array via z.array; array→Set on load, Set→array on save).
6. **web** split `protocol/session-event.ts` (447) → `session-event-schema.ts` (schemas+parseSessionEvent) + `session-event-mapper.ts` (parseCursorSeq+toSessionStreamEvent); extract a `base()` envelope-projection helper for the 16-case switch.
7. **web** comment de-noise (reducer/use-conversation/simulator multi-line → ≤1-line WHY); fix reply.ts stale file pointers.
8. **session→web** seq → first-class integer envelope field. **✅ DESIGNED (probe workflow `wf_dbad81b7`, 8 agents + 3 adversarial critics, all grep-verified).**
   **⚠️ CORRECTION of my prior note:** the "redis trailing-seq resets every ms" was a MISDIAGNOSIS. web's cursor is the Normalizer-built DOMAIN cursor `run_x:NNNN` (`normalize.ts:197`, per-run monotonic counter `++cursorSeq` padded 4) — NOT the redis xadd id. The redis id lives ONLY in the transport layer (StreamItem.cursor, used for server-side resubscribe `xread` lastId) and NEVER reaches web (SSE `id:`=`event.cursor`=domain `run_x:NNNN`; `item.cursor` is discarded at http.ts:136). So the reset does NOT occur in current code — it's only a *latent* fragility in mapper.ts's claimed `NNNN-NNNN` compat comment, structurally removed once seq is its own field.
   **Final design (minimalism critic OVERRODE the workflow's own draft):**
   - seq source = **pass through agent's inbound `event.seq`** (`agent-event.ts:83`, ALREADY consumed for idempotency at `normalize.ts:39`) — ZERO new state. The draft's "new `envelopeSeq` counter" is YAGNI: agent seq already exists, backend-agnostic, per-run monotonic. Synthesized events (`run.started`→session.created+run.created) reuse the run.started seq; harmless (session.created never enters `stepsByRun`; run.created maps to null at web).
   - web schema seq MUST be **R2 (optional + mapper fallback `event.seq ?? parseCursorSeq`)**, NOT required. behavior-compat BLOCKER: redis replay stream has NO MAXLEN/EXPIRE (`stream-port.ts:99`) + session ignores Last-Event-ID while web uses native EventSource (auto-reconnect re-sends FULL replay) → required-seq would reject pre-upgrade no-seq envelopes forever → whole-stream crash. R2 mandatory unless db14 flushed AND no long-lived sessions.
   - SSE gate assertion = **per-runId grouped monotonic**, NOT whole-stream. HARD FACT (3 critics concur): replay is per-SESSION single stream carrying MULTIPLE runs (`start-run.ts:71` append(sessionId); `http.ts:128` subscribe(replayStream(sessionId))); per-run seq resets at each run boundary — fine for reducer (only compares within `stepsByRun[runId]`) but "whole-stream increasing" is a FALSE invariant that would mis-fail the gate on any multi-run session.
   - TDD must cover `reducer.ts:100` `withRestoredTextSteps` `Math.max(seq)` baseline (absolute-value dep) + update `reducer.test` seq fixtures (currently `run_01:0001..0004→[1,2,3,4]`).
   - cursor unchanged. ~few lines; memory-mode behavior-zero (agent seq per-run monotonic == current cursorSeq-derived).
   **Latent BLOCKER, orthogonal to seq — do NOT fix here, separate ticket:** SSE `id:`=per-run cursor `run_x:NNNN`; if anyone wires Last-Event-ID resume, it cross-run-rewinds and drops events.
9. **all** contract codegen — `/Kokoro/contract/events.yaml` single source. **✅ PHASE 1 DONE (`a1c02dd`):** events.yaml is now the single source for 13 kinds × 3 views (agent-out/agui-out/render) + payload field-name sets + transport constants + status; `contract/verify.py` is the deterministic drift gate (structural parse of all 6 files, per-view kind-set + field-name-set assertion, exit≠0 + precise file·kind·field report on drift; injection-tested). Replaces & deletes `check-contract-kinds.sh` (false byte-identical premise). Zero contract-source touched, 74/56/170 unchanged. **PHASE 2 (deferred — YAGNI for early-stage chatbot, gate already stops drift):** deterministic generator → regenerate 6 mirrors + generate-and-diff byte-reproduce + flip to `@generated` source + CI `git diff --exit-code` + extend verify.py to type/required/naming-style. Trigger phase 2 only when contract-change frequency justifies it. humanGate.
10. **agent** `drive_agent_events` → explicit `Segmenter` (open/openIfClosed/close/current) replacing 3 nonlocals + 2 byte-identical ref fns; thin dispatcher. TDD, segment-boundary tests as oracle, emission order zero-change. humanGate.
11. **session** split `runRequestSchema` out of `domain/agent-event.ts` → `domain/run-request.ts`. Pure move.
12. **agent** `events.py`→`agent_event.py` (the only plural domain file). Must follow codegen flip (or update generator output path).
13. **web** `components/` (13 flat) → `thread/` (8) + `composer/` (2), icons.tsx at root; mirror the test tree.
14. **web** flatten single-file concern subdirs: `domain/shared/session-stream-event.ts`→`domain/`, `infrastructure/protocol/session-event*.ts`→`infrastructure/` (after step6 it's 2 files, <3 rule → flatten).
15. **all** run.completed.status → shared enum (completed|cancelled|timeout); web relaxes z.literal('completed') so a new terminal state can't strict-parse to null (client never settles).
16. **all** delete redundant activity-event `message_ref` (tool/subagent keyed by id). NON-behavior-preserving; only after segment_id lands. Last.

## Critic missedGaps (resolve during execution)
- **run.created double-handling**: session emits it, web maps to null. Don't half-fix — either session also stops emitting OR web keeps the null-case + documents "deliberately emit / deliberately drop". Pick one.
- **protocol split (step6) vs flatten (step14) order**: split FIRST (447→2 files), flatten LAST (2 files <3 → land them in infrastructure/ root). Conflicting if reordered.
- **transportEventNames from-enum derivation**: must keep a live EventSource listener per kind — a missing registration = silent dropped event. SSE gate must assert per-kind listener.
- **seenEventIds Set migration**: keep z.array(z.string()) schema (Set isn't JSON-serializable); Set lives in memory only.
- **codegen byte-reproduce difficulty**: 3 different kind subsets (agent-out vs agui vs render) + 2 naming styles (snake↔camel, dot↔kebab) + envelope add/drop fields — the mapping table is itself a new single point. Hence the two-phase split.
- **workspace hygiene**: root 29 PNGs / tmp / claude-progress noise — gitignore before the codegen `git diff --exit-code` gate, else dirty files pollute it.

## Status (done so far this arc)
Three-repo DDD 4-layer + naming + de-shim + dead-code (11 commits) · Lessie frontend (2) · web `application/session-stream/` subdir (1) · **agent cast cleanup 35→6 type-shims, pyright 0/0/0** (6 commits, SSE-gate verified) · P0 SSE loopback gate · steps 3–7/11/13/14 web+session cleanliness · **step9 contract codegen PHASE 1 (`a1c02dd`): events.yaml single source + verify.py drift gate, injection-tested, zero contract-source touched, 74/56/170 unchanged**.

**Remaining = behavior-面 stream changes, each warrants a focused session (user: "stream 出问题影响过大"):**
- step8 seq first-class — design depth found (redis cursor non-monotonic, see step8 above); needs brainstorming→TDD→SSE-gate.
- step10 Segmenter — the most fragile (3 nonlocals + 2 byte-identical ref fns); TDD with segment-boundary oracle.
- step12 events.py→agent_event.py rename (mechanical).
- step15 status enum (small contract tighten across 3 repos).
- step16 delete activity message_ref — NON-behavior-preserving, only after segment_id; last.
- step9 phase 2 (generator flip) — deferred YAGNI.
