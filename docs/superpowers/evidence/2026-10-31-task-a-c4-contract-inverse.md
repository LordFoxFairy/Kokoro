> 历史过程材料（Task A已收尾）：本页保留原设计／失败／验证事实，不再作为执行入口。现行边界见[当前技术总览](../../kokoro-handbook/technical/00-system-overview.md)，后继事项见[TODO](../../../todo.md)。

# Task A C-4 contract inverse 与 BFF 全量复验（2026-10-31）

## 收敛内容

- OpenAPI 当前版本为 `28.18.0`。历史 Public28.15/28.16/28.17 inverse 先移除 Account profile read 增量，再按原有精确 hash 链恢复，避免 v28.18 新增 owner route 破坏历史 contract byte 校验。
- governance 将 `GET /v1/account/profile readAccountProfile` 纳入正式 IAM permission 映射 `iam:account-profile.read`，保留严格权限格式与其它 owner route 的 fail-closed 校验。
- IAM consumer contract/test pin 与当前已提交的 IAM `0.18.0` artifact 对齐，generated SDK 清单包含 `readAccountProfile`，历史 `0.15.0` vendor 仍仅作为既有 R357 历史 fixture 保留。
- `project-pin-public-contract` 的历史 operation inventory 在校验前显式剥离唯一的 Account profile read operation，并验证方法、路径和唯一性；不放宽其它 message/action baseline。
- native route HTTP fixtures 继续从 `dist` 加载，避免 source-loader 对 `.js`/`.ts` 映射的环境竞争。

## 串行验证

工作区：`/Users/nako/.codex/worktrees/task-a-c1-cleanup/Kokoro/apps/kokoro-bff`

- `pnpm build`：通过
- `pnpm typecheck`：通过
- `pnpm lint`：通过
- `pnpm format:check`：通过
- `pnpm test:nest-architecture`：12/12 通过
- contract/IAM focused：45/45 通过
- `pnpm test`：2312 tests，2295 pass，15 fail，2 skip；skip 为资源门禁保护的真实 PostgreSQL 条件测试，不计为通过。失败集中在既有 Artifact/Personal Storage Product HTTP、Project exact-download、Admin Web credential fixture 与 anonymous Share fixture；当前仍是 baseline/环境缺口，不能作为 C-4 通过。
- build-output focused feedback/run-display/project-binding：78/78 通过

## 仍未闭环

- C-1.3 的真实 IAM cookie→BFF→App receipt 仍需要 `IAM_TEST_ADMIN_URL`；sign-in/sign-out/tenant-switch/revocation 旅程收据尚未形成。
- LegacyRoutes 全量退出、global composition 与剩余 Repository/Service/Port 收敛仍未完成。
- A-01/A-02/A-07 继续停写。
