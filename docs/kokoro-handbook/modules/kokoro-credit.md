# kokoro-credit 技术方案

## 定位

kokoro-credit 是积分账户、冻结、账本、usage、pricing rule 和扣费闭环的唯一权威。

不是支付收单方，不是模型路由方，不是任务执行方。它只回答"账户有多少、使用时扣多少、扣了多少"。

实现状态：两字段账户(balanceMicros + heldMicros)、quote / hold / capture / release / spend / grant、PricingRule、UsageRecord 已实现，全部原子条件更新 + idempotencyKey 唯一约束幂等。Entitlement / SpendLimit、多桶、standalone refund、hold 过期回收为规划。

## 业务职责

owns：

```text
CreditAccount      积分账户(balanceMicros + heldMicros 两字段，无多桶)。
CreditHold         扣费前的冻结。
CreditLedgerEntry  唯一权威账本流水。
UsageRecord        一次能力使用记录。
PricingRule        featureKey(+labelKey)单位定价。
Entitlement        权益(规划，未实现)。
SpendLimit         消费上限(规划，未实现)。
```

does not own：

```text
支付订单和确认(kokoro-payment)。
模型 provider 路由和价格上限(kokoro-model 只给成本参考)。
用户身份和权限(kokoro-user)。
agent 任务执行(kokoro-agent)。
```

## 上游和下游

```text
上游(调用 credit)：
  kokoro-agent     quote / hold / capture / release / spend。
  kokoro-payment   confirmOrder 时 ensure + grant 积分。

下游(credit 调用)：
  当前无强依赖；env 含 user / model base url 供后续扩展。
```

## 核心对象

```text
CreditAccount
  ownerKind(user|team) + ownerId，balanceMicros，heldMicros，status(active|disabled)。
  available = balanceMicros - heldMicros。unique(ownerKind, ownerId)。

CreditHold
  accountId，amountMicros，status(active|captured|released)，idempotencyKey，expiresAt?。
  expiresAt 当前仅存储，不参与自动回收(规划)。

CreditLedgerEntry
  amountMicros 可负(spend/capture)可正(grant)，balanceAfterMicros，reason，idempotencyKey(unique)，requestId?。

UsageRecord
  accountId?，featureKey，amountMicros，modelBindingId?，requestId?，idempotencyKey?(unique)，
  status(recorded|settled|failed，当前仅 capture 写 settled)。

PricingRule
  featureKey，labelKey?，unit，amountMicros，status(active|disabled)，
  effectiveFrom / effectiveUntil?(时间窗)。
```

生命周期(扣费闭环)：

```text
quote(纯读) -> hold -> execute -> capture -> ledger(负) + usage(settled)
                          \-> release(失败/取消)
直扣分支:  spend(无 hold，直接动可用额，写负 ledger)
grant:     正向加余额(支付发放 / reason=refund 冲正)
```

账户金额变化(原子，无 bucket 顺序)：

```text
hold     heldMicros += amount      WHERE balance - held >= amount
capture  balance -= actual; held -= hold.amount   (差额回可用)
release  held -= amount
spend    balance -= amount         WHERE status=active AND balance - held >= amount
grant    balance += amount
```

## 数据模型

MySQL(Prisma，权威，必须事务)：

```text
credit_accounts          unique(ownerKind, ownerId)，index(status)
credit_holds             unique(idempotencyKey)
credit_ledger_entries    unique(idempotencyKey)
credit_usage_records     unique(idempotencyKey?)，index(featureKey, createdAt) / (accountId, createdAt)
credit_pricing_rules     index(featureKey, status)
```

其它存储：

```text
Mongo / Redis / Object Storage：不使用(账务严禁放 Mongo，余额严禁放 Redis)。
外部系统：无。
```

## API / RPC / Events

已实现：

```text
GET  /healthz
POST /credit/accounts/ensure   入: ownerKind(user|team), ownerId           出: CreditAccount
POST /credit/quote             入: featureKey, labelKey?, quantity?         出: QuoteResult(纯读)
POST /credit/hold              入: accountId, amountMicros, idempotencyKey, expiresAt?
                               出: CreditHold(active)
POST /credit/capture           入: holdId, actualAmountMicros, idempotencyKey, reason,
                                   featureKey, modelBindingId?, requestId?
                               出: { account, entry }(写 ledger 负 + usage settled，hold=captured)
POST /credit/release           入: holdId, idempotencyKey                    出: CreditHold(released)
POST /credit/spend             入: accountId, amountMicros, idempotencyKey, reason, requestId?
                               出: { account, entry }(直扣可用额，写负 ledger)
POST /credit/grant             入: accountId, amountMicros, idempotencyKey, reason, requestId?
                               出: { account, entry }(加余额)
```

注：quote / release 已实现但未登记在 module.ts 的 routes 清单内。

幂等 key：

```text
hold / capture / release / spend / grant   idempotencyKey(各表唯一约束兜底，冲突时回查并幂等返回)。
refund                                     无 standalone 操作；冲正以 grant(reason=refund)。
```

错误码(产品语言)：

```text
余额不足   hold / spend 原子条件命中 0 行 -> InsufficientCredit。
幂等冲突   idempotencyKey 命中唯一约束 -> 回查已有结果幂等返回。
状态非法   capture/release 时 hold 非 active -> CreditHoldNotActive。
未命中     holdId / PricingRule 不存在 -> NotFound。
```

## Admin 管理

```text
basePath  /admin/credits（manifest resources: accounts / ledger / usage / pricing）
resources accounts / ledger / usage / pricing(后续 holds / entitlements / spend-limits / manual-adjustments)
权限 key  credit.read / credit.write / credit.adjust
操作      手动发放、手动调整、查看 usage 和毛利。
审计      grant / spend / 手动调整应写审计(规划接入统一审计)。
```

注：上述读端点(ledger/usage 查询、余额查询、hold 列表)当前 HTTP 层尚未实现，为后台规划。

## 业务链路

```text
credit-reserve-commit-refund   扣费闭环核心(balance/held 模型)。
general-chat                   对话扣费。
music-studio-generate          长耗时 job 的 hold 一致性。
payment-to-credit              支付确认后 grant。
agent-handoff                  subagent 的 usage 归并到主 jobId。
```

## 部署

```text
服务名   kokoro-credit
端口     4231
env      DATABASE_URL_CREDIT, KOKORO_CREDIT_PORT, KOKORO_CREDIT_BASE_URL,
         KOKORO_USER_BASE_URL, KOKORO_MODEL_BASE_URL, KOKORO_PAYMENT_BASE_URL
多 Pod   无状态；余额/冻结/幂等状态只存 MySQL；hold/capture 走条件 UPDATE / 事务；
         不依赖分布式锁，用唯一索引 + 原子条件更新保证幂等与不超扣。
```

## 测试

```text
单测      quote 计价、micros 解析、原子条件分支。
集成      idempotencyKey 重试不重复扣、余额不足不能 hold/spend、
          capture/release 后余额正确、不同 owner 账户隔离。
反例      负数/超大额度、actual > hold、重复 capture、重复 release、
          支付确认仅通过 grant 发放一次。
门禁      涉及 schema/repository/API 时跑 test:integration。
```

## 风险和边界

```text
最容易乱：把价格、模型、套餐、扣费写在同一处。
禁止     payment / agent / model 直接写 credit 表。
禁止     绕过 credit service 改余额。
禁止     把账本放 Mongo、把余额放 Redis。
要求     所有余额变化只经 grant / spend / capture，且必须幂等。
要求     spend 只动可用额(不吃 held)，防止 capture 时出现负余额。
```

## 后续任务

```text
P0  standalone refund(反向关联原 ledger entry)、hold 过期自动回收(读 expiresAt)。
P1  Entitlement / SpendLimit、account disabled 状态强校验、读端点(余额/ledger/usage/hold 查询)。
P2  LiteLLM spend 对账、毛利报表、PricingRule 后台维护。
```
