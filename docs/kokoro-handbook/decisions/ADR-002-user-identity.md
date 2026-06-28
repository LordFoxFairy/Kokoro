# ADR-002 同邮箱跨站默认是不同用户

状态：已采纳。

## 背景

用户在 music.example.com 用 a@example.com 注册，又在 video.example.com 用同一邮箱注册。应当是同一账号还是两个账号？

## 决策

```text
unique(siteId, emailNormalized)
unique(siteId, provider, providerSubject)
unique(siteId, personalOwnerUserId)
同邮箱在不同站点创建不同 User。每个 User 在站点内有唯一 personal workspace。
```

## 理由

```text
邮箱是登录凭证，不是跨产品身份，可代表不同使用意图和隐私上下文。
免费额度、套餐、风控状态都应按站点独立，避免跨站污染。
白标客户不能看到"同邮箱已在其他产品存在"。
按产品独立统计获客/留存/转化，LTV 分析清晰。
```

## 约束

```text
emailNormalized 按 siteId 唯一，非全局唯一。
跨站账号绑定（统一积分/订阅）必须通过显式 AccountLink 等能力实现，不能默认。
风险信号可平台级聚合（见 ADR），但业务身份永远 site scoped。
```

## 替代方案（已否决）

```text
全局邮箱唯一，多 site 自动合并   破坏站点独立性，体验混乱。
全局账号 + site 分身             复杂度高，多数用户不需要跨站身份。
```

## 影响

P0 回填现有 User 的 default site；新增 ExternalIdentity 表记录 provider/providerSubject/userId；新增上述 unique 约束；老 API 灰度废弃。

相关：[ADR-001 站点边界](ADR-001-site-boundary.md)、[user-register-login 链路](../business-flows/user-register-login.md)。
