# Repo-Local CLAUDE Overlay Design

- **Date:** 2026-06-01
- **Status:** approved-by-user
- **Scope:** `kokoro-web`, `kokoro-session`, `kokoro-agent`
- **Related:** `CLAUDE.md`, `docs/product/04-architecture/repository-boundaries.md`, `docs/protocol/README.md`, `kokoro-web/AGENTS.md`

---

## 1. Goal

Add thin, repo-local `CLAUDE.md` overlays for the three primary runtime repositories so future contributors can understand each repo’s purpose, stack-specific constraints, verification commands, and code-placement rules without weakening the root Kokoro governance.

The overlays should make the codebase easier to navigate with LSP/editor tooling, easier to change without cross-repo drift, and easier for multiple people to extend without re-learning the same boundaries from scratch.

---

## 2. Why this change is needed

The root `Kokoro/CLAUDE.md` already defines strong global rules around planning, schema strictness, testing, fail-loud behavior, and repository boundaries. That is the correct source of truth for system-wide governance.

What is missing is thin, local guidance inside the runtime repos themselves:

- `kokoro-web` currently has only a narrow Next.js warning through `AGENTS.md`
- `kokoro-session` has no local CLAUDE overlay
- `kokoro-agent` has no local CLAUDE overlay

As a result, contributors can still understand the global architecture, but they do not get repo-local reminders about:

- what belongs in that repo
- what layer a file should live in
- what stack-specific pitfalls matter there
- what exact verification commands should run after changes

This is especially important now because the current priority is the three-repo runtime chain:

- `kokoro-web` → Next.js UI + SSE/session-stream consumer
- `kokoro-session` → browser-facing session/SSE/replay contract owner
- `kokoro-agent` → Python worker + raw execution event producer

Other future middle-platform repos are not the current focus.

---

## 3. Recommended approach

### Chosen approach: thin overlays

Keep the root Kokoro governance in `Kokoro/CLAUDE.md`, and add short repo-local `CLAUDE.md` overlays that only document local constraints, local stack realities, and local verification expectations.

This is a **progressive disclosure** approach:

1. **Root CLAUDE** answers system-wide policy questions.
2. **Repo-local CLAUDE** answers “how do I work safely in this repo?”
3. **Repo-local AGENTS** remain for framework/tooling caveats when needed.

### Why this is the best option

- It preserves one global source of truth for architecture and governance.
- It avoids copy-pasting the same rules into every subrepo.
- It keeps local files short enough that contributors will actually read them.
- It improves LSP/editor navigation because the overlays explicitly reinforce where code belongs and how modules should stay small and purpose-specific.
- It matches the user’s preference for Claude Code-style progressive disclosure rather than giant all-in-one instruction files.

### Alternatives rejected

#### 1. Full self-contained subrepo handbooks
Rejected because they would duplicate too much of the root guidance and inevitably drift.

#### 2. No local overlays, only root rules
Rejected because contributors still need repo-local guidance for Next.js, Bun/TypeScript session wiring, and Python worker boundaries.

#### 3. One shared runtime instruction file imported everywhere
Rejected because the three repos have meaningfully different local stacks and pitfalls; one shared runtime overlay would become vague or bloated.

---

## 4. Layering model

### Root `Kokoro/CLAUDE.md` owns

- planning discipline
- schema strictness principles
- testing philosophy
- fail-loud expectations
- repository-boundary governance
- cross-repo contract discipline

### Repo-local `CLAUDE.md` owns

- repo purpose and non-goals
- critical local boundaries
- where code belongs inside that repo
- local verification commands
- local stack pitfalls

### Repo-local `AGENTS.md` owns

- framework/tooling caveats that are easier to express as operational notes
- example: `kokoro-web/AGENTS.md` keeping the Next.js warning

The repo-local overlays must **complement** the root policy, not weaken it.

---

## 5. Required structure for each repo-local CLAUDE overlay

Each overlay should follow the same progressive-disclosure order:

1. **Repo purpose**
   - what this repo owns
   - what it must not own

2. **Critical boundaries**
   - the most important architectural constraints for this repo

3. **Where code belongs**
   - how files should be placed by responsibility
   - how to keep modules narrow and LSP-friendly

4. **Verification checklist**
   - exact commands for this repo
   - when extra commands are required

5. **Local pitfalls**
   - the top few mistakes contributors are likely to make in that repo

This structure keeps the most important context first and details second.

---

## 6. Repo-specific content

### `kokoro-web`

The overlay should emphasize:

- this repo is the **Next.js UI and session-stream consumer**
- `kokoro-web` must not take on session orchestration or raw agent-event semantics
- transport envelope parsing belongs in infrastructure
- reducer/application code should stay transport-agnostic
- `use client` stays isolated to interactive entrypoints
- app-router, metadata, and layout decisions are framework-sensitive
- verification should normally include `npm run lint`, `npm run typecheck`, `npm run test`, and `npm run build` when route/layout/hydration-sensitive code changes
- Vitest runs in `jsdom`, so browser APIs may require explicit stubs in tests

### `kokoro-session`

The overlay should emphasize:

- this repo is the **browser-facing session/SSE/replay contract owner**
- `domain` stays pure, `application` orchestrates, `infrastructure` owns Redis/SSE/stream semantics, `interfaces` owns HTTP
- `src/main.ts` should remain wiring-only
- protocol shapes should not be duplicated across layers
- Redis key naming, replay, and stream semantics should stay centralized
- verification should include `bun test`, `bun run typecheck`, and `bun run lint`
- small, purpose-specific modules are preferred so the repo remains LSP-friendly and easier to reason about

### `kokoro-agent`

The overlay should emphasize:

- this repo is the **Python worker and raw execution-event producer**
- `worker.py` owns lifecycle/loop concerns; `run_agent.py` owns execution/orchestration
- boundary payloads should use explicit Pydantic models instead of drifting ad hoc dicts
- package layout under `src/kokoro_agent` should remain responsibility-first and narrow
- verification should include `pytest`, `ruff`, and `pyright` strict mode
- module growth should be handled by splitting files by responsibility rather than inflating single files

---

## 7. Non-goals

This change should **not**:

- redefine the root Kokoro governance
- duplicate entire sections of `Kokoro/CLAUDE.md`
- add support-repo guidance for future middle-platform repos yet
- move protocol ownership away from `docs/protocol/*`
- introduce new runtime architecture or code refactors

---

## 8. Verification strategy

After implementation:

1. Read all three repo-local `CLAUDE.md` files and confirm they follow the same thin-overlay structure.
2. Confirm none of them contradict root governance or repo-boundary docs.
3. Confirm `kokoro-web/CLAUDE.md` preserves the current `@AGENTS.md` inclusion so the Next.js caveat still applies.
4. Confirm each overlay includes exact verification commands appropriate to its local stack.
5. Confirm the guidance clearly reinforces the current three-repo priority and does not prematurely optimize for other future support repos.

---

## 9. Intended outcome

After this change, a contributor entering any of the three primary runtime repos should be able to answer quickly:

- what this repo is for
- what boundaries matter here
- where new code should go
- what commands prove the change is safe
- what local mistakes to avoid

That should make the overall codebase easier to understand, easier to keep clean, and more resilient to multi-contributor drift.