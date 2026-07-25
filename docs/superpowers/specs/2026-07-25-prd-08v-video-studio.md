---
artifact: product-requirements-document
prdId: PRD-08V
version: "1.0"
created: 2026-07-25
status: internal-review-active
scope: video-studio-text-image-video-generation-storyboard-shot-plan-timeline-edit-extend-reframe-inpaint-lip-sync-upscale-interpolation-audio-subtitle-export
accountableProductRole: Video Studio Product Lead
mandatoryCosigners: [Video ML, Job Runtime, Asset, Artifact, Model Platform, Trust, Rights, Accessibility, Web, Support, SRE, QA]
engineeringOwner: team:video-studio-engineering
qaOwner: team:video-studio-quality
supportOperationsOwner: team:video-studio-operations
namedOwnerAssignmentStatus: assigned-team-responsibility-ids
implementationAuthorized: false
gaRuntimeSemanticChangeAuthorized: false
---

# PRD-08V：Video Studio

## 1. Overview

### Problem

Video 不是“输入 prompt 输出 mp4”。完整创作包含故事板、镜头计划、角色与场景连续性、源素材、剪辑时间线、
画面与声音同步、字幕、局部修复、延展、重构图、补帧、放大和多种交付版本。若把这些能力压成一个宽泛
`generateVideo(prompt, options)`，镜头身份、源版本、帧范围、音画同步、素材权利、候选费用和失败恢复都会丢失；
若由浏览器小数秒、转码预览或 Provider 百分比担任权威，extend、inpaint、lip-sync 和字幕会在帧率、可变帧率、
重采样或回调乱序后漂移。人物和声音还涉及肖像、同意、未成年人、深伪和发布披露等高风险约束。

### Solution

在 PRD-07 的共享 Draft→Operation→Job→Attempt→Candidate→Artifact→Usage 主链上，建立有限、版本化的 Video
Operation family：`text_to_video`、`image_to_video`、`video_to_video`、`shot_generate`、`extend`、`reframe`、
`video_inpaint`、`lip_sync`、`upscale`、`frame_interpolation` 和 `timeline_rendition`。Video Draft 用不可变的
Storyboard、Shot Plan、Timeline、Track、Reference Binding 与 Continuity Specification 表达意图；提交时冻结为 typed
`VideoOperationSpec`。每个输出创建新的 ArtifactVersion，不原地改 source。

Image、Music、Video 共用同一个 GA 接入、SubmitOperation façade、Job Runtime、Asset/Blob、Artifact、Trust、Usage Rating、
Credit/Hold 与 Support/Operations 基建；不新建 modality 子仓、Video 专属 Job 服务或 Provider 服务。Video 需要已发布的
主 `video.assistant` role 和 generation roles，但角色解析只扩展 Model/Agent assignment 与 OperationDefinition，不能改变
GA graph、assembly、tool、checkpoint、effect、Handoff、namespace 或 terminal 语义；任何 GA runtime 改动继续受专项审批门。

### Users and stories

| ID | User story | Priority |
|---|---|---|
| VID-US-01 | 用户可从文本、单图/多图或视频源生成可比较的视频候选 | P0 if-enabled |
| VID-US-02 | 用户可建立故事板和镜头计划，逐镜头声明构图、动作、角色、场景、时长和转场意图 | P0 |
| VID-US-03 | 用户可在精确时间线上组合视频、音频和字幕，并用帧/时间码结构化路径完成编辑 | P0 |
| VID-US-04 | 用户可对确切源版本执行 extend、reframe、inpaint、lip-sync、upscale 和 interpolation | P0/P1 by family |
| VID-US-05 | 用户可维持角色与场景的一致性，同时理解它是受能力和证据约束的意图，不是绝对保证 | P0 |
| VID-US-06 | 用户可离开长任务、恢复同一 Job、保留 partial shots，并理解 unknown、费用与恢复动作 | P0 |
| VID-US-07 | 键盘、屏幕阅读器、放大、语音和移动用户可通过 shot/track/list/timecode 完成等价流程 | P0 |

## 2. Goals、Metrics and Non-Goals

### Goals

1. 每个 Video operation 有明确 family、输入/输出、source revision、timebase、角色和费用维度，不接收万能 Provider payload。
2. Storyboard、Shot Plan、Timeline、帧范围、音频/字幕轨和 continuity 全部版本化、可重建、可审计。
3. Direct Studio 与 Agent tool 复用同一 Operation/Job/Artifact/Trust/Usage/Credit spine。
4. Provider effect、Job execution、Candidate/Shot 状态、Artifact finalization、Trust 与 Cost 正交恢复；unknown 不重放。
5. 角色/肖像/声音、素材权利、未成年人和 publication eligibility 在正确 stage fail closed。
6. 桌面与移动 complete process、播放器、故事板和时间线满足 PRD-14 与完整 WCAG 2.2 A/AA。

### Success Metrics

| Metric | Baseline | Target | ProductMetric dimensions / action |
|---|---:|---:|---|
| Video Operation 缺 family/source/timebase/output provenance | 未建立 | 0 | Site/Profile/Definition；compile No-Go |
| source/timeline revision 漂移导致错误片段或错误帧被编辑 | 未建立 | 0 certification failures | family/timebase/adapter；disable family |
| 同 submit identity 重复 Operation/Hold/Provider logical effect | PRD-07 目标 | 0 | source direct/agent；P0 page |
| unknown Provider outcome 自动 retry/fallback | PRD-07 目标 | 0 | provider/deployment/family；P0 page |
| completed required output 缺 Artifact/Usage/Trust receipt | 未建立 | 0 | finalizer stage；release blocker |
| candidate/shot/audio/subtitle Artifact、Decision、Usage、charge 串位 | 未建立 | 0 | output slot/track kind；release blocker |
| Video/source/timebase/rights/consent对象跨 Site 引用成功 | 未建立 | 0 | cross-Site matrix；P0 page |
| assistant/generation Usage、track eligibility或source snapshot串位 | 未建立 | 0 | role/family/track；release blocker |
| 角色/场景 continuity 明示要求被静默丢弃 | 未建立 | 0 | capability/ModelOption；fail before effect |
| lip-sync 帧/音频边界超过已发布 tolerance | 未建立 | 0 certified outputs | locale/language/fps；disable assignment |
| restricted/缺权利/缺同意输出进入 export/share/publication | 未建立 | 0 | purpose/policy/age band；P0 page |
| accepted long Job 刷新/断网后无法恢复同一 owner projection | 未建立 | 0 certification scenarios | desktop/mobile/browser；release blocker |
| Video complete process 任一适用 WCAG 2.2 A/AA failure | 未建立 | 0 | Site/Profile/locale/AT；release blocker |
| P0 operation canonical terminal within published deadline | 未建立 | ≥ 99%，外部故障单列 | family/provider/queue class；page/runbook |

所有指标必须引用 ProductMetricRevision，定义 numerator、denominator、exclusions、window、freshness、owner、target、
guardrail 与 release action；至少按 Site、Profile、SurfaceRevision、OperationDefinitionRevision、ModelOption 和 direct/agent
切分，不用全局平均掩盖单 Site、单语言或单 timebase 失败。

### Non-Goals

- V1 不提供完整 NLE/合成软件、实时多人剪辑、任意节点图、用户脚本、模型训练或权重上传。
- 不暴露 Provider、Deployment、底层 scheduler、secret、GPU、raw safety setting 或任意 codec/filter graph。
- 不承诺相同 seed、角色参考或 scene prompt 在不同模型/Deployment/adapter/revision 上逐帧复现。
- 不把“角色一致性”解释为生物识别身份认证，也不建立跨 Site 人脸/声音档案。
- 不自动推定用户拥有 source、角色、地点、商标、音乐、声音、表演或发布权利。
- 不把字幕当音频描述，也不把 transcript 当 PRD-14 要求的全部媒体替代。
- Video Studio 不拥有 Job、Provider Attempt、Blob、Artifact、Trust Decision、Credit Journal 或 customer pricing。
- 不为 Video 新建子仓、modality 服务或第二套 Job/Asset/Trust/Cost runtime。
- 本 PRD 不授权任何实现或 GA runtime 语义变更。

## 3. Scope and Priority

### P0 — enabled Video Profile 的首发合同

- text-to-video、image-to-video、video-to-video 与单镜头 `shot_generate`。
- Storyboard、Shot Plan、角色/场景 reference binding、基础 continuity constraints。
- 版本化单序列 Timeline；视频、音频、字幕轨；剪切、排序、trim、mute、简单 transition intent。
- extend、reframe、video inpaint、lip-sync 的 family contract；具体 family 只有认证后才可 enable。
- 长 Job、逐 shot/candidate partial、cancel、unknown、finalization、lineage、private preview、标准 export。
- 桌面与移动的创建、review、提交、状态、恢复、播放器和结构化时间线等价路径。
- rights/consent/minor/likeness/deepfake/disclosure/a11y gate 与 Support/Operations 闭环。

### P1 — 独立认证后可启用

- upscale、frame interpolation、复杂多段 lip-sync、多音轨 mixdown、批量多比例 rendition。
- 高级 camera/motion continuity、镜头间自动衔接建议和长序列分段生成。
- 自动字幕/翻译/说话人对齐建议；未经人工质量 review 不计作 conforming caption。
- 高级 subject/object masks、track matte、关键帧化 reframe 与复杂 transition profile。

P1 不得作为 P0 Storyboard/Timeline/Recovery/Trust/A11y 缺口的替代。Profile 只可启用已发布 Definition、owner、
Provider certification、Support runbook 和 delta Certification 完整的 family。

### Out of scope

- live video generation/streaming broadcast、实时 avatar 通话、实时 motion capture。
- 任意第三方 URL crawler、公共素材抓取、未审计 plugin/codec/filter。
- public Share/SEO 产品面；Video 只输出供 PRD-09 另行授权的 Artifact。
- 自动法律结论、版权清权或“无深伪风险”保证。

### Canonical Journey `VID-01@1`

```text
Actor: authenticated creator with Site/Project access
Entry: enabled Video Studio route, Chat media Job card, or Library “use as source”
Preconditions: enabled Surface/Definition/Model roles; eligible Plan/Credit; ready source grants;
               current ContentPolicy/Rights/Consent/A11y revisions
Happy path: create/recover Draft → Storyboard/Shot Plan/Timeline → quote/review → submit same identity
            → queue/run/finalize → compare partial/full candidates → save Artifact → authorized export
Alternate paths: text/image/video source; single shot or sequence; direct or agent; mobile or desktop;
                 extend/reframe/inpaint/lip-sync/upscale/interpolation by enabled family
Failure paths: draft conflict; stale source/timebase; rights/consent input; reconfirmation; delayed/cancel;
               unknown Provider outcome; partial/restricted output; finalization/cost/export blocked
Terminal outcomes: completed | partial | failed | canceled | unknown with reconciliation owner
Required common journeys: ST-01…06, AS-01…02, SAF-01…02, UX-01…02, SUP-01…03, NOT-01
```

`VID-01` 发布后不可原地改语义；SiteRelease、OperationDefinition 和 CertificationInstance 必须绑定确切 revision。
每个 failure/terminal branch 必须解析本 PRD 的 UserVisibleState、RecoveryAction、Support Case、Metric 和 acceptance evidence。

## 4. Canonical Product Objects and Ownership

```text
VideoDraftRevision
  immutable siteId / draftRef / operationFamily / storyboardRevisionRef? / shotPlanRevisionRef?
  timelineRevisionRef? / sourceBindings[] / continuityRevisionRef?
  ModelOption / candidateCount / parameterSet / output+export intent

StoryboardRevision
  immutable siteId / ordered BoardFrame[] / narrative beat / scene+character refs / text alternative
  board image AssetVersion refs / transition intent / createdBy+revision

ShotPlanRevision
  immutable siteId / ordered ShotDescriptor[] / sequence timebase / target duration / continuity links

ShotDescriptor
  immutable siteId / stable shotId / storyboardFrameRef? / prompt+action intent / subject+scene bindings
  composition / camera+motion intent / duration / transition handles / audio+dialogue intent
  preservation+continuity constraints / output slot contract

VideoTimelineRevision
  immutable siteId / exact ProjectTimebase / source mapping refs / ordered tracks / edit decisions
  sequence duration ticks / render profile / revision+parent

VideoTrackRevision
  immutable siteId / stable trackId / kind=video|audio|subtitle / ordered clips+cues / role / language?
  gain+mute+mix intent or caption style intent / sync origin / contribution manifest
  Decision+RightsSnapshot+ConsentEpoch / UsageAllocation+costProjection / per-purpose eligibility refs

VideoClipBinding
  immutable siteId / stable clipId / typed sourceMediaVersionRef=AssetVersionRef|ArtifactVersionRef / sourceTimelineRevision
  source interval / sequence interval / transform / speed mapping / transition handles

SubtitleCueRevision
  immutable siteId / stable cueId / contentLanguage / exact sequence interval / text / speaker? / kind
  provenance=human|provider|derived|imported / quality=unreviewed|estimated|reviewed

VideoReferenceBinding
  immutable siteId / typed sourceMediaVersionRef / role=subject|character|face|voice|style|composition|
  motion|camera|scene|background|edit_base|continuation|audio_context
  exact source interval? / influence class / rights+consent+age refs / policy revision

ContinuitySpecRevision
  immutable siteId / Site-local characterRef[] / sceneRef[] / wardrobe+prop+lighting+camera constraints
  invariant|preference classification / evidence+capability / allowed variation

MediaTimeMappingRevision
  immutable siteId / source media+track / original PTS+DTS facts / normalized representation digest
  rational source-to-project piecewise mapping / VFR+audio sample origins / priming+padding / rounding / tool revision

SpatialTemporalMaskRevision
  immutable siteId / source media+Timeline+Mapping / exact interval / logical frame coordinate space
  mask track Blob+checksum / polarity+feather+smoothing intent / tool revision

VideoSourceSnapshotRevision
  immutable siteId / source media+track+clip IDs / Timeline+Mapping / Storyboard+ShotPlan+Continuity
  masks+audio+subtitle+alignment revisions / rights+consent epochs / coherence digest

VideoOperationSpec
  immutable siteId / family / VideoSourceSnapshotRevision + explicit deltas / exact ranges
  assistant+generation role requirements / typed parameters / candidate+track contract
  policy+rights+consent / quote dimensions / cancel+delivery policy

VideoCandidateResult
  immutable siteId / candidateId / shotId? / ArtifactVersion refs / exact duration+media metadata
  audio+subtitle relations / MediaAccessibility+AccessibleOutputProfile refs
  owner-issued Decision+rights+usage+cost projection refs / preview+export eligibility
```

除 Platform baseline 外，所有 Video 业务对象、唯一键、队列分区、callback mapping 和引用都冻结 immutable `siteId`；
Quote、submit、每个 effect、finalization、playback/export mint均验证同 Site/Project/purpose。跨 Site拒绝不得泄漏对象是否存在，
相同content hash、用户、subject或Provider operation ID也不继承授权。

Ownership：

- Project/Video Studio owns Draft、Storyboard、ShotPlan、Timeline、Track、ContinuitySpec revisions；它们是 intent，不是 Job。
- PRD-06 Asset owns upload/scan/AssetVersion/AssetGrant；Video 不接收客户端 URL、storage key 或未 ready bytes。
- Platform Admission owns OperationAuthorization、entitlement、rights/consent/policy gates、root Hold 与 RatingPolicy snapshot。
- PRD-07 Job Runtime owns Operation execution、Job DAG、lease、Attempt、progress、cancel、unknown 与 finalization saga。
- Model Gateway/Capability Runtime owns Provider deployment resolution、Provider Attempt/effect identity、outcome、usage facts。
- Artifact owns stable Artifact、immutable ArtifactVersion、Blob refs、renditions、lineage 和 export delivery refs。
- Trust owns canonical Decision、restriction、rights/consent epoch 与 PublicationAuthorization；ProviderSafetyFact 只是 evidence。
- Usage Rating/Credit owns customer rating、settlement/correction；Video 只展示 `costState` projection。
- Session/GA 只保存 Job/Artifact handle 和 source provenance；GA 不拥有 Video state machine、timebase、Provider 或费用。

## 5. Operation Families and Model Roles

| Family | Required input | Output contract | Priority |
|---|---|---|---|
| `text_to_video` | text/shot intent + output profile | one or more independent video candidates | P0 |
| `image_to_video` | one or more image refs + motion/camera intent | video derived from exact image versions | P0 |
| `video_to_video` | exact source video/timeline + transformation intent | new full or bounded transformed version | P0 |
| `shot_generate` | one ShotDescriptor + bindings/continuity | shot candidate linked to stable shotId | P0 |
| `extend` | source + left/right/end boundary + duration/shot intent | longer version with old/new range mapping | P0 |
| `reframe` | source + target aspect/subject framing path | new framed version with crop/pad/generation provenance | P0 |
| `video_inpaint` | source + exact interval + spatial mask track + edit intent | new version with bounded spatial-temporal edit | P0 if certified |
| `lip_sync` | video face/character binding + dialogue/audio track + language | new synchronized video/audio relation | P0 if certified |
| `upscale` | source + target dimensions/quality profile | new higher-resolution rendition/version | P1 |
| `frame_interpolation` | source + target frame rate/motion profile | new timing-preserving derived version | P1 |
| `timeline_rendition` | frozen Timeline + export/mix/caption profile | rendered ArtifactVersion; no generation rerun | P0 |

- 每个 family 是独立 OperationDefinitionRevision；同一 Provider endpoint 不构成合并 typed schema 的理由。
- `video.assistant` 是 Video Studio 的主 assistant role，负责澄清意图、提出 Storyboard/ShotPlan/Timeline/字幕建议和
  parameter diff；建议必须由用户 apply 才创建新 DraftRevision，不自动提交、扩权、接受费用或声称拥有 rights。
- effect roles 至少区分 `video.generation`，并可由 Definition 声明 `video.edit`、`video.lip_sync`、`video.upscale`、
  `video.interpolation`、`video.caption`、`video.safety`。每个角色由 EffectiveModelBundle 解析；用户只选择产品 ModelOption。
- enabled family只要求其OperationDefinition明示的required role set完整；纯rendition/upscale等未使用assistant的family不因
  assistant缺席失败，也不允许运行时临场补默认role。Surface可以另行要求发布assistant入口，但不改变family runtime合同。
- 主 assistant role 可通过 Direct Studio 或既有 GA assistant/tool entry 参与，但必须调用同一 SubmitOperation façade；
  不新增 GA graph node 语义、generation terminal、checkpoint schema 或第二条 charge path。
- adapter 不支持 continuity、mask、frame rate、audio、caption 或 preservation 参数时 Admission fail/reconfirm；禁止 silent drop。
- assistant是显式、独立的authorized ModelInvocation，具有logical call identity、Trust input gate、provenance、
  AttemptUsageFact、Quote/charge policy和root Hold allocation；它只创建proposed DraftRevision，Submit不得隐式调用、自动apply、
  扩大rights或把assistant Usage混入generation/edit/lip-sync/rendition Attempt。
- 每个OperationDefinition同时冻结runtime roles、effect/candidate identity、`cancelScope=operation|attempt|candidate_slot`、
  preview retention、ChargeTreatment与fallback certification；Provider只支持attempt cancel时UI不得声称逐candidate cancel。

## 6. Storyboard、Shot Plan and Continuity

### 6.1 Storyboard and shot planning

- Storyboard frame 是可选视觉参考，不是最终帧。每格有 stable ID、narrative beat、shot link、顺序、文本替代和 provenance。
- ShotPlan 明确镜头顺序、目标时长、构图、camera/motion、subject action、scene、dialogue/audio、transition 与 handles。
- reorder、duplicate、split、merge、replace 创建新 ShotPlanRevision；已提交 Operation 始终使用冻结 revision。
- 多 shot 提交编译为已发布 OperationDefinition 允许的 Job DAG；用户/Prompt 不提交任意 graph，依赖必须 acyclic。
- 单 shot failure/unknown/restriction 不覆盖其他 shot。Sequence readiness 明确 `complete|partial|blocked`，并列出缺口。

### 6.2 Character and scene consistency

- `characterRef`、`sceneRef` 是 Project/Site-local creative identities，引用确切 Asset/Artifact/description revision；不以
  filename、content hash、人脸 embedding 或用户名称作为跨 Site identity authority。
- 每个 reference 明确 role、允许特征、rights/consent/age、private/public/remix scope。face/voice/likeness 走 PRD-16。
- continuity requirement 分 `invariant`（adapter 必须满足或 fail）与 `preference`（best-effort并明示能力）；不能把
  best-effort 营销为逐镜头完全一致。
- Shot 记录 continuity input、observed evaluation 与用户选择。自动一致性信号只是质量 evidence，不是身份或权利结论。
- wardrobe、prop、lighting、geography、screen direction、camera language 可作结构化约束；Provider不支持时在 Quote 前说明。
- 用户替换角色/场景 reference 或相关 consent/rights epoch 变化时，受影响 shot 必须重审/reconfirm；已生成 Artifact 不改写。

## 7. Exact Frame、Timebase and Source Revision Authority

### 7.1 Canonical authority

- 每个 source 保存 exact media facts：container/codec、coded/display dimensions、pixel aspect、orientation、color/HDR、
  audio sample rate/channel、duration、frame count（若可证明）、presentation timestamps、timebase revision 和 checksum。
- ProjectTimebase 使用 exact rational frame rate `fpsNumerator/fpsDenominator` 与 integer sequence ticks；帧锁定区间使用
  `[startFrameInclusive, endFrameExclusive)`，非整帧媒体使用 `[startTickInclusive, endTickExclusive)`。浮点秒、CSS位置、
  播放器 time、波形像素和 SMPTE 展示字符串都不是 authority。
- drop-frame/non-drop-frame timecode 只是版本化 display/mapping policy；不得把标签直接当帧序号。
- Variable-frame-rate source 先创建不可变 analysis/normalized proxy 和 source PTS↔proxy frame/tick mapping；Operation 绑定
  original source revision、mapping revision 与实际使用 representation。proxy 不冒充原 source。
- `MediaTimeMappingRevision`冻结原始PTS/DTS、edit list、VFR、audio sample origin、codec priming/padding、normalized digest、
  piecewise rational transform与rounding/tool revision；不允许每个adapter各自解释同一source或用单一fps近似VFR。
- Audio 使用 exact sample range或sequence ticks；lip-sync、字幕和视频帧通过同一 TimelineRevision 的 rational mapping 对齐。
- range 为空、反向、越界、落在旧 Timeline、映射不完整、source checksum/revision变化或 rounding 不唯一时 fail/reconfirm；
  不自动 clamp、拉伸或选择最近帧。

### 7.2 Source revision binding

- 所有 edit/extend/reframe/inpaint/lip-sync/upscale/interpolation 必须冻结 exact AssetVersion/ArtifactVersion、
  SourceTimelineRevision、clip/edit decision revision、range、transform 与 digest。
- `source latest`、mutable URL、Library current pointer、浏览器缓存或文件名不能进入 OperationSpec。
- 用户在提交后替换 source、字幕、dialogue、mask 或 track 只创建新 revision/Operation，不改变运行中 Job。
- `VideoSourceSnapshotRevision`将source/track/clip、Timeline/Mapping、Storyboard/ShotPlan/Continuity、mask、audio/subtitle/
  alignment与rights epochs冻结为coherence digest。Quote后任一dependency head变化，submit必须CAS失败并展示reconfirmation diff，
  不读取`current/latest`或混合新旧revision。
- source 被 revoke：effect 前拒绝；已不可逆提交只允许 finalization 到 quarantine/reconciliation，并保留 lineage/Usage fact。
- 派生版本继承 parent 最严格 rights、consent、restriction、retention 与 provenance，不能通过转码/裁剪/补帧洗白。

## 8. Timeline、Video/Audio/Subtitle Tracks

- V1 是一个版本化 sequence，含有序 video/audio/subtitle tracks；track/clip/cue 都有 stable logical ID。
- trim、split、reorder、mute、gain、speed intent、transition、caption edit 形成 EditDecision/Track revision；不改源 bytes。
- speed/rate change 必须用 exact piecewise mapping；若会改变音高、同步或字幕，Quote/review 展示影响并要求 capability。
- transition 有 published type、duration与handles；handles不足时 reject/reconfirm，不自动重复帧或吃掉内容。
- 音频轨区分 dialogue、music、effects、ambience、voiceover、mix；每轨有语言、sync origin、gain/mute和rights refs。
- 字幕 cue 保存 content language、speaker、exact interval、文本、provenance和quality。自动生成/翻译默认 `estimated`，
  未经语言与内容 review 不算 conforming caption，不可绕过 PRD-14 publish gate。
- captions、subtitles、transcript、audio description 是不同产品对象/可访问要求；导出 profile 明确烧录、sidecar或metadata。
- 每个track/clip/cue的Trust、rights、consent、Usage allocation与per-purpose eligibility独立保存owner-issued refs；sequence或
  candidate allow是所有贡献源当前资格的most-restrictive reduction，不能放行被限制的音轨、字幕、人物或局部片段。
- waveform、filmstrip、thumbnail和low-resolution proxy是 visual/performance projections；不得成为 edit或Trust authority。
- Timeline rendition 创建 RenditionJob 和新 ArtifactVersion，不重跑已完成 generation；源 clips/tracks保持不变。

## 9. Family-specific Requirements

### 9.1 Text/Image/Video-to-video and shot generation

- 提交前 review family、prompt/ShotPlan、source/reference roles、continuity、时长、比例、frame rate intent、候选数、
  ModelOption、Quote ceiling、rights/consent/disclosure和 charge treatment。
- image-to-video 明确每张图是 start frame、end frame、character、scene、style 或 composition；不能从位置推断。
- video-to-video 明确 preservation/transformation dimensions、source interval和audio treatment；不支持的维度不静默改写。
- candidate/shot slots 在 Provider I/O 前分配 stable identity；preview/frame sample 不等于 final Artifact。
- reroll、variation、alternate shot 是新 visible Operation/Quote，引用 parent candidate；不是隐藏 Provider retry。

### 9.2 Extend and reframe

- extend 声明 left/right/end/both、boundary frame/tick、目标新增时长、context window、continuity和audio/caption处理。
- 新 Timeline 映射 original preserved range 与 generated range，不能把 bytes 拼接成无 provenance master。
- reframe 声明 target aspect/dimensions、crop|pad|generate policy、subject safe region、camera path和caption/graphic safe areas。
- face/subject auto-tracking是versioned evidence；confidence不足要求结构化关键帧/区域修正，不静默裁掉主体或字幕。

### 9.3 Video inpaint

- SpatialTemporalMaskRevision 绑定 source、TimelineRevision、exact interval、frame coordinate space、mask track checksum、
  polarity、feather/temporal smoothing intent和tool revision。
- viewport/CSS/device pixels不进入 spec；orientation、pixel aspect、proxy mapping只转换一次并通过 golden corpus验证。
- mask为空、全帧、越界、丢帧、与source revision不匹配或Provider只支持单帧时，提交前明确 reject/reconfirm。
- output验证 edited/protected范围与duration/frame mapping；结果是新完整 ArtifactVersion，不覆盖 source。

### 9.4 Lip-sync

- lip-sync 冻结 exact video interval、face/character binding、dialogue audio/track revision、language、phoneme/alignment evidence、
  preservation与output audio policy。不得只凭同名角色或可见人脸授权。
- face/voice/likeness必须有Site-local、purpose/model/public/remix scope匹配的 ConsentEvidence；minor/age-unknown、public figure、
  deceptive/election-sensitive内容走Platform最保护 baseline，普通checkbox/guardian不能覆盖absolute deny。
- 多人画面必须由用户或经review的binding明确目标；confidence不足不自动选择最大脸。
- provider alignment、口型同步、声音内容和字幕相互独立验证；超过发布 tolerance 进入partial/failed/review，不标completed。
- 音轨被替换、重采样或字幕被修改时旧alignment失效；创建新revision，不silent reuse。

### 9.5 Upscale and frame interpolation

- upscale 冻结 exact width/height或scale、aspect、pixel aspect、color/HDR、detail/face enhancement policy。face enhancement
  不得默认改变身份特征，并受likeness gate。
- interpolation 冻结 source timebase、target rational fps、duration-preservation、motion/scene-cut policy与audio treatment。
- 不能通过重复/丢弃/补帧改变 authoritative duration；任何 cadence、scene cut、A/V drift 超tolerance进入validation failure。
- Provider返回错误dimensions/fps/duration/color/audio mapping时保持finalizing/failed；只重试validation/Artifact receipt，不rerun effect。

## 10. Draft、Quote、Submit and Shared Job Lifecycle

- 空 Draft/Storyboard 不 reserve Credit。autosave 按 `(draftId, baseRevision, clientMutationId, requestDigest)` CAS；并发产生
  explicit conflict/fork/merge，不last-write-wins覆盖 storyboard、shot、source、mask、tracks或字幕。
- Quote 基于canonical revision/spec，冻结duration、pixels、frames、candidate/shot count、track处理、family、quality、
  ModelOption、RatingPolicy和maximum reservation ceiling；client不提供price micros。
- price、policy、ModelOption、source eligibility、rights/consent、material timebase或参数变化时返回
  `reconfirmation_required`与safe diff；确认前不创建 executable Job/effect。
- Direct Web与Agent使用相同SubmitOperation identity、spec digest、root Hold、Job plan、Attempt、Artifact、Trust和Usage合同；
  agent delegated allocation只作为root Hold受限child allocation，不创建第二Hold。
- submit、queue、lease、callback、cancel、unknown、partial与finalization严格继承PRD-07。浏览器关闭/刷新不cancel Job。
- unknown submission/outcome只可attach/query/reconcile/wait/Support；不能自动或手动通过新Provider、ModelOption、Attempt、
  Operation绕过同一uncertain effect。
- finalizer只补Blob/Artifact/Decision/Usage/notification receipts，绝不rerun Provider。completed required output必须有
  exact media validation、ArtifactVersion和AttemptUsageEvidence receipts；Rating outage可completed/cost_pending。
- cancel是intent直到canonical owner证明；已完成shot/candidate保留，queued无effect slot可释放，submitted/unknown继续reconcile。

## 11. Trust、Rights、Consent、Minor and Publication

- input prompt、Storyboard、source/reference、face/voice、mask edit、output和export/publication分别执行PRD-16 stage gate。
- rights bundle按source/master recording、composition/music、performance、voice、likeness、script/text、location/property、
  trademark、territory、term、commercial/public/remix/training/sublicense拆分；普通“拥有版权”声明不是充分证据。
- 每个enabled family发布 `VideoRightsRequirementMatrixRevision`，按source/reference role × family × output kind × private/
  download/export/public/remix/training × territory冻结required evidence、deny/review和disclosure；矩阵缺失的Site/Profile fail closed。
- Asset/Artifact owner为exact source interval创建purpose-bound `DerivedVideoInputVersion`，冻结Site、source+track、Mapping、range、
  representation checksum、TTL、revoke epoch与allowed Deployment；Gateway不得任意range-read整库、扩大purpose或复用过期输入。
- character/scene continuity不能将他人肖像、声音、作品或地点权利扩展到新shot、公开用途或训练用途。
- minor/age-unknown的sexualized likeness、voice clone、deepfake、public remix和高风险训练材料按Platform baseline deny或
  specialist review；Site不能放宽，guardian不能覆盖absolute deny。
- output的private preview、private download、export、public Share、SEO/remix各自授权；生成成功不等于可发布。
- deceptive/synthetic-media disclosure、watermark与provenance requirement按policy冻结；缺失/损坏时阻断需要它的delivery。
- ProviderSafetyFact、face detector、copyright/near-match信号只是evidence；Trust Decision才是canonical authority。
- consent/rights/restriction epoch revoke 后不发新effect/token；已提交effect只finalize到quarantine/reconcile。Appeal产生新
  Decision，不覆盖历史；overturn也要重新满足独立rights/consent/a11y/publication gate。
- preview、download、export、Share、remix与public delivery使用短期purpose-bound `PublicationAuthorization`，冻结siteId、
  ArtifactVersion、audience与policy/rights/consent/restriction epochs；每次mint/受控访问复验，旧token、Appeal或CDN缓存不复活。
- restricted frame、audio、subtitle或candidate不得出现在thumbnail、filmstrip、player、notification、receipt或普通Support。

## 12. Artifact、Lineage、Version and Export

- 每个allowed candidate/shot/sequence/rendition创建immutable ArtifactVersion，记录parent/source、Storyboard/ShotPlan/
  Timeline/Track revisions、Operation/Job/Attempt/Candidate、model/adapter/policy/rights/consent、media facts和provenance。
- source、shot、sequence、upscale/interpolation/rendition形成有向无环lineage；相同bytes可按Blob policy去重，但不同
  candidate/Operation/rights scope绝不合并ArtifactVersion或ownership。
- “Continue editing / Use as source / Extend / Reframe / Inpaint / Lip-sync / Upscale”创建新DraftRevision和Operation。
- compare支持shot/sequence A/B、同步或单独播放、frame/timecode/metadata/continuity/cost diff；selection不修改Artifact。
- export profile冻结container、codec、dimensions、rational fps、bitrate/quality、color/HDR、audio codec/sample/channel/
  loudness、caption/audio-description tracks、metadata、watermark/disclosure、rights和estimated cost。
- format conversion、mixdown、caption mux、thumbnail/proxy、多比例交付创建RenditionJob；不重跑generation或改source。
- delivery每次验证Site/subject/Project/current rights/consent/restriction/a11y/TTL；storage URL不是长期ref。
- response丢失按same ExportRequest/Artifact查询；delivery过期可重建交付，不重新生成source。

## 13. Accessibility、Desktop and Mobile UX

### Desktop

- Desktop 提供Storyboard grid、Shot inspector、source/reference panel、multitrack Timeline、player和Job/Candidate panel；
  layout可调整但focus order、reading anchor和logical IDs稳定。
- drag/drop、scrub、trim handles、mask、crop和track reorder都有keyboard、数值、列表/表格和undo/redo等价路径。
- player支持play/pause/seek、速度、音量、mute、loop range、frame step（适用时）、caption/audio-description选择和状态播报。

### Mobile

- Mobile P0支持创建/编辑prompt、Storyboard/Shot list、选择source/reference、结构化timecode/range、track/cue list、Quote/
  confirm、monitor/cancel/recovery、review partial、playback、基础export。操作使用逐步sheet而非缩小桌面Timeline。
- 精细mask、关键帧或多轨P1若该移动variant未具备语义等价路径，Profile必须标明该variant `not_enableable`，提供保存并在
  desktop继续的安全handoff；不得显示可进入却不能完成的控件。P0 complete process不得依赖切换设备。
- touch target、orientation、virtual keyboard/IME、background/reconnect、低带宽proxy和data-use提示必须认证；后台不cancel Job。

### Accessible alternatives and media

- Storyboard有有序文本/list/table替代；每shot有描述、角色/场景、时长、状态与操作。
- Timeline有track/clip/cue表、exact start/end、source range、order、sync和数值step controls；视觉filmstrip/waveform非唯一入口。
- spatial mask/reframe有对象/区域列表、x/y/width/height、frame interval、polarity和关键点数值路径；输出相同OperationSpec。
- 所有预录媒体按MediaAccessibilityRevision逐项提供适用captions、time-based alternative、audio description、transcript/
  text alternative。transcript不替代SC 1.2.5；未经语言/内容review的自动结果不能作为conformance evidence。
- progress不逐帧/逐percent播报；阶段、partial、unknown、费用和CTA以可查询live region更新，terminal只播报一次。
- 任一enabled full page、state、responsive variant和complete process的适用WCAG 2.2 A/AA failure阻断SiteRelease。

## 14. Cost Semantics and User-visible States

Quote dimensions至少覆盖output actual seconds、pixels、rational fps、candidate/shot count、family、track/字幕/音频处理、
reference analysis、quality和rendition。Provider cost不等于customer charge；pre-effect deny、post-effect quarantine、partial
shot、preview retention、cancel、unknown、appeal overturn分别冻结ChargeTreatmentPolicy。unknown不释放committed allocation。

| State | Meaning | RecoveryAction |
|---|---|---|
| `draft_saved` / `draft_conflict` | Storyboard/Shot/Timeline revision已保存或并发分叉 | continue/fork/compare/explicit merge |
| `source_or_timebase_invalid` | source/mapping/range/revision不兼容 | reselect/remap/change parameters |
| `rights_or_consent_required` | 素材/likeness/voice/minor evidence不足 | provide evidence/remove/change/cancel |
| `quote_ready` / `reconfirmation_required` | estimate有效或material条件变化 | confirm/requote/change parameters |
| `admission_pending` / `waiting_interaction` | 校验或需用户输入 | wait/query same identity/provide input/reauth |
| `queued` / `delayed` | 已接受排队或超过正常age | leave/wait/cancel/page owner after SLA |
| `running` / `previewing` | effect可能已提交；preview非final | view/leave/cancel request |
| `cancel_requested` | cancel outcome未证明 | wait/query；不重复或宣称canceled |
| `unknown` / `reconciling` | submission/outcome不明 | wait/query/Support；retry/fallback disabled |
| `finalizing` | 验证媒体并创建Trust/Artifact/Usage receipts | wait；only finalizer retry |
| `completed` / `partial` | 全部或部分合格shot/candidate可用 | compare/edit/export/new explicit Operation |
| `restricted` | candidate/track/cue不可消费/发布 | safe reason/appeal/delete where allowed |
| `failed` / `canceled` | canonical owner确认终态 | safe newOperation/Support；显示cost事实 |
| `cost_pending` / `correction_pending` | 结果/usage存在，结算或纠错未完 | use where allowed/wait/view receipt |
| `export_blocked` | Artifact存在但rights/disclosure/a11y/profile不足 | remedy/appeal/change export profile |

每个状态必须显示owner、freshness、费用事实、retry safety、预计等待或deadline、可用CTA和Site-bound Support deep link；
同一状态不得同时代表“安全重试”和“可能重复Provider effect”。

## 15. Failure、Recovery and Idempotency

| Scenario | Expected behavior |
|---|---|
| 双击Submit或response丢失 | same key+digest返回同Operation/Job/rootHold；different digest冲突 |
| autosave两端并发 | CAS conflict/fork/merge；不覆盖shot、track、mask或字幕 |
| source在Quote后换revision | reconfirm exact diff；不以latest替换 |
| browser显示29.97、source为VFR | exact rational/PTS mapping authority；不按rounded seconds选帧 |
| lease过期但Provider已收到 | higher epoch attach/query/reconcile；不rerun |
| callback重复、乱序、late | append/reducer幂等；一个Attempt/candidate/finalization |
| Provider 100%后timeout | progress非terminal；进入unknown/reconcile |
| cancel与success竞态 | 两facts保留；late output仍按Artifact/Trust/Usage/charge收口 |
| 8 shots中5成功、1restricted、2unknown | sequence partial；逐shot身份/Decision/Usage，unknown禁retry |
| finalizer在Blob/Artifact/Usage处crash | 重放缺失receipt；不rerunProvider、不重复Artifact/capture |
| lip-sync audio revision变更 | old alignment invalid；reconfirm/newOperation，不silent reuse |
| SiteRelease rollback mid-Job | frozen spec完成；新download/export按current policy |
| consent/rights queued后revoke | pre-effect拒绝；submitted output quarantine/reconcile |
| subtitle provider失败 | video candidate不被伪装为fully accessible；remediation/export blocked |
| mobile后台/网络切换 | Job继续；return query same owner projection，不触发effect |
| source delete与active lineage并发 | 阻止new grants；reference/retention disposition，不破坏历史Artifact |

Idempotency minimum：Draft mutation、SubmitOperation、Provider operation key、callback fact、Candidate slot、Blob ingest、
CreateArtifactVersion、AttemptUsageEvidence、ExportRequest、Notification和operator command均有稳定identity+request digest；
同identity不同digest拒绝。任何unknown只可由canonical query/reconciliation或published irreconcilable policy收口。

## 16. Admin、Support and Operations

- Video Console在通用Job timeline增加family、Storyboard/ShotPlan/Timeline/timebase/source digest、continuity、mask、face/voice、
  candidate/track/cue、media validation、Trust、Artifact/Usage和export eligibility；默认不播放或展示原内容。
- raw video/audio/likeness/rightsevidence访问使用Site/resource/field/action/TTL-bound ContentAccessGrant，默认blur/mute/
  frame-sample/redacted transcript，specialist role和必要maker-checker；Support不可扩权或download。
- typed commands：`ReconcileUnknownVideoAttempt`、`RetryVideoFinalization`、`InvalidateTimelineMapping`、
  `InvalidateMaskOrAlignment`、`StartVideoOutputReevaluation`、`RebuildVideoProjection`、`RevokePlaybackOrExport`、
  `OpenRightsOrLikenessReview`。禁止mark succeeded/completed/clean、改Usage/Credit或直接rerunProvider。
- 每个command登记role、Site/resource、reason、risk/step-up/maker-checker、expectedVersion、idempotency、PII masking、audit、
  user notification、SLA、receipt和recovery runbook。
- monitoring覆盖queue/fairness、attempt/callback/reconciliation、timebase/mapping、duration/fps/A-V drift、continuity、lip-sync、
  media validation、partial shots、Artifact/Usage/Hold lag、restriction/appeal、export/a11y，按必要revision切分。
- runbooks覆盖long queue、Provider outage/unknown、VFR/timecode regression、mask mapping、A/V drift、late callback、preview leak、
  consent revoke、Artifact/Usage outage、caption remediation、CDN/token revoke和backup/restore。

## 17. Acceptance Criteria

### AC-VID-01 — Family and source binding are explicit

```gherkin
Given text, image, video, extend, inpaint and lip-sync have different input contracts
When a Video Draft is submitted
Then exactly one published OperationDefinition validates the complete typed spec and exact source revisions
And no arbitrary Provider payload, mutable latest pointer or silently ignored parameter reaches execution
```

### AC-VID-02 — Storyboard and shot partials remain independent

```gherkin
Given a Shot Plan contains allowed, restricted, failed and unknown shot candidates
When Job finalization and sequence projection run
Then every shot keeps a stable Candidate, Decision, Artifact, Usage and cost identity
And allowed shots remain usable while restricted content stays hidden and unknown effects cannot retry
```

### AC-VID-03 — Exact timebase selects the intended interval

```gherkin
Given a variable-frame-rate source, a normalized proxy and a rounded player time display differ
When the user submits extend, reframe, inpaint or interpolation
Then the source revision, PTS mapping, rational ProjectTimebase and exact half-open range are frozen
And an ambiguous, stale or out-of-range mapping fails before effect rather than selecting a nearby frame
```

### AC-VID-04 — Source edits never overwrite history

```gherkin
Given a user transforms one ArtifactVersion through video-to-video, extend, inpaint and upscale
When each Operation completes
Then every result is a new immutable ArtifactVersion linked to its exact parent and revisions
And source bytes, Timeline, rights, Share and settled Usage remain unchanged
```

### AC-VID-05 — Continuity claims are truthful

```gherkin
Given a character and scene continuity request contains invariants and preferences
When the selected ModelOption lacks certified support for one dimension
Then the invariant fails or requires a compatible option and the preference is disclosed as best effort
And no UI, Artifact metadata or export claims guaranteed identity or scene consistency without evidence
```

### AC-VID-06 — Lip-sync requires exact consent and alignment

```gherkin
Given video shows a represented person and dialogue uses a voice binding
When lip-sync is admitted
Then face, voice, purpose, model, public/remix, age and consent scopes are current and Site-local
And the exact video, audio, language and alignment revisions are frozen
And missing consent, ambiguous target person or stale alignment denies before Provider effect
```

### AC-VID-07 — Minor and age-unknown high-risk media fails closed

```gherkin
Given a represented subject is a minor or age-unknown
When sexualized likeness, voice clone, deepfake or public remix is requested
Then Platform policy denies or routes the frozen specialist review path
And Site policy, ordinary checkbox or guardian evidence cannot override an absolute deny
```

### AC-VID-08 — Unknown outcome cannot be bypassed

```gherkin
Given Provider submission or outcome is unknown for one shot or sequence
When automation, a worker or the user requests retry with another ModelOption or Provider
Then no new effect replays the uncertain operation
And the same effect identity is queried until reconciled or closed by the published irreconcilable policy
```

### AC-VID-09 — Cancel preserves completed work

```gherkin
Given some shots completed while others are queued, submitted or unknown
When cancel is requested
Then completed shots and their Usage remain intact
And every remaining slot follows authoritative cancel or reconciliation without a fabricated sequence-wide canceled state
```

### AC-VID-10 — Finalization validates media without regeneration

```gherkin
Given Provider reports success but dimensions, frame rate, duration, A/V sync, codec, checksum or provenance is invalid
When finalization runs
Then no ready completed Artifact or export is exposed
And recovery retries validation, Blob, Trust, Artifact and Usage receipts without rerunning generation
```

### AC-VID-11 — Audio and subtitle tracks remain aligned and distinct

```gherkin
Given dialogue audio is resampled and captions are edited after automatic alignment
When a Timeline rendition is prepared
Then exact sample/tick mappings and the newest reviewed cue revisions are used
And transcript, captions and audio description remain distinct eligibility objects
And stale alignment cannot silently produce a published rendition
```

### AC-VID-12 — Accessible timeline path is equivalent

```gherkin
Given a non-pointer user orders shots, trims a clip, selects a frame range, edits a subtitle and submits reframe
When structured shot, track, cue and numeric time controls are used
Then they produce the same canonical VideoOperationSpec as visual storyboard and Timeline interactions
And focus, reading anchor, player, progress and recovery satisfy every applicable WCAG A/AA criterion
```

### AC-VID-13 — Media alternatives gate publication

```gherkin
Given prerecorded synchronized video has captions and a transcript but lacks required audio description
When export, Share or SiteRelease certification evaluates it
Then the transcript does not substitute for the missing audio description
And publication and conforming export remain blocked while the private Artifact and cost history stay intact
```

### AC-VID-14 — Agent and Direct share one spine

```gherkin
Given Chat Agent and Video Studio submit equivalent certified VideoOperationSpecs
When both execute
Then their Job, Attempt, Candidate, Artifact, Trust, Usage and Cost contracts are identical
And GA receives only an opaque Job handle without Video Provider branches, a second Hold or changed terminal semantics
```

### AC-VID-15 — Mobile long-job recovery is owner-driven

```gherkin
Given a user submits on mobile, backgrounds the browser and later opens the Job on desktop
When projections are rebuilt from owner receipts
Then the same Operation, shot candidates, progress, cost and Artifact lineage are shown
And reconnect triggers no Provider, finalizer or settlement effect
```

### AC-VID-16 — Private result does not imply publication

```gherkin
Given a video is allowed for private preview but lacks current rights, consent, disclosure or accessibility eligibility
When export, Share, remix or public delivery is requested
Then no PublicationAuthorization or delivery token is issued
And the Artifact, original Decision and cost remain immutable with an exact safe remedy or appeal path
```

### AC-VID-17 — Reframe and inpaint coordinates are deterministic

```gherkin
Given a rotated source, pixel-aspect mapping, zoomed proxy and spatial-temporal mask
When reframe or inpaint is submitted
Then logical source coordinates, frame interval, transforms, mask polarity and revisions are frozen once
And golden validation edits the intended region or rejects before effect without using viewport pixels
```

### AC-VID-18 — Upscale and interpolation preserve authority

```gherkin
Given upscale or interpolation returns a different duration, cadence, color profile or A/V mapping than requested
When output validation runs
Then the result remains finalizing, partial or failed under the published tolerance
And no corrected-looking metadata fabricates compliance or rewrites the source timeline
```

### AC-VID-19 — Cross-Site video references are confined

```gherkin
Given Site A owns a source, Timeline, Mapping, Storyboard, Track, rights or Consent reference
When Site B submits an Operation, callback or operator command containing any such reference
Then authorization rejects before metadata disclosure, bytes, preview, export or Provider effect
And no existence, timing, rights, policy or content signal from Site A is returned
```

### AC-VID-20 — Source snapshot remains revision-coherent

```gherkin
Given a Quote freezes source, Mapping, Timeline, Storyboard, ShotPlan, mask, audio, subtitle and alignment revisions
When any dependency head changes before submit or rendition
Then snapshot CAS or coherence digest validation fails and a new diff and Quote are required
And no current-head object or mixed revision set is read implicitly
```

### AC-VID-21 — Track and clip restrictions survive composition

```gherkin
Given one audio, subtitle, character or clip contribution is restricted while the sequence candidate is otherwise allowed
When preview, export, remix or publication is requested
Then the most-restrictive current Decision, rights and consent applies for that purpose
And candidate-level allow cannot expose the contribution while Usage and cost allocations remain auditable
```

### AC-VID-22 — Assistant and effect roles are separately authorized

```gherkin
Given a user requests assistant help before generation, edit, lip-sync or rendition
When the assistant proposes Storyboard, ShotPlan, Timeline or subtitle changes
Then it runs as an explicit ModelInvocation with its own provenance, Usage and charge policy
And submit never invokes it implicitly or mixes its Attempt with any media effect settlement
```

### AC-VID-23 — Derived source input is purpose-bound

```gherkin
Given an exact source interval is prepared for one Site, Operation and Deployment
When a caller requests another range, purpose, Deployment or an expired input
Then the DerivedVideoInputVersion grant is rejected before bytes or Provider effect
And Gateway cannot range-read the source library or widen the grant
```

### AC-VID-24 — Publication epoch race fails closed

```gherkin
Given a video was eligible when a PublicationAuthorization was issued
When rights, consent, accessibility or restriction epoch changes before token mint or controlled access
Then the stale authorization is rejected and origin access remains revoked
And no Appeal, rebuilt Share or cached token restores the old use
```

### AC-VID-25 — Cancel scope is truthful

```gherkin
Given the certified Provider can cancel only an entire Attempt containing multiple shot or candidate slots
When one slot requests cancellation
Then Web does not claim slot-level canceled certainty or discard late canonical facts
And every output, Usage and charge reconciles under the frozen attempt-level cancel policy
```

## 18. Analytics and Product Operations

Required low-sensitivity events：draft revision/conflict、storyboard/shot/timeline mutation、quote/reconfirmation、submit identity、
queue/delay/progress freshness、cancel intent/outcome、unknown/reconciliation、candidate/shot terminal、finalization receipt、
timebase/mapping validation、rights/consent interaction、restriction/appeal、export eligibility、mobile/desktop resume和a11y recovery。

事件不得包含prompt原文、raw frame/audio/subtitle、face/voice embedding、rights evidence、userId、filename、storage key、
Provider raw payload或secret。使用opaque refs和低基数reason category；analytics失败不改变Operation/Trust/Cost authority。

## 19. Dependencies、Risks and Milestones

| Dependency/Risk | Owner | Mitigation |
|---|---|---|
| PRD-07 Job/Cost spine未批准或未认证 | Studio Platform Product Lead | Video不可独建runtime；Profile保持disabled |
| Asset/Artifact source与lineage合同缺口 | Asset/Artifact owners | exact version grants、receipt和negative certification |
| VFR/timebase/codec差异造成帧漂移 | Video ML + QA | rational mapping、golden corpus、real media matrix |
| 角色一致性被误解为身份保证 | Video PM + Trust | invariant/preference分级、evidence、文案和UAT |
| lip-sync/likeness被滥用 | Trust/Legal | Site-local consent、age/publication gate、specialist review |
| 长Job与昂贵effect重复 | Job Runtime/SRE | effect ledger、unknown no-retry、chaos certification |
| 自动字幕造成虚假可访问性 | Accessibility/Localization | unreviewed状态、人工质量证据、publish hard gate |
| 移动端专业控件不可完成 | Web/A11y | structured flow、variant inventory、完整流程认证 |
| GA角色扩展被误当runtime授权 | GA owner | assignment-only boundary；专项审批门与negative architecture test |

Milestones：

1. Product review：冻结VID-01、P0/P1 family、state/recovery、rights与a11y合同。
2. Child architecture Spec：冻结schema、timebase/source mapping、role assignment、Job/Artifact/Trust接口和clean cut。
3. Provider certification：逐family/ModelOption验证输入、输出、idempotency、retrieval、cancel、unknown和cost evidence。
4. Desktop/mobile UAT：Storyboard、Timeline、long Job、partial/unknown、structured alternative和media alternatives。
5. Site/Profile delta Certification：完成安全、费用、运营、灾难恢复、cross-Site与disabled negative matrix后才可enable。

## 20. Verification and Release Gates

- Schema/golden：每family typed schema、source revision、rational timebase、VFR/PTS、drop-frame display、frame/sample/tick mapping、
  mask/reframe坐标、lip-sync、dimensions/fps/color/audio/caption output；unsupported parameter fail-before-effect。
- Property：half-open ranges、mapping round-trip、Timeline/lineage DAG、candidate/shot/track isolation、submit uniqueness、lease fencing、
  reducer/cancel race、finalization receipts、Usage/correction invariants。
- Adversarial：corrupt/polyglot/container bomb、metadata/subtitle injection、malicious codec/parser budget、bidi filename/cue、
  face/voice spoof、minor/deepfake/public figure、cross-Site refs和callback spoof。
- Integration/chaos：real object storage、queue、fake/sandbox Provider、callback duplicate/out-of-order/late、lease steal、
  queue/Provider/Trust/Artifact/Usage outage、consent revoke、Site rollback、browser disconnect、backup/restore。
- UX/a11y：desktop/mobile、keyboard、screen reader、magnification、speech、switch、RTL/IME、Storyboard/Timeline structured parity、
  player、caption/transcript/audio-description、zoom/reflow/reduced motion和complete process。
- Operations：long queue/load/soak、fairness、unknown deadline、Hold/finalization aging、operator command auth、JIT evidence access、
  alert→runbook→receipt、rolling deploy/rollback和DR restore。
- Traceability：Profile→VID-01 revision→P0/P1 requirement→contract→test→evidence→owner 100%；disabled route/API/Admin/
  assignment四层negative evidence完整。

内部批准还要求：

- 每个enabled family已发布OperationDefinition、runtime roles、VideoRightsRequirementMatrix、cancel scope、ChargeTreatment、
  output validator、fallback equivalence与real Provider sandbox certification，缺任一项即fail closed。
- 两Site交叉source/Timeline/Mapping/Storyboard/Track/rights/consent/callback负向矩阵、VFR/PTS/timebase golden corpus、
  minor/likeness/lip-sync Legal matrix、partial/cancel/unknown/finalizer chaos、Usage/root Hold守恒和Browser/AT认证全部通过。
- Legal已为目标launch jurisdiction签发rights、minor、deceptive/election-sensitive、notice、takedown与retention matrix；
  缺地区证据不得enable对应Site/Profile/family。

No-Go：万能Video payload/任意workflow；mutable source/latest或浮点秒权威；timebase/mask/alignment无证据；source overwrite；
candidate/shot/track串位；unknown retry/fallback；finalizer rerunProvider；角色一致性虚假保证；lip-sync缺consent/age gate；
private allow绕过export/share；自动字幕冒充conforming；移动或Timeline pointer-only；GA出现Video Provider业务分支、第二套
Job/Asset/Trust/Cost或任何未专项批准的runtime语义变更。

Release gate：P0全部关闭；P1只有在其独立Definition、Provider、Trust/Legal、A11y、Support和delta Certification证据齐全
后可逐项启用。任何 cross-Site、重复effect/charge、unknown误重试、缺rights/consent、minor absolute deny绕过、required
Artifact/Usage receipt缺失或适用WCAG 2.2 A/AA failure均不可accepted-risk放行，只能修复或关闭Surface/family。

## 21. Related Documents and Approval Boundary

- [PRD-00 Launch Profile](2026-07-25-prd-00-launch-profile-and-journey-contract.md)
- [PRD-06 Asset](2026-07-25-prd-06-asset-intake-and-attachment-safety.md)
- [PRD-07 Studio Common](2026-07-25-prd-07-studio-common-job-and-cost-ux.md)
- [PRD-08I Image Studio](2026-07-25-prd-08i-image-studio.md)
- [PRD-08M Music Studio](2026-07-25-prd-08m-music-studio.md)
- [PRD-14 Accessibility](2026-07-25-prd-14-localization-and-accessibility.md)
- [PRD-16 Trust](2026-07-25-prd-16-trust-content-safety-and-media-rights.md)
- [Product Requirements Governance and Registry](2026-07-25-product-requirements-governance-and-prd-registry-design.md)

本 PRD 只有在 Video Studio Product Lead、Studio Platform Product Lead、Video ML、Job/Asset/Artifact/Model、Trust/Legal、
Accessibility、Web、Support/SRE与QA完成各自证据签署后才能退出internal review。本文批准仍不授权业务实现；任何实现计划
必须另行批准。本文不修改或授权修改GA runtime；命中GA graph、assembly、tool、checkpoint、effect、Handoff、namespace、
terminal或主assistant runtime语义的提案必须停止并进入专项书面审批。
