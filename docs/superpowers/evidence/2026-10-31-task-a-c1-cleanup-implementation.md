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

BFF child `7a41d9b` centralizes scheduled-task create/update/delete/retry and project-scoped create business execution in `scheduled-task-mutation-native.ts`, shared by `ScheduledTaskMutationMiddleware` and raw `createBffServer`. The old `live-bff.ts` dispatcher is deleted; authorization, idempotency lineage, owner checks, stable task IDs, outbox service calls and error mapping now have one implementation. The raw server retains only the pre-admission check needed before the generic receipt claim.

验证：BFF build/lint/typecheck；Nest runtime/feature architecture 24/24；BFF architecture 34/34；scheduler + BFF mock focused 39/39；business-store integration 6 pass / 75 environment-gated skip。C-2 LegacyRoutes runtime and C-3 global provider census remain open。

### Project command/read cutover（2026-10-31）

BFF child `7a41d9b` moves project create/instruction command handling into `ProjectsModule` through `ProjectMutationMiddleware`, with a feature-owned `PROJECT_IDEMPOTENCY` provider. Native admission, strict JSON/name/instruction validation, persistent idempotency replay/conflict handling, project owner scope, slug-conflict mapping and canonical response envelopes remain unchanged. The project core-read adapter now also owns `GET /v1/projects/:id/tasks`; the duplicate `liveBffBusiness` task branch was removed. No second ProjectService, Repository or SQL writer was introduced.

验证：BFF build/lint/typecheck；Nest runtime/feature architecture 24/24；BFF architecture 34/34；BFF mock contract 25/25；Project pin focused 15/15；business-store integration 在缺少 PostgreSQL/Redis 时 6 pass / 75 skip。Nest 与 raw `createBffServer` 现在共用同一 `project-mutation-native` adapter，未保留第二套 create/instruction 实现；C-2/C-3/C-4 和 A gates remain open。

### Personal Billing owner cutover（2026-10-31）

BFF child `7a41d9b` moves personal Billing routes (`GET /v1/billing/summary`, `GET /v1/billing/ledger`, `PUT /v1/billing/credit-account`, `GET /v1/billing/plans`, `POST /v1/billing/checkout`) into `BillingModule`. `BillingPersonalMiddleware` and `billing-personal-native` share one admission, query validation, owner transport, bounded cancellation, response mapping and persistent idempotency provider; the old `owner.ts` Billing branches are deleted. Existing Billing owner and BFF mock fixtures remain unchanged.

验证：BFF build/lint/typecheck；Nest runtime/feature architecture 24/24；BFF architecture 34/34；Billing personal + BFF mock 66/66。Remaining owner route families and LegacyRoutes/global composition deletion remain open。

### System model catalog cutover（2026-10-31）

BFF child `7a41d9b` moves `GET /v1/models` into `SystemModule` through `SystemModelCatalogMiddleware` and `system-model-catalog-native`. The exact owner query projection, System credential transport, model catalog validation, request-id and upstream error mapping are shared by Nest and raw `createBffServer`; the duplicate `owner.ts` model branch is deleted.

验证：BFF build/lint/typecheck；Nest runtime/feature architecture 24/24；BFF architecture 34/34；BFF mock contract 25/25。Remaining owner projection routes and LegacyRoutes/global composition deletion remain open。

### MCP platform projection cutover（2026-10-31）

BFF child `7a41d9b` moves `GET /v1/mcp/servers` and `GET /v1/mcp/connections` into `McpModule` through `PlatformProjectionMiddleware`. Admission, MCP budget, strict query/body validation, named Platform projection client, cursor/error mapping and no-store response semantics are shared by Nest and raw `createBffServer`; `owner.ts` no longer dispatches Platform projections. The retired System/Skills fallback is isolated in `retired-owner-native` rather than the owner dispatcher.

验证：BFF build/lint/typecheck；Nest runtime/feature architecture 24/24；BFF architecture 34/34；platform projection + BFF mock 50/50。Remaining MCP/Skills owner surfaces and LegacyRoutes/global composition deletion remain open。

### Owner transport module cleanup（2026-10-31）

BFF child `7a41d9b` renames the remaining shared owner transport helper from `owner.ts` to `owner-request.ts` and removes the obsolete route-module name. System model catalog and Music now consume the explicit transport helper; no `liveOwnerBusiness` dispatcher remains.

验证：BFF build/lint/typecheck；Nest runtime/feature architecture 24/24；BFF architecture 34/34；BFF mock 25/25；Billing personal 66/66。

### Personal MCP route cutover（2026-11-01）

BFF child `7a41d9b` moves the full browser-private Personal MCP surface into `McpModule` through `McpPersonalMiddleware`. The route now consumes only a narrow `McpPersonalProvider` (personal client, MCP authorization, session admission), while raw `createBffServer` remains structurally compatible. Server icon handling shares the same narrow provider; no `BffServerComposition` construction or LegacyRoutes runtime dependency was added.

验证：BFF build/lint/typecheck；Nest runtime/feature architecture 24/24；BFF architecture 34/34；Personal MCP HTTP/command + BFF mock 106/106。Remaining Library/personal-file route families, LegacyRoutes/global composition deletion and C-4 full suite remain open。

### C-4 full-run revalidation（2026-10-31）

在 `7a41d9b` 后串行启动 BFF `pnpm test`：focused 早期继续出现既有 R357 shared-summary fixture failures，随后停在 `test/contract/skill-specification-http.test.mjs` 的长时间 pending 状态；已手动终止，未取得完整汇总，不能计作 C-4 通过。进程状态已复核清零；本次切片以 build/lint/typecheck、Nest architecture、BFF architecture、scheduler 39/39、BFF mock 25/25 作为有效证据。
