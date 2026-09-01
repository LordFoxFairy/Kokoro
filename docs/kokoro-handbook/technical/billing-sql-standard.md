# Billing SQL 规范

> Clean-build 目标规范。现有 `kokoro-billing/database/migrations` 属于未上线探索代码，不是本规范的目标 schema；新实现按 50 重新建库，不保留旧表名、旧字段或兼容入口。

## 1. 数据库基础

应用运行时使用 MySQL pool；每个 application transaction 必须在独立物理 session 上完成，不能让并发 HTTP
请求共享一个事务连接。请求/worker 入口通过数据库 context 绑定事务 session；migration runner 例外地使用
专用连接维持 `GET_LOCK` 和 DDL session。

- MySQL 8.4、InnoDB、`utf8mb4`、`utf8mb4_0900_ai_ci`。
- 表按 bounded context 使用 `entitlement_*` / `payment_*` 前缀；表名、列名、索引名使用 snake_case。
- 表名采用“bounded-context owner + aggregate/fact”命名，按语义需要使用两段或多段 snake_case，而不是按仓库名命名：`entitlement_credit_grant` 表示 Entitlement owner 下 Credit 子域的 Grant fact；`payment_settlement` 表示 Payment owner 下的 Settlement fact；`entitlement_credit_hold_allocation` 表示 Hold 与 Grant 之间的分配关系。禁止为了凑段数重复表达同一 owner，也禁止为了缩短名称丢失关系语义。
- 迁移文件名统一为 `NNNN-kebab-case.sql`；CI 的 `pnpm sql:check` 检查 bounded-context 表名、约束名和索引名，防止新增重复 owner 前缀或非 snake_case 标识符。
- `entitlement_credit_grant` 保留 `grant` 而不改成 `credit_bucket`/`credit_balance`：它代表一笔可追溯、可过期、可撤销、按来源隔离的 credit lot；账户余额是 projection，不能成为 grant 的替代命名或事实表。
- 不省略 owner 前缀，也不把相邻关系拼进主表名：分配关系单独命名为 `entitlement_credit_hold_allocation`。同一命名规则下，`entitlement_entitlement_grant` 属于重复前缀错误，禁止出现。
- 主键统一 `CHAR(36)` UUID；跨 JSON/HTTP 的金额和计数统一十进制字符串。
- 对外租户标识统一使用 `tenantId`；全新数据库统一使用 `tenant_id VARCHAR(191) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin`，不创建 `site_id` 兼容列，不把 opaque tenant 强制收窄成 UUID `CHAR(36)`。
- 金额字段使用 `BIGINT`，绝不使用 `FLOAT`、`DOUBLE` 或 `DECIMAL` 承担 micros 计费事实。
- 所有外部支付/退款/订阅引用都必须带 provider namespace；唯一性使用 `(tenant_id, provider, external_*_ref)`，不能假设不同支付渠道的外部编号全局唯一。
- MySQL 驱动连接统一开启 `supportBigNumbers=true` 与 `bigNumberStrings=true`，在驱动边界将 `BIGINT` 保留为十进制字符串；只有经过 `Number.isSafeInteger` 保护的值才允许转换为 JavaScript `number`，否则使用 `BigInt`。
- 时间统一 `DATETIME(6)` UTC；代码层禁止使用本地时区计算账期。
- `metadata`/provider payload 使用 JSON，只作为不可变快照或非关键扩展字段，不把可查询业务字段藏在 JSON。
- 幂等 receipt 按 bounded context 归属：Catalog/Credit/Entitlement command 使用 `entitlement_command_receipt`，Payment
  command（包括 Admin refund、provider event retry）使用 `payment_command_receipt`；不因为同库就跨 owner 复用 receipt 表。当前 command 都在单个 MySQL
  transaction 内完成，`lease_until` 仅为未来确有异步长事务的 command 预留，不把未实现的 lease recovery 写成现状。

## 2. 状态与删除

- 不使用 MySQL `ENUM` 作为业务状态；使用 `VARCHAR(32)` + `CHECK`，便于未来 schema 演进。
- 订单、支付事件、退款、权益和钱包 hold 的终态禁止物理删除。
- Credit journal、allocation、audit event append-only；provider event 的原始 payload、外部 id 和 site 归属不可变，但允许更新 `processing_status`、`processed_at`、`processing_attempts`、`last_error` 等处理投影；终态事实禁止 DELETE。
- 可运营资源使用 `deleted_at/deleted_by/delete_reason`，并保留唯一键策略和恢复规则。
- 所有表必须有 `created_at`；可变表增加 `updated_at`；事件表保留 `processed_at`/`last_error`。

## 3. 金额与关系

```text
credit account gross balance = available_micros + held_micros
credit account available balance = gross balance - held_micros
credit account available projection = SUM(credit grant remaining) - active hold allocations
credit account gross projection = available_micros + held_micros = SUM(credit grant remaining)
ledger amount_micros: signed BIGINT
grant/hold/usage amount_micros: non-negative BIGINT
available_micros is the spendable projection; held_micros is reserved separately. A fully reserved account may
therefore have `available_micros = 0` and `held_micros > 0`.
```

购买金额（minor currency unit）与产品积分（credit micros）是不同字段、不同单位，禁止混用。

财务事实禁止 `ON DELETE CASCADE`。外键只用于阻止孤儿记录；撤销、退款、过期均通过新事实记录完成。

## 4. 索引

- 多租户查询索引以 `tenant_id` 或明确的 owner/account 列作为前导列。
- 预算/时间窗口查询必须有复合索引，例如 `(account_id, created_at, id)`、`(status, expires_at, id)`。
- 幂等事件必须有唯一键：按租户隔离的 `(tenant_id, provider, external_event_id)`、`(tenant_id, command_name, idempotency_key)`；业务 source fact 还必须有 `(tenant_id, source_kind, source_ref, entry_kind)` 等稳定唯一约束。
- 每条高频查询在 migration review 中提供 `EXPLAIN` 证据；不能只按 ORM 自动索引。
- credit grant 消耗必须覆盖 `(credit_account_id, status, expires_at, burn_priority, credit_grant_id)`。

## 5. 事务与 schema versioning

- schema version 只前进、不提供 down migration；未来破坏性变更拆成 expand -> backfill -> contract；当前 clean build 不包含旧数据回填。
- 每个 numbered migration 写入 `billing_schema_migrations(version, checksum, applied_at)`；该表是仓库迁移元数据，不属于 Payment 或 Entitlement 业务事实。
- DDL 与数据回填分开；大表回填必须批次化、可恢复、限速。
- 任何余额、hold、allocation、ledger 变化必须在同一 MySQL transaction 提交。
- Payment 不把外部 provider 网络调用放进事务；只写 `payment_provider_event`/`payment_outbox`，由 worker
  产生 `payment_settlement`，再通过稳定 source ref 触发 Entitlement Acquisition/Fulfillment。
- provider 网络调用、Redis 调用、消息发送不得放进 MySQL transaction；只写 outbox 后异步执行。
- SQL 使用参数绑定；禁止字符串拼接用户输入；所有连接设置超时和事务隔离级别。

## 6. 审计与对账

至少提供以下 reconcile：

1. payment settlement 与 entitlement acquisition/fulfillment 状态；
2. fulfillment 与 entitlement/credit grant；
3. CreditGrant remaining 与 HoldAllocation/consumption allocation；
4. CreditAccount projection 与 signed CreditJournal；
5. active CreditHold 与 HoldAllocation；
6. provider event 与 payment/refund/dispute terminal state。

Reconciliation API 必须同时暴露 account、settlement→fulfillment、reversal→fulfillment reversal 和 failed provider
event 四类 drift；不能只统计余额 projection，否则支付链路可能出现“已收款但未发放”或“已退款但未逆向”的盲区。

任何 drift 都必须可按 `tenant_id + account_id + order_id + provider_event_id + request_id` 定位，禁止直接
修正余额绕过 ledger。
