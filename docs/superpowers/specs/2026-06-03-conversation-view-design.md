# Conversation View Design

- **Date:** 2026-06-03
- **Status:** approved-by-user-delegation ("一个对话的完美形态")
- **Scope:** `kokoro-web` — evolve the approved minimal first-screen shell into a complete, multi-turn, streaming conversation view, demonstrable standalone.
- **Related:** `docs/superpowers/specs/2026-05-29-three-repo-demo-slice-design.md`, `docs/superpowers/specs/2026-06-02-minimal-web-shell-refinement-design.md`, `docs/protocol/session-stream.md`

---

## 1. Goal

Turn the static first screen into a working conversation: the user types a prompt, their message appears, an assistant reply streams in, the thread accumulates across turns, and run status (streaming / completed / failed) is shown calmly. It must be demonstrable inside `kokoro-web` alone — without `kokoro-session` / `kokoro-agent` running — by gracefully degrading to a local simulated stream that travels the exact same reducer fold path.

This is the complete form of the **current protocol contract** (`session.created`, `run.created`, `message.delta`, `message.completed`, `run.completed`, `run.failed`). It does not add protocol fields.

## 2. What already exists (do not rebuild)

- `applySessionEvent` reducer: dedup by `eventId`, merge deltas by `messageId`, `message.completed` overwrites, terminal `run.completed`/`run.failed`. Replay-safe.
- `consumeLiveSession({input, onState, ...})`: POST run + open SSE + fold per-event + close on terminal + resilient `onerror`.
- Strict zod transport parsing; domain event union (assistant + user roles already modeled).
- The approved empty first screen (rail + hero + calm B-style composer).
- `ArtifactPreview` (A2UI static surface) — kept, unmounted, reserved.

## 3. The architecture gap and the chosen fill

**Problem:** the protocol streams only assistant messages, and each run folds from a fresh reducer state. A multi-turn conversation needs (a) locally-authored user messages and (b) a thread that persists across runs. Per repo boundaries, that cross-turn fold is an **application** concern, not component glue.

**Chosen design — one reducer for the whole thread:**

1. `appendUserMessage(state, {id, content})` (application/reducer): pure; pushes a `role:"user"` message. User messages are local, never server-replayed, so they are not tracked in `seenEventIds`.
2. `consumeLiveSession` gains optional `initialState` (default `createSessionStreamState()`) and `onSettled?`. The shell threads its persistent state in, so each run's assistant events fold on top of the existing thread.
3. Local fallback: `buildSimulatedReplyEvents(input, ids)` (pure, returns ordered domain events) + `simulateAssistantReply({...})` (timer-driven driver) produce a streaming assistant reply through the same reducer when the backend is absent.
4. `startSessionReply` orchestrator: try live; on POST/transport failure, fall back to simulation. Injected into `SessionShell` as an optional prop (default = real orchestrator) so component tests stay timer-free.

**Rejected:** component-owned merge array (leaks fold logic into the view, fragile across turns); reset-per-run (loses history and user bubbles).

## 4. Layout / states

- **Empty** (no messages): the approved hero + centered composer. Unchanged visually.
- **Active** (≥1 message): scrollable Conversation Thread fills the main area, composer pinned to the bottom, hero hidden. User messages right-aligned (uses pre-existing `--surface-user-soft` / `--border-user-soft`), assistant left-aligned prose.
- **Streaming**: calm inline indicator; composer input disabled mid-run.
- **Completed**: indicator clears.
- **Failed**: gentle inline error in the thread; composer re-enabled.

Composer becomes a controlled `<textarea>`: Enter sends, Shift+Enter newlines, disabled while empty or streaming. `+` / mode (`Fast`) / mic stay placeholders per the 06-02 refinement.

## 5. Conflict surfaced (Rule 7)

The 2026-05-29 three-repo design lists a **Run Detail Lane + Artifact Summary Card**. The more recent 2026-06-02 refinement deliberately removed the artifact lane, and `session-stream.md` downgrades `artifact.available` to a reserved parse-and-ignore family outside the current closed loop. **Decision: follow the more recent specs** — no artifact lane this slice; `ArtifactPreview` stays as a reserved component. Flagged here for the architecture review; easy to call back when artifacts are promoted into the contract.

## 6. Boundaries (must hold)

- Transport parsing / SSE wiring stays in infrastructure + application; the reducer/selectors stay transport-agnostic.
- The component renders normalized `SessionStreamState`; it does not touch wire payloads.
- `"use client"` stays confined to `SessionShell`.

## 7. Testing strategy (intent, not just shape)

- **reducer**: `appendUserMessage` accumulates across turns, preserves order with folded assistant messages, is immutable, and user messages survive a subsequent run fold.
- **preview/transport**: `buildSimulatedReplyEvents` is deterministic and terminates with `run-completed`; `consumeLiveSession` with `initialState` keeps prior thread; `simulateAssistantReply` streams to completion (fake timers).
- **shell**: empty state still renders the approved first screen; submitting renders the user message immediately; an assistant reply renders; input is disabled while streaming; a second turn keeps the first turn's messages; failed turn shows an inline error and re-enables input.
- Keep every existing test green.

## 8. Definition of done

`lint` + `typecheck` + `test` + `build` all green; coverage of the new application logic via boundary tests; a visual Playwright pass driving a real multi-turn conversation (empty → send → streamed reply → second turn) with screenshots.
