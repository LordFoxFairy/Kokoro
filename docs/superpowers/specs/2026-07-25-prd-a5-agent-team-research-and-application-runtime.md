---
artifact: product-requirements-document
prdId: PRD-A5
version: "1.0"
created: 2026-07-25
status: internal-review-active
scope: agent-team-task-graph-budget-member-run-research-citation-aggregation-application-revision-deployment-rollout
accountableProductRole: Agent Team and Application Product Lead
mandatoryCosigners: [GA Owner, Job Runtime, Model Platform, Execution Runtime, Trust, Application Runtime, Accessibility, Support, SRE, QA]
engineeringOwner: team:agent-team-application-engineering
qaOwner: team:agent-team-application-quality
supportOperationsOwner: team:agent-team-application-operations
namedOwnerAssignmentStatus: assigned-team-responsibility-ids
implementationAuthorized: false
gaRuntimeSemanticChangeAuthorized: false
---

# PRD-A5：Agent Team、Wide Research 与 Application Runtime

## 1. Overview

### Problem

复杂研究、代码和媒体任务需要多个独立Agent并行，但不能把“多Agent”实现成同一GA graph里的无界fan-out或共享可变目录。每个成员
必须有明确TaskNode、Run、模型/能力、budget slice、Target、产物、失败和取消语义；聚合不能覆盖partial/unknown或二次扣费。

用户还可能把成果部署为长期Application。如果把Deployment当Job terminal、把Routine当daemon，浏览器关闭、版本更新、健康失败、
回滚、secret和流量切换都无法正确治理。

### Solution

建立GA外部AgentTeam domain：TaskGraph版本化、节点依赖、claim lease、成员Run/Job、budget child allocation和aggregation receipt。
Wide Research是它的认证Profile。建立独立Application Runtime：ApplicationRevision→BuildArtifact→EnvironmentDeployment→Rollout→
ServiceInstance；每次build/deploy仍走Admission/Job/Artifact，长期服务独立观察、扩缩容和回滚。

### User stories

| ID | User story | Priority |
|---|---|---|
| TEAM-US-01 | 用户可查看/确认团队计划、节点依赖、成员、预算和预期产物 | P0 advanced |
| TEAM-US-02 | 多个成员可并行执行且不会重复claim、共享危险目录或超出root budget | P0 |
| TEAM-US-03 | 用户可暂停/取消节点或团队，并保留成功、partial、restricted和unknown事实 | P0 |
| RES-US-01 | Research用户可看到查询、来源、引用、证据质量、冲突和未覆盖问题 | P0 |
| APP-US-01 | 用户可从已批准ApplicationRevision构建、预览、部署、canary、promote和rollback | P0 |
| APP-US-02 | 长期应用有健康、费用、secret、日志、域名和停止/删除闭环 | P0 |

## 2. Goals、Metrics and Non-Goals

### Goals

1. Handoff、Subagent、ChildRun和AgentTeamRun四种语义不混淆。
2. TaskGraph节点claim、dependency、budget、workspace和output都有稳定identity与fencing。
3. Team只reserve一次root Hold，成员使用守恒child allocations，aggregator不二次计费。
4. partial/restricted/unknown成员不被聚合器伪装为完整成功。
5. Wide Research提供source/citation/provenance/coverage/contradiction闭环。
6. Application/Deployment/Rollout/ServiceInstance与Job/Routine/SiteRelease概念分离。

### Success metrics

| Metric | Target |
|---|---:|
| 同TaskNode重复claim/Run/Provider effect | 0 |
| member allocations总和超过Team/root ceiling | 0 |
| 并行代码成员无独立worktree仍写同目录 | 0 |
| partial/unknown/restricted被标complete | 0 |
| aggregation重复Usage/charge | 0 |
| Research引用无法定位source revision/evidence | 0 |
| Application promote缺health/certification/rollback | 0 |
| ServiceInstance获得Platform/GA长期credential | 0 |

### Non-goals

- AgentTeam不是GA internal subagent、Handoff、Persona Switch或一个巨大graph node。
- V1不允许用户上传任意orchestrator code、无限递归team/fanout或成员互发未审计prompt。
- Wide Research不保证互联网事实绝对正确，不把单一模型总结当证据。
- Application Runtime不是SiteRelease、Routine、Job或ExecutionTarget；不托管任意未经审核container/root access。
- 本PRD不授权修改GA graph、assembly、subagent inheritance、Handoff、checkpoint、tool、cancel或terminal。

## 3. Canonical objects

```text
AgentTeamRevision
  immutable siteId / teamId+revision / product profile / member role slots
  allowed AgentRevision+ModelOption+Capability sets / max graph+fanout+depth
  budget+target+workspace+aggregation policies / effective window

AgentTeamRun
  immutable siteId / teamRunId / team revision / task anchor / executionRoot
  TaskGraphRevision / root Hold+budget refs / lifecycle / terminal receipt

TaskGraphRevision
  immutable siteId / graphId / ordered TaskNode revisions / dependency edges
  input+output contracts / criticality / graph digest / createdBy plan revision

TaskNodeRevision
  stable nodeId / kind / instructions+context refs / dependency refs
  member role+AgentRevision / model+capability requirements
  target+workspace policy / budget ceiling / output contract / retry policy

TaskClaim
  teamRun+node / claimant Run or worker / claimEpoch / lease+heartbeat / state

TeamMemberExecution
  node+claim refs / Run|Operation|Job owner refs / allocation ref
  progress+interaction+terminal+Artifact+Usage refs

AggregationRevision
  teamRun / input node output revisions / missing+restricted+unknown manifest
  method+model/procedure refs / result Artifact / coverage+quality / receipt

ResearchSourceRevision
  immutable siteId / sourceId / canonical URL or dataset ref / fetched representation
  retrieval time / publisher+date evidence / content digest / rights+Trust refs

CitationBinding
  claim/segment ref / source revision / exact locator+excerpt digest
  support|contradict|background / confidence+review state

Application
  immutable siteId / applicationId / projectRef / owner subject generation / lifecycle

ApplicationRevision
  source Artifact/Repository+commit / build specification / runtime contract
  routes+inputs+outputs / dependency+secret refs / policy+resource profile / digest

EnvironmentDeployment
  immutable siteId / application+revision / environment+region / target runtime
  config+secret revision / active rollout / lifecycle

DeploymentRollout
  deployment / from+to revisions / strategy / traffic steps
  health+guardrails / rollback target / state+receipts

ServiceInstanceObservation
  deployment+rollout / instance provider identity / observed revision
  health+capacity+cost+log safe refs / observedAt
```

## 4. Team planning and approval

- 用户intent先形成PlanProposal：目标、deliverables、TaskGraph、dependencies、member roles、Targets、workspaces、estimated budget和风险。
- plan是proposed diff；用户接受后Platform编译publishedAgentTeamRevision/site inventory并Admission，不等于批准未来未知tools。
- TaskGraph必须DAG；cycle、orphan required node、ambiguous output、unbounded dynamic expansion在effect前拒绝。
- dynamic node只能由Definition声明的expansion point创建，受max nodes/depth/fanout/budget和用户可见revision约束。
- critical node失败/unknown如何影响下游在plan中冻结：block、allow partial input或explicit fallback；不能临场猜。
- member AgentRevision/ModelOption/Capability只从Site published inventory选择；不暴露Provider/secret。
- 如果成员需要新的GA role binding、Handoff或subagent model semantics，plan保持not_enableable并触发GA专项提案。

## 5. Admission and budget

```text
accepted Team Plan
→ one AgentTeamRun + ExecutionRoot
→ one root CreditHold
→ Team parent BudgetAllocation
→ node/member child allocations via Platform CAS
→ Run/Operation/Job per node
```

- child ceiling总和、committed和captured遵循Execution Budget protocol；成员不能拿root完整ceiling。
- dependency blocked/canceled节点未commit额度可fenced return；submitted/unknown额度保持reconciling。
- dynamic expansion只能从parent node unassigned slice切片，不能提高root ceiling。
- 预算不足时team暂停/partial/请求新AuthorizationSegment；不静默降低Model/skip required node/透支。
- aggregator有独立bounded allocation（若使用模型/compute）；读取成员Artifacts不再次计成员Usage。
- retry/fallback Attempts按node frozen policy和logical effect identity；unknown禁止新成员“重新做一遍”。

## 6. Node scheduling、claim and fencing

- Scheduler只对dependencies满足且policy允许的node创建claim；claim+active-count/budget reservation原子。
- `claimEpoch`/lease防stale worker；lease loss不证明member Run/Provider未启动，恢复先查owner receipt。
- 同node最多一个canonical active member execution；speculative parallel仅在Definition显式声明多个candidate slots时使用不同identity。
- node input是dependency output Artifact/version refs和ContextManifest，不复制mutable shared state。
- code nodes默认独立Worktree；媒体/研究节点通过immutableAsset/Artifact/Source refs协作。
- waiting interaction/Target/Connection不阻塞不相关nodes，但保留critical path、deadline和用户notification。
- member terminal由其Run/Job owner决定；Team projection不能自行mark success/canceled。

## 7. Team lifecycle、cancel and recovery

`planning | admission_pending | queued | running | waiting_interaction | partial | cancel_requested | canceled | failed | unknown | completed | cost_pending`

- pause停止新claim，不cancel active members；resume重验SiteRelease、permissions、Targets和budget。
- cancel team向activeowner发送cancel intent，阻止新nodes；逐member保留canonical outcome/Usage/Artifact。
- `cancel_requested`直到所有required member states可归约；一个unknown member阻止“fully canceled”。
- browser disconnect/TaskView loss不影响Team；attach从owner facts恢复，不重复claim。
- coordinator crash从TaskGraph/claims/member receipts/outbox重建；不请求GA重放内部events。
- irreconcilable member按node policy/Support处理，Team可以partial但必须列出missing/unknown和费用状态。

## 8. Aggregation and result quality

- aggregation输入冻结exact member output revisions、Decision/rights、source/citation、Usage和terminal states。
- allowed output不能引用或摘要restricted content给无权限用户；redacted/missing明确标记。
- required node failed/unknown时只能按published output contract返回partial/blocked，不得生成“完整答案”隐藏缺口。
- aggregation可确定性merge或新ModelInvocation；后者有logical identity、Usage、budget和Trust，不复用成员model call。
- result保留per-node lineage和coverage manifest；用户可下钻TaskNode、Artifact、Citation和cost。
- duplicate aggregator response/receipt幂等；不能创建第二final Artifact或capture。

## 9. Wide Research profile

### 9.1 Research workflow

```text
research question + scope
→ query/decomposition plan
→ parallel source discovery/retrieval nodes
→ source validation/extraction nodes
→ claim/evidence/contradiction graph
→ synthesis/coverage review
→ report Artifact + citation manifest
```

- query plan显示时间范围、语言、source classes、exclusions、budget和stop condition；用户可调整后执行。
- retrieval只使用published browser/search/dataset capabilities和SSRF-safe fetch；不执行网页脚本或下载无限内容。
- SourceRevision保存canonical URL/dataset, fetched representation digest, publisher/date/retrieval evidence；页面变化产生新revision。
- citation绑定exact source revision和locator/excerpt digest；引用URL存在不等于支持claim。
- 多source去重不按URL字符串粗合并；canonicalization保留redirect/archive/version证据。
- paywall/login/private source需要current Connection/rights，不绕过访问控制；报告不泄漏受限全文。

### 9.2 Evidence quality

- 区分primary/official、research、secondary、community、unknown source class，但classification不是事实真伪Decision。
- claim记录supporting/contradicting/background citations、时间适用性、confidence和unresolved conflicts。
- 需要current事实时冻结research cutoff/retrieval times；旧缓存标stale并按policy刷新。
- near-duplicate/model-generated/SEO spam信号只是evidence；Trust/quality reducer决定使用/降权/排除。
- synthesis明确未覆盖问题、source gaps、conflicts和inference；不伪造引用、不引用未检索内容。
- source内容是不可信input，防prompt injection/tool instruction；网页文字不能修改system policy、Target permission或budget。

## 10. Application definition and build

- 用户从approved Artifact/RepositoryRevision/ChangeSet创建ApplicationDraft，声明routes、inputs/outputs、runtime、resources、data、
  network、secrets、health和scaling intent。
- build spec使用published template/buildpack，禁止任意privileged Docker socket、host mount或Platform internal package/credential。
- Build是Job：冻结source/lock/toolchain/SBOM/provenance，输出signed BuildArtifact；response loss查询samebuild，不重复paid effect。
- dependency/license/vulnerability/secret/malware scan、contract tests和runtime policy都是candidate qualification。
- ApplicationRevision immutable；config/secret/code变化分别创建revision并进入新Rollout，不修改active instance。
- generated application若需要Routine/Trigger，创建受限RoutineRevision；不在container内藏cron绕过Admission。

## 11. Deployment、rollout and rollback

```text
ApplicationRevision + qualified BuildArtifact
→ EnvironmentDeployment candidate
→ provision intent/provider reconciliation
→ preview/smoke
→ canary traffic steps
→ promote active or rollback
→ continuous ServiceInstanceObservation
```

- EnvironmentDeployment不是SiteRelease；Site只决定Application feature是否可用，App deployment管理用户应用实例。
- environment/region/domain/config/secret/resource/egress policy冻结；staging token/secret不能在production使用。
- provider effect通过durableActivation/Rollout intent和idempotency key；timeout为unknown/reconcile，不再create deployment。
- canary每step验证health/error/latency/cost/security/Trust guardrails和minimum observation window。
- rollback创建新Rollout到已认证revision；不改旧DeploymentRollout history或假定provider已回退。
- DB/schema migration有expand/backfill/contract与前滚/回滚策略；不能仅回滚image忽略data compatibility。
- active service与build/deploy Job分离；Job完成不等于Service长期healthy。

## 12. Runtime safety、secrets and operations

- ServiceInstance只获得application-scoped runtime identity和secret leases，不获得Platform DB、GA、Site workload、Provider master secret。
- ingress/domain/certificate通过typed provider intent；不接受任意Host绑定或让App伪装Kokoro Site。
- egress、CPU/memory/storage/concurrency/request size和execution time按resource profile；noisy app不影响其他Site。
- logs/traces/metrics只通过tenant-scoped collection；默认redact secret/PII/prompt，不让用户查询其他App/Site。
- health observation是evidence；Deployment reducer决定degraded/active/rollback，不让instance自报healthy即promote。
- scale-to-zero/cold start/idle cost按Offering显示；persistent service成本不是某个Build Job无限Hold。
- suspend阻止new traffic/effects但保留data/receipt；delete走Data Governance、domain/certificate/secret/storage/backup disposition。

## 13. TaskView and user experience

- AgentTeamRun和Application Build/Rollout分别产生TaskView anchor；ServiceInstance长期状态在Application页面，不伪装永不终止Task。
- Team视图提供graph/list、critical path、member status、budget、interactions、Artifacts和partial/missing manifest。
- Research视图提供query plan、sources、claims/citations、conflicts、coverage和report。
- Deployment视图提供revision diff、build qualification、rollout steps、traffic、health、cost和rollback。
- graph/timeline都有keyboard/screen-reader list/table替代；颜色/animation不是唯一状态。
- Web/CLI/Desktop/Mobile attach同projection；mutation路由真实TeamRun/Node/Deployment owner。

## 14. Admin and support

- Team Console：TaskGraph/claims/member owner/budget/Usage/Artifact/aggregation/reconciliation safe projection。
- Research Console：source retrieval/Trust/citation/coverage，不默认展示受限全文。
- Application Console：revision/build/SBOM/deployment/rollout/instance/health/domain/secret refs/cost/retention。
- typed commands：PauseTeamClaims、FenceTaskClaim、ReconcileMemberExecution、RetryAggregationFinalization、RestrictResearchSource、
  RebuildTeamProjection、PauseRollout、PromoteCertifiedStep、RollbackDeployment、ReconcileProviderDeployment、SuspendApplication。
- 禁止mark member/Team healthy/completed、改Usage、rerununknown、读取secret、跨Site source、直接改traffic/provider或DB mutation。

## 15. Acceptance criteria

### AC-TEAM-01 — One node has one canonical claim

```gherkin
Given multiple schedulers or workers race for one ready TaskNode
When claims and member execution are created
Then exactly one canonical claim epoch and owner execution commits
And stale claimants cannot create Run, Job, budget, Artifact or terminal facts
```

### AC-TEAM-02 — Team budget conserves root

```gherkin
Given members, dynamic nodes and aggregator request budget concurrently
When Platform allocates child slices
Then all active, committed and captured amounts remain within one Team/root ceiling
And no member, retry, Job or aggregator creates a second Hold or double charge
```

### AC-TEAM-03 — Partial and unknown remain visible

```gherkin
Given required members are allowed, failed, restricted and unknown
When aggregation runs
Then output follows the frozen partial/blocked contract with an exact missing manifest
And no restricted or unknown contribution is hidden inside a completed claim
```

### AC-TEAM-04 — Code members do not share mutable worktree

```gherkin
Given two team members modify the same repository
When they execute in parallel
Then independent Worktrees and ChangeSets isolate writes and budget/action receipts
And integration requires explicit conflict/diff/merge review
```

### AC-RES-01 — Citation supports an exact claim

```gherkin
Given a report contains a factual claim and citation
When the user opens evidence
Then the citation resolves to the exact retrieved SourceRevision and locator used in synthesis
And missing, contradictory, stale or background-only evidence is not presented as direct support
```

### AC-RES-02 — Source prompt injection cannot control the team

```gherkin
Given retrieved content instructs the Agent to change tools, reveal secrets or ignore policy
When extraction and synthesis process it
Then content remains untrusted evidence under the frozen task contract
And no permission, Target, budget, system instruction or external effect is changed
```

### AC-APP-01 — Deployment response loss creates one rollout

```gherkin
Given provider accepted a deployment or traffic step before response loss
When reconciliation runs
Then the same rollout/provider operation is queried to a canonical outcome
And no duplicate environment, domain, instance or traffic promotion is created
```

### AC-APP-02 — Rollback is a new audited rollout

```gherkin
Given a canary breaches a guardrail after traffic was shifted
When rollback is requested
Then a new Rollout references the certified prior revision and reconciles provider traffic
And history, Usage, health evidence and data migration state are not overwritten
```

### AC-APP-03 — Application has no Platform credential

```gherkin
Given a deployed application needs databases, APIs or secrets
When runtime credentials are issued
Then each lease is application/environment/resource-scoped and revocable
And no Platform DB, Site workload, GA, Model Provider or other Application secret is exposed
```

## 16. Verification and release gates

- Team：DAG/cycle/dynamic expansion、claim/lease races、dependency/partial/cancel/unknown、budget property和projection rebuild。
- workspace/target：per-memberWorktree、permission、Connector/Target revoke、interaction和multi-device attach。
- Research：retrieval SSRF/size/rights、prompt injection、source canonicalization/version、citation locator、contradiction/coverage。
- Application build：source/lock/SBOM/signature/license/vulnerability/secret、sandbox/network和determinism。
- Deployment：provider unknown/idempotency、canary/guardrail/traffic race、rollback/data migration、region/domain/certificate、DR restore。
- security/a11y：two-Site/member/source/App isolation、secret leases、logs/metrics、graph/list equivalence和complete process。

No-Go：AgentTeam=GA subagent；unbounded fanout；duplicateclaim；sharedmutableworktree；child sum超root；aggregator二次扣费；
partial洗白；伪引用；source控制tools；Application=Job/Site/Routine；provider timeout新建deployment；rollback改历史；App拿Platform secret。

## 17. Related documents and approval boundary

- [Execution Budget Protocol](2026-07-25-execution-budget-allocation-protocol-design.md)
- [PRD-A2 ExecutionTarget](2026-07-25-prd-a2-target-device-permission-and-interaction.md)
- [PRD-A3 Developer Workspace](2026-07-25-prd-a3-developer-workspace-context-and-multidevice.md)
- [PRD-A4 Routine](2026-07-25-prd-a4-routine-connector-and-taskview.md)
- [Asset/Artifact ownership](2026-07-25-asset-artifact-ownership-promotion-gc-design.md)

本文批准不授权实现、真实多Agent运行或应用部署。默认实现路径是GA外部AgentTeam coordinator调用既有Run/Job边界；若任何需求必须
修改GA graph、assembly、subagent inheritance、Handoff、checkpoint、tool、cancel、terminal或namespace，必须停止并专项与用户对齐。
