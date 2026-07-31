# Kokoro 文档总入口

主仓 `docs/` 是产品、架构、业务链路、跨仓规范和历史材料的总入口。当前文件数较多，阅读时先按下面的层级判断，不要从目录树随机翻。

## 先看这三个

0. [当前活跃文档白名单](CURRENT.md)
   给 agent 和人类的最小阅读集合。当前主线默认只读这里列出的文档。

1. [Kokoro 总手册](kokoro-handbook/README.md)
   稳定权威入口。正式技术方案、长期规则和 ADR 从这里进入；草案才放 specs。

2. [Codebase Map](CODEBASE_MAP.md)
   给 code agent / worker 的仓库地图。包含根仓、子仓、文档归属、验证命令和并行派工约束。

3. [Namespace 运行时隔离](kokoro-handbook/technical/17-namespace-runtime-isolation.md)
   当前最容易写错的规则：`siteId` 是平台业务隔离边界，`namespace` 是 GA/runtime 唯一隔离键，GA 不接收 `userId` / `ownerId` 第二轴。

## 当前主线

当前活跃阅读集合以 [CURRENT.md](CURRENT.md) 为**唯一入口**；下面是主线骨架，阅读顺序、附录与派工状态以 CURRENT.md 为准：

1. [联邦产品平台总架构（当前唯一总入口）](kokoro-handbook/technical/24-federated-product-platform-architecture.md)
2. [PostgreSQL Platform / Session 数据边界](kokoro-handbook/decisions/ADR-012-postgresql-platform-session-boundary.md)
3. [Product Memory 与 Context Authority](kokoro-handbook/decisions/ADR-013-product-memory-and-context-authority.md)
4. [Media Operation 与 Artifact Authority](kokoro-handbook/decisions/ADR-015-media-operation-and-artifact-authority.md)
5. [Web Release Composition](kokoro-handbook/decisions/ADR-016-web-release-composition.md)
6. [Contract、Transport 与 Internal RPC 统一技术方案](superpowers/specs/2026-07-27-contract-transport-and-internal-rpc-design.md)

旧 [technical/22](kokoro-handbook/technical/22-capability-hub.md) 只保留 Hub 演进历史；当前 Hub runtime consumer 与
ConnectRPC 边界以 technical/24 和 Root boundary registry 为准。

注意：`handoffs/` 是短期派工单，不是长期权威。派工单里的稳定结论必须回流到 handbook。

历史入口（已过期，不作架构事实，仅供考古）：

- [2026-07-07 能力 buildout 派工单](handoffs/2026-07-07-capability-buildout-handoff.md)
- [2026-07-07 runtime buildout 派工单](handoffs/2026-07-07-runtime-buildout-next-handoff.md)

## 按任务找

| 你要做什么 | 先看 |
|---|---|
| 理解整体系统 | `kokoro-handbook/technical/24-federated-product-platform-architecture.md` |
| 判断仓库边界 | `CODEBASE_MAP.md`、`kokoro-handbook/technical/01-repository-map.md` |
| 改 agent/session/web 链路 | `kokoro-handbook/technical/24-federated-product-platform-architecture.md`、相关 accepted ADR 与子仓 INDEX |
| 改 namespace/auth | `kokoro-handbook/technical/17-namespace-runtime-isolation.md` |
| 改 capability hub / skill / MCP | `kokoro-handbook/technical/24-federated-product-platform-architecture.md`、Root boundary registry、Platform Hub/Agent 子仓 INDEX；旧 product/technical/22 只作历史背景 |
| 改 platform 模块 | `../kokoro-platform/docs/README.md`、`kokoro-handbook/technical/24-federated-product-platform-architecture.md`、模块 INDEX |
| 查验收报告 | `reports/` |
| 查产品原型和设计历史 | `product/`、`prototypes/`、`research/`，但先看 handbook 判断是否仍有效 |
| 给 worker 派活 | `CODEBASE_MAP.md` + 对应 spec/plan/handoff |

## 目录分层

### 权威层

- `kokoro-handbook/`
  长期稳定的总手册。承载正式技术方案、已确认产品形态、模块边界、技术规则和 ADR。

- `CODEBASE_MAP.md`
  给人和 agent 的仓库导航。涉及并行 worker 时必须注入。

### 过程层

- `superpowers/specs/`
  有日期的草案和过程稿。讨论、打磨、方案对比和历史入口放这里；正式版迁入 handbook。

- `superpowers/plans/`
  有日期的实现计划。用于执行，不作为长期权威。

- `handoffs/`
  短期交接稿。只解释“这轮怎么派”，不解释“系统长期是什么”。

- `reports/`
  审计、测试、验收报告。用于证明某阶段状态。

### 产品与历史层

- `requirements/`
  需求、能力、流程和契约映射。

- `product/`
  原型时代和产品形态材料。很多内容是历史设计，不能直接当当前实现事实。

- `prototypes/`
  静态原型、截图和可视化验证材料。

- `research/`、`lessons/`
  外部研究、截图、经验教训。

- `decisions/`
  早期 ADR。当前权威 ADR 入口优先看 `kokoro-handbook/decisions/`。

- `brainstorm/`、`plans/`、`test-cases.md`
  历史工作材料。使用前先和 handbook / reports 对齐。

- `task.md`
  当前跨会话 campaign、候选 commit、阻塞与下一步；不保存历史流水账。

## 写新文档

```text
正式跨仓技术方案    -> docs/kokoro-handbook/technical/
稳定产品/技术规则   -> docs/kokoro-handbook/
跨仓草案/方案对比    -> docs/superpowers/specs/YYYY-MM-DD-*.md
实现计划            -> docs/superpowers/plans/YYYY-MM-DD-*.md
短期派工            -> docs/handoffs/YYYY-MM-DD-*.md
子仓实现细节        -> kokoro-*/docs/
外部参考/截图/探索   -> tmp/ 或 kokoro-*/tmp/
```

治理规则：

1. 子仓 docs 只写实现细节、调试和测试说明，不替代主仓手册。
2. 新关键决策讨论期放 `superpowers/specs/`；作为正式技术方案后迁入 handbook，再落到子仓 README 或实现文档。
3. siteId 是平台业务隔离边界；namespace 是 GA/runtime 的唯一隔离键。两者不能互相替代。
4. GA 只消费 namespace；不得把 ownerId/userId/workspaceId 作为第二身份轴传入 GA。
5. Root `contract/` 是跨仓契约单源，不新增第五个 contracts 仓库；Platform/Session 使用彼此独立的 PostgreSQL
   database，Agent 使用 MongoDB，Redis 不作最终业务真源。
6. 外部参考项目路径、分支名、逐字文案和代码只能放 tmp 中间产物，不进入正式文档或正式代码。

## Agent 负载规则

`docs/` 下有大量历史文件。agent 不应该递归读取整个目录，也不应该把 `product/`、
`prototypes/`、`research/` 当作当前事实来源。进入 `docs/` 时遵守 [docs/AGENTS.md](AGENTS.md)：

```text
默认只读 CODEBASE_MAP.md + README.md + CURRENT.md + 当前任务点名文件。
```
