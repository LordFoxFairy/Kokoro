---
artifact: product-requirements-document
prdId: PRD-06
version: "1.0"
created: 2026-07-25
status: internal-review-active
scope: asset-upload-import-resume-validation-scan-quarantine-attachment-input
accountableProductRole: Asset Product Lead
mandatoryCosigners: [Security, Trust, Privacy, Storage, Web, Session, Job, Support, Data Governance, QA]
engineeringOwner: team:asset-storage-engineering
qaOwner: team:asset-security-quality
supportOperationsOwner: team:asset-recovery-operations
namedOwnerAssignmentStatus: assigned-team-responsibility-ids
implementationAuthorized: false
---

# PRD-06：Asset Intake 与 Attachment Safety

## 1. Overview

### Problem

Chat、Image、Music、Video、Developer Workspace 与 Support 都需要接收文件，但“浏览器选中文件”“对象存储已有
字节”“可以被模型读取”是三个不同事实。若 Web 直接把 presigned URL 当 Asset，或让 Session/Job/Hub 各自实现
上传，将出现跨 Site 引用、伪造 MIME、zip bomb、恶意 SVG/PDF、扫描竞态、配额绕过、孤儿 multipart、删除不彻底
和未扫描输入进入 Provider context。现有 Hub Skill ZIP 上传是 capability package workflow，不是用户 Asset authority；
Session workspace file/download 也不是产品上传系统。

### Solution

建立独立 Asset bounded context，拥有 `UploadIntent`、`UploadSession`、`BlobCandidate`、`ScanEvaluation` 与
`Asset/AssetVersion`，并向 Trust/Platform 提供 eligibility evidence。Web 只获取短时、Site/subject/project/purpose-bound upload capability；
字节先进入不可公开的 quarantine storage，完整性、类型、内容安全、malware 与 policy 全部完成后，才以同一
Platform workflow 原子创建可引用 AssetVersion。Chat/Studio/Job/GA 只消费 opaque、purpose-bound AssetGrant，
永不消费客户端 URL、storage key 或未经 current decision 的 Blob。

### Users and stories

| ID | User story | Priority |
|---|---|---|
| AST-US-01 | 用户可选择、预检、断点续传、暂停/取消文件，并在刷新后恢复同一上传 | P0 if-enabled |
| AST-US-02 | 用户准确看到验证、扫描、隔离、可用、失败及修复动作，不把“上传完成”误报为“可使用” | P0 |
| AST-US-03 | Chat/Studio 只能提交当前 Site、Project、purpose 和 policy 允许的 AssetVersion | P0 |
| AST-US-04 | 用户可删除未使用上传或 Asset，并理解被作品引用、Retention/LegalHold 阻止时的结果 | P0 |
| AST-US-05 | Support/Security 可恢复卡住扫描、隔离危险内容，但不能下载原始恶意字节或直接改表 | P0 |

## 2. Goals、Metrics and Non-Goals

### Goals

1. 字节完整、扫描通过、Asset 可引用三阶段严格分离；scan/quarantine 永远在 Provider effect 前。
2. 所有对象和 storage prefix immutable Site-scoped，任何跨 Site reference 在披露 existence 前拒绝。
3. 上传可恢复、可取消、可回收，重复请求不重复占用 quota 或创建 AssetVersion。
4. filename/MIME/extension 只作提示；server-detected type、policy 与安全 evidence 才决定用途。
5. Asset 删除、Blob 去重、引用、Retention、LegalHold 与 GC receipt 可证明。

### Success Metrics

| Metric | Target |
|---|---:|
| 未通过 current scan/policy 的字节进入 Run/Job/Provider context | 0 |
| cross-Site Asset/Blob/upload capability 泄漏或引用 | 0 |
| 同 upload identity 重复 AssetVersion、quota charge 或 Blob finalize | 0 |
| complete/abort 后 orphan multipart 超 GC SLA | 0；超时 page |
| 用户刷新/断网后恢复同一 offset/part manifest | 100% certification scenarios |
| client MIME/extension 被当安全 authority | 0 |
| required scanner outage 时 fail-open | 0 |
| 删除完成缺 reference/retention/object GC receipt | 0 |

### Non-Goals

- Asset 不拥有 Session Message、Operation、Job、ArtifactVersion、Share 或 Provider execution。
- 不把 object-store checksum、ETag 或 contentHash 当 ownership、rights、scan 或 Asset identity。
- 不在 V1 实现公共任意 URL crawler；URL import 只有独立 allowlisted Connector/Import policy 才可启用。
- 不复用 Hub Skill ZIP upload API；Capability package 有自己的 schema/signing/review authority。
- 不向第三方公共扫描服务上传用户内容，除非 Site/region/privacy policy 明确批准。
- 不承诺 scanner 能证明文件绝对安全；结果是版本化 evidence，使用时仍受 current policy/epoch 限制。

## 3. Product Objects and Ownership

```text
AssetPolicyRevision
  siteId / surface+purpose / allowed detected media classes / size+count limits
  archive/container rules / scanner+CDR requirements / region+retention / expiry

UploadIntent
  siteId / subjectGeneration / projectRef / purpose / client metadata snapshot
  expectedSize / expectedChecksum / policyRevision / idempotencyKey+requestDigest

UploadSession
  uploadIntentRef / protocolRevision / storageTenant+region / quarantineObjectRef
  offsetOrPartManifest / capabilityAudience / expiresAt / state / expectedVersion

BlobCandidate
  siteId / quarantineObjectRef / fullObjectChecksum / byteSize
  clientMediaType / detectedMediaType / signature+container facts / contentHash

ScanEvaluation
  siteId / blobCandidateRef / scanner+signature+policy revisions
  malware/content/CDR/container results / evidenceRefs / outcome / occurredAt

Asset
  siteId / assetId / projectRef / stable logical identity / lifecycle

AssetVersion
  siteId / assetId / versionId / blobRef / sourceUploadIntentRef
  detected media metadata / decision+policy+scan epochs / provenance / createdAt

AssetEligibilityProjection / AssetGrant
  siteId / assetVersionRef / subjectOrExecution audience / purpose / allowed transforms
  policy+restriction+scan epochs / issuedAt+expiresAt / nonce

AssetReference
  siteId / assetVersionRef / ownerContext+resourceRef+version / purpose / lifecycle

ObjectGcIntent / ObjectGcReceipt
```

- Asset context 独占 upload/scan/Asset metadata 与 Blob reference authority；Object Storage 只保存 bytes/observations。
  `ScanEvaluation` 是 evidence，Trust 拥有 canonical safety Decision；`AssetEligibilityProjection` 只组合当前 receipts，
  Platform Admission 才能签发 AssetGrant。Asset/Scanner 不得自行 allow 被 Trust/Restriction deny 的内容。
- `Blob` 可以按 encrypted storage domain + content hash 物理去重，但 AssetVersion、ownership、Site authorization、
  rights、retention 和 audit 绝不合并。跨 Site 默认不物理去重；若未来启用，必须用 per-Site envelope/key 和不可推断
  refcount，不能通过 timing/size/hash 暴露另一 Site 内容。
- filename 原值属于用户 metadata，单独加密/最小化；storage key 使用服务端随机 opaque identity，无扩展名、路径或
  user input。展示/下载 filename 经过 header/Unicode/bidi/path 安全策略，不用于 filesystem path。
- 所有 upload、callback、scan、reference、GC 对象 immutable `siteId`；Provider/object-store callback mapping 以
  `(storageTenantRef, region, providerUploadOrObjectId) -> (siteId, uploadSessionId, candidateId)` 固定，mismatch quarantine。

## 4. Intake and Upload Requirements

### 4.1 Client selection and preflight

- Web 在读取内容前展示 Site Surface 支持的类型、数量、单文件/总大小、用途、费用/配额与 privacy notice。
- client extension/MIME/size/hash 只用于快速 UX 和 request digest；服务端重新验证，客户端拒绝不替代服务端 gate。
- 文件夹、拖放、粘贴、camera/microphone 等入口归一为 typed candidate；clipboard HTML/URL 不自动下载远程内容。
- accessibility：选择/移除/排序/重命名/错误/进度/暂停/继续/取消均有键盘和 AT 路径；进度不逐字节播报。

### 4.2 Intent and quota admission

- `CreateUploadIntent` 从 trusted Site/AuthSession/Project/purpose 编译 policy、storage region 和 storage quota
  reservation；浏览器提交 siteId/project owner/storage key 无扩权作用。
- idempotency 唯一为 `(siteId, subjectGeneration, idempotencyKey)`，保存 request digest；同 key同 digest 返回同
  UploadIntent/Session，同 key不同 digest 冲突。
- quota 分 `upload_inflight`、`quarantine_bytes`、`ready_asset_bytes` 和 `trash_retained_bytes` 投影；不能仅在 complete
  后检查，否则并发 multipart 可突破上限。reservation expiry 仅释放能证明无 committed parts/object 的额度。
- capability 短时、audience-bound，只允许指定 upload/session/object prefix/part size/checksum/byte ceiling；不得 list、
  read、copy、set public ACL、改变 encryption/metadata 或写其他 key。

### 4.3 Resumable bytes

- V1 支持版本化 resumable protocol adapter；可用 tus 1.0 core 或 S3 multipart，但 canonical UploadSession 状态与
  identity 不依赖某 provider header/ETag。
- 每次 resume 查询 server offset/part manifest；client cursor 不可信。part number/range/checksum 重叠冲突拒绝，
  exact duplicate 返回原 receipt。finalize 使用 expected size + full-object checksum；multipart ETag 不冒充内容 hash。
- `completing` 前冻结 part manifest；Complete/Abort 并发由 expectedVersion/CAS 单一获胜。Abort 只有确认 provider
  multipart terminated/object absent 后才释放 bytes reservation；timeout/unknown 进入 reconciliation，不创建第二上传。
- capability 过期可在重新认证/同 generation/policy recheck 后续签原 UploadSession；旧 capability epoch 不可再写。

## 5. Validation、Scanning and Promotion

### 5.1 Validation pipeline

```text
bytes_complete
→ checksum_verifying
→ type_and_container_inspection
→ malware_scan
→ content/trust evaluation where applicable
→ CDR/transcode/safe rendition where policy requires
→ promotion_ready
→ AssetVersion + Blob promotion + reference receipt
```

- 只允许 business-required detected media classes；extension、Content-Type、magic signature、container/codec/internal
  entries 必须相互一致或进入 typed reject/review。SVG/HTML/PDF/Office/archive 等 active/container type 默认高风险。
- archive 检查 nested depth、entry count、expanded bytes/ratio、path traversal、duplicate/case-conflicting names、symlink/
  special file、encrypted entry 与 parser resource budget；未知/加密 archive 默认 reject 或 specialist review。
- scanner/CDR/parser 在无网络、只读、CPU/memory/time/output 限制沙箱运行；原始危险字节不进入日志、Support、
  analytics、thumbnailer、metadata index 或通用 preview。
- `ScanEvaluation` append-only；scanner definition/signature/policy revision 固定。scanner timeout/error/outage 产生
  `scan_unavailable`，required policy 下保持 quarantine，不 fail-open。
- `clean` 只表示该 revision evidence 未发现禁止项；Trust decision、rights/consent 和 current restriction 仍独立。

### 5.2 Atomic promotion

- promotion 同一 Asset UoW 创建 Asset/AssetVersion/AssetReference initial receipt、quota transition 和 outbox；Blob
  server-side copy/tag/rename 若不能同事务完成，用 intention + immutable checksum saga，读授权只在 DB promotion
  receipt 与 storage observation同时成立后发布。
- storage copy 成功但 DB commit 未完成产生 tagged orphan，由 same intent reconciliation 恢复或 GC；绝不按 filename/
  age 猜测归属。DB ready 但 Blob observation缺失保持 `promotion_recovering`，不发 AssetGrant。
- duplicate promote 按 `(siteId, uploadIntentId, promotionPurpose)` 唯一返回同 AssetVersion。
- derived safe rendition/CDR output 是新的 Blob/AssetVersion relation，保留 parent、tool/revision/provenance；不得原地
  替换 raw evidence或声称等价，产品使用 policy 明确 raw/derived 哪个可被模型或用户下载。

## 6. Attachment and Consumer Authorization

- Message draft 可引用 `uploading|scanning` candidate，但 Send/Operation submit 前必须把每个 candidate 解析为 current
  `AssetVersion` + purpose-bound AssetGrant；任一未 ready/denied/expired 时不创建 executable Run/Job。
- Session 只保存 AssetVersion/attachment projection，不保存 storage key、presigned URL、scan authority 或 Blob bytes。
- Platform Admission 验证 Site、subject/project access、purpose/media capability、entitlement/quota、Trust/rights/
  consent/restriction/scan epochs，并为 GA/Job 发 opaque grant。GA 仅透传 grant，不解释 siteId/owner/Blob。
- Provider/Gateway/Worker 通过受控 fetch broker 获取有限 bytes/derived representation；grant 绑定 audience、attempt/
  operation、byte range、transform、TTL，禁止任意 URL/SSRF、list/copy/reshare。
- attachment 在 queued Run/Job 后被 revoke：未 effect Attempt fail；已 effect 仅 finalization/quarantine/reconcile，
  不伪造未发送。原 Run 冻结 lineage，但新 branch/retry 必须 current authorization。

## 7. Lifecycle、Deletion and Data Rights

- 删除 UploadSession 与删除 Asset 不同。未 promoted upload 可 abort + orphan GC；Asset soft delete 先阻止新 grants，
  保留现有 reference/retention/LegalHold 决策。
- AssetVersion 被 Session/Artifact/Support/Legal evidence 引用时，用户看到 reference class 与允许的 unlink/delete/
  replace；不得 cascade 删除别人的 shared content、历史 financial/security fact 或已提交 Provider evidence。
- physical Blob GC 只在所有 AssetReference/retention/LegalHold/refcount 都为零后创建 ObjectGcIntent；object store delete
  receipt + checksum/key version observation 才完成。versioned bucket/delete marker 需继续 lifecycle purge evidence。
- PRD-15 export 包含 requester-related metadata、可允许的原始/derived file 和 manifest；quarantined malware/illegal/
  third-party protected bytes 按 DisclosureDecision omitted/retained，只给安全理由。
- scanner signature 后来发现 false negative 时创建 reevaluation campaign；current grants/references 依 risk policy revoke/
  quarantine，历史 AssetVersion/evidence 不改写，所有 affected Run/Artifact/Share 走各 owner 的 reconcile/takedown。

## 8. User-visible States and Recovery

| State | Meaning | Recovery |
|---|---|---|
| preflight_rejected | client hint 已超明显类型/数量/大小限制 | remove/change file；可访问规则说明 |
| reserving | 创建 intent/quota/capability | wait/query same idempotency |
| uploading | 正在传输 | pause/resume/query server offset/cancel |
| upload_interrupted | 网络或 capability 中断，server progress 已保存 | reauth/renew capability/resume same session |
| completing | parts 已冻结，核验完整对象 | wait/query；不重新 complete 新 upload |
| reconciling_upload | complete/abort provider outcome unknown | wait/Support；禁止第二 upload 消耗同 reservation |
| validating/scanning | 字节完整但不可用 | wait；可离开页面，Notification/Center 可回到状态 |
| scan_unavailable | required scanner 暂不可用 | wait/retry by owner；用户不能选择 fail-open |
| additional_evidence_required | 类型/rights/consent 需输入 | provide safe evidence/change file/cancel |
| quarantined | 风险信号阻止使用 | safe reason/appeal if eligible/delete where allowed |
| promotion_recovering | scan通过但 Asset/Blob receipt 未闭合 | wait/query/Support；Run/Job仍不能提交 |
| ready | current purpose 可引用 | attach/use/delete/manage |
| revoked | 新使用被策略或用户撤销 | replace/remove/appeal；历史 effects单独处理 |
| deletion_pending/retained | 新授权停止，等待 refs/retention/GC | unlink/view safe retention reason/cancel if allowed |
| deleted | logical Asset 删除且 mandatory GC receipt闭合或明确 retained | no access；new upload creates new identity |

## 9. Admin、Support and Operations

- Admin 使用专用 Upload/Scan/Quarantine/GC queues；ResourceTable 不执行 promote、mark clean、release quarantine 或
  object delete。所有命令要求 Site/resource scope、reason、expectedVersion、idempotency、step-up/risk、audit/receipt。
- `RetryScanner` 只为同 BlobCandidate 创建新 ScanEvaluation，不原地改 result；`ReleaseFalsePositive` 由 authorized
  Trust/Security Decision 产生新 eligibility，Support 无权调用。
- `AbortOrphanUpload`、`RetryPromotion`、`ReconcileProviderObject`、`StartReevaluationCampaign`、`ApproveGcIntent`
  逐项登记 OperatorCommandMatrix；跨 Site/mass delete/high-risk evidence access maker-checker。
- Support 只看 filename-safe projection、size/type class、state、safe reason、age、receipts/CTA；不能获取 presigned URL、
  raw malware、scanner signature detail、storage key 或直接下载 archive。
- SLO：upload intent、resume、scan queue/age、promotion、orphan/abort、quarantine review、GC、re-evaluation coverage 按
  Site/Profile/media/policy/scanner revision切分；metrics label 不含 filename/hash/userId。

## 10. Edge Cases

| Scenario | Expected behavior |
|---|---|
| client 声称 image/png，字节是 HTML/SVG polyglot | server detected/container policy 决定 reject/quarantine；不 preview/attach |
| 两 tab 同 key 上传不同文件 | request digest conflict；不复用 capability/storage object |
| part upload 重放 | same part/checksum 返回原 receipt；不同 bytes 冲突并冻结 complete |
| Complete 请求 timeout | query/reconcile provider object；禁止创建第二 UploadSession |
| Abort 与 Complete 并发 | expectedVersion 单一 winner；loser 查询 canonical state |
| scanner outage | `scan_unavailable` quarantine；不发 AssetGrant |
| scan clean 后 restriction revokes | current epoch 阻止新 grant；queued effect fail，submitted effect quarantine/reconcile |
| same bytes 两个 Projects | 可共享物理 Blob policy，但创建不同 AssetVersion/reference/authorization |
| user deletes Asset used by Artifact | new grant停止；unlink/retention policy 决定，不能破坏 Artifact lineage |
| object copied but DB promotion crashes | intent-tagged orphan reconcile/GC；用户不见 ready |
| zip has `../`、symlink、encrypted nested bomb | bounded parser reject/quarantine，绝不展开到通用 filesystem |
| filename 含 CRLF、path、bidi control | storage identity无关；展示/Content-Disposition 安全编码并提供 logical name |
| Site A grant used in Site B | existence-safe deny before object read/metadata disclosure |

## 11. Acceptance Criteria

### AC-AST-01 — Upload is not Asset readiness

```gherkin
Given a browser has completed every upload byte
When checksum, type, scanner, Trust or promotion receipt is incomplete
Then the candidate is not ready and no AssetGrant is issued
And no Run, Job, preview, download or Provider context can consume it
```

### AC-AST-02 — Resumable idempotency

```gherkin
Given an UploadSession has acknowledged bytes or multipart parts
When the browser refreshes, retries an exact part or renews an expired capability
Then server offset/manifest and the same upload identity are returned
And a conflicting part, request digest or subject generation is rejected
```

### AC-AST-03 — Complete/abort race

```gherkin
Given complete and abort commands race for one UploadSession
When expectedVersion is applied
Then exactly one transition wins and the loser queries the canonical state
And quota is released only after storage absence or retained exactly once for the completed object
```

### AC-AST-04 — Server detects content

```gherkin
Given extension and client Content-Type claim an allowed image while bytes contain an active or conflicting format
When validation runs
Then detected signature, container and policy determine rejection or quarantine
And client metadata never authorizes preview, model use or download
```

### AC-AST-05 — Scanner outage fails closed

```gherkin
Given AssetPolicy requires malware or content scanning
When the scanner times out, errors or has an expired signature revision
Then the candidate remains scan_unavailable or quarantined
And retries create versioned evidence without marking the previous result clean
```

### AC-AST-06 — Site and purpose isolation

```gherkin
Given Site A owns an UploadSession, AssetVersion and AssetGrant
When Site B or a different purpose/audience presents any of those refs
Then access is rejected before byte or metadata disclosure
And no timing, hash, filename or existence signal crosses Site scope
```

### AC-AST-07 — Admission gates attachment

```gherkin
Given a Message draft contains ready, scanning and revoked candidates
When Send or Studio submit is attempted
Then only current ready AssetVersions can receive purpose-bound grants
And the executable Run or Job is not created while any required attachment is unresolved
```

### AC-AST-08 — Promotion recovery is effect-safe

```gherkin
Given storage copy succeeds and Asset database commit or response is lost
When reconciliation repeats the same promotion identity
Then exactly one AssetVersion and quota transition exist
And the Provider is not called and orphan bytes are either adopted or garbage-collected with receipts
```

### AC-AST-09 — Reference-aware deletion

```gherkin
Given an AssetVersion is referenced by Session, Artifact, Support evidence or LegalHold
When deletion is requested
Then new grants stop and each owner returns unlink, retain or delete disposition
And physical Blob GC waits for every reference/retention receipt without cascading unrelated content
```

### AC-AST-10 — Archive and filename adversarial safety

```gherkin
Given an archive or filename contains traversal, symlink, nested bomb, CRLF or bidi controls
When intake and display run
Then bounded validation rejects or isolates dangerous bytes without filesystem escape
And storage keys, headers, logs and UI never interpret the user filename as authority or path
```

### AC-AST-11 — Late false-negative response

```gherkin
Given a new scanner revision identifies a previously ready Asset as dangerous
When a reevaluation campaign reaches it
Then current grants are revoked or quarantined under policy and affected owners reconcile
And historical AssetVersion, ScanEvaluation and prior Provider effects remain immutable and auditable
```

## 12. Dependencies、Risks and Milestones

| Risk/Dependency | Mitigation |
|---|---|
| direct-to-storage capability 被扩权 | audience/prefix/size/checksum/operation restrictions + short TTL + epoch |
| multipart/object lifecycle 泄漏成本 | quota reservation、abort/reconcile、provider lifecycle + orphan SLO |
| polyglot/parser exploit | business allowlist、sandbox、signature/container checks、resource budget、CDR |
| scanner false negative/positive | versioned evidence、reevaluation、Trust specialist appeal、no mark-clean command |
| Blob dedupe 泄漏跨站信息 | default Site storage domain、opaque refs、no hash/timing API、per-Site encryption |
| deletion 破坏 lineage | AssetReference participants、retention/LegalHold、GC receipt |
| 误复用 Hub/Session API | architecture dependency gate；独立 Asset contract/service owner |

Wave 3 只冻结 Chat attachment projection/admission gate；Wave 4 实现 Asset/Blob/upload/scan/promotion/GC 与各 Studio
用途；Wave 7 完成 Admin/Support/Trust/Data Rights queues；Wave 9 对每个 enabled Site/Profile 运行真实 object store、
scanner outage、multipart crash、archive bomb、cross-Site、GC/restore certification。

外部模式参考：

- [OWASP File Upload Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html)：采用业务
  allowlist、服务端类型/签名、随机非 Webroot 存储、malware/CDR 与权限/体积限制。
- [tus resumable upload protocol](https://tus.io/protocols/resumable-upload)：参考 offset/checksum/termination 语义；
  authentication、Site authority 和 Asset promotion 仍由 Kokoro 定义。
- [Amazon S3 multipart upload](https://docs.aws.amazon.com/AmazonS3/latest/userguide/mpuoverview.html)：参考 part、complete/
  abort 与 full-object checksum；ETag/Provider state 不成为 Kokoro Asset authority。

本文批准不授权实现，也不修改 GA runtime。

相关合同：[PRD-05 Chat](2026-07-25-prd-05-chat-conversation-run-and-interaction.md)、
[PRD-14 Accessibility](2026-07-25-prd-14-localization-and-accessibility.md)、
[PRD-15 Data Rights](2026-07-25-prd-15-notification-preferences-and-data-rights.md)、
[PRD-16 Trust](2026-07-25-prd-16-trust-content-safety-and-media-rights.md)。
