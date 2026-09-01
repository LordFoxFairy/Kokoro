# Payment/Credit → Billing 迁移映射

> 迁移对象：`kokoro-payment`、`kokoro-credit`。两者保留为历史实现与回滚参考；新能力进入 `kokoro-billing`，不在旧仓库继续扩张。
>
> **范围注记：**本文已有的 `RecordUsageEvent / AuthorizeUsage / SettleUsage` 是当前 Billing V1 token/generic-usage
> 物理迁移路径。Feature-first GA 的按 provider-accepted `ModelInvocation` 次数扣积分是下一阶段、独立 contract migration；
> 它不能复用 V1 的自由 `subjectId`、token 数量或 `amountMicros` 写入口。

## 1. 代码与职责映射

| 旧仓库 | 旧概念 | Billing 目标 | 迁移规则 |
|---|---|---|---|
| `kokoro-payment` | Plan / price | `entitlement_offer` + immutable `entitlement_offer_revision` | V1 将套餐的金额、币种、credit 和 billing interval 冻结在 revision；Payment 只引用 revision，不提前引入未落地的 product/price/benefit 拆表 |
| `kokoro-payment` | Provider config | `payment_provider_account` | provider account 绑定 tenant；新 webhook 不从任意 payload tenantId/siteId 授权租户，历史 siteId 仅做一致性校验 |
| `kokoro-payment` | Order | `payment_checkout` + `payment_settlement` | order 不再同时承担 provider attempt、履约和积分发放 |
| `kokoro-payment` | PaymentEvent | `payment_provider_event` | 先 inbox，再产生 settlement/reversal |
| `kokoro-payment` | Subscription | `payment_provider_subscription` + `payment_subscription_period` + Entitlement `subscription_term` | provider 周期事实与用户权益周期分离 |
| `kokoro-payment` | Refund | `payment_reversal` | reversal 通过 source fact 触发 fulfillment reversal |
| `kokoro-credit` | account/balance | `entitlement_credit_account` | balance 是 projection，不是唯一账本 |
| `kokoro-credit` | grant | `entitlement_credit_grant` | 每次购买/兑换/补偿都是独立 grant lot |
| `kokoro-credit` | ledger/transaction | `entitlement_credit_journal` | append-only；所有扣减必须落 journal |
| `kokoro-credit` | hold | `entitlement_credit_hold` + allocation | 预授权与结算分离，支持未知 committed exposure |
| `kokoro-credit` | usage | `entitlement_usage_event` + `entitlement_usage_settlement` | 观测事件不直接扣账；settle 才 capture/release |

## 2. 现有实现的边界修正

旧 Credit 的 `recordUsage()` 语义不能作为最终扣账入口：它应只承载 usage observation，不能把状态标为 settled 后又不写 debit journal。
**对 V1 legacy caller**，Billing 先拆为：

1. `RecordUsageEvent`：保存原始/规范化用量，source event 唯一。
2. `AuthorizeUsage`：按 grant burn order 建立 hold 与 allocation，并冻结 price revision。
3. `SettleUsage`：按实际用量 capture/release allocation，写 journal，更新可重建 projection。

**对 Feature-first GA target**，替换的不是上述 API 名，而是整个计费单位和 trust boundary：

1. `AuthorizeModelInvocation(invocationId, billingRef, billingSubject, featureKey)`：Billing 以固定每调用价格创建绑定唯一
   `holdRef`，授权失败时 GA 不发送 provider；
2. `ModelInvocationAccepted`：GA 只在 provider 接受后，以 durable outbox 写 `invocationId + holdRef + priceRef + GA receipt`；
3. `ReleaseModelInvocationHold`：明确 rejected 或 reconciliation-not-accepted 才释放同一 hold；unknown 保持 pending；
4. 价格使用 `meter_kind=model_invocation` / `invocation_micros`；token 仅记录成本、预算、诊断，不决定用户价格。

`billingRef` 必须绑定 tenant + subject(kind/ref) + Feature；`RuntimeNamespace`、actor、短时 attestation 和调用方裸
`amountMicros` 都不是 Billing payer/price 输入。

旧 Payment 的“confirm order → 直接 HTTP grant → mark paid”改成：

1. provider event inbox；
2. payment settlement stable fact；
3. outbox 投递 `AcceptPaymentSettlement`；
4. Entitlement 生成 acquisition、fulfillment、credit grant、journal；
5. provider 查询/对账与业务重试均以 source fact 幂等。

## 3. 迁移顺序

1. 先建立 `kokoro-billing` 的 catalog、account、grant、journal、receipt、outbox 基础模型。
2. 迁移 Credit 的只读 projection 与 grant 数据，校验 journal 重放后的余额。
3. legacy Model/Agent caller 先切换至 V1 `AuthorizeUsage`/`SettleUsage` internal API。
4. 另行 expand GA target schema/OpenAPI：typed subject、BillingAdmission、per-invocation hold、ModelInvocation receipt；先 shadow
   观察、不二次扣账，随后只让 Feature-first GA 使用 `AuthorizeModelInvocation / Accepted / Release`，最后删除它到 V1 token usage route 的权限。
5. 接入 Payment provider inbox、settlement、reversal，不改变外部支付 provider。
6. 将旧 Payment 的购买成功改为 settlement → fulfillment；完成双读、对账和回滚窗口后停止旧路径写入。
7. 完成 admin reconciliation、refund、subscription period 等 V1 运营能力；dispute/chargeback 与 redemption
   作为后续独立领域扩展，不在本次切流中制造未定义的伪模型。

## 4. 验收门槛

- 旧新余额按 account/grant/journal 三层对账一致。
- 同一 purchase、refund、usage、webhook 重放不会生成重复事实。
- Payment 故障不会让 Credit 出现半笔 grant；Credit 故障不会让 Payment settlement 丢失。
- Redis 清空、重复投递、worker 崩溃、provider unknown 后，MySQL source facts 可恢复完整状态。

## 5. 当前实现证据

目标仓库已经建立可独立验证的 **V1 Payment/Credit 与 generic metering** 实现闭环：

- `kokoro-billing/src/modules/credit/allocate-grants.ts`：稳定 grant burn order 与不足余额错误；
- `kokoro-billing/database/migrations/0001-billing-core.sql`：Payment/Entitlement/Credit 核心表；
- `kokoro-billing/scripts/apply-migrations.ts`：编号 migration、checksum 和事务提交；
- `kokoro-billing/src/infrastructure/redis/idempotency-hint.ts`：Redis claim/replay/conflict 快速路径；
- `kokoro-billing/src/modules/payment/billing-settlement-service.ts`：Payment settlement → Acquisition →
  Fulfillment → CreditGrant → CreditJournal 的同库事务切片；重复调用和并发调用均按 source fact 幂等；
- `kokoro-billing/src/modules/payment/provider-event-inbox-service.ts`：provider signature gate、raw payload inbox、
  provider + external event id 唯一重放，并在同一事务写入 `PaymentProviderEventReceived` outbox；
- `kokoro-billing/database/migrations/0002-payment-fulfillment.sql`：acquisition、fulfillment、payment outbox 表；
- `kokoro-billing/src/modules/payment/billing-reversal-service.ts` 与 `0003-reversal.sql`：未消费 grant 的
  source-specific reversal；余额不足保留为 reconciliation exposure，不静默制造负余额；
- `kokoro-billing/src/modules/metering/usage-settlement-service.ts`：RecordUsageEvent → AuthorizeUsage（hold +
  grant allocation）→ SettleUsage（capture/release + journal + outbox）；Redis 不参与最终扣账；
- `kokoro-billing/src/infrastructure/mysql/outbox-worker.ts` 与 `0005-outbox-leases.sql`：MySQL
  `SKIP LOCKED` + lease claim + publish mark，至少一次投递；
- `kokoro-billing/src/modules/credit/admin-grant-service.ts`、`account-query-service.ts` 与 `0006-admin-audit.sql`、
  `0009-credit-account-quota.sql`：Admin 手工 grant、operator/reason audit、User 账户查询，以及 target
  summary/ledger/by-model 读面；
- `kokoro-billing/src/infrastructure/providers/hmac-signature-verifier.ts`：timestamped HMAC provider 验签，
  raw body 在 JSON parse 前保留；
- `kokoro-billing/src/modules/reconcile/reconciliation-service.ts`：projection/grant/journal 对账与未履约
  settlement 漂移报告；
- `kokoro-billing/src/modules/payment/billing-reversal-service.ts` + Admin refund route：退款 source fact、
  reversal journal 和 operator audit；
- `kokoro-billing/database/migrations/0010-payment-subscriptions.sql`：provider account/customer binding、
  subscription 与 period 稳定事实，避免把周期状态塞进 checkout/order；
- `kokoro-billing/database/migrations/0011-provider-event-payload-hash.sql`：冻结 provider webhook payload hash，
  同一 external event id 携带不同 payload 时返回幂等冲突；
- `kokoro-billing/database/migrations/0012-payment-outbox-source-unique.sql`：同一 settlement source 的逻辑事件
  只允许一条 payment outbox，防止 command replay 重复发布；
- `kokoro-billing/database/migrations/0013-credit-available-semantics.sql`：明确 `available_micros` 为扣除
  active hold 后的可用余额，允许账户全部额度处于 hold，并修正对账公式；
- `kokoro-billing/database/migrations/0014-provider-event-processing-state.sql`：记录 provider event 的处理尝试与
  最后错误，支持 worker 失败重试和运营重放；
- `kokoro-billing/src/modules/payment/provider-event-processor.ts`、`src/modules/credit/subscription-grant-service.ts`：
  worker 处理 payment success、refund、subscription period，并按 source fact 幂等发放周期积分；
- `kokoro-billing/database/migrations/0015-entitlement-subscription-term.sql`：将 payment provider period 与
  Entitlement 用户权益周期分开建模，避免只记录支付订阅而没有权益状态事实；
- `kokoro-billing/database/migrations/0016-payment-checkout-provider-session.sql`、`0017-payment-command-receipt.sql` 与官方 Stripe SDK adapter：将 hosted checkout session 作为 Payment fact 关联到 checkout；外部 session 创建使用 Stripe idempotency key，本地无 provider 时 fail-closed；
- `kokoro-billing/database/migrations/0018-outbox-dead-letter.sql`：为 Payment/Entitlement outbox 增加有限重试后的
  `dead_lettered_at`，避免 poison event 无限占用 worker；Admin provider-event retry 会清除该标记并重新排队；
- `kokoro-billing/database/migrations/0019-provider-scoped-payment-refs.sql`：将支付/退款外部引用纳入 provider namespace，
  以 `(site_id, provider, external_*_ref)` 保证跨渠道订单号复用时仍不发生错误冲突；
- `kokoro-billing/database/migrations/0020-payment-settlement-provider-index.sql`：为 provider + checkout 的成功结算查询增加复合索引，
  退款事件只在同一 provider namespace 内选择 settlement；
- `kokoro-billing/database/migrations/0021-provider-scoped-subscription-refs.sql`：为订阅外部引用补齐 provider namespace，避免不同渠道复用同一订阅号时发生唯一键冲突；
- `kokoro-billing/database/migrations/0022-provider-account-global-identity.sql`：为 provider account 建立全局外部身份唯一约束，webhook 按 provider account 映射 tenant；
- `kokoro-billing/database/migrations/0023-provider-account-checkout-facts.sql`：持久化 checkout 选择的 provider account 与 webhook 观察到的 account，防止支付回调跨 account 履约；
- `kokoro-billing/database/migrations/0024-tenant-id-width.sql`：将内部兼容列 `site_id` 扩展为与 IAM opaque `tenantId` 对齐的 `VARCHAR(191)`，避免把租户错误限制为 UUID；
- `kokoro-billing/database/migrations/0025-subscription-period-tenant-lineage.sql`：为 subscription period 补齐独立 `site_id` lineage，并从 provider subscription 回填；
- `kokoro-billing/database/migrations/0026-hold-allocation-tenant-lineage.sql`：为 hold allocation 补齐 `site_id` 和复合外键，数据库层阻止跨租户 hold/grant 关联；
- `kokoro-billing/database/migrations/0027-tenant-composite-foreign-keys.sql`：为所有 tenant-owned relation 补齐 `(site_id, id)` 复合唯一键与复合外键，数据库层阻止跨租户 account、grant、hold、journal、fulfillment、payment 和 subscription 关联；
- `kokoro-billing/database/migrations/0028-tenant-composite-reference-completion.sql`：补齐 customer binding、subscription term/period 等后续 payment-entitlement 关系的 tenant composite FK；
- `kokoro-billing/database/migrations/0029-checkout-offer-revision-lineage.sql`：补齐 checkout → offer revision 的 tenant composite FK，禁止 checkout 跨租户引用套餐版本；
- `kokoro-billing/src/modules/payment/providers/`：复用旧 Payment 已验证的 Stripe/Alipay/WeChat provider
  adapter、raw-body 验签、事件归一化和 fail-closed registry，不重新发明 provider 协议；
- `kokoro-billing/src/infrastructure/mysql/connection.ts`：应用使用 MySQL pool，每个 HTTP/worker transaction
  通过 context 绑定独立物理 session；migration runner 使用专用连接维持 `GET_LOCK`；
- `kokoro-billing/src/modules/admin/admin-stats-service.ts` 与 `/admin/billing/stats`：提供 site-scoped、按币种拆分的
  只读运营聚合，不把跨币种金额压成一个总数；
- `kokoro-billing/.github/workflows/ci.yml`：冻结 lockfile、MySQL/Redis 真实依赖、migration、build 和 test gates；
- `kokoro-billing/test/unit/`、`test/integration/`：单测与真实 MySQL/Redis 验证。

这证明的是 Billing V1 核心链路、User/Internal/Admin API 与基础设施切片已经可运行；它不等于旧 writer
已经切换，**也不等于 Feature-first GA 的按调用次数 contract 已实现**。后者须同时落地 target OpenAPI、MySQL migration、
GA caller 与 provider-accepted/reconciliation integration tests。旧 writer 停写、真实环境观察窗口和 operator sign-off 仍按本映射的迁移门禁推进。
