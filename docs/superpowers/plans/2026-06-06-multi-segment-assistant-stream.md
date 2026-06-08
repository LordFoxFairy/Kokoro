# Multi-Segment Assistant Stream and Local Process Attachment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade Kokoro so a single run can render multiple assistant text segments, each with its own nearby tools/subagents/thinking block, using stable cross-repo attachment identity instead of run-level heuristics.

**Architecture:** Reuse `message_ref` as the stable assistant-segment identity across agent, session, and web. Extend raw tool/subagent events to carry that identity, normalize them into browser-facing `message_id`, replace the web’s run-scoped activity buckets with message-scoped activity state, and update rendering so each assistant segment gets its own local process block. Keep the migration incremental and replay-safe.

**Tech Stack:** Python + Pydantic (`kokoro-agent`), Bun + TypeScript + Zod (`kokoro-session`), Next.js + React + TypeScript + Vitest (`kokoro-web`).

---

## File map

### `kokoro-agent`
- Modify: `kokoro-agent/src/kokoro_agent/events.py`
  - Extend raw tool/subagent payload contracts with `message_ref`.
- Modify: `kokoro-agent/src/kokoro_agent/run_agent.py`
  - Keep one shared `message_ref` across thinking/text/tool/subagent events for the same assistant segment; only allocate a new one when a new assistant segment truly begins.
- Modify: `kokoro-agent/tests/test_events.py`
  - Assert new payload shape and serialization for tool/subagent events with `message_ref`.
- Modify: `kokoro-agent/tests/test_run_agent.py`
  - Assert segment identity behavior across text/tool/subagent emission.

### `kokoro-session`
- Modify: `kokoro-session/src/domain/agent-events.ts`
  - Accept `message_ref` on tool/subagent events.
- Modify: `kokoro-session/src/domain/events.ts`
  - Add browser-facing `message_id` to tool/subagent events.
- Modify: `kokoro-session/src/application/normalize.ts`
  - Map inbound `message_ref` to stable browser `message_id` for tool/subagent events.
- Modify: `kokoro-session/tests/normalize.test.ts`
  - Cover message-scoped normalization for tools/subagents and multiple assistant segments.
- Modify: `kokoro-session/tests/agent-events.test.ts`
  - Cover schema changes for raw inbound payloads.

### `kokoro-web`
- Modify: `kokoro-web/src/domain/shared/session-stream-event.ts`
  - Add `messageId` to tool/subagent session event variants.
- Modify: `kokoro-web/src/infrastructure/protocol/session-event.ts`
  - Parse the new message-scoped tool/subagent contract.
- Modify: `kokoro-web/src/application/session-stream-reducer.ts`
  - Replace run-level `thinking/toolCalls/subagents` buffers with message-scoped activity buckets.
- Modify: `kokoro-web/src/interfaces/session-stream/components/conversation-thread.tsx`
  - Render all assistant segments after the last user message, not just the first one.
- Modify: `kokoro-web/src/interfaces/session-stream/components/assistant-turn.tsx`
  - Render one process block per assistant segment using its own activity bucket.
- Modify: `kokoro-web/src/interfaces/session-stream/components/process-block.tsx`
  - Consume message-scoped activity instead of one shared run bucket.
- Modify: `kokoro-web/src/interfaces/session-stream/components/subagent-row.tsx`
  - Keep structured milestone presentation but now tied to the correct segment.
- Modify: `kokoro-web/src/interfaces/session-stream/components/tool-call-row.tsx`
  - Keep tool detail presentation but message-scoped.
- Modify: `kokoro-web/tests/application/session-stream-reducer.test.ts`
  - Add failing tests for message-scoped attachment and multi-segment rendering state.
- Modify: `kokoro-web/tests/interfaces/session-stream/session-shell.test.tsx`
  - Add scenario coverage for multi-segment runs and correct local process attachment.
- Modify: `kokoro-web/tests/interfaces/session-stream/process-block.test.tsx`
  - Keep process expectations aligned with segment-scoped data.
- Modify/Create: `kokoro-web/tests/interfaces/session-stream/subagent-row.test.tsx`
  - Validate structured milestone rows under segment-scoped attachment.

### Docs / handoff
- Modify: `claude-progress.md`
- Modify: `tasks/todo.md`

---

### Task 1: Make raw agent activity message-scoped at the source

**Files:**
- Modify: `kokoro-agent/src/kokoro_agent/events.py`
- Modify: `kokoro-agent/src/kokoro_agent/run_agent.py`
- Modify: `kokoro-agent/tests/test_events.py`
- Modify: `kokoro-agent/tests/test_run_agent.py`

- [ ] **Step 1: Write the failing raw-payload test in `kokoro-agent/tests/test_events.py`**

```python
def test_tool_and_subagent_events_require_message_ref() -> None:
    tool_event = AgentEvent(
        kind="tool.invoked",
        run_id="run_01",
        seq=2,
        payload={
            "message_ref": "msgref_01",
            "tool_id": "tool_01",
            "name": "get_weather",
            "args": {"city": "北京"},
        },
    )
    dumped = tool_event.model_dump()
    assert dumped["payload"]["message_ref"] == "msgref_01"
```

- [ ] **Step 2: Write the failing segment-identity test in `kokoro-agent/tests/test_run_agent.py`**

```python
def test_translate_stream_event_keeps_tool_and_subagent_on_current_message_ref() -> None:
    events = [
        {"event": "on_chat_model_end", "name": "ChatOpenAI", "data": {"output": AIMessage(content="第一段")}},
        {"event": "on_tool_start", "name": "get_weather", "run_id": "tool_x", "data": {"input": {"city": "北京"}}},
        {"event": "on_tool_end", "name": "get_weather", "run_id": "tool_x", "data": {"output": "晴"}},
    ]

    out = list(flatten_mapped(events))
    text_ref = out[0][1]["message_ref"]
    assert out[1][1]["message_ref"] == text_ref
    assert out[2][1]["message_ref"] == text_ref
```

- [ ] **Step 3: Run focused agent tests to verify RED**

Run:
```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-agent && uv run pytest tests/test_events.py tests/test_run_agent.py -q
```

Expected:
- FAIL because raw tool/subagent payloads do not yet include `message_ref`, and text/tool identity is not shared by design.

- [ ] **Step 4: Implement the minimal agent contract change**

In `kokoro-agent/src/kokoro_agent/events.py`, update the documented payloads and schema expectations so tool/subagent payloads carry `message_ref`:

```python
#   tool.invoked       {"message_ref": str, "tool_id": str, "name": str, "args": dict[str, object]}
#   tool.returned      {"message_ref": str, "tool_id": str, "name": str, "result": str}
#   subagent.started   {"message_ref": str, "subagent_id": str, "name": str, "description": str}
#   subagent.finished  {"message_ref": str, "subagent_id": str, "name": str}
```

In `kokoro-agent/src/kokoro_agent/run_agent.py`, carry a current segment ref and stamp activity with it:

```python
def current_ref() -> str:
    nonlocal active_message_ref
    if active_message_ref is None:
        active_message_ref = new_ref()
    return active_message_ref

# final text for a segment
body = {"message_ref": current_ref(), "text": payload["text"]}

# tool/subagent events during that segment
{"message_ref": current_ref(), "tool_id": tool_id, ...}
```

Only allocate a new `message_ref` when the next assistant segment truly begins.

- [ ] **Step 5: Re-run focused agent tests to verify GREEN**

Run:
```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-agent && uv run pytest tests/test_events.py tests/test_run_agent.py -q
```

Expected:
- PASS

- [ ] **Step 6: Commit the agent message-scoping slice**

```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-agent && git add src/kokoro_agent/events.py src/kokoro_agent/run_agent.py tests/test_events.py tests/test_run_agent.py && git commit -m "feat: attach agent activity to assistant message refs"
```

---

### Task 2: Normalize message-scoped activity into browser-facing message IDs

**Files:**
- Modify: `kokoro-session/src/domain/agent-events.ts`
- Modify: `kokoro-session/src/domain/events.ts`
- Modify: `kokoro-session/src/application/normalize.ts`
- Modify: `kokoro-session/tests/normalize.test.ts`
- Modify: `kokoro-session/tests/agent-events.test.ts`

- [ ] **Step 1: Write the failing normalize test for tool/subagent message attachment**

```ts
test("tool and subagent events inherit the browser message_id derived from message_ref", () => {
  const n = makeNormalizer()
  const text = n.ingest({
    kind: "text.completed",
    run_id: "run_x",
    seq: 1,
    payload: { message_ref: "seg_1", text: "第一段" },
  })
  const tool = n.ingest({
    kind: "tool.invoked",
    run_id: "run_x",
    seq: 2,
    payload: { message_ref: "seg_1", tool_id: "tool_1", name: "get_weather", args: { city: "北京" } },
  })

  const textMessageId = text[0]?.payload.message_id
  expect(tool[0]?.payload.message_id).toBe(textMessageId)
})
```

- [ ] **Step 2: Run focused session tests to verify RED**

Run:
```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-session && bun test tests/normalize.test.ts tests/agent-events.test.ts
```

Expected:
- FAIL because the current schemas and normalizer do not accept or emit message-scoped tool/subagent attachment.

- [ ] **Step 3: Implement the minimal session contract upgrade**

In `src/domain/agent-events.ts`, add `message_ref` to tool/subagent payload schemas.

In `src/domain/events.ts`, add `message_id` to browser-facing payloads:

```ts
const toolInvokedPayload = z.object({
  message_id: nonEmptyString,
  tool_id: nonEmptyString,
  name: nonEmptyString,
  args: z.record(z.unknown()),
}).strict()
```

In `normalize.ts`, route tool/subagent events through `messageIdFor(event.payload.message_ref)`.

- [ ] **Step 4: Re-run focused session tests to verify GREEN**

Run:
```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-session && bun test tests/normalize.test.ts tests/agent-events.test.ts
```

Expected:
- PASS

- [ ] **Step 5: Commit the session normalization slice**

```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-session && git add src/domain/agent-events.ts src/domain/events.ts src/application/normalize.ts tests/normalize.test.ts tests/agent-events.test.ts && git commit -m "feat: normalize tool and subagent activity by message id"
```

---

### Task 3: Replace run-scoped activity buckets with message-scoped state in the web reducer

**Files:**
- Modify: `kokoro-web/src/domain/shared/session-stream-event.ts`
- Modify: `kokoro-web/src/infrastructure/protocol/session-event.ts`
- Modify: `kokoro-web/src/application/session-stream-reducer.ts`
- Modify: `kokoro-web/tests/application/session-stream-reducer.test.ts`

- [ ] **Step 1: Write the failing reducer test for per-message attachment**

```ts
it("keeps tool and subagent activity attached to the correct assistant message", () => {
  let state = createSessionStreamState()
  state = applySessionEvent(state, msgCompleted("m1", "第一段"))
  state = applySessionEvent(state, toolInvoked("m1", "tool_1", "get_weather"))
  state = applySessionEvent(state, msgCompleted("m2", "第二段"))
  state = applySessionEvent(state, subagentStarted("m2", "sa_1", "researcher"))

  expect(state.activityByMessageId["m1"]?.toolCalls).toHaveLength(1)
  expect(state.activityByMessageId["m2"]?.subagents).toHaveLength(1)
})
```

- [ ] **Step 2: Run the focused reducer test to verify RED**

Run:
```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-web && bun run test tests/application/session-stream-reducer.test.ts
```

Expected:
- FAIL because current state is run-scoped (`thinking/toolCalls/subagents` shared across the whole thread).

- [ ] **Step 3: Implement the message-scoped reducer model**

Refactor `SessionStreamState` toward message-scoped activity:

```ts
export type SegmentActivity = {
  messageId: string
  thinking: string
  toolCalls: SessionToolCall[]
  subagents: SessionSubagent[]
}

export type SessionStreamState = {
  seenEventIds: string[]
  messages: SessionMessage[]
  todos: SessionTodo[]
  activityByMessageId: Record<string, SegmentActivity>
  runStatus: "idle" | "completed" | "failed"
}
```

Update `applySessionEvent()` so:
- `thinking.delta` appends to `activityByMessageId[event.messageId].thinking`
- `tool.invoked/returned` update the bucket for `event.messageId`
- `subagent.started/finished` update the bucket for `event.messageId`
- `appendUserMessage()` resets run-level transient state only as appropriate, without deleting prior message-scoped activity from completed segments in the thread

- [ ] **Step 4: Re-run the reducer tests to verify GREEN**

Run:
```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-web && bun run test tests/application/session-stream-reducer.test.ts
```

Expected:
- PASS

- [ ] **Step 5: Commit the web state-model rewrite**

```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-web && git add src/domain/shared/session-stream-event.ts src/infrastructure/protocol/session-event.ts src/application/session-stream-reducer.ts tests/application/session-stream-reducer.test.ts && git commit -m "refactor: store assistant activity by message id"
```

---

### Task 4: Render all assistant segments and locally attach process blocks

**Files:**
- Modify: `kokoro-web/src/interfaces/session-stream/components/conversation-thread.tsx`
- Modify: `kokoro-web/src/interfaces/session-stream/components/assistant-turn.tsx`
- Modify: `kokoro-web/src/interfaces/session-stream/components/process-block.tsx`
- Modify: `kokoro-web/src/interfaces/session-stream/components/subagent-row.tsx`
- Modify: `kokoro-web/src/interfaces/session-stream/components/tool-call-row.tsx`
- Modify: `kokoro-web/tests/interfaces/session-stream/session-shell.test.tsx`
- Modify/Create: `kokoro-web/tests/interfaces/session-stream/subagent-row.test.tsx`

- [ ] **Step 1: Write the failing rendering test for multiple assistant segments**

```tsx
it("renders every assistant segment after the last user message, each with its own local activity", () => {
  render(<SessionShell startReply={multiSegmentReply()} />)

  send("帮我规划一下")

  expect(screen.getByText("第一段结论")).toBeInTheDocument()
  expect(screen.getByText("第二段补充")).toBeInTheDocument()
  expect(segmentFor("第一段结论")).toContainElement(screen.getByText("get_weather"))
  expect(segmentFor("第二段补充")).toContainElement(screen.getByText("weather-analyst"))
})
```

- [ ] **Step 2: Run focused UI tests to verify RED**

Run:
```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-web && bun run test tests/interfaces/session-stream/session-shell.test.tsx tests/interfaces/session-stream/subagent-row.test.tsx
```

Expected:
- FAIL because `ConversationThread` still renders only the first assistant message in the run tail.

- [ ] **Step 3: Implement the segment-aware renderer**

Refactor `ConversationThread` so it renders all assistant messages after the last user message, each with its own activity bucket lookup.

Sketch:

```tsx
const tail = messages.slice(lastUserIndex + 1)
const assistantSegments = tail.filter((message) => message.role === "assistant")

{assistantSegments.map((message) => (
  <AssistantTurn
    key={message.id}
    message={message}
    activity={activityByMessageId[message.id]}
    isStreaming={isStreaming && message.id === assistantSegments.at(-1)?.id}
  />
))}
```

And update `AssistantTurn` / `ProcessBlock` props accordingly.

- [ ] **Step 4: Re-run focused UI tests to verify GREEN**

Run:
```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-web && bun run test tests/interfaces/session-stream/session-shell.test.tsx tests/interfaces/session-stream/process-block.test.tsx tests/interfaces/session-stream/subagent-row.test.tsx
```

Expected:
- PASS

- [ ] **Step 5: Commit the segment-aware rendering slice**

```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-web && git add src/interfaces/session-stream/components/conversation-thread.tsx src/interfaces/session-stream/components/assistant-turn.tsx src/interfaces/session-stream/components/process-block.tsx src/interfaces/session-stream/components/subagent-row.tsx src/interfaces/session-stream/components/tool-call-row.tsx tests/interfaces/session-stream/session-shell.test.tsx tests/interfaces/session-stream/subagent-row.test.tsx && git commit -m "feat: render multi-segment assistant turns with local process blocks"
```

---

### Task 5: Verify replay/reconnect behavior and update handoff docs

**Files:**
- Modify: `claude-progress.md`
- Modify: `tasks/todo.md`

- [ ] **Step 1: Run full repo gates**

Run:
```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-agent && uv run pytest && uv run ruff check src tests && uv run pyright
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-session && bun run lint && bun run typecheck && bun test
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-web && bun run lint && bun run typecheck && bun run test
```

Expected:
- PASS

- [ ] **Step 2: Run browser-level verification for multi-segment behavior**

Use Playwright and the real dev flow to confirm:
- multiple assistant text segments all render,
- tools/subagents appear under the intended segment,
- Thinking mode can show richer local process blocks,
- reconnect/replay preserves segment-local attachment.

- [ ] **Step 3: Update handoff docs**

Suggested `tasks/todo.md` additions:

```md
- [x] Upgrade the execution stream to support multiple assistant segments with local process attachment.
- [x] Normalize tool/subagent activity to message-scoped identity across agent/session/web.
```

Suggested `claude-progress.md` note:

```md
- 2026-06-06 multi-segment stream upgrade: assistant text, thinking, tool, and subagent activity now attach by message identity, allowing multiple assistant bubbles per run with local process blocks that survive replay and reconnect.
```

- [ ] **Step 4: Commit docs and handoff updates**

```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro && git add claude-progress.md tasks/todo.md docs/superpowers/specs/2026-06-06-multi-segment-assistant-stream-design.md docs/superpowers/plans/2026-06-06-multi-segment-assistant-stream.md && git commit -m "docs: record multi-segment assistant stream upgrade"
```

---

## Self-review

- The design’s core requirement (stable multi-segment assistant bubbles with local process attachment) maps directly to Tasks 1–5.
- No placeholders remain: each step names exact files, commands, and intended behavior.
- The plan respects DDD boundaries by upgrading the contract where the identity gap actually lives, rather than hiding it under front-end heuristics.

Plan complete and saved to `docs/superpowers/plans/2026-06-06-multi-segment-assistant-stream.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
