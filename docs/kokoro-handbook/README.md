# Kokoro 总手册

本目录是 Kokoro 主仓的产品手册和技术方案总入口，覆盖产品形态、
跨仓架构、模块边界、业务链路、运营规范和关键 ADR。子仓 README
说明当前实现，子仓 docs 说明局部实现细节；本手册负责把全局总设计
统一起来。子仓 docs 只能补实现细节，不能替代本手册。

## 实现状态

诚实区分"已建"与"规划"，避免把未落地的写成已落地：

```text
已建 / 已落基础（V1 运行时三仓 + 根契约）：
  kokoro-session 的 message-first API、Mongo SessionStore、
  session_events replay、SSE live；
  kokoro-web 的聊天 UI、EventSource 消费、eventId 去重、
  append-order reducer、HITL approve/reject/cancel；
  kokoro-agent 的 DeepAgents/LangChain worker、HITL interrupt、
  checkpoint/run_state、raw AgentEvent。

P0 待合流（仍属三仓运行时，不能写成已完成）：
  session run.request agent_run_input manifest 与 agent Python RunRequest 尚未合流；
  web 尚未 snapshot-first hydrate；
  MCP、skills、backendPolicy、e2b/custom sandbox 仍是目标能力，不是完整实现。

规划 / 部分实现（平台域）：
  kokoro-platform 下 site/user/model/credit/payment/litellm 多为 planned 或最小实现。
  相关模块、链路、运维文档描述目标设计，落地以各子仓为准。
```

## V1 运行时主链路（目标标准）

```text
kokoro-web -> kokoro-session -> Redis -> kokoro-agent
  -> Redis -> kokoro-session -> SSE -> kokoro-web
```

```text
kokoro-web      只做 UI、SiteContext 注入、snapshot 加载、SSE 消费、Skill/MCP 入口和本地投影。
kokoro-session  拥有聊天窗口、消息、运行状态、浏览器事件和 replay 语义。
kokoro-agent    拥有 LangChain/LangGraph 执行、Skills、MCP adapter、工具、子代理、HITL、checkpoint、memory、sandbox。
MongoDB         session messages/events、agent checkpoint/memory 和运行时文档状态的长期真源。
MySQL           三仓之外的平台业务域，三仓只消费上游解析后的 SiteContext/policy 结果。
Redis           队列、实时流、短期 live fanout、分布式锁和短租约，不作长期真源。
```

当前代码是否已达到目标标准，以
[V1 运行时技术方案](technical/11-agent-session-web-v1-runtime.md) 的“当前实现事实”和
各模块文档的“当前实现状态”为准。

## 强制约束

```text
1. 文档必须中文。
2. 主仓 docs/kokoro-handbook 是总入口。
3. 子仓 docs 只能补实现细节，不能替代主仓手册。
4. siteId 是第一业务隔离边界。
5. 同邮箱跨站默认不同用户。
6. 不新增 kokoro-contracts。
7. 不使用 ports 目录命名。
8. 核心管理和账务数据用 MySQL。
9. 产物、job result、创作内容、非结构化上下文用 Mongo。
10. Redis 只做 live stream、短期队列、广播、限流辅助，不作长期真源。
11. 当前不引入 PostgreSQL。
12. agent 不能直接扣积分（只能 credit.quote/hold/commit/release）。
13. payment 不能直接写 credit ledger。
14. model 不能决定最终价格。
15. web/gateway 不能绕过 SiteContext。
16. 浏览器只消费 kokoro-session 的 SSE。
17. kokoro-agent 不直接面向浏览器。
18. kokoro-session 不执行 agent。
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
- [08-deployment](technical/08-deployment.md)
- [09-security-permissions](technical/09-security-permissions.md)
- [10-observability](technical/10-observability.md)
- [11-agent-session-web-v1-runtime](technical/11-agent-session-web-v1-runtime.md)
- [12-agent-session-web-p0-implementation-design](technical/12-agent-session-web-p0-implementation-design.md)
- [13-agent-business-orchestration-roadmap](technical/13-agent-business-orchestration-roadmap.md)
- [14-agent-runtime-refactor-plan](technical/14-agent-runtime-refactor-plan.md)
- [15-skill-mcp-hub-runtime-boundary](technical/15-skill-mcp-hub-runtime-boundary.md)

### 模块 modules/

- [kokoro-platform](modules/kokoro-platform.md)
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
- [general-chat-to-music-entry](business-flows/general-chat-to-music-entry.md)
- [agent-handoff](business-flows/agent-handoff.md)
- [session-lifecycle](business-flows/session-lifecycle.md)
- [credit-reserve-commit-refund](business-flows/credit-reserve-commit-refund.md)
- [payment-to-credit](business-flows/payment-to-credit.md)
- [model-resolution](business-flows/model-resolution.md)
- [music-studio-generate](business-flows/music-studio-generate.md)
- [artifact-job-result](business-flows/artifact-job-result.md)

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
- [ADR-005 MySQL 与 Mongo](decisions/ADR-005-mysql-and-mongo.md)
- [ADR-006 agent sandbox runtime](decisions/ADR-006-agent-sandbox-runtime.md)
- [ADR-007 kokoro-platform 子模块](decisions/ADR-007-kokoro-platform-submodule.md)

## 旧文档处理

旧文档中关于 `seq`、`cursor`、`lastResumeId`、`?after=`、SQLite 默认存储、
浏览器手动维护 replay cursor 的叙述属于历史实现阶段资料。本手册标准：

```text
eventId 只做幂等，不做排序。
SSE id: 是传输层内部续点，不进入产品领域模型。
浏览器刷新不保存 lastResumeId，而是加载 session snapshot 后重新 attach active run。
排序真源是 kokoro-session 写入 Mongo 的追加顺序和 SSE 单连接发送顺序。
Mongo 是 session 消息和 runtime 文档长期真源；Redis 只负责实时传输和短期锁。
```

主仓另有 `docs/product`、`docs/protocol`、`docs/requirements`、`docs/research` 保留历史设计与协议材料；全局总设计统一从本目录进入。
