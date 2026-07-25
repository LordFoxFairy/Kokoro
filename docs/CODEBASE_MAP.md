# Kokoro Codebase Map

状态：2026-07-12
用途：给主控会话、code agent 和并行 worker 的最小上下文地图。

## 仓库边界

```text
Kokoro/                 根仓: docs, handbook, cross-repo contract, submodule pins, scripts
  contract/             跨仓契约单源和生成器
  docs/                 总手册、规格、计划、交接、报告、历史资料
  kokoro-agent/         Python agent runtime subrepo
  kokoro-session/       TypeScript session/SSE subrepo
  kokoro-web/           Web pnpm monorepo：apps/user(用户面) + apps/admin(运营后台) + packages/*(共享)
  kokoro-platform/      Platform domain parent subrepo
```

## 文档归属

| 位置 | 放什么 | 不放什么 |
|---|---|---|
| `docs/CURRENT.md` | 当前活跃文档白名单 | 历史材料索引 |
| `docs/kokoro-handbook/` | 稳定跨仓规则、模块边界、业务链路、ADR、技术结论 | 临时派工细节、未审定探索 |
| `docs/superpowers/specs/` | 有日期的技术方案稿 | 子仓局部调试笔记 |
| `docs/superpowers/plans/` | 有日期的实现计划 | 长期权威结论 |
| `docs/handoffs/` | 短期交接和派工单 | handbook 替代品 |
| `kokoro-*/docs/` | 子仓自己的实现边界、调试、测试、接入说明 | 跨仓权威规则 |
| `tmp/` / `kokoro-*/tmp/` | 临时调研、外部参考、截图、中间产物 | 正式方案、代码引用来源 |

## 当前稳定规则

- `siteId` 是平台业务隔离边界。
- `namespace` 是 GA（kokoro-agent runtime）唯一隔离键。
- GA（kokoro-agent runtime）只消费 `namespace`，不消费 `userId` / `ownerId` / `workspaceId`。
- namespace 是 opaque id，不拼 `user:<id>` / `team:<id>` 业务前缀。
- capability registry 采用一个边界，V1 只覆盖 `skill` / `mcp`。
- DeepAgents graph 内部运行节点不是 capability kind，不做 package / enablement。
- web 只消费 session HTTP/SSE，不直连 agent。
- session 不执行 agent。
- agent 不面向浏览器，不写 session messages，不扣积分。
- 外部参考项目路径、分支名、逐字文案和代码只允许出现在 `tmp/` 中间产物。

## 子仓说明

### kokoro-agent

执行层。消费 run request，执行 LangChain/LangGraph/DeepAgents，发布 raw agent events。

正式文档入口：`kokoro-agent/README.md`、`kokoro-agent/docs/README.md`。

常用验证：

```bash
uv run ruff check .
uv run pyright
uv run pytest
```

### kokoro-session

会话和浏览器传输层。拥有 sessions/messages/runs/session_events、snapshot、SSE、HITL control。

正式文档入口：`kokoro-session/README.md`、`kokoro-session/docs/README.md`。

常用验证：

```bash
npm test
npm run typecheck
npm run lint
```

### kokoro-web（pnpm monorepo）

一个子仓两个独立部署的 Next.js app + 共享包（架构地图见 `kokoro-web/INDEX.md`）：

- `apps/user`（`@kokoro/web-user`）：用户面工作台。消费 session HTTP/SSE，走 web BFF 不直连 DB。Next16/React19/antd6。
- `apps/admin`（`@kokoro/admin-web`）：运营后台。NextAuth + Prisma 直连 DB 的特权面。Next16/React19/antd6。
- `packages/*`：`@kokoro/tsconfig`（共享 TS 基线）、`@kokoro/i18n`（i18n 引擎）。

**两 app 当前已统一 Next 16.2.6 / React 19.2.4 / antd 6.5.0 / Vitest 4.1.x**。pnpm 仍使用
`node-linker=isolated` 保护依赖边界；跨仓 TS/Vitest/Node/package-manager/lockfile 分裂由 Wave 0 统一。
正式文档入口：`kokoro-web/README.md`、`kokoro-web/apps/user/docs/README.md`。

常用验证（pnpm workspace）：

```bash
pnpm install
pnpm -r typecheck
pnpm -r test                          # user 484 / admin 25 / i18n 12
pnpm --filter @kokoro/web-user build
```

注意：Next.js 版本有项目规则要求。修改 framework-facing code 前先读
`apps/user/node_modules/next/dist/docs/` 中相关文档。

### kokoro-platform

平台域父仓。管理 site/user/model/credit/payment/litellm/admin 等平台模块和部署/验证约束。

其中 **kokoro-hub**（`@kokoro/hub`，端口 4251）是能力中台模块：skill/MCP 注册管理写面（上传/审核/版本/启停/配额/运营位），与 agent 装配热路径**读写分离同库**（hub 写 Mongo+S3，agent 直读，每 run 不跨 hub RPC）。边界见 `docs/kokoro-handbook/technical/22-capability-hub.md` 与 `docs/kokoro-handbook/modules/kokoro-hub.md`；运营台见 `docs/kokoro-handbook/technical/23-platform-ops-console.md`。

正式文档入口：`kokoro-platform/README.md`、`kokoro-platform/docs/README.md`。

常用验证：

```bash
pnpm test
pnpm test:integration
pnpm typecheck
pnpm lint
```

## 并行派工约束

- 给外部 worker 注入本文件。
- 让 worker 先读 `docs/CURRENT.md`，不要让 worker 递归展开全量 `docs/`。
- worker 完成后必须在主仓重新跑对应验证，不能只信 worker 的 `__EXIT=0`。
- 涉及多个独立写入面时，按子仓/文件树分 worker，避免两个 worker 改同一文件。
- 根仓 handbook/spec 更新要先于子仓实现文档落地。
