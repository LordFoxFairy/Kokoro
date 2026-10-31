# Task A Project resource-delete feature cutover receipt

日期：2026-10-31  
范围：C-2 Projects resource command bundle、C-3 provider seam、C-4 BFF verification

## 变更

- BFF 子仓提交 `14aa2322030c9f967f7903562c7794f51fdcf7c1` 将 `DELETE /v1/projects/{project_id}/resources/{asset_id}` 接入 `project-native.ts` 的 `handleProjectResourceDeleteRequest`。
- `ProjectsModule` 的 `ProjectPinMiddleware` 现在接管资源 keyed delete；Project owner 只通过 `ProjectCoreReadProvider.find` 解析 canonical Project，Storage 仍由既有 `ProjectResourceAccessClient`/Connect owner 负责，未复制 SQL 或 scope-release writer。
- raw `createBffServer` 的显式链路同步接入 native handler；测试组合器旁路不变。
- 删除旧 `src/http/routes/project-resource-delete.ts`、server dispatcher 分支与 route import；保留严格空体/idempotency/CAS、owner replay、request-id 与取消预算。

## 证据

- architecture red/green：`test/nest-feature-architecture.test.ts` 锁定 `handleProjectResourceDeleteRequest` 的 module/native/server ownership，并断言旧 `projectResourceDeleteRoute` 不再进入 server。
- Project resource focused：`node --import tsx --test --test-concurrency=1 test/project-resource-list.test.mjs test/project-resource-delete.test.mjs`，37/37 passed。
- BFF static gates：`pnpm build`、`pnpm typecheck`、`pnpm lint`、`git diff --check` 通过。
- BFF 串行全量：`pnpm test`，2310 tests / 2308 pass / 0 fail / 2 skip，duration 160976 ms；2 个 skip 为既有真实 PostgreSQL 资源门禁，不计为通过。

## 未关闭范围

该切片只关闭 Project resource keyed delete 的旧 dispatcher 入口；Project resource upload/detail/download、skill-selection、剩余 LegacyRoutes/global composition 与 Repository/Service/Port 仍按 Task A 计划继续迁移。A-01/A-02/A-07 继续停写。
