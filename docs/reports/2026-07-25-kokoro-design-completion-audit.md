---
artifact: design-completion-audit
version: "1.0"
created: 2026-07-25
status: internal-review-active
scope: product-platform-web-session-commerce-model-job-media-site-admin-agent-testing-migration-operations
implementationAuthorized: false
gaRuntimeSemanticChangeAuthorized: false
---

# Kokoro 全局设计完成度与实现授权审计

## 1. Executive decision

本报告回答三个不同问题，禁止混成一个“完成”状态：

1. 产品与架构是否有可实施的设计覆盖？
2. 哪些设计仍需用户或 GA 专项批准？
3. 当前代码与生产证据是否已经存在？

当前裁决：

- 产品 Registry 已有 27 份 PRD，覆盖 Core、Studio、Operations、Growth、Trust、Model、Capability 与 Advanced Agent。
- Umbrella 与关键 child Spec 已覆盖 Platform/Web/Session、内部 RPC、预算树、Media Resource、投影重建、客户端访问和 Model/LiteLLM。
- 两轮独立红队发现的产品 Registry、首发附件/Library scope、上线证据分层和生产门问题已纳入当前修订。
- 设计仍为 `internal-review-active`；正式迁入 handbook、实现计划与业务代码均尚未授权。
- GA 的成熟 runtime 保留。Handoff、logical model call、delegated operation tool 等若无法零语义变化接入，必须暂停并取得用户专项批准。
- Production 仍为 No-Go：所有实现、迁移、RC、负向、安全、负载、DR 和 ReleaseCertification evidence 均未开始。

## 2. Status vocabulary

| Status | Meaning |
|---|---|
| `design-covered` | owner、边界、journey、状态、恢复、验收和 child contract 已形成 |
| `review-required` | 设计已形成，但指定 cosigner/用户尚未书面批准 |
| `GA-user-approval-required` | 可能改变 GA graph/checkpoint/tool/event/effect/terminal 等语义 |
| `implementation-not-authorized` | 不得开始业务实现或迁移 |
| `evidence-not-started` | 实现、RC、production-like 或 production evidence 不存在 |
| `qualified` | revision 有有效 CapabilityQualificationAttestation，不代表可上线 |
| `release-certified` | 具体 SiteRelease candidate 有 digest-bound ReleaseCertificationInstance |

## 3. Objective-area verdict

| Objective area | Design evidence | Verdict | Remaining gate |
|---|---|---|---|
| Product governance | Launch Profile、Journey/State/Recovery/Metric catalogs、27-PRD Registry | design-covered / review-required | named DRI routing、用户批准、迁 handbook |
| Platform modular core | Umbrella §4-7 + Modular Core/Internal RPC Spec | design-covered / review-required | implementation plan；不得 self-RPC/cross-module DB write |
| Web Fleet | PRD-12 + Umbrella Web Fleet rules | design-covered / review-required | 两个独立 Site Project production-like evidence |
| Web product UX | PRD-00/01/03/05/06/09/13/14/15/16 + vertical fixtures | design-covered / review-required | design QA、browser/a11y、真实状态 UAT |
| Session | PRD-05 + P0 Closure + Session HTTP/SSE Spec | design-covered / review-required | full snapshot/cursor/replay/backpressure/drain/10k-24h evidence |
| Identity/Workspace | PRD-01/02 | design-covered / review-required | Site-bound auth、MFA/device、membership/data-rights implementation |
| Catalog/Offering/Subscription | PRD-03/04 + Umbrella commerce model | design-covered / review-required | schema/UoW/provider implementation；redeem-first payment disabled |
| Redeem/Card Code | PRD-03 + Admin/Support PRDs | design-covered / review-required | CSPRNG/HMAC、atomic claim+fulfillment、maker-checker、fault tests |
| Payment/Refund/Dispute | PRD-04 | design-covered / review-required | disabled in first profile；future provider adapter certification |
| Credit/Usage/Rating | PRD-03 + Execution Budget Spec | design-covered / review-required | root Hold/allocation/journal conservation property/chaos evidence |
| Model Control | Model Architecture + PRD-17 | design-covered / review-required | provider/evaluation/canary thresholds、operator UAT |
| Model Gateway/LiteLLM | Model Architecture + P0 Closure | design-covered / review-required | one-alias config、attempt/usage、unknown/cancel/stream certification |
| Capability Hub/Runtime | PRD-18 + Capability Control/Runtime child Spec | design-covered / review-required | package/provider qualification values、GA differential gate、implementation evidence |
| Job/Operation | PRD-07/08* + P0 Closure | design-covered / review-required | provider callback/finalizer/unknown/usage evidence implementation |
| Media Resource | PRD-06/09 + Asset/Artifact/Blob/GC Spec | design-covered / review-required | three-owner schema、DerivedInputVersion、GCPlan/receipt evidence |
| Image Studio | PRD-07/08I + `image-studio@1` fixture | design-covered / review-required | real provider, mask/edit/batch/upscale, Trust/Artifact certification |
| Music Studio | PRD-07/08M + `music-studio@1` fixture | design-covered / review-required | dual model roles、audio rights、track/stem/export provider evidence |
| Video Studio | PRD-07/08V + `video-studio@1` fixture | design-covered / review-required | shot/long-job/partial/likeness/voice/export provider evidence |
| Admin/Support | PRD-10/11 | design-covered / review-required | no DB role/bypass、privileged auth、maker-checker、case recovery UAT |
| Growth/SEO/Experiment | PRD-13 | design-covered / review-required | consent/assignment/exposure/outcome implementation and Site metrics |
| Notification/Data Rights | PRD-15 + Projection Spec | design-covered / review-required | delivery receipts、participant/LegalHold/restore/rebuild evidence |
| Trust/Media Rights | PRD-16 + Studio/Media specs | design-covered / review-required | Decision/evidence split、appeal、edge purge/reporting incident tests |
| Projection/Event retention | Projection Rebuild Spec | design-covered / review-required | owner truth rebuild、shadow comparison、switch/rollback、DR exercise |
| AgentRevision/Handoff | PRD-A1 | review-required / GA-user-approval-required | product approval then separate GA Phase B approval package |
| Target/Device/Permission | PRD-A2 | design-covered / review-required | execution runtime/local connector security implementation |
| Developer Workspace | PRD-A3 | design-covered / review-required | worktree/diff/checkpoint/git/multidevice implementation |
| Routine/Connector/TaskView | PRD-A4 + PRD-18 | design-covered / review-required | normal Admission per trigger、projection rebuild、revoke evidence |
| AgentTeam/Application | PRD-A5 | design-covered / review-required | coordinator/budget/task graph/rollout implementation；GA boundary unchanged |
| CLI/Desktop/IDE | PRD-A6 + Client Access Spec | design-covered / review-required | OAuth/device/client supply chain/local target certification |
| Testing/Release/Operations | Delivery Program + Launch Checklist v1.1 | design-covered / review-required | all execution rows evidence-not-started |

## 4. Business chain closure

### 4.1 Redeem-first acquisition to value

```text
SiteRelease/Profile/Offering
→ Site-bound Identity + BillingAccount + Project
→ RedeemAttempt/Redemption
→ FulfillmentTransaction
→ SubscriptionTerm/EntitlementGrant/CreditGrant
→ Admission + one root Hold + bounded child allocations
→ Run or Operation/Job
→ Model/Capability/Target/Provider AttemptUsageFact
→ ArtifactVersion or Session terminal projection
→ Canonical UsageEvidence → Rating → Settlement/CreditJournal
→ Account/Library/Notification/Support/Data Rights
```

Payment、Redemption、AdminGrant 与 ProgramWindow 只共享 Fulfillment 之后的链路。首发关闭 Payment acquisition 时，
不得伪造 Order/Payment/Refund；外部售卡退款使用 external reference + Redemption source reversal/replacement。

### 4.2 Chat and agent chain

```text
Web/Client → Session submit → Platform Admission
→ opaque ExecutionManifest/modelAuthorizationHandle/capability grants
→ GA RunExecution
→ Model Gateway / Capability Runtime / delegated Job / ExecutionTarget
→ GA durable terminal + Session projection/snapshot/SSE
→ usage settlement、Artifact/TaskView、Support recovery
```

Session 不执行 GA、不定价、不 resolve 模型/Capability；GA 不读取 Site/User/Plan/Price，不扣 Credit，不拥有 Job/Artifact/
Provider business truth。CLI/Desktop/IDE 只是同一链路的新 public client。

### 4.3 Direct Studio and delegated generation

Direct Studio 与 GA tool 都创建同一 canonical OperationSpec，进入同一 Job/Attempt/Media Resource/Usage 链。区别只在
requester 与 attached/detached wait relation，不产生第二套 generation backend，也不让 GA 承担 Job owner。

## 5. Architecture integrity decisions

1. Platform 是 modular core；同 bounded context 内使用 transaction-scoped application interface，跨独立 context 使用
   versioned RPC + receipt/outbox/inbox。未来拆服务必须重画 aggregate/transaction/saga，不宣称换 adapter 即可。
2. Site Web 是独立产品项目；共享的是发布后的 capability packages 与同一后端，不共享 root lock、artifact 或 deploy。
3. `siteId` 是 Platform isolation；GA 只消费 opaque `namespace`，二者不相等也不形成双身份轴。
4. ModelDefinition/Deployment 单一列表，上层按 Chat/Music/Image/Video role bundle/option/assignment 组合；LiteLLM 只是 adapter。
5. 一次 ExecutionRoot 只有一个 root Hold，所有消费者使用有界 allocation；unknown liability 不释放复用。
6. Asset、Artifact、Blob/Lifecycle 是 Media Resource 内三个 owner；相同 bytes 不合并 Site、owner、rights 或 lineage。
7. full Session snapshot 是长期页面恢复入口；SSE 只做增量与有界 replay，invalid cursor typed fail。
8. Qualification 先于 candidate compile；ReleaseCertification 只能在 compile/build/preview 后生成，Activation 依赖后者。

## 6. Red-team closure

### Product red-team findings incorporated

- safe attachment 与 minimal Library 已从模糊 `if-enabled` 修正为 Reference Profile Core minimum；Public Share 保持 optional。
- 新增 PRD-17（Model）、PRD-18（Capability）与 PRD-A6（Client），并扩展 canonical journey families。
- Core/Advanced architecture journey 已增加 canonical journey 与 PRD/cut crosswalk。
- Coverage Contract 已落成逐 capability ledger，显式登记 entry、owner/truth、security/budget/idempotency、
  interface/terminal/failure/recovery、operations、PRD/Spec/cut/status；实现证据仍诚实标为未开始。
- 新增 Image/Music/Video 三个独立 Site Profile review fixtures。
- coverage 结论不再用“列出模块”冒充实现或 certification。

### Launch/SRE red-team findings incorporated

- Launch Checklist 使用 `Design approved → Implemented → RC verified → Signed`，不再使用自报 `production_ready` 布尔。
- 新增 Session snapshot/SSE、预算树守恒、projection/retention/DR、Media GC、多 Site project provenance、Admin DB/权限
  与 redeem-only 七层关闭的 P0 证据门。
- 第二个真实 production Site 不是首发前提，但两个独立 production-like Site Project 的隔离认证是 Must Have。

## 7. Remaining review gates

| Gate | Owner | Current state | Exit |
|---|---|---|---|
| Product cross-PRD review | Product/Architecture/Domain owners | autonomous red-team complete；human cosign pending | 27 PRD journey/state/recovery/metric 无 P0；指定 cosigner 签署 |
| Architecture boundary review | Platform/Web/Session/Commerce/Model/Runtime/Security/SRE | autonomous red-team complete；human cosign pending | ownership/RPC/data/failure/DR 无 P0；领域 owner 签署 |
| Named owner routing | Product leadership | not evidenced | team responsibility ID 映射 DRI、backup、on-call、signer |
| User design approval | User | pending | 书面批准当前设计包或提出修改 |
| GA Phase B changes | User + GA owner | not authorized | 每项语义 delta 独立批准；否则 Phase A zero-delta only |
| Implementation authorization | User | false | 用户批准设计后进入 writing-plans |
| Qualification/RC evidence | Engineering/QA/SRE/Security | not started | 实现后按具体 profile/candidate 生成，不可预填 |

## 8. Final verdict

设计包已通过本轮多代理与机器化内部红队，达到“提交用户做最终设计复审”的状态，但尚不能宣称“已批准”或
“可上线”。实现仍禁止启动，直到：

1. 用户审阅并批准设计包；
2. 对任何实际 GA 语义变化取得单独批准；
3. 随后使用 `writing-plans` 生成按 Wave、文件、测试和回滚拆分的实现计划。

设计批准不会自动生成生产证据。真实上线必须再通过 Launch Checklist 的 implementation、RC、security、load、DR、
rollback 和 digest-bound ReleaseCertification gates。
