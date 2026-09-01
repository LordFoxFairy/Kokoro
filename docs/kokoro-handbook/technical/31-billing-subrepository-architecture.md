# Kokoro Billing 子仓库重规划

> 历史讨论稿。当前 clean-build 唯一方案见 [50-billing-commerce-rearchitecture.md](50-billing-commerce-rearchitecture.md)；本文不定义兼容、迁移或实现边界。

状态：新的目标架构，2026-08-22。

## 1. 决策摘要

现有 `kokoro-payment` 与 `kokoro-credit` 收敛到一个新的业务子仓库：`kokoro-billing`。

合并的是代码仓库、版本发布、迁移工程和跨域业务闭环；**不合并 Payment 与 Entitlement/Credit 的
数据 owner 和事务边界**。仓库内部保留两个 bounded context：

```text
Payment Context     = provider money facts / checkout / settlement / reversal
Entitlement Context = catalog / fulfillment / subscription term / credit grant / metering / journal
```

根仓 PRD-03/04 与 canonical data model 已经明确：Payment 是 acquisition adapter，Entitlement 是购买
后的 Fulfillment/Credit authority。两者可由同一仓库的 `billing-api`/`billing-worker` 发布，但不能出现
一个万能 `BillingRepository` 或 Payment 直接写 Credit 表。

旧仓库进入迁移态：

```text
kokoro-payment  ─┐
                 ├─> kokoro-billing
kokoro-credit   ─┘
```

迁移完成后，旧仓库不再作为业务 runtime writer；Payment 与 Credit 的历史设计卡保留为迁移记录，
本文件成为目标架构的权威方案。

## 2.1 当前交付边界

当前子仓库按“实现闭环”验收，而不是按部署验收：SQL migrations、MySQL source facts、Redis 协调、User/Internal/Admin/Webhook
API、OpenAPI 契约、payment worker、credit sweeper、reconcile、审计与重放均属于本仓库实现范围；Docker/Kubernetes
部署编排、真实旧库导入、旧 writer 停写和 operator sign-off 属于后续切流门禁，不混入本地设计完成度。

因此“仓库实现完成”只表示目标路径可独立运行并可验证，不表示线上切流已经发生。旧 writer 的逐文件清单和切流条件见
[`billing-old-writer-inventory.md`](billing-old-writer-inventory.md) 与 [`billing-legacy-cutover-runbook.md`](billing-legacy-cutover-runbook.md)。

## 2. 为什么必须合并

套餐支付、订阅续费、订单退款、权益发放、积分 grant、积分消耗和对账构成一条商业账务链路。
现在 Payment 通过 HTTP 调用 Credit：

```text
Payment order -> payment settlement fact -> Entitlement fulfillment -> CreditGrant
Payment refund -> payment reversal fact -> Entitlement fulfillment reversal -> CreditJournal
```

这会造成：

- 支付已成功但权益发放失败，需要跨仓补偿；
- 退款状态与积分逆向分录需要两套重试状态机；
- 套餐的积分额度、来源、过期时间、优先消耗规则无法和购买事实同一事务编排；
- Credit 的总余额模型无法表达购买积分、赠送积分、订阅周期积分和过期积分的来源差异；
- 两个仓库分别维护 SQL/Prisma/schema/contract，最终对账跨越多个 owner。

成熟 AI billing 产品通常把 metering、limits、prepaid credits、cost tracking 放在同一 billing
体系中；支付 provider 仍是独立 adapter，但购买、权益、钱包和账本由同一个 billing owner 收敛。

## 3. 新子仓库边界

套餐 benefit、多类型权益、Promotion/Coupon 和 Redeem Code 的目标扩展不拆出新仓库，继续归属 Entitlement Context；
详细模型、卡密安全、状态机、API 与实施顺序见
[46-billing-package-credit-redeem-architecture.md](46-billing-package-credit-redeem-architecture.md)。

### Entitlement Context 拥有

- Offer/immutable offer revision、Acquisition、Fulfillment；V1 将套餐价格与 benefit 快照收敛在 revision，待真实需求出现再拆分 product/price/benefit 表；
- SubscriptionTerm、EntitlementGrant；
- CreditAccount、CreditGrant、CreditHold、HoldAllocation、CreditJournal；
- UsagePriceRevision、UsageEvent、AuthorizeUsage、SettleUsage；
- 来源级 revoke/reversal、outbox、audit、reconciliation。

### Payment Context 拥有

- checkout intent、provider account、provider event inbox；
- payment settlement、provider subscription/period、refund/dispute reversal；
- Payment command receipt、payment outbox 和 provider reconciliation。

Payment 通过 stable `PaymentSettlement`/`PaymentReversal` contract 触发 Entitlement 的
`AcceptPayment`/`ReverseFulfillment`，不直接写 `entitlement_credit_*`、`entitlement_subscription_term` 或
`entitlement_credit_grant`。

### 不拥有

- IAM、用户、Team、Site、组织关系和登录会话；
- Model catalog、模型 provider 路由和模型健康检查；
- Agent/Session 执行状态与对话数据；
- Stripe/支付宝/微信的密钥明文；只保存 secret reference；
- 外部支付机构的最终结算事实；Billing 保存 provider event 与本地订单映射。

## 4. 目录与运行时

```text
kokoro-billing/
├── src/
│   ├── modules/
│   │   ├── catalog/          offer、immutable revision、admin publish
│   │   ├── credit/           account、grant、hold、allocation、journal
│   │   ├── metering/         usage event、price revision、authorize、settle
│   │   ├── payment/          provider、checkout、settlement、reversal
│   │   ├── admin/            tenant-scoped stats and operations
│   │   └── reconcile/        projection、payment、provider drift
│   ├── infrastructure/
│   │   ├── mysql/            mysql2、transaction、repositories
│   │   ├── redis/            idempotency fast-path、lease、rate coordination
│   │   └── providers/        stripe/alipay/wechat/mock adapters
│   ├── interfaces/http/      public、internal、admin、webhook routes
│   ├── main.ts               billing-api entrypoint
│   └── README.md             implementation notes
├── scripts/                  migration、worker、import、audit entrypoints
├── database/
│   ├── migrations/0001-*.sql
│   └── README.md
├── contract/
│   └── openapi/billing-v1.yaml
└── docs/
```

V1 的 canonical transport 是 OpenAPI HTTP；只有平台实际采用内部 RPC 时，才新增并生成 Protobuf contract，
不为尚不存在的 transport 预留空目录或虚构 generated snapshot。migration、worker、reconcile 入口位于仓库根部
`scripts/`，与实际子仓库布局保持一致。

## 5. 端到端业务链路

### 购买套餐

```text
GET plans
  -> POST checkout
  -> payment provider
  -> signed webhook + provider event idempotency
  -> payment settlement fact
  -> entitlement acquisition(source=payment settlement)
  -> fulfillment transaction
  -> entitlement grant + credit grant lot
  -> credit journal + balance projection
```

### AI 请求计费

```text
IAM/Session admits ExecutionIdentity.subject
  -> Billing creates or validates billing_ref(subject, tenant, Feature)

each GA ModelInvocation(invocation_id, cost_policy=separate)
  -> Billing AuthorizeModelInvocation(billing_ref, billing_subject, feature, model label)
  -> fixed per-invocation price + hold_ref
  -> GA model execution
  -> provider accepts invocation_id
  -> GA durable ModelInvocationAccepted(billing_subject, billing_ref, hold_ref, GA service receipt)
  -> Billing validates receipt and captures usage(invocation_id)
  -> consume CreditGrant by priority/expiry
  -> usage settlement + CreditJournal + audit

provider rejects invocation_id
  -> GA durable release(hold_ref) -> Billing idempotent hold release

provider result unknown
  -> keep hold_ref -> reconcile provider -> capture once or release once
```

这里的产品单位是 provider 接受的 `ModelInvocation` 次数；token 仅为 provider 成本、预算和诊断。`billing_subject` 是
`ExecutionIdentity.subject` 的窄投影，Billing 依此选择个人或项目 payer；它不是 GA `RuntimeNamespace`。`billing_ref` 是 Billing
在 Session admission 签发的 opaque 账务上下文；它绑定 subject、tenant 和 Feature，但不是账户 ID 或一次 provider 调用的 hold。
`hold_ref` 才是 Billing 对一个 `invocation_id` 建立的 reservation。GA durable usage receipt 可延迟重放，因此 Billing 依赖
`invocation_id`、`hold_ref`、GA service identity 和既有 binding 幂等结算，不依赖一张会过期的动态工具 attestation。

#### Model invocation metering contract

`ModelInvocation` 是 GA ledger 的执行事实；Billing 只拥有它的可计费镜像与钱包 mutation。两边不共享 repository、数据库或
checkpoint，但使用相同的 `invocation_id` 作为一次调用的唯一业务键：

```text
AuthorizeModelInvocation (GA -> Billing, synchronous before provider send)
  invocation_id / billing_ref / billing_subject(kind, opaque_ref)
  feature_key / requested_model_label? / GA service identity
  -> hold_ref / price_ref / amount_micros

ModelInvocationAccepted (GA -> Billing, durable outbox after provider acceptance)
  invocation_id / billing_ref / hold_ref / billing_subject
  feature_key / price_ref / accepted_provider_ref / accepted_at / GA receipt
  -> captured | already_captured

ReleaseModelInvocationHold (GA -> Billing, durable outbox after confirmed rejection)
  invocation_id / hold_ref / reason=rejected | reconciliation_not_accepted / GA receipt
  -> released | already_released
```

Billing 的 target `UsagePriceRate` 使用 `meter_kind=model_invocation` 与 `invocation_micros`，可按 `feature_key` 与受控模型标签
区分价格；它不接收 input/output token 数量来决定用户价格。`billing_subject` 采用 `kind + opaque_ref` 两个业务字段，
并以 `(tenant_id, subject_kind, subject_ref)` 定位 Billing payer，不能把 project 与 personal 同名 opaque ref 混为同一账户。
`billing_ref`、`hold_ref`、`price_ref` 都是 Billing-owned opaque refs，GA 只保存并回传，不解析/拼接它们。

`zero_rated` 与 Studio Job `included` reasoning 不调用 Authorize/Accepted/Release 这条模型调用结算链；`separate` 才需要完整链。
每一个实际模型发送（entry、private task、Swarm peer、summary）各有一个 invocation key；Feature 的
`max_model_invocations` 同时限定 GA slot 和一条 Run 最多可以建立的 Billing holds。

#### 从现有 token 计量面切换的硬门

当前 `kokoro-billing` OpenAPI、`UsageSettlementService` 与 MySQL rate 列仍是 **V1 token 计量物理基线**。它们可以继续处理
尚未切换的旧调用，但新 Feature-first GA 绝不向 `usage/events` 提交自由 `subjectId`、token 数量或任意 `amountMicros`。目标切换采用
expand → dual-read verification → cutover → contract delete：

1. Billing 新增 typed `subject_kind + subject_ref`、`billing_ref` admission record、per-invocation `hold_ref` 和 `(tenant_id, invocation_id)`
   唯一 usage fact；账户/hold/usage/settlement 以该三元 subject key 关联。
2. 新增 `meter_kind=model_invocation` 的 fixed `invocation_micros` price rate；新 `AuthorizeModelInvocation` 不接受 input/output token
   或调用方传入价格。token 可作为 provider-cost diagnostics 另存，但不进入 hold/capture 计算。
3. 新 Internal Metering contract 同时提供 authorize、accepted capture 与 rejected release，三者均验证 GA workload identity、
   `billing_ref`/`hold_ref` binding 和 idempotent `invocation_id`；GA 只调用这组新入口。
4. `unknown` provider result 的 hold 进入 reconciliation_pending，不被普通 hold expiry job 自动释放；仅 provider evidence 或人工受权
   reconciliation 可以 terminal capture/release。
5. 对每个 Feature 做 shadow：比较旧 token quote 与新调用次 price 的**观测差异**，不写第二笔用户扣账；验证通过后新 GA caller
   enforce 新入口，再删除 GA 到旧 token usage endpoint 的 client/permission。旧 endpoint 在最后 legacy caller drain 后移除。

门禁至少覆盖：个人与项目同 opaque ref 不串账、授权拒绝不发送 provider、accepted capture 只一次、rejected release 只一次、unknown
不重发/不自动释放、outbox 重放无双扣、`included/zero_rated` 无 reasoning 二次扣费、Run 内每个模型发送都不超过
`max_model_invocations` 与其对应 hold 上限。

### 退款

```text
refund request
  -> provider refund event / local refund state
  -> entitlement revoke or compensating CreditJournal entry
  -> refund ledger + audit
  -> order/refund terminal state
```

支付成功事实与权益到账状态分开建模：`payment_settlement=succeeded` 不等于
`entitlement_fulfillment=committed`。权益授予由 outbox 可重试，最终必须有
`committed / pending / failed / reversed / reconciliation_required` 明确状态。

## 6. 技术栈

| 层 | 选择 | 规则 |
|---|---|---|
| Runtime | Node.js 22 LTS | `engines >=22 <25` |
| Language | TypeScript strict | domain 不依赖 HTTP、SQL client、provider SDK |
| Package | pnpm workspace | lockfile 必须提交，CI `--frozen-lockfile` |
| HTTP | Fastify + Zod/JSON Schema | public/internal/admin route access 分层 |
| DB | MySQL 8.4 + InnoDB | SQL-first，`mysql2/promise` pool；每个 application transaction 独占一个物理 session，不使用 Prisma 作为业务 owner |
| Cache/coordination | Redis 7+ | lease、短期幂等快路径、限流协调；不是真实余额来源 |
| Contract | OpenAPI | HTTP canonical contract；内部 RPC 采用后再新增 Protobuf，不预先造 transport |
| Tests | Vitest + real MySQL/Redis integration | 禁止只用 mock 宣称账务完成 |
| Observability | Prometheus metrics + structured logs + audit events | requestId、provider event id、order id 全链路贯通 |
| Delivery | Docker、GitHub Actions | 本仓库提供 image、CI、migration/worker compiled entrypoints；Kubernetes/Kustomize 编排由平台部署仓库负责，不在子仓库虚构 manifests |

Redis 与 MySQL 都是正式运行依赖：Redis 负责协调和快速拒绝，MySQL 负责 Payment/Entitlement 各自的
事实、CreditJournal、Fulfillment 和最终幂等事实；两个 context 共享数据库实例但不共享 repository 和
写权限。Redis 故障可以降级为 MySQL 路径；MySQL 不可用时禁止 mutation。

成熟方案复用边界见 [`32-billing-mature-systems-research.md`](32-billing-mature-systems-research.md)：
不复制 LiteLLM 的 provider cost calculation，不直接搬入 OpenMeter/Lago 的异构基础设施，只采用其
已经验证的 usage event、entitlement、grant priority/expiration、credit transaction 和 outbox 语义。

Provider inbox/outbox、worker 状态机、重放和上线门禁见
[`billing-event-processing.md`](billing-event-processing.md)。

## 7. 数据 owner

`kokoro-billing` 是以下 `payment_*`/`entitlement_*` 表的唯一 runtime writer。其他仓库只能调用契约，
不得 import repository、Prisma client 或直接写表。Payment 与 Entitlement 各自拥有自己的表集合和
application port。

```text
entitlement_offer
entitlement_offer_revision
entitlement_acquisition
entitlement_fulfillment
entitlement_fulfillment_reversal
entitlement_subscription_term
entitlement_credit_account
entitlement_credit_grant
entitlement_credit_hold
entitlement_credit_hold_allocation
entitlement_credit_journal
entitlement_usage_price_revision
entitlement_usage_price_rate
entitlement_usage_settlement
entitlement_usage_event              # target: meter_kind=model_invocation, invocation_id and subject_kind/ref
entitlement_command_receipt
entitlement_audit_event
entitlement_outbox
payment_provider_account
payment_command_receipt
payment_customer_binding
payment_checkout
payment_provider_event
payment_settlement
payment_provider_subscription
payment_subscription_period
payment_reversal
payment_outbox
```

## 8. 一致性决策

- Checkout/provider event/payment settlement/Acquisition/Fulfillment/Credit mutation 都使用业务幂等键和 request fingerprint。
- 同仓不等于所有步骤共用一个长事务；provider webhook 只在 MySQL 内落事件和 outbox，worker 执行
  钱包授予，避免把外部网络调用放入数据库事务。
- CreditGrant 记录 `source_kind/source_ref`、`original_micros`、`remaining_micros`、`expires_at`、
  `priority`；消耗按优先级和最早过期优先，并留下 allocation 明细。
- CreditJournal append-only；余额 projection 只由 Entitlement/Credit application 更新；reconcile 比较 projection、
  grant allocation、ledger 和 hold allocation。
- 模型调用结算的唯一业务键是 `(tenant_id, invocation_id)`；`ModelInvocationAccepted` 与 release outbox 可以任意重放，
  但同一 hold 只能 capture 或 release 其一。`unknown` 在 provider reconciliation 结束前保持 hold，不能由普通 expiry sweeper 猜测释放。
- target metering price 只接受 `meter_kind=model_invocation` 的 fixed `invocation_micros`；provider token/cost 是诊断事实，
  不进入 CreditPrice/hold/capture 的用户价格计算。
- Billing subject 以 `(tenant_id, subject_kind, subject_ref)` 定位，`billing_ref` 绑定 admission subject/Feature，`hold_ref` 绑定单一
  invocation；GA 不提交 accountId、直接 subjectId 或 RuntimeNamespace 选择 payer。
- provider event 是 inbox：先唯一落库，再异步处理；重复 webhook 只能返回既有处理结果。

## 9. API 面隔离

Billing 不是“所有调用方共享一套 API”。用户、内部服务、Admin、Provider Webhook 是四个独立边界，
分别定义认证、授权、输入输出和审计：

```text
Web BFF      -> User/Storefront API      -> IAM RS256/JWKS session + tenant_id match
Model/Agent  -> Internal Metering API    -> GA service identity + subject-bound usage receipt + billing_ref binding
PlatformAdmin-> Admin API                -> operator proxy secret + RBAC + reason
Provider     -> Webhook Inbox API        -> signature + provider event id
```

用户端不接触 `grant/refund/reconcile/outbox replay`；内部服务不获得 Admin 能力；Provider webhook 不
直接写 credit account。所有高权限操作最终经过 Billing application command 并写 audit event。
