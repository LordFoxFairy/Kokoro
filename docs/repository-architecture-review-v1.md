# Kokoro 子仓库架构与工程规范审计 v1

状态：2026-09-02 · Root 审计与第一轮代码收敛后的当前基线

本文是当前实现的审计结论，不替代各子仓库自己的 README、API contract、runbook 和测试。
目标是回答三个问题：每个仓库是否只有一个清晰职责、依赖方向是否正确、工程门禁是否足以支撑
独立发布。历史 handbook、旧 MySQL/Mongo 方案和已归档仓库不属于当前运行架构。

## 1. 当前拓扑

```text
Browser
  -> kokoro-app Web same-origin /api/*
  -> kokoro-bff Chat + business BFF
  -> IAM / System / Model / Billing / Capability / Storage
  -> kokoro-agent HTTP ingress -> Agent worker
  -> kokoro-scheduler internal dispatch / replay
```

边界原则：Web 不直连业务仓；BFF 不读任何 sibling 数据库；每个 owner 自己拥有 schema、迁移、
API、测试、Dockerfile 和 CI；Root 只拥有跨仓 contract、部署编排、拓扑审计和跨仓验收。

## 2. 逐仓库架构判断

| 仓库 | 当前职责 | 分层/入口 | 审计结论 |
|---|---|---|---|
| `kokoro-app` | Web UI、同源 `/api/*` adapter | `src/app`、`src/lib`、`packages/*` | 边界正确；`packages/*` 是 Web 仓内复用包，不是后端共享仓，不应承载业务事实。 |
| `kokoro-bff` | Chat、项目/任务业务、鉴权、幂等、owner adapter、SSE | `src/main.ts`、`src/http/routes`、`src/application`、`src/modules`、`src/adapters`、`src/infrastructure` | 业务入口正确；Project/ScheduledTask 已通过 application service 注入 repository port，PostgreSQL adapter 与 mock fixture 分离；`src/main.ts` 已收敛为组合根和通用请求管线，资源路由位于 `src/http/routes/*`。 |
| `kokoro-agent` | Run 执行、HITL、恢复、事件投影、HTTP ingress、worker | `src/kokoro_agent/worker`、`execution`、`repositories`、`infrastructure`、`contract` | 能力完整但复杂度最高；repository 只负责 Agent 运行事实，infrastructure 只负责 PG/框架适配；必须坚持 Feature/Agent/Runtime/Worker 分层，禁止将编排规则重新塞回 BFF。 |
| `kokoro-iam` | Tenant、User、Auth、AuthZ、Role、Permission、Audit、ExecutionIdentity | `src/main.ts`、`tenant-binding.ts`、Root/本仓 Proto | 单一职责清晰；IAM 只输出身份与授权事实，不拥有 Site manifest、Model provider 或 Billing 状态。 |
| `kokoro-system` | Site、Site Host、Workspace、Runtime Manifest、系统策略 | `src/modules/runtime-manifest`、`interfaces/http` | 边界正确；Site/Host binding 由 System 自己拥有，tenant_id 是唯一跨仓隔离键，不调用 IAM Host 接口。 |
| `kokoro-model` | Model Catalog、Provider、Availability、Policy、resolve | `src/domain`、`application`、`interfaces/http|rpc` | 目录与解析清晰；LiteLLM 只是可选 transport，Model 不探活、不启动、不拥有 LiteLLM。 |
| `kokoro-billing` | Payment、Subscription、Checkout、Refund、Credit、Ledger、Metering | `src/modules/*`、`src/domain`、PostgreSQL/Redis | 合并 Credit 合理；账务必须保持单写入事实和状态机，旧兼容表只能只读或退出。 |
| `kokoro-capability` | Skill、MCP Connector 控制面、安装、授权、receipt | `src/application`、`src/modules`、`src/adapters` | 领域边界合理；Capability 不拥有 Agent 执行态，不复制 Storage 字节，不绕过 IAM。 |
| `kokoro-storage` | Upload、Asset、Artifact、scan、ObjectStore 引用 | `src/application`、`src/modules`、`src/adapters` | 以 PostgreSQL 保存元数据、S3-compatible store 保存字节的设计正确；扫描失败应保持 fail-closed。 |
| `kokoro-scheduler` | 通用 ScheduleJob、trigger、lease、retry、misfire、dispatch | `cmd/scheduler`、`internal` | 独立 Go 仓合理；不读业务库、不理解 Billing/Project 规则。`SCHEDULER_JOBS_JSON` 只能作为本地/阶段性配置，不能替代生产注册事实。 |

## 3. 已确认的工程规范

### 仓库和依赖

- Root + 10 个独立子仓各自是独立 Git root。
- 当前本地和 GitHub 远端每个仓库只保留 `main` 分支。
- 子仓之间不通过 sibling 源码、数据库表、ORM schema 或相对路径导入耦合。
- Root 的 gitlink 只固定 Agent 的 `main` commit；其余仓库由部署/契约引用，不被 vendored。
- 每个 active 仓库拥有自己的 Dockerfile、CI、release workflow、文档和质量检查。

### API 和数据

- 外部 HTTP 使用 `snake_case`。
- v1 成功响应统一为 `{data, meta}`，错误统一为 `{error, meta}`。
- `request_id`、tenant context、service authentication 和 `Idempotency-Key` 在跨仓边界必须显式传递。
- PostgreSQL 保存业务事实；Redis 只做 cache、stream、queue、lease、限流和幂等快速路径。
- Storage 的对象字节不进入 Web、BFF 或业务表。
- 浏览器自定义域名字段不是安全边界；BFF 根据服务端配置生成受信请求上下文。

### 质量和发布

- 普通 push/PR 只运行质量门禁。
- `vMAJOR.MINOR.PATCH` tag 才构建并发布 GHCR 生产镜像。
- Docker 使用生产启动入口，本地开发使用各仓库 dev/test 命令。
- TypeScript 使用严格类型、运行时 schema 校验和独立构建；Python 使用 Ruff、Pyright、pytest；Go 使用 `go test` 与 race 检查。
- 生成代码包含 provenance；修改 Root contract 后由各仓库重新生成并在自身仓库验证。

## 4. 当前不合理或需要继续收敛的地方

### P0：BFF 的真实 upstream 仍需逐项替换 fixture

当前接口与 owner health 已闭环，但生产还需要完整 typed client、超时/重试、凭据、错误映射和
真实 provider 配置。BFF 不应通过一个“万能 adapter”吞掉 owner 差异，也不应把 mock 成功伪装成
生产成功。

### P0：ScheduledTask 与 ScheduleJob 需要持久化注册协议

BFF 拥有用户任务事实，Scheduler 拥有执行事实。需要补齐注册、更新、暂停、删除、重启恢复、
注册失败补偿和 reconciliation；线上不能把 `SCHEDULER_JOBS_JSON` 当作唯一任务来源。

### P1：Root machine-readable contract 仍需覆盖所有跨仓 HTTP

IAM/Model/Capability/Storage 的 Proto 与 Root contract 较完整；System、Billing、Scheduler 的
跨仓 HTTP/command 仍有一部分依赖各仓 Markdown。最终应把请求、响应、错误、鉴权和幂等字段提升
到 Root 可校验格式。

### P1：HTTP envelope 和错误码需要单一版本冻结

System、Model 的本轮正式 HTTP surface 已统一到 `{data, meta}` / `{error, meta}`，Billing 的
`/v1/*` surface 也由 transport hook 统一输出 `meta.request_id`，其中字段使用 snake_case。
Billing 当前 `/v1/*` surface 已删除旧无版本 route alias，统一由 transport hook 输出 `meta.request_id`；BFF 仍需继续收敛其他 owner
projection。历史兼容字段必须设置退出时间，不能继续增加双 envelope、双分页字段或顶层兼容字段。BFF 只做一次 transport projection，owner
内部模型不泄露到外部 API。

### P1：Billing 旧数据模型需要明确退出策略

新模型成为唯一 writer；旧表如果保留，只能作为有期限的只读迁移/审计层，并记录删除条件。

### P1：BFF 与 Agent 的几个返回成功路径仍然不够诚实

- BFF Session list 已改为调用 Agent 的持久化 identity-scoped query，并透传 opaque cursor；后续
  仍需补齐 Agent session metadata 与执行事实的恢复/删除生命周期，不得在 BFF 恢复进程内索引。
- BFF 的 Project tasks 已归入 BFF 自有 `bff_project_task` 事实表；后续只需补齐创建/更新命令和统一
  cursor 分页，不得退回从 Agent 读取或用空数组伪装成功。
- Agent evidence 查询需要校验 Run 的 identity/scope，并将诊断原始事件与用户可见投影分开。
- Agent admission、dispatch claim 和 steer command 需要可恢复的 durable inbox/outbox，避免
  “先 claim/ACK，后持久化”造成崩溃丢失。
- BFF mutation 现在会在副作用前登记 pending receipt；相同 key 的并发请求返回
  `409 idempotency_in_progress`，成功后按原状态/响应重放，5xx 会释放 claim。PostgreSQL
  pending claim 具备 60 秒过期回收；仍需在真实 PostgreSQL 多副本环境补充故障注入验证。
- Agent HTTP ingress 已改为缺少内部 secret 时 fail-closed；健康检查仍保持可用，其他请求返回
  `service_auth_not_configured`，但跨仓 admission/outbox 仍需继续补齐。
- Scheduler occurrence claim 已改为 dispatch 后保留至 lease TTL，修复多副本在成功 dispatch 后
  重复执行同一 occurrence 的路径；业务任务注册与恢复协议仍属于 P0。
- Scheduler internal HTTP 现在只接受标准 `Authorization: Bearer` 与 `X-Request-Id`，旧的
  `X-Kokoro-*` 凭据和 request-id 别名已删除，避免继续扩大兼容面。

### P1：IAM、System、Model 的接口实现需要与声明完全对齐

- IAM Proto 声明的认证/授权能力多于当前 HTTP handler；必须区分“目标 contract”和“当前可用
  surface”，不能让 manifest 把未实现 RPC 误判为可用。
- IAM Proto 与当前 HTTP handler 仍需形成“声明/实现”矩阵，避免未实现 RPC 被误判为可用。
- Billing 的旧无版本 HTTP、重复 OpenAPI 文件和 admin manifest 已删除；剩余数据库迁移历史只允许作为数据审阅材料，不能重新成为 writer。
  BFF 的 owner projections 还要逐项做 wire contract 校验。
- Model `/resolve` 本轮已改为内部认证并从可信上下文读取 tenant，同时删除本地 fixture 的 body
  tenant 兼容协议；开发态 route-access 也已取消隐式匿名直通，仅显式测试 fixture 可绕过，后续仍需
  把请求级模型解析为 approved revision/alias 的 contract fixture。
- Billing 已删除 provider webhook 中旧 `site_id` payload hint；应用层内部变量仍有 `siteId` 历史命名，
  后续应在不改变数据库迁移语义的前提下逐步收敛为 tenant vocabulary。
- System 业务路由已删除未配置 service token 时的匿名 fixture 模式；缺少 BFF service credential
  现在明确返回 `503 service_auth_not_configured`，health/readiness 仍为公开探针。

### P1：BFF 入口文件过大，已影响可读性和扩展性

`kokoro-bff/src/main.ts` 当前约 242 行，负责组合根、通用鉴权/幂等管线和最终 owner fallback；资源路由已拆到 `src/http/routes/*`，不再同时承载 Chat、项目、
技能、MCP、Billing、Storage、Scheduler 和 owner projection。职责虽然在业务上属于 BFF，但
实现层仍偏向单文件 route host。当前已经先把 v1 projection、Mori/scheduled 输入 DTO、
Project/ScheduledTask application service、repository port 和 PostgreSQL adapter 分离；下一步
应继续按 vertical slice 拆为：

```text
src/http/router.ts
src/http/auth.ts
src/routes/chat.ts
src/routes/projects.ts
src/routes/capability.ts
src/routes/billing.ts
src/routes/scheduled.ts
src/adapters/*
```

拆分时保持 `main.ts` 只做装配，路由依赖窄接口，避免为了“重构”重新制造跨仓共享包。

### P1：跨仓上下文和认证不能有可配置的 fail-open

开发 fixture 可以显式使用无 secret 的本地模式，但 live/production 业务路由必须强制 service
authentication、IAM-derived tenant context 和 Run scope。不能因为某个 token 未配置就把原始
请求头当作可信权限事实。

### P2：Scheduler 与 Agent 的可靠性边界要补齐

- Scheduler 的 retry horizon 不能超过 occurrence lease；需要续租或按最大退避计算 lease。
- 调度停止必须真正取消 runner、HTTP request 和 backoff context。
- occurrence identity 的精度必须覆盖支持的最小 `@every` interval，不能按秒截断。
- Scheduler 不能把全局 target token 转发到任意 URL，应使用目标 allowlist/绑定的 service identity。

### P2：质量门禁还可以进一步统一

当前仓库的检查命令和成熟度略有差异。下一步建议补齐统一的依赖扫描、SBOM、镜像 provenance/签名、
OpenAPI/Proto breaking check 和跨仓 contract matrix；这些属于发布增强，不改变当前 owner 拆分。

### P2：不要用“lint”掩盖 typecheck，也不要用空成功掩盖缺实现

部分仓库的 `lint` 脚本实际上只是重复执行 TypeScript typecheck；部分 integration 名称实际使用
in-memory fixture。脚本名称、测试分层和门禁结果必须准确表达实际覆盖范围。建议统一：

```text
lint       = 静态规范
typecheck  = 类型检查
unit       = 无外部依赖的单元测试
component  = 本仓 adapter + fixture
integration= 真实 PostgreSQL/Redis/ObjectStore
contract   = Root wire compatibility
```

## 5. Manus API 对齐原则

完整的对齐基线见 [`MANUS_API_ALIGNMENT.md`](./MANUS_API_ALIGNMENT.md)。

Manus v2 的核心不是某几个路径名称，而是成熟的异步资源模型：创建任务立即返回稳定的
`request_id`/`task_id`，通过状态、消息回放、后续消息、确认动作和 webhook 承接完整生命周期。
Kokoro 应当尽量保持这些用户可感知的语义：

```text
POST message/command -> 202 + stable receipt
GET events/messages  -> replayable, cursor-based
confirmation         -> explicit command, not hidden boolean
retry/replay         -> idempotent by command/occurrence identity
```

Kokoro 不需要复制 Manus 的所有外部字段，而是将同一成熟语义落在 BFF Chat、Agent Run、Capability、
Storage、Billing 和 Scheduler 的 owner 边界内。新增 API 先回答资源 owner、生命周期、异步状态、
回放方式、幂等键和错误码，再决定路径和字段。

## 6. 结论

当前拆分没有发现需要重新合并仓库的结构性错误。最合理的长期形态是：

```text
Web = 表现与同源适配
BFF = Chat/业务编排与外部业务入口
Agent = 执行运行时
IAM = 身份授权
System = Site/Workspace/运行配置
Model = 模型目录与解析
Billing = 商业与账务（含 Credit）
Capability = Skill/MCP 控制面
Storage = 文件/对象生命周期
Scheduler = 通用调度执行
```

当前最重要的不是继续增加仓库，而是冻结上述边界，并把 BFF、Scheduler、Root contract、Billing
兼容层这四处收敛到生产级事实源。
