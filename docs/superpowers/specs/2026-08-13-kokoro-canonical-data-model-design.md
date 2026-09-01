---
artifact: data-architecture-spec
version: "0.11"
created: 2026-08-13
status: superseded-reference
scope: kokoro-postgresql-canonical-model
---

# Kokoro PostgreSQL Canonical Data Model

> **已被当前方案 supersede（2026-08-27）。** 本文仅保留作历史决策输入，不是当前
> Capability/Storage 的 schema 或 API authority。当前实现使用 Capability/Storage 各自拥有的
> MySQL schema、Root v1 protobuf 和 S3-compatible ObjectStore；MCP 资源名以
> `McpServer` / `McpConnection` 为准。本文中的 PostgreSQL、旧部署前缀和旧 MCP 表名不得复制到新实现。

## 0. 文档定位

本文先定义数据、关系、写权限和事务，再由这些事实推导能力子仓。对应的仓库/RPC 结果见
[`2026-08-13-sql-first-capability-architecture-design.md`](2026-08-13-sql-first-capability-architecture-design.md)。

这里定义的是**目标 canonical superset**，用于锁定最终关系、owner 和迁移方向；它不是要求第一批
一次创建全部表。首发按 §0.1 的 slice manifest 安装实际被真链写入的表，后续只从本文已审定的
关系中增加能力。本文不照搬当前六份 MySQL Prisma schema、Session/Hub/Agent Mongo collection，
也不为未进入当前 slice 的能力提前安装空表。

### 0.1 Baseline slices

| Slice | 目标 | 安装范围 |
|---|---|---|
| A：SQL-backed Chat | Site host、IAM login/RBAC、Conversation/Message、Agent admission/execution/projection、Model resolve、显式 empty Capability snapshot | 只安装这些命令实际写入的表；Usage 明确为 `unmetered`，仍记录 run usage，但不创建 Credit hold；不包含 Artifact/Payment/Redemption |
| B：Agent capabilities | Skill/MCP catalog、Storage upload/asset/artifact、metered Credit authorization/settlement | 增加 Capability/Storage 与 Entitlement usage/credit 表；不改变 Slice A identity |
| C：Commercial | Offer/Redemption/Acquisition/Fulfillment 与 one-time Payment/reversal | 增加剩余 Entitlement/Payment 表；Payment 和 Redemption 复用同一 Fulfillment |

Root 每个 slice 都生成一份完整可重放 baseline；进入 production 后冻结 baseline，后续使用 ordered
forward migration。下面标为“目标”的表可以晚于 Slice A 安装，但关系和 owner 不再临时改名。
指向后续 slice 表的 nullable 列/FK 也与目标表同批增加：例如 Slice A 的 manifest 只有
`usage_mode='unmetered'` + policy digest，Slice B 才增加 hold ref/price digest；`site.current_brand_id` 与
Brand 同批增加。这样 fresh DDL 不引用不存在的表，也不为未来能力预装空结构。

### 0.2 Slice A exact table manifest

- Site：`site_site`, `site_domain`。
- IAM：`iam_principal`, `iam_user`, `iam_identity`, `iam_contact`, `iam_magic_link`,
  `iam_auth_session`, `iam_command_receipt`, `iam_organization`, `iam_membership`, `iam_role`,
  `iam_permission`, `iam_role_permission`, `iam_membership_role`, `iam_security_event`。
- Chat：`chat_conversation`, `chat_message`, `chat_message_part`, `chat_command_receipt`,
  `chat_run_launch`, `chat_active_run`, `chat_run_view`, `chat_interaction`, `chat_control_command`,
  `chat_control_outbox`, `chat_launch_outbox`, `chat_projection_inbox`, `chat_projection_dlq`,
  `chat_stream_event`。
- Agent：`agent_run`, `agent_execution_manifest`, `agent_run_lease`, `agent_control_inbox`,
  `agent_event_outbox`, `agent_dispatch_outbox`, `agent_projection_ack`, `agent_tool_effect`,
  `agent_run_usage`, `agent_run_usage_line`, `agent_sandbox_binding`, `agent_memory`,
  `agent_dispatch_dlq`，以及固定版本官方 checkpointer 四张表。
- Capability：`capability_runtime_snapshot`, `capability_command_receipt`；snapshot 在 Slice A 明确为空，
  因此 item 表和 Skill/MCP FK 延后到 Slice B，不伪造默认 Skill/MCP。
- Model：`model_provider`, `model_definition`, `model_revision`, `model_routing_policy`,
  `model_provider_health_state`。Slice A health state 只存 `unknown`，不预装尚无 probe writer 的 observation 表；
  后续 health slice 同批增加 observation、`last_observation_id` FK 与 owner command。

Slice A 共 50 张 owner 业务表 + 4 张官方 checkpointer 表。其余目标表不出现在 Slice A DDL、Prisma
client、deployable 或 secret/config surface；这条 exact manifest 由 Root catalog test 锁定。Slice A
不安装 `iam_principal_role` 或 `iam_operator_site_role`，因此只允许 control-plane Admin 登录和低风险全局 read；任何 target-Site
管理操作保持 feature-off，直到后续 slice 安装 operator-site assignment 与对应 owner-local authorization。

## 1. 三个安全轴与业务聚合

多租户和授权只使用下面三个稳定安全轴，不再用 `ownerId`、email、namespace、Project 或 JSON header
互相冒充。Conversation/Run 是业务 aggregate identity，不是第四个租户轴：

| 轴 | 含义 | 权威表 | 使用规则 |
|---|---|---|---|
| `site_id` | 产品站点、品牌和策略顶层 | `site_site` | 包含多个 personal/team organization；不同 Site 的账号不共享 |
| `principal_id` | Site 内的人/service account，或独立 control-plane operator | `iam_principal` | 产品用户不跨 Site；operator 是独立身份，可获多个 target Site scope；不传入 GA core |
| `organization_id` | Site 内的个人空间或团队空间 | `iam_organization` | personal/team；属于且只能属于一个 Site；个人登录后由 IAM 幂等建立 personal organization |

推导链固定为：

```text
site --contains--> principal
site --contains--> organization --contains--> conversation
principal --membership--> organization
conversation --owns--> opaque agent namespace
project --optionally groups--> conversations   # Slice A 以后再增加
```

Conversation 可直接属于 personal/team organization；创建或打开 Conversation 不依赖 Project。
Project 只是用户主动使用的长期分组、共享上下文和协作容器，不进入 Slice A，不是登录或发起 Agent Run 的
bootstrap 步骤。GA core 只消费 `namespace`、`session_id=conversation_id` 与 frozen execution manifest，
不接收 `principal_id`、`organization_id` 或 `site_id` 作为第二隔离轴。

## 2. 全局 SQL 规则

### 2.1 物理与命名

- 一个 PostgreSQL 18 database，一个 `kokoro` schema。
- 表按 owner 前缀命名：`iam_*`、`site_*`、`chat_*`、`agent_*`、`capability_*`、
  `model_*`、`storage_*`、`entitlement_*`、`payment_*`。
- 主键为应用生成的 UUID；每张业务表只有一个明确 PK。
- 所有 mutable aggregate 有 `generation bigint NOT NULL DEFAULT 1`、`created_at timestamptz`、
  `updated_at timestamptz`；append-only fact 没有伪 `updated_at`。
- 金额为 `bigint` minor units + `char(3)` currency；Credit 为 `bigint` micros。

### 2.2 约束

- 稳定关系必须是 FK；同库不能继续把 `siteId/teamId/modelId` 当无约束字符串。
- 每个 composite FK 的 referenced tuple 必须有同序 `UNIQUE` candidate key；Root catalog test 在真实
  PostgreSQL 创建并核对 FK/unique 列序，不用文档或 SQL 字符串匹配代替。
- Tenant lineage 规则全局适用：只存直接 parent 时由 parent 推导 site/org；一旦同表同时保存
  `site_id`、`organization_id`、可选 `project_id` 或 actor principal 中两个以上，就必须用 composite FK
  证明它们属于同一条 `Site → Organization` 链；存在 Project 时还必须证明 Project 与 Conversation 属于同一 Organization/Site。表格中的“FK”不代表允许独立 FK 拼接。
- 业务候选键使用正常 `UNIQUE`；读取索引使用普通非唯一 index。
- `CHECK` 保护非负数、时间区间、状态组合、成对 nullable 字段和 JSON schema version。
- JSONB 仅承载 bounded snapshot/provider payload/typed part；identity、金额、状态和 FK 不进 JSONB。
- 同一事务中的竞争使用唯一约束、row lock 和 generation CAS；禁止 unprotected query-then-insert。
- 所有 `current_*`、`live` binding 和可执行 routing pointer 必须只引用已 published/approved revision。
  实现使用带状态的可引用 candidate key，或 `DEFERRABLE INITIALLY DEFERRED` constraint trigger；每个
  pointer 都要有“draft revision 被拒绝”的 PG18 negative test。Slice A 的 `model_routing_policy` 首先落实，
  后续覆盖 Site Brand、Skill/MCP current、Offer current 与 Artifact current。

### 2.3 删除与保留

| 数据类别 | 策略 |
|---|---|
| User/Organization/Site/Conversation/optional Project aggregate | lifecycle + generation；默认 `ON DELETE RESTRICT`，不做跨域级联删除 |
| Credential/AuthSession | revoke 后按 retention hard-delete；只允许对无业务引用的 ephemeral child `ON DELETE CASCADE` |
| Message/Run/Artifact/Acquisition/Fulfillment/Ledger/Payment fact | append-only 或 terminal，不物理删除；按 retention 冷存/脱敏 |
| PII deletion | 先 revoke identity/credential/session，再把 profile/contact 去标识化；audit/ledger 保留 opaque principal UUID |
| Blob | metadata terminal 后由 GC command 删除 object bytes；任何 live Asset/Artifact/Package FK 存在时拒绝 |

不使用“每表一个 deleted_at”模板；只有确有恢复语义的 aggregate 才有 archive/trash/restore。

## 3. Site 与 IAM

### 3.1 Site tables

| 表 | 必需列 | 主关系与约束 |
|---|---|---|
| `site_site` | `site_id`, `key`, `name`, `status`, `default_locale`, `timezone`, `current_brand_id?`, `generation` | 产品表面根；key UNIQUE；composite FK 保证 brand同site，constraint trigger拒绝未published brand |
| `site_domain` | `domain_id`, `site_id`, `normalized_host`, `status`, `is_primary`, `verification_token_hash?`, `verified_at?` | FK site；host UNIQUE；每 site 一个 live primary |
| `site_brand` | `brand_id`, `site_id`, `revision`, `logo_blob_id?`, `theme`, `copy_namespace`, `published_at?` | `UNIQUE(brand_id,site_id)`、`UNIQUE(site_id,revision)`；published immutable；PublishBrand 同事务更新 site.current_brand_id |
| `site_feature` | `feature_id`, `site_id`, `key`, `enabled`, `configuration`, `generation` | FK site；`UNIQUE(site_id,key)` |

首发不建第二套 SiteBrandConfig/SEO/App 表；新增真实需求时以 revision 或独立 aggregate 扩展。

### 3.2 IAM tables

| 表 | 必需列 | 主关系与约束 |
|---|---|---|
| `iam_principal` | `principal_id`, `principal_scope(site|control_plane)`, `site_id?`, `kind(user|service_account|operator)`, `status`, `generation` | `UNIQUE(principal_id,site_id)`；site scope=>site非空且非operator；control_plane=>site空且operator |
| `iam_user` | `principal_id`, `display_name`, `avatar_url`, `locale` | PK/FK principal；不以 email 作为 identity |
| `iam_identity` | `identity_id`, `principal_scope`, `site_id?`, `principal_id`, `issuer`, `subject`, `status` | FK principal_id；site/control-plane partial UNIQUE；deferred scope trigger 校验 principal_scope/site_id exact match |
| `iam_contact` | `contact_id`, `principal_scope`, `site_id?`, `principal_id`, `kind(email|phone)`, `normalized_value`, `status(active|revoked)`, `verified_at?`, `revoked_at?` | FK principal_id + 同一 scope trigger；同 scope active contact partial UNIQUE |
| `iam_credential` | `credential_id`, `principal_id`, `identity_id?`, `kind`, `secret_hash/public_key`, `status`, `last_used_at` | CHECK private/public material 组合；不存明文 token |
| `iam_magic_link` | `magic_link_id`, `principal_scope(site|control_plane)`, `site_id?`, `normalized_email`, `token_hash`, `nonce_hash?`, `expires_at`, `consumed_at?`, `superseded_at?` | scope/site CHECK；token hash UNIQUE；消费/替换 CAS；User/Admin 复用成熟语义 |
| `iam_auth_session` | `auth_session_id`, `principal_scope(site|control_plane)`, `site_id?`, `organization_id?`, `principal_id`, `family_ref`, `family_generation`, `token_hash`, `expires_at`, `rotated_to?`, `revoked_at?` | FK principal_id + deferred scope trigger；site user session 的 organization 非空且 composite FK 到同 site org/active membership，control-plane session 的 organization 为空；token hash UNIQUE；`UNIQUE(family_ref,family_generation)`；family generation immutable/monotonic and is the deterministic refresh derivation input；rotate/revoke CAS |
| `iam_command_receipt` | `receipt_id`, `command_id`, `command_kind`, `request_digest`, `status`, `result_ref?`, `result_payload?` | command UNIQUE；same digest replay/different digest conflict |
| `iam_organization` | `organization_id`, `site_id`, `kind(personal|team)`, `personal_owner_principal_id?`, `name`, `status`, `generation` | `UNIQUE(organization_id,site_id)`；personal owner composite FK 到同 site 的普通 principal；partial `UNIQUE(site_id,personal_owner_principal_id)` |
| `iam_membership` | `membership_id`, `site_id`, `organization_id`, `principal_id`, `status`, `generation` | 两组 composite FK 保证 org/principal 同 site；`UNIQUE(organization_id,principal_id)`；`UNIQUE(membership_id,organization_id)` |
| `iam_role` | `role_id`, `site_id`, `organization_id?`, `key`, `name`, `role_kind(site|organization)`, `status` | `UNIQUE(role_id,site_id)`、`UNIQUE(role_id,organization_id)`；site/org role 分别 scoped key UNIQUE；scope CHECK |
| `iam_permission` | `permission_id`, `key`, `description`, `status(active|disabled)`, `generation` | key UNIQUE；稳定 permission catalog；disabled permission 即使仍有 role binding 也不授权 |
| `iam_role_permission` | `role_id`, `permission_id` | 复合 UNIQUE；双 FK；无独立业务 identity |
| `iam_membership_role` | `organization_id`, `membership_id`, `role_id` | composite FK 到同一 org 的 membership/role；`UNIQUE(membership_id,role_id)`；拒绝跨组织绑定 |
| `iam_principal_role` | `assignment_id`, `site_id`, `role_id`, `principal_id`, `scope_kind(site|organization)`, `organization_id?`, `status` | 仅 site-scoped principal/service account；composite FK 保证 principal/role/scope 同 site/org |
| `iam_operator_site_role` | `assignment_id`, `operator_principal_id`, `target_site_id`, `role_id`, `status` | operator 必须 control_plane；composite FK role/target site；`UNIQUE(operator_principal_id,target_site_id,role_id)`；承接 Admin `scopeSites` |
| `iam_invite` | `invite_id`, `site_id`, `organization_id`, `normalized_email`, `role_id`, `token_hash`, `status`, `expires_at` | composite FK org/role/site 保证同 organization；token hash UNIQUE；pending→accepted/revoked/expired |
| `iam_service_account` | `principal_id`, `site_id`, `organization_id`, `name`, `token_prefix`, `secret_hash` | PK/composite FK principal+org/site；prefix UNIQUE |
| `iam_security_event` | `event_id`, `principal_scope?`, `site_id?`, `target_site_id?`, `principal_id?`, `actor_service?`, `kind`, `request_id`, `payload`, `occurred_at` | typed scope/site actor 与 target；append-only；payload 有 schema version |

`iam_identity`、`iam_contact`、`iam_auth_session` 统一使用 FK `principal_id` 加
`DEFERRABLE INITIALLY DEFERRED` constraint trigger：site principal 必须 exact site，control-plane principal 必须
`site_id IS NULL`。这是特意避免 PostgreSQL `MATCH SIMPLE` 对 NULL composite FK 跳过检查；PG18 负向测试
必须覆盖 operator row 指向 site principal、site row 指向 operator 以及 scope/site 漂移。`iam_auth_session`
另用 deferred trigger/composite FK 证明 site session 的 organization 与 principal active membership 同属 Site；
control-plane session 必须 `organization_id IS NULL`。同一 family 的 `family_generation` 只在 rotate 创建 successor
时单调增加，之后不可修改；receipt 重放以该 immutable generation 重导出同一 refresh token。

## 4. Chat

| 表 | 必需列 | 主关系与约束 |
|---|---|---|
| `chat_conversation` | `conversation_id`, `organization_id`, `site_id`, `created_by_principal_id`, `title`, `agent_namespace`, `state(active|archived|trashed)`, `next_stream_seq`, `generation` | composite FK organization/site 与 principal/site；`UNIQUE(conversation_id,organization_id)`、`UNIQUE(conversation_id,site_id)`；namespace UNIQUE；stream seq 在事务内分配 |
| `chat_message` | `message_id`, `conversation_id`, `parent_message_id?`, `role`, `status`, `ordinal`, `generation` | `UNIQUE(message_id,conversation_id)`；parent 用 composite FK 保证同 conversation；`UNIQUE(conversation_id,ordinal)` |
| `chat_message_part` | `part_id`, `message_id`, `ordinal`, `kind`, `schema_version`, `payload`, `status`, `generation` | FK message；`UNIQUE(message_id,ordinal)`；typed bounded JSONB |
| `chat_command_receipt` | `receipt_id`, `site_id`, `organization_id`, `conversation_id?`, `command_id`, `command_kind`, `request_digest`, `status`, `result_ref?`, `result_payload?` | composite org/site；optional conversation composite FK；`UNIQUE(receipt_id,conversation_id,organization_id)` candidate；`UNIQUE(organization_id,command_id)`；CreateConversation 可先 claim 后填 result |
| `chat_run_launch` | `launch_id`, `conversation_id`, `user_message_id`, `assistant_message_id`, `requested_model_ref?`, `requested_agent_ref?`, `state`, `agent_run_id?`, `manifest_digest?`, `generation` | `UNIQUE(launch_id,conversation_id)`；message 用 composite FK 保证同 conversation；user/assistant 不得相同；accepted 后 immutable |
| `chat_active_run` | `conversation_id`, `launch_id`, `acquired_at` | conversation PK；launch UNIQUE；composite FK `(launch_id,conversation_id)` 保证同 conversation |
| `chat_run_view` | `agent_run_id`, `launch_id`, `conversation_id`, `epoch`, `state`, `received_seq`, `projected_seq`, `terminal_kind?`, `generation` | agent run PK；`UNIQUE(agent_run_id,conversation_id)`；launch UNIQUE；`(launch_id,conversation_id)` FK；只由 projector 写 |
| `chat_interaction` | `interaction_id`, `agent_run_id`, `conversation_id`, `kind`, `action_digest`, `schema_version`, `payload jsonb`, `status`, `expires_at?`, `generation` | `UNIQUE(interaction_id,conversation_id)`；`(agent_run_id,conversation_id)` FK；immutable bounded payload；pending→resolved/cancelled/expired |
| `chat_control_command` | `control_id`, `receipt_id`, `conversation_id`, `organization_id`, `interaction_id?`, `expected_generation`, `decisions jsonb`, `status` | `(receipt_id,conversation_id,organization_id)` 与 optional `(interaction_id,conversation_id)` composite FK；receipt UNIQUE；canonical nonempty exact target set；同 org 内也不能跨 Conversation 决策；pause-frame decision effectively-once |
| `chat_control_outbox` | `outbox_id`, `control_id`, `payload`, `attempt`, `next_attempt_at`, `published_at?`, `acked_at?` | control UNIQUE/FK；与 control 同事务 |
| `chat_launch_outbox` | `outbox_id`, `launch_id`, `request_digest`, `payload`, `attempt`, `next_attempt_at`, `accepted_at?` | launch UNIQUE/FK；Submit transaction 内创建 |
| `chat_projection_inbox` | `inbox_id`, `producer`, `agent_run_id`, `epoch`, `producer_seq`, `event_id`, `schema_version`, `payload`, `status` | event id UNIQUE；`UNIQUE(producer,agent_run_id,producer_seq)`，producer_seq 是 run-global；epoch 只作 fence 证据，旧 epoch event 拒绝 |
| `chat_projection_dlq` | `dlq_id`, `inbox_id`, `error_code`, `repair_status`, `attempt`, `next_attempt_at` | inbox UNIQUE/FK；不伪造 Agent terminal |
| `chat_stream_event` | `stream_event_id`, `conversation_id`, `seq`, `event_id`, `kind`, `schema_version`, `payload`, `expires_at?` | `UNIQUE(conversation_id,seq)`、`UNIQUE(conversation_id,event_id)`；snapshot watermark 后的 bounded SSE tail |
| `chat_share` | `share_id`, `conversation_id`, `token_hash`, `expires_at?`, `revoked_at?`, `created_at` | FK conversation；token hash UNIQUE；每 conversation 一个 live share 的 partial UNIQUE；目标保留现有公开 snapshot 语义，Slice B 再安装 |
| `chat_project`（后续） | `project_id`, `organization_id`, `site_id`, `project_key`, `name`, `status`, `generation` | optional organizer；org/site composite FK；org+key UNIQUE；不拥有 namespace，不是 Conversation 前置 |
| `chat_project_conversation`（后续） | `project_id`, `conversation_id`, `organization_id`, `site_id`, `added_at` | 两组 composite FK 强制同 Organization/Site；一个 Conversation 可在产品规则允许时加入一个 Project；不改变 Conversation identity |

Chat 不拥有 billing、Skill/MCP、Model、Agent checkpoint、Blob 或 Artifact bytes。

`ReadConversationSnapshot` 必须在同一 repeatable-read transaction 中读取 Conversation、Message/Part、RunView、
active Run、pending Interaction，并以该数据库快照内的 `next_stream_seq - 1` 返回 `watermark`。Web hydration
先用这份完整 owner snapshot 构建现有 reducer state，再从 `watermark` 之后订阅 SSE。只有完整 snapshot 已可
重建历史内容时，`chat_stream_event` 才允许按 retention 删除旧 tail；不得继续依赖 `lastSeq=0` 全量事件回放。

Branch/edit/regenerate 是最小闭环后的第一个扩展：届时新增 `chat_branch`，把 Message ordinal 唯一键迁为
`(branch_id,ordinal)`，并为 Conversation 增加 current branch/leaf。Project 分组同样在后续 slice 增加，
初始 baseline 不为了尚未上线的分支或 Project 提前增加循环 FK。

## 5. Agent execution

| 表 | 必需列 | 主关系与约束 |
|---|---|---|
| `agent_run` | `agent_run_id`, `launch_id`, `launch_request_digest`, `namespace`, `execution_manifest_id?`, `state`, `epoch`, `next_event_seq`, `generation`, `terminal_at?` | launch UNIQUE；same launch+same digest exact replay、digest drift conflict；`UNIQUE(agent_run_id,launch_id)`、`UNIQUE(agent_run_id,namespace)`；`next_event_seq` under run-row lock allocates one run-global sequence and never resets across epoch；preparing/admission_failed 可无 manifest；CAS 后不可换 |
| `agent_execution_manifest` | `execution_manifest_id`, `agent_run_id`, `namespace`, `digest`, `agent_preset_key`, `agent_preset_digest`, `model_revision_id`, `capability_snapshot_id`, `usage_mode(unmetered|metered)`, `usage_policy_digest`, `usage_authorization_ref?`, `credit_hold_id?`, `usage_price_digest?`, `payload`, `created_at` | composite FK run/namespace；run UNIQUE；metered refs成套非空；price revision只由 hold拥有，manifest冻结digest；immutable |
| `agent_run_lease` | `agent_run_id`, `worker_id`, `lease_token_hash`, `leased_until`, `generation` | run PK/FK；claim/renew/release CAS |
| `agent_control_inbox` | `control_id`, `agent_run_id`, `command_id`, `request_digest`, `status`, `applied_at?` | `UNIQUE(agent_run_id,command_id)` + digest；FK run |
| `agent_event_outbox` | `event_id`, `agent_run_id`, `epoch`, `seq`, `kind`, `schema_version`, `payload`, `published_at?`, `acked_at?` | `UNIQUE(agent_run_id,seq)`；event id UNIQUE；seq 从 1 run-global 单调，epoch 不重置 seq 且必须匹配 current lease；可另建 `(agent_run_id,epoch,seq)` lookup index |
| `agent_dispatch_outbox` | `outbox_id`, `agent_run_id`, `manifest_digest`, `attempt`, `next_attempt_at`, `dispatched_at?` | run UNIQUE/FK；worker dispatch after admission commit |
| `agent_projection_ack` | `agent_run_id`, `consumer`, `projected_epoch`, `projected_seq`, `producer_close_requested`, `consumer_closed`, `generation` | run+consumer PK；projected_seq 是 run-global 单调 watermark；epoch 只作 fence，旧 epoch 或 seq 回退不推进；替代 Agent/Session 共享 manifest 双写 |
| `agent_tool_effect` | `effect_id`, `agent_run_id`, `tool_call_id`, `effect_kind`, `request_digest`, `status`, `result_digest?` | `UNIQUE(run,tool_call_id,effect_kind)`；claim-before-effect |
| `agent_run_usage` | `run_usage_id`, `agent_run_id`, `digest`, `input_tokens`, `output_tokens`, `cached_tokens`, `call_count`, `finalized_at` | run UNIQUE/FK；terminal aggregate immutable；非负 CHECK；**唯一 billable usage authority** |
| `agent_run_usage_line` | `usage_line_id`, `run_usage_id`, `model_revision_id`, `feature_key`, `input_tokens`, `output_tokens`, `cached_tokens`, `call_count` | FK run usage/model revision；`UNIQUE(run_usage_id,model_revision_id,feature_key)`；聚合 main/subagent 调用 |
| `agent_sandbox_binding` | `binding_id`, `agent_run_id`, `backend`, `workspace_ref`, `state`, `generation` | FK run；一个 live binding/run |
| `agent_memory` | `memory_id`, `namespace`, `memory_key`, `schema_version`, `payload`, `expires_at?`, `generation` | `UNIQUE(namespace,memory_key)`；到期后由 Agent retention command hard-delete；只由 Agent memory adapter 写 |
| `agent_dispatch_dlq` | `dlq_id`, `agent_run_id?`, `request_digest`, `error_code`, `payload`, `retry_status`, `created_at` | append-only failure evidence；repair command 更新 retry 状态 |

LangGraph checkpoint/writes 使用固定版本官方 PostgreSQL checkpointer 的
`checkpoints`、`checkpoint_blobs`、`checkpoint_writes`、`checkpoint_migrations` 表。Root 在生成
baseline 时执行该固定版本 setup 并把结果纳入 deterministic DDL inventory；Agent runtime 没有自行迁移权限，
也不在业务表中复制 checkpoint 状态。

`agent_run_usage`/`agent_run_usage_line` 覆盖主 agent、subagent 和工具触发的模型调用，按 run 和
model/feature 维度汇总当前 GA 已有的 usage 累计。Entitlement 只能消费这个 terminal aggregate，不自行
推算 token；Model 不写 usage。首发不保留没有产品审计需求的逐 provider-call SQL 明细。

AgentPreset 首发由 Agent 仓受版本控制的配置拥有，由 Agent admission 在进程内解析；manifest 冻结
key+digest。Slice A 不为它增加 RPC 或 SQL 表，它也不是 Site、Chat 中的隐含自由字符串。

## 6. Capability 与 Model control

### 6.1 Capability

| 表 | 必需列 | 主关系与约束 |
|---|---|---|
| `capability_skill` | `skill_id`, `scope_kind(official|organization|project)`, `organization_id?`, `project_id?`, `normalized_name`, `status`, `current_revision_id?`, `generation` | scope CHECK；scoped partial UNIQUE；current revision composite FK 保证属于本 skill；project→org→official |
| `capability_skill_revision` | `skill_revision_id`, `skill_id`, `revision`, `content_hash`, `package_id`, `actor_scope`, `actor_site_id?`, `created_by_principal_id`, `review_status`, `published_at?` | revision claims；scope trigger：official须control-plane operator，org/project须同-site principal；immutable |
| `capability_package` | `package_id`, `storage_blob_id`, `content_hash`, `size_bytes`, `format`, `validation_digest`, `created_at` | FK storage blob；content hash UNIQUE；validated immutable metadata |
| `capability_installation` | `installation_id`, `organization_id`, `project_id?`, `skill_id`, `skill_revision_id`, `status`, `generation` | organization 必填、project 可选；同 scope live partial UNIQUE；revision 必须属于 skill；Project 后续启用不改变 org-scope 安装 |
| `capability_grant` | `grant_id`, `organization_id`, `project_id?`, `skill_revision_id?`, `mcp_revision_id?`, `permission_set`, `status`, `expires_at?` | exactly one target CHECK；organization 必填、project 可选；FK revisions |
| `mcp_server` | `mcp_server_id`, `scope_kind(official|organization|project)`, `organization_id?`, `project_id?`, `normalized_name`, `status`, `current_revision_id?`, `generation` | scoped partial UNIQUE；current revision composite FK 保证属于本 server；解析 project→org→official |
| `capability_mcp_revision` | `mcp_revision_id`, `mcp_server_id`, `revision`, `transport`, `url`, `allowed_tools`, `config_hash`, `actor_scope`, `actor_site_id?`, `created_by_principal_id`, `published_at?` | revision claims；与 server scope/actor 同一 deferred trigger；published immutable |
| `capability_mcp_connection` | `connection_id`, `organization_id`, `project_id?`, `mcp_server_id`, `mcp_revision_id`, `secret_handle_id?`, `status`, `generation`, `last_verified_at?` | org scope 或 optional project scope 与 secret 一致；同 scope 一个 live server；revision 属于 server |
| `capability_secret_handle` | `secret_handle_id`, `organization_id`, `project_id?`, `name`, `ciphertext`, `key_id`, `generation`, `revoked_at?` | FK org/optional project；scoped name UNIQUE；connection 与 secret 必须同 scope；明文不出边界 |
| `capability_runtime_snapshot` | `snapshot_id`, `organization_id`, `project_id?`, `scope_key`, `digest`, `created_at` | organization scope 必填、project 可选；目标使用 org/project 分支 partial UNIQUE；immutable；Slice A 物理表尚无 project 列并固定 `UNIQUE(organization_id,scope_key,digest)`，只允许 organization scope 的显式 empty snapshot，`scope_key` 为 opaque Agent namespace |
| `capability_runtime_snapshot_item` | `snapshot_id`, `item_kind(skill|mcp)`, `skill_revision_id?`, `mcp_revision_id?`, `ordinal` | FK snapshot/revisions；exactly one target CHECK；`UNIQUE(snapshot,item_kind,ordinal)` |
| `capability_command_receipt` | `receipt_id`, `command_id`, `command_kind`, `request_digest`, `status`, `result_ref?` | command UNIQUE；Slice A 只允许 `ResolveRuntimeSnapshot` same-digest replay/drift conflict；后续 slice 才加入 publish/install/grant kinds |

### 6.2 Model control

| 表 | 必需列 | 主关系与约束 |
|---|---|---|
| `model_provider` | `provider_id`, `key`, `display_name`, `status`, `secret_handle_ref?`, `generation` | key UNIQUE；目标 slice 的 secret 是外部 secret-manager handle；Slice A 必须 NULL 且 Model 不读取 inference secret |
| `model_definition` | `model_id`, `key`, `display_name`, `status`, `current_revision_id?`, `generation` | key UNIQUE；current revision composite FK 保证属于本 model |
| `model_revision` | `model_revision_id`, `model_id`, `revision`, `provider_id`, `provider_model_name`, `transport(litellm|direct|local)`, `modalities`, `context_window`, `published_at?` | `UNIQUE(model_revision_id,model_id)`、`UNIQUE(model,revision)`；published immutable |
| `model_routing_policy` | `routing_policy_id`, `site_id`, `label`, `model_revision_id`, `priority`, `status`, `generation` | FK site/model revision；live `(site,label,priority)` unique；deferred trigger 拒绝未 published revision |
| `model_provider_health_state` | `provider_id`, `status(healthy|degraded|unavailable|unknown)`, `last_observation_id?`, `generation`, `updated_at` | provider PK/FK；目标 health slice 的非 unknown 状态必须有同 provider observation；Slice A 物理 shape 只有 `provider_id,status='unknown',generation,updated_at`，后续 migration 同批增加 observation pointer/FK |
| `model_provider_health_observation` | `observation_id`, `provider_id`, `probe_id`, `status`, `latency_ms?`, `error_code?`, `observed_at` | `UNIQUE(observation_id,provider_id)`、`UNIQUE(provider_id,probe_id)`；append-only probe evidence |

首发不建立 Model Invoke/Stream RPC，也不把现有 LiteLLM provider 调用搬出 GA。Model RPC 只返回 frozen
`ModelSelection`；Agent 继续使用已验证的 `model/factory.py` 与 `kokoro-litellm` 调用路径，并把真实
usage 写入 `agent_run_usage`/`agent_run_usage_line`。`model_revision.transport=direct|local` 仅供测试和本地
fixture；production routing policy 只接受 `litellm`，Root deploy/config gate 拒绝 direct-provider secret ownership。

## 7. Storage

| 表 | 必需列 | 主关系与约束 |
|---|---|---|
| `storage_blob` | `blob_id`, `content_hash`, `size_bytes`, `media_type`, `backend`, `object_key`, `state`, `created_at` | `(content_hash,size_bytes)` 与 `(backend,object_key)` UNIQUE；ready blob immutable |
| `storage_upload_session` | `upload_session_id`, `scope_kind(organization|project|internal)`, `site_id?`, `organization_id?`, `project_id?`, `principal_id?`, `actor_service?`, `purpose`, `expected_size`, `media_type`, `state`, `expires_at`, `generation` | organization scope 不依赖 Project；project scope 额外校验同 org/site；internal scope只允许 approved service+purpose；size CHECK |
| `storage_asset` | `asset_id`, `site_id`, `organization_id`, `project_id?`, `created_by_principal_id`, `source_blob_id`, `state`, `generation` | composite FK org/principal与site；project 可选且存在时必须同 org/site；FK blob；upload→scan→ready/rejected |
| `storage_scan` | `scan_id`, `asset_id`, `scanner`, `signature_version`, `result`, `evidence_digest`, `scanned_at` | `UNIQUE(asset_id,evidence_digest)`；append-only；same evidence exact replay |
| `storage_artifact` | `artifact_id`, `organization_id`, `project_id?`, `kind`, `created_by_agent_run_id?`, `current_revision_id?`, `state`, `generation` | organization 直接拥有；project 可选；current revision composite FK 保证属于本 artifact |
| `storage_artifact_revision` | `artifact_revision_id`, `artifact_id`, `revision`, `blob_id`, `source_asset_id?`, `lineage`, `created_at` | `UNIQUE(artifact_revision_id,artifact_id)`、`UNIQUE(artifact,revision)`；immutable |
| `storage_share` | `share_id`, `artifact_revision_id`, `token_hash`, `expires_at?`, `revoked_at?` | FK revision；token hash UNIQUE |
| `storage_command_receipt` | `receipt_id`, `command_id`, `command_kind`, `request_digest`, `status`, `result_ref?` | command UNIQUE；upload/artifact replay authority |
| `storage_outbox` | `outbox_id`, `aggregate_kind`, `aggregate_id`, `effect_kind`, `command_id`, `payload`, `attempt`, `next_attempt_at`, `completed_at?` | command/effect UNIQUE；scan/object/GC effect |

Skill package 通过 `capability_skill_revision.package_id → capability_package.storage_blob_id` 引用
`storage_blob`；Chat MessagePart 只保存
`asset_id`/`artifact_revision_id` typed reference，不复制对象 metadata。

## 8. Entitlement

### 8.1 Catalog / acquisition / fulfillment

| 表 | 必需列 | 主关系与约束 |
|---|---|---|
| `entitlement_product` | `product_id`, `site_id`, `key`, `name`, `status`, `generation` | `UNIQUE(product_id,site_id)`、`UNIQUE(site,key)` |
| `entitlement_offer` | `offer_id`, `product_id`, `site_id`, `key`, `status`, `current_revision_id?`, `generation` | `UNIQUE(offer_id,site_id)`；composite FK product/site；product+key UNIQUE；current revision same offer |
| `entitlement_offer_revision` | `offer_revision_id`, `offer_id`, `site_id`, `revision`, `billing_kind(one_time|recurring)`, `published_at?` | composite FK offer/site；candidate keys含 revision/site、revision/billing kind；immutable |
| `entitlement_price` | `price_id`, `offer_revision_id`, `billing_kind`, `currency`, `amount_minor`, `interval?`, `interval_count?` | composite FK revision/billing kind；`UNIQUE(offer_revision_id,currency)`；row CHECK 实现 one_time/recurring interval pairing；非负 |
| `entitlement_benefit` | `benefit_id`, `offer_revision_id`, `kind(credit|entitlement|subscription)`, `quantity`, `configuration` | FK revision；typed configuration + schema version |
| `entitlement_redemption_campaign` | `campaign_id`, `site_id`, `offer_revision_id`, `name`, `starts_at`, `ends_at?`, `status`, `generation` | `UNIQUE(campaign_id,site_id)`；composite FK offer revision/site；valid interval |
| `entitlement_redemption_code` | `code_id`, `site_id`, `campaign_id`, `code_hash`, `max_redemptions`, `redeemed_count`, `status`, `generation` | `UNIQUE(code_id,site_id)`；composite FK campaign/site；hash UNIQUE；counter bounds |
| `entitlement_redemption_attempt` | `attempt_id`, `receipt_id`, `code_id`, `site_id`, `principal_id`, `organization_id`, `status`, `acquisition_id?` | receipt UNIQUE/FK；composite FK principal/org/site；campaign offer同site；code row lock |
| `entitlement_acquisition` | `acquisition_id`, `site_id`, `organization_id`, `offer_revision_id`, `source_kind(redemption|payment|admin_grant)`, `source_ref`, `fact_digest`, `occurred_at` | `UNIQUE(acquisition_id,site_id,organization_id)`；composite FK org/offer与site；source identity UNIQUE |
| `entitlement_fulfillment` | `fulfillment_id`, `acquisition_id`, `site_id`, `organization_id`, `command_digest`, `state`, `committed_at?`, `reconciliation_reason?` | `UNIQUE(fulfillment_id,site_id,organization_id)`；composite FK acquisition/site/org；acquisition UNIQUE |
| `entitlement_fulfillment_reversal` | `fulfillment_reversal_id`, `original_fulfillment_id`, `site_id`, `organization_id`, `source_kind(payment_reversal|admin_reversal)`, `source_ref`, `fact_digest`, `state`, `occurred_at` | `UNIQUE(fulfillment_reversal_id,site_id,organization_id)`；composite FK original fulfillment；source identity UNIQUE |
| `entitlement_grant` | `entitlement_grant_id`, `fulfillment_id`, `site_id`, `organization_id`, `key`, `scope`, `starts_at`, `ends_at?`, `revoked_by_reversal_id?` | composite FK fulfillment/site/org 与 reversal/site/org；grant payload immutable，仅允许 revocation pointer 从 NULL 单向写入一次；不自引用 |
| `entitlement_subscription_term` | `subscription_term_id`, `fulfillment_id`, `site_id`, `organization_id`, `product_id`, `starts_at`, `ends_at`, `renewal_source_ref?`, `revoked_by_reversal_id?` | composite FK fulfillment/reversal与site/org；product 必须同 site；valid interval |
| `entitlement_usage_price_revision` | `usage_price_revision_id`, `site_id`, `revision`, `effective_from`, `effective_to?`, `published_at` | `UNIQUE(usage_price_revision_id,site_id)`、`UNIQUE(site_id,revision)`；`effective_to IS NULL OR effective_to > effective_from`；site-level immutable rate-card header |
| `entitlement_usage_price_rate` | `usage_price_rate_id`, `usage_price_revision_id`, `feature_key`, `model_revision_id`, `input_micros_per_million`, `output_micros_per_million`, `cached_micros_per_million` | `UNIQUE(price_revision,feature_key,model_revision)`；非负；一次 run 可有多 feature/model line |

### 8.2 Credit

| 表 | 必需列 | 主关系与约束 |
|---|---|---|
| `entitlement_credit_account` | `credit_account_id`, `site_id`, `organization_id`, `status`, `available_micros`, `held_micros`, `next_journal_seq`, `generation` | UNIQUE `(account,site)` 与 `(account,site,org)`；org UNIQUE；journal seq under row lock |
| `entitlement_credit_grant` | `credit_grant_id`, `credit_account_id`, `site_id`, `organization_id`, `fulfillment_id?`, `source_kind`, `source_ref`, `amount_micros`, `remaining_micros`, `expires_at?`, `revoked_by_reversal_id?` | `UNIQUE(grant_id,account_id)`；same-tenant composite FKs；source UNIQUE；remaining bounds |
| `entitlement_credit_journal` | `journal_id`, `credit_account_id`, `account_seq`, `credit_grant_id?`, `hold_id?`, `entry_kind`, `amount_micros`, `receipt_id`, `line_no`, `balance_after_micros`, `occurred_at` | optional `(grant,account)`/`(hold,account)` composite FK + paired-null CHECK；account+seq、receipt+line UNIQUE |
| `entitlement_credit_hold` | `hold_id`, `site_id`, `credit_account_id`, `usage_authorization_ref`, `execution_ref`, `usage_price_revision_id`, `amount_micros`, `status`, `expires_at`, `generation` | UNIQUE `(hold,account)` 与 `(hold,account,price_revision)`；same-site account/price FKs；无 Agent FK |
| `entitlement_credit_hold_allocation` | `allocation_id`, `credit_account_id`, `hold_id`, `credit_grant_id`, `reserved_micros`, `captured_micros`, `released_micros` | composite FK `(hold,account)` 与 `(grant,account)`；`UNIQUE(hold,grant)`；终态守恒 |
| `entitlement_usage_settlement` | `settlement_id`, `agent_run_usage_id`, `credit_account_id`, `hold_id`, `usage_price_revision_id`, `amount_micros`, `status`, `occurred_at` | composite FK `(hold,account,price_revision)`；run usage UNIQUE；exact replay |
| `entitlement_command_receipt` | `receipt_id`, `organization_id`, `command_id`, `command_kind`, `request_digest`, `status`, `result_ref?` | `(organization,command)` UNIQUE；all owner command replay authority |
| `entitlement_outbox` | `outbox_id`, `aggregate_kind`, `aggregate_id`, `effect_kind`, `command_id`, `payload`, `attempt`, `next_attempt_at`, `completed_at?` | command/effect UNIQUE；external notification/reversal delivery |

Credit account balance 是 journal projection；Grant 保留来源与过期证据。现有 bucket 算法可作为 grant
选择/余额 projection 实现继续使用，但不能再把三个 mutable bucket 当唯一账务真相。

Hold 进入 captured/released/expired 终态时，数据库负向测试必须证明 allocation 总和满足
`SUM(captured_micros + released_micros) = SUM(reserved_micros)`。实际 cost 大于 reserved 时首发直接
`reconciliation_required` 并拒绝静默少扣；不自动超额扣款。后续若要 top-up，必须以新的 command
在 account lock 下增加 hold/allocation/journal，再结算原 run usage。

Usage rate-card 的生效窗口统一为 `[effective_from,effective_to)`。Root baseline 启用 `btree_gist`，对已发布
revision 建立 `EXCLUDE USING gist (site_id WITH =, tstzrange(effective_from,effective_to,'[)') WITH &&)`，
同一 Site 任一时刻最多命中一张 rate-card；`AuthorizeUsage` 在零命中或多命中时 fail closed，不按发布时间猜测。

## 9. Payment

| 表 | 必需列 | 主关系与约束 |
|---|---|---|
| `payment_provider_account` | `provider_account_id`, `site_id`, `provider`, `key`, `secret_handle_ref`, `webhook_secret_handle_ref`, `configuration`, `status`, `generation` | FK Site；`UNIQUE(provider_account_id,site_id)`、`UNIQUE(site_id,provider,key)`；provider secret/config authority；不存明文 secret |
| `payment_command_receipt` | `receipt_id`, `organization_id`, `command_id`, `command_kind`, `request_digest`, `status`, `result_ref?`, `result_payload?` | `UNIQUE(organization_id,command_id)`；same digest replay/different digest conflict |
| `payment_customer_binding` | `binding_id`, `site_id`, `organization_id`, `provider_account_id`, `provider_customer_ref` | composite FK org/site 与 provider-account/site；`UNIQUE(organization_id,provider_account_id)` 与 `UNIQUE(provider_account_id,provider_customer_ref)` |
| `payment_checkout` | `checkout_id`, `receipt_id`, `site_id`, `organization_id`, `principal_id`, `offer_revision_id`, `price_id`, `amount_minor`, `currency`, `mode`, `provider_account_id`, `provider_session_ref?`, `state`, `expires_at`, `generation` | receipt UNIQUE/FK；checkout/site/org/account candidate；account+provider session partial UNIQUE；price/revision+same-site FKs |
| `payment_provider_event` | `provider_event_id`, `site_id`, `provider_account_id`, `external_event_ref`, `event_type`, `payload_digest`, `payload`, `state`, `received_at` | composite FK provider-account/site；`UNIQUE(provider_account_id,external_event_ref)`；same digest replay/drift reject |
| `payment_settlement` | `settlement_id`, `checkout_id?`, `site_id`, `organization_id`, `provider_account_id`, `object_kind`, `external_object_ref`, `amount_minor`, `currency`, `offer_revision_id`, `fact_digest`, `acquisition_ref?`, `state`, `occurred_at` | composite FK checkout/site/org/provider account；`UNIQUE(settlement_id,provider_account_id)`；account+kind+object UNIQUE |
| `payment_provider_subscription` | `provider_subscription_id`, `site_id`, `organization_id`, `provider_account_id`, `external_subscription_ref`, `offer_revision_id`, `state`, `cancel_at_period_end`, `current_period_start`, `current_period_end`, `observed_at`, `generation` | `UNIQUE(provider_subscription_id,provider_account_id)`；composite FK org/offer与site；account+external ref UNIQUE；current snapshot |
| `payment_subscription_period` | `period_id`, `provider_subscription_id`, `provider_account_id`, `external_invoice_ref`, `period_start`, `period_end`, `amount_minor`, `currency`, `settlement_id?`, `observed_at` | composite FK subscription/account 与 optional settlement/account；account+invoice UNIQUE；append-only |
| `payment_reversal` | `reversal_id`, `settlement_id`, `site_id`, `provider_account_id`, `kind(refund|dispute)`, `external_reversal_ref`, `amount_minor`, `currency`, `fact_digest`, `state`, `occurred_at` | composite FK settlement/provider-account/site；account+kind+external ref UNIQUE；append-only |
| `payment_outbox` | `outbox_id`, `aggregate_kind`, `aggregate_id`, `effect_kind`, `command_id`, `payload`, `attempt`, `next_attempt_at`, `completed_at?` | command/effect UNIQUE；provider/Entitlement effect after commit |

Payment 只写 payment 表和 acquisition outbox；Entitlement 根据 `payment_settlement` 的 stable source ref 创建
Acquisition/Fulfillment。Payment 不写 Credit、SubscriptionTerm 或 Entitlement。

## 10. Owner / writer / reader matrix

| 表前缀 | 唯一 writer | 主要写命令 | 允许 reader |
|---|---|---|---|
| `iam_*` | IAM | login/rotate/revoke/invite/member/role/admin identity | Web BFF、Site/Chat/Entitlement 仅经 IAM RPC；Root audit fixture |
| `site_*` | Site | create/activate/domain/brand/feature | Web、IAM、Chat、Catalog 经 Site RPC |
| `chat_*` | Chat | Conversation/Submit/Control/project Agent fact（projection） | Web 经 HTTP；Agent 只经 RPC ack/read，不直写 |
| `agent_*` | Agent | launch/claim/control/event/effect/usage | Chat/Entitlement 经 RPC/stream；不直写 |
| `capability_*` | Capability | publish/install/grant/connect/snapshot | Agent/Web/Admin 经 RPC |
| `model_*` | Model | publish/policy/resolve | Agent/Web/Admin 经 RPC；Agent 只保存 selected revision ref |
| `storage_*` | Storage | upload/scan/promote/artifact/share/GC | Chat/Agent/Web/Capability 经 RPC |
| `entitlement_*` | Entitlement | catalog/redeem/acquire/fulfill/grant/hold/settle | Web/Agent/Payment/Admin 经 RPC |
| `payment_*` | Payment | checkout/provider-event/settlement/subscription/reversal | Web/Entitlement/Admin 经 RPC |

“同一个数据库”不等于允许跨仓直接 UPDATE。跨仓 FK 由 Root baseline 保护；跨仓业务读取和命令通过
RPC。只有 Root migration/test fixture 能跨 owner 写测试数据。

### 10.1 逐表 writer catalog

下面所有表的 DDL owner 都是 Root。`Writer` 固定表示唯一 owner repository / aggregate gateway，不是
发起命令的 component 名；其他 repo 即使持有同一 `kokoro_app` 凭据，也只能经 RPC 消费。
`Command / transaction` 列列出获准调用该 gateway 的 application command 与状态 transition。若同一行
分阶段更新，只允许表中明确列出的字段/状态：Chat message placeholder→projected、Interaction
pending→resolved、Agent Run preparing→queued→running→terminal、Credit Grant remaining/revocation。
Readers 是业务 reader，不含 Root fixture/audit。

#### IAM / Site

| Table | Writer | Command / transaction | Readers | Lock、retention |
|---|---|---|---|---|
| `iam_principal` | IAM Identity | Provision/Disable/DeletePrincipal | 所有需要验证 principal 的 owner 经 IAM RPC | site/control-plane scope immutable；deleted 后 PII erase，RESTRICT |
| `iam_user` | IAM Identity | Provision/Update/DeletePrincipal | Web/Admin | principal PK/FK；PII erase |
| `iam_identity` | IAM Authentication | Bind/ConsumeLoginIdentity | IAM Auth/Admin | site+issuer+subject UNIQUE；revoke/retain |
| `iam_contact` | IAM Identity | Verify/ReplaceContact | Web/Admin | verified contact uniqueness；PII erase |
| `iam_credential` | IAM Authentication | Register/RevokeCredential | IAM Auth only | credential CAS；retention hard-delete |
| `iam_magic_link` | IAM Authentication | Issue/ConsumeMagicLink | IAM Auth only | token UNIQUE；consume row CAS；ephemeral retention |
| `iam_auth_session` | IAM Authentication | Login/Rotate/RevokeSession | Web BFF/IAM Admin | token UNIQUE；family lock；ephemeral retention |
| `iam_command_receipt` | IAM Application | IAM mutating commands | Web BFF/Admin | command UNIQUE+digest；retain through replay window |
| `iam_organization` | IAM Organization | Create/DisableOrganization | Site/Chat/Entitlement via IAM | site+personal owner claim；lifecycle RESTRICT |
| `iam_membership` | IAM Organization | Add/Remove/TransferOwner | IAM AuthZ/Web | same-site composite FK；org+principal UNIQUE；org lock |
| `iam_role` | IAM Authorization | PublishRole | IAM AuthZ/Admin | site/org scoped key UNIQUE；referenced roles RESTRICT |
| `iam_permission` | IAM Authorization | SeedPermissionCatalog | IAM AuthZ/Admin | key UNIQUE；append/disable |
| `iam_role_permission` | IAM Authorization | PublishRole | IAM AuthZ | role+permission UNIQUE；role-owned replace transaction |
| `iam_membership_role` | IAM Authorization | AssignMembershipRole | IAM AuthZ/Web | same-organization composite FK；membership+role UNIQUE |
| `iam_principal_role` | IAM Authorization | AssignSite/OrganizationRole | IAM AuthZ/Admin | site/org scope CHECK；principal+role+scope claim |
| `iam_operator_site_role` | IAM Authorization | AssignOperatorSiteRole | IAM AuthZ/Admin | control-plane operator + target site/role composite FK；scopeSites 行化 |
| `iam_invite` | IAM Organization | Invite/Accept/Revoke | Web/Admin | token UNIQUE；org lock；expiry retention |
| `iam_service_account` | IAM Organization | Create/Rotate/RevokeServiceAccount | Admin/internal auth | principal PK；secret CAS；PII-free retain |
| `iam_security_event` | IAM Audit Store | Any IAM security transaction | Admin/audit export | typed principal/target Site scope；append-only retention |
| `site_site` | Site Core | Create/Activate/SuspendSite | Web/IAM/Chat/Entitlement | product-surface root；generation CAS；lifecycle RESTRICT |
| `site_domain` | Site Domain | Add/Verify/PromoteDomain | Web/IAM redirect | host UNIQUE；site lock；lifecycle |
| `site_brand` | Site Brand | PublishBrand | Web | site+revision UNIQUE；published append-only |
| `site_feature` | Site Feature | SetFeature | Web/owner services | site+key UNIQUE；generation CAS |

#### Chat / Agent

| Table | Writer | Command / transaction | Readers | Lock、retention |
|---|---|---|---|---|
| `chat_conversation` | Chat Conversation | Create/Rename/Archive/TrashConversation | Web | org/site/actor composite FK；opaque namespace；generation CAS；retention policy |
| `chat_message` | Chat Message Store | SubmitMessage/ProjectAgentEvent | Web snapshot | conversation+ordinal UNIQUE；identity immutable；仅 placeholder→projected |
| `chat_message_part` | Chat Message Store | SubmitMessage/ProjectAgentEvent | Web snapshot | message+ordinal UNIQUE；part generation CAS |
| `chat_command_receipt` | Chat Application | Every Chat command | Web/BFF | org+command UNIQUE + digest；conversation result 可后填且 composite FK |
| `chat_run_launch` | Chat Run | SubmitMessage/RecordAdmission | Web/Chat recovery | message FK；generation CAS；terminal retain |
| `chat_active_run` | Chat Run | Submit/Terminal | Chat submit/recovery | conversation PK + launch UNIQUE；insert/delete lock |
| `chat_run_view` | Chat Projector | ProjectAgentEvent | Web snapshot | agent run PK；epoch/seq monotonic |
| `chat_interaction` | Chat Interaction Store | ProjectAgentEvent/DecideInteraction | Web | action digest/schema/payload immutable；generation CAS；仅 pending→terminal |
| `chat_control_command` | Chat Control | DecideInteraction/Cancel/Steer | Web/reconciler | receipt UNIQUE；interaction lock；digest 归 owner receipt |
| `chat_control_outbox` | Chat Control worker | DecideInteraction/PublishControl | Chat worker | control UNIQUE；at-least-once; retain until ack+window |
| `chat_launch_outbox` | Chat Launch worker | SubmitMessage/PublishLaunch | Chat worker | launch UNIQUE；at-least-once until Agent accepted |
| `chat_projection_inbox` | Chat Projector | IngestAgentEvent | Projector/recovery | event/producer seq UNIQUE；insert claim |
| `chat_projection_dlq` | Chat Projection Store | Quarantine/RepairEvent | Admin/recovery | inbox UNIQUE；repair generation |
| `chat_stream_event` | Chat Stream Store | Any browser-visible transaction | Web SSE | conversation seq/event UNIQUE；只保留 snapshot watermark 后的 bounded tail |
| `chat_share` | Chat Share | Create/RevokeShare | Web/public snapshot | token UNIQUE；active-per-conversation partial UNIQUE；expiry/revoke |
| `agent_execution_manifest` | Agent Admission | FinalizeAdmission | GA execution/audit | run/digest UNIQUE；namespace composite FK；append-only |
| `agent_run` | Agent Run Store | ClaimLaunch/FinalizeAdmission/Start/Terminal | Chat/Entitlement via RPC | launch UNIQUE；nullable manifest only preparing/admission_failed；明确状态 fence |
| `agent_run_lease` | Agent Supervisor | Claim/Renew/ReleaseRun | Agent worker only | run PK；token+generation CAS；ephemeral after terminal |
| `agent_control_inbox` | Agent Control Store | ApplyControl | Agent execution | run+command UNIQUE+digest；retain with run |
| `agent_event_outbox` | Agent Execution | EmitRunEvent | Publisher/Chat via stream | run+global seq UNIQUE；epoch fence；ack watermark retention |
| `agent_dispatch_outbox` | Agent Run Store | LaunchRun/DispatchRun | Agent worker | run UNIQUE；at-least-once dispatch until claim |
| `agent_projection_ack` | Agent Ack service | AckProjection | Agent recovery | run+consumer PK；projected epoch fence + global seq monotonic watermark |
| `agent_tool_effect` | Agent Tool runtime | Claim/CommitToolEffect | Agent recovery/audit | tool effect UNIQUE；append/terminal |
| `agent_run_usage` | Agent Execution | FinalizeRunUsage | Entitlement settlement | run UNIQUE；terminal aggregate；唯一 billable usage authority |
| `agent_run_usage_line` | Agent Execution | FinalizeRunUsage | Entitlement settlement/audit | run usage+model+feature UNIQUE；append-only aggregate line |
| `agent_sandbox_binding` | Agent Sandbox | Bind/CloseSandbox | Agent recovery/Storage | one live/run；generation CAS |
| `agent_memory` | Agent Memory Store | Put/Delete/ExpireMemory | GA only | namespace+key UNIQUE；generation + expires_at retention |
| `agent_dispatch_dlq` | Agent Supervisor | Quarantine/RepairDispatch | Admin/recovery | append-only evidence + repair state |

#### Capability / Model / Storage

| Table | Writer | Command / transaction | Readers | Lock、retention |
|---|---|---|---|---|
| `capability_skill` | Capability Skill | Create/Publish/DeleteSkill | Web/Agent resolve | official/org/project scoped name claims；local-over-official |
| `capability_package` | Capability Package | ValidatePackage | Skill publish/Agent materializer | hash UNIQUE；Storage blob FK；append-only |
| `capability_skill_revision` | Capability Skill | PublishSkillRevision | Agent/Web/Admin | skill+revision UNIQUE；published immutable |
| `capability_installation` | Capability Install | Install/Restore/RemoveSkill | Web/Agent resolve | partial project+skill live UNIQUE；generation |
| `capability_grant` | Capability Grant | Grant/RevokeCapability | Agent resolve/Web | target CHECK；project lock；append/revoke |
| `mcp_server` | MCP registry | Create/Publish/DeleteMcp | Web/Agent resolve | official/org/project scoped name claims；local-over-official |
| `capability_mcp_revision` | Capability MCP | PublishMcpRevision | Agent/Admin | server+revision UNIQUE；published immutable |
| `capability_mcp_connection` | Capability MCP | Connect/Verify/Disconnect | Agent resolve/Web | partial project+server live UNIQUE；same-scope secret composite FK |
| `capability_secret_handle` | Capability Secret | Put/Rotate/RevokeSecret | MCP runtime only | org/project scoped handle/name claim；ciphertext retention |
| `capability_runtime_snapshot` | Capability Resolver | ResolveRuntimeSnapshot | Agent admission/audit | target scope+digest UNIQUE；Slice A 为 `organization_id+scope_key+digest`；append-only；empty snapshot valid |
| `capability_runtime_snapshot_item` | Capability Resolver | ResolveRuntimeSnapshot | Agent admission | snapshot item UNIQUE；append-only |
| `capability_command_receipt` | Capability Application | ResolveRuntimeSnapshot（Slice A）；后续 Publish/Install/Grant | Agent admission；后续 Web/Admin | command UNIQUE+digest；same digest replay、drift conflict、result snapshot ref retention |
| `model_provider` | Model Control | Create/DisableProvider | Agent resolve/Admin | key UNIQUE；generation/lifecycle |
| `model_definition` | Model Control | Create/PublishModel | Agent/Web/Admin | key UNIQUE；generation/lifecycle |
| `model_revision` | Model Control | PublishModelRevision | Agent/LiteLLM config/Admin | model+revision UNIQUE；published immutable |
| `model_routing_policy` | Model Control | SetRoutingPolicy | Agent ResolveModel/Web | site+label+priority claim；generation |
| `model_provider_health_state` | Model Control/Health | BootstrapModelCatalog（Slice A unknown）/ ProjectProviderHealth（future） | Model resolver/Admin | provider PK；generation CAS；fallback current state |
| `model_provider_health_observation`（future health slice） | Model Health | RecordProviderProbe | Model health projector/Admin | append-only probe evidence；不在 Slice A inventory |
| `storage_blob` | Storage Blob | Commit/DeleteBlob | Capability/Asset/Artifact | hash+size and backend+object-key UNIQUE；FK blocks GC |
| `storage_upload_session` | Storage Upload | Begin/Complete/ExpireUpload | Web/worker | project or approved internal-purpose scope；generation/expiry |
| `storage_asset` | Storage Asset | FinalizeUpload/Promote/RejectAsset | Chat/Web/Agent | org/project FK；generation state machine |
| `storage_scan` | Storage Scanner | RecordScan | Asset promoter/Admin | evidence identity claim；append-only |
| `storage_artifact` | Storage Artifact | Create/Publish/ArchiveArtifact | Chat/Web/Agent | org/project FK；generation/lifecycle |
| `storage_artifact_revision` | Storage Artifact | PublishArtifactRevision | Chat/Web/download | artifact+revision UNIQUE；append-only |
| `storage_share` | Storage Share | Create/RevokeShare | public download/Web | token UNIQUE；expiry/revoke retention |
| `storage_command_receipt` | Storage Application | Upload/Artifact/Share commands | Web/Agent | command UNIQUE+digest；replay retention |
| `storage_outbox` | Storage worker | Scan/Object/GC effects | Storage worker | command+effect UNIQUE；at-least-once retention |

#### Entitlement / Payment

| Table | Writer | Command / transaction | Readers | Lock、retention |
|---|---|---|---|---|
| `entitlement_product` | Entitlement Catalog | Create/DisableProduct | Web/Admin | site+key UNIQUE；generation |
| `entitlement_offer` | Entitlement Catalog | Create/DisableOffer | Web/Admin | product+key UNIQUE；generation |
| `entitlement_offer_revision` | Entitlement Catalog | PublishOfferRevision | Web/Payment/Fulfillment | offer+revision UNIQUE；published immutable |
| `entitlement_price` | Entitlement Catalog | PublishOfferRevision | Web/Payment | offer revision FK；billing CHECK；immutable |
| `entitlement_benefit` | Entitlement Catalog | PublishOfferRevision | Fulfillment/Web | revision FK；typed config；immutable |
| `entitlement_redemption_campaign` | Entitlement Redemption | Create/DisableCampaign | Web/Admin | site 由 offer revision 推导；generation |
| `entitlement_redemption_code` | Entitlement Redemption | Issue/Redeem/RevokeCode | Redemption only | hash UNIQUE；row lock counter；secret retention |
| `entitlement_redemption_attempt` | Entitlement Redemption | Redeem | Web/Admin/reconcile | receipt UNIQUE；append terminal |
| `entitlement_acquisition` | Entitlement Acquisition | Redeem/AcceptPayment/AdminGrant | Fulfillment/Admin | source kind+ref UNIQUE；append-only |
| `entitlement_fulfillment` | Entitlement Fulfillment | FulfillAcquisition | Web/Admin | acquisition UNIQUE；receipt/fence；terminal |
| `entitlement_fulfillment_reversal` | Entitlement Fulfillment | ReverseFulfillment | Web/Admin/Payment reconcile | source kind+ref UNIQUE；original fulfillment FK；append-only |
| `entitlement_grant` | Entitlement Grant Store | Fulfill/ReverseFulfillment | IAM/Web/authorization | immutable payload + one-way terminal reversal pointer |
| `entitlement_subscription_term` | Entitlement Fulfillment | Fulfill/Reverse/RenewTerm | Web/authorization | period CHECK；explicit reversal FK |
| `entitlement_usage_price_revision` | Entitlement Pricing | PublishUsagePriceRevision | Agent admission/Admin | site+revision UNIQUE；immutable rate-card header |
| `entitlement_usage_price_rate` | Entitlement Pricing | PublishUsagePriceRevision | Agent admission/settlement | revision+feature+model UNIQUE；nonnegative rates |
| `entitlement_credit_account` | Entitlement Credit | Ensure/Authorize/SettleCredit | Web/Agent/Admin | org UNIQUE；account row lock；generation |
| `entitlement_credit_grant` | Entitlement Credit Store | Grant/Revoke/ExpireCredit（Fulfillment 是授权 caller） | Credit allocator/Web | source UNIQUE；remaining bounds；explicit reversal FK；row lock |
| `entitlement_credit_hold` | Entitlement Credit | Authorize/Settle/ReleaseUsage | Agent/recovery | authorization UNIQUE；same-site account/price；account lock/CAS |
| `entitlement_credit_hold_allocation` | Entitlement Credit | Authorize/Settle/ReleaseUsage | Credit audit | hold+grant UNIQUE；sum CHECK；rows locked |
| `entitlement_credit_journal` | Entitlement Credit | Any credit mutation | Web/Admin/audit | account+seq and receipt+line UNIQUE；多 grant 分录；append-only |
| `entitlement_usage_settlement` | Entitlement Credit | SettleUsage | Agent/Admin | agent run usage UNIQUE；frozen price revision；append terminal |
| `entitlement_command_receipt` | Entitlement Application | Redeem/Fulfill/Credit commands | Web/Agent/Payment | org+command UNIQUE+digest；replay retention |
| `entitlement_outbox` | Entitlement worker | Reversal/notification effects | Entitlement worker | command+effect UNIQUE；at-least-once retention |
| `payment_provider_account` | Payment Provider | Configure/DisableProviderAccount | Payment/Admin | site+provider+key UNIQUE；secret handles；generation |
| `payment_command_receipt` | Payment Application | Checkout/Portal commands | Web/Admin | org+command UNIQUE+digest；replay/reconcile authority |
| `payment_customer_binding` | Payment Customer | EnsureCustomer | Web/Admin | org/account and account/customer claims |
| `payment_checkout` | Payment Checkout | Create/ReconcileCheckout | Web/Admin | receipt UNIQUE；generation/terminal retain |
| `payment_provider_event` | Payment Webhook | Accept/ProcessProviderEvent | Payment reconcile/Admin | account+event UNIQUE+digest；append evidence |
| `payment_settlement` | Payment Settlement | ProcessProviderEvent | Entitlement/Admin | account+kind+object UNIQUE；append-only |
| `payment_provider_subscription` | Payment Subscription | ObserveSubscription | Web/Admin | account+subscription UNIQUE；generation current mirror |
| `payment_subscription_period` | Payment Subscription | ObservePaidInvoice | Entitlement/Admin | account+invoice UNIQUE；append-only |
| `payment_reversal` | Payment Reversal | ObserveRefund/Dispute | Entitlement/Admin | account+kind+reversal UNIQUE；append-only |
| `payment_outbox` | Payment worker | Checkout/Settlement/Reversal side effects | Payment worker | command+effect UNIQUE；at-least-once retention |

### 10.2 Admin dual-control scope cut

当前 Admin `ApprovalRequest`/dual-control 语义不塞进 IAM，也不由 Admin Web 直接写业务表。本版 slice
inventory 只开放低风险/只读 Admin；现有危险 effect 算法与行为测试作为非执行参考暂不删除，但路由、
deployable 和旧数据库 authority 必须 zero-traffic。某个危险命令进入后续 slice 前，
必须在对应 owner 内明确加入 approval request、effect receipt/reconcile 与 append-only audit 表和事务，
再迁行为测试、开放 RPC、删除旧实现。该 owner-local schema 需要单独设计批准，不能用一个跨域 generic
approval 表代替。

## 11. Transaction matrix

| Command | Locked rows / claims | Written tables | Idempotency | After commit | Retry / reconcile |
|---|---|---|---|---|---|
| IAM `ConsumeMagicLink` | magic link token row；existing identity/contact | magic_link, principal/user/identity/contact, personal org/membership, auth_session, security_event, command_receipt | caller command + link token digest | sign session/JWT response | receipt re-read；consumed link cannot create second principal |
| IAM `RotateSession` | old auth session + family | old/new auth_session, security_event, command_receipt | rotation command + old token digest | sign JWT | receipt re-read；family revoke on replay drift |
| Chat `CreateConversation` | organization；organization-scoped receipt claim | receipt，随后 conversation + result；零 stream event | `(organization,command)` + digest | none | IAM 只 Authorize；receipt 在 conversation ID 产生前可 claim；重放返回同一 conversation/opaque namespace；watermark=0/current |
| Chat `SubmitMessage` | conversation active-run PK；owner receipt | receipt, user/assistant message+parts, run_launch, active_run, launch_outbox；首 Submit 3 条、后续 2 条 stream events | `(organization,command)` + digest（conversation及解析后的 `default/general` 选择进digest） | launch worker calls Agent | at-least-once launch；Agent run keyed by launch ID |
| Chat `RecordAdmissionFailure` | launch + active-run + assistant placeholder | launch failed, assistant failed, delete active_run, append synthetic browser `run.failed` | launch response digest + launch generation | none | `AGENT_ADMISSION_REJECTED` exact replay；duplicate/restart不重复 terminal event |
| Agent `ClaimLaunch` | launch identity claim | agent_run(state=preparing) | launch ID + launch request digest | idempotent RPC resolve Capability/Model；metered 时 Entitlement AuthorizeUsage | admission failure 把 run 终止为 admission_failed；不创建 manifest/outbox |
| Agent `FinalizeAdmission` | preparing run generation；resolved snapshot/revision/auth refs | execution_manifest, run(CAS→queued), dispatch_outbox | launch ID + canonical manifest digest | worker dispatch to Redis/internal queue | 同 digest 返回同 run；异 digest拒绝；finalize 失败时 release hold |
| Agent `Claim/FinalizeToolEffect` | run/tool effect identity；request digest claim | tool_effect claim，外部调用后 finalize result digest/status | run+tool_call+effect_kind + digest | claim commit 后才执行外部 effect | outcome unknown 由同 effect row reconcile；不把外部调用包进 EmitEvent事务 |
| Agent `EmitEvent` | run generation/terminal fence；event seq | event_outbox, run state；terminal 时 run_usage + usage_lines | event ID；run usage digest | Redis publish | retry until projection ack；terminal不能 revive；usage aggregate exact replay |
| Chat `ProjectAgentEvent` | inbox event claim；run view/message/interaction rows | projection_inbox or DLQ, run_view, message/part/interaction, stream_event | event ID + run-global producer seq；epoch fence | ack Agent projection | gap waits；旧 epoch 拒绝；schema error DLQ；same event replay |
| Chat `DecideInteraction` | interaction generation；owner receipt | receipt, control_command, interaction, control_outbox, stream_event | `(organization,command)` + digest（conversation/action进digest） | publish Agent control | retry until Agent control receipt |
| Storage `FinalizeUpload` | upload generation；blob hash claim | upload, blob, asset, command_receipt, outbox | command + content digest | scan worker/object verification | object/scan ambiguity reconciled by hash/key |
| Capability `PublishRevision` | skill/server generation；command claim | package, revision, current pointer, command_receipt | command + content/config hash | optional cache/materializer notification | Storage blob must already be ready；same revision replay |
| Entitlement `Redeem` | redemption code; org credit account；owner receipt | code counter, attempt, acquisition, fulfillment, grants/term/credit grant+journal, receipt | `(org,command)` + code/offer digest | optional notification outbox | attempt FK receipt；code limit under row lock |
| Entitlement `AuthorizeUsage` | published price revision；credit account + eligible grants | hold, hold_allocation, multi-line journal, receipt | usage authorization ref/execution ref + request digest | return hold + frozen usage price revision to Agent | 无 Agent FK；expired/rejected admission release idempotent |
| Entitlement `SettleUsage` | terminal run usage claim；hold/account/grant allocations；frozen rate rows | allocation capture/release, hold, grants, multi-line journal, usage_settlement, receipt | agent run usage ID + digest | none | missing terminal aggregate retryable；terminal hold replay exact |
| Payment `CreateCheckout` | owner receipt/checkout claim；offer price read | payment_command_receipt, checkout, payment_outbox | `(organization,command)` + frozen offer/price digest | provider call uses receipt-derived idempotency key | outcome unknown retrieves same provider session |
| Payment `AcceptWebhook` | provider event claim；checkout/subscription row | provider_event, checkout/subscription/period, settlement, payment_outbox | provider account+event ID + payload digest | deliver settlement source to Entitlement | transient dependency retry；semantic drift durable reject |
| Payment `RecordReversal` | provider-account reversal claim；settlement | reversal, settlement state, payment_outbox | provider account+kind+reversal ID + fact digest | call Entitlement `ReverseFulfillment` | Entitlement writes one fulfillment_reversal and idempotent inverse facts |

## 12. 当前持久化语义到 PostgreSQL 的映射

当前开发数据按 clean replace 丢弃；下表迁移的是**行为、不变量和测试**，不是在线双写或数据导入。

| Current source | Target | 必须复用的行为测试 / 裁决 |
|---|---|---|
| Session `sessions` | `chat_conversation`, `chat_active_run` | Conversation 直接属于 Organization；namespace 固定在 Conversation；active slot 改为 PK 行 |
| Session `session_seq_counters` | `chat_conversation.next_stream_seq`, `chat_stream_event` | transaction 内单调分配；session+seq unique |
| Session `messages` | `chat_message`, `chat_message_part` | identity/ordinal/status；content 拆 typed parts |
| Session `runs` 内 projection/decision ids | `chat_run_launch`, `chat_run_view`, `chat_interaction`, `chat_control_command` | terminal convergence；decision effectively-once |
| Session `pending_pauses` | `chat_interaction` | approval/question/review/input 分 kind；pending terminal cancellation |
| Session `session_events` | `chat_stream_event` | durable-first、event id/seq dedupe、SSE replay |
| Session `deliveries` | `storage_artifact_revision` + Chat typed artifact ref | 内容寻址保留；Session 不再拥有 library |
| Session `session_shares` | `chat_share`（Slice B 安装） | 保留 create/revoke/public snapshot、token hash、active-per-conversation 行为测试；不与 Artifact share 混用 |
| Session `run_dispatches` | `chat_launch_outbox`, `agent_run`, `agent_dispatch_outbox` | 删除 Agent/Session 共享 CAS collection |
| Session `control_outbox` | `chat_control_outbox`, `agent_control_inbox` | recorded→published→applied；跨仓各写自己的表 |
| Session `run_event_receipts` | `chat_projection_inbox` | event id + producer seq identity |
| Session `run_receipt_manifests` | `agent_projection_ack` + Chat run cursor fields | run-global projected watermark 单调；epoch 只作 fence；不再字段级双写 |
| Session `billing_journal` | `entitlement_credit_hold`, allocation, journal, usage settlement | saga 行为迁 owner；Chat 无 billing 表；Slice A 显式 unmetered |
| Agent Mongo run ledger | `agent_run`, manifest, lease, control, event outbox, tool effect, run usage/lines, sandbox binding | supervisor/fence/outbox/control/effect/usage behavior suite 原样跑新 adapter |
| Agent Mongo checkpoint/writes | LangGraph PostgreSQL checkpointer standard tables | 使用官方 saver/store；不手写第二套 checkpoint |
| Agent `kokoro_agent_memory` | `agent_memory` | namespace+key、version、TTL/retention |
| Agent `dispatch_dlq` | `agent_dispatch_dlq` | quarantine/repair evidence |
| Hub `skills/skill_state/skill_revisions` | capability skill/package/revision/installation/grant | package/hash/quota/revision tests；current pointer 与 revision 同事务 |
| Hub `mcp_servers/mcp_server_revisions/mcp_secrets` | capability MCP/revision/connection/secret/grant | config hash、AES-GCM、SSRF、CAS/revision tests |
| 六份 MySQL Prisma schemas | Site/IAM/Model/Entitlement/Payment tables | 保留 PaymentProvider 为 provider account、Model health/fallback、Credit/Payment idempotency；迁 behavior tests，不迁开发数据 |

删除 Mongo/MySQL adapter 前，每一行至少有一个 PostgreSQL behavior test 和一个 zero-call gate。

## 13. 由数据反推边界

边界判定采用三个条件：共同不变量、共同事务、唯一 writer。由上面的关系和 transaction matrix 得到：

1. User/Identity/Auth/Organization/Role/Permission 共享 session/member/role 不变量和安全事务，形成 IAM。
2. Conversation/Message/RunView/Interaction 共享 create/submit/project/control 事务，形成 Chat；Project 分组与 Branch 都是后续可选能力。
3. Agent run/lease/event/effect/usage 共享执行 fence，形成 Agent；Catalog/Model 不进入这笔事务。
4. Skill 与 MCP 共享 revision/grant/runtime snapshot，形成 Capability；Blob bytes 由 Storage 写。
5. Model 只拥有 catalog/revision/routing；provider invocation 继续在 GA/LiteLLM，避免重写成熟路径。
6. Blob/Upload/Asset/Scan/Artifact 共享 promotion/retention，形成 Storage。
7. Catalog/Redemption/Acquisition/Fulfillment/Entitlement/Credit 共享幂等发放事务，形成 Entitlement。
8. Checkout/ProviderEvent/Settlement/Subscription/Reversal 共享外部 money fact 与 reconciliation，形成 Payment。

因此能力子仓不是先拍脑袋列十个名字；它们是上述表组和原子事务的代码 ownership 结果。
