# Credit Reserve-Commit-Refund 链路

## 目标

把一次能力使用的费用，从"预估"安全地走到"落账"或"释放/退款"，全程幂等、不超扣、不漏扣、可审计。这是所有计费链路的底层闭环。

## 参与模块

```text
kokoro-agent / kokoro-session   发起 quote / hold / capture / release。
kokoro-credit                   唯一账本权威，执行 hold/capture/release/grant/refund。
kokoro-payment                  refund 关联支付时参与。
kokoro-model                    提供成本参考（不决定价格）。
```

## 前置条件

```text
SiteContext 已解析（siteId 确定）。
CreditAccount 已存在或首次自动 ensure。
PricingRule 覆盖目标 featureKey。
```

## 主流程

```text
1. Quote
   POST /credit/quote  入: siteId, workspaceId, featureKey, modelBindingId/plan, quantity
   按 PricingRule 计算 estimateMicros，返回 bucketBreakdown。无副作用。

2. Reserve(Hold)
   POST /credit/hold   入: siteId, accountId, amountMicros, idempotencyKey, expiresAt
   按 bucket 优先级校验 remainingMicros >= amountMicros，写 CreditHold(active)。

3. Execute
   agent/provider 执行实际任务，得到真实用量。

4. Commit(Capture)
   POST /credit/capture 入: siteId, holdId, actualAmountMicros, idempotencyKey
   从 bucket 扣 actualAmountMicros，写 CreditLedgerEntry（负数）和 UsageRecord(settled)，
   CreditHold=captured。
```

## 异常流程

```text
余额不足          step 2 hold 失败 -> 402，提示充值。
任务失败/取消      POST /credit/release 入: siteId, holdId, idempotencyKey
                  CreditHold=released，不写 ledger，额度恢复。
超时              hold 到 expiresAt 自动过期释放。
已落账后需退款     POST /credit/refund 入: siteId, ledgerEntryId, amountMicros, reason, idempotencyKey
                  校验原 entry 已 settled -> 建 refund bucket（正数）+ 反向 ledger entry。
重复请求          同 idempotencyKey 重放 -> 幂等返回已有结果，不重复扣。
```

## 数据变化

```text
CreditHold          新增/更新状态 active|captured|released|expired。
CreditLedgerEntry   capture 写负数；refund 写正数。
CreditBucket        capture 减 remainingMicros；refund 建 source=refund 新桶。
UsageRecord         状态流转 quoted -> held -> settled / failed。
```

## 幂等和一致性

```text
hold / capture / release    idempotencyKey；unique(siteId, accountId, idempotencyKey) 兜底。
refund                      original ledgerEntryId + idempotencyKey。
事务                        capture 必须在 DB 事务内完成 bucket 扣减 + ledger 写入。
不可盲目重试                 capture / commit 属于副作用写，只能靠 idempotencyKey 安全重放。
```

## 用户可见结果

```text
成功     任务完成，余额按实际用量减少，usage 历史可见。
余额不足  402 toast + 充值/升级入口。
失败     额度自动恢复，无扣费，可重试。
退款     余额回补，ledger 可见退款条目。
```

## 验收标准

```text
同 idempotencyKey 重试 N 次，余额只变一次。
余额不足时 hold 必失败，不产生负余额。
release 后额度完全恢复，不留悬挂 hold。
capture 后 ledger 与 bucket 余额一致（账平）。
refund 后金额可追溯到原 ledger entry。
不同 site 账户完全隔离。
```
