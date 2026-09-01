# ADR-023：Billing 采用模块化单体，PostgreSQL 保证正确性，Redis 只做协调

- 状态：已更新（2026-09-01），存储基线以 [ADR-028](ADR-028-postgresql-redis-runtime-baseline.md) 为准
- 日期：2026-08-24

## Context

Payment、Entitlement/Credit、套餐与兑换需要共享清晰的业务边界，但首发阶段拆成多个仓库会扩大
跨服务事务、契约和对账复杂度。系统同时具备 PostgreSQL 与 Redis；若把 Redis lock 或 SETNX 当作余额和幂等的
最终依据，Redis 故障、淘汰或脑裂会造成重复发放或重复扣费。

## Decision

保持一个 Git repository：`kokoro-billing`，内部按 bounded context 和模块组织，运行时拆为 Billing API、Payment worker、
Credit sweeper、migration job。Payment 与 Entitlement/Credit 分别拥有自己的表和 application ports，不共享万能 repository。

PostgreSQL 是 payment、fulfillment、credit grant、hold、allocation、journal、receipt 和 outbox 的最终事实源。
所有关键 mutation 在一个 MySQL transaction 中完成，使用唯一约束、行锁、状态机和 append-only facts 保证正确性。

Redis 只用于 idempotency hint、短 lease、缓存、限流和 worker coordination。Redis 命中可以快速返回已知结果，Redis miss、
eviction、重启或短暂不可用都不能改变 MySQL 事务语义。

## Alternatives

1. Payment/Credit 独立 repo/service：边界更硬，但购买→发放→退款需要跨服务补偿与对账，当前阶段成本过高。
2. Redis 作为分布式锁和幂等真源：低延迟，但无法承载账务事实和持久审计，不接受。
3. Kafka 作为 Billing 首发必需组件：能力可行，但当前先不引入。

## Consequences

- 代码边界通过 import rules、ports、表 owner 和 contract tests 强化，而不是依赖仓库数量制造边界。
- 未来满足数据库 owner、团队 ownership、吞吐/隔离或发布生命周期独立等条件时，可从模块化单体拆出 service/repo。
- Redis 故障时允许性能、缓存和限流降级；关键 mutation 必须回到 MySQL，不能静默成功。
- 仍需持续验证 transaction lock order、deadlock retry、outbox lease 和 reconcile；这不是用 Redis lock 可以替代的。
