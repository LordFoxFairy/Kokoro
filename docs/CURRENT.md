# 当前活跃文档白名单

状态：2026-09-15
用途：降低 agent 阅读负担。做**目标 GA/Feature-first 架构**的 runtime、capability、deliver 主线时，只读
“当前目标架构评审主线”；本地原型文档只用来核对现有代码行为，不能反向生成首发代码。

## 2026-09-15 Root 当前路径与只读验证导航

当前九个正式运行仓中，仅 `kokoro-agent` 是 Root gitlink；Web 是 `Kokoro/kokoro/` 的独立
checkout，远端 `LordFoxFairy/kokoro-app`。`apps/` 尚未实施；目标九仓 Submodule 固定组合及
组合 CI 尚待独立切片验收。`scripts/verify-ten-repository-full.sh` 仍暂停，入口只报
`VERIFICATION_ENTRY_PAUSED`、退出 2，不触及基础设施；不能将静态治理 PASS 写成完整九仓验收。

2026-09-15 read-only snapshot（Task 1 前 Root commit `17c4fcbce5ddf5f77573fc5110dffb4cfd0a8799`）：
`python3 scripts/verify-repository-topology.py` 静态 PASS；
`python3 -m pytest scripts/tests -q` 为 82 PASS / 2 个既有手册断言 FAIL；
`python3 scripts/verify-ten-repository-standard.py --format json` 审计九仓、244 条既有违规。
这些数量是本轮比较基线，不是当前切片验收；不替代子仓真实 lint/test/build/schema/smoke，亦不覆盖
下文先前已验的 System owner commit 与隔离 HTTP smoke 证据。

## 当前 System 完整交付主线

用户明确要求完整 System，不以 Nest + Site CRUD 截止。唯一任务表在
[System IMPLEMENTATION_PLAN](../kokoro-system/docs/IMPLEMENTATION_PLAN.md)，设计决定为
[ADR-031](kokoro-handbook/decisions/ADR-031-system-http-nestjs-convergence.md)。
**完整业务源码、跨仓 HTTP、NestJS 工程边界与tag镜像发布已验收**，不是 Nest + Site CRUD 切片。五模块 Sites、Workspaces、Products、Runtime Manifests、Model Catalog，83业务operation+2probes；旧四层/RPC/Proto/generated/SDK退出。

| Owner / 当前交付 commit | Root 实际验证（2026-09-08） |
| --- | --- |
| System `f3b5a186da37cb879c1d91defd9e264a2006fa5e`（镜像tag `v0.1.2`→`7252d50`） | 本地 `pnpm verify`：99pass/0skip、fresh23/22；GitHub release/CI runs `34222465469`/`34222465488` success |
| BFF `26eec0112c83ea98aa045896d385c89ad88b45d2`（consumer `1e03b87`） | Node22 `pnpm lint && pnpm typecheck && pnpm build && pnpm test`：152 pass / 0 fail / 0 skip |
| Agent `e24b4aab05ee6df811c21089effbe1f91d7c2f2c` | `uv lock --check`、`uv run ruff check .`、`uv run pyright`通过（0error/0warning）；`uv run pytest -q`：611pass / 6既有skip / 77集成等标记deselected / 66第三方warnings |

Root 在上述 System committed HEAD 实跑：

```bash
python3 scripts/e2e/run_system_owner_smoke.py \
  --postgres postgresql://nako@localhost/postgres --redis redis://localhost:6379/2 \
  --node24-bin /Users/nako/.nvm/versions/node/v24.13.0/bin \
  --node22-bin /Users/nako/.nvm/versions/node/v22.22.2/bin
```

结果 PASS：真实 System/BFF `pnpm dev`，HTTP建资源/发布配置/绑定覆盖，BFF manifest/catalog/default与跨tenant隔离，BFF调用Agent-only resolve被403拒绝，Agent真实HTTP默认/显式解析与model factory映射、跨tenant拒绝。全部自建PG数据库、Redis前缀、进程组清理后才PASS；不包含provider推理、完整Agent worker执行或镜像实跑。
R6 committed HEAD smoke仍为PASS，日志 `/tmp/r6-root-verify-committed.log`、`/tmp/r6-root-smoke-committed.log`。System与Agent clean；BFF仍有任务外 `docs/api/v1/agui-chat.md` / `test/lifecycle.test.ts` dirty，本轮未改未提交，smoke输出显式记录dirty。

R6把规范从“文档约定”落成可执行门禁：ESLint使用`recommendedTypeChecked`+`projectService`并启用Promise/unsafe/exhaustive规则；Repository不再依赖HTTP错误或分页类型；SystemError保持中性，HTTP状态在transport穷尽映射；四个feature使用显式public入口与最小Nest exports；Controller禁止直连database/cache，HealthService承接readiness；禁止跨feature deep import、循环、forwardRef/ModuleRef及手工实例化Service/Repository。OpenAPI字节、canonical SQL、package/lock、83+2路由契约均未改变。

Root `python3 scripts/verify-repository-topology.py` 与 `python3 scripts/verify-backend-design.py --manifest-only`通过；活动运行仓9个，旧Model退出active/clone/consumer配置，但checkout/remote/历史保留、不归档、不删旧数据。Capability→Platform另属其他任务。
Root focused governance/topology/smoke **81pass**；先前全 `python3 -m pytest scripts/tests -q` **82pass / 2既有手册测试失败**（例子数18/11与旧标题断言，已在原基线复现）。本轮 `python3 scripts/verify-ten-repository-standard.py --format json` 当前System **0违规**，其他8仓合计208条未收敛，不记作九仓全绿。未触及Root SQL手册、Agent gitlink或其他任务变更。

System `v0.1.2` 已由tag触发GitHub Actions完成镜像build、真实image smoke、HIGH/CRITICAL Trivy、CycloneDX SBOM及GHCR推广；`0.1.2`/`0.1`/`latest`统一digest `sha256:8fe6e701451f461b02b84c6520d76f49ad872c8f11d6ae3a8c5b80532797eb37`。user-owned private repository不支持GitHub attestation，相关步骤按可见性明确skip，不冒称已签。生产容量/SLO/灾备/secret轮换及provider推理仍由部署环境另验。
旧 Root full/owner-health runner 已暂停（退出2、无基础设施操作），危险共享清理实现已删除；隔离全九仓编排重建由Root后续承担，不混入本轮System完成声明。

## 当前工程规范入口

目录、命名、语言、SQL 与 Agent 执行规则先读 [AGENTS](../AGENTS.md) 及其引用的三份手册。
下方业务目标文档只说明能力语义，不覆盖新工程基线。旧版 54/55 已撤销为导航页；当前物理实现尚待逐仓对齐。

本轮规范验证与逐仓待办见 [工程手册验证记录](reports/2026-09-04-engineering-handbook-verification.md)。

2026-09-07 用户已批准 Capability 的 NestJS + Prisma 收敛，见 [Capability 任务板](superpowers/plans/2026-09-07-capability-nestjs-prisma.md)。IAM 等仓由各自负责人继续推进；本任务不接管其修改，跨仓 contract 按 owner 顺序交接。

以下为 IAM 原有阶段导航，最新状态仍以 IAM 自仓 CURRENT/ACCEPTANCE 与任务板为准，不再作为其他子仓的全局阻断条件。
当前为 R5 规范与 IAM 设计收敛：TS 手册已改为成熟框架/class 优先目标，IAM 先更新技术/API/数据与 ADR；
本轮不修改业务源码、机器契约或 Schema，不把文档交付当作框架切换或生产验收。
当前代码、已验范围与剩余缺口只看 [IAM CURRENT](../kokoro-iam/docs/CURRENT.md) 和 [IAM ACCEPTANCE](../kokoro-iam/docs/ACCEPTANCE.md)，
本导航不再复制各阶段commit/测试数量；派工、模型、写入授权及最新续接点以 [IAM任务板](superpowers/plans/2026-09-04-iam-engineering-alignment.md) 为准。
技术方案由主控评估，不重复要求用户选择内部目录或已确定规则；完整环境/消费者证据缺失时仍明确保留。

## 阶段 2 仓库治理入口

先读 [`REPOSITORY_STATUS.md`](REPOSITORY_STATUS.md) 和 [`CODEBASE_MAP.md`](CODEBASE_MAP.md)。当前正式拓扑为
`kokoro-app`（本地 `kokoro`）→ `kokoro-bff`（Chat/业务 BFF）→ `kokoro-agent`，以及
`kokoro-iam`、`kokoro-system`（含 model-catalog）、`kokoro-billing`、`kokoro-capability`、
`kokoro-storage`、`kokoro-scheduler` 六个独立业务仓。Root 只维护架构文档、部署入口和拓扑/验证工具；各仓自持本仓 API contract。

2026-09-04 已接受的目标拓扑见
[ADR-029](kokoro-handbook/decisions/ADR-029-system-model-and-platform-boundaries.md)：`kokoro-model` 合入
`kokoro-system/model-catalog`，`kokoro-capability` clean-slate 重命名为 `kokoro-platform`，首批一级域为
Skills/MCP。System 完整源码与消费者 HTTP 已验证；旧 Model checkout/remote 保留但不列为活动服务。Capability→Platform 仍是另一个 cutover，未在本轮实施。

`kokoro-session`、`kokoro-gateway`、旧 `kokoro-platform` 实现、旧 `kokoro-web` monorepo、独立 `kokoro-credit`
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
8. [**阶段 1 存储基线：PostgreSQL + Redis**](../kokoro-agent/docs/agent/api-contract.md)
9. [**Web/BFF/Agent 三仓边界与 Chat v1**](../kokoro/docs/integration/chat-bff-contract-v1.md)
10. [**阶段 1 闭环验收证据**](reports/2026-09-01-phase1-closure.md)
11. [**Kokoro v1 与 Manus API 对齐基线**](MANUS_API_ALIGNMENT.md)
12. [**PostgreSQL 与 SQL 工程规范**](kokoro-handbook/standards/03-sql-and-postgresql.md)
13. [**TypeScript 后端成熟工程规范**](kokoro-handbook/standards/08-typescript-backend-engineering.md)
14. [**Python 后端成熟工程规范**](kokoro-handbook/standards/09-python-backend-engineering.md)
15. [**Kokoro 总体架构规范 v1**](ARCHITECTURE_STANDARD.md)

## 当前目标架构评审主线

以下文档描述当前首发架构，优先于旧过程稿。实现尚未覆盖的部分必须在代码与交接中明确标注，
不能把方案文字误称为已上线行为。

### 架构评审核心四份

1. [**GA 核心架构总览**](kokoro-handbook/technical/42-ga-core-architecture.md)
2. [**Kokoro GA 整体 Agent 最终技术方案**](kokoro-handbook/technical/36-ga-final-agent-technical-plan.md)
3. [**阶段 1 存储基线：PostgreSQL + Redis**](../kokoro-agent/docs/agent/api-contract.md)
4. [**Web/BFF/Agent 三仓边界与 Chat v1**](../kokoro/docs/integration/chat-bff-contract-v1.md)

评审“整个 Agent 怎么设计”时以以上四份为止；没有额外的独立 Session plan、binding 或 graph-version 设计需要拼读。下面的文档都是
**实施某个边界时的专项证据**，只能细化这两份方案，不能覆盖或再造一套整体架构。

### 按专题细化

| 主题                                       | 文档                                                                                                                                                                                                                                                  |
| ------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| native runtime、首次启动与恢复             | [34 GA Runtime](kokoro-handbook/technical/34-ga-agent-runtime-architecture.md)                                                                                                                                                                        |
| official Swarm / handoff                   | [35 GA × Swarm](kokoro-handbook/technical/35-ga-langgraph-swarm-architecture.md)、[ADR-020](kokoro-handbook/decisions/ADR-020-native-framework-compatibility-and-swarm-adapter.md)                                                                    |
| bounded fan-out / map-reduce               | [40 GA 工作画像](kokoro-handbook/technical/40-ga-work-profiles-and-bounded-fanout.md)                                                                                                                                                                 |
| 质量、评测、上线                           | [39 Evaluation](kokoro-handbook/technical/39-ga-evaluation-and-evidence-architecture.md)、[41 Outcome Contract](kokoro-handbook/technical/41-feature-outcome-contracts-and-quality-gates.md)                                                          |
| Harness / 产品能力装配 业界校准            | [44 GA Harness 与产品能力装配调研](kokoro-handbook/technical/44-ga-harness-and-workflow-research.md)                                                                                                                                                  |
| Feature warm、Factory 与未来可视化 Builder | [GA 核心架构](kokoro-handbook/technical/42-ga-core-architecture.md)、[GA 落地切片](kokoro-handbook/technical/43-ga-clean-build-slices.md)                                                                                                             |
| native Agent state、fork、delete、memory   | [ADR-018](kokoro-handbook/decisions/ADR-018-ga-thread-context-compaction-and-memory.md)、[Session 生命周期](kokoro-handbook/business-flows/session-lifecycle.md)                                                                                      |
| FeatureKey 与 tenant/App exposure          | [ADR-021](kokoro-handbook/decisions/ADR-021-feature-key-global-catalog-identity.md)、[31 Tenant/System/Web](kokoro-handbook/technical/31-kokoro-tenant-system-architecture-v2.md)                                                                     |
| 运行事件、reply owner、JobRef card         | [ADR-016](kokoro-handbook/decisions/ADR-016-orchestration-policy-and-product-event-projection.md)、[Session/GA/Web 链路](kokoro-handbook/business-flows/agent-session-web-general-chat-runtime.md)                                                    |
| 当前本地原型目录/边界                      | [Agent 设计卡](kokoro-handbook/technical/backend-design/09-agent.md)、[Agent 模块](kokoro-handbook/modules/kokoro-agent.md)、[BFF Chat 契约](../kokoro/docs/integration/chat-bff-contract-v1.md)                                                      |
| clean-build 实现切片                       | [45 GA 原型就绪审计](kokoro-handbook/technical/45-ga-prototype-readiness-audit.md)、[43 GA clean-build 切片](kokoro-handbook/technical/43-ga-clean-build-slices.md)、[38 GA 公共运行契约](kokoro-handbook/technical/38-ga-public-runtime-contract.md) |
| Storage 与 Capability 当前原型参考         | [29 Storage target × Capability](kokoro-handbook/technical/29-capability-storage-runtime-architecture.md)、[Capability 设计卡](kokoro-handbook/technical/backend-design/05-capability.md)                                                             |
| Feature context 基础裁决                   | [ADR-015](kokoro-handbook/decisions/ADR-015-agent-state-and-feature-context.md)                                                                                                                                                                       |

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
10. [Session HTTP/SSE Production Transport](superpowers/specs/2026-07-25-session-http-sse-production-transport-design.md)
11. [Client Access Plane：CLI、Desktop 与 IDE](superpowers/specs/2026-07-25-client-access-plane-developer-client-design.md)
12. [Capability Control、Runtime、Connection 与 Effect](superpowers/specs/2026-07-25-capability-control-runtime-connection-effect-architecture-design.md)
13. [PRD-00 Launch Profile 与 Journey Contract](superpowers/specs/2026-07-25-prd-00-launch-profile-and-journey-contract.md)
14. [PRD-01 Site Identity 与 Account Security](superpowers/specs/2026-07-25-prd-01-site-identity-and-account-security.md)
15. [PRD-02 Workspace、Membership 与 Project](superpowers/specs/2026-07-25-prd-02-workspace-membership-and-project.md)
16. [PRD-03 Account、Plan、Redeem 与 Credit](superpowers/specs/2026-07-25-prd-03-account-plan-redeem-and-credit.md)
17. [PRD-04 Checkout、Subscription 与 Billing](superpowers/specs/2026-07-25-prd-04-checkout-subscription-and-billing.md)
18. [PRD-05 Chat Conversation、Run 与 Interaction](superpowers/specs/2026-07-25-prd-05-chat-conversation-run-and-interaction.md)
19. [PRD-06 Asset Intake 与 Attachment Safety](superpowers/specs/2026-07-25-prd-06-asset-intake-and-attachment-safety.md)
20. [PRD-07 Studio Common、Job 与 Cost UX](superpowers/specs/2026-07-25-prd-07-studio-common-job-and-cost-ux.md)
21. [PRD-08I Image Studio](superpowers/specs/2026-07-25-prd-08i-image-studio.md)
22. [PRD-08M Music Studio](superpowers/specs/2026-07-25-prd-08m-music-studio.md)
23. [PRD-08V Video Studio](superpowers/specs/2026-07-25-prd-08v-video-studio.md)
24. [PRD-09 Library、Artifact、Export 与 Share](superpowers/specs/2026-07-25-prd-09-library-artifact-export-and-share.md)
25. [PRD-10 Admin Operating Console](superpowers/specs/2026-07-25-prd-10-admin-operating-console.md)
26. [PRD-11 Support、Recovery 与 Appeals](superpowers/specs/2026-07-25-prd-11-support-recovery-and-appeals.md)
27. [PRD-12 Site Lifecycle 与 Fleet](superpowers/specs/2026-07-25-prd-12-site-lifecycle-and-fleet.md)
28. [PRD-13 Growth、SEO、Experiment 与 Attribution](superpowers/specs/2026-07-25-prd-13-growth-seo-experiment-and-attribution.md)
29. [PRD-14 Localization 与 Accessibility](superpowers/specs/2026-07-25-prd-14-localization-and-accessibility.md)
30. [PRD-15 Notification、Preferences 与 Data Rights](superpowers/specs/2026-07-25-prd-15-notification-preferences-and-data-rights.md)
31. [PRD-16 Trust、Content Safety 与 Media Rights](superpowers/specs/2026-07-25-prd-16-trust-content-safety-and-media-rights.md)
32. [PRD-17 Model Option、Control 与 Provider Operations](superpowers/specs/2026-07-25-prd-17-model-option-control-and-provider-operations.md)
33. [PRD-18 Capability Catalog、Connection、Consent 与 Runtime UX](superpowers/specs/2026-07-25-prd-18-capability-catalog-connection-consent-runtime-ux.md)
34. [PRD-A1 AgentRevision、Selection 与 Handoff](superpowers/specs/2026-07-25-prd-a1-agent-revision-and-handoff-product.md)
35. [PRD-A2 ExecutionTarget、Device、Permission 与 Interaction](superpowers/specs/2026-07-25-prd-a2-target-device-permission-and-interaction.md)
36. [PRD-A3 Developer Workspace、Context 与 Multi-device](superpowers/specs/2026-07-25-prd-a3-developer-workspace-context-and-multidevice.md)
37. [PRD-A4 Routine、Connector 与 TaskView](superpowers/specs/2026-07-25-prd-a4-routine-connector-and-taskview.md)
38. [PRD-A5 Agent Team、Wide Research 与 Application Runtime](superpowers/specs/2026-07-25-prd-a5-agent-team-research-and-application-runtime.md)
39. [PRD-A6 Client Access Plane：CLI、Desktop 与 IDE](superpowers/specs/2026-07-25-prd-a6-client-access-plane-cli-desktop-and-ide.md)
40. [全项目模块、能力与闭环覆盖审计](reports/2026-07-25-kokoro-module-capability-coverage-audit.md)
41. [Redeem-first Production Launch Checklist](reports/2026-07-25-kokoro-production-launch-readiness-checklist.md)
42. [全局设计完成度与实现授权审计](reports/2026-07-25-kokoro-design-completion-audit.md)

## 当前实施计划

1. [Kokoro 十仓生产级工程闭环总实施计划](superpowers/plans/2026-09-03-kokoro-production-closure.md)
2. [Wave 0：十仓治理与文档基线实施计划](superpowers/plans/2026-09-03-governance-documentation-baseline.md)
3. [十仓生产级重构缺口基线](reports/2026-09-03-ten-repository-gap-baseline.md)
4. [历史 Wave 0 Repository、Toolchain、Contract 与 Documentation Foundation Implementation Plan](superpowers/plans/2026-07-26-wave-0-repository-contract-foundation-implementation-plan.md)

## Goal 2 当前基线（2026-09-02）

阶段 2 曾完成一次可重复的真实本地闭环验收；2026-09-02 全局 owner 修正后，该 evidence 需要重新跑一次：10 个 active child repository 均有独立 GitHub
仓库，所有子仓 main 与 origin/main 对齐；各 owner 仓负责本仓 v1 契约；Root 只负责拓扑/设计门禁、
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
- Web 不直连 Agent、IAM 或任何业务数据库。浏览器提供的 X-Domain、X-Forwarded-\*
  和 Host 不作为租户身份来源；BFF 通过 KOKORO_DOMAIN 生成标准 Forwarded，
  通过 IAM 完成身份/权限 admission，再将受信 tenant_id 与 Host 交给 System；Site/Host binding 由 System 自己校验。

当前闭环校正项已完成：IAM 不承担 Host lookup 与 Site binding；BFF live System projection 使用服务端
`KOKORO_TENANT_ID` + `KOKORO_DOMAIN`，System 在自己的 Site/Host 数据中完成校验。真实 E2E 需使用这两个配置验证，不能再配置
废弃的 IAM Host lookup。

### Goal 2 已收口能力

1. 本仓契约：
   各 owner 仓库分别维护自己的 v1 API/Schema/事件文档；HTTP 成功统一为
   {data, meta:{request_id}}，错误统一为 {error:{code,message}, meta:{request_id}}。具体字段由事实 owner 仓库定义，Root 不生成镜像。
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
   各自维护源码、测试、API contract、Dockerfile、CI、runbook 和唯一 canonical schema；Root 不复制
   sibling source，不跨仓共享数据库表/ORM schema。

### 阶段 2 证据入口

- [仓库状态索引](REPOSITORY_STATUS.md)
- [仓库地图](CODEBASE_MAP.md)
- [阶段 2 最终测试报告](reports/2026-09-02-stage2-final-test-report.md)
- [Owner health + live business JSON](reports/2026-09-01-stage2-owner-health.json)
- [阶段 2 仓库审计](reports/2026-09-01-stage2-repository-audit.md)
- [阶段 2 收口报告](reports/2026-09-01-stage2-repository-closure.md)

废弃仓库 kokoro-session、kokoro-gateway、kokoro-platform、旧 kokoro-web
均已移出本地工作区并在 GitHub archived；独立 kokoro-credit 与旧 Site 占位目录
没有正式远程仓，也不出现在当前 manifest、Compose、CI 或运行路径中。历史材料只用于
迁移考古，不是当前实现入口。

镜像发布约束保持不变：普通 push/PR 只运行质量检查；只有 v\*._._ tag 触发生产
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
