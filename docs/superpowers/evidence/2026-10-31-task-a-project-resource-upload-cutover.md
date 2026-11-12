> 历史过程材料（Task A已收尾）：本页保留原设计／失败／验证事实，不再作为执行入口。现行边界见[当前技术总览](../../kokoro-handbook/technical/00-system-overview.md)，后继事项见[TODO](../../../todo.md)。

# Task A Project resource-upload feature cutover receipt

日期：2026-10-31
范围：C-2 Projects resource upload、C-3 feature-local receipt/provider seam、C-4 BFF verification

## 变更

- BFF 子仓提交 `d6a6322`/`4501a2c` 将 `POST /v1/projects/{project_id}/resources` 接入 `ProjectPinMiddleware` 与 `handleProjectResourceUploadRequest`。
- Upload handler 只依赖窄 `ProjectResourceUploadProvider`：canonical Project `find`、PostgreSQL idempotency receipt owner 与 feature-local in-memory index；Storage 继续使用既有 `StorageUploadClient`/`uploadProjectResource` checkpoint、Complete、scan 与 lost-ACK 语义。
- raw `createBffServer` 显式 feature chain 同步接入 upload；旧 `handleBffRequest` 的 `projectResourceRoute` 分支/import 删除。无效 pin-only test composition 不要求 upload provider，保持原 fixture 边界。
- 保留 body 1 MiB、multipart 单文件、tenant/subject admission、idempotency conflict/pending/replay、45 秒 cancellation、receipt CAS 与 error envelope。

## 证据

- TDD red/green：新增 `Projects feature handler owns resource upload with persistent receipt recovery`；缺少 handler 时先失败，实现后通过。
- Focused：`pnpm build`；`pnpm exec tsx --test --test-concurrency=1 test/nest-feature-architecture.test.ts test/project-resource-upload.test.mjs`，25/25 passed；pin regression 4/4 passed。
- BFF static：`pnpm lint`、`pnpm typecheck`、`git diff --check` 通过。
- BFF 串行全量（`4501a2c`）：`pnpm test`，2312 tests / 2310 pass / 0 fail / 2 skip，duration 155741.028083 ms。
- `pnpm format:check` 仍有既有清单基线 warning，未进行无关全文件格式化。

## 未关闭范围

Project skill-selection、MCP recommendations、剩余 LegacyRoutes/global composition 与 Repository/Service/Port 仍未完成；A-01/A-02/A-07 继续停写。
