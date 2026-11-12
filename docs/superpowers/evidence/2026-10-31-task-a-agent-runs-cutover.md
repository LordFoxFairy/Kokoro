> 历史过程材料（Task A已收尾）：本页保留原设计／失败／验证事实，不再作为执行入口。现行边界见[当前技术总览](../../kokoro-handbook/technical/00-system-overview.md)，后继事项见[TODO](../../../todo.md)。

# Task A AgentRuns internal route cutover（2026-10-31）

## 变更

- BFF `a677cd2`：`AgentRunsModule` 注册 `AGENT_RUNS_READER` 与 `AgentRunsMiddleware`。
- 新增 `src/http/routes/agent-runs-native.ts`，承接：
  - `POST /internal/v1/model-admissions`
  - `POST /internal/v1/model-admissions/{admission_id}/settle`
  - `POST /internal/v1/model-admissions/recover`
  - `POST /internal/v1/project-execution-bindings/verify`
- `AgentRunsMiddleware` 同时承接 `GET /v1/sessions/:id/runs/:run/display`，通过 `RUN_DISPLAY_PROVIDER` 组合 submitted-run reader 与 `CHAT_SERVICE`，保留最终准入和 bounded Agent read。
- provider 使用唯一 `BFF_DATABASE` 构造 `PostgresAgentDispatchOutboxRepository`，复用 submitted-run 与 project-binding reader；不复制 outbox、SQL 或 Billing/IAM owner contract。
- 从 `handleBffRequest` 删除旧 internal 分支；raw server 与 Nest middleware 共用同一 adapter。

## 验证

- `pnpm typecheck`：通过。
- `pnpm build`：通过。
- `pnpm lint`：通过。
- `pnpm format:check`：通过。
- `pnpm test:nest-architecture`：11/11 通过。
- `node --import tsx --test --test-concurrency=1 test/model-admission-http.test.mjs`：9/9 通过。
- `node --import tsx --test --test-concurrency=1 test/bff.test.ts`：25/25 通过。
- `pnpm test:nest-architecture`：12/12 通过，包含 run-display provider seam 与 Chat/Agent module graph 非循环断言。
- build-output focused HTTP fixtures：run display 与 project binding 通过；model admission 独立 9/9 通过。
- `test/project-execution-binding-http.test.mjs` 的直接 source-loader 路径仍受既有 `.js`/`.ts` ESM 解析限制；生产 build 与 Agent adapter architecture gate 通过，该 loader 失败不改变 route 行为。

## 未关闭项

- LegacyRoutes 仍承载其它 Chat/Agent/Scheduled/Skills/MCP/Billing/Music route 与 worker，不能删除。
- C-1.3 真实 IAM cookie→BFF→IAM receipt、sign-in/sign-out/tenant-switch/revocation 旅程仍待环境与独立 evidence。
- A-01/A-02/A-07 继续停写。
