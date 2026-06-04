# Todo

- [x] Create `kokoro-web/` as an independent Git repository.
- [x] Scaffold Bun + Next.js + Tailwind + shadcn/ui baseline.
- [x] Add DDD folders and dependency boundaries.
- [x] Add strict protocol schemas with failing tests first.
- [x] Add replay reducer with failing tests first.
- [x] Render the minimal chat shell using seed events.
- [x] Run test, lint, typecheck, and build.

## Documentation alignment

- [x] Add a durable three-primary-runtime architecture overview.
- [x] Record the main-agent/user-alignment lesson and defensive rule.
- [x] Persist the DeepAgents/LangChain orchestration reuse preference in project memory.
- [x] Clarify the protocol docs so the current minimal session-stream closed loop is distinct from browser-reserved parse-and-ignore event families.

## First-screen shell redesign (staged)

- [x] Add `run.created` to the protocol union as a parse-and-ignore family (maps to null) with red→green tests.
- [x] Replace the two-card protocol demo with the approved minimal first-screen shell (rail + hero + static composer).
- [x] Rework `globals.css` for the first-screen layout.
- [x] Keep the SSE reducer wired but surfaced via `data-*` while message rendering is deferred to the chat-view slice.
- [x] Gitignore local agent/MCP scratch dirs (`.playwright-mcp/`, `.superpowers/`).
- [x] Land the first-screen slice (commits `2d0cf08`, `bf0dde3`).

## Conversation view slice (in progress)

Design: `docs/superpowers/specs/2026-06-03-conversation-view-design.md`. Goal: complete multi-turn streaming conversation, demonstrable standalone via graceful local-simulation fallback. Artifact lane deferred (reserved) per the more recent refinement + protocol downgrade.

- [x] application: `appendUserMessage(state, {id, content})` pure helper + tests (multi-turn accumulation, immutability, ordering, survives run fold).
- [x] application: `consumeLiveSession` gains optional `initialState` + `onSettled`; all existing preview tests still green.
- [x] application: `buildSimulatedReplyEvents` (pure, deterministic, terminates) + `simulateAssistantReply` driver + `startSessionReply` orchestrator (live→fallback) + tests.
- [x] interfaces: `SessionShell` rewritten into empty/active conversation — controlled textarea composer (Enter sends, disabled while streaming), thread rendering, calm streaming indicator, inline failed state; injectable `startReply`.
- [x] styles: extended `globals.css` with thread/bubble/active-layout classes.
- [x] tests: shell test covers empty first screen, user msg render, assistant reply, streaming-disabled input, multi-turn history, inline failed error (29 tests pass).
- [x] verify: lint + typecheck + test + build green; Playwright visual pass over a real multi-turn conversation.
- [x] UI feedback pass (2026-06-03): scaled the whole UI to compact/conventional sizes; switched to comfortable left/right bubble layout (assistant left+avatar, user right); removed composer hover layout-shift. Re-verified all gates + visually.
- [x] Committed the conversation-view base (kokoro-web `7aada7e`).

## Production-usable polish (2026-06-03, via workflow + subagents)

Ran a multi-agent workflow (audit → plan → [implement → per-round QA gate] ×6 → 4-lens review) with a hard zero-cruft rule and a quality gate after every workstream.

- [x] Foundation cleanup: removed dead exports (createPreviewSessionState/startDemoSession/openDemoSessionStream/previewEvents); reducer dedups session-created + pins role-per-messageId; explicit parse-and-ignore listeners.
- [x] Stop/cancel generation + calm streaming indicator (reduced-motion aware).
- [x] SSR-safe single-conversation persistence (localStorage), 新对话 reset+refocus, retry-on-failure, double-send guard.
- [x] Composer auto-grow + focus return + input length cap.
- [x] Scroll stickiness + jump-to-latest; inline failed state.
- [x] A11y/visual polish: lang=zh-CN, aria-live/atomic, focus-visible (no reflow), WCAG contrast bumps, message/pulse animations.
- [x] Verified in main: lint+typecheck+test(79)+build green; Playwright pass (empty → send → reply → reload-persists → 新对话 resets). Review: production-ready, 0 blockers. Committed kokoro-web `7aada7e`.
- [ ] (deferred) markdown rendering for assistant text; multi-conversation history list; artifact lane promotion.

## Follow-up roadmap (recorded 2026-06-04)

Design source of truth = `docs/prototypes/variant-a-mi-mu/` (serve + screenshot before any UI work). Pin one anchor, confirm with user, then proceed. Don't over-reach: change only what's asked.

### A. Chat polish (kokoro-web)
- [x] Stop/cancel button design: it already exists (send→wood ■ "停止生成" during streaming, cancel semantics). Made the local preview stream slower (stepMs 28→60) so the stop is visible/usable. Decision: stop/cancel, NOT pause/resume (not meaningful for one-shot LLM replies).
- [ ] Starter chips on the empty screen (prototype `.chip--template` row: 海报/落地页/课件/写信/想法可视化/更多) → click prefills the composer. High comfort value; faithful to prototype.
- [ ] Wire the Fast/Thinking mode to the run's `execution_style` (currently display-only).
- [ ] Attach menu (上传图片/文件/拍照) → real native file picker, then backend upload when available (currently placeholder).
- [ ] Markdown rendering for assistant messages (real LLM output is markdown) — needs a sanitized renderer.
- [ ] Multi-conversation history list in the rail (currently single persisted conversation).

### B. Close the three-repo live loop (the real "production" gap)
- [ ] kokoro-session: fix 1-line lint (`sessionEventNames`) + commit the uncommitted Zod migration.
- [ ] kokoro-agent: add `from collections.abc import Mapping` (2 failing tests) + commit the local-fake-model.
- [ ] Run all three together (memory or Redis stream) with `KOKORO_LOCAL_FAKE_MODEL=1` (no API key) and verify a real end-to-end message web→session→agent→web streams in the browser (the loop has never been run together).
- [ ] Optional: real LLM via `ANTHROPIC_API_KEY`.

### C. Design-direction decision (needs user call)
- [ ] How much of the richer prototype to adopt vs the approved 06-02 minimal shell: serif hero accent, rail nav sections (创作/进阶/发现), warm send button. (06-02 chose minimal; prototype is richer — surface as a decision, don't silently pick.)

### D. Housekeeping
- [ ] Investigate/remove the stray sibling `~/WebstormProjects/kokoro-web` (duplicate of `Kokoro/kokoro-web`).
