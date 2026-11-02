# Task A 清理与重构只读盘点

> 当前入口：本文保留初始逐文件disposition/风险矩阵，G0待批准等表述仅为当时快照；当前剩余消费者、问题和TODO统一维护于 [Task A闭环方案](../plans/2026-11-01-task-a-c1-c4-technical-plan.md)。不据历史勾选判定当前完成。

> 状态：只读盘点；本文件不授权删除或重写。本轮未修改业务代码、测试、契约、数据库或运行配置。

## 1. 基线

- Root：`3a3b6b91faf4540a2499915698f2abbdb525ba85`
- App：`apps/kokoro-app` @ `73b2df451c2604a6d1e9413bf07eb383b95219e9`
- BFF：`apps/kokoro-bff` @ `853ca9a5d8da3500b0c37543c72198a520e46225`
- Agent：`apps/kokoro-agent` @ `c43fc3f22c676b459dd45d74438a6ccb515e5abd`
- IAM：`apps/kokoro-iam` @ `b9a63c533ab95b70a07693190d64bd09791a125b`
- Capability/Platform：`apps/kokoro-capability` @ `44fcc5da599b4a5cec3077e41aaef4375fe4add2`
- System：`apps/kokoro-system` @ `49a5f8e5e2797ec2d1a6fcf8c5f398184821bf33`
- Billing：`apps/kokoro-billing` @ `b7c9858844df4c9b99e40e16bd9984b1d268b503`
- Storage：`apps/kokoro-storage` @ `4a990617ffe36d739b5a3e622132c304d4d48d41`
- Scheduler：`apps/kokoro-scheduler` @ `cfb2502b0ef9331f79a328ec85c254157340962c`
- Admin：`apps/kokoro-admin` @ `d221b18d28e15ec423798416aa8abd1f71f44bf8`
- Mori：`apps/kokoro-mori` @ `12a1060830e1239c2ccb866baeefa4546ec04bb5`
- Web shared：`libs/kokoro-web-shared` @ `0c4e87ace01340aaa07bc57935f1d98b8e77af14`

子仓工作区无业务 diff；Root 当前未跟踪文件是任务交接文档和清理技术方案文档。

## 2. 处理标记

- **D0**：兼容/演进专用，满足引用复核后删除条件。
- **R**：保留事实语义但重写结构或 contract。
- **R→D**：先迁移到新 owner，再删除旧文件。
- **K**：当前 owner/可靠性能力保留；后续可迁移目录，不等于永远不重构。
- **K﻿?**：需要确认是否仍有显式 preview/fixture 消费，暂不删除。

## 3. 删除候选

### 3.1 BFF 兼容/演进脚本（D0）

- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/scripts/evolve-agent-failure-schema.mjs`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/scripts/evolve-message-feedback-schema.mjs`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/scripts/evolve-message-final-answer-schema.mjs`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/scripts/evolve-message-parts-schema.mjs`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/scripts/evolve-message-regeneration-schema.mjs`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/scripts/evolve-personalization-schema.mjs`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/scripts/evolve-project-mcp-recommendations-schema.mjs`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/scripts/evolve-project-pin-schema.mjs`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/scripts/evolve-skill-share-usage-schema.mjs`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/scripts/message-schema-evolution.mjs`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/scripts/personalization-schema-evolution.mjs`

这些脚本当前被 `package.json`、`test/architecture.test.ts` 或 evolution 测试引用；删除时必须同步删引用。

### 3.2 BFF 演进测试（D0）

- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/test/agent-failure-schema-evolution.integration.mjs`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/test/message-parts-schema-evolution.integration.mjs`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/test/message-regeneration-schema-evolution.integration.mjs`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/test/personalization-schema-evolution.integration.mjs`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/test/project-mcp-recommendations-schema-evolution.integration.mjs`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/test/project-pin-schema-evolution.integration.mjs`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/test/skill-share-usage-schema-evolution.integration.mjs`

替代证据为 fresh canonical schema/contract 测试，不保留迁移路径。

### 3.3 BFF 全局组合器（R→D）

- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/application/ports/bff-business-store.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/infrastructure/postgres/repositories.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/application/services.ts`

删除条件：Account/session、Projects、Agent Runs、AG-UI Nest modules 完成 provider 注册并通过 Root 验证。

### 3.4 C-1 exact disposition manifest

下列清单是 C-1 的闭集；未列出的关键词命中按 §6.3/§7 分类为当前语义或外部协议，不得因关键词直接删除。

| Owner | 文件 | disposition | replacement/evidence |
|---|---|---|---|
| BFF | `scripts/evolve-agent-failure-schema.mjs`, `scripts/evolve-message-feedback-schema.mjs`, `scripts/evolve-message-final-answer-schema.mjs`, `scripts/evolve-message-parts-schema.mjs`, `scripts/evolve-message-regeneration-schema.mjs`, `scripts/evolve-personalization-schema.mjs`, `scripts/evolve-project-mcp-recommendations-schema.mjs`, `scripts/evolve-project-pin-schema.mjs`, `scripts/evolve-skill-share-usage-schema.mjs`, `scripts/message-schema-evolution.mjs`, `scripts/personalization-schema-evolution.mjs`, `scripts/skill-share-usage-schema-catalog.mjs` | delete | fresh canonical `database/schema.sql`, current catalog and owner contract tests |
| BFF | `test/agent-failure-schema-evolution.integration.mjs`, `test/message-final-answer-schema.integration.mjs`, `test/message-parts-schema-evolution.integration.mjs`, `test/message-regeneration-schema-evolution.integration.mjs`, `test/personalization-schema-evolution.integration.mjs`, `test/project-mcp-recommendations-schema-evolution.integration.mjs`, `test/project-pin-schema-evolution.integration.mjs`, `test/skill-share-usage-schema-evolution.integration.mjs` | delete | corresponding current HTTP/contract/integration tests |
| BFF | `test/architecture.test.ts`, `test/message-feedback.integration.mjs`, `test/project-pin-schema.test.mjs`, `package.json`, `INDEX.md`, `README.md`, `docs/CURRENT.md`, `docs/TECHNICAL_DESIGN.md` | rewrite | remove evolution references only; preserve current feedback/pin/schema facts |
| App | `src/components/blocks/app-frame/app-frame-helpers.ts`, `src/components/blocks/app-frame/use-app-frame-navigation.ts` | rewrite | canonical query URL + direct deep-link/back-forward tests |
| App | `src/core/projections.ts`, `src/core/reducer.ts`, `src/core/state.ts`, `src/engine/machine.ts`, `src/ui/shell/page-clients.ts`, `src/ui/thread/answer-action-scope.ts`, `src/ui/thread/assistant-turn.tsx`, `src/ui/thread/completed-turn-sections.ts` | rewrite | ordered public positions, canonical terminals/final reference, explicit `localDraft` |
| App | `src/core/INDEX.md` | rewrite | document canonical state only |
| App | `tests/core/final-answer-reference.test.ts`, `tests/core/message-parts.test.ts`, `tests/core/projections.test.ts`, `tests/core/run-terminals.test.ts`, `tests/ui/answer-actions-wiring.test.tsx`, `tests/ui/app-frame-navigation.test.tsx`, `tests/ui/whole-turn-process.test.tsx` | rewrite | canonical contract/reducer/navigation regression evidence |
| Agent | `src/kokoro_agent/application/run_display.py`, `src/kokoro_agent/infrastructure/checkpoint_display.py` | rewrite | typed RunDisplay from current journal/checkpoint/frozen recipe |
| Agent | `tests/unit/chat/test_historical_mcp_display.py` | rewrite | current typed display/failure evidence |
| App auth | `src/app/api/auth/[...nextauth]/route.ts`, `src/lib/server/oidc-provider.ts`, `src/lib/server/oidc-token.ts`, `src/lib/server/oidc-rp-transaction.ts`, `src/lib/server/oidc-transaction-cookies.ts`, `src/lib/server/oidc-csrf.ts`, `src/lib/server/oidc-bff-agent.ts`, `src/app/auth/consent/route.ts`, `src/app/iam/interactions/consent/route.ts` | delete after native cutover | IAM artifact `native-session-admission.v1.json`, App native adapter tests |
| App auth | `src/app/iam/[...path]/route.ts`, `src/app/auth/sign-in/route.ts`, `src/app/auth/select-tenant/route.ts`, `src/app/iam/interactions/select-tenant/route.ts`, `src/lib/server/product-identity.ts`, `src/lib/server/product-session.ts`, `src/lib/server/product-session-store.ts`, `src/proxy.ts` | rewrite native adapter; delete Product Session files after consumer cutover | native session admission; no Product Session projection, access/refresh token, or fallback |
| Capability auth | `src/infrastructure/iam/platform-workload-authorizer.ts` and its `global_register` operation catalog/tests | rewrite in C-1.3 auth cutover | direct service credential; retain third-party MCP OAuth |

The C-1 production commits are pinned in `docs/superpowers/evidence/2026-10-31-task-a-c1-cleanup-implementation.md`; first-party auth rows remain future work and are explicitly not claimed as implemented by C-1.

## 4. 保留候选

### 4.0 后端框架现状（只读确认）

当前 TypeScript 后端 owner 的框架分布如下：

| 子仓 | 当前框架 | 本轮结论 |
|---|---|---|
| `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-iam` | NestJS 12 + Express | 保留当前 Nest 模块边界 |
| `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-capability` | NestJS 12 + Express/Connect | 保留当前 Nest 模块边界 |
| `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-system` | NestJS 12 + Express | 保留当前 Nest 模块边界 |
| `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-billing` | NestJS 12 + Fastify | 保留当前 Nest 模块边界 |
| `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-storage` | NestJS 12 + Fastify/Connect | 保留当前 Nest 模块边界 |
| `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff` | 手写 Node HTTP，无 Nest 依赖 | 本轮唯一 TypeScript 后端迁移到 NestJS 的对象 |
| `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-agent` | Python | 遵循 Python owner 规范，不迁 NestJS |
| `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-scheduler` | Go | 遵循 Go owner 规范，不迁 NestJS |

因此“其他后端按 NestJS 规范”对 TypeScript owner 基本成立，但不是所有后端都使用 NestJS；语言边界保持各自规范。BFF 的非 Nest 运行时是明确结构性偏差，不是风格选择。

BFF Nest adapter 的只读建议为 `@nestjs/platform-express`：IAM/Capability/System 已使用 Express，BFF 当前 97 个文件直接依赖 `IncomingMessage/ServerResponse`、30 个 SSE 相关文件、42 个 `rawHeaders` 使用点，Express 的原生 Node req/res 接缝更接近现有语义；Fastify 作为其他 owner 的选择继续保留在各自边界。进入 C-2 前仍需以 focused transport tests 验证 SSE、原始 body/header、取消和有界读取，不同时维护 Express/Fastify 双运行时。

### 4.1 Agent 当前可靠性 owner（K）

- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-agent/src/kokoro_agent/domain/run/`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-agent/src/kokoro_agent/infrastructure/postgres_run_repository.py`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-agent/src/kokoro_agent/infrastructure/postgres_run_interactions.py`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-agent/src/kokoro_agent/infrastructure/postgres_run_leases.py`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-agent/src/kokoro_agent/infrastructure/postgres_run_events.py`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-agent/src/kokoro_agent/interfaces/http/ingress.py`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-agent/src/kokoro_agent/application/chat/service.py`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-agent/src/kokoro_agent/domain/chat/repositories.py`

`history/replay` 在这些路径中是当前 durable 能力，不按名称删除。

### 4.2 BFF 复杂持久化边界（K，迁入 feature module）

- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/infrastructure/postgres/chat-repository.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/infrastructure/postgres/chat-turn-commit.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/infrastructure/postgres/agui-projection-repository.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/infrastructure/postgres/agui-consumer-repository.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/infrastructure/postgres/agent-dispatch-outbox-repository.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/infrastructure/postgres/agent-cancellation-outbox-repository.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/infrastructure/postgres/project-scope-release-outbox-repository.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/infrastructure/postgres/conversation-move.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/infrastructure/postgres/conversation-move-lease.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/infrastructure/postgres/message-parts.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/infrastructure/postgres/message-parts-read.ts`

保留依据：事务、CAS、lease、outbox、幂等或复杂查询。后续只改变 owner 归属和注入方式。

### 4.3 其他 NestJS 后端基线（K）

- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-capability/src/app.module.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-iam/src/app.module.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-system/src/app.module.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-billing/src/app.module.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-storage/src/app.module.ts`

这些仓库当前已使用 NestJS，不纳入本轮整体删除；后续按 feature 逐个审计 Repository 取舍。

## 5. 重写候选

### 5.1 BFF NestJS bootstrap/组合（R）

- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/main.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/bootstrap/server.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/bootstrap/runtime.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/config/runtime.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/http/routes/routing.ts`

目标：唯一 Nest bootstrap、AppModule、database/config/health/http 横切模块，删除手写 Node route dispatcher。

### 5.2 BFF A 相关入口（R）

- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/http/routes/agent.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/http/routes/chat.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/http/routes/run-display.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/http/routes/move-session.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/http/routes/project-rename.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/http/routes/project-delete.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/http/routes/project-deletion-status.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/http/routes/scheduled-task-read.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/http/routes/scheduler.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/application/chat-service.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/application/chat-turn-service.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/application/project-service.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/application/ports/chat-repository.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/application/ports/project-repository.ts`

目标：Controller 只处理输入/输出，Service/Provider 处理用例，复杂持久化边界 feature-local。

### 5.3 App 会话/恢复/显示（R）

- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/src/core/conversations.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/src/core/persistence.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/src/core/reducer.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/src/core/projections.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/src/core/final-answer-reference.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/src/components/blocks/app-frame/app-frame-helpers.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/src/components/blocks/app-frame/use-app-frame-navigation.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/src/engine/machine.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/src/engine/client.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/src/engine/execution-adapter.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/src/engine/reattach.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/src/engine/submission-recovery.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/src/contract/chat.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/src/contract/agui-events.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/src/contract/http.ts`

删除目标：hash conversation URL、inline/ordered 双读、timeline fallback、旧 producer optional 兼容。
`localDraft` 是当前未提交会话的显式 UI 来源证明，不代表 owner 已创建；保留其 canonical draft lifecycle，A-01 只重写其与 owner create/retry/retire 的边界。`conversationTitle` 为空标题时的首条用户消息派生也先按当前展示语义验收，不按名称直接删除。

### 5.4 Agent display（R）

- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-agent/src/kokoro_agent/application/run_display.py`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-agent/src/kokoro_agent/domain/chat/projection.py`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-agent/src/kokoro_agent/infrastructure/checkpoint_display.py`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-agent/src/kokoro_agent/interfaces/http/run_display.py`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-agent/src/kokoro_agent/interfaces/http/server.py`

删除目标：`legacy_failed`、旧 source digest 特判、从旧参数/历史事件补 display detail。
`frozen recipe` 是当前 Run 的 canonical execution fact 与完整性校验，保留 `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-agent/src/kokoro_agent/infrastructure/checkpoint_display.py`、`/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-agent/src/kokoro_agent/model/call_artifacts.py` 中的校验，不按名称删除。

## 6. 测试清理

### 6.1 重写

- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/tests/core/conversations.test.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/tests/core/persistence.test.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/tests/core/projections.test.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/tests/ui/app-frame-navigation.test.tsx`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/tests/engine/engine.test.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/tests/engine/reattach.test.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/tests/engine/submission-recovery.test.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/test/architecture.test.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/test/chat-service.test.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/test/agent-display-projection.test.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/test/agent-run-display-http.test.mjs`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-agent/tests/unit/chat/test_historical_mcp_display.py`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-agent/tests/integration/database/test_run_display.py`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-agent/tests/contract/test_final_display_contract.py`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-agent/tests/contract/test_run_display_contract.py`

### 6.2 暂不删除，先确认用途（K?）

- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/tests/dev/preview-clients.test.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/tests/dev/preview-transport.test.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/tests/scheduled/preview-storage.test.tsx`

这些测试是否保留取决于 preview 是否仍是显式隔离的开发 surface；不得作为 live fallback 或默认业务门禁。

### 6.3 关键词扫描不是删除清单

对 App/BFF/Agent tests 做 `legacy|compat|fallback|oidc|oauth2|schema-evolution|historical` 扫描会命中大量真实当前语义（错误闭集、MCP transport、OAuth provider、replay、frozen recipe、focus fallback、preview fixture）。因此测试清理以 6.1、11.5 和生产消费者反向引用为准：关键词命中只触发人工分类，不直接批量删除。

### 6.4 默认脚本与资源矩阵（G0 闭集）

| Owner | 默认入口 | 当前/目标职责 | 资源要求 | 结果证据 |
|---|---|---|---|---|
| App | `pnpm contract`, `pnpm test:architecture`, `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build` | canonical Web contract、architecture、unit/integration、生产构建；`pnpm test:e2e` 作为浏览器层单独入口 | 默认不要求 PG/Redis；真实 App/BFF/IAM 旅程使用隔离 origin/session | C-1 受影响 Vitest；清理后 canonical conversation/engine/navigation tests |
| BFF | `pnpm format:check`, `pnpm lint`, `pnpm typecheck`, `pnpm contract:check`, `pnpm test:architecture`, `pnpm test`, `pnpm build` | 生成 contract、architecture、unit/HTTP、默认集成替身；`pnpm test:integration` 只在独立 PG/Redis 上运行 | Redis DB 8；PG/Redis 缺失则明确 SKIP，不算 PASS | Nest architecture + feature contract/HTTP + disposable integration |
| Agent | `uv run ruff format --check .`, `uv run ruff check .`, `uv run pyright`, `uv run pytest`, `uv build` | canonical Run/RunDisplay/worker contract 与 Python package | 默认排除 integration/e2e/acceptance；真实验证显式 fixture | display contract/integration、worker recovery、wheel/sdist |
| Root | `git diff --check`, `python3 scripts/verify-repository-topology.py`, `python3 -m pytest scripts/tests -q` | 只验证组合拓扑与治理，不复制子仓业务测试 | 无业务服务 | Root gitlink、文档链接、治理报告 |

BFF 的 `test` 文件列表在 C-4 迁移时改为按 `test/unit`, `test/contract`, `test/integration`, `test/architecture` 职责发现；在迁移完成前保留现有显式列表作为基线，禁止以删除测试来消除失败。App/Agent 的 preview fixture 仅在显式 preview/dev 命令中运行，不进入默认 live 门禁。

### 6.5 测试/fixture/generated disposition 规则

| 类别 | disposition | 替代证据 |
|---|---|---|
| BFF `schema-evolution` tests/scripts/catalog | 删除；C-1 已按消费者反向顺序清理 | fresh canonical schema、contract 与现有业务 integration |
| App hash/inline/ordered/fallback tests | 重写为 canonical query URL、ordered parts、public position 与 final reference | `tests/core`, `tests/engine`, navigation E2E |
| Agent `legacy_failed`/source-digest display tests | 重写为 typed RunDisplay/journal/checkpoint evidence | display contract、run-display HTTP、真实 PG |
| `preview-*` tests | 保留但移出默认 live；若无显式 preview consumer 则删除 | dedicated preview command only |
| generated client/artifact snapshots | 保留唯一生成物；删除已无生产 consumer 的 snapshot/oracle | generator `--check` + consumer contract |
| fixtures/helpers 只服务删除项 | 与删除项同提交删除 | 反向 `rg` 零生产/默认脚本引用 |

逐文件审计输出必须记录 `path, disposition, producer/consumer, replacement, test command`；关键词扫描结果只能产生审计候选，不直接产生删除操作。

## 7. 不得误删的能力

以下名称即使包含 `history`、`replay`、`fallback`、`unknown`，也必须先证明是兼容逻辑后再处理：

- durable event replay；
- idempotency/receipt replay；
- CAS/lease/outbox 重放；
- cancel/late-result reconciliation；
- AG-UI cursor replay；
- snapshot → replay → live 恢复；
- unknown/failed 终态保护；
- UI 焦点恢复和资源缺失时的可见错误态。

## 8. 只读动作状态

1. **已完成**：D0 文件 import graph、package script、architecture test 引用复核。
2. **已完成**：R→D 文件与 Nest feature/provider 映射，未写实现。
3. **已完成**：Repository 调用方、事务边界、owner 和并入 Service 条件记录。
4. **已完成**：测试生产消费者、独有行为证据和默认脚本引用记录。
5. **已完成**：C-1/C-2/C-3/C-4 停写边界已形成，执行顺序见 [执行计划](../plans/2026-10-30-task-a-cleanup-refactor-execution.md)。

当前仍停在 G0 设计门；本文件与执行计划补齐闭集后，需由审阅者确认并由用户放行，才进入后续清理实现阶段。

## 9. 本轮引用复核证据

### 9.1 Schema Evolution 引用

- BFF `package.json` 的 `format:check`、`test`、`contract:test` 和相关专用脚本仍包含 evolution 文件名。
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/test/architecture.test.ts` 直接读取多份 `evolve-*.mjs`、schema catalog 和演进文件；删除时必须先改 architecture oracle。
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/test/project-pin-schema.test.mjs` 直接 import `scripts/evolve-project-pin-schema.mjs`。
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/test/message-final-answer-schema.integration.mjs`、`message-regeneration-schema-evolution.integration.mjs` 和相关 personalization/project tests 仍通过脚本建立演进夹具。

结论：这些文件不是“删文件即可”，需要同步清理 package scripts、architecture test、schema catalog 和 fixture 入口；但它们不应迁移成 runtime compatibility。

只读引用计数（按脚本文件名反向搜索）：`evolve-agent-failure-schema.mjs` 3 个消费者、`evolve-message-feedback-schema.mjs` 4 个、`evolve-message-parts-schema.mjs` 3 个、`evolve-personalization-schema.mjs` 4 个、`evolve-project-mcp-recommendations-schema.mjs` 6 个、`evolve-project-pin-schema.mjs` 4 个、`evolve-skill-share-usage-schema.mjs` 1 个；因此 C-1 必须按“脚本 → package script → architecture oracle → evolution test/fixture → generated/catalog 文档”顺序停写删除，不应先单独删文件。

### 9.2 BFF 全局组合引用

- `BffBusinessStore` 被 `src/bootstrap/runtime.ts`、`src/bootstrap/server.ts`、scheduler/agent/project route 和多个测试直接引用。
- `PostgresBffRepositories` 当前由 `src/bootstrap/runtime.ts` 作为生产组合入口构造。
- `BffApplicationServices` 当前由 `PostgresBffRepositories` 构造并暴露为 `businessStore.services`。

只读反向搜索计数：`BffBusinessStore` 27 个文件、`PostgresBffRepositories` 14 个文件、`BffApplicationServices` 5 个文件、旧 Chat port 16 个文件、`ProjectRepository` 10 个文件。该引用面证明迁移必须先建立 Nest feature provider 图，再逐 route/provider 切换；当前不适合单文件删除。

结论：三者属于 **R→D**，必须先建立 Nest module provider 图，再删除旧组合器；当前阶段不应直接删除。

### 9.3 App/Agent 兼容引用

- App `localDraft` 主要集中在 `core/conversations.ts`、`core/persistence.ts`、`engine/machine.ts`、AppFrame 导航和对应 core/engine/UI tests；当前文档已证明它是 canonical 未提交状态，不列入 D0 删除。清理目标是移除其伪 owner/fallback 解释，不删除 draft 本身。
- App conversation hash 兼容集中在 `app-frame-helpers.ts` 与 `use-app-frame-navigation.ts`，需要同步移除 hash parser、hash normalization 和相关 E2E 断言。
- Agent `legacy_failed`、旧 source digest 特判和 reviewed legacy display 分支集中在 `application/run_display.py` 及 `test_historical_mcp_display.py`、`test_run_display.py`；`frozen recipe` 校验属于当前 execution fact，保留并单独验证。
- IAM scope evolution 兼容标记集中在：
  - `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-iam/src/modules/auth/oauth/clients/account-profile-scope.service.ts`
  - `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-iam/src/modules/auth/oauth/clients/account-session-scope.service.ts`
  这些是 IAM owner 的 scope provisioning 演进逻辑；方案 B 不把第三方/Open App OAuth 能力一起删除，后续须按 OAuth client 是否仍被外部消费者使用分别裁决。

结论：App/Agent 这些文件以 **R** 为主，删除的是符号/分支和对应测试，不是整文件直接删除。

## 10. Repository 复杂度初判

### 10.1 必须拆分，不应继续作为单一巨型 Port

- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/application/ports/chat-repository.ts`
  - 当前同时承载会话列表、snapshot、message parts、Run process、final answer、archive、feedback、share、move、delete。
  - 目标拆为 feature-local reader/writer：Account/session、Messages、RunDisplay、Archive、Share、Feedback。
  - 不是直接删除，而是拆分后删除旧巨型 interface。

- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/application/ports/project-repository.ts`
  - 当前同时承载 project CRUD、rename/delete、pin、MCP recommendations、Skill selection、instruction revision、Task list。
  - 目标拆为 Projects、ProjectTasks、ProjectPins、ProjectRecommendations、ProjectSkillSelection。

### 10.2 保留，但迁入 feature module

- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/application/ports/idempotency-repository.ts`
  - 保留：receipt claim/CAS/release 是跨 mutation 的真实持久边界。

- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/application/ports/scheduled-task-repository.ts`
  - 保留：任务事实、Scheduler outbox、callback lookup 和事务写入存在真实边界。
  - 仍需拆分 read、mutation、outbox，不保留一个万能接口。

- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/application/ports/personal-knowledge-repository.ts`
  - 保留：revision、limit、usage 开关和删除 tombstone 具有独立事实边界。

- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/application/ports/public-share-repository.ts`
  - 保留：公开分享读取与本人 Chat 读取是不同权限边界。

### 10.3 可能并入 feature Service 的薄 Port

- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/application/ports/personalization-repository.ts`
  - 只有 read/replace 两个操作；若当前唯一调用方和唯一 PostgreSQL 实现确认无独立适配器需求，可并入 PersonalizationService。

- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/application/ports/project-execution-binding-reader.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/application/ports/submitted-agent-run-reader.ts`
  - 先确认是否只是 Agent admission 的窄 reader；若没有第二实现，迁入 AgentRunsModule provider，不保留全局 Port 目录。

结论：Repository 清理不是“全部删除”，而是删除机械包装、拆分巨型接口、保留真实事务/权限/owner 边界。

### 10.4 当前复杂度证据

| 文件 | 当前规模 | 只读结论 |
|---|---:|---|
| `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/application/ports/chat-repository.ts` | 171 行、跨会话/消息/parts/Run/归档/分享/反馈/移动/删除 | 拆为 feature-local ports；不整体删除底层事务实现 |
| `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/infrastructure/postgres/chat-repository.ts` | 696 行 | 保留真实复杂查询/事务，按 Chat/Account-session/RunDisplay feature provider 拆迁 |
| `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/application/ports/project-repository.ts` | 67 行、项目 CRUD + pin + recommendations + instructions + skills + tasks | 拆 Projects/ProjectTasks/ProjectPins/Recommendations/SkillSelection |
| `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/infrastructure/postgres/project-repository.ts` | 262 行 | 保留 owner/事务事实，拆 provider 方法集合 |
| `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/application/ports/scheduled-task-repository.ts` | 63 行 | 保留：任务事实、Scheduler outbox、callback 与事务状态 |
| `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/infrastructure/postgres/scheduled-task-repository.ts` | 696 行 | 保留真实 lease/outbox/锁，按 feature provider 注入 |
| `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/application/ports/idempotency-repository.ts` | 23 行 | 保留：receipt claim/CAS/release 是跨 mutation 的事实边界 |
| `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/infrastructure/postgres/repositories.ts` | 133 行 | R→D：Nest provider 图完成后删除全局组合器 |
| `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/application/services.ts` | 约 70 行 | R→D：feature Service 直接注入，不保留全局 `BffApplicationServices` 聚合器 |
| `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/application/ports/bff-business-store.ts` | 52 行、聚合多个 outbox/reader/service | R→D：删除服务定位器，按 Nest module provider 暴露窄依赖 |

这组证据支持“拆巨型接口、保留复杂持久化、删除全局组合器”的取舍，不支持全仓机械删除 Repository 或建立新的 BaseRepository。

### 10.5 全量 Port disposition（G0 闭集）

下表覆盖 `apps/kokoro-bff/src/application/ports/*.ts` 当前全部 23 个 Port。`保留` 表示迁入对应 feature module；`拆分` 表示旧接口删除、底层真实事务/查询继续保留；`并入` 表示删除 Port 抽象但保留具名 provider；`删除` 仅适用于全局 locator。

| 文件 | 结论 | 新 owner/provider | 证据与替代测试 |
|---|---|---|---|
| `agent-cancellation-delivery.ts` | 保留 | `AgentRunsModule` delivery provider | Agent cancel outbox/late result；`agent-cancellation-outbox.test.ts` |
| `agent-cancellation-outbox-repository.ts` | 保留 | `AgentRunsModule` repository | transaction/CAS/outbox；cancellation integration |
| `agent-dispatch-delivery.ts` | 保留 | `AgentRunsModule` delivery provider | dispatch identity/lease；dispatch HTTP/contract tests |
| `agent-dispatch-outbox-repository.ts` | 保留 | `AgentRunsModule` repository | unique receipt/outbox；dispatch integration |
| `bff-business-store.ts` | 删除 | 各 feature module exports | 仅服务定位器；Nest architecture gate + feature tests |
| `chat-repository.ts` | 拆分 | `ChatModule` + `AguiModule` + `AgentRunsModule` readers/writers | 171 行跨事实接口；chat/message/AG-UI/run display tests |
| `idempotency-repository.ts` | 保留 | `IdempotencyProvider` exported narrowly | receipt claim/CAS/release；idempotency contract/integration |
| `personal-knowledge-repository.ts` | 保留 | `AccountModule` personalization provider | revision/limit/tombstone；personal-knowledge tests |
| `personalization-repository.ts` | 并入 | `AccountModule` `PersonalizationService` | 单实现 read/replace；input/HTTP/transaction tests |
| `project-execution-binding-reader.ts` | 并入 | `ProjectsModule` execution-binding reader | 单一 Agent admission reader；execution-binding HTTP/contract |
| `project-repository.ts` | 拆分 | `ProjectsModule` project/pin/recommendation/task providers | CRUD + pin/recommendation/task 混合；对应 feature tests |
| `project-scope-release-outbox.ts` | 保留 | `ProjectsModule` scope-release provider | scope release/outbox/rollback；project deletion integration |
| `public-share-repository.ts` | 保留 | `AccountModule` public-share repository | public/private permission boundary；share HTTP/ACL tests |
| `scheduled-agent-dispatch-delivery.ts` | 保留 | `ScheduledTasksModule` delivery provider | Scheduler→Agent identity；scheduler dispatch tests |
| `scheduled-agent-dispatch-repository.ts` | 保留 | `ScheduledTasksModule` repository | durable dispatch/terminal state；integration |
| `scheduled-task-outbox-delivery.ts` | 保留 | `ScheduledTasksModule` outbox delivery | outbox retry/fencing；scheduled outbox tests |
| `scheduled-task-outbox-repository.ts` | 保留 | `ScheduledTasksModule` repository | transaction/outbox claim；scheduled integration |
| `scheduled-task-repository.ts` | 拆分 | `ScheduledTasksModule` read/mutation providers | task facts + callback/outbox 分离；scheduled HTTP/DB tests |
| `scheduled-task-state-reader.ts` | 保留 | `ScheduledTasksModule` state reader | Scheduler state projection；read contract tests |
| `scheduler-dispatch-receipt-repository.ts` | 保留 | `ScheduledTasksModule` receipt provider | receipt replay/idempotency；receipt integration |
| `skill-share-repository.ts` | 保留 | `SkillsModule` share provider | share ACL/usage boundary；skill-share tests |
| `stable-id-generator.ts` | 并入 | feature-scoped `StableIdProvider` | deterministic ID only；unit tests, no standalone port |
| `submitted-agent-run-reader.ts` | 并入 | `AgentRunsModule` submitted-run reader | single admission read path；submitted-run integration |

删除条件固定为：新 provider graph 编译通过、旧 Port 零生产 import、对应 contract/integration 测试已迁移；未满足前不得删除底层 PostgreSQL 文件。

## 11. Login/OAuth 只读审计

### 11.1 当前实际存在的三类 OAuth/Token 路径

#### A. First-party Web 登录仍走 OIDC/Auth.js

证据路径：

- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/src/app/api/auth/[...nextauth]/route.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/src/lib/server/oidc-provider.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/src/lib/server/oidc-token.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/src/lib/server/oidc-rp-transaction.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/src/lib/server/oidc-transaction-cookies.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/src/app/iam/[...path]/route.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/src/app/auth/sign-in/route.ts`

当前流程包含：Auth.js CSRF → `/iam/oauth2/authorize` → IAM sign-in/consent/tenant continuation → callback → token exchange → Product Session/Redis。

这不是第三方 MCP OAuth，而是本产品 Web 作为 IAM OAuth/OIDC client 的 first-party 登录链。当前 ADR-035 明确保留它，但用户最新反馈要求重新审查该决定。

#### B. 内部机器认证

当前已部分切换为 direct service credential：

- BFF Platform client：`/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/infrastructure/clients/platform/platform-service-credential.ts`
- Agent Platform credential：`/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-agent/src/kokoro_agent/clients/platform_credentials.py`
- Capability local service policy：`/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-capability/src/infrastructure/auth/platform-service-auth.policy.ts`
- Capability service credential reader：`/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-capability/src/infrastructure/auth/platform-service-credentials.ts`

这些路径没有看到 `client_credentials` exchange；Bearer 变量是本地服务凭据，不等于 OAuth access token。

但 Capability 仍保留一个明确的机器 OAuth 例外：

- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-capability/src/infrastructure/iam/platform-workload-authorizer.ts`
- `global_register` 仅允许 `kokoro-system`，当前仍调用 IAM workload introspection。

这是当前内部 OAuth 的明确残留，不应被“普通 BFF/Agent 已改 direct credential”掩盖。

#### C. 第三方/外部能力 OAuth

以下属于合法外部授权，不应按内部 OAuth 删除：

- MCP provider OAuth：
  `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-capability/src/modules/mcp/authorization/product-mcp-oauth.service.ts`
- MCP OAuth metadata/token/refresh：
  `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-capability/src/infrastructure/clients/mcp/mcp-oauth-metadata.ts`
- IAM OAuth provider/client/token/consent 作为外部 OAuth issuer 的 owner 实现：
  `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-iam/src/modules/auth/oauth/`

### 11.2 当前不一致

- Root 架构规范和 ADR-035 已规定内部机器不重复走 IAM OAuth/introspection。
- Capability 仍保留 `global_register` workload OAuth 例外。
- IAM `apps/kokoro-iam/docs/SECURITY.md` 仍描述“Trusted service → IAM-issued access token”，与 direct-service 目标不一致，属于待更新文档/目标态残留。
- 方案 B 选定后，以下规范文档必须在实现切片中同步修订，避免文档继续把 Auth.js/OIDC RP 当成当前目标：
  - `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/docs/kokoro-handbook/decisions/ADR-035-direct-internal-service-authentication.md`
  - `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-iam/docs/SECURITY.md`
  - `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/docs/SECURITY.md`
  - `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/docs/TECHNICAL_DESIGN.md` 中 Web/Auth.js/OIDC relay 的目标态段落
- App 的 first-party Web OIDC 仍然是真实运行代码和依赖，不是单纯历史文档。
- BFF relay policy 仍暴露 `/oauth2/authorize`、`/oauth2/token`、`/oauth2/revoke` 等 browser/OIDC 路径；方案 B 已裁决删除这些 first-party relay 入口，仅保留 native session、租户选择和邀请路径。

### 11.3 Auth 清理决策边界

本轮已将两个边界分别裁决：

1. **机器身份决定**：删除全部内部 machine OAuth，包含 `global_register`，统一 direct service credential；保留用户权限检查、execution proof、撤权 barrier 和业务授权。
2. **人类登录决定**：采用方案 B，first-party Web 不再作为 OAuth/OIDC RP，改消费 IAM native session。

方案 B 下的重写/删除候选（按职责分类，不整目录盲删）：

- **删除 first-party OAuth RP：**
  - `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/src/app/api/auth/[...nextauth]/route.ts`
  - `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/src/lib/server/oidc-provider.ts`
  - `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/src/lib/server/oidc-token.ts`
  - `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/src/lib/server/oidc-rp-transaction.ts`
  - `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/src/lib/server/oidc-transaction-cookies.ts`
  - `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/src/lib/server/oidc-csrf.ts`
  - `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/src/lib/server/oidc-bff-agent.ts`
  - `next-auth`、`openid-client` 及仅服务上述 RP 的配置、fixture、测试和环境变量。
- **重写为 native-session adapter：**
  - `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/src/app/iam/[...path]/route.ts`：只保留 `/sign-in/*`、`/get-session`、`/sign-out`、`/organization/set-active`、邀请等 native 路径，删除 `/oauth2/*` browser relay。
  - `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/src/app/auth/sign-in/route.ts`：保留同源表单与 CSRF，改为直接调用 IAM native sign-in，不再调用 `/oauth2/continue`。
  - `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/src/app/auth/select-tenant/route.ts` 与 `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/src/app/iam/interactions/select-tenant/route.ts`：仅在产品仍需要租户选择时保留并改用 native `organization/set-active`；不再承载 OAuth continuation。
  - `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/src/lib/server/product-identity.ts`、`/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/src/lib/server/product-bff.ts`：改为 native session admission / 无凭据 projection，删除 `Bearer access` 依赖。
- **删除 OAuth-only interaction：**
  - `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/src/app/auth/consent/route.ts`
  - `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/src/app/iam/interactions/consent/route.ts`
- **BFF browser relay 重写：**
  - `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/http/routes/iam-protocol-relay.policy.ts`
  - `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/http/routes/iam-protocol-relay.transport.ts`
  - `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/http/routes/iam-protocol-relay.ts`
  - 删除 `/oauth2/authorize`、`/oauth2/token`、`/oauth2/revoke`、`/oauth2/consent`、`/oauth2/continue` 等 first-party relay 入口；保留 native sign-in/session/logout、租户选择与邀请所需路径。
- **native admission 契约的后续 owner 写区（当前只读，不修改）：**
  - IAM：
    - `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-iam/src/modules/auth/internal-access/direct-service-authenticator.ts`
    - `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-iam/src/modules/auth/internal-access/internal-auth.guard.ts`
    - `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-iam/src/modules/auth/internal-access/internal-principal.types.ts`
    - `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-iam/src/config/environment.schema.ts`
    - 新增 feature-local native session admission controller/service/repository、contract/OpenAPI/SDK 与直接凭据配置；旧 `session-authorizations/verify` 的 bearer contract 保持独立。
  - BFF：
    - `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/auth/session-admission.transport.ts`
    - `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/config/runtime.ts`
    - `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/auth/`
    - `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/openapi-ts.iam.config.ts`
    - `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/generated/iam-http/`
    - `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/contract/vendor/kokoro-iam/`
    - 后续发送 allowlist Cookie + BFF native admission credential；不把旧 user Bearer 和新 Cookie 双发。
- **Product Session 取舍：**
  - `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/src/lib/server/product-session.ts`
  - `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/src/lib/server/product-session-store.ts`
  - 结论已固定为 native admission 迁移后整套删除。BFF 直接消费 IAM allowlisted Cookie，不保留无凭据 Product Session 投影、access/refresh token 或双写 fallback。

**关联生产消费者必须同步重写：**

- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/src/proxy.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/src/app/login/route.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/src/app/auth/sign-out/page.tsx`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/src/app/auth/sign-in/failed/page.tsx`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/src/app/app/layout.tsx`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/src/lib/server/iam-relay-policy.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/src/lib/server/iam-logout-response.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/src/lib/server/archived-tasks.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/src/lib/server/shared-tasks.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/src/lib/server/account-profile.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/src/lib/server/INDEX.md`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/src/generated/iam-relay-policy.json`（由唯一 policy 源重新生成，不手改）

同时需要先发布 native-session admission 契约，先闭合身份链路，再删除 OAuth route，避免留下无身份 session。

### 11.4 保留边界

- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/auth/session-admission.transport.ts`：这是用户 session 的在线权限/tenant admission，不等于 machine OAuth mint；先保留。
- IAM 浏览器 Session、CSRF、membership、role、permission：继续由 IAM owner 负责。
- MCP 外部 provider OAuth：继续由 Capability 负责。
- Billing/资金授权、execution proof、撤权 barrier：继续保留，不能因删除 OAuth 混入登录重构。

### 11.5 相关测试待分级

#### 删除（只证明 first-party OAuth RP/兼容 token 生命周期）

- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/tests/server/oidc-provider.test.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/tests/server/oidc-refresh-session-binding.test.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/tests/server/oidc-rp-transaction.test.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/tests/server/login-route.test.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/tests/system/oidc-rp-next-http.integration.test.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/tests/server/product-login-intent.test.ts`

#### 重写（保留 native session/admission 独有证据）

- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/test/iam-protocol-relay-policy.test.ts`（删除 OAuth 路由断言，重写 native-only allowlist）
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/test/iam-protocol-relay-transport.test.ts`（重写 native cookie/session admission）
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/test/iam-protocol-relay.integration.mjs`（删除 first-party OAuth journey，保留 native sign-in/session/logout/invitation）
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/tests/app/iam-relay-route.test.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/tests/app/iam-invitation-route.test.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/tests/server/iam-relay-transport.test.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/tests/server/proxy-sign-in.test.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/tests/system/iam-relay-next-http.integration.test.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/tests/system/iam-rp-proxy-origin-next-http.integration.test.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/tests/server/product-bff.test.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/tests/server/product-identity.test.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/tests/system/product-bff-next-http.integration.test.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/tests/server/product-session-cookie.test.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/tests/server/product-session-singleflight.test.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/tests/server/product-session-store.test.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/tests/system/session-route-http.integration.test.ts`

`product-session-*` 在 native-session admission consumer 切换后整套删除；旧 access/refresh、Redis 双 CAS 与 refresh reservation 断言不迁移，替代证据是 native adapter/admission contract tests。

#### 保留（与 first-party Web OAuth 无关）

- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-iam/test/consumer/auth-flow.consumer.test.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-iam/test/integration/oauth-client-lifecycle.test.ts`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-iam/test/integration/fixed-web-oauth-client.test.ts`：改为验证 Product Web client 已退出/不再被 native Web 使用；IAM 对第三方/Open App 的 OAuth provider 生命周期仍保留。

其中 third-party OAuth issuer、MCP provider OAuth、IAM permission/session admission 测试不因 first-party 登录重构而删除。

### 11.6 已选方案：B（IAM native session，删除 first-party Web OAuth/OIDC RP）

本轮将方案 B 作为目标基线，原因是它与现行 owner 边界一致：浏览器登录和用户会话只能由 `kokoro-iam` 负责，Web 不应为了访问自家 IAM 再注册一个 OAuth client、维护 callback、交换 access/refresh token，并在 App 内再次复制 Product Session 生命周期。其他后端项目并不是各自照抄一套 OAuth；它们的共同规范是：

IAM 当前已经提供 native session 原语，来源为 `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-iam/src/modules/auth/ingress/auth-routes.constants.ts` 与 `better-auth.config.ts`：`/iam/sign-in/email`、`/iam/sign-in/magic-link`、`/iam/get-session`、`/iam/sign-out`。当前 Better Auth cookie attributes 仍固定 `path: "/iam"`，因此方案 B 的设计门还包含同源 App/BFF 请求如何携带该 cookie；优先统一 cookie path 与 native admission，不新增第二套可写 cookie/session。方案 B 不需要新增第二个身份系统；需要新增的是 Web/BFF 消费该 native session 的唯一 admission 机器契约。

- `kokoro-iam`：唯一的浏览器认证、native session、用户身份/租户/权限事实 owner，同时保留向第三方提供 OAuth/OIDC 的 provider 能力；
- `kokoro-app` / `kokoro-admin`：同源 Web 消费 IAM native session。Admin 已按该方向复用 Product Session；App 当前仍是 first-party Auth.js RP，属于本次要删除的重复层；
- `kokoro-bff`：接收 Web 的可信 session context，向 IAM 做在线 session/权限 admission；不 mint、refresh 或 introspect machine OAuth；
- `kokoro-capability` / `kokoro-system` / `kokoro-billing` / `kokoro-storage` / `kokoro-agent`：内部调用使用 direct service credential 与可信 tenant/subject/run context，不实现浏览器 OAuth；
- MCP provider OAuth 与 Billing 资金授权：仍是外部/业务授权边界，继续保留，不能与 first-party 登录混为一谈。

方案 B 的目标链路固定为：

```text
Browser -> App same-origin auth adapter -> IAM native session
Browser -> App same-origin API -> BFF session admission -> IAM current session/permission
 BFF/Agent/System -> owner service direct credential + trusted context
Third-party MCP -> provider OAuth/PKCE (保留)
```

native-session admission 的 G0 fixed design input 为 `IAM native session cookie + BFF direct service credential -> IAM current-session verifier`：IAM 只返回当前 `subject_id`、`tenant_id`、`session_id` 和资格结果，不返回 OAuth token；App 只转发 allowlist cookie，BFF 每次请求在线 admission。当前 `/internal/v1/session-authorizations/verify` 明确依赖 user-delegated Bearer 与 OAuth client/resource/binding，保留给其真实 bearer/Open App 语义；方案 B 已固定独立的 native-session admission contract 和 `kokoro-bff/session_admission` credential profile，不把旧 Bearer endpoint 改成双输入。

Product Session 不保留投影：native admission 直接消费 IAM native session，故删除 Product Session store/cookie 与 refresh reservation；不得继续保存 IAM access token、refresh token、issuer callback state，也不能维护两套可写 session。

方案 B 的实现/清理顺序（仍是只读设计，不改业务代码）：

1. 先在 IAM/Web/BFF 三方发布唯一 native-session admission 机器契约，明确 cookie/session handle、subject、tenant、session revocation、CSRF、logout、跨域/同源边界和失败语义；
2. 在现 App 上标注并停用 Auth.js/OIDC RP、`oidc-*` transaction/token/CSRF/relay 代码及其 first-party tests；
3. 删除 `/iam/oauth2/*` browser relay 中仅服务 Product Web 登录的路径与 BFF relay 测试；保留 IAM 对第三方/原生 provider 所需的 OAuth/OIDC issuer 路径；
4. 在 native admission consumer 切换后整套删除 Product Session；不保留投影、fallback、双读、双写；
5. 最后删除 Capability `global_register` workload OAuth，统一所有机器 surface 为 direct service credential，并同步修正文档、生成契约和测试矩阵。

因此，方案 B 是“统一认证 owner、删除 first-party OAuth 重复层”的目标架构，不是“所有后端都复制 IAM 登录实现”。当前源码尚未达到该目标，必须按上述顺序完成设计门、契约和只读验证后才能实施删除。

### 11.7 Native-session admission contract（G0 exact wire）

唯一 machine artifact：`apps/kokoro-iam/contract/openapi/native-session-admission.v1.json`（相对 Root）。
版本 `1.0.0`，SHA-256 `5cf59df4b7bd9853edfd2eabb31afc236c0ec0db371f9737706fc129484fd83f`。

| 项目 | 固定值 |
|---|---|
| Operation | `POST /internal/v1/native-session-admission/verify` |
| Request body | `null`；禁止 body 自报 `subject_id`、`tenant_id`、`session_id` |
| Required headers | `Authorization: Bearer <direct service credential>`、`Cookie`、`Origin`、`X-Request-Id`、`Accept: application/json` |
| Cookie names | 非生产：`kokoro-issuer.session_token`、`kokoro-issuer.session_data`、`kokoro-issuer.dont_remember`、仅交互需要时的 `kokoro-issuer.session_token.oauth_logout_confirmation`；生产名称逐一加 `__Secure-` |
| Cookie attributes after cutover | `Path=/`、无 `Domain`、`HttpOnly`、`SameSite=Lax`、生产 `Secure`；旧 `Path=/iam` 只在一次性清理响应中删除，不再接受为 admission 输入 |
| Success | `200 {data:{subject_id,tenant_id,session_id,permissions[],session_expires_at},meta:{request_id,contract_version:"1.0.0"}}` |
| Error closed set | `400 native_session_request_invalid`; `401 native_session_missing/native_session_invalid/native_session_revoked/native_session_expired`; `403 native_session_origin_forbidden/native_session_csrf_failed`; `429 native_session_rate_limited`; `503 native_session_service_unavailable`; `504 native_session_deadline_exceeded` |
| CSRF | `Origin === IAM_WEB_ORIGIN`；IAM 原生 unsafe mutation 继续执行自身 CSRF 检查；BFF 不接受浏览器 bearer 或 body 身份 |
| Revocation/logout | IAM 每次鲜读 Session/User/Member/active tenant；sign-out 先撤销当前 session generation，再清目标 `/` 与旧 `/iam` cookie；撤销后继续返回 401，迟到请求不复活 |
| Tenant switch | 由 IAM native `organization/set-active` 更新同一 session；后续 admission 只返回新的 active tenant。请求没有 caller-supplied tenant selector |
| Direct credential | caller=`kokoro-bff`、surface=`session_admission`、audience=`kokoro-iam`；双槽轮换，重叠 15 分钟，旧槽在所有 BFF 实例确认新 generation 后移除；凭据不写日志/响应 |

| Writer | 交付物 | 停写出口 |
|---|---|---|
| IAM | contract、controller/service、generated SDK、direct credential reader、session cookie cutover（G0 后） | IAM contract check、native session HTTP/PG/Redis proof、artifact digest |
| BFF | admission client/provider、Cookie allowlist、请求上下文映射 | BFF contract/type/HTTP/architecture proof，消费 IAM 固定 digest |
| App | same-origin adapter、sign-in/sign-out/tenant flow、旧 RP 删除 | App contract/type/E2E proof；不保留 OAuth token/Product Session 双读 |
| Capability | C-1.3 auth cutover 删除 `global_register` workload OAuth，切 direct credential | machine-auth contract/negative proof；第三方 MCP OAuth 不受影响 |

生命周期顺序固定为：先发行并固定 IAM artifact → BFF/App 成对消费 → 正常 sign-in/refresh/sign-out/tenant-switch/撤权验收 → 删除 App first-party RP 与 BFF OAuth relay → 删除 Capability `global_register` workload OAuth。任何阶段不得先删除旧入口后留下无身份请求，也不得把旧 bearer endpoint 改成 Cookie/bearer 双输入。

## 12. 只读盘点证据

阶段执行顺序与停写边界以 [Task A 清理与重构执行计划](../plans/2026-10-30-task-a-cleanup-refactor-execution.md) 为准；本清单只记录当前事实和路径证据。

2026-10-30 在 Root 工作区重新核验：

- Root 与 §1 列出的 12 个 runtime module/gitlink HEAD 与 §1 完全一致；子仓工作区无业务 diff。
- `python3 scripts/verify-repository-topology.py`：PASS，发现 9 个 runtime owner module，全部 checkout initialized；其余 Admin/Mori/Web shared gitlink 也已核对。
- 本文引用的 208 个绝对路径全部存在；删除/保留/重写清单没有悬空路径。
- TypeScript owner 中 IAM、Capability、System、Billing、Storage 使用 NestJS 12；BFF `package.json` 无 NestJS 依赖；Agent 为 Python，Scheduler 为 Go。
- App 仍声明 `next-auth@4.24.15` 与 `openid-client@5.7.1`，且生产代码仍包含 `/iam/oauth2/*`、Product Session access/refresh 和 Auth.js RP；这证明 first-party OAuth 是当前运行事实，不是历史文档误报。
- IAM native route allowlist 已包含 `/sign-in/email`、`/sign-in/magic-link`、`/get-session`、`/sign-out`；方案 B 有现有 owner 原语可承接，不需要新增第二个 OAuth issuer。
- 本轮未修改业务代码、测试、契约、Schema、lockfile、运行配置或子仓 gitlink；仅更新本 Root 设计/盘点文档。

规范审计补充：

- `python3 scripts/verify-ten-repository-standard.py --format json` 当前结果为 `FAIL`，`violation_count=224`，`unverified_count=0`。
- 与本任务直接相关的失败包括：BFF 缺少 NestJS runtime/bootstrap、BFF `message-parts-read.ts` 兼容标记、App/Agent 兼容标记、IAM OAuth client scope 兼容标记，以及多个跨仓文件粒度/配置边界/契约治理问题。
- 因此“其他 TypeScript 后端使用 NestJS”不等于“所有后端已经完全符合规范”；本轮先收敛 BFF Nest runtime 和 Task A 相关 clean-slate 违规，不把 224 条历史/任务外问题混入本次业务代码修改。
- 盘点纠偏：`localDraft` 与 Agent `frozen recipe` 经源码/INDEX 复核属于当前产品状态/执行完整性事实，不再列为删除候选；清理只针对其周边的旧 hash、伪 owner fallback、旧 source-digest 特判和未证明的历史展示推导。

### 12.1 Task A 首批切片证据边界

- A-01 会话创建/恢复：当前主路径仍分布在 App `core/conversations.ts`、`core/persistence.ts`、AppFrame 导航、`engine/machine.ts` 与 BFF Chat/Project route；本轮先删除旧 hash/双形态兼容，保留并重写 canonical `localDraft` lifecycle，再进入真实创建、URL、刷新、前后退、多标签和迟到响应验收。
- A-02 Agent 展示：`docs/CURRENT.md` 2026-10-28 已记录 native 工具详情读取局部通过，但主行动语义、正文—动作—正文分层、历史/刷新一致性仍 OPEN；先沿 canonical RunDisplay/AG-UI/BFF projection，不新增解释事件或第二套展示协议。
- A-07 Project Todo：当前只读事实为：
  - `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/database/schema.sql` 已存在 `bff_project_task` 表；
  - `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/infrastructure/postgres/project-repository.ts` 只有项目任务读取投影；
  - `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/src/http/routes/live-bff.ts` 目前只暴露 `GET /v1/projects/{projectId}/tasks`；
  - `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/contract/openapi/v1/openapi.yaml` 只有 `listProjectTasks`，未见 create/update/delete Project Todo operation；
  - App 当前 `TodoBar`/`executionProcess.todos` 是 Run 执行进度，不是 Project Todo 事实，不能直接复用为项目任务板。
- A-07 的后续写入顺序固定为：先在 BFF Nest feature module 中冻结 ProjectTask canonical schema/authorization/concurrency/idempotency contract，再生成 App client，最后接页面；不直接 SQL 灌任务、不把 Run Todo 改名成 Project Todo、不保留旧列表兼容入口。

### 12.2 兼容词命中后的边界分类

全量 `rg` 命中不能直接等价为删除项。当前需要分别处理：

- **Task A 明确删除/重写：** `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/src/core/state.ts` 的 `cancelledRuns` 旧字段迁移、`/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/src/ui/thread/assistant-turn.tsx` 的 `legacyFinalId`、`/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app/src/core/reducer.ts` 的 `legacyRenderAnchor`、Agent `run_display.py` 的 `legacy_failed` 与旧 source digest 特判。
- **当前语义保留：** localDraft、frozen recipe、durable replay、contract_incompatible 错误状态、focus/asset fallback 等可靠性或用户状态；逐项以 owner 事实和测试目的确认。
- **Task B/外部协议边界：** `sse_compat` transport、MCP custom form 的历史连接状态、MCP provider/OAuth 兼容、第三方协议字段不在 Task A 清理中；不把 B 的外部协议能力误删为 A 的旧兼容。

这份分类把“兼容强制删除”限定到已确认的旧 wire/旧状态迁移/旧展示推导，同时保护仍然属于当前契约的错误、恢复、外部协议和执行完整性语义。
