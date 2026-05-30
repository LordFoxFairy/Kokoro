# Chat Shell × A2UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `kokoro-web` 对话外壳按 `variant-a-mi-mu` 原型重做，改由 **session 产出 A2UI v0_9 operation 流**、**web 用官方 `@a2ui/react`+`@a2ui/web_core` + 自定义 `kokoro/chat/v1` catalog 渲染**；保留实时 SSE，agent 不动，离线可测。

**Architecture:** agent（纯生产，零改）→ StreamPort → session 现有归一化产 AGUI `SessionEvent`（内部表示，不动）→ **新增 `A2uiProjector` 把有序 `SessionEvent` 投影成 A2UI op** → SSE（每行一条 op）→ web `MessageProcessor.processMessages()` 增量喂 → `<A2uiSurface>` 用自定义 catalog（Thread/Message/ThinkingBlock/ToolCard）渲染成"米+木+纸感"对话。

**Tech Stack:** TS / Bun / Zod strict / `bun test`（session）；Next.js 16 / React 19 / `@a2ui/react@0.10.0` / `@a2ui/web_core@0.10.0` / vitest + `@testing-library/react` / Tailwind v4（web）；Playwright（离线截图）。无真实 LLM/key（沿用 `KOKORO_MODEL=scripted`）。

**Contracts:** A2UI v0_9 op 子集（`createSurface`/`updateComponents`/`updateDataModel`）；catalog id `kokoro/chat/v1`；`session-stream.md` 升 v2.0.0（线上格式由 AGUI 信封→A2UI op 流）。Spec：`docs/superpowers/specs/2026-05-30-chat-shell-a2ui-design.md`。

**Conventions:** TDD red→green，每步一动作，频繁 commit，surgical changes，无 `any`（用 `z.infer`），每仓收尾 LSP+lint+test 全绿。

**已锁定事实（来自代码探查）：**
- session 现状：`Normalizer.ingest(raw)→SessionEvent[]`（`src/application/normalize.ts`）；`relayRun` 把归一化结果 append 进 `replayStore`（`src/application/start_run.ts`）；SSE 在 `src/interfaces/http.ts:streamSession` 先读 `readReplaySnapshot` 快照再 `subscribe` 续订，每条 `SessionEvent` 经 `toSseChunk` 发出。`SessionEvent` 定义在 `src/domain/events.ts`，事件名 ∈ {session.created, run.created, message.delta, message.completed, thinking.summary, tool.started, tool.completed, run.completed, run.failed}。
- web 现状：`@a2ui/react@0.10.0`+`@a2ui/web_core@0.10.0` 已装，`src/interfaces/session-stream/artifact-preview.tsx` 已用 `new MessageProcessor([basicCatalog])` + `processor.model.getSurface(id)` + `<A2uiSurface surface={...}/>` 渲染静态 v0_9 surface。`A2uiMessage`（v0_9）形如 `{version:"v0.9", createSurface:{surfaceId,catalogId}}` / `{version:"v0.9", updateComponents:{surfaceId,components:[{id,component,...}]}}` / `{version:"v0.9", updateDataModel:{surfaceId,path,value}}`。绑定属性写 `{ path: "/x" }`（见 artifact-preview 的 `text:{path:"/title"}`）。
- 自定义 catalog API：`new Catalog(id, components[])`（`@a2ui/web_core/v0_9`）；组件实现 `createComponentImplementation(api, RenderComponent)`（`@a2ui/react/v0_9`），`api={name, schema:ZodObject}`；容器用 `buildChild(id)` 渲染子节点。`A2uiSurface` props：`{ surface: SurfaceModel }`，无 components/overrides prop——扩展只经 catalog。**RenderComponent 的精确 props 形状（`ReactA2uiComponentProps`）在 Task B1 用 spike 测试 + 读 .d.ts 锁定，后续组件按锁定签名实现。**

---

## Chunk A — kokoro-session：A2UI op 域 + 投影器 + SSE 接线

Dir `kokoro-session/`。先 `git checkout main && git pull`（若 feat/tools-and-thinking 已并入；否则 `git checkout feat/tools-and-thinking`），再 `git checkout -b feat/chat-shell-a2ui`。测试：`bun test`。LSP：`bunx tsc --noEmit && bunx eslint .`。

### Task A1: A2UI op 域类型 + Zod schema

**Files:**
- Create: `src/domain/a2ui.ts`
- Test: `tests/a2ui.test.ts`

- [ ] **Step 1: 写失败测试** `tests/a2ui.test.ts`

```ts
import { describe, expect, it } from "bun:test"
import { a2uiOpSchema, type A2uiOp } from "../src/domain/a2ui"

describe("a2uiOpSchema", () => {
  it("accepts createSurface", () => {
    const op = { version: "v0.9", createSurface: { surfaceId: "ses_1", catalogId: "kokoro/chat/v1" } }
    expect(a2uiOpSchema.parse(op)).toEqual(op)
  })

  it("accepts updateComponents with passthrough component props", () => {
    const op = {
      version: "v0.9",
      updateComponents: {
        surfaceId: "ses_1",
        components: [{ id: "root", component: "Thread", children: ["m_1"] }],
      },
    }
    expect(a2uiOpSchema.parse(op)).toEqual(op)
  })

  it("accepts updateDataModel", () => {
    const op = { version: "v0.9", updateDataModel: { surfaceId: "ses_1", path: "/messages/m_1", value: "hi" } }
    expect(a2uiOpSchema.parse(op)).toEqual(op)
  })

  it("rejects wrong version", () => {
    expect(() => a2uiOpSchema.parse({ version: "v1", createSurface: { surfaceId: "s", catalogId: "c" } })).toThrow()
  })

  it("rejects component missing id/component", () => {
    expect(() =>
      a2uiOpSchema.parse({ version: "v0.9", updateComponents: { surfaceId: "s", components: [{ id: "x" }] } }),
    ).toThrow()
  })

  it("infers A2uiOp union", () => {
    const op: A2uiOp = { version: "v0.9", updateDataModel: { surfaceId: "s", path: "/a", value: 1 } }
    expect(op.version).toBe("v0.9")
  })
})
```

- [ ] **Step 2: 跑测试确认失败**

Run: `bun test tests/a2ui.test.ts`
Expected: FAIL（`Cannot find module '../src/domain/a2ui'`）

- [ ] **Step 3: 写实现** `src/domain/a2ui.ts`

```ts
import { z } from "zod"

// A2UI v0_9 operation（session→web 线上格式）。对齐 @a2ui/web_core 的 A2uiMessage。
// 组件项除必填 id/component 外按各组件 schema 放行（passthrough），与 @a2ui 一致。

const a2uiComponentSchema = z
  .object({ id: z.string().min(1), component: z.string().min(1) })
  .passthrough()

const createSurfaceOp = z
  .object({
    version: z.literal("v0.9"),
    createSurface: z.object({ surfaceId: z.string().min(1), catalogId: z.string().min(1) }).strict(),
  })
  .strict()

const updateComponentsOp = z
  .object({
    version: z.literal("v0.9"),
    updateComponents: z
      .object({ surfaceId: z.string().min(1), components: z.array(a2uiComponentSchema) })
      .strict(),
  })
  .strict()

const updateDataModelOp = z
  .object({
    version: z.literal("v0.9"),
    updateDataModel: z
      .object({ surfaceId: z.string().min(1), path: z.string().optional(), value: z.unknown() })
      .strict(),
  })
  .strict()

export const a2uiOpSchema = z.union([createSurfaceOp, updateComponentsOp, updateDataModelOp])

export type A2uiOp = z.infer<typeof a2uiOpSchema>
export type A2uiComponent = z.infer<typeof a2uiComponentSchema>
```

- [ ] **Step 4: 跑测试确认通过**

Run: `bun test tests/a2ui.test.ts`
Expected: PASS（6 个用例）

- [ ] **Step 5: commit**

```bash
git add src/domain/a2ui.ts tests/a2ui.test.ts
git commit -m "feat(session): A2UI v0_9 op domain types + strict zod schema"
```

### Task A2: A2uiProjector —— SessionEvent → A2UI op

**Files:**
- Create: `src/application/a2ui-projector.ts`
- Test: `tests/a2ui-projector.test.ts`

投影规则（surfaceId = 注入值，通常 = sessionId；root 为 `Thread`，children 按到达顺序累加）：
- `session.created` → 无 op（surface 在 run.created 建）。
- `run.created` → 首次：`createSurface{surfaceId, "kokoro/chat/v1"}` + `updateComponents` root `Thread{children:[]}`；非首次无 op。
- `thinking.summary` → mount `ThinkingBlock{summary:{path:"/thinking/{id}"}}` + `updateDataModel(/thinking/{id}=summary)` + root.children += id。id = `th_{++n}`。
- `tool.started` → mount `ToolCard{toolName,status:"running"}`（id = `tool_call_id`）+ root.children += id。
- `tool.completed` → `updateComponents` 同 id `ToolCard{toolName,status}`（不再加 child）。
- `message.delta` → 首个 delta：mount `Message{author:"ai",text:{path:"/messages/{message_id}"}}`（id=`message_id`）+ root.children += id；每个 delta：累加文本 → `updateDataModel(/messages/{message_id}=累计值)`。
- `message.completed` → `updateDataModel(/messages/{message_id}=content)`（覆盖为终值）。
- `run.completed` → 无 op。
- `run.failed` → mount `Message{author:"ai",text:{path:"/messages/err_{run}"}}` + `updateDataModel(=`⚠️ ${message}`)` + root.children += id。

- [ ] **Step 1: 写失败测试** `tests/a2ui-projector.test.ts`

```ts
import { describe, expect, it } from "bun:test"
import { A2uiProjector } from "../src/application/a2ui-projector"
import type { SessionEvent } from "../src/domain/events"

function ev(event: SessionEvent["event"], payload: Record<string, unknown>, n: number): SessionEvent {
  return {
    event,
    event_id: `evt_${n}`,
    session_id: "ses_1",
    conversation_id: "conv_1",
    run_id: "run_1",
    cursor: `run_1:${String(n).padStart(4, "0")}`,
    timestamp: "2026-05-30T00:00:00.000Z",
    payload,
  }
}

describe("A2uiProjector", () => {
  it("creates surface + Thread root on run.created (once)", () => {
    const p = new A2uiProjector("ses_1")
    const ops = p.project(ev("run.created", { run_id: "run_1" }, 1))
    expect(ops[0]).toEqual({ version: "v0.9", createSurface: { surfaceId: "ses_1", catalogId: "kokoro/chat/v1" } })
    expect(ops[1]).toEqual({
      version: "v0.9",
      updateComponents: { surfaceId: "ses_1", components: [{ id: "root", component: "Thread", children: [] }] },
    })
    // second run.created → no ops
    expect(p.project(ev("run.created", { run_id: "run_1" }, 2))).toEqual([])
  })

  it("session.created yields nothing", () => {
    const p = new A2uiProjector("ses_1")
    expect(p.project(ev("session.created", { session_id: "ses_1", conversation_id: "conv_1", owner_id: "x" }, 1))).toEqual([])
  })

  it("projects thinking.summary into ThinkingBlock + dataModel + root child", () => {
    const p = new A2uiProjector("ses_1")
    p.project(ev("run.created", { run_id: "run_1" }, 1))
    const ops = p.project(ev("thinking.summary", { run_id: "run_1", summary: "想一下" }, 2))
    expect(ops).toEqual([
      { version: "v0.9", updateComponents: { surfaceId: "ses_1", components: [{ id: "th_1", component: "ThinkingBlock", summary: { path: "/thinking/th_1" } }] } },
      { version: "v0.9", updateDataModel: { surfaceId: "ses_1", path: "/thinking/th_1", value: "想一下" } },
      { version: "v0.9", updateComponents: { surfaceId: "ses_1", components: [{ id: "root", component: "Thread", children: ["th_1"] }] } },
    ])
  })

  it("projects tool start→complete with stable id and status flip", () => {
    const p = new A2uiProjector("ses_1")
    p.project(ev("run.created", { run_id: "run_1" }, 1))
    const started = p.project(ev("tool.started", { tool_call_id: "run_1:tool_0001", tool_name: "echo_search" }, 2))
    expect(started[0]).toEqual({ version: "v0.9", updateComponents: { surfaceId: "ses_1", components: [{ id: "run_1:tool_0001", component: "ToolCard", toolName: "echo_search", status: "running" }] } })
    expect(started[1]).toEqual({ version: "v0.9", updateComponents: { surfaceId: "ses_1", components: [{ id: "root", component: "Thread", children: ["run_1:tool_0001"] }] } })
    const done = p.project(ev("tool.completed", { tool_call_id: "run_1:tool_0001", tool_name: "echo_search", status: "ok" }, 3))
    expect(done).toEqual([{ version: "v0.9", updateComponents: { surfaceId: "ses_1", components: [{ id: "run_1:tool_0001", component: "ToolCard", toolName: "echo_search", status: "ok" }] } }])
  })

  it("accumulates message deltas into dataModel and mounts Message once", () => {
    const p = new A2uiProjector("ses_1")
    p.project(ev("run.created", { run_id: "run_1" }, 1))
    const d1 = p.project(ev("message.delta", { message_id: "run_1:msg_0001", delta: "好的，", role: "assistant" }, 2))
    expect(d1[0]).toEqual({ version: "v0.9", updateComponents: { surfaceId: "ses_1", components: [{ id: "run_1:msg_0001", component: "Message", author: "ai", text: { path: "/messages/run_1:msg_0001" } }] } })
    expect(d1[1]).toEqual({ version: "v0.9", updateDataModel: { surfaceId: "ses_1", path: "/messages/run_1:msg_0001", value: "好的，" } })
    expect(d1[2]).toEqual({ version: "v0.9", updateComponents: { surfaceId: "ses_1", components: [{ id: "root", component: "Thread", children: ["run_1:msg_0001"] }] } })
    const d2 = p.project(ev("message.delta", { message_id: "run_1:msg_0001", delta: "结果是…", role: "assistant" }, 3))
    expect(d2).toEqual([{ version: "v0.9", updateDataModel: { surfaceId: "ses_1", path: "/messages/run_1:msg_0001", value: "好的，结果是…" } }])
  })

  it("message.completed overwrites accumulated text with final content", () => {
    const p = new A2uiProjector("ses_1")
    p.project(ev("run.created", { run_id: "run_1" }, 1))
    p.project(ev("message.delta", { message_id: "run_1:msg_0001", delta: "好的", role: "assistant" }, 2))
    const done = p.project(ev("message.completed", { message_id: "run_1:msg_0001", role: "assistant", content: "好的，最终答案。" }, 3))
    expect(done).toEqual([{ version: "v0.9", updateDataModel: { surfaceId: "ses_1", path: "/messages/run_1:msg_0001", value: "好的，最终答案。" } }])
  })

  it("run.failed appends an error Message", () => {
    const p = new A2uiProjector("ses_1")
    p.project(ev("run.created", { run_id: "run_1" }, 1))
    const ops = p.project(ev("run.failed", { run_id: "run_1", error_kind: "Boom", message: "炸了" }, 2))
    expect(ops[0]).toEqual({ version: "v0.9", updateComponents: { surfaceId: "ses_1", components: [{ id: "err_run_1", component: "Message", author: "ai", text: { path: "/messages/err_run_1" } }] } })
    expect(ops[1]).toEqual({ version: "v0.9", updateDataModel: { surfaceId: "ses_1", path: "/messages/err_run_1", value: "⚠️ 炸了" } })
    expect(ops[2]).toEqual({ version: "v0.9", updateComponents: { surfaceId: "ses_1", components: [{ id: "root", component: "Thread", children: ["err_run_1"] }] } })
  })

  it("run.completed yields nothing", () => {
    const p = new A2uiProjector("ses_1")
    p.project(ev("run.created", { run_id: "run_1" }, 1))
    expect(p.project(ev("run.completed", { run_id: "run_1", status: "completed" }, 2))).toEqual([])
  })
})
```

- [ ] **Step 2: 跑测试确认失败**

Run: `bun test tests/a2ui-projector.test.ts`
Expected: FAIL（模块不存在）

- [ ] **Step 3: 写实现** `src/application/a2ui-projector.ts`

```ts
import type { SessionEvent } from "../domain/events"
import { a2uiOpSchema, type A2uiOp } from "../domain/a2ui"

const CATALOG_ID = "kokoro/chat/v1"

// 把有序的归一化 SessionEvent 投影成 A2UI v0_9 op 流。
// 有状态（root.children 累加、按 message_id 累计文本、surface 单次创建），但状态完全由
// 有序事件流重建——每个 SSE 连接 new 一个，顺序喂 snapshot+tail 即可确定性重放。
export class A2uiProjector {
  private readonly surfaceId: string
  private surfaceCreated = false
  private readonly children: string[] = []
  private thinkingCounter = 0
  private readonly messageText = new Map<string, string>()

  constructor(surfaceId: string) {
    this.surfaceId = surfaceId
  }

  project(event: SessionEvent): A2uiOp[] {
    return this.map(event).map((op) => a2uiOpSchema.parse(op))
  }

  private rootOp(): A2uiOp {
    return {
      version: "v0.9",
      updateComponents: {
        surfaceId: this.surfaceId,
        components: [{ id: "root", component: "Thread", children: [...this.children] }],
      },
    }
  }

  private mountComponent(component: Record<string, unknown>): A2uiOp {
    return { version: "v0.9", updateComponents: { surfaceId: this.surfaceId, components: [component] } }
  }

  private setData(path: string, value: unknown): A2uiOp {
    return { version: "v0.9", updateDataModel: { surfaceId: this.surfaceId, path, value } }
  }

  private map(event: SessionEvent): A2uiOp[] {
    switch (event.event) {
      case "session.created":
        return []
      case "run.created": {
        if (this.surfaceCreated) return []
        this.surfaceCreated = true
        return [
          { version: "v0.9", createSurface: { surfaceId: this.surfaceId, catalogId: CATALOG_ID } },
          this.rootOp(),
        ]
      }
      case "thinking.summary": {
        const id = `th_${++this.thinkingCounter}`
        const path = `/thinking/${id}`
        this.children.push(id)
        return [
          this.mountComponent({ id, component: "ThinkingBlock", summary: { path } }),
          this.setData(path, String(event.payload.summary ?? "")),
          this.rootOp(),
        ]
      }
      case "tool.started": {
        const id = String(event.payload.tool_call_id)
        this.children.push(id)
        return [
          this.mountComponent({ id, component: "ToolCard", toolName: String(event.payload.tool_name), status: "running" }),
          this.rootOp(),
        ]
      }
      case "tool.completed": {
        const id = String(event.payload.tool_call_id)
        return [
          this.mountComponent({ id, component: "ToolCard", toolName: String(event.payload.tool_name), status: String(event.payload.status) }),
        ]
      }
      case "message.delta": {
        const id = String(event.payload.message_id)
        const path = `/messages/${id}`
        const prev = this.messageText.get(id)
        const next = (prev ?? "") + String(event.payload.delta ?? "")
        this.messageText.set(id, next)
        if (prev === undefined) {
          this.children.push(id)
          return [
            this.mountComponent({ id, component: "Message", author: "ai", text: { path } }),
            this.setData(path, next),
            this.rootOp(),
          ]
        }
        return [this.setData(path, next)]
      }
      case "message.completed": {
        const id = String(event.payload.message_id)
        const path = `/messages/${id}`
        this.messageText.set(id, String(event.payload.content ?? ""))
        return [this.setData(path, String(event.payload.content ?? ""))]
      }
      case "run.completed":
        return []
      case "run.failed": {
        const id = `err_${event.run_id}`
        const path = `/messages/${id}`
        this.children.push(id)
        return [
          this.mountComponent({ id, component: "Message", author: "ai", text: { path } }),
          this.setData(path, `⚠️ ${String(event.payload.message ?? "")}`),
          this.rootOp(),
        ]
      }
      default:
        return []
    }
  }
}
```

- [ ] **Step 4: 跑测试确认通过**

Run: `bun test tests/a2ui-projector.test.ts`
Expected: PASS（9 个用例）

- [ ] **Step 5: commit**

```bash
git add src/application/a2ui-projector.ts tests/a2ui-projector.test.ts
git commit -m "feat(session): A2uiProjector maps SessionEvent stream to A2UI ops"
```

### Task A3: SSE 发 A2UI op + http.ts 接线

**Files:**
- Modify: `src/infrastructure/sse.ts`
- Modify: `src/interfaces/http.ts:115-145`（`streamSession`）
- Test: `tests/sse.test.ts`（新增对 A2UI chunk 的断言）

- [ ] **Step 1: 写失败测试** `tests/sse.test.ts`

```ts
import { describe, expect, it } from "bun:test"
import { toA2uiSseChunk } from "../src/infrastructure/sse"

describe("toA2uiSseChunk", () => {
  it("emits id + a2ui.op event + json data", () => {
    const op = { version: "v0.9" as const, updateDataModel: { surfaceId: "ses_1", path: "/m", value: "x" } }
    const chunk = toA2uiSseChunk(op, "run_1:0002:0")
    expect(chunk).toBe(`id: run_1:0002:0\nevent: a2ui.op\ndata: ${JSON.stringify(op)}\n\n`)
  })
})
```

- [ ] **Step 2: 跑测试确认失败**

Run: `bun test tests/sse.test.ts`
Expected: FAIL（`toA2uiSseChunk` 不存在）

- [ ] **Step 3: 写实现** —— 在 `src/infrastructure/sse.ts` 追加（保留现有 `toSseChunk` 不删，供内部/兼容用）：

```ts
import type { A2uiOp } from "../domain/a2ui"

// A2UI op 的 SSE 封装：每行一条 op，事件名固定 a2ui.op，id 用来源 cursor + op 序号便于将来续传。
export function toA2uiSseChunk(op: A2uiOp, id: string): string {
  return `id: ${id}\n` + `event: a2ui.op\n` + `data: ${JSON.stringify(op)}\n\n`
}
```

- [ ] **Step 4: 跑测试确认通过**

Run: `bun test tests/sse.test.ts`
Expected: PASS

- [ ] **Step 5: 接线 `streamSession`** —— 修改 `src/interfaces/http.ts`。先更顶部 import：

```ts
import { toA2uiSseChunk } from "../infrastructure/sse"
import { A2uiProjector } from "../application/a2ui-projector"
```
（移除不再用的 `import { toSseChunk } from "../infrastructure/sse"`，保留 `parseSessionEvent`。）

把 `streamSession` 函数体（当前 121-144 行）替换为：

```ts
  res.writeHead(200, {
    "content-type": "text/event-stream",
    "cache-control": "no-cache",
    connection: "keep-alive",
  })

  // 每个连接独立 projector：把有序 SessionEvent 投影成 A2UI op，先重放快照再续订。
  const projector = new A2uiProjector(sessionId)
  const writeEvent = (event: SessionEvent, opSeqBase: number): void => {
    projector.project(event).forEach((op, i) => {
      res.write(toA2uiSseChunk(op, `${event.cursor}:${opSeqBase + i}`))
    })
  }

  const snapshot = await readReplaySnapshot(dependencies.streamPort, sessionId)
  let lastCursor = ""
  for (const event of snapshot) {
    writeEvent(event, 0)
    lastCursor = event.cursor
  }

  const stream = replayStream(sessionId)
  let aborted = false
  req.on("close", () => {
    aborted = true
  })

  for await (const item of dependencies.streamPort.subscribe(stream, lastCursor)) {
    if (aborted) break
    writeEvent(parseSessionEvent(item.event), 0)
  }
  res.end()
```
并在 `streamSession` 顶部确保 `SessionEvent` 类型已 import：把现有 `import { parseSessionEvent } from "../domain/events"` 改为 `import { parseSessionEvent, type SessionEvent } from "../domain/events"`。

- [ ] **Step 6: 跑全量 + LSP 绿**

Run: `bunx tsc --noEmit && bunx eslint . && bun test`
Expected: 全绿（含既有 normalize/relay 测试不受影响）

- [ ] **Step 7: commit**

```bash
git add src/infrastructure/sse.ts src/interfaces/http.ts tests/sse.test.ts
git commit -m "feat(session): stream A2UI ops over SSE via per-connection projector"
```

### Task A4: session 绿门 + 收尾

- [ ] **Step 1:** `bunx tsc --noEmit && bunx eslint . && bun test` 全绿，贴输出。
- [ ] **Step 2: commit（若有残留）**

```bash
git add -A && git commit -m "chore(session): chat-shell-a2ui lint/type/test green" || echo "nothing to commit"
```

---

## Chunk B — kokoro-web：自定义 catalog + 组件 + processor 消费

Dir `kokoro-web/`。`git checkout feat/bootstrap-shell`（web 主线，见上轮）`&& git checkout -b feat/chat-shell-a2ui`。测试：`bun run test`（vitest）。LSP：`bunx tsc --noEmit && bun run lint`。

> 设计 token 已在 `src/app/globals.css`（`--background:#faf7f2`、`--brand-wood:#8b6f47`、`--surface-soft`、`--border-soft`、`--radius-*` 等），直接复用；新增组件用这些变量 + 现有 `.kk-*` class 习惯。

### Task B1: 锁定 @a2ui 自定义组件 API（spike 测试 — 先建 Message）

**Files:**
- Create: `src/interfaces/a2ui/catalog.ts`（自定义 catalog 装配）
- Create: `src/interfaces/a2ui/components/message.tsx`
- Test: `src/interfaces/a2ui/__tests__/message.test.tsx`

目的：用最小自定义组件锁定 `createComponentImplementation` + `new Catalog` + `MessageProcessor` + `<A2uiSurface>` 的精确用法。**实现前先读** `node_modules/@a2ui/react/dist/**/v0_9/index.d.ts` 与 `node_modules/@a2ui/web_core/dist/**/v0_9/catalog/types.d.ts`，确认 `createComponentImplementation` 与 `RenderComponent` 的确切签名，按其调整下方 `MessageRender` 的 props 解构。

- [ ] **Step 1: 写失败测试** `src/interfaces/a2ui/__tests__/message.test.tsx`

```tsx
import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"
import { A2uiSurface } from "@a2ui/react/v0_9"
import { MessageProcessor } from "@a2ui/web_core/v0_9"
import { kokoroChatCatalog } from "../catalog"

function surfaceFor(messages: unknown[]) {
  const processor = new MessageProcessor([kokoroChatCatalog])
  processor.processMessages(messages as never)
  return processor.model.getSurface("s")!
}

describe("Message (kokoro/chat/v1)", () => {
  it("renders an assistant message from dataModel binding, left-aligned, no bubble", () => {
    const surface = surfaceFor([
      { version: "v0.9", createSurface: { surfaceId: "s", catalogId: "kokoro/chat/v1" } },
      { version: "v0.9", updateComponents: { surfaceId: "s", components: [
        { id: "root", component: "Thread", children: ["m1"] },
        { id: "m1", component: "Message", author: "ai", text: { path: "/messages/m1" } },
      ] } },
      { version: "v0.9", updateDataModel: { surfaceId: "s", path: "/messages/m1", value: "你好，我在。" } },
    ])
    render(<A2uiSurface surface={surface} />)
    const el = screen.getByText("你好，我在。")
    expect(el.closest(".kk-msg")).toHaveClass("kk-msg--ai")
  })
})
```

- [ ] **Step 2: 跑测试确认失败**

Run: `bun run test src/interfaces/a2ui/__tests__/message.test.tsx`
Expected: FAIL（`../catalog` 不存在）

- [ ] **Step 3: 写 Message 组件** `src/interfaces/a2ui/components/message.tsx`

> 按 Task B1 Step 0 读到的 `.d.ts` 签名调整解构；以下为基于探查的预期形状（`createComponentImplementation(api, RenderComponent)`，RenderComponent 收到经 schema 解析的 props，文本绑定 `{path}` 已解析为字符串）。

```tsx
import { z } from "zod"
import { createComponentImplementation } from "@a2ui/react/v0_9"

const messageSchema = z.object({
  author: z.enum(["ai", "user"]),
  text: z.string(),
})

// AI 左对齐无气泡叙述流；user 右对齐气泡（ADR-008）。
function MessageRender({ author, text }: z.infer<typeof messageSchema>) {
  const isAi = author === "ai"
  return (
    <div className={isAi ? "kk-msg kk-msg--ai" : "kk-msg kk-msg--user"}>
      <p className="kk-msg__text">{text}</p>
    </div>
  )
}

export const messageComponent = createComponentImplementation(
  { name: "Message", schema: messageSchema },
  MessageRender,
)
```

- [ ] **Step 4: 写 catalog 装配** `src/interfaces/a2ui/catalog.ts`

```ts
import { Catalog } from "@a2ui/web_core/v0_9"
import { messageComponent } from "./components/message"

// kokoro 对话 catalog；createSurface.catalogId 必须等于此 id。
// 组件随实现逐步加入（thread/thinking/tool 见后续 task）。
export const KOKORO_CHAT_CATALOG_ID = "kokoro/chat/v1"

export const kokoroChatCatalog = new Catalog(KOKORO_CHAT_CATALOG_ID, [messageComponent])
```

- [ ] **Step 5: 加最小样式** —— 在 `src/app/globals.css` 末尾追加：

```css
.kk-msg { display: flex; flex-direction: column; }
.kk-msg--ai { align-items: flex-start; }
.kk-msg--user { align-items: flex-end; }
.kk-msg__text {
  max-width: 42rem;
  font-size: 0.95rem;
  line-height: 1.75rem;
  color: var(--foreground);
  white-space: pre-wrap;
}
.kk-msg--user .kk-msg__text {
  border: 1px solid var(--border-user-soft);
  background: var(--surface-user-soft);
  border-radius: var(--radius-soft);
  padding: 0.625rem 0.875rem;
}
```

- [ ] **Step 6: 跑测试确认通过**

Run: `bun run test src/interfaces/a2ui/__tests__/message.test.tsx`
Expected: PASS。**若 RenderComponent 签名与上面不符**：读 `.d.ts` 改 `MessageRender` 解构（例如 props 可能是 `{ properties }` 或 `{ context }`），改到测试绿。把最终确定的签名记到本文件 Task B1 顶部备注，后续组件照此写。

- [ ] **Step 7: commit**

```bash
git add src/interfaces/a2ui/ src/app/globals.css
git commit -m "feat(web): kokoro/chat/v1 catalog + Message component (a2ui custom render)"
```

### Task B2: Thread 容器组件

**Files:**
- Create: `src/interfaces/a2ui/components/thread.tsx`
- Modify: `src/interfaces/a2ui/catalog.ts`（注册 thread）
- Test: `src/interfaces/a2ui/__tests__/thread.test.tsx`

- [ ] **Step 1: 写失败测试** `src/interfaces/a2ui/__tests__/thread.test.tsx`

```tsx
import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"
import { A2uiSurface } from "@a2ui/react/v0_9"
import { MessageProcessor } from "@a2ui/web_core/v0_9"
import { kokoroChatCatalog } from "../catalog"

describe("Thread (kokoro/chat/v1)", () => {
  it("renders children in order", () => {
    const processor = new MessageProcessor([kokoroChatCatalog])
    processor.processMessages([
      { version: "v0.9", createSurface: { surfaceId: "s", catalogId: "kokoro/chat/v1" } },
      { version: "v0.9", updateComponents: { surfaceId: "s", components: [
        { id: "root", component: "Thread", children: ["m1", "m2"] },
        { id: "m1", component: "Message", author: "ai", text: { path: "/m1" } },
        { id: "m2", component: "Message", author: "ai", text: { path: "/m2" } },
      ] } },
      { version: "v0.9", updateDataModel: { surfaceId: "s", path: "/m1", value: "一" } },
      { version: "v0.9", updateDataModel: { surfaceId: "s", path: "/m2", value: "二" } },
    ] as never)
    render(<A2uiSurface surface={processor.model.getSurface("s")!} />)
    const container = screen.getByTestId("kk-thread")
    expect(container.textContent).toBe("一二")
  })
})
```

- [ ] **Step 2: 跑测试确认失败**

Run: `bun run test src/interfaces/a2ui/__tests__/thread.test.tsx`
Expected: FAIL（catalog 无 Thread → 渲染不出 children / getByTestId 失败）

- [ ] **Step 3: 写 Thread 组件** `src/interfaces/a2ui/components/thread.tsx`

> 容器组件需用 `buildChild(id)` 渲染子节点。按 B1 锁定的容器签名实现（探查显示容器拿到 `children: string[]` 与 `buildChild`）。

```tsx
import { z } from "zod"
import { createComponentImplementation } from "@a2ui/react/v0_9"

const threadSchema = z.object({ children: z.array(z.string()).default([]) })

// 对话滚动容器：按 children 顺序竖排（对标原型 .chat-thread）。
function ThreadRender(
  { children }: z.infer<typeof threadSchema>,
  buildChild: (id: string) => React.ReactNode,
) {
  return (
    <div className="kk-thread" data-testid="kk-thread">
      {children.map((id) => (
        <div key={id} className="kk-thread__item">
          {buildChild(id)}
        </div>
      ))}
    </div>
  )
}

export const threadComponent = createComponentImplementation(
  { name: "Thread", schema: threadSchema },
  ThreadRender,
)
```
> `buildChild` 的获取方式按 `.d.ts` 锁定：可能作为第二参数，或来自 props 的 `buildChild`。调整到测试绿，并把容器签名追加到 B1 备注。

- [ ] **Step 4: 注册 Thread** —— 改 `src/interfaces/a2ui/catalog.ts`：

```ts
import { Catalog } from "@a2ui/web_core/v0_9"
import { messageComponent } from "./components/message"
import { threadComponent } from "./components/thread"

export const KOKORO_CHAT_CATALOG_ID = "kokoro/chat/v1"

export const kokoroChatCatalog = new Catalog(KOKORO_CHAT_CATALOG_ID, [threadComponent, messageComponent])
```

- [ ] **Step 5: 加样式** —— `src/app/globals.css` 追加：

```css
.kk-thread { display: flex; flex-direction: column; gap: 1.25rem; }
```

- [ ] **Step 6: 跑测试确认通过**

Run: `bun run test src/interfaces/a2ui/__tests__/thread.test.tsx`
Expected: PASS

- [ ] **Step 7: commit**

```bash
git add src/interfaces/a2ui/ src/app/globals.css
git commit -m "feat(web): Thread container component for kokoro/chat/v1"
```

### Task B3: ThinkingBlock 组件（迁移现有视觉）

**Files:**
- Create: `src/interfaces/a2ui/components/thinking-block.tsx`
- Modify: `src/interfaces/a2ui/catalog.ts`
- Test: `src/interfaces/a2ui/__tests__/thinking-block.test.tsx`

> 复用现有 `src/interfaces/session-stream/thinking-block.tsx` 的视觉（💭 思考 折叠），重包成 a2ui 组件，绑定 `summary:{path}`。

- [ ] **Step 1: 写失败测试** `src/interfaces/a2ui/__tests__/thinking-block.test.tsx`

```tsx
import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"
import { A2uiSurface } from "@a2ui/react/v0_9"
import { MessageProcessor } from "@a2ui/web_core/v0_9"
import { kokoroChatCatalog } from "../catalog"

describe("ThinkingBlock (kokoro/chat/v1)", () => {
  it("renders collapsed summary text from dataModel", () => {
    const processor = new MessageProcessor([kokoroChatCatalog])
    processor.processMessages([
      { version: "v0.9", createSurface: { surfaceId: "s", catalogId: "kokoro/chat/v1" } },
      { version: "v0.9", updateComponents: { surfaceId: "s", components: [
        { id: "root", component: "Thread", children: ["t1"] },
        { id: "t1", component: "ThinkingBlock", summary: { path: "/t1" } },
      ] } },
      { version: "v0.9", updateDataModel: { surfaceId: "s", path: "/t1", value: "在想要不要先查一下。" } },
    ] as never)
    render(<A2uiSurface surface={processor.model.getSurface("s")!} />)
    expect(screen.getByText("在想要不要先查一下。")).toBeInTheDocument()
    // 默认折叠：details 无 open 属性
    const details = screen.getByText("在想要不要先查一下。").closest("details")
    expect(details).not.toHaveAttribute("open")
  })
})
```

- [ ] **Step 2: 跑测试确认失败**

Run: `bun run test src/interfaces/a2ui/__tests__/thinking-block.test.tsx`
Expected: FAIL

- [ ] **Step 3: 写组件** `src/interfaces/a2ui/components/thinking-block.tsx`

```tsx
import { z } from "zod"
import { createComponentImplementation } from "@a2ui/react/v0_9"

const thinkingSchema = z.object({ summary: z.string() })

// 可折叠思考块（对标原型 .thinking）；默认折叠。
function ThinkingRender({ summary }: z.infer<typeof thinkingSchema>) {
  return (
    <details className="kk-thinking">
      <summary className="kk-thinking__summary">💭 思考</summary>
      <p className="kk-thinking__body">{summary}</p>
    </details>
  )
}

export const thinkingBlockComponent = createComponentImplementation(
  { name: "ThinkingBlock", schema: thinkingSchema },
  ThinkingRender,
)
```

- [ ] **Step 4: 注册 + 样式** —— catalog.ts 加 `thinkingBlockComponent`；`globals.css` 追加：

```css
.kk-thinking { border: 1px solid var(--border-soft); border-radius: var(--radius-soft); background: var(--surface-soft); padding: 0.5rem 0.875rem; }
.kk-thinking__summary { cursor: pointer; font-size: 0.8125rem; color: var(--brand-wood); list-style: none; }
.kk-thinking__body { margin-top: 0.5rem; font-size: 0.875rem; line-height: 1.6rem; color: rgba(43,37,32,0.78); white-space: pre-wrap; }
```

catalog.ts 数组改为 `[threadComponent, messageComponent, thinkingBlockComponent]`。

- [ ] **Step 5: 跑测试确认通过**

Run: `bun run test src/interfaces/a2ui/__tests__/thinking-block.test.tsx`
Expected: PASS

- [ ] **Step 6: commit**

```bash
git add src/interfaces/a2ui/ src/app/globals.css
git commit -m "feat(web): ThinkingBlock component for kokoro/chat/v1"
```

### Task B4: ToolCard 组件

**Files:**
- Create: `src/interfaces/a2ui/components/tool-card.tsx`
- Modify: `src/interfaces/a2ui/catalog.ts`
- Test: `src/interfaces/a2ui/__tests__/tool-card.test.tsx`

- [ ] **Step 1: 写失败测试** `src/interfaces/a2ui/__tests__/tool-card.test.tsx`

```tsx
import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"
import { A2uiSurface } from "@a2ui/react/v0_9"
import { MessageProcessor } from "@a2ui/web_core/v0_9"
import { kokoroChatCatalog } from "../catalog"

function surfaceFor(status: string) {
  const processor = new MessageProcessor([kokoroChatCatalog])
  processor.processMessages([
    { version: "v0.9", createSurface: { surfaceId: "s", catalogId: "kokoro/chat/v1" } },
    { version: "v0.9", updateComponents: { surfaceId: "s", components: [
      { id: "root", component: "Thread", children: ["c1"] },
      { id: "c1", component: "ToolCard", toolName: "echo_search", status },
    ] } },
  ] as never)
  return processor.model.getSurface("s")!
}

describe("ToolCard (kokoro/chat/v1)", () => {
  it("shows running state", () => {
    render(<A2uiSurface surface={surfaceFor("running")} />)
    expect(screen.getByText(/echo_search/)).toBeInTheDocument()
    expect(screen.getByTestId("kk-tool").dataset.status).toBe("running")
  })
  it("shows done state", () => {
    render(<A2uiSurface surface={surfaceFor("ok")} />)
    expect(screen.getByTestId("kk-tool").dataset.status).toBe("ok")
  })
})
```

- [ ] **Step 2: 跑测试确认失败**

Run: `bun run test src/interfaces/a2ui/__tests__/tool-card.test.tsx`
Expected: FAIL

- [ ] **Step 3: 写组件** `src/interfaces/a2ui/components/tool-card.tsx`

```tsx
import { z } from "zod"
import { createComponentImplementation } from "@a2ui/react/v0_9"

const toolSchema = z.object({ toolName: z.string(), status: z.string() })

// 工具卡（对标原型 .tool-call-details）：running 呼吸，done/ok ✓，error ⚠️。
function ToolRender({ toolName, status }: z.infer<typeof toolSchema>) {
  const mark = status === "running" ? "⟳" : status === "error" ? "⚠️" : "✓"
  return (
    <div className="kk-tool" data-testid="kk-tool" data-status={status}>
      <span className="kk-tool__icon">🔧</span>
      <span className="kk-tool__name">{toolName}</span>
      <span className="kk-tool__mark">{mark}</span>
    </div>
  )
}

export const toolCardComponent = createComponentImplementation(
  { name: "ToolCard", schema: toolSchema },
  ToolRender,
)
```

- [ ] **Step 4: 注册 + 样式** —— catalog.ts 数组改为 `[threadComponent, messageComponent, thinkingBlockComponent, toolCardComponent]`；`globals.css` 追加：

```css
.kk-tool { display: inline-flex; align-items: center; gap: 0.5rem; border: 1px solid var(--border-soft); border-radius: 999px; background: var(--surface); padding: 0.375rem 0.75rem; font-size: 0.8125rem; color: var(--foreground); }
.kk-tool[data-status="running"] .kk-tool__mark { animation: kk-pulse 1.8s ease-in-out infinite; }
@keyframes kk-pulse { 0%,100% { opacity: 0.4; } 50% { opacity: 1; } }
```

- [ ] **Step 5: 跑测试确认通过**

Run: `bun run test src/interfaces/a2ui/__tests__/tool-card.test.tsx`
Expected: PASS（2 用例）

- [ ] **Step 6: commit**

```bash
git add src/interfaces/a2ui/ src/app/globals.css
git commit -m "feat(web): ToolCard component for kokoro/chat/v1"
```

### Task B5: A2UI SSE 消费 hook —— 接 op 流喂 processor

**Files:**
- Create: `src/application/a2ui-session.ts`（消费 SSE a2ui.op → MessageProcessor）
- Create: `src/interfaces/a2ui/use-a2ui-surface.ts`（React hook）
- Test: `src/application/__tests__/a2ui-session.test.ts`

> 替代旧 `session-stream-preview.ts` 的消费路径。仍复用 `resolveSessionBaseUrl`/POST run 触发逻辑（从旧文件搬 `resolveSessionBaseUrl`、`demoSessionId`、`buildRunUrl` 思路），但 SSE 解码改成 `a2ui.op` → `processor.processMessages([op])`。

- [ ] **Step 1: 写失败测试** `src/application/__tests__/a2ui-session.test.ts`

```ts
import { describe, expect, it } from "vitest"
import { MessageProcessor } from "@a2ui/web_core/v0_9"
import { kokoroChatCatalog } from "@/interfaces/a2ui/catalog"
import { feedA2uiLine } from "../a2ui-session"

describe("feedA2uiLine", () => {
  it("parses a JSON op line and feeds the processor incrementally", () => {
    const processor = new MessageProcessor([kokoroChatCatalog])
    feedA2uiLine(processor, JSON.stringify({ version: "v0.9", createSurface: { surfaceId: "s", catalogId: "kokoro/chat/v1" } }))
    feedA2uiLine(processor, JSON.stringify({ version: "v0.9", updateComponents: { surfaceId: "s", components: [{ id: "root", component: "Thread", children: [] }] } }))
    expect(processor.model.getSurface("s")).toBeTruthy()
  })

  it("ignores malformed lines without throwing", () => {
    const processor = new MessageProcessor([kokoroChatCatalog])
    expect(() => feedA2uiLine(processor, "not json")).not.toThrow()
    expect(() => feedA2uiLine(processor, JSON.stringify({ nope: 1 }))).not.toThrow()
  })
})
```

- [ ] **Step 2: 跑测试确认失败**

Run: `bun run test src/application/__tests__/a2ui-session.test.ts`
Expected: FAIL

- [ ] **Step 3: 写实现** `src/application/a2ui-session.ts`

```ts
import type { MessageProcessor } from "@a2ui/web_core/v0_9"

export function resolveSessionBaseUrl(): string {
  if (process.env.NEXT_PUBLIC_KOKORO_SESSION_BASE_URL) {
    return process.env.NEXT_PUBLIC_KOKORO_SESSION_BASE_URL
  }
  if (typeof window !== "undefined") {
    const host = window.location.hostname === "localhost" ? "localhost" : "127.0.0.1"
    return `http://${host}:3001`
  }
  return "http://127.0.0.1:3001"
}

// 单条 SSE a2ui.op 载荷 → 喂 processor。畸形行吞掉不崩（纯渲染韧性）。
export function feedA2uiLine(processor: MessageProcessor<never>, data: string): void {
  let op: unknown
  try {
    op = JSON.parse(data)
  } catch {
    return
  }
  if (typeof op !== "object" || op === null || !("version" in op)) {
    return
  }
  try {
    processor.processMessages([op] as never)
  } catch {
    // 单条 op 适配失败不撕毁整条流
  }
}

export type A2uiSessionHandle = { close: () => void }

// POST 触发 run，开 EventSource 订阅 a2ui.op，逐条喂 processor。onOp 回调供 React 重渲染节流。
export async function startA2uiSession(opts: {
  processor: MessageProcessor<never>
  input: string
  sessionId: string
  conversationId?: string
  onOp?: () => void
  baseUrl?: string
}): Promise<A2uiSessionHandle> {
  const baseUrl = opts.baseUrl ?? resolveSessionBaseUrl()
  const conversationId = opts.conversationId ?? opts.sessionId
  const runUrl = new URL(`/sessions/${opts.sessionId}/runs`, baseUrl)
  runUrl.searchParams.set("conversation_id", conversationId)
  runUrl.searchParams.set("input", opts.input)
  runUrl.searchParams.set("execution_style", "thinking")

  const res = await fetch(runUrl.toString(), { method: "POST" })
  if (!res.ok) throw new Error(`session start failed: ${res.status}`)

  if (typeof EventSource === "undefined") return { close: () => {} }
  const streamUrl = new URL(`/sessions/${opts.sessionId}/stream`, baseUrl)
  const source = new EventSource(streamUrl.toString())
  const handler: EventListener = (e) => {
    if (e instanceof MessageEvent) {
      feedA2uiLine(opts.processor, e.data as string)
      opts.onOp?.()
    }
  }
  source.addEventListener("a2ui.op", handler)
  return {
    close: () => {
      source.removeEventListener("a2ui.op", handler)
      source.close()
    },
  }
}
```
> 注：`execution_style=thinking` 让 scripted/真实脑产 thinking。`MessageProcessor<never>` 仅为类型占位，B6 用真实 catalog 实例时类型自洽；若 tsc 报参数化不符，按 `.d.ts` 改为 `MessageProcessor<ReactComponentImplementation>`。

- [ ] **Step 4: 跑测试确认通过**

Run: `bun run test src/application/__tests__/a2ui-session.test.ts`
Expected: PASS

- [ ] **Step 5: 写 hook** `src/interfaces/a2ui/use-a2ui-surface.ts`

```tsx
"use client"

import { useEffect, useRef, useState } from "react"
import { MessageProcessor, type SurfaceModel } from "@a2ui/web_core/v0_9"
import type { ReactComponentImplementation } from "@a2ui/react/v0_9"
import { kokoroChatCatalog } from "./catalog"
import { startA2uiSession, type A2uiSessionHandle } from "@/application/a2ui-session"

// 起一个 run 并把 A2UI op 流折进 processor，surface 变化时触发重渲染。
export function useA2uiSurface(input: { text: string; sessionId: string }) {
  const [surface, setSurface] = useState<SurfaceModel<ReactComponentImplementation> | null>(null)
  const [tick, setTick] = useState(0)
  const processorRef = useRef<MessageProcessor<ReactComponentImplementation> | null>(null)

  useEffect(() => {
    if (typeof window === "undefined") return
    const processor = new MessageProcessor<ReactComponentImplementation>([kokoroChatCatalog])
    processorRef.current = processor
    let handle: A2uiSessionHandle = { close: () => {} }
    let disposed = false

    const sync = () => {
      const s = processor.model.getSurface(input.sessionId)
      if (s) setSurface(s)
      setTick((t) => t + 1)
    }
    processor.onSurfaceCreated(() => sync())

    void startA2uiSession({
      processor: processor as unknown as MessageProcessor<never>,
      input: input.text,
      sessionId: input.sessionId,
      onOp: sync,
    })
      .then((h) => {
        if (disposed) h.close()
        else handle = h
      })
      .catch(() => {})

    return () => {
      disposed = true
      handle.close()
    }
  }, [input.text, input.sessionId])

  return { surface, tick }
}
```
> `tick` 强制在 op 到达后重渲染（surface 内部 signals 也会驱动 A2uiSurface 自身，但顶层 surface 引用不变时用 tick 兜底）。若 `onSurfaceCreated`/类型签名与 `.d.ts` 不符，按实际签名微调。

- [ ] **Step 6: tsc + lint 绿，commit**

Run: `bunx tsc --noEmit && bun run lint`
Expected: 绿

```bash
git add src/application/a2ui-session.ts src/application/__tests__/a2ui-session.test.ts src/interfaces/a2ui/use-a2ui-surface.ts
git commit -m "feat(web): consume A2UI op SSE stream into MessageProcessor"
```

---

## Chunk C — kokoro-web：聊天外壳（侧栏 IA + composer + 装配）

### Task C1: 侧栏 IA 外壳（视觉占位）

**Files:**
- Create: `src/interfaces/chat/sidebar.tsx`
- Test: `src/interfaces/chat/__tests__/sidebar.test.tsx`

> 对标 `variant-a-mi-mu` 单列分组（PROJECT-STATE §4）：新对话/搜索 · 创作(7 组件) · 进阶 · 发现 · 用户行。本轮纯展示，不接路由。

- [ ] **Step 1: 写失败测试** `src/interfaces/chat/__tests__/sidebar.test.tsx`

```tsx
import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"
import { Sidebar } from "../sidebar"

describe("Sidebar", () => {
  it("renders brand + primary nav + creation group", () => {
    render(<Sidebar />)
    expect(screen.getByText("Kokoro")).toBeInTheDocument()
    expect(screen.getByText("新对话")).toBeInTheDocument()
    for (const label of ["图片", "视频", "数字人", "音频", "设计", "文档", "站点"]) {
      expect(screen.getByText(label)).toBeInTheDocument()
    }
  })
})
```

- [ ] **Step 2: 跑测试确认失败**

Run: `bun run test src/interfaces/chat/__tests__/sidebar.test.tsx`
Expected: FAIL

- [ ] **Step 3: 写组件** `src/interfaces/chat/sidebar.tsx`

```tsx
const CREATION = ["图片", "视频", "数字人", "音频", "设计", "文档", "站点"]
const DISCOVER = ["案例", "Skill Hub", "MCP Hub"]

// 侧栏 IA 外壳（视觉占位，不接路由）。对标 variant-a-mi-mu 单列分组。
export function Sidebar() {
  return (
    <aside className="kk-sidebar">
      <div className="kk-sidebar__brand">
        <span className="kk-sidebar__mark">心</span>
        <span className="kk-sidebar__name">Kokoro</span>
      </div>
      <nav className="kk-sidebar__nav">
        <button className="kk-nav-item kk-nav-item--primary" type="button">新对话</button>
        <button className="kk-nav-item" type="button">搜索</button>
      </nav>
      <p className="kk-sidebar__group-label">创作</p>
      <nav className="kk-sidebar__nav">
        {CREATION.map((label) => (
          <button key={label} className="kk-nav-item" type="button">{label}</button>
        ))}
      </nav>
      <p className="kk-sidebar__group-label">发现</p>
      <nav className="kk-sidebar__nav">
        {DISCOVER.map((label) => (
          <button key={label} className="kk-nav-item" type="button">{label}</button>
        ))}
      </nav>
      <div className="kk-sidebar__user">小 · 免费</div>
    </aside>
  )
}
```

- [ ] **Step 4: 样式** —— `globals.css` 追加：

```css
.kk-sidebar { display: flex; flex-direction: column; gap: 0.5rem; width: 15rem; padding: 1rem; background: var(--surface-soft); border-right: 1px solid var(--border-soft); }
.kk-sidebar__brand { display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem; }
.kk-sidebar__mark { display: inline-flex; align-items: center; justify-content: center; width: 1.75rem; height: 1.75rem; border-radius: 999px; background: var(--brand-wood); color: #fffdf9; font-size: 0.875rem; }
.kk-sidebar__name { font-weight: 600; color: var(--foreground); }
.kk-sidebar__group-label { margin-top: 0.75rem; font-size: 0.6875rem; letter-spacing: 0.18em; text-transform: uppercase; color: var(--brand-wood); }
.kk-sidebar__nav { display: flex; flex-direction: column; gap: 0.125rem; }
.kk-nav-item { text-align: left; padding: 0.5rem 0.625rem; border-radius: var(--radius-soft); font-size: 0.875rem; color: var(--foreground); background: transparent; border: none; cursor: pointer; }
.kk-nav-item:hover { background: var(--brand-wood-soft); }
.kk-nav-item--primary { color: var(--brand-wood); font-weight: 600; }
.kk-sidebar__user { margin-top: auto; padding: 0.5rem 0.625rem; font-size: 0.8125rem; color: rgba(43,37,32,0.72); }
```

- [ ] **Step 5: 跑测试确认通过 + commit**

Run: `bun run test src/interfaces/chat/__tests__/sidebar.test.tsx`
Expected: PASS

```bash
git add src/interfaces/chat/sidebar.tsx src/interfaces/chat/__tests__/sidebar.test.tsx src/app/globals.css
git commit -m "feat(web): sidebar IA shell (variant-a-mi-mu single-column groups)"
```

### Task C2: Composer（input-pill）

**Files:**
- Create: `src/interfaces/chat/composer.tsx`
- Test: `src/interfaces/chat/__tests__/composer.test.tsx`

- [ ] **Step 1: 写失败测试** `src/interfaces/chat/__tests__/composer.test.tsx`

```tsx
import { render, screen, fireEvent } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"
import { Composer } from "../composer"

describe("Composer", () => {
  it("submits trimmed input and clears", () => {
    const onSend = vi.fn()
    render(<Composer onSend={onSend} />)
    const field = screen.getByPlaceholderText("把想说的告诉我。") as HTMLTextAreaElement
    fireEvent.change(field, { target: { value: "  你好  " } })
    fireEvent.click(screen.getByRole("button", { name: "发送" }))
    expect(onSend).toHaveBeenCalledWith("你好")
    expect(field.value).toBe("")
  })

  it("does not submit empty", () => {
    const onSend = vi.fn()
    render(<Composer onSend={onSend} />)
    fireEvent.click(screen.getByRole("button", { name: "发送" }))
    expect(onSend).not.toHaveBeenCalled()
  })
})
```

- [ ] **Step 2: 跑测试确认失败**

Run: `bun run test src/interfaces/chat/__tests__/composer.test.tsx`
Expected: FAIL

- [ ] **Step 3: 写组件** `src/interfaces/chat/composer.tsx`

```tsx
"use client"

import { useState } from "react"

// input-pill 输入区（对标原型 .input-pill）。附件/模式 chip 本轮视觉占位。
export function Composer({ onSend }: { onSend: (text: string) => void }) {
  const [value, setValue] = useState("")
  const submit = () => {
    const text = value.trim()
    if (!text) return
    onSend(text)
    setValue("")
  }
  return (
    <div className="kk-composer">
      <button className="kk-composer__attach" type="button" aria-label="附件">＋</button>
      <textarea
        className="kk-composer__field"
        placeholder="把想说的告诉我。"
        value={value}
        rows={1}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault()
            submit()
          }
        }}
      />
      <span className="kk-composer__mode">细想</span>
      <button className="kk-composer__send" type="button" aria-label="发送" onClick={submit}>↑</button>
    </div>
  )
}
```

- [ ] **Step 4: 样式** —— `globals.css` 追加：

```css
.kk-composer { display: flex; align-items: center; gap: 0.5rem; border: 1px solid var(--border-soft); border-radius: var(--radius-pill, 24px); background: var(--surface); padding: 0.5rem 0.75rem; box-shadow: 0 6px 24px rgba(139,111,71,0.06); }
.kk-composer__attach, .kk-composer__send { width: 2rem; height: 2rem; border-radius: 999px; border: none; cursor: pointer; font-size: 1rem; }
.kk-composer__attach { background: transparent; color: var(--brand-wood); }
.kk-composer__send { background: var(--brand-wood); color: #fffdf9; }
.kk-composer__field { flex: 1; resize: none; border: none; outline: none; background: transparent; font-size: 0.95rem; line-height: 1.5rem; color: var(--foreground); }
.kk-composer__mode { font-size: 0.75rem; color: var(--brand-wood); border: 1px solid var(--brand-wood-soft); border-radius: 999px; padding: 0.125rem 0.5rem; }
```
（若 `--radius-pill` 未定义则在 `:root` 增 `--radius-pill: 24px;`。）

- [ ] **Step 5: 跑测试确认通过 + commit**

Run: `bun run test src/interfaces/chat/__tests__/composer.test.tsx`
Expected: PASS（2 用例）

```bash
git add src/interfaces/chat/composer.tsx src/interfaces/chat/__tests__/composer.test.tsx src/app/globals.css
git commit -m "feat(web): input-pill composer"
```

### Task C3: 聊天页装配（替换旧 SessionShell）

**Files:**
- Create: `src/interfaces/chat/chat-page.tsx`
- Modify: `src/app/page.tsx`
- Delete（旧朴素外壳）: `src/interfaces/session-stream/session-shell.tsx`、`src/application/session-stream-preview.ts`、`src/application/session-stream-reducer.ts`、`src/infrastructure/protocol/session-event.ts`、`src/domain/shared/session-stream-event.ts`、`src/interfaces/session-stream/thinking-block.tsx`、`src/interfaces/session-stream/tool-card.tsx`、`src/interfaces/session-stream/artifact-preview.tsx`（其测试一并删）
- Test: `src/interfaces/chat/__tests__/chat-page.test.tsx`（空状态渲染）

> 删除前先 `git grep` 确认无其它引用：`git grep -l "session-stream-reducer\|session-stream-preview\|SessionShell\|artifact-preview"`。仅删本轮被取代的文件；`page.tsx` 改指 `ChatPage`。

- [ ] **Step 1: 写失败测试** `src/interfaces/chat/__tests__/chat-page.test.tsx`

```tsx
import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"
import { ChatPage } from "../chat-page"

describe("ChatPage", () => {
  it("renders greeting empty state + composer + sidebar", () => {
    render(<ChatPage />)
    expect(screen.getByText("Kokoro")).toBeInTheDocument()
    expect(screen.getByText(/今天想做/)).toBeInTheDocument()
    expect(screen.getByPlaceholderText("把想说的告诉我。")).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: 跑测试确认失败**

Run: `bun run test src/interfaces/chat/__tests__/chat-page.test.tsx`
Expected: FAIL

- [ ] **Step 3: 写装配** `src/interfaces/chat/chat-page.tsx`

```tsx
"use client"

import { useState } from "react"
import { A2uiSurface } from "@a2ui/react/v0_9"
import { Sidebar } from "./sidebar"
import { Composer } from "./composer"
import { useA2uiSurface } from "@/interfaces/a2ui/use-a2ui-surface"

function makeSessionId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return `ses_${crypto.randomUUID().replace(/-/g, "").slice(0, 12)}`
  }
  return "ses_demo"
}

export function ChatPage() {
  const [run, setRun] = useState<{ text: string; sessionId: string } | null>(null)
  const { surface } = useA2uiSurface(run ?? { text: "", sessionId: "" })

  return (
    <div className="kk-app">
      <Sidebar />
      <main className="kk-main">
        {!run && (
          <div className="kk-empty">
            <h1 className="kk-empty__title">今天想做<span className="kk-empty__accent">什么</span>？</h1>
            <p className="kk-empty__sub">不急，先把想法说给我。</p>
          </div>
        )}
        <div className="kk-conversation">
          {surface && <A2uiSurface surface={surface} />}
        </div>
        <div className="kk-composer-dock">
          <Composer onSend={(text) => setRun({ text, sessionId: makeSessionId() })} />
        </div>
      </main>
    </div>
  )
}
```

- [ ] **Step 4: 改 `src/app/page.tsx`**

```tsx
import { ChatPage } from "@/interfaces/chat/chat-page"

export default function Page() {
  return <ChatPage />
}
```

- [ ] **Step 5: 删旧文件 + 样式**

```bash
git rm src/interfaces/session-stream/session-shell.tsx \
  src/application/session-stream-preview.ts \
  src/application/session-stream-reducer.ts \
  src/infrastructure/protocol/session-event.ts \
  src/domain/shared/session-stream-event.ts \
  src/interfaces/session-stream/thinking-block.tsx \
  src/interfaces/session-stream/tool-card.tsx \
  src/interfaces/session-stream/artifact-preview.tsx
# 同时 git rm 这些文件对应的旧测试（用 git grep / ls 找到 *.test.ts(x)）
```
`globals.css` 追加：

```css
.kk-app { display: flex; min-height: 100vh; background: var(--background); }
.kk-main { flex: 1; display: flex; flex-direction: column; max-width: 56rem; margin: 0 auto; padding: 2rem 1.5rem; }
.kk-empty { margin: auto 0 1.5rem; text-align: center; }
.kk-empty__title { font-size: 2rem; font-weight: 600; color: var(--foreground); }
.kk-empty__accent { color: var(--brand-wood); }
.kk-empty__sub { margin-top: 0.5rem; color: rgba(43,37,32,0.7); }
.kk-conversation { flex: 1; }
.kk-composer-dock { position: sticky; bottom: 1rem; margin-top: 1rem; }
```

- [ ] **Step 6: 跑测试 + 全量 LSP/lint/build 绿**

Run: `bunx tsc --noEmit && bun run lint && bun run test && bun run build`
Expected: 全绿（删文件后无悬空 import；若有，按 `git grep` 结果清理引用）

- [ ] **Step 7: commit**

```bash
git add -A
git commit -m "feat(web): chat page assembling sidebar + A2UI surface + composer; drop legacy shell"
```

### Task C4: web 绿门

- [ ] **Step 1:** `bunx tsc --noEmit && bun run lint && bun run test && bun run build` 全绿，贴关键输出。
- [ ] **Step 2: commit（若有残留）**

```bash
git add -A && git commit -m "chore(web): chat-shell-a2ui lint/type/test/build green" || echo "nothing to commit"
```

---

## Chunk D — 协议文档：session-stream.md v2.0.0

Dir 父仓 `Kokoro/`（分支 `docs/chat-shell-a2ui`，本计划所在分支）。

### Task D1: 升级 session-stream.md

**Files:**
- Modify: `docs/protocol/session-stream.md`

- [ ] **Step 1:** 读现 `docs/protocol/session-stream.md`，在头部 frontmatter `version` 升到 `2.0.0`，并在正文加一节「v2.0.0 — A2UI op 流」，写明：
  - session→web 线上格式从自研 AGUI 信封改为 **A2UI v0_9 operation 流**（`createSurface`/`updateComponents`/`updateDataModel`）。
  - catalog `kokoro/chat/v1` 组件集：`Thread` / `Message{author,text}` / `ThinkingBlock{summary}` / `ToolCard{toolName,status}`。
  - SSE 封装：`event: a2ui.op`，`data:` 为单条 op JSON，`id:` = `{cursor}:{opSeq}`。
  - 内部仍由 `Normalizer` 产 AGUI `SessionEvent`（内部表示），经 `A2uiProjector` 投影成 op；replay 仍存 SessionEvent，重连从头重放（中点续传留后轮）。
  - 旧版（v1.0.0 AGUI 信封）移入「历史」段，注明 superseded-by v2.0.0。
- [ ] **Step 2: commit**

```bash
git add docs/protocol/session-stream.md
git commit -m "docs(protocol): session-stream v2.0.0 — A2UI op stream + kokoro/chat/v1 catalog"
```

---

## Chunk E — 集成离线浏览器验证（控制器执行，不派子代理）

### Task E1: 三进程离线 e2e + 截图

- [ ] **Step 1:** 起 redis：`redis-server --daemonize yes`（已装；docker daemon 可能关）。
- [ ] **Step 2:** 三进程（各自终端 / 后台），全程 `KOKORO_STREAM_BACKEND=redis KOKORO_MODEL=scripted`：
  - agent worker：`cd kokoro-agent && KOKORO_STREAM_BACKEND=redis KOKORO_MODEL=scripted uv run kokoro-agent-worker`
  - session：`cd kokoro-session && KOKORO_STREAM_BACKEND=redis bun run start`
  - web：`cd kokoro-web && bun run dev`
- [ ] **Step 3:** Playwright：开 `http://localhost:3000`，在 composer 输入「帮我查一下」并发送；等待 surface 渲染。
- [ ] **Step 4:** 断言看到：💭 思考块（默认折叠）+ 🔧 echo_search 工具卡（running→✓）+ AI 正文消息，左对齐无气泡。展开思考块。截图两张（折叠 / 展开）存 `kokoro-web/.playwright-mcp/`（已 gitignore）。0 console error。
- [ ] **Step 5:** 停进程 + redis（`redis-cli shutdown` 或 `kill`），清 `dump.rdb`。

## Done criteria
- 三仓（session/web + 父仓 docs）LSP/linter/test 全绿；agent 不改仍绿。
- 事件族经 **A2UI op 流** agent→session→web 贯通：session `A2uiProjector` 产 `createSurface`/`updateComponents`/`updateDataModel`；web `@a2ui` + `kokoro/chat/v1` catalog 渲染成 variant-a-mi-mu 风格对话（侧栏 + input-pill + 无气泡 AI + 折叠思考块 + 工具卡）。
- 离线浏览器 e2e 截图存档（折叠/展开），无真实 LLM/key。
- agent 只产原始 kind；web 只消费 A2UI op；session 拥有投影。无跨仓 import。

## 自检（writing-plans self-review）
- Spec 覆盖：§5 op 子集→A1/A2/A3；§6 catalog 4 组件→B1-B4；§7 数据流→A2 投影规则 + B5 消费；§4 架构边界→A 不碰 normalize、agent 不动；§9 测试→各 task TDD + E1 e2e；§10 协议→D1。canvas/断连续传/agent 选型明确不做（spec §11）。
- 类型一致：op 形状 `{version:"v0.9", <opKey>:{...}}` 全文一致；组件名 Thread/Message/ThinkingBlock/ToolCard 在 session 投影（A2）与 web catalog（B1-B4）两侧字面一致；`message_id`/`tool_call_id` 作为组件 id 贯穿。
- 已标注的实现期确认点：B1 锁定 `createComponentImplementation`/`buildChild`/`RenderComponent` 精确签名（读 .d.ts），后续组件照此；B5 `MessageProcessor` 泛型参数按 .d.ts 微调。这些是对未稳定外部包的必要 spike，非占位。
