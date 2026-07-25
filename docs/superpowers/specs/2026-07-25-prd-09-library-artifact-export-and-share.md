---
artifact: product-requirements-document
prdId: PRD-09
version: "1.0"
created: 2026-07-25
status: internal-review-active
scope: library-artifact-lineage-collection-search-trash-quota-export-delivery-share-revoke-report
accountableProductRole: Library and Artifact Product Lead
mandatoryCosigners: [Artifact, Asset, Trust, Rights, Data Governance, Accessibility, Web, Support, SRE, QA]
engineeringOwner: team:library-artifact-engineering
qaOwner: team:library-artifact-quality
supportOperationsOwner: team:library-artifact-operations
namedOwnerAssignmentStatus: assigned-team-responsibility-ids
implementationAuthorized: false
gaRuntimeSemanticChangeAuthorized: false
---

# PRD-09：Library、Artifact、Export 与 Share

## 1. Overview

### Problem

Chat 与各 Studio 会产生消息附件、候选、版本、track、rendition 和导出结果。若 Library 直接把 object storage 列表当作品库，
会丢失 Artifact lineage、Site/Project 权限、Trust/rights 状态、logical/physical quota、trash/legal hold 与 active Job 引用；若
Share 只是公开一个长期 storage URL，撤销、申诉、takedown、访问审计和跨 Site 隔离均无法成立。

### Solution

Library 是 Artifact owner facts 的 Site-scoped 产品投影，不拥有 Blob、Trust Decision、Credit 或 Job。核心 Profile 提供最小
Library：browse、search、filter、lineage、collection、trash、restore、quota、preview、download/export request。Share/Public
是独立 if-enabled capability，通过短期 PublicationAuthorization、ShareRevision 和 DeliveryGrant 发布，不改变 ArtifactVersion。

### Users and stories

| ID | User story | Priority |
|---|---|---|
| LIB-US-01 | 用户可按 Project、类型、来源、日期和状态找到自己的 Artifact 与版本 | P0 |
| LIB-US-02 | 用户可查看来源、父子版本、Job、费用和当前可用动作，不把同 Blob 当同作品 | P0 |
| LIB-US-03 | 用户可收藏、组织、移入回收站、恢复，并理解 quota、retention 与不可删除原因 | P0 |
| LIB-US-04 | 用户可请求适用的 rendition/download/export，断线后恢复同一请求 | P0 |
| LIB-US-05 | 启用 Share 时，用户可发布、过期、撤销、查看限制与处理举报 | P0 if-enabled |
| LIB-US-06 | 键盘、屏幕阅读器和移动用户可完成浏览、筛选、预览、版本、trash和export流程 | P0 |

## 2. Goals、Metrics and Non-Goals

### Goals

1. LibraryItem、Artifact、ArtifactVersion、Blob、Asset、Job 与 Share 权威不混合。
2. 所有列表、search cursor、lineage、delivery和operator action保持 immutable `siteId` 隔离。
3. logical ownership、physical bytes、trash、retention、LegalHold与quota口径可解释、可重建。
4. download/export/share分别授权；private可用不等于public、commercial或remix可用。
5. 删除、撤销、purge和GC如实表达异步/partial/unknown，不伪造“已彻底删除”。
6. minimal Library可随core-redeem-chat Profile编译；Share/SEO缺PRD-13证据时保持关闭。

### Success metrics

| Metric | Target |
|---|---:|
| 跨 Site list/search/lineage/preview/delivery信息泄漏 | 0 |
| Library projection把不同ArtifactVersion因同Blob错误合并 | 0 |
| active lineage/LegalHold/retention对象被GC | 0 |
| trash/restore/delete重复请求产生冲突终态 | 0 |
| restricted/current-epoch invalid对象获得download/share token | 0 |
| export response丢失导致重复RenditionJob或重复charge | 0 |
| Library完整流程适用WCAG 2.2 A/AA failure | 0 |

### Non-goals

- Library不写ArtifactVersion、Blob、Trust Decision、Usage、Credit Journal或Provider effect。
- V1不提供跨Site共享账户、全局素材市场、公共发现流、协同DAM、任意外部URL导入或无限自定义metadata schema。
- Share不是对象存储ACL、永久URL、跨Site授权或SEO自动开启。
- trash不等于物理删除；deletion receipt不承诺删除LegalHold、已结算事实或合法保留证据。
- 本PRD不修改GA；GA只消费/产生opaque Artifact或Job handle。

## 3. Scope and Profile split

### Core `minimal-library@1`

- Project-scoped browse/search/filter/sort、recent、favorites、collections和stable pagination。
- Artifact/version详情、lineage、source Job、safe cost/rights/status projections。
- preview、eligible download、rendition/export request、request recovery。
- trash/restore/deletion request、quota/retention解释、Support入口。
- desktop/mobile/a11y、empty/error/stale/rebuilding状态。

### If-enabled Share

- private link或public ShareRevision、audience、expiry、password/access policy、download/remix permission。
- publication eligibility、current-epoch token、revoke、takedown、report、purge progress。
- SEO/indexing/attribution只有PRD-13和Site Profile同时启用才可打开。

## 4. Canonical Product Objects and ownership

```text
LibraryItemProjection
  immutable siteId / libraryItemId / artifactRef / currentArtifactVersionRef
  projectRef / owner subject generation / media class / title+safe metadata
  source surface+Operation+Job refs / availability+cost states / freshness

CollectionRevision
  immutable siteId / collectionId / projectRef / title / ordered or rule-based members
  baseRevision / membership digest / createdBy / lifecycle

FavoriteBinding
  immutable siteId / subject generation / artifactVersionRef / createdAt

LineageProjection
  immutable siteId / artifactVersionRef / parent+source refs / relation kind
  projection revision+watermark / completeness

TrashEntry
  immutable siteId / artifactRef / requestedBy / trashedAt / purgeEligibleAt
  restore policy / active blockers / retention+LegalHold refs / state

QuotaProjection
  immutable siteId / billingAccount+project refs / logical active+trash+retained units
  physical attributed bytes / limit revision / freshness / explanation

ExportRequest
  immutable siteId / artifactVersionRef / outputProfileRevision / purpose+audience
  request identity+digest / RenditionJob? / delivery state / cost projection

ShareRevision
  immutable siteId / shareId / artifactVersionRef / audience+purpose / expiry
  download+remix policy / publication+restriction epochs / lifecycle / supersedes

DeliveryGrant
  immutable siteId / artifactVersion or rendition ref / subject or share audience
  purpose / policy+rights+consent+restriction epochs / short TTL / nonce
```

- Artifact owner独占Artifact/ArtifactVersion/Blob/lineage facts；Library只保存可重建projection和用户组织metadata。
- Trust独占Decision、Rights/Consent restriction与PublicationAuthorization；Share只能引用当前owner-issued facts。
- Data Governance独占retention、LegalHold、erasure disposition和destruction receipt；GC只消费授权计划。
- Rating/Credit独占customer charge；ExportRequest仅显示quote/cost projection。
- 所有对象、唯一键、search index、cursor、cache key、CDN mapping和audit事件均包含immutable `siteId`。

## 5. Browse、Search、Collection and Lineage

- query默认注入server-resolved Site/subject/Project scope；客户端siteId不是授权依据。
- filters至少包括Project、media class、source surface、created/updated、availability、restriction、favorite、trash和collection。
- cursor绑定siteId、query digest、sort revision和expiry；不能跨query、用户或Site复用，也不泄漏总数差异。
- search index是projection，可显示freshness/rebuilding；read-by-id仍回到authority authorization，不因索引命中放行。
- title/tag/collection是Library metadata revision，不改ArtifactVersion；并发修改用baseRevision CAS，不last-write-wins。
- lineage DAG显示parent/source/relation和缺失/retained节点；同Blob checksum不合并identity、ownership、rights或cost。
- restricted节点只显示safe category和可用remedy，不渲染thumbnail、prompt、raw metadata或相邻受限内容。

## 6. Preview、Export and Delivery

- preview根据media class使用短期DeliveryGrant；image/video/audio/document structured alternative与player控制遵循PRD-14。
- original download、format conversion、resize/transcode、stem/package和caption bundle使用不同OutputProfileRevision/purpose。
- ExportRequest identity为`(siteId, artifactVersionRef, subjectGeneration, purpose, idempotencyKey)+requestDigest`；同key异digest拒绝。
- 已存在合格rendition时可复用ArtifactVersion ref；否则创建RenditionJob，不重跑generation、修改source或隐藏charge。
- response丢失只查询同ExportRequest；delivery token过期只重mint，不创建第二RenditionJob或charge。
- 每次mint和受控访问复验Site、subject/project、policy、rights、consent、restriction、a11y与TTL；storage key永不返回。
- output无效时finalizer只重试Blob/Artifact/Usage receipts，不rerunProvider effect。

## 7. Trash、Restore、Retention、Quota and GC

- trash是用户可逆的visibility/lifecycle command，不立即删Blob、Artifact、lineage、Usage或Trust facts。
- active Job/source grant、child lineage、Share、LegalHold、retention、Support/appeal会形成typed blocker；UI显示safe类别和next actor。
- restore在purge commit前使用same TrashEntry expectedVersion；若Project/entitlement/rights变化，恢复identity但重新评估可用动作。
- purge eligibility由Data Governance计划决定；origin revoke先于异步thumbnail/CDN/search/object cleanup。
- Blob GC必须证明无active Asset/Artifact/rendition/Job/retention/legal references；去重Blob只在最后一个可删引用后处理。
- quota同时展示logical active、trash、retained与可选physical attribution；dedupe savings不改变用户ownership或删除权。
- quota projection stale时阻止会超额的effect或要求authority refresh，不以旧数值承诺成功。

## 8. Share、Revoke、Report and Publication

- Share创建前要求current PublicationAuthorization；private preview eligibility不自动允许public、download、remix或SEO。
- ShareRevision不可原地扩大audience/purpose；material change创建新revision并撤销旧DeliveryGrant。
- origin authorization在takedown/revoke时同步拒绝；CDN/search purge异步表示`pending|partial|unknown|complete`并持续reconcile。
- rights/consent/restriction epoch变化后旧Share/token不复活；Appeal overturn也需新Decision与新PublicationAuthorization。
- report intake使用Site-bound target token、rate/bot defense、safe attachment intake和pseudonymous reporter key；不向双方泄漏身份。
- password/secret link只存强hash与rate limit state；URL、analytics、logs和referrer不得携带raw secret。
- SEO metadata只消费safe public projection；Share关闭、restricted或purge pending时禁止继续生成新index feed。

## 9. User-visible states and recovery

| State | Meaning | Recovery |
|---|---|---|
| available / processing | Artifact可用或projection/rendition处理中 | open/wait/refresh |
| stale / rebuilding | search/lineage/quota projection落后 | show freshness/query authority/wait |
| moderation_pending / restricted | Trust尚未允许或已限制 | safe reason/appeal/delete where allowed |
| export_pending / cost_pending | rendition或结算未完成 | query same request/wait/receipt |
| export_blocked | rights/a11y/profile/entitlement不足 | remedy/change profile/appeal |
| shared / expiring / expired | Share有效、将过期或已过期 | view/extend by new revision/recreate |
| revoke_pending / purge_partial / purge_unknown | origin已撤或边缘清理未完 | wait/Support；不宣称complete |
| trashed / restore_blocked | 已隐藏或因policy/project阻止恢复 | restore/remedy/Support |
| purge_scheduled / retained / legal_hold | 等待删除或依法保留 | cancel where allowed/view safe reason |
| deleted | 可删资源已按plan处理且有receipt | no restore/Support for receipt |

每个状态显示owner、freshness、费用、retry safety、deadline、CTA和Site-bound Support deep link；unknown不得展示create-again来
绕过同一不确定effect。

## 10. Admin、Support and Operations

- Library Console提供safe Artifact/lineage/Share/trash/quota/export timeline；默认不加载raw content、prompt或rights evidence。
- typed commands：RebuildLibraryProjection、ReconcileExportRequest、RetryRenditionFinalization、RevokeShareAtOrigin、
  RetryManagedPurge、ReevaluateEligibility、ExecuteAuthorizedGCPlan。禁止mark clean/available/deleted、改Usage/Credit或直接删Blob。
- command均登记Site/resource、role、reason、step-up/maker-checker、expectedVersion、idempotency、audit、notification、receipt和runbook。
- metrics覆盖projection lag、search correctness、lineage gaps、quota freshness、trash/restore、retention blockers、export latency/
  duplication、Share revoke/purge aging、cross-Site rejects与a11y；按Site/Profile/revision切分。

## 11. Acceptance Criteria

### AC-LIB-01 — Cross-Site browse and direct read are confined

```gherkin
Given Site A owns an Artifact, collection, lineage, export and Share
When Site B searches, guesses an ID, reuses a cursor or presents a delivery token
Then every path rejects without disclosing existence, count, timing, metadata or policy
And no cache, index or CDN mapping crosses the Site boundary
```

### AC-LIB-02 — Same Blob does not merge Artifact identity

```gherkin
Given two ArtifactVersions share deduplicated bytes but have different Sites, Operations or rights
When Library projects and later deletes one reference
Then identities, lineage, authorization, quota attribution and history remain separate
And Blob GC cannot run while any protected reference remains
```

### AC-LIB-03 — Export is idempotent and does not regenerate source

```gherkin
Given an ExportRequest response is lost after a RenditionJob is accepted
When the client retries the same identity and digest
Then it receives the same request, Job, Hold allocation and eventual delivery
And no generation rerun, duplicate rendition or duplicate charge occurs
```

### AC-LIB-04 — Trash and restore respect blockers

```gherkin
Given an Artifact has active lineage, Share, retention or LegalHold references
When the user trashes or requests deletion
Then Library hides it where allowed but exposes safe blocker categories and deadlines
And restore or purge uses versioned authority without mutating historical facts
```

### AC-LIB-05 — Publication revocation wins every race

```gherkin
Given a Share and DeliveryGrant were issued before rights or restriction revocation
When a viewer mints or uses a token after the epoch changes
Then origin access is denied and managed purge continues as pending, partial or unknown
And no Appeal, cached token or rebuilt Share silently restores the old authorization
```

### AC-LIB-06 — Search rebuild does not become authority

```gherkin
Given the Library index is stale or rebuilding
When a result is listed or omitted
Then read, preview and action authorization still consult current owner facts
And UI shows freshness without leaking restricted or cross-Site totals
```

### AC-LIB-07 — Quota and GC remain explainable

```gherkin
Given active, trashed, retained and deduplicated objects contribute differently
When quota and deletion are shown
Then logical and physical measures, freshness and blockers are separately explained
And no stale projection or dedupe claim authorizes an unsafe effect or GC
```

### AC-LIB-08 — Accessible Library complete process

```gherkin
Given a keyboard or screen-reader user browses, filters, opens lineage, previews media, trashes, restores and exports
When structured controls are used on desktop or mobile
Then they perform the same canonical commands as visual interactions
And every enabled page, state and recovery path satisfies applicable WCAG 2.2 A/AA
```

## 12. Verification and Release Gates

- schema/property：cursor/query binding、CAS collections、lineage DAG、Export identity、Trash transitions、quota arithmetic、GC reachability。
- security：cross-Site ID/cursor/cache/CDN/token negative matrix、enumeration、signed URL replay、secret link rate limit、report abuse。
- integration/chaos：index lag/rebuild、object store outage、Rendition finalizer crash、duplicate request、rights revoke、partial CDN purge、DR restore。
- accessibility：grid/list/filters/preview/player/lineage/trash/export/share在desktop/mobile与真实browser/AT完整流程。
- data governance：active lineage、retention、LegalHold、export/delete concurrency、destruction receipt和dedupe Blob最后引用。

No-Go：Library直列storage；跨Site泄漏；sameBlob合并Artifact；search index授权；unknown重复export；trash即物理删除；
active/retained对象GC；private allow直接Share；永久storage URL；purge partial宣称complete；缺PRD-14证据仍发布。

## 13. Related Documents and Approval Boundary

- [PRD-00 Launch Profile](2026-07-25-prd-00-launch-profile-and-journey-contract.md)
- [PRD-06 Asset](2026-07-25-prd-06-asset-intake-and-attachment-safety.md)
- [PRD-07 Studio Common](2026-07-25-prd-07-studio-common-job-and-cost-ux.md)
- [PRD-14 Accessibility](2026-07-25-prd-14-localization-and-accessibility.md)
- [PRD-15 Data Rights](2026-07-25-prd-15-notification-preferences-and-data-rights.md)
- [PRD-16 Trust](2026-07-25-prd-16-trust-content-safety-and-media-rights.md)

本文批准不授权实现，也不修改GA runtime。Share/SEO只有在PRD-13、Trust、Legal、A11y和Site delta Certification完整时启用。
