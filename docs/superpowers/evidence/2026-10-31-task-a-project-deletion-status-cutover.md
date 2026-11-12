> 历史过程材料（Task A已收尾）：本页保留原设计／失败／验证事实，不再作为执行入口。现行边界见[当前技术总览](../../kokoro-handbook/technical/00-system-overview.md)，后继事项见[TODO](../../../todo.md)。

# Task A Projects deletion-status feature cutover receipt

日期：2026-10-31
范围：C-2 Projects route bundle、C-3 provider seam、C-4 BFF verification

## 变更

- BFF 子仓提交 `7afbaffd0a1fbd93af4141bfade8f3b6f1df7fb1` 将 `GET /v1/projects/{project_id}/deletion` 接入 `project-native.ts` 的 `ProjectCoreReadProvider` 与 `handleProjectDeletionStatusRequest`。
- `ProjectsModule` 的 `ProjectPinMiddleware` 现在先处理 deletion-status，再处理项目集合/详情/revisions 与 pin；生产 provider 仍由唯一 `PROJECT_SERVICE` 注入并复用既有 `ProjectService.deletion`/`ProjectRepository.projectDeletion` 事务读边界。
- raw `createBffServer` 的显式链路同步接入 native handler，保留测试组合器的 `routeHandler` 旁路语义。
- 删除旧 `src/http/routes/project-deletion-status.ts`、`server.ts` 旧 path 判定/分支和无调用 import；更新 BFF 技术设计的文件落点。
- 错误响应继续保持 Project deletion contract 的裸 `error.code/message/retryable`、`x-request-id` 与 `Cache-Control: no-store`；成功响应保持 `{ data }`，没有新增 meta、receipt 或第二 SQL owner。

## 证据

- architecture red/green：`test/nest-feature-architecture.test.ts` 锁定 `ProjectsModule`/middleware/native route/server ownership，并断言旧 `projectDeletionStatusRoute` 不再进入 server。
- BFF focused：`node --test --test-concurrency=1 test/nest-feature-architecture.test.ts`，10/10 passed。
- BFF mock contract：`node --import tsx --test --test-concurrency=1 test/bff.test.ts`，25/25 passed。
- BFF static gates：`pnpm build`、`pnpm typecheck`、`pnpm lint`、`git diff --check` 均通过；人工 HTTP fixture 验证 200 data-only、query/header invalid 400 closed error。
- BFF 串行全量：`pnpm test`，2310 tests / 2308 pass / 0 fail / 2 skip，duration 156711 ms；2 个 skip 为既有真实 PostgreSQL 资源门禁，不计为通过。

## 未关闭范围

该切片只关闭 project deletion-status 的旧 dispatcher 入口；`LegacyRoutesRuntime`、global composition、其余 Project mutation/resource/skills bundle 与剩余 Repository/Service/Port 仍按 Task A 计划继续迁移。A-01/A-02/A-07 继续停写。
