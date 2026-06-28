# ADR-001 siteId 是第一业务隔离边界

状态：已采纳。

## 背景

Kokoro 要支持多个独立 AI 产品站点（zeze.work、music.example.com、video.example.com、白标站），每个站点独立品牌、套餐、SEO、风控和运营。需要一个统一且不可绕过的隔离边界。

## 决策

```text
所有业务数据默认带 siteId，或能通过上级对象追溯 siteId。
siteId 是所有查询和写入的第一过滤条件。
入口层（web/gateway）通过 kokoro-site 把 host 解析为 SiteContext，
业务子仓只消费 siteId，不自己从 host 推断站点。
```

必须直接带 siteId 的实体：User、Workspace/Team、CreditAccount、LedgerEntry、UsageRecord、PaymentOrder、Subscription、Project、Job、Artifact。

可平台复用（不带 siteId，靠 SiteModelPolicy 控制可见性）：ProviderAccount、ModelBinding。

## 约束

```text
缺失 siteId 的业务写请求必须拒绝。
后台查询默认按 siteId 过滤，只有 platform super admin 可跨站且必须审计。
web/gateway 不能绕过 SiteContext。
```

## 替代方案（已否决）

```text
全局邮箱 User + Org 隔离
  邮箱是登录凭证不是跨产品身份；免费额度/套餐/风控会全平台串联污染转化；
  白标客户隐私风险。

引入 Tenant 中间层（多 site 属于一个 Tenant）
  Kokoro 只有 platform 和 site 两层，Tenant 过度复杂化。
```

## 影响

迁移现有数据时回填 default site，新增 siteId 字段和 unique 约束；所有 API/SDK 强制 siteId 上下文；代码审查检查 siteId filter 完整性。详见 [migration-checklist](../operations/migration-checklist.md)。

相关：[ADR-002 用户身份](ADR-002-user-identity.md)、[ADR-003 credit ledger](ADR-003-credit-ledger.md)。
