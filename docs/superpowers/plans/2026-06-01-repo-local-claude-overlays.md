# Repo-Local CLAUDE Overlays Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add thin, repo-local `CLAUDE.md` overlays for `kokoro-web`, `kokoro-session`, and `kokoro-agent` so contributors can understand local boundaries, file placement, verification commands, and stack pitfalls without duplicating root Kokoro governance.

**Architecture:** Keep `Kokoro/CLAUDE.md` as the global governance source of truth and add short, progressive-disclosure overlays in each primary runtime repo. Each overlay should describe repo purpose, critical boundaries, where code belongs, verification commands, and local pitfalls, while preserving existing framework-specific notes such as `kokoro-web/AGENTS.md`.

**Tech Stack:** Markdown instruction files, Next.js 16, React 19, TypeScript, Bun, Zod, ioredis, Python 3.11, Pydantic v2, Ruff, Pyright

---

### Task 1: Add the `kokoro-web` thin overlay

**Files:**
- Modify: `/Users/yuri/WebstormProjects/Kokoro/kokoro-web/CLAUDE.md`
- Reference: `/Users/yuri/WebstormProjects/Kokoro/kokoro-web/AGENTS.md`
- Reference: `/Users/yuri/WebstormProjects/Kokoro/kokoro-web/package.json`
- Reference: `/Users/yuri/WebstormProjects/Kokoro/kokoro-web/vitest.config.ts`

- [ ] **Step 1: Write the full replacement content for `kokoro-web/CLAUDE.md`**

```md
@AGENTS.md

# kokoro-web local overlay

This file adds repo-local guidance for `kokoro-web`. Root governance still lives in `Kokoro/CLAUDE.md` and the protocol/spec docs under `Kokoro/docs/`.

## Repo purpose

`kokoro-web` is the Next.js frontend for Kokoro.

It owns:
- chat UI
- session-stream consumption over HTTP/SSE
- AGUI/A2UI-oriented rendering
- browser-facing replay presentation

It must not own:
- session orchestration
- Redis/replay storage internals
- raw agent-event semantics
- direct coupling to `kokoro-agent`

## Critical boundaries

- Treat `kokoro-session` as the browser-facing contract owner.
- Parse transport envelopes in infrastructure, then map them into domain/application-friendly events.
- Keep reducers and UI components transport-agnostic.
- Keep `use client` isolated to interactive entrypoints.
- When touching Next.js App Router behavior, read the relevant framework docs referenced by `AGENTS.md` before changing code.

## Where code belongs

- `src/domain/` → domain event types and pure business shapes
- `src/application/` → state folding, stream consumption orchestration, app-facing flows
- `src/infrastructure/` → protocol parsing, transport adapters, browser boundary code
- `src/interfaces/` → React components and UI composition
- `src/app/` → framework entrypoints only

Do not let UI components reach directly into raw transport parsing when an application or infrastructure module can own that boundary.

## Verification checklist

- Run `npm run lint` after any code change.
- Run `npm run typecheck` after any TypeScript or protocol change.
- Run `npm run test` after any reducer, stream, or parser change.
- Run `npm run build` when touching `src/app/*`, metadata, layout, or hydration-sensitive client/server boundaries.

## Local pitfalls

- Do not weaken strict parsing in `src/infrastructure/protocol/*` just to tolerate drift from upstream; fix the owner or the spec.
- Do not move session-stream ownership into components.
- Do not expand client components upward unless interactivity truly requires it.
- Vitest runs in `jsdom`; browser APIs may need explicit stubs in tests.
```

- [ ] **Step 2: Write the file exactly as planned**

Use the content from Step 1 to replace `/Users/yuri/WebstormProjects/Kokoro/kokoro-web/CLAUDE.md`.

- [ ] **Step 3: Read the file and verify the thin-overlay structure**

Run:
```bash
python3 - <<'PY'
from pathlib import Path
p = Path('/Users/yuri/WebstormProjects/Kokoro/kokoro-web/CLAUDE.md')
text = p.read_text()
for required in [
    '@AGENTS.md',
    '## Repo purpose',
    '## Critical boundaries',
    '## Where code belongs',
    '## Verification checklist',
    '## Local pitfalls',
]:
    assert required in text, required
print('kokoro-web CLAUDE structure ok')
PY
```
Expected: prints `kokoro-web CLAUDE structure ok`.

- [ ] **Step 4: Commit the `kokoro-web` overlay**

```bash
cd /Users/yuri/WebstormProjects/Kokoro/kokoro-web
git add CLAUDE.md
git commit -m "docs: add kokoro-web CLAUDE overlay"
```

### Task 2: Add the `kokoro-session` thin overlay

**Files:**
- Create: `/Users/yuri/WebstormProjects/Kokoro/kokoro-session/CLAUDE.md`
- Reference: `/Users/yuri/WebstormProjects/Kokoro/kokoro-session/package.json`
- Reference: `/Users/yuri/WebstormProjects/Kokoro/kokoro-session/src/main.ts`

- [ ] **Step 1: Write the full file content for `kokoro-session/CLAUDE.md`**

```md
# kokoro-session local overlay

This file adds repo-local guidance for `kokoro-session`. Root governance still lives in `Kokoro/CLAUDE.md` and the protocol/spec docs under `Kokoro/docs/`.

## Repo purpose

`kokoro-session` is the browser-facing session, SSE, and replay owner.

It owns:
- session/run lifecycle
- HTTP session endpoints
- browser-facing session-stream contract
- SSE serialization
- replay/resume semantics
- normalization from raw agent events into browser-safe events

It must not own:
- frontend rendering
- raw UI state
- DeepAgents execution logic
- direct browser component concerns

## Critical boundaries

- `kokoro-session` owns the browser-facing contract consumed by `kokoro-web`.
- Raw worker events from `kokoro-agent` must be normalized here before reaching the browser.
- Do not duplicate boundary types across `domain`, `application`, `interfaces`, or docs.
- Keep `src/main.ts` as wiring only.

## Where code belongs

- `src/domain/` → event schemas, domain-level contracts, pure types
- `src/application/` → orchestration, normalization, run/session flows
- `src/infrastructure/` → Redis, SSE framing, stream/replay storage details
- `src/interfaces/` → HTTP request/response handling only
- `src/main.ts` → composition root only

When a file starts combining schema ownership, orchestration, and transport specifics, split it before it becomes a navigation problem.

## Verification checklist

- Run `bun run lint` after code changes.
- Run `bun run typecheck` after TypeScript or schema changes.
- Run `bun test` after protocol, replay, stream, or HTTP changes.
- For contract changes, verify the matching Kokoro spec docs and the `kokoro-web` consumer behavior in the same slice.

## Local pitfalls

- Do not let browser-facing event names or payloads drift from `Kokoro/docs/protocol/*`.
- Do not move Redis/SSE semantics into application orchestration if they belong in infrastructure.
- Do not reintroduce duplicate protocol types across layers.
- Do not let `src/main.ts` absorb business logic just because it is convenient.
```

- [ ] **Step 2: Create the file exactly as planned**

Use the content from Step 1 to create `/Users/yuri/WebstormProjects/Kokoro/kokoro-session/CLAUDE.md`.

- [ ] **Step 3: Read the file and verify the thin-overlay structure**

Run:
```bash
python3 - <<'PY'
from pathlib import Path
p = Path('/Users/yuri/WebstormProjects/Kokoro/kokoro-session/CLAUDE.md')
text = p.read_text()
for required in [
    '## Repo purpose',
    '## Critical boundaries',
    '## Where code belongs',
    '## Verification checklist',
    '## Local pitfalls',
]:
    assert required in text, required
print('kokoro-session CLAUDE structure ok')
PY
```
Expected: prints `kokoro-session CLAUDE structure ok`.

- [ ] **Step 4: Commit the `kokoro-session` overlay**

```bash
cd /Users/yuri/WebstormProjects/Kokoro/kokoro-session
git add CLAUDE.md
git commit -m "docs: add kokoro-session CLAUDE overlay"
```

### Task 3: Add the `kokoro-agent` thin overlay

**Files:**
- Create: `/Users/yuri/WebstormProjects/Kokoro/kokoro-agent/CLAUDE.md`
- Reference: `/Users/yuri/WebstormProjects/Kokoro/kokoro-agent/pyproject.toml`
- Reference: `/Users/yuri/WebstormProjects/Kokoro/kokoro-agent/src/kokoro_agent/worker.py`
- Reference: `/Users/yuri/WebstormProjects/Kokoro/kokoro-agent/src/kokoro_agent/run_agent.py`

- [ ] **Step 1: Write the full file content for `kokoro-agent/CLAUDE.md`**

```md
# kokoro-agent local overlay

This file adds repo-local guidance for `kokoro-agent`. Root governance still lives in `Kokoro/CLAUDE.md` and the protocol/spec docs under `Kokoro/docs/`.

## Repo purpose

`kokoro-agent` is the Python worker and raw execution-event producer.

It owns:
- worker lifecycle
- model/tool execution orchestration
- raw execution event emission
- producer-side boundary validation before events leave the worker

It must not own:
- browser-facing SSE/session contracts
- frontend rendering concerns
- browser replay semantics
- direct coupling to `kokoro-web`

## Critical boundaries

- `worker.py` should own long-running loop and lifecycle concerns.
- `run_agent.py` should own execution behavior and emitted event sequencing.
- Event/message/result payloads should use explicit Pydantic models near the boundary; avoid ad hoc dict drift.
- Browser-facing contracts belong to `kokoro-session`, not here.

## Where code belongs

- `src/kokoro_agent/events.py` → boundary event models and protocol-side data structures
- `src/kokoro_agent/run_agent.py` → execution flow and event production
- `src/kokoro_agent/worker.py` → worker loop and stream handling
- `src/kokoro_agent/infrastructure/` → model client, stream adapters, integration details

If worker lifecycle logic and event-generation logic start mixing in one file, split them before the module becomes hard to navigate.

## Verification checklist

- Run `pytest` after behavior changes.
- Run `ruff check` after Python code changes.
- Run `pyright` after changing models, event shapes, or package structure.
- For raw event contract changes, verify the matching `kokoro-session` parser/tests in the same slice.

## Local pitfalls

- Do not leak browser-facing assumptions into raw execution events.
- Do not replace explicit Pydantic models with loosely shaped dicts at the boundary.
- Do not let top-level modules accumulate unrelated helpers when a focused submodule would be clearer.
- Keep the `src/kokoro_agent` package structure predictable so Pyright and editor navigation remain reliable.
```

- [ ] **Step 2: Create the file exactly as planned**

Use the content from Step 1 to create `/Users/yuri/WebstormProjects/Kokoro/kokoro-agent/CLAUDE.md`.

- [ ] **Step 3: Read the file and verify the thin-overlay structure**

Run:
```bash
python3 - <<'PY'
from pathlib import Path
p = Path('/Users/yuri/WebstormProjects/Kokoro/kokoro-agent/CLAUDE.md')
text = p.read_text()
for required in [
    '## Repo purpose',
    '## Critical boundaries',
    '## Where code belongs',
    '## Verification checklist',
    '## Local pitfalls',
]:
    assert required in text, required
print('kokoro-agent CLAUDE structure ok')
PY
```
Expected: prints `kokoro-agent CLAUDE structure ok`.

- [ ] **Step 4: Commit the `kokoro-agent` overlay**

```bash
cd /Users/yuri/WebstormProjects/Kokoro/kokoro-agent
git add CLAUDE.md
git commit -m "docs: add kokoro-agent CLAUDE overlay"
```

### Task 4: Verify the overlays against root governance and repo priorities

**Files:**
- Modify: `/Users/yuri/WebstormProjects/Kokoro/docs/superpowers/specs/2026-06-01-repo-local-claude-overlays-design.md` (reference only if clarifying intent)
- Reference: `/Users/yuri/WebstormProjects/Kokoro/CLAUDE.md`
- Reference: `/Users/yuri/WebstormProjects/Kokoro/docs/product/04-architecture/repository-boundaries.md`
- Reference: `/Users/yuri/WebstormProjects/Kokoro/docs/protocol/README.md`

- [ ] **Step 1: Run a consistency check across all three overlays**

Run:
```bash
python3 - <<'PY'
from pathlib import Path
files = [
    Path('/Users/yuri/WebstormProjects/Kokoro/kokoro-web/CLAUDE.md'),
    Path('/Users/yuri/WebstormProjects/Kokoro/kokoro-session/CLAUDE.md'),
    Path('/Users/yuri/WebstormProjects/Kokoro/kokoro-agent/CLAUDE.md'),
]
required = [
    '## Repo purpose',
    '## Critical boundaries',
    '## Where code belongs',
    '## Verification checklist',
    '## Local pitfalls',
]
for file in files:
    text = file.read_text()
    for marker in required:
        assert marker in text, (file, marker)
print('all overlay structures ok')
PY
```
Expected: prints `all overlay structures ok`.

- [ ] **Step 2: Manually review for conflict with root governance**

Read these files together and confirm the overlays complement rather than contradict them:
- `/Users/yuri/WebstormProjects/Kokoro/CLAUDE.md`
- `/Users/yuri/WebstormProjects/Kokoro/docs/product/04-architecture/repository-boundaries.md`
- `/Users/yuri/WebstormProjects/Kokoro/docs/protocol/README.md`
- the three new/updated subrepo `CLAUDE.md` files

Expected review result:
- root docs still own global governance
- subrepo overlays only add local stack/boundary guidance
- the current priority remains the three primary repos, not future support repos

- [ ] **Step 3: Show the final pending changes for the three repos**

Run:
```bash
for repo in \
  /Users/yuri/WebstormProjects/Kokoro/kokoro-web \
  /Users/yuri/WebstormProjects/Kokoro/kokoro-session \
  /Users/yuri/WebstormProjects/Kokoro/kokoro-agent; do
  echo "=== $repo ==="
  git -C "$repo" status --short
  echo
 done
```
Expected: each repo shows only its `CLAUDE.md` change for this slice.

- [ ] **Step 4: Commit any final wording adjustments in the affected repos**

If the review in Step 2 requires wording cleanup, commit those final edits in the corresponding repo with one of:

```bash
cd /Users/yuri/WebstormProjects/Kokoro/kokoro-web && git add CLAUDE.md && git commit -m "docs: refine kokoro-web CLAUDE overlay"
```

```bash
cd /Users/yuri/WebstormProjects/Kokoro/kokoro-session && git add CLAUDE.md && git commit -m "docs: refine kokoro-session CLAUDE overlay"
```

```bash
cd /Users/yuri/WebstormProjects/Kokoro/kokoro-agent && git add CLAUDE.md && git commit -m "docs: refine kokoro-agent CLAUDE overlay"
```

If no wording adjustment is needed, record that no extra commit was necessary.

---

## Self-review

- Spec coverage: this plan covers all approved repo-local overlay requirements: thin layering, three-repo priority, progressive disclosure structure, local verification commands, and non-conflict with root governance.
- Placeholder scan: no TBD/TODO placeholders remain; every file path, content block, and command is explicit.
- Type consistency: repo names, file paths, and section headings are consistent across all tasks.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-01-repo-local-claude-overlays.md`. Two execution options:

1. Subagent-Driven (recommended) - I dispatch a fresh subagent per task, review between tasks, fast iteration

2. Inline Execution - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?