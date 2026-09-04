# 后端目录与依赖规范

状态：概念补充，2026-09-04

> **已被语言手册细化**：TypeScript/Python 不再按本文件示例机械创建模块内四层；分别使用
> [TypeScript 后端成熟工程规范](08-typescript-backend-engineering.md) 与
> [Python 后端成熟工程规范](09-python-backend-engineering.md)。本文件继续约束业务 owner、入口、副作用和
> import 边界。

目录必须反映业务边界和运行链路，不按“公司统一模板”制造空目录。

## 1. 业务服务默认结构

```text
src/
├── modules/<business-module>/      # TypeScript；Python 直接使用业务 package
│   ├── <subject>.schema.ts         # 有 transport 边界时
│   ├── <subject>.service.ts        # 用例、事务和业务编排
│   ├── <subject>.repository.ts     # 有持久化时
│   └── <subject>.routes.ts         # 有 HTTP 时
├── generated/           只读生成产物
├── config/
├── app.ts               应用装配，不监听端口
└── server.ts            进程入口
```

上图是 TypeScript 的浅层示意，不是必建文件清单；Python 的真实结构见 09 手册。复杂模块先按子业务展开，
确有复杂不变量时才在该模块内部增加 `domain/` 或 `use-cases/`。不要把所有文件集中到全局 `services/`、
`repositories/`、`utils/`，也不要按 PostgreSQL/Redis/ORM 品牌建立业务目录。

## 2. 运行时服务结构

```text
BFF:   request/event ingress -> conversation/projection -> data access -> replay
Agent: worker -> runs/execution -> tools/skills/mcp -> records/events
```

运行时服务按消息、状态和副作用链路组织；它们不因为存在数据库就强行创建业务 Domain 层。

## 3. 入口和副作用

- `app/bootstrap` 负责依赖装配和资源生命周期，不承载业务判断；进程入口只负责 listen/signal/shutdown。
- route/connect/consumer 负责输入校验、上下文解析、DTO 转换和错误映射。
- service/use case 负责用例、授权入口和本地事务边界。
- repository/client/cache/publisher 负责数据库、外部服务、缓存和消息 I/O。
- 每个进程有唯一明确入口；同仓多个进程按语言手册组织，不通过隐藏 import 启动运行时。

## 4. 依赖门禁

架构测试必须能阻止：

- 业务规则 import Fastify/ORM/database/Redis/provider SDK；
- route/connect/consumer 直接写数据库；
- 模块导入其他模块持久化实现；
- generated 文件被手工修改；
- Root 反向成为业务 service；
- legacy platform 重新获得业务写面。

目录评审必须结合 import 图、contract consumer、schema owner 和测试入口，不接受只看文件夹名称的“架构证明”。
