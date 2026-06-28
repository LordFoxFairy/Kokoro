# ADR-003 credit 是唯一账本，payment 与 credit 分离

状态：已采纳。

## 背景

支付成功后是否应直接增加用户余额？积分、权益、扣费、定价应集中在哪里？

## 决策

```text
payment 负责"卖什么"：plan / offer / order / subscription / payment event / refund。
credit 负责"到账什么权益、怎么消耗"：account / bucket / hold / ledger / usage / pricing / entitlement。
payment 成功事件 -> 调用 credit.grant，由 credit 创建 EntitlementGrant 和 CreditBucket。
CreditLedgerEntry 是唯一余额权威。默认积分和权益按 site scoped，不跨站共享。
```

## 理由

```text
支付成功 ≠ 可用所有功能（买 music.pro 不应解锁 video）。
增量积分包 ≠ 套餐权益，需分离。
折扣是 pricing 逻辑，不是直接改余额。
退款、异常补救需要独立于支付状态机。
跨站共享会污染毛利分析和营销灵活性。
```

## 约束

```text
payment 不能直接写 credit ledger。
agent / model 不能直接改余额；agent 只能 quote/hold/commit/release。
model 不决定最终价格，只给成本参考。
支付 webhook 幂等：unique(siteId, provider, eventId)。
credit grant 幂等：idempotencyKey。
payment 成功但 grant 失败 -> 运营队列监控 + 人工补救。
```

## 替代方案（已否决）

```text
payment 直接写 credit        耦合，难扩展权益类型，退款混乱。
全局钱包，site 只是消费渠道    破坏套餐独立性，毛利难算，免费/付费额度混淆。
```

## 影响

落地扣费闭环 quote->hold->capture/release->refund（见 [credit-reserve-commit-refund](../business-flows/credit-reserve-commit-refund.md)）；payment->credit 走 grant（见 [payment-to-credit](../business-flows/payment-to-credit.md)）。

相关：[kokoro-credit 模块](../modules/kokoro-credit.md)、[kokoro-payment 模块](../modules/kokoro-payment.md)。
