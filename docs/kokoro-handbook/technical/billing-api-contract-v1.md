# kokoro-billing 对外 API 契约 v1

> **状态：V1 token 计量物理基线。**本文描述当前 `kokoro-billing` OpenAPI 与已实现的 quote / usage-event / settle 路由；
> 它**不定义** Feature-first GA 的模型调用扣费。GA target 以
> [31 Billing 子仓架构](31-billing-subrepository-architecture.md#model-invocation-metering-contract) 与
> [38 GA 公共运行契约](38-ga-public-runtime-contract.md#53-model-与-billing) 为准：用户价格按 provider 接受的
> `ModelInvocation` 次数，provider token 只作成本、预算和诊断。

当前 HTTP canonical contract 位于
`/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-billing/contract/openapi/billing-v1.yaml`；
`contract/proto/kokoro/billing/v1/` 仅在未来确实采用内部 RPC 时再生成，不为尚未存在的 transport 预先造一套
平行契约。本文件定义 API 边界，OpenAPI 是 User、Internal、Admin、Provider Webhook 的可验证来源。

本契约遵循根仓 PRD-03/04：Payment API 产生 acquisition/payment facts；Entitlement API 负责
Fulfillment、CreditGrant、Hold 和 Journal。两者在同一代码仓库内协作，但不共享业务 repository。

套餐多 benefit、Promotion/Coupon、Entitlement Redeem Code 和 Gift/Prepaid Credit Code 的目标扩展不在当前
OpenAPI v1 中；其领域模型、状态机和目标路由统一见
[46-billing-package-credit-redeem-architecture.md](46-billing-package-credit-redeem-architecture.md)。

## 通用约束

- 所有响应使用 `{ data, requestId }` 或 `{ error: { code, message }, requestId }`。
- 跨服务调用必须透传 `x-kokoro-request-id`；边缘请求缺失时由 BFF 生成 UUID，Billing 响应中的 `requestId` 与该链路标识对应。
- 所有会写入业务事实的 command 必须接受 `Idempotency-Key`，服务端保存 request fingerprint；Admin refund 的 key
  会持久化到 Payment-owned `payment_command_receipt`，不能仅依赖 Redis TTL 或 provider refund reference；`accounts/ensure` 通过
  `(tenantId, subjectId)` 自然键幂等，`quotes` 是无副作用计算查询，二者不要求该 header。
- 金额和数量使用十进制字符串；货币金额必须带 `currency`，积分必须带 `unit=credit_micros`。
- 对外上下文统一称为 `tenantId`，来自可信 request context；不接受客户端任意覆盖租户 header。
- 跨服务统一使用平台标准 `x-kokoro-tenant-id` 传递租户上下文；生产 User 面使用 IAM RS256/JWKS Bearer JWT，JWT
  的 `tenant_id` 必须与该 header 一致；Internal 面使用 `x-kokoro-service` + 独立 service secret；Admin 面使用
  `x-kokoro-operator` + `billing.admin` + 独立 operator proxy secret。Billing 不把旧的非标准 `x-kokoro-site`
  作为正式契约。
- public storefront、internal service、admin、provider webhook 使用不同 route access policy。
- 运维端点遵循平台标准：`GET /healthz` 仅表示进程存活，`GET /readyz` 同时检查 MySQL 与 Redis，`GET /metrics`
  为 Prometheus 旁路指标；这些端点不属于业务 API 鉴权面。

## API 面不是一套

Billing 明确拆成四个 API surface，不能让用户 API 复用 admin DTO，也不能让浏览器直连内部钱包
mutation：

| API 面 | 调用方 | 认证/授权 | 能看到/能做什么 | 禁止事项 |
|---|---|---|---|---|
| User / Storefront | Web BFF、登录用户 | 用户会话 + tenant/team membership | active 套餐、自己的 checkout、自己的订单/余额/用量 | 不能传 ownerId 替换身份；不能 grant/refund/replay/reconcile |
| Internal Service | Model、Agent、Session、Payment worker | service identity + internal secret | quote、hold、settle、credit-account query、outbox command | 不能越过 service policy 访问 admin 面 |
| Admin / Operations | platform-admin、运营人员 | operator identity + admin RBAC/audit | 套餐管理、手工 grant、退款、replay、stats、reconcile | 不能伪造用户上下文；高风险动作必须 reason/operator |
| Provider Webhook | Stripe/支付宝/微信 | provider signature + event id | 支付成功、失败、退款、订阅事件 inbox | 不能直接改钱包或绕过事件处理 |

用户面推荐由 `web-bff` 代理，Billing 仍验证 IAM 签发的 RS256/JWKS session，并只接受 JWT `sub` 与 `tenant_id`
  产生的主体上下文；Admin 面由 `platform-admin` 代理，Billing 校验独立 operator proxy secret 与 operator context。
两侧即使底层都使用同一个
application use case，也必须拥有不同的 route、schema、权限和审计策略。

## Storefront API

```text
GET  /billing/plans
POST /billing/checkout
```

`/billing/plans` 的 `tenantId` 与主体来自已验证的 user context header，不放在浏览器 query/body 中；每个 offer 只返回当前
最新的 published revision，历史 revision 仅供已创建 checkout 使用，避免 storefront 展示重复套餐。
当前迁移契约用 `offerRevisionId + currency + immutable quoteSnapshot` 创建 checkout；服务端只接受已发布
revision 的报价快照，不信任客户端自行增加积分数量或金额。旧 `planId` checkout 只作为迁移兼容面，不能成为
Billing 的最终契约。

用户查询只允许当前主体可见资源：

```text
GET /billing/me/credit-account
```

`/billing/me/*` 的 account/team 来源只能来自已验证 context，不接受 body 中的 `accountId` 作为授权依据。

## Provider webhook API

```text
POST /billing/webhooks/{provider}
```

要求 provider signature 验证、raw body 保留、provider account 映射到 tenant、`provider + eventId` 唯一、先 inbox 落库后异步处理。生产环境只接受 provider account registry 的映射结果作为租户权威；direct-account endpoint 若签名事件没有顶层 account ref，必须通过 `BILLING_PROVIDER_ACCOUNT_REF_<PROVIDER>` 配置固定 account，再查询 registry；新建 provider metadata 使用 `tenantId`，历史 payload 中的 `siteId` 仅做映射结果一致性校验，不参与租户选择。重复
事件返回原处理结果，不重复确认订单、发放权益或退款。

## Internal entitlement/credit/metering API

```text
POST /internal/billing/entitlement/accounts/ensure
GET  /internal/billing/entitlement/accounts/summary?subjectId=...
GET  /internal/billing/entitlement/accounts/ledger?subjectId=...&limit=...
GET  /internal/billing/entitlement/accounts/by-model?subjectId=...
POST /internal/billing/entitlement/quotes
POST /internal/billing/entitlement/holds
POST /internal/billing/entitlement/holds/{holdId}/release
POST /internal/billing/entitlement/usage/events
POST /internal/billing/entitlement/usage/settle
POST /internal/billing/payment/settlements/accept
```

### Feature-first GA target（尚未落入本 V1 OpenAPI）

新的 GA caller 不使用本节的 `usage/events`、`usage/settle`、`quotes(inputTokens, outputTokens)` 或允许调用方提交
`subjectId/quantityMicros` 的 generic command。完成 target migration 后，Billing 会新增由 GA workload identity 调用的三条
内部 contract：

```text
POST /internal/billing/model-invocations/authorize
  invocationId + billingRef + billingSubject(kind, opaqueRef) + featureKey + requestedModelLabel?
  -> holdRef + priceRef + amountMicros

POST /internal/billing/model-invocations/accepted
  invocationId + billingRef + holdRef + billingSubject + featureKey + priceRef
  + acceptedProviderRef + acceptedAt + gaReceipt
  -> captured | already_captured

POST /internal/billing/model-invocations/{invocationId}/release
  holdRef + reason=rejected|reconciliation_not_accepted + gaReceipt
  -> released | already_released
```

`billingRef` 在 Session/Billing admission 时绑定 `tenant + subject + feature`；每一次实际 provider send 只由 Billing
返回一个 `holdRef`。新 price rate 的 `meter_kind=model_invocation` / `invocation_micros` 是固定每调用价格，绝不接受 token
数量或 caller 传入金额决定用户扣费。`unknown` 提交维持 hold，直至 provider reconciliation 终态。上述三个 target route、对应 OpenAPI
schema、MySQL migration、GA contract tests 尚需在同一切换 PR 实现；在此之前 V1 route 只能服务 legacy caller，不能被
Feature-first GA 接入。

`usage/events` 只记录计量事实；请求必须携带调用方生成的稳定 `usageEventId`，用于事件事实幂等；`usage/settle`
才产生 CreditGrant 扣减。settle 必须提供 `holdId`、实际使用量、usage event id（或由 hold 稳定派生）和
idempotency key。

Session usage migration uses `accounts/ensure → quotes → holds → usage/settle|holds/{holdId}/release`.
The quote is resolved from the published usage-price revision; the hold stores the selected pricing revision so
token settlement cannot be repriced by later admin changes.

`payment/settlements/accept` 只写入稳定的 PaymentSettlement source fact，并触发
`Acquisition(source_kind=payment, source_ref=settlement_id)`；它不直接返回或修改 CreditJournal。
请求中的 `provider` 是可选的 provider namespace；省略时仅用于受信任的内部导入并默认为 `internal`。外部支付引用
按 `(site_id, provider, externalPaymentRef)` 去重，避免不同渠道复用同一订单号造成误冲突。
Usage pricing V1 只接受 input/output token 计价；数据库保留 `cached_micros_per_million` 扩展列，但在缓存 token
尚未进入 Session usage wire contract 前不对外暴露，避免出现“配置了价格但结算永远不带用量”的假闭环。

## Admin API

```text
GET  /admin/billing/plans
POST /admin/billing/plans
GET  /admin/billing/usage-pricing
POST /admin/billing/usage-pricing
POST /admin/billing/grants
POST /admin/billing/refunds/{settlementId}
POST /admin/billing/provider-events/{providerEventId}/retry
GET  /admin/billing/provider-events?status=failed&limit=50&cursor=CURSOR
GET  /admin/billing/credit-operations
GET  /admin/billing/payment-operations
GET  /admin/billing/manifest
GET  /admin/billing/reconcile
GET  /admin/billing/stats
```

`/admin/billing/stats` 仅返回当前 tenant 的只读聚合：checkout/provider event 状态计数、按币种拆分的成功结算/退款金额，
以及 Credit account/grant/remaining projection 数量；金额和计数均以十进制字符串返回，不跨 currency 汇总。

Admin grant、refund、provider event replay 都必须留下 operator、reason、requestId 和 audit event。
Provider event 查询仅返回当前 site 的事件，用于运营排障；`status` 可筛选 `received`、`processed`、`ignored`、`failed`，
`limit` 范围为 1–100，返回 `nextCursor` 时使用不透明 cursor 继续查询。查询不改变事件状态，重放必须通过带幂等键和 reason 的 retry 命令完成。

`/admin/billing/reconcile` 返回 account projection、settlement→fulfillment、reversal→fulfillment reversal 和 failed
provider event 四类 drift；`status=ok` 只在四类结果均为空时成立。

当前实现切片已落地 `/billing/plans`、`/billing/me/credit-account`、`/admin/billing/plans`、`/admin/billing/usage-pricing`、
`/admin/billing/grants`、`/admin/billing/refunds/{settlementId}`、`/admin/billing/stats`、provider event retry 和 reconcile。
旧 Web BFF 的 checkout/mock-pay 切流状态以
`billing-migration-manifest.yaml` 为准，不在契约未闭合时宣称旧 writer 已停止。

Provider webhook 使用 timestamped HMAC 适配器：验签输入为 `timestamp.rawBody`，签名头使用
`t=UNIX_SECONDS,v1=HEX_SHA256`；raw body 必须在 JSON parse 前保留，且 timestamp 超过 tolerance 直接拒绝。

## 错误码

```text
billing.invalid_request       400
billing.unauthorized           401
billing.plan_not_found         404
billing.idempotency_conflict  409
billing.command_in_progress    409
billing.command_unknown        409
billing.credit_projection_drift 409
billing.reversal_exposure      409
billing.insufficient_credit   402
billing.usage_event_mismatch  409
billing.order_not_confirmable 409
billing.provider_signature     401
billing.provider_tenant_missing 400
billing.provider_tenant_mismatch 400
payment.webhook_payload_invalid 400
billing.internal_error         500
```

Reconciliation drift 是成功返回的 Admin 报告（`200`，且 `data.status = drift`），不是传输层错误。
