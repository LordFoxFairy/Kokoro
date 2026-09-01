# Capability × MCP × Connector × Skill 方案

状态：**Capability v1 设计与实现基线，尚未对外发布**（2026-08-27）

本仓库尚未对外发布，因此 Connector、MCP、Skill 的新增接口统一进入
`kokoro.capability.v1`；现在不拆 v2、不维护 v1/v2 双写或转换层。只有在
v1 已有外部消费者且出现无法 additive 演进的语义/安全边界变化时，才新建 v2。

## 1. 设计结论

Capability 不是一个“把所有工具塞给 Agent”的大表，而是三个独立对象的控制面。它们属于
两个不同的产品面：Skill 是工作流内容面，Connector 与 MCP 是外部集成面。

```text
Skill      = 如何完成一类工作的可移植工作流与资料
Connector  = 用户/项目/组织授权的一个外部系统连接实例
MCP        = 外部系统能力暴露所使用的协议、server、client session 和 primitives
```

三者关系：

```text
Skill instructions/resources
        │ declares required capability, never grants authority
        ▼
Connector authorization + IAM subject grant + feature policy
        │ permits a bounded MCP surface
        ▼
MCP adapter/runtime
        │ establishes session and invokes selected tool/resource
        ▼
External system
```

Skill 是“操作手册”，Connector 是“已授权连接实例”，MCP 是“协议与能力暴露模型”。它们不能互相替代。

### 1.1 Connector 与 MCP 的准确关系

Connector 和 MCP 确实属于同一个 Integration domain，但不是同一个对象：

```text
Connector
  = 谁授权了哪个外部系统、以什么 scope、绑定哪个 credential handle

MCP Server/Registry
  = 外部 server 的协议身份、transport、tools/resources/prompts 声明

McpConnection
  = 某个 Connector 到某个 MCP server 的策略化连接，以及允许哪些 primitives
```

一个 Connector 可以是 `builtin`、`byok` 或 `mcp` 类型；Manus 的 `mcp` connector 表示
“通过 MCP 接入的连接实例”，不是把 Connector 定义成 MCP 协议本身。Kokoro 因此保留
`Connector`、`McpServer`、`McpConnection` 三个独立 identity，避免把授权、协议声明和运行时
session 混成一张表。

## 2. 从 Manus 设计中吸收的原则

Manus 的公开设计体现了几个值得采用的原则：

1. **Skill progressive disclosure**：启动只加载 name/description；触发时加载 `SKILL.md`；脚本、references、templates 按需读取。
2. **Skill portable package**：Skill 由 `SKILL.md`、YAML metadata 和可选资源组成，可通过文件、zip 或 GitHub 分享。
3. **Connector 是用户中心的授权层**：用户先完成 OAuth/凭据授权，再在 task 中选择一个或多个 connector；移除连接时清理登录信息和保存凭据。
4. **MCP 与 Skill 互补**：MCP 负责标准化访问外部数据和工具；Skill 负责解释什么时候、如何使用这些工具。
5. **项目/团队范围与个人范围分离**：共享 Skill 必须有明确 scope 和发布/锁定语义，不能把个人授权隐式带入共享项目。

参考：Manus [Skills sharing guide](https://help.manus.im/en/articles/14753565-how-to-share-and-use-skills-in-manus)、[Connectors guide](https://help.manus.im/en/articles/12231777-how-can-i-use-manus-connectors)、[Skills and MCP design](https://manus.im/blog/manus-skills)、[Manus API Connectors](https://open.manus.ai/docs/v2/connectors)。

### 2.1 本次核对后的具体吸收

Manus 的公开 API 进一步确认了四个边界：

1. `skill.list` 返回稳定 skill ID 和 metadata，任务只提交 ID；`enable_skills` 与 `force_skills` 是两种不同的任务意图，不能把完整 skill 正文塞进 task request。
2. Connector 是独立资源，task 通过一个或多个 connector ID 引用；省略显式 connector 时才使用 project/user default。
3. Task 创建、消息追加、消息读取、任务详情是不同操作，创建接口只建立异步任务，不把整个运行时状态作为同步 response 返回。
4. Task reference 和 file reference 都采用 ID，并在需要时按需读取；这与 Skill metadata-first、Storage AssetRef 的 progressive disclosure 一致。

Kokoro 采用这些交互原则，但不复制 Manus 的 JSON `{ok,data,error}` envelope，也不把
`task.create` 变成 Capability 的职责。Task、run、message、workbench 仍由 GA/Session owner
管理；Capability 只解析 source、connector 和 policy，返回最小 opaque reference 或短期 grant。

## 3. Kokoro 的对象模型

### 3.1 Skill

Capability owns：

```text
skill identity: qualified_name + owner subject + logical source selector
metadata: name, bounded description, tags, declared inputs
visibility/status: private, project, organization, active, withdrawn, quarantined
package AssetRef + content_digest
validation result and source revision
```

Skill package 采用 Agent Skills 目录形态：

```text
skill-name/
├── SKILL.md              # required entry; YAML frontmatter + instructions
├── scripts/              # optional, sandboxed; never trusted by default
├── references/           # optional, loaded on demand
└── templates/            # optional, loaded on demand
```

`SKILL.md` 只能描述工作流、知识和输入输出约定；不能声明 IAM grant、MCP secret、Agent member、graph edge、sandbox escape 或 billing policy。

### 3.2 Connector

Capability owns connector control-plane metadata：

```text
connector_id (opaque)
connector_type (builtin | byok | mcp)
provider_key
owner_scope (user | project | organization)
external_account_ref (opaque)
requested scopes and approved scopes
status (pending | active | revoked | error)
credential_handle_ref (opaque)
capability allow/deny policy
```

SecretStore owns secret values. Connector runtime owns active OAuth token refresh、MCP session、transport、rate limit and provider error translation。Capability 只保存 handle/reference，不保存 token、API key 或 cookie。

一个 connector 是一个已授权实例，不是 provider 类型本身；同一 GitHub/Notion provider 可以有多个不同 external account 和不同 scope。

### 3.3 MCP

Capability 只管理 MCP registry、McpConnection 和 exposure policy：

```text
server identity / server declaration digest
connector-to-server connection policy
transport class (stdio | streamable-http | sse-compat)
declared tool/resource/prompt summary
allowed tool selector and output limits
approval requirement and audit policy
```

MCP adapter/runtime owns：

```text
initialize/handshake
transport and session lifecycle
tool invocation/resource read
OAuth challenge and token refresh
provider-specific protocol behavior
```

### 3.4 Harness 参考的边界

DeepSeek Harness 的公开架构把 model adapter、tool registry、session log、agent loop 和
filesystem/sandbox 都作为可替换 plugin，并用 typed service/event 连接；Codex 则把 CLI、runtime、
SDK 和应用层分开。Kokoro 只吸收两个工程原则：

- Capability 内部以窄 service port 和 adapter 组合，provider/MCP transport 可替换；
- 对外通过稳定 client facade 消费 generated v1 contract，调用方不依赖私有模块。

Capability 不因此变成通用 plugin kernel，也不接管 Agent loop、Session event log、sandbox
或 UI。plugin 的可替换性属于 adapter 结构，业务 owner 仍由本设计卡固定。

参考：[DeepSeek Harness architecture](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/architecture.md)、[OpenAI Codex repository](https://github.com/openai/codex)。

Agent/GA 只看到经过 policy intersection 后的 typed tool surface，不直接看到 provider URL、
credential、Redis key 或 connector secret。MCP server 的 `tools/list`、`resources/list` 等
协议事实属于 MCP adapter/runtime 的 session view；Capability 保存可审计的声明摘要和 policy，
不伪造 handshake 结果。

## 4. 权限与有效工具面

一次 MCP tool call 的有效权限必须同时满足：

```text
IAM trusted subject assertion
∩ Connector owner scope and approved OAuth scopes
∩ Capability allow/deny policy
∩ current Feature/Agent policy
∩ MCP server declared tool selector
∩ per-call approval / budget / rate limit
```

任意一层缺失或 Redis/connector runtime 不可用，调用 fail closed。Skill 文本只能提出“需要使用某个 connector/tool”，不能自行扩大交集。

共享项目规则：

- project/team connector 只能授权给该 scope 内的 subject。
- personal connector 不自动出现在 project/team run。
- 共享 Skill 可以被项目继承，但不会继承发布者的个人 connector 授权。
- connector revoke 立即阻断新调用；已加载 Skill 作为文本仍可存在，但在下一 tool boundary 重新检查。
- shared session 输出必须脱敏，不能泄露 token、account id 或原始 connector response 中的 secret。

## 5. 生命周期

### Connector lifecycle

```text
CreateConnector
  -> pending authorization
  -> OAuth/API-key consent
  -> ValidateConnector
  -> active
  -> error | revoked
```

移除 connector 的语义是撤销授权、删除 credential handle/value、使 runtime session 失效，并留下不可逆审计事件；不是删除历史 task 的文本记录。

### Skill lifecycle

```text
Import/Upload/Git source
  -> parse and validate SKILL.md
  -> malware/content scan via Storage
  -> register metadata + AssetRef
  -> private/project/organization visibility
  -> discover summary
  -> resolve current source
  -> GA loads package into durable workbench
  -> withdraw/quarantine
```

Skill 的 package bytes 必须走 Storage `CreateUpload`、`CompleteUpload`、clean gate 和 AssetRef；Capability 不直接写 ObjectStore。

### MCP exposure lifecycle

```text
connector active
  -> adapter handshake
  -> enumerate declared tools/resources
  -> apply policy intersection
  -> expose bounded typed surface
  -> invoke with per-call attestation
  -> audit result metadata only
```

MCP server 掉线不应伪造工具成功，也不能通过旧 cache 继续产生可调用 surface。

## 6. v1 公开 API 规划

以下是当前 v1 Root protobuf contract 的 API shape；实现通过 generated contract 与独立 client facade
消费，不能再造私有 REST/JSON 旁路。Capability 尚未对外发布，因此后续 additive 字段仍可在 v1
内完成；只有出现不可兼容的语义或安全边界变化时才新建 v2。

### 6.1 从 Manus API 借鉴、但不照搬

Manus 将 API 按资源分组，并让 task 请求显式携带 connector/skill IDs；connector 在 task 创建时支持 explicit、project default、user default 的优先级，后续消息又区分 override、clear、reuse。[Manus task.create](https://open.manus.ai/docs/v2/task.create)、[Manus connectors](https://open.manus.ai/docs/v2/connectors)、[Manus skill.list](https://open.manus.ai/docs/v2/skill.list)

Kokoro v1 采用这些交互原则，但保留 Connect/protobuf 和 Kokoro 的 owner boundary：

```text
explicit request selection > project default > user default
follow-up omitted        = reuse current run connection policy
explicit replacement     = override
explicit clear           = clear
```

“force skill”只能表达调用方的任务意图，不能绕过 IAM、Capability policy、connector scope、scan gate 或审批。

### 6.2 Connector control plane

```text
CreateConnector(owner_scope, provider_key, protocol, requested_scopes)
BeginConnectorAuthorization(connector_id)
CompleteConnectorAuthorization(connector_id, authorization_result)
ListConnectors(owner_scope, status_filter)
GetConnector(connector_id)
RevokeConnector(connector_id, reason)
```

API 只返回 opaque connector id、provider display metadata、approved scope 摘要和状态；不返回 secret/token/provider credential。

### 6.3 Skill source plane

```text
DiscoverVisibleSkills(attestation, query, limit)
ResolveVisibleSkill(attestation, source_selector)
  GetApprovedSkillPackageReference(attestation, source_ref)
WithdrawSkill(source_ref, reason)
```

### 6.4 MCP registry/runtime plane

```text
ListConnectorCapabilities(attestation, connector_id)
ResolveMcpTool(attestation, connector_id, tool_selector)
  AuthorizeMcpTool(attestation, connector_id, tool_selector, typed_arguments)
```

`AuthorizeMcpTool` 只返回短期 invocation grant；实际 `Invoke` 由 MCP adapter/runtime owner 提供。Capability 负责授权决策与 `McpConnection` policy，不把 provider execution 逻辑塞进 Capability。

### 6.5 v1 contract 共同规则

```text
每个资源都有 opaque id
跨请求引用使用 id，不使用 provider URL、bucket、object key 或文件路径
列表接口使用 limit + cursor，不使用 page number
写操作带 request_id + CommandIdentity，重试返回同一结果
所有错误带 canonical ErrorCode、request_id、retryable
所有跨运行调用带 audience/operation/request-binding attestation
```

Connect/protobuf 的 response 不复制 Manus 的 JSON `{ok,data,error}` 外壳；使用 Root common error model 和明确的 response message。
Manus 的资源 ID、显式 task selection、分页和 override/clear/reuse 语义可以借鉴，但不把 Manus 的 API 字段直接当作 Kokoro wire contract。

## 7. 当前实现与 v1 演进

当前 `kokoro-capability` 已将以下 Root v1 service 落地为独立 public surface：

```text
SkillCatalogService
SkillSourceService
ConnectorService
McpServerService
McpConnectionService
McpAuthorizationService
```

在资源和 client 层，MCP Server 与 MCP Connection 已经是两个独立边界：分别使用
`McpServerClient` 与 `McpConnectionClient`，分别绑定 `McpServerService` 和
`McpConnectionService`。二者从 v1 起就是独立 wire service，不是部署名、数据库 owner
或消费者必须依赖的资源名。未来拆分时只替换 endpoint/service adapter；资源 ID、
`McpServer`、`McpConnection` 和 v1 字段保持不变。

`ResolveRuntimeSnapshot` 仍保留为未上线的 legacy physical baseline，GA/Session 不得把它当作
新的 runtime binding contract。当前已实现的 v1 能力包括：

```text
Connector create/begin/complete/list/get/revoke
MCP Server register/get/list catalog
MCP declaration enumeration and bounded authorization grant
Skill metadata-first discover/resolve/approved package reference
Storage clean-gated portable Skill package upload/reference
personal subject scope filtering and Redis fail-closed admission
opaque cursor and durable command/idempotency semantics
```

`AuthorizeMcpTool` 只签发短期 invocation grant，不执行 MCP tool。实际 MCP handshake/session/
transport/invoke 仍由 MCP runtime owner 完成。Skill package 的 `SKILL.md`、`references/`、
`templates/`、`scripts/` 通过 Storage 受控 package reference 交给 GA；Capability 不执行脚本。

仍需继续演进的事项是 OAuth refresh/rotation 的真实外部 runtime adapter、团队/项目成员关系解析、
GA durable workbench lock，以及跨服务 invalidation wire contract 的独立评审。Provider catalog、
Connector revoke、Git/source import、Storage clean gate、MCP declaration adapter 和 MySQL outbox
已经落地。前一组事项分别属于外部 provider/GA/IAM 或跨仓评审边界，不得通过 Capability 私有状态
冒充完成；继续追加时必须先更新 Root contract、generated mirror、schema owner inventory、
authorization tests、secret redaction tests 与 runtime fail-closed tests，再实现 adapter。

明确不进入当前 v1 的只有 provider-specific SDK API、裸 token/URL、Agent graph/成员配置和 Storage 私有表/Redis key。

## 8. 验收标准

```text
Skill:
  metadata-first discover / on-demand package read / Storage clean gate
Connector:
  OAuth/API-key never stored in Capability / revoke removes secret access
MCP:
  only bounded typed surface / no raw URL or credential / transport errors fail closed
Scope:
  personal connector cannot cross into project/team run
Security:
  attestation request binding / output redaction / tool approval / audit metadata
Reliability:
  Redis unavailable, connector unavailable or MCP handshake failure => no successful call
```
