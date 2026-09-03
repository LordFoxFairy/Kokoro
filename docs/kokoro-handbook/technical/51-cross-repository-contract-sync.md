# 51. 跨子仓 API/AIP 契约与技术方案同步

状态：当前首发架构规则（2026-09-02）。每个 owner 仓库在本仓维护自己的 v1 API contract；Root 只维护仓库归属、架构规则和验证入口。

这份规则解决一个容易混淆的问题：**每个 wire/API contract 由事实 owner 在本仓定义，消费者按明确版本接入**。
Goal 2 的七个正式 owner 都必须有本仓 API contract、技术方案、BFF 接入、验收和风险文档；
这些文档是本仓实现契约，不得反向制造第二套跨仓 wire schema，也不得复制其他仓的实现。

## Goal 2 owner matrix

| Owner | Owner authority | Owner contract surface |
|---|---|---|
| `kokoro-iam` | IAM 本仓 API/Proto | users, tenants, auth, authz, roles, permissions, OAuth, Passkey, audit |
| `kokoro-system` | System 本仓 API/Proto | Site, Workspace, Manifest, config and site policy HTTP/RPC fixture |
| `kokoro-model` | Model 本仓 API/Proto | catalog/provider/availability/capability and tenant policy |
| `kokoro-billing` | Owner OpenAPI v1 | payment/subscription/checkout/refund/Credit/Ledger |
| `kokoro-capability` | Capability 本仓 API/Proto | Skills and MCP Connector control plane; Agent owns live MCP execution |
| `kokoro-storage` | Storage 本仓 API/Proto | files/uploads/assets/artifacts and S3-compatible object references |
| `kokoro-scheduler` | Owner configuration/internal-command contract | generic schedule/lease/retry/misfire; no business DB or Billing logic |

Root 不登记或生成 owner wire。跨仓字段变化先在事实 owner 仓库的本地 contract 中完成，再由消费者更新自己的 client facade 和 contract tests；owner-only HTTP/config 变化只在该 owner 内收敛。

## 1. 唯一权威与各仓职责

```text
Owner repository contract/docs
        │ 生成
        ├── kokoro-agent consumer
        ├── kokoro-bff consumer
        ├── kokoro-capability consumer
        ├── kokoro-storage consumer
        └── kokoro-app/root-e2e consumer
```

| 位置 | 唯一职责 | 不负责 |
|---|---|---|
| Owner repository contract/docs | Proto/OpenAPI、字段、错误/幂等/兼容规则、consumer-facing surface | 其他 owner 的数据库实现 |
| `kokoro-agent` | DeepAgents/LangGraph/Swarm 执行、Feature/Agent 组装、RunLedger、checkpoint、`chat_messages/chat_events` | Session 产品投影、Capability/Storage 私库 |
| `kokoro-bff` | Chat、Project/ScheduledTask 业务事实、鉴权、幂等、owner adapter、SSE projection | Agent 数据库、业务 owner 数据库、Agent 执行事实 |
| `kokoro-capability` | Skill CRUD/find/resolve、MCP 子域 Connector metadata 与授权 | GA default Skill 执行、package bytes、MCP transport |
| `kokoro-storage` | Upload、Asset、Scan、Artifact 与 S3-compatible ObjectStore 生命周期；元数据使用 PostgreSQL | Agent workbench、Skill policy、Session history |

## 2. 同一交付批次的更新顺序

```text
1. 在事实 owner 仓库修改本仓 contract/docs
2. 运行该仓 format / lint / breaking / contract gate
3. 在消费者仓更新 typed client、adapter、测试和运行时实现
4. 更新消费者本仓 API/AIP 摘录和 technical-plan
5. 运行 owner 与消费者各自 verify，再运行 Root topology/E2E gate
```

若只改变 owner 内部实现（例如 GA 的 RunLedger 表、Storage 的 S3 adapter），不改公共 contract；只需更新该仓技术方案和测试。
若改变跨仓字段或事件，必须从事实 owner 仓库开始；不能在消费者仓伪造第二份 owner contract。

## 3. 各子仓需要维护的文档

### Agent

- `kokoro-agent/docs/agent/api-contract.md`：GA 对 Launch、Control、ProductEvent、聊天事实的消费视图。
- `kokoro-agent/docs/agent/technical-plan.md`：`Feature -> Agent(s) -> AgentFactory -> DeepAgents -> RunLedger` 的实现链路。
- 不能在 Agent 文档中新增 `deps`、Session 配置、Agent 选择器或自定义 State；使用 DeepAgents/LangGraph 原生 state。

### BFF Chat

- `kokoro-bff/docs/api/`：Web-facing Chat、Project、ScheduledTask、SSE 和 owner adapter 的消费视图。
- BFF 负责产品 Session 资源概念、消息入口、鉴权、幂等和事件 projection，不拥有 Agent
  执行事实，也不读取 Agent 数据库。
- BFF 的跨仓请求必须依据 owner contract 生成/校验，不能重新创建 Session 独立 owner。

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
禁止把 Storage bucket/object key 暴露到消费者 contract
禁止用 Session 配置、Agent 版本、release/binding 对象替代 feature_key
禁止为了“同步”建立第二套事件表或第二套 Agent runtime
```

最终判断标准很简单：**事实 owner 回答“本仓边界怎么说”，消费者回答“如何接入”，Root 只回答“归属和如何验证”**。三者通过版本化文档、client facade、contract
测试和 verify gate 对齐，而不是通过复制代码或复制文档来对齐。
