# 统一后台

## 范围

本文定义 Kokoro 的统一管理后台：各业务子仓如何贡献后台能力，`kokoro-web/admin` 如何渲染壳子，权限和审计如何收口，跨站访问如何受限。

## 核心结构

后台不是每个子仓各起一个后台，而是「壳子 + manifest」：

```text
kokoro-web/admin   渲染壳子，统一导航、登录、权限拦截、审计入口。
子仓 admin manifest  每个子仓声明自己的后台资源、操作和权限 key。
```

子仓只贡献 manifest 和后端 API，不贡献后台前端框架。新增一个后台模块 = 子仓加一份 manifest，不改壳子。

## Admin manifest

每个子仓的 manifest 声明：

```text
basePath        后台挂载路径，如 /admin/credit。
resources       资源清单（accounts / ledger / orders ...）。
权限 key        每个资源-操作对应的 permission key。
resource-action 资源上允许的动作（read / write / refund / adjust ...）。
```

manifest 是后台能力的单源真理。壳子据此渲染菜单、按钮和守卫；resources 以 manifest 为准，不在壳子里硬编码。

## 后台分层

```text
Platform Console   平台超级后台，跨站管理能力和成本。
Site Console       站点后台，只管理当前站点。
Workspace Console  团队/个人工作区设置。
Provider Console   LiteLLM、Stripe 等第三方后台链接或嵌入。
```

## 资源清单

按子仓 basePath 收口（resources 以各子仓 manifest 为准）：

```text
/admin/sites      sites / domains / brand / seo / 上线 checklist     —— kokoro-site
/admin/users      users / teams / memberships / service-accounts     —— kokoro-user
/admin/model      provider accounts / model bindings / labels / health —— kokoro-model
/admin/credit     accounts / ledger / usage / pricing-rules          —— kokoro-credit
/admin/payment    plans / orders / subscriptions / payment events / refunds —— kokoro-payment
```

Platform Console 跨站聚合页：

```text
Sites / Capabilities / Models / Billing Ops / Credit Ops
Cost & Margin / Risk / SEO Ops
```

Site Console 站内页：

```text
Overview / Users / Billing / Credits / Content / Models / Settings
```

## 权限模型

权限按 permission key 授予，按 resource-action 校验。现有 key（细分 read/write 部分规划中）：

```text
site.admin.manage / workspace.member.manage
model.provider.manage
credit.read / credit.write / credit.adjust
payment.order.read（write / refund 规划中）
```

第一阶段用户角色：`owner / admin / member`。后续接入 permission key 体系，由 `kokoro-user` 的 Role/Permission 承载。

## 跨站边界

```text
默认       后台查询带 siteId，site admin 只能看本 site 数据。
跨站       仅 platform root admin 可跨站查询和聚合。
红线       site admin 不能查询其它 site 的 user / order / credit / artifact。
```

跨站只读聚合（成本、毛利、收入）属于 Platform Console，不下放到 Site Console。站点边界见 [../decisions/ADR-001-site-boundary](../decisions/ADR-001-site-boundary.md)。

## 审计

所有高影响操作必须写审计：

```text
credit       grant / spend / refund / 手动调整。
payment      退款 / 订单干预 / provider config 变更。
site         status 变更 / domain / canonical / robots / model allowlist。
pricing      pricing rule / free quota 变更。
user         角色变更 / service account / 跨站操作。
```

高风险配置变更走 `draft -> review -> publish -> rollback -> audit`，不允许无审计直接生效。

## 可观测性维度

后台指标和日志必须支持这些维度，便于按站点独立运营：

```text
siteId / appKey / surface / capabilityKey / modelLabel
provider / workspaceId / plan-offer / route-pageType
```

可重试的运营异常队列（payment webhook failed、capture failed、provider charged but job failed 等）也由后台呈现，带状态机、幂等和人工操作审计。

## 验收标准

```text
site admin 只能看到本 site 数据。
platform admin 能按 site/capability 看收入、成本和毛利。
每个 job 能从请求追踪到 provider 成本和 credit ledger。
payment/credit 异常有可重试队列。
pricing/SEO/domain/model policy 变更有审计和回滚。
新增后台模块只需子仓加 manifest，不改壳子。
```
