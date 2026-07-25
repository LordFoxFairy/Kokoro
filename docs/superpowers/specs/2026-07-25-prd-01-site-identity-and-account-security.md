---
artifact: product-requirements-document
prdId: PRD-01
version: "1.0"
created: 2026-07-25
status: internal-review-active
scope: site-local-identity-authentication-session-mfa-recovery-account-security
accountableProductRole: Identity & Collaboration PM
mandatoryCosigners: [Security, Privacy, Support, Web, Identity Engineering, QA]
engineeringOwner: team:identity-engineering
qaOwner: team:identity-quality
supportOperationsOwner: team:identity-support-operations
namedOwnerAssignmentStatus: assigned-team-responsibility-ids
implementationAuthorized: false
---

# PRD-01：Site Identity 与 Account Security

## 1. Overview

### Problem

当前实现只覆盖部分 Magic Link 和 runtime token 换签，无法形成注册、法务接受、邮箱验证、密码、OAuth、
MFA、设备会话、账户恢复、Security Notification 和 Support 的生产闭环。更严重的是 Web AuthSession 与
Workspace namespace token 混用，Host/配置/Risk 某些路径 fail-open；这些问题会直接阻断 Redeem、Chat、
数据权利和多 Site 上线。

### Solution

Platform Identity 成为 Site-local User、LoginIdentifier、Credential、FederatedIdentity、Authenticator、
AuthSession、AccountRecovery、SecurityEvent 和 LegalAcceptanceEvidence 的唯一真源。每个 Site Web 只通过
绑定自身 workload identity 的 BFF 发起认证；浏览器不能声明 siteId。Web AuthSession 与 GA runtime grant
完全拆开：用户选择 Workspace/Project 后，Platform 才换出只含 opaque namespace 的短期执行授权；GA 仍不
接收 User/Site/Workspace。

密码、TOTP、OAuth/OIDC、Passkey 使用成熟标准和库；Kokoro 只拥有产品状态、Site 隔离、策略、审计和恢复。

### Users and stories

| ID | User story | Priority |
|---|---|---|
| ID-US-01 | Visitor 能注册、接受本站法务版本、验证邮箱并安全进入产品 | P0 |
| ID-US-02 | User 能登录、登出当前/全部会话、修改或重置密码 | P0 |
| ID-US-03 | User 能启用 TOTP、使用单次恢复码并管理设备/会话 | P0 |
| ID-US-04 | User 能安全变更邮箱并收到旧/新邮箱通知 | P0 |
| ID-US-05 | 丢失多个认证器的 User 能通过严格 AccountRecovery 恢复 | P0 |
| ID-US-06 | 同邮箱在不同 Site 得到完全独立的账户、会话和后续权益 | P0 |
| ID-US-07 | OAuth 启用时不成为自动合并或账户接管旁路；其他认证方法未完成专项认证前不能启用 | P0 if-enabled |
| ID-US-08 | Admin/Support 能处理安全事件，但看不到 secret、不能越权或直接改凭据 | P0 |

## 2. Goals、Metrics and Non-Goals

### Goals

1. 在一个 Site 内完成注册到安全登录、恢复和撤销的完整链路。
2. 相同邮箱在不同 Site 的 User、Credential、Session、Workspace、权益和 Support 完全隔离。
3. 每个失败/locked/pending 状态都有安全 RecoveryAction。
4. 用户可以撤销当前、单设备、除当前外全部或全部 AuthSession。
5. 密码、OAuth、MFA reset、邮箱变更和 Support 不能成为账户接管旁路。

### Metrics

| Metric | Core target |
|---|---:|
| 跨 Site User/Cookie/token/callback/Support 泄漏 | 0 |
| 未授权 AuthSession/runtime grant 签发 | 0 |
| 错 purpose/expired/consumed token 被接受 | 0 |
| TOTP timestep 或 recovery code 重放成功 | 0 |
| 注册到邮箱激活 | p50 ≤ 2m，p95 ≤ 10m；外部邮件延迟单列 |
| 密码登录服务端延迟 | p95 ≤ 1.5s；外部 challenge 时间排除 |
| Auth API availability | ≥ 99.95% |
| 撤销提交后 refresh 再成功 | 0 |
| revocation 到所有 protected API | p99 ≤ 10s |
| mandatory SecurityEvent/NotificationRequest 原子创建 | 100% |
| lost-response 恢复同 AuthTransaction receipt | 100% |
| 登录/恢复 enumeration 自动化可区分 | 0 |

### Non-Goals

- 不建立跨 Site Global User，不自动共享 Workspace、套餐、积分或历史。
- 不在本 PRD 实现 CLI/Desktop device flow；属于 PRD-A2/A3。
- 不支持安全问题/KBA 或 SMS 作为 Core MFA。
- Support 不能设置密码、查看 TOTP secret/recovery code 或替用户跳过 MFA。
- Export/Deletion 主流程属于 PRD-15；本 PRD 只提供 re-auth、session revoke 和 Identity participant。
- 不修改 GA graph、namespace 或运行行为。

## 3. Scope

### Core-always

- Email + password registration、LegalAcceptanceEvidence、email verification/resend。
- password login/change/reset；current/all session logout。
- TOTP enrollment/challenge/disable 与 single-use recovery codes；功能必须可用，但普通用户是否强制启用由
  Site/Risk policy 决定。
- session/device list、single/other/all revoke。
- email change、security events/notifications、full AccountRecovery。
- Site-local isolation、Admin/Support 最小运营、deletion 前 step-up。

### If-enabled（启用后成为 Profile P0）

- Google/GitHub 等 OAuth/OIDC、OAuth link/unlink/new registration；每个 provider/client 独立认证。

### Not-enableable in this revision

- Magic Link login、Enterprise OIDC/SAML、Passkey/WebAuthn 保留 contract kind，但在补齐 method-specific Journey、
  FR、AC、安全评审和 provider certification 前，Profile compiler 必须拒绝启用，不能复用笼统 `auth` Surface
  或 OAuth 验收旁路上线。

### P1

- Passkey 作为默认 phishing-resistant authenticator。
- 多 verified recovery address、IdP discovery、用户安全事件报告下载、风险型 trusted-device UX。

## 4. Product Objects and Ownership

```text
User(siteId, subjectGeneration, lifecycleStatus)
LoginIdentifier(kind=email, normalizedValue, verifiedAt, status)
Credential(kind=password, verifierVersion, status, rotatedAt, compromisedAt)
FederatedIdentity(siteId, issuer, subject, metadataSnapshot, status)
Authenticator(kind=totp|passkey, status, enrolledAt, lastUsedAt)
RecoveryCode(authenticatorId, secretHash, consumedAt, replacementSetRef)
AuthTransaction(purpose, site/host/audience, state, expiry, attemptBudget, risk/return refs)
AuthSession(siteId, userId, sessionId, authTime/strength/factors, idle/absolute expiry, revoke fact)
RefreshTokenFamily(sessionId, generation, rotation/reuse state)
DeviceObservation(platform/browser/approximate region/first-last seen)
LegalAcceptanceEvidence(site/user/document/revision/locale/time/evidence digest)
AccountRecovery(state, requiredProofSet, cooldown, decision refs)
SecurityEvent(type, severity, actor/session/risk/notification refs)
```

Ownership：Identity owns above；Site owns Host/SiteRelease/auth-method policy/LegalRevision refs；Risk owns Decision/
Restriction/Epoch；Notification owns delivery；Data Governance owns retention/deletion；Support owns Case；Workspace
在 User active 后 bootstrap。NextAuth/OAuth Provider 等只是 adapter，不拥有 Site-local User。

## 5. Request and Token Boundaries

- Browser/BFF：trusted SiteContext + AnonymousPrincipal 或 UserPrincipal。
- Browser JS 不持 access/refresh token；BFF 使用 Secure/HttpOnly/SameSite `__Host-` cookie。
- AuthSession 主体固定为 `siteId + userId + sessionId + authStrength`，不能属于 Workspace namespace。
- 用户选 Project 后，Platform 以 AuthSession + Membership + Admission 换取短期 runtime grant；grant 只向 GA
  暴露 opaque namespace 和必要授权 refs。
- grant 签发前必须在同一受信查询/事务快照中证明：
  `SiteContext.siteId == User.siteId == AuthSession.siteId == Workspace.siteId == Membership.workspace.siteId ==
  BillingAccount.siteId == Project.siteId == ExecutionSpace.siteId`，且对象属于当前 subject、membership 和
  authorization revision。任一不相等、缺失、过期或跨 Site cache hit 都 fail closed，且不泄漏对象是否存在。
- runtime grant 绑定 audience、operation/resource scope、opaque namespace、subject generation、AuthSession ref、
  membership/authorization/restriction epoch、issued/expiry 和唯一 replay identity；这些业务 refs 仅由 Platform
  验签/授权层消费，不下推为 GA 的第二身份轴。GA 仍只消费 opaque namespace 与执行所需窄授权。
- `/auth/sessions` 类接口不能接受自由 `siteId + externalUserId` 直接签发；只能消费已完成且不可重放的
  AuthTransaction 或可信 ActorPrincipal。
- callback、token、cookie、CSRF、OAuth client/redirect、email link 全部 Site/Host/audience/purpose bound。

## 6. User Lifecycle and Visible States

User lifecycle、AuthTransaction、Credential、Authenticator、AuthSession 分开建模，再投影：

| Product state | Meaning | CTA/Recovery |
|---|---|---|
| registration_pending | 注册事务未完成 | resume/restart |
| verification_pending | User/credential 已建但邮箱未验证 | resend/change email/Support |
| active | 可认证和进入已授权产品 | continue |
| challenge_required | MFA/risk challenge | provide factor/recovery |
| locked | 显式 Risk/Security restriction | wait/Support/appeal category |
| recovery_pending | AccountRecovery 处理中 | provide evidence/wait |
| email_change_pending | 新邮箱待验证 | resend/cancel/keep old email |
| session_revoked | 当前 AuthSession 无效 | reauthenticate/return intent |
| deletion_pending | Data Governance workflow 中 | progress/cancel window/Support |
| deleted | 当前 subject generation 关闭 | new registration creates new generation |

失败计数不能永久锁账号；`locked` 只来自版本化 Decision/Operator command。pending/unknown 显示更新时间、
deadline、owner 和安全 CTA；客户端 retry 复用同 AuthTransaction identity。

## 7. Functional Requirements

### 7.1 Registration、Legal and Verification

- SiteRelease 冻结 allowed methods、age/region eligibility 和 mandatory LegalRevision。
- Terms、Privacy acknowledgment、age declaration、optional Marketing Consent 分开记录；营销不得预选或作为
  服务条件。
- 创建 User/Identifier/Credential/Acceptance/VerificationChallenge/NotificationRequest 使用一个 Platform UoW。
- User 初始 `verification_pending`，不能取得 runtime grant。
- 同 Site 重复 email 公开响应一致：未验证账号安全 resend；已存在账号发登录/重置指引，不泄漏存在性。
- 不执行 Gmail dot/plus 等 provider-specific email 折叠。
- verify token CSPRNG、server-side hash、single-use、purpose/site/host/audience/generation/expiry bound。
- 邮箱验证不等于登录；链接允许跨设备打开但不建立 AuthSession。
- 验证成功才原子 activate User 并触发 PRD-02 personal bootstrap。
- 未验证账号按 RetentionPolicy 清理；未来注册使用新 subject generation。

### 7.2 Password

遵守当前 NIST/OWASP 基线：单因子密码最少 15 字符、支持至少 64 字符/Unicode/space/password manager paste；
不强制大小写数字符号组合、不定期轮换、不用安全问题；拒绝常见/已泄露密码。Verifier 使用版本化 Argon2id
参数，成功认证可透明 rehash。长度按 Unicode code point 计算，完整输入在 hash 前使用统一 NFC 规范化且绝不
截断；客户端、blocklist 与 verifier 使用同一 revision。修改密码要求近期 re-auth，撤销其他 session、rotate
current session 并通知。

### 7.3 Login and Logout

- 登录 transaction 由可信 SiteContext 创建；未解析 Host 或配置缺失 production fail closed。
- 错误不区分 email 不存在、password 错、未激活等可枚举事实。
- 多维限速：Site、IP、account lookup hash、device/risk、攻击速度；高风险依赖失败不允许本机放行。
- 当前 logout 只撤销当前 session/family；“除当前外全部”和“全部设备”是独立确认操作。
- preview auth 是显式非生产 Profile/build；生产探针异常不能放行 workspace。

### 7.4 Forgot Password and Reset

- 请求统一响应/近似时长，不锁账号、不直接修改密码。
- reset token single-use、hash-only、Site/purpose/generation/expiry bound。
- 成功后不自动登录，默认 revoke 全部 session，MFA 仍有效并需重新 challenge，发送安全通知。
- 响应丢失查询 transaction receipt；同 key 不重复修改。
- 同时失去 MFA 进入 AccountRecovery，email reset 不能绕过第二因子。

### 7.5 OAuth/OIDC（if-enabled）

- Authorization Code + PKCE S256、OIDC nonce、server state、exact redirect、issuer/client/audience/Site/Host/
  return-intent binding；禁止 implicit、wildcard redirect 和任意 return URL。
- FederatedIdentity 唯一 `(siteId, issuer, subject)`；provider email 不是 identity key。
- 同 issuer/subject 在 Site A/B 得到独立 local User。
- `email_verified` 不自动链接现有 User；OAuth 新 User 仍完成本站 Legal/registration。
- email collision 要求先用已有 authenticator 登录，再显式 link；collision 响应不泄漏其他 User。
- link/unlink 要 recent re-auth；至少保留一个 active authenticator，不能把账户变成不可登录。
- 多 issuer client 使用 issuer identification response 或每 issuer 独立 redirect URI 防 mix-up；callback 校验
  ID Token/JARM（若使用）的 signature、issuer、audience/authorized party、nonce、code verifier、auth time 和
  transaction generation，authorization response/code 原子单次消费。
- discovery/metadata、authorization/token/JWKS endpoint 使用发布时 allowlist/pinning，不接受 callback 自报
  endpoint；provider access/refresh token 加密保存，绑定 client/resource/scope，rotation/reuse 按 provider
  policy 处理并审计。

### 7.6 TOTP and Recovery Codes

- Enrollment 两阶段：recent step-up → secret 显示一次 → valid code confirmation → active；未确认不影响旧登录。
- secret envelope encryption/key version，禁止 log/analytics/Support/QR cache。
- challenge 有 attempt budget/time window，同 timestep replay 拒绝。
- enrollment 生成一组 10 个、每个至少 128-bit 随机的 single-use code，只显示一次、server-side hash。
- 使用后失效并通知；regenerate 撤销整组旧 code。
- disable/reset 要另一 active factor 或正式 AccountRecovery；不能仅凭当前可疑 session。
- Admin 高权限认证由 PRD-10 要求 phishing-resistant factor；TOTP 不是 phishing-resistant。

### 7.7 Session and Device

- `AuthStrengthPolicyRevision` 映射已验证 factor 到产品认证强度，并冻结各敏感命令所需强度、recent-auth 最大
  年龄、idle/absolute timeout。AuthSession 的强度不得高于实际认证；step-up 不永久延长原认证保证。
- anonymous/pre-auth → authenticated、login、account switch、权限提升、step-up 和 recovery completion 都生成
  新的高熵 session id/refresh family，并原子失效旧 id，防止 session fixation。
- Core cookie 固定 `__Host-`、Secure、HttpOnly、SameSite、`Path=/`、无 Domain，cookie/session/server expiry
  一致；所有浏览器 mutation 同时验证 Origin 和不可预测 CSRF token，SameSite 不是唯一 CSRF 防线。
- DeviceObservation 只作说明，不是可信设备或权限证据。
- 用户看到 device type、browser、approximate region、first/last activity/current marker，不展示完整 IP。
- refresh family 每 AuthSession 独立 rotation；reuse 默认只 revoke 对应 family，Risk 可升级全账户 revoke。
- password reset、MFA recovery、account recovery、suspend 按 policy 推进 SecurityEpoch/revoke sessions。
- protected API 校验 revocation/epoch/auth strength，不等待长 JWT 自然过期。
- re-auth return intent 只允许签名 allowlist path，禁止 open redirect。

### 7.8 Email Change

- recent step-up；新 email 为 pending identifier，旧 email 保持 primary/recovery。
- 新 email 验证后原子切换 `(siteId, normalizedEmail)`；同时通知旧/新邮箱，旧邮箱提供 security response。
- commit 后 revoke 其他 sessions/rotate current；Site 内 collision 返回不透明 unavailable，不查询其他 Site。
- 无旧邮箱走 AccountRecovery；Support 不直接覆盖 email；provider email 不被本地变更改写。

### 7.9 Risk and Abnormal Login

signals 可含新设备、异常地区/速度、credential stuffing、token reuse；用户只见粗粒度 category。

- low：正常；medium：额外 challenge；high：deny + SecurityEvent/notification。
- Risk 依赖不可用时，registration/recovery/email/MFA/password sensitive mutation fail closed。
- 已有低风险 session 仅在仍持有效短期 signed decision 时可继续非敏感操作。
- failure 使用 rate/challenge，不用永久计数锁；new device、suspicious attempt、lock/unlock 都通知。

### 7.10 Full Account Recovery

- `RecoveryPolicyRevision` 按恢复目标与原账户认证强度冻结允许的 evidence class、组合、有效期、attempt budget、
  cooldown、operator assurance 与禁止动作；Support 和 Site 配置不能在运行时降低 required proof set。
- Core 自助完整恢复只接受：未使用的预注册 recovery code；或仍可用的 active authenticator + 恢复开始前已
  verified 的安全渠道。recovery code 在 Core 被定义为单次完整恢复凭据，因此必须至少 128-bit、只存 hash、
  单次使用、使用即通知并撤销整组；单独 email、Support 判断、设备信息、交易事实或 KBA 均不够。
- 用户既无 recovery code 又无 active authenticator 时，Core 不承诺可恢复。只有 Site 预先启用了经过安全评审
  的外部 identity-proofing recovery method，才能由 Support 创建高保证恢复；该流程要求 policy-bound proof、
  JIT action/resource scope、双人批准、独立审计告警和至少 72h cooldown。Support 不得自由裁量或数据库绕过。
- RecoveryTransaction 冻结 proof set、risk decision、cooldown、subject generation，以及恢复开始前 verified
  security channel snapshot。
- 完成时 revoke compromised credentials/authenticators/sessions，绑定 replacement factor，推进 SecurityEpoch，
  启动高风险操作 cooldown；replacement factor 必须实际 challenge 成功后才 active。cooldown 内禁止邮箱/MFA、
  Payment/Redemption liability、ownership、数据导出/删除等高风险变更。
- 开始、失败与完成通知至少发送到恢复开始前的 channel snapshot；恢复中新增渠道只能额外接收，不能替代旧渠道。
- Support-assisted recovery 要 operator step-up、maker-checker、evidence/timeline；不能直接设 `mfa=false`。

## 8. Durable Notification Contract

Mandatory、不可关闭：verification、reset request/completion、password change、new/abnormal device login、email
change、MFA enable/disable/reset、recovery-code use/regenerate、AccountRecovery lifecycle、session revoke、suspend/
unlock、deletion lifecycle。

每条 NotificationRequest 冻结 Site/recipient/source version/SecurityEvent/template/brand/legal/locale/deep-link/
idempotency。Auth transaction 与 request/outbox 原子；Notification owns retry/receipt/DLQ。SMTP timeout 不让认证
状态 unknown，resend 复用或 supersede challenge，不创建第二个 User。高风险 delivery 超 SLA page owner。

## 9. Admin and Support

- OperatorPrincipal 决定 Site scope，query/body 不扩大；同 email 其他 Site 不可见。
- email 默认 mask；查看完整 PII 要 reason/step-up/audit；factor 只显示 type/status/time。
- Allowed typed commands：resend verification、revoke one/all session、suspend/unsuspend、require credential reset、
  open MFA recovery、cancel email change、resolve RecoveryCase。
- suspend/unsuspend、all-session revoke、MFA recovery、Recovery resolution 按风险要求 maker-checker。
- 禁止普通 Admin create User、mark email verified、查看 token/recovery code、设置临时 password 或 DB write。
- Global analytics、Global security response 与 BreakGlass 是三个不同 scope。BreakGlass 必须绑定 incident/Case、
  JIT、action/resource/field/TTL 限定、maker-checker、禁止批量导出，并触发实时审计告警与事后复盘；普通
  Support 不存在跨 Site email search。
- Support Case kinds：verification delivery、locked、password/MFA recovery、OAuth collision、email change、session
  compromise、full recovery；未登录用户通过不枚举账号的 provisional Case，核验后才关联 User。

## 10. Edge Cases

| Scenario | Expected behavior |
|---|---|
| Site A token 在 Site B callback | fail closed；无 User/Session/link mutation |
| token purpose 混用/重放/过期 | reject + resend/restart RecoveryAction |
| mail send failed after request commit | deterministic auth state；Notification retry/resend same intent |
| OAuth email matches local User | no auto-link/duplicate；authenticate existing User first |
| unlink last authenticator | reject + add another method guidance |
| TOTP enroll 未确认 | pending discarded/expired；旧 auth unaffected |
| TOTP/recovery code replay | reject、no second session、SecurityEvent |
| one User logout in shared Workspace | only own AuthSession revoked；namespace peers unaffected |
| Risk dependency down | sensitive mutation fail closed、no partial write |
| production auth config/probe missing | startup/request fail；never preview-authenticated fallback |
| email change response lost | query same transaction；no second primary identifier |
| recovery while deletion pending | policy/Support decision；不能偷偷创建新 generation/恢复 deleted subject |
| Site/Principal/Workspace/Project/ExecutionSpace 任一交叉替换 | grant exchange fail closed；不签 namespace grant、不泄漏对象存在性 |
| anonymous session id 在登录后复用 | 生成新 AuthSession/family，旧 id 原子失效 |
| OAuth issuer/client/code/token mix-up 或 replay | callback fail closed，无 link/User/AuthSession mutation |
| 用户丢失全部 factor 与 recovery code | 不降级到 email/Support/KBA；仅可走预批准 external identity-proofing，否则明确不可恢复 |

## 11. Acceptance Criteria

### AC-ID-01 — Registration and legal evidence

```gherkin
Given Site A requires Terms v3 and Privacy v5
When a visitor registers and accepts both revisions
Then User is verification_pending
And Credential, acceptance evidence, verification challenge and NotificationRequest commit atomically
And no runtime grant is issued before verification
```

### AC-ID-02 — Same email, two Sites

```gherkin
Given a@example.com is active in Site A
When it registers and verifies in Site B
Then Site B creates distinct User, Credential, AuthSession and personal Workspace
And Site A reset, MFA, Support and entitlements remain unchanged
```

### AC-ID-03 — Enumeration resistance

```gherkin
Given one email exists and one does not
When anonymous registration/reset requests are submitted
Then public response shape, guidance and observable timing class are equivalent
And only the applicable Site-local workflow changes
```

### AC-ID-04 — Token binding

```gherkin
Given a verify_email token belongs to Site A
When replayed, expired, used for reset, or opened through Site B
Then it is rejected without changing User/AuthSession
And a safe resend/restart action is shown
```

### AC-ID-05 — Password reset

```gherkin
Given an active MFA user consumes a valid reset token
When a new password is committed
Then prior sessions are revoked, the user is not auto-logged-in, MFA remains required
And a mandatory security notification is enqueued
```

### AC-ID-06 — OAuth callback and collision

```gherkin
Given an OAuth transaction is Site A/client/issuer/redirect bound
When callback context differs or reported email matches an unlinked local User
Then callback fails or requires existing-user authentication
And no auto-link, duplicate User or cross-Site session is created
```

### AC-ID-07 — MFA replay

```gherkin
Given a TOTP timestep or recovery code was accepted
When submitted again
Then challenge is rejected, no second AuthSession is created, and SecurityEvent is recorded
```

### AC-ID-08 — Single-session revoke

```gherkin
Given a user has phone and laptop sessions
When the phone is revoked
Then only its refresh family fails within the revocation SLO
And the laptop remains active unless Risk explicitly escalates account-wide revoke
```

### AC-ID-09 — Email change

```gherkin
Given change old@example.com → new@example.com is pending
Then old remains primary until new verification commits
When committed, the switch is atomic, other sessions revoke, and both addresses are notified
```

### AC-ID-10 — Full recovery

```gherkin
Given password and TOTP are both lost
When required proof and maker-checker review succeed
Then compromised factors/sessions revoke, replacement factors bind, SecurityEpoch increases
And every verified channel receives completion notification
```

### AC-ID-11 — Risk/config fail closed

```gherkin
Given production Identity/Risk/signing/Site resolution is unavailable or incomplete
When registration, reset, MFA recovery or auth startup occurs
Then no preview/fallback authentication or partial mutation is allowed
And operator diagnosis plus safe user recovery is provided
```

### AC-ID-12 — Admin scope

```gherkin
Given Site A Support searches an email also present in Site B
Then only Site A is returned and no signal reveals Site B
And broader access requires independently authorized Global/BreakGlass scope
```

### AC-ID-13 — Runtime grant tuple isolation

```gherkin
Given Site A and Site B each have a User, AuthSession, Workspace, BillingAccount, Project and ExecutionSpace
When any one element from Site B or a stale authorization epoch is substituted into Site A's grant exchange
Then Platform denies the exchange without revealing which object exists
And no runtime grant or GA request is produced
When all Site A elements and revisions match
Then the issued grant exposes only its opaque namespace and narrow execution authorization to GA
```

### AC-ID-14 — Recovery assurance

```gherkin
Given an MFA user has lost password and TOTP
When the caller presents only email control, device facts, transaction history or Support assertion
Then full recovery is denied without changing authenticators, sessions or SecurityEpoch
When an unused pre-registered recovery code succeeds and a replacement factor is challenged successfully
Then recovery commits once, old factors and sessions revoke, cooldown begins, and pre-recovery channels are notified
```

### AC-ID-15 — Session fixation and step-up

```gherkin
Given an attacker knows a pre-authentication session id
When the user logs in or completes step-up
Then a new unpredictable AuthSession and refresh family are issued and the old id is unusable
And sensitive commands reject expired recent-auth or insufficient AuthStrengthPolicyRevision
```

### AC-ID-16 — OAuth mix-up and replay

```gherkin
Given an OAuth transaction is pinned to one Site, issuer, client, redirect, nonce and PKCE verifier
When an authorization response, code, token endpoint, issuer or client is substituted or replayed
Then callback validation fails closed
And no User, FederatedIdentity, Credential or AuthSession changes
```

## 12. Journey and Evidence Mapping

| Canonical journey | Acceptance scenarios |
|---|---|
| ID-01 register/verify | AC-ID-01、02、03、04、11 |
| ID-02 login/logout | AC-ID-03、11、15 |
| ID-03 password/account recovery | AC-ID-05、10、14 |
| ID-04 OAuth | AC-ID-06、16 |
| ID-05 MFA | AC-ID-07、10、14、15 |
| ID-06 device/session | AC-ID-08、15 |
| ID-07 export/delete participant | PRD-15 scenarios + AC-ID-10、12 |

## 13. Analytics, Dependencies and Risks

Events：flow started/completed/denied/recovered、method、challenge、session create/revoke/reuse、email/MFA/password/
recovery lifecycle、SecurityEvent、mandatory notification state。禁止 email/IP/OAuth subject/token/secret；仅 Site、
Profile、method、flow revision、粗粒度 outcome/risk reason。

| Risk | Mitigation |
|---|---|
| 旧 Magic Link route 继续承担 verify/reset/login 多 purpose | clean remove；本 revision 标记 not-enableable，未来专项 PRD 必须按 purpose 分离 |
| Identity 与 namespace 再耦合 | Web AuthSession 与 runtime grant/audience 分离；GA only namespace |
| OAuth 自动合并导致 takeover | issuer+subject identity、explicit authenticated link、no email auto-link |
| MFA recovery 成为弱旁路 | proof set、cooldown、SecurityEpoch、maker-checker、multi-channel notify |
| Notification failure 破坏 auth | request/outbox 原子，delivery 独立 retry/receipt |
| Risk/Redis failure fail-open | sensitive flows fail closed、distributed policy authority |
| Admin 过强 | typed commands、scope/step-up/maker-checker、no secret/DB writes |

Email canonicalization 使用版本化 `EmailNormalizationPolicyRevision`：trim transport-only whitespace、Unicode/IDNA
域名处理、local-part case policy、canonical bytes 和迁移规则在一个实现中冻结；注册、OAuth collision、email
change、Support lookup 和数据库唯一约束必须引用同一 revision，不做 provider-specific dot/plus 折叠。

Enumeration certification 使用黑盒攻击模型，覆盖 status/body length/cache、rate-limit bucket、时延分布和邮件/
Support side effect；样本量与统计阈值由 Security Test Policy revision 冻结并按 Site 执行，不能仅靠相同文案通过。

Wave 1 architecture Spec 必须 clean rewrite 当前 User/session/magic-link/Host-preview 边界，冻结 schema、token family、
cookie、OAuth/TOTP adapters、migration 和双 Site E2E。成熟标准依据：[NIST SP 800-63B-4](https://pages.nist.gov/800-63-4/sp800-63b.html)、
[OAuth 2.0 Security BCP RFC 9700](https://datatracker.ietf.org/doc/html/rfc9700)、
[OWASP Authentication](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)、
[Forgot Password](https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html)、
[MFA](https://cheatsheetseries.owasp.org/cheatsheets/Multifactor_Authentication_Cheat_Sheet.html) 和
[Session Management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)。

本文批准不授权实现，也不触及 GA runtime。
