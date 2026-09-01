# kokoro-credit 历史技术方案

> 迁移状态：历史 runtime。新积分、权益和计量能力进入 `kokoro-billing` 的 Entitlement/Credit Context；
> 详见 [`technical/31-billing-subrepository-architecture.md`](../technical/31-billing-subrepository-architecture.md)。

> 执行级设计以 [Credit 设计卡](../technical/backend-design/03-credit.md) 为准。

## 定位

kokoro-credit 是积分账户、冻结、账本、usage、pricing rule 和扣费闭环的唯一权威。

不是支付收单方，不是模型路由方，不是任务执行方。它只回答"账户有多少、使用时扣多少、扣了多少"。

当前实现状态：本文只记录已废弃独立 `kokoro-credit` 原型的历史行为，不是当前实现入口。新 Credit account、grant、spend、refund、quote、pricing、hold、capture、release、usage settle、quota、admin 和过期处理均归 `kokoro-billing`；当前账务事实使用 PostgreSQL，Redis 只承担幂等快路径与协调。

## 业务职责

owns：

```text
  CreditAccount      积分账户(balanceMicros + heldMicros)，附带 period quota 与 reserved hold window。
CreditHold         扣费前的冻结。
CreditLedgerEntry  唯一权威账本流水。
UsageRecord        一次能力使用记录。
PricingRule        featureKey(+labelKey)单位定价。
Entitlement        权益(规划，未实现)。
SpendLimit         消费上限(规划，未实现)。
```

does not own：

```text
支付订单和确认（kokoro-billing 的 Payment context）。
模型 provider 路由和价格上限(kokoro-model 只给成本参考)。
用户身份和权限(kokoro-iam)。
agent 任务执行(kokoro-agent)。
```

## 上游和下游

```text
上游(调用 credit)：
  kokoro-agent     quote / hold / capture / release / spend。
  kokoro-billing   checkout/webhook/fulfillment 时 ensure + grant 积分。

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
  expiresAt 由 admin sweep 处理；sweep 与 capture/release 通过行锁竞争，只有一个状态转移成功。

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
Mongo / Object Storage：不使用。Redis：运行依赖，仅用于短期 mutation cache、lease 和协调；账务严禁放 Redis。
外部系统：无。
```

## API / RPC / Events

已实现：

```text
GET  /healthz                  liveness
GET  /readyz                   MySQL + Redis readiness
POST /credit/accounts/ensure   ensure account
POST /credit/quote             quote pricing
POST /credit/holds             create hold
POST /credit/holds/:id/capture capture only
POST /credit/holds/:id/release release only
POST /credit/usage/settle      atomic capture + ledger + settled usage, or release for zero usage
POST /credit/usage             record usage
POST /credit/spend             direct spend with quota enforcement
POST /credit/grant             grant balance
POST /credit/refund            positive reversal grant
GET  /credit/accounts/:id/ledger
GET  /credit/accounts/:id/usage
```

注：quote / release 已实现但未登记在 module.ts 的 routes 清单内。

幂等 key：

```text
hold / capture / release / spend / grant   idempotencyKey(各表唯一约束兜底，冲突时回查并幂等返回)。
refund                                     独立 refund mutation，使用自己的 ledger operation/key。
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
审计      grant / spend / refund / hold 生命周期 / usage settle 写入 Credit audit events；统一外部审计事件仍由平台编排。
```

注：runtime-internal 只读窄读面(余额+活跃 holds 聚合、ledger 分页)已落地(WEB-BILLING,credit 5986941)，经 session /billing/* 代理服务 web;admin 全量审计读面见 /admin/credits/*。

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
端口     4231（KOKORO_CREDIT_PORT）
env      DATABASE_URL, REDIS_URL, KOKORO_CREDIT_HOST, KOKORO_CREDIT_PORT
多 Pod   无状态；余额/冻结/幂等状态只存 MySQL；hold/capture 走条件 UPDATE / 事务；
         Redis lease 只用于协调，MySQL 唯一索引 + InnoDB 行锁 + 原子条件更新保证幂等与不超扣。
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
P0  account/hold 查询分页、账务对账报表和统一外部审计事件。
P1  生产告警规则、指标持久化与审计归档策略。
P2  Entitlement / SpendLimit 等产品层策略（不回写 Credit 账本模型）。
```
