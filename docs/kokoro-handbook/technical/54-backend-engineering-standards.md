# Kokoro 后端工程规范：模块、契约、DTO、Repository 与 SQL

状态：当前 Goal 2 全局规范，2026-09-02。

本文是七个正式业务子仓库的工程实现规范。它不新增业务边界，不替代 Root `contract/`，也不要求
所有仓库机械套用完整 DDD。仓库复杂度由真实业务不变量决定，但依赖方向、DTO 边界、Repository
边界、SQL 事实归属和测试层次必须清晰可见。

## 1. 全局边界

```text
Web
  -> BFF
    -> IAM / System / Model / Billing / Capability / Storage / Scheduler
      -> Agent（仅执行链路需要时）
```

- Root 只维护跨仓 contract、生成物、架构规范、验证工具和文档，不拥有业务 Entity、Repository、Service 或业务表。
- 一个正式子仓库对应一个业务 owner；一个仓库可以包含多个内聚 module，不为每个名词创建一个服务。
- 跨仓只使用 Root contract 或 owner 明确发布的 API/RPC；不共享数据库、ORM model、SQL 文件或业务 DTO。
- `kokoro-bff` 是 Web 统一业务入口，但不读取 sibling 数据库；Chat 是 BFF 内部 module。
- Agent、Scheduler 等运行时型仓库按执行链路组织，不为形式上的 DDD 创建空的 Entity/Repository 层。

## 2. TypeScript 业务仓库的标准目录

标准 L1/L2 仓库采用业务 module 优先、层次局部化：

```text
src/
├── modules/
│   └── <bounded-module>/
│       ├── domain/
│       │   ├── model.ts                 # Entity / Aggregate / Value Object
│       │   ├── enums.ts                 # 只属于本 module 的状态和值
│       │   ├── errors.ts                # 领域错误
│       │   └── repository.ts            # Repository port（需要持久化时）
│       ├── application/
│       │   ├── commands/                # command input、handler、result
│       │   ├── queries/                 # query input、query service、result
│       │   ├── dto.ts                   # application DTO，不暴露 DB row
│       │   └── ports.ts                 # 外部服务、时钟、事务等 port
│       ├── infrastructure/
│       │   ├── postgres/                # 本 module 的 SQL/Repository 实现
│       │   ├── redis/                   # cache/lease/coordination adapter
│       │   └── providers/               # 第三方或跨仓 client
│       └── interfaces/
│           ├── http/                    # handler、request schema、response mapper
│           └── rpc/                     # RPC service、wire mapper
├── config/
├── bootstrap/
├── generated/                           # 只读生成物，禁止手改
└── main.ts                              # 只做 composition root 和启动
```

L0/L1 仓库可以减少目录，但必须保留以下可辨识边界：

```text
interface -> application -> domain port
infrastructure -> application/domain port
domain -> 不依赖 HTTP、Fastify、pg、Redis、provider SDK
```

禁止以下结构：

- 一个 `main.ts` 同时放 HTTP 路由、DTO、校验、业务流程、SQL、Repository 和启动装配；
- `src/common/`、`src/utils/`、`src/types/` 作为无 owner 的业务垃圾桶；
- `GenericRepository<T>`、万能 `BillingService` 或跨 module 的数据库 Repository；
- interface 层直接执行 SQL 或修改 domain 状态；
- generated 类型、DB row、domain model、HTTP response 共用同一个类型。

## 3. DTO、Domain、DB Row 和 Wire 类型

四类类型必须分开：

| 类型 | 所属位置 | 责任 |
|---|---|---|
| Wire/generated type | `generated/` 或 contract consumer | 跨仓字段编号和 wire 兼容 |
| Request/Response DTO | `interfaces/http`、`interfaces/rpc` | transport 校验和外部字段命名 |
| Domain model | `modules/*/domain` | 不变量、状态迁移、业务含义 |
| DB Row | `infrastructure/postgres` | SQL 列名、nullable、数据库类型 |

推荐显式命名：

```text
CreateUploadRequest       # HTTP/RPC 入参
CreateUploadCommand       # application 入参
Upload                    # domain model
UploadRow                 # PostgreSQL 查询结果
UploadResponse            # 外部成功 DTO
toUpload(row)             # Row -> Domain
toUploadResponse(upload)  # Domain -> Wire DTO
```

- HTTP handler 只负责解析 request、调用 application service、映射结果和错误。
- Application service 负责用例编排、权限入口、事务边界和调用 ports。
- Domain model 负责状态机和不变量，不接收未经验证的 HTTP body。
- DB Row 不得从 infrastructure 泄漏到 application/interface。
- `snake_case` 是外部 HTTP wire；内部 TypeScript 可以使用 `camelCase`。
- Protobuf generated enum/field 不重新定义；业务内部状态若不是跨仓字段，放在 module domain。

## 4. Service、Repository 和 Port

### Application Service

Application Service 是用例入口，例如：

```text
CreateUploadService
CaptureCreditHoldService
ResolveModelService
RegisterScheduleJobService
```

它负责：

1. 接收已解析的 Command/Query DTO；
2. 调用 IAM-derived identity 和授权 port；
3. 读取/修改 domain aggregate；
4. 通过 Repository port 持久化；
5. 在一个明确的事务内写入事实、receipt 和 outbox；
6. 返回 application result，不返回数据库驱动类型。

### Repository

- Repository port 放在 domain 或 application，取决于 module 依赖；实现放在 infrastructure。
- Repository 按 aggregate/fact owner 定义窄接口，例如 `CreditHoldRepository`、`ModelCatalogRepository`。
- Repository 负责参数化 SQL、锁顺序、租户条件、Row mapper 和事务内持久化。
- Query-only 列表可以使用专用 `QueryService` 或 read repository；不得把所有表包进一个 Repository。
- 一个 Repository 不跨 bounded context；跨仓数据只通过 API/RPC。

### Domain Service / Policy

- Domain Service 只承载跨实体但纯业务的规则；不执行 SQL、不发 HTTP。
- Provider、ObjectStore、IAM、Clock、IdGenerator 等外部能力用 port + adapter 表达。
- Strategy/Policy 用于可变规则，例如 credit burn order、model visibility、misfire policy。

## 5. API 契约规范

Root 与 owner contract 的职责固定为：

```text
Root contract
  = 跨仓 wire、身份上下文、字段、事件、兼容规则

Owner API_CONTRACT/docs
  = 本仓 route、DTO、状态机、错误映射、权限、配置和调用示例
```

统一要求：

- 成功：`{ data, meta: { request_id } }`；
- 错误：`{ error: { code, message, retryable?, details? }, meta: { request_id } }`；
- 外部 HTTP 字段使用 `snake_case`；
- 列表使用不透明 `cursor` 和 `data.next_cursor`，不把 offset 作为稳定协议；
- mutation 使用 `Idempotency-Key` 或 protobuf `CommandIdentity`；
- 异步资源返回稳定 `resource_id`/`run_id`，明确状态机、终态、取消、重试和 replay；
- 429 返回稳定错误码和 `Retry-After`；
- `Forwarded`、request id、tenant、subject、actor 只接受受信服务上下文；
- owner adapter 只做一次 DTO、错误和权限映射，不将 owner-only 字段泄露给 Web。

同一 mutation 的幂等实现必须包含：

```text
atomic claim -> pending/committed/retryable state -> durable receipt -> replay
```

仅有进程内 `Map` 或“执行后再 INSERT receipt”不构成并发幂等闭环。

## 6. PostgreSQL、Redis 和 SQL

- PostgreSQL 是业务事实源；Redis 只用于 cache、stream、queue、lease、限流和协调。
- 每个仓库只访问自己的 PostgreSQL schema；跨仓关系使用 API/RPC reference，不建跨仓 FK。
- 所有 SQL 使用 PostgreSQL `$1, $2, ...` 参数占位符和参数绑定；禁止字符串拼接。
- 每个写入用例明确事务边界、锁定对象、唯一约束和失败回滚语义。
- 余额、Hold、Commit、Refund、Ledger 等账务事实只通过 application service + transaction 修改。
- schema 是新系统唯一基线；migration 按唯一递增版本执行，文件名不可重复，checksum 必须校验。
- 当前目标是 clean build：不保留旧 route alias、旧数据库双写、兼容列、旧 ORM writer 或“暂时”分支。
- 迁移文件只用于当前 schema 演进；已退出的旧系统迁移计划和兼容层不进入 runtime source。
- 对象字节只通过 Storage ObjectStore；业务表保存 reference、hash、size、mime 和生命周期状态。

## 7. 测试结构

```text
test/
├── unit/          # domain/application 规则
├── integration/   # PostgreSQL/Redis/provider adapter
├── contract/      # Root/owner API wire parity
├── architecture/  # import、边界、禁止旧路径、SQL 规则
└── smoke/         # 独立启动、health/ready、最小真实 HTTP/RPC
```

每个 mutation 至少覆盖：

- 正向创建/更新；
- 字段校验和状态冲突；
- tenant/permission 隔离；
- 同 key 同 payload replay；
- 同 key 不同 payload conflict；
- 并发 duplicate claim；
- owner/DB/Redis 失败；
- retry、恢复和最终一致性；
- HTTP/RPC 响应与文档逐字段一致。

## 8. Go Scheduler 例外

`kokoro-scheduler` 使用 Go，但遵守相同边界：

```text
internal/domain       ScheduleJob、Occurrence、Lease、RetryPolicy
internal/application  register、trigger、pause、resume、dispatch
internal/ports        Clock、LeaseStore、TargetClient
internal/adapters     Redis、HTTP、config
internal/transport    HTTP handler、request/response DTO
cmd/scheduler         composition root
```

Scheduler 不拥有 Billing/Credit/ScheduledTask 业务事实，不连接业务数据库；目标业务 owner 负责 command receipt 和业务状态。

## 9. Clean-build 验收

一个仓库满足以下条件后，才算通过本规范：

1. 目录能看出 module、domain、application、infrastructure、interface 和启动装配；
2. 外部 DTO、domain model、DB Row、generated wire 类型分离；
3. Repository/service/port 的依赖方向由 architecture test 固化；
4. SQL 只有本仓事实，migration 序号唯一且可重复执行；
5. 没有旧 route、旧 writer、兼容 alias、跨仓数据库访问或未标记的 mock fallback；
6. API docs、实现、contract test、integration test 和 smoke test 一致；
7. 未完成能力记录为明确风险，不用 fixture 通过冒充生产闭环。

