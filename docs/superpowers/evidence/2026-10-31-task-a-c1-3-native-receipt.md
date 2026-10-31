# Task A C-1.3 IAM native profile receipt（2026-10-31）

## 修复

- IAM `InternalAuthGuard` 将 `account.profile.update` 的请求体误判为非法 Session body，导致所有带 JSON 的 profile update 在 owner boundary 直接返回 400。现仅对 profile read 拒绝 body；profile update 只拒绝 query，JSON body 交由 canonical schema/controller 校验。
- IAM Better Auth issuer cookie 已从 `Path=/iam` 切为 G0 contract 固定的 `Path=/`；native admission integration 断言每个登录 Set-Cookie 均为 root path，BFF/App relay policy 同步接受 root path。
- native profile integration fixture 在登录后显式通过同一 issuer cookie 设置 active organization，确保 native admission 验证的 active tenant 来自 IAM session，而不是 fixture 外部状态。

## 真实本地收据

工作区：`/Users/nako/.codex/worktrees/task-a-c1-cleanup/Kokoro/apps/kokoro-iam`

命令：

```bash
IAM_TEST_ADMIN_URL=postgresql://nako@127.0.0.1:5432/postgres \
IAM_TEST_REDIS_URL=redis://127.0.0.1:6379/1 \
VITEST_MAX_WORKERS=1 \
pnpm exec vitest run \
  test/integration/bff-session-admission-host.test.ts \
  test/integration/account-profile/account-profile.test.ts \
  --maxWorkers=1
```

结果：2 files / 12 tests passed；覆盖 native cookie profile read、bearer read、profile update CAS/rollback、same/different session 竞争、撤权后的 401、服务端 admission host 资源清理。

配套门禁：`pnpm format:check`、`pnpm lint`、`pnpm typecheck`、`pnpm contract:check`、`pnpm build`、IAM deterministic `pnpm test` 1561/1561 通过；`test/unit/internal-auth.guard.test.ts` 48/48 通过。

## Root 跨仓收据

工作区：`/Users/nako/.codex/worktrees/task-a-c1-cleanup/Kokoro`

- `python3 scripts/e2e/run_bff_iam_session_smoke.py ... --expected-bff-sha 3ca1525... --expected-iam-sha f4f1585...`：7/7 cases passed；覆盖真实 IAM session admission、BFF owner fact 归属、缺 bearer、signout、reset、新身份隔离、member removal、IAM outage 与资源清理。
- `python3 scripts/e2e/run_bff_iam_oidc_smoke.py ... --expected-bff-sha 3ca1525... --expected-iam-sha f4f1585...`：42/42 cases 在 cookie cutover 前通过；Path=/ cutover 后需重跑，当前一次重跑在 OAuth foreign-tenant guard 阶段失败，不作为现行通过证据。
- 两个 smoke 均使用本地 PostgreSQL/Redis、BFF source build 和 IAM test-owned host；Root gitlink、子仓 clean、process/database/Redis cleanup 均通过。
- App native/policy focused gate：7 files / 120 tests passed，覆盖 native Cookie adapter、account profile admission、session proxy、relay policy 和 root-scoped cookie projection。

Smoke 中发现并修复的运行时依赖：`AgentRunsModule` 与 `ScheduledTasksModule` 显式导入 `AccountModule`，为 native middleware 提供 `SESSION_ADMISSION`；对应 BFF commits `4e794ce`、`b3a9ab5`。

## 尚未闭环

- 该收据闭合 IAM native owner/profile、IAM→BFF real session/OIDC 与撤权行为，不代表 App→BFF→IAM native sign-in/sign-out/active-tenant switch/revocation 旅程已完成。
- IAM issuer cookie scope 已按 G0 contract 切为 `Path=/`，BFF/App relay policy 同步切换；当前剩余缺口是用真实 HTTPS 浏览器证明 `/api/*` native adapter 触达 BFF/IAM，随后才删除旧 RP/Product Session。
- App Product Session/Auth.js/OIDC 旧入口与 BFF LegacyRoutes 仍按 Goal 停写线保留，A-01/A-02/A-07 不启动。
