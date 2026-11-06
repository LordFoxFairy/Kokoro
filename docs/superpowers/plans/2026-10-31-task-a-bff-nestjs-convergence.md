# Task A BFF NestJS 收敛实施计划

> 当前入口：本文保留原Nest迁移设计、过渡图与历史checkbox；最新基线、删除门、Goal及TODO统一见 [Task A闭环方案](2026-11-01-task-a-c1-c4-technical-plan.md)。不据本历史计划的状态判断当前完成。

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 `apps/kokoro-bff` 从手写 `node:http` 单体路由编排收敛为唯一 NestJS 12 原生运行时，并按真实复杂度拆分 feature module、Service、Repository 与外部 owner provider，删除旧 bootstrap/重复 composition。

**Architecture:** `NestFactory` 是唯一进程入口；`AppModule` 只负责配置、数据库/Redis 生命周期、health、跨 feature owner providers 和 feature modules。每个业务 feature 通过 Controller → Service →（必要时）具名 Repository/owner Client，HTTP wire 仍由现有 OpenAPI/生成 client/canonical schema 维护。迁移按 feature 逐步切换；未迁移的非 A routes 只能由 Nest 内冻结 `LegacyRoutesModule` adapter 承载，不得有第二 listener、alias、双写或双读；全部 feature 切换后删除 `bootstrap/server.ts`、`bootstrap/runtime.ts` 的旧手写 dispatcher 与 global store locator。

**Tech Stack:** Node 24 LTS、NestJS 12.0.1、`@nestjs/platform-express` 12.0.1、Zod 4.5.4、`pg`、`redis`、现有 OpenAPI/Connect generated clients、Vitest/Node test。

**G0 prerequisite:** 本计划的 IAM native-session admission contract 已固定为
`apps/kokoro-iam/contract/openapi/native-session-admission.v1.json`，version `1.0.0`，SHA-256
`5cf59df4b7bd9853edfd2eabb31afc236c0ec0db371f9737706fc129484fd83f`。G0 通过前只允许 contract/design/architecture-gate 变更；Nest feature 迁移从 G0 通过后的首个停写基线开始。

---

## 设计裁决

1. **唯一 runtime**：`src/main.ts` 只调用 `NestFactory.create()`；不再由 `node:http.createServer` 直接绑定业务路由。
2. **唯一 composition root**：`src/app.module.ts` 统一装配 config、PostgreSQL、Redis、IAM admission、owner clients、feature modules、worker lifecycle。`createBffComposition()` 不再作为生产 locator；测试用 `TestingModule` override provider。
3. **HTTP 迁移边界**：保持已发布 `/v1`、`/internal/v1`、`/iam` wire contract；旧 hash/alias/evolution 入口不恢复。Controller 只负责 raw request/context/pipe/error mapping，Service 负责业务用例，Repository 只负责真实复杂查询/事务/租户过滤。
4. **Repository 取舍**：保留 Chat、Project、ScheduledTask、Idempotency、AG-UI ledger/outbox 等真实复杂边界；删除 `BffBusinessStore`、`BffApplicationServices`、`PostgresBffRepositories` 这类 global locator/composition wrapper。简单 owner projection 直接注入 feature Service + generated client，不新增空 Repository。
5. **生命周期**：数据库池、Redis client、worker dispatcher、AG-UI projector 由 Nest provider 的 `OnModuleInit`/`OnApplicationShutdown` 管理；保留既有 drain 顺序、lease fencing、outbox、取消、readiness 与 bounded shutdown。
6. **切换方式**：Nest 是唯一 listener；每个 feature 完成 Controller/Service/测试后再将该路径从冻结 `LegacyRoutesModule` adapter 移出。adapter 只承载未迁移非 A routes、不新增 route、不改变 wire；最终所有 graph modules 切换后删除 adapter。中间提交不得新增兼容 alias 或第二份协议实现。

## 目标目录

```text
apps/kokoro-bff/src/
  main.ts                         # 唯一 NestFactory 入口
  app.module.ts                   # composition root
  config/                         # typed config provider（保留现有 schema）
  common/
    http/                         # filter/pipe/interceptor/request context
    lifecycle/                    # shutdown/readiness/drain
    database/                     # BFF PostgreSQL provider + schema readiness
    redis/                        # Redis provider/namespace
  modules/
    health/
    chat/                         # Conversation/Message/AG-UI public product API
    projects/                     # Project, pin, rename, resource, execution binding
    scheduled-tasks/
    account/                      # profile/sessions/personalization/archived/shared tasks
    skills/                       # public/product/admin/install/download lifecycle
    mcp/                          # personal/provider/project publication/package/icon
    billing/                      # credit grant/metering/model admission/settlement
    system/                       # runtime manifest/model routing/config/owner relay
    iam-relay/                    # native IAM protocol adapter
    music/
  integrations/                  # owner HTTP/Connect clients; no business route logic
  generated/                     # existing generated artifacts only
```

## 删除/保留矩阵

| 当前入口/结构 | C-2 目标 | 处理 |
|---|---|---|
| `src/main.ts` + `bootstrap/server.ts` | Nest `main.ts` + `AppModule` | 重写入口，最终删除旧 server dispatcher |
| `src/bootstrap/runtime.ts` | feature providers/modules | 按依赖拆出，删除 global composition |
| `BffBusinessStore` / `BffApplicationServices` | feature-scoped providers | 删除 global locator；保留业务服务本体 |
| `PostgresBffRepositories` | named Repository providers | 按 Chat/Project/Scheduled/Idempotency/AG-UI 拆分 |
| `src/http/routes/*` | Nest Controllers + Services | 按 feature 迁移，不新增 alias |
| `src/http/request.ts`, `response.ts`, `contracts` | common HTTP pipe/filter/mapper | 保留单一 wire parser/error 事实源，禁止复制 DTO |
| `src/infrastructure/clients/*` | integration providers | 保留 generated client 与 owner boundary，移入模块 exports |
| `src/application/agui/*`、outbox/dispatcher | lifecycle-managed providers | 保留 durable ledger/lease/outbox 语义，删除手工 start/stop 编排 |
| `src/upstream.ts` | typed owner HTTP provider | 保留协议能力，注入 config/deadline，不允许 Controller 直调 |
| `database/schema.sql` | canonical schema | 不改表、不引 migration chain；Nest readiness 只检查 canonical owner |
| 旧 `node:http` listener / generic fallback | 无 | C-2 完成时强制删除 |

---

## Chunk 1：依赖、运行时基线与架构门

### Task 1: 固定 Nest 运行依赖和脚本

**Files:**
- Modify: `apps/kokoro-bff/package.json`
- Modify: `apps/kokoro-bff/pnpm-lock.yaml`
- Test: `scripts/tests/test_ten_repository_standard.py`（仅在 Root 规则需要更新时）

- [ ] **Step 1: Add exact Nest 12 dependencies**

Add runtime `@nestjs/common`, `@nestjs/core`, `@nestjs/platform-express`, `reflect-metadata`, `rxjs` at the same versions as `apps/kokoro-system` (`12.0.1`, `0.2.2`, `7.8.2`). Add `@nestjs/testing` as dev dependency. Keep Node engine aligned with the repository Node 24 policy before implementation.

- [ ] **Step 2: Add Nest quality scripts**

Add `format:check` coverage for new `src/app.module.ts`, `src/common/**`, `src/modules/**`, `src/main.ts`; keep existing focused file list until it is replaced by a stable glob/formatter list. Add `test:nest-architecture` for module/import/lifecycle checks.

- [ ] **Step 3: Frozen install and dependency audit**

Run:

```bash
cd apps/kokoro-bff
pnpm install --frozen-lockfile
pnpm typecheck
```

Expected: install and existing checks pass before runtime files change.

- [ ] **Step 4: Commit**

```bash
git add package.json pnpm-lock.yaml
 git commit -m "refactor(bff): add nest runtime baseline"
```

### Task 2: Add Nest architecture gates before feature migration

**Files:**
- Create: `apps/kokoro-bff/test/nest-runtime-architecture.test.ts`
- Modify: `apps/kokoro-bff/test/architecture.test.ts`
- Modify: `apps/kokoro-bff/package.json`

- [ ] **Step 1: Write red gates**

Assert that `package.json` contains exact Nest runtime dependencies, `src/main.ts` imports `NestFactory`, `AppModule` exists, no production file imports `node:http.createServer`, and no feature Controller imports PostgreSQL/Redis directly.

- [ ] **Step 2: Run the gate**

```bash
pnpm test:nest-architecture
```

Expected: FAIL because the native Nest bootstrap does not exist yet.

- [ ] **Step 3: Commit test-only gate**

```bash
git add test/nest-runtime-architecture.test.ts test/architecture.test.ts package.json
git commit -m "test(bff): require native nest runtime"
```

---

## Chunk 2：Nest composition root、config、health 与 lifecycle

### Task 3: Move config/database/redis/readiness to providers

**Files:**
- Create: `apps/kokoro-bff/src/app.module.ts`
- Create: `apps/kokoro-bff/src/common/database/database.module.ts`
- Create: `apps/kokoro-bff/src/common/database/database.provider.ts`
- Create: `apps/kokoro-bff/src/common/redis/redis.module.ts`
- Create: `apps/kokoro-bff/src/common/redis/redis.provider.ts`
- Create: `apps/kokoro-bff/src/common/lifecycle/readiness.indicator.ts`
- Create: `apps/kokoro-bff/src/common/lifecycle/graceful-shutdown.ts`
- Modify: `apps/kokoro-bff/src/config/runtime.ts`
- Modify: `apps/kokoro-bff/src/http/routes/*` only when extracting a provider dependency

- [ ] **Step 1: Define provider contracts**

Create typed tokens/classes for `BffConfig`, `Pool`, Redis client, readiness and shutdown. Providers must own creation/close; Services receive typed providers, not `process.env` or raw clients.

- [ ] **Step 2: Preserve current readiness semantics**

Port `readyz` checks for canonical schema, Redis, required upstreams and Agent enablement. Keep `/healthz` liveness-only. Add tests for startup failure, readiness false, graceful drain, SIGINT/SIGTERM idempotence and hard deadline.

- [ ] **Step 3: Run focused lifecycle tests**

```bash
pnpm test -- test/nest-runtime-architecture.test.ts test/lifecycle.test.ts test/config.test.ts
```

- [ ] **Step 4: Commit**

```bash
git add src/app.module.ts src/common src/config/runtime.ts test
 git commit -m "refactor(bff): move runtime resources into nest providers"
```

### Task 4: Replace the Node listener with NestFactory

**Files:**
- Modify: `apps/kokoro-bff/src/main.ts`
- Create: `apps/kokoro-bff/src/http/application.setup.ts`
- Modify: `apps/kokoro-bff/src/bootstrap/server.ts` only for extracted handler calls during cutover
- Modify: `apps/kokoro-bff/test/lifecycle.test.ts`

- [ ] **Step 1: Implement Nest bootstrap**

Use `NestFactory.create<NestExpressApplication>(AppModule, { bodyParser: false, bufferLogs: true })`; configure raw-body capture, request-id, no-store defaults, error filter and shutdown hooks. Do not create a second `http.Server` manually.

- [ ] **Step 2: Keep one listener and one signal owner**

`main.ts` binds exactly once, obtains the Nest HTTP server, registers the single graceful shutdown owner and starts lifecycle-managed workers through providers.

- [ ] **Step 3: Verify smoke and architecture**

```bash
pnpm build
pnpm test:nest-architecture
pnpm test -- test/lifecycle.test.ts test/config.test.ts
```

- [ ] **Step 4: Commit**

```bash
git add src/main.ts src/http/application.setup.ts src/bootstrap/server.ts test/lifecycle.test.ts test/nest-runtime-architecture.test.ts
git commit -m "refactor(bff): make nest the sole http runtime"
```

---

## Chunk 3：Feature module migration and repository/service cutover

Migrate in this order so every slice has an independently testable owner boundary:

1. `health` and `system/iam-relay` (protocol/liveness, smallest risk)
2. `account` and `mcp` admission (auth/context first)
3. `chat` and `agui` (durable ledger, message facts, replay)
4. `projects` and `scheduled-tasks` (transactions/outbox/locks)
5. `skills` (largest route surface, generated owner clients)
6. `billing` and `music` (service-only/internal boundaries)

### Task 5: Split global BFF composition into feature providers

**Files:**
- Create: `src/modules/<feature>/<feature>.module.ts`
- Create: `src/modules/<feature>/<feature>.controller.ts`
- Create/Modify: `src/modules/<feature>/<feature>.service.ts`
- Create only where justified: `src/modules/<feature>/<feature>.repository.ts`
- Modify/Delete after consumers move: `src/application/ports/bff-business-store.ts`, `src/application/services.ts`, `src/infrastructure/postgres/repositories.ts`
- Tests: existing feature tests plus `test/nest-architecture.test.ts`

- [ ] **Step 1: Write module boundary tests**

For each feature, assert Controller imports only Service/wire schemas, Service does not import `IncomingMessage`/`ServerResponse` or `process.env`, Repository is owned by exactly one module, and cross-feature access uses exported providers.

- [ ] **Step 2: Extract the smallest feature first**

Move health/system routes to controllers and provider clients. Do not create a `CommonService`, `BaseRepository`, generic route registry or compatibility alias.

- [ ] **Step 3: Extract Chat and AG-UI with existing invariants**

Keep feature-local durable conversation/message/parts readers/writers; keep AG-UI ledger/cursor/replay/lease/outbox provider ownership. Preserve tenant/subject admission, cancellation, idempotency and transaction boundaries in integration tests.

- [ ] **Step 4: Extract Projects/ScheduledTasks**

Keep named repositories for Project parent locks, pin/rename/delete, ScheduledTask outbox and scheduler state. Controllers must not see `PoolClient`, SQL or Redis.

- [ ] **Step 5: Extract Skills/MCP/Billing/System features**

Move existing route functions into controllers/services one public operation at a time. Generated owner clients remain integration providers. Preserve OpenAPI operation IDs, error tuples, headers, idempotency and body budgets exactly.

- [ ] **Step 6: Remove global locators**

After the last consumer moves, delete `BffBusinessStore`, `BffApplicationServices`, `PostgresBffRepositories`, and old runtime factory fields. Replace tests that instantiate global stores with `TestingModule` provider overrides or feature-level fixtures.

- [ ] **Step 7: Commit each feature slice**

Use commits such as:

```bash
git commit -m "refactor(bff-chat): move chat routes into nest module"
git commit -m "refactor(bff-projects): split project repositories by owner"
```

### Task 6: Delete old dispatcher and duplicate route orchestration

**Files:**
- Delete after final cutover: `src/bootstrap/server.ts`
- Delete after final cutover: `src/bootstrap/runtime.ts`
- Delete only confirmed dead route helpers/tests
- Modify: `src/main.ts`, `src/app.module.ts`, `test/architecture.test.ts`, package scripts

- [ ] **Step 1: Prove no imports remain**

```bash
rg -n 'bootstrap/server|bootstrap/runtime|createBffServer|createBffComposition|node:http.*createServer' src test package.json
```

Expected: only migration evidence/tests before deletion; zero after deletion.

- [ ] **Step 2: Remove the old files**

Delete the dispatcher and composition wrappers. Do not leave a `legacy` or fallback runtime.

- [ ] **Step 3: Run full gates**

```bash
pnpm format:check
pnpm lint
pnpm typecheck
pnpm test:architecture
pnpm contract:check
pnpm test
pnpm build
```

- [ ] **Step 4: Commit**

```bash
git add src test package.json pnpm-lock.yaml
 git commit -m "refactor(bff): delete hand-written http dispatcher"
```

---

## Cross-cutting verification and stop boundaries

- Every feature slice must run its focused unit/contract/integration tests before the next slice.
- The full BFF gates run only after the final dispatcher deletion; PostgreSQL/Redis integration runs only with explicit disposable fixtures.
- Root verification after the BFF submodule commit: `python3 scripts/verify-repository-topology.py` and relevant governance checks.
- No BFF NestJS completion claim until the old listener, old dispatcher, global store locator and duplicate route orchestration are deleted and `src/main.ts` reaches NestFactory directly.
- A-01 session creation/recovery, A-02 Agent display and A-07 Project Todo start only after this C-2/C-3 cutover is verified.
