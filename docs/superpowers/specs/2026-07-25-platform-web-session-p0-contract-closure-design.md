---
artifact: architecture-decision-set
version: "1.0"
created: 2026-07-25
status: internal-review-active
scope: web-fleet-dependency-certification-dag-ga-opaque-model-authorization-job-cost-finality-session-access
implementationAuthorized: false
gaRuntimeSemanticChangeAuthorized: false
---

# Platform、Web、Session P0 Contract Closure

## 1. Purpose and authority

本文关闭目标架构红队发现的五项互斥合同。它是以下目标文档的强制子方案；上游摘要与本文冲突时必须修订上游，不能让
实现者二选一：

- Site Web source/dependency authority。
- Profile qualification与Release certification DAG。
- GA到Model Gateway的opaque authorization。
- Job execution completion与cost finality。
- BFF到Session的Site/subject authorization wire contract。

本文不授权实现。凡要求修改GA graph、assembly、state/checkpoint、tool schema、HITL、Handoff、namespace、cancel或terminal
语义的方案仍为No-Go，必须单独获得用户批准。

## 2. System invariants

1. 一个Site对应一个独立、产品命名的Web Project；不同Site不共享用户身份、runtime state或deployment artifact。
2. 共享Backend、GA和Web capability source不等于共享Site Project lock/release authority。
3. Certification digest graph必须可从既存叶节点单向计算，不允许占位、自引用或事后改写digest。
4. GA只消费opaque namespace、opaque Job/Artifact handle和opaque modelAuthorizationHandle，不解释业务claims。
5. Session可以消费Site/subject/workspace/project授权，但这些claims不进入GA wire。
6. execution完成、Artifact可用、usage evidence durable和customer cost final是正交状态。

## 3. ADR-WEB-01 — Web Fleet Source and Dependency Authority

### Decision

采用独立Fleet Project authority：

```text
Shared Web Capability Source
  → build/test/sign/publish immutable semver packages
  → package registry + provenance + compatibility manifest
  → independent product-named Site Web Project
       own repository/source history
       own package lock
       own CI/security evidence
       own artifact/image digest
       own domain/release/rollback
```

- Kokoro根workspace的单pnpm lock只治理Backend、Session、Platform、Admin和共享capability source workspace。
- Site Web Project不是根pnpm workspace leaf，不以workspace/source path引用未发布共享包。
- 每个Site Project可以位于独立repo、submodule或独立CI checkout；物理托管方式不改变其dependency authority。
- Project使用产品自身名称，不要求`site-*`目录或包名前缀。Platform只保存opaque SiteProjectBinding与release evidence。
- `kokoro-web/apps/user`在迁移期作为reference Site Project source，目标态必须从共享source workspace的单lock承诺中移出；
  `apps/admin`属于共享Platform Admin，不是某个用户Site。
- shared package发布包含source digest、SBOM、license/provenance、Node/React/Next compatibility、migration notes和签名。
- Site Project只升级显式版本并提交自己的lock diff；中央批量升级创建逐Project PR/candidate，不直接改active deployment。

### Consequences

- 一个Site升级或回滚不会改变其他Site build provenance。
- 共享修复需要Fleet campaign，而不是假设一次root lock变更自动升级所有Site。
- CI必须认证registry compromise、yanked package、compatibility floor、orphan project和批量回滚。

### Rejected

- 单Monorepo/单lock承载所有Site app：不能提供用户要求的独立Project dependency/release authority。
- 复制共享source到每站：会产生不可治理fork和安全漂移。
- production直接引用workspace package：无法证明已发布版本、回滚和供应链边界。

### Acceptance

- Site A package/lock升级不改变Site B source、lock、artifact digest或deployment evidence。
- shared critical fix可列出所有eligible/blocked/pending Site Projects及其真实版本，不能以package发布成功冒充Fleet完成。
- production build检测到workspace/file/git-floating dependency时fail closed。

## 4. ADR-REL-01 — Certification DAG and Trust Root

### Decision

把“能力合格”和“具体Release合格”分成两层：

```text
PRD/spec/contract/test/runbook/source revisions
  → CapabilityQualificationAttestation
  → ProfileCandidateCompile
  → EffectiveInventoryRevision + Config/Image/Package digests
  → Preview/Integration/Negative/Operational evidence
  → ReleaseCertificationInstance
  → ActivationAuthorization
```

#### CapabilityQualificationAttestation

在具体SiteRelease之前存在，绑定：

- capability/surface/operation/model option revision。
- PRD、contract schema、test suite、runbook、owner与qualification evidence digest。
- supported environment/locale/browser/provider/jurisdiction范围。
- issued/expiry/revocation、signer set与qualification policy revision。

Profile candidate compile只要求当前有效且覆盖目标范围的Qualification，不要求尚不存在的Release certificate。

#### ReleaseCertificationInstance

在candidate compile/build/preview之后产生，绑定：

- siteId、SiteReleaseCandidate、Profile revision与EffectiveInventory digest。
- source/package lock/SBOM/config/image/database migration digests。
- qualification set digest和实际preview/E2E/security/a11y/ops/rollback evidence。
- signer set、issued/expiry/revocation与CertificationPolicy revision。

Activation只接受完整ReleaseCertificationInstance；certificate不能复用于不同Site、candidate或digest。

### Canonical digest rules

- 每个node先canonical serialize，再hash；集合排序、schema version、hash algorithm和signing envelope固定。
- certificate只引用已存在的child digests，不把自己的ID/signature/digest放入preimage。
- signature envelope在content digest之后生成；多签以独立签名集合包裹同一content digest。
- correction创建新revision并supersede，绝不改写旧attestation/certificate。

### Failure semantics

- qualification过期/撤销：新compile fail；active release按restriction policy drain/suspend，不静默继续。
- candidate evidence失败：保持candidate/failed，不能生成partial certificate。
- signer/KMS outage：candidate可保留，activation blocked；不得临时关闭signature gate。
- rollback使用目标旧artifact自己的有效certificate或重新认证，不能仅因“曾active”跳过当前restriction epoch。

### Acceptance

- 从叶子revision到ActivationAuthorization可拓扑排序且无环。
- 首个Release不需要placeholder/self-signed evidence即可compile和certify。
- 修改任一inventory/config/image/lock digest都会使旧ReleaseCertificationInstance不匹配。

## 5. ADR-GA-01 — Opaque Model Authorization Handle

### Decision

Platform Admission创建server-side `ModelExecutionAuthorizationRecord`；GA/Job Worker只获得高熵随机
`modelAuthorizationHandle`。handle不是可解析JWT，不含可读业务claims。

```text
Platform Admission transaction
  persist AuthorizationRecord + root Hold/allocation linkage
  persist GatewayAuthorizationOutbox
    → Gateway materializes encrypted authorization record
      → return opaque handle to execution manifest

GA BaseChatModel adapter
  handle + logicalModelCallId + typed model request
    → Gateway local authorization resolution/atomic budget consumption
      → ModelInvocation/Attempt/Usage facts
```

`ModelExecutionAuthorizationRecord`由Platform/Gateway解析，冻结siteId、billingAccount、executionRoot、rootHold、allocation、
RatingPolicy、PlanModelGrant、EffectiveBundle、surface/operation/agent refs、restriction epochs、audience、budget、issued/expiry。

GA约束：

- 只透传handle；不得decode、branch、index、join或持久化claims。
- 日志最多记录salted correlation hash，不输出raw handle。
- handle不能作为namespace、user、Site、Plan或model role identity。
- Gateway写入Usage linkage；GA的terminal token projection不是计费authority。

### Multi-turn、resume and revocation

- authorization是execution root/segment级，Gateway在其内原子派生并消费per-invocation budget。
- GA无需每个turn调用Platform；Gateway本地记录和signed deny/epoch feed决定有效性。
- HITL pause可能超过TTL时，由Session/Platform在resume admission前轮换handle；旧handle不能创建新Attempt。
- attach只可恢复同logical invocation；unknown outcome禁止创建新Attempt。
- Gateway authorization materialization未确认时Run不得dispatch；Gateway outage时不回退到绕过authorization的direct provider。

### Mandatory spike and GA gate

Phase A所有主agent、subagent和Handoff仍使用同一`assistant.primary`。必须先证明现有execution metadata可产生crash-stable
`logicalModelCallId`。若必须修改GA checkpoint/state、assembly或Handoff model binding，立即停止并提交专项GA提案。

### Acceptance

- GA wire/manifest/storage中不存在可读Site/User/Workspace/Billing/Plan/Price claims。
- 两Site使用相同request/model时，Gateway仍按record严格隔离Usage、Hold和callback。
- handle泄漏到错误audience、过期、撤销、request digest不匹配或allocation耗尽时均在Provider effect前拒绝。
- 五轮model/tool循环只消费五个logical invocation；crash/attach不重复Provider effect。

## 6. ADR-JOB-01 — Execution Completion vs Cost Finality

### Decision

Job execution和cost使用两个正交状态机：

```text
Provider canonical outcome
 + local AttemptUsageFact/outbox durable
 + required output validation
 + required Blob/ArtifactVersion/Trust receipts
 = Job product completion eligible

Canonical usage ingestion
 → rating
 → capture/release/correction
 = cost finality
```

- `AttemptUsageEvidenceReceipt`表示producer本地UsageFact/outbox已durable，是terminal Attempt与Job completion必要证据。
- `CanonicalUsageIngestReceipt`、Rating和Settlement异步推进cost projection，不阻塞合格Artifact交付。
- rating outage时Job可`completed|partial + cost_pending`；root Hold/committed allocation不得因timeout释放。
- terminal Attempt缺Usage evidence不能默认为0；进入finalizing/reconciliation并page owner。
- finalizer只补验证、Blob、Artifact、Trust、Usage/Notification receipts；绝不重复Provider effect。
- late Usage correction追加revision，不改Job execution terminal或原Usage fact。

### Acceptance

- Rating服务完全不可用时，已具有durable Usage evidence的合格作品仍可按policy交付并显示cost_pending。
- producer outbox重放不会重复capture；settlement恢复后同allocation只结算一次。
- 缺Usage evidence、unknown Provider outcome或缺required Artifact receipt时不能伪造completed。

## 7. SessionAccessGrant and BFF Security Contract

### Boundary

浏览器只持有Site Web auth session。BFF使用workload identity和server-resolved SiteContext向Platform Authorization换取
audience-bound `SessionAccessGrant`；浏览器不能自行构造Site、namespace或workspace claims。

```text
Browser auth cookie + CSRF/origin proof
  → Site Web BFF
    → Platform authorize actor/action/resource/current epochs
      → SessionAccessGrant(aud=session)
        → Session HTTP/SSE/read/control
          → GA dispatch manifest(namespace + opaque handles only)
```

### Grant claims

- grantId、audience、issuer、issued/not-before/expiry、key revision。
- immutable siteId、actorRef、subjectGeneration、AuthSessionRef。
- workspace/project refs与允许的session/run/read/control actions。
- membership、authorization、restriction和credential epochs。
- optional exact session/run resource binding、request class和delegation chain。

Session消费这些业务claims，但只把上游已解析的opaque namespace传GA。namespace不等于subject、owner或siteId。

### Session authorization index

Session维护由Platform事件/同步查询构建的最小authorization projection：Site、subject generation、workspace/project membership、
restriction epochs和resource bindings。它不成为Identity owner；用于在每个read/SSE/control effect point fail closed。

### HTTP、SSE and snapshot

- create/read/list/control/SSE使用同一authorization evaluator，不存在“GET较宽、control较严”的分叉。
- SSE credential短期、audience/resource-bound；reconnect可轮换grant但cursor必须绑定siteId、sessionId、subject generation和stream epoch。
- heartbeat、idle timeout、slow consumer/backpressure、connection quota、deploy drain与cursor retention由Session transport child spec冻结。
- snapshot是完整长期页面projection，至少包含当前messages/runs/interactions/artifact/job refs与watermark；SSE只传增量。
- cursor过期返回typed snapshot-required，不要求浏览器从全历史SSE重建真源。

### Revocation and non-disclosure

- membership remove、subject generation变化、Site suspend、AuthSession revoke与restriction epoch更新通过signed feed/outbox生效。
- stale grant在所有read/control/SSE effect point拒绝；active connection在revocation budget内关闭。
- unauthorized与不存在对外使用相同safe envelope/latency class，不泄漏其他Site/resource存在性。
- BFF/Session日志不记录cookie、raw grant、prompt或跨Site identifiers；只使用安全correlation refs。

### Acceptance

- Site A grant访问Site B session/read/SSE/control全部拒绝且零存在性泄漏。
- Workspace revoke、Project transfer、subject generation变化和Site suspend在规定epoch SLA内终止旧read/control/SSE能力。
- SSE断线用新grant+旧合法cursor恢复不重复message；跨subject/site cursor拒绝。
- snapshot可在无历史SSE的干净浏览器上完整重建页面。
- GA收到的manifest不增加Site/User/Workspace claims或第二身份轴。

## 8. Cross-decision failure matrix

| Failure | Required behavior |
|---|---|
| shared package发布成功、部分Site升级失败 | Fleet显示per-Project状态；不宣称全量完成 |
| qualification撤销、candidate尚未active | compile/activation fail；保留可审计candidate |
| Gateway authorization outbox延迟 | Run不dispatch；不直连Provider绕过 |
| handle在Provider send后结果unknown | attach/reconcile；不发新handle绕过同effect |
| Artifact完成、Rating outage | completed/cost_pending；Hold保持并后台结算 |
| Session grant过期但SSE连接仍活跃 | revocation/expiry关闭；新grant按绑定cursor恢复 |
| Platform epoch feed失联 | security-critical grant按短grace/fail closed，不无限LKG |

## 9. Verification and exit gates

- Web Fleet：两独立Site Project lock/artifact/rollback、registry compromise、bulk upgrade/partial failure、SBOM/license evidence。
- Certification：DAG cycle detector、canonical digest golden、多签/rotation/revoke、first release、rollback和tamper tests。
- Model auth：handle entropy/audience/TTL/revoke、multi-turn budget、two-Site negative、Provider effect crash points、attach和Usage守恒。
- Job/cost：producer outbox、Rating outage、late correction、finalizer replay、missing evidence和Hold aging。
- Session：cross-Site/membership/subject generation matrix、HTTP/SSE parity、cursor binding、snapshot rebuild、revocation soak和deploy drain。

No-Go：Site Project production引用workspace源码；Certification自引用/placeholder；GA可读业务claims；Gateway outage绕过授权；
Job等待Rating才完成或缺Usage evidence仍完成；namespace=owner授权shortcut；snapshot依赖全历史SSE；stale grant继续control。

## 10. Related documents

- [Platform/Web/Session target architecture](2026-07-25-platform-web-session-target-architecture-design.md)
- [Wave 0 repository foundation](2026-07-25-wave-0-repository-contract-foundation-design.md)
- [PRD-00 Launch Profile](2026-07-25-prd-00-launch-profile-and-journey-contract.md)
- [PRD-05 Chat](2026-07-25-prd-05-chat-conversation-run-and-interaction.md)
- [PRD-12 Site Fleet](2026-07-25-prd-12-site-lifecycle-and-fleet.md)
- [Model Control/Gateway/LiteLLM](2026-07-25-model-control-gateway-litellm-architecture-design.md)

本文退出internal review后仍不授权实现。它只关闭目标设计冲突，并成为后续Wave child spec与implementation plan的上游。
