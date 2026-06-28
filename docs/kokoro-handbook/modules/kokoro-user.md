# kokoro-user 技术方案

## 定位

kokoro-user 是站点内身份、团队/workspace、成员、权限、服务账号和审计的权威模块。

它的核心判断：User 是站点内用户，不是全局邮箱账号。同邮箱在不同 siteId 下默认是不同 User。

实现状态：users/teams/memberships/roles/invites/service_accounts/user_audit_logs 表已建，ensure/me-teams 最小接口已实现；站点化（全字段加 siteId）、workspace 重构、权限 key、邀请/成员管理 API 为规划。

## 业务职责

owns：

```text
User             站点内用户。
ExternalIdentity OAuth 等外部身份绑定。
Team/Workspace   personal 与 team 两类。
Membership       用户在 workspace 的角色。
Role/Permission  角色与权限 key。
Invite           成员邀请。
ServiceAccount   API key / 服务账号。
UserAuditLog     身份相关写操作审计。
```

does not own：

```text
积分余额（kokoro-credit）。
支付订单（kokoro-payment）。
模型 provider secret（kokoro-model）。
agent session、artifact（运行时仓库）。
站点事实与 host 解析（kokoro-site）。
```

## 上游和下游

```text
上游（调用 user）：
  入口/web/admin   /users/ensure、/me/teams、成员与邀请管理。

下游（user 调用）：
  kokoro-site      消费 siteId / SiteContext（不自己解析 host）。

user 不直接改余额、不直接创建订单。它向 credit/payment 提供身份上下文：
  siteId / userId / workspaceId / membershipRole / permission context。
```

## 核心对象

```text
User             siteId, emailNormalized, emailVerifiedAt, displayName, avatarUrl,
                 status(active|disabled|deleted), disabledAt, deletedAt, lastSeenAt, metadata。
ExternalIdentity siteId, userId, provider, providerSubject, emailAtProvider, linkedAt。
Workspace        siteId, name, slug, type(personal|team), ownerUserId, personalOwnerUserId, status。
Membership       siteId, workspaceId, userId, role(owner|admin|member), status。
Role             siteId, workspaceId, key, permissions, status。
Invite           siteId, workspaceId, emailNormalized, role, tokenHash, status, expiresAt。
ServiceAccount   siteId, workspaceId, ownerUserId, name, tokenPrefix, secretHash, status。
UserAuditLog     siteId, actorUserId, actorService, workspaceId, action, targetType, targetId, requestId, metadata。
```

行为约定：

```text
同邮箱跨站默认创建不同 User。
每个站点有自己的 personal workspace。
站点封禁/注销/禁用只影响当前站点。
跨站账号绑定以后通过显式 AccountLink 做，不默认合并。
```

## 数据模型

MySQL（Prisma，已实现）：

```text
users
teams
memberships
roles
invites
service_accounts
user_audit_logs
```

站点化关键字段（规划，全部加 siteId）：

```text
User.siteId / User.emailNormalized
ExternalIdentity.siteId
Team.siteId / Membership.siteId / Role.siteId?
Invite.siteId / ServiceAccount.siteId / UserAuditLog.siteId
```

唯一约束（规划）：

```text
unique(siteId, emailNormalized)
unique(siteId, provider, providerSubject)
unique(siteId, personalOwnerUserId)
unique(siteId, teamId/workspaceId, userId)
```

其它存储：

```text
Mongo / Redis / 对象存储 / 外部系统：当前不使用。
```

## API / RPC / Events

已实现：

```text
GET  /healthz
POST /users/ensure
GET  /me/teams
```

规划补齐：

```text
POST /users/ensure                  必须带 siteId 或 SiteContext header，返回 User + personal workspace + owner membership。
GET  /me/teams                      必须按 siteId 过滤。
POST /teams                         创建 team workspace。
PATCH /teams/:id
POST /invites                       邀请成员。
POST /invites/accept                必须匹配 siteId。
PATCH /memberships/:id              改角色。
DELETE /memberships/:id
POST /service-accounts
POST /service-accounts/:id/rotate
POST /service-accounts/:id/revoke
```

```text
幂等  同 site 同邮箱 /users/ensure 幂等返回同一 user。
```

## Admin 管理

```text
basePath  /admin/users
resources users / teams / memberships / service-accounts
权限 key  owner / admin / member（第一阶段简单角色）；
          后续 permission key：site.admin.manage / workspace.member.manage /
          payment.order.read / credit.adjust / model.provider.manage /
          artifact.publish / seo.page.manage。
操作      用户禁用、workspace 创建/禁用、邀请、改角色、服务账号轮换。
审计      所有写操作写 UserAuditLog，必须带 siteId / requestId / actor / target。
          覆盖动作：user.ensure / user.disable / workspace.create / workspace.disable /
          invite.create / invite.accept / membership.role_change /
          service_account.create / service_account.rotate。
```

后台查询默认带 siteId，仅 platform root admin 可跨站查询。

## 业务链路

```text
user-ensure        登录/注册 -> ensure User + personal workspace + owner membership。
invite-accept      邀请加入 team workspace（必须匹配 siteId）。
identity-to-credit user 提供身份上下文，credit/payment 自行业务判断。
```

详见 [ADR-002 同邮箱跨站默认不同用户](../decisions/ADR-002-user-identity.md)。

## 部署

```text
服务名   kokoro-user
端口     4211
env      DATABASE_URL_USER, KOKORO_USER_PORT, KOKORO_USER_BASE_URL, KOKORO_SITE_BASE_URL
多 Pod   权威状态在 MySQL，可多副本。
```

## 测试

```text
集成    同 site 同邮箱幂等返回同一 user。
反例    同邮箱不同 site 创建两个 user；同 OAuth subject 不同 site 两个 user；
        /me/teams 不返回其它 site 的 team；personal workspace 每 site 唯一；
        service account token 不跨 site 生效。
```

## 风险和边界

```text
最大风险是过早做全局用户合并。解决：先用 siteId + emailNormalized，未来再显式引入 AccountLink。
保留全局 externalUserId unique 会让多站点同 OAuth subject 被错误合并。
workspace 不带 siteId 会让后台和 artifact 串站。
invite token 不绑 siteId 可能跨站接受邀请。
service account 不带 siteId 会让 API key 权限越界。
```

## 后续任务

```text
P0  站点化迁移（新增 siteId 字段回填 default site；新建 ExternalIdentity 表回填 externalUserId；
    建 site scoped 唯一约束；弱化全局 unique externalUserId）。
P1  team/invite/membership/service-account 管理 API；permission key 体系。
P2  显式 AccountLink 跨站绑定。
```
