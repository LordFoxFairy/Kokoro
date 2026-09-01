# Billing 旧 Credit/Payment 切换 Runbook

目标：在不丢失积分、支付和幂等事实的前提下，将 `kokoro-credit` / `kokoro-payment` 的写入收敛到
`kokoro-billing`。本文件是上线前操作门禁，不代表当前已切换。

> **范围：V1 legacy Credit/Payment 与 token/generic metering。**Feature-first GA 的按 `ModelInvocation` 次数扣积分不通过
> 本 runbook 的 `usage_price_revision` 或 `usage/settle` 上线；它必须先完成
> `AuthorizeModelInvocation / ModelInvocationAccepted / ReleaseModelInvocationHold` 的 contract/schema/caller cutover，
> 并验证 provider-unknown hold 的 reconciliation，再允许任何 GA Feature enforce。

旧 writer 的逐文件清单见 [`billing-old-writer-inventory.md`](billing-old-writer-inventory.md)。

## 0. 前置条件

1. Billing MySQL migrations 已应用至最新版本（当前 `0018-outbox-dead-letter`）。
2. Redis 用于幂等快速提示和 sweep leader lease；MySQL 是最终事实源。Lease 丢失只会导致重复尝试，不能导致账务错误。
3. 为每个 site 建立已发布 `usage_price_revision` 和 rate；没有价格时禁止启用 Session enforce。
4. 旧 Credit 与 Billing 使用同一租户映射：`site_id + owner_kind + owner_id` → `site_id + subject_id`。

运行时必须周期性执行 hold expiry job（Redis TTL 不是账务释放机制）：

```bash
DATABASE_URL=TARGET REDIS_URL=REDIS_TARGET pnpm db:expire-credit-holds
```

## 1. 数据迁移顺序

Billing 提供 guarded importer。默认执行只读盘点与 target shadow 对账，不写库：

```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-billing
DATABASE_URL=TARGET LEGACY_CREDIT_DATABASE_URL=SOURCE pnpm db:import-legacy-credit
```

迁移后必须运行只读全量对账；该命令逐 account 校验 projection、migration grant、journal、hold 和 active
allocation，不仅检查源表数量：

```bash
DATABASE_URL=TARGET LEGACY_CREDIT_DATABASE_URL=SOURCE pnpm db:audit-legacy-credit
```

只有报告零 drift 后才允许显式 apply；apply 使用 source fact 唯一键，可安全重跑：

```bash
DATABASE_URL=TARGET LEGACY_CREDIT_DATABASE_URL=SOURCE \
IMPORT_LEGACY_CREDIT_APPLY=true pnpm db:import-legacy-credit
```

`TARGET` 与 `SOURCE` 可以是同一个 MySQL 实例，但必须先完成 Billing migrations；导入器不会用 UPDATE
覆盖已有 Billing 余额，发现 target/legacy 不一致会终止并输出 drift。

### Credit

按 account 分批执行；每个 account 的事务提交后写入 `entitlement_command_receipt`
（`command_name = legacy_credit_import`），作为可重放的迁移 receipt；同一 idempotency key
若 payload hash 不一致，视为迁移冲突并终止，不静默覆盖：

1. `credit_accounts` → `entitlement_credit_account`；保留 `site_id`、owner、balance、held、quota、generation。
2. 旧 ledger 先落 `entitlement_credit_journal`，保持原始 entry id 作为 `source_ref`；opening balance 作为单独的
   `legacy_opening` grant/journal fact。
3. 每个账户建立一个可追溯的 `legacy_migration` grant lot，`remaining_micros` 必须等于旧 balance，不能直接
   写一个不可解释的 balance 修正。
4. active hold 迁移为 `entitlement_credit_hold + entitlement_credit_hold_allocation`；captured/released hold
   只作为历史事实保留，不允许再次参与可用额度计算。
5. `credit_pricing_rules` 映射为 Billing usage price revision/rate；无法判断旧 `unit` 是否为 token 计价时，
   标记为人工审核，不猜测换算比例。

### Payment

先执行只读 inventory，并对已有 target facts 做 shadow 对账，确认订单/套餐/退款没有孤儿：

```bash
LEGACY_PAYMENT_DATABASE_URL=SOURCE pnpm db:audit-legacy-payment
```

provider event 因旧表缺少 `site_id`，必须从可解析的订单关联或 provider account 映射补齐；subscription
必须映射为 provider subscription + period，不能把旧 subscription 直接伪装成一次性 settlement。inventory
报告未达到 ready 前，不执行 Payment apply。

当 inventory ready 后，执行受保护导入：

```bash
LEGACY_PAYMENT_DATABASE_URL=SOURCE pnpm db:audit-legacy-payment
DATABASE_URL=TARGET LEGACY_PAYMENT_DATABASE_URL=SOURCE \
LEGACY_PAYMENT_PROVIDER_SITE_MAP_JSON='{"mock":"SITE"}' \
LEGACY_PAYMENT_TEAM_SITE_MAP_JSON='{"TEAM":"SITE"}' \
IMPORT_LEGACY_PAYMENT_APPLY=true pnpm db:import-legacy-payment
```

Payment apply 后必须带上 `DATABASE_URL=TARGET` 再运行同一个 audit；此时审计会逐条核对 target 的 offer
revision、checkout、settlement、reversal、provider event、subscription binding 和 period，而不是只检查旧库孤儿数量。

导入器当前覆盖 legacy plan → offer/revision、order → checkout/settlement、succeeded refund → reversal；每个
Payment source fact 使用独立事务和 `payment_command_receipt`，保证 checkout/settlement、reversal、subscription
period 不会出现半笔导入；
provider event 与 subscription 在完成 site/period 映射前会阻止 apply。导入后的历史 settlement 不自动再次
发放积分，积分余额由 Credit importer 导入，避免重复 grant。

1. provider event 先导入 `payment_provider_event`，保留 raw payload 和外部 event id。
2. 已成功付款导入 `payment_settlement`，再通过 source fact 驱动 acquisition/fulfillment/grant。
3. refund 导入 `payment_reversal`；不得直接修改 grant remaining 或 account balance。

## 2. 对账 SQL 不变量

### 本地 fixture 验证记录

2026-08-22 已使用本地 MySQL fixture 执行两条迁移链路：

- Credit：legacy `kokoro` → target `kokoro_billing`，1 个 account、1 个 migration grant、2 个 hold，最终
  `status=ready`、`drifts=[]`；
- Payment：legacy `kokoro_payment_fixture` → target `kokoro_billing`，1 个 plan、1 个 checkout、1 个 settlement、
  1 个 reversal、1 个 provider event、1 个 subscription，导入后 source/target audit 均为 `status=ready`、`drifts=[]`。

这些结果证明 importer/audit 逻辑可运行，不等同于线上旧 writer 已停写；真实环境仍需用生产 legacy schema
重复执行 inventory、shadow audit 和 operator sign-off。

每个 site/subject 必须满足：

```text
Billing.available_micros + Billing.held_micros = SUM(entitlement_credit_grant.remaining_micros)
Billing.available_micros + Billing.held_micros = SUM(entitlement_credit_journal.amount_micros)
Billing.held_micros = SUM(entitlement_credit_hold.requested_micros WHERE status = 'active')
legacy.balance_micros = Billing.available_micros + Billing.held_micros
legacy.held_micros = Billing.held_micros
```

任何 drift 都进入 reconciliation queue；禁止用 UPDATE balance 的方式“修平”。

## 3. Shadow / enforce 切换

1. `shadow`：允许业务继续运行，但记录 target quote、hold、settle/release 结果和 legacy 对账结果；不把 Redis
   结果当作成功证明。
2. 连续完成规定观察窗口，且 purchase/refund/usage/webhook 重放无重复事实、无余额 drift 后，逐 site 开启
   `KOKORO_BILLING_BASE_URL`。
3. 再将 `KOKORO_BILLING_MODE` 切为 `enforce`；缺价、Billing 不可达、未知 committed exposure 均 fail closed
   并进入 reconcile。
4. 保留旧只读查询作为 rollback window，但关闭旧 grant/spend/hold/settle writer；rollback 只能切回读面，不能
   恢复双写。

## 4. 关闭条件

- 所有 consumer manifest 状态为 `migrated-*`；
- old writer inventory 为空；
- Billing reconcile 连续零 drift；
- Redis 清空、重复 webhook、worker 崩溃、DB 重试均能由 MySQL source fact 恢复；
- operator 完成 rollback exercise 并签字。
