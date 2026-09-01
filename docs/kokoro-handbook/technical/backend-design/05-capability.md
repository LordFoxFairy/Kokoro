# kokoro-capability 设计卡

状态：当前 Capability owner 边界，2026-08-27。

`kokoro-capability` 管理用户、项目和 session 的 Skill/MCP 资源。它是资源目录与授权事实 owner，
不是 Agent runtime、Feature 组装器或 GA checkpoint owner。

## 1. Owner 划分

```text
Capability
  -> Skill/MCP 的 subject/session logical path、可见性、CRUD、授权结果

Storage
  -> package bytes、checksum/scan、Asset/Artifact 生命周期

GA
  -> 默认 Skill、find_skills/load_skill、Workbench、Agent/Feature、RunLedger、native checkpoint
```

Capability 不拥有 GA 默认 Skill、Agent、Feature、DeepAgents state、LangGraph thread、Workbench、
Artifact bytes、S3 bucket、用户聊天事实或 Billing。

## 2. Skill public contract

GA 的 `find_skills` 需要外部资源时，通过 Capability public contract 获取**当前可见的短摘要**：

```text
GA -> DiscoverVisibleSkills(query, limit <= 5)
Capability -> [{source_selector, scope_kind, display_name, summary, tags}]
```

模型不直接访问 Capability；GA 将返回结果转为当前调用的 opaque `candidate_ref`。`source_selector`、
`candidate_ref` 都不是路径，不能由模型自行拼接。

当模型调用 `load_skill(candidate_ref)` 时：

```text
GA
  -> 校验 candidate_ref 属于当前 Feature、subject、session 范围
  -> Capability ResolveVisibleSkill(source_selector)
  -> Storage 读取 package_asset_ref
  -> 校验 SKILL.md / checksum
  -> 写入当前 DeepAgents Workbench
```

Capability 只返回当前可见的 source reference 和 Storage AssetRef，不返回 Agent、Tool、MCP、模型、
Sandbox、权限、计费或 ProductEvent 配方。

## 3. Subject、actor 与 session

Capability 的 Skill path 由受信 `ExecutionIdentity` 和 `session_id` 决定：

```text
subject path  -> 个人、项目或服务主体的共享 Skill
session path  -> 当前 ProductSession 专属 Skill
actor         -> 本次请求的发起者，只用于 IAM 授权和审计
```

actor 不会自动产生个人 Skill overlay。GA 不向 Capability 传 RuntimeNamespace、LangGraph thread、
裸 user/project ID 或本地路径。

## 4. MCP 边界

Capability 管理 MCP 注册信息、可见性、授权和凭据句柄。GA 的 `clients/mcp.py` 只读取当前运行所需
的连接描述，再由 GA MCP adapter 执行调用。明文凭据、Capability 数据库连接和 MCP CRUD 均不进入
Agent/Feature API。

## 5. 内容与完整性

Skill 包遵循 DeepAgents 的 `SKILL.md` 形状。Capability 负责 source 可见性和 CRUD；Storage 负责
bytes、扫描和生命周期；GA 负责读取后的格式校验与 Workbench 挂载。摘要或 checksum 只用于完整性
和审计，不构成 Skill release、Session 版本或 Agent 绑定机制。

普通 CRUD 只影响下一次 `find_skills`。已经加载到当前 thread Workbench 的内容保持不变；显式撤销在
下一次 `load_skill` 或工具边界拒绝，恢复不会重新接受浏览器传入的路径。

## 6. 可用性与故障

- Capability/Storage 暂不可用时，GA 默认 Skill 和已挂载 Skill 仍可使用；
- 外部摘要不可用时，`find_skills` 返回 GA 默认摘要并明确来源不可用，不从旧缓存伪造候选；
- source withdrawn、scan 非 clean、checksum 失配或超出大小/路径限制时，不挂载；
- Capability 不直接写 GA Workbench，GA 也不直接写 Capability 数据库；
- 任何 public contract 重试都以 `request_id` 和 operation digest 幂等。

## 7. 验收门

- Capability 只暴露 Skill/MCP 当前 owner 事实，不暴露 GA 内部 namespace/thread；
- GA 默认 Feature 在 Capability/Storage 离线时仍可执行；
- `find_skills` 只返回当前可见摘要，`load_skill` 只接受当前 opaque candidate；
- Skill 内容不改变 Agent、Feature、Swarm、工具、权限、计费或模型；
- subject/session path 的越权、路径穿越、跨 session 读取和撤销后加载均被拒绝；
- package bytes 和 Artifact 生命周期始终由 Storage public contract 管理。

## 8. Feature-first target boundary

当前 Feature-first 目标能力边界是 subject/session Skill logical path、可见性与 CRUD，以及
MCP/Connector control-plane policy；不存在 runtime snapshot、Skill 发布平台或会话执行配置。
Target endpoint card：只传当前操作所需的最小事实，禁止把运行时状态、路径或凭据带入 Capability。

旧设计审计中出现的 `DiscoverVisibleSkillPaths`、`ResolveVisibleSkillPath` 是迁移期术语别名；
当前 v1 wire 使用 `DiscoverVisibleSkills`、`ResolveVisibleSkill`。RuntimeNamespace、thread_id、raw subject/path
不是 Capability public request 字段，可信 subject/scope 只来自 IAM attestation。
**它不接收 GA RuntimeNamespace**；`RunExecutionAttestation` 的 source-owner proof 不携带 RuntimeNamespace。

Capability metadata
是 source data，不是 prompt/Tool/权限声明；dynamic `SKILL.md`/resource 是受限 tool data，
只能在 GA 当前调用的边界内读取，不能改变 static ToolPolicy、权限或 Feature 配置。

## 100 分证据

| 维度 | 可验证证据 |
|---|---|
| owns / doesNotOwn | 本卡第 1 节；`kokoro-capability/docs/OWNER_AND_MIGRATION.md` |
| 唯一入口与目录边界 | `kokoro-capability/src/main.ts`；`kokoro-capability/test/architecture/architecture.test.ts` |
| Root v1 contract | `contract/proto/kokoro/capability/v1/capability_runtime.proto`；生成镜像 provenance check |
| MySQL / Redis；不使用 MongoDB | `kokoro-capability/database/schema.sql`；`kokoro-capability/docs/SCHEMA_OWNER_INVENTORY.md`；Capability 无 Mongo client/package/config；Redis 非 PONG 时 fail closed |
| Skill / Connector / MCP client | `kokoro-capability/src/infrastructure/capability/capability-client.ts` 与 `capability-facades.ts`；各资源 client 独立可部署 |
| Storage 协作 | `src/infrastructure/storage/storage-client.ts` 只消费 Storage public contract，不读取 Storage schema、bucket 或 object key |
| MCP 运行边界 | `McpServer` / `McpConnection` 仅保存 control-plane declaration/policy；MCP Client、Host、session、invocation 属于 runtime owner |
| 授权与撤销 | `test/integration/capability-service.test.ts`、`connector-revocation.test.ts`、`mcp-http.test.ts` |
| Skill package 完整性 | portable `SKILL.md` manifest gate、Storage clean gate、digest match 与 package installation tests |
| 迁移与旧写面 | `kokoro-capability/docs/MIGRATION_PLAN.md`；旧 snapshot RPC 只保留兼容 descriptor，不挂载生产 service |

复核命令：`cd kokoro-capability && pnpm verify`；根契约执行
`python3 contract/validate_slice_a_manifest.py contract/slice-a-contract-manifest.yaml` 与
`uv run python scripts/contract/render_slice_a.py --manifest contract/slice-a-contract-manifest.yaml --check`。
