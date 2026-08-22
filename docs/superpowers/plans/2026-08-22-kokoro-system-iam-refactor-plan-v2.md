# kokoro-system 与 kokoro-iam 改造实施计划 v2

状态：研发闭环已完成；Tenant/System 基础切片、兼容 API tenant 审计和跨租户验证已落地，2026-08-22。

当前已完成：IAM TenantDomain/tenant-binding、AuthAdapter tenant scope、Session/JWT tenant claim、组织/授权/旧 Site API/Administration 关键路径 tenant 过滤，生产 bootstrap 显式注入 Redis；System tenant-scoped Runtime Manifest、locale/surface scope precedence、MySQL/Redis cache contract 和 SQL policy。

> 本文是给 IAM/System agent 的执行入口；`tenant_id` 是唯一隔离键。旧计划中将 `site_id` 与 `tenant_id` 并列的步骤不再执行。

## 1. 目标

交付两个独立子仓库：

```text
kokoro-iam/
kokoro-system/
```

不修改 Admin Web。IAM 负责 Tenant 安全边界；System 负责通用产品能力和配置。

## 2. IAM 改造

1. 以 `tenant_id` 作为唯一隔离键；不新建平行 `site_id` 隔离轴。
2. Host/domain 解析结果绑定到 `tenant_id`。
3. User、Contact、Principal、Organization、Membership、AuthSession 全部带 `tenant_id`。
4. 身份逻辑唯一性使用 `(tenant_id, normalized_email)`；数据库不建立业务 UNIQUE 索引，使用冲突锁和应用层错误码保证并发一致性。
5. Authentication、Refresh、Logout、GetSession 全部校验 `tenant_id`。
6. Authorization 校验 Tenant、Organization、Membership、Role、Permission。
7. 任意浏览器提交的 `tenant_id`、Host 转发头或伪造上下文都不具备权威性。

## 3. System 独立子仓库

建立：

```text
kokoro-system/
├── src/modules/product
├── src/modules/navigation
├── src/modules/localization
├── src/modules/theme
├── src/modules/feature-flags
├── src/modules/capability-assignment
├── src/modules/commerce-assignment
├── src/modules/model-assignment
├── src/modules/asset-metadata
└── src/modules/release
```

第一版交付：

```text
tenant-scoped config
menu/navigation
i18n namespace and overrides
theme/layout manifest
feature flags
product/app/surface registry
capability/offering/model references
runtime manifest
config version/digest/release pointer
```

明确不做：

```text
证书/DNS 编排
站点创建销毁工作流
部署平台
Payment/Credit/Model/Capability 事实
React 页面和组件
```

## 4. Runtime Context

```text
TenantRequestContext {
  tenantId
  actorId?
  organizationId?
  permissions
  correlationId
}
```

业务请求由 BFF/受信入口建立上下文；业务 body 不重复添加 `tenant_id`。浏览器不读取或提交内部 `tenant_id`。

## 5. 验收门禁

```text
同邮箱跨 Tenant 创建两份独立身份
Tenant A token 访问 Tenant B 资源失败
Tenant A organization/member 访问 Tenant B 资源失败
未知/disabled Host 不产生业务写入
System manifest 按 tenant_id 隔离
菜单/i18n/theme 不进入 IAM 权限模型
Payment/Credit/Model/Hub/Session 不共享 System 私有表
GA 只收到 opaque namespace
```

## 6. 本轮研发验证证据

```text
kokoro-iam: 60 files / 211 tests passed
kokoro-iam: typecheck、lint、build passed
kokoro-iam: fresh MySQL 8.4 schema passed；foreignKeyCount=0、businessTriggerCount=0
kokoro-system: 3 files / 5 tests passed
kokoro-system: typecheck、lint、build passed
```

## 7. 拆仓规则

通用业务能力新增到既有仓库 module；领域事实新增到现有 owner。新建 repository 必须有独立数据 owner、SLO、故障域、扩缩容或发布节奏证据。
