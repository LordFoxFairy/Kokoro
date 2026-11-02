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
- 当前 BFF 全量：2312 tests / 2295 pass / 15 fail / 2 skip；失败集中在既有 Artifact/Personal Storage Product HTTP、Project exact-download、Admin Web credential fixture 与 anonymous Share fixture；IAM unit：1403 pass；Root topology/diff-check 通过。BFF exact-download focused 22/22 通过，但不改变全量非绿结论。

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
- [x] Connector list (`GET /v1/connector.list`) now uses `McpModule` `MCP_PERSONAL_CLIENT`/`ConnectorListMiddleware`; native admission and MCP read qualification happen before owner reads, while the existing projection, pagination, request-id/no-store and failure envelopes remain unchanged (`418021f`).
- [x] MCP provider/package admin (`/v1/admin/mcp/providers/**`, `/v1/admin/mcp/packages/**`) now uses `McpModule` `MCP_PROVIDER_ADMIN_CLIENT`/`MCP_PACKAGE_ADMIN_CLIENT`/`McpAdminMiddleware`; catalog admission, platform-admin qualification, command/body validation, bounded cancellation and owner error mapping remain unchanged (`b178828`).
- [x] MCP project publication (`/browser/v1/mcp/**` publication/pin/receipt) now uses `McpModule` `MCP_PROJECT_PUBLICATION_CLIENT`/`McpProjectPublicationMiddleware`; project scope rechecks, read/manage admission, receipt/CAS, original command digest, cancellation and owner result validation remain unchanged (`9adb097`).
- [x] App skill-bindings (`/v1/admin/open-apps/:app_id/skill-bindings[/:series_id]`) now uses `SkillsModule` `APP_SKILL_BINDING_CLIENT`/`OPEN_APP_MANAGEMENT_ADMISSION`/`SkillsMiddleware`; fresh operator registration, exact app/tenant binding, CAS/idempotency and dual owner credentials remain unchanged (`49511ae`).
- [x] Skill specification reads (`/v1/skill.list`, `/skill.v1.SkillOptionalService/*`, `/skill.v1.SkillService/DownloadSkill`) now use `SkillsModule` `SKILL_LIST_ADMISSION`/`SKILL_SPECIFICATION_SOURCE`/`SKILL_DOWNLOAD_HANDLES`/`SkillsMiddleware`; public/private admission, exact source projection, opaque handles and response/error contracts remain unchanged (`dff1787`).
- [x] All Skill package inspection (`GET /v1/self/skills/:id/package`, `GET /v1/skill-installations/:id/package`, `GET /v1/projects/:id/skill-installations/:installation_id/package`) now uses SkillsModule/ProjectsModule `SKILL_PACKAGE_INSPECTION_CLIENT` middleware; strict request validation, current admission, exact project scope, owner projection and bounded response behavior remain unchanged (`b610c92`).
- [x] Exact Skill download handlers now consume a narrow `SkillDownloadProvider` contract instead of `BffServerComposition`; SkillsModule/ProjectsModule now own exact source construction and POST native middleware, including project installation recheck; raw fallback/GET handle cleanup remains open (`82199a4`, `6633306`).
- [x] Project skill-installations (`/v1/projects/:id/skill-installations/**`) now use `ProjectsModule` `ProjectPinMiddleware` + `SKILL_AUTHORIZATION`/`SKILL_INSTALLATION_CLIENT`; the old project branch is removed while package-inspection paths remain in the canonical package route, and owner qualification/rechecks are preserved (`d9a8a24`).
- [x] Personal skill-installations (`/v1/skill-installations/**`) now use `SkillsModule` `SkillsMiddleware` + `SKILL_AUTHORIZATION`/`SKILL_INSTALLATION_CLIENT`; the old personal dispatcher branch is removed while the same installation owner contract and admission errors are preserved (`1153be7`).
- [x] Managed personal Skill reads (`GET /v1/self/skills[/:skill_id[/versions]]`) now use `SkillsModule` `SkillsMiddleware`; the old dispatcher read branch is removed while projection, IAM enrichment, deadline and error mapping remain unchanged (`7aa092b`).
- [x] Browser-private Skill enable command (`/skill.v1.SkillOptionalService/SetSkillInstallationEnabled`) now uses `SkillsModule` `SkillsMiddleware`; the old dispatcher branch is removed while installation owner ACK/error/deadline behavior remains unchanged (`2531941`).
- [x] Skill usage (`POST /v1/skills/usage`) now uses `SkillsModule` `SkillsMiddleware` and its `SKILL_USAGE_READER` pool-backed provider; the old dispatcher branch is removed while admission, bounded refs and unavailable/zero semantics remain unchanged (`a75930e`).
- [x] Personal Skill lifecycle (`POST /v1/self/skills/:id/versions`, `POST /withdraw`, `DELETE /v1/self/skills/:id`) now uses `SkillsModule` `SKILL_DRAFT_CLIENT`/`SkillsMiddleware`; the old dispatcher branches are removed while action admission, strict path handling, CAS/idempotency and owner ACK/error semantics remain unchanged (`e1a4f4d`).
- [x] Skill draft creation (`POST /v1/skills/drafts`) now uses `SkillsModule` `SKILL_DRAFT_CLIENT`/`SkillsMiddleware`; the old dispatcher branch is removed while create-draft admission, exact path/query behavior, body budget, idempotency and owner projection remain unchanged (`e2365e5`).
- [x] Skill draft mutations (`PATCH /v1/skills/:id/draft`, `POST /discard`, `POST /audience`) now use `SkillsModule` `SKILL_PRODUCT_CLIENT`/`SkillsMiddleware`; the old dispatcher branches are removed while action admission, strict input, command digest and owner error behavior remain unchanged (`8a85548`).
- [x] Skill catalog commands (`POST /v1/skills/:id/package-upload[/{complete}]`, `POST /validate`, `POST /publish`) now use `SkillsModule` `SKILL_DRAFT_CLIENT`/`SkillsMiddleware`; the old dispatcher branches are removed while action admission, strict path, owner projection, object-origin and budget behavior remain unchanged (`9fde981`).
- [x] Skill package-upload reference read (`GET /v1/skills/:id/package-upload`) now uses `SkillsModule` `SKILL_DRAFT_CLIENT`/`SkillsMiddleware`; the old dispatcher branch is removed while user admission, owner reference projection and strict read behavior remain unchanged (`6109daa`).
- [x] Skill cover routes (`GET /v1/skills/:id/cover`, `GET/POST /cover-upload`, `POST /cover-upload/complete`) now use `SkillsModule` `SKILL_PRODUCT_CLIENT`/`SkillsMiddleware`; the old dispatcher branches are removed while admission/recheck, action authorization, object-origin, media validation and budget behavior remain unchanged (`6784090`).
- [x] Published Skill package read (`GET /v1/skills/:id/package`) now uses `SkillsModule` `SKILL_PRODUCT_CLIENT`/`SkillsMiddleware`; the old dispatcher branch is removed while user admission, strict file_path handling and owner bytes projection remain unchanged (`ef1241c`).
- [x] Skill admin routes (`GET/POST /v1/admin/skills/**`) now use `SkillsModule` `SKILL_ADMIN_CLIENT`/`SkillsMiddleware`; the old dispatcher branch is removed while admin action admission, dedicated machine credential, owner projection and budget behavior remain unchanged (`11ce200`).
- [x] GitHub Skill preview (`POST /v1/skills/github/preview`) now uses `SkillsModule` `SkillsMiddleware`; the old dispatcher branch is removed while preview input, immutable GitHub resolution, final session recheck and dependency mapping remain unchanged (`684fb00`).
- [x] GitHub Skill import (`POST /v1/skills/github/import`) now uses `SkillsModule` `SKILL_IMPORT_RECEIPTS`/`SkillsMiddleware`; the old dispatcher branch is removed while shared receipt handoff, immutable source validation, owner commands and final session recheck remain unchanged (`f19c0f9`).
- [x] AI Skill import (`POST /v1/skills/ai-import`) now uses `SkillsModule` `SkillsMiddleware` with `SKILL_IMPORT_RECEIPTS` plus Chat-owned `SKILL_AI_ASSOCIATION`; the old dispatcher branch is removed while artifact re-read, receipt handoff, owner commands and final session recheck remain unchanged (`01d62f4`).
- [x] Skill share (`/v1/skill-shares/**`) now uses `SkillsModule` `SKILL_SHARE_REPOSITORY`/`SKILL_SPECIFICATION_SOURCE` and `SkillsMiddleware`; the old dispatcher branch is removed while validated public origin, owner inspection, creator revoke and current qualification remain unchanged (`ec56b0e`).
- [x] Admin identity (`GET /v1/admin/identity/{members,invitations,roles}`) now uses `AccountModule` `handleAdminIdentityRequest`; the old dispatcher branch is removed while tenant qualification, page validation, cancellation and IAM error mapping remain unchanged (`80c19b0`).
- [x] Billing admin (`POST /v1/admin/billing/credit-grants`, `/v1/admin/billing/metering/**`) now uses `BillingModule` `BillingAdminMiddleware`; the old dispatcher branches are removed while administrator recheck, absolute deadline, owner mapping and strict request-shape validation remain unchanged (`44a2e86`).
- [x] System admin (`/v1/admin/model-*`, `/v1/admin/model-providers/**`) now uses `SystemModule` `SystemMiddleware` and `handleSystemAdminRequest`; the old dispatcher branches are removed while administrator admission, strict request shape, deadline/cancellation and System owner mapping remain unchanged (`2005772`).
- [x] Chat move (`POST /v1/sessions/:id/move`) now uses `ChatModule` `handleMoveSessionRequest` with a narrow `ChatMoveProvider`; the old dispatcher branch is removed while canonical ids, idempotency, scope semantics, cancellation and owner result mapping remain unchanged (`f66e06a`).
- [x] Browser local Skill import (`/browser/v1/skills/local-imports/**`) now uses `SkillsModule` `SKILL_LOCAL_IMPORT_CLIENT`/`SkillsMiddleware`; the old dispatcher branch is removed while dual action admission, owner RPCs, replay and credential-set gating remain unchanged (`4b8b63d`).
- [x] Personal Knowledge (`/v1/preferences/knowledge[/**]`, `/v1/preferences/knowledge-usage`) now uses `AccountModule` `PERSONAL_KNOWLEDGE_REPOSITORY`/middleware; the old dispatcher branch is removed while tenant/subject admission, revision/CAS, limits/tombstones, usage and budget behavior remain unchanged (`e8d7cf6`).
- [x] C-3 Knowledge cleanup moves `personalKnowledge` out of `BffApplicationServices` into the named `BffBusinessStore.personalKnowledge` transitional seam; AccountModule remains the canonical feature provider and SQL owner is unchanged (`2564efb`).
- [x] C-3 Skill usage cleanup moves `skillUsage` out of `BffApplicationServices` into the named `BffBusinessStore.skillUsage` transitional seam; SkillsModule remains the canonical usage provider and projection SQL owner is unchanged (`a414503`).
- [x] C-3 Skill AI association cleanup moves `skillAiAssociation` out of `BffApplicationServices` into the named `BffBusinessStore.skillAiAssociation` transitional seam; import routes keep the same artifact owner query (`9f2c6f1`).
- [x] C-3 Skill share cleanup moves `skillShares` out of `BffApplicationServices` into the named `BffBusinessStore.skillShares` transitional seam; share/exact-download repository ownership is unchanged (`109efc7`).
- [x] C-3 Public share cleanup moves `PublicShareApplicationService` out of `BffApplicationServices` into the named `BffBusinessStore.publicShareService` transitional seam; ChatModule remains the canonical provider (`a80afa8`).
- [x] C-3 ScheduledTask cleanup deletes `BffBusinessStore.scheduledTaskService`; runtime snapshots, scheduler callback reads, and live-bff authorization/create/update/delete/retry consumers use `services.scheduledTasks` (`33a1bf0`).
- [x] C-3 Project cleanup deletes `BffBusinessStore.projectService`; Project/Chat authorization, resource, Skill-selection, MCP recommendation and live-bff project consumers use `services.projects` or feature composition (`2cc1c1b`).

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
- [x] Chat direct read bundle（`GET /v1/sessions[/:id]`、messages、parts、run process）已接入 `ChatModule` 的 `handleChatBusinessReadRequest`；feature-local `ChatBusinessProvider` 取代该路径对 `BffBusinessStore` 的依赖，保留 IAM admission、owner recheck、分页/cursor、取消和 canonical envelope；project-scoped、events 与 POST mutation 保持旧入口等待下一 slice（`0823d97`）。
- [x] Chat migrated-path bypass 已接入 `LegacyRoutesMiddleware`：public share、archive/shared tasks、direct Chat reads、feedback、regeneration、move 直接交给 Chat feature middleware；POST messages、events、title/delete/share 与 project-scoped reads 继续保留在旧入口并由负向测试锁定（`630efbf`）。
- [x] Chat title/delete/share mutations（含 `project_ref`）已由 `ChatModule` 的 `CHAT_IDEMPOTENCY` + 共享 `ProjectAccessModule` + `ChatApplicationService` 接管；Chat POST 仍保留旧入口（`ff14c86`）。
- [x] Chat AG-UI events（含 `project_ref`）已由 `ChatModule` + `AguiModule` + 共享 `ProjectAccessModule` 接管；projection/consumer/runtime provider 与 SSE replay/connection limits 复用既有 Agent adapter，Chat POST 与 LegacyRoutes projector worker 仍 transitional（`ff14c86`）。
- [x] Chat POST message submission 已由 `ChatModule` 接管；复用 `ChatTurnApplicationService`/Agent outbox、共享 Project owner、Skill installation owner、idempotency receipt 与 selection recheck，LegacyRoutes 不再接收 `/v1/sessions/:id/messages` POST（`ff14c86`）。
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

- BFF child `5659b1d` completed the prior route cutovers, direct Chat read feature ownership, exact Skill download POST/GET handle feature ownership, named Chat/ChatTurn service seams, Music `/v1/mori/**` feature ownership, and Message regeneration/ChatTurn feature ownership; it removed both Skill download branches and the Mori branch/retired helper from the old dispatcher. It also moved Knowledge, Skill usage, Skill AI association, Skill share, Public share, ScheduledTask and Project owner seams out of the global service aggregate. ScheduledTask, Project, Chat, Music and regeneration consumers now prefer named/native seams, GitHub/AI import and Skill share use narrow SkillsModule receipt/association/specification providers, and the migrated routes stay on the native chain for both production and mock/raw composition. The features own narrow providers, admission seams, candidate clients and lifecycle cleanup; no second business repository/service or global locator was introduced.
- Focused verification passed: `pnpm lint`, `pnpm typecheck`, `pnpm build`, `pnpm test:nest-architecture` (18/18), `pnpm test:architecture` (34/34), Music focused (12/12), Message regeneration focused (4/4), exact-download HTTP/policy/unit (22/22), Chat/ChatTurn/run-display focused (212/212), BFF mock contract (25/25), connector-list HTTP (5/5), MCP provider/package admin HTTP (12/12), MCP project publication HTTP (27/27), App skill-bindings/Open App management (12/12), Skill specification contract/focused (149/149), package inspection unit (47/47; 4 environment skips), plus the prior feature suites. The latest BFF full run is 2316 tests / 2299 pass / 15 fail / 2 skip; failures remain the existing Artifact/Personal Storage Product HTTP, Project exact-download, Admin Web credential fixture and anonymous Share fixture baselines, so C-4 remains open.
- Current remaining C-3 census: `BffApplicationServices` remains as the compatibility aggregate for integration fixtures; ScheduledTask/Chat/ChatTurn/Project production providers are feature-local or read through `services` and no longer duplicated on `BffBusinessStore`. Remaining direct aggregate references are limited to compatibility fallbacks and integration tests; LegacyRoutes/createBffComposition/handleBffRequest references remain and require the next zero-consumer proof. No A gate is opened.
- BFF `pnpm format:check` still reports pre-existing warnings including `src/bootstrap/server.ts` and `src/modules/projects/project-pin.middleware.ts`; full BFF test run completed non-green on the baseline/environment failures above. This is evidence of current state, not a C-4 pass.
- Chat POST/events/project-scope bundles are now cut over; next slice is Agent dispatch/run-control and LegacyRoutes projector worker ownership, followed by the remaining global provider/Port census. LegacyRoutes deletion and global Repository/Service/Port removal stay blocked until route census and provider import census are zero.
- `a5b94c0` moves run control (`POST /v1/sessions/:id/runs/:run/control`) into `AgentRunsModule`; remaining Agent run/session paths and projector lifecycle still require ownership cleanup.
- `ba8ab60` extends the `LegacyRoutesMiddleware` bypass to AgentRuns-owned internal admission/binding and exact Run display paths. AgentRuns method/credential/owner-read/error behavior remains in `AgentRunsMiddleware`; this is a boundary cutover, not LegacyRoutes deletion.
- `ba8ab60` moves Agent dispatch/cancellation outbox repository, delivery and lifecycle ownership into `AgentDispatchModule`; `LegacyRoutesRuntime` no longer starts those workers, and explicit-null composition options prevent duplicate production workers. Apply the same rule to AG-UI projector and scheduled/project-scope workers before removing the transitional runtime.
- `ba8ab60` applies the same lifecycle rule to AG-UI projector ownership: `AguiModule` constructs and starts the canonical projector, while raw composition receives an explicit feature instance only for shutdown compatibility. The next worker slice is scheduled/project-scope lifecycle, not a new generic worker wrapper.
- `ba8ab60` applies the lifecycle rule to scheduled-task outbox ownership: `ScheduledTasksModule` constructs and starts the scheduler worker, while LegacyRoutes only receives its explicit shutdown seam. The remaining worker TODO is scheduled Agent dispatch/terminal and project-scope release ownership.
- `ba8ab60` applies the lifecycle rule to project-scope release ownership: `ProjectsModule` constructs and starts the Storage release worker only when storage is configured, while LegacyRoutes receives only the explicit shutdown seam. The remaining worker TODO is scheduled Agent dispatch/terminal ownership.
- `ba8ab60` closes the scheduled Agent dispatch/terminal lifecycle slice in `ScheduledTasksModule`; Agent/upstream guards, bounded retry/concurrency and shutdown are feature-owned. Remaining C-2/C-3 work is route census/global composition removal and the non-worker session/run paths.
- `ba8ab60` extends Chat business-read cutover to `project_ref` collection/session/message/parts/process reads through the shared Project owner. Remaining route TODO is limited to the non-Chat session/run families and LegacyRoutes/global composition deletion proof.
- `ba8ab60` moves the Scheduler callback route into `ScheduledTasksModule` with one canonical task service, receipt repository and scheduled-Agent repository; the next route slice remains scheduled-task CRUD/current owner mutation and remaining global composition cleanup.
- `ba8ab60` extends the scheduled-task feature slice through create/update/delete/retry and project-scoped create mutations. `e1f2b81` extends the ProjectsModule slice through project create/instruction commands and project tasks reads, with a feature-owned idempotency provider and no second Project owner; Nest and raw `createBffServer` share one project mutation adapter.
- `e1f2b81` completes the scheduled mutation adapter split: `scheduled-task-mutation-native.ts` is shared by Nest and raw `createBffServer`, and the duplicate `live-bff.ts` dispatcher is deleted. The remaining deletion gate is the broader LegacyRoutes/global-composition census, not another scheduled-task implementation.
- `e1f2b81` moves personal Billing summary/ledger/credit-account/plans/checkout into `BillingModule`; the owner Billing branches are deleted and the route keeps one feature-local persistent receipt seam. Remaining work is the other owner route families plus LegacyRoutes/global composition removal.
- `e1f2b81` moves `GET /v1/models` into `SystemModule` with one shared owner projection adapter and deletes the `owner.ts` branch. Remaining work is the other owner projection routes plus LegacyRoutes/global composition removal.
- `e1f2b81` moves MCP Server/Connection projections into `McpModule`, deletes the owner Platform projection branch, and isolates retired System/Skills errors in a dedicated adapter. Remaining work is the other MCP/Skills owner surfaces plus LegacyRoutes/global composition removal.
- `e1f2b81` removes the obsolete `owner.ts` route module by retaining only the explicit `owner-request.ts` transport helper used by System/Music; no generic `liveOwnerBusiness` dispatcher remains.
- `e1f2b81` moves the browser-private Personal MCP surface into `McpModule` with a narrow provider and no new global composition dependency; remaining route census now centers on Library/personal-file and residual Skills/LegacyRoutes paths.
- `e1f2b81` moves Library/artifact/personal-file routes into `AccountModule`, deletes the duplicate raw server branches, and adds feature-owned artifact/idempotency providers. Remaining route census is residual Skills plus LegacyRoutes/global composition deletion.
- `7cf1312` terminates unknown `/v1/system/*` and `/v1/skills/*` requests in the owning `SystemModule`/`SkillsModule` through the dedicated retired-owner adapter, with the same IAM admission and explicit 503 error mapping; these requests no longer fall through to `LegacyRoutes`.
- `86c714b` restores the named `SkillShareRepository` seam for raw/test compositions through the existing compatibility extractor; the shared-revision specification contract is green at 110/110 without introducing another repository owner.
- `34899e0` reuses that named seam when constructing the raw exact-download source, closing the Project exact-download compatibility gap at 18/18 without adding a duplicate owner.
- `a725bdc` closes the last raw/test route seams for System admin and public Share while preserving native Skills admin termination; BFF full validation is now 2315/2315 with two environment skips.
- `b7b30e5` moves browser Custom API CRUD into `McpModule` with one named client provider shared by Custom API and Project MCP recommendations; no second Platform client is constructed.
- `a09176a` narrows ScheduledTask mutation authorization/execution to named Project/ScheduledTask providers and removes those production route consumers from the global `BffBusinessStore.services` aggregate.
- `06ae1a6` narrows the Scheduler callback to the same explicit `SchedulerDispatchProvider`, removing its production `source.services.scheduledTasks` unwrap.
- `3c27f97` deletes the retired Project resource upload dispatcher and duplicate tests; canonical Project feature handlers remain the only upload owner.
- `8df63bb` deletes the LegacyRoutes Nest composition and shutdown bridge; feature middleware is now the sole production Nest route graph, while raw `createBffServer` remains test/compatibility-only.
- `2d1103f` removes a `BffApplicationServices` type mirror from Skill specification and keeps the dependency at the Project owner boundary.
- Current next TODO is unchanged in scope: migrate the remaining session/run and owner route families, then complete provider/Port import census before deleting global composition. Re-run the BFF focused gates after each route bundle and keep A-01/A-02/A-07 stopped.
- Native-session focused revalidation remains green on the current checkout (IAM 3/3; App native/session/account/team/sign-in/out focused 167/167); this does not replace the missing IAM_TEST_ADMIN_URL/Redis real host and cross-owner tenant-switch/revocation journey receipts.

- `630efbf` adds a negative LegacyRoutes boundary for the already migrated Chat paths. This is an adapter bypass, not the Chat bundle completion: the old dispatcher still owns Chat POST/events/title/delete/share and project-scoped reads.
- `3961450` established the direct Chat mutation seam; `ff14c86` extends it to project-scoped title/delete/share through a shared `ProjectAccessModule`, avoiding a second ProjectService owner.
- `76b9402` established the direct events stream; `ff14c86` extends it to project-scoped events and moves Chat POST through the same owner/provider graph. The LegacyRoutes projector worker remains transitional.


### 2026-11-01 execution update

- `045dbf7` moves `PublicShareRepository` to the Chat feature boundary; `03940f9` moves `SkillShareRepository` to the Skills feature boundary. Both slices preserve the single PostgreSQL implementation and add architecture assertions against restoring global port files.
- The next C-3 step remains an evidence-based per-port audit. Do not move shared idempotency or outbox contracts without proving an exclusive owner; do not delete raw compatibility composition until route/provider import census and C-4 owner gates are green. A-01/A-02/A-07 remain stopped.

### 2026-11-01 execution update (Account/Skills ports)

- `758d58f` localizes the Account Personal Knowledge port; `224a624` localizes the Account Library Artifact port; `03940f9` localizes the Skills Share port. The moves are type/import-boundary changes only, with single-owner PostgreSQL implementations and negative architecture assertions.
- Keep the next pass evidence-driven: classify remaining global ports as true cross-feature contracts versus feature-owned seams before moving or deleting them. Do not touch A-01/A-02/A-07 or claim C-3/C-4 completion until raw compatibility, route census, and owner full-gate evidence are closed.

### 2026-11-02 execution update

- 新增 `docs/superpowers/evidence/2026-10-31-task-a-c1-c3-inventory.md`，冻结 route/provider ownership、C-3 keep/move/delete 决策与 C-4/E2E 阻塞项。
- BFF child `0b65b918b96664ec5285998c5e87450b30533879` 将公开合法 `GET /v1/agents/connections/setup` 从 generic raw fallback 切到具名 Agent setup adapter：严格校验 platform/query/body、IAM admission、disabled fail-closed（`agent_not_configured`）、enabled owner identity headers 与响应投影。
- 验证：BFF build、focused BFF/architecture/Nest tests **95/95**、lint、diff-check 通过；BFF full test、真实 kokoro-agent setup owner receipt、Root/跨仓 E2E 仍未完成。
- C-2/C-3/C-4 与 A-01/A-02/A-07 状态不变：继续停写 `handleBffRequest`/`createBffComposition`/`PostgresBffRepositories` 的删除，先完成剩余 raw session/run 与 fixture/provider census，再串行全量验证。

### 2026-11-02 execution update (Chat compatibility chain)

- BFF child `bb1fa5e8a7fd4959a113afd0cbcf8d013d1b7ff` routes Chat mutation, AG-UI events, Chat message submission and regeneration through the existing Chat/AgentRuns/Agui feature adapters before raw fallback. Mock `routeHandler` remains an explicit test seam.
- Focused verification: BFF build plus BFF/Chat/regeneration/Nest suite **65/65**, lint and diff-check passed. `handleBffRequest` and `PostgresBffRepositories` remain open until raw integration fixtures and provider import census are migrated.

### 2026-11-02 execution update (Agent control compatibility chain)

- BFF child `393b9d5bd67f07e8b4c87b81f6c594f848621fee` adds the AgentRuns-owned control adapter to raw `createBffServer`; the route is verified through a real raw server fixture rather than only the mock `routeHandler` seam.
- Focused verification: build plus Agent control/raw compatibility/Nest architecture **68/68**, lint and diff-check passed. Remaining C-2/C-3 work is the zero-consumer proof for `handleBffRequest`, raw global composition and remaining session/run/fixture references; C-4 full owner gates and cross-owner E2E remain open.
- App native-session audit confirms first-party runtime cutover is complete at source level, but real IAM→BFF→App login/tenant-switch/sign-out/revocation receipts remain an environment gate. A-01/A-02/A-07 stay stopped.

### 2026-11-02 execution update (App config and C-4 gate)

- App child `b0919ffc20fe4ba3b281a8150aee503e1744a274` removes stale legacy auth environment comments from the five active templates; architecture **50/50** and lint pass. Runtime native-only evidence is stronger, but real cross-owner receipts remain an environment gate.
- BFF child `062f93ff6ed249c45843bfec360fc9267104e1b9` removes deleted LegacyRoutes/global-port/service paths from `format:check`; the command now reaches the existing 30-file formatting warning baseline instead of missing-file errors. Do not claim format green until those warnings are separately owned and fixed.
- C-3 census confirms only shared idempotency remains under `src/application/ports`, while `PostgresBffRepositories` and raw compatibility fixture consumers remain. Next work is to classify/freeze the five raw fallback surfaces and migrate or explicitly retain their fixtures before deleting raw composition; A-01/A-02/A-07 remain stopped.

### 2026-11-02 execution update (browser MCP/custom API compatibility chain)

- BFF child `562817cb70b7eb09f162929b4f665a5b85b5bc04` shares the Personal MCP and Custom API feature entrypoints between Nest middleware and raw `createBffServer`; raw requests no longer reach the generic `handleBffRequest` MCP/custom-api branch.
- Focused verification: build plus Custom API/Personal MCP/icon/Nest architecture **127/127**, lint and diff-check passed. Remaining raw fallback categories are internal Scheduler dispatch, residual unknown sessions/run, retired-owner handling and generic upstream proxy; raw composition deletion still waits on fixture/provider census and owner gates.

### 2026-11-02 execution update (residual session/run fallback)

- BFF child `e8e7207a3d7d1bbbc9a4f35bb502138754f0e2d6` terminates unknown live `/v1/sessions/**` paths before the raw session fallback, with a raw regression proving canonical 404 and known Agent control/Chat paths unchanged.
- `liveAgentSession` remains a named adapter implementation for AG-UI events and Agent control; only the `handleBffRequest` residual unknown-session fallback is closed. Remaining C-2/C-3 work is internal Scheduler callback, retired-owner/generic-upstream compatibility and fixture/provider migration before raw composition deletion.

### 2026-11-02 execution update (Scheduler and retired-owner raw cutovers)

- BFF child `07584d25cd531cef472ec668ee1cab688ff1800b` routes raw Scheduler callbacks through the shared feature-owned `schedulerDispatch` entrypoint and deletes the duplicate `handleBffRequest` scheduler branch. Raw provider-null/routeHandler semantics and request-id behavior are covered by focused tests; no generic proxy or second Scheduler owner was added.
- BFF child `1f5e2cd50707c7d3e622e3428cc2dff2c66ca170` routes unknown raw System/Skills paths through `handleRetiredOwnerRawRequest`, preserves the explicit historical Skill 404 shapes, and deletes the retired-owner business branch from `handleBffRequest`. Nest retired-owner middleware remains the production feature boundary; raw `createBffServer` remains compatibility-only.
- Main-checkout revalidation: BFF build/typecheck/lint/diff-check, mock contract **28/28**, architecture/Nest suite **69/69**, and Scheduler identity/outbox/receiver **28/28** pass. `pnpm format:check` and full BFF test remain non-green only on the recorded pre-existing warning/fixture baseline; no C-4 pass is claimed.
- Remaining C-2/C-3 deletion gate is unchanged: generic configured-upstream compatibility, raw integration fixture/provider census, `createBffComposition`/`handleBffRequest`/`PostgresBffRepositories` zero-consumer proof, then serial owner/root full gates. C-1.3 real IAM→BFF→App receipts and E2E service startup remain open; A-01/A-02/A-07 stay stopped.

### 2026-11-02 execution update (full-gate diagnostic and fixture census)

- BFF `pnpm test` after child `1f5e2cd` remains non-green: 1177 tests started, 1043 passed, 21 failed, 113 cancelled after the existing Skill shared-revision/archived owner fixture failures and a long pending `test/contract/skill-specification-http.test.mjs`. This is a diagnostic baseline, not a C-4 pass; no assertions or timeouts were weakened.
- Read-only `PostgresBffRepositories` census found only raw runtime production construction, plus nine integration suites with 102 direct constructors, 17 raw database pool/notify accesses, and 10 stale `store.services.*` fixture accesses. Next C-3 slice is a test-only owner fixture factory under isolated PG/Redis; wrapper deletion stays blocked until all imports and direct aggregate accesses are gone.

### 2026-11-02 execution update (generic owner fallback)

- BFF child `6f9cc641d59d10b7778985aefb61d8e7cbe54f42` terminates unknown raw Agent/Billing paths with canonical 404 after named adapters and proves configured upstreams are not called. Exact setup/personal routes and mock route-handler seams remain unchanged.
- Main-checkout revalidation is green for BFF build/typecheck/lint/diff-check, mock contract **29/29**, and architecture/Nest **70/70**. Remaining C-2/C-3 work is compatibility fixture/provider migration and any explicitly justified configured-upstream suffix; C-4/full owner and real C-1.3 receipts remain open.

### 2026-11-02 execution update (E2E readiness)

- 当前本地仅有受管 PostgreSQL/Redis 与既存 MinIO/Mailpit/ClamAV 依赖容器；IAM/BFF/App/Agent/System/Billing/Storage/Scheduler/Capability/Admin 未启动，且缺少本轮 `IAM_TEST_ADMIN_URL`、隔离 PG/Redis 测试 URL。C-1.3 real journey、C-4 integration/E2E 继续保持 open；不伪造服务 receipt，不执行破坏性 schema/资源操作。

- Readiness audit 已冻结启动依赖：隔离 PG/Redis → IAM → System/Capability/Storage/Billing/Scheduler → BFF → Agent HTTP/worker → App → Admin；当前所有应用进程未启动，缺少 test admin URL、owner schema/namespace 与 service credentials。恢复这些外部条件前，C-1.3/E2E 只能保持阻塞记录，不进入 A。

- `pnpm format:check` after `6f9cc64` reports 31 existing warnings (including `server.ts`, `scheduler.ts`, and architecture files) with no missing paths. Do not reformat unrelated files or mark C-4 green until the warning set is separately owned.

### 2026-11-02 execution update (App typecheck baseline)

- App child `f5d122bb41beb3e141015b758411dbcc0afc583b` removes the stale reconnect-status prop from the App frame boundary. Typecheck/lint/architecture **50/50** are green; this does not substitute for real native-session receipts or E2E service readiness.

- IAM static recheck: lint/typecheck/contracts/SDK/120-file test suite (**1561/1561**) and build pass; `pnpm verify` remains format-blocked by the existing `test/integration/bff-session-admission-host.test.ts` warning. Real IAM admin/PG/Redis receipt evidence is still unavailable.

### 2026-11-02 execution update (named PersonalKnowledge fixture)

- BFF child `24e157bb023b5132c59fdd153af1c608134c0ee2` removes the stale PersonalKnowledge global-service fixture accesses without adding an alias. Focused contract/input/HTTP tests pass and integration cases are explicitly skipped without isolated PG/Redis.
- App full test remains a contract-artifact digest mismatch baseline; do not regenerate pinned public artifacts in this cleanup slice. Keep C-4 open until owner artifact provenance is reconciled and the serial suite is rerun.

### 2026-11-02 execution update (named PublicShare fixture)

- BFF child `4af24bf` removes four stale global-service fixture accesses in Message-parts/AG-UI integration tests by using the existing named PublicShare application service. Resource-gated SQL cases remain skipped without isolated PG/Redis; no C-3 owner boundary was widened.

### 2026-11-02 execution update (production owner-resource factory)

- BFF child `673306e5e6c889c8bfbfde02933de1253b4f3034` removes the production runtime dependency on `new PostgresBffRepositories` by introducing a named PostgreSQL owner-resource graph. The compatibility wrapper remains only for raw/integration consumers until their fixtures are migrated.
- Main-checkout focused verification: BFF build/typecheck/lint/diff-check, mock contract **29/29**, architecture/Nest **70/70**. C-3 wrapper deletion and C-4 full integration remain open; A gates stay stopped.

### 2026-11-02 execution update (fixture migration and wrapper deletion)

- Child `c6c2aa6e88e2b6fdb53517b38bc527118f537e0d` migrated the nine PostgreSQL integration suites from the old aggregate to `createPostgresBffOwnerResources` without changing SQL, cleanup, worker, or receipt behavior. The resource-gated run was **6 pass / 223 skip / 1 pre-existing baseline failure** because isolated PG/Redis URLs are absent.
- Child `8150106dc11676817daca57c6ecbf956fdf283d3` deleted the now-unreferenced `PostgresBffRepositories` class and added a negative architecture assertion. Root revalidation after pin: topology PASS; governance **1846 passed / 3 skipped / 502 subtests**; BFF build/typecheck/lint/mock29/architecture70 pass. C-3 wrapper deletion is closed; C-2 raw composition and C-4/E2E remain open.
- Child `88538a88f3849e8aaeb2777d755f9b4616885ab4` adds a raw-chain negative guard for unknown `/v1/models/**` suffixes; canonical `GET /v1/models` remains the only model route. Focused BFF/Nest/Root gates are green; generic compatibility and full owner/E2E gates remain open.
- Child `dfe1584eceb8151edfd6ac5871810142108eeb1c` adds the analogous guard for unknown `/v1/library/**` suffixes; canonical Library routes remain unchanged and Storage is not called for undocumented paths. Focused BFF/Nest/Root gates are green; raw businessStore/provider seams and C-4/E2E remain open.

- 主方随后重跑 BFF `pnpm test`：**1178 tests / 1044 pass / 21 fail / 113 cancelled / 0 skip**；`test/contract/skill-specification-http.test.mjs` 长 pending 后中止，失败仍为既有 archived-tasks/Skill shared-revision fixture baseline。该结果不计 C-4 通过，也未修改断言或 timeout。

### 2026-11-02 generic-tail closure

- `a86ecae` removes the unreachable generic configured-owner proxy tail from `handleBffRequest`; named adapters/guards own all currently known owner prefixes, and the residual fallback returns canonical 404 while committing/releasing idempotency state.
- Archived/Shared Tasks raw fixtures use explicit `chatService`; this closes two stale aggregate-shaped fixture seams without changing production contracts.
- Re-run Root topology/governance after pin. Keep C-1.3 real receipts, owner full gates, isolated PG/Redis integration, and E2E startup as open gates; do not enter A-01/A-02/A-07.

### 2026-11-02 SkillShare provider migration

- Migrate shared-summary fixture consumers to the existing top-level `skillShareRepository`; keep the disconnect cancellation case intact and rerun it separately.
- After Root pins `13319aa`, rerun topology/governance and then the complete BFF owner gate. Do not treat the 110-case focused result as C-4 completion; A-01/A-02/A-07 remain stopped.

### 2026-11-02 AgentRuns fixture migration

- Keep the internal AgentRuns adapter as the owner boundary and migrate only fixture shape (`submittedAgentRuns` top-level, `businessStore: null`).
- Re-pin Root, rerun topology/governance, then repeat the BFF full diagnostic; do not call focused model-admission tests an owner E2E receipt.

### 2026-11-02 PublicShare fixture migration

- Keep public sharing on the Chat-owned `publicShareService`; migrate only the two raw User-admission fixture seams and preserve anonymous/fallback projections.
- Re-pin Root and rerun the owner/full diagnostic; do not broaden into the exact-download fixture that still requires a non-null owner resource graph.

### 2026-11-02 Skill-import shell cleanup

- Keep the receipt/idempotency seam because the fixture exercises durable replay; remove only empty aggregate placeholders and do not infer a new owner provider.
- Re-pin Root and continue the remaining provider census; no A gate movement.
