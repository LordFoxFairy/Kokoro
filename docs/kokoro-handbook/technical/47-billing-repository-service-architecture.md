# Billing Repository / Service / 设计模式总方案

> 历史讨论稿。当前 clean-build repo/service 目标以 [50-billing-commerce-rearchitecture.md](50-billing-commerce-rearchitecture.md) 为准；不为旧 V1 增加兼容层。

状态：目标架构与实施方案，2026-08-24。本文回答三个问题：Billing 是否需要 Repository/Service 分层、Git repo 与
runtime service 如何划分、需求和设计模式如何形成可验证闭环。

## 1. 直接结论

### 1.1 Git repository 与 runtime service 不是一回事

当前采用 **一个 Git repository、一个业务 bounded context 集合、多个可独立启动的 runtime process**：

```text
kokoro-billing/                  # 一个 Git repo，一个 owner，一个版本线
  billing-api                    # HTTP User/Admin/Internal/Webhook
  billing-payment-worker         # Provider inbox -> settlement/reversal processor
  billing-credit-sweeper          # grant/hold expiry worker
  billing-migrator                # 单实例 migration job
```

这不是把每个 noun 拆成一个微服务。套餐、兑换、积分和支付共享严谨的账务边界，拆成独立服务会把一次本应在 MySQL
事务内完成的 `Redeem -> Grant -> Journal` 变成分布式补偿问题。未来只有当 bounded context 的数据库 owner、团队边界、
吞吐和发布生命周期真正分离时，才拆成独立部署/仓库。

### 1.2 Service 分层

Billing 中的 `Service` 不是一个万能 Service 类，而是四种明确角色：

| 类型 | 责任 | 是否持有 SQL | 示例 |
|---|---|---:|---|
| Application Service / Command Handler | 编排一个用例、授权、事务、幂等、锁顺序、调用 ports | 否 | `RedeemCodeHandler`, `CreateCheckoutHandler` |
| Domain Service | 无法归属于单一 aggregate 的纯业务规则 | 否 | `GrantAllocator`, `PromotionEligibility` |
| Repository | 一个 aggregate/fact owner 的持久化读写、锁定和唯一事实操作 | 是（实现层） | `CreditGrantRepository`, `RedeemCodeRepository` |
| Infrastructure Adapter / Worker | MySQL、Redis、Stripe、outbox、HTTP、定时任务等外部适配 | 是（适配层） | `MysqlRedeemCodeRepository`, `StripeWebhookAdapter` |

Query/read model 可以绕过 Domain Aggregate 使用专用 `QueryService`，但 mutation 只能通过 Application Service -> Repository；
不允许 Controller、Worker、Provider adapter 直接写业务表。

### 1.3 当前实现的真实状态

现有 `kokoro-billing/src/modules/*` 已按 bounded context、transaction 和业务链路分组，但多个 service 目前直接持有
`mysql2 Connection` 并内嵌 SQL。这是可运行的第一实现切片，不是最终分层标准。

本方案将进行 **渐进式 seam extraction**：先冻结端口和 aggregate owner，再把 SQL 从 Application Service 移到 repository
实现；不为了形式把每条 SELECT 包一层无语义的 GenericRepository。

## 2. 大厂/成熟实践的采用原则

成熟 DDD 指南通常建议：一个 bounded context 一个内聚 domain model；Repository 把持久化关注点隔离出 domain；每个
aggregate root 一个 repository；同一 bounded context 可以由多个 physical process 组成，但不因此复制 domain model。
这与当前 Billing 的“一个 repo、Payment + Entitlement 两个 bounded context、API/worker 分进程”一致。

采用：

- Strategic DDD：bounded context、context map、ubiquitous language、anti-corruption layer；
- Tactical DDD：aggregate root、entity、value object、domain service、repository、domain event；
- Hexagonal / Ports & Adapters：domain/application 不依赖 MySQL、Redis、Fastify、Stripe；
- Transaction Script 只用于简单 read/query 或 provider parsing，不用于 Credit/Redeem mutation；
- CQRS-lite：command 写 aggregate/fact，query 使用专用 read SQL；不建设没有读写压力依据的事件溯源系统；
- Inbox/Outbox：外部事件先落库，同一事务写 outbox，消费者至少一次、source fact 幂等；
- Process Manager：只用于跨 transaction 的 Payment -> Entitlement、provider unknown reconciliation；
- Specification：Promotion eligibility、Campaign quota、Package applicability 组合规则；
- Strategy/Adapter：Stripe/WeChat/Alipay provider 与优惠计算策略；
- Factory：从 immutable PackageRevision/BenefitTemplate 创建 grant，不让 HTTP DTO 直接构造账务事实。

不采用：

- 每张表一个微服务；
- 一个 `BillingService`/`Repository<T>` 包揽所有领域；
- Redis lock 作为余额、兑换次数或幂等最终权威；
- 为了“看起来 DDD”而创建只有转发逻辑的 Entity/Repository；
- 当前阶段引入 Kafka、PostgreSQL、ClickHouse 或完整 invoice engine。

## 3. 目标目录结构

```text
kokoro-billing/
├── src/
│   ├── bounded-contexts/
│   │   ├── entitlement/
│   │   │   ├── domain/
│   │   │   │   ├── catalog/              # Package/Revision/Price/Benefit
│   │   │   │   ├── credit/               # Account/Grant/Hold/Journal
│   │   │   │   ├── redeem/               # Campaign/Code/Redemption
│   │   │   │   ├── promotion/            # Promotion/Discount/Eligibility
│   │   │   │   └── shared/                # value objects 与 domain event base
│   │   │   ├── application/
│   │   │   │   ├── commands/              # handler + command DTO + result
│   │   │   │   ├── queries/               # read/query service
│   │   │   │   └── ports/                 # repository、clock、outbox、authorization ports
│   │   │   └── infrastructure/mysql/     # 每个 aggregate/fact 的具体 repository
│   │   └── payment/
│   │       ├── domain/                    # Checkout/Settlement/Subscription/Reversal
│   │       ├── application/commands/
│   │       ├── application/queries/
│   │       ├── application/ports/
│   │       └── infrastructure/mysql/     # Payment repositories
│   ├── cross-context/
│   │   ├── payment-entitlement/           # stable application ports + ACL
│   │   └── events/                        # versioned integration event envelope
│   ├── runtime/
│   │   ├── api.ts                          # Fastify composition root
│   │   ├── payment-worker.ts               # worker composition root
│   │   ├── credit-sweeper.ts               # sweeper composition root
│   │   └── migrator.ts                     # migration composition root
│   └── infrastructure/                    # shared technical adapters only
│       ├── mysql/                          # pool/UoW/transaction context
│       ├── redis/                          # hint/lease/cache
│       ├── providers/                      # external provider adapters
│       ├── observability/
│       └── security/
├── contract/openapi/v1/                  # 首发 HTTP contract；版本只在 transport boundary
├── database/migrations/
├── test/
│   ├── contract/
│   ├── domain/
│   ├── application/
│   ├── integration/
│   └── architecture/
└── docs/
```

版本规则：首发路由统一为 `/v1/...`。只在 `contract/openapi/v1/`、`interfaces/http/v1/` 和 `interfaces/admin/v1/`
放 transport contract；`application`、`domain`、`ports`、`repository`、`database` 不按 API 版本复制。未来 v2
只有在 breaking change 时新增 adapter 和 OpenAPI contract，不在首发阶段创建空 v2 或双写。

迁移规则：当前 `src/modules` 不会一次性大搬家；每完成一个 vertical slice，按上述边界迁移并删除旧直连路径。最终禁止
`src/interfaces` import concrete MySQL repository，禁止 `domain` import `mysql2`/`redis`/`fastify`。

## 4. Aggregate 与 Repository 设计

### 4.1 Aggregate 边界

| Aggregate / fact owner | 一致性不变量 | Repository 最小职责 |
|---|---|---|
| `PackageRevision` | 发布后不可变；价格/benefit snapshot 稳定 | find published、lock revision、publish revision |
| `Promotion` / `PromotionRedemption` | eligibility、次数、窗口、状态不能超发 | lock promotion、reserve/commit/release redemption |
| `RedeemCampaign` / `RedeemCode` | 单码一次、quota 不超、hash 不泄露 | find by hash for update、mark redeemed/disable |
| `CreditAccount` | available + held 与 grant/allocation 投影一致 | lock account、update projection、read summary |
| `CreditGrant` | remaining 不负、来源唯一、过期/撤销规则 | select eligible for update、consume/revoke |
| `CreditHold` | active/captured/released 单向状态、allocation 总额平衡 | create hold、lock hold、capture/release |
| `CreditJournal` | append-only、来源可追踪、序号单调 | append entry、next sequence、read ledger |
| `Checkout` | quote hash、租户、金额和 immutable benefit snapshot 一致 | create idempotent、lock checkout、attach provider session |
| `PaymentSettlement/Reversal` | provider source 唯一、退款不超过已结算金额 | record fact、lock settlement、record reversal |

一个 Repository 可以在一个 transaction 中协作多个 aggregate repository，但不能让一个 Repository 跨 bounded context
写入对方表。跨 context 使用 application port/outbox。

### 4.2 Ports 示例

```ts
export interface RedeemCodeRepository {
  findForUpdate(siteId: string, codeHash: Buffer): Promise<RedeemCodeRecord | null>;
  markRedeemed(input: { siteId: string; codeId: string; redemptionId: string; redeemedAt: Date }): Promise<void>;
}

export interface CreditGrantRepository {
  listEligibleForUpdate(input: { siteId: string; accountId: string; amountMicros: bigint }): Promise<CreditGrantRecord[]>;
  consume(input: { siteId: string; grantId: string; amountMicros: bigint }): Promise<void>;
}

export interface BillingUnitOfWork {
  run<T>(task: (tx: BillingTransaction) => Promise<T>): Promise<T>;
}
```

Port 返回领域可用 record/value object，不返回 mysql2 `RowDataPacket`。Repository 实现负责参数绑定、锁顺序、复合租户条件、
affectedRows 检查和数据库错误映射。

## 5. Application Service 设计

每个 command handler 只做以下顺序：

```text
parse/authorize request
 -> derive tenant/subject from trusted context
 -> calculate payload fingerprint
 -> claim durable command receipt
 -> BillingUnitOfWork.run()
     lock aggregate roots in documented order
     validate domain invariants/specifications
     write facts/projections/journal/outbox
 -> map result/error to contract
```

典型 handler：

```text
CreateCheckoutHandler
RedeemCodeHandler
ReservePromotionHandler
PublishPackageRevisionHandler
AuthorizeUsageHandler
CaptureUsageHandler
ReleaseUsageHandler
AcceptPaymentSettlementHandler
AcceptPaymentReversalHandler
ExpireGrantsHandler
ReconcileBillingHandler
```

Handler 不知道 Fastify request，不接收任意 `accountId` 作为授权依据，不调用 provider 网络请求；provider session 创建采用
明确的 two-phase orchestration：先 durable checkout intent，再外部 provider idempotency，再回写 session fact。

## 6. 需求分析与设计流程

每个新能力必须先产生以下设计证据，不能直接从“加一张表”开始：

### 6.1 需求卡

```text
用户/运营角色：谁发起、谁受益、谁审计
核心旅程：成功路径与所有可见状态
业务词汇：Package、Price、Benefit、Promotion、Redeem、Grant、Wallet
金额/积分单位：currency minor / credit_micros，转换边界
权限：tenant、subject、team、operator、service identity
不变量：最多一次、不可超发、不可跨租户、不可负余额、可重建
失败语义：provider unknown、DB timeout、Redis outage、worker crash、重复请求
可观测性：requestId、sourceRef、audit、metrics、reconcile query
验收：Given/When/Then + property/invariant + integration evidence
```

### 6.2 Event Storming / Context Map 输出

先画事件链，而不是先画类：

```text
PackagePublished
PromotionReserved
CheckoutCreated
PaymentSettled
RedemptionCommitted
EntitlementFulfilled
CreditGranted
CreditHeld
CreditCaptured
CreditReleased
CreditRevoked
```

每个事件标注 owner、source fact、事务边界、重试策略和消费者；跨 context 只暴露 integration event，不共享实体和数据库
repository。

### 6.3 设计评审门

一个能力只有同时回答以下问题才能进入实现：

1. 谁是数据 owner，谁可以写？
2. 哪个 aggregate 控制不变量？
3. 一个请求的 durable idempotency key 是什么？
4. 并发锁定顺序是什么？
5. 外部调用失败会留下什么事实？
6. 退款/撤销/过期如何反向处理？
7. 查询如何按 tenant 隔离并分页？
8. Redis、outbox、worker、reconcile 分别承担什么？
9. API、SQL、事件、审计和指标是否同一套 vocabulary？
10. 如何用测试证明“不会重复、不会超发、不会跨租户”？

## 7. 非功能要求

| 类别 | 目标方案 |
|---|---|
| 一致性 | 同一 aggregate mutation 使用 MySQL transaction；ledger/source facts append-only |
| 可用性 | Redis 故障不影响最终正确性；provider/worker 失败可重试；unknown 保留 exposure |
| 安全 | tenant context 由 IAM/service identity 派生；卡密只存 hash；Admin 高风险动作需要 reason/audit |
| 性能 | hot path 使用复合索引、`FOR UPDATE`、批量 worker；Redis 仅作 hint，不把锁扩大到全局 |
| 可观测 | structured error、requestId、sourceRef、outbox age、dead letter、reconcile drift |
| 可演进 | schema expand/backfill/contract；V1 creditMicros 兼容投影，未来 benefit 多态化 |
| 运维 | API、payment worker、sweeper、migrator 独立进程；同 repo 同版本、独立扩缩容 |

## 8. 依赖规则与架构测试

必须加入 architecture tests：

```text
domain -> 只能依赖 domain/shared 标准库
application -> 可依赖 domain 与 ports，不能依赖 mysql2/redis/fastify
infrastructure -> 实现 ports，可依赖 mysql2/redis/provider SDK
interfaces -> 只能调用 application ports/handlers，不能执行 SQL
Payment -> 不能 import Entitlement concrete repository
Entitlement -> 不能 import Payment table/repository
mutation SQL -> 只能出现在 infrastructure repository 与 migration
```

允许的例外必须是带 ADR 的 composition root；不允许通过 barrel export 绕过边界。

## 9. 当前落地差距与实施顺序

当前主要差距不是总体领域方向，而是代码结构仍是“模块内 Application Service + 直接 SQL”。按以下顺序收敛：

1. 先建立 `BillingUnitOfWork`、领域 ports 和 architecture test，不改业务行为；
2. 迁移 Credit mutation：`CreditAccount`、`CreditGrant`、`CreditHold`、`CreditJournal` repositories；
3. 迁移 Redeem/Promotion target extension，先完成 domain/application/integration tests；
4. 迁移 Payment settlement/reversal/checkout repositories；
5. 迁移 query services 和 admin stats；
6. 最后拆 runtime composition roots，复用同一 application/domain 包；
7. 每一步保持现有 API、29 migrations 和真实 MySQL/Redis 测试全部通过。

不在本轮直接把所有旧文件重命名；先以 vertical slice 迁移，避免大规模机械改名制造风险。

## 10. 参考依据

- Microsoft：一个 bounded context 一个内聚 domain model，且一个 bounded context 可以由多个 physical service 组成：
  <https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/microservice-domain-model>
- Microsoft：Repository 把持久化移出 domain，原则上每个 aggregate root 一个 repository：
  <https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/infrastructure-persistence-layer-design>
- AWS：按 subdomain/bounded context 拆服务，并保持业务边界：
  <https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-decomposing-monoliths/decompose-subdomain.html>
- AWS：Hexagonal architecture、DDD、CQRS 和 command pattern 的组合实践：
  <https://docs.aws.amazon.com/prescriptive-guidance/latest/hexagonal-architectures/best-practices.html>
- Martin Fowler：Bounded Context：<https://martinfowler.com/bliki/BoundedContext.html>
