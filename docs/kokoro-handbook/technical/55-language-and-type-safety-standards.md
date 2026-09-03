# Kokoro 语言、时间与类型安全工程规范

状态：V1 工程基线，2026-09-02。

本文将 Google、Microsoft、Alibaba、Python Typing、Pydantic、mypy、TypeScript 和 PostgreSQL 的公开规范提炼为 Kokoro 可执行的工程规则。外部规范用于校准通用工程实践；Kokoro 的 clean-slate、无外键和 owner 边界属于本项目自己的硬约束。

## 0. 时间标准：存储 UTC，表达 RFC 3339，业务时区显式化

Kokoro 对时间统一按“瞬时点（instant）”处理：数据库保存 UTC 语义，API 传 RFC 3339 时间戳，用户展示时再转换为用户或站点时区。UTC 是系统基准，但不把所有“日期”和“本地营业时间”机械转换成 UTC。

### 0.1 数据库

- 事件时间、审计时间、过期时间、发布时间、删除时间统一使用 PostgreSQL `TIMESTAMPTZ(3)`。
- `created_at`、`updated_at` 默认 `CURRENT_TIMESTAMP(3)`；应用写入使用注入的 UTC Clock，数据库默认值用于直接 SQL 写入和兜底。
- `updated_at` 不会因为 `DEFAULT` 自动更新；由 Repository 显式写入，避免隐藏副作用。
- 纯日期使用 `DATE`，例如账期日、生日、结算日；不要用午夜 UTC 冒充日期。
- 周期任务保存 `timezone`（IANA 名称，如 `America/New_York`）和本地规则；计算出的具体执行点另存为 `TIMESTAMPTZ(3)`。
- 禁止在事实表中混用 `created_at`、Unix 秒和无时区 `TIMESTAMP` 表示同一种时间。协议确实要求 Unix 时间时，只在边界层转换。
- 同一毫秒内的排序使用稳定 ID 或显式序号作为第二排序键，不能依赖时间精度解决并发顺序。

推荐公共字段：

```sql
created_at TIMESTAMPTZ(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
updated_at TIMESTAMPTZ(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3)
```

### 0.2 TypeScript、Python、Go

- TypeScript 使用 `Date` 表示瞬时点；进入领域层前必须是已校验的有效时间。字符串只允许存在于 DTO/协议边界，领域对象不传递任意时间字符串。
- Python 使用带时区的 `datetime`，创建当前时间使用 `datetime.now(timezone.utc)`；领域层禁止 naive `datetime`。
- Go 使用 `time.Time`，进入领域层统一调用 `.UTC()`；领域层禁止用裸字符串承载时间。
- 所有语言采用依赖注入的 `Clock`/`TimeProvider`，生产实现返回 UTC，测试实现返回固定时间。

### 0.3 API

- JSON 时间统一输出 RFC 3339 UTC，例如 `2026-09-02T12:34:56.123Z`。
- 接收带偏移量的 RFC 3339 时间时，边界层立即归一化为 UTC；响应不回显任意本地时区格式。
- 时区字段必须声明语义并校验为 IANA 时区名；不要接受含糊的 `CST`、`EST` 这类缩写。

## 1. 调研结论

海内外大厂没有一份完全统一的目录或 DDD 模板，但反复出现以下共同点：

1. 公开契约优先于内部实现；API 不镜像数据库表。
2. 类型检查、运行时校验、格式化、lint、架构检查和 CI 都应工具化。
3. 领域边界、数据 owner、事务边界和依赖方向比目录名称更重要。
4. 可重试 API 需要幂等语义、稳定错误和并发控制。
5. 规则分为 `MUST`、`SHOULD`、`MAY`，并为例外留下明确原因。

Google API Design Guide 采用 resource-oriented design 和 `List/Get/Create/Update/Delete` 标准方法；Microsoft REST Guidelines 强调显式版本、错误契约、分页、幂等与乐观并发；Alibaba P3C 将代码、异常、测试、安全、工程结构和数据库规则工具化。参考链接见本文末尾。

## 2. Python 规范

### 2.1 类型目标

新代码和被修改的公共 API 使用完整类型标注。Python 仍然是渐进式类型系统，类型标注本身不是运行时验证；因此系统边界同时需要运行时 schema 校验。

推荐工具链：

```text
ruff              格式化和静态 lint
pyright 或 mypy   静态类型检查
pytest            行为测试
Pydantic          HTTP/RPC/配置/第三方 payload 运行时校验
```

### 2.2 TypedDict 的正确位置

`TypedDict` 表达“运行时就是普通 dict，但静态上拥有固定字符串键”的数据形状。它适合：

```python
from typing import NotRequired, TypedDict


class EventMetadata(TypedDict):
    request_id: str
    source: str
    trace_id: NotRequired[str]
```

适用位置：

- 已经确定是 dict 形状的 JSON metadata；
- 内部轻量 payload；
- `**kwargs` 或结构化字典参数；
- 不需要行为、不变量和运行时转换的对象。

`TypedDict` 不负责运行时校验，也不适合作为 HTTP 请求、数据库 Row、领域聚合或带跨字段不变量的模型。外部输入使用 Pydantic：

```python
from pydantic import BaseModel, ConfigDict, Field


class CreateSkillRequest(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)

    display_name: str = Field(min_length=1, max_length=255)
    tags: list[str]
```

原则：

```text
TypedDict       = 静态 dict shape
Pydantic        = 边界运行时 validation / serialization
dataclass       = 内部数据对象或值对象
class           = 需要行为和不变量的聚合/实体
Protocol        = Repository、Clock、Client 等窄接口
```

### 2.3 Python 类型细则

- 边界输入默认 `strict=True`、`extra="forbid"`；确需扩展字段时显式记录原因。
- 新代码使用 `list[str]`、`dict[str, T]`、`str | None` 等现代语法。
- 函数参数优先使用 `Mapping`、`Sequence`、`Iterable` 等抽象类型；具体实现返回具体类型。
- `Any` 只在无法表达或第三方类型缺失的局部边界使用，并附原因；不让 `Any` 进入 Domain、Repository Port 或公开 API。
- 可以接受任意对象时使用 `object`，不要用 `Any`。
- Repository Port 使用 `Protocol`，具体 PostgreSQL/Redis 实现放 Infrastructure。
- 使用 `NewType` 或值对象区分 `TenantId`、`UserId`、`RunId` 等语义不同的字符串。
- 不用 `cast`、`type: ignore`、宽泛 `dict[str, Any]` 掩盖设计问题；例外必须局部、有原因、有测试。

推荐 mypy 起点：

```toml
[tool.mypy]
strict = true
warn_unused_configs = true
```

大型旧仓库可以按模块逐步收紧，但新模块应直接达到 strict；mypy 文档明确建议新代码增加标注，并以 `--strict` 作为目标。

## 3. TypeScript 规范

### 3.1 编译器基线

```json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noImplicitOverride": true,
    "noImplicitReturns": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true
  }
}
```

`strict` 提供更强的类型保证；`noUncheckedIndexedAccess` 会让未声明的索引访问包含 `undefined`；`exactOptionalPropertyTypes` 区分“字段缺失”和“字段存在但值为 undefined”。

### 3.2 `any`、`unknown` 和类型断言

```text
外部未知输入       unknown
运行时 schema 后    推导出的具体类型
确实任意对象       object
字典               Record<string, T>
Any                仅限局部、已解释的第三方或测试边界
```

外部 JSON 的标准路径：

```text
unknown
→ Zod/TypeBox/Valibot parse
→ Request DTO
→ Command/Query
```

类型断言 `as T` 和非空断言 `!` 不会插入运行时检查，应优先使用 schema、类型守卫或显式 mapper。接口适合描述结构化能力；类型别名适合 union、tuple、品牌 ID 和组合类型。领域聚合可以使用 class，但 DTO 和 Row 不需要为了形式改成 class。

### 3.3 TypeScript 分层

```text
interfaces       transport schema、request/response mapper
application      use case、command/query、transaction、ports
domain           aggregate、entity、value object、policy
infrastructure   SQL、Redis、HTTP client、SDK adapter
bootstrap        composition root
```

Generated wire type、Request DTO、Command、Domain Model、DB Row 和 Response DTO 分开定义。

## 4. SQL 与持久化规范

### 4.1 表结构

普通可变 tenant-owned 资源通常从以下基线开始：

```sql
    id          UUID           PRIMARY KEY,
    tenant_id   TEXT           NOT NULL,
    created_at  TIMESTAMPTZ(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at  TIMESTAMPTZ(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3)
```

这是基线而非机械模板。`status`、`version`、审计主体、`deleted_at`、`revision`、digest、幂等字段根据真实业务不变量选择。Event/Ledger 表通常是 append-only，只保留 `occurred_at` 等事实时间。

统一规则：

- 一个仓库统一 UUID、ULID 或 opaque text；
- 时间使用 `TIMESTAMPTZ`；
- 金额使用最小货币单位整数加 `currency_code`；
- 核心关系和查询字段使用普通列，不藏在 JSONB；
- `NOT NULL`、`CHECK`、`PRIMARY KEY` 和有业务语义的 `UNIQUE` 尽量由 schema 表达；
- 每个索引都要对应真实查询、排序、租户过滤或并发路径；
- `PRIMARY KEY` 和 `UNIQUE` 自动带来唯一索引，不重复创建等价索引。

### 4.2 外键与 JOIN

外键是数据库设计选项，不是全行业统一答案。单库、单 owner 内的强一致关系可以使用外键；跨服务关系通常通过 API/RPC、事件和本地 reference 维护。Kokoro V1 选择无外键，因此关系写入需要 tenant 校验、owner/permission 校验、状态校验、固定锁顺序、事务、UNIQUE/CHECK 和异步 reconciliation。

同一数据库、同一 owner、同一 bounded context 内允许 JOIN：

- Repository 或 Query Service 负责 JOIN；Application 负责业务语义和权限；
- JOIN 和 WHERE 都显式带 tenant 范围；
- 使用显式 `JOIN ... ON`，不用逗号隐式笛卡尔连接和 `NATURAL JOIN`；
- `INNER JOIN` 表示必需关系，`LEFT JOIN` 表示可选关系，存在性判断优先 `EXISTS`；
- 读取避免 N+1，使用明确列，避免 `SELECT *`；
- 列表使用稳定唯一排序和 keyset cursor；
- 跨仓库不做数据库 JOIN。

### 4.3 写路径

```text
BEGIN
→ tenant-scoped existence check
→ owner / permission check
→ state check
→ fixed-order row lock when required
→ write facts and relation
→ write receipt/outbox
→ COMMIT
```

SQL 使用参数绑定；动态排序、列名和表名使用白名单。Application 不拼 SQL，Repository 不决定业务授权。

## 5. API 规范

采用 Google 风格的资源和标准方法作为默认形态：

```text
GET    /v1/resources
GET    /v1/resources/{id}
POST   /v1/resources
PATCH  /v1/resources/{id}
DELETE /v1/resources/{id}
```

动作型业务使用明确 command，例如 `POST /v1/resources/{id}:publish` 或 RPC `PublishResource`。

统一要求：

- contract-first，OpenAPI/Proto/JSON Schema 作为唯一 wire source；
- explicit versioning；
- list 从首版就设计分页；
- 具备外部副作用且可能被重试的 mutation 具备 idempotency identity；需要异步恢复或结果重放时再使用 durable receipt；
- 错误包含稳定顶层 code、可诊断 message 和 request id；
- 长任务使用 `202`、operation/resource status 和 status endpoint；
- 修改竞争使用 ETag/If-Match 或等价的 version；
- API 只暴露领域契约，不暴露数据库列、ORM 类型和 provider 细节。

## 6. 落地顺序

```text
1. 冻结 owner、contract、状态机和数据库事实
2. 为每个仓库建立语言 strict baseline
3. 先拆边界类型和 ports，再移动 SQL/adapter
4. 为每个 use case 添加 unit/contract/integration/smoke 测试
5. 增加 architecture test、SQL lint、contract breaking check
6. 在 CI 执行 lint/typecheck/test/build/schema smoke
7. 按 bounded context 小步重构，不跨仓复制实现
```

## 7. 公开参考

- [Google TypeScript Style Guide](https://google.github.io/styleguide/tsguide.html)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Google Cloud API Design Guide](https://docs.cloud.google.com/apis/design)
- [Microsoft REST API Guidelines](https://github.com/microsoft/api-guidelines)
- [Alibaba Java Coding Guidelines / P3C](https://github.com/alibaba/p3c)
- [Python Typing Specification: TypedDict](https://typing.python.org/en/latest/spec/typeddict.html)
- [Python Typing Specification: Best Practices](https://typing.python.org/en/latest/reference/best_practices.html)
- [Pydantic Strict Mode](https://docs.pydantic.dev/latest/concepts/strict_mode/)
- [mypy strict checking](https://mypy.readthedocs.io/en/stable/command_line.html#cmdoption-mypy-strict)
- [PostgreSQL Constraints](https://www.postgresql.org/docs/current/ddl-constraints.html)
- [PostgreSQL Joins](https://www.postgresql.org/docs/current/queries-table-expressions.html)
- [PostgreSQL Indexes](https://www.postgresql.org/docs/current/indexes.html)
- [GitLab SQL Style Guide](https://handbook.gitlab.com/handbook/enterprise-data/platform/sql-style-guide/)
