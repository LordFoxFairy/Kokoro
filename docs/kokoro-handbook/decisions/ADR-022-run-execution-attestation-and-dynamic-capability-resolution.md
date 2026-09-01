# ADR-022 ExecutionIdentity 与动态能力边界

状态：已采纳，2026-08-27。实现以 [42 GA 核心架构](../technical/42-ga-core-architecture.md) 与
[38 GA 公共运行契约](../technical/38-ga-public-runtime-contract.md) 为准。

## 决策

外部只提交服务端构造的：

```text
feature_key
ExecutionIdentity(tenant_ref, actor, subject, identity_assertion_ref)
input(message_id, content)
```

GA 从 `ExecutionIdentity` 派生私有 `RuntimeNamespace`；caller 不能选择 namespace、thread、Agent、Skill、MCP、sandbox 或 graph。

Feature/Agent 的默认能力由 GA 内置声明决定。用户、项目和 Session Skill/MCP 的 CRUD 与路径来自
Capability public contract；包体和 Artifact 来自 Storage public contract。GA 在实际调用边界重新校验 owner
授权，只把本次允许的能力装配到当前 DeepAgent，不把 CapabilitySnapshot 或凭据写入 checkpoint。

计费归属使用 `ExecutionIdentity.subject` 与稳定 `invocation_id`；RuntimeNamespace 只用于 GA 隔离，
不参与扣费或反向查账户。
