# Agent 协作与 Handoff 链路

状态：当前 GA 协作链路，2026-08-27。总体边界以
[42 GA 核心架构](../technical/42-ga-core-architecture.md) 和
[36 GA 总体方案](../technical/36-ga-final-agent-technical-plan.md) 为准。

## 先选正确的 DeepAgents 原生机制

| 需求 | 机制 |
|---|---|
| 缺少知识、脚本或参考资料 | GA 固定 `find_skills` / `load_skill` |
| 隔离研究、并行子任务或长上下文工作 | DeepAgents 原生 `task` subagent |
| 专业 Agent 接手同一用户会话 | 官方 `langgraph-swarm` handoff |

Skill、prompt、MCP server 和工作区文件都是 Agent 的能力输入，不是额外角色或 peer。GA 不创建
Workflow、lead、flow、Team、Role 或自定义 handoff router。

## 主流程

```text
feature_key
  -> GA worker 取 worker-local Feature
  -> AgentFactory
  -> 单 Agent: deepagents.create_deep_agent(...)
     多 peer: 每个 Agent create_deep_agent(...) + official create_swarm(...)
  -> DeepAgents native state/checkpoint
  -> GA RunLedger / chat facts / Workbench
  -> Redis live -> Session 查询/replay -> AG-UI/SSE
```

Feature 负责选择 Agent、入口 Agent 和允许的 peer handoff。调用方只提交
`feature_key + ExecutionIdentity + input`，不提交 Agent、成员、Skill、MCP、graph、namespace
或 thread 配方。

## 两种协作语义

### DeepAgents 原生 subagent

主 Agent 需要后台隔离工作时，使用 DeepAgents 的 `subagents`/`task`。子代理在父 Agent 的原生
执行中完成，用户回复仍归父 Agent；GA 只在 RunLedger 记录必要的 WorkItem 事实，不创建 child
Session、第二个 checkpoint 或新的运行时。

### 官方 Swarm handoff

多个 Agent 需要在同一用户会话中互相接手时，Feature 声明 handoff 边：

```text
music      -> [music]
chat       -> [general]
music_chat -> [general, music]
              general -> music
              music -> general
```

AgentFactory 为每个 peer 调用 DeepAgents `create_deep_agent`，再把原生 runnable 交给官方
`langgraph_swarm.create_swarm`。`SwarmState.active_agent`、handoff 工具和恢复语义全部由官方
框架拥有；GA 不复制或重命名它们。

## 权限与计费

每个 Agent 的固定工具、Skill、MCP 和 sandbox policy 由 GA 的 Feature/Agent 声明确定；外部
Capability 只允许在当前主体授权范围内收窄能力。每一次 provider accepted model invocation
产生稳定 `invocation_id`，Billing 按调用次数幂等结算；HITL、handoff、replay 和恢复不会重复
产生调用事实。

## 恢复与失败

- DeepAgents native state/checkpoint 或官方 `SwarmState` 是恢复真源。
- 同一 Session 的普通新消息仅在前一 Run terminal 后继续同一 thread；fork 才建立新的
  Session/thread/state。
- worker 重启只恢复既有 checkpoint 与 RunLedger，不根据请求重新组装另一套图或状态。
- handoff、subagent、工具和 provider 失败都归属于当前 Run；终态由 GA 的 terminal claim 收口。
- GA `chat_messages/chat_events` 与 LangChain native message/checkpoint ID 分离；Redis 仅为实时
  传输，断线由 durable chat events replay。

## 验收

```text
single Agent     = 直接 DeepAgents
后台协作         = DeepAgents native subagent
会话交接         = official langgraph-swarm
产品组装         = Feature
```

任何新增能力都先判断它属于现有 Agent 的工具/Skill/subagent，还是一个新的完整 Agent；只有
需要对外暴露新的产品入口时才新增 Feature。不要为一项能力拆出 composer、arranger、reviewer
等角色文件，也不要增加第二个编排或运行时层。
