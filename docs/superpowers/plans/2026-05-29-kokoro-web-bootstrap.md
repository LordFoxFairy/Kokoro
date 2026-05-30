# Kokoro Web Bootstrap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an independent `kokoro-web` repository under the parent workspace with a Bun-managed Next.js frontend, strict DDD boundaries, and a tested protocol-driven chat-shell skeleton.

**Architecture:** The repo consumes protocol contracts as strict Zod schemas in `domain/shared`, folds session events into replay-safe UI state in `application`, exposes browser/runtime adapters in `infrastructure`, and renders a minimal shell in `interfaces`. The parent `Kokoro` repository only tracks docs and ignores the child repo source.

**Tech Stack:** Bun, Next.js App Router, React, TypeScript, Tailwind CSS, shadcn/ui, Zod, Vitest, Testing Library

---

### Task 1: Parent repository ignores and planning artifacts

**Files:**
- Modify: `.gitignore`
- Create: `docs/superpowers/specs/2026-05-29-kokoro-web-design.md`
- Create: `docs/superpowers/plans/2026-05-29-kokoro-web-bootstrap.md`
- Create: `claude-progress.md`
- Create: `tasks/todo.md`

- [ ] **Step 1: Add child repository ignore rule to parent `.gitignore`**

```gitignore
kokoro-web/
```

- [ ] **Step 2: Verify the parent repo now hides the child repo path**

Run: `git check-ignore -v kokoro-web`
Expected: output references `.gitignore` and the `kokoro-web/` rule.

- [ ] **Step 3: Write the progress handoff file**

```markdown
# Claude Progress

- Date: 2026-05-29
- Active stream: kokoro-web bootstrap
- Completed:
  - Wrote kokoro-web design spec
  - Wrote kokoro-web implementation plan
- In progress:
  - Create independent kokoro-web repository
  - Scaffold strict DDD frontend skeleton
- Next verification:
  - `cd kokoro-web && bun run test && bun run lint && bun run typecheck`
```

- [ ] **Step 4: Write the task checklist file**

```markdown
# Todo

- [ ] Create `kokoro-web/` as an independent Git repository.
- [ ] Scaffold Bun + Next.js + Tailwind + shadcn/ui baseline.
- [ ] Add DDD folders and dependency boundaries.
- [ ] Add strict protocol schemas with failing tests first.
- [ ] Add replay reducer with failing tests first.
- [ ] Render the minimal chat shell using seed events.
- [ ] Run test, lint, and typecheck.
```

- [ ] **Step 5: Commit the parent-repo planning artifacts**

```bash
git add .gitignore docs/superpowers/specs/2026-05-29-kokoro-web-design.md docs/superpowers/plans/2026-05-29-kokoro-web-bootstrap.md claude-progress.md tasks/todo.md
git commit -m "docs(kokoro): add kokoro-web bootstrap spec and plan"
```

### Task 2: Create the independent `kokoro-web` repository

**Files:**
- Create: `kokoro-web/.gitignore`
- Create: `kokoro-web/package.json`
- Create: `kokoro-web/bun.lock`
- Create: `kokoro-web/tsconfig.json`
- Create: `kokoro-web/next.config.ts`
- Create: `kokoro-web/eslint.config.mjs`
- Create: `kokoro-web/components.json`

- [ ] **Step 1: Bootstrap the Next.js app without a nested auto-generated git repo conflict**

```bash
bun create next-app@latest kokoro-web --ts --tailwind --eslint --app --src-dir --use-bun --import-alias "@/*" --yes --disable-git
```

- [ ] **Step 2: Verify the scaffold command produced the expected root files**

Run: `find kokoro-web -maxdepth 2 \( -name package.json -o -name tsconfig.json -o -name next.config.ts -o -name src \) | sort`
Expected: includes `kokoro-web/package.json`, `kokoro-web/tsconfig.json`, `kokoro-web/next.config.ts`, and `kokoro-web/src`.

- [ ] **Step 3: Initialize the child repository Git history**

```bash
cd kokoro-web && git init && git branch -m main
```

- [ ] **Step 4: Replace the default ignore file with a repo-specific strict frontend ignore set**

```gitignore
# dependencies
node_modules/

# next build output
.next/
out/

# production
build/
coverage/

# local env files
.env*
!.env.example

# logs
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*

# system / editor
.DS_Store
.idea/
.vscode/

# test artifacts
playwright-report/
vitest-report/
```

- [ ] **Step 5: Commit the raw scaffold in the child repository**

```bash
cd kokoro-web && git add . && git commit -m "chore(repo): initialize next frontend scaffold"
```

### Task 3: Install UI/runtime dependencies and DDD structure

**Files:**
- Modify: `kokoro-web/package.json`
- Modify: `kokoro-web/tsconfig.json`
- Create: `kokoro-web/components.json`
- Create: `kokoro-web/src/domain/shared/.gitkeep`
- Create: `kokoro-web/src/application/.gitkeep`
- Create: `kokoro-web/src/infrastructure/.gitkeep`
- Create: `kokoro-web/src/interfaces/.gitkeep`
- Create: `kokoro-web/src/lib/utils.ts`

- [ ] **Step 1: Install the minimal runtime and test dependencies**

```bash
cd kokoro-web && bun add zod @a2ui/react clsx tailwind-merge && bun add -d vitest @testing-library/react @testing-library/jest-dom jsdom @types/jsdom
```

- [ ] **Step 2: Initialize shadcn/ui non-interactively**

```bash
cd kokoro-web && bunx --bun shadcn@latest init -y --template next
```

- [ ] **Step 3: Create the DDD directories and a shared className utility**

```bash
cd kokoro-web && mkdir -p src/domain/shared src/application src/infrastructure src/interfaces src/tests
```

```ts
import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

- [ ] **Step 4: Verify the directories and `components.json` now exist**

Run: `find kokoro-web/src -maxdepth 2 -type d | sort && test -f kokoro-web/components.json`
Expected: prints `domain/shared`, `application`, `infrastructure`, `interfaces` and exits 0.

- [ ] **Step 5: Commit the dependency and structure baseline**

```bash
cd kokoro-web && git add package.json bun.lock components.json tsconfig.json src/lib/utils.ts src/domain src/application src/infrastructure src/interfaces && git commit -m "chore(frontend): add ddd folders and ui dependencies"
```

### Task 4: Write failing tests for protocol schemas

**Files:**
- Create: `kokoro-web/src/domain/shared/session-event.ts`
- Create: `kokoro-web/tests/domain/shared/session-event.test.ts`

- [ ] **Step 1: Write the failing schema tests first**

```ts
import { describe, expect, it } from "vitest"
import { parseSessionEvent } from "@/domain/shared/session-event"

describe("parseSessionEvent", () => {
  it("accepts a valid message delta envelope", () => {
    const event = parseSessionEvent({
      event: "message.delta",
      event_id: "evt_01",
      session_id: "ses_01",
      conversation_id: "conv_01",
      run_id: "run_01",
      cursor: "1748428800-000012",
      timestamp: "2026-05-28T12:00:00.000Z",
      payload: {
        message_id: "msg_01",
        delta: "Hello",
        role: "assistant",
      },
    })

    expect(event.event).toBe("message.delta")
    expect(event.payload.delta).toBe("Hello")
  })

  it("rejects extra top-level fields", () => {
    expect(() =>
      parseSessionEvent({
        event: "run.completed",
        event_id: "evt_02",
        session_id: "ses_01",
        conversation_id: "conv_01",
        run_id: "run_01",
        cursor: "1748428800-000013",
        timestamp: "2026-05-28T12:00:01.000Z",
        payload: { run_id: "run_01", status: "completed" },
        injected: true,
      }),
    ).toThrowError(/unrecognized/i)
  })
})
```

- [ ] **Step 2: Run the schema test and verify RED**

Run: `cd kokoro-web && bun vitest run tests/domain/shared/session-event.test.ts`
Expected: FAIL because `@/domain/shared/session-event` does not exist yet.

- [ ] **Step 3: Write the minimal Zod-backed parser**

```ts
import { z } from "zod"

const envelopeSchema = z
  .object({
    event: z.enum([
      "session.created",
      "message.delta",
      "message.completed",
      "artifact.available",
      "permission.required",
      "run.completed",
      "run.failed",
    ]),
    event_id: z.string().min(1),
    session_id: z.string().min(1),
    conversation_id: z.string().min(1),
    run_id: z.string().min(1),
    cursor: z.string().min(1),
    timestamp: z.string().datetime(),
    payload: z.unknown(),
  })
  .strict()

const messageDeltaSchema = envelopeSchema.extend({
  event: z.literal("message.delta"),
  payload: z
    .object({
      message_id: z.string().min(1),
      delta: z.string(),
      role: z.enum(["assistant", "user"]),
    })
    .strict(),
})

const runCompletedSchema = envelopeSchema.extend({
  event: z.literal("run.completed"),
  payload: z
    .object({
      run_id: z.string().min(1),
      status: z.enum(["completed"]),
    })
    .strict(),
})

const fallbackSchema = envelopeSchema

const sessionEventSchema = z.union([
  messageDeltaSchema,
  runCompletedSchema,
  fallbackSchema,
])

export type SessionEvent = z.infer<typeof sessionEventSchema>

export function parseSessionEvent(input: unknown): SessionEvent {
  return sessionEventSchema.parse(input)
}
```

- [ ] **Step 4: Re-run the schema test and verify GREEN**

Run: `cd kokoro-web && bun vitest run tests/domain/shared/session-event.test.ts`
Expected: PASS with 2 tests passed.

- [ ] **Step 5: Commit the protocol schema slice**

```bash
cd kokoro-web && git add src/domain/shared/session-event.ts tests/domain/shared/session-event.test.ts && git commit -m "feat(domain): add session event schema"
```

### Task 5: Write failing tests for replay-safe reducer

**Files:**
- Create: `kokoro-web/src/application/session-stream-reducer.ts`
- Create: `kokoro-web/tests/application/session-stream-reducer.test.ts`

- [ ] **Step 1: Write the failing reducer tests first**

```ts
import { describe, expect, it } from "vitest"
import { applySessionEvent, createSessionStreamState } from "@/application/session-stream-reducer"
import { parseSessionEvent } from "@/domain/shared/session-event"

describe("applySessionEvent", () => {
  it("deduplicates repeated event ids", () => {
    const event = parseSessionEvent({
      event: "message.delta",
      event_id: "evt_01",
      session_id: "ses_01",
      conversation_id: "conv_01",
      run_id: "run_01",
      cursor: "1748428800-000012",
      timestamp: "2026-05-28T12:00:00.000Z",
      payload: { message_id: "msg_01", delta: "Hi", role: "assistant" },
    })

    const once = applySessionEvent(createSessionStreamState(), event)
    const twice = applySessionEvent(once, event)

    expect(twice.messages).toHaveLength(1)
    expect(twice.messages[0]?.content).toBe("Hi")
    expect(twice.seenEventIds).toEqual(["evt_01"])
  })

  it("lets message.completed replace accumulated delta content", () => {
    const state = [
      parseSessionEvent({
        event: "message.delta",
        event_id: "evt_01",
        session_id: "ses_01",
        conversation_id: "conv_01",
        run_id: "run_01",
        cursor: "1748428800-000012",
        timestamp: "2026-05-28T12:00:00.000Z",
        payload: { message_id: "msg_01", delta: "He", role: "assistant" },
      }),
      parseSessionEvent({
        event: "message.delta",
        event_id: "evt_02",
        session_id: "ses_01",
        conversation_id: "conv_01",
        run_id: "run_01",
        cursor: "1748428800-000013",
        timestamp: "2026-05-28T12:00:01.000Z",
        payload: { message_id: "msg_01", delta: "llo", role: "assistant" },
      }),
      parseSessionEvent({
        event: "message.completed",
        event_id: "evt_03",
        session_id: "ses_01",
        conversation_id: "conv_01",
        run_id: "run_01",
        cursor: "1748428800-000014",
        timestamp: "2026-05-28T12:00:02.000Z",
        payload: { message_id: "msg_01", role: "assistant", content: "Hello" },
      }),
    ].reduce(applySessionEvent, createSessionStreamState())

    expect(state.messages[0]?.content).toBe("Hello")
  })
})
```

- [ ] **Step 2: Run the reducer test and verify RED**

Run: `cd kokoro-web && bun vitest run tests/application/session-stream-reducer.test.ts`
Expected: FAIL because the reducer module does not exist yet.

- [ ] **Step 3: Write the minimal reducer**

```ts
import type { SessionEvent } from "@/domain/shared/session-event"

export type SessionMessage = {
  id: string
  role: "assistant" | "user"
  content: string
}

export type SessionStreamState = {
  seenEventIds: string[]
  messages: SessionMessage[]
  runStatus: "idle" | "completed" | "failed"
}

export function createSessionStreamState(): SessionStreamState {
  return {
    seenEventIds: [],
    messages: [],
    runStatus: "idle",
  }
}

export function applySessionEvent(
  state: SessionStreamState,
  event: SessionEvent,
): SessionStreamState {
  if (state.seenEventIds.includes(event.event_id)) {
    return state
  }

  const nextState: SessionStreamState = {
    ...state,
    seenEventIds: [...state.seenEventIds, event.event_id],
    messages: [...state.messages],
  }

  if (event.event === "message.delta") {
    const existing = nextState.messages.find((message) => message.id === event.payload.message_id)

    if (existing) {
      existing.content += event.payload.delta
    } else {
      nextState.messages.push({
        id: event.payload.message_id,
        role: event.payload.role,
        content: event.payload.delta,
      })
    }
  }

  if (event.event === "message.completed") {
    const index = nextState.messages.findIndex((message) => message.id === event.payload.message_id)

    if (index >= 0) {
      nextState.messages[index] = {
        id: event.payload.message_id,
        role: event.payload.role,
        content: event.payload.content,
      }
    } else {
      nextState.messages.push({
        id: event.payload.message_id,
        role: event.payload.role,
        content: event.payload.content,
      })
    }
  }

  if (event.event === "run.completed") {
    nextState.runStatus = "completed"
  }

  if (event.event === "run.failed") {
    nextState.runStatus = "failed"
  }

  return nextState
}
```

- [ ] **Step 4: Re-run the reducer test and verify GREEN**

Run: `cd kokoro-web && bun vitest run tests/application/session-stream-reducer.test.ts`
Expected: PASS with 2 tests passed.

- [ ] **Step 5: Commit the reducer slice**

```bash
cd kokoro-web && git add src/application/session-stream-reducer.ts tests/application/session-stream-reducer.test.ts && git commit -m "feat(application): add replay-safe session reducer"
```

### Task 6: Render the minimal chat shell

**Files:**
- Modify: `kokoro-web/src/app/page.tsx`
- Create: `kokoro-web/src/interfaces/session-stream/session-shell.tsx`
- Create: `kokoro-web/src/interfaces/session-stream/session-shell.test.tsx`
- Create: `kokoro-web/src/interfaces/session-stream/seed-events.ts`

- [ ] **Step 1: Write the failing UI test first**

```tsx
import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"
import { SessionShell } from "@/interfaces/session-stream/session-shell"

describe("SessionShell", () => {
  it("renders the folded assistant message and status", () => {
    render(<SessionShell />)

    expect(screen.getByText("Kokoro / session stream preview")).toBeInTheDocument()
    expect(screen.getByText("Hello from replay-safe shell.")).toBeInTheDocument()
    expect(screen.getByText("completed")).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Run the UI test and verify RED**

Run: `cd kokoro-web && bun vitest run src/interfaces/session-stream/session-shell.test.tsx`
Expected: FAIL because `SessionShell` does not exist yet.

- [ ] **Step 3: Write the seed events and minimal component**

```ts
import { parseSessionEvent } from "@/domain/shared/session-event"

export const seedEvents = [
  parseSessionEvent({
    event: "message.delta",
    event_id: "evt_01",
    session_id: "ses_01",
    conversation_id: "conv_01",
    run_id: "run_01",
    cursor: "1748428800-000012",
    timestamp: "2026-05-28T12:00:00.000Z",
    payload: { message_id: "msg_01", delta: "Hello ", role: "assistant" },
  }),
  parseSessionEvent({
    event: "message.completed",
    event_id: "evt_02",
    session_id: "ses_01",
    conversation_id: "conv_01",
    run_id: "run_01",
    cursor: "1748428800-000013",
    timestamp: "2026-05-28T12:00:01.000Z",
    payload: { message_id: "msg_01", role: "assistant", content: "Hello from replay-safe shell." },
  }),
  parseSessionEvent({
    event: "run.completed",
    event_id: "evt_03",
    session_id: "ses_01",
    conversation_id: "conv_01",
    run_id: "run_01",
    cursor: "1748428800-000014",
    timestamp: "2026-05-28T12:00:02.000Z",
    payload: { run_id: "run_01", status: "completed" },
  }),
]
```

```tsx
import { applySessionEvent, createSessionStreamState } from "@/application/session-stream-reducer"
import { seedEvents } from "@/interfaces/session-stream/seed-events"

export function SessionShell() {
  const state = seedEvents.reduce(applySessionEvent, createSessionStreamState())

  return (
    <main className="min-h-screen bg-stone-50 px-6 py-10 text-stone-900">
      <div className="mx-auto flex max-w-4xl flex-col gap-6">
        <header className="space-y-2">
          <p className="text-sm uppercase tracking-[0.24em] text-stone-500">Kokoro</p>
          <h1 className="text-3xl font-semibold">Kokoro / session stream preview</h1>
          <p className="text-sm text-stone-600">Protocol-first shell for AGUI + SSE integration.</p>
        </header>

        <section className="rounded-2xl border border-stone-200 bg-white p-5 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <span className="text-sm text-stone-500">run status</span>
            <span className="rounded-full bg-stone-100 px-3 py-1 text-sm text-stone-700">{state.runStatus}</span>
          </div>

          <div className="space-y-3">
            {state.messages.map((message) => (
              <article key={message.id} className="rounded-xl bg-stone-50 p-4">
                <p className="mb-2 text-xs uppercase tracking-[0.2em] text-stone-400">{message.role}</p>
                <p className="text-sm leading-7 text-stone-700">{message.content}</p>
              </article>
            ))}
          </div>
        </section>
      </div>
    </main>
  )
}
```

```tsx
import { SessionShell } from "@/interfaces/session-stream/session-shell"

export default function Home() {
  return <SessionShell />
}
```

- [ ] **Step 4: Re-run the UI test and verify GREEN**

Run: `cd kokoro-web && bun vitest run src/interfaces/session-stream/session-shell.test.tsx`
Expected: PASS with 1 test passed.

- [ ] **Step 5: Commit the shell slice**

```bash
cd kokoro-web && git add src/app/page.tsx src/interfaces/session-stream src/interfaces/session-stream/session-shell.test.tsx && git commit -m "feat(interfaces): add minimal session shell"
```

### Task 7: Full verification and handoff

**Files:**
- Modify: `claude-progress.md`
- Modify: `tasks/todo.md`

- [ ] **Step 1: Run the complete test suite**

Run: `cd kokoro-web && bun run test`
Expected: all tests pass, 0 failures.

- [ ] **Step 2: Run lint and typecheck**

Run: `cd kokoro-web && bun run lint && bun run typecheck`
Expected: both commands exit 0 with no warnings or errors.

- [ ] **Step 3: Update the handoff files with actual results**

```markdown
# Claude Progress

- Date: 2026-05-29
- Active stream: kokoro-web bootstrap
- Completed:
  - Created independent kokoro-web repository
  - Added strict protocol schemas and replay reducer
  - Added minimal session shell
  - Verified test, lint, and typecheck
- Remaining:
  - Real SSE transport integration
  - Real A2UI artifact rendering
- Next recommended slice:
  - Add `EventSource` adapter in `src/infrastructure/transport/`
```
```

```markdown
# Todo

- [x] Create `kokoro-web/` as an independent Git repository.
- [x] Scaffold Bun + Next.js + Tailwind + shadcn/ui baseline.
- [x] Add DDD folders and dependency boundaries.
- [x] Add strict protocol schemas with failing tests first.
- [x] Add replay reducer with failing tests first.
- [x] Render the minimal chat shell using seed events.
- [x] Run test, lint, and typecheck.
```

- [ ] **Step 4: Commit the final handoff updates in the parent repo**

```bash
git add claude-progress.md tasks/todo.md
git commit -m "docs(progress): record kokoro-web bootstrap handoff"
```
