---
artifact: architecture-audit
version: "1.0"
created: 2026-08-13
status: current-fact
scope: kokoro-root-agent-session-web-platform
---

# Kokoro SQL-first 能力与现有实现审计

## 0. 结论

这次不从进程数、部署便利或现有目录反推架构。审计后的结论是：

1. **GA 执行内核已经成熟，保留。** DeepAgent 组装、worker supervisor、HITL、checkpoint/resume、outbox/fence、control inbox、tool effect journal、sandbox 与 Web 主聊天状态机不是重写对象。
2. **Web User 主闭环已经成熟，保留。** 纯 reducer/projection、SSE 重连、幂等 command、BFF 身份封装和完整 Chat/HITL UI 都应继续使用。当前 owner hydration 只返回 metadata，历史内容依赖从 `lastSeq=0` 全量回放；目标必须补成 message/part/interaction 完整 snapshot + watermark 后的 SSE tail，不能把现状误记为完整 content snapshot。
3. **需要重写的是后端数据权威与边界。** 当前 Platform 是六份 MySQL Prisma schema 加 Hub Mongo；Session 是 13 个 Mongo collection；Agent 还会直接读写部分 Session collection。跨域关系、事务和 ownership 没有统一 SQL 权威。
4. **当前 Platform 不是废代码。** User/Team 事务、Credit hold/settle、Payment 幂等补偿、Hub package/MCP 校验、Site host resolve、Model fallback、Admin dual-control 都有可复用实现。
5. **最终形态应先定 PostgreSQL 关系模型，再由表 ownership 和事务边界推导能力子仓及 RPC。** 不能再由现有 package、端口、Docker service 或语言决定领域边界。

## 1. 审计基线

本报告只以当前 Root pin 和 checked-out child HEAD 为事实，不引用其他 worktree：

| 仓库 | HEAD |
|---|---|
| Root | `ac516fca61646ad4d8930439c24e76dac2da212e` |
| Agent | `18b394dc3df019244875e643c142c2b08b9db708` |
| Platform | `d30a16a782aca0fe131acbe8cbfbbd63fdf1b989` |
| Session | `4f4aa3defc5cce79be58c447d7f053c6204ef48f` |
| Web | `f3936befb7ae4c219273ae9b7f4efb97cb6a1425` |

### 1.1 本轮实际验证

| Surface | 结果 | 准确解释 |
|---|---|---|
| Root contract generator | `23 passed` | 当前 YAML contract 生成器工作正常 |
| Platform workspace tests | `1038 passed` | 八个 package 的业务单测强；根 DDD layout gate 与实际目录冲突 |
| Platform typecheck | 通过 | 当前 TypeScript 类型闭合 |
| Platform DB integration | 未取得 | 本地缺六个 `DATABASE_URL_*`，不能宣称数据库集成通过 |
| Web tests | `521 passed` | User 484、Admin 25、i18n 12 |
| Web typecheck/build | User/Admin 通过 | User 成熟；Admin 仍主要是控制台壳和 gateway client |
| Web lint | 未全绿 | i18n 缺局部 eslint 依赖，Admin ESLint 9 配置错误 |
| Agent pure/focused tests | `318 passed`，10 个 infra error | error 均为 Redis 未启动；不是执行核心失败 |
| Agent full release gate | 未取得 | Redis/Mongo 未启动；ruff 16 项；本地 pyright 环境报告大量依赖/API 漂移 |
| Session tests | 未取得 | 当前 checkout 无 `node_modules`；CI 定义了 Mongo/Redis 测试环境 |

“代码很多”不等于“全部上线完成”；“局部门禁没跑通”也不等于应推倒成熟算法。后续计划必须同时保护这两个事实。

## 2. 当前数据现实

### 2.1 Platform

当前 SQL 权威是六份 MySQL Prisma schema，共 37 张表：

- Site：Site、Domain、App、Policy、Brand、SEO、FeatureFlag。
- User：User、Team、Membership、Role、Invite、ServiceAccount、MagicLink、RefreshToken、AuditLog。
- Model：ProviderAccount、ModelBinding、ModelLabel、SiteModelPolicy。
- Credit：Account、LedgerEntry、Hold、UsageRecord、PricingRule。
- Payment：Plan、Order、Subscription、PaymentEvent、PaymentProvider、Refund。
- Admin：OperatorRole、OperatorAccount、AuditLog、ApprovalRequest、VerificationToken、AuthEvent。

Hub 另以 Mongo 保存 Skill/MCP current、revision 和 secret。即使六个 datasource 指向同一个 MySQL，代码仍按六套迁移、六套 client、HTTP hop 和无 FK 字符串引用运行，不存在统一事务与 owner inventory。

### 2.2 Session / Chat

Session 当前用 Mongo 保存 13 个 collection：Session、Message、Run、SessionSeqCounter、Event、Pause、Delivery、Share、ControlOutbox、RunDispatch、RunEventReceipt、ReceiptManifest、BillingJournal。Control decision IDs 内嵌在 Run 文档，不是独立 collection。

已经存在且必须保留的语义：

- `(session,event_id)` 与 `(session,seq)` 幂等、单调事件；
- `(session,idempotency_key)` Run 幂等；
- 一个 Session 同时一个 active Run；
- durable event 先落库再 broadcast；
- terminal convergence、gap/quarantine、recovery/finalization；
- control recorded/published/persisted/applied；
- Web 不直连 GA，Agent 不写 Message。

当前确定缺陷：

- Submit 的 active slot、message、run、dispatch、billing 是多次独立写，崩溃可留下孤儿 active slot；
- Control decision 与 outbox 不在同一事务；
- Agent 和 Session 双写 dispatch/receipt manifest；
- Session 直接拥有 Model/Hub/Credit/Artifact 解析与编排；
- Message 是可变大字段，缺 branch、edit/regenerate 和 versioned part；
- owner 被简化成 namespace；
- incompatible event 和 dispatch timeout 会被 Session 伪造成 GA terminal fact。

### 2.3 Agent

Agent 当前 durable state 由 Redis + Mongo 组成：run ledger 大文档、LangGraph checkpoint/writes、memory、dispatch DLQ、event outbox、tool/control/effect/usage/sandbox state。

执行核心质量高；问题是持久化边界和 catalog/provider/storage 越权：

- SkillHub 同时写 catalog、seed、package 与 runtime materialization；
- MCP runtime 直接读 Hub revision/secret；
- GA 仍保留 direct-provider fallback；生产 LiteLLM 路径只持 gateway key，最终只需删除 fallback ownership；
- workspace/delivery durable metadata 没有独立 Storage owner；
- 与 Session 共享 collection 字段级双写。

### 2.4 Web

User Web 已形成稳定的 UI/状态机/BFF 三层，缺口主要是后端真源、真实 infra E2E，以及可选附件能力。Admin 有可用壳，但数据/auth migration 与 Platform Admin 重复，最终应只做 IAM 和各能力 Admin RPC 的客户端。

## 3. 能力成熟度与裁决

| 能力 | 当前成熟度 | 裁决 |
|---|---:|---|
| GA execution / HITL / recovery | 高 | **KEEP** 算法；只换 persistence 与 capability/model/storage adapter |
| User Web chat engine/UI/BFF | 高 | **KEEP**；对接新 Chat/IAM API |
| User/Team/Membership/Invite | 中高 | **KEEP** 事务与测试；归并到 IAM |
| Authentication | 中 | **KEEP** token hash/CAS/JWKS；补标准 Identity/Credential/Session；MFA/passkey 后续 ADR |
| Credit hold/settle/release | 高 | **KEEP** domain 算法；修 quota 原子性并补 Grant/source ledger |
| Payment order/webhook | 中 | **KEEP** adapter/幂等/sweep；拆出 Catalog/Fulfillment，补真实 checkout |
| Skill/MCP | 中高 | **KEEP** validation/hash/SSRF/keyring；**REWRITE** SQL revision/claim/grant ownership |
| Site | 中 | **KEEP** host/DNS/resolve；Site 作为产品顶层，简化 Brand，补 lifecycle |
| Model | 中低 | **KEEP** catalog/fallback/health/secret-ref；补 immutable revision/routing；调用、attempt telemetry 与 usage 继续归 GA/LiteLLM |
| Admin | 中 | **KEEP** OIDC/RBAC/dual-control 概念；重写 effect receipt/reconcile |
| Session projection/recovery | 中高 | **KEEP** 行为；**REWRITE** PostgreSQL UoW 与 Chat 模型 |
| Storage / Asset / Artifact | 低 | **ADD** 独立能力边界 |
| Catalog / Redemption / Fulfillment | 很低 | **ADD**，复用 Payment/Credit 而不是复制 |

## 4. KEEP / MOVE / REWRITE / DELETE

### KEEP

- Agent assembly、supervisor、HITL、checkpoint/resume、outbox/fence、control inbox、effect journal、sandbox。
- Web reducer/projection、SSE、reattach、idempotency、BFF sealed session、Chat/HITL UI。
- Session durable-first projection、terminal recovery、watermark、control lifecycle。
- User/Team/Membership/Invite 的事务与最后 owner 保护。
- Credit bucket/hold/capture/release/expiry 与幂等算法。
- Payment webhook 验签、event/order 幂等、confirming sweep、refund 补偿。
- Hub package 校验、hash、MCP config/secret/SSRF。
- Site host/DNS/active resolve；Model fallback/health；Admin OIDC/RBAC/dual-control。

### MOVE

- User auth/profile/team/RBAC → `kokoro-iam` 内部模块。
- Session 的 Conversation/Message/Run/HITL/projection → `kokoro-chat`；Project 仅作为后续可选分组能力。
- Skill/MCP catalog、revision、grant、package metadata → `kokoro-capability`。
- Provider catalog/routing/health → `kokoro-model`；provider invocation、attempt telemetry 与 usage aggregation 留在 `kokoro-agent`/LiteLLM。
- workspace/blob/upload/scan/asset/artifact/delivery lifecycle → `kokoro-storage`。
- Plan 中产品/价格/benefit、Redemption、Fulfillment、SubscriptionTerm、Credit → `kokoro-entitlement`。
- provider customer/checkout/event/settlement/refund → `kokoro-payment`。
- Admin 业务规则留在各 owner；Admin Web 只调用 owner RPC。

### REWRITE

- MySQL/Mongo 最终权威 → 一份 PostgreSQL 18 canonical baseline。
- 六份 Prisma datasource、Hub/Session/Agent Mongo repository → capability-owned PostgreSQL repositories。
- Session submit/control/terminal → SQL transaction + outbox/inbox。
- Agent/Session 共享 collection → owner RPC/event acknowledgement。
- mutable Plan → immutable OfferRevision/Price/Benefit。
- Hub current+revision 双写 → 单事务 revision/pointer/grant。
- Admin remote effect → command receipt/effect receipt/reconcile。

### DELETE

- 由进程角色、端口、Docker service 反推领域 ownership 的规则。
- 跨服务共享 Mongo collection 与字段级双写。
- Session 内 Hub/Model/Credit/Artifact owner 逻辑。
- GA 内 catalog control-plane writer 和 production direct-provider ownership。
- Admin Web 自有业务数据库 migration、通用 fetch 作为业务 authority。
- 长期双写、旧 API alias、旧 datasource 和兼容层。

## 5. 对下一步设计的硬约束

1. 一个物理 PostgreSQL；Root 组合并验证一份 baseline。
2. SQL 使用正常 PK、FK、UNIQUE、CHECK、INDEX 和事务；不人为禁止关系约束。
3. 表可以放在同一数据库；ownership 是“谁能写哪张表/哪个状态”，不是给每个模块造数据库。
4. 子仓按能力边界划分，子仓内部再分模块；仓库不是模块，模块也不是部署单位。
5. 同仓模块直接调用 application service；跨仓同步调用使用 Protobuf RPC；异步事实只在确有解耦/重放需要时走 outbox/Redis Stream。
6. Web 只经 HTTP/BFF；MCP 只用于 Agent 工具能力，不充当通用内部 RPC。
7. GA、Web 的成熟核心不重写；只改边界 adapter。
8. 首个闭环完成后硬删旧存储和旧入口，不维持两套架构。

下一份方案以这些事实为输入，不以旧目标文档的进程拓扑为输入。
