# kokoro-payment 设计卡

> 历史设计卡：新能力以 [`05-billing.md`](05-billing.md) 与
> [`../31-billing-subrepository-architecture.md`](../31-billing-subrepository-architecture.md) 为准。
> `kokoro-payment` 进入迁移态，目标 owner 是 `kokoro-billing` 的 Payment Context。

## 历史定位

商品、套餐、Checkout、Order、Subscription、Provider Event、Refund 的唯一 owner。

## 领域等级

L2。支付订单状态、provider event 幂等、订阅状态和退款状态存在真实状态机。

## 目标目录

```text
src/
├── modules/
│   ├── catalog/
│   ├── checkout/
│   ├── order/
│   ├── provider-event/
│   ├── subscription/
│   ├── refund/
│   └── benefit-grant/
├── providers/{stripe,alipay,wechat}/
├── interfaces/{http,rpc,admin}/
├── infrastructure/mysql/
├── generated/
├── config/
└── main.ts
```

## 关键边界

- provider payload 在 adapter 处归一化。
- Payment 不直接写 Credit 表；购买后的积分授予调用 Credit command。
- 支付成功、退款成功和 Credit grant 是不同事实，不能用一个 `paid` 字段代替。
- 当前不拆 `kokoro-entitlement`；权益复杂度不足以形成独立 owner。

## 100 分证据

- order/provider event/subscription/refund 状态机有 domain 测试。
- provider event 唯一键和重放测试存在。
- Payment -> Credit 只有公开 contract。
- provider SDK 不泄漏到 domain/application。
- 退款、重复 webhook、授予失败和重试语义明确。


## 当前落地证据与迁移门禁

当前代码证据（只证明现状，不等于目标已完成）：

- `kokoro-payment`
- `docs/kokoro-handbook/business-flows/payment-to-credit.md`

迁移完成前必须同时具备：

- schema 与唯一 owner / runtime writer 清单一致；
- 公开 contract、生成物和 consumer 清单一致；
- architecture test 能阻止越界 import、跨表写入和旧入口回流；
- unit、integration、contract test 覆盖本卡的核心不变量；
- 旧入口或旧写面已删除，或有明确的兼容截止版本和回滚方案。
