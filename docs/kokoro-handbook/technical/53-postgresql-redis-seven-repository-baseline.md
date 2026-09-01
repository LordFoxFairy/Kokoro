# Goal 2：七个正式子仓库的 PostgreSQL + Redis 技术基线

## 1. 数据分层

| 层 | PostgreSQL | Redis | ObjectStore |
|---|---|---|---|
| IAM | 用户、Tenant、组织、Role、Permission、审计、receipt | session/cache、短租约、幂等快速路径 | — |
| System | Site、Workspace、Manifest、策略、配置 release | cache/coordination | — |
| Model | catalog、provider、availability、能力契约 | catalog cache、刷新协调 | — |
| Billing | payment、subscription、checkout、refund、credit、ledger、receipt | hold/lease、幂等和 worker coordination | — |
| Capability | skill、MCP connector/server/tool catalog、安装状态、版本、权限 | install lock、outbox/短期 coordination | 可选引用，不保存字节 |
| Storage | file、upload、artifact、scan、生命周期元数据 | upload/scan coordination | blob bytes、presigned transfer |
| Scheduler | v1 配置驱动；未来 durable registry 自有 schema | occurrence lease | — |

## 2. 跨仓规则

- 每个仓库只访问自己的 PostgreSQL schema；服务间使用 API/RPC 和可信 service context。
- `request_id` 贯穿请求/事件/receipt；写操作使用 `Idempotency-Key`。
- cursor 分页只暴露 opaque cursor，不把数据库 offset 暴露为公开契约。
- 统一响应 envelope 的 wire 版本由根仓 contract/定义，错误码包含 machine-readable code、
  request_id、retryable 和 details。
- Storage 的业务仓只保存 `storage_ref`/artifact metadata，不复制对象存储字节；
  Capability 的 MCP Connector 是 MCP 子域的 connector/adapter，不创建独立顶层业务仓。
- Scheduler 只触发业务 command；Billing、Credit、Capability 等任务定义和业务状态由
  对应业务仓拥有。

## 3. 迁移与运行要求

每个目标仓应提供 PostgreSQL migration、schema contract test、Mock/Fixture、失败恢复
测试、独立运行说明、BFF 接入说明、验收命令和风险清单。Redis 只作为可恢复的协调层；
数据库事务提交前不得把 Redis 状态当作业务成功。Storage 生产环境必须使用
S3-compatible ObjectStore，local profile 才允许安全的本地替身。
