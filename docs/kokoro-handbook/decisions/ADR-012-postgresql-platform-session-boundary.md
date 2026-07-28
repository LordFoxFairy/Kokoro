# ADR-012 PostgreSQL 作为 Platform 与 Session 的关系型真源

状态：已采纳（2026-07-28）。  
取代：[ADR-005 MySQL + Mongo 数据边界](ADR-005-mysql-and-mongo.md)。  
实现状态：尚未完成；只有迁移、验证和发布门全部通过后才能称为 production-ready。

## 背景

Kokoro 尚未上线，当前代码却同时存在六套 Platform MySQL Prisma schema、跨同一 Platform bounded context 的
self-RPC，以及 Session Mongo 投影。目标产品要求 Site、Identity、Workspace、Catalog、Commerce、Credit、
Policy、Admin 在一次 Platform 工作流中完成强事务、幂等、receipt、outbox 和审计；Session 也需要完整
Conversation/Turn/Branch/MessagePart/RunView 投影、关系约束、搜索、command receipt 和 durable outbox。

继续保留 MySQL 多 schema + Mongo Session 会把错误的服务边界、跨库补偿和投影约束固化到新产品。项目尚未承载
生产事实，因此现在进行一次 clean replacement，比长期双写或为旧结构建立兼容层更安全。

## 决策

```text
PostgreSQL 18
  kokoro-platform: 独立 database、owner role、migration role、runtime role
    Site / Identity / Workspace / Catalog / Commerce / Credit / Model Control /
    Policy / Admin / Audit / transactional Outbox

  kokoro-session: 独立 database、owner role、migration role、runtime role
    Session / Branch / Turn / MessagePart / RunView / projection checkpoint /
    command receipt / Inbox / Outbox / DLQ

MongoDB
  kokoro-agent: checkpoint、runtime state、memory 等 GA 自有文档状态
  kokoro-hub: Skill/MCP registry、revision、secret metadata 等 Hub 自有文档状态

Redis
  queue、live stream、fanout、lease、rate limit、短期缓存；永不成为长期业务真源

Object Storage
  blob、package、upload、export、artifact bytes；数据库只保存受控 metadata/ref/hash
```

Platform 与 Session 只共享数据库引擎，不共享 database、schema、role、migration 或事务。跨仓仍只走版本化
HTTP/RPC/SSE/durable event；任何仓不得读取或写入另一仓数据库。

Platform 是一个模块化控制面产品。同一 Platform workflow 通过本地 application port 和一个
`PlatformUnitOfWork` 协作；`PlatformTransaction` 是 opaque capability，不能把 Prisma transaction client 暴露给
其他模块。每张表只有一个模块 owner，跨模块 workflow 只拿 transaction-scoped narrow port，禁止 self-RPC、
跨模块 repository import 和直接写他域表。

Session 只拥有对话与浏览器投影，不拥有 Site、Identity、Plan、Capability、Model、Pricing 或 Credit 真相。
Platform Admission 通过版本化 contract 提供准入和 receipt；Session 不能跨库补写 Platform 状态。

## 默认 Infra 与切换

根仓仍是 Infra authority。实现 Wave 1/3 时，默认开发/CI 基建中的 MySQL process 被一个 PostgreSQL 18 process
替换；不长期保留 MySQL + PostgreSQL 双默认栈，也不为并行 agent 启动多套 compose project。

旧 MySQL container 在切换时停止，旧 volume 仅归档保留。删除 volume、image 或开发数据属于独立破坏性动作，
不由本 ADR 授权。当前 Mongo、Redis、MinIO volume 同样保留。

切换顺序固定为：

1. 只读盘点旧 MySQL/Mongo 的 schema、row count、非 seed 数据和外部 receipt；发现未知生产/财务事实即停止。
2. 建立 PostgreSQL database、least-privilege roles、migration、backup/restore 与监控。
3. 停写并 drain；执行一次确定性转换，隔离无法证明 owner/order/digest 的行，不猜测补值。
4. 验证 row/digest/约束/投影/双 Site 隔离、receipt/outbox/reconciliation 与恢复演练。
5. 原子切换默认 Infra、应用配置与 traffic；旧存储只读归档，不再接写。
6. 完成一个完整 SLO 窗口和 rollback rehearsal 后，删除旧代码路径、env、self-RPC 和文档口径。

项目未上线，因此不实施长期 production dual-write。切换后数据库回滚采用 forward fix 或 restore point；不得把新
事实写回旧 MySQL/Mongo 来制造双真源。

## 理由

- Platform 的 Site/Identity/Commerce/Credit/Admin 需要跨模块强事务、约束、锁序、outbox 和财务可审计性。
- Session 的 branch DAG、part lifecycle、command receipt、projection checkpoint、Inbox/Outbox/DLQ 更适合显式
  关系约束和可重建投影。
- PostgreSQL 的事务、约束、JSONB、全文索引、advisory/row lock、logical observability 能统一两类关系型需求，
  同时保持两个独立数据库的部署与故障边界。
- Mongo 继续服务真正的文档型 owner；不是因为已有 Mongo 就让 Session 业务投影缺失关系不变量。
- 单一默认关系型引擎降低本地、CI、备份、恢复与 on-call 复杂度。

## 约束

- 跨仓禁止共享数据库、事务、ORM model、generated Prisma client 或 repository source。
- Platform 模块表 owner、依赖 DAG、public barrel 与 table-access gate 必须机器校验。
- 账务只使用 integer micros/decimal integer，不使用 float；Journal append-only，纠错使用 reversal/correction。
- Redis/cache 丢失不能导致业务事实丢失；对象存储 bytes 必须有数据库 owner/ref 与生命周期 receipt。
- migration、runtime、read-only/support role 分离；应用 role 不拥有 DDL 权限。
- 生产 readiness 必须包含真实 PostgreSQL concurrency、backup restore、failover、migration rollback、RPO/RTO、
  load/soak、跨 Site negative test 和 clean recursive clone evidence。
- 更新本 ADR 的实现 PR 必须同步 handbook、CODEBASE_MAP、INDEX、deployables manifest、compose/CI/runbook；在
  真实切换前，旧文档只能明确标成 current legacy，不得同时宣称两个目标真源。

## 被否决方案

### 继续 MySQL + Mongo

技术上可行，但会保留六套 Platform schema/self-RPC 和 Session 文档投影的错误边界；后续 Commerce UoW、
Admission receipt 和 branch projection 仍需额外分布式补偿或弱约束。

### Platform 用 PostgreSQL、Session 继续 Mongo

减少迁移面，但 Session 的 branch、part、receipt、Inbox/Outbox/checkpoint 仍缺数据库级关系不变量，并继续依赖
应用代码维持可重建性。

### Platform 与 Session 共用一个 PostgreSQL database

能方便联表，却破坏独立仓库、独立部署、独立回滚和协议边界，形成跨仓直写诱因，故禁止。

### 长期 MySQL/PostgreSQL 双写

会产生冲突真源、复杂恢复和无法证明的账务差异。项目尚未上线，没有承担该复杂度的理由。

## 影响

正面影响：Platform 工作流、Commerce/Credit、Session projection 和运维栈获得一致、可验证的事务基础；后续按
真实 aggregate 拆服务仍可通过 outbox/RPC 演进。

负面影响：需要一次性重写 Prisma schema/migration、Session store、默认 Infra、测试夹具和大量 handbook 当前
口径；团队必须掌握 PostgreSQL 运维，切换期间不能并行推进依赖旧存储的业务入口。

风险控制：以 Wave 1/2A/3 child spec、逐表 cutover ledger、真实数据库并发测试、备份恢复和 release evidence
约束实现。未生成这些证据前，本 ADR 只代表目标决策，不代表迁移已完成。
