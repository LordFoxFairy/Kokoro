# Task A Project resource-read feature cutover receipt

日期：2026-10-31  
范围：C-2 Projects resource read/download bundle、C-3 provider seam、C-4 BFF focused verification

## 变更

- BFF 子仓提交 `525a150` 将 `GET /v1/projects/{project_id}/resources/{asset_id}` 与 `/download` 接入 `project-native.ts` 的 `handleProjectResourceReadRequest`。
- `ProjectsModule` 的 `ProjectPinMiddleware` 现在接管资源 metadata/download read；Project owner 只通过窄 `ProjectResourceProjectReader.find` 解析 canonical Project，Storage 仍由既有 `ProjectResourceAccessClient` 与 verified spool/download owner seam 负责，未复制 SQL、Storage transport 或 global store reader。
- raw `createBffServer` 的显式 feature chain 同步接入 native handler；`handleBffRequest` 的资源 read/download 分支、旧 import 与 `BffBusinessStore` 直接耦合已删除。
- `project-resource-read.ts` 与 `currentResourceProject` 改为接收 feature-local project reader，保留 exact path/body/header validation、10 秒 metadata/120 秒 download budget、owner recheck、bytes/hash verification、spool cleanup、request-id 与 cancellation。

## 证据

- TDD red/green：新增 `Projects feature handler owns item metadata reads without entering the legacy dispatcher`，缺少 handler 时先失败；实现后 focused 通过。
- Project resource focused：`pnpm exec tsx --test --test-concurrency=1 test/nest-feature-architecture.test.ts test/project-resource-access.test.mjs`，20/20 passed。
- BFF static gates：`pnpm build`、`pnpm lint`、`pnpm typecheck`、`git diff --check` 通过。
- `pnpm format:check` 仍按既有基线失败：`test/project-resource-list.test.mjs`、`src/bootstrap/runtime.ts`、`src/bootstrap/server.ts`、`src/modules/chat/chat.module.ts`、`src/http/routes/project-native.ts`；本切片未进行无关全文件格式化。

## 未关闭范围

该切片只关闭 Project resource metadata/download 的旧 dispatcher 入口；Project resource upload、skill-selection、MCP recommendations、剩余 LegacyRoutes/global composition 与 Repository/Service/Port 仍按 Task A 计划继续迁移。BFF 串行全量最近证据仍对应前一提交 `14aa232`；`525a150` 之后尚未重跑全量。A-01/A-02/A-07 继续停写。
