# 数据库迁移基础规范

状态：未来生产数据演进参考，Kokoro V1 当前不启用（2026-09-04）

> 当前唯一正式数据库规范是 [PostgreSQL 与 SQL 工程规范](03-sql-and-postgresql.md)。Kokoro V1 使用 fresh
> schema，禁止 `database/migrations/`、migration runner 和 migration ledger。本文件只说明未来已经存在必须保留的
> 生产数据后，如何重新评审版本化演进；Agent 不得据此提前恢复迁移体系。

## 1. 唯一事实源

- owner 子仓库的唯一 canonical schema 是当前物理 DDL authority；每个业务表只允许一个 owner。
- Root 只通过 topology/architecture checks 检查 owner 归属，不复制 schema 或 migration manifest。
- 每张表必须登记 owner、runtime writer、读面、删除策略和敏感字段。
- 未来若经 ADR 启用 migration，迁移不能通过 ORM 自动同步隐式执行；DDL 变更必须可审查、可重放。

## 2. 迁移要求

未来每个 migration 必须说明：

```text
前置版本 / 目标版本
变更对象与 owner
锁和数据量影响
expand / backfill / contract 阶段
向前兼容窗口
验证 SQL
回滚或前向修复方案
```

当前 clean-build 阶段只维护并验证完整 `database/schema.sql`，不生成 migration。后续线上已有数据且经过 ADR
启用版本化演进后，才使用 expand -> backfill -> contract；届时需要单独设计兼容窗口、锁、恢复和回退，不能把
V1 的历史开发 schema 伪装成生产 migration 链。

## 3. 不允许的迁移

- 直接删除仍被运行时读取的列或表；
- 以应用层“先查再插入”替代唯一约束；
- 用 `jsonb` 隐藏尚未完成的业务建模；
- 让一个迁移同时修改多个 owner 的业务表而没有跨 owner ADR；
- 只在开发数据库执行、未在 fresh PostgreSQL 重建验证；
- 修改 baseline 后不更新 manifest/hash 和证据。

## 4. 验收门禁

未来启用 migration 后，变更至少通过：

1. fresh database 初始化；
2. migration forward；
3. schema、约束、索引和 owner inventory 校验；
4. Repository 集成测试；
5. 当前 schema 下的 Repository 集成测试和状态机恢复测试；
6. baseline 与生成物 provenance 校验。
