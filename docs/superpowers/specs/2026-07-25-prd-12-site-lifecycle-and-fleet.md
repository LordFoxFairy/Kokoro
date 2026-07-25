---
artifact: product-requirements-document
prdId: PRD-12
version: "1.0"
created: 2026-07-25
status: internal-review-active
scope: site-provision-domain-web-project-profile-release-suspend-decommission-fleet
accountableProductRole: Platform Product Lead
mandatoryCosigners: [Site Fleet, SRE, Security, Release, Legal, Data Governance, Web Platform, QA]
engineeringOwner: team:site-platform-engineering
qaOwner: team:site-fleet-quality
supportOperationsOwner: team:site-fleet-operations
namedOwnerAssignmentStatus: assigned-team-responsibility-ids
implementationAuthorized: false
---

# PRD-12：Site Lifecycle 与 Fleet

## 1. Overview

### Problem

Kokoro 的增长本质是快速发布多个用户无感知、彼此独立的产品 Site。若一个 Site 只是数据库配置或 Host
换皮，就无法独立 IA、SEO、域名、Cookie、法务、认证、发布和回滚；若每个 Site 复制一套后端，则业务和
账务会分叉。还必须处理 provision 半失败、域名/证书丢失、workload identity 撤销、暂停和退站，而不只是
“创建 Site/发布 Release”两个 happy path。

### Solution

一 Site 一独立 Web Project/app/deployment/domain/release cycle；所有 Site 复用同一 Platform、Session、GA、
Job、Gateway 和业务逻辑。Platform `site` 模块拥有 Site lifecycle、Project/Domain/Deployment binding、
Profile binding、SiteRelease 和 ActivationAttempt。Site Fleet 提供标准 scaffold、preview、drift、promote、
rollback、suspend 和 decommission 专用工作流。

### Users and stories

| ID | User story | Priority |
|---|---|---|
| SF-US-01 | Platform operator 能从申请到 preview 创建一个独立且安全绑定的 Site | P0 |
| SF-US-02 | Site owner 能配置品牌/法务/Profile 并在真实 preview 验证 | P0 |
| SF-US-03 | Release owner 能 canary/promote/rollback，崩溃后恢复同一 ActivationAttempt | P0 |
| SF-US-04 | Security operator 能立即 suspend Site 或撤销 binding，同时保留审计和用户补救入口 | P0 |
| SF-US-05 | Data/Legal owner 能安全 decommission Site，不丢强制事实或历史用户权利 | P0 |
| SF-US-06 | Fleet owner 能发现 template/dependency/config drift 并逐 Site 可审阅升级 | P1 |

## 2. Goals、Metrics and Non-Goals

### Goals

- Site identity、Web deployment、domain、Profile、Release 和 workload credential 全部可追溯。
- Site A 的 credential、Cookie、cache、config、数据和品牌永远不能命中 Site B。
- provision/activate/rollback/decommission 每个 crash point 都有 durable attempt/receipt/recovery。
- 新 Site 不需要修改共享后端业务代码或增加 `if (siteId)`。

### Metrics

| Metric | Target |
|---|---:|
| 新 Site 从 approved request 到 preview_ready | p50 ≤ 1 business day；自动基础设施步骤 p95 ≤ 30m |
| 跨 Site 绑定/数据/Cookie/品牌泄漏 | 0 |
| provider promote 后未知且无 reconciler owner | 0 |
| failed activation 影响旧 active Release | 0 |
| production rollback objective | decision 后 ≤ 15m 恢复已认证 Release |
| 未登记 fleet drift | 0；每周全量扫描，Critical 当日 page |
| domain/certificate 到期未提前告警 | 0；至少 30/14/7/1 天告警 |

### Non-Goals

- 不允许一个 deployment 按 Host 动态切换多个 Site。
- 不为每 Site 部署一套后端或复制 Catalog/Model/Commerce 数据。
- Site Fleet 不编辑具体业务表、Provider secret 或用户数据。
- 不将 SiteRelease 与用户 Application/EnvironmentDeployment 合并。
- 不承诺所有 Site 同时升级；共享安全/contract 最低版本除外。

## 3. Product Model

| Object | Meaning |
|---|---|
| SiteRequest | 创建新 Site 的审批意图和 owner/business/legal metadata |
| Site | 永不复用的稳定产品站点 identity、site key 和 lifecycle tombstone |
| SiteProjectBinding | Site 到独立 repository/app/provider project/environment/workload identity 的绑定 |
| DomainBinding | domain、verification、certificate、canonical/redirect policy |
| SiteConfigRevision | runtime feature/policy refs，不保存品牌文案副本 |
| LaunchProductProfileRef | Site 的产品承诺基线 |
| SiteRelease | Web artifact + config/assortment/model/agent/capability/sales/legal revisions 快照 |
| SiteDeploymentBinding | provider deployment 与确切 Release/artifact digest 的可信映射 |
| ActivationAttempt | 外部 promote + active pointer + drain 的 durable workflow |
| DeploymentObservation | provider 实际流量、health、artifact、domain 状态事实 |
| FleetTemplateRevision | app scaffold/toolchain/design-system/contract baseline |
| FleetDriftObservation | Site app 与批准 baseline 的差异和风险 |

## 4. Site Lifecycle

```text
requested → approved → provisioning → configuring → preview_ready → active
requested/approved/provisioning/configuring → rejected | failed
active ↔ suspended
active/suspended → decommissioning → decommissioned
```

`failed` 不是可接流量状态；只能 resume 同一 ProvisioningAttempt 或经过 scoped teardown receipt 后创建新 Attempt。
`suspended → active` 不是直接字段翻转，而是 `RequestSiteResume` 创建新的 ActivationAttempt，重新验证 Domain、
certificate、workload identity、Profile/Release certification、kill switch 和 mandatory inbound policy 后 CAS active。
`decommissioning` 在 Domain/credential revocation 之前允许经 maker-checker cancel 并重编译 plan；进入不可逆点后
只能完成 decommission。`decommissioned` 永不回到 active，也不复用 siteId/site key。

### Requested and approved

SiteRequest 冻结 accountable Product/Site/Engineering/Security/Support owners、site kind、regions/locales、法律
主体、预期 Profile、domain plan、数据驻留/分类和成本 envelope。production Site 要 maker-checker；拒绝保留原因，
不创建可交换 SiteContext 的 binding。

### Provisioning

Durable ProvisioningAttempt 的有序步骤：

```text
reserve site key/id
→ create independent Web app/project from FleetTemplateRevision
→ create provider project/environment
→ establish workload identity and SiteProjectBinding
→ prepare domain verification/certificate
→ bind Reference Profile and baseline config/legal refs
→ deploy preview artifact
→ security/config smoke
→ preview_ready receipt
```

外部步骤前先持久化 intent/idempotency key；timeout 后查询 provider，不创建第二份 project/domain/cert。
失败可 resume 或执行 scoped teardown；orphan resource 进入 reconciliation inventory。

### Active

只有已通过 profile-scoped CertificationInstance 的 SiteRelease 可激活。Active Site 可以有 current、candidate、
draining deployment slots，但一个 environment 只有一个 authoritative active pointer。Release compile 必须纳入
逐 method/provider/client 的 AuthMethodInventory、route/API/Admin inventory 与 disabled negative evidence，不能以
笼统 `auth` Surface 放行未认证 adapter。

### Suspended

SuspensionPolicyRevision 分别定义：landing/status、auth、new acquisition、new admission、active Run/Job、Artifact
read/export、Support、Data Rights、webhook/Payment/Dispute mandatory facts。安全紧急 suspend 可立即阻断新副作用，
但不能拒收外部财务/法律事实或删除历史。

### Decommissioning

DecommissionPlan 必须：

1. 停止新 signup/acquisition/admission，保留明确用户页面。
2. 处理 active Subscription、Code Program、Payment/Dispute、Run/Job/Routine、Share、Case。
3. 通知用户并提供导出/迁移窗口；记录未送达处理。
4. 执行 Retention/LegalHold/Data Governance participants 和对象 GC。
5. 撤销 workload/Provider/Domain/Certificate/secret binding，设置 canonical redirect/gone policy。
6. 验证无 active traffic/credential/orphan resource 后进入 decommissioned。

Site row、Audit 和强制交易事实按政策保留最小记录；decommission 不是 `DELETE FROM site`。
完成后保留 Site tombstone、历史 public key/audience revocation、domain ownership history 和 credential revocation
epoch。旧 cookie、token、SiteContext、workload identity、Release 或 cached binding 必须永久拒绝；domain 未来
重用需要新的 SiteRequest、重新证明控制权、完成 takeover cooldown，并产生新的 siteId，不能恢复旧账户/数据。

## 5. One Site, One Web Project

每个 app 独立拥有 route tree、IA、brand assets、SEO、legal rendering、analytics entry、build/deploy/domain 和
rollback。共享 packages 只提供无品牌 Surface/design/runtime primitives，禁止具体 Site import、Logo/文案、
Host-switch 和 `if(siteId)`。

共享 Web 能力通过受签名、不可变 semver package/artifact registry 发布；每个 Site Project 在自己的 lockfile 中
精确 pin 版本与 provenance，独立 PR/CI/preview/rollback。Site Project 不通过相对路径读取另一个 Site，也不在
生产构建中直接引用共享仓未发布源码。Critical contract/security floor 由 Fleet policy 设 deadline，但升级仍
产生可审阅 diff 和独立 Release evidence。

### Fleet scaffold

`create-site-app` 产品工作流（实现形式由 Wave 1 Spec 冻结）输入 site key、kind、locales、profile 和 owner，
生成独立 app root、INDEX、typed brand token contract、route manifest、deployment config 和 baseline tests。
它不自动 publish production。

### Fleet upgrades

- FleetTemplateRevision 发布 migration guide/codemod、security/contract minimum 和 preview evidence。
- 每个 Site 通过独立 PR 接受升级，可保留产品发布节奏。
- Critical security/contract floor 有 deadline；过期阻断下一次 Release，必要时实时 kill switch。
- Drift 不等于所有差异错误：approved customization 有 owner/reason/expiry；unregistered drift 告警。

## 6. Domain、Certificate and Workload Identity

- Domain 先以 DNS challenge 验证 control，再创建/观察 certificate；Host 只路由，不证明 Site identity。
- canonical、www/apex、locale subpath/subdomain 和 redirect policy 由 Site Web/DomainBinding 冻结。
- certificate renewal、CAA/DNS change、provider deletion 和 domain takeover risk 持续观察。
- Web BFF 以 SiteProjectBinding workload identity 交换短期 SiteContext；browser 不持有 credential。
- credential audience/scope/environment 最小化；rotation 支持 current/next overlap，旧 credential 明确 revoke。
- provider project/deployment 只能绑定一个 Site/environment；复用检测 hard fail。
- SiteProjectBinding 与 WorkloadIdentityBinding 使用独立 generation/epoch；交换 SiteContext 时同时验证 provider
  subject、environment、artifact/release digest、audience 与 active binding generation。Site app 自报 header、Host、
  siteId、project id 或 release id 均不能扩大绑定。

## 7. SiteRelease and Activation UX

### Candidate preparation

Operator 看到 Web artifact、Profile/Surface diff、config/assortment/model/agent/capability/sales/legal diff、DB/
contract compatibility、test/evidence expiry、accepted risks 和 rollback target。未知或无 owner diff 阻断。

### ActivationAttempt states

```text
preparing → promote_requested → observing → pointer_committing → draining → succeeded
          └→ failed | unknown
```

- provider operation key 从 activationAttemptId 稳定派生。
- provider unknown 时只查询/reconcile，不发第二次 promote。
- observation 达到 frozen health/traffic predicate 后才 CAS active pointer。
- pointer 被其他 Attempt 改变时，不覆盖新 pointer；candidate 进入 drain/compensate。
- pointer 已切但旧 deployment 未 drain 时 Attempt 仍未 succeeded。

### Rollback

Rollback 创建新的 ActivationAttempt 指向旧 immutable Release，并重新校验 kill switch、secret revocation、
schema/contract 和当前 policy。数据库 migration 使用 forward repair，不用破坏性逆迁移。

## 8. User-visible and Operator States

| Area | States | Required action/meaning |
|---|---|---|
| Site request | draft、submitted、reviewing、approved、rejected | edit/submit/provide evidence/appeal |
| Site lifecycle | provisioning、configuring、preview_ready、active、suspended、decommissioning、decommissioned、failed | owner、progress、next safe command、user impact |
| Domain | pending_verification、verified、certificate_pending、active、expiring、failed、revoked | DNS action、deadline、fallback/runbook |
| Release | draft、validating、ready、activating、active、draining、retired、failed | evidence、approval、promote/rollback |
| Activation | preparing、promote_requested、observing、pointer_committing、draining、succeeded、failed、unknown | provider reality、retry safety、reconcile owner |
| Fleet drift | compliant、approved_variance、upgrade_available、security_required、contract_blocked | PR/codemod/deadline/exception |

用户只看到 active/suspended/decommission notice 和可用动作，不暴露 provider/internal attempt 枚举。

## 9. Admin、Support and Governance

- Site Fleet 是专用 Admin Surface，不使用万能 ResourceTable。
- 角色区分 Platform Site Provisioner、Site Owner、Release Approver、Security/SRE、Auditor；production publish、
  suspend、decommission、domain/credential change 均在 OperatorCommandMatrix。
- Support 可以确认 Site 状态和用户影响，但不能切 Release、改 domain 或跨站搜索用户。
- 每个 Site 有 status/incident communication owner、SupportTier、runbook、dashboard 和 escalation。
- decommission/suspend/rollback 必须生成用户/Support communication plan 和 delivery evidence。

## 10. Edge Cases

| Scenario | Expected behavior |
|---|---|
| provider project 已创建但 DB receipt 丢失 | 按 provisioning key 查询并认领；不重复创建 |
| domain verification 被第三方改变 | binding 进入 failed/revoked，停止 promote，告警 takeover risk |
| certificate 到期 | 提前告警；无法续期时阻止新 candidate并执行流量/通知 runbook |
| Web deployment 自报另一 Site | SiteDeploymentBinding 校验拒绝 |
| Profile/Legal/Assortment 在 validation 后更新 | candidate 使用冻结 refs；新 revision 需重新 compile/certify |
| promote 成功、pointer CAS 前 crash | reconciler 观察实际流量并继续同一 Attempt |
| pointer CAS 成功、drain 前 crash | active 保持，恢复 drain/observation，不回滚新 Release |
| suspend 与在途 Redemption 并发 | availability/security线性化规则决定；返回后无新成功，已提交事实保留 |
| decommission 有 active Dispute/LegalHold | 保留 mandatory processing 和最小后台，不宣告完全删除 |
| Site owner 离职 | owner transfer/Platform governance Case，不共享 credential 或数据库改 owner |
| fleet template升级破坏品牌定制 | preview diff/codemod PR；不自动覆盖 Site-owned assets |
| suspended Site 直接改 status=active | 拒绝；必须用新 ActivationAttempt 重新认证 binding/domain/profile/release |
| decommission 后旧 cookie/token/workload credential 重放 | tombstone/revocation epoch 永久拒绝，不恢复旧 SiteContext |
| 旧 domain 被新 Site 使用 | 新 SiteRequest + control proof + takeover cooldown + 新 siteId；不关联旧账户/数据 |
| Site Project 引用未发布 shared source | build/provenance gate 拒绝；只能 pin signed immutable package/artifact |

## 11. Acceptance Criteria

### AC-SF-01 — Isolated provisioning

```gherkin
Given two approved SiteRequests use the same backend capabilities
When both are provisioned
Then they have different Web projects, workload identities, domains and SiteProjectBindings
And each credential can exchange SiteContext only for its bound Site/environment
```

### AC-SF-02 — Crash-safe provisioning

```gherkin
Given provider project creation succeeds and the worker crashes before local receipt persistence
When provisioning resumes
Then it queries by the same provider operation key and records the existing project
And no duplicate provider project or credential is created
```

### AC-SF-03 — Failed candidate protects active

```gherkin
Given an active healthy Release and a candidate with expired evidence
When activation is requested
Then validation fails before traffic promotion
And the active Release and user sessions remain unchanged
```

### AC-SF-04 — Unknown promotion

```gherkin
Given provider promotion times out with unknown outcome
When the reconciler runs
Then it observes the same provider operation and traffic state
And it never sends a second blind promote
And pointer commit occurs only after the frozen predicate is proven
```

### AC-SF-05 — Suspend preserves mandatory facts

```gherkin
Given a Site is suspended for security
When users attempt new admission and a Payment dispute webhook arrives
Then new admission fails closed
And the signed external dispute fact is still accepted and reconciled
And users retain the published Support/Data Rights path
```

### AC-SF-06 — Decommission closure

```gherkin
Given a Site has users, Artifacts, active Cases and a LegalHold
When decommission is approved
Then new product writes stop and users receive export/closure instructions
And decommission remains in progress until all mandatory retention, Case, domain, credential and GC receipts exist
```

### AC-SF-07 — No Host-based authority

```gherkin
Given a request uses Site A Host with Site B cookie, release id or forged site header
When it reaches a protected command
Then trusted workload binding and actor audience validation reject it
And no default Site fallback occurs
```

### AC-SF-08 — Resume is a certified activation

```gherkin
Given a Site is suspended and its prior workload credential or certification has expired
When an operator requests resume
Then a new ActivationAttempt revalidates domain, certificate, workload binding, Profile, Release and kill switches
And no direct lifecycle field update can restore traffic
```

### AC-SF-09 — Decommission cannot be resurrected

```gherkin
Given a Site completed decommission and retained a tombstone plus revocation epoch
When an old cookie, token, workload credential, SiteContext, Release or cached binding is replayed
Then every protected exchange fails closed permanently
And reusing the former domain requires a new SiteRequest, proof, cooldown and new siteId without old account linkage
```

### AC-SF-10 — Independent Web supply chain

```gherkin
Given two Site Projects consume the same shared Web primitive revision
When one Site upgrades or rolls back its pinned package and lockfile
Then the other Site's source, build, deployment and Release remain unchanged
And an unsigned, mutable or unpublished shared source dependency fails provenance verification
```

## 12. Analytics、Dependencies and Risks

Events：request submitted/approved/rejected、provision step/receipt/orphan、domain/certificate state、preview/certification、
ActivationAttempt/Observation/pointer/drain、rollback、suspend/resume、decommission step、fleet drift/upgrade/exception。
敏感 provider refs 和 credential 不进入 analytics。

| Risk | Mitigation |
|---|---|
| Site Fleet 变成后端业务编排中心 | 只管理 Site/Release/bindings；业务 assignment 通过 owner revisions |
| 自动化脚本不可恢复 | durable attempt、provider idempotency/query、receipt、orphan reconciler |
| Site 定制导致共享包分叉 | semantic contract + explicit Site app ownership + drift review |
| 全站 suspend 阻断财务/数据权利 | policy 区分新副作用与 mandatory inbound/Support/Governance |
| decommission 误删法定事实 | Data Governance Plan、LegalHold、participant/GC receipts |
| 多 Site credential 泄漏 | workload identity、audience、rotation、no browser secret、cross-site negative E2E |

Milestones：Wave 0 建 Fleet/INDEX/template governance；Wave 1 实现 Site lifecycle、binding、Profile compile 和
ActivationAttempt；Wave 7 完成专用 Admin/Support/Fleet drift/decommission；Wave 9 以两个独立 Site 进行 provision/
promote/rollback/suspend 演练。

本文不涉及 GA runtime；批准也不授权实现。
