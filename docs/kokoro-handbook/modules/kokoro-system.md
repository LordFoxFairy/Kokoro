# kokoro-system：通用业务能力与产品配置控制面

> **命名约束：** 当前系统使用 `tenant_id` 作为唯一身份/数据隔离键；`site` 仅表示产品/品牌/域名语义，不再建立并行的 `site_id` 隔离轴。详细方案以 [Tenant、System 与 User Web 架构 v2](../technical/31-kokoro-tenant-system-architecture-v2.md) 为准。

状态：研发基线已落地，2026-08-22；业务 module 按增量实现。

## 定位

`kokoro-system` 是独立后端子仓库和独立运行服务，承载跨产品、跨 Web 面的通用业务能力与产品配置。
它不是其它子仓库的父仓库，也不挂载 IAM、Payment、Credit、Model、Session 或 Agent 的源代码。

它解决的问题是：新增一个普通的通用业务能力时，优先在同一服务内新增 module，而不是为菜单、i18n、主题、
功能开关等各开一个服务。

## 拥有

```text
Product / Application registry
Global FeatureDefinition (FeatureKey、I/O、用户可见 delivery/error/updating state、baseline permission、cost policy；即 ProductOutcomeContract)
Tenant/App AppFeatureExposure (FeatureKey、route、slug、UI visibility)
Navigation / menu
Localization bundles and namespaces
Theme / skin metadata and token manifests
Feature flags
Product capability exposure
Notification templates
Asset metadata and public references
Product UI configuration / Feature exposure（不指向 GA Workflow）
Admin resource manifests
```

这些对象可以按 `tenant_id`、`product_id`、`app_key`、`surface` 或 `global` 作用域配置；`site` 只保留为品牌、域名和产品入口语义，不是独立隔离键。

## 不拥有

```text
Identity、Authentication、Organization、Role、Permission 的事实 -> kokoro-iam
Payment、Order、Subscription、Refund 的事实 -> kokoro-payment
Credit Account、Hold、Ledger、Usage 的事实 -> kokoro-credit
Model Provider、Model Revision、Routing 的事实 -> kokoro-model
Skill、MCP、Capability Runtime 的事实 -> kokoro-hub
Conversation、Run、SSE、HITL 的事实 -> kokoro-session
Agent 执行、GA Feature/Agent Catalog、DeepAgents checkpoint、Feature evaluation 与运行证据 -> kokoro-agent 的 CI/evaluation 边界
React 组件和 Web 页面 -> kokoro-web-user / kokoro-web-admin
环境变量、Secret、容器和基础设施 -> deploy/ops
```

`kokoro-system` 可以保存其它领域的 assignment/reference，例如某产品启用哪个 offering 或 capability，
但不复制其价格、账本、执行配置或授权事实；引用必须由被引用的 owner 在使用时重新校验。

## Site / Tenant 边界

`tenant_id` 是 IAM 的唯一身份、授权和数据隔离键；当前不建立独立的 `site_id` 隔离轴。
域名、品牌和产品入口通过 Tenant/domain 与 product 配置表达，system 不创建第二套 Tenant 事实。

```text
kokoro-iam
  负责 tenant/domain identity、用户、组织、登录、成员关系、权限和 TenantBinding。

kokoro-system
  负责按 tenant/product 编排菜单、i18n、主题、产品入口和通用配置。
```

Tenant 是 IAM 的身份与授权隔离边界；同一邮箱在不同 Tenant 下是不同身份上下文：

```text
(tenant-a, email@example.com) != (tenant-b, email@example.com)
```

IAM 的唯一性约束和认证会话必须带 `tenant_id`；system 的配置读取使用 `tenant_id`/`product_id` 或明确的 global scope。TenantBinding 的最终 owner 是 IAM，system 只消费已校验的 binding。

## 目录

```text
kokoro-system/
├── src/
│   ├── modules/
│   │   ├── product/
│   │   ├── navigation/
│   │   ├── localization/
│   │   ├── theme/
│   │   ├── feature-flags/
│   │   ├── capability-assignment/
│   │   ├── asset/
│   │   ├── notification/
│   │   └── feature-exposure/
│   ├── interfaces/{http,rpc,admin}/
│   ├── infrastructure/
│   ├── generated/
│   ├── config/
│   ├── bootstrap/
│   └── main.ts
├── test/
├── docs/
└── package.json
```

每个 module 自己拥有 schema、application use case、权限、审计和测试。新增通用能力先新增 module，不新增仓库。

## 运行时契约

```http
GET /system/runtime-manifest?product_id=PRODUCT_ID&locale=LOCALE
```

返回 `SystemRuntimeManifest`：

```text
product / app / surface
navigation
locale namespaces and overrides
theme / skin manifest
enabled product entries
feature flags
safe domain references
```

System product/UI manifest 不传给 GA RunRequest，不引用 Workflow/Agent，也不作为 Session Workflow/
graph 选择。System 与 GA 只用 `feature_key` 做 CI/发布 join：System 先保存 disabled FeatureDefinition，GA Builder
发布同 key 的 candidate 并完成 all-worker warm，随后 System 才启用产品 admission。GA catalog 更新不由 System runtime manifest
反向解析。这里的 `feature_key` 是全局唯一、不可变的 FeatureKey；tenant/App/route/display slug 只在 System admission
映射到它，不能成为 GA catalog 的复合 key 或运行时 selector。详细门禁见
[42 GA 核心架构](../technical/42-ga-core-architecture.md) 与
[ADR-021](../decisions/ADR-021-feature-key-global-catalog-identity.md) 与
[41 Feature 结果契约](../technical/41-feature-outcome-contracts-and-quality-gates.md)。

浏览器不直接选择 `tenant_id`。Web BFF 从受信 Host 解析得到 TenantBinding，并通过受信内部请求上下文传入；System 重新向 IAM 校验 Host 与 `tenant_id` 的绑定。

## 仓库拆分规则

新增需求按以下顺序处理：

1. 通用产品能力：进入 `kokoro-system` 的现有或新 module。
2. 已有领域事实：进入对应 owner 仓库的 module。
3. 只有在独立部署、独立数据 owner、独立扩缩容、独立故障域或独立发布节奏成为硬需求时，才评估新子仓库。

`kokoro-system` 是一个独立子仓库，但不是“每种配置一个服务”；它是通用能力的模块化后端。
