# Billing MySQL Schema v1

> **状态：V1 token 计量物理基线。**本 schema 描述当前 `kokoro-billing` MySQL 物理模型；其中 `subject_id`、
> `input_micros_per_million` 与 `output_micros_per_million` 不是 Feature-first GA 的目标计费模型。目标以
> [31 Billing 子仓架构](31-billing-subrepository-architecture.md#从现有-token-计量面切换的硬门) 为准：
> `ModelInvocation` 按次扣积分，token 只保留 provider-cost diagnostics。

> 目标数据库：MySQL 8.4。本文是 `kokoro-billing` 的逻辑 schema，不替代 migration；所有业务表必须按 `billing-sql-standard.md` 生成 numbered migration。

## 1. 通用列与类型

- 主键：应用生成 UUID，使用 `CHAR(36)`；高写入事件表可采用 `BINARY(16)`，但仓库内必须统一转换层。
- 租户隔离键：对外是 IAM opaque `tenantId`；内部兼容列仍名为 `site_id`，使用 `VARCHAR(191) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin`，不能使用 `CHAR(36)` 假设租户一定是 UUID。迁移 `0024-tenant-id-width` 负责从历史宽度扩展。
- 金额/积分：`BIGINT` 最小单位，禁止 `FLOAT`/`DOUBLE`/金额 `DECIMAL` 混用。
- `credit_account.available_micros` 是扣除 active hold 后的可用余额；`held_micros` 独立记录冻结额，允许账户全部余额处于 hold 中。
- 时间：UTC `DATETIME(6)`；禁止依赖数据库 session timezone。
- 状态：`VARCHAR(32)` + `CHECK`，不使用 MySQL `ENUM`，便于前向兼容。
- Projection/可变聚合表按需使用 `created_at`、`updated_at`、`generation`；事实表追加后不可 UPDATE 业务含义。
- 租户 lineage：`site_id` 必须出现在所有跨租户可见表，并参与必要的复合 FK/唯一键；`0026` 保护 hold allocation，
  `0027` 将 account、grant、hold、journal、fulfillment、usage、payment、subscription 等 tenant-owned relation
  全部收敛到 `(site_id, id)` 复合外键；`0029` 补齐 checkout → offer revision 的复合外键。

## 2. Entitlement/Credit 表

| 表 | 关键列 | 约束/用途 |
|---|---|---|
| `entitlement_credit_account` | `credit_account_id`, `site_id`, `subject_id`, `available_micros`, `held_micros`, `quota_micros`, `quota_period`, `generation` | `(site_id, subject_id)` 唯一；projection，可重建；quota 只作为账户策略读面，不参与 grant 事实 |
| `entitlement_credit_grant` | `credit_grant_id`, `credit_account_id`, `source_kind`, `source_ref`, `original_micros`, `remaining_micros`, `effective_at`, `expires_at`, `burn_priority`, `status` | `(site_id, source_kind, source_ref, program_key)` 唯一；消费排序为 `expires_at ASC NULLS LAST, burn_priority ASC, issued_at ASC, credit_grant_id ASC`；subscription period grant 的 `expires_at` 等于 provider period end |
| `entitlement_credit_hold` | `credit_hold_id`, `credit_account_id`, `idempotency_key`, `requested_micros`, `status`, `expires_at` | `(site_id, idempotency_key)` 唯一；重放会比较 account、金额、feature、label、model 和 pricing revision；锁定后才能分配 |
| `entitlement_credit_hold_allocation` | `credit_hold_id`, `site_id`, `credit_grant_id`, `held_micros`, `captured_micros`, `released_micros` | `(hold_id, grant_id)` 唯一；通过 `(site_id, hold_id)` 与 `(site_id, grant_id)` 复合 FK 防止跨租户 allocation |
| `entitlement_credit_journal` | `journal_id`, `credit_account_id`, `entry_kind`, `amount_micros`, `source_kind`, `source_ref`, `journal_seq` | `(credit_account_id, journal_seq)` 唯一；append-only；借贷方向由 entry kind 明确 |
| `entitlement_usage_event` | `usage_event_id`, `site_id`, `subject_id`, `source_event_id`, `dimensions_json`, `quantity_micros` | source event 唯一且 payload 变化冲突；只记录观测事实 |
| `entitlement_usage_settlement` | `usage_settlement_id`, `credit_hold_id`, `usage_event_id`, `actual_micros`, `status` | hold 与 usage event 各唯一；关联 capture/release 与 journal |
| `entitlement_acquisition` | `acquisition_id`, `site_id`, `subject_id`, `source_kind`, `source_ref`, `program_key`, `quantity_micros` | Payment settlement、redemption 等 acquisition source 的统一事实；source/program 唯一 |
| `entitlement_fulfillment` | `fulfillment_id`, `acquisition_id`, `status`, `committed_at` | 一次 acquisition 最多一次 fulfillment；`committed` 才触发 grant |
| `entitlement_command_receipt` | `receipt_id`, `site_id`, `command_name`, `idempotency_key`, `payload_hash`, `status`, `result_json`, `lease_until` | Entitlement/Credit command 幂等、重放与冲突检测；当前 command 在单事务内完成 |
| `entitlement_audit_event` | `audit_event_id`, `site_id`, `operator_id`, `action`, `subject_id`, `resource_type`, `resource_id`, `reason`, `payload_json` | Admin grant/refund/replay 等高权限操作追加事实 |
| `entitlement_outbox` | `outbox_id`, `aggregate_type`, `aggregate_id`, `event_type`, `payload_json`, `published_at`, `attempts`, `lease_token`, `lease_until`, `dead_lettered_at` | 与领域事实同事务写入；用 lease + `SKIP LOCKED` 至少一次投递，超过重试预算进入 dead-letter |
| `entitlement_subscription_term` | `term_id`, `site_id`, `subject_id`, `source_period_id`, `program_key`, `period_start`, `period_end`, `status`, `grant_micros` | Payment period 对应的用户权益周期；周期积分以 `source_period_id` 幂等发放 |

### 2.1 Catalog

| 表 | 关键列 | 约束/用途 |
|---|---|---|
| `entitlement_offer` | `offer_id`, `site_id`, `offer_key`, `status` | `(site_id, offer_key)` 唯一；承载可运营的套餐身份 |
| `entitlement_offer_revision` | `offer_revision_id`, `offer_id`, `revision`, `name`, `currency`, `amount_minor`, `credit_micros`, `billing_interval`, `status`, `published_at` | `(offer_id, revision)` 唯一；published revision 是 checkout 唯一可引用的 immutable quote source；storefront 只读 published/active/non-deleted revision |

### 2.2 Usage pricing

| 表 | 关键列 | 约束/用途 |
|---|---|---|
| `entitlement_usage_price_revision` | `usage_price_revision_id`, `site_id`, `revision`, `effective_from`, `effective_to`, `status`, `published_at` | site+revision 唯一；只允许 published revision 参与 quote；settlement 引用 admission 时的 revision |
| `entitlement_usage_price_rate` | `usage_price_rate_id`, `usage_price_revision_id`, `feature_key`, `label_key`, `input_micros_per_million`, `output_micros_per_million`, `cached_micros_per_million`, `reservation_micros` | rate immutable within revision；V1 输入/输出按 token 计算，cached 列预留，reservation 用于 admission hold；不把价格放 JSON |

### 2.3 Feature-first GA target delta（尚未实现）

V1 physical schema 继续为 legacy caller 保留，直到它们 drain 完成；GA target 需要单独 expand migration，而不是在
`quantity_micros` 或 token rate 上打补丁：

```text
CreditAccount / BillingAdmission
  tenant_id + subject_kind + subject_ref        # unique payer identity; no bare subject_id
  billing_ref                                   # binds tenant + subject + feature

InvocationPriceRate
  meter_kind = model_invocation
  invocation_micros                             # fixed user price; no input/output token price

ModelInvocationUsage
  tenant_id + invocation_id                     # unique execution/billing fact
  billing_ref + hold_ref + price_ref
  subject_kind + subject_ref + feature_key
  accepted_provider_ref + accepted_at
  status = authorized | captured | released | reconciliation_pending
```

`hold_ref` 一对一绑定 `invocation_id`，capture/release 互斥且可重放。`reconciliation_pending` 不由普通 expiry job 猜测释放。
旧 token 列可在同一调用保存 provider-cost diagnostics，但不得进入 target hold/capture/user-price 计算。

## 3. Payment 表

| 表 | 关键列 | 约束/用途 |
|---|---|---|
| `payment_provider_account` | `provider_account_id`, `site_id`, `provider`, `external_account_ref`, `status` | provider account 唯一映射；`(provider, external_account_ref)` 全局唯一，是 webhook tenant boundary；密钥只存 secret reference |
| `payment_command_receipt` | `receipt_id`, `site_id`, `command_name`, `idempotency_key`, `payload_hash`, `status`, `result_json`, `lease_until` | Payment command 幂等、重放与冲突检测；当前 command 在单事务内完成，不复用 Entitlement receipt |
| `payment_customer_binding` | `binding_id`, `site_id`, `subject_id`, `provider_account_id`, `external_customer_ref` | `(provider_account_id, external_customer_ref)` 唯一 |
| `payment_checkout` | `checkout_id`, `site_id`, `offer_revision_id`, `quote_snapshot_json`, `provider`, `provider_session_id`, `checkout_url`, `status`, `expires_at` | checkout 保存价格快照和 hosted provider session，不回读可变 catalog；`(site_id, offer_revision_id)` 由复合外键约束；provider session 创建在 MySQL 事务外，结果回写可重放 |
| `payment_provider_event` | `provider_event_id`, `site_id`, `provider`, `external_event_id`, `event_type`, `payload_json`, `payload_hash`, `signature_valid`, `processing_status` | `(site_id, provider, external_event_id)` 唯一；payload hash 防止同一外部事件静默接受不同内容 |
| `payment_settlement` | `settlement_id`, `checkout_id`, `provider_event_id`, `provider`, `external_payment_ref`, `amount_minor`, `currency`, `status` | `(site_id, provider, external_payment_ref)` 唯一；成功 settlement 才能触发 acquisition |
| `payment_reversal` | `reversal_id`, `settlement_id`, `provider`, `external_reversal_ref`, `amount_minor`, `reason`, `status` | `(site_id, provider, external_reversal_ref)` 唯一；支持部分退款 |
| `payment_outbox` | `outbox_id`, `aggregate_type`, `aggregate_id`, `event_type`, `payload_json`, `published_at`, `attempts`, `lease_token`, `lease_until`, `dead_lettered_at` | settlement/reversal 发送给 Entitlement；超过重试预算进入 dead-letter，运营 retry 可重新排队 |
| `payment_provider_subscription` | `provider_subscription_id`, `site_id`, `provider`, `subject_id`, `external_subscription_ref`, `status` | provider subscription 稳定事实；`(site_id, provider, external_subscription_ref)` 唯一 |
| `payment_subscription_period` | `period_id`, `site_id`, `provider_subscription_id`, `period_start`, `period_end`, `status` | provider 周期窗口事实，独立保留 tenant lineage；对应的用户权益状态由 `entitlement_subscription_term` 拥有 |
| `entitlement_fulfillment_reversal` | `fulfillment_reversal_id`, `fulfillment_id`, `payment_reversal_id`, `amount_micros`, `status` | 一个 payment reversal 只能产生一个 credit reversal；余额不足进入 reconciliation exposure |

## 4. MySQL 锁与索引要求

1. 事务内按固定顺序 `receipt → account/settlement → grants/holds → journal → outbox` 获取 `SELECT ... FOR UPDATE`，减少死锁。
2. `credit_grant` 必须有 `(site_id, credit_account_id, status, expires_at, burn_priority, issued_at, credit_grant_id)` 复合索引。
3. `payment_provider_event` 必须有 provider event 唯一索引和 `(processing_status, received_at)` 处理索引。
4. 所有 JSON 只承载不可检索快照/原始 payload；会参与权限、计费、排序的字段必须是强类型列。
5. FK 默认 `ON DELETE RESTRICT`；支付、账本、provider event、grant、journal 不做物理级联删除。
6. 余额 projection 与 journal 不允许跨事务“先缓存后落库”；修复 projection 必须由重放 journal 的管理命令完成并留下 audit。
