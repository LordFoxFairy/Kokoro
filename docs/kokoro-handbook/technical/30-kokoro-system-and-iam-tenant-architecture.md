# Kokoro System 与 IAM Tenant 架构技术方案

> 本文已由 `31-kokoro-tenant-system-architecture-v2.md` supersede。当前以 `tenant_id` 为唯一隔离键；本文中将 `site_id` 作为独立隔离轴的表述不再执行。

> **已被当前方案 supersede：** 请以 [31-kokoro-tenant-system-architecture-v2.md](31-kokoro-tenant-system-architecture-v2.md) 为准。当前只使用 `tenant_id` 作为隔离键，不执行本文中 `site_id`/`tenant_id` 双键方案。

状态：目标技术方案，2026-08-22。

## 1. 决策

Kokoro 使用两个相邻但不同的控制面：

```text
kokoro-iam
  Tenant/Realm 安全边界、Identity、Organization、Authentication、Authorization、Audit

kokoro-system
  通用产品能力、产品配置、导航、i18n、主题、Feature、Runtime Manifest、配置发布
```

二者都是独立子仓库、独立构建和独立部署，不互相挂载源代码。新增普通通用能力先在 `kokoro-system` 内增加 module；
只有独立数据 owner、独立故障域、独立扩缩容或独立发布节奏成为硬要求时，才创建新的后端子仓库。

## 2. 四个概念

```text
site_id
  域名/产品入口与配置作用域；不替代 tenant_id。

product_id / product_profile_id
  产品组合：菜单、i18n、主题、功能入口、能力和业务引用。

namespace
  GA 的 opaque 执行隔离键；不拼接 user/site/tenant 业务前缀。
```

```text
Host → IAM SiteBinding → tenant_id + site_id → TenantRequestContext
```

## 3. IAM 边界

### 拥有

```text
Site/Tenant identity
SiteBinding (host -> site_id)
SiteDomain / host binding
Identity / User / Contact
Organization / Membership
Authentication / AuthSession
Role / Permission / Authorization
Security Audit
```

### 不拥有

```text
菜单显示顺序和 React 页面
i18n 文案内容
CSS token 和主题实现
Payment 价格与订单事实
Credit 账本
Model provider 路由事实
Capability 执行版本
Session 消息和 Run
Agent 执行
```

### 身份唯一性

```text
逻辑身份键为 `(tenant_id, normalized_email)`；数据库不建立业务 UNIQUE 索引，由事务内冲突锁、查询和应用层错误码共同保证。
```

同一邮箱在不同 Site/Tenant 下是不同身份；登录、Session、Organization、Membership、权限和数据均不跨 Site 复用。

## 4. System 边界

`kokoro-system` 是独立的通用业务能力服务，不是 `kokoro-platform` 的父仓库，也不是 IAM 的附属目录。

### Modules

```text
product
application
navigation
localization
theme
feature-flags
capability-assignment
commerce-assignment
model-assignment
notification-template
asset-metadata
release
```

### System 保存选择，不复制事实

```text
system: product-a enables offering=pro
payment: pro 的价格、订单、订阅和退款事实

system: product-a enables capability=music.generate
hub: capability 的版本、连接器、授权和执行事实
```

## 5. 数据模型

### IAM owner schema

```text
iam_site
  tenant_id, site_id, key, status, default_locale, timezone, product_profile_id?

iam_site_domain
  site_domain_id, site_id, host, status, is_primary, canonical_host

iam_user
  user_id, tenant_id, normalized_email, status

iam_organization
  organization_id, tenant_id, ...

iam_membership
  membership_id, tenant_id, site_id, organization_id, principal_id, status

iam_auth_session
  auth_session_id, tenant_id, site_id, principal_id, organization_id, ...
```

所有跨 Site 关联只保存 ID，不建立数据库外键；由应用层事务校验、显式行锁/锁桶和契约测试保证一致性。

### System owner schema

```text
system_product
system_product_profile
system_navigation
system_locale_bundle
system_theme_manifest
system_feature_flag
system_capability_assignment
system_commerce_assignment
system_model_assignment
system_asset_ref
system_config_release
system_release_binding
```

配置记录统一具有：

```text
scope_type / scope_id
config_key
schema_version
status
config_version
release_id
digest
updated_by
```

禁止建立无 schema、无 owner 的万能 `system_config` JSON 垃圾桶。

## 6. SiteRequestContext

服务间请求由 Web BFF 或受信入口构建：

```text
SiteRequestContext {
  siteId: string                # 数据、授权和产品入口的 canonical key
  actorId: string | null
  organizationId: string | null
  permissions: string[]
  correlationId: string
}
```

规则：

1. 浏览器不提交 `site_id` 作为权威选择。
2. BFF 根据 Host、部署绑定和密封 Session 得到上下文。
3. IAM 校验 SiteBinding、Site 状态、用户和组织成员关系。
4. 下游 owner 校验自己的资源与 `siteId` 一致。
5. 业务 payload 不重复塞 `site_id`；内部 transport 使用受信 context/envelope。
6. 浏览器响应过滤内部 site ID，只返回必要的公开品牌、产品和 UI 配置。
7. 进入 GA 后只传 opaque namespace；GA 不把 site 当第二隔离轴。

## 7. SystemRuntimeManifest

```http
GET /system/runtime-manifest?site_id=SITE_ID&product_id=PRODUCT_ID&locale=LOCALE
```

该请求只允许服务端调用，返回：

```text
product / app / surface
navigation
locale namespace and site overrides
theme tokens and layout key
enabled product entries
feature flags
safe references to offering/model/capability
configVersion / releaseId / digest
```

Web User 只消费这个 manifest；它不直连 system database，也不读取其它服务的内部配置表。

## 8. 端到端链路

```text
Browser Host
  → Web BFF normalizes Host
  → resolve SiteBinding
  → IAM validates tenant/session
  → System returns RuntimeManifest
  → Web User renders shadcn/ui + menu + i18n + theme
  → Payment/Credit/Model/Hub/Session receive SiteRequestContext
  → Agent receives only opaque namespace
```

## 9. 版本与缓存

```text
MySQL owner data
  → config release / digest
  → SystemRuntimeManifest
  → Web BFF short TTL cache
```

配置发布可以动态生效；React 组件和页面代码变化仍通过 `kokoro-web-user` CI/CD 发布。
缓存失效不改变 owner；配置版本和 digest 用于回滚、审计和一致性检查。

## 10. 关键不变量

```text
同邮箱跨 Tenant 不合并。
未知 Host 不落默认 Tenant 执行业务写入。
浏览器不能伪造 TenantContext。
下游业务写入必须有 TenantContext。
System 不拥有 Payment/Credit/Model/Capability 事实。
IAM 不拥有 Web React/UI 实现。
GA 只消费 opaque namespace。
新增普通通用能力不自动新增 repository。
```
