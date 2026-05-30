# Agent Real-LLM Brain Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace `kokoro-agent`'s deterministic echo brain with a real streaming LLM brain that emits `text.delta`/`text.completed`/`run.failed` raw agent events, with a pluggable provider (`KOKORO_MODEL`), verified entirely offline with a fake chat model.

**Architecture:** A new `make_chat_model()` reads `KOKORO_MODEL` (default `anthropic:claude-sonnet-4-6`) via LangChain `init_chat_model`. `run_agent` becomes an async generator that streams `model.astream_events(...)`, mapping `on_chat_model_stream` text chunks to `text.delta` events (running seq), finishing with `text.completed` + `run.completed`, and catching any error into `run.failed`. The worker injects the model and awaits the async generator. `kokoro-session` / `kokoro-web` / `StreamPort` are untouched.

**Tech Stack:** Python 3.11+, uv, LangChain (`init_chat_model`, `astream_events`), `langchain-anthropic`, Pydantic v2 (strict), pytest + pytest-asyncio. Tests use `langchain_core.language_models.fake_chat_models.GenericFakeChatModel` — no real LLM, no API key, no network.

**Contract:** `Kokoro/docs/protocol/agent-events.md` v0.1.0 (unchanged this round). Spec: `Kokoro/docs/superpowers/specs/2026-05-30-agent-real-llm-brain-design.md`.

**Conventions (CLAUDE.md):** strict Pydantic, no bare `print` (use `logging`), `asyncio.timeout` to bound hangs, no swallowed `except`, surgical changes, TDD red→green, frequent commits. End ruff/pyright(strict)/pytest green.

**Working dir:** `kokoro-agent/`. Run tests with `uv run pytest`. Branch: continue on `feat/pluggable-event-loop` (or a new `feat/real-llm-brain` if the prior is merged — controller decides).

---

## Chunk 1: Real streaming LLM brain

### Task 1: `make_chat_model()` provider factory

**Files:**
- Create: `src/kokoro_agent/infrastructure/model.py`
- Modify: `pyproject.toml` (declare `langchain-anthropic`)
- Test: `tests/test_model.py`

- [ ] **Step 1: Write the failing test**

```python
import pytest
from kokoro_agent.infrastructure.model import make_chat_model

def test_make_chat_model_reads_env(monkeypatch):
    # default model id when KOKORO_MODEL unset -> still returns a model object
    monkeypatch.delenv("KOKORO_MODEL", raising=False)
    # We do not call the network; init_chat_model builds a client lazily.
    model = make_chat_model()
    assert model is not None

def test_make_chat_model_invalid_spec_fails_loud(monkeypatch):
    monkeypatch.setenv("KOKORO_MODEL", "not-a-valid-provider-spec-xyz")
    with pytest.raises(Exception):
        make_chat_model()
```

- [ ] **Step 2: Run, verify RED** — `uv run pytest tests/test_model.py -q` → fails (module missing).
- [ ] **Step 3: Implement** `make_chat_model()`:

```python
from __future__ import annotations
import os
from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel

DEFAULT_MODEL = "anthropic:claude-sonnet-4-6"

def make_chat_model() -> BaseChatModel:
    spec = os.environ.get("KOKORO_MODEL", DEFAULT_MODEL)
    # fail loud on invalid spec / missing provider package
    return init_chat_model(spec)
```

(If `init_chat_model` import path differs in the installed version, use the import that the installed `langchain` exposes — verify with `uv run python -c "from langchain.chat_models import init_chat_model"`.)

- [ ] **Step 4: Run, verify GREEN.** If `test_make_chat_model_reads_env` requires provider creds even to construct, adjust the test to assert construction is lazy OR `monkeypatch.setenv` a dummy `ANTHROPIC_API_KEY` (construction must not perform network I/O — only object build). Document the chosen behavior in a comment.
- [ ] **Step 5: Add `langchain-anthropic` to `pyproject.toml` deps; `uv sync`.**
- [ ] **Step 6: Commit** — `feat(agent): pluggable chat-model factory (KOKORO_MODEL)`

### Task 2: `run_agent` async streaming — happy path

**Files:**
- Modify: `src/kokoro_agent/run_agent.py`
- Test: `tests/test_run_agent.py` (new; the old one was removed last round)

- [ ] **Step 1: Write the failing test** (fake model streams tokens):

```python
import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage
from kokoro_agent.events import RunRequest
from kokoro_agent.run_agent import run_agent

def _req(text="hi"):
    return RunRequest(kind="run.request", run_id="run_1", session_id="s",
                      conversation_id="c", input=text, execution_style="fast")

@pytest.mark.asyncio
async def test_run_agent_streams_text_then_completes():
    model = GenericFakeChatModel(messages=iter([AIMessage(content="Hello world")]))
    events = [e async for e in run_agent(_req(), model)]
    kinds = [e.kind for e in events]
    assert kinds[0] == "run.started"
    assert "text.delta" in kinds
    assert kinds[-2] == "text.completed"
    assert kinds[-1] == "run.completed"
    # seq strictly increasing from 1
    seqs = [e.seq for e in events]
    assert seqs == sorted(seqs) and seqs[0] == 1 and len(set(seqs)) == len(seqs)
    # completed text == concatenation of deltas
    deltas = "".join(e.payload["text"] for e in events if e.kind == "text.delta")
    completed = next(e for e in events if e.kind == "text.completed")
    assert completed.payload["text"] == deltas == "Hello world"
```

(Note: confirm how `GenericFakeChatModel` chunks `astream_events` — it streams the message token-by-token by whitespace/char per its implementation; the test asserts on the *concatenation*, not delta count, to stay robust.)

- [ ] **Step 2: Run, verify RED.**
- [ ] **Step 3: Implement** the async generator:

```python
from __future__ import annotations
import asyncio
from collections.abc import AsyncIterator
from langchain_core.language_models import BaseChatModel
from kokoro_agent.events import AgentEvent, RunRequest

ASTREAM_TIMEOUT_S = 120

def _text_of(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return "".join(parts)
    return ""

async def run_agent(req: RunRequest, model: BaseChatModel) -> AsyncIterator[AgentEvent]:
    seq = 1
    message_ref = "m1"
    full = ""
    yield AgentEvent(kind="run.started", run_id=req.run_id, seq=seq, payload={})
    try:
        async with asyncio.timeout(ASTREAM_TIMEOUT_S):
            async for ev in model.astream_events([("user", req.input)]):
                if ev.get("event") != "on_chat_model_stream":
                    continue
                chunk = ev.get("data", {}).get("chunk")
                text = _text_of(getattr(chunk, "content", ""))
                if not text:
                    continue
                seq += 1
                full += text
                yield AgentEvent(kind="text.delta", run_id=req.run_id, seq=seq,
                                 payload={"message_ref": message_ref, "text": text})
        seq += 1
        yield AgentEvent(kind="text.completed", run_id=req.run_id, seq=seq,
                         payload={"message_ref": message_ref, "text": full})
        seq += 1
        yield AgentEvent(kind="run.completed", run_id=req.run_id, seq=seq,
                         payload={"status": "completed"})
    except Exception as error:  # noqa: BLE001 — boundary: any brain failure -> run.failed
        seq += 1
        yield AgentEvent(kind="run.failed", run_id=req.run_id, seq=seq,
                         payload={"error_kind": type(error).__name__, "message": str(error)})
```

- [ ] **Step 4: Run, verify GREEN.**
- [ ] **Step 5: Commit** — `feat(agent): stream real LLM tokens into text.delta events`

### Task 3: `run_agent` edge cases — list content, empty stream, error

**Files:**
- Modify: `tests/test_run_agent.py`

- [ ] **Step 1: Write failing tests:**

```python
@pytest.mark.asyncio
async def test_list_content_extracts_only_text_blocks():
    msg = AIMessage(content=[{"type": "text", "text": "Hi"},
                             {"type": "thinking", "thinking": "secret"}])
    model = GenericFakeChatModel(messages=iter([msg]))
    events = [e async for e in run_agent(_req(), model)]
    full = "".join(e.payload["text"] for e in events if e.kind == "text.delta")
    assert "secret" not in full and "Hi" in full

@pytest.mark.asyncio
async def test_empty_stream_still_completes():
    model = GenericFakeChatModel(messages=iter([AIMessage(content="")]))
    events = [e async for e in run_agent(_req(""), model)]
    kinds = [e.kind for e in events]
    assert kinds[0] == "run.started" and kinds[-1] == "run.completed"
    completed = next(e for e in events if e.kind == "text.completed")
    assert completed.payload["text"] == ""

@pytest.mark.asyncio
async def test_brain_error_yields_run_failed():
    class Boom(GenericFakeChatModel):
        async def astream_events(self, *a, **k):
            raise RuntimeError("model down")
            yield  # pragma: no cover
    events = [e async for e in run_agent(_req(), Boom(messages=iter([])))]
    assert events[0].kind == "run.started"
    assert events[-1].kind == "run.failed"
    assert events[-1].payload["error_kind"] == "RuntimeError"
    assert "model down" in events[-1].payload["message"]
```

(Verify `GenericFakeChatModel`'s list-content streaming behavior empirically first; if it serializes list content differently, adjust the assertion to match how `on_chat_model_stream` surfaces `chunk.content`. Keep the intent: non-text blocks never leak into `text.delta`.)

- [ ] **Step 2: Run, verify RED** (for any not already covered).
- [ ] **Step 3: Adjust `_text_of` / implementation** only as needed to pass; do not change behavior beyond the spec.
- [ ] **Step 4: Run, verify GREEN.**
- [ ] **Step 5: Commit** — `test(agent): list-content/empty/error edge cases for streaming brain`

### Task 4: Worker awaits the async brain with injected model

**Files:**
- Modify: `src/kokoro_agent/worker.py`
- Test: `tests/test_worker.py` (update)

- [ ] **Step 1: Update the failing test** — inject a fake model + MemoryStreamPort; assert the events stream contains the full streamed sequence and is idempotent on duplicate run_id:

```python
@pytest.mark.asyncio
async def test_worker_streams_with_injected_model():
    from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
    from langchain_core.messages import AIMessage
    from kokoro_agent.infrastructure.stream_port import MemoryStreamPort
    port = MemoryStreamPort()
    model = GenericFakeChatModel(messages=iter([AIMessage(content="Hello world"),
                                                AIMessage(content="Hello world")]))
    req = {"kind":"run.request","run_id":"run_1","session_id":"s",
           "conversation_id":"c","input":"hi","execution_style":"fast"}
    await port.publish("kokoro:runs:requests", req)
    processed = set()
    await run_once(port, processed, model)          # consume + produce
    await port.publish("kokoro:runs:requests", req)  # duplicate
    await run_once(port, processed, model)
    kinds = [i.event["kind"] for i in await port.read_all("kokoro:run:run_1:events")]
    assert kinds[0] == "run.started" and kinds[-1] == "run.completed"
    assert kinds.count("run.started") == 1  # idempotent
```

- [ ] **Step 2: Run, verify RED.**
- [ ] **Step 3: Implement** — thread `model` through `run_once(port, processed, model)` and `_handle_request(port, raw, processed, model)`; change `for event in run_agent(req)` → `async for event in run_agent(req, model)`. In `_serve`, build `model = make_chat_model()` once and pass it down. Keep `make_chat_model` import lazy-friendly (only constructed in `_serve`/`main`, never at import time, so tests don't need creds).
- [ ] **Step 4: Run, verify GREEN.**
- [ ] **Step 5: Commit** — `feat(agent): worker awaits streaming brain with injected model`

### Task 5: Green gate

- [ ] Run `uv run ruff check . && uv run pyright && uv run pytest -q` → all green (no real-LLM tests; redis tests still skip without server).
- [ ] Confirm `git diff --stat` touches only `kokoro-agent/` brain/worker/model/tests/pyproject.
- [ ] Commit `chore(agent): real-llm brain lint/type/test green`.

---

## Done criteria
- `run_agent` is an async streaming generator; real provider selectable via `KOKORO_MODEL` (default `anthropic:claude-sonnet-4-6`).
- `text.delta` (streamed) + `text.completed` + `run.failed` emitted per `agent-events.md`; seq monotonic; raw kinds only (no AGUI/owner fields).
- All tests pass offline with `GenericFakeChatModel` — no API key, no network, no real LLM call.
- ruff + pyright(strict) + pytest green. `kokoro-session` / `kokoro-web` / `StreamPort` unchanged.
- Tools / thinking / DeepAgents explicitly deferred; `astream_events` interface leaves their hooks (`on_tool_start/end`, thinking blocks) ready.
