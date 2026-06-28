# User Register / Login 链路

## 目标

在当前站点内创建或确认一个 User，并初始化它的身份、personal workspace 和成员关系。核心约束：同邮箱、同 OAuth subject 跨站默认不合并，每个站点是独立账号。

## 参与模块

```text
kokoro-site                    提供 SiteContext（siteId 已确定）。
kokoro-user                    身份、workspace、成员、审计权威，执行 ensure。
kokoro-credit                  首次注册可由免费套餐链路 grant 免费额度（不在本链路写余额）。
```

## 前置条件

```text
SiteContext 已解析，siteId 通过 x-kokoro-site-id 传入。
登录方为邮箱或 OAuth provider identity。
```

## 主流程

```text
1. Ensure
   POST /users/ensure
   headers: x-kokoro-site-id
   body: email 或 provider identity（provider, providerSubject, emailAtProvider）。

2. 查重
   邮箱:  按 unique(siteId, emailNormalized) 查 User。
   OAuth: 按 unique(siteId, provider, providerSubject) 查 ExternalIdentity。

3. 命中 -> 返回已有 User（幂等）；未命中 -> 创建：
   User(siteId, emailNormalized, status=active)
   ExternalIdentity(siteId, userId, provider, providerSubject)（OAuth 登录时）
   Workspace(siteId, type=personal, ownerUserId)
   Membership(siteId, workspaceId, userId, role=owner)

4. 返回
   User + personal Workspace + owner Membership。

5. 审计
   写 UserAuditLog(user.ensure / workspace.create)，带 siteId, requestId, actor, target。
```

## 异常流程

```text
同邮箱跨站         music 与 video 各建独立 User，绝不合并（P2）。
同 OAuth subject 跨站   各站独立 ExternalIdentity -> 独立 User。
slug 冲突         personal workspace 受 unique(siteId, slug) 与 unique(siteId, personalOwnerUserId) 约束。
缺 siteId         user 写操作拒绝（site-resolution 失败时不进入本链路）。
站点禁用          写入拒绝。
```

## 数据变化

```text
User              新增（unique(siteId, emailNormalized)）。
ExternalIdentity  OAuth 登录新增（unique(siteId, provider, providerSubject)）。
Workspace         新增 personal workspace（unique(siteId, personalOwnerUserId)）。
Membership        新增 owner（unique(siteId, workspaceId, userId)）。
UserAuditLog      写 user.ensure / workspace.create。
```

## 幂等和一致性

```text
ensure            按 unique(siteId, emailNormalized) / unique(siteId, provider, providerSubject) 天然幂等：
                  重复调用返回同一 User，不重复建 workspace。
requestId         审计与追踪关联。
强一致            User + ExternalIdentity + Workspace + Membership 在同事务内创建。
```

## 用户可见结果

```text
首次注册   建站内账号 + personal workspace，可触发免费额度发放。
再次登录   命中已有账号，无重复创建。
跨站注册   同邮箱在另一站是全新账号，额度、套餐、workspace 互不影响。
```

## 验收标准

```text
同邮箱在两个 site 注册得到两个 User。
同 OAuth subject 在两个 site 登录得到两个 User。
personal workspace 在两个 site 各一份。
重复 ensure 不重复建 workspace。
site A 的 userId 不能访问 site B workspace。
```

## 相关

```text
原则     ../decisions/ADR-002-user-identity.md
前置     ./site-resolution.md
后续     ./payment-to-credit.md（订单与积分发放）
```
