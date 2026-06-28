# Site Resolution 链路

## 目标

把一个 HTTP host（加 path）解析成 SiteContext，确定当前请求属于哪个独立 AI 产品站点、该站点怎么运行，并把上下文注入下游可消费的 `x-kokoro-*` headers。这是所有业务请求的第一步，纯查询、无副作用。

## 参与模块

```text
kokoro-site                    入口权威，resolve(host, path) -> SiteContext。
kokoro-web / admin / gateway   解析后注入 x-kokoro-* headers。
下游服务                        只消费 headers，不从 host 猜站点（P9）。
```

## 前置条件

```text
SiteDomain 已绑定且 status=active，host 指向某 siteId。
Site status=active。
站点配置（Brand/App/Policy/Seo）已就绪。
```

## 主流程

```text
1. 入口收到请求
   取 HTTP Host + path，生成 requestId。

2. Resolve
   GET /sites/resolve?host=music.example.com&path=/ai-song-generator
   kokoro-site 查 SiteDomain(host) -> siteId，再聚合 Site/Brand/App/Capability/Seo。
   命中进程内短 TTL cache（配置变更后 30-60s 生效），MySQL 为最终真相。

3. 组装 SiteContext
   siteId, siteKey, host, canonicalHost, appKey, surface, brandKey, locale, requestId。

4. 注入 headers
   web/admin/gateway 把 SiteContext 写成 x-kokoro-* headers。

5. 认证后补齐
   登录后追加 userId, workspaceId, role, permissions。
```

## 异常流程

```text
域名未绑定        host 查不到 SiteDomain -> 拒绝，不落到默认站点执行业务写入。
站点未 active     Site status != active 或 SiteDomain status != active -> 前台与 API 写入都拒绝。
canonical 不匹配  请求 host != SiteDomain.canonicalHost -> 301 跳转到 canonicalHost。
```

## 数据变化

```text
无写入。纯读 Site / SiteDomain / SiteBrandConfig / SiteApp / SiteCapability / SiteSeoConfig。
```

## 幂等和一致性

```text
requestId        本次请求全链路追踪，向下游传递。
无副作用          解析可任意重试，不产生状态变化。
缓存一致          MySQL 权威；进程内短 TTL cache 允许 30-60s 滞后；后续 Redis + 版本广播 invalidate。
```

## 用户可见结果

```text
正常      请求落到正确站点，前台按该站 Brand/SEO 渲染。
非 canonical  301 跳转到主域名。
未绑定/禁用    站点不可访问，业务写入被拒。
```

## 验收标准

```text
同一后端服务能服务多个 host。
host 解析失败时不落到默认站点执行写入。
非 canonical host 访问 -> 301 到 canonicalHost。
站点禁用后前台和 API 写入都拒绝。
下游服务只认 x-kokoro-* headers，不读 host。
```

## 相关

```text
原则     ../decisions/ADR-001-site-boundary.md
模块     ../modules/kokoro-web.md
后续     ./user-register-login.md（认证后补齐 userId/workspaceId）
```
