# ADR-024：BillingSubject 与 PayerAccount 分离

- 状态：accepted
- 日期：2026-08-24

## Context

当前 V1 以 `(tenant_id, subject_id)` 直接定位 CreditAccount。这个模型适合个人账户的第一切片，但不能表达项目/团队/组织
共同付费，也不能支持多个 usage subject 归属于同一个 payer。成熟 metering/billing 系统通常把 usage subject 与 billing
customer/entity 分开；否则执行主体、扣费主体、支付 customer 和 RuntimeNamespace 会混成一个身份轴。

## Decision

目标模型固定为：

```text
BillingSubject(tenant, kind, opaque_ref)
  -> BillingCustomerBinding
  -> PayerAccount(tenant, kind, account_ref)
  -> CreditAccount / PaymentCustomer
```

Internal metering API 接收 IAM 提供的 typed subject 窄投影与 Billing 签发的 `billingRef`，不接收 caller 自选 account ID、
RuntimeNamespace 或最终价格。Binding 的创建/变更属于 Billing application command，必须有租户授权、reason、审计和对未结算
hold/usage 的迁移策略。

V1 旧 `subjectId` route 保持 compatibility，但只允许映射到默认 personal payer；Feature-first GA 必须使用 typed
`billingSubject + billingRef` contract。目标 migration 在没有完成 binding、跨 tenant foreign key、reconcile 和 caller tests
前，不删除旧列或宣称切换完成。

## Consequences

- Personal、project、organization 账户可以共用 Credit/Payment 领域模型。
- 账单归属和 usage 归属可以独立审计，退款/撤销可追溯到原 payer。
- 需要新增 binding/source facts 与迁移策略，不能仅改 API 字段名。
- Billing 不负责 IAM 组织关系，只消费 IAM 授权后的主体与 payer binding command。
