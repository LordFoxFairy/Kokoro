# Kokoro Tenant、System 与 User Web 架构技术方案 v2

状态：当前有效方案，2026-08-22。

> 本文 supersede `30-kokoro-system-and-iam-tenant-architecture.md` 中将 `site_id` 与 `tenant_id` 并列为隔离键的表述。

## 1. 统一命名决定

```text
tenant_id
  唯一的身份、权限和业务数据隔离键。

site / site_key
  产品、品牌、域名和展示语义；当前一个 site 就是一个 tenant，不再建立第二套隔离 ID。

namespace
  GA 的 opaque 执行隔离键，不拼接 tenant/user/team 前缀。
```

当前关系：

```text
Host / domain → tenant_id
tenant_id      → System product/config scope
tenant_id      → IAM / Payment / Credit / Session data scope
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
Tenant/domain binding
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

浏览器不能提交 `tenant_id` 作为权威选择；Web BFF 从 Host、部署绑定和密封 Session 建立可信上下文。

## 4. kokoro-system

`kokoro-system` 是通用业务能力和产品配置控制面，负责：

```text
Product / application registry
Navigation / menu
Localization namespace and overrides
Theme / skin / layout metadata
Feature flags
Product capability exposure
Notification templates
Asset metadata references
Config version / release pointer
Runtime manifest
```

按 `tenant_id`、`product_id`、`app_key`、`surface` 或 `global` 作用域配置。

它只保存跨领域选择，不复制领域事实：

```text
system: tenant-a enables offering=pro
payment: pro 的价格、订单、订阅和退款

system: tenant-a enables capability=music.generate
hub: capability 的版本、授权和执行事实
```

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

```text
Browser
  → Web BFF 根据 Host 解析 tenant_id
  → IAM 校验 Tenant/User/Organization/Permission
  → System 读取 tenant-scoped manifest
  → Payment/Credit/Model/Hub/Session 使用 tenant context
  → Agent admission 后只保留 opaque namespace
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
enabled product entries
feature flags
safe domain references
configVersion / releaseId / digest
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
