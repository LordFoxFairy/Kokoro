---
artifact: module-capability-coverage-audit
version: "1.2"
created: 2026-07-25
status: internal-review-active
authority: docs/superpowers/specs/2026-07-25-platform-web-session-target-architecture-design.md@1.5
scope: product-journey-module-interface-spec-verification-traceability
---

# Kokoro 全项目模块、能力与闭环覆盖审计

## 0. 结论与用途

本文不是第二份总架构，也不是空 child Spec 集合。它回答一个更严格的问题：Kokoro 的每个用户承诺、
产品 Surface、bounded context、运行服务和横切能力，是否都有唯一 owner、进入/完成/失败恢复协议、对应
child PRD/Spec、实施 Wave 与生产证据。

当前裁决：

- Umbrella v1.5 已覆盖整体边界和关键分布式不变量，没有理由新增万能后端、第二套 Agent runtime、第二套
  Commerce 后半链或每个 Site 一套后端。
- `docs/requirements/` 和 `docs/kokoro-handbook/product/` 主要描述当前/历史 Chat 产品，不能证明目标产品全量
  覆盖。Wave 0/8 前它们只作为现状和设计历史，不能覆盖 v1.5。
- 完整设计采用“Umbrella 不变量 + 27 份已登记产品 PRD + 按风险拆分的架构 child Spec + profile-scoped certification”，
  不把所有字段、状态机和迁移塞进一个不可实施的超大文件。
- 本矩阵不存在 `done by association`：模块出现在目录图里不等于设计完成；设计从 `design-covered` 经过评审，
  实现后再分别取得 Qualification 与具体 ReleaseCertification，任何阶段都不能越级。

## 1. Coverage Contract

每个受管能力必须具有以下字段，否则 child Spec review 直接失败：

```text
capabilityId / userOrOperator / entrySurface / commandOwner
aggregateOwner / authoritativeStateMachine / sourceOfTruth
securityContext / entitlementAndBudget / idempotencyIdentity
syncRpcOrEvent / terminalAuthority / failureOwner / recoveryProtocol
userVisibleStates / adminSupportWorkflow / observabilityAndSlo
dataGovernanceParticipant / childPrd / childArchitectureSpec
implementationCut / verificationEvidence / releaseScope
```

设计与交付状态不能混用。当前审计固定使用：

- `design-covered`：已有明确 owner、边界、PRD/Spec 与验收合同，但仍处内部评审。
- `review-required`：设计已形成，尚缺指定角色或用户书面批准。
- `GA-user-approval-required`：可能改变 GA runtime 语义，必须单独获得用户批准。
- `implementation-not-authorized`：不得开始实现；这也是当前全局默认状态。
- `evidence-not-started`：实现、迁移、RC、负向验证或生产证据尚未生成。
- `qualified`：具体 capability/surface revision 已有有效 `CapabilityQualificationAttestation`；不单独授权上线。
- `release-certified`：具体 SiteRelease candidate 在 compile/build/preview 后取得匹配 digest 的
  `ReleaseCertificationInstance`。
- `disabled`：route、bootstrap、API authorization、Admin 四层均关闭且有负向证据。

不得使用“规划中”“基本完成”“后续支持”等无法验收的状态。

### 1.1 Capability Contract Ledger

下表把 Coverage Contract 落成逐项 ledger。`Owner/Truth` 同时给出 command owner、aggregate/source of truth 与
authoritative state；`Control` 同时给出 security context、entitlement/budget 与 idempotency；`Completion` 同时给出
interface、terminal/failure owner 与 recovery；`Operations` 同时给出 user-visible state、Admin/Support、observability 与
Data Governance participant。具体字段/schema 以链接 PRD/Spec 为准。

| Capability | Entry / actor | Owner / truth | Control | Completion / recovery | Operations | PRD / architecture / cut | Status |
|---|---|---|---|---|---|---|---|
| Site/Fleet | domain、Site app、Admin；user/operator | site module；Site/Binding/Config/Release/ActivationAttempt | trusted Host/Binding + Site/Global operator scope；release command key+digest/CAS | typed Platform command + deployment receipt；ActivationAttempt owns terminal，Fleet reconciler handles unknown | release states；Fleet Admin/Support；availability/deploy/rollback SLO；retention/decommission participant | PRD-00/12；Umbrella + P0 Closure；1/7/8/9 | design-covered / review-required |
| Identity/Device session | auth/account/client；user/support | identity module；User/Credential/FederatedIdentity/AuthSession/MFA/Recovery | Site-bound issuer/cookie/token、Risk epoch；no execution budget；request key+subject generation | Identity API/events；aggregate terminal；Identity/Notification/Support recover verify/revoke | auth states；security Admin/Support；login/recovery metrics；Export/Delete/LegalHold | PRD-01/15/A6；Client Access Spec；1/6 | design-covered / review-required |
| Workspace/Project | onboarding/settings/invite；member/operator | workspace module；Workspace/Membership/Project/ExecutionSpace mapping | Site/membership/role/last-owner；no Credit authority；expectedVersion+invite identity | typed local application interface/events；workspace aggregate terminal；owner transfer/invite recovery | membership/project states；Admin/Support；orphan/transfer metrics；Data Rights participant | PRD-02；Umbrella/RPC；1 | design-covered / review-required |
| Catalog/Offering/Commerce | pricing/account/Admin；user/operator | catalog/offering/commerce；immutable Product/Plan/Price/Offering/Quote/Order revisions | Site/Profile/SalesPolicy；quote eligibility；command key+body digest | Platform local UoW/events；Order owns terminal；expiry/requote/reconcile | offer/order states；Commerce Admin/Support；conversion/error metrics；financial retention | PRD-03/04；Umbrella/RPC；2A/2B | design-covered / review-required |
| Subscription/Fulfillment/Entitlement | redeem/checkout/account；user/operator | subscription/fulfillment/entitlement；Term/Transaction/Grant | source lineage、BillingAccount、Site；program/plan rules；source command idempotency | same Platform UoW then facts；each owner aggregate terminal；reversal/replacement/reconcile | term/grant states；Commerce/Support；duplicate/orphan metrics；financial/Data Rights policy | PRD-03/04；Umbrella；2A/2B | design-covered / review-required |
| Redeem/Card Code | redeem UI/Admin batch；user/operator | redeem；Program/Batch/Code/Attempt/Redemption/Campaign | Site/program/risk、CSPRNG+HMAC；attempt key+code digest | local UoW → Fulfillment receipt；Redemption owns terminal；lost response/review/reversal/replacement | redeem states；maker-checker/Support；success/race/fraud metrics；secret/financial retention | PRD-03/10/11；Umbrella；2A/7 | design-covered / review-required |
| Payment/Refund/Dispute | checkout/account/Admin；user/operator/provider | payment；Checkout/Attempt/Fact/Payment/Refund/Dispute/Reconciliation | Site/provider account/risk/PCI boundary；provider+local idempotency | Provider adapter + webhook inbox；canonical Fact owns truth；unknown/late/reconcile/original-route refund | payment states；Finance/Support；success/unknown/dispute metrics；financial retention | PRD-04/10/11；Umbrella；2B/7 | design-covered / review-required；disabled first profile |
| Credit/Budget/Usage/Rating | account + all execution admissions；user/workload/operator | credit + usage-rating；Grant/Journal/Hold/Allocation/CanonicalUsage/Rating/Settlement | BillingAccount/Site/source；one root Hold/bounded children；stable execution/allocation/usage IDs | local commands/events/outbox；Journal/Settlement terminal；unknown liability retained、late correction/reconcile | available/reserved/cost_pending；Finance Admin/Support；conservation/aging metrics；financial retention | PRD-03；Budget Spec；2A+all execution cuts | design-covered / review-required |
| Model Control/Gateway/LiteLLM | model option/Admin + GA/Job calls；user/operator/workload | model-control owns catalog/assignment；Gateway owns Invocation/Attempt/Resolution/UsageFact | Site/Plan/Surface/Input/Policy in server-side authorization；opaque handle；logicalModelCallId | RPC/stream/callback；Attempt owner terminal；pre-effect retry only、unknown reconcile、cost_pending | option/attempt/config states；Model Admin/Support；quality/latency/drift/unknown；evaluation retention | PRD-17；Model Architecture + P0 Closure；5A | design-covered / review-required；GA adapter delta gated |
| Capability Hub/Runtime | Chat/Routine/Admin catalog/connection/call；user/operator/workload | Hub owns revision/package/connection policy；Runtime owns CapabilityCall/effect/UsageFact | Qualification/assignment/consent/grant/secret audience；bounded allocation；operation/effect identity | RPC/stream/elicitation/receipt；Call owns terminal；revoke/unknown/query/reconcile | catalog/connection/call states；Capability Admin/Support；call/revoke/supply-chain metrics；secret/data participant | PRD-18；Capability Control/Runtime Spec；5A/6C | design-covered / review-required；GA Skill/MCP delta gated |
| Session/Task projection | Web/client conversation/task；user/support | Session owns Session/Message/Part/Branch/launch+control projections；TaskView read-only | SessionAccessGrant/Site/subject generation；no pricing; submit/control key+digest | HTTP snapshot + SSE + owner-routed commands；GA owns Run terminal；reattach/typed cursor/rebuild | run/interaction/task states；Session/Support；SSE/freshness metrics；Export/Delete participant | PRD-05/A4/A6；Session Transport + Projection Specs；3/6C | design-covered / review-required |
| GA RunExecution | admitted Chat/Agent；workload/user projection | GA；RunExecution/checkpoint/lease/epoch/effect/outbox | opaque namespace/handles/grants/limits；delegated allocation；run/effect/logical-call IDs | queue/control + narrow adapters；GA terminal authority；lease/effect unknown/HITL recovery | projected Run states；GA ops via typed façade；terminal/effect/lease metrics；runtime retention | PRD-05/A1/A5；Umbrella/P0 Closure；3/5A/5B/6D | design-covered；semantic changes GA-user-approval-required |
| Operation/Job | Studio/direct or GA delegated；user/workload/operator | Job；Operation/Job/Attempt/lease/progress/finalization | Admission/OperationAuthorization/Site/Project；bounded allocation；operation/attempt/provider IDs | RPC/queue/callback/outbox；Job owns provider-independent terminal；unknown/finalizer-only recovery | queued/running/partial/cost_pending；Job Admin/Support；queue/provider/finalizer metrics；retention participant | PRD-07/08*；Umbrella/P0 Closure；4 | design-covered / review-required |
| Media Resource | upload/Studio/Library/Share；user/operator/workload | Asset、Artifact、Blob-Lifecycle three owners | Site/Project/rights/scan/Trust/AssetGrant；quota/allocation；upload/finalize/share/GC identities | typed interfaces + receipts；owner aggregates terminal；quarantine/DerivedInput/export/GC unknown recovery | asset/artifact/share/GC states；Media/Trust/Support；storage/lineage/GC metrics；retention/LegalHold/DR | PRD-06/09/16；Asset/Artifact/GC Spec；4/7 | design-covered / review-required |
| Trust/Risk/Media Rights | intake/generation/share/report/appeal；user/operator | risk-policy + Trust decision owners；Policy/Evidence/Decision/Restriction/Appeal | Site/profile/legal baseline/consent epoch；no bypass；stable evaluation/decision/appeal IDs | owner commands/events；Decision/Appeal terminal；partial/unknown reporting and purge | restricted/appeal states；Trust Admin/Support；decision/purge/SLA metrics；evidence retention/LegalHold | PRD-16；Media/Projection specs；1/4/7 | design-covered / review-required |
| Notification/Data Rights | settings/notification/export/delete；user/operator | notification + data-governance；Preference/Request/Delivery and Export/Delete/Hold Plan/Receipt | Site/subject/jurisdiction/mandatory class；no business budget; intent/participant/delivery identities | outbox/provider/participant APIs；Delivery/Plan owner terminal；unknown/DLQ/resume/rebuild-safe recovery | delivery/export/delete states；Privacy Admin/Support；SLA/backlog metrics；policy itself | PRD-15；Projection Spec；1/6C/7 | design-covered / review-required |
| Admin/Support/Audit | admin app/support center；operator/support/user | domain owners remain authority；admin façade/SupportCase/audit envelope | phishing-resistant auth、Site/Global/BreakGlass、step-up/maker-checker/JIT；command key+parameter digest | typed commands/read models/case refs；domain owner terminal；case/escalation/reconciliation | queue/case/audit states；no DB role；SLA/command/audit metrics；evidence governance | PRD-10/11；RPC + Projection specs；all cuts/7 | design-covered / review-required |
| Growth/Experiment | landing/share/campaign/Admin；anonymous/user/operator | growth；Attribution/Experiment/Assignment/Exposure/Outcome | consent/Site/profile/subject generation；no authorization override；assignment/exposure IDs | event/API/projection；source journey owns business terminal；analytics failure non-blocking | consent/experiment states；Growth Admin/Support；funnel/guardrail metrics；privacy retention | PRD-13；Umbrella/Projection；1/7 | design-covered / review-required |
| ExecutionTarget/Device Gateway | adaptive workspace/client/local/cloud/browser；user/workload | Execution Runtime owns target/lease/action；Gateway owns channel/presence | assignment + TargetAuthorization + permission epoch；allocation；action identity/receipt | control RPC/outbound connector；Action owner terminal；offline/takeover/revoke/unknown reconcile | target/permission/action states；Runtime Admin/Support；lease/action metrics；local-data policy | PRD-A2/A6；Client Access Spec；6A | design-covered / review-required |
| Developer Workspace | developer client/workspace；developer/workload | Developer Workspace；RepoBinding/Worktree/ChangeSet/CodeCheckpoint refs | Site/Project/target/repo permission；operation budget；binding/checkpoint/git IDs | typed commands/provider refs；workspace operation terminal；dirty/conflict/rewind/fork recovery | repo/diff/checkpoint states；Dev Admin/Support；change/CI metrics；code retention | PRD-A3/A6；Client Access Spec；6B | design-covered / review-required |
| Automation/TaskView | routine/connector/task UI；user/operator/scheduler | Automation owns Routine/Trigger/Run；TaskView read-only | Site/owner/trigger/normal Admission each occurrence；bounded budget；schedule/trigger IDs | scheduler→Admission, never GA direct；RoutineRun owner terminal；DST/misfire/wait/revoke/rebuild | routine/task states；Automation Admin/Support；misfire/lag metrics；retention participant | PRD-A4/18；Projection Spec；6C | design-covered / review-required |
| Agent Registry/Team/App | agent picker/team/application UI；user/operator/workload | agent-registry, AgentTeam coordinator, Application Runtime each own facts | published revisions/edges/grants/root slices；stable team/node/rollout IDs | manifests/RPC/events；member Run/Job + coordinator/app terminal；partial/cancel/aggregate/rollback | selection/team/deploy states；Agent/App Admin/Support；fanout/rollout metrics；retention | PRD-A1/A5；Umbrella/Budget；5B/6D | design-covered；Handoff delta GA-user-approval-required |
| Site Web/Client UI | independent Site project/Web/CLI/Desktop/IDE；user | project owns routes/brand/drafts；backend owners all business truth | trusted Site binding/OAuth/BFF; no direct budget authority；submit/task intent keys | public Platform/Session/Task façades；owner receipts determine terminal；offline/update/a11y recovery | all product states；no business DB/Admin bypass；UX/perf/a11y metrics；cache/data-rights policy | PRD-00/05/12/14/A6；Web Fleet + Client Specs；1/3/6/8/9 | design-covered / review-required |

Ledger 中 `verificationEvidence` 当前统一为 `evidence-not-started`；它只在获批实现后的具体 cut/profile/release 绑定
真实报告 digest。`releaseScope` 由 LaunchProductProfile/EnabledSurfaceInventory 冻结，不能从“模块存在”推断。

## 2. 权威文档与外部参考边界

| 来源 | 用途 | 不允许成为 |
|---|---|---|
| Umbrella v1.5 | 目标边界、不变量、主链、Wave 和验收 scope | 当前代码已实现证明 |
| Production Delivery Program | child cut 顺序、review/implementation/evidence protocol | 领域字段和状态机真源 |
| Wave child PRD/Spec | 当前 cut 的产品和技术权威 | 其他 cut 的隐式授权 |
| INDEX/CODEBASE_MAP | 当前已实现代码边界和真实验证入口 | 未来目标设计 |
| ReleaseEvidenceBundle | 某 profile/revision 的生产证据 | 永久有效或其他 profile 的证据 |
| 历史 requirements/handbook/spec | 现状、用户意图和决策考古 | 覆盖 v1.5 的新目标 |

参考项目只借鉴模式，不复制实现：

| 参考 | 借鉴内容 | Kokoro 裁决 |
|---|---|---|
| [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code/cli-usage) | continue/resume、权限模式、MCP、CLI/IDE 产品语义 | 新客户端复用同一 Session/GA/Job，不复制账户/Task/runtime |
| LangGraph/DeepAgents | checkpoint、图执行、HITL、多 Agent 模式 | 保留 GA 底座；Handoff 与 Subagent 分离，改行为先专项批准 |
| [Vercel AI SDK persistence](https://ai-sdk.dev/docs/ai-sdk-ui/chatbot-message-persistence) / [resume](https://ai-sdk.dev/docs/ai-sdk-ui/chatbot-resume-streams) | typed UI parts、持久消息、stream resume、tool UI | 仅作 Web primitive；Session durable contract 仍是系统真源 |
| [Stripe Payment lifecycle](https://docs.stripe.com/payments/paymentintents/lifecycle) / [Billing Credits](https://docs.stripe.com/billing/subscriptions/usage-based/billing-credits) | Payment Intent/Fact、webhook、Credit Grant/append-only ledger | acquisition 与 fulfillment 分离，Credit closed-loop，不照搬法币账本 |
| [Lago prepaid credits](https://getlago.com/docs/guide/wallet-and-prepaid-credits/overview) | metering、wallet/grant trace、subscription/usage 分层 | 借鉴领域边界；AGPL 实现不得复制 |
| [LiteLLM routing](https://docs.litellm.ai/docs/routing) | Provider 协议归一、模型组与运行路由 | 仅 Gateway adapter；其 DB/key/budget/fallback 不是 Kokoro 真源 |
| Manus 类产品 | 长任务、浏览器/电脑、Task timeline、产物交付 | 复用 ExecutionTarget/Job/TaskView/Artifact，不新增第二套 Agent 后端 |

## 3. Core Production Journey Catalog

所有 `core-always` 旅程都必须出现在首发 LaunchProductProfile；`if-enabled` 只在 inventory 开放时要求
生产证据，但关闭状态也必须有负向验证。

本节 `CORE-*` 是架构闭环 ID，用于追踪 owner 与 cut；产品层 canonical `LP/ID/WS/AC/RD/CH/ST/...`
Journey IDs、状态和 PRD 文件注册以
`docs/superpowers/specs/2026-07-25-product-requirements-governance-and-prd-registry-design.md` 为准。

| Architecture journey | Canonical journey | 用户完成目标 | 权威链 | 主要恢复/失败闭环 | Scope / PRD / cut |
|---|---|---|---|---|---|
| CORE-IDENT-01 | ID-01 | 注册并验证邮箱 | Site BFF → Identity User/Credential/Verification | 过期/重放/串站链接拒绝；邮件按 Site 绑定 | core-always / PRD-01 / 1 |
| CORE-IDENT-02 | ID-02/03/05/06 | 登录、登出和恢复账号 | Identity Session/MFA/Recovery | 设备撤销、全会话撤销、异常登录、re-auth | core-always / PRD-01 / 1 |
| CORE-IDENT-03 | ID-04 | OAuth link/unlink | FederatedIdentity → Site-local User | state/redirect 冲突、同邮箱不自动跨站合并 | if-enabled / PRD-01 / 1 |
| CORE-WORK-01 | WS-01/04 | 建立 Workspace/Project | Workspace/Membership/Project | invite expiry、角色变更、ownership transfer | core-always / PRD-02 / 1 |
| CORE-ACCOUNT-01 | AC-01/CR-01 | 查看套餐、权益和积分 | Subscription/Entitlement/Credit projections | reserved/cost_pending、来源/到期、不会自动续费 | core-always / PRD-03 / 2A |
| CORE-REDEEM-01 | RD-01/02/03/04 | 预览并兑换卡密 | Redemption → Fulfillment → Term/Grant | 同 key 恢复、并发双兑、错站安全错误、Risk review | core-always / PRD-03 / 2A |
| CORE-REDEEM-02 | RD-01/03 | 叠加第二张卡 | Stacking preview → fresh redeem recheck | preview 不占 Code；Plan mismatch/expiry 可解释 | core-always / PRD-03 / 2A |
| CORE-REDEEM-03 | RD-05/SUP-03 | 处理撤销/补发/争议 | SupportCase → source reversal/replacement | 不转移已兑 Code、不碰其他来源 Grant | core-always / PRD-03/11 / 2A+7 |
| CORE-CHAT-01 | CH-01/02 | 新建、搜索和管理对话 | Session/Message/Branch | rename/archive/delete/restore、空状态/onboarding | core-always / PRD-05 / 3 |
| CORE-CHAT-02 | CH-03/04/07/08/09 | 发送并持续查看回答 | RunLaunchProjection → GA RunExecution → Session projection | reconnect/reattach、投影坏帧不伪造 terminal | core-always / PRD-05/17/18 / 3+5A |
| CORE-CHAT-03 | CH-05/06 | 停止、继续、编辑和重生成 | GA control + ConversationBranch | cancel/terminal race、原分支/Artifact provenance 保留 | core-always / PRD-05 / 3 |
| CORE-ASSET-01 | AS-01/02 | 上传安全附件 | Asset upload/quarantine/scan | 分片 retry/cancel、恶意/超限不创建 Run/Job | core-always minimal + if-enabled extended / PRD-06 / 4 |
| CORE-STUDIO-01 | ST-01/02/03/04 | 保存草稿并提交生成 | Draft → Operation → Job → Provider → finalization | 自动保存、重复提交、queue/cancel/unknown | if-enabled / PRD-07/08* / 4+5A |
| CORE-STUDIO-02 | ST-05/06 | 比较、重试和导出 | Artifact/Version/Rendition/Export | Provider 不重跑、export retry、moderation 分离 | if-enabled / PRD-07/09 / 4 |
| CORE-LIBRARY-01 | LIB-01/02 | 管理作品和版本 | Project/Asset/ArtifactVersion/Library projection | trash/restore、quota、retention/object GC | core-always minimal / PRD-09 / 4 |
| CORE-SHARE-01 | SHR-01 | 分享或撤销作品 | Share/Publish + moderation policy | expiry/revoke、生成成功但分享受限可解释 | if-enabled / PRD-09/13/16 / 4+7 |
| CORE-SUPPORT-01 | SUP-01/02/03 | 创建和跟进支持工单 | SupportCase/Message/Evidence/SLA | 身份核验、Site secrecy、escalation、resolution notice | core-always / PRD-11 / 7 |
| CORE-GOV-01 | ID-07 | 导出或删除个人数据 | DataGovernance coordinator + participant receipts | LegalHold、partial resume、object GC、re-registration | core-always / PRD-01/15 / 1+各 cut+7 |
| CORE-ADMIN-01 | SF-01/02/03、ADM-01/02/03 | 发布/回滚 Site | SiteRelease/ActivationAttempt/Observation | provider unknown、pointer CAS、drain/reconcile | core-always / PRD-10/12 / 1+7 |
| CORE-ADMIN-02 | ADM-01/02/03 | 管理 Redeem 和账务 Case | Program/Batch/Campaign/Journal/Case workflows | maker-checker、密文一次导出、补偿禁直写 DB | core-always / PRD-03/10/11 / 2A+7 |
| CORE-PAY-01 | PAY-01/02 | 购买或续订 | Quote/Order/Payment Fact → Fulfillment | unknown/late success/webhook/reconciliation | if-enabled / PRD-04 / 2B |
| CORE-PAY-02 | PAY-03 | 退款和 dispute | RefundReservation/Fact/Dispute/Recovery | 原 Provider route、partial allocation、不跨来源扣 Grant | if-enabled / PRD-04/11 / 2B+7 |

## 4. Advanced Agent Journey Catalog

| Architecture journey | Canonical journey | 用户目标 | 权威链与关键边界 | Scope / PRD / cut |
|---|---|---|---|---|
| ADV-AGENT-01 | AGT-01 | 使用已发布 AgentRevision | Agent Registry → Manifest → GA | PRD-A1 / 5B |
| ADV-AGENT-02 | AGT-02 | Agent A handoff 给 Agent B | Handoff edge + checkpointed activeAgentRevision | PRD-A1 / 5B；GA 专项批准 |
| ADV-TARGET-01 | TGT-01 | 选择临时/持久云环境 | Platform assignment → TargetAuthorization → Runtime lease | PRD-A2 / 6A |
| ADV-TARGET-02 | TGT-01/02 | 使用本地电脑/浏览器 | Device Gateway + local enforcement + epochs | PRD-A2 / 6A |
| ADV-TAKEOVER-01 | TGT-03 | 人工接管再交还 | TakeoverLease/controlEpoch/checkpoint | PRD-A2 / 6A |
| ADV-DEV-01 | DEV-01 | 绑定仓库并隔离修改 | RepositoryBinding → Worktree → ChangeSet | PRD-A3 / 6B |
| ADV-DEV-02 | DEV-02 | checkpoint/rewind/commit/PR | CodeCheckpoint + explicit fork + provider refs | PRD-A3 / 6B |
| ADV-CONTEXT-01 | DEV-03 | 管理指令、文件和 Memory | ProjectContextRevision/Memory provenance | PRD-A3 / 6B |
| ADV-ROUTINE-01 | AUT-01 | 创建计划任务/事件触发 | RoutineRevision/Trigger → normal Admission | PRD-A4 / 6C |
| ADV-CONNECT-01 | CON-01 | 安装 Connector/Plugin/Hook | Capability revision/permission/secret ref | PRD-18/A4 / 6C |
| ADV-TASK-01 | TASK-01 | 跨端查看和继续任务 | TaskView projection → commands routed to owner | PRD-A4 / 6C |
| ADV-TEAM-01 | TEAM-01/RES-01 | 并行 Wide Research/Agent Team | TaskGraph/TaskClaim/ChildBudgetSlice/Aggregation | PRD-A5 / 6D |
| ADV-APP-01 | APP-01 | 部署长期应用/服务 | ApplicationRevision → Rollout/Job → EnvironmentDeployment | PRD-A5 / 6D |
| ADV-CLIENT-01 | CLIENT-01/02 | CLI/Desktop/IDE 接入 | Site OAuth PKCE/device flow → same runtime APIs | PRD-A6 + Client Access Spec / 6A-6C |

## 5. Platform Bounded Context Coverage

下表的 command/event 是必须在 child Spec 细化的 contract family，不是完整 wire schema。

| Module | 唯一 owns | 关键 command / facts | 明确不 owns | Child cut |
|---|---|---|---|---|
| site | Site、Binding、ConfigRevision、Release、ActivationAttempt | exchange/compile/activate/rollback；release facts | Web 品牌源、用户身份、外部部署现实 | 1 |
| identity | User、Credential、FederatedIdentity、AuthSession、MFA/Recovery | register/verify/auth/revoke/link/delete-subject | Workspace、跨站全局用户 | 1 |
| workspace | Workspace、Membership、Project、ExecutionSpace mapping | invite/change-role/transfer/create-project/bind-space | GA namespace 内部、Artifact/Session 状态 | 1 |
| catalog | Product/Plan/Price/Offering immutable revisions | publish/revoke revision | Fulfillment/Grant 生命周期 | 2A |
| offering | SiteOfferingAssignment、AssortmentRevision | assign/compile assortment | Product/Price 定义、SiteRelease active pointer | 2A |
| commerce | Quote、Order | quote/create/cancel order | Provider IO、Grant、Credit | 2A/2B |
| subscription | Subscription、Binding、Cycle、TermAllocation、RenewalIntent | create/change/cancel/renew；term facts | Payment Fact、Entitlement implementation | 2A/2B |
| fulfillment | ProgramVersion、Transaction、ReversalTransaction | FulfillSource/ReverseSource | acquisition Provider IO、余额表 | 2A |
| entitlement | TemplateVersion、Grant、Revocation | grant/revoke/check | Credit quantity、套餐展示 | 2A |
| credit | CreditGrant、Journal、Hold、Allocation、BalanceProjection | grant/reserve/commit/capture/release/revoke | Provider Money、Usage producer facts | 2A |
| usage-rating | CanonicalUsageEvidence、CostAssessment、Rating、Settlement | ingest/rate/settle/reconcile | Provider effect、Session token UI | 2A |
| redeem | Program/Availability/Batch/Code/Attempt/Redemption/Campaign | publish/export/activate/redeem/reverse/replace | 假 Payment/Refund、直接改 Credit | 2A |
| payment | ProviderAccount metadata、Checkout/Attempt/Fact/Payment/Refund/Dispute/Reconciliation | checkout/reduce webhook/refund/reconcile | Subscription/Grant 后半链、LiteLLM budget | 2B |
| model-control | ModelDefinition/Deployment/Profile/Pool/RoutePolicy/Bundle/Option/Assignment/EvaluationSuite/PromotionDecision | publish/evaluate/promote/assign/authorize route | Invocation/Attempt/health runtime | 5A |
| agent-registry | AgentDefinition/Revision/TeamRevision/assignment | publish/assign/retire | GA RunExecution、prompt runtime storage细节 | 5B |
| risk-policy | Policy/Signal/Decision/Restriction/Epoch/token | evaluate/apply/lift | 修改历史业务 Fact | 1+各 effect cut |
| data-governance | Retention/Export/Deletion/LegalHold/Plan/Receipt | request/plan/execute/verify | 跨 context 直接删表 | 1+各 cut+7 |
| growth | Attribution/Experiment/Assignment/Exposure/Outcome definitions | publish/assign/expose | Authorization、Price、跨站 identity | 1+7 |
| notification | Preference/Template/Request/Delivery/Attempt | request/expand/deliver/retry | 改变源业务终态 | 1 contract、6C/7 runtime |
| audit | immutable operator/security/business audit envelope | append/query/export subject | 业务 aggregate 或 editable log | 1+各 cut |
| admin façade | typed commands + composed read models | route command/approval/work queue | 独立业务表、万能 repository | 7 |

## 6. Independent Runtime Context Coverage

| Context | 唯一 owns | Required completion/recovery | 不变量 / child cut |
|---|---|---|---|
| Session | Session/Message/Part/Branch/RunLaunchProjection/RunView/ControlOutbox | durable projection、SSE reattach、branch、owner-routed controls | 不授权/扣费/执行 GA / 3 |
| GA | RunExecution/checkpoint/lease/epoch/effect/outbox | authoritative terminal、lease steal fencing、unknown effect | 只收 namespace/opaque grants；改行为先批准 / 3,5A,5B |
| Model Gateway | Invocation/Attempt/Resolution/HealthObservation/AttemptUsageFact | exact deployment、stream/cancel/callback/unknown/circuit | LiteLLM 仅 adapter / 5A |
| Capability Hub | Revision/package/connection/secret refs/control lifecycle | publish/revoke/assignment observation | 不在每 Run 做热路径 RPC / 5A |
| Capability Runtime | discovery/call/external-call state/AttemptUsageFact | grant validate、elicitation、unknown/revocation | 不解释套餐/余额 / 5A |
| Job | Operation/Job/Attempt/lease/progress/finalization receipts | provider outcome 后只恢复 finalization、不重跑 effect | Direct 与 delegated 统一 / 4 |
| Media Resource / Asset | UploadSession、scan evidence、Asset/AssetVersion、AssetGrant | quarantine/resume/promotion/input grant | 不拥有 Artifact/Job/Trust Decision / 4 |
| Media Resource / Artifact | Artifact/ArtifactVersion、Lineage、Rendition、Share | idempotent finalization、derived input、export/share receipt | 不拥有 Blob lifecycle 或执行 Provider / 4 |
| Media Resource / Blob-Lifecycle | physical BlobReference、replica、retention、GCPlan/DestructionReceipt | reference graph revalidation、partial/unknown deletion recovery | 相同 bytes 不合并 Site/owner/rights identity / 4 |
| Task Projection | TaskView/timeline/search read model | rebuild/high-watermark/double-read/CAS cutover | 只读、mutation 回源 / 3,6C |
| Execution Runtime | Target registration/observation/lease/environment/browser session | connection/lease/control epoch、offline/unknown | Platform owns assignment / 6A |
| Device Gateway | local channel/presence/scoped command transport | reconnect fencing、no credential cloud copy | 不解释 entitlement / 6A |
| Developer Workspace | RepositoryBinding/Worktree/ChangeSet/CodeCheckpoint refs | dirty tree protection、rewind fork、merge conflict | Worktree 不是 Target / 6B |
| Automation | Routine/Revision/Trigger/Schedule/Run | dedupe/misfire/wait/deadline/normal Admission | Routine 不是 Job/daemon / 6C |
| Application Runtime | App/Revision/Deployment/Rollout/Instance observations | desired/observed reconcile、rollback as new rollout | SiteRelease 另域 / 6D |

## 7. Web、Admin 与 Site Fleet Coverage

| Surface/package | 必须提供 | 后端 authority | Child PRD/cut |
|---|---|---|---|
| site app shell | independent route/brand/SEO/legal/domain/deploy/rollback | SiteRelease + project-owned brand source | 1+7 |
| auth surface | register/verify/login/recovery/MFA/device/session | Identity | Identity PRD / 1 |
| account surface | plan/term/entitlement/credit/hold/usage/redeem history | Platform projections | Account/Redeem PRD / 2A |
| redeem surface | input/preview/review/result recovery/receipt/support | Redeem/Fulfillment | Account/Redeem PRD / 2A |
| chat surface | list/search/manage/branch/typed parts/HITL/Job cards | Session + TaskView refs | Chat PRD / 3+5A |
| model option surface | Site/Plan/Surface eligible options、default、unavailable/reconfirmation、route explanation | Model Control + Gateway projections | PRD-17 / 5A |
| capability surface | Skill/MCP discovery、assignment、connection/consent、elicitation、revoke、usage state | Capability Hub/Runtime | PRD-18 / 5A+6C |
| image studio | reference/mask/edit/batch/compare/upscale/export | Operation/Job/Artifact | Image Studio PRD / 4 |
| music studio | lyrics/waveform/extend/remix/stem/version/export | Operation/Job/Artifact | Music Studio PRD / 4 |
| video studio | shot/storyboard/assets/long queue/upscale/export | Operation/Job/Artifact | Video Studio PRD / 4 |
| library | Project filters/version/trash/quota/share/export | Artifact/Project | Library PRD / 4 |
| adaptive agent workspace | plan/files/browser/task/artifact panels | typed projections only | 5B/6A-6D |
| developer surface | repository/diff/checkpoint/PR/CI | Developer Workspace/TaskView | 6B |
| admin | Site Fleet/Commerce/Redeem/Model/Runtime/Risk/Governance/System | domain commands + read models | Admin/Support PRD / 7 |
| support | Case inbox/timeline/evidence/SLA/escalation/resolution | SupportCase + opaque domain refs | Admin/Support PRD / 7 |
| design system | headless primitives/semantic tokens/a11y/i18n | no business authority | all Web cuts |
| site scaffold/fleet | create-site-app/template version/drift/codemod/preview | repository + Site Fleet evidence | 1+7 |

## 8. Commerce、Credit 与 Subscription Closure Audit

必须同时成立：

1. Payment、Redemption、AdminGrant、ProgramWindow 是不同 acquisition source；从 Fulfillment 后共享
   Subscription/Entitlement/Credit，不伪造彼此前半链。
2. 每条事实保留 origin Site、BillingAccount、billing entity/liability 和 source lineage；GlobalScope 只是
   查询授权，不是去 Site 化。
3. 三桶是 daily/period/permanent UX projection；权威是 CreditGrant、append-only Journal、HoldAllocation。
4. 一个 ExecutionRoot 只创建一次 root Hold；Model/Capability/Job 使用 UsageAllocation 或
   DelegatedBudgetAllocation，AgentTeam ChildBudgetSlice 是受约束子类型。
5. 同一 `(BillingAccount, serviceScope)` 首发最多一个 effective base Subscription；同 Plan 卡延长，不同 Plan
   走 ChangePlan；credit pack 不创建 Subscription。
6. Redemption claim/Fulfillment/Grant 同一 PlatformUnitOfWork；Code 永不重新开放，售后用 reversal/replacement。
7. Payment V1 automatic capture；unknown Attempt 阻止可能双收款的新 Attempt；redirect 不确认付款。
8. Refund 只在 Provider succeeded Fact 后逆转原 source；Dispute/Recovery 不扣其他 Grant、不静默造负余额。
9. AttemptUsageFact 与执行 Attempt 本地原子；usage-rating 唯一 canonical evidence/rating/settlement owner。
10. 用户 Account 展示 source、term、expiry、available/reserved/cost_pending 和 receipt，不展示假财务对象。

任何一条在 Wave 2A/2B child Spec 中缺字段、状态、锁序、幂等或 E2E，即为 P0。

## 9. Model、LiteLLM 与多模态 Closure Audit

```text
Global Model Catalog
→ Profile per role
→ Pool + RoutePolicy
→ ModelBundleRevision(role → profile)
→ SurfaceModelAssignment + PlanModelGrant
→ AuthorizedModelRoute
→ Gateway ResolutionRecord/Attempt
→ AttemptUsageFact
```

必须同时成立：

- Chat、Music、Image、Video 不复制 ModelDefinition/Deployment list；各 Surface 组合自己的 visible Option 和
  hidden orchestrator/summarizer role。
- Admission 冻结 eligible set、policy、rating 和 grant；Gateway 只在允许集合内按健康选择 Deployment。
- 同 canonical model deployment failover 与跨 model fallback 分开；首 token/Artifact/effect 后禁止隐藏续接。
- LiteLLM 每个 alias 精确对应一个 Kokoro Deployment；隐藏 fallback、virtual-key budget 和 LiteLLM spend
  log 不得成为业务真源。
- 每次 adapter/config revision 都经过 candidate → contract/provider certification → activation → canary/rollback；
  unknown alias、缺关键 metadata、header/usage 丢失和 health 误判必须 fail closed。
- Image/Music/Video adapter 独立认证；“LiteLLM API 有 endpoint”不等于可进入 production assignment。
- Model/Route/Prompt/Agent candidate 通过受治理 DatasetRef、offline quality/safety/latency/cost eval、provider
  certification、shadow/canary 和 signed PromotionDecision；数据许可/PII metadata 或 evidence 过期即阻断。
- Provider secret 只在 Secret Manager/Gateway/Capability Runtime audience 内，GA/Session/Web 不持有。

## 10. General Agent Closure Audit

GA 现有 LangGraph/DeepAgents、checkpoint、lease、HITL、effect journal 和 terminal claim 是保留底座。目标闭环：

- RunExecution 只有 GA 可创建并宣告 terminal；Session 只发起 launch/control 并投影。
- ExecutionManifest 只含 namespace、revision、opaque grants、limits 和 trace；不含 Site/User/Plan/Price/Secret。
- Model、Capability、Job、Artifact 都通过独立后端窄接口；GA 专注图执行与业务编排。
- Persona Switch、Subagent、ChildRun、Handoff、AgentTeam 五种语义不混名。
- Handoff 切换 AgentRevision、model roles、skills/tools/policy，并持久化 activeAgentRevision 与 durable event。
- 每个 effect 使用 audience-bound ExecutionGrant、expected epoch 和 effect claim；unknown 不盲重试。
- attached/detached Job 只改变等待/取消关系，不改变 Job owner 或预算真源。
- CLI/Desktop/IDE 是同一 runtime 的客户端，通过 Site OAuth/registered device 接入，不复制 Session/Credit/Task。

以下实现动作仍是专项用户批准门：RunLedger/dispatch/terminal/lease、graph/assembly/swarm、checkpoint schema、
Agent/Prompt/Tool/Skill/MCP 装配、Provider/streaming/reasoning 行为、effect/unknown recovery、namespace、durable
event/terminal semantics、GA delegated operation tool。

## 11. Cross-Cutting Coverage

| Concern | 必须证明 | 冻结 cut |
|---|---|---|
| Request security | Anonymous/User/Operator/Workload principal、trusted product context、delegated grant、audience/expiry/revocation | 1 |
| RPC registry | caller/owner/schema/audience/deadline/retry/idempotency/receipt/failure/fallback | 0 contract + 各 cut |
| Event envelope | aggregate version、correlation/causation、classification、partition、Inbox、DLQ、replay safety | 0/1 |
| Transactions | local UoW + Outbox；外部 effect 不进 DB transaction | 各 owner cut |
| Idempotency | key + canonical body digest + result receipt + conflict semantics | 各 mutation cut |
| Observability | SLI numerator/denominator/window/source/owner/error budget；sensitive/cardinality limits | 1 起逐 cut |
| Overload | admission shed、per-Site fairness、queue age、Provider/worker concurrency、no policy bypass | 1/4/5A |
| Secrets | SecretRef、short lease、audience、rotation、redaction、no browser/event/GA secret | 0/1/5A/6 |
| Data governance | participant API、LegalHold epoch、retention、GC receipt、rebuild | 1+每个 context |
| Notification | source fact/request、template/locale/site binding、delivery/unknown/DLQ | 1/6C/7 |
| Content safety | input rights/scan、NSFW/copyright/voice/likeness、generation/share distinction、appeal | 4/7 |
| i18n/a11y | locale/timezone/number/RTL/legal/template/browser/keyboard/screen reader | 每 Web cut |
| Supply chain | pinned lock/image digest/SBOM/provenance/license/registry policy | 0/9 |
| DR | failure-domain RPO/RTO、backup/PITR/object restore/reconciliation/projection rebuild | 0 foundation + 9 |
| Release | immutable SiteRelease、ActivationAttempt、Qualification → compile/build/preview → ReleaseCertification DAG | 1/8/9 |

架构 child Spec 的当前覆盖入口：

- [P0 Contract Closure](../superpowers/specs/2026-07-25-platform-web-session-p0-contract-closure-design.md)：Certification DAG、GA opaque model authorization、Job/cost、Session snapshot。
- [Session Production Transport](../superpowers/specs/2026-07-25-session-http-sse-production-transport-design.md)：snapshot、opaque cursor、bounded replay、backpressure、drain、soak。
- [Client Access Plane](../superpowers/specs/2026-07-25-client-access-plane-developer-client-design.md)：CLI/Desktop/IDE OAuth、attach/fork/new run、local action receipts。
- [Capability Control/Runtime](../superpowers/specs/2026-07-25-capability-control-runtime-connection-effect-architecture-design.md)：package qualification、assignment、connection/secret、effect/usage/revoke 与 GA hot-path gate。
- [Platform Modular Core/Internal RPC](../superpowers/specs/2026-07-25-platform-modular-core-internal-rpc-design.md)：in-process transaction interface 与 remote RPC/saga 分离。
- [Execution Budget Allocation](../superpowers/specs/2026-07-25-execution-budget-allocation-protocol-design.md)：单 root Hold、有界 child allocation、unknown liability。
- [Asset/Artifact/Blob Ownership and GC](../superpowers/specs/2026-07-25-asset-artifact-ownership-promotion-gc-design.md)：Media Resource 内三 owner、DerivedInputVersion、GCPlan。
- [Projection Rebuild/Event Retention/Migration](../superpowers/specs/2026-07-25-projection-rebuild-event-retention-migration-design.md)：owner truth、shadow rebuild、retention、authority switch 与 DR。

## 12. Child PRD/Spec Deliverable Map

不得预创建空文件；进入 cut 时才生成以下完整产物：

| Cut | 必须先有的产品 PRD | 技术 Spec 重点 | 退出证据 |
|---|---|---|---|
| 0 | 无业务 PRD | repository/toolchain/contract/INDEX/CI/provenance | fresh clone、determinism、GA corpus |
| 1 | Identity/Auth + Workspace/Site Release PRD | principals/UoW/Activation/Risk/Governance contracts | 双 Site auth/release/security E2E |
| 2A | Account/Redeem/Billing PRD | Catalog/Fulfillment/Term/Grant/Journal/Budget/Usage | redeem-only certification |
| 2B | Checkout/Subscription Management PRD | Payment/Refund/Dispute/dunning/provider reducer | provider certification |
| 3 | Chat/Conversation PRD | Run launch/control/projection/branch/SSE | reconnect/branch/terminal races |
| 5A | PRD-17 Model + PRD-18 Capability（Chat 交互由 PRD-05） | Control/Gateway/LiteLLM/Runtime/minimum GA adapter | model/capability qualification + release certification |
| 4 | PRD-06/07/08I/08M/08V/09 | Operation/Job/finalization/Media Resource/Share | real Provider Studio E2E |
| 5B | AgentRevision/Handoff PRD | true handoff/checkpoint/effect safety | GA专项批准 + chaos |
| 6A | PRD-A2 + PRD-A6 client lifecycle | target/device/takeover/grants/epochs/client OAuth | local/cloud/browser/client safety |
| 6B | PRD-A3 + PRD-A6 developer clients | repo/worktree/checkpoint/context/memory | dirty tree/rewind/multi-client |
| 6C | PRD-A4 + PRD-18 + PRD-A6 | automation/notification/capability/task projection/client continue | misfire/revocation/rebuild/offline |
| 6D | AgentTeam/Wide Research/Application PRD | task graph/budget/aggregation/long service | fan-out/cancel/rollout chaos |
| 7 | Core Admin/Support/Governance PRD | façade/RBAC/case/SLA/fleet/reconciliation | operator UAT/security/audit |
| 8/9 | Launch Profile + Operations PRD | clean cut/evidence/canary/rollback/on-call | profile certification instance |

## 13. Coverage Gaps 与当前 Go/No-Go

### 已关闭的架构 P0

- Run、Usage、Model、Project、Admin façade 的唯一 owner。
- Job → Artifact → Usage finalization saga。
- root budget 与 delegated allocation，避免 GA/Model/Job 双预留。
- RequestSecurityContext 和跨端 principal。
- Site ActivationAttempt 和外部部署 crash reconciliation。
- Core/Advanced scope、5A→4→5B 顺序、profile-scoped Wave 8/9。
- Redeem/Payment 分离前半链、共享 Fulfillment/Grant 后半链。
- LiteLLM adapter isolation。

### 仍未完成但不是总架构开放题

| Item | 当前状态 | 关闭方式 |
|---|---|---|
| Umbrella v1.5 用户书面复审 | pending | 用户批准或提出修改 |
| 四来源仓内部 LicenseRef 权属确认 | pending | owner attestation；Wave 0 import hard gate |
| 首发 Site/Profile/Surface/Offering/Model 实际配置 | pending operational data | Wave 1/2A/5A child PRD + SiteRelease |
| 27 份产品 PRD | design-covered / review-required | 全部文件已存在且保留 implementationAuthorized=false；完成交叉 PRD 红队与用户复审 |
| 架构 child Spec | design-covered / review-required | 已关闭 P0 Contract、Session、Client、RPC、Budget、Media、Projection；继续做全局一致性红队 |
| GA runtime 变更 | gated | 每次命中 §10 清单先专项对齐 |
| 真实 Payment Provider | disabled for redeem-only | 2B 后才允许进入 assignment |
| 实现与生产证据 | implementation-not-authorized / evidence-not-started | 用户批准后实施；设计、评审或截图不能替代 RC evidence |

### 最终裁决

- **Product design coverage：** 27 份 Registry PRD、canonical journey crosswalk 与 Capability Contract Ledger 已形成；
  本轮机器追踪未发现 design-level orphan，仍需指定 cosigner 与用户复审。
- **Architecture design coverage：** Umbrella 与七份关键 child Spec 已覆盖 Platform/Web/Session、RPC、预算、Media、投影和客户端边界，仍处内部评审。
- **GA boundary：** 保留现有成熟底座；Handoff 等任何运行语义变化仍为 `GA-user-approval-required`。
- **Implementation authorization：** `implementation-not-authorized`；等待用户复审后才进入 writing-plans。
- **Production readiness：** `evidence-not-started` / No-Go；不存在有效 `ReleaseCertificationInstance`。

本审计证明“整体不会漏模块”，不把未来必须完成的 child 细节伪装成已经完成。后续每关闭一个 cut，都要
更新本矩阵的状态和 evidence ref；新增 Surface/Context 若没有 owner、child spec 和 certification scope，
SiteRelease compile 必须拒绝。
