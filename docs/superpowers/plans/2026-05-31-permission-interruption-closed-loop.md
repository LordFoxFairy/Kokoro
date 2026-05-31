# Permission Interruption Closed Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在不接 `kokoro-agent` 真实权限事件、也不放开真实危险工具的前提下，把 `permission.required` 做成一条完整闭环：session 能产出并 replay ask/resolved 生命周期，web 能在线程里渲染 `PermissionCard` 并提交 `allow once` / `allow for session` / `deny` 决策。

**Architecture:** 这轮继续沿用已经验证过的 harness seam：`kokoro-session` 负责**会话语义**（synthetic permission fixture、decision endpoint、SessionEvent、A2UI projector），`kokoro-web` 负责**纯渲染 + 决策提交**，`kokoro-agent` 保持不动。权限卡片是 timeline 里的 A2UI 组件，不是 composer 邻近 banner；同一 `request_id` 的 ask → resolved 通过同一个 data-model path 原地收敛，刷新后靠 replay 自然恢复。

**Tech Stack:** TypeScript / Bun / Zod / Node HTTP（kokoro-session）；Next.js 16 / React 19 / `@a2ui/react` / `@a2ui/web_core` / Vitest / Testing Library（kokoro-web）；Playwright（离线浏览器验证）；Markdown protocol docs（父仓）。

**Repo stack:** 这轮不动 `kokoro-agent`。`kokoro-session` 与 `kokoro-web` 都从各自的 `feat/agent-deepagents-planning` 分支再起一层新分支；父仓文档从 `docs/agent-deepagents-planning` 再起一层新分支，保持 stacked PR 干净。

---

## File map (lock this before coding)

### Parent repo (`Kokoro/`)
- Modify: `docs/protocol/session-stream.md` — 统一 `permission.required` 的 canonical shape，补 `PermissionCard` 渲染约定与 decision endpoint
- Modify: `docs/protocol/safety-and-permission-envelope.md` — 统一 `decision` 字段、ask/resolved 示例、受约束 ask-form 定位
- Modify (final bookkeeping): `claude-progress.md` — 记录本轮实现结果与验证命令
- Modify (final bookkeeping): `tasks/todo.md` — 标记 permission slice 完成并推进 deferred items

### `kokoro-session/`
- Create: `src/domain/permissions.ts` — permission payload / decision body 的 Zod schema 与小型 helper（`permissionRequestIdForRun` 等）
- Modify: `src/domain/events.ts` — `SessionEventName` 增加 `permission.required`
- Modify: `src/application/a2ui-projector.ts` — 把 `permission.required` 投影成 `PermissionCard` + `/permissions/{request_id}` data model
- Modify: `src/interfaces/http.ts` — synthetic fixture run、decision endpoint、append helper、validation
- Test: `tests/a2ui-projector.test.ts`
- Test: `tests/http.test.ts`

### `kokoro-web/`
- Modify: `src/application/a2ui-session.ts` — run URL builder（支持 fixture）、decision submit helper
- Modify: `src/interfaces/a2ui/use-a2ui-surface.ts` — 透传 fixture
- Create: `src/interfaces/a2ui/components/permission-card.tsx` — timeline 权限卡片（ask / resolved）
- Modify: `src/interfaces/a2ui/catalog.ts` — 注册 `PermissionCard`
- Modify: `src/app/globals.css` — permission 卡片样式
- Modify: `src/interfaces/chat/chat-page.tsx` — 只在 dev/e2e 时从 URL search 读取 `?fixture=permission`
- Test: `src/application/__tests__/a2ui-session.test.ts`
- Test: `src/interfaces/a2ui/__tests__/permission-card.test.tsx`
- Test: `src/interfaces/chat/__tests__/chat-page.test.tsx`

---

## Branch setup

### Parent repo

- [ ] **Step 1: create docs branch**

Run:

```bash
git checkout docs/agent-deepagents-planning
git checkout -b docs/permission-interruption-closed-loop
```

Expected: branch switches cleanly from the current stacked docs branch.

### `kokoro-session/`

- [ ] **Step 2: create session branch**

Run:

```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-session
git checkout feat/agent-deepagents-planning
git checkout -b feat/permission-interruption-closed-loop
```

Expected: branch switches cleanly from the current stacked session branch.

### `kokoro-web/`

- [ ] **Step 3: create web branch**

Run:

```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-web
git checkout feat/agent-deepagents-planning
git checkout -b feat/permission-interruption-closed-loop
```

Expected: branch switches cleanly from the current stacked web branch.

---

## Task 1: Align protocol docs first

**Files:**
- Modify: `docs/protocol/session-stream.md`
- Modify: `docs/protocol/safety-and-permission-envelope.md`

### `docs/protocol/session-stream.md`
- In the event families section, keep `permission.required`
- Replace `decision_kind` with `decision`
- Add the A2UI catalog contract for `PermissionCard{ sessionId, requestPath:{path} }`
- Add the session decision endpoint contract: `POST /sessions/{session_id}/permissions/{request_id}/decision`
- Explicitly say `PermissionCard` is a **specialized ask card / constrained decision form**, not a generic free-text query

### `docs/protocol/safety-and-permission-envelope.md`
- Keep `decision: "ask" | "allow" | "deny"`
- Keep `scope: "once" | "session"` for allow decisions
- Add one ask example and two resolved examples
- Add one sentence that this envelope is rendered as a timeline card, not a global banner, in the current Kokoro shell

- [ ] **Step 1: edit `docs/protocol/session-stream.md`**

Insert / rewrite the permission section to this shape:

```md
### `permission.required`
- **Purpose:** 当前 run 因权限或安全中断而挂起，等待用户决策
- **Required fields:** `request_id`, `decision`, `message`
- **Optional fields:** `scope`, `options`, `kind`
- **Producer repo:** `kokoro-session`
- **Consumer repo:** `kokoro-web`
- **Replay behavior:** 必须 replay；刷新后仍能复原 ask / resolved 卡片

Ask payload example:
```json
{
  "request_id": "perm_run_01",
  "decision": "ask",
  "scope": "session",
  "message": "我想访问这个外部资源，可以吗？",
  "options": ["once", "session", "deny"],
  "kind": "permission"
}
```
```

- [ ] **Step 2: edit `docs/protocol/safety-and-permission-envelope.md`**

Make the canonical examples look like:

```md
### `ask`
```json
{
  "decision": "ask",
  "request_id": "perm_run_01",
  "scope": "session",
  "message": "我想访问这个外部资源，可以吗？",
  "options": ["once", "session", "deny"]
}
```

### `allow`
```json
{
  "decision": "allow",
  "scope": "once",
  "message": "这一步已经允许继续了。"
}
```

### `deny`
```json
{
  "decision": "deny",
  "message": "这一步未被允许继续。"
}
```
```

- [ ] **Step 3: verify there is no stale `decision_kind` left**

Run:

```bash
rg -n "decision_kind|PermissionCard|permission.required" docs/protocol/session-stream.md docs/protocol/safety-and-permission-envelope.md
```

Expected:
- `decision_kind` no longer appears
- `permission.required` and `PermissionCard` both appear in the updated docs

- [ ] **Step 4: commit docs alignment**

```bash
git add docs/protocol/session-stream.md docs/protocol/safety-and-permission-envelope.md
git commit -m "docs(protocol): align permission interruption contract"
```

---

## Task 2: Add session-side permission event shape and A2UI projection

**Files:**
- Create: `kokoro-session/src/domain/permissions.ts`
- Modify: `kokoro-session/src/domain/events.ts`
- Modify: `kokoro-session/src/application/a2ui-projector.ts`
- Test: `kokoro-session/tests/a2ui-projector.test.ts`

- [ ] **Step 1: write the failing projector tests**

Append these tests to `kokoro-session/tests/a2ui-projector.test.ts`:

```ts
it("projects permission.required ask into a PermissionCard mounted once + dataModel", () => {
  const p = new A2uiProjector("ses_1")
  p.project(ev("run.created", { run_id: "run_1" }, 1))
  const ops = p.project(ev("permission.required", {
    request_id: "perm_run_1",
    decision: "ask",
    scope: "session",
    message: "我想访问这个外部资源，可以吗？",
    options: ["once", "session", "deny"],
    kind: "permission",
  }, 2))

  expect(ops[0]).toEqual({
    version: "v0.9",
    updateComponents: {
      surfaceId: "ses_1",
      components: [{
        id: "perm_run_1",
        component: "PermissionCard",
        sessionId: "ses_1",
        requestPath: { path: "/permissions/perm_run_1" },
      }],
    },
  })
  expect(ops[1]).toEqual({
    version: "v0.9",
    updateDataModel: {
      surfaceId: "ses_1",
      path: "/permissions/perm_run_1",
      value: {
        requestId: "perm_run_1",
        decision: "ask",
        scope: "session",
        message: "我想访问这个外部资源，可以吗？",
        options: ["once", "session", "deny"],
        kind: "permission",
      },
    },
  })
  expect(ops[2]).toEqual({
    version: "v0.9",
    updateComponents: {
      surfaceId: "ses_1",
      components: [{ id: "root", component: "Thread", children: ["perm_run_1"] }],
    },
  })
})

it("updates an existing permission card in place when ask resolves", () => {
  const p = new A2uiProjector("ses_1")
  p.project(ev("run.created", { run_id: "run_1" }, 1))
  p.project(ev("permission.required", {
    request_id: "perm_run_1",
    decision: "ask",
    scope: "session",
    message: "我想访问这个外部资源，可以吗？",
    options: ["once", "session", "deny"],
    kind: "permission",
  }, 2))

  const ops = p.project(ev("permission.required", {
    request_id: "perm_run_1",
    decision: "allow",
    scope: "once",
    message: "这一步已经允许继续了。",
    kind: "permission",
  }, 3))

  expect(ops).toEqual([{ 
    version: "v0.9",
    updateDataModel: {
      surfaceId: "ses_1",
      path: "/permissions/perm_run_1",
      value: {
        requestId: "perm_run_1",
        decision: "allow",
        scope: "once",
        message: "这一步已经允许继续了。",
        kind: "permission",
      },
    },
  }])
})
```

- [ ] **Step 2: run the focused session test and confirm it fails**

Run:

```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-session
bun test tests/a2ui-projector.test.ts
```

Expected: FAIL because `permission.required` is still unsupported and `PermissionCard` is unknown to the projector.

- [ ] **Step 3: create `src/domain/permissions.ts`**

Write this file:

```ts
import { z } from "zod"

export const permissionDecisionSchema = z.enum(["ask", "allow", "deny"])
export const permissionScopeSchema = z.enum(["once", "session"])
export const permissionKindSchema = z.enum(["permission", "circuit_breaker"])
export const permissionOptionSchema = z.enum(["once", "session", "deny"])

export const permissionRequiredPayloadSchema = z.object({
  request_id: z.string().min(1),
  decision: permissionDecisionSchema,
  scope: z.string().min(1).optional(),
  message: z.string().min(1),
  options: z.array(permissionOptionSchema).optional(),
  kind: permissionKindSchema.optional(),
}).strict()

export const permissionDecisionBodySchema = z.discriminatedUnion("decision", [
  z.object({ decision: z.literal("allow"), scope: permissionScopeSchema }).strict(),
  z.object({ decision: z.literal("deny") }).strict(),
])

export type PermissionRequiredPayload = z.infer<typeof permissionRequiredPayloadSchema>
export type PermissionDecisionBody = z.infer<typeof permissionDecisionBodySchema>

export function permissionRequestIdForRun(runId: string): string {
  return `perm_${runId}`
}
```

- [ ] **Step 4: add `permission.required` to `src/domain/events.ts`**

Change the event name list to:

```ts
const sessionEventNames = [
  "session.created",
  "run.created",
  "message.delta",
  "message.completed",
  "thinking.summary",
  "tool.started",
  "tool.completed",
  "plan.updated",
  "permission.required",
  "run.completed",
  "run.failed",
] as const
```

- [ ] **Step 5: implement the projector case in `src/application/a2ui-projector.ts`**

Add a mounted set near the existing fields:

```ts
private readonly mountedPermissions = new Set<string>()
```

Add this switch case:

```ts
case "permission.required": {
  const requestId = String(event.payload.request_id)
  const path = `/permissions/${requestId}`
  const value = {
    requestId,
    decision: String(event.payload.decision ?? "ask"),
    scope: typeof event.payload.scope === "string" ? event.payload.scope : undefined,
    message: String(event.payload.message ?? ""),
    options: Array.isArray(event.payload.options) ? event.payload.options : undefined,
    kind: typeof event.payload.kind === "string" ? event.payload.kind : "permission",
  }

  if (!this.mountedPermissions.has(requestId)) {
    this.mountedPermissions.add(requestId)
    this.children.push(requestId)
    return [
      this.mountComponent(requestId, "PermissionCard", {
        sessionId: this.surfaceId,
        requestPath: { path },
      }),
      this.setData(path, value),
      this.rootOp(),
    ]
  }

  return [this.setData(path, value)]
}
```

- [ ] **Step 6: run the focused test again**

Run:

```bash
bun test tests/a2ui-projector.test.ts
```

Expected: PASS.

- [ ] **Step 7: commit the session projector layer**

```bash
git add src/domain/permissions.ts src/domain/events.ts src/application/a2ui-projector.ts tests/a2ui-projector.test.ts
git commit -m "feat(session): project permission.required into A2UI PermissionCard"
```

---

## Task 3: Add the synthetic fixture run and decision endpoint to `kokoro-session`

**Files:**
- Modify: `kokoro-session/src/interfaces/http.ts`
- Test: `kokoro-session/tests/http.test.ts`

- [ ] **Step 1: write failing HTTP tests**

Append these tests to `kokoro-session/tests/http.test.ts`:

```ts
test("permission fixture run replays a PermissionCard over SSE", async () => {
  const deps = makeDeps()
  await listen(deps)

  const res = await fetch(`${baseUrl}/sessions/ses_perm/runs?input=hello&fixture=permission`, {
    method: "POST",
  })
  const body = await res.json() as { runId: string }
  expect(body.runId).toMatch(/^run_/)

  const stream = await fetch(`${baseUrl}/sessions/ses_perm/stream`, {
    headers: { accept: "text/event-stream" },
    signal: AbortSignal.timeout(3000),
  })
  const text = await readUntil(stream, "PermissionCard")
  expect(text).toContain("event: a2ui.op")
  expect(text).toContain("PermissionCard")
  expect(text).toContain("我想访问这个外部资源，可以吗？")
})

test("permission decision endpoint resolves the existing card in place", async () => {
  const deps = makeDeps()
  await listen(deps)

  const start = await fetch(`${baseUrl}/sessions/ses_perm/runs?input=hello&fixture=permission`, {
    method: "POST",
  })
  const { runId } = await start.json() as { runId: string }
  const requestId = `perm_${runId}`

  const stream = await fetch(`${baseUrl}/sessions/ses_perm/stream`, {
    headers: { accept: "text/event-stream" },
    signal: AbortSignal.timeout(5000),
  })
  const reading = readUntil(stream, "这一步已经允许继续了。")

  const decision = await fetch(`${baseUrl}/sessions/ses_perm/permissions/${requestId}/decision`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ decision: "allow", scope: "once" }),
  })

  expect(decision.status).toBe(200)
  const live = await reading
  expect(live).toContain("这一步已经允许继续了。")
  expect(live).toContain("updateDataModel")
})
```

- [ ] **Step 2: run the focused HTTP test file and confirm failure**

Run:

```bash
bun test tests/http.test.ts
```

Expected: FAIL because `fixture=permission` and `/permissions/:requestId/decision` do not exist yet.

- [ ] **Step 3: extend `BuildServerDependencies` in `src/interfaces/http.ts` with a tiny clock**

Change the dependency type to:

```ts
export type BuildServerDependencies = {
  streamPort: StreamPort
  replayStore: ReplayStore
  newEventId?: () => string
  now?: () => Date
}
```

Inside `handle`, normalize the clock once:

```ts
const newEventId = dependencies.newEventId ?? (() => crypto.randomUUID())
const now = dependencies.now ?? (() => new Date())
```

- [ ] **Step 4: add fixture detection to `POST /sessions/:id/runs`**

Right before the existing `startRun(...)` call, branch on `fixture`:

```ts
const fixture = requestUrl.searchParams.get("fixture")
if (fixture === "permission") {
  const runId = `run_${Math.random().toString(36).slice(2, 10)}`
  await appendPermissionFixture({
    sessionId,
    conversationId: requestUrl.searchParams.get("conversation_id") ?? sessionId,
    runId,
    replayStore: dependencies.replayStore,
    newEventId,
    now,
  })
  res.statusCode = 200
  res.setHeader("content-type", "application/json")
  res.end(JSON.stringify({ runId }))
  return
}
```

Then add the helper below `streamSession`:

```ts
async function appendPermissionFixture(opts: {
  sessionId: string
  conversationId: string
  runId: string
  replayStore: ReplayStore
  newEventId: () => string
  now: () => Date
}): Promise<void> {
  const requestId = permissionRequestIdForRun(opts.runId)
  const stamp = opts.now().toISOString()
  await opts.replayStore.append(opts.sessionId, [
    {
      event: "session.created",
      event_id: opts.newEventId(),
      session_id: opts.sessionId,
      conversation_id: opts.conversationId,
      run_id: opts.runId,
      cursor: `${opts.runId}:0001`,
      timestamp: stamp,
      payload: {
        session_id: opts.sessionId,
        conversation_id: opts.conversationId,
        owner_id: "kokoro-session",
      },
    },
    {
      event: "run.created",
      event_id: opts.newEventId(),
      session_id: opts.sessionId,
      conversation_id: opts.conversationId,
      run_id: opts.runId,
      cursor: `${opts.runId}:0002`,
      timestamp: stamp,
      payload: { run_id: opts.runId },
    },
    {
      event: "permission.required",
      event_id: opts.newEventId(),
      session_id: opts.sessionId,
      conversation_id: opts.conversationId,
      run_id: opts.runId,
      cursor: `${opts.runId}:0003`,
      timestamp: stamp,
      payload: {
        request_id: requestId,
        decision: "ask",
        scope: "session",
        message: "我想访问这个外部资源，可以吗？",
        options: ["once", "session", "deny"],
        kind: "permission",
      },
    },
  ])
}
```

- [ ] **Step 5: add the decision endpoint in `src/interfaces/http.ts`**

Add this route before the final 404:

```ts
if (
  req.method === "POST" &&
  sessionId &&
  requestUrl.pathname === `/sessions/${sessionId}/permissions/${requestUrl.pathname.split("/").filter(Boolean)[3]}/decision`
) {
  await decidePermission(req, res, dependencies, sessionId, requestUrl.pathname.split("/").filter(Boolean)[3]!)
  return
}
```

Implement `decidePermission(...)` as:

```ts
async function decidePermission(
  req: IncomingMessage,
  res: ServerResponse,
  dependencies: BuildServerDependencies,
  sessionId: string,
  requestId: string,
): Promise<void> {
  const raw = await readJson(req)
  const body = permissionDecisionBodySchema.parse(raw)
  const runId = requestId.replace(/^perm_/, "")
  const snapshot = await dependencies.streamPort.readAll(replayStream(sessionId))
  const current = snapshot
    .map((item) => parseSessionEvent(item.event))
    .filter((event) => event.event === "permission.required" && event.payload.request_id === requestId)
    .at(-1)

  if (!current) {
    res.statusCode = 404
    res.end("unknown permission request")
    return
  }

  if (current.payload.decision !== "ask") {
    res.statusCode = 200
    res.setHeader("content-type", "application/json")
    res.end(JSON.stringify(current.payload))
    return
  }

  const nextSeq = snapshot
    .map((item) => parseSessionEvent(item.event))
    .filter((event) => event.run_id === runId)
    .map((event) => Number(event.cursor.split(":").at(-1)))
    .reduce((max, n) => Math.max(max, Number.isFinite(n) ? n : 0), 0) + 1

  const resolved = {
    request_id: requestId,
    decision: body.decision,
    ...(body.decision === "allow" ? { scope: body.scope } : {}),
    message: body.decision === "allow"
      ? body.scope === "session"
        ? "本会话内同类动作已允许继续。"
        : "这一步已经允许继续了。"
      : "这一步未被允许继续。",
    kind: current.payload.kind ?? "permission",
  }

  await dependencies.replayStore.append(sessionId, [{
    event: "permission.required",
    event_id: (dependencies.newEventId ?? (() => crypto.randomUUID()))(),
    session_id: sessionId,
    conversation_id: current.conversation_id,
    run_id: runId,
    cursor: `${runId}:${String(nextSeq).padStart(4, "0")}`,
    timestamp: (dependencies.now ?? (() => new Date()))().toISOString(),
    payload: resolved,
  }])

  res.statusCode = 200
  res.setHeader("content-type", "application/json")
  res.end(JSON.stringify(resolved))
}
```

Also add the JSON reader helper:

```ts
async function readJson(req: IncomingMessage): Promise<unknown> {
  const chunks: Uint8Array[] = []
  for await (const chunk of req) chunks.push(typeof chunk === "string" ? Buffer.from(chunk) : chunk)
  const text = Buffer.concat(chunks).toString("utf8")
  return text ? JSON.parse(text) : {}
}
```

- [ ] **Step 6: make the HTTP tests deterministic**

In `makeDeps()` inside `tests/http.test.ts`, pass deterministic clocks into `buildServer(...)`:

```ts
function makeDeps() {
  const streamPort = new MemoryStreamPort()
  const replayStore = makeReplayStore(streamPort)
  let n = 0
  return {
    streamPort,
    replayStore,
    newEventId: () => `evt_${++n}`,
    now: () => new Date("2026-05-31T00:00:00.000Z"),
  }
}
```

- [ ] **Step 7: run the focused test file again**

Run:

```bash
bun test tests/http.test.ts
```

Expected: PASS.

- [ ] **Step 8: run the full session green gate**

Run:

```bash
bunx tsc --noEmit
bunx eslint .
bun test
```

Expected: all three commands PASS.

- [ ] **Step 9: commit the HTTP surface**

```bash
git add src/interfaces/http.ts tests/http.test.ts
git commit -m "feat(session): add synthetic permission fixture and decision endpoint"
```

---

## Task 4: Add the web-side session helpers and `PermissionCard`

**Files:**
- Modify: `kokoro-web/src/application/a2ui-session.ts`
- Create: `kokoro-web/src/interfaces/a2ui/components/permission-card.tsx`
- Modify: `kokoro-web/src/interfaces/a2ui/catalog.ts`
- Modify: `kokoro-web/src/app/globals.css`
- Test: `kokoro-web/src/application/__tests__/a2ui-session.test.ts`
- Test: `kokoro-web/src/interfaces/a2ui/__tests__/permission-card.test.tsx`

- [ ] **Step 1: write the failing session-helper tests**

Replace / extend `kokoro-web/src/application/__tests__/a2ui-session.test.ts` with:

```ts
import { afterEach, describe, expect, it, vi } from "vitest"
import { MessageProcessor } from "@a2ui/web_core/v0_9"
import { kokoroChatCatalog } from "@/interfaces/a2ui/catalog"
import { buildRunUrl, feedA2uiLine, submitPermissionDecision } from "../a2ui-session"

afterEach(() => {
  vi.restoreAllMocks()
})

describe("buildRunUrl", () => {
  it("adds the optional permission fixture query param", () => {
    const url = buildRunUrl({
      baseUrl: "http://127.0.0.1:3001",
      sessionId: "ses_1",
      conversationId: "ses_1",
      input: "hello",
      fixture: "permission",
    })
    expect(url).toContain("/sessions/ses_1/runs")
    expect(url).toContain("fixture=permission")
  })
})

describe("feedA2uiLine", () => {
  it("parses a JSON op line and feeds the processor incrementally", () => {
    const processor = new MessageProcessor([kokoroChatCatalog])
    feedA2uiLine(processor, JSON.stringify({ version: "v0.9", createSurface: { surfaceId: "s", catalogId: "kokoro/chat/v1" } }))
    feedA2uiLine(processor, JSON.stringify({ version: "v0.9", updateComponents: { surfaceId: "s", components: [{ id: "root", component: "Thread", children: [] }] } }))
    expect(processor.model.getSurface("s")).toBeTruthy()
  })
})

describe("submitPermissionDecision", () => {
  it("posts the resolved decision body to kokoro-session", async () => {
    const fetchMock = vi.fn(async () => new Response("{}", { status: 200 }))
    vi.stubGlobal("fetch", fetchMock)

    await submitPermissionDecision({
      baseUrl: "http://127.0.0.1:3001",
      sessionId: "ses_1",
      requestId: "perm_run_1",
      decision: { decision: "allow", scope: "once" },
    })

    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:3001/sessions/ses_1/permissions/perm_run_1/decision",
      expect.objectContaining({ method: "POST" }),
    )
  })
})
```

- [ ] **Step 2: run the helper test file and confirm failure**

Run:

```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-web
bun run test src/application/__tests__/a2ui-session.test.ts
```

Expected: FAIL because `buildRunUrl` and `submitPermissionDecision` do not exist yet.

- [ ] **Step 3: implement the helper functions in `src/application/a2ui-session.ts`**

Refactor the file to expose:

```ts
export function buildRunUrl(opts: {
  baseUrl: string
  sessionId: string
  conversationId: string
  input: string
  fixture?: "permission"
}): string {
  const runUrl = new URL(`/sessions/${opts.sessionId}/runs`, opts.baseUrl)
  runUrl.searchParams.set("conversation_id", opts.conversationId)
  runUrl.searchParams.set("input", opts.input)
  runUrl.searchParams.set("execution_style", "thinking")
  if (opts.fixture) runUrl.searchParams.set("fixture", opts.fixture)
  return runUrl.toString()
}

export async function submitPermissionDecision(opts: {
  sessionId: string
  requestId: string
  decision:
    | { decision: "allow"; scope: "once" | "session" }
    | { decision: "deny" }
  baseUrl?: string
}): Promise<void> {
  const baseUrl = opts.baseUrl ?? resolveSessionBaseUrl()
  const res = await fetch(
    `${baseUrl}/sessions/${opts.sessionId}/permissions/${opts.requestId}/decision`,
    {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(opts.decision),
    },
  )
  if (!res.ok) throw new Error(`permission decision failed: ${res.status}`)
}
```

Then make `startA2uiSession(...)` use `buildRunUrl(...)`:

```ts
const runUrl = buildRunUrl({
  baseUrl,
  sessionId: opts.sessionId,
  conversationId,
  input: opts.input,
  fixture: opts.fixture,
})
```

- [ ] **Step 4: write the failing component test**

Create `kokoro-web/src/interfaces/a2ui/__tests__/permission-card.test.tsx`:

```tsx
import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import { describe, expect, it, vi, afterEach } from "vitest"
import { A2uiSurface } from "@a2ui/react/v0_9"
import { MessageProcessor, type A2uiMessage } from "@a2ui/web_core/v0_9"
import { kokoroChatCatalog } from "../catalog"

afterEach(() => {
  vi.restoreAllMocks()
})

describe("PermissionCard (kokoro/chat/v1)", () => {
  it("renders ask actions and posts allow-once", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response("{}", { status: 200 })))

    const processor = new MessageProcessor([kokoroChatCatalog])
    processor.processMessages([
      { version: "v0.9", createSurface: { surfaceId: "s", catalogId: "kokoro/chat/v1" } },
      { version: "v0.9", updateComponents: { surfaceId: "s", components: [
        { id: "root", component: "Thread", children: ["perm_run_1"] },
        { id: "perm_run_1", component: "PermissionCard", sessionId: "s", requestPath: { path: "/permissions/perm_run_1" } },
      ] } },
      { version: "v0.9", updateDataModel: { surfaceId: "s", path: "/permissions/perm_run_1", value: {
        requestId: "perm_run_1",
        decision: "ask",
        scope: "session",
        message: "我想访问这个外部资源，可以吗？",
        options: ["once", "session", "deny"],
        kind: "permission",
      } } },
    ] as A2uiMessage[])

    render(<A2uiSurface surface={processor.model.getSurface("s")!} />)
    fireEvent.click(screen.getByRole("button", { name: "Allow once" }))

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledTimes(1)
    })
  })

  it("renders a resolved card without action buttons", () => {
    const processor = new MessageProcessor([kokoroChatCatalog])
    processor.processMessages([
      { version: "v0.9", createSurface: { surfaceId: "s", catalogId: "kokoro/chat/v1" } },
      { version: "v0.9", updateComponents: { surfaceId: "s", components: [
        { id: "root", component: "Thread", children: ["perm_run_1"] },
        { id: "perm_run_1", component: "PermissionCard", sessionId: "s", requestPath: { path: "/permissions/perm_run_1" } },
      ] } },
      { version: "v0.9", updateDataModel: { surfaceId: "s", path: "/permissions/perm_run_1", value: {
        requestId: "perm_run_1",
        decision: "allow",
        scope: "once",
        message: "这一步已经允许继续了。",
        kind: "permission",
      } } },
    ] as A2uiMessage[])

    render(<A2uiSurface surface={processor.model.getSurface("s")!} />)
    expect(screen.getByText("这一步已经允许继续了。"))
      .toBeInTheDocument()
    expect(screen.queryByRole("button", { name: "Allow once" })).toBeNull()
    expect(screen.queryByRole("button", { name: "Deny" })).toBeNull()
  })
})
```

- [ ] **Step 5: run the component test and confirm failure**

Run:

```bash
bun run test src/interfaces/a2ui/__tests__/permission-card.test.tsx
```

Expected: FAIL because `PermissionCard` is not registered and the component file does not exist yet.

- [ ] **Step 6: create `src/interfaces/a2ui/components/permission-card.tsx`**

Write this file:

```tsx
import { useState } from "react"
import { z } from "zod"
import { createComponentImplementation } from "@a2ui/react/v0_9"
import { DynamicValueSchema } from "@a2ui/web_core/v0_9"
import { submitPermissionDecision } from "@/application/a2ui-session"

const permissionCardSchema = z.object({
  sessionId: z.string(),
  requestPath: DynamicValueSchema,
})

type PermissionRecord = {
  requestId: string
  decision: "ask" | "allow" | "deny"
  scope?: "once" | "session"
  message: string
  options?: string[]
  kind?: "permission" | "circuit_breaker"
}

function readRecord(value: unknown): PermissionRecord | null {
  if (typeof value !== "object" || value === null || Array.isArray(value)) return null
  const record = value as Record<string, unknown>
  if (typeof record.requestId !== "string") return null
  if (typeof record.decision !== "string") return null
  if (typeof record.message !== "string") return null
  return {
    requestId: record.requestId as PermissionRecord["requestId"],
    decision: record.decision as PermissionRecord["decision"],
    scope: typeof record.scope === "string" ? (record.scope as PermissionRecord["scope"]) : undefined,
    message: record.message as string,
    options: Array.isArray(record.options) ? record.options.filter((x): x is string => typeof x === "string") : undefined,
    kind: record.kind === "circuit_breaker" ? "circuit_breaker" : "permission",
  }
}

function PermissionRender({ props }: { props: z.infer<typeof permissionCardSchema> & { requestPath: unknown } }) {
  const request = readRecord(props.requestPath)
  const [submitting, setSubmitting] = useState<null | "once" | "session" | "deny">(null)
  const [error, setError] = useState<string | null>(null)

  if (!request) return null
  const ask = request.decision === "ask"

  const decide = async (decision: { decision: "allow"; scope: "once" | "session" } | { decision: "deny" }, key: "once" | "session" | "deny") => {
    setSubmitting(key)
    setError(null)
    try {
      await submitPermissionDecision({
        sessionId: props.sessionId,
        requestId: request.requestId,
        decision,
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : "permission decision failed")
    } finally {
      setSubmitting(null)
    }
  }

  return (
    <div className="kk-permission" data-testid="kk-permission" data-kind={request.kind} data-decision={request.decision}>
      <p className="kk-permission__title">需要你的确认</p>
      <p className="kk-permission__message">{request.message}</p>
      {ask ? (
        <div className="kk-permission__actions">
          <button type="button" onClick={() => decide({ decision: "allow", scope: "once" }, "once")} disabled={submitting !== null}>Allow once</button>
          <button type="button" onClick={() => decide({ decision: "allow", scope: "session" }, "session")} disabled={submitting !== null}>Allow for session</button>
          <button type="button" onClick={() => decide({ decision: "deny" }, "deny")} disabled={submitting !== null}>Deny</button>
        </div>
      ) : (
        <p className="kk-permission__resolved">{request.message}</p>
      )}
      {error ? <p className="kk-permission__error">{error}</p> : null}
    </div>
  )
}

export const permissionCardComponent = createComponentImplementation(
  { name: "PermissionCard", schema: permissionCardSchema },
  PermissionRender,
)
```

- [ ] **Step 7: register the component and add styles**

In `src/interfaces/a2ui/catalog.ts`, add the import and register it:

```ts
import { permissionCardComponent } from "./components/permission-card"

export const kokoroChatCatalog = new Catalog(KOKORO_CHAT_CATALOG_ID, [
  threadComponent,
  messageComponent,
  thinkingBlockComponent,
  toolCardComponent,
  planComponent,
  permissionCardComponent,
])
```

Append these styles to `src/app/globals.css`:

```css
.kk-permission {
  border: 1px solid var(--border-soft);
  border-radius: var(--radius-soft);
  background: var(--surface-soft);
  padding: 0.875rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.kk-permission[data-kind="circuit_breaker"] {
  border-color: var(--brand-wood);
  box-shadow: 0 10px 24px rgba(139, 111, 71, 0.10);
}

.kk-permission__title {
  font-size: 0.8125rem;
  color: var(--brand-wood);
  font-weight: 600;
}

.kk-permission__message,
.kk-permission__resolved,
.kk-permission__error {
  margin: 0;
  font-size: 0.9rem;
  line-height: 1.6;
}

.kk-permission__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.kk-permission__actions button {
  border: 1px solid var(--border-soft);
  background: var(--surface);
  color: var(--foreground);
  border-radius: 999px;
  padding: 0.375rem 0.75rem;
  cursor: pointer;
}

.kk-permission__actions button:disabled {
  opacity: 0.6;
  cursor: wait;
}

.kk-permission__error {
  color: #a34a2a;
}
```

- [ ] **Step 8: run the focused web tests again**

Run:

```bash
bun run test src/application/__tests__/a2ui-session.test.ts src/interfaces/a2ui/__tests__/permission-card.test.tsx
```

Expected: PASS.

- [ ] **Step 9: commit the web helper/component layer**

```bash
git add src/application/a2ui-session.ts src/application/__tests__/a2ui-session.test.ts src/interfaces/a2ui/components/permission-card.tsx src/interfaces/a2ui/catalog.ts src/interfaces/a2ui/__tests__/permission-card.test.tsx src/app/globals.css
git commit -m "feat(web): add PermissionCard and permission decision helpers"
```

---

## Task 5: Thread the synthetic fixture through the main chat shell and run browser e2e

**Files:**
- Modify: `kokoro-web/src/interfaces/a2ui/use-a2ui-surface.ts`
- Modify: `kokoro-web/src/interfaces/chat/chat-page.tsx`
- Test: `kokoro-web/src/interfaces/chat/__tests__/chat-page.test.tsx`

- [ ] **Step 1: write the failing chat-page test**

Append this test to `kokoro-web/src/interfaces/chat/__tests__/chat-page.test.tsx`:

```tsx
import { readPermissionFixture } from "../chat-page"

it("reads only the supported permission fixture from location search", () => {
  expect(readPermissionFixture("?fixture=permission")).toBe("permission")
  expect(readPermissionFixture("?fixture=nope")).toBeUndefined()
  expect(readPermissionFixture("")).toBeUndefined()
})
```

- [ ] **Step 2: run the focused chat-page test and confirm failure**

Run:

```bash
bun run test src/interfaces/chat/__tests__/chat-page.test.tsx
```

Expected: FAIL because `readPermissionFixture` does not exist yet.

- [ ] **Step 3: implement the fixture passthrough in `src/interfaces/chat/chat-page.tsx`**

Change the run state and add the helper:

```tsx
export function readPermissionFixture(search: string): "permission" | undefined {
  const value = new URLSearchParams(search).get("fixture")
  return value === "permission" ? "permission" : undefined
}

export function ChatPage() {
  const [run, setRun] = useState<{ text: string; sessionId: string; fixture?: "permission" } | null>(null)
  const { surface } = useA2uiSurface(run ?? { text: "", sessionId: "", fixture: undefined })

  return (
    <div className="kk-app">
      ...
      <Composer onSend={(text) => setRun({
        text,
        sessionId: makeSessionId(),
        fixture: typeof window !== "undefined"
          ? readPermissionFixture(window.location.search)
          : undefined,
      })} />
    </div>
  )
}
```

- [ ] **Step 4: thread `fixture` through `src/interfaces/a2ui/use-a2ui-surface.ts`**

Update the input type and `startA2uiSession(...)` call:

```ts
export function useA2uiSurface(input: { text: string; sessionId: string; fixture?: "permission" }) {
  ...
  void startA2uiSession({
    processor,
    input: input.text,
    sessionId: input.sessionId,
    fixture: input.fixture,
    onOp: sync,
  })
```

Also extend the `startA2uiSession` opts type in `src/application/a2ui-session.ts`:

```ts
fixture?: "permission"
```

- [ ] **Step 5: rerun the focused chat-page test**

Run:

```bash
bun run test src/interfaces/chat/__tests__/chat-page.test.tsx
```

Expected: PASS.

- [ ] **Step 6: run the full web green gate**

Run:

```bash
bunx tsc --noEmit
bun run lint
bun run test
bun run build
```

Expected: all four commands PASS.

- [ ] **Step 7: run the offline browser e2e on the main chat path**

Start only session + web (agent stays OFF in this synthetic-first slice):

```bash
# terminal 1
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-session
bun run start

# terminal 2
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-web
bun run dev
```

Then use Playwright on:

- URL: `http://127.0.0.1:3000/?fixture=permission`
- In the composer, type any short prompt (for example `需要访问外部资源`) and send it
- Wait for a `PermissionCard` with `需要你的确认`
- Click `Allow once`
- Assert that the same card now shows `这一步已经允许继续了。`
- Capture at least one screenshot
- Confirm browser console has **0 error**

- [ ] **Step 8: commit the main-shell fixture threading**

```bash
git add src/interfaces/a2ui/use-a2ui-surface.ts src/interfaces/chat/chat-page.tsx src/interfaces/chat/__tests__/chat-page.test.tsx
git commit -m "feat(web): thread permission fixture through the main chat shell"
```

---

## Task 6: Final bookkeeping in the parent repo

**Files:**
- Modify: `claude-progress.md`
- Modify: `tasks/todo.md`

- [ ] **Step 1: update `tasks/todo.md`**

Append a new completed section like this after the current `agent DeepAgents + planning` block:

```md
## permission interruption closed loop (2026-05-31) — DONE — plan: docs/superpowers/plans/2026-05-31-permission-interruption-closed-loop.md
- [x] protocol: unified canonical `decision` shape across `session-stream.md` and `safety-and-permission-envelope.md`
- [x] session: synthetic permission fixture + decision endpoint + `permission.required` replay / projector
- [x] web: `PermissionCard` timeline component + decision submit helper + main-shell `?fixture=permission` passthrough
- [x] offline browser e2e: main chat path renders ask card, allows once, card resolves in place, 0 console errors
- [ ] next: real agent/tool permission source (replace synthetic fixture)
```

- [ ] **Step 2: update `claude-progress.md`**

Add a new top section with:

```md
- Date: 2026-05-31
- Active stream: **permission interruption closed loop — DONE (synthetic-first)**. Session now owns the permission lifecycle (`permission.required` ask/resolved + decision endpoint), web renders a thread-local `PermissionCard`, and the main chat path can trigger the offline fixture via `?fixture=permission`. Agent remains untouched this slice.
```

Also note the exact verification commands that passed.

- [ ] **Step 3: verify the parent repo diff is still surgical**

Run:

```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro
git diff -- docs/protocol/session-stream.md docs/protocol/safety-and-permission-envelope.md docs/superpowers/plans/2026-05-31-permission-interruption-closed-loop.md claude-progress.md tasks/todo.md
git status --short
```

Expected:
- only the intended parent-repo files are modified
- no stray temp files or screenshots are tracked

- [ ] **Step 4: commit the parent bookkeeping**

```bash
git add claude-progress.md tasks/todo.md
git commit -m "docs: record permission interruption closed-loop progress"
```

---

## Done criteria

A slice is done only when **all** of the following are true:

1. `docs/protocol/session-stream.md` and `docs/protocol/safety-and-permission-envelope.md` agree on `decision`-based canonical shape
2. `kokoro-session` accepts `fixture=permission`, replays a `PermissionCard`, and accepts `POST /sessions/{session_id}/permissions/{request_id}/decision`
3. `kokoro-web` renders `PermissionCard` in the timeline, submits `allow once` / `allow for session` / `deny`, and removes action buttons after resolve
4. `bunx tsc --noEmit && bunx eslint . && bun test` passes in `kokoro-session`
5. `bunx tsc --noEmit && bun run lint && bun run test && bun run build` passes in `kokoro-web`
6. Browser e2e on `http://127.0.0.1:3000/?fixture=permission` shows ask → allow once → resolved in place, with 0 console errors and at least one screenshot
7. `claude-progress.md` and `tasks/todo.md` are updated for cross-session continuity

---

## Self-review

### Spec coverage
- canonical `decision` field alignment → Task 1
- session-owned replayable permission lifecycle → Tasks 2 and 3
- thread-local `PermissionCard` instead of banner → Tasks 2 and 4
- synthetic-first, no agent changes → Task 3 fixture path + e2e notes in Task 5
- user decisions `allow once` / `allow for session` / `deny` → Task 4 component + Task 3 endpoint
- refresh/replay safety → Task 2 projector + Task 3 SSE / decision tests
- main chat path verification → Task 5

### Placeholder scan
- no `TBD`
- no `implement later`
- every touched file is named explicitly
- every behavioral task has an actual code snippet or exact command

### Type consistency
- session event name is always `permission.required`
- session payload uses snake_case (`request_id`)
- A2UI data model uses camelCase (`requestId`) for web ergonomics
- component prop is always `requestPath`
- resolved decisions are always `allow` with `scope: once|session` or `deny`

### Explicitly deferred
- real `kokoro-agent` permission events
- FS/execute/creation-tool gating
- long-lived permission memory / org policy
- `artifact.available` / three-column canvas work
- SSE mid-stream hardening beyond what already exists
