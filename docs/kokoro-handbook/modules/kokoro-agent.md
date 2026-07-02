# kokoro-agent 技术方案

三仓 V1 运行时总方案见：
[Agent / Session / Web V1 标准运行时方案](../technical/11-agent-session-web-v1-runtime.md)。
HIL 和工具执行前后拦截专项方案见：
[Agent HIL 与工具拦截标准方案](../technical/12-agent-hitl-tool-interception.md)。

本文件是 `kokoro-agent` 专项方案。它只定义 Agent 仓自己的边界、目录、
模型和运行链路，不替代 `kokoro-session` / `kokoro-web` 文档。

## 定位

`kokoro-agent` 是 Agent 执行服务。

它接收 `kokoro-session` 投递的 `RunRequest`，基于 DeepAgents、
LangChain 和 LangGraph 构造可运行 agent，执行模型、工具、Skills、MCP、
Subagents、HITL 和 sandbox/backend，输出 raw agent events 给
`kokoro-session`。

它不是业务域服务，不是浏览器 API，不拥有聊天消息，不直接扣积分，不拥有
Skill Hub / MCP Hub 的安装、审核和启用状态。

## 设计推理

### 第一步：从完整 Agent 链路开始

`kokoro-agent` 不是传统业务域服务，它更像一个受控 Agent worker。
目录必须贴着执行链路走，而不是先套 `domain/application/infrastructure`
模板。

完整链路：

```text
1. session 投递 run.request。
2. worker 领取 run，并用 runId lease 防重复执行。
3. 解析 RunRequest。
4. 校验本次 run 的 capabilities 和 permissions。
5. 准备 model、tools、skills、MCP、subagents、sandbox、memory。
6. 基于 DeepAgents 构建可运行 agent。
7. 执行 agent，或根据 run.resume 恢复 agent。
8. DeepAgents/LangChain/LangGraph 负责原生 stream、interrupt、checkpoint。
9. Agent 只发布 Kokoro 关心的 RawAgentEvent。
10. 遇到敏感工具时，输出 awaiting approval 并等待 session resume。
11. run completed / failed / cancelled 后明确通知 session。
```

这个链路决定目录，而不是目录决定链路。

### 第二步：明确 DeepAgents 已经负责什么

既然 `kokoro-agent` 深度依赖 DeepAgents，就不能伪装成可替换 adapter，
也不能再自造一套小 LangChain。

DeepAgents/LangChain/LangGraph 负责：

```text
可运行 agent。
模型调用。
tool calling。
subagents / task。
skills。
MCP tools。
interrupt / HITL。
Command(resume=...)。
thread_id / checkpoint。
stream events。
backend / sandbox。
memory/store。
```

Kokoro 不应重复实现：

```text
read_events.py / map_events.py 这种自造事件系统。
RuntimeSubagentRegistry 这种自造子代理注册中心。
_LangChainActionRequest 这种框架泄漏类型名。
自维护 tool approval state machine。
自维护 checkpoint 协议。
自维护 MCP 工具协议。
```

### 第三步：明确 Kokoro-agent 自己负责什么

Kokoro-agent 的价值是把产品请求变成一次可控执行：

```text
RunRequest
  -> Capabilities
  -> Permissions
  -> DeepAgents graph
  -> Execute / Resume
  -> RawAgentEvent
  -> Session 持久化和重放
```

因此 Agent 自己拥有：

```text
RunRequest 解析。
Capabilities 校验。
Permissions 策略落地。
DeepAgents 创建参数准备。
工具、skills、MCP、subagents、sandbox 的本次 run 装配。
run lease。
agent checkpoint / memory。
RawAgentEvent 输出边界。
```

不拥有：

```text
聊天消息事实源。
浏览器 event cursor。
Skill/MCP Hub 安装、审核、市场、启用状态。
价格、账务、扣积分。
session messages / session events / run snapshot。
```

### 第四步：为什么不用 DDD 四层目录

Agent 服务不像订单、支付、库存，不适合重 DDD。

硬套 DDD 会导致：

```text
domain 变成纯类型桶。
application 变成脚本壳。
infrastructure 变成巨大垃圾桶。
为了分层写 ports/protocols。
读代码的人找不到“run 是怎么执行的”。
```

所以采用执行链路架构。

保留的 DDD 思想只有三点：

```text
边界清晰：agent 不写 session messages，不扣积分，不拥有 Hub。
语言清晰：RunRequest、Capabilities、Permissions、RawAgentEvent。
依赖清晰：worker 调 execution，execution 使用各能力模块。
```

不保留：

```text
domain/application/infrastructure/interfaces 四层模板。
repository/service/entity/aggregate 命名。
ports 目录。
为了抽象而抽象的 protocol 层。
```

## 业务职责

### Owns

```text
RunRequest 解析。
Capabilities / RunContext 的 agent 侧模型。
DeepAgents graph 构造。
模型调用。
工具注册和工具权限映射。
Skills mount 加载。
MCP client tool wrapper。
Subagents 配置映射。
HITL interrupt_on 和 Command(resume=...)。
Backend/sandbox 选择和安全策略执行。
LangGraph checkpointer / store。
RawAgentEvent 生成。
run lease 和 worker 执行保护。
Agent 侧 checkpoint / memory。
```

### Does not own

```text
浏览器 session event 契约。
聊天窗口 messages。
session events / run snapshot。
Skill Hub / MCP Hub 安装、审核、市场、启用状态。
SiteContext 最终业务授权。
Web UI 状态。
账务、支付、价格、套餐和积分。
模型最终价格决策。
```

## 上游和下游

```text
上游：
  kokoro-session
    发送 run.request / run.resume / run.cancel。
    提供本次 run 已授权的 runtime 能力。

下游：
  Redis
    run request/control/event stream。

  Mongo
    agent checkpoint / memory / long-running state。

  DeepAgents / LangChain / LangGraph
    agent 执行、interrupt、stream、checkpoint/store 接口。

  Model provider
    OpenAI / Anthropic / local fake / other provider。

  MCP server
    HTTP / streamable HTTP / 受限 stdio。

  Sandbox provider
    state / local_shell / e2b / custom。
```

Agent 不直接调用 `kokoro-web`，不直接读写 `kokoro-session` 的 message
collections。

## 目录架构

目标目录按执行链路组织：

```text
kokoro_agent/
  worker/
    main.py
    messages.py

  run/
    request.py
    context.py
    capabilities.py
    lifecycle.py
    events.py
    json_payload.py

  execution/
    build_agent.py
    protocols.py
    run_agent.py
    resume_agent.py
    approvals.py
    events.py
    publish_agent_events.py
    prompts/
      __init__.py
      system.md

  tools/
    registry.py
    permissions.py
    ask_user.py
    names.py

  subagents/
    __init__.py
    catalog.py
    definitions.py
    types.py

  skills/
    mounts.py

  mcp/
    servers.py
    tools.py

  sandbox/
    backend.py
    policy.py

  storage/
    __init__.py
    checkpoints.py
    memory.py
    leases.py
    run_state.py
    mongo_lease_store.py
    sqlite_lease_store.py

  streams/
    __init__.py
    factory.py
    protocol.py
    json_types.py
    redis.py
    memory.py

  model/
    __init__.py
    factory.py
    local_fake.py
    settings.py

  config.py
  observability.py
```

## 目录与文件职责说明

每个目录和 `.py` 文件都必须回答三句话：

```text
为什么存在？
为什么放在这里？
禁止放什么？
```

回答不上来，不创建文件。

### `worker/`

`worker/` 是进程入口层，只负责接消息和调度执行链路。

```text
worker/main.py
  存在理由：
    启动 worker 进程，加载配置，创建 Redis/Mongo/model 等依赖，
    订阅 run/control 消息，然后调用 execution。

  放置理由：
    这是进程入口，不是 Agent 执行逻辑。

  禁止：
    不写 graph 执行逻辑。
    不解析 DeepAgents stream。
    不注册工具。
    不写业务状态机。

worker/messages.py
  存在理由：
    解析和校验 Redis wire messages，如 run.request、run.resume、run.cancel。

  放置理由：
    这些是 worker 入站消息格式，不是 run 领域模型本身。

  禁止：
    不创建 agent。
    不连接 MCP。
    不做权限判断。
    不发布 raw events。
```

### `run/`

`run/` 描述一次 Agent 执行本身，不依赖 DeepAgents。

```text
run/request.py
  存在理由：
    定义 RunRequest，描述 session 发来的单次执行请求。

  放置理由：
    RunRequest 是整个执行链路的输入，必须独立于 worker 和 DeepAgents。

  禁止：
    不读取环境变量。
    不创建模型。
    不 import DeepAgents。

run/context.py
  存在理由：
    定义 RunContext，描述 site/user/workspace/project/session/namespace 等上下文。

  放置理由：
    context 是本次 run 的背景信息，不是权限实现，也不是数据库查询。

  禁止：
    不查数据库。
    不做 Hub 查询。
    不决定用户能用什么。

run/capabilities.py
  存在理由：
    定义本次 run 被授权的能力：model、tools、skills、MCP、subagents、sandbox、memory。

  放置理由：
    capabilities 是 Agent 执行的核心输入边界。

  禁止：
    不安装 skill。
    不连接 MCP。
    不创建工具实例。
    不扩大授权范围。

run/lifecycle.py
  存在理由：
    定义 run 状态、终态和可恢复规则。

  放置理由：
    lifecycle 是 run 自己的状态语言。

  禁止：
    不写 Redis。
    不抢 worker lease。
    不发布 event。

run/events.py
  存在理由：
    定义 Agent 输出给 Session 的 RawAgentEvent 信封和 payload 类型。

  放置理由：
    RawAgentEvent 是 run 的对外事实，不属于 DeepAgents 原生事件。

  禁止：
    不生成 browser cursor。
    不持久化 session event。
    不依赖 Redis/Mongo。

run/json_payload.py
  存在理由：
    定义 JSON-safe payload 类型别名。

  放置理由：
    多个边界都需要 JSON payload 类型，放在 run 下避免散落。

  禁止：
    不做序列化副作用。
    不放业务状态。
```

### `execution/`

`execution/` 是 Agent 执行编排层。它基于 DeepAgents 实现 Kokoro 的执行链路，
但目录不叫 `deepagents`，因为 DeepAgents 是底座，不是架构语言。

```text
execution/build_agent.py
  存在理由：
    把 RunRequest、RunContext、Capabilities 和配置转换为可运行 agent。
    内部调用 DeepAgents 原生 create_deep_agent，并校验返回对象满足本仓执行协议。

  放置理由：
    维护者要找的是“如何构建 agent”，不是 graph、adapter 或框架名。

  禁止：
    不消费 Redis。
    不发布事件。
    不查询 Hub。
    不做价格或账务判断。
    不变成 kokoro_agent/deepagents 目录。
    不隐藏或重写 DeepAgents 行为。
    不做 session 持久化。

execution/protocols.py
  存在理由：
    描述本仓对 DeepAgents/LangGraph stream 对象的最小协议。

  放置理由：
    这是 execution 使用的窄接口，不是全仓 ports 层。

  禁止：
    不创建 ports 目录。
    不复制 LangGraph 完整类型系统。
    不放具体 Redis/Mongo 实现。

execution/run_agent.py
  存在理由：
    启动一次 agent 执行，并处理 completed / failed / cancelled。

  放置理由：
    这是一次新 run 的主流程。

  禁止：
    不注册全局 mutable tool registry。
    不实现工具本身。
    不把 LangChain event system 重写一遍。

execution/resume_agent.py
  存在理由：
    把 session 发来的 resume 决策转换为 DeepAgents/LangGraph Command(resume=...)。

  放置理由：
    resume 是执行链路的一种入口，和新 run 分开更清楚。

  禁止：
    不自己实现审批状态机。
    不伪造工具执行结果。

execution/approvals.py
  存在理由：
    处理 ApprovalRequest / ApprovalDecision 与 interrupt_on / Command(resume=...) 的边界转换。

  放置理由：
    审批是 execution 的暂停和恢复边界。

  禁止：
    不把 reject 当正常 tool result。
    不让 respond 用于危险工具。
    不跳过 edit 后的参数校验。

execution/events.py
  存在理由：
    构造 Kokoro RawAgentEvent。

  放置理由：
    这是 DeepAgents 原生 stream 和 Kokoro raw event 之间的输出语言。

  禁止：
    不重写 LangChain/DeepAgents event system。
    不生成 browser cursor。
    不负责 session replay。

execution/publish_agent_events.py
  存在理由：
    从 DeepAgents typed stream 中取出 Kokoro 关心的事件并发布到 stream。

  放置理由：
    这里是执行过程的输出发布边界，不是独立 event framework。

  禁止：
    不命名为 read_events.py 或 map_events.py。
    不维护跨服务顺序字段。
    不做 Mongo 持久化。

execution/prompts/
  存在理由：
    存放默认系统提示词和执行底座提示模板。

  放置理由：
    prompts 属于构建 agent 的输入。

  禁止：
    不放用户动态数据。
    不放 site/workspace 私有配置。

execution/prompts/__init__.py
  存在理由：
    读取随包分发的系统提示词资源。

  放置理由：
    提示词资源属于构建 agent 的输入。

  禁止：
    不读用户配置。
    不拼接动态上下文。

execution/prompts/system.md
  存在理由：
    默认系统提示词正文。

  放置理由：
    文本资源与 prompt loader 同目录维护。

  禁止：
    不放 secret。
    不放 site/user/workspace 私有内容。
```

### `tools/`

`tools/` 只放 Kokoro 自己明确拥有的工具和工具集合装配。

```text
tools/registry.py
  存在理由：
    根据 capabilities 组装本次 run 的工具集合，交给 DeepAgents。

  放置理由：
    工具集合是执行能力的一部分，但不是 run 请求类型。

  禁止：
    不维护跨 run 全局 mutable registry。
    不绕过 permissions。
    不自动暴露所有 MCP/skills 工具。

tools/permissions.py
  存在理由：
    将 allow / ask / deny 策略转换为工具可用性和 interrupt_on 配置。

  放置理由：
    这是工具调用前的治理，不是 UI 审批页面。

  禁止：
    不直接弹 UI。
    不写 session 状态。
    不让 sandbox 覆盖 deny。

tools/ask_user.py
  存在理由：
    模型向用户请求补充信息的标准工具。

  放置理由：
    这是 Kokoro 明确拥有的默认工具。

  禁止：
    不用于危险工具拒绝。
    不替代普通聊天消息。
    不直接调用 web。

tools/names.py
  存在理由：
    集中声明 DeepAgents/Kokoro 共享的保留工具名。

  放置理由：
    工具名属于 tools 能力边界，不属于 run request。

  禁止：
    不注册工具实例。
    不决定权限。
    不放 provider 名。
```

### `subagents/`

`subagents/` 描述可被本次 run 使用的子代理定义。

```text
subagents/__init__.py
  存在理由：
    导出稳定的 subagent catalog/definition API。

  放置理由：
    只作为包入口，便于 execution/build_agent.py 使用。

  禁止：
    不注册全局 mutable 状态。
    不读取环境变量以外的外部系统。

subagents/catalog.py
  存在理由：
    管理内建和配置声明的子代理 catalog。

  放置理由：
    catalog 是本次 run 可用子代理定义的来源。

  禁止：
    不让模型静默写入。
    不查询 Hub。

subagents/definitions.py
  存在理由：
    把 capabilities 中的 subagent 配置转换为 DeepAgents subagents 参数。

  放置理由：
    子代理是 Agent 能力，不是 worker 消息，也不是全局 Hub。

  禁止：
    不让模型静默创建同权限子代理。
    不默认继承主 Agent 全部 tools/skills/MCP/sandbox。
    不维护 RuntimeSubagentRegistry。

subagents/types.py
  存在理由：
    定义 RegisteredSubagent 和 SubagentSource。

  放置理由：
    这是子代理 catalog 和事件归属共用的稳定类型。

  禁止：
    不引用 DeepAgents 具体实现。
    不放运行时 registry。
```

### `skills/`

`skills/` 只消费已授权 skill mount，不拥有 Hub。

```text
skills/mounts.py
  存在理由：
    校验并加载本次 run 已授权、已解析、可读取的 skill mounts。

  放置理由：
    skill mount 是执行输入的一部分，但安装和审核不在 Agent。

  禁止：
    不做 git/http 安装。
    不拥有审核状态。
    不扩大工具、MCP 或 sandbox 权限。
```

### `mcp/`

`mcp/` 只连接本次 run 授权的 MCP server/tool。

```text
mcp/servers.py
  存在理由：
    根据 Capabilities 建立 MCP server 连接。

  放置理由：
    MCP server 是外部工具能力来源。

  禁止：
    不扫描全局 MCP 列表。
    不读取未授权 secrets。
    不绕过 namespace/TTL。

mcp/tools.py
  存在理由：
    把 allowed MCP tools 暴露给 DeepAgents。

  放置理由：
    MCP tool 暴露需要独立治理名称、schema、timeout 和结果大小。

  禁止：
    不绕过 allowedTools。
    不把大结果直接塞进 event。
```

### `sandbox/`

`sandbox/` 负责执行环境选择和安全策略。

```text
sandbox/backend.py
  存在理由：
    创建 state / local_shell / e2b / custom backend。

  放置理由：
    backend 是工具和代码执行环境。

  禁止：
    不把 local_shell 作为生产默认。
    不吞掉 provider 初始化失败。

sandbox/policy.py
  存在理由：
    定义 sandbox mode、scope、workspace access、network、timeout、resource limits。

  放置理由：
    sandbox policy 是执行环境约束，不是工具权限本身。

  禁止：
    不让 sandbox 覆盖工具 deny。
    不在 policy 里做账务或 Hub 判断。
```

### `storage/`

`storage/` 存 Agent 自己的执行状态，不存聊天消息。

```text
storage/__init__.py
  存在理由：
    导出 storage 稳定入口，如 make_run_state_store。

  放置理由：
    只服务包导入，不承载业务逻辑。

  禁止：
    不创建连接。
    不读取配置。

storage/checkpoints.py
  存在理由：
    持久化 LangGraph checkpoint，用于 resume、HITL 和故障恢复。

  放置理由：
    checkpoint 是 Agent 执行侧状态。

  禁止：
    不写 session messages。
    不当作聊天历史事实源。

storage/memory.py
  存在理由：
    管理 Agent memory/store。

  放置理由：
    memory 是 Agent 长期上下文，不是 session messages。

  禁止：
    不跨 namespace 泄漏。
    不替代 session 的消息存储。

storage/leases.py
  存在理由：
    管理 run worker lease，防重复执行。

  放置理由：
    lease 是 worker 多实例执行保护。

  禁止：
    不做 session 业务锁。
    不决定 session 是否可创建新消息。

storage/run_state.py
  存在理由：
    定义 RunStateStore 协议，约束 run 去重、resume、终态认领。

  放置理由：
    这是 storage 内部稳定契约，不是 ports 目录。

  禁止：
    不写具体数据库逻辑。
    不读取配置。

storage/mongo_lease_store.py
  存在理由：
    Mongo 实现的 run state / lease store。

  放置理由：
    Mongo 是多 Pod 下的共享执行状态后端。

  禁止：
    不存 session messages。
    不存浏览器事件。

storage/sqlite_lease_store.py
  存在理由：
    SQLite 实现的本地测试和单进程 run state store。

  放置理由：
    SQLite 只服务 agent 本地测试和开发。

  禁止：
    不作为生产默认策略。
    不跨 Pod 使用。
```

### `streams/`

`streams/` 负责 Agent 与 Session 之间的运行时 stream。

```text
streams/__init__.py
  存在理由：
    导出 stream 稳定入口，如 make_stream、MemoryStream、RedisStream。

  放置理由：
    只服务包导入，不承载业务逻辑。

  禁止：
    不创建连接。
    不读取配置。

streams/factory.py
  存在理由：
    根据配置选择 Redis 或 memory stream。

  放置理由：
    stream 后端选择属于传输层。

  禁止：
    不执行 Agent。
    不做 Mongo 轮询。

streams/protocol.py
  存在理由：
    定义 StreamProtocol 和 StreamItem。

  放置理由：
    execution/worker 只依赖这个窄协议。

  禁止：
    不绑定 Redis。
    不生成 browser cursor。

streams/json_types.py
  存在理由：
    校验 stream payload 是否 JSON-safe。

  放置理由：
    stream 是 JSON wire 边界。

  禁止：
    不放业务字段。
    不做 schema 版本治理。

streams/redis.py
  存在理由：
    读写 Redis run/control/event stream。

  放置理由：
    Redis 是跨服务传输层。

  禁止：
    不做 Mongo 轮询。
    不放 Agent 执行业务流程。
    不生成 browser cursor。

streams/memory.py
  存在理由：
    测试用内存 stream。

  放置理由：
    单测和本地 fake 需要快速替代 Redis。

  禁止：
    不作为生产配置。
    不成为第二事实源。
```

### `model/`

`model/` 创建 chat model，不做价格和账务。

```text
model/__init__.py
  存在理由：
    导出 model 稳定入口，如 make_chat_model 和 LocalFakeChatModel。

  放置理由：
    只服务包导入，不承载业务逻辑。

  禁止：
    不创建模型实例。
    不读取配置。

model/factory.py
  存在理由：
    根据 Capabilities 创建 chat model。

  放置理由：
    模型 provider 是执行依赖。

  禁止：
    不决定最终价格。
    不扣积分。
    不读取 session messages。

model/local_fake.py
  存在理由：
    测试和本地开发 fake model。

  放置理由：
    fake model 是 model provider 的测试实现。

  禁止：
    不进入生产默认。
    不掩盖真实 provider 错误。

model/settings.py
  存在理由：
    定义模型 provider 配置和默认模型。

  放置理由：
    配置类型属于 model 能力边界。

  禁止：
    不扣积分。
    不决定最终价格。
```

### 根文件

```text
config.py
  存在理由：
    解析环境变量和 yaml 配置。

  放置理由：
    配置是全局启动输入。

  禁止：
    不执行业务逻辑。
    不创建 graph。
    不连接外部服务。

observability.py
  存在理由：
    trace、log、metrics、error metadata。

  放置理由：
    观测横切整个 worker。

  禁止：
    不影响业务决策。
    不吞异常。
```

### 禁止目录和文件名

```text
kokoro_agent/deepagents/
kokoro_agent/runtime/
kokoro_agent/adapters/
domain/
application/
infrastructure/
interfaces/
ports/
execution/read_events.py
execution/map_events.py
run/invoke.py
projection/transformer.py
RuntimeSubagentRegistry
_LangChainActionRequest
RunJob
AgentRunOptions
KokoroRunContext
```

禁止理由：

```text
deepagents
  依赖底座名，不是 Kokoro 目录语言。

runtime
  太泛，整个 Agent 服务都可以叫 runtime。

adapters
  太泛，不能告诉读者这里负责什么。

domain/application/infrastructure/interfaces
  对 Agent worker 过重，容易把执行链路拆散。

ports
  抽象味太重，当前不需要。

read_events / map_events
  暗示重写 LangChain/DeepAgents event system。

invoke
  框架动作名，不是业务动作名。

projection / transformer
  学术化且含糊，实际只是 RawAgentEvent 输出边界。
```

### `__init__.py` 规则

```text
只允许包说明或稳定导出。
不写业务逻辑。
不创建对象。
不读配置。
不隐式注册工具。
```

## 核心对象

### RunRequest

`RunRequest` 是 session 发给 agent 的执行输入。

```text
RunRequest
  kind
  runId
  threadId
  input
  runtime
  context
  trace
```

说明：

```text
runId
  Kokoro 一次执行的 ID，用于 event stream、幂等和追踪。

threadId
  LangGraph 线程 ID，传入 configurable.thread_id。
  它不是 conversationId，也不是 sessionId。

input
  本次用户输入和必要消息上下文。

runtime
  本次 run 被授权的模型、工具、skills、MCP、subagents、sandbox、approval。

context
  本次 run 的最小业务上下文，如 site/user/workspace/project/namespace。

trace
  观测字段，不参与业务判断。
```

禁止字段：

```text
conversationId
  容易和 sessionId/threadId 混用。

permissionMode
  太粗，应该表达为 runtime.approval 和 per-tool policy。

AgentRunInput / RunJob
  抽象但不清晰。

SkillSpec source union
  安装来源不是 agent 职责。
```

### Capabilities

```text
Capabilities
  model
  tools
  subagents
  skills
  mcpServers
  sandbox
  approval
  memory
```

规则：

```text
Capabilities 表示本次 run 可用能力。
它由 session 或上游业务编排层生成。
Agent 不查询 Hub 来决定用户有什么。
Agent 不扩大 Capabilities 授权范围。
```

### RunContext

推荐命名为 `RunContext`，不要加 `Kokoro` 前缀。

```text
RunContext
  namespace
  siteId
  userId
  workspaceId
  projectId
  sessionId
  artifactScope
  memoryScope
```

说明：

```text
namespace
  agent 侧资源隔离键。
  可由 site/user/workspace/project/session 组合生成。
  Agent 只把它当隔离字符串，不理解复杂业务。

sessionId
  Kokoro 聊天窗口或会话 ID，用于追踪和上下文。

threadId
  LangGraph checkpoint 线程 ID，不应和 sessionId 混用。
```

### RawAgentEvent

Agent 输出 raw event，不输出 browser-facing event。

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

规则：

```text
raw event 不带 web cursor。
raw event 不依赖 BaseMessage.id 排序。
raw event 可以携带 provider/langchain message id 作为 metadata。
session 负责持久化、排序、重放和 browser event 映射。
```

### ToolPolicy

```text
ToolPolicy
  allow
  ask
  deny
```

策略应支持：

```text
按工具名。
按参数。
按 namespace。
按 sandbox。
按 secret grant。
按 MCP server/tool。
```

### ApprovalDecision

```text
approve
reject
edit
respond
```

规则：

```text
respond 只用于 ask_user。
危险工具不同意必须 reject。
edit 表示用户修改工具参数后继续。
approve 表示按原参数执行。
```

## DeepAgents 接入

Agent 必须顺着 DeepAgents/LangGraph 原生能力，而不是自造第二套 agent
framework。

基础映射：

```python
create_deep_agent(
    model=model,
    tools=tools,
    system_prompt=system_prompt,
    skills=skill_paths,
    backend=backend,
    permissions=filesystem_permissions,
    subagents=subagents,
    middleware=middleware,
    interrupt_on=interrupt_on,
    context_schema=RunContext,
    checkpointer=checkpointer,
    store=store,
)
```

Kokoro 只做三类事：

```text
RunRequest -> DeepAgents 参数。
DeepAgents/LangGraph stream -> RawAgentEvent。
Session control -> Command(resume=...)。
```

不做：

```text
复制 DeepAgents 的 subagent 机制。
复制 LangGraph 的 checkpoint 机制。
复制 LangChain middleware 机制。
复制 MCP 工具协议。
```

## Tools

V1 默认工具应少而标准。

```text
ask_user
  模型向用户提问。
  对应 HITL respond 的唯一默认场景。

task / delegate
  交给配置型或受控临时子代理。
  对齐 Claude Code 一类产品里常见的任务委派体验。

todo
  Agent 内部计划和进度。
  输出 todo.updated。
```

不默认提供：

```text
clock / now
  不是 agent 核心能力。测试可用 fixture。

自写 web_fetch
  如果 DeepAgents/LangChain/MCP 已有可用 fetch/search 工具，优先接入现有能力。
  确实要自建时，文件名必须表达清楚，如 web_fetch.py 或 web_search.py。
```

工具命名规则：

```text
工具名小写 snake_case。
文件名和工具语义一致。
不要用 fetch.py 这种含义过宽的名字。
不要把 provider 或框架名写进业务类型名。
```

## Subagents

Subagents 是 V1 核心能力，但必须按授权边界运行。

### 配置型 Subagents

由 `Capabilities.subagents` 传入，映射到 DeepAgents `subagents=`。

```text
name
description
system_prompt
tools
model
skills
mcpServers
approval
sandbox
```

规则：

```text
默认不继承主 agent 的全部工具。
默认不继承全部 MCP servers。
默认不继承全部 skills。
默认不能再创建子代理。
需要继承时必须显式配置。
```

### 临时 Delegate

模型可以请求临时委派，但必须经过策略。

```text
subagent_create = deny | ask | allow
```

默认建议：

```text
开发环境 ask。
生产环境 deny 或按官方策略 allowlist。
高权限工具永远 ask。
```

不允许：

```text
RuntimeSubagentRegistry 让模型静默注册同权限子代理。
模型自己写 system_prompt 后直接获得主 agent 权限。
临时子代理默认拥有 shell、MCP secrets、artifact 写权限。
```

## HITL / 审批

HITL 使用 DeepAgents/LangGraph 原生 interrupt / resume 机制。

链路：

```text
1. ToolPolicy 生成 interrupt_on。
2. DeepAgents 执行到敏感工具。
3. LangGraph interrupt 返回 action_requests 和 review_configs。
4. Agent 输出 tool.awaiting_approval raw event。
5. Session 持久化并转为前端可渲染审批状态。
6. Web 用户 approve / reject / edit / respond。
7. Session 发 run.resume。
8. Agent 转为 Command(resume=...)。
9. Graph 继续执行或终止。
```

审批模型：

```text
ApprovalRequest
  runId
  toolCallId
  toolName
  args
  description
  allowedDecisions
  risk

ApprovalDecision
  toolCallId
  decision
  editedArgs
  message
```

规则：

```text
respond 只给 ask_user。
reject 不应该伪装成工具正常结果。
edit 后必须重新校验参数和权限。
审批状态必须可恢复，worker 重启不丢。
```

## Skills

Skill 是 V1 能力，但 Agent 不拥有 Hub。

Agent 接收的是已授权、已解析、可加载的 mount：

```text
skills:
  - name: official/pdf
    path: /runtime/skills/official/pdf
    lock: sha256:...

  - name: user/release_note
    path: /runtime/skills/users/u_123/release_note
    lock: sha256:...
```

Agent 不接收：

```text
git url
http bundle url
artifact id
marketplace id
审核状态
定价
```

这些属于 Hub/Session/Web 或上游编排层。

Agent 侧规则：

```text
按 path/mount 加载 skill。
校验 lock/hash。
skill 不得扩大 tools/MCP/sandbox 权限。
skill supporting files 按需读取，不一次性全部塞进 prompt。
skill 加载失败要 fail closed，并输出明确错误。
```

## MCP

MCP 是 V1 外部工具接入能力。

推荐策略：

```text
生产主路径：
  HTTP / streamable HTTP。

受限路径：
  stdio，仅本地开发、桌面宿主或明确 sandbox。

兼容路径：
  SSE，不作为默认推荐。
```

Agent 接收：

```text
mcpServers:
  - name
    transport
    url
    allowedTools
    secretGrant
    timeout
```

规则：

```text
只连接 Capabilities 授权的 server。
只暴露 allowedTools。
工具命名 mcp__{server}__{tool}。
secret grant 绑定 namespace/run/tool/TTL。
大结果写 artifact/content ref，event 只给摘要和引用。
```

## Sandbox / Backend

V1 支持可配置 backend。

```text
state
  默认安全 backend。
  不执行本地 shell。

local_shell
  本地开发和明确测试。
  生产默认禁止。

e2b
  远程隔离执行。
  适合代码、文件、shell、浏览器类任务。

custom
  企业私有 sandbox provider。
```

策略：

```text
没有显式 sandbox policy 的高风险工具 fail closed。
local_shell 在 production profile 下必须拒绝。
文件系统权限由 RunRequest runtime.permissions 限定。
sandbox 输出大文件时写 artifact，不塞进 event。
```

## 数据模型

Mongo（agent 拥有）：

```text
kokoro_agent_checkpoints
  runId
  threadId
  checkpointId
  state
  metadata
  createdAt

kokoro_agent_memory
  namespace
  subjectId
  memoryType
  content
  metadata
  createdAt
```

Redis：

```text
kokoro:agent:run_requests
kokoro:agent:run_controls
kokoro:agent:run:{runId}:events
kokoro:agent:leases:{runId}
```

不使用：

```text
Agent 不写 MySQL 账务表。
Agent 不写 session messages。
Agent 不使用 SQLite 作为生产策略。
SQLite 只允许作为本地测试 checkpointer fixture。
```

## API / RPC / Events

入站消息：

```text
run.request
run.resume
run.cancel
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

错误策略：

```text
配置错误：run.failed，错误明确。
权限错误：tool.awaiting_approval 或 tool.denied。
MCP/skill/sandbox 初始化失败：fail closed。
底层 event 解析失败：记录 raw metadata，输出 run.failed，不静默吞。
```

## Admin 管理

Agent 不提供独立后台页面，但需要暴露给平台后台的资源：

```text
run 详情。
worker lease。
checkpoint 状态。
tool approval 记录。
skill mount 结果。
MCP server 连接状态。
sandbox provider 状态。
错误和 trace。
```

权限 key 由平台统一定义，Agent 只输出可审计数据。

## 业务链路

### 普通聊天

```text
1. Web 提交消息给 Session。
2. Session 持久化用户消息。
3. Session 构造 RunRequest。
4. Agent 构造 DeepAgents graph。
5. Agent 输出 raw events。
6. Session 持久化并映射为聊天窗口事件。
7. Web 通过 SSE 接收。
```

### 工具审批

```text
1. Agent 调用敏感工具前 interrupt。
2. Agent 输出 tool.awaiting_approval。
3. Session 保存审批状态。
4. Web 展示审批 UI。
5. 用户选择 approve/reject/edit/respond。
6. Session 发 run.resume。
7. Agent Command(resume=...) 后继续。
```

### ask_user

```text
1. 模型需要用户补充信息。
2. 调用 ask_user。
3. Agent 输出 tool.awaiting_approval，allowedDecisions 只允许 respond。
4. Web 呈现为对话式提问。
5. 用户回答后 resume。
```

### Subagent

```text
1. 主 agent 调用 task/delegate。
2. Agent 根据 Capabilities 找到配置型 subagent。
3. 子代理只获得显式授权的 tools/skills/MCP/sandbox。
4. 子代理事件映射为 subagent.* raw events。
```

## 部署

```text
服务名：
  kokoro-agent-worker

入口：
  kokoro-agent-worker

运行时：
  Python + uv

关键环境变量：
  KOKORO_REDIS_URL
  KOKORO_AGENT_MONGO_URL
  KOKORO_AGENT_CHECKPOINTER
  KOKORO_AGENT_DEFAULT_BACKEND=state|local_shell|e2b|custom
  OPENAI_API_KEY
  ANTHROPIC_API_KEY
  E2B_API_KEY

多 Pod：
  runId lease。
  threadId checkpoint。
  control resume 幂等。
```

配置文件：

```text
.env.example.yaml
.env.dev
.env.development
.env.test
.env.prerelease
.env.prod
```

规则：

```text
本地开发可以启用 local_shell。
测试可以使用 local fake model 和 memory stream。
生产必须显式选择安全 backend。
K8s 用 env/configmap/secret 覆盖同名配置。
```

## 测试

单测：

```text
RunRequest parser。
Capabilities resolver。
RunContext namespace。
ToolPolicy -> interrupt_on。
ApprovalDecision -> Command(resume=...)。
Agent event mapper。
Skill mount loader。
MCP wrapper。
Sandbox policy。
Subagent config mapping。
```

集成：

```text
Redis run.request -> raw events。
HITL approve/reject/edit/respond。
ask_user -> respond。
checkpoint resume。
state backend smoke。
local_shell dev smoke。
e2b smoke。
MCP HTTP server smoke。
skill mount smoke。
```

必须覆盖的反例：

```text
未授权 MCP tool 不暴露。
未授权 skill 不加载。
local_shell 在 prod profile 下失败。
临时 subagent 不能继承主 agent 全部权限。
respond 不能用于危险工具。
edit 后参数必须重新校验。
重复 run.request 只执行一次。
worker 重启后 pending approval 可恢复。
BaseMessage.id 不参与跨服务排序。
```

## 风险和边界

最高风险：

```text
把 DeepAgents 依赖变成顶层架构名。
为 LangGraph event 自造第二套框架。
让模型静默创建同权限子代理。
让 skill/MCP 扩大权限。
把 local_shell 当生产 sandbox。
Agent 写 session messages。
Agent 扣积分或决定价格。
```

禁止项：

```text
不新增 kokoro-contracts。
不使用 ports 目录命名。
不引入 PostgreSQL。
不保留 legacy 兼容 shim。
不为了旧测试保留 seq/cursor 兼容字段。
不把安装来源 union 放进 agent request。
```

## 后续任务

P0：

```text
冻结目录架构。
把现有不清晰目录和文件命名收敛为执行链路架构。
删除 clock/now、自写 fetch、runtime subagent registry。
落地 ask_user。
RunRequest / Capabilities / RunContext 定稿。
HITL 走 interrupt_on + Command(resume=...)。
Subagents 改为 DeepAgents 标准配置映射。
```

P1：

```text
MCP HTTP / streamable HTTP client。
Skills mount loader 和 lock/hash 校验。
E2B backend。
OpenTelemetry / LangSmith trace。
Admin 可审计状态输出。
```

P2：

```text
更复杂的专业 agent 编排。
异步 subagent 调度。
多模型路由。
长任务 artifact 结果回写。
```
