# Wave 1 Platform / Identity / Site / Policy 可实施设计

> 日期：2026-07-28
>
> 状态：`internally-approved`；架构决策与独立内部评审均已闭合
>
> implementationAuthorized: `true`
>
> gaRuntimeSemanticChangeAuthorized: `false`
>
> 父设计：`2026-07-25-platform-web-session-target-architecture-design.md` v1.5
>
> 首发档：`core-redeem-chat@1`
>
> 适用仓：Root、`kokoro-platform`、`kokoro-web`；GA 仅做契约回归，不改语义，现有
> `run.request`/`run.cancel` wire 保持字节级不变

## 1. 本文裁决什么

本文是 Wave 1 子架构，不重述 Umbrella。它把以下 P0 变成实现约束：

1. `core-redeem-chat@1` 是唯一首发产品面，不存在运行时偷偷开启的购买、协作或 OAuth。
2. 一个 Site 对应一个独立 Web project/repository、lock、CI、artifact、deployment 与 release。
3. Platform 是一个独立子仓、一个控制面产品、一个 bounded context；Site、Identity、Workspace、
   Catalog、Commerce/Credit、ModelControl、Admin、Audit 通过 owner-scoped application port、显式 workflow 和
   同一 Unit of Work 协作，任何模块都拿不到跨 owner 的 raw Prisma transaction。
4. Site 产品身份和用户/操作员身份分离为 `RequestSecurityContext`，所有副作用在 effect point 重新授权。
5. 账号、会话、个人 Workspace、账务与数据权利默认按 Site 隔离。
6. Site publish 由 immutable `SiteRelease`、Profile/brand/SEO digest 与 CAS active pointer 驱动。
7. Admin 的 Site/Global/BreakGlass scope、environment/region/device 授权轴、OIDC、maker/checker、自升级禁止、
   审批/执行/审计原子性有唯一语义。
8. redeem-only 通过七层关闭新购 Payment surface，而不是只隐藏按钮。
9. 旧 MySQL/多进程 self-RPC/Host 换皮/Magic Link/Team/Payment 入口按唯一 owner wave clean replace，不做兼容层；
   ModelControl 在 W1 完成迁移，Redeem/Fulfillment/Credit authority 由 W2A 唯一实现。
10. 每项结论必须由真实 PostgreSQL、两套独立 Site project 和负向安全测试证明。

本文没有待裁决 P0。文末风险均有默认处理，不是 TODO。

## 2. 首发能力与非目标

### 2.1 `core-redeem-chat@1` 启用

- Site-bound 邮箱 + password 注册/验证/登录、password change/reset、TOTP enrollment/challenge/disable、
  recovery-code lifecycle、full AccountRecovery、email change、device/session list/revoke 与删除前 re-auth。
- 个人 Workspace、owner Membership、BillingAccount、默认 Project、ExecutionSpace。
- Account、Redeem、Credit balance/ledger；W1 只建立 personal BillingAccount bootstrap 与调用边界，
  Redemption/Fulfillment/Grant/Journal/Hold 的唯一实现和认证属于 W2A。
- Chat、父设计允许的安全附件、最小 Library。
- Notification、Support、Core Admin、Data Rights。
- Site project 的品牌、SEO、营销、法务静态内容与发布/回滚。

### 2.2 在此 Profile 禁用

- checkout、新订单、订阅、支付 provider、退款、争议等新资金获取链路。
- 用户 Magic Link 登录、OAuth/OIDC、Passkey、企业 SSO。
- Team 邀请/成员/切换、共享 Workspace、协作角色。
- Studio、Public Share、高级 agent surface。
- 可由客户端、Site key、feature flag 或缺失配置绕开的隐式能力。

Admin OIDC 是控制面强认证，不属于上面“用户 OIDC 禁用”。Credit/Redeem 是首发能力，
不因 Payment acquisition 被关闭而关闭；但它们在 W2A 通过前不会被 W1 单独宣称可上线。

## 3. 当前代码事实与 replacement verdict

| 当前事实 | 代码位置 | Wave 1 verdict |
|---|---|---|
| Site/User/Model/Admin/Credit/Payment 各自 MySQL、进程和 base URL | `kokoro-platform/kokoro-*/prisma/schema.prisma`、各 `src/main.ts` | Site/User/Model/Admin 在 W1 clean replace 为单 Platform API/Worker + `DATABASE_URL_PLATFORM`；Credit 在 W2A 原子切换 |
| 同 Platform 模块用 `callService`、caller secret、可伪造 context header 互调 | `kokoro-platform-kit/src/http/{request-context,internal-client,route-access}.ts` | 只允许真正远程边界使用；Platform 内改本地 typed port/UoW |
| Site 以 Host 查 mutable brand/SEO，支持 upsert/delete/restore/rebind | `kokoro-site/src/**`、`/site-context/resolve` | 删除；改 workload binding exchange + immutable release/pointer |
| User 以 `(siteId, externalUserId)`、Team、MagicLink、namespace refresh 为核心 | `kokoro-user/prisma/schema.prisma`、`src/**` | 删除；改 Site-local User、AuthSession/family、personal Workspace |
| Web cookie 混入 runtime JWT、refresh、namespace、siteId | `apps/user/src/lib/server/session-envelope.ts` | 删除；cookie 只装 opaque AuthSession/refresh credential |
| auth 即使 strict Site resolve 失败也退 `KOKORO_SITE_ID` | `apps/user/src/lib/server/site.ts` 的 `resolveSiteId` | 删除；绑定/域名/会话不一致一律 fail closed |
| 用户 Web 是 Magic Link，探针异常和 preview fail open | `apps/user/src/app/api/auth/**`、`ui/auth/**` | 删除；password/TOTP，生产无 preview auth bypass |
| Team、checkout、mock pay 路由可达 | `apps/user/src/app/api/{team,billing}/**` | 删除 route、UI、client、test 与 env，不留 501 假入口 |
| Admin Web 用邮件 Magic Link；Platform 还支持 dev/proxy auth | `apps/admin/auth.ts`、`kokoro-platform-admin/src/auth.ts` | 生产与 production-like 仅 OIDC Authorization Code + PKCE |
| Admin 用 `*` JSON 表示 scope，角色/操作员可直接 upsert | `kokoro-platform-admin/src/rbac.ts`、`server.ts` | typed `SiteScope`/`GlobalScope`/`BreakGlassScope` + environment/region/device；权限变更受审批且禁止自升级 |
| 审批先 claim，远程执行，再单独写状态/审计 | `kokoro-platform-admin/src/approval.ts`、`gateway.ts` | Platform 本地命令 + 同一 PostgreSQL transaction；外部 effect 用 durable intent |

当前 MySQL 集成测试证明的是旧实现，不是本文验收证据。

## 4. Platform 形态与代码边界

### 4.1 唯一 Platform 产品

`kokoro-platform` 是独立 Git 子仓和唯一控制面产品。目标目录固定为：

```text
kokoro-platform/
  prisma/schema.prisma
  prisma/migrations/
  src/modules/{site,identity,workspace,catalog,commerce,credit,model-control,admin,policy,audit}/
    domain/
    application/{contracts,services}/
    infrastructure/postgres/
    INDEX.md
  src/workflows/{registration,site-lifecycle,admin-command}/
  src/shared/{unit-of-work,outbox-inbox,security-context,observability}/
  src/infrastructure/postgres/
  src/interfaces/http/          # Site Web ordinary OpenAPI/HTTP
  src/interfaces/connect/       # privileged Admin/admission contracts
  src/process/api.ts
  src/process/worker.ts
```

API 与 Worker 可作为两个 process role 独立伸缩，但共享同一代码、Platform schema、application port、
domain invariant 与 Unit of Work。不得把 `site/user/catalog/commerce/credit/admin` 再部署成互相 HTTP 的
微服务，也不得保留它们的 `*_BASE_URL` 作为本地调用开关。

### 4.2 本地与远程调用规则

- Platform 内：构造函数注入 typed application port；mutation 传入同一 `PlatformTransaction`。
- 跨 Git 仓：只用 Root contract 生成的 versioned HTTP/RPC/SSE；禁止 sibling source import。
- Site Web → Platform：ordinary versioned OpenAPI/HTTP，workload identity + browser actor credential。
- Admin Web → Platform：versioned Connect/RPC，OIDC operator session + Admin workload identity。
- Platform → Session/Job：versioned RPC/HTTP；W1 只冻结 contract/Policy shell。GA 仍只接收现有
  `run.request`/`run.cancel`，不接收任何新增 grant/auth/credit field。
- Hub、Model Gateway、Job 等确需独立扩缩/隔离的 context 保留远程边界。
- 远程 provider 结果永远不包在 PostgreSQL transaction 中；用 intent/receipt/reconcile。
- 同一 remote operation 只有一个权威 transport，不提供 HTTP 与 RPC 双写通道。

`PlatformTransaction` 是只允许 UoW 装配器识别的 opaque capability，不是 Prisma client、ORM model 或通用
repository locator。每个 owner module 只能由自己的 repository factory 把该 capability 解析成私有 repository；
workflow 只拿 transaction-scoped owner ports。禁止 module import 另一 module 的 `infrastructure/`、Prisma model、
private table 或 repository，也禁止 factory 把任意 repository 暴露给 application service。

依赖方向固定为 `interfaces/process -> workflows/application -> domain`，infrastructure 只实现向内 contract；
domain 不 import framework/ORM/transport。`src/workflows` 是跨 module 强事务的唯一 owner，普通 module application
service 不得直接写另一 module 的表。架构测试同时扫描 import graph、公开 barrel、table owner 和 transaction-handle
泄漏；仅禁止 `fetch/callService` 不足以通过 W1 gate。

### 4.3 首批 application ports

```ts
interface SiteApplication {
  requestSite(cmd, ctx, tx): Promise<SiteRequestReceipt>
  provisionSite(cmd, ctx): Promise<ProvisioningReceipt>
  exchangeProductContext(cmd, caller): Promise<TrustedProductContext>
  createRelease(cmd, ctx, tx): Promise<SiteRelease>
  activateRelease(cmd, ctx): Promise<ActivationReceipt>
  suspendSite(cmd, ctx, tx): Promise<SuspensionReceipt>
  resumeSite(cmd, ctx): Promise<ActivationReceipt>
  planDecommission(cmd, ctx, tx): Promise<DecommissionPlan>
  cancelDecommission(cmd, ctx, tx): Promise<DecommissionReceipt>
  executeDecommission(cmd, ctx): Promise<DecommissionReceipt>
}

interface IdentityApplication {
  beginRegistration(cmd, ctx, tx): Promise<AuthTransaction>
  verifyEmailAndActivate(cmd, ctx, tx): Promise<IdentityActivationReceipt>
  authenticatePassword(cmd, ctx, tx): Promise<AuthSessionReceipt>
  beginPasswordReset(cmd, ctx, tx): Promise<AuthTransaction>
  completePasswordReset(cmd, ctx, tx): Promise<CredentialChangeReceipt>
  changePassword(cmd, ctx, tx): Promise<CredentialChangeReceipt>
  beginEmailChange(cmd, ctx, tx): Promise<AuthTransaction>
  completeEmailChange(cmd, ctx, tx): Promise<IdentifierChangeReceipt>
  beginTotpEnrollment(cmd, ctx, tx): Promise<AuthenticatorEnrollment>
  confirmTotpEnrollment(cmd, ctx, tx): Promise<AuthenticatorReceipt>
  disableTotp(cmd, ctx, tx): Promise<AuthenticatorReceipt>
  regenerateRecoveryCodes(cmd, ctx, tx): Promise<RecoveryCodeReceipt>
  beginAccountRecovery(cmd, ctx, tx): Promise<RecoveryTransaction>
  completeAccountRecovery(cmd, ctx, tx): Promise<RecoveryReceipt>
  refresh(cmd, ctx, tx): Promise<AuthSessionReceipt>
  revokeSession(cmd, ctx, tx): Promise<void>
  disableUser(cmd, ctx, tx): Promise<void>
}

interface PersonalWorkspaceBootstrap {
  createForUser(input, tx): Promise<PersonalBootstrapReceipt>
}

interface CommerceBootstrap {
  createRedeemOnlyBillingAccount(input, tx): Promise<BillingAccountRef>
}

interface ModelControlApplication {
  importLegacyCatalog(input, ctx, tx): Promise<ModelCatalogImportReceipt>
  readAuthorizedCatalog(query, ctx): Promise<ModelCatalogProjection>
  publishAssignment(command, ctx, tx): Promise<ModelAssignmentReceipt>
}

interface AdminCommandBus {
  prepare(command, ctx, tx): Promise<PreparedAdminCommand>
  executePrepared(approvalId, ctx, tx): Promise<CommandReceipt>
}
```

这些接口只暴露 domain DTO/ID/receipt；`tx` 是 opaque capability，不得暴露 Prisma model/client、Fastify request、
fetch response 或 GA 类型。Redeem/Fulfillment/Credit mutation ports 不在本文重复定义，以 W2A 为唯一 authority。

## 5. 数据库裁决：PostgreSQL 18 是唯一 Platform 真源

### 5.1 冲突裁决

`docs/kokoro-handbook/decisions/ADR-005-mysql-and-mongo.md` 的“Platform 使用 MySQL、不引入
PostgreSQL”被父目标与本文 **supersede**。Wave 1 Platform 唯一默认数据库为 PostgreSQL 18：

```text
DATABASE_URL_PLATFORM=postgresql://.../kokoro_platform
schema=platform
```

不再支持 `DATABASE_URL_SITE|USER|MODEL|CREDIT|PAYMENT|ADMIN`，不再启动 MySQL。选择 PostgreSQL 的原因：

- 系统未上线，可 clean replace，没有生产双写或在线迁移收益。
- registration + personal bootstrap、Admin approval + mutation + audit、release pointer + outbox 要跨模块强事务。
- Site active domain、active release、登录标识等需要 partial unique constraint。
- immutable manifest/command snapshot 需要 JSONB、digest check 与可查询审计。
- 一个 Platform 数据库/连接池比六个 MySQL service DB 更快落地，也消除 self-RPC partial failure。

MongoDB 不与 PostgreSQL 争夺 Platform 事实：它仅保留在 GA checkpoint/memory 与独立 Hub 等父设计明确的
运行时 context；Session 目标真源同样是 PostgreSQL，不得在 W1 文档重新引入 Mongo 双口径。Redis 不是真源，
对象存储只保存 blob/immutable artifact。MySQL 从默认 infra 清退。

本文进入 `internally-approved` 之前必须新增替代 ADR-012，并把 ADR-005 状态改为
`superseded-by-ADR-012` 后双向回链。ADR-012 至少冻结：Platform/Session 使用 PostgreSQL 18、GA checkpoint 与
Hub 的 Mongo owner 不变、同 Platform schema 与 module table ownership 的取舍、API/Worker/migrator database role、
RPO/RTO、前向修复、默认 Infra 从 MySQL 切到 PostgreSQL，以及拒绝长期双写/双读。同步 handbook、父设计、
CODEBASE_MAP、INDEX、CI 和 runbook；合并门扫描旧“Platform MySQL”语句，不能长期留下两个真源。

父设计 §27 遗留的“一 Site 一独立 Web Project，但同一 Monorepo”必须在同一审批系列修正为：每个 production
Site 是根 workspace 之外的独立 source repository/project/lock/CI/artifact/deployment/release，只消费签名包；
`kokoro-web/apps/reference-site` 仅是 fixture。不得让冲突权威文档进入实现阶段。

### 5.2 PostgreSQL 使用规则

- 一个 Prisma 7 schema 和 migration owner；所有 Platform 表位于 `platform` schema。
- 一个 `PlatformUnitOfWork` 传递 transaction client；application 层禁止自己新开连接。
- 金额/credit 使用 `bigint` 最小单位；时间使用 `timestamptz`；不可变 payload 使用 JSONB + SHA-256 digest。
- 每个 command 有 `(environment, caller_identity, operation, idempotency_key)` unique 与 immutable request digest；
  digest 至少覆盖 contract version、region、Site/Global/BreakGlass scope、actor/target safe ref 与 canonical payload。
  同 identity 同 digest 返回同 receipt，同 identity 不同 digest 返回 conflict；不得因另一 Site 碰撞泄漏存在性。
- outbox 与业务事实同 transaction；consumer 用 `(consumer, event_id)` inbox unique 去重。
- migration 必须含 SQL check/partial unique；不能用 application pre-check 代替并发约束。
- Platform API role 无 migration/drop 权限；migrator role 无运行时流量权限；Worker 按 job 表收敛权限。

### 5.3 Deployable 与数据库角色

W1 必须新增并由 CI 校验 `deployables.yaml`，至少登记以下 process role；同一 image 不能抹掉角色边界：

| deployable | command / owner | database role | readiness / drain |
|---|---|---|---|
| Platform API | `src/process/api.ts` / Platform | DML + owner projection read，无 DDL | PostgreSQL/contract/security 可安全接收；HTTP graceful drain |
| Platform Worker | `src/process/worker.ts` / Platform | job/outbox claim + owner DML，无 DDL | lease/queue 可推进；停止 claim 后等待或交回 lease |
| Platform Migrator | one-shot Prisma/SQL migration / Data | migration DDL，无 runtime traffic | advisory lock、schema preflight、前向修复 receipt |
| Site Web | 每个独立 Site repository command / Site owner | 无 Platform DB role | binding/release/contract exact match；独立 drain/rollback |
| Admin Web | `kokoro-web` Admin artifact / Admin owner | 无 Platform DB role | OIDC/config/generated client ready；无业务 DB fallback |

manifest 还必须登记 image build root、inbound/outbound contract、secret class、audience、region/environment、scaling
key、SLO/runbook/release owner。生产 API/Worker 启动不得隐式 migrate；migrator 不加载 Site/User/Provider credential。

## 6. `RequestSecurityContext` 与 effect-point policy

### 6.1 唯一上下文

```ts
type RequestSecurityContext = {
  requestId: string
  correlationId: string
  trustedCaller: TrustedProductContext | TrustedAdminWorkloadContext | TrustedWorkerContext
  actor: AnonymousPrincipal | UserPrincipal | OperatorPrincipal | WorkloadPrincipal
  delegatedGrant: DelegatedExecutionGrant | null
  audience: string
  environment: EnvironmentId
  region: RegionId
  issuedAt: Instant
  expiresAt: Instant
}

type TrustedAdminWorkloadContext = {
  kind: "admin_workload"
  workloadIdentityId: WorkloadIdentityBindingId
  environment: EnvironmentId
  region: RegionId
  audience: string
  allowedOperations: string[]
  bindingEpoch: bigint
  issuedAt: Instant
  expiresAt: Instant
}

type TrustedWorkerContext = {
  kind: "platform_worker"
  workloadIdentityId: WorkloadIdentityBindingId
  processRole: string
  environment: EnvironmentId
  region: RegionId
  audience: string
  allowedOperations: string[]
  bindingEpoch: bigint
  issuedAt: Instant
  expiresAt: Instant
}

type TrustedProductContext = {
  bindingId: SiteProjectBindingId
  workloadIdentityId: WorkloadIdentityBindingId
  siteId: SiteId
  releaseId: SiteReleaseId
  environment: EnvironmentId
  region: RegionId
  audience: string
  allowedOperations: string[]
  siteSecurityEpoch: bigint
  bindingEpoch: bigint
  issuedAt: Instant
  expiresAt: Instant
}

type UserPrincipal = {
  kind: "user"
  userId: UserId
  authSessionId: AuthSessionId
  siteId: SiteId
  userSecurityEpoch: bigint
  sessionEpoch: bigint
  authenticationMethods: ("password" | "totp" | "recovery_code")[]
  authenticatedAt: Instant
}

type OperatorPrincipal = {
  kind: "operator"
  operatorId: OperatorId
  oidcIssuer: string
  oidcSubject: string
  sessionId: OperatorSessionId
  assuranceLevel: "phishing_resistant"
  factorClasses: NonEmptyArray<string>
  authenticatedAt: Instant
  stepUpAt: Instant | null
  managedDeviceRef: ManagedDeviceRef
  environment: EnvironmentId
  region: RegionId
  operatorSecurityEpoch: bigint
  sessionEpoch: bigint
  restrictionEpoch: bigint
}
```

`TrustedProductContext` 由 Platform 根据经验证的 workload identity、`SiteProjectBinding`、
`WorkloadIdentityBinding`、deployment/release 和 audience 交换。`Host`、`x-kokoro-site-id`、body 的
`siteId`、Web env 只能作为要交叉检查的 routing hint，不能生成权威上下文。

旧 `x-kokoro-principal` JSON、`x-kokoro-site-id` 透传和 caller-level shared secret 不能进入新 handler。
边界 adapter 验证后构造 typed context；application/domain 不读原始 header。

### 6.2 `CallerOperationPolicy`

每个 operation 在静态 registry 有且仅有一条策略：

```ts
type CallerOperationPolicy = {
  operation: OperationId
  allowedWorkloadKinds: WorkloadKind[]
  requiredAudience: string
  allowedActorKinds: ActorKind[]
  requiredProductOperations: string[]
  scopeRule: "same_site" | "same_workspace" | "explicit_global" | "explicit_breakglass"
  requiredAssurance: "anonymous" | "password" | "mfa" | "phishing_resistant"
  maxStepUpAgeSeconds: number | null
  managedDeviceRequired: boolean
  allowedEnvironments: EnvironmentId[]
  allowedRegions: RegionId[]
  riskClass: "normal" | "sensitive" | "irreversible"
  restrictionChecks: RestrictionCheck[]
  effectPoint: EffectPointId
}
```

默认 deny。route 名、HTTP method、UI visibility 和 permission glob 都不能替代 operation policy。

| operation family | caller / actor | scope | effect-point rule |
|---|---|---|---|
| `site.context.exchange` | bound Site Web workload / anonymous | binding 的单 Site | binding、release、domain、Site 均 active |
| `identity.registration.*` | bound Site Web / anonymous | same Site | Profile 允许 password；Risk 可用；challenge 未过期 |
| `identity.session.create` | bound Site Web / anonymous | same Site | User/Site/credential active；按策略要求 TOTP |
| `identity.session.refresh` | bound Site Web / session credential | same Site/session | family current generation；所有 epoch/status 再查 |
| `identity.session.revoke.*` | bound Site Web / same User | same Site/user | 仅 current/single/others/all 的明确 target |
| `workspace.personal.read` | bound Site Web / User | same Site/workspace | active owner membership + active Workspace |
| `redeem.apply` | bound Site Web / User | same Site/BillingAccount | code、account、profile、risk、idempotency 同 txn重验 |
| `chat.execution.prepare` | bound Site Web / User | same Site/workspace | 仅冻结 Policy shell；W2A+W3 qualified 前 unavailable，不 mint grant、不注册 effect route |
| `site.release.*` | Admin Web / Operator | explicit Site | permission + scope + step-up + approval policy |
| `admin.global.*` | Admin Web / Operator | explicit GlobalScope | phishing-resistant + step-up + maker/checker |
| `worker.site.reconcile` | Platform Worker workload | intent target | lease、attempt、epoch、desired state 一致 |

### 6.3 effect point

副作用前最后一步统一调用 `EffectAuthorizer.authorize(policy, context, resourceSnapshot, tx)`：

- 重查 Site/User/AuthSession/Membership/Binding 状态与 epoch，而不是信任路由入口的旧判断。
- 验证 audience、resource Site/Workspace、delegated grant subject、expiry、operation。
- sensitive/irreversible 操作要求 Risk `allow`；Risk timeout/unavailable 一律拒绝并写安全审计。
- 先授权再写业务事实；授权使用的行与 mutation 在同一 transaction 中锁定或以 version CAS。
- effect 完成同时写 `SecurityDecisionRecord`、command receipt 和 outbox。
- remote effect 的 effect point 是“提交 durable intent”；Worker 在真正调用 provider 前再次授权。

`PolicyDecisionToken` 可供 Session/Job → Platform 的远程 effect point 使用，TTL 不超过 60 秒，绑定 operation、
environment、region、siteId、workspaceId、subject、resource digest、request digest 和 epoch。敏感 effect 仍调用
versioned Admission RPC 做实时复核；
Admission 不可用 fail closed。该 token/delegated grant 永不序列化进 GA wire；GA 的既有 namespace 字段若存在，
仍按原 `run.request` contract 传递，不增加 Site/User/Workspace/authorization 语义。

### 6.4 Risk 两阶段决策

`RiskDecisionPort` 不得在 PostgreSQL transaction 内发网络请求。对 registration、login、recovery、redeem、
Admin sensitive/breakglass，边界 workflow 在开启 UoW 前获取短时、签名的 `RiskDecisionSnapshot`：

```text
riskDecisionId / policyRevision / decision=allow|challenge|deny
environment / region / operation / trusted Site or explicit platform scope
actor or anonymous subject ref / resource+request digest
riskEpoch / subject security epochs / issuedAt / expiresAt / signature key version
```

事务内 `EffectAuthorizer` 只锁本地 decision record、restriction/risk epoch 与目标 aggregate，验证签名、digest、
freshness 和 epoch 后再 mutation；过期或 epoch 变化就回滚并要求重新评估。Risk timeout、无效签名或 stale snapshot
在 sensitive/irreversible flow fail closed。Worker 对真实 remote effect 再取新 snapshot 或实时 Admission；不得复用
提交 intent 时已过期的 allow，也不得在 transaction 中 fetch Risk。

## 7. Site、独立项目与发布模型

### 7.1 Web project 决策

`kokoro-web` 只拥有：

- versioned、signed、brand-neutral `@kokoro/site-app-kit`；
- 与 Root generated contract 对齐的 `@kokoro/site-client`；
- `templates/site-web` scaffold；
- `apps/reference-site` 参考项目，仅作为 contract/E2E fixture，不是多 Site 生产 host。

每个生产 Site 由 scaffold 生成到独立 Site project/repository，拥有自己的 `package.json`、lockfile、CI、
source ownership、artifact digest、deployment、domain、release 与 rollback。它只消费 registry 中已签名的
immutable package。当前 `apps/user` 不得继续用 Host 在运行时换 brand 冒充多个 Site；实现时由
`apps/reference-site` 取代，首个真实 Site 另建独立 project。

Site 差异只能进入该 Site project 的 manifest/assets/content，或进入 Platform 的 versioned Profile/assignment。
共享 backend 禁止出现 `if (siteKey === ...)`、每站路由分支或 brand copy。

### 7.2 核心表与约束

| aggregate/table | 必需字段/约束 |
|---|---|
| `site` | `id,key,status,security_epoch,active_release_id,version`; `key` 永不复用 |
| `site_request` | requester、normalized request、approval state、idempotency/digest |
| `provisioning_attempt` | Site/project/domain intents、attempt state、lease、last observation |
| `site_project_binding` | `site_id,provider,project_ref,source_repo_ref,status,epoch`; active project ref unique |
| `workload_identity_binding` | `project_binding_id,principal_ref,audiences,environment,status,epoch` |
| `domain_binding` | normalized host、site、environment、verification、status、certificate ref |
| `site_config_revision` | immutable config JSONB/digest、creator、created_at |
| `launch_product_profile_revision` | `profile_key,revision,status,capability_inventory,digest`; immutable |
| `site_profile_assignment` | Site、profile revision、effective state；每 Site 仅一 active assignment |
| `site_release` | artifact/profile/config/brand/SEO/legal/route digests、state、certification ref |
| `site_deployment_binding` | release、provider deployment ref、environment、observed digest/state |
| `activation_attempt` | from/to release、state、idempotency、expected Site version、timestamps |
| `activation_observation` | append-only provider observation、digest、time |
| `suspension_policy_revision` | signup/auth/acquisition/admission、active work、Support、Data Rights、mandatory inbound 的独立处置 |
| `decommission_plan` | plan digest、reversible/irreversible fence、participant epochs、notification/export window、state |
| `decommission_participant_receipt` | owner、plan digest、retain/deidentify/revoke/GC disposition、state/evidence |
| `domain_ownership_history` | domain、旧 Site tombstone、新 binding proof/cooldown、时间线；append-only |
| `decommission_receipt` | tombstone、participant/GC completion、revoked binding、domain disposition、final digest |

关键 partial unique：

- `domain_binding(normalized_host) WHERE status IN ('pending','active')`；active/pending 期间不得 rebind。旧 Site 完成
  decommission 后，域名字面值只有经新 SiteRequest、重新证明控制权、takeover cooldown 和 maker/checker 才能绑定
  新 siteId；不得恢复旧账户/credential/data，历史 ownership 永久保留。
- 每 Site/environment 一个 active `site_project_binding`。
- 每 Site 一个 `active_release_id`，且该 release 的 Site 必须相同、状态必须 active。
- 每 Site 一个 active Profile assignment。
- decommissioned Site id/key、旧 binding identity 与 revoked workload principal 永不复用；domain history/tombstone
  永不删除，但不等价于域名字面值永久禁止绑定新 Site。

### 7.3 状态机

```text
Site: requested -> approved -> provisioning -> configuring -> preview_ready -> active
      requested|approved|provisioning|configuring -> failed
      failed -> (same-attempt reconcile | decommissioning)
      active -> suspended
      suspended -> resuming -> active
      active|suspended|failed -> decommissioning_reversible
      decommissioning_reversible -> active|suspended | decommissioning_irreversible
      decommissioning_irreversible -> decommissioned

Release: draft -> validating -> ready -> activating -> active -> retired
         validating|activating -> failed

ActivationAttempt:
  preparing -> promote_requested -> observing -> pointer_committing
  -> draining -> succeeded
  any nonterminal -> failed | outcome_unknown -> observing
```

非法转移由 domain state machine 拒绝。active Site 不直接进入 generic `failed`；安全/运营异常进入 suspended 或
保留 active 并让具体 release/dependency observation failed。`suspended -> active` 只能由新 ActivationAttempt 完成。
`decommissioned` Site identity 不可恢复；原 domain 若重新使用，是全新 SiteRequest/new siteId，不是 restore。

### 7.4 immutable publish pointer

每个 Site project 构建 `site-release-manifest.v1.json`，至少含：

```text
siteKey, projectRef, sourceCommit, appKitVersion, contractVersion,
artifactDigest, routeManifestDigest, brandAssetDigest, seoManifestDigest,
legalManifestDigest, profileKey, profileRevision, buildProvenanceRef
```

Platform 只存 manifest/digest/ref，不存可编辑 brand/SEO copy。`SiteRelease` 创建后不可修改；更改任何字段
必须创建新 release。Brand/SEO/法务正文归 Site Web source/artifact，Platform 只验证 ownership、digest、
required fields 和 capability compatibility。

激活步骤：

1. transaction 创建 `ActivationAttempt(preparing)`，冻结 target release、expected Site version 和 predicate digest。
2. Worker 验证 certification、current policy、domain/project binding 与 artifact provenance。
3. 写 durable promote intent 后调用 deployment provider；不持 DB transaction 等网络。
4. append observations；timeout 写 `outcome_unknown`，同 attempt 继续 reconcile，不新建重复 deployment。
5. 观测到 exact artifact/release healthy 后，transaction 锁 Site，以 version CAS 设置
   `active_release_id=target`；target release 进入 active，旧 deployment slot/release compatibility 进入 bounded
   draining，写 pointer receipt、audit、outbox，但 Attempt 尚未 succeeded。
6. drain window 内旧 tab 只能通过其 exact deployment binding/release/audience 使用冻结的兼容读写集合；不能提交
   target-only capability，也不能自报 releaseId 换权限。drain 完成后旧 release retired、Attempt succeeded；drain
   失败不回滚 pointer，继续同一 Attempt reconcile。

Rollback 是指向旧 immutable release 的新 ActivationAttempt；仍需以当前 contract/security/profile 重新验证，
不能直接写 pointer。

### 7.5 Suspend、resume 与 decommission

Suspend 在一个 transaction 中 bump `site_security_epoch`、冻结 `SuspensionPolicyRevision`、撤销用户 session 与
delegated grant，并拒绝新 signup/acquisition/admission。不得无差别撤销承载状态页、Support、Data Rights、历史
Artifact export 和 mandatory financial/legal inbound 的 workload audience；这些入口使用独立最小 operation
allowlist、不能发起新产品副作用。只有 binding/credential 本身泄露时才 revoke 对应 binding，并切换到独立安全
控制面入口。resume 创建新 ActivationAttempt，重新验证 domain/certificate/binding/Profile/Release/certification/
kill switch 后才恢复流量，不能直接改 status。

Decommission 先创建 immutable `DecommissionPlan`，冻结 Site/Profile、active work、Subscription/Code、Payment/
Dispute、Case、notification/export window、Retention/LegalHold 与所有 participant epoch。进入 irreversible fence 前，
maker/checker 可取消并按当前 policy 回到 active 或 suspended；进入后只能完成。每个 owner 返回幂等 participant/
object-GC receipt，任何 missing/partial/unknown 均保持 decommissioning 并进入 reconciliation，不能宣告完成。

新 signup/acquisition/admission 在 plan 开始后关闭，但 mandatory webhook、Support、Data Rights、Audit 与 LegalHold
继续由窄控制面处理。只有通知/导出窗口、法定处置、active work policy、binding/domain/certificate/secret revoke、
traffic=0、orphan inventory=0 和全部 mandatory receipt 被验证后，才提交永久 Site tombstone。旧 cookie/token/
SiteContext/workload principal 永久拒绝；域名未来重用遵循 §7.2 的 new siteId 流程。

## 8. Identity、session 与 personal Workspace

### 8.1 Site-local identity schema

| aggregate/table | 必需字段/约束 |
|---|---|
| `user_account` | `id,site_id,subject_generation,status,security_epoch,created_at`; 不使用 externalUserId 作主身份 |
| `login_identifier` | `site_id,user_id,generation,kind,normalized_value,verified_at,status` |
| `password_credential` | user、Argon2id parameters/hash、version、changed_at、status |
| `authenticator` | user、TOTP encrypted secret ref/status、enrollment transaction；确认首个 code 后才 active |
| `recovery_code_set/code` | set generation、每 code hash/used_at、replaced_at；一次性导出，旧 set 原子撤销 |
| `auth_transaction` | Site、purpose、subject generation、identifier/challenge hash、request digest、attempts、expiry、consumed_at |
| `recovery_transaction` | proof-set/policy/risk snapshot、channel snapshot、cooldown、replacement factor、state |
| `auth_session` | Site/User/device label、secret hash、status、session_epoch、auth methods/times |
| `refresh_token_family` | AuthSession、family status、generation、reuse_detected_at、expiry |
| `refresh_token_instance` | family、generation、token hash、issued/consumed/replaced/revoked times |
| `legal_acceptance` | User、document digest/version、locale、accepted_at、request evidence |
| `security_event` | append-only auth/revoke/disable/reuse/risk decision |
| `credential_command_receipt` | registration/verify/reset/change/email/MFA/recovery identity、digest、result refs |
| `identity_subject_tombstone` | Site、旧 subject generation、deletion receipt、retention/re-registration policy |

数据库约束：

- `UNIQUE(site_id, kind, normalized_value) WHERE status IN ('pending_verification','active')`；删除完成后的新注册使用
  新 subject generation，不复活旧 User/Workspace/session。
- 同一邮箱在不同 Site 创建不同 User、credential、session、Workspace、BillingAccount 与 rights subject。
- password 使用批准的 Argon2id 参数和 pepper secret ref；日志、event、audit 不含 password/token/OTP。
- recovery code 一次性 CAS；TOTP enrollment 在确认首个 code 前不 active。
- `AuthSession` 与 GA runtime execution/checkpoint identity 是不同对象，不能把 namespace/runtime JWT 塞回
  session 表或 cookie。

### 8.2 注册、邮箱验证与 activation

`beginRegistration` 在一个 Platform UoW 中：

1. 验证 Site/Profile/Legal revision、password policy、RiskDecisionSnapshot 和 enumeration policy。
2. 创建 `user_account(status=verification_pending)`、pending `login_identifier`、password credential、分别记录
   Terms/Privacy/age/optional marketing consent，并创建 Site/purpose/host/audience/subject-generation-bound 的
   verification `auth_transaction`。
3. 原子写 registration receipt、SecurityEvent 和 NotificationRequest outbox；任何写失败全部回滚。
4. 同 Site 重复请求使用 non-disclosing response：未验证 subject 安全 resend/supersede challenge，active subject
   只发送登录/重置指引，不创建第二个 User，也不向调用者透露分支。

`verifyEmailAndActivate` 在一个 `SERIALIZABLE` Platform transaction 中：

1. 锁定并单次消费未过期 verification transaction；核对 Site、host/audience、purpose、subject generation、
   attempts、Risk snapshot 与 User 仍为 verification_pending。
2. 设置 identifier verified、User active；调本地 `PersonalWorkspaceBootstrap` 创建 personal Workspace、owner
   Membership、BillingAccount、default Project、ExecutionSpace 和 opaque GA namespace allocation intent。
3. 写 activation/bootstrap receipt、security audit、verification notification 与 outbox；任一步失败时 verification
   consume、User activation 与 personal graph 全部回滚，同 identity 重试返回同 receipt。
4. 邮箱验证不创建 `AuthSession`、refresh family 或 browser cookie。用户必须随后显式 password/TOTP login；
   verify link 可跨设备打开而不会把打开链接的设备自动登录。

GA namespace 若需要远程分配，transaction 内先分配 Platform-owned opaque namespace ID 并写 outbox；GA 仅消费该
opaque ID。远程 provisioning 失败由 Worker reconcile，不创建第二个 Workspace。

### 8.3 password/TOTP login

- 登录输入只含 email/password；Site 来自 `TrustedProductContext`。
- identifier lookup、password verify、lockout/rate/Risk 都按 Site；Redis unavailable 时 sensitive auth fail closed。
- 需要 TOTP 时先返回短期 `auth_transaction`，完成 TOTP 后才建 AuthSession。
- 错误对未知账号、错 password、disabled 账号统一；security event 内保留内部 reason。
- Core 用户 OAuth/Magic Link/passkey adapter 不注册、不出 route、不进构建依赖。
- 单因子 password 至少 15 Unicode code points、支持至少 64/Unicode/space/password-manager paste，NFC 后完整
  hash、不截断、不强制字符组合/周期轮换；按版本化 blocklist 与 Argon2id policy 校验，成功登录可透明 rehash。
- pre-auth/login/step-up/recovery completion 必须生成新高熵 AuthSession/family 并原子废弃旧 pre-auth id；
  return intent 仅允许签名 allowlist path，禁止 session fixation/open redirect。

认证密码学不得自研。Platform Identity 使用维护中的标准库：`argon2` 负责 Argon2id password hash/verify，
`jose` 负责签名/验证 policy token，`otplib` 负责 RFC 6238 TOTP，`openid-client` 负责 OIDC discovery/JWKS/
issuer/audience/nonce/PKCE；若将来批准 Passkey/WebAuthn，只能使用 `@simplewebauthn/server`。所有库固定版本并
进入 SBOM、安全升级与测试；禁止手写 hash 格式、JWT 编解码、OIDC/WebAuthn challenge 或 session crypto。

除 password/TOTP/recovery 外的用户认证方法按四层关闭：

| layer | Core 要求 |
|---|---|
| Web/provider | Auth.js 不注册 Email、OAuth/OIDC、WebAuthn provider，页面和 callback route 不存在 |
| Platform API/bootstrap | OpenAPI 无 Magic Link/OAuth/Passkey/SSO endpoint，启动不读其 client/SMTP/WebAuthn config |
| policy/domain | operation registry 与 Profile inventory 无对应 operation/method，伪造调用 default deny |
| build/certification | dependency、route manifest、env schema、SBOM 与 E2E 负扫，命中即拒绝 SiteRelease |

### 8.4 Password、MFA、email change 与 AccountRecovery

- password reset request 对存在/不存在账号返回相同公开响应与时延等级；token 只存 hash，绑定 Site/purpose/
  generation/audience/expiry。完成 reset 不自动登录，默认 revoke 全部 session，MFA 保持有效并发送 mandatory
  notification；响应丢失查询同 receipt，不再次修改 password。
- password change 要 recent re-auth，commit 时撤销其他 session、rotate current family、bump credential epoch 并通知。
- TOTP enrollment 是 `pending -> confirmed -> active` 两阶段；secret envelope-encrypted 且只展示一次，challenge
  有 attempt/time budget 并拒绝同 timestep replay。每组生成 10 个至少 128-bit 的 recovery code，只存 hash；
  regenerate 原子撤销旧组，disable/reset 要另一 active factor 或正式 recovery。
- email change 创建 pending identifier；新邮箱验证前旧邮箱仍 primary/recovery。commit 原子切换 Site-local unique、
  revoke others/rotate current，并通知旧/新邮箱；无旧渠道必须走 AccountRecovery，Support 不直接覆盖 email。
- Full AccountRecovery 由版本化 RecoveryPolicy 冻结 proof set、attempt/cooldown、Risk、恢复开始前 verified channel
  snapshot 与 replacement factor。Core 只接受未使用的预注册 recovery code，或 active authenticator + 原安全渠道；
  email/device/交易/KBA/Support 断言单独不够。完成时撤销旧 factor/session、挑战并绑定 replacement factor、推进
  SecurityEpoch、开始高风险 cooldown，并通知所有 pre-recovery channel。无有效 proof 时明确不可恢复；只有
  Site 预先认证的 external identity-proofing 流程可由 scoped JIT + maker/checker 承接。
- recovery cooldown 内禁止 email/MFA、Redemption liability、ownership、export/delete 等高风险命令；每个 effect
  point 重验 recovery restriction epoch。所有 reset/change/MFA/recovery command 都使用同 key+digest receipt。

### 8.5 cookie、refresh、revoke、disable

Site Web 必须使用 Auth.js 负责 browser/BFF session choreography、cookie serialization、CSRF、callback 与 cookie
密钥轮换，不得保留当前手写 AES-GCM `session-envelope.ts`、手写 cookie parser/serializer 或自制 CSRF 协议。
Platform Identity 仍是 User、credential、AuthSession、refresh family 与 revoke/disable 的唯一 authority；Auth.js
adapter/provider 只能通过 generated Platform client 调用它，不能拥有账户事实或直连 Platform 数据库。

Auth.js session 中只允许保存 Platform 签发的 opaque AuthSession/refresh handle，不能保存 runtime JWT、Site/User/
Workspace/namespace claim。每次 BFF protected call 都将 opaque handle 交 Platform 重验，而不是相信 Auth.js callback
中的旧 profile。Auth.js 配置只持有：

```text
__Host-kokoro.session-token = Auth.js encrypted session; payload only opaque Platform session/refresh handles
__Host-kokoro.csrf-token    = Auth.js-managed CSRF value
Auth.js transient state/nonce/PKCE cookies when a configured protocol flow requires them
```

所有 cookie 均 `Secure; Path=/`，SameSite 按 Auth.js 安全默认和协议需求固定；session 与敏感 transient cookie
必须 HttpOnly。不设置 Domain，不自行序列化，不把 Site/User/Workspace/namespace/runtime JWT 放进 cookie。
BFF server-side 把 opaque credential 交 Platform，Platform 同时验证 Site workload binding 与 actor session。
Password/TOTP 的 Auth.js authorize callback 只调用 generated Platform client；refresh callback 仅在 Platform
成功 rotation 后用 Auth.js 自身 session API 原子替换两个 opaque handle，不解码、不自行签发 credential。

Refresh 必须在一个 transaction 中：

1. 按 token hash 锁 current instance + family + AuthSession + User + Site。
2. 核对未过期、未消费、current generation、binding audience、所有 status/epoch。
3. CAS 消费旧 token、generation +1、创建新 instance、更新 session last_seen 和 receipt。
4. 若发现 reuse，原子 revoke 整个 family 和 AuthSession、bump `session_epoch`、写 security event/outbox，拒绝签发。
5. commit 后返回新 credential；网络 outcome unknown 用同 digest receipt reconcile，不能重做 rotation。

支持明确操作：`revoke-current`、`revoke-session(sessionId)`、`revoke-others`、`revoke-all`。每个只作用于同
Site/User；越权时 404 等价响应。`disableUser` 在同 transaction 设置 disabled、bump user epoch、revoke all
AuthSession/family、撤销 delegated grants、写 audit/outbox。`disableSite` 同理作用于该 Site 全部 active session。

所有 protected Platform API 每次检查 active session/user/site 和 epoch；不以 access token TTL 等待吊销生效。
Session/Job 的短 delegated grant 在敏感 effect point 通过 Admission 再查 epoch。

### 8.6 personal Workspace

| table | 必需约束 |
|---|---|
| `workspace` | `site_id,kind='personal',status,security_epoch`; `personal_owner_user_id` unique per Site/User |
| `workspace_membership` | personal Workspace 仅一 active owner；无 invite/admin/member mutation |
| `billing_account` | Site/Workspace unique，`acquisition_mode='redeem_only'` |
| `project` | personal Workspace 仅一个 default Project（partial unique） |
| `execution_space` | Project、opaque `execution_namespace` unique、status/epoch |

User ID 不是 Workspace ID，Workspace ID 也不直接作为 GA namespace。Core Profile 的 collaboration policy 恒为
disabled；invite/member/team/switch operation 不在 policy registry，命中未知 operation 即 deny。

## 9. Admin security model

### 9.1 OIDC 与 principal

Production/production-like Admin Web 只用 OIDC Authorization Code + PKCE。Admin Web/Auth.js 固定验证 state、
nonce、code verifier；Platform 独立验证 issuer、audience、签名、exp/iat、nonce 与认证强度 claims。Operator
identity 唯一键是 `(issuer, subject)`，email 只作显示/通知，不能作稳定主键。Admin session 短时、
server-side、可撤销。

Admin Web 使用 Auth.js 的 OIDC provider 与 browser-session/CSRF/state/nonce/PKCE 实现；Platform 使用标准
OIDC/JOSE library 对提交给 `AdminIdentityService.ExchangeOidcSession` 的 token 独立验证。issuer 与 audience 在
Web provider 和 Platform verifier 两侧都是 production 启动必填，不能因 discovery 成功而省略 audience，
也不能手写 JWT parser 或只信 Admin Web 注入的 email。

`ExchangeOidcSession` 只接受由 Platform `BeginOperatorLogin` 预先创建的单次 `OperatorAuthTransactionRef`，该
transaction 冻结 issuer/client/audience/exact redirect/nonce/PKCE challenge/environment/region/managed-device policy/
return intent 与 expiry。Admin Web 完成 browser callback 后提交 authorization result + transaction ref；Platform
对同一 transaction 原子消费 code/result，独立执行 discovery/JWKS pin、签名、issuer/aud/azp、nonce、PKCE、
auth_time、acr/amr、device claim 与 replay 验证后才创建 OperatorSession。Web 验证用于 browser safety，不能替代
Platform authority；只提交 email/header 或未绑定 transaction 的 ID token 一律拒绝。

普通读要求 phishing-resistant authentication；权限/Scope/Site lifecycle/disable/redeem override 等 sensitive
命令要求近期 step-up，`auth_time` 和批准的 `amr/acr` 均满足政策。dev header、默认 operator、proxy email、
Admin Magic Link 在 production-like 构建和启动均拒绝。

phishing-resistant assurance 与 step-up freshness 是两个正交字段：step-up 不能把 password/TOTP 会话升级为
phishing-resistant，后者必须由 IdP/managed-device policy 认可的硬件绑定 factor 证明。environment、region、device、
operator/session/restriction epoch 任一变化，都让下一次读与 effect-point authorization 失败。

### 9.2 scope 无歧义

```ts
type OperatorScope =
  | { kind: "site"; siteIds: NonEmptyArray<SiteId>; environment: EnvironmentId; region: RegionId }
  | { kind: "global"; grantId: GlobalScopeGrantId; environment: EnvironmentId; region: RegionId }
  | {
      kind: "breakglass"
      grantId: BreakGlassGrantId
      incidentId: IncidentId
      environment: EnvironmentId
      region: RegionId
      operation: OperationId
      resourceRefs: NonEmptyArray<ResourceRef>
      fieldAllowlist: NonEmptyArray<FieldId>
      expiresAt: Instant
    }
```

- 数据库用 typed rows `operator_site_scope`、`operator_global_scope_grant` 与 `breakglass_grant`，不存 `"*"` JSON。
- 缺失 `siteId` 是 invalid request，不等价 global。
- global operation 必须选择 `{kind:'global'}`、具备 exact permission、active GlobalScope grant 和 step-up。
- breakglass 不是 GlobalScope 别名；只允许 grant 中 exact operation/resource/field，不能 fan-out 搜索、扩大 Site、
  复用到另一 environment/region 或开启 acquisition。普通 Site/Global permission 不能隐式使用 breakglass。
- Site-scoped list 在 SQL predicate 先过滤再 limit；缺 `siteId` 不 fan-out，也不读全表后过滤。
- Platform-global resource 不接受 Site scope；Site resource 不接受 Global 省略 target。

### 9.3 防自升级

以下命令 actor 与 target 相同即拒绝：改变自身 Role/permission/scope/status、授予 GlobalScope、延长自身
breakglass、审批自身请求。操作者不能授予自己不拥有或不可委派的 permission/scope。Role definition、
GlobalScope、Operator enable/disable 均为 `dangerMutation`，强制不同 maker/checker；最后一个恢复管理员的
降级/禁用还需固定 platform recovery policy。

### 9.4 approval / execute / audit 原子性

核心表：`operator_identity`、`operator_auth_transaction`、`operator_session`、`managed_device_observation`、`role`、
`role_permission`、`operator_role_assignment`、`operator_site_scope`、`operator_global_scope_grant`、
`approval_request`、`admin_command_attempt`、`admin_command_receipt`、`rejected_command_attempt_receipt`、
`audit_record`、`breakglass_grant`。

`approval_request` 固定保存 canonical operation、typed target scope、environment、region、managed-device policy、
immutable parameter JSONB、SHA-256 digest、expected target version、maker、required permission/assurance、max step-up
age、各 security/restriction epoch、expiry 和状态。修改参数、scope/environment/region/version/epoch 任一变化必须
新建 request；approval 不可跨 environment/region/release replay。

```text
pending -> approved | rejected | expired
approved -> executing -> executed | failed | outcome_unknown
outcome_unknown -> executing | executed | failed
```

执行 Platform-local 命令前，独立 fail-closed audit gate transaction 先创建
`AdminCommandAttempt(status=started, commandIdentity, parameterDigest, actor/context refs)`；如果该 append path 不可用，
命令在任何业务 effect 前拒绝且不执行。随后一个 PostgreSQL 业务 transaction 完成：

1. `FOR UPDATE` approval、checker session、maker/checker assignments、target aggregate。
2. 重算 parameter digest，重验不同 maker/checker、permission、typed scope、environment/region/device、
   phishing-resistant assurance、step-up freshness、operator/session/restriction epoch、Risk、target version。
3. claim command receipt；调用本地 owner application port 完成 domain mutation。
4. 写 domain receipt、approval final state、append-only audit、security decision、outbox。
5. 一起 commit；任一写失败则业务 mutation 也回滚。

成功 effect 的 final audit/receipt 与业务 mutation 保持上述同一 UoW，并引用 started attempt。入口授权拒绝、domain
拒绝、serialization exhaustion 或业务 UoW 回滚时，不伪称 rollback 内 audit 可保留；通过独立 transaction append
`RejectedCommandAttemptReceipt`，冻结 attempt/command identity、actor/trusted caller/scope refs、parameter digest、
decision/error class、correlation 和时间（不含 credential、secret 或正文 PII），并 CAS attempt 为 rejected/rolled_back。
同 attempt 重试先恢复该 receipt，不能再次执行 effect；append 失败则保持 fail closed、page Security/Admin owner，
不返回或缓存可被解释为成功/可安全重放的业务 receipt。

若批准的是外部 effect，步骤 3 只原子写 durable effect intent + audit/receipt `accepted`；Worker 调 provider 前
再授权，记录 observation，最终 transaction 原子写业务承认事实、receipt 与 audit。timeout 置
`outcome_unknown` 并 reconcile 同一 intent，禁止盲重试。

Admin façade 不 import repository/Prisma，不直接写任何业务表；只调用 `AdminCommandBus`。业务 owner 在本地
application service 内执行，避免当前 gateway 对同 Platform 模块 self-RPC。

### 9.5 breakglass

Breakglass 仅在 IdP/常规授权故障时启用：JIT、单 operation/resource/field allowlist、最长 30 分钟、关联
incident、双人批准、实时 paging、全量 audit、自动 revoke、24 小时内 postmortem。它不能提供通用跨 Site
email 搜索、不能绕过 Site tombstone、不能自批，也不能开启 Payment acquisition。

## 10. Redeem-only Payment 七层关闭

七层是独立验收门，任一层失败都不允许发布 `core-redeem-chat@1`：

1. **Source/route 层**：Site project 不含 checkout、plans-for-purchase、mock-pay、refund、dispute route 或 UI；
   当前 `apps/user/src/app/api/billing/**` acquisition route 与 `/billing/pay/**` 删除。
2. **Build/navigation 层**：route manifest、navigation、server action 和 client chunk 均无 acquisition symbol；
   `apps/admin/app/payment/page.tsx` 及对应 action 不进入 Core artifact。
3. **Profile/bootstrap 层**：`capability_inventory.payment_acquisition='disabled'`，Site/Workspace bootstrap 只创建
   `BillingAccount(acquisition_mode='redeem_only')`，不创建 Plan/Order/Subscription。
4. **HTTP/RPC admission 层**：OpenAPI/Connect descriptor 不发布 create-checkout/order/refund/dispute operation；
   请求旧 path 可使用 404/410 transport status，但 response 必须包含 versioned stable
   `ACQUISITION_CHANNEL_DISABLED` domain code，绝不调用 owner、数据库或 provider，也不泄漏 Provider 配置。
5. **Domain/effect policy 层**：`CallerOperationPolicy` registry 没有 acquisition operation；伪造内部调用也
   `operation.unknown` deny。Admin command manifest 同样没有 grant-plan/refund/provider mutation。
6. **Dependency/secret/startup 层**：Core deploy 不安装/初始化 payment SDK，不定义 PaymentProviderAccount，
   不读 provider key/webhook/mock secret，不依赖 `KOKORO_PAYMENT_BASE_URL`，缺支付配置仍可健康启动。
7. **Assignment/certification/provenance 层**：SiteRelease validator 对 Profile、route manifest、SBOM、env schema、
   Admin manifest 和 E2E traffic 做负向扫描；发现 route、SDK、secret、provider egress 或 payment mutation 即拒签。

保留的是 Redeem/Credit；其实现由 W2A 唯一拥有。因为系统未上线，migration preflight 预期不存在真实 payment；
测试/seed Plan、Order、Subscription、Refund、PaymentEvent 全部删除。若 preflight 意外发现带外部 provider receipt
的真实事实，W1 cutover 必须硬停止并导出不可变证据；不得把它们导入一个无法履责的只读死档后继续上线。
只有 W2B 已提供原 ProviderAccount 的 historical Refund/Dispute/Reconciliation preservation path，或 Data/Finance/
Legal 以签名 disposition 证明不存在剩余责任，才能继续。payment acquisition 仍保持关闭，历史责任接口不能创建
新 Checkout/Order/Subscription。

## 11. Risk、Notification、Data Rights 与审计

- `RiskDecisionPort` 对 registration、login anomaly、recovery、redeem、Admin sensitive、breakglass 强制调用，
  严格采用 §6.4 的 transaction 外 assessment + transaction 内 signed snapshot/epoch recheck。
- Risk timeout/invalid signature/stale decision 对 sensitive operation fail closed；普通只读可按父 policy 降级。
- Notification intent 与业务事实同 transaction 写 outbox；Notification owner at-least-once materialize，template
  仅引用 SiteRelease 中的 brand/legal digest。
- Data Rights subject 是 `(siteId,userId,subjectGeneration)`；export/delete 不按跨 Site email 聚合，新注册创建
  新 generation，不能恢复旧 User/Workspace/session。
- W1 冻结下列 transaction-scoped `DataRightsParticipant` contract；完整 coordinator/Admin/User UI 在 Wave 7，
  但 Identity/Workspace/Site 必须在自身 W1 实现 participant 与 receipt，不能留给 coordinator 跨表删除：

```ts
interface DataRightsParticipant {
  prepareExport(input, ctx): Promise<ExportParticipantPlan>
  materializeExport(input, ctx): Promise<ParticipantReceipt>
  freezeSubject(input, ctx, tx): Promise<ParticipantReceipt>
  planDisposition(input, ctx): Promise<DispositionPlan>
  executeDisposition(input, ctx, tx): Promise<ParticipantReceipt>
  verifyDisposition(input, ctx): Promise<ParticipantReceipt>
}
```

每个 plan/receipt 绑定 Site、subject generation、request/plan digest、retention policy、LegalHold/participant epoch、
owner、idempotency、state/evidence。新增 LegalHold/epoch 使旧 plan 失效；partial/unknown 保持可恢复。删除先 revoke
session/grant、冻结新产品写入，再按 owner disposition retain/deidentify/unlink/delete/GC；不提供
`/users/:id/delete|restore` 直写路由。
- `NotificationRequest` 冻结 SiteRelease/template/brand/legal/locale/recipient/security event/deep-link/idempotency，
  与源事实同 transaction 写 outbox；materializer 以 request/channel identity 幂等、记录 accepted/delivered/failed/
  unknown receipt 和 DLQ。verification/reset/password/email/MFA/recovery/session/deletion 通知为 mandatory。
- W1 Identity/Site Admin command 产生 typed `SupportCaseRef`/安全 timeline ref；Support 只能按 Site scope 使用安全 ref，
  不通过跨 Site email 搜索或 direct DB 修复。完整 SupportCase workflow 仍由 Wave 7 owner 实现。
- Audit append-only，至少含 actor、trusted caller、operation、scope、decision、reason code、parameter digest、
  command/approval/receipt refs、before/after digest、result、timestamps；禁止 credential/secret/正文 PII。

## 12. 外部接口冻结

### 12.1 Site Web → Platform OpenAPI

| operation | method/path | actor | transaction owner |
|---|---|---|---|
| exchange product | `POST /v1/product-context:exchange` | workload | Site read/short token |
| begin registration | `POST /v1/identity/registrations` | anonymous | Identity |
| verify email + activate | `POST /v1/identity/verifications/{id}:complete` | anonymous | Platform activation/bootstrap UoW |
| resend verification | `POST /v1/identity/verifications:resend` | anonymous | Identity/Notification UoW |
| password login | `POST /v1/identity/sessions` | anonymous | Identity |
| complete MFA | `POST /v1/identity/sessions/{id}:verify-mfa` | anonymous transaction | Identity |
| refresh | `POST /v1/identity/sessions:refresh` | session/refresh credential | Identity |
| list devices | `GET /v1/identity/sessions` | User | Identity read |
| revoke | `POST /v1/identity/sessions:revoke` | User | Identity |
| begin/complete password reset | `POST /v1/identity/password-resets[/{id}:complete]` | anonymous | Identity |
| change password | `POST /v1/identity/password:change` | User + recent re-auth | Identity |
| begin/complete email change | `POST /v1/identity/email-changes[/{id}:complete]` | User + recent re-auth | Identity |
| TOTP enroll/confirm/disable | `POST /v1/identity/totp/{action}` | User + required factor | Identity |
| recovery code regenerate | `POST /v1/identity/recovery-codes:regenerate` | User + step-up | Identity |
| begin/complete account recovery | `POST /v1/identity/account-recoveries[/{id}:complete]` | recovery transaction | Identity |
| re-auth | `POST /v1/identity/sessions:reauthenticate` | User | Identity |
| personal context | `GET /v1/me/personal-context` | User | Workspace read |

Mutation 要求 `Idempotency-Key`、contract version、CSRF 和 workload binding；body 禁止 siteId/userId/workspaceId
authority fields。响应错误使用 versioned stable code，不泄露账号存在性。

W1 只冻结 `chat.execution.prepare` 的 operation identity、request-security 与 default-deny Policy shell；
`POST /v1/executions:prepare` 不进入 W1 OpenAPI descriptor、不注册 route，也不创建 Credit/Hold/grant。只有 W2A
Credit authority 与 W3 Session admission 均 qualified 后，才能由对应 owner 发布该 contract 与实现；此前调用稳定
返回 unavailable/route absent，不能回退旧 Credit service。

`POST /v1/redeem:apply` 属于 W2A OpenAPI 与 Commerce/Credit UoW，本 Spec 只要求它未来复用同一
RequestSecurityContext、Risk snapshot、BillingAccount binding 与 command identity，不在 W1 重复冻结 payload 或实现。
W2A 未通过前，Core SiteRelease 不能把 Redeem 标记为 qualified。

### 12.2 Admin Web → Platform Connect

```text
AdminIdentityService: BeginOperatorLogin, ExchangeOidcSession, BeginStepUp, CompleteStepUp, SignOut
AdminQueryService: GetSite, ListSites, GetUserWithinSite, GetAuditWithinScope
AdminCommandService: PrepareCommand, SubmitForApproval, DecideApproval, ExecuteApproved, GetReceipt
SiteLifecycleService: RequestSite, ReconcileProvisioning, CreateRelease, ActivateRelease,
                      SuspendSite, ResumeSite, PlanDecommission, CancelDecommission,
                      ExecuteDecommission, GetDecommissionReceipt
AdmissionService: AuthorizeEffect, GetRestrictionEpochs
```

每个 command message 明确 `CommandIdentity{idempotencyKey,digestAlgorithm,requestDigest}`、environment、region、
managed-device ref、security epochs 和 typed Site/Global/BreakGlass scope oneof；不能用 omitted field 表达 global，
不能用 GlobalScope 承载 breakglass。Admin Web 只使用 generated client。

### 12.3 Platform → runtime

Platform 为 Session/Job → Platform effect call 验证的 `DelegatedExecutionGrant` 仅含 opaque subject/namespace、
operation、resource digest、expiry、epoch 与 audience；它不进入 Session → GA dispatch，也不进入 GA
request/manifest/event。GA 继续接收现有字节级 `run.request`/`run.cancel`，禁止新增 `siteId,userId,ownerId,
workspaceId,projectId` 或 grant/auth/credit field；运行语义、checkpoint、tool loop、SSE ordering 均不改变。

## 13. 事务与恢复矩阵

| flow | single Platform transaction | commit 后动作 | 恢复键 |
|---|---|---|---|
| registration begin | pending User/identifier + credential/legal + verification transaction + notification outbox | verification delivery | registration id + digest |
| email verify/activation | verification consume + User active + personal bootstrap + outbox；不建 session | activation notification/namespace provision | verification id + digest |
| password/MFA session | auth transaction consume + session/family + security event | cookie response | auth transaction id |
| password reset/change | token/re-auth consume + credential epoch + session revoke/rotation + receipt/outbox | security notification | credential command id + digest |
| email change | pending identifier consume + primary swap + session revoke/rotation + receipt/outbox | old/new channel notification | email-change id + digest |
| TOTP/recovery code | enrollment/challenge consume + authenticator/set CAS + receipt/outbox | mandatory notification | authenticator command id + digest |
| AccountRecovery | proof/replacement challenge + factor/session revoke + SecurityEpoch/cooldown + receipt/outbox | multi-channel notification | recovery id + digest |
| refresh | old consume + family generation + new token + receipt | new cookie | token family + generation/digest |
| disable/revoke | status/epoch + sessions/grants + audit/outbox | cache invalidation | command id |
| Admin local command | effect 前 attempt audit gate；成功时 approval claim + domain mutation + receipt/audit/outbox 同 UoW；拒绝/回滚另写 fail-closed receipt | notify/security page | approval/command/attempt id |
| release activation | intent only；pointer commit 是后续独立 txn | provider promote/observe | activation attempt id |
| Site suspend | SuspensionPolicy + Site epoch + session/grant revoke + restricted allowlist/audit | traffic/security propagation | suspend command id |
| decommission | plan/fence/participant epoch + intent/receipt state；最终 tombstone 独立 txn | notify/export/provider/GC/verify | decommission plan/receipt id |
| model-control import | immutable source inventory + model/catalog/assignment facts + import receipt | generated projection/cache | source digest + import command id |

Redeem/Fulfillment/Grant/Journal/Hold transaction matrix 仅由 W2A 定义，W1 不实现第二条路径。禁止在 transaction
内 fetch；Risk 遵循 §6.4。Worker claim 使用 lease + `FOR UPDATE SKIP LOCKED`，lease 过期可由另一 Worker 接管；
所有外部 observation append-only。未知结果先 reconcile receipt/provider state，不能创建新业务 effect。

故障默认：

- PostgreSQL 不可达：所有 mutation fail closed；不以 Redis/cache 继续写。
- Risk 不可达：auth/redeem/Admin sensitive/irreversible fail closed。
- Notification 不可达：业务 transaction 可提交 outbox，Worker 重试；不重复业务事实。
- deployment provider timeout：ActivationAttempt=`outcome_unknown`，active pointer 不动。
- pointer commit 后 drain 失败：新 release 保持 active，Worker 继续 drain，不来回切 pointer。
- refresh response 丢失：客户端用同 idempotency/digest reconcile receipt；旧 token 不获得第二次 rotation。
- workload binding 泄露：revoke binding + bump binding/Site epoch，所有 exchange/effect 立即拒绝。
- decommission cleanup partial：Site 保持对应 decommissioning phase；窄 Support/Data Rights/mandatory inbound 继续，
  participant/GC 逐项 reconcile，全部验证后才永久 tombstone。

## 14. Clean replacement 与迁移顺序

### 14.1 数据 preflight

实现 PR 首先提供只读 inventory：六个 MySQL schema 的表/row count、非 seed marker、external provider receipt、
当前 Site/domain/project ref，以及 ModelDefinition/ProviderAccount metadata/ModelBinding/Label/Site policy 的 source
digest。任何非 ephemeral 环境或真实 payment receipt 使自动 cutover 停止；不得静默删除。
预期结论是“未上线、仅 dev/test/seed”，随后导出必要的 Site key/domain/project binding 清单供人工复核，
不是做旧 schema 兼容导入。

### 14.2 建新再切换

1. ADR-012 与父设计冲突修订先合并；在 `kokoro-platform/prisma` 建 PostgreSQL 18 schema、constraints、migration、
   seed、owner-scoped repository factory 与 UoW。
2. 在单 Platform process 内实现 Site/Identity/Workspace/ModelControl/Admin/Policy/Audit application ports；Commerce
   只实现 personal BillingAccount bootstrap shell，Credit/Redemption/Fulfillment/Grant/Journal/Hold 不在 W1 手搓。
3. W1 把现有 model catalog/label/provider metadata/Site assignment 迁入 `model-control`：先导出 canonical source
   inventory/digest，事务导入 immutable definitions/assignments，逐项比对读 projection 与 authorization，再切所有
   consumer 到本地 owner port/generated API。Provider secret 仍只保存 SecretRef，Model Gateway 仍是远程 effect role。
4. 生成新 OpenAPI/Connect contract，Site reference project 与 Admin Web 只消费 generated client。
5. 创建两个根 workspace 之外的独立 production-like Site repository/project，发布 signed artifact，完成独立
   deployment/release/rollback，并登记 source/artifact provenance。
6. 切 Platform API/Worker 和 `DATABASE_URL_PLATFORM`；禁止同时运行旧写面。W1 未 qualified 的 Redeem/Credit/API
   保持不可达，直到 W2A 在同 PostgreSQL owner model 上完成，不回退旧 Credit service。
7. 完成验证后从默认 Infra 移除/停止 MySQL process，保留只读 dev snapshot 并 archive volume；绝不自动删除
   volume、image 或 dev data。更新 infra/CI/runbook/ADR/INDEX，只有经用户/运维单独明确授权才可物理删除 archive。

不做 dual-write、dual-read、shadow compatibility endpoint、旧 token adapter 或 Host resolve fallback。

### 14.3 必删清单

- `kokoro-site`、`kokoro-user`、`kokoro-platform-admin` 作为独立 process 的 main/config/db/client 与 service deploy。
  领域代码只可经评审搬入新目录，旧 route/repository/schema/migration/test 删除。
- `kokoro-model` 独立 process/db/client/base URL 在 W1-C model-control import/cutover 证据通过后删除；Model Gateway/
  LiteLLM/Hub 远程角色不删除。
- `kokoro-payment` acquisition package、registry/deploy、provider SDK/config/secret 与 Admin manifest删除；旧
  `kokoro-credit` process/db/route 不作为兼容层保留。Commerce/Credit/Redemption 的新 authority 只能由 W2A 建立，
  W1 期间对应 Surface/route 必须 unqualified/unreachable。
- `DATABASE_URL_SITE|USER|MODEL|CREDIT|PAYMENT|ADMIN`、各同域 `*_BASE_URL`、MySQL compose/K8s/CI job。
- `/sites/upsert`、Site/domain/app/policy/flag upsert/delete/restore、`/site-context/resolve`。
- `/auth/magic-links*`、旧 `/auth/sessions|refresh*`、`/users/ensure`、`/bff/teams|invites|team-sessions`、
  direct user/team delete/restore。
- Web `apps/user` 的 runtime Host换皮、Magic Link callback、preview auth bypass、Team UI/routes、checkout/plans/
  mock-pay/payment page、runtime-JWT session envelope 和相关 env/tests/i18n。
- Admin Web Nodemailer/Magic Link、payment page；Platform Admin dev/proxy auth、raw manifest proxy、`*` scope JSON。
- `x-kokoro-principal`、`x-kokoro-site-id` authority、同 Platform `callService` 与 `KOKORO_INTERNAL_SECRET_*` self-RPC。
- 说明上述旧方式的 INDEX/README/handbook 内容；Git 已保存历史，不留“deprecated but supported”文字。

真正独立的 Model Gateway/Hub remote config 不在本条误删范围；但它们访问 Platform 必须用新 contract/policy。

### 14.4 rollback

数据库 cutover 前保存可恢复的旧 dev snapshot 并 archive 原 MySQL volume，仅用于整套故障回滚，禁止新系统读取，
不得自动销毁。切换失败时只能整套回到旧 prelaunch environment，不能一部分走 PostgreSQL、一部分继续 MySQL。
新 schema migration 必须前向修复；正式接受新写入后不得回滚到会丢新事实的旧 MySQL。

## 15. 实现序列与 owner

| slice | owner | 产物 | 退出条件 |
|---|---|---|---|
| W1-A storage/UoW | Platform Data | PostgreSQL schema、migration、outbox/inbox、receipt | 真 PG constraint/rollback/serializable tests |
| W1-B security/policy | Platform Security | workload exchange、context builder、Risk snapshot、policy/effect authorizer、Data Rights participant contract | header/site/env/region/epoch/Risk negative tests |
| W1-C model-control | Platform Model Control | legacy inventory/import、catalog/assignment owner ports、consumer cutover | source/projection digest parity、Site authorization、old service zero consumer |
| W1-D Site/release | Platform Site + Web Fleet | lifecycle、bindings、Profile、release/activation/suspend/decommission | 两独立 project activate/rollback/drain/suspend/decommission |
| W1-E Identity | Platform Identity | registration/verify、password reset/change、TOTP/recovery、email、session/revoke/disable | 全 PRD-01 Core journey + real PG race/replay tests |
| W1-F personal bootstrap | Workspace + Commerce | atomic personal graph、redeem-only BillingAccount shell | failure injection leaves zero partial aggregates；无 Credit/Grant shortcut |
| W1-G Admin | Admin + Security | OIDC transaction、typed scopes/axes、approval/command/audit | self-escalation、env/region/device/breakglass、atomicity tests |
| W1-H removal/certification | all owners + QA/SRE | old surface deletion、seven-layer scan、deployables/runbook | W1 evidence approved；Redeem/Credit 明确等待 W2A |

同一 slice 可分 PR，但没有通过前一 slice contract/constraint gate，不得以 fake repository 宣称后一 slice完成。

## 16. 真实测试与证据

### 16.1 测试层

- **Static architecture**：禁止 Platform 内 `fetch/callService` 到本地 owner；禁止跨 module import
  `infrastructure/repository/Prisma/private table`、raw transaction handle、sibling source、Site-specific branch 与旧
  env/route；每个 public barrel/table/deployable 有唯一 owner。
- **Unit/property**：全部状态机转移、Site/Global/BreakGlass scope oneof、environment/region/device/assurance/step-up、
  caller-scoped idempotency digest、Risk snapshot、epoch comparison、registration/verification separation、TOTP timestep/
  recovery-code replay、refresh generation、domain normalization/takeover cooldown、decommission plan invalidation。
- **真实 PostgreSQL integration**：partial unique、FK/check、pending registration 与 activation/bootstrap 两个
  serializable transaction、outbox atomicity、password reset/email/MFA/recovery receipts、refresh race/reuse、
  last-owner personal invariant、approval/mutation/audit rollback、LegalHold/participant epoch、SKIP LOCKED takeover。
- **Contract**：OpenAPI/Connect generated client/server compatibility；未知 field/version、wrong audience、oversize、
  malformed credential fail closed。
- **E2E**：两个根 workspace 外不同 repository/lock/artifact/deployment 的 Site；同一 email 两套独立账号/
  Workspace/session/reset/recovery/Support/Data Rights；A cookie/workload/domain 不可访问 B；独立发布、回滚、
  current/candidate/draining、暂停/恢复、decommission 与受控 domain new-site takeover。
- **Security**：Host/header/body Site forgery、stolen/revoked binding、disabled User/Site、session replay、CSRF、
  OIDC issuer/aud/azp/nonce/PKCE/acr/auth_time、managed-device、staging↔production/region replay、self-escalation、
  maker=checker、omitted Site/global、Global↔BreakGlass confusion、Risk timeout/invalid/stale decision。
- **Payment negative**：七层逐项静态 + runtime 证明；对旧 checkout/refund/provider/admin path 发请求，确认
  stable `ACQUISITION_CHANNEL_DISABLED`、无 DB row/egress/secret read/SDK init；真实 provider receipt preflight 必须
  hard stop，不能导入只读死档后继续。
- **Failure/DR**：provider timeout/outcome unknown、pointer CAS race、Worker crash/lease takeover、PostgreSQL
  backup restore 后 receipt/release/session/model-control/participant consistency、drain crash、decommission partial、
  IdP/Risk/Notification unavailable 与 migration advisory-lock/forward-repair。
- **GA non-regression**：现有 GA suite 全绿；golden-byte test 证明 `run.request`/`run.cancel` 与当前 contract 完全一致，
  schema negative test 证明 Site/User/Workspace/grant/auth/credit fields 未进入 GA；W2A+W3 qualified 前 Prepare route
  manifest/descriptor 为零且 default deny。

测试不得 skip 缺少的 PostgreSQL/IdP/provider emulator；缺依赖就是红。repository mock 不能证明 transaction。
实现验证复用唯一默认 Infra composition，不为 agent/slice 启动额外 stack；结束后删除临时 container，不删除
volume/image/dev data。旧 MySQL PASS 不算新证据。

### 16.2 SLO、容量与运维证据

- Site product-context exchange 在已缓存有效 manifest 时 p95 `<200ms`；Platform Admission 本身 p95 `<250ms`；
  password/TOTP login 在冻结 Argon2 参数与目标硬件下 p95 `<750ms`，不得为压测降低安全参数。
- 验证 100 Site、100 Admission/s、10,000 跨系统 SSE envelope 下 Platform 非 SSE 依赖的公平性，并覆盖 5 倍
  短突发；超过 envelope 有界 429/backpressure，不能跳过 Risk/Policy/receipt/outbox。
- Platform API/Worker 月可用性目标 99.9%；critical Site/User/operator epoch 在下一 effect point 立即生效，普通
  authorization propagation p99 `<=30s`。SLI 冻结 numerator/denominator/window/exclusion/source/owner/page threshold。
- 已确认 Platform transaction 在实例/AZ 故障下 RPO 0、服务 RTO `<5m`；redeem-only 首发 region loss 使用
  PostgreSQL WAL/object version 异地复制，RPO `<=5m`、RTO `<=60m`，并有真实 restore/role rotation/runbook drill。
- 指标至少覆盖 context exchange/auth/admission latency+deny、Risk decision、session revoke/reuse、outbox/inbox lag、
  worker lease、release activate/drain、decommission participant、Admin approval/unknown、model import parity；trace 使用
  correlation/causation safe refs，不记录 email/token/OTP/code/provider secret。

### 16.3 证据包

实现完成后写入 `docs/reports/evidence/wave-1/`：

```text
platform-postgres-migration-and-transaction.md
platform-module-uow-and-model-control-cutover.md
site-project-release-suspend-decommission.md
identity-complete-journey-and-session-security.md
admin-oidc-scope-axes-breakglass-atomicity.md
risk-data-rights-notification-participants.md
redeem-only-seven-layer-closure.md
platform-deployables-slo-load-and-dr.md
ga-semantic-non-regression.md
wave-1-clean-replacement-inventory.md
```

每份包含 commit/pin、contract digest、artifact digest、命令、环境版本、原始 report 路径、通过/失败数、
时间和 owner。`ReleaseCertification` 绑定上述 digest；“代码存在”“测试 written”“旧 MySQL suite pass”不算证据。

## 17. Wave 1 退出门与 P0 closure

| P0 | 架构解法 | 必需证据 |
|---|---|---|
| Site-bound complete auth | pending registration→verify activation→explicit login + reset/change/MFA/recovery/email/session；effect recheck | PRD-01 Core 全旅程、双 Site 同邮箱/恢复隔离、replay/fixation/race 全拒 |
| 两个独立 Site project | app-kit/scaffold/reference + 每 Site 独立 repo/lock/artifact/deploy/release | 两个 provenance、独立 activate/rollback/drain/suspend/decommission 与串味负测 |
| Admin 无 DB/bypass | generated Connect + bound OIDC transaction + typed scope/axes + local command bus/UoW | import scan、self-escalation、env/region/device/breakglass、atomic rollback |
| ModelControl 本地 owner | W1 canonical import + projection parity + consumer cutover | source/import digest、Site assignment auth、旧 model service consumer=0 |
| redeem-only acquisition closure | §10 七个 gate；W1 不实现 Redeem/Credit，等待 W2A qualification | stable disabled code、SBOM/env、runtime no-row/no-egress；W2A 未过前 Redeem unqualified |
| Data Rights participant ready | Identity/Workspace/Site owner contract + subject generation + plan/epoch receipt | export/freeze/disposition/verify、LegalHold invalidation、partial recovery；不冒充 Wave 7 coordinator完成 |

最终退出还要求：

- ADR-012 已 supersede ADR-005；PostgreSQL 18 是 Platform 唯一事实源，默认 Infra/INDEX 无 MySQL 双口径，
  旧 volume 只 stop/archive 未自动删除。
- registration begin、verify/personal bootstrap、reset/change/recovery、refresh、Admin local execute、release pointer/
  drain transaction 经真实 PG 验证；Risk assessment 无 transaction 内 fetch。
- Site suspend/resume/decommission、User disable、session revoke 在最终 effect point 生效，同时 Support/Data Rights/
  mandatory inbound 的窄入口不被整站误杀。
- `deployables.yaml`、SLO/load/DR/runbook 与 evidence digest 完整；API/Worker/migrator/Site/Admin 角色可独立发布/回滚。
- 当前旧 route/env/process/test/文档清退，扫描为零；不存在 compatibility adapter。
- W2A 是 Redeem/Fulfillment/Credit 唯一实现；W2A 未通过时相应 Surface/route 未 qualified/unreachable。
- GA 语义、`run.request`/`run.cancel` golden-byte 与禁止字段 contract test 全绿；W2A+W3 qualified 前 Prepare
  descriptor/route 不存在。
- 证据尚未生成时状态只能是 `implementation-not-verified`，不得写“P0 已通过”。

## 18. 已接受风险与默认处置

| 风险 | 默认处置 |
|---|---|
| PostgreSQL clean replace 占用 Wave 1 容量 | 不保留 MySQL 双轨；先做 storage/UoW，换取后续事务简单性 |
| 每 Site 独立 project 增加 fleet 维护 | scaffold + signed app-kit + compatibility floor；不回退 Host 多租户单 artifact |
| effect-point 实时复核增加延迟 | 本地 Platform 同 txn；远程用短 token + sensitive Admission，先以安全为准 |
| OIDC/IdP 不可用阻断 Admin | fail closed + 窄 breakglass；不恢复 Magic Link/dev header |
| release provider timeout 产生未知结果 | durable attempt/observation/reconcile；不猜测成功或盲重试 |
| 意外发现真实旧 payment fact | W1 cutover 硬停止；需 W2B historical responsibility path 或 Finance/Data/Legal 签名 disposition，不导入只读死档蒙混上线 |
| 大规模 Site session revoke 扫描成本 | epoch 使 effect 立即失效，异步批量标记 session 负责清理而非安全正确性 |
| W1/W2A Commerce owner 重叠 | W1 仅建 BillingAccount bootstrap shell；Redeem/Fulfillment/Credit ports、route、事实链和认证只在 W2A |
| Admin/Site 安全收紧误杀法定义务入口 | typed suspension policy 与独立 minimal audience 保留 Support/Data Rights/mandatory inbound，不恢复产品副作用 |

以上取舍为本 Wave 的默认实现答案。任何改变都必须新 ADR/父设计复审，不能在代码中以 feature flag、
fallback、兼容 route 或 Site-specific branch 偷偷改写。

## 19. Internal review record

- 2026-07-28：独立架构评审结论为 `APPROVED`，未发现阻止 Wave 1 实施的开放 P0。
- 用户已授权 Root、Infra、Platform 与 Web 的非 GA 实现；实施必须按独立子仓提交、验证、发布与 pin promotion。
- GA 授权仍为 `false`：仅允许 golden-byte、禁止字段与兼容性回归，不得修改 graph、checkpoint、control、terminal、handoff 或既有 `run.request`/`run.cancel` 语义。
- `chat.execution.prepare` 在 W2A 与 W3 共同 qualified 前不得出现 descriptor、route 或兼容实现；任何偏离本文默认裁决的变更必须重新评审。
