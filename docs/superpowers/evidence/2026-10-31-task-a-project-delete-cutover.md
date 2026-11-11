# Task A Projects delete feature cutover receipt

日期：2026-10-31
范围：C-2 Projects route bundle、C-3 provider seam、C-4 BFF verification

## 变更

- BFF 子仓提交 `1817bd96af6b86f16c50f3220abbfcf23715fc23` 将 `DELETE /v1/projects/{project_id}` 接入 `project-native.ts` 的 `ProjectCoreReadProvider` 与 `handleProjectDeleteRequest`。
- `ProjectsModule` 的 `ProjectPinMiddleware` 现在按 rename → delete → deletion-status → collection/detail/revisions → pin 顺序处理项目 native path；生产 provider 仍由唯一 `PROJECT_SERVICE` 注入并复用 `ProjectService.delete`/`ProjectRepository.deleteProject` 的 receipt、CAS、scope-release/outbox 事务边界。
- raw `createBffServer` 的显式链路同步接入 native handler；测试组合器 `routeHandler` 旁路不变。
- 删除旧 `src/http/routes/project-delete.ts`、`server.ts` 旧 path 判定/分支和 route import；保留 `project-deletion-input.ts` 严格空体/idempotency 校验与 canonical deletion contract。
- 保持 202 `Location`、accepted/not_found/in_progress/conflict、retryable 与取消预算语义；没有新增 mutation framework、repository、receipt 或第二 SQL writer。

## 证据

- architecture red/green：`test/nest-feature-architecture.test.ts` 锁定 `ProjectsModule`/middleware/native route/server ownership，并断言旧 `projectDeleteRoute` 不再进入 server。
- BFF focused：`node --import tsx --test --test-concurrency=1 test/nest-feature-architecture.test.ts test/project-pin-http.test.mjs test/contract/openapi-contract.test.mjs test/bff.test.ts`，131/131 passed。
- BFF static gates：`pnpm build`、`pnpm typecheck`、`pnpm lint`、`git diff --check` 通过；人工 HTTP fixture 验证 202 accepted、Location、query alias 400。
- BFF 删除切片后的串行全量：`pnpm test`，2310 tests / 2308 pass / 0 fail / 2 skip，duration 157229 ms；2 个 skip 为既有真实 PostgreSQL 资源门禁，不计为通过。

## 未关闭范围

该切片只关闭 project delete 的旧 dispatcher 入口；`LegacyRoutesRuntime`、global composition、Project resource/skills bundle 与剩余 Repository/Service/Port 仍按 Task A 计划继续迁移。A-01/A-02/A-07 继续停写。
