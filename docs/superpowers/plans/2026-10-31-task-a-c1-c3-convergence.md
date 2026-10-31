# Task A C-1.3～C-4 收敛实施方案

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents are available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在进入 A-01/A-02/A-07 前，完成 C-1.3 first-party native-session 链路、BFF LegacyRoutes 全量退出、Repository/Service/Port feature-local 收敛，并以 Root/子仓全量门禁证明当前态已达到 C-1～C-4 完成条件。

**Architecture:** IAM 是唯一 native session、active tenant、membership、permission owner；App 只做同源 cookie adapter；BFF 在 HTTP boundary 一次完成 native admission 并冻结 subject/tenant/session context。BFF 以 Nest `AppModule` 为唯一 composition root，先按业务切片把 LegacyRoutes 中的 route ownership 下沉到 feature Controller → Service/use case → 必要的 feature-local Repository/owner Client，最后删除 LegacyRoutes、旧 dispatcher 与 global composition wrapper。

**Tech Stack:** Node 24、NestJS 12、Express adapter、TypeScript、Zod、PostgreSQL/Redis、现有 generated OpenAPI/Connect clients、Vitest/Node test、Root topology checks。

---

## 0. 当前基线与停写边界

**停写代码基线：** Root `f17bf828`（后续仅有文档同步提交 `18b59a43`），工作树 clean（子仓 App `4c41104d`、BFF `65cf2082`、IAM `108beedf`）。文档提交不改变代码基线；每次新增 evidence 后重新记录 Root 文档 HEAD 与子仓 gitlink。

**已交付事实：**

- G0 native-session contract 已固定：version `1.0.0`，digest `5cf59df4b7bd9853edfd2eabb31afc236c0ec0db371f9737706fc129484fd83f`。
- IAM runtime：child `497900ab`，新增 native admission controller/service/schema、direct credential profile、Cookie/Origin/body/header 校验和 fresh session projection，并接入 account/Team owner native proof；新增 canonical `GET /internal/v1/account/profile`。
- BFF native consumer：child `65cf2082`，新增 direct credential reader、native transport/client、Cookie allowlist、AccountModule/runtime wiring 和 owner transport forwarding。
- BFF Nest foundation/feature graph/ownership slices：`3f643ef`、`cd4ffb1`、`aacf1c5`、`6a42bd3`、`eefe02a`、`c9263cd`。
- 当前 BFF 全量：2301 pass / 2 skip / 0 fail；IAM unit：1403 pass；Root topology/diff-check 通过。

**C-1.3 owner cutover design gate (now fixed):** Account profile/profile update, account sessions, and Team are owner operations, not browser relays. The BFF sends the allowlisted IAM cookie, fixed configured Origin, request id, and the BFF `session_admission` direct credential. IAM authenticates that service identity, verifies the fresh issuer session/active tenant/membership/session id, and creates a marked native user principal. Account self operations retain Product tenant/session/CAS/transaction/Audit checks while skipping OAuth grant lookup only for the marked native proof; Team owner repositories recheck persisted role permissions in their existing snapshot. Legacy bearer remains only on uncut consumers and native requests fail closed rather than manufacturing a bearer. No DTO/schema/version change is introduced by this additive auth mode.

**明确未完成：**

- App 同源 native adapter、旧 Auth.js/OIDC RP、Product Session store/refresh reservation 尚未删除。
- App profile read 已切到 BFF `GET /v1/account/profile`；IAM owner artifact、BFF generated client 和 App consumer 已固定于 Root `c7af342b`，真实 infrastructure receipt 仍待环境补齐。
- `src/modules/legacy-routes/legacy-routes.runtime.ts` 仍持有 `createBffComposition()` 与旧 `handleBffRequest`，业务 route 尚未全部下沉。
- `BffBusinessStore`、`BffApplicationServices`、`PostgresBffRepositories` 仍是生产组合边界；`src/application/ports` 仍有全局 port。
- C-4 只完成基础门禁，未完成“LegacyRoutes 清零 + global composition 删除 + feature-local ownership”验收。
- A-01/A-02/A-07 在本方案完成前保持停写。

## 1. Goal / TODO 清单

| Goal | 结果定义 | 当前状态 | 证据/出口 |
|---|---|---:|---|
| G1 C-1.3 | App→BFF→IAM native session 链路闭合；旧 first-party RP/Session 在消费者切换后删除 | 进行中 | App native adapter、sign-in/sign-out/tenant-switch、撤权测试；删除旧 RP 后全量验证 |
| G2 LegacyRoutes | LegacyRoutes 只剩零业务 route 的冻结 adapter，最终删除 runtime/module/旧 dispatcher | 未完成 | 每个 feature slice 的 route inventory、Nest controller/service 测试；最终 `rg handleBffRequest` 只剩迁移记录/测试允许项 |
| G3 C-3 边界 | 每个保留 Repository/Service/Port 有真实事务/锁/CAS/lease/outbox/owner boundary 证据；其余并入 feature 或删除 | 未完成 | feature ownership 测试、全局 port 反向引用清单、global locator 删除 |
| G4 C-4 | 默认脚本只跑 canonical 当前行为；旧兼容/fallback/alias 测试清理；Root/子仓全量门禁通过 | 部分完成 | BFF/IAM/App/Agent 各 owner gate + Root topology + evidence |
| G5 A gate | C-1～C-4 完成且无未决设计/环境缺口后才进入 A-01/A-02/A-07 | 停写 | 本方案最终验收表 |

## 2. 非目标与不变量

- 本阶段不改业务 owner Schema、PostgreSQL DDL、跨仓 HTTP/Connect contract 版本或发布配置。
- 不把 LegacyRoutes 只改名为 Controller；每个下沉 slice 必须拥有真实 provider/use case、route 行为测试和从 adapter 移除的证据。
- 不保留 native session 与浏览器 bearer 的“无条件双读”；native 配置启用时用户准入只携带 allowlisted Cookie + Origin + BFF direct credential。
- 旧 bearer 仅可继续存在于独立 owner authorization surface；在对应 native owner 等价能力完成前，调用必须 fail-closed，不得伪造身份。
- 不删除仍有生产消费者的 global port；先移动到 feature-local，再反向确认 import 为零后删除旧路径。
- 不在全量测试与并行 build 竞争时宣称通过；全量门禁必须串行、停写后执行。

## 3. 目标架构与写区

### 3.1 认证链路

```text
IAM native session cookie
  -> App same-origin adapter (allowlisted Cookie/Origin/request id)
  -> BFF SessionAdmissionClient.verifyNative()
       + kokoro-bff/session_admission direct credential
  -> IAM fresh session + active tenant + membership/permissions
  -> AdmittedUserRequestContext(subject, tenant, session, permissions)
  -> feature Service / owner client
```

删除顺序固定为：App adapter 验证 → BFF native consumer 验证 → sign-in/sign-out/tenant-switch/撤权实测 → 删除 App first-party RP/Product Session → 删除只服务这些入口的旧测试与 relay 分支。Capability `global_register` 另行按 direct credential writer 表执行，不与 BFF route 迁移混写。

### 3.2 BFF route 下沉边界

| 阶段 | 唯一 writer | 允许路径 | 交付物 |
|---|---|---|---|
| C-1.3 App 闭环 | App owner | `apps/kokoro-app/src/**`、对应 tests/scripts | same-origin native adapter、旧 RP 删除 |
| C-2.5 Account/Projects | BFF owner | `apps/kokoro-bff/src/modules/account/**`、`projects/**`、相关 `src/http/routes/**`、tests | 第一批真实 Controller/Service/feature provider；从 LegacyRoutes 移除对应 route |
| C-2.6 Chat/AgentRuns/AG-UI | BFF owner | `chat/**`、`agent-runs/**`、`agui/**`、相关 persistence adapters/tests | durable ledger/run boundary 下沉，不改变 AG-UI wire |
| C-2.7 Scheduled/Skills/MCP/System/Billing/Music | BFF owner | 对应 feature modules + integration clients/tests | 按 route inventory 逐批退出 LegacyRoutes |
| C-3 | BFF owner | feature-local ports/repositories/services、旧 global wrapper | 移动/合并/删除，保留真实事务与 owner boundary |
| C-4 | Root + owner | 默认 scripts、architecture/contract tests、evidence | 清理旧兼容测试、串行全量验证 |

## 4. 实施顺序

### Task 1：冻结 inventory 与 acceptance matrix

**Files:**

- Modify: `docs/superpowers/evidence/2026-10-31-task-a-c1-cleanup-implementation.md`
- Create: `docs/superpowers/evidence/2026-10-31-task-a-c1-c3-inventory.md`
- Inspect only: `apps/kokoro-bff/src/modules/legacy-routes/*`
- Inspect only: `apps/kokoro-bff/src/bootstrap/runtime.ts`, `apps/kokoro-bff/src/bootstrap/server.ts`, `apps/kokoro-bff/src/main.ts`, `apps/kokoro-bff/src/app.module.ts`, `apps/kokoro-bff/src/common/lifecycle/graceful-shutdown.ts`
- Inspect only: `apps/kokoro-bff/src/application/ports/**`, `apps/kokoro-bff/src/application/services.ts`, `apps/kokoro-bff/src/infrastructure/postgres/repositories.ts`

- [x] 列出每个 `server.ts` path/method family 的当前 handler、目标 feature、依赖、测试、迁移状态；`LegacyRoutesRuntime` 只作为 middleware wrapper 单独记录。
- [ ] 列出 `BffBusinessStore`、`BffApplicationServices`、`PostgresBffRepositories` 的字段/方法及生产消费者。
- [ ] 对 `src/application/ports/**` 逐项标记 keep/move/merge/delete，并记录真实事务/锁/CAS/lease/outbox/owner boundary 证据。
- [x] 为每个 slice 写明“从 `server.ts`/adapter 删除的具体 path”和最低验证命令；没有 route/消费者证据的 slice 不进入实现。

### Task 2：完成 App native adapter，再关闭 C-1.3

**Files:**

- Modify: `apps/kokoro-app/src/**` native same-origin adapter and request context
- Delete after consumer proof: `apps/kokoro-app/src/app/api/auth/[...nextauth]/route.ts`, `src/lib/server/oidc-*`, first-party OAuth relay/token helpers（以实际 inventory 为准）
- Delete after adapter proof: Product Session cookie/store、refresh reservation 与只保护旧 RP 的 tests
- Test: App native adapter、sign-in/sign-out、tenant switch、revocation/multi-tab/late response

- [x] 先补 native adapter contract tests，证明浏览器 Authorization/body tenant 不会跨 boundary。
- [x] 接入 BFF native admission，保持 request-id、Origin、Cookie allowlist 与取消预算；`GET /api/auth/session` native path 不再要求旧 RP config。
- [x] Browser `endProductSession` 先读 native session；native session 直接走 issuer signout handoff，legacy Product Session 才走 Auth.js CSRF fallback。
- [ ] 实测登录、登出、active tenant 切换、撤权后的 401/403 与多标签 late response。
- [ ] 只有消费者证据成立后才删除旧 RP、Product Session 与 token/refresh 测试。
- [ ] 运行 App focused lint/typecheck/test；记录既有 `onReconnect` baseline，不扩大修复范围。

### Task 2.1：冻结并实现 Account Profile read owner contract

**设计门：** profile read 是 IAM account owner projection，不复用 OAuth userinfo relay。先变更 IAM API contract 与 generated artifacts，再按消费者顺序接入 BFF 和 App；在 contract、artifact、focused tests 与真实链路 receipt 齐备前，不删除旧 RP/Product Session。

**Contract：**

- IAM `GET /internal/v1/account/profile`，无 query/body，`Cache-Control: no-store`，标准 `accountProfileResponseSchema` 返回 `data.subject`, `data.name`, `data.email`, `data.email_verified`。
- native 请求使用现有 direct `session_admission` credential + allowlisted IAM Cookie + fixed Origin + request id；IAM fresh-recheck session、active tenant、membership、session id，并标记 native principal。
- legacy bearer 请求保持现有 account profile scope/tenant/client 校验；两种模式共享同一 response/error schema，不引入第二套 DTO。
- BFF 新增 `GET /v1/account/profile`，仅负责 request admission、owner credential materialization、generated IAM client 调用、deadline/cancel、closed error mapping 和 no-store response；不读取 IAM 数据库。
- App `GET /api/account/profile` 改用 `admittedProductSession` + BFF native headers；只接受 BFF canonical projection，保持 subject binding、final admission recheck、no-store 与 bounded body。

**验证出口：** IAM contract/HTTP/guard tests → BFF client/HTTP tests → App profile-read focused tests → 真实 cookie→BFF→IAM receipt → 停写后串行 owner gates。生成器、OpenAPI digest 和 consumer pin 已在同一提交序列中更新；当前仅真实 receipt 为环境缺口。

### Task 3：Personalization 第一批真实 route 下沉（C-1.3 profile-read gate 之后）

**Files:**

- Modify/Create: `apps/kokoro-bff/src/modules/account/**`
- Modify: `apps/kokoro-bff/src/bootstrap/server.ts`, `apps/kokoro-bff/src/bootstrap/runtime.ts` only for the exact migrated path/provider seam
- Modify: `apps/kokoro-bff/src/modules/legacy-routes/*`, `apps/kokoro-bff/src/app.module.ts`, `apps/kokoro-bff/src/main.ts`, `apps/kokoro-bff/src/common/lifecycle/graceful-shutdown.ts` only when the route/worker graph requires it
- Modify: `apps/kokoro-bff/src/http/routes/personalization.ts` only if its raw HTTP parsing is extracted into the controller boundary; exact focused tests and explicit package.json file lists

- [x] 以已有 `PERSONALIZATION_PROVIDER` 作为首个 C-2 slice，先写 architecture/HTTP seam，迁移精确的 `GET/PUT /v1/preferences/personalization`。
- [x] AccountModule `AccountMiddleware` 负责 native/user admission context、owner transport、raw body/query/content-type/abort/5 秒 deadline 与 error envelope；`PERSONALIZATION_PROVIDER` 继续负责真实 CAS/事务，未复制 Repository 或 generic receipt。
- [x] 在 `AccountModule` 注册 middleware/provider，显式注入 `PERSONALIZATION_PROVIDER` 与 `SESSION_ADMISSION`；Account native bundle 在旧 dispatcher 前终止。
- [x] Account native bundle（profile/sessions/team/me/personalization）与 System runtime-manifest 已从 `handleBffRequest` 分派移出；`createBffServer` 只保留显式 feature adapter seam 供现有 raw HTTP/integration fixture 使用，并由同一 handler 实现。
- [x] 同步 BFF `package.json` 显式 format 文件清单；BFF build/typecheck/format/lint、feature focused tests、`test:nest-architecture`、`test:architecture` 已通过。

**Personalization slice exit:** only after Task 2.1 profile-read contract/artifacts/receipt are complete; this slice must not remove `BffBusinessStore`, `BffApplicationServices`, `PostgresBffRepositories`, or unrelated LegacyRoutes branches.

### Task 3.1：Projects 第一批真实 route 下沉

- Modify/Create: `apps/kokoro-bff/src/modules/projects/**`
- Modify: exact project route branches in `apps/kokoro-bff/src/bootstrap/server.ts`, feature wiring, focused tests and explicit package.json file lists
- [ ] After Personalization exit, choose Project read/rename/pin only when the provider graph and DB pool owner are explicit; preserve project scope, idempotency and deadline behavior.
- [x] Project pin (`GET /v1/self/project-pins`, `PUT /v1/projects/:id/pin`) now uses `ProjectsModule` `PROJECT_SERVICE` + `ProjectPinMiddleware`; `handleBffRequest` no longer owns the branch and existing natural-idempotency/owner-scope behavior is preserved.
- [x] Project resource metadata/download (`GET /v1/projects/:id/resources/:asset_id[\/download]`) now uses `ProjectsModule` `ProjectPinMiddleware` + `handleProjectResourceReadRequest`; old dispatcher branch is deleted and verified-download/owner-recheck behavior is preserved.
- [x] Project resource upload (`POST /v1/projects/:id/resources`) now uses `ProjectsModule` `ProjectPinMiddleware` + `handleProjectResourceUploadRequest`; old dispatcher branch is deleted and receipt/checkpoint/scan behavior is preserved.
- [x] Project skill-selection (`GET/PUT /v1/projects/:id/skill-selection`) now uses `ProjectsModule` `PROJECT_SKILL_SELECTION_PROVIDER` + `PROJECT_SKILL_INSTALLATION_CLIENT` and `ProjectPinMiddleware`; the old `handleBffRequest` branch is removed, native admission/recheck and persistent receipt validation are preserved (`2dd93ca`).
- [x] Project MCP recommendations (`GET/PUT /v1/projects/:id/mcp-recommendations`) now use `McpModule` `PROJECT_MCP_RECOMMENDATIONS_PROVIDER`/`MCP_AUTHORIZATION` and `ProjectMcpRecommendationsMiddleware`; the old `handleBffRequest` branch is removed, candidate validation, read-vs-manage admission, CAS and cancellation are preserved (`9310aa6`).
- [x] Project skill-installations (`/v1/projects/:id/skill-installations/**`) now use `ProjectsModule` `ProjectPinMiddleware` + `SKILL_AUTHORIZATION`/`SKILL_INSTALLATION_CLIENT`; the old project branch is removed while package-inspection paths remain in the canonical package route, and owner qualification/rechecks are preserved (`d9a8a24`).
- [x] Personal skill-installations (`/v1/skill-installations/**`) now use `SkillsModule` `SkillsMiddleware` + `SKILL_AUTHORIZATION`/`SKILL_INSTALLATION_CLIENT`; the old personal dispatcher branch is removed while the same installation owner contract and admission errors are preserved (`1153be7`).
- [x] Managed personal Skill reads (`GET /v1/self/skills[/:skill_id[/versions]]`) now use `SkillsModule` `SkillsMiddleware`; the old dispatcher read branch is removed while projection, IAM enrichment, deadline and error mapping remain unchanged (`7aa092b`).
- [x] Browser-private Skill enable command (`/skill.v1.SkillOptionalService/SetSkillInstallationEnabled`) now uses `SkillsModule` `SkillsMiddleware`; the old dispatcher branch is removed while installation owner ACK/error/deadline behavior remains unchanged (`2531941`).
- [x] Skill usage (`POST /v1/skills/usage`) now uses `SkillsModule` `SkillsMiddleware` and its `SKILL_USAGE_READER` pool-backed provider; the old dispatcher branch is removed while admission, bounded refs and unavailable/zero semantics remain unchanged (`a75930e`).
- [x] Personal Skill lifecycle (`POST /v1/self/skills/:id/versions`, `POST /withdraw`, `DELETE /v1/self/skills/:id`) now uses `SkillsModule` `SKILL_DRAFT_CLIENT`/`SkillsMiddleware`; the old dispatcher branches are removed while action admission, strict path handling, CAS/idempotency and owner ACK/error semantics remain unchanged (`e1a4f4d`).
- [x] Skill draft creation (`POST /v1/skills/drafts`) now uses `SkillsModule` `SKILL_DRAFT_CLIENT`/`SkillsMiddleware`; the old dispatcher branch is removed while create-draft admission, exact path/query behavior, body budget, idempotency and owner projection remain unchanged (`e2365e5`).
- [x] Skill draft mutations (`PATCH /v1/skills/:id/draft`, `POST /discard`, `POST /audience`) now use `SkillsModule` `SKILL_PRODUCT_CLIENT`/`SkillsMiddleware`; the old dispatcher branches are removed while action admission, strict input, command digest and owner error behavior remain unchanged (`8a85548`).

### Task 4：Chat/AgentRuns/AG-UI 与 ScheduledTasks 下沉

**Files:**

- Modify/Create: `apps/kokoro-bff/src/modules/chat/**`, `agent-runs/**`, `agui/**`, `scheduled-tasks/**`
- Modify: `src/application/agui/**`, outbox/dispatcher providers only where ownership moves
- Modify: `src/modules/legacy-routes/legacy-routes.runtime.ts`
- Test: corresponding HTTP/ledger/replay/outbox/cancel/lease tests

- [x] Chat archive/share bundle（archived tasks、shared tasks、session archive/restore）已接入 `ChatModule` 的 `CHAT_SERVICE` provider 与 `ChatMiddleware`，从 `handleBffRequest` 移除旧分支；HTTP/error/admission/architecture focused tests 通过。
- [x] ScheduledTask current-read bundle（`GET /v1/scheduled-tasks[/:id]`）已接入 `ScheduledTasksModule` 的 `SCHEDULED_TASK_READ_SERVICE` provider 与 `ScheduledTaskReadMiddleware`，从 `handleBffRequest` 移除旧分支；保留 5 秒预算、owner current-state read、snapshot revalidation 与 final admission。
- [x] AgentRuns internal bundle（model admission/settlement/recovery 与 project-execution-binding verify）已接入 `AgentRunsModule` 的 `AGENT_RUNS_READER` provider 与 `AgentRunsMiddleware`，从 `handleBffRequest` 移除旧分支；保留 dedicated credential、durable reader、Billing/IAM owner boundary 与 bounded cancellation。
- [x] Agent run-display bundle（`GET /v1/sessions/:id/runs/:run/display`）已接入 `RUN_DISPLAY_PROVIDER` 与 `AgentRunsMiddleware`，从 `handleBffRequest` 移除旧分支；保留 submitted-run binding、Chat owner read、AG-UI transport、final admission 与 5 秒预算。
- [x] Chat message-feedback bundle（`GET/PUT /v1/sessions/:id/messages/:message/feedback`）已接入 `CHAT_SERVICE` 与 `ChatMiddleware`，从 `handleBffRequest` 移除旧分支；保留 feedback CAS/read、re-admission 与错误闭集。
- [ ] 保留 durable ledger、cursor/replay、lease/CAS/outbox、取消和 drain 顺序；不复制 AG-UI envelope。
- [ ] 将 Chat/Run/AG-UI repository/client 拆成 feature-local provider；只对有真实复杂边界的 repository 保留独立类型。
- [ ] 每个 route bundle 迁移后从 adapter 删除并执行 focused HTTP + architecture tests。

### Task 5：剩余 feature route 与 LegacyRoutes 删除

**Files:**

- Modify/Create: `skills/**`, `mcp/**`, `system/**`, `billing/**`, `music/**`, `iam-relay/**`
- Delete after zero-route proof: `src/modules/legacy-routes/legacy-routes.runtime.ts`, `legacy-routes.module.ts`, `legacy-routes.middleware.ts`
- Delete after provider graph proof: old `src/bootstrap/server.ts` business dispatcher and `src/bootstrap/runtime.ts` global composition paths

- [ ] 以 Task 1 inventory 为序迁移，不新增 route/alias/fallback；实际写区包含 `bootstrap/server.ts`、`app.module.ts`、`main.ts` 和测试引用，不把 runtime wrapper 改名为 Controller。
- [ ] 每一批完成后更新 route census；census 为零前不删除 adapter。
- [ ] 所有 feature provider cutover 与反向 import census 完成后，才删除旧 listener/dispatcher；运行 source-runtime architecture gate，证明唯一 Nest listener 和唯一 composition root。

### Task 6：C-3 Repository/Service/Port 收敛（按 slice 前置，最终删除后置）

**Files:**

- Move/Modify: `apps/kokoro-bff/src/application/ports/**` → feature-local ports
- Modify/Delete: `src/infrastructure/postgres/repositories.ts`, `src/application/services.ts`, `src/application/ports/bff-business-store.ts`
- Modify: feature module providers/tests/architecture oracle

- [ ] 先按 inventory 移动有真实 owner boundary 的 port，不改行为。
- [x] 首个 C-3 slice 已将 `PersonalizationProvider` 从 `BffApplicationServices` 移到 `BffBusinessStore.personalizationProvider` 的显式 raw-server seam；CAS/事务实现未复制。
- [ ] 单实现、无边界的 Service 并入 feature Service/Provider；只转发一次的 Port 删除并把测试绑定公开行为。
- [ ] 每个 feature slice 先完成对应 provider cutover 与 import census；全部 route slice 完成后，`BffBusinessStore`/`PostgresBffRepositories`/`BffApplicationServices` 才能从生产 composition 删除，避免先删 wrapper 造成循环依赖或第二套 locator。
- [ ] 运行全局 import census，确认没有相对路径穿越 sibling、第二 DTO/ORM/SQL owner 或空模块。

### Task 7：C-4 清理与最终全量验证

**Files:**

- Modify/Delete: default test scripts、legacy/fallback/evolution fixtures、architecture oracles
- Modify: `docs/superpowers/evidence/2026-10-31-task-a-c1-cleanup-implementation.md`

- [ ] 删除只验证已删除 alias/fallback/旧 dispatcher 的测试；保留能证明当前 canonical 行为和失败恢复的测试。
- [ ] 串行执行：

```bash
git diff --check
python3 scripts/verify-repository-topology.py
python3 -m pytest scripts/tests -q
# IAM
cd apps/kokoro-iam && pnpm prisma:format && pnpm prisma:validate && pnpm prisma:generate && pnpm format:check && pnpm lint && pnpm typecheck && pnpm contract:check && pnpm test && pnpm build
# BFF
cd ../kokoro-bff && pnpm format:check && pnpm lint && pnpm typecheck && pnpm contract:check && pnpm build && pnpm test:nest-architecture && pnpm test:architecture && pnpm test
# when isolated PostgreSQL/Redis resources are available
pnpm test:integration
# App / Agent 按各自 AGENTS.md 完整 owner gate
```

- [ ] 记录 pass/fail/skip、既有 baseline、环境缺口和未决风险；全量验证前不进入 A。
- [ ] 更新任务台账与 plan 状态；只有所有 G1～G4 acceptance criteria 满足后，才创建 A-01/A-02/A-07 的实施计划。

## 5. 风险与处理

| 风险 | 处理 |
|---|---|
| App native adapter 与 BFF native consumer 不成对 | 先 contract test/HTTP fixture，再删除旧 RP；不保留无凭据 fallback |
| BFF native identity 无 bearer，旧 Skill/MCP owner 调用被拒绝 | 为对应 owner surface 单独设计 native/direct credential boundary；在迁移前保持 fail-closed，不伪造 bearer |
| LegacyRoutes 下沉造成 wire/取消/幂等变化 | 每个 slice 保留现有 raw request、deadline、abort、idempotency、error envelope 测试；route 移除后重跑原测试 |
| global composition 删除过早 | 以 route census、provider graph 和 source import census 为删除门；不以空模块/重命名作为完成证据 |
| 全量测试与 build 并发导致 dist 缺失 | worker 停写后串行执行 build → focused gates → full test |
| 权限/tenant/session 语义漂移 | session context 只在 HTTP boundary 冻结；owner 数据库不跨边界读取；所有 admin/action 再做 fresh qualification |

## 6. 完成定义与 A gate

- [ ] C-1.3：App native adapter、BFF native consumer、IAM runtime、sign-in/sign-out/tenant-switch/revocation 证据齐全；`GET /internal/v1/account/profile` owner contract、generated IAM/BFF artifacts、App profile-read receipt 齐全后，旧 first-party RP/Product Session 才能删除。当前 App 既有 7 failures、2 skips 与 `onReconnect` typecheck baseline 需单列，不能笼统写成全绿。
- [ ] C-2：唯一 Nest listener、唯一 AppModule composition root；LegacyRoutes 与旧 dispatcher 删除，且反向搜索 `LegacyRoutesModule/Runtime/Middleware`、`createBffComposition`、`handleBffRequest`、`createBffServer` 生产引用为零或有明确保留证据。
- [ ] C-3：global Repository/Service/Port 只剩有证据的 feature-local boundary；global locator/wrapper 删除。
- [ ] C-4：默认测试只覆盖 canonical 当前态；owner/root 全量门禁通过；证据文档更新完成。
- [ ] A-01/A-02/A-07：仅在上述四项均通过后另建实施计划并开始。

### 2026-10-31 execution update

- BFF child `8a85548` completed the project skill-selection, project MCP recommendations, project/personal skill-installations, managed personal Skill reads, Skill enable command, Skill usage, personal Skill lifecycle and Skill draft creation/mutation feature cutovers, and fixed the managed-read method boundary so POST lifecycle commands continue to the canonical lifecycle adapter. The features own narrow providers, admission seams, candidate clients and lifecycle cleanup; no second repository/service or global locator was introduced.
- Focused verification passed: `pnpm lint`, `pnpm typecheck`, `pnpm build`, `pnpm test:nest-architecture` (15/15), `pnpm test:architecture` (34/34), Skill draft/lifecycle/usage suite (107/107), and the prior combined Skills/MCP/content/installation/usage/personal-lifecycle suite (203/203; prior skill-selection/contract focus remains 144/144). The `a75930e` full BFF run was 2312 tests / 2302 pass / 8 fail / 2 skip; six lifecycle regressions were fixed by `a0bc277` and rechecked 19/19. The remaining Artifact/Personal Storage failures still require a stopped-worktree full rerun and are not a C-4 pass.
- BFF `pnpm format:check` still reports pre-existing warnings including `src/bootstrap/server.ts` and `src/modules/projects/project-pin.middleware.ts`; full BFF test run remains non-green on unrelated baseline/environment failures and was interrupted at the existing long-running contract boundary. This is evidence of current state, not a C-4 pass.
- Next slice is the remaining other Skills route bundle; LegacyRoutes deletion and global Repository/Service/Port removal stay blocked until route census and provider import census are zero.

