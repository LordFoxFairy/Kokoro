# 站点上线清单

## 范围

本文定义一个 AI 产品站点从配置到上线的检查项，以及站点生命周期状态机。多站点不是建很多域名，而是平台化孵化、验证、运营和下线独立 AI 产品。新增站点只需配置，不复制平台后端。

## 站点生命周期状态机

```text
draft        只允许 platform admin 配置。
sandbox      允许内部账号访问，用测试 provider/payment。
beta         允许白名单/邀请码访问，小流量验证成本/转化/留存。
active       正常服务和索引。
paused       暂停新任务，保留登录和账单。
sunsetting   停止新注册和新购买，允许导出、退款、查看历史。
archived     禁止业务写入，只保留审计读取。
disabled     站点关闭，所有访问返回明确错误或维护页。
```

状态影响：注册 / 登录 / 新建 workspace / 新建订单 / 领取免费额度 / 发起 agent job / 公开 SEO 页面 / sitemap 输出 / 后台操作。

## 上线前检查

### 域名 / SSL / canonical

- [ ] SiteDomain 已验证。
- [ ] canonicalHost 已配置。
- [ ] SSL 证书就绪，HTTPS 可访问。

### 品牌配置

- [ ] SiteBrand 完整（名称、logo、主题）。
- [ ] site theme / i18n / navigation 已配置。

### 商业模型（offer / pricing / entitlement）

- [ ] SiteOffer 至少有免费或付费方案。
- [ ] CreditBucket / Entitlement 初始化规则存在。
- [ ] PricingRule 可覆盖主要能力（capability）。
- [ ] offer 站点隔离：本站 offer 不出现在其它站。

### 模型配置（SiteModelPolicy / fallback / provider 健康）

- [ ] SiteModelPolicy 可 resolve 默认模型。
- [ ] 未授权模型无法被站点 resolve。
- [ ] provider health 可触发站点内 fallback，fallback 不越过 site allowlist。
- [ ] pricing 仍由 credit 管，不与模型可见性混在一起。

### SEO（robots / sitemap / canonical / noindex 白标）

- [ ] SEO 首页和核心页面已配置。
- [ ] robots / sitemap 策略已确认，sitemap 不跨站。
- [ ] 每个 host 输出独立 metadata，canonical 指向本站。
- [ ] 白标站默认 noindex 或按策略控制索引。
- [ ] SEO 页面不是单纯关键词替换。

### 风控限流

- [ ] 风控和限流策略存在（免费额度 farming、支付异常、内容风险）。
- [ ] 可观测性维度齐全：siteId / capabilityKey / modelLabel / provider 等。

### 客服 / 法律

- [ ] 隐私政策链接存在。
- [ ] 服务条款链接存在。
- [ ] 退款 / 客服入口存在。

## 上线后运营对象

站点上线后按这些维度独立看数据，不只看全平台总数：

```text
Acquisition  SEO 页面、广告 campaign、推荐链接、模板案例页。
Activation   首次注册、首次生成、首次保存产物。
Conversion   首次到达额度墙、首次 checkout、首次订阅。
Retention    回访、项目继续编辑、二次生成、订阅续费。
Expansion    增量积分包、高级模型、团队协作、API 使用。
Support      失败任务、退款、额度争议、内容安全申诉。
```

## 配置变更治理

高风险配置变更走 `draft -> review -> publish -> rollback -> audit`，不允许无审计直接生效：

```text
pricing rule / free quota / payment provider
domain / canonical / robots policy
model allowlist / site status
```

## 下线策略

站点下线不能简单删除。

sunsetting 阶段：

```text
停止新注册 / 新购买 / SEO index 新页面。
保留登录、历史产物查看、数据导出、退款/客服、账本审计。
```

archived 阶段：

```text
关闭业务写入，只保留合规需要的订单/账本/审计。
artifact 按策略删除或冷存储。
搜索引擎输出 noindex 或 410/301 策略。
```

## 验收标准

```text
新站从 draft 到 active 有明确 checklist 并逐项通过。
disabled/sunsetting 状态会影响注册、支付、生成和 SEO。
站点运营指标能独立看 acquisition/activation/conversion/retention。
下线站点不再产生新订单或新扣费。
archived 站点不出现在 sitemap。
新增一个站点只需配置 site/brand/offer/model policy/seo，不复制平台后端。
```

站点边界见 [../decisions/ADR-001-site-boundary](../decisions/ADR-001-site-boundary.md)；上线前数据站点化见 [migration-checklist](migration-checklist.md)；后台运营见 [admin-console](admin-console.md)。
