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
- `python3 scripts/e2e/run_web_native_session_smoke.py ... --expected-iam-sha e1f537b02cb326cfb3751316b1591fa82313f70a`：4/4 cases passed；在 test-owned HTTPS Web origin 上验证 `/api/auth/session` native subject、`/api/session/projects` Web→BFF→IAM 链路、IAM signout 后的 401，以及进程/数据库/Redis 清理。IAM fixture 由 `IAM_TEST_WEB_ORIGIN` 固定到同一 Web origin，并通过直接 session-admission credential 启动 BFF。
- 在 `BFF cb02934e48954d55a52b6918646256bc672f28d1` 将 `GET /v1/projects` 下沉到 `ProjectsModule` 后，按 Root gitlink 精确复跑同一 HTTPS smoke，仍为 4/4 cases passed；因此 receipt 同时覆盖最新 feature middleware/provider 图，而非只覆盖旧 dispatcher。
- 随 `BFF e8d9a27900869d91c86e54d75246debb71946bec` 再将项目详情读取移入同一 feature provider 后，Root gitlink 精确复跑仍为 4/4 cases passed；`/api/session/projects` 业务链路保持 native admission 与 signout 语义。
- `BFF b9294ab63eb5dbb25a55eed46d6e716df31594ce` 将项目 instruction-revisions 读取继续下沉后，Root gitlink 精确复跑 HTTPS native smoke 仍为 4/4。
- `BFF fd27d8d76386152ee8e2dd41d9ce232500a09938` 完成 global chat/project service-field cleanup 后，Root gitlink 精确复跑 HTTPS native smoke 仍为 4/4。
- `BFF fd74e02f9e148d0a480ecbc3e47a2de0ddaf1362` 将 public share projection 移入 Chat feature 后，Root gitlink 精确复跑 HTTPS native smoke 仍为 4/4。
- `BFF 8448a7e19b5e810a553f6699e859fd9cd57797ee` 保留 test-only shared reader fallback 后，Root gitlink 精确复跑 HTTPS native smoke 仍为 4/4。

Smoke 中发现并修复的运行时依赖：`AgentRunsModule` 与 `ScheduledTasksModule` 显式导入 `AccountModule`，为 native middleware 提供 `SESSION_ADMISSION`；对应 BFF commits `4e794ce`、`b3a9ab5`。

## 尚未闭环

- 该收据闭合 IAM native owner/profile、IAM→BFF real session/OIDC 与 Web HTTPS native session/signout 入口，不代表完整 App native sign-in/active-tenant switch/revocation UI 旅程已完成。
- IAM issuer cookie scope 已按 G0 contract 切为 `Path=/`，BFF/App relay policy 同步切换；当前剩余缺口是完整 native sign-in/active-tenant switch UI 与旧 RP/Product Session 删除前的全量回归。
- App Product Session/Auth.js/OIDC 旧入口与 BFF LegacyRoutes 仍按 Goal 停写线保留，A-01/A-02/A-07 不启动。
