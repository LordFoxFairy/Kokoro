# `kokoro-system` 业务边界设计卡

## 定位

按 [ADR-031](../../decisions/ADR-031-system-http-nestjs-convergence.md)，System 是五个业务模块的 owner：
Sites、Workspaces、Products、Runtime Manifest、Model Catalog。配置按所属业务能力放置，不建通用 key/value 模块。
Release/Binding 属 Products 生命周期，不是独立一级模块。Workspace 不是 IAM Organization 或 BFF Project。

## 数据与依赖边界

- PostgreSQL SQL-first canonical schema 是唯一持久化事实；Redis 仅缓存和协调，使用 global/tenant generation fence。
- IAM 拥有身份/权限；System 验证服务凭据与可信上下文，并在自己的 Site/Host/Policy 中完成准入。
- Model Catalog 管理 provider metadata、definition、不可变 revision、label、tenant policy、health 和路由；不执行推理或保存 provider 明文凭据。
- 不拥有 Chat/Project、Billing ledger、Platform Skills/MCP、Storage bytes 或 Agent Run。
- 旧 Model checkout 仅保留历史，活动服务身份不再独立部署；Capability→Platform 的另一 cutover 不在本卡实施。

## 契约与验收

单一 Nest HTTP `/v1/system/*`，运行时 schema 单向生成 OpenAPI；删除旧 Proto/SDK/双协议路径。
接口与数据事实源只在 [System 技术方案](../../../../kokoro-system/docs/TECHNICAL_DESIGN.md)、
[API 契约](../../../../kokoro-system/docs/API_CONTRACT.md)、[数据模型](../../../../kokoro-system/docs/DATA_MODEL.md)。
真实实现、测试与未完成项看 [System CURRENT](../../../../kokoro-system/docs/CURRENT.md)，本卡不是验收报告。
Root 用独立随机数据库/缓存前缀，验证 System HTTP → BFF manifest/catalog 与 Agent resolve；不跨仓读写业务表。
