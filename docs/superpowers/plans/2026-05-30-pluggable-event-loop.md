# Pluggable Event Loop Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewire `kokoro-agent → kokoro-session → kokoro-web` so agent emits raw events through a pluggable `StreamPort` (memory|redis), session normalizes them into the AGUI envelope with replay, and web consumes live SSE in a real browser — agent brain stays deterministic.

**Architecture:** A `StreamPort` abstraction (publish / subscribe / readAll) is implemented in both Python (agent) and TS (session) with two adapters: `memory` (single-process, tests) and `redis` (cross-language end-to-end), selected by `KOKORO_STREAM_BACKEND`. Agent is a pure worker consuming run-requests and publishing raw `agent-events.md` kinds; session is the business layer that maps raw events → `session-stream.md` AGUI envelope, owns cursor/event_id/replay, and serves SSE; web is a pure renderer.

**Tech Stack:** Python 3.11 + uv + Pydantic(strict) + redis-py + pytest; TypeScript + Bun + Zod(strict) + ioredis + vitest; Next.js + EventSource.

**Contracts:** `docs/protocol/agent-events.md` (agent→session, v0.1.0), `docs/protocol/session-stream.md` (session→web, v1.0.0 locked). Spec: `docs/superpowers/specs/2026-05-30-pluggable-event-loop-design.md`.

**Conventions (CLAUDE.md):** strict schema validation at every boundary (Pydantic `strict=True` / Zod `.strict()`), no `any`, DDD layering, ports/adapters, surgical changes, TDD red→green, frequent commits. Each repo must end LSP+linter green (ruff/pyright, tsc/eslint) and tests 100% pass incl. schema-crash + idempotency boundaries.

---

## Chunk 1: kokoro-agent — StreamPort + raw events + worker

Working dir: `kokoro-agent/`. Run tests with `uv run pytest`.

### Task 1: Pydantic models for agent-events.md (strict)

**Files:**
- Create: `src/kokoro_agent/events.py` (replace AGUI-shaped helpers)
- Test: `tests/test_events.py`

- [ ] **Step 1: Write failing tests** — strict models reject missing/extra fields.

```python
import pytest
from pydantic import ValidationError
from kokoro_agent.events import RunRequest, AgentEvent

def test_run_request_strict_rejects_missing_input():
    with pytest.raises(ValidationError):
        RunRequest(kind="run.request", run_id="run_1", session_id="s", conversation_id="c")

def test_agent_event_requires_seq():
    with pytest.raises(ValidationError):
        AgentEvent(kind="text.delta", run_id="run_1", payload={"message_ref": "m", "text": "hi"})

def test_text_delta_roundtrip():
    e = AgentEvent(kind="text.delta", run_id="run_1", seq=2, payload={"message_ref": "m", "text": "hi"})
    assert e.kind == "text.delta" and e.seq == 2
```

- [ ] **Step 2: Run, verify RED** — `uv run pytest tests/test_events.py -q` → fails (no models).

- [ ] **Step 3: Implement strict models.**

```python
from __future__ import annotations
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict

AgentKind = Literal[
    "run.started", "text.delta", "text.completed",
    "tool.invoked", "tool.returned", "run.completed", "run.failed",
]

class RunRequest(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    kind: Literal["run.request"]
    run_id: str
    session_id: str
    conversation_id: str
    input: str
    execution_style: str = "fast"

class AgentEvent(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    kind: AgentKind
    run_id: str
    seq: int
    payload: dict[str, Any] = {}
```

- [ ] **Step 4: Run, verify GREEN.**
- [ ] **Step 5: Commit** — `git add -A && git commit -m "feat(agent): strict pydantic models for agent-events contract"`

### Task 2: StreamPort protocol + MemoryStreamPort

**Files:**
- Create: `src/kokoro_agent/infrastructure/stream_port.py`
- Test: `tests/test_stream_port_memory.py`

- [ ] **Step 1: Write failing tests.**

```python
import pytest
from kokoro_agent.infrastructure.stream_port import MemoryStreamPort

@pytest.mark.asyncio
async def test_publish_then_readall_preserves_order():
    port = MemoryStreamPort()
    await port.publish("s", {"a": 1}); await port.publish("s", {"a": 2})
    items = await port.readAll("s")
    assert [i.event["a"] for i in items] == [1, 2]
    assert items[0].cursor != items[1].cursor

@pytest.mark.asyncio
async def test_subscribe_from_cursor_skips_prior():
    port = MemoryStreamPort()
    await port.publish("s", {"a": 1})
    c = (await port.readAll("s"))[0].cursor
    await port.publish("s", {"a": 2})
    seen = []
    async for item in port.subscribe("s", from_cursor=c):
        seen.append(item.event["a"])
        if len(seen) == 1: break
    assert seen == [2]
```

- [ ] **Step 2: Run, verify RED.**
- [ ] **Step 3: Implement** the `StreamItem` dataclass, `StreamPort` Protocol (`publish`, `subscribe`, `readAll`), and `MemoryStreamPort` (append-only list keyed by stream, monotonic int cursor as zero-padded string, `subscribe` polls with `asyncio.sleep(0)` + an `asyncio.Event` per stream). Wrap any awaits that could hang with `asyncio.timeout`.
- [ ] **Step 4: Run, verify GREEN.**
- [ ] **Step 5: Commit** — `feat(agent): StreamPort protocol + in-memory adapter`

### Task 3: RedisStreamPort

**Files:**
- Modify: `pyproject.toml` (add `redis>=5`, `pytest-asyncio`)
- Modify: `src/kokoro_agent/infrastructure/stream_port.py`
- Test: `tests/test_stream_port_redis.py` (mark `@pytest.mark.redis`; skip if `KOKORO_STREAM_BACKEND!=redis` or no server)

- [ ] **Step 1: Write failing test** — same contract as memory, against `redis.asyncio` using `XADD`/`XRANGE`/`XREAD`; entry id is the cursor. Guard with `pytest.importorskip` + connection probe → skip cleanly when no Redis.
- [ ] **Step 2: Run, verify RED/SKIP.**
- [ ] **Step 3: Implement `RedisStreamPort`** (`XADD stream * data=<json>`, `readAll`=`XRANGE - +`, `subscribe`=`XREAD BLOCK` loop from cursor). Add `make_stream_port()` factory reading `KOKORO_STREAM_BACKEND`.
- [ ] **Step 4: Run with local redis** — `KOKORO_STREAM_BACKEND=redis uv run pytest tests/test_stream_port_redis.py -q` → PASS.
- [ ] **Step 5: Commit** — `feat(agent): redis StreamPort adapter + factory`

### Task 4: Deterministic worker (run_agent + consumer loop)

**Files:**
- Modify: `src/kokoro_agent/run_agent.py` (raw kinds only; drop AGUI/owner_id)
- Create: `src/kokoro_agent/worker.py` (+ console-script in pyproject `[project.scripts] kokoro-agent-worker = "kokoro_agent.worker:main"`)
- Test: `tests/test_worker.py`

- [ ] **Step 1: Write failing test** — given a `MemoryStreamPort` seeded with one `run.request`, running one worker iteration publishes the full sequence to `kokoro:run:{run_id}:events` and is idempotent on duplicate request (same run_id → no duplicate events, dedup by run_id).

```python
@pytest.mark.asyncio
async def test_worker_emits_sequence_and_is_idempotent():
    port = MemoryStreamPort()
    req = {"kind":"run.request","run_id":"run_1","session_id":"s","conversation_id":"c","input":"hi","execution_style":"fast"}
    await port.publish("kokoro:runs:requests", req)
    await run_once(port)              # consume + produce
    await port.publish("kokoro:runs:requests", req)  # duplicate
    await run_once(port)
    kinds = [i.event["kind"] for i in await port.readAll("kokoro:run:run_1:events")]
    assert kinds == ["run.started","text.delta","text.completed","run.completed"]
```

- [ ] **Step 2: Run, verify RED.**
- [ ] **Step 3: Implement** `run_agent(req) -> Iterator[AgentEvent]` (deterministic: echo `Kokoro received: {input}`, seq 1..4, raw kinds), and `worker.run_once(port)` / `main()` consuming requests with an in-process processed-run set for idempotency.
- [ ] **Step 4: Run, verify GREEN.**
- [ ] **Step 5: Commit** — `feat(agent): deterministic worker over StreamPort (raw agent events)`

### Task 5: Green gate (agent)
- [ ] Run `uv run ruff check . && uv run pyright && uv run pytest -q` → all green. Fix anything. Commit `chore(agent): lint/type/test green`.

---

## Chunk 2: kokoro-session — StreamPort + normalize + SSE server

Working dir: `kokoro-session/`. Run tests with `bun test`.

### Task 6: Zod schemas for both contracts (strict)

**Files:**
- Modify: `src/domain/events.ts` (AGUI envelope — keep) ; Create: `src/domain/agent-events.ts` (raw inbound)
- Test: `tests/agent-events.test.ts`

- [ ] **Step 1: Write failing tests** — `agentEventSchema.strict()` rejects missing `seq`/extra keys; `runRequestSchema` requires `input`.
- [ ] **Step 2: RED.**
- [ ] **Step 3: Implement** Zod `runRequestSchema`, `agentEventSchema` (`.strict()`), `export type AgentEvent = z.infer<...>`. No `any`.
- [ ] **Step 4: GREEN.**
- [ ] **Step 5: Commit** — `feat(session): strict zod schemas for agent-events contract`

### Task 7: StreamPort (TS) + memory + redis

**Files:**
- Create: `src/infrastructure/stream-port.ts` (replace `redis_stream.ts` stub)
- Modify: `package.json` (add `ioredis`, dev `@types/...` as needed)
- Test: `tests/stream-port.memory.test.ts`, `tests/stream-port.redis.test.ts` (redis test skips without server)

- [ ] **Step 1: Write failing memory tests** — publish→readAll order + distinct cursors; subscribe(from_cursor) skips prior. Mirror the Python contract.
- [ ] **Step 2: RED.**
- [ ] **Step 3: Implement** `StreamPort` interface (`publish`, `subscribe` async iterable, `readAll`), `MemoryStreamPort`, `RedisStreamPort` (ioredis `xadd`/`xrange`/`xread BLOCK`), and `makeStreamPort()` reading `KOKORO_STREAM_BACKEND`.
- [ ] **Step 4: GREEN** (memory). With local redis: `KOKORO_STREAM_BACKEND=redis bun test tests/stream-port.redis.test.ts`.
- [ ] **Step 5: Commit** — `feat(session): StreamPort interface + memory/redis adapters`

### Task 8: Normalizer (raw agent events → AGUI envelope)

**Files:**
- Create: `src/application/normalize.ts`
- Test: `tests/normalize.test.ts`

- [ ] **Step 1: Write failing tests** — a `Normalizer` bound to `(session_id, conversation_id, run_id)`:
  - `run.started` → emits `session.created` (first time) + `run.created`, cursor `run_1:0001`, `0002`…
  - `text.delta{message_ref,text}` → `message.delta{message_id, delta, role:"assistant"}` (stable message_id per message_ref).
  - `text.completed` → `message.completed{content}`.
  - `run.completed` → `run.completed`.
  - Each emitted envelope has unique `event_id`, monotonic `cursor`, ISO `timestamp`, all `session-stream.md` required fields.
  - Idempotency: feeding the same `(run_id, seq)` twice yields the mapped events only once.

- [ ] **Step 2: RED.**
- [ ] **Step 3: Implement** `Normalizer` (inject id/clock factories so tests are deterministic; dedup set on `(run_id, seq)`; message_ref→message_id map). Validate inbound with `agentEventSchema`, output with AGUI `eventSchema`.
- [ ] **Step 4: GREEN.**
- [ ] **Step 5: Commit** — `feat(session): normalize raw agent events into AGUI envelope`

### Task 9: start_run + replay over StreamPort, wired to normalizer

**Files:**
- Modify: `src/application/start_run.ts` (publish run.request; no HTTP to agent)
- Modify: `src/infrastructure/replay_store.ts` (back with StreamPort)
- Test: `tests/start-run.test.ts` (update)

- [ ] **Step 1: Update failing test** — `startRun({sessionId,input,...})` with an injected `MemoryStreamPort`: returns `{runId}`, publishes a valid `run.request` to `kokoro:runs:requests`. A separate consumer test: feeding agent events through the normalizer appends AGUI events to replay, readable by `readEvents(sessionId)`.
- [ ] **Step 2: RED.**
- [ ] **Step 3: Implement** — `startRun` generates `run_id`, publishes request; a `relay(streamPort, normalizer, replayStore)` consumes `kokoro:run:{run_id}:events`, normalizes, appends to replay. Wire deps via the existing ports pattern.
- [ ] **Step 4: GREEN.**
- [ ] **Step 5: Commit** — `feat(session): publish run requests + relay/normalize into replay`

### Task 10: HTTP/SSE server + boot entry

**Files:**
- Modify: `src/interfaces/http.ts` (GET /stream = replay + live subscribe)
- Create: `src/main.ts` ; Modify: `package.json` scripts `"start": "bun run src/main.ts"`, `"dev": "bun --watch src/main.ts"`
- Test: `tests/http.test.ts`

- [ ] **Step 1: Write failing test** — `buildServer({...injected})`: POST `/sessions/ses_x/runs?input=hi` → 200 `{runId}`; after relay drains, GET `/sessions/ses_x/stream` → SSE chunks containing `session.created`…`run.completed` with `id:`/`event:`/`data:` lines.
- [ ] **Step 2: RED.**
- [ ] **Step 3: Implement** SSE handler: replay `readAll` then continue `subscribe` from last cursor; `main.ts` builds `makeStreamPort()` + server `.listen(3001)`.
- [ ] **Step 4: GREEN.**
- [ ] **Step 5: Commit** — `feat(session): SSE stream endpoint + server boot entry`

### Task 11: Green gate (session)
- [ ] `bunx tsc --noEmit && bunx eslint . && bun test` → green. Commit `chore(session): lint/type/test green`.

---

## Chunk 3: kokoro-web — live SSE consumption + browser verify

Working dir: `kokoro-web/`. Run tests with `bun run test`.

### Task 12: Real SSE client wired into reducer

**Files:**
- Modify: `src/application/session-stream-preview.ts` (real fetch POST + EventSource → reducer)
- Test: `tests/interfaces/session-stream/session-shell.test.tsx` (update), `tests/application/session-stream-preview.test.ts`

- [ ] **Step 1: Write failing test** — given a mocked `EventSource` emitting the AGUI sequence, the preview folds events into reducer state producing a thread with the assistant message text and a completed run. Strict-parse each event with the existing protocol parser (reject malformed).
- [ ] **Step 2: RED.**
- [ ] **Step 3: Implement** — POST to `${base}/sessions/{id}/runs?input=...`, open `EventSource(${base}/sessions/{id}/stream)`, parse via existing session-event schema, dispatch into reducer; close on `run.completed`/`run.failed`.
- [ ] **Step 4: GREEN** — `bun run test`.
- [ ] **Step 5: Commit** — `feat(web): consume live session SSE into chat reducer`

### Task 13: Browser end-to-end verification (redis backend)

**Files:** none (verification + screenshot)

- [ ] **Step 1:** Start local Redis (`docker run -p 6379:6379 redis` or `brew services start redis`).
- [ ] **Step 2:** `KOKORO_STREAM_BACKEND=redis` start agent worker (`uv run kokoro-agent-worker`), session (`bun run start`), web (`bun run dev`).
- [ ] **Step 3:** Drive the chat main path with Playwright MCP: navigate to web, submit "hello kokoro", wait for the assistant message + completed run, capture a screenshot.
- [ ] **Step 4:** Boundary checks — kill Redis mid-run: web shows a recoverable state, no crash; restart + replay restores the thread via `GET /stream`.
- [ ] **Step 5: Commit (parent repo docs)** — update `claude-progress.md` + `tasks/todo.md`; do NOT commit child repos here.

### Task 14: Green gate (web)
- [ ] `bunx tsc --noEmit && bun run lint && bun run test && bun run build` → green. Commit `chore(web): lint/type/test/build green`.

---

## Done criteria (whole slice)
- Three repos: ruff/pyright + tsc/eslint green; pytest/vitest 100% pass incl. schema-crash + idempotency + disconnect boundaries.
- `KOKORO_STREAM_BACKEND=memory` runs all unit/integration tests with zero infra.
- `KOKORO_STREAM_BACKEND=redis` runs the real 3-process browser demo; screenshot captured.
- agent emits only raw `agent-events.md` kinds; web consumes only AGUI `session-stream.md`; session owns normalization+replay. No cross-repo source imports.
