# Kokoro Mori Preview Studio Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create an independent `kokoro-mori` Next.js product repository with a working light-first music studio preview that establishes the Mori Create, Projects, Library, generation queue, candidate comparison, and persistent player surfaces.

**Architecture:** Mori owns all music domain types, page composition, brand tokens, audio preview fixtures, and provider-neutral interactions. It reuses browser-safe shared packages through package dependencies while keeping provider adapters and BFF routes outside the client. The first vertical slice is local-preview driven, so every screen is deterministic and testable without generating music or consuming provider credits.

**Tech Stack:** Next.js 16, React 19, TypeScript 5, Tailwind 4, CSS Modules, shadcn/Radix primitives, Vitest, Testing Library, Node.js 22, pnpm 11.2.2.

## Global Constraints

- Mori is a sibling product repository named `kokoro-mori`; the brand name is `Mori`, not `kokoro-music`.
- Default theme is light with warm off-white surfaces and low-contrast lavender/peach/mint gradients.
- The primary mental model is `Project-first`; candidates and versions are not chat messages.
- Create defaults to Smart mode; Custom controls are progressively disclosed.
- Studio only opens with an existing project and version reference.
- Browser requests use same-origin `/api/*`; external fields are `snake_case`; responses use `{data, meta}` or `{error, meta}`; writes include `Idempotency-Key`; async events use SSE and `Last-Event-ID`.
- No Suno/Tad private API, credential, token, provider task id, or provider-specific branch appears in the browser product.
- All generation actions in preview use fixtures and do not invoke a real provider.

---

### Task 1: Scaffold the sibling product repository

**Files:**
- Create: `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-mori/.gitignore`
- Create: `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-mori/package.json`
- Create: `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-mori/pnpm-workspace.yaml`
- Create: `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-mori/tsconfig.json`
- Create: `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-mori/next.config.ts`
- Create: `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-mori/postcss.config.mjs`
- Create: `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-mori/vitest.config.ts`
- Create: `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-mori/src/app/layout.tsx`
- Create: `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-mori/src/app/page.tsx`

**Interfaces:**
- Produces: a standalone Next app that can render `/` without a service dependency.

- [ ] **Step 1: Initialize the repository**

```bash
mkdir -p kokoro-mori/src/app kokoro-mori/src/features/mori kokoro-mori/src/ui/mori kokoro-mori/public/audio
git init -b main kokoro-mori
```

- [ ] **Step 2: Add dependency declarations**

Use the existing `kokoro/package.json` version floors for Next, React, TypeScript, Vitest, Testing Library, Tailwind, Radix, Lucide, and Zod. Add local package references to `../kokoro-web-shared/packages/i18n`, `../kokoro-web-shared/packages/web-core`, and `../kokoro-web-shared/packages/tsconfig` only as a local bootstrap bridge; source imports remain package imports.

- [ ] **Step 3: Add path aliases and test configuration**

`tsconfig.json` must define `@/*` → `src/*`, `strict: true`, `noEmit: true`, `moduleResolution: "bundler"`, and JSX React support. Vitest must run `tests/**/*.test.tsx` in `jsdom` with the Testing Library setup.

- [ ] **Step 4: Add the neutral app shell**

`layout.tsx` sets `lang="en"`, `metadata.title` to `Mori`, and imports `globals.css`. `page.tsx` renders `MoriWorkspace` from the feature layer and owns no music state.

- [ ] **Step 5: Verify the shell**

```bash
pnpm --dir kokoro-mori install
pnpm --dir kokoro-mori typecheck
```

Expected: exit 0 before the feature components are added.

- [ ] **Step 6: Commit the repository shell**

```bash
git -C kokoro-mori add .
git -C kokoro-mori commit -m "chore: scaffold Mori music studio repository"
```

### Task 2: Add the Mori domain model and deterministic preview fixtures

**Files:**
- Create: `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-mori/src/features/mori/domain.ts`
- Create: `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-mori/src/features/mori/preview-data.ts`
- Create: `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-mori/src/features/mori/preview-data.test.ts`

**Interfaces:**
- Produces: `Project`, `SongPlan`, `Generation`, `Candidate`, `Version`, `LibraryItem`, and `PlayerState` types; fixture data used by the UI.

- [ ] **Step 1: Write the domain tests**

```ts
import { describe, expect, it } from "vitest"
import { previewProject, previewCandidates, previewLibrary } from "./preview-data"

describe("Mori preview model", () => {
  it("keeps a project current version linked to a candidate-derived version", () => {
    expect(previewProject.currentVersionRef).toBe(previewCandidates[0]?.versionRef)
  })

  it("exposes library items as project or version records", () => {
    expect(previewLibrary.every((item) => item.kind === "project" || item.kind === "version")).toBe(true)
  })
})
```

- [ ] **Step 2: Implement narrow domain types**

Use opaque string refs and explicit literal status unions. `Version` is immutable and stores `sourceCandidateRef`; `Generation` stores `status`, `progress`, and `candidateRefs`; no type contains `provider_name` or a provider task id.

- [ ] **Step 3: Implement fixtures**

Create one project named `First Light`, one Song Plan, one succeeded generation, two candidates with different durations, one current version, three library items, and an idle player. Use stable refs such as `project_preview_first_light` and `version_preview_first_light_a`.

- [ ] **Step 4: Run the domain tests**

```bash
pnpm --dir kokoro-mori exec vitest run src/features/mori/preview-data.test.ts
```

Expected: PASS.

- [ ] **Step 5: Commit the domain slice**

```bash
git -C kokoro-mori add src/features/mori/domain.ts src/features/mori/preview-data.ts src/features/mori/preview-data.test.ts
git -C kokoro-mori commit -m "feat: add Mori music preview domain model"
```

### Task 3: Implement the light-first visual foundation

**Files:**
- Create: `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-mori/src/app/globals.css`
- Create: `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-mori/src/features/mori/mori-workspace.module.css`
- Create: `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-mori/src/features/mori/mori-tokens.ts`
- Create: `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-mori/src/features/mori/mori-tokens.test.ts`

**Interfaces:**
- Consumes: `Mori` visual values from the design baseline.
- Produces: CSS custom properties and layout classes used by all Mori surfaces.

- [ ] **Step 1: Write token assertions**

```ts
import { describe, expect, it } from "vitest"
import { MORI_TOKENS } from "./mori-tokens"

describe("Mori visual tokens", () => {
  it("uses a light-first surface and cool-warm gradient palette", () => {
    expect(MORI_TOKENS.background).toBe("#FBFAF8")
    expect(MORI_TOKENS.lavender).toBe("#EDE9FE")
    expect(MORI_TOKENS.peach).toBe("#FDE7DA")
    expect(MORI_TOKENS.mint).toBe("#E7F6EF")
  })
})
```

- [ ] **Step 2: Implement CSS variables**

Declare `--mori-background`, `--mori-surface`, `--mori-foreground`, `--mori-muted`, `--mori-border`, `--mori-primary`, `--mori-lavender`, `--mori-peach`, `--mori-mint`, and radius/shadow/motion variables. Set `color-scheme: light` and avoid a `.dark` default branch.

- [ ] **Step 3: Implement the three-column geometry**

Use a fixed rail, a minmax center canvas, and a collapsible inspector column. Reserve bottom player height in the shell so content never sits under the player. At viewport widths under 900px, collapse the inspector into an overlay and turn the rail into a top menu.

- [ ] **Step 4: Run token tests and lint**

```bash
pnpm --dir kokoro-mori exec vitest run src/features/mori/mori-tokens.test.ts
pnpm --dir kokoro-mori lint
```

Expected: PASS.

- [ ] **Step 5: Commit the visual foundation**

```bash
git -C kokoro-mori add src/app/globals.css src/features/mori/mori-workspace.module.css src/features/mori/mori-tokens.ts src/features/mori/mori-tokens.test.ts
git -C kokoro-mori commit -m "feat: add Mori light gradient visual foundation"
```

### Task 4: Build the Mori workspace surfaces

**Files:**
- Create: `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-mori/src/features/mori/mori-workspace.tsx`
- Create: `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-mori/src/features/mori/mori-workspace.test.tsx`
- Create: `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-mori/src/features/mori/components/mori-rail.tsx`
- Create: `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-mori/src/features/mori/components/create-canvas.tsx`
- Create: `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-mori/src/features/mori/components/inspector-panel.tsx`
- Create: `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-mori/src/features/mori/components/persistent-player.tsx`
- Create: `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-mori/src/features/mori/components/waveform.tsx`

**Interfaces:**
- Consumes: preview domain fixtures and `MoriWorkspace` layout classes.
- Produces: a working Create screen with navigation, Smart/Custom controls, queue/candidate inspector, and persistent player.

- [ ] **Step 1: Write interaction tests**

```tsx
import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MoriWorkspace } from "./mori-workspace"

it("starts in Smart Create mode with light workspace landmarks", () => {
  render(<MoriWorkspace />)
  expect(screen.getByRole("navigation", { name: "Mori" })).toBeInTheDocument()
  expect(screen.getByRole("heading", { name: /make something you can feel/i })).toBeInTheDocument()
  expect(screen.getByRole("tab", { name: "Smart" })).toHaveAttribute("aria-selected", "true")
  expect(screen.getByRole("region", { name: /generation queue/i })).toBeInTheDocument()
  expect(screen.getByRole("region", { name: /persistent player/i })).toBeInTheDocument()
})

it("reveals Custom controls without leaving Create", async () => {
  const user = userEvent.setup()
  render(<MoriWorkspace />)
  await user.click(screen.getByRole("tab", { name: "Custom" }))
  expect(screen.getByLabelText(/lyrics or instrumental/i)).toBeInTheDocument()
  expect(screen.getByLabelText(/style/i)).toBeInTheDocument()
  expect(screen.getByRole("button", { name: /reference audio/i })).toBeInTheDocument()
})
```

- [ ] **Step 2: Implement Rail**

Render brand `Mori`, `New creation`, Create, Projects, Library, and project-context labels only when a project is selected. Keep the global list to three entries.

- [ ] **Step 3: Implement Create Canvas**

Smart shows one prompt textarea, a Song Plan preview hint, and a gradient `Generate` button. Custom adds Lyrics/Instrumental, Style, Reference audio, Voice, Duration, and Advanced controls inside a disclosure panel. The submit handler only updates the local preview queue state.

- [ ] **Step 4: Implement Queue and Inspector**

Render `Preparing`, `Generating`, `Ready`, and `Failed` fixture states with an accessible status label. Ready state shows two candidates with play buttons, duration, version ref, and `Set as current version` action.

- [ ] **Step 5: Implement Persistent Player and Waveform**

Use a deterministic CSS/SVG waveform, not an audio provider. Player actions update `PlayerState` locally and expose `aria-label` values for play/pause, seek, volume, and close.

- [ ] **Step 6: Run component tests**

```bash
pnpm --dir kokoro-mori exec vitest run src/features/mori/mori-workspace.test.tsx
```

Expected: PASS with no network calls.

- [ ] **Step 7: Commit the first UI vertical slice**

```bash
git -C kokoro-mori add src/features/mori
git -C kokoro-mori commit -m "feat: add Mori create workspace preview"
```

### Task 5: Add page-level IA fixtures for Projects and Library

**Files:**
- Create: `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-mori/src/app/projects/page.tsx`
- Create: `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-mori/src/app/library/page.tsx`
- Create: `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-mori/src/features/mori/project-list.tsx`
- Create: `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-mori/src/features/mori/library-list.tsx`
- Test: `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-mori/src/features/mori/project-library.test.tsx`

**Interfaces:**
- Consumes: `previewProject` and `previewLibrary` from Task 2.
- Produces: predictable `/projects` and `/library` pages using the same Rail and visual tokens as Create.

- [ ] **Step 1: Write findability tests**

```tsx
import { render, screen } from "@testing-library/react"
import { ProjectsPageContent } from "./project-list"
import { LibraryPageContent } from "./library-list"

it("makes project continuation information findable", () => {
  render(<ProjectsPageContent />)
  expect(screen.getByText("Continue creating")).toBeInTheDocument()
  expect(screen.getByText("Current version")).toBeInTheDocument()
  expect(screen.getByText("Last activity")).toBeInTheDocument()
})

it("keeps library filters local and provider-neutral", () => {
  render(<LibraryPageContent />)
  for (const label of ["All", "Projects", "Versions", "Lyrics", "Exports"]) {
    expect(screen.getByRole("button", { name: label })).toBeInTheDocument()
  }
  expect(screen.queryByText(/suno|tad/i)).not.toBeInTheDocument()
})
```

- [ ] **Step 2: Implement Projects**

Use project cards with cover gradient, title, current version, candidate count, and Continue action. A project card navigates to `/projects/{project_ref}` using an opaque ref.

- [ ] **Step 3: Implement Library**

Use a filterable grid/list fixture with stable labels and empty state. Keep the filter bar local to Library rather than promoting filters to global navigation.

- [ ] **Step 4: Run page tests and build**

```bash
pnpm --dir kokoro-mori exec vitest run src/features/mori/project-library.test.tsx
pnpm --dir kokoro-mori build
```

Expected: PASS and a successful production build.

- [ ] **Step 5: Commit page IA**

```bash
git -C kokoro-mori add src/app/projects src/app/library src/features/mori
git -C kokoro-mori commit -m "feat: add Mori projects and library surfaces"
```

### Task 6: Add contract-ready client seams without a provider

**Files:**
- Create: `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-mori/src/lib/mori-api.ts`
- Create: `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-mori/src/features/mori/generation-controller.ts`
- Create: `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-mori/src/features/mori/generation-controller.test.ts`

**Interfaces:**
- Produces: typed client seams for future `/api/v1` contract integration while preview remains fixture-backed.

- [ ] **Step 1: Write API shape tests**

Assert that `createGenerationRequest` returns `prompt`, `lyrics`, `style`, `reference_asset_refs`, `voice_ref`, `duration_seconds`, and `mode` in `snake_case`, and never returns a provider key.

- [ ] **Step 2: Implement request types and controller**

`mori-api.ts` defines `ApiSuccess<T>`, `ApiError`, `GenerationCreateInput`, `GenerationReceipt`, and an injectable `MoriApi` interface. `generation-controller.ts` accepts either a preview adapter or future HTTP adapter and always exposes `queued`, `generating`, `succeeded`, `failed`, `cancelled`, and `expired` states.

- [ ] **Step 3: Implement preview adapter**

The preview adapter returns a deterministic receipt and emits local state transitions; it never calls `fetch` and never generates audio.

- [ ] **Step 4: Run contract seam tests**

```bash
pnpm --dir kokoro-mori exec vitest run src/features/mori/generation-controller.test.ts
pnpm --dir kokoro-mori typecheck
pnpm --dir kokoro-mori lint
```

Expected: PASS.

- [ ] **Step 5: Commit the contract seam**

```bash
git -C kokoro-mori add src/lib/mori-api.ts src/features/mori/generation-controller.ts src/features/mori/generation-controller.test.ts
git -C kokoro-mori commit -m "feat: add provider-neutral Mori generation seam"
```

### Task 7: Verify the full Mori preview and record evidence

**Files:**
- Create: `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-mori/ACCEPTANCE.md`
- Create: `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-mori/docs/README.md`

**Interfaces:**
- Consumes: all tasks above.
- Produces: human-readable acceptance evidence for the first Mori preview slice.

- [ ] **Step 1: Run the full check**

```bash
pnpm --dir kokoro-mori lint
pnpm --dir kokoro-mori typecheck
pnpm --dir kokoro-mori test
pnpm --dir kokoro-mori build
```

- [ ] **Step 2: Run the local preview**

```bash
pnpm --dir kokoro-mori dev
```

Open `/`, `/projects`, and `/library`. Verify light background, three-column desktop layout, Custom disclosure, candidate comparison, persistent player, and responsive inspector collapse.

- [ ] **Step 3: Record evidence**

`ACCEPTANCE.md` records exact commands, result summaries, and the fixture-only boundary. `docs/README.md` links the design baseline and states the next gate is the full API contract before provider integration.

- [ ] **Step 4: Commit acceptance evidence**

```bash
git -C kokoro-mori add ACCEPTANCE.md docs/README.md
git -C kokoro-mori commit -m "docs: record Mori preview acceptance"
```
