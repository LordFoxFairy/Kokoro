# Kokoro 总手册

本目录是 Kokoro 的长期权威手册，放正式的产品形态、跨仓架构、模块边界、
业务链路、技术方案、运营规范和关键 ADR。

它不是过程方案池，也不是派工单目录。正在打磨、尚未成为正式版的跨仓方案放在
`docs/superpowers/specs/`；正式技术方案放回本目录的 `technical/` 或 `product/`；
执行计划放在 `docs/superpowers/plans/`；短期交接放在 `docs/handoffs/`。

子仓 README 说明当前实现，子仓 docs 说明局部实现细节；本手册负责把全局总设计统一起来。
子仓 docs 只能补实现细节，不能替代本手册。

## 当前事实源

整体架构、owner、协议、产品装配与当前能力状态统一见
[Kokoro 联邦产品平台总架构](technical/24-federated-product-platform-architecture.md)。旧 V1/V2 过程稿不再是
当前实现入口。模块是否可上线以子仓 composition、launch blocker、跨仓兼容与发布证据为准，不以“已有代码/测试”
替代完整业务闭环。

## 当前主链路

```text
Site Web -> Site BFF -> Platform public HTTP
Site Web -> kokoro-session HTTP/SSE -> durable transport -> kokoro-agent
kokoro-session -> Platform owner ConnectRPC
kokoro-agent -> Platform Hub ConnectRPC / Model Gateway ConnectRPC / narrow capability RPC
Platform Model Gateway -> LiteLLM/provider adapter OpenAI-compatible HTTP
```

```text
kokoro-web      每个 Site 独立项目；UI、BFF、snapshot/SSE 消费和浏览器投影，不直连 Agent/数据库。
kokoro-session  Conversation/Message/Run、浏览器 snapshot/SSE/control 与相关投影 owner。
kokoro-agent    LangChain/LangGraph 执行、Skills/MCP 消费、工具、handoff、checkpoint、sandbox；只认 opaque namespace。
kokoro-platform Site/Identity/Commerce/Credit/Model/Hub/Media/Artifact/Memory 等业务 owner 与多进程 composition。
PostgreSQL      Platform 与 Session 的结构化 owner 数据、RLS、receipt、outbox；各 workload 最小权限。
MongoDB         Agent checkpoint/ledger 与 Hub package/catalog 文档真源；使用独立逻辑数据库、credential 与 owner。
Redis           durable/live transport、短期 fanout、lease/限流辅助；不作最终业务真源。
S3/MinIO        Asset、Artifact、Skill package 和 workspace/delivery bytes；对象 key 不成为公共身份。
```

## 强制约束

```text
1. 文档必须中文。
2. 主仓 docs/kokoro-handbook 是总入口。
3. 子仓 docs 只能补实现细节，不能替代主仓手册；冲突以 technical/24 与已接受 ADR 为准。
4. siteId 是平台业务隔离边界；namespace 是 GA/runtime 唯一隔离键。
5. 同邮箱跨站默认不同用户；跨站共享只能通过标准 OAuth/OIDC linking 显式建立。
6. Root `contract/` 是跨仓契约单源，不新增第五个 contracts 仓库。
7. Platform 同 bounded context 通过 application interface/UoW 协作；禁止 self-RPC、跨模块 repository/表访问。
8. Platform 与 Session 的结构化 owner 数据使用 PostgreSQL；Agent checkpoint/ledger 使用 MongoDB。
9. Redis 只做 transport、live fanout、lease 与限流辅助，不作最终业务真源。
10. S3/MinIO 存放 Asset、Artifact、Skill package 和 workspace/delivery bytes。
11. Agent 不能直接扣积分；只能消费 owner 签发的预算/分配并回传 usage evidence。
12. Payment/Redemption 不直接写 Credit ledger，统一进入 Fulfillment。
13. Model/LiteLLM 不决定最终价格、套餐或权益。
14. Web/Gateway 不得绕过可信 ProductContext/SiteContext。
15. 浏览器通过 Session SSE 消费对话实时状态，不直连 Agent。
16. kokoro-agent 不直接面向浏览器，不成为 Platform 业务数据库。
17. kokoro-session 不执行 Agent，也不成为 Hub/Media/Memory 业务 owner。
18. GA 契约不得新增 userId/ownerId/workspaceId/siteId 作为第二隔离轴。
19. namespace 不加 user:/team: 等业务前缀；上游选择空间，GA 只消费 opaque namespace。
20. 不建立顶层 Generation 或通用 Job owner；长任务归属具体 domain。
```

## 目录

以下目录保留了不同阶段的产品与实现材料，并不表示每一页都是当前事实。涉及仓库拓扑、owner、存储、协议、命名或
上线状态时，必须先以 `technical/24` 与已接受 ADR 为准；旧页只补充仍未冲突的局部背景。

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

当前权威入口：

- [24-federated-product-platform-architecture](technical/24-federated-product-platform-architecture.md)（**当前整体架构唯一总入口**）

局部说明与历史资料：

- [00-system-overview](technical/00-system-overview.md)
- [01-repository-map](technical/01-repository-map.md)（历史局部说明；旧 MySQL/子仓结构已失效）
- [02-platform-architecture](technical/02-platform-architecture.md)（历史局部说明；旧多业务子仓结构已失效）
- [03-agent-architecture](technical/03-agent-architecture.md)
- [04-session-architecture](technical/04-session-architecture.md)（历史局部说明；存储/协议以 technical/24 为准）
- [05-web-architecture](technical/05-web-architecture.md)
- [06-data-storage](technical/06-data-storage.md)（已取代的 MySQL/Mongo 存储草案）
- [07-service-communication](technical/07-service-communication.md)（历史通信草案）
- [08-deployment](technical/08-deployment.md)（历史部署草案；旧 MySQL/三仓拓扑已失效）
- [09-security-permissions](technical/09-security-permissions.md)（历史安全草案；旧 MySQL/token 规则已失效）
- [10-observability](technical/10-observability.md)
- [11-agent-session-web-v1-runtime](technical/11-agent-session-web-v1-runtime.md)
- [12-agent-hitl-tool-interception](technical/12-agent-hitl-tool-interception.md)
- [13-agent-docs-map](technical/13-agent-docs-map.md)
- [14-web-i18n-capability](technical/14-web-i18n-capability.md)
- [15-v2-technical-plan](technical/15-v2-technical-plan.md)
- [16-session-deletion-cascade](technical/16-session-deletion-cascade.md)
- [17-namespace-runtime-isolation](technical/17-namespace-runtime-isolation.md)
- [18-capability-namespace-auth-sandbox-artifacts](technical/18-capability-namespace-auth-sandbox-artifacts.md)
- [19-current-runtime-capability-review-plan](technical/19-current-runtime-capability-review-plan.md)（历史扩展附录）
- [20-kokoro-v1-technical-plan](technical/20-kokoro-v1-technical-plan.md)（2026-07-10 三仓阶段历史基线）
- [21-platform-mainchain-closure](technical/21-platform-mainchain-closure.md)（签发链/计费链/编排/E2E-40，P1-P5 已落地事实）
- [22-capability-hub](technical/22-capability-hub.md)（历史实现册；旧 tRPC/Session consumer/Agent 直库方案已失效）
- [23-platform-ops-console](technical/23-platform-ops-console.md)（运营台现状：三维 RBAC / maker-checker / DB 审计 / manifest 代理 / internal-secret 现状）

### 模块 modules/

- [kokoro-platform](modules/kokoro-platform.md)
- [kokoro-hub](modules/kokoro-hub.md)
- [kokoro-site](modules/kokoro-site.md)
- [kokoro-user](modules/kokoro-user.md)
- [kokoro-model](modules/kokoro-model.md)
- [kokoro-credit](modules/kokoro-credit.md)
- [kokoro-payment](modules/kokoro-payment.md)
- [kokoro-litellm](modules/kokoro-litellm.md)
- [kokoro-agent](modules/kokoro-agent.md)
- [kokoro-session](modules/kokoro-session.md)
- [kokoro-web](modules/kokoro-web.md)

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
- [model-resolution](business-flows/model-resolution.md)
- [music-studio-generate](business-flows/music-studio-generate.md)（历史 Job 术语；以 ADR-015 MediaOperation 为准）
- [artifact-job-result](business-flows/artifact-job-result.md)（历史 Job 术语；以 ADR-015 为准）

### 运维 operations/

- [local-development](operations/local-development.md)
- [docker-and-k8s](operations/docker-and-k8s.md)
- [admin-console](operations/admin-console.md)
- [testing-checklist](operations/testing-checklist.md)
- [migration-checklist](operations/migration-checklist.md)
- [release-checklist](operations/release-checklist.md)

### 决策 decisions/

- [ADR-001 站点边界](decisions/ADR-001-site-boundary.md)
- [ADR-002 用户身份](decisions/ADR-002-user-identity.md)
- [ADR-003 credit 账本](decisions/ADR-003-credit-ledger.md)
- [ADR-004 agent 编排](decisions/ADR-004-agent-orchestration.md)
- [ADR-005 MySQL 与 Mongo](decisions/ADR-005-mysql-and-mongo.md)（已被 ADR-012 取代）
- [ADR-006 agent sandbox runtime](decisions/ADR-006-agent-sandbox-runtime.md)
- [ADR-007 kokoro-platform 子模块](decisions/ADR-007-kokoro-platform-submodule.md)
- [ADR-008 Agent / Session / Web 标准运行时边界](decisions/ADR-008-agent-session-web-standard-runtime.md)
- [ADR-009 Workspace Storage](decisions/ADR-009-workspace-storage.md)
- [ADR-010 BYO Extensions 与 Config Tree](decisions/ADR-010-byo-extensions-and-config-tree.md)
- [ADR-011 Asset Source](decisions/ADR-011-asset-source.md)
- [ADR-012 PostgreSQL Platform / Session 边界](decisions/ADR-012-postgresql-platform-session-boundary.md)
- [ADR-013 Product Memory 与 Context Authority](decisions/ADR-013-product-memory-and-context-authority.md)
- [ADR-014 Stable Interaction Owner 与 Decision Recovery](decisions/ADR-014-stable-interaction-owner-and-decision-recovery.md)
- [ADR-015 Media Operation 与 Artifact Authority](decisions/ADR-015-media-operation-and-artifact-authority.md)
- [ADR-016 Web Release Composition](decisions/ADR-016-web-release-composition.md)

## 旧文档处理

旧文档中关于 `seq`、`lastResumeId`、`?after=`、SQLite/MySQL 默认存储、Session 使用 Mongo、浏览器手动维护 replay
cursor 的叙述属于历史实现阶段资料。当前标准：

```text
eventId 只做幂等，不做排序。
SSE id: 是传输层内部续点，不进入产品领域模型。
浏览器刷新不保存 lastResumeId，而是加载 session snapshot 后重新 attach active run。
排序真源是 kokoro-session PostgreSQL owner projection 的持久化顺序和 SSE 单连接发送顺序。
PostgreSQL 是 Session 结构化 owner 数据真源；MongoDB 只保留 Agent checkpoint/ledger 等 Agent-owned 文档。
Redis 只负责 transport、实时传输和短期 lease，不作最终业务真源。
```

主仓另有 `docs/product`、`docs/protocol`、`docs/requirements`、`docs/research` 保留历史设计与协议材料；全局总设计统一从本目录进入。
