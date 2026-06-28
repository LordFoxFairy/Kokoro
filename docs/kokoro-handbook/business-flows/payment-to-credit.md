# Payment to Credit 链路

## 目标

把一次成功支付安全地变成站内权益和积分：创建订单 -> provider webhook 通知 -> 订单 paid -> credit 发放 EntitlementGrant 和 CreditBucket。全程幂等，payment 不写 ledger，credit 是唯一账本。

## 参与模块

```text
kokoro-payment                 卖什么、交易状态：Order / Subscription / PaymentEvent。
provider                       Stripe 等收单方，回调 webhook。
kokoro-credit                  唯一账本：grant 发 EntitlementGrant + CreditBucket。
kokoro-site                    决定该站卖哪些 SiteOffer。
```

## 前置条件

```text
SiteContext 已解析（siteId 确定）。
User + workspace 已存在（见 user-register-login）。
SiteOffer 在该站 status=active。
```

## 主流程

```text
1. 创建订单
   POST 创建 Order(siteId, userId, workspaceId, offerId, amountMinor, currency,
        status=pending, provider, idempotencyKey)。
   按 offer 跳转到 provider 收银台。

2. Provider webhook
   provider 支付成功后回调，落 PaymentEvent(siteId, provider, eventId, eventType, payload,
        status=received)，按 unique(siteId, provider, eventId) 去重。

3. 处理事件
   关联 Order -> status=paid（订阅则建/更新 Subscription，currentPeriodStart/End）。
   PaymentEvent status=processed。

4. credit.grant
   payment 调 credit.grant 发放权益和积分，不直接写 credit 表：
   POST /credit/grant 入: siteId, accountId, amountMicros, bucketSource, sourceRefId, idempotencyKey
   建 EntitlementGrant(sourceKind=offer, sourceId, capabilityKey, surface)
   建 CreditBucket(source=subscription|topup, sourceRefType, sourceRefId)。
```

## 异常流程

```text
webhook 失败       PaymentEvent status=failed，可重投；unique(siteId, provider, eventId) 防重复处理。
grant 失败补救      Order 已 paid 但 grant 未成功 -> 按 idempotencyKey 重试 grant，安全重放不重复发。
退款              provider refund -> Order status=refunded -> credit.refund（反向 ledger + refund bucket，
                  见 credit-reserve-commit-refund）。
跨站              order/subscription/credit 均 site scoped；music 订阅不给 video 权益（P4/P5）。
```

## 数据变化

```text
Order              status pending -> paid / canceled / refunded。
Subscription       订阅类新增/更新（status active|canceled|past_due, currentPeriod*）。
PaymentEvent       received -> processed / failed（unique(siteId, provider, eventId)）。
EntitlementGrant   新增（sourceKind=offer）。
CreditBucket       新增 source=subscription | topup。
CreditLedgerEntry  grant 发放写正数（credit 内部）。
```

## 幂等和一致性

```text
Order             idempotencyKey 防重复下单。
PaymentEvent      unique(siteId, provider, eventId) 防重复处理 webhook。
grant             idempotencyKey + sourceRefId 防重复发放（支付成功仅发一次）。
强一致            payment event -> order/subscription -> credit grant 必须幂等。
边界              payment 不写 ledger；credit 不收单。增量积分包只加 bucket，不改 entitlement。
```

## 用户可见结果

```text
支付成功   套餐权益生效，积分到账，可在 usage/余额看到。
订阅       周期内权益有效，到期按 currentPeriodEnd 刷新。
退款       余额/权益回退，ledger 可追溯。
```

## 验收标准

```text
同一 webhook eventId 重投，权益与积分只发一次。
Order 仅在 paid 后触发 grant。
music 订阅不影响 video 权益与余额。
增量积分包不解锁套餐未授权的能力。
grant 失败可按 idempotencyKey 安全补发。
```

## 相关

```text
账本     ../decisions/ADR-003-credit-ledger.md
扣费闭环  ./credit-reserve-commit-refund.md
模块     ../modules/kokoro-credit.md
```
