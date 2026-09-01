# API、RPC 与错误契约规范

状态：正式规范，2026-08-21

## 1. 契约优先

- 跨仓协议由 Root `contract/` 维护，生成客户端/服务端代码。
- 业务模块内部可以使用本地类型，但跨边界必须经过明确 schema。
- 生成代码不得手工修改；修改源 `.proto`、OpenAPI 或 schema 后重新生成并验证 provenance。
- 契约命名使用业务语言，不使用数据库表名或内部 ORM 类型作为公共协议。

首发版本规则：Kokoro 尚未对外上线时，公共 HTTP/API surface 与内部 RPC 统一使用 `v1`；版本只存在于 API、DTO、protobuf package 和 generated client 层。领域对象、application service、repository、数据库表和 Redis key 不复制版本。只有不兼容的 wire、DTO、错误或授权语义变化才创建 `v2`。Capability × Storage 的具体边界见 [v1 API 与 Client 契约](../technical/52-capability-storage-v1-api-and-client-contract.md)。

## 2. Interface 层职责

Interface 只做：

- 认证上下文解析
- 输入 schema 校验
- 外部字段到 Command/Query 的转换
- 调用 Application use case
- 内部错误到公共错误契约的映射

Interface 不做：

- 直接写数据库
- 组织跨模块业务流程
- 直接返回 ORM entity
- 把任意用户字段透传给 SQL、排序或 provider

## 3. Command 与 Query

写操作使用 Command，读操作使用 Query：

```text
CreateIdentityCommand
ReserveCreditCommand
GetIdentityQuery
ListModelBindingsQuery
```

规则：

- Command 表达一次业务意图，不设计成任意字段的万能 PATCH。
- Query 返回专用 read model 或 response DTO，不强迫经过完整聚合。
- 写入返回稳定的资源标识、状态和必要版本，不返回数据库行的全部字段。
- 领域实体、数据库记录和公共 Response DTO 不复用同一类型。

## 4. 错误模型

公共错误至少包含：

```text
code       稳定机器可读码
message    面向调用方的简短说明
request_id 关联本次请求
details    经过 schema 约束的结构化细节，可选
```

错误分类：

```text
validation         输入不合法
authentication     未认证
authorization      无权执行
not_found          资源不存在或不可见
conflict           版本、唯一性或状态冲突
rate_limited       当前阶段只保留协议码，不建设完整限流平台
dependency         外部依赖失败
internal           未分类内部错误
```

规则：

- 不把数据库异常、堆栈、SQL、provider secret 返回给调用方。
- 不用 HTTP status 或 gRPC status 单独表达业务语义；业务 code 必须稳定。
- 不把“资源不存在”和“资源存在但无权访问”自动合并成会泄露信息的错误。
- 客户端可依赖 code，不依赖 message 文案。

## 5. RPC 基础规则

- 每个 command 明确 `request_id` 或 `command_id`，需要幂等时由 owner 持久化。
- RPC caller 必须设置超时，不使用无限等待。
- 只有幂等读和明确幂等写才允许自动重试。
- 重试必须能区分业务拒绝、瞬时依赖失败和永久参数错误。
- 跨仓请求携带经过上游解析的 SiteContext/PrincipalContext，不自行重新解释身份轴。
- 不能把 `userId`、`ownerId`、`workspaceId` 作为 GA 的第二隔离轴；GA 只消费 opaque `namespace`。

### 5.1 Client facade

跨仓消费者必须通过 owner 提供的 typed client facade：facade 负责输入校验、generated v1 request 构造、deadline、幂等重试、response allow-list mapping 和稳定错误映射。消费者不得直接导入 generated message、ORM entity、数据库 client、Redis key 或 provider SDK。共享 transport channel 不构成共享业务 owner。
