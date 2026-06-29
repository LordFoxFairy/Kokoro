# Credit Reserve-Commit-Refund 链路

## 目标

把一次能力使用的费用，从"预估"安全地走到"落账"或"释放"，全程幂等、不超扣、不漏扣、可审计。这是所有计费链路的底层闭环。

## 实现状态

```text
已实现   两字段账户(balanceMicros + heldMicros)、quote / hold / capture / release / spend / grant，
         全部原子条件更新 + idempotencyKey 唯一约束幂等。
规划     standalone refund 操作(当前 refund 只是 ledger reason 取值)、
         hold 过期自动回收(expiresAt 已存但未读取)、entitlement / spend limit。
```

## 参与模块

```text
kokoro-agent / kokoro-session   发起 quote / hold / capture / release / spend。
kokoro-credit                   唯一账本权威，执行 hold/capture/release/spend/grant。
kokoro-payment                  支付成功后调 grant 发放积分(见 payment-to-credit)。
kokoro-model                    提供成本参考(不决定价格)。
```

## 账户模型(真实)

```text
CreditAccount 只有两个金额字段:
  balanceMicros   账户总余额。
  heldMicros      已冻结(尚未落账)的部分。
available = balanceMicros - heldMicros   可用额，无 CreditBucket / 多桶。

owner 维度: unique(ownerKind, ownerId)，ownerKind = user | team。
```

## 前置条件

```text
CreditAccount 已存在或首次 POST /credit/accounts/ensure。
PricingRule 覆盖目标 featureKey(+labelKey)。
```

## 主流程

```text
1. Quote(纯读)
   POST /credit/quote  入: featureKey, labelKey?, quantity?
   按 PricingRule(featureKey + labelKey，否则回退 labelKey=null，取最新生效项)计价，
   amountMicros = rule.amountMicros * quantity。无副作用。

2. Reserve(Hold) — 原子条件
   POST /credit/hold   入: accountId, amountMicros, idempotencyKey, expiresAt?
   单条原子 SQL: heldMicros += amount WHERE balanceMicros - heldMicros >= amount。
   更新命中则建 CreditHold(active)；命中 0 行则余额不足报错。
   expiresAt 当前仅存储，不参与自动回收(规划)。

3. Execute
   agent/provider 执行实际任务，得到真实用量。

4. Commit(Capture) — 事务 + 原子状态转移
   POST /credit/capture 入: holdId, actualAmountMicros, idempotencyKey, reason, featureKey, modelBindingId?
   要求 actualAmount <= hold.amountMicros。事务内:
     hold: active -> captured(原子条件，命中 0 行视为竞态/已处理)；
     account: balanceMicros -= actualAmount; heldMicros -= hold.amountMicros
              (冻结全额释放，多冻结的差额自动回到可用)；
     写 CreditLedgerEntry(负数 amountMicros)；
     写 UsageRecord(status=settled)。
```

无 hold 的直扣路径:

```text
Spend(直扣) — 原子条件
   POST /credit/spend  入: accountId, amountMicros, idempotencyKey, reason
   单条原子 SQL: balanceMicros -= amount
                 WHERE status=active AND balanceMicros - heldMicros >= amount。
   只能动可用额(不吃 held)，命中则写负数 ledger，命中 0 行余额不足报错。
```

## 异常流程

```text
余额不足          hold / spend 原子条件命中 0 行 -> 报 InsufficientCredit。
任务失败/取消      POST /credit/release 入: holdId, idempotencyKey
                  hold active -> released(原子条件)，heldMicros -= hold.amountMicros，
                  不写 ledger，可用额恢复；已 released 则幂等返回。
超时              hold.expiresAt 已存储但当前不触发自动回收(规划)；
                  需上游显式 release。
已落账后需退款     当前无 standalone refund 端点。冲正以 grant(reason=refund)正向加余额。
                  反向退款流程(关联原 ledger entry)为规划。
重复请求          同 idempotencyKey 重放 -> 命中唯一约束 -> 幂等返回已有结果，不重复扣。
```

## 数据变化

```text
CreditAccount       hold: heldMicros += amount。
                    capture: balanceMicros -= actual; heldMicros -= hold.amount。
                    release: heldMicros -= amount。
                    spend: balanceMicros -= amount。
                    grant: balanceMicros += amount。
CreditHold          状态 active -> captured | released。
CreditLedgerEntry   capture / spend 写负数；grant 写正数；balanceAfterMicros 落账后余额。
UsageRecord         capture 写 status=settled(枚举另有 recorded / failed，当前未使用)。
```

## 幂等和一致性

```text
hold / capture / release / spend / grant   idempotencyKey；
                                           各表 unique(idempotencyKey) 兜底。
原子性                                      hold/spend 走单条带条件 UPDATE；
                                           capture/release 在事务内做条件状态转移。
事务                                        capture 在 DB 事务内完成
                                           hold 转移 + 账户扣减 + ledger + usage。
不可盲目重试                                capture / spend 是副作用写，只能靠 idempotencyKey 安全重放。
```

## 用户可见结果

```text
成功     任务完成，余额按实际用量减少，usage(settled)可见。
余额不足  InsufficientCredit + 充值/升级入口。
失败     冻结释放，可用额恢复，无扣费，可重试。
```

## 验收标准

```text
同 idempotencyKey 重试 N 次，余额只变一次。
余额不足时 hold / spend 必失败，不产生负可用额。
release 后 heldMicros 完全恢复，不留悬挂 hold。
capture 后 balanceMicros 减实际、heldMicros 减冻结全额(差额回可用)，ledger 账平。
spend 只动可用额，不吃别人的 hold。
不同 owner(user/team)账户完全隔离。
```

## 相关

```text
账本     ../decisions/ADR-003-credit-ledger.md
模块     ../modules/kokoro-credit.md
支付发放  ./payment-to-credit.md
```
