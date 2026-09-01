# ADR-025：吸收腾讯云/阿里云费用中心模式，不复制云厂商复杂度

- 状态：accepted
- 日期：2026-08-24

## Context

Kokoro 的产品同时需要套餐、预付积分、按量模型调用、优惠、退款和多租户运营。Stripe 只解决支付 provider，不能单独表达
“谁付款、谁使用、哪一批预付额度被抵扣、额度冻结后何时释放、账单与用量如何解释”。腾讯云和阿里云的公开费用中心文档提供了
更接近该问题的成熟业务抽象。

## Decision

吸收以下模式：

1. Billing Account/Payer 与登录 Account/Usage Subject 分离；
2. Cash、Credit Limit、Voucher/Coupon、Prepaid Resource Grant 分开建模；
3. Prepaid grant 按有效期/优先级扣减，用完后可进入 pay-as-you-go 或拒绝；
4. Hold/Frozen、Captured、Released 是不同事实状态；
5. Order、Payment、Bill/Receipt、Usage Detail、Credit Ledger、Reconcile 是不同查询模型；
6. 企业 Admin 通过 financial permission 管理 payer、优惠、退款和账单，而非复用普通用户权限。

不复制云厂商的资源实例、地域、复杂税务、信用授信和财务总账；这些只有产生实际需求时才增加 bounded context。

## Consequences

- `PayerAccount` 和 `BillingCustomerBinding` 成为目标模型，不再把 `subject_id` 作为长期唯一账户模型。
- CreditGrant/Promotion/PaymentSettlement 必须保持不同 owner 和 source fact。
- User API 要能解释余额、grant 消耗和过期；Admin API 要能解释预算、退款、冻结和 drift。
- V1 仍可使用 prepaid credit + Stripe payment，但迁移到目标模型时必须增加 binding 和 fallback policy 的 migration/test。
