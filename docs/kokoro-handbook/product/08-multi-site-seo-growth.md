# 多站点、SEO 和增长

## 定位

Kokoro 不是只做一个主站，而是可以复制多个独立 AI 产品站点。每个站点有独立品牌、定位、SEO、套餐和数据分析，底层复用平台。

## 站点类型

```text
主站       通用 AI 工作台和品牌入口。
垂直产品站  music/video/image/code 等。
SEO 内容站  围绕长尾关键词和模板页增长。
白标站     给客户独立品牌和域名。
活动站     临时 campaign 或模板市场。
```

站点和协作边界见 [05-teams-workspaces-projects](05-teams-workspaces-projects.md)。

## SEO 页面类型

```text
首页       品牌和核心价值。
功能页     AI music generator、AI video maker 等。
模板页     风格、行业、用途模板。
产物公开页  用户可分享结果。
教程页     how-to、最佳实践、案例。
价格页     套餐和权益。
```

## 站点隔离

每个站点默认按 siteId 隔离：

```text
用户、套餐、积分、SEO 配置、品牌、
analytics、风控状态、客服和运营状态。
```

## 增长归因

必须按 siteId 记录：

```text
visit
signup
activation
first_job
first_artifact
payment
retention
share
```

## 内容治理

SEO 内容不能只是换关键词。每个站点必须有真实功能和真实转化路径：

```text
keyword -> landing page -> create intent -> job -> artifact -> signup/payment
```

## 风险

```text
不要复制低质量页面。
不要多个站点 canonical 混乱。
不要让白标客户数据互相可见。
不要把所有站点注册合并成全局用户。
```
