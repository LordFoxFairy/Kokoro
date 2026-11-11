# Task A Project resource-list feature cutover receipt

日期：2026-10-31
范围：C-2 Projects resource read bundle、C-3 provider seam、C-4 BFF verification

## 变更

- BFF 子仓提交 `52eeff7d6561f3ecc752a2c58d86fd72476d159b` 将 `GET /v1/projects/{project_id}/resources` 接入 `project-native.ts` 的 `handleProjectResourceListRequest`。
- `ProjectsModule` 的 `ProjectPinMiddleware` 现在接管资源集合读取；Project owner 只通过 `ProjectCoreReadProvider.find` 解析 canonical Project，Storage 仍由既有 `StorageUploadClient`/Connect owner 负责，未复制 SQL 或 Storage transport。
- raw `createBffServer` 的显式链路同步接入 native handler；测试组合器旁路不变。
- 删除旧 `src/http/routes/project-resource-list.ts`、server dispatcher 分支、route import 与显式 package format 文件项；资源分页 parser、Storage header scope、no-store/request-id、10 秒取消预算保持不变。

## 证据

- architecture red/green：`test/nest-feature-architecture.test.ts` 锁定 `handleProjectResourceListRequest` 的 module/native/server ownership，并断言旧 `projectResourceListRoute` 不再进入 server。
- Project resource focused：`node --import tsx --test --test-concurrency=1 test/project-resource-list.test.mjs`，22/22 passed。
- BFF static gates：`pnpm build`、`pnpm typecheck`、`pnpm lint`、`git diff --check` 通过。
- BFF 串行全量：`pnpm test`，2310 tests / 2308 pass / 0 fail / 2 skip，duration 155944 ms；2 个 skip 为既有真实 PostgreSQL 资源门禁，不计为通过。

## 未关闭范围

该切片只关闭 Project resource collection list 的旧 dispatcher 入口；Project resource upload/detail/download/delete、skill-selection、剩余 LegacyRoutes/global composition 与 Repository/Service/Port 仍按 Task A 计划继续迁移。A-01/A-02/A-07 继续停写。
