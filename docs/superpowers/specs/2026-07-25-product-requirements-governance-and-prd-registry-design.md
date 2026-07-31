---
artifact: product-requirements-governance-design
version: "1.1"
created: 2026-07-25
status: internal-review-active
parent: 2026-07-25-platform-web-session-target-architecture-design.md
scope: launch-profile-journey-state-recovery-metric-prd-traceability
implementationAuthorized: false
---

# Kokoro 产品需求治理、Launch Profile 与 PRD Registry

## 0. 文档定位

本文把 Umbrella 架构中的能力转成可实现、可验收的产品治理契约。它不新增后端服务，也不替代各领域
child PRD/Spec。它解决七个问题：首发到底开放什么、用户到底完成哪些旅程、每个状态看到什么、失败后
下一步是什么、指标由谁负责、各 Wave 必须先写哪份 PRD、旧 requirements 如何迁移。

产品流程固定为：

```text
LaunchProductProfile
→ CanonicalJourneyCatalog
→ child Product PRD + product red-team
→ architecture child Spec + architecture/reliability/security review
→ implementation plan
→ implementation/evidence/cleanup
→ profile-scoped CertificationInstance
```

任何实现计划若没有 Journey ID、产品状态和恢复动作映射，review 失败。

## 1. 七个产品治理真源

### 1.1 LaunchProductProfile

```text
profileId / revision / targetSiteKind
enabledSurfaceInventory
disabledSurfaceInventory
requiredJourneyIds
model/agent/capability/assortment refs
salesPolicyRevisionRef
contentPolicyProfileRef
locale/browser/accessibility baseline
metricTargetRevisionRef
supportAndOperationsTier
certificationPolicyRef
```

Profile 是产品承诺，不是 Feature Flag 集合。启用 Surface 必须绑定完整旅程、API/Admin command、revision、
evidence 和 owner；禁用 Surface 必须在 route、bootstrap、API authorization、Admin 四层 fail closed。

### 1.2 CanonicalJourneyCatalog

每条 Journey 至少包含：

```text
journeyId / revision / scopeClass / actor / entry / preconditions
happyPath / alternatePaths / failurePaths / terminalOutcomes
userVisibleStateRefs / recoveryActionRefs / supportCaseKinds
metricRefs / requiredSurfaceRefs / childPrdRef / acceptanceScenarioRefs
```

Journey 发布后不可原地改语义；变化创建 revision。SiteRelease/Certification 绑定具体 revision。

### 1.3 UserVisibleStateCatalog

内部领域状态不得原样倾倒给用户。产品状态记录：stable state key、适用 Surface、用户解释、数据新鲜度、
是否产生费用、可用 CTA、重试安全、预计等待、Support deep link 和 telemetry event。

### 1.4 RecoveryActionCatalog

每个 error/partial/unknown 状态必须映射一个动作：`retry_same_identity`、`resume`、`wait_and_refresh`、
`provide_input`、`change_parameters`、`reauthenticate`、`request_support`、`appeal`、`no_user_action`。禁止用
“请稍后重试”覆盖 unknown Provider outcome、已提交支付或已 committed Hold。

### 1.5 ProductMetricCatalog

Metric 定义 numerator、denominator、exclusions、window、dimensions、event source、owner、target、guardrail、
alert/action。所有指标至少按 Site、Profile、SurfaceRevision 切分；不以全局平均掩盖单 Site 失败。

### 1.6 OperatorCommandMatrix

每个 Admin command 登记：role、Site/Global scope、read/write/risk class、reason、step-up、maker-checker、
expectedVersion、idempotency、PII masking、queue owner、SLA、audit event、user notification 和 recovery runbook。

### 1.7 ContentPolicyProfile

冻结文本、Image、Music/Voice、Video/Likeness、Code/Execution、Upload、Public Share 的输入权利、允许/拒绝、
年龄/地域、NSFW、版权、声音克隆同意、肖像/深伪、水印/披露、moderation、appeal 和 retention policy。
Site policy 只能在 Platform 最低安全线之上收紧，不能放宽法律/安全基线。

## 2. Reference Launch Profile：`core-redeem-chat`

这是工程上第一个必须可认证的具体 Profile，不代表最终商业 Site 必须使用 General Chat。Music/Image Site
可创建自己的 Profile，但必须达到相同 Identity、Account、Support、安全、恢复和运维标准。

### 2.1 Enabled

```text
Site-bound email/password Identity、TOTP/Recovery、Device Session
Personal Workspace + BillingAccount + Project
Account/Plan/Entitlement/Credit/Usage history
Redeem input/preview/review/receipt/reversal-support
General Chat + typed parts + branch + HITL + reconnect
safe text/file attachment intake
minimal Artifact/Library for Chat outputs and downloads
Notification for security/redeem/run/case/data-rights events
User Support Center
Core Admin: Site Fleet/Redeem/Credit/Run/Case/Governance/System
Export/Deletion/Retention/LegalHold
```

### 2.2 Disabled

```text
Checkout/Payment/Refund/Dispute UI and mutation
Magic Link login、OAuth/OIDC、Passkey/WebAuthn、Enterprise SSO
Image/Music/Video Studio
public Share/SEO remix
multi-member Workspace collaboration
local/cloud ExecutionTarget selection
Developer Workspace/CLI/Desktop/IDE
Routine/Connector/Plugin user surfaces
true Agent Handoff/AgentTeam/Wide Research/Application Runtime
```

禁用不删除底层 contract；它要求所有入口负向证据。Profile 后续开启任一能力时，必须绑定对应 child PRD、
provider certification 和 delta CertificationInstance。

### 2.3 Proposed launch targets

这些是产品复审基线，Site 可以收紧，不能在 RC 临时放宽：

| Metric | Target |
|---|---:|
| 合法、符合资格 Code 的 Redemption 成功率 | ≥ 99.9%，排除明确用户取消和 policy deny |
| Redemption 响应丢失后恢复同一 receipt | 100% |
| 重复 Redemption/Fulfillment/Grant | 0 |
| 跨 Site 身份、数据、Cookie、品牌泄漏 | 0 |
| 注册/兑换到首个成功 Chat 的 TTFV | p50 ≤ 90s，p95 ≤ 5m |
| 已接受 Chat Run 形成 completed/partial/可解释 terminal | ≥ 99%，排除用户 cancel |
| active Run 刷新/断网后恢复 | ≥ 99.9% |
| committed Hold 无 owner、重复 capture 或负余额 | 0 |
| enabled Surface 任一适用 WCAG 2.2 A/AA failure | 0；完整页面、状态、变体与 complete process 均为 Release blocker |
| Support 首次响应/解决 | 生产支持时段 p90 ≤ 4h / p90 ≤ 2 business days |
| Critical security、账务或数据 blocker | 0 |

Provider 外部故障单独计量，但用户仍必须获得确定状态、恢复动作和 Support 路径。
Reference Profile 使用 `core-standard` SupportTierRevision：安全、跨站、重复扣费/Grant、数据丢失类 P0
24×7 page，15 分钟内 acknowledgement；普通 Case 使用 SiteRelease 发布的 5×9 business calendar，上表 4h/2
business days 只在该 calendar 内计时。用户提交前必须看到适用 SLA，不能在出错后才解释“非工作时间”。

### 2.4 Vertical Site Profile review fixtures

以下三个 fixture 用于证明“一 Site 一独立产品”不是同一 Chat App 的换色。它们是产品评审基线，不是自动启用的
production assignment；实际 SiteRelease 仍绑定不可变 revision、Qualification 与 ReleaseCertification。

| Profile fixture | Enabled product surfaces | Disabled by default | First-value metric | Required governed bindings |
|---|---|---|---|---|
| `image-studio@1` | Site-bound Identity、Account/Redeem/Credit、safe attachment、Image Studio、minimal Library、Notification、Support、Core Admin、Data Rights | Payment、General Chat、Music/Video、Public Share、Advanced Agent | eligible user 从兑换/登录到首张可下载 allowed image 的 p50/p95 | Image Offering、generation+editing/upscale model roles、image tools、rights/NSFW policy、Artifact/Export |
| `music-studio@1` | Site-bound Identity、Account/Redeem/Credit、safe attachment、Music Studio、minimal Library、Notification、Support、Core Admin、Data Rights | Payment、General Chat、Image/Video、Public Share、Advanced Agent | eligible user 到首个可播放且可导出的 allowed track 的 p50/p95 | Music Offering、main orchestrator+music generation roles、lyrics/audio capabilities、voice/music rights、Artifact/Export |
| `video-studio@1` | Site-bound Identity、Account/Redeem/Credit、safe attachment、Video Studio、minimal Library、Notification、Support、Core Admin、Data Rights | Payment、General Chat、Image/Music standalone、Public Share、Advanced Agent | eligible user 到首个可预览 allowed shot，以及完整 export 的 p50/p95 | Video Offering、main orchestrator+video/image/audio roles、storyboard/render capabilities、likeness/voice policy、Artifact/Export |

共同规则：

- 每个 fixture 编译自己的 enabled/disabled inventory、Offering、ModelBundle、Capability、ContentPolicy、metric 与
  Support tier；不能继承另一个 Site 的 mutable 配置。
- General Chat 是否开放是显式 Surface 决策；即使不开放，Studio 的 hidden main/orchestrator model role 仍由
  ModelBundle 提供，不能把浏览器表单直接绑 Provider。
- disabled Surface 在 route、bootstrap、API authorization、Admin 四层 fail closed；共享后端存在能力不等于该 Site
  对用户承诺能力。
- 三个 fixture 均使用独立 Web Project、lockfile、CI、artifact、deployment 和 rollback authority；共享的是已发布
  Web capability packages 与同一套 Backend/Session/Job/GA/Gateway。

## 3. Mandatory Product PRD Registry

PRD 可以在对应 cut 之前创建为 `internal-review-active` 草案，以便跨域红队；但不得提前批准、写成实现事实或
作为 implementation authorization。本 Registry 冻结名称、owner 和范围，禁止用一份万能 PRD 合并专业产品。

| ID / canonical filename | Wave | Scope | Mandatory journeys |
|---|---|---|---|
| PRD-00 [`2026-07-25-prd-00-launch-profile-and-journey-contract.md`](2026-07-25-prd-00-launch-profile-and-journey-contract.md) | cross-wave | core | Profile、inventory、catalog、metrics、enable/disable evidence |
| PRD-01 [`2026-07-25-prd-01-site-identity-and-account-security.md`](2026-07-25-prd-01-site-identity-and-account-security.md) | 1 | core | register/verify/login/logout/recovery/OAuth/MFA/device/session |
| PRD-02 [`2026-07-25-prd-02-workspace-membership-and-project.md`](2026-07-25-prd-02-workspace-membership-and-project.md) | 1 | core+if-enabled | personal bootstrap、invite、role、last owner、Project lifecycle |
| PRD-03 [`2026-07-25-prd-03-account-plan-redeem-and-credit.md`](2026-07-25-prd-03-account-plan-redeem-and-credit.md) | 2A | core | plan/term/credit、redeem preview/result/review/reversal/support |
| PRD-04 [`2026-07-25-prd-04-checkout-subscription-and-billing.md`](2026-07-25-prd-04-checkout-subscription-and-billing.md) | 2B | if-enabled | quote/checkout/redirect/renew/change/cancel/refund/dispute |
| PRD-05 [`2026-07-25-prd-05-chat-conversation-run-and-interaction.md`](2026-07-25-prd-05-chat-conversation-run-and-interaction.md) | 3/5A | core profile | onboarding/manage/composer/stream/control/branch/HITL/model/Job |
| PRD-06 [`2026-07-25-prd-06-asset-intake-and-attachment-safety.md`](2026-07-25-prd-06-asset-intake-and-attachment-safety.md) | 3/4 | core safe attachment + if-enabled extended import | upload/resume/scan/quarantine/quota/delete/appeal |
| PRD-07 [`2026-07-25-prd-07-studio-common-job-and-cost-ux.md`](2026-07-25-prd-07-studio-common-job-and-cost-ux.md) | 4 | if-enabled | draft/autosave/quote/submit/queue/unknown/partial/export |
| PRD-08I [`2026-07-25-prd-08i-image-studio.md`](2026-07-25-prd-08i-image-studio.md) | 4 | if-enabled | generate/reference/mask/inpaint/outpaint/batch/upscale |
| PRD-08M [`2026-07-25-prd-08m-music-studio.md`](2026-07-25-prd-08m-music-studio.md) | 4 | if-enabled | lyrics/player/generate/extend/remix/stem/export |
| PRD-08V [`2026-07-25-prd-08v-video-studio.md`](2026-07-25-prd-08v-video-studio.md) | 4 | if-enabled | storyboard/assets/shot/long queue/partial/upscale/export |
| PRD-09 [`2026-07-25-prd-09-library-artifact-export-and-share.md`](2026-07-25-prd-09-library-artifact-export-and-share.md) | 4 | core minimal + if-enabled Share | lineage/search/trash/quota/rendition/share/revoke/moderation |
| PRD-10 [`2026-07-25-prd-10-admin-operating-console.md`](2026-07-25-prd-10-admin-operating-console.md) | 7 + annex per cut | core | auth/scope/queues/commands/approval/diagnosis/audit |
| PRD-11 [`2026-07-25-prd-11-support-recovery-and-appeals.md`](2026-07-25-prd-11-support-recovery-and-appeals.md) | 1 contract/7 | core | user center/intake/triage/SLA/evidence/escalation/compensation |
| PRD-12 [`2026-07-25-prd-12-site-lifecycle-and-fleet.md`](2026-07-25-prd-12-site-lifecycle-and-fleet.md) | 1/7 | core | provision/domain/certificate/preview/promote/rollback/suspend/decommission |
| PRD-13 [`2026-07-25-prd-13-growth-seo-experiment-and-attribution.md`](2026-07-25-prd-13-growth-seo-experiment-and-attribution.md) | 7 | if-enabled | acquisition/deep link/consent/stitch/exposure/guardrail/share SEO |
| PRD-14 [`2026-07-25-prd-14-localization-and-accessibility.md`](2026-07-25-prd-14-localization-and-accessibility.md) | cross-wave | core | locale/fallback/time/number/RTL/WCAG/browser/AT |
| PRD-15 [`2026-07-25-prd-15-notification-preferences-and-data-rights.md`](2026-07-25-prd-15-notification-preferences-and-data-rights.md) | 1/6C/7 | core | mandatory events/preferences/delivery/deep link/export/delete UX |
| PRD-16 [`2026-07-25-prd-16-trust-content-safety-and-media-rights.md`](2026-07-25-prd-16-trust-content-safety-and-media-rights.md) | 1/4/7 | core+if-enabled | input/generation/share/appeal/voice/likeness/copyright/NSFW |
| PRD-17 [`2026-07-25-prd-17-model-option-control-and-provider-operations.md`](2026-07-25-prd-17-model-option-control-and-provider-operations.md) | 5A | core dependency + if-enabled operator surface | model option/default/unavailable、evaluation/promotion/canary/rollback、provider certification |
| PRD-18 [`2026-07-25-prd-18-capability-catalog-connection-consent-runtime-ux.md`](2026-07-25-prd-18-capability-catalog-connection-consent-runtime-ux.md) | 5A/6C | core dependency + if-enabled catalog/connection | skill/MCP discovery、qualification、connection/consent/revoke、elicitation、runtime cost/unknown |
| PRD-19 [`2026-07-30-prd-19-product-memory-and-context-use.md`](2026-07-30-prd-19-product-memory-and-context-use.md) | M0-M4 | core explicit + if-enabled learned/past-chat context | remember/correct/forget、selection/explanation、past-chat、temporary、pause/reset/export/purge |
| PRD-A1 [`2026-07-25-prd-a1-agent-revision-and-handoff-product.md`](2026-07-25-prd-a1-agent-revision-and-handoff-product.md) | 5B | advanced | publish/select/handoff visibility/recovery；GA专项批准 |
| PRD-A2 [`2026-07-25-prd-a2-target-device-permission-and-interaction.md`](2026-07-25-prd-a2-target-device-permission-and-interaction.md) | 6A | advanced | onboard/pair/trust/select/takeover/approval/revoke |
| PRD-A3 [`2026-07-25-prd-a3-developer-workspace-context-and-multidevice.md`](2026-07-25-prd-a3-developer-workspace-context-and-multidevice.md) | 6B | advanced | repo/worktree/diff/test/checkpoint/rewind/PR/attach/fork |
| PRD-A4 [`2026-07-25-prd-a4-routine-connector-and-taskview.md`](2026-07-25-prd-a4-routine-connector-and-taskview.md) | 6C | advanced | builder/schedule/DST/misfire/OAuth/wait/notification/task timeline |
| PRD-A5 [`2026-07-25-prd-a5-agent-team-research-and-application-runtime.md`](2026-07-25-prd-a5-agent-team-research-and-application-runtime.md) | 6D | advanced | team plan/budget/nodes/partial/cancel/aggregate/deploy/rollback |
| PRD-A6 [`2026-07-25-prd-a6-client-access-plane-cli-desktop-and-ide.md`](2026-07-25-prd-a6-client-access-plane-cli-desktop-and-ide.md) | 6A-6C | advanced | install/update、OAuth/device flow、attach/fork/new run、offline、revocation、compatibility、Support |

每份 PRD 必须通过 `deliver-prd` 质量项，并由产品红队检查 Journey、state、recovery、metrics、scope 和运营闭环。

### 3.1 Accountable product roles

| PRD group | Accountable product role | Mandatory co-signers |
|---|---|---|
| PRD-00/12 | Platform Product Lead | Site Fleet、SRE、Security、Release |
| PRD-01/02 | Identity & Collaboration PM | Security、Privacy、Support、Web |
| PRD-03/04 | Commerce PM | Finance、Risk、Support、Legal、Web |
| PRD-05/06 | Chat Product Lead | Session/GA/Model owners、Trust、Web QA |
| PRD-07/08I/08M/08V/09 | Studio Product Lead + each vertical PM | Job/Artifact/Model、Trust/Legal、Design |
| PRD-10/11 | Operations & Support PM | Security、Finance、Risk、Data Governance |
| PRD-13 | Growth PM | Privacy、Site Fleet、Analytics |
| PRD-14 | Design Systems/A11y Lead | each Surface PM、Web QA |
| PRD-15/16 | Privacy/Trust Product Lead | Legal、Security、Support、Content Ops |
| PRD-17 | Model Product Lead | Model Platform、Gateway、GA owner、Usage Rating、Trust、Support、SRE |
| PRD-18 | Capability Product Lead | Capability Hub/Runtime、GA owner、Security、Trust、Support、SRE |
| PRD-19 | Personalization & Memory Product Lead | Privacy、Platform Memory、Session、GA、Web、Data Governance、Model Platform、Accessibility、Support、SRE |
| PRD-A1-A6 | Agent Product Lead | GA owner、Runtime/Security、Support、SRE |

每份实际 PRD frontmatter 还必须登记 named Engineering、QA、Support/Operations owner；可以使用唯一、可路由的
team responsibility ID，但不能使用“全体团队”或无 owner 角色。责任 ID 无 on-call/approval mapping 时不能批准。

## 4. Canonical Journey Families

本文冻结 canonical Journey IDs；`docs/reports/2026-07-25-kokoro-module-capability-coverage-audit.md` 负责把它们
映射到模块 owner/cut，child PRD 再展开 Given/When/Then、状态和恢复分支。PRD 不得少于：

| Family | Required journey IDs |
|---|---|
| Launch/Site | LP-01、SF-01 provision、SF-02 promote/rollback、SF-03 suspend/decommission |
| Identity | ID-01 register、02 login、03 recovery、04 OAuth、05 MFA、06 device/session、07 export/delete |
| Workspace | WS-01 personal bootstrap、02 invite、03 role/leave/transfer、04 Project lifecycle |
| Account/Redeem | AC-01、RD-01 input/preview、02 lost-response、03 receipt、04 review、05 reversal/replacement、CR-01 pending/reconcile |
| Payment | PAY-01 checkout、02 subscription lifecycle、03 refund/dispute |
| Chat | CH-01 onboarding、02 manage、03 composer、04 reconnect、05 stop/cancel/continue、06 branch、07 HITL、08 model option、09 media Job |
| Asset | AS-01 upload/scan、AS-02 quota/quarantine/recovery |
| Studio | ST-01 draft、02 quote/submit、03 queue/cancel/retry、04 unknown、05 partial/compare、06 lineage/export |
| Vertical Studio | IMG-01、MUS-01、VID-01 |
| Library/Share | LIB-01 browse/organize、02 quota/trash/GC、SHR-01 share/revoke/report |
| Admin/Support | ADM-01 auth/scope、02 high-risk command、03 recovery；SUP-01 user case、02 operator lifecycle、03 compensation/confirmation |
| Growth/UX/Safety | GR-01/02/03、UX-01 locale、UX-02 a11y、SAF-01 block/appeal、SAF-02 media rights、NOT-01 notification |
| Model/Capability | MOD-01 option/default、MOD-02 unavailable/reconfirmation、MOD-03 operator lifecycle；CAP-01 discover/assign、CAP-02 connect/consent、CAP-03 invoke/elicitation/revoke、CAP-04 operator lifecycle |
| Memory/Context | MEM-01 remember/inspect、MEM-02 correct/forget、MEM-03 proposal、MEM-04 selection/explanation、MEM-05 past-chat、MEM-06 pause/reset/temporary/data-rights、MEM-07 operator recovery |
| Advanced Agent | AGT-01 select、AGT-02 handoff |
| Target | TGT-01 pair/select、TGT-02 permission、TGT-03 takeover/revoke |
| Developer | DEV-01 repo/worktree、DEV-02 checkpoint/git、DEV-03 multidevice/context |
| Automation | AUT-01 routine、CON-01 connector、TASK-01 task view |
| Team/Application | TEAM-01 team、RES-01 wide research、APP-01 application deploy |
| Client | CLIENT-01 install/auth/revoke、CLIENT-02 attach/fork/new run/offline |

## 5. UserVisibleStateCatalog Minimum

| Surface | Product states | Mandatory definition |
|---|---|---|
| Identity | verification_pending、active、challenge_required、locked、recovery_pending、deletion_pending、deleted | CTA、retry window、session effect、Support |
| Workspace invite | pending、accepted、declined、expired、revoked、membership_conflict | visibility、resend/revoke、audit |
| Redeem | validating、review_pending、succeeded、safe_rejected、temporarily_unavailable、reversed、replacement_pending | Code consumed? rights visible? retry safe? |
| Credit | available、reserved、cost_pending、settled、expired、reversed、reconciliation_required | source、amount、freshness、receipt |
| Chat Run | preparing、waiting_input、queued、running、stopping、completed、partial、failed、canceled、unknown、recovering、cost_pending | Stop/Cancel/Continue/Retry and cost |
| Attachment | local_validating、uploading、scanning、ready、quarantined、failed、canceled、expired | progress、Run eligibility、appeal/delete |
| Studio Job | draft、admission_pending、queued、running、finalizing、completed、partial、cancel_requested、canceled、failed、unknown、cost_pending | Provider replay safety、cost、Artifact |
| Artifact/Share | processing、available、moderation_pending、restricted、shared、expired、revoked、trashed、retained、deleted | view/download/share/restore |
| Support Case | draft、submitted、verification_required、triaged、in_progress、waiting_user、waiting_internal、escalated、resolved、closed、reopened | actor、SLA、next action、notification |
| Site Release | draft、validating、preview、candidate、canary、active、draining、rolled_back、failed、suspended、decommissioning | traffic、rollback、user impact |
| Notification | queued、provider_accepted、delivered、failed、unknown、suppressed | channel/action/fallback |

Child PRD 可以把多个内部状态映射到同一产品状态，但不能让同一产品状态同时表示“可以安全重试”和
“重试可能重复扣费/副作用”。

## 6. RecoveryActionCatalog Minimum

| Recovery key | 适用条件 | 必须行为 |
|---|---|---|
| retry_same_identity | 请求确定未执行或幂等 receipt 可查询 | 复用 key/digest，不创建第二 aggregate |
| resume | 有 checkpoint/active stream/paused decision | 保留 revision、lineage、budget segment rules |
| wait_and_refresh | 已提交且 outcome/pending 不由客户端重试解决 | 显示更新时间、deadline、后台 owner |
| provide_input | HITL/review/verification 缺用户材料 | 精确要求、expiry、隐私说明 |
| change_parameters | policy/format/compatibility 可由用户修正 | 保留 draft，不重复收费 |
| reauthenticate | auth strength/session 过期 | 返回原 intent，防 open redirect/CSRF |
| request_support | 系统无法自助收口或达到 SLA | 预填安全 correlation refs，不泄漏 secret/Code |
| appeal | moderation/risk/content decision 可申诉 | 创建新 Appeal/Decision，不覆盖历史 |
| no_user_action | 系统后台 retry/reconcile | 禁止展示误导 CTA，完成时通知 |

## 7. Global Product Baselines

### 7.1 Accessibility

- 所有 Core P0 旅程必须达到 WCAG 2.2 AA；Site policy 只能提高标准。
- keyboard、focus order/return、screen reader name/state、live region、reduced motion、contrast、zoom/reflow、
  error association、timeout extension 是 Release gate。
- Music/Video player、timeline、waveform、canvas/mask 等专业控件必须提供等价可操作路径。

### 7.2 Localization

- 每个 SiteRelease 冻结 supported locales、default、fallback chain、timezone、number/Credit/date format、RTL、
  email/push/legal template revision。
- 缺 translation key、fallback 到错误 Site、法务版本不匹配或 layout overflow 阻断 publish。

### 7.3 Site lifecycle

```text
requested → provisioning → configuring → preview_ready → candidate → active
active ↔ suspended
active/suspended → decommissioning → decommissioned
```

provision 绑定 owner、app、domain、certificate、brand/legal、SiteProjectBinding 和 baseline profile；suspend
明确登录/运行中 Job/历史 Artifact 行为；decommission 先冻结新写入、导出/retention/legal hold、redirect、
domain/certificate 处置，再删除可删资源。它不等于删除 Site 表。

## 8. Requirements v2 Migration

现有 `docs/requirements/` 保留为当前/历史 Chat 验收资料，不能再标“完整产品需求”。迁移规则：

1. Wave 0 更新 README/模板，支持 ProductProfile → Journey → Capability/Contract → Test/Evidence 四层引用。
2. 每个业务 Wave 在产品 PRD批准后才写对应 v2 requirements，不在 Wave 0 空写未来状态。
3. 旧 localStorage 会话权威、HITL 状态矛盾和三仓边界随 Wave 3/8 删除或归档。
4. 每个 Journey ID 必须能反向找到 PRD revision、contract、test、release evidence；orphan test/requirement 阻断。
5. `docs/CURRENT.md` 只指向批准的当前事实与正在复审的目标，明确两者状态，不制造双真源。

## 9. Review 与退出门

本文内部通过需要：

- Reference Profile 没有启用无 PRD/owner/evidence 的 Surface。
- Registry 覆盖 Module Coverage Audit 的所有 Core/Advanced journey family。
- 每个 PRD 只有一个主产品 owner，可列多个协作 owner。
- UserVisibleState 不混淆 retry-safe 与 unknown side-effect。
- WCAG 2.2 AA、Site lifecycle、ContentPolicy、OperatorCommandMatrix 不可被 Site 任意关闭。
- GA 相关 PRD 只冻结产品语义，不隐式授权 GA runtime 重构。

本文批准后也不授权业务实现；它成为各 child PRD 的上游输入。第一个实施计划仍是 Wave 0，且受用户书面
批准与四来源 LicenseRef attestation 约束。

## 10. Dependencies、Risks 与 Milestones

### 10.1 Dependencies

| Dependency | Owner | 影响 |
|---|---|---|
| Umbrella v1.5 书面批准 | Product/Architecture owner | 未批准前不得把 Registry 当实施授权 |
| Wave 0 requirements/index governance | Foundation owner | 没有机器追踪时 Journey/PRD/evidence 会漂移 |
| 每个 PRD accountable owner 与 co-signers | Product leadership | owner 空缺不得以工程师临场产品决策替代 |
| SiteRelease/Certification contract | Wave 1/8/9 owners | Profile、inventory、metrics 与 evidence 无法绑定 |
| Notification/Support 最小 contract | Wave 1 owners | Identity/Redeem/Data Rights 失败旅程无法闭环 |

### 10.2 Risks

| Risk | 影响 | Mitigation |
|---|---|---|
| Registry 变成文档官僚流程 | PRD 慢且无人使用 | 每个 ID 必须链接真实 contract/test/evidence；无消费者条目删除 |
| Parent、PRD、requirements 重复事实 | 冲突和实现误判 | Parent owns boundary；PRD owns product journey；requirements owns testable mapping；INDEX owns current code |
| Reference Profile 被误解为唯一产品 | 阻碍 Music/Image 套皮增长 | 明确它是最低认证基线；其他 Site 用独立 Profile 组合相同后端 |
| 指标目标脱离真实 Provider | 错误 Go/No-Go | 外部故障单列；RC 前只能收紧 target，放宽需正式 risk acceptance 与 expiry |
| Studio 被合并成万能表单 | 专业体验不足 | Common PRD 只共享生命周期；Image/Music/Video 独立 PRD/UAT |
| a11y/i18n/Safety 延后 | Core 上线后高成本返工 | PRD-14/16 是跨 Wave 硬输入，不是 Wave 9 附录 |
| Admin/Support 晚于领域实现 | 无法运营恢复 | 每个领域 cut 同波提供 Admin annex/recovery command；Wave 7 只聚合产品面 |
| Advanced PRD 暗中改 GA | 破坏成熟底座 | PRD-A1 只定义产品语义；命中 GA 改动清单时单独用户批准 |

### 10.3 Milestones

1. Foundation：建立 Registry/Journey/requirements/evidence schema 与 coverage gate。
2. Core definition：批准 Reference Profile 和 PRD-00/01/02/03/05/06/09/10/11/12/14/15/16/17/18。
3. Core execution：按 1→2A→3→5A→4→7 交付启用旅程。
4. Core certification：生成 profile-scoped Wave 8/9 instance 并上线。
5. Optional commerce/studios：2B 和各专业 Studio 按独立 Profile delta certification 开放。
6. Advanced program：5B、6A-6D 逐 cut 产品/技术双审，任何 GA runtime 变更先专项对齐。
7. Transformation final：全部目标 Profile、旧事实源清零和最终 8/9 instance 通过。
