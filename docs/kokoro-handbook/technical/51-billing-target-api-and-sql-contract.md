# Kokoro Billing Clean-Build：目标 API 与 SQL 契约

状态：**目标契约冻结版，供 `kokoro-billing` 从零实现；不是 V1 兼容层。**

本文件是 50 号总体架构的实现级补充。它只描述 clean-build 的目标名称、字段、状态和事务边界；旧 migration、旧 OpenAPI、旧
`site_id`、旧 token settlement 不属于本契约。

## 0. 目录与版本约定

```text
kokoro-billing/
├── contract/openapi/v1/openapi.yaml
├── src/interfaces/http/v1/
├── src/interfaces/admin/v1/
├── src/application/       # 无 v1/v2
├── src/domain/            # 无 v1/v2
├── src/ports/             # 无 v1/v2
└── database/              # 无 v1/v2 表副本
```

`v1` 是首发 HTTP contract namespace。版本只存在于 transport boundary：URL、OpenAPI、DTO、validation schema、错误码文档和 SDK。
领域对象、application service、repository port、MySQL 表以及 Redis key 不能按 API 版本复制。当前不创建 `v2` 目录、不注册 v2 route，
未来只有发生破坏性 transport contract 变化时才新增 `interfaces/http/v2` 和 `contract/openapi/v2`。

该规则已由 [ADR-027](../decisions/ADR-027-billing-api-versioning-and-transport-boundary.md) 固化；Manus 的 operation-style URL 仅作为异步
执行与事件契约参考，不复制为 Kokoro 的 URL 命名风格。

## 1. 资源与事实 owner

| 资源 | owner | 说明 |
|---|---|---|
| Product / Offer / PricePolicyRevision | Commerce | 已发布 revision 不可变；金额和 grant policy 在 quote 中快照 |
| Order / OrderLine / Adjustment | Commerce | 购买意图和最终商业金额 |
| PaymentCollection / Attempt / Settlement / Refund | Payment | 钱的 provider 事实；`unknown` 必须 reconcile |
| BillingSubject / PayerAccount | Entitlement | usage 主体与付款主体的绑定 |
| CreditGrant / Hold / Journal | Entitlement | 积分 lot、预留和 append-only 账本 |
| Execution / StudioJob / ModelInvocation | GA / Studio | 执行事实；Billing 只接收 typed receipt |
| Invoice / Receipt | Payment | 首发只做 provider/customer receipt projection；不把它作为扣账事实 |

`Invoice` 是否进入面向用户的正式财务单据，取决于税务、地区和会计要求；首发产品不以 invoice 作为订单支付或权益发放的前置条件。
若未来启用，必须由 Payment 从 settlement/refund facts 生成 immutable revision，不得从当前订单或 catalog 重算。

## 2. PricePolicyRevision

价格 policy 是用户价格唯一来源，不能由 Model provider、浏览器或 caller 金额决定。

```sql
CREATE TABLE commerce_price_policy_revision (
  tenant_id              VARCHAR(64) NOT NULL,
  price_policy_revision_id BINARY(16) NOT NULL,
  policy_key              VARCHAR(128) NOT NULL,
  revision                BIGINT UNSIGNED NOT NULL,
  status                  VARCHAR(16) NOT NULL,
  currency                CHAR(3) NOT NULL,
  effective_from          DATETIME(6) NOT NULL,
  effective_to            DATETIME(6) NULL,
  published_at            DATETIME(6) NULL,
  policy_digest           CHAR(64) NOT NULL,
  created_at              DATETIME(6) NOT NULL,
  PRIMARY KEY (tenant_id, price_policy_revision_id),
  UNIQUE KEY uq_price_policy_revision (tenant_id, policy_key, revision),
  CONSTRAINT ck_price_policy_status CHECK (status IN ('draft','published','retired')),
  CONSTRAINT ck_price_policy_window CHECK (effective_to IS NULL OR effective_to > effective_from)
) ENGINE=InnoDB;

CREATE TABLE commerce_price_policy_rate (
  tenant_id              VARCHAR(64) NOT NULL,
  price_policy_revision_id BINARY(16) NOT NULL,
  rate_id                 BINARY(16) NOT NULL,
  feature_key             VARCHAR(128) NOT NULL,
  surface                 VARCHAR(32) NOT NULL,
  meter_kind              VARCHAR(32) NOT NULL,
  unit_price_minor        BIGINT NOT NULL,
  included_units          BIGINT UNSIGNED NOT NULL DEFAULT 0,
  billing_unit            VARCHAR(32) NOT NULL,
  created_at              DATETIME(6) NOT NULL,
  PRIMARY KEY (tenant_id, rate_id),
  UNIQUE KEY uq_price_policy_rate (tenant_id, price_policy_revision_id, feature_key, surface, meter_kind),
  CONSTRAINT fk_rate_revision FOREIGN KEY (tenant_id, price_policy_revision_id)
    REFERENCES commerce_price_policy_revision (tenant_id, price_policy_revision_id),
  CONSTRAINT ck_rate_price CHECK (unit_price_minor >= 0)
) ENGINE=InnoDB;
```

`model_invocation` 的 `billing_unit` 是一次 provider invocation；token 仅进入 `usage_metadata` 成本分析。Quote、OrderLine、Admission
和 Hold 都保存 `price_policy_revision_id` 与解析出的金额快照。

## 3. Execution / Admission contract

所有业务 HTTP 路由使用 `/v1` contract namespace；未来破坏性变更进入 `/v2`，不在 `/v1` 中静默兼容两套字段。

### 3.1 Internal API

```text
POST /v1/internal/billing/admissions
POST /v1/internal/billing/admissions/{admissionId}/capture
POST /v1/internal/billing/admissions/{admissionId}/release
POST /v1/internal/billing/execution-events
```

所有写命令都要求 service identity、`x-kokoro-tenant-id`、`Idempotency-Key`、request id。请求中的 `tenantId` 必须与受信 service context
一致；`amount`、`accountId`、`siteId`、任意 runtime namespace 不接受为计费依据。

```json
{
  "billing_subject": {"kind": "project", "ref": "subj_TARGET"},
  "payer_ref": "payer_TARGET",
  "feature_key": "feature_TARGET",
  "surface": "ga",
  "invocation_id": "inv_TARGET",
  "execution_id": "exec_TARGET",
  "meter_kind": "model_invocation",
  "requested_model_tier": "tier_TARGET"
}
```

响应（首发 HTTP JSON 统一使用 `snake_case`）：

```json
{
  "data": {
    "admission_id": "adm_TARGET",
    "hold_id": "hold_TARGET",
    "mode": "included|credit|payg|rejected",
    "price_policy_revision_id": "price_TARGET",
    "amount": "0",
    "currency": "USD",
    "status": "held|accepted_without_charge|rejected"
  },
  "meta": {"request_id": "req_TARGET"}
}
```

Capture 只接受：`invocationId`、原 `admissionId`/`holdId`、受信 `acceptedProviderRef`、`acceptedAt`、`serviceReceipt`、`receiptSchemaVersion`。
成功 capture、release 和未知状态都必须可重放；同一 invocation 的 capture/release 互斥。

### 3.2 Execution event

```json
{
  "event_id": "evt_TARGET",
  "event_type": "execution.waiting|execution.accepted|execution.rejected|execution.failed|execution.unknown",
  "execution_id": "exec_TARGET",
  "invocation_id": "inv_TARGET",
  "occurred_at": "2026-08-27T00:00:00Z",
  "receipt_schema_version": "1",
  "receipt": {
    "provider_operation_ref": "provider_op_TARGET",
    "result_digest": "sha256_TARGET",
    "usage_metadata": {}
  },
  "signature": "sig_TARGET"
}
```

`waiting` 只改变 execution 状态；Billing Hold 仍是 `active`。`accepted` 才能 capture，明确 rejected/failed 才能 release，unknown
保留 hold 并创建 reconcile work item。事件 inbox 先验签和落库，再异步驱动 Billing command；event 到达本身不是结算事实。

## 4. Subscription lifecycle

```text
draft -> active -> past_due -> cancelled | expired
```

- Payment provider period 是 Payment 事实；用户可用权益周期是 Entitlement 事实；两者通过 immutable `source_period_ref` 关联；
- 每个 `(tenant_id, subscription_id, period_key)` 只能生成一次 fulfillment；续费 webhook 重复或乱序只更新合法状态；
- 续费支付 unknown 时不提前发放下一周期 grant；grace policy 若启用，必须是已发布 entitlement policy；
- cancel 默认停止下一周期续费，不撤销当前已承诺且未过期的 grant；立即取消和退款是两个显式 command；
- 周期 grant 的 `source_period_ref`、grant template revision、expiry 和 priority 必须快照。

## 5. Promotion budget reservation

Promotion 计算不是简单 `discount_total`。并发 checkout 必须在同一 MySQL transaction 中锁定 campaign revision 的 budget ledger：

```text
evaluate conditions
 -> insert promotion_redemption (pending)
 -> reserve budget / per-payer quota with unique key
 -> write order_adjustment snapshot
 -> order paid => redemption committed
 -> order expired/cancelled => reservation released
```

`pending` reservation 有 TTL，但过期处理必须由 MySQL 行锁和状态机完成；Redis 只能做快速拒绝和限流提示。支付失败不得消耗 committed redemption，
支付成功后的退款不恢复已使用的优惠次数，除非 promotion policy 明确允许且由 Admin command 执行。

## 6. Refund allocation

退款 command 必须引用原 `paymentSettlementId`，并明确 `allocationMode=proportional|line_specific`。事务顺序：

```text
payment refund receipt
 -> lock settlement + order lines
 -> create refund allocation per line/adjustment
 -> create payment refund fact
 -> outbox entitlement reversal
 -> entitlement locks fulfillment/grants
 -> reversal journal or exposure fact
```

已消费权益不静默恢复；余额不足产生 `entitlement_fulfillment_reversal(status='exposure')`，由 Admin/finance reconcile。退款金额、已退金额和可退金额
全部使用 settlement currency 的整数 minor units；退款不得超过 captured amount。

## 7. Reconcile 与 repair command

Reconcile 是发现 drift 和生成受控 command，不是直接改 projection：

| 检查 | 发现 | 修复命令 |
|---|---|---|
| Provider event → settlement | 缺失、重复、金额币种不一致 | `ReplayProviderEvent` / `CreateSettlementCorrection` |
| Settlement → fulfillment | 支付成功但未发放或重复发放 | `RetryFulfillment` / `ReverseDuplicateFulfillment` |
| Admission → execution receipt | hold 超时、accepted 缺失、重复 capture | `ReconcileAdmission` |
| Journal → grant projection | projection 漂移 | `RebuildCreditProjection` |
| Refund → reversal | 钱已退但权益未撤销 | `RetryFulfillmentReversal` |

每个 repair command 具备 command receipt、payload hash、operator/reason（若为 Admin）、dry-run 结果和审计事件；命令执行仍走正常 owner
application service 和不变量校验。禁止运维 SQL 直接 `UPDATE balance`、`UPDATE status` 或删除事实表。

## 8. 目标验收门

- 全部金额/积分/数量在 API 为十进制字符串，在 MySQL 为带单位整数；
- tenant 复合主键/FK、`tenant_id` 命名和 HTTP JSON `tenant_id` 一致；无 `site_id` 兼容字段；
- Redis 停止、淘汰、重启后，重复 command 仍由 MySQL receipt/unique fact 返回同一结果；
- provider timeout、webhook 重复/乱序、worker crash、deadlock retry、unknown hold、partial refund、duplicate fulfillment 均有集成测试；
- User、Admin、Internal、Webhook 四个 surface 的 DTO、鉴权和错误码互不越权；
- OpenAPI、SQL schema、状态机、事务矩阵、运行单元目录和实现代码由同一 contract test 校验。
