# Kokoro 文档总入口

主仓 `docs/` 是产品、架构、业务链路、跨仓规范和历史材料的总入口。当前文件数较多，阅读时先按下面的层级判断，不要从目录树随机翻。

## 阶段 1 当前基线

本轮实际闭环只覆盖 `kokoro` Web、`kokoro-bff` 和 `kokoro-agent` 三个子仓库：Web 负责同源入口，
BFF 负责 Chat 与业务编排，Agent 负责 Run 执行、HITL 和 worker。Chat 不再作为独立仓库，
不使用 `kokoro-gateway`，也不新增独立 `kokoro-session`。

存储基线见 [storage-baseline-v1](../contract/spec/storage-baseline-v1.md)：阶段 1 只使用
PostgreSQL（持久化真源）与 Redis（队列、事件流、租约和短期协调），不再新增 MySQL/MongoDB
运行时依赖。历史文档中的旧 owner、Session/Gateway 及 MySQL/Mongo 组合只用于迁移考古，不能
作为本轮新代码和部署配置的依据。

Root 当前部署只使用 `deploy/docker-compose.phase1.yml` 和 `deploy/provision-phase1.sh`；旧双 Compose、k8s、
全栈 provisioning 和旧拓扑验证入口已移到 Root 外的 `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro-archive-2026-09-01/root-legacy/`。

## 阶段 2 当前收口

阶段 2 的正式仓库是 `kokoro-iam`、`kokoro-system`、`kokoro-model`、`kokoro-billing`、
`kokoro-capability`、`kokoro-storage` 和 `kokoro-scheduler`。每个仓库独立拥有实现、测试、Dockerfile、
CI、发布文档和本仓 API contract；Root 只提供跨仓 contract、拓扑索引、部署入口与验证脚本。Credit 在
Billing 内部，Chat 在 BFF 的 Chat 业务模块边界内，Scheduler 是独立 Go 仓库，不读取其他业务数据库。
本地阶段 2 收口以 [`REPOSITORY_STATUS.md`](REPOSITORY_STATUS.md)、[Goal 2 manifest](../contract/goal2-repository-contract-manifest.json)
和[阶段 2 仓库收口报告](reports/2026-09-01-stage2-repository-closure.md)为准。

## 先看这三个

0. [当前活跃文档白名单](CURRENT.md)
   给 agent 和人类的最小阅读集合。当前主线默认只读这里列出的文档。

1. [Kokoro 总手册](kokoro-handbook/README.md)
   稳定权威入口。正式技术方案、长期规则和 ADR 从这里进入；草案才放 specs。

2. [Codebase Map](CODEBASE_MAP.md)
   给 code agent / worker 的仓库地图。包含根仓、子仓、文档归属、验证命令和并行派工约束。

3. [GA identity 与动态 owner 重验](kokoro-handbook/decisions/ADR-022-run-execution-attestation-and-dynamic-capability-resolution.md)
   当前最容易写错的规则：外部传受信 `ExecutionIdentity(tenant_ref, actor, subject, identity_assertion_ref)`；GA 在 ingress 只从 tenant + subject 派生内部
   `RuntimeNamespace`：仅首次 target bootstrap（普通 Launch claim 或 fork `ForkConversation` prepare） 派生并固化 ThreadLocator，后续新 Launch 以 current identity 验证后复用，Cleanup 以已接受 delete 的 durable tenant-subject lifecycle envelope 验证 locator/fence；已 claim run 的恢复只比较 ledger/locator，完全不等待新 identity。浏览器、Session 和 caller 不提交 namespace/thread，也不以 `userId` / `ownerId` / `workspaceId` 选择图或 checkpoint。

## 当前主线

当前活跃阅读集合以 [CURRENT.md](CURRENT.md) 为**唯一入口**。Agent/Session/Capability 设计时，固定先读：

1. [GA 核心架构总览](kokoro-handbook/technical/42-ga-core-architecture.md)
2. [GA 整体 Agent 最终技术方案](kokoro-handbook/technical/36-ga-final-agent-technical-plan.md)
4. [App、Feature 与 Agent 产品架构](kokoro-handbook/technical/37-product-experience-agent-studio-architecture.md)
5. [GA 公共运行契约](kokoro-handbook/technical/38-ga-public-runtime-contract.md)
6. [GA Evaluation 与运行证据](kokoro-handbook/technical/39-ga-evaluation-and-evidence-architecture.md)
7. [GA 工作画像与有界并行任务](kokoro-handbook/technical/40-ga-work-profiles-and-bounded-fanout.md)
8. [Feature 结果契约与质量门](kokoro-handbook/technical/41-feature-outcome-contracts-and-quality-gates.md)
9. [Session 生命周期](kokoro-handbook/business-flows/session-lifecycle.md)
10. [GA-first SkillRuntime](kokoro-handbook/technical/33-ga-first-skill-runtime-architecture.md)
11. [V1 最终技术方案（仅物理基线）](kokoro-handbook/technical/20-kokoro-v1-technical-plan.md)

`kokoro-chat` 独立分仓、独立 `kokoro-session`、Gateway、Capability runtime snapshot/revision、
Session Agent selection 等资料均为历史迁移材料；不得据此新增目标代码或 contract。

## 按任务找

| 你要做什么 | 先看 |
|---|---|
| 理解整体系统 | `kokoro-handbook/README.md`、`kokoro-handbook/technical/00-system-overview.md` |
| 判断仓库边界 | `CODEBASE_MAP.md`、`kokoro-handbook/technical/01-repository-map.md` |
| 改 agent/session/web 链路 | `kokoro-handbook/technical/36-ga-final-agent-technical-plan.md` + `business-flows/agent-session-web-general-chat-runtime.md` |
| 改 GA identity/auth/运行时隔离 | `kokoro-handbook/technical/38-ga-public-runtime-contract.md` + `kokoro-handbook/decisions/ADR-022-run-execution-attestation-and-dynamic-capability-resolution.md` |
| 改 capability / skill / MCP | `kokoro-handbook/technical/33-ga-first-skill-runtime-architecture.md` + `technical/backend-design/05-capability.md` |
| 改阶段 2 业务域 | `REPOSITORY_STATUS.md`、`contract/goal2-repository-contract-manifest.json` 及对应 `kokoro-*` 仓库的 `docs/README.md` |
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

- `brainstorm/`、`plans/`、`task.md`、`test-cases.md`
  历史工作材料或局部账本。使用前先和 handbook / reports 对齐。

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
3. siteId 是平台业务隔离边界；`RuntimeNamespace` 是 GA/runtime 的唯一**内部**隔离键。两者不能互相替代。
4. 上游只提交服务端构造的 `ExecutionIdentity(tenant_ref, actor, subject, identity_assertion_ref)`；GA ingress 自己只在首次 target bootstrap（普通 Launch claim 或 fork `ForkConversation` prepare） 从 tenant + subject 派生 RuntimeNamespace 并固化 locator，后续新 Launch 以 current identity 验证后复用，Cleanup 以已接受 delete 的 durable tenant-subject lifecycle envelope 验证 locator/fence，已 claim run 只从 ledger/locator 恢复。不得把 caller namespace、ownerId/userId/workspaceId 作为 Agent、graph 或 checkpoint 的第二身份轴传入 GA。
5. 阶段 1 不新增 kokoro-contracts；只使用 PostgreSQL + Redis，不能继续新增 MySQL/MongoDB，
   也不能把 Redis 当长期真源。跨仓契约以 `contract/` 与三仓各自的 v1 摘录为准。
6. 外部参考项目路径、分支名、逐字文案和代码只能放 tmp 中间产物，不进入正式文档或正式代码。

## Agent 负载规则

`docs/` 下有大量历史文件。agent 不应该递归读取整个目录，也不应该把 `product/`、
`prototypes/`、`research/` 当作当前事实来源。进入 `docs/` 时遵守 [docs/AGENTS.md](AGENTS.md)：

```text
默认只读 CODEBASE_MAP.md + README.md + CURRENT.md + 当前任务点名文件。
```
