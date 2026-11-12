> 历史过程材料（Task A已收尾）：本页保留原设计／失败／验证事实，不再作为执行入口。现行边界见[当前技术总览](../../kokoro-handbook/technical/00-system-overview.md)，后继事项见[TODO](../../../todo.md)。

# Task A 清理与重构技术方案

> 当前入口：G0已于2026-10-31通过，见ADR-036与实施证据。本文设计约束仍适用，下方阶段状态为历史快照；最新实施状态统一维护于 [Task A闭环方案](https://github.com/LordFoxFairy/Kokoro/blob/bdebba56a046703400845f79ae57834d4dfa4d0a/docs/superpowers/plans/2026-11-01-task-a-c1-c4-technical-plan.md)。不据历史勾选判定当前完成。

> 状态：G0 设计门补齐中；本轮只补契约/盘点/架构材料，不启动服务、不执行数据库清理、不发布。C-1 阶段提交仅作历史阶段证据，C-2/C-3/C-4 实施须等 G0 审阅放行。

## 1. 目标

在实现任务 A（工作台、项目与任务执行）之前，先清理当前代码树中的旧兼容逻辑、无效代码、重复实现、过度分层、无依据的 Repository/Service/Port，以及会拖累当前主路径的历史测试。

本轮完成后，代码应满足：

```text
一个业务事实 → 一个 owner
一个 wire → 一个 canonical contract
一个写入口 → 一个持久化边界
一个读取路径 → 一个状态投影
一套当前测试 → 一套当前门禁
```

本方案明确采用 clean-slate 收敛：旧协议、旧字段、旧路由、旧 alias、旧 fallback、双读、双写、迁移桥均不保留。

## 2. 范围

### 2.1 纳入范围

- `apps/kokoro-app`：会话、URL、Engine、AG-UI 投影、过程展示、项目工作区相关旧逻辑。
- `apps/kokoro-bff`：手写 Node HTTP 运行时、路由组合、Application/Port/Repository 分层、Chat/Project/Agent/AG-UI 相关实现。
- `apps/kokoro-agent`：Run display、历史回放、旧展示事实推导和兼容解析。
- 与上述代码直接关联的 contract、generated 产物、schema、测试和 package scripts。
- BFF 向 NestJS 原生 Module/Controller/Provider/DI 的收敛。

### 2.2 不纳入本轮

- 不实现 A-01/A-02/A-07 业务功能。
- 不新增用户功能、API、数据表、字段或执行能力。
- 不做旧数据迁移、历史数据回填或兼容部署。
- 不清理仅用于审计背景的历史文档；历史文档不得被运行时代码引用即可。
- 不顺手修改 B 负责的 MCP、Skills、账户、团队和 Billing 业务行为；仅清理直接共享且被证明为死代码的部分。

## 3. 当前发现

### 3.1 BFF 架构偏差

Root TypeScript 后端规范要求 NestJS 原生 Module、Controller、Provider、DI；当前 BFF 仍是手写 Node HTTP 入口：

```text
src/main.ts
src/http/routes/*
src/application/*
src/infrastructure/postgres/*
```

BFF 当前没有 NestJS 运行依赖，且通过 `PostgresBffRepositories`、`BffApplicationServices` 和大量 `application/ports/*` 进行手工组合。这是本次必须处理的结构性问题，而非局部样式问题。

### 3.2 过度分层与聚合器

已确认需要逐项判断的高风险位置：

- `apps/kokoro-bff/src/application/services.ts`
- `apps/kokoro-bff/src/application/ports/bff-business-store.ts`
- `apps/kokoro-bff/src/application/ports/chat-repository.ts`
- `apps/kokoro-bff/src/application/ports/project-repository.ts`
- `apps/kokoro-bff/src/infrastructure/postgres/repositories.ts`
- 只做一层转发的 `ProjectService`、简单 CRUD Service、单实现 Port
- 将多个 owner 事实挂到一个 `BffBusinessStore` 的服务定位器

这些位置不能默认保留；只有实际存在事务、lease、CAS、outbox、跨数据源或 owner 边界时才保留独立组件。

### 3.3 App 兼容逻辑

当前 A 相关代码同时包含真正的兼容分支和仍属当前语义的状态：

- **确认删除：** 旧 hash conversation URL 与 query URL 双入口；inline message 与 ordered message/parts 双形态；缺少 public position 时从 Agent seq/数组顺序补位置；未锚定 snapshot activity 的历史顺序 fallback；旧 producer 缺字段时的 optional 兼容。
- **先保留并单独验收：** `ConversationStore.localDraft` 是当前未提交会话的显式 UI 来源证明，不代表 owner 已创建；`conversationTitle` 是服务端标题为空时由首条用户消息派生的当前展示规则；删除最后一项时的空工作台状态需要重写，但不应先按“兼容”删除。
- **严格按 owner 事实重写：** 从旧文本、旧终态或空正文推导 final/cancelled 的分支，只保留 canonical Message/Run/terminal facts 能证明的路径。

因此，C-1 删除的是被证实为旧协议/旧入口的分支；当前 draft/空工作台业务语义进入 A-01 canonical 状态机重写，避免把有效产品状态误删为兼容逻辑。

### 3.4 Agent 兼容逻辑

`apps/kokoro-agent/src/kokoro_agent/application/run_display.py` 及相关 projection/replay 代码存在：

- legacy metadata 解释；
- 由已确认旧版本 source digest 特判的 `legacy_failed` 集合；
- 从旧参数或历史事件补 display detail；
- 历史 display 与当前 Run display 混合读取。

`frozen recipe` 本身不是兼容逻辑，而是当前 Run 的 canonical execution fact 和完整性校验，必须保留；清理目标是删除旧 source digest 特判、旧历史字段补偿和未经当前 Run/journal/checkpoint 证明的展示推导。Agent 最终只保留当前 typed Run journal/checkpoint → `RunDisplay` 的单一路径。

### 3.5 测试负担

当前测试文件规模约为：App 399、BFF 217、Agent 306。BFF 默认 test/contract 脚本维护了大量手工文件列表，并存在多组：

- `schema-evolution`；
- legacy/fallback/preview；
- 同一行为的 input、HTTP、contract、repository、integration 重复覆盖；
- 只保护内部实现或旧目录的测试。

测试必须按当前 canonical 行为重新分级，不能因为历史测试存在就继续保留旧实现。

### 3.6 原有不合理设计与重复实现清单

以下项目不是“风格偏好”，而是会造成事实分裂、依赖隐藏或维护成本失控的结构问题：

| 问题 | 当前表现 | 重构方向 |
|---|---|---|
| 服务定位器 | `PostgresBffRepositories` 暴露大量 public repository/queue/service 字段 | 由 Nest feature module 显式注入，删除全局聚合对象 |
| 巨型业务 Port | `BffBusinessStore` 同时承载 Chat、Project、Agent、Scheduler、AG-UI、Artifact | 按 feature 拆分 provider，删除可选属性和运行时缺失分支 |
| 技术层优先 | `application`/`infrastructure` 先于业务能力组织目录 | 按 sessions/projects/agent-runs/agui 等 owner feature 组织 |
| 薄 Service/Repository | 仅一层 `return repository.method(...)` 的类和 Port | 并入 feature Service 或直接 provider |
| 传输层承载业务 | 手写 route 中包含准入、重试、持久化和状态推导 | Controller 只做输入/输出，业务放 feature provider |
| 状态坐标重复 | Agent seq、public sequence、event cursor、数组位置并存并互相补值 | public sequence + event cursor 为唯一公共坐标 |
| Display 重建事实 | Agent/BFF/App 分别从活动、参数、snapshot 推导展示语义 | Agent 产出 typed RunDisplay，其他层只投影 |
| 错误重复映射 | route、client、mapper 各自重新解释 status/code/body | owner contract 生成闭集，单点映射 |
| 类型镜像 | generated 类型、wire 类型、domain 类型和手写 DTO 重复表达同一 shape | 保留事实源与必要边界类型，删除镜像 |
| Preview/live 混用 | 运行时根据 flag 在 preview client 与 live client 间切换 | preview 仅测试/演示边界，live 无 fallback |
| 手工测试编排 | package script 维护超长文件清单，删除文件后仍可能被引用 | 按 test 目录职责分组，删除孤儿 fixture/helper |

## 4. Clean-slate 规则

### 4.1 强制删除项

以下内容不得进入重构后的生产代码或默认测试入口：

- 兼容 route、兼容 alias、旧 namespace、旧字段别名；
- 双读、双写、旧新 envelope 转换；
- fallback parser、宽松 parser、silent default；
- schema evolution/migration bridge；
- 旧 URL/hash 输入；
- preview/fake 作为 live 运行兜底；
- 仅为历史数据保留的 optional 分支；
- 只在测试中存在、生产没有 owner 的 fake/in-memory 业务实现。

### 4.2 必须保留的业务不变量

删除兼容逻辑不等于删除安全和可靠性：

- tenant/actor/subject 可信上下文；
- 权限和撤权；
- 幂等 key 与 request digest；
- transaction/CAS/lease/outbox；
- cancel、late result、replay、resume；
- 敏感信息过滤；
- AG-UI cursor 与事件去重；
- 失败、unknown、取消的真实终态。

## 5. BFF NestJS 目标结构

### 5.1 运行时目标

```text
src/main.ts                 # 唯一 bootstrap
src/app.module.ts           # composition root
src/config/                 # typed config
src/database/               # PostgreSQL/Redis 生命周期
src/health/                 # readiness/liveness
src/http/                   # 全进程 HTTP 横切能力
src/modules/
  account/                    # profile/session/personalization/account facts
  projects/
  agent-runs/
  agui/
  attachments/
  scheduled-tasks/
```

浏览器请求方向保持：

```text
Browser → Web same-origin adapter → BFF Controller → owner client / database → response
```

### 5.1.1 Feature/provider graph（G0 canonical）

迁移以以下 module 图为唯一目标；`imports` 只表示 Nest module 依赖，`exports` 只暴露表中 provider，禁止回到全局 locator。

| Module | imports | exports | providers / owner clients | 旧 route 映射 |
|---|---|---|---|---|
| `HealthModule` | `ConfigModule`, `DatabaseModule`, `RedisModule` | `ReadinessIndicator` | liveness/readiness、bounded shutdown health | `/healthz`, `/readyz` |
| `IamRelayModule` | `ConfigModule`, `HttpModule` | `IamRelayService` | native-session admission client、IAM protocol relay transport/policy | `iam-protocol-relay`, session/tenant/invitation relay |
| `AccountModule` | `IamRelayModule`, `DatabaseModule` | account readers/writers | profile/session/personalization/archive/share readers；IAM account client | `account-profile`, `account-sessions`, `personalization`, `archived-tasks`, `shared-tasks` |
| `ChatModule` | `AccountModule`, `DatabaseModule`, `AgentRunsModule` | `ChatService`, `ChatFactReader`, `MessageMutationService` | feature-local chat fact readers/writers、message/parts/feedback/regeneration providers、idempotency | `chat`, message mutation/read routes |
| `AguiModule` | `ChatModule`, `RedisModule`, `DatabaseModule` | `AguiProjector`, `AguiReplayReader` | durable ledger/cursor/replay/lease/outbox projector and SSE writer | `agui`, process-page, replay/SSE routes |
| `AgentRunsModule` | `IamRelayModule`, `DatabaseModule`, `AgentClientModule` | run display/control/dispatch providers | Agent HTTP client、dispatch/cancel outbox、run display/final readers | `agent`, `run-display`, model admission/control |
| `ProjectsModule` | `AccountModule`, `ChatModule`, `DatabaseModule`, `StorageClientModule` | project use cases | project CRUD, pins, recommendations, resources, execution binding, scope-release outbox | `project-*`, resource and execution-binding routes |
| `ScheduledTasksModule` | `ProjectsModule`, `AgentRunsModule`, `SchedulerClientModule`, `DatabaseModule` | schedule read/mutation | scheduled task facts, CAS/lease/outbox/receipt and Scheduler client | `scheduled-task-*`, `scheduler` |
| `SkillsModule` | `AccountModule`, `IamRelayModule`, `PlatformClientModule`, `StorageClientModule` | skill use cases | catalog/install/download/import/publish/share/usage providers and owner clients | `skill-*`, local/GitHub import and package routes |
| `McpModule` | `AccountModule`, `IamRelayModule`, `PlatformClientModule`, `StorageClientModule` | MCP use cases | personal/provider/project publication, OAuth/connection, package/icon providers | `mcp-*`, connector routes |
| `BillingModule` | `AccountModule`, `SystemClientModule`, `BillingClientModule` | billing/model admission | credit grant, metering, model admission/settlement clients | `billing-*`, model admission/settlement routes |
| `SystemModule` | `IamRelayModule`, `SystemClientModule` | runtime/model readers | runtime manifest, model catalog/routing/config owner clients | `runtime-manifest`, `model-*` routes |
| `MusicModule` | `AccountModule`, `MoriClientModule` | music use cases | Mori adapter and music routes | `mori`, `music` routes |

| `ConfigModule` | none | `BffConfig` | typed environment/schema validation; no runtime side effects | `src/config/runtime.ts` |
| `DatabaseModule` | `ConfigModule` | `Pool`, `DatabaseReadiness` | create/close PG pool, schema readiness, bounded shutdown | `src/infrastructure/postgres/client.ts` |
| `RedisModule` | `ConfigModule` | `RedisClient`, `RedisReadiness` | create/close Redis DB 8 client, namespace and drain | Redis bootstrap in `src/bootstrap/runtime.ts` |
| `HttpModule` | `ConfigModule` | request-id/body-budget/exception filters | raw headers/body budget/SSE cancellation; no business route | `src/http/request.ts`, `response.ts` |
| `AgentClientModule` | `ConfigModule` | typed `AgentClient` | credential/deadline/cancel transport; no DB access | `src/infrastructure/clients/agent/*` |
| `SchedulerClientModule` | `ConfigModule` | typed `SchedulerClient` | callback/receipt transport and deadline | `src/infrastructure/clients/scheduler/*` |
| `PlatformClientModule` | `ConfigModule` | typed `PlatformClient` | generated Connect/HTTP clients and service credential | `src/infrastructure/clients/platform/*` |
| `StorageClientModule` | `ConfigModule` | typed `StorageClient` | blob/artifact transport and scope policy | `src/infrastructure/clients/storage/*` |
| `BillingClientModule` | `ConfigModule` | typed `BillingClient` | admission/metering/settlement transport | `src/infrastructure/clients/owner/billing-*` |
| `SystemClientModule` | `ConfigModule` | typed `SystemClient` | runtime/model catalog/config transport | `src/infrastructure/clients/owner/system-*` |
| `MoriClientModule` | `ConfigModule` | typed `MoriClient` | music owner transport | `src/infrastructure/clients/mori/*` |

Cross-cutting providers are limited to the modules above plus request-context, request-id, body-budget and graceful shutdown. No Controller receives `Pool`, `RedisClient`, `IncomingMessage` or `ServerResponse`; no module imports another module's database repository directly. Every client module exports only its typed owner client and owns credential/deadline policy; worker/projector lifecycle providers are registered by the feature that owns their durable facts.

### 5.2 Repository 取舍

#### 删除 Repository 的条件

- 只有一个具体实现；
- 只有一个调用方；
- 只是把 SQL/Prisma 调用原样转发；
- 没有独立事务、锁、lease、outbox 或多数据源边界；
- 测试只为了替换它而存在。

此类逻辑并入 feature Service/Provider，删除对应 Port、adapter、mock 和重复类型。

#### 保留 Repository 的条件

- 负责跨多表事务或明确的 owner 写边界；
- 维护 CAS、lease、outbox、幂等 receipt；
- 同一用例需要多个数据源/实现；
- SQL 查询本身是稳定、复杂且独立演进的能力；
- 需要隔离外部 owner 或持久化协议。

保留时 Repository 必须归属 feature module，不建立全局 Repository 层，不建立 BaseRepository。

### 5.3 组合方式

删除 `PostgresBffRepositories` 作为服务定位器和 `BffApplicationServices` 作为聚合器，改为 Nest module 内明确注册：

- `AccountModule` 只导出账户/会话/分享用例和必要 reader；
- `ProjectsModule` 只导出项目用例；
- `AgentRunsModule` 只导出 dispatch/control/read；
- `AguiModule` 只导出 durable projection/stream provider；
- 外部 owner client 由对应 module 注入；
- 禁止把所有 repository/service 挂到一个全局 store。

## 6. 旧逻辑删除矩阵

| 范围 | 删除对象 | 新唯一实现 | 验证 |
|---|---|---|---|
| App 会话 | 旧 hash URL、幽灵 fallback 会话、未锚定顺序 fallback | Engine 临时 submission + BFF session list；`localDraft` 作为明确未提交状态保留 | session creation/retry/URL/draft tests |
| App URL | hash/query 双入口 | canonical query URL | direct/deep-link/back-forward E2E |
| App 消息 | inline/ordered 双形态 | ordered message + parts | strict contract + hydration tests |
| App timeline | Agent seq/数组 fallback | public sequence + activity anchor | reducer/projection tests |
| App final | 旧文本/空正文推断 | exact final reference | final-answer contract |
| BFF route | 旧 route/旧 envelope | Nest Controller + canonical envelope | HTTP contract |
| BFF composition | service locator/聚合 store | feature module DI | architecture tests |
| BFF persistence | 无边界 Repository | feature-local direct provider 或具名 complex Repository | integration tests |
| Agent display | legacy metadata/old recipe | typed RunDisplay projection | display contract/integration |
| 测试 | evolution/fallback/重复旧测试 | canonical unit/contract/integration/E2E | test inventory + default scripts |

## 7. 测试清理矩阵

### 保留

- canonical OpenAPI/Proto/JSON contract；
- owner 权限、tenant、幂等、CAS、lease、outbox；
- fresh schema/install；
- AG-UI live/replay/snapshot 一致性；
- Run 取消、恢复、迟到、unknown、终态；
- A 主旅程浏览器验收；
- 能复现当前缺陷的回归测试。

### 重写

- 仍测试当前行为但耦合旧文件结构的测试；
- 同一事实被多层重复断言、但没有新增证据的测试；
- 直接锁定私有方法、调用顺序、源码字符串的测试；
- 使用旧 fixture 但目标已改为 fresh canonical schema 的 integration。

### 删除

- `legacy`、`compat`、`fallback`、`schema-evolution`、migration bridge；
- 已删除 route/field/alias 的测试；
- preview/fake 作为 live 替代的测试；
- 已无生产消费者的 generated snapshot/oracle；
- 重复验证同一 serializer/parser 的测试；
- 只为让旧实现继续通过而存在的测试。

### 默认脚本

BFF 不再维护超长手工文件清单，统一为目录职责：

```text
test:unit
test:contract
test:integration
test:architecture
test:e2e
```

删除测试时必须同时删除 package script、fixture、helper 和只服务该测试的测试替身。

## 8. 执行阶段

本文件是清理/重构总设计，不把所有改动压成一个实现 PR。后续 implementation plan 必须拆成可独立验证的切片：

1. **C-1 兼容删除**：App、BFF、Agent 的旧 route/field/parser/fallback 删除；native auth cutover 另按 C-1.3 writer 表执行。
2. **C-2 BFF Nest 基础与 A 依赖 feature**：bootstrap、模块、database/http 横切，以及 Account/session、Projects、Agent Runs/AG-UI；非 A route 通过冻结 `LegacyRoutesModule` adapter 暂时承载在同一 Nest listener 内。
3. **C-3 Repository 与重复实现收敛**：按 feature 逐项合并或保留复杂持久化边界。
4. **C-4 测试与门禁收敛**：删除旧测试、重写 canonical 测试、重建默认脚本。
5. **A-01/A-02/A-07**：仅在 C-1～C-4 完成并通过 Root 验证后进入业务实现。

### 阶段 0：只读盘点

- 固定当前 Root/submodule HEAD、工作区 diff、运行入口和正常源码。
- 建立生产 import graph、route inventory、owner/写入口表、测试覆盖矩阵。
- 标记死代码、重复实现、兼容逻辑、过度分层和测试孤岛。

### 阶段 1：删除兼容逻辑

- 先删生产兼容分支和旧入口。
- 同步删掉只保护这些分支的测试、fixture、脚本和 generated 消费。
- 将 strict canonical parser/contract 设为唯一入口。

### 阶段 2：BFF NestJS 收敛

- 建立 Nest bootstrap、app module、config/database/health/http 基础模块。
- 先迁移 Account/session、Projects、Agent Runs、AG-UI 四个 A 依赖 feature；随后完成其余 graph modules。
- 删除手写 route dispatcher、服务定位器和无信息增益的 application/infrastructure 层。
- 复杂事务/lease/outbox Repository 迁入对应 feature module；简单 CRUD 直接由 Service/Provider 访问数据库。

### 阶段 3：测试收敛

- 删除历史兼容测试。
- 为 canonical feature 建立最小充分的 unit/contract/integration/E2E。
- 重写 package scripts 与 architecture boundaries。
- 对所有删除项执行反向搜索，确保没有生产引用。

### 阶段 4：再进入任务 A

- 以清理后的 BFF contract 和 Nest feature 为基线实现 A-01。
- A-02 只接 canonical AG-UI/snapshot/parts/RunDisplay。
- A-07 在会话主片稳定后实现。

## 9. 验证门禁

本轮清理/重构完成前，不报告任务 A 功能完成。至少需要：

```bash
git diff --check
python3 scripts/verify-repository-topology.py
pnpm lint
pnpm typecheck
pnpm test:architecture
pnpm test
pnpm build
```

各子仓还需执行其自身 `format/typecheck/contract/test/build` 门禁；涉及数据库时使用 fresh isolated schema，不执行正常库破坏性清理。

兼容残留审计：

```bash
rg -n -i 'legacy|compat|fallback|deprecated|schema-evolution|migration-bridge|alias' \
  apps/kokoro-app apps/kokoro-bff apps/kokoro-agent
```

命中项必须逐条归类为：删除、当前业务语义、或仅文档历史；运行时代码和默认测试入口不得保留兼容命中。

## 10. 完成条件

- BFF 已按 NestJS 运行时和 feature module 收敛，A 依赖的四个 feature 不再依赖旧手写 dispatcher。
- 兼容 route/field/alias/fallback/double-read/double-write 全部删除。
- Repository 只保留真实事务、锁、outbox、owner boundary 或多数据源需要的部分。
- `BffBusinessStore`、全局 service locator、无信息增益的 service/port 层已删除或拆回 feature owner。
- 测试默认入口只包含 canonical 当前行为；旧测试不再拖累当前门禁。
- 生成物由唯一事实源生成，未手改、未保留重复副本。
- Root 重新验证通过后，才开始任务 A 的业务实现。

## 11. 当前决策

本方案已确认：

1. BFF 纳入 NestJS 收敛；
2. 兼容逻辑强制删除；
3. 先清理与重构，暂不写业务代码；
4. 明确检查不合理设计、重复实现、Repository 取舍和测试清理；
5. 清理完成后再进入任务 A 的 A-01/A-02；
6. 人类登录采用方案 B：IAM 是唯一浏览器登录/用户会话 owner，Product Web 不再作为 first-party OAuth/OIDC RP；同源 Web adapter 只消费 IAM native session，native admission consumer 切换后删除 Product Session cookie/store 与 refresh reservation；
7. 机器身份与人类登录分开：内部服务统一 direct service credential + 可信用户上下文，删除 `global_register` workload OAuth 例外；第三方 MCP OAuth、IAM 作为外部 OAuth issuer 的能力和 Billing 资金授权不删除。

方案 B 的边界说明：这不是让每个后端项目各自实现登录，而是让每个后端不实现浏览器 OAuth。`kokoro-iam` 继续唯一拥有 Better Auth/native browser session、OAuth/OIDC provider、User/Tenant/Permission；`kokoro-app` 与 `kokoro-admin` 是同源 Web 消费方；BFF、Capability、System、Billing、Storage、Agent 只消费受信 session context 或 direct service credential。方案 B 的实现前置是先发布 IAM native-session 到 Web/BFF 的单一 session-admission 契约，再删除 App 的 Auth.js/OIDC RP、Product Session cookie/store 和 refresh reservation；不留下第二套无身份会话。

### 11.1 方案 B 的 native-session admission 契约（G0 fixed design input）

为避免“删掉 OAuth 后再造第二个 token 系统”，目标传输固定为 IAM 原生 session cookie + BFF direct service credential：

```text
Browser Cookie (IAM native session, HttpOnly)
  -> App same-origin adapter
  -> BFF request (allowlisted Cookie only)
  -> IAM /internal/v1/native-session-admission/verify
       + BFF direct service credential
  -> trusted {subject, tenant, session, permissions}
```

契约约束：

- IAM 继续是 session row、session revocation、active tenant、membership、role、permission 的唯一 owner；BFF 不读 IAM 数据库。
- IAM native session cookie 的路径必须覆盖同源 App/BFF adapter；优先把 Better Auth session cookie 从当前 `/iam` path 收敛到统一同源 path，并在迁移窗口清除旧 path cookie，不同时维护两套 cookie。
- App 只转发 IAM allowlist cookie、Origin/CSRF 所需头和 request id；不接受浏览器 `Authorization`、body 自报 tenant/subject，也不把 IAM cookie 暴露给 JavaScript。
- BFF 以 direct service credential 调 IAM native-session admission；请求携带的 cookie/session handle 是用户会话句柄，不是 OAuth access token，不做 token mint、refresh、exchange 或 introspection。
- IAM 现有 `POST /internal/v1/session-authorizations/verify` 继续只服务真正的 user-delegated bearer / Open App / API-key 语义；它依赖 OAuth client/resource/binding，不能把 first-party Web native cookie 硬塞进这个 endpoint。方案 B 应发行独立的 `native-session-admission` owner contract 和 BFF 专用 direct credential profile，再在没有消费者后删除旧 first-party RP，而不是给旧 endpoint 加双输入 fallback。
- 新 native profile 使用接收方拥有的独立 credential file（caller=`kokoro-bff`、surface=`session_admission`、固定 Product tenant），不复用 Platform/Billing/Agent credential；IAM 每次鲜读、校验文件权限/轮换/重复 secret/tenant 绑定，BFF 每次请求只带该 direct credential。
- IAM 响应只返回当前可信 `subject_id`、`tenant_id`、`session_id`、当前资格和闭集错误；不返回 access token、refresh token、OIDC code、client secret 或原始 cookie。
- BFF 每次业务请求重新 admission；撤销、租户切换、账号禁用、权限变化立即由 IAM 当前事实生效。BFF 不缓存长期用户准入结果。
- Sign-in、sign-out、tenant selection 保留 IAM native endpoint 和同源 CSRF；删除 `/oauth2/authorize`、`/oauth2/token`、`/oauth2/continue`、`/oauth2/end-session` 的 first-party Web 路径。
- Product Session cookie/store 与 refresh reservation 在 native admission consumer 切换后删除；不保留无凭据投影、双读或双写。BFF 直接消费 IAM native session，跨进程传递由 allowlisted Cookie 完成。

G0 已固定 IAM owner artifact `apps/kokoro-iam/contract/openapi/native-session-admission.v1.json`（version `1.0.0`, SHA-256 `5cf59df4b7bd9853edfd2eabb31afc236c0ec0db371f9737706fc129484fd83f`）。请求不接受 caller-supplied tenant；IAM active tenant 是唯一 tenant source，因此错误闭集不含 tenant-mismatch 分支。本轮不修改 IAM runtime、Schema、cookie path 或 HTTP 业务实现；后续必须按该 artifact 生成/校验 SDK，再由 App/BFF 成对切换，最后删除旧 RP 和 token 测试。该 artifact 是 owner machine contract pin，不是已完成的 controller/consumer 实现。

本文件是设计基线，不等同于已实施、已验证或已合并。

阶段执行顺序、唯一 writer、停写门、C-1～C-4 验证和进入 A-01/A-02/A-07 的具体步骤见 [执行计划](https://github.com/LordFoxFairy/Kokoro/blob/bdebba56a046703400845f79ae57834d4dfa4d0a/docs/superpowers/plans/2026-10-30-task-a-cleanup-refactor-execution.md)。
