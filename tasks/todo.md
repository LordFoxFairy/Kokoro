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
- [ ] (deferred) artifact lane promotion.

## Follow-up roadmap (recorded 2026-06-04)

Design source of truth = `docs/prototypes/variant-a-mi-mu/` (serve + screenshot before any UI work). Pin one anchor, confirm with user, then proceed. Don't over-reach: change only what's asked.

### A. Chat polish (kokoro-web)
- [x] Stop/cancel button design: it already exists (send→wood ■ "停止生成" during streaming, cancel semantics). Made the local preview stream slower (stepMs 28→60) so the stop is visible/usable. Decision: stop/cancel, NOT pause/resume (not meaningful for one-shot LLM replies).
- [x] Starter chips on the empty screen (海报/落地页/课件/写信/想法可视化), matching the prototype `.chip--template` row. Click prefills the composer with a continuable starter prompt (caret at end), does NOT send; chips confined to the empty hero. kokoro-web `ce291bf`, lint/typecheck/test(82)/build green + Playwright-verified. (Dropped the prototype's `更多…` chip — it linked to a non-existent gallery; add when templates/gallery exists.)
- [x] Wire the Fast/Thinking mode to the run's `execution_style` end-to-end. Completed on the locked baseline branches: `kokoro-web` now threads the selected `fast | thinking` mode into the live run request and surfaces contract failures as explicit failed runs; `kokoro-session` restricts `execution_style` to `fast | thinking` and rejects invalid values with HTTP 400; `kokoro-agent` resolves model/runtime config per run instead of using a worker-global model instance, and the current `openai:glm-5` path verifies a distinct `thinking` runtime (`reasoning_effort="high"`) versus `fast`.
- [~] Attach menu (上传图片/文件/拍照):**悬空入口已闭环为 disabled+「即将支持」**(/goal G1,消点击无反馈的误导);**真实文件选择/拍照/后端上传流仍未做**(需后端上传能力)。语音 mic(G2)、rail 搜索 ⌘K(G3)同样改 disabled。

### B. Close the three-repo live loop (the real "production" gap) — DONE 2026-06-04
- [x] kokoro-session: fixed lint (`sessionEventNames` → `SessionEventName` derived from the Zod schema) + landed the Zod migration. Branch `feat/three-repo-loop` (8c9428f).
- [x] kokoro-agent: added `from collections.abc import Mapping` + tightened the payload TypeGuard for pyright --strict; committed the local-fake-model. Branch `feat/three-repo-loop` (673ee61).
- [x] Ran all three together over Redis (existing shared container, isolated db 15) with `KOKORO_LOCAL_FAKE_MODEL=1`. **Found + fixed a real Redis-only SSE cursor bug** (session resumed XREAD from the domain `envelope.cursor` as if it were a Redis stream id → silent empty `/stream`; MemoryStreamPort masked it). Verified end-to-end via curl (session.created→deltas→message.completed→run.completed) AND in the browser via Playwright: real agent reply rendered ("Local fallback active…"), transport label "实时 · http://localhost:3001" (live path, not the preview fallback). See lessons 2026-06-04.
- [ ] Optional: verify and use real provider credentials for the live worker path. Current baseline status: `kokoro-agent` already includes `langchain-openai`, `python-dotenv`, `load_dotenv()`, and env-based `KOKORO_MODEL` / `OPENAI_BASE_URL` / `OPENAI_API_KEY` model bootstrapping; what remains is operational verification / choosing the provider credentials for the live worker path.

### C. Design-direction decision (needs user call)
- [x] 设计方向 DONE(用户定 2026-06-20:**暖化视觉、保持对话为核**,不做 richer 创作套件)。web #13 `44cc545`:补 `--font-serif` 系统宋体栈;hero「今天想做什么?」+ 品牌 Kokoro/こころ 上衬线;发送键 `#9fd1ff`(cyan,违铁律)→ 木色。调色本就米木纸感。Playwright 验证。**richer 创作套件(7 生成器/Hub/teams)= 大产品赌注,显式不做**,要走产品化路线再单议。可选后续:首屏顶部柔和渐变右上略冷,可暖化。

### D. Housekeeping
- [ ] Investigate/remove the stray sibling `~/WebstormProjects/kokoro-web` (duplicate of `Kokoro/kokoro-web`).

## E. Agent activity rendering (ACTIVE GOAL, set 2026-06-05)

Goal: display real agent activity end-to-end — thinking, tool calls, subagents, CC-style live todo — plus 中断恢复 and a left-rail sessions list. User-chosen: **backend-first with real DeepAgents**, **todo aligned to Claude Code**. Memory: [[kokoro-agent-activity-goal]]. Crux: the pipeline currently DROPS thinking/tools/subagents (agent strips them; protocol doesn't model them) — cross-repo vertical: agent emits → AgentEvent contract → session protocol (Pydantic+Zod, synced) → relay → web reducer+UI.

Key finding: `deepagents 0.6.6` `create_deep_agent(model, tools, system_prompt=, subagents=)` → LangGraph, with built-in `write_todos` (CC todo), `task` (subagents), file ops, `execute`. Reuse it; stream via `astream_events` → map to our events. Tool loops need a tool-calling model: support real (`ANTHROPIC_API_KEY`) AND a scripted tool-calling fake (key-free, deterministic, test-friendly).

- [ ] E1 (agent contract): extend `AgentEvent` kinds — add `thinking.delta`, `todo.updated`, `subagent.started`, `subagent.finished` (`tool.invoked/returned` already exist); document payload shapes; boundary tests (Schema崩塌/空值/序列). Keep agent events loose; strict normalization stays at the session boundary.
- [x] E2 (agent runtime) DONE (agent 63c6031): `run_agent` builds `create_deep_agent` + streams `astream_events(v2)` → pure `translate_stream_event` mapper + `drive_agent_events` envelope. Scripted tool-calling `LocalFakeChatModel` (GenericFakeChatModel can't bind_tools) restores the credential-free path. `KOKORO_DISABLE_STREAMING` for streaming-averse gateways. pytest(44)/ruff/pyright green. **Verified end-to-end with real gpt-5.4: 4× todo.updated evolving pending→in_progress→completed (live CC checklist) + markdown answer.**
  - **Model enabled (1f5da32):** test model via an OpenAI-compatible gateway, configured in `.env` (gitignored — never committed): `KOKORO_MODEL=openai:<model>`, `OPENAI_BASE_URL=<gateway>/v1` (the `/v1` suffix is required), `OPENAI_API_KEY=<key>`. langchain-openai + python-dotenv added; worker load_dotenv().
  - **Gateway constraint:** rejects STREAMING ("concurrency limit exceeded"). Must build the model `disable_streaming=True`. Consequence: no token-level deltas — emit full text per `on_chat_model_end` (one text.delta or text.completed). Token streaming later if the gateway supports it.
  - **Empirical astream_events(version="v2") shapes** (probed): emit on these, skip the rest:
    - `on_tool_start::write_todos` → `todo.updated`, payload `{"todos": data.input["todos"]}` — input.todos IS the CC list `[{content, status: pending|in_progress|completed}]`.
    - `on_tool_start::<name>` (name != write_todos/task) → `tool.invoked` {tool_id, name, args=data.input}; `on_tool_end::<name>` → `tool.returned` {tool_id, name, result=str(data.output)}. (tool_id: data.run_id of the tool event correlates start/end.)
    - `on_tool_start::task` → `subagent.started`; subagent's nested events arrive with metadata identifying it; `on_tool_end::task` → `subagent.finished`. (Handle nesting in a later pass if complex.)
    - `on_chat_model_end::ChatOpenAI` → the AIMessage: if it has tool_calls it's an intermediate turn (skip text); the final one (no tool_calls) → text. (reasoning/thinking content block → thinking.delta when present.)
    - Skip internal graph nodes: `on_chain_*::{LangGraph, model, tools, TodoListMiddleware*, PatchToolCallsMiddleware*}`.
    - Terminal: after the stream ends → `run.completed`; wrap the whole loop and emit `run.failed` on exception (mirror current run_agent's boundary).
- [x] E3 (session protocol) DONE (session 1d58ed5): mirrored the new families in `events.ts` (Zod) + `normalize.ts` (relay into replay/SSE), and fixed a tool-payload drift (inbound expected {tool,input} the agent never sent → now {tool_id,name,args/result}). typecheck/lint/test(51) green.
- [x] E4 (web) DONE (web 7271578): parse + reducer-accumulate the activity families (todos replaced wholesale, toolCalls timeline, subagents, thinking; legacy persist via .default(); per-turn reset). ActivityPanel renders the CC-style todo checklist + tools + subagents + collapsible thinking. lint/typecheck/test(92)/build green.
- [x] **MINIMAL CLOSED LOOP VERIFIED END-TO-END (2026-06-05)** with real gpt-5.4: web→session→agent(DeepAgents)→Redis→normalize→web. Browser showed the live CC-style todo checklist (3 items → completed) beside the markdown answer; transport "实时". tools/subagents/thinking are fully wired + unit-tested but only render when the agent produces them (needs a registered domain tool / subagent spawn / a reasoning model — none triggered by this prompt+gpt-5.4).
- [x] E5 (中断恢复) DONE (web 7e1555c, session 712a34b): on reload/disconnect the web re-subscribes to the in-flight run's SSE and continues (per-conversation backend session id; pendingInput marks in-flight, set on onLive/cleared on settle/stop; 90s fallback). **Fixed a real session bug**: RedisStreamPort shared ONE blocking connection for all BLOCK xreads → dispatch + relays + concurrent SSE starved each other and /stream wedged; now each subscribe uses its own connection (712a34b). Browser-verified: after reloading mid-run the todo checklist progressed (events continued) and the terminal event was handled (the run itself then failed only due to the gateway's concurrency cap — external; the failed state shows 重试). lint/typecheck/test(105 web, 51 session)/build green.
- [x] Floating + collapsible activity panel (web f07f79c): ActivityPanel hovers top-right of the conversation, collapses to a "计划 N/M" pill — real-time progress without scrolling away.
- [x] E6 (sessions list) DONE (web 2876bdf): conversation-store (pure, Zod) replaces single-thread persistence; multi-conversation under `kokoro:conversations`; rail renders the history list (active highlight, hover delete, auto-title from first message), switch/new/delete; switching/deleting aborts an in-flight reply. lint/typecheck/test(103)/build green; browser-verified switching between two conversations.
- [ ] stream_port.py polish (transport foundation, folds in): `_BLOCK_MS` → constructor param; document `_CURSOR_WIDTH`/`_REDIS_FIELD` as cross-language contract constants (NOT .env — would silently break the loop). Filename mirrors `stream-port.ts` (rename both or neither). This is the main remaining engineering cleanup item under the agent-activity / three-repo transport line.

## F. Stream perfection + ordered-parts + turn lifecycle (DONE 2026-06-10)

- [x] Real token streaming (agent `bc316d7`): LangChain `on_chat_model_stream` (`_TEXT_STREAM_INTENT`, `streamed_text`/`sub_streamed_text`) → char-by-char answers; verified live (77 glm-5 deltas, 42 message.delta). Fixed segment-attachment: tool now attaches to the FOLLOWING segment (`active_message_ref is None OR segment_completed`), killing the "tool→text→tool collapses into one bubble" defect.
- [x] Ordered-parts model (web `61715b6`): reducer rewritten around `SessionStep` union (`thinking|tool|subagent|text`, each with `seq`+`messageId`) in `stepsByRun` keyed by runId; `seq` from envelope cursor → render order == emission order. `buildThreadItems` groups consecutive assistant msgs by runId. Layout: ONE avatar/turn + vertical spine of segments, each = bubble ABOVE its process (user overrode research's process-above-text). Spec: `docs/superpowers/plans/2026-06-09-ordered-parts-stream-rewrite.md`. Design panel = 3 cross-validating agents.
- [x] Turn lifecycle affordances (web `9c82c69`): submitted-no-token scaffold (no blank frame); forming bubble (`正在思考` in the bubble slot when process precedes text, never an empty bubble); collapse-on-settle (`open = manualOpen ?? live`, no remount, manual override wins); reconnect anchor (`isReconnecting` → 「重连中…」warm-wood capsule). Single live anchor preserved. 178 vitest + tsc + eslint green; Playwright in-page recorder captured forming→text+caret→collapsed-settle deterministically.
- [x] REAL-backend e2e (DONE 2026-06-20,见 §I 末):curl 驱动 agent(LocalFake)→Redis db15→session(:3001)→SSE 全链路;`/batch` 大重构后合并 main 上事件按序全到:session.created→run.created→todo.updated→tool.invoked→tool.returned→message.delta→message.completed→run.completed。证明重构未破 live loop。(Playwright 真模型联跑仍可选后补。)
- [x] DDD architecture refactor DONE(2026-06-19/20 /batch + 收尾 survey + **/goal 深度重构**,见 §I/§J):god-file split + 三仓类型纯净/边界硬化/零遮掩;**/goal 深度架构重构(8 worker)**——agent worker.py 222→31、driver/control/adapter/subagent 拆分 + H3 cancel bug 修复;session 删死抽象/端口收窄/SSE 抽离;web reducer 616 行拆分/useTransportSession 收敛/悬空能力闭环。全合入 main + 组合态 + 跨栈 e2e 验证。见 §J。

## G. 测试体系 + 真实效果 + 扩展性(DONE 2026-06-13)

- [x] 《测试用例总目录》:62 流程 × 三层矩阵 + 10 缺口全部清账(4 行为修复 + 6 组测试;基数 80/66/175 → 88/74/189)。
- [x] 真实 LLM e2e 实证:完整回答(修 translator 中间叙述丢弃)、刷新中断恢复、todo 4/4、4 张截图。
- [x] 《能力扩展架构设计》:工具/workspace/teams/HITL 分期 + 新 kind SOP。
- [ ] (后续可选)X1 自定义工具首落地;T1a 双 run 并发幂等 e2e;web lint 警告保持零。

## H. HITL/chatbot 缺陷打磨 (设计 2026-06-14,用户全选 + 分层指令)

设计原则(用户定):**各层各管自己的**——agent=执行+自己的 LLM 上下文记忆(可压缩);
session=传输/relay/replay(不碰会话记忆);web=UI+完整展示历史+发 input/决定/取消。

### 控制协议统一(支撑 #2/#3/#8)
control 消息(非 codegen,手定): `{kind:"control", decision:"approve"|"reject"|"cancel", tool_id?}`
- approve/reject 带 tool_id → gate 按自己的 tool_id 匹配(废弃 DecisionCursor 顺序游标);
  reject 不带 tool_id = 广播(放弃 run 时 reject 全部待批)。
- cancel = 取消整个 run(worker 取消该 run 的 task)。
- web: 审批按钮带 toolId;stop/放弃 发 reject(广播) + cancel;session control 端点透传 decision+tool_id;agent gate/worker 消费。

### 增量(逐个 TDD + 门禁绿 + 真机验证)
- [x] #1 worker 并发化(agent only,无契约) DONE(agent 05514b2,8+160 pytest):`_serve` 每 run 一个 asyncio task + 有上限 Semaphore;processed 去重在 spawn 前同步;task 异常不崩 loop。修「awaiting 冻结全局」。
- [x] #8 取消 DONE(agent 9b1002d/session 5d6054d/web d1de82a+c9465be):control 加 cancel;worker 每 run cancel-watcher→task.cancel()→run.completed(cancelled);web stop/放弃发 cancel + 本地 markRunCancelled 收口。真机验证(awaiting→stop→redis cancelled,无 ghost)。
- [x] #3 放弃解阻塞全部 DONE:由 #8 cancel 覆盖(取消整个 run→所有待批门随 task 一起死)。
- [~] #2 并行 tool_id 精确匹配 DEFERRED:探针证实门控工具协程拿不到自己的 tool run_id(run_manager 不注入/config.run_id 为 None),不 hack langchain 内部就无法精确匹配;顺序执行(常态)无此问题,留记录。
- [~] #7 记忆(agent only,各管各的):**核心已接线**——run_agent 传 `{"configurable":{"thread_id": conversation_id}}` + checkpointer 串到 create_deep_agent,worker 用 `InMemorySaver`,跨 run 记忆在 worker 进程生命周期内生效。**剩余**:换持久 saver(跨重启)+ 压缩 middleware。web/session 不变。
- [x] #4 超时设计修复 DONE(agent #12 `dc..`):用户指出审批不该有超时。移除 `drive_agent_events` 的 `asyncio.timeout(120)`——它包住整个 astream(含 HITL 审批等待),用户审批超 120s 会被误杀成 run.failed;HITL 须无限等用户,放弃由 cancel 收口(fetch 工具级 HTTP 截止保留)。`TimeoutError` → 显式 `run.completed{status:"timeout"}`,不混同 reject/失败(契约+session schema 已支持透传)。**剩余(契约后续)**:web `run-completed` 是 generated、当前丢 status,UI 区分 timeout/cancelled 需动 `contract/events.yaml` 重生成,真超时已极罕见,单列。
- [x] #5 control POST 错误处理(web)DONE:`use-hitl-control` POST 失败保持 awaiting、不伪造「已取消」;tool-call-row 审批按钮 catch 失败 → 显「决定发送失败，请重试」+ 复位可重试。非静默。
- [x] #6 plan 模式语义 DONE(agent #14 `bf304d9`,2026-06-20,用户定):**plan = 交互审批,不是只读、不是「只规划不执行」**。移除 `fs_permissions`(它对 plan 硬 deny FS 写=只读,与语义矛盾);plan 仍经 `blocked_tools(plan)` + `gate_tools_interactive` 暂停审批敏感工具(比 default 多拦子代理)。**FS 写暂不可审批化**(deepagents 中间件仅 allow/deny、写工具不在可门控集),故 plan 下 FS 写放行——若需 FS 写审批属后续。文档同步 `docs/requirements/00-product/trust-modes.md`。
- [x] #9 worker processed set 有界 DONE:`ProcessedRunIds`(`MAX_PROCESSED_RUN_IDS=4096`,按插入序超限逐出最旧)限制长驻 worker 内存增长。
- [~] #10 HITL 编辑工具参数:**协议地基 DONE,web 默认 UI 撤回**(2026-06-20)。
  - **保留**:control 协议(手定非 codegen)加可选 `args`——approve 整体替换工具参数。agent #13 `ControlMessage.args` + `await_decision` 返回完整消息 + gate approve 用编辑参数执行;session #9 `controlEventSchema.args` + `?args=<json>` 端点透传(非法→400)。三仓单元 TDD,dormant 待 UI 调用。
  - **撤回(web #11 → revert #12)**:统一 JSON textarea 对所有工具 one-size-fits-all、编辑裸 JSON 易错。用户定:默认简单只读审批,**后续按不同 tool 定制对应 UI**。届时只需在该 tool 的 UI 调 `sendToolDecision(runId,"approve",customArgs)`,底层已通。
  - **后续**:per-tool 定制审批 UI(按工具类型给合适控件)。

## I. 三仓 /batch 全面打磨(DONE 2026-06-19→20,audit workflow + 16 worktree workers)

ultracode `/batch`:只读审计 workflow(36 Explore agent 逐文件对标三仓 CLAUDE.md)→ 16 个主题化、文件互不重叠工作单元 → 各自后台 worktree worker(实现→code-review→门→TDD→PR)。全部合入各仓 main 并在真实 origin/main 验证。Memory: [[kokoro-batch-worktree-orchestration]]。

- [x] kokoro-agent(6 PR,`6c51ba6..d3950d2`):类型遮掩清零(type:ignore/pyright:ignore/cast/Any 兜底全消)、StreamItem→Pydantic strict、工具输入 strict+forbid、bind_tools LSP 合规、settings `T|None` 语义、注释 WHY-only、权限测试参数化。**mypy+pyright 双绿 + 240 pytest + src 零遮掩**。
- [x] kokoro-session(4 PR,`3b975aa..962983b`):Redis 损坏条目崩溃守卫(+SSE 跳脏事件)、入口硬化(端口 Zod 校验/监听错误/进程级 handler)、control 决策走 Zod 非法→400、测试 typed accessor。**typecheck+lint+106 test**。
- [x] kokoro-web(6 PR,经 hitl-wip-base PR#10 `4eb8627..95b3670`):mapper 穷尽性、localStorage Zod、composer type guard、startSessionReply 异步纪律硬化、**use-conversation God-object 拆分(公开 API 不变)**、thread 渲染簇类型纯净。**tsc+eslint+255 test**。
- [x] 顶级 follow-up:#1 真零遮掩(mypy `python_executable` 指向 venv → 删 agent_builder `type:ignore` + yaml override);#2 cancel 功能完整(interactive_gate 抛 `CancelledError` 让 run 级取消独占终止,TDD)。
- [x] 功能层验证(超单测/类型门):web `next build` 生产构建成功;session 启动绑端口+连 Redis+脏端口运行时回退 3001;agent import+worker 测试。
- [~] #3 todo-bar 稳定 id:**判定不做**——跨三仓 `contract/events.yaml` 重生成 vs 一个可能不显现的 React key reconciliation 边角,风险>收益。单列独立后续(真做时按 contract codegen 单源走)。
- [x] **Phase 0 跨栈 e2e 复验(2026-06-20)**:agent(LocalFake)+session+Redis db15,curl 驱动一个真实 DeepAgents run,SSE 八类事件按序全到(todo/tool/text/completed),证明合并后 live loop 未破。顺带验证 SE-2 端口冲突响亮退出。e2e 脚本 `/tmp/kokoro-e2e.sh`。
- 反向修正 §H 过时项:**#9 已完成**(ProcessedRunIds 有界)、**#7 核心已接线**(thread_id=conversation_id + InMemorySaver,标 [~] 待持久 saver)、#5 已处理 control POST 失败。

## J. /goal 三仓深度架构重构(DONE 2026-06-20,自主无交互,8 worker)

3 只读架构审计 agent 通读三仓全源 → ~30 findings → 8 文件互不重叠重构 worker(并行 worktree)→ 逐仓组合态 + 跨栈 e2e 验证 → 全合入 main。详见 claude-progress.md。

- [x] **agent**(4 PR,#15-#18 → `2381450`):H1 drive_agent_events 拆 TextAccumulator+SubagentRouter;**H3 cancel 退化 bug 修复**(ControlChannelClosed,不伪造 reject,TDD);H2 control.py 三层拆分;M1 **worker.py 222→31**(RequestAdmission+RunSupervisor);M2 终态工厂下沉;M3 SubagentCatalog 值对象;M5 adapter 拆 header/tool_input/message;L1 prompt 外置。mypy57/pyright0/251 pytest/零遮掩。
- [x] **session**(1 PR,#10 → `0f1af00`):删 ReplayStore 死抽象、StreamProtocol 端口收窄、HTTP query Zod 化+统一路由、抽 sse-endpoint、MemoryStream lastIndex 消 O(n²)。109 test。
- [x] **web**(3 PR → `dc947d3`):reducer 616 行拆 types/mutations/projection+switch 穷尽(公开 API 不变);抽 useTransportSession 收敛在途句柄+消 eslint-disable;composer 拆;G1-G3 悬空能力 disabled;F11 Zod 双参。255 test。
- [x] 跨栈 e2e 复验:深度重构后 live loop 八类事件按序全跑通。
- [~] control schema codegen:三仓**当前实证一致**;full codegen 不成比例(3 字段手定 schema + event-shaped 生成器),deferred。
- [ ] (低优先后续)agent L4 registry 所有权收敛(动 worker,本轮跳);web G4 run-failed 错误数据用好(retryable/message);web F10 pendingInput 改名;agent M6/session F3 control codegen(同上)。
