---
artifact: product-requirements-document
prdId: PRD-05
version: "1.0"
created: 2026-07-25
status: internal-review-active
scope: chat-conversation-message-run-stream-control-branch-hitl-job-artifact-cost
accountableProductRole: Chat Product Lead
mandatoryCosigners: [Session, GA, Model Platform, Usage Rating, Trust, Web, Accessibility, QA, Support, SRE]
engineeringOwner: team:chat-session-engineering
qaOwner: team:chat-runtime-quality
supportOperationsOwner: team:chat-runtime-operations
namedOwnerAssignmentStatus: assigned-team-responsibility-ids
implementationAuthorized: false
gaRuntimeSemanticChangeAuthorized: false
---

# PRD-05：Chat Conversation、Run 与 Interaction

## 1. Overview

### 1.1 Problem Statement

Kokoro 已有 Chat、SSE、HITL 与 GA 执行底座，但当前实现与目标产品之间仍存在结构性缺口：浏览器状态、
Session 投影、GA Run、模型选择、Credit、后台 Job 与 Artifact 的 ownership 尚未完全分离；断线恢复仍可能把
live delta 当作长期事实；Stop、Cancel、Retry、Continue、Edit、Regenerate 的对象语义不够明确；HITL、模型
失败、费用 pending 与 Provider unknown 缺少统一的用户状态和运营闭环。

如果继续在现有页面和 Session billing path 上叠加功能，Chat 会同时变成会话库、Agent Runtime、模型路由器、
计费器和 Job 管理器。结果是重复 Run、重复副作用、错误释放 committed Hold、分支覆盖历史、用户刷新后看到
与真实执行不一致的状态，以及 Support 无法解释“发生了什么、是否收费、下一步做什么”。

### 1.2 Solution Summary

交付一个以 `Project → Session → ConversationBranch → Message/MessagePart → Run` 为用户主线的生产级 Chat：

- Web 只通过 Session HTTP/SSE 读写 Chat，不直连 GA、Model Gateway、Job、Artifact 或业务数据库。
- Session 拥有 Conversation、typed parts、branch、Run 投影、HITL 投影、浏览器 stream 与 control outbox；不执行
  Agent、不解析模型 Deployment、不授权 Capability、不计算价格、不 reserve/capture/release Credit。
- GA 只消费不可变 ExecutionManifest 与 opaque `namespace`，拥有 RunExecution、checkpoint、effect 与 terminal。
- Platform Admission 拥有 entitlement、model/capability resolution、rating snapshot 与 root Credit Hold；Model
  Gateway、Capability Runtime、Job 产生 AttemptUsageFact，Platform usage-rating 结算。
- 长任务通过 Job card 与 Artifact card 进入同一 Conversation；attached/detached lifecycle 不依赖浏览器存活。
- Snapshot、durable event 与 live delta 分层；断线只 attach 同一 Run/Job，不重新提交 Provider 或工具副作用。

本文定义产品旅程和验收语义，不授权实现，也不改变 GA 的 graph、assembly、tool、checkpoint、effect、Handoff、
namespace、runEpoch、lease 或 terminal semantics。

### 1.3 Target Users

- 首次用户：通过示例与空状态在最少步骤内完成第一轮有价值对话。
- 日常 Chat 用户：管理多个 Session、附件、分支、模型选项和历史输出。
- 高级 Chat 用户：在同一个 Chat 中查看 tool、plan、HITL、Job、Artifact 与费用，不进入另一套“高级账户”。
- 移动端与辅助技术用户：完成与桌面端等价的发送、恢复、审批、分支和结果访问。
- Support/SRE/运营人员：在严格 Site scope 下诊断 Run、stream、HITL、Job、Artifact 与费用状态并安全恢复。

### 1.4 User Stories

| ID | User story | Priority |
|---|---|---|
| US-CHAT-01 | 作为新用户，我能理解 Chat 能做什么并在 90 秒内完成首轮有效回复 | P0 |
| US-CHAT-02 | 作为用户，我能新建、查找、重命名、归档、删除和恢复自己的 Session | P0 |
| US-CHAT-03 | 作为用户，我能发送文本、已通过安全检查的附件与产品级模型选项，重复点击不会创建第二个 Run | P0 |
| US-CHAT-04 | 作为用户，我刷新、断网或切换设备后仍 attach 同一 active Run、HITL、Job 和结果 | P0 |
| US-CHAT-05 | 作为用户，我能明确 Stop 当前 Run、取消尚未开始的请求或 Job，并理解哪些结果/费用已经不可逆 | P0 |
| US-CHAT-06 | 作为用户，我能 Edit、Regenerate、Retry 或 Continue，同时保留原分支、工具、Job、Artifact 和费用历史 | P0 |
| US-CHAT-07 | 作为用户，我能安全 approve/reject/edit/respond，过期或需重认证时不会重复执行工具 | P0 |
| US-CHAT-08 | 作为用户，我只看到当前 Site、Plan 与 Surface 发布的 ModelOption，不会看到 Provider 或 Deployment | P0 |
| US-CHAT-09 | 作为用户，我能在 Chat 中启动媒体 Job、离开页面后继续运行，并通过 Artifact 进入 Library/Studio | P0 if-enabled |
| US-CHAT-10 | 作为 Support，我能从安全 correlation refs 重建投影、解释 partial/unknown/cost_pending，并走正式恢复流程 | P0 |

## 2. Goals、Metrics 与 Non-Goals

### 2.1 Goals

1. CH-01…CH-09 每条旅程都有明确对象、产品状态、恢复动作、费用语义和 Support owner。
2. 任意已接受提交最多创建一个用户消息、一个 launch identity 和一个 GA RunExecution。
3. active Run 在浏览器刷新、断网、Session/GA 单实例重启后可 attach/recover，不重复模型或工具副作用。
4. Message/Part/Branch 使用追加历史；Edit/Regenerate 永不覆盖旧消息、Job、Approval 或 Artifact provenance。
5. HITL 的 action、scope、deadline、expiry、reauth 和回执对用户与辅助技术均明确。
6. completed/partial/failed/canceled/unknown 与 cost_pending/settled/reconciliation_required 正交展示。
7. Chat 的所有 enabled 页面、状态、响应式变体和完整流程满足 PRD-14 的 WCAG 2.2 A/AA、locale 与时间要求。

### 2.2 Success Metrics

所有指标必须登记 ProductMetricRevision，并至少按 Site、Profile、SurfaceRevision、Web build、locale、device class、
ModelOption、Run terminal class 和 recovery path 分维度；不得用全局平均掩盖单 Site 或单辅助技术失败。

| Metric | Definition | Target |
|---|---|---:|
| First Chat TTFV | 完成注册/兑换后至首个成功可见 assistant part | p50 ≤ 90s，p95 ≤ 5m |
| Accepted submit uniqueness | 同一 command identity 产生的 user Message/launch/RunExecution 数 | 恰好 1/1/≤1；重复为 0 |
| Accepted Run explained terminal | 已 GA 接受且非用户取消的 Run 在期限内到 completed/partial/failed/unknown+owner | ≥ 99% |
| Active Run refresh/reconnect recovery | active Run 经刷新/网络切换后恢复同一 projection 与 control | ≥ 99.9% |
| Terminal projection convergence | GA terminal 后 Session/Web 收敛到一致 terminal | p99 ≤ 10s；超过进入 repair queue |
| Branch history loss | Edit/Regenerate/active-leaf switch 覆盖或遗失历史对象 | 0 |
| HITL duplicate effect | 重复/乱序/过期 decision 导致工具重复执行 | 0 |
| Unknown unsafe retry | unknown Provider/effect outcome 触发新 Attempt/Run | 0 |
| Cost integrity | committed Hold 无 owner、重复 capture、错误 release 或负余额 | 0 |
| Enabled Chat WCAG A/AA failure | 完整页面、状态、变体和 complete process | 0；任一失败阻断 Release |
| Support contact rate | 每千 Run 的 Case，按 reason/recovery 分层 | 建立首发 baseline；P0 spike 触发 release review |

### 2.3 Non-Goals

- 不在本文设计专业 Image/Music/Video Studio 编辑器；Chat 只展示/控制其 Job 与 Artifact 引用。
- 不实现真实 Agent Handoff、AgentTeam、Wide Research、Routine、ExecutionTarget 或 Developer Workspace。
- 不允许同一 Session 并行多个 active GA Run；detached Job 可以并行存在。
- 不让 Web 直接消费 GA raw event、Model Gateway invocation stream 或 Provider callback。
- 不让 Session 持有模型目录、Provider 路由、Capability policy、Credit Journal 或客户价格。
- 不把 TaskView、Job、Operation 或 Artifact 合并成新的万能 Chat aggregate。
- 不以客户端本地记录作为 Session、Run、HITL、费用或 Artifact 真源。
- 不在 PRD 中授权改变 GA 的 cancel、checkpoint、effect claim 或 terminal 语义。

## 3. Product Model 与 Ownership

### 3.1 Canonical objects

| Object | Product meaning | Authority |
|---|---|---|
| Project | Session、Asset、Artifact 与默认设置的用户可见容器 | Platform workspace |
| Session | 持续对话容器，拥有标题、归档/删除状态和 active leaf | Session |
| ConversationBranch | 从某 parent Message 分叉、指向一个 active leaf 的追加历史 | Session |
| Message | 一次 user/assistant/system-visible expression；发布后内容不可原地改写 | Session |
| MessagePart | versioned typed UI unit，可 append/patch/complete | Session projection |
| RunLaunchProjection | Admission 前后、GA 接受前的 launch/等待投影 | Session |
| RunExecution | 一次 Agent graph execution 的唯一写真源 | GA |
| RunView | GA durable facts 在 Chat 中的可恢复读投影 | Session |
| InteractionRequest | 登录、MFA、CAPTCHA、外部接管等非工具审批交互 | initiating owner；Session projection |
| ApprovalRequest/Decision | 精确 action digest 的 HITL 请求与用户决定 | GA/initiating runtime；Session control projection |
| Operation/Job | 可排队、租约、恢复、callback、独立 cancel 的后台能力 | Job |
| ArtifactVersion | 不可变结果版本与 provenance | Artifact |
| CostView | reserved/cost_pending/settled/reconciliation 的用户投影 | Platform Credit/Usage facts；Session reference |

产品界面可使用“Conversation/对话”作为用户术语，但 canonical contract 和存储对象统一叫 `Session`；不得再创建
与 Session 平行、互相映射的 Conversation aggregate。`ConversationBranch` 只表示 Session 内的消息分支。

`Run` 在产品文案中指 GA authoritative `RunExecution`。GA 尚未接受 launch 前，UI 只能显示 preparing、
waiting_prerequisite 或 recovering 的 `RunLaunchProjection`，不能宣称 started/completed/failed。

### 3.2 Message and part contract

```text
Message
  messageId / sessionId / branchId
  role = user | assistant | system_notice
  parentMessageId?
  triggerRunId?
  createdAt / completedAt?
  status = committed | streaming | completed | partial | failed | superseded_in_active_view
  parts[]

MessagePart
  partId / messageId / schemaVersion / ordinal
  kind
  lifecycle = created | streaming | completed | partial | failed | canceled | unsupported
  content/ref/safeMetadata
  languageTag? / accessibilityLabelRef?
  createdAt / updatedAt
```

首发 part kind：

```text
text | reasoning | citation | tool-call | approval | interaction | plan |
job | artifact | cost | notice | error
```

- `text` 是用户/助手正文；stream delta 只更新对应 stable part，不生成每 token 新 part。
- `reasoning` 只在 Site/Model/Policy 允许时显示；不得把隐藏 reasoning 泄漏到日志、transcript 或导出。
- `citation` 保存可验证 source ref、label、retrieval timestamp 与失效状态，不伪装来源可信度。
- `tool-call` 区分 proposed/awaiting/started/result/unknown，不向用户暴露 secret 或原始敏感参数。
- `approval` 与 `interaction` 必须分开；工具授权不能用登录/MFA 代替，登录/MFA 不能伪装 approve。
- `job`/`artifact` 只保存 owner ref 与安全投影，不复制 Job/Artifact 真源。
- `cost` 显示估算、reserved、pending 或 final receipt ref，不使用 Run terminal token total 计费。
- 未知 schema/version 渲染为 `unsupported` card，保留 message、part identity、时间、Support CTA 与原始安全 ref；
  不丢弃整条 Message，也不把未知内容当 HTML 渲染。

### 3.3 Boundary invariants

```text
Browser → Site Web/BFF → Session HTTP/SSE
Session → Platform Prepare/FinalizeRun
Session → GA Launch/Control
GA → Model Gateway / Capability Runtime / Job
Attempt producer → Platform usage-rating
GA/Job/Artifact/Platform facts → Session projections → Web
```

硬约束：

- 本 PRD 的 Chat Web 只经 Session HTTP/SSE 读写；Chat 中的 Job/Artifact/Cost card query/control 也通过 Session
  façade/projection 路由到真实 owner，不由浏览器直连其内部 RPC 或拼 internal reference。
- Session 不执行 Agent、不选择 Deployment、不翻译 Provider 参数、不读 Hub 数据库、不扣 Credit、不写 Job/
  Artifact 真源、不自判 GA terminal。
- GA 只消费 opaque `namespace` 作为隔离键。Site/User/Workspace/Plan/Price/Provider secret 不进入 GA wire，
  不建立第二身份轴。
- GA 继续拥有 graph、assembly、tool、checkpoint、effect、Handoff、Run lease/epoch 与 terminal；本文只要求
  Session 正确投影其 durable facts。
- 每个 Run 使用一个 execution root/root Hold。GA 创建 attached/detached Job 时使用 delegated allocation，不创建
  第二个账户 Hold。

## 4. Canonical Journeys

### 4.1 CH-01 — Onboarding and first value

Entry：首次进入 General Chat、兑换成功后的 next action、或无 Session 的 Project。

1. 显示 Site-specific 空状态、产品能力边界、隐私/附件提示和 3–6 个经 Product owner 发布的示例。
2. 示例是可编辑 composer draft，不点击即执行，不携带隐藏附件/工具/模型参数。
3. 若用户未选择 ModelOption，使用 SiteRelease 发布的 default option；`assistant.primary` 可对用户隐藏但必须完整。
4. 首次提交前显示可用 Credit/资格摘要；不要求用户理解 Provider、Deployment、Hold 或内部 role。
5. Admission 拒绝时保留 draft，并给出 redeem、change_parameters、reauthenticate 或 Support 的精确动作。
6. 首个成功回复可引导用户保存 Session、打开 Artifact 或继续提问，但不强制弹窗和增长流程。

终态：first_value_completed、draft_retained_after_block、user_abandoned。TTFV 只计算可见且可理解的成功 assistant
part，不把 placeholder、queued、tool-only 或 error 当成功。

### 4.2 CH-02 — Session management

- 新建：创建空 Session，不创建 Run、不 reserve Credit；首条提交时再完成 Project/ExecutionSpace authorization。
- 列表：按 updated time 分页，显示 title、最近安全摘要、active/attention state、Job badge，不加载完整消息正文。
- 搜索：只返回当前 Site/Project/subject 有权的 Session；索引延迟必须显示 freshness，不用跨 Site fallback。
- 标题：自动标题只是建议且有 provenance；用户重命名优先，后台 summary 不得覆盖用户 title。
- 归档/恢复：不删除内容、不 cancel Run/Job；active Session 归档前确认并说明仍运行对象。
- 删除：先进入 soft-deleted/trash；active Run 请求 Stop，detached Job 按发布 policy 继续或显式 cancel；retention、
  LegalHold、Artifact、Data Rights 由各 owner 处理，不能由 Session 跨库删除。
- permanent deletion 只由 PRD-15 Data Rights/Product Closure workflow 执行；Chat UI 只显示 request/receipt。
- deep link 到无权、已删或过期 Session 不泄漏存在性，提供安全返回与 Support 路径。

### 4.3 CH-03 — Composer、attachment and submit

Composer draft 包含：

```text
text
ordered attachmentRefs
selected ModelOption ref or published-default marker
optional product-level effort/agent entry allowed by Surface
clientCommandId / idempotencyKey
draftRevision
```

提交规则：

1. IME composition 期间 Enter 不提交；支持 multiline、grapheme-safe limit、paste、undo 和移动端键盘。
2. 空白文本仅在至少一个 `ready` attachment 或明确支持的 structured input 存在时可提交。
3. 附件必须来自 PRD-06 的 typed Asset ref 且状态为 `ready`；uploading/scanning/quarantined/failed/expired 不创建
   可执行 Run。用户可移除失败附件而不丢文本 draft。
4. Web 发送 `clientCommandId + idempotencyKey + canonical draft digest`。同 key/同 digest 返回同一 Message/
   launch receipt；同 key/不同 digest 返回 idempotency conflict 并保留最新 draft。
5. Session 原子/可恢复地持久化 user Message、branch linkage、launch identity 与 command receipt，再调用 Platform
   Admission。响应丢失后客户端查询 receipt，禁止换 key 自动重发。
6. 同一 Session V1 只有一个 active GA Run。已有 active Run 时，新输入默认进入 draft，不自动 steer；只有发布的
   `steer_current_run` capability 明确启用且 GA 语义专项批准后，才可提供运行中插话。
7. selected ModelOption、effort、agent entry 是产品 ref；Provider/Deployment/raw model string 被拒绝。
8. 发送成功后 composer focus 保持；清空的是已 receipt 的 draft revision，不清空用户在响应等待期间的新输入。

### 4.4 CH-04 — Stream、snapshot and reconnect

浏览器恢复协议固定为：

```text
GET Session snapshot
  → messages/parts projection + active Run/Job/HITL refs + projection watermark
attach Session SSE with opaque ack cursor / Last-Event-ID
  → replay durable events after watermark
  → hand off to live tail
Web dedupe by stable eventId and apply monotonic part/run versions
```

- `SessionStreamCursor` 是 Session transport 的 opaque ack cursor，不是 GA durableSeq、Model Gateway cursor、业务
  ordering key 或客户端可构造的 offset。客户端只回传最后完整应用的 cursor；错误、过期或跨 Session cursor 触发
  snapshot repair，而不是空流或 Provider retry。
- Snapshot 是长期可读投影；durable Session events 用于增量收敛；live delta 是 best effort。丢失 reasoning/text
  delta 由 durable part complete/partial/terminal 收口。
- `ack` 只表示 Web 已应用 Session event，不授权删除长期事实，也不证明用户看过内容。
- 重连期间显示 recovering 与最后更新时间；不得把断线显示成 Run failed，也不得自动 Stop/Cancel。
- 多 Tab 同时 attach 可以共读；mutation 使用 expectedVersion/idempotency，不能因两个 Tab 重复 control。
- terminal event 丢失时，Session 从 GA authoritative lookup/durable outbox 修复 RunView；Job/Artifact card 分别从其
  owner receipt 修复。投影修复不写回或重跑执行真源。
- cursor replay 过期时返回 typed `stream_replay_expired`，Web 重新取 snapshot 并恢复 logical message anchor。

### 4.5 CH-05 — Stop、Cancel、Continue and Retry

四个词严格绑定对象，UI 不显示无对象的万能“取消”：

| Action | Applies to | Semantics |
|---|---|---|
| Stop | running/waiting_input GA Run | 向 GA 发送 `CancelRunExecution(expectedVersion)`；进入 stopping，结果由 GA terminal 决定；当前轮/在飞 effect 遵循已批准 best-effort 语义 |
| Cancel launch | preparing/waiting_prerequisite、GA 尚未接受 | 取消 RunLaunchProjection，证明未创建 RunExecution/Attempt 后释放 reserved authorization；unknown 时先 reconcile |
| Cancel Job | queued/running Job card | 路由 Job owner 的 expectedVersion command；attached/detached 均不由 Session 自判终态 |
| Continue | terminal Run 后继续同一 branch | 新建 user Message 和新 Run；不 resume 已 terminal GA Run，不隐藏旧 partial/cost |
| Resume HITL | paused Run 的有效 request | 对同一 Run 提交 decision；不是 Continue，也不新建 Run |
| Retry same identity | 确定 command/launch 未执行或 receipt 可查 | 复用原 key/digest，返回/推进同一 aggregate |
| Regenerate | 对同一 trigger 重新生成 | 新 Run + 新 assistant branch，保留原分支 |

- 用户 Stop 后立即显示 `stopping`，而不是伪造 canceled。GA 返回 completed/partial/canceled/failed/unknown 后再收口。
- detached Job 默认不随 Run Stop；attached Job 根据冻结 cancel policy 请求取消并显示自身状态。
- 已产生 token/tool/Artifact 后的失败，Retry 必须是用户明确的新 branch/Run；禁止无感跨模型拼接。
- Provider/effect outcome unknown 时只允许 wait_and_refresh/request_support，不允许 Retry/Regenerate 自动重放。
- Continue 可以由用户输入新内容，也可使用明确的“继续”suggestion；它始终产生可见 user intent Message。
- Cancel/Stop 不自动释放 committed Hold。只有 authoritative outcome 和 Usage/Rating/Settlement 决定 capture/release。

### 4.6 CH-06 — Edit、Regenerate and branch navigation

```text
Message.parentMessageId
Run.triggerMessageId
ConversationBranch.root/leaf
Session.activeLeafMessageId
```

- Edit 创建一个新 user Message，parent 指向被编辑消息的 parent；原消息不可变。
- 被编辑消息之后的 assistant/tool/Job/Approval/Artifact 留在原 branch；不会删除、改 owner 或迁移费用。
- Regenerate 从同一个 trigger user Message 创建新的 Run 和 assistant branch；每次 regenerate 有独立 launch identity。
- branch selector 显示当前位置、兄弟分支数量、创建时间、terminal/cost/Artifact 摘要，不泄漏隐藏 reasoning。
- 切换 active leaf 只改变读投影；active Run 所属 branch 在运行期间可查看但不能被另一 branch 的 composer 输入
  隐式接管。
- 若当前 Session 有 active Run，用户切到旧 branch 后 Regenerate 必须等待/Stop 当前 Run；V1 不并行两个 active Run。
- 从历史 Message edit/regenerate 时，附件/ModelOption/AgentRevision 不自动升级为当前配置。UI 显示原 snapshot，
  新 Run 重新 Admission；已撤销或无权 ref 要求用户 change_parameters，不静默替换。
- Branch deep link 使用 stable branch/message ID；删除/归档 Session 后遵循相同授权和 retention。

### 4.7 CH-07 — HITL、approval、interaction and reauthentication

HITL 产品状态：

```text
requested → visible → decision_recorded → applied → resumed
requested/visible → expired | revoked | superseded
decision_recorded → failed_to_apply | reconciliation_required
```

每个 request 必须显示：request kind、发起 Run/tool、用户可理解的 action/resource、风险等级、参数变化摘要、
allowed decisions、费用影响、deadline/timezone、是否可延长、需要的 auth strength、privacy notice 和 Support ref。

- Tool approval decision：`approve | reject | edit`。`respond` 仅用于 ask-user/input request。
- InteractionRequest 用于 login/MFA/CAPTCHA/external takeover，不使用 approve/reject；完成后返回原 intent。
- Decision 绑定 requestId、exact action digest、runId、branchId、actor、auth/session generation、policy revision、
  expectedVersion、decisionId、expiry。参数变化后旧 approval 失效。
- 同一 frame 有多个 request 时按稳定顺序呈现；只有 contract 明确允许 batch decision 时才能一次提交，且每项
  都有独立决定和回执。禁止“全部允许以后也允许”的暗选项。
- 高风险/过期 session 在 decision commit 前 step-up reauth。Reauth 成功不等于批准，只恢复原 request；失败、
  cancel 或 open-redirect 校验失败不改变 Run/effect。
- deadline 前按 TimingPolicy 提醒并允许符合 PRD-14 的 extend；expiry 后不能提交旧 decision。系统按冻结 policy
  reject/cancel/fail 或等待新 request，绝不默认 approve、skip 或重跑工具。
- decision response 丢失时查询同 `decisionId` receipt；同 ID/同 digest 返回同结果，同 ID/不同 digest conflict。
- Session control outbox 投递失败时显示 `decision_recorded/pending_apply` 并后台重试同 decision；不能要求用户再点。
- applied 只表示 GA/owner 接受 decision；外部 side effect 成功与否仍由 tool/Job/Attempt fact 决定。

PlanProposal 与工具 approval 分离。Proposal 必须引用真实 `ownerRef`、目标、步骤摘要、预算/时间上限、待用
Capability/Job、可见风险、expiry 和 revision；Session 只保存对话投影。`AcceptPlanProposal`/`RejectPlanProposal`
按 ownerRef 路由，使用 expectedVersion/idempotency/reauth policy。Accept 只允许 owner 进入下一状态，不等于批量批准
未来工具或副作用；每个需要 ask 的 action 仍产生独立 ApprovalRequest。Proposal 变更创建新 revision，旧 acceptance
不能应用到新步骤、预算或资源。

### 4.8 CH-08 — Model option

- 用户看到 SiteRelease 发布的 `ModelOptionRevision`（如 Standard/Fast/Quality），不看到 Provider、Account、region、
  Deployment、LiteLLM alias 或 raw model ID。
- 未选择时使用发布的 default Option；General Chat hidden `assistant.primary` 仍由 EffectiveModelBundle 完整解析。
- selector 显示能力、相对速度/质量、支持的附件/上下文、可能的费用区间与 Plan eligibility；不承诺具体 Provider。
- 选择在 submit receipt 中冻结 Option revision；Session 只保存 selection，不 resolve Profile/Pool/Deployment。
- disabled/expired/unentitled/不兼容 Option 在 Admission 前 fail closed，保留 draft并提供 change_parameters/redeem；
  不静默回 default。
- health failover 只在 Gateway 已授权 route 内发生。首 token/effect 后禁止无感跨模型 continuation。
- retry/regenerate 可以让用户选择当前可用 Option，但必须新建 Run；历史 Run 继续显示原 Option label snapshot 与
  safe route explanation ref。
- Site 没开放 selector 时不显示空控件；hidden default 仍必须在 Release certification 中通过 role completeness。

### 4.9 CH-09 — Media Job、Artifact and cards

- GA tool 发起媒体/后台 Operation 时，Session 创建/更新 `job` part，引用 `operationId/jobId/runId/toolCallId`。
- `attached` Job：Run 等待；Run Stop 按冻结 policy请求 Job cancel。`detached` Job：Run 可结束，Job 继续，card
  明确“可离开页面”。
- Job card 显示 admission/queue/progress/finalizing/partial/unknown/cancel/cost 状态、创建时间、预估/已等待时长、
  当前恢复动作与通知偏好。Provider internal job ID 不暴露。
- Job 完成且有 Artifact receipt 后添加 `artifact` part；Blob/Artifact 仍归 Artifact owner，Session 不复制二进制。
- Artifact card 支持 preview、download（需重新授权）、open in Library，以及该 Site 启用时的 open in Studio。
- partial candidates 分别保留 ArtifactVersion/provenance；Retry 创建新 JobAttempt/Operation policy 指定的新 attempt，
  不覆盖 partial 结果。
- Provider outcome unknown 不显示 failed 或“重新生成”；显示 wait_and_refresh、reconciliation deadline 与 Support。
- Job/Artifact/Usage event 丢失时从 owner receipts 修复 card，不重跑 Provider。

## 5. User-Visible State Catalog

### 5.1 Run execution and cost are orthogonal

```text
executionState = preparing | waiting_prerequisite | queued | running | waiting_input |
                 stopping | recovering | completed | partial | failed | canceled | unknown

costState = none | estimating | reserved | committed | cost_pending | settled |
            released | reconciliation_required
```

禁止把 `completed/cost_pending` 显示成“未完成”，也禁止把 `failed/settled` 显示成“未收费”。每个组合只显示
owner 已确认的事实：

| Execution state | User meaning | Allowed actions |
|---|---|---|
| preparing | 正在校验资格/配置，尚无 GA Run | Cancel launch；等待 |
| waiting_prerequisite | 附件/目标/交互未满足，尚未 dispatch | provide_input、reauthenticate、Cancel launch |
| queued | GA 已接受，等待执行 | Stop；查看 queue freshness |
| running | 正在执行，可能已有不可逆 effect | Stop；离开页面；查看 activity |
| waiting_input | GA 已暂停等待有效 HITL/Interaction | provide_input/approve/reject/edit、extend、Stop |
| stopping | Stop 已记录，终态未确认 | wait_and_refresh；不得重复 Stop 产生新命令 |
| recovering | projection/worker 正在从 durable truth 收敛 | wait_and_refresh；保留 last known safe state |
| completed | 预期结果完成 | Continue、Regenerate、open Artifact；费用可能 pending |
| partial | 有可保留结果但未完整完成 | Continue/Regenerate 明确新 Run；保留 partial 与费用 |
| failed | 已确定失败 | 按 retry safety Retry/Regenerate/change_parameters/Support |
| canceled | authoritative owner 确认取消 | Continue/Regenerate；显示已发生 effect/cost |
| unknown | 无法确认 Provider/effect outcome | wait_and_refresh/Support；禁止 Retry |

### 5.2 Error taxonomy

用户错误必须是稳定 code + localized explanation + safe detail ref，不以 Provider exception 文本作为 UI contract：

```text
chat.submit.invalid
chat.submit.idempotency_conflict
chat.session.active_run
chat.attachment.not_ready
chat.model_option.unavailable
chat.admission.entitlement_denied
chat.admission.credit_insufficient
chat.admission.risk_denied
chat.launch.unknown
chat.stream.replay_expired
chat.run.failed
chat.run.partial
chat.run.unknown
chat.hitl.expired
chat.hitl.reauthentication_required
chat.control.version_conflict
chat.job.unknown
chat.cost.pending
chat.cost.reconciliation_required
chat.contract.unsupported_part
```

相同 code 可以有不同安全 detail category；不得将 raw prompt、tool args、Code、secret、Provider body、跨 Site
identity 或隐藏 policy reason 放进 URL、toast、analytics 或 Support copy。

## 6. Recovery Matrix

| Condition | RecoveryAction | Required behavior |
|---|---|---|
| submit response lost | retry_same_identity | 查询/重发同 key+digest，返回同 Message/launch receipt |
| Admission definitely rejected | change_parameters / redeem / reauthenticate | 保留 draft，不创建 GA Run，不收费 |
| launch finalized、GA response lost | wait_and_refresh | 只查同 launch/run；无 authoritative no-execution proof 不释放 committed Hold |
| SSE disconnected | resume | snapshot + Session cursor attach，同一 Run 不重启 |
| cursor expired/corrupt | wait_and_refresh | 全量 snapshot repair；不使用 cursor 推断 terminal |
| HITL pending | provide_input | 精确 request、deadline、scope、privacy、decision receipt |
| HITL expired | reauthenticate / provide_input | 旧 decision 永久无效；按 policy创建新 request或收口 |
| terminal failed before any effect and retry-safe | retry_same_identity or Regenerate | launch transport 重试复用 identity；产品重试新 branch/Run |
| partial output/effect exists | Regenerate / Continue | 用户明确创建新 Run，旧结果、费用与 lineage 保留 |
| Provider/effect unknown | no_user_action / request_support | 后台 reconcile；禁止重复副作用 |
| Job callback/event lost | wait_and_refresh | owner lookup/receipt repair，不重跑 Provider |
| completed but cost pending | no_user_action | 结果可用；后台 settle，通知 final/reconciliation |
| projection contract incompatible | request_support | 保留 raw durable ref、显示 unsupported card、进入 DLQ/repair |

任何状态都不能只显示“请稍后重试”。必须显示最后更新时间、是否已提交、是否可能收费、是否安全重试、后台
owner、预计/最大等待窗口和 Support deep link。

## 7. Web、Mobile、Accessibility and Localization

### 7.1 Desktop and mobile information architecture

- Desktop：Session rail、message thread、composer 为主；activity/Job/Artifact/branch 采用可关闭 side panel。
- Mobile：同一 Session，不建立简化真源；rail、branch、activity、Artifact 进入分层 route/drawer，返回保留 logical
  message anchor、composer draft 和 active control。
- 复杂 tool/reasoning 默认摘要，可展开；用户正文、HITL、错误、费用和关键结果不得埋在 hover。
- 页面 background/锁屏不 Stop Run；重新前台通过 snapshot/attach 恢复。
- 草稿可以 Site-local encrypted-at-rest browser storage 作为便利缓存，但服务器 receipt 后的 Message/Run 状态不得
  从 localStorage 恢复或覆盖。

### 7.2 Accessibility hard requirements

- 整个 enabled Chat Surface、所有状态、响应式变体和 complete process 满足 PRD-14；任一适用 WCAG 2.2 A/AA
  failure 阻断 Release，不能按 defect severity waiver。
- Stream 不逐 token `aria-live`；按阶段/段落节流，terminal 只播报一次，可关闭自动播报。
- 新消息、tool、HITL、reconnect、branch switch 不抢 composer/阅读焦点；提供跳到最新、跳到待处理、unread count。
- virtualized history 不卸载 focused object；提供完整、线性、非虚拟化 accessible transcript，包含所有可公开
  message/part、speaker、tool/HITL state、error、citation、cost 与 recovery action。
- transcript/main view/branch switch/reconnect 保留 logical message anchor 和 reading position。
- Stop/Cancel/Retry/Continue、ModelOption、Job/Artifact card 的 name/role/state/disabled/cost effect 可由 AT 读取。
- HITL deadline、extend、expiry、reauth 有固定 focus return；触发点消失时 focus 到新状态标题或下一安全对象。
- Code/table/citation/diff 有 semantic/plain-text alternative；颜色、spinner、动画不是唯一状态表达。

### 7.3 Localization and time

- Message content language 与 formatting locale 分离；用户/模型内容未知语言时不假标 Site locale。
- Session title、示例、错误、状态、HITL、费用、通知和 Support macro 使用 SiteRelease 冻结 bundle revision。
- SSE/reconnect/hydration 期间 `siteReleaseId + locale + bundleDigest + formatterRevision` 原子一致，不出现可见文案与
  accessible name 不同 revision。
- deadline、queue time、Run/Job start/finish、Credit expiry 显示 absolute instant、timezone 和必要 relative time；
  authoritative deadline 不由浏览器本地时间决定。
- RTL/bidi、IME、grapheme、emoji/ZWJ 与 logical-order copy 遵循 PRD-14；opaque Code/ID 不做 locale normalization。

## 8. Trust、Privacy and Security

- 每个 command 重新验证可信 SiteContext、actor principal、Session/Project authorization、CSRF、expectedVersion、
  restriction epoch 和 audience；浏览器 siteId/releaseId/namespace 不作为授权证据。
- prompt、attachment、tool result、citation 与 model output 都是不可信内容，必须经过 typed rendering/sanitization；
  禁止任意 HTML、URL scheme、filename、Markdown link、SVG 或 code execution 逃逸。
- attachment intake、ContentPolicy、moderation、appeal 由 PRD-06/16 管理；Chat 不把 policy deny 伪装 Provider error。
- generation、download、share 是独立权利；Artifact 可生成但不可分享时仍显示费用、限制原因类别和 appeal。
- logs/traces/metrics 默认只存 opaque refs、size、class 和 safe error code，不存 prompt/output/tool args 全文。
- Support timeline 采用 PII masking 与 Site scope；跨站搜索必须 GlobalScope+reason+audit，不可按邮箱泄漏存在性。
- Session、Message、Approval、stream journal、accessible transcript 是 PRD-15 export/delete/retention participants；
  LegalHold 与 data-rights workflow 不由 Chat route 绕过。
- Reauth return intent 必须 same-Site allowlist、CSRF-safe、single-use/short TTL，不能将 HITL action digest放入开放 URL。

## 9. Admin and Support Operations

### 9.1 Required read views

在 Site-scoped Admin 中提供安全 timeline：

```text
Session / Branch / Message / Part projection versions
RunLaunchProjection / Admission / manifest ref / GA Run state
durable cursor / projection lag / reconnect count / DLQ
HITL request / decision receipt / expiry / reauth (masked)
Operation / Job / Attempt / Artifact receipts
root Hold / cost state / Usage settlement refs
safe errors / owner / next reconciliation deadline
```

Admin 不显示完整 secret、卡密、Provider credential、隐藏 reasoning 或默认未获业务授权的 prompt/output。

### 9.2 Operator commands

所有命令必须进入 OperatorCommandMatrix，包含 role、Site/Global scope、risk class、reason、step-up、maker-checker、
expectedVersion、idempotency、PII masking、queue owner、SLA、audit、用户通知和 runbook。

| Command | Scope/risk | Product effect |
|---|---|---|
| RebuildSessionProjection | Site / medium | 从 GA/Job/Artifact durable truth 重建读投影；不重跑执行 |
| ReattachRunProjection | Site / medium | 修复 lost subscription/outbox cursor；不创建第二 Run |
| RequestRunStop | Site / high | 代用户发送 GA control；必须展示不可逆 effect/cost，不自判 canceled |
| ReconcileUnknownRun | Site / high | 查询 GA/Gateway/Capability/Job receipts，形成 reconciliation decision |
| RequeueProjectionDLQ | Site / medium | 重放 projection event；不得触发 Provider side effect |
| ExpireInvalidHITL | Site / medium | 关闭已过期 request projection；不能默认 reject/approve真实 owner状态 |
| OpenRuntimeSupportCase | Site / low | 预填安全 refs 与 timeline，不复制敏感内容 |
| ApplyCreditCorrection | 不属于 Chat command | 必须走 Commerce 正式 Correction/AdminGrant/reversal workflow |

Support 不能直接改 Message、Run terminal、Job、Artifact 或 Journal。用户可见 Case resolution 必须说明：执行结果、
费用状态、是否有 partial Artifact、采取的恢复动作、后续通知和可申诉/复核路径。

### 9.3 Runbooks and alerts

必须有：SSE reconnect storm、projection lag/DLQ、GA launch unknown、stuck running/stopping、HITL pending age、Job
unknown/finalization lag、cost_pending/Hold aging、cross-Site denial spike、unsupported part、notification delivery failure。
每个 alert 绑定 owner、page/ticket threshold、user impact、safe diagnostic query、recovery command 与 escalation SLA。

## 10. Functional Requirements

### 10.1 Session and branch

- FR-CHAT-001：Session 所有 read/write 自动注入可信 Site/subject scope；跨 Site/无权请求不泄漏存在性。
- FR-CHAT-002：Session title/archive/trash/restore 使用 expectedVersion 和幂等 command；与 active Run/Job 的关系明示。
- FR-CHAT-003：Message/Part/Branch 追加且有稳定 identity；Edit/Regenerate 不更新历史 content/provenance。
- FR-CHAT-004：一个 Session 同时最多一个 non-terminal GA Run；Job 不计入该互斥。
- FR-CHAT-005：未知 part schema 安全降级并保留 Support/upgrade path。

### 10.2 Submit and admission

- FR-CHAT-010：submit receipt 同时绑定 command key、canonical digest、Session/branch/draft revision、Message 与 launch。
- FR-CHAT-011：重复同 key/同 digest 返回同 receipt；不同 digest conflict；响应丢失可查询。
- FR-CHAT-012：Attachment 非 ready、Option 无权、auth/risk/entitlement/Credit 拒绝不得 dispatch GA。
- FR-CHAT-013：Session 调用 Platform Prepare/Finalize；不得自行解析 entitlement/model/capability/rating或变更 Hold。
- FR-CHAT-014：Finalize 后只以同 launchId/runId 重试 GA；无权威 no-execution proof 不释放 committed Hold或新建 Run。
- FR-CHAT-015：GA 接受前所有状态叫 RunLaunchProjection；GA 接受后 terminal 只来自 GA facts。

### 10.3 Stream and projection

- FR-CHAT-020：snapshot 包含投影 watermark、active Run/Job/HITL refs 与 part schema versions。
- FR-CHAT-021：durable event at-least-once、eventId 去重、aggregate/part version 单调；live delta 可丢但终态收口。
- FR-CHAT-022：SSE cursor opaque、Session-bound、tamper-safe；invalid/expired/cross-session 均 snapshot repair。
- FR-CHAT-023：Session 投影失败进入 DLQ/repair，不反向标记 GA/Job failed。
- FR-CHAT-024：terminal、Job completion、Artifact、cost 事件丢失均从真实 owner receipt 修复，不重做 effect。

### 10.4 Control and HITL

- FR-CHAT-030：Stop/Cancel/Continue/Retry 的对象、expectedVersion、retry safety 和费用说明必须可见。
- FR-CHAT-031：control decision 使用 durable outbox/receipt；重复 decisionId 不重复应用。
- FR-CHAT-032：approval 与 interaction 分型，allowed decisions 由真实 owner contract提供，Session不得扩张。
- FR-CHAT-033：expiry/reauth/extension 遵循冻结 TimingPolicy；过期不默认批准、跳过或重跑。
- FR-CHAT-034：unknown outcome 禁止自动 Retry/Regenerate；必须 reconcile 或 Support。
- FR-CHAT-035：PlanProposal accept/reject 路由真实 owner；accept 不产生隐含 tool approval，revision/digest变化后旧决定失效。

### 10.5 Model、Job and cost

- FR-CHAT-040：Web/Session 只传/存 ModelOption revision；Gateway 才选择 Deployment。
- FR-CHAT-041：默认/hidden role 必须在 SiteRelease compile 完整，不允许运行时 global fallback。
- FR-CHAT-042：Job card 只引用 Job truth；attached/detached、cancel、partial、unknown 与 Artifact receipt明确。
- FR-CHAT-043：Session 不以 token total settle；cost view 来自 root Hold、AttemptUsageFact、Rating/Settlement投影。
- FR-CHAT-044：completed/cost_pending 可交付结果；settlement failure 不重跑 Run/Provider。
- FR-CHAT-045：用户可从每个 final cost view 查看安全 receipt、source bucket projection 与 dispute/Support入口。

## 11. Edge Cases and Failure Matrix

| Scenario | Expected behavior |
|---|---|
| 双击发送/浏览器自动重试 | 同 command receipt；一个 user Message、一个 launch、最多一个 RunExecution |
| 相同 key 不同内容 | idempotency conflict；旧 receipt不被新 draft覆盖 |
| user Message 已存、Admission timeout | preparing/recovering；查询同 Admission；不创建第二 Message |
| Finalize committed、GA RPC timeout | launch unknown；查询同 runId/launchId；禁止 release/recreate |
| GA Run 已建、Session crash | 启动后从 durable facts恢复同 RunView和active lock |
| SSE 在 text delta 中断 | snapshot+cursor attach；completed/partial part 收口，不重跑 model |
| terminal event 比前序 part先到投影 | durable sequence/version等待缺口或repair；不提前清空active state造成历史丢失 |
| 两 Tab 同时 Stop | expectedVersion/decision idempotency；GA只处理一个有效control identity |
| Stop 后 late token/usage | UI按 GA terminal fence忽略非法 display delta；Usage/Cost仍入账；不由Session删除事实 |
| HITL decision响应丢失 | 查询decision receipt；不再次点击生成新decision |
| Reauth期间HITL过期 | 返回expired状态；reauth不复活旧grant/action digest |
| Edit包含已撤销attachment/model | 保留原branch；新branch要求change_parameters，不静默替换 |
| Regenerate时已有active Run | 阻止并提示等待/Stop；不并发第二Run |
| detached Job在Run结束后完成 | 更新同job/artifact card并通知；不改变旧Run terminal |
| Job callback重复/乱序 | Job owner reducer去重；Session只投影最新authoritative version |
| Artifact创建成功但part event丢失 | owner receipt修复card；不重跑Job |
| Run completed、Usage服务不可用 | 结果可见+cost_pending；Hold committed由后台settle/reconcile |
| Provider unknown后用户点Retry | 禁止并解释；wait_and_refresh/Support |
| Model Option被实时撤销 | 尚未effect的Attempt拒绝；已开始Attempt按冻结policy收口；不静默default |
| SiteRelease回滚时Run活跃 | Run使用冻结Manifest；旧tab在兼容窗口attach；新Run用新Release |
| unknown part/version | unsupported card+Support；其余Message继续可读 |
| archived/deleted Session有active objects | 显示确认和object-specific policy；不以隐藏页面冒充cancel/delete |
| browser localStorage损坏 | 丢弃本地draft cache或安全恢复；不覆盖服务器Session/Run事实 |

## 12. Acceptance Criteria

### AC-CH-01 — Onboarding to first value

```gherkin
Given a new core-redeem-chat user has valid entitlement and Credit
When they open Chat, edit a published example and submit it
Then one Session, one user Message and one Run launch receipt are created
And a completed or partial assistant response is visible with an explicit cost state
And TTFV is measured from the published journey entry rather than page render
```

### AC-CH-02 — Session management lifecycle

```gherkin
Given a user has active, archived, trashed and restored Sessions
When they list, search, rename, archive, trash and restore them
Then every command remains Site and subject scoped and idempotent
And active Run and detached Job consequences are explained before destructive actions
And no operation deletes GA, Artifact or legal-retention facts directly
```

### AC-CH-03 — Submit idempotency under crash

```gherkin
Given the same submit is retried after crashes before and after Message persistence, Admission finalization and GA acceptance
When every retry uses the same command key and canonical digest
Then exactly one user Message and launch receipt exist
And at most one GA RunExecution exists for the launch identity
And a different digest with the same key is rejected without replacing the original receipt
```

### AC-CH-04 — Attachment and model fail closed

```gherkin
Given an attachment is scanning or quarantined or a ModelOption is expired, disabled or not entitled
When the user submits
Then no executable Run is dispatched
And the text draft and safe attachment references are preserved
And the UI offers the exact remove, wait, appeal, change-parameter or redeem action
And no raw Provider or Deployment fallback occurs
```

### AC-CH-05 — Snapshot, replay and live handoff

```gherkin
Given a Run streams text, tool, HITL and Job events while the network disconnects
When the browser loads a snapshot and reconnects with its last valid Session cursor
Then durable events after the snapshot are applied once in order
And live deltas do not duplicate completed parts or announcements
And the same Run, HITL and Job identities remain attached
And no model, tool or Provider call is retried because of the browser disconnect
```

### AC-CH-06 — Cursor expiry recovery

```gherkin
Given a cursor is expired, malformed, tampered or belongs to another Session
When reconnect is attempted
Then Session does not return a misleading empty stream or cross-Session event
And Web repairs from a fresh authorized snapshot
And the repair does not alter any GA, Job, Artifact or Credit fact
```

### AC-CH-07 — Stop and cancel object semantics

```gherkin
Given one launch is waiting before GA acceptance, one GA Run is running and one detached Job is active
When the user invokes the available cancel or Stop controls
Then cancel-launch affects only the pre-GA projection and reserved authorization
And Stop sends one expected-version GA cancel request and remains stopping until GA terminal
And the detached Job follows its own cancel policy rather than being silently killed
And committed Credit is released or captured only from authoritative outcome and usage facts
```

### AC-CH-08 — Branch-preserving edit and regenerate

```gherkin
Given a branch contains user text, tool calls, an Approval, a Job, an Artifact and settled Usage
When the user edits the trigger or regenerates the answer
Then a new immutable branch and new Run are created
And every object and cost on the original branch remains navigable and unchanged
And switching active leaf changes only the read view
```

### AC-CH-09 — HITL idempotency, expiry and reauth

```gherkin
Given a high-risk tool request requires step-up authentication and later expires
When the user reauthenticates, submits a decision twice and the control response is lost
Then reauthentication returns to the same request but does not approve it
And the same decision identity is applied at most once
And an expired action digest never executes or becomes valid again
And the user can query a durable decision receipt and recovery action
```

### AC-CH-10 — Unknown outcome blocks retry

```gherkin
Given a model, capability or Job effect was submitted but its outcome is unknown
When the user opens the error actions or a client repeats the command
Then Retry and automatic fallback are unavailable
And the same attempt is queried and reconciled until its published deadline
And Support receives safe correlation references without secrets or cross-Site data
```

### AC-CH-11 — Cost state is independent

```gherkin
Given a Run completes while canonical usage ingestion or rating is unavailable
When the final assistant part is displayed
Then the result is usable and execution is completed with cost_pending
And the committed Hold is not released by a generic timeout
And later settlement updates the same cost part without changing Run or Artifact terminal state
```

### AC-CH-12 — Attached and detached media Job

```gherkin
Given one attached and one detached media Job are created by Chat tools
When the Run is stopped and the browser closes
Then each Job follows its frozen attachment and cancel policy
And the detached Job continues without the Session connection
And any completed ArtifactVersion appears once with Job and Attempt provenance
And callback replay does not duplicate Artifact or charge
```

### AC-CH-13 — Mobile and accessible complete process

```gherkin
Given keyboard, screen-reader, magnification, speech or mobile users execute every Chat state and recovery path
When they compose, stream, navigate branches, approve, reconnect, Stop, Continue and open Job/Artifact cards
Then the complete process satisfies every applicable WCAG 2.2 A and AA criterion
And focus, reading anchor and composer draft remain stable
And an accessible non-virtualized transcript exposes every permitted part, state, cost and recovery action
```

### AC-CH-14 — Cross-Site and stale-client negative matrix

```gherkin
Given Site A and Site B have independent Sessions, cookies, ModelOptions and releases
When hosts, cookies, Session IDs, cursors, release IDs, option refs or command receipts are crossed
Then all protected reads and mutations fail closed without revealing existence
And no Session, GA namespace, Model authorization, Job, Artifact or Credit fact crosses Site scope
```

### AC-CH-15 — Projection crash and replay chaos

```gherkin
Given Session crashes after durable event receipt but before part projection, live publish or terminal cleanup
When the projection worker restarts and events are duplicated, delayed or reordered
Then MessagePart and RunView converge to the authoritative facts
And active-run admission is eventually cleared only after terminal convergence
And no Provider effect, HITL decision, Artifact or Credit capture is duplicated
```

### AC-CH-16 — GA semantic preservation gate

```gherkin
Given the new Session, Model Gateway adapter or stream contract is compared with the approved GA runtime corpus
When graph execution, tool calls, HITL, checkpoint recovery, effect claims, handoff/persona behavior, cancel and terminal are exercised
Then no semantic difference is introduced by PRD-05 implementation
And any required difference stops implementation and enters the explicit user approval gate
```

### AC-CH-17 — Plan acceptance is not blanket approval

```gherkin
Given a PlanProposal lists steps, budget, Capability use and a future high-risk tool action
When the user accepts the exact proposal revision and the owner begins execution
Then the accepted decision is routed idempotently to the proposal owner
And a changed plan revision requires a new decision
And every later action classified ask still creates its own scoped ApprovalRequest
And Session neither owns the proposal lifecycle nor converts acceptance into persistent permission
```

## 13. Negative、Property and Chaos Test Catalog

### 13.1 Static and contract

- Web forbidden imports/direct calls：GA、Provider SDK、Platform DB、Session store、Credit repository。
- Session forbidden imports/ownership：Model Control routing、Provider adapter、Credit Journal/capture、Capability Hub DB、
  Job worker、Artifact store、GA graph/checkpoint internals。
- GA wire negative schema：Site/User/Owner/Workspace/Plan/Price/Provider secret 字段为 0；namespace 只能 opaque。
- generated TS/Python schemas 对 MessagePart、Run fact、control、cursor、unknown version 双向兼容且零漂移。

### 13.2 Property and concurrency

- 任意 submit crash/retry schedule 下 `(commandKey,digest)` 只关联一个 Message/launch receipt。
- 任意 branch edit/regenerate/switch 序列下历史 DAG 无 cycle、无 orphan、旧 provenance不变。
- 任意 event duplicate/reorder/gap 下 part version、RunView terminal 和 cost projection 单调收敛。
- 任意 control duplicate/version conflict 下 decision/effect at-most-once；过期 decision 永不生效。
- 任意 AttemptUsage duplicate/correction 下客户 capture 不重复，root Hold allocation 不超 reservation。

### 13.3 Failure and chaos

- Web refresh/offline/多 Tab、Session API/SSE/projection worker restart、GA worker lease reclaim、Redis transport中断、
  PostgreSQL/Mongo failover、outbox publish failure、DLQ replay。
- crash points：Message 前/后、Admission prepare/finalize 前/后、GA launch intent/receipt 前/后、首 token前/后、
  tool effect claim 前/后、HITL decision persist/publish/apply 前/后、terminal persist/project 前/后。
- Job/Model callback duplicate、out-of-order、late success、cancel timeout、unknown→reconciled/irreconcilable。
- SiteRelease current/candidate/rollback与 active Run、旧 tab、revocation epoch 交错。
- a11y/locale：SSR hydration bundle切换、RTL、IME、200% zoom/400% reflow、virtualization、live-region reconnect、
  HITL expiry与 focus replacement。

任何 chaos case 的通过条件不仅是进程存活，还包括：Run/Message/Part/Effect/Job/Artifact/Hold/Usage 唯一性、用户
可解释 terminal、projection 可重建、无跨 Site 泄漏、无不可恢复 pending。

## 14. Analytics and Telemetry

Required product events：onboarding viewed/example selected、Session created/renamed/archived/trashed/restored、draft
submitted/blocked、submit receipt recovered、stream connected/reconnected/replay-expired/repaired、Run state changed、
Stop/Cancel/Continue/Retry/Regenerate、branch switched、HITL shown/extended/decided/expired/reauth、Job/Artifact card state、
cost state changed、Support opened。

Telemetry 规则：

- event identity 与 aggregate refs 幂等；analytics failure 不改变 Chat/Run/Job终态。
- 禁止 prompt/output全文、tool args、attachment filename、raw URL、secret、Code、email、userId、high-cardinality error
  进入 metrics label。
- P0 failure/unknown/reconciliation/security trace按冻结 retention采集；普通 success可采样但不得破坏metric denominator。
- 每个漏斗明确 exclusion：用户主动放弃、policy deny、Provider external failure分别记录，不从成功率中静默删除。

## 15. Dependencies、Risks and Mitigations

| Dependency/Risk | Impact | Mitigation |
|---|---|---|
| PRD-00 Profile/Inventory 未冻结 | Chat enablement无法认证 | Profile compile必须引用CH revision、owner和evidence |
| Wave 1 SiteContext/Auth/Restriction 未落地 | 跨Site与控制授权不可靠 | Chat implementation依赖其production-ready contract |
| PRD-03 Credit/Usage未落地 | cost/Hold语义可能回退Session billing | 禁止旧billing path作为目标；Wave 2A先冻结contract |
| Model Gateway logical call/stream attach语义未通过spike | 重连可能重复model call或改GA checkpoint | Phase A只做保持语义的外围adapter；命中专项批准门即停止 |
| PRD-06 Asset安全未完成 | attachment可成为执行绕过 | core launch只允许已认证ready Asset；否则关闭attachment |
| Job/Artifact未生产化 | CH-09无法完整 | 对core profile可按Inventory关闭media Job；不能用fake card |
| Stream delta被当durable | 断线丢内容/重复播报 | durable complete/terminal收口，delta best effort，snapshot repair |
| Stop/Cancel文案混淆 | 用户误以为副作用/收费撤销 | 对象化control与authoritative terminal/cost双状态 |
| Branch与current config漂移 | 重跑得到不可解释结果 | 历史snapshot+新Admission；不静默替换revoked ref |
| Session投影成为第二Run真源 | terminal分叉 | GA lookup/outbox repair；Session禁止自判terminal |
| a11y动态UI回归 | Core用户无法完成 | PRD-14完整流程硬门+真实AT/browser evidence |

## 16. Milestones and Exit Gates

1. Product review：Chat Product、Web、Accessibility、Trust、Support确认CH-01…09、state/recovery/copy semantics。
2. Architecture review：Session、GA、Model、Usage、Job/Artifact、SRE确认owner、RPC/event、idempotency与unknown。
3. Contract spike：证明GA外围Model adapter的logical call identity、stream/tool/HITL/cancel/terminal语义不变；失败即进入
   用户专项批准，不继续实现。
4. Wave 3 child Spec：冻结Session PostgreSQL schema、branch/part/projection、HTTP/SSE/control contract与clean cut。
5. Wave 5A child Spec：冻结Gateway adapter、Attempt journal、Usage evidence和GA外围cutover。
6. Wave 4 child Spec：冻结Chat Job/Artifact card与Operation finalization；未启用时四层fail closed。
7. RC：两个独立Site browser E2E、negative matrix、property/chaos/load/a11y/i18n/Support UAT与Release Evidence通过。

PRD-05 退出要求：全部 P0/P1 review finding关闭；每条 FR/AC映射 contract/test/evidence owner；Core profile不存在stub/
mock入口；所有 enabled Chat状态均有恢复与运营闭环。本文内部批准仍不授权实现，必须等待用户批准总方案、本文与
对应architecture child Spec后再生成implementation plan。

## 17. 需用户专项批准（当前均未授权）

以下任何发现必须停止相关实现、提交独立语义提案并得到用户明确批准：

1. 为稳定 `logicalModelCallId`、Run launch identity或stream replay而修改GA checkpoint schema/state keys。
2. 修改GA RunLedger、dispatch、lease/runEpoch、terminal claim、terminal event kind/order或cancel安全边界。
3. 修改graph/assembly/swarm、Agent/Prompt/Tool/Skill/MCP装配、subagent继承或Persona/Handoff语义。
4. 修改effect claim/tool journal/unknown recovery，或允许未知外部副作用自动retry。
5. 要求GA保存浏览器ack cursor、Session projection字段、Site/User/Workspace/Plan或第二身份轴。
6. 将Stop从当前批准的轮边界best-effort提升为强制中断在飞model/tool，或改变late delta/usage处理。
7. 为运行中steer、多active Run或跨branch并发而改变GA input/checkpoint/ordering语义。
8. Gateway adapter导致streaming、reasoning、tool-call ID/ordering、structured output、HITL、usage或terminal行为变化。

PRD-05 的产品目标不要求上述改变。若目标可通过Session投影、Platform Admission、Gateway外围adapter、Job/Artifact
owner contract完成，则继续保持GA核心不变。

## 18. Related Documents

- [产品需求治理、Launch Profile 与 PRD Registry](2026-07-25-product-requirements-governance-and-prd-registry-design.md)
- [PRD-00 Launch Profile 与 Journey Contract](2026-07-25-prd-00-launch-profile-and-journey-contract.md)
- [Platform、Web、Session 目标架构](2026-07-25-platform-web-session-target-architecture-design.md)
- [Model Control、Model Gateway 与 LiteLLM 目标架构](2026-07-25-model-control-gateway-litellm-architecture-design.md)
- [PRD-06 Asset Intake 与 Attachment Safety](2026-07-25-prd-06-asset-intake-and-attachment-safety.md)
- [PRD-14 Localization 与 Accessibility](2026-07-25-prd-14-localization-and-accessibility.md)
- [PRD-15 Notification、Preferences 与 Data Rights](2026-07-25-prd-15-notification-preferences-and-data-rights.md)
- [PRD-16 Trust、Content Safety 与 Media Rights](2026-07-25-prd-16-trust-content-safety-and-media-rights.md)
- [当前 Agent / Session / Web V1 Runtime](../../kokoro-handbook/technical/11-agent-session-web-v1-runtime.md)

## 19. Revision History

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-07-25 | 首稿：冻结CH-01…09、typed parts、submit/stream/control/branch/HITL/Job/Artifact/cost产品契约与GA专项批准门 |
