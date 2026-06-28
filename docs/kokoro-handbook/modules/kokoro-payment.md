# kokoro-payment 技术方案

## 定位

kokoro-payment 是 plan、offer、order、subscription、payment event、refund 和支付 provider webhook 的权威模块。

它回答"卖什么、卖多少钱、订单走到哪一步、provider 回调了什么"。它不放积分账本、不做运行时 usage metering。

实现状态：payment_plans/orders/subscriptions/events/refunds 表和 upsert/orders/record 最小接口已实现；PlanTemplate、SiteOffer、ProviderPaymentConfig、站点化和 provider 接入为规划。

## 业务职责

owns：

```text
Plan / PlanTemplate     套餐定义与模板。
SiteOffer               站点级售卖项（规划）。
Order                   订单。
Subscription            订阅。
PaymentEvent            provider webhook 事件。
Refund                  退款。
ProviderPaymentConfig   支付 provider 配置引用（规划）。
```

does not own：

```text
积分账本（kokoro-credit）。
运行时 usage metering（kokoro-credit）。
模型 provider routing（kokoro-model）。
用户身份（kokoro-user）。
```

## 上游和下游

```text
上游（调用 payment）：
  入口/web          创建订单、查询 offer。
  支付 provider     webhook -> /payment-events/record。

下游（payment 调用）：
  kokoro-site       消费 siteId（SiteOffer / 订单按 site 隔离）。
  kokoro-credit     支付成功后调 credit grant / entitlement issue。
                    payment 不能直接写 credit ledger。
```

## 核心对象

```text
Plan
  siteId, key, name, currency, amountMinor, billingInterval, status。

Order
  siteId, teamId/workspaceId, planId/offerId, amountMinor, currency,
  status, idempotencyKey, provider, providerOrderId。

Subscription
  siteId, teamId/workspaceId, planId/offerId, status, providerSubscriptionId。

PaymentEvent
  siteId?, provider, eventId, eventType, payload, status。

Refund
  退款记录，必须形成明确的 credit adjustment 流程，不直接扣余额。
```

## 数据模型

MySQL（Prisma，已实现）：

```text
payment_plans
payment_orders
payment_subscriptions
payment_events
payment_refunds
```

规划新增：

```text
PlanTemplate
SiteOffer
ProviderPaymentConfig
```

唯一约束（规划）：

```text
Plan          unique(siteId, key)
Order         unique(siteId, idempotencyKey)
PaymentEvent  unique(provider, eventId)
Subscription  index(siteId, teamId, status)
```

其它存储：

```text
Mongo / Redis / 对象存储：当前不使用。
外部系统：支付 provider（Stripe / 支付宝 / 微信支付 / 后续 Paddle、LemonSqueezy）。
          payment 只保存 provider config 引用、order 映射、webhook 事件、状态机，
          不复制 provider 完整后台。
```

## API / RPC / Events

已实现：

```text
GET  /healthz
POST /plans/upsert
POST /orders
POST /payment-events/record
```

```text
幂等  order 按 unique(siteId, idempotencyKey)；
      payment event 按 unique(provider, eventId)；
      支付成功只触发一次 credit grant。
错误码 idempotencyKey / eventId 冲突走幂等返回已有结果。
```

## Admin 管理

```text
basePath  /admin/payment（resources 以 manifest 为准）
resources plans / orders / subscriptions / payment events / refunds
          （后续 site offers / provider configs / webhook replay / manual reconciliation）
权限 key  payment.order.read（细分 write/refund 规划中）
操作      套餐维护、订单与订阅查看、webhook 重放、退款、人工对账。
审计      退款与人工对账必须审计（规划接入统一审计）。
```

后台查询默认带 siteId，仅 platform root admin 可跨站查询。

## 业务链路

```text
payment-to-credit
  payment event processed
    -> payment 确认 order/subscription
    -> 调用 credit grant / entitlement issue
    -> credit 写 ledger
```

payment 不直接写 credit ledger，边界见 [ADR-003 credit 是唯一账本](../decisions/ADR-003-credit-ledger.md) 与 [kokoro-credit](kokoro-credit.md)。

## 部署

```text
服务名   kokoro-payment
端口     4241
env      DATABASE_URL_PAYMENT, KOKORO_PAYMENT_PORT, KOKORO_PAYMENT_BASE_URL,
         KOKORO_SITE_BASE_URL, KOKORO_CREDIT_BASE_URL
多 Pod   权威状态在 MySQL，可多副本；webhook 处理靠 unique(provider, eventId) 幂等。
```

## 测试

```text
集成    provider event id 幂等；order idempotencyKey 幂等；不同 site 可同 plan key。
反例    支付成功只触发一次 credit grant；refund 不直接扣余额，必须走 credit adjustment 流程。
```

## 风险和边界

```text
最大风险是把 plan、offer、credit package 混成一张表。
正确边界：payment 负责"卖什么"，credit 负责"到账什么权益和怎么消费"。
支付底层不从 0 实现，优先接成熟 provider。
refund 必须形成明确的 credit adjustment 流程，不绕过 credit 改余额。
```

## 后续任务

```text
P0  站点化（订单/订阅加 siteId）；provider event/order 幂等反例测试。
P1  PlanTemplate / SiteOffer / ProviderPaymentConfig；接入首个 provider（Stripe 或支付宝/微信）。
P2  webhook replay、manual reconciliation、退款对账闭环。
```
