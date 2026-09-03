@CLAUDE.md

# Kokoro Agent 工程规范手册

本文件是 Kokoro Root 与七个正式业务子仓的长期工程控制手册，使用中文维护。它不是建议清单，而是
Agent 执行代码、Schema、API、测试和文档任务时的默认工作契约。规则已经明确时直接执行，不重复向用户
询问已经决定的目录、时间、SQL、外键、迁移和兼容层规则。

## 0. 适用范围与权威顺序

适用仓库：`kokoro-iam`、`kokoro-system`、`kokoro-model`、`kokoro-billing`、
`kokoro-capability`、`kokoro-storage`、`kokoro-scheduler`。Root 只拥有架构文档、部署编排、质量门禁和仓库拓扑，不拥有跨仓 API contract，也不拥有七仓的业务表、Entity、Repository 或业务 Service。每个 active repository 自己维护本仓 contract、Schema、generated code 和 CI。

规则冲突时按以下顺序处理：

```text
系统/平台指令
-> 当前用户明确要求
-> 本文件
-> docs/CURRENT.md、docs/CODEBASE_MAP.md、docs/ARCHITECTURE_STANDARD.md
-> docs/kokoro-handbook/technical/54-*.md、55-*.md
-> 当前子仓 README、API contract、技术设计
-> 历史报告、旧方案、归档文档
```

历史文档只用于考古，不得重新成为代码、Schema、部署或 API 的实现依据。

## 1. 总原则

1. 一个业务事实只有一个 owner；一个仓库只访问自己的数据库事实。
2. 一个文件只承担一个清晰职责；禁止用 `service.ts`、`models.ts`、`repositories.ts` 收纳整个业务。
3. 先确认 owner、契约、状态机、事务边界和依赖方向，再修改实现。
4. 领域规则、应用编排、基础设施、传输协议和启动装配分离。
5. DTO、Command/Query、Domain Model、DB Row、Generated Wire Type、Response 必须区分。
6. 不为了形式上的 DDD 创建空层；简单 CRUD 可以少建目录，但不能越过依赖边界。
7. 规则必须同时落在代码、测试、架构检查和 CI，不只写在 Markdown 中。
8. 时间瞬时点统一按 UTC 存储和传输；日期、本地时间和周期任务时区必须显式建模。

## 2. TypeScript 标准目录与命名

正式 TypeScript 业务仓采用“顶层分层、层内按 bounded context 组织”：

```text
src/
  domain/
    <bounded-context>/
      models/
      enums/
      errors/
      repositories/              # Repository port
      services/                  # 纯业务 Domain Service，非编排 Service
  application/
    <bounded-context>/
      commands/
      queries/
      dto/
      mappers/
      ports/                     # Clock、外部 Client、事务等抽象
  infrastructure/
    repositories/<bounded-context>/
    clients/<dependency>/
    persistence/                 # 仅在有明确技术职责时使用
  interfaces/
    http/
    rpc/
  config/
  bootstrap/
  generated/                     # 只读生成物
```

命名规则：

```text
架构层：domain/application/infrastructure/interfaces/config/bootstrap
同类文件目录：models/enums/errors/repositories/services/commands/queries/mappers/ports/clients
缩写和协议：dto/api/http/rpc/sql 保持约定写法，不强行写成 dtos/apis
文件：单数职责名，例如 user.ts、user-repository.ts、create-user.ts
```

禁止：

- 同时保留 `src/modules`、`src/adapters` 与新的四层作为重复实现层；
- `common/`、`utils/`、`types/` 成为无 owner 的业务垃圾桶；
- HTTP handler 直接执行 SQL；
- Infrastructure 类型泄漏到 Domain/Application；
- ORM Entity 同时充当 Request DTO、Domain Model 和 Response。

## 3. 依赖方向与各层职责

```text
interfaces -> application -> domain
bootstrap -> application + concrete infrastructure
infrastructure -> domain/application ports
domain -> 不依赖 HTTP、Fastify、pg、ORM、Redis、RPC、provider SDK
```

### Domain

- Entity、Aggregate、Value Object、状态机、领域错误和纯业务规则。
- Repository port 放在 Domain；只读投影或外部能力 port 可放 Application。
- 不处理 HTTP body、数据库 Row、事务连接、Redis、日志实现和第三方 SDK。

### Application

- 一个公开用例对应一个明确的 command/query handler、use-case service 或 function。
- 负责授权入口、事务边界、Repository 调用、外部 Port 编排、幂等和结果组装。
- 不返回 ORM 对象、数据库连接或 `Row`。

### Infrastructure

- 实现 Repository、PostgreSQL、Redis、ObjectStore、外部 HTTP/RPC 和 provider adapter。
- 负责参数化 SQL、锁、事务执行、`Row <-> Domain` mapper 和错误归一。
- 不在 SQL Repository 中决定业务授权或状态机规则。

### Interfaces

- 负责请求解析、运行时 Schema 校验、受信上下文读取、响应映射和错误映射。
- 不执行 SQL，不直接修改 Domain，不绕过 Application。

## 4. 类型安全

### TypeScript

六个正式 TypeScript 子仓统一使用 `pnpm@11.25.0` 与单一 `pnpm-lock.yaml`；不并存 npm/yarn lockfile，CI、
release 和本地验证使用同一 package manager 与 frozen lockfile。

所有新代码目标：

```json
{
  "strict": true,
  "noUncheckedIndexedAccess": true,
  "exactOptionalPropertyTypes": true,
  "noImplicitOverride": true,
  "noImplicitReturns": true,
  "noUnusedLocals": true,
  "noUnusedParameters": true
}
```

```text
外部 JSON/未知值 -> unknown -> Zod/TypeBox/Valibot 校验 -> 具体 DTO
数据库 Row       -> 独立 Row 类型 -> mapper -> Domain/Application 类型
any              -> 仅限局部第三方边界，并写出原因
```

禁止使用 `as T`、非空断言 `!`、宽泛 `any` 掩盖校验、空值和类型设计问题。DTO、Command、Domain
Model、DB Row、Response 各自定义；不要因为减少 mapper 就合并类型。

### Python

```text
TypedDict  = 静态 dict shape，不负责运行时校验
Pydantic   = 外部输入、配置和第三方 payload 的运行时校验
dataclass  = 内部数据对象和值对象
class      = 需要行为、不变量和状态迁移的 Entity/Aggregate
Protocol   = Repository、Clock、Client 等窄 Port
```

新代码使用完整标注，目标为 Pyright strict 或 `mypy --strict`。边界模型默认 strict、extra forbid；
`Any`、`cast`、`type: ignore` 只能局部使用并注明原因。领域时间使用带时区 `datetime`。

### Go

`go vet`、`go test`、必要时 `-race` 为基础门禁。公共函数显式返回 error；外部请求携带可取消的
`context.Context`；领域时间使用 `time.Time`，进入领域层统一 `.UTC()`。Go 只使用官方仍支持的版本并在
`go.mod` 固定补丁版本；当前 Scheduler 基线为 `go 1.26.8`，构建镜像同时固定 tag 与 digest。

## 5. API 规范

1. 每个事实 owner 仓库的 protobuf、OpenAPI 或 JSON Schema 是本仓 Wire Contract 的唯一事实源；Generated 文件只在本仓生成，不手改。Root 不保存跨仓 wire source。
2. HTTP 使用显式版本，例如 `/v1/...`；资源使用名词，动作使用明确 command。
3. 外部 JSON 使用 `snake_case`，内部 TypeScript 使用 `camelCase`。
4. 成功统一 `{ "data": ..., "meta": { "request_id": ... } }`；错误统一 `{ "error": { "code", "message", "details?" }, "meta": { "request_id" } }`。
5. 错误 `code` 稳定可编程；不返回 SQL、堆栈、provider 原文或 secret。
6. 列表默认 opaque cursor，明确最小/最大 limit 和稳定排序；长期公开协议不暴露数据库 offset。
7. 具备外部副作用且可能被重试的 command 使用 `Idempotency-Key` 或 `CommandIdentity`，保存 request digest；需要异步恢复或结果重放时使用 durable receipt。
8. GET/HEAD 通常天然幂等，DELETE 和明确状态设定的 PUT 可按契约实现幂等，不为形式强加重复 receipt。
9. 异步任务明确 `202`、资源状态、终态、取消、重试、replay 和失败恢复。
10. tenant、subject、actor、request id、service identity 来自受信服务上下文，不从 body 推导。
11. 修改竞争使用 `version`、ETag/If-Match 或等价并发条件。

### 5.1 Contract、Protocol 与 Generated 的边界

`contract/`、`protocol/` 和 `generated/` 不是三套可以互相复制的 DTO 目录。它们的职责必须固定：

```text
事实 owner 仓库/
  contract/                  # 本仓对外 API/RPC/Event 的可审查契约事实源
    openapi/                 # HTTP/OpenAPI（若本仓提供 HTTP）
    proto/                   # RPC/Protobuf（若本仓提供 RPC）
    json-schema/             # 独立 JSON 消息（若本仓确有此边界）
    tests/                   # schema lint、breaking、consumer/producer contract tests
  src/generated/             # 由 contract 或已固定外部协议生成；只读，不手改
  src/protocol/              # 本仓自有跨进程协议的运行时模型/编码适配
  src/interfaces/            # HTTP/RPC handler、mapper、error mapping
```

规则：

1. Root 只维护仓库拓扑、架构决策、部署编排和治理脚本；Root 不得重新建立一个跨仓 `contract/`、
   共享业务 DTO 包或跨仓生成器。一个 owner 仓库不应再把同一份契约复制成 Root、消费者和实现三份可编辑来源。
2. `contract/` 只描述当前仓库拥有或直接承接的边界，不放数据库 schema、ORM Entity、Domain Model、
   Application Command 或别的仓库的 API。API 文档可以引用外部资源，但不复制外部资源的业务事实。
3. 消费方可以使用生成的 client/type，但必须来自版本固定的发布 artifact、明确的本地 contract snapshot
   或供应方仓库的固定 commit，并记录版本、来源和 digest。禁止手改 generated 文件，禁止把 generated
   类型当作 Domain Model、DB Row 或持久化输入。
4. `protocol/` 只承载本仓真正拥有的跨进程消息、命令、事件和编码规则。它不是把所有外部服务 DTO
   汇总进来的公共目录；外部服务 payload 必须在 `infrastructure/clients/<owner>/` 边界解析成窄类型。
5. Redis stream 名称、key 构造器、TTL、consumer group 和连接参数是基础设施细节，放在
   `infrastructure/redis/`；稳定的消息 envelope/schema 可以由 `protocol/` 拥有。两者不定义重复字段。
6. 简单服务可以只有 `contract/` 和 `interfaces/`，不因目录模板强行创建空的 `protocol/`、`generated/`
   或完整 DDD 层。目录的存在必须对应真实边界和可验证职责。
7. 契约变更顺序固定为：owner 先修改 contract -> 运行 lint/schema/breaking/contract tests -> 重新生成
   client -> 更新实现与消费者 -> 运行 integration/smoke -> 在 commit 中同时提交契约、生成物、测试和文档。
   Generated 物的 provenance 必须指向本仓 contract 版本，而不是已经删除的 Root 路径。

Python Agent 的推荐落点是：

```text
src/kokoro_agent/
  protocol/                  # control.py、events.py 等 Agent 自有跨进程模型
  domain/                    # Entity、Value Object、规则
  application/               # use case、command/query、窄 Port
  infrastructure/            # postgres、redis、外部 client 的实现
  interfaces/                # HTTP/RPC/event ingress/egress 映射
```

`repositories/` 不是必须的顶层层级。Repository Port 应放在实际 owner 的 `domain/<context>/repositories/`
或 `application/<context>/ports/`，transport-neutral record 放在同一 context；具体实现只放
`infrastructure/<technology>/repositories/`。只有在 Agent 已经形成稳定的跨 context execution
repository package 时，才保留顶层 `repositories/`，并且不得与另一套同名 Port/实现并行存在。

## 6. 时间规范

```text
数据库事实：TIMESTAMPTZ(3)
默认值：CURRENT_TIMESTAMP(3)
API：RFC 3339 UTC，例如 2026-09-02T12:34:56.123Z
TypeScript：Date
Python：datetime + timezone.utc
Go：time.Time.UTC()
```

- `created_at`、`updated_at`、`occurred_at`、`expires_at`、`published_at`、`deleted_at` 使用 `TIMESTAMPTZ(3)`。
- 纯日期使用 `DATE`；本地营业时间使用 `TIME + IANA timezone`。
- 周期调度保存 IANA 时区和本地规则，具体 occurrence 保存 UTC instant。
- 应用注入 `Clock`/`TimeProvider`；测试使用固定时间。
- 不用 Unix 秒、naive datetime 或无时区 `TIMESTAMP` 表示数据库事实。
- 同一毫秒内的顺序使用 ID 或序号作为第二排序键。

## 7. PostgreSQL 与 SQL 规范

### Schema

每个正式仓库只保留一份当前 Schema：`database/schema.sql` 或唯一 canonical ORM schema。普通
tenant-owned 资源通常使用：

```sql
id          UUID           PRIMARY KEY,
tenant_id   TEXT           NOT NULL,
created_at  TIMESTAMPTZ(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
updated_at  TIMESTAMPTZ(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3)
```

按真实不变量选择：

```text
status          有生命周期状态机时使用，并配合 CHECK
version         需要乐观并发控制时使用
created_by      需要审计主体时使用
deleted_at      真实软删除语义存在时使用
revision        有版本概念时使用
idempotency_key 有重试幂等语义时使用
occurred_at     Event/Ledger 的事实时间
```

- 金额使用最小货币单位整数加 `currency_code`，禁止浮点金额。
- 核心查询字段使用普通列；JSONB 只保存结构化 metadata，不替代关系字段。
- 每个 `UNIQUE` 必须有业务语义；不为查询方便或模拟外键堆唯一约束。
- 每个索引必须对应真实查询、排序、tenant 过滤、唯一性或并发路径；PK/UNIQUE 已自动建立的等价索引不重复创建。
- Event、Ledger、Audit 通常 append-only，不机械添加 `updated_at`。

### SQL 命名与 Schema 编排

- 表名、列名、索引名、约束名全部使用小写 `snake_case`；表名使用 owner 前缀加单数资源名，例如 `billing_payment`、`system_site_host`。
- 单仓内统一选择 `id` 或 `<resource>_id` 作为主键命名；资源引用使用 `<resource>_id` 并与 owner 契约一致；跨仓引用使用带语义的 opaque reference，例如 `provider_account_ref`。
- 索引命名使用 `ix_<table>_<purpose>`，唯一约束使用 `uq_<table>_<purpose>`，检查约束使用 `ck_<table>_<purpose>`；每个约束名必须可读。
- Schema 文件按 extension/type、表、约束、索引、注释顺序组织；表注释写明 owner、生命周期和关键不变量。
- `NULL` 表示“未知/不适用/尚未发生”的明确语义；不是为了少写默认值而允许 NULL。
- `status` 使用有限状态集合和 `CHECK`；不要用多个互相矛盾的 boolean 表示同一个状态机。
- 动态 SQL 的表名、列名和排序字段只能来自白名单，值全部使用参数绑定。

### Kokoro V1 数据库硬约束

以下是本项目 clean-slate 取舍，不宣称为全行业统一标准：

1. 不保留 `database/migrations/`、迁移表、迁移编号和 migration runner。
2. `db:apply-schema` 只在空数据库安装当前 Schema，不执行历史升级。
3. 正式 SQL 禁止 `FOREIGN KEY` 和 `REFERENCES`；关系由 Application、Repository、事务、锁、状态校验和 reconciliation 维护。
4. 删除旧表、旧字段、旧索引、旧 DTO、旧 endpoint、旧 header、旧 token、fallback、双读双写和 compatibility alias。
5. 生产 `src/` 不放 InMemory、Fake、Fixture 或 test-only provider；测试替身放 `test/fixtures/`、`test/doubles/`。
6. `CREATE TABLE IF NOT EXISTS` 可以使用，便于本地重复安装；它不负责修复 Schema drift，fresh database 和 drift check 仍然必需。
7. 本地七仓共享一个 PostgreSQL 实例和一个 Redis 实例；依赖可以是本机进程或各一个容器，但禁止每仓重复启动。各仓使用独立 PostgreSQL database/schema 与固定 Redis logical DB：IAM=1、System=2、Model=3、Billing=4、Capability=5、Storage=6、Scheduler=7。应用开发进程只从源码以 `pnpm dev`/`go run` 启动，应用容器只用于发布候选镜像 smoke。

### SQL 执行与 JOIN

- PostgreSQL 使用 `$1`、`$2` 等参数绑定；禁止拼接用户输入、动态列名、表名和排序字段。
- 动态排序使用白名单映射；查询使用明确列，不使用 `SELECT *`。
- 同一数据库、同一 owner、同一 bounded context 内允许显式 `JOIN ... ON`。
- tenant-owned JOIN 的连接条件和过滤条件都必须带 tenant 范围。
- 存在性判断优先 `EXISTS`；读取避免 N+1；公开列表使用稳定 keyset cursor。
- 跨仓库、跨数据库、跨 owner 禁止数据库 JOIN，使用 API/RPC、快照或异步投影。
- 关系写入按以下顺序执行：tenant existence -> owner/permission -> state -> fixed-order lock -> 同一事务写关系和事实 -> commit。
- Repository 负责 SQL、锁和 Row mapper；Application 负责用例、权限入口和业务语义。

## 8. 七个子仓的 owner 边界

| 子仓 | 只拥有的事实 |
|---|---|
| `kokoro-iam` | Tenant、Identity、Authentication、Authorization、Role、Permission、Audit、Receipt |
| `kokoro-system` | Site、Host、Workspace、Runtime Manifest、System Policy、配置发布 |
| `kokoro-model` | Model Catalog、Provider Metadata、Availability、Routing Policy、Resolve |
| `kokoro-billing` | Payment、Subscription、Checkout、Refund、Credit、Ledger、Metering、Reconcile |
| `kokoro-capability` | Skill、MCP Control Plane、Installation、Authorization、Provider Metadata、Receipt |
| `kokoro-storage` | Blob、Upload、Asset、Artifact、Scan、对象生命周期元数据；对象字节在 ObjectStore |
| `kokoro-scheduler` | Schedule、Occurrence、Lease、Retry、Dispatch；不拥有 Billing/Agent 业务事实 |

跨仓只通过事实 owner 仓库发布的 contract、API/RPC 和受信 service context；不共享数据库、ORM schema、SQL 文件、业务 DTO 或相对路径 import。

Scheduler 的目标 Go 目录：

```text
cmd/scheduler/
internal/domain/
internal/application/
internal/ports/
internal/adapters/
internal/transport/
```

## 9. 测试、可靠性和安全门禁

测试目录：

```text
test/{unit,integration,contract,architecture,smoke,fixtures,doubles}/
```

- `unit` 测试纯 Domain/Application；`integration` 必须使用真实 PostgreSQL、Redis、ObjectStore 或 provider；Fixture 不得冒充 integration。
- `architecture` 检查目录、import、owner、tenant predicate、参数化 SQL、无外键、无旧路径和生产替身。
- `contract` 检查 API/RPC 与本仓 owner schema；`smoke` 检查真实启动、health、ready 和最小请求。
- 外部 client 必须有 connect/read/overall timeout；重试仅用于可重试瞬时错误，并使用指数退避和 jitter。
- 支持请求取消、graceful shutdown、worker drain、lease 恢复、重复投递和故障注入。
- 结构化日志至少包含 service、operation、request_id、trace_id、结果和耗时；禁止记录 token、密码和敏感载荷。
- 配置、依赖、源码、镜像和 secret 通过阻断式扫描；发布物提供 SBOM、max provenance 和不可变 digest 签名。
- GitHub Actions 第三方 action 固定到完整 commit SHA，并在注释中保留可读版本；禁止仅引用可移动 major tag。
- 生产容器使用非 root 用户并声明 HEALTHCHECK；release 在推送前构建、扫描并启动候选镜像验证 health/ready。
- 每个服务维护 `docs/SLO.md` 和故障 runbook，定义关键 SLI/SLO、告警阈值、错误预算与处置链接；目标不能冒充实测结果。

## 10. Agent 执行协议

1. 开始前读取本文件、`docs/CURRENT.md`、`docs/CODEBASE_MAP.md`、目标仓 README、API contract 和相关状态文档。
2. 先检查 Git 状态、分支、工作区和协作者未提交变更；不覆盖、回滚或重写其他 Agent 的工作。
3. 多仓独立任务可以并行；一个仓库同一时间只允许一个写入 Agent。所有 worker 必须读取 `docs/CODEBASE_MAP.md`。
4. 开始修改前列出：owner、目标目录、依赖方向、删除项、Schema/API 变化、行为保持项和验证命令。
5. 先改目标仓库自己的 contract/模型/port，再改 application，再改 infrastructure/interfaces，最后更新启动装配、测试和文档；Root 不新增跨仓 contract。
6. 代码、Schema、contract、测试、CI 和文档必须一起收敛；只移动文件或只改命名不算完成。
7. 不新增万能 Service、万能 Repository、无 owner 的 common/utils、兼容 alias 或“临时”双轨实现。
8. Agent 报告不等于完成；主工作区必须重新执行真实 lint、typecheck、test、build、schema 和 smoke 验证。
9. 完成报告必须列出修改文件、命令、结果、失败项、已知风险和后续 owner；未通过项明确标记为未完成。

## 11. 默认验证命令

Root 在七仓验证阶段另外执行：

```bash
python3 scripts/verify-seven-repository-standard.py
./scripts/verify-seven-repository-full.sh  # 本地 Docker PostgreSQL/Redis/MinIO 可用时的最终全量门禁
```

该命令只检查跨仓结构性不变量；它不能替代各子仓的真实 lint、typecheck、test、build、Schema 和
smoke 验证。

TypeScript 子仓：

```bash
pnpm lint
pnpm typecheck
pnpm test
pnpm build
pnpm db:apply-schema
```

Go Scheduler：

```bash
gofmt -w .
go vet ./...
go test ./...
go build ./...
```

`lint` 必须是真实静态检查，不得只是 `typecheck` 别名；Schema、contract、architecture 和真实基础设施验证不能由空测试或内存替身代替。
