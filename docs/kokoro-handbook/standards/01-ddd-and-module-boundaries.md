# DDD 与模块边界规范

状态：概念补充，2026-09-04

> 物理目录、命名与语言实践以
> [TypeScript 后端成熟工程规范](08-typescript-backend-engineering.md) 和
> [Python 后端成熟工程规范](09-python-backend-engineering.md) 为准。本文件中的分层图只表达概念依赖，
> 不要求顶层四层或 `ports/` 目录。

本规范定义什么时候使用 DDD、如何划分 Module，以及如何证明边界成立。DDD 是解决业务复杂度的工具，不是目录装饰。

## 1. 先划边界，再选架构

每个模块在评审时必须写清楚：

- 业务语言和核心用例；
- owns / does not own；
- 数据表和唯一 runtime writer；
- 对外命令、查询和事件；
- 必须保持的不变量；
- 允许依赖和明确禁止依赖；
- 当前实现、目标结构和迁移退出条件。

Repository、Bounded Context、Module、Deployment Unit 可以暂时一一对应，但不能把部署拓扑当成业务边界的证明。

## 2. L0 / L1 / L2 选择

| 等级 | 适用情况                                     | 必需内容                                                               | 禁止内容                         |
| ---- | -------------------------------------------- | ---------------------------------------------------------------------- | -------------------------------- |
| L0   | 目录、配置、简单后台资源、无复杂状态 CRUD    | 业务边界、必要的 schema/用例/数据访问与测试                            | 空 Aggregate/Entity/Domain Event |
| L1   | 有稳定业务规则但状态机有限                   | module 边界、Policy、用例/Service、Repository、规则测试                | 为形式完整而拆无意义子域         |
| L2   | 余额、支付、身份权限、复杂状态机和并发不变量 | 显式不变量、事务/幂等与并发测试；Aggregate/Value Object 按建模收益选择 | 用 ORM CRUD 代替业务模型         |

执行引擎不强行套 L0/L1/L2；分类帮助讨论复杂度，不驱动批量生成目录。

## 3. 依赖规则

```text
HTTP/RPC/worker -> Service/use case -> 业务规则
Repository/client/cache -> 消费方声明的最小依赖 shape
app/bootstrap -> concrete implementations 与资源生命周期
```

- 业务规则不依赖 ORM、HTTP、RPC、provider SDK 或配置框架。
- 模块之间只依赖公开 contract、命令、查询或 projection。
- 不导入其他模块的内部 Model、Repository 实现或数据库表。
- 共享包只能提供稳定的技术能力，不能承载业务 DTO、Policy 或 Repository。

## 4. 验收证据

设计卡必须同时覆盖边界、数据 owner、复杂度选择、目录、依赖、契约和测试七项；实现阶段必须由 architecture test、schema owner inventory、contract test 和集成测试提供证据。
