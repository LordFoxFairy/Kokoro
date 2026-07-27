---
artifact: product-requirements-document
prdId: PRD-17
version: "1.0"
created: 2026-07-25
status: internal-review-active
scope: model-option-eligibility-control-plane-provider-operations-evaluation-promotion-drift-recovery
accountableProductRole: Model Platform Product Lead
mandatoryCosigners: [Site Fleet, Chat, Studio, Model Platform, GA, Job, Usage Rating, Finance, Trust, Security, SRE, Support, QA]
engineeringOwner: team:model-platform-engineering
qaOwner: team:model-platform-quality
supportOperationsOwner: team:model-gateway-operations
namedOwnerAssignmentStatus: assigned-team-responsibility-ids
implementationAuthorized: false
gaRuntimeSemanticChangeAuthorized: false
---

# PRD-17：Model Option、Control Plane 与 Provider Operations

## 1. Overview

### 1.1 Problem Statement

Kokoro 已明确“底层 Model Catalog 全平台一份、各 Site/Plan/Surface 组合发布、Gateway 选择真实
Deployment、LiteLLM 只是可替换 adapter”的目标架构，但仍缺少一份完整产品合同，把用户选择模型的体验与
运营人员管理模型供应链的流程真正闭环。

若只实现一个模型下拉框和若干后台配置表，会产生以下生产问题：

1. 用户看到的 Option 与 SiteRelease、Plan、Surface 或附件能力不一致，提交后才发现不可用，甚至被静默换成
   另一个模型。
2. 默认 Option 在发布、回滚或故障时漂移，历史会话无法解释当时使用了什么产品选择。
3. Provider 故障后系统为了“可用性”跨模型无感续写，导致回答语义、工具调用、费用和安全属性不可解释。
4. ModelDefinition、Deployment、Profile、Pool、Route、Bundle、Option 与 Assignment 被当成一张可编辑配置表，
   无法证明依赖完整性、评测结果、审批、回滚目标和影响范围。
5. LiteLLM YAML、Gateway bundle 和 Control Plane revision 发生漂移，或 adapter/provider certification 过期，仍继续
   接受生产流量。
6. Support 只能看到 Provider 错误或“模型不可用”，无法回答是否已提交、是否会收费、是否可以重试、何时恢复。

### 1.2 Solution Summary

交付两条相互关联但权责分离的产品闭环：

- **用户 ModelOption 闭环**：用户只看到 SiteRelease 发布且当前 Site、Plan、Surface、输入能力和政策均允许的
  `ModelOptionRevision`；未显式选择时使用已发布 default；显式选择失效时 fail closed、保留输入并要求重新确认，
  不静默回 default；允许的健康 failover 仅发生在同一已授权 Option/Route 内，并提供产品层 disclosure。
- **Model Operations 闭环**：运营人员通过 typed Control Plane workflow 管理 Catalog、Deployment、Profile、Pool、
  Route、Bundle、Option、Assignment、评测、认证、shadow、canary、promotion、rollback、LiteLLM config、drift、
  certificate expiry、incident 和 reconciliation；Admin 只是 façade，Model Control 与 Gateway 继续拥有各自真源。

所有发布对象版本化且发布后不可变。所有 active 组合都可从用户 Option 追踪到 SiteRelease、Plan grant、Effective
Bundle、Profile、Pool、Route、Deployment、ProviderCertification、EvaluationReport、GatewayConfig 与回滚目标。
本文补充产品旅程、状态、恢复、运营、指标和验收，不重新设计底层模型技术架构。

### 1.3 Target Users

- Chat/Studio 用户：选择可理解的速度、质量、能力与费用档位，而不需要理解 Provider 或 Deployment。
- Site Product Owner：按 Site 产品定位发布默认项和可选项，且知道每个选择的能力、成本、风险和依赖。
- Model Product/ML Evaluation：管理产品组合、评测基线、升级影响与 promotion 证据。
- Model Operator/SRE：处理 Provider、Deployment、容量、健康、LiteLLM、证书和配置漂移。
- Finance/Usage Rating：追踪 Provider cost、客户 rating 边界和异常成本，但不在 Gateway 中定价。
- Trust/Security：控制数据地域、训练/保留政策、安全能力、secret 与紧急 deny。
- Support：从用户可见 Option 追踪原始 Run/Job/Attempt 状态并给出安全恢复动作。

### 1.4 User Stories

| ID | User story | Priority |
|---|---|---|
| US-MOD-01 | 作为用户，我只看到当前 Site、Plan 与 Surface 真正可用的模型选项及其能力差异 | P0 |
| US-MOD-02 | 作为用户，我未选择模型时能获得稳定的发布默认项，且历史运行保留当时的 Option 快照 | P0 |
| US-MOD-03 | 作为用户，我选择的 Option 在提交前失效时不会被静默替换，并能保留输入后重新选择 | P0 |
| US-MOD-04 | 作为用户，我能理解一次失败是否发生了同等部署 failover、是否可能收费和是否可安全重试 | P0 |
| US-MOD-05 | 作为 Site Product Owner，我能发布某 Surface 的完整默认/可见/隐藏 role 组合并在上线前看到影响 | P0 |
| US-MOD-06 | 作为 Model Operator，我能以受控生命周期管理 catalog、deployment、profile、pool、route、bundle 与 assignment | P0 |
| US-MOD-07 | 作为 Evaluation Owner，我能以可复现证据推动 candidate 经 certification、shadow、canary 和 promotion | P0 |
| US-MOD-08 | 作为 SRE，我能发现 LiteLLM/config/provider drift、证书过期与容量故障，并安全 restrict、rollback 或 reconcile | P0 |
| US-MOD-09 | 作为 Support，我能在 Site scope 内解释 unavailable、fallback、unknown、cost_pending 与恢复时限 | P0 |
| US-MOD-10 | 作为 Studio 用户，我能同时获得专业 generation Option 与隐藏主模型/安全模型的完整组合 | P0 if-enabled |

## 2. Goals、Success Metrics 与 Non-Goals

### 2.1 Goals

1. ModelOption 的发现、默认、选择、冻结、失效、重新确认、运行、历史解释和恢复形成完整用户闭环。
2. Site、Plan、Surface、Operation/Input、地域、Trust 与实时 restriction 在 effect 前全部 fail closed。
3. 每个 active Option/Assignment 有可追踪的评测、认证、发布、canary、回滚、Support 与 SRE 证据。
4. Model Control 的产品对象、Gateway 的 runtime attempt 与 LiteLLM 的 transport config 不形成重复 authority。
5. Provider 故障、unknown outcome、证书过期、配置漂移和 Control Plane outage 都有明确状态、owner、SLA 与恢复动作。
6. Chat、Image、Music 与 Video 能复用同一 Catalog，同时拥有各自完整的 role composition。

### 2.2 Success Metrics

所有指标必须引用版本化 `ProductMetricRevision`，固定 numerator、denominator、window、exclusion、dimensions、owner、
target、alert 与 mandatory action。至少按 Site、Profile、Surface、Option revision、role、Deployment、adapter、region、
Plan、release、request class 和 terminal class切分；不得用全局平均掩盖单 Site 或单 Provider 故障。

| Metric | Baseline | Target / guardrail | Evidence and action |
|---|---:|---:|---|
| 用户可见但 Admission 不可用的 Option | 未统一 | < 0.1%；权限/发布错误为 0 | option availability funnel；发布错误阻断/回滚 |
| 显式 Option 被静默替换为 default/其他 Option | 当前风险待盘点 | 0 | submit/authorization property test；任一命中 P0 |
| Effective Bundle 缺 required hidden/generation role | 未统一 | 0 | SiteRelease compile gate |
| 未认证/过期 certification 的 Deployment 获得新 Attempt | 未统一 | 0 | Gateway effect-point audit；任一命中 P0 |
| unknown Provider outcome 触发 retry/fallback | 未统一 | 0 | Attempt ledger invariant |
| fallback disclosure 覆盖 | 未统一 | 100% eligible user-visible outcomes | Run/Job safe explanation projection |
| Option selection → Attempt route explainability | 未统一 | 100% | traceability query/Support UAT |
| LiteLLM/GatewayConfig unauthorized drift | 未统一 | 0 active；发现 p99 ≤ 60s | signed digest monitor + automatic quarantine |
| certification expiry lead time alert | 未统一 | 100% at 30/14/7/1 day windows | certificate dashboard/page |
| expired certification 导致非计划中断 | 未统一 | 0 | renewal SLO + fail-closed drill |
| canary automatic rollback detection | 未统一 | p95 ≤ 5m for frozen critical guardrail | promotion timeline and receipt |
| route/config rollback success | 未统一 | p95 ≤ 10m；0 unknown active epoch | rollback game day |
| Model Attempt usage/cost fact completeness | 未统一 | 100% terminal/reconciled Attempt | Usage outbox audit |
| Model P0 Support Case 可解释率 | 未统一 | 100% 有 owner/state/next action/deadline | case sampling |

### 2.3 Non-Goals

- 不向用户展示或允许选择 Provider、ProviderAccount、region、Deployment、LiteLLM alias 或 raw model ID。
- 不在本文定义客户售价、套餐价格、Credit journal 或结算算法；Plan grant 与 RatingPolicy 由 Commerce/Usage owner 管理。
- 不让 Session、Web、GA、Job 或 LiteLLM 拥有 Catalog、business fallback 或 route authority。
- 不用健康探测直接改写 Deployment lifecycle，不用 LiteLLM UI/YAML直接发布生产配置。
- 不承诺跨 ModelDefinition 的无感续写，也不在 V1 引入 hedging/speculative parallel attempts。
- 不把 Evaluation/Benchmark 结果当成 SiteRelease 自动上线授权；promotion 与 Release certification 仍是独立门。
- 不修改 GA graph、assembly、prompt、tool、skills/MCP、checkpoint、effect journal、HITL、cancel、Handoff、namespace、
  runEpoch、terminal 或 event ordering semantics。

## 3. Product Objects and Authority

### 3.1 User-facing objects

```text
ModelOptionRevision
  optionId / revision / localizedLabel+description refs
  capabilitySummary / latencyTier / qualityTier / costBandRef
  inputCompatibilitySummary / limitationDisclosureRefs
  roleOverrideRefs / defaultEligibility / selectorVisibility
  lifecycle / validFrom / validUntil

ModelOptionAvailability
  siteReleaseRef / surfaceRevisionRef / planModelGrantRef
  optionRevisionRef / operationOrInputClass
  state / safeReasonCode / observedAt / validUntil
  allowedRecoveryActions / disclosureRevisionRef

ModelSelectionSnapshot
  source = published_default | explicit_user_selection
  optionRevisionRef / optionLabelSnapshotRef
  siteReleaseRef / surfaceRevisionRef / planGrantRevisionRef
  selectedAt / acceptedCommandReceiptRef
```

`ModelOptionAvailability` 是面向展示的可缓存投影，不是授权；提交时 Platform Admission 必须依据可信 SiteContext、
当前 release/plan/restriction/input重新验证。`ModelSelectionSnapshot` 只记录产品选择，不包含 Provider/Deployment。

### 3.2 Control-plane objects

| Object | Product meaning | Authority |
|---|---|---|
| ModelDefinition | 全平台唯一逻辑模型与能力身份 | Model Control |
| ModelDeployment | 确切 Provider account/environment/region/upstream version/adapter | Model Control lifecycle；Gateway runtime health |
| ModelProfileRevision | 一个 role 的能力、参数和 route contract | Model Control |
| ModelPoolRevision | 允许候选集合，不代表 fallback 等价 | Model Control |
| FallbackEquivalenceRevision | 在限定 role/request class 下允许的等价关系和证据 | Model Control |
| RoutePolicyRevision | 候选过滤、排序、fallback、capacity 与 disclosure policy | Model Control |
| ModelBundleRevision | 完整 `roleKey → Profile` 组合 | Model Control |
| ModelOptionRevision | 用户可见的受限 role override | Model Control/Product |
| SurfaceModelAssignmentRevision | Site/Surface 的 default、visible、hidden、rollout 和 expiry | Model Control + Site Product |
| EffectiveModelBundleRevision | SiteRelease compile 后的唯一完整组合 | SiteRelease compiler output |
| PlanModelGrantRevision | Entitlement 对 Option/limits 的授权 | Commerce/Entitlement |
| ProviderCertification | Deployment/adapter/protocol能力认证 | Model Evaluation/QA/Security |
| ModelPromotionDecision | candidate 到指定环境/流量范围的签名决定 | Model Governance |
| GatewayConfigRevision | Gateway/LiteLLM 可部署配置的签名产物 | Model Control compiler |

### 3.3 Runtime and operations facts

| Object | Meaning | Authority |
|---|---|---|
| ModelExecutionAuthorization | execution root 的 server-side bounded model authorization | Platform Admission/Gateway authorization store |
| ModelInvocation/ModelAttempt | logical call 与真实 Provider IO | Model Gateway |
| ResolutionRecord | 某 Attempt 的选择、排除和 fallback 解释 | Model Gateway |
| ProviderOutcomeFact | submitted/unknown/terminal/reconciled事实 | Model Gateway reducer |
| AttemptUsageFact/ProviderCostFact | canonical usage输入与 Provider成本证据 | Model Gateway；Usage Rating消费 |
| DeploymentHealthObservation | synthetic/traffic/provider/capacity观测 | Gateway/SRE；非 lifecycle authority |
| DriftObservation | expected与observed digest/version差异 | Configuration/Certification monitor |
| OperatorCommandReceipt | 运营命令的领域 authoritative receipt | Model Control/Gateway owner |

### 3.4 Boundary invariants

```text
Site Web/BFF → Session/Studio API → Platform Admission
Platform Admission → opaque modelAuthorizationHandle → GA/Job
GA/Job → Model Gateway → Direct Adapter or LiteLLM Adapter → Provider
Model Control → signed compiled bundles/config → Admission/Gateway
Gateway Attempt facts → Usage Rating / Job or GA projection / Support
Admin Console → typed Model Control or Gateway commands only
```

- Browser/Session 只传 ModelOption revision，不传 Deployment 或可读 authorization claims。
- GA 只透传 opaque `modelAuthorizationHandle` 与稳定 logical call identity，不读取 Site、Plan、Billing 或 route。
- LiteLLM 一个 alias 只绑定一个 Kokoro Deployment，不拥有跨 Deployment fallback、预算或 canonical usage。
- Model Control 不执行 Provider IO；Gateway 不发布 Product/Plan/Option/Assignment。
- Site-specific 差异存在于 revision/assignment/release，不进入共享后端的 `if (siteId)` 分支。

## 4. Canonical User Journeys

### 4.1 MOD-01 — Discover eligible ModelOptions

1. 用户进入 Chat 或已启用 Studio，Web 从受信 bootstrap/query 获取 `ModelOptionAvailability` 列表。
2. 列表只包含当前 SiteRelease、Surface、Plan、region/age/policy 与基础输入能力允许的 published revision。
3. 每项显示稳定产品名称、能力差异、相对速度/质量、支持输入、上下文/时长限制、费用档位和重要限制。
4. 不显示 Provider、Deployment、region、alias、健康分数或内部 role。
5. Site 未开放 selector 时不渲染空控件；仍显示必要的默认能力/费用 disclosure。
6. availability stale 时显示最后更新时间并在 submit 重验，不能据缓存承诺一定可用。

终态：`options_presented | hidden_default_presented | no_eligible_option | availability_unknown`。

### 4.2 MOD-02 — Published default

- 每个 enabled Surface 必须在 SiteRelease compile 得到一个完整 default Effective Bundle；不是运行时 global fallback。
- 用户未显式选择时，receipt 记录 `published_default + exact Option revision`。
- default 可对 selector 隐藏，但其 label/capability/cost disclosure、Plan eligibility、所有 required roles、认证与
  rollback evidence必须完整。
- default revision 改变只影响新提交；已接受 Run/Job 保持原 authorization/selection snapshot。
- default 被紧急撤销且没有另一个已发布、已认证 default 时，Surface 新提交进入 unavailable，不允许临场使用全局模型。

### 4.3 MOD-03 — Explicit selection and submission

1. 用户选择 Option 后，composer/operation draft 保存 option ref 与当时 label snapshot。
2. 提交 receipt 将 exact Option revision、draft/operation digest 和 command identity 绑定。
3. Admission 重新检查 SiteRelease、Surface、Plan grant、input/modality/context/parameter、region、Trust、restriction、
   validity 和 budget。
4. 通过后生成完整 Effective Bundle 与 opaque authorization；Session/Studio 不看到 route details。
5. 同 key/同 digest 返回同 receipt；更换 Option 会改变 digest，不能复用旧幂等身份。

### 4.4 MOD-04 — Unavailable and reconfirmation

显式选择在提交前变为 disabled、expired、unentitled、incompatible、restricted 或无任何 eligible route 时：

- 不创建 executable Run/Job 或 Provider Attempt；保留 prompt、附件、参数和 draft。
- 展示稳定 safe reason category、最后校验时间、影响范围与允许动作。
- 可提供当前 eligible alternatives，但必须由用户明确选择并重新确认；不能自动切 default。
- 若价格档位、能力、数据地域、内容保留、输入兼容或输出权利发生 materially different change，即使 Option label
  不变，也必须生成新 revision 并要求用户重新确认。
- 仅瞬时容量/健康不足且没有 Provider effect 时，可在原 Option/Route policy 内等待或使用已认证等价 Deployment；
  这不改变产品选择，但要按 disclosure policy说明。

安全 reason categories：

```text
option_not_in_release | plan_not_eligible | option_expired | option_disabled |
input_incompatible | region_or_policy_restricted | temporarily_unavailable |
capacity_exhausted | certification_invalid | configuration_unavailable
```

### 4.5 MOD-05 — Fallback and disclosure

- fallback 只在 Gateway 已冻结 RoutePolicy 与 FallbackEquivalence 内发生。
- 同 ModelDefinition 的等价 Deployment failover可保持 Option；跨 Definition 只在专门评测和产品 disclosure批准时允许。
- Provider effect 前且原 Attempt `definitely_not_submitted` 才可创建下一个 Attempt。
- `submission_unknown`、outcome unknown、已有可见 token、tool call/effect、Artifact 或 partial candidate 时禁止无感 fallback。
- 用户正常成功时无需暴露供应商，但 history/cost/support projection记录“在已批准可用性路径内完成”的 safe
  explanation；若 fallback 对延迟、能力、数据政策、费用档位或结果一致性有可感知影响，必须在结果旁明确披露。
- 无法保持已承诺产品语义时，以 partial/failed/unknown 收口；Retry/Regenerate 是用户明确的新 Run/Job。

### 4.6 MOD-06 — Historical explanation

历史 Run/Job 显示原 Option label snapshot、selection source、能力/费用档位、执行状态、fallback disclosure、cost
state 和 Support ref。当前 Option 已 retired 不改变历史 label，不重新解析为新 revision。普通用户看不到 Deployment，
Support 在授权范围内可从 Option/authorization/attempt refs追踪 ResolutionRecord 和 certification。

### 4.7 MOD-07 — Multi-role Studio composition

- Image/Music/Video 每个 enabled Operation 至少解析 `*.assistant` 与 `*.generation`，并按 OperationSpec补全 safety、
  lyrics/storyboard/upscale 等明确 role。
- 用户 generation Option 只能覆盖其声明的 generation role；隐藏 orchestrator/main/safety role 从 Assignment/Agent
  manifest补齐，客户端不可覆盖。
- 缺任一 required role、Plan grant、evaluation、ProviderCertification 或 usage dimension 时 SiteRelease compile失败。
- assistant 与 generation 分别产生 Invocation/Attempt/Usage fact，不把 token、图片、音频秒或视频秒混为一次 usage。

## 5. Model Operations Journeys

### 5.1 MOP-01 — Register catalog and deployment candidate

1. Operator 创建不可变 ModelDefinition revision，声明 vendor/family/modalities/context/parameter taxonomy。
2. 注册 ProviderAccount 只保存 Secret Manager ref、environment、region、data/training/retention policy与 owner。
3. 创建 Deployment candidate，绑定 exact upstream version、account、region、adapter、protocol/mapping revisions。
4. 系统校验别名不可漂移、一个 deployment只归一个 definition、secret/capability/cost/region metadata完整。
5. candidate 只能进入 evaluation，不可直接进入 active Pool 或 Site assignment。

### 5.2 MOP-02 — Compose profile, pool and route

- Profile 定义 role所需 modality、tool/stream/reasoning/structured output、parameter envelope、SLO与route ref。
- Pool 只列候选，不隐含等价；跨 Definition fallback 必须引用 FallbackEquivalence evidence。
- RoutePolicy 明确过滤顺序、deterministic排序、pre-effect retry、capacity、circuit、unknown、disclosure和deny epoch。
- dry-run 必须展示典型 request classes 的 included/excluded candidate、safe reason、cost/capacity blast radius和差异。
- publish 使用 expectedVersion、idempotency、reason、step-up与maker-checker；active revision不可原地编辑。

### 5.3 MOP-03 — Compose bundle, option and assignment

1. Model Product 创建完整 Bundle，并以 Option 只声明有限 role override。
2. Site Product Owner 为一个 Site/Surface candidate选择 default、visible options、hidden roles、Plan grants、rollout与expiry。
3. compiler 展开 Effective Bundle，检查 required role、Operation/Agent manifest、Site/Plan/Trust/region和所有证据。
4. impact view列出受影响 SiteRelease、Surface、Plan、用户选择、active Runs/Jobs、成本、容量、Support和rollback target。
5. Assignment publish 不直接上线；只能进入 SiteRelease candidate、preview、certification与activation。

### 5.4 MOP-04 — Evaluate and certify

```text
candidate
→ offline evaluation
→ provider protocol/capability certification
→ shadow
→ canary
→ signed ModelPromotionDecision
→ assignment candidate
→ SiteRelease certification and activation
```

- EvaluationSuite冻结 dataset/Data refs、license/consent/PII、metrics、thresholds、judge、seed、parameter、parser和版本。
- suite至少覆盖质量、事实性/任务成功、tool/structured output、stream IDs/order、reasoning visibility、safety、拒答、
  multilingual、latency、capacity、usage/cost、cancel、timeout、unknown、callback与data-region行为。
- evaluation通过普通 Job/Gateway执行，产生 ProviderCostFact；不扣终端用户 Credit。
- ProviderCertification绑定 exact deployment/account/adapter/protocol/mapping/SDK/upstream observed revision、suite/report、
  environment/region、scope、签名、validity和revocation。
- Prompt、Agent、Route、Adapter、Provider version、parameter mapping或dataset policy变化按影响图使对应证据失效。

### 5.5 MOP-05 — Shadow and canary

- shadow只允许经 privacy/consent和数据政策批准的输入；结果不返回用户、不触发 tool/effect、不进入用户费用。
- canary按不可变 cohort/traffic allocation、Site/Surface/request class、start/end、budget和stop conditions执行。
- guardrail至少含 error/unknown、latency、quality/safety、tool/stream contract、usage/cost anomaly、cross-region与投诉。
- 每个 canary decision记录 sample size、confidence、exclusions、current vs candidate diff和owner。
- 触发 frozen critical guardrail自动停止新 candidate Attempt，并按 policy切回 previous certified route；已提交 Attempt
  继续 canonical reconcile，不能被“回滚”删除。

### 5.6 MOP-06 — Promote, activate and rollback

- PromotionDecision 与 SiteRelease Activation 是两层决定：前者证明 model组合可进入候选，后者授权具体 SiteRelease。
- activate 原子切换 signed bundle/config epoch；Gateway只接受已materialized且readiness通过的 revision。
- rollback目标必须在发布前固定并保持 certification有效、secret可用、schema兼容、capacity足够。
- rollback改变新 Invocation的route，不改写已授权/已提交 Attempt，不撤销 usage/cost/provenance。
- rollback后生成 authoritative receipt、affected release/traffic、in-flight disposition、notification、audit和follow-up。
- previous revision若因安全/secret revocation已不合法，禁止回滚，进入 restrict/disable与替代 candidate流程。

### 5.7 MOP-07 — LiteLLM config lifecycle and drift

```text
compile signed GatewayConfigRevision
→ prepare candidate LiteLLM config
→ validate one alias = one Deployment
→ secret/endpoint/capability smoke
→ candidate readiness
→ activate matching config epoch
→ continuously attest observed digest/image/alias map
```

- production config只能由 compiler生成，禁止直接修改 YAML、LiteLLM DB/UI或virtual key成为业务 authority。
- drift包括 image digest、config digest、alias mapping、provider model、secret revision、retry/fallback、timeout和feature flag。
- drift观察不能自动“接受当前状态”；未授权 drift 使新 candidate promotion阻断，active critical drift触发隔离/rollback/page。
- LiteLLM outage可切到已认证 direct-adapter Deployment，但必须是显式 Route/Config revision，不是单请求暗门。
- drift修复使用 `reconcile_to_declared_revision` 或签名的新 candidate；禁止从运行实例反向覆盖 Control Plane真源。

### 5.8 MOP-08 — Certification expiry and renewal

- 每个 certification显示 scope、remaining validity、renewal owner、所需 suite、依赖变化和30/14/7/1天告警。
- renewal产生新 certificate，不延长原记录；证据、adapter、provider observed revision或policy改变时重跑影响 suite。
- certificate expiry/revoke后 Gateway effect point拒绝新 Attempt；已提交 Attempt只允许完成/reconcile/cancel policy。
- 若 default route将无有效候选，Site/Product/SRE提前选择已认证替代或关闭提交；不可在到期时临场绕过。
- 过期不删除历史 Attempt/Artifact/Usage；Support仍可验证当时 certificate有效性。

### 5.9 MOP-09 — Provider incident and recovery

1. health/cost/security/unknown/capacity signal进入对应 incident/queue并关联 exact account/deployment/region。
2. managed deny/circuit只影响新 pre-effect Attempt；已提交 Provider IO进入 retrieval/reconciliation。
3. safe failover受 Route/equivalence/certification约束；无候选时向用户返回 typed unavailable。
4. Provider late success、duplicate callback、invoice correction更新同 Attempt facts，不创建新用户结果或重复收费。
5. recovery需验证 health、capacity、secret、config、certification和canary；不能因 status page恢复就直接全量放开。

## 6. Eligibility and Availability Contract

### 6.1 Eligibility intersection

用户可见和可执行 eligibility 必须是下列交集，不允许任一层“兜底放开”：

```text
SiteRelease inventory
∩ SurfaceModelAssignment revision
∩ PlanModelGrant revision
∩ Surface/Operation role requirements
∩ input/modality/context/parameter compatibility
∩ region/data/content/consent policy
∩ current restriction and model-control epochs
∩ valid certification and config
∩ runtime capacity/health before effect
```

展示 projection 可把瞬时健康作为 `available | temporarily_unavailable | availability_unknown`，但最终授权只能由
Admission/Gateway effect point完成。Plan 升降级、SiteRelease切换或 restriction更新后，旧页面缓存不能继续提交。

### 6.2 Default, unavailable and reconfirmation rules

| Situation | Required behavior |
|---|---|
| 用户从未选择 | 使用当前 SiteRelease 发布 default，并冻结 exact revision |
| 用户显式选择仍 eligible | 按同 revision Admission；不得替换 |
| 显式 Option expired/disabled/unentitled | 保留 draft，拒绝 dispatch，要求重新选择/兑换/Support |
| 同 label 发布新 revision | 不自动视为同意；material change要求 reconfirmation |
| only deployment unhealthy, certified equivalent exists | 原 Option内受控 failover；按 disclosure policy说明 |
| only eligible route materially changes promise | 阻止并要求明确选择/reconfirmation |
| no eligible default | Surface新提交 unavailable；不走global default |
| active Run/Job配置后来撤销 | 已提交effect按冻结policy收口；下一 Attempt由epoch拒绝或续授权 |

### 6.3 Material-change taxonomy

以下任一变化必须新 Option/Profile/Assignment revision并触发重新确认或新 SiteRelease：费用档位、输出权利、data
region/retention/training policy、可用 modality、最大输入/上下文/时长、tool/structured-output能力、reasoning可见性、
safety boundary、quality/latency承诺、cross-Definition fallback或用户可见限制。纯文案错字可通过相同语义的
localized bundle revision修复，但不得借此改变产品承诺。

## 7. User-visible and Operator State Catalog

### 7.1 ModelOption availability states

```text
draft | validating | published | disabled | expired | retired

availability = available | temporarily_unavailable | unavailable |
               reconfirmation_required | availability_unknown
```

| State | User meaning | Allowed actions |
|---|---|---|
| available | 当前可选择；提交仍会重验 | select / submit |
| temporarily_unavailable | 瞬时健康或容量无可用 route，尚无 effect | wait_and_refresh / select_alternative |
| unavailable | release/plan/policy/capability/certification不允许 | change_parameters / redeem / select_alternative / Support |
| reconfirmation_required | 承诺发生实质变化，需要用户明确确认 | review_change / confirm_new_revision / keep_draft |
| availability_unknown | projection或control state无法证实 | wait_and_refresh / Support；禁止猜测可用 |

### 7.2 Control-plane lifecycle states

```text
ModelDefinition/Profile/Pool/Route/Bundle/Option/Assignment:
draft → validating → ready → published → retired

Deployment:
draft → validating → certified → active ↔ degraded → disabled → retired

Promotion:
proposed → evaluating → certified → shadowing → canary → approved | rejected | stopped | expired

Config activation:
compiled → prepared → ready → active → superseded | rolled_back | quarantined

Incident/Reconciliation:
detected → restricted → investigating → reconciling → recovered | degraded_accepted | retired
```

`degraded_accepted` 不是永久 waiver，必须绑定范围、owner、补偿控制、expiry和重新评估；安全、跨 Site、unknown retry、
无 certification、usage/cost丢失不能 accepted-risk放行。

### 7.3 Stable error taxonomy

```text
model.option.not_in_release
model.option.plan_not_eligible
model.option.expired
model.option.disabled
model.option.input_incompatible
model.option.reconfirmation_required
model.option.temporarily_unavailable
model.option.availability_unknown
model.route.no_eligible_candidate
model.route.certification_invalid
model.attempt.submission_unknown
model.attempt.outcome_unknown
model.attempt.reconciliation_required
model.config.drift_detected
model.config.activation_failed
model.certification.expiring
model.certification.expired
model.provider.capacity_exhausted
model.usage.cost_pending
```

用户文案只使用 safe category 与产品动作；Provider exception、account、endpoint、secret、raw request或跨 Site细节不得
进入 UI/URL/analytics。Operator可在授权后查看 safe technical detail和correlation refs。

## 8. Recovery Matrix

| Condition | RecoveryAction | Required behavior |
|---|---|---|
| Option list stale | refresh_availability | 重新取可信投影；不自动改变已选 draft |
| selected Option失效且尚未提交 | select_alternative / reconfirm | 保留draft；新选择产生新digest |
| Admission拒绝 | change_parameters / redeem / reauthenticate | 不创建Run/Job/Attempt，不收费 |
| Gateway无eligible candidate且无effect | wait_and_refresh / select_alternative | 返回typed unavailable；不global fallback |
| pre-effect Attempt definitely not submitted | retry_same_invocation_policy | Gateway按同Invocation和Route创建受控next Attempt |
| submission/outcome unknown | no_user_action / request_support | 查询原operation并reconcile；禁止fallback/retry |
| stream在可见token后中断 | attach_or_terminal | 重连原journal/terminal；禁止跨模型续写 |
| LiteLLM critical drift | quarantine_and_rollback | 停止新Attempt，回到预认证config或关闭route |
| certification即将到期 | renew_or_replace | 新证书/替代route在到期前完成canary |
| certification已过期 | disable_new_attempts | 已提交Attempt reconcile；新调用fail closed |
| canary guardrail breach | stop_canary_and_rollback | 停新candidate流量，保留全部Attempt/usage证据 |
| rollback target不再合法 | restrict_surface | 不强行rollback；关闭新提交并建立替代candidate |
| Usage/Rating不可用 | no_user_action | 结果可完成为cost_pending，committed allocation保留 |
| Provider late success/correction | reconcile_same_attempt | 更新同Attempt/Usage revision，不创建第二结果/收费 |

任何恢复页都必须显示：是否已提交 Provider、是否可能收费、是否安全重试、last known state、observedAt、owner、
reconciliation/renewal deadline、下一动作和 Support deep link。

## 9. Functional Requirements

### 9.1 ModelOption and user choice

- FR-MOD-001：Web只消费版本化 ModelOption/Availability，不接收或提交 Provider/Deployment/raw model。
- FR-MOD-002：Option列表由 SiteRelease、Surface、Plan和政策交集产生，跨 Site ref fail closed且不泄漏存在性。
- FR-MOD-003：未显式选择只使用 published default exact revision；不存在合法default时阻止Surface新提交。
- FR-MOD-004：显式选择在receipt/authorization冻结；disabled/expired/unentitled/incompatible时不静默default。
- FR-MOD-005：material change产生新revision与reconfirmation；同label不能绕过。
- FR-MOD-006：历史Run/Job保留Option label/capability/cost/disclosure snapshot，不按当前catalog重写。
- FR-MOD-007：Option disclosure必须可本地化、可访问，并说明能力、限制、相对质量/延迟和费用档位。

### 9.2 Role completeness and Site composition

- FR-MOD-010：每个enabled Surface compile完整Effective Bundle，不允许运行时global role fallback。
- FR-MOD-011：General Chat至少有`assistant.primary`；Studio按OperationSpec同时具备assistant/generation及安全role。
- FR-MOD-012：Option只能覆盖声明role；hidden/internal role不可由客户端覆盖。
- FR-MOD-013：Assignment绑定SiteRelease candidate、Plan grants、rollout、expiry、Support tier和rollback target。
- FR-MOD-014：同一Catalog可被多个独立Site引用，但账号、授权、历史、Release与Web部署仍严格隔离。

### 9.3 Catalog and policy operations

- FR-MOD-020：Definition、Deployment、Profile、Pool、Equivalence、Route、Bundle、Option、Assignment独立版本化。
- FR-MOD-021：published revision不可原地编辑；mutation使用expectedVersion、idempotency、reason、step-up、audit。
- FR-MOD-022：Pool membership不自动授予fallback等价；跨Definition必须有独立evidence与scope。
- FR-MOD-023：candidate dry-run展示依赖图、included/excluded reason、capacity/cost/risk和受影响SiteRelease。
- FR-MOD-024：Admin/BFF不得直接改Model Control/Gateway DB、LiteLLM YAML/DB或active config。
- FR-MOD-025：高风险publish/promotion/secret/config/deny/rollback必须maker-checker并在effect point重验。

### 9.4 Evaluation, promotion and certification

- FR-MOD-030：任何production Deployment/Route必须有scope匹配且未过期ProviderCertification。
- FR-MOD-031：EvaluationSuite及Report记录dataset权利、版本、metrics、threshold、judge、seed、variance和cost。
- FR-MOD-032：shadow禁止用户可见输出、tool/effect和用户收费，且必须通过privacy/data policy。
- FR-MOD-033：canary冻结cohort、traffic、budget、guardrails、stop/rollback policy并产生per-attempt证据。
- FR-MOD-034：PromotionDecision不等于SiteRelease activation；两层digest/signature不能自引用或复用错误scope。
- FR-MOD-035：影响模型行为的Provider/SDK/adapter/mapping/route/prompt/agent变化使对应证据失效并重评。

### 9.5 Gateway, fallback and unknown

- FR-MOD-040：Gateway只消费opaque authorization handle并在effect前重验revision、epoch、budget与candidate。
- FR-MOD-041：ResolutionRecord记录候选、排除原因、fallback与disclosure；用户仅见安全产品解释。
- FR-MOD-042：只有original Attempt definitely_not_submitted才可fallback；unknown/post-output/post-effect禁止。
- FR-MOD-043：fallback不得降低Plan、data region、retention、content、safety、parameter或费用承诺。
- FR-MOD-044：Attempt terminal/unknown/reconciled与Usage/Cost outbox持久化，不因浏览器断线重跑。
- FR-MOD-045：completed/cost_pending允许交付；Gateway/LiteLLM不计算客户价格或直接写Credit Journal。

### 9.6 LiteLLM and configuration operations

- FR-MOD-050：一个LiteLLM alias精确对应一个Kokoro Deployment；禁止LiteLLM business routing/fallback/budget。
- FR-MOD-051：GatewayConfigRevision由Control compiler生成并签名，prepare/readiness/activate同epoch完成。
- FR-MOD-052：持续比较expected与observed image/config/alias/model/secret/retry/timeout digests。
- FR-MOD-053：critical drift自动quarantine/rollback/page；不得自动采纳运行态为新真源。
- FR-MOD-054：direct adapter fallback是独立Deployment和显式Config/Route revision，不做请求内隐藏旁路。

### 9.7 Certification expiry and incident recovery

- FR-MOD-060：certificate在30/14/7/1天告警并有renewal owner、suite、capacity和替代route计划。
- FR-MOD-061：expired/revoked certificate在effect point阻止新Attempt；历史事实和已提交Attempt按policy保留/reconcile。
- FR-MOD-062：Provider incident按account/deployment/region/operation隔离，不将单一health signal改写lifecycle。
- FR-MOD-063：恢复流量需health+capacity+secret+config+certification+canary证据，不能仅依赖Provider status page。
- FR-MOD-064：irreconcilable到期必须有Finance/Support/Hold disposition，不能永久unknown或无限占用allocation。

## 10. Admin, Support and Operations

### 10.1 Required Model Console views

1. Catalog graph：Definition→Deployment→Profile→Pool/Equivalence→Route→Bundle/Option→Assignment→SiteRelease。
2. Provider view：Account/secret revision、region、policy、cost、capacity、health、certification与incident。
3. Evaluation view：Suite、dataset rights、Run、Report、shadow/canary、PromotionDecision与影响图。
4. Runtime timeline：Authorization、Invocation、Resolution、Attempt、ProviderOutcome、Usage/Cost、fallback和reconciliation。
5. Config view：GatewayConfig/LiteLLM expected/observed digest、alias map、image、secret、drift、activate与rollback。
6. Expiry view：所有certificate、renewal owner、remaining time、blocked assignments和replacement readiness。

所有视图带 environment、region、Site scope、freshness、source owner、revision和safe fields。普通Model Operator不能因
查看route而获得prompt/output、用户identity、Billing细节或secret。

### 10.2 Typed operator commands

| Command | Risk / approval | Product effect |
|---|---|---|
| RegisterModelDefinitionRevision | medium / maker | 创建candidate catalog revision |
| RegisterDeploymentCandidate | high / maker-checker | 绑定account/adapter/upstream revision，不激活 |
| CertifyDeployment | high / maker-checker | 引用exact report产生有限期certificate |
| PublishModelProfilePoolRoute | high / maker-checker | 发布不可变policy revision，不切生产流量 |
| PublishModelBundleOptionAssignment | high / maker-checker | 创建SiteRelease candidate input，不直接上线 |
| StartEvaluationOrCanary | high / maker-checker | 以冻结scope/budget执行评测或canary |
| RecordModelPromotionDecision | critical / maker-checker | 签名批准或拒绝指定candidate/scope |
| PrepareActivateGatewayConfig | critical / maker-checker | prepare/readiness后切换config epoch |
| RollbackGatewayConfigOrRoute | critical / maker-checker | 切回已认证目标，不改历史Attempt |
| ApplyManagedDeploymentDeny | critical / dual review or emergency tighten | 阻止新Attempt；短TTL紧急收紧可先执行后复核 |
| RotateProviderSecret | critical / maker-checker | current/next overlap、验证、切换、revoke receipt |
| ReconcileModelAttempt | high / maker-checker by policy | 查询原Provider effect，不盲重试 |
| QuarantineConfigDrift | critical / policy automation + page | 隔离未声明config并保持证据 |

所有命令进入 PRD-10 `OperatorCommandRegistry`，包含scope、role、risk、reason、step-up、approval、CAS、idempotency、
receipt、notification、SLA、audit、reconciliation与runbook。超时只查询同request identity。

### 10.3 Queues, dashboards and alerts

必须提供：deployment validation、evaluation/certification、promotion/canary、certificate renewal、provider health/capacity、
Attempt unknown/reconciliation、Usage outbox/cost anomaly、config/LiteLLM drift、secret rotation、Site assignment compile和
Support escalation队列。每个queue固定owner、backup、ack/update/resolution SLA、aging、capacity、escalation和runbook。

P0 alerts至少覆盖：未认证Attempt、unknown retry/fallback、critical drift、alias ambiguity、cross-Site authorization、
usage fact丢失、secret exposure/revoke failure、canary critical guardrail、expired certificate active traffic和rollback失败。

### 10.4 Support workflow

```text
SupportCase + Site/Run/Job safe refs
→ ModelOption/selection/availability snapshot
→ Authorization/Invocation/Attempt safe timeline
→ execution + fallback + cost states
→ Model Operations queue handoff
→ authoritative reconcile/recovery receipt
→ user-visible resolution + notification
```

Support不得直接启用Option、改route、重试unknown Attempt、切Deployment、改Usage或补Credit。财务修正进入Commerce
Correction流程；模型团队只提供Attempt/Usage evidence。Case在execution、cost、recovery和mandatory notification均有
authoritative receipt前不能关闭。

## 11. Security, Privacy, Accessibility and Localization

- 每个read/command/effect验证可信environment/region/Site/role/scope/epoch；浏览器siteId/releaseId不构成授权。
- Provider secret只以Secret Manager ref和短时workload fetch存在；绝不进入revision diff、log、trace、Support或analytics。
- prompt/output/tool schema默认不进入Model Console；需要内容诊断时走PRD-10 JIT evidence grant和PRD-16 Trust边界。
- data residency、provider training/retention与content consent是route硬约束，fallback不得降低。
- Option selector、availability、reconfirmation、fallback disclosure和所有恢复状态满足PRD-14 WCAG 2.2 A/AA完整流程。
- 能力、限制、费用档位与状态不只靠颜色/图标；keyboard、screen reader、mobile、200% zoom/400% reflow可完成。
- localize的是产品label/reason/recovery copy；canonical ID、time、usage dimension不做locale normalization。
- deadline/expiry/canary window同时显示absolute instant、timezone和必要relative time；权威判断不依赖浏览器时钟。

## 12. Edge Cases and Failure Matrix

| Scenario | Expected behavior |
|---|---|
| 用户打开页面后Plan降级 | submit重验失败、保留draft、显示redeem/select alternative；不dispatch |
| 同名Option发布新revision | 旧draft显示变更并要求reconfirm；不按label自动升级 |
| SiteRelease回滚时有active Run | active authorization/Attempt按冻结policy；新提交使用rollback release |
| default Option被紧急撤销 | 无合法替代则关闭新提交；不使用global default |
| visible generation Option完整但hidden safety role缺失 | compile hard fail，Surface不能上线 |
| Pool有两个Definition但无Equivalence | 不得cross-model fallback；候选只按精确policy使用 |
| Provider连接在send前确定失败 | 同Invocation可按route创建next Attempt并记录Resolution |
| Provider timeout无法确定是否提交 | submission_unknown，禁止retry/fallback，保留allocation并reconcile |
| stream已有token后Deployment故障 | attach/partial/failed，不跨模型拼接答案 |
| canary指标总体正常但单Site安全失败 | 按Site维度critical guardrail停止并rollback |
| certificate在approval后activation前过期 | activation recheck失败；重新认证，不能复用签名 |
| certificate在async Attempt运行中到期 | 不创建新Attempt；原已提交operation查询/reconcile |
| LiteLLM alias意外映射两个Deployment | readiness/active drift P0；quarantine并停止新Attempt |
| LiteLLM UI手工修改retry/fallback | drift检测并恢复声明revision；不自动采纳 |
| Config rollback target secret已撤销 | 禁止rollback，restrict route并启用合法替代流程 |
| Control Plane不可用但bundle仍有效 | 已授权/有效期内调用按policy继续；告警；过期后新Admission关闭 |
| Gateway terminal已存但Usage outbox延迟 | 不重跑Provider；结果cost_pending，outbox恢复 |
| Provider late success与用户已开Support Case | 同Attempt reconcile，更新Case和费用；不创建第二Artifact |
| Support尝试直接切route或重试unknown | command拒绝并审计；转Model queue |

## 13. Acceptance Criteria

### AC-MOD-01 — Site, Plan and Surface eligibility

```gherkin
Given two Sites publish different Chat and Music ModelOptions and Plans
When hosts, option refs, plan grants, releases or operation classes are crossed
Then discovery and submission fail closed without revealing the other Site
And no unauthorized EffectiveBundle, ModelAuthorization or Provider Attempt is created
```

### AC-MOD-02 — Stable published default

```gherkin
Given a Chat Surface hides its selector but publishes a complete default Option
When a user submits without an explicit selection
Then the exact default Option revision is frozen in the receipt and authorization
And assistant.primary and every required hidden role resolve at release compile time
And no runtime global default is consulted
```

### AC-MOD-03 — Explicit selection never silently falls back

```gherkin
Given a user selected an Option that becomes expired, disabled or unentitled before submit
When Admission validates the command
Then the draft and attachments are preserved and no Run, Job or Attempt is dispatched
And the UI offers eligible alternatives with their changed promises
And only an explicit new selection and confirmation can change the Option revision
```

### AC-MOD-04 — Material change requires reconfirmation

```gherkin
Given an Option keeps the same localized label but changes cost tier, capability, data policy or fallback semantics
When an old draft is submitted
Then the old receipt cannot authorize the new revision
And the user receives an accessible material-change summary
And a new command digest is created only after explicit reconfirmation
```

### AC-MOD-05 — Role completeness for Chat and Studio

```gherkin
Given a candidate enables General Chat, Music and Video
When the SiteRelease compiles its model assignments
Then Chat resolves assistant.primary
And Music and Video resolve their assistant, generation and declared safety roles
And any missing, cross-Site, uncertified or ungranted role blocks the candidate
```

### AC-MOD-06 — Safe pre-effect fallback

```gherkin
Given an authorized Route has two certified equivalent Deployments
And the first Attempt is proven definitely_not_submitted
When its connection fails before Provider effect
Then Gateway may create one policy-authorized next Attempt in the same Invocation
And ResolutionRecord preserves both decisions and the required product disclosure
And the user's selected Option and price envelope do not change
```

### AC-MOD-07 — Unknown blocks retry and fallback

```gherkin
Given a Provider operation may have been submitted but its outcome is unknown
When a caller, user or operator requests retry or fallback
Then no second Provider Attempt is created
And the original operation is queried until reconciled or irreconcilable deadline
And execution, possible cost, owner and next action remain visible
```

### AC-MOD-08 — No post-output cross-model continuation

```gherkin
Given an Attempt emitted user-visible tokens, a tool call or a partial media candidate
When the Deployment fails
Then Gateway does not continue the same result with another ModelDefinition
And the Run or Job reaches an explained partial, failed or unknown state
And any retry is an explicit new Run, branch or Job with preserved provenance and cost
```

### AC-MOD-09 — Catalog and assignment immutable publication

```gherkin
Given an operator changes a Profile, Pool, Route, Bundle, Option or Assignment
When publication is requested
Then a new immutable revision, impact diff, expectedVersion and approval digest are required
And no active row, LiteLLM YAML or SiteRelease is mutated in place
And publication alone does not activate production traffic
```

### AC-MOD-10 — Reproducible evaluation and promotion

```gherkin
Given a Deployment candidate completed quality, safety, protocol, latency and usage suites
When a PromotionDecision is reviewed
Then dataset rights, suite, report, adapter, mapping, provider revision, confidence and cost are immutable and traceable
And shadow and canary evidence match the exact candidate and scope
And a changed dependency invalidates the affected evidence instead of reusing it
```

### AC-MOD-11 — Canary guardrail rollback

```gherkin
Given a candidate Route is serving a bounded canary
When a frozen critical guardrail breaches for one Site or request class
Then new candidate Attempts stop within the published SLO
And traffic returns only to the pre-certified rollback target
And in-flight Attempts, Usage facts and incident evidence remain intact and reconcilable
```

### AC-MOD-12 — LiteLLM one-alias invariant

```gherkin
Given a signed GatewayConfig declares one alias for one Deployment
When the loaded LiteLLM config maps it to another or multiple upstream deployments
Then readiness or continuous drift verification fails
And new traffic is quarantined or rolled back before business routing can occur
And the observed config is never adopted as Control Plane truth
```

### AC-MOD-13 — Certification expiry fail closed

```gherkin
Given a Deployment certification expires or is revoked
When Gateway evaluates a new Attempt
Then the Deployment is excluded before Provider effect
And no cached bundle, health state or operator override can restore eligibility
And already submitted operations follow their frozen cancel and reconciliation policy
```

### AC-MOD-14 — Config activation and rollback epoch

```gherkin
Given a new GatewayConfig and LiteLLM config are prepared
When activation occurs or fails midway
Then Gateway only routes against a fully ready matching signed epoch
And failure leaves one authoritative active epoch with a queryable receipt
And rollback uses the predeclared certified target without changing historical Attempts
```

### AC-MOD-15 — Attempt usage and customer cost separation

```gherkin
Given an Attempt reaches success, failure, cancel or reconciled terminal while Usage Rating is unavailable
When Gateway commits the outcome
Then ProviderCostFact, AttemptUsageFact and outbox evidence are durable and unique
And the user result may be completed with cost_pending
And neither Gateway nor LiteLLM writes customer Credit or calculates customer price
```

### AC-MOD-16 — Provider late outcome reconciliation

```gherkin
Given an unknown async generation later reports success and duplicate callbacks arrive
When the provider inbox and reconciler process them
Then one ModelAttempt terminal and one finalization intent are produced
And Artifact and Usage lineage are not duplicated
And Support and the user receive the updated authoritative outcome
```

### AC-MOD-17 — Support-safe explanation

```gherkin
Given a user reports that a selected Option was unavailable, failed over or remained unknown
When Support opens the Site-scoped timeline
Then it can see the selection snapshot, safe Resolution explanation, attempt/cost state, deadline and owner
And it cannot see another Site, Provider secret or restricted prompt/output
And it cannot retry the Attempt or mutate the route directly
```

### AC-MOD-18 — Emergency deny and recovery

```gherkin
Given a ProviderAccount or Deployment has an urgent security restriction
When an authorized managed deny is applied
Then new pre-effect Attempts are rejected within the propagation SLO
And irreversible Attempts only cancel or reconcile under frozen policy
And restoring traffic requires current secret, config, certification, health, capacity and canary evidence
```

### AC-MOD-19 — Historical stability

```gherkin
Given an Option and Deployment are later retired and the SiteRelease changes
When a user or authorized Support operator views an old Run or Job
Then the original Option label and promise snapshot, execution, disclosure and cost states remain explainable
And the history is not re-resolved through the current Catalog
```

### AC-MOD-20 — GA semantic preservation gate

```gherkin
Given Model Gateway is introduced at the existing GA model factory boundary
When the approved differential corpus covers stream ordering, tool-call IDs, reasoning, structured output, HITL, cancel and terminal
Then graph, assembly, prompt, tool, skills/MCP, checkpoint, effect, Handoff, namespace and terminal semantics are unchanged
And any required semantic difference stops implementation for explicit user approval
```

## 14. Negative, Property, Chaos and Certification Tests

### 14.1 Static and contract

- Web/Session forbidden fields/imports：Provider、Deployment、secret、Gateway route resolver、raw model string。
- GA forbidden claims/imports：Site/User/Plan/Billing/Provider secret与直接Provider production SDK branch。
- LiteLLM forbidden authority：multi-deployment alias、business fallback、customer budget/rate、Site virtual-key policy。
- generated TS/Python schemas对Option/Authorization/Invocation/Event/Usage strict parity，unknown字段fail closed。
- every enabled role maps to exact published Profile/Pool/Route/certification/config revision。

### 14.2 Property and concurrency

- 任意Site/Plan/Surface/Option排列只得到eligibility交集，不因缺配置扩大权限。
- 任意default/explicit/revision变化序列均不发生静默Option替换。
- 任意candidate ordering/health变化均只选择Route允许候选且生成可解释ResolutionRecord。
- 任意Attempt crash/retry schedule，unknown不产生第二Provider effect；terminal Usage fact唯一。
- 任意并发config activate/rollback只有一个authoritative epoch，alias映射无歧义。
- 任意certificate expiry/revoke/cache schedule，effect point不使用无效证据。

### 14.3 Failure and chaos

- Control Plane outage/bundle expiry/revocation、Gateway多pod crash/drain、quota owner failover。
- LiteLLM process/config/DB outage、manual drift、alias冲突、secret rotation中断、direct adapter cutover。
- Provider send前/后timeout、首chunk前/后断线、duplicate/out-of-order callback、late success、invoice correction。
- evaluation/shadow/canary worker crash、metric delay、single-Site regression、rollback target失效。
- Usage outbox、Rating、Session/Job projection和Support notification outage。
- SiteRelease promote/rollback与active Run/Job、Plan change、restriction epoch、certificate expiry交错。

通过条件不仅是请求最终成功，还包括：无跨Site/Plan绕过、无静默语义变化、无重复Attempt/Artifact/charge、历史可解释、
unknown有期限、config epoch唯一、用户与Support均有正确恢复动作。

## 15. Analytics and Telemetry

Required product events：option list viewed、default presented、option selected、selection invalidated、reconfirmation shown/
accepted/abandoned、submit blocked reason、fallback eligible/attempted/completed/blocked、availability recovered、Support opened。

Required operations events：catalog/deployment/policy revision created/validated/published/retired、evaluation/shadow/canary
started/stopped、PromotionDecision、config prepared/activated/rolled back/quarantined、drift detected/resolved、certificate
expiring/renewed/expired/revoked、managed deny、provider incident、Attempt unknown/reconciled、usage outbox/cost anomaly。

Telemetry不得包含prompt/output全文、tool args、secret、endpoint、用户identity、Code、raw Provider payload或高基数错误。
Analytics失败不改变用户执行或Attempt终态；audit/config/certification evidence写入失败必须阻断高风险发布/命令。

## 16. Dependencies, Risks and Mitigations

### 16.1 Dependencies

| Dependency | Owner | Impact if delayed |
|---|---|---|
| PRD-00 Profile/Inventory/Certification | Site Fleet/Release | Option/Assignment不能进入SiteRelease |
| PRD-03 Plan/Credit/Usage contracts | Commerce/Usage | eligibility与cost_pending无法闭环 |
| PRD-05 Chat selection/receipt/session projection | Chat/Session | 用户选择与历史解释不完整 |
| PRD-07/08I/08M/08V Operation/role requirements | Studio owners | 专业bundle无法证明完整 |
| PRD-10 Operator identity/command/queue/audit | Admin/Security | Model Console不能安全运营 |
| PRD-16 Content/Data rights | Trust/Data Governance | route、evaluation和fallback政策不完整 |
| Model Gateway contract spike | Model Platform/GA | GA外围adapter能否无语义变化切换未知 |
| Usage Rating canonical ingest | Usage/Finance | Attempt可完成但长期cost_pending |

### 16.2 Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| ModelOption成为Provider别名 | medium | high | product-only schema、forbidden fields、历史snapshot |
| 过度追求可用性导致静默fallback | high | critical | pre-effect proof、Equivalence、disclosure、unknown No-Go |
| Config对象过多难运营 | medium | medium | dependency graph、typed workflow、compiled bundle、统一console |
| certification更新跟不上Provider漂移 | high | high |短TTL、expiry lead alerts、observed revision、替代route |
| LiteLLM成为第二control plane | high | critical | generated config、one alias invariant、drift quarantine、no business routing |
| canary全局指标掩盖单Site伤害 | medium | high | Site/request class维度guardrail与自动停止 |
| rollback目标已失效 | medium | high | preflight持续校验、无合法target时restrict而非强回滚 |
| Support为止损盲重试unknown | medium | critical | typed queue、无retry权限、same-attempt reconciliation |
| Model改造触碰GA语义 | medium | critical | Phase A外围adapter+differential corpus+用户专项批准门 |

## 17. Milestones and Release Gates

### 17.1 Milestones

1. **Product/architecture review**：Chat、Studio、Site、Commerce、Model、GA、Trust、Support确认Option/eligibility/
   disclosure/operations边界。
2. **Wave 0 contract**：冻结stable IDs、runtime schema、catalog dependency graph、evidence、metrics和negative gates。
3. **Wave 5A Control foundation**：Catalog/Deployment/Profile/Pool/Route/Bundle/Option/Assignment与compiled bundle。
4. **Evaluation and operations**：suite/report/certification、shadow/canary/promotion、Model Console、queues/runbooks。
5. **Gateway/LiteLLM cut**：Attempt/Usage/unknown、generated config、drift、expiry、direct adapter和provider sandbox认证。
6. **Product integration**：Chat default/selector/reconfirmation、Studio multi-role、Support timeline、two-Site E2E。
7. **RC certification**：load/soak/chaos/DR/security/a11y/i18n/Finance/Support/SRE game days和SiteRelease evidence。

### 17.2 Release blockers

以下任一条件阻断对应Model revision、Surface或SiteRelease：

- 用户能选择Provider/Deployment/raw model，或显式Option被静默替换；
- default/hidden/generation role不完整，或运行时需要global fallback补齐；
- active Deployment缺有效scope-matched certification、evaluation、secret/config或rollback evidence；
- unknown/post-output/post-effect触发retry/fallback；
- LiteLLM alias映射多个Deployment或拥有business fallback/budget/rating authority；
- Config/LiteLLM drift可直接生效、无法quarantine，或active epoch不唯一；
- terminal/reconciled Attempt缺ProviderCostFact/AttemptUsageFact/outbox；
- canary无Site维度guardrail、自动stop或authoritative rollback receipt；
- certificate expiry/revoke不能在effect point fail closed；
- Model Console存在direct DB/YAML/UI mutation、共享管理员或缺typed receipt/reconciliation；
- enabled Surface的用户 unavailable/fallback/unknown/cost_pending 无Support/notification/recovery闭环；
- GA differential corpus发现未授权语义差异。

## 18. Review Questions and Authorization Boundary

- [ ] Site/Product：default、visible/hidden Option、material change与reconfirmation承诺是否批准？
- [ ] Chat/Studio：selector、历史snapshot、fallback disclosure与multi-role composition是否完整？
- [ ] Model Platform：Catalog/Deployment/Profile/Pool/Route/Bundle/Assignment lifecycle与Gateway边界是否批准？
- [ ] Evaluation/Trust：dataset权利、suite、certification TTL、shadow/canary和promotion门是否批准？
- [ ] SRE/Security：LiteLLM drift、secret、deny epoch、expiry、rollback和incident恢复是否可运营？
- [ ] Finance/Usage：Provider cost、AttemptUsageFact、cost_pending和irreconcilable disposition是否闭环？
- [ ] Support/QA：状态、错误、SLA、two-Site negative、unknown与恢复验收是否充分？
- [ ] GA Owner/User：Phase A外围adapter是否能由差分测试证明零runtime semantic change？

本文处于内部评审，`implementationAuthorized: false`。批准本文仍不授权实现、数据迁移、Provider调用或生产发布。
`gaRuntimeSemanticChangeAuthorized: false`：任何需要修改GA graph、assembly、prompt、tool、skills/MCP、checkpoint、
effect、HITL、cancel、Handoff、namespace、runEpoch、terminal或event ordering的方案必须停止并由用户专项批准。

## 19. Related Documents

- [PRD-00 Launch Profile 与 Journey Contract](2026-07-25-prd-00-launch-profile-and-journey-contract.md)
- [PRD-03 Account、Plan、Redeem 与 Credit](2026-07-25-prd-03-account-plan-redeem-and-credit.md)
- [PRD-05 Chat Conversation、Run 与 Interaction](2026-07-25-prd-05-chat-conversation-run-and-interaction.md)
- [PRD-07 Studio Common、Job 与 Cost UX](2026-07-25-prd-07-studio-common-job-and-cost-ux.md)
- [PRD-08I Image Studio](2026-07-25-prd-08i-image-studio.md)
- [PRD-08M Music Studio](2026-07-25-prd-08m-music-studio.md)
- [PRD-08V Video Studio](2026-07-25-prd-08v-video-studio.md)
- [PRD-10 Admin Operating Console](2026-07-25-prd-10-admin-operating-console.md)
- [PRD-16 Trust、Content Safety 与 Media Rights](2026-07-25-prd-16-trust-content-safety-and-media-rights.md)
- [Model Control、Model Gateway 与 LiteLLM 目标架构](2026-07-25-model-control-gateway-litellm-architecture-design.md)

## 20. Revision History

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-07-25 | 首稿：闭环ModelOption eligibility/default/unavailable/reconfirmation/fallback disclosure与Model/Provider运营全生命周期 |
