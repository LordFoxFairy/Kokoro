# Kokoro 后端最终架构与目录规约（历史全局拆仓总图）

状态：**历史全局拆仓总图**，2026-08-22。标题中的“最终”只反映旧 SQL-first 拆仓阶段；其中独立 `kokoro-chat` owner、Chat/Session 分离与 Capability runtime snapshot 不覆盖当前 Feature-first GA 架构。

当前总评审入口是 [36 GA 整体 Agent 技术方案](36-ga-final-agent-technical-plan.md)、[37 产品体验与 Agent Studio](37-product-experience-agent-studio-architecture.md)、[38 公共运行契约](38-ga-public-runtime-contract.md) 与 [backend-design manifest](backend-design/backend-design-manifest.json)：产品 Session 是会话消息/projection/control 的唯一 owner，GA 是 `ConversationState`/checkpoint 的唯一 owner。


历史状态：旧“最终”拆仓汇总，非当前 Agent/Session/Capability target。

本文保留后端仓库、业务边界和目录的历史汇总，不再作为当前总入口。当前 Feature-first owner 由 36/37/38 与目标设计卡裁决。

逐仓库执行级设计卡见 [`technical/backend-design/`](backend-design/README.md)；本文件与设计卡冲突时，以设计卡的具体 owner/目录说明为准，并通过 ADR 记录反向变更。

Redis 运行时依赖、Streams、Lua、HA 与故障矩阵见 [`28-redis-runtime-and-idempotency-research.md`](28-redis-runtime-and-idempotency-research.md)。

## 0. 2026-08-22 Billing 架构修订

本节修订本文件中旧的 Payment/Credit 独立仓库描述。以后的 Billing 设计以
[`31-billing-subrepository-architecture.md`](31-billing-subrepository-architecture.md)、
[`billing-transaction-matrix.md`](billing-transaction-matrix.md) 和
[`backend-design/05-billing.md`](backend-design/05-billing.md) 为执行级权威：

- `kokoro-payment` 与 `kokoro-credit` 收敛为一个目标代码子仓库 `kokoro-billing`；
- `kokoro-billing` 内部保留 Payment 与 Entitlement/Credit 两个 bounded context；
- Billing 对外统一使用 IAM 提供的 opaque `tenantId` 与 `x-kokoro-tenant-id`；MySQL 内部历史物理列仍可暂用 `site_id`，只在 HTTP adapter 做 `tenantId -> site_id` 映射。新 Provider metadata 使用 `tenantId`；历史 payload 的 `siteId` 仅做映射结果一致性校验，不作为租户选择依据；
- Payment 拥有 provider money facts、checkout、settlement、reversal；
- Entitlement/Credit 拥有 catalog、fulfillment、subscription term、CreditGrant、Hold、Journal、metering；
- User、Admin、Internal、Webhook 是四个 API surface，Admin 与 User 的认证、授权、响应模型和限流策略分离；
- Payment 不直接写 Credit 表，跨上下文通过 settlement/reversal source fact、application port 和 outbox 协作；
- MySQL 8.4 是最终业务事实，Redis 只承担短 TTL 幂等快速路径、锁/lease、缓存、限流和异步协调；
- 本文件 6.7/6.8 的旧独立仓库目录仅作为迁移前 current-state 记录，不再是新能力的目标 owner。

这次修订不代表迁移已经完成；完成证据仍须同时满足目标仓库、schema、契约、测试、旧 writer 删除和对账门禁。

## 1. 最终决策

Kokoro 采用：

```text
战略层：按业务能力划分 Bounded Context
代码层：业务模块优先，技术层次局部化
复杂度层：L0 / L1 / L2 分级采用 DDD
运行时层：业务服务、会话管道、Agent 执行器分别采用适合自己的结构
数据层：MySQL 结构化事实、MongoDB 文档/向量事实；每个事实一个 owner、一个 runtime writer
契约层：Root contract/ 为跨仓唯一契约源
```

不采用：

```text
全仓统一 domain/application/infrastructure/interfaces 模板
全局 domain/entities、domain/services、common、utils 垃圾桶
按数据库表拆业务仓库
按技术组件拆业务边界
把 Agent/Session 强行改成业务 DDD
用 Platform 父仓承载所有业务编排
```

## 2. 四个边界必须分开

```text
Repository       代码协作、版本、所有权边界
Bounded Context  业务语言、模型和规则边界
Module           一个仓库内部的业务能力边界
Deployment Unit  独立启动、发布、扩缩容边界
```

它们可以暂时合并，但不能因为当前部署方便就把它们永久混为一谈。

```text
一个 Repository 可以包含多个 Module
多个 Module 可以先共用一个进程
一个 Bounded Context 未来可以拆成独立 Repository
一个 Deployment Unit 不必等于一个数据库表或一个领域对象
```

## 3. 最终仓库拓扑

```text
Kokoro/
├── contract/                 跨仓契约源、生成器、兼容性门禁
├── database/                 MySQL 物理 schema、migration、baseline、owner inventory、验证
├── deploy/                   根级部署样例和基础设施声明
├── scripts/                  跨仓验证、闭环和一次性工具
├── docs/                     总架构、规范、ADR、迁移计划
├── kokoro-iam/               身份、组织和授权
├── kokoro-model/             模型目录和路由策略
├── kokoro-billing/           Payment + Entitlement/Credit；统一商业账务闭环
├── kokoro-credit/            迁移中的历史 runtime，不接收新业务能力
├── kokoro-payment/           迁移中的历史 runtime，不接收新业务能力
├── kokoro-capability/        Skill/MCP 控制面
├── kokoro-storage/           文件和产物生命周期
├── kokoro-chat/              会话业务
├── kokoro-session/           会话编排、relay、SSE、恢复运行时
├── kokoro-agent/             Agent 执行、工具、能力和状态运行时
└── kokoro-web/               用户面和运营面前端
```

### Root 仓职责

Root 只拥有跨仓事实：

- Protobuf/OpenAPI/JSON Schema 源文件
- MySQL 物理 schema、migration、表 owner 和 baseline
- MongoDB collection、index 和向量 owner 清单
- 生成产物的 provenance 和兼容性检查
- 跨仓版本组合、E2E 和数据库验证
- 文档入口与总体迁移状态

Root 不拥有业务 Service、领域 Entity、模块 Repository，也不提供中央 `common` 业务包。

## 4. 业务后端统一使用“模块优先”

不是：

```text
src/domain/
src/application/
src/infrastructure/
src/interfaces/
```

然后把所有领域混在一起。

而是：

```text
src/modules/<business-module>/
├── domain/           只有该模块确有领域规则时创建
├── application/      该模块的用例和事务编排
├── infrastructure/   该模块的数据库和外部适配器
└── interfaces/       该模块的 HTTP/RPC/worker 入口
```

简单模块可以不创建完整层级：

```text
src/modules/model-catalog/
├── model.ts
├── repository.ts
├── service.ts
└── routes.ts
```

复杂模块才展开聚合和子领域：

```text
src/modules/credit/
├── account/
│   ├── domain/
│   ├── application/
│   ├── infrastructure/
│   └── interfaces/
├── hold/
├── ledger/
└── usage/
```

## 5. DDD 采用等级

### L0：简单数据模块

适用于配置、只读目录、简单后台资源和无复杂状态的 CRUD。

```text
业务模块 + Application Service + Repository + schema
```

不创建空的 Entity、Aggregate、Value Object、Domain Event 目录。

### L1：轻量 DDD

Kokoro 默认等级。重点是业务模块边界、领域词汇、Repository 隔离和局部业务规则。

```text
modules/capability/
├── domain/
├── application/
├── infrastructure/
└── interfaces/
```

Application 可以承载业务流程编排；稳定且需要复用的状态规则应进入 Domain 对象或 Policy。

### L2：标准战术 DDD

只用于 Credit、Payment、IAM 和确有复杂状态机的模块。

必须明确：

- 聚合根是谁
- 聚合保护哪些不变量
- 哪些状态必须同一事务完成
- 哪些值具有独立业务语义
- 哪些事件是真实领域事实

答不出这些问题时，不得仅凭目录命名宣称使用 L2。

## 6. 最终业务边界与目录

### 6.1 `kokoro-iam`

目标合并来源：`kokoro-site` + `kokoro-user`。

```text
kokoro-iam/
├── src/
│   ├── modules/
│   │   ├── site/
│   │   ├── identity/
│   │   ├── organization/
│   │   ├── authentication/
│   │   ├── authorization/
│   │   └── audit/
│   ├── generated/
│   ├── config/
│   ├── bootstrap/
│   └── main.ts
├── test/{unit,integration,architecture}/
└── docs/
```

Site 是 IAM 的 Site/Realm 子域，不单独制造 Site runtime。动态域名运营、Fleet 或独立 Site 生命周期真正形成新上下文时再拆分。

### 6.2 `kokoro-chat`

```text
kokoro-chat/
├── src/
│   ├── modules/
│   │   ├── conversation/
│   │   ├── message/
│   │   ├── interaction/
│   │   └── run-projection/
│   ├── infrastructure/
│   ├── interfaces/
│   ├── generated/
│   ├── config/
│   └── main.ts
└── test/
```

Chat 拥有会话业务事实和投影，不拥有浏览器 SSE relay 的传输实现。

### 6.3 `kokoro-agent`

不套 DDD，按执行链路组织：

```text
src/kokoro_agent/
├── contract/            生成 wire 类型
├── worker/              消费、租约、恢复、关停和进程装配
├── agents/              preset/factory 与本次 run 装配
├── execution/           agent invoke、HITL、终态认领、事件发射
├── state.py             RunScope 和 graph state
├── tools/ skills/ mcp/  授权 capability runtime
├── subagents/ sandbox/  委派执行与执行环境
├── model/               model/provider adapter
├── storage/             checkpoint、memory、run ledger
├── streams/             request/control/event adapter
├── prompts/
└── config.py
```

这里的 `run/capabilities/providers/persistence` 是语义层，分别由
`state.py`、五个 capability sibling packages、`model/`/`content_source.py`、`storage/`
实现；不以改目录名取代运行时设计。Agent 的核心模型是执行阶段、运行状态、能力装配和
事件管道，不是业务聚合。

`S3Workspace` 属于 GA 管理的可选 sandbox workspace adapter：当前 S3 profile 连接
MinIO 的 S3-compatible API（默认 profile 仍为 local workspace），生产可切换 AWS S3、Ceph、R2 或其他 S3-compatible
provider。它既不是 Artifact 业务 owner，也不是 Agent core 的硬依赖；业务 Artifact
仍走 Storage 的公开 upload/finalize contract。

Skill 采用 **GA-first runtime**。`Agent.default_skills` 是 GA 直接拥有的默认能力，不依赖
Capability/Storage；其他 GA optional Skill 与 CA 提供的 user/session logical path 都通过固定的
`find_skills(query, limit)` / `load_skill(candidate_ref)` 进入同一发现面。`candidate_ref` 由 GA 生成，模型不提交裸
name、path、URL 或 bucket key。CA（`kokoro-capability`）只负责 user/session source 的 CRUD、目录、可见性与 opaque path；
Storage 只提供受控 package bytes、scan 与 checksum/reference。

GA 在加载时复核当前 policy、path、manifest、scan 与可选 digest，再将已验证内容挂载到 GA thread workbench，并写
`.kokoro/skills.lock` 供 pause/resume、worker 迁移或 sandbox 重建时重物化。lock 不进入 checkpoint 或 Session，也不形成
run binding、Skill revision 或版本平台。CA 与 Storage 都服务于 Skill，但不拥有 DeepAgents 的发现决策、加载、workbench
或恢复。

因此 Agent worker 删除的是 legacy Hub 直读及 `seed/upsert` 混合面，而非 GA 自己的配置/发现能力。默认 Skill
不依赖 CA；动态 Skill 不改变 graph/tool schema，也不把全量 Skill 文档塞进图。完整过程见
[33 GA-first SkillRuntime](33-ga-first-skill-runtime-architecture.md)。

### 6.4 `kokoro-session`

不套 DDD，按会话传输管道组织：

```text
src/
├── ingress/             HTTP command admission
├── relay/               agent wire -> session event
├── projection/          snapshot 和 pending pause 投影
├── persistence/         Mongo store、seq 和幂等
├── transport/           Redis live bus、SSE attach
├── recovery/            未终态 run 恢复
├── contract/            生成协议类型
├── config/
└── main.ts
```

Session 只编排、持久化和传输，不执行 Agent，不拥有用户/支付/积分主数据。

### 6.5 `kokoro-capability`

```text
src/modules/
├── client-skill/           Client/租户 Skill catalog、安装、可见性
├── mcp/
├── installation/
├── authorization/
└── runtime-snapshot/
```

Capability 是 GA 的 user/session Skill source 辅助面：它维护目录、path、可见性和管理 CRUD，
并以 Storage asset reference 指向 package bytes。GA 保有默认 Skill、vector discovery、候选二次
校验、加载决策和 DeepAgents 注入；Capability 的 runtime snapshot/path 只供 GA 发现和读取前解析。
包存储和 secret store 都是 adapter，不拥有运行时注入状态。

### 6.6 `kokoro-model`

```text
src/
├── catalog/             provider、definition、revision
├── routing/             binding、fallback、health projection
├── policies/            site/feature visibility
├── adapters/            LiteLLM/direct provider
├── interfaces/
├── generated/
├── config/
└── main.ts
```

Model 负责“可用什么、如何路由”，不负责扣费、权益和用户权限最终裁决。

### 6.7 `kokoro-payment`（历史 current-state；目标迁移至 `kokoro-billing`）

```text
src/
├── modules/
│   ├── catalog/             plan、price、feature package
│   ├── checkout/
│   ├── order/
│   ├── provider-event/
│   ├── subscription/
│   ├── refund/
│   └── benefit-grant/       购买后的 credit/feature 授予编排
├── providers/           stripe、alipay、wechat 等 adapter
├── generated/
├── config/
├── bootstrap/
└── main.ts
```

Provider payload 先在 adapter 边界归一化，Domain 不依赖 Stripe/支付宝/微信类型。

本节只记录迁移前结构。新方案不再增加 `benefit-grant` 或跨仓 Credit client；套餐购买的 fulfillment、subscription term 和 credit grant 迁移到 `kokoro-billing` 的 Entitlement Context，provider money facts 留在 Payment Context。

### 6.8 `kokoro-credit`（历史 current-state；目标迁移至 `kokoro-billing`）

```text
src/modules/
├── credit/        ports、inputs、views、domain errors
├── hold/          hold lifecycle 与 settle 编排
├── pricing/       pricing rule 与 quote
├── usage/         usage read boundary
└── admin/         quota、stats、生命周期
src/infrastructure/
├── mysql/         Credit/Hold repository、InnoDB transaction
└── redis/         mutation cache、lease、coordination
```

CreditAccount、CreditHold、LedgerEntry 的聚合和事务边界按余额不变量设计，不能按表生成万能 CRUD Service。

### 6.9 `kokoro-storage`

```text
src/
├── modules/
│   ├── blob/
│   ├── upload/
│   ├── asset/
│   ├── artifact/
│   └── scan/
├── object-store/        Local/S3 实现
├── scanners/            扫描器 adapter
├── interfaces/
├── config/
└── main.ts
```

Local 和 S3 是同一个 ObjectStore 端口的实现，不是两个业务模块。

### 6.10 `kokoro-platform` 与 `kokoro-platform-kit`

`kokoro-platform` 不进入最终业务运行时拓扑。它当前只是历史上的平台父仓/模块集合；其注册表、组合、验证和部署职责回收到 Root 的 `scripts/`、`deploy/`、`database/` 和 `docs/`。现有代码在迁移完成前保留为 legacy，不再向其中增加新业务能力。

`kokoro-platform-kit` 也不作为独立业务仓库保留。确有跨服务技术代码时，放入受控的技术基础包；业务 DTO、业务 Policy 和业务 Repository 不进入共享包。

```text
Root/
├── scripts/                 跨仓注册、验证和组合命令
├── deploy/                  部署组合
├── database/                数据库工具链
└── docs/                    架构与规范
```

### 6.11 `kokoro-litellm`

```text
platform-kit:
  http / config / errors / security / request-context

litellm:
  config / scripts / deploy / docs
```

前者只放技术能力，后者只放网关部署接入；二者都不是业务领域仓库。

## 7. 统一依赖规则

业务模块内部：

```text
interfaces -> application -> domain
infrastructure -> domain/application contracts
bootstrap/main -> concrete implementations
```

运行时仓库使用自己的自然依赖：

```text
session: ingress -> relay/projection -> persistence/transport
agent: worker -> execution -> capabilities/providers/persistence
```

禁止：

- Domain 依赖 ORM、HTTP、RPC 或 provider SDK。
- Interfaces 直接写数据库。
- Application 直接创建具体 Infrastructure 实例。
- 模块直接导入其他模块的数据库 Model 或 Repository 实现。
- 通过 `common`/`shared` 传播领域对象。
- generated 文件被业务代码手工修改。

## 8. 测试目录

```text
test/
├── unit/                  领域规则和用例
├── integration/           真实数据库/外部边界
├── contract/              RPC/OpenAPI/生成契约
└── architecture/         依赖、owner、入口和生成物门禁
```

复杂模块内部可按业务模块镜像；不按“所有 Service/Repository”做技术垃圾桶。

## 9. 当前实现迁移顺序

不做一次性目录大搬家，按以下顺序迁移：

1. 为每个模块登记 owner、用例、表、入口和公开契约。
2. 先建立目标模块目录和 `INDEX.md`，不立即删除旧目录。
3. 将现有代码按业务能力映射到目标模块。
4. 先迁移一条完整核心用例及其测试。
5. 增加 architecture test，禁止新代码扩大旧跨模块依赖。
6. 通过行为、数据库、契约和集成门禁。
7. 删除旧入口，更新 README、INDEX、ADR 和迁移记录。

当前平台旧 MySQL/Prisma 模块与新的 MySQL migration/baseline 目标同时存在时，文档必须明确标注 current/target，不能用目录移动掩盖数据库和运行时迁移尚未完成的事实。旧 Root PostgreSQL baseline 按 ADR-013 处理为迁移期历史方案。

## 10. 目录设计验收

新仓库或新模块必须能回答：

- 它属于哪个业务能力或运行链路？
- 谁是数据 owner，谁是唯一 writer？
- 选择 L0、L1 还是 L2 的理由是什么？
- 哪些文件是 Domain、DTO、数据库行、契约生成物？
- 入口和副作用在哪里？
- 哪些模块明确不能 import？
- 测试如何证明边界成立？
- 当前实现到目标结构的迁移步骤是什么？

任何只能回答“这是公司的统一模板”“大家都这么建目录”的设计，不通过架构评审。

## 11. 研究结论与可迁移原则

这份最终设计不是从一张 DDD 目录图反推出来的，而是对照以下成熟实践后收敛：

| 参考 | 采用的原则 | Kokoro 的落点 |
|---|---|---|
| [DDD by Examples / library](https://github.com/ddd-by-examples/library) | 每个 Bounded Context 使用与问题复杂度匹配的局部架构；复杂借贷域使用领域模型，简单域可以 CRUD | L0/L1/L2，不要求所有仓库统一深度 |
| [Kamil Grzybek Modular Monolith](https://github.com/kgrzybek/modular-monolith-with-ddd) | 模块拥有公开 API、内部隔离和架构测试；模块可以先共进程，再独立演进 | Module 先于 Deployment Unit，architecture tests 强制边界 |
| [GitLab domain isolation](https://handbook.gitlab.com/handbook/engineering/architecture/design-documents/modular_monolith/domain_layer/) | Domain 只通过公开 API 交互，独占自己的数据；领域代码与通用库分开 | 每张表一个 owner，禁止跨模块模型和表访问 |
| [Microsoft eShop reference architecture](https://github.com/dotnet/docs/blob/main/docs/architecture/cloud-native/introduce-eshoponcontainers-reference-app.md) | 不同服务按复杂度选择 CRUD 或 DDD，而不是架构一刀切 | Model 可 L0/L1，Credit/Payment 才进入 L2 |
| [Shopify CLI architecture](https://shopify.github.io/cli/cli/architecture.html) | 基础能力与可选 feature 模块分开，模块应有可解释的依赖层次 | Root 技术工具和业务模块分开，不制造 Platform 业务父层 |

从这些项目中保留的不是目录名字，而是五条判断：

1. 先确认业务边界，再决定 Repository、进程和目录。
2. 一个上下文内部可以有自己的局部架构，复杂度不同不强行统一。
3. 领域隔离必须有公开 API、数据所有权和自动化架构门禁。
4. 模块化的价值是可独立理解、测试和演进，不是把系统拆成更多名字。
5. 目录移动不是架构重构；边界、依赖、数据和契约必须同时改变。

## 12. 各仓库 100 分设计验收卡

以下是“设计完成度”评分，不是对当前代码已落地程度的虚假宣称。每个仓库只有在实现阶段提交证据后，才能把对应卡片标记为已达 100 分。

通用评分：

```text
边界和职责       20
数据 owner        15
复杂度/DDD 选择   15
目录可读性        15
依赖可执行性      15
公开契约          10
测试映射          10
--------------------
合计              100
```

设计阶段的目标卡片：

| 仓库 | 100 分必须证明的重点 |
|---|---|
| IAM | Site/Identity/Organization/Auth/Authorization 分域；权限和数据 owner 清楚；核心不变量进入 L2；跨域只走公开 API |
| Model | Catalog、Routing、Policy 分开；LiteLLM 只是 adapter；不把 pricing、credit、用户授权塞进 Model |
| Credit | Account/Hold/Ledger/Usage 聚合关系清楚；余额不变量、事务、幂等和并发更新可验证 |
| Payment | Catalog/Checkout/Order/Provider Event/Subscription/Refund 分开；provider payload 归一化；不写 Credit 表 |
| Capability | user/session Skill path + MCP/Installation/Authorization 辅助边界清楚；GA 保有默认/发现/注入；包存储和 secret store 只是 adapter |
| Storage | Blob/Upload/Asset/Artifact/Scan 生命周期清楚；Local/S3 只实现同一 ObjectStore 端口 |
| Chat | Conversation/Message/Interaction/Run Projection 与 Session 传输分离；不拥有 Agent 执行 |
| Session | Ingress/Relay/Projection/Persistence/Transport/Recovery 形成完整管道；不伪装成业务 DDD |
| Agent | Worker/Run/Execution/Capabilities/Persistence/Streams 形成执行链路；只消费 opaque namespace |
| Root | Contract/Database/Deploy/Scripts/Docs 各有唯一职责；不成为中央业务服务 |

任何一项只能靠 README 口头解释、无法通过 import/test/schema/contract 证据证明，均不得记满分。

## 13. 当前代码证据与目标差距

“设计 100 分”不等于“当前代码已经落地”。截至当前仓库证据，目标和实现关系如下：

| 目标边界 | 当前证据 | 当前结论 | 下一步 |
|---|---|---|---|
| IAM | `database/schema/20-iam.sql`、`contract/consumers.yaml` 已有 `kokoro-iam`；旧 Platform 仍有 site/user | 目标边界已有基础，旧入口未合并 | 统一 contract consumer、迁移 site/user 行为后删除旧入口 |
| Chat | `database/schema/30-chat.sql`、contract chat、session 运行时 | 业务数据和传输运行时仍需明确 owner 分离 | Chat 拥有业务事实，Session 只拥有传输管道 |
| Agent | `database/schema/40-agent.sql`、`kokoro-agent` 真实执行代码 | 运行时结构成熟，不做 DDD 重排 | 只校验 contract、namespace 和 adapter 边界 |
| Capability | `kokoro-capability` canonical MySQL schema、Root v1 contract、独立 Skill/Connector/MCP clients、Redis fail-closed runtime、Capability architecture/integration/contract tests | Capability v1 control-plane 已落地；旧 Hub 仍是迁移前历史写面 | 完成 Hub 只读迁移与 Agent/GA dynamic source cutover 后删除旧写面和 Root compatibility descriptor |
| Model | `database/schema/60-model.mysql.sql`、旧 `kokoro-model` | 目标和现有模块较接近 | 收敛 provider/routing/policy 目录，清理跨模块依赖 |
| Credit | 独立 `kokoro-credit` 拥有 MySQL/InnoDB schema/migrations、Redis coordination、账户 mutation、pricing、quota reset、ledger/usage read、原子 SettleUsage、Hold/Capture/Release runtime、reconciliation、audit events、Prometheus metrics、HTTP/RPC 文档和真实依赖测试；旧 `kokoro-platform/kokoro-credit` 已删除并改为 external registry | 独立 runtime 已接管 writer；剩余是生产部署告警、审计归档和读面分页策略 | 切换剩余 consumers 到 contract，补齐生产部署与 admin lifecycle 门禁 |
| Billing | 目标 `kokoro-billing` 已建立架构入口、API OpenAPI、事务矩阵、MySQL schema 规范和迁移映射；旧 `kokoro-payment`/`kokoro-credit` 仍是历史 writer | 设计与迁移准备完成，runtime 尚未切 writer | 按 migration gates 实现 schema、use case、真实依赖测试、双写对账，再停止旧 writer |
| Storage | `kokoro-storage` canonical MySQL schema、Root v1 contract、唯一生产入口、Redis fail-closed runtime、AWS SDK S3-compatible adapter、真实 MinIO smoke 与 Capability package E2E | Storage v1 已落地并通过真实基础设施验证；无 MongoDB 依赖 | 按迁移计划切换 Session workspace、Agent sandbox 和 Hub package 旧写面，完成对账后删除旧 writer |
| Session | `kokoro-session/src/{relay,store,transport,http}` 真实存在 | 管道结构已存在 | 按 ingress/projection/persistence/recovery 补职责地图，不改成 DDD |
| Root | `contract/`、`database/`、`scripts/`、`deploy/`、`docs/` 真实存在 | Root 具备承载条件 | 逐步吸收 legacy platform 的 registry/composition/validation |

因此，当前仍不能把整体迁移描述写成“已完成”：Credit、Payment、IAM 以及 Capability/Storage 的外部 consumer cutover 仍有独立门禁。Capability/Storage v1 本身已具备 schema、入口、契约、测试和运行时证据；最终整体状态仍以各仓库的旧 writer 删除、对账和生产部署证据为准。
