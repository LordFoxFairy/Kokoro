# Task A C-1 清理实施证据（2026-10-31）

## 范围

本阶段只执行已确认的 clean-slate 清理，不开始 BFF NestJS 收敛、Repository 重写或业务契约改造。

- BFF：删除全部 schema-evolution CLI、共享 evolution runner 与对应演进 integration tests；package 入口、architecture oracle、反馈/Project Pin 当前测试同步收敛。保留唯一 fresh-only `scripts/apply-schema.mjs` 与 canonical catalog 校验。
- App：删除 `cancelledRuns` HMR 迁移、Conversation hash URL 解析/规范化、无序 snapshot activity 的 synthetic fallback、legacy final proof folding；保留 canonical `runTerminalsById`、ordered public positions、durable final identity、localDraft 与 frozen execution facts。
- Agent：删除基于旧 `mcp/tools.py` source digest 的 `legacy_failed` 展示推断；保留 frozen recipe authority 和当前 journal/activity failure evidence。

## 子仓提交

- `apps/kokoro-bff` `bb4943f` — `refactor(bff): remove schema evolution compatibility`
- `apps/kokoro-app` `4da1c1b` — `refactor(app): remove retired conversation compatibility`
- `apps/kokoro-agent` `c761fad` — `refactor(agent): remove legacy display failure inference`

## 验证

### BFF

- `pnpm typecheck`：通过
- `pnpm build`：通过
- `pnpm lint`：通过
- `pnpm format:check`：通过
- `pnpm test`：2301 pass / 2 skip / 0 fail
- 真实 PostgreSQL 条件测试按资源门禁跳过；没有把 skip 记为通过

### App

- `pnpm lint`：通过
- 受影响 Vitest：6 files / 72 tests pass
- `pnpm typecheck`：仍有基线错误 `src/components/blocks/app-frame/app-frame-main-surface.tsx` 的 `onReconnect` 属性类型不匹配；该错误不由本 C-1 修改引入

### Agent

- `uv run ruff check src/kokoro_agent/application/run_display.py src/kokoro_agent/infrastructure/checkpoint_display.py tests/unit/chat/test_historical_mcp_display.py`：通过
- 受影响 display/contract/http 单测：130 pass

### App native runtime slice（子仓 `4c41104d`）

- `tests/ui/use-session-state.test.tsx`：79 pass；覆盖 native projection 直接 admission，确认不发 Product CSRF/refresh POST。
- archived/shared/session archive/share adapters 与 sign-in failure recovery focused：68 pass；验证 native admission 迁移不改变 legacy bearer fallback、最终 admission recheck、取消和错误闭集。
- `tests/server/product-bff.test.ts`、`tests/ui/product-auth-client.test.ts` 与相关 session tests：focused pass。
- touched-file ESLint：pass。
- `pnpm typecheck`：仍为既有 `src/components/blocks/app-frame/app-frame-main-surface.tsx:onReconnect` 类型错误。

### C-1.3 Native owner cutover slice（2026-10-31）

本轮只推进仍依赖 bearer 的三组 owner surface，不删除旧 Product Session/RP：

- IAM `108beedf`（runtime `6b26433`）：在现有 `InternalAuthGuard` 中增加显式 native owner 分支。BFF direct `session_admission` credential、allowlisted Cookie、固定 Origin 和 request id 通过后，IAM fresh-recheck issuer session、active tenant、membership、session id；account profile/session 使用 native 标记跳过 OAuth grant lookup，但保留 Product tenant、session、CAS、事务、Audit 和错误边界；Team 继续由 owner snapshot 复核角色权限。既有 bearer 分支保持不变。
- BFF `65cf2082`：`ownerSessionAuth` 只在 account profile/sessions/team 路由上把原生 allowlisted Cookie + 固定 Origin + fresh direct credential 传给 IAM；legacy bearer 仍只在未迁移 surface 使用，native 请求不制造空 bearer。IAM owner clients 的响应闭集、预算、取消、错误映射保持。
- App `4c41104d`：account profile update、account sessions、Team adapter 改用 `admittedProductSession` 与同一 native proof；native synthetic TTL 不参与身份快照比较，仍以每次 BFF admission 复核 subject/session/expiry。旧无 native cookie 的 Product Session fallback 保留在迁移边界内。

### C-1.3 focused verification

- IAM：`pnpm typecheck`、`pnpm lint`、`vitest run test/unit/internal-auth.guard.test.ts test/unit/account-profile/account-profile-service.test.ts test/unit/account-sessions/account-session-cursor.test.ts`，56 pass。
- BFF：`pnpm typecheck`、`pnpm lint`、`pnpm build`，以及 user-admission/account-profile/account-sessions/team focused tests，96 pass。
- App：`tests/server/account-profile-update.test.ts`、`tests/server/account-sessions.test.ts`、`tests/system/team-product-route.test.ts`，116 pass；touched route/native tests保持通过。

本 slice 尚未覆盖 App profile read 的 userinfo owner contract、sign-in/sign-out/tenant-switch/revocation 的真实旅程收据、旧 RP/Product Session 删除，也未开始 LegacyRoutes/global composition/Repository/Service/Port 清理；A-01/A-02/A-07 继续停写。

## 停止线

C-1 兼容清理的主仓复核补充（2026-10-31）：

- App 受影响 Vitest：7 files / 91 tests pass；受影响 ESLint：pass。
- Agent display/contract/http focused pytest：24 pass；ruff touched-file check：pass。
- BFF Nest foundation/feature graph gates：4 pass；typecheck/build/lint/format：pass。
- BFF `pnpm test` 曾在与并行 build 竞争时出现 dist 缺失、既有 contract fixture failures 和 pending tests；该结果不计为 C-1 全量通过，需在所有 BFF worker 停写后重跑。

C-1 旧兼容实现证据已固定；C-2 feature graph 已开始但 LegacyRoutes adapter、global composition 和大 Port 仍保留。C-3/C-4、C-1.3 auth cutover 未宣称完成。

## G0/C-2～C-4 复核（2026-10-31）

G0 设计门已由 reviewer 通过，IAM native-session artifact 已固定：

- `apps/kokoro-iam` `461a57ab486e1041d8d5c926103443e030f191fb`
- `contract/openapi/native-session-admission.v1.json`
- version `1.0.0`
- SHA-256 `5cf59df4b7bd9853edfd2eabb31afc236c0ec0db371f9737706fc129484fd83f`

BFF 收敛提交：

- `3f643ef`：Nest 唯一 runtime entry、AppModule、Config/Database/Redis/Lifecycle/Health/LegacyRoutes adapter。
- `cd4ffb1`：Account/Chat/AgentRuns/Projects/AG-UI/Skills/MCP/Billing/System/Music/ScheduledTasks canonical feature graph。
- `aacf1c5`：删除 global `PersonalizationRepository`，迁移为 AccountModule feature-local `PersonalizationProvider`/token。
- `a9bd12d`：刷新 Nest lockfile 后的八个 consumer manifest pin，并同步 R257 design path。

Root gitlink 已更新至 BFF `a9bd12da7b6ed0a8a128f4ee387a19ee15f49a17`；最新 Root integration commit 为 `3633bea2`。

### 新鲜验证

- BFF `pnpm format:check`：通过。
- BFF `pnpm lint`：通过。
- BFF `pnpm typecheck`：通过。
- BFF `pnpm build`：通过。
- BFF `pnpm test:architecture`：33/33 通过。
- BFF `pnpm test:nest-architecture`：4/4 通过。
- BFF contract governance / Platform / Storage focused gate：52/52 通过。
- BFF `pnpm test`：2301 pass / 2 skip / 0 fail；skip 为受资源门禁保护的真实 PostgreSQL 条件测试，未将 skip 计为通过。
- App native adapter/probe/adapters focused Vitest：8 files / 155 tests pass；ESLint focused pass；既有全仓 typecheck 的 `app-frame-main-surface.tsx:onReconnect` 错误仍为基线。
- Agent display/contract/http focused pytest：24 pass；ruff touched-file check pass。
- Root `python3 scripts/verify-repository-topology.py`：PASS。
- Root `git diff --check`：通过。

### 停写后 App 全量门禁复核（2026-10-31）

- `pnpm test`：362 files；6890 pass、2 skip、7 fail。失败集中在既有 process/activity UI 断言（`segment-process.test.tsx` 4、`process-activity-groups.test.tsx` 2）和 sign-out 页面文案契约 1；另有 stored-session fixture 因缺少 `KOKORO_TEST_REDIS_URL` 触发环境缺口。该结果不计为 App 全量通过，也不扩大 C-1.3 代码范围。
- native session focused/probe 测试保持通过；C-1.3 当前仍以 focused evidence 交付，待真实 IAM→BFF→App journey 收据和现有 App baseline 收敛后再关闭。

### 仍未越过的停写边界

C-1 compatibility cleanup、C-2 foundation/feature graph、C-3 personalization slice 和 C-4 default contract-pin/test gate 已交付；但 C-1.3 first-party native-session runtime cutover、LegacyRoutes 全量替换/旧 dispatcher 删除、其余 global Repository/Service/Port 拆分尚未完成。因此 A-01/A-02/A-07 继续保持未启动，不能把当前证据标记为 C-1～C-4 完整通过。

C-1.3 native-session runtime/consumer 已交付两段闭环（admission proof 与 account/Team owner proof），但尚未宣称全量 auth cleanup：

- IAM child `108beed`（runtime `6b26433`）：新增 `POST /internal/v1/native-session-admission/verify` controller/service/schema；并将 account profile/session 与 Team owner operations 接入显式 native proof 分支；独立 `kokoro-bff/session_admission` direct credential；严格 Cookie/Origin/Accept/body/duplicate-header 校验；fresh Better Auth session、active tenant、membership、role permissions 查询；native error closed set；生成 `contract/openapi/iam.internal.v1.json`。
- BFF child `65cf208`：新增受限 credential reader、native transport/client、Cookie allowlist、Origin 校验、AccountModule/runtime wiring 和 owner transport forwarding；配置 `KOKORO_BFF_IAM_SESSION_ADMISSION_CREDENTIAL_FILE` 与 `KOKORO_IAM_WEB_ORIGIN`。启用两项配置时用户准入不再发送浏览器 bearer；未迁移的独立 owner authorization consumers 仍保持 fail-closed。
- App child `d944ac3` + `f0ffd2d2` + `0bd1481c` + `de40f9c3` + `68813cd3`：为 `/api/session/*` 同源适配器增加 IAM native-session Cookie 投影；只转发 allowlisted IAM cookies、固定配置 Origin、request-id 与 web-bff service credential，过滤 Product/第三方 cookie，重复或空 native cookie fail-closed。`admittedProductSession` 在 native cookie 存在时改为通过 BFF `/v1/me` 获取当前 subject，并把 native cookie proof 传给后续 BFF owner calls，不再发送 bearer；App `/app` SSR shell 和 `/api/auth/session` probe 现在优先使用同一 native identity proof，native probe 不再发 Product CSRF/refresh POST，native sign-out 返回 IAM end-session relay；archived/shared task 与 session archive/share adapters 已切到同一 admission helper，sign-in failure recovery 也先检查 native proof，并有单测覆盖 native recovery redirect。当前仍保留 Product Session 作为无 native cookie 的过渡路径，account profile/sessions/team 等仍依赖 IAM bearer owner surface，尚未切换。
- Root integration `1c63b007`：同时 pin IAM `108beed`、BFF `65cf208` 与 App `4c41104d`。

本次主仓复核：BFF focused owner/native tests 96 pass，IAM focused native guard/account tests 56 pass，App account/profile/session/Team focused tests 116 pass；各自 typecheck/lint/build 通过。App 全仓 typecheck 仍仅有既有 `app-frame-main-surface.tsx:onReconnect` baseline。全量验证已在 worker 停写后重跑，dist 缺失的并行竞争结果不计入验收。

仍未完成：App 尚保留 account profile/sessions/team 等依赖 IAM bearer owner surface；旧 first-party RP/Product Session 删除、其余 App API route 切换、BFF LegacyRoutes 全量替换/旧 dispatcher 删除，以及剩余 global Repository/Service/Port 收敛仍在停写线之后。故 A-01/A-02/A-07 继续保持未启动，C-1～C-4 不标记为全部通过。

### Chat direct read cutover（2026-10-31）

BFF child `5659b1d` 将 direct/no-`project_ref` 的 Chat GET collection、session snapshot、message list、message parts 和 Run process reads 接入 `ChatModule`，同时在 Nest `ChatMiddleware` 与 raw `createBffServer` 注册 `handleChatBusinessReadRequest`。该 adapter 先执行 `authorizeUserRequest`，再执行 Chat owner recheck，最后复用 `liveChatBusiness` 的既有分页、cursor、read budget、取消、error envelope 和 request-id 语义；`ChatBusinessProvider` 让这些 reads 不再依赖全局 `BffBusinessStore`。Chat POST、events、project-scoped reads、AgentRuns/AG-UI 仍在下一 slice，LegacyRoutes/global composition 尚未删除。

验证：direct Chat read 2/2、BFF mock contract 25/25、Nest architecture 18/18、BFF architecture 34/34、`pnpm lint`、`pnpm typecheck`、`pnpm build`；停写后串行 `pnpm test` 为 2316 tests / 2299 pass / 15 fail / 2 skip，15 项失败仍为既有 Artifact/Personal Storage Product HTTP、Project exact-download、Admin Web credential fixture 与 anonymous Share fixture。

### Public Share provider handoff（2026-10-31）

BFF child `330e439` 将 `PublicShareApplicationService` 从隐式 `BffBusinessStore` 查找改为 `ChatModule` → `PUBLIC_SHARE_SERVICE` → `LegacyRoutesRuntime` → `BffCompositionOptions.publicShareService` 的显式链路。`GET /v1/shared/{shareId}` 已继续使用 `composition.publicShareService`，store 字段仅作为未迁移 raw/test composition fallback；本提交不宣称 LegacyRoutes 或 global composition 已删除。

验证：BFF build、lint、typecheck 通过；Nest runtime architecture 5/5；Skill share/exact-download focused 40/40。

### Scheduled current-read provider handoff（2026-10-31）

BFF child `46bb5ac` 将 `ScheduledTaskReadService` 从 transitional runtime 内部按 `BffBusinessStore.services.scheduledTasks` 组装，改为 `ScheduledTasksModule` → `SCHEDULED_TASK_READ_SERVICE` → `LegacyRoutesRuntime` → `BffCompositionOptions.scheduledTaskReader` 的显式链路。current-read route 继续复用 `composition.scheduledTaskReader`，mutation/callback/outbox 保持在未迁移清单中；本提交不宣称 ScheduledTasks 或 LegacyRoutes 完成删除。

验证：BFF build、lint、typecheck 通过；Nest runtime architecture 5/5；scheduler focused 38/38。

`814d3e6` 仅修正 Nest feature architecture 对 LegacyRoutes 扩展 imports 的精确断言，验证结果为 20/20；不改变运行时行为。

### Chat/Project service provider handoff（2026-10-31）

BFF child `d2b0bfe` 将 `CHAT_SERVICE`、`CHAT_TURN_SERVICE`、`PROJECT_SERVICE` 从 `ChatModule`/`AgentDispatchModule`/`ProjectsModule` 显式注入 `LegacyRoutesRuntime`，并传入 `createBffComposition`。Chat authorization 的 `chatProvider` 改为优先使用 `composition.chatTurnService`；global `BffApplicationServices` 仍保留给未迁移的 raw/test 与 Chat POST/Agent mutation 路径，不宣称 LegacyRoutes 或聚合服务已删除。

验证：BFF build、lint、typecheck 通过；Nest runtime/feature architecture 20/20；Chat+Scheduler focused 156/156。

### Project skill-selection provider handoff（2026-10-31）

BFF child `b9ac010` 将 `PROJECT_SKILL_SELECTION_PROVIDER` 从 `ProjectsModule` 接入 `LegacyRoutesRuntime`，`createBffServer` 优先读取 `composition.projectSkillSelectionProvider`，并保留旧业务 store 构造仅作 raw/test fallback。该切片没有删除 Project service、LegacyRoutes 或 exact-download compatibility path。

验证：BFF build、lint、typecheck 通过；Nest runtime/feature architecture 20/20；Project pin/skill focused 12/12，exact Project download 的 10 项既有 fixture failures 单列。

### Project MCP recommendation provider handoff（2026-10-31）

BFF child `1301269` 将 `PROJECT_MCP_RECOMMENDATIONS_PROVIDER` 从 `McpModule` 接入 `LegacyRoutesRuntime`，raw recommendation route 优先读取 `composition.projectMcpRecommendationsProvider`；旧 business-store provider 构造保持为 raw/test fallback，不扩大 MCP personal execution 或 Task B 范围。

验证：BFF build、lint、typecheck 通过；Nest runtime/feature architecture 20/20；MCP recommendation/publication focused 60/60。

### Skill download/specification provider handoff（2026-10-31）

BFF child `c8c3259` 将 `SKILL_EXACT_DOWNLOAD_SOURCE` 与 `SKILL_SPECIFICATION_SOURCE` 从 `SkillsModule` 接入 `LegacyRoutesRuntime`，使 raw composition 优先消费 feature-owned exact-download/specification provider；business-store skill-share/usage fallback 仍只服务未迁移 raw/test composition。

验证：BFF build、lint、typecheck 通过；Nest runtime/feature architecture 20/20；Skill download/share/specification focused 60/60。

### Migrated Chat path LegacyRoutes bypass（2026-10-31）

BFF child `630efbf` adds an explicit `LegacyRoutesMiddleware` boundary. Migrated Chat paths—public share, archive/shared tasks, direct Chat reads, feedback, regeneration and move—now bypass `LegacyRoutesRuntime`; negative tests retain Chat POST/events/title/delete/share and project-scoped reads in the transitional dispatcher until their feature bundle is cut over. Raw `createBffServer` compatibility remains unchanged.

验证：LegacyRoutes bypass 2/2；Nest runtime/feature architecture 20/20；Chat/feedback/regeneration focused 34/34；build/lint/typecheck 通过。

### Direct Chat mutation cutover（2026-10-31）

BFF child `3961450` moves direct no-`project_ref` Chat title/delete/share mutations into `ChatModule`. `CHAT_IDEMPOTENCY` owns the PostgreSQL receipt adapter; `handleChatMutationRequest` preserves admission, canonical fingerprint, replay/conflict/pending behavior and delegates business semantics to the existing `liveChatBusiness`. Project-scoped mutations, Chat POST messages and events remain transitional by design.

验证：direct Chat mutation 1/1、LegacyRoutes bypass 2/2、Nest runtime/feature architecture 20/20、BFF mock contract 25/25、build/lint/typecheck 通过。

### Direct Chat events cutover（2026-10-31）

BFF child `76b9402` moves direct no-`project_ref` AG-UI events into `ChatModule` + `AguiModule`. The feature graph now owns projection, consumer registration, session runtime and source-active gating for this route, while reusing `liveAgentSession` for durable replay/SSE behavior. Project-scoped events, Chat POST messages and the LegacyRoutes projector worker remain transitional.

验证：本轮选定 AG-UI replay/runtime/SSE tests、LegacyRoutes bypass 2/2、Nest runtime/feature architecture 20/20、BFF architecture 34/34、build/lint/typecheck 全部通过。

### Project-scoped Chat owner sharing（2026-10-31）

BFF child `ff14c86` extracts `ProjectAccessModule` as the single ProjectService/selection provider owner and lets ChatModule consume it. This extends title/delete/share mutations and AG-UI events to project-scoped requests without introducing a second ProjectRepository or service; Chat POST remains the next route bundle.

验证：project-scoped Chat mutation focused 1/1、LegacyRoutes bypass 2/2、Nest runtime/feature architecture 20/20、build/lint/typecheck 通过。

### Chat POST cutover（2026-10-31）

BFF child `ff14c86` moves Chat message submission into `ChatModule`. `SkillInstallationAccessModule` is now the shared installation client owner consumed by Skills, Projects and Chat; the feature route preserves ChatTurn outbox commit, project access, skill qualification, idempotency, cancellation and canonical 202 response behavior. LegacyRoutes no longer receives `/v1/sessions/:id/messages` POST.

验证：Chat message POST 1/1、BFF mock contract 25/25、LegacyRoutes bypass 3/3、Nest runtime/feature architecture 20/20、build/lint/typecheck 通过。

### Agent run-control cutover（2026-10-31）

BFF child `a5b94c0` moves run-control POST into `AgentRunsModule`. `AGENT_CONTROL_IDEMPOTENCY` owns the receipt adapter; the route reuses shared Chat/Project providers and `liveAgentSession` for Agent control receipt validation, resume state checks, queued cancellation startup bridging, and bounded cancellation. Remaining Agent session/run paths and projector lifecycle stay transitional.

验证：Nest runtime/feature architecture 20/20、BFF architecture 34/34、LegacyRoutes bypass coverage、build/lint/typecheck 通过。

### AgentRuns LegacyRoutes boundary（2026-10-31）

BFF child `ba8ab60` extends the negative `LegacyRoutesMiddleware` boundary to the AgentRuns-owned internal admission/binding paths and exact Run display path. `isAgentRunsInternalRequest` and the existing `isRunDisplayRequest` matcher now bypass the legacy runtime for these routes, while the feature middleware remains the only handler for method validation, credential checks, owner reads, response caps, cancellation and error envelopes. No new Repository/Service/Port or compatibility alias was introduced.

验证：BFF build/lint/typecheck；BFF architecture 34/34；Nest runtime/feature architecture 20/20；Agent model-admission/settlement/recovery, project-execution-binding and Run display focused tests 99/99；LegacyRoutes bypass 2/2。`LegacyRoutes`、Agent dispatch worker lifecycle、剩余 session/run paths 与 global composition 仍未删除，C-2/C-3/C-4 不提前关闭。

### Agent outbox worker ownership（2026-10-31）

BFF child `ba8ab60` moves Agent dispatch and cancellation outbox worker construction/lifecycle into `AgentDispatchModule`. The feature module now owns the Postgres repository adapters, delivery adapters, worker identity, start/stop hooks and explicit disabled-agent behavior; `LegacyRoutesRuntime` receives the same feature-owned worker instances only as a raw-composition shutdown seam and no longer starts them. Explicit `null` options prevent `createBffComposition` from constructing a second production worker, while raw/test composition without the feature option keeps its compatibility worker behavior.

验证：build/lint/typecheck；Nest runtime/feature architecture 21/21；BFF architecture 34/34；Agent dispatch/cancellation/control focused 54/54；LegacyRoutes bypass 2/2。AG-UI projector、scheduled/project-scope worker lifecycle、剩余 session/run route 与 global composition 仍待按同一 owner 规则迁移。

### AG-UI projector ownership（2026-10-31）

BFF child `ba8ab60` moves the AG-UI projector repository/source-reader construction and start/stop lifecycle into `AguiModule`. The feature provider reuses the canonical `AGUI_PROJECTION`/consumer repositories and the existing Agent source contract, returns `null` when Agent projection is disabled, and is passed into raw composition only as a shutdown seam. `LegacyRoutesRuntime` no longer starts the projector; explicit-null composition options prevent a second production projector while raw/test composition retains its standalone fallback.

验证：build/lint/typecheck；Nest runtime/feature architecture 22/22；BFF architecture 34/34；AG-UI projector focused cases 6/6；其余 direct message-parts/replay imports仍受既有 Node strip-only/缺失 `.js` fixture baseline影响，不作为本 slice 通过证据。Scheduled/project-scope worker lifecycle、剩余 session/run route 与 global composition 仍待迁移。

### Scheduled outbox worker ownership（2026-10-31）

BFF child `ba8ab60` moves the scheduled-task outbox repository, scheduler delivery and worker lifecycle into `ScheduledTasksModule`. The module owns the stable worker identity and shutdown hook; `LegacyRoutesRuntime` receives the feature instance only for raw-composition shutdown and no longer starts it. Explicit-null composition options prevent a duplicate production scheduler worker; raw/test composition without the feature option retains its compatibility fallback.

验证：build/lint/typecheck；Nest runtime/feature architecture 23/23；BFF architecture 34/34。Scheduled task outbox behavior remains covered by the existing scheduler/outbox suites. Scheduled Agent dispatch/terminal and project-scope release worker lifecycle、剩余 session/run route 与 global composition 仍待迁移。

### Project-scope release worker ownership（2026-10-31）

BFF child `ba8ab60` moves the project-scope release outbox repository, Storage release client and worker lifecycle into `ProjectsModule`. The module keeps the existing storage-enabled condition and bounded release/settlement behavior, owns the worker identity/start/stop hooks, and exposes the feature instance to raw composition only for shutdown. Explicit-null composition options prevent a duplicate production worker; raw/test composition without the feature option retains its compatibility fallback.

验证：build/lint/typecheck；Nest runtime/feature architecture 24/24；BFF architecture 34/34。Project resource/delete/scope-release focused contracts remain on the existing owner boundary. Scheduled Agent dispatch/terminal lifecycle、剩余 session/run route 与 global composition 仍待迁移。

### Scheduled Agent worker ownership（2026-10-31）

BFF child `ba8ab60` moves the scheduled Agent dispatch/terminal repository, Agent delivery/source adapters and worker lifecycle into `ScheduledTasksModule`. The feature keeps the existing Agent-enabled/upstream-configured condition, stable worker identities, bounded concurrency/retry/backoff and shutdown ordering; `LegacyRoutesRuntime` receives the feature instances only for raw-composition shutdown and no longer starts them. Explicit-null composition options prevent duplicate production workers while raw/test composition retains its fallback.

验证：build/lint/typecheck；Nest runtime/feature architecture 24/24；BFF architecture 34/34；scheduled Agent focused tests 15 pass / 13 resource-gated skip；其余 skips 为真实 PostgreSQL/Redis 条件测试，不计为通过。剩余 session/run route、global composition 与 C-4 全量 owner gate 仍未关闭。

### Project-scoped Chat read cutover（2026-10-31）

BFF child `ba8ab60` extends `ChatModule` business-read ownership to `project_ref` collection/session/message/parts/process reads. The adapter now passes the shared `ProjectAccessModule` owner into Chat authorization, preserving current project existence/recheck, Chat owner reads, pagination/cursor, cancellation and error envelopes; direct reads remain compatible without a project provider in raw focused fixtures. The `LegacyRoutesMiddleware` boundary now locks project-scoped Chat reads as migrated.

验证：Chat business direct/project focused 4/4；LegacyRoutes bypass 5/5；build/lint/typecheck；Nest runtime/feature architecture 24/24；BFF architecture 34/34。Remaining session/run families, LegacyRoutes runtime/global composition and C-3 Port census remain open。

### C-1.3 native-session focused revalidation（2026-10-31）

当前 App/IAM checkout 复验：IAM `test/unit/native-session-admission.test.ts` 3/3；App native-session/BFF adapter、native auth route、sign-in flow、tenant-route focused 22/22；App account profile/session/Team、sign-in/sign-out failure and recovery focused 145/145。真实 IAM_TEST_ADMIN_URL/Redis 集成 host 与跨 App→BFF→IAM sign-in/tenant-switch/revocation journey 仍是环境收据缺口，旧 RP/Product Session 尚未删除。

### Scheduler callback cutover（2026-10-31）

BFF child `ba8ab60` moves `POST /internal/bff/scheduled-tasks/dispatch` into `ScheduledTasksModule`. The feature owns the canonical `ScheduledTaskService`, scheduler receipt repository and scheduled-Agent dispatch repository; the middleware preserves service authentication, webhook/body validation, receipt claim/CAS, frozen task revision checks and 202/409/503 mapping. `LegacyRoutesMiddleware` bypasses the exact callback path while raw `createBffServer` compatibility remains unchanged.

验证：BFF build/lint/typecheck；Nest runtime/feature architecture 24/24；BFF architecture 34/34；scheduler/scheduled-agent focused 28 tests（13 real-resource cases remain environment-gated skip）；LegacyRoutes bypass 3/3。

### Scheduled task mutation cutover（2026-10-31）

BFF child `ba8ab60` moves scheduled-task create/update/delete/retry and project-scoped scheduled-task create mutations into `ScheduledTasksModule`. The feature middleware owns native admission, strict input parsing, project/task owner rechecks, persistent idempotency receipts, stable task IDs, CAS/outbox service calls and canonical response/error mapping. The shared `PostgresScheduledTaskRepository` is reused by read, mutation and scheduler callback paths; no second task repository or receipt store is introduced.

验证：build/lint/typecheck；Nest runtime/feature architecture 24/24；BFF architecture 34/34；scheduler focused 14/14；LegacyRoutes bypass covers the callback and scheduled Chat/Agent boundaries. Remaining scheduled current-read/full owner integration and C-4 full suite remain open。

### Scheduled mutation canonical adapter（2026-10-31）

BFF child `e1f2b81` centralizes scheduled-task create/update/delete/retry and project-scoped create business execution in `scheduled-task-mutation-native.ts`, shared by `ScheduledTaskMutationMiddleware` and raw `createBffServer`. The old `live-bff.ts` dispatcher is deleted; authorization, idempotency lineage, owner checks, stable task IDs, outbox service calls and error mapping now have one implementation. The raw server retains only the pre-admission check needed before the generic receipt claim.

验证：BFF build/lint/typecheck；Nest runtime/feature architecture 24/24；BFF architecture 34/34；scheduler + BFF mock focused 39/39；business-store integration 6 pass / 75 environment-gated skip。C-2 LegacyRoutes runtime and C-3 global provider census remain open。

### Project command/read cutover（2026-10-31）

BFF child `e1f2b81` moves project create/instruction command handling into `ProjectsModule` through `ProjectMutationMiddleware`, with a feature-owned `PROJECT_IDEMPOTENCY` provider. Native admission, strict JSON/name/instruction validation, persistent idempotency replay/conflict handling, project owner scope, slug-conflict mapping and canonical response envelopes remain unchanged. The project core-read adapter now also owns `GET /v1/projects/:id/tasks`; the duplicate `liveBffBusiness` task branch was removed. No second ProjectService, Repository or SQL writer was introduced.

验证：BFF build/lint/typecheck；Nest runtime/feature architecture 24/24；BFF architecture 34/34；BFF mock contract 25/25；Project pin focused 15/15；business-store integration 在缺少 PostgreSQL/Redis 时 6 pass / 75 skip。Nest 与 raw `createBffServer` 现在共用同一 `project-mutation-native` adapter，未保留第二套 create/instruction 实现；C-2/C-3/C-4 和 A gates remain open。

### Personal Billing owner cutover（2026-10-31）

BFF child `e1f2b81` moves personal Billing routes (`GET /v1/billing/summary`, `GET /v1/billing/ledger`, `PUT /v1/billing/credit-account`, `GET /v1/billing/plans`, `POST /v1/billing/checkout`) into `BillingModule`. `BillingPersonalMiddleware` and `billing-personal-native` share one admission, query validation, owner transport, bounded cancellation, response mapping and persistent idempotency provider; the old `owner.ts` Billing branches are deleted. Existing Billing owner and BFF mock fixtures remain unchanged.

验证：BFF build/lint/typecheck；Nest runtime/feature architecture 24/24；BFF architecture 34/34；Billing personal + BFF mock 66/66。Remaining owner route families and LegacyRoutes/global composition deletion remain open。

### System model catalog cutover（2026-10-31）

BFF child `e1f2b81` moves `GET /v1/models` into `SystemModule` through `SystemModelCatalogMiddleware` and `system-model-catalog-native`. The exact owner query projection, System credential transport, model catalog validation, request-id and upstream error mapping are shared by Nest and raw `createBffServer`; the duplicate `owner.ts` model branch is deleted.

验证：BFF build/lint/typecheck；Nest runtime/feature architecture 24/24；BFF architecture 34/34；BFF mock contract 25/25。Remaining owner projection routes and LegacyRoutes/global composition deletion remain open。

### MCP platform projection cutover（2026-10-31）

BFF child `e1f2b81` moves `GET /v1/mcp/servers` and `GET /v1/mcp/connections` into `McpModule` through `PlatformProjectionMiddleware`. Admission, MCP budget, strict query/body validation, named Platform projection client, cursor/error mapping and no-store response semantics are shared by Nest and raw `createBffServer`; `owner.ts` no longer dispatches Platform projections. The retired System/Skills fallback is isolated in `retired-owner-native` rather than the owner dispatcher.

验证：BFF build/lint/typecheck；Nest runtime/feature architecture 24/24；BFF architecture 34/34；platform projection + BFF mock 50/50。Remaining MCP/Skills owner surfaces and LegacyRoutes/global composition deletion remain open。

### Owner transport module cleanup（2026-10-31）

BFF child `e1f2b81` renames the remaining shared owner transport helper from `owner.ts` to `owner-request.ts` and removes the obsolete route-module name. System model catalog and Music now consume the explicit transport helper; no `liveOwnerBusiness` dispatcher remains.

验证：BFF build/lint/typecheck；Nest runtime/feature architecture 24/24；BFF architecture 34/34；BFF mock 25/25；Billing personal 66/66。

### Personal MCP route cutover（2026-11-01）

BFF child `e1f2b81` moves the full browser-private Personal MCP surface into `McpModule` through `McpPersonalMiddleware`. The route now consumes only a narrow `McpPersonalProvider` (personal client, MCP authorization, session admission), while raw `createBffServer` remains structurally compatible. Server icon handling shares the same narrow provider; no `BffServerComposition` construction or LegacyRoutes runtime dependency was added.

验证：BFF build/lint/typecheck；Nest runtime/feature architecture 24/24；BFF architecture 34/34；Personal MCP HTTP/command + BFF mock 106/106。Remaining Library/personal-file route families, LegacyRoutes/global composition deletion and C-4 full suite remain open。

### Library and personal-file route cutover（2026-11-01）

BFF child `e1f2b81` moves `/v1/library`, artifact reads/downloads, personal file download and personal file upload into `AccountModule` through `LibraryMiddleware` and `library-native`. The feature owns its artifact repository and idempotency provider; raw `createBffServer` uses the same adapter before the transitional mutation receipt. Partial raw fixtures remain supported without requiring unrelated Project/Chat services.

验证：BFF build/lint/typecheck；Nest runtime/feature architecture 24/24；BFF architecture 34/34；Library/personal-file + BFF mock 58/58。Remaining residual Skills routes, LegacyRoutes/global composition deletion and C-4 full suite remain open。

### C-4 full-run revalidation（2026-10-31）

在 `e1f2b81` 后串行启动 BFF `pnpm test`：focused 早期继续出现既有 R357 shared-summary fixture failures，随后停在 `test/contract/skill-specification-http.test.mjs` 的长时间 pending 状态；已手动终止，未取得完整汇总，不能计作 C-4 通过。进程状态已复核清零；本次切片以 build/lint/typecheck、Nest architecture、BFF architecture、scheduler 39/39、BFF mock 25/25 作为有效证据。

BFF child `7cf1312` closes the remaining retired System/Skills fallback at the feature boundary. `SystemMiddleware` and `SkillsMiddleware` now invoke `handleRetiredOwnerRequest` after their native handlers; the adapter performs the standard IAM user admission and returns the existing `system_projection_not_configured` / `platform_operation_not_available` 503 contract without entering `LegacyRoutes`. Verification after the cutover: build, lint, typecheck, Nest architecture 24/24, BFF architecture 34/34, and mock contract 25/25 all passed. This is a route-boundary cleanup only; LegacyRoutes/global composition and the C-4 full serial gate remain open.

BFF child `86c714b` restores the named `SkillShareRepository` seam for transitional raw/test composition by reusing `skillShareRepositoryFromBusinessStore` when only the legacy service-shaped fixture is present. This fixes the existing shared-revision contract without adding a second owner or repository: `test/contract/skill-specification-http.test.mjs` now passes 110/110, including the exact old-revision share and fail-closed cases.

BFF child `34899e0` applies the same compatibility extractor to `ExactSkillDownloadService`: raw/test composition now recognizes the service-shaped SkillShare repository when constructing the project/personal exact-download source. Project exact-download and package inspection coverage is green at 18/18; no new Project or Skill repository is introduced.

Root validation follow-up: `require_free_web_port` now resolves the patched `WEB_PORT` at call time instead of capturing 3310 in a default argument. The focused launcher suite is 61/61; the serial Root governance suite is 1845 passed, 3 skipped, with one remaining environment failure because `@aws-sdk/client-s3` is not installed for the W2 Storage smoke. This is recorded as an environment gap, not a C-4 pass.

BFF child `a725bdc` closes the remaining raw/test composition gaps: System administrator routes stay behind the explicit route-handler seam, Skills administrator routes terminate natively even when a raw test handler is present, and service-shaped `publicShares` is recognized as the transitional public-share provider. After installing the locked Storage dependencies, Root governance is now 1846 passed / 3 skipped, and the complete BFF suite is 2317 tests / 2315 passed / 0 failed / 2 skipped in 203.5s. C-4 BFF and Root owner gates are green; cross-owner IAM/App real journey and LegacyRoutes/global composition deletion remain open.

BFF child `b7b30e5` moves browser Custom API CRUD into `McpModule` via `CustomApiMiddleware` and a feature-owned `CUSTOM_API_CLIENT`; the raw server now passes only the narrow client seam to the shared route. Project MCP recommendations reuse the same client instead of constructing a duplicate. Custom API focused tests remain 7/7, Nest architecture 24/24, and the full BFF suite remains green at 2317/2315/0/2.

BFF child `a09176a` narrows the ScheduledTask raw compatibility path to explicit `PROJECT_SERVICE` + `SCHEDULED_TASK_SERVICE` providers. Authorization and mutation execution no longer consume `BffBusinessStore.services` in production route code; the same canonical services remain the only owner for raw/test fallback. Scheduled/project focused validation is 129/129 and the complete BFF suite remains 2317/2315/0/2.

BFF child `06ae1a6` applies the same provider boundary to the Scheduler callback: raw `createBffServer` now assembles `SchedulerDispatchProvider` explicitly, and the scheduler route no longer unwraps `source.services.scheduledTasks`. Architecture, scheduler, mock and full BFF gates remain green.

BFF child `3c27f97` deletes the retired `project-resource.ts` upload dispatcher and its two duplicate compatibility tests. Canonical `project-native.ts` upload/read/delete coverage remains; the post-cleanup full BFF suite is 2315 tests / 2313 passed / 0 failed / 2 skipped.

BFF child `8df63bb` removes `LegacyRoutesModule`, `LegacyRoutesRuntime`, its middleware, and the unused `GracefulShutdown` bridge from the production Nest graph. Feature modules now form the only Nest composition; raw `createBffServer` remains an explicit compatibility/test entrypoint. Nest architecture is 23/23, BFF architecture 34/34, and the full BFF suite is 2315/2313/0/2.

BFF child `2d1103f` removes the remaining `BffApplicationServices` type mirror from `SkillSpecificationService`; the Project dependency is now expressed directly as `Pick<ProjectService, "find">`. Skill specification focused validation remains 110/110.


### C-3 aggregate runtime fallback removal（2026-11-01）

BFF child `62fe701` removes the `BffApplicationServices` aggregate from the `BffBusinessStore` contract and stops production bootstrap/server code from reading `businessStore.services.*`. The live PostgreSQL composition exposes named owner service seams for bootstrap (`chatService`, `chatTurnService`, `projectService`, `scheduledTaskService`); the aggregate view remains only on the concrete repository fixture for existing integration tests and is no longer a runtime application port. Project skill-selection, Project MCP recommendations, Skill share lookup and message regeneration now receive explicit owner/receipt providers rather than a global store locator.

验证：BFF build/typecheck；BFF architecture 34/34；Nest runtime/feature architecture 23/23；Project MCP recommendation HTTP 8/8；`git diff --check` clean. The compatibility aggregate and remaining feature-local Port census are still open C-3 work; A-01/A-02/A-07 remain stopped.


### C-3 compatibility aggregate deletion（2026-11-01）

BFF child `6f9a9e2` deletes `src/application/services.ts` and removes the aggregate class from the PostgreSQL composition. Named `ProjectService`, `ScheduledTaskService`, `ChatApplicationService` and `ChatTurnApplicationService` instances are constructed once and exposed to bootstrap; the concrete repository retains only a typed compatibility view for integration fixtures, with no production consumer. Personal Knowledge, AI Skill import and Message regeneration route contracts no longer accept `BffBusinessStore.services`; affected raw fixtures were migrated to explicit owner providers.

验证：BFF build/typecheck；BFF architecture 34/34；Nest runtime/feature architecture 23/23；focused feedback/regeneration/project-pin/MCP/personal-knowledge/AI-hand-off tests 46/46；project/resource/installation focused tests 66/66. Remaining C-3 work is the compatibility view removal from integration fixtures and the per-port keep/move/delete audit.


### C-3 artifact library port isolation（2026-11-01）

BFF child `5de502c` moves `ArtifactAssociation`, `ArtifactPosition` and `ArtifactLibraryRepository` out of the global `bff-business-store` port into the Account/Library-owned `artifact-library-repository` port. Library routes, AccountModule, Storage artifact projection and PostgreSQL adapter now import the narrow feature port; no behavior, SQL owner or storage transport changed.

验证：BFF build/typecheck；BFF architecture 34/34；Nest runtime/feature architecture 23/23；`git diff --check` clean. The remaining `BffBusinessStore` lifecycle/outbox fields still require feature-owner migration evidence.

### C-3 scheduler receipt port isolation（2026-11-01）

BFF child `039e8d8` removes the Scheduler callback route's type dependency on the aggregate `BffBusinessStore`. `SchedulerDispatchProvider`, settlement and unknown-claim release now consume the feature-owned `SchedulerDispatchReceiptRepository` port directly; the raw/test fixture migration uses the already-named `scheduledTaskService` seam instead of `services.scheduledTasks`. No receipt repository, task service or worker implementation was duplicated.

验证：BFF build/typecheck；Scheduler focused 14/14；`git diff --check` clean. The concrete PostgreSQL compatibility view and remaining lifecycle/outbox/feature ports are still open C-3 work; A-01/A-02/A-07 remain stopped.

### C-3 skill-share provider type isolation（2026-11-01）

BFF child `27523d9` removes the remaining `BffBusinessStore` import from the native Skill Share route. The transitional raw composition fallback now accepts a narrow structural `{ skillShares?: SkillShareRepository }` source, so the route depends on the feature port rather than the aggregate store contract. No repository, service or owner boundary was duplicated.

验证：BFF build/typecheck；BFF architecture 34/34；Nest feature architecture 19/19；Skill Share HTTP 4/4；`git diff --check` clean. The known R357 shared-summary fixture failures remain baseline and are not attributed to this type-only cleanup; the compatibility aggregate and remaining lifecycle/outbox/feature ports remain open C-3 work.

### C-3 AG-UI consumer provider isolation（2026-11-01）

BFF child `11d8199` adds an explicit `agUiConsumers` composition seam. Raw Chat admission now receives the Agui-owned consumer repository through `BffServerComposition`/`ChatBusinessProvider` instead of reading `businessStore.agUiConsumers` in the server dispatcher; PostgreSQL remains the single concrete repository owner and the bootstrap fallback is only the transitional composition boundary.

验证：BFF build/typecheck/lint；BFF + Nest architecture 53/53；Chat/AG-UI focused 12/12；`git diff --check` clean. `BffBusinessStore.agUiConsumers` is still a bootstrap compatibility source for the next deletion slice; the remaining lifecycle/outbox/feature ports stay open C-3 work.

### C-3 AG-UI projection provider isolation（2026-11-01）

BFF child `db3c94a` adds the matching explicit `agUiProjection` composition seam. The raw Agent session path and AG-UI projector construction now use the named projection provider, while `BffBusinessStore.agUi` is read only by bootstrap compatibility wiring. The PostgreSQL projection implementation remains single-owner and no generic abstraction was introduced.

验证：BFF build/typecheck/lint；BFF + Nest architecture 53/53；Chat/AG-UI focused 137/137；`git diff --check` clean. The remaining bootstrap store fields, lifecycle/outbox ports and full C-4 cross-owner journey remain open.

### C-3 Agent reader provider isolation（2026-11-01）

BFF child `4144fee` adds explicit `submittedAgentRuns` and `projectExecutionBindings` composition seams. Raw AgentRuns internal admission and Run display now consume the named reader providers rather than reading those fields from `businessStore` inside the dispatcher; bootstrap remains the only transitional bridge from the concrete PostgreSQL composition.

验证：BFF build/typecheck/lint；BFF + Nest architecture 53/53；Agent display/admission/project-binding focused 144/144；`git diff --check` clean. The compatibility fields remain in the bootstrap source until all raw/test consumers are migrated; C-3 and C-4 are not closed.

### C-3 Scheduler/Artifact provider isolation（2026-11-01）

BFF child `1a1fe92` exposes `schedulerDispatchReceipts`, `scheduledAgentDispatch` and `artifactLibrary` as explicit raw composition providers. Scheduler callback and Library routing no longer read those repositories from `businessStore` in the server dispatcher; the Scheduler/Artifact providers remain single-owner. The Project resource HTTP fixture was migrated from `services.projects` to the named `projectService` seam, closing the focused provider drift without restoring aggregate fallback.

验证：BFF build/typecheck/lint；BFF + Nest architecture 53/53；Project resource upload + Scheduler + architecture focused 80/80；`git diff --check` clean. Remaining worker lifecycle fields and the concrete compatibility aggregate are still open C-3 work.

### C-3 scheduled-task compatibility view removal（2026-11-01）

BFF child `10477a7` removes `scheduledTasks` from the concrete `PostgresBffRepositories.services` fixture-only aggregate. Scheduler integration fixtures now use the named `scheduledTaskService` and the explicit raw `scheduledTaskService` provider, so the production port and test seam share one owner without a duplicate aggregate property.

验证：BFF build/typecheck/lint；BFF + Nest architecture 67/67；Scheduler focused 14/14；`rg` confirms no `services.scheduledTasks` consumer remains. The remaining compatibility view fields (`projects`, `chat`, `chatTurns`) and lifecycle/outbox ports remain open C-3 work; integration execution needs the local PostgreSQL/Redis environment.

### C-3 project compatibility view removal（2026-11-01）

BFF child `c373066` removes `projects` from the concrete `PostgresBffRepositories.services` fixture-only aggregate. Project resource access/delete, BusinessStore deletion observation and Chat project-selection integration fixtures now use the named `projectService`; no `services.projects` consumer remains outside an intentionally independent MCP route fixture. The canonical ProjectService remains the sole owner.

验证：BFF build/typecheck/lint；BFF + Nest architecture 67/67；Project resource access/delete/upload focused tests green; `git diff --check` clean. One Chat integration test remains an environment/baseline failure (no real IAM/DB session in this run); remaining compatibility view fields are `chat`/`chatTurns` only.

### C-3 compatibility aggregate deletion（2026-11-01）

BFF child `e220ae4` removes the remaining `services` compatibility aggregate from `PostgresBffRepositories`. Chat/ChatTurn integration fixtures now use the named `chatService` and `chatTurnService`; no `services.chat`, `services.chatTurns`, `services.projects` or `services.scheduledTasks` consumer remains. The canonical named services and feature-local ports are now the only application service seams; no duplicate implementation or fallback was added.

验证：BFF build/typecheck/lint；BFF + Nest architecture 173/173；Chat/Message/AG-UI focused 173/173；integration files `node --check` clean；`git diff --check` clean. Real PostgreSQL/Redis integration remains environment-gated; C-4 full cross-owner validation and IAM/App native journey are still open, so A-01/A-02/A-07 remain stopped.

### C-3 BffBusinessStore application-port narrowing（2026-11-01）

BFF child `46096d4` narrows `BffBusinessStore` to the durable idempotency and lifecycle contract. Feature repositories, services, AG-UI resources and outbox resources are now represented only by bootstrap-local `BffInfrastructureStore` and explicit `BffServerComposition` providers; the aggregate application port no longer carries feature resource fields. Existing PostgreSQL implementations remain single-owner and raw compatibility behavior is unchanged.

验证：BFF build/typecheck/lint；BFF + Nest architecture 53/53；scheduler/Skill Share/Project resource/Chat focused set 87/87；`git diff --check` clean. This closes the global application-port field census; feature lifecycle worker proof and cross-owner C-4 remain open.


### C-3 bootstrap-only runtime store seam（2026-11-01）

BFF child `95d6516` 删除 `src/application/ports/bff-business-store.ts`。`BffBusinessStore` 不再作为应用层全局 Port 暴露；`BffRuntimeStore` 仅在 `bootstrap/runtime.ts` 内组合 `IdempotencyRepository` 与数据库生命周期，feature resources 继续通过命名的 `BffServerComposition` providers 传递。没有新增 Repository/Service 实现，也没有改变 raw/test compatibility 的行为边界。

验证：BFF `pnpm build`、`pnpm typecheck`、`pnpm lint`；BFF architecture 34/34；`git diff --check` clean。`PostgresBffRepositories` 仍是真实 PostgreSQL composition 与现有 integration fixtures 的 owner；C-3 其余 lifecycle/fixture census 和 C-4 全量跨 owner 验证继续 open。

### C-1.3 App native-session runtime cutover（2026-11-01）

App child `bc1f5c4b` 将首方 `GET /login` 改为白名单 `return_to` 校验后直接 303 到
`/auth/sign-in?native=1&return_to=...`；不再签发 Auth.js handoff CSRF、Product login intent 或隐藏
`/api/auth/signin/kokoro-iam` POST。`auth/sign-in/route.ts` 识别精确 native marker 后只调用
IAM `/sign-in/email`，校验 allowlisted `kokoro-issuer.session_token`，原样转发 native session cookie，
清理 flow/CSRF 并 303 回白名单目标；native 分支不调用 `/iam/oauth2/continue`。App shell `15720322`
改为 native BFF admission only：缺 cookie 进入 `/login`，invalid/unavailable 保持 serverUnavailable，
不再从 Product Session Redis fallback 授予 SSR 准入。旧 OAuth relay 与 Product Session 文件仍保留给后续删除切片，
不得被新的登录入口调用。

验证：App `tests/server/login-route.test.ts`、`tests/server/native-sign-in-route.test.ts`、
`tests/server/proxy-sign-in.test.ts`、`tests/app/sign-in-failure-page.test.tsx`、`tests/ui/app-gate.test.tsx`
共 31 项通过；touched-file ESLint 通过。App 全仓 `pnpm typecheck` 仍被既有
`src/components/blocks/app-frame/app-frame-main-surface.tsx:onReconnect` 类型错误阻断；未将其记为本片引入。
旧 OIDC system fixture 仍引用 legacy `/login` 隐藏表单，需在删除 first-party RP 前继续迁移，故 C-1.3、C-4 与
全量跨 owner journey 尚未关闭，A-01/A-02/A-07 继续停写。

### C-1.3 App native-session runtime cutover continuation（2026-11-01）

App child `d7e7e179` completes the next native-only runtime slice. The catch-all
`/api/auth/[...nextauth]` adapter now exposes only native `GET /session` and
`POST /signout`; it no longer imports Auth.js, OIDC RP transactions, Product
Session storage, refresh, or token revocation. Sign-out is a method-preserving
307 handoff to `/iam/sign-out`, so the API path cannot create or clear a local
Product Session. Native sign-in rejects legacy OAuth query shapes before form
processing and no longer calls `/iam/oauth2/continue`. Product BFF admission
and all migrated account/feature adapters now use the native IAM cookie and
service/origin headers; Bearer fallback and Redis/secret configuration are no
longer runtime requirements.

验证：App native/session/sign-in/product-BFF focused suites 88/88、54/54、
108/108、6/6；account/profile and cross-feature focused bundle 172/172；
touched-file ESLint and `git diff --check` clean. App `pnpm typecheck` remains
blocked only by the pre-existing `app-frame-main-surface.tsx:onReconnect`
error. Old OIDC/Product Session source and tests, native tenant interaction
OAuth query handling, and remaining legacy mocks are still open cleanup work;
C-1.3/C-4 and A-01/A-02/A-07 remain open/stopped.

### C-1.3 browser recovery and tenant boundary cleanup（2026-11-01）

App child `cd4da8b6` removes the browser Product Session refresh surface. The
session probe now performs only bounded native `GET /api/auth/session` reads;
it no longer prefetches Auth.js CSRF, issues a refresh POST, interprets
`refresh_required`, or carries an uncertain Product Session mutation state.
`endProductSession` uses only `POST /iam/sign-out`, and the obsolete client
refresh/CSRF tests were replaced by native-session boundary coverage. App child
`6c566893` removes `oauth_query` from the native IAM organization activation
payload; the signed interaction cookie remains the only interaction binding.

验证：native session/sign-in/browser recovery focused suites 74/74; touched
file ESLint and `git diff --check` clean. App typecheck remains blocked only by
the pre-existing `app-frame-main-surface.tsx:onReconnect` error. Old RP/
Product Session server files and their real-HTTP fixtures still require a
separate deletion/migration slice; C-1.3/C-4 remain open and A-01/A-02/A-07
stay stopped.

### C-1.3 legacy runtime deletion and native fixture migration（2026-11-01）

App child `e277273a` completes the deletion slice for the first-party legacy runtime. Removed the Auth.js/OIDC RP helpers (`oidc-provider`, `oidc-token`, RP transaction/cookie/CSRF/agent) and Product Session identity/cookie/store/return modules, renamed the native browser recovery helper to `login-recovery.ts`, and removed their server and real-HTTP test fixtures. `package.json`/`pnpm-lock.yaml` no longer include `next-auth` or `openid-client`. Native BFF fixtures now assert issuer-cookie forwarding rather than Bearer/Product Session fallback; architecture and contract checks assert the native-only `/api/auth/session`/`signout` adapter and the absence of deleted files. The legacy IAM RP real-HTTP suites were deleted because their hidden Auth.js form/state contract is no longer a runtime contract; native IAM unit/app coverage remains in the current focused suites.

验证：App `tests/app` 617/618 passed (the single public-skill-list provenance hash mismatch is pre-existing); App `tests/server` 279/279；architecture/contract 29/29；native/product-BFF/system focused bundles 26/26、73/73、39/39、18/18；touched-file ESLint and `git diff --check` clean. `pnpm typecheck` remains blocked only by the pre-existing `src/components/blocks/app-frame/app-frame-main-surface.tsx:186` `onReconnect` prop mismatch; Node 24 vs package Node 22 engine warning remains environment-only. C-1.3 still requires the remaining route/docs census and C-4 full cross-owner verification; A-01/A-02/A-07 remain stopped.

### C-4 App native-session UI fixture closure（2026-11-01）

App child `76d2cc34` aligns the remaining UI fixtures with the native-session and ordered-activity contracts. Removed stale Auth.js CSRF/session-POST expectations from the project rail, rewrote Settings logout retirement cases around `POST /iam/sign-out`, updated account-profile fixtures to the strict IAM-owned projection, and migrated process-only/HITL tests from the retired top-level activity compatibility prop to ordered `steps`. Snapshot activity coverage now uses anchored message-parts history; summary assertions use the canonical `Files processed` label.

验证：App `pnpm vitest run tests/ui` **271 files / 3182 tests passed**；focused account/profile/app-frame/settings/process suites 520/520；touched-file ESLint and `git diff --check` clean. This closes the App UI fixture failure set without restoring legacy runtime paths. App `pnpm typecheck` remains blocked only by the pre-existing `app-frame-main-surface.tsx:186` `onReconnect` prop mismatch; C-1.3 route/docs census and C-4 cross-owner verification remain open, so A-01/A-02/A-07 stay stopped.

### C-1.3 first-party OAuth relay deletion and native-session contract closure（2026-11-01）

BFF child `071c49022c31acae56d3be92e6df80fae5cf799a` removes browser-private OAuth/OIDC relay routes from the published policy and transport. The relay now admits only native sign-up/sign-in, verify-email, sign-out, get-session, fixed-tenant activation, and the three invitation owner operations; callback/logout issuer configuration, browser navigation transport, OAuth query bodies, and OAuth-only response branches are deleted. Browser Authorization headers are rejected before IAM I/O, issuer cookies are filtered to the native session set, and the generated policy snapshot hash is `b2adc766332c1ca87b55900f359f5cc931b7f50505a19ea21cbb0c36faf9f72f`.

App child `c21984b9e5e30f4fca1c2777e173fc3928afc182` consumes that exact BFF snapshot, cuts `/iam/[...path]` to native get-session/verify-email/sign-out, deletes OAuth consent routes and logout response projection, removes callback/authorize/end-session proxy branches, updates the sign-out page to native `POST /iam/sign-out`, and rewrites the route/contract/transport fixtures to native semantics. Interaction CSRF and tenant continuation remain only for native sign-in/select-tenant/invitation flows.

验证：BFF `pnpm build`、`pnpm typecheck`、`pnpm lint`；BFF native relay policy/transport tests **12/12**；BFF `git diff --check` clean. App `pnpm vitest run tests/ui` **164 files / 3182 tests passed**；App server suite **17 files / 258 tests passed**；native IAM relay/interaction/proxy focused bundle **74/74**；App focused contract/architecture **30/30**；App `pnpm lint` and `git diff --check` clean. App `pnpm typecheck` remains blocked only by the pre-existing `src/components/blocks/app-frame/app-frame-main-surface.tsx:186` `onReconnect` prop mismatch. The broader App contract directory still has unrelated baseline generated BFF public snapshot/version drift (48 existing failures in the full directory run); it is not attributed to this IAM relay slice. C-1.3 native runtime is closed for the App/BFF relay surface; LegacyRoutes and remaining Repository/Service/Port census plus C-4 cross-owner verification remain open before A-01/A-02/A-07.

### C-3 feature-local capability ports continuation（2026-11-01）

BFF child `045dbf7` moves `PublicShareRepository` from the global `application/ports` directory to the Chat-owned `application/chat` boundary. The service and PostgreSQL adapter now consume that feature port, and a Nest architecture assertion prevents the retired global path from returning. BFF child `03940f9` applies the same treatment to `SkillShareRepository`, moving it to `application/skills` and updating the Skills middleware, native/raw route seams, runtime composition, and PostgreSQL composition without duplicating the repository or changing the share contract.

验证：BFF build/typecheck/lint；BFF architecture + Nest runtime/feature architecture **59/59**；`git diff --check` clean. These are narrow C-3 port-isolation slices; global `IdempotencyRepository`, owner repositories, outbox ports, and raw compatibility composition still require the planned keep/move/delete audit. C-4 full cross-owner verification remains open, and A-01/A-02/A-07 stay stopped.

### C-3 Account/Skills capability port isolation continuation（2026-11-01）

BFF child `758d58f` moves `PersonalKnowledgeRepository` into the Account-owned `application/account` boundary. Child `224a624` completes the matching Account Library move for `ArtifactLibraryRepository`; Account middleware/routes, Storage artifact projection, and PostgreSQL composition now import the feature-local port. Child `03940f9` moves `SkillShareRepository` into the Skills-owned `application/skills` boundary. Each change keeps one concrete PostgreSQL implementation, preserves existing wire/transaction behavior, and adds a negative architecture assertion for the retired global path.

验证：BFF build/typecheck/lint；BFF architecture + Nest runtime/feature architecture **61/61**；`git diff --check` clean. The remaining global ports are reviewed as shared idempotency, owner repositories, or lifecycle/outbox seams and require an explicit keep/move/delete decision; raw compatibility composition and C-4 full owner validation remain open. A-01/A-02/A-07 stay stopped.

### Task A closure and E2E readiness audit（2026-11-01）

当前结论：Task A 尚未闭环，A-01/A-02/A-07 继续停写。

- C-1.3：App/BFF native-session relay 删除与 native fixture closure 已有子仓证据；IAM→BFF→App 的真实 sign-in/session-admission/profile/tenant-switch/sign-out/revocation 旅程仍缺真实 PG/Redis 与服务进程收据，因此不能把跨 owner C-1.3 写成全绿。
- C-2：Nest 生产图已删除 `LegacyRoutesModule/Runtime/Middleware`，但 `createBffComposition`、`handleBffRequest`、`createBffServer` 仍保留在 raw test/compatibility 入口，按设计门尚未满足零生产兼容路径证明。
- C-3：最近已完成四个 feature-local port slices（Chat Public Share、Skills Share、Account Personal Knowledge、Account Library Artifact）；剩余 idempotency、Chat/Project/Scheduled/Agent/worker outbox 等 global ports 需逐项判定 keep/move/delete，不能批量机械搬迁。
- C-4：Root `git diff --check`、拓扑检查与 `python3 -m pytest scripts/tests -q` 通过（1846 passed / 3 skipped）。BFF focused build/typecheck/lint 与 architecture/Nest 61/61 通过；本轮 `pnpm test` 在 `test/contract/skill-specification-http.test.mjs` 运行约 300 秒无终态，按超时中止，部分结果 1038 passed / 21 failed / 113 cancelled，不能作为全量绿证据。App 仍有既有 `onReconnect` typecheck 阻塞与全契约生成快照漂移基线。

E2E 预检：当前本机仅探测到 PostgreSQL `127.0.0.1:5432`、Redis `127.0.0.1:6379`、MinIO recovery `39190/39192`、Mailpit `1025/8025`、ClamAV `43310`；IAM/BFF/App/Agent/System/Billing/Storage/Scheduler/Capability/Admin 均无运行监听。PostgreSQL `postgres` 数据库当前仅有 `kokoro_agent`、`kokoro_platform` 与历史 `kokoro_test_*` schema，缺少本轮 IAM/BFF/System/Billing/Storage/Scheduler 的隔离 owner schema；Redis DB9 仍有既有 key，未执行清理。

端到端启动顺序冻结为：IAM（3101）→ System（4240）/Storage（8085）→ Capability（8086）/Scheduler（8080）/Billing（4245）→ Agent HTTP/worker（4401）→ BFF（4300）→ App（3000）/Admin（3320）。启动前须补齐 owner schema、隔离 Redis logical DB/prefix、Storage S3/ClamAV 与 IAM/BFF/owner credential 配对；完成 `/healthz`/`/readyz` 后，依次验证 native login/session admission、BFF `/v1/me`、profile/tenant/team/sign-out/revocation，再验证 Chat/Agent/Skills/Storage/Billing/Scheduler。当前资源与进程条件不足，未宣称 E2E 通过。

### C-3 Chat repository port isolation continuation（2026-11-02）

BFF child `61834b7` moves the 171-line `ChatRepository` contract and its Chat read/mutation value types from global `application/ports` to `application/chat`. Chat services, HTTP inputs/routes, public-share adapter, PostgreSQL readers, archive/shared-task adapters, and focused fixtures now import the Chat-owned port. No SQL, wire envelope, authorization rule, transaction, or repository implementation changed.

验证：BFF build/typecheck/lint；architecture/Nest/runtime/feature + Chat/archive/shared-task/Skill Share focused tests **208/208**；`git diff --check` clean. The full BFF `pnpm test` remains a separate long-running baseline/environment gate and is not reclassified by this type-boundary slice. Remaining global ports are still subject to the planned owner audit; A-01/A-02/A-07 stay stopped.

补充：Chat port cutover 后由 BFF child `fb36fa5` 修正 Public Share port 的相对导入，Root 以 `acd8c89a` 更新 gitlink；行为与验证范围不变。

### C-3 Projects repository port isolation continuation（2026-11-02）

BFF child `6926525` moves the Project owner repository contract from global `application/ports` to `application/projects`. ProjectService, Skill specification's Project owner scope, project HTTP inputs/routes, PostgreSQL Project adapters/composition, and architecture fixtures now consume the feature-local port. No Project SQL, Storage boundary, receipt semantics, or route behavior changed.

验证：BFF build/typecheck/lint；Projects/Project Resource/MCP recommendation/architecture focused tests **122/122**；`git diff --check` clean. The Project Skill content suite remains environment-gated by its existing Platform dependency fixture and was kept outside this green slice. Remaining global ports and raw compatibility composition remain open C-3 work; A-01/A-02/A-07 stay stopped.

### C-3 AgentRuns reader port isolation continuation（2026-11-02）

BFF child `6d3d7ce` moves `ProjectExecutionBindingReader` and `SubmittedAgentRunReader` into the AgentRuns-owned `application/agent-runs` boundary. Agent admission/display/model-admission routes, AgentRuns module/middleware, PostgreSQL bindings/outbox composition, and runtime wiring now use the feature-local contracts. No Agent protocol, receipt, authorization, or persistence behavior changed.

验证：BFF build/typecheck/lint；AgentRuns/Project binding/model-admission/architecture focused tests **193/193**；`git diff --check` clean. Remaining global ports are shared idempotency or lifecycle/outbox contracts requiring separate ownership proofs; C-2/C-4 and A-01/A-02/A-07 remain open/stopped.

### C-3 Projects release outbox port isolation continuation（2026-11-02）

BFF child `a4e1241` moves `ProjectScopeReleaseOutboxRepository` into the Projects-owned `application/projects` boundary. Project release dispatcher, Storage scope-release client, PostgreSQL adapter/composition, runtime wiring, and ProjectsModule now consume the feature-local port; lifecycle and release semantics are unchanged.

验证：BFF build/typecheck/lint；Project resource + architecture/Nest focused tests **101/101**；`git diff --check` clean. Remaining global ports are scheduled/Agent outbox contracts and shared idempotency, each requiring its own owner proof; C-2/C-4 and A-01/A-02/A-07 remain open/stopped.

### C-3 ScheduledTask port isolation continuation（2026-11-02）

BFF child `4fe8f51` moves `ScheduledTaskRepository`, `ScheduledTaskOutboxRepository`, and `ScheduledTaskOutboxDeliveryPort` into the ScheduledTasks-owned `application/scheduled` boundary. ScheduledTask service/read/mutation code, scheduler state/outbox adapters, PostgreSQL composition, worker module, and test fixtures now use the feature-local contracts. Durable outbox leasing, Scheduler callback behavior, retries, settlement, and shutdown semantics are unchanged.

验证：BFF build/typecheck/lint；ScheduledTask/Scheduler/Agent terminal/architecture focused tests **160/160**；`git diff --check` clean. Remaining global ports are Agent dispatch/cancellation, scheduled Agent dispatch, Scheduler receipt, stable ID generation, and shared idempotency; C-2/C-4 and A-01/A-02/A-07 remain open/stopped.

### C-3 Agent dispatch port isolation continuation（2026-11-02）

BFF child `3af1684` moves Agent dispatch and cancellation delivery/outbox contracts into the AgentDispatch-owned `application/agent-dispatch` boundary. ChatTurn commit, dispatch/cancellation workers, Agent HTTP delivery, PostgreSQL repositories/composition, and fixtures now use the feature-local contracts. No Agent wire, lease, retry, cancellation, or Chat admission behavior changed.

验证：BFF build/typecheck/lint；Agent dispatch/cancellation/ChatTurn/regeneration/architecture focused tests **203/203**；`git diff --check` clean. Remaining global ports are scheduled-Agent delivery/repository, Scheduler callback receipt, stable ID generation, and shared idempotency; C-2/C-4 and A-01/A-02/A-07 remain open/stopped.

### C-3 global port census checkpoint（2026-11-02）

After the feature moves through child `ca4b529`, `src/application/ports` contains only `idempotency-repository.ts`. Its callers span Account, Chat, Projects, ScheduledTasks, Skills, Billing, AgentRuns, Music, Library and raw bootstrap because it is the shared durable receipt/CAS contract; it remains an explicit cross-feature boundary rather than a feature locator. All repository, delivery, reader, and outbox ports with an exclusive owner now live under `application/{account,agent-dispatch,agent-runs,chat,projects,scheduled,skills}`.

验证：the latest scheduled/Agent focused bundle is **132/132** after the move; build/typecheck/lint and architecture gates are green. This closes the source-level port placement census, but C-3 still requires raw compatibility composition/dispatcher deletion proof and C-4 owner/root full-gate evidence before A gates open.

### C-2 raw-only Agent setup route isolation（2026-11-02）

BFF child `0b65b918b96664ec5285998c5e87450b30533879` adds the named `agentConnectionSetupRequest` adapter. `GET /v1/agents/connections/setup` now validates the strict platform/query/body contract, performs the same IAM admission boundary, returns `agent_not_configured` when live Agent is disabled, and uses Agent identity headers plus strict response projection when an Agent upstream is explicitly enabled. The compatibility `routeHandler` remains untouched for the mock fixture; the production raw chain invokes this adapter before `handleBffRequest`, so this legal contract path no longer reaches generic `upstreamKey('agents')` fallback.

验证：BFF `pnpm build`; `node --import tsx --test --test-concurrency=1 test/bff.test.ts test/architecture.test.ts test/nest-runtime-architecture.test.ts test/nest-feature-architecture.test.ts` **95/95**; `pnpm lint`; `git diff --check`。这只是 C-2 route inventory 的一项隔离，不代表 `handleBffRequest`、`createBffComposition`、`PostgresBffRepositories` 已删除；真实 kokoro-agent setup owner endpoint 与跨仓 E2E receipt 仍待补齐。

### C-2 raw compatibility Chat mutation/event cutover（2026-11-02）

BFF child `bb1fa5e8a7fd4959a113afd0cbcf8d013d1b7ff` extends the raw `createBffServer` compatibility chain to invoke the same feature adapters already owned by `ChatModule`: message regeneration, title/delete/share mutations, AG-UI events, and message submission. The chain is gated off for the mock `routeHandler` seam and when the required named feature providers are absent; it does not duplicate Chat/Agent/AG-UI services or change the wire contract. This removes those legal Chat paths from the raw `handleBffRequest` session branch for live compatibility compositions while preserving the existing mock fixture path.

验证：BFF build；focused BFF/Chat/regen/Nest suite **65/65**；lint and `git diff --check` passed. Full BFF test and raw integration fixture census remain open; this is not the deletion of `handleBffRequest` or `PostgresBffRepositories`.

### Root verification after BFF child pin `bb1fa5e` (2026-11-02)

Root `git diff --check`, `python3 scripts/verify-repository-topology.py`, and `python3 -m pytest scripts/tests -q` passed after pinning BFF `bb1fa5e8a7fd4959a113afd0cbcf8d013d1b7ff` (**1846 passed / 3 skipped / 502 subtests**). This is Root governance/topology evidence only; it does not replace the pending BFF full owner gate or E2E service receipts.

### C-2 raw compatibility Agent control cutover（2026-11-02）

BFF child `393b9d5bd67f07e8b4c87b81f6c594f848621fee` adds the existing `handleAgentControlRequest` feature adapter to the raw `createBffServer` chain. `POST /v1/sessions/:session_id/runs/:run_id/control` now uses the same AgentRuns-owned admission, Chat/Project recheck, durable idempotency receipt and strict Agent control receipt path as Nest `AgentRunsMiddleware`; the mock `routeHandler` seam and provider-null fallback remain explicit compatibility guards. The old `handleBffRequest` session branch is no longer the first live compatibility owner for this route.

验证：BFF `pnpm build`; raw compatibility + Agent control + Nest runtime/feature architecture tests **68/68**; `pnpm lint`; `git diff --check`。`liveAgentSession` remains as the bounded compatibility implementation used by the named adapter; it is not deleted until the remaining session/run route census and provider import census prove zero consumers.

### C-1.3 native-session runtime audit（2026-11-02）

App read-only audit confirms first-party runtime is native-session only: old OIDC/Auth.js/ProductSession runtime and dependencies were removed in App child history; `/api/auth/[...nextauth]` is a native `/session`/`/signout` compatibility adapter without RP fallback. IAM OAuth protocol relay and public Skill bearer remain separate owner protocols and are intentionally retained. Five active `.env*.example` files still contain stale legacy variable comments and historical docs retain old terminology; these are documentation/configuration cleanup items, not runtime fallback evidence.

C-1.3 remains open because the real IAM→BFF→App PG/Redis receipt is missing for login, active-tenant switch, sign-out and revocation. No A-01/A-02/A-07 work is opened.

### Root verification after BFF Agent control pin `393b9d5` (2026-11-02)

Root `git diff --check`, `python3 scripts/verify-repository-topology.py`, and `python3 -m pytest scripts/tests -q` passed after pinning BFF `393b9d5bd67f07e8b4c87b81f6c594f848621fee` (**1846 passed / 3 skipped / 502 subtests**). Topology reports the new BFF child SHA; this remains governance evidence only and does not close BFF full owner gates, real C-1.3 receipts, or E2E service readiness.

### C-1.3 App native-session static configuration cleanup（2026-11-02）

App child `b0919ffc20fe4ba3b281a8150aee503e1744a274` removes stale `NEXTAUTH_*`, `KOKORO_OIDC_*`, and `KOKORO_WEB_AUTH_SECRET` comments from the five active `.env*.example` templates and replaces them with native-session deployment guidance. Historical docs and test fixture stubs remain unchanged; source runtime has no reads of those legacy variables.

验证：App `pnpm test:architecture` **50/50**, `pnpm lint`, `git diff --check` passed. This removes deployment ambiguity but does not create the missing real IAM→BFF→App login, tenant-switch, sign-out or revocation receipts.

### C-4 format gate stale-path cleanup（2026-11-02）

BFF child `062f93ff6ed249c45843bfec360fc9267104e1b9` removes deleted LegacyRoutes/global-port/service paths from the explicit `format:check` file list; no deleted compatibility file is restored. After the cleanup, `pnpm format:check` no longer reports missing files and still exits 1 only for the pre-existing 30-file Prettier warning baseline (including `server.ts`, feature middleware and architecture tests). This is a gate-cleanup slice, not a format-green claim.

### C-3/C-4 global composition census checkpoint（2026-11-02）

The BFF source census confirms `src/application/ports` now contains only the shared `idempotency-repository.ts`; `BffBusinessStore`/`BffApplicationServices` files and production imports are already zero. `PostgresBffRepositories` remains in raw compatibility runtime and is directly constructed by multiple PostgreSQL integration suites, so it cannot yet be deleted. Remaining raw fallback surfaces are internal Scheduler callback, browser-private MCP/custom API, residual sessions/run, retired-owner termination and generic configured-upstream proxy. Nest `AppModule` is the only production composition root; raw `createBffServer` remains an explicit fixture/compatibility entrypoint until those consumers are migrated or frozen.

### Root verification after App/BFF C-1.3/C-4 pins `b0919ff` / `062f93f` (2026-11-02)

Root `git diff --check`, `python3 scripts/verify-repository-topology.py`, and `python3 -m pytest scripts/tests -q` passed after pinning App `b0919ffc20fe4ba3b281a8150aee503e1744a274` and BFF `062f93ff6ed249c45843bfec360fc9267104e1b9` (**1846 passed / 3 skipped / 502 subtests**). The topology gate is green; BFF format warnings, owner full gates, real native-session receipts and E2E startup remain open.

### C-2 raw compatibility browser MCP/custom API cutover（2026-11-02）

BFF child `562817cb70b7eb09f162929b4f665a5b85b5bc04` extracts shared raw/Nest feature entrypoints for Personal MCP and Custom API. Raw `createBffServer` now invokes the same admitted `mcpPersonalRoute`/`customApiRoute` path before `handleBffRequest`, preserving request-id/cache headers, native admission, owner client identity and strict error projection; Nest middleware delegates to the same entrypoints. The mock `routeHandler` seam remains disabled for compatibility fixtures.

验证：BFF build; Custom API, Personal MCP command/server/authorization, MCP icon, Nest runtime/feature architecture **127/127**; lint and diff-check passed. This removes browser-private MCP/custom API from the generic raw business fallback, but does not delete raw compatibility composition or the remaining scheduler/session/retired-owner/upstream fallback categories.

### Root verification after browser MCP BFF pin `562817c` (2026-11-02)

Root `git diff --check`, `python3 scripts/verify-repository-topology.py`, and `python3 -m pytest scripts/tests -q` passed after pinning BFF `562817cb70b7eb09f162929b4f665a5b85b5bc04` (**1846 passed / 3 skipped / 502 subtests**). The new raw MCP/custom API cutover is topology/governance-green; owner full gates, real native-session receipts, E2E services and remaining raw fallback deletion are still open.

### C-2 residual session/run fallback closure（2026-11-02）

BFF child `e8e7207a3d7d1bbbc9a4f35bb502138754f0e2d6` adds a live-composition guard after all named session/run adapters: unknown `/v1/sessions/**` suffixes now terminate with the canonical 404 envelope instead of falling through to `liveChatBusiness`/`liveAgentSession`; provider-null and mock `routeHandler` compatibility seams remain unchanged. `liveAgentSession` itself remains because the named Chat events and Agent control adapters still use it.

验证：BFF build; Agent control, Chat business/events/message/mutation and Nest architecture **74/74**; lint and diff-check passed. The remaining raw fallback is now limited to non-session owner categories and explicit compatibility providers.

### Root verification after session fallback pin `e8e7207` (2026-11-02)

Root `git diff --check`, `python3 scripts/verify-repository-topology.py`, and `python3 -m pytest scripts/tests -q` passed after pinning BFF `e8e7207a3d7d1bbbc9a4f35bb502138754f0e2d6` (**1846 passed / 3 skipped / 502 subtests**). Unknown live session termination is now covered by the raw focused gate; BFF owner full tests, real native-session receipts, E2E startup and non-session raw composition removal remain open.

### C-2 raw Scheduler callback cutover（2026-11-02）

BFF child `07584d25cd531cef472ec668ee1cab688ff1800b` moves the raw compatibility callback `POST /internal/bff/scheduled-tasks/dispatch` out of `handleBffRequest` into the same feature-owned `schedulerDispatch` entrypoint used by `SchedulerDispatchMiddleware`. The raw chain now builds one narrow `SchedulerDispatchProvider` and invokes it before generic routing; provider-null, `routeHandler` and request-id semantics remain explicit. No second Scheduler service/repository or generic upstream path was introduced.

验证：主方在 child checkout 重新运行 `pnpm build`、`pnpm typecheck`、`pnpm lint`、`git diff --check`；`test/bff.test.ts` **28/28**；architecture/Nest runtime/feature suite **69/69**；scheduler identity/outbox/receiver bundle **28/28**。`pnpm format:check` remains blocked only by the tracked pre-existing warning baseline; BFF full `pnpm test` diagnostic仍有既有 fixture failures/timeouts，不作为 C-4 通过。

### C-2 retired-owner raw termination cutover（2026-11-02）

BFF child `1f5e2cd50707c7d3e622e3428cc2dff2c66ca170` inserts `handleRetiredOwnerRawRequest` after the named feature adapters and removes the retired System/Skills business branch from `handleBffRequest`. Unknown `/v1/system/**` and `/v1/skills/**` requests now use the dedicated IAM-admitted retired-owner adapter and return the existing 503 contracts without generic upstream proxy or receipt claims. Raw compatibility preserves the historical 404 shapes for retired Skill root/by-id/download and enable/disable paths; mock `routeHandler` compositions remain on their fixture handler. Nest `SystemModule`/`SkillsModule` broad retired-owner behavior is unchanged.

验证：主方已在 child checkout 复核 `pnpm build`、`pnpm typecheck`、`pnpm lint`、`git diff --check`；`test/bff.test.ts` **28/28**；architecture/Nest runtime/feature suite **69/69**。C-2 raw fallback census is reduced to generic configured-upstream compatibility plus raw/test fixture/provider consumers; `createBffComposition`, `handleBffRequest` and `PostgresBffRepositories` remain intentionally retained pending zero-consumer proof and C-4 owner gates。

### Root verification after Scheduler/retired-owner BFF pin `1f5e2cd`（2026-11-02）

Root `git diff --check`, `python3 scripts/verify-repository-topology.py`, and `python3 -m pytest scripts/tests -q` passed after pinning BFF `1f5e2cd50707c7d3e622e3428cc2dff2c66ca170`; governance result: **1846 passed / 3 skipped / 502 subtests**. This closes the root topology/governance recheck for the two raw cutovers only. BFF `pnpm format:check`, full owner test baseline, real C-1.3 IAM→BFF→App receipts, E2E service startup, and raw composition zero-consumer proof remain open; A-01/A-02/A-07 stay stopped.

### C-4 BFF full-owner diagnostic after raw cutovers（2026-11-02）

在 child `1f5e2cd` 停写后串行运行 `pnpm test`。构建完成，测试在 `test/contract/skill-specification-http.test.mjs` 长时间 pending 后手动终止；汇总为 **1177 tests / 1043 pass / 21 fail / 113 cancelled / 0 skip**，失败首先集中在既有 archived-tasks 503 fixture 基线及 shared-revision/owner fixture，后续取消项是 pending 阻塞的连锁结果。该诊断不作为 C-4 通过，也未删断言或放宽超时；需要独立 owner 修复/环境资源后再重跑完整 BFF gate。

### C-3 raw PostgreSQL fixture census（2026-11-02）

只读 census 确认 `PostgresBffRepositories` 的生产引用仅在 `src/bootstrap/runtime.ts` 的 raw compatibility composition（import/constructor）；实现仍是唯一集中 PostgreSQL aggregate。9 个 integration suites 直接 import wrapper，共 **102 次** `new PostgresBffRepositories`；另有 17 处对 raw `database` pool/notify 的直接 fixture 访问，10 处 stale `store.services.*` 访问（PersonalKnowledge/PublicShare）。因此不能只删除 wrapper 或改名：先提供 test-only owner fixture factory/显式 named providers，迁移 fresh PostgreSQL/Redis 条件套件，再证明零 import 后删除 runtime aggregate。当前环境未提供 `KOKORO_TEST_POSTGRES_URL`/`KOKORO_TEST_REDIS_URL`，不执行破坏性 schema 操作，不宣称 C-3/C-4 已闭环。

### C-2 generic configured-owner fallback termination（2026-11-02）

BFF child `6f9cc641d59d10b7778985aefb61d8e7cbe54f42` adds a raw-chain negative guard for unknown `/v1/agents/**` and `/v1/billing/**` paths after the named Agent setup/Billing adapters. Unknown paths now return canonical 404 without calling configured upstreams; exact Agent setup and Billing personal routes remain on their named adapters, and mock `routeHandler` fixtures are unchanged. `handleBffRequest` remains as an explicit compatibility path for the remaining raw/test census rather than being deleted prematurely.

验证：主方复核 BFF build/typecheck/lint/diff-check；BFF mock contract **29/29**；architecture/Nest runtime/feature suite **70/70**。This closes the known public Agent/Billing generic fallback categories; raw fixture/provider migration and the remaining configured-upstream compatibility surface are still open.

### Root verification after configured-owner fallback BFF pin `6f9cc64`（2026-11-02）

Root `git diff --check`, `python3 scripts/verify-repository-topology.py`, and `python3 -m pytest scripts/tests -q` passed after pinning BFF `6f9cc641d59d10b7778985aefb61d8e7cbe54f42`; governance result: **1846 passed / 3 skipped / 502 subtests**. This verifies the raw Agent/Billing negative guard at Root level only; C-4 full owner gates, fixture migration, real C-1.3 receipts, E2E startup, and A gates remain open.

### Cross-owner E2E readiness snapshot（2026-11-02）

本地进程/端口核验显示当前只有受管 PostgreSQL `127.0.0.1:5432` 与 Redis `127.0.0.1:6379` 在监听；未发现 IAM、BFF、App、Agent、System、Billing、Storage、Scheduler、Capability 或 Admin 应用进程。Docker 仅有既存 MinIO/Mailpit/ClamAV 依赖容器，未启动业务 owner 容器；`IAM_TEST_ADMIN_URL`、`KOKORO_TEST_POSTGRES_URL`、`KOKORO_TEST_REDIS_URL` 未设置。故当前不能形成端到端登录/租户切换/登出/撤权 receipt，也不把 focused/raw HTTP fixture 视作 E2E。启动顺序与缺口待 readiness audit 收敛后再执行；不重启或改写他人/受管资源。

### E2E readiness audit detail（2026-11-02）

只读 audit 给出最小启动顺序：隔离 PG schemas/Redis namespaces → IAM → System/Capability/Storage/Billing/Scheduler → BFF → Agent HTTP/worker → App → Admin。各仓健康入口分别为 IAM/BFF/Agent/App 及 owner `/healthz`/`/readyz`；Agent HTTP 默认 4401、BFF 4300、App 3000、System 4240、Admin 内部 3320，Scheduler 默认 8080。当前缺少 IAM test admin URL、隔离 owner URL/schema/namespace、service credential 文件与运行时 secret，且应用进程/业务容器均未启动；本轮只记录缺口，不执行服务启动、凭据生成或 schema reset。

### C-4 format gate recheck after `6f9cc64`（2026-11-02）

`pnpm format:check` reaches the complete declared file list without missing-path errors and exits 1 on **31** existing Prettier warnings, including the touched raw server/scheduler/architecture files. No formatting-only sweep was applied because it would widen the cleanup slice; format remains an explicit C-4 blocker rather than being reported green.

### C-1.3 App typecheck baseline cleanup（2026-11-02）

App child `f5d122bb41beb3e141015b758411dbcc0afc583b` removes the stale `onReconnect` prop from `AppFrameMainSurface` and its parent call. `AppFrameConnectionStatus` already owns a data-only status surface, so this is a type-boundary cleanup with no connection UI/behavior change.

验证：App `pnpm typecheck`, `pnpm lint`, `pnpm test:architecture` **50/50**, `git diff --check` passed (Node engine warning only). This closes the known App typecheck baseline; C-1.3 real IAM→BFF→App login/tenant-switch/sign-out/revocation receipts and E2E startup remain open.

### Root verification after App typecheck cleanup pin `f5d122bb`（2026-11-02）

Root topology verification and `python3 -m pytest scripts/tests -q` passed after pinning App `f5d122bb41beb3e141015b758411dbcc0afc583b`; result **1846 passed / 3 skipped / 502 subtests**. The App static typecheck baseline is now closed; native-session real receipts, E2E service readiness, BFF format/full-owner gate and raw fixture zero-consumer proof remain open.

### IAM owner static gate recheck（2026-11-02）

IAM child `e1f537b02cb326cfb3751316b1591fa82313f70a` was rechecked without changing source. `pnpm verify` stops at one existing Prettier warning (`test/integration/bff-session-admission-host.test.ts`); the remaining serial gates passed: lint, typecheck, contract/check-breaking, SDK check, **120 files / 1561 tests**, and build. This is static owner evidence only; `IAM_TEST_ADMIN_URL`/isolated integration resources are still absent, so native-session cross-owner receipts remain open.

### C-3 named PersonalKnowledge fixture seam（2026-11-02）

BFF child `24e157bb023b5132c59fdd153af1c608134c0ee2` updates seven stale integration-fixture accesses from removed `store.services.personalKnowledge` to the existing `PostgresBffRepositories.personalKnowledge` named seam. No production code, SQL, wrapper shape, or behavior changed.

验证：BFF build/typecheck/lint/diff-check；personal-knowledge contract/input/HTTP/integration bundle **6 pass / 6 resource-gated skip**. `KOKORO_TEST_POSTGRES_URL`/`KOKORO_TEST_REDIS_URL` remain unset, so the SQL lock/CAS cases were not claimed as green.

### App full-test diagnostic after typecheck cleanup（2026-11-02）

App `pnpm test` remains non-green on the existing contract-artifact digest baseline: multiple BFF owner/public contract suites report pinned-byte/hash drift (first failure `scripts/generate-bff-project-resource.mjs`, expected vs actual owner digest), followed by related contract failures. The App child worktree stayed clean; no generated artifact or contract was rewritten to silence the mismatch. Architecture/lint/typecheck remain the valid static evidence for `f5d122bb`; full App C-4 validation remains open.

### Root verification after PersonalKnowledge fixture pin `24e157b`（2026-11-02）

Root topology and governance recheck passed after pinning BFF `24e157bb023b5132c59fdd153af1c608134c0ee2`: **1846 passed / 3 skipped / 502 subtests**. The named fixture cleanup is now part of the verified Root combination; remaining C-3 integration wrappers, App artifact baseline, real native-session receipts and E2E readiness remain open.

### C-3 named PublicShare fixture seams（2026-11-02）

BFF child `4af24bf` updates four stale integration-fixture accesses from removed `store.services.publicShares` to the existing named `store.publicShareService` seam in Message-parts and AG-UI projection suites. No production code, wrapper, SQL, or public-share behavior changed.

验证：BFF build/typecheck/lint/diff-check；Message-parts/AG-UI integration bundle **63 resource-gated skips / 0 failures** (test PG/Redis URLs absent); mock contract **29/29**；architecture/Nest **70/70**.

### Root verification after PublicShare fixture pin `4af24bf`（2026-11-02）

Root topology and governance recheck passed after pinning BFF `4af24bf72a5dc70a4a072025b726496ee1673762`: **1846 passed / 3 skipped / 502 subtests**. PublicShare fixture cleanup is integrated without changing production ownership; remaining raw database/worker fixture migration, App artifact reconciliation, C-1.3 receipts and E2E startup remain open.

### C-3 production PostgreSQL owner-resource factory（2026-11-02）

BFF child `673306e5e6c889c8bfbfde02933de1253b4f3034` extracts the PostgreSQL owner graph into `createPostgresBffOwnerResources`/`PostgresBffOwnerResources`. Production `createBffComposition` now consumes the named resource factory and no longer constructs `PostgresBffRepositories`; the class remains only as an explicit raw/integration compatibility wrapper. Construction order, SQL/transaction/worker/readiness/close behavior are unchanged, and no application layer receives the database handle.

验证：主方复核 BFF build/typecheck/lint/diff-check；mock contract **29/29**；architecture/Nest runtime/feature **70/70**。`pnpm format:check` remains exit 1 on the existing 31-file warning set; no unrelated formatting sweep was applied. Integration wrapper consumers remain and still require fixture migration before deleting the compatibility class.

### Root verification after production owner-resource factory pin `673306e`（2026-11-02）

Root topology and governance recheck passed after pinning BFF `673306e5e6c889c8bfbfde02933de1253b4f3034`: **1846 passed / 3 skipped / 502 subtests**. Production no longer constructs the global repository aggregate; raw/integration compatibility consumers remain the next deletion gate.

### C-3 PostgreSQL integration fixture migration（2026-11-02）

BFF child `c6c2aa6e88e2b6fdb53517b38bc527118f537e0d` migrates the nine remaining PostgreSQL integration suites (`agui-http`, `agui-projection`, `archived-tasks`, `business-store`, `chat-facts`, `message-parts-read`, `personal-knowledge`, `scheduled-agent-dispatch`, `scheduler-dispatch-receipt`) from `new PostgresBffRepositories(...)` to `createPostgresBffOwnerResources(...)`. The migration is mechanical: SQL, cleanup, worker wiring, receipt behavior, and direct fixture fields are unchanged. Test census now has zero `PostgresBffRepositories` imports/constructors; only the architecture oracle's negative runtime assertion retains the class name. No alias or second aggregate was added.

主方在 child 停写后复核：`pnpm build`、`pnpm typecheck`、`pnpm lint`、`git diff --check`、BFF mock contract **29/29**、architecture/Nest **70/70** 通过。九个 integration suite 共 **230** 项：**6 pass / 223 resource-gated skip / 1 fail**；唯一失败为 `chat-facts` standalone 的既有 `401 !== 404`，在迁移前 HEAD 基线复跑同样失败，不能计为本轮回归。由于 `KOKORO_TEST_POSTGRES_URL`/`KOKORO_TEST_REDIS_URL` 未设置，不能把 skip 视为真实 owner integration 通过。

下一删除门：在主方复核 17 处 raw `database.pool/notify` fixture 访问及 `createBffComposition`/`handleBffRequest` provider census 后，若确认无运行时消费者，再删除 `PostgresBffRepositories` compatibility class；随后串行重跑 BFF full owner gate、Root topology/governance，并保持 C-1.3 真实 IAM→BFF→App receipts、E2E service startup 与 A-01/A-02/A-07 停写。

### C-3 PostgreSQL aggregate deletion（2026-11-02）

BFF child `8150106dc11676817daca57c6ecbf956fdf283d3` deletes the now-unreferenced `PostgresBffRepositories` compatibility class (84 lines). `createPostgresBffOwnerResources` remains the sole PostgreSQL owner graph and still exposes the explicit `database`/receipt seams required by resource-gated integration fixtures; no production application layer receives the database handle. The architecture oracle now asserts the old class is absent, preventing a compatibility alias from returning.

主方在 child 停写后复核：BFF build、typecheck、lint、diff-check、mock contract **29/29**、architecture/Nest **70/70** 通过。`PostgresBffRepositories` 在 src/test 已无 import/new，仅 historical design text 与负断言保留；17 个 raw `database.pool/notify` fixture accesses are named-factory seams, not wrapper consumers, and remain unchanged.

### Root verification after PostgreSQL aggregate deletion pin `8150106`（2026-11-02）

Root `python3 scripts/verify-repository-topology.py` passed and `python3 -m pytest scripts/tests -q` returned **1846 passed / 3 skipped / 502 subtests**; `git diff --check` passed. This closes the C-3 wrapper deletion gate only. `createBffComposition`/`handleBffRequest` raw compatibility, BFF full-owner failures/format warnings, real IAM→BFF→App receipts, E2E service startup and A-01/A-02/A-07 remain open.

### C-2 unknown model suffix termination（2026-11-02）

BFF child `88538a88f3849e8aaeb2777d755f9b4616885ab4` extends the raw negative guard to non-canonical `/v1/models/**` requests. Only canonical `GET /v1/models` reaches the System model-catalog adapter; unknown model suffixes now return the canonical 404 envelope without calling a configured `model` upstream. The change leaves the owner projection, query mapping, and `routeHandler` fixture seam unchanged.

验证：BFF build/typecheck/lint/diff-check、mock contract **29/29**、architecture/Nest **70/70**；Root topology PASS，治理 **1846 passed / 3 skipped / 502 subtests**。

### C-2 unknown Library suffix termination（2026-11-02）

BFF child `dfe1584eceb8151edfd6ac5871810142108eeb1c` extends the raw configured-owner guard to non-canonical `/v1/library/**` requests. Canonical Library list/artifact/content/file routes continue through the named Library adapter; unknown suffixes now return 404 without calling a configured Storage upstream. The routeHandler fixture seam and canonical response/error shapes remain unchanged.

验证：BFF build/typecheck/lint/diff-check、mock contract **29/29**、architecture/Nest **70/70**；Root topology PASS，治理 **1846 passed / 3 skipped / 502 subtests**。

### C-4 BFF full-gate recheck after aggregate deletion（2026-11-02）

主方在 child `8150106` 停写后重新运行 `pnpm test`。构建完成；测试在 `test/contract/skill-specification-http.test.mjs` 的长 pending 后按现有安全边界中止，汇总为 **1178 tests / 1044 pass / 21 fail / 113 cancelled / 0 skip**。新增计数仅来自本次串行复跑；失败仍集中在既有 archived-tasks 503 fixture 与 Skill shared-revision/owner fixture，pending 造成后续取消。未删除断言、未放宽 timeout，不将此结果计为 C-4 通过。

### C-2 generic configured-owner proxy tail deletion（2026-11-02）

只读 raw-route census 确认 `handleBffRequest` 中 `upstreamKey`/`proxyUpstream` generic tail 在当前生产链无已知可达入口：Agent、Billing、Model、Library、Session、System/Skills、Mori 均已由具名 adapter 或 negative guard 先行处理。BFF child `a86ecae3f2def6f32b03485d3a88e5d0bc1ef097` 删除 `upstream_not_configured`/`upstream_unreachable` generic proxy 分支，保留 BFF-owned 业务、幂等票据及 named adapter；未处理路径统一通过 `reply(..., 404, ..., mutation)` 结算，避免遗留 pending receipt。`configuredUpstream` 仍保留在 health/readiness owner 配置检查。

同一 child 将 `archived-tasks-http.test.mjs` 与 `shared-tasks-http.test.mjs` 的旧 `businessStore.services.chat` fixture 迁移到显式 `chatService`，不再以 aggregate shape 冒充 Chat owner。验证：BFF `pnpm build`、`pnpm typecheck`、`pnpm lint`、`test:architecture` 34/34、`test:nest-architecture` 36/36、mock BFF 29/29、Archived Tasks HTTP/contract bundle 42/42、Shared Tasks HTTP 14/14、Mori bundle 12/12、`git diff --check` 均通过。`pnpm format:check` 仍是既有 31 warnings 基线，不作格式扫尾。

### Root verification after BFF generic-tail/fixture pin `a86ecae`（2026-11-02）

Root 将 BFF gitlink 更新至 `a86ecae3f2def6f32b03485d3a88e5d0bc1ef097` 后重跑 `git diff --check` 与 `python3 scripts/verify-repository-topology.py`（PASS）；Root 治理套件保持 **1846 passed / 3 skipped / 502 subtests**。该切片不关闭 C-1.3 真实 IAM receipt、BFF/App/IAM owner full gate、隔离 PG/Redis integration 或跨仓 E2E，A-01/A-02/A-07 继续停写。

### C-3 explicit SkillShare fixture seam（2026-11-02）

BFF child `13319aa34628bb7b7dd4667ed615f6377078f84b` migrates the three shared-summary fixture groups in `test/contract/skill-specification-http.test.mjs` from `businessStore.services.skillShares` to the top-level `skillShareRepository` provider. The production route already consumes this named provider; no alias, aggregate, SQL, or contract change was added.

验证：focused shared-revision/shared-summary cases **13/13**；full Skill specification contract suite excluding the known long-running disconnect case **110/110**；BFF build/typecheck/lint/diff-check passed. The disconnect cancellation case remains separately pending and is not hidden; full BFF `pnpm test` must be rerun after that pending baseline is resolved.

### Root verification after SkillShare fixture pin `13319aa`（2026-11-02）

Root BFF gitlink now points to `13319aa34628bb7b7dd4667ed615f6377078f84b`. The fixture slice is owner-boundary green at child level; Root topology/governance recheck is required before treating the pin as integrated. C-1.3 real receipts, isolated PG/Redis integration, BFF/App/IAM full gates, and E2E service startup remain open.

### C-3 submitted AgentRuns provider fixture seam（2026-11-02）

BFF child `b8bf18aaf0de9edb8359d0d7320a856b52e63d51` migrates model admission, recovery, and settlement HTTP fixtures from `businessStore.submittedAgentRuns` plus an empty `services` shell to the explicit top-level `submittedAgentRuns` provider with `businessStore: null`. The internal AgentRuns adapter already consumes this named provider; no production or Billing contract change was made.

验证：`test/model-admission-http.test.mjs`, `test/model-admission-recovery-http.test.mjs`, and `test/model-settlement-http.test.mjs` **24/24** pass; `git diff --check` passed. This closes three raw provider-shape consumers without claiming real Billing/Agent owner receipts.

### C-3 PublicShare fixture seam（2026-11-02）

BFF child `64d5c3ea7dae963476553b401af2309d8f06ea4f` migrates both User-admission Share fixtures from `businessStore.services.publicShares` to the explicit top-level `publicShareService`, with `businessStore: null`. The Chat public-share adapter already owns this provider; the migration removes a stale aggregate shape and the unused private snapshot fallback.

验证：`test/user-admission.test.ts` **24/24** pass; `git diff --check` passed. No production code, schema, public contract, or cross-owner receipt was changed.

### C-3 empty Skill-import fixture shell cleanup（2026-11-02）

BFF child `dcfd0aee6d2ef0b151be84a9a23d71d3d50b0c41` removes two empty `services: {}` placeholders from Skill GitHub import fixtures. The receipt methods remain explicit on the test-only business-store seam; no feature provider, alias, or production code was added.

验证：`test/skill-github-import.test.mjs` **52/52** pass; `git diff --check` passed. This is a narrow fixture cleanup and does not substitute for real Platform/Storage owner integration.

### C-3 Project Skill content fixture owner binding（2026-11-02）

BFF child `0a22f4d24972fa82b1310b97c841d82b6572424b` removes the stale `services.projects`/`services.skillShares` fixture shape from `test/project-skill-content-http.test.mjs`. The fixture now injects explicit `projectService` and `skillShareRepository`, while retaining a minimal in-memory receipt repository because the exact project-download source requires a non-null idempotency owner resource. This is a test-only owner-boundary correction; no production alias or duplicate aggregate was added.

验证：Project Skill content HTTP suite **18/18** pass, including package inspection, exact download, membership/pin rechecks, digest mismatch, cancellation and expiry; `git diff --check` passed.

### Technical plan freeze and C-4 recheck（2026-11-01）

Root 冻结技术方案 `docs/superpowers/plans/2026-11-01-task-a-c1-c4-technical-plan.md`，同步记录当前问题清单、Goal/TODO、owner 边界、执行顺序、验证与回滚约束。Goal 保持 ACTIVE；A-01/A-02/A-07 继续停写。

在 BFF `0a22f4d` 完成 Project Skill content fixture owner binding 后，主方重新执行 `pnpm test`：**2298 tests / 2294 pass / 2 fail / 0 cancelled / 2 skipped**。剩余两项固定为 MCP denied-icon owner call 与 Skill installation Chat invalid-owner error mapping；无 pending cancellation。该结果仍不是 C-4 通过，需先修复两项并重跑 BFF/App/IAM/Root 全量门。

本轮确认的外部缺口未变化：真实 IAM/BFF/App/owner 进程未启动，`IAM_TEST_ADMIN_URL`、隔离 PG/Redis URL 与 service credentials 缺失；不启动未配置服务、不重置共享资源、不伪造 native-session receipt。

### C-4 BFF 两个行为失败闭环（2026-11-01）

BFF child `228e3d691f6b5c93575950babb3d9f4c6b409c0a` 完成两项最小修复：

1. `mcp-personal` mutation 在 owner dispatch 前先执行 `manage` action admission；denied icon mutation 不再调用 Platform。
2. `skill-installation-http` 的 Project installation Chat invalid-owner 场景补齐完整最小 receipt repository seam（`claimReceipt`/`putReceipt`/`releaseReceipt` 等），保持 typed owner error 映射为 `502/skill_installation_response_invalid`，不改通用 catch 或契约断言。

主方在 child 停写后复核：MCP focused **42/42**、Skill installation focused **24/24**；BFF `pnpm build`、`pnpm typecheck`、`pnpm lint`、`git diff --check` 均通过。随后 full `pnpm test` 完成：**2298 tests / 2296 pass / 0 fail / 0 cancelled / 2 skipped**（约 199 秒）。该 child 尚未由 Root pin；Root topology/governance、BFF format warnings、App/IAM full gate 与 C-1.3 真实 E2E 仍保持未闭环。

### Root pin and governance recheck after BFF `228e3d6`（2026-11-01）

Root pinned `apps/kokoro-bff` to `228e3d691f6b5c93575950babb3d9f4c6b409c0a` in commit `d37dc378`. 主方重新执行 `git diff --check`、`python3 scripts/verify-repository-topology.py` 与 `python3 -m pytest scripts/tests -q`：topology **PASS**；治理 **1846 passed / 3 skipped / 502 subtests passed**。BFF full behavior gate 现为 0 fail；C-1.3 真实隔离资源、App digest、IAM verify warning、BFF format warning 与跨仓 E2E 仍是后续 TODO。

### App/IAM follow-up gate evidence（2026-11-01）

App `f5d122bb` static recheck passed: `pnpm typecheck`, `pnpm lint`, and `pnpm test:architecture` (**50/50**). Full `pnpm test` remains red with **6316 pass / 50 fail / 353 files**; the failures share pinned BFF public artifact/version drift (for example expected `ea003110...` vs current `35a86f91...`, plus Activity details version drift), so no digest/baseline was changed.

IAM child `b336aa0cd13b6abafde6938d32f5380f4b99f471` first formats only `test/integration/bff-session-admission-host.test.ts`. After provenance review, child `a1457be` regenerates the checked-in SDK for the already-published native-session/profile operations (`ReadAccountProfile`, `VerifyNativeSession` and native-session error codes). 主方复核 `pnpm sdk:check`、format/lint/typecheck 与完整 `pnpm verify`：**120 test files / 1561 tests passed / build passed**。该变更只同步生成物，不改运行时契约；C-1.3 真实资源与跨仓 E2E 仍保持 open。

Root then pinned IAM to `a1457be836c21eb558c8cbf7d9366e60f8ce59b8` and reran `git diff --check`, topology, and governance: topology **PASS**; governance **1846 passed / 3 skipped / 502 subtests passed**. Current Root worktree remains clean at the docs-only integration commits; no application service was started.


### 当前进度审计与方案重整（Root 4715d2b7，文档轮）

用户要求先整理当前所有问题、技术方案、TODO与Goal，本轮转为只读并行审计，Root唯一文档writer；没有继续实现、启动业务服务、安装Schema、提交或发布。执行树仍为task-a-c1-cleanup；既有App/BFF/Root未提交代码原样保留。

- 主窗口`get_goal`核验既有目标为active；G0已有reviewer通过证据。本轮没有complete、blocked或新建重叠Goal。新的阶段目标及17项TODO统一在[当前技术方案](../plans/2026-11-01-task-a-c1-c4-technical-plan.md)，原A-01～A-16责任完整保留。
- App writer停止在f5d122bb+56路径候选：报告Node22.23.4、focused23、contract452、architecture50、完整354files/6373pass/0skip、types/lint/build/diff通过；独审核56路径SHA无漂移，Public28.18原件/父逆证与旧hash保持。以上为worker冻结证据，Root完整门与Git集成尚未完成。
- BFF writer停止在228e3d6+11路径候选：移除main raw export/两处类型倒依赖、6测试明确raw入口、默认test/architecture纳入Nest suites。worker architecture73/focused123、types/lint/build/diff通过；独审补强side-effect import漏检后未见新增确定阻断。全业务与真实I/O未在候选最终树重跑。
- 当前raw census为56文件148直接调用、helper18文件42调用、composition3文件4调用、owner-resource9suites102调用；集合重叠，非可相加总数。生产入口隔离不等于ADR-036要求的raw server/runtime删除。
- 新补回原计划遗漏的Capability global_register：当前仍走IAM workload introspection。policy声明caller为kokoro-system，但System当前源码未定位真实producer；先盘点再固定窄切片，不新增无需求功能。
- 新记录Nest生命周期缺口：DatabaseModule只有factory，尚缺实际Nest app.close/SIGTERM→worker drain/池释放证明；raw lifecycle测试不替代生产图。
- Root本轮实际运行`python3 -m pytest scripts/tests/test_web_native_session_smoke.py -q`：exit1，1pass/2fail；两项AttributeError均为尚无close_native_resources。保留RED半成品，未继续实现。前序删除的KOKORO_WEB_REDIS_URL仍被App native登录flow/CSRF使用，登记为待修复配置缺口，非退休配置。
- 现runner仅fixture cookie/session/projects/fixture signout后401及日志4case；不含真实浏览器登录/双tenant切换/App退出/独立撤权。App默认Playwright开启preview；IAM verify不包含integration。历史IAM12、session7、HTTPS4证据保留原SHA，不外推到当前候选。
- 前序受管PG只读连接/Redis PING已通过，纠正旧“缺环境输入即无资源”的表述；本轮未运行服务健康探针或真实E2E，未宣称所有仓库已启动。dirty App/BFF尚不满足runner exact-source/clean/gitlink前置。

文档统一采用候选/已提交/Root复验分层状态；旧计划与问题台账增加历史入口标记，task/CURRENT仅摘要。验证结果在本段收尾补记，不将文档整理算作C gates或Task A产品完成。


文档收尾：三个只读角色完成审计；最终独审通过，17问题/17TODO/A-01～A-16映射齐全。补齐旧Nest计划历史导航，并修正T-06候选格式门与T-17前置运行保障的依赖循环。G-DOC/T-01仅标记文档VERIFIED，机器Goal保持active，其余C/A完成状态不提升。Root最终diff/新增本地链接检查通过，既有69个源码/子仓候选路径与本轮进入时SHA一致；本轮未新增业务修改。Root红测1pass/2fail仍如实保留，未把文档交付写成全量测试通过。


### Chunk 1 候选接收：App/BFF 主方完整门与独立 draft PR（2026-11-01）

用户明确要求每仓独立PR、完成后才考虑合并main；当前保持draft，不合并main、不部署。Root串行负责验证/Git，原main工作区未改写。

- App 56路径停写hash前后匹配；Root Node22.23.4/pnpm11.25 `pnpm check` exit0：contract48files/452pass、architecture4files/50pass、full354files/6373pass/0skip，lint/types/build通过。实现提交4260f698；fetch后把origin/main的空树merge整合到候选9ba653433c75dd3919bcc3de3cafc778fda4b975，前后tree相同。独立[draft PR #50](https://github.com/LordFoxFairy/kokoro-app/pull/50)已核OPEN/isDraft/head SHA；Root pin尚待。
- BFF32格式路径与原11候选不重叠，AST/注释32/32等价。第一轮Root全门真实失败于Storage固定Node22；追加T-18将七生成链/pin/CI/Docker对齐Node24.20.0，106generated正规再生成仍字节不变，owner/vendor/wire/历史摘要/lock保持。第二轮contract1343pass/1fail，旧blob负控临时repo漏带.node-version；只补复制pin一行，第21工具链路径，旧拒绝断言未放宽。
- 第三轮Root `pnpm format:check && pnpm check` exit0：contract1344pass/0skip，默认2345total/2343pass/0fail/2skip，lint/types/build通过；最终1068tracked冻结hash独审一致。两项skip均为既有schema测试缺KOKORO_TEST_POSTGRES_ADMIN_URL，另注入受管PG隔离fixture执行schema-governance整文件15pass/0fail/0skip，覆盖共存/SQL失败回滚/R237；各自有临时库由finally回收。未宣称完整业务PG/Redis integration通过。
- BFF准确提交原64路径及本仓CURRENT摘要，共65文件为173e0263f21e2cc7499a67592b4526d811dde693；提交/推送前非递归fetch确认origin/main是祖先，未改main。独立[draft PR #18](https://github.com/LordFoxFairy/kokoro-bff/pull/18)已核OPEN/isDraft/head SHA。
- T-13阶段：前序close函数未实现的1pass/2fail保留RED。实现后Root三套runner相关测试52pass/31subtests；独审发现Node期望/实测混淆、source失败丢先前证据、IAM测试部分连接失败回收、ps inventory异常阻断IAM强杀、保留依赖缺私有恢复身份五项问题。原writer退出live后将同6文件写区交接native_cleanup_review_fixes，修复中；真实IAM integration、最终freeze及原生链路尚未执行。
- 本轮受管PG/Redis只读探测通过，另只运行上述自有PG schema fixture；未启动完整应用组合、未接管用户预览、未交付常驻同步端到端环境。T-14只读已确认接收方和测试client，无System真实producer证据；需后续owner认证profile与取消边界设计，不新增无需求producer。

本次局部结果推进T-06/T-07/T-12/T-18，不关闭G1/G2/G3。机器Goal继续active，A门停写；完整最终门/真实四旅程/清理删除项仍以唯一技术方案为准。


### T-13 停写与主方真实宿主验收

六路径五项修复获规格/质量双审；最终manifest由Root逐hash核对。Root三套runner60pass/31subtests，完整治理1876pass/3skip/502subtests、exit0。IAM两真实host文件62pass/0skip；完整verify121files/1566pass，format/lint/types/contract/breaking/SDK/build通过。精确5路径（4测试+本仓摘要）提交e6a01cf7f1aeef0cfd5a63efe78e194b50ad1e9b并推送本仓draft PR #6，无main合并。App/BFF已验SHA不变；Root三gitlink暂存后topology PASS。未运行当前最小native/四浏览器旅程，随后按源码精确组合执行。暂停后用户已明确续接；工具Goal仍paused，不伪报active或重复建Goal。


### 精确组合首次 native 运行：真实失败与清理证据

Root b2f9a59c配对App9ba65343/BFF173e026/IAMe6a01cf，三子仓clean/gitlink以及实际Node24/24/22.23.4检查通过。正常runner和只增加内存脱敏诊断的复跑均exit1、0checks，stage=BFF startup；build/schema/IAMhost已过。诊断明确Nest UnknownExportException：ChatModule尝试导出由AgentDispatchModule拥有的CHAT_TURN_SERVICE。原始敏感诊断不保留；脱敏机器收据置ignored目录。两次cleanup均passed/quiescent=true、无文件保留，失败不计native成功。I-19/T-17登记前置修复，完整四旅程、后继清理和A门仍未放行。


### 用户恢复active后的TODO/Goal重新对齐

最新用户事件及get_goal已确认active；此前暂停原因只可确定是会话接收到paused状态/中断事件，具体触发方式无证据。修正主TODO中pin尚未提交、IAM旧verify、T13无退出收据等陈旧状态；保留历史证据，不抹掉真实失败。18TODO中的9条已验只代表切片/前置，绝不换算Task A完成比例。G1/G2/G3仍OPEN，当前优先T17真实DI启动回归，随后native/四旅程/global_register/删除/最终验收。方案新增低置信度前置排期预算与重估点，Task A全部16项未有可靠总工期。本轮仅文档整理，无业务改动/服务启动/新一轮全门。


### T-17 真实DI前置修复与完整门

BFF173e026基线新增实际生产AppModule compile回归，五阶段真实RED定位Chat/Projects/Skills非法导出及ProjectAccess/Billing缺DB token；只修正五module imports/exports。7路径停写、范围外1061tracked不变；四关键token单注册/严格owner同实例，默认test/architecture先clean build，不用stale dist。两失效源码断言核对回真实owner，原业务断言保持。独审CLEAR；Root冻结1068hash逐项核验，完整format/check exit0：contract1344pass、default2346total/2344pass/0fail/2skip、lint/types/build。workerarchitecture74/runtime5辅助证据。BFF4d6d17b（7代码/测试+CURRENT）沿PR18交付，未合并main。当前尚未用新pin跑真实native，完整T17生命周期仍OPEN。


### Root535e7071 最小native成功收据

精确App9ba65343/BFF4d6d17b/IAMe6a01cf source/clean/gitlink与Node24/24/22.23.4通过；Root实际执行native runner，失败时才拦截诊断的包装未替换成功行为。4checks PASS：fixture native cookie的App session、同源projects、fixture IAM signout后401、秘密日志检查；cleanup PASS/quiescent=true/无保留workdir，脱敏机器收据在ignored本地证据。不是冷登录、双tenant、App退出或独立撤权的浏览器四旅程；也不证明完整drain/SSE/worker/PG池优雅释放。T-13在此最小范围闭合，T-17完整项/G1/G2/G3仍OPEN。

T-14并行仅落Capability三面文档71行，Root复核scope/派生auth索引/冻结合同关系及取消未知提交边界；9本地链接/diff检查通过，历史正文原字节保留。无生产/contract/provenance/测试变更，Capability44fcc5d三文档dirty待后继实现，不冒认证cutover完成。


### T-05真实冷登录RED、T-14并行候选

当前精确三owner组合的新Chromium空context没有注入cookie，真实/login表单已出现且POST303；其后浏览器同源session401、projects401。测试邮箱由本次自有IAM fixture get-session内存读取，密码是现fixture公开test-only常量，未记录凭据/会话内容；独立脱敏收据保留HTTP状态。原最小HTTP4checks仍PASS、该run资源清理PASS；两类证据不能互相替代。现有效App/IAM/BFF固定Product设计与G0均未批准同App跨tenant正向切换，Root纠正T05错误要求为异tenant会话拒绝/固定域恢复；App补固定tenant原生准入，不恢复selector。

Capability T14按已审三面门实现，Node24.20.0/pnpm11.25 frozen install成功、lock未改；实际RED含System仍OAuth、缺auth-source索引、两处取消迟到写，后继候选尚未最终停写。Root三退休resource配置消费者6路径候选独审CLEAR，主方实际154pass/141subtests；同文件聚合credential与单projection同名O_EXCL碰撞先真实RED后独立文件名修复，真实文件权限/精确内容/正常异常回收保留。Root完整治理已exit0：1879pass/3skip/506subtests，六文件冻结hash保持；真实Capability接收方尚未运行。旧opt-in/CI其他OAuth债务不算本片通过。

### 本次用户四问对齐与App候选交接

get_goal实测active；当前Goal只覆盖C-1.3～C-4，Task A产品16项未闭环。暂停历史仅有paused状态事件/中断证据，不猜客户端具体触发。Root更新唯一台账主表、已验前置复选框、当前组合与并行角色，旧启动失败/后续设计待做文字归为历史。保留3～7工作日为低置信度C阶段资源预算，不作为Task A全部工期承诺。

App9ba基线新增五文件冷登录候选已停写；worker日志55pass/0skip、lint/typecheck通过，尚未Root完整门或真实浏览器GREEN。记录为候选交接，不提前关闭I-21/T-05。Capability取消deadline两负控RED已登记在T-14，允许等价识别既有Connect DeadlineExceeded的最小修复，不扩事务方案。此次进度整理未另启服务、运行Schema或提交/推送/合main。

随后T-14 worker交接：71路径（67存在/4删除）已停写，最终7files123pass/0skip，触及format/eslint/typecheck/tsc编译/readonly publication/diff均通过，独审deadline修复后CLEAR。以上是worker证据，不是Root owner全门；Root尚未运行该接收方真实PG/Redis。T-14标REVIEW_PENDING，G1不提升。

### T-05 App冷登录Root主验及PR50交付

Root全1494tracked hash冻结后以Node22.23.4/pnpm11.25.0执行pnpm check：exit0、contract48files452pass、architecture4files50pass、full354files6401pass/0skip，lint/types/build通过。前后输入hash一致；独审CLEAR。五路径提交727cd674fd45487d3d9becc685701546623865b1，fetch非递归核main/PR分支无新分叉后沿PR50推送；未合main。真实浏览器GREEN待本次Root精确gitlink提交后运行。独审辅助29测试使用Node24，不替代Root规定Node22主验。

只读发现App退出nativeSignOut POST未传body与transport严格规则不符，登记I-24待实际复现；不据静态疑点称退出已修。Capability停写71hash复核及独审CLEAR，Root完整门独立串行启动，尚不提前报结果。

### 冷登录真实GREEN与T14完整门首次RED

精确Root4fdb2ede/App727/BFF4d6/IAMe6实际跑同冷登录诊断：空Chromium且cookies_injected=false，表单303/session200/projects200，status=passed。原native runner4checks PASS，source/clean/gitlink及Node均真，cleanup passed/quiescent、无文件保留。保留旧RED与新GREEN独立脱敏收据；不把该诊断当完整四旅程或常驻环境。

Capability Root首次format/lint/Prisma validate/build均0，verify1：3049pass/678skip/2fail（preflight旧ENOENT与generated-client旧wrong-purpose Code16），默认678skip不算通过。1110文件前后hash完全一致，无生成漂移。仅两既有测试语义承接后再Root真实与完整门，原RED保留。

T14首次真实接收方组实际RED：System注册/重放/冲突/disabled/撤销已走，末尾断言误用了canonical不存在的tenantId。按原schema改查ownerTenantId和ownerUserId均null，所有zero receipt/outbox/IAM负控保持，生产零改动；失败run的数据库inventory前后相同。旧日志归档，新72路径停写，待Root复跑。I-24已真实transport RED→GREEN候选，主方全门进行中，不先报真实退出成功。

I-24 Root完整check exit0：contract452、architecture50、354files6403pass/0skip、lint/types/build，1494hash保持；独审CLEAR，三路径1d54eedd沿PR50推送。Capability真实组修canonical断言后exit0，1pass/13非选，数据库inventory前后相同，零Redis key写；实际覆盖System注册/重放/冲突/disabled、错caller与unknown拒绝、撤销、两owner字段null及零receipt/outbox/IAM。最终完整门另跑，不用1case代替全门。

### T14源码交付及I24真实第二层RED

Capability最终72路径加CURRENT为f515e225；Root五门均0，202files3051pass/678skip，1111输入停写前后hash一致。真实receiver1pass/13名称未选、DBinventory保持。已独立推送PR13，base原PR12候选；fetch发现其4新增提交2ad（73路径含contract/schema），PR13实际CONFLICTING；不force、不合并main，后继独立集成与重新全门登记I-25。

Root325d/App1d54真实冷登录仍303/session200/projects200；实际App退出415/session200/projects200，内存旧cookie独立HTTP重放亦200。原fixture4checks和cleanup PASS不覆盖该RED。锁定BetterCall有流无Content-Type抛415、JSON空流又400，既有IAM真实HTTP成功例是JSON {}。因此I24保OPEN，批准仅App adapter将已严格校验空浏览器请求规范化为固定JSON {}两字节，不放宽用户body/Origin或transport。

I-25独立只读merge-base/diff/legacy三参数merge-tree确认9重叠/5文本冲突，并发现远端v2 contract generator重建provenance会丢T14 serviceCredentialSources的确定接缝；登记精确双checker/生成保索引回归及新canonical真实验证要求。未写Git对象/index/worktree，未擅自合并B01或推进其消费者。

I-24第二层候选Root完整check exit0（452/50/6407、lint/types/build；1494输入hash保持），独审CLEAR。e1be73e0三文件沿PR50交付，浏览器严格零体不变，只有adapter固定JSON{}两字节；本次Root精确pin后真实复验，上轮415仍留证。

### I-24真实退出最终GREEN及oracle纠正

Root1e6/App e1be精确组合：真实新Chromium登录303、session200/true、projects200；App sign-out200、session200/false、issuer token cookie0、projects401、内存旧cookie重放401。原4checks与cleanup PASS/quiescent/无保留文件。首轮新实现signout已200但临时driver误要求缺cookie session401；核现native route和既有契约后改精确匿名false/零cookie及两个401，完整重跑GREEN，生产无额外改动。旧415真实RED及错误oracle均保留。脱敏浏览器收据与source SHA/driver hash/cleanup存同ignored run目录，不记录原cookie/密码。该范围不冒Settings点击或完整四旅程验收。


### 2026-11-02 T-05 browser fixture 主控真实 RED

在Task A工作树、IAM e6a01cf7基线上，仅现有host integration新增测试；Root使用Node24.20.0、corepack pnpm及既有受管PG/Redis执行：

```sh
corepack pnpm exec vitest run test/integration/bff-session-admission-host.test.ts -t 'binds only fresh browser sessions and isolates tenant, signout and revocation journeys' --maxWorkers=1
```

exit1，1 failed / 10未选（不计通过），2.74s。ready阶段成功，发送browser_fixture后旧host严格command enum不支持该命令，退出导致`host exited before browser protocol response`；失败对应缺失协议而非资源启动失败。未修改生产、放宽断言或启动产品旅程。测试冻结SHA256 `23adf38ecc115b6802a97240911a2061331b8f89c1d61f3af26d3533785c157e`，原host SHA256 `9e52a911f77f44e64a1e0eca02abeceb1a3027d457d9a891b0b4581016cfe5be`。本次不据进程退出宣称完整资源inventory验收。

原IAM writer继续test-only host有限协议及pending-command关闭；独立Root worker先补永久browser模式的行为测试，互斥写区。Root负责真实资源、独审接收、完整门及Git。T-05/G1保持OPEN，未运行GREEN/浏览器四旅程。


### 2026-11-02 T-05 Root 永久 browser 模式真实单测 RED

Root主方执行`python3 -m pytest scripts/tests/test_web_native_session_smoke.py -q --tb=short`，exit1，34 failed / 30 passed，3.88s。新增模式选择、有限broker、结果验证、main失败传播和browser group优先清理尚无实现；无collection错误，原30测试仍过。此阶段只有单测替身，无浏览器或PG/Redis连接。已交唯一Root三路径writer实现；最终receipt需固定白名单HTTP/owner/UI事实而非仅passed标签，取消与迟到仅记录实际观察分支。主方将按停写候选重跑相关门，不以本RED或worker结果称四旅程完成。


### 2026-11-02 T-05 首次候选真实运行与退出 oracle 纠偏

Root执行新主旅程及pending信号/EOF三个选中测试：1 failed / 2 passed / 10未选，6.90s。两个pending关闭案例通过；主旅程实际sign-out200后物理row仍在，原测试期待消失失败。独审与owner writer分别核当前`account-session-adapter`把官方delete转为`terminateAccountSessions`，repository只收紧expiresAt并撤派生凭据；DATA_MODEL明确expired tombstone保留。故不改生产、不额外DELETE换绿，而在私有inspect协议增加unexpired事实，保持exists物理语义；补旧cookie原生get-session null及后续BFF401。此为新增测试oracle错误，原HTTP退出修复不重开为生产缺陷。原RED保留，候选纠偏后重新冻结/独审/实跑；T-05仍OPEN。


### 2026-11-02 T-05 IAM test-only host 候选真实 GREEN

Root第二轮曾因同一测试第4次登录返回429而失败（1fail/2pass）；已核锁定BetterAuth `/sign-in*` 特殊限流3次/10秒，保留原规则，将独立历史SID重绑风险拆到独立host，两次登录；主旅程保持三次，不更改IP/headers、不等待假时间或关闭限流。

新冻结host SHA256 `48ac3b1aa6dacf0dddd49db1b9c6f52b8e96707ad1efde57b90fa1a309ea0659`；integration `24e86cf7a1973a37d410b32090dd07efba46a77e51acb67c1d0a0bc94b8e4ebf`。规格与质量独审CLEAR。Root新增4个选中真实测试4pass/10未选（9.75s），再完整运行native host和原web-oidc host两个integration文件，**66pass/0skip，110.76s，exit0**。覆盖真实owner登录/session绑定、异tenant与membership隔离、退出tombstone/旧cookie原生失效、SID历史重放、reset/stop及pending SIGTERM/EOF资源回收。此为测试host验收，不是App UI四旅程；owner完整verify随后串行执行。


IAM最终verify exit0：Node24.20.0/corepack pnpm12.3.4，format/lint/types/contract/SDK/default121files1566pass/build；536 tracked输入hash前后不变。Root在确认远端main无新增、PR分支与本地HEAD一致后，仅暂存原3路径提交`1ee8d156252cc1c19ba6951546552e9b01123979`并推送原draft PR6；GitHub核PR OPEN/draft、head精确匹配，未merge。此时Root尚未提交新gitlink，浏览器driver规格独审发现“关闭整个Settings会丢已显示快照”的P2，原writer最小修复中；不以已过78单测代替真实UI退休证据。


### 2026-11-02 T-05 Root 永久 browser 模式工程接收

规格独审P2已修：不Escape卸载Settings快照，而通过现有appearance→account标签保持边界；真实profile200 barrier就绪后、tenant mutation前明确验证已有name/email可见，receipt缺该事实或false均拒绝。正常读取/恢复仍要求可编辑。真实本地pipe测试另复现进程stop→group检查间reap竞态，局部改为stop→wait(5s)→group检查，等待失败仍保留依赖；没有改共享runtime helper。

Root停写复验：82个runner定向通过（5.09s）；完整`python3 -m pytest scripts/tests -q` **1931pass/3skip/506subtests，122.05s，exit0**；两个Python文件Ruff format/check、Node22.23.4 driver语法及diff通过。规格/质量双审CLEAR。3路径冻结SHA与执行前后相同：runner `8150db322a6050ba474bdb1d75b89a46a1828ae884f4508bb8b456e427a5e127`、Chromium driver `1ca96c53a1eb47e18ec3dadfa15cab9225f49706740d2a4b6f95540a6ce5f3bb`、runner test `7ddddb3b4f1251708864b998e5e32d76a199e7e2c49186d0a1ddddff46de8bd9`。

这些仅为编排工程证据（含本地pipe子进程），不是实际App/IAM/BFF浏览器四旅程。默认最小4checks保持；新模式fail-closed，真实scope、frame focus、迟到响应及Chromium子树清理要由精确提交组合实际运行后记录。


### 2026-11-02 正式浏览器 RED 与当前状态复核

当前Root `dd447c6878c3b00340e51554311340a2dc1857c0`，精确IAM1ee8/App e1be/BFF4d6；d309永久driver工程门1931pass/3skip后，dd447仅增加白名单stage/type/driver行列诊断，Root91定向、Ruff/Node语法/diff通过，未再运行完整治理。不将d309完整门冒称dd447全门。

正式browser receipt `var/dev/web-native-session-smoke/6273525d4a9b3328ff50b4ae/receipt.json`：status failed，stage browser cold_login，TimeoutError位于driver114:50账户入口可见性等待，completed_journeys=0；此前表单303与/app URL等待已过。cleanup passed/quiescent、owned_files_retained=false，凭据日志检查通过。原d309首次失败同样不得标四旅程通过。

私有诊断副本（不作为正式验收driver）在run `1971c4dc963c90e4229aa617`仍失败且cleanup通过；其行号124属于副本，不套用于正式driver。脱敏诊断：session200/认证true、SSR admitted=true，但UI未就绪；脚本70×200/22×304，无脚本失败；14次精确HMR Upgrade请求均404，13条console错误均为WebSocket分类。源码代理剥离Connection且无101双向隧道，确认传输缺口；尚未证其是UI超时唯一原因。I-26收录修复边界与原四旅程重验条件，不以诊断放宽产品断言。

本轮用户要求进度/Goal/TODO/工期复核：主控get_goal返回active，Root与两只读agent核26问题/18TODO/16原A项；修正当前摘要仍写tests-only待RED的过时状态。未启动服务、未改业务代码或共享资源。当前G1/G2/G3未过，没有可保留同步环境；历史暂停具体触发来源未确认，不归责用户。文档diff、链接及独立复核结果在本轮交付记录，不把本次审计算新增运行验收。

本轮文档复核完成：独立review CLEAR；I-26行分隔排版已修。主控`git diff --check`通过，四文件本地Markdown文件链接69个检查/0缺失（不含anchor有效性验证）；问题26/TODO18/原A16计数核对一致。仅上述四文档未提交，基线dd447c68，未修改业务源码或PR/main状态。


### 2026-11-02 I-26 隔离 HMR 传输修复工程接收

Root在08c00523文档基线上实际执行tests-only真实TLS Upgrade回归：1 failed/22未选，0.69s，期望101实际404；证实旧代理丢Connection Upgrade。随后仅修改共享smoke代理、native runner和两现有测试文件：browser-mode Web显式启用精确HMR路径，固定loopback上游、严格101、无额外子协议/压缩协商、双向固定缓冲与TLS pending、有限握手/连接数/idle/total、关闭等待自有handler；默认HTTP/SSE不启用。不改App/IAM/BFF产品源码、认证或driver断言。

独审发现并修正enabled普通POST短读、背压空转、普通上游关闭遗漏、连接数上限与普通响应超时从10秒误缩5秒，均有相应回归。新增raw target精确校验，避免HTTP parser归一化`//`路径误入HMR。普通HTTP连接预算5秒但响应读仍保原10秒；body上限及SSE逻辑不扩大。规格与质量双审CLEAR。

Root停写复验：三现有文件定向**165pass/52subtests，40.69s，exit0**；完整`python3 -m pytest scripts/tests -q` **1959pass/3skip/531subtests，157.47s，exit0**；四文件Ruff format/check及diff通过，四输入SHA256前后不变。代理e615d6bae0490f4b8987a13d60b5e8b000a696f9f2dcd87558ac2f8aef3bc8c4；native runner8e4037531e7052a927d6af189bc880064e9a1b0682b3a663d4bbc1f18b1be995；代理测试8526f45802bcb52ef9eded3e48c038f4d3acbad83b0ad4c4ab0bb0a337c6fc25；native测试dd877132fd4b467f4611d8054d93b35117d68b1057cea03a8e5963a3835bbfcd。主方日志留私有/tmp，不入Git。

以上证明代理工程切片，不证明HMR是原UI卡住唯一原因。Root精确提交后跑正式原四旅程；真实结果之前I-26/T-05/G1保持开放。

### 2026-11-02 I-26 后正式旅程推进与 I-27 transport RED

Root50ac142b正式run8160b6005dd8862d3c703cb0已越过cold_login账户入口、真实profile200及可见性，进入tenant_rejection_recovery，在driver226 profileBarrier catch失败。整体收据仍completed_journeys=0，无部分成功receipt，不冒四旅程通过；cleanup PASS/quiescent/无保留文件与credential scan PASS。

私有诊断副本e9584f77fc27584a88faf83c仅新增错误固定类别与同一原请求的loopback读取对照：原route.fetch在secure TLS建立前断开（upstream_status=null），不是ENOTFOUND/证书校验/超时/业务断言；同一profile请求使用既有自有HTTPS端口、原Host与allHeaders后返回200。未输出cookie、原错误message、响应体或URL；诊断副本不算正式验收。前两诊断run a53a06c9/222a44ab用于缩小错误分类，均保留失败。

锁定Playwright1.62.1的Route.fetch走Node APIRequestContext/http(s).request，不继承Chromium host-resolver-rules；ignoreHTTPSErrors会继承，不错误归因证书校验。App readAccountProfile拒绝上游set-cookie且自身仅返回cache-control/request-id，loopback对照不涉及新cookie写入。登记I-27/既有T-05，仅修driver传输映射，保真实上游与全部UI/预算断言。

I-27候选已停写双审CLEAR；Root重跑native runner整份测试108pass（5.97s），Node22语法、Ruff format/check与diff通过。driver SHA256 8214c4649bd90974b2532c3404cfde24e9115e4a12f71fc9d9c0a262c1b6caa4，测试514c5d1b9fb6c78956fa1f6e8e6b5bc8661970c0038f6d1cad7d6dceabd49458。该后继为局部驱动修复，1959完整门仍绑定50ac前一源码；精确提交后先复跑真实旅程，再按最终影响完成Root全门。

### 2026-11-02 I-27后真实旅程与G1独立预审

Rootbad20503正式run c2e12b5aab0f6d7eb70bb900已取真实profile barrier，在driver382异tenant状态断言失败。私有只增加status/固定code投影的诊断40e265df84d599a6b174487d显示session401/native_session_required、projects403/product_tenant_forbidden；不是越权200。BFF authorizeUserRequest明确namespace不符固定tenant返回403，App auth/session将不合格claims投影401，故登记I-28测试oracle纠偏，不改业务实现。其他membership/exact-session撤销保持401。正式run cleanup PASS/quiescent/无保留文件、credential scan PASS，仍无完整四旅程收据。

独立G1只读审计另确认I-29：生产Nest feature→authorizeUserRequest缺native配置分支→SessionAdmissionClient.verify→旧IAM session-authorizations/verify仍可达；不是单纯旧raw测试，须G1前移除回退并承接有效权限。I-30为消费证据缺口：IAM native artifact SHA匹配、BFF vendor497900包含native操作，但生成器include未纳入且client手写native schema；需受控消费审核，不冒称已证wire失败。公共OAuth/skill.list不随名称误删。完整负控仍需case/SHA/result/零副作用映射，四旅程全绿也不自动关闭G1。

I-28只纠正已由实际行为与owner契约证明的异tenant oracle，新增两个实际typed code并拒绝旧401/401或任意错code；规格与质量双审CLEAR。Root目标121pass（6.02s），最终完整治理**1989pass/3skip/531subtests，152.27s，exit0**，三输入SHA保持。driver a8216f6cf18ceb4f59193d93ce6b79e4e30b1402f2bb4880cb531b586b674152；runner7abe404d0879bb77a5869ca9385bcc35c8317c7476b52c7b99ca6f6fcca17b27；测试058dcc66d1835eda1db1caa2de00dfcc54f3203297b32b35e0fff80cd826fa11。原App/BFF/IAM源码与pin不变，精确提交后原四旅程再跑；负控不改成任选401或403。

### 2026-11-02 I-32真实焦点诊断与额外G1证据缺口

Rootcc405cc4正式run6cb4509024b133f193c0ddc7：tenant_rejection_recovery在focusProbe172等待session响应超时；cleanup PASS/quiescent/无保留文件、credential scan PASS。锁定Playwright1.62.1 coreBundle37399在主frame默认设置focus emulation=true。私有诊断只对page/peer各创建CDP session关闭该override（不dispatchEvent、不加timeout），ecfbb0f5659e34406c291314记录trusted_observed=true、session401，随后异tenant退休/恢复及UI退出全段通过；最终在independent_revocation的新context登录账户入口114超时。私有副本不作为正式4/4，所有失败收据保留，cleanup均PASS。I-32只授权focus纠偏，不猜测第四旅程根因。

G1只读负控审计登记I-31：BFF默认test未包含native-session-admission三例，IAM direct-service测试参数未含session_admission；现有匿名/Origin/伪造身份/撤权风险可复用，但native专用服务凭据、重复退出、IAM连接失败/超时与native mutation零副作用须补明确证据。紧凑case/基线/缺口映射已入唯一计划§5.1，未运行这些新门，未据原默认测试数量宣称完成。

I-32两路径已获规格/质量独审CLEAR；Root整份native测试128pass（7.15s），最终完整治理**1996pass/3skip/531subtests，152.65s，exit0**，两输入hash保持。driver79886347ccdbbaab87be984761bff24c28564f3071fe1d9cb6f267433bfa1354；测试0ffbb98578080aad3653e30c5cad965346b70452d541f295dd6a9d07bfeb7114。仅关闭Playwright对两页的固定focus override，仍由真实bringToFront触发可信事件，不合成事件、不改预算；Node/Ruff/diff门一并核验，精确提交后正式四旅程重跑。

### 2026-11-02 Root34af正式第四旅程失败（I-33）

正式run85be0e91605401666e2bc49c，stage independent_revocation，Error/driver140:3，失败在openProfile的200断言，之前三旅程的顺序断言已走过；未输出完整browser_result，整体失败/0完整旅程收据，不伪造3/4验收。cleanup PASS/quiescent/无文件保留，credential scan PASS。

私有诊断5b4c6fc8与36234205均到相同profile断言；3623420569a1b8f9b6f7dbbe仅增加固定状态字段，确认login ordinal=3、profile status503、typed error code未取得，未保存body或原错误message。该次与正式run cleanup均核PASS。旧私有ecfbb0曾同阶段账户入口超时，作为现象保留，不覆盖正式profile失败。I-33下一动作是定位响应所属边界，未改产品或放宽200/显示/时限要求。

本轮所有实现worker已停写，独审已交接，所有主控测试/浏览器handle均终态；后续可直接继续既定I-33调查与G1 I-29～31，无需用户重复批准。

本轮最终文档独审CLEAR：修正I-21误拼表格与真正T-05旧状态，历史交接/当前动作和未重估预算分开；问题33/TODO18/原A16复核一致。Root topology PASS，四文档本地文件链接69检查/0缺失（未验证anchor），diff通过；源码仍34af35dd，文档后继不改变1996治理门绑定。每仓保留原draft PR、未merge main/部署。

### 2026-11-02 任务状态与遗留诊断终态复核（文档轮）

Root HEAD6b0184e6，最后源码34af35dd，工作树文档修改前clean。本轮get_goal=active；取回上一诊断handle终态exit1，d11f80d96398bb7fef5e138e收据failed、completed_journeys=0、browser/browser_failure=null，cleanup passed/quiescent/无保留自有文件，credential_log_check passed。仅复核既有运行，不启动新服务/测试。

私有代理元数据83条，含profile503的合法JSON/typed code account_profile_unavailable；同run另有/v1/me429。request-id散列未建立跨跳关联，浏览器详细诊断文件未产出，故不能认定429已是profile503根因，也不能把该副本归为正式四旅程验收。相关诊断runner/driver进程检查无匹配，执行已结束；不把Goal active写成后台仍在运行。敏感响应体/凭据/机器PID不写入台账。

本轮三个只读角色并行复核TODO分类、闭环证据、A全范围估时；Root唯一文档writer。前述已验工程门保留原SHA范围，本轮不复跑业务全门、不宣称新业务通过。

文档停写复核：独立review CLEAR；Root核18个唯一TODO、33个唯一问题ID及状态分类一致；本次新增行本地文件链接2处/0缺失（未检查anchor），git diff --check通过。本轮4份文档未提交，无源码或gitlink改动；旧业务测试结果仍绑定原源码，不冒本轮重跑。

### 2026-11-02 I-30 正规native消费闭合（BFF f81f271）

固定IAM497900/0.18 vendor/digest保持，include唯一新增verifyNativeSession，23→24；正规生成替代client手写success/error，删除任意error-code fallback；native套件纳入默认入口。generator仅在对应response精确恢复三层closed及RFC3339 offset，16生成文件allowlist/双生成保持；无Schema/lockfile/授权业务变化。I-29现permissions映射与Bearer回退未冒完成。

writer先RED3（operation/default入口/unknown error），首轮生成又真实暴露offset拒绝；修正后定向79pass。规格审直接核owner原件、generated闭集/日期/错误等价及摘要CLEAR；质量审CLEAR。Root停写1068输入hash冻结前后无漂移，Node24.20.0，pnpm format:check与pnpm check exit0：contract1345pass/0skip（168.53s），默认2350pass/2原条件skip（203.89s），lint/typecheck/build通过。真实资源测试未在此片运行，skip不计通过。Root未修改或新增业务门限。

BFF十路径明确暂存提交f81f271，非递归fetch核原PR分支0/0、main无未整合新增，再推送原PR18分支；不合并main、不部署。后继Root精确pin并运行I-33私有请求关联实验。

### 2026-11-02 I-33关联因果与单变量窗口对照

组合Root75f6e1ce / BFFf81f271、App e1be、IAM1ee8。私有run7890d3103ca3b7ead51c0f52仍failed independent_revocation/driver140:3，但同profile入站hash匹配唯一/me429 session_rate_limited（2ms），App随后503 account_profile_unavailable（11ms）；无Retry-After、无该次业务profile调用。关联只加精确profile GET的随机request-id，不改身份/限流/预算，不存body/cookie。cleanup passed/quiescent、credential scan passed。

同组合私有单变量run3dbb48c32c2b8082d65ffa9a：仅旧context关闭后、独立撤权contexts创建前sleep60,001ms，原175秒总预算/3秒焦点/4.5秒退休与全部assertions保持。结果passed/4完整旅程、0次429、5次profile200；观测请求完成最大间隔61,694ms，cleanup passed/quiescent/无保留文件、credential scan passed。此为私有修改driver的实验证据，不替代正规源码旅程验收，也不证明共享credential的产品容量合理。

只读owner核：native配额继承旧Internal Guard的100/60秒安全默认，key为caller/credential/operation；锁定Redis存储只在首次INCR设置60秒TTL，拒绝不会延长。没有找到native聚合Web容量已验结论，不把对照通过当产品容量修复。Root正规场景边界调度候选及App最终鲜验不可用误判401的I-34独立修复进入TDD；各自窄写区、不改IAM限额。

### 2026-11-02 I-33正规编排与I-34生产窄修验收

Root driver两路径c142c49c：新增场景边界完整窗口等待，remaining budget不足/提前完成/到期/sleep异常均拒绝，不改175s及撤权断言。writer先RED8与计时临界RED1，再focused10/整份native137通过；规格/质量双审CLEAR。Root停写整套治理2005pass/3skip，157.65s、exit0，两输入hash保持；Node/Ruff相关检查通过。未以私有4/4代正式验收。

App fdbb49f17bfbb09684cd5c3cfaea1c1678306697：仅删除account-profile最终admission的catch(null)，两份相邻测试/索引承接；最终429/503/断连均503、真实无效401、同主体200。真实loopback RED3（原401）→focused40pass；双审CLEAR。Root Node22.23.4 pnpm check完整exit0：contract452、architecture50、default354files/6411pass/0skip（103.08s），lint/typecheck/build通过；1494输入hash前后无漂移。App非递归fetch确认main无未整合新增、原PR分支0/0，三路径明确提交并推原draft PR50，无main合并/部署。正式组合旅程待Root新pin后执行；未跑无关preview Playwright全集。

### 2026-11-02 I-29 owner局部设计门通过（尚未实现）

IAM5fffe60/BFF105024d各仅三面设计文档，共218行新增、原文逐字保留，12本地文件链接/精确六路径/diff检查通过；规格/架构与质量双审CLEAR。初审服务与人类401同码歧义已收敛为native2单一新增服务错误code→BFF既有503，只有明确human拒绝401；此是目标待正式发行，不改native1历史或当前源码。平台管理员真实事实、四action及Account/Team事务证明、全部BFF消费者/删除清单、原角色/operator/公共身份政策与零DDL已明确；容量不新增SLO/生产压测门。两仓各推原draft PR6/18，无合并/部署。此次文档任务未重复运行业务全门，IAM运行源码仍1ee8、BFF仍f81；Root后继精确pin。

### 2026-11-02 正式native浏览器四旅程4/4（Root aec5775a）

正规driver c142c49c，Root精确组合aec5775a；App fdbb49f17bfbb09684cd5c3cfaea1c1678306697、BFF105024d33611dfaccc9a072d04f0864d03015ef9、IAM5fffe60ce07920b761213339e66bfbde31302603。run2a960804d5cac08754f45228为正式browser_journeys模式，status passed/completed_journeys4，三owner clean/root_gitlink_matches全true，实际Node IAM/BFF24.20.0、App22.23.4。此非私有修改driver，不注入诊断request-id；Root与三个owner验收前后停写。

冷登录无初始cookie→303、session/projects/profile200且私有资料真实可见；合法异tenant→session401/native_session_required、projects403/product_tenant_forbidden，资料退休后重登恢复200；UI退出200、cookie0、session200/false、项目及旧cookie401，owner保expired tombstone。A exact Session被删除后A两读401且UI退休，B仍200；撤member后B Session仍存在未过期但两读401且UI退休。held profile上游200、本次race observation=cancelled、cross_tab_focus=true/private_ui_retired=true，不冒非协作JS迟到值交付覆盖。

cleanup passed/quiescent、无保留自有文件/恢复记录、credential_log_check passed；所有进程已终态，未留常驻同步环境。Root topology PASS、工作树clean（文档补录前）；未将临时三服务旅程称全产品/所有仓库启动。I-26/27/28/32/33取得当前完整旅程证据；G1仍需I-29完整native owner/consumer切换与I-31其余负控，G2/G3/原A功能未关闭。

最终Root文档独审CLEAR，已纠正旧剩余预算/历史设计/待运行措辞；主方核34唯一问题、18唯一TODO与状态分类、后续验证命令表均一致，新改行2处本地文件链接无缺失（anchor未验）、diff检查通过。Goal继续active；未将4/4提升为G1或全Task A完成。
