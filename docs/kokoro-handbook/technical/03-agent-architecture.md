# Agent 架构

Agent 模块详案见：[kokoro-agent 技术方案](../modules/kokoro-agent.md)。
三仓 V1 运行时总方案见：
[Agent / Session / Web V1 标准运行时方案](11-agent-session-web-v1-runtime.md)。

## 结论

`kokoro-agent` 不采用传统 DDD 四层目录。

它采用执行链路架构：

```text
worker 接消息
run 描述本次执行
execution 运行或恢复 agent
tools / subagents / skills / mcp / sandbox 提供执行能力
storage / streams / model / config / observability 提供支撑设施
```

DeepAgents 是执行底座，可以在代码中直接使用，但禁止成为目录名。

## 推理过程

### 1. 从 Agent 链路开始

```text
session 投递 run.request。
worker 领取 run。
解析 RunRequest。
校验 capabilities 和 permissions。
准备 model、tools、skills、MCP、subagents、sandbox、memory。
创建 DeepAgents graph。
执行或 resume graph。
DeepAgents/LangChain/LangGraph 负责 stream、interrupt、checkpoint。
Agent 发布 RawAgentEvent。
Session 负责持久化、排序、重放和浏览器事件。
```

目录必须服务这条链路。

### 2. 不套传统 DDD

Agent 不是订单、支付、库存，不需要 `domain/application/infrastructure/interfaces`
四层模板。

硬套后容易出现：

```text
domain 变成类型桶。
application 变成脚本壳。
infrastructure 变成巨大垃圾桶。
ports/protocols 为抽象而抽象。
```

只保留三种边界意识：

```text
agent 不写 session messages。
agent 不扣积分。
agent 不拥有 Skill/MCP Hub。
```

### 3. 不重写 DeepAgents

DeepAgents/LangChain/LangGraph 负责：

```text
可运行 agent。
tool calling。
skills。
MCP tools。
subagents。
interrupt / Command(resume=...)。
thread_id / checkpoint。
stream events。
backend / sandbox。
```

Kokoro-agent 负责：

```text
RunRequest -> Capabilities -> Permissions -> DeepAgents graph。
Execute / Resume。
RawAgentEvent 输出。
run lease、checkpoint、memory。
```

## 目标目录

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

  tools/
    registry.py
    permissions.py
    ask_user.py
    names.py

  subagents/
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
    checkpoints.py
    memory.py
    leases.py
    run_state.py
    mongo_lease_store.py
    sqlite_lease_store.py

  streams/
    factory.py
    protocol.py
    json_types.py
    redis.py
    memory.py

  model/
    factory.py
    local_fake.py
    settings.py

  config.py
  observability.py
```

每个目录和 `.py` 的存在理由、放置理由和禁止项，以
[kokoro-agent 技术方案](../modules/kokoro-agent.md) 为准。

## 命名红线

禁止新增三类形态：

1. 以框架品牌或泛词命名目录，例如 `deepagents`、`runtime`、`adapters`。
2. 把 Agent worker 套进重 DDD 四层模板，例如 `domain/application/infrastructure/interfaces/ports`。
3. 自造 LangChain/DeepAgents 已经有的事件系统或框架动作名，例如 `read_events`、`map_events`、`run.invoke`。

禁止保留含糊类型名：`RuntimeSubagentRegistry`、`_LangChainActionRequest`、`RunJob`、`AgentRunOptions`、`KokoroRunContext`。

## 命名规则

```text
目录名表达 Agent 链路职责，不表达框架品牌名。
文件名表达维护者要找的业务动作，不表达内部技术动作。
DeepAgents 可以 import，不能成为目录名。
LangChain/DeepAgents event 已经存在，Kokoro 不命名 read/map events。
__init__.py 只允许包说明和稳定导出。
```

## V1 能力范围

V1 必须支持：

```text
通用聊天 agent loop。
DeepAgents create_deep_agent。
LangGraph thread_id / checkpointer / interrupt。
RunContext 注入。
Skills mount 加载。
MCP HTTP / streamable HTTP client。
ask_user。
task/delegate subagent。
todo。
HITL approve/reject/edit/respond。
state/local_shell/e2b/custom backend。
raw agent events。
```

V1 不做：

```text
Agent 查询 Hub/catalog。
Agent 决定价格。
Agent 写 session messages。
Agent 直接扣积分。
Provider-neutral 第二套 agent framework。
```

## 验收标准

```text
从目录能读出 Agent 完整执行链路。
每个目录和 .py 都有存在理由、放置理由、禁止项。
没有以框架品牌或泛词命名的顶层/子目录。
没有 DDD 四层模板目录。
没有自造 read/map event wrapper。
HITL 使用 interrupt_on + Command(resume=...)。
skills/MCP/sandbox 都来自本次 run 的显式授权 capabilities。
```
