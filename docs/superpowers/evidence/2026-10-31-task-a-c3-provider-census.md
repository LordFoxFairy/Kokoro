# Task A C-3 Provider/Service Census（2026-10-31）

## 当前已清除的 global service 重复字段

`BffBusinessStore` 与 `PostgresBffRepositories` 已不再重复暴露：

- Chat：`chatService`
- ChatTurn：`chatTurnService`
- Project：`projectService`
- ScheduledTask：`scheduledTaskService`
- Account personalization：`personalizationProvider`

对应 feature owner：`CHAT_SERVICE`、`CHAT_TURN_SERVICE`、`PROJECT_SERVICE`、`SCHEDULED_TASK_READ_SERVICE` 及 `BffApplicationServices.services` 兼容聚合。

## 仍保留的 transitional raw-server seams

以下字段仍有真实 raw `createBffServer` / `LegacyRoutes` 消费者，暂不机械删除：

| 字段 | 当前消费者 | 删除前置条件 |
|---|---|---|
| `personalKnowledge` | raw compatibility adapter; `LegacyRoutesRuntime` now receives explicit `PERSONAL_KNOWLEDGE_REPOSITORY` | 删除 `BffBusinessStore.personalKnowledge` after raw/test composition consumes the explicit feature provider |
| `skillUsage` | raw Skill usage adapter; `LegacyRoutesRuntime` now receives explicit `SKILL_USAGE_READER` | SkillsModule/SkillsMiddleware 成为唯一 runtime path，删除 `BffBusinessStore.skillUsage` fallback |
| `skillAiAssociation` | AI Skill import raw adapter | SkillsModule association provider 覆盖 raw composition，artifact owner contract 保持不变 |
| `skillShares` | Skill share/exact-download raw composition | SkillsModule share/download provider 覆盖 raw source construction |
| `publicShareService` | raw public-share projection; `LegacyRoutesRuntime` now receives explicit `PUBLIC_SHARE_SERVICE` from `ChatModule` | ChatModule provider 覆盖 raw chain；删除 `BffBusinessStore.publicShareService` fallback after raw/test composition no longer needs it |

这些字段是当前存在证据的兼容边界，不是新的 owner；Account personalization 已从 global store 删除。禁止继续新增同类字段。

## BffApplicationServices 聚合

当前仍有四个聚合字段：

- `projects`
- `scheduledTasks`
- `chat`
- `chatTurns`

其中 Chat/Project/ScheduledTask 的 HTTP provider 已完成具名 feature seam；聚合仅保留给未迁移的 Chat POST/Agent dispatch、LegacyRoutes raw composition、integration fixtures 和剩余兼容路径。

## LegacyRoutes 删除门

当前生产引用仍集中在：

- `src/modules/legacy-routes/legacy-routes.module.ts`
- `src/modules/legacy-routes/legacy-routes.middleware.ts`
- `src/modules/legacy-routes/legacy-routes.runtime.ts`
- `src/bootstrap/server.ts`
- `src/bootstrap/runtime.ts`
- `src/app.module.ts`

删除顺序固定为：剩余 route census 清零 → raw provider fallback 清零 → 唯一 Nest listener/composition proof → 删除 LegacyRoutes runtime/module/middleware。

## 当前验证证据

- BFF architecture：34/34
- Nest runtime architecture：5/5
- Chat/BFF focused：230/230
- ScheduledTask focused：106/106
- BFF full：2316 tests / 2299 pass / 15 fail / 2 skip；15 项失败为既有 Storage/Product、Project exact-download、Admin credential、anonymous Share fixtures。
- Root topology：PASS

### 2026-11-01 Scheduler receipt port isolation

BFF child `039e8d8` removes the Scheduler callback route's type-level dependency on `BffBusinessStore`. The route now consumes `SchedulerDispatchReceiptRepository` directly for claim settlement and unknown-claim release, while its raw/test fixtures use the named `scheduledTaskService` provider. Scheduler focused coverage is 14/14; build/typecheck and diff checks are clean. This closes one C-3 port consumer but does not close the remaining compatibility aggregate or lifecycle/outbox port census.

### 2026-11-01 Skill Share provider type isolation

BFF child `27523d9` removes the native Skill Share route's `BffBusinessStore` import. Its raw compatibility extractor consumes only a narrow structural `SkillShareRepository` source, leaving aggregate knowledge at the bootstrap compatibility seam. BFF/Nest architecture and Skill Share HTTP focused checks are green; the R357 shared-summary failures remain the pre-existing fixture baseline.

### 2026-11-01 AG-UI consumer provider isolation

BFF child `11d8199` exposes the Agui-owned consumer repository as an explicit composition provider. The raw server's Chat provider no longer reads `businessStore.agUiConsumers`; only bootstrap fallback wiring still bridges the live PostgreSQL composition. BFF/Nest architecture and Chat/AG-UI focused checks are green, with no duplicate consumer repository or projection implementation.

### 2026-11-01 AG-UI projection provider isolation

BFF child `db3c94a` exposes the Agui-owned projection as an explicit composition provider. The raw Agent session path and projector use `composition.agUiProjection`; the aggregate `agUi` field remains only at bootstrap fallback wiring. Architecture, build/typecheck/lint and the focused Chat/AG-UI set are green; the compatibility aggregate is not yet deleted.

### 2026-11-01 Agent reader provider isolation

BFF child `4144fee` exposes AgentRuns-owned submitted-run and project-execution-binding readers through explicit composition fields. Raw internal admission and Run display no longer read `businessStore.submittedAgentRuns` or `businessStore.projectExecutionBindings`; only bootstrap fallback wiring bridges the live store. Focused Agent display/admission/binding coverage is 144/144, with no duplicate reader implementation.

### 2026-11-01 Scheduler/Artifact provider isolation

BFF child `1a1fe92` exposes Scheduler receipt/dispatch and Artifact Library repositories through explicit composition fields. Raw Scheduler and Library routes no longer read those repository fields from `businessStore`; the Project resource HTTP fixture now supplies `projectService` explicitly instead of `services.projects`. The combined Project resource/Scheduler/architecture focused set is 80/80; no owner or repository was duplicated.

### 2026-11-01 ScheduledTask compatibility view removal

BFF child `10477a7` removes `scheduledTasks` from `PostgresBffRepositories.services` and migrates Scheduler integration fixtures to `scheduledTaskService`. No `services.scheduledTasks` consumer remains in source or tests; the named ScheduledTask service and Scheduler callback provider remain the only owner seams. PostgreSQL/Redis integration execution is pending the local isolated environment.

### 2026-11-01 Project compatibility view removal

BFF child `c373066` removes `projects` from `PostgresBffRepositories.services` and migrates Project resource/delete and Chat project-selection fixtures to `projectService`. No `services.projects` consumer remains except the standalone Project MCP test fixture that does not use the concrete repository. The canonical ProjectService remains single-owner; PostgreSQL/Redis integration is environment-gated.

### 2026-11-01 Compatibility aggregate deletion

BFF child `e220ae4` removes the `services` compatibility view entirely from `PostgresBffRepositories`. All concrete Chat/ChatTurn integration consumers use `chatService`/`chatTurnService`, and the source/test census has no `services.chat`, `services.chatTurns`, `services.projects` or `services.scheduledTasks` consumers. This closes the aggregate-view portion of C-3; lifecycle/outbox fields and full cross-owner C-4 evidence remain separate gates.

### 2026-11-01 BffBusinessStore application-port narrowing

BFF child `46096d4` removes feature repository/service/AG-UI/outbox fields from `BffBusinessStore`. Bootstrap resolves the concrete PostgreSQL infrastructure through a local `BffInfrastructureStore` and passes named providers through `BffServerComposition`; application routes no longer receive a global feature-resource locator. This closes the global application-port field census without introducing a second owner.

## 2026-10-31 provider handoff update

BFF child `330e439` adds the explicit `PUBLIC_SHARE_SERVICE` seam to the transitional runtime. `LegacyRoutesModule` imports `ChatModule`; `LegacyRoutesRuntime` injects `PublicShareApplicationService` and passes it to `createBffComposition`; raw shared-public handling reads `composition.publicShareService`. `BffCompositionOptions.publicShareService` now prefers the feature provider while retaining the store fallback only for un-migrated test/raw composition. This is a provider handoff, not LegacyRoutes completion.

BFF child `46bb5ac` adds the explicit `SCHEDULED_TASK_READ_SERVICE` seam to the transitional runtime. `LegacyRoutesModule` imports `ScheduledTasksModule`; `LegacyRoutesRuntime` injects `ScheduledTaskReadService` and passes it to `createBffComposition`; `BffCompositionOptions.scheduledTaskReader` now prefers that feature provider while retaining the old service-derived reader only for raw/test composition. Current-read behavior remains covered by the existing scheduler focused suite; mutation/callback/outbox routes remain in the next census slice.

BFF child `d2b0bfe` adds explicit `CHAT_SERVICE`, `CHAT_TURN_SERVICE`, and `PROJECT_SERVICE` injection to `LegacyRoutesRuntime` from `ChatModule`/`AgentDispatchModule`/`ProjectsModule`. `createBffComposition` and the Chat authorization provider now prefer these named feature services; `BffApplicationServices` remains only as a transitional fallback for raw/test composition and un-migrated mutation/Agent paths.

BFF child `b9ac010` adds `PROJECT_SKILL_SELECTION_PROVIDER` to the same explicit chain. The raw server prefers `composition.projectSkillSelectionProvider`, while `projectSkillSelectionProvider(BffBusinessStore)` remains only a raw/test fallback until the project skill-selection path is fully owned by the Nest middleware.

BFF child `1301269` adds `PROJECT_MCP_RECOMMENDATIONS_PROVIDER` to the explicit chain. `LegacyRoutesRuntime` receives the provider from `McpModule`; the raw server prefers `composition.projectMcpRecommendationsProvider`, preserving the business-store constructor only for raw/test fallback.

BFF child `c8c3259` passes `SKILL_EXACT_DOWNLOAD_SOURCE` and `SKILL_SPECIFICATION_SOURCE` from `SkillsModule` into `LegacyRoutesRuntime` and `BffCompositionOptions`. The raw server can now use the feature-owned exact-download/specification providers without rebuilding them from `BffBusinessStore.skillShares`/usage; those store fallbacks remain only for explicitly un-migrated raw/test compositions.

BFF child `630efbf` adds a negative LegacyRoutes boundary for migrated Chat paths. `LegacyRoutesMiddleware` bypasses public share, archive/shared tasks, direct Chat reads, feedback, regeneration and move; un-migrated Chat POST/events/title/delete/share and project-scoped reads remain routed through the transitional dispatcher and are covered by explicit negative tests.

BFF child `3961450` adds `CHAT_IDEMPOTENCY` in `ChatModule` and moves direct no-`project_ref` title/delete/share mutations through `handleChatMutationRequest` + `liveChatBusiness`. The provider uses one PostgreSQL receipt owner and a process-local replay map; project-scoped variants and Chat POST/events remain transitional.

BFF child `76b9402` adds `AguiModule` providers for the canonical projection, consumer repository, session runtime and source-active gate. Direct no-`project_ref` Chat events now use `liveAgentSession` through `ChatModule`; project-scoped events and the LegacyRoutes projector worker remain transitional until Agent/AG-UI ownership is fully cut over.

BFF child `ff14c86` extracts `ProjectAccessModule` as the single `PROJECT_SERVICE`/`PROJECT_SKILL_SELECTION_PROVIDER` owner provider. `ChatModule` now consumes that shared owner for project-scoped mutation/event authorization, avoiding a second ProjectService/Repository implementation while `ProjectsModule` continues to own project middleware and exact-download adapters.

BFF child `ff14c86` also extracts `SkillInstallationAccessModule` as the sole installation client owner and moves Chat POST submission into `ChatModule`. The route reuses `ChatTurnApplicationService`, Agent outbox, ProjectAccessModule, Skill installation rechecks and idempotency; Skills/Projects consume the same installation client without a second Platform client.

BFF child `a5b94c0` moves run-control receipt/admission into `AgentRunsModule` with `AGENT_CONTROL_IDEMPOTENCY`, shared Chat/Project owners and the existing `liveAgentSession` control semantics. Agent dispatch worker lifecycle and remaining session/run paths stay transitional until the next ownership slice.

BFF child `ba8ab60` extends the LegacyRoutes negative boundary to the AgentRuns-owned internal admission/binding routes and exact Run display route. `AgentRunsMiddleware` is now the only Nest path for those route families; `LegacyRoutesMiddleware` bypasses them without adding another provider or changing the existing credential, owner-read, cancellation, response-cap or error contracts. Agent dispatch worker lifecycle, remaining session/run paths, raw compatibility composition and the global aggregate remain transitional.

BFF child `ba8ab60` also moves Agent dispatch/cancellation outbox repository, delivery and worker lifecycle ownership into `AgentDispatchModule`. `LegacyRoutesRuntime` receives the feature-owned instances only to preserve raw composition shutdown wiring and does not start them; explicit-null composition options prevent duplicate production workers. AG-UI projector, scheduled-task/agent workers and project-scope release worker remain the next lifecycle slices.

BFF child `ba8ab60` moves AG-UI projector construction and lifecycle into `AguiModule`, reusing its canonical projection/consumer providers and Agent source reader. `LegacyRoutesRuntime` receives the feature-owned projector only for raw composition shutdown and does not start it; explicit-null composition options keep raw/test fallback separate from production ownership. Scheduled/project-scope worker lifecycle remains transitional.

BFF child `ba8ab60` moves scheduled-task outbox repository, Scheduler delivery and worker lifecycle into `ScheduledTasksModule`. `LegacyRoutesRuntime` receives the feature-owned instance only as a raw shutdown seam and does not start it; explicit-null composition options avoid a second production worker. Scheduled Agent dispatch/terminal and project-scope release lifecycle remain transitional.

BFF child `ba8ab60` moves project-scope release outbox repository, Storage release client and worker lifecycle into `ProjectsModule`. The storage-disabled branch remains explicit (`null` worker), and the raw runtime receives only the feature-owned instance for shutdown compatibility. Scheduled Agent dispatch/terminal lifecycle and remaining global composition are still transitional.

BFF child `ba8ab60` moves scheduled Agent dispatch/terminal repository, Agent delivery/source adapters and lifecycle into `ScheduledTasksModule`. The feature owns the Agent-enabled/upstream guard, worker identities, bounded concurrency/retry and stop ordering; raw composition receives explicit instances only for shutdown compatibility. No generic worker abstraction or second repository owner was added.

BFF child `ba8ab60` extends `ChatModule` business-read ownership to project-scoped Chat collection/session/message/parts/process reads. The route consumes the shared `PROJECT_SERVICE` owner and adds no Project repository/service or duplicate authorization path; LegacyRoutes now bypasses the project-scoped read family as well as direct reads.

BFF child `ba8ab60` moves the Scheduler callback route into `ScheduledTasksModule`, sharing the feature-owned scheduled-task service, Scheduler receipt repository and scheduled-Agent dispatch repository. The raw runtime keeps only compatibility composition; no second receipt or task repository is introduced.

BFF child `ba8ab60` extends the same feature seam to scheduled-task create/update/delete/retry and project-scoped create mutations. Read, mutation and Scheduler callback paths now share one `PostgresScheduledTaskRepository`/`ScheduledTaskService` owner plus one persistent idempotency boundary; legacy live-bff remains only as raw compatibility.

A-01/A-02/A-07 继续停写。


## 2026-11-01 aggregate runtime fallback closure

BFF child `62fe701` removes `BffBusinessStore.services` from the application port and removes all `businessStore.services.*` reads from `bootstrap/runtime.ts` and `bootstrap/server.ts`. The runtime now consumes explicit owner services from named composition seams. Project skill-selection, Project MCP recommendations, Skill share lookup and message regeneration no longer accept a global store aggregate as their production provider. `PostgresBffRepositories.services` remains a compatibility view for existing integration fixtures only; it is the next deletion target after those fixtures are migrated.

Verification: build/typecheck, BFF architecture 34/34, Nest runtime/feature architecture 23/23, Project MCP recommendation HTTP 8/8.


## 2026-11-01 aggregate class deletion

BFF child `6f9a9e2` deletes `src/application/services.ts` and constructs each named application service exactly once in `PostgresBffRepositories`. The `services` property is now a typed fixture-only compatibility view; no source runtime/bootstrap/route code reads it. Personal Knowledge, AI Skill import and Message regeneration no longer expose aggregate fallback contracts.

The compatibility view remains an integration-fixture migration target; C-3 is not closed until its consumers are zero and each remaining Port has keep/move/delete evidence.


## 2026-11-01 Artifact Library port isolation

BFF child `5de502c` moves the artifact library contract to `src/application/ports/artifact-library-repository.ts`; `bff-business-store.ts` now only carries the transitional runtime store and no artifact DTO/port definitions. Account/Library/Storage/PostgreSQL consumers use the feature-local port with the existing bounded artifact query and verified transfer behavior.


### 2026-11-01 bootstrap-only runtime store seam

BFF child `95d6516` 删除全局 `BffBusinessStore` application Port；runtime 内部 `BffRuntimeStore` 只承担 Idempotency 与 ready/close 生命周期，feature resources 仍以明确 provider 字段跨 raw composition 边界。该切片没有新增抽象层或第二 owner；`PostgresBffRepositories` 继续作为 PostgreSQL composition/集成 fixture owner，待后续 lifecycle/fixture census 决定是否拆分。

### 2026-11-01 App native login consumer cutover

App child `bc1f5c4b`/`15720322` 已将新的 `/login` 与 `/app` SSR admission 绑定 IAM native session：首方登录只传递 allowlisted `return_to`，IAM 邮箱登录成功后发行 native cookie；App shell 不再把 Product Session Redis 作为 SSR 准入 fallback。该切片不删除 OAuth relay、Auth.js RP、Product Session 或其测试 fixture；这些旧入口仍是 C-1.3 后续清理目标，不能以本片标记全量 auth cleanup。
