# Payment to Credit 链路

## 目标

把一次成功支付安全地变成站内积分：创建订单 -> 确认订单(pending -> paid) -> 经 HTTP 调 credit ensure + grant 发放积分。全程幂等，payment 不写 ledger，credit 是唯一账本。

## 实现状态

```text
已实现   Plan.creditMicros、createOrder(pending)、confirmOrder(pending->paid 前先 grant)、
         recordPaymentEvent(仅存事件)；confirmOrder 经 HTTP 调 credit
         /credit/accounts/ensure + /credit/grant，幂等键 order:<id>。
规划     EntitlementGrant / 权益发放、Subscription 驱动(表已建但无逻辑)、
         Refund 驱动(表已建但无逻辑)、SiteOffer / ProviderPaymentConfig、
         真实 provider 接入、webhook -> confirmOrder 自动驱动、站点化(siteId)。
```

## 参与模块

```text
kokoro-payment                 卖什么、交易状态: Plan / Order(+ 表 Subscription/PaymentEvent/Refund)。
kokoro-credit                  唯一账本: grant 加余额(reason=subscription)。
provider(规划)                 Stripe 等收单方回调 webhook -> 驱动 confirmOrder。
```

## 前置条件

```text
User / team 已存在(订单按 teamId)。
Plan 已 upsert，creditMicros 决定本单发多少积分。
```

## 主流程

```text
1. 创建订单
   POST /orders 入: teamId, planId, amountMinor, currency, idempotencyKey
   建 Order(status=pending)。unique(idempotencyKey)防重复下单。

2. 确认订单(当前为直接调用，非 webhook 驱动)
   POST /orders/:id/confirm
   - order 已 paid     -> 幂等返回，不再发放。
   - order 非 pending  -> OrderNotConfirmable。
   - order pending     -> 取 Plan；若 plan.creditMicros > 0:
       先 grant 再标 paid(失败时 order 仍 pending，同幂等键重试不重复发):
         POST {KOKORO_CREDIT_BASE_URL}/credit/accounts/ensure
              入: ownerKind=team, ownerId=teamId  -> accountId
         POST {KOKORO_CREDIT_BASE_URL}/credit/grant
              入: accountId, amountMicros=plan.creditMicros,
                  idempotencyKey="order:<id>", reason=subscription
       grant 成功后 markOrderPaid -> status=paid。

3. 记录 provider 事件(规划驱动)
   POST /payment-events/record 入: provider, eventId, eventType, payload?
   建 PaymentEvent(status=received)，unique(provider, eventId)去重。
   当前仅存储，不自动驱动 confirmOrder(规划: webhook -> confirm)。
```

## 异常流程

```text
grant 失败       confirmOrder 抛错，order 保持 pending；
                 同幂等键 order:<id> 重试 confirm，credit 侧幂等不重复发。
重复 confirm     order 已 paid -> 幂等返回，不再 grant。
退款             Refund 表已建但无服务逻辑(规划: 走 credit 冲正)。
订阅周期         Subscription 表已建但无驱动逻辑(规划)。
站点化           当前无 siteId，订单/账户不按 site 隔离(规划)。
```

## 数据变化

```text
Order              status pending -> paid(confirmOrder);canceled/refunded 枚举存在但无驱动。
PaymentEvent       received(仅存储，不流转处理)。
Subscription       表存在，无写入逻辑(规划)。
Refund             表存在，无写入逻辑(规划)。
CreditAccount      credit 侧 grant: balanceMicros += creditMicros。
CreditLedgerEntry  credit 侧 grant 写正数(payment 不直接写)。
```

## 幂等和一致性

```text
Order             unique(idempotencyKey)防重复下单。
PaymentEvent      unique(provider, eventId)防重复存事件。
grant             idempotencyKey="order:<id>" 防重复发放(支付成功仅发一次)。
顺序保证          confirmOrder 先 grant 后 markPaid;grant 失败 order 留 pending 可安全重试。
边界              payment 不写 ledger;credit 不收单。
```

## 用户可见结果

```text
支付确认   confirmOrder 后积分到账，可在余额看到。
重复确认   不重复发积分。
(规划)权益/订阅/退款   EntitlementGrant、Subscription 刷新、Refund 回退尚未实现。
```

## 验收标准

```text
同一 order confirm 多次，积分只发一次(幂等键 order:<id>)。
Order 仅在 pending->paid 时触发 grant;creditMicros=0 不发。
grant 失败 order 保持 pending，可按同幂等键安全补发。
payment 不写 credit ledger。
```

## 相关

```text
账本     ../decisions/ADR-003-credit-ledger.md
扣费闭环  ./credit-reserve-commit-refund.md
模块     ../modules/kokoro-payment.md
```
