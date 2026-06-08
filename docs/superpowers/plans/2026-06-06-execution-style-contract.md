# Execution Style Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn `execution_style` from a display-only UI concept into a real per-run execution contract across `kokoro-web`, `kokoro-session`, and `kokoro-agent`.

**Architecture:** Keep `execution_style` as the stable business-level mode `fast | thinking`. Thread that mode from the web conversation state into the live run request, validate and relay it strictly in session, and resolve it inside agent to a per-run execution configuration that changes actual runtime behavior. Rewrite the agent model-lifecycle seam if necessary; do not leave a worker-global single model that makes per-run style impossible.

**Tech Stack:** Next.js + TypeScript + Vitest (`kokoro-web`), Bun + TypeScript + Zod (`kokoro-session`), Python 3.14 + Pydantic + pytest + LangChain/DeepAgents (`kokoro-agent`).

---

## File map

### `kokoro-web`
- Modify: `kokoro-web/src/application/session-stream-preview.ts`
  - Add `executionStyle`/`mode` to the request-building path and remove `execution_style=default`.
- Modify: `kokoro-web/src/interfaces/session-stream/hooks/use-conversation.ts`
  - Thread the active mode into `startReply()`.
- Modify: `kokoro-web/tests/application/session-stream-preview.test.ts`
  - Add failing assertions for `fast`/`thinking` query propagation.
- Modify: `kokoro-web/tests/interfaces/session-stream/session-shell.test.tsx`
  - Verify selected mode affects the live request path while lock behavior remains intact.

### `kokoro-session`
- Modify: `kokoro-session/src/domain/agent-events.ts`
  - Narrow `execution_style` to the explicit allowed values for this pass.
- Modify: `kokoro-session/src/interfaces/http.ts`
  - Keep reading the query value, but fail loud through stricter schema validation.
- Modify: `kokoro-session/tests/http.test.ts`
  - Add request-path coverage for valid/invalid `execution_style`.
- Modify: `kokoro-session/tests/start-run.test.ts`
  - Assert `execution_style` enters `run.request` unchanged.
- Modify: `kokoro-session/tests/agent-events.test.ts`
  - Update schema expectations to match the narrowed contract.

### `kokoro-agent`
- Modify: `kokoro-agent/src/kokoro_agent/infrastructure/model.py`
  - Introduce per-run execution-style resolution and model acquisition logic.
- Modify: `kokoro-agent/src/kokoro_agent/worker.py`
  - Stop relying on one worker-global model instance if that blocks per-run mode behavior.
- Modify: `kokoro-agent/src/kokoro_agent/run_agent.py`
  - Ensure the per-run resolved model is used for this request.
- Modify: `kokoro-agent/tests/test_model.py`
  - Add failing tests for execution-style resolution.
- Modify: `kokoro-agent/tests/test_worker.py`
  - Add failing tests proving different run requests can resolve different configs.
- Create or Modify: `kokoro-agent/tests/test_run_agent.py`
  - Only if needed to assert the resolved per-run model reaches the DeepAgents execution path.

### Docs / handoff
- Modify: `tasks/todo.md`
  - Mark this line accurately as complete only after all repos and live verification pass.
- Modify: `claude-progress.md`
  - Record what changed, what was rewritten, and how the live verification proved the contract.

---

### Task 1: Prove web currently ignores the selected mode

**Files:**
- Modify: `kokoro-web/tests/application/session-stream-preview.test.ts`
- Modify: `kokoro-web/tests/interfaces/session-stream/session-shell.test.tsx`

- [ ] **Step 1: Write the failing request-builder test in `kokoro-web/tests/application/session-stream-preview.test.ts`**

```ts
it("sends the selected execution_style on the live run request", async () => {
  const fetchMock = vi.fn().mockResolvedValue({ ok: true })
  global.fetch = fetchMock as typeof fetch
  global.EventSource = class {
    addEventListener() {}
    removeEventListener() {}
    close() {}
  } as unknown as typeof EventSource

  await consumeLiveSession({
    input: "你好",
    sessionId: "ses_01",
    conversationId: "conv_01",
    executionStyle: "thinking",
    onState: () => {},
  })

  const requestUrl = new URL(fetchMock.mock.calls[0][0] as string)
  expect(requestUrl.searchParams.get("execution_style")).toBe("thinking")
})
```

- [ ] **Step 2: Run the focused web test and verify RED**

Run:
```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-web && bun test tests/application/session-stream-preview.test.ts
```

Expected:
- FAIL because `ConsumeLiveSessionInput` does not accept `executionStyle` yet, or because the request still uses `default`.

- [ ] **Step 3: Write the failing UI threading test in `kokoro-web/tests/interfaces/session-stream/session-shell.test.tsx`**

```tsx
it("passes the active mode into the live reply start path", async () => {
  const startReply = vi.fn().mockReturnValue({ close: () => {} })
  render(<SessionShell startReply={startReply} />)

  await userEvent.click(screen.getByLabelText("切换模式"))
  await userEvent.click(screen.getByText("Thinking"))
  await userEvent.type(screen.getByLabelText("对话输入"), "帮我规划一下")
  await userEvent.keyboard("{Enter}")

  expect(startReply).toHaveBeenCalledWith(
    expect.objectContaining({ executionStyle: "thinking" }),
  )
})
```

- [ ] **Step 4: Run the focused UI test and verify RED**

Run:
```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-web && bun test tests/interfaces/session-stream/session-shell.test.tsx
```

Expected:
- FAIL because `startReply` does not receive an execution-style field.

- [ ] **Step 5: Implement the minimal web threading change**

Update `kokoro-web/src/application/session-stream-preview.ts` so the input type and URL builder accept the selected execution style:

```ts
export type ConsumeLiveSessionInput = {
  input: string
  baseUrl?: string
  sessionId?: string
  conversationId?: string
  executionStyle: "fast" | "thinking"
  initialState?: SessionStreamState
  onState: (snapshot: SessionStreamSnapshot) => void
  onSettled?: () => void
  onError?: (event: Event) => void
}

function buildRunUrl(input: ConsumeLiveSessionInput, baseUrl: string) {
  const sessionId = input.sessionId ?? demoSessionId
  const conversationId = input.conversationId ?? demoConversationId
  const requestUrl = new URL(`/sessions/${sessionId}/runs`, baseUrl)
  requestUrl.searchParams.set("conversation_id", conversationId)
  requestUrl.searchParams.set("input", input.input)
  requestUrl.searchParams.set("execution_style", input.executionStyle)
  return { requestUrl, sessionId }
}
```

And thread the active mode from `kokoro-web/src/interfaces/session-stream/hooks/use-conversation.ts` into `startReply()`:

```ts
replyHandleRef.current = startReply({
  input: content,
  executionStyle: mode,
  initialState: seededThread,
  sessionId: storeAtStart.activeId,
  onState: (next: SessionStreamState) => {
    setLiveStore((prev) => withActiveThread(prev ?? storeAtStart, next, nowMs()))
  },
  onLive: () => {
    setLiveStore((prev) => (prev ? setActivePending(prev, content) : prev))
  },
  onSettled: (mode: ReplyMode) => {
    requestInFlightRef.current = false
    setIsStreaming(false)
    setTransportLabel(mode === "live" ? `实时 · ${resolveSessionBaseUrl()}` : "本地预览")
    setLiveStore((prev) => (prev ? setActivePending(prev, undefined) : prev))
    composerRef.current?.focus()
  },
})
```

- [ ] **Step 6: Re-run the focused web tests and verify GREEN**

Run:
```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-web && bun test tests/application/session-stream-preview.test.ts tests/interfaces/session-stream/session-shell.test.tsx
```

Expected:
- PASS

- [ ] **Step 7: Commit the web request-threading slice**

```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-web && git add src/application/session-stream-preview.ts src/interfaces/session-stream/hooks/use-conversation.ts tests/application/session-stream-preview.test.ts tests/interfaces/session-stream/session-shell.test.tsx && git commit -m "feat: wire execution style through web run requests"
```

---

### Task 2: Make session validate and relay only the allowed execution styles

**Files:**
- Modify: `kokoro-session/src/domain/agent-events.ts`
- Modify: `kokoro-session/tests/http.test.ts`
- Modify: `kokoro-session/tests/start-run.test.ts`
- Modify: `kokoro-session/tests/agent-events.test.ts`

- [ ] **Step 1: Write the failing session HTTP contract test**

```ts
test("POST /sessions/:id/runs relays execution_style=thinking into run.request", async () => {
  const published: unknown[] = []
  const server = buildServer({
    streamPort: {
      publish: async (_stream, event) => {
        published.push(event)
      },
      subscribe: async function* () {},
    },
    replayStore: fakeReplayStore(),
    normalizer: fakeNormalizer(),
  })

  const response = await fetch("http://127.0.0.1:3001/sessions/ses_01/runs?input=hello&execution_style=thinking", {
    method: "POST",
  })

  expect(response.status).toBe(200)
  expect(published[0]).toMatchObject({ execution_style: "thinking" })
})
```

- [ ] **Step 2: Write the failing invalid-style test**

```ts
test("POST /sessions/:id/runs rejects unknown execution_style", async () => {
  const response = await fetch("http://127.0.0.1:3001/sessions/ses_01/runs?input=hello&execution_style=default", {
    method: "POST",
  })

  expect(response.status).toBe(400)
})
```

- [ ] **Step 3: Run the focused session tests and verify RED**

Run:
```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-session && bun test tests/http.test.ts tests/start-run.test.ts tests/agent-events.test.ts
```

Expected:
- FAIL because the schema still accepts broad optional strings and the invalid-style path is not rejected.

- [ ] **Step 4: Implement the minimal session contract tightening**

In `kokoro-session/src/domain/agent-events.ts`, narrow the run-request schema field:

```ts
const executionStyle = z.enum(["fast", "thinking"])

export const runRequestSchema = z
  .object({
    kind: z.literal("run.request"),
    run_id: runId,
    session_id: sessionId,
    conversation_id: conversationId,
    input: nonEmptyText,
    execution_style: executionStyle.optional(),
  })
  .strict()
```

Keep `http.ts` and `start_run.ts` behavior simple: read the query value and rely on `runRequestSchema.parse()` to reject illegal inputs.

- [ ] **Step 5: Re-run the focused session tests and verify GREEN**

Run:
```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-session && bun test tests/http.test.ts tests/start-run.test.ts tests/agent-events.test.ts
```

Expected:
- PASS

- [ ] **Step 6: Commit the session contract slice**

```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-session && git add src/domain/agent-events.ts tests/http.test.ts tests/start-run.test.ts tests/agent-events.test.ts && git commit -m "feat: enforce execution style contract in session"
```

---

### Task 3: Rewrite agent runtime to resolve execution style per run

**Files:**
- Modify: `kokoro-agent/src/kokoro_agent/infrastructure/model.py`
- Modify: `kokoro-agent/src/kokoro_agent/worker.py`
- Modify: `kokoro-agent/src/kokoro_agent/run_agent.py`
- Modify: `kokoro-agent/tests/test_model.py`
- Modify: `kokoro-agent/tests/test_worker.py`
- Modify: `kokoro-agent/tests/test_run_agent.py` (if needed)

- [ ] **Step 1: Write the failing agent resolution test**

Add to `kokoro-agent/tests/test_model.py`:

```python
def test_resolve_execution_style_maps_fast_and_thinking_differently(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KOKORO_MODEL", "openai:glm-5")
    monkeypatch.setenv("KOKORO_DISABLE_STREAMING", "1")

    fast = resolve_execution_config("fast")
    thinking = resolve_execution_config("thinking")

    assert fast.style == "fast"
    assert thinking.style == "thinking"
    assert (fast.model_spec, fast.disable_streaming) != (thinking.model_spec, thinking.disable_streaming)
```

- [ ] **Step 2: Write the failing worker lifecycle test**

Add to `kokoro-agent/tests/test_worker.py`:

```python
async def test_run_once_resolves_model_per_request(monkeypatch: pytest.MonkeyPatch) -> None:
    resolved: list[str] = []

    def fake_make_chat_model(style: str):
        resolved.append(style)
        return make_local_fake_chat_model()

    monkeypatch.setattr("kokoro_agent.worker.make_chat_model_for_style", fake_make_chat_model)

    port = MemoryStreamPort()
    await port.publish(
        REQUESTS_STREAM,
        {
            "kind": "run.request",
            "run_id": "run_fast",
            "session_id": "ses_01",
            "conversation_id": "conv_01",
            "input": "hello",
            "execution_style": "fast",
        },
    )
    await port.publish(
        REQUESTS_STREAM,
        {
            "kind": "run.request",
            "run_id": "run_thinking",
            "session_id": "ses_01",
            "conversation_id": "conv_01",
            "input": "hello",
            "execution_style": "thinking",
        },
    )

    await run_once(port, set())

    assert resolved == ["fast", "thinking"]
```

- [ ] **Step 3: Run the focused agent tests and verify RED**

Run:
```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-agent && uv run pytest tests/test_model.py tests/test_worker.py -q
```

Expected:
- FAIL because there is no per-run execution-style resolver yet, and worker currently builds one model globally.

- [ ] **Step 4: Implement the minimal agent rewrite**

In `kokoro-agent/src/kokoro_agent/infrastructure/model.py`, extract a real execution-style resolver:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class ExecutionConfig:
    style: str
    model_spec: str
    disable_streaming: bool


def resolve_execution_config(style: str) -> ExecutionConfig:
    if style == "thinking":
        return ExecutionConfig(
            style="thinking",
            model_spec=os.environ.get("KOKORO_THINKING_MODEL", os.environ.get("KOKORO_MODEL", DEFAULT_MODEL)),
            disable_streaming=os.environ.get("KOKORO_DISABLE_STREAMING") == "1",
        )
    return ExecutionConfig(
        style="fast",
        model_spec=os.environ.get("KOKORO_FAST_MODEL", os.environ.get("KOKORO_MODEL", DEFAULT_MODEL)),
        disable_streaming=os.environ.get("KOKORO_DISABLE_STREAMING") == "1",
    )


def make_chat_model_for_style(style: str) -> BaseChatModel:
    if os.environ.get(LOCAL_FAKE_MODEL_FLAG) == "1":
        return make_local_fake_chat_model()
    config = resolve_execution_config(style)
    if config.disable_streaming:
        return init_chat_model(config.model_spec, disable_streaming=True)
    return init_chat_model(config.model_spec)
```

In `kokoro-agent/src/kokoro_agent/worker.py`, resolve the model inside request handling:

```python
async def _handle_request(
    port: StreamPort,
    raw: dict[str, object],
    processed: set[str],
) -> None:
    try:
        request = RunRequest.model_validate(raw)
    except ValidationError as error:
        LOGGER.warning("dropping malformed run.request: %s", error)
        return

    if request.run_id in processed:
        LOGGER.debug("skipping already-processed run_id=%s", request.run_id)
        return
    processed.add(request.run_id)

    model = make_chat_model_for_style(request.execution_style)
    stream = events_stream(request.run_id)
    async for event in run_agent(request, model):
        await port.publish(stream, event.model_dump())
```

Update `run_once()` / `_serve()` signatures accordingly so they no longer receive a single prebuilt model.

- [ ] **Step 5: Re-run the focused agent tests and verify GREEN**

Run:
```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-agent && uv run pytest tests/test_model.py tests/test_worker.py -q
```

Expected:
- PASS

- [ ] **Step 6: Commit the agent runtime rewrite**

```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-agent && git add src/kokoro_agent/infrastructure/model.py src/kokoro_agent/worker.py src/kokoro_agent/run_agent.py tests/test_model.py tests/test_worker.py tests/test_run_agent.py && git commit -m "refactor: resolve execution style per agent run"
```

---

### Task 4: Run full repo gates and prove Fast/Thinking are real

**Files:**
- Modify: `claude-progress.md`
- Modify: `tasks/todo.md`

- [ ] **Step 1: Run all web gates**

Run:
```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-web && bun run lint && bun run typecheck && bun test
```

Expected:
- All PASS

- [ ] **Step 2: Run all session gates**

Run:
```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-session && bun run lint && bun run typecheck && bun test
```

Expected:
- All PASS

- [ ] **Step 3: Run all agent gates**

Run:
```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-agent && uv run pytest && uv run ruff check && uv run pyright
```

Expected:
- All PASS

- [ ] **Step 4: Run one real live verification for each mode**

Run the worker and session with the configured `.env`, then verify that both modes can be triggered and distinguished. Minimum acceptable proof:

```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-agent && uv run python - <<'PY'
from dotenv import load_dotenv
load_dotenv('.env')
print('agent env ready for live verification')
PY
```

Then use the app / test harness to trigger one `fast` run and one `thinking` run, and capture evidence showing:
- request query differs;
- session relayed value differs;
- agent-side execution config differs.

Expected:
- Evidence answers: “用户点 Thinking 后，系统哪里变了？”

- [ ] **Step 5: Update handoff docs**

Record the completed contract in `claude-progress.md` and mark the accurate status in `tasks/todo.md`.

Suggested `tasks/todo.md` update:

```md
- [x] Wire the Fast/Thinking mode to the run's `execution_style` end-to-end. `kokoro-web` now sends the selected mode, `kokoro-session` validates `fast|thinking`, and `kokoro-agent` resolves execution config per run instead of using a worker-global model.
```

- [ ] **Step 6: Commit the root handoff updates**

```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro && git add claude-progress.md tasks/todo.md docs/superpowers/specs/2026-06-06-execution-style-contract-design.md docs/superpowers/plans/2026-06-06-execution-style-contract.md && git commit -m "docs: record execution style contract plan"
```

---

## Self-review

- The spec requirement “execution_style becomes a real per-run execution contract” maps to Tasks 1–4.
- No placeholder tasks remain: each step names exact files, commands, and expected outcomes.
- Types are consistent across the plan: the first pass uses `fast | thinking` throughout, with the agent responsible for mapping those stable business modes to actual runtime configuration.

Plan complete and saved to `docs/superpowers/plans/2026-06-06-execution-style-contract.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
