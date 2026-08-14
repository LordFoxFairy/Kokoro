# kokoro-iam

状态：目标架构已确认，PostgreSQL owner schema 已落地，子仓重构实施中。

## 1. 职责

`kokoro-iam` 是一个安全上下文，统一拥有：

```text
Site
Identity
Organization
Authentication
Authorization
Audit
```

它不拥有 Conversation、Agent Run、Model Catalog、Capability、Entitlement 或 Payment。

Site 是产品站点/Realm；Organization 是 Site 内的租户/安全空间；Project 是后续可选业务
分组。这三个概念不同，但 Site 当前规模小且与登录和租户约束强耦合，因此不单独拆仓。

## 2. Slice A 表所有权

| 模块 | 表 |
|---|---|
| Site | `site_site`、`site_domain` |
| Identity | `iam_principal`、`iam_user`、`iam_identity`、`iam_contact` |
| Organization | `iam_organization`、`iam_membership` |
| Authorization | `iam_role`、`iam_permission`、`iam_role_permission`、`iam_membership_role` |
| Authentication | `iam_magic_link`、`iam_auth_session` |
| Application | `iam_command_receipt` |
| Audit | `iam_security_event` |

Root 是这些表的 DDL authority；IAM 是唯一 runtime writer。

## 3. 目标目录

```text
kokoro-iam/
├── src/
│   ├── domain/
│   │   ├── site/
│   │   │   ├── entities/
│   │   │   ├── value-objects/
│   │   │   └── repositories/
│   │   ├── identity/
│   │   │   ├── entities/
│   │   │   ├── value-objects/
│   │   │   ├── services/
│   │   │   ├── repositories/
│   │   │   └── events/
│   │   ├── organization/
│   │   │   ├── entities/
│   │   │   ├── value-objects/
│   │   │   ├── services/
│   │   │   ├── repositories/
│   │   │   └── events/
│   │   ├── authentication/
│   │   │   ├── entities/
│   │   │   ├── value-objects/
│   │   │   ├── services/
│   │   │   ├── repositories/
│   │   │   └── events/
│   │   ├── authorization/
│   │   │   ├── entities/
│   │   │   ├── value-objects/
│   │   │   ├── services/
│   │   │   ├── repositories/
│   │   │   └── events/
│   │   └── audit/
│   │       ├── events/
│   │       └── repositories/
│   ├── application/
│   │   ├── site/
│   │   │   ├── commands/
│   │   │   └── queries/
│   │   ├── authentication/
│   │   │   ├── commands/
│   │   │   └── queries/
│   │   ├── identity/commands/
│   │   ├── organization/commands/
│   │   ├── authorization/
│   │   │   ├── commands/
│   │   │   └── queries/
│   │   ├── idempotency/
│   │   └── ports/
│   ├── infrastructure/
│   │   ├── persistence/postgres/
│   │   ├── security/
│   │   ├── messaging/
│   │   └── config/
│   ├── interfaces/
│   │   ├── rpc/
│   │   └── http/
│   ├── generated/proto/
│   ├── bootstrap.ts
│   └── main.ts
├── prisma/schema.prisma
├── test/
│   ├── unit/
│   ├── integration/postgres/
│   ├── contract/rpc/
│   └── architecture/
└── Dockerfile
```

目录按真实文件渐进创建；不创建空 `services/events` 目录。`entities/value-objects` 只位于
具体业务模块内部。

## 4. 关键应用事务

`ConsumeMagicLink` 在一个 IAM 本地事务中完成：

```text
claim CommandReceipt
-> consume MagicLink
-> ensure Identity/Contact
-> ensure Principal/User
-> ensure Personal Organization
-> ensure Owner Membership
-> ensure personal_owner Role/Permission bindings
-> create AuthSession
-> append SecurityEvent
-> commit
-> sign access JWT and derive refresh token
```

`RefreshSession` 锁定 refresh family，创建唯一 successor，并在同一事务写 rotation、receipt
和 SecurityEvent。旧 token 携新 command 重放时撤销 family；相同 command/digest 丢响应重试
返回同一 session 和可重导 refresh token。

`Authorize` 校验 JWT、active AuthSession、Site/Organization/Principal binding、Membership、Role
和 active Permission。禁用 Membership 或 Permission 后不得继续授权。

## 5. 公开接口

Slice A 只公开：

```text
SiteService
  ResolveSiteByHost
  GetSite

IamAuthenticationService
  RequestMagicLink
  ConsumeMagicLink
  RefreshSession
  Logout
  GetSession

IamAuthorizationService
  Authorize

HTTP
  GET /.well-known/jwks.json
```

Web 可以调用 Site 和 Authentication；Chat 只能调用 Authorization；JWKS 是公开密钥材料。Caller
身份在解码业务 payload 前验证。

## 6. 迁移原则

| 旧能力 | 裁决 |
|---|---|
| Magic Link nonce、单次消费、存在隐藏、限流 | 保留行为，迁移实现 |
| Refresh lost-response replay 与 reuse detection | 保留 |
| JWT/JWKS | 保留行为，重接基础设施 |
| User/Profile | 移入 Identity |
| Team/Membership | Team 统一为 Organization，Membership 保留 |
| Role/Permission | 移入 Authorization |
| MySQL repositories/migrations | PostgreSQL parity 后删除 |
| 旧 HTTP/BFF/Admin 业务路由 | RPC parity 后删除 |
| `userPlatformModule` | 删除 |
| 重复 MagicLink/RefreshToken 模型 | 合并为唯一 Domain 模型 |

禁止在 parity 前删除成熟行为，也禁止通过缩小 tsconfig/test/lint 范围绕过旧代码。

## 7. 完成门禁

- 登录到 personal Organization 的真实 PostgreSQL 事务通过；
- Refresh/Logout/GetSession/Authorize 真实闭环；
- JWT/JWKS 和 method-level workload caller matrix 通过；
- 并发 Magic Link、refresh rotation 和 membership/session 负向测试通过；
- 重启和丢响应恢复通过；
- 全部 active source 进入 test/typecheck/lint/build；
- 旧 MySQL/HTTP/Admin authority zero-call；
- fresh PostgreSQL、Docker、RPC interoperability 通过；
- 只有一个入口和一套权威领域模型。
