# ADR-026：引入 Order/Adjustment/PaymentCollection 事实层

- 状态：accepted
- 日期：2026-08-24

## Context

当前 Billing V1 以 `payment_checkout` 直接连接 provider session 与 `payment_settlement`。这能完成一单一商品的本地切片，
但不能严谨表达商城必需的订单行、优惠调整、支付授权/捕获/作废、3DS、重试、多支付和部分退款。

成熟商城通常把 Order 作为购买中心，把 Adjustment 保存为可解释的价格修改，把 PaymentCollection/PaymentSession/Payment/Refund
分开。否则退款、审计和历史价格重算会依赖 JSON 或一个不断膨胀的 checkout 表。

## Decision

目标模型采用：

```text
Order -> OrderLine + OrderAdjustment -> PaymentCollection
  -> PaymentSession -> PaymentAttempt/Transaction -> Settlement/Refund
  -> Fulfillment
```

目标表为 `payment_order`、`payment_order_line`、`payment_order_adjustment`、`payment_collection`、`payment_session`、
`payment_attempt`、`payment_refund`，并保留 `payment_settlement` 作为 capture/settlement source fact。

现有 `payment_checkout` 是 compatibility slice，不立即删除；后续以 expand → 双读校验 → caller 切换 → contract 删除迁移。
数字商品暂不引入库存、物流、税务总账，但 `OrderLine`、`Adjustment`、Payment lifecycle 不能因此省略。

## Consequences

- Promotion 的折扣可以按订单或订单行解释，退款可以按原始 line/adjustment 计算；
- provider authorization、capture、void、refund 的重试和部分成功有明确事实；
- 需要新增 migration、OpenAPI schema、read model、reconcile 和 integration tests；
- V1 仍可继续运行，不把未实现的商城扩展写成当前实现完成。
