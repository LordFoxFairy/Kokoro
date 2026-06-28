# kokoro-agent 技术方案

## 定位

`kokoro-agent` 是 Kokoro 三仓运行时的执行层。它负责按 `AgentExecutionManifest` 执行 LangChain/LangGraph agent loop，调用模型、skills、MCP tools、内置工具、子代理和 sandbox，并产出 raw execution events 给 `kokoro-session`。

它不是浏览器 API，不拥有 session messages，不直接扣积分。

## 业务职责

### Owns

```text
AgentExecutionManifest 的运行时解释。
LangChain/LangGraph agent loop。
Model runtime 调用。
Skills 加载、注入和执行。
MCP client tool 调用。
Tool registry 和 tool namespace。
Subagent / handoff 执行。
HITL 工具审批等待和恢复。
Sandbox runtime: local / e2b / custom。
Agent checkpoint / memory / run state。
Raw execution events。
```

### Does not own

```text
浏览器 session event 契约。
Session messages / session events / run snapshot。
Web UI 状态。
SiteContext 最终授权。
三仓运行时之外的业务账务、支付、价格、运营和审核。
```

## 上游和下游

```text
上游：
  kokoro-session 通过 Redis run request 发送 AgentExecutionManifest。

下游：
  Redis raw event stream，发送给 kokoro-session。
  LangChain/LangGraph。
  Model provider。
  MCP server。
  Sandbox provider。
  Mongo agent checkpoint/memory。
```

Agent 不直接调用 `kokoro-web`，不直接写 `kokoro-session` 的 Mongo collections。

## 核心对象

```text
AgentExecutionManifest
  一次执行的完整清单。

SkillPackage / SkillRef
  本次 run 可用 skill。

McpServerRef / McpToolRef
  本次 run 可用 MCP server/tool。

ToolDefinition
  内置工具、skill 工具、MCP 工具、subagent 工具的统一运行时描述。

SandboxPolicy
  local/e2b/custom、网络、文件、超时、资源限制。

AgentRunState
  claim、running、awaiting_approval、completed、failed、cancelled。

RawExecutionEvent
  agent 输出给 session 的事件。
```

## 数据模型

Mongo（agent 自己拥有）：

```text
kokoro_agent.checkpoints
  siteId, sessionId, runId, threadId, checkpointId, state, createdAt。

kokoro_agent.memories
  siteId, scope, subjectId, memoryType, content, metadata, createdAt。

kokoro_agent.tool_state
  siteId, runId, toolCallId, status, input, outputRef, error, createdAt。
```

Redis：

```text
kokoro:runs:requests
kokoro:run:{runId}:events
kokoro:run:{runId}:control
kokoro:agent:run:{runId}:lease
kokoro:agent:session:{sessionId}:lease
```

Agent 不写 MySQL 账务表，不写 session messages。

## API / RPC / Events

Agent 没有面向浏览器的 HTTP API。V1 接口是 Redis stream。

入站 run request：

```text
event: run.request
payload: AgentExecutionManifest
idempotency: runId
```

入站 control：

```text
decision: approve | reject | cancel | respond
target: runId + optional toolCallId
```

出站 raw events：

```text
run.started
message.delta
message.completed
thinking.delta
tool.invoked
tool.awaiting_approval
tool.returned
todo.updated
subagent.started
subagent.finished
run.completed
run.failed
```

幂等：

- `runId` claim 防重复执行。
- `toolCallId` 防重复工具恢复。
- raw event 可带 `eventId`，session 仍需做幂等落库。

## 运行时管理

Agent 自身不提供三仓之外的管理能力。它只消费上游解析后的运行时配置：

```text
model runtime policy
skill enablement
MCP server enablement
tool risk policy
sandbox policy
HITL policy
agent memory retention policy
```

这些配置由上游解析后进入 `AgentExecutionManifest`，agent 不跨站查询全局配置。

## 业务链路

`kokoro-agent` 只参与三仓运行链路：

```text
kokoro-session 发送 AgentExecutionManifest。
kokoro-agent claim runId 并执行 LangChain/LangGraph。
kokoro-agent 按 manifest 加载 model、skills、MCP、tools、sandbox 和 permission policy。
kokoro-agent 输出 raw execution events 给 kokoro-session。
kokoro-session 负责归一化、持久化和推送给 web。
```

Agent 不拥有通用产品业务链路文档；涉及平台、账务、市场、后台的链路不在本文维护。

## 部署

```text
服务名        kokoro-agent-worker
运行时        Python + uv
入口          kokoro-agent-worker
环境变量      KOKORO_REDIS_URL
              KOKORO_STREAM_BACKEND
              KOKORO_MODEL
              OPENAI_API_KEY / ANTHROPIC_API_KEY / provider keys
              KOKORO_AGENT_STATE_BACKEND=mongo
              KOKORO_AGENT_MONGO_URL
              KOKORO_SANDBOX_BACKEND=local|e2b|custom
              E2B_API_KEY
多 Pod        runId lease + session lease，防重复执行。
```

本地默认可用 fake model + local sandbox。生产高风险工具必须显式配置 sandbox。

## 测试

```text
单测：
  manifest 解析、tool registry、skill loader、MCP tool wrapper、sandbox policy、event adapter。

集成：
  Redis run request -> raw events。
  HITL approve/reject/cancel。
  Mongo checkpoint/memory。
  local/e2b sandbox smoke。

反例：
  未授权 skill/MCP tool 不可用。
  同 run 重复投递只执行一次。
  MCP 大返回截断。
  sandbox timeout。
  LangChain malformed event 不崩 worker。
```

## 风险和边界

```text
禁止 agent 直接写 session messages。
禁止 agent 直接扣积分。
禁止把 MCP/skill 全局列表塞进每次 prompt。
禁止把本地 sandbox 当生产隔离。
禁止使用 LangChain BaseMessage.id 当跨服务排序。
禁止跨 run 复用 mutable tool registry。
```

## 后续任务

```text
P0  AgentExecutionManifest 类型定稿。
    Skill loader 最小实现。
    HTTP MCP client 最小实现。
    SandboxRuntime local/e2b/custom 接口和 local 实现。
    runId/sessionId lease。

P1  MCP tool schema 按需加载。
    Skill 自动触发。
    Mongo checkpoint/memory 持久化。
    E2B 集成测试。

P2  专业 agent profile 接入同一 manifest 机制。
    多 agent handoff 可视化事件。
    memory retention/admin policy。
```
