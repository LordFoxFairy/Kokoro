# 35. GA × official LangGraph Swarm

状态：42/36 的 Swarm 细节，2026-08-27。

Swarm 不是 GA 自己的 runtime。只有当一个 Feature 明确需要多个 Agent 互相接手同一用户对话时，
AgentFactory 为每个 peer 调用 DeepAgents `create_deep_agent`，再调用官方
`langgraph_swarm.create_swarm`。

## 1. 两种协作语义

```text
主 Agent 委派后台隔离工作 -> DeepAgents native subagent
不同 Agent 接手用户会话   -> official langgraph-swarm
```

不要把 peer handoff、后台 task 和固定步骤混在一个自有 Team/产品能力装配/router 中。

## 2. Feature 声明

```text
music      -> [music]
music_chat -> [general, music]
              entry_agent = general
              handoffs = general -> music, music -> general
```

Feature 负责声明成员和允许的 handoff 边；Session、RunRequest 和 Builder 不得在运行时修改它们。
Agent key 使用稳定的 lower-snake-case code key，直接传给 DeepAgents 与官方
`create_handoff_tool`，不做 alias/binding。

## 3. 官方对象与状态

```text
AgentFactory
  -> create_deep_agent(peer_1)
  -> create_deep_agent(peer_2)
  -> create_swarm(peers, default_active_agent=entry)
  -> official SwarmState + one outer checkpoint
```

GA 不实现 handoff router、prompt-swap 或自定义 `active_agent` state。新 thread 不接受调用方提供
native state；继续运行时只从官方 checkpoint 恢复 `SwarmState.active_agent`。

## 4. 边界规则

- handoff target 必须是 Feature 声明的其他 Agent，禁止 self/unknown target；
- 一个模型消息最多一个 handoff tool call，避免官方 ToolNode batch 产生不确定交接；
- peer 不再挂 native subagent；需要后台隔离任务时改用单 Agent 的 DeepAgents 路径；
- Swarm peer 使用 GA 固定 ToolPolicy/HITL 和 external-client contract，不读取外部私库；
- handoff、checkpoint、RunLedger 和 chat facts 的恢复仍由 GA worker 负责，但不重写官方状态。
