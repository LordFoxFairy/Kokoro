---
artifact: architecture-design
version: "1.0"
created: 2026-08-22
status: proposed
scope: system-repository-tenant-isolation-and-user-web
implementationAuthorized: false
reviewGate: iam-tenant-contract-required
---

# kokoro-system、Tenant 隔离与 kokoro-web-user 技术方案

## 1. 决策摘要

Kokoro 采用四种边界：

```text
Repository       代码协作和版本边界
Bounded Context  业务语言和数据 owner 边界
Module           仓库内能力边界
Deployment Unit  独立启动、扩缩容和发布边界
```

新增业务不自动新增 repository。通用产品能力进入独立的 `kokoro-system` repository 内的 module；领域事实进入既有 owner；
只有运行时和故障边界真实独立时才提取新的 deployment/repository。

## 2. 目标仓库拓扑

```text
kokoro-system/       通用业务能力、产品配置和运行时 manifest
kokoro-iam/          Identity、Tenant/Realm、Authentication、Organization、Authorization、Audit
kokoro-payment/      Payment facts
kokoro-credit/       Credit facts
kokoro-model/        Model facts and routing
kokoro-hub/          Capability/Skill/MCP facts
kokoro-session/      Conversation、Run、browser transport
kokoro-agent/        Agent execution
kokoro-web-user/     User Web 独立前端子仓库
kokoro-web-admin/    Admin Web 独立前端子仓库
```

`kokoro-system` 不包含其它仓库的源代码；各仓库通过生成契约、HTTP/RPC 和事件交互。

## 3. Domain → Site 与 IAM

IAM 继续存在，并负责安全边界：

```text
site_id
用户身份
组织和成员关系
认证会话
角色和权限
跨租户拒绝
安全审计
```

`site_id` 是当前唯一的安全、数据隔离和域名/产品入口标识。Site 同时就是当前的 Tenant/Realm；当前不引入第二个租户 ID。

```text
Host → SiteBinding(IAM) → site_id
```

Site 同时是入口、产品配置、身份、授权和业务数据边界。

同一邮箱在不同租户下不共享身份：

```text
logical identity key = (tenant_id, normalized_email); physical database has no business UNIQUE index
session binding      = site_id + principal_id + organization_id
authorization scope  = site_id + organization_id + principal_id
```

任何浏览器提交的 `site_id` 都不是权威。Web BFF 根据 Host 得到 SiteBinding，内部形成 `SiteRequestContext`；IAM 和下游 owner 在写操作前校验 active site。

## 4. kokoro-system 的通用能力

```text
Product / application registry
Navigation and menu
Localization namespace and site overrides
Theme / skin / layout metadata
Feature flags
Product capability exposure
Notification templates
Asset metadata references
Configuration version and release pointer
Admin manifests
```

它保存按 Site/Product 作用域的跨模块选择，不复制领域事实：

```text
system: site-a enables offering=pro
payment: pro 的价格、订单、退款

system: site-a enables capability=music.generate
hub: capability 的版本、连接器和执行规则
```

## 5. Web 数据流

```text
Host / deployment binding
  -> Web BFF SiteContext
  -> kokoro-iam 校验 site/security context
  -> kokoro-system 获取 SystemRuntimeManifest
  -> kokoro-web-user 渲染 shadcn/ui、菜单、i18n、theme 和产品入口
  -> 各领域服务按 site context 执行真实业务
```

`kokoro-web-user` 拥有 React、布局和渲染器；`kokoro-system` 拥有产品级配置；IAM 拥有 SiteBinding、身份、会话和权限判断。Web BFF 不得接受浏览器自选的 site_id。

## 6. 配置契约

不得建立无限制的 `system_config` JSON 垃圾桶。每个 module 有独立 schema，但共享：

```text
scopeType / scopeId
configKey
schemaVersion
value
status
configVersion
releaseId
digest
updatedBy
```

读取接口：

```http
GET /system/runtime-manifest?site_id=SITE_ID&product_key=PRODUCT_KEY&locale=LOCALE
```

Manifest 可以包含：

```text
navigation
locale namespaces
theme tokens
layout key
enabled product entries
feature flags
domain references
configVersion / releaseId / digest
```

## 7. 新业务决策表

```text
菜单 / i18n / theme / feature flag       -> kokoro-system module
用户 / 组织 / 权限                         -> kokoro-iam module
订单 / 订阅 / 退款                         -> kokoro-payment module
额度 / 扣费 / 账本                         -> kokoro-credit module
模型 / provider / routing                  -> kokoro-model module
Skill / MCP / capability                   -> kokoro-hub module
Conversation / SSE / HITL                  -> kokoro-session module
Agent execution                            -> kokoro-agent module
```

内部业务请求统一携带 `SiteRequestContext`，不要求每个业务 payload 重复写 `site_id`：

```text
SiteRequestContext
  siteId         # 数据、权限和产品入口的 canonical key
  actorId
  organizationId?
  correlationId
```

浏览器不接收内部 site_id；Web BFF 只返回必要的公开品牌和产品字段。GA admission 结束后只向 GA 传递 opaque namespace，site_id 不成为 GA 的第二隔离轴。

只有独立 SLO、独立数据 owner、独立故障域、独立扩缩容或独立发布需要时，才创建新 repository/deployment。
