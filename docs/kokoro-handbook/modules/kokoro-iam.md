# kokoro-iam

> 执行级设计以 [IAM 设计卡](../technical/backend-design/01-iam.md) 为准。

状态：目标架构已确认，PostgreSQL owner schema 已落地，子仓重构实施中。

## 1. 职责

`kokoro-iam` 是一个安全上下文，统一拥有：

```text
Identity
Organization
Authentication
Authorization
Audit
```

它不拥有 Conversation、Agent Run、Model Catalog、Capability、Entitlement 或 Payment。

Site 是产品站点/Realm；Organization 是 Site 内的租户/安全空间；Project 是后续可选业务
分组。这三个概念不同。每个 Web 套皮/套壳部署通过服务端 env 选择 Site，IAM 不负责选择，
只验证并固化 Site 安全上下文，因此不建立独立 Site 子仓库或运行服务。

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
└── package.json
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

Web 调用 Authentication 时注入其服务端 env 绑定的 SiteContext；Chat 只能调用
Authorization；JWKS 是公开密钥材料。Caller
身份在解码业务 payload 前验证。

### 5.1 GA 运行身份：IAM 给主体事实，GA 自己做隔离

Agent 运行不把 IAM 的用户、组织或项目 ID 直接改名为 `namespace`。一次被受理的产品执行使用 Root generated contract 的
窄 envelope：

```text
ExecutionIdentity
  actor: ActorRef(person | service, opaque_ref)
  subject: ExecutionSubjectRef(personal | project | service, opaque_ref)
  identity_assertion_ref: service-only current IAM assertion handle
```

IAM/Entry/Session 的责任是：认证调用者、确认 actor 可代表本次 subject、并为服务间验证绑定 assertion。Session 将该受信
envelope 与 `session_id`、`feature_key`、输入和 opaque AssetRef 一起放入 Root `LaunchRunRequest`；它不保存或选择
`RuntimeNamespace`，也不传独立 `thread_id`。

GA 的唯一 ingress `RuntimeIdentityResolver` 以受控 canonical tenant + subject 和 GA key material 派生内部、不透明的
`RuntimeNamespace`，只用于 GA checkpoint、RunLedger、workbench 与 thread gate。IAM 不调用 GA、不维护该值；GA 不维护
membership/role，不把 actor/subject 解释成 Agent、graph、Skill 或权限配置。Capability、Storage、Studio 在具体 public operation
时通过 attestation 和自己当前的 owner facts 重新判断，而不是复用一份 Session grant snapshot。

这一层不是额外 Principal 表或新的 IAM 领域实体；它是跨服务 command 的受信身份上下文。完整 Root 字段和恢复语义以
[GA 公共运行契约](../technical/38-ga-public-runtime-contract.md) 与
[ADR-022](../decisions/ADR-022-run-execution-attestation-and-dynamic-capability-resolution.md) 为准。

## 6. Web SiteContext

同一份 Web 代码和镜像可以多次部署：

```text
Web Shell A: KOKORO_SITE_ID=site-a + A 品牌配置
Web Shell B: KOKORO_SITE_ID=site-b + B 品牌配置
Web Shell C: KOKORO_SITE_ID=site-c + C 品牌配置
```

`KOKORO_SITE_ID` 是 Web/BFF 服务端运行时配置，不依赖浏览器 request body。Site ID 不是
秘密，可以进入页面 SiteContext，但 IAM 必须以受信 Web 调用和数据库中的 active Site 记录
重新验证，不能让浏览器切换为其他 Site。

`site_site` 保存 FK 根、状态和必要元数据；Web 的皮肤、文案和静态品牌配置可以由各套壳部署
管理。动态域名目录和一套 Web runtime 服务多个 Site 不属于首发。

## 7. 迁移原则

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

## 8. 完成门禁

- 登录到 personal Organization 的真实 PostgreSQL 事务通过；
- Refresh/Logout/GetSession/Authorize 真实闭环；
- JWT/JWKS 和 method-level workload caller matrix 通过；
- 并发 Magic Link、refresh rotation 和 membership/session 负向测试通过；
- 重启和丢响应恢复通过；
- 全部 active source 进入 test/typecheck/lint/build；
- 旧 MySQL/HTTP/Admin authority zero-call；
- fresh/local PostgreSQL、本地 `pnpm dev`、RPC interoperability 通过；
- 只有一个入口和一套权威领域模型。

Dockerfile 和 Compose 不属于当前 IAM 业务闭环门禁；本地进程闭环稳定后再进入交付阶段。
