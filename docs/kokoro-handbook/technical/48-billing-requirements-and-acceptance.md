# Billing 需求闭环、业务旅程与验收标准

> 历史讨论稿。当前 clean-build 需求、状态机与验收基线以 [50-billing-commerce-rearchitecture.md](50-billing-commerce-rearchitecture.md) 为准。

状态：**目标需求与验收基线**，2026-08-24。本文补充 31、46、47 与 `kokoro-billing/docs/API_CONTRACT.md`；它不是“已实现”声明。

## 1. 产品问题与边界

Billing 解决四个问题：

1. 用户能看到可购买的套餐、价格和权益，并完成一次可重试的支付；
2. 支付成功后，权益和积分只发放一次，来源、过期时间和退款影响可追溯；
3. 模型/Feature 只能申请、确认、释放扣费，不能自己决定价格或直接写账本；
4. Admin 能运营目录、授权发放、退款、重试和对账，但不能绕过事实账本修余额。

当前不属于 Billing：登录、用户/组织主数据、模型目录、Agent/Session 状态、文件内容和支付机构最终账务。

## 1.1 成熟项目复核后的关键修正

本次不是只参考目录，而是复核了 Lago、Kill Bill、OpenMeter 和 Medusa 的公开模型与实现讨论：

- Lago 将 subscription、usage、coupon、prepaid credit 和 payment orchestration 放在同一商业链路，但把支付适配器与 Billing/Metering 逻辑分开；
- Kill Bill 把 catalog、subscription、invoice、payment、usage、entitlement 分成可替换模块，而不是让一个 Payment Service 直接发放权益；
- OpenMeter 明确区分 **usage subject** 与 **billing customer**，并支持多个 subject 归属于一个 customer；这正是 Kokoro 需要的 `billingSubject -> payer/account` 映射；
- Medusa 的公开讨论暴露了 promotion/payment 的 check-then-act 并发风险，说明 promotion budget、payment capture/refund 不能只靠应用层先查后写，必须使用数据库锁/版本/唯一约束。

因此本方案新增四个明确边界：

1. `billingSubject` 是产生用量的个人、项目或执行主体；`payer/account` 是真正承担积分/付款的 Billing 账户；两者不能用一个 `userId` 字段混淆；
2. Billing Order/Checkout、Payment Settlement、Invoice/Receipt、Entitlement Fulfillment 是不同事实。V1 只实现订单/checkout/settlement/receipt；税务发票和完整 invoice engine 作为后续 bounded module，不伪装成支付订单；
3. Promotion 的使用次数、预算和每 customer 限制必须在兑换/checkout 事务内原子占用；不能先读剩余次数再异步扣减；
4. Subscription 的购买、续期、升级、降级、取消、暂停、到期、proration 和 grant 发放必须是显式状态/事件；不能仅用 provider webhook 的一个 `paid` 布尔值表示完整订阅生命周期。

参考：[Lago](https://github.com/getlago/lago)、[Lago prepaid credit notes](https://github.com/getlago/lago/wiki/What-I-Wish-Someone-Told-Me-About-Prepaid-Credits)、
[Kill Bill](https://github.com/killbill/killbill)、[OpenMeter](https://github.com/openmeterio/openmeter)、
[OpenMeter subject/customer model](https://github.com/openmeterio/openmeter/blob/main/docs/migration-guides/2025-08-12-subject-customer-consolidation.md)、
[Medusa promotion/payment race discussion](https://github.com/medusajs/medusa/issues/16012)。

## 2. 角色与 API 面

| 角色 | API 面 | 可做 | 不可做 |
|---|---|---|---|
| User/Storefront | `/billing/*`、`/billing/me/*` | 查看已发布套餐、创建 checkout、查询自己的订单/账户、兑换可用 code | 发布价格、查看 code 库存、修改余额 |
| Admin/Operator | `/admin/billing/*` | 发布 immutable revision、配置 promotion/redeem campaign、授权 grant、发起退款、重试、对账 | 直接 UPDATE journal/balance、跨 tenant 操作 |
| Internal service | `/internal/billing/*` | admission/hold、accepted/release、settlement source fact、受控查询 | 使用用户凭证冒充 Admin、传入任意价格/金额 |
| Payment provider | `/webhooks/billing/{provider}` | 提交签名事件 | 选择租户、直接发放权益 |

四个 API 面必须分别认证、授权、限流、审计和错误映射。外部租户字段只有 `tenantId` / `X-Kokoro-Tenant-Id`；数据库的
`site_id` 是内部历史列，HTTP adapter 负责映射。Provider payload 中的 `tenantId` 或历史 `siteId` 只做一致性校验，
不能作为租户选择依据。

## 3. 核心用户旅程

### 3.1 浏览、购买与发放

```text
published package revision
  -> quote snapshot
  -> checkout intent (idempotent)
  -> provider payment
  -> signed webhook inbox (idempotent)
  -> settlement source fact
  -> acquisition + fulfillment
  -> entitlement/credit grant + journal + projection
```

要求：quote 固化价格、币种、权益和 revision；之后管理员改价不能重算已创建 checkout。支付 webhook 可重复、乱序、延迟；
只有 settlement 终态才能触发 fulfillment。Fulfillment 重试必须返回同一 grant/journal 结果。

### 3.2 模型调用扣费

```text
Authorize(invocationId, billingRef, subject, feature)
  -> fixed price snapshot + hold
  -> provider send
  -> Accepted receipt -> capture once
  -> confirmed rejection -> release once
  -> unknown -> retain hold until reconciliation
```

调用方不能传入 `amountMicros` 或 token 量决定用户价格。`invocationId` 是一次调用的幂等键，`billingRef`、`holdRef`、`priceRef`
均由 Billing 产生并只回传 opaque 值。

### 3.3 兑换与优惠

- Promotion Code 只改变 checkout price，不产生 Credit；一次兑换与 checkout 绑定并记录折扣快照。
- Entitlement Redeem Code 兑换后按 campaign revision 发放套餐周期、feature 或 credit grant。
- Gift/Prepaid Credit Code 是 redeem code 的一种 grant template，不另造“卡密余额”模型。
- Code 明文只在生成/导入时出现；数据库仅保存规范化 code 的 HMAC，日志、trace、outbox 和 metrics 不得出现明文。

### 3.4 退款、撤销与过期

退款先写 Payment reversal fact，再由 Entitlement 根据 acquisition/source ref 计算可撤销权益。已经消费的权益不能让账户
余额变成不受解释的负数；产生 `reversal_exposure`，交给 Admin/对账处理。过期、撤销、释放都追加事实，不删除历史 journal。

## 4. 状态机与不变量

### 4.1 状态机

```text
Checkout:     created -> pending -> paid | failed | expired
Settlement:   received -> applied | rejected | pending_reconcile
Fulfillment:  pending -> fulfilled | partially_reversed | reversed | blocked
Hold:         active -> captured | released | expired
Redeem code:  available -> redeemed | revoked | expired
Promotion:    draft -> published -> retired
```

状态只能沿允许的前向边迁移；重复命令返回首次结果，payload/key 不一致返回 conflict。

### 4.3 账户归属模型

```text
ExecutionIdentity.subject / billingSubject
  -> BillingCustomerBinding(tenant, subject_kind, subject_ref)
  -> PayerAccount(tenant, account_kind=personal|project|organization)
  -> CreditAccount / PaymentCustomer
```

同一个 tenant 内多个 subject 可以归属于同一个 payer；同一个 opaque subject 不能跨 tenant 复用。Billing API 接受
`billingSubject` 的窄投影和 Billing 签发的 `billingRef`，不接受 RuntimeNamespace、checkpoint key 或 caller 自选 account id。
Admin 可以查看 binding，但不能通过 API 任意把 subject 改绑到另一个 payer；改绑必须是有 reason 的审计命令，并规定对历史 grant、
hold 和未结算 usage 的归属策略。

### 4.2 必须始终成立

1. MySQL/InnoDB 是 payment、entitlement、credit 的最终事实源；余额是 projection，不是手工事实；
2. `gross = available + held = SUM(grant.remaining)`，不含已 capture/release 的额度；
3. 每个 hold 只能 capture 或 release 一次；每个 settlement/acquisition/fulfillment 来源只能成功发放一次；
4. journal、allocation、provider raw event、reversal 事实 append-only；
5. 所有跨租户引用包含 tenant lineage（当前物理实现为 `site_id` 复合外键）；
6. Redis 丢失、过期、重启时，业务结果仍由 MySQL receipt、唯一键、行锁和事务决定；Redis 只优化并发和延迟。

## 5. 设计模式与适用位置

| 模式 | Billing 中的落点 | 目的 |
|---|---|---|
| Modular Monolith | 一个 `kokoro-billing` repo，多个 context、多个 runtime process | 先保持事务与发布闭环，边界可演进 |
| Hexagonal / Ports & Adapters | Application ports；MySQL、Redis、Stripe、HTTP 为 adapters | 领域规则可单测，替换基础设施不改用例 |
| Aggregate + invariant | CreditAccount/Hold、Checkout、RedeemCode | 把余额、状态和单次消费约束放在 owner 内 |
| Application Service / Unit of Work | `CaptureUsage`、`AcceptSettlement`、`RedeemCode` | 编排授权、幂等、锁顺序、事务提交 |
| Repository | 按 aggregate/fact 定义窄接口 | 隐藏 SQL；禁止 GenericRepository<T> 和跨 context 直写 |
| Inbox/Outbox | provider inbox、payment/entitlement outbox | 外部事件至少一次投递，事务内记录、事务外发送 |
| Policy / Strategy | grant burn priority、promotion eligibility、provider adapter | 变化规则可替换，不能散落在 controller |
| Snapshot | quote、package revision、price revision、grant template revision | 历史购买不受未来配置修改影响 |
| Saga/compensation | settlement→fulfillment、refund→reversal | 跨 context/外部 provider 失败时可重试、可对账 |
| CQRS-lite | mutation facts 与 admin/read query 分离 | 不把报表查询塞进 aggregate；仍以 MySQL 为权威 |

## 6. SQL 与基础设施裁决

- 当前首发依赖固定为 MySQL 8.4 + Redis；不引入 PostgreSQL、Kafka、ClickHouse 作为 Billing 必需组件。
- 表名使用 `<owner>_<aggregate_or_fact>`：`entitlement_credit_grant` 合法，因为它是 Entitlement owner 下的 Credit Grant lot；
  `entitlement_entitlement_grant` 重复 owner，`credit_balance` 也不应替代 grant fact。
- 金额/积分使用带单位的 `BIGINT`（如 `amount_micros`、`credit_micros`），API 使用十进制字符串；时间为 UTC `DATETIME(6)`。
- MySQL transaction 内完成余额、hold、allocation、journal；Redis lock 失效不能导致错误业务结果。
- Redis 负责 idempotency hint、短 lease、rate limit、cache、worker coordination；绝不只依赖 Redis SETNX 判断“已扣费”。

## 7. Given/When/Then 验收基线

| 场景 | Given | When | Then |
|---|---|---|---|
| 重复 checkout | 相同 tenant + idempotency key 已成功 | 再次提交相同 payload | 返回同一 checkout，不新增 provider session |
| 幂等冲突 | key 已绑定不同 payload | 再次提交 | `billing.idempotency_conflict`，MySQL 事实不变 |
| 重复 webhook | provider event 已 processed | 再投递 raw event | 返回已处理结果，不重复 settlement/grant |
| 并发扣费 | 账户仅剩一份额度 | 两个 invocation 同时 authorize | 至多一个 hold 成功；结果不依赖 Redis 是否命中 |
| accepted 重放 | hold 已 captured | 重复提交同 invocation receipt | 返回 already_captured，不重复 journal |
| provider unknown | provider 结果未知 | 未收到终态 | hold 保持 active，可由 reconcile 决定 capture/release |
| 退款已消费 | grant 部分 consumed | Admin 发起退款 | 记录 reversal exposure，不直接篡改 balance |
| code 并发兑换 | 同一 code available | 两个用户同时 redeem | 一个成功，一个 conflict/invalid；只产生一份 grant |
| tenant 越权 | JWT tenant 与 header 不同 | 调用 User/Admin API | 400/403，不能读取或写入另一 tenant |
| Redis 故障 | Redis down/evicted | 执行幂等 mutation | MySQL receipt/unique key 仍保证正确结果；仅性能/限流降级 |

## 8. Edge case 与运营错误矩阵

| 类别 | 例子 | 处理 |
|---|---|---|
| 输入 | 空 code、未知字段、负数、错误 currency | 边界 schema 拒绝，统一 error code |
| 并发 | 同一 checkout/redeem/refund 双提交 | MySQL unique + row lock + receipt，返回首次结果 |
| 事件 | 重复、乱序、旧签名、未知 provider event | inbox 去重；验签失败拒绝；未知事件保留审计并可重试 |
| 账务 | grant 不足、hold 超时、退款超过可撤销额度 | 不静默修余额，形成 journal/reconcile drift |
| 配置 | 发布后修改 price/benefit | 新 revision；旧 quote/fulfillment 使用 snapshot |
| 依赖 | Redis/MySQL/provider 短暂不可用 | 事务不部分提交；worker 重试；MySQL 不可用时拒绝 mutation |
| 权限 | Admin 跨 tenant、User 查询他人订单、Internal 伪造 receipt | policy + tenant lineage + issuer binding + audit |

## 9. 完成定义与当前状态

### 9.1 方案完成定义

方案只有同时具备以下内容才算闭环：边界/owner、用户与 Admin 旅程、状态机、不变量、SQL 命名、基础设施职责、API schema、
错误码、幂等/并发策略、审计/对账、GWT 验收和实现状态矩阵。31/46/47/本文件与子仓 README 共同满足该文档门槛。

### 9.2 实现状态（必须诚实）

| 能力 | 当前状态 |
|---|---|
| MySQL + Redis V1 基础、Payment、Credit hold/settle/release、Admin/User API、OpenAPI parity | 已实现并有本地验证 |
| repo/service ports 全量迁移 | 计划中；当前仍有部分 service 直接持有 mysql2 connection |
| Package/Benefit 多表扩展、Promotion Code、Redeem Code | 目标方案已定，尚未实现 |
| Feature-first per-invocation contract | 目标方案已定，尚未实现 |
| 部署、旧 writer 停写、真实切流 | 未执行；不属于当前本地方案验收 |

实现完成必须逐项更新表格、migration、OpenAPI、测试和 closure evidence；不得以文档存在代替代码证据。

### 9.3 当前 V1 契约与目标契约的边界

历史 token/generic-usage 方案中的 `subjectId`、`quantityMicros` 和 generic usage routes 是过渡性 compatibility surface，
不能直接给 Feature-first GA 使用。目标 contract 必须在一个完整变更中冻结以下字段：

```text
AuthorizeModelInvocation:
  invocationId, billingRef, billingSubject(kind, opaqueRef), featureKey, requestedModelLabel?

ModelInvocationAccepted:
  invocationId, billingRef, holdRef, priceRef, billingSubject, featureKey,
  acceptedProviderRef, acceptedAt, gaReceiptId, authenticatedIssuer

ReleaseModelInvocationHold:
  invocationId, holdRef, reason, gaReceiptId, authenticatedIssuer
```

目标 contract 不接受 caller 传入账户 ID、最终金额、token 数量或 RuntimeNamespace；目标 migration 必须新增
`billing_customer_binding`/等价事实和 invocation binding，目标 API parity、GA caller、MySQL migration、integration test
必须同一切片落地。旧 `subjectId` route 在迁移完成前保留为 legacy，不得被文档描述为 GA contract。

## 10. 实施顺序

1. 先落地 Repository ports、Unit of Work 与 architecture import tests；
2. 迁移 Credit mutation vertical slice，保持当前 API 行为；
3. 冻结并实现 Package/Benefit/Promotion/Redeem 的 schema + contract + service + integration tests；
4. 迁移 Payment repositories，并通过 settlement/reversal ACL 连接 Entitlement；
5. 实现 Feature-first invocation contract，再进行独立的部署/切流评审。

## 11. 评审结论

当前可信结论是：`kokoro-billing` 的 **V1 本地实现闭环、目标架构和扩展方案已分层记录**；它还不是“所有未来能力都已经实现”，
也不是“已上线”。后续每个能力以本文件的验收条目为实现门禁。
