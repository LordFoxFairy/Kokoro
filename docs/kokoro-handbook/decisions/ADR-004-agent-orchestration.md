# ADR-004 三层运行时与 Agent 编排边界

状态：已采纳。

## 背景

浏览器、会话流、agent 执行三者职责若混在一起，会导致前端直连模型、
会话层执行推理、agent 直接面向浏览器等耦合。需要固定运行时分层和
编排边界。

## 决策

```text
kokoro-web      纯 UI 消费层，消费 session SSE，reducer 折叠 thread，不产生权威事件。
kokoro-session  浏览器面对的 session/SSE/replay 层，strict parse + normalize + 持久化 + 发布。
kokoro-agent    执行层，跑 LangChain/DeepAgents/LangGraph，调用模型/工具/subagent，产出原始执行事件。

Agent 编排发生在 agent 内部，不是前端跳转。V1 先支持通用 Skills、
MCP tools、内置工具和轻量 subagent；专业 Agent 后续接入同一机制。

Session 发给 Agent 的不是零散字段，而是 `AgentRunInput`：
site/user/workspace/session/run 身份、上下文、model runtime、permission mode、
backend policy、启用的 skills、MCP servers/tools、内置工具集合和 trace context。
```

## 不变量

```text
浏览器只消费 kokoro-session 的 SSE。
kokoro-agent 不直接面向浏览器。
kokoro-session 不执行 agent。
kokoro-web 不产生权威事件。
agent 不直接扣积分（只能 credit.quote/hold/commit/release）。
eventId 是幂等去重锚点，不承担排序。
LangChain BaseMessage.id / tool call id 是身份标识，不承担跨服务排序。
浏览器排序依赖 session 写入和 SSE 发送顺序，不反解 cursor/seq。
run.completed(status=completed/cancelled/timeout) 和 run.failed 是终态。
```

## 替代方案（已否决）

```text
web 直连 agent / 模型        丧失会话归一化、回放、去重、权限校验。
session 内执行推理           会话层与执行层耦合，无法独立扩容 agent worker。
handoff 做成前端路由         无法在一次 run 内编排多 agent 和共享 credit/artifact 上下文。
```

## 影响

事件契约：agent 原始事件 -> session browser-facing session event。
详见 [agent 架构](../technical/03-agent-architecture.md)、
[session 架构](../technical/04-session-architecture.md)、
[agent-handoff 链路](../business-flows/agent-handoff.md)。

约束：langchain + deepagents 是长期基座，不做 provider-neutral 重抽象，只在其上构建。
