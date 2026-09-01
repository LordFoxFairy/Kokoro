# ADR-018 GA Thread、上下文与记忆边界

状态：已废止；当前以 [42 GA 核心架构](../technical/42-ga-core-architecture.md) 与
[ADR-020](ADR-020-native-framework-compatibility-and-swarm-adapter.md) 为准。

## 当前规则

- DeepAgents/LangGraph 原生 state 与 checkpoint 是 Agent 的唯一上下文事实；GA 不定义 state 包装类型。
- 官方 Swarm 的 `active_agent` 只存在于官方 `SwarmState`。
- 同一 Session 的普通后续消息在上一 Run terminal 后继续同一 checkpoint；fork 创建新的 Session/thread/state。
- GA 的 RunLedger、ExecutionIdentity、Skill mount、memory store、workbench 和 ProductEvent 与 checkpoint 分离。
- 上下文压缩、文件 offload 等行为优先使用 DeepAgents 已提供的 middleware/backend；GA 只装配参数，不复制其 reducer 或消息模型。

Session 不保存 `RuntimeConfig`、`RuntimeContext`、Agent/graph/version/binding，也不参与 checkpoint 恢复。
