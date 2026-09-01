# 后端工程规范

本目录只收录研发侧后端代码与数据库工程规范，不承担部署运维规范，也不提前引入形式化 DDD 模板。

## 规范边界

当前研发规范优先级：

1. 业务边界和模块所有权
2. L0/L1/L2 DDD 采用等级
3. 目录、依赖和公开契约
4. SQL、事务、Repository 和迁移
5. API/RPC 和错误模型
6. 测试与架构门禁

## 研发规范与运维规范边界

### 本目录负责：研发代码规范

- 业务模块和代码所有权
- L0/L1/L2 DDD 采用等级
- 目录、依赖和公开契约
- SQL、事务、Repository、并发和幂等
- API/RPC、错误码和输入校验
- 单元测试、集成测试和架构测试
- schema、代码生成和数据库迁移的研发约束

### 不属于本目录：运维规范

- 部署拓扑和容器编排
- 日志、Metrics、Tracing 平台建设
- SLO/SLI、告警和 on-call
- 容量规划、压测和成本治理
- 灾备、多活、故障演练和事故响应
- 灰度、回滚、发布审批和生产变更流程

这些内容属于运维/交付体系，不能混入研发代码规范。当前只在代码边界保留必要的契约字段和错误语义，不建设对应的运维平台。

## 当前入口

- [后端架构与 DDD 采用等级](../technical/25-backend-architecture-and-ddd-levels.md)
- [后端最终架构与目录规约](../technical/27-final-backend-architecture.md)
- [Redis 运行时依赖、队列与幂等调研](../technical/28-redis-runtime-and-idempotency-research.md)
- [DDD 与模块边界规范](01-ddd-and-module-boundaries.md)
- [后端目录与依赖规范](02-backend-directory-and-dependencies.md)
- [后端子仓库与 DDD 架构规范](../technical/24-backend-subrepository-ddd-architecture.md)
- [ADR-012：后端子仓库与 DDD 分层规范](../decisions/ADR-012-backend-subrepository-ddd-layers.md)
- [SQL 与 PostgreSQL 规范](03-sql-and-postgresql.md)
- [事务、Repository 与幂等基础规范](04-transaction-repository-idempotency.md)
- [API、RPC 与错误契约规范](05-api-rpc-and-error-contracts.md)
- [测试与工程门禁规范](06-testing-and-quality-gates.md)
- [数据库迁移基础规范](07-database-migration-basics.md)
- [PostgreSQL 历史迁移参考](03-sql-and-postgresql.md)

## 后续文档顺序

```text
01-ddd-and-module-boundaries.md
02-backend-directory-and-dependencies.md
03-sql-and-postgresql.md
04-transaction-repository-idempotency.md
05-api-rpc-and-error-contracts.md
06-testing-and-quality-gates.md
07-database-migration-basics.md
```

`03-sql-and-postgresql.md` 是当前 PostgreSQL + Redis 基线的 SQL 规范；存储决策以 ADR-028 为准。旧 MySQL/Mongo 规范已移出当前工作区，仅在 Root 外归档目录供迁移考古。后续文档必须以 25 的 L0/L1/L2 定义为前提，不得把完整 DDD 模板作为所有模块的默认实现。
