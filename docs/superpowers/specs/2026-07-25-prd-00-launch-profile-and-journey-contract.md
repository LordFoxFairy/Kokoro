---
artifact: product-requirements-document
prdId: PRD-00
version: "1.1"
created: 2026-07-25
status: approved
approved: 2026-07-31
scope: launch-profile-enabled-surface-journey-state-metric-certification-contract
accountableProductRole: Platform Product Lead
mandatoryCosigners: [Site Fleet, SRE, Security, Release, Product Operations, QA]
engineeringOwner: team:site-platform-engineering
qaOwner: team:release-quality
supportOperationsOwner: team:site-fleet-operations
namedOwnerAssignmentStatus: assigned-team-responsibility-ids
implementationAuthorized: true
implementationAuthorizationScope: core-redeem-chat-and-web-release-composition-foundation
---

# PRD-00：Launch Profile 与 Journey Contract

## 1. Overview

### 1.1 Problem Statement

Kokoro 支持一个后端服务多个独立 Site，每个 Site 又可以只开放 Chat、Music Studio 或其他组合。如果“开放
什么”只靠前端菜单、Feature Flag 或口头约定，系统会出现五类生产事故：页面隐藏但 API 仍可调用、产品
旅程只做半条、Site A 误用 Site B 配置、未认证 Provider 被开放、Core/Advanced 的上线标准互相污染。

### 1.2 Solution Summary

建立版本化 `LaunchProductProfile`、`SurfaceInventoryRevision`、`CanonicalJourneyCatalog`、
`CapabilityQualificationAttestation`与`ReleaseCertificationInstance`产品合同。SiteRelease只能引用已发布Profile；
compile时展开所有Surface、Journey、
route、API、Admin command、Model/Agent/Capability assignment 和 evidence。未知、缺 owner、缺恢复、缺证据、
证据过期或只隐藏 UI 的条目全部 fail closed。

Product/Surface 定义统一来自 Platform Product Catalog 的 immutable `ProductSurfaceCatalogRevision`；Site 模块只拥有某个
Site 的 Profile/Inventory/Release 选择。Web 的物理裁剪由 ADR-016 的 WebBuildIntent → CompiledWebManifest → real artifact
链完成，不能由 Product Profile 直接携带代码路径或 package。

### 1.3 Target Users

- Site Product Owner：决定一个独立产品站点向用户承诺什么。
- Release/QA Owner：知道本次必须验证哪些旅程和哪些禁用面。
- Domain PM/Engineer：知道自己的 PRD/Spec 被哪些 Profile 消费。
- Support/SRE/Security：知道启用能力的 Case、SLA、runbook、alert 和 kill switch。
- 最终用户：只能看到真正可完成、可恢复、可支持的产品入口。

### 1.4 User Stories

| ID | User story | Priority |
|---|---|---|
| US-PROFILE-01 | 作为 Site Product Owner，我能组合已批准 Surface 并立即看到完整用户承诺和依赖 | P0 |
| US-PROFILE-02 | 作为 Release Owner，我能证明启用和禁用的每个入口均与 inventory 一致 | P0 |
| US-PROFILE-03 | 作为 QA，我能从 Profile 自动得到应跑 Journey 和负向测试，而不是手工维护清单 | P0 |
| US-PROFILE-04 | 作为 Support/SRE，我能从 enabled Surface 找到 Case、SLA、runbook、dashboard 和 kill switch | P0 |
| US-PROFILE-05 | 作为终端用户，我不会进入无法完成、无法恢复或无人支持的功能 | P0 |
| US-PROFILE-06 | 作为增长团队，我能创建独立 Music/Image/Chat Site Profile 而不修改共享后端业务代码 | P1 |

## 2. Goals、Metrics 与 Non-Goals

### 2.1 Goals

1. 一个 SiteRelease 的产品承诺可机器编译、审查、测试和回滚。
2. 每个 enabled Surface 都有完整 Journey/State/Recovery/Metric/Support/Operations 证据。
3. 每个 disabled Surface 在 artifact、release/bootstrap、BFF/API、owner/effect authorization、new-dispatch credential
   五层关闭，并以负向测试证明；共享 worker 不因单 Site 关闭而停机。
4. Core、if-enabled、advanced 和 transformation-final 的认证范围互不混淆。
5. 新 Site 通过独立 Profile 组合后端能力，不在共享代码添加 Site 特判。

### 2.2 Success Metrics

| Metric | Baseline | Target | Evidence |
|---|---:|---:|---|
| Enabled inventory entry 无 Journey/owner/evidence | 未统一 | 0 | compile report |
| Disabled Surface 可由 route/API/Admin/assignment 任一旁路访问 | 未统一 | 0 | negative E2E |
| Profile 引用不可解析或过期 revision | 未统一 | 0 | schema/cross-domain gate |
| Release 后发现“能进入但不能完成”的 P0 旅程 | 未统一 | 0 | RC UAT + incident taxonomy |
| Profile → Journey → PRD → Spec → Test → Evidence 追踪覆盖 | 未统一 | 100% | traceability report |
| Site-specific branch in shared backend/package | 当前存在风险 | 0 新增 | architecture gate |

### 2.3 Non-Goals

- 不在 Profile 中保存可编辑品牌、SEO、法律文案；这些属于 Site Web project/LegalRevision。
- 不在 Profile 中复制 Product/Plan/Model/Agent/Capability 定义；只引用已发布 revision。
- 不用 Profile 替代 Entitlement、Risk、Admission 或实时 kill switch。
- 不在本 PRD 决定价格、模型部署、Merchant、具体首发域名和营销文案。
- 不允许 Profile 动态把一个部署从 Site A 切成 Site B。

## 3. Product Objects

### 3.0 ProductSurfaceCatalogRevision

Platform Product Catalog 发布完整、不可变的目录 revision。每个 SurfaceDefinition 至少包含：

```text
surfaceRef / surfaceRevision / productRef
kind / dependencySurfaceRefs
requiredJourneyRevisionRefs
publicOperationFamilyRefs / adminCommandFamilyRefs
requiredModelRoleRefs / capabilityRequirementRefs
retirementPolicyRef / supportRequirementRef
```

这些是业务 requirement，不包含 pathname、React package、BFF handler、template、npm spec 或其他 Web 物理映射；后者只由
WebCompositionRegistryRevision 拥有。Surface definition 发布后不可变；目录 retire 只阻止新 Profile 引用。

### 3.1 LaunchProductProfile

```text
profileId
revision
name
targetSiteKind
status = draft | validating | ready | published | retired
productSurfaceCatalogRevisionRef
surfaceInventoryRevisionRef
compiledJourneyClosureDigest
assortment/model/agent/capability policy refs
authMethodPolicyRevisionRef
salesPolicyRevisionRef
contentPolicyProfileRef
localeAccessibilityBaselineRef
metricTargetRevisionRef
supportTierRevisionRef
operatorCommandMatrixRevisionRef
certificationPolicyRef
createdBy/reviewedBy/publishedAt
```

规则：

- 发布后不可变；变更创建 revision。
- `retired` 只阻止新 SiteRelease 引用，不改写已启动 Run、MediaOperation、domain workflow 或交易。
- Profile 不能直接引用 secret、Provider credential、用户或 BillingAccount。
- Site 可以引用同一 Profile revision，但其 SiteRelease 仍绑定独立 app、domain、assortment 和 assignments。
- `compiledJourneyClosureDigest` 由 Product Catalog compiler 对 core-always journeys 与所有 enabled Surface 的
  `requiredJourneyRevisionRefs` 求确定性依赖闭包后产生；Product Owner 不能手工增加、删除或覆盖 Journey refs。

Ownership 固定为：Platform Product Catalog 拥有 Product/Surface definition 与 CanonicalJourney catalog revision；
Platform `site` 模块拥有 Profile/SurfaceInventory revision、publish lifecycle 和 SiteRelease binding；Admin 只是 façade。
Root 只拥有 Journey/State/Recovery/Metric 的 schema、canonicalization 与 compatibility gate，不拥有业务 IDs 或
published catalog。Certification/Evidence 由 Release pipeline 产生，Site 模块只引用 signed result，不伪造测试事实。

### 3.2 Surface Inventory Entry

```text
surfaceRef / surfaceRevision
catalogRevisionRef
disposition = enabled | disabled
siteModelAgentCapabilityAssignmentRefs
sitePolicy/assortment/entitlementRequirementRefs
qualificationScopeRefs
testReportRefs / runbookRefs / dashboardAlertRefs
supportCaseKindRefs / contentPolicyRefs
capabilityQualificationAttestationRefs
acceptedRiskRefs with owner/expiry
```

`capabilityQualificationAttestationRefs`必须由accountable owners签名，在具体Release之前存在并绑定PRD/spec/contract/
test/runbook revision与适用范围；它不能是自由布尔值，也不能引用尚未生成的Release certificate。`enabled`条目缺任一
mandatory ref时compile失败；`disabled`条目必须提供五层关闭
证据，不能只省略 enabled entry。

`SurfaceInventoryRevision` 必须是所引用 `ProductSurfaceCatalogRevision` 的 exact、互斥、完整分区：catalog 中每个
Surface 必须且只能出现一次，状态只能是 `enabled|disabled`；unknown、duplicate、missing 都使 publish/compile 失败。
Product Owner 只选择 enabled 集合，compiler 从 catalog 全集确定性推导 disabled 集合。新增 Surface 必须产生新的 catalog
revision，旧 Profile 不会在未评审时自动获得或遗漏它。

五层关闭证据由 compiler、owner negative inventory 和 release certification 根据完整分区生成；运营员不能上传一个
自由布尔值把 disabled 宣称为已关闭。

Profile command family 固定为 `CreateProfileDraft`、`ValidateProfileCandidate`、`PublishProfileRevision`、
`RetireProfileRevision` 和 `BindProfileToSiteReleaseCandidate`；没有直接 `ActivateProfile`，上线只通过
SiteRelease ActivationAttempt。所有 mutation 使用 expectedVersion、idempotency key、reason 和审计。

### 3.3 CanonicalJourney

```text
journeyId / revision
scopeClass = core-always | if-enabled | advanced-cut | transformation-final
actor / entry / preconditions
happyPath / alternatePaths / failurePaths
terminalOutcomes
userVisibleStateRefs / recoveryActionRefs
supportCaseKindRefs / metricRefs
requiredSurfaceRefs / childPrdRef
acceptanceScenarioRefs
```

### 3.4 Qualification and ReleaseCertificationInstance

Profile candidate compile只消费有效`CapabilityQualificationAttestation`；compile/build/preview完成后才生成
`ReleaseCertificationInstance`。两层digest严格单向，禁止placeholder、自引用或复用其他Site/candidate证据。

```text
certificationId
profileId/revision
siteReleaseCandidateRef
productSurfaceCatalogDigest
surfaceInventoryRevisionRef/digest
source/contract/lock/image/config digests
appliedGateRefs / skippedGateRefs with scope reason
evidenceBundleRef
generatedAt/validUntil
producerIdentity/signature
producerTrustPolicyRevisionRef/keyVersion/signatureAudience
supersedesCertificationId?
decision = passed | failed | expired | revoked
```

Core certification 可以允许对应 SiteRelease 上线，但不关闭 Transformation Program；高级能力用 delta
Certification，最终以 transformation-final instance 收口。

Release activation必须持有匹配全部compiled inventory、source、contract、lock、image与config digest的有效instance。
Qualification只证明能力在声明范围内合格，不单独授权任何SiteRelease上线。

## 4. Reference Profile：`core-redeem-chat@1`

### 4.1 Enabled Surface Inventory

| Surface | Required Journey families | Authority / minimum dependency |
|---|---|---|
| auth-password | ID-01…03、ID-06 | Identity password/verification/session adapters、Notification、Risk |
| auth-totp-recovery | ID-03、ID-05…06 | Identity authenticator/recovery/session adapters、Notification、Risk、Support |
| personal-workspace | WS-01、WS-04 | Workspace/Project/ExecutionSpace mapping |
| account | AC-01、CR-01 | Subscription/Entitlement/Credit/Usage projections |
| redeem | RD-01…05 | Redeem/Fulfillment/Grant/Support |
| general-chat | CH-01…08 | Session、Platform Admission、GA、Model Gateway、Capability Runtime |
| attachment | AS-01…02 | Asset/Object Storage/scan/quarantine/Risk |
| minimal-library | LIB-01/02 without public share | Project/Artifact/Blob/Export |
| notification-center | NOT-01 | Notification preferences/request/delivery |
| support-center | SUP-01…03 | SupportCase + domain refs |
| core-admin | ADM-01…03、SF-01…03 | Admin façade、Site Fleet、Commerce/Runtime/Governance commands |
| data-rights | ID-07 | Export/Deletion/Retention/LegalHold participants |

### 4.2 Disabled Surface Inventory

| Surface | Disabled proof |
|---|---|
| auth-magic-link-login | initiation/callback/link route absent or denied、bootstrap method absent、provider/config/secret unused、Admin cannot enable |
| auth-oauth-oidc | each provider/client initiation/callback/link/unlink route denied、provider assignment absent、secret unused、Admin cannot enable |
| auth-passkey-webauthn | registration/challenge/verification route denied、bootstrap method absent、RP configuration unused、Admin cannot enable |
| auth-enterprise-saml-oidc | discovery/initiation/callback/link route denied、tenant/provider assignment absent、secret/certificate unused、Admin cannot enable |
| checkout/new payment acquisition | route absent、bootstrap capability absent、mutation returns channel disabled、Admin cannot create new Provider IO |
| Image/Music/Video Studio | no route/assignment/operation family authorization/Admin publish |
| public Share/SEO remix | no public route/share command/crawler artifact |
| Workspace collaboration | invite/membership mutation disabled；personal workspace remains |
| Target/Device/Developer/CLI | no device registration/target assignment/client OAuth grants |
| Routine/Connector/Plugin user surfaces | no create/install/connect mutation；internal required capability remains governed |
| Handoff/AgentTeam/Wide Research/Application Runtime | no assignment/Manifest edge/route/Admin publish |

本表只是 Reference Profile 的产品摘要，不是关闭证据。最终 disabled 集合必须由 exact Catalog/SurfaceInventory 的完整分区
推导，并由 Web compiler、各 owner negative inventory 与 ReleaseCertification 共同产生五层机器证据；自然语言行不能
单独授权发布。

### 4.3 User Promise

用户可以注册、兑换 Code、看到权益/积分、完成可靠 Chat、上传安全附件、恢复断线、管理对话和最小作品、
获得通知与 Support、执行数据权利。用户不会看到支付、专业 Studio、公开分享或高级 Agent 入口。

## 5. Functional Requirements

### 5.1 Profile Authoring

- FR-001：Product Owner 从已发布 Surface/PRD/assignment revision 组合 draft，不允许自由 JSON。
- FR-002：编辑器显示依赖图、新增/删除 Journey、用户承诺差异、成本/风险/Support 影响。
- FR-003：任何 Surface enable 自动引入 mandatory Journey，不允许手工取消 core dependency。
- FR-004：disable 提示历史数据、active Run/MediaOperation/domain workflow、Artifact 可见性与 deep-link 兼容影响。
- FR-005：production publish 使用 expectedVersion、reason、step-up 和 maker-checker。

### 5.2 Compile and Validate

- FR-010：schema、引用、scope、dependency、role completeness、Site compatibility 全量校验。
- FR-011：Product Catalog 枚举业务 operation/assignment requirement，Web registry/compiler 枚举 route/bootstrap/BFF；
  certification 比对两边闭包，发现未登记入口、缺物理实现或多余实现即失败。
- FR-012：每个 enabled Journey 必须解析 Product PRD、architecture Spec、acceptance scenarios 和有效 evidence。
- FR-013：accepted risk 必须绑定 profile/surface/release、owner、expiry 和 compensating control；过期失败。
- FR-014：ContentPolicy、locale/a11y、SupportTier、metric target 缺失失败。
- FR-015：从未启用 Payment 的 redeem-only Site 不依赖 Provider secret/account，新 Checkout/PaymentAttempt
  mutation fail closed。曾产生 Payment Fact 的 Site 即使关闭 acquisition，也必须保留历史 Refund/Dispute/
  reconciliation 与法定通知能力，并使用原 ProviderAccount；关闭销售入口不能逃避既有义务。
- FR-016：跨 Site、重复收费/Grant、账务守恒、secret、Critical/High exploit、数据丢失和 WCAG Core blocker
  不允许 accepted-risk waiver；只能修复或关闭 Surface。
- FR-017：Profile 与 SiteRelease 的 LegalRevision、SalesPolicy、ContentPolicy、locale 和 age/region eligibility
  必须兼容；Profile 本身不复制法务内容。
- FR-018：认证不是一个可整体放行的黑盒 Surface。每个 method/provider/client 必须有独立 inventory entry，
  覆盖 bootstrap discovery、initiation、callback、link/unlink、Admin/config、secret dependency 与负向证据。
  未具备完整 Journey/FR/AC/运营闭环的方法状态只能是 `not_enableable`，不能借 `auth` 已启用而上线。
- FR-019：Certification producer 必须来自版本化 trusted-producer registry；签名绑定 environment、Profile、
  SiteRelease、inventory/evidence digest、algorithm/key version、audience、validity 与 revocation status。跨环境、
  跨 Release、已撤销 key 或过期 attestation 的重放必须失败。

### 5.3 Preview and Certification

- FR-020：preview 使用 candidate Site deployment 与非生产数据/secret，不能共享 production Cookie/account。
- FR-021：QA 从 inventory 自动生成 applied journey suite 和 disabled negative suite。
- FR-022：每个 test evidence 记录 source/image/contract/config digest、producer、time、validity。
- FR-023：Security/SRE/Product/Support 只签署自己 accountable domain，任一 blocker 可否决。
- FR-024：Certification 过期、evidence revoked 或 kill switch 触发时阻止新 promote。

### 5.4 Activate, Rollback and Evolve

- FR-030：Profile 只随 SiteRelease ActivationAttempt 切换，不直接修改 active product。
- FR-031：同一 Site 的 AuthSession 可以跨兼容 Release 继续有效；旧 tab 的静态资源和请求仍绑定其可信
  deployment/release context，并在 compatibility/drain window 内使用原 Release。过窗要求刷新，不静默换
  Journey semantics。浏览器提交的 release id 永远不是授权依据。
- FR-032：已启动 Run/MediaOperation/domain workflow/transaction 使用冻结 Manifest/Operation/Quote，不因 Profile rollback 重跑。
- FR-033：rollback 前重新校验当前 kill switch、secret revocation、schema/contract 和安全 policy。
- FR-034：新增 Surface 使用 delta Certification；删除 Surface 明确历史数据/deep link/notification/support 行为。

## 6. User Experience Requirements

### 6.1 Product Owner

Profile editor 采用“Surface + Journey + dependency/evidence”信息架构，不显示数据库表。必须有：current/candidate
diff、用户承诺 diff、enabled/disabled 状态、阻断原因、owner、证据有效期、preview deep link、approval history。

### 6.2 Site Operator

Site Fleet 显示 Site lifecycle、active/candidate Profile、active Release、domain/certificate、deployment slots、
certification validity、drift 和 rollback target。Profile publish 与 Release activate 是两个命令，不能混成一个
“保存并上线”。

### 6.3 End User

- 导航和空状态只能承诺 enabled Surface。
- 历史 deep link 指向 disabled Surface 时由 base shell 的通用、静态 `RetiredSurface/Gone` resolver 显示稳定说明与允许的
  Library/Data Rights/Support 动作；它不重新打包已禁用产品的 route、facade 或代码。
- Profile 切换不跨 Site 合并账户、套餐、积分或历史。
- 用户不看到 internal Wave、Profile ID 或 Provider deployment；Support 可用安全 correlation refs 定位。

## 7. Edge Cases and Recovery

| Scenario | Expected behavior |
|---|---|
| Profile 引用不存在/retired revision | validating failed；active Release 不受影响 |
| route 存在但 inventory 未登记 | compile hard fail |
| UI hidden 但 API command 可调用 | negative suite fail；No-Go |
| evidence 在 approval 后、activate 前过期 | ActivationAttempt recheck fail |
| candidate 认证后发生 critical kill switch | 阻止 activate；已 active 受实时 deny 覆盖 |
| enable Studio 但没有认证 generation adapter | assignment/compile fail |
| disable Studio 时有 running MediaOperation | 禁止该 Site/新 Release 的 assignment、credential 与 dispatch；已接受的 operation 按冻结旧 Release/OperationSpec 完成或 drain；共享 worker 继续服务其他 Site/旧 operation |
| disable Chat 时存在旧 deep link | 按 retention policy read/export 或受控 gone page，不开放新 Run |
| Profile rollback 与新交易并发 | active pointer/Release snapshot 决定；不改写已提交事实 |
| Site A Profile 被 Site B deployment 声明 | DeploymentBinding/SiteContext 校验拒绝 |
| password-only Profile 调用 OAuth/Magic Link/Passkey/SAML | initiation、callback、link/unlink 和 Admin/config 全部拒绝；不读取 provider secret，不创建 AuthTransaction/AuthSession |
| Certification event 丢失 | 以 immutable instance/query 恢复，不重跑 Provider effect |
| accepted risk 过期 | 下一次 promote 阻断；active Release 告警并按 risk policy 处置 |
| Product owner 删除 mandatory Journey | schema/dependency validation 拒绝 |
| 曾收款 Site 切到 redeem-only | 阻止新 Checkout，但保留历史 Payment/Refund/Dispute/Admin/Support 责任链 |

## 8. Acceptance Criteria

### AC-001 — Enabled Surface completeness

```gherkin
Given core-redeem-chat candidate enables general-chat
When the profile is compiled
Then Chat routes, commands, model/capability assignments and all CH journey revisions are present
And each journey resolves a PRD, architecture spec, test evidence, runbook and owner
And missing or expired evidence fails compilation
```

### AC-002 — Disabled Payment fail closed

```gherkin
Given a new Site has always used redeem_only and has no Payment Fact
When a user, stale client or operator invokes checkout or new-payment mutation
Then the request returns ACQUISITION_CHANNEL_DISABLED without creating Order or Provider IO
And no Payment provider secret/account is required for startup
```

若 Site 历史上存在 Payment Fact，测试必须额外证明新 Checkout 关闭但 Refund/Dispute/reconciliation 对历史事实
仍可通过原 ProviderAccount 完成。

### AC-003 — Unknown entry detection

```gherkin
Given a code change adds a route or mutation not present in the inventory
When release inventory verification runs
Then the candidate fails with the exact unregistered entry and owner
```

### AC-004 — Profile-scoped certification

```gherkin
Given Core does not enable Payment, Studio or Advanced Agent surfaces
When CertificationInstance is generated
Then core-always gates are applied
And disabled negative gates are applied
And advanced/payment functional gates are skipped only with explicit scope reasons
And the result does not mark the Transformation Program complete
```

### AC-005 — Safe evolution

```gherkin
Given a new Profile revision disables a previously enabled Studio
And a MediaOperation from the old Release is running
When the new Release activates
Then the MediaOperation completes against its frozen OperationSpec
And historical Artifact access follows the published retirement policy
And new Studio route and submission are denied
```

### AC-006 — Multi-Site isolation

```gherkin
Given Site A and Site B use different Profiles and Web deployments
When their cookies, hosts, binding credentials or release ids are crossed
Then all protected requests fail closed
And neither Site reveals the other Site's account, entitlement, data or enabled surfaces
```

这里的 crossed release id 指跨 Site、伪造或与可信 DeploymentBinding 不一致；同一 Site 在发布兼容窗口内的
旧 AuthSession 仍可使用，但只能由其原 workload/deployment binding 建立 Release context，不能由 cookie/query/header
自由指定。

### AC-007 — Disabled auth method fail closed

```gherkin
Given a Profile enables password and TOTP but marks OAuth, Magic Link, Passkey and enterprise SSO disabled
When a browser, stale client or operator invokes any disabled method initiation, callback, link, unlink or configuration command
Then the request is denied before provider or secret access
And no AuthTransaction, User, Credential, FederatedIdentity or AuthSession is created or changed
And certification contains one negative result for every registered method/provider/client entry
```

### AC-008 — Certification signature replay

```gherkin
Given a valid certification signature belongs to another environment, SiteRelease, evidence digest, audience or revoked key
When it is attached to a production candidate
Then trust-policy validation rejects it
And the candidate cannot be promoted
```

## 9. Analytics and Product Operations

Required events：profile draft/validation/publish、inventory compile result、preview start/result、certification decision、
activation/rollback、disabled route attempt、evidence expiry、accepted risk expiry、user deep-link gone state。

事件不得包含 secret、prompt、Code 原文或跨 Site identity；Profile/Surface/Revision 可作低基数维度。Analytics
失败不能阻断交易/执行，但 Profile compile/certification evidence 写入失败必须阻断发布。

## 10. Dependencies and Risks

| Dependency/Risk | Mitigation |
|---|---|
| SiteRelease/ActivationAttempt 尚未实现 | Wave 1 同时交付，Profile 不自建 active pointer |
| PRD/Spec/Evidence 尚未齐全 | compile fail closed；不使用 waiver 绕过 missing P0 journey |
| Profile 过度配置化 | Surface schema/typed revision，禁止自由 JSON 和 Site 特判 |
| Reference Profile 被当成唯一产品 | 明确其他 Site 使用独立 Profile；共享后端但独立 Web/Release |
| 证据过期导致频繁阻塞 | 定义 validity、nightly refresh 和 owner alert；不永久复用旧证据 |
| 关闭 Surface 伤害历史用户 | 每个 disable change 强制 retirement/deep-link/data policy |
| Profile 与实时安全冲突 | kill switch/restriction 可覆盖旧 Release，普通配置不可改运行中 snapshot |

## 11. Milestones and Exit

1. Wave 0：冻结 Profile/Journey/inventory/evidence contract source、owner 与 traceability gate。
2. Wave 1：实现 Profile/SiteRelease compile、Reference Profile draft/preview 和 disabled negative inventory。
3. 各业务 Wave：发布 Surface/Journey/PRD/Spec/test revisions，更新 Reference Profile candidate。
4. Wave 7：完成 Site Fleet/Profile editor、OperatorCommandMatrix 和 Support/Operations UAT。
5. Wave 8/9：生成 `core-redeem-chat` CertificationInstance；高级能力随后用 delta instance。

PRD-00 产品验收只有在 Product、Architecture、QA、Security、SRE、Support 对各自门签署后完成。用户已授权
`core-redeem-chat` 与 ADR-016 基础架构进入实现；该授权允许编写 contracts、Product Catalog、SurfaceInventory、Web
composition/build control 和 SiteRelease 集成，不等于任何 Surface 获得 activation 或 launch certification。Payment
provider 与 advanced surfaces 继续 feature-off，Agent 核心语义变更仍需单独对齐。
