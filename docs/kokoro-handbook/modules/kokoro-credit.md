# kokoro-credit 技术方案

## 定位

kokoro-credit 是积分账户、冻结、账本、usage、pricing rule、权益和扣费闭环的唯一权威。

不是支付收单方，不是模型路由方，不是任务执行方。它只回答"到账什么权益、使用时扣多少、扣了多少"。

## 业务职责

owns：

```text
CreditAccount      站点内积分账户。
CreditBucket       额度来源桶（试用/赠送/订阅/充值/退款/管理员发放）。
CreditHold         扣费前的冻结。
CreditLedgerEntry  唯一权威账本流水。
UsageRecord        一次能力使用记录。
PricingRule        capability 单位定价。
Entitlement        权益（可用功能、额度、并发）。
SpendLimit         消费上限。
```

does not own：

```text
支付订单和 capture（kokoro-payment）。
模型 provider 路由和价格上限（kokoro-model 只给成本参考）。
用户身份和权限（kokoro-user）。
agent 任务执行（kokoro-agent）。
```

## 上游和下游

```text
上游（调用 credit）：
  kokoro-agent     quote / hold / commit / release。
  kokoro-payment   支付成功后 grant 积分和权益。

下游（credit 调用）：
  kokoro-site      消费 siteId / SiteContext。
  kokoro-model     取模型成本参考（不取价格）。
```

## 核心对象

```text
CreditAccount
  siteId + ownerKind(user|workspace) + ownerId，balanceMicros。

CreditBucket
  source = free_trial | free_monthly | subscription | topup | admin_grant | refund
  originalMicros / remainingMicros / expiresAt / priority / sourceRefType / sourceRefId。

CreditHold
  状态 active | captured | released | expired，带 idempotencyKey 和 expiresAt。

CreditLedgerEntry
  amountMicros 可负（消费）可正（发放/退款），balanceAfterMicros，reason，bucketId。

UsageRecord
  featureKey + modelBindingId + quantity/unit + amountMicros，状态 quoted | held | settled | failed。
```

生命周期（扣费闭环）：

```text
quote -> hold -> execute -> commit(capture) -> ledger + usage
                      \-> release(失败/取消/超时)
settled -> refund(可选，反向 ledger + refund bucket)
```

扣费顺序（默认，按 bucket）：

```text
1. 当前 site 即将过期的 free_trial / free_monthly
2. 当前 site 当前周期的 subscription
3. 当前 site 的 topup
4. 当前 site 的 admin_grant / refund
```

## 数据模型

MySQL（权威，必须事务）：

```text
credit_accounts          unique(siteId, ownerKind, ownerId)
credit_buckets           siteId + accountId + source
credit_holds             unique(siteId, accountId, idempotencyKey)
credit_ledger_entries    unique(siteId, accountId, idempotencyKey)
credit_usage_records     siteId + jobId + featureKey
credit_pricing_rules     siteId + featureKey (+ modelLabel)
```

其它存储：

```text
Mongo / Redis / Object Storage：不使用（账务严禁放 Mongo，余额严禁放 Redis）。
外部系统：无。LiteLLM spend 只做护栏，对账后仍以本账本为准。
```

## API / RPC / Events

```text
POST /credit/accounts/ensure
POST /credit/quote     入: siteId, workspaceId, featureKey, modelBindingId/plan, quantity
                       出: estimateMicros, bucketBreakdown（无副作用）
POST /credit/hold      入: siteId, accountId, amountMicros, idempotencyKey, expiresAt
                       出: CreditHold(active)
POST /credit/capture   入: siteId, holdId, actualAmountMicros, idempotencyKey
                       出: CreditLedgerEntry（写 ledger + usage，hold=captured）
POST /credit/release   入: siteId, holdId, idempotencyKey（不写 ledger，恢复额度）
POST /credit/grant     入: siteId, accountId, amountMicros, bucketSource, sourceRefId, idempotencyKey
POST /credit/refund    入: siteId, ledgerEntryId, amountMicros, reason, idempotencyKey
```

幂等 key：

```text
hold / capture / release / grant   idempotencyKey（唯一约束兜底）
refund                             original ledgerEntryId + idempotencyKey
```

错误码（产品语言）：

```text
402 余额不足（hold 失败）。
409 idempotencyKey 冲突（幂等返回已有结果）。
404 holdId / ledgerEntryId 不存在。
```

## Admin 管理

```text
basePath  /admin/credit
resources accounts / ledger / usage / pricing-rules（后续 holds / entitlements / spend-limits / manual-adjustments）
权限 key  credit.read / credit.write / credit.adjust
操作      手动发放、手动调整、退款、查看 usage 和毛利。
审计      所有 grant / spend / refund / manual adjustment 必须写审计。
```

后台查询默认带 siteId，仅 platform root admin 可跨站查询。

## 业务链路

```text
credit-reserve-commit-refund   扣费闭环核心。
general-chat                   对话扣费。
music-studio-generate          长耗时 job 的 hold 一致性。
payment-to-credit              支付成功后 grant。
agent-handoff                  subagent 的 usage 归并到主 jobId。
```

## 部署

```text
服务名   kokoro-credit
端口     4231
env      DATABASE_URL_CREDIT, KOKORO_CREDIT_PORT, KOKORO_CREDIT_BASE_URL,
         KOKORO_SITE_BASE_URL, KOKORO_MODEL_BASE_URL
多 Pod   无状态；余额/冻结/幂等状态只存 MySQL；hold/capture 必须 DB 事务；
         不依赖分布式锁，用唯一索引 + 乐观锁保证幂等。
```

## 测试

```text
单测      bucket 选择顺序、quote 计算、micros 解析。
集成      idempotencyKey 重试不重复扣、余额不足不能 hold、
          capture/release 后余额正确、不同 site 账户隔离。
反例      负数/超大额度、过期 hold、重复 capture、重复 refund、
          payment 成功仅通过 grant 发放一次。
门禁      涉及 schema/repository/API 时跑 test:integration。
```

## 风险和边界

```text
最容易乱：把价格、模型、套餐、扣费写在同一处。
禁止     payment / agent / model 直接写 credit 表。
禁止     绕过 credit service 改余额。
禁止     把账本放 Mongo、把余额放 Redis。
要求     所有余额变化只经 grant / spend，且必须幂等。
要求     套餐权益（entitlement）与积分（bucket）边界清晰分离。
```

## 后续任务

```text
P0  site 化改造、hold/commit/release 完整流程、幂等反例测试。
P1  多 Pod 下的乐观锁设计、entitlement/spend limit。
P2  LiteLLM spend 对账、毛利报表。
```
