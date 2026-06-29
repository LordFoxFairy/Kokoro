# kokoro-payment 技术方案

## 定位

kokoro-payment 是 plan、order、subscription、payment event、refund 的权威模块。

它回答"卖什么、卖多少钱、送多少积分、订单走到哪一步、provider 回调了什么"。它不放积分账本、不做运行时 usage metering。

实现状态：payment_plans/orders/subscriptions/events/refunds 表已建；upsertPlan、createOrder、confirmOrder、recordPaymentEvent 已实现。confirmOrder(pending->paid)前经 HTTP 调 credit ensure + grant，发放 Plan.creditMicros，幂等键 order:<id>。Subscription / Refund 为表占位无逻辑；EntitlementGrant、SiteOffer、PlanTemplate、ProviderPaymentConfig、真实 provider 接入、webhook 驱动、站点化(siteId)为规划。

## 业务职责

owns：

```text
Plan                    套餐定义(含 creditMicros 发放额)。
Order                   订单。
Subscription            订阅(表已建，无服务逻辑，规划)。
PaymentEvent            provider webhook 事件(当前仅存储)。
Refund                  退款(表已建，无服务逻辑，规划)。
PlanTemplate / SiteOffer / ProviderPaymentConfig   规划，未实现。
```

does not own：

```text
积分账本(kokoro-credit)。
运行时 usage metering(kokoro-credit)。
模型 provider routing(kokoro-model)。
用户身份(kokoro-user)。
```

## 上游和下游

```text
上游(调用 payment)：
  入口/web          创建订单(POST /orders)、确认订单(POST /orders/:id/confirm)。
  支付 provider     webhook -> /payment-events/record(当前仅存储，不驱动确认)。

下游(payment 调用)：
  kokoro-credit     confirmOrder 时经 HTTP 调 /credit/accounts/ensure + /credit/grant。
                    payment 不直接写 credit ledger。
```

## 核心对象

```text
Plan
  key(unique), name, currency, amountMinor, creditMicros(购买发放的积分),
  billingInterval, status。

Order
  teamId, planId, amountMinor, currency, status(pending|paid|canceled|refunded),
  idempotencyKey(unique), provider?, providerOrderId?。

Subscription（表占位）
  teamId, planId, status, provider?, providerSubscriptionId?,
  currentPeriodStart/End。无服务逻辑。

PaymentEvent
  provider, eventId, eventType, payload, status。unique(provider, eventId)。

Refund（表占位）
  orderId, amountMinor, currency, status, reason?。无服务逻辑；
  规划走 credit 冲正，不直接扣余额。
```

## 数据模型

MySQL（Prisma，已实现）：

```text
payment_plans          unique(key)，index(status)
payment_orders         unique(idempotencyKey)，index(teamId, status) / (planId)
payment_subscriptions  index(teamId, status)（表占位）
payment_events         unique(provider, eventId)
payment_refunds        index(orderId, status)（表占位）
```

规划新增：

```text
PlanTemplate
SiteOffer
ProviderPaymentConfig
EntitlementGrant（权益发放，当前无）
```

注：当前 Order / Subscription 无 siteId；站点化为规划。

其它存储：

```text
Mongo / Redis / 对象存储：当前不使用。
外部系统：支付 provider(规划接入 Stripe / 支付宝 / 微信支付等)。
          payment 只保存 order 映射、webhook 事件、状态机，不复制 provider 完整后台。
          当前无真实 provider SDK 调用。
```

## API / RPC / Events

已实现：

```text
GET  /healthz
POST /plans/upsert            入: key, name, currency, amountMinor, creditMicros?, billingInterval
                              出: Plan
POST /orders                  入: teamId, planId, amountMinor, currency, idempotencyKey
                              出: Order(status=pending)
POST /orders/:id/confirm      确认订单 pending->paid；creditMicros>0 时先 grant 再标 paid
                              出: Order(status=paid)
POST /payment-events/record   入: provider, eventId, eventType, payload?
                              出: PaymentEvent(status=received)，仅存储不驱动确认
```

confirmOrder -> credit 发放（已实现）：

```text
pending order + plan.creditMicros > 0:
  POST {KOKORO_CREDIT_BASE_URL}/credit/accounts/ensure  入: ownerKind=team, ownerId=teamId -> accountId
  POST {KOKORO_CREDIT_BASE_URL}/credit/grant            入: accountId, amountMicros=creditMicros,
                                                            idempotencyKey="order:<id>", reason=subscription
  grant 成功 -> markOrderPaid。grant 失败 -> order 留 pending，可同幂等键重试。
```

```text
幂等  order 按 unique(idempotencyKey)；payment event 按 unique(provider, eventId)；
      confirmOrder 的 credit grant 按 idempotencyKey="order:<id>"，支付确认只发一次。
约束  webhook -> confirmOrder 自动驱动未实现；当前 confirm 为显式端点调用。
```

## Admin 管理

```text
basePath  /admin/payments（resources 以 manifest 为准）
resources plans / orders / subscriptions / payment events / refunds
          （后续 site offers / provider configs / webhook replay / manual reconciliation）
权限 key  payment.order.read（细分 write/refund 规划中）
操作      套餐维护、订单查看（subscription/refund 为只读占位）。
审计      退款与人工对账必须审计（规划接入统一审计）。
```

注：subscriptions / refunds 后台为只读占位资源，无写入逻辑。

## 业务链路

```text
payment-to-credit
  POST /orders(pending)
    -> POST /orders/:id/confirm
    -> credit ensure + grant(reason=subscription, key=order:<id>)
    -> markOrderPaid
  (规划) provider webhook -> /payment-events/record -> 驱动 confirmOrder。
```

payment 不直接写 credit ledger，边界见 [ADR-003 credit 是唯一账本](../decisions/ADR-003-credit-ledger.md) 与 [kokoro-credit](kokoro-credit.md)。

## 部署

```text
服务名   kokoro-payment
端口     4241
依赖     user, credit
env      DATABASE_URL_PAYMENT, KOKORO_PAYMENT_PORT, KOKORO_PAYMENT_BASE_URL,
         KOKORO_USER_BASE_URL, KOKORO_MODEL_BASE_URL, KOKORO_CREDIT_BASE_URL
多 Pod   权威状态在 MySQL，可多副本；webhook 存储靠 unique(provider, eventId) 幂等；
         confirmOrder 的发放靠 idempotencyKey=order:<id> 幂等。
```

## 测试

```text
集成    order idempotencyKey 幂等；provider event id 幂等存储；
        confirmOrder 发放积分一次、再次 confirm 不重复发；
        recordPaymentEvent 不触碰 credit ledger。
反例    creditMicros=0 不发放；grant 失败 order 留 pending 可重试；
        重复 confirm(已 paid)幂等返回。
```

## 风险和边界

```text
最大风险是把 plan、offer、credit package 混成一张表。
正确边界：payment 负责"卖什么、送多少积分(creditMicros)"，credit 负责"到账与消费"。
支付底层不从 0 实现，优先接成熟 provider(规划)。
refund 必须走 credit 冲正流程，不绕过 credit 改余额(当前 refund 表占位，逻辑规划)。
```

## 后续任务

```text
P0  站点化(订单/订阅加 siteId)；webhook -> confirmOrder 驱动。
P1  Subscription / Refund 服务逻辑落地；EntitlementGrant 权益发放；
    PlanTemplate / SiteOffer / ProviderPaymentConfig；接入首个 provider。
P2  webhook replay、manual reconciliation、退款对账闭环。
```
