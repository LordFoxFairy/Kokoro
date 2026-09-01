# 后端子仓库与 DDD 架构规范（历史全局拆仓方案）

状态：**历史全局拆仓方案**，2026-08-22。本文曾把 Conversation/Message 拆为独立 `kokoro-chat`，并把 Capability 设计为 version/snapshot owner；这与当前 Feature-first GA 目标冲突。

当前目标只以 `kokoro-session` 作为产品 Session admission/message/projection/control/SSE/lifecycle owner；GA 作为 AgentState/checkpoint/RunLedger owner；Capability 只管理 user/session Skill path、visibility、CRUD。新设计请先读 [36 GA 整体 Agent 技术方案](36-ga-final-agent-technical-plan.md)、[38 公共运行契约](38-ga-public-runtime-contract.md) 与 [05 Capability 设计卡](backend-design/05-capability.md)。


> 版本说明：本文保留原始 Payment/Credit 拆分阶段的架构原则；Billing 的最新 owner、事务和迁移边界以
> [`27-final-backend-architecture.md`](27-final-backend-architecture.md) 与
> [`31-billing-subrepository-architecture.md`](31-billing-subrepository-architecture.md) 为准。

> 业务边界与 DDD 分级仍有效；其中 PostgreSQL SQL-first 存储方案已由 [ADR-013](../decisions/ADR-013-mysql-mongo-final-storage.md) 取代。V1 结构化业务数据以 MySQL 为准，MongoDB 负责运行时文档与向量。

历史状态：该阶段的拆仓图不再作为目标实现依据。

本文保留后端子仓库划分、目录结构和依赖规则的历史推导；当前实现与目标 owner 以 36/38/设计卡为准。

DDD 采用等级、轻量 DDD 与标准战术 DDD 的区别，以 [25：后端架构与 DDD 采用等级](25-backend-architecture-and-ddd-levels.md)
为准。本文件描述的是共享边界和目标子仓库，不要求所有子仓库复制完整的
`entities/value-objects/services/repositories/events` 目录模板。

当前 Agent、Session、Capability 的目录与 owner 以 36/38/设计卡为准；本文件及 25/26/27 不再互相构成最终准则。

## 1. 统一规则

新建或重构的业务后端子仓库使用相同的四层依赖模型：

```text
src/
├── domain/
├── application/
├── infrastructure/
├── interfaces/
├── generated/
├── bootstrap.ts | bootstrap.py
└── main.ts | main.py
```

```text
Interfaces -> Application -> Domain
Infrastructure -----------> Domain/Application ports
bootstrap/main -----------> all layers
```

禁止反向依赖：

```text
Domain -> Application/Infrastructure/Interfaces
Application -> Infrastructure/Interfaces
Infrastructure -> Interfaces
```

## 2. 目录决策规则

每次新建目录前必须回答：

1. 它是业务模块还是技术分类？
2. 它保护哪个聚合、状态机或事务不变量？
3. 同领域成熟项目如何组织同类能力？
4. 当前是否有足够真实文件，还是只会形成空目录？
5. 拆分后依赖方向是否更明确？
6. 是否符合 TypeScript/Python 的语言与工具链习惯？
7. 是否保留现有成熟行为？
8. 子仓库是否因此更容易独立构建、测试、启动和部署？

复杂业务模块允许：

```text
domain/<module>/
├── entities/
├── value-objects/
├── services/
├── repositories/
└── events/
```

这些目录只在非空且确有导航价值时创建。禁止全局
`domain/entities`、`domain/value-objects` 混放所有模块。

## 3. 子仓库规划

| 子仓库 | 数据前缀 | 业务职责 | DDD 深度 |
|---|---|---|---|
| `kokoro-iam` | `site_*`、`iam_*` | Site、身份、组织、认证、角色、权限、安全审计 | L2 核心领域 |
| `kokoro-chat` | `chat_*` | Conversation、Message、Run 投影、HITL、浏览器事件 | L1 起步，按复杂度升级 |
| `kokoro-agent` | `agent_*` | Run、Manifest、Lease、Control、Usage、恢复 | 保留既有运行时架构 |
| `kokoro-capability` | `capability_*` | Skill、MCP、安装、授权、运行快照 | L1 起步，授权规则局部 L2 |
| `kokoro-model` | `model_*` | Provider、Model Revision、Routing、Health | L0/L1 |
| `kokoro-storage` | `storage_*` | Blob、Upload、Asset、Artifact、Scan | L1 |
| `kokoro-payment` | `payment_*` | 商品、Checkout、Order、Subscription、Provider Event、Refund | L2 核心领域 |

## 4. 子仓库模块

### IAM

```text
Identity / Organization / Authentication / Authorization / Audit
```

详细规则见 [kokoro-iam](../modules/kokoro-iam.md)。

Site 表示产品站点/Realm，不等于 Organization tenant，也不等于可选 Project。一个 Web
代码库可以部署多个套皮/套壳实例；每个实例用服务端 `KOKORO_SITE_ID` 选择 Site，并把该
SiteContext 注入登录和后续 BFF 请求。IAM 不替 Web 选择 Site，只验证 `site_site` 存在、active，
并把 Site 固化到 Principal、Organization、AuthSession 和 JWT 安全链。浏览器提交的 `site_id`
不构成权威。

首发没有独立 Site 服务、端口或 `ResolveSiteByHost` RPC。`site_site` 保留为 PostgreSQL FK 和
生命周期真相；动态 `site_domain`、一套 Web runtime 服务多个 Site、Fleet/品牌发布形成真实
独立能力时再评估 Site runtime。

### Chat

```text
Conversation / Message / Run / Interaction / Stream
```

Conversation 直属 Organization。Project 是后续可选组织能力，不是首链必需轴。

### Agent

```text
Run / Manifest / Lease / Control / ToolEffect / Usage
```

保持现有成熟 GA execution/checkpoint/tool/HITL/runtime 目录与依赖方式，不做 DDD 目录迁移。
本轮只增加或校验 PostgreSQL/RPC adapter、生成契约和部署入口，不改变核心风格。

### Capability

```text
Skill / MCP / RuntimeSnapshot
```

保留 official 与 organization-owned 池、同名覆盖和 secret 同租户解析语义。

### Model

```text
Provider / Definition / Revision / RoutingPolicy / ProviderHealth
```

只负责目录、解析、路由和健康状态；实际 inference 继续通过 LiteLLM/OpenAI-compatible
路径，不自建模型调用网关。

### Storage

```text
Blob / Upload / Asset / Artifact / Scan
```

Local 与 S3 是同一个 ObjectStore port 的 Infrastructure 实现，不是两个业务模块。

### Payment

```text
ProviderAccount / Customer / Checkout / Settlement / Subscription / Reversal
```

Payment 维护商品、订单、订阅和支付事实；购买后的积分授予通过 Credit；当前不建立独立 Entitlement 子仓库。

## 5. 数据与通信

- 一个物理 PostgreSQL 可以承载组合 baseline；每张业务表只有一个 owner 和 runtime writer。
- Root 是唯一物理 DDL authority；子仓库可以拥有 owner-scoped client schema，但不运行
  migration/db push。
- 子仓库之间通过 Root 生成的 RPC 契约通信，不直接写其他 owner 的表。
- 同一子仓库内的强一致业务使用本地事务，不拆成分布式事务。
- Redis 只承担明确的 live queue/fanout/lease 能力，不成为业务长期真相。

## 6. 工程门禁

每个子仓库必须满足：

1. 一个 production entrypoint；
2. 全部 active production source 进入 typecheck/lint/build/test；
3. fresh PostgreSQL integration；
4. RPC caller/contract tests；
5. architecture dependency tests；
6. 本地 `dev` 入口和真实本地进程 smoke；
7. 生成代码 provenance/check；
8. 旧入口仅在行为替代证据通过后删除；
9. 不通过缩小配置范围制造假绿；
10. 能在自己的 Git 根独立开发、验证和部署。

## 7. 当前开发与测试方式

当前阶段先完成本地开发闭环，不以 Docker 为前提：

```text
local PostgreSQL
-> IAM dev
-> Model / Capability dev
-> Agent dev
-> Chat dev
-> Web dev（后接）
```

- TypeScript 子仓提供自己的 `pnpm dev`；Python Agent 保留现有 `uv run` 开发入口。
- 每个进程从本地 `.env.local` 或显式环境变量读取 endpoint、数据库 URL 和测试凭据。
- 单元测试后直接运行本地 PostgreSQL integration 和真实 RPC interoperability。
- 后端闭环先用测试客户端验证，不等待 Web，也不等待容器镜像。
- Dockerfile、Compose、镜像安全和容器网络在本地闭环稳定后单独设计和验收。
