# i18n Admin Workbench Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a usable i18n admin workbench in `kokoro-web` using Ant Design, backed by the existing `kokoro-platform` i18n preview API.

**Architecture:** `kokoro-platform` remains the i18n data/API provider. `kokoro-web` adds a Next.js admin route that fetches the catalog payload server-side and renders a client-side Ant Design table workbench for language switching, search, filters, and detail inspection.

**Tech Stack:** Next.js App Router, React, TypeScript, Ant Design, Vitest, Testing Library, Playwright CLI.

---

## Chunk 1: Web Admin UI

### Task 1: Add Workbench Contract And Client Behavior

**Files:**
- Create: `kokoro-web/src/app/admin/i18n/i18n-workbench.tsx`
- Create: `kokoro-web/src/app/admin/i18n/page.tsx`
- Test: `kokoro-web/tests/app/admin-i18n-workbench.test.tsx`

- [ ] **Step 1: Write failing tests**

Cover language `Select`, search filtering, status filtering, and details drawer.

- [ ] **Step 2: Run focused test**

Run: `pnpm test tests/app/admin-i18n-workbench.test.tsx`
Expected: FAIL because the workbench component does not exist.

- [ ] **Step 3: Implement Ant Design workbench**

Use `Table`, `Select`, `Input.Search`, `Tag`, `Drawer`, `Descriptions`, `ConfigProvider`, `App`, and compact enterprise spacing.

- [ ] **Step 4: Run focused test**

Run: `pnpm test tests/app/admin-i18n-workbench.test.tsx`
Expected: PASS.

### Task 2: Add Ant Design Dependency And Global Reset

**Files:**
- Modify: `kokoro-web/package.json`
- Modify: `kokoro-web/src/app/layout.tsx`
- Modify: `kokoro-web/tests/setup.ts`

- [ ] **Step 1: Install `antd`**

Run: `pnpm add antd`

- [ ] **Step 2: Import Ant Design reset**

Import `antd/dist/reset.css` once from the root layout.

- [ ] **Step 3: Add jsdom browser API shims**

Provide minimal `matchMedia`, `ResizeObserver`, and `getComputedStyle` support needed by Ant Design tests.

### Task 3: Verify End To End

**Files:**
- Existing platform preview server
- New web admin route

- [ ] **Step 1: Run automated checks**

Run `pnpm test`, `pnpm typecheck`, and `pnpm lint` in `kokoro-web`; run platform checks from `kokoro-platform`.

- [ ] **Step 2: Run browser verification**

Start `kokoro-platform` i18n preview and `kokoro-web` dev server. Use Playwright headed browser to open `/admin/i18n`, switch language, search `用户`, open a row detail drawer, and capture screenshots.
