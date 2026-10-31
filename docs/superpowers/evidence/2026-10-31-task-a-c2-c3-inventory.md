# Task A C-2/C-3 路由与边界盘点（2026-10-31）

## 1. 盘点目的与冻结结论

本文件是进入 C-2/C-3 实现前的 route/owner/provider inventory。盘点范围覆盖真实生产入口：

- `apps/kokoro-bff/src/main.ts`、`src/app.module.ts`、`src/common/lifecycle/graceful-shutdown.ts`
- `src/modules/legacy-routes/*`
- `src/bootstrap/server.ts`、`src/bootstrap/runtime.ts`
- `src/http/routes/**`
- `src/application/ports/**`、`src/application/services.ts`、`src/infrastructure/postgres/repositories.ts`

冻结结论：`LegacyRoutesRuntime` 只是 Nest middleware 包装器，业务分派事实在 `src/bootstrap/server.ts`；因此 C-2 的迁移写区必须同时包含 `server.ts`、`runtime.ts`、`app.module.ts`、`main.ts`、shutdown provider 与对应测试/脚本，不能只修改 `legacy-routes.runtime.ts`。在所有 route bundle 尚未切换前，不删除旧 dispatcher 或 global composition。

当前代码/组合基线：Root `18b59a43`（文档同步提交），BFF `2df4bcc`（先前 `caccdc9`、`a677cd2`、`6874034`、`ef1c53b`、`6de89c7`、`108a0bc`、`4667506`、`96806f4`、`39d5481`、`7f61218`、`2a504c0`）。Account/System/Chat/Projects/Scheduled/Agent route bundles 已切换；personalization、Chat archive/share/feedback、Project pin、ScheduledTask read、AgentRuns reader 与 run-display provider seam 已脱离旧 dispatcher，本文件继续记录剩余 route/边界盘点。

## 2. 生产入口与运行时依赖

| 入口/文件 | 当前职责 | 目标状态 | 删除门 |
|---|---|---|---|
| `src/main.ts` | `NestFactory.create(AppModule, { bodyParser: false })`，启动 HTTP listener | 唯一 Nest listener；保留 | 所有 route 已由 Nest controller/adapter 接管且 listener smoke 通过 |
| `src/app.module.ts` | 注册 feature modules + `LegacyRoutesModule` + `GracefulShutdown` | 注册真实 feature controller/provider；移除 `LegacyRoutesModule` | `LegacyRoutes*` 反向 import 为零 |
| `src/modules/legacy-routes/legacy-routes.middleware.ts` | 捕获所有请求并委派 runtime；异常时写 500/销毁响应 | 删除 | route census 清零 |
| `src/modules/legacy-routes/legacy-routes.runtime.ts` | 创建 `BffServerComposition`、启动/停止 worker、调用 `handleBffRequest` | 删除；worker/close 由 feature/runtime provider 承接 | 唯一 composition root 与 shutdown graph 已验证 |
| `src/common/lifecycle/graceful-shutdown.ts` | 依赖 `LegacyRoutesRuntime.close()` | 改为依赖明确的 worker/store lifecycle owner | Legacy runtime import 为零 |
| `src/bootstrap/server.ts` | 当前完整 HTTP admission、路由分派、owner proxy、generic fallback | 按 bundle 拆为 feature controller/adapter；最终仅保留测试/独立 server factory（若仍有真实消费者） | `handleBffRequest`/`createBffServer` 生产引用为零或有明确保留证据 |
| `src/bootstrap/runtime.ts` | 当前全部 client、store、worker 的 global composition | 按 feature provider graph 拆分；最终删除 global locator 部分 | `createBffComposition` 与 global wrapper import census 为零 |

## 3. Legacy dispatcher route census

`handleBffRequest()` 的 route facts 以“方法 + path family → 当前 handler → 目标 owner/feature → 迁移门”记录。路径 family 是为避免把同一条业务事实机械拆成重复 Controller；实现时仍须为每个公开方法保留原 contract/error/cancel/idempotency 证据。

| Route family（method/path） | 当前 handler/依赖 | 目标 feature owner | 迁移状态/最小证据 |
|---|---|---|---|
| `ALL /iam/**` | `iamProtocolRelay` | IAM relay module / owner transport | 保留独立协议边界；先完成 native owner/profile read contract，再移出通用 dispatcher |
| `GET/PATCH /v1/account/profile` | AccountModule `AccountMiddleware` → `accountProfileRoute` → IAM client | AccountModule + IAM owner client | **migrated**; raw `createBffServer` uses same adapter, native transport/final admission preserved |
| `GET /v1/account/archived-tasks`; `GET/POST /v1/sessions/:id/{archive,restore}` | `ChatModule` `ChatMiddleware` → `chat-native` → `archivedTasksRoute`, `CHAT_SERVICE` | Chat/Account | **migrated**; 保留 no-store、re-admission、archive state 错误闭集 |
| `GET /v1/account/shared-tasks` | `ChatModule` `ChatMiddleware` → `chat-native` → `sharedTasksRoute`, `CHAT_SERVICE` | Chat/Account | **migrated**; shared-task projection 与失效响应 focused tests 通过 |
| `POST /internal/v1/model-admissions[/**]` | `AgentRunsModule` `AgentRunsMiddleware` → `agent-runs-native` → `agentModelAdmissionRoute`, `AGENT_RUNS_READER` | AgentRunsModule | **migrated**; dedicated credential, submitted-run reader and Billing admission/settlement boundary preserved |
| `POST /internal/v1/project-execution-bindings/verify` | `AgentRunsModule` `AgentRunsMiddleware` → `agent-runs-native` → `projectExecutionBindingRoute`, `AGENT_RUNS_READER` | AgentRunsModule/Projects | **migrated**; execution-binding owner and dedicated service credential preserved |
| `ALL /v1/app-skill-bindings/**`、platform specification/download/import routes | `appSkillBindingsRoute`, `skillSpecificationReadRoute`, `skillSpecificationEnabledRoute`, `skillDownloadHandleRoute`, `exactSkillDownloadRoute`, `localSkillImportRoute` | SkillsModule / Platform owner clients | preserve package budget, project access, generated Connect contracts |
| `GET /healthz`, `GET /readyz` | inline checks in dispatcher + `HealthModule` | HealthModule | remove duplicate inline checks only after listener smoke confirms Nest controller behavior |
| `GET /v1/shared/:shareId` | inline public share projection or `sharedSessionReader` | Chat/PublicShare feature | preserve server auth, scope/project query validation, public snapshot |
| `ALL /internal/v1/bff/scheduled-tasks/dispatch` | `schedulerDispatch`, store receipt | ScheduledTasksModule | preserve server auth, event receipt CAS and outbox delivery |
| `GET /v1/system/runtime-manifest` | SystemModule `SystemMiddleware` → `runtimeManifest` | SystemModule | **migrated**; service auth, tenant projection, owner normalization and focused BFF tests pass |
| Connector/MCP browser routes | `connectorListRoute`, `mcpPackageAdminRoute`, `mcpProviderAdminRoute`, `mcpPersonalRoute`, `mcpProjectPublicationRoute`, `customApiRoute`, MCP authorization clients | McpModule | keep MCP budget/action checks and owner clients; no generic platform fallback |
| `GET /v1/sessions/:id/runs/:run/display` | `AgentRunsModule` `AgentRunsMiddleware` → `run-display` adapter, `RUN_DISPLAY_PROVIDER` | AgentRuns/Agui | **migrated**; preserve submitted-run binding, Chat owner read, AG-UI transport and final admission |
| `GET/PUT /v1/sessions/:id/messages/:message/feedback` | `ChatModule` `ChatMiddleware` → `message-feedback-native` → `messageFeedbackRoute`, `CHAT_SERVICE` | ChatModule | **migrated**; preserve feedback CAS/read, re-admission and error mapping |
| `POST /v1/sessions/:id/messages/:message/regenerate` | `messageRegenerationRoute` + fresh admission | ChatModule/AgentRuns | preserve idempotency/re-admission/error mapping |
| `GET /v1/self/project-pins`, `PUT /v1/projects/:id/pin` | `ProjectsModule` `ProjectPinMiddleware` → `project-native` → `projectPinRoute`, `PROJECT_SERVICE` | ProjectsModule | **migrated**; preserve project ownership, 10s deadline, natural idempotency and final admission |
| `GET /v1/scheduled-tasks[/:id]` | `ScheduledTasksModule` `ScheduledTaskReadMiddleware` → `scheduled-task-native` → `scheduledTaskReadRoute`, `SCHEDULED_TASK_READ_SERVICE` | ScheduledTasksModule | **migrated**; preserve scheduler timeout, re-admission, snapshot/revalidation and owner current-state binding |
| `POST/GET/DELETE /v1/skill-shares[/:id][/skill]`; skill usage/package/cover/import lifecycle | skill route family + product clients/store skill services | SkillsModule | preserve skill authorization, package budget, owner Connect artifacts |
| `GET/PUT /v1/preferences/personalization` | AccountModule `AccountMiddleware` → `handlePersonalizationRequest` → `PERSONALIZATION_PROVIDER`；raw `createBffServer` 仅保留显式兼容 seam | AccountModule | **migrated**; CAS/cancel/raw body focused and architecture gates passed |
| `GET/POST/PATCH/DELETE /v1/projects/**` | `liveBffBusiness`, project routes, `businessStore.services.projects` | ProjectsModule | split read/mutate/resource/rename/delete/status/pin/selection; preserve transaction/idempotency/owner scope |
| `GET/POST/PATCH/DELETE /v1/scheduled-tasks/**` | `liveBffBusiness`, scheduled routes/service | ScheduledTasksModule | split create/update/delete/retry/read; preserve lineage/idempotency/calendar validation |
| `GET/POST/PATCH/DELETE /v1/sessions/**` | `liveChatBusiness`, `liveAgentSession`, AG-UI/outbox services | ChatModule + AgentRunsModule + AguiModule | preserve durable ledger, cursor/replay, cancellation, outbox lease/drain |
| `GET /v1/me` | AccountModule `AccountMiddleware` → frozen admitted context projection | AccountModule | **migrated**; no owner DB read |
| `GET /v1/account/sessions[/:id]`、`DELETE /v1/account/sessions/:id` | AccountModule `AccountMiddleware` → `accountSessionsRoute`, IAM native owner transport | AccountModule + IAM client | **migrated**; input/CAS/error tests pass |
| `GET/ALL /v1/team/**` | AccountModule `AccountMiddleware` → `liveTeamRead`/`liveTeamWrite`, IAM native owner transport | AccountModule/Team provider | **migrated**; role/permission snapshot and owner error tests pass |
| `GET/POST /v1/admin/**` | billing metering/credit, identity, model config/routing, skill admin | Billing/System/Skills/Account modules | each admin owner keeps explicit permission and deadline; no catch-all admin controller |
| `GET/POST /v1/library/**` | library/artifact/file routes, artifact library provider, Storage owner | Library/Storage feature boundary (or explicit owning module) | keep bounded downloads, project/tenant scope, storage client identity |
| `GET/POST /v1/billing/**` | `liveOwnerBusiness`, billing clients | BillingModule | preserve owner projection/error normalization and idempotency |
| `ALL /v1/mori/**` | `liveMoriBusiness` | MusicModule | preserve owner proxy and idempotency |
| Remaining configured upstream paths | `liveOwnerBusiness` / `proxyUpstream` | explicit owner adapters only | generic fallback is temporary; removed once current contracts have named adapters or fail-closed 404/503 |

**Route removal rule:** each row is considered migrated only when (1) feature controller/adapter handles exact method/path, (2) existing HTTP/error/cancel/idempotency tests pass against that handler, (3) Legacy dispatcher has an explicit negative test or exclusion for the path, and (4) reverse route census shows no second handler.

## 4. Global composition / service locator census

### 4.1 `BffBusinessStore`

Current public fields and observed production consumers:

| Field | Boundary evidence | Candidate action |
|---|---|---|
| `services` | projects, scheduled, chat, chatTurns, publicShares, personalization, skillShares, skillUsage, skillAiAssociation, personalKnowledge | Split by feature; delete aggregate after all consumers move |
| `agUi`, `agUiConsumers` | durable projection ledger/consumer lease | Keep as AguiModule provider; move out of global store |
| `scheduledTaskOutbox`, `scheduledAgentDispatch`, `schedulerDispatchReceipts` | outbox/CAS/lease/event receipt | Keep, move to ScheduledTasks/AgentRuns providers |
| `agentDispatchOutbox`, `agentCancellationOutbox`, `submittedAgentRuns`, `projectExecutionBindings` | durable command/cancellation/admission facts | Keep, move to AgentRuns provider |
| `artifactLibrary`, `projectScopeReleaseOutbox` | artifact/storage scope release boundary | Keep, move to Library/Storage owner provider |
| `idempotency` methods | persistent public receipt/CAS | Keep as explicit Idempotency provider; no aggregate wrapper |
| `ready()/close()` | DB/Redis lifecycle | move to explicit database/lifecycle owner |

### 4.2 `BffApplicationServices`

| Member | Current implementation | Action |
|---|---|---|
| `ProjectService` | project repository façade with project/task/revision/resource methods | move to ProjectsModule service; retain only if it owns a real scope/transaction rule |
| `ScheduledTaskService` | scheduler/task lifecycle and lineage | move to ScheduledTasksModule service |
| `ChatApplicationService` | chat repository façade, cursor/replay/message reads | move to ChatModule service |
| `ChatTurnApplicationService` | durable agent dispatch + stable id | move to Chat/AgentRuns use case; retain outbox/idempotency boundary |
| `PublicShareApplicationService` | public share projection | move to Chat/PublicShare provider |
| `personalization` | feature-local provider；此前暴露在 global aggregate，现已改为 `BffBusinessStore.personalizationProvider` 的 raw-server seam + AccountModule DI | **migrated first C-3 slice**; 删除 aggregate field，保留 CAS/transaction provider，后续删除 raw seam |
| `skillShares`, `skillUsage`, `skillAiAssociation`, `personalKnowledge` | optional feature providers hidden behind aggregate | inject directly in Skills/Account/Chat feature modules; preserve owner-specific provider |

### 4.3 `PostgresBffRepositories`

It is a service locator, not a domain owner. Its constructor currently creates database, idempotency, project/scheduled/chat/public-share repositories, outboxes, AG-UI consumers, artifact library, skill-share repository and `BffApplicationServices`. Migration order is provider-by-provider; no mechanical rename.

- First move `PostgresPersonalizationRepository` (already module-local) and `PostgresProjectRepository`/`PostgresScheduledTaskRepository` into their feature modules.
- Then move Chat/Agent/AG-UI repositories and outboxes with their transaction/lease tests.
- Keep one `PostgresBffDatabase` provider per BFF process; do not create multiple pools or duplicate SQL owners.
- Delete `PostgresBffRepositories` only after all fields have explicit Nest providers and `createBffComposition` no longer constructs it.

## 5. Port keep/move/merge/delete candidates

| Port | Evidence | Candidate | Delete gate |
|---|---|---|---|
| `idempotency-repository` | persistent receipt claim/CAS/release | keep; feature-independent provider | only after explicit provider is used by all mutations |
| `project-repository` | project scope, revisions, tasks, resources, deletion | move to ProjectsModule | all project consumers use feature provider |
| `scheduled-task-repository` | calendar/lineage/CAS/task lifecycle | move to ScheduledTasksModule | scheduled consumers moved |
| `scheduled-task-outbox-repository` | durable scheduler dispatch outbox | move to ScheduledTasksModule | dispatcher/provider moved |
| `scheduler-dispatch-receipt-repository` | scheduler event idempotency/CAS | move to ScheduledTasksModule | internal dispatch route moved |
| `chat-repository` | private messages, cursor/replay, transaction reads | move to ChatModule | chat route/provider migration |
| `public-share-repository` | public share/snapshot owner | move to Chat/PublicShare feature | public share route migrated |
| `personal-knowledge-repository` | account-owned knowledge data | move to AccountModule | personal knowledge route migrated |
| `skill-share-repository` | skill share lifecycle/expiry | move to SkillsModule | skill share routes migrated |
| `agent-dispatch-outbox-repository` | Chat→Agent command queue | move to AgentRunsModule | chat/agent outbox provider migration |
| `agent-cancellation-outbox-repository` | delete compensation queue | move to AgentRunsModule | cancellation dispatcher migration |
| `scheduled-agent-dispatch-repository` | scheduled-task terminal-gated queue | move to ScheduledTasks/AgentRuns | terminal/dispatch workers moved |
| `project-scope-release-outbox` | storage scope-release queue | move to Projects/Storage boundary | release worker moved |
| `agui-projection-repository` | durable AG-UI ledger | keep, move to AguiModule | projector/controller migration |
| `agui-source-reader` | external Agent source read | move to AguiModule infrastructure | projector source wiring moved |
| `submitted-agent-run-reader` | Agent admission facts | move to AgentRunsModule | internal admission route migrated |
| `project-execution-binding-reader` | project execution verification | move to AgentRuns/Projects | verify route migrated |
| `stable-id-generator` | deterministic scheduled task/outbox IDs | move to ScheduledTasks provider | no global consumers |
| `agent-*delivery` ports | delivery interface with bounded retry/receipt behavior | keep feature-local; do not delete as thin type only | dispatcher no longer uses global composition |
| `scheduled-task-outbox-delivery` | scheduler delivery protocol | keep feature-local | worker provider migration |
| `bff-business-store` | aggregate of all above fields | delete after provider cutover | production import census zero |

## 6. Current reverse-import census (read-only evidence)

Commands used:

```bash
rg -n "LegacyRoutesModule|LegacyRoutesRuntime|LegacyRoutesMiddleware|createBffComposition|handleBffRequest|createBffServer|BffBusinessStore|BffApplicationServices|PostgresBffRepositories" src test scripts package.json
find src/application/ports src/application/agui/ports -type f | sort
```

Current facts:

- `LegacyRoutesModule` is imported by `src/app.module.ts`; middleware catches `*` and owns every request not excluded by health/readiness.
- `LegacyRoutesRuntime` is imported by `LegacyRoutesModule` and `GracefulShutdown`.
- `createBffComposition` is called by `LegacyRoutesRuntime` and `createBffServer`; `handleBffRequest` is called by both runtime and server factory.
- `BffBusinessStore` is imported by route handlers, application helpers, `bootstrap/runtime.ts`, tests and infrastructure; it cannot be deleted before feature provider cutover.
- `BffApplicationServices` is constructed only by `PostgresBffRepositories`, but its member services are consumed widely through `businessStore.services`.
- `PostgresBffRepositories` is constructed by `bootstrap/runtime.ts`; it is the current global database/service locator.
- The 24 port files include real transaction/CAS/lease/outbox boundaries; no blanket deletion is valid. The candidate table above is the required per-port decision record.
- `DatabaseModule` already exposes `BFF_DATABASE`/`BFF_POOL`, while `PostgresBffRepositories` constructs a second `PostgresBffDatabase`. Provider extraction must choose one database/pool owner before moving repositories; creating a second Nest provider is a lifecycle and connection-budget regression.

## 7. Next implementation gate

1. Finish C-1.3 profile-read owner contract (`GET /internal/v1/account/profile`) and its IAM generated artifact, BFF client/contract, App adapter and real receipt before deleting first-party RP/Product Session.
2. Update BFF package scripts/file lists whenever new Controller/Service/tests are added; explicit lists currently omit unregistered files from default `format:check`/`test` gates.
3. Start C-2 with `GET/PUT /v1/preferences/personalization` only after the profile-read gate. This slice has an existing feature-local `PERSONALIZATION_PROVIDER` and real CAS/transaction tests; it must not delete `BffBusinessStore` or unrelated global wrappers.
4. For each slice, migrate exact paths, add negative legacy-dispatch tests, run focused gates, then update this census and only then proceed to the next slice.
