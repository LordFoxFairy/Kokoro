# 后端仓库、模块与目录架构总设计（历史全局拆仓方案）

状态：**历史全局拆仓方案**，2026-08-22。本文保留早期仓库/DDD 推导；其中 `kokoro-chat` 与 `kokoro-session` 的双层会话 owner、Capability runtime snapshot 不进入当前 Feature-first 目标。

当前目标目录与 owner 以 [36 GA 整体 Agent 技术方案](36-ga-final-agent-technical-plan.md)、[38 公共运行契约](38-ga-public-runtime-contract.md) 和 [backend-design manifest](backend-design/backend-design-manifest.json) 为准。


> 版本说明：本文是 Billing 收敛前的拓扑基线。Payment/Credit 的最新目标拓扑与迁移态说明见
> [`27-final-backend-architecture.md`](27-final-backend-architecture.md) 和
> [`31-billing-subrepository-architecture.md`](31-billing-subrepository-architecture.md)。

> 本文只定义仓库和目录迁移；V1 存储以 [ADR-013](../decisions/ADR-013-mysql-mongo-final-storage.md) 为准，旧 PostgreSQL baseline 不再扩展。

历史状态：早期仓库/目录拓扑，不作为当前目标架构。

本文只保留历史仓库类型和迁移细节；当前 Feature-first owner 以 36/38/目标设计卡为准。

本文件解决“每个子仓库复制一份 DDD 四层模板”造成的目录腐化问题。目标不是让所有仓库长得一样，而是让每个仓库的目录能够直接表达：它拥有哪类业务、哪条运行链路、哪些数据、哪些入口，以及哪些内容明确不属于它。

## 1. 先区分四个概念

```text
Repository       代码协作和版本边界
Bounded Context  业务模型和语言边界
Module           一个仓库内部的业务能力边界
Deployment Unit  独立启动、扩缩容和发布的运行边界
```

它们不要求一一对应：

```text
一个 Repository 可以包含多个 Module
一个 Module 可以先和其他 Module 共用一个 Deployment Unit
一个 Bounded Context 未来可以拆成独立 Repository/Deployment Unit
一个技术库不应该伪装成 Bounded Context
```

因此，Kokoro 不使用以下机械规则：

```text
一张表 = 一个仓库
一个仓库 = 一个微服务
每个仓库 = 同一套 domain/application/infrastructure/interfaces 空目录
每个领域对象 = 一个 Entity
```

## 2. 总体拓扑

```text
Kokoro/
├── contract/                 跨仓契约源与生成门禁
├── database/                 物理 MySQL schema、baseline、slice、验证
├── deploy/                   环境部署样例和基础设施声明
├── scripts/                  根级验证、闭环、迁移辅助脚本
├── docs/                     跨仓权威设计和工程规范
├── kokoro-platform/          迁移期历史父仓（不进入最终运行时）
├── kokoro-session/           会话编排与浏览器传输运行时
├── kokoro-agent/             Agent 执行运行时
└── kokoro-web/               用户面和运营面前端
```

根仓只拥有跨仓事实：

- Protobuf/OpenAPI 等公共契约源
- 物理数据库 schema 和 owner inventory
- 版本组合、生成门禁和跨仓验证
- 部署组合和文档入口

根仓不拥有业务 Application Service，不把所有领域实体搬进 `common`，不成为另一个 Platform 父服务。

### 当前实现与目标的关系

当前 `kokoro-platform/kokoro-*` 仍是迁移中的平台模块集合，部分模块使用独立 Prisma/MySQL schema 和独立 HTTP 入口；这属于现有实现事实，不代表目标目录必须继续按当前物理目录复制。

目标架构中的 `database/schema/` MySQL migration/baseline、owner inventory 和跨仓契约是新 SQL-first 后端的统一边界。迁移期间必须同时标注“当前实现”和“目标目录”，通过行为、数据和契约门禁后再删除旧入口，不能只移动文件夹就宣称完成重构。

## 3. 业务后端的默认形态：业务模块优先，层次局部化

业务后端默认采用“feature/module first”，而不是全局技术目录：

```text
src/
├── modules/
│   ├── identity/
│   │   ├── domain/
│   │   ├── application/
│   │   ├── infrastructure/
│   │   └── interfaces/
│   └── organization/
│       ├── domain/
│       ├── application/
│       ├── infrastructure/
│       └── interfaces/
├── shared/                  经过批准的技术/值类型，默认为空
├── generated/               契约或数据库生成物，只读
├── config/
├── bootstrap/
└── main.ts
```

但层次不是强制深度：

### L0 简单模块

```text
modules/model-catalog/
├── model.ts
├── repository.ts
├── service.ts
└── routes.ts
```

### L1 轻量领域模块

```text
modules/capability/
├── domain/
│   ├── skill.ts
│   ├── mcp-server.ts
│   └── repository.ts
├── application/
│   ├── install-skill.ts
│   └── resolve-runtime-snapshot.ts
├── infrastructure/
│   ├── mongo-skill-repository.ts
│   └── package-store.ts
└── interfaces/
    └── http/
```

### L2 标准领域模块

```text
modules/credit/
├── domain/
│   ├── account/
│   │   ├── credit-account.ts
│   │   ├── credit-account-id.ts
│   │   └── credit-account-repository.ts
│   ├── hold/
│   │   ├── credit-hold.ts
│   │   └── hold-policy.ts
│   ├── ledger/
│   │   ├── ledger-entry.ts
│   │   └── ledger-repository.ts
│   └── domain-errors.ts
├── application/
│   ├── quote-credit.ts
│   ├── hold-credit.ts
│   ├── capture-hold.ts
│   └── release-hold.ts
├── infrastructure/
│   └── postgres/
│       ├── credit-account-repository.ts
│       └── credit-transaction.ts
└── interfaces/
    ├── rpc/
    └── http/
```

L2 的目录按真实聚合和用例展开，不能只按术语建空目录。

## 4. 每类仓库的正确结构

### 4.1 IAM：身份与授权领域

IAM 是复杂业务领域，采用 L2，但以业务子域组织，而不是全局 `entities`：

```text
kokoro-iam/
├── src/
│   ├── modules/
│   │   ├── identity/
│   │   │   ├── domain/
│   │   │   ├── application/
│   │   │   ├── infrastructure/
│   │   │   └── interfaces/
│   │   ├── organization/
│   │   ├── authentication/
│   │   ├── authorization/
│   │   └── audit/
│   ├── generated/
│   ├── config/
│   ├── bootstrap/
│   └── main.ts
├── test/
│   ├── unit/
│   ├── integration/
│   └── architecture/
├── docs/
├── package.json
└── tsconfig.json
```

IAM 内部不能让 `identity` 直接修改 `organization` 的 Repository；跨子域操作进入 Application 用例或显式策略。

迁移映射：

```text
旧 kokoro-site + kokoro-user  -> 目标 kokoro-iam
```

Site 是 IAM 的 Site/Realm 子域，不因为存在 `site_*` 表就单独制造一个 Site runtime。只有动态域名运营、Site fleet 或独立生命周期形成真实上下文时，才重新评估拆分。

### 4.2 权益概念：当前不拆独立仓库

当前不建立 `kokoro-entitlement`。套餐、订阅、兑换和购买结果归 Payment；积分授予和账本归 Credit；feature access 由具体业务 owner 的 policy 决定。只有权益规则形成独立高复杂度上下文时，才重新评估拆分。

### 4.3 Payment：支付事实与 provider adapter

```text
kokoro-payment/
└── src/
    ├── modules/
    │   ├── checkout/
    │   ├── order/
    │   ├── provider-event/
    │   ├── subscription/
    │   └── refund/
    ├── providers/
    │   ├── stripe/
    │   ├── alipay/
    │   └── wechat/
    ├── generated/
    ├── config/
    ├── bootstrap/
    └── main.ts
```

Provider adapter 是 Infrastructure，不是 Domain；provider payload 先在边界归一化，领域只接收 `PaymentEvent` 等 Kokoro 术语。

### 4.4 Credit：账本和额度状态

Credit 是最需要 L2 的模块之一：

```text
kokoro-credit/
└── src/
    ├── modules/
    │   ├── account/
    │   ├── quote/
    │   ├── hold/
    │   ├── capture/
    │   ├── release/
    │   ├── ledger/
    │   └── usage/
    ├── infrastructure/mysql/
    ├── interfaces/rpc/
    ├── interfaces/admin/
    ├── config/
    ├── bootstrap/
    └── main.ts
```

`CreditAccount`、`CreditHold` 和 `LedgerEntry` 的关系按事务和不变量设计，不按数据库表逐个生成 Service。

### 4.5 Model：模型目录和路由策略

Model 多数是 L0/L1，不需要完整 DDD：

```text
kokoro-model/
└── src/
    ├── catalog/              Provider / ModelDefinition / Revision
    ├── routing/              Binding / fallback / health projection
    ├── policies/             feature/site visibility
    ├── adapters/             LiteLLM/client boundary
    ├── interfaces/
    ├── generated/
    ├── config/
    └── main.ts
```

只有当 routing policy 形成复杂状态机时，才在 `catalog/` 或 `routing/` 内局部升级为 Domain Model。不能为了“模型领域”复制一套完整 DDD 空结构。

### 4.6 Capability：Skill/MCP 控制面

```text
kokoro-capability/
└── src/
    ├── modules/
    │   ├── skill/
    │   ├── mcp/
    │   ├── installation/
    │   ├── authorization/
    │   └── runtime-snapshot/
    ├── adapters/
    │   ├── package-store/
    │   └── secret-store/
    ├── interfaces/
    ├── config/
    └── main.ts
```

Skill/MCP 的包存储和 secret 存储是适配器；可见性、授权、版本和运行快照才是业务模型。

### 4.7 Storage：文件和产物生命周期

```text
kokoro-storage/
└── src/
    ├── modules/
    │   ├── blob/
    │   ├── upload/
    │   ├── asset/
    │   ├── artifact/
    │   └── scan/
    ├── object-store/          Local/S3 adapter
    ├── scanners/              MIME/virus/content scanner adapter
    ├── interfaces/
    ├── config/
    └── main.ts
```

Local 和 S3 不是两个业务领域，而是同一个 `ObjectStore` 端口的不同实现。

### 4.8 Chat：BFF 内部模块，而不是独立子仓

```text
kokoro-bff/src/modules/chat/
└── src/
    ├── modules/
    │   ├── conversation/
    │   ├── message/
    │   ├── interaction/
    │   └── run-projection/
    ├── interfaces/
    ├── infrastructure/
    ├── generated/
    ├── config/
    └── main.ts
```

Chat 属于 `kokoro-bff` 内部 chat 模块，拥有 BFF 范围内的会话业务事实和投影；Session
仍拥有浏览器传输、relay、SSE 和恢复管道。二者不能因为都有 `session` 或 `run` 字段就
创建独立 Chat/Session 业务仓库。

### 4.9 Session：运行管道架构，不套 DDD

Session 是编排/传输运行时，不适合伪装成 `domain/application/infrastructure`：

```text
kokoro-session/
└── src/
    ├── ingress/               HTTP command admission
    ├── relay/                 agent wire -> session event pipeline
    ├── projection/            snapshot/pending pause projections
    ├── persistence/           Mongo store and sequence ownership
    ├── transport/             Redis live bus and SSE attach
    ├── recovery/              startup/run recovery
    ├── contract/              generated transport types
    ├── config/
    └── main.ts
```

当前 `relay/store/transport/http` 的自然结构方向是正确的；应做的是把 `ingress/projection/recovery` 的职责说清楚，而不是重写成 DDD 四层。

### 4.10 Agent：执行运行时架构，不套 DDD

```text
kokoro-agent/
└── src/kokoro_agent/
    ├── contract/              generated wire types
    ├── worker/                消费、租约、恢复、关停和进程装配
    ├── agents/                preset/factory 与本次 run 装配
    ├── execution/             graph/agent invoke、终态认领、事件发射
    ├── state.py               RunScope、状态和运行上下文
    ├── tools/ skills/ mcp/    授权 capability runtime
    ├── subagents/ sandbox/    委派执行和执行环境
    ├── model/                 model/provider adapter
    ├── storage/               checkpoint、memory、run state
    ├── streams/               request/control/event stream adapter
    ├── prompts/
    └── config.py
```

Agent 的核心抽象是执行阶段、状态、能力装配和事件管道，不是 User/Order/Credit 等业务聚合。
`run/capabilities/providers/persistence` 是跨仓讨论用的语义分组，不要求另建同名目录；现有
`agents/execution/state.py/{tools,skills,mcp,subagents,sandbox}/model/storage` 已是可读的
执行链路。S3Workspace 是 sandbox 的可选 S3-compatible persistence adapter，不属于
Artifact 业务 owner；现有 `execution/hitl/skills/mcp/sandbox/streams/storage` 内容不应被强行搬进 DDD 层。

### 4.11 Platform kit：技术内核，不得成为业务公共层（迁移期说明）

本节只描述历史技术包的迁移边界；最终不保留为独立业务仓库，统一以 `27-final-backend-architecture.md` 的 6.10 节为准。

```text
kokoro-platform-kit/
└── src/
    ├── http/
    ├── config/
    ├── contracts/             仅通用协议工具，不放业务 DTO
    ├── errors/
    ├── security/
    └── index.ts
```

`platform-kit` 不能放 User、Payment、Credit、Model 的业务类型；跨模块共享业务概念必须通过契约或明确的 owner API。

### 4.11.1 LiteLLM：部署接入，不是后端业务子仓

```text
kokoro-litellm/
├── config/
├── scripts/
├── deploy/
└── docs/
```

LiteLLM 负责网关运行和 provider 代理配置；Kokoro 的模型目录、业务可见性、套餐策略和 Credit 结算分别由 Model、Payment、Credit 拥有。`kokoro-litellm` 不创建 Domain/Application 层，也不承载 Kokoro 业务状态。

### 4.12 Platform 父仓：迁移期 legacy，不是最终业务领域

当前 `kokoro-platform` 仅作为迁移期 legacy 保留，不再继续增加新的业务 Service。最终组合、注册、验证和部署职责回收到 Root：

```text
Root/
├── scripts/                  跨仓验证和组合
├── deploy/                   部署样例
├── database/                 数据库工具链
└── docs/                     长期架构和规范
```

如果暂时保留现有 `kokoro-site/`、`kokoro-user/` 等目录，它们只作为迁移源，不再向其中增加新业务能力。平台根的 `src/` 只允许保留临时迁移注册表和验证入口：

```text
platform root src/
├── registry/                 模块清单、owner、运行入口
├── composition/              本地依赖组合
└── validation/               跨模块门禁
```

禁止在平台根出现：

- `src/user-service.ts`、`src/payment-service.ts` 等跨模块业务编排。
- 中央 Prisma client 或中央业务 Repository。
- 各模块共享的业务 DTO、Entity、Policy。
- 以 `platform` 为名的万能业务模块。

## 5. 测试目录必须镜像真实边界

简单模块：

```text
test/
├── unit/
├── integration/
└── architecture/
```

复杂模块按模块镜像：

```text
test/
├── unit/
│   ├── credit-account/
│   └── credit-hold/
├── integration/
│   ├── postgres/
│   └── rpc/
└── architecture/
```

测试不按“所有 service 一堆、所有 repository 一堆”组织；测试目录应让人能看到业务能力和边界。

## 6. 目录反模式清单

以下结构视为架构问题：

```text
src/domain/entities/         所有领域实体的垃圾桶
src/services/                所有业务流程的垃圾桶
src/utils/                   无 owner 的隐藏依赖
src/common/                  不受控的跨域共享
src/types/                   不区分 Domain/DTO/DB/generated
src/infrastructure/          把 ORM、HTTP、provider、缓存全部混在一起
src/generated/               被手工修改或和领域代码混编
src/interfaces/              既处理协议又做业务编排
```

出现 `common`、`shared`、`utils` 时必须在相邻 `INDEX.md` 记录允许的 import 范围和 owner；没有明确范围就不创建。

## 7. 迁移原则

当前旧 Platform 子目录不做“先重命名、后补行为”的大爆炸改造。迁移顺序：

1. 先为每个现有模块写出 owner、use case、数据表和入口清单。
2. 将当前 `domain/application/infrastructure/interfaces` 映射到具体业务模块。
3. 把生成 Prisma 代码移出业务导航面，标记为只读产物。
4. 先补 architecture tests，禁止新代码扩大跨模块依赖。
5. 以一个完整核心用例为单位迁移，而不是一次性搬目录。
6. 通过行为、数据库、契约和集成门禁后，再删除旧入口。

Agent 和 Session 保留当前运行时自然结构，只补职责地图和边界测试，不做形式化 DDD 重排。

## 8. 设计验收标准

一个新子仓库或模块只有同时满足以下条件，目录设计才算通过：

- 从目录能看出业务能力或运行链路。
- 能明确说出唯一数据 owner 和 runtime writer。
- 入口、契约、生成物、基础设施和领域代码可区分。
- 依赖方向可由测试或包边界强制，而不是靠约定记忆。
- 不存在为了模板完整而创建的空目录。
- L0/L1/L2 选择有业务理由。
- 测试目录能对应真实边界。
- 现有行为和迁移路径可验证。
