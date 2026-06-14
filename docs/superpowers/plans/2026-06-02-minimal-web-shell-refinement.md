# Minimal Web Shell Refinement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refine `kokoro-web` into the approved minimal first-screen shell: minimal left rail, large center question copy, Gemini-inspired user placeholder card, and a calmer B-style composer with `Fast` / `Thinking` visible by default and stronger chip chrome only on hover/focus.

**Architecture:** Keep the refinement mostly inside `src/interfaces/session-stream/session-shell.tsx` and shared shell styling in `src/app/globals.css`, because the current first screen is concentrated there. Preserve the three-repo boundary model: this is a UI/layout refinement inside `kokoro-web`, not a session/agent protocol change, and keep transport parsing/reducer behavior where it already belongs.

**Tech Stack:** Next.js 16 App Router, React 19, TypeScript, Tailwind CSS, Vitest, Testing Library, jsdom

---

### Task 1: Lock the refined shell layout with a failing UI test

**Files:**
- Modify: `/Users/yuri/WebstormProjects/Kokoro/kokoro-web/tests/interfaces/session-stream/session-shell.test.tsx`
- Reference: `/Users/yuri/WebstormProjects/Kokoro/kokoro-web/src/interfaces/session-stream/session-shell.tsx`

- [ ] **Step 1: Replace the current shell smoke test with an assertion set that matches the approved minimal shell**

```tsx
import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"

import { SessionShell } from "@/interfaces/session-stream/session-shell"

describe("SessionShell", () => {
  it("renders the approved minimal first-screen shell", () => {
    render(<SessionShell />)

    expect(screen.getByText("Kokoro")).toBeInTheDocument()
    expect(screen.getByText("新对话")).toBeInTheDocument()
    expect(screen.getByText("搜索")).toBeInTheDocument()
    expect(screen.getByText("当前用户")).toBeInTheDocument()

    expect(screen.getByRole("heading", { name: "今天想做什么？" })).toBeInTheDocument()
    expect(screen.getByText("不急，先把想法说给我")).toBeInTheDocument()

    expect(screen.getByText("把想说的告诉我。")).toBeInTheDocument()
    expect(screen.getAllByText("Fast").length).toBeGreaterThan(0)

    expect(screen.queryByText("A2UI artifact preview")).not.toBeInTheDocument()
    expect(screen.queryByText("Protocol-first chat shell for AGUI + SSE replay.")).not.toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Run the shell test to verify RED**

Run:
```bash
cd /Users/yuri/WebstormProjects/Kokoro/kokoro-web && npm test -- tests/interfaces/session-stream/session-shell.test.tsx
```
Expected: FAIL because the current shell still renders the older status/artifact layout instead of the approved minimal shell.

- [ ] **Step 3: Commit the failing shell test**

```bash
cd /Users/yuri/WebstormProjects/Kokoro/kokoro-web
git add tests/interfaces/session-stream/session-shell.test.tsx
git commit -m "test: lock minimal web shell layout"
```

### Task 2: Implement the minimal left rail, center copy, and Gemini-style user placeholder card

**Files:**
- Modify: `/Users/yuri/WebstormProjects/Kokoro/kokoro-web/src/interfaces/session-stream/session-shell.tsx`
- Modify: `/Users/yuri/WebstormProjects/Kokoro/kokoro-web/src/app/globals.css`
- Test: `/Users/yuri/WebstormProjects/Kokoro/kokoro-web/tests/interfaces/session-stream/session-shell.test.tsx`

- [ ] **Step 1: Replace the old two-card shell layout in `session-shell.tsx` with the approved minimal structural markup**

```tsx
return (
  <main className="kk-shell">
    <aside className="kk-rail">
      <div className="kk-rail__brand">
        <div className="kk-rail__brand-mark">心</div>
        <div>
          <p className="kk-rail__brand-title">Kokoro</p>
          <p className="kk-rail__brand-subtitle">こころ</p>
        </div>
      </div>

      <button className="kk-rail__new-chat" type="button">
        <span aria-hidden>＋</span>
        <span>新对话</span>
      </button>

      <div className="kk-rail__search" role="search">
        <span aria-hidden>⌕</span>
        <span>搜索</span>
        <span className="kk-rail__search-shortcut">⌘K</span>
      </div>

      <div className="kk-rail__user-card">
        <div className="kk-rail__user-avatar" aria-hidden />
        <div>
          <p className="kk-rail__user-name">当前用户</p>
          <p className="kk-rail__user-meta">placeholder</p>
        </div>
      </div>
    </aside>

    <section className="kk-shell__main">
      <div className="kk-shell__hero">
        <h1 className="kk-shell__headline">今天想做什么？</h1>
        <p className="kk-shell__subhead">不急，先把想法说给我</p>
      </div>

      <div className="kk-shell__composer-wrap">
        {/* composer inserted in Task 3 */}
      </div>
    </section>
  </main>
)
```

- [ ] **Step 2: Add the minimal shell layout and user-card styles to `globals.css`**

```css
.kk-shell {
  display: grid;
  min-height: 100vh;
  grid-template-columns: 300px minmax(0, 1fr);
  background: var(--background);
}

.kk-rail {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  border-right: 1px solid var(--border-soft);
  padding: 1.5rem 1rem;
  background: color-mix(in srgb, var(--background) 88%, white 12%);
}

.kk-rail__brand {
  display: flex;
  align-items: center;
  gap: 0.875rem;
  padding: 0.5rem;
}

.kk-rail__brand-mark {
  display: flex;
  height: 3rem;
  width: 3rem;
  align-items: center;
  justify-content: center;
  border-radius: 0.9rem;
  background: var(--brand-wood);
  color: #fffdf9;
}

.kk-rail__brand-title {
  font-size: 1.5rem;
  color: var(--foreground);
}

.kk-rail__brand-subtitle {
  font-size: 0.875rem;
  letter-spacing: 0.2em;
  color: rgba(43, 37, 32, 0.45);
}

.kk-rail__new-chat,
.kk-rail__search,
.kk-rail__user-card {
  border-radius: 1.5rem;
}

.kk-rail__new-chat {
  display: flex;
  align-items: center;
  gap: 0.875rem;
  border: 1px solid var(--border-soft);
  background: var(--surface);
  padding: 1.15rem 1.25rem;
  color: var(--foreground);
}

.kk-rail__search {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--surface-soft);
  padding: 1.15rem 1.25rem;
  color: rgba(43, 37, 32, 0.68);
}

.kk-rail__search-shortcut {
  border: 1px solid var(--border-soft);
  border-radius: 0.75rem;
  padding: 0.2rem 0.55rem;
  font-size: 0.8125rem;
}

.kk-rail__user-card {
  margin-top: auto;
  display: flex;
  align-items: center;
  gap: 1rem;
  border: 1px solid color-mix(in srgb, var(--border-soft) 65%, white 35%);
  background: color-mix(in srgb, var(--surface-soft) 82%, white 18%);
  padding: 1.1rem 1.2rem;
}

.kk-rail__user-avatar {
  height: 4.5rem;
  width: 4.5rem;
  border-radius: 999px;
  background: color-mix(in srgb, var(--brand-wood-soft) 55%, var(--brand-wood) 45%);
}

.kk-rail__user-name {
  font-size: 1.375rem;
  color: var(--foreground);
}

.kk-rail__user-meta {
  margin-top: 0.2rem;
  font-size: 1rem;
  color: rgba(43, 37, 32, 0.42);
}

.kk-shell__main {
  display: flex;
  min-width: 0;
  flex-direction: column;
}

.kk-shell__hero {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  text-align: center;
}

.kk-shell__headline {
  font-size: clamp(3.5rem, 6vw, 5.75rem);
  line-height: 1.05;
  color: color-mix(in srgb, var(--foreground) 84%, var(--brand-wood) 16%);
}

.kk-shell__subhead {
  margin-top: 1rem;
  font-size: clamp(1.4rem, 2.2vw, 1.875rem);
  color: color-mix(in srgb, var(--brand-wood) 62%, white 38%);
}
```

- [ ] **Step 3: Re-run the shell test to check GREEN for the layout-only part**

Run:
```bash
cd /Users/yuri/WebstormProjects/Kokoro/kokoro-web && npm test -- tests/interfaces/session-stream/session-shell.test.tsx
```
Expected: either PASS already, or fail only because the composer markup from Task 3 is not in place yet.

- [ ] **Step 4: Commit the layout refinement**

```bash
cd /Users/yuri/WebstormProjects/Kokoro/kokoro-web
git add src/interfaces/session-stream/session-shell.tsx src/app/globals.css tests/interfaces/session-stream/session-shell.test.tsx
git commit -m "feat: refine minimal shell layout"
```

### Task 3: Implement the calmer Gemini-inspired composer behavior

**Files:**
- Modify: `/Users/yuri/WebstormProjects/Kokoro/kokoro-web/src/interfaces/session-stream/session-shell.tsx`
- Modify: `/Users/yuri/WebstormProjects/Kokoro/kokoro-web/src/app/globals.css`
- Test: `/Users/yuri/WebstormProjects/Kokoro/kokoro-web/tests/interfaces/session-stream/session-shell.test.tsx`

- [ ] **Step 1: Extend the shell test so it checks the refined composer defaults**

```tsx
expect(screen.getByText("Fast")).toBeInTheDocument()
expect(screen.getByLabelText("语音输入")).toBeInTheDocument()
expect(screen.getByLabelText("发送消息")).toBeInTheDocument()
expect(screen.getByLabelText("附加内容")).toBeInTheDocument()
```

- [ ] **Step 2: Run the shell test to verify RED for composer details**

Run:
```bash
cd /Users/yuri/WebstormProjects/Kokoro/kokoro-web && npm test -- tests/interfaces/session-stream/session-shell.test.tsx
```
Expected: FAIL because the current shell does not yet render the approved composer controls and accessible labels.

- [ ] **Step 3: Replace the composer placeholder with the approved B-style markup**

```tsx
<div className="kk-shell__composer-wrap">
  <form className="kk-composer" aria-label="开始新对话">
    <button className="kk-composer__add" type="button" aria-label="附加内容">
      +
    </button>

    <div className="kk-composer__input-copy">把想说的告诉我。</div>

    <button className="kk-composer__mode" type="button" aria-label="切换模式">
      <span>Fast</span>
      <span aria-hidden>▾</span>
    </button>

    <button className="kk-composer__mic" type="button" aria-label="语音输入">
      <span aria-hidden>🎤</span>
    </button>

    <button className="kk-composer__send" type="submit" aria-label="发送消息">
      <span aria-hidden>↑</span>
    </button>
  </form>
</div>
```

- [ ] **Step 4: Add the hover/focus-only mode-chip enhancement styles**

```css
.kk-shell__composer-wrap {
  display: flex;
  justify-content: center;
  padding: 0 2rem 1.75rem;
}

.kk-composer {
  display: flex;
  width: min(980px, 100%);
  align-items: center;
  gap: 0.9rem;
  border: 2px solid color-mix(in srgb, var(--brand-wood) 72%, var(--border-soft) 28%);
  border-radius: 2rem;
  background: var(--surface);
  padding: 1rem 1.15rem;
  box-shadow: 0 10px 28px rgba(139, 111, 71, 0.12);
}

.kk-composer__add,
.kk-composer__mic,
.kk-composer__send,
.kk-composer__mode {
  border: 0;
  background: transparent;
  color: var(--foreground);
}

.kk-composer__add {
  display: flex;
  height: 2.75rem;
  width: 2.75rem;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: color-mix(in srgb, var(--brand-wood-soft) 82%, white 18%);
  color: var(--brand-wood);
  font-size: 1.6rem;
}

.kk-composer__input-copy {
  min-width: 0;
  flex: 1;
  color: rgba(43, 37, 32, 0.58);
  font-size: 1.25rem;
}

.kk-composer__mode {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  border-radius: 999px;
  padding: 0.55rem 0.25rem;
  color: color-mix(in srgb, var(--foreground) 78%, var(--brand-wood) 22%);
  transition: background-color 120ms ease, padding 120ms ease, box-shadow 120ms ease;
}

.kk-composer:hover .kk-composer__mode,
.kk-composer:focus-within .kk-composer__mode {
  padding: 0.7rem 1rem;
  background: color-mix(in srgb, var(--surface-soft) 82%, white 18%);
  box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--border-soft) 82%, white 18%);
}

.kk-composer__mic {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.6rem;
}

.kk-composer__send {
  display: flex;
  height: 2.75rem;
  width: 2.75rem;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: #9fd1ff;
  font-size: 1.35rem;
}
```

- [ ] **Step 5: Re-run the shell test and verify GREEN**

Run:
```bash
cd /Users/yuri/WebstormProjects/Kokoro/kokoro-web && npm test -- tests/interfaces/session-stream/session-shell.test.tsx
```
Expected: PASS.

- [ ] **Step 6: Commit the composer refinement**

```bash
cd /Users/yuri/WebstormProjects/Kokoro/kokoro-web
git add src/interfaces/session-stream/session-shell.tsx src/app/globals.css tests/interfaces/session-stream/session-shell.test.tsx
git commit -m "feat: refine shell composer behavior"
```

### Task 4: Verify the refined shell and keep the runtime boundaries intact

**Files:**
- Reference: `/Users/yuri/WebstormProjects/Kokoro/kokoro-web/src/application/session-stream-preview.ts`
- Reference: `/Users/yuri/WebstormProjects/Kokoro/kokoro-web/tests/application/session-stream-preview.test.ts`
- Reference: `/Users/yuri/WebstormProjects/Kokoro/kokoro-web/tests/application/session-stream-reducer.test.ts`

- [ ] **Step 1: Run the shell test plus the existing stream/reducer safety net**

Run:
```bash
cd /Users/yuri/WebstormProjects/Kokoro/kokoro-web && npm test -- tests/interfaces/session-stream/session-shell.test.tsx tests/application/session-stream-preview.test.ts tests/application/session-stream-reducer.test.ts
```
Expected: PASS across all files, proving the UI refinement did not break existing session-stream consumer behavior.

- [ ] **Step 2: Run lint and typecheck**

Run:
```bash
cd /Users/yuri/WebstormProjects/Kokoro/kokoro-web && npm run lint && npm run typecheck
```
Expected: both commands PASS.

- [ ] **Step 3: Run a production build because the shell touches app-facing UI and hydration-sensitive client markup**

Run:
```bash
cd /Users/yuri/WebstormProjects/Kokoro/kokoro-web && npm run build
```
Expected: PASS with a successful Next.js production build.

- [ ] **Step 4: Commit final shell verification state**

If Tasks 1–3 already produced the intended commits and no extra code changed in this verification task, record that no additional commit is needed.

If you had to make a last wording or accessibility fix during verification, then commit it with:

```bash
cd /Users/yuri/WebstormProjects/Kokoro/kokoro-web
git add src/interfaces/session-stream/session-shell.tsx src/app/globals.css tests/interfaces/session-stream/session-shell.test.tsx
git commit -m "fix: polish minimal shell refinement"
```

---

## Self-review

- Spec coverage: the plan covers every approved layout decision from the design doc — minimal left rail, big center copy, Gemini-inspired user placeholder card, B-style composer, always-visible `Fast` text and mic, hover/focus-only stronger mode-chip chrome, and no marketing/extra surfaces.
- Placeholder scan: no TBD/TODO placeholders remain; all files, commands, and code snippets are explicit.
- Type consistency: the plan consistently treats this as a `kokoro-web` UI-only refinement and does not introduce contradictory session/agent ownership changes.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-02-minimal-web-shell-refinement.md`. Two execution options:

1. Subagent-Driven (recommended) - I dispatch a fresh subagent per task, review between tasks, fast iteration

2. Inline Execution - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?