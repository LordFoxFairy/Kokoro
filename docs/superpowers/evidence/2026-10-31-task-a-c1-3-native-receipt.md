# Task A C-1.3 IAM native profile receipt（2026-10-31）

## 修复

- IAM `InternalAuthGuard` 将 `account.profile.update` 的请求体误判为非法 Session body，导致所有带 JSON 的 profile update 在 owner boundary 直接返回 400。现仅对 profile read 拒绝 body；profile update 只拒绝 query，JSON body 交由 canonical schema/controller 校验。
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

配套门禁：`pnpm format:check`、`pnpm lint`、`pnpm typecheck`、`pnpm contract:check`、`pnpm build`、`test/unit/internal-auth.guard.test.ts` 48/48 通过。

## 尚未闭环

- 该收据只闭合 IAM native owner/profile 片段与撤权行为，不代表 App→BFF→IAM 全链路 sign-in/sign-out/active-tenant switch/revocation 旅程已完成。
- App Product Session/Auth.js/OIDC 旧入口与 BFF LegacyRoutes 仍按 Goal 停写线保留，A-01/A-02/A-07 不启动。
