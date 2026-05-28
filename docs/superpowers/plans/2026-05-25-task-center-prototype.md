# Task Center Prototype Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Kokoro’s scheduling/task-center prototype to the static HTML prototype, including a new “我的任务” page and connected entry points from chat, a studio page, a result page, and the cases page.

**Architecture:** Keep the existing prototype shell intact and add one new page plus surgical updates to four existing pages. Reuse shared CSS only for cross-page primitives that truly repeat; keep page-specific visual treatments in each page’s inline `<style>` block to match the current single-file prototype convention.

**Tech Stack:** Static HTML, shared CSS in `docs/prototypes/variant-a-mi-mu/css/*.css`, page-local inline CSS, SVG/inline illustration assets, Playwright/manual browser verification.

---

## File Map

- Create: `docs/prototypes/variant-a-mi-mu/tasks.html` — new “我的任务” page with summary, four sections, cards, and detail drawer-style panel.
- Modify: `docs/prototypes/variant-a-mi-mu/chat.html` — add scheduling confirmation card and navigation entry to the task center.
- Modify: `docs/prototypes/variant-a-mi-mu/canvas-image.html` — add a scheduler/clock entry in the generator bar and navigation entry.
- Modify: `docs/prototypes/variant-a-mi-mu/canvas-image-result.html` — add “continue this rhythm” actions and notification linkage.
- Modify: `docs/prototypes/variant-a-mi-mu/templates.html` — add schedule-oriented case actions and navigation entry.
- Modify: `docs/prototypes/variant-a-mi-mu/css/components.css` — add a minimal shared nav-item icon treatment only if the new “我的任务” entry needs no page-local workaround.
- Optional Create: `docs/prototypes/variant-a-mi-mu/screenshots/43-task-center.png` and follow-up screenshots via Playwright capture.

---

### Task 1: Build the “我的任务” page shell

**Files:**
- Create: `docs/prototypes/variant-a-mi-mu/tasks.html`
- Reference: `docs/superpowers/specs/2026-05-25-kokoro-task-center-page-spec.md`
- Reference: `docs/prototypes/variant-a-mi-mu/templates.html`

- [ ] **Step 1: Write the page skeleton using the existing shell**

Create `tasks.html` with:
- the standard sidebar shell copied from an existing prototype page,
- a topbar title of `我的任务`,
- a main content wrapper for the new page,
- a new nav item linking to `tasks.html` and marked current.

Use this title block in the page body:

```html
<div class="tasks-page__hero">
  <div>
    <div class="tasks-page__eyebrow">持续协作</div>
    <h1 class="tasks-page__title">我的任务</h1>
    <p class="tasks-page__sub">这些是 Kokoro 正在替你记着和推进的事。</p>
  </div>
  <div class="tasks-page__summary-row" aria-label="任务摘要">
    <article class="tasks-page__summary-card">
      <span class="tasks-page__summary-label">即将开始</span>
      <strong class="tasks-page__summary-value">2</strong>
    </article>
    <article class="tasks-page__summary-card">
      <span class="tasks-page__summary-label">正在进行</span>
      <strong class="tasks-page__summary-value">1</strong>
    </article>
    <article class="tasks-page__summary-card">
      <span class="tasks-page__summary-label">等你决定</span>
      <strong class="tasks-page__summary-value">1</strong>
    </article>
    <article class="tasks-page__summary-card">
      <span class="tasks-page__summary-label">本周已完成</span>
      <strong class="tasks-page__summary-value">5</strong>
    </article>
  </div>
</div>
```

- [ ] **Step 2: Add the four core task sections and example cards**

Create sections for:
- `即将开始`
- `正在进行`
- `等你决定`
- `已完成 / 暂停中 / 没做成`

Each section must contain at least 2 sample cards. Use the first card in “即将开始” as:

```html
<article class="task-card task-card--scheduled is-current">
  <div class="task-card__meta-row">
    <span class="task-card__source">来自案例库</span>
    <span class="task-card__rhythm">每周</span>
  </div>
  <h3 class="task-card__title">每周内容选题</h3>
  <p class="task-card__status">下次：周一 09:00 · 到时候直接帮我做</p>
  <div class="task-card__preview task-card__preview--text">
    <span>小红书选题 / 公众号备选 / 标题方向</span>
  </div>
  <div class="task-card__actions">
    <a class="btn btn--primary btn--sm" href="#task-detail">查看</a>
    <button class="btn btn--ghost btn--sm" type="button">现在执行</button>
    <button class="btn btn--ghost btn--sm" type="button">改时间</button>
  </div>
</article>
```

- [ ] **Step 3: Add the task detail panel in-page**

Implement a right-side or lower-page detail panel (static open state is fine for prototype) with:
- overview,
- “这件事会怎么发生”,
- recent result,
- event timeline,
- actions.

Use this body:

```html
<aside class="task-detail" id="task-detail" aria-label="任务详情">
  <div class="task-detail__eyebrow">任务详情</div>
  <h2 class="task-detail__title">每周内容选题</h2>
  <p class="task-detail__status">每周一 09:00 开始 · 默认替你先出第一版，做完回来告诉你。</p>
  <section class="task-detail__section">
    <h3>这件事会怎么发生</h3>
    <p>我会在每周一早上先整理 3 个方向。若需要你选方向，我会先停在草稿，不会直接推到底。</p>
  </section>
  <section class="task-detail__section">
    <h3>最近结果</h3>
    <a class="task-detail__result" href="canvas-result.html">上周复盘 · 3 个选题已经整理好</a>
  </section>
  <section class="task-detail__section">
    <h3>最近记录</h3>
    <ul class="task-detail__timeline">
      <li>上周一 · 给出 3 个选题</li>
      <li>周三 · 你把节奏改成了每周一</li>
      <li>今天 · 下次执行时间确认在 09:00</li>
    </ul>
  </section>
</aside>
```

- [ ] **Step 4: Add page-local CSS in `<style>`**

Define page-local classes for:
- `.tasks-page__*`
- `.task-section__*`
- `.task-card__*`
- `.task-detail__*`

Visual requirements:
- warm paper surfaces,
- cards that feel like entrusted work rather than dashboard rows,
- one highlighted “current” card,
- summary cards with restrained contrast,
- responsive two-column main area where cards occupy the main column and detail panel anchors the side.

- [ ] **Step 5: Verify the page opens and visually matches the spec**

Run:
```bash
python3 -m http.server 8753 --directory /Users/yuri/WebstormProjects/Kokoro/docs/prototypes/variant-a-mi-mu
```

Then inspect in browser:
- `http://localhost:8753/tasks.html`

Expected:
- page loads,
- sidebar matches the rest of the prototype,
- “我的任务” nav item is current,
- all four sections are visible,
- detail panel is present,
- no cyan/dark/glass styling appears.

---

### Task 2: Add task-center navigation across touched pages

**Files:**
- Modify: `docs/prototypes/variant-a-mi-mu/chat.html`
- Modify: `docs/prototypes/variant-a-mi-mu/canvas-image.html`
- Modify: `docs/prototypes/variant-a-mi-mu/canvas-image-result.html`
- Modify: `docs/prototypes/variant-a-mi-mu/templates.html`

- [ ] **Step 1: Add a new sidebar nav item linking to `tasks.html`**

Insert the new entry in the discovery/utility area before `团队` on each touched page.

Use this exact block:

```html
<a class="nav-item" href="tasks.html">
  <svg class="nav-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3.5 4.5h9M3.5 8h9M3.5 11.5h6"/><circle cx="12.25" cy="11.5" r="1.25"/></svg>
  <span>我的任务</span>
</a>
```

- [ ] **Step 2: Run a quick grep-style verification**

Run:
```bash
grep -n "我的任务" /Users/yuri/WebstormProjects/Kokoro/docs/prototypes/variant-a-mi-mu/chat.html /Users/yuri/WebstormProjects/Kokoro/docs/prototypes/variant-a-mi-mu/canvas-image.html /Users/yuri/WebstormProjects/Kokoro/docs/prototypes/variant-a-mi-mu/canvas-image-result.html /Users/yuri/WebstormProjects/Kokoro/docs/prototypes/variant-a-mi-mu/templates.html /Users/yuri/WebstormProjects/Kokoro/docs/prototypes/variant-a-mi-mu/tasks.html
```

Expected: each file contains the nav entry, and `tasks.html` contains the current-state version.

---

### Task 3: Add chat scheduling confirmation card

**Files:**
- Modify: `docs/prototypes/variant-a-mi-mu/chat.html`
- Reference: `docs/superpowers/specs/2026-05-25-kokoro-scheduling-and-task-center-design.md`

- [ ] **Step 1: Add a new assistant message block showing schedule understanding**

Insert a new assistant reply near the bottom of the chat thread, after the existing “在想，要不要顺手帮你拟个发送时间” line. Use:

```html
<article class="message message--ai">
  <div class="schedule-card" aria-label="调度确认卡">
    <div class="schedule-card__eyebrow">我先替你记住了</div>
    <h3 class="schedule-card__title">明早 09:00 再继续这封信</h3>
    <p class="schedule-card__body">我会先把这封信整理成更适合发送的版本，做完后回到这里告诉你。你也可以在「我的任务」里随时改时间。</p>
    <div class="schedule-card__actions">
      <a class="btn btn--primary btn--sm" href="tasks.html">去我的任务看</a>
      <button class="btn btn--ghost btn--sm" type="button">改一下时间</button>
      <button class="btn btn--ghost btn--sm" type="button">只提醒我就好</button>
    </div>
  </div>
</article>
```

- [ ] **Step 2: Add page-local CSS for `.schedule-card__*`**

Add inline styles in `chat.html` for:
- softly elevated card surface,
- mono eyebrow,
- serif title,
- compact action row,
- no cold/high-tech treatment.

- [ ] **Step 3: Verify the card reads as a confirmation, not a dashboard**

Open:
```bash
http://localhost:8753/chat.html
```

Expected:
- new card appears naturally in the conversation,
- “去我的任务看” links to `tasks.html`,
- styling feels like Kokoro guidance rather than system alerting.

---

### Task 4: Add scheduler entry to the image studio page

**Files:**
- Modify: `docs/prototypes/variant-a-mi-mu/canvas-image.html`
- Modify: `docs/prototypes/variant-a-mi-mu/css/function-tool.css` (only if shared classes are cleaner than page-local additions)

- [ ] **Step 1: Add a clock-trigger control beside the generate action**

In the bottom bar action area, add a schedule details/dropdown before the generate CTA. Use:

```html
<details class="fn-schedule">
  <summary class="chip chip--control">稍后做 ▾</summary>
  <div class="fn-schedule__menu" role="menu">
    <div class="fn-schedule__label">把这件事交给 Kokoro</div>
    <button class="fn-schedule__item is-current" type="button" role="menuitem">今天晚上 20:00</button>
    <button class="fn-schedule__item" type="button" role="menuitem">明天早上 09:00</button>
    <button class="fn-schedule__item" type="button" role="menuitem">每周一来一版</button>
    <button class="fn-schedule__item" type="button" role="menuitem">只提醒我就好</button>
  </div>
</details>
```

- [ ] **Step 2: Add a helper line under the bar or near the actions**

Add this explanatory note so the interaction reads as “continuous help”:

```html
<p class="fn-studio__schedule-note">也可以让 Kokoro 晚点再做，或者按固定节奏替你继续出图。</p>
```

- [ ] **Step 3: Add CSS for the schedule menu**

Create styles for:
- `.fn-schedule`
- `.fn-schedule__menu`
- `.fn-schedule__label`
- `.fn-schedule__item`
- `.fn-studio__schedule-note`

The menu should pop upward like the model picker, and the note should sit quietly under the generator without turning the page into a form-heavy control panel.

- [ ] **Step 4: Verify the studio still feels like a creation page first**

Open:
```bash
http://localhost:8753/canvas-image.html
```

Expected:
- “生成” remains primary,
- “稍后做” feels secondary but discoverable,
- the page still reads as a warm single-column studio.

---

### Task 5: Add “continue this rhythm” actions to the image result page

**Files:**
- Modify: `docs/prototypes/variant-a-mi-mu/canvas-image-result.html`

- [ ] **Step 1: Add a notification-like success strip near the top of the right canvas pane**

Insert a subtle strip under the toolbar or above the hero preview using:

```html
<div class="canvas-rhythm-note" role="status" aria-label="结果提醒">
  <span class="canvas-rhythm-note__dot" aria-hidden="true"></span>
  <span>这张已经替你收好了。你也可以明天继续，或者设成每周都来一版。</span>
  <a class="canvas-rhythm-note__link" href="tasks.html">去我的任务</a>
</div>
```

- [ ] **Step 2: Add a rhythm action group near the existing hero caption or control area**

Use:

```html
<div class="canvas-rhythm-actions" aria-label="继续这条线">
  <a class="btn btn--primary btn--sm" href="canvas-image.html">再做一版</a>
  <a class="btn btn--ghost btn--sm" href="tasks.html">明天继续</a>
  <a class="btn btn--ghost btn--sm" href="tasks.html">每周按这个风格来一版</a>
</div>
```

- [ ] **Step 3: Add page-local CSS for the note and actions**

Define:
- `.canvas-rhythm-note__*`
- `.canvas-rhythm-actions`

The strip should feel like a calm follow-up, not a loud toast.

- [ ] **Step 4: Verify the result page becomes a loop, not an endpoint**

Open:
```bash
http://localhost:8753/canvas-image-result.html
```

Expected:
- result page still centers the generated image,
- a clear path exists to continue later or weekly,
- `tasks.html` is reachable from the new elements.

---

### Task 6: Add scheduled-use actions to the cases page

**Files:**
- Modify: `docs/prototypes/variant-a-mi-mu/templates.html`

- [ ] **Step 1: Add action rows to case cards for at least the first four cards**

For the first four visible case cards, add a compact action row under the title/body. Use this pattern:

```html
<div class="cases__actions">
  <a class="btn btn--primary btn--sm" href="canvas-image-result.html">现在试试</a>
  <a class="btn btn--ghost btn--sm" href="tasks.html">明天来一版</a>
  <a class="btn btn--ghost btn--sm" href="tasks.html">每周按这个做</a>
</div>
```

Point each “现在试试” to that card’s existing destination, and both schedule links to `tasks.html`.

- [ ] **Step 2: Update the hero subcopy to reflect the method-library idea**

Replace the current hero subcopy with:

```html
<p class="cases__sub">每个案例都是一种做法。你可以现在试，也可以交给 Kokoro 明天或每周继续替你做。</p>
```

- [ ] **Step 3: Add inline CSS for `.cases__actions`**

Ensure the action row fits the current card rhythm without overpowering the preview artwork.

- [ ] **Step 4: Verify the page still feels like a curated case library**

Open:
```bash
http://localhost:8753/templates.html
```

Expected:
- card actions are readable,
- cards still feel curated and visual,
- schedule links point to the task center.

---

### Task 7: Capture final verification and screenshots

**Files:**
- Verify: `docs/prototypes/variant-a-mi-mu/tasks.html`
- Verify: `docs/prototypes/variant-a-mi-mu/chat.html`
- Verify: `docs/prototypes/variant-a-mi-mu/canvas-image.html`
- Verify: `docs/prototypes/variant-a-mi-mu/canvas-image-result.html`
- Verify: `docs/prototypes/variant-a-mi-mu/templates.html`
- Output: `docs/prototypes/variant-a-mi-mu/screenshots/43-task-center.png`
- Output: `docs/prototypes/variant-a-mi-mu/screenshots/44-chat-schedule-card.png`
- Output: `docs/prototypes/variant-a-mi-mu/screenshots/45-image-studio-schedule.png`
- Output: `docs/prototypes/variant-a-mi-mu/screenshots/46-image-result-rhythm.png`
- Output: `docs/prototypes/variant-a-mi-mu/screenshots/47-cases-schedule-actions.png`

- [ ] **Step 1: Start the local server**

Run:
```bash
python3 -m http.server 8753 --directory /Users/yuri/WebstormProjects/Kokoro/docs/prototypes/variant-a-mi-mu
```

Expected: server listens successfully on port `8753`.

- [ ] **Step 2: Open each page and visually inspect**

Check:
- `http://localhost:8753/tasks.html`
- `http://localhost:8753/chat.html`
- `http://localhost:8753/canvas-image.html`
- `http://localhost:8753/canvas-image-result.html`
- `http://localhost:8753/templates.html`

Expected:
- all load without broken layout,
- links to `tasks.html` work,
- the new controls match the warm Kokoro design language,
- no page looks like a developer console or admin backend.

- [ ] **Step 3: Capture final screenshots**

Use Playwright screenshots saved to the listed filenames.

Expected:
- each screenshot clearly shows the newly added scheduling/task-center affordance,
- screenshots are presentation-ready for the human partner.

- [ ] **Step 4: Run a quick final file-status check**

Run:
```bash
git status --short
```

Expected: only the intended prototype/spec/plan files changed.

---

## Self-Review

### Spec coverage
- Task center page: covered in Task 1.
- Navigation integration: covered in Task 2.
- Chat confirmation card: covered in Task 3.
- Studio schedule entry: covered in Task 4.
- Result-page loop: covered in Task 5.
- Cases scheduling actions: covered in Task 6.
- Final prototype screenshots: covered in Task 7.

### Placeholder scan
- No TBD/TODO placeholders remain.
- All file paths and output filenames are explicit.
- Verification commands are included.

### Consistency scan
- Uses `tasks.html` consistently for the task center.
- Uses “我的任务” consistently as the user-facing label.
- Keeps all schedule links pointing to the same new page.
