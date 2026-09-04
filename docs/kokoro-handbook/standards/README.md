# Kokoro 工程规范入口

后端开发首先读取三份正式手册：

1. [PostgreSQL 与 SQL 工程规范](03-sql-and-postgresql.md)
2. [TypeScript 后端成熟工程规范](08-typescript-backend-engineering.md)
3. [Python 后端成熟工程规范](09-python-backend-engineering.md)

三份手册分别是 SQL、TypeScript、Python 的唯一可编辑规范事实源。`AGENTS.md` 只引用，不复制其完整规则。

按任务继续读取：

- [DDD 与模块边界](01-ddd-and-module-boundaries.md)：只解释业务建模和依赖原则，不规定统一物理目录。
- [目录与依赖概念](02-backend-directory-and-dependencies.md)：补充边界原则；与语言手册冲突时以 08/09 为准。
- [事务、Repository 与幂等](04-transaction-repository-idempotency.md)
- [API、RPC 与错误契约](05-api-rpc-and-error-contracts.md)
- [测试与质量门禁](06-testing-and-quality-gates.md)
- [数据库迁移基础](07-database-migration-basics.md)：历史/未来生产演进参考；Kokoro V1 当前不保留 migration 链。

## 权威顺序

```text
AGENTS.md 的 owner/执行规则
-> 03 / 08 / 09 三份正式手册
-> 04 / 05 / 06 专项规则
-> 01 / 02 概念说明
-> 旧 technical/、报告和已废止 ADR（只用于考古）
```

不得从旧文档恢复强制顶层四层、`ports/`、按技术品牌建立业务目录、外键或 migration runner。
