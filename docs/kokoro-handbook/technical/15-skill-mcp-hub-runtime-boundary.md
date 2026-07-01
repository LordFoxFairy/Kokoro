# Skill Hub / MCP Hub 与三仓运行时边界方案

## 定位

本文只定义 `kokoro-web`、`kokoro-session`、`kokoro-agent` 如何接入
Skill Hub / MCP Hub 的运行时边界。它不是 Hub/Platform 的权威数据库设计，
也不要求三仓在 V1 内实现完整 marketplace。

核心判断：

```text
Hub 是产品资产与治理层。
session 是 run capability snapshot 的拥有者。
agent 是 runtime compiler + executor。
web 是 display manifest consumer + per-run selector。
```

因此：

```text
web 不直连 agent。
agent 不拥有 Hub catalog、安装关系、审核关系。
session 不执行工具，不解析 secret 明文。
Hub/Platform 不进入 token stream 热路径。
```

## 非目标

V1 不做完整 Hub 产品化：

```text
不做：
  公开广场排名、评分、收益分成。
  三方托管 MCP 平台。
  agent 内建 marketplace。
  web 通过 agent 查询能力目录。
  session 直接实现 Hub 后台管理。

要做：
  三仓运行时契约先稳定。
  session 能持久化每次 run 的能力快照。
  agent 能从快照编译 runtime。
  web 能用快照渲染历史 run 的能力来源。
```

## 总链路

```text
kokoro-web
  展示目录、安装状态、权限提示和本轮选择。
  只调用 Hub/Platform API 与 kokoro-session。

Hub / Platform
  拥有 catalog、版本、安装、启用、审核、权限、secret 授权关系。
  为 session 提供 resolver，不参与 token 流。

kokoro-session
  接收 web 的 selectedSkillIds / selectedMcpServerIds / selectedToolNames。
  调 resolver 生成 RunCapabilitySnapshot。
  持久化 snapshot，再投递 run.request 给 agent。

kokoro-agent
  只消费 RunCapabilitySnapshot.runtime。
  编译 DeepAgents/LangChain runtime。
  执行工具、MCP、subagent、middleware、HITL、sandbox。
```

## V1 能力边界

V1 的运行时能力按 fail-closed 处理：

```text
默认可用：
  内置工具。
  ask_user_question HITL 工具。
  内置 subagent。
  local_shell backend。
  HTTP MCP adapter。

可配置但必须显式打开：
  e2b backend。
  custom sandbox backend。
  外部 artifact/object storage。

未来能力：
  stdio MCP。
  SSE MCP。
  commandRef 启动外部本地进程。
```

`stdio`、`sse`、`commandRef` 可以在 manifest 版本中预留字段，但 V1 runtime
默认不执行。只有满足以下条件才允许打开：

```text
1. 管理员显式启用。
2. resolver 下发的 policy 允许。
3. agent sandbox/backend 支持该 transport。
4. capability lock 校验通过。
5. secret grant 在有效期内。
```

任意条件缺失时，agent 必须拒绝编译该 capability，并返回可审计的 admission 错误。

## Manifest 双视图

### Display Manifest

Display Manifest 给 web 和后台管理使用，是实时产品视图：

```text
SkillDisplayManifest
  schemaVersion
  skillId
  versionId
  slug
  name
  shortDescription
  longDescription
  icon
  screenshots[]
  categories[]
  tags[]
  author
  ownerType: official | workspace | user | community
  visibility: public | workspace | private
  official
  reviewStatus: draft | pending_review | published | deprecated
  riskLevel: safe | approval_required | admin_required
  requiredPermissions[]
  requiredSecrets[]
  installState
  enabledState
  examples[]
```

```text
McpDisplayManifest
  schemaVersion
  mcpServerId
  versionId
  slug
  name
  description
  icon
  provider
  transport: http | stdio_future | sse_future
  toolCount
  exposedToolNames[]
  requiredPermissions[]
  requiredSecrets[]
  riskLevel
  official
  reviewStatus
  installState
  enabledState
```

Display Manifest 可以包含文案、图片、运营字段、安装状态和启用状态。agent 不消费
Display Manifest。

### Runtime Manifest

Runtime Manifest 给 agent runtime compiler 使用，必须小而确定：

```text
SkillRuntimeManifest
  schemaVersion
  skillId
  versionId
  lockId
  name
  namespace
  promptFragments[]
  toolRefs[]
  subagentRefs[]
  middlewareRefs[]
  mcpServerRefs[]
  approvalRules[]
  filesystemPolicy?
  sandboxPolicy?
  resourceLimits?
  artifactPolicy?
```

```text
McpRuntimeManifest
  schemaVersion
  mcpServerId
  versionId
  lockId
  namespace
  transport: http | stdio_future | sse_future
  endpointRef?
  commandRefFuture?
  secretGrantRefs[]
  toolAllowlist[]
  approvalRules[]
  timeoutMs
  networkPolicy?
```

Runtime Manifest 不能包含 marketplace 展示信息，不能包含明文 secret，不能带用户
安装状态。

## RunDisplaySnapshot

历史 run 不能引用实时 Display Manifest，否则 skill 改名、下架、安装状态变化后，
历史聊天会变得不可解释。session 必须保存不可变展示快照：

```text
RunDisplaySnapshot
  skillCards[]
    skillId
    versionId
    name
    icon
    ownerType
    official
    sourceLabel
    riskLevel
    reviewStatusAtRun
    capabilityHash

  mcpCards[]
    mcpServerId
    versionId
    name
    icon
    provider
    transportLabel
    official
    sourceLabel
    riskLevel
    reviewStatusAtRun
    capabilityHash

  toolCards[]
    toolName
    namespace
    displayName
    sourceRef
    riskLevel
```

RunDisplaySnapshot 不保存 `installState` / `enabledState`。这两个是实时账号状态，
不属于历史 run。

## RunCapabilitySnapshot

`kokoro-session` 在 run admission 成功后生成并持久化本轮能力快照：

```text
RunCapabilitySnapshot
  snapshotId
  schemaVersion
  siteId
  workspaceId?
  projectId?
  userId
  sessionId
  runId
  createdAt

  selected:
    skillVersionIds[]
    mcpServerVersionIds[]
    toolNames[]

  display:
    RunDisplaySnapshot

  runtime:
    skills: SkillRuntimeManifest[]
    mcpServers: McpRuntimeManifest[]
    tools: ToolRuntimeManifest[]
    subagents: SubagentRuntimeManifest[]
    approvalPolicy
    backendPolicy
    sandboxPolicy

  locks:
    manifestHashes[]
    policyHash
    schemaHash
    packageLocks[]
    skillLocks[]
    mcpLocks[]

  grants:
    secretGrants[]

  audit:
    resolvedBy
    resolverVersion
    policyVersion
    resolverInputHash
```

session 保存 snapshot 的原因：

```text
1. replay 时 web 能知道当时这个工具/skill 的名字、图标、风险来源。
2. 审计时能解释本次 run 为什么有某个 MCP tool。
3. skill 更新不会改变历史 run 的含义。
4. agent 重启/resume 时不需要回查 Hub。
5. web 不需要调用 agent 获取展示数据。
```

## 三仓接口

### Web -> Hub / Platform

用于目录、安装、启用和选择。V1 没有正式 Hub 服务时，web 可以使用本地静态
catalog stub，但字段必须对齐 Display Manifest。

```text
GET /hub/skills
GET /hub/skills/:skillId
POST /hub/skills/:skillId/install
POST /hub/skills/:skillId/enable

GET /hub/mcp-servers
GET /hub/mcp-servers/:mcpServerId
POST /hub/mcp-servers/:mcpServerId/install
POST /hub/mcp-servers/:mcpServerId/enable
```

这些 API 属于 Hub/Platform，不属于 agent。

### Web -> Session

web 发消息时只带用户本轮选择，不带完整 manifest：

```text
POST /sessions/:sessionId/messages
  idempotencyKey
  content
  executionStyle?
  selectedSkillIds?
  selectedMcpServerIds?
  selectedToolNames?
```

web 不传 secret，不传 Runtime Manifest，不传工具实现。

### Session -> Capability Resolver

session 在 startRun 时请求解析：

```text
POST /capabilities/resolve-run-snapshot
  siteId
  workspaceId?
  projectId?
  userId
  sessionId
  runId
  selectedSkillIds[]
  selectedMcpServerIds[]
  selectedToolNames[]
  executionStyle?
```

返回：

```text
RunCapabilitySnapshot
```

如果 Hub/Platform V1 未落地，session 先用本地 resolver fake。fake 的接口必须和正式
resolver 一致，不能让 agent 或 web 直接读取 fake 数据。

### Session -> Agent

`run.request` 目标结构：

```text
kind: run.request
site_id
session_id
run_id
agent_run_input:
  siteId
  workspaceId?
  projectId?
  sessionId
  runId
  userId
  inputMessageId
  assistantMessageId
  content
  attachments[]
  execution
  modelRuntime
  capabilitySnapshot
```

Agent 接收的是 `capabilitySnapshot.runtime` 和受限 grant，不接收 Hub catalog。

## Agent RuntimeCompiler

`kokoro-agent` 只实现能力编译器：

```text
RuntimeCompiler.compile(input: AgentRunInput) -> CompiledRuntime
```

输入：

```text
AgentRunInput.capabilitySnapshot.runtime
```

输出：

```text
CompiledRuntime
  model
  tools[]
  subagents[]
  systemPrompt
  middleware[]
  interruptOn
  permissions
  checkpoint
  backend
  sandbox
```

编译规则：

```text
1. skills.promptFragments 合并进 system prompt，但必须保留来源边界。
2. mcpServers 编译成 MCP client/tool adapters。
3. approvalRules 编译成 DeepAgents/LangChain HITL interrupt_on。
4. filesystemPolicy 编译成 DeepAgents FilesystemPermission。
5. sandboxPolicy 决定 local_shell/e2b/custom execution backend。
6. secretGrantRefs 只能解析 snapshot 内授权的 grant。
7. lockId 用于审计和复现，不用于排序。
8. namespace 决定工具命名空间，冲突时 fail-closed。
```

Agent 中禁止出现：

```text
HubCatalogStore
SkillInstallStore
McpMarketplaceClient
UserSkillRepository
WorkspaceMcpRepository
```

这些属于 Hub/Platform。

## Secret Grant 边界

secret 不能用“裸 secretRef 任意查询”的方式下发给 agent。resolver 必须生成受限 grant：

```text
SecretGrant
  grantId
  secretRef
  scope:
    siteId
    workspaceId?
    projectId?
    userId
    runId
    capabilityRef
    toolNames[]
  expiresAt
  audience: agent-runtime
  noLog: true
```

规则：

```text
1. agent 只能解析 snapshot.grants 内的 grant。
2. grant 绑定 site/workspace/user/run/capability/tool。
3. grant 过期、撤销、scope 不匹配时 fail-closed。
4. secret 明文不得进入 session events、SSE、web state、日志。
5. 每次 grant 解析必须写审计记录。
6. agent 不能按任意 secretRef 查询 secret manager。
```

## 权限合并规则

Skill/MCP 权限分三层：

```text
Catalog 权限：
  用户能不能看到这个 skill/mcp。

Install 权限：
  用户或 workspace 能不能安装。

Run 权限：
  本轮 run 能不能启用，并且哪些 tool 需要 HITL。
```

策略合并顺序：

```text
managed policy
site policy
workspace policy
project policy
user policy
request policy
```

硬规则：

```text
1. deny 优先级最高。
2. 未识别 policy version fail-closed。
3. 高风险工具默认 ask 或 deny，不能默认 allow。
4. request policy 只能收紧，不能放宽上层限制。
5. tool namespace 冲突时拒绝编译，不做隐式覆盖。
6. 每个 HITL approve/reject/respond/edit 都必须可审计。
```

## Lock 与版本规则

Runtime Manifest 必须可复现：

```text
必须覆盖：
  manifest schemaVersion。
  prompt fragment hash。
  tool schema hash。
  middleware hash。
  subagent spec hash。
  MCP tool list hash。
  policy hash。
  package/directory lock hash。
```

规则：

```text
1. unsupported schemaVersion fail-closed。
2. lock hash 不匹配 fail-closed。
3. lock 不参与排序。
4. eventId 不参与排序。
5. replay 排序真源仍是 session 持久化追加顺序与 SSE 单连接发送顺序。
```

## 数据归属

本文只声明三仓运行时的数据责任：

```text
kokoro-session:
  sessions
  messages
  runs
  session_events
  run_capability_snapshots

kokoro-agent:
  checkpoint
  memory
  run_state
  artifact runtime refs

kokoro-web:
  UI state
  selected capability ids
  local draft
```

Hub/Platform 的 catalog、安装、启用、审核、secret 授权和后台审计属于平台域。
具体 MySQL 表和 Mongo 集合由平台文档定义，本文不作为权威 schema。

Redis 只做短期运行时：

```text
实时队列。
live stream。
短 TTL lock。
capability resolver cache。
```

Redis 不能作为 Hub catalog 或 run snapshot 长期真源。

## Web 呈现原则

web 展示产品语义，不展示 agent 内部：

```text
展示：
  能力名、图标、来源、官方标识、风险、所需授权、安装状态、启用状态、示例。

历史 run 展示：
  使用 RunDisplaySnapshot。
  不读取实时 installState / enabledState 改写历史。

不展示：
  raw system prompt。
  secretGrant。
  MCP endpoint 明文。
  DeepAgents middleware 内部结构。
```

聊天过程里的 tool/subagent 渲染：

```text
1. session event 只带 tool name / tool id / source refs。
2. web 从 run snapshot display 补展示名、图标、风险标签。
3. 如果 display 缺失，降级显示 tool name，不中断流。
```

## 业务链路

### 浏览与安装

```text
1. web 进入 Skill Hub / MCP Hub。
2. web 调 Hub API 获取 Display Manifest 列表。
3. 用户安装或启用。
4. Hub/Platform 写安装关系和审计日志。
5. 需要 secret 时走授权流程，明文进入 secret manager，业务库只存 ref。
```

### 发起聊天 run

```text
1. 用户在 web 选择本轮 skill/mcp/tool。
2. web POST /sessions/:id/messages，只传 selected ids。
3. session admission 检查同 session active run。
4. session 调 resolver 得到 RunCapabilitySnapshot。
5. session 写 message、run、run_capability_snapshot。
6. session 投递 run.request 给 agent。
7. agent RuntimeCompiler 编译 snapshot。
8. agent 执行并输出 raw events。
9. session normalize + append session_events + live SSE。
10. web 用 session events + RunDisplaySnapshot 渲染。
```

### 审批和 HITL

```text
1. agent 根据 approvalRules 触发 interrupt_on。
2. session 转成 tool.awaiting_approval。
3. web 展示来自 RunDisplaySnapshot 的风险说明和工具摘要。
4. 用户 approve/reject/respond/edit。
5. web POST control 到 session。
6. session 转发 run.resume。
7. agent resume 并继续执行。
8. session 写 HITL 决策审计。
```

## 分期

### P0：三仓运行时边界

```text
web:
  保留 selectedSkillIds / selectedMcpServerIds / selectedToolNames。
  加静态 Display Manifest stub，只用于 UI，不给 agent。

session:
  定义 RunCapabilitySnapshot schema。
  startRun 生成本地 fake snapshot 并随 run 存储。
  run.request 下发 agent_run_input.capabilitySnapshot。

agent:
  接受 AgentRunInput.capabilitySnapshot。
  RuntimeCompiler 支持内置 tools、ask_user_question、built-in subagents。
  HTTP MCP adapter 可以接入，stdio/sse 默认 fail-closed。
  不查询 Hub。
```

### P1：接入外部 resolver

```text
Hub/Platform:
  提供 capability resolver API。
  提供 Display Manifest API。
  提供 secret grant 授权结果。

session:
  fake resolver 替换成 HTTP/RPC resolver。
  run snapshot 持久化和 replay API。
```

P1 对三仓的要求是消费 resolver，不是让三仓实现 Hub/Platform。

### P2：完整 runtime adapter

```text
agent:
  MCP adapter 扩展。
  skill prompt/tool/subagent/middleware loader。
  e2b/custom sandbox。
  capability lock 校验。

web:
  Hub 搜索、安装、权限提示、per-run 选择器。
  聊天过程按 snapshot 展示能力来源。
```

## 风险和边界

```text
风险：web 需要展示 agent runtime 信息。
处理：展示信息来自 Display Manifest / RunDisplaySnapshot，不来自 agent。

风险：agent 需要知道用户安装了什么。
处理：session/resolver 在 run 前解析，agent 只消费 snapshot。

风险：skill 更新后历史 replay 变样。
处理：run snapshot pin versionId、lockId、hash 和 display。

风险：MCP secret 泄露到 web/session。
处理：web/session 只见 grant/ref，明文只在授权执行边界短暂出现。

风险：Runtime Manifest 过大。
处理：只传本轮运行需要的最小子集，长文档用锁定 ref。

风险：Hub 未落地时三仓空等。
处理：P0 使用 session fake resolver，但接口形状与正式 resolver 一致。

风险：为了支持所有 transport 把 agent 打开成任意进程启动器。
处理：stdio/sse/commandRef 默认未来态，未显式授权和 sandbox 支持时 fail-closed。
```

## 最终结论

```text
Skill/MCP Hub 是产品资产系统。
kokoro-agent 是 runtime compiler + executor。
kokoro-session 是 run snapshot owner + relay。
kokoro-web 是 display manifest consumer + per-run selector。

web 不调 agent。
agent 不拥有 Hub。
session 不执行能力。
Hub 不参与 token 流热路径。
```
