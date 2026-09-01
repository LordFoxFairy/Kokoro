# ADR-028：正式子仓库采用 PostgreSQL + Redis 基线

- 状态：Accepted
- 日期：2026-09-01
- 范围：Goal 2 的 kokoro-iam、kokoro-system、kokoro-model、kokoro-billing、kokoro-capability、kokoro-storage、kokoro-scheduler

## 决策

正式业务子仓库统一以 PostgreSQL 保存业务事实，以 Redis 提供缓存、短期协调、租约和
幂等快速路径。业务正确性、状态机、账务、权限、资源元数据和 command receipt 均必须
落在 PostgreSQL 事务边界内。Redis 故障时由各仓按契约选择 fail-closed 或降级；Redis
不能成为业务事实的唯一来源。

Storage 的对象字节使用 S3-compatible ObjectStore（生产为外部对象存储，开发可用
MinIO/local fixture）；PostgreSQL 只保存 object key、digest、size、scan、artifact
和生命周期元数据。

Scheduler v1 使用 Go 和部署注入的 ScheduleJob 配置，Redis 只做多实例 occurrence
lease；业务执行 receipt 由目标业务仓写入自己的 PostgreSQL。未来引入持久化调度注册表
时，Scheduler 自己拥有 PostgreSQL schema，不读取任何业务数据库。

`kokoro-session` 当前属于本阶段明确排除的仓库；其 MongoDB 迁移另行立项，不作为 Goal 2
的完成条件，也不影响七个目标仓的基线一致性。

## 约束

1. 新增目标仓代码、迁移、fixture、环境变量和文档不得以 MySQL/MariaDB 或 MongoDB
   作为当前运行时依赖。
2. 每个仓库拥有自己的 PostgreSQL schema/migration，不跨仓读取数据库。
3. BFF 仅通过公开 API/RPC 接入；Agent 仅执行；IAM 输出可信 ExecutionIdentity；
   Billing 内含 Credit；Capability 内含 Skill + MCP/Connector；Storage 拥有对象元数据；
   Scheduler 不包含业务逻辑。
4. wire contract 仍由根仓 `contract/` 权威文件定义，各子仓 API_CONTRACT/docs 说明
   本仓实现细节。

## 验收

七个目标仓分别执行自己的 lint、typecheck、test、build、启动检查，并使用 Mock/Fixture
完成跨仓契约联调。验收报告必须列出真实 PostgreSQL/Redis smoke 的执行情况和剩余风险。
