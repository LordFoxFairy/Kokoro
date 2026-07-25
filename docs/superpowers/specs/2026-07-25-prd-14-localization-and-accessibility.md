---
artifact: product-requirements-document
prdId: PRD-14
version: "1.0"
created: 2026-07-25
status: internal-review-active
scope: localization-internationalization-accessibility-browser-assistive-technology
accountableProductRole: Design Systems & Accessibility Lead
mandatoryCosigners: [Web, Product, Legal, Notification, Support, Trust, QA]
engineeringOwner: team:web-platform-engineering
qaOwner: team:accessibility-localization-quality
supportOperationsOwner: team:accessibility-support-operations
namedOwnerAssignmentStatus: assigned-team-responsibility-ids
implementationAuthorized: false
---

# PRD-14：Localization 与 Accessibility

## 1. Overview

### Problem

Kokoro 会以一 Site 一独立 Web Project 的方式发布 Chat、Image、Music、Video 等产品。若 locale、时区、数字、
法务模板、邮件和无障碍只由页面临时处理，同一用户会在 Web、邮件、导出、Support 与后台看到不同语言和时间，
动态 Chat stream、HITL、媒体播放器、canvas 等控件也可能对键盘和辅助技术不可用。上线后再补会造成组件、文案、
测试和数据模型的系统性返工。

### Solution

建立跨 Site 的版本化 `LocalePolicyRevision`、`TranslationBundleRevision`、`AccessibilityBaselineRevision` 与
`BrowserAssistiveTechnologyMatrixRevision`。SiteRelease 冻结支持语言、默认语言、fallback、时区和法务/通知
模板；每个 Web Project 复用无品牌、可访问的共享 primitives，但独立拥有产品 IA 和文案。每个 enabled
Surface 的完整页面、响应式变体、用户可见状态和完整流程都必须满足全部适用 WCAG 2.2 A/AA success
criteria；P0 Journey 只是必跑认证套件，不缩小合规范围。Site 只能收紧，不能降低平台底线。

### Users and stories

| ID | User story | Priority |
|---|---|---|
| UX-US-01 | 用户在 Web、邮件、导出和 Support 中看到一致、正确的语言与格式 | P0 |
| UX-US-02 | 键盘和屏幕阅读器用户可以完成注册、兑换、Chat、Studio、Support 与数据权利全流程 | P0 |
| UX-US-03 | 用户可以理解 streaming、等待、错误、HITL 和长任务状态，而不被逐 token 播报淹没 | P0 |
| UX-US-04 | Music/Video/waveform/canvas/mask 等专业控件提供等价可操作路径 | P0 if-enabled |
| UX-US-05 | Site operator 在发布前看到缺翻译、法务不匹配、overflow、RTL 和 a11y blocker | P0 |

## 2. Goals、Metrics and Non-Goals

### Goals

1. 所有用户可见 surface、通知、法务与导出使用同一 Site/locale revision 链。
2. 所有 enabled Surface 的 full page/complete process 达到 WCAG 2.2 AA，并可由真实键盘/AT 用户完成。
3. 缺 key、错误 Site fallback、法务版本错配和任一适用 WCAG 2.2 A/AA failure 阻断 Release。
4. 动态 AI UI 有稳定 focus、announcement、reduced-motion 和 timeout 行为。

### Success Metrics

| Metric | Target |
|---|---:|
| production missing translation key 或跨 Site fallback | 0 |
| enabled Surface 任一适用 A/AA criterion failure | 0；全部为 Release blocker |
| full-page/complete-process manual pass | 100% certification scope |
| keyboard-only completion rate | 100% certification scenarios |
| supported screen-reader/browser matrix pass | 100% blocking cells |
| legal/notification locale revision mismatch | 0 |
| layout overflow/clip at 200% zoom or required reflow | 0 blocker |
| AT 用户 P0 Journey completion/recovery、error/abandonment | 分 Site/Profile/locale/AT family 建立 baseline 并持续改善；不替代 WCAG gate |
| production a11y regression MTTA/MTTR | 绑定 ProductMetricRevision、page 与 release action |

每项引用 ProductMetricRevision，冻结 denominator、window、matrix、owner、guardrail 和 release action。

### Non-Goals

- 不要求首发支持所有语言；每个 SiteRelease 只承诺其明确 inventory。
- 不用机器翻译直接发布法务、安全、支付、恢复或处罚文案。
- 不以自动扫描替代人工键盘、屏幕阅读器、zoom/reflow 和认知负荷测试。
- 不强迫所有 Site 使用相同视觉品牌或 IA。
- 不把 locale 当 Site、身份、价格、权限或账务 authority。

## 3. Product Contracts

```text
LocalePolicyRevision
  siteId / supportedLocaleTags / defaultLocale / fallbackGraph
  urlStrategy / userPreferencePolicy / timezonePolicy
  number/currency/credit/date/relative-time/list/plural rules
  cldrVersion / icuOrIntlCapabilityDigest / tzdbVersion
  messageSyntaxVersion / formatterRevision / localeMatchingRevision

TranslationBundleRevision
  siteId / locale / namespace / sourceDigest / legalAndTemplateRefs
  reviewStatus / provenance / publishedAt

AccessibilityBaselineRevision
  wcagVersion=2.2 / conformance=AA
  conformanceScope / fullPageRefs / completeProcessRefs / technologyRefs
  accessibilitySupportRefs / thirdPartyContentPolicy / conformingAlternateRefs
  nonInterferenceEvidence / componentPatternRefs / interactionRules / mediaAlternativeRules

BrowserAssistiveTechnologyMatrixRevision
  browser/os/AT/version cells / blocking level / evidence validity

MediaAccessibilityRevision
  mediaClass=prerecorded_audio_only|prerecorded_video_only|prerecorded_synchronized|
    live_synchronized|live_audio_only|decorative|media_alternative_for_text
  applicableCriterionIds / contentLanguageTag / timeBasedMediaAlternativeRef
  captionTrackRef / audioTrackRef / audioDescriptionRef / textAlternativeRef
  qualityReview / exceptionCriterionId+exceptionEvidence / publishabilityStatus

LocaleMatchingRevision
  ianaLanguageSubtagRegistryFileDate / cldrAliasVersion / canonicalizationPipelineOrder
  matchingMode=rfc4647_lookup / rawRangePreservationPolicy / extensionAndPrivateUseComparisonPolicy
  acceptLanguageParserRevision / qTieAndInputOrderPolicy / wildcardDefaultPolicy / selectedSupportedTagPolicy

UnicodeInputPolicyRevision
  fieldClass=display_text|searchable_text|identifier|filename|secret|opaque_code|signed_payload
  normalization/caseFold/localeTransform policy / rawValueRetention / derivedSearchKeyRevision

TemporalPolicyRevision
  gapPolicy=reject|shift_forward|shift_backward / overlapPolicy=earlier|later|reject
  recurrenceIdentityRule / recomputeEffectiveFrom / historicalRenderingPolicy
  businessCalendarRevision / authoritativeDeadlineInstant

TimingPolicyRevision
  owner / duration / journey+state / conformancePath
  warningLeadTime / extensionCount / adjustableRange / exceptionCriterion+evidence
  draftPreservation / reauthenticationReturnIntent

ConformingAlternateRevision
  sourcePage+state+process / alternateRef / locale / information+function parity digests
  freshnessRevision / reachableMechanismEvidence / nonInterferenceEvidence

AccessibleOutputProfileRevision
  outputKind / format+version / locale / contentLanguage / semantic+reading-order+table rules
  alternative+metadata+extraction rules / zoomReflowPolicy / blockingClientMatrix
  accessibleFallbackRef / authenticatedRetrievalJourneyRef / expiryRecoveryRef
```

术语固定：`contentLanguageTag` 表示内容发音/语言，`formattingLocale` 表示格式，`jurisdiction/region` 表示法律/
商业范围，`calendar` 与 `timeZoneId` 表示时间语义；禁止从 locale 推断 jurisdiction、currency 或 timezone。

- Locale tag 使用 BCP 47；`LocaleMatchingRevision` 冻结 IANA 与 CLDR alias 的 pipeline 顺序、RFC 4647 lookup、
  Accept-Language parser/q tie/input order/wildcard/default、`u-` extension/private-use comparison/allowlist、等价 URL
  redirect 和 CDN `Vary/cache-key`。canonicalization 只用于匹配与稳定 identity，保留 raw input 审计；range 与候选
  同步 canonicalize，最终返回 Site allowlist 内的 selected supported tag，不把内部截断值冒充用户原 tag。format
  使用冻结的 CLDR/ICU/
  Intl capability digest，不维护自制月份、复数和货币规则。
- fallback 是有向无环图，必须终止于 Site 的 default locale；不得 fallback 到另一个 Site 的 bundle。
- URL locale、已登录 preference、Site default 和 browser hint 的优先级由 revision 固定；browser hint 只用于首次
  建议，不能覆盖显式选择。
- Credit unit 与法币分开格式化；内部 micros、ledger account 和 Provider amount 不直接暴露。
- source 文案 key 发布后语义不可静默变化；破坏性变化创建新 key/revision。
- 冻结 template 若被判定有错误法务/安全语义或钓鱼风险，可标 `revokedForDelivery`；受控 supersession 保留原
  event locale、old/new digest、reason 与审计链，尚未 provider-accepted 的 retry 使用批准修复 revision。

## 4. Functional Requirements

### 4.1 Locale selection and persistence

- 首次访问从可信 Site 支持列表选择 locale；不支持或伪造 tag 回到 Site default，不进入任意 fallback。
- Accept-Language/tag 有长度、range 数、非法 q 值与 parser budget 上限。用户显式选择保存在 Site-local preference；
  未登录 cookie 必须 host-only、Secure、SameSite、固定 Path/TTL，只作为 Site-scoped hint 而非 authority，禁止跨 Site Domain cookie。
- 登录、登出、账户恢复和 Project 切换不静默改变 locale；邮件/通知使用事件发生时冻结的 recipient locale。
- deep link 保留合法 locale 和安全 return intent；不允许 locale segment 形成 open redirect 或 cache poisoning。

### 4.2 Translation governance

- route、component、email、push、Support macro、legal notice、export manifest 都引用已发布 bundle revision。
- SSR→RSC/Flight→hydrate 全程冻结 `siteReleaseId + locale + bundleDigest + formatterRevision`；hydration 后不能
  静默换 bundle。新 revision 只在下一次 revision-bound navigation/request 生效，visible text、accessible name、
  lang/dir 与 DOM ID relationships 必须原子一致。
- build 提取静态 key；dynamic key 只能来自 typed registry。missing/unused/cross-Site key 进入 CI 和 Release report。
- pseudo-locale 覆盖长度扩张、双向文本、插值、复数和缺 key；用户内容不进入翻译 key。
- 插值按目标上下文转义；禁止用翻译 HTML 绕过 sanitizer。人名、模型名、Code、金额、时间使用 typed formatter。
- text input/search/editor 正确处理 IME composition、Unicode normalization、grapheme cluster、emoji/ZWJ、locale
  line breaking/collation 和 locale-aware decimal parsing；不得在 composition 中途提交、按 UTF-16 code unit 截断
  用户内容，或将展示格式直接作为 money/Credit authority 输入。
- normalization 按 `UnicodeInputPolicyRevision` 的 field class 执行；secret、opaque code、signed payload 与协议
  identifier 不得隐式 normalize/case-fold/locale transform，raw value 保留，search key 单独派生并版本化。不可信
  bidi control 在 Chat、Artifact、filename、citation、Support/Admin 等安全展示中 directional isolate，并提供可发现的
  logical-order 原值；不能只在 diff/log/audit 显式化。
- legal/security/commerce/recovery/trust 文案使用 exact approved `locale × jurisdiction` compatibility；缺失时禁用
  相关 Journey 或使用明确批准的替代，不走普通语言 fallback。LegalAcceptanceEvidence 冻结实际呈现 digest、
  locale、direction、timezone、document revision 和 accessible-rendering evidence。

### 4.3 Time、number and directionality

- 时间类型明确区分 `Instant / PlainDate / PlainTime / ZonedDateTime / Duration / BusinessCalendar`。Instant 用 UTC；
  civil date/time、自然日 entitlement、quiet hours 和 recurrence 不压成 instant。Zoned value 保存 IANA zone、
  calendar、offset、tzdb revision 与 `TemporalPolicyRevision` 的 DST gap/overlap disambiguation。tzdb/CLDR 升级只从
  effective cutover 重算未来 occurrence，并用 recurrence identity 防 duplicate/missed execution；历史 receipt、Legal
  acceptance、ledger display 与已结束 SLA 按事件冻结的 formatter/tzdb/calendar revision 重现，不能被当前环境改写。
  BusinessCalendarRevision 与 authoritative deadline instant 是 SLA authority。
- Subscription term、Code expiry、SLA、cooldown 等显示绝对时间、时区和必要的相对时间；DST overlap/gap 使用
  明确 offset/instant，不从模糊本地时间推断。
- 每个 route 设置 canonical `<html lang dir>`，message/part 的语言变化使用 content-language metadata/`lang`；
  未知语言不假标 Site locale。RTL 在 layout/icons/charts/code 分别处理；不可信混向插值使用 directional isolate/
  `bdi dir=auto`，Code/hash/URL/terminal 保持 logical LTR 和 logical-order copy。bidi controls 以可见/转义方式进入
  diff/log/audit，不能形成视觉欺骗。

### 4.4 Core accessibility baseline

- 所有交互有可感知 name/role/state、键盘路径、可见 focus、正确 focus order/return 和足够 target size。
- form error 与字段程序化关联，提交后 focus 到错误摘要；颜色、动画、hover、拖拽不是唯一信息/操作渠道。
- 200% text zoom、400% reflow、high contrast、reduced motion、text spacing 和 orientation 变化不丢功能。
- modal、popover、drawer、command palette、virtual list、toast 使用经验证 pattern；关闭后 focus 返回触发点或
  下一个合理工作对象。
- 每个 content-set timeout 绑定 `TimingPolicyRevision` 并选择精确 WCAG 2.2 SC 2.2.1 conformance path：turn off、
  adjust beforehand、warn-and-extend 或有证据的 real-time/essential/over-20-hours exception。warn-and-extend 至少提前
  20 秒且可简单延长至少 10 次；adjustable range 至少为默认的 10 倍。“安全”“支付”“HITL”或 Provider limitation
  本身不是例外。expiry 保存非敏感 draft 与安全 return intent。
- 认证允许 password manager、autocomplete、copy/paste；password、TOTP、recovery code 可复制/自动填充，任何
  cognitive-function test/CAPTCHA 都必须具备符合标准的替代或允许辅助机制，不能要求无辅助记忆/转录。
- 同一流程已提供的信息不得无理由重复输入；允许选择/自动填充。Legal acceptance、Redeem、Payment、export/
  delete 等法律、财务或数据后果操作在 commit 前必须可 review、correct、confirm，或具备可逆机制。
- 精确测试覆盖 320 CSS px（vertical content）/256 CSS px（horizontal writing 的对应维度）reflow、24×24 CSS px
  target 或标准例外、focus not obscured、contrast/non-text contrast 和 WCAG text-spacing 参数；“400%”不替代 SC。

### 4.5 Chat、streaming and HITL

- streaming region 不逐 token `aria-live`；以节流的阶段/段落更新，终态只播报一次，用户可关闭自动 announce。
- new message、tool call、HITL、error、reconnect、branch switch 不抢走 composer focus；提供“跳到最新内容”、
  “跳到待处理请求”和 unread count。
- Stop/Cancel/Retry/Continue 的 label、disabled state 和费用影响可被 AT 读取；thinking/queued/recovering 不只靠
  spinner。
- code、diff、citation、artifact、table 有语义化读法、复制/下载和纯文本替代；syntax color 不承载唯一含义。
- message/part 使用 stable logical ID；branch/reconnect 不用新 DOM identity 冒充同一消息。virtualized history 不卸载
  DOM focus 所在对象；因 AT virtual cursor 无法可靠跟踪时，提供可发现、完整、线性、非虚拟化 accessible transcript，
  包含全部 message/part、speaker、tool/HITL state、error、citation、费用语义和 recovery action，不以摘要代替。
  transcript/主视图切换保留 logical message anchor 与 reading position；关闭自动 announce 后仍可查询。
- HITL deadline、extend、expire、reauth 与 DOM replacement 有固定 focus-return/recovery；触发点消失时 focus 到
  新状态标题/下一安全对象，绝不落到 body。

### 4.6 Studio and media controls

- waveform/timeline/canvas/mask/storyboard 提供键盘操作、数值输入、列表/表格替代和可撤销历史。
- Music/Video player 支持键盘、速度/音量、时间位置和状态播报。每个媒体按 `MediaAccessibilityRevision.mediaClass`
  逐项决定适用 SC：prerecorded audio-only 提供 time-based alternative；prerecorded video-only 提供 time-based
  alternative 或等价 audio track；prerecorded synchronized media 提供 captions、满足 A 级 1.2.3，并为全部预录
  video content 提供 AA 级 audio description；live synchronized media 提供 live captions。media-alternative-for-text
  只能按具体 criterion 和 clearly-labelled evidence 使用，不能作为通用豁免。
- `MediaAccessibilityRevision` 冻结 content language、caption/transcript/audio-description/text alternative、quality
  review、例外依据和 publishability。transcript 不能替代 SC 1.2.5 audio description；缺任一适用 A/AA alternative
  时 preview 只进入 remediation，export/share/publish/enabled certification 阻断。自动 caption/transcript/
  description 未经 content-language 和内容质量人工审核不能算满足 criterion。
- image mask/selection 提供坐标/尺寸/对象列表等非 pointer 路径；无法提供等价体验的专业 Surface 不得进入
  enabled inventory。
- Image/Chart/Artifact 的 text alternative 记录状态、content-language、provenance、quality review 和用户编辑；
  “生成中/待审核”不是已完成 alternative，装饰性内容需明确空替代，信息图需等价数据/描述。

## 5. User-visible States and Recovery

| State | Meaning | Recovery |
|---|---|---|
| locale_loading | 已知 Site/locale，bundle 尚在加载 | 使用已验证 cached revision 或 wait；不跨 Site fallback |
| locale_unavailable | 请求语言未发布 | 切到公开 default 并解释；允许选择支持语言 |
| translation_incomplete | preview/candidate 缺 key | operator 修复；production compile hard fail |
| additional_input_required | 流程需要额外输入 | 同一业务状态机提供等价交互、focus 到精确要求、保留 draft；不要求披露诊断 |
| session_timeout_warning | 操作即将超时 | extend、save draft 或安全重新认证 |

## 6. Admin、Support and Release

- Translation Console 只管理 bundle workflow，不直接编辑 active SiteRelease；发布新 immutable revision。
- A11y Issue 关联 Site/Profile/Surface/Journey/component/browser/AT/evidence。任何适用 A/AA criterion failure 都是
  Release blocker，不允许按 internal Medium/Low 或 accepted risk 放行；severity 只决定修复排序。
- Support 能记录 assistive technology 和阻塞步骤，但不要求用户披露诊断；提供可访问替代渠道。
- Release candidate 自动运行 key completeness、pseudo-locale、lint/axe 类扫描、visual overflow/RTL；人工执行
  每个 full page、state、complete process 的 keyboard、screen reader、zoom/reflow、media alternative 和 P0
  Journey matrix。Evidence 绑定 SiteRelease×locale×viewport×state×process×technology/accessibility support。
- Browser/AT matrix 冻结 blocking/advisory cell selection、desktop/mobile/browser/OS/AT/input modality、version window、
  real-device requirement、evidence TTL 和重大 browser/AT/framework release trigger。共享 primitive evidence 不替代
  每个独立 Site app/Next/React 版本的最终证据。blocking baseline 在 candidate testing 前由 Accessibility Lead、QA、
  Site Product owner 按目标 locale/user/device/support promise 冻结；发现失败后不得 reclassify、缩 scope 或改 denominator
  放行。变更需新 revision、影响分析和重认证，且 accessibility-supported evidence 按 content language 验证。
- baseline 至少评估 keyboard、desktop/mobile screen reader、magnification/high-contrast、speech input 与 switch/
  alternative input；可按市场设 blocking/advisory，但不得因无自动化能力排除。
- HTML email 必须有语义/reading order/alt/link purpose/lang/dir/contrast、plain-text MIME、zoom/reflow 和 blocking
  client evidence；每种 PDF/HTML/CSV/JSON/media bundle 使用 `AccessibleOutputProfileRevision` 定义 format-specific
  semantic、reading order、table/header、alternative、metadata/title、extraction、retrieval/expiry recovery。格式无法表达
  等价语义时提供同样可发现、同样受保护、信息和功能等价的 accessible format。深链目标保持 Site/locale/a11y continuity。
- conforming alternate 必须与 source 达到相同 level、locale、信息/功能与更新及时性，通过 accessibility-supported
  mechanism 直接可达且主版本不干扰；`ConformingAlternateRevision` 任一 parity/freshness/reachability/non-interference
  evidence 不成立时不得用于 conformance。
- SiteRelease compile 检查共享 i18n/a11y package minimum、baseline expiry、approved variance 和独立 app evidence；
  template/codemod upgrade 会使受影响 evidence 失效并需重跑。
- `SiteAccessibilityCertificationInstance` 绑定 SiteReleaseId、Web build/SSR runtime digest、RSC-client manifest、shared
  package revisions、TranslationBundleRevision、remote config/enabled Surface digest、third-party widget、CDN/service-
  worker cache policy、BrowserATMatrixRevision、evidence set 与 expiresAt。任一输入变化、evidence expiry 或 production
  A/AA regression 都使 certification 失效；active Site 必须 rollback、disable Surface 或阻断新流量进入 remediation。
- shared primitive 改动需运行所有受影响 Site contract suite；每个独立 Site Project 仍生成自己的证据。

## 7. Edge Cases

| Scenario | Expected behavior |
|---|---|
| Site A 缺 key、Site B 有同名 key | Site A compile fail；绝不读取 Site B bundle |
| 邮件事件后用户切换 locale | 已入队通知保持冻结 revision；后续事件使用新 preference |
| fallback graph cycle | publish/compile 拒绝 |
| DST 导致本地时间不存在或重复 | 以 instant+offset 显示并解释，不双执行、不丢 SLA |
| streaming reconnect 重放 chunk | UI 去重，live region 不重复播报历史 token |
| modal 中 AuthSession 过期 | 保存安全 draft，关闭/重新认证后返回 intent 和合理 focus |
| canvas 仅支持鼠标 | Surface certification fail，不能通过“建议使用鼠标”豁免 |
| 自动扫描通过、键盘流程失败 | Release No-Go |

## 8. Acceptance Criteria

### AC-UX-01 — Cross-Site locale isolation

```gherkin
Given Site A and Site B publish different bundles with the same key
When Site A requests an unsupported locale or misses the key
Then it uses only Site A's declared fallback or fails candidate compilation
And no Site B text, brand, legal revision or cache entry is returned
```

### AC-UX-02 — Consistent frozen notification locale

```gherkin
Given a security event freezes Site A locale and template revisions
When the user changes locale before delivery retry
Then every retry renders the same approved event revision
And later events use the newly selected locale
```

### AC-UX-03 — Keyboard Core journey

```gherkin
Given a keyboard-only user starts registration, Redeem, Chat and Support
When every P0 action, error and recovery branch is exercised
Then the journey completes without pointer input
And focus order, return, error association and status announcements remain correct
```

### AC-UX-04 — Streaming announcement

```gherkin
Given an assistant response streams many tokens and reconnects once
When a screen reader observes the conversation
Then historical chunks are not announced again and tokens are not individually announced
And queued, recovering, completed and error transitions are announced once with available actions
```

### AC-UX-05 — Zoom、reflow and RTL

```gherkin
Given a supported RTL locale at required zoom and reflow settings
When a user completes account, Chat and enabled Studio journeys
Then content and controls do not clip, overlap or require two-dimensional scrolling except allowed content
And mixed-direction Code, URLs and identifiers remain understandable and copyable
```

### AC-UX-06 — Media equivalent operation

```gherkin
Given an enabled Music, Video or Image Studio uses waveform, timeline or canvas interaction
When a non-pointer user edits the same product parameters
Then an equivalent keyboard and structured-control path exists
And the resulting OperationSpec is semantically identical
And preview, export or share is blocked until every applicable caption, transcript, audio-description and text-alternative requirement is satisfied in the content language
```

### AC-UX-07 — Full-page and complete-process conformance

```gherkin
Given an enabled Surface contains P0 and non-P0 components across responsive variants and third-party content
When SiteRelease accessibility certification runs
Then every full page, user-visible state and complete process satisfies every applicable WCAG 2.2 A and AA criterion
And any failed criterion blocks release regardless of internal defect severity
```

### AC-UX-08 — Accessible authentication

```gherkin
Given a user uses a password manager, copy/paste, autocomplete or assistive technology
When they register, complete MFA, recover the account or reauthenticate
Then no step requires unaided memorization or transcription
And every cognitive-function test has a conforming alternative or permitted assistance mechanism
```

### AC-UX-09 — Legal、financial and data error prevention

```gherkin
Given a user will accept legal terms, redeem value, pay, export or delete data
When the consequential action is prepared
Then inputs and consequences are reviewable and correctable before commit or the operation is safely reversible
And evidence freezes the exact accessible localized rendering that was confirmed
```

### AC-UX-10 — SSR and hydration revision atomicity

```gherkin
Given a request starts on bundle revision N while N+1 is published
When Next renders and React hydrates
Then route, html lang/dir, visible text, accessible names and ID relationships all use N
And N+1 applies only on a later revision-bound navigation or request
```

### AC-UX-11 — Locale canonicalization and cache isolation

```gherkin
Given equivalent, deprecated, unsupported, private-use and weighted language ranges
When locale negotiation and CDN lookup occur
Then one frozen BCP 47 canonicalization and RFC 4647 policy selects only the Site allowlist
And cache identity includes Site, Release, locale and bundle digest
```

### AC-UX-12 — Temporal semantics under tzdb change

```gherkin
Given an instant, civil date and recurring local schedule cross a DST rule update
When tzdb is upgraded
Then each preserves its declared temporal type
And future schedule changes are recomputed, versioned and communicated without duplicate or missed execution
```

### AC-UX-13 — Virtualized Chat and HITL expiry

```gherkin
Given a screen-reader user reviews an older virtualized message while a HITL request streams and later expires
When history mounts or unmounts and the request changes state
Then reading position and composer focus remain stable
And pending request, deadline, extension, expiry and recovery are available on demand exactly once
```

### AC-UX-14 — Accessible notification and export

```gherkin
Given a frozen mandatory notification and export are rendered
When they are opened in blocking client/AT cells
Then HTML and plain text reading order, language, direction, link purpose, alternatives and semantic export structure are usable
And deep links preserve the frozen Site locale without cross-Site or jurisdictional fallback
```

### AC-UX-15 — Focus、target and reflow specifics

```gherkin
Given sticky Chat controls, toasts and modal content at required reflow and target-size settings
When keyboard focus moves through every control
Then author content never fully obscures focus
And target sizing/spacing, contrast, non-text contrast and text-spacing satisfy every applicable A/AA criterion
```

### AC-UX-16 — Media criterion mapping

```gherkin
Given prerecorded synchronized media contains essential visual information and a transcript but no conforming audio description
When AA certification runs
Then the transcript does not satisfy SC 1.2.5
And export, share, publish and SiteRelease certification are blocked

Given live synchronized media exposes live audio on an enabled Surface
When the Surface is certified
Then conforming live captions are available or the Surface is not enableable
```

### AC-UX-17 — Time-limit conformance path

```gherkin
Given a content-set authentication, payment or HITL time limit
When TimingPolicyRevision is certified
Then it satisfies one exact SC 2.2.1 conformance path
And a security, payment or Provider label alone cannot authorize an exception
And expiration preserves non-sensitive input and a safe return intent
```

### AC-UX-18 — Complete accessible Chat transcript

```gherkin
Given a screen-reader user opens the accessible transcript
When visual history virtualizes, reconnects or switches branch
Then every message, part, speaker, tool/HITL state, error, citation, fee and recovery action remains in logical order
And no focused or selected logical object disappears
And returning to the main view restores the same logical anchor
```

### AC-UX-19 — Unicode field semantics and bidi safety

```gherkin
Given a password, opaque Code, signed payload, filename and untrusted bidi-controlled label
When input, matching, display and copy occur
Then secret and opaque protocol values are not implicitly normalized or case-folded
And safety-sensitive UI isolates direction while exposing an unambiguous logical-order representation
```

### AC-UX-20 — Historical time reproduction

```gherkin
Given a historical receipt and a future recurrence were created under tzdb and BusinessCalendar revision N
When revision N+1 changes DST or holidays
Then the historical receipt renders with N while only future cutover occurrences are recomputed
And occurrence identity and authoritative deadlines prevent duplicate, missed or silently shifted obligations
```

### AC-UX-21 — Certification binds deployable artifact

```gherkin
Given a certified Site changes Web build, SSR/RSC assets, remote flags, enabled Surface, widget or cache policy
When the changed artifact reaches release evaluation or production regression detection
Then the prior CertificationInstance is invalid
And the Site rolls back, disables the Surface or blocks new traffic until recertified
```

### AC-UX-22 — Conforming alternate parity

```gherkin
Given a nonconforming primary version references a conforming alternate
When SiteRelease evaluates that claim
Then locale, conformance level, information, functions, freshness, direct reachability and non-interference all pass
And any missing parity evidence blocks use of the alternate for conformance
```

## 9. Dependencies、Risks and Milestones

| Risk/Dependency | Mitigation |
|---|---|
| 每个 Site Project 翻译漂移 | signed bundle/package revision、typed key extraction、candidate compile |
| 动态 Chat UI 过度播报 | stable live-region policy、throttled phases、manual AT tests |
| 专业控件只面向 pointer | structured alternative controls、Surface-specific certification |
| 法务文案 fallback 错误 | LegalRevision/locale compatibility hard gate |
| 自动工具产生虚假信心 | manual P0 matrix 与真实 AT/browser evidence mandatory |
| 版本矩阵快速过期 | evidence validity、quarterly review、critical browser/AT release trigger |

Wave 1 冻结 locale/a11y contracts 与核心 Web primitives；每个后续 PRD 附 surface-specific interaction annex；
Wave 8/9 对每个 enabled Site/Profile 生成 matrix evidence。标准依据为 W3C WCAG 2.2、WAI-ARIA Authoring
Practices、BCP 47 与 Unicode CLDR；实现前由 architecture child Spec 冻结 package、schema、CI 和 test harness。

本文批准不授权实现，也不修改 GA runtime。
