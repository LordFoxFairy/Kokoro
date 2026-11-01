# Task A C-3 Provider/Service Census（2026-10-31）

## 当前已清除的 global service 重复字段

`BffBusinessStore` 与 `PostgresBffRepositories` 已不再重复暴露：

- Chat：`chatService`
- ChatTurn：`chatTurnService`
- Project：`projectService`
- ScheduledTask：`scheduledTaskService`
- Account personalization：`personalizationProvider`

对应 feature owner：`CHAT_SERVICE`、`CHAT_TURN_SERVICE`、`PROJECT_SERVICE`、`SCHEDULED_TASK_READ_SERVICE` 及 `BffApplicationServices.services` 兼容聚合。

## 仍保留的 transitional raw-server seams

以下字段仍有真实 raw `createBffServer` / `LegacyRoutes` 消费者，暂不机械删除：

| 字段 | 当前消费者 | 删除前置条件 |
|---|---|---|
| `personalKnowledge` | raw compatibility adapter; `LegacyRoutesRuntime` now receives explicit `PERSONAL_KNOWLEDGE_REPOSITORY` | 删除 `BffBusinessStore.personalKnowledge` after raw/test composition consumes the explicit feature provider |
| `skillUsage` | raw Skill usage adapter; `LegacyRoutesRuntime` now receives explicit `SKILL_USAGE_READER` | SkillsModule/SkillsMiddleware 成为唯一 runtime path，删除 `BffBusinessStore.skillUsage` fallback |
| `skillAiAssociation` | AI Skill import raw adapter | SkillsModule association provider 覆盖 raw composition，artifact owner contract 保持不变 |
| `skillShares` | Skill share/exact-download raw composition | SkillsModule share/download provider 覆盖 raw source construction |
| `publicShareService` | raw public-share projection; `LegacyRoutesRuntime` now receives explicit `PUBLIC_SHARE_SERVICE` from `ChatModule` | ChatModule provider 覆盖 raw chain；删除 `BffBusinessStore.publicShareService` fallback after raw/test composition no longer needs it |

这些字段是当前存在证据的兼容边界，不是新的 owner；Account personalization 已从 global store 删除。禁止继续新增同类字段。

## BffApplicationServices 聚合

当前仍有四个聚合字段：

- `projects`
- `scheduledTasks`
- `chat`
- `chatTurns`

其中 Chat/Project/ScheduledTask 的 HTTP provider 已完成具名 feature seam；聚合仅保留给未迁移的 Chat POST/Agent dispatch、LegacyRoutes raw composition、integration fixtures 和剩余兼容路径。

## LegacyRoutes 删除门

当前生产引用仍集中在：

- `src/modules/legacy-routes/legacy-routes.module.ts`
- `src/modules/legacy-routes/legacy-routes.middleware.ts`
- `src/modules/legacy-routes/legacy-routes.runtime.ts`
- `src/bootstrap/server.ts`
- `src/bootstrap/runtime.ts`
- `src/app.module.ts`

删除顺序固定为：剩余 route census 清零 → raw provider fallback 清零 → 唯一 Nest listener/composition proof → 删除 LegacyRoutes runtime/module/middleware。

## 当前验证证据

- BFF architecture：34/34
- Nest runtime architecture：5/5
- Chat/BFF focused：230/230
- ScheduledTask focused：106/106
- BFF full：2316 tests / 2299 pass / 15 fail / 2 skip；15 项失败为既有 Storage/Product、Project exact-download、Admin credential、anonymous Share fixtures。
- Root topology：PASS

## 2026-10-31 provider handoff update

BFF child `330e439` adds the explicit `PUBLIC_SHARE_SERVICE` seam to the transitional runtime. `LegacyRoutesModule` imports `ChatModule`; `LegacyRoutesRuntime` injects `PublicShareApplicationService` and passes it to `createBffComposition`; raw shared-public handling reads `composition.publicShareService`. `BffCompositionOptions.publicShareService` now prefers the feature provider while retaining the store fallback only for un-migrated test/raw composition. This is a provider handoff, not LegacyRoutes completion.

BFF child `46bb5ac` adds the explicit `SCHEDULED_TASK_READ_SERVICE` seam to the transitional runtime. `LegacyRoutesModule` imports `ScheduledTasksModule`; `LegacyRoutesRuntime` injects `ScheduledTaskReadService` and passes it to `createBffComposition`; `BffCompositionOptions.scheduledTaskReader` now prefers that feature provider while retaining the old service-derived reader only for raw/test composition. Current-read behavior remains covered by the existing scheduler focused suite; mutation/callback/outbox routes remain in the next census slice.

A-01/A-02/A-07 继续停写。
