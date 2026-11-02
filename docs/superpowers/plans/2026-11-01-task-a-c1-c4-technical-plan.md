# Task A C-1.3～C-4 闭环 Technical Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在不进入 A-01/A-02/A-07 的前提下，完成 Task A 的 C-1.3 native-session 真实收据、C-2/C-3 BFF 边界与 fixture 清理、C-4 Root/owner 全量验证，并形成可重复的端到端闭环证据。

**Architecture:** Browser 只经 App same-origin adapter 进入 BFF；BFF 的 Nest feature middleware 是生产 owner boundary，raw `createBffServer` 仅保留有证据的兼容/测试入口。BFF-owned Chat/Projects/ScheduledTasks/AgentRuns/Skills/Account 通过显式 provider 组合，跨请求事实由 owner 的 PostgreSQL/Redis 与幂等 receipt 保存；未知 owner suffix 终止为 canonical 404，不再 generic proxy。

**Tech Stack:** TypeScript/Node.js, NestJS, pnpm, PostgreSQL, Redis, Connect/HTTP generated clients, Python Root governance scripts, isolated local E2E resources.

---

## 0. 设计门结论与当前基线

### 0.1 组合身份

- Root worktree：`/Users/nako/.codex/worktrees/task-a-c1-cleanup/Kokoro`
- Root branch：`codex/task-a-c1-cleanup`
- Root HEAD（本计划冻结时）：`c59bcf54`（后续只更新本计划、TODO 和经批准的窄切片）
- BFF：`228e3d691f6b5c93575950babb3d9f4c6b409c0a`
- App：`f5d122bb41beb3e141015b758411dbcc0afc583b`
- IAM：`a1457be836c21eb558c8cbf7d9366e60f8ce59b8`

### 0.2 已关闭的 C-2/C-3 切片

- raw Scheduler callback、retired System/Skills、unknown sessions、unknown Agent/Billing/Model/Library suffix 已走 named adapter/guard。
- raw generic configured-owner proxy tail 已删除；未处理路径通过 `reply(..., 404, ..., mutation)` 结算幂等票据。
- `PostgresBffRepositories` compatibility class 已删除；9 个 PostgreSQL integration suites 使用 `createPostgresBffOwnerResources`。
- `src/application/ports` 仅保留 `idempotency-repository.ts`；LegacyRoutes 生产 composition 已不存在。
- Archived/Shared Tasks、Skill shared-summary、Model admission/recovery/settlement、User-admission Share、GitHub Skill import、Project Skill content fixtures 已迁移到显式 owner provider 或最小 receipt seam。

### 0.3 当前验证事实

- BFF full `pnpm test`（在 `228e3d6` 上）：**2298 tests / 2296 pass / 0 fail / 0 cancelled / 2 skipped**。
- C-4 两个行为失败均已修复：denied MCP icon mutation 在授权拒绝后零 Platform command；Skill installation Chat invalid-owner 场景通过显式最小 receipt seam 保持 `502/skill_installation_response_invalid`。
- BFF `pnpm format:check`：当前列出 32 个文件 warnings（含本轮已触及文件）；本计划不做无关格式扫尾。
- App static gates：`typecheck`/`lint`/`test:architecture` **50/50**；full `pnpm test` 当前 **6316 pass / 50 fail / 353 files**，失败集中在 pinned BFF artifact/version drift。
- IAM static gates：child `a1457be` 发布 native-session SDK 生成物（含 `ReadAccountProfile`、`VerifyNativeSession` 与错误码）；format/lint/typecheck、SDK check、contract gates 与 `pnpm verify` 均通过：**120 files / 1561 tests / build PASS**。
- Root topology：最新 pin 后 `verify-repository-topology.py` PASS；Root governance 最近有效证据为 **1846 passed / 3 skipped / 502 subtests**，BFF `0a22f4d` pin 后仍需再次串行复核。
- 真实 C-1.3/E2E：当前只有受管 PostgreSQL `127.0.0.1:5432` 与 Redis `127.0.0.1:6379`；IAM/BFF/App/Agent/owner 进程未启动，`IAM_TEST_ADMIN_URL`、`KOKORO_TEST_POSTGRES_URL`、`KOKORO_TEST_REDIS_URL` 未提供。

---

## 1. 问题清单（按闭环阻断顺序）

| ID | 问题 | 影响 | 处理策略 | 状态 |
| --- | --- | --- | --- | --- |
| I-01 | 缺少隔离 IAM admin URL、PG/Redis URL、service credentials、owner URLs | C-1.3 login/tenant-switch/sign-out/revocation 无真实 receipt；integration/E2E 不能验收 | 先补环境输入与隔离资源；不重置共享资源、不生成凭据 | OPEN / external prerequisite |
| I-02 | MCP denied icon mutation 在授权拒绝后仍调用 Platform | C-4 行为回归；存在越权副作用风险 | `228e3d6` 在 mutation owner dispatch 前补 `manage` action admission；focused 42/42，full 0 fail | DONE |
| I-03 | Skill installation Chat invalid owner response 映射成 `chat_unavailable` | C-4 错误契约不闭合，掩盖 `skill_installation_response_invalid` | `228e3d6` 将 fixture 补为完整 receipt seam，保留 typed owner error 映射；focused 24/24，full 0 fail | DONE |
| I-04 | BFF 32 个 format warnings | BFF/C-4 format gate 非绿 | 只处理受影响文件；禁止全仓格式化扩散 | OPEN |
| I-05 | App pinned artifact digest drift | App full contract gate 非绿 | 追溯生成物 provenance；未经 owner 裁决不刷新 hash/生成物 | OPEN |
| I-06 | IAM `pnpm verify` 在 SDK 生成物 drift 停止 | native-session API 已进入 OpenAPI，SDK 生成物需同步 | `a1457be` 重新生成并校验 SDK，`pnpm verify` 120/1561/build PASS | DONE |
| I-07 | 真实 owner full gate 与 E2E 尚未串行跑完 | 无法宣称 Task A 或 C-4 完成 | 依序启动隔离 owner，收集 health/receipt/E2E evidence | OPEN |
| I-08 | A-01/A-02/A-07 依赖 C-1～C-4 | 提前进入会造成边界漂移 | 保持停写，直到所有 C gate 证据齐全 | STOPPED |

---

## 2. 目标与验收定义

### Goal（机器目标，保持 ACTIVE）

> 完成 Task A 的 C-1.3～C-4 闭环：有真实 IAM native-session login/tenant-switch/sign-out/revocation receipt；BFF feature ownership、LegacyRoutes/global composition/无边界 Repository/Service/Port 清理完成；Root、BFF、App、IAM 与跨仓 E2E 按顺序通过或对失败给出可复现证据。A-01/A-02/A-07 在此之前保持停写。

### 完成判定

1. C-1.3：真实隔离环境中完成 login → active tenant switch → sign-out → revoked session；PG/Redis receipt、IAM/BFF/App request-id 与撤权结果可关联。
2. C-2/C-3：生产 Nest chain 无 LegacyRoutes/global aggregate；raw compatibility 只剩有文档、测试和退出条件的 seam；fixture/provider census 证明无旧 `businessStore.services.*`、无 `PostgresBffRepositories` 新消费者。
3. C-4：BFF full、App full、IAM verify、Root topology/governance、受影响 owner gates 均有命令、版本、结果；失败必须分类为新失败、既存失败或环境缺口。
4. E2E：依赖 owner 启动顺序、健康探针、关键旅程与失败恢复均有本地证据；不以 fixture/mock/static 代替真实链路。
5. 只有以上 1～4 全部完成后，才建立 A-01/A-02/A-07 的新计划。

---

## 3. 目标架构与闭环逻辑

```text
App native session
  -> same-origin adapter (/api/session, /api/signout, tenant switch)
  -> BFF IAM native-session admission
  -> named BFF feature adapter / Nest middleware
  -> owner API/RPC (Agent/System/Billing/Storage/Scheduler/Capability)
  -> owner PostgreSQL/Redis transaction + idempotency receipt
  -> BFF durable ledger/cursor/replay
  -> App UI state
```

- **认证事实**：tenant、actor、subject 只来自 IAM admission；body/header 自报身份不得参与授权。
- **幂等事实**：mutation 先 claim，再 owner command；成功 `putReceipt`，失败 release；未知 ACK 保持可恢复，不伪造成功。
- **路由事实**：canonical route 由 named adapter 处理；未知 owner suffix 404；不再 generic proxy。
- **数据事实**：每个 owner 只访问自己的 schema/Repository；BFF 只通过 owner API/RPC，不读取他人 DB。
- **恢复事实**：服务重启通过 receipt/cursor/replay 恢复；取消/超时不产生迟到响应或重复 owner command。

---

## 4. 分阶段执行计划（后续按 TODO 逐项更新）

### Chunk 1：修复 BFF 两个剩余行为失败

**Files:**
- Modify: `apps/kokoro-bff/src/http/routes/mcp-personal.ts` 或其 named middleware/adapter（以测试调用栈为准）
- Modify: `apps/kokoro-bff/test/mcp-personal-http.test.mjs`
- Modify: `apps/kokoro-bff/src/http/routes/chat-message-native.ts` / `apps/kokoro-bff/src/http/routes/chat.ts`（仅在调用栈确认错误映射 owner 后）
- Modify: `apps/kokoro-bff/test/skill-installation-http.test.mjs`

- [x] Step 1：单独运行两个失败用例，保存调用顺序、admission 结果、owner call count 与 response envelope。
  - Run: `pnpm exec tsx --test --test-name-pattern='denied icon mutation reaches no Platform command' test/mcp-personal-http.test.mjs`
  - Run: `pnpm exec tsx --test --test-name-pattern='Project installation six routes' test/skill-installation-http.test.mjs`
- [x] Step 2：为每个失败补/确认最小 RED 断言：denied icon `ownerCalls === 0`；invalid installation owner response 映射 `502/skill_installation_response_invalid`。
- [x] Step 3：只在 named adapter 内修 admission→owner dispatch 或 typed error mapping；不改通用 catch、timeout、断言和路由范围。
- [x] Step 4：运行两套 focused tests、BFF build/typecheck/lint/diff-check。
- [x] Step 5：提交独立 child commit，回到 Root 重新验证；child `228e3d6`，Root 待 pin 后复跑 topology/governance。

### Chunk 2：C-1.3 native-session 真实环境闭环

**Files/Resources:**
- Read/verify: `apps/kokoro-iam/README.md`, `apps/kokoro-bff/README.md`, `apps/kokoro-app/README.md`
- Read: `docs/REPOSITORY_STATUS.md`, `docs/CODEBASE_MAP.md`, `docs/kokoro-handbook/standards/04-transaction-repository-idempotency.md`
- Evidence (ignored/local): `output/e2e/task-a-c1-3/<run-id>/`

- [ ] Step 1：确认并记录隔离 PG schema、Redis namespace、IAM test admin URL、owner URLs、service credential 文件路径（不把 secret 写入 Git/聊天）。
- [ ] Step 2：按顺序启动 IAM → System/Capability/Storage/Billing/Scheduler → BFF → Agent → App → Admin；每个服务先 `/healthz` 再 `/readyz`。
- [ ] Step 3：执行 login、tenant switch、sign-out、revocation；记录 request-id、receipt scope、PG/Redis record、最终 HTTP/UI 状态。
- [ ] Step 4：执行匿名、foreign tenant、旧 token、重复 sign-out、重放/并发/取消负控；确认无越权 owner I/O。
- [ ] Step 5：关闭自有进程并清理自有 schema/namespace；保留脱敏 manifest 与日志索引。
- [ ] Step 6：Root review evidence 后才把 C-1.3 标记 DONE；缺配置时只更新 TODO，不宣称完成。

### Chunk 3：C-4 owner/full gates

- [ ] Step 1：BFF 完整 `pnpm test`、`pnpm format:check`、`pnpm check`；记录 0 fail/0 cancelled 或逐项分类。
- [ ] Step 2：App `pnpm lint && pnpm typecheck && pnpm test:architecture && pnpm test && pnpm build`；先解决 artifact digest provenance，不手改 baseline。
- [ ] Step 3：IAM `pnpm verify`；先处理唯一 format warning，再重跑完整 verify。
- [ ] Step 4：跨仓 integration 仅使用 `KOKORO_TEST_POSTGRES_URL`/`KOKORO_TEST_REDIS_URL` 隔离资源；skip 必须注明环境原因。
- [ ] Step 5：Root `git diff --check`、`python3 scripts/verify-repository-topology.py`、`python3 -m pytest scripts/tests -q`，并核对全部 submodule SHA。

### Chunk 4：A gate handoff（仅在 C-1.3～C-4 全绿后）

- [ ] Step 1：生成 A-01/A-02/A-07 独立 scope/owner/contract/data/rollback 设计门。
- [ ] Step 2：冻结本计划和证据索引，明确当前 commit/生成物 digest/服务版本。
- [ ] Step 3：只在 Root 明确授权后创建 A 计划；不在本计划中预写 A 代码。

---

## 5. TODO 台账（每轮更新）

| TODO | Owner | 状态 | 完成证据/下一动作 |
| --- | --- | --- | --- |
| T-01 更新 Goal 与本技术方案 | Root | DONE（本次） | 本文件、`docs/task.md`、Goal ACTIVE |
| T-02 修复 MCP denied icon owner call | BFF | DONE | child `228e3d6`; focused 42/42; full BFF 0 fail |
| T-03 修复 Skill installation invalid-owner error mapping | BFF | DONE | child `228e3d6`; focused 24/24; full BFF 0 fail |
| T-04 提供 C-1.3 隔离环境输入 | Root/环境 owner | OPEN | `IAM_TEST_ADMIN_URL`、隔离 PG/Redis/credentials |
| T-05 真实 IAM→BFF→App 四旅程 receipt | Root + IAM/BFF/App | WAITING T-04 | 脱敏 E2E manifest |
| T-06 BFF format warning 32 项 | BFF | OPEN | 只修受影响文件，重跑 format；当前保持非阻断历史基线 |
| T-07 App artifact digest drift | App/Root | OPEN | provenance review 后重生成/拒绝变更 |
| T-08 IAM verify / SDK drift | IAM | DONE | child `a1457be`; SDK check、`pnpm verify` 120 files / 1561 tests / build PASS |
| T-09 Root/owner full serial gate | Root | WAITING T-04 | 先 pin BFF `228e3d6`，再复跑 Root topology/governance、App/IAM/owner full gate |
| T-10 A-01/A-02/A-07 | Root | STOPPED | T-09 全绿后另立计划 |

---

## 6. 风险、回滚与禁止事项

- **风险**：重启/复用受管 PG、Redis、MinIO 会污染他人数据；没有隔离 URL 时不得运行 integration/E2E。
- **风险**：为清零失败而放宽断言、增加 timeout、改 baseline、吞掉 owner error 会破坏闭环；所有失败保持可复现。
- **回滚**：每个 child slice 一个 Conventional Commit；Root 只更新精确 gitlink。若行为回归，回退 child commit 和 Root pin，不回滚他人未交接改动。
- **禁止**：`git add .`、强制覆盖混合工作区、重置共享资源、生成凭据写入 repo、恢复 generic proxy、引入第二 aggregate/alias、在 C-4 前进入 A gates。

---

## 7. 更新协议

每次继续任务必须同时更新：

1. `docs/task.md`：Goal 状态、TODO 状态、当前 Root/BFF/App/IAM SHA。
2. 本计划：对应 checkbox、命令、实际结果、失败分类。
3. `docs/superpowers/evidence/2026-10-31-task-a-c1-cleanup-implementation.md`：追加一段带日期的事实证据。
4. Root `git status --short --branch`、child status、topology/governance 命令结果。

Goal 只有在 C-1.3/C-2/C-3/C-4/E2E 全部满足时才允许 `complete`；缺环境时保持 `active`，不得用 `blocked` 代替“等待外部输入”。
