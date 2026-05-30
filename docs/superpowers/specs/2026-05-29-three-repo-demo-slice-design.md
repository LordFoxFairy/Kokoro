# Three-Repo Demo Slice Design

- **Date:** 2026-05-29
- **Status:** approved-by-user-delegation
- **Scope:** `kokoro-web` + `kokoro-session` + `kokoro-agent` first end-to-end demo slice
- **Runtime repos:**
  - `kokoro-web` → `https://github.com/LordFoxFairy/kokoro-web.git`
  - `kokoro-session` → `https://github.com/LordFoxFairy/kokoro-session.git`
  - `kokoro-agent` → `https://github.com/LordFoxFairy/kokoro-agent.git`
- **Related:** `docs/decisions/ADR-007-prototype-and-production-stack.md`, `docs/decisions/ADR-009-repository-boundaries-and-ownership.md`, `docs/protocol/session-stream.md`, `docs/protocol/session-replay-and-resume.md`

---

## 1. Goal

Build the smallest believable three-repository Kokoro demo that supports a real chat request flowing through all runtime repos:

1. User submits a prompt in `kokoro-web`
2. `kokoro-session` creates a run and opens an SSE stream
3. `kokoro-agent` (DeepAgents + Python + LangChain ecosystem) produces normalized events
4. `kokoro-session` forwards browser-safe SSE events with a replay buffer
5. `kokoro-web` renders a prototype-aligned chat shell with streaming assistant text, run status, and a minimal artifact summary

This slice must optimize for **demo clarity, debugging ease, and clean boundaries**, not feature breadth.

---

## 2. Non-goals for the first slice

Do **not** build these in phase 1:

- Full Redis durability
- Full permission workflow
- Full MCP / workflow / team surfaces
- Complex A2UI canvas renderer
- Multi-user collaboration
- Compatibility layers for older naming or architecture

If a feature does not help the first end-to-end chat demo, it stays out.

---

## 3. Recommended approach

### Chosen approach: Chat-first thin bridge

- `kokoro-web` becomes a simple, prototype-aligned chat application shell
- `kokoro-session` is a thin HTTP + SSE broker with a small in-memory replay buffer
- `kokoro-agent` is a focused DeepAgents-powered event producer

### Why this is the best option

- It follows the user’s preference for the **best current path** rather than compatibility baggage
- It minimizes code while preserving clean repo boundaries
- It uses mature ecosystem pieces instead of custom frameworks
- It gives the fastest path to a believable three-repo demo that is easy to debug live

### Alternatives rejected

#### Session-first heavy contract rig
Rejected because it delays the first visible demo and over-invests in the middle layer before the user sees real value.

#### Agent-first orchestration showcase
Rejected because it makes the agent impressive in isolation but slows down the browser-visible end-to-end flow.

---

## 4. Repository responsibilities for phase 1

### `kokoro-web`
Owns:
- Session rail
- Conversation thread
- Composer
- Run detail lane
- SSE client
- Replay UI recovery

Does not own:
- Agent execution
- Redis replay logic
- Final permission decisions

### `kokoro-session`
Owns:
- Session/run lifecycle
- `POST /sessions/:id/runs`
- `GET /sessions/:id/stream`
- SSE serialization
- Small replay buffer
- Normalization from agent events to browser SSE events

Does not own:
- DOM / UI rendering
- DeepAgents logic

### `kokoro-agent`
Owns:
- DeepAgents + LangChain execution
- Prompt-to-event production
- Minimal artifact summary generation

Does not own:
- Browser-facing SSE transport
- Web layout
- Replay storage

---

## 5. First-screen `kokoro-web` layout

The first browser screen should mirror the prototype’s chat shape, but remain implementation-light.

### Regions

1. **Session Rail**
   - Brand
   - New chat button
   - Recent conversations
   - Settings/account entry

2. **Conversation Thread**
   - Title row
   - Streaming message area
   - User messages right-aligned
   - Assistant messages left-aligned prose-first
   - Inline status blocks where needed

3. **Composer**
   - Text input
   - Send action
   - Minimal status affordance only

4. **Run Detail Lane**
   - Current run status pill
   - Latest artifact summary card
   - Replay status hint

### First-screen states

Must support:
- Empty
- Streaming
- Completed
- Failed
- Replaying

### Naming

Use the clearest production names:
- `Session Rail`
- `Conversation Thread`
- `Composer`
- `Run Detail Lane`
- `Artifact Summary Card`

Avoid awkward provisional names that exist only because of older experiments.

---

## 6. First event set

### Agent-to-session internal events

The first agent event contract only needs:
- `run.created`
- `message.delta`
- `message.completed`
- `artifact.available`
- `run.completed`
- `run.failed`

### Session-to-web SSE events

The first browser-facing SSE contract only needs:
- `session.created`
- `run.created`
- `message.delta`
- `message.completed`
- `artifact.available`
- `run.completed`
- `run.failed`

This intentionally excludes more advanced surfaces like `permission.required`, `thinking.summary`, and tool lifecycle until the first demo is stable.

---

## 7. First replay model

Phase 1 replay must be intentionally small and predictable:

- In-memory event buffer owned by `kokoro-session`
- Append-only per session
- Client reconnects with latest cursor
- Server replays events after that cursor
- Refresh must reconstruct the latest visible conversation state

Do not introduce Redis in phase 1 unless a hard blocker appears.

---

## 8. Minimal repository skeletons

### `kokoro-agent`

```text
src/kokoro_agent/
  domain/events.py
  application/run_agent.py
  infrastructure/runner.py
```

Reasoning:
- Responsibility-first naming
- No DeepAgents/LangChain prefixes in filenames
- No fake abstraction for runtime switching

### `kokoro-session`

```text
src/
  domain/events.ts
  application/start_run.ts
  infrastructure/sse.ts
  infrastructure/memory_store.ts
  infrastructure/agent_client.ts
  interfaces/http.ts
```

Reasoning:
- Smallest useful bridge
- Explicit in-memory storage in phase 1
- Explicit agent client boundary

### `kokoro-web`

Continue evolving the current repo toward:

```text
src/
  app/
  domain/shared/
  application/
  infrastructure/
  interfaces/
```

with emphasis on the chat shell and SSE consumption path, not an elaborate A2UI artifact renderer.

---

## 9. Acceptance criteria

The first slice is done only when:

1. All three runtime repos are independently git-initialized, connected to their GitHub origins, and pushed at meaningful checkpoints
2. `kokoro-web` renders the prototype-aligned chat shell
3. A browser prompt can reach `kokoro-agent` through `kokoro-session`
4. Assistant text streams visibly in the UI
5. A minimal artifact summary card appears in the right lane
6. Refresh restores the latest stream via replay
7. Each repo passes its own local verification commands
8. No compatibility shims or legacy dual-path code are introduced to get there
