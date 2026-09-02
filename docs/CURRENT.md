# 当前活跃文档白名单

状态：2026-09-02
用途：降低 agent 阅读负担。做**目标 GA/Feature-first 架构**的 runtime、capability、deliver 主线时，只读
“当前目标架构评审主线”；本地原型文档只用来核对现有代码行为，不能反向生成首发代码。

## 阶段 2 仓库治理入口

先读 [`REPOSITORY_STATUS.md`](REPOSITORY_STATUS.md) 和 [`CODEBASE_MAP.md`](CODEBASE_MAP.md)。当前正式拓扑为
`kokoro-app`（本地 `kokoro`）→ `kokoro-bff`（Chat/业务 BFF）→ `kokoro-agent`，以及
`kokoro-iam`、`kokoro-system`、`kokoro-model`、`kokoro-billing`、`kokoro-capability`、
`kokoro-storage`、`kokoro-scheduler` 七个独立业务仓。Root 只维护跨仓契约、文档、部署入口和验证工具。

`kokoro-session`、`kokoro-gateway`、`kokoro-platform`、旧 `kokoro-web` monorepo、独立 `kokoro-credit`
和旧 Site 占位目录均已退出当前拓扑；历史文件只作迁移考古。Credit 归 `kokoro-billing`，Chat 归
`kokoro-bff 的 Chat 内部业务边界`，不再创建独立仓。所有正式业务仓采用 PostgreSQL + Redis；对象字节使用
Storage 的 S3-compatible ObjectStore。

## 必读

1. [Codebase Map](CODEBASE_MAP.md)
2. [docs 总入口](README.md)
3. [Kokoro 总手册](kokoro-handbook/README.md)
4. [**子仓库架构与工程规范审计 v1**](repository-architecture-review-v1.md)
5. [**GA 核心架构总览：一个闭环底座，多个内置 Agent 产品**](kokoro-handbook/technical/42-ga-core-architecture.md)
6. [**Kokoro GA 整体 Agent 最终技术方案**](kokoro-handbook/technical/36-ga-final-agent-technical-plan.md)
7. [**Kokoro 统一入口、App 与 Agent 产品架构**](kokoro-handbook/technical/37-product-experience-agent-studio-architecture.md)
8. [**阶段 1 存储基线：PostgreSQL + Redis**](../contract/spec/storage-baseline-v1.md)
9. [**Web/BFF/Agent 三仓边界与 Chat v1**](../kokoro/docs/integration/chat-bff-contract-v1.md)
10. [**阶段 1 闭环验收证据**](reports/2026-09-01-phase1-closure.md)
11. [**Kokoro v1 与 Manus API 对齐基线**](MANUS_API_ALIGNMENT.md)
12. [**Kokoro 后端工程规范：模块、契约、DTO、Repository 与 SQL**](kokoro-handbook/technical/54-backend-engineering-standards.md)

## 当前目标架构评审主线

以下文档描述当前首发架构，优先于旧过程稿。实现尚未覆盖的部分必须在代码与交接中明确标注，
不能把方案文字误称为已上线行为。

### 架构评审核心四份

1. [**GA 核心架构总览**](kokoro-handbook/technical/42-ga-core-architecture.md)
2. [**Kokoro GA 整体 Agent 最终技术方案**](kokoro-handbook/technical/36-ga-final-agent-technical-plan.md)
3. [**阶段 1 存储基线：PostgreSQL + Redis**](../contract/spec/storage-baseline-v1.md)
4. [**Web/BFF/Agent 三仓边界与 Chat v1**](../kokoro/docs/integration/chat-bff-contract-v1.md)

评审“整个 Agent 怎么设计”时以以上四份为止；没有额外的独立 Session plan、binding 或 graph-version 设计需要拼读。下面的文档都是
**实施某个边界时的专项证据**，只能细化这两份方案，不能覆盖或再造一套整体架构。

### 按专题细化

| 主题 | 文档 |
|---|---|
| native runtime、首次启动与恢复 | [34 GA Runtime](kokoro-handbook/technical/34-ga-agent-runtime-architecture.md) |
| official Swarm / handoff | [35 GA × Swarm](kokoro-handbook/technical/35-ga-langgraph-swarm-architecture.md)、[ADR-020](kokoro-handbook/decisions/ADR-020-native-framework-compatibility-and-swarm-adapter.md) |
| bounded fan-out / map-reduce | [40 GA 工作画像](kokoro-handbook/technical/40-ga-work-profiles-and-bounded-fanout.md) |
| 质量、评测、上线 | [39 Evaluation](kokoro-handbook/technical/39-ga-evaluation-and-evidence-architecture.md)、[41 Outcome Contract](kokoro-handbook/technical/41-feature-outcome-contracts-and-quality-gates.md) |
| Harness / 产品能力装配 业界校准 | [44 GA Harness 与产品能力装配调研](kokoro-handbook/technical/44-ga-harness-and-workflow-research.md) |
| Feature warm、Factory 与未来可视化 Builder | [GA 核心架构](kokoro-handbook/technical/42-ga-core-architecture.md)、[GA 落地切片](kokoro-handbook/technical/43-ga-clean-build-slices.md) |
| native Agent state、fork、delete、memory | [ADR-018](kokoro-handbook/decisions/ADR-018-ga-thread-context-compaction-and-memory.md)、[Session 生命周期](kokoro-handbook/business-flows/session-lifecycle.md) |
| FeatureKey 与 tenant/App exposure | [ADR-021](kokoro-handbook/decisions/ADR-021-feature-key-global-catalog-identity.md)、[31 Tenant/System/Web](kokoro-handbook/technical/31-kokoro-tenant-system-architecture-v2.md) |
| 运行事件、reply owner、JobRef card | [ADR-016](kokoro-handbook/decisions/ADR-016-orchestration-policy-and-product-event-projection.md)、[Session/GA/Web 链路](kokoro-handbook/business-flows/agent-session-web-general-chat-runtime.md) |
| 当前本地原型目录/边界 | [Agent 设计卡](kokoro-handbook/technical/backend-design/09-agent.md)、[Agent 模块](kokoro-handbook/modules/kokoro-agent.md)、[BFF Chat 契约](../kokoro/docs/integration/chat-bff-contract-v1.md) |
| clean-build 实现切片 | [45 GA 原型就绪审计](kokoro-handbook/technical/45-ga-prototype-readiness-audit.md)、[43 GA clean-build 切片](kokoro-handbook/technical/43-ga-clean-build-slices.md)、[38 GA 公共运行契约](kokoro-handbook/technical/38-ga-public-runtime-contract.md) |
| Storage 与 Capability 当前原型参考 | [29 Storage target × Capability](kokoro-handbook/technical/29-capability-storage-runtime-architecture.md)、[Capability 设计卡](kokoro-handbook/technical/backend-design/05-capability.md) |
| Feature context 基础裁决 | [ADR-015](kokoro-handbook/decisions/ADR-015-agent-state-and-feature-context.md) |

以下仍为过程方案：

0. [kokoro-system、Tenant 隔离与 kokoro-web-user 技术方案](superpowers/specs/2026-08-22-kokoro-system-and-web-user-architecture.md)
0.1 [kokoro-system 与 kokoro-iam 改造实施计划 v2](superpowers/plans/2026-08-22-kokoro-system-iam-refactor-plan-v2.md)

1. [整体业务、Platform、Web、Session 与 Agent 产品目标架构 v1.5](superpowers/specs/2026-07-25-platform-web-session-target-architecture-design.md)
2. [Production Delivery Program](superpowers/plans/2026-07-25-kokoro-production-delivery-program.md)
3. [Wave 0 Repository/Toolchain/Contract Foundation v1.2](superpowers/specs/2026-07-25-wave-0-repository-contract-foundation-design.md)
4. [产品需求治理、Launch Profile 与 PRD Registry](superpowers/specs/2026-07-25-product-requirements-governance-and-prd-registry-design.md)
5. [Model Control、Model Gateway 与 LiteLLM 目标架构](superpowers/specs/2026-07-25-model-control-gateway-litellm-architecture-design.md)
6. [Platform/Web/Session P0 Contract Closure](superpowers/specs/2026-07-25-platform-web-session-p0-contract-closure-design.md)
7. [Platform Modular Core 与 Internal RPC](superpowers/specs/2026-07-25-platform-modular-core-internal-rpc-design.md)
8. [Execution Budget Allocation Protocol](superpowers/specs/2026-07-25-execution-budget-allocation-protocol-design.md)
9. [Asset、Artifact、Blob Ownership、Promotion 与 GC](superpowers/specs/2026-07-25-asset-artifact-ownership-promotion-gc-design.md)
11. [Session HTTP/SSE Production Transport](superpowers/specs/2026-07-25-session-http-sse-production-transport-design.md)
12. [Client Access Plane：CLI、Desktop 与 IDE](superpowers/specs/2026-07-25-client-access-plane-developer-client-design.md)
13. [Capability Control、Runtime、Connection 与 Effect](superpowers/specs/2026-07-25-capability-control-runtime-connection-effect-architecture-design.md)
14. [PRD-00 Launch Profile 与 Journey Contract](superpowers/specs/2026-07-25-prd-00-launch-profile-and-journey-contract.md)
15. [PRD-01 Site Identity 与 Account Security](superpowers/specs/2026-07-25-prd-01-site-identity-and-account-security.md)
16. [PRD-02 Workspace、Membership 与 Project](superpowers/specs/2026-07-25-prd-02-workspace-membership-and-project.md)
17. [PRD-03 Account、Plan、Redeem 与 Credit](superpowers/specs/2026-07-25-prd-03-account-plan-redeem-and-credit.md)
18. [PRD-04 Checkout、Subscription 与 Billing](superpowers/specs/2026-07-25-prd-04-checkout-subscription-and-billing.md)
19. [PRD-05 Chat Conversation、Run 与 Interaction](superpowers/specs/2026-07-25-prd-05-chat-conversation-run-and-interaction.md)
20. [PRD-06 Asset Intake 与 Attachment Safety](superpowers/specs/2026-07-25-prd-06-asset-intake-and-attachment-safety.md)
21. [PRD-07 Studio Common、Job 与 Cost UX](superpowers/specs/2026-07-25-prd-07-studio-common-job-and-cost-ux.md)
22. [PRD-08I Image Studio](superpowers/specs/2026-07-25-prd-08i-image-studio.md)
23. [PRD-08M Music Studio](superpowers/specs/2026-07-25-prd-08m-music-studio.md)
24. [PRD-08V Video Studio](superpowers/specs/2026-07-25-prd-08v-video-studio.md)
25. [PRD-09 Library、Artifact、Export 与 Share](superpowers/specs/2026-07-25-prd-09-library-artifact-export-and-share.md)
26. [PRD-10 Admin Operating Console](superpowers/specs/2026-07-25-prd-10-admin-operating-console.md)
27. [PRD-11 Support、Recovery 与 Appeals](superpowers/specs/2026-07-25-prd-11-support-recovery-and-appeals.md)
28. [PRD-12 Site Lifecycle 与 Fleet](superpowers/specs/2026-07-25-prd-12-site-lifecycle-and-fleet.md)
29. [PRD-13 Growth、SEO、Experiment 与 Attribution](superpowers/specs/2026-07-25-prd-13-growth-seo-experiment-and-attribution.md)
30. [PRD-14 Localization 与 Accessibility](superpowers/specs/2026-07-25-prd-14-localization-and-accessibility.md)
31. [PRD-15 Notification、Preferences 与 Data Rights](superpowers/specs/2026-07-25-prd-15-notification-preferences-and-data-rights.md)
32. [PRD-16 Trust、Content Safety 与 Media Rights](superpowers/specs/2026-07-25-prd-16-trust-content-safety-and-media-rights.md)
33. [PRD-17 Model Option、Control 与 Provider Operations](superpowers/specs/2026-07-25-prd-17-model-option-control-and-provider-operations.md)
34. [PRD-18 Capability Catalog、Connection、Consent 与 Runtime UX](superpowers/specs/2026-07-25-prd-18-capability-catalog-connection-consent-runtime-ux.md)
35. [PRD-A1 AgentRevision、Selection 与 Handoff](superpowers/specs/2026-07-25-prd-a1-agent-revision-and-handoff-product.md)
36. [PRD-A2 ExecutionTarget、Device、Permission 与 Interaction](superpowers/specs/2026-07-25-prd-a2-target-device-permission-and-interaction.md)
37. [PRD-A3 Developer Workspace、Context 与 Multi-device](superpowers/specs/2026-07-25-prd-a3-developer-workspace-context-and-multidevice.md)
38. [PRD-A4 Routine、Connector 与 TaskView](superpowers/specs/2026-07-25-prd-a4-routine-connector-and-taskview.md)
39. [PRD-A5 Agent Team、Wide Research 与 Application Runtime](superpowers/specs/2026-07-25-prd-a5-agent-team-research-and-application-runtime.md)
40. [PRD-A6 Client Access Plane：CLI、Desktop 与 IDE](superpowers/specs/2026-07-25-prd-a6-client-access-plane-cli-desktop-and-ide.md)
41. [全项目模块、能力与闭环覆盖审计](reports/2026-07-25-kokoro-module-capability-coverage-audit.md)
42. [Redeem-first Production Launch Checklist](reports/2026-07-25-kokoro-production-launch-readiness-checklist.md)
43. [全局设计完成度与实现授权审计](reports/2026-07-25-kokoro-design-completion-audit.md)

## 当前实施计划

1. [Wave 0 Repository、Toolchain、Contract 与 Documentation Foundation Implementation Plan](superpowers/plans/2026-07-26-wave-0-repository-contract-foundation-implementation-plan.md)

## Goal 2 当前基线（2026-09-02）

阶段 2 已完成一次可重复的真实本地闭环验收：10 个 active child repository 均有独立 GitHub
仓库，所有子仓 main 与 origin/main 对齐；Root 负责跨仓 v1 契约、拓扑/设计门禁、
部署入口、审计和 E2E 编排，不承载子仓业务实现。当前链路为：

    kokoro-app (Web)
      → same-origin /api/*
      → kokoro-bff (Chat + business BFF)
      → IAM/System/Model/Billing/Capability/Storage
      → kokoro-agent HTTP ingress
      → kokoro-scheduler internal command / occurrence replay

边界裁决：

- Chat 是 kokoro-bff 内部业务模块；Session 是 BFF 的 v1 API 概念，不存在独立
  kokoro-chat/kokoro-session 运行仓。
- Project 与 ScheduledTask 的用户业务事实归 BFF；Scheduler 只拥有通用 ScheduleJob、
  lease、retry、misfire、pause/resume 和 dispatch，不读 BFF/Billing 数据库。
- Credit 归 kokoro-billing；Model、IAM、System 均保持独立业务 owner。
- 正式业务仓统一 PostgreSQL + Redis；PostgreSQL 保存事实，Redis 只做 cache、stream、
  queue、lease、限流和协调；对象字节由 Storage 的 S3-compatible ObjectStore 管理。
- Web 不直连 Agent、IAM 或任何业务数据库。浏览器提供的 X-Domain、X-Forwarded-*
  和 Host 不作为租户身份来源；BFF 通过 KOKORO_DOMAIN 生成标准 Forwarded，
  通过 IAM 完成身份/权限 admission，再将受信 tenant_id 与 Host 交给 System；Site/Host binding 由 System 自己校验。

### Goal 2 已收口能力

1. Root machine-readable 契约：
   contract/goal2-cross-repository-contract-v1.json 是跨仓 wire authority，
   contract/goal2-repository-contract-manifest.json 是仓库注册表。HTTP 成功统一为
   {data, meta:{request_id}}；列表/事件游标放在资源 payload 的 data.next_cursor。错误统一为
   {error:{code,message}, meta:{request_id}}，外部 HTTP 字段使用 snake_case。
2. BFF live 适配：
   System runtime manifest、Model catalog、Billing catalog/checkout、
   Capability skill/MCP read projections、Storage library projection、Agent Chat
   launch/control/replay/detail 均有显式 adapter；Project/ScheduledTask 使用 BFF
   PostgreSQL/Redis business store，并将 ScheduleJob 注册、dispatch、幂等 receipt
   和 replay 接通。没有 owner ingress 的写操作显式 fail-closed，不回退成伪造成功。
3. Agent ingress：
   Agent 自仓维护 Run admission、Agent-owned PostgreSQL ledger、Redis stream、
   HTTP run/control/evidence/history/replay，BFF 不读 Agent 的数据库或 Redis。BFF
   mutation body 明确发送 Content-Length，避免 stdlib ingress 把 JSON 读取成空对象。
4. 调度事实边界：
   BFF 是 ScheduledTask 业务事实 owner，Scheduler 是执行 owner，目标业务/Agent
   保存 command receipt；同一 job_name + occurrence 使用同一 Idempotency-Key，
   replay 返回原始 receipt，不启动第二个 Agent run。
5. 子仓自洽：
   Web、BFF、Agent、IAM、System、Model、Billing、Capability、Storage、Scheduler
   各自维护源码、测试、API contract、Dockerfile、CI、runbook 和迁移；Root 不复制
   sibling source，不跨仓共享数据库表/ORM schema。

### 阶段 2 证据入口

- [跨仓 v1 契约](../contract/goal2-cross-repository-contract-v1.json)
- [仓库契约注册表](../contract/goal2-repository-contract-manifest.json)
- [仓库状态索引](REPOSITORY_STATUS.md)
- [CODEBASE_MAP](CODEBASE_MAP.md)
- [阶段 2 最终测试报告](reports/2026-09-02-stage2-final-test-report.md)
- [Owner health + live business JSON](reports/2026-09-01-stage2-owner-health.json)
- [阶段 2 仓库审计](reports/2026-09-01-stage2-repository-audit.md)
- [阶段 2 收口报告](reports/2026-09-01-stage2-repository-closure.md)

废弃仓库 kokoro-session、kokoro-gateway、kokoro-platform、旧 kokoro-web
均已移出本地工作区并在 GitHub archived；独立 kokoro-credit 与旧 Site 占位目录
没有正式远程仓，也不出现在当前 manifest、Compose、CI 或运行路径中。历史材料只用于
迁移考古，不是当前实现入口。

镜像发布约束保持不变：普通 push/PR 只运行质量检查；只有 v*.*.* tag 触发生产
GHCR workflow。Dockerfile 使用生产启动命令，本地开发直接使用各仓 dev 命令；
本轮未修改 GHCR package visibility。

## 本地原型与历史材料（仅参考，不进入首发）

- [本地原型技术方案](kokoro-handbook/technical/20-kokoro-v1-technical-plan.md)：当前物理行为参考，不是首发 GA 架构。
- [早期全局拆仓与 DDD 图](kokoro-handbook/technical/24-backend-subrepository-ddd-architecture.md)、
  [DDD 分级](kokoro-handbook/technical/25-backend-architecture-and-ddd-levels.md)、
  [仓库拓扑](kokoro-handbook/technical/26-backend-repository-and-directory-topology.md)、
  [旧“最终”后端图](kokoro-handbook/technical/27-final-backend-architecture.md) 与
  [ADR-012](kokoro-handbook/decisions/ADR-012-backend-subrepository-ddd-layers.md)：历史拆仓材料；其中 `kokoro-chat` 独立 owner 与 Capability snapshot 不作目标依据。
- [Platform × 主链闭环](kokoro-handbook/technical/21-platform-mainchain-closure.md)：历史 Platform 接线事实；计费/Run owner 服从 36/37/38。
- [Agent / Session / Web 本地原型运行时](kokoro-handbook/technical/11-agent-session-web-v1-runtime.md)、
  [V2 技术方案](kokoro-handbook/technical/15-v2-technical-plan.md)、
  [Capability/namespace/sandbox 旧附录](kokoro-handbook/technical/18-capability-namespace-auth-sandbox-artifacts.md)、
  [Skill Hub 旧产品手册](kokoro-handbook/product/06-skill-hub-and-mcp-hub.md)：均只作原型考古。
- [跨仓闭环与遗留对齐总设计](superpowers/specs/2026-07-11-cross-repo-closure-and-legacy-alignment-design.md)、
  [WP-0 交接](handoffs/2026-07-09-wp0-landing-and-next-review-handoff.md) 与旧派工单：过程记录，不作架构事实。

## 默认不读

这些目录是历史、过程、原型或研究材料。除非任务点名，否则不要让 agent 展开：

```text
product/
prototypes/
research/
brainstorm/
plans/
superpowers/plans/
```

需要考古时，先在 `docs/README.md` 判断目录性质，再打开具体文件。
