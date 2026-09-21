# Kokoro 总体架构规范 v1

状态：正式目标，2026-09-21。

本文只定义系统级边界。语言目录、代码风格与 SQL 细节由以下唯一专项手册负责：

- [PostgreSQL 与 SQL 工程规范](kokoro-handbook/standards/03-sql-and-postgresql.md)
- [TypeScript 后端成熟工程规范](kokoro-handbook/standards/08-typescript-backend-engineering.md)
- [Python 后端成熟工程规范](kokoro-handbook/standards/09-python-backend-engineering.md)

## 1. 架构原则

Kokoro 采用“少量独立服务 + 服务内业务模块”的结构。Bounded context 是代码和数据边界，不等于每个名词都要
创建一个仓库或微服务。拆服务必须由独立 owner、SLO、扩缩容、故障域、安全域或发布节奏证明，不能靠目录美观。

```text
Browser -> Web -> BFF -> internal owner services / Agent / Scheduler
```

- 一个业务事实只有一个 owner 和一个 writer。
- 跨仓只通过版本化 API/RPC/Event；不共享数据库、ORM schema、SQL、业务 DTO 或源码 import。
- 服务内按业务模块聚合；具体物理目录遵循语言手册。
- HTTP/RPC/worker 只处理协议，业务 Service/use case 负责授权、事务和编排，Repository/client 负责 I/O。
- 简单模块不制造 DDD 空层，复杂状态机才建立显式 Domain Model。

## 2. 目标运行仓与 owner

| 仓库               | Owner                                                                              |
| ------------------ | ---------------------------------------------------------------------------------- |
| `kokoro`           | Web UI、浏览器状态、同源 adapter                                                   |
| `kokoro-bff`       | Conversation、Message、Project、Share、ScheduledTask、Public API、AG-UI projection |
| `kokoro-agent`     | Run、Checkpoint、Lease、Tool Journal、执行、Approval/HITL、Evidence                |
| `kokoro-iam`       | Tenant、Identity、AuthN/AuthZ、Role、Permission、Audit                             |
| `kokoro-system`    | 系统控制面：Site、Host、Workspace、Runtime、Policy、模型目录与路由配置             |
| `kokoro-billing`   | Payment、Subscription、Checkout、Refund、Credit、Ledger、Metering、Reconciliation  |
| `kokoro-platform`  | Agent Capability Control Plane：Skills 与 MCP；后续平台模块须单独 ADR              |
| `kokoro-storage`   | Blob、Upload、Asset、Artifact、Scan、ObjectStore metadata                          |
| `kokoro-scheduler` | Schedule、Occurrence、Lease、Retry、Outbox、Dispatch                               |

### 2.1 已裁决的收敛

```text
kokoro-model       -> kokoro-system 内的 model-catalog 业务模块
kokoro-capability  -> kokoro-platform
kokoro-platform    -> skills 与 mcp 两个一级业务域
```

`kokoro-model` 合并是部署和仓库合并，不是把模型目录/路由策略混入通用 config。`model-catalog` 保持自己的业务词汇、
`model_*` 表、contract namespace、权限和测试，以便未来在独立团队/SLO/容量证据出现时重新拆出。

`kokoro-platform` 是明确的 Agent Capability Control Plane，不是共享代码垃圾桶。新增中间平台能力必须有事实 owner、
契约、生命周期、权限、观测和 ADR，并证明不属于 System/IAM/Billing/Storage/Scheduler/Agent 的既有边界。
历史归档的 platform 代码不直接恢复；目标仓由当前 Capability 以 clean-slate 方式收敛。

当前物理身份仍是 `kokoro-capability`。只有 remote、path、package、service、env、Proto、数据库、Redis 和 consumer
在 Wave 3 同一窗口完成切换并通过 owner 完整门禁与跨仓 integration/smoke 后，才改称 `kokoro-platform`；切换前的
Root 路径、运行身份和当前状态不得提前使用目标名称，也不保留兼容 alias。

### 2.2 目标模块地图

```text
kokoro-system/src/modules/
  sites/
  workspaces/
  runtimes/
  policies/
  model-catalog/
    catalog/
    providers/
    revisions/
    routing/
    availability/

kokoro-platform/src/modules/
  skills/
    catalog/
    revisions/
    packages/
    installations/
  mcp/
    providers/
    connectors/
    servers/
    connections/
    authorizations/
```

上图是候选业务能力地图，具体子目录须经各仓技术方案确认，不机械全建。这些能力不要求建立 `postgres/`、`redis/`、`domain/application/infrastructure` 模板。具体文件按对应语言
手册和模块实际复杂度设计。

`kokoro-system` 不建设任意 key/value 配置垃圾桶。新配置默认放回其事实 owner：Site 配置在 `sites`，模型路由在
`model-catalog`，运行参数在 `runtimes`。只有具备独立身份、生命周期、权限、契约和查询模型时才增加一级模块，
不是每出现一种配置都新增一个 `<name>-config` 目录。

## 3. 数据边界

- 本地与 CI 复用一个 PostgreSQL 实例和一套应用 role/credential；每个数据 owner 仍使用独立 database/schema 与独立连接 URL。代码、Schema、查询、事务和测试继续禁止跨 owner SQL/JOIN、表引用、ORM model 与 canonical schema 共享。每 owner 独立 production role、GRANT/REVOKE、数据库 mTLS 和 NetworkPolicy 属于部署阶段，不是当前闭环门禁。
- 每个数据 owner 维护一份唯一 canonical schema；SQL-first 使用 `database/schema.sql`，ORM-first 使用技术方案批准的唯一 ORM schema。
- Kokoro V1 clean-slate 不保留 migration 链、外键或兼容 schema；完整规则只见 SQL 手册。
- 同一 owner/数据库/业务边界允许 JOIN；跨 owner 禁止 JOIN。
- PostgreSQL 是 durable truth；Redis 只用于缓存、lease、通知和 stream。
- 所有 tenant-owned 查询和写入显式携带 tenant predicate。
- 跨服务引用使用 opaque ID；关系存在性、权限、状态、删除和 reconciliation 由 owner API 与应用事务维护。

Model 合入 System 后使用同一 System 数据库，但 `system_*` 和 `model_*` 表仍分别属于各自模块；模块间只通过公开
Service API，不允许任意交叉查询。旧 Model 数据库与 Redis DB 3 在 cutover 后删除，不做长期双写。

Platform 从 Capability cutover 时继承该数据 owner，并重新固定服务名、数据库、Redis namespace、service identity、
contract owner 和消费者配置；旧 Capability 名称不保留兼容 alias。

## 4. API 与协议

| Caller → Owner               | 唯一目标协议                  | 契约 owner | 说明                                             |
| ---------------------------- | ----------------------------- | ---------- | ------------------------------------------------ |
| Browser → Web                | same-origin HTTP              | Web        | Cookie、CSRF、浏览器状态。                       |
| Web → BFF                    | HTTP/OpenAPI；AG-UI/SSE       | BFF        | Public Product API 与 durable event projection。 |
| BFF → IAM                    | HTTP/OpenAPI generated client | IAM        | OAuth/OIDC/Better Auth 保持原生 HTTP 语义。      |
| BFF/Agent → System           | HTTP/OpenAPI generated client | System     | 不因统一偏好重写当前稳定 HTTP。                  |
| BFF/Agent → Platform         | ConnectRPC/Proto              | Platform   | Skills/MCP typed command/query。                 |
| BFF/Agent/Platform → Storage | ConnectRPC/Proto v2           | Storage    | Asset、Artifact、Upload、Package reference。     |
| BFF → Agent                  | HTTP/OpenAPI generated client | Agent      | Run dispatch/control 与可恢复 event paging。     |
| BFF → Scheduler              | HTTP/OpenAPI generated client | Scheduler  | Schedule command/query。                         |
| Scheduler → BFF/Agent        | HTTP event protocol           | Scheduler  | Durable retry、receipt、duplicate delivery。     |
| BFF → Billing                | HTTP/OpenAPI generated client | Billing    | Checkout、payment resource 与 provider webhook。 |

- BFF 是唯一 public Product API owner；Web 使用 browser-private 同源 adapter。
- 内部服务 contract 由各 owner 仓维护；Root 只做 catalog 和治理。
- API 技术设计确定唯一 schema-first/code-first 方向；OpenAPI/Proto/JSON Schema artifact 与 runtime validator 不双向手改。
- 所有 API 明确 owner、visibility、version、permission、idempotency、错误码和分页语义。
- AG-UI 是 Web/BFF 的唯一 Agent 网络事件协议；Vercel AI SDK 只作 Web 内 UI adapter。
- 跨仓变更顺序：owner contract -> lint/breaking/generate -> 实现 -> 消费者 -> integration/smoke。

## 5. 运行与故障边界

- BFF 不读取内部 owner 数据库；Agent 不复制 Platform/Storage 业务事实。
- System 内 `model-catalog` 的 provider availability 故障不得使 Site/Workspace 的基础读取不可用；模块应有独立 timeout、
  cache namespace、权限和 readiness 细分。
- Platform 的 Skills 与 MCP 可以使用同一仓和镜像，但可配置独立 runtime profile、workload identity、readiness 和扩缩容。
- Scheduler 重启后从 PostgreSQL 恢复权威 schedule/occurrence；Redis 丢失不能丢任务事实。
- 外部调用设置 timeout、取消、幂等和稳定错误归一；事务内不执行不可控网络请求。

## 6. Clean-slate cutover 原则

Model/System 与 Capability/Platform 的拓扑变更分别作为独立目标执行：

1. 先冻结 owner、目标 contract、schema 与消费者清单；
2. 在目标仓建立模块和 architecture tests；
3. 搬移业务事实与测试，统一唯一数据库访问技术；
4. 更新 BFF/Agent/Storage/Scheduler 的 typed client 与配置；
5. 使用 fresh PostgreSQL/Redis 验证，不迁移历史开发数据；
6. 删除旧仓 runtime、旧 service identity、旧 env、旧 contract 副本和旧部署；
7. 执行全量 contract/integration/smoke 后再更新仓库拓扑权威文档。

禁止 proxy compatibility service、双读双写、旧 header/env alias 或两个 owner 同时运行。

## 7. 架构完成证据

每个仓必须维护 README、INDEX、CURRENT、TECHNICAL_DESIGN、API_CONTRACT、DATA_MODEL、SECURITY、RELIABILITY、
ACCEPTANCE、SLO、RUNBOOK 与有效 ADR。完成报告至少包含：

```text
当前 commit
owner 与目标模块
删除的旧边界
contract/schema 变化
lint/typecheck/test/build 结果
fresh schema 与真实集成结果
health/ready/smoke 结果
未完成风险与后续 owner
```

目录看起来整齐、Agent 自评分或历史报告都不构成架构完成证据。
