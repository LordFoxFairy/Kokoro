@CLAUDE.md

# Kokoro 后端工程规范手册

本文件是本仓库及其子仓库的长期工程控制手册。所有 Agent 在开始工作前自动读取并遵循本文件，规则已经明确时直接执行，不重复向用户确认。

本文件规定通用工程原则；当前仓库的业务 owner、跨仓契约、目录事实和实施状态分别以以下文档为准：

1. `docs/CURRENT.md`
2. `docs/CODEBASE_MAP.md`
3. `docs/ARCHITECTURE_STANDARD.md`
4. 各子仓自己的 `README.md`、`docs/API_CONTRACT.md` 和技术设计文档

## 一、基本原则

1. 先确认业务 owner、公开契约、数据 owner 和依赖方向，再修改代码。
2. 一个文件承担一个清晰职责；一个业务事实只能有一个 owner。
3. 优先按 bounded context / 业务模块组织代码，层次在模块内部保持清晰。
4. 领域规则、应用编排、基础设施实现、传输协议和启动装配彼此分离。
5. DTO、领域模型、数据库 Row、生成代码和 HTTP/RPC Response 使用不同类型。
6. 设计以可测试、可观测、可回滚、可独立发布为目标，不以目录数量或 class 数量作为质量指标。
7. 不为了形式上的 DDD 创建空层；CRUD 简单模块保持简单，但边界必须明确。

## 二、标准分层

```text
src/
  bootstrap/                 # 依赖装配、启动、关闭
  config/                    # 环境变量和运行配置解析
  domain/                    # 聚合、实体、值对象、领域规则、Repository Port
    <bounded-context>/
      model/
      enum/
      repository/
      service/
  application/               # 用例、Command、Query、DTO、事务和外部 Port
    <bounded-context>/
      dto/
      service/
      mapper/
  infrastructure/            # PostgreSQL、Redis、外部服务和 SDK 的具体实现
    repository/
    client/
  interfaces/                # HTTP、RPC、CLI 等协议适配
    http/
    rpc/
```

依赖方向固定为：

```text
interfaces -> application -> domain
bootstrap -> concrete infrastructure + application
infrastructure -> domain/application ports
```

### Domain

- 只表达业务不变量、状态机、聚合行为和值对象。
- 保持对 HTTP 框架、数据库驱动、ORM、Redis、RPC 和第三方 SDK 的独立性。
- Repository 在 Domain 或 Application 定义接口，具体实现放在 Infrastructure。

### Application

- 一个公开用例对应一个明确的 handler、service 或 function。
- 负责权限入口、事务边界、Repository 调用、外部 Port 编排、幂等和结果组装。
- 不向上层泄露数据库连接、ORM 对象或数据库 Row。

### Infrastructure

- 负责参数化 SQL、数据库事务、锁、缓存、队列、HTTP client 和 SDK 适配。
- 负责 `Row -> Domain` 与 `Domain -> Row` 的转换。
- 外部依赖通过窄接口接入，不将供应商类型传播到 Domain。

### Interfaces

- 负责请求解析、运行时 schema 校验、鉴权上下文读取、错误映射和响应转换。
- 不直接执行 SQL，不实现业务状态迁移，不绕过 Application。

## 三、类型和 API 规范

统一数据流：

```text
Request DTO -> Command/Query -> Domain Model -> DB Row -> Response DTO
```

强制区分：

```text
CreateOrderRequest       # 传输层请求
CreateOrderCommand       # 应用层命令
Order                    # 领域聚合
OrderRow                 # 数据库查询结果
OrderResponse            # 对外响应
```

API 规范：

1. Root protobuf、OpenAPI 或 JSON Schema 是 wire contract 的唯一事实源。
2. 生成代码只生成，不手工修改。
3. HTTP 使用明确版本，例如 `/v1/...`；资源名称使用名词，动作使用明确 command。
4. 外部 HTTP 字段使用 `snake_case`，内部 TypeScript 使用 `camelCase`。
5. 成功响应统一为 `{ data, meta }`，错误响应统一为 `{ error, meta }`。
6. 错误使用稳定 machine-readable `code`；内部异常堆栈、SQL 和 provider 原文不直接返回。
7. 列表使用 opaque cursor 和明确的 limit 上限，不把数据库 offset 直接暴露为稳定协议。
8. 写操作使用明确的 idempotency identity、request digest、状态和 durable receipt。
9. tenant、subject、actor、request id 等安全上下文来自受信服务上下文，不从请求体推导。
10. 异步操作必须明确 `202`、资源状态、终态、取消、重试和 replay 语义。
11. 每个公开 endpoint 或 RPC 都要有正向、非法输入、权限、重复请求和依赖失败测试。

## 四、数据库和 SQL 规范

通用规则：

1. PostgreSQL 保存业务事实；Redis 只承担 cache、queue、stream、lease、限流和协调。
2. SQL 全部使用参数绑定，禁止字符串拼接。
3. 每个写用例明确事务边界、锁顺序、并发冲突和失败回滚语义。
4. tenant-owned 表的查询、更新和删除显式带 tenant predicate。
5. `UNIQUE` 只表达真实业务不变量，并在 schema owner 文档中说明语义。
6. 索引根据实际查询、排序、租户隔离和锁竞争设计，不为“可能以后查询”堆积索引。
7. NULL、时间、金额、digest、状态值和分页排序规则必须显式定义。
8. 跨 bounded context 使用 API/RPC，不共享数据库表、ORM schema 或 SQL 文件。

SQL 基线字段按生命周期选择：普通 tenant-owned 资源通常有 `id`、`tenant_id`、`created_at`、
`updated_at`；`status`、审计主体、`version`、`deleted_at`、`revision`、digest 和幂等字段只在
真实业务需要时加入。时间使用 `TIMESTAMPTZ`，金额使用最小货币单位整数加 currency，核心字段不藏在
JSONB 中，append-only event/ledger 保留发生时间而不是机械添加 `updated_at`。

同一数据库和 bounded context 内允许 JOIN，由 Repository/Query Service 执行；Application 决定业务
语义和权限。tenant-owned 表参与 JOIN 时显式限定 tenant；跨仓库使用 API/RPC。读取优先一次合理 JOIN
而非 N+1，存在性判断使用 `EXISTS`，查询使用明确列和稳定 keyset cursor，写竞争使用固定锁顺序和
`FOR UPDATE`。无外键的关系写入必须完成 tenant-scoped existence、owner/permission、state、锁、
单事务写入和 UNIQUE/CHECK 闭环。

### Kokoro V1 当前硬约束

以下属于本项目 clean-slate 规则，不包装成所有公司的统一行业标准：

1. 每个正式仓库只有一份 canonical `database/schema.sql` 或唯一 canonical ORM schema。
2. `database/migrations/`、迁移表、迁移编号、migration runner 和旧兼容 schema 均移除。
3. `db:apply-schema` 只向空数据库安装当前 schema，不执行历史升级逻辑。
4. 正式仓库 SQL 不使用 `FOREIGN KEY` 或 `REFERENCES`；跨表关系由应用事务、Repository 查询和状态校验维护。
5. 旧表、旧字段、旧索引、旧 DTO、旧 endpoint、旧 header、旧 token、fallback、双读双写和 compatibility alias 均删除。
6. 生产 `src/` 不放 InMemory、Fake、Fixture 或 test-only provider；测试替身放在 `test/fixtures/` 或 `test/doubles/`。
7. `sse-compat` 等合法协议值不属于兼容层；静态检查使用精确标识符，避免宽泛关键字误报。

## 五、测试和质量门禁

测试目录建议：

```text
test/
  unit/          # Domain 和 Application 的纯规则
  integration/   # 真实 PostgreSQL、Redis、ObjectStore、provider adapter
  contract/      # API/RPC wire contract
  architecture/  # import、目录、SQL 和 owner 边界
  smoke/         # 独立启动、health、ready 和最小真实请求
  fixtures/      # 固定输入和输出
  doubles/       # 测试替身
```

TypeScript 仓库在提交前执行：

```bash
pnpm lint
pnpm typecheck
pnpm test
pnpm build
pnpm db:apply-schema
```

其中 `lint` 必须是真实静态检查，不得只是 `typecheck` 的别名。架构检查至少覆盖：

- Domain 对框架和基础设施的依赖；
- Interfaces 直接访问数据库；
- 跨 bounded context 的内部 import；
- 生产源代码中的测试替身；
- migration、外键和兼容标识符；
- tenant predicate、参数化 SQL 和公开 contract 对齐。

Scheduler 执行：

```bash
gofmt -w .
go vet ./...
go test ./...
go build ./...
```

Agent 的报告不等于验证完成；主工作区必须重新执行真实验证命令。

## 六、Agent 执行方式

1. 任务开始先读取本文件、当前状态文档、代码地图、目标子仓 README 和相关 contract。
2. 多文件或架构变更先列出目标目录、依赖方向、行为保持项、删除项和验证命令。
3. 规则已经明确时直接按规则执行，不反复询问同一问题。
4. 发现现有代码与规范冲突时，以当前用户指令、本文件和当前正式架构文档为准，清理错误旧路径。
5. 修改前检查工作区状态和相关调用方；不覆盖其他协作者的未提交修改。
6. 新增抽象前先确认真实用例和 owner；不增加万能 Service、万能 Repository、无 owner 的 common/utils。
7. 代码、schema、contract、测试和文档必须一起收敛；只改文档不算完成架构重构。
8. 完成前报告修改文件、验证命令、验证结果、已知风险和未完成项。
