# Task A C-1.3～C-4 收敛实施方案

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents are available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在进入 A-01/A-02/A-07 前，完成 C-1.3 first-party native-session 链路、BFF LegacyRoutes 全量退出、Repository/Service/Port feature-local 收敛，并以 Root/子仓全量门禁证明当前态已达到 C-1～C-4 完成条件。

**Architecture:** IAM 是唯一 native session、active tenant、membership、permission owner；App 只做同源 cookie adapter；BFF 在 HTTP boundary 一次完成 native admission 并冻结 subject/tenant/session context。BFF 以 Nest `AppModule` 为唯一 composition root，先按业务切片把 LegacyRoutes 中的 route ownership 下沉到 feature Controller → Service/use case → 必要的 feature-local Repository/owner Client，最后删除 LegacyRoutes、旧 dispatcher 与 global composition wrapper。

**Tech Stack:** Node 24、NestJS 12、Express adapter、TypeScript、Zod、PostgreSQL/Redis、现有 generated OpenAPI/Connect clients、Vitest/Node test、Root topology checks。

---

## 0. 当前基线与停写边界

**停写基线：** Root `1c63b007`，工作树 clean（子仓 App `4c41104d`、BFF `65cf2082`、IAM `108beedf`）。

**已交付事实：**

- G0 native-session contract 已固定：version `1.0.0`，digest `5cf59df4b7bd9853edfd2eabb31afc236c0ec0db371f9737706fc129484fd83f`。
- IAM runtime：child `108beedf`，新增 native admission controller/service/schema、direct credential profile、Cookie/Origin/body/header 校验和 fresh session projection，并接入 account/Team owner native proof。
- BFF native consumer：child `65cf2082`，新增 direct credential reader、native transport/client、Cookie allowlist、AccountModule/runtime wiring 和 owner transport forwarding。
- BFF Nest foundation/feature graph/ownership slices：`3f643ef`、`cd4ffb1`、`aacf1c5`、`6a42bd3`、`eefe02a`、`c9263cd`。
- 当前 BFF 全量：2301 pass / 2 skip / 0 fail；IAM unit：1403 pass；Root topology/diff-check 通过。

**C-1.3 owner cutover design gate (now fixed):** Account profile/profile update, account sessions, and Team are owner operations, not browser relays. The BFF sends the allowlisted IAM cookie, fixed configured Origin, request id, and the BFF `session_admission` direct credential. IAM authenticates that service identity, verifies the fresh issuer session/active tenant/membership/session id, and creates a marked native user principal. Account self operations retain Product tenant/session/CAS/transaction/Audit checks while skipping OAuth grant lookup only for the marked native proof; Team owner repositories recheck persisted role permissions in their existing snapshot. Legacy bearer remains only on uncut consumers and native requests fail closed rather than manufacturing a bearer. No DTO/schema/version change is introduced by this additive auth mode.

**明确未完成：**

- App 同源 native adapter、旧 Auth.js/OIDC RP、Product Session store/refresh reservation 尚未删除。
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
- Inspect only: `apps/kokoro-bff/src/modules/legacy-routes/legacy-routes.runtime.ts`
- Inspect only: `apps/kokoro-bff/src/bootstrap/runtime.ts`, `apps/kokoro-bff/src/bootstrap/server.ts`, `apps/kokoro-bff/src/application/ports/**`

- [ ] 列出每条 LegacyRoutes path/method 的当前 handler、目标 feature、依赖、测试、迁移状态。
- [ ] 列出 `BffBusinessStore`、`BffApplicationServices`、`PostgresBffRepositories` 的字段/方法及生产消费者。
- [ ] 对 `src/application/ports/**` 逐项标记 keep/move/merge/delete，并记录真实事务/锁/CAS/lease/outbox/owner boundary 证据。
- [ ] 为每个 slice 写明“从 adapter 删除的具体 path”和最低验证命令；没有 route/消费者证据的 slice 不进入实现。

### Task 2：完成 App native adapter，再关闭 C-1.3

**Files:**

- Modify: `apps/kokoro-app/src/**` native same-origin adapter and request context
- Delete after consumer proof: `apps/kokoro-app/src/app/api/auth/[...nextauth]/route.ts`, `src/lib/server/oidc-*`, first-party OAuth relay/token helpers（以实际 inventory 为准）
- Delete after adapter proof: Product Session cookie/store、refresh reservation 与只保护旧 RP 的 tests
- Test: App native adapter、sign-in/sign-out、tenant switch、revocation/multi-tab/late response

- [ ] 先补 native adapter contract tests，证明浏览器 Authorization/body tenant 不会跨 boundary。
- [ ] 接入 BFF native admission，保持 request-id、Origin、Cookie allowlist 与取消预算。
- [ ] 实测登录、登出、active tenant 切换、撤权后的 401/403 与多标签 late response。
- [ ] 只有消费者证据成立后才删除旧 RP、Product Session 与 token/refresh 测试。
- [ ] 运行 App focused lint/typecheck/test；记录既有 `onReconnect` baseline，不扩大修复范围。

### Task 3：Account/Projects 第一批真实 route 下沉

**Files:**

- Modify/Create: `apps/kokoro-bff/src/modules/account/**`
- Modify/Create: `apps/kokoro-bff/src/modules/projects/**`
- Modify: `apps/kokoro-bff/src/modules/legacy-routes/legacy-routes.runtime.ts`
- Modify: corresponding `src/http/routes/account-*.ts`, `project-*.ts`, `test/**`

- [ ] 选取 route bundle（Account profile/sessions 或 Project read/rename/pin）并先写 red HTTP/architecture tests。
- [ ] 将 raw input/context/error mapping 放入 Controller，业务规则放入 Service/use case，真实 CAS/事务放入 named Repository；owner call 保持 integration client 边界。
- [ ] 在 AppModule/feature module 注册 provider，测试注入 seam，不再从 `createBffComposition()` locator 取服务。
- [ ] 从 LegacyRoutesRuntime 移除已迁移 path，并添加“该 path 不再由 adapter 处理”的回归断言。
- [ ] 运行 format/lint/typecheck/build、feature focused tests、`test:nest-architecture`、`test:architecture`。

### Task 4：Chat/AgentRuns/AG-UI 与 ScheduledTasks 下沉

**Files:**

- Modify/Create: `apps/kokoro-bff/src/modules/chat/**`, `agent-runs/**`, `agui/**`, `scheduled-tasks/**`
- Modify: `src/application/agui/**`, outbox/dispatcher providers only where ownership moves
- Modify: `src/modules/legacy-routes/legacy-routes.runtime.ts`
- Test: corresponding HTTP/ledger/replay/outbox/cancel/lease tests

- [ ] 保留 durable ledger、cursor/replay、lease/CAS/outbox、取消和 drain 顺序；不复制 AG-UI envelope。
- [ ] 将 Chat/Run/AG-UI repository/client 拆成 feature-local provider；只对有真实复杂边界的 repository 保留独立类型。
- [ ] 每个 route bundle 迁移后从 adapter 删除并执行 focused HTTP + architecture tests。

### Task 5：剩余 feature route 与 LegacyRoutes 删除

**Files:**

- Modify/Create: `skills/**`, `mcp/**`, `system/**`, `billing/**`, `music/**`, `iam-relay/**`
- Delete after zero-route proof: `src/modules/legacy-routes/legacy-routes.runtime.ts`, `legacy-routes.module.ts`, `legacy-routes.middleware.ts`
- Delete after provider graph proof: old `src/bootstrap/server.ts` business dispatcher and `src/bootstrap/runtime.ts` global composition paths

- [ ] 以 Task 1 inventory 为序迁移，不新增 route/alias/fallback。
- [ ] 每一批完成后更新 route census；census 为零前不删除 adapter。
- [ ] 删除旧 listener/dispatcher 后运行 source-runtime architecture gate，证明唯一 Nest listener 和唯一 composition root。

### Task 6：C-3 Repository/Service/Port 收敛

**Files:**

- Move/Modify: `apps/kokoro-bff/src/application/ports/**` → feature-local ports
- Modify/Delete: `src/infrastructure/postgres/repositories.ts`, `src/application/services.ts`, `src/application/ports/bff-business-store.ts`
- Modify: feature module providers/tests/architecture oracle

- [ ] 先按 inventory 移动有真实 owner boundary 的 port，不改行为。
- [ ] 单实现、无边界的 Service 并入 feature Service/Provider；只转发一次的 Port 删除并把测试绑定公开行为。
- [ ] `BffBusinessStore`/`PostgresBffRepositories`/`BffApplicationServices` 不再出现在生产 composition 后，删除旧 wrapper。
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
# IAM
cd apps/kokoro-iam && pnpm format:check && pnpm lint && pnpm typecheck && pnpm contract:check && pnpm test:unit && pnpm build
# BFF
cd ../kokoro-bff && pnpm format:check && pnpm lint && pnpm typecheck && pnpm build && pnpm test:nest-architecture && pnpm test:architecture && pnpm test
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

- [ ] C-1.3：App native adapter、BFF native consumer、IAM runtime、sign-in/sign-out/tenant-switch/revocation 证据齐全；旧 first-party RP/Product Session 已删除。
- [ ] C-2：唯一 Nest listener、唯一 AppModule composition root；LegacyRoutes 与旧 dispatcher 删除。
- [ ] C-3：global Repository/Service/Port 只剩有证据的 feature-local boundary；global locator/wrapper 删除。
- [ ] C-4：默认测试只覆盖 canonical 当前态；owner/root 全量门禁通过；证据文档更新完成。
- [ ] A-01/A-02/A-07：仅在上述四项均通过后另建实施计划并开始。

