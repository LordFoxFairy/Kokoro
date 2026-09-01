# ADR-008 Agent / Session / Web 标准运行时边界

> **状态：历史 V1 三仓运行时决策。**其中 Session→Agent 传 `RuntimeConfig`、Agent→Session 传 raw execution
> events 的模型已被目标架构替代。新设计只读 [36 GA 整体 Agent 技术方案](../technical/36-ga-final-agent-technical-plan.md)、
> [38 公共运行契约](../technical/38-ga-public-runtime-contract.md) 与
> [ADR-016 ProductEvent](ADR-016-orchestration-policy-and-product-event-projection.md)：Session 只持有产品
> `feature_key` 与投影，GA checkpoint 持有同一 Session 的 `ConversationState`，跨仓输出只能是安全 ProductEvent。

状态：已采纳（V1）。

## 背景

三仓运行时已经具备通用聊天、流式事件、HITL、Skills、MCP、subagents
和 sandbox 的雏形，但实现和文档中曾混入多套自造概念：

```text
RunJob
AgentRunInput
conversationId
permissionMode
seq
cursor
lastResumeId / ?after=
runtime-custom subagent registry
respond 作为通用控制动作
```

这些概念容易造成维护负担：Web 误把传输游标当业务状态，Session 先 live
后落库导致 replay 不可靠，Agent 复制 LangGraph/DeepAgents 的能力而不是使用
原生机制。

## 决策

V1 以主流框架和浏览器标准为基础：

```text
LangChain / LangGraph:
  Runtime context
  config.configurable.thread_id
  checkpointer / store
  middleware
  interrupt / Command(resume=...)

DeepAgents:
  create_deep_agent
  tools
  skills
  backend
  permissions
  subagents / task tool
  interrupt_on

Browser:
  POST 创建消息
  GET snapshot
  EventSource SSE
  Last-Event-ID 自动续连
```

三仓契约固定为：

```text
web -> session:
  POST /sessions/:sessionId/messages
  GET  /sessions/:sessionId
  GET  /sessions/:sessionId/events
  POST /sessions/:sessionId/runs/:runId/control

session -> agent:
  RunRequest

agent -> session:
  raw execution events

session -> web:
  browser-facing session events
```

`RunRequest` 是跨服务执行请求：

```text
RunRequest
  runId
  threadId
  input
  runtime: RuntimeConfig
  context: RuntimeContext
  trace
```

## 不变量

```text
sessionId 是产品聊天窗口 ID。
threadId 是 Agent/LangGraph 边界 ID；V1 等于 sessionId。
conversationId 删除。
eventId 只做幂等去重，不排序。
SSE id 只做 Last-Event-ID replay anchor。
Web 不读取 cursor/order 字段；seq 只作同一 run 内 UI 交错。
Session relay 必须 DB-first，再 publish live。
Agent 不写 session Mongo。
Session 不读 agent checkpoint。
Skills/MCP Hub 安装、审核、启用不归 agent 拥有。
Subagents 走 DeepAgents subagents/task；临时 delegate 必须受权限策略约束。
respond 只用于 ask_user_question。
```

## 替代方案（已否决）

```text
保留 RunJob
  过于抽象，不贴近 LangGraph/DeepAgents/CLI 工具命名。

保留 AgentRunInput
  容易继续膨胀为所有字段的大杂烩，且脱离原生 RuntimeConfig/context 语义。

Web 使用 ?after= 手动续传
  绕开 EventSource Last-Event-ID，重复发明恢复协议。

Redis cursor/seq 作为业务排序源
  把传输细节泄漏到 Web domain，后续维护困难。

Agent 拥有 Skill/MCP Hub
  会迫使 Web 调 agent 做管理，破坏三仓边界。

模型静默创建同权限 runtime subagent
  容易绕过权限、sandbox 和审计。
```

## 影响

正向影响：

```text
命名贴近 LangChain/DeepAgents 标准。
Web/Session/Agent 边界清楚。
Replay 与 refresh 语义可靠。
HITL 与 ask_user_question 不混淆。
Skills/MCP 可管理、可审计、可替换。
```

代价：

```text
需要删除旧接口和旧字段，不能靠兼容 shim 拖着走。
需要重写 Web reducer 中 seq/cursor 排序假设。
需要重写 Session relay 为 DB-first。
需要重构 Agent 目录和 RunRequest 类型。
```

## 后续执行规则

```text
实现前先改测试：旧字段出现即失败。
删除旧入口，不做长期兼容。
每个自定义抽象必须说明对应的原生机制，以及为什么不能直接用原生机制。
三仓外模块不因本 ADR 被修改。
```
