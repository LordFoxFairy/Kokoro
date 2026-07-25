---
artifact: product-requirements-document
prdId: PRD-13
version: "1.0"
created: 2026-07-25
status: internal-review-active
scope: growth-acquisition-seo-deep-link-consent-attribution-experiment-exposure-guardrail-share-indexing
accountableProductRole: Growth Product Lead
mandatoryCosigners: [Privacy, Site Fleet, Analytics, Trust, Accessibility, Web, Commerce, Support, SRE, QA]
engineeringOwner: team:growth-platform-engineering
qaOwner: team:growth-quality
supportOperationsOwner: team:growth-operations
namedOwnerAssignmentStatus: assigned-team-responsibility-ids
implementationAuthorized: false
gaRuntimeSemanticChangeAuthorized: false
---

# PRD-13：Growth、SEO、Experiment 与 Attribution

## 1. Overview

### Problem

Kokoro的增长模型是多个用户无感知关联的独立Site Web Project共享后端能力。若Growth用全局cookie、email、设备指纹或同一
analytics project跨站拼接，会破坏“一Site一产品”的身份和隐私边界；若实验只在前端随机、页面加载即算曝光、统计失败仍
自动promote，会产生错误结论。SEO、Share页面、deep link、登录回跳、Offering和Consent也可能互相绕过Trust、价格、a11y或
SiteRelease。

### Solution

建立Site-scoped Growth domain：版本化Campaign/Link/SEO/Experiment配置，可信SiteContext下的anonymous acquisition session，
same-Site consent-aware attribution，server-side deterministic assignment，render-qualified exposure，guardrail/decision和可回滚
release。Public Share SEO只消费PRD-09/16授权的safe projection；Analytics/Growth失败不阻断Identity、Redeem、Credit、Chat、Job
或Artifact核心链路。

### Users and stories

| ID | User story | Priority |
|---|---|---|
| GR-US-01 | 访客从搜索、广告、推荐或Share进入正确Site和目标页面，不被开放重定向 | P0 if-enabled |
| GR-US-02 | 用户能理解并控制适用的analytics/marketing consent，拒绝后仍可使用核心产品 | P0 |
| GR-US-03 | Growth owner可运行有明确hypothesis、audience、exposure、guardrail和stop rule的实验 | P0 if-enabled |
| GR-US-04 | Site owner可发布robots/sitemap/canonical/metadata并安全撤销被限制的Share索引 | P0 |
| GR-US-05 | Analyst可解释同Site acquisition→registration→redeem→first value漏斗而不查看PII/content | P0 |
| GR-US-06 | 用户在登录、验证或升级后回到原same-Site intent，不重复提交或重复扣费 | P0 |

## 2. Goals、Metrics and Non-Goals

### Goals

1. 所有Growth对象、cookie、pseudonym、事件、assignment和index feed严格immutable `siteId`。
2. SEO、deep link、consent、attribution、experiment、exposure和decision都有version/owner/receipt/recovery。
3. anonymous→authenticated stitching只发生在同Site、同合法purpose和server-verified transition。
4. exposure表示用户真正有机会看到/使用variant，不把assignment、prefetch、bot或后台请求当曝光。
5. 实验不能改变安全底线、付款/积分authority、无障碍、数据权利或未确认Quote。
6. analytics outage、ad blocker或consent拒绝不破坏核心旅程。

### Success metrics

| Metric | Target |
|---|---:|
| 跨Site cookie/pseudonym/stitch/assignment/event关联成功 | 0 |
| open redirect、错误Site deep link或auth return | 0 |
| 未同意仍写非必要analytics/marketing identifier | 0 |
| assignment未真正render仍记录qualified exposure | 0 |
| experiment绕过Trust/price/Credit/a11y/release gate | 0 |
| restricted/revoked Share继续进入新sitemap/index feed | 0 |
| analytics failure导致核心command失败或重复effect | 0 |
| 实验decision缺sample/guardrail/owner/evidence | 0 |
| applicable WCAG 2.2 A/AA experiment regression | 0 |

### Non-goals

- 不建立跨Site customer identity graph、共享登录、email/device fingerprint匹配或第三方data broker profile。
- 不让Growth拥有Catalog/Offering/Order/Payment/Entitlement/Credit/Share/Trust的业务事实。
- 不做隐蔽价格、虚假稀缺、强制同意、预选营销、难取消或其他dark pattern。
- 不把GA prompt/output、文件、Code、卡密、Payment payload或rights evidence写入analytics。
- 不允许实验修改GA graph/prompt/tool/Handoff/checkpoint/terminal；Agent实验另走GA专项审批。
- 不保证搜索引擎或第三方缓存立即删除，只管理Kokoro origin/feed/purge evidence。

## 3. Canonical product objects

```text
GrowthPolicyRevision
  immutable siteId / jurisdiction+purpose / consent requirements
  identifier+event allowlist / retention / vendor+region / effective window

AcquisitionSession
  immutable siteId / anonymousSessionId / pseudonymous browser key
  landing+referrer classification / CampaignLink ref / consent state
  created+lastSeen / expiry / stitchedAccountRef?

CampaignRevision
  immutable siteId / campaignId / objective / audience / active window
  approved landing refs / attribution policy / budget metadata refs / lifecycle

CampaignLinkRevision
  immutable siteId / linkId / campaignRef / exact target intent
  allowed parameters / signature / expiry / one-time policy?

AttributionTouch
  immutable siteId / acquisitionSession / touchId / source+medium+campaign classes
  landing ref / occurredAt / consent+policy revision / evidence class

AttributionRevision
  immutable siteId / subjectGeneration or acquisitionSession / conversion kind
  eligible touches / model=first|last|linear|none / result+confidence / supersedes

ExperimentRevision
  immutable siteId / experimentId / hypothesis / unit+salt revision
  audience+exclusions / variants+weights / metrics+guardrails
  start/stop rules / owner / lifecycle / SiteRelease bindings

ExperimentAssignment
  immutable siteId / experiment revision / unit pseudonym / variant
  assignment digest / issuedAt / expiry / eligibility revision

ExposureFact
  immutable siteId / assignment / surface+component revision
  qualified event / occurredAt / client+server evidence / idempotency

ExperimentDecisionRevision
  immutable siteId / experiment / analysis dataset+code digest
  sample+SRM+quality / metric+guardrail results / decision / approvers

SeoProfileRevision
  immutable siteId / locale/domain / robots+sitemap+canonical policy
  metadata templates / structured data allowlist / indexability rules
```

- ProductMetricRevision拥有metric definition；Growth只引用冻结definition和低敏事件。
- Site Fleet拥有domain/SiteRelease；Growth不能按Host/default猜Site。
- PRD-09/Trust拥有Share/PublicationAuthorization；SEO只投影当前允许对象。
- Commerce拥有Offering/Quote；Growth可选择已发布Offering ref，不能传price/credit amount。

## 4. Site、cookie and pseudonym isolation

- cookie使用Site自己的host-only或精确domain policy、Secure、HttpOnly（server identifiers）、SameSite和purpose-specific expiry。
- 禁止共享parent-domain cookie、localStorage key、analytics user ID、experiment salt或link secret跨Site复用。
- pseudonym由Site-specific key/version生成，不能反推出Account/email，也不能与另Site pseudonym稳定join。
- 相同浏览器、IP、email、OAuth subject、Payment fingerprint或repository不自动关联Site。
- server analytics pipeline和warehouse每行携immutable siteId；row policy、partition、export和query均执行Site scope。
- Global aggregate只允许达到privacy threshold且无法反推Site/user的governance-approved projection，不恢复跨Siteidentity graph。

## 5. Landing and deep-link contract

- `CampaignLinkRevision`只指向allowlisted same-Site route和typed intent；不接受任意return URL、javascript/data/file scheme或raw command。
- UTM/click/referrer参数先长度、字符、重复键和allowlist校验，再映射为低基数source classes；原始query按retention policy丢弃。
- auth/verify/recovery/OAuth return使用server-side single-use intent：冻结siteId、route、resource safe ref、issued/expiry、CSRF state。
- 登录后重验route、SiteRelease、Project/resource authorization和intent freshness；material条件变化显示diff，不自动POST旧command。
- deep link到disabled/restricted/deleted资源返回safe fallback，不泄漏其他Site或原资源存在性。
- bot/prefetch/link scanner请求不创建authenticated conversion、experiment exposure或不可逆intent。

## 6. Consent and privacy

- necessary、functional、analytics、personalization、marketing分别建模；Site/jurisdiction policy决定notice、default和renewal。
- 非必要consent默认不预选；拒绝/撤回路径与接受同等易用，不以拒绝阻止core use。
- ConsentRevision冻结notice locale/a11y、purpose、vendors/categories、issued/expiry/revoke epoch和proof。
- consent前只处理必要security/routing facts；analytics buffer不得“先收后等同意”。
- 撤回推进epoch，停止新identifier/event/vendor export，并按retention/Data Rights创建deletion/deidentification plan。
- 服务端仍可生成不使用非必要identifier的operational metrics，但不得换名字继续做marketing attribution。
- vendor destination、region、schema、data processing purpose和failure policy进入SiteRelease；未知vendor/config fail closed。

## 7. Attribution and stitching

- touch只在policy/consent允许时创建；direct/unknown是合法classification，不补猜source。
- conversion facts来自owner outbox，例如Account verified、Redeem fulfilled、first Run/Job completed，不由浏览器自报success。
- anonymous→account stitching仅在同Site登录成功后，由server验证AcquisitionSession cookie、subject generation、consent、expiry和
  anti-fixation nonce；创建append-onlyStitchFact，不改历史touch。
- login前后session rotation防fixation；攻击者不能把自己的campaign session绑定受害者Account。
- attribution model/version冻结；late touch/conversion创建新AttributionRevision，不覆盖旧报表事实。
- Card Code只记录safe program/campaign ref，绝不记录Code原文/fingerprint到Growth event。
- refund/reversal/account deletion可产生conversion correction fact，但不改Payment/Credit source truth。

## 8. Experiment lifecycle

```text
draft
→ validation
→ preview/internal
→ candidate
→ active
→ paused|stopped
→ analyzing
→ decided=ship|rollback|inconclusive
→ archived
```

### 8.1 Definition and assignment

- hypothesis、primary metric、guardrails、unit、audience、exclusions、minimum sample/duration和stop rule在active前冻结。
- assignment在server/BFF基于Site-specific salt、eligible unit和revision确定；客户端不选variant或传bucket。
- weights/material variant变化创建新revision/experiment phase，不污染旧sample。
- anonymous和authenticated unit切换按明确policy；不得双计或通过登录选择更有利variant。
- assignment稳定但不等于exposure；用户不满足audience/feature/consent时不分流或使用control safe path。

### 8.2 Exposure

- qualified exposure要求variant component实际render/可操作且关键data已加载；prefetch、SSR bot、background tab、error boundary不算。
- 每unit/experiment/phase按metric policy幂等；重复hydration/reconnect不重复exposure。
- client evidence与server surface revision绑定；Analytics接受前校验Site、assignment、variant、release和event schema。
- accessibility variant必须在exposure前通过same release gate，不能把残障用户排除以掩盖失败。

### 8.3 Guardrails and decision

- mandatory guardrails：error/recovery、latency、Credit/payment variance、Trust block/appeal、a11y、Support、retention/consent。
- safety/security/legal/financial invariant不作为可优化metric，variant不能放宽baseline。
- SRM、missing exposure、bot/employee contamination、novelty/seasonality、multiple testing和data freshness在decision前审查。
- automatic stop只可按预注册harm threshold暂停/回滚，不可在证据不足时自动promote。
- decision引用immutable dataset snapshot、analysis code/query digest、metric revisions、结果和approver；`inconclusive`是合法结果。
- ship仍需正常SiteRelease candidate/certification，不让experiment assignment成为长期feature flag authority。

## 9. Forbidden experiment surfaces

以下默认不可实验或只能比较不改变authority的UX：

- phishing-resistant auth、MFA/recovery assurance、CSRF、session expiry和security warnings。
- Card Code entropy/redemption、Credit Journal/Hold/rating/correction。
- Payment amount/currency/tax/refund/dispute和已确认Quote。
- Trust baseline、minor/illegal-content/rights/consent、takedown和evidence access。
- Data Rights、LegalHold、retention/destruction。
- WCAG conformance、required media alternatives和critical error recovery。
- GA graph/prompt/tool/Handoff/checkpoint/cancel/terminal semantics。

需要研究这些领域时使用offline evaluation、shadow evidence或显式专项审批，不能随机真实用户承担风险。

## 10. SEO and public Share

- 每个Site独立robots、sitemap、canonical host/locale、hreflang、OpenGraph和structured data revision。
- canonical URL只使用已验证active domain；preview/candidate/internal host始终noindex。
- sitemap只包含current PublicationAuthorization允许且indexable的public routes/ShareRevision；private token URL永不列入。
- Share metadata来自safe projection，不包含prompt、filename、user identity、Provider/internal IDs或restricted thumbnail。
- revoke/takedown先停止origin和新feed，再异步purge CDN/search submission；状态如实为pending/partial/unknown/complete。
- Appeal overturn不自动恢复旧URL/token/index；创建新PublicationAuthorization和明确republish action。
- structured data/template严格schema/escaping，用户文本不进入raw JSON-LD/HTML；防XSS、SEO spam和prompt leakage。
- 404/410/noindex按resource lifecycle和non-disclosure policy区分；未授权请求不泄漏存在性。

## 11. Analytics event contract

```text
ProductEvent {
  eventId / eventType / schemaVersion
  immutable siteId / SiteRelease+surface revisions
  pseudonymous subject or acquisition session ref
  occurredAt / receivedAt
  consent+policy revision
  low-cardinality dimensions
  correlation/causation safe refs
}
```

- event allowlist、unit、required/forbidden fields、sampling和retention进入registry；unknown event/field quarantine/drop并告警。
- 不包含prompt/output/file/path/repo URL/email/IP raw、Card Code、Payment payload、rights evidence、secret、GA checkpoint/namespace。
- IP/user-agent只在security/short-lived geo/device classification boundary处理，warehouse存低精度class或不存。
- event producer outbox适用于authoritative conversions；view/exposure可由BFF/client签名证据进入dedupe pipeline。
- analytics unavailable使用bounded queue/drop policy，不回压core command；不得为补event重复业务effect。

## 12. User-visible states and recovery

| State | Meaning | Recovery |
|---|---|---|
| consent_required / accepted / declined / withdrawn | purpose选择状态 | review/change；core remains available |
| link_valid / expired / invalid / unavailable | deep link可用性 | safe landing/restart flow |
| experiment_control / variant / paused | 用户看到已认证体验 | no forced action；stable UX |
| analytics_delayed / unavailable | 非核心观测延迟 | core continues；background reconcile/drop by policy |
| share_indexable / noindex / purge_pending | public SEO状态 | owner action/wait/support |

用户无需看到内部experiment ID/bucket，但涉及material UX差异、personalization或consent时提供适用说明和退出路径。

## 13. Admin and operations

- Growth Console提供Site-scoped Campaign/Link/Consent/Attribution/Experiment/Exposure quality/SEO projection，不展示PII/content。
- typed commands：PublishCampaignRevision、Activate/SuspendCampaign、PublishExperimentCandidate、PauseForHarm、StopExperiment、
  RecordExperimentDecision、PublishSeoProfile、RebuildSitemap、RevokeIndexability、RetryManagedPurge。
- high-risk/mass campaign、vendor/consent policy、experimentship和SEO mass publish使用maker-checker、expectedVersion、dry-run和receipt。
- 禁止直接改assignment/exposure/conversion、手工把结果标显著、补写consent、跨Site查email或修改Share/Offering authority。
- monitoring：link errors/open redirect rejects、consent rates、event loss/freshness、SRM、guardrails、sitemap/index/purge、bot traffic、
  vendor export和cross-Site rejects；低基数并按Site/Profile/revision。

## 14. Acceptance criteria

### AC-GR-01 — Cross-Site stitching is impossible

```gherkin
Given the same browser or email interacts with two independent Sites
When login, attribution, experiment assignment and analytics run
Then each Site uses independent cookies, pseudonyms, grants, salts and events
And no user, campaign, conversion or behavior graph is joined across Sites
```

### AC-GR-02 — Deep link returns to exact safe intent

```gherkin
Given a visitor must login or verify before opening a same-Site resource
When the flow completes
Then a server-side single-use intent returns to the allowed route after current authorization
And no external URL, other Site, stale command POST or untrusted parameter is replayed
```

### AC-GR-03 — Consent rejection preserves core use

```gherkin
Given a jurisdiction requires opt-in analytics and marketing consent
When a user declines or later withdraws
Then non-essential identifiers, collection and vendor export stop under the published policy
And Identity, Redeem, Credit, Chat, Job and Artifact core journeys remain usable
```

### AC-GR-04 — Assignment is not exposure

```gherkin
Given a user is assigned a variant but the component is prefetched, hidden, errors or never becomes operable
When exposure processing runs
Then no qualified ExposureFact is recorded
And reconnect or hydration cannot fabricate or duplicate exposure
```

### AC-GR-05 — Experiment cannot weaken invariants

```gherkin
Given a variant changes pricing UX, Trust, security, accessibility or Data Rights behavior
When experiment validation and SiteRelease compile run
Then any weaker invariant or missing certification blocks activation
And assignment cannot bypass the owner authority or confirmed Quote
```

### AC-GR-06 — Decision is reproducible and honest

```gherkin
Given an experiment reaches its planned analysis window
When a ship, rollback or inconclusive decision is recorded
Then dataset, query/code, metric revisions, SRM, guardrails, exclusions and approvers are immutable and reproducible
And missing/stale evidence cannot be represented as a successful experiment
```

### AC-GR-07 — Revoked Share leaves every new SEO feed

```gherkin
Given a public Share is revoked or restricted while crawlers and CDN may cache it
When SEO reconciliation runs
Then origin and all new sitemap/metadata feeds deny it immediately
And purge remains pending, partial or unknown until managed target receipts exist
```

### AC-GR-08 — Analytics outage never repeats business effect

```gherkin
Given a conversion owner commits while analytics ingestion is unavailable
When delivery retries or drops under policy
Then the original business receipt remains authoritative and the same event identity deduplicates
And no Redeem, Payment, Grant, Run, Job or Notification effect is replayed to recover analytics
```

## 15. Verification and release gates

- privacy：two-Site cookie/storage/pseudonym/salt/vendor isolation、consent accept/decline/withdraw、retention/delete和warehouse RLS。
- links：scheme/host/path/query/open redirect、auth return、expired/single-use、bot/prefetch和disabled resource。
- experiment：assignment determinism、anonymous→account transition、exposure qualification、SRM、guardrails、pause/rollback/decision。
- SEO：canonical/robots/sitemap/hreflang/JSON-LD escaping、preview noindex、Share revoke/purge和restricted metadata。
- resilience：analytics/vendor outage、event duplicate/late/drop、Site rollback、key rotation、CDN/search partial和DR restore。
- UX/a11y：consent、landing/auth return、all variants、error/recovery和mobile/locale/RTL完整WCAG 2.2 A/AA。

No-Go：跨Sitecookie/stitch；fingerprinting；open redirect；consent前收集；拒绝阻断core；assignment=exposure；前端自选variant；
实验改ledger/price/Trust/a11y/GA；缺SRM/guardrail仍ship；restricted Share进feed；analytics失败重放业务；PII/content进event。

## 16. Related documents and approval boundary

- [PRD-00 Launch Profile](2026-07-25-prd-00-launch-profile-and-journey-contract.md)
- [PRD-01 Identity](2026-07-25-prd-01-site-identity-and-account-security.md)
- [PRD-04 Billing](2026-07-25-prd-04-checkout-subscription-and-billing.md)
- [PRD-09 Library/Share](2026-07-25-prd-09-library-artifact-export-and-share.md)
- [PRD-12 Site Fleet](2026-07-25-prd-12-site-lifecycle-and-fleet.md)
- [PRD-15 Data Rights](2026-07-25-prd-15-notification-preferences-and-data-rights.md)
- [PRD-16 Trust](2026-07-25-prd-16-trust-content-safety-and-media-rights.md)

本文批准不授权实现或真实用户实验，也不修改GA runtime。任何Agent prompt/tool/graph/Handoff/checkpoint/cancel/terminal实验必须停止
并另行与用户对齐；本PRD只覆盖Web/Platform Growth边界。
