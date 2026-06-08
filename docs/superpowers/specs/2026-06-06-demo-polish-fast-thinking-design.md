# Demo Polish, Fast/Thinking Differentiation, and Chat Interaction Design

## Context

Current baseline after the execution-style contract pass:
- `kokoro-web` already sends the selected `fast | thinking` mode into the live run request path.
- `kokoro-session` validates `execution_style` as `fast | thinking` and rejects invalid values fail-loud.
- `kokoro-agent` resolves execution behavior per run, and the current `glm-5` path already differentiates `fast` vs `thinking` at runtime.

So the backend contract is no longer the blocker.

The remaining gap is now **presentation, interaction, and demo readability**:
- the product still does not make the difference between Fast and Thinking sufficiently legible to a first-time viewer;
- child-agent/subagent activity needs a better display strategy;
- several conversation states (`live`, `preview`, `failed`, `settled`) still feel more technically correct than experientially polished;
- the overall chat flow is functional, but not yet demo-grade in terms of clarity, pacing, and trust.

## Goal

Turn the current shell into a **demo-grade conversation experience** where:
1. the main path from first screen to final answer feels intentional and smooth;
2. Fast vs Thinking are clearly distinguishable in user-facing behavior, not just backend configuration;
3. subagent activity is visible enough to build trust, but not noisy enough to overwhelm the conversation;
4. state transitions (live / failed / preview / completed) are self-explanatory and visually coherent.

## Core design decision

### Chosen focus order

This polish pass will prioritize:
1. **Main chat path** (`empty → choose mode → send → see progress → receive answer → settle`)
2. **Fast / Thinking differentiation**
3. **Structured subagent activity stream**

This means we will *not* begin by over-expanding tool/subagent detail. The main path must read cleanly first; only then should deeper process visibility be layered in.

## Approaches considered

### Approach A — Main-path-first polish with mode differentiation and structured process stream **(recommended)**

- polish the first-run conversation path first
- make Fast / Thinking feel different in pacing and information density
- show subagent progress as structured milestones rather than full internal streams

**Pros**
- strongest demo value
- easiest for first-time viewers to understand
- preserves a clean main conversation
- aligns with maintainable architecture (UI consumes structured state, not raw internal chatter)

**Cons**
- requires deliberate editorial design, not just component tweaks

### Approach B — Process-first polish

- prioritize tool calls, subagents, planning, and activity panels
- let the answer bubble remain mostly as-is

**Pros**
- shows technical sophistication quickly

**Cons**
- conversation can become noisy before the main path is emotionally and visually clear
- risks a “debug console in chat clothing” feel

### Approach C — Surface-only visual pass

- keep interaction logic mostly the same
- tune spacing, labels, borders, animation, and hierarchy only

**Pros**
- fast

**Cons**
- does not solve the current legibility problem
- Fast / Thinking would still feel like mostly the same product with different labels

## Decision

Choose **Approach A**.

We will polish the conversation as a coherent narrative first, then use that narrative to make Fast / Thinking feel intentionally different, while exposing subagent activity as clean structured progress instead of raw internal stream spam.

## Product-level principles

### 1. Main answer remains primary
The answer bubble is always the main event. Process information exists to support trust, not to compete for attention.

### 2. Thinking is richer, not louder
Thinking mode should feel deeper and more deliberate, but not visually chaotic. More visibility should mean better-structured visibility, not more clutter.

### 3. Subagent activity should be readable at a glance
Users should be able to understand:
- who is working,
- what stage they are in,
- whether they are done,
- what came out of the work,
without reading raw internal text streams.

### 4. Technical states must be translated into human states
`live`, `preview`, `failed`, `contract rejected`, `reattached` are implementation concerns. The UI should express them as understandable user states.

## Design scope

### A. Main chat path polish

#### Empty state
The empty hero should clearly suggest that mode choice matters before the first message. The empty state should not feel like a static landing page; it should feel like the beginning of an interaction.

Design direction:
- keep the existing calm headline structure
- make the selected mode more visibly part of the pre-send context
- ensure starter chips and composer feel like one coordinated surface, not separate modules

#### Send transition
After sending, the transition from idle composer to active run should feel immediate and trustworthy.

Design direction:
- the user should instantly see that the selected mode is now the active mode for this run
- the first visible progress cue should appear quickly, without waiting for a large answer body
- the transport label should stop feeling like debug metadata and instead become a subtle confidence/status cue

#### Settled state
Once the answer lands, the UI should feel composed rather than mechanically “finished”.

Design direction:
- process should collapse into a calmer summary state
- answer should remain visually dominant
- settled runs should read as complete, not merely no-longer-streaming

### B. Fast / Thinking differentiation

This is the heart of the polish pass.

#### Fast mode should feel
- direct
- lightweight
- low-friction
- answer-oriented

User-facing behavior:
- fewer process details shown by default
- subagent activity summarized at a higher level
- lighter copy tone for status labels
- process block should collapse more aggressively once an answer arrives

#### Thinking mode should feel
- deliberate
- structured
- trustworthy
- process-aware

User-facing behavior:
- richer milestone visibility
- more explicit reasoning/process framing
- subagent activity can reveal more stages and summaries
- process block can stay more informative after settle, without becoming the dominant surface

#### Important constraint
The differentiation should not depend on hacks like completely different layouts. Both modes should remain recognizably the same product; the difference should come from pacing, disclosure level, and information density.

## C. Subagent stream strategy

### Decision
Subagent stream should be shown as a **structured milestone stream**, not a full internal text stream.

### What to show by default
For each subagent:
- name
- current state (`working`, `done`, `failed`)
- short role/goal label
- one-line latest milestone or outcome summary

### What to show on expand
On user expansion — and more readily in Thinking mode — show:
- stage milestones
- tools used
- concise intermediate findings
- final sub-result summary

### What not to show by default
Do **not** default to:
- token-by-token or paragraph-by-paragraph raw internal generation
- full hidden chain-of-thought style dumps
- noisy repeated progress lines that drown the answer

### Why
This gives users trust and observability without turning the product into a terminal transcript.

## D. Process block behavior

The current `ProcessBlock` is the right structural home, but its narrative role needs sharpening.

### Fast mode
- summary should stay short and action-oriented
- once the answer lands, default collapsed state should emphasize that the answer is ready
- the process title can be plainer and less “deep-work” flavored

### Thinking mode
- summary can remain more descriptive after settle
- expanded content can expose more milestone-level detail
- the process block should feel like a supporting notebook, not a dump pile

### Unified rule
The process block should never visually overpower the answer bubble.

## E. Todo bar role

The pinned `TodoBar` should remain distinct from the in-thread process stream, but the relationship between the two should feel coordinated.

Design direction:
- todo bar = the current high-level run plan
- process block = what actually happened during execution
- the two should not duplicate each other line-for-line

The user should understand:
- top bar = plan/status overview
- inline process = execution details

## F. Transport and failure language

Current implementation is technically correct, but demo polish needs a stronger narrative hierarchy.

### Live
Should read as calm confidence, not engineering jargon.

### Preview
Should clearly communicate “local preview / simulated path” without sounding like a broken fallback.

### Failed
Should read as recoverable, legible, and actionable.

Especially after the recent execution-style fail-loud changes, a run rejected by the backend contract must feel like a coherent failure state, not a silent mode-switch or unexplained no-op.

## Architectural guidance

### What belongs in UI
- disclosure behavior
- labels
- pacing
- mode-specific visibility rules
- visual hierarchy

### What belongs in application state
- normalized mode-aware process summaries
- structured subagent milestone model if needed
- mode-specific defaults for expansion/collapse behavior

### What does not belong in UI state
- raw provider details
- backend-specific transport semantics leaking directly into labels
- raw internal subagent text streams as the primary data model

### DDD boundary rule
If new demo-polish behavior needs new data structures, add them at the domain/application seam of `kokoro-web` as stable UI-facing state. Do not make presentational components invent ad-hoc semantics from low-level raw events.

## Success criteria

This design is successful when:
1. a first-time viewer can immediately tell that Fast and Thinking are intentionally different modes;
2. the main answer remains primary in both modes;
3. subagent activity feels informative and elegant, not spammy;
4. run-state transitions feel coherent and user-facing, not like backend leakage;
5. the demo path from first input to settled answer feels polished enough to present without narration doing all the explanatory work.

## Non-goals for this pass

- fully implementing native file upload/camera capture
- redesigning the whole rail IA from scratch
- exposing raw child-agent token streams
- changing the backend execution contract again

Those can come later. This pass is about making the current real capabilities legible, intentional, and demo-grade.
