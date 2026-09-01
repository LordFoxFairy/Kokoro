# `kokoro-credit` 设计卡

> 历史设计卡：新能力以 [`05-billing.md`](05-billing.md)、
> [`../31-billing-subrepository-architecture.md`](../31-billing-subrepository-architecture.md) 和
> [`../billing-transaction-matrix.md`](../billing-transaction-matrix.md) 为准。
> `kokoro-credit` 进入迁移态，目标 owner 是 `kokoro-billing` 的 Entitlement/Credit Context。

状态：目标设计与独立仓库执行基线，2026-08-22

本卡是 [`27-final-backend-architecture.md`](../27-final-backend-architecture.md) 对 Credit 的执行级展开。当前唯一 runtime writer 是独立仓库 `kokoro-credit`；`kokoro-platform/kokoro-credit` 已删除，仅保留迁移历史。

## 1. 定位与边界

`kokoro-credit` 是积分账户、可用余额、冻结、结算、释放、账本和用量的唯一 owner，也是这些数据的唯一 runtime writer。

拥有：

- `CreditAccount`：按 `(siteId, ownerKind, ownerId)` 唯一定位的账户；
- `CreditHold`：一次预授权及其生命周期；
- `CreditLedgerEntry`：不可变的余额变更事实；
- `UsageRecord`：已结算/失败的用量事实；
- `PricingRule` 与 `Quote`：Credit 负责计价和报价；
- grant、spend、hold、capture、release、usage settle 的幂等状态。

不拥有：

- 用户、组织、site、namespace 的身份与授权；
- 套餐、订单、支付 provider、订阅生命周期；
- 模型目录、模型路由和 provider 健康状态；
- Agent 执行状态、Session 消息和浏览器 SSE；
- 任何其他仓库的业务表或 Prisma/ORM model。

上游只能通过公开 command/query contract 调用。Payment 的购买成功通过 `GrantCredit` 发放积分；Model 只提供外部模型标识和成本输入；Agent/Session 只能发起 quote/hold/capture/release/usage settle，不得写 Credit 表。

## 2. 复杂度等级与领域模型

等级：**L2 标准战术 DDD**。

选择理由：余额不变量、并发条件更新、冻结状态机、不可变账本、跨表事务和幂等重放共同决定正确性，不能按表生成 CRUD service。

### 2.1 聚合与事务边界

| 聚合/事实 | 保护的不变量 | 写入边界 |
|---|---|---|
| `CreditAccount` | 金额非负；`available = balance - held`；账户状态可用 | 账户行条件更新；与 Hold/Ledger 同事务 |
| `CreditHold` | active 只能转为 captured/released/expired 一次；capture 不得超过 hold | Hold 行条件更新；与账户及账本同事务 |
| `CreditLedgerEntry` | append-only；每次余额变化恰有一条分录；幂等键唯一 | 只由 Credit 写入，禁止 update/delete |
| `UsageRecord` | settle/retry 幂等；金额与 capture 结果一致 | 与 capture 同事务，或由显式失败命令写入 |
| `PricingRule` | 同一时间点只能选择确定的有效规则；历史规则可审计 | Credit pricing module 独占 |

Account 与 Hold 的余额变更必须在同一数据库事务完成。Ledger 是事实记录，不是用来反推并发余额的锁；当前余额由 Account 条件更新维护，Ledger 用于审计和对账。

### 2.2 命令

```text
EnsureAccount
GrantCredit
SpendCredit
CreateHold
CaptureHold
ReleaseHold
ExpireHold
SettleUsage
CreateQuote
RecordUsageFailure
```

所有副作用命令都需要调用方提供 `idempotencyKey`。同一 key 必须返回第一次成功结果；同一 key 配置不同 payload 必须返回幂等冲突，而不是执行第二次操作。

## 3. 核心不变量与状态机

金额统一使用非负整数 `micros`，跨 JSON/HTTP 序列化为十进制字符串；金额单位转换不使用浮点数。

```text
available = balanceMicros - heldMicros
balanceMicros >= 0
heldMicros >= 0
heldMicros <= balanceMicros
hold.amountMicros > 0
hold.reserved amounts sum to hold.amountMicros
```

生命周期：

```text
active -> captured
active -> released
active -> expired
captured / released / expired -> terminal（不可再写）
```

操作规则：

1. `hold` 只在 `status=active` 且 `balance - held >= amount` 时增加 `held` 并创建 active hold。
2. `capture` 只接受 `0 < actual <= hold.amount`；账户扣除实际金额，同时释放整笔 held；差额回到 available；写一条负 ledger 和一条 settled usage。
3. `release` 不写 ledger，只减少 held；重复 release 返回原结果。
4. `expire` 等同 release，但只有到期的 active hold 可执行；sweeper 与显式 release 竞争时只有一个成功。
5. `spend` 只扣 available，不得消耗其他 hold；成功必须同时写负 ledger。
6. `grant` 增加余额并写正 ledger；Payment 不得直接插入 ledger。
7. 每次余额变化必须与 ledger 在同一事务提交；事务失败时两者都不可见。

## 4. 数据 owner 与目标持久化

Credit 独立仓库维护运行时 MySQL schema 与 numbered migrations；Root 维护跨仓 owner/contract/baseline 清单。Credit 是以下表的业务 owner 和唯一 runtime writer：

```text
credit_accounts
credit_holds
credit_ledger_entries
credit_usage_records
credit_pricing_rules
```

目标数据库为 MySQL 8/InnoDB。逻辑字段至少包括：

- account：`id, site_id, owner_kind, owner_id, status, balance_micros, held_micros, version, created_at, updated_at`；
- hold：`id, account_id, amount_micros, status, idempotency_key, expires_at, pricing_ref, request_id, timestamps`；
- ledger：`id, account_id, signed_amount_micros, balance_after_micros, operation, idempotency_key, request_id, created_at`；
- usage：`id, account_id, hold_id, feature_key, measured_usage, amount_micros, status, idempotency_key, created_at`；
- pricing：`id, feature_key, label_key, unit, unit_amount_micros, effective_from, effective_until, status`。

必须有：

```text
UNIQUE(account.site_id, owner_kind, owner_id)
UNIQUE(hold.idempotency_key)
UNIQUE(ledger.idempotency_key)
UNIQUE(usage.idempotency_key)                 -- nullable only for non-metered records
CHECK(account.balance_micros >= 0)
CHECK(account.held_micros >= 0)
CHECK(account.held_micros <= account.balance_micros)
CHECK(hold.amount_micros > 0)
```

具体 SQL 位于 `kokoro-credit/database/schema.sql`，增量迁移位于 `kokoro-credit/database/migrations/`；`db:apply` 记录 checksum，Credit repository 不使用 Prisma/ORM。

## 5. 并发与幂等实现约束

`hold`/`spend` 使用带条件的单条 `UPDATE ... WHERE`，根据 affected rows 判断余额不足。`capture`/`release`/`expire` 使用事务内的 `UPDATE ... WHERE status='active'`，只有成功抢到状态转移的事务继续修改账户和写分录。

推荐事务顺序：`lock account -> lock hold -> validate -> update account -> insert ledger/usage -> commit`。所有数据库错误必须回滚；不得用进程内 mutex、缓存余额或 Redis 作为真源。

幂等读取顺序：先按 key 查询成功结果；不存在时进入事务并依赖唯一约束兜底；唯一冲突后重新读取并返回已提交结果。payload hash 不一致返回 `idempotency_conflict`。

## 6. 公开契约与入口

跨仓 contract 的唯一源是 Root `contract/`。Credit 生成类型放 `src/generated/`，不得手改生成文件。

最小公开 command/query 面：

```text
POST /credit/accounts/ensure
POST /credit/quote
POST /credit/grant
POST /credit/spend
POST /credit/holds
POST /credit/holds/{holdId}/capture
POST /credit/holds/{holdId}/release
POST /credit/usage/settle
GET  /credit/accounts/{accountId}
GET  /credit/accounts/{accountId}/ledger
```

HTTP 只是入口；内部 RPC/worker 入口复用同一 application command，不复制领域逻辑。边界 schema 必须拒绝未知字段，`siteId`、`namespace`、owner、金额和幂等 key 必须显式校验。Credit 使用 `siteId` 作为业务隔离上下文；Agent 侧只接收上游解析后的 opaque `namespace`，Credit 可将其映射为 team account，但不得把身份语义传播到 Agent。

## 7. 当前目录

```text
kokoro-credit/
├── src/
│   ├── modules/
│   │   ├── account/       聚合、账户查询和状态
│   │   ├── credit/        CreditMutationPort 与 view/input 类型
│   │   ├── hold/          创建、capture、release、settle 编排
│   │   ├── pricing/       pricing 选择与报价
│   │   ├── usage/         usage 查询边界
│   │   └── admin/         stats、quota、生命周期
│   ├── interfaces/{rpc,http,admin}/
│   ├── infrastructure/mysql/  Credit/Hold repository、事务和 adapter
│   ├── infrastructure/redis/  cache、lease、fail-open coordination
│   ├── generated/
│   ├── config/
│   ├── bootstrap/
│   └── main.ts
├── test/{unit,integration,contract,architecture}/
└── docs/{README.md,INDEX.md}
```

依赖方向：`interfaces -> application/use case -> domain`；`infrastructure -> domain ports`；`bootstrap/main -> concrete adapters`。任何模块不得导入其他模块的数据库 row、repository 实现或私有 symbol。

## 8. 测试

### Unit

- 金额解析、非负约束和整数换算；
- hold/capture/release 状态转移；
- capture 差额回可用、超额拒绝；
- 计价规则选择、数量边界和 usage 计算；
- 幂等 payload hash 冲突。

### Integration（真实 MySQL）

- 两个并发 hold 不得突破 available；
- spend 不得吃 held；
- 并发 capture/release 只有一个状态转移成功；
- 重放每个 command N 次只产生一次余额变化和一次 ledger；
- 事务失败时 account、hold、ledger、usage 一起回滚；
- 过期 sweep 与显式 release 的竞争；
- 不同 site/owner 账户隔离。

### Contract / architecture

- 生成物与 Root contract 一致；
- Payment 只能调用 grant command；
- Model/Agent/Session 不得 import Credit infrastructure 或写表；
- schema owner 与 runtime writer 清单一致；
- 旧 Prisma/MySQL 入口和 `kokoro-platform` registry 不再成为最终运行入口。

## 100 分证据

- `hold/capture/release` 有真实 MySQL 并发测试；
- 条件 UPDATE、唯一幂等键和 ledger 约束同时存在；
- Domain 行为不依赖 Prisma；
- Payment 只能通过公开 command grant，不可跨表写入；
- 失败、重复、超额和版本冲突路径全部覆盖。

## 9. 当前实现与迁移步骤

当前证据位于独立仓库 `kokoro-credit`：已完成 MySQL/InnoDB account/grant/spend/refund/quote/pricing、Hold 生命周期、原子 SettleUsage、usage、quota、admin、Redis coordinator、HTTP、真实依赖集成测试和 migration runner；root contract consumer 已切换到 external Credit service。

迁移按完整用例推进：

1. Root `database/` 登记 Credit 表 owner、字段、唯一约束和 baseline；独立仓库维护执行迁移。
2. Root `contract/` 固化 grant、hold、capture、release、usage settle 的 command/result/error schema，并生成 Credit 类型。
3. ✅ 建立独立 `kokoro-credit` 目标目录、`INDEX.md`、MySQL/Redis adapter 和 architecture tests。
4. ✅ 完成 `CreateHold -> CaptureHold/ReleaseHold` 及真实并发测试。
5. ✅ 完成 grant/spend/refund/quote/pricing/usage/admin，补齐 quota 和 settle 原子事务。
6. ✅ Payment 通过 external Credit contract 调用，禁止跨表写入。
7. ✅ 完成 quota window reset、sweeper 调度、reconciliation、audit events 和 Prometheus metrics；继续补生产告警、审计归档与分页读面。
8. ✅ 删除旧 Prisma/MySQL writer、旧 registry 注入和兼容入口。

当前 slice 的运行时能力与验证门禁已满足；全平台上线仍需生产部署、告警、审计归档和消费者切换证据，不能把当前测试绿灯扩大解释为全平台上线完成。

## 10. 现阶段明确决策

- Credit 使用 L2，但不把所有实现机械拆成空目录；只有承担独立规则的模块保留目录。
- 账本 append-only；退款是新的正向 grant/reversal command，不更新历史分录。
- Payment 拥有购买事实，Credit 拥有授信结果；两者通过幂等 command 解耦。
- Model 提供成本输入或 binding 标识，Credit 决定计价；两者不共享数据库表。
- 可过期额度/多桶规则若继续保留，必须进入 Credit domain 并由真实 MySQL 测试证明；不能只留在旧 Prisma 注释或 adapter 中。
