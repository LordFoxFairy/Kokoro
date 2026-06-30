# Agent / Session / Web P0 实施设计

本文只约束 `kokoro-agent`、`kokoro-session`、`kokoro-web` 三仓。目标是把
V1 runtime 从“设计正确但代码未合流”推进到“主链路可信可跑”。

## 设计参考

这些参考只取工程范式，不复制闭源产品内部实现：

- OpenAI Responses streaming 使用 SSE 传输增量输出；这支持我们的
  session -> web 单连接流式消费设计。
  <https://developers.openai.com/api/docs/guides/streaming-responses>
- Gemini function calling 明确区分工具使用模式，如 auto / any / none /
  validated；这说明“是否使用工具”不应混在权限审批里。
  <https://ai.google.dev/gemini-api/docs/function-calling>
- Claude Code settings 有多层 scope 和优先级，permission rules 是 merge
  治理；这适合 Kokoro 的 site / workspace / project / user 策略。
  <https://code.claude.com/docs/en/settings>
- Claude Code subagents 是显式配置、带 scope、tools、permission mode 的
  能力，不是让模型无门槛创建任意 system prompt。
  <https://code.claude.com/docs/en/sub-agents>
- MCP tools 规范要求工具可发现、输入输出有 schema，并强调敏感操作需要
  人类确认、访问控制、限流、输出清洗和审计。
  <https://modelcontextprotocol.io/specification/2025-06-18/server/tools>

## P0 不变量

```text
1. AgentRunInput 是 agent 唯一入站产品上下文。
2. session messages 是聊天展示真源，session_events 是 replay/audit/live。
3. eventId 只做幂等，不排序。
4. Web 先 snapshot hydrate，再 attach active run stream。
5. agent 只消费 manifest，不读取 session Mongo，不自行查全局 skills/MCP。
6. runtime subagent creation 默认必须过 HITL/policy gate。
7. local_shell 不能作为 production sandbox。
8. 不为旧 RunRequest、旧 localStorage 或旧测试保留长期兼容分支。
```

## P0 目标模型

### RunRequest

Redis `kokoro:runs:requests` 的 `run.request` 只保留 manifest-first 形态：

```text
kind: run.request
site_id
run_id
session_id
agent_run_input
```

agent Python 不再接受旧扁平字段：

```text
conversation_id
input
execution_style
permission_mode
```

这些值都必须来自 `agent_run_input`。

### AgentRunInput

P0 目标字段：

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
    backend: state | local_shell | e2b | custom
    resourceLimits?
    networkPolicy?
    artifactStorage?

  capabilities
    skills[]
    mcpServers[]
    tools[]
    subagents[]

  traceContext
    requestId
    idempotencyKey
```

### 删除 `permissionMode`

当前 `permissionMode` 同时承担“工具是否审批”“是否 plan”“UI 档位”三种语义，
已经导致三仓 enum 漂移。P0 要拆掉：

```text
execution.style
  fast | thinking
  只描述模型/agent 执行风格。

execution.toolMode
  auto | none | required
  描述模型能不能用工具、是否必须用工具。

approvalPolicy
  描述哪些工具、MCP、subagent、sandbox 行为需要用户或策略批准。
```

Web 可以继续给用户展示简单预设：

```text
自动        -> toolMode=auto, approvalPolicy=allow low-risk / ask high-risk
每次询问    -> toolMode=auto, approvalPolicy=ask all side-effect tools
不用工具    -> toolMode=none
```

但 agent 不再消费 `permissionMode` 字段。

## ApprovalPolicy

P0 最小结构：

```text
ApprovalPolicy
  defaultAction: allow | ask | deny
  rules:
    - match
      action: allow | ask | deny
      decisions: approve | reject | edit | respond
      reason
```

匹配对象：

```text
tool:fetch_url
tool:shell
mcp:{serverSlug}:{toolName}
skill:{skillId}
subagent:{subagentName}
runtime_subagent:create
sandbox:local_shell
```

规则来源按优先级 merge：

```text
managed policy
site policy
workspace policy
project policy
user preference
request override
```

越高优先级可以收窄权限，不能被低优先级放大。高风险操作默认 `ask` 或
`deny`，不能默认 `allow`。

## Session Snapshot DTO

`GET /sessions/:sessionId` 不应长期直接暴露内部 `events` 全量结构。

P0 DTO：

```text
SessionSnapshot
  session
    siteId
    sessionId
    ownerUserId
    activeRunId
    status
    updatedAt

  messagesPage
    items[]
    nextCursor?

  activeRun?
    runId
    status
    userMessageId
    assistantMessageId
    createdAt
    updatedAt

  recentActivity
    runId?
    items[]

  eventWatermark
    eventId?
```

`recentActivity.items` 是投影，不是原始 `session_events`。诊断场景需要
event log 时，后续另开 admin/diagnostic API。

## Session 投影规则

`SessionStore.appendEvent` 必须是 DB-first，并在同一事务里维护必要投影。

```text
message.delta
  P0 可只写 session_events，不必每个 delta 更新 messages。

message.completed
  写 session_events。
  更新 assistant message content。
  更新 assistant message status=completed。

run.completed
  写 session_events。
  更新 run status。
  清 ChatSession.activeRunId。

run.failed
  写 session_events。
  更新 run status=failed。
  清 ChatSession.activeRunId。
  assistant message status=failed。
```

如果同一 `eventId` 已存在，append 必须幂等返回 `stored=false`，不能重复改投影。

## POST Message 失败语义

`POST /sessions/:id/messages` 的顺序：

```text
1. Mongo transaction 写 user message / assistant placeholder / run / activeRunId。
2. 构建并 strict parse run.request。
3. publish Redis run.request。
4. 返回 202。
```

如果第 3 步失败：

```text
run.status = enqueue_failed
assistant message.status = failed
ChatSession.activeRunId = null
返回 503 或 500，带 requestId
```

不能留下永久 active run。

## HITL Control

`POST /sessions/:sessionId/runs/:runId/control` 必须先查本地 session store：

```text
run 属于 siteId。
run 属于 sessionId。
session 属于 userId 或当前用户有 workspace 权限。
run.status 是 awaiting / running / queued 中可控制状态。
cancel 可以终止 running/awaiting。
resume 只能用于 awaiting。
```

校验通过后，session 再投递 `run.resume` 或 `run.cancel`。

## Runtime Subagent Gate

当前 runtime subagent tool 允许模型传 `name / description / system_prompt / task`
并立即执行。P0 要改成默认 gated：

```text
1. 模型调用 runtime_subagent.create。
2. HITL 展示 name / description / system_prompt / task / requested tools。
3. 用户或 policy approve 后，agent materialize 到 run-scoped registry。
4. reject 时返回 tool resolution，不创建子代理。
```

实现上优先复用 LangChain/DeepAgents 的 HITL interrupt，而不是自研第二套审批流。

P0 不做长期保存 runtime subagent；它只属于当前 run。需要长期保存的 subagent
走后续正式 Skill/Subagent 管理。

## MCP / Skills Manifest

P0 不做广场和后台，只做 run-scoped 能力清单。

```text
SkillRef
  skillId
  version
  name
  description
  bodyRef
  allowedTools[]
  allowedMcpServers[]
  risk

McpServerRef
  serverSlug
  authRef
  allowedTools[]

ToolRef
  name
  source: builtin | skill | mcp | runtime
  inputSchema
  outputSchema?
  risk
  approvalRuleRef?
```

agent 只看 manifest 内的能力。manifest 没列出的 skill、MCP server、tool，
本轮不可见。

MCP tool 结果：

```text
小结果 -> tool.returned.result 摘要
结构化结果 -> structuredContent 校验后转摘要 + ref
大结果/二进制 -> artifactRef，不进 SSE 全量 body
错误 -> is_error=true，并保留 provider error kind
```

## BackendPolicy

```text
state
  默认安全 backend，适合普通推理和受控工具。

local_shell
  只允许 development/test/单租户受控环境。
  production 发现 local_shell 必须 fail loud。

e2b
  远程隔离执行，缺依赖或密钥 fail loud。

custom
  企业自定义 backend，必须声明 capability 和 isolation level。
```

S3/object storage 不是 sandbox，只能作为 artifact storage。

## Web Hydrate

Web P0 启动顺序：

```text
1. GET /sessions/:sessionId
2. SnapshotHydrator -> SessionStreamState
3. 如果 activeRun 存在，打开 /stream
4. reducer 用 eventId 去重
5. terminal event 后关闭 live handle
```

Web 不能：

```text
保存 lastResumeId 作为产品状态。
按 eventId 排序。
把 localStorage 视为权威消息历史。
在生产后端失败时静默落到 simulator。
```

## 实施顺序

### P0-A 契约合流

```text
1. 在 agent 定义 AgentRunInput Pydantic 模型。
2. 修改 agent RunRequest 为 manifest-first。
3. 删除旧 flat RunRequest 字段和旧测试。
4. session/web/agent 增加真实 run.request 端到端 smoke。
```

### P0-B Session 事实源

```text
1. appendEvent(message.completed) 写 assistant message content。
2. appendEvent(run terminal) 写 run status、清 activeRunId。
3. startRun publish 失败标 enqueue_failed 并清 activeRunId。
4. control endpoint 补 site/session/user/run ownership 校验。
```

### P0-C Web Snapshot

```text
1. 定义 SessionSnapshot DTO。
2. 实现 SnapshotHydrator。
3. reattach 改为 snapshot-first。
4. simulator 只允许 dev/preview，production fail visible。
```

### P0-D Agent Policy

```text
1. 删除 permissionMode，改 execution.toolMode + approvalPolicy。
2. Runtime subagent creation 接入 HITL gate。
3. backendPolicy 接入 DeepAgents backend。
4. skills/MCP/tool manifest 形成 run-scoped registry。
```

## 验收门槛

```text
契约：
  session 生成的 run.request 能被 agent strict parse。
  agent 不再接受旧 flat RunRequest。

消息：
  message.completed 后 GET snapshot 能看到 assistant 完整内容。

恢复：
  刷新后先 snapshot hydrate，再 attach active run。
  Redis live 被裁剪后，历史仍能从 Mongo replay。

失败：
  Redis publish run.request 失败不会卡 activeRunId。
  malformed agent event 不污染 Mongo，不杀 relay。

HITL：
  control 必须校验 run/session/site/user 归属。
  runtime subagent create 默认会被 ask/deny，不会直接执行。

权限：
  toolMode 与 approvalPolicy 分离。
  production local_shell fail loud。

边界：
  Web 不直连 agent/Redis/Mongo/MCP。
  Agent 不读 session Mongo。
  Session 不执行 tools。
```
