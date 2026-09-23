# PostgreSQL 与 SQL 工程规范

状态：正式规范，2026-09-21 修订。

适用范围：Kokoro 所有 PostgreSQL schema、SQL、数据库访问代码、事务、索引与数据库测试。本文同时说明
PostgreSQL 的通用语义、规模化系统的成熟实践和 Kokoro V1 的强制 profile；不把具体 profile 扩大为所有数据库场景的唯一答案。

阅读路径：1–5 节确认项目规则与字段；6–13 节查类型、查询、事务和生命周期；15–16 节用于验收与新表评审。

## 1. 已确定的技术基线

Kokoro V1 统一采用：

```text
PostgreSQL
+ 每个数据 owner 选择一份唯一 canonical schema
+ TypeScript 使用本仓 ADR 选定的一种 ORM/数据访问栈
+ Python 使用 psycopg 3
+ 空数据库安装与 drift 校验
+ 应用层维护跨表关系
```

项目硬约束：

1. 每个数据 owner 仓库只维护一份 canonical schema：SQL-first 使用 `database/schema.sql`，ORM-first 可使用该 ORM 的
   canonical schema（例如 `prisma/schema.prisma`）。两种模式不得并存为可编辑事实源；生成 DDL/Client 必须只读并有 drift gate。
2. V1 clean-slate 不保留 `database/migrations/`、migration runner、migration ledger 或历史升级路径。
3. 正式 SQL 禁止 `FOREIGN KEY` 和 `REFERENCES`。无外键并非 Kokoro 独有：Alibaba 开发手册将禁用外键/级联列为强制项，
   Vitess 也明确不鼓励分片 keyspace 使用外键约束；Kokoro 采用这一常见的大规模分布式治理路线作为硬规则。
   PostgreSQL/Spanner 等数据库仍支持并在部分场景推荐 enforced foreign key，因此本文不把它描述成所有公司的统一规则。
4. `CREATE TABLE IF NOT EXISTS` 可以使用；它容忍已存在的同名表，不修复 schema drift；`db:apply-schema` 只检查目标 owner schema 是否为空，发现该 schema 非空就停止，不要求同库其他 owner schema 为空，绝不自动删库。
5. 所有值使用参数绑定；表名、列名、排序方向等不能参数化的结构只能来自代码白名单。
6. 本地与 CI 的应用目标是一个 PostgreSQL 实例、一个数据库和一套应用 role/credential；每个数据 owner 在同库使用独立 schema 与指向该 schema 的连接 URL。代码、Schema、查询、事务和测试继续禁止跨 owner SQL/JOIN、表引用、ORM model 与 canonical schema 共享；表名前缀不代替 owner schema。现有部分 installer/URL 仍锁定 `public` 或整库空白，须由 owner 代码切片改为 schema 边界后才能宣称单库应用组合通过。测试 fixture 临时库只是运行隔离，不是新增应用数据库或角色。每 owner 独立 production role、GRANT/REVOKE、数据库 mTLS 和 NetworkPolicy 属于部署阶段，不是当前开发门禁。

## 2. 数据所有权先于表设计

创建表前必须先回答：

```text
owner 是哪个服务和业务模块？
谁是唯一 writer？
资源的身份和生命周期是什么？
哪些状态转换必须原子完成？
哪些查询是线上真实路径？
保留、删除、审计和恢复策略是什么？
```

规则：

- 一张业务表只有一个 owner 和一个写入边界。
- 跨服务只保存 opaque reference 或必要快照，不复制对方的完整业务事实。
- 跨服务读取通过 API/RPC、事件投影或本仓快照完成，禁止跨 owner 数据库查询和 JOIN。
- 表不是按页面或 DTO 创建；同一个业务事实不能因多个接口复制成多张真源表。
- Redis、搜索索引、对象存储 metadata projection 和消息队列都不是 PostgreSQL 业务事实的替代品。

## 3. Schema 文件组织

每仓在技术方案/ADR 中二选一：

```text
SQL-first
  database/schema.sql
  scripts/apply-schema.ts|py

ORM-first（以 Prisma 为例）
  prisma/schema.prisma
  prisma.config.ts
  src/generated/prisma/       # 只读生成物
```

SQL-first 的 `schema.sql` 按以下顺序组织：

```text
1. 必要 extension
2. table
3. 真实需要的 table-level CHECK / UNIQUE
4. 有查询或约束证据的 index
5. COMMENT
```

要求：

- schema 应能在目标 owner 的全新空 schema 一次成功安装；不得要求其他 owner 的 schema 也为空。
- `db:apply-schema` 在执行前只确认目标 owner schema 为空，使用 owner 范围的 advisory lock 防止并发安装，并在事务可覆盖的范围内失败回滚。
- 安装后对 catalog 做 drift check：表、列、类型、默认值、约束和索引必须与预期一致。
- 开发样本与 schema 分开，放语言手册规定的 test(s)/fixtures；生产启动不自动 seed。产品必需的基础字典数据单独说明 owner 和安装规则，不与测试样本混放。
- SQL-first 不依赖 ORM 自动同步。ORM-first 的 schema apply 命令必须是仓库批准的显式命令，只允许目标 owner 空 schema（测试可使用隔离的临时库），生产启动不得
  “顺便修表”。无历史 migration 的 clean-slate 仓可以使用 `db push`；一旦进入有数据的持续演进阶段必须另立 ADR 选择 migration/expand-contract。

## 4. 命名规则

统一使用小写 `snake_case`。Kokoro 选择“owner 前缀 + 单数资源名”，例如：

```text
表                 system_site
                   billing_payment
                   platform_skill

主键               id
资源引用           site_id
跨服务不透明引用   provider_account_ref

普通索引           ix_<table>_<purpose>
唯一约束           uq_<table>_<purpose>
检查约束           ck_<table>_<purpose>
```

具体规则：

- 一个仓统一使用 `id` 作为本表主键；引用字段使用 `<resource>_id`。
- 名称必须避开 PostgreSQL 关键字，并控制在 PostgreSQL 63-byte identifier 上限内；超长名称先缩短业务词汇，
  不依赖数据库静默截断。
- 表名不用 `data`、`info`、`common`、`base`、`temp` 等无业务含义后缀。
- 缩写只使用团队公认术语，如 `api`、`rpc`、`url`；不把长业务名压成难懂首字母。
- 布尔字段表达肯定语义，如 `is_enabled`、`requires_approval`；同一状态机不同时使用 `status` 和多组可冲突布尔值。
- 显式命名业务 UNIQUE/CHECK 和自建索引，方便错误定位；内联 PRIMARY KEY/NOT NULL 可使用数据库生成名，不额外堆命名样板。

## 5. 字段基线：按表类型选择，不机械复制

### 5.1 普通可变 tenant 资源

“统一字段”是指**同一类表的名称、类型和语义统一**，不是所有表机械复制同一组列。Kokoro 的可变、用户可见、
需要恢复窗口的 tenant 资源默认使用：

```sql
CREATE TABLE IF NOT EXISTS system_site (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  site_key TEXT NOT NULL,
  display_name TEXT NOT NULL,
  created_at TIMESTAMPTZ(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updated_at TIMESTAMPTZ(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  deleted_at TIMESTAMPTZ(3) NULL
);
```

这是最小默认模板，故意不放 `status`、`version`、`UNIQUE`、业务 `CHECK` 和审计 actor。它们必须由真实业务语义逐项加入，
不得因为复制了新表模板就出现。

字段决策如下。表中“条件字段”表示条件不成立时必须省略，绝不是每表默认列：

| 字段                                       | 默认性          | 何时出现                                             | 规则                                                   |
| ------------------------------------------ | --------------- | ---------------------------------------------------- | ------------------------------------------------------ |
| `id`                                       | 资源表默认      | 表示有独立身份的资源                                 | `UUID PRIMARY KEY`，默认由应用生成；仓内策略一致       |
| `tenant_id`                                | 条件字段        | 数据由 tenant 拥有                                   | 与 owner 契约使用相同类型，每条访问路径显式过滤        |
| `created_at`                               | 普通资源默认    | 需要记录资源创建瞬时点                               | `TIMESTAMPTZ(3)`，不可被普通更新覆盖                   |
| `updated_at`                               | 条件字段        | 资源允许原地修改                                     | 每次真实变更由写入语句显式更新                         |
| `deleted_at`                               | Kokoro 资源策略 | 用户可见资源采用可恢复删除                           | 软删除标记；未删除为 `NULL`；非此类表省略              |
| `status`                                   | **默认不加**    | 存在两个以上有业务差异、转换受规则约束的生命周期状态 | 先定义状态、合法转换与终态；不能仅因“以后可能用到”添加 |
| `version`                                  | **默认不加**    | 用例明确采用乐观并发控制                             | 更新比较旧版本并原子递增                               |
| `created_by` / `updated_by` / `deleted_by` | **默认不加**    | 审计要求必须回答操作主体                             | 保存受信 actor 的 opaque ID                            |

不要默认加入：

```text
status、version、remark、description、metadata、extra、ext、sort、业务 UNIQUE/CHECK
```

这些字段只有在存在明确业务语义和查询/保留策略时才出现。

### 5.2 Append-only event、ledger、audit

Append-only 表通常使用：

```text
id / sequence
tenant_id（若属于 tenant）
aggregate_id 或 subject_id
event_type / entry_type
occurred_at
payload / amount / immutable facts
```

通常不使用 `updated_at` 和软删除。更正通过 reversal、补偿记录或新版本完成，禁止原地覆盖历史事实。

### 5.3 幂等 receipt 与 outbox 分开设计

只有可重试写命令或可靠事件发布需要时才建表。它是所属业务模块的内部一致性结构，不默认升级成独立
`command-receipts` 业务模块。

命令 receipt 按去重与重放需求选择：

```text
tenant_id
operation
idempotency_key
request_digest
status（只有持久化处理中/完成/失败状态时）
response_or_result_reference
created_at / completed_at / expires_at
```

唯一约束通常落在 `(tenant_id, operation, idempotency_key)`；相同 key 但不同 digest 必须冲突，不得返回旧结果。

Outbox 记录待投递事件，不复制上述 receipt 模板。按实际投递语义选择 event ID、类型/版本、payload、发生时间、
投递次数、下次尝试时间和已发布时间；需要多 worker 抢占时再增加租约信息。两类表都需规定去重窗口、清理和崩溃恢复。

## 6. 类型选择

### 6.1 ID

- 默认 `UUID`，由应用统一生成；如果选择 UUIDv7，生成库、时钟回拨行为和跨语言兼容必须固定并测试。
- 不在同一仓随意混用自增整数、UUID、ULID 和业务字符串。
- 外部 provider ID 通常使用 `TEXT` 并保留 provider namespace，不伪装成本仓主键。

### 6.2 时间

```text
瞬时点        TIMESTAMPTZ(3)，API 输出 RFC 3339 UTC（...Z）
纯日历日期    DATE
本地钟点      TIME + IANA timezone 字段
持续时长      BIGINT 毫秒或 INTERVAL，按使用场景明确选择
```

- `created_at`、`occurred_at`、`expires_at` 等瞬时点统一 UTC 语义。
- `TIMESTAMPTZ` 保存的是绝对 instant，不保存原始地区时区。数据库连接 session 固定为 `UTC`，API/日志统一输出
  RFC 3339 `Z`；用户选择的 IANA timezone 作为独立业务字段保存。
- 禁止用无时区 `TIMESTAMP`、naive datetime 或 Unix 秒列保存跨服务业务瞬时点。
- 周期任务保存本地规则与 IANA timezone，实际 occurrence 单独保存 UTC instant。
- 同一毫秒的严格顺序依赖 sequence、revision 或 ID，不假设 timestamp 唯一。

### 6.3 金额与精确数值

- 金额默认使用最小货币单位的 `BIGINT` 加 `currency_code`，例如 `amount_minor`。
- 汇率、比例、计量精度使用明确 scale 的 `NUMERIC(p, s)`；禁止 `REAL`/`DOUBLE PRECISION` 表示钱。
- 每个算术边界声明舍入模式；数据库和 TypeScript/Python 结果必须有交叉测试。

### 6.4 文本、枚举和 JSONB

- 默认使用 `TEXT`；只有确有字符数上限时才使用 `VARCHAR(n)`；`n` 计字符而非字节，协议字节上限须另行校验。
- 普通 CRUD 表默认不添加 `status`。只有资源确实存在状态机时才建该列；若状态可由 `deleted_at`、`expires_at`、
  `published_at` 等事实无歧义推导，则不再保存一份可能漂移的 `status`。
- 只有一个独立二值属性时优先使用语义明确的 boolean；“是否删除”仍由 `deleted_at` 表达，不创建
  `status = 'deleted'` 与其重复。
- 确实需要 `status` 时通常使用 `TEXT`，状态转换由业务代码控制。`CHECK (status IN (...))` 仍是单独设计决策，
  不是拥有 `status` 后的强制搭配；仅在值集合稳定且数据库拒绝非法值的收益高于演进成本时添加。
- `JSONB` 只保存开放 metadata、外部原始 payload 或版本化扩展对象；稳定且参与过滤、JOIN、唯一性的数据必须拆成普通列。
- JSONB 必须有 schema/version、大小上限、敏感信息策略和真实查询需求；不以它逃避建模。

### 6.5 NULL

`NULL` 必须代表明确的“未知、不适用或尚未发生”。禁止用空字符串、零、空 UUID、`'unknown'` 等 magic value
代替，也禁止为了少写插入字段而随意允许 NULL。

## 7. 无外键条件下的关系完整性

同库强关系使用数据库外键与由应用层维护关系，都是业界存在的成熟路线。高并发、分库分表和跨 owner 场景经常选择后者；
Kokoro V1 明确采用无外键 profile，因此必须用更完整的应用闭环补偿，而不是只删除约束。

每个关系写入固定执行：

```text
1. 从受信上下文取得 tenant/actor
2. 在 owner 边界确认被引用资源存在
3. 校验 owner、权限和资源状态
4. 对并发相关行按固定顺序加锁
5. 在同一事务写入关系与本仓事实
6. 依靠 PRIMARY KEY 和已明确选定的 UNIQUE/CHECK 保证本地不变量
7. 需要可靠事件发布时，同一事务写 outbox row；commit 后由 dispatcher 发布
8. 周期 reconciliation 检测 orphan、过期引用和投影漂移
```

额外要求：

- 引用列不会因外键自动获得索引；只在 JOIN、反向影响检查或线上过滤确实使用时建立对应索引。
- 删除 owner 资源前先执行影响检查；跨服务删除使用状态终止、事件通知和可重试清理，不做隐式级联。
- orphan 检测 SQL、修复策略和告警 owner 写入 `docs/DATA_MODEL.md` / `docs/RUNBOOK.md`。
- 本仓父记录的创建关系与删除路径必须采用同一套加锁协议，并在锁内重新校验状态；只在其中一边加锁仍有竞态。
- 跨服务资源的存在性检查只是当时快照，不承诺跨库原子性；明确引用失效时的补偿、重试或业务拒绝策略。
- “先查再写”不保证并发正确；仍需事务、锁、唯一约束或乐观版本。

## 8. JOIN 规则

JOIN 本身不是坏实践。允许范围：

```text
同一数据库 + 同一事实 owner + 同一业务边界
```

规则：

- 跨仓、跨数据库、跨 owner 禁止 JOIN；使用 API/RPC、事件投影或本仓快照。
- tenant-owned 表的 `ON` 和 `WHERE` 都必须保持 tenant 范围，不能只凭资源 ID 连接。
- 必需关系用 `INNER JOIN`；可选关系用 `LEFT JOIN`，右表过滤条件放置位置必须保留预期语义。
- 存在性判断优先 `EXISTS`；不要为了判断存在拉取整行或制造 `DISTINCT` 掩盖重复。
- 一次合理 JOIN 通常优于 N+1；但报表型巨型 JOIN 应转为明确 projection/read model，而不是污染写模型。
- 只选择需要列并为重名列显式 alias；禁止 `SELECT *`。

## 9. SQL 编写规范

### 9.1 参数绑定与 ORM

TypeScript 仓若选择 `pg`，使用 `$1`、`$2`：

```ts
await pool.query(
  `SELECT id, tenant_id, site_key, display_name,
          created_at, updated_at, deleted_at
     FROM system_site
    WHERE tenant_id = $1
      AND id = $2
      AND deleted_at IS NULL`,
  [tenantId, siteId],
);
```

Python psycopg 使用 `%s` 或 `%(name)s`，不得照抄 `$1`：

```python
cursor.execute(
    """
    SELECT id, tenant_id, site_key, display_name,
           created_at, updated_at, deleted_at
      FROM system_site
     WHERE tenant_id = %(tenant_id)s
       AND id = %(site_id)s
       AND deleted_at IS NULL
    """,
    {"tenant_id": tenant_id, "site_id": site_id},
)
```

动态结构使用白名单映射。禁止把客户端值直接拼入表名、列名、方向、JSON path 或 SQL fragment。

TypeScript 仓若选择 Prisma，普通 CRUD/query 使用生成的 typed Client；事务使用 `$transaction`，唯一冲突、事务冲突和条件更新
按 Prisma 稳定错误码/affected count 归一。业务 Service/Repository 不同时保留 `pg` 查询实现，也不因少数复杂查询临时形成双轨；
确需 raw SQL 时必须由本仓 ADR 明确用途、边界、参数化、测试和退出条件。

### 9.2 明确列和写入范围

- `SELECT`、`INSERT ... RETURNING` 明确列名。
- 每个 update 方法只更新该用例拥有的字段，不使用“把任意 object 自动转 SET”的万能 helper。
- 写入后检查 affected row count；乐观锁更新为零时返回稳定 conflict，而不是当作成功。
- 批量写声明 batch size、事务边界和部分失败语义。

### 9.3 分页

- 对外列表默认 opaque keyset cursor；排序必须稳定，并以唯一键收尾。
- 典型顺序：`ORDER BY created_at DESC, id DESC`。
- 对应索引按 tenant/filter/order 设计，例如 `(tenant_id, created_at DESC, id DESC)`。
- 后台小表可以使用 offset，但必须有最大 offset/limit；不得把数据库 offset 暴露为长期公开契约。

### 9.4 CTE、子查询和窗口函数

以可读性和执行计划决定，不设“CTE 一律好/坏”的机械规则。复杂 SQL 必须：

- 写清业务目的和输入规模；
- 使用真实或代表性数据运行 `EXPLAIN (ANALYZE, BUFFERS)`；
- 记录关键 plan、耗时和回归阈值；
- 避免通过层层视图/CTE 隐藏笛卡尔积和重复扫描。

## 10. 索引与约束

### 10.1 约束

约束是数据库最后一道并发完整性保护，但不是新表的装饰模板。每一个非 PK 约束都必须在 `docs/DATA_MODEL.md` 写出它保护的
业务不变量和演进方式。

- `PRIMARY KEY`：资源身份，资源表必须有。
- `NOT NULL`：只在“缺失值永远非法”时使用；这是字段语义，不是为了省默认值。
- `CHECK`：仅保护稳定的单行数据不变量；不将频繁变化的业务流程复制成数据库状态机。
- `UNIQUE`：仅用于真实业务唯一性、幂等身份或序列不变量。若业务允许重复，就不应为了查询加 `UNIQUE`。
- 对严格唯一不变量，仅在应用层执行“先查后写”会有并发竞争；必须使用数据库 `UNIQUE`/唯一索引或等价的串行化方案。
- 软删除后允许重用业务键时，可用 `WHERE deleted_at IS NULL` 的 partial unique index；若历史身份仍必须全局唯一，则不应使用 partial。
- PK/UNIQUE 已创建等价索引时不重复创建。业务 UNIQUE/CHECK 显式命名，但不创建没有需求的约束。

### 10.2 索引

每个索引提交时必须关联一条真实 query/constraint。设计顺序考虑：

```text
tenant / 等值过滤 -> 选择性过滤 -> 范围 -> 排序 -> 唯一 tie-breaker
```

不是固定口诀，最终以执行计划和数据分布验证。还应注意：

- partial index 只用于稳定、常用谓词，如未删除或 active 记录。
- `INCLUDE` 仅在 index-only scan 有证据收益时使用。
- 低基数字段通常不能单独成为有效索引。
- 索引增加写放大、锁和存储；无使用证据的索引应删除。
- 大表索引构建、锁影响和失败恢复必须在生产演进方案中说明；V1 owner 空 schema 安装不等于未来永远不需要 migration。

## 11. 事务、锁和并发

- 事务边界由业务 Service/use case 决定，Repository 执行同一 transaction 中的 SQL。
- node-postgres 事务中的全部语句必须使用同一个 checked-out client；不得用 `pool.query()` 分别执行
  `BEGIN`、业务 SQL 和 `COMMIT`。psycopg 同样在同一个 connection transaction 中完成。
- 事务内不调用不可控网络服务；需要可靠发布时，业务事实与 outbox row 在同一事务写入，commit 后由独立 dispatcher 发送。
- 所有并发写规定锁顺序，避免不同路径反向锁表/行。
- 需要读取后决定写入时使用 `SELECT ... FOR UPDATE`、乐观版本或原子条件更新；不得只靠进程内 mutex。
- isolation level 按不变量选择，并有并发测试；不是全部无脑 SERIALIZABLE，也不是默认级别永远足够。
- deadlock、serialization failure 只在整个操作具备幂等身份时有限重试，并使用退避与 jitter。

仅在该资源已选择 `version` 乐观并发时，更新示例为：

```sql
UPDATE system_site
   SET display_name = $1,
       version = version + 1,
       updated_at = CURRENT_TIMESTAMP(3)
 WHERE tenant_id = $2
   AND id = $3
   AND version = $4
   AND deleted_at IS NULL
RETURNING id, version, updated_at;
```

## 12. `updated_at`、触发器与数据库函数

- `updated_at` 由每条有效 mutation 显式更新；no-op 是否更新时间由业务语义统一决定。
- 不使用通用 trigger 偷偷修改业务字段、发布事件或编排跨模块流程。
- 技术性 trigger/数据库函数若确有必要，必须有 owner、测试、可观测性和 ADR；不能成为应用看不见的第二套业务逻辑。
- `CURRENT_TIMESTAMP(3)` 在事务内保持一致，这是多数审计写入需要的语义；若需要真实 wall-clock 差异，必须明确说明。

## 13. 数据保留、删除和敏感信息

- 每张含用户/审计/事件数据的表声明 retention、删除方式和 legal hold 需求。
- Kokoro 中可变、用户可见且有恢复需求的资源默认软删除；使用 `deleted_at TIMESTAMPTZ(3)`，活跃读路径必须包含
  `deleted_at IS NULL`。
- 对外 API 和业务方法仍命名为 `DELETE /v1/sites/{id}` / `deleteSite`；“默认软删除”是实现策略，不增加
  `safeDelete`、`soft=true`、`is_safe` 这类模糊标记。
- 软删除写入同时设置 `deleted_at`、`updated_at` 和必要 actor，重复删除语义在 API 契约中明确；恢复使用独立 `restoreSite` 用例。
- Append-only ledger/audit/event、outbox/receipt 保留数据、lease/session/临时数据、可重建 projection 与无独立恢复语义的关联表
  不机械添加 `deleted_at`；它们按 retention 物理清理、分区淘汰或重建。
- 隐私撤回、密钥/凭据泄漏和法定删除可要求物理删除或不可逆匿名化；软删除不得冒充合规删除。
- secret、token、密码和完整支付凭据不进入普通业务表；只保存 hash、密文或 secret handle，并明确 key rotation。
- 日志、错误和查询诊断不得输出连接串、参数中的敏感值或完整 payload。
- 大表归档/分区只在容量和访问模式有证据后引入；不为“未来可能很大”预建复杂分区体系。

## 14. 数据访问代码位置

数据访问放在所属业务模块的 Repository/Query 或简单 Service 中。小模块默认平铺：

```text
src/modules/sites/
  site.repository.ts
  site-search.query.ts           # 只有复杂独立读模型时才创建
```

文件继续增长时先按业务子能力拆目录；只在多个同类数据访问文件确实共同变化时才建 `repositories/`/`queries/`。不按数据库品牌建立
`postgres/`，也不建立 `infrastructure/persistence/postgres/` 这种只增加路径长度的包装。Redis 业务文件按 cache/event/lease 职责命名，
不按驱动品牌分组。

Repository 在这里指“该模块的数据访问组件”，不是 Git 仓库，也不是 ORM。默认只有一个具体实现，不再配套创建
`ISiteRepository`、`SiteRepositoryPort`、`PgSiteRepository` 三件套。复杂读模型可以使用 `*.query.ts`，不必强行
伪装成 Aggregate Repository。

使用 Prisma 时，连接生命周期由唯一 `PrismaService`/DatabaseModule 管理；业务文件使用 `SiteRepository`，不使用
`PostgresSiteRepository`、`PrismaSiteRepository` 等把已确定技术栈重复写入每个类名。简单 CRUD 可以由 Service 直接使用 Prisma；
复杂查询、幂等状态机、共享写入策略或独立测试边界出现后再增加 Repository class。

## 15. 验证门禁

每个持久化 owner 至少验证：

```bash
pnpm db:apply-schema       # 或对应 Python/Go 命令；目标 owner schema 必须为空
pnpm test:integration
pnpm test                  # 包含 schema/architecture checks
```

CI 阻断：

1. `database/migrations/`、migration ledger 或第二份可编辑 schema；唯一 canonical schema 的位置由本仓技术方案/ADR 确定；
2. `FOREIGN KEY`、`REFERENCES`；
3. 无时区 `TIMESTAMP`、浮点金额、未命名业务 UNIQUE/CHECK；
4. `SELECT *`、疑似字符串拼接 SQL、错误的参数占位符；
5. tenant-owned query 缺失 tenant predicate；
6. 跨 owner 表名或数据库访问；
7. 冗余/无用途索引和没有业务解释的 UNIQUE；
8. route/controller 中出现 SQL；
9. schema 安装、集成、并发、幂等或 drift 验证缺失。

## 16. 新表评审清单

```text
1. owner、唯一 writer 和所属业务模块是什么？
2. 是资源表、关系表、事件/账本、receipt/outbox，还是投影？
3. 每个字段的类型、NULL、默认值和保留语义是什么？
4. 哪些 UNIQUE/CHECK 是真实业务不变量？
5. 无外键后，存在性、删除、orphan 和 reconciliation 如何闭环？
6. 线上读写 SQL 是什么，索引分别服务哪条 query？
7. tenant 条件、稳定排序和并发冲突如何处理？
8. 时间、金额、敏感信息和 JSONB 是否正确建模？
9. fresh install、drift、integration、concurrency 如何验证？
10. 是否真的需要这张表，还是复制了另一 owner 的事实？
```

完成这些设计项后再创建表和索引。静态扫描只检测语法与可识别模式；tenant 正确性、查询性能、并发完整性与 retention
需要真实数据库测试及人工评审，正则零命中不代表全部正确。

## 17. 参考依据

- [PostgreSQL: Constraints](https://www.postgresql.org/docs/current/ddl-constraints.html)
- [PostgreSQL: Date/Time Types](https://www.postgresql.org/docs/current/datatype-datetime.html)
- [PostgreSQL: Indexes](https://www.postgresql.org/docs/current/indexes.html)
- [PostgreSQL: Using EXPLAIN](https://www.postgresql.org/docs/current/using-explain.html)
- [PostgreSQL: Transaction Isolation](https://www.postgresql.org/docs/current/transaction-iso.html)
- [GitLab: Database development guidelines](https://docs.gitlab.com/development/database/)
- [GitLab: Adding database indexes](https://docs.gitlab.com/development/database/adding_database_indexes/)
- [GitLab: Query performance guidelines](https://docs.gitlab.com/development/database/query_performance/)
- [GitLab: Constraint naming conventions](https://docs.gitlab.com/development/database/constraint_naming_convention/)
- [Alibaba P3C: 建表规约](https://github.com/alibaba/p3c/blob/master/p3c-gitbook/MySQL%E6%95%B0%E6%8D%AE%E5%BA%93/%E5%BB%BA%E8%A1%A8%E8%A7%84%E7%BA%A6.md)
- [Alibaba P3C: 索引规约](https://github.com/alibaba/p3c/blob/master/p3c-gitbook/MySQL%E6%95%B0%E6%8D%AE%E5%BA%93/%E7%B4%A2%E5%BC%95%E8%A7%84%E7%BA%A6.md)
- [Vitess: Are foreign keys supported?](https://vitess.io/docs/faq/getting-started/compatibility/are-foreign-keys-supported-in-vitess/)
- [Google Cloud Spanner: Foreign keys](https://cloud.google.com/spanner/docs/foreign-keys/overview)
- [node-postgres: Queries](https://node-postgres.com/features/queries)
- [node-postgres: Transactions](https://node-postgres.com/features/transactions)
- [Prisma ORM: Database drivers](https://www.prisma.io/docs/orm/v7/core-concepts/supported-databases/database-drivers)
- [Prisma ORM: Relation mode](https://docs.prisma.io/docs/orm/prisma-schema/data-model/relations/relation-mode)
- [Prisma CLI: db push](https://www.prisma.io/docs/cli/db/push)
- [psycopg 3: Transactions management](https://www.psycopg.org/psycopg3/docs/basic/transactions.html)

参考方法是“吸收经过规模验证的评审和故障经验”，不是整本照搬：PostgreSQL 官方文档决定数据库语义；GitLab 公开规范用于索引成本、
query plan 和 database review 经验；Alibaba P3C 与 Vitess 证明无外键是大规模系统的成熟治理路线，而不是 Kokoro 自创。
P3C 是 MySQL 规范，其 unsigned type、行数阈值和执行计划术语不照搬到 PostgreSQL；Spanner/GitLab 对外键的不同选择也说明
是否 enforced 必须服从系统形态，不能以“大厂”二字代替架构分析。

“V1 无外键、无历史 migration、单一 canonical schema”是 Kokoro 的硬规则。其中无外键与公开的大规模分布式实践一致；
其余条款必须能追溯到 PostgreSQL 语义、真实查询/故障或当前项目决策。
