# Billing Provider Event Processing

状态：目标实现门禁，2026-08-22。

## 1. 结论

Webhook HTTP 入口只负责验签、保存原始事件和写入 `payment_outbox`，不在请求线程中直接
发放积分。真正的支付闭环由 `billing-worker` 消费 `PaymentProviderEventReceived` 完成：

```text
provider webhook
  -> payment_provider_event (inbox, unique site/provider/external_event_id)
  -> payment_outbox (PaymentProviderEventReceived)
  -> billing-worker (MySQL row lease on a separate lease session)
  -> payment settlement / reversal / subscription period
  -> entitlement fulfillment / credit journal
```

这条边界继承成熟支付系统的 inbox/outbox、可重放和状态机做法，避免把外部 provider 网络调用
放进 MySQL 事务，也避免 webhook 超时导致「钱已到、权益未到」不可观察。

## 2. 事件处理契约

| 事件 | 处理器 | 成功事实 | 失败策略 |
|---|---|---|---|
| `payment_succeeded` | `PaymentSettlementProcessor` | `payment_settlement=succeeded`，随后 fulfillment | 可重试；金额、币种、checkout 快照不一致进入 `failed` |
| `refund_succeeded` | `PaymentReversalProcessor` | `payment_reversal=succeeded`，随后 reversal journal | 可重试；余额暴露进入 `reconciliation_required`，禁止静默扣负数 |
| `subscription_updated` | `SubscriptionPeriodProcessor` | provider subscription + period 唯一落库 | 缺少 subject/offer/period 映射进入 `failed`，不得猜测发放 |
| 未订阅事件 | `UnknownEventProcessor` | `processing_status=ignored` | 记录 event type 和 metrics；不得丢弃原始 payload |

所有处理器必须满足：

1. 以 `(site_id, provider, external_event_id)` 作为事件幂等键；
2. 以 `source_kind + source_ref` 作为 payment/entitlement 事实幂等键；
3. 先写 source fact，再执行 fulfillment/reversal；重试只重放 application command；
4. 任何跨 context 调用只能使用 application port，不能直接写对方表；
5. 终态只有 `processed`、`ignored`、`failed`。`failed` 必须保留错误码、attempts 和人工重放入口；outbox
   使用有限重试预算，超过预算写入 `dead_lettered_at`，不会无限占用 worker。

## 3. Worker 运行模型

`process-payment-events.ts` 是独立的 long-running worker 入口；默认在队列为空时按轮询间隔等待，`ONCE=true`
用于迁移/测试的一次性运行。`OutboxWorker` 使用 MySQL `FOR UPDATE SKIP LOCKED` 抢占单条 outbox，并通过
`lease_token/lease_until` 防止 worker 崩溃后永久卡死。Payment worker 不使用进程级 Redis 全局锁，允许多个实例
并行消费；Redis 只用于 API 幂等快速提示和 Credit hold sweeper 的 leader lease。这样 Redis 故障时仍可由
MySQL 多实例抢占继续处理，不能把 Redis 当作账务锁或余额来源。

Billing API、payment worker 和 credit sweeper 均暴露平台统一的 `/metrics` Prometheus 端点；API 包含进程指标、HTTP
请求总量和请求耗时，worker 包含处理结果、dead-letter、lease-lost、`PaymentProviderEventReceived` 队列 pending age 与 sweeper run 指标。settlement/reversal integration outbox 不冒充 provider processing queue。指标采集是旁路，抓取失败不会影响业务请求。
`BILLING_OUTBOX_MAX_ATTEMPTS` 控制 poison event 的最大尝试次数（默认 10，允许 1–100）。

Ingress 的 `BILLING_ENABLED_PROVIDERS` 只控制当前 webhook 接入面；worker 会注册全部内置 provider parser，避免
临时关闭某个 provider 后，已经进入 inbox 的历史事件被永久 stranded。provider webhook secret 只在 HTTP ingress
启动时校验；worker 处理已验签的 inbox fact，不重复承担 ingress secret 校验。

建议拆成独立进程，而不是与 HTTP server 共用生命周期：

```text
billing-api      : HTTP、验签、inbox、查询
billing-worker   : payment_outbox provider processing、bounded retry、dead-letter metrics
  billing-sweeper  : `worker:credit-sweeper`，credit hold/grant expiry、stale command、reconcile
```

`entitlement_outbox` 是同事务写入的 durable integration boundary；当前 V1 没有额外引入 Kafka/RabbitMQ，也不把
它伪装成已接入的消息系统。若某个下游需要消费 Entitlement 事件，必须实现显式 publisher/consumer adapter，使用
outbox lease、重复投递幂等和 published watermark；它不是 Payment/ Credit 核心 mutation 的隐式依赖。

handler 执行期间 `OutboxWorker` 会续租 `lease_until`；发布、重试或 dead-letter 更新必须携带原始
`lease_token`，这些 lease 写入使用独立 MySQL session，不会加入 handler 的业务 transaction；租约丢失时不伪报成功，交由下一次抢占重新处理。

payment worker 必须公开 `billing_worker_results_total`、`billing_worker_oldest_pending_age_seconds`；credit sweeper 必须公开
`billing_sweeper_runs_total`；
和按 `event_type/provider` 分组的指标。发布前必须用真实 MySQL + Redis 验证：重复 webhook、
worker 崩溃、租约过期、handler 重试、Redis 重启、MySQL 事务回滚均能收敛。

## 4. Provider adapter 边界

Provider adapter 只做四件事：原始字节验签（Stripe 使用官方 Stripe SDK）、body 解码（包含 WeChat APIv3 resource 解密）、事件归一化、提取稳定外部引用。它不负责
写支付表、不负责发放 credit、不负责调用 Credit API。归一化结果至少包含：

Stripe Checkout 的 `checkout.session.completed`/`checkout.session.async_payment_succeeded` 是一次性
`PaymentSettlement` 的 canonical acquisition event；关联的 `payment_intent.succeeded` 只作为已知事件确认并忽略，
避免同一 Checkout Session 产生两笔结算。订阅 Checkout 的 session completion 仍忽略，周期授予以
`customer.subscription.*` 的 provider subscription/period 事实为准，避免订阅首笔付款与周期事件重复发放积分。
周期积分 grant 会复制 `currentPeriodEnd` 到 `expires_at`；已经过期的延迟周期事件拒绝发放，避免把订阅额度错误变成永久积分。

```ts
type ParsedProviderEvent = {
  eventId: string;
  eventType: string;
  payloadTenantId: string | null;
  orderId: string | null;
  externalPaymentRef: string | null;
  externalReversalRef: string | null;
  refundAmountMinor: number | null;
  subscription: {
    providerSubscriptionId: string;
    teamId: string;
    planId: string;
    status: "active" | "past_due" | "canceled";
    currentPeriodStart: string | null;
    currentPeriodEnd: string | null;
    grantCredits: boolean;
  } | null;
};
```

多租户 webhook 不接受隐式的 `undefined` tenant：Stripe/Alipay/WeChat 必须从 provider metadata/账号映射或
每个 endpoint 的可信 tenant context 在 HTTP adapter 内映射为内部 `siteId`；新建支付 metadata 使用 `tenantId`，历史 payload 的 `siteId` 只保留为兼容性一致性提示。HTTP body 中的 tenant/site 标识不参与租户选择，解析不到可信映射时拒绝入 inbox。

对于 provider 签名事件本身不携带顶层 account ref 的 direct-account endpoint，必须配置该 endpoint 对应的
`BILLING_PROVIDER_ACCOUNT_REF_<PROVIDER>`。它只用于查 provider-account registry，不能由请求 header 或 payload
覆盖；Connect/多账户事件优先使用签名事件中的 account ref。

金额必须从 provider 事实与 checkout/settlement 快照交叉校验，不能信任客户端 webhook 中的任意
grant 数值。部分退款必须携带 provider refund reference 和退款金额；Billing 按 settlement minor amount
比例计算可冲正的 credit，并在锁定 grant 后累计校验，避免重复冲正或超额扣回。

## 5. 上线门禁

- [x] `billing-worker` 有真实代码入口：`pnpm worker:payment-events`；deployment/compose 单独运行属于部署阶段门禁；
- [x] payment success、refund、subscription 三个 processor 均有真实 MySQL integration test；
- [x] provider partial refund 以 settlement minor amount 为比例，在锁定 grant 后计算累计 credit reversal，避免并发
  partial refund 重复冲正或因先到事件吞掉后到事件；取消订阅无周期窗口时只更新 provider subscription 状态。
- [x] provider event 由 `received -> processed/ignored/failed` 的状态转换可审计、可重放；
- [ ] 旧 `kokoro-payment` webhook/confirm/refund writer 已停止，或明确处于 shadow-only；
- [ ] 双读审计通过且没有 settlement、reversal、fulfillment、credit grant drift；
- [ ] 断开 Redis 不能制造重复付款或重复积分，断开 MySQL 必须拒绝 mutation。

在这些门禁完成前，`kokoro-billing` 只能称为迁移准备/双写验证态，不宣称 Payment + Credit
业务闭环已经上线。

Checkout 也必须 fail-closed：本地 `mock` 作为 fixture provider；Stripe 已通过官方 Stripe SDK 创建
hosted Checkout Session，`once` 使用 Payment mode，`month/year` 使用 Subscription mode，并将
`provider_session_id/checkout_url` 回写 Billing。支付宝/微信 webhook
已能验签、归一化并异步处理，但对应 hosted-checkout adapter 接入前不会伪造本地支付 URL。

## 6. SQL 命名决策

`entitlement_credit_grant` 是合规命名，不需要改成含糊的 `credit` 或 `grant`：

- `entitlement_` 是 bounded context 前缀，避免与 payment、usage、IAM 的表混淆；
- `credit` 是业务对象类别；
- `grant` 是来源批次/授予批次，而不是余额 projection；
- 同一规则下使用 `entitlement_credit_account`、`entitlement_credit_hold`、
  `entitlement_credit_journal`，形成可搜索、可审计的稳定族；
- 表名使用 snake_case、单数业务实体、无缩写；主键和外键采用 `{table_singular}_id`。

因此保留 `entitlement_credit_grant`，不做为了“好看”而破坏迁移和查询一致性的重命名。
