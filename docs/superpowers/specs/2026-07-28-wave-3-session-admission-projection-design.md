---
artifact: architecture-spec
version: "1.1"
created: 2026-07-28
revised: 2026-07-28
status: internally-approved
implementationAuthorized: true
gaRuntimeSemanticChangeAuthorized: false
wave: 3
scope: session-projection-branch-platform-admission-web-chat-site-artifact
authority:
  - docs/superpowers/specs/2026-07-25-platform-web-session-target-architecture-design.md
  - docs/superpowers/specs/2026-07-25-prd-05-chat-conversation-run-and-interaction.md
  - docs/superpowers/specs/2026-07-25-prd-06-asset-intake-and-attachment-safety.md
  - docs/superpowers/specs/2026-07-25-session-http-sse-production-transport-design.md
  - docs/superpowers/specs/2026-07-25-asset-artifact-ownership-promotion-gc-design.md
  - docs/superpowers/specs/2026-07-25-prd-12-site-lifecycle-and-fleet.md
  - docs/superpowers/specs/2026-07-25-execution-budget-allocation-protocol-design.md
program: docs/superpowers/plans/2026-07-25-kokoro-production-delivery-program.md
---

# Wave 3：Session Admission、Projection 与独立 Site Web

## 1. 裁决与完成定义

Wave 3 把 General Chat 从“浏览器重放事件 + Session 自行拼商业配置”的当前实现，切成：

```text
independent Site Web artifact
  → trusted Site BFF + SessionAccessGrant
  → complete Session snapshot + resumable SSE delta
  → Platform PrepareRun + FinalizeRunAuthorization
  → Session durable run_dispatch_outbox
  → unchanged GA run.request / run.cancel / RunExecution
```

本 Wave 完成时必须同时成立：

1. Session 只拥有对话、分支、投影、发起过程和控制 outbox；不再解析 Site、套餐、Credit、Capability、
   Provider 或客户价格。
2. Platform Admission 是唯一 Run 准入、ExecutionManifest、root Hold/AuthorizationSegment 与命令 receipt 真源。
3. GA 仍是 `RunExecution`、checkpoint、effect、epoch 与 terminal outcome 唯一真源；本 Wave 对
   `kokoro-agent` 代码、wire 和业务语义零修改，不新增 Launch/Authorization/digest/version 字段或 RPC。
4. owner snapshot 是完整页面投影，SSE 只是有界增量；刷新、跨设备和断线不依赖全历史 SSE 重放。
5. edit、regenerate、fork、cancel、retry 均有不可歧义的身份、receipt 与恢复路径。
6. 每个 production Site 是独立、产品命名的 Web project/artifact/deployment/rollback 单元；共享包无品牌。
7. 当前 MIME/file/delivery viewer 不得称为 Studio。MediaJob、Operation、JobAttempt、Asset upload/scan、
   ArtifactVersion/finalization 属于 Wave 4；Wave 3 只消费安全引用和展示投影。

若以上任一项只在 Web 本地 mock、Session legacy adapter 或文档声明中成立，Wave 3 不算完成。
本文件仍处于内部评审，未授权 implementation plan 或业务代码修改。

## 2. 已核实的当前事实

以下是 2026-07-28 对代码、contract、测试和各级 `INDEX.md` 的核验结论，不是目标状态：

| Surface | 当前事实 | Wave 3 判定 |
|---|---|---|
| Session auth | `src/http/auth.ts` 令 JWT `sub` 同时成为 `ownerId` 和 `namespace` | 必须删除该捷径 |
| owner snapshot | `src/http/server.ts` 故意省略 `messages`；Web 从 seq 0 回放 | 生产模型错误 |
| SSE | 数字 `Last-Event-ID`；非法值退成全量；无 heartbeat/backpressure；live 脏帧 skip | 必须替换 |
| message | `MessageRecord` 只有 `role/content/status`，无 part/parent/branch | 必须迁移 |
| concurrency | active Run 时 `start-message.ts` 自动发 `run.steer` 并返回 202 | Chat V1 禁止 |
| capability | 首消息把 `agent/skills/pinned_skills/mcp_servers` 写进 Session | 可保留意图，换成 revision refs |
| model | 每消息可选 raw `provider:name`，legacy billing 可改写 | 改为每 Turn `ModelOptionRevisionRef` |
| admission | `PlatformAdmissionPort` 声明 prepare/finalize/receipt；legacy adapter 返回 unknown/not_found | 尚无 provider |
| proto | `platform.admission.v1` 是 `contract-only`；`FinalizeRun` 被描述成终态结算 | 与目标 pre-dispatch commit 冲突 |
| billing | Session `src/billing/**` 做 hold/settle/reconcile，终态 token usage 参与结算 | 必须移出 Session |
| Hub/model | Session 直接 resolve Hub、Model catalog 与 billing availability；部分路径 fail-open | 必须移出 Session |
| storage | Mongo 中有 session/message/run/event/control/billing/delivery，无 branch/part | 切 PostgreSQL 投影模型 |
| Web state | flat messages + steps，单 activeRun；hydration 不读 owner messages | 必须重写投影 reducer |
| Web reconnect | 固定 2s 重连，数字 seq；错误 payload 终止；无 typed repair | 必须替换 |
| Web rail | 服务端只列 title；搜索是客户端子串；无 archive/pin/folder | 必须补服务端真源 |
| Web BFF | 密封 cookie 内含 runtime JWT/site/namespace；代理直接注入 Bearer | 换 workload exchange/grant |
| Site binding | `site.ts` 按 Host resolve，缺配置或 auth 路径可退 `KOKORO_SITE_ID` | production 禁止 |
| user app | 单一 `apps/user` 是通用能力源，不是一 Site 一独立产物 | 拆共享包与 thin app |
| admin app | 无 DB；真实 RPC 仅 AdminAuth；其余是 manifest 驱动资源表 | 不虚称 Admission provider |
| artifact UI | Session `/artifacts` 实为 contentHash/delivery/workspace reader | 不是 Artifact/Studio |

当前 `session-browser` contract 的 Session/Web Zod mirrors 字节一致，这是可保留的 codegen 门；其 schema
语义需破坏性升级。`platform-admission` registry 虽有 machine-readable proto，却仍是 `contract-only`，provider
还误登记为 `platform.admin`；生成到 Admin Web 的 `admission_pb.ts` 也只证明 codegen，不证明服务存在。

## 3. 范围与依赖边界

### 3.1 本 Wave 交付

- Session PostgreSQL 写模型、完整 snapshot、typed parts、Branch、RunLaunchProjection、RunView。
- Platform Admission Connect RPC 的真实 provider/client、幂等命令 receipt 与对账 worker。
- SessionAccessGrant 鉴权、跨 Site/Project/subject-generation 隔离。
- Web Chat projection、SSE 恢复、分支操作、可靠 cancel、服务端会话管理与费用投影。
- Site bootstrap 与“一 Site 一独立 Web artifact”的 build/release contract。
- attachment 引用的准入接口；不实现对象上传、扫描器、Blob/Asset/Artifact 写模型。

### 3.2 明确不做

- 不改 GA graph、checkpoint、handoff、tool-effect、terminal event 或 Provider 语义。
- 不实现 Media `Operation/Job/JobAttempt/MediaJob`、专业 Studio、Artifact Library、compare/export/share。
- 不让 Session 存 object-store credential、presigned URL、scanner evidence 或 Artifact binary。
- 不把当前 file/delivery/MIME preview 改名成 ArtifactVersion 或 Studio。
- 不做 Admin 的 Session mutation；Support/Admin 命令属于后续运营 Wave。
- 不保留新旧 production dual-write、namespace=owner、Host→Site 或全历史 SSE fallback。

Wave 3 可以渲染 `job`/`artifact` part 的稳定占位和外部引用，但只有 Wave 4 owner 发布事实后才能出现
ready/preview/download 能力。未启用 Wave 4 的 Site bootstrap 必须隐藏 Studio、Library 与上传入口。

## 4. 领域术语与唯一 owner

### 4.1 Conversation、Turn、Branch、Run

| 术语 | 冻结语义 | 持久化与 owner |
|---|---|---|
| Conversation | 用户产品术语；与一个 `Session` 一一对应，不是第二个 aggregate | Session；API 仍用 `sessionId` |
| Message | 一次不可变的 user/assistant/system expression | Session |
| MessagePart | Message 内有序、typed、可版本化投影单元 | Session projection |
| Turn | 一个 trigger user Message、其 Run 引用与 assistant Message 的读模型分组 | 派生，不建可写 aggregate |
| ConversationBranch | 从 parent Message 到 active leaf 的追加历史 | Session |
| RunLaunchProjection | dispatch 与首个 GA durable event 观察前的恢复对象 | Session |
| Run | 一次真实 Agent 图执行 | GA `RunExecution` |
| RunView | GA/Platform 事实在 Chat 中的可重建展示投影 | Session projection |

`conversationId == sessionId`。Web 可以显示“对话”，contract、日志和 owner 不再创建第二个 Conversation ID。
`TurnRef = {branchId, triggerMessageId, runId?}`，仅供渲染、analytics 和 command targeting。

### 4.2 Project 与能力事实

- `Project` 归 Platform workspace；Session 只保存 opaque `ProjectRef`。
- `SiteContext`、actor、membership、entitlement 与 current epochs 归 Platform。
- AgentRevision、SkillRevision、MCP server/tool schema、Connection grant 归 Capability Control Plane。
- ModelOptionRevision/RoutePolicy/RatingSnapshot 归 Platform Model/Admission。
- Session 只保存被 Admission 签名、可安全展示的 revision refs/snapshots；不缓存 secret 或可自行授权的 token。
- Usage/Rating/Settlement/CreditJournal 归 Platform；Session 只保存 cost projection refs。

## 5. Session 数据模型

Wave 3 的权威存储为 PostgreSQL。下面是 migration 必须表达的 DDL 级约束；实现可调整命名，不能弱化键、
scope、FK、fence 或 RLS。

### 5.1 核心表

```sql
session(
  site_id, session_id, project_ref, created_by_subject_ref,
  subject_generation_at_create, title,
  lifecycle CHECK IN ('active','archived','trashed'),
  active_branch_id NULL, active_leaf_message_id NULL,
  version CHECK (version > 0), created_at, updated_at, archived_at NULL, trashed_at NULL,
  PRIMARY KEY(site_id, session_id)
)

conversation_branch(
  site_id, session_id, branch_id, parent_branch_id NULL,
  forked_from_message_id NULL, root_message_id NULL, leaf_message_id NULL,
  origin CHECK IN ('original','edit','regenerate','fork'),
  created_by_subject_ref, version CHECK (version > 0), created_at,
  PRIMARY KEY(site_id, session_id, branch_id),
  FOREIGN KEY(site_id,session_id) REFERENCES session(site_id,session_id) ON DELETE RESTRICT,
  FOREIGN KEY(site_id,session_id,parent_branch_id)
    REFERENCES conversation_branch(site_id,session_id,branch_id) DEFERRABLE,
  CHECK ((root_message_id IS NULL) = (leaf_message_id IS NULL))
)

message(
  site_id, session_id, message_id, branch_id, parent_message_id NULL,
  role CHECK IN ('user','assistant','system'), ordinal CHECK (ordinal >= 0),
  trigger_message_id NULL, run_id NULL,
  lifecycle CHECK IN ('created','streaming','completed','partial','failed','canceled'),
  created_by_subject_ref, created_at,
  PRIMARY KEY(site_id,session_id,message_id),
  UNIQUE(site_id,session_id,branch_id,ordinal),
  FOREIGN KEY(site_id,session_id,branch_id)
    REFERENCES conversation_branch(site_id,session_id,branch_id) ON DELETE RESTRICT,
  FOREIGN KEY(site_id,session_id,parent_message_id)
    REFERENCES message(site_id,session_id,message_id) DEFERRABLE
)

message_part(
  site_id, session_id, message_id, part_id, ordinal CHECK (ordinal >= 0),
  kind, schema_version CHECK (schema_version > 0),
  lifecycle CHECK IN ('created','streaming','completed','partial','failed','canceled','unsupported'),
  payload_json, safe_display_json, version CHECK (version > 0), created_at, completed_at NULL,
  PRIMARY KEY(site_id,session_id,message_id,part_id),
  UNIQUE(site_id,session_id,message_id,ordinal),
  FOREIGN KEY(site_id,session_id,message_id)
    REFERENCES message(site_id,session_id,message_id) ON DELETE RESTRICT
)

message_attachment_ref(
  site_id, session_id, message_id, ordinal CHECK (ordinal >= 0),
  asset_ref, asset_version_ref, asset_grant_ref,
  readiness_snapshot, media_type, display_name, size_bytes CHECK (size_bytes >= 0), attached_at,
  PRIMARY KEY(site_id,session_id,message_id,ordinal),
  UNIQUE(site_id,asset_grant_ref,message_id),
  FOREIGN KEY(site_id,session_id,message_id)
    REFERENCES message(site_id,session_id,message_id) ON DELETE RESTRICT
)
```

`session.active_*`、Branch root/leaf 与其 Message 的 site/session 一致性用 deferrable composite FK 或同事务
constraint trigger 强制。空 Session 的 initial Branch 允许 root/leaf 同时为 NULL；非空 Branch 两者必须同时存在。
硬删除只由 retention/data-rights purge procedure 按依赖顺序执行，普通业务角色没有 cascade delete。

MessagePart 合法转移为 `created→streaming→completed|partial|failed|canceled` 或 `created→completed`；无法解释的
kind/version 投影成 terminal `unsupported`。只有 `streaming` assistant part 可按 expected part version patch；任何
terminal part 不原地改写，修正必须追加 revision/event。用户 edit 永远创建新 Message。

### 5.2 发起、执行与控制表

```sql
session_runtime_binding(
  site_id, session_id, platform_binding_ref, ga_namespace_ciphertext,
  capability_snapshot_ref, configuration_revision_id, safe_display_json, binding_digest,
  PRIMARY KEY(site_id,session_id), UNIQUE(site_id,platform_binding_ref),
  FOREIGN KEY(site_id,session_id) REFERENCES session(site_id,session_id) ON DELETE RESTRICT
)

run_launch_projection(
  site_id, session_id, launch_id, branch_id, trigger_message_id, proposed_run_id,
  submit_command_id, submit_request_digest,
  admission_receipt_ref NULL, manifest_ref NULL, manifest_digest NULL,
  authorization_segment_ref NULL, finalize_receipt_ref NULL,
  state, version CHECK (version > 0), failure_code NULL, created_at, updated_at,
  PRIMARY KEY(site_id,session_id,launch_id),
  UNIQUE(site_id,session_id,proposed_run_id),
  UNIQUE(site_id,session_id,submit_command_id),
  FOREIGN KEY(site_id,session_id,trigger_message_id)
    REFERENCES message(site_id,session_id,message_id) ON DELETE RESTRICT
)

run_view(
  site_id, session_id, run_id, launch_id, branch_id, assistant_message_id,
  projection_version CHECK (projection_version > 0), execution_status, cost_status,
  terminal_outcome NULL, terminal_at NULL, last_durable_seq CHECK (last_durable_seq >= 0),
  PRIMARY KEY(site_id,session_id,run_id), UNIQUE(site_id,session_id,launch_id),
  FOREIGN KEY(site_id,session_id,launch_id)
    REFERENCES run_launch_projection(site_id,session_id,launch_id) ON DELETE RESTRICT
)

platform_admission_outbox(
  site_id, session_id, outbox_id, launch_id, operation, command_id, request_digest,
  payload_json, state CHECK IN ('pending','leased','sent','receipt_pending','applied','dead'),
  attempt_count, next_attempt_at, lease_owner NULL, lease_until NULL,
  PRIMARY KEY(site_id,session_id,outbox_id),
  UNIQUE(site_id,operation,command_id),
  FOREIGN KEY(site_id,session_id,launch_id)
    REFERENCES run_launch_projection(site_id,session_id,launch_id) ON DELETE RESTRICT
)

run_dispatch_outbox(
  site_id, session_id, dispatch_id, launch_id, run_id,
  launch_version_fence, authorization_segment_ref, finalize_receipt_ref,
  payload_json, payload_sha256,
  state CHECK IN ('pending','leased','published','event_observed','dispatch_unknown','dead'), transport_message_id NULL,
  attempt_count, next_attempt_at, lease_owner NULL, lease_until NULL,
  PRIMARY KEY(site_id,session_id,dispatch_id),
  UNIQUE(site_id,session_id,launch_id), UNIQUE(site_id,session_id,run_id),
  CHECK (length(payload_sha256)=64),
  FOREIGN KEY(site_id,session_id,launch_id)
    REFERENCES run_launch_projection(site_id,session_id,launch_id) ON DELETE RESTRICT
)

control_outbox(
  site_id, session_id, decision_id, run_id, kind CHECK IN ('run.cancel','run.resume'),
  run_view_version_fence, request_digest, payload_json, state,
  attempt_count, next_attempt_at, transport_message_id NULL,
  PRIMARY KEY(site_id,session_id,decision_id),
  UNIQUE(site_id,session_id,run_id,kind,request_digest),
  FOREIGN KEY(site_id,session_id,run_id)
    REFERENCES run_view(site_id,session_id,run_id) ON DELETE RESTRICT
)
```

`run_dispatch_outbox.payload_json` 必须逐字段符合现有 `contract/spec/control.yaml` 的 `run.request`，只含现有
`run_id/thread_id/input/runtime/context/trace`。authorization ref、digest 与 fence 只存在 Session 表中，绝不发给 GA。
dispatcher claim 时 CAS `launch_version_fence` 且重验 segment=committed；同 run 只允许一个 immutable payload digest。
Redis XADD 后 crash 可以重发完全相同 payload；GA 现有 RunLedger 以 run_id keep-first，Session 本地 unique/digest
防止同 run 异 payload。第一个 GA durable event 才把 launch 投影为 `event_observed`；XADD 成功不等于 Run 真相。

### 5.3 流、幂等与用户组织表

```sql
session_event(
  site_id, session_id, stream_epoch, durable_seq, event_id, aggregate_version,
  schema_version, kind, payload_json, recorded_at,
  PRIMARY KEY(site_id,session_id,stream_epoch,durable_seq),
  UNIQUE(site_id,event_id), CHECK (durable_seq > 0 AND aggregate_version > 0)
)
agent_event_inbox(
  producer, event_id, payload_sha256, site_id, session_id, run_id, received_at, applied_at NULL,
  PRIMARY KEY(producer,event_id), CHECK (length(payload_sha256)=64)
)
projection_checkpoint(
  consumer, partition_key, stream_epoch, durable_seq, updated_at,
  PRIMARY KEY(consumer,partition_key), CHECK (durable_seq >= 0)
)
projection_dlq(
  dlq_id, consumer, producer, event_id, payload_sha256, schema_version,
  quarantine_payload_ref, safe_error_code, retry_state, first_seen_at, last_seen_at,
  PRIMARY KEY(dlq_id), UNIQUE(consumer,producer,event_id,schema_version)
)
command_receipt(
  site_id, session_id, subject_ref, subject_generation, operation, command_id,
  request_digest, status, result_json, owner_receipt_ref NULL, created_at, updated_at,
  PRIMARY KEY(site_id,session_id,subject_ref,operation,command_id),
  CHECK (length(request_digest)=64),
  FOREIGN KEY(site_id,session_id) REFERENCES session(site_id,session_id) ON DELETE RESTRICT
)
session_access_acl_projection(
  site_id, session_id, subject_ref, subject_generation, project_ref, scopes, expires_at,
  PRIMARY KEY(site_id,session_id,subject_ref)
)
session_folder(site_id,project_ref,owner_subject_ref,folder_id,name,version,created_at,updated_at,
  PRIMARY KEY(site_id,owner_subject_ref,folder_id), UNIQUE(site_id,owner_subject_ref,project_ref,name))
session_user_preference(site_id,session_id,subject_ref,pinned,folder_id NULL,version,updated_at,
  PRIMARY KEY(site_id,session_id,subject_ref))
```

同 `(producer,eventId)` 异 digest 不覆盖 Inbox，直接 DLQ + security alert。checkpoint 与投影写在同一 DB transaction；
DLQ 未处置时不得推进越过该 durable seq。outbox 均使用 `FOR UPDATE SKIP LOCKED`/lease、attempt cap 与显式 dead 状态，
但 dead 不等于业务失败，reconciler 仍以 receipt/owner fact 收口。

所有 tenant 表启用并强制 RLS。每事务只在 SessionAccessGrant 验证后设置 `app.site_id/app.subject_ref/
app.subject_generation`；policy 通过 `session_access_acl_projection` 校验 scope/project。应用 role 不得 `BYPASSRLS`，
migration/recovery role 独立审计。所有 FK 带 site_id；禁止依赖 Web 过滤或只按裸 ID 查询。

Archive/Trash 是 Session aggregate 状态；pin/folder 是 actor 级组织偏好，不改变共享 Session 历史。
所有列表/search query 必须同时约束 `siteId + projectRef + actor authorization`，不能先查再在 Web 过滤。

## 6. Typed MessagePart contract

首批 kind 固定为：

```text
text | reasoning | citation | tool-call | approval | interaction |
plan | job | artifact | cost | notice | error
```

每个 part envelope 都含：

```text
partId, messageId, ordinal, kind, schemaVersion, lifecycle, version, payload
```

`lifecycle` 仅为 `created|streaming|completed|partial|failed|canceled|unsupported`，转移与 §5 DDL 一致；
不得再使用 `open/complete` 或把 Run lifecycle 填进 part。

约束如下：

- `text`：结构化 text spans；不得承载 HTML。
- `reasoning`：只允许 owner 明确发布的 safe summary；不得泄漏 hidden chain-of-thought。
- `citation`：`sourceRef/title/locator/attribution`，下载需另取授权 grant。
- `tool-call`：安全 tool label、input summary、status、effect/receipt refs；不含 secret/raw credential。
- `approval` / `interaction`：ownerRef、expectedVersion、deadline、allowed actions、receipt/status。
- `plan`：`PlanProposalRef` 与只读 steps；接受/拒绝按真实 ownerRef 路由。
- `job` / `artifact`：仅 opaque refs、safe metadata 与 owner status；Wave 3 不写其真源。
- `cost`：Platform cost projection ref、amount/currency/credit unit、freshness 和 cost status。
- `notice` / `error`：stable code、用户安全文案、retry class、support correlation ref。

attachment 不伪造成 Artifact part。用户 Message 通过有序 `message_attachment_ref` 关联 AssetVersion；可在 UI
显示 attachment chip。未知 `kind` 或 `schemaVersion` 必须渲染 `unsupported part` 卡并保留 ordinal，不能丢消息、
猜字段或继续错误 apply patch。

## 7. Attachment admission，仅 owner interface

Wave 3 只定义和消费：

```text
ResolveAttachmentEligibility(
  SessionAccessGrant,
  projectRef,
  refs[{assetRef, assetVersionRef, assetGrantRef}],
  purpose=chat_run_input
)
→ eligible[{assetVersionRef, immutableVersionDigest, mediaType,
            readiness=ready, policyDecisionRef, expiresAt}]
  | denied[{ref, reasonCode}]
```

该接口及 `AssetGrant` 的签发/撤销 owner 是 Platform Policy/Admission；它消费 Media Resource 的版本化 scan、
promotion、rights evidence 后签发 audience/purpose/epoch 有界的 grant。Wave 4 Media Resource 不签 AssetGrant。
`PrepareRun` 必须再次在 Platform effect point 校验 refs，并把不可变 digest/policy refs 写入 manifest。任一输入
处于 uploading/scanning/quarantined/revoked/deleted/expired，Run 保持 `waiting_prerequisite` 或拒绝；绝不 dispatch。

对象存储 direct upload、multipart、scan、quarantine、finalize、promotion evidence、retention/GC 的 owner interface
由 Wave 4 Media Resource 实现。Wave 3 Web 只接受 Platform 返回的 ready grant/ref，不得：

```text
Media Resource owner interface（Wave 4 实现；Wave 3 仅冻结依赖）
  CreateUploadIntent → Create/ResumeUploadSession
  CompleteUploadSession → ValidateBlobCandidate → EvaluateScan
  PromoteReadyAssetVersion → PublishReadyAssetEvidence
  GetUpload/Scan/PromotionCommandReceipt
```

这些命令的 byte/object key、checksum、scanner evidence、promotion receipt 与 GC disposition 都留在 Media
Resource；Session contract 只看 `AssetVersionRef + AssetGrantRef + safe readiness`。

- 经 Session 上传或转发 bytes；
- 保存 presigned URL 为长期引用；
- 把 MIME sniff 结果当 Trust 决策；
- 用 contentHash 充当 Asset/Artifact identity；
- 在 owner 未上线时提供“假上传成功”。

## 8. Session-locked capability 与 per-Turn model

### 8.1 CapabilitySnapshot

空 Session 不预造 runtime 配置。Platform 在首个 `PrepareRun` 内解析并持久化 immutable
`SessionExecutionBinding/CapabilitySnapshot`，Session 只保存其 opaque ref、现有 GA wire 所需的 resolved runtime
副本和 safe display：

```text
capabilitySnapshotId
agentRevisionRef
skillRevisionRefs[]
mcpBindings[{serverRevisionRef, toolSchemaDigest, connectionGrantRef}]
configurationRevisionId
restrictionEpochAtLock
safeDisplaySnapshot
```

Agent、Skills 与 MCP bindings 对整个 Session 锁定；之后不得就地替换。用户要换 Agent/Skills/MCP 时创建新
Session，或显式 fork 到新 Session 并产生新的 snapshot。active branch 切换不改变锁定值。
后续 `PrepareRun` 只提交 `sessionId`，Platform 读取自己拥有的 binding；Session 不把 capability ref 或 namespace
作为授权输入回传。首 Turn 可提交用户意图 `requestedAgentOptionRef/requestedSkillOptionRefs/requestedMcpOptionRefs`，
Platform 可以拒绝或收窄，最终只有响应中锁定的 binding 生效。

历史 snapshot 保存名称、版本、内容/schema digest、来源和已撤销/不可用展示状态；不保存 secret、access token、
provider credential 或可执行 package bytes。实时 revocation 可以阻止未来 effect，但不改写历史显示。

### 8.2 ModelSelectionSnapshot

Model 是每 Turn 选择：

```text
modelOptionRevisionRef
userVisibleLabelSnapshot
effort/thinking selection
routePolicyRef (Platform-filled)
ratingSnapshotRef (Platform-filled)
```

浏览器只提交当前 Site bootstrap 允许的 `ModelOptionRevisionRef`，不得提交 provider/model raw name。Platform
Admission fail-closed 地验证可用性；未知、禁用、越权或撤销返回 typed denial，不得静默回默认。Session 只保存
用户选择和 Admission 回执；GA 只收到签名 manifest 中的 runtime route，不从 Session legacy billing 改写。

跨设备 snapshot 必须含 capability/model 的历史 safe display snapshot，因此旧对话在 catalog 变化后仍可读；
新 Turn 仍按当前 epoch 重验 entitlement、connection 与 model availability。

## 9. Platform Admission contract

### 9.1 更正现有 proto

根 `contract/proto/kokoro/platform/admission/v1/admission.proto` 必须先做显式 breaking migration：

- operations 固定为 `PrepareRun`、`FinalizeRunAuthorization`、`ReleaseRunAuthorization`、
  `ReconcileRunAuthorization`、`GetCommandReceipt`。
- `FinalizeRunAuthorization` 取代当前“记录 Run 如何结束”的 `FinalizeRun`；它是 dispatch 前
  `reserved→committed` CAS，不是 terminal settlement。
- provider boundary 改为 Platform Admission application service，不是 `platform.admin`。
- registry lifecycle 只有在真实 provider、Session client 与 compatibility scenario 通过后才从 `contract-only`
  变 `active`。

不得在相同 RPC 名下悄悄反转 `FinalizeRun` 语义。若 v1 已被任何外部 pin 消费，应新增 admission v2；当前
contract-only 且零真实消费者时可清替 v1，并由 `buf breaking` allowlist 记录一次性原因。

### 9.2 命令

```text
PrepareRunRequest
  command{commandId,idempotencyKey,digestAlgorithm,requestDigest}
  siteId
  effect{
    sessionAccessGrant, projectRef, sessionId, launchId, proposedRunId, triggerMessageId,
    modelOptionRevisionRef, attachmentRefs[], interactionPrerequisiteRefs[],
    initialIntent?{requestedAgentOptionRef,requestedSkillOptionRefs[],requestedMcpOptionRefs[]},
    clientIntent{effort,locale}
  }

PrepareRunResponse
  outcome=accepted|denied|waiting_prerequisite|pending|outcome_unknown
  commandReceipt
  prepared{manifestRef,manifestDigest,sessionExecutionBindingRef,
           gaNamespace,runtimeConfig,capabilitySnapshotRef,configurationRevisionId,
           executionBudgetRootRef,rootHoldRef,authorizationSegmentRef,
           segmentVersion,status=reserved,expiresAt,
           safeAdmissionSnapshot}?  # accepted/waiting_prerequisite 时存在
  denial{code,retryClass,safeDetails}?

FinalizeRunAuthorizationRequest
  command{...}
  siteId
  effect{manifestRef,manifestDigest,authorizationSegmentRef,
         expectedSegmentVersion,launchId,sessionIntentReceiptRef,prerequisiteReceipts[]}

FinalizeRunAuthorizationResponse
  outcome=committed|expired|denied|pending|outcome_unknown
  commandReceipt
  committed{authorizationSegmentRef,segmentVersion,committedAt}?

ReleaseRunAuthorizationRequest
  command{...}, siteId
  effect{manifestRef,authorizationSegmentRef,expectedSegmentVersion,reasonCode,noDispatchEvidenceRef}
→ released|already_released|not_releasable|pending|outcome_unknown + commandReceipt

ReconcileRunAuthorizationRequest
  command{...}, siteId
  effect{manifestRef,authorizationSegmentRef,expectedSegmentVersion,
         sessionDispatchReceiptRef?,gaDurableEventReceiptRef?,terminalOwnerEvidenceRef?}
→ execution_observed|released_no_effect|awaiting_owner_evidence|reconciliation_required|settled + commandReceipt

GetCommandReceiptRequest
  siteId, operation, commandId, digestAlgorithm, requestDigest
```

所有 effectful request 的 siteId 是被 BFF workload exchange/Session grant 约束的 payload 字段，不接受裸 header
自我声明。Prepare 输入明确不含 namespace、CapabilitySnapshotRef、resolved RuntimeConfig、Hold 或 Segment；这些都由
Platform 解析、持久化、返回并锁定。`runtimeConfig + gaNamespace` 必须精确适配现有 `run.request`，不要求 GA 新字段。

### 9.3 Platform 数据与事务

```sql
admission_command_receipt(
  site_id, operation, command_id, request_digest, idempotency_key,
  state, effect_ref NULL, effect_version NULL, result_digest, safe_result_json,
  created_at, updated_at,
  PRIMARY KEY(site_id,operation,command_id),
  UNIQUE(site_id,operation,idempotency_key), CHECK(length(request_digest)=64)
)
platform_session_execution_binding(
  site_id,session_id,binding_id,ga_namespace,capability_snapshot_ref,
  configuration_revision_id,binding_digest,safe_display_json,created_at,
  PRIMARY KEY(site_id,session_id), UNIQUE(site_id,binding_id), UNIQUE(site_id,ga_namespace)
)
execution_manifest(
  site_id,manifest_id,session_id,launch_id,binding_id,model_option_revision_ref,
  resolved_runtime_json,attachment_policy_refs,rating_snapshot_ref,manifest_digest,created_at,
  PRIMARY KEY(site_id,manifest_id), UNIQUE(site_id,launch_id), CHECK(length(manifest_digest)=64)
)
execution_budget_root(
  site_id,execution_root_id,liability_account_ref,root_hold_ref,rating_policy_revision_ref,
  reserved_ceiling,state,version,
  PRIMARY KEY(site_id,execution_root_id), UNIQUE(site_id,root_hold_ref)
)
authorization_segment(
  site_id,segment_id,execution_root_id,manifest_id,root_hold_ref,
  status CHECK IN ('reserved','committed','rating_pending','settled','released','expired','reconciliation_required'),
  version,reserved_at,committed_at NULL,closed_at NULL,expires_at,
  PRIMARY KEY(site_id,segment_id), UNIQUE(site_id,execution_root_id,manifest_id),
  FOREIGN KEY(site_id,execution_root_id) REFERENCES execution_budget_root ON DELETE RESTRICT,
  FOREIGN KEY(site_id,manifest_id) REFERENCES execution_manifest ON DELETE RESTRICT
)
admission_domain_outbox(
  site_id,outbox_id,aggregate_type,aggregate_id,aggregate_version,event_type,payload_json,
  state,attempt_count,next_attempt_at,created_at,
  PRIMARY KEY(site_id,outbox_id), UNIQUE(site_id,aggregate_type,aggregate_id,aggregate_version,event_type)
)
```

root Hold/Grant allocations/Journal 复用 Execution Budget authority，不另造 Session 账本。`PrepareRun` 在一个 Platform
transaction 内重验 grant/project/entitlement/model/capability/AssetGrant，创建或读取 session binding，冻结 manifest，
建立一个 `(executionRoot,liabilityAccount)` root Hold、reserved Segment、receipt 与 domain outbox。余额不足则只写
denied receipt，不产生可执行 manifest/segment。

`FinalizeRunAuthorization` 在一个 transaction 内核对同 manifest/digest、prerequisite receipts、root Hold 和 expected
Segment version，CAS `reserved→committed` 并写 receipt/outbox。`Release` 只允许 reserved 且由可信 evidence 证明未
dispatch；committed 永不普通 release。`Reconcile` 只消费 owner-issued evidence，不能把 caller 的“没有执行”当事实。
所有命令同 command/digest 返回同 receipt，同 identity 异 digest 冲突；receipt lookup 按 Site+operation+identity scope，
跨 Site 返回 not-found。

### 9.4 权威状态机

```text
Admission command:
unseen → pending → accepted | denied | waiting_prerequisite
                  ↘ outcome_unknown (caller knowledge only)

AuthorizationSegment:
reserved → committed → rating_pending → settled
    │           └──────────────→ reconciliation_required → settled
    └→ released | expired

RunLaunchProjection:
draft → admission_pending → waiting_prerequisite
      → prepared → authorization_committing → dispatch_pending
      → ga_event_observed
      → rejected | canceled_before_dispatch | reconciliation_required
```

`outcome_unknown` 不是 Platform 领域终态，只是 caller 不知道结果。Session 必须用相同 command identity 查询
receipt；`not_found` 只允许 receipt lookup，并且跨 Site 一律 non-disclosing not-found。

Finalize committed 后不可因 timeout 释放。Session reconciler 以同一 launch/digest 检查本地 dispatch receipt 和 GA
现有 durable events；不能证明未执行时调用 Platform Reconcile 并保持 committed/reconciliation_required。

### 9.5 Crash matrix

| Crash/timeout 点 | 恢复与禁止项 |
|---|---|
| Prepare 进 Platform transaction 前 | 同 command/digest retry；无 receipt 即可重试 |
| Prepare commit 后、response 前 | `GetCommandReceipt(PREPARE)`；禁止第二 Hold/Segment |
| Session 保存 Prepare response 前 crash | 同 receipt 恢复 binding/manifest/segment；不重算配置 |
| prerequisite wait 超过 reserved TTL | Platform expiry/release；同 launch 以新 admission command 重新 Prepare，不复制 Session/Message |
| Finalize transaction 前 | 同 command retry；仍 reserved，不 dispatch |
| Finalize commit 后、response 前 | `GetCommandReceipt(FINALIZE)`；committed 不 TTL release |
| Session 保存 finalize 后、建 dispatch outbox 前 | receipt reconciler 原子补 `run_dispatch_outbox` |
| dispatch outbox commit 后、XADD 前 | scanner 以同 row 重试 |
| XADD 后、保存 transport id 前 | 仅重发相同 run.request；GA 现有 run_id keep-first；禁止换 payload |
| 已 XADD、首个 GA durable event 未见 | 状态 `dispatch_unknown`，查 Session transport/GA durable fact；不得 Release |
| reserved launch cancel 与 Finalize 竞态 | expected Segment/session version 只有一方胜；Finalize 胜则进入 committed reconciliation |
| Platform domain outbox publish crash | 重发相同 aggregateVersion event；consumer Inbox 去重，不重做 Hold effect |
| terminal/usage evidence 尚未上线或缺失 | Segment 保持 committed/reconciliation_required；Wave 3 不伪造 usage 或 settlement |

## 10. 发消息与分支命令

### 10.1 空 Session、initial Branch 与首发原子性

```text
POST /v1/sessions
  {projectRef,title?,commandIdentity}
→ 201 {sessionId,initialBranchId,sessionVersion,commandReceipt,snapshotWatermark}
```

CreateSession 的一个 PostgreSQL transaction 必须写 `session(version=1)`、root/leaf 均 NULL 的
`conversation_branch(origin=original)`、activeBranchId、command receipt 和 `session.created` event；它不创建
Message、runtime binding、Run、Hold 或 Admission。重复 command 同 digest 返回同空 Session。

首个与后续 Submit 使用同一 contract：

```text
POST /v1/sessions/{sessionId}/messages
Idempotency-Key: <opaque>

{
  requestDigest,
  expectedSessionVersion,
  branchId,
  parentMessageId,
  parts:[{kind:"text",schemaVersion:1,payload:{text}}],
  attachmentRefs:[],
  modelOptionRevisionRef,
  effort
}
```

首发的一个 Session transaction 必须同时：锁 session/initial branch；验证 expected version、branch 仍为空且无 active
launch；插入 immutable user Message/parts/attachment refs 与 assistant `created` placeholder；把 Branch root 指向 user、
leaf 指向 assistant，更新 Session active leaf/version；创建 `RunLaunchProjection(admission_pending)`、Submit receipt、
session events 和 `platform_admission_outbox(PREPARE)`。任一步失败整笔回滚。Platform RPC 只在 commit 后由 outbox
scanner 调用，因此不会出现 Hold 已 reserve 但首条 Message 不存在。

Prepare response 的 binding/manifest/segment 保存与 `platform_admission_outbox(FINALIZE)` 同一 Session transaction；
Finalize receipt=committed 的保存与 `run_dispatch_outbox` 同一 transaction。HTTP 可返回 202 durable intent receipt，
Web 从 snapshot/SSE 看 admission 状态，绝不以请求连接存活作为执行保证。

同 key/同 digest 返回同 receipt；同 key/异 digest 返回 `IDEMPOTENCY_CONFLICT`。一个 Session 同时最多一个
accepted/nonterminal Run。存在 active Run 时，新输入可保存为本地 Web draft，但 server Submit 返回
`ACTIVE_RUN_EXISTS`；不得自动 `run.steer`。未来 steering 需独立 PRD/命令，不借 SubmitMessage 实现。

### 10.2 Edit、Regenerate、Fork

```text
POST /v1/sessions/{id}/branches:edit-message
  {sourceMessageId,newParts,attachmentRefs,expectedSessionVersion,commandIdentity}

POST /v1/sessions/{id}/branches:regenerate
  {triggerMessageId,sourceAssistantMessageId?,modelOptionRevisionRef,
   expectedSessionVersion,commandIdentity}

POST /v1/sessions/{id}/branches:fork
  {fromMessageId,activate,expectedSessionVersion,commandIdentity}

POST /v1/sessions/{id}/branches/{branchId}:activate
  {expectedSessionVersion,commandIdentity}
```

- Edit 创建 sibling user Message、新 Branch，并在成功 admission 后启动新 Run；旧 Message 不变。
- Regenerate 复用同一 trigger user Message，创建 sibling assistant branch、新 launch/new Run。
- Fork 只创建/激活 Branch，不自动执行；后续 SubmitMessage 才创建 launch。
- 原 tool/approval/job/artifact/cost provenance 留在原 Branch。
- product retry 是 Regenerate/new Run；transport retry 只重发同 command identity。未知外部 effect 不得 regenerate
  伪装成重试，先 receipt/reconcile。

## 11. 可靠 cancel 与 receipt

取消分两个 owner：

1. dispatch 前：`CancelRunLaunch` 由 Session CAS `RunLaunchProjection`，若 segment 仅 reserved 则请求 Platform
   release；Finalize committed 后进入 reconciliation，不能自行释放。
2. GA 接受后：浏览器携 `expectedRunViewVersion`；Session 在同一 transaction 验证当前 RunView version 并只写一个
   ControlOutbox/receipt，scanner 按现有 wire 原样发送一次 `run.cancel{run_id,thread_id,decision_id}`。version fence
   不发送给 GA，也不要求 GA 理解 expectedVersion；GA event 决定最终 canceled/completed/failed。

```text
Control receipt:
accepted → forwarding → owner_persisted → applied → terminal_observed
    └────────────→ outcome_unknown → reconciled
    └────────────→ rejected | superseded
```

Web 点击 Stop 后把 RunView 展示为 `cancelling`，禁用重复 Stop，但不显示 canceled。若 completion 与 cancel
竞态，Session expected-version 只裁决“能否发出 control”；最终由 GA terminal fact 与 Session control receipt 投影
收敛，completed 可以合法胜出。重复 cancel 同 key/digest 返回同 receipt，异 digest 冲突。断线后 snapshot 必须携
control receipt 与 `cancelling` projection。

API：

```text
POST /v1/sessions/{sid}/launches/{launchId}:cancel
POST /v1/sessions/{sid}/runs/{runId}:request-cancellation
GET  /v1/sessions/{sid}/commands/{commandId}/receipt
```

## 12. 完整 snapshot 与生产 SSE

### 12.1 Snapshot

```text
GET /v1/sessions/{sessionId}/snapshot
→ session metadata/version
  authorized branches + activeLeafMessageId
  complete messages + complete/current parts
  attachment safe refs
  run launch/run/control views
  approval/interaction/plan/job/artifact/cost projections
  capability/model historical display snapshots
  snapshotWatermark{streamEpoch,durableSeq,projectionVersion}
  nextPageCursor? (仅超大历史的已声明分页边界)
```

返回体必须来自一个一致 projection boundary：所有内容均不晚于 watermark。snapshot 可以分页历史 Branch，
但首屏必须完整覆盖 active Branch 和所有 active cards；不得把 `messages` 做 optional，也不得要求从 seq 0 补齐。

### 12.2 Cursor 与连接

SSE endpoint：`GET /v1/sessions/{id}/events?after={cursor}`。客户端优先用 `Last-Event-ID` 传 opaque、签名
cursor；query 仅供 fetch/polyfill，两者同时存在但不一致返回 `CURSOR_CONFLICT`。cursor 绑定：

```text
siteId, sessionId, subjectBindingHash, subjectGeneration, audience,
streamEpoch, lastDurableSeq, snapshotRevision, schemaRevision,
issuedAt, expiresAt, signingKeyRevision, optionalGrantFamily
```

损坏为 400，跨主体/Site 使用 non-disclosing 404/403，ahead/retention/epoch 为 typed 409，schema 不兼容为
409/426；绝不回全历史。客户端按错误 action：
`retry_same_cursor | refresh_grant | refetch_snapshot | upgrade_client | stop`。

响应固定 `Cache-Control: no-store, no-transform` 并关闭 proxy buffering。服务端每 15 秒发带 jitter 的 SSE
comment heartbeat；部署的 proxy idle timeout 必须大于两倍 heartbeat，并在 heartbeat/epoch update 重验长连接
grant 的 expiry/revocation。每连接限制 frame、
事件速率、待发送 bytes 和 replay window。慢消费者收到 `stream.draining` 控制 frame 后关闭；若已无法发送，
直接关闭，客户端用最后 acknowledged durable cursor 恢复。Readiness 关闭后先 drain，禁止接新流。

### 12.3 顺序、坏帧与重连

- durable event 按 `(streamEpoch,durableSeq)` 严格连续；duplicate eventId/seq 幂等忽略。
- live delta 是 best effort，只能修改 `streaming` part；offset 仅在单连接内按 `(runId,partId,attemptId)` 暂存去重，
  不写 PostgreSQL checkpoint、不进入 cursor/snapshot，重连后由 durable completed/partial projection 收口。
- envelope 合法但未知 part schema：保存顺序并渲染 unsupported card。
- JSON/事件 envelope/已知 schema malformed：客户端停止 apply，记录不含 payload 的 contract telemetry，关闭流并
  refetch snapshot；不得 skip-and-continue。
- 服务端从 bus 读到 malformed durable event：不推进 watermark，隔离到 DLQ 并告警；不得把后续 seq 越过去。
- 重连使用 exponential backoff + full jitter、上限 30 秒，尊重 `Retry-After`；鉴权/contract 错误不盲重试。
- snapshot 与 attach 竞态：先保存 watermark，再从其后订阅；服务端 replay window 覆盖二者间隙。

## 13. 服务端 search、archive、pin 与 folder

```text
GET /v1/sessions
  ?projectRef=&q=&lifecycle=active|archived|trashed
  &folderId=&pinned=&sort=updated_desc&cursor=&limit=

PATCH /v1/sessions/{id}
  {title,expectedVersion,commandIdentity}
POST /v1/sessions/{id}:archive
POST /v1/sessions/{id}:restore
POST /v1/sessions/{id}:trash
PUT  /v1/sessions/{id}/preference
  {pinned,folderId,expectedVersion,commandIdentity}

POST /v1/session-folders
PATCH/DELETE /v1/session-folders/{folderId}
```

搜索由 Session 的授权 read projection 执行，至少索引 title 和用户/assistant 的 safe text parts；reasoning、secret、
tool raw input、hidden/moderated payload 不入索引。结果带 `indexWatermark` 和 `nextCursor`，分页稳定。Archive 不
cancel Run；Trash active Run 必须先走可靠 cancellation policy。删除 folder 只解除关联，不删除 Session。

pin/folder 是 actor-scoped；协作者不可替他人改偏好。Web `rail-search.ts` 的本地过滤只能做已加载结果的即时
highlight，不能充当结果真源。

## 14. Usage 与 cost truth

执行状态与费用状态正交：

```text
executionStatus = admission_pending | waiting_prerequisite | running |
                  paused | cancelling | completed | failed | canceled | outcome_unknown

costStatus = none | reserved | committed | cost_pending | settled |
             released | reconciliation_required
```

Wave 3 不实现或迁移任何 `AttemptUsageFact` producer。Gateway/Capability 的 producer、canonical Usage ingestion 与
settlement 属于 Wave 5A；本 Wave 只消费 Platform 已拥有的 reservation/commit/cost projection contract，并证明
Session 不再生成 billing evidence。Wave 5A 未 active/certified 时，production paid execution feature 必须关闭；
Wave 3 测试只能注入 owner-contract fixture，不能把 fixture 冒充真实计费闭环。

Session 只消费：

```text
RunCostProjection{runId,costStatus,estimate?,ratedAmount?,currencyOrCreditUnit,
                  ratingSnapshotRef,usageEvidenceRefs[],freshness,updatedAt}
```

GA terminal token usage 只用于运行展示/观测，不是 billing evidence。Run 可以
`completed + cost_pending`；不能因 rating outage 重跑 Run，也不能把 committed Hold 按 timeout 释放。旧
`GET /billing/*` Session 代理和 `billing_journal` 不进入新 contract。

## 15. Web production auth 与 Site bootstrap

### 15.1 可信链

```text
deployment-bound SiteProjectBinding credential
  → Platform ExchangeSiteContext(workload identity, deployment ref)
  → SiteContext(siteId,siteReleaseId,webArtifactDigest,current epochs)
  + AuthSession/actor
  → Platform IssueSessionAccessGrant(project/member/scopes)
  → BFF calls Session HTTP/SSE
```

浏览器不提交 `siteId`、namespace 或 raw Session Bearer。BFF 不再把通用 runtime JWT 直接转发 Session；每个
request/stream 使用 audience 为 `session.read|session.write|session.control|session.stream` 的短期 grant。Session
在每个 effect point 使用同一 evaluator，并在 subject generation/revocation 变化时拒绝旧 grant/cursor。

production 下以下任一缺失都 fail closed：SiteProjectBinding、workload credential、Site release、AuthSession、
Project membership、grant verifier key、contract compatibility。不得回 `KOKORO_SITE_ID`、默认品牌、Host query
或 caller header。local development 可有显式 `KOKORO_LOCAL_UNSAFE_SITE_BINDING=1`，启动日志/页面水印必须醒目，
且构建/部署 gate 禁止该值进入 production。

#### 15.1.1 SessionAccessGrant 签发、双证据与撤销投影

`SessionAccessGrant` 是 Platform Authorization 签发的独立 JOSE credential，不复用用户登录 access token，也不属于
Admission。V1 使用 `jose` 的 asymmetric `RS256` compact JWS；production 禁止 HS256。签发私钥只在 Platform
Authorization signer，Session 只持 JWKS/pinned public keys；该 key ring 与 UserSession key ring 分离，`kid` 必填，
轮换采用 current+previous 双读和明确退役时间。固定 `iss`，`aud` 只能是
`session.read|session.write|session.control|session.stream` 之一，`jti/iat/nbf/exp` 必填，TTL 不超过 5 分钟。

签发时 Platform 在一个 transaction 中锁定并复核 ProductContext、Site/User/AuthSession/ProjectMembership、restriction
与 credential 状态，持久化独立 `grantRef`、purpose、可选 exact session/run binding、epoch vector digest、key revision、
expiry 与 status，再写 authorization outbox。每次签发可产生新 grant；不能把 credential 当幂等 command response。
公开响应中的 binding 只是 BFF 的安全回显，Session 的可信 claims 必须来自 JWS 验签结果。

Session v3 同时要求两个独立证据：

1. transport adapter 验证 Site BFF workload credential（production 首选 mTLS/SPIFFE 或部署绑定的非用户 service
   credential），形成 trusted workload claims；
2. application provider 验证 purpose-bound SessionAccessGrant。

任一缺失/失效都 fail closed。两份证据必须精确一致于 `siteProjectBindingRef/deploymentRef/siteRef/siteReleaseRef/
webArtifactDigest/runtimeEnvironment/region/sessionContractRevision`；不一致按 non-disclosure
`SESSION_SCOPE_MISMATCH`，不能相信浏览器 header/body 自填值。v3 是 server-to-server BFF 边界，不开放浏览器 CORS，
raw grant 永不进入浏览器。

仅靠短 TTL 不能满足主动撤销。Platform 为 Site suspend、AuthSession revoke、subject generation、Membership、
authorization/restriction/credential/policy 变化原子 bump 聚合 `revocationEpoch` 并发布签名 durable authorization event。
Session 以 inbox+digest 去重、单调 sequence/gap 检测更新本地 `platform_authorization_projection`；已有
`session_access_acl_projection` 继续表达 Session-owned resource ACL，两者必须同时通过。新验签 grant 只允许在本地投影
不存在时以其签名 epoch vector seed，或以严格更高的聚合 revocation epoch 前进，旧 grant 不得覆盖更新投影。

所有 mutation/control、read/snapshot 建立和 SSE 建连前调用同一个 evaluator；SSE heartbeat 至少每 15 秒检查一次。
authorization projection 超过 30 秒未收到 signed freshness/event、出现 sequence gap、签名/epoch 向后、feed bootstrap
失败或 key revision 未知时 fail closed。正常 revocation SLO 为 30 秒；恢复通过 Platform 的 privileged snapshot/replay
consumer contract 补齐 gap，不在 HTTP hot path 每次同步调用 Platform，也不把 Authorization 塞进 Admission。

### 15.2 Bootstrap 分工

独立 Web artifact 本地拥有：route tree、brand assets/tokens、SEO、营销/法务文案、locale bundles 和 analytics
入口。Platform bootstrap 返回动态授权事实：

```text
siteId, siteReleaseId, webArtifactDigest, actor safe profile,
enabledSurfaceIds, featurePolicyRevision,
project summaries, modelOption catalog refs, agent catalog refs,
sessionContractRevision, localePolicy, current epochs, cache policy
```

BFF 必须校验 bootstrap 的 `webArtifactDigest` 与自身构建 manifest 一致；不一致返回 maintenance/upgrade，不能
套用别站配置。品牌内容不从一个万能远端 JSON 改写，动态 feature 也不硬编码在 thin app。

### 15.3 外部独立 Site repo 与 shared capability source

`kokoro-web` 只拥有 versioned shared packages、scaffold 和 reference app：

```text
kokoro-web/packages/session-client    generated Session HTTP/SSE client + cursor policy
kokoro-web/packages/chat-surface      brandless Chat components + Kokoro runtime adapter
kokoro-web/packages/bff-runtime       workload exchange/grant/proxy helpers
kokoro-web/packages/design-system     brandless primitives/token contract
kokoro-web/apps/user                  reference/scaffold/test harness；禁止 production deploy
```

每个 production Site 必须在 `kokoro-web`/root superproject 之外拥有独立 source repository、build root、
`package.json`、package-manager lock、CI、artifact registry identity、deployment、release 和 rollback；它只按 exact
package version 消费发布的 Kokoro shared packages，不 import sibling source、不共享 lock。每个 Site artifact 生成
`site-web-artifact-manifest.json`（SiteProjectBinding ref、source commit、lock/artifact/route/brand/legal/contract digest）。
禁止 `if(siteId)`、同一 artifact 运行时换 Site，或用 root compatibility evidence 冒充 Site CI/release evidence。
`apps/admin` 仍是独立 Admin deployable、无业务 DB；Admission mirror 不等于 provider。

### 15.4 assistant-ui runtime integration

Chat UI 冻结精确依赖 `@assistant-ui/react@0.14.28`，不得使用 caret/tilde/workspace 浮动范围；各外部 Site lock
必须钉 npm integrity `sha512-HZ0aQ5Ozq5jvAfD4ZWPs13Ujod9aNbLXMfVx7fTqbCqZE6dB/tVUTsrimIMthGeCXA6jO6Fj0HnZiykBS4jwRA==`。
版本来自 2026-07-28 npm registry 查询；升级必须独立 contract/UI E2E 与 lock review。集成采用官方
[`ExternalStoreRuntime`](https://www.assistant-ui.com/docs/runtimes/custom/external-store)（React hook
`useExternalStoreRuntime`）+ `KokoroExternalStoreAdapter`：

- `messages/messageRepository` 仅由 Kokoro complete snapshot + SSE projection 转换；Assistant UI 不是真源。
- `onNew/onEdit/onReload/onCancel` 分别调用 Submit/Edit/Regenerate/RequestCancellation；handler 完成不代表 terminal。
- typed MessagePart 使用 Kokoro renderer registry；未知 version 显示 unsupported，不丢 part。
- branch head、thread id、isRunning/cancelling 从 Kokoro projection 单向派生；branch activate 仍发 Session command。
- 不采用 AssistantCloud 保存 thread/attachment/telemetry，不用 AssistantTransport/AI SDK transport 替代 Session
  HTTP/SSE、cursor、receipt 或 BFF auth，也不把 `thread.export()` 当持久化格式。

## 16. HTTP 错误 contract

统一 envelope：

```text
{error:{code,message,retryClass,action,details?},requestId,correlationId}
```

首批 stable code：

| Code | HTTP | action |
|---|---:|---|
| `BFF_WORKLOAD_REQUIRED` | 401 | stop |
| `BFF_WORKLOAD_REVOKED` | 403 | stop |
| `SESSION_ACCESS_GRANT_REQUIRED` | 401 | refresh_grant |
| `SESSION_ACCESS_GRANT_EXPIRED` | 401 | refresh_grant |
| `SESSION_ACCESS_GRANT_REVOKED` | 401/403 | reauthenticate |
| `SESSION_SCOPE_MISMATCH` | 404 | stop；不披露存在性 |
| `SESSION_NOT_FOUND` | 404 | stop |
| `SESSION_VERSION_CONFLICT` | 409 | refetch_snapshot |
| `IDEMPOTENCY_CONFLICT` | 409 | developer_error |
| `ACTIVE_RUN_EXISTS` | 409 | wait_or_cancel |
| `CAPABILITY_SNAPSHOT_LOCKED` | 409 | fork_new_session |
| `MODEL_OPTION_UNAVAILABLE` | 422 | choose_model |
| `ATTACHMENT_NOT_READY` | 409 | wait_prerequisite |
| `ATTACHMENT_REVOKED` | 422 | remove_attachment |
| `ADMISSION_DENIED` | 422/403 | show_reason |
| `ADMISSION_OUTCOME_UNKNOWN` | 503 | reconcile_receipt |
| `LAUNCH_OUTCOME_UNKNOWN` | 503 | reconcile_receipt |
| `RUN_CANCELLATION_PENDING` | 202 | poll_or_stream |
| `RUN_OUTCOME_UNKNOWN` | 409 | reconcile_receipt |
| `CURSOR_INVALID` | 400 | refetch_snapshot |
| `CURSOR_CONFLICT` | 400 | developer_error |
| `CURSOR_AHEAD` | 409 | refetch_snapshot |
| `SNAPSHOT_REQUIRED` | 409 | refetch_snapshot |
| `CURSOR_SCOPE_MISMATCH` | 404 | stop |
| `STREAM_EPOCH_MISMATCH` | 409 | refetch_snapshot |
| `CLIENT_CONTRACT_UPGRADE_REQUIRED` | 426 | upgrade_client |
| `PART_SCHEMA_UNSUPPORTED` | 200 projection | render_unsupported |

`message` 是用户安全文案，不含策略细节、secret、raw provider error 或跨 Site identifier。Web 分支只按 code/
action，不解析英文 message。

## 17. 迁移与 clean cut

项目尚未上线，采用停写、转换、验证、原子切换；不做长期 dual-write。

### 17.1 数据迁移

1. 冻结旧 Session 写入，drain active Run；cutover gate 要求 active Run、pending pause、unresolved control、
   billing reconciliation 均为零。GA 不参与 schema migration。
2. 创建 PostgreSQL schema、RLS/owner query、outbox/inbox、search index 和 projection checkpoints。
3. 每个旧 Session 建 `original` Branch；flat Message 变一个 complete `text@v1` part；按 created order 补 parent、
   ordinal、active leaf。无法证明顺序的数据进 quarantine report，不猜历史。
4. 旧 agent/skills/MCP snapshot 只有 exact revision/digest 可解析时才生成 CapabilitySnapshot；否则标
   `historical_unresolved`，该 Session 只读，用户 fork 新 Session 后才能再执行。
5. 旧 raw model 保存为 historical display，不变成可执行 ModelOptionRef。
6. terminal Run 只迁 RunView 与原事件审计；active Run 不迁。旧 billing journal 仅导出审计，由 Platform
   对账确认，不导入为 canonical Usage/Settlement。
7. delivery/contentHash/file 数据不迁成 Artifact。若需保留，只作为 `legacy_mime_preview` 只读 export 清单；
   production UI 默认关闭，Wave 4 后由真实 Asset/Artifact import 流处理。
8. 双跑只允许 read-only projection comparison。行数、branch DAG、message/part digest、watermark、owner scope、
   search count 全部匹配后原子切 traffic；回滚到旧版只能只读，不能恢复双写。

### 17.2 必删旧 adapter/surface

Session cutover 删除或解除 production assembly：

- `src/platform/legacy-admission-adapter.ts`、`legacy-terminal-event-adapter.ts` 与 port 中全部 legacy methods；
- `src/billing/**`、billing reconciler/journal/hold_id、`GET /billing/*`；
- `src/hub/resolver.ts`、`src/namespace/profile.ts` 的 capability/model admission 职责；
- `GET /models`、`GET /agents` 的 Session-owned/fail-open catalog；
- active Run 的 `run.steer` SubmitMessage 分支；
- Mongo `messages/runs/session_events/control/billing/deliveries` production store adapter；
- 数字 `Last-Event-ID`、invalid→full replay、owner snapshot omit-messages、live dirty skip；
- Session `/files`、`/artifacts`、`deliveries` 作为“作品库”的 production route/命名。

Web cutover 删除或替换：

- `core/hydration.ts` 的“snapshot 不含 messages、从 seq 0 重建”假设；
- flat message/run `core/reducer.ts`、`core/projections.ts` 与单 active Run projection；
- `engine/client.ts` 数字 cursor、固定 2s 重连与 malformed-frame current policy；
- `rail-search.ts` 客户端搜索真源；
- `lib/server/site.ts` Host/default Site fallback、`auth.ts` 的 `KOKORO_SITE_ID`/runtime JWT Session proxy；
- `/api/session/*` 直接透传通用 Bearer 的实现；
- Session billing/model/agent/artifact legacy clients 与把 delivery viewer 称 Artifact Library/Studio 的 UI。

根 contract 同步替换 `contract/spec/http.yaml`、`events.yaml` 和 admission proto，重新生成 Session/Web/Platform
mirrors。`contract/spec/control.yaml` 与 GA generated mirror 必须 byte-identical 保持不变；Wave 3 仅停止 Session
产生 `run.steer`。旧 Session 字段/operation 不留 optional compatibility branch；registry/INDEX 同一 promotion 更新。

## 18. 测试与 E2E 门

### 18.1 Contract/静态门

- Proto/OpenAPI/JSON Schema lint、buf breaking 决策、generated mirror byte parity。
- registry 校验 provider/consumer/audience/siteBinding/deadline/retry/receipt/lifecycle。
- 禁止 Session import billing/Hub/Provider、禁止 Web raw namespace/siteId/provider model、禁止 GA 出现 Site/owner。
- 禁止 shared Web package 引具体 Site app、品牌文案或 `if(siteId)`；`apps/user` production deploy gate 必须失败。
- 外部 Site lock 断言 `@assistant-ui/react` exact 0.14.28/integrity；禁止 AssistantCloud/AssistantTransport imports。
- repository boundary、独立 lock/build/artifact/pin 门保持通过。

### 18.2 Session/Platform 集成

- PostgreSQL transaction：message/branch/launch/outbox 原子；同 key 同 digest 幂等、异 digest 冲突。
- Branch DAG：edit/regenerate/fork/activate 不修改旧历史，provenance 可追溯。
- Capability session lock、per-Turn model、revocation 与 historical display。
- Attachment ready/scan pending/revoked/跨 Project/跨 Site 负例；任何负例 GA dispatch 数为零。
- Prepare/Finalize/Release/Reconcile 覆盖 §9.5 每个 crash point、receipt pending/not-found 与 CAS 竞态。
- dispatch 重发只产生 byte-identical 现有 `run.request`；Session 拒绝同 run 异 payload，GA 现有 keep-first 回归不变。
- cancel pre-launch、GA event observed 后 cancel、Session stale-version fence、cancel/completion race 与 receipt recovery。
- owner cost fixture 可投影 `completed+cost_pending`；本 Wave 不测试/实现 AttemptUsage producer 或 settlement。
- snapshot transaction consistency、projection rebuild、DLQ 后不越过坏 durable seq。

### 18.3 SSE/负载

- snapshot watermark 与 attach race、duplicate/gap/epoch change、cursor expiry/tamper/cross-subject/cross-Site。
- 15s heartbeat、proxy idle、graceful drain、buffer cap、slow consumer、replay window exceeded。
- malformed JSON/envelope/known payload fail-repair；unknown part version unsupported-card；不得 skip ordering gap。
- 10,000 并发连接、per-Site fairness、24h soak、10x reconnect storm；记录 p50/p95/p99 与内存上限。

### 18.4 Web Playwright/E2E

- 两个外部独立 Site repositories 分别 clean-clone/build；repo/lock/CI/artifact/route/brand/legal/binding digest 独立，
  且不依赖 `kokoro-web/apps/user` build root，可分别 rollback。
- 交叉 Host、伪 siteId、错 binding、错 artifact digest、撤销 grant、旧 subject generation 全部 fail closed。
- 新对话→typed stream→刷新→跨设备继续；完整 snapshot 后仅续 delta。
- active Run 再提交不 steer；Stop 显示 cancelling，刷新后 receipt/terminal 收敛。
- edit/regenerate/fork/branch selector、server search/archive/restore/pin/folder 跨设备一致。
- ExternalStoreRuntime adapter 的 onNew/edit/reload/cancel 只产生对应 Kokoro command；snapshot/SSE 重水合后 UI 一致，
  Assistant UI export/cloud/transport 不产生第二份 history 或网络请求。
- model disabled、attachment scanning、insufficient entitlement、Admission unknown、GA unknown、cost_pending 有可解释 UI。
- Wave 4 feature off 时无 Studio/Library/upload；legacy MIME preview 不出现 Studio 文案。
- Admin 仍不连业务 DB；Admission 未 active 时不显示“provider healthy”。

### 18.5 GA 回归不变量

根 E2E 用当前 pin 的 GA 验证 launch/control/event compatibility、checkpoint 恢复、HITL 和 terminal event；
`kokoro-agent` git diff 必须为空。若实现需要改 GA business semantics，停止 Wave 3，另开专项设计与批准。

## 19. 可观测性、SLO 与告警

### 19.1 指标

```text
session_http_requests_total{route,status_class,error_code,site_tier}
session_snapshot_duration_seconds{site_tier,result}
session_snapshot_bytes{site_tier}
session_projection_lag_seconds{projection}
session_sse_connections{site_tier}
session_sse_reconnect_total{reason}
session_sse_cursor_reject_total{reason}
session_sse_slow_consumer_total{site_tier}
session_sse_buffer_bytes{site_tier}
session_branch_command_total{kind,result}
session_control_receipt_age_seconds{kind,state}
platform_admission_duration_seconds{operation,outcome}
platform_authorization_segments{state}
platform_admission_receipt_age_seconds{operation,state}
session_launch_reconciliation_age_seconds{state}
session_cost_projection_age_seconds{cost_status}
web_site_binding_failure_total{reason}
web_bootstrap_duration_seconds{site_tier,result}
```

不得把 siteId、userId、sessionId、runId、commandId、model/provider 名作为 metric label。它们只进入受控 trace/log，
且按分类脱敏。所有 command/receipt/launch/Run 通过 correlation/causation IDs 关联。

### 19.2 SLO/告警

- Session snapshot/list/search 的数值预算由 production capacity profile 与 RC baseline 冻结，本 child spec 不虚构值。
- Platform Admission owner processing p95 < 250 ms；不含外部 prerequisite wait。
- healthy connection 的 durable event 可见延迟 p95 < 1 s；heartbeat 缺失两个周期即告警。
- cursor 非预期拒绝率、slow-consumer、projection lag、DLQ、committed segment 未见首个 GA durable event、
  cancellation receipt age、cost_pending age 均设 burn-rate 告警。
- 跨 Site 授权成功数和 wrong-artifact bootstrap 成功数必须恒为零；任何一次按安全事件处理。

日志必须记录 operation、safe error code、contract revision、owner receipt ref 与 digest prefix；不记录 part raw payload、
attachment URL、JWT/grant、MCP input、secret、完整 request digest 或隐藏 reasoning。

## 20. 发布、回滚与验收顺序

1. 先发布 contract/codegen/registry，Admission 仍 `contract-only`，不接 production traffic。
2. Platform 发布 Admission provider + receipt store/reconciler，shadow 只比较决策，不 reserve/capture。
3. Session 发布 PostgreSQL projection 与 read-only migration verifier；旧 Mongo 仍服务旧 traffic。
4. 发布两个独立 Site Web artifacts 到预发布，跑 isolation、snapshot/SSE、branch/cancel E2E。
5. 停写/drain、数据迁移、启用 SessionAccessGrant、Admission reserve/finalize、Session run.request dispatch；原子切流。
6. 观察至少一个完整 SLO 窗口后删除 legacy production assembly 和配置，再提升 root BOM/pins。

回滚必须按 pin 组合：Web 可独立回上一 artifact；Session/Platform contract compatibility window 内可独立回滚。
一旦产生 committed AuthorizationSegment，新版 reconciler 必须继续运行到清零；不能为回滚释放未知执行的额度。
数据库回滚使用 forward fix/restore point，旧 Mongo 只能只读核对，不能重新接写。

Wave 3 最终验收证据：

- Platform Admission registry 为 `active` 且 provider health/receipt recovery 真实通过。
- Session legacy commercial adapter、billing、Hub resolution 与 production Mongo path 零消费者。
- snapshot 包含完整 active Branch messages/parts，Web 未发 seq 0 全历史请求。
- edit/regenerate/fork/cancel/reconnect/cross-device/server organization E2E 全过。
- 两个独立 Site Web artifacts 的 build/deploy/rollback 与跨 Site negative matrix 全过。
- Wave 4 surfaces 关闭时产品不宣称 Studio/Artifact Library；GA git diff 为零。
- 四个子仓本地 CI、root contract/architecture/compatibility/Infra E2E 与 clean recursive clone 通过。

## 21. 主要风险与冻结处置

| 风险 | 冻结处置 |
|---|---|
| Admission proto `FinalizeRun` 现语义相反 | 明确 breaking/v2；禁止同名静默反转 |
| commit 后 Session crash 造成 Hold 悬挂 | 同 launch receipt reconcile；committed 不 TTL release |
| 完整 snapshot 过大 | active Branch 完整、历史显式分页；绝不退全历史 SSE |
| catalog/revocation 使历史无法渲染 | 保存 safe immutable display snapshot，未来 effect 再验 current epoch |
| Mongo→PostgreSQL 顺序或权限猜错 | quarantine + read-only，禁止推测/自动扩大 owner |
| 通用 user app 再次变万能多租户壳 | 独立 lock/artifact/binding/rollback + shared-package static gate |
| Wave 3 UI 偷跑 Studio | bootstrap feature off、术语 lint、Wave 4 owner receipt 前不显示 ready |
| cancel/complete 竞态误报 | Session expected-version 仅做发出前 fencing；GA terminal + Session receipt 投影裁决 |
| malformed event 被跳过导致投影漂移 | 不推进 watermark，DLQ + snapshot repair |
| cost 延迟被误判免费或失败 | execution/cost 正交，显示 cost_pending，Platform 是唯一金额真源 |

以上处置为实现约束，不留给各仓自行选择另一套 fallback。

## 22. Internal review record

- 2026-07-28：独立架构红队复核通过；GA 零变更、Platform Admission、Session PostgreSQL、独立 Site Web、
  assistant-ui、AssetGrant/Usage owner、cursor/SLO/status 等 Critical 均已实质关闭。
- 用户已预先授权非 GA 实现；`implementationAuthorized=true`。`gaRuntimeSemanticChangeAuthorized=false` 继续生效，
  任何需要修改 GA 代码、wire 或业务语义的实现必须停止并单独对齐。
