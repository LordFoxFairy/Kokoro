# Kokoro Capability × Storage 最终技术方案

状态：**Storage v1 与 Capability v1 正式方案**，2026-08-27

> **阅读边界：**Storage 的 Asset/Artifact lifecycle、scan 与 S3-compatible ObjectStore 分层，以及 Capability 的
> Skill source、Connector、MCP control-plane 是当前 v1 owner 设计。历史 `ResolveRuntimeSnapshot`、
> `revision`、`agent_namespace` 和 Capability immutable snapshot 已从 Capability v1 源码与 MySQL baseline 移除，
> 仅 Root descriptor 在迁移期保留，**不是** Feature-first GA 的 runtime input。GA target 以
> [33 GA SkillRuntime](33-ga-first-skill-runtime-architecture.md)、
> [36 总体 Agent 方案](36-ga-final-agent-technical-plan.md) 与
> [ADR-022](../decisions/ADR-022-run-execution-attestation-and-dynamic-capability-resolution.md) 为准：GA default Skill 直接运行；
> subject/session Skill（personal subject 即用户，project/service subject 即共享主体）仅经 `find_skills/load_skill` 的按需 public path 读取；没有 Capability runtime snapshot、Skill version/release 或
> Session binding。

本文件只定义 `kokoro-capability` 与 `kokoro-storage` 的边界、数据 owner、对象存储策略、运行流程和验收标准。Agent、Session、Hub 的首发实现各自建立唯一目标路径；本文件不改写它们的内部实现。

## 1. 架构结论

```text
Capability v1 public surfaces
  ├─ owns capability metadata / authorization / installation / source reads
  └─ consumes Root Storage contract
         │
         ▼
Storage
  ├─ owns upload / blob / asset / scan / artifact lifecycle
  ├─ MySQL: structured final truth and command receipt
  ├─ Redis: runtime admission/liveness gate (fail closed)
  └─ ObjectStore port
         └─ S3-compatible adapter
              ├─ local MinIO (default integration profile)
              ├─ AWS S3
              └─ Ceph RGW / compatible providers
```

核心原则：

1. Storage 是业务 bounded context，不是数据库 wrapper 或 S3 SDK wrapper。
2. Capability 不访问 Storage 的数据库、Mongo collection、Redis key 或 bucket。
3. ObjectStore 保存 bytes；MySQL 保存生命周期最终状态、扫描结果和 report identity；Storage v1 不依赖 MongoDB。
4. Redis 不是最终真相；Redis 不可用时 Storage/Capability 相关新 command fail closed。v1 持久幂等 receipt 由各自 owner 的 MySQL 保存。
5. ObjectStore 中存在对象，不代表业务上传已经完成。
6. 完整生命周期 v1 包含 upload/status/abort、asset、scan、artifact draft/final 和 download reference；multipart、删除策略和批量查询属于后续增量。

## 2. 责任边界

### 2.1 kokoro-storage owns

```text
upload admission and completion
object key allocation
blob metadata
asset identity and visibility
scan state and report reference
artifact draft/final lifecycle
content hash / size verification
short-lived upload/download reference
command receipt and final idempotency
```

### 2.2 kokoro-storage doesNotOwn

```text
IAM identity and authorization master data
Capability policy、Skill/MCP metadata 与 installation policy
Session snapshot/event/replay
Agent checkpoint/memory/execution event
Model/Credit/Payment
MongoDB-owned Session/Agent documents and runtime state
```

### 2.3 当前 `kokoro-capability` v1 拥有

```text
Skill/MCP metadata
installation and authorization
storage_asset_id + content_digest business association
Capability command receipt
```

### 2.4 Feature-first GA target：CA 是动态 source owner，不是 runtime snapshot owner

GA runtime 与 Capability 的稳定分工如下：

```text
GA
  default Skill / Agent policy / candidate index / find_skills + load_skill
  loaded Skill -> GA workbench -> DeepAgents context

Capability
  subject/session Skill logical path / current visibility / CRUD / source locator

Storage
  controlled package bytes / checksum / scan / Asset lifecycle
```

Capability target 不向 GA 返回完整 snapshot、Agent/Tool/MCP 配方、`revision`、release/connection policy，且不接收 GA
`RuntimeNamespace`、checkpoint key 或 caller-selected namespace。内容 digest 只作为 Storage bytes 的完整性验证；它不是 Skill
发布版本。GA `DefaultSkillCatalog` 只拥有 default/mounted `SkillSummary`；动态 `SkillRankingIndex` 只可保存按
`RuntimeNamespace + exact session_id + summary_fingerprint` 分区的排序词项/向量分数。每次 external `find_skills` 都调用
`DiscoverVisibleSkillPaths` 取得本次 current `VisibleSkillSummary`，ranker 只能对其中仍存在的 candidate 排序；cache 不可单独
产生候选、展示 metadata、决定可见性或加载，`load_skill` 仍 resolve/read 重验。

目标 public calls 的语义是：

```text
DiscoverVisibleSkillPaths(RunExecutionAttestation, query)
  -> current VisibleSkillSummary list

ResolveVisibleSkillPath(RunExecutionAttestation, source selector)
  -> current visible source + Storage AssetRef + optional content digest

ReadApprovedSkillPackage(RunExecutionAttestation, AssetRef)
  -> scan-approved bytes / manifest
```

proof 只带 session、exact selector request binding 与 sealed IAM assertion reference；Capability/Storage 从 assertion 得到可信
tenant/subject 后重验当前事实。subject path 固定为 `tenant + subject`：personal subject 是用户私有 path，project/service subject
是相应主体共享 path；session path 仅匹配 exact `session_id`。`actor` 只用于本次代表关系的 IAM/owner recheck，不形成可自动
mount 的个人 overlay。`RuntimeNamespace` 只由 GA 本地用于 candidate/thread/workbench 隔离，不进入这些 public calls。GA 成功
mount 后拥有 `.kokoro/skills.lock`、workbench 与恢复；普通 Capability CRUD 只影响后续 discover，不重写当前 thread。fork 重新
discover 同一 subject path，不复制旧 session path、mount 或 workbench。

首次 `ReadApprovedSkillPackage` 只服务于新的 `load_skill`：GA 在返回 tool success 前，先将已验证 package 原子复制到自身的
durable thread workbench，再写 lock。后续 worker/sandbox 重建读取这份 GA copy，不拿 `source_ref` 回到 Capability/Storage 重新
resolve/read；这使普通 CRUD、source outage 与 Storage 内容生命周期不成为已注入线程的隐式重写通道。GA durable workbench 可以是
持久本地卷或其 MinIO-first `S3Workspace` adapter，仍是 GA 私有运行面，不是 Storage Artifact。

### 2.5 kokoro-capability doesNotOwn

```text
upload/blob/asset/scan/artifact lifecycle
S3 bucket/key policy
ObjectStore SDK client
Storage MySQL schema
```

## 3. 存储分层与 schema owner

| 事实 | owner | 存储 | 最终 writer |
|---|---|---|---|
| `storage_upload` | Storage | MySQL | kokoro-storage |
| `storage_blob` | Storage | MySQL | kokoro-storage |
| `storage_asset` | Storage | MySQL | kokoro-storage |
| `storage_scan` | Storage | MySQL | kokoro-storage |
| `storage_artifact` | Storage | MySQL | kokoro-storage |
| `storage_command_receipt` | Storage | MySQL | kokoro-storage |
| scan outcome/report identity | Storage | MySQL `storage_scan` | kokoro-storage |
| artifact/preview manifest | owning runtime or ObjectStore, not Storage v1 | contract-specific | owning service |
| runtime admission/liveness | Storage runtime | Redis | kokoro-storage |
| package/artifact/blob bytes | Storage | S3-compatible ObjectStore | ObjectStore adapter |
| capability metadata/authorization/installation/source state | Capability | MySQL | kokoro-capability |

MySQL schema 的 canonical 字段以 `kokoro-storage/database/schema.sql` 为准，当前使用 `namespace`；这是 Storage V1 的内部物理列名，
不建立 Browser/Session/GA caller 向 Storage 传 GA `RuntimeNamespace` 的 target contract，也不另造 `storage_scope` 字段。

Storage v1 不创建 Mongo collection，也不要求 Mongo 可用。Scanner 的结构化结果与稳定 report id 在 MySQL 事务中和 asset 状态一起提交；ObjectStore 仅在未来需要保留大体积原始报告时承载其 bytes，不能绕过 MySQL 状态机。

## 4. ObjectStore 方案

### 4.1 协议选择

MinIO 支持 S3 API，因此“本地 MinIO”仍然按 S3-compatible 处理：

```text
业务模块 -> ObjectStore port -> AWS SDK S3 client -> S3-compatible endpoint
```

供应商差异只允许存在于 adapter 配置：

| Provider | endpoint | path style | 备注 |
|---|---|---|---|
| AWS S3 | 通常为空 | 默认 virtual-hosted | 使用 AWS region 与 SigV4 |
| MinIO | `http(s)://host:9000` | 本地通常 true | 本地集成默认 provider |
| Ceph RGW | RGW endpoint | 按 RGW/网关配置 | 只依赖兼容核心 API |

Kokoro 只依赖：PUT、GET、HEAD、DELETE、presigned PUT/GET、metadata、content length、SHA-256 metadata。供应商扩展不能进入 Capability/Storage domain。

### 4.2 profile

```text
minio-s3（默认 S3-compatible 集成 profile）
  MinIO container
  S3-compatible adapter
  用于真实 presigned、权限、endpoint 和对象语义验证

local-fs（显式 no-infra 测试 profile）
  LocalObjectStore
  只用于 unit test / 无基础设施开发
  不作为 S3 行为验证依据
```

`KOKORO_OBJECT_STORE_DRIVER=local` 必须显式设置；默认 driver 为 `s3`，默认 profile 为 `minio`，默认 endpoint
指向 Docker MinIO。`local-fs` 只表示显式选择 `LocalObjectStore`，不表示 Storage 的默认实现。

### 4.3 key 与引用

- object key 由 Storage 生成，调用方不能生成 bucket/key。
- `object_key` 只作为 Storage 内部实现值；上层长期业务事实优先保存 `asset_id + content_sha256`，不出现在 Storage public response。
- 原始 filename 仅用于生成受限对象 key/元数据，不能成为授权依据。
- `asset_id`、`artifact_id` 是业务引用，不是 S3 key。
- `upload_url`、`download_url` 为短期引用，不进入长期业务事实。

## 5. Upload/Asset/Artifact 状态机

### 5.1 Upload

```text
pending -> completed
pending -> aborted（通过 `AbortUpload`，补偿任务也可收敛超时状态）
```

`CompleteUpload` 必须完成 ObjectStore HEAD、size 和 digest 校验；不能只检查对象是否存在。

### 5.2 Scan

```text
pending -> clean
pending -> infected
pending -> unknown
```

只有 `clean` asset 可以被 `GetPackageReference` 返回下载引用。`infected`、`unknown` 和不存在的 scan 状态都按前置条件失败处理。

### 5.3 Artifact

```text
draft -> final
```

当前 v1 通过 `CreateArtifact` 创建 draft，再由 `FinalizeArtifact` 固化 final。final 后 digest、asset_id 和状态不可修改。

## 6. 端到端流程

### 6.1 Capability package

```text
Capability -> CreateUpload(UPLOAD_PURPOSE_CAPABILITY_PACKAGE)
Capability -> PUT upload_url
Capability -> CompleteUpload
Storage    -> HEAD/checksum/size
Storage    -> scan outcome + report identity in MySQL
Storage    -> MySQL asset(clean)
Capability -> GetPackageReference(asset_id + digest)
Capability -> installation transaction
```

跨服务不使用分布式事务：

- Storage 成功、Capability 失败：按 `request_id + digest` 重放 Storage 结果。
- Capability 只有在 scan clean、digest 匹配并获得 `asset_id` 后才能写 active installation。
- Storage 不决定 Capability authorization。

### 6.2 Asset/Artifact

```text
CreateUpload(upload_purpose=ASSET|ARTIFACT)
  -> presigned upload
  -> CompleteUpload
  -> clean asset
  -> internal draft artifact
  -> FinalizeArtifact
  -> final artifact reference
```

### 6.3 半成功补偿

```text
ObjectStore object exists + MySQL pending/missing
  -> orphan reconciliation
  -> retry completion or delete object

ObjectStore bytes exist + MySQL transaction failed
  -> bytes remain outside the business read path
  -> reconciliation retries or removes them; never directly promote business state

MySQL pending + object missing
  -> expire/abort reservation
```

## 7. Redis 运行时策略

Redis 当前 v1 用于：

```text
startup liveness check
per-RPC admission check
```

MySQL `storage_command_receipt` 是 Storage v1 的持久幂等事实；Capability 的 command receipt 由 Capability 自己的 owner schema 保存。
Redis claim、upload reservation TTL、short lease、scan coordination 和 retry suppression 不是当前公开 v1 RPC。

Redis 不可用时：

- 不接受新的 upload admission。
- 不签发新的 upload/download reference。
- 不执行 finalize 或任何未挂载的 legacy snapshot command。
- 不降级到进程内 Map、SQLite 或绕过 Redis 直接假装成功。
- 恢复后从 MySQL 最终状态重建短期运行 key。

## 8. API contract 权威关系

### Storage

权威：

```text
contract/proto/kokoro/storage/v1/storage.proto
kokoro-storage/docs/API_CONTRACT.md
```

v1 RPC（完整生命周期）：

```text
CreateUpload / CompleteUpload / AbortUpload / GetUploadStatus
GetAsset / GetScanStatus / GetPackageReference / GetDownloadReference
CreateArtifact / FinalizeArtifact
```

### Capability

权威：

```text
contract/proto/kokoro/capability/v1/capability_runtime.proto
kokoro-capability/docs/API_CONTRACT.md
```

v1 RPC：

```text
SkillCatalogService: CreateSkillDraft / ValidateSkillDraft / PublishSkill / WithdrawSkill
SkillSourceService: DiscoverVisibleSkills / ResolveVisibleSkill / GetApprovedSkillPackageReference
ConnectorService: CreateConnector / BeginConnectorAuthorization / CompleteConnectorAuthorization /
  ListConnectors / GetConnector / RevokeConnector
McpServerService: RegisterMcpServer / GetMcpServer / ListMcpServers
McpConnectionService: CreateMcpConnection / ListMcpServerDeclarations / GetMcpConnection /
  ListMcpConnections / RevokeMcpConnection
McpAuthorizationService: ListConnectorCapabilities / AuthorizeMcpTool
ConnectorProviderService: ListConnectorProviders
```

Root proto 是唯一 source of truth；子仓 generated mirror 通过 provenance hash 检查，禁止手改 generated TS。

## 9. Legacy snapshot compatibility boundary

`CapabilityRuntimeService.ResolveRuntimeSnapshot` 仅在 Root contract 中作为迁移期 descriptor 保留至
2026-10-15。Capability v1 不挂载该 service，不创建 `runtime_snapshot` 表，不保留 snapshot module、writer 或
client facade。Agent/GA 完成动态 Skill source cutover 后，Root consumer registry 与 descriptor 一并删除。
在此之前也不得把 legacy RPC 重新注册到 Capability server。

## 10. 错误与幂等

统一错误分类：

```text
INVALID_ARGUMENT
UNAUTHENTICATED
PERMISSION_DENIED
NOT_FOUND
COMMAND_DIGEST_MISMATCH
CONFLICT
PRECONDITION_FAILED
DEPENDENCY_UNAVAILABLE
RATE_LIMITED
INTERNAL
```

幂等规则：

1. `request_id/command_id + request_digest` 是 command identity。
2. 同 identity 重试返回原结果并标记 `replayed=true`。
3. 相同 command id 使用不同 digest 返回 `COMMAND_DIGEST_MISMATCH`。
4. digest、size、namespace 或 asset 不一致不得自动覆盖。
5. 权限、输入错误和 digest mismatch 不可重试；临时依赖故障可重试。

## 11. 验收矩阵

| 维度 | 证据 |
|---|---|
| Root contract lint | `pnpm exec buf lint contract` |
| generated/provenance | capability/storage `pnpm contract:check` |
| ObjectStore | MinIO S3 smoke；AWS/Ceph 只替换 endpoint/profile |
| MySQL/Redis/MinIO | infrastructure smoke；MongoDB 不属于 Capability/Storage v1 |
| Storage RPC mapping | RPC contract tests |
| Capability V1 baseline | Skill source/Connector/MCP contract tests；GA target 另以 find/load + owner-proof tests 验收 |
| Redis fail closed | runtime smoke/config tests |
| owner/schema | schema owner inventory + architecture tests |
| docs/code alignment | README/INDEX/API/technical design 同步检查 |

## 12. 后续增量，不属于当前完整生命周期 v1

以下内容明确标记为**后续增量，当前不属于完整生命周期 v1**，不能在文档中当作已发布 API：

```text
DeleteObjectRequest RPC
multipart RPC 级编排
provider-specific lifecycle/retention API
batch query/reference RPC
```

新增时遵循：只追加 protobuf field/RPC/enum value，不复用 field number，不把数据库 schema 暴露为公共 API。

## 13. 结论

Capability 只管理“谁能发现/安装什么”；Storage 只管理“bytes 如何上传、扫描、引用和最终化”。MinIO、AWS S3、Ceph 的差异停留在 S3-compatible adapter 配置层。Capability 使用自己的 MySQL schema 与 Redis admission；Storage 使用自己的 MySQL schema、Redis admission 和 S3-compatible ObjectStore，Storage v1 不连接 MongoDB。Capability 不连接 MongoDB，也不连接任何 ObjectStore，边界不互相越权。
