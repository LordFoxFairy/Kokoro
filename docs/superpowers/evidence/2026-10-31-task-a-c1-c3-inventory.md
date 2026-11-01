# Task A C-1.3～C-3 只读 Inventory（2026-10-31）

## 1. 基线与证据范围

- Root：`d9329c9e`；当前工作树 clean。
- BFF：`apps/kokoro-bff` `3961450`（在既有 feature cutover 基础上，将 direct Chat collection/session/message reads 与无 `project_ref` 的 Chat title/delete/share mutations 下沉到 ChatModule，并让 LegacyRoutesMiddleware 绕过已迁移的 Chat path；此前将 exact Skill download 的 source construction、POST native middleware 与 GET opaque-handle middleware 下沉到 SkillsModule/ProjectsModule，将 `/v1/mori/**` 的 admission、幂等、owner projection/stream 迁入 MusicModule，并将 Message regeneration/ChatTurn service 下沉到 ChatModule/AgentDispatchModule；从旧 dispatcher 删除三类 Skill download/Mori 分支并移除退休 Mori routing helper；个人、managed、share、project installation、scheduled current-read、Chat/ChatTurn、Project service、Project skill-selection、Project MCP recommendation、Skill specification 与 exact-download providers 均保留精确 owner/revision recheck）。
- IAM：`apps/kokoro-iam` `2fbb96a0`。
- App：`apps/kokoro-app` `4da1c1b2`。
- Agent：`apps/kokoro-agent` `c761fad3`。
- 本文只读检查 `apps/kokoro-bff/src`、BFF tests、既有 Task A 设计/盘点；不改变业务代码、contract、Schema、lockfile 或运行配置。

目标是把“LegacyRoutes 当前处理的事实”“global composition 当前暴露的事实”“Port 当前的真实边界”冻结成后续切片的删除门。表中的“目标 owner”是已批准设计中的候选归属，不表示已经完成迁移。

## 2. LegacyRoutes 运行事实

当前入口链：

```text
Nest AppModule
  -> LegacyRoutesModule
  -> LegacyRoutesMiddleware (all routes except healthz/readyz)
  -> LegacyRoutesRuntime
  -> createBffComposition(config, { sessionAdmission })
  -> handleBffRequest(request, response, config, composition)
```

证据：

- `apps/kokoro-bff/src/app.module.ts` 导入 `LegacyRoutesModule`。
- `apps/kokoro-bff/src/modules/legacy-routes/legacy-routes.module.ts` 将 middleware 挂到 `*` 全路径。
- `apps/kokoro-bff/src/modules/legacy-routes/legacy-routes.runtime.ts` 构造全局 composition 并启动全部 worker。
- `apps/kokoro-bff/src/modules/legacy-routes/legacy-routes.middleware.ts` 将所有请求交给 runtime。
- `apps/kokoro-bff/src/common/lifecycle/graceful-shutdown.ts` 仍通过 `LegacyRoutesRuntime.close()` 关闭 worker/store。
- `apps/kokoro-bff/src/bootstrap/server.ts` 仍同时导出 `handleBffRequest` 和独立 `createBffServer`。

因此当前 Nest 仍承载旧 dispatcher 的未迁移路径；已迁移 Chat path 由 `LegacyRoutesMiddleware` 明确绕过，但不能通过该 bypass 或增加 module 壳宣称 LegacyRoutes 已删除。

## 3. Route census（当前 handler → 目标 feature）

### 3.1 非版本化、内部和横切入口

| 当前 path/method | 当前 handler | 目标 owner | 依赖/保留不变量 | 状态 |
|---|---|---|---|---|
| `GET /healthz` | `HealthController` 与旧 `handleBffRequest` 均有分支 | `HealthModule` | readiness/liveness、bounded shutdown | Controller 已存在；旧分支待删除 |
| `GET /readyz` | `HealthController` 与旧 dispatcher | `HealthModule` | DB/Redis/IAM readiness、503 语义 | Controller 已存在；旧分支待删除 |
| `/iam/**` | `iamProtocolRelay` | `IamRelayModule` | 原生协议 wire、Cookie/Origin/错误闭集 | module 只有 relay service；route 仍旧 dispatcher |
| `GET /v1/shared/{shareId}` | `handleBffRequest` 内 public-share projection | `AccountModule`/`ChatModule` | 公开分享权限与 snapshot projection | ChatModule provider 已接入；旧入口仍待删除 |
| `POST /internal/v1/model-admissions/**` | `agentModelAdmissionRoute` | `AgentRunsModule` + Billing/System owner clients | model admission、service auth、预算 | 未迁移 |
| `POST /internal/v1/project-execution-bindings/verify` | `projectExecutionBindingRoute` | `AgentRunsModule`/`ProjectsModule` | execution binding、identity assertion、项目资格 | 未迁移 |
| `POST /internal/v1/bff/scheduled-tasks/dispatch` | `schedulerDispatch` | `ScheduledTasksModule` | Scheduler callback、receipt claim/CAS、lease | 未迁移 |
| `GET /v1/system/runtime-manifest` | `runtimeManifest` | `SystemModule` | owner manifest、版本/错误映射 | 未迁移 |

### 3.2 Account / session / preferences

| 当前 path/method | 当前 handler | 目标 owner | 依赖/保留不变量 | 状态 |
|---|---|---|---|---|
| `PATCH /v1/account/profile` | `accountProfileRoute`（dispatcher 前置分支） | `AccountModule` | IAM profile owner、native admission、snake_case contract | 未迁移 |
| `GET /v1/account/archived-tasks` | `archivedTasksRoute` | `AccountModule` + Chat reader | archived cursor、权限、owner query | 未迁移 |
| `GET /v1/account/shared-tasks` | `sharedTasksRoute` | `AccountModule` + Chat reader | shared cursor、分享边界 | 未迁移 |
| `GET /v1/sessions/{id}/archive` | `archivedTasksRoute` | `AccountModule`/Chat archive provider | archive state、tenant/subject binding | 未迁移 |
| `POST /v1/sessions/{id}/archive|restore` | `archivedTasksRoute` | `AccountModule`/Chat archive provider | idempotency、状态转换、迟到请求 | 未迁移 |
| `GET /v1/me` | dispatcher inline branch | `AccountModule` | admitted subject/tenant/platform admin；body/query rejection | 未迁移 |
| `GET /v1/account/sessions` | `accountSessionsRoute` | `AccountModule` | IAM session list、撤权语义、native cookie | 未迁移 |
| `DELETE /v1/account/sessions/{id}` | `accountSessionsRoute` | `AccountModule` | 当前 session 撤销、迟到请求 401 | 未迁移 |
| `GET/POST/... /v1/team/**` | `liveTeamRead`/`liveTeamWrite` | Task B/Account boundary | 团队 owner、权限和外部 contract；本 Goal 只迁 adapter | 冻结不扩展 |
| `GET/PUT/... /v1/preferences/personalization` | `personalizationRoute` | `AccountModule` | read/replace、revision/transaction | provider 已局部 feature-local；route 未迁移 |
| `GET/POST/PATCH/DELETE /v1/preferences/knowledge[/**]` | `personalKnowledgeRoute` | `AccountModule` | revision、limit、usage、删除 tombstone | 未迁移 |
| `POST /v1/sessions/{id}/move` | `moveSessionRoute` | `ChatModule`/ProjectsModule | project scope、idempotency、移动回读 | 未迁移 |

### 3.3 Chat / AgentRuns / AG-UI

| 当前 path/method | 当前 handler | 目标 owner | 依赖/保留不变量 | 状态 |
|---|---|---|---|---|
| `GET/POST/... /v1/sessions/**` | `liveChatBusiness`、`liveAgentSession`、`liveOwnerBusiness` | `ChatModule` + `AgentRunsModule` + `AguiModule` | message parts、idempotent chat turn、dispatch outbox、AG-UI cursor/replay | direct GET collection/session/messages/parts/process 与无 `project_ref` title/delete/share 已由 ChatModule 接管；POST/events/project-scoped 与 Agent/AG-UI 仍待迁移 |
| `GET /v1/sessions/{id}/runs/{runId}/display` | `runDisplayRoute` | `AgentRunsModule` | canonical RunDisplay、owner identity、5s admission budget | 未迁移 |
| `POST /v1/sessions/{id}/messages/{id}/feedback` | `messageFeedbackRoute` | `ChatModule` | feedback state、CAS/permission | 未迁移 |
| `POST /v1/sessions/{id}/messages/{id}/regenerate` | `messageRegenerationRoute` | `ChatModule` + AgentRunsModule | source fingerprint、dispatch receipt、late result | 未迁移 |
| `GET/POST/... /v1/sessions/{id}/messages/**` | `liveChatBusiness` + `chat-authorization` | `ChatModule` | project/session binding、idempotency、message ordering | direct GET list/parts 已接入 ChatModule；POST/feedback/regeneration 与 project scope 仍待迁移 |
| `GET /v1/sessions/{id}/process` 与 replay/SSE 相关路径 | `liveAgentSession` + `AgUiSessionRuntime` | `AguiModule` + AgentRunsModule | durable ledger、cursor、replay、cancel/drain | 未迁移 |
| `GET /v1/sessions/{id}/artifacts` 等 | `liveChatBusiness`/artifact readers | `ChatModule` + Storage client | artifact association、权限、分页 | 未迁移 |

`/v1/sessions/**` 不能按一条 generic route 机械搬迁；必须按 Chat facts、Run control/display、AG-UI durable projection 三条 owner seam 拆分。

### 3.4 Projects / resources / project execution

| 当前 path/method | 当前 handler | 目标 owner | 依赖/保留不变量 | 状态 |
|---|---|---|---|---|
| `GET/POST/... /v1/projects/**` | `liveBffBusiness` 与专用 route | `ProjectsModule` | project owner scope、CAS、idempotency | 未迁移 |
| `GET /v1/self/project-pins` | `handleProjectPinRequest` (`project-native.ts`) | `ProjectsModule` | cursor、pin state、权限 | 已迁移（既有 pin cutover） |
| `PUT/DELETE /v1/projects/{id}/pin` | `handleProjectPinRequest` (`project-native.ts`) | `ProjectsModule` | CAS、project owner | 已迁移（既有 pin cutover） |
| `GET /v1/projects/{id}/mcp-recommendations` | `handleProjectMcpRecommendationsRequest` → `McpModule` | `McpModule` + Projects provider | recommendation snapshot、MCP read admission | 已迁移（`9310aa6`） |
| `PUT/POST /v1/projects/{id}/mcp-recommendations` | `handleProjectMcpRecommendationsRequest` → `McpModule` | `McpModule` + Projects provider | expected state version、precondition failure | 已迁移（`9310aa6`） |
| `PATCH /v1/projects/{id}/name` | `handleProjectRenameRequest` (`project-native.ts`) | `ProjectsModule` | rename receipt、conflict | 已迁移（`1db4e51`） |
| `DELETE /v1/projects/{id}` | `handleProjectDeleteRequest` (`project-native.ts`) | `ProjectsModule` + scope-release outbox | logical release、physical cleanup、恢复 | 已迁移（`1817bd9`） |
| `GET /v1/projects/{id}/deletion` | `handleProjectDeletionStatusRequest` (`project-native.ts`) | `ProjectsModule` | deletion state projection | 已迁移（`7afbaff`） |
| `GET /v1/projects/{id}/resources` | `handleProjectResourceListRequest` (`project-native.ts`) | `ProjectsModule` + Storage client | project scope、分页 | 已迁移（`52eeff7`） |
| `POST /v1/projects/{id}/resources` | `projectResourceRoute` | `ProjectsModule` + Storage client | upload/idempotency/scan state | 未迁移 |
| `GET /v1/projects/{id}/resources/{resourceId}` | `handleProjectResourceReadRequest` (`project-native.ts`) | `ProjectsModule` + Storage client | read qualification、scope | 已迁移（`525a150`） |
| `GET /v1/projects/{id}/resources/{resourceId}/download` | `handleProjectResourceReadRequest` (`project-native.ts`) | `ProjectsModule` + Storage client | exact bytes、expiry | 已迁移（`525a150`） |
| `DELETE /v1/projects/{id}/resources/{resourceId}` | `handleProjectResourceDeleteRequest` (`project-native.ts`) | `ProjectsModule` + Storage client | deletion/outbox/recovery | 已迁移（`14aa232`） |
| `PUT/POST /v1/projects/{id}/skill-selection` | `handleProjectSkillSelectionRequest` → `ProjectPinMiddleware` | `ProjectsModule` + Skills client | project access、installation IDs、CAS | 已迁移（`2dd93ca`） |
| `/v1/projects/{id}/skill-installations/**` | `handleProjectSkillInstallationRequest` → `ProjectPinMiddleware` | `ProjectsModule` + Skills authorization/client | project access、owner qualification、package route exclusion | 已迁移（`d9a8a24`） |
| `GET /v1/projects/{id}/tasks` | `liveBffBusiness`/project repository | `ProjectsModule` ProjectTask provider | A-07 canonical ProjectTask contract | A-07 停写 |

### 3.5 ScheduledTasks

| 当前 path/method | 当前 handler | 目标 owner | 依赖/保留不变量 | 状态 |
|---|---|---|---|---|
| `GET /v1/scheduled-tasks` | `scheduledTaskReadRoute` | `ScheduledTasksModule` | task snapshot、Scheduler state、project availability | 未迁移 |
| `GET /v1/scheduled-tasks/{id}` | `scheduledTaskReadRoute` | `ScheduledTasksModule` | scope/permission/read consistency | 未迁移 |
| `POST /v1/scheduled-tasks` | `liveBffBusiness` + `scheduledCreateInput` | `ScheduledTasksModule` | task fact + Scheduler outbox 同事务、idempotency | 未迁移 |
| `PATCH /v1/scheduled-tasks/{id}` | `liveBffBusiness` | `ScheduledTasksModule` | CAS、outbox、timezone/DST | 未迁移 |
| `DELETE /v1/scheduled-tasks/{id}` | `liveBffBusiness` | `ScheduledTasksModule` | terminal/disable、outbox | 未迁移 |
| `POST /internal/v1/bff/scheduled-tasks/dispatch` | `schedulerDispatch` | `ScheduledTasksModule` | callback receipt、lease、Agent dispatch | 未迁移 |

### 3.6 Skills / MCP / System / Billing / Music / Storage

| 当前 path family | 当前 handler | 目标 owner | 处理边界 | 状态 |
|---|---|---|---|---|
| `/v1/skills/**`, `/v1/self/skills/**`, `/v1/skill-installations/**` | `skill*Route`、platform clients、`SkillsModule`/`ProjectsModule` middleware | `SkillsModule`/`ProjectsModule` | 仅迁移 BFF adapter；不改 Task B 能力语义、第三方 OAuth 或 owner contract | App skill-bindings、skill specification reads、全部 Skill package inspection、personal skill-installations、managed reads、Skill enable command、Skill usage、personal Skill lifecycle、Skill draft creation/mutations、Skill catalog commands/read/cover、published package read、Skill admin、GitHub preview、local import、exact Skill download POST 已迁移；GET opaque handle 与 raw compatibility fallback 仍待清理 |
| `/browser/v1/mcp/**` | `mcpPersonalRoute`、`customApiRoute` | `McpModule` | MCP budget、OAuth/connection、custom API contract | 冻结不扩展 |
| `/v1/mcp/**`, project publication/recommendations | `McpProjectPublicationMiddleware`、`McpAdminMiddleware`、`ProjectMcpRecommendationsMiddleware` | `McpModule` | owner client、权限、request budget | connector list、provider/package admin、project publication、recommendations 已迁移；personal MCP 执行保持冻结 |
| `/v1/system/runtime-manifest`, `/v1/models/**`, `/v1/admin/model-*/**` | `runtimeManifest`、`liveOwnerBusiness`、model admin routes | `SystemModule` | runtime/model owner client、admin auth | 未迁移 |
| `/v1/admin/billing/**`, `/v1/billing/**` | `liveAdminMetering`、`liveAdminCreditGrant`、`liveOwnerBusiness` | `BillingModule` | billing owner、metering/settlement、admin qualification | 未迁移 |
| `/v1/mori/**` | `handleMoriRequest` → `MusicMiddleware` → `liveMoriBusiness` | `MusicModule` | Mori owner client、upstream mapping、admission、幂等、SSE projection | 已迁移；raw createBffServer 保留同一 native adapter，旧 dispatcher 分支已删除 |
| `/v1/library/**`、artifact/file upload/download | `library*Route`、`personalFile*Route`、`liveOwnerBusiness` | `ProjectsModule` + `StorageClientModule`（当前缺失） | exact bytes、scan/expiry、scope/permission | 未迁移 |
| 未命中特殊 route 的 owner path | `liveOwnerBusiness` → `proxyUpstream` | 对应 owner client module | 不得继续作为任意 proxy 垃圾桶；需按 owner inventory 收敛 | 未迁移 |

## 4. 当前 Feature Module 状态

| Module | 当前实现 | 实际问题 | 下一步删除门 |
|---|---|---|---|
| `AccountModule` | Database/IAM relay、Personalization provider、SessionAdmission provider | 仅有两个 provider，account route 仍在旧 dispatcher | profile/session/archive/share/knowledge route 至少有真实 Controller/provider 后再移除旧入口 |
| `ProjectsModule` | `PROJECT_SERVICE`、project resource provider、skill-selection provider/client、`ProjectPinMiddleware` | 仍有 project installation/MCP/task/mutation bundles 在旧 dispatcher | 完成剩余 project bundles 后删除旧 project fallback |
| `ChatModule` | `CHAT_SERVICE`、`CHAT_TURN_SERVICE`、`PUBLIC_SHARE_SERVICE`、native archive/share/feedback/regeneration/move 与 direct Chat read middleware | Chat POST/events/project scope、Agent/AG-UI 仍由旧 dispatcher 组合 | 继续拆 Chat/Run/AG-UI provider，逐 bundle 删除旧分支 |
| `AgentRunsModule` | 仅声明 IAM/Database imports | 未承接 Agent client、run display/control、outbox | run display/control/dispatch seam + cancellation/replay tests |
| `AguiModule` | 仅声明 Chat/Redis/Database imports | 未承接 projector/ledger/replay provider | durable ledger/cursor/replay Controller/provider + tests |
| `ScheduledTasksModule` | `SCHEDULED_TASK_READ_SERVICE`、current-read middleware、Projects/AgentRuns/Database imports | mutation/callback/outbox 仍在旧 dispatcher；raw composition 仍需逐步清 fallback | read/mutation/callback/outbox slice + tests |
| `SkillsModule`/`BillingModule`/`SystemModule`/`MusicModule` | SkillsModule 已拥有 App binding、specification、installation、catalog、admin、import、share 与 lifecycle providers；其余模块主要是 imports 声明 | Billing/System/Music 仍需按 route bundle 补齐真实 owner seam | 逐 route bundle 承接真实 client/use case；否则保持 inventory 状态 |
| `McpModule` | `PROJECT_MCP_RECOMMENDATIONS_PROVIDER`、MCP authorization、personal/connector/admin/publication clients、对应 middleware | personal MCP execution 与少量旧 owner projection 仍在旧 dispatcher | 继续按 route bundle 下沉并补 client lifecycle |
| `LegacyRoutesModule` | all-route middleware + global runtime | 当前唯一实际业务入口 | route census 清零后删除 module/runtime/middleware |

## 5. Global composition / consumer census

| 对象 | 当前生产位置 | 只读消费者证据 | 目标处置 |
|---|---|---:|---|
| `BffBusinessStore` | `bootstrap/runtime.ts` 构造并传入 `server.ts` | 27 个文件（既有盘点复核） | 删除 locator；按 feature 导出窄 provider |
| `BffApplicationServices` | `PostgresBffRepositories.services` | 5 个文件（既有盘点复核） | 删除聚合器；Service 直接由 feature module 注入 |
| `PostgresBffRepositories` | `createBffComposition()` | 14 个文件生产/测试引用（含集成测试） | 先拆 provider；测试改为 feature seam；最后删除 wrapper |
| `handleBffRequest` | `legacy-routes.runtime.ts`、`createBffServer()` | source + architecture tests | route census 清零后删除业务 dispatcher；保留必要 bootstrap 生命周期实现 |
| `createBffComposition` | `LegacyRoutesRuntime`、`createBffServer`、测试 | source + focused tests | Nest AppModule provider graph 成为唯一 production composition；测试按 feature 注入 |
| `GracefulShutdown` | 注入 `LegacyRoutesRuntime` | lifecycle provider | 迁移 worker/store close 到 owner module 后删除 LegacyRoutes 依赖 |

## 6. Port disposition（当前文件系统闭集）

当前 `apps/kokoro-bff/src/application/ports/` 实际有 **21** 个文件。既有盘点中的“23 个 Port”与当前 checkout 不一致：`personalization-repository.ts` 已迁到 `modules/account/personalization.provider.ts`，`scheduled-task-state-reader.ts` 当前位于 `modules/scheduled-tasks/`，不再属于该目录；这项文档漂移已记录，不把旧数量当作完成证据。

| 当前 Port | 真实边界初判 | 目标 owner | 处置 |
|---|---|---|---|
| `agent-cancellation-delivery.ts` | Agent cancel 外部传输 | `AgentRunsModule` | 保留，迁 feature-local |
| `agent-cancellation-outbox-repository.ts` | durable compensation queue、lease/CAS | `AgentRunsModule`/Chat | 保留，迁 feature-local |
| `agent-dispatch-delivery.ts` | Agent dispatch 外部传输 | `AgentRunsModule` | 保留，迁 feature-local |
| `agent-dispatch-outbox-repository.ts` | Chat turn atomic commit + outbox + receipt | `ChatModule`/`AgentRunsModule` | 保留真实边界，拆消费接口 |
| `bff-business-store.ts` | global locator，聚合 services/outbox/readers | 各 feature exports | 删除；先完成 provider graph |
| `chat-repository.ts` | 171 行跨 Chat/Run/Archive/Share/Feedback | `ChatModule`/`AgentRunsModule`/`AccountModule` | 拆分旧 interface，不删除底层复杂查询 |
| `idempotency-repository.ts` | receipt claim/CAS/release | cross-cutting named provider + feature | 保留真实边界，移出 global store |
| `personal-knowledge-repository.ts` | revision/limit/usage/tombstone | `AccountModule` | 保留，迁 feature-local |
| `project-execution-binding-reader.ts` | admitted execution binding read | `AgentRunsModule`/`ProjectsModule` | 并入具名 provider，删除全局 Port |
| `project-repository.ts` | project CRUD/pin/recommendation/skill/task 混合 | `ProjectsModule` | 拆分 feature readers/writers |
| `project-scope-release-outbox.ts` | project/conversation scope release queue | `ProjectsModule` + Storage | 保留，迁 feature-local |
| `public-share-repository.ts` | public/private permission boundary | `AccountModule`/`ChatModule` | 保留，迁 feature-local |
| `scheduled-agent-dispatch-delivery.ts` | Scheduler→Agent delivery | `ScheduledTasksModule` | 保留，迁 feature-local |
| `scheduled-agent-dispatch-repository.ts` | terminal-gated dispatch/consumer lease | `ScheduledTasksModule` | 保留，迁 feature-local |
| `scheduled-task-outbox-delivery.ts` | Scheduler command attempt | `ScheduledTasksModule` | 保留，迁 feature-local |
| `scheduled-task-outbox-repository.ts` | Scheduler outbox claim/retry/fence | `ScheduledTasksModule` | 保留，迁 feature-local |
| `scheduled-task-repository.ts` | scheduled facts + callback + mutation/outbox | `ScheduledTasksModule` | 拆 read/mutation/callback，不保留万能接口 |
| `scheduler-dispatch-receipt-repository.ts` | callback receipt claim/complete | `ScheduledTasksModule` | 保留，迁 feature-local |
| `skill-share-repository.ts` | skill share ACL/lifecycle | `SkillsModule` | 保留，迁 feature-local |
| `stable-id-generator.ts` | deterministic ID helper | owning feature | 并入具名 provider/function；删除独立全局 Port |
| `submitted-agent-run-reader.ts` | immutable submission admission read | `AgentRunsModule` | 并入具名 provider；删除全局 Port |

删除底层 PostgreSQL 文件的前置条件：目标 provider 编译通过、旧 Port 生产 import 为零、原有 contract/integration 行为已迁移、事务/锁/幂等/取消/replay 证据不丢失。

## 7. 第一条实现切片与停止线

第一条切片选择 **Account profile + account sessions**，原因是：

1. `AccountModule` 已有 `SESSION_ADMISSION` 和 Personalization provider，依赖面小于 Chat/AG-UI；
2. 能直接证明 native-session context 到 Controller 的边界；
3. 迁移完成后可从 `LegacyRoutesRuntime` 删除明确的 profile/session paths；
4. 不触碰 A-01/A-02/A-07 业务行为。

切片准入条件：

- 先补 route-level red contract/architecture test；
- 明确 `Controller → AccountService/use case → IAM client/feature provider`；
- 保留 Cookie/Origin、tenant/subject、撤权、错误闭集、request-id 和取消预算；
- 从旧 dispatcher 删除 profile/session 具体 path；
- focused gates 与停写后串行 BFF gates 通过后，才进入下一 bundle。

当前状态：inventory 已冻结；业务实现仍停写在下一切片准入前。 

## 8. 盘点后的已验证增量（2026-10-31）

本文件第 3～7 节保留最初 route/provider census；以下是其后的实际状态，不覆盖未迁移项：

- BFF `5659b1d` 已将 Health、IAM relay、`GET /v1/me`、`GET /v1/projects` 集合/详情/instruction-revisions/deletion-status、rename/delete/resource-list/resource-read/resource-download/resource-upload/resource-delete、project skill-selection、project MCP recommendations、`GET /v1/connector.list`、MCP provider/package admin 与 browser project publication routes、App skill-bindings、Skill specification reads、全部 Skill package inspection、project/personal skill-installations、managed personal Skill reads、Skill enable command、Skill usage、personal skill lifecycle、skill draft creation/mutations、Skill catalog commands/read/cover、published package read、Skill admin、GitHub preview、local import、public share projection、exact Skill download POST/GET opaque-handle、`/v1/mori/**` admission/幂等/owner projection source/middleware、direct Chat reads 迁入 feature middleware/provider，并从旧 dispatcher 删除三类已迁移分支；同时将 Chat direct reads 与 Chat/ChatTurn feature providers 接入 runtime、Chat authorization、live Chat、regeneration 与 run-display raw adapter；Chat/ChatTurn 已不再挂在 `BffBusinessStore` 字段上，保留 test-only shared reader fallback。旧 dispatcher 对应分支与 project deletion-status/rename/delete/resource-list/resource-read/resource-upload/resource-delete/skill-selection/MCP recommendations/connector.list/MCP admin/project-publication/App skill-bindings/skill-specification/managed-skill-package-inspection/personal-skill-package-inspection/project-skill-package-inspection/project/personal skill-installations/managed reads/enable/usage/personal lifecycle/skill draft creation/mutations/catalog command/read/cover/published package/admin/GitHub preview/local import/Mori source routes 已删除。
- `BffBusinessStore` 与 `PostgresBffRepositories` 的重复 `projectService`、`chatService`、`chatTurnService` 字段均已删除；runtime/feature consumers 统一读取具名 feature composition 或 `BffApplicationServices.services` 兼容聚合。`personalizationProvider` 与 global `services` 仍属于待迁移边界。
- Root pin：Root `81dd982d`、App `9cde5640`、BFF `5659b1d`、IAM `e1f537b02cb326cfb3751316b1591fa82313f70a`。
- 最新 BFF focused 串行验证：`pnpm build`、`pnpm lint`、`pnpm typecheck`、Nest architecture 18/18、BFF architecture 34/34、direct Chat read 2/2、Chat/ChatTurn/run-display focused 212/212、exact-download HTTP/policy/unit 22/22、BFF mock contract 25/25、connector-list HTTP 5/5、MCP provider/package admin HTTP 12/12、MCP project publication HTTP 27/27、App skill-bindings/Open App management 12/12、Skill specification contract/focused 149/149、package inspection unit 47/47（4 个环境 skip）；停写后最新 `pnpm test` 为 2316 tests / 2299 pass / 15 fail / 2 skip，失败集中在既有 Artifact/Personal Storage Product HTTP、Project exact-download、Admin Web credential fixture 与 anonymous Share fixture，不作为 C-4 通过。
- 仍未完成：LegacyRoutes 全量退出、`createBffComposition`/`PostgresBffRepositories` 生产移除、Chat POST/events/project scope、AgentRuns/AG-UI/剩余 ScheduledTask aggregate consumers/remaining Skills/MCP route bundles、剩余 Port 逐项迁移、C-4 Root/子仓最终串行门禁。

