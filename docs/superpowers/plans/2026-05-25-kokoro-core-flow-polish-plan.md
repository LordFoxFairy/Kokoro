# Kokoro Core Flow Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Raise Kokoro’s core prototype flow from a connected demo into a more mature, system-like product experience across home/chat, a representative studio page, a representative result page, the task center, and the cases library.

**Architecture:** Treat one page in each core role as the design baseline, then propagate the improved language outward. Keep the existing static prototype architecture and shell intact, making surgical changes that strengthen hierarchy, continuity, and “next step” clarity without broad refactors.

**Tech Stack:** Static HTML, shared CSS, page-local inline CSS, existing SVG/illustration assets, local HTTP preview, Playwright browser verification.

---

## File Map

- Modify: `docs/prototypes/variant-a-mi-mu/index.html` — home page as the system entry and expectation-setter.
- Modify: `docs/prototypes/variant-a-mi-mu/chat.html` — chat as the primary conversational flow.
- Modify: `docs/prototypes/variant-a-mi-mu/canvas-image.html` — representative Studio page.
- Modify: `docs/prototypes/variant-a-mi-mu/canvas-image-result.html` — representative Result page.
- Modify: `docs/prototypes/variant-a-mi-mu/tasks.html` — task center as the second main hub.
- Modify: `docs/prototypes/variant-a-mi-mu/templates.html` — cases library as a methods library.
- Reference: `docs/superpowers/specs/2026-05-25-kokoro-core-flow-polish-design.md`
- Reference: `docs/superpowers/specs/2026-05-25-kokoro-scheduling-and-task-center-design.md`
- Output: `docs/prototypes/variant-a-mi-mu/screenshots/48-home-core-flow-polish.png`
- Output: `docs/prototypes/variant-a-mi-mu/screenshots/49-chat-core-flow-polish.png`
- Output: `docs/prototypes/variant-a-mi-mu/screenshots/50-image-studio-core-flow-polish.png`
- Output: `docs/prototypes/variant-a-mi-mu/screenshots/51-image-result-core-flow-polish.png`
- Output: `docs/prototypes/variant-a-mi-mu/screenshots/52-task-center-core-flow-polish.png`
- Output: `docs/prototypes/variant-a-mi-mu/screenshots/53-cases-core-flow-polish.png`

---

### Task 1: Reframe the home page as a true core-flow entry point

**Files:**
- Modify: `docs/prototypes/variant-a-mi-mu/index.html`

- [ ] **Step 1: Tighten the topbar and stage hierarchy**

Update the empty topbar title area so the page feels like a real product surface, not an unfinished blank. Replace the current empty span in the topbar with a quiet system label:

```html
<span class="topbar__title">今天的开始</span>
```

Expected result: the page feels intentional before the greeting section appears.

- [ ] **Step 2: Add a “three ways to begin” helper strip under the composer**

Insert a compact helper row below the input pill and above the template chips:

```html
<div class="home-start-ways" aria-label="开始方式">
  <div class="home-start-ways__item"><strong>说出来</strong><span>直接把想法告诉 Kokoro</span></div>
  <div class="home-start-ways__item"><strong>挑一个</strong><span>从案例或功能开始</span></div>
  <div class="home-start-ways__item"><strong>交给它</strong><span>稍后继续，或按节奏替你跟进</span></div>
</div>
```

This must make the home page explain the full system, not just the chat box.

- [ ] **Step 3: Add a direct bridge to the task center near the home hint**

Replace the single-line hint with a richer line that includes “我的任务”:

```html
<div class="home-hint">
  不知道做什么？点一个试试看，或者去 <a href="tasks.html">我的任务</a> 看看 Kokoro 正在替你推进什么。
  <span class="kbd-hint" style="margin-left:8px;">按 <span class="kbd">Enter</span> 发送 · <span class="kbd">⌘K</span> 搜索</span>
</div>
```

Expected result: the task center is part of the primary flow, not just a sidebar extra.

- [ ] **Step 4: Improve showcase section framing so it feels like a methods preview, not a gallery widget**

Change the showcase heading/subheading to make it read as “what you can ask Kokoro to do” rather than pure visual samples. Add a short subcopy under the showcase head:

```html
<p class="showcase__sub">先看一眼它能怎样接住一个想法，再决定现在开始，还是交给它之后继续。</p>
```

Add page-local CSS for:
- `.home-start-ways`
- `.home-start-ways__item`
- `.showcase__sub`

- [ ] **Step 5: Verify the home page now explains the system more clearly**

Run local preview and inspect:
```bash
curl -I http://127.0.0.1:8753/index.html
```

Expected: `HTTP/1.0 200 OK`

Then visually confirm in browser that:
- the topbar no longer looks unfinished,
- the home page shows three clear ways to begin,
- the task center is visible in the first screenful,
- the showcase feels like a flow preview rather than a detached gallery.

---

### Task 2: Polish chat into a more mature conversational control surface

**Files:**
- Modify: `docs/prototypes/variant-a-mi-mu/chat.html`

- [ ] **Step 1: Add a short conversation-stage descriptor near the top of the chat view**

Under the topbar and before the thread, insert a compact stage card:

```html
<div class="chat-stage-note" aria-label="当前协作阶段">
  <span class="chat-stage-note__label">当前阶段</span>
  <strong class="chat-stage-note__title">先把话说清楚，再慢慢替你整理出来</strong>
  <span class="chat-stage-note__sub">这段对话会自然流向结果页，也可以交给 Kokoro 明早继续。</span>
</div>
```

This should make the chat page feel like part of a multi-step product flow.

- [ ] **Step 2: Strengthen the visual separation between conversation, result card, and schedule card**

Adjust page-local CSS so that:
- the existing document result card feels more like a delivered artifact,
- the schedule card feels like a calm continuation card,
- the thinking state is lighter than both.

Use CSS changes only; do not rewrite the entire message thread.

- [ ] **Step 3: Add a compact “next step” row after the schedule card**

Insert:

```html
<div class="chat-next-steps" aria-label="下一步">
  <a class="chip chip--template" href="canvas.html">看格式化结果</a>
  <a class="chip chip--template" href="tasks.html">去我的任务</a>
  <a class="chip chip--template" href="templates.html">看看相似案例</a>
</div>
```

Expected result: chat more clearly communicates where the user can go next.

- [ ] **Step 4: Refine the composer to feel less like a prototype footer**

Add a small helper label above or inside the composer area such as:

```html
<div class="composer-dock__label">继续说一句，或者让我明早替你继续。</div>
```

Keep it subtle and warm.

- [ ] **Step 5: Verify the chat page reads as a believable collaboration surface**

Check:
```bash
curl -I http://127.0.0.1:8753/chat.html
```

Expected: `HTTP/1.0 200 OK`

In browser verify:
- the page has a clear sense of current stage,
- result and schedule are visually distinct,
- “next step” options are visible,
- the bottom composer feels integrated, not like a bolted-on demo control.

---

### Task 3: Deepen the image Studio page as the baseline creation surface

**Files:**
- Modify: `docs/prototypes/variant-a-mi-mu/canvas-image.html`

- [ ] **Step 1: Add a quiet “what happens next” explainer near the hero or schedule note**

Insert a small section between the hero and the generator bar, or directly under the note, using:

```html
<div class="fn-studio__flow-note" aria-label="生成后会发生什么">
  <span>现在生成，会直接带你去结果。</span>
  <span>稍后做，会先替你记进「我的任务」。</span>
</div>
```

This should strengthen the page’s place in the system.

- [ ] **Step 2: Make the generator bar feel more product-grade**

Adjust page-local or shared CSS so the bar has:
- stronger visual focus,
- clearer grouping between prompt, parameters, schedule, and generate,
- slightly more polished spacing.

Do not add new capabilities here; refine hierarchy only.

- [ ] **Step 3: Add a compact “最近你常这样做” strip below the generator**

Use:

```html
<div class="fn-studio__recents" aria-label="最近常这样做">
  <a class="chip chip--template" href="canvas-image-result.html">暖光橘猫 · 看上一版</a>
  <a class="chip chip--template" href="tasks.html">每周一来一版 · 去我的任务</a>
  <a class="chip chip--template" href="templates.html">看看类似案例</a>
</div>
```

Expected result: the page no longer feels like an isolated form.

- [ ] **Step 4: Refine schedule menu language to feel more continuous and less menu-like**

Keep the same items, but ensure the menu label and note work together as a “time extension” of generating. If needed, update the menu label to:

```html
<div class="fn-schedule__label">如果不是现在，也可以让 Kokoro 替你记着</div>
```

- [ ] **Step 5: Verify the Studio page still feels centered on creation**

Check:
```bash
curl -I http://127.0.0.1:8753/canvas-image.html
```

Expected: `HTTP/1.0 200 OK`

In browser verify:
- “生成” remains primary,
- the page now better explains immediate vs delayed work,
- the generator bar looks more mature and intentional.

---

### Task 4: Deepen the image result page as a true continuation surface

**Files:**
- Modify: `docs/prototypes/variant-a-mi-mu/canvas-image-result.html`

- [ ] **Step 1: Add a result-stage descriptor above the canvas content**

Insert, near the new rhythm note:

```html
<div class="canvas-stage-note" aria-label="当前结果阶段">
  <span class="canvas-stage-note__label">这次已经做出来了</span>
  <strong class="canvas-stage-note__title">接下来可以继续调，也可以把这条线交给 Kokoro 之后再跟进。</strong>
</div>
```

- [ ] **Step 2: Strengthen the “continue this line” action group**

Keep the current actions, but add a fourth path to the case library/method idea:

```html
<a class="btn btn--ghost btn--sm" href="templates.html">看看类似做法</a>
```

Now the result page explicitly branches to:
- rerun,
- task center,
- recurring flow,
- method library.

- [ ] **Step 3: Add a compact “why this version works” summary under the hero caption**

Use:

```html
<p class="canvas-image__why">这一版保留了暖光、留白和更轻的背景虚化，所以更像一张能反复迭代的基准图。</p>
```

This should make the result page feel editorial and deliberate.

- [ ] **Step 4: Refine note/action spacing so the page feels staged, not stacked**

Adjust page-local CSS for:
- `.canvas-rhythm-note`
- `.canvas-stage-note__*`
- `.canvas-rhythm-actions`
- `.canvas-image__why`

Aim for a clearer vertical sequence:
1. state,
2. result,
3. reason,
4. next actions.

- [ ] **Step 5: Verify the result page no longer feels like an endpoint**

Check:
```bash
curl -I http://127.0.0.1:8753/canvas-image-result.html
```

Expected: `HTTP/1.0 200 OK`

In browser verify:
- the result has a stage descriptor,
- the page clearly suggests what to do next,
- the “continue this line” area feels like part of the page structure, not an afterthought.

---

### Task 5: Mature the task center from “new page” to “second main hub”

**Files:**
- Modify: `docs/prototypes/variant-a-mi-mu/tasks.html`

- [ ] **Step 1: Strengthen the page’s “second main hub” framing**

Add a slim helper strip under the summary cards:

```html
<div class="tasks-page__system-note" aria-label="任务页说明">
  <span>这里不是后台，而是 Kokoro 正在替你记着和推进的事。</span>
  <a href="chat.html">回到对话</a>
  <a href="templates.html">看看案例</a>
</div>
```

- [ ] **Step 2: Make one card in each section feel more “result-rich”**

Improve one featured card per section with slightly richer previews or more deliberate text hierarchy. Do this without bloating all cards equally; the page should have a clear focal rhythm.

- [ ] **Step 3: Deepen the detail panel so it feels more trustworthy**

Add one small subsection to the detail panel:

```html
<section class="task-detail__section">
  <h3>下一次回来你会看到什么</h3>
  <p>如果我顺利做完，你会先看到 3 个方向；如果我需要你点头，我会把它留在“等你决定”里，不会让它悄悄消失。</p>
</section>
```

- [ ] **Step 4: Add clearer in-page section transitions**

Use CSS or subtle labels so the four sections feel more editorially paced, less like equally weighted blocks.

- [ ] **Step 5: Verify the page now feels like a core system hub**

Check:
```bash
curl -I http://127.0.0.1:8753/tasks.html
```

Expected: `HTTP/1.0 200 OK`

In browser verify:
- the page reads as “my ongoing collaboration surface,”
- not as a dashboard or admin page,
- the detail panel feels like part of a mature system.

---

### Task 6: Elevate the cases page from gallery to method library

**Files:**
- Modify: `docs/prototypes/variant-a-mi-mu/templates.html`

- [ ] **Step 1: Add a short methods framing block under the hero**

Insert:

```html
<div class="cases__method-note" aria-label="案例库说明">
  <strong>这些不是只给你看的作品。</strong>
  <span>它们是已经被证明可行的做法：你可以现在开始，也可以交给 Kokoro 明天或每周继续替你做。</span>
</div>
```

- [ ] **Step 2: Improve action hierarchy on cards**

Adjust card action styling so:
- “现在试试” is clearly primary,
- “明天来一版 / 每周按这个做” are visibly secondary,
- the row remains elegant and doesn’t overpower the visual preview.

- [ ] **Step 3: Add a compact route back to the task center above the first group**

Use:

```html
<div class="cases__flow-links">
  <a class="chip chip--template" href="tasks.html">去我的任务看看正在继续的案例</a>
  <a class="chip chip--template" href="index.html">回到首页重新开始</a>
</div>
```

- [ ] **Step 4: Refine the first group’s card spacing so the library feels more curated**

Use page-local CSS adjustments only. The goal is to make the first screen of cards feel like a confident editorial selection rather than a grid dropped on the page.

- [ ] **Step 5: Verify the page now reads as a methods library**

Check:
```bash
curl -I http://127.0.0.1:8753/templates.html
```

Expected: `HTTP/1.0 200 OK`

In browser verify:
- the hero copy supports the “method library” concept,
- the card actions are clear and balanced,
- the page connects naturally to both home and task center.

---

### Task 7: Final core-flow verification and screenshots

**Files:**
- Verify: `docs/prototypes/variant-a-mi-mu/index.html`
- Verify: `docs/prototypes/variant-a-mi-mu/chat.html`
- Verify: `docs/prototypes/variant-a-mi-mu/canvas-image.html`
- Verify: `docs/prototypes/variant-a-mi-mu/canvas-image-result.html`
- Verify: `docs/prototypes/variant-a-mi-mu/tasks.html`
- Verify: `docs/prototypes/variant-a-mi-mu/templates.html`
- Output: `docs/prototypes/variant-a-mi-mu/screenshots/48-home-core-flow-polish.png`
- Output: `docs/prototypes/variant-a-mi-mu/screenshots/49-chat-core-flow-polish.png`
- Output: `docs/prototypes/variant-a-mi-mu/screenshots/50-image-studio-core-flow-polish.png`
- Output: `docs/prototypes/variant-a-mi-mu/screenshots/51-image-result-core-flow-polish.png`
- Output: `docs/prototypes/variant-a-mi-mu/screenshots/52-task-center-core-flow-polish.png`
- Output: `docs/prototypes/variant-a-mi-mu/screenshots/53-cases-core-flow-polish.png`

- [ ] **Step 1: Reuse the local static server**

Ensure the prototype server is running at:
```bash
http://127.0.0.1:8753
```

If not, run:
```bash
python3 -m http.server 8753 --directory /Users/yuri/WebstormProjects/Kokoro/docs/prototypes/variant-a-mi-mu
```

Expected: server responds on port `8753`.

- [ ] **Step 2: Confirm all six core pages return HTTP 200**

Run:
```bash
curl -I http://127.0.0.1:8753/index.html && \
curl -I http://127.0.0.1:8753/chat.html && \
curl -I http://127.0.0.1:8753/canvas-image.html && \
curl -I http://127.0.0.1:8753/canvas-image-result.html && \
curl -I http://127.0.0.1:8753/tasks.html && \
curl -I http://127.0.0.1:8753/templates.html
```

Expected: all six return `HTTP/1.0 200 OK`.

- [ ] **Step 3: Visually inspect all six pages in the browser**

Verify:
- home clearly explains three ways to begin,
- chat has stronger stage and next-step clarity,
- studio looks more product-grade and explains immediate vs later flow,
- result reads as a continuation surface,
- task center feels like a second main hub,
- cases library feels like a methods library.

- [ ] **Step 4: Capture the six final screenshots**

Use Playwright MCP screenshots saved to the filenames listed above.

Expected: each image clearly communicates the improved hierarchy and flow role of its page.

- [ ] **Step 5: Run final working tree verification**

Run:
```bash
git status --short
```

Expected: changes are limited to the planned prototype/spec/plan files plus expected screenshots.

---

## Self-Review

### Spec coverage
- Home flow reframing: Task 1
- Chat maturity and continuity: Task 2
- Studio baseline polish: Task 3
- Result continuation structure: Task 4
- Task center maturity: Task 5
- Cases library method framing: Task 6
- Final verification and screenshots: Task 7

### Placeholder scan
- No TBD/TODO markers remain.
- All files, commands, and screenshot outputs are explicit.
- Each page has a concrete set of changes, not vague polish language.

### Consistency scan
- Uses “我的任务” consistently as the task hub label.
- Uses “稍后做 / 明天继续 / 每周按这个做” consistently for scheduling language.
- Keeps the representative page strategy intact: one baseline page per role, then expansion later.
