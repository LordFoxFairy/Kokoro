# Payment to Credit 链路

> 本文保留迁移前 `kokoro-payment -> kokoro-credit` 流程的入口名称，当前实现契约以独立
> `kokoro-billing` 子仓库为准，不再使用旧 `/orders`、`/credit/grant` 写入口。

## 当前闭环

```text
User:        POST /billing/checkout -> hosted checkout -> provider webhook
Payment:     provider event inbox -> settlement/reversal/subscription period
Entitlement: settlement -> acquisition -> fulfillment -> credit grant -> journal
Credit:      quote -> hold -> usage settle/release -> journal
Admin:       grant/refund/retry/reconcile/stats -> /admin/billing/*
```

Payment 不直接写 CreditJournal；Payment 与 Entitlement 在同一子仓内仍保持 bounded context 边界，通过稳定事实和
outbox 协作。MySQL 保存余额、支付和最终幂等状态，Redis 只承担租约、短路和运行时协调。

## 关键保证

- provider webhook 先验签、保留 raw body、写 inbox，再异步处理；`(site_id, provider, event_id)` 唯一。
- 同一 settlement 只能产生一个 acquisition/fulfillment；同一 reversal 只能产生一个冲正事实。
- settlement 成功后通过 subscription/settlement application port 发放权益，CreditJournal 是余额变更唯一来源。
- 退款不直接改余额，先生成 payment reversal，再按未消费 grant 做 entitlement reversal。
- quote、hold、settle、release 都有 MySQL 幂等记录；Redis 故障不改变账务正确性。
- 所有租户查询必须携带可信 `site_id`，用户、Internal、Admin API 使用独立 route 和认证策略。

## 历史迁移

旧订单、支付事件、订阅和退款必须按
`../technical/billing-legacy-cutover-runbook.md` 完成 site/provider/period 映射、dry-run audit 和 receipt
校验后导入；切流前必须通过 `kokoro-billing/contract/openapi/v1/openapi.yaml` 的 old-writer gate。新代码和新文档不得继续引用旧
writer 作为生产入口。

## 权威文档

- `../technical/31-billing-subrepository-architecture.md`
- `../technical/billing-api-contract-v1.md`
- `../technical/billing-transaction-matrix.md`
- `../technical/billing-event-processing.md`
- `../technical/billing-mysql-schema-v1.md`
