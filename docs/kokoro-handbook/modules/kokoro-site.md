# kokoro-site 技术方案

## 定位

kokoro-site 是站点事实和 SiteContext 解析的唯一权威。它的存在是为了避免 web、user、credit、payment、model 各自解析域名和站点策略。

它只回答一个问题：当前请求属于哪个站点，以及这个站点该如何运行。它不管余额、不处理订单、不执行 agent。

实现状态：site/domain/app/policy 的最小表和 upsert/resolve 接口已实现；brand/SEO 管理 API、domain 验证状态流转、缓存策略为规划。

## 业务职责

owns：

```text
Site            站点实例。
SiteDomain      域名绑定和 canonical host，domain -> site 的解析权威。
SiteApp         站点启用的 app/surface。
SitePolicy      注册、workspace、钱包、模型、支付、SEO 策略。
SiteBrandConfig 主题、logo、文案命名空间、布局、导航。
SiteSeoConfig   title、description、canonical、robots、sitemap、structured data。
```

does not own：

```text
用户、团队、workspace（kokoro-user）。
积分账户和账本（kokoro-credit）。
支付订单和订阅（kokoro-payment）。
模型 provider secret（kokoro-model）。
agent job、artifact（运行时仓库）。
```

## 上游和下游

```text
上游（调用 site）：
  入口层 web/admin/gateway  GET /site-context/resolve。

下游（site 不主动调用业务子仓）：
  site 是叶子权威，被 user/model/credit/payment 间接依赖（消费 siteId）。
```

## 核心对象

```text
Site             key、name、status、defaultLocale、timezone、ownerKind(platform|customer)、metadata。
SiteDomain       host、status(pending|active|disabled)、isPrimary、canonicalHost、verifiedAt。
SiteApp          appKey、surface、status、defaultRoute、priority。
SitePolicy       policyKey、policyJson/value、status。
SiteBrandConfig  themeKey、logoUrl、faviconUrl、layoutKey、copyNamespace、navigationJson。
SiteSeoConfig    routePattern、titleTemplate、descriptionTemplate、canonicalPolicy、
                 robotsPolicy、structuredDataKind、sitemapPriority。
```

策略类型默认值：

```text
identityPolicy  = site_scoped
workspacePolicy = site_scoped
walletPolicy    = site_scoped
paymentPolicy   = platform_provider
modelPolicy     = site_allowlist
seoPolicy       = indexable
```

## 数据模型

MySQL（Prisma，权威）：

```text
site_sites          id, key, name, status, defaultLocale, timezone, metadata
site_domains        id, siteId, host, status, isPrimary, canonicalHost, metadata
site_apps           id, siteId, appKey, surface, status, defaultRoute, metadata
site_policies       id, siteId, key, value, status
site_brand_configs  id, siteId, key, themeKey, logoUrl, copyNamespace, layoutKey, status, metadata
site_seo_configs    id, siteId, routePattern, titleTemplate, descriptionTemplate,
                    canonicalPolicy, robotsPolicy, structuredDataKind, sitemapPriority, status, metadata
```

唯一约束：

```text
Site.key
SiteDomain.host
SiteApp(siteId, appKey, surface)
SitePolicy(siteId, key)
SiteBrandConfig(siteId, key)
SiteSeoConfig(siteId, routePattern)
```

其它存储：

```text
Mongo / Redis / 对象存储：当前不使用。
缓存（规划）：进程内短 TTL（30-60s）-> 后续 Redis cache + site_config_version + 发布广播失效。
任何缓存都不改变权威关系，MySQL 是最终真相。
外部系统：无。
```

## API / RPC / Events

```text
GET  /healthz
GET  /sites
POST /sites/upsert
POST /site-domains/upsert
POST /site-apps/upsert
POST /site-policies/upsert
GET  /site-context/resolve   入: host, appKey?, surface?
                             出: siteId, siteKey, host, appKey?, surface?, defaultLocale, timezone
```

```text
错误码  domain 未启用 / site 未 active -> not found（不得落到默认站点执行业务写入）。
幂等    upsert 接口按唯一约束幂等。
```

## Admin 管理

```text
basePath  /admin/sites
resources sites / domains / apps / policies（后续 brand / seo）
权限 key  site.read / site.write
          siteDomain.read / siteDomain.write
          siteApp.read / siteApp.write
          sitePolicy.read / sitePolicy.write
操作      站点/域名/应用/策略的增改查，品牌与 SEO 配置（规划）。
审计      写操作审计（规划接入统一审计）。
```

平台超级后台可切站查看；站点后台只看当前 site，白标站默认禁止跨站后台查看。

## 业务链路

```text
site-resolution   host -> SiteContext -> 注入 header -> 下游消费 siteId。
```

认证后 SiteContext 补 userId/workspaceId/role/permissions。详见 [ADR-001 站点边界](../decisions/ADR-001-site-boundary.md)。

## 部署

```text
服务名   kokoro-site
端口     4201
env      DATABASE_URL_SITE, KOKORO_SITE_PORT, KOKORO_SITE_BASE_URL
多 Pod   支持多副本；权威状态全部在 MySQL，不依赖进程内缓存做权威。
```

## 测试

```text
集成    upsert site/domain/app/policy 后 resolve 成功。
反例    domain pending/disabled 不 resolve；site 未 active 不 resolve；
        同一域名只能绑定一个 active site。
门禁    涉及 schema/repository/API 时跑 test:integration。
```

## 风险和边界

```text
host 解析失败时不能落到默认站点执行业务写入。
domain 变更需同步 canonical 和 sitemap。
白标站必须默认禁止跨站后台查看。
SitePolicy 不能变成无类型大 JSON 黑洞；高频策略需独立字段或 schema 校验。
业务子仓禁止自己解析 host，只消费 siteId。
```

## 后续任务

```text
P0  集成测试 upsert->resolve；domain pending verification 状态流转；SiteContext header helper。
P1  站点生命周期 draft/sandbox/beta/active/suspended/archive；默认站点初始化模板；brand/SEO 管理 API。
P2  gateway/web 侧缓存策略（Redis + config version + 失效广播）。
```
