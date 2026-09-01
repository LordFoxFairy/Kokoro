# ADR-012：后端子仓库与 DDD 分层规范（历史全局拆仓决策）

状态：**历史全局拆仓决策**，2026-08-22。本文的通用目录/依赖原则可作考古；其中 `kokoro-chat` 独立会话 owner 与旧存储拆分不覆盖当前 Feature-first GA target。

当前 Agent/Session/Capability owner 以 [ADR-015](ADR-015-agent-state-and-feature-context.md)、[36 GA 整体 Agent 技术方案](../technical/36-ga-final-agent-technical-plan.md) 和 [38 公共运行契约](../technical/38-ga-public-runtime-contract.md) 为准。


> 本 ADR 的仓库边界、模块化和 DDD 分级继续有效；其中 PostgreSQL baseline 与 SQL-first 存储决策已由 [ADR-013](ADR-013-mysql-mongo-final-storage.md) 取代。

- 历史状态：已接受于旧全局拆仓阶段；当前 Agent/Session/Capability owner 以 ADR-015 与 36/38 为准。
- 日期：2026-08-14
- 适用范围：Kokoro 业务后端子仓库

## 背景

旧 Platform 父仓、按部署便利划分的模块，以及新旧 HTTP/RPC、MySQL/PostgreSQL
实现并存，导致业务所有权、运行入口和测试范围不一致。仅复制某种 DDD 目录模板也不能解决
这些问题；目录必须由业务边界、聚合、事务和依赖方向推导。

## 决策

1. 一个业务子仓库对应一个明确业务能力区和唯一数据写入者。Site 不单独制造子仓库：每个
   Web 套壳部署通过服务端 env 选择自己的 `site_id`，IAM 只验证 Site 和安全绑定；动态
   Site/Domain 运营能力出现前不建立独立 Site runtime。
2. 每个业务子仓库内部统一使用 `domain / application / infrastructure / interfaces`
   四层依赖模型。
3. 复杂子仓库先按业务模块划分；`entities / value-objects / services /
   repositories / events` 只能位于具体业务模块内部。
4. 简单子仓库不创建空目录或单文件模板目录，可以在对应层内平铺。
5. Domain 不依赖框架；Application 编排用例和事务；Infrastructure 实现持久化及外部
   能力；Interfaces 只负责 RPC/HTTP/worker 协议转换。
6. `bootstrap` 或 `main` 是唯一 composition root；不允许同一子仓库存在两套业务入口。
7. Root 仓库负责 Protobuf/OpenAPI、物理 PostgreSQL baseline、owner inventory、版本组合与
   E2E，不承载业务编排。
8. 生成文件是契约产物，不属于业务层；子仓库不得手工修改。
9. 成熟 `kokoro-agent` 保留现有运行时架构，不参与本轮 DDD 目录重排；只校验服务边界和
   契约适配。
10. 目录设计必须同时通过同领域成熟项目对照、现有行为保留审计和全量工程门禁，不以
   “看起来像 DDD”作为接受依据。
11. 当前开发阶段使用各子仓库本地 `dev` 入口和本地 PostgreSQL 完成真实闭环；Docker、
    Compose 和镜像门禁属于后续交付阶段，不作为目录与业务能力对齐的前置条件。

## 子仓库

首批目标业务子仓库：

```text
kokoro-iam
kokoro-chat
kokoro-agent
kokoro-capability
kokoro-model
kokoro-storage
kokoro-entitlement
kokoro-payment
```

`kokoro-agent` 保持既有 runtime 结构；`kokoro-web` 使用前端 feature/BFF 结构；Root 使用
contract/database/deploy/scripts/docs 治理结构。三者不为形式统一而重排成业务 DDD 模板。

## 不采用的方案

### 单一 Platform 父服务承载全部业务

拒绝。它让独立业务写入者、部署边界和事务边界混在一起。

### 所有领域对象放入全局 `domain/entities`

拒绝。它按技术类型而不是业务能力聚合，最终形成跨模块垃圾桶。

### 所有子仓库复制相同深度的空目录

拒绝。四层依赖必须一致，但目录深度由真实模型数量和复杂度决定。

### 为统一目录重写成熟 Agent/GA 内核

拒绝。Agent 保留成熟 execution/checkpoint/stream/tool/runtime 自然结构，只通过窄契约和
adapter 接入新的 PostgreSQL/RPC 边界。

## 后果

- 子仓库边界和依赖方向更容易通过架构测试强制。
- 复杂领域会增加必要目录层级，但这些目录必须有真实模型和行为支撑。
- 旧代码只有在行为替代、数据库/RPC 集成和全量门禁通过后才删除。
- 目标架构和当前运行时在迁移期必须明确区分，不把规划写成已落地事实。
- 先保证本地进程可运行、可调试、可集成，再增加容器包装，避免部署细节反向主导业务架构。
