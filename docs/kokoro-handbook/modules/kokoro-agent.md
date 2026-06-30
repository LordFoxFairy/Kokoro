# kokoro-agent 技术方案

本文只约束 `kokoro-agent` 子仓。三仓总链路见
[Agent / Session / Web V1 运行时技术方案](../technical/11-agent-session-web-v1-runtime.md)。

## 定位

`kokoro-agent` 是执行层 worker。它消费 `kokoro-session` 投递的 run 请求，
基于 DeepAgents / LangChain / LangGraph 执行模型、工具、子代理和 HITL，
然后把 agent 原始 wire events 写回 Redis。

它不是浏览器 API，不拥有聊天消息事实源，不决定积分扣费，不直接写
`kokoro-session` 的 Mongo collections。

## 当前实现状态

已实现：

```text
Redis 请求流消费：kokoro:runs:requests。
入站消息：run.request / run.resume / run.cancel。
DeepAgents create_deep_agent 构造入口。
LangChain HumanInTheLoopMiddleware interrupt_on 配置。
内置工具 now / fetch_url。
运行时子代理 prototype 与 task 工具。
AgentEvent 严格 wire envelope：event / request_id / timestamp / data。
原始事件输出到 kokoro:run:{runId}:events。
checkpoint 后端：memory / sqlite / mongo。
run_state 后端：memory / sqlite / mongo。
Langfuse opt-in 观测。
```

尚未完整实现，不能写成已完成：

```text
AgentRunInput manifest 与 agent 入站 RunRequest 完全合流。
MCP/skills manifest 到 DeepAgents adapters/skills 的产品化加载。
Backend/storage 与 execution sandbox 分离配置。
runtime subagent creation 收敛到 manifest-first gate。
生产级 sessionId 分布式串行锁。
```

## 业务职责

### Owns

```text
run.request / run.resume / run.cancel 的执行侧消费。
DeepAgents / LangGraph agent loop。
模型调用和 streaming event 投影。
工具注册、工具审批、工具结果投影。
子代理执行和子代理事件投影。
HITL interrupt resume/cancel。
Agent checkpoint 与 run_state。
agent 原始 wire event 契约。
```

### Does Not Own

```text
聊天窗口、聊天消息、session events、SSE replay。
浏览器可见 AGUI/render 契约。
Web reducer / UI 状态。
SiteContext 最终解析。
积分、支付、价格、账务。
MCP/skill 官方广场和后台管理。
```

## 上游和下游

```text
上游：
  kokoro-session 通过 Redis 请求流投递 run.request / run.resume / run.cancel。

下游：
  Redis kokoro:run:{runId}:events，供 kokoro-session relay 消费。
  Model provider。
  DeepAgents / LangChain / LangGraph。
  checkpoint / run_state 存储。
  将来接入的 MCP server / sandbox provider / artifact storage。
```

Agent 不调用 `kokoro-web`，不读取 `kokoro-session` Mongo，不直接调用 credit/payment。

## 核心对象

### 当前代码对象

```text
RunRequest
  当前 Python 入站模型：kind, run_id, session_id, conversation_id, input,
  execution_style, permission_mode。

InboundMessage
  run.request / run.resume / run.cancel 判别联合。

AgentEvent
  原始 wire envelope：event, request_id, timestamp, data。

RunSupervisor
  消费请求流、run 去重、resume/cancel、终态认领。

RunStateStore
  run_id 去重、原 request 持久化、terminal 状态认领。

CheckpointSaver
  LangGraph checkpoint，支撑 HITL resume。
```

### V1 目标对象

```text
AgentRunInput
  session 下发的完整 manifest：site/workspace/project/session/run/user、
  recentMessages、modelRuntime、execution、approvalPolicy、backendPolicy、
  capabilities、locks。

RunCapabilityCompiler
  把 capabilities 编译成 DeepAgents tools/subagents/skills、interrupt_on、
  permissions、backend、memory。

BackendPolicy
  storageBackend 与 executionSandbox 的组合策略。

Skill/Mcp Manifest
  本次 run 可用能力和 lock 的最小清单，不把全局目录塞进 prompt。
```

## 数据模型

Agent 自己只拥有执行恢复所需状态。

```text
LangGraph checkpoint
  memory：测试或单进程临时。
  sqlite：本地开发/单 worker 可用，便于独立测试。
  mongo：多 pod / production 建议。

DeepAgents memory / skill files
  通过 backend/store namespace 暴露给 DeepAgents。
  不是 session messages，不直接给 Web 展示。

Kokoro RunStateStore
  memory：测试或单进程临时。
  sqlite：本地开发/单 worker 可用。
  mongo：多 pod / production 建议，_id=run_id 做原子认领。
```

不允许：

```text
agent 写 kokoro_session.messages。
agent 写 kokoro_session.session_events。
agent 写 credit ledger。
agent 把 checkpoint 当聊天历史事实源。
```

## API / RPC / Events

### 当前入站

当前 agent 代码接受的 `run.request` 是扁平结构：

```text
kind: run.request
run_id
session_id
conversation_id
input
execution_style
permission_mode
```

当前 `kokoro-session` 已经开始投递 `agent_run_input` manifest：

```text
kind: run.request
site_id
run_id
session_id
agent_run_input
```

这是 P0 契约差距。下一步必须让 agent Python 入站模型接受 manifest，
不能继续让 session 和 agent 各自维护一套 run.request。

### 当前出站

Agent wire event 单源是 `kokoro-agent/src/kokoro_agent/interfaces/envelope.py`。

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

`request_id` 当前等同 run id。它不是排序字段。Agent 不发 `seq`。

## Admin 管理

Agent 子仓本身不提供后台。后台能力应由上游产品模块维护，并在 run 前解析成 manifest：

```text
模型策略。
skill 启用状态。
MCP server 授权状态。
工具风险策略。
backend/sandbox 策略。
memory/checkpoint 保留策略。
```

Agent 只能消费这些策略，不跨站查询或自行放大权限。

## 业务链路

```text
1. session 投递 run.request。
2. agent worker parse inbound。
3. RunSupervisor 用 run_state try_register 抢占 run。
4. RunCapabilityCompiler 基于 manifest 构造 DeepAgents runtime。
5. LangGraph checkpoint 记录运行态。
6. 模型、工具、子代理、HITL 产生投影。
7. AgentEvent 写入 kokoro:run:{runId}:events。
8. session relay 归一化、持久化、SSE 推给 web。
```

HITL：

```text
1. HumanInTheLoopMiddleware 产生 interrupt/action_requests。
2. agent 输出 tool_call_awaiting，带 approvalBatchId、ordinal、actionName、
   args preview、allowedDecisions。
3. web 通过 session control 提交结构化 run.resume。
4. agent 按原始 action_requests 顺序恢复 decisions。
5. agent 从 checkpoint 恢复同一 thread。
6. reject/respond 的工具结果由 agent 合成 tool resolution event。
```

## 部署

```text
服务名        kokoro-agent-worker
运行时        Python + uv
入口          kokoro-agent-worker
Redis         KOKORO_STREAM_BACKEND=redis
              KOKORO_REDIS_URL
模型          KOKORO_MODEL
              KOKORO_LOCAL_FAKE_MODEL=1
checkpoint    KOKORO_CHECKPOINT_BACKEND=memory|sqlite|mongo
run_state     KOKORO_RUN_STATE_BACKEND=memory|sqlite|mongo
Mongo         KOKORO_MONGO_URL
              KOKORO_MONGO_DB
HITL          KOKORO_REQUIRES_APPROVAL_TOOLS
观测          LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY
```

Production 建议：

```text
stream=redis。
checkpoint=mongo。
run_state=mongo。
local_fake_model 关闭。
高风险工具默认需要 HITL 或 sandbox。
```

SQLite 可以保留在 agent 子仓用于本地开发和独立测试，但不能作为多 pod
production 方案。

## Backend / Sandbox 设计

当前代码尚未把 backend/sandbox 建成完整能力。V1 设计原则：

```text
优先使用 DeepAgents 官方 backend，不自研一套 agent framework。
storageBackend 负责 state/store/memory/skills/file view。
executionSandbox 负责 shell/code/browser 等副作用执行。
local_shell 只允许 development/test/受控单租户。
e2b/custom 是显式配置能力，缺依赖或密钥必须 fail loud。
S3 不是 sandbox，只能作为 artifact/object storage 或 backend 存储组成。
```

运行时配置最终应收敛成一个 `backendPolicy`：

```text
storageBackend: state | store | custom
executionSandbox: none | local_shell | e2b | custom
options: provider-specific settings
networkPolicy
resourceLimits
artifactStorage
```

## 测试

必须覆盖：

```text
入站 run.request manifest 解析。
run_state 去重与 terminal 认领。
checkpoint resume。
HITL approve / reject / edit / respond / cancel。
malformed inbound 不杀 worker。
agent event strict extra=forbid。
tool/subagent event 投影。
Redis transport。
Mongo checkpoint/run_state 集成。
```

## 风险和边界

必须明确禁止：

```text
用 BaseMessage.id 做跨服务排序。
重新引入 seq。
agent 直接写 session Mongo。
agent 直接扣积分。
runtime subagent 默认直接创建并执行。
MCP/skill 全局列表无过滤塞进 prompt。
local_shell 作为默认生产 sandbox。
__init__.py 放业务逻辑。
```

## 后续任务

### P0

```text
让 Python RunRequest 接受 session 的 agent_run_input manifest。
把 conversation_id/input 从旧扁平 wire 迁移到 manifest。
删除 permissionMode，改用 execution.toolMode + approvalPolicy。
移除 memory_store.py 作为 runtime 选项，只保留测试 fixture 或明确标注 test-only。
运行时子代理改成 manifest-first gate，不再默认现场创建。
backendPolicy 拆成 storageBackend + executionSandbox。
MCP manifest 通过 LangChain adapters 加载过滤后的 tools。
skills manifest + lock 编译到 DeepAgents skills/backend 文件视图。
```

### P1

```text
E2B/custom backend smoke test。
MCP tool schema 按需加载。
tool policy 与 HITL 策略统一到 interrupt_on / permissions / wrapped tools。
run/session 分布式 lease 细化。
CapabilityRef / CapabilityInvocation / CapabilityResult。
RunCapabilityCompiler 支持 capability tool wrapper。
general.music.generate adapter smoke。
```

### P2

```text
专业 agent profile。
agent handoff 可视化事件。
memory retention/admin policy。
Music specialist agent profile。
Studio capability orchestration。
```
