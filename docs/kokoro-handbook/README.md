# Kokoro 总手册

本目录是 Kokoro 的长期权威手册，放正式的产品形态、跨仓架构、模块边界、
业务链路、技术方案、运营规范和关键 ADR。

它不是过程方案池，也不是派工单目录。正在打磨、尚未成为正式版的跨仓方案放在
`docs/superpowers/specs/`；正式技术方案放回本目录的 `technical/` 或 `product/`；
执行计划放在 `docs/superpowers/plans/`；短期交接放在 `docs/handoffs/`。

子仓 README 说明当前实现，子仓 docs 说明局部实现细节；本手册负责把全局总设计统一起来。
子仓 docs 只能补实现细节，不能替代本手册。

## 实现状态

诚实区分本地原型与首发架构，避免把未上线的写成已上线：

```text
当前阶段 1 运行闭环：
  kokoro（Web）/ kokoro-bff（Chat 与业务 BFF）/ kokoro-agent（Run worker、HITL、恢复）。
  持久化基线为 PostgreSQL + Redis。

阶段 2 正式业务仓：
  kokoro-iam / kokoro-system / kokoro-model / kokoro-billing /
  kokoro-capability / kokoro-storage / kokoro-scheduler。

历史本地原型（未上线，已移出 Root）：
  kokoro-web / kokoro-session / kokoro-platform / kokoro-gateway / kokoro-credit 及其旧部署、验证入口。

首发架构（clean build）：
  现有原型没有生产 Session、Run、checkpoint、Artifact 或账务事实需要保留。GA、Session、Capability、Storage 与 Billing
  以 handbook 的目标契约直接实现；原型代码只作实现参考，不形成兼容读写、双轨运行或数据搬运。
```

### 阶段 2 归属速查

| 业务面 | 当前 owner | 边界结论 |
|---|---|---|
| Web | `LordFoxFairy/kokoro-app` | 独立 Web 子仓；只暴露同源 `/api/*` adapter，不直连业务仓 |
| Chat / 业务编排 | `LordFoxFairy/kokoro-bff` | BFF 的 Chat 业务模块边界是 Chat 唯一业务入口；Session 是资源概念，不是独立仓库 |
| 执行 | `LordFoxFairy/kokoro-agent` | Worker、HITL、恢复和执行事件；由 BFF 通过内部契约承接 |
| 身份与权限 | `kokoro-iam` | Tenant、User、Auth、AuthZ、Role、Permission、Audit |
| 系统与模型 | `kokoro-system` / `kokoro-model` | Site/Workspace/Runtime 配置与 Model Catalog/Provider 分开归属 |
| 商业计费 | `kokoro-billing` | Payment、Subscription、Checkout、Refund、Credit、Ledger 同仓；不再单列 `kokoro-credit` |
| 能力与对象 | `kokoro-capability` / `kokoro-storage` | Skill/MCP 控制面与 Asset/ObjectStore 元数据分开；对象字节不进入 Web/BFF |
| 调度 | `kokoro-scheduler` | 独立 Go 调度 owner；通用任务、lease、retry，不承载 Billing 业务规则 |

`kokoro-gateway`、`kokoro-session`、`kokoro-platform`、旧 `kokoro-web` 与 `kokoro-credit` 均为历史/归档名称。它们可以被检索用于考古，但不得作为当前仓库、环境变量、部署服务或依赖入口。当前跨仓 wire 以 [`../../contract/goal2-repository-contract-manifest.json`](../../contract/goal2-repository-contract-manifest.json) 与各仓 `/v1` 契约为准。

## 当前 Feature-first / GA 目标架构（2026-08-22）

当前 Agent/Capability 的唯一评审主线是：

- [GA 核心架构总览](technical/42-ga-core-architecture.md)（先读：对象、owner 与一条运行主链）
- [GA 整体 Agent 最终技术方案](technical/36-ga-final-agent-technical-plan.md)
- [统一入口、App、Feature 与 Agent 产品架构](technical/37-product-experience-agent-studio-architecture.md)
- [GA 公共运行契约](technical/38-ga-public-runtime-contract.md)
- [GA 评测与运行证据](technical/39-ga-evaluation-and-evidence-architecture.md)
- [GA 工作画像与有界并行任务](technical/40-ga-work-profiles-and-bounded-fanout.md)
- [Feature 结果契约与质量门](technical/41-feature-outcome-contracts-and-quality-gates.md)
- [GA Harness 与 Agent 组装校准](technical/44-ga-harness-and-workflow-research.md)
- [GA 原型就绪审计](technical/45-ga-prototype-readiness-audit.md)
- [跨子仓 API/AIP 契约与技术方案同步](technical/51-cross-repository-contract-sync.md)
- [Capability × Storage v1 API 与 Client 契约](technical/52-capability-storage-v1-api-and-client-contract.md)
- [GA Runtime](technical/34-ga-agent-runtime-architecture.md)、[GA-first SkillRuntime](technical/33-ga-first-skill-runtime-architecture.md)、[GA × official Swarm](technical/35-ga-langgraph-swarm-architecture.md)
- [产品 Session 生命周期](business-flows/session-lifecycle.md) 与 [Session/GA/Web 运行链路](business-flows/agent-session-web-general-chat-runtime.md)
- [后端目标仓库设计卡](technical/backend-design/README.md)

核心 owner 固定为：`kokoro-bff 的 Chat 内部业务边界` 拥有 Web-facing session/message/SSE/control 适配；上游 IAM 只向 GA
提交服务端构造的 `ExecutionIdentity(tenant_ref, actor, subject, identity_assertion_ref)`，GA ingress 从 tenant + subject 派生内部 `RuntimeNamespace`；GA 使用
DeepAgents/LangGraph 原生 state、官方 `SwarmState`、checkpoint、RunLedger、workbench、HITL execution 与 `chat_events`；Capability 只拥有
user/session Skill path、visibility、CRUD；Storage 拥有 bytes/scan/Asset/Artifact。当前不使用独立 `kokoro-chat` runtime、
Capability runtime snapshot 或 Agent/Skill 版本/Session binding 机制。

Billing 当前唯一业务与技术权威是 [Billing 商业系统重构版最终架构](technical/50-billing-commerce-rearchitecture.md)；
正式业务仓统一遵守 PostgreSQL + Redis，旧 MySQL/Mongo SQL 与迁移资料只保留为历史审阅记录。
新 API 必须按当前 Root contract 和 owner 的 canonical v1 contract 重新生成，不创建第二份 Billing OpenAPI。

## 当前阶段 1 链路

```text
kokoro Web -> kokoro-bff 的 Chat 内部业务边界 -> kokoro-agent
                 PostgreSQL durable facts + Redis transport
```

```text
kokoro          只做 Web UI 与同源 /api/* route adapter。
kokoro-bff      负责 Chat/业务编排、鉴权、幂等、错误归一、SSE 与 owner adapter。
kokoro-agent    负责 Run 执行、HITL、恢复与 worker；PostgreSQL 保存 durable facts，Redis 只作 transport/lease/cache。
Goal 2 owners   各自维护 PostgreSQL schema、Redis adapter、API、迁移、测试、Docker 与 CI。
```

## 强制约束

```text
1. 文档必须中文。
2. 主仓 docs/kokoro-handbook 是总入口。
3. 子仓 docs 只能补实现细节，不能替代主仓手册。
4. tenant_id 是身份、权限和业务数据隔离键；site/site_key 只承载产品、品牌和域名语义；`RuntimeNamespace` 是 GA/runtime 唯一的内部隔离键。
5. 同邮箱跨 Tenant 默认不同用户。
6. 不新增 kokoro-contracts。
7. 当前本地原型不使用 ports 目录；首发 DDD 子仓允许明确的 Application ports，以 24 为准。
8. 阶段 1 与阶段 2 正式仓的持久化基线为 PostgreSQL + Redis；Root 不新增 MySQL/Mongo 运行时。
9. Storage 对象字节使用 S3-compatible ObjectStore，PostgreSQL 保存元数据与生命周期事实。
10. Redis 只做 live stream、短期队列、广播、限流辅助和幂等快速路径，不作业务幂等最终真源。
11. Redis 不是长期事实源；跨仓 owner 通过 API/contract 交互，不共享数据库 schema。
12. agent 不能直接扣积分（只能 credit.quote/hold/commit/release）。
13. payment 不能直接写 credit ledger。
14. model 不能决定最终价格。
15. web/bff 不能绕过服务端 deployment binding、身份与 owner scope。
16. 浏览器只消费 kokoro-bff 的同源 SSE。
17. kokoro-agent 不直接面向浏览器。
18. kokoro-bff 不直接读取 Agent 数据库；Agent 只通过服务 contract/transport 交互。
19. GA Root caller 只提交服务端构造的 `ExecutionIdentity(tenant_ref, actor, subject, identity_assertion_ref)`；不得新增 caller `namespace` / `thread_id`，也不得用 userId / ownerId / workspaceId 作为隔离辅助字段。
20. GA ingress 以受控 canonical `tenant_ref + subject` 和 key material 派生 opaque `RuntimeNamespace`；不拼 user:/team: 等业务前缀、不反向暴露，也不让上游选择该值；扣积分仍使用 subject + Billing binding，不从 namespace 反查账户。
```

## 目录

### 产品 product/

- [00-product-shape](product/00-product-shape.md)
- [01-general-chat](product/01-general-chat.md)
- [02-studio-products](product/02-studio-products.md)
- [03-music-studio](product/03-music-studio.md)
- [04-video-image-code](product/04-video-image-code.md)
- [05-teams-workspaces-projects](product/05-teams-workspaces-projects.md)
- [06-skill-hub-and-mcp-hub](product/06-skill-hub-and-mcp-hub.md)
- [07-pricing-credit-plans](product/07-pricing-credit-plans.md)
- [08-multi-site-seo-growth](product/08-multi-site-seo-growth.md)

### 技术 technical/

- [00-system-overview](technical/00-system-overview.md)
- [01-repository-map](technical/01-repository-map.md)
- [02-platform-architecture](technical/02-platform-architecture.md)
- [03-agent-architecture](technical/03-agent-architecture.md)
- [04-session-architecture](technical/04-session-architecture.md)
- [05-web-architecture](technical/05-web-architecture.md)
- [06-data-storage](technical/06-data-storage.md)
- [07-service-communication](technical/07-service-communication.md)
- [08-deployment](technical/08-deployment.md)（历史本地原型 deployment；当前 deployment plane 见 operations/docker-and-k8s）
- [09-security-permissions](technical/09-security-permissions.md)
- [10-observability](technical/10-observability.md)
- [11-agent-session-web-v1-runtime](technical/11-agent-session-web-v1-runtime.md)
- [12-agent-hitl-tool-interception](technical/12-agent-hitl-tool-interception.md)
- [13-agent-docs-map](technical/13-agent-docs-map.md)
- [14-web-i18n-capability](technical/14-web-i18n-capability.md)
- [15-v2-technical-plan](technical/15-v2-technical-plan.md)
- [16-session-deletion-cascade](technical/16-session-deletion-cascade.md)（历史本地原型软删规格；首发 delete 见 ADR-018/38）
- [17-namespace-runtime-isolation](technical/17-namespace-runtime-isolation.md)（本地原型 namespace 物理参考；首发 ingress 规则以 38/ADR-022 为准）
- [18-capability-namespace-auth-sandbox-artifacts](technical/18-capability-namespace-auth-sandbox-artifacts.md)
- [19-current-runtime-capability-review-plan](technical/19-current-runtime-capability-review-plan.md)（已被 20 取代，保留为扩展附录）
- [20-kokoro-v1-technical-plan](technical/20-kokoro-v1-technical-plan.md)（**本地原型物理参考 / 不进入首发**）
- [21-platform-mainchain-closure](technical/21-platform-mainchain-closure.md)（**历史 Platform 接线记录**；当前 owner 见阶段 2 归属速查与 36/37/38）
- [22-capability-hub](technical/22-capability-hub.md)（**历史 Hub 边界记录**；当前 Skill/MCP owner 为 `kokoro-capability`，跨仓入口为 BFF v1）
- [23-platform-ops-console](technical/23-platform-ops-console.md)（运营台现状：三维 RBAC / maker-checker / DB 审计 / manifest 代理 / internal-secret 现状）
- [24-backend-subrepository-ddd-architecture](technical/24-backend-subrepository-ddd-architecture.md)（历史全局拆仓材料）
- [25-backend-architecture-and-ddd-levels](technical/25-backend-architecture-and-ddd-levels.md)（历史 DDD 分级材料）
- [26-backend-repository-and-directory-topology](technical/26-backend-repository-and-directory-topology.md)（历史仓库拓扑）
- [27-final-backend-architecture](technical/27-final-backend-architecture.md)（**历史全局拆仓总图**；当前 owner 以阶段 2 归属速查、36/38 和设计卡为准）
- [29-capability-storage-runtime-architecture](technical/29-capability-storage-runtime-architecture.md)（**Storage target owner；Capability snapshot/revision/agent_namespace 仅本地原型参考**）
- [46-capability-mcp-connector-skill-design](technical/46-capability-mcp-connector-skill-design.md)（**Capability v1：Manus 风格 Skill、Connector、MCP 分层与 API 规划**）
- [33-ga-first-skill-runtime-architecture](technical/33-ga-first-skill-runtime-architecture.md)（**GA default Skill、find_skills/load_skill、CA path 与恢复**）
- [34-ga-agent-runtime-architecture](technical/34-ga-agent-runtime-architecture.md)（**GA 总体控制面、运行时与能力架构**）
- [35-ga-langgraph-swarm-architecture](technical/35-ga-langgraph-swarm-architecture.md)（**GA × official LangGraph Swarm 编排架构**）
- [36-ga-final-agent-technical-plan](technical/36-ga-final-agent-technical-plan.md)（**GA 整体 Agent 最终技术方案 / 单一评审入口**）
- [37-product-experience-agent-studio-architecture](technical/37-product-experience-agent-studio-architecture.md)（**Kokoro 统一入口、App、Feature 与单/多 Agent 产品架构**）
- [38 GA 公共运行契约](technical/38-ga-public-runtime-contract.md)（**Feature-first Root command 与 Session/GA 的唯一公共边界**）
- [39-ga-evaluation-and-evidence-architecture](technical/39-ga-evaluation-and-evidence-architecture.md)（**GA 真实装配评测、运行证据与上线门**）
- [40-ga-work-profiles-and-bounded-fanout](technical/40-ga-work-profiles-and-bounded-fanout.md)（**GA 同一父 Run 的 private task、map/reduce 与恢复边界**）
- [41-feature-outcome-contracts-and-quality-gates](technical/41-feature-outcome-contracts-and-quality-gates.md)（**Feature 用户可见交付、质量/成本基线与 promotion gate**）
- [42-ga-core-architecture](technical/42-ga-core-architecture.md)（**一个闭环 GA 底座、Feature/Agent 组装、DeepAgents 原生执行、identity/namespace 与外部 owner 的首读总览**）
- [45-ga-prototype-readiness-audit](technical/45-ga-prototype-readiness-audit.md)（**当前原型差距、default-only 首发闭环与实现前置条件**）
- [后端逐仓库设计卡](technical/backend-design/README.md)（每个仓库的职责、目录、owner、契约和 100 分验收证据）
- [后端逐仓库设计审计](technical/backend-design/10-design-audit.md)（设计完成度与当前实现差距）

### 模块 modules/

当前运行模块按子仓归属理解：

- [kokoro-agent](modules/kokoro-agent.md)（独立执行子仓）
- [kokoro-iam](modules/kokoro-iam.md)（独立身份与权限子仓）
- [kokoro-model](modules/kokoro-model.md)（独立模型目录子仓）
- [kokoro-system](modules/kokoro-system.md)（独立系统配置子仓）
- [后端逐仓库设计卡](technical/backend-design/README.md)（BFF、Billing、Capability、Storage、Scheduler 的当前职责、契约和验收证据）

历史模块记录（只用于考古）：

- [kokoro-platform](modules/kokoro-platform.md)、[kokoro-hub](modules/kokoro-hub.md)
- [kokoro-site](modules/kokoro-site.md)、[kokoro-user](modules/kokoro-user.md)
- [kokoro-credit](modules/kokoro-credit.md)、[kokoro-payment](modules/kokoro-payment.md)、[kokoro-litellm](modules/kokoro-litellm.md)
- [kokoro-session](modules/kokoro-session.md)、[kokoro-web](modules/kokoro-web.md)

当前 Chat 不从 `kokoro-session` 记录进入，而从 `kokoro-bff 的 Chat 内部业务边界` 与 [`business-bff-contract-v1.md`](../../kokoro/docs/integration/business-bff-contract-v1.md) 进入；Credit 不从 `kokoro-credit` 进入，而从 Billing 设计与 API 契约进入。

### 业务链路 business-flows/

- [00-overview](business-flows/00-overview.md)
- [site-resolution](business-flows/site-resolution.md)
- [user-register-login](business-flows/user-register-login.md)
- [general-chat](business-flows/general-chat.md)
- [agent-session-web-general-chat-runtime](business-flows/agent-session-web-general-chat-runtime.md)
- [agent-handoff](business-flows/agent-handoff.md)
- [session-lifecycle](business-flows/session-lifecycle.md)
- [credit-reserve-commit-refund](business-flows/credit-reserve-commit-refund.md)
- [payment-to-credit](business-flows/payment-to-credit.md)
- [model-resolution](business-flows/model-resolution.md)（历史 V1 ModelBinding resolver；目标模型选择见 36/38）
- [music-studio-generate](business-flows/music-studio-generate.md)
- [artifact-job-result](business-flows/artifact-job-result.md)

### 运维 operations/

- [local-development](operations/local-development.md)
- [docker-and-k8s](operations/docker-and-k8s.md)（deployment plane；不定义 GA 产品编排）
- [admin-console](operations/admin-console.md)
- [testing-checklist](operations/testing-checklist.md)
- [历史实现清单](operations/migration-checklist.md)
- [release-checklist](operations/release-checklist.md)

### 决策 decisions/

- [ADR-001 站点边界](decisions/ADR-001-site-boundary.md)
- [ADR-002 用户身份](decisions/ADR-002-user-identity.md)
- [ADR-003 credit 账本](decisions/ADR-003-credit-ledger.md)
- [ADR-004 agent 编排](decisions/ADR-004-agent-orchestration.md)
- [ADR-005 MySQL 与 Mongo](decisions/ADR-005-mysql-and-mongo.md)
- [ADR-006 agent sandbox runtime](decisions/ADR-006-agent-sandbox-runtime.md)（历史 V1 sandbox 实现）
- [ADR-007 kokoro-platform 子模块](decisions/ADR-007-kokoro-platform-submodule.md)
- [ADR-008 Agent / Session / Web 标准运行时边界](decisions/ADR-008-agent-session-web-standard-runtime.md)（历史 V1 runtime）
- [ADR-012 后端子仓库与 DDD 分层规范](decisions/ADR-012-backend-subrepository-ddd-layers.md)（历史全局拆仓决策）
- [ADR-014 Payment/Credit 合并为 Billing](decisions/ADR-014-billing-subrepository-consolidation.md)
- [ADR-024 BillingSubject 与 PayerAccount 分离](decisions/ADR-024-billing-subject-payer-separation.md)
- [ADR-025 腾讯云/阿里云费用中心模式复用](decisions/ADR-025-cloud-billing-patterns.md)
- [ADR-026 Order/Adjustment/PaymentCollection 事实层](decisions/ADR-026-commerce-order-payment-facts.md)
- [ADR-027 Billing API 版本与传输边界](decisions/ADR-027-billing-api-versioning-and-transport-boundary.md)
- [ADR-015 Feature Context 与 DeepAgents AgentState](decisions/ADR-015-agent-state-and-feature-context.md)
- [ADR-016 编排策略、回复归属与安全 ProductEvent](decisions/ADR-016-orchestration-policy-and-product-event-projection.md)
- [ADR-017（已废止）：DeepAgents 就绪历史记录](decisions/ADR-017-ga-compiled-graph-readiness-and-feature-promotion.md)
- [ADR-018 DeepAgents Thread Context、原生压缩与 Memory](decisions/ADR-018-ga-thread-context-compaction-and-memory.md)
- [ADR-019（已废止）：动态组装历史记录](decisions/ADR-019-ga-builder-as-catalog-compiler.md)
- [ADR-020 原生框架组合与 Official Swarm 接入门](decisions/ADR-020-native-framework-compatibility-and-swarm-adapter.md)
- [ADR-021 全局 FeatureKey、tenant/App 映射与 Feature 组合 identity](decisions/ADR-021-feature-key-global-catalog-identity.md)
- [ADR-022 GA RunExecutionAttestation 与动态 Capability 重验](decisions/ADR-022-run-execution-attestation-and-dynamic-capability-resolution.md)

### 工程规范 standards/

- [后端工程规范入口](standards/README.md)

## 旧文档处理

旧文档中关于 `seq`、`cursor`、`lastResumeId`、`?after=`、SQLite 默认存储、
浏览器手动维护 replay cursor 的叙述属于历史实现阶段资料。本手册当前标准：

```text
event_id 只做事件幂等与去重，不作为跨仓业务排序字段。
SSE id 是传输层内部续点，不进入产品领域模型。
浏览器刷新加载当前 BFF Chat snapshot，再按当前 BFF Chat contract attach active run；不自行维护跨设备业务 cursor。
Chat/Session durable facts 由 `kokoro-bff 的 Chat 内部业务边界` 按其 PostgreSQL contract 负责；Agent 执行事实由 `kokoro-agent` 按自己的 owner contract 负责。
Redis 只用于实时传输、短期队列、lease、cache 和幂等快速路径；不作为长期事实源。旧 Mongo/Session 叙述只保留在历史文档中。
```

主仓另有 `docs/product`、`docs/protocol`、`docs/requirements`、`docs/research` 保留历史设计与协议材料；全局总设计统一从本目录进入。
## Billing 设计基线
- [kokoro-billing 子仓库入口](../../kokoro-billing/README.md)
- [Billing 子仓库总体架构](technical/31-billing-subrepository-architecture.md)
- [成熟方案调研与复用裁决](technical/32-billing-mature-systems-research.md)
- [Billing 需求闭环与验收标准](technical/48-billing-requirements-and-acceptance.md)
- [Billing 最终业务与技术架构](technical/49-billing-final-technical-architecture.md)
- [Billing 商业系统重构版最终架构](technical/50-billing-commerce-rearchitecture.md)
- [事务矩阵](technical/billing-transaction-matrix.md)
- [MySQL Schema v1（历史）](technical/billing-mysql-schema-v1.md)
- [Payment/Credit 历史映射](technical/billing-migration-map.md)
- [Billing API 契约](technical/billing-api-contract-v1.md)
- [Billing SQL 标准（当前 PostgreSQL）](technical/billing-sql-standard.md)
- 旧 Credit/Payment 切换 Runbook 不属于当前 clean-build 方案。

- [Billing CI 与首发门禁](technical/billing-ci-and-migration-gates.md)
