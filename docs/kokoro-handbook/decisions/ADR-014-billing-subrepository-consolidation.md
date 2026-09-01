# ADR-014：Payment 与 Entitlement/Credit 收敛到 Billing 子仓库

- 状态：accepted
- 日期：2026-08-22

## Context

套餐支付、订单、订阅、退款、权益发放和积分必须形成可重试、可对账的业务闭环。当前
`kokoro-payment` 通过 HTTP 调用独立 `kokoro-credit`，跨两个 schema 维护补偿状态。

## Decision

建立 `kokoro-billing`，由一个仓库管理 Payment 与 Entitlement 两个 bounded context，并统一发布、迁移和
运行手册。Payment 继续拥有 provider money facts；Entitlement 继续拥有 Fulfillment、SubscriptionTerm、
CreditGrant、CreditHold、CreditJournal。两者通过 PaymentSettlement/PaymentReversal + outbox contract
协作，绝不通过一个万能 repository 或跨表直写合并。

所有业务事实使用 PostgreSQL；Redis 只承担协调、短期快路径和 lease。外部 provider 不进入数据库
事务，使用 inbox/outbox 和幂等 worker 收敛。

## Alternatives

1. 继续 Payment/Credit 双仓：跨仓 grant/reverse 补偿复杂，购买来源和 CreditGrant 无法自然闭环。
2. 一个仓库一个万能账务模块：边界消失，provider SDK、money fact 和 credit journal 耦合。
3. 采用第三方 billing 平台：当前需要自有多租户、模型用量和内部 hold 语义，先保留自有 owner。

## Consequences

- 需要迁移两套 schema、contract、消费者和运行入口；这是一次有计划的 breaking architecture change。
- Payment 和 Credit 旧仓库短期保留只读迁移状态，禁止新增业务能力。
- 购买发放从跨仓同步 HTTP 改为同一 Billing 仓库内的 Payment→Entitlement outbox/worker，但仍保留
  bounded context 和独立 writer。
- Credit 必须从单一总余额升级为 CreditGrant + HoldAllocation + CreditJournal，支持赠送、购买、订阅周期、
  来源级撤销和过期。
