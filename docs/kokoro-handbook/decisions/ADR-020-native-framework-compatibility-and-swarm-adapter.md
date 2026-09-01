# ADR-020 DeepAgents 原生组合与官方 Swarm 接入

状态：已采纳，2026-08-27。

关联：[42 GA 核心架构](../technical/42-ga-core-architecture.md)、[36 GA 技术方案](../technical/36-ga-final-agent-technical-plan.md) 与
[35 LangGraph Swarm 专项](../technical/35-ga-langgraph-swarm-architecture.md)。

## 背景

GA 的唯一 Agent 基础是 DeepAgents。GA 需要同时支持两种协作语义：

```text
后台隔离工作       -> DeepAgents native subagent
同一用户会话的接手 -> official langgraph-swarm
```

此前把 `langchain.agents.create_agent` 作为 Swarm peer、把 DeepAgents 只用于单 Agent 的方案，
会让同一个产品出现两套 Agent 语义，也违背 GA 的基础选择。该方案废弃。

## 决策

### 1. 所有 GA Agent 都从 DeepAgents 创建

```text
Agent definition
  -> AgentFactory
  -> deepagents.create_deep_agent(...)
  -> DeepAgents native runnable
```

单 Agent Feature 直接运行这个 native runnable。需要后台隔离任务时，使用同一个 Agent 的
DeepAgents native subagent，不创建 GA 角色或平行 Agent 类型。

### 2. 多 Agent 只接官方 Swarm

```text
Feature.agents
  -> 为每个 Agent 调用 deepagents.create_deep_agent(...)
  -> 为声明的边创建官方 create_handoff_tool
  -> langgraph_swarm.create_swarm(...)
  -> official SwarmState + 一个 outer checkpoint
```

`swarm.py` 只做上述官方 API 的薄接线：

- `Agent.key` 使用 lower-snake-case，并直接作为 peer name；
- handoff target 必须是 Feature 中的其他 Agent；
- 禁止 self/unknown target、alias、动态 member 和调用方提供的 `active_agent`；
- 一条模型消息最多包含一个 handoff call，混合普通工具的 batch fail-loud；
- `active_agent` 只属于官方 `SwarmState`，GA 不维护副本。

GA 不实现 router、prompt swap、自定义 handoff command 或第二套 state。

### 3. 兼容性门禁不改变基础选择

DeepAgents compiled runnable 与官方 Swarm 的兼容性必须通过真实的 A→B handoff、checkpoint、
restart、HITL 和下一轮消息测试后，组合 Feature 才能启用。

如果锁定的 DeepAgents/LangGraph/Swarm 组合未通过门禁：

1. worker warm 阶段将该 Swarm Feature 标记为不可用并给出明确错误；
2. 单 Agent Feature 和 native subagent Feature 继续运行；
3. 不降级为 `langchain.agents.create_agent`；
4. 不实现 GA 自有 router 或状态适配层；
5. 通过官方依赖升级重新验证后再启用。

框架依赖锁只属于部署构建输入，不进入 Session、Run、Agent 或 checkpoint 字段。

### 4. 状态与上下文归属

```text
单 Agent / native subagent -> DeepAgents 原生 state/checkpoint
Swarm                    -> official SwarmState/checkpoint
```

GA 不定义 `DeepAgentState`、`KokoroAgentState`、`SwarmState` 替代品或 Session Agent state。
`ExecutionIdentity`、RunLedger、Skill mount、计费和产品事件保留在 GA 自己的事实面，不塞入
native checkpoint。

## 验收门

- `music` Agent 可单独作为 `music` Feature；
- 组合 Feature 的每个 peer 都由 `deepagents.create_deep_agent` 创建；
- handoff 只调用官方 `create_handoff_tool` 与 `langgraph_swarm.create_swarm`；
- A→B handoff 后 `SwarmState.active_agent`、checkpoint 恢复和下一轮消息均正确；
- 兼容性失败时 fail-loud，不出现第二套 Agent runtime；
- Session 不保存 Agent、member、图、依赖版本或 active-agent 选择。
