# Three-Repo Demo Slice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first end-to-end Kokoro demo across `kokoro-web`, `kokoro-session`, and `kokoro-agent`, centered on a prototype-aligned chat shell, a thin SSE bridge, and a DeepAgents-backed event producer.

**Architecture:** `kokoro-web` consumes a browser-safe SSE stream and replays recent events into a simple chat layout. `kokoro-session` owns run lifecycle, SSE serialization, and a small in-memory replay buffer. `kokoro-agent` uses Python + DeepAgents + LangChain to emit the minimal normalized event set for the first demo.

**Tech Stack:** Bun, Next.js App Router, Tailwind CSS, shadcn-style components, TypeScript, Python, DeepAgents, LangChain, SSE, Vitest, pytest

---

### Task 1: Initialize and push the two new runtime repositories

**Files:**
- Create: `../kokoro-session/.gitignore`
- Create: `../kokoro-session/README.md`
- Create: `../kokoro-session/package.json`
- Create: `../kokoro-agent/.gitignore`
- Create: `../kokoro-agent/README.md`
- Create: `../kokoro-agent/pyproject.toml`

- [ ] **Step 1: Create the repository directories**

```bash
mkdir -p /Users/yuri/WebstormProjects/kokoro-session
mkdir -p /Users/yuri/WebstormProjects/kokoro-agent
```

- [ ] **Step 2: Add the minimal `.gitignore` for `kokoro-session`**

```gitignore
node_modules/
dist/
.env*
.DS_Store
.vscode/
.idea/
coverage/
```

- [ ] **Step 3: Add the minimal `.gitignore` for `kokoro-agent`**

```gitignore
__pycache__/
.pytest_cache/
.venv/
.env*
.DS_Store
.vscode/
.idea/
coverage/
```

- [ ] **Step 4: Initialize each repository and attach the prepared GitHub origin**

```bash
cd /Users/yuri/WebstormProjects/kokoro-session && git init && git remote add origin https://github.com/LordFoxFairy/kokoro-session.git
cd /Users/yuri/WebstormProjects/kokoro-agent && git init && git remote add origin https://github.com/LordFoxFairy/kokoro-agent.git
```

- [ ] **Step 5: Verify both repos have the correct remotes**

Run:
```bash
cd /Users/yuri/WebstormProjects/kokoro-session && git remote -v
cd /Users/yuri/WebstormProjects/kokoro-agent && git remote -v
```
Expected: each repository prints its GitHub `origin` URL.

### Task 2: Bootstrap `kokoro-agent` as a minimal DeepAgents event producer

**Files:**
- Create: `/Users/yuri/WebstormProjects/kokoro-agent/pyproject.toml`
- Create: `/Users/yuri/WebstormProjects/kokoro-agent/src/kokoro_agent/domain/events.py`
- Create: `/Users/yuri/WebstormProjects/kokoro-agent/src/kokoro_agent/application/run_agent.py`
- Create: `/Users/yuri/WebstormProjects/kokoro-agent/src/kokoro_agent/infrastructure/runner.py`
- Test: `/Users/yuri/WebstormProjects/kokoro-agent/tests/test_run_agent.py`

- [ ] **Step 1: Write the failing pytest first**

```python
from kokoro_agent.application.run_agent import run_agent


def test_run_agent_emits_message_and_completion_events() -> None:
    events = list(run_agent("hello kokoro"))

    assert events[0]["event"] == "run.created"
    assert any(event["event"] == "message.delta" for event in events)
    assert any(event["event"] == "message.completed" for event in events)
    assert events[-1]["event"] == "run.completed"
```

- [ ] **Step 2: Run the test and verify RED**

Run:
```bash
cd /Users/yuri/WebstormProjects/kokoro-agent && pytest tests/test_run_agent.py -q
```
Expected: FAIL because `kokoro_agent.application.run_agent` does not exist yet.

- [ ] **Step 3: Write the minimal domain event helpers**

```python
from __future__ import annotations

from typing import Any


def run_created(run_id: str) -> dict[str, Any]:
    return {"event": "run.created", "run_id": run_id}


def message_delta(run_id: str, delta: str) -> dict[str, Any]:
    return {"event": "message.delta", "run_id": run_id, "delta": delta}


def message_completed(run_id: str, content: str) -> dict[str, Any]:
    return {"event": "message.completed", "run_id": run_id, "content": content}


def run_completed(run_id: str) -> dict[str, Any]:
    return {"event": "run.completed", "run_id": run_id}
```

- [ ] **Step 4: Write the minimal runner and `run_agent` use case**

```python
from __future__ import annotations

from collections.abc import Iterator
from uuid import uuid4

from kokoro_agent.domain import events


def run_agent(user_input: str) -> Iterator[dict[str, object]]:
    run_id = f"run_{uuid4().hex[:8]}"

    yield events.run_created(run_id)
    yield events.message_delta(run_id, f"Kokoro received: {user_input}")
    yield events.message_completed(run_id, f"Kokoro received: {user_input}")
    yield events.run_completed(run_id)
```

- [ ] **Step 5: Re-run the test and verify GREEN**

Run:
```bash
cd /Users/yuri/WebstormProjects/kokoro-agent && pytest tests/test_run_agent.py -q
```
Expected: PASS.

- [ ] **Step 6: Commit and push the first `kokoro-agent` checkpoint**

```bash
cd /Users/yuri/WebstormProjects/kokoro-agent
git add .
git commit -m "feat: bootstrap kokoro-agent"
git push -u origin main
```

### Task 3: Bootstrap `kokoro-session` as the minimal HTTP + SSE bridge

**Files:**
- Create: `/Users/yuri/WebstormProjects/kokoro-session/package.json`
- Create: `/Users/yuri/WebstormProjects/kokoro-session/src/domain/events.ts`
- Create: `/Users/yuri/WebstormProjects/kokoro-session/src/application/start_run.ts`
- Create: `/Users/yuri/WebstormProjects/kokoro-session/src/infrastructure/memory_store.ts`
- Create: `/Users/yuri/WebstormProjects/kokoro-session/src/infrastructure/agent_client.ts`
- Create: `/Users/yuri/WebstormProjects/kokoro-session/src/infrastructure/sse.ts`
- Create: `/Users/yuri/WebstormProjects/kokoro-session/src/interfaces/http.ts`
- Test: `/Users/yuri/WebstormProjects/kokoro-session/tests/start-run.test.ts`

- [ ] **Step 1: Write the failing session test first**

```ts
import { describe, expect, it } from "vitest"

import { startRun } from "../src/application/start_run"

describe("startRun", () => {
  it("creates a run and stores replayable events", async () => {
    const result = await startRun({
      sessionId: "ses_01",
      input: "hello kokoro",
      executionStyle: "default",
    })

    expect(result.runId).toMatch(/^run_/)
    expect(result.events.at(0)?.event).toBe("run.created")
    expect(result.events.at(-1)?.event).toBe("run.completed")
  })
})
```

- [ ] **Step 2: Run the test and verify RED**

Run:
```bash
cd /Users/yuri/WebstormProjects/kokoro-session && bun vitest run tests/start-run.test.ts
```
Expected: FAIL because `start_run` is missing.

- [ ] **Step 3: Write the minimal in-memory store and start-run flow**

```ts
export type SessionEvent = {
  event: string
  runId: string
  [key: string]: unknown
}

const replayStore = new Map<string, SessionEvent[]>()

export function appendEvents(sessionId: string, events: SessionEvent[]) {
  const previous = replayStore.get(sessionId) ?? []
  replayStore.set(sessionId, [...previous, ...events])
}

export function readEvents(sessionId: string) {
  return replayStore.get(sessionId) ?? []
}
```

```ts
import { randomUUID } from "node:crypto"

import { appendEvents, type SessionEvent } from "../infrastructure/memory_store"

export async function startRun(input: {
  sessionId: string
  input: string
  executionStyle: string
}) {
  const runId = `run_${randomUUID().slice(0, 8)}`
  const events: SessionEvent[] = [
    { event: "run.created", runId },
    { event: "message.delta", runId, delta: `Kokoro received: ${input.input}` },
    { event: "message.completed", runId, content: `Kokoro received: ${input.input}` },
    { event: "run.completed", runId },
  ]

  appendEvents(input.sessionId, events)

  return { runId, events }
}
```

- [ ] **Step 4: Re-run the test and verify GREEN**

Run:
```bash
cd /Users/yuri/WebstormProjects/kokoro-session && bun vitest run tests/start-run.test.ts
```
Expected: PASS.

- [ ] **Step 5: Add the minimal HTTP/SSE surface**

```ts
import { createServer } from "node:http"
import { readEvents } from "../infrastructure/memory_store"
import { startRun } from "../application/start_run"

export function buildServer() {
  return createServer(async (req, res) => {
    if (req.method === "POST" && req.url === "/sessions/ses_01/runs") {
      const result = await startRun({
        sessionId: "ses_01",
        input: "hello kokoro",
        executionStyle: "default",
      })
      res.setHeader("content-type", "application/json")
      res.end(JSON.stringify(result))
      return
    }

    if (req.method === "GET" && req.url === "/sessions/ses_01/stream") {
      res.writeHead(200, {
        "content-type": "text/event-stream",
        "cache-control": "no-cache",
        connection: "keep-alive",
      })

      for (const event of readEvents("ses_01")) {
        res.write(`data: ${JSON.stringify(event)}\n\n`)
      }
      res.end()
      return
    }

    res.statusCode = 404
    res.end("not found")
  })
}
```

- [ ] **Step 6: Commit and push the first `kokoro-session` checkpoint**

```bash
cd /Users/yuri/WebstormProjects/kokoro-session
git add .
git commit -m "feat: bootstrap kokoro-session"
git push -u origin main
```

### Task 4: Refocus `kokoro-web` on the real chat demo path

**Files:**
- Modify: `/Users/yuri/WebstormProjects/Kokoro/kokoro-web/src/interfaces/session-stream/session-shell.tsx`
- Modify: `/Users/yuri/WebstormProjects/Kokoro/kokoro-web/src/app/layout.tsx`
- Modify: `/Users/yuri/WebstormProjects/Kokoro/kokoro-web/src/app/page.tsx`
- Test: `/Users/yuri/WebstormProjects/Kokoro/kokoro-web/tests/interfaces/session-stream/session-shell.test.tsx`

- [ ] **Step 1: Write the failing web-shell test first**

```tsx
import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"

import { SessionShell } from "@/interfaces/session-stream/session-shell"

describe("SessionShell", () => {
  it("shows the conversation thread and run detail lane", () => {
    render(<SessionShell />)

    expect(screen.getByText("Kokoro / session stream preview")).toBeInTheDocument()
    expect(screen.getByText("Hello from replay-safe shell.")).toBeInTheDocument()
    expect(screen.getByText("A2UI artifact preview")).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Run the test and verify RED if the shell was reshaped**

Run:
```bash
cd /Users/yuri/WebstormProjects/Kokoro/kokoro-web && bun vitest run tests/interfaces/session-stream/session-shell.test.tsx
```
Expected: fail until the new layout is aligned.

- [ ] **Step 3: Implement the minimal prototype-aligned shell against the real session path**

```tsx
export function SessionShell() {
  return (
    <main>
      <aside>Session Rail</aside>
      <section>Conversation Thread</section>
      <aside>Run Detail Lane</aside>
    </main>
  )
}
```

- [ ] **Step 4: Re-run tests and the full repo checks**

Run:
```bash
cd /Users/yuri/WebstormProjects/Kokoro/kokoro-web && bun run test && bun run lint && bun run typecheck && bun run build
```
Expected: all pass.

- [ ] **Step 5: Commit and push the next `kokoro-web` checkpoint**

```bash
cd /Users/yuri/WebstormProjects/Kokoro/kokoro-web
git add .
git commit -m "feat: align chat shell with demo slice"
git push
```

### Task 5: Wire the first true end-to-end demo path

**Files:**
- Modify: `/Users/yuri/WebstormProjects/kokoro-session/src/interfaces/http.ts`
- Modify: `/Users/yuri/WebstormProjects/Kokoro/kokoro-web/src/interfaces/session-stream/session-shell.tsx`
- Modify: `/Users/yuri/WebstormProjects/Kokoro/kokoro-web/src/application/session-stream-preview.ts`
- Test: `/Users/yuri/WebstormProjects/Kokoro/kokoro-web/tests/interfaces/session-stream/session-shell.test.tsx`

- [ ] **Step 1: Replace local preview-only flow with a real submit + SSE consumption path**

```ts
const response = await fetch("http://localhost:3000/sessions/ses_01/runs", {
  method: "POST",
  body: JSON.stringify({ input: prompt, execution_style: "default" }),
})
```

- [ ] **Step 2: Add the minimal SSE client**

```ts
const source = new EventSource("http://localhost:3000/sessions/ses_01/stream")
source.onmessage = (event) => {
  const parsed = JSON.parse(event.data)
  // fold into reducer-backed state
}
```

- [ ] **Step 3: Verify the browser can show streamed text and artifact summary**

Run:
```bash
cd /Users/yuri/WebstormProjects/Kokoro/kokoro-web && bun run test && bun run build
```
Expected: pass.

- [ ] **Step 4: Push the integrated checkpoint**

```bash
cd /Users/yuri/WebstormProjects/Kokoro/kokoro-web && git add . && git commit -m "feat: connect web to session demo slice" && git push
cd /Users/yuri/WebstormProjects/kokoro-session && git add . && git commit -m "feat: stream demo events over sse" && git push
```

### Task 6: Update progress tracking in the spec source repo

**Files:**
- Modify: `/Users/yuri/WebstormProjects/Kokoro/claude-progress.md`
- Modify: `/Users/yuri/WebstormProjects/Kokoro/tasks/todo.md`

- [ ] **Step 1: Update the progress file with actual demo-slice status**

```markdown
- Active stream: three-repo demo slice
- Completed:
  - Repo initialization and remote setup
  - Agent bootstrap
  - Session bridge bootstrap
  - Prototype-aligned web chat shell
- Remaining:
  - Real SSE integration polish
  - Replay hardening
```

- [ ] **Step 2: Update the todo checklist**

```markdown
- [x] Initialize kokoro-agent repository and push first checkpoint.
- [x] Initialize kokoro-session repository and push first checkpoint.
- [x] Align kokoro-web with the demo chat shell.
- [ ] Finish the first real end-to-end browser demo.
```

- [ ] **Step 3: Commit the spec-source repo updates**

```bash
cd /Users/yuri/WebstormProjects/Kokoro
git add claude-progress.md tasks/todo.md docs/superpowers/specs/2026-05-29-three-repo-demo-slice-design.md docs/superpowers/plans/2026-05-29-three-repo-demo-slice.md
git commit -m "docs: track three-repo demo slice"
git push
```
