---
artifact: product-requirements-document
prdId: PRD-08I
version: "1.0"
created: 2026-07-25
status: internal-review-active
scope: image-studio-generate-reference-edit-mask-inpaint-outpaint-variation-batch-upscale-export
accountableProductRole: Image Studio Product Lead
mandatoryCosigners: [Image ML, Job Runtime, Asset, Artifact, Model Platform, Trust, Accessibility, Web, Support, QA]
engineeringOwner: team:image-studio-engineering
qaOwner: team:image-studio-quality
supportOperationsOwner: team:image-studio-operations
namedOwnerAssignmentStatus: assigned-team-responsibility-ids
implementationAuthorized: false
gaRuntimeSemanticChangeAuthorized: false
---

# PRD-08I：Image Studio

## 1. Overview

### Problem

Image 产品不只是 prompt→图片。用户需要 reference、composition/style guidance、mask、局部编辑、扩图、变体、
批量候选、比较、upscale、透明背景和格式导出。若把所有操作压成一个 `generateImage(prompt, options)`，mask 坐标、
reference用途、parent lineage、候选费用和安全限制会丢失；若直接暴露 Provider/Comfy graph，又会造成参数漂移、
跨模型不可解释、任意 workflow 越权和无法保证的 seed 复现。Canvas 仅鼠标可用也会让专业流程无法通过上线认证。

### Solution

在 PRD-07 的 Draft→Operation→Job→Attempt→Artifact 主链上，定义有限且版本化的 Image Operation family：
`text_to_image`、`image_variation`、`image_edit`、`inpaint`、`outpaint`、`upscale`、`background_transform`。每种操作有
独立 typed schema、input/output contract、Model role、Asset/right/consent/Trust gate 和 quote dimensions。Canvas 保存
结构化 layer/selection/mask DraftRevision，提交时冻结为 immutable OperationSpec；结果永远创建新 ArtifactVersion，
不原地覆盖 source image。

### Users and stories

| ID | User story | Priority |
|---|---|---|
| IMG-US-01 | 用户可从文本和尺寸/构图意图生成一组可比较候选 | P0 if-enabled |
| IMG-US-02 | 用户可引用自己有权使用的图片，并明确它用于内容、构图、风格、颜色还是编辑 base | P0 |
| IMG-US-03 | 用户可用 mask/list/coordinates 做局部修改和 outpaint，撤销不会破坏原图 | P0 |
| IMG-US-04 | 用户可对某个候选做 variation/upscale/背景处理并保留完整版本谱系 | P0 |
| IMG-US-05 | 用户能看到每个候选的生成、安全、费用和可导出状态，不因部分失败丢掉成功结果 | P0 |
| IMG-US-06 | 非 pointer 用户可通过对象列表、数值区域与结构化控件完成等价编辑 | P0 |

## 2. Goals、Metrics and Non-Goals

### Goals

1. 每个 Image operation 都有单一 purpose schema，不用任意 provider payload 或万能 node graph。
2. source、reference、mask、canvas coordinate space 与 output slot 完整版本化、可重建。
3. batch 每个 candidate 的 Artifact/Usage/Trust/Cost 独立；partial 不串位。
4. Image assistant 与 generation model role 分离，用户只选择产品 ModelOption。
5. private preview、download、export、share/remix 分别授权；生成成功不等于可以公开。
6. Canvas 与专业控件满足完整 WCAG 2.2 A/AA 和 structured alternative。

### Success Metrics

| Metric | Target |
|---|---:|
| Image Operation 缺 source/mask/reference/output provenance | 0 |
| mask 坐标/方向/缩放漂移导致编辑错误 | 0 certification failures |
| batch candidate Artifact/Usage/Decision/charge 串位 | 0 |
| source ArtifactVersion 被编辑操作原地覆盖 | 0 |
| disabled/unsupported parameter 被静默 drop | 0 |
| seed 被错误承诺跨 Deployment/adapter bitwise reproduce | 0 |
| restricted candidate进入download/export/share | 0 |
| Canvas pointer-only blocker | 0；任一适用 A/AA failure阻断Release |

### Non-Goals

- V1 不提供任意 Comfy/node graph、用户脚本、模型权重/LoRA/VAE 上传、checkpoint merge 或训练。
- 不暴露 Provider、Deployment、scheduler内部名、secret、raw safety setting或GPU/VRAM控制。
- 不承诺同 seed 在不同模型、Deployment、adapter、hardware或revision产生相同字节。
- 不把 Photo editor 的全套 raster/vector功能、多人实时协作或无限layer compositor作为首发目标。
- 不自动认定用户上传reference拥有版权、肖像或训练授权。
- Image Studio 不执行 Job、Provider或Artifact persistence；只使用共享owner contract。
- 不修改 GA；Agent 调用相同 Image Operation facade。

## 3. Product Objects and Operation Families

```text
ImageDraftRevision
  draftRef / canvasRevision / operationFamily / prompt+negative intent
  sourceArtifactVersion? / referenceBindings[] / layerRefs[] / selectionRefs[]
  maskRevision? / outputLayout / candidateCount / ModelOption / parameterSet

ImageReferenceBinding
  assetOrArtifactVersionRef / role=content|composition|style|color|identity|edit_base
  influence class/range / crop+transform / rights+consent refs / policy revision

ImageCanvasRevision
  logical width+height / coordinateSpaceRevision / background / ordered layers
  viewport transform (UI only) / object list / selection/mask refs

ImageMaskRevision
  sourceCanvasRevision / coordinate space / width+height / polarity / feather intent
  raster or vector region Blob ref / checksum / createdBy+tool revision

ImageOperationSpec
  family / immutable inputs / typed parameters / output contract
  assistant+generation role requirements / candidate slots / quote dimensions

ImageCandidateResult
  candidateId / ArtifactVersion / width+height / media metadata
  Decision+rights+usage+cost refs / preview+export eligibility
```

| Family | Required input | Product output |
|---|---|---|
| `text_to_image` | prompt intent + output layout | N independent image candidates |
| `image_variation` | one source version + variation intent | lineage-bound alternatives |
| `image_edit` | edit base + prompt/instruction + optional references | new full image version |
| `inpaint` | edit base + mask + edit intent | same logical canvas extent unless policy says otherwise |
| `outpaint` | edit base + expanded canvas + protected/source region | larger canvas version |
| `upscale` | source version + target scale/size + enhancement policy | new rendition/version with dimensions/provenance |
| `background_transform` | source + subject/background selection intent | transparent/replaced/background-adjusted version |

- 每个 family 是独立 OperationDefinitionRevision。Provider可用同一endpoint实现多个family，但不能以相似为由共用
  含糊schema；这与成熟 Diffusers “one task, one pipeline”原则一致。
- OperationDefinition 固定可见参数、合法组合、capability mapping、quote dimensions、fallback equivalence、input/output
  media constraints。Provider adapter只映射，不静默补值/drop行为参数。

## 4. Create and Prompt Assistance

- prompt是用户内容，不是Provider payload。UI区分主描述、避免意图、构图/颜色/风格等结构化可选字段；具体文本
  compilation由版本化PromptTemplate/Adapter完成并留digest，用户可查看安全摘要而不暴露隐藏policy prompt。
- `image.assistant` 可帮助澄清、改写prompt、从reference提取可编辑描述或建议参数；它不自动提交generation、不拥有
  reference rights、不修改current draft、不代表用户接受更高费用。
- assistant建议以proposed diff显示，用户apply后创建新DraftRevision；拒绝不影响原draft。
- 模型选择只展示Image ModelOption的能力/速度/相对质量/支持family/尺寸/费用范围。内部`image.assistant`和
  `image.generation` role必须同时由EffectiveModelBundle完整解析。
- 具体Provider不支持negative prompt/seed/style reference/mask feather时，Admission按capability fail closed或要求改参数；
  禁止静默drop。
- prompt/parameter client limit只是UX；server按grapheme/schema/policy重新验证。IME期间Enter不提交。

## 5. Reference、Source and Rights

- Reference必须是PRD-06 ready AssetVersion或ArtifactVersion，绑定当前Site/Project/purpose AssetGrant；浏览器URL、data URL、
  object key、clipboard远程URL不能直接成为Provider input。
- 用户选择每个reference role，系统不从位置/文件名猜“style”或“identity”。同一Asset多role需显式binding。
- edit_base是像素修改source；content/composition/style/color是conditioning；identity/face/likeness进入PRD-16更高强度
  consent、age、public figure、minor/deepfake gate。
- RightsBasis按asset/version/right type/territory/use/term/public/remix保存。普通checkbox/assertion不是已验证rights。
- reference crop/rotate/flip/color transform属于DraftRevision和OperationSpec；原AssetVersion不变。
- source/references在queued Job后被revoke：未effectAttempt拒绝；已effect只finalize到quarantine/reconcile，不发布。
- image-to-image、variation、upscale、mask edit继承parent最严格restriction/rights/retention，不能通过派生洗白。

## 6. Canvas、Mask and Structured Editing

### 6.1 Coordinate contract

- authoritative coordinate space是`ImageCanvasRevision` logical pixels或版本化normalized coordinates；CSS/device pixels、
  zoom/pan/retina scale只属UI viewport，不能进入OperationSpec。
- layer/object/selection/mask均引用canvas revision和transform matrix；source orientation/EXIF先安全normalize为新的derived
  representation，记录原orientation，不在client/server各自重复旋转。
- mask明确polarity（edited/protected）、alpha/threshold/feather intent、width/height/checksum。Provider adapter负责精确
  polarity/size mapping，并通过golden mask corpus验证；不能默认“白=edit”适用于所有Provider。
- base/canvas/mask revision不匹配、mask空/全选、区域越界或尺寸变化时提交前typed reject/reconfirmation，不自动拉伸。

### 6.2 Editing behavior

- Canvas支持zoom/pan、select、brush/erase mask、rectangle/lasso、layer visibility/order、undo/redo；每个material edit
  创建或合并为有界DraftRevision，不把pointer event history作为长期真源。
- undo/redo只移动draft revision/编辑历史cursor，不删除已提交Operation/Artifact/Usage。
- inpaint显示protected/edited region预览；outpaint显示original bounds、expanded bounds和填充区域。
- structured alternative提供object/layer list、region x/y/width/height、polarity、feather、crop/transform数值控件、preview
  description和undo history。结果OperationSpec必须与Canvas路径语义相同。
- touch/keyboard/speech/switch input均可完成；focus、reading anchor、快捷键帮助、target/reflow遵循PRD-14。
- 无法为某专业工具提供等价操作时，该工具/Surface不得进入enabled inventory，不能用“建议鼠标”豁免。

## 7. Generate、Batch and Candidate UX

- 提交前review exact family、draft revision、reference/mask/source、output尺寸/比例、candidate count、ModelOption、Quote范围、
  rights/consent/disclosure与可能的post-effect charge。
- `candidateCount`受Plan/OperationDefinition/Provider capability/quote ceiling约束；batch slots在Provider前分配stable ID。
- batch可单Job多candidate或Job DAG，内部形态由Definition决定，但用户/Artifact/Usage始终逐candidateidentity。
- preview progress不等于candidate ready；低清预览/latent preview默认不保存为Artifact，不通过Trust/download/export。
- 每个candidate状态：queued/running/previewing/finalizing/allowed/restricted/failed/unknown/canceled；Operation可partial。
- allowed candidate即时可比较/收藏/打开；restricted内容不可在thumbnail/notification/receipt/Support泄漏；failed/unknown
  不覆盖allowed。
- 用户取消remaining candidates时保留已完成结果，未提交slot释放allocation；submitted/unknown按PRD-07收口。
- “reroll/variation/more like this”是新visible Operation，引用parent candidate和新Quote；不是隐藏Provider retry。

## 8. Variations、Edit、Outpaint and Upscale

- Variation冻结parent ArtifactVersion、variation strength/intention、seed policy和ModelOption；创建siblings/child lineage，
  不修改parent。
- Edit/inpaint/outpaint每次提交冻结base+mask+canvas revision。结果可作为新Canvas base，但需用户显式“Continue editing”
  生成新DraftRevision。
- upscale区分resolution upscale、detail enhancement、face restoration等产品operation；face enhancement受identity/
  likeness/policy gate，不能默认执行或修改人物身份特征。
- upscale target用exact width/height或published scale，检查aspect/maximum pixels/format/alpha/color profile；Provider返回
  dimensions不符进入output validation/finalization failure，不标completed。
- background removal/replacement保留alpha matte/subject selection provenance；transparent preview棋盘格不是实际背景。
- iterative edit若旧mask不适用于新base，系统明确invalidate或提供经过review的transform，不静默复用错位mask。
- 每个派生操作独立Quote/Hold/Usage；UI清楚区分“复用素材”与“免费重做”。

## 9. Reproducibility and Metadata

- 保存用户seed intent、Provider-returned seed（若有）、canonical参数、ModelOption、Definition/Profile/Deployment/Adapter/
  observed provider revision、prompt/template digest、source/ref/mask checksums和operation provenance。
- UI术语分级：`same settings`、`provider reproducible under certified revision`、`not guaranteed reproducible`；没有认证证据
  不显示“完全复现”。
- Provider alias漂移或未观察exact model revision时reproducible=false，并缩短certification；seed不能掩盖漂移。
- Import PNG/metadata可提出parameter draft，但所有metadata视为不可信、schema限制、去secret/路径/HTML，需用户review；
  不导入Provider API key、arbitrary workflow/script或跨Site Asset ref。
- Export metadata按privacy/disclosure policy：可以嵌入canonical provenance/watermark，不默认嵌入prompt、user identity、
  hiddenreasoning、internal IDs或source filename。

## 10. Trust、Safety and Publication

- input prompt、reference、mask-targeted edit与output每stage执行PRD-16。ProviderSafetyFact只是evidence，Trust发布Decision。
- minor/age-unknown、sexualized likeness、voice/identity proxy、public figure、election/deceptive media走Platform最保护baseline；
  Site不能放宽，guardian consent不能覆盖absolute deny。
- output allowed for private不等于download/export/share/remix；每次mint/refresh验证current policy/rights/consent/
  restriction epochs与shortTTLauthorization。
- watermark/C2PA/provenance adapter按Site/policy要求；缺失、损坏、被剥离时明确降级并阻断需要它的export/share。
- Takedown先revokeorigin/新token，再异步purge managed thumbnails/CDN/search；UI诚实显示partial/unknown。
- ChargeTreatment逐stage/candidate冻结：pre-effectdeny、post-effectquarantine、partial、unknown、appealoverturn；受限内容不出现在cost receipt。

## 11. Artifact、Compare and Export

- 每个allowedcandidate创建ArtifactVersion：parent/Operation/Job/Attempt/Candidate/Blob、width/height/colorspace/alpha、
  source/ref/mask、parameters/model/policy/rights/provenance完整。
- compare支持2–4个candidate的fit/actual pixels、zoom/pan sync、metadata diff和accessibility descriptions；compare selection
  只是read preference，不修改Artifact。
- export profile至少按enabled inventory支持web image和preserving-alpha格式；具体PNG/JPEG/WebP/AVIF/TIFF等必须在
  Definition中认证色彩、alpha、metadata、quality与browser/clientmatrix，不能只按扩展名。
- resize/crop/compress/format conversion若跨worker或耗时，创建RenditionJob；不重跑generation。source ArtifactVersion不变。
- export确认exact size/format/quality/alpha/color profile/metadata/watermark/rights/estimatedcost，并提供accessible text alternative。
- download使用BFF/Artifactauthorization，不暴露storage key；过期delivery可重建rendition/delivery，不新生成source。
- Chat→Image Studio传同ArtifactVersion/Asset refs创建Draft，不复制字节；Image→Library也使用同identity。

## 12. User-visible States and Recovery

| State | Meaning | Recovery |
|---|---|---|
| draft_saved / conflict | Canvas/parameter revision保存或并发冲突 | continue/fork/compare/merge |
| source_or_mask_invalid | source/mask/canvas revision或坐标不兼容 | reselect/remap/recreate mask |
| rights_or_consent_required | reference/use缺证据 | provide/change/remove/cancel |
| quote_ready / reconfirmation | estimate有效或material变化 | confirm/requote/change |
| queued / running / previewing | Job进行，preview非结果 | leave/wait/cancel request |
| cancel_requested | cancel未确认 | wait/query；不宣称canceled |
| unknown / reconciling | Provider effect/outcome不明 | wait/Support；retry disabled |
| finalizing | 正在校验Blob/Trust/Artifact/Usage | wait；只retry finalizer |
| completed / partial | 全部或部分candidate可用 | compare/edit/upscale/export/newoperation |
| restricted | candidate不可消费/发布 | safe reason/appeal/delete where allowed |
| failed / canceled | canonical终态 | safe retry/newoperation/Support |
| cost_pending | result可用，settlement未完 | use/wait/view receipt |
| export_blocked | generation存在但export条件不满足 | rights/a11y/disclosure/appeal/change format |

## 13. Admin、Support and Operations

- Image Console在通用Job timeline上增加family/schema、source/ref/mask/canvas digest、candidate slots、output validation、
  Trust/provenance/export eligibility；默认不展示原图/prompt。
- evidence access使用Site/resource/field/action/TTL-bound ContentAccessGrant，默认blur/redacted，最高风险专岗/双人；
  Support无法扩权。
- typed commands：RetryFinalization、ReconcileUnknown、InvalidateBrokenMaskMapping、StartOutputReevaluation、
  RebuildImageProjection、RevokeExportAuthorization。不能markclean/completed、改Artifact/Usage或直接重跑Provider。
- monitoring：family/ModelOption success、queue/attempt/finalizationage、mask/output validation、partialdistribution、
  candidate cost、restriction/appeal、export failures、a11y Canvas failures，按Site/Profile/Definition revision切分。
- runbooks覆盖Provider尺寸/alpha错误、mask polarity adapter regression、preview leak、callbacklate、provenance missing、
  thumbnail/CDN purge和scanner/Trust outage。

## 14. Edge Cases

| Scenario | Expected behavior |
|---|---|
| EXIF rotated base + client mask | normalize derived base + versioned transform；mask不双旋转 |
| mask polarity differs by Provider | adapter golden corpus映射；不能默认或silent invert |
| mask revision belongs old canvas | reject/reconfirm；不拉伸到new canvas |
| user changeszoom before submit | viewport不影响logical coordinates/spec |
| 4 candidates: 2 allowed,1restricted,1unknown | Operation partial；逐candidateArtifact/Usage/Decision，unknown禁retry |
| seed same但Deployment变更 | 显示not guaranteed reproducible；新Operation保留both revisions |
| source rights revoked whilequeued | pre-effect拒绝；submitted output quarantine/reconcile |
| upscale returns wrongdimensions | output validation fail/finalizing recovery；不completed |
| cancel arrives after2 candidatescomplete | 保留2 results；remaining逐attemptcancel/unknown处理 |
| Provider preview containsrestricted image | preview不得绕过Trust；隔离且不展示/通知 |
| metadata import containsscript/API key/path | strictsafe fields only；secret/script ignored/rejected并审计 |
| oldArtifact sharedthenedited | newversion独立publicationauthorization；旧share不自动指向newversion |

## 15. Acceptance Criteria

### AC-IMG-01 — Operation family is explicit

```gherkin
Given text generation, variation, inpaint, outpaint and upscale have different input contracts
When a Draft is submitted
Then exactly one published Image OperationDefinition validates the complete typed spec
And no arbitrary workflow, Provider payload or silently ignored behavior parameter reaches execution
```

### AC-IMG-02 — Mask coordinates are deterministic

```gherkin
Given an EXIF-oriented source, resized viewport, zoomed Canvas and versioned mask
When inpaint is submitted
Then source normalization, logical coordinate transform, mask size and polarity are frozen in the spec
And server/adapter golden validation edits the intended region or rejects before effect
```

### AC-IMG-03 — Reference purpose and rights are bound

```gherkin
Given one image is used as edit base, style reference and identity reference
When Admission evaluates it
Then every role has an explicit binding, purpose grant and required rights/consent evidence
And a generic upload checkbox or same-file hash cannot authorize missing identity/publication scope
```

### AC-IMG-04 — Batch candidates remain independent

```gherkin
Given a batch produces allowed, restricted, failed and unknown candidates
When Job finalization and Studio projection run
Then each candidate keeps a stable Artifact/Decision/Usage/cost identity
And allowed results remain usable while restricted content stays hidden and unknown cannot auto-retry
```

### AC-IMG-05 — Edit never overwrites source

```gherkin
Given a user inpaints, outpaints, varies and upscales one ArtifactVersion
When each operation completes
Then every result is a new immutable ArtifactVersion linked to its exact parent/spec/mask/Attempt
And the source bytes, metadata, rights, Share and settled Usage remain unchanged
```

### AC-IMG-06 — Cancel preserves completed candidates

```gherkin
Given some candidate effects completed before cancel and others are queued, submitted or unknown
When cancel is requested
Then completed candidates and their Usage are retained
And each remaining slot follows authoritative cancel/reconcile without fabricating a batch-wide canceled state
```

### AC-IMG-07 — Seed is not a false guarantee

```gherkin
Given a prior result has a seed but current Deployment, adapter, provider revision or parameters differ
When the user chooses reuse settings
Then the UI discloses the certified reproducibility class and freezes both old and new revisions
And it never promises bitwise reproduction without matching certified evidence
```

### AC-IMG-08 — Private generation does not imply export

```gherkin
Given an image is allowed for private preview but lacks current rights, watermark, text alternative or publication eligibility
When export or Share is requested
Then the generation Artifact and cost remain intact but no delivery authorization is issued
And the user receives a safe exact remediation or appeal route
```

### AC-IMG-09 — Structured Canvas alternative

```gherkin
Given a non-pointer user selects a region, changes mask polarity/feather, transforms a reference and submits inpaint
When the structured object/list/numeric path is used
Then it produces the same canonical OperationSpec as the Canvas path
And focus, reading position, undo and result comparison satisfy every applicable WCAG A/AA criterion
```

### AC-IMG-10 — Agent and Direct use one spine

```gherkin
Given Chat Agent and Image Studio submit equivalent Image OperationSpecs
When both execute
Then they share Image Definition, Job, Attempt, Artifact, Trust and Usage contracts
And GA receives only an opaque Job handle without image Provider branches or a second charge path
```

### AC-IMG-11 — Output validation precedes completion

```gherkin
Given Provider reports success but output checksum, media type, dimensions, alpha or required provenance is invalid
When finalization runs
Then Job remains finalizing/failed under typed output validation and no ready Artifact/export is exposed
And recovery retries validation/storage receipts without rerunning Provider
```

## 16. Verification and Release Gates

- schema/golden：每family参数、capability、mask polarity/coordinates、EXIF、alpha/colorspace、output dimensions、unsupported
  parameter fail-before-effect。
- property：Canvas transforms、mask revision mismatch、candidate identity、lineage DAG、batch/cancel/unknown、Blob dedupe不合并Artifact。
- adversarial：polyglot/reference malware、SVG/metadata injection、bidi filename、decompression/parser budget、malicious PNG metadata。
- integration/chaos：real object storage + fake/real sandbox image Provider、callback duplicate/late、lease steal、finalizer outage、
  Trust/Usage/Artifact outage、Site rollback/revocation。
- UX/a11y：desktop/mobile、keyboard/screen reader/magnification/speech/switch、Canvas/structured equivalence、RTL/IME、compare/export。
- Trust/legal：minor/likeness/deepfake、rightsbundle、appeal、watermark/provenance、takedown partial purge。

No-Go：arbitraryProvider/node payload；mask mapping无evidence；reference role/rights不明确；candidate串位；source overwrite；
unknown retry；seed false guarantee；private allow绕过export/share；Canvas pointer-only；GA出现imageProvider业务分支。

## 17. External References

- [ComfyUI](https://github.com/Comfy-Org/ComfyUI)：参考queue/history、workflow provenance、mask/upload和结果追踪；普通
  Kokoro用户不获得任意node graph或本地模型管理权限。
- [InvokeAI](https://github.com/invoke-ai/InvokeAI)：参考Canvas layer/lasso/mask与workflow-to-canvas产品交互；Kokoro使用
  typed Draft/Operation而非复制实现。
- [Hugging Face Diffusers pipeline principles](https://github.com/huggingface/diffusers/blob/main/src/diffusers/pipelines/README.md)
  与[inpaint contract](https://github.com/huggingface/diffusers/blob/main/docs/source/en/using-diffusers/inpaint.md)：参考单用途
  pipeline以及base+mask语义；Provider library不是Kokoro product/rights/Job authority。
- [AUTOMATIC1111 WebUI](https://github.com/AUTOMATIC1111/stable-diffusion-webui)：参考variation、inpaint/outpaint、upscale、
  batch和parameter provenance的用户习惯；不采纳任意脚本/扩展、checkpoint或底层参数直接暴露。

## 18. Related Documents

- [PRD-06 Asset](2026-07-25-prd-06-asset-intake-and-attachment-safety.md)
- [PRD-07 Studio Common](2026-07-25-prd-07-studio-common-job-and-cost-ux.md)
- [PRD-14 Accessibility](2026-07-25-prd-14-localization-and-accessibility.md)
- [PRD-16 Trust](2026-07-25-prd-16-trust-content-safety-and-media-rights.md)
- [Model Control/Gateway](2026-07-25-model-control-gateway-litellm-architecture-design.md)

本文批准不授权实现，也不修改 GA runtime。
