# 后端子仓库与 DDD 架构规范

状态：目标架构已对齐，实施中。

本文件是后端子仓库划分、目录结构和依赖规则的正式入口。当前运行时事实仍以对应子仓
README 和已通过的门禁为准；迁移完成后再删除旧入口。

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
| `kokoro-iam` | `site_*`、`iam_*` | Site、身份、组织、认证、角色、权限、安全审计 | 完整 DDD |
| `kokoro-chat` | `chat_*` | Conversation、Message、Run 投影、HITL、浏览器事件 | 完整 DDD |
| `kokoro-agent` | `agent_*` | Run、Manifest、Lease、Control、Usage、恢复 | 保留既有运行时架构 |
| `kokoro-capability` | `capability_*` | Skill、MCP、安装、授权、运行快照 | 完整 DDD |
| `kokoro-model` | `model_*` | Provider、Model Revision、Routing、Health | 轻量 DDD |
| `kokoro-storage` | `storage_*` | Blob、Upload、Asset、Artifact、Scan | 完整 DDD |
| `kokoro-entitlement` | `entitlement_*` | Offer、卡密、权益、订阅期限、积分、用量结算 | 完整 DDD |
| `kokoro-payment` | `payment_*` | 支付账户、Checkout、Settlement、Subscription、Reversal | 完整 DDD |

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

### Entitlement

```text
Catalog / Redemption / Entitlement / Subscription / Credit / UsageSettlement
```

它拥有套餐、卡密、权益和积分真相，不使用含糊的 `kokoro-commerce` 名称。

### Payment

```text
ProviderAccount / Customer / Checkout / Settlement / Subscription / Reversal
```

Payment 只维护支付事实；权益是否生效由 Entitlement 决定。

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
