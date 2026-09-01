# SQL 与 PostgreSQL 规范

状态：正式规范，2026-08-21

适用范围：Root `database/schema/`、PostgreSQL baseline、各后端子仓库的持久化适配器和 SQL 查询。

本规范参考 PostgreSQL 的关系约束能力、Alibaba P3C 的数据库工程规则，以及 Kokoro 当前的 owner-scoped baseline。参考其他公司的规则时只吸收原则，不直接复制 MySQL、Java 或分库分表场景下不适用的限制。

## 1. 数据所有权

- Root `database/schema/` 是物理 PostgreSQL DDL 的唯一权威来源。
- 每张业务表只有一个 owner 和 runtime writer。
- 子仓库可以定义 Repository 和查询适配器，但不修改其他 owner 的表。
- 跨领域读取通过 RPC、公开查询契约或明确的 projection，不通过跨 owner SQL。
- Foreign Key、UNIQUE、CHECK 和 NOT NULL 是数据库不变量的一部分，不用应用层重复检查代替。
- 删除策略必须显式选择：禁止删除、软删除、状态终止或级联删除；不允许依赖 ORM 默认行为。

## 2. 命名

统一使用小写 snake_case：

```text
表：      <domain>_<singular_noun>
字段：    <singular_noun>_<meaning>
主键：    <singular_noun>_id
外键：    <referenced_noun>_id
普通索引：<table>_<columns>_idx
唯一索引：<table>_<columns>_uidx
外键约束：<table>_<purpose>_fk
检查约束：<table>_<purpose>_ck
唯一约束：<table>_<purpose>_key
```

示例：

```sql
CREATE TABLE credit_account (...);

CREATE UNIQUE INDEX credit_account_site_owner_uidx
  ON credit_account(site_id, owner_id);

CONSTRAINT credit_account_status_ck
  CHECK (status IN ('active', 'closed'));
```

规则：

- 表名使用单数，不使用含糊的 `data`、`info`、`common`、`base`。
- 不使用 PostgreSQL 关键字和容易产生歧义的缩写。
- 布尔字段优先使用有业务含义的名称，例如 `is_active`；状态机优先使用 `status`，不要同时存在可互相矛盾的 `status` 和 `is_active`。
- 领域前缀必须与 owner 对齐，例如 `iam_*`、`chat_*`、`credit_*`。

## 3. 类型与通用字段

- 主键默认使用 `uuid`，由应用生成或使用明确的数据库生成策略。
- 时间默认使用 `timestamptz`，禁止使用无时区 `timestamp` 表示跨服务业务时间。
- 所有业务时间字段明确含义：`created_at`、`updated_at`、`expires_at`、`consumed_at`、`revoked_at`。
- 金额和积分使用整数最小单位，例如 `amount_micros bigint`，不使用浮点数。
- 状态字段使用 `text` + `CHECK`，状态较稳定且需要跨语言共享时保持字符串语义；不要用数据库 enum 锁死迁移流程。
- 结构稳定的字段使用明确标量类型；只有结构确实开放、版本变化频繁或需要保存外部原始 payload 时使用 `jsonb`。
- `jsonb` 必须说明 owner、schema 版本和查询需求，不能作为逃避建模的万能字段。
- 可空表示业务上的“不存在”，不能用空字符串、`0` 或特殊 magic value 代替。

## 4. 约束与索引

- 能由数据库证明的不变量，优先使用 `NOT NULL`、`CHECK`、`UNIQUE` 和 `FOREIGN KEY`。
- 唯一性必须由数据库唯一约束或唯一索引保证，禁止使用“先查询再插入”代替。
- 条件唯一性使用 partial unique index，例如只约束 active 记录。
- 每个索引必须对应真实查询、排序、唯一性或外键访问路径；提交时写明服务/查询用途。
- 复合索引按查询谓词设计：等值过滤列优先，其次范围列，最后排序列；不能仅凭字段区分度拍脑袋。
- 索引列顺序必须与实际 `WHERE`、`ORDER BY` 和分页方式一起验证。
- 不为每个字段机械建索引；索引会增加写入成本和存储成本。
- 大表迁移新增索引优先评估并发创建、锁时间和回滚方式。

## 5. SQL 查询

- 所有用户输入必须参数化，禁止字符串拼接 SQL。
- 默认禁止 `SELECT *`；查询只选择需要的列。
- 通用更新接口禁止无条件更新全部字段；每个命令只更新它拥有的字段。
- 列表接口必须限制 page size；优先使用 keyset/cursor pagination，避免大 offset。
- 分页排序必须稳定，至少包含唯一键作为最终排序键。
- `ORDER BY`、筛选字段、动态列名必须使用白名单，不允许直接透传用户输入。
- 删除和数据修复脚本先 SELECT 确认范围，再执行写操作，并记录影响行数。
- 复杂查询提交时提供 `EXPLAIN (ANALYZE, BUFFERS)` 结果或说明为什么当前阶段不需要。
- 不在业务代码中循环执行 N+1 查询；批量操作必须明确批量大小、事务边界和失败行为。
- 事务内不调用不可控的外部网络服务。

## 6. 表设计示例

```sql
CREATE TABLE iam_identity (
  identity_id uuid PRIMARY KEY,
  site_id uuid NOT NULL,
  issuer text NOT NULL,
  subject text NOT NULL,
  status text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT iam_identity_status_ck
    CHECK (status IN ('active', 'revoked')),
  CONSTRAINT iam_identity_site_fk
    FOREIGN KEY (site_id) REFERENCES site_site(site_id) ON DELETE RESTRICT
);

CREATE UNIQUE INDEX iam_identity_site_subject_uidx
  ON iam_identity(site_id, issuer, subject);
```

## 7. Migration 规则

- 新增或修改 DDL 先改 `database/schema/` 源文件，再重新生成 baseline；不手工改生成物。
- 每次迁移记录数据影响、锁影响、兼容窗口、验证 SQL 和回滚/前滚策略。
- 生产变更遵循“扩展—迁移—收缩”：先新增兼容结构，再部署读写逻辑，再回填，最后删除旧结构。
- 删除列、重命名列、收紧 NOT NULL、改变状态含义都必须分阶段完成。
- 数据回填脚本可重复运行，按批次执行，并具有明确的幂等条件。
- Schema 变更必须有 fresh PostgreSQL 验证，不以已有本地数据库能启动作为证据。
- 生成的 baseline、manifest 和 schema hash 必须能追溯到源 SQL 与生成命令。

## 8. 当前基线的适用结论

当前 PostgreSQL baseline 已采用以下有效实践：

- UUID 主键
- `timestamptz`
- owner 前缀表名
- CHECK 约束表达状态和跨字段不变量
- partial unique index 表达 active 记录唯一性
- Foreign Key + `ON DELETE RESTRICT`
- generation/version 字段表达并发更新保护

后续新增表应延续这些规则，不再从旧 MySQL 文档反推 PostgreSQL 设计。

## 9. 当前不做

- 不提前引入分库分表。
- 不为预期数据量很小的表提前做复杂分片。
- 不用存储过程承载核心业务流程。
- 不引入数据库触发器作为跨模块业务编排机制。
- 不把 Redis、缓存或消息队列当作 SQL 业务真源。
