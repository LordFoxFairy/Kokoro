# Task A ScheduledTask current-read cutover（2026-10-31）

## 变更

- BFF `6874034`：`ScheduledTasksModule` 注册 `SCHEDULED_TASK_READ_SERVICE` 与 `ScheduledTaskReadMiddleware`。
- 新增 `src/http/routes/scheduled-task-native.ts`，承接 `GET /v1/scheduled-tasks` 与 `GET /v1/scheduled-tasks/:id`。
- provider 使用唯一 `BFF_DATABASE` 构造 `PostgresScheduledTaskRepository`，并复用 Scheduler current-state owner adapter；不复制快照、调度 SQL、lease 或状态机。
- 从 `handleBffRequest` 删除旧 current-read 分支；raw test composition 保持 `routeHandler` 旁路，mutation fixture 不被 read adapter 截获。

## 闭环证据

```text
scheduled route inventory
  → SCHEDULED_TASK_READ_SERVICE provider
  → scheduled-task-native adapter + middleware
  → 删除 server.ts 旧 current-read 分支
  → routeHandler 旁路保护
  → bff mock contract + architecture + focused gates
```

## 验证

- `pnpm typecheck`：通过。
- `pnpm build`：通过。
- `pnpm lint`：通过。
- `pnpm format:check`：通过。
- `pnpm test:nest-architecture`：10/10 通过。
- `node --import tsx --test --test-concurrency=1 test/bff.test.ts`：25/25 通过；scheduled mutation fixture 未被新 read adapter 改写。
- App native focused：91/91 通过；IAM native/profile/session focused：35/35 通过。

## 未关闭项

- LegacyRoutes 仍承载其它 Chat/Agent/Scheduled/Skills/MCP/Billing/Music route 与 worker，不能删除。
- C-1.3 真实 IAM cookie→BFF→IAM receipt、sign-in/sign-out/tenant-switch/revocation 旅程仍待环境与独立 evidence。
- A-01/A-02/A-07 继续停写。
