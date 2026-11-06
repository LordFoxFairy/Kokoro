# Task A Projects rename feature cutover receipt

日期：2026-10-31  
范围：C-2 Projects route bundle、C-3 provider seam、C-4 BFF verification

## 变更

- BFF 子仓提交 `1db4e51185d26d5a6dccb015fbeea3d1ab219027` 将 `PATCH /v1/projects/{project_id}/name` 接入 `project-native.ts` 的 `ProjectCoreReadProvider` 与 `handleProjectRenameRequest`。
- `ProjectsModule` 的 `ProjectPinMiddleware` 现在先处理 rename，再处理 deletion-status、项目集合/详情/revisions 与 pin；生产 provider 仍由唯一 `PROJECT_SERVICE` 注入并复用既有 `ProjectService.rename`/`ProjectRepository.renameProject` receipt/CAS 事务边界。
- raw `createBffServer` 的显式链路同步接入 native handler；测试组合器的 `routeHandler` 旁路不变。
- 删除旧 `src/http/routes/project-rename.ts`、`server.ts` 旧 path 判定/分支和 route import；保留严格输入 parser、canonical `project-rename-input.ts` 与 PostgreSQL receipt helper。
- rename 的 idempotency key、JSON body、no-store/request-id、取消预算及 `renamed/not_found/conflict` 映射保持原 contract；没有新增 mutation framework、repository、receipt 或第二 SQL writer。

## 证据

- architecture red/green：`test/nest-feature-architecture.test.ts` 锁定 `ProjectsModule`/middleware/native route/server ownership，并断言旧 `projectRenameRoute` 不再进入 server。
- BFF focused：`node --import tsx --test --test-concurrency=1 test/nest-feature-architecture.test.ts test/project-pin-http.test.mjs test/contract/openapi-contract.test.mjs test/bff.test.ts`，131/131 passed。
- BFF static gates：`pnpm build`、`pnpm typecheck`、`pnpm lint`、`git diff --check` 通过；人工 HTTP fixture 验证 rename 200、query alias 400 与重复 key 仍由 provider 接收。
- `pnpm format:check` 仍报告既有 `src/bootstrap/runtime.ts`、`src/bootstrap/server.ts`、`src/modules/chat/chat.module.ts` 格式差异；本切片新增 `project-native.ts` 已单文件按既有 source style 保持最小 diff，未扩大无关格式化。

## 未关闭范围

该切片只关闭 project rename 的旧 dispatcher 入口；`LegacyRoutesRuntime`、global composition、Project delete/resource/skills bundle 与剩余 Repository/Service/Port 仍按 Task A 计划继续迁移。A-01/A-02/A-07 继续停写。
