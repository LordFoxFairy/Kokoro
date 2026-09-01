# 51. 跨子仓 API/AIP 契约与技术方案同步

状态：当前首发架构规则（2026-09-01）。Goal 2 七仓机器索引见
[`contract/goal2-repository-contract-manifest.json`](../../../contract/goal2-repository-contract-manifest.json)。

这份规则解决一个容易混淆的问题：**跨仓 wire 契约只定义一次，owner surface 按边界分别维护**。
Goal 2 的七个正式 owner 都必须有本仓 API contract、技术方案、BFF 接入、验收和风险文档；
这些文档是本仓实现契约，不得反向制造第二套跨仓 wire schema，也不得复制其他仓的实现。

## Goal 2 owner matrix

| Owner | Cross-repository authority | Owner contract surface |
|---|---|---|
| `kokoro-iam` | Root IAM authentication/authorization Proto + owner IAM Proto | users, tenants, auth, authz, roles, permissions, OAuth, Passkey, audit |
| `kokoro-system` | Root Site shared types where consumed | Site, Workspace, Manifest, config and site policy HTTP/RPC fixture |
| `kokoro-model` | Root Model Catalog Proto | catalog/provider/availability/capability and tenant policy |
| `kokoro-billing` | Owner OpenAPI v1 | payment/subscription/checkout/refund/Credit/Ledger |
| `kokoro-capability` | Root Capability + Storage Proto | Skills and MCP Connector control plane; Agent owns live MCP execution |
| `kokoro-storage` | Root Storage Proto | files/uploads/assets/artifacts and S3-compatible object references |
| `kokoro-scheduler` | Owner configuration/internal-command contract | generic schedule/lease/retry/misfire; no business DB or Billing logic |

The root registry intentionally records System, Billing and Scheduler owner surfaces without
inventing a parallel Proto for them. A later cross-repository wire change must promote its fields
into Root contract first; an owner-only HTTP/config change stays in that owner.

## 1. 唯一权威与各仓职责

```text
Root contract/proto + manifest + Goal 2 owner registry
        │ 生成
        ├── kokoro-agent consumer
        ├── kokoro-session consumer（仅既有 Slice A 兼容闭环）
        ├── kokoro-capability consumer
        ├── kokoro-storage consumer
        └── kokoro-web/root-e2e consumer
```

| 位置 | 唯一职责 | 不负责 |
|---|---|---|
| Root `contract/` | Proto/OpenAPI、字段编号、oneof、错误/幂等/兼容规则、consumer closure | 任何 owner 的数据库实现 |
| `kokoro-agent` | DeepAgents/LangGraph/Swarm 执行、Feature/Agent 组装、RunLedger、checkpoint、`chat_messages/chat_events` | Session 产品投影、Capability/Storage 私库 |
| `kokoro-session` | ProductSession、IAM admission、历史查询、事件 replay、AG-UI/SSE | Agent 执行、checkpoint、GA 聊天事实写入 |
| `kokoro-capability` | Skill CRUD/find/resolve、MCP 子域 Connector metadata 与授权 | GA default Skill 执行、package bytes、MCP transport |
| `kokoro-storage` | Upload、Asset、Scan、Artifact 与 S3-compatible ObjectStore 生命周期；元数据使用 PostgreSQL | Agent workbench、Skill policy、Session history |

## 2. 同一交付批次的更新顺序

```text
1. 修改 Root contract/proto 与 manifest
2. 运行 format / lint / breaking / manifest gate
3. 重新生成各 consumer，并写入 provenance
4. 更新 owner adapter、测试和运行时实现
5. 更新对应子仓 docs/*/api-contract.md
6. 更新对应子仓 technical-plan.md / TECHNICAL_DESIGN.md
7. 运行各仓 verify，再运行 Root render/e2e gate
```

若只改变 owner 内部实现（例如 GA 的 RunLedger 表、Storage 的 S3 adapter），不改 Root contract；只需更新该仓技术方案和测试。
若改变跨仓字段或事件，必须从 Root 开始，不能直接手改子仓 `src/contract/`。

## 3. 各子仓需要维护的文档

### GA

- `kokoro-agent/docs/agent/api-contract.md`：GA 对 Launch、Control、ProductEvent、聊天事实的消费视图。
- `kokoro-agent/docs/agent/technical-plan.md`：`Feature -> Agent(s) -> AgentFactory -> DeepAgents -> RunLedger` 的实现链路。
- 不能在 GA 文档中新增 `deps`、Session 配置、Agent 选择器或自定义 State；使用 DeepAgents/LangGraph 原生 state。

### Session

- `kokoro-session/docs/session/api-contract.md`：Session 对 Root 命令和安全 ProductEvent 的消费视图。
- `kokoro-session/docs/session/technical-plan.md`：ProductSession、授权、查询/replay、AG-UI/SSE 的实现链路。
- Session 不把 LangChain `Message.id/thread_id/checkpoint_id` 映射成产品消息，也不写 GA canonical chat facts。
- 当前 Session Redis relay 使用严格 internal adapter；它与 Root/GA 语义对齐，但 launch
  envelope 的 `input={message_id,content}` 与 Root protobuf 顶层 `message_id/content` 需在
  transport mapping 转换。生成 consumer、ChatQuery transport 和 `kokoro-session` consumer
  命名需要在 Root manifest 与本仓同一批次接通。

### Capability

- `kokoro-capability/docs/API_CONTRACT.md`：Skill 管理与 find/resolve、MCP 子域 Connector、MCP Server/Connection/Authorization 的 owner contract。
- `kokoro-capability/docs/TECHNICAL_DESIGN.md`：metadata/policy/authorization 的实现和 client facade 边界。
- GA 内置 Skill 与 `find_skills/load_skill` 属于 GA；用户/项目/会话 Skill 的 CRUD 与 source path 才调用 Capability。

### Storage

- `kokoro-storage/docs/API_CONTRACT.md`：Upload、Complete、Scan、Asset、Artifact、受控 read/write reference 的 owner contract。
- `kokoro-storage/docs/TECHNICAL_DESIGN.md`：PostgreSQL/S3-compatible adapter、scan gate 和幂等 receipt 的实现方案；Storage v1 不依赖 MongoDB。
- MinIO 只是默认 S3-compatible endpoint；后续 AWS S3、Ceph RGW 等通过同一 ObjectStore adapter contract 接入。
- 内部 S3 endpoint 与 presigned URL 的 consumer-facing endpoint 可分离；部署通过
  `KOKORO_OBJECT_STORE_PUBLIC_ENDPOINT` 固化可达性，不进入 v1 wire contract。

## 4. 明确禁止的重复设计

```text
禁止在子仓复制 Root Proto/OpenAPI 或手写跨仓 DTO
禁止把 LangChain checkpoint 表当作产品聊天表
禁止把 Capability 的 Skill metadata 当作 GA native state
禁止把 Storage bucket/object key 暴露到 Root contract
禁止用 Session 配置、Agent 版本、release/binding 对象替代 feature_key
禁止为了“同步”建立第二套事件表或第二套 Agent runtime
```

最终判断标准很简单：**Root 只回答“跨服务怎么说”，owner 技术方案只回答“本仓怎么做”**。两者通过生成物 provenance、contract
测试和 verify gate 对齐，而不是通过复制代码或复制文档来对齐。
