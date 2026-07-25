---
artifact: product-requirements-document
prdId: PRD-08M
version: "1.0"
created: 2026-07-25
status: internal-review-active
scope: music-studio-lyrics-instrumental-reference-timeline-generate-retake-repaint-extend-remix-stem-export
accountableProductRole: Music Studio Product Lead
mandatoryCosigners: [Music ML, Job Runtime, Asset, Artifact, Model Platform, Trust, Rights, Accessibility, Web, Support, QA]
engineeringOwner: team:music-studio-engineering
qaOwner: team:music-studio-quality
supportOperationsOwner: team:music-studio-operations
namedOwnerAssignmentStatus: assigned-team-responsibility-ids
implementationAuthorized: false
gaRuntimeSemanticChangeAuthorized: false
---

# PRD-08M：Music Studio

## 1. Overview

### Problem

Music 不是“输入 prompt 输出 mp3”。完整歌曲包含歌词结构、语言、演唱、旋律、和声、节奏、编曲、音色、master，
用户还需要试听、extend、局部 repaint、歌词修改、remix、retake、stem 和多格式导出。reference audio 可能只提供
节奏/旋律/风格/声音/歌词片段，每一种用途的版权、表演、声音肖像和允许范围不同。若统一成一个宽泛 reference 或
“我拥有版权” checkbox，会错误授权 voice clone、sample、composition/master/performance；若时间轴只按播放器秒数
临场计算，extend/repaint 的 segment、歌词对齐和版本 lineage 会在转码/采样率变化后漂移。

### Solution

在 PRD-07 通用 Job 主链上建立版本化 Music Operation family：`text_to_music`、`lyrics_to_song`、`instrumental`、
`retake`、`repaint_segment`、`edit_lyrics`、`extend`、`remix`、`generate_stem`、`separate_stems` 与 `master_rendition`。
Studio Draft 以结构化 SongPlan、LyricsRevision、TimelineRevision、MusicReferenceBinding 和 Mix/Export profile表达用户
意图；每次提交编译 immutable MusicOperationSpec。每个结果创建新的 ArtifactVersion/TrackSet lineage，Direct Studio
与 Agent tool 复用同一 Job、Model Gateway、Trust、Usage、Artifact 和 Cost 链。

### Users and stories

| ID | User story | Priority |
|---|---|---|
| MUS-US-01 | 用户可生成纯音乐或带结构化歌词的完整音乐候选，并比较段落与整体结果 | P0 if-enabled |
| MUS-US-02 | 用户可上传/选择 reference，并明确它用于 melody、rhythm、style、voice、sample 还是 continuation source | P0 |
| MUS-US-03 | 用户可在时间轴选择准确片段做 retake/repaint/歌词修改或左右 extend，旧版本不被覆盖 | P0 |
| MUS-US-04 | 用户可 remix、生成/分离 stem、试听不同 mix/master，并理解能力限制与费用 | P0 |
| MUS-US-05 | 用户可看到歌词语言、caption/transcript、rights/disclosure、候选/track和导出资格 | P0 |
| MUS-US-06 | 键盘、屏幕阅读器和非波形用户可通过 segment/track/list/timecode 完成等价流程 | P0 |

## 2. Goals、Metrics and Non-Goals

### Goals

1. operation family、reference role、track/segment/timebase 与 rights basis 明确，不使用万能 audio payload。
2. composition/master/performance/sample/lyrics/voice/likeness 权利逐项检查，普通 assertion 不越权。
3. 时间轴、extend/repaint、lyrics alignment 绑定 immutable source revision 与 rational sample/time mapping。
4. candidate、track/stem、Artifact、Usage、Trust、Cost 独立且可从 Job receipts重建。
5. player/waveform/timeline有完整结构化替代、caption/transcript/lyrics和媒体无障碍合同。
6. generated、private playback、download、stem export、commercial/public use分别授权。

### Success Metrics

| Metric | Target |
|---|---:|
| reference role/right type 未声明仍触发 Provider effect | 0 |
| voice/likeness operation 缺有效 ConsentEvidence | 0 |
| segment/timebase漂移导致错误repaint/extend | 0 certification failures |
| candidate/track/stem Artifact、Usage、Decision、charge串位 | 0 |
| Music/rights/consent/timeline对象跨 Site 引用成功 | 0 |
| assistant/generation Usage、track eligibility 或 stale MixRevision 串位 | 0 |
| AudioTimeMappingRevision mismatch仍允许submit | 0 |
| source/master/lyrics revision被派生操作原地覆盖 | 0 |
| Provider percent/preview 被误报为final track | 0 |
| 生成成功被误报为商业/公开/可stem导出授权 | 0 |
| required caption/transcript/lyrics/audio-description equivalent缺失仍发布 | 0 |
| waveform pointer-only blocker | 0；A/AA failure阻断SiteRelease |

### Non-Goals

- V1 不提供完整 DAW、MIDI editor、plugin host、实时多人录音、live performance或用户自训练模型。
- 不承诺生成内容版权归属、原创性、商业许可或不与已有作品相似；显示已批准policy与rights状态。
- 不允许上传任意模型/LoRA、访问Provider底层scheduler/CFG、直接操作GPU或提交任意audio workflow graph。
- 不把stem separation输出误称为原始multitrack recording；它是derived estimate。
- 不承诺不同Model/Deployment/adapter/seed产生相同歌曲，也不把reference style当可复制艺人身份。
- Music Studio不拥有Job、Provider、Trust Decision、Credit或Artifact binary。
- 不修改GA；Agent获得opaque Job handle。

## 3. Canonical Product Objects

```text
MusicDraftRevision
  immutable siteId / draftRef / operationFamily / SongPlanRevision / LyricsRevision?
  MusicTimelineRevision? / referenceBindings[] / sourceTrackSetRevisionRef?
  ModelOption / candidateCount / parameterSet / mix+export intent

SongPlanRevision
  immutable siteId / language / vocalMode=instrumental|vocal|mixed / durationIntent
  genre+mood+instrumentation+tempo intent / ordered section descriptors

VoiceIntentRevision / VoiceSlot
  immutable siteId / mode=generic_synthetic|non_identifiable|represented_subject|clone|ensemble
  subject+voice binding refs / role+language / age eligibility+consent refs / persona+deceptive-use intent

LyricsRevision
  immutable siteId / contentLanguage / ordered lyric sections / lines / pronunciation annotations
  rights+author refs / explicit-content classification / alignment status

MusicTimelineRevision
  immutable siteId / typed sourceMediaVersionRef=AssetVersionRef|ArtifactVersionRef
  canonical sampleRate / channel layout / exact duration samples
  sections / segment markers / lyric alignment refs / timebase revision

TempoMapRevision
  immutable siteId / TimelineRevision / tempo+time-signature segments / beat-bar projection / evidence+confidence

AudioTimeMappingRevision
  immutable siteId / source media+track / canonical PCM representation digest / source+canonical sample origins
  exact duration / codec priming+padding / piecewise rational transforms / rounding+channel mapping / tool revision

LyricsAlignmentRevision
  immutable siteId / exact source media+track / Timeline+Mapping+Lyrics revisions / segments+confidence+evidence class

MusicReferenceBinding
  immutable siteId / assetOrArtifactVersion / role=melody|rhythm|style|voice|sample|continuation|mix_context
  exact segment / influence class / rights+consent refs / territory+use+term

MusicOperationSpec
  immutable siteId / family / MusicSourceSnapshotRevision + explicit deltas / typed parameters
  assistant+generation role requirements / candidate+track output contract / quote dimensions

MusicSourceSnapshotRevision
  immutable siteId / source media+TrackSet+track IDs / Timeline+Mapping / SongPlan+VoiceIntent
  Lyrics+LyricsAlignment / MixRevision / rights+consent epochs / coherence digest

MixRevision
  immutable siteId / source TrackSet / ordered track IDs / gain+mute+pan / render profile / revision digest

TrackSet / TrackDescriptor
  immutable siteId / stable trackId / mix|vocal|instrumental|stem / instrumentOrRole / channel layout / sync origin
  parent+contribution manifest / ArtifactVersion / derived class / Decision+RightsSnapshot+ConsentEpoch refs
  UsageAllocation+costProjection refs / per-purpose playback+download+stem+commercial+public eligibility

MusicCandidateResult
  immutable siteId / candidateId / TrackSet / ArtifactVersion refs / duration+audio metadata
  lyrics alignment / owner-issued Decision+rights+usage+cost projection refs / playback+export eligibility
```

- `music.assistant` 理解意图、建议SongPlan/lyrics structure/parameters；`music.generation`执行真实音频生成。Stem、rendition、
  quality、moderation可有独立发布 role，但每个 family/stage 只能使用 OperationDefinition 明示的 required/optional roles。
- ModelOption覆盖产品role，不暴露Provider/Deployment。SiteRelease compile只要求该 enabled family 的完整 role set；纯
  rendition/stem operation不因未使用assistant而失败，也不能临场补默认role。
- source audio与歌词/plan/timeline分别版本化；同一音频的不同rights/use不因contentHash合并。
- 所有 Music 业务对象、identity、唯一键、队列分区、callback mapping 与引用都冻结 immutable `siteId`。跨 Site 即使
  content hash、用户邮箱、Provider operation ID 或 consent subject 相同也不继承对象、权利、授权或存在性信号。

## 4. Operation Families

| Family | Required inputs | Output contract |
|---|---|---|
| `text_to_music` | SongPlan，lyrics optional | one or more complete mix candidates |
| `lyrics_to_song` | structured Lyrics + vocal SongPlan | mix plus required lyrics/alignment metadata |
| `instrumental` | instrumental plan | no implied lyrics/vocal/voice identity |
| `retake` | source version + preservation/variation intent | related candidate preserving declared attributes |
| `repaint_segment` | source Timeline + exact segment + replacement intent | new complete version with localized changed region |
| `edit_lyrics` | source + aligned segment + new LyricsRevision | new version；preserve melody/vocal only if certified |
| `extend` | source Timeline + left/right duration/section intent | new longer version with source lineage |
| `remix` | source + new style/arrangement/mix intent | transformed complete version；not a mere rendition |
| `generate_stem` | mix/context + requested instrument/role | complementary or isolated derived track |
| `separate_stems` | source mix + published stem set | derived estimated TrackSet |
| `master_rendition` | source TrackSet + loudness/format profile | rendition；no composition generation |

- 每个family使用独立OperationDefinition和capability/rights/quote/outputvalidation，不以同一Providerendpoint为由合并schema。
- `edit_lyrics preserve melody`、`remix change melody`等是certified capability，不是UI文案承诺。Provider无法保证时必须
  改成best-effort说明或不enable。
- source/segment/duration/model capability不匹配时Admission fail/reconfirmation，不silent trim/resample/drop lyrics。

## 5. Song Plan and Lyrics

### 5.1 SongPlan

- genre/mood/instrumentation/tempo/vocal描述采用product vocabulary + optional free text；adapter编译到Provider prompt，
  保存template/parameter digest但不泄漏hidden policy prompt。
- duration是intent/allowed range；Provider exact duration能力按certification显示。输出超tolerance进入validation/partial，
  不假装命中。
- section descriptors支持intro/verse/pre-chorus/chorus/bridge/break/outro/custom label，顺序/重复/目标duration可见；
  adapter不支持structure conditioning时UI不可承诺逐section遵循。
- assistant建议是proposed diff，用户apply才创建DraftRevision；不自动生成、不扩大rights、不改变费用ceiling。
- vocal intent不能只藏在自由文本。每个VoiceSlot明确generic/non-identifiable/represented subject/clone/ensemble、subject、
  language、age eligibility、consent和deceptive/public intent；prompt或assistant检测到未声明身份、艺人、公众人物、多人或
  未成年人声音时，必须在effect前deny/review/reconfirm，不能把它降级成generic voice。

### 5.2 Lyrics

- LyricsRevision保存content language、section/line/stanza identity、原文、可选pronunciation/phoneme guide和author/rights。
- structure tag是product schema，不直接拼Provider control token。未知/custom tag需OperationDefinition支持或在提交前解释转换。
- 用户输入/导入lyrics做grapheme/IME/bidi/normalization policy；opaque notation与语言文本分开，不按UTF-16截断。
- lyrics length与section duration compatibility在Quote前提示，server重验；不silent drop超长段落。
- instrumental operation明确lyrics absent；不得因旧draft残留偷偷生成vocal。
- generated lyrics若由assistant产生，保存source/provenance/model/rights policy；用户edit创建新revision。
- lyrics alignment是versioned evidence，状态unavailable|estimated|provider_reported|reviewed；播放器highlight不能冒充准确。
- assistant调用是独立、显式的 authorized ModelInvocation：具有logical call identity、输入Trust gate、provenance、
  AttemptUsageFact、Quote/charge policy与root Hold allocation。它只产出proposed DraftRevision；Submit不隐式补跑assistant，
  assistant失败或费用不得混入generation/stem/rendition Attempt。

## 6. Reference、Voice and Rights

- reference必须是PRD-06 ready AssetVersion/ArtifactVersion和purpose-bound grant；不接受任意URL/storage key。
- 每个binding显式role与segment：melody、rhythm、style、voice、sample、continuation、mix_context。不得从文件名/track位置猜。
- 权利bundle至少区分composition、master recording、lyrics、performance、sample、voice/likeness、trademark/persona、
  territory、term、commercial/public/remix/training/sublicense。每个required basis均满足才发effect/publicationauthorization。
- style reference不等于复制艺人身份/voice；artist imitation/public figure/voice clone按Platform policy deny/review/disclose。
- voice binding必须有Site-local ConsentEvidence：represented party、capturing actor/authority、verification、notice locale/a11y、
  purpose/model/public/remix/training、territory、expiry/revocation epoch。checkbox/知晓email/普通upload不足。
- minor/age-unknown voice/likeness/sexualized/deceptive/public remix走PRD-16 most-protective baseline；guardian不能覆盖absolute deny。
- sample/continuation source在queued后revoke：pre-effect拒绝，submitted effect quarantine/reconcile；派生继承parent最严格限制。
- 每个 enabled family发布 `RightsRequirementMatrixRevision`，按reference role × operation family × purpose × territory × term
  冻结required rights/consent。矩阵缺失或不覆盖当前用途时SiteRelease/Admission fail closed，不由adapter猜测。
- reference segment按canonical timeline/sample range，不使用browser rounded seconds。Asset owner创建purpose-bound
  `DerivedAudioInputVersion`，冻结source、track、Mapping、exact range、checksum、TTL与allowed deployment；Gateway只消费授权ref，
  adapter不得任意range-read整库或在TTL后复用clip。
- 用户 RightsAssertion 只是声明，不是已验证权利。权利争议、notice、counter-evidence、territory、期限与恢复使用 PRD-16
  的 RightsDispute/Restriction/Resolution；单一 Appeal overturn 不得绕过仍有效的 composition、master、voice 或 consent 限制。

## 7. Timeline、Playback and Segment Editing

### 7.1 Canonical timebase

- authoritative range以`startSampleInclusive/endSampleExclusive + canonicalSampleRate`或exact rational time表示；UI hh:mm:ss.ms
  是projection。转码/波形overview不改变source timeline。
- imported audio先生成normalized analysis representation，保存original sample rate/channel/codec/duration/checksum和mapping；
  Operation引用source ArtifactVersion + TimelineRevision。
- `AudioTimeMappingRevision`明确source sample origin、decoded canonical PCM digest、codec priming/trailing padding、piecewise rational
  transform、boundary rounding、track offset和channel mapping。AAC/MP3等有delay/padding的source不得用播放器秒数或单一比例近似。
- beat/bar/section量化只作为 `TempoMapRevision` 的音乐坐标projection，提交必须编译成exact sample/rational range；tempo或
  time-signature evidence不可靠时不enable“按小节精确”编辑，也不让UI吸附后冒充sample-exact。
- section/lyric/beat markers有source=evidence/provider/derived/user、confidence/revision；derived beat grid不是真相authority。
- range为空、越界、反向、落在旧timeline、source变化或requiredalignment缺失时submit fail/reconfirm，不自动clamp。
- `MusicSourceSnapshotRevision`把media/track、Timeline/Mapping、Lyrics/Alignment、SongPlan/VoiceIntent、Mix与rights epochs冻结为
  coherence digest。Operation只引用snapshot+显式delta；Quote后任一dependency head改变都需CAS失败并重新确认。

### 7.2 Player and waveform

- player支持play/pause/seek、速度、音量、mute、loop segment、current/total time、track选择与download eligibility。
- waveform是visual projection，可按zoom加载tiles，但不能作为唯一编辑面。structured timeline列出sections/tracks/markers/
  exact start/end，支持键盘/数值/step controls和文本摘要。
- playback signed range/url短时且current authorization；restricted/quarantined raw/reference不通过player泄漏。
- preview snippet/low-quality stage明确标preview，不可export/share，不产生final Artifact promise。
- autoplay遵循browser/user preference；不会突然播放、逐sample announce或用声音作为唯一状态提示。

### 7.3 Repaint and lyric edit

- repaint冻结source、segment、crossfade/preservation intent、replacementSongPlan/Lyrics和OutputContract。
- changed region之外“preserve”按capability分级：strict certified|best effort|unsupported；不能营销为无损保留。
- lyrics edit必须绑定旧alignment segment与newLyricsRevision；修改文本长度导致segment不兼容时reconfirm/扩大range，不silent squeeze。
- result始终是新complete ArtifactVersion，并记录changed segment/crossfade/provenance；不局部覆盖oldBlob。

## 8. Generate、Retake、Extend and Remix

- 提交review显示family、SongPlan/Lyrics、references/rights、source/segment、duration、candidate count、ModelOption、Quote ceiling、
  voice/disclosure/charge policy。
- candidate slots在Provider前stable分配；每candidate独立TrackSet/Decision/Usage/cost。preview/stage1 output若用户可明确
  保留，必须有独立candidate/Artifact/charge contract；否则只是ephemeral preview。
- retake声明preserve维度和variation strength class；不承诺seed/model跨revision复现。
- extend显式left/right/both、目标duration/section、source boundary/context window。新timeline映射oldsource range与newrange，
  不把extension bytes拼接成无provenance master。
- left/right、stage和candidate拥有stable subresult ID与独立outcome/Usage/Artifact receipt；任一side unknown时不得归约成complete
  master，只有冻结retention contract允许的独立结果可交付，cancel也逐subresult收口。
- remix是新arrangement/performance/mix，必须重新rights/voice/publication gate；不是免费format conversion。
- same settings/reproducibility按certification分级；保存Provider-returned seed和exact observed revisions，但不false guarantee。
- partial/unknown/cancel遵循PRD-07逐candidate/attempt规则；unknown不能通过选另一ModelOption重新生成。
- OperationDefinition冻结 `cancelScope=operation|attempt|candidate_slot`、certainty、preview retention和charge treatment；Provider
  只支持attempt cancel时，UI不得展示逐candidate取消或把未确认cancel投影为canceled。

## 9. Stem、TrackSet and Mix

- TrackDescriptor区分source recorded track、generated stem、separated estimate、vocal、instrumental、mix、master rendition；
  UI不能把separated estimate称为“原始stem”。
- stem generation需要requested instrument/role、mix context、sync origin、duration/sample rate/channel/output profile；产生新ArtifactVersion。
- stem separation固定published stem taxonomy（如 vocal/drums/bass/other），每track有quality/confidence/bleed disclosure；
  Provider差异不通过自由字符串进入UI。
- 所有tracks共享canonicalzero/timebase或明确offset；output validation检查duration tolerance、sample rate、channel、clipping、
  checksum。sync mismatch进入finalizing failure/partial，不completed。
- TrackSet的每一用途资格是所有贡献track当前资格的most-restrictive reduction；candidate allow不能覆盖某个sample/voice/
  source track的restriction。逐track Decision、rights、consent、Usage allocation与cost projection不得聚合后丢失。
- mix controls V1只覆盖published gain/mute/pan/order/selection与master profile；若仅客户端non-destructive preview，保存MixRevision；
  export mixdown创建RenditionJob和newArtifactVersion，不修改source tracks。
- track solo/mute/gain有AT可读state和数值替代；waveform/color不是唯一身份。

## 10. Audio Validation、Trust and Accessibility

- server验证detected audio/container/codec/duration/sample rate/channels/loudness、silence/truncation、NaN/Inf/DC offset、true peak/
  intersample clipping、phase/channel mapping、sample-accurate offset、splice click/crossfade、corruption/metadata；client MIME不authority。
  validator产出typed fail/review/partial，禁止为通过验收silent repair。active/unsupported/container bomb按Asset policy隔离。
- Trust在input/reference/output/publication各stage评估；ProviderSafetyFact只是evidence。restricted audio不进入player/
  waveform tile/notification/receipt/Support。
- lyric explicit content、hate/harassment、illegal signal、voice impersonation、copyright near-match/provenance按PRD-16 route；
  signal不是legal conclusion。
- 预录同步媒体若Studio展示歌词/visualizer/tutorial，按PRD-14适用caption/transcript/audio description；音频作品至少提供
  content-language、lyrics/transcript或描述性alternative（按media class/criterion判断），不能用“音乐无需无障碍”跳过。
- user可编辑lyrics/transcript/text alternative；auto alignment/transcript未经language/content review标estimated，不作为reviewed。
- player/timeline/track list完整keyboard/screen-reader/magnification/speech/switch/mobile；focus/reading anchor不因progress更新跳动。
- 每个candidate/export冻结 `MediaAccessibilityRevision` 与 `AccessibleOutputProfileRevision`：media class、content language、
  time-based alternative、lyrics/transcript/alignment review state、适用criterion与exception evidence。未reviewed自动文本不能满足
  发布门；timeline、loop/seek、track/mix、reduced motion/visualizer和announcement均进入真实browser/AT matrix。

## 11. Artifact、Export and Publication

- allowedcandidate创建stable Music Artifact + immutable ArtifactVersion/TrackSet；保存parent/source、Operation/Job/Attempt/
  Candidate、audio metadata、SongPlan/Lyrics/Timeline/reference、model/policy/rights/consent/provenance。
- compare支持候选或版本A/B、同步播放/切换、section/lyrics/metadata/cost diff；避免同时播放造成认知/听觉负担。
- export profile区分mix master、instrumental、vocal、individual stems、lyrics/timecoded text、cover metadata package。
- format/profile可包括WAV/FLAC/MP3/AAC/OGG等enabled inventory，但必须冻结codec/container/sample rate/bit depth/bitrate/
  channel/loudness/metadata/artwork/rights；不能只改扩展名。
- mastering/loudness normalization/format conversion是RenditionJob；不重跑compositiongeneration。clipping/loudness validation
  不通过则failed/reconfirmation，不silent normalize超policy。
- private playback、download、stem export、current rights evidence/use-restriction statement、public Share/remix各自authorization；
  该statement不是Kokoro对版权归属、原创性或商业许可的法律保证；rights不足不删除
  generated Artifact/cost，但阻断对应delivery并给safe remedy。
- playback token、download、Share、public/remix 和 commercial use 使用短期、purpose-bound `PublicationAuthorization`，冻结
  `siteId + ArtifactVersion + audience + policy/rights/consent/restriction epochs`；每次 mint/受控访问复验当前 epoch，旧授权
  不因 Appeal、Share 重建或 CDN 缓存而复活。
- export delivery每次验证Site/subject/project/rights/consent/restriction/TTL；storage URL不是长期ref。
- metadata默认不嵌prompt、userId、internalprovider/secret/sourcefilename；按policy嵌canonicalprovenance/watermark/disclosure。

## 12. Cost and User-visible States

- Quote dimensions至少duration intent/output actual seconds、candidate count、generation family、track/stem count、quality/profile、
  reference processing与rendition。client不传price micros。
- pre-effectdeny、stage1/preview、post-effectquarantine、partialtracks、unknown、cancel、appealoverturn逐family冻结ChargeTreatment。
- Provider cost不等于customer charge；AttemptUsageFact按audio seconds/features/track count/fixed operation等记录evidence grade。
- completed/cost_pending可播放；failed/settled、canceled/partial也可能有费用。unknown不释放committed allocation。

| State | Meaning | Recovery |
|---|---|---|
| draft_saved/conflict | SongPlan/Lyrics/Timeline revision保存或冲突 | continue/fork/compare/merge |
| source_or_segment_invalid | source/timeline/range/alignment不兼容 | reselect/remap/change segment |
| rights_or_consent_required | composition/master/sample/voice等缺证据 | provide/remove/change/cancel |
| quote_ready/reconfirmation | estimate有效或material change | confirm/requote/change |
| queued/running/previewing | Job进行，preview非final | leave/wait/cancel request |
| waiting_interaction | 需lyrics/rights/reauth/input | provide/change/cancel |
| cancel_requested | Provider cancel未确认 | wait/query |
| unknown/reconciling | effect/outcome不明 | wait/Support；retry disabled |
| finalizing | 校验audio/Trust/Artifact/Usage | wait；only finalizer retry |
| completed/partial | 全部或部分candidate/track可用 | compare/edit/extend/remix/export |
| restricted | candidate不可消费/发布 | safe reason/appeal/delete where allowed |
| failed/canceled | canonical terminal | show prior effect certainty/snapshot/new Quote before safe newOperation；Support |
| cost_pending | result存在，结算未完 | play where allowed/wait/receipt |
| export_blocked | 作品存在但delivery rights/a11y/disclosure不足 | remedy/appeal/change profile |

## 13. Admin、Support and Operations

- Music Console在Job timeline增加family、SongPlan/Lyrics/Timeline/reference/rights/voice、candidate/TrackSet、audio validation、
  Trust、Artifact/Usage/export；默认不播放或显示完整lyrics/reference。
- raw audio/voice/illegal/rightsevidence访问需field/action/TTL-boundContentAccessGrant、specialistrole、watermarkedplayer、
  no download/copy；Support不可扩权。
- typed commands：ReconcileUnknownMusicAttempt、RetryMusicFinalization、InvalidateTimelineMapping、StartRightsReview、
  RebuildTrackProjection、RevokePlayback/Export、StartAudioReevaluation。不得markclean/completed、改Usage或直接rerunProvider。
- 每个 command 必须冻结 `siteId`、target generation/revision、expectedVersion、idempotency key、reason、actor/approval scope 与
  receipt；高风险 evidence access、rights restore、playback/export revoke 按 PRD-10 maker-checker/step-up 矩阵执行，禁止跨 Site。
- monitoring：family/locale/vocal mode、durationerror、lyricsalignment、queue/attempt/finalization、candidate/trackpartial、rights/
  consent/restriction、loudness/clipping、export、player/a11y，按Site/Profile/Definition revision。
- runbooks：callbacklate、duration/codec mismatch、timeline offset、voiceconsent revoke、near-matchsignal、stem sync/bleed、
  preview leak、Usage/Artifact outage、CDN purge。

## 14. Edge Cases

| Scenario | Expected behavior |
|---|---|
| lyrics oldrevision changed aftersubmit | Job usesfrozenrevision；newedit createsnewOperation |
| client range rounded, source48kHz | canonical sample range wins；UI projection不改变boundaries |
| source resampled aftermask/segment | newTimeline mapping required；oldsegment reject/reconfirm |
| voice consent revoked whilequeued | pre-effectdeny；submitted result quarantine/reconcile |
| 3 candidates: mixsuccess, one restricted, oneunknown | partial；allowedplayback, restrictedhidden, unknownnoretry |
| Provider says100% but noaudio | progress nonterminal；unknown/finalization based onfacts |
| extend both sides partialsuccess | exactnew/oldranges andcandidate status；not flatten into successfulmaster |
| stem separation hasheavy bleed | derivedestimate disclosure/quality；not originalstems |
| lyric edit changes 2s line to20s | reselect/expand segment or reject；no silent squeeze |
| cancel afterstage1 preview | preview retention/charge followsfrozenpolicy；not finalunlessreceiptcontract |
| commercial export lacks compositionright | Artifact/privateplayback remain；exportblocked withsafe category |
| same seed differentDeployment | no reproducibilitypromise；versions recorded |

## 15. Acceptance Criteria

### AC-MUS-01 — Family and vocal intent are explicit

```gherkin
Given instrumental, lyrics-to-song, repaint, extend, remix and stem operations have different contracts
When a Draft is submitted
Then one published Music OperationDefinition validates exact source, vocal mode, lyrics, timeline and output requirements
And no stale lyrics, arbitrary Provider payload or silently dropped parameter reaches execution
```

### AC-MUS-02 — Reference rights are role-specific

```gherkin
Given one audio file is bound as melody, sample, voice and continuation source
When Admission evaluates the Operation
Then each role requires its exact composition/master/performance/sample/voice rights and consent scope
And a generic ownership assertion or same content hash cannot authorize missing uses
```

### AC-MUS-03 — Segment mapping is exact

```gherkin
Given browser time display, resampled analysis audio and original source have different timebases
When repaint or extend is submitted
Then source ArtifactVersion, TimelineRevision and exact sample/rational ranges are frozen
And stale, rounded, empty or out-of-range selections fail before effect rather than editing another segment
```

### AC-MUS-04 — Lyric edit preserves only certified dimensions

```gherkin
Given a user edits lyrics for an aligned segment and requests melody/vocal preservation
When the selected ModelOption lacks certified preservation capability or new text no longer fits the segment
Then Studio requires a different mode, range or reconfirmation
And it never promises preservation or silently compresses/drops lyrics
```

### AC-MUS-05 — Candidate and TrackSet isolation

```gherkin
Given candidates and stems become allowed, restricted, failed and unknown independently
When finalization runs
Then every candidate/track keeps stable Artifact, Decision, Usage, sync and cost identity
And allowed tracks remain usable without exposing restricted content or retrying unknown effects
```

### AC-MUS-06 — Extend creates auditable timeline

```gherkin
Given a source is extended left and right around an immutable middle range
When the Operation completes
Then the new ArtifactVersion maps old and new sample ranges with model/Attempt provenance
And source bytes, Timeline, Share and settled Usage remain unchanged
```

### AC-MUS-07 — Stem labels are truthful

```gherkin
Given stem separation derives vocal, drums, bass and other tracks from a mix
When results and export are shown
Then each track is labeled as a derived estimate with quality/bleed/sync metadata
And no UI, manifest or rights statement calls it an original multitrack recording
```

### AC-MUS-08 — Cancel and preview do not fabricate completion

```gherkin
Given a Provider emits a stage preview before cancel or connection loss
When outcome is reduced
Then preview becomes a final Artifact only if the frozen preview-retention contract and receipts allow it
And otherwise cancel/unknown continues without claiming a completed song or releasing committed cost unsafely
```

### AC-MUS-09 — Private playback does not imply export

```gherkin
Given a generated song is allowed for private playback but lacks voice, sample, composition, disclosure or accessibility eligibility
When stem, commercial or public export is requested
Then no delivery authorization is issued while the Artifact and cost history remain intact
And the user receives exact safe remedy or appeal categories
```

### AC-MUS-10 — Structured timeline is equivalent

```gherkin
Given a non-pointer user selects a section, loops playback, edits lyrics, requests repaint and chooses tracks
When the structured section/track/timecode controls are used
Then they produce the same canonical MusicOperationSpec as waveform interactions
And player, progress, focus, transcript/lyrics and recovery satisfy every applicable WCAG A/AA criterion
```

### AC-MUS-11 — Agent and Direct share one spine

```gherkin
Given Chat Agent and Music Studio submit equivalent certified MusicOperationSpecs
When both execute
Then Job, Gateway, Candidate, TrackSet, Artifact, Trust, Usage and Cost contracts are identical
And GA receives only an opaque Job handle without music Provider branches or a second charge path
```

### AC-MUS-12 — Output validation precedes terminal

```gherkin
Given Provider reports success but duration, codec, channels, TrackSet sync, checksum or required provenance is invalid
When finalization runs
Then Job does not expose a ready completed Artifact/export
And recovery retries validation, Blob, Artifact and Usage receipts without rerunning music generation
```

### AC-MUS-13 — Cross-Site music isolation

```gherkin
Given Site A owns a MusicDraft, Timeline, reference grant, ConsentEvidence and Artifact lineage
When Site B submits an Operation or operator command using any of those references
Then authorization rejects before metadata disclosure, playback, export or Provider effect
And no existence, timing, rights, policy or content signal from Site A is returned
```

### AC-MUS-14 — Publication epoch race

```gherkin
Given a song was eligible for one private or public use when a PublicationAuthorization was issued
When rights, consent or restriction epoch changes before token mint or controlled access
Then the stale authorization is rejected and origin access remains revoked
And no cached token, Appeal result or rebuilt Share silently restores the old use
```

### AC-MUS-15 — Independent rights restrictions survive appeal

```gherkin
Given a moderation restriction is overturned while a composition, master, sample, voice or consent restriction remains active
When delivery or republication is evaluated
Then the original moderation Decision is superseded without weakening the independent restriction
And a new current-epoch authorization is required before playback, export, remix, commercial or public use
```

### AC-MUS-16 — Voice identity is typed before effect

```gherkin
Given prompt, lyrics or references request an identified, cloned, ensemble, public-figure, minor or age-unknown voice
When the VoiceIntent slots, age eligibility or purpose-scoped ConsentEvidence are missing or inconsistent
Then Admission denies, reviews or requires explicit reconfirmation before any assistant or generation effect
And free text cannot downgrade the request to a generic synthetic voice
```

### AC-MUS-17 — Source snapshot remains revision-coherent

```gherkin
Given a Quote freezes audio, TrackSet, Timeline, Mapping, Lyrics, Alignment and Mix revisions
When any dependency head changes before submit or export
Then snapshot CAS or coherence digest validation fails and the user receives a new diff and Quote
And no current-head Mix, stale alignment or unrelated track is read implicitly
```

### AC-MUS-18 — Track restriction and cost remain isolated

```gherkin
Given one separated or generated track contains a restricted sample or revoked represented voice
When the parent candidate is otherwise allowed
Then TrackSet eligibility applies the most-restrictive current Decision, rights and consent for each requested purpose
And that track cannot be played or exported through candidate-level allow while Usage and cost allocations remain auditable
```

### AC-MUS-19 — Assistant and generation are separately authorized

```gherkin
Given a user requests assistant help before music generation
When the assistant proposes lyrics, SongPlan, voice slots or parameters
Then it runs as an explicit authorized ModelInvocation with its own provenance, Usage and charge policy
And submit never invokes it implicitly or mixes its Attempt with generation, stem or rendition settlement
```

### AC-MUS-20 — Lossy and resampled time mapping is exact

```gherkin
Given a 44.1 kHz lossy source has codec priming and is analyzed as 48 kHz canonical PCM
When a segment is selected and repainted
Then the frozen AudioTimeMappingRevision applies exact origins, padding, rational transforms and rounding policy
And golden output proves the intended source samples and track were changed without drift
```

### AC-MUS-21 — Multi-side extend does not hide unknown

```gherkin
Given left and right extension subresults have stable identities
When one succeeds and the other has an unknown Provider outcome
Then no complete master is fabricated and the unknown side is never retried
And only independently retained results allowed by the frozen contract can be delivered or charged
```

### AC-MUS-22 — Derived audio input is purpose-bound

```gherkin
Given an exact reference segment is prepared for one Operation and Deployment
When a caller requests another range, purpose, Site, Deployment or an expired input
Then the DerivedAudioInputVersion grant is rejected before bytes or Provider effect
And Gateway cannot range-read the source library or widen the grant
```

### AC-MUS-23 — Media accessibility revision gates delivery

```gherkin
Given a candidate or export requires a reviewed time-based alternative for its media class
When only estimated lyrics, alignment or transcript is available
Then the required public or export authorization is blocked with a review remedy
And structured timeline, player and mix controls remain fully operable without waveform or pointer input
```

### AC-MUS-24 — Invalid audio success is not completed

```gherkin
Given Provider reports success but output is silent, truncated, non-finite, misaligned, clipped or has an invalid splice
When the certified audio validator evaluates the exact family and output profile
Then it emits a typed fail, review or partial result and exposes no ready final Artifact
And recovery never silently repairs or reruns the Provider effect
```

### AC-MUS-25 — Cancel granularity is truthful

```gherkin
Given the certified Provider can cancel only an entire Attempt that contains several candidate slots
When a user requests cancellation for one candidate
Then Web does not claim candidate-level cancel or terminal canceled certainty
And late tracks, Usage and cost reconcile under the frozen attempt-level policy without exposing restricted output
```

### AC-MUS-26 — Revocation is checked at every effect

```gherkin
Given voice, sample or rights authorization was valid for an assistant proposal
When its epoch is revoked before generation, stem processing or export mint
Then every later effect revalidates and rejects the stale authorization
And an already submitted effect is quarantined and reconciled without automatic retry
```

## 16. Verification and Release Gates

- schema/golden：每family、SongPlan/Lyrics tags、language/section、timeline/sample mapping、reference roles、codec/channel/
  duration/stem sync、unsupported parameter fail-before-effect。
- sample golden：44.1/48/96k、PCM/lossy、priming/padding、mono/stereo/multichannel、offset tracks与piecewise mapping；
  任一目标segment漂移即No-Go。
- property：range conversion、resample mapping、tempo projection、section/lyrics identity、candidate/TrackSet isolation、lineage DAG、
  partial/cancel/unknown。
- audio adversarial：corrupt/containerbomb/metadata injection、ultrasonic/clipping/extreme loudness、malicious lyrics/bidi、voice spoof。
- integration/chaos：object storage + sandbox Provider、callback duplicate/late、longqueue/lease steal、stage preview、Artifact/
  Usage/Trust outage、consent revoke、Site rollback。
- rights/safety：composition/master/performance/sample/voice/likeness、minor/public figure、near-match、appeal/takedown。
- isolation/settlement：两Site同hash/Provider operation ID和交叉Asset/Timeline/TrackSet/Mix/rights refs；assistant/generation/
  stem/rendition AttemptUsage与root Hold allocation守恒。
- UX/a11y：desktop/mobile、keyboard/screenreader/magnification/speech/switch、player/waveform structured parity、lyrics language、
  media alternative/export format/client matrix。

内部批准还要求：

- 每个 enabled family 已发布 OperationDefinition、runtime role requirements、RightsRequirementMatrix、cancel scope、
  ChargeTreatment、output validator、fallback equivalence与sandbox certification，缺任一项即fail closed。
- 跨 Site source/timeline/TrackSet/Mix/rights/consent/callback负向矩阵、sample-golden corpus、voice/minor/public-figure矩阵、
  partial/cancel/late/unknown/finalizer chaos、Usage/root Hold守恒与Site/Profile/locale/browser/AT认证全部通过。
- Legal已为目标launch jurisdiction签发rights、minor、notice、takedown与retention matrix；缺地区证据不得enable该Site profile。

No-Go：万能music.generate或reference；RightsRequirementMatrix缺失；voice intent/consent弱；timeline用roundedbrowser seconds authority；
unknown retry；source overwrite；candidate/track串位；derived stem冒充original；private allow绕过export；waveform pointer-only；
GA出现musicProvider业务分支。

## 17. External References

- [ACE-Step](https://github.com/ace-step/ACE-Step)：参考text-to-music、retake/repaint、lyrics edit、extend、remix、track/stem
  的专业任务分离；其模型能力和UI不成为Kokoro权利或质量承诺。
- [YuE](https://github.com/multimodal-art-projection/YuE)：参考结构化lyrics、full-song/incremental generation、reference audio、
  continuation和stage preview；Kokoro以Job/Candidate/Timeline receipts治理。
- [AudioCraft MusicGen](https://github.com/facebookresearch/audiocraft/blob/main/docs/MUSICGEN.md)：参考text/melody conditioning、
  continuation与sampling metadata；不暴露底层checkpoint/sampler为产品contract。
- [Stable Audio Tools](https://github.com/Stability-AI/stable-audio-tools)：参考conditional/inpaint audio与sample rate/channel
  capability；training/config不是Studio用户面。

## 18. Related Documents

- [PRD-06 Asset](2026-07-25-prd-06-asset-intake-and-attachment-safety.md)
- [PRD-07 Studio Common](2026-07-25-prd-07-studio-common-job-and-cost-ux.md)
- [PRD-14 Accessibility](2026-07-25-prd-14-localization-and-accessibility.md)
- [PRD-16 Trust](2026-07-25-prd-16-trust-content-safety-and-media-rights.md)
- [Model Control/Gateway](2026-07-25-model-control-gateway-litellm-architecture-design.md)

本文批准不授权实现，也不修改 GA runtime。
