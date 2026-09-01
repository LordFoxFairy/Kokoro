# 后端目录与依赖规范

状态：正式规范，2026-08-21

目录必须反映业务边界和运行链路，不按“公司统一模板”制造空目录。

## 1. 业务服务默认结构

```text
src/
├── modules/<business-module>/
│   ├── domain/          仅在存在稳定领域规则时创建
│   ├── application/     用例、事务和跨 adapter 编排
│   ├── infrastructure/  数据库与外部系统适配器
│   └── interfaces/      HTTP/RPC/worker 入口
├── generated/           只读生成产物
├── config/
├── bootstrap/
└── main.ts
```

简单模块可以使用 `model.ts`、`repository.ts`、`service.ts`、`routes.ts` 的浅结构；复杂模块按业务子模块展开，不把所有文件集中到全局 `services/`、`repositories/` 或 `utils/`。

## 2. 运行时服务结构

```text
Session: ingress -> relay/projection -> persistence/transport -> recovery
Agent:   worker -> run/execution -> capabilities/providers/persistence/streams
```

运行时服务按消息、状态和副作用链路组织；它们不因为存在数据库就强行创建业务 Domain 层。

## 3. 入口和副作用

- `main/bootstrap` 负责依赖注入和进程启动，不承载业务判断。
- `interfaces` 负责输入校验、上下文解析、DTO 转换和错误映射。
- `application` 负责用例和本地事务边界。
- `infrastructure` 负责具体数据库、队列、对象存储和 provider adapter。
- 生产入口必须唯一；测试入口必须明确标注，不得通过隐藏 import 绕过正式入口。

## 4. 依赖门禁

架构测试必须能阻止：

- domain import infrastructure/interfaces；
- interface 直接写数据库；
- 模块导入其他模块持久化实现；
- generated 文件被手工修改；
- Root 反向成为业务 service；
- legacy platform 重新获得业务写面。

目录评审必须结合 import 图、contract consumer、schema owner 和测试入口，不接受只看文件夹名称的“架构证明”。
