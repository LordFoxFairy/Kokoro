# Capability × Storage v1 API 与 Client 契约

状态：**首发前正式契约基线，尚未对外上线**（2026-08-29）。

这份文档把 `kokoro-capability` 与 `kokoro-storage` 的边界、API 版本、Client 封装和跨仓调用闭环固定下来。
Root contract 定义 wire，子仓技术方案定义实现，本文定义两者如何协作。

## 1. 不变的架构结论

```text
GA / Session / Hub / external BFF
        │ 只消费 generated v1 contract + typed client facade
        ▼
Capability v1                         Storage v1
Skill source / Connector / MCP        Upload / Asset / Scan / Artifact
metadata / policy / authorization     lifecycle / reference / bytes boundary
        │                              │
        └──── Storage public contract ┘

Capability MySQL + Redis               Storage MySQL + Redis
                                      S3-compatible ObjectStore
                                      ├─ Docker MinIO (default)
                                      ├─ AWS S3
                                      └─ Ceph RGW / compatible provider
```

### 1.1 Owner 矩阵

| Owner | owns | doesNotOwn |
|---|---|---|
| Capability | Skill source/metadata/visibility、Connector instance、MCP server/connection policy、authorization decision、Capability receipt/outbox | package bytes、bucket/object key、scan、Artifact、MCP transport/session、secret value、GA Skill runtime、MongoDB |
| Storage | upload admission/completion、blob/asset/scan/artifact lifecycle、content digest、短期 read/write reference、Storage receipt | Skill/MCP policy、Connector authorization、Session/Agent state、IAM master data、MongoDB |
| ObjectStore adapter | 原始 bytes 的 put/head/get/delete | 业务状态、授权、扫描结论、asset identity |
| GA/Agent | Agent Skill 声明、Capability 解析接线、DeepAgents 原生 SkillsMiddleware/read_file、Workbench、实际 MCP runtime | Capability/Storage 私库、bucket/key、credential、Skill CRUD/runtime 重实现 |

Capability 与 Storage 均为独立 bounded context，可独立部署。拆分部署只替换 endpoint 和 transport adapter，不重命名资源、数据库表、client 或 v1 wire service。

## 2. v1 版本和传输规则

当前没有上线消费者，因此所有新增公共接口统一进入 `v1`：

```text
外部 BFF/API：/v1/skills、/v1/connectors、/v1/mcp、/v1/files
内部 Connect RPC：kokoro.capability.v1.*、kokoro.storage.v1.*
Root source：contract/proto/kokoro/{capability,storage}/v1/*.proto
```

- 领域对象、Application service、repository port、MySQL 表和 Redis key 不复制版本。
- additive 字段使用新的 field number；不复用编号，不改变既有字段语义，不把未知 enum 当成成功。
- 只有 wire、DTO、错误语义、授权语义或不兼容的状态机变化才创建 `v2`。
- 不设计 `v1.1`、`v1.0.1`、v1/v2 双写或内部版本化数据库表。
- Root protobuf 是唯一 wire 权威；子仓不得维护平行 OpenAPI、私有 JSON DTO 或手写 generated message。
- Connect response 使用明确 response message 和 Root common error；Manus 的资源化、异步、opaque ID、分页、request ID 原则可借鉴，不复制 `{ok,data,error}` JSON envelope 到内部 protobuf。

## 3. Capability v1 API surface

Skill、Connector、MCP Server、MCP Connection、MCP Authorization 是五个独立资源面；共享 transport 不等于共享业务状态。

```text
SkillCatalogClient
  DiscoverVisibleSkills(attestation, query, tags, scope, page)

SkillSourceClient
  ResolveVisibleSkill(attestation, source_selector)
  GetApprovedSkillPackageReference(attestation, source_ref)
  CreateSkillDraft / ValidateSkillDraft / PublishSkill / WithdrawSkill

ConnectorProviderClient
  ListConnectorProviders(attestation, page)

ConnectorClient
  CreateConnector / BeginConnectorAuthorization / CompleteConnectorAuthorization
  ListConnectors / GetConnector / RevokeConnector

McpServerClient
  RegisterMcpServer / GetMcpServer / ListMcpServers

McpConnectionClient
  CreateMcpConnection / ListMcpServerDeclarations

McpAuthorizationClient
  ListConnectorCapabilities / AuthorizeMcpTool
```

契约不返回 token、API key、cookie、bucket、object key、provider SDK object 或 MCP session。`AuthorizeMcpTool` 只签发短期、operation-bound invocation grant；transport、handshake、session 和 invoke 由 MCP runtime owner 执行。

选择语义采用稳定的显式规则：

```text
explicit selection > project default > user default
follow-up omitted = reuse
explicit replacement = override
explicit clear = clear
```

这里的 `reuse/override/clear` 只适用于已有运行任务的 follow-up command；初始创建请求只解析一次
explicit/project default/user default。后续请求省略选择字段时复用任务当前配置，不重新读取后来变化的默认值。

`enabled/forced` 只表示候选意图，不能越过 IAM attestation、owner scope、approved scope、Capability policy、真实 MCP declaration、scan gate 或审批门。

## 4. Storage v1 API surface

```text
StorageClient
  CreateUpload
  CompleteUpload
  AbortUpload
  GetUploadStatus
  GetAsset
  GetScanStatus
  GetPackageReference
  GetDownloadReference
  CreateArtifact
  FinalizeArtifact
```

GA 的产物工具不直接编排上述十个 RPC，也不接受 raw ObjectStore。部署向
`WorkerClients.delivery` 注入窄 `DeliveryClient.publish(request) -> receipt` facade，由该
client adapter 按 Storage v1 闭环 upload、asset、scan 和 artifact。GA 只提供已验证身份、
namespace、run/path metadata、mime、SHA-256 与当次 workspace bytes；回执不暴露
bucket/key/presigned credential。

所有 command 携带 `request_id + CommandIdentity(command_id, request_digest)`；query 也必须携带 namespace 和最小身份上下文。幂等最终事实由 owner MySQL receipt 保存，`request_id` 只做追踪，不能替代 command identity。

### 4.1 Capability package 协作

```text
Capability -> Storage.CreateUpload(UPLOAD_PURPOSE_CAPABILITY_PACKAGE)
Capability -> presigned PUT(upload_url)
Capability -> Storage.CompleteUpload
Storage    -> ObjectStore HEAD/read + 真实 SHA-256 + scanner
Storage    -> MySQL asset + scan(clean) transaction
Capability -> Storage.GetPackageReference(asset_id, digest)
Capability -> install metadata/reference only
```

Capability 不直接 import Storage schema、S3 SDK、bucket、object key 或 Redis key。Storage 只返回 clean asset 的短期 reference；Capability package 的 `SKILL.md` manifest gate 与 Capability metadata transaction 仍由 Capability 自己完成。

## 5. S3-compatible ObjectStore：协议统一，差异收敛在 adapter

Storage 的生产业务代码只依赖 `ObjectStorePort`。默认 profile 是 Docker MinIO，但 MinIO 不是另一种存储实现，也不是本地文件夹：它通过 AWS SDK S3 adapter 按 S3 协议访问。

| 项目 | AWS S3 | MinIO | Ceph RGW/其他兼容实现 | 处理方式 |
|---|---|---|---|---|
| endpoint | 云端 regional endpoint | 部署提供的 HTTP endpoint | 部署提供的 endpoint | adapter/config |
| addressing | 通常 virtual-hosted | 常需 `forcePathStyle` | 由部署与网关决定 | adapter/config |
| region/signing | AWS region 与 SigV4 | 配置 region，通常 SigV4 | 配置兼容 region/signing | adapter/config |
| presign 可达性 | 云端公网/私网 | 容器内 endpoint 可能不可被 client 访问 | 网关/私网可达性不同 | public endpoint config |
| metadata/checksum | provider 行为有差异 | metadata 可靠性/代理行为不同 | 兼容程度不同 | Storage 读取 bytes 重算 SHA-256 |
| multipart/lifecycle/versioning | 能力丰富 | 可支持但部署相关 | 能力取决于版本 | 不进入 v1 public contract |

共同的 v1 交集只使用：短期 presigned PUT/GET、HEAD、受控单对象读写和 delete compensation。业务不依赖 provider-specific header、version ID、lifecycle rule 或 vendor SDK 类型。`content_sha256` 永远以 Storage 读取真实 bytes 后计算的结果为准，不能信任调用方 metadata。

配置原则：

```text
KOKORO_OBJECT_STORE_DRIVER=s3       # v1 默认且生产唯一 profile
KOKORO_OBJECT_STORE_ENDPOINT=...    # MinIO/AWS/Ceph 由部署提供
KOKORO_OBJECT_STORE_PUBLIC_ENDPOINT=... # presigned URL 的消费者可达地址
KOKORO_OBJECT_STORE_BUCKET=...      # 仅 deployment/adapter 使用，不进入 wire
```

`LocalObjectStore` 仅用于显式 unit/no-infra profile，不是默认生产路径，也不代表“本地 S3”。

## 6. Client facade 契约

每个子仓的 public client 是消费者唯一入口：

```text
typed consumer input
  -> validate identity / attestation / command digest
  -> build generated kokoro.*.v1 request
  -> bounded Connect call
  -> validate response invariants and error mapping
  -> return plain owner read model
```

客户端必须：

- 设置 deadline；不允许无限等待。
- 仅对明确幂等的 read/command 自动重试，并保留原 command identity。
- 对 response 做 allow-list mapping，不把 generated message、ORM entity 或 provider 字段泄漏出去。
- 将 `DEPENDENCY_UNAVAILABLE`、`PRECONDITION_FAILED`、`CONFLICT` 映射为稳定机器可读错误；不暴露堆栈、SQL、secret 或 provider raw payload。
- Storage URL 必须为短期 HTTP(S)、无 fragment、无额外长期凭据；Capability 只接收 asset/reference，不持久化 presigned URL。

资源 client 可共享 Connect channel，但不得共享 repository、授权状态或数据库连接。未来独立部署只需要改 client endpoint resolver。

## 7. Manus API 核对后的吸收项与不照搬项

本节是针对 Manus 当前公开 API 文档的核对记录，不是 Kokoro 的第二套契约。

### 吸收项

1. **资源化引用**：Skill、Connector、File/Asset 和 Task 都以 opaque ID/reference 互相引用；请求不内嵌完整 Skill 正文或文件 bytes。
2. **metadata-first**：Skill 列表返回 `id/name/description/owner_type/created_at/updated_at` 等摘要，任务再使用 Skill ID；Kokoro 将其落到
   `DiscoverVisibleSkills -> ResolveVisibleSkill -> GetApprovedSkillPackageReference` 三段式读取。
3. **显式能力选择**：创建运行时可显式传入 connector/skill selection；省略时按 owner scope 的默认规则解析，后续 follow-up 明确区分 reuse、override、clear。
4. **异步资源生命周期**：创建动作只返回资源 ID、request ID 和追踪引用，状态/消息/后续操作分开；Capability 不承载 Task API，Storage 不承载 Run API。
5. **认证分层**：Manus 将 API key 与 OAuth Bearer token 分开，并对 OAuth endpoint 使用 scope；Kokoro 对外 BFF 采用 User/Admin/Internal/Webhook 四类 surface，
   Capability 的 connector authorization 只保存 opaque handle，Storage 不接收 provider credential。
6. **边界校验**：数组长度、ID 格式、正文大小、附件大小、未知资源可见性和错误码都在 transport/application 边界验证；Kokoro client 同样必须在发 RPC 前校验，
   不能将错误留给数据库或 provider SDK。

### 不照搬项

- Manus 当前公开 endpoint 是 `/v2/<resource.action>`，但 Kokoro 尚未上线，首发统一为 `/v1`；不会因为参考 Manus 的当前 v2 路径而提前引入 v2。
- Manus 的 `{ok, request_id, data, error}` 是其外部 JSON envelope；Kokoro 内部使用 Root protobuf 明确 response/error message，外部 BFF 若采用 envelope 也必须由 BFF 自己定义并保持与 RPC 解耦。
- Manus 的 Task、Project、Agent、File、Webhook 是其平台 owner；Kokoro 只吸收资源化和生命周期原则，不把这些资源搬进 Capability 或 Storage。
- Manus connector 的 UUID 是其平台实例 ID；Kokoro 的 `connector_id`、`server_id`、`connection_id` 和 `asset_id` 都是本域 opaque reference，不能互相复用。

核对来源：Manus [Authentication](https://open.manus.ai/docs/v2/authentication)、[task.create](https://open.manus.ai/docs/v2/task.create)、
[Connectors](https://open.manus.ai/docs/v2/connectors)、[skill.list](https://open.manus.ai/docs/v2/skill.list)。

## 8. 故障与安全不变量

- Redis 是 Capability/Storage 的 runtime admission 硬依赖；connect、ping、每次 public command 都有 bounded timeout。
- Redis 不可用时 fail closed：不创建 connector、不给 skill package upload admission、不签发 read/invocation reference、不 finalize。
- MySQL 不可用时不返回假成功；ObjectStore 不可用时不把 pending 伪装成 completed。
- object 存在不等于 upload completed；只有 MySQL lifecycle + clean scan + digest 校验完成才可读。
- connector revoke 立即阻断新授权/调用；MCP declaration 过期、digest 不一致或 server down 时不使用旧 cache 伪造 surface。
- Capability 与 Storage 之间不使用分布式事务：Storage 以 command replay 和 reconciliation 收敛，Capability 以本地 transaction/outbox 收敛。

## 9. 生成、架构与测试门

每次公共契约变更必须按以下顺序：

```text
Root proto/manifest
  -> generated mirror/provenance check
  -> client facade contract tests
  -> owner unit/integration tests
  -> architecture boundary tests
  -> independent Compose readiness + smoke
```

最低验证集合：

```text
cd kokoro-capability && pnpm verify
cd kokoro-storage && pnpm verify
python3 contract/validate_slice_a_manifest.py contract/slice-a-contract-manifest.yaml
uv run python scripts/contract/render_slice_a.py --manifest contract/slice-a-contract-manifest.yaml --check
python3 scripts/verify-backend-design.py
```

## 10. 明确不属于 v1

以下能力等上线后有真实兼容需求再新增 Root contract，不提前污染 v1：

```text
Capability：provider-specific SDK API、raw token、MCP invoke transport、团队成员目录 owner
Storage：multipart orchestration、provider lifecycle/versioning、批量 reference、公开 delete RPC、MongoDB persistence
跨仓：v1/v2 双写、数据库版本复制、私有 REST 旁路、把 Session/Agent 改造成 Capability/Storage 子域
```

这不是遗留 TODO，而是当前首发边界；新增任何一项必须先更新 Root contract、owner inventory、client facade 和验证门。
