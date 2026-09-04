@CLAUDE.md

# Kokoro Agent 工程规范手册

本文件是 Kokoro Root 与十个正式运行仓的长期中文工程控制手册。前半部分是可复用于 TypeScript、Python、
Go 后端与 Web 的通用工程基线；标明“Kokoro”的条款是本项目明确取舍。它不是建议清单，而是 Agent 执行
代码、Schema、API、测试、交互和文档任务时的默认工作契约。规则已经明确时直接执行，不重复询问已经决定的
目录、时间、SQL、外键、迁移、兼容层、协议和本地基础设施规则。

## 0. 适用范围与权威顺序

适用仓库：`kokoro`、`kokoro-bff`、`kokoro-agent`、`kokoro-iam`、`kokoro-system`、
`kokoro-model`、`kokoro-billing`、`kokoro-capability`、`kokoro-storage`、`kokoro-scheduler`。
Root 只拥有架构文档、开发者门户编排、部署编排、质量门禁和仓库拓扑，不拥有跨仓 API contract，也不拥有
十仓的业务表、Entity、Repository 或业务 Service。每个 active repository 自己维护本仓 contract、Schema、
generated code、测试和 CI。

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
9. 公开契约和持久化不变量优先于目录美观；目录调整必须伴随真实依赖倒置、行为测试和旧路径删除。
10. “完成”“生产级”“满分”必须绑定当前 commit、执行命令和 evidence；历史报告与 Agent 自报不作证据。

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

`models/`、`enums/`、`errors/`、`repositories/`、`services/`、`commands/`、`queries/`、`mappers/`、
`ports/`、`clients/` 使用复数，因为目录容纳同类职责集合；`dto/`、`api/`、`http/`、`rpc/`、`sql/` 是
约定缩写或协议名，保持单数写法。不要为了“统一加 s”制造 `dtos/`、`https/` 一类非惯用目录。

禁止：

- 同时保留 `src/modules`、`src/adapters` 与新的四层作为重复实现层；
- `common/`、`utils/`、`types/` 成为无 owner 的业务垃圾桶；
- HTTP handler 直接执行 SQL；
- Infrastructure 类型泄漏到 Domain/Application；
- ORM Entity 同时充当 Request DTO、Domain Model 和 Response。

Web 可以按 feature 组织组件、hooks、state 和 view model，但服务端数据读取、鉴权、同源 adapter 与浏览器组件
必须分开；BFF 仍按 Domain/Application/Infrastructure/Interfaces 依赖方向组织，不能因为叫 BFF 就把所有逻辑
堆进 route handler。

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

八个正式 TypeScript 子仓统一使用 `pnpm@11.25.0` 与单一 `pnpm-lock.yaml`；不并存 npm/yarn lockfile，CI、
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
  "noUnusedParameters": true,
  "useUnknownInCatchVariables": true
}
```

```text
外部 JSON/未知值 -> unknown -> Zod/TypeBox/Valibot 校验 -> 具体 DTO
数据库 Row       -> 独立 Row 类型 -> mapper -> Domain/Application 类型
any              -> 仅限局部第三方边界，并写出原因
```

禁止使用 `as T`、双重断言、非空断言 `!`、宽泛 `any` 掩盖校验、空值和类型设计问题。允许的例外仅限
`as const`、经过运行时校验后的局部第三方 interop，以及 TypeScript 暂时无法表达但已有测试覆盖的不变量；
例外必须收敛在边界函数并写明原因。DTO、Command、Domain Model、DB Row、Generated Wire Type、Response
各自定义；不要因为减少 mapper 就合并类型。

### Python

```text
TypedDict  = 静态 dict shape，不负责运行时校验
Pydantic   = 外部输入、配置和第三方 payload 的运行时校验
dataclass  = 内部数据对象和值对象
class      = 需要行为、不变量和状态迁移的 Entity/Aggregate
Protocol   = Repository、Clock、Client 等窄 Port
Enum       = 有限状态和可审查协议值，不使用散落字符串
```

新代码使用完整标注，目标为 Pyright strict 或 `mypy --strict`。边界模型默认 strict、extra forbid；
`Any`、`cast`、`type: ignore` 只能局部使用并注明原因；禁止 file-wide Pyright/Mypy suppression。
数据库 row 使用独立 `TypedDict` 或 typed record 后再由 mapper 转换，不把裸 `dict[str, Any]` 贯穿业务层。
领域时间使用带时区 `datetime`，测试注入 Clock。

### Go

`go vet`、`go test`、必要时 `-race` 为基础门禁。公共函数显式返回 error；外部请求携带可取消的
`context.Context`；领域时间使用 `time.Time`，进入领域层统一 `.UTC()`。Go 只使用官方仍支持的版本并在
`go.mod` 固定补丁版本；当前 Scheduler 基线为 `go 1.26.8`，构建镜像同时固定 tag 与 digest。

### 代码粒度与复杂度预算

预算用于尽早触发拆分，不鼓励为了行数切出无语义碎片：

| 对象 | 评审线 | 默认阻断线 |
| --- | ---: | ---: |
| 普通源码文件 | 400 行 | 800 行 |
| React component/module | 300 行 | 500 行 |
| CSS module | 300 行 | 500 行 |
| 函数/方法 | 60 行 | 100 行 |
| 圈复杂度 | 10 | 15 |
| 嵌套深度 | 4 层 | 5 层 |

- 超过评审线必须说明继续聚合的业务理由；超过阻断线必须拆分或在仓库 architecture test 中登记 owner、理由、
  到期时间和替代方案。
- Generated、固定协议枚举、i18n message catalog 和纯静态数据表可以豁免，但必须可重生成且禁止混入手写业务逻辑。
- 拆分按 use case、aggregate、state machine、adapter、mapper、view state 或 CSS responsibility 进行；禁止只按行号切文件。

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
12. 每个 HTTP client 必须设置 connect/read/overall timeout、取消传播、响应大小上限和稳定错误归一；重试前先判断
    方法与 command 是否具备幂等身份。

### 5.1 API 可见性与事实源

每条协议只属于以下一种可见性：

| 可见性 | Owner 与用途 | 发布规则 |
| --- | --- | --- |
| `public` | `kokoro-bff` 对开发者开放的 Product API | 进入 Developer API 门户、版本与弃用策略 |
| `browser-private` | `kokoro` 同源 adapter | 仅 Web 使用，不承诺第三方兼容性 |
| `internal-owner` | IAM/System/Model/Billing/Capability/Storage/Agent/Scheduler | 固定版本 artifact，仅受信服务调用 |
| `event-protocol` | owner 发布的异步消息 | 显式 producer、consumer、ordering、delivery 与 replay 语义 |

OpenAPI operation 应声明 `x-kokoro-owner`、`x-kokoro-visibility`、`x-kokoro-stability`、
`x-kokoro-idempotency`、`x-kokoro-permission`。人类文档解释策略，OpenAPI/Proto/JSON Schema 才是字段级
机器事实源；运行时 validator、generated types 和示例必须由事实源校验。

### 5.2 Contract、Protocol 与 Generated 的边界

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

### 5.3 AG-UI 与 Vercel AI SDK

- Web 与 BFF 的 Agent 网络事件只使用 AG-UI；删除 legacy `SessionEvent`、第二套 SSE envelope、双读和 runtime fallback。
- BFF 将 Agent 执行事件投影成 durable public AG-UI ledger，拥有单调 cursor、replay、断线恢复、保留与 GC 语义；
  Redis stream 不是公开事件事实源。
- Web 在仓内实现窄 `AgUiChatTransport`，把 AG-UI 映射成 Vercel AI SDK `UIMessage`/parts；Vercel AI SDK 是
  React 状态与渲染适配层，不建立第二套网络协议或第二个 resumable stream 事实源。
- 标准事件优先使用 Run、Text、Tool、Reasoning、Activity、Subagent 和 Interrupt/Resume；`CUSTOM` 只表达确无
  标准事件的领域 artifact/delivery，不用来逃避标准语义。
- HITL 使用结构化 interrupt/resume；resume 必须携带同 thread、全部未决 interrupt、幂等 identity 和校验结果。
- 客户端必须显式建模 `idle`、`submitting`、`queued`、`streaming`、`awaiting_approval`、`resuming`、
  `cancelling`、`reconnecting`、`completed`、`failed`，并以 receipt/event reconciliation 收敛 optimistic state。

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
7. 本地十仓共享一个 PostgreSQL 实例和一个 Redis 实例；执行脚本先探测并复用已有实例，只有缺失时才各启动
   一个依赖，且只清理自己创建的资源。各持久化 owner 使用独立 PostgreSQL database/schema；固定 Redis
   logical DB 为 IAM=1、System=2、Model=3、Billing=4、Capability=5、Storage=6、Scheduler=7、BFF=8、
   Agent=9，DB 0 保留。Web 不拥有数据库或 Redis。应用开发进程只从源码以 `pnpm dev`、`uv run`、`go run`
   启动，应用容器只用于发布候选镜像 smoke。

### SQL 执行与 JOIN

- PostgreSQL 使用 `$1`、`$2` 等参数绑定；禁止拼接用户输入、动态列名、表名和排序字段。
- 动态排序使用白名单映射；查询使用明确列，不使用 `SELECT *`。
- 同一数据库、同一 owner、同一 bounded context 内允许显式 `JOIN ... ON`。
- tenant-owned JOIN 的连接条件和过滤条件都必须带 tenant 范围。
- 存在性判断优先 `EXISTS`；读取避免 N+1；公开列表使用稳定 keyset cursor。
- 跨仓库、跨数据库、跨 owner 禁止数据库 JOIN，使用 API/RPC、快照或异步投影。
- 关系写入按以下顺序执行：tenant existence -> owner/permission -> state -> fixed-order lock -> 同一事务写关系和事实 -> commit。
- Repository 负责 SQL、锁和 Row mapper；Application 负责用例、权限入口和业务语义。

## 8. 十仓 owner 与运行边界

| 子仓 | 只拥有的事实或职责 |
| --- | --- |
| `kokoro` | UI、浏览器交互状态、HttpOnly session cookie、同源 adapter；不拥有服务端业务事实 |
| `kokoro-bff` | Conversation、Message、Share、Project、ScheduledTask、公开 Product API、durable AG-UI projection |
| `kokoro-agent` | Run、Checkpoint、Lease、Tool Journal、执行事件、HITL、Evidence；不拥有 Conversation/Project/ScheduledTask |
| `kokoro-iam` | Tenant、Identity、Authentication、Authorization、Role、Permission、Audit、Receipt |
| `kokoro-system` | Site、Host、Workspace、Runtime Manifest、System Policy、配置发布 |
| `kokoro-model` | Model Catalog、Provider Metadata、Availability、Routing Policy、Resolve |
| `kokoro-billing` | Payment、Subscription、Checkout、Refund、Credit、Ledger、Metering、Reconcile |
| `kokoro-capability` | Skill、MCP Control Plane、Installation、Authorization、Provider Metadata、Receipt |
| `kokoro-storage` | Blob、Upload、Asset、Artifact、Scan、对象生命周期元数据；对象字节在 ObjectStore |
| `kokoro-scheduler` | Schedule、Occurrence、Receipt、Outbox、Lease、Retry、Dispatch；不拥有 Billing/Agent 业务事实 |

跨仓只通过事实 owner 仓库发布的 contract、API/RPC 和受信 service context；不共享数据库、ORM schema、SQL 文件、业务 DTO 或相对路径 import。

固定调用方向为：Browser -> Web same-origin adapter -> BFF -> owner API/Agent/Scheduler。Web 不直连 IAM 或
其他 owner；BFF 不读取 Agent 或其他 owner 数据库；Agent 通过 Capability/Storage 的真实 client 获取授权能力和
保存 artifact，不复制两仓模型。Scheduler 只负责通用 schedule/occurrence/lease/retry/dispatch。

Scheduler 的目标 Go 目录：

```text
cmd/scheduler/
internal/domain/
internal/application/
internal/ports/
internal/adapters/
internal/transport/
```

### Kokoro Scheduler 技术选型边界

以下是 Kokoro 项目取舍，不是所有 Go 调度系统的唯一标准：

- `kokoro-scheduler` 是本选型的 owner；`github.com/go-co-op/gocron/v2` 只作为可替换的 timer/wakeup
  adapter，必须隐藏在 `ScheduleEngine` 等窄 Port 后。候选对比结论是：`github.com/robfig/cron/v3` 的直接
  使用已不满足本项目维护活跃度与生命周期治理要求，gocron/v2 具有活跃的稳定 major 和适合 adapter 的
  生命周期/context 接口，因此选择后者。现有 robfig/cron 的直接依赖、源码 import 和并行 adapter 必须删除；
  当前基线仍传递依赖该模块，只能将其作为纳入 SBOM 与扫描的传递依赖，业务代码不得直接调用。
- 目标固定基线为 `github.com/go-co-op/gocron/v2 v2.22.0`：稳定版发布日期为 2026-07-09，选型验证日期为
  2026-09-04，模块最低 Go 版本为 1.22、许可证为 MIT，与本项目 Go 1.26.8 基线兼容。实现仓必须在
  `go.mod`/`go.sum` 固定并复验精确版本，不提交 `latest`；后续升级服从下节依赖治理门禁。
- PostgreSQL 是 Scheduler 自有 `Schedule`、`Occurrence`、`Receipt` 和 `Outbox` 的唯一权威事实源；进程启动
  或恢复必须从 PostgreSQL 重建待唤醒集合。Redis 只用于 lease、通知、缓存等协调与加速，丢失或清空 Redis
  不得造成权威事实丢失。Scheduler 仍不拥有 BFF 的 `ScheduledTask` 或目标服务的业务 receipt，也不读取其他
  owner 的数据库。
- gocron 的进程内 jobs 以及可选 locker/elector 只提供唤醒或并发提示，不能替代持久化、幂等唯一约束、
  misfire 扫描、recovery、transactional outbox 或投递 receipt。重启、重复唤醒、进程崩溃和 Redis 故障下的
  正确性必须由 Scheduler application、PostgreSQL 事务和可重放状态机证明。
- 替换/退出路径固定为保持 Port 与 contract 不变，使用相同的 UTC、misfire、重复触发、暂停/恢复和 graceful
  shutdown 行为测试替换 adapter；不得把 gocron 类型泄漏进 Domain、持久化模型或 HTTP/RPC contract。

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

### 9.1 依赖与技术选型治理

依赖必须活跃、主流、可维护，但不能盲目追 `latest`。以下是所有语言与正式仓库的通用标准；具体库的选定
属于对应项目或 bounded context 的明确取舍：

1. 依赖必须处于活跃维护状态、具有稳定主版本和可持续维护路径，并在目标生态有足够采用、文档和故障经验；
   “主流”不等于 star 数最多，“活跃”也不等于发布时间最新。不得仅凭 star、下载量、单次 benchmark 或发布日期
   决策，也不得为了追新盲目升级。
2. 选型至少核验：官方维护与弃用状态；最近 12–18 个月的 release、有效 commit、issue/安全响应；稳定 major
   与升级政策；目标 Go/Node/Python 和框架兼容性；许可证；直接与传递依赖树、来源和供应链风险；可替换边界；
   在本仓真实负载下的基准；timeout、重试、取消、崩溃恢复、数据一致性等故障语义。
3. 新依赖或重大替换进入实现前，必须在 PR、有效 ADR 或依赖登记中记录 owner、用途、候选对比与淘汰理由、
   选定精确版本、该版本发布日期、验证日期、兼容性/许可证结论，以及替换或退出策略。小版本安全升级至少记录
   影响范围、release notes、lockfile diff 和验证证据。
4. manifest 与 lockfile 固定精确版本并一起提交；容器和 GitHub Actions 另按 digest/SHA 固定。禁止在可重复构建
   路径中使用 `latest`、浮动分支、未固定 URL 或自动漂移版本。文档中的“最新”只表示**截至所写验证日期的最新
   稳定兼容版本**；beta、RC、nightly 或未发布 commit 不得冒充稳定版，确需预发布版本时必须单独 ADR、到期日
   和回退方案。
5. Renovate/Dependabot 只负责提出可审查 PR，不直接改变技术基线或绕过 review。升级必须检查直接/传递依赖变化，
   并通过本仓真实 lint、typecheck/vet、test、build、contract、Schema、integration、smoke 和供应链扫描中所有
   相关门禁后才能合并。
6. 核心依赖若连续 12–18 个月没有有效 release/commit，出现未处理的安全或运行时兼容问题、正式弃用、维护权
   不明或关键故障语义不再满足要求，必须触发 ADR/replacement review。成熟稳定而低频发布不自动判死刑，但必须
   用维护声明、安全响应和兼容性证据决定继续固定、接管、隔离或替换，不能因升级成本而默认永久保留。

Web 额外门禁：

- 样式使用语义 design token；组件 CSS 不散落品牌色/状态色硬编码，`!important` 只允许登记的第三方覆盖；
- 去掉 `outline` 必须提供等价且清晰的 `:focus-visible`；动画遵守 `prefers-reduced-motion`；
- 所有交互覆盖 loading、empty、error、disabled、optimistic、reconnecting、partial 和 success 状态；
- Playwright 覆盖桌面/移动关键路径，axe 阻断严重可访问性问题，视觉回归保护核心页面，并设置 bundle budget；
- 同源 adapter 具备 CSRF、防缓存泄漏、CSP/安全响应头、超时、取消、body/response size limit，禁止匿名注入可信身份。

## 10. 文档与 Developer API 门禁

每个正式仓库至少维护：

```text
README.md                    # 五分钟启动、验证、owner 概览
INDEX.md                     # 仓库代码与边界地图
docs/INDEX.md                # 文档阅读顺序
docs/CURRENT.md              # 当前实现、缺口与证据，不写愿景冒充事实
docs/TECHNICAL_DESIGN.md     # 当前架构、依赖、状态机、事务、失败恢复
docs/API_CONTRACT.md         # 人类可读协议策略，链接机器事实源
docs/DATA_MODEL.md           # 表 owner、不变量、关系维护、索引与 retention
docs/SECURITY.md             # trust boundary、authn/authz、tenant、secret、abuse controls
docs/RELIABILITY.md          # timeout、retry、idempotency、outbox、recovery、degradation
docs/ACCEPTANCE.md           # 可执行验收矩阵
docs/SLO.md                  # SLI/SLO、错误预算和告警
docs/RUNBOOK.md              # 诊断、处置、回滚和恢复
docs/ADR/                    # 仍有效的架构决策
contract/README.md           # 有机器 contract 时：owner/version/generation/breaking/provenance
```

- `README.md` 不是完整设计，`INDEX.md` 不是进度报告，`CURRENT.md` 不是历史日志，`API_CONTRACT.md` 不复制
  OpenAPI 字段，`contract/README.md` 不定义业务模型。
- Root 的 Developer API 门户只发布 BFF `public` contract 与开发者指南。它通过 catalog 固定 owner artifact 的
  version、commit 和 digest 后生成 reference，不复制一份可手改的跨仓 contract。
- 文档 CI 执行 Markdown/style/link/build、OpenAPI lint/breaking、generated drift、示例编译/运行和 visibility
  检查；公开文档禁止泄漏 internal endpoint、service credential、数据库结构和未脱敏 payload。

## 11. Agent 执行协议

1. 开始前读取本文件、`docs/CURRENT.md`、`docs/CODEBASE_MAP.md`、目标仓 README、API contract 和相关状态文档。
2. 先检查 Git 状态、分支、工作区和协作者未提交变更；不覆盖、回滚或重写其他 Agent 的工作。
3. 多仓独立任务可以并行；一个仓库同一时间只允许一个写入 Agent。所有 worker 必须读取 `docs/CODEBASE_MAP.md`。
4. 开始修改前列出：owner、目标目录、依赖方向、删除项、Schema/API 变化、行为保持项和验证命令。
5. 先改目标仓库自己的 contract/模型/port，再改 application，再改 infrastructure/interfaces，最后更新启动装配、测试和文档；Root 不新增跨仓 contract。
6. 代码、Schema、contract、测试、CI 和文档必须一起收敛；只移动文件或只改命名不算完成。
7. 不新增万能 Service、万能 Repository、无 owner 的 common/utils、兼容 alias 或“临时”双轨实现。
8. Agent 报告不等于完成；主工作区必须重新执行真实 lint、typecheck、test、build、schema 和 smoke 验证。
9. 完成报告必须列出修改文件、命令、结果、失败项、已知风险和后续 owner；未通过项明确标记为未完成。
10. 两个以上独立仓库默认并行，但每仓同一时刻只有一个写入 Agent；跨仓 contract 先由 owner 提交，再更新消费者。
11. 架构重构使用 `codex/` 分支和小粒度 commit；不把移动目录、功能修改、格式化和生成物更新混成不可审查提交。
12. 不在已有 PostgreSQL/Redis 时重复启动容器；不以 Docker 应用容器替代源码 lint/test/dev 验证。

### 11.1 多 Agent 主控与派工协议

本节是所有后续重构任务的默认控制面。用户已经确认的目标、目录、时间、SQL、协议和本地依赖规则视为已
锁定；收到“继续”“恢复”或等价指令时，直接从当前 goal、工作树和缺口队列继续，不重新询问已经确定的
事项。

1. 主 Agent 先把任务拆成互不重叠的 surface（仓库、bounded context、contract、UI/CSS、验证或文档），
   再决定自己立即处理的关键路径；两个及以上独立 surface 默认并行派工。
2. 一个仓库同一时刻只能有一个写入 Agent。只读审查 Agent 可以并行，但不得在审查期间暗中改文件；要写入
   时必须先声明新的窄切片并确认没有重叠。
3. 每个 worker 启动消息必须是中文，并明确：owner、绝对工作目录、允许写入的文件集合、明确排除的路径、
   依赖方向、删除项、契约/Schema 影响、验证命令、commit 要求和报告格式。必须注入
   `docs/CODEBASE_MAP.md`；缺失时先生成地图再派工。
4. worker 可以继续拆分子任务，但只在主 Agent 明确允许时进行；子任务必须登记名称、owner、写入集合和依赖，
   不能产生未命名或重复写入的隐形 worker。跨仓 contract 先由事实 owner 完成，消费者 worker 等 owner commit
   后再启动。
5. worker 只提交自己的窄切片，不替其他 Agent 暂存、回滚、格式化或清理文件。生成物、缓存、coverage、`.next`
   和本地临时数据库不得进入 commit。完成消息统一使用：

   ```text
   状态：已提交 / 部分完成 / 被阻塞
   commit：<sha 或未提交原因>
   修改文件：<绝对路径列表>
   验证：<命令 -> 实际结果>
   未完成与风险：<明确列出，不用“应该可以”>
   后续 owner：<仓库/Agent/主控>
   ```

6. worker 的退出码、口头“完成”、历史报告或设计评分都不是证据。主 Agent 收到 commit 后先审查 diff 和 owner
   边界，再在主工作树重新运行对应 lint、typecheck、test、build、contract、Schema、integration 和 smoke；
   只有这些输出与当前 commit 绑定后，才能移动缺口队列。
7. 并行切片之间共享 PostgreSQL/Redis 时只由主控编排生命周期：先探测并复用已有实例，按固定 database/logical
   DB 隔离；不得让多个 worker 各自启动同名容器、清空非自己创建的资源或把 Docker 应用容器当作源码验证。
8. 主 Agent 每一波结束时维护简短的派工表（worker、仓库、写入集合、commit、验证、剩余风险），再决定下一波；
   未完成的失败项保留在队列中，不通过放宽门禁、增加 alias、双读写或空测试来“清零”。

## 12. 默认验证命令

Root 在十仓验证阶段另外执行：

```bash
python3 scripts/verify-ten-repository-standard.py
./scripts/verify-ten-repository-full.sh
```

该命令只检查跨仓结构性不变量；它不能替代各子仓的真实 lint、typecheck、test、build、Schema 和
smoke 验证。

TypeScript 服务仓：

```bash
pnpm lint
pnpm typecheck
pnpm test
pnpm build
pnpm db:apply-schema
```

Web 不机械执行 `db:apply-schema`，必须执行：

```bash
pnpm lint
pnpm typecheck
pnpm test
pnpm build
pnpm test:e2e
```

Python Agent：

```bash
uv sync --frozen
uv run pyright
uv run pytest
```

Go Scheduler：

```bash
gofmt -w .
go vet ./...
go test ./...
go build ./...
```

`lint` 必须是真实静态检查，不得只是 `typecheck` 别名；Schema、contract、architecture 和真实基础设施验证不能由空测试或内存替身代替。
