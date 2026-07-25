---
artifact: product-requirements-document
prdId: PRD-A1
version: "1.0"
created: 2026-07-25
status: internal-review-active
scope: agent-catalog-revision-publish-select-persona-delegation-subagent-handoff-visibility-recovery
accountableProductRole: Agent Product Lead
mandatoryCosigners: [GA Owner, Session, Model Platform, Capability, Trust, Accessibility, Support, SRE, QA]
engineeringOwner: team:agent-product-engineering
qaOwner: team:agent-runtime-quality
supportOperationsOwner: team:agent-operations
namedOwnerAssignmentStatus: assigned-team-responsibility-ids
implementationAuthorized: false
gaRuntimeSemanticChangeAuthorized: false
---

# PRD-A1：AgentRevision、Selection 与 Handoff

## 1. Overview

### Problem

Kokoro希望封装Agent 1/2/3等产品Agent，并允许Agent在合适时转交给另一个Agent。但当前容易混淆四种不同语义：只换prompt的
Persona Switch、父Agent仍主导的Delegation/Subagent、跨Run的AgentTeam，以及同一Run内主导Agent真正转移的Handoff。如果都叫
handoff，会导致model/tools/skills/policy、checkpoint、pending effect、HITL、费用和terminal无法恢复。

### Solution

建立Platform Agent Catalog与immutable AgentRevision；Site/Surface发布可见或hidden default AgentOption。Core Phase A继续使用
现有单一主assistant与现有GA assembly/subagent/swarm语义。Advanced Phase B才引入真实Handoff：仅沿published edge、在safe boundary、
以稳定HandoffIntent/Commit把同一Run的activeAgentRevision转给receiver，并冻结context/capability/model/budget变化。

本文可作为产品设计评审，但真实Handoff实现必须另获用户对GA语义的逐项批准。

### User stories

| ID | User story | Priority |
|---|---|---|
| AGT-US-01 | 用户可在Site允许时选择已发布Agent，并理解其能力、数据、费用和限制 | P0 advanced |
| AGT-US-02 | Site可配置一个不展示选择器的hidden/default主Agent | P0 |
| AGT-US-03 | Agent可建议或自动执行published Handoff，并向用户显示当前主导Agent和原因 | P0 Phase B |
| AGT-US-04 | Handoff后上下文、pending interaction、budget、permissions和Artifacts可确定恢复 | P0 Phase B |
| AGT-US-05 | 用户可停止、拒绝、返回或重新开始，不产生重复tool/model/effect | P0 |
| AGT-US-06 | Admin可发布、canary、撤销AgentRevision和Handoff edge，不改运行中revision | P0 |

## 2. Goals、Metrics and Non-Goals

### Goals

1. Agent、Persona、Subagent、Handoff和AgentTeam语义严格分离。
2. AgentRevision不可变并完整声明instructions、model roles、capabilities、policy和Handoff edges。
3. SiteRelease编译唯一Agent assignment；运行时不临场使用global default或未发布Agent。
4. Handoff只在effect-safe boundary发生，crash/replay不会双转移或重放tool。
5. model/capability/budget/permission变化对用户可见且由Platform/Gateway/Capability owner授权。
6. Phase A保持现有GA行为；Phase B所有GA变化由专项审批和differential corpus门控。

### Success metrics

| Metric | Target |
|---|---:|
| Persona/Delegation/Subagent/AgentTeam误标为Handoff | 0 |
| 未发布/跨SiteAgentRevision或edge进入Run | 0 |
| Handoff crash/replay造成双commit或重复effect | 0 |
| receiver获得未声明tool/skill/model/permission | 0 |
| Handoff后active agent、状态或费用无法解释 | 0 |
| Phase A adapter cutover改变graph/event/tool/HITL/terminal | 0 |
| 未获用户批准实施Phase B GA semantic change | 0 |

### Non-goals

- V1 Core不要求真实Handoff；General Chat可使用hidden `assistant.primary`单Agent。
- 不允许用户上传任意system prompt/runtime code或自由拼装model profile/tools。
- Handoff不是新Run、Job、AgentTeam node、model fallback、Persona Switch或“换个名字继续”。
- 不把AgentRevision发布权交给GA；Platform Catalog/Release拥有发布和assignment。
- 不让GA解释Site/Plan/Credit/Price/Provider secret；只接收opaque compiled manifest/handles。
- 本PRD本身不授权GA graph/assembly/checkpoint/tool/HITL/Handoff/cancel/terminal修改。

## 3. Canonical product objects

```text
AgentDefinition
  logical agentId / stable product identity / owner / lifecycle

AgentRevision
  agentId+revision / instructions+prompt template refs
  required model role manifest / skill+MCP+tool capability requirements
  memory/context policy / Trust+interaction policy
  handoff edge refs / evaluation+certification refs / immutable digest

AgentOptionRevision
  immutable siteId / user-facing label+description / AgentRevision ref
  visible|hidden / allowed surfaces+plans / capability+cost disclosures

SurfaceAgentAssignmentRevision
  immutable siteId / surface+release / default AgentOption
  visible options / hidden internal agents / rollout+expiry

EffectiveAgentManifestRevision
  immutable siteId / run or release compile scope
  exact AgentRevision / prompt+model+capability+policy digests
  allowed Handoff graph / epochs / manifest digest

HandoffEdgeRevision
  from AgentRevision / to AgentRevision / reason taxonomy
  preconditions / context transfer contract / required user interaction
  model+capability+permission delta / max uses / fallback policy

HandoffIntent
  runRef / intentId / from+to revisions / edge revision
  reason / current safe-boundary ref / context+delta digest / expected run epoch

HandoffCommit
  intentRef / previous+active AgentRevision / checkpoint/state revision
  effectiveAt / handoff ordinal / durable event ref / receipt
```

Platform业务对象携带siteId；GA只消费EffectiveAgentManifest的opaque handle/digest和namespace，不以siteId作为第二隔离轴。

## 4. Agent catalog and revision publishing

- AgentDefinition是稳定产品identity；任何instructions/model role/tool/skill/memory/Handoff变化创建新AgentRevision。
- prompt/instructions是版本化资产，保存digest、owner、source/license/provenance和evaluation；不在Admin自由文本热改production。
- capability requirement使用published capability IDs/schema ranges，不引用private implementation、secret或任意MCP URL。
- model requirement使用role manifest，如`assistant.primary/research.primary`，不引用Provider/Deployment。
- AgentRevision声明interaction types、content/data policy、target needs、maximum autonomous step/hand-off depth和safe stop。
- publish流程：draft→schema/contract→offline eval→security/Trust→sandbox→canary candidate→signed publish；失败/撤销不改历史revision。
- Site只能assign已发布且适用其Profile/jurisdiction/data region的revision；cross-Site自定义不自动复用。

## 5. Agent selection and default model behavior

- Site/Surface可隐藏选择器并发布一个default AgentOption；这仍是明确Assignment，不是runtime global fallback。
- Chat默认主模型来自EffectiveModelBundle的`assistant.primary`，与公开“AI Chat ModelOption”概念分离。
- Image/Music/Video等Surface可拥有自己的Agent/model roles组合；缺required role时SiteRelease fail，不临场补模型。
- 用户选择只在published AgentOptions中发生，冻结到Run admission；客户端传AgentRevision ID不构成授权。
- active Run不因Admin发布/撤销新revision静默漂移；security emergency restriction可阻止新effect并按policy停止/收口。
- selection material change显示Agent、capability、data/target、cost/interaction diff并重新Quote/confirm。

## 6. Collaboration semantics taxonomy

| Term | Authority semantics | Run identity | Active leader |
|---|---|---|---|
| Persona Switch | 同一Agent runtime只改变published persona/presentation | same | unchanged |
| Delegation | parent Agent调用bounded helper并接收result | same parent Run or child effect | parent remains leader |
| Subagent/ChildRun | parent创建受限子执行，拥有独立child lifecycle | child identity/lineage | parent remains leader |
| Handoff | 同一Run主导Agent从from revision原子转给to revision | same Run | receiver becomes leader |
| AgentTeamRun | 外部TaskGraph协调多个独立members | separate member Runs | coordinator/graph, no single GA handoff |

产品UI、events、metrics、docs和Admin必须使用此taxonomy；不允许为了营销把Persona/Delegation称为Handoff。

## 7. Handoff eligibility and UX

- Handoff只沿EffectiveAgentManifest中directed published edge；不能根据prompt写任意receiver name。
- preconditions可包括intent class、completed steps、no pending effect、required context/permission/model/capability和handoff budget。
- edge声明`automatic_allowed|user_confirmation_required|user_only`；高影响domain/permission/cost变化默认确认。
- 用户看到from/to Agent、reason、将转移的目标/上下文、能力/模型/费用/权限变化、pending work和返回/停止选项。
- current active Agent在stream、TaskView、messages和accessible status中清晰可见；不暴露hidden system prompt/provider。
- Handoff loop/max ordinal、A↔B cycle和repeated failed edge受Manifest限制；达到上限停止/ask，不无限循环收费。
- receiver不合格/不可用时保持from Agent或typed waiting/failure；不能静默Persona Switch或选择未发布fallback Agent。

## 8. Safe boundary and state transfer

真实Handoff必须发生在GA定义并认证的safe boundary：

- 当前model turn和tool call已durable收口；无未claim/unknown external effect被当作可重做。
- HITL/approval要么仍由明确owner持有，要么transfer contract显式迁移；不能丢失/重复Decision。
- Run epoch、checkpoint revision和activeAgentRevision expectedVersion确定。
- source Agent outbox/event到handoff intent之前的顺序durable。
- receiver所需model/capability handles由Platform/Gateway/Capability预授权且未过期。

Context transfer只包含edge允许的typed refs：task intent、approved conversation parts/summary、Artifacts、tool receipts、pending interaction、
budget/permission opaque handles和safe memory refs。不得转移raw secrets、other-Site data、unapproved hidden reasoning、stale tool token、
Provider credential或完整workspace bytes。

## 9. Handoff transaction and crash recovery

目标Phase B状态机：

```text
eligible
→ HandoffIntent durable
→ resolve current authorization/model/capability/context delta
→ optional user Decision durable
→ checkpoint CAS commits activeAgentRevision + handoff ordinal
→ durable agent.handoff committed event
→ receiver resumes next safe step
```

- intent identity+digest幂等；同identity不同from/to/context拒绝。
- crash在Intent前：from Agent保持active；crash在Intent后/Commit前：reconciler查询same intent，不双commit。
- checkpoint commit和durable handoff event必须有可证明原子/ordered protocol；不能出现UI显示receiver而checkpoint仍from。
- receiver首次model/tool effect绑定post-handoff epoch/ordinal；stale from Agent不能继续写effect/event/terminal。
- Handoff不创建新root Hold；model/capability delta从同ExecutionBudget parent切片，unknown旧effect保留额度。
- cancel与handoff竞态使用Run owner CAS；只有一个canonical transition，loser读取current state。

## 10. Model、capability and permission delta

### Phase A（当前允许设计/未来adapter cutover）

- 所有main/subagent/persona仍使用同一`assistant.primary`。
- 只替换BaseChatModel外围Gateway adapter，保持graph、assembly、prompt、tools、checkpoint、events、HITL和terminal。
- Handoff UI/产品不enable；现有swarm prompt switch正名Persona Switch。

### Phase B（需要专项用户批准）

- AgentRevision role manifest可给receiver解析不同model roles。
- Handoff可切换receiver instructions、model adapter、skills/tools和policy，但只使用compiled deltas。
- capability set采用least privilege：receiver不自动继承from Agent全部tools/Connections/Target permissions。
- new capability/target/secret/action需current Platform/用户authorization；Handoff reason不构成approval。
- model unavailable遵循role-specific fallback equivalence；首token/tool/reasoning后不跨model续接。

## 11. Revoke、rollback and compatibility

- AgentRevision/edge撤销阻止新Run/Handoff；active Run按restriction policy继续当前revision、等待、safe stop或cancel request。
- 已committed Handoff不因edge下架“倒退activeAgent”；返回需要published reverse edge或新Run。
- SiteRelease rollback只影响新Admission；activeRun manifest frozen，security deny可覆盖effect。
- checkpoint/schema必须携manifest/revision compatibility；旧Run恢复时receiver runtime不兼容则typed migration_blocked，不silent coerce。
- Agent publish rollback创建新Assignment/SiteRelease；不删除bad revision/evaluation/Run history。

## 12. Cost、TaskView and user states

- Handoff本身可zero-rated；from/to model/tool Usage分别绑定同ExecutionRoot allocations和AgentRevision refs。
- 用户看到Agent-level cost breakdown只作为projection，不让GA/Agent计算price。
- TaskView/Session projection显示`active_agent`、handoff requested/waiting/committed/failed、reason category和freshness。
- states：`agent_selected | handoff_suggested | handoff_confirmation | handoff_committing | active_agent_changed |
  handoff_blocked | handoff_failed | run_waiting | run_terminal`。
- projection丢失从GA/Session durable facts重建；TaskView不写activeAgent或直接发checkpoint mutation。
- accessible live region只在canonical commit播报一次；persona文案变化不冒充leader变化。

## 13. Admin and operations

- Agent Console显示Definition/Revision/prompt+model+capability digests、assignments、edges、evaluations、canary、revoke和Run handoff timeline。
- typed commands：PublishAgentRevision、PublishHandoffEdge、BindAgentAssignment、PauseAssignment、EmergencyRestrictAgentRevision、
  RevokeHandoffEdge、RebuildAgentProjection、ReconcileHandoffIntent。
- publish/revoke/critical edge/hidden tool变化使用maker-checker、expectedVersion、dry-run、Site impact和rollback receipt。
- 禁止Admin改activeAgent/checkpoint、mark handoff committed、重放tool/model、查看hidden prompt/reasoning/secret或绕过GA owner。
- metrics：selection、handoff eligibility/suggest/confirm/commit/fail/loop、time-to-resume、model/capability delta、cost、user stop、
  stale writer reject和cross-Site negative；按Site/Surface/Agent/edge revisions。

## 14. Acceptance criteria

### AC-AGT-01 — Taxonomy is truthful

```gherkin
Given a runtime only changes persona prompt or delegates to a helper while the parent remains leader
When UI, events and analytics describe the action
Then it is Persona Switch or Delegation/Subagent, not Handoff
And activeAgentRevision and leader ownership do not change
```

### AC-AGT-02 — Only published edges can hand off

```gherkin
Given an Agent requests a receiver not present in the EffectiveAgentManifest edge graph
When Handoff admission evaluates the intent
Then it rejects before checkpoint, model, tool or permission change
And prompt text or client IDs cannot create a dynamic edge
```

### AC-AGT-03 — Crash commits at most one leader transfer

```gherkin
Given the process crashes before, during or after HandoffIntent and checkpoint CAS
When recovery replays the same intent
Then exactly one activeAgentRevision and committed handoff ordinal result
And from/receiver cannot both progress model, tool or terminal effects
```

### AC-AGT-04 — Receiver gets least privilege

```gherkin
Given the receiver requires a different model, capability or Target action
When Handoff commits
Then only compiled current handles and explicitly transferred context become available
And from-Agent tools, secrets, permissions or other-Site data are not inherited
```

### AC-AGT-05 — Handoff preserves unknown effects

```gherkin
Given the source Agent has a submitted or unknown external effect
When a Handoff is proposed
Then the effect identity, allocation and reconciliation owner remain intact or the edge is blocked by safe-boundary policy
And the receiver cannot retry or redo it to continue
```

### AC-AGT-06 — Model role change never hides continuation

```gherkin
Given receiver model role resolves to a different Deployment or fallback
When Handoff begins receiver execution
Then the change follows the compiled role/fallback contract before the new model call
And no output stream is spliced across models after first token, reasoning or tool call
```

### AC-AGT-07 — Revocation does not rewrite active history

```gherkin
Given an AgentRevision or edge is revoked after a Run committed Handoff
When restriction propagates
Then new admissions/effects obey current deny policy while historical manifest and Handoff receipts remain immutable
And activeAgent is not silently rolled back to another revision
```

### AC-AGT-08 — Phase A remains behavior-identical

```gherkin
Given Model Gateway adapter replaces direct model transport in Phase A
When the differential corpus runs
Then graph/state keys, prompts, model/tool/reasoning IDs and order, HITL, subagent/persona, checkpoint, cancel and terminal remain equivalent
And all calls still use one assistant.primary without Handoff semantics
```

## 15. GA semantic change approval matrix

以下每项默认`not authorized`，必须在实现计划前由用户逐项批准：

- graph topology、node、state reducer或assembly/middleware/prompt composition变化。
- checkpoint新增/修改`activeAgentRevision`、handoff ordinal或model-call identity。
- durable `agent.handoff` event kind/order和Session/Web contract。
- per-Agent/main/subagent/Handoff model role binding。
- Handoff切换instructions/tools/skills/MCP/policy/context/memory。
- tool schema、tool-call ID/order、effect journal、HITL frame/resume变化。
- stale Agent fencing、Run epoch、cancel/terminal ownership变化。
- namespace含义或GA接收Site/User/Workspace/Billing/Plan字段。
- 在首token/tool/reasoning后跨model/Agent续接。

无需专项改变且可先做的仅包括：Catalog/PRD/schema/evaluation的Platform设计、Persona命名纠偏，以及保持BaseChatModel公开行为的
Gateway adapter differential spike。

## 16. Verification and release gates

- catalog：immutable revision、digest、assignment/option、cross-Site、publish/canary/revoke/rollback和dependency inventory。
- taxonomy：Persona/Delegation/Subagent/Handoff/AgentTeam product/event/metric contract tests。
- handoff chaos（仅批准后）：每个intent/checkpoint/event/effect边界crash、duplicate/replay、cancel/revoke/model outage和stale writer。
- security：context/permission/tool/model delta、prompt injection、dynamic edge、Site/manifest/epoch拼接、secret/hidden prompt leakage。
- UX/a11y：selection/hidden default/suggest/confirm/commit/fail/current agent在Web/CLI/Desktop/Mobile完整流程。
- Phase A differential：text/reasoning/tool IDs/order、HITL、subagent/persona、checkpoint resume、cancel和terminal exactly once。

No-Go：Persona冒充Handoff；dynamic receiver；运行时global default；未发布Agent；Handoff重复effect；双active leader；receiver继承全权限；
首token后切model；Admin改checkpoint；AgentTeam塞入GA；任何approval matrix项目未获用户批准即实现。

## 17. Related documents and authorization boundary

- [Model Control/Gateway](2026-07-25-model-control-gateway-litellm-architecture-design.md)
- [PRD-05 Chat](2026-07-25-prd-05-chat-conversation-run-and-interaction.md)
- [PRD-A5 Agent Team](2026-07-25-prd-a5-agent-team-research-and-application-runtime.md)
- [Execution Budget Protocol](2026-07-25-execution-budget-allocation-protocol-design.md)

本文只请求对产品目标和GA专项审批矩阵进行评审。`implementationAuthorized: false`且
`gaRuntimeSemanticChangeAuthorized: false`；在用户明确批准Phase B前，真实Handoff保持disabled/not_enableable。
