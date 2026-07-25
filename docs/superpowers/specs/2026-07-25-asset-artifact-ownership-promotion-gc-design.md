---
artifact: architecture-design
version: "1.0"
created: 2026-07-25
status: internal-review-active
scope: asset-artifact-blob-upload-scan-promotion-derived-input-lineage-rendition-retention-gc
implementationAuthorized: false
gaRuntimeSemanticChangeAuthorized: false
---

# Asset、Artifact、Blob Ownership、Promotion 与 GC

## 1. Decision summary

Asset和Artifact是同一`Media Resource` bounded context中的两个owner modules，不是同一个aggregate，也不是Image/Music/Video
各自的服务：

```text
Media Resource bounded context
  Asset module
    UploadIntent / UploadSession / BlobCandidate
    ScanEvaluation / Asset / AssetVersion / AssetGrant

  Artifact module
    Artifact / ArtifactVersion / LineageEdge
    Rendition / Delivery / Share resource refs

  Blob and Lifecycle module
    BlobObject / StorageReplica / RetentionBinding
    ReferenceGraph / GCPlan / DestructionReceipt

  Workers/process roles
    upload finalizer / scanner / metadata extractor
    artifact finalizer / rendition
    retention / GC / repair
```

V1共享代码库、数据库事务和对象存储adapter，可按worker role独立部署/扩缩容。未来提取服务必须遵循Internal RPC/extraction
规则，不通过“相同interface换adapter”保持虚假原子性。

## 2. Ownership invariants

1. Asset表示用户/业务认可的可复用输入resource；Artifact表示Operation/Job产生的不可变产品output。
2. Blob表示物理bytes/content address，不拥有Site、作品身份、权利、Decision、lineage或customer charge。
3. 相同Blob可被多个AssetVersion/ArtifactVersion引用，但这些identity、Site、rights、retention和deletion永不合并。
4. Scanner/metadata/provider只产生evidence；Trust拥有canonical safety Decision。
5. Job拥有execution/finalization workflow，不拥有ArtifactVersion或Blob；通过idempotent command取得owner receipt。
6. Studio/Library只消费projection/ref；不写Asset/Artifact/Blob authority。
7. storage URL/key不是resource ref；所有byte access使用purpose/audience/TTL-bound grant。
8. GC只能执行Data Governance批准且ReferenceGraph证明安全的GCPlan，不能按age/hash或“数据库没搜到”直接删除。

## 3. Canonical objects

```text
UploadIntent
  immutable siteId / intentId / subjectGeneration / projectRef / purpose
  declared media constraints / quota reservation / expiry / request digest

UploadSession
  immutable siteId / sessionId / intentRef / protocol=tus|multipart
  expected size+checksum / received parts+ranges / lease+expiry / state

BlobCandidate
  immutable siteId / candidateId / uploadSessionRef / temporary object ref
  observed size+checksums / media sniff evidence / quarantine state

ScanEvaluationRevision
  immutable siteId / candidate or version ref / scanner+rules revision
  observed media facts / signals / evidence refs / occurred+observed times

Asset
  immutable siteId / assetId / projectRef / owner subject generation / lifecycle

AssetVersion
  immutable siteId / assetVersionId / assetId / blobRef
  source+upload refs / detected media metadata / scan+Decision refs
  rights+consent+retention refs / supersedes? / state

Artifact
  immutable siteId / artifactId / projectRef / media class / lifecycle

ArtifactVersion
  immutable siteId / artifactVersionId / artifactId / blob or TrackSet refs
  Operation+Job+Attempt+Candidate refs / parent+source lineage
  model+policy+rights+consent+Usage evidence refs / media metadata / state

LineageEdge
  immutable siteId / fromVersion / toVersion / relation kind
  source segment+mapping refs / contribution manifest / operation ref

DerivedInputVersion
  immutable siteId / source AssetVersion|ArtifactVersion / exact representation+range
  transform+mapping / checksum / purpose+allowed audience/deployment
  rights+consent+restriction epochs / issued+expiry / revoke state

BlobObject
  blobId / content hash+algorithm / byte size / encryption+storage class
  replica refs / integrity state / createdAt

ResourceBlobReference
  immutable siteId / resource version / blobRef / role / retention class / active state

GCPlanRevision
  planId / environment+region / candidate blob+resource refs
  reference snapshot+watermark / blockers / authorized actions / expiry

DestructionReceipt
  plan+object+replica refs / deletion outcome / provider receipts
  occurred+verified times / residual or unknown replicas / supersedes?
```

Asset/Artifact union只以typed ref表达；禁止裸`resourceId`让consumer猜kind。

## 4. Upload and intake lifecycle

```text
UploadIntent
→ UploadSession
→ receiving / paused / expired / canceled
→ bytes_complete
→ BlobCandidate quarantined
→ media validation + malware/content scanner evidence
→ Trust Decision
→ Blob promotion + AssetVersion ready
```

- intent冻结Site/Project/subject、purpose、size/type/count/quota；客户端filename/MIME/checksum均不authority。
- multipart/tus支持resume、offset/part checksum和complete CAS；同intent+digest返回同session，不重复quota reservation。
- bytes complete只表示传输完整，不表示scan clean、Trust allow或Asset ready。
- temporary object默认quarantine bucket/class，不能被Web player、Provider、Library、notification或Support直接读取。
- metadata extractor、decoder和scanner运行在resource/cpu/time/decompression budget sandbox；polyglot、archive bomb、active content fail closed。
- Scanner outage保持scanning/quarantine；不得超时自动allow。false positive通过Appeal/新Decision，不改原evidence。
- promotion在一个owner transaction创建BlobObject/ref、AssetVersion、Decision linkage、quota fact和outbox；response丢失查询同receipt。

## 5. Asset lifecycle and grants

- AssetVersion immutable；replace/edit metadata创建新version，旧version只通过lifecycle/restriction facts改变可用projection。
- `AssetGrant`冻结siteId、assetVersion、subject/project、purpose、audience、fields/range、policy/rights/consent/restriction epochs、TTL。
- provider输入不直接获得Asset store凭据；Media Resource创建DerivedInputVersion和短期delivery，Gateway/Capability消费exact ref。
- revoke阻止新grant/effect；已提交Provider effect保留Usage并quarantine/reconcile output。
- same content hash、same filename、same uploader或same represented subject不跨Site/Project继承grant/Decision/rights。
- user delete先停止新grant并创建Data Governance disposition；active Job/lineage/retention/LegalHold按typed blocker收口。

## 6. Artifact finalization

```text
Job/Attempt canonical output fact
→ CreateArtifactVersion command(attempt + outputOrdinal + digest)
→ verify authorized BlobCandidate/provider retrieval
→ validate media/integrity/provenance
→ Trust output Decision
→ persist BlobObject/reference + ArtifactVersion + Lineage + outbox
→ return ArtifactReceipt
```

- identity固定为`siteId + operationId + attemptId + outputOrdinal`；相同digest幂等，不同digest quarantine/conflict。
- Provider success/progress/URL不是Artifact。只有requiredvalidation、Trust、Blob/reference和Artifact receipt完成才ready。
- Artifact finalizer可重试provider object retrieval、validation、Blob promotion和receipt；绝不重跑Provider generation。
- provider retrieval使用Gateway签发的attempt-bound grant，限制host/object/size/MIME/checksum/redirect/decompression；防SSRF。
- output restricted时可保存受控ArtifactVersion/Usage lineage但不生成preview/delivery；具体retention由Trust/Data Governance决定。
- candidate/track/shot独立ArtifactVersion或typedTrackSet ref；partial不能把restricted/unknown slot合并进allowed master。

## 7. Reuse、promotion and conversion

### Artifact used as input

- Library“Use as source”创建新Draft binding/AssetGrant-equivalent authorization，source仍是exact ArtifactVersion。
- Media Resource基于ArtifactVersion创建DerivedInputVersion；不复制Blob、不创建伪Asset、不改变Artifact ownership。
- lineage记录`derived_from/conditioned_by/edited_from/sample_of`等明确relation和segment/mapping。

### Artifact promoted to reusable Asset

只有产品确实需要独立Asset lifecycle（例如素材库、可替换逻辑名称）时，执行显式`CreateAssetFromArtifactVersion`：

- 创建新Asset/AssetVersion identity并引用同Blob。
- 保留source Artifact lineage、rights/consent/restriction/retention最严格继承。
- 不复制bytes、不丢Operation/Usage provenance、不把Artifact删除权变成Asset删除权。
- command有Site/Project/purpose、idempotency、expected source revision和receipt；不是自动promotion。

### Asset converted to Artifact

纯上传不是generated Artifact。只有导入/normalize/rendition等产品Operation有明确output contract时创建ArtifactVersion，并记录source
AssetVersion/transform/Usage；禁止为统一列表把每个Asset伪造成Artifact。

## 8. Rendition and delivery

- rendition是Artifact派生Operation/Job，冻结source version、output profile、rights/a11y/disclosure和cost ceiling。
- same eligible rendition可按exact profile/digest复用ArtifactVersion；不同purpose/rights不因同bytes合并delivery authorization。
- delivery使用短期purpose-bound grant，mint/access均复验Site/subject/project/policy/rights/consent/restriction/TTL。
- URL过期只remint；source/rendition不存在或restricted不触发regeneration。
- CDN/thumbnail/proxy是managed replicas/projections；revoke origin先于异步purge，状态真实表示pending/partial/unknown/complete。

## 9. Blob storage and integrity

- content hash在受信server读取完整bytes后计算；客户端hash只用于resume/early mismatch。
- encryption key scope、region/residency、storage class和replication由policy冻结；Blob ID不暴露bucket/key。
- upload/provider temp、quarantine、ready、retained和deletion-pending使用不同storage state/credential policy。
- integrity scrub产生evidence；corruption不原地替换bytes，标记affected references并从验证replica修复或进入recovery。
- dedupe只在legal/security/residency允许的boundary内物理复用；不可通过timing/quota/hash API泄漏其他Site拥有相同bytes。
- provider callback/object与attempt mapping不明时quarantine，不能按filename/key猜Artifact。

## 10. Retention、deletion and GC

### Reference graph blockers

GC至少检查：

- active AssetVersion/ArtifactVersion/TrackSet/rendition references。
- active Upload/Job/finalizer/DerivedInput/Delivery grants。
- parent/child lineage和Project transfer/migration。
- Share/publication/CDN/thumbnail/search replicas。
- Trust Appeal/rights dispute/illegal-content/legal evidence。
- Data Rights export/delete plan、retention、LegalHold和Support/Finance evidence。
- backup/replica retention与provider deletion certainty。

### GC protocol

```text
discover candidate
→ build reference snapshot at watermark
→ Data Governance disposition
→ create expiring GCPlan
→ revalidate references + epochs immediately before effect
→ revoke origin access
→ delete managed replicas/object with provider identities
→ append per-target outcome
→ DestructionReceipt complete|partial|unknown
```

- discovery/projection不能授权delete；GCPlan是唯一effect authorization。
- new reference aftersnapshot使plan CAS失败；不允许“最终再查一次普通查询”代替强guard。
- provider delete timeout为unknown，reconcile同object request；不重复换bucket/key删除或宣称complete。
- dedup Blob只有最后一个可删ResourceBlobReference且所有global blockers清零才物理删除。
- legal retention结束创建新disposition/plan；不修改旧hold/receipt。

## 11. Site isolation and access

- 所有业务对象、references、unique keys、queue partitions、callbacks、indexes和audit包含immutable siteId；Blob physical identity除外，
  但任何Blob lookup必须经Site-scoped resource ref授权。
- cross-Site source/lineage/Grant/Decision/retention拼接在metadata/bytes/effect前拒绝，错误不泄漏存在性/hash/size/timing。
- Global incident/GC只能用显式列举siteIds/resources/actions的GlobalScope grant，不按email/hash/provider key自动合并。
- object storage credential按worker role/audience最小化；Web、GA、Admin和Support不持有bucket-wide credential。

## 12. Process and deployment placement

- V1 modules位于共享Backend codebase；API负责commands/queries，workers负责scan/finalize/rendition/GC。
- Job process可托管artifact finalizer worker binary，但Artifact module/database owner不变；“托管process”不等于“Job拥有数据”。
- scanner、codec/media parser和high-risk review derivative worker可独立sandbox/scale。
- 不为Image/Music/Video/provider各开repository/service；差异由OperationDefinition、validator和adapter表达。
- 未来独立部署Media Resource service时，先重画Job finalization saga、transaction/outbox和failure states，不共享DB写表。

## 13. Admin and support

- safe projection显示source/lineage、Blob integrity、scan/Decision、grants、retention、replicas、GC plan/outcomes，不默认展示bytes。
- typed commands：RetryUploadFinalization、RescanAssetVersion、RebuildResourceProjection、RetryArtifactFinalization、
  RepairFromVerifiedReplica、RevokeDelivery、CreateAssetFromArtifactVersion、ExecuteAuthorizedGCPlan、ReconcileDeletionOutcome。
- 禁止：MarkClean/Ready、直接改Decision、替换Blob、改lineage/Usage、按hash批删、手工move object冒充promotion。
- evidence/bytes access使用field/action/TTL-bound grant、watermark/redaction、maker-checker（高风险）和每次access audit。

## 14. Acceptance criteria

### AC-MR-01 — Same Blob does not merge resources

```gherkin
Given two Sites or Operations reference identical bytes
When one Asset or Artifact is restricted, deleted or retained
Then resource identity, rights, lineage, quota and lifecycle remain independent
And physical GC cannot occur while any protected reference exists
```

### AC-MR-02 — Bytes complete is not ready

```gherkin
Given multipart upload has all bytes and a matching client checksum
When scan, media validation or Trust Decision is pending
Then no AssetGrant, preview, Provider input or Library-ready state is issued
And the candidate remains quarantined with an owner and recovery path
```

### AC-MR-03 — Artifact finalizer never regenerates

```gherkin
Given Provider output exists but Blob or Artifact receipt persistence crashes
When finalization retries
Then it retrieves and validates the same attempt output and creates one ArtifactVersion
And it never reruns Provider generation or creates a second customer effect
```

### AC-MR-04 — Artifact reuse does not require byte copy

```gherkin
Given an allowed ArtifactVersion is selected as a Studio source
When a new Operation is admitted
Then a purpose-bound DerivedInputVersion references exact source, mapping and epochs
And no bytes, fake Asset identity, rights or Usage history are duplicated
```

### AC-MR-05 — GC revalidates the reference graph

```gherkin
Given a GCPlan was built before a new lineage, LegalHold or active grant appeared
When deletion reaches the effect point
Then expected watermark or reference guard fails and no object is deleted
And a new Data Governance disposition is required
```

### AC-MR-06 — Cross-Site Blob probing fails

```gherkin
Given Site A has bytes with a known hash, size or storage timing
When Site B uploads, searches, references or requests delivery using those facts
Then the system reveals no existence or dedupe signal before Site B establishes its own authorized resource
And no Site A metadata, grant or retention state is inherited
```

## 15. Verification and release gates

- upload：multipart/tus offset/checksum/resume/expire/cancel、quota、polyglot/bomb/parser sandbox和scanner outage。
- artifact：duplicate/late Provider callback、retrieval SSRF/redirect/size、output ordinal、partial TrackSet和finalizer replay。
- lineage：DAG、typed relations、source segment/mapping、promotion/no-copy和sameBlob identity separation。
- access：Asset/DerivedInput/Delivery grants、epoch revoke、cross-Site negative、storage credential and URL leakage。
- lifecycle：retention/LegalHold/activeJob/share/backup blockers、GC race、provider delete unknown、DR restore和destruction receipts。
- operations：projection rebuild、integrity scrub/repair、Admin maker-checker、two-Site quota/dedupe timing和load/soak。

No-Go：bytes-complete=ready；scanner作Decision；Job写Artifact表；Studio/Library写Blob；samehash合并identity；长期storage URL；
Artifact-as-input复制bytes；automatic fake Asset；finalizer rerunProvider；GC按age/hash；delete timeout宣称complete；跨Site dedupe泄漏。

## 16. Related documents and approval boundary

- [PRD-06 Asset Intake](2026-07-25-prd-06-asset-intake-and-attachment-safety.md)
- [PRD-07 Studio Job](2026-07-25-prd-07-studio-common-job-and-cost-ux.md)
- [PRD-09 Library](2026-07-25-prd-09-library-artifact-export-and-share.md)
- [PRD-15 Data Rights](2026-07-25-prd-15-notification-preferences-and-data-rights.md)
- [PRD-16 Trust](2026-07-25-prd-16-trust-content-safety-and-media-rights.md)
- [Platform Modular Core/Internal RPC](2026-07-25-platform-modular-core-internal-rpc-design.md)

本文批准不授权实现或数据迁移，也不修改GA runtime。GA/Session只传opaque Asset/Artifact/Job handles；不得为媒体资源管理向GA
加入Site/User/Blob/storage/rights第二身份轴。
