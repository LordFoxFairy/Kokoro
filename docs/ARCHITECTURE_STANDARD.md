# Kokoro 正式子仓统一工程规范 v1

状态：Goal 2 重构基线，2026-09-02。

本文是当前所有 active 子仓库的实现规范（Web、BFF、Agent，以及 IAM、System、Model、Billing、Capability、Storage、Scheduler）。子仓库的 `API_CONTRACT`、本仓技术设计和测试可以细化本文，不能重新定义目录分层、租户隔离和数据库约束规则。

## 1. 设计依据与统一取舍

本规范不是把某一套目录名当成“大厂标准”。Microsoft 的 DDD 微服务参考架构明确区分
Domain、Application、Infrastructure 和 Web，并建议 Repository interface 与实现分离；同时也明确说明，
简单 CRUD 服务不必强行套完整 DDD。NestJS 把 feature module 作为大型应用的组织方式，Go 官方生态则常见
`cmd`、`internal` 和按 package 聚合的布局。因此本项目统一的是**依赖方向、边界和文件职责**，不是机械禁止
`adapter`、`infrastructure` 或 `module` 这些词。

依据：

- [Microsoft: DDD-oriented microservice](https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/ddd-oriented-microservice)
- [Microsoft: infrastructure persistence and Repository](https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/infrastructure-persistence-layer-design)
- [NestJS: Modules and feature modules](https://docs.nestjs.com/modules)
- [Go project layout: cmd/internal](https://github.com/golang-standards/project-layout)

因此，TypeScript 子仓库采用以下默认布局；必要时可以按 bounded context 做局部 feature module，但必须遵守同样的依赖规则：

```text
src/
  bootstrap/                 # 组合根：配置、repo、service、transport 装配
  config/                    # 环境变量解析与启动配置
  domain/<bounded-context>/
    model/                   # 聚合根、实体、值对象、领域不变量
    enum/                    # 领域枚举和状态
    repository/              # Repository interface/port
    service/                 # 必要的 domain service
  application/<bounded-context>/
    dto/                     # use-case 输入/输出 DTO，不暴露数据库 row
    service/                 # application use case，保持薄
    mapper/                  # domain/application/transport 映射
  infrastructure/
    repository/<bounded-context>/ # PostgreSQL/Redis repository 实现
    client/<dependency>/          # IAM、Storage、MCP、provider client
  interfaces/http/            # HTTP 协议映射、鉴权入口、统一 envelope
  interfaces/rpc/             # RPC 协议映射和 generated message 转换
```

规则：

- `infrastructure` 是合法的实现层；`adapter` 是实现角色而不是必须的顶层目录。一个仓库不同时建立
  `adapters/` 和 `infrastructure/` 两套同义实现层，也不把任何一个当成万能收纳目录。
- `modules/` 只有在它明确表示 bounded context/feature module 时才可以存在；不能用来逃避
  `model`、`application`、`repository` 和 `service` 的职责拆分。
- `common/`、`utils/` 不作为无边界业务收纳目录；确实跨域复用的纯技术原语应有明确 owner 和 API。
- 不把整个业务压在一个 `service.ts`、`models.ts` 或 `application.ts` 中；一个文件只承担一个明确的 use case、aggregate、repository 或 transport concern。
- `domain` 不依赖 `application`、`infrastructure` 和 transport；`application` 只协调 domain；具体 PostgreSQL、Redis、HTTP provider 实现在 `infrastructure`，只由 `bootstrap` 注入。
- `interfaces` 只做协议转换，不持有领域规则；DTO 不等于 ORM 类型，model 不等于 DTO。
- Mock/Fixture 默认放在 `test/fixtures/` 或 `test/doubles/`；只有明确支持 local runtime 的内存实现才可以进入
  `infrastructure`, 且不能被 production bootstrap 默认装配。
- 空的 README-only 目录、没有 owner 的旧目录、旧 compatibility alias 和搬空后的目录必须删除。

推荐的 Capability 终态示例：

```text
src/
  domain/skill/{model,enum,repository,service}/
  domain/mcp/{model,enum,repository,service}/
  application/skill/{dto,service,mapper}/
  application/mcp/{dto,service,mapper}/
  infrastructure/repository/{skill,mcp,command}/
  infrastructure/client/{iam,storage,secret,mcp-provider}/
  interfaces/http/
  interfaces/rpc/
  bootstrap/
```

## 2. DDD 依赖方向

```text
interfaces                  -> application service -> domain model/repository contracts
bootstrap                   -> concrete repository/client + application service + interfaces
infrastructure.repository  -> domain repository contracts + database driver
infrastructure.client      -> external wire/SDK only
domain                      -> no database, Redis, HTTP, RPC, framework import
```

Repository interface 放在 domain，具体 Repository 放在 infrastructure；`client` 是跨仓或 provider 的外部边界。
跨仓资源只保存 opaque ID 和必要的快照，不读取对方数据库。业务状态、权限判断、幂等和状态迁移属于
domain/application service，不属于 transport 或 repository SQL 拼装函数。

## 3. 租户与资源标识

- `tenant_id` 是跨仓 opaque isolation context；每个业务查询、更新、删除和事务都必须显式带 tenant predicate。
- `site_id` 只属于 System；System 通过 `tenant_id + host` 解析 Site，其他仓库不复制 Site 表，也不把 Site 作为 IAM 事实。
- 资源主键使用 opaque `id`；主键不因为租户隔离再制造 `(tenant_id, id)` 的冗余唯一约束。
- 跨聚合、跨模块、跨仓引用由 service 在同一业务事务或明确的 saga/补偿流程中校验；跨仓由公开 API/RPC 校验。

## 4. PostgreSQL 约束红线

- 所有 active 子仓库的 schema、migration、Prisma 生成 SQL 和测试数据库中均禁止 `FOREIGN KEY`、`REFERENCES` 和任何外键约束。
- 关系完整性由 application transaction、tenant predicate、资源存在性检查、状态机和 outbox/补偿机制维护。
- `PRIMARY KEY` 保留为资源身份约束。
- `UNIQUE` 只保留以下三类：
  1. 真实业务自然键，例如 tenant 内的 `site_key`、provider 外部号、版本号；
  2. 幂等键，例如 `(tenant_id, command_name, idempotency_key)`；
  3. 明确的一对一或序列约束，例如一个 settlement 只能对应一个 reversal。
- 禁止为外键服务而添加 `(tenant_id, primary_id)`、`(tenant_id, child_id)` 等冗余 UNIQUE；禁止以复合 UNIQUE 伪装跨聚合关系。
- 每个 UNIQUE 必须在本仓 `SCHEMA_OWNER_INVENTORY` 或技术设计中写出业务语义；没有业务语义的 UNIQUE 直接删除。

### 4.1 Schema 基线字段

“公共字段”是按表的生命周期和 owner 选择的基线，不是所有表无条件复制一套字段。普通可变的
tenant-owned 资源通常包含：

```sql
id          UUID        PRIMARY KEY,
tenant_id   TEXT        NOT NULL,
created_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
updated_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
```

项目可以统一使用 UUID、ULID 或 opaque text，但一个仓库内应保持一致；不要同时混用自增整数、UUID
和随机业务字符串。`tenant_id` 只出现在 tenant-owned 表中；global catalog 表不添加没有语义的
tenant 列。

按实际不变量选择以下字段：

- `status`：存在生命周期状态机时使用，并配合 `CHECK`；不要用多个互相矛盾的 boolean 代替状态机；
- `created_by`、`updated_by`：需要审计主体时使用 opaque identity reference；
- `version`：需要乐观并发控制时使用非负整数；
- `deleted_at`、`deleted_by`：只有软删除是业务语义时使用；删除语义不明确时保留明确状态或物理删除；
- `revision`、`content_sha256`、`idempotency_key`：只在版本、内容寻址或幂等确实存在时使用；
- append-only event/ledger 表保留 `occurred_at`，通常不添加无意义的 `updated_at`。

统一约定：时间使用 `TIMESTAMPTZ` 并按 UTC 解释；金额使用最小货币单位整数加 `currency`，不使用
浮点数；核心查询字段使用明确列，不把 `metadata_json` 当作关系字段；可空性、默认值和状态转换都在
schema 与 application 中分别表达清楚。

### 4.2 JOIN 与跨表关系

- 同一数据库、同一业务 owner、同一 bounded context 内允许 JOIN；JOIN 由 Infrastructure 的
  Repository 或 Query Service 执行，Application 决定业务用例和权限语义。
- 跨仓库、跨数据库和跨 owner 不做 JOIN，使用 API/RPC、快照或明确的异步投影。
- tenant-owned 表参与 JOIN 时，JOIN 条件和过滤条件都带 tenant 范围，避免只按资源 ID 连接。
- 读取详情或列表时优先使用一次合理 JOIN，避免 N+1；写入关系时先由 Application 校验业务
  关系，再由 Repository 在同一事务中执行参数化 SQL。
- `INNER JOIN` 表示关联记录必须存在；可选关系使用 `LEFT JOIN`，其过滤条件放在 `ON` 时保持
  左连接语义；存在性判断优先使用 `EXISTS`，不为了判断存在而拉取整行。
- 查询显式列名，避免 `SELECT *`；稳定分页使用 `(created_at, id)` 等唯一排序键的 keyset cursor，
  不把 offset 当作长期 API 协议。
- 写路径涉及竞争时使用固定锁顺序和 `SELECT ... FOR UPDATE`；Repository 负责 SQL 锁，Domain
  负责状态转换，二者不互相越界。

### 4.3 无外键项目的关系维护

外键是否使用不是所有公司的统一答案：同一数据库内强一致关系通常可以使用外键；跨服务数据库本来
就无法使用跨库外键。Kokoro V1 选择不使用外键，因此每个关系写入必须具备以下闭环：

```text
tenant-scoped existence check
→ permission/owner check
→ state check
→ fixed-order row lock when concurrent
→ write relation and fact in one transaction
→ UNIQUE/CHECK protection for local invariants
→ failure rollback and, for async flows, reconciliation evidence
```

Application 负责“是否允许建立关系”，Repository 负责“如何查询和写入关系”，SQL 负责参数绑定、锁和
本地约束。JOIN 可以用于一次读取关系，不能替代权限判断，也不能把跨仓业务事实拼成一个数据库查询。

### 4.4 SQL 文件和执行规则

- canonical schema 按 extension、类型、表、索引、注释的顺序组织；每张表写明 owner 和关键不变量；
- clean-slate `db:apply-schema` 在事务中执行当前 schema；schema 不通过 `IF NOT EXISTS` 静默掩盖旧表；
- 所有 INSERT、UPDATE、DELETE 和 SELECT 使用参数占位符；禁止拼接用户输入、动态表名和排序字段；
- 动态排序使用白名单映射，分页和批处理使用稳定唯一排序；
- 每个索引都要对应真实查询或并发访问路径；索引顺序优先考虑 tenant、过滤列和排序列；
- 不把业务状态转换写进难以测试的触发器；复杂规则放在 Domain/Application，schema 保留 NOT NULL、
  CHECK、PRIMARY KEY 和有业务语义的 UNIQUE。

## 5. V1 clean-build policy（目标门禁）

当前产品按 V1 clean-build 收敛，尚未上线的数据不作为兼容约束。因此最终形态不建立历史迁移链，也不保留旧代码兼容层：

- 每个仓库只有一份 canonical schema（Prisma 仓库的 `schema.prisma` 同时必须生成无外键 SQL）；
- 不创建 `database/migrations/`，不创建 `*_schema_migrations` ledger，不扫描历史 migration；
- 本地和 CI 使用 fresh database，重复验证先销毁再重建；
- 删除旧表名、旧字段、旧 endpoint、旧 header、旧 token、旧 DTO 和旧业务目录，不做双读、双写、alias 或 fallback；
- `dist/`、generated client、generated protobuf 只由当前源码重新生成，旧生成物不作为兼容入口；
- 新契约直接采用 V1 最终形态，破坏旧本地调用方不需要兼容窗口。

因此目标态的 `db:apply-schema` 含义是“在空数据库安装当前 V1 schema”，不是升级任意历史数据库。收敛期间如某仓仍有 migration/FK/旧兼容实现，必须在该仓的状态文档中列为未完成项，并在进入发布门禁前删除；检查应该失败并提示重建，而不是吞掉错误继续运行。

## 6. API 与测试门禁

每个仓库的 `API_CONTRACT/docs` 必须说明 request/response、错误码、`request_id`、`Idempotency-Key`、分页 cursor、事件、权限和 tenant 边界。测试至少覆盖：

- 正向、字段校验、资源状态机；
- tenant 越权和错误身份；
- 幂等重放、并发冲突、失败重试、恢复和 outbox；
- schema 禁止外键、禁止冗余 tenant-primary UNIQUE；
- 本仓真实启动、PostgreSQL/Redis smoke 和 BFF v1 mock 联调。

## 7. 重构顺序

先改本规范和本仓目录树，再改 API contract/docs，再改 model/dto/service/repo，再改 SQL，最后补 fixture、测试和启动验证。当前没有迁移/兼容要求时，直接删除旧路径并保留一套 canonical schema；不通过别名、双读写或历史目录维持旧实现。
