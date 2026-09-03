# Kokoro 后端工程规范：模块、契约、DTO、Repository 与 SQL

状态：当前 Goal 2 全局规范，2026-09-02。

本文是七个正式业务子仓库的工程实现规范。它不新增业务边界，也不要求
所有仓库机械套用完整 DDD。仓库复杂度由真实业务不变量决定，但依赖方向、DTO 边界、Repository
边界、SQL 事实归属和测试层次必须清晰可见。

## 1. 全局边界

```text
Web
  -> BFF
    -> IAM / System / Model / Billing / Capability / Storage / Scheduler
      -> Agent（仅执行链路需要时）
```

- Root 只维护架构规范、验证工具和文档，不拥有跨仓 contract、生成物、业务 Entity、Repository、Service 或业务表。
- 一个正式子仓库对应一个业务 owner；一个仓库可以包含多个内聚 module，不为每个名词创建一个服务。
- 跨仓只使用事实 owner 明确发布的 API/RPC；不共享数据库、ORM model、SQL 文件或业务 DTO。
- `kokoro-bff` 是 Web 统一业务入口，但不读取 sibling 数据库；Chat 是 BFF 内部 module。
- Agent、Scheduler 等运行时型仓库按执行链路组织，不为形式上的 DDD 创建空的 Entity/Repository 层。

### 1.1 七个正式子仓的目标边界

七个仓库不要求拥有相同数量的目录；统一的是 owner、依赖方向、契约和数据事实归属：

| 子仓 | 主要 bounded context | 目标实现重点 |
|---|---|---|
| `kokoro-iam` | tenant、identity、authentication、authorization、audit | 拆出 Auth/AuthZ 用例；删除迁移运行时；Repository 只拥有身份与权限事实 |
| `kokoro-system` | site、workspace、runtime manifest、system policy | 删除生产路径 InMemory；统一 PostgreSQL 参数占位符和 UTC 时间；配置发布状态由领域模型维护 |
| `kokoro-model` | model catalog、provider、availability、routing policy | 合并为唯一 canonical schema；删除 `db:migrate`/重复 init SQL；外部 provider 只经 client port |
| `kokoro-billing` | payment、subscription、checkout、credit、ledger、reconcile | 将账务状态机和事务收敛到 application/domain；从 38 个历史迁移重建 V1 schema；禁止跨模块万能 service |
| `kokoro-capability` | skill、MCP connector、installation、authorization、receipt/outbox | 继续当前 clean-slate 拆分；生产代码不放 InMemory，测试替身只在 `test/fixtures`/`test/doubles` |
| `kokoro-storage` | blob、upload、asset、artifact、scan | 收敛 `adapters`/`modules` 重复层；业务表只存对象元数据与引用；对象字节只走 ObjectStore |
| `kokoro-scheduler` | schedule、occurrence、lease、retry、dispatch | 使用 Go `cmd` + `internal/{domain,application,ports,adapters,transport}`；只发送业务 command，不拥有 Billing 事实 |

当前重构顺序：先处理 IAM/System/Model 的基础边界，再处理 Billing/Storage 的数据重建，Capability
在现有重构完成后接入统一门禁，Scheduler 独立按 Go 布局收敛。每个仓库单独完成验证后再进入下一仓，
不在同一仓同时保留新旧两套实现。

## 2. TypeScript 业务仓库的标准目录

正式 TypeScript 业务仓库统一采用“顶层分层、层内按 bounded context 组织”。这样既能一眼看出依赖方向，
又不会把多个业务域塞进一个 `service.ts`。`modules/` 不能再和顶层四层并存为两套重复实现层。

```text
src/
├── domain/
│   └── <bounded-context>/
│       ├── models/                       # Entity / Aggregate / Value Object
│       ├── enums/                        # 只属于本 context 的状态和值
│       ├── errors/                       # 领域错误
│       └── repositories/                 # Repository port
├── application/
│   └── <bounded-context>/
│       ├── commands/                     # command、handler、result
│       ├── queries/                      # query、read model、result
│       ├── dto/                          # application DTO，不暴露 DB row
│       ├── mappers/                      # 类型映射
│       └── ports/                        # 外部服务、Clock、事务等 port
├── infrastructure/
│   ├── repositories/<bounded-context>/  # PostgreSQL/Redis 实现
│   └── clients/<dependency>/             # 第三方或跨仓 client
├── interfaces/
│   ├── http/                             # handler、request schema、response mapper
│   └── rpc/                              # RPC service、wire mapper
├── config/
├── bootstrap/
└── generated/                            # 只读生成物，禁止手改
```

小型仓库可以减少目录，但必须保留以下可辨识边界：

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
| Domain model | `domain/<bounded-context>` | 不变量、状态迁移、业务含义 |
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

契约归属固定为：

```text
事实 owner 仓库的 API_CONTRACT/docs
  = 本仓 route、DTO、状态机、错误映射、权限、配置和调用示例

Root
  = 仓库归属、架构原则、拓扑和验证入口；不保存跨仓 wire source
```

统一要求：

- 成功：`{ data, meta: { request_id } }`；
- 错误：`{ error: { code, message, retryable?, details? }, meta: { request_id } }`；
- 外部 HTTP 字段使用 `snake_case`；
- 列表使用不透明 `cursor` 和 `data.next_cursor`，不把 offset 作为稳定协议；
- 具备外部副作用且可能被重试的 command 使用 `Idempotency-Key` 或 protobuf `CommandIdentity`；天然幂等的 GET、DELETE 和明确的状态设定操作不为形式强加幂等层；
- 异步资源返回稳定 `resource_id`/`run_id`，明确状态机、终态、取消、重试和 replay；
- 429 返回稳定错误码和 `Retry-After`；
- `Forwarded`、request id、tenant、subject、actor 只接受受信服务上下文；
- owner adapter 只做一次 DTO、错误和权限映射，不将 owner-only 字段泄露给 Web。

需要 durable replay 的 mutation，其幂等实现必须包含：

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
- schema 是新系统唯一基线；V1 clean-slate 只保留一份 `database/schema.sql` 或唯一 canonical ORM schema，空库安装由 `db:apply-schema` 负责。
- 当前目标是 clean build：不保留旧 route alias、旧数据库双写、兼容列、旧 ORM writer 或“暂时”分支。
- 不保留 `database/migrations/`、迁移表、迁移编号和 migration runner；本地及 CI 通过删除并重建 fresh database 验证当前 schema。
- 对象字节只通过 Storage ObjectStore；业务表保存 reference、hash、size、mime 和生命周期状态。

## 7. 测试结构

```text
test/
├── unit/          # domain/application 规则
├── integration/   # PostgreSQL/Redis/provider adapter
├── contract/      # 本仓 contract 与 transport parity
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

## 9. 生产可靠性与可观测性

目录和类型清晰不等于生产级。每个可部署仓库还必须具备：

- 结构化日志，至少包含 `request_id`、`trace_id`、service、operation、tenant scope 和结果；禁止记录 token、密码、完整支付载荷和敏感个人数据；
- OpenTelemetry trace、metric、log 三类信号，外部调用和数据库查询可关联到同一 trace；
- HTTP/RPC client 明确 connect/read/overall timeout；只对可重试的瞬时错误重试，并使用指数退避和 jitter；
- PostgreSQL pool 上限、statement timeout、transaction timeout、慢查询记录和连接关闭；
- graceful shutdown、请求取消、worker drain、队列 lease 恢复和重复投递测试；
- health 与 readiness 分离，readiness 必须反映关键依赖是否可用；
- SLI/SLO、错误预算、告警阈值和故障演练记录；
- 依赖锁定、SBOM、镜像 provenance/signature、secret scan 和安全更新流程。

OpenTelemetry 将 trace、metric、log 作为跨语言的可观测性信号；它是 instrumentation/规范层，
不是业务日志平台本身。[OpenTelemetry Documentation](https://opentelemetry.io/docs/)

## 10. Clean-build 验收

一个仓库满足以下条件后，才算通过本规范：

1. 目录能看出 module、domain、application、infrastructure、interface 和启动装配；
2. 外部 DTO、domain model、DB Row、generated wire 类型分离；
3. Repository/service/port 的依赖方向由 architecture test 固化；
4. SQL 只有本仓事实，canonical schema 可在 fresh database 中重复安装；
5. 没有旧 route、旧 writer、兼容 alias、跨仓数据库访问或未标记的 mock fallback；
6. API docs、实现、contract test、integration test 和 smoke test 一致；
7. 未完成能力记录为明确风险，不用 fixture 通过冒充生产闭环。

## 11. 生产级认证门槛

“顶级标准”不是目录看起来像 DDD，而是每个仓库都能提供可复核证据。以下任一 P0 项不通过，仓库
就只能标记为原型或重构中，不能标记为生产级：

| 维度 | 必须有的证据 |
|---|---|
| Owner/边界 | owner、does-not-own、跨仓 API/RPC、依赖图和 architecture test |
| 类型/代码 | strict typecheck、真实 lint、禁止未解释的 `any`/cast/ignore、生成物 provenance |
| 数据/SQL | 唯一 canonical schema、fresh install、参数化 SQL、tenant 隔离、事务/锁/约束测试 |
| API | OpenAPI/Proto/JSON Schema、错误码、版本、分页、幂等、contract test、breaking check |
| 可靠性 | timeout、retry policy、backoff、取消、graceful shutdown、重复投递和故障恢复测试 |
| 可观测性 | trace/metric/log、request_id/trace_id 关联、关键 SLI/SLO、告警和 runbook |
| 安全 | service authentication、授权边界、secret scan、敏感字段脱敏、依赖和镜像扫描 |
| 发布 | CI 阻断规则、可回滚构建、SBOM、镜像 provenance/signature、环境配置审计 |
| 性能 | 关键查询 `EXPLAIN` 证据、连接池边界、容量基线、p95/p99 延迟与吞吐数据 |

每个仓库的验收记录必须同时包含“命令、版本、时间、结果、失败项和责任人”，不能只写“已验证”。
Google SRE 将 SLI、SLO 和 error budget 作为管理生产服务的基础，而不是上线后的附加监控。[Google SRE: Service Level Objectives](https://sre.google/sre-book/service-level-objectives/)
