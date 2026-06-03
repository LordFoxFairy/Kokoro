# Minimal Web Shell Refinement Design

- **Date:** 2026-06-02
- **Status:** approved-in-conversation
- **Scope:** `kokoro-web` minimal first-screen shell refinement only
- **Related:** `docs/superpowers/specs/2026-05-29-kokoro-web-design.md`, `docs/superpowers/specs/2026-05-29-three-repo-demo-slice-design.md`, `docs/product/04-architecture/repository-boundaries.md`, `docs/protocol/README.md`

---

## 1. Goal

Refine the initial `kokoro-web` shell so the first screen matches the current minimal product direction more closely: fewer premature surfaces, a Gemini-inspired but Kokoro-branded left rail, and a simpler chat composer that supports the first closed loop without marketing or over-designed extras.

The result should feel intentional, calm, and immediately understandable while staying tightly scoped to the current three-repo priority:

- `kokoro-web` owns the UI shell
- `kokoro-session` owns the browser-facing session contract
- `kokoro-agent` owns raw execution events

This change is a UI/layout refinement, not a new protocol or session behavior change.

---

## 2. What prompted the change

The current shell direction is too wide for the first closed loop:

- the left rail contains more than is needed right now
- the center area risks drifting into marketing/promo territory
- the composer details were not aligned closely enough with the Gemini interaction pattern the user wants to reference
- some controls were being exposed too aggressively in the default state

The user explicitly narrowed the first-screen requirements:

- left rail should keep only the current top block, new chat, search, and a bottom user placeholder
- marketing content should not be shown yet
- the chat/composer details should be closer to Gemini’s interaction model
- mode text like `Fast` / `Thinking` should remain visible by default, but the stronger button-like treatment should appear only on hover/focus
- the bottom user placeholder should follow a larger Gemini-like card layout

---

## 3. Recommended approach

### Chosen approach: Gemini-inspired minimal shell, not full Gemini imitation

Keep the page structure extremely small and focus only on the first closed loop:

1. minimal left rail
2. large central question copy
3. minimal composer with restrained progressive disclosure

The shell should borrow interaction patterns from Gemini where they help clarity, but should not copy every surface or introduce controls that the current Kokoro runtime does not need yet.

### Why this is the best option

- It respects the user’s request to finish the smallest useful loop sooner.
- It improves visual clarity without adding new product scope.
- It keeps `kokoro-web` in its role as a UI consumer rather than leaking session/agent concerns upward.
- It reduces the amount of placeholder UI that would need to be reworked later.

### Alternatives rejected

#### 1. Keep the existing broader shell and trim later
Rejected because it leaves too much premature structure in place and slows convergence on the first usable experience.

#### 2. Fully imitate Gemini’s full screen
Rejected because it would add surfaces and interaction expectations that Kokoro does not need yet.

#### 3. Make the first screen almost empty
Rejected because the shell still needs clear structure and a welcoming first interaction point.

---

## 4. Locked layout decisions

### Left rail

Keep only these four elements:

1. Kokoro logo / brand block at the top
2. `新对话` entry
3. `搜索` row
4. bottom user placeholder card

Do not include:

- marketing/promo content
- extra navigation blocks
- recommendation cards
- history/detail sections beyond what is required for the first loop

### Bottom user placeholder

Use a larger Gemini-inspired card treatment rather than a tiny footer chip:

- larger rounded container
- larger avatar placeholder circle
- two text lines: current user label + placeholder sublabel

This is still a placeholder, not a profile feature.

### Center area

Keep only a large centered question headline and small subtitle.

The center should not contain:

- marketing copy
- feature tiles
- onboarding cards
- recommendation modules

### Composer

Use the previously chosen **B-style** overall structure as the base, but refine the interaction rules:

- `Fast` / `Thinking` style mode text is visible by default
- microphone is visible by default
- send button is visible by default
- the mode selector becomes more obviously button-like on hover/focus, rather than appearing from nothing
- the `+` affordance may remain visually present, but its behavior stays placeholder-only for this slice

This preserves the Gemini-like progressive disclosure the user wants:

- the control is present
- the stronger chrome is conditional
- the first-screen default state stays calm and less noisy

---

## 5. Interaction rules

### Mode selector behavior

Default state:
- mode text is visible (`Fast` in the first screen)
- treatment is light and not over-emphasized

Hover/focus state:
- the mode area gains the stronger chip/button appearance
- this should work for both pointer hover and keyboard/input focus
- mobile/non-hover contexts should still be able to expose the control via focus/active behavior

### Add (`+`) affordance

For this slice, it remains a **visual placeholder** only.

That means:
- keep the affordance in the layout if it helps the intended shell shape
- do not expand into real upload/menu flows yet
- do not add marketing or extra option groups just because the button exists

### Composer scope

The composer for this refinement is still text-first.

Do not expand this slice into:
- working upload flows
- real voice input
- multi-mode tool menus
- rich onboarding flows

---

## 6. Architecture constraints

This refinement must stay inside `kokoro-web` UI structure unless a bug forces otherwise.

It must not:
- introduce new session protocol fields
- change `kokoro-session` contract ownership
- change `kokoro-agent` event semantics
- move browser-facing protocol parsing out of the existing infrastructure boundary

`kokoro-web` should continue to keep:
- transport parsing in infrastructure
- state folding/orchestration in application
- components/layout in interfaces/app

---

## 7. Files likely to change

Primary candidates inside `kokoro-web`:

- `src/interfaces/session-stream/session-shell.tsx`
- any closely related presentational UI modules used by that shell
- possibly small style/helper files if needed for the refined shell treatment

This refinement should avoid broad structural rewrites. The goal is to tighten the shell, not re-architect the frontend.

---

## 8. Verification strategy

After implementation:

1. visually confirm the left rail now contains only the four locked elements
2. confirm marketing/promotional content is absent
3. confirm the center area only contains the large question copy and subtitle
4. confirm the composer default state keeps mode text, mic, and send visible
5. confirm the stronger chip/button treatment appears only on hover/focus for the mode selector
6. confirm no new session/agent responsibilities leaked into the web layer
7. run the relevant `kokoro-web` verification commands:
   - `npm run lint`
   - `npm run typecheck`
   - `npm run test`
   - `npm run build` if app/layout/hydration-sensitive code changes

---

## 9. Intended outcome

The first Kokoro screen should feel more finished by doing less:

- fewer premature surfaces
- clearer first interaction
- calmer composer
- better alignment with the desired Gemini-style interaction cues
- stronger focus on the current three-repo closed loop rather than future features

This should produce a shell that is easier to trust, easier to implement cleanly, and easier to evolve without undoing unnecessary earlier design decisions.