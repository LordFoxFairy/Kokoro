# Kokoro Tenant、System 与 User Web 架构技术方案 v2

状态：当前有效方案，2026-08-22。

> 本文 supersede `30-kokoro-system-and-iam-tenant-architecture.md` 中将 `site_id` 与 `tenant_id` 并列为隔离键的表述。

## 1. 统一命名决定

```text
tenant_id
  唯一的身份、权限和业务数据隔离键；对外跨仓契约使用这个标识。

site / site_id
  产品、品牌、域名和展示语义；由 System 内部管理。每个 tenant 必须绑定一个有效 site，
  但 site_id 不作为对外授权选择，也不建立第二套业务隔离轴。

namespace
  GA 的 opaque 执行隔离键。它只在 GA 首次 target bootstrap（普通 Launch claim 或 fork `ForkConversation` prepare） 时由可信
  tenant_ref + execution subject 派生；不拼接 tenant/user/team 前缀，
  也不是 Browser、Session 或 IAM caller 传给 GA 的字段。
```

当前关系：

```text
Host / domain → tenant-site binding → tenant_id
tenant_id      → System site/product/config scope
tenant_id      → IAM / Billing / Model / Capability / Storage / Scheduler data scope
```

如果未来出现一个 Tenant 下多个独立产品入口，再新增明确的 `site_key`/`product_id`，不改变 `tenant_id` 的安全含义。

## 2. 仓库拓扑

```text
kokoro-system/       独立通用业务能力与产品配置服务
kokoro-iam/          独立身份、Tenant、认证、组织、权限服务
kokoro-payment/      支付事实
kokoro-credit/       Credit 事实
kokoro-model/        模型事实和路由
kokoro-hub/          Skill/MCP/Capability 事实
kokoro-session/      会话、Run、SSE、HITL
kokoro-agent/        Agent 执行
kokoro-web-user/     User Web 独立前端子仓库
kokoro-web-admin/    Admin Web 独立前端子仓库
```

`kokoro-system` 不挂载其它仓库；每个仓库独立 Git、lockfile、测试、构建和部署。

## 3. IAM

IAM 拥有：

```text
Tenant identity
    Tenant-Site/domain binding
User / Contact / Principal
Organization / Membership
Authentication / AuthSession
Role / Permission / Authorization
Security audit
```

同一邮箱跨 Tenant 不合并：

```text
逻辑身份键：`(tenant_id, normalized_email)`；数据库不建立业务 UNIQUE 索引，使用事务内冲突锁、查询和应用层错误码保证并发一致性。
```

登录态、Organization、Workspace、Membership、权限和业务数据都必须绑定 `tenant_id`。
只有 `kokoro-system` 的 Site 资源与 `kokoro-iam` 的 Tenant-Site binding 保存 `site_id` 内部引用。

浏览器不能提交 `tenant_id` 作为权威选择；Web BFF 从 Host、部署绑定和密封 Session 建立可信上下文。

## 4. kokoro-system

`kokoro-system` 是通用业务能力和产品配置控制面，负责：

```text
Product / application registry
Global FeatureDefinition + tenant/App AppFeatureExposure（只提供可信 FeatureKey）
Navigation / menu
Localization namespace and overrides
Theme / skin / layout metadata
Feature flags
Product capability exposure
Notification templates
Asset metadata references
Runtime manifest
```

按 `tenant_id`、`product_id`、`app_key`、`surface` 或 `global` 作用域配置。

它只保存跨领域选择，不复制领域事实：

```text
system: tenant-a enables offering=pro
payment: pro 的价格、订单、订阅和退款

system: tenant-a publishes app=music / feature=FEATURE_KEY_MUSIC_CREATE
GA: Feature 定义、Agent、能力约束与 native readiness 事实

system: tenant-a enables capability=music.generate
hub: capability 的授权和执行事实
```

`feature_key` 是 System、GA、Session、Studio/Credit 共享的产品语义键，准确类型是**全局唯一、不可变的
FeatureKey**。System 的 global `FeatureDefinition` 拥有这个 key、输入输出、用户可见 delivery/error/updating state、基线权限、
`cost_policy` 与产品状态；这组 ProductOutcomeContract 只说明用户获得什么，不含 Agent/member/graph/Skill/Tool/provider。tenant/App/Host/route/
display slug 位于 `AppFeatureExposure`，它只映射到一个 global FeatureKey。这些展示/入口对象不是 GA catalog identity。
GA 只拥有同 key 的 Feature 定义/Agent。System 发布或 CI
校验每个 enabled Feature 在 GA catalog 有 route；GA 受理时再次校验 key，双方不复制对方的配置或私库读取。

因此 GA 的 `FeatureCatalog` 只以 FeatureKey 索引，不以 `(tenant_id, app_key, slug)` 复合索引，也不在 worker 查询 System。
两个 tenant 可以把同名入口显式映射到同一个 FeatureKey 来复用编排；同一产品功能的 checkpoint-compatible GA policy
演进走普通 catalog rollout，不改变 FeatureKey。只有 tenant 专属静态产品组装、新的产品功能边界，或无法兼容既有
checkpoint 的拓扑变化，System 才分配新的 global FeatureKey 并走 GA candidate warm 后再启用。用户、套餐、可见
Skill/Asset 等动态差异只形成经 source owner 当前重验的动态收窄 constraint，不创建 graph variant。详见
[ADR-021 FeatureKey identity](../decisions/ADR-021-feature-key-global-catalog-identity.md) 与
[ADR-022 RunExecutionAttestation](../decisions/ADR-022-run-execution-attestation-and-dynamic-capability-resolution.md) 与
[41 Feature 结果契约](41-feature-outcome-contracts-and-quality-gates.md)。

System 的产品 UI/exposure 配置与 GA Feature 定义 deployment 是两条独立的 owner 流：前者不携带 Agent/Feature 定义/model/tool
内容，后者不读取 System 私库。若 Admin 同时新增产品入口和编排，则以 `feature_key` 协调“System disabled Feature ->
GA candidate 校验/warm -> System enable”的顺序；它不生成 Session agent、binding 或 graph identity。System 产品结果契约与 GA execution contract 仅在 CI 以 FeatureKey join，
验证 safe delivery、Artifact/Job 与成本关系；它们不建立 runtime RPC 或双写配置。见
[42 GA 核心架构](../technical/42-ga-core-architecture.md) 与
[41 Feature 结果契约](41-feature-outcome-contracts-and-quality-gates.md)。

## 5. 请求上下文

内部请求统一使用：

```text
TenantRequestContext {
  tenantId: string              # 唯一隔离键
  actorId: string | null
  organizationId: string | null
  permissions: string[]
  correlationId: string
}
```

业务 payload 不重复携带 `tenant_id`；内部 transport/envelope 传递受信 context。
进入 GA 的 Root Launch 不转交 `TenantRequestContext.namespace`，而由 Session/IAM 从上述可信上下文构造
`ExecutionIdentity(tenant_ref, actor, subject, identity_assertion_ref)`。这两者有不同职责：

| 对象 | 用途 | owner | 是否进入 GA public request |
|---|---|---|---|
| `tenant_id` / `tenant_ref` | tenancy、IAM、产品准入与业务数据隔离 | IAM/System/各业务 owner | 只作为受信 `ExecutionIdentity.tenant_ref`。 |
| `actor` | 谁发起这一次 Launch 或后续控制 | IAM/Session audit | Launch 进入 `ExecutionIdentity`；后续 control 只附 Session `control_audit_ref`。 |
| `subject` | 个人/项目/服务执行归属、积分 payer 与 Capability path | Session/IAM/Billing/Capability | 作为受信 `ExecutionIdentity.subject`；Billing 使用其最小投影。 |
| `RuntimeNamespace` | GA checkpoint、RunLedger、workbench、thread gate 隔离 | GA | 否。GA ingress 首次 target bootstrap 派生并固化到 private `ThreadLocator`。 |

因此 GA 同时需要“谁的业务执行”（`ExecutionIdentity.subject`）和自己的运行隔离根
（`RuntimeNamespace`）：前者服务计费、审计与外部 owner current recheck，后者只保证 GA execution state 不串。GA
绝不从 namespace 反查账户、项目或用户；Billing/Capability/Storage/Studio public contract 也不接收它。

```text
Browser
  → Web BFF 根据 Host 解析 tenant_id
  → IAM 校验 Tenant/User/Organization/Permission
  → System 读取 tenant-scoped manifest
  → Payment/Credit/Model/Hub/Session 使用 tenant context
  → Session/IAM 以 trusted ExecutionIdentity 受理 Launch
  → GA 首次 target bootstrap 派生 private RuntimeNamespace，并以 ThreadLocator 固化
```

浏览器响应不暴露内部 `tenant_id`；只返回必要的品牌、产品、菜单、i18n 和 UI 配置。

## 6. Runtime Manifest

```http
GET /system/runtime-manifest?product_id=PRODUCT_ID&locale=LOCALE
```

服务端根据可信请求上下文获得真正的 `tenant_id`；`tenant_key` 不作为浏览器可提交的授权参数。Manifest 包含：

```text
navigation
locale namespaces
theme tokens
layout key
enabled product entries / App / Feature references
feature flags
safe domain references
manifest digest
```

## 7. 新业务与拆仓

```text
菜单/i18n/theme/feature/product config → kokoro-system module
用户/组织/权限 → kokoro-iam module
订单/订阅/退款 → kokoro-payment module
额度/账本/usage → kokoro-credit module
模型/provider/routing → kokoro-model module
Skill/MCP/capability → kokoro-hub module
会话/SSE/HITL → kokoro-session module
Agent execution → kokoro-agent module
```

新增业务不自动新建子仓库。只有独立数据 owner、独立 SLO、独立扩缩容、独立故障域或独立发布节奏成立时才提取新仓库。
