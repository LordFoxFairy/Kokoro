# ADR-015 Agent 原生状态与 Feature 上下文

状态：已废止；当前以 [42 GA 核心架构](../technical/42-ga-core-architecture.md) 为准。

GA 不定义 `KokoroAgentState`、`DeepAgentState`、`ConversationState` 包装类或 Session Agent state。
DeepAgents/LangGraph 自己拥有 native state/checkpoint；官方 Swarm 自己拥有 `SwarmState`。

```text
Feature -> AgentFactory -> create_deep_agent(...)
                           -> native checkpoint
Feature(多个 peer) -> official langgraph_swarm -> official SwarmState
```

`ExecutionIdentity`、RunLedger、HITL、Skill mount、计费和产品事件属于 GA 事实面，不塞入 native state。
Session 只保存 `feature_key`、用户可见消息和生命周期，不保存 Agent、member、graph、版本或 binding。
