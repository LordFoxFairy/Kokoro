> 历史过程材料（Task A已收尾）：本页保留原设计／失败／验证事实，不再作为执行入口。现行边界见[当前技术总览](../../kokoro-handbook/technical/00-system-overview.md)，后继事项见[TODO](../../../todo.md)。

# Task A Projects pin route cutover（2026-10-31）

## 变更

- BFF `ef1c53b`：`ProjectsModule` 注册 `PROJECT_SERVICE` 与 `ProjectPinMiddleware`。
- 新增 `src/http/routes/project-native.ts`，承接：
  - `GET /v1/self/project-pins`
  - `PUT /v1/projects/:id/pin`
- `projectPinRoute` 改为接收 `ProjectPinProvider`，继续使用现有 `ProjectService`/`ProjectRepository` 的自然幂等、owner scope、10 秒预算和最终 admission；没有复制 SQL、receipt 或 Repository。
- 从 `handleBffRequest` 删除旧 Project pin 分支；raw `createBffServer` 与 Nest middleware 共用同一 adapter。

## 闭环证据

```text
Project pin inventory
  → PROJECT_SERVICE provider
  → project-native adapter + middleware
  → 删除 server.ts 旧分支/全局 pin deadline
  → negative architecture assertion
  → focused HTTP/input/repository tests
```

## 验证

- `pnpm typecheck`：通过。
- `pnpm build`：通过。
- `pnpm lint`：通过。
- `pnpm format:check`：通过。
- `node --test --test-concurrency=1 test/nest-feature-architecture.test.ts test/project-pin-http.test.mjs`：Project pin HTTP 与 ownership assertion 通过；直接单测 source imports 的 ESM 解析受既有 `tsx`/`.js` source-loader 限制，不作为行为失败。
- `pnpm test:project-pin`：Project pin input/repository/HTTP 11 项通过；4 项历史 contract inverse 因 `Activity details version drift` 失败，属于 C-4 既有基线。

## 未关闭项

- `LegacyRoutesRuntime`、`handleBffRequest` 与 `BffBusinessStore` 仍承载其它未迁移 route/worker，不能删除。
- C-1.3 真实 IAM cookie→BFF→IAM receipt、sign-in/sign-out/tenant-switch/revocation 旅程仍待环境与独立 evidence。
- A-01/A-02/A-07 继续停写。
