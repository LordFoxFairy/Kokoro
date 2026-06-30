# Agent 架构

三仓 V1 运行时总方案见：
[Agent / Session / Web V1 运行时技术方案](11-agent-session-web-v1-runtime.md)。

## 定位

`kokoro-agent` 是三仓里的执行 runtime。它接收 `kokoro-session`
发来的 `AgentRunInput`，使用 LangChain/LangGraph 执行模型、skills、
MCP tools、内置工具、子代理、HITL 和 sandbox，产出 raw execution events。

它不是浏览器服务，不拥有聊天消息历史，不直接扣积分。

## 当前实现状态

当前代码已经有 DeepAgents/LangChain worker、HITL interrupt、checkpoint/run_state、
内置 `now` / `fetch_url` 工具和 agent raw wire event。

仍未完整落地：

- `AgentRunInput` manifest 与 Python 入站 `RunRequest` 合流。
- MCP client / skills manifest 的产品化加载。
- backend/sandbox policy 到 DeepAgents backend 的统一配置。
- runtime subagent creation 的审批拦截。

因此本文的 Skills、MCP、sandbox 章节是 V1 目标设计，不代表当前代码已经闭环。

## V1 目标能力范围

V1 agent 必须支持：

- 通用聊天 agent loop。
- LangChain/LangGraph 模型调用、tool calling、streaming、checkpoint。
- Skills：官方、用户、workspace/project 级 skill 的加载和执行。
- MCP client：HTTP MCP server 连接，tool/prompt/resource 发现，按需加载 tool schema。
- 内置工具：时间、网络读取、未来文件/代码工具。
- HITL：工具调用前的 approve/reject/cancel。
- Backend/sandbox：开发可 local_shell，生产使用 state 或显式远程 backend。
- Raw event 输出：message/tool/todo/subagent/thinking/run terminal。

V1 不要求：

- 三仓运行时之外的完整业务产品编排。
- 三仓运行时之外的运营能力。
- Agent 自己决定价格或直接写账本。

## 分层

```text
domain
  RunRequest / AgentRunInput / AgentEvent / SkillRef / McpToolRef / BackendPolicy

application
  admission / run supervisor / invoke / event projection / HITL control

infrastructure
  LangChain/LangGraph adapter
  model runtime
  skill loader
  MCP client
  tool registry
  sandbox runtime
  checkpoint / run state / memory
  Redis transport

interfaces
  worker entry
  inbound Redis command parser
  raw event envelope
```

目录可以按现有仓库逐步整理，但命名不要使用 `ports/` 目录。
应用层需要抽象时用 `application/protocols` 或 `application/interfaces`。

## AgentRunInput

Session 发给 agent 的执行输入必须收敛为 manifest，而不是散字段拼装。

```text
AgentRunInput
  siteId
  workspaceId
  projectId
  sessionId
  runId
  userId
  inputMessageId
  assistantMessageId
  context
    recentMessages
    summary
    artifactRefs
    toolResultRefs
    userProvidedFiles
  modelRuntime
  permissionMode
  backendPolicy
  enabledSkills
  enabledMcpServers
  enabledTools
  traceContext
```

说明：

- `siteId` 必填，agent 所有工具访问都要带它。
- `enabledSkills` 是本次可用 skill 清单，不是 agent 自己跨站查询。
- `enabledMcpServers` 是本次可用 MCP server/tool 清单，不是全局 MCP 列表。
- `context` 是 session 已整理好的上下文包或独立 artifact/content 引用。
- agent 不直接读 session Mongo，也不自己补查全局 skill/MCP 列表。

## Skills

Skill 是 V1 的通用 agent 能力，不是 V2 才有。

### Skill 形态

```text
SkillPackage
  skillId
  siteId
  ownerScope: official | user | workspace | project
  name
  description
  trigger
  body
  allowedTools
  allowedMcpServers
  requiredSandbox
  version
```

Agent 执行时只拿到已授权、已启用、已解析的 skill。Skill 本体存储和
管理不是 agent 直接拥有；agent 负责加载、校验、注入上下文并执行。

### 触发

V1 支持：

- 手动 `/skill` 触发。
- Agent 根据 description 做轻量选择。

V1 不做：

- 三仓运行时之外的运营能力。
- 未授权自动安装第三方 skill。

### 安全

- Skill 不能扩大工具权限，只能收窄或请求用户确认。
- Skill 内引用 MCP/tool 必须在 manifest 的授权范围内。
- Skill 正文进入模型上下文前要限制大小，附属资料按需加载。

## MCP Client

MCP 是 V1 的通用外部工具接入，不是垂直业务功能。

### V1 支持

- HTTP MCP server。
- 列出 tools / prompts / resources。
- 调用 tool。
- tool schema 按需加载，避免一次性塞满上下文。
- OAuth/API key 等凭据由上游管理后以安全引用传给 agent。

### V1 暂不支持

- stdio MCP server，除非未来桌面端承载。
- 完整公开广场商业化。
- Kokoro 反向作为 MCP server。

### MCP 工具命名

```text
mcp__{serverSlug}__{toolName}
```

Agent 内部可以保留 MCP 原始 tool name，但 raw event 和日志要带
server slug，便于权限和审计。

## Tool Registry

Agent 每次运行构建一个 run-scoped tool registry：

```text
Built-in tools
  当前 now / fetch_url；目标可统一命名为 web_fetch / future file/code tools

Skill tools
  skill 暴露的流程型工具或 prompt wrapper

MCP tools
  mcp__server__tool

Runtime subagent tools
  task / delegate / specialist agent
```

规则：

- registry 按 run 创建，不跨 run 泄漏。
- 同名工具必须拒绝或显式 namespace。
- 高风险工具默认走 HITL。
- Code/file/browser 类工具必须绑定 sandbox policy。

## LangChain/LangGraph

Agent 应优先复用 LangChain/LangGraph 能力：

- tool calling
- streaming events
- checkpoint
- memory
- middleware
- HITL interrupt
- subagent / handoff

Kokoro 自己只做三件事：

1. 把产品上下文变成 manifest。
2. 把 LangChain/LangGraph 原生事件翻译成 Kokoro raw event。
3. 把工具、安全、sandbox、MCP、skill 纳入统一治理。

不要重写一个新的 agent framework。

## Sandbox

Sandbox 属于 agent。Kokoro 配置最终要构造成 DeepAgents backend instance，
交给 `create_deep_agent(..., backend=backend_instance)`。

策略：

```text
state        安全默认，适合普通推理和受控工具编排。
local_shell  本地开发和受控测试，不能作为生产隔离。
e2b          远程隔离执行，V1 优先支持。
custom       企业/私有云自研 backend 或 sandbox。
```

所有 sandbox 实现都应满足：

- 创建 workspace。
- 写入输入文件。
- 执行命令或代码。
- 读取结果。
- 控制网络、文件系统、超时、资源。
- 清理 workspace。

本地 shell 不能被当成生产安全边界。S3/object storage 不是执行 sandbox，
只能作为 artifact/object storage 或 custom backend 的存储组成。

## Checkpoint 和 Memory

Agent 的 checkpoint/memory 是执行侧状态：

- LangGraph checkpoint 用于 run resume、HITL、故障恢复。
- memory 用于 agent 长期上下文和压缩记忆。
- 存储建议 Mongo：`kokoro_agent.checkpoints`、`kokoro_agent.memories`。
- tool call 恢复状态属于 LangGraph checkpoint，不单独建第二事实源。

Session 不读取这些 collection。Session 只看 messages/runs/session_events。

## Raw Events

Agent 输出的是 Python wire `AgentEvent`，单源在
`kokoro-agent/src/kokoro_agent/interfaces/envelope.py`。它不是
`contract/events.yaml` 里的 session AGUI/render 事件。

```text
event:
  agent_status
  text_chunk
  reasoning_chunk
  tool_call_start
  tool_call_awaiting
  tool_call_end
  agent_done
  agent_error

envelope:
  request_id
  timestamp
  data
```

规则：

- `request_id` 当前等同 runId，但不是排序字段。
- `agent_done.data.status` 表示 completed / cancelled / timeout。
- `agent_error` 表示失败终态。
- LangChain `BaseMessage.id` 是消息身份，不是顺序。
- tool call id 是工具身份，不是顺序。
- segmentId 用于同一段输出的 delta 归并。
- Session 负责把 AgentEvent 转成 browser-facing SessionEvent。

## 性能

- 高频 token delta 做 20-50ms 或 N 字符 micro-batch。
- MCP tool schema 按需加载。
- 大 MCP/tool 返回截断并写 artifact 或 context ref。
- 长任务转 job/artifact，不把完整二进制或大 JSON 塞进 SSE。

## 风险

- 把 skill/MCP/agent profile 写死到 prompt，后续不可治理。
- 让 agent 直接查 session Mongo，破坏边界。
- 让 agent 直接扣积分。
- 把 LangChain 内部 id 当跨服务顺序。
- 本地 sandbox 误用到生产高风险工具。
