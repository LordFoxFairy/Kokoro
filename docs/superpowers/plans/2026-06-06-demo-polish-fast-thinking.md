# Demo Polish, Fast/Thinking Differentiation, and Structured Subagent Stream Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the current Kokoro chat shell into a demo-grade conversation flow where the main path feels polished, Fast vs Thinking are clearly different to users, and subagent activity is shown as clean structured progress instead of noisy raw stream output.

**Architecture:** Keep backend execution semantics untouched unless the UI truly needs additional structured state. Concentrate this pass in `kokoro-web`, using stable application/domain state to drive presentation differences between Fast and Thinking, and keeping components small, composable, and readable. Prefer explicit mode-aware UI state and structured milestone rendering over ad-hoc conditionals scattered across presentational components.

**Tech Stack:** Next.js App Router, React 19, TypeScript, Vitest, Testing Library, existing `kokoro-web` conversation-store / session-stream reducer / activity components.

---

## File map

### Likely UI behavior files
- Modify: `kokoro-web/src/interfaces/session-stream/session-shell.tsx`
  - Main page composition and ordering of hero/thread/todo/composer.
- Modify: `kokoro-web/src/interfaces/session-stream/components/composer.tsx`
  - Mode affordance, transport/failure labels, attach affordance behavior, mode-specific cues.
- Modify: `kokoro-web/src/interfaces/session-stream/components/process-block.tsx`
  - Mode-aware process disclosure and richer but controlled Thinking presentation.
- Modify: `kokoro-web/src/interfaces/session-stream/components/subagent-row.tsx`
  - Structured milestone display (status, role, latest milestone/summary).
- Modify: `kokoro-web/src/interfaces/session-stream/components/tool-call-row.tsx`
  - Ensure tool activity presentation fits the new hierarchy.
- Modify: `kokoro-web/src/interfaces/session-stream/components/todo-bar.tsx`
  - Clarify relationship between plan summary and inline execution details.
- Modify: `kokoro-web/src/interfaces/session-stream/components/session-rail.tsx`
  - Keep the rail aligned with demo-first main flow if any wording/interaction needs light adjustment.

### Likely state / application files
- Modify: `kokoro-web/src/interfaces/session-stream/hooks/use-conversation.ts`
  - Centralize mode-aware transport labels / failed-state labeling / settled-state behavior.
- Modify: `kokoro-web/src/application/session-stream-reducer.ts`
  - Only if needed for structured milestone derivation from existing subagent/tool state.
- Modify: `kokoro-web/src/application/conversation-store.ts`
  - Only if mode-aware persisted metadata or display summaries need one stable place.

### Styles
- Modify: `kokoro-web/src/app/styles/composer.css`
- Modify: `kokoro-web/src/app/styles/activity.css`
- Modify: `kokoro-web/src/app/styles/thread.css`
- Modify: `kokoro-web/src/app/styles/rail.css` (only if needed)

### Tests
- Modify: `kokoro-web/tests/interfaces/session-stream/session-shell.test.tsx`
- Modify: `kokoro-web/tests/interfaces/session-stream/process-block.test.tsx`
- Modify: `kokoro-web/tests/interfaces/session-stream/todo-bar.test.tsx`
- Modify: `kokoro-web/tests/application/session-stream-reducer.test.ts` (only if state derivation changes)
- Create: `kokoro-web/tests/interfaces/session-stream/subagent-row.test.tsx` (if structured milestone row grows beyond trivial markup)

### Docs / handoff
- Modify: `claude-progress.md`
- Modify: `tasks/todo.md`

---

### Task 1: Define the demo-grade main path and mode-aware labels in tests first

**Files:**
- Modify: `kokoro-web/tests/interfaces/session-stream/session-shell.test.tsx`
- Modify: `kokoro-web/tests/interfaces/session-stream/process-block.test.tsx`
- Modify: `kokoro-web/tests/interfaces/session-stream/todo-bar.test.tsx`

- [ ] **Step 1: Write a failing SessionShell test for mode-aware first-run experience**

Add a test that proves Fast and Thinking present different user-facing progress cues.

```tsx
it("shows a lighter progress label for Fast and a richer one for Thinking", () => {
  const startReply = vi.fn(instantReply((input) => `答：${input}`))
  render(<SessionShell startReply={startReply} />)

  fireEvent.change(screen.getByLabelText("对话输入"), {
    target: { value: "帮我规划一下" },
  })
  fireEvent.submit(screen.getByRole("form", { name: "消息编辑区" }))

  expect(screen.getByText(/快速回应中|快速整理中/)).toBeInTheDocument()

  fireEvent.click(screen.getByText("新对话"))
  fireEvent.click(screen.getByLabelText("切换模式"))
  fireEvent.click(screen.getByRole("menuitemradio", { name: /Thinking/ }))
  fireEvent.change(screen.getByLabelText("对话输入"), {
    target: { value: "帮我规划一下" },
  })
  fireEvent.submit(screen.getByRole("form", { name: "消息编辑区" }))

  expect(screen.getByText(/正在分步思考|正在深入分析/)).toBeInTheDocument()
})
```

- [ ] **Step 2: Run the focused SessionShell test to verify RED**

Run:
```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-web && bun run test tests/interfaces/session-stream/session-shell.test.tsx
```

Expected:
- FAIL because Fast and Thinking currently share the same visible transport/progress phrasing.

- [ ] **Step 3: Write a failing ProcessBlock test for mode-aware disclosure density**

Add a test proving Thinking retains richer process description while Fast stays compact.

```tsx
it("keeps Thinking process copy richer than Fast after settle", () => {
  const { rerender } = render(
    <ProcessBlock
      mode="fast"
      thinking="先查天气，再给建议。"
      toolCalls={[toolCall("get_weather")]}
      subagents={[subagent("weather-analyst", "分析天气与出行适宜度")]}
      live={false}
    />,
  )

  expect(screen.getByText(/思考过程/)).toBeInTheDocument()
  expect(screen.queryByText(/分步|阶段/)).toBeNull()

  rerender(
    <ProcessBlock
      mode="thinking"
      thinking="先查天气，再比较温度、风力与空气质量，最后汇总为建议。"
      toolCalls={[toolCall("get_weather")]}
      subagents={[subagent("weather-analyst", "分析天气与出行适宜度")]}
      live={false}
    />,
  )

  expect(screen.getByText(/分步|阶段|分析路径/)).toBeInTheDocument()
})
```

- [ ] **Step 4: Run the focused ProcessBlock test to verify RED**

Run:
```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-web && bun run test tests/interfaces/session-stream/process-block.test.tsx
```

Expected:
- FAIL because `ProcessBlock` currently has no mode-aware copy or disclosure behavior.

- [ ] **Step 5: Write a failing TodoBar test for “plan vs execution” separation clarity**

```tsx
it("labels the pinned plan bar as overview rather than duplicating execution detail", () => {
  render(
    <TodoBar
      mode="thinking"
      todos={[
        { content: "查询北京今天天气", status: "completed" },
        { content: "评估是否适合出门", status: "in_progress" },
      ]}
    />,
  )

  expect(screen.getByText(/计划总览|当前计划/)).toBeInTheDocument()
  expect(screen.queryByText(/工具调用/)).toBeNull()
})
```

- [ ] **Step 6: Run the focused TodoBar test to verify RED**

Run:
```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-web && bun run test tests/interfaces/session-stream/todo-bar.test.tsx
```

Expected:
- FAIL because the component currently has no mode-aware or “overview” distinction.

- [ ] **Step 7: Commit the test-only red stage for demo polish task 1**

```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-web && git add tests/interfaces/session-stream/session-shell.test.tsx tests/interfaces/session-stream/process-block.test.tsx tests/interfaces/session-stream/todo-bar.test.tsx && git commit -m "test: define demo polish mode-aware interaction behavior"
```

---

### Task 2: Implement mode-aware main-path polish in SessionShell and Composer

**Files:**
- Modify: `kokoro-web/src/interfaces/session-stream/session-shell.tsx`
- Modify: `kokoro-web/src/interfaces/session-stream/components/composer.tsx`
- Modify: `kokoro-web/src/interfaces/session-stream/hooks/use-conversation.ts`
- Test: `kokoro-web/tests/interfaces/session-stream/session-shell.test.tsx`

- [ ] **Step 1: Implement a single mode-aware presentation seam in `use-conversation.ts`**

Introduce one stable UI-facing descriptor instead of sprinkling `mode === "thinking"` throughout components.

```ts
export type ModePresentation = {
  transportLabel: string
  liveHint: string
  settledHint: string
  failedHint: string
}

export function modePresentation(mode: AgentMode, transport: ReplyMode | "error"): ModePresentation {
  if (mode === "thinking") {
    return {
      transportLabel:
        transport === "live"
          ? "Thinking · 深度思考中"
          : transport === "preview"
            ? "Thinking · 本地预览"
            : "Thinking · 启动失败",
      liveHint: "正在分步思考…",
      settledHint: "已完成深度思考",
      failedHint: "深度思考未能启动，请重试",
    }
  }
  return {
    transportLabel:
      transport === "live"
        ? "Fast · 快速回应中"
        : transport === "preview"
          ? "Fast · 本地预览"
          : "Fast · 启动失败",
    liveHint: "正在快速整理…",
    settledHint: "已快速整理",
    failedHint: "快速回应未能启动，请重试",
  }
}
```

- [ ] **Step 2: Thread the mode presentation into `SessionShell` and `Composer`**

Update `SessionShell` so the empty hero, transport row, and current-run feedback can reflect the chosen mode without duplicating logic.

```tsx
const presentation = modePresentation(mode, transportMode)

<Composer
  ...
  transportLabel={presentation.transportLabel}
  modeHint={isStreaming ? presentation.liveHint : hasFailed ? presentation.failedHint : presentation.settledHint}
/>
```

And add a lightweight mode hint slot in `ComposerProps` / JSX:

```tsx
type ComposerProps = {
  ...
  modeHint: string
}

<p className="kk-shell__transport">
  <span>{transportLabel}</span>
  <span className="kk-shell__transport-sep">·</span>
  <span>{modeHint}</span>
</p>
```

- [ ] **Step 3: Run the focused SessionShell tests to verify GREEN**

Run:
```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-web && bun run test tests/interfaces/session-stream/session-shell.test.tsx
```

Expected:
- PASS

- [ ] **Step 4: Refactor only for readability once green**

Keep the mode-presentation logic centralized. If a component needs more than one inline conditional for Fast/Thinking copy, extract that logic upward rather than duplicating it.

- [ ] **Step 5: Commit the main-path polish slice**

```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-web && git add src/interfaces/session-stream/session-shell.tsx src/interfaces/session-stream/components/composer.tsx src/interfaces/session-stream/hooks/use-conversation.ts tests/interfaces/session-stream/session-shell.test.tsx && git commit -m "feat: polish main chat path for fast and thinking modes"
```

---

### Task 3: Turn subagent output into a structured milestone stream

**Files:**
- Modify: `kokoro-web/src/interfaces/session-stream/components/process-block.tsx`
- Modify: `kokoro-web/src/interfaces/session-stream/components/subagent-row.tsx`
- Modify: `kokoro-web/src/interfaces/session-stream/components/tool-call-row.tsx`
- Optionally Modify: `kokoro-web/src/application/session-stream-reducer.ts`
- Test: `kokoro-web/tests/interfaces/session-stream/process-block.test.tsx`
- Create or Modify: `kokoro-web/tests/interfaces/session-stream/subagent-row.test.tsx`

- [ ] **Step 1: Write the failing structured-subagent-stream test**

```tsx
it("shows subagents as milestone rows rather than dumping raw stream text", () => {
  render(
    <ProcessBlock
      mode="thinking"
      thinking="先查天气，再做路线建议。"
      toolCalls={[]}
      subagents={[
        {
          id: "sub_1",
          name: "weather-analyst",
          description: "分析天气与出行适宜度",
          status: "running",
          milestone: "已完成天气读取，正在整理结论",
        },
      ]}
      live={true}
    />,
  )

  expect(screen.getByText("weather-analyst")).toBeInTheDocument()
  expect(screen.getByText("已完成天气读取，正在整理结论")).toBeInTheDocument()
  expect(screen.queryByText(/原始流式段落/)).toBeNull()
})
```

- [ ] **Step 2: Run the focused subagent/process tests to verify RED**

Run:
```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-web && bun run test tests/interfaces/session-stream/process-block.test.tsx tests/interfaces/session-stream/subagent-row.test.tsx
```

Expected:
- FAIL because subagents currently only expose a thinner row model without explicit milestone/summary affordances.

- [ ] **Step 3: Implement the minimal structured milestone rendering**

Keep the state stable and UI-facing. If needed, derive a “latest milestone” summary once in state logic rather than constructing ad-hoc strings in JSX.

Example UI shape for `subagent-row.tsx`:

```tsx
<div className={`kk-subagent kk-subagent--${subagent.status}`}>
  <div className="kk-subagent__head">
    <span className="kk-subagent__name">{subagent.name}</span>
    <span className="kk-subagent__state">{labelForStatus(subagent.status)}</span>
  </div>
  <p className="kk-subagent__role">{subagent.description}</p>
  {subagent.milestone ? <p className="kk-subagent__milestone">{subagent.milestone}</p> : null}
</div>
```

- [ ] **Step 4: Make the disclosure denser in Thinking and lighter in Fast**

Implement one explicit rule in `ProcessBlock`:
- Fast: default summary is shorter and more collapsed after settle
- Thinking: summary can preserve one extra milestone line after settle

Do not create separate components for each mode; keep one structure with mode-aware disclosure settings.

- [ ] **Step 5: Re-run the focused process tests to verify GREEN**

Run:
```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-web && bun run test tests/interfaces/session-stream/process-block.test.tsx tests/interfaces/session-stream/subagent-row.test.tsx
```

Expected:
- PASS

- [ ] **Step 6: Commit the structured subagent stream slice**

```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-web && git add src/interfaces/session-stream/components/process-block.tsx src/interfaces/session-stream/components/subagent-row.tsx src/interfaces/session-stream/components/tool-call-row.tsx tests/interfaces/session-stream/process-block.test.tsx tests/interfaces/session-stream/subagent-row.test.tsx src/application/session-stream-reducer.ts && git commit -m "feat: present subagents as structured milestone stream"
```

---

### Task 4: Clarify plan-vs-process hierarchy and polish visual language

**Files:**
- Modify: `kokoro-web/src/interfaces/session-stream/components/todo-bar.tsx`
- Modify: `kokoro-web/src/app/styles/activity.css`
- Modify: `kokoro-web/src/app/styles/composer.css`
- Modify: `kokoro-web/src/app/styles/thread.css`
- Modify: `kokoro-web/src/app/styles/rail.css` (only if required)
- Test: `kokoro-web/tests/interfaces/session-stream/todo-bar.test.tsx`

- [ ] **Step 1: Implement plan-overview language in `TodoBar`**

Make the pinned bar read like an overview, not an execution log.

```tsx
<span className="kk-todobar__eyebrow">当前计划</span>
<span>计划总览</span>
<span className="kk-todobar__count">{doneCount}/{todos.length}</span>
```

- [ ] **Step 2: Tune visual hierarchy in CSS**

Examples of the intended direction:
- answer bubble remains the strongest surface
- process block uses lighter background and smaller density
- transport row feels like calm metadata, not debug text
- Thinking mode can slightly expand process spacing/density without shifting the overall layout

Example CSS moves:

```css
.kk-process {
  background: color-mix(in srgb, var(--surface-soft) 62%, var(--surface) 38%);
}

.kk-process[data-mode="thinking"] .kk-process__body {
  gap: 0.55rem;
}

.kk-process[data-mode="fast"] .kk-process__body {
  gap: 0.35rem;
}

.kk-shell__transport {
  display: inline-flex;
  gap: 0.35rem;
  align-items: center;
}
```

- [ ] **Step 3: Run focused hierarchy tests and a full web gate check**

Run:
```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-web && bun run test tests/interfaces/session-stream/todo-bar.test.tsx tests/interfaces/session-stream/process-block.test.tsx tests/interfaces/session-stream/session-shell.test.tsx && bun run lint && bun run typecheck && bun run test
```

Expected:
- PASS

- [ ] **Step 4: Commit the hierarchy/visual polish slice**

```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-web && git add src/interfaces/session-stream/components/todo-bar.tsx src/app/styles/activity.css src/app/styles/composer.css src/app/styles/thread.css src/app/styles/rail.css tests/interfaces/session-stream/todo-bar.test.tsx tests/interfaces/session-stream/process-block.test.tsx tests/interfaces/session-stream/session-shell.test.tsx && git commit -m "feat: polish demo hierarchy for fast thinking and process flow"
```

---

### Task 5: Final verification, demo pass, and handoff updates

**Files:**
- Modify: `claude-progress.md`
- Modify: `tasks/todo.md`

- [ ] **Step 1: Run the full `kokoro-web` verification suite**

Run:
```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-web && bun run lint && bun run typecheck && bun run test
```

Expected:
- PASS

- [ ] **Step 2: Run a browser-level demo verification**

Use the local app path and visually confirm:
- empty hero feels coherent
- Fast and Thinking clearly read as different modes
- subagent/process display is structured and not spammy
- failed / preview / live states are understandable

Document what was seen in terms of user-visible behavior, not just “page loaded”.

- [ ] **Step 3: Update handoff docs**

Suggested `tasks/todo.md` updates:

```md
- [x] Polish the main chat path so the first-run demo is mode-aware and self-explanatory.
- [x] Differentiate Fast vs Thinking in user-facing pacing, status language, and process disclosure.
- [x] Present child/subagent activity as a structured milestone stream instead of raw stream spam.
```

Suggested `claude-progress.md` note:

```md
- 2026-06-06 demo polish pass: main path polished, Fast/Thinking differentiated in user-facing feedback, subagent activity rendered as structured milestone stream, and transport/failure language unified for demo readability.
```

- [ ] **Step 4: Commit the demo-polish docs and handoff updates**

```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro && git add claude-progress.md tasks/todo.md docs/superpowers/specs/2026-06-06-demo-polish-fast-thinking-design.md docs/superpowers/plans/2026-06-06-demo-polish-fast-thinking.md && git commit -m "docs: record demo polish plan and progress"
```

---

## Self-review

- The spec’s three core goals (main-path polish, mode differentiation, structured subagent stream) are each mapped to dedicated tasks.
- No placeholders remain: every step names exact files, commands, and intended behavior.
- The plan keeps DDD boundaries clean by concentrating this pass in `kokoro-web` unless a new stable UI-facing state seam is truly required.

Plan complete and saved to `docs/superpowers/plans/2026-06-06-demo-polish-fast-thinking.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
