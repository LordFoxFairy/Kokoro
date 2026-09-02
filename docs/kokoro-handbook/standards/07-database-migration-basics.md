# 数据库迁移基础规范

状态：正式规范，2026-08-21

适用范围：Root `database/`、baseline、migration 脚本和各正式子仓库 PostgreSQL 持久化实现。

## 1. 唯一事实源

- Root `database/` 与 owner 子仓库的 PostgreSQL migration 是当前物理 DDL authority；每个业务表只允许一个 owner。
- `database/baseline/manifest.json` 记录基线文件、顺序和 hash。
- 每张表必须登记 owner、runtime writer、读面、删除策略和敏感字段。
- 迁移文件不能通过 ORM 自动同步隐式生成；DDL 变更必须可审查、可重放。

## 2. 迁移要求

每个迁移必须说明：

```text
前置版本 / 目标版本
变更对象与 owner
锁和数据量影响
expand / backfill / contract 阶段
向前兼容窗口
验证 SQL
回滚或前向修复方案
```

对于当前 clean-build 阶段，不保留旧 MySQL/Mongo 兼容层；直接建立目标 PostgreSQL schema，并保证 migration 可重复执行。后续线上已有数据演进才使用 expand → backfill → contract。大表索引评估锁时间，必要时使用并发创建并单独验证。

## 3. 不允许的迁移

- 直接删除仍被运行时读取的列或表；
- 以应用层“先查再插入”替代唯一约束；
- 用 `jsonb` 隐藏尚未完成的业务建模；
- 让一个迁移同时修改多个 owner 的业务表而没有跨 owner ADR；
- 只在开发数据库执行、未在 fresh PostgreSQL 重建验证；
- 修改 baseline 后不更新 manifest/hash 和证据。

## 4. 验收门禁

变更至少通过：

1. fresh database 初始化；
2. migration forward；
3. schema、约束、索引和 owner inventory 校验；
4. Repository 集成测试；
5. 当前 schema 下的 Repository 集成测试和状态机恢复测试；
6. baseline 与生成物 provenance 校验。
