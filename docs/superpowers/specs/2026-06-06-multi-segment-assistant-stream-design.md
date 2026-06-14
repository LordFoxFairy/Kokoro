# Multi-Segment Assistant Stream and Local Process Attachment Design

## Context

Current baseline after the execution-style contract pass and initial demo polish work:
- `kokoro-agent` emits `text.delta`, `text.completed`, and `thinking.delta` with `message_ref`.
- `kokoro-session` normalizes those text/thinking events into browser-facing events with stable `message_id` values.
- `kokoro-web` stores assistant/user messages in a flat `messages[]` list but stores `thinking`, `toolCalls`, `subagents`, and `todos` as single run-scoped buffers on the whole thread.
- `ConversationThread` still assumes the current run has at most one assistant answer bubble after the last user message.

That model is enough for a simple “one answer bubble + one shared process block” UI, but it is not enough for the experience we actually want to demo:
- a single run can produce multiple assistant text segments,
- tools and subagents should appear locally attached to the relevant segment,
- Thinking mode should support richer multi-stage flows,
- replay and interruption recovery should preserve those relationships.

## Problem statement

Today, the system has an identity mismatch:

### What is message-scoped today
- `thinking.delta`
- `text.delta`
- `text.completed`

These all carry `message_ref` at the agent layer and become stable `message_id` values in session/browser.

### What is only run-scoped today
- `tool.invoked`
- `tool.returned`
- `todo.updated`
- `subagent.started`
- `subagent.finished`

These do **not** carry any attachment identity that ties them to a particular assistant message/segment.

As a result, the web layer cannot stably answer:
> Which assistant text segment should this tool call or subagent belong under?

Without that identity, the front end can only:
- keep one shared process block per run, or
- guess based on event order.

That is not stable enough for a product-quality multi-segment conversation model.

## Goal

Upgrade the cross-repo contract so that a run can safely render as:
- user message
- assistant segment A
  - nearby thinking / tool / subagent activity for segment A
- assistant segment B
  - nearby thinking / tool / subagent activity for segment B
- assistant segment C
  - nearby thinking / tool / subagent activity for segment C

while remaining:
- replay-safe
- interrupt-recovery-safe
- mode-aware (`fast | thinking`)
- maintainable across agent → session → web boundaries

## Core design decision

### Attachment identity must become explicit
We should not build “nearby process blocks” on front-end heuristics like “attach activity to the most recent assistant message.”

Instead, we should add one explicit identity unit across the whole pipeline.

### Chosen identity model
Use a stable assistant-segment identity carried as `message_ref` at the agent boundary and normalized to browser-facing `message_id` in session.

That means:
- every assistant text/thinking/tool/subagent event that belongs to a segment shares the same `message_ref`
- session maps that `message_ref` to one stable browser `message_id`
- web stores message-scoped activity by `messageId`

## Why this model

### Better than front-end heuristics
Heuristics based on event order break under:
- replay,
- reconnect,
- out-of-order buffering,
- complex `text → tool → text → subagent → text` runs,
- future model changes.

### Better than introducing a separate `segment_ref`
A separate segment id is possible, but the system already has a functioning text-side `message_ref -> message_id` mapping. Extending the existing identity is less conceptually expensive than introducing a parallel identity namespace unless we later discover a true need to distinguish “message bubble” from “segment”.

## Approaches considered

### Approach A — Front-end heuristic only
- keep current protocol unchanged
- attach tool/subagent activity to the latest assistant message on the web side

**Pros**
- fastest to hack together

**Cons**
- not replay-safe
- not reconnect-safe
- will mis-attach activity in multi-stage runs
- does not meet the user’s “real, comfortable, polished” standard

### Approach B — Cross-repo protocol upgrade using shared `message_ref` **(recommended)**
- extend tool/subagent (and optionally todo) events to carry `message_ref`
- normalize them to stable browser `message_id`
- store activity by message id in the web reducer

**Pros**
- stable
- replay-safe
- reconnect-safe
- clean DDD boundary story
- supports true multi-segment UI

**Cons**
- touches all three repos
- requires migration work across schemas, normalize logic, reducer, and rendering

### Approach C — Introduce a brand-new `segment_ref`
- keep text `message_ref` semantics unchanged
- add a parallel `segment_ref` for attachment

**Pros**
- future flexibility if segments and message bubbles diverge

**Cons**
- more complexity now
- duplicates identity concepts before we need them

## Decision

Choose **Approach B**.

We will use a single assistant-segment identity (`message_ref` at the raw agent layer, `message_id` at the browser-facing session/web layer) as the stable unit for attaching thinking/tools/subagents to the correct assistant segment.

## Cross-repo design

## 1. Agent (`kokoro-agent`)

### Current problem
`run_agent.py` currently assigns `message_ref` to text and thinking independently, and tool/subagent events do not carry any message identity at all.

### Required change
When the agent enters a new assistant segment, it must allocate one shared `message_ref` and use it consistently for:
- `thinking.delta`
- `text.delta`
- `text.completed`
- `tool.invoked`
- `tool.returned`
- `subagent.started`
- `subagent.finished`
- optionally `todo.updated` if todo should become segment-aware later

### Important rule
A single segment should keep the same `message_ref` until the agent intentionally starts another assistant segment.

### First-pass practical interpretation
For the current DeepAgents loop, this means:
- do **not** generate a fresh `message_ref` for thinking and a different one for final text of the same segment
- when tool/subagent events happen during that segment, stamp them with the same `message_ref`
- when a later assistant text segment begins, allocate a new `message_ref`

## 2. Session (`kokoro-session`)

### Current problem
`normalize.ts` only maps `message_ref -> message_id` for thinking/text events. Tool/subagent events are emitted without any `message_id`.

### Required change
Extend raw agent-event schemas and browser-facing session-event schemas so that:
- tool and subagent events carry `message_ref` inbound,
- session normalizes them into browser-facing events carrying `message_id`.

### Browser-facing contract change
The following session events should gain `message_id`:
- `tool.invoked`
- `tool.returned`
- `subagent.started`
- `subagent.finished`
- optionally `todo.updated` only if we decide todo also becomes message-scoped

### Non-goal
Do not change unrelated replay cursor semantics in this pass.

## 3. Web (`kokoro-web`)

### Current problem
Reducer state is run-scoped for activity and message-scoped only for text bubbles.

### Required change
Replace the single shared activity buffers with message-scoped activity state.

### Recommended state shape
Something structurally close to:

```ts
type AssistantSegmentActivity = {
  messageId: string
  thinking: string
  toolCalls: SessionToolCall[]
  subagents: SessionSubagent[]
}

type SessionStreamState = {
  seenEventIds: string[]
  messages: SessionMessage[]
  todos: SessionTodo[]
  activityByMessageId: Record<string, AssistantSegmentActivity>
  runStatus: "idle" | "completed" | "failed"
}
```

This does **not** require collapsing messages and activity into one object immediately, but it does require message-scoped lookup instead of one shared run-level bucket.

### Rendering model
`ConversationThread` should stop assuming “one current assistant answer per run.”
Instead it should render all assistant messages after the last user message, and for each assistant message:
- find the activity bucket for that `messageId`
- render a local process block under or alongside that specific segment

### Transitional compromise
If we need an incremental rollout, the renderer can first:
- support multiple assistant segments,
- attach process only when a matching `activityByMessageId[messageId]` exists,
- keep one fallback shared run-level process block for legacy events during migration.

## 4. Thinking mode behavior

Thinking mode should become structurally richer through this model:
- more segments are allowed naturally,
- each segment can expose a richer local process block,
- subagent/tool milestones can feel attached to the relevant reasoning step instead of floating as a global afterthought.

Fast mode can still remain compact:
- fewer segments,
- lighter local process disclosure,
- quicker collapse behavior.

## 5. Interruption recovery implications

This upgrade is not just visual.
It materially improves interruption recovery because the web state can reconstruct:
- which assistant segments already existed,
- which local process blocks belonged to which segment,
- where later replayed tool/subagent events should attach.

Without explicit attachment identity, reconnect can only restore one coarse shared process area.

## Browser UX consequences

When this design lands, the user will see:
- more natural multi-step assistant turns,
- tools and subagents visually attached to the segment they informed,
- Thinking mode with clearer stage-by-stage progression,
- less ambiguity about which process belongs to which answer fragment.

## Risks

1. **Migration complexity**
This touches all three repos and requires schema, normalize, reducer, and rendering changes.

2. **Partial rollout risk**
If only one repo is upgraded, attachments will be inconsistent. The implementation must be staged carefully and verified end-to-end.

3. **Message-ref lifecycle bugs**
If the agent allocates too many or too few shared refs, activities may still attach incorrectly. Tests must cover segment boundaries explicitly.

## Success criteria

This design is complete when:
1. tool/subagent events carry stable segment/message attachment identity from agent through session to web;
2. web reducer stores process activity per assistant message rather than one shared run bucket;
3. a single run can render multiple assistant segments without dropping later messages;
4. each segment can show nearby process/tool/subagent state correctly after replay or reconnect;
5. Fast and Thinking can diverge not only in wording, but in real segment/process structure.

## Non-goals for this pass

- redesigning the entire visual language of every bubble and panel at the same time
- solving native file upload
- changing transport cursor formats
- introducing a second parallel identity system unless `message_ref` proves insufficient

The priority here is structural correctness first, then demo polish on top of the correct structure.
