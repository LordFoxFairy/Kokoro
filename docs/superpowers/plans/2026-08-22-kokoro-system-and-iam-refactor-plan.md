# kokoro-system 与 kokoro-iam 改造实施计划

> **已被当前计划 supersede：** 请以 `2026-08-22-kokoro-system-iam-refactor-plan-v2.md` 为准；当前唯一隔离键是 `tenant_id`。

状态：阶段 0-2 已完成；阶段 3-4 仍需接入业务服务和 User Web。执行对象为 IAM/System agent。Admin Web 不在本计划范围内。

## 目标

完成两个独立后端子仓库：

```text
kokoro-iam/
kokoro-system/
```

IAM 提供 Tenant/Realm 安全隔离与身份授权；System 提供通用业务能力和产品配置。两者通过稳定契约协作，不共享源代码、
私有 repository、ORM entity 或数据库写面。

## 阶段 0：契约和 owner 冻结

### 产出

```text
TenantContext / SiteBinding schema
IAM authentication/authorization contract
SystemRuntimeManifest schema
system module registry
table owner inventory
```

### 门禁

```text
每张表只有一个 runtime writer
每个 API 有明确 caller、scope 和错误语义
site_id/namespace 两者语义不混用
```

## 阶段 1：IAM Tenant 基础（已完成基础闭环）

### 实现

1. 建立 `iam_site`、`iam_site_domain`。
2. 将 User、Contact、Organization、Membership、AuthSession 全部绑定 `site_id`。
3. 将 `(tenant_id, normalized_email)` 定义为逻辑身份键；数据库不建立业务 UNIQUE 索引，使用事务内冲突锁和应用层错误码保证并发一致性。
4. SiteDomain resolve 得到 `host -> site_id`。
5. Authentication 在请求、消费 Magic Link、Refresh、Logout、GetSession 时校验 Tenant。
6. Authorization 在 Permission 判断时校验 Tenant、Organization、Membership。
7. 统一 `SiteRequestContext`，拒绝浏览器自选 Site。

### 必测反例

```text
同邮箱不同 Tenant 创建两份身份
Tenant A token 访问 Tenant B 资源失败
Tenant A membership 访问 Tenant B organization 失败
未知/disabled Host 不产生业务写入
旧 Tenant session 不能切换 Site
```

## 阶段 2：kokoro-system 独立子仓库（已完成 Runtime Manifest 垂直切片）

### 实现 module

```text
product
navigation
localization
theme
feature-flags
capability-assignment
commerce-assignment
model-assignment
asset-metadata
release
```

### 第一版能力

```text
按 scope 读取和写入 typed config
菜单配置
i18n namespace/override
theme token/layout manifest
产品/App/Surface registry
Feature flags
Offering/Capability/Model 引用
RuntimeManifest 查询
配置版本、digest、active binding
Admin manifest 和权限声明
```

### 明确不做

```text
站点创建/销毁编排
DNS 或证书编排
复杂部署平台
Payment/Credit/Model/Capability 业务事实
React 页面和组件
```

## 阶段 3：业务服务接入 TenantContext

按 owner 逐个接入：

```text
Payment: order/subscription/refund scope
Credit: account/hold/ledger/usage scope
Model: site/product visibility policy
Hub: capability assignment and connection scope
Session: session/conversation/run scope
Agent: admission strips site context and keeps opaque namespace
```

任何服务不得从 Host 自行推断 Tenant，也不得直接写其它 owner 表。

## 阶段 4：User Web 接入

`kokoro-web-user`：

1. BFF 解析 Host 与部署绑定。
2. BFF 调 IAM 校验 TenantContext。
3. BFF 调 System 读取 RuntimeManifest。
4. 页面渲染 shadcn/ui、主题、导航、i18n 和产品入口。
5. 浏览器不提交或读取内部 `site_id`。
6. User Web 的 session/auth 请求统一从 server context 注入 TenantContext。

Admin Web 不在本阶段修改。

## 阶段 5：独立部署和回归

### 每个仓库必须通过

```bash
pnpm test
pnpm typecheck
pnpm lint
pnpm build
```

### 跨仓验收

```text
Host → SiteBinding → TenantContext → IAM → System → Web manifest
```

### 安全验收

```text
cross-tenant read = 0
cross-tenant write = 0
same-email cross-tenant collision = 0
browser-forged site context = 0
GA receives site/tenant as second axis = 0
```

## 拆仓规则

本计划执行期间不因新增普通业务能力创建新仓库：

```text
菜单/i18n/theme/feature/product config → kokoro-system module
身份/组织/权限 → kokoro-iam module
领域事实 → 现有 owner module
```

只有经过独立 SLO、数据 owner、故障域、扩缩容和发布节奏评估后，才创建新的 repository/deployment。
