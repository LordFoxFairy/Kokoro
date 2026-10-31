# ADR-036 BFF NestJS 原生运行时与按能力收敛

状态：Accepted / G0 approved; implementation authorized (2026-10-31)

## Context

`apps/kokoro-bff` 当前由 `node:http` 直接创建 listener，并把大量 route、认证、owner client、PostgreSQL/Redis 装配和 worker 生命周期集中在 `bootstrap/server.ts` 与 `bootstrap/runtime.ts`。这套实现已经承接了完整的 public Product API、AG-UI durable ledger、outbox、取消、幂等和多个 owner client，但运行时没有 Nest Module/DI 边界，global `BffBusinessStore`/`BffApplicationServices`/`PostgresBffRepositories` 造成跨 feature locator，Repository/Service/Port 的职责难以审查。

Kokoro 的 TypeScript 后端标准已经统一采用 NestJS 12 原生 runtime、Module、Controller、Provider 和显式 DI。C-1 的阶段提交已删除 BFF schema-evolution CLI/测试以及 App/Agent 的确认兼容逻辑；这些提交仅作为阶段证据，G0 放行前仍必须完成契约、逐文件 disposition 和验证矩阵审阅。

## Decision

1. BFF 使用 `@nestjs/core` 12.0.1 + `@nestjs/platform-express` 12.0.1；`src/main.ts` 通过 `NestFactory.create()` 创建唯一应用和唯一 listener。
2. `src/app.module.ts` 是唯一 composition root。配置、PostgreSQL、Redis、IAM admission、owner clients、feature modules、health 与 worker lifecycle 通过 Nest providers/imports/exports 装配；测试通过 `TestingModule` override provider。
3. 业务按 capability 建立 feature modules：Health、Chat/AG-UI、Projects、ScheduledTasks、Account、Skills、MCP、Billing、System/IAM relay、Music。Controller 只做 wire/context/pipe/error mapping；Service 负责用例/授权/事务编排；外部 owner client 作为 integration provider。
4. Repository 不是默认层。保留 Chat、Project、ScheduledTask、Idempotency、AG-UI ledger/outbox 等真实复杂数据访问边界；简单 owner projection 直接由 feature Service 注入 generated client。删除 global `BffBusinessStore`、`BffApplicationServices`、`PostgresBffRepositories` locator，不建立 `BaseRepository`、万能 `CommonService` 或重复 DTO/ORM model。
5. 迁移按 feature 完成可验证切片；Nest 是唯一 HTTP listener。未迁移的非 A routes 仅可由 Nest 内冻结 `LegacyRoutesModule` adapter 承载；在同一条 public contract、schema、错误、权限、幂等、取消和恢复语义下切换 Controller。禁止新 alias、双读/双写、第二套 HTTP listener 或 migration fallback。
6. 所有 graph feature 切换完成后删除 `LegacyRoutesModule`、`src/bootstrap/server.ts`、`src/bootstrap/runtime.ts` 的手写 dispatcher/composition。`database/schema.sql` 继续是唯一 canonical schema；本 ADR 不引入 migration chain、表迁移或跨 owner SQL。

## G0 release prerequisites

G0 放行前必须同时具备以下机器可核对材料：

| 材料 | 唯一 owner / writer | 固定位置 | 放行条件 |
|---|---|---|---|
| native-session admission contract `1.0.0` | IAM | `apps/kokoro-iam/contract/openapi/native-session-admission.v1.json` | `POST /internal/v1/native-session-admission/verify` 的请求、响应、错误闭集、Cookie/CSRF/撤权语义与 SHA-256 `5cf59df4b7bd9853edfd2eabb31afc236c0ec0db371f9737706fc129484fd83f` 固定；IAM generated client 与 BFF consumer 必须同片交付 |
| BFF feature/provider map | Task A | 本 ADR 与 Task A inventory | 每个 module 的 imports/exports、provider token、owner client、生命周期与旧 route 映射逐项列明 |
| C-1 disposition | App/BFF/Agent | Task A inventory | 每个删除/重写/保留文件有生产消费者、替代事实和测试证据 |
| Repository/Service/Port disposition | BFF | Task A inventory | 每个现有 Port 有保留、拆分、并入或删除结论与事务/权限证据 |
| Test/script matrix | App/BFF/Agent | Task A inventory | 默认脚本、fixture、generated oracle、integration 资源和替代测试逐项列明 |

在上述材料通过审阅前，`apps/kokoro-bff` 的 Nest 依赖基线与 architecture gate 只作为预备提交，不进入 feature 迁移。

## Consequences

### Positive

- Nest lifecycle 统一管理数据库、Redis、worker drain、readiness 和关闭顺序。
- Module exports 明确跨 feature 依赖，global locator 与隐藏装配消失。
- Controller/Service/Repository/owner client 的边界可由 architecture tests 检查，Repository 只在真实复杂度存在时保留。
- 旧 dispatcher 删除后，BFF 只剩一套业务 runtime 与一套协议实现，便于后续 A-01/A-02/A-07。

### Costs and risks

- BFF route surface 很大，迁移需要按 Chat/Project/Scheduled/Skills/MCP 等能力分批提交并保持完整 contract gates。
- 迁移期间不能使用兼容 alias 或第二 listener 掩盖遗漏；每个 feature 必须先有正/负路径测试再切换。
- 现有 Node raw request/body budget、SSE、IAM relay、owner Connect/HTTP adapter 需要明确挂接 Nest raw-body/Express lifecycle，不能只依赖默认 middleware。
- 真正完成必须证明旧 bootstrap/runtime 已删除，并重新运行完整 BFF tests、contract、build、架构门及必要 disposable PG/Redis integration。

## Verification

- `pnpm format:check`, `pnpm lint`, `pnpm typecheck`, `pnpm test:architecture`, `pnpm contract:check`, `pnpm test`, `pnpm build`
- `python3 scripts/verify-repository-topology.py`
- 受影响的 PostgreSQL/Redis integration 使用独立 disposable fixture；skip 不记为通过。
