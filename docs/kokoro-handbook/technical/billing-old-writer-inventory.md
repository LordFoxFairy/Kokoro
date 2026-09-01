# Billing Legacy Writer Inventory

状态：迁移前基线，2026-08-22。

本清单不是“没有发现引用”式结论，而是按旧仓库实际 SQL/ORM 写路径建立的停写清单。只有这些路径全部
进入 read-only 或移除 runtime deployment，才满足 `old_writers_stop`。

## 1. Payment writer

| 仓库 | 文件 | 写事实 | 替代路径 |
|---|---|---|---|
| `kokoro-payment` | `src/infrastructure/mysql/prisma-payment-repository.ts` | Plan、Order、PaymentEvent、Subscription、Refund、Provider config | Billing catalog、checkout、provider inbox、subscription processor、reversal |
| `kokoro-payment` | `src/modules/order/application/payment-service.ts` | confirm → paid、refund → refunded、订阅周期授予 | Billing payment worker + source fact + entitlement application port |
| `kokoro-payment` | `src/modules/provider-event/application/webhook-service.ts` | webhook 入库并同步推进 confirm/refund/subscription | Billing HTTP inbox + `billing-worker` |
| `kokoro-payment` | `src/interfaces/http/routes.ts` | `/orders`、confirm、refund、provider event admin mutation | Billing User/Admin/Provider API |
| `kokoro-payment` | `src/interfaces/http/webhook-routes.ts` | provider webhook runtime ingress | Billing `/billing/webhooks/:provider` |

## 2. Credit writer

| 仓库 | 文件 | 写事实 | 替代路径 |
|---|---|---|---|
| `kokoro-credit` | `src/infrastructure/mysql/credit-repository.ts` | account、grant、spend、refund、usage、pricing rule | Billing `credit/*`、metering、journal、pricing revision |
| `kokoro-credit` | `src/infrastructure/mysql/hold-repository.ts` | hold、capture、release、usage settle、expiry | Billing hold allocation、settle/release、Redis leader sweep |
| `kokoro-credit` | `src/infrastructure/mysql/hold-sql.ts` | hold SQL mutation fragments | Billing `UsageSettlementService` |
| `kokoro-credit` | `src/main.ts` | hold expiry runtime | `scripts/expire-credit-holds.ts` + `RedisLease` |

## 3. 当前判定

```text
kokoro-payment  = legacy runtime writer，尚未停写
kokoro-credit   = legacy runtime writer，尚未停写
kokoro-billing  = target writer + migration/shadow 验证实现
```

本地 shadow 证据（2026-08-22）：Credit legacy `kokoro` → Billing 与 Payment fixture
`kokoro_payment_fixture` → Billing 均已完成 importer 后 source/target audit，结果均为 `status=ready`、`drifts=[]`。
这证明迁移事实与对账工具闭环可运行，但不改变上面的 runtime writer 判定。

因此当前不能把“Billing 测试全绿”解释为“旧 writer 已切换”。测试证明目标实现能够运行；停写还需要：

1. 为每个 deployment 删除旧 Payment/Credit writer process，保留只读查询或回滚镜像；
2. 逐 consumer 将 `target-first-with-legacy-fallback` 切为 target-only；
3. 在观察窗口执行 Payment/Credit audit、reconcile、重复 webhook、worker crash/retry 和 rollback exercise；
4. operator 对 source fact、余额、grant、hold、settlement、reversal 零 drift 签字；
5. 将本清单中的所有 writer 标记为 `stopped`，并把 stop 时间写入 release manifest。

## 4. 禁止的伪完成

- 只停 HTTP 入口但保留旧 worker，不算停写；
- 只迁移 account 余额、不迁移 ledger/grant/hold，不算 Credit 完成；
- 只接收 webhook、不消费 outbox，不算 Payment 完成；
- 只把 fallback URL 删除、不做 source fact 对账，不算切换完成。
