# Ordered-Parts Streaming Rewrite (kokoro-web)

> Rewrite the multi-segment assistant turn from a "messages + activity-buckets"
> approximation into an **ordered list of typed steps per turn**, so the true
> emission order `thinking → tool → text → tool → text` is faithfully rendered.
> WEB-ONLY: the wire is already ordered (envelope carries `cursor`/timestamp);
> `toSessionStreamEvent` currently discards it. No agent/session change needed.

## Design thesis

One TURN = one avatar + one vertical spine, rendering the agent's work in **true
temporal order**: an append-only sequence of typed steps (reasoning, tool,
subagent, text) where **process is shown ABOVE the text it precedes** (no answer
exists yet to put first; reordering on settle lies about causality and forces a
reflow). At every instant: **exactly one live anchor** (a pulsing caret/shimmer)
on the currently-growing step, gone the instant the run completes. **No state is
ever a blank frame; no running step ever shows an empty box** — a running
tool/subagent shows name + args as content with a determinate running affordance
(label + shimmer + elapsed timer). While live, the tail step is expanded and
prior process auto-collapses to one-line summaries; on completion all successful
process collapses to compact summaries while the answer (and any error) stays
open — **answer-forward by emphasis + disclosure, never by moving DOM**.

## Locked decisions

- **One avatar per TURN** (per assistant run), not per segment. All steps hang
  off one spine under one avatar.
- **Process ABOVE text**, true temporal order, **never reorder DOM on settle**.
- **Ordered Step model**: replace `SegmentActivity{thinking, toolCalls[],
  subagents[]}` with `Step[]` per turn: `Step = { kind:
  'thinking'|'tool'|'subagent'|'text', seq, ...payload }`, `seq` from the
  transport's monotonic order (envelope cursor). Reducer **appends** in seq
  order instead of bucketing by kind. Delete the dead run-level mirror
  (`toolCalls`/`subagents`/`thinking`).
- **Single live anchor** as a first-class singleton: at most one step has
  `isLive=true` (the tail), tracked from the stream, forced false on complete.
  Assert `<=1` live anchor in tests; zero at complete.
- **Tool error state**: `status: running|done|error` + `errorText`; segment-level
  (the turn usually continues), stays expanded.
- **Never-blank running steps**: running tool shows name + args as content +
  "运行中…" affordance (shimmer + elapsed) in the result slot; do NOT auto-open
  into an empty result panel.
- **Collapse without remount**: drive open-state from a derived phase default +
  a per-step user-override; remove the `key={live|settled}` remount.
- **Derived `runPhase`**: `idle | submitted | streaming | settling | complete |
  failed | reconnecting`, computed from `runStatus` + `isStreaming` +
  `transportState` + reattach signals; the thread renders a distinct non-empty
  affordance per phase (esp. submitted-no-token and reconnecting).

## Owner-ruled forks (decided 2026-06-09)

1. **Interleave depth** → segment-level first (process-above-text per segment);
   Step model designed to support full inline (tool→paragraph→tool→paragraph)
   as a follow-up.
2. **Reasoning visibility** → shown muted while live, auto-collapse to「思考 Ns」.
3. **Todo placement** → keep global TodoBar for v1, fix the per-turn wipe
   (`appendUserMessage` wipes todos); moving it into the turn as the first step
   is a later option. (Owner may flip to todo-in-turn.)
4. **Elapsed timer** → thread envelope timestamps; show per-step + total turn
   duration.
5. **Failure** → preserve partial streamed steps; retry re-runs replacing the
   failed turn.

## Target structure

```
<article class="kk-turn kk-turn--assistant" data-phase={runPhase} aria-atomic={isLiveTurn}>
  <div class="kk-turn__avatar kk-turn__avatar--bot" data-live={isLiveTurn}><RobotIcon/></div>  // ONCE
  <div class="kk-turn__spine">
    <ol class="kk-turn__steps">                 // ordered by seq, true emission order
      thinking -> <ReasoningStep muted live defaultOpen={isLive}/>     // above the text it precedes
      tool     -> <ToolStep running|done|error  // running: name+args+运行中 (NEVER empty); error stays open
                            live defaultOpen={isLive || error}/>
      subagent -> <SubagentStep indented nested live/>
      text     -> <AnswerBubble markdown caret={isLive && content}/>   // the ONLY caret, full emphasis
    </ol>
    {phase==='submitted'    && <LiveAnchor kind="thinking"/>}      // #2 never blank
    {phase==='reconnecting' && <LiveAnchor kind="reconnecting"/>}  // #14 distinct
    {phase==='complete'     && <TurnFooter copy retry duration/>}
    {phase==='failed'       && <TurnFailure why partialPreserved retry/>}
  </div>
</article>
```

Invariants (asserted in tests): exactly one `data-live` across the thread (zero
at complete); intra-turn gap < inter-turn gap; cards reserved for AnswerBubble +
collapsed summaries (process steps are quiet rows on the spine); answer never
moves above its process on settle; container does not remount on settle.

Grouping: group consecutive assistant messages of one `runId` under one turn;
interleave their steps by seq; the opening user message renders as a plain
user-side `MessageBubble` above.

## Phased plan (1-3 land together; tests green between phases where independent)

- **Phase 0** — thread a monotonic `seq` onto every domain `SessionStreamEvent`
  in `toSessionStreamEvent` (from the envelope cursor `run_x:NNNN`); add `seq` to
  the event union. Test: ordered fixture → strictly increasing seq. No UI change.
- **Phase 1** — reducer ordered `Step[]` per turn (replace `SegmentActivity`);
  append in seq order; add tool `error`+`errorText`; delete the dead run-level
  mirror; derive `runPhase`. Tests: tool→text→tool→text → 4 ordered steps;
  persistence round-trips; old-snapshot back-compat.
- **Phase 2** — single `TurnContainer` (one avatar + spine), group consecutive
  assistant messages of a run; drop the per-message/orphan AssistantTurn fan-out
  and the always-on status strip. Test: multi-segment turn = ONE avatar;
  inter-turn gap > intra-turn gap.
- **Phase 3** — render steps strictly in seq order, process above text by style
  not position; assert no DOM reorder live→settled.
- **Phase 4** — single live-anchor singleton (tail step from the stream, not the
  "no orphans" heuristic); split `isTextGrowing` (caret) vs `isTurnLive`
  (spinner/expand); force false on complete. Invariant test.
- **Phase 5** — never-blank running steps + explicit tool error state; inline
  param summary, raw JSON only when expanded; cap output height + "show more".
- **Phase 6** — phase-keyed collapse defaults WITHOUT remount; user toggles
  persist within session; summary counts all dimensions (思考过程 · N 工具 · M 子智能体).
- **Phase 7** — distinct submitted-no-token (#2) + reconnecting (#14)
  affordances; failure preserves partial steps; per-state non-empty assertion.
- **Phase 8** — vitest + tsc + Playwright the main path
  (submit→reasoning→tool running→result→text→tool→text→complete) + forced
  reconnect, one screenshot per key state (#2,#4,#6,#8,#12,#14).
