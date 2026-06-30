# Kokoro Agent Runtime 重构实施方案

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development
> or superpowers:executing-plans to implement this plan. Steps use checkbox
> (`- [ ]`) syntax for tracking.

**Goal:** 把 `kokoro-agent` 重构成 manifest-first、DeepAgents/LangChain 原生优先、
轻量 DDD 的执行 runtime。

**Architecture:** Agent 不做沉重 DDD，不自研第二套 agent framework。稳定边界只保留
入站 manifest、runtime policy、AgentEvent 和少量协议接口；模型、HITL、tools、
subagents、skills、filesystem、backend、checkpoint 尽量映射到 DeepAgents/LangChain
原生 primitives。

**Tech Stack:** Python、Pydantic v2、DeepAgents 0.6.6、LangChain/LangGraph、
Redis、Mongo checkpoint/run_state、uv、pytest、pyright、ruff。

---

## 结论

当前 `kokoro-agent` 已经能跑，但不是最终标准形态。它的问题不是“没有 DDD”，
而是轻量边界没有收紧：

```text
RunRequest 仍是旧扁平结构。
permission_mode 混合了工具模式和审批策略。
conversation_id 被用作 LangGraph thread_id，但 agent 不应拥有聊天历史事实源。
build_agent 直接拼 tools/subagents/permission，缺 manifest compiler。
runtime_subagent 允许模型现场写 system_prompt 并执行，默认太危险。
DeepAgents 原生 middleware/backend/skills/permissions 没被充分利用。
tools 文件和工具命名仍有 demo 味道。
application/projection/awaiting.py 命名抽象，HITL 事件语义不够显式。
审批只写了 approve/reject/edit/respond，但没有拆清结构化按钮、自由文本审批、
外部执行工具和参数编辑白名单。
```

目标不是写更多层，而是把不稳定的东西集中在少数边界。

## 不变量

```text
1. AgentRunInput 是 run.request 唯一产品上下文。
2. agent 不读取 session Mongo，不写 session messages/events。
3. agent 不扣积分，不决定价格，不直接写业务库。
4. agent 不使用 seq、eventPosition 或 BaseMessage.id 做跨服务排序。
5. LangGraph thread_id 使用 runId；sessionId 只是业务上下文。
6. 同 session 单 active run 由 session admission 保证。
7. runtime subagent 默认不能由模型自由创建并执行。
8. DeepAgents/LangChain 有原生能力时，Kokoro 只做编译和策略边界。
9. 不保留旧 flat RunRequest、permissionMode、conversation_id 兼容路径。
10. 不使用 `ports/` 目录命名。
11. `__init__.py` 只做导出，不放业务逻辑。
12. 工具执行前拦截必须发生在 framework pause/interrupt 边界，不在工具内部
    “先执行再补救”。
13. 自由文本审批必须保守：无法严格判断时默认 reject，不默认 approve。
```

## 目标目录

```text
kokoro_agent/
  interfaces/
    worker.py
    inbound.py
    envelope.py

  domain/
    agent_run_input.py
    agent_event.py
    runtime_policy.py
    capabilities.py
    subagent_profile.py
    json_payload.py
    tool_names.py
    prompts/
      system.md

  application/
    runtime/
      compiler.py
      compiled_runtime.py
      supervisor.py
      invoke.py
      stream_consumer.py
    projection/
      agent_event_mapper.py
      approval_projection.py
    protocols/
      agent.py
      run_state.py
      stream.py

  infrastructure/
    deepagents/
      agent_factory.py
      backend_factory.py
      middleware_factory.py
      subagent_factory.py
      skill_loader.py
    model/
      chat_model.py
      local_fake.py
      settings.py
    tools/
      registry.py
      current_time.py
      web_fetch.py
      capability_tool.py
      mcp_tool_loader.py
    sandbox/
      execution_sandbox.py
      local_shell.py
      e2b.py
      custom.py
    permission/
      approval_policy.py
      filesystem_permissions.py
    checkpoint/
      factory.py
    run_state/
      factory.py
      mongo_store.py
      sqlite_store.py
    transport/
      factory.py
      memory_stream.py
      redis_stream.py
    config.py
    observability.py
```

说明：

```text
domain
  只放稳定数据模型和业务语言，不引用 DeepAgents/LangChain。

application/runtime
  编排一次 run：compile -> invoke -> stream -> terminal claim。

infrastructure/deepagents
  唯一 DeepAgents/LangChain 构造适配点。

infrastructure/tools
  只放 Kokoro 自有工具和 tool loader。DeepAgents 内置文件/execute 工具不在这里重写。

infrastructure/sandbox
  执行副作用隔离策略，不等于 storage backend。
```

## 核心模型

### AgentRunInput

创建 `kokoro_agent/domain/agent_run_input.py`：

```text
AgentRunInput
  ids
    siteId
    workspaceId?
    projectId?
    sessionId
    runId
    userId
    inputMessageId
    assistantMessageId

  input
    content
    attachments[]

  context
    recentMessages[]
    summary?
    artifactRefs[]
    toolResultRefs[]
    userProvidedFiles[]

  modelRuntime
    provider
    model
    reasoningEffort?
    responseFormat?

  execution
    style: fast | thinking
    toolMode: auto | none | required

  approvalPolicy
    defaultAction: allow | ask | deny
    rules[]

  backendPolicy
    storageBackend: state | store | custom
    executionSandbox: none | local_shell | e2b | custom
    resourceLimits?
    networkPolicy?
    artifactStorage?

  capabilities
    skills[]
    mcpServers[]
    tools[]
    subagents[]
    locks

  traceContext
    requestId
    idempotencyKey?
```

`AgentRunInput` 是 session/platform 编译后的 manifest。Agent 不再补查全局 skill、
MCP、权限或聊天历史。

### RunRequest

`run.request` 只保留：

```text
kind: run.request
site_id
session_id
run_id
agent_run_input
```

删除：

```text
conversation_id
input
execution_style
permission_mode
```

LangGraph config：

```text
thread_id = agent_run_input.ids.runId
```

原因：checkpoint 只用于一次 run 的暂停/恢复。聊天历史由 session 的
`recentMessages` manifest 传入，不靠 agent checkpoint 跨 run 续命。

### CompiledAgentRuntime

创建 `kokoro_agent/application/runtime/compiled_runtime.py`：

```text
CompiledAgentRuntime
  runId
  sessionId
  threadId
  initialPayload
  model
  tools
  subagents
  skills
  memory
  middleware
  interruptOn
  permissions
  backend
  checkpointer
  traceConfig
```

这是 application 和 DeepAgents adapter 之间的唯一交接对象。

### ApprovalIntent

创建 `kokoro_agent/domain/runtime_policy.py` 时同时定义审批意图：

```text
ApprovalIntent
  kind: structured | free_text | external_execution
  approvalBatchId
  ordinal
  toolCallId
  actionName
  originalArgs
  editableFields[]
  allowedActions[]
  preview?
```

说明：

```text
structured
  Web 按按钮提交 approve/reject/edit/respond。

free_text
  用户在暂停态直接输入自然语言。系统可用一个无工具、无历史、单次
  structured-output 的审批解释器，把文本转成 approve/reject/edit/respond。

external_execution
  工具本体不在 agent 里执行，例如 OAuth 授权、表单确认、高成本确认、
  浏览器侧文件选择。Web 或 owning service 返回结果后再 resume。
```

`ApprovalIntent` 不是新的框架 runtime，只是 Kokoro 对 DeepAgents/LangChain
pending tool call 的产品语义封装。

## DeepAgents / LangChain 映射

本地已确认 `deepagents 0.6.6` 的 `create_deep_agent` 原生支持：

```text
model
tools
system_prompt
middleware
subagents
skills
memory
permissions
backend
interrupt_on
response_format
state_schema
context_schema
checkpointer
store
debug
name
cache
```

因此 Kokoro 不应该自研：

```text
agent loop
tool calling runtime
HITL interrupt runtime
filesystem read/write/edit/grep/execute 工具
subagent task runtime
skills progressive disclosure runtime
checkpoint runtime
backend file view runtime
```

Kokoro 应该负责：

```text
manifest strict parse。
权限、lock、policy 编译。
工具/skill/MCP 白名单过滤。
provider 密钥和 site/workspace/project 上下文传递。
AgentEvent 投影。
run 去重、terminal claim。
```

### DeepAgents 原生对应关系

工具执行前人工审批：

```text
DeepAgents/LangChain:
  HumanInTheLoopMiddleware，由 create_deep_agent(interrupt_on=...) 注入。

Kokoro:
  approvalPolicy 编译成 interrupt_on。
```

审批动作：

```text
DeepAgents/LangChain:
  InterruptOnConfig.allowed_decisions 原生支持 approve/edit/reject/respond。

Kokoro:
  Web 只提交当前 action 允许的 decision。
```

reject / respond：

```text
DeepAgents/LangChain:
  reject 生成 error ToolMessage。
  respond 生成 success ToolMessage，并跳过真实工具执行。

Kokoro:
  agent 投影 synthetic resolution event。
  respond 可承载外部执行结果，例如表单、授权、高成本确认。
```

主动询问用户：

```text
DeepAgents/LangChain:
  ask_user_question 是普通 StructuredTool。
  interrupt_on 将 ask_user_question 配置为 input_required。
  用户回答通过 respond decision 变成 success ToolMessage。

Kokoro:
  ask_user_question 工具本体不直接执行。
  Web 渲染问题卡片；用户提交后 session 转 run.resume/respond。
```

工具参数 edit：

```text
DeepAgents/LangChain:
  edit decision 会替换 tool call args。

Kokoro:
  必须先校验 editableFields，不能让模型或用户扩大权限。
```

工具执行 wrapper：

```text
DeepAgents/LangChain:
  AgentMiddleware.awrap_tool_call 或 wrapped StructuredTool。

Kokoro:
  做参数校验、错误 envelope、结果摘要、capability RPC。
```

文件工具权限：

```text
DeepAgents:
  FilesystemPermission 支持 allow/deny。

Kokoro:
  只用于文件读写 allow/deny；需要审批时仍走 interrupt_on。
```

shell/code 执行：

```text
DeepAgents:
  execute 只在 backend 支持 SandboxBackendProtocol 时真实执行。

Kokoro:
  executionSandbox=none 时必须禁用或确保 execute 不可用。
  production 不能使用 local shell 作为安全边界。
```

skills：

```text
DeepAgents:
  SkillsMiddleware / skills=，支持 progressive disclosure。

Kokoro:
  只从 manifest lock 暴露 skill source。
```

subagents：

```text
DeepAgents:
  SubAgent / CompiledSubAgent / AsyncSubAgent。

Kokoro:
  只编译 manifest 中的 profile。
  remote / compiled subagent 需要各自配置审批。
```

默认内置工具：

```text
DeepAgents:
  默认注入 write_todos、filesystem、可能的 task。

Kokoro:
  compiler 必须显式排除未授权内置工具。
  不能以为 tools=[] 就无工具。
```

实现提醒：

```text
create_deep_agent(tools=...) 是 additive，不是替换默认工具。
如果 manifest 不允许 filesystem/execute/task/write_todos，必须通过 DeepAgents
harness/profile/exclusion 能力或 adapter 明确禁掉。
Declarative SubAgent 默认继承顶层 interrupt_on；CompiledSubAgent 和 AsyncSubAgent
不自动继承，必须在各自 runnable/remote runtime 内配置。
FilesystemPermission 不是审批系统，不能替代 HITL。
```

## Runtime Compiler

创建 `kokoro_agent/application/runtime/compiler.py`。

职责：

```text
AgentRunInput -> CompiledAgentRuntime
```

编译规则：

```text
modelRuntime
  -> make_chat_model(...)

input + context.recentMessages
  -> initialPayload {"messages": [...]}

execution.toolMode
  none     -> 显式排除非必要工具，包括 DeepAgents 默认工具。
  auto     -> 暴露 manifest 允许的工具，并排除未授权默认工具。
  required -> 至少暴露一个可用工具，否则 fail loud。

approvalPolicy
  -> interrupt_on + filesystem permissions + wrapped tool policy。

backendPolicy.storageBackend
  state  -> DeepAgents StateBackend。
  store  -> DeepAgents StoreBackend。
  custom -> configured BackendProtocol。

backendPolicy.executionSandbox
  none        -> 不暴露 execute/shell/code 副作用。
  local_shell -> DeepAgents LocalShellBackend 或 sandbox wrapped tool，且仅 dev/test。
  e2b         -> E2B adapter，缺依赖或密钥 fail loud。
  custom      -> 自定义 ExecutionSandbox adapter。

capabilities.skills
  -> DeepAgents skills + backend 文件视图。

capabilities.mcpServers
  -> LangChain MCP adapter tools，按 allowedTools 过滤。

capabilities.subagents
  -> DeepAgents SubAgent / AsyncSubAgent / CompiledSubAgent。
```

`compiler.py` 不直接 import Redis/Mongo/Web，也不写事件。

## Permission / HITL

删除 `permissionMode`。

目标模型：

```text
execution.toolMode
  auto | none | required

approvalPolicy.defaultAction
  allow | ask | deny

approvalPolicy.rules[]
  match: tool:web_fetch | mcp:github:create_issue | subagent:researcher | sandbox:local_shell
  action: allow | ask | deny
  decisions: approve | reject | edit | respond
```

编译到原生能力：

```text
普通 LangChain tool
  -> interrupt_on

MCP tool
  -> MCP adapter tool + interrupt_on

filesystem
  -> DeepAgents FilesystemPermission

sandbox execute
  -> backend/sandbox adapter + interrupt_on

runtime subagent proposal
  -> ask 或 deny，不默认执行
```

### 两条 Resume 路径

结构化按钮路径：

```text
1. DeepAgents/LangChain 产生 pending action_requests。
2. agent 投影 tool_call_awaiting。
3. web 渲染按钮或可编辑表单。
4. web 提交 run.resume(decisions[])。
5. agent 按 approvalBatchId + ordinal 恢复。
```

自由文本路径：

```text
1. run 处于 awaiting。
2. 用户直接输入“可以，继续”或“改成发给 A，不要发给 B”。
3. session 不能创建新 active run；它应把该输入路由为 paused run 的 resume。
4. agent 使用 ApprovalDecisionInterpreter 做单次结构化判断。
5. 判断失败或 schema 校验失败，默认 reject。
6. 若包含 edit，必须只允许 UI/manifest 标记为 editable 的字段。
```

自由文本审批解释器约束：

```text
无工具。
无长期记忆。
不写 DB。
不读取 session Mongo。
输入只包含最近必要上下文、pending tool call、用户新消息。
输出 strict schema。
不能自己发明 editedArgs。
不能扩大权限或选择未列出的 action。
```

### Wire 建议

HITL wire：

```text
tool_call_awaiting
  approvalBatchId
  ordinal
  toolCallId
  actionName
  args
  editableFields
  allowedActions
  allowedDecisions
  approvalKind: confirmation | input_required | external_execution | authorization
  preview?
  inputRequest?

run.resume
  approvalBatchId
  decisions[]
    ordinal
    decision
    editedAction?
    message?
```

`toolCallId` 可用于 UI 和校验，但恢复顺序以 `approvalBatchId + ordinal` 对齐，
因为 LangGraph resume decisions 本身是顺序匹配。

### Reject / Respond 的权威结果

如果用户 reject、自由文本无法判断、或 edit 不合法，agent 必须合成一个
`tool_call_end` / tool resolution event，让后续模型上下文明确看到该工具已被取消。
不能只在 UI 上把卡片关掉。

### 外部执行工具

某些工具不应在 agent 进程直接执行：

```text
OAuth 授权。
高成本确认。
用户表单输入。
文件选择。
未来浏览器侧或 owning-service 侧任务确认。
模型主动询问用户。
```

这些工具进入模型时仍表现为 tool，但执行前必须产生 external execution pause。
Web 或 owning service 完成后，结果作为 tool result resume 回 LangGraph。

Kokoro 不需要为此自研一套暂停框架：优先使用 DeepAgents/LangChain
`interrupt_on`、wrapped tool 和 checkpoint resume 表达。

## Tools

内置工具只保留成熟、可解释、可治理的最小集合：

```text
current_time
  低风险，可默认暴露。

web_fetch
  有 SSRF 防护，但仍是网络读取能力，必须受 manifest/networkPolicy/approvalPolicy 管。

ask_user_question
  模型需要用户澄清、选择或提供少量输入时使用。它不是普通聊天消息，
  而是 input_required 型 HITL 工具。
```

### ask_user_question 工具

`ask_user_question` 是 V1 必须内置的交互工具。它的目标是让模型在缺少关键信息、
需要用户选择、需要轻量表单输入时暂停，而不是继续猜。

命名约定：

```text
Tool name: ask_user_question
Schema type: AskUserQuestionOption / AskUserQuestionResult
Web component: AskUserQuestionCard
```

工具名使用 Python/LangChain 常见的 snake_case；产品语义对齐 “Ask User Question”。

工具 schema：

```text
ask_user_question
  prompt: string
  description?: string
  inputType: text | textarea | single_choice | multi_choice | confirmation
  options?: AskUserQuestionOption[]
  required?: boolean
  allowCustomOption?: boolean

AskUserQuestionOption
  id: string
  label: string
  description?: string
```

执行语义：

```text
1. compiler 暴露 ask_user_question。
2. approvalPolicy 固定把 ask_user_question 编译为 input_required。
3. interrupt_on["ask_user_question"] 只允许 respond/reject，不允许 approve 后真执行。
4. agent 投影 tool_call_awaiting，approvalKind=input_required。
5. Session normalize 成浏览器可渲染的输入请求。
6. Web 渲染 AskUserQuestionCard。
7. 用户提交后，Session 发送 run.resume respond decision。
8. respond message 是结构化 JSON tool result，模型继续执行。
```

tool result schema：

```text
AskUserQuestionResult
  submitted: boolean
  value?: string
  selectedOptionIds?: string[]
  values?: object
  cancelled?: boolean
```

取消语义：

```text
用户取消 -> reject。
空回答且 required=true -> Web 不允许提交。
非法 option id -> Session 拒绝 resume。
```

Web 渲染要求：

```text
AskUserQuestionCard 必须显示在 assistant turn/activity 内，不作为新的 user message。
卡片展示 prompt、description、选项或输入框。
single_choice 用单选按钮或分段选项。
multi_choice 用 checkbox。
confirmation 用确认/取消按钮。
text/textarea 用输入框。
提交后卡片进入 settled 状态，显示用户回答摘要。
刷新/replay 后仍能恢复 pending 或 settled 状态。
同一 toolCallId 只能提交一次，重复提交必须幂等。
移动端文本和按钮不能溢出。
```

重命名：

```text
infrastructure/tools/clock.py -> current_time.py
infrastructure/tools/fetch.py -> web_fetch.py
```

工具名也同步标准化：

```text
now       -> current_time
fetch_url -> web_fetch
```

不保留旧工具名兼容。对应 session/web 测试一次性改净。

不在 V1 默认实现：

```text
通用本地 shell。
任意文件写入。
浏览器自动化。
runtime 自定义 system_prompt 子代理直接执行。
```

这些能力必须通过 `backendPolicy.executionSandbox` 和 manifest 显式打开。

工具执行前拦截规则：

```text
1. compiler 决定工具是否暴露。
2. approvalPolicy 决定工具是否 interrupt。
3. wrapper 只做参数校验、结果摘要、外部服务调用和 error envelope。
4. 高风险工具必须在执行前暂停，不允许先执行再询问。
5. 工具返回 ValidationError 时转结构化 tool error，允许模型修正参数后重试。
6. DeepAgents 默认工具也要经过 manifest gate；不能因为框架默认注入就默认开放。
```

## Subagents

保留 DeepAgents 原生 subagents，但删除默认运行时注册表路径。

删除或降级为实验能力：

```text
infrastructure/subagent/registry.py
infrastructure/tools/runtime_subagent.py
RuntimeSubagentRegistry
build_runtime_custom_subagent_tool
```

目标：

```text
SubagentProfile
  name
  description
  systemPromptRef 或 systemPrompt
  tools[]
  skills[]
  model?
  approvalPolicy?
  source: built_in | workspace | project | skill | experimental
```

运行规则：

```text
1. session/platform 在 AgentRunInput.capabilities.subagents 中列出允许 profile。
2. compiler 把 profile 编译成 DeepAgents SubAgent/AsyncSubAgent/CompiledSubAgent。
3. 模型只能调用 manifest 中存在的 subagent。
4. 未列出的动态子代理请求默认 deny。
5. 如果未来支持动态创建，只能作为 proposal event + HITL，而不是立即执行。
```

## Skills

V1 支持 skills，但 agent 不拥有 skill hub。

Agent 只消费：

```text
SkillRef
SkillLockEntry
skillPath 或 backend 文件视图
allowedTools
allowedMcpServers
```

编译：

```text
capabilities.skills -> DeepAgents skills + SkillsMiddleware/backend 文件视图
```

规则：

```text
Skill 不能扩大工具权限。
Skill lock hash 必须覆盖整个目录。
Skill 正文和附属资料按需加载，不一次性塞满 prompt。
未出现在 manifest 的 skill 不可见。
```

## MCP

Kokoro 不实现 MCP runtime。Agent 通过 LangChain MCP adapter 加载已授权工具。

命名：

```text
mcp__{serverSlug}__{toolName}
```

规则：

```text
只加载 manifest.allowedTools。
schema 按需加载。
凭据使用 authRef，由上游解析，不写入日志和事件。
大结果返回 summary + artifactRef，不把完整二进制或大 JSON 推入 SSE。
高风险 MCP tool 默认 ask 或 deny。
```

## Backend / Sandbox

必须拆开两个概念。

```text
storageBackend
  state | store | custom
  用于 DeepAgents 文件视图、skills、memory、上下文状态。

executionSandbox
  none | local_shell | e2b | custom
  用于 shell/code/browser 等副作用执行。
```

本地开发默认：

```text
storageBackend=state
executionSandbox=local_shell
```

生产默认：

```text
storageBackend=state 或 store
executionSandbox=none
```

如果生产需要代码执行：

```text
executionSandbox=e2b 或 custom
```

S3 不是 sandbox。S3 只能作为 artifact/object storage，或者某个 backend/sandbox
实现的外部存储组成。

## Run Supervisor

`RunSupervisor` 目标职责：

```text
parse 后的 InboundMessage dispatch。
run_state try_register。
run_state terminal claim。
resume/cancel 幂等保护。
调用 RuntimeCompiler。
调用 invoke_once。
```

它不应该：

```text
读取 permissionMode。
拼 HumanMessage(request.input)。
知道 tools/subagents 怎么构造。
知道 DeepAgents backend 细节。
使用 conversation_id。
```

`invoke_once` 目标职责：

```text
发布 run.started。
调用 agent.astream_events。
消费 v3 typed projections。
HITL pause 时发布 approval events。
自然完成时发布 terminal。
异常时发布 agent_error。
```

`stream_consumer.py` 可以继续保留并发消费四路投影，因为这是 LangGraph v3
typed projection 的正确消费方式；但注释要压缩，避免把复杂性解释成自研协议。

## Event Contract

AgentEvent 继续是 agent -> session 的 raw wire。

保留：

```text
agent_status
text_chunk
reasoning_chunk
tool_call_start
tool_call_awaiting
tool_call_end
agent_done
agent_error
```

调整：

```text
tool_call_awaiting 增加 approvalBatchId / ordinal / allowedDecisions。
tool_call_start/end 使用 actionName/toolName 统一命名。
text/reasoning 的 segmentId 来自 BaseMessage.id 或自生成 id，只做身份，不排序。
```

不新增：

```text
seq
eventPosition
cursor
lastResumeId
```

这些属于 session/web 传输或存储层，不进入 agent raw contract。

## 配置

短期继续保留 env var，因为 Docker/K8s 最稳定。

允许新增统一 loader，但只能在 `infrastructure/config.py` 收口：

```text
.env
.env.development
.env.test
.env.prod
.env.prerelease
.env.yaml
.env.example.yaml
真实环境变量覆盖本地文件
```

不要在各模块散落读取环境变量。

P0 必须支持：

```text
KOKORO_STREAM_BACKEND
KOKORO_REDIS_URL
KOKORO_CHECKPOINT_BACKEND
KOKORO_RUN_STATE_BACKEND
KOKORO_MONGO_URL
KOKORO_MONGO_DB
KOKORO_STORAGE_BACKEND
KOKORO_EXECUTION_SANDBOX
KOKORO_ENV
```

`local_shell` 在 `KOKORO_ENV=prod` 时必须 fail loud。

## 实施顺序

### Task 1: Contract First

**Files:**

```text
Create: kokoro-agent/src/kokoro_agent/domain/agent_run_input.py
Create: kokoro-agent/src/kokoro_agent/domain/runtime_policy.py
Create: kokoro-agent/src/kokoro_agent/domain/capabilities.py
Modify: kokoro-agent/src/kokoro_agent/domain/run_request.py
Modify: kokoro-agent/src/kokoro_agent/interfaces/inbound.py
Modify: kokoro-agent/tests/interfaces/test_inbound.py
Modify: kokoro-agent/tests/test_worker.py
```

- [ ] 新增 `AgentRunInput` Pydantic strict model。
- [ ] `RunRequest` 改为 manifest-first。
- [ ] 删除 `PermissionMode`。
- [ ] 删除 `conversation_id/input/execution_style/permission_mode`。
- [ ] 测试旧 flat run.request 必须 fail。
- [ ] 测试 session manifest run.request 必须 pass。

### Task 2: Runtime Compiler

**Files:**

```text
Create: kokoro-agent/src/kokoro_agent/application/runtime/compiler.py
Create: kokoro-agent/src/kokoro_agent/application/runtime/compiled_runtime.py
Move: kokoro-agent/src/kokoro_agent/application/run/supervisor.py
      -> kokoro-agent/src/kokoro_agent/application/runtime/supervisor.py
Move: kokoro-agent/src/kokoro_agent/application/run/invoke.py
      -> kokoro-agent/src/kokoro_agent/application/runtime/invoke.py
Move: kokoro-agent/src/kokoro_agent/application/run/consumer.py
      -> kokoro-agent/src/kokoro_agent/application/runtime/stream_consumer.py
Modify: kokoro-agent/src/kokoro_agent/interfaces/worker.py
Modify: kokoro-agent/tests/run/test_supervisor.py
Modify: kokoro-agent/tests/run/test_invoke.py
```

- [ ] 编译 `AgentRunInput` 到 `CompiledAgentRuntime`。
- [ ] `RunSupervisor` 只调用 compiler，不构造 tools/subagents。
- [ ] LangGraph `thread_id` 改为 `runId`。
- [ ] 删除 application 层的 `build_agent`。
- [ ] resume/cancel 测试改成 runId thread。

### Task 3: DeepAgents Adapter

**Files:**

```text
Create: kokoro-agent/src/kokoro_agent/infrastructure/deepagents/agent_factory.py
Create: kokoro-agent/src/kokoro_agent/infrastructure/deepagents/backend_factory.py
Create: kokoro-agent/src/kokoro_agent/infrastructure/deepagents/middleware_factory.py
Create: kokoro-agent/src/kokoro_agent/infrastructure/deepagents/subagent_factory.py
Create: kokoro-agent/src/kokoro_agent/infrastructure/deepagents/skill_loader.py
Delete: kokoro-agent/src/kokoro_agent/application/agent_factory.py
Delete or move: kokoro-agent/src/kokoro_agent/infrastructure/agent_builder.py
Modify: kokoro-agent/tests/test_factories.py
```

- [ ] `create_deep_agent` 只在 `infrastructure/deepagents/agent_factory.py` 调用。
- [ ] factory 参数与 `CompiledAgentRuntime` 对齐。
- [ ] 支持 `middleware/subagents/skills/memory/permissions/backend/interrupt_on`。
- [ ] DeepAgents 类型缺口只允许在 adapter 局部收口。

### Task 4: Approval Policy

**Files:**

```text
Create: kokoro-agent/src/kokoro_agent/infrastructure/permission/approval_policy.py
Create: kokoro-agent/src/kokoro_agent/infrastructure/permission/filesystem_permissions.py
Create: kokoro-agent/src/kokoro_agent/application/runtime/approval_decision.py
Move: kokoro-agent/src/kokoro_agent/application/projection/awaiting.py
      -> kokoro-agent/src/kokoro_agent/application/projection/approval_projection.py
Modify: kokoro-agent/src/kokoro_agent/interfaces/inbound.py
Modify: kokoro-agent/src/kokoro_agent/interfaces/envelope.py
Modify: kokoro-agent/tests/projection/test_awaiting.py
Modify: kokoro-agent/tests/run/test_hitl_e2e.py
Delete: kokoro-agent/src/kokoro_agent/infrastructure/permission/interrupt_config.py
```

- [ ] `approvalPolicy` 编译成 `interrupt_on`。
- [ ] approval event 输出 `approvalBatchId/ordinal/allowedDecisions`。
- [ ] `run.resume` 按 batch + ordinal 恢复。
- [ ] reject/respond 的 synthetic tool result 仍发权威 resolution event。
- [ ] 支持 structured resume 与 free-text approval 两条路径。
- [ ] free-text approval 解释失败时默认 reject。
- [ ] edit 只允许 manifest/UI 标记的 editable fields。
- [ ] external execution tool 只产生 pause，不能在 agent 里直接执行。
- [ ] 删除 `KOKORO_REQUIRES_APPROVAL_TOOLS` 作为核心策略；可作为 dev fallback。

### Task 5: Built-in Tools

**Files:**

```text
Create: kokoro-agent/src/kokoro_agent/infrastructure/tools/registry.py
Create: kokoro-agent/src/kokoro_agent/infrastructure/tools/ask_user_question.py
Move: kokoro-agent/src/kokoro_agent/infrastructure/tools/clock.py
      -> kokoro-agent/src/kokoro_agent/infrastructure/tools/current_time.py
Move: kokoro-agent/src/kokoro_agent/infrastructure/tools/fetch.py
      -> kokoro-agent/src/kokoro_agent/infrastructure/tools/web_fetch.py
Modify: kokoro-agent/src/kokoro_agent/domain/tool_names.py
Modify: kokoro-agent/src/kokoro_agent/infrastructure/tools/__init__.py
Modify: kokoro-agent/tests/test_tools.py
```

- [ ] 工具名改为 `current_time` / `web_fetch`。
- [ ] 不保留 `now` / `fetch_url` 兼容。
- [ ] `web_fetch` 受 manifest/networkPolicy 控制。
- [ ] 新增 `ask_user_question`，只走 input_required pause，不在 agent 里直接执行。
- [ ] `ask_user_question` 的 respond result 使用 strict JSON schema。
- [ ] `registry.py` 负责工具名冲突和 allowlist。

### Task 6: Remove Runtime Subagent Default Path

**Files:**

```text
Create: kokoro-agent/src/kokoro_agent/domain/subagent_profile.py
Modify: kokoro-agent/src/kokoro_agent/infrastructure/deepagents/subagent_factory.py
Modify: kokoro-agent/src/kokoro_agent/application/projection/agent_event_mapper.py
Delete: kokoro-agent/src/kokoro_agent/infrastructure/tools/runtime_subagent.py
Delete: kokoro-agent/src/kokoro_agent/infrastructure/subagent/registry.py
Modify: kokoro-agent/tests/test_runtime_subagent_protocol.py
Modify: kokoro-agent/tests/test_subagents.py
```

- [ ] Manifest 中列出的 subagent 才能被编译。
- [ ] 删除默认 `agent_runtime` tool。
- [ ] 动态创建子代理只保留为未来 experimental proposal，不进默认 P0。
- [ ] 旧 runtime subagent 测试删除或改成 deny/proposal 测试。

### Task 7: Backend / Sandbox

**Files:**

```text
Create: kokoro-agent/src/kokoro_agent/infrastructure/sandbox/execution_sandbox.py
Create: kokoro-agent/src/kokoro_agent/infrastructure/sandbox/local_shell.py
Create: kokoro-agent/src/kokoro_agent/infrastructure/sandbox/e2b.py
Create: kokoro-agent/src/kokoro_agent/infrastructure/sandbox/custom.py
Modify: kokoro-agent/src/kokoro_agent/infrastructure/deepagents/backend_factory.py
Modify: kokoro-agent/src/kokoro_agent/infrastructure/config.py
Modify: kokoro-agent/tests/test_config.py
Create: kokoro-agent/tests/test_backend_policy.py
```

- [ ] `storageBackend` 映射 DeepAgents StateBackend/StoreBackend/custom。
- [ ] `executionSandbox=none` 不暴露 execute 能力。
- [ ] `executionSandbox=local_shell` 只允许 dev/test。
- [ ] `executionSandbox=e2b` 缺依赖或密钥 fail loud。
- [ ] S3 只作为 artifact/object storage 配置，不作为 sandbox。
- [ ] DeepAgents 默认 filesystem/execute/task/write_todos 工具按 manifest 显式排除。

### Task 8: Skills / MCP Minimal Manifest

**Files:**

```text
Create: kokoro-agent/src/kokoro_agent/infrastructure/tools/mcp_tool_loader.py
Create: kokoro-agent/src/kokoro_agent/infrastructure/tools/capability_tool.py
Modify: kokoro-agent/src/kokoro_agent/infrastructure/deepagents/skill_loader.py
Modify: kokoro-agent/src/kokoro_agent/application/runtime/compiler.py
Create: kokoro-agent/tests/test_skill_manifest.py
Create: kokoro-agent/tests/test_mcp_manifest.py
```

- [ ] Skills 只从 manifest/lock 加载。
- [ ] MCP 只加载 allowedTools。
- [ ] 所有外部 capability tool 都走 wrapper + approval policy。
- [ ] 大结果返回 summary + ref，不把大对象塞进 AgentEvent。
- [ ] OAuth、表单、高成本确认类工具走 external execution pause。
- [ ] capability wrapper 返回结构化 tool error，不能抛裸异常给模型。

### Task 9: Web AskUserQuestion Render

**Files:**

```text
Modify: kokoro-session contract / normalizer tests for input_required events.
Modify: kokoro-web transport mapper / reducer for ask_user_question pending/settled.
Create or modify: kokoro-web AskUserQuestionCard component.
Create: kokoro-web tests for single_choice, multi_choice, text, cancel, replay.
```

- [ ] Session 把 agent `ask_user_question` awaiting event normalize 为
      input-required 事件。
- [ ] Web 用 AskUserQuestionCard 渲染 pending input。
- [ ] Web submit 走 control/resume respond，不创建新 user message。
- [ ] Replay 后 pending 卡片仍可提交，settled 卡片不可重复提交。
- [ ] 移动端和桌面布局不溢出，不遮挡 assistant 内容。

### Task 10: Verification

**Files:**

```text
Modify: kokoro-agent/README.md
Modify: kokoro-agent/tests/*
```

- [ ] `uv run pytest`
- [ ] `uv run pyright`
- [ ] `uv run ruff check`
- [ ] Redis transport tests 可在无 Redis 环境明确 skip。
- [ ] Mongo integration tests 可在无 Mongo 环境明确 skip。
- [ ] README 更新为新目录、新 env、新运行方式。

## 验收标准

```text
1. agent strict parse session manifest-first run.request。
2. 旧 flat RunRequest 测试明确失败。
3. 代码中不存在 permission_mode / PermissionMode / conversation_id 核心路径。
4. LangGraph thread_id 使用 runId。
5. RuntimeCompiler 是唯一 runtime 编译入口。
6. create_deep_agent 只在 infrastructure/deepagents 调用。
7. 默认路径不包含 runtime_subagent tool。
8. 未授权 DeepAgents 默认工具不会出现在 compiled runtime。
9. current_time/web_fetch 命名统一。
10. ask_user_question 能暂停 run，并通过 respond 把用户回答送回模型。
11. ask_user_question 在 Web 中渲染为交互卡片，不伪装成普通用户消息。
12. local_shell 在 prod fail loud。
13. agent 不读写 session Mongo。
14. 无 seq/eventPosition/cursor 排序字段进入 agent。
15. structured resume 和 free-text approval 都有测试。
16. external execution tool 不会在 agent 进程直接执行。
17. 非法 edit / 未知 action / 判断失败均保守 reject。
18. pyright/ruff/pytest 通过或明确记录外部依赖 skip。
```

## 风险

```text
DeepAgents/LangGraph typed stream 仍有类型缺口：
  允许在 adapter 局部 ignore，不允许扩散到 application。

HITL decisions 顺序对齐容易错：
  approvalBatchId + ordinal 是主键，toolCallId 用作 UI/校验辅助。

工具名改动会影响 session/web tests：
  不做兼容，但必须一次性改净三仓测试。

runtime subagent 删除会减少“模型自由发挥”能力：
  这是有意的。V1 先保证可治理，动态能力作为 proposal/HITL 后续加。

backend/sandbox 容易混：
  storageBackend 解决文件视图和记忆；executionSandbox 解决副作用执行。
```

## 不做项

```text
不新增 kokoro-contracts。
不引入 PostgreSQL。
不把 agent 改成沉重 DDD。
不做完整 skill/MCP hub 后台。
不实现完整 music/studio business orchestration。
不在 Web 或 Session 暴露 agent 内部 DeepAgents 对象。
```
