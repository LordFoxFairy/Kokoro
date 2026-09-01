# 后端架构与 DDD 采用等级（历史全局拆仓方案）

状态：**历史全局拆仓方案**，2026-08-22。本文的 DDD 分级讨论可作一般工程参考，但其 `kokoro-chat` 独立 owner、Capability version/snapshot 及旧 SQL-first 拆仓结论不作为当前 Agent/Session 实现依据。

当前 Feature-first 运行链路以产品 Session + GA 为两个 runtime owner：见 [36 GA 整体 Agent 技术方案](36-ga-final-agent-technical-plan.md)、[38 公共运行契约](38-ga-public-runtime-contract.md) 和 [Session 生命周期](../business-flows/session-lifecycle.md)。


> 本文只定义业务边界与 DDD 分级；存储选型以 [ADR-013](../decisions/ADR-013-mysql-mongo-final-storage.md) 为准，不新增 PostgreSQL。

历史状态：通用 DDD 分级参考，非当前 Agent/Session/Capability 目标规范。

本文件解决一个容易被混淆的问题：Kokoro 不把“DDD”当作固定目录模板，也不要求每个后端模块都使用完整战术 DDD。DDD 的采用等级必须由业务复杂度、业务不变量、团队边界和数据一致性需求决定。

## 1. 术语结论

DDD 不是一种部署架构，也不是 `domain/application/infrastructure/interfaces` 目录模板。它是以领域模型和领域语言为中心的分析、设计与实现方法。

DDD 有两个层面：

```text
战略设计：领域、子域、限界上下文、上下文映射、团队与系统边界
战术设计：实体、值对象、聚合、领域服务、领域事件、仓储、工厂
```

分层、六边形、整洁架构、模块化单体和微服务都是承载这些设计的架构选择，不是 DDD 本身。分层是控制依赖和复杂度的逻辑结构，不等于必须拆成多个进程。

“轻量 DDD / DDD Lite”不是 DDD 官方标准术语。在工程实践中，本规范将它定义为：

> 使用战略 DDD 划分业务模块，并使用简化的领域分层和 Repository 边界；不强制为每个模块建立完整聚合、值对象、领域事件和领域服务体系。

轻量 DDD 不是“少建几个目录”，也不是把传统三层架构改名。它至少必须保留业务模块边界、领域语言、依赖方向和数据写入者边界。

## 2. Kokoro 采用三档模型

### L0：事务脚本 / CRUD 模块

适用于没有复杂业务规则的数据能力：配置、只读目录、简单后台管理和低状态 CRUD。

```text
module/
├── interfaces/
├── application/
├── infrastructure/
└── model-or-schema/
```

规则：

- 可以使用简单 Application Service 编排一次数据库操作。
- 不为了形式创建 Entity、Aggregate、Value Object、Domain Event 目录。
- 仍然必须遵守模块边界、输入校验、事务边界和 Repository/SQL 访问规则。
- L0 不是全局的 `controller/service/dao` 技术分层；代码仍以业务模块为第一层组织。

### L1：轻量 DDD / 领域模块化架构

这是 Kokoro 的默认方案。

```text
module/
├── interfaces/
├── application/
├── domain/
└── infrastructure/
```

推荐的最小形态：

```text
domain/
├── user.ts
├── user-policy.ts
└── user-repository.ts
```

规则：

- 先按业务模块组织，再按技术层组织。
- Application Service 负责用例流程、授权前置检查、事务协调和端口调用。
- Domain 保存可复用的业务规则、状态转换和领域概念。
- Infrastructure 实现数据库、RPC、第三方 SDK 和文件存储适配器。
- Interfaces 只负责 HTTP/RPC/worker 协议转换，不直接编排业务。
- 可以使用普通领域对象和少量行为方法，不要求所有数据都建成充血聚合。
- Repository 接口可以放在 domain；简单模块也可以放在 application，关键是实现依赖不能反向泄漏。
- 不跨模块读取或写入其他模块的表。

L1 的目标是让业务边界清楚、修改范围可控，而不是模拟一本 DDD 术语词典。

### L2：标准战术 DDD

只用于复杂核心领域：

- IAM / Authorization
- Credit / Ledger
- Payment / Settlement
- Payment / Subscription
- 复杂的 Agent Run 状态和资源租约

典型结构：

```text
module/
├── interfaces/
├── application/
│   ├── commands/
│   ├── queries/
│   └── handlers/
├── domain/
│   ├── aggregates/
│   ├── entities/
│   ├── value-objects/
│   ├── domain-services/
│   ├── repositories/
│   └── events/
└── infrastructure/
```

启用 L2 必须能回答：

1. 哪些规则是领域不变量？
2. 哪个聚合根负责保护这些不变量？
3. 哪些状态变化必须在同一事务内完成？
4. 哪些概念不是普通字符串、数字或数据库行，而是有业务语义的值对象？
5. 哪些事件是领域事实，哪些只是应用层副作用？

如果这些问题答不出来，只建立完整 DDD 目录，不得称为 L2。

## 3. 传统三层、L1 和 L2 的边界

```text
传统三层：技术分层优先，Service 容易成为业务逻辑垃圾桶
L1：业务模块优先，简化分层，业务规则按稳定性放入领域对象或应用服务
L2：限界上下文和聚合优先，领域模型保护核心不变量，应用层保持薄
```

L1 允许 Application Service 中存在业务流程，但以下规则不能只存在于 Controller 或散落在多个 Service 中：

- 状态机合法转换
- 权限和所有权不变量
- 金额、积分、余额不可透支规则
- 幂等命令的语义
- 订阅、支付、权益生效条件
- 聚合内部对象之间的一致性规则

这些规则应进入 Domain 对象、Domain Policy 或 L2 Aggregate。

## 4. Kokoro 的架构落点

### 子仓库边界

子仓库按业务能力和唯一写入者划分，而不是按 Controller、数据库表或第三方技术划分。一个业务子仓库可以包含多个内部模块，但每张业务表只能有一个 runtime writer。

```text
kokoro-iam          L2
kokoro-chat         L1 起步，复杂会话规则再局部升级 L2
kokoro-agent        保留 execution/runtime 自然结构，不套 DDD 模板
kokoro-capability   L1 起步，授权和运行快照按需升级
kokoro-model        L0/L1
kokoro-storage      L1
kokoro-payment      L2
```

这里的等级是默认起点，不是永久标签。一个子仓库内部可以按模块分别采用 L0、L1、L2。

### 依赖方向

```text
interfaces -> application -> domain
infrastructure -> domain/application contracts
bootstrap/main -> all concrete implementations
```

禁止：

- Domain 依赖 ORM、HTTP、RPC、消息客户端或具体数据库。
- Application 直接 `new` 具体 Infrastructure 实现。
- Interfaces 直接写数据库或调用别的模块 Repository。
- 一个领域模块导入另一个领域模块的持久化 Model。
- 通过公共 `common` 包共享所有领域实体，形成跨域垃圾桶。

## 5. 目录设计规则

目录必须表达业务导航价值。新增目录前回答：

1. 它属于哪个业务模块？
2. 它保护哪个业务不变量或用例边界？
3. 不建立它会产生什么真实混乱？
4. 是否已经有足够的真实代码支撑它？
5. 它是否会改变依赖方向或数据所有权？

禁止：

- 全局 `domain/entities`、`domain/services`、`domain/events` 垃圾桶。
- 为了看起来像 DDD 而创建空的六层目录。
- 以 ORM Model 直接冒充领域实体。
- 让所有模块都复制同一份模板。

允许：

- 简单模块在 `domain/` 内平铺文件。
- 复杂模块按聚合或子领域进一步分目录。
- Agent 等运行时系统采用自己的职责链和执行模型。

## 6. 当前范围与明确不做

当前后端架构规范只覆盖：

- 业务边界和子仓库所有权
- L0/L1/L2 DDD 采用规则
- 目录和依赖方向
- Application、Domain、Infrastructure、Interfaces 职责
- MySQL schema 与 owner 边界
- Repository、事务、幂等和迁移基础规则
- API/RPC 契约和测试门禁

当前不建设完整的：

- SRE 体系、SLO/SLI
- 分布式追踪平台
- 熔断降级平台
- 多活、灾备和容量治理
- Outbox/Inbox 通用框架
- CQRS/Event Sourcing 基础设施
- 复杂事件总线治理

这些能力只有在对应业务复杂度或部署规模出现时，按具体场景引入。

## 7. 调研依据

- [Microsoft：Use Domain Analysis to Model Microservices](https://learn.microsoft.com/en-us/azure/architecture/microservices/model/domain-analysis)：战略 DDD、限界上下文和按业务能力划分边界。
- [Microsoft：Use Tactical DDD to Design Microservices](https://learn.microsoft.com/en-us/azure/architecture/microservices/model/tactical-ddd)：实体、聚合和战术设计的适用关系。
- [Microsoft：Designing a DDD-oriented microservice](https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/ddd-oriented-microservice)：应用层保持薄、领域模型隔离基础设施。
- [Microsoft .NET eShop reference architecture](https://github.com/dotnet/docs/blob/main/docs/architecture/cloud-native/introduce-eshoponcontainers-reference-app.md)：不同微服务可以按复杂度采用 CRUD 或 DDD，而不是一刀切。
- [Alibaba P3C](https://github.com/alibaba/p3c)：工程门禁、数据库命名、SQL、输入校验和代码审查规则的实践参考。
- [Google Engineering Practices](https://google.github.io/eng-practices/review/reviewer/standard.html)：代码评审以持续改善代码健康度为目标，而不是追求形式统一。
