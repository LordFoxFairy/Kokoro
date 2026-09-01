# ADR-021 FeatureKey 是全局产品能力 identity

状态：已采纳，2026-08-27。实现边界以 [42 GA 核心架构](../technical/42-ga-core-architecture.md) 与
[36 GA 技术方案](../technical/36-ga-final-agent-technical-plan.md) 为准。

## 决策

`feature_key` 是 System、Session、GA、Studio 与 Billing 识别同一产品能力的唯一业务键。
它不是 Agent 名、模型标签、route/slug，也不是图或版本引用。

```text
App / route / slug
  -> System admission
  -> feature_key
  -> Session
  -> GA FeatureCatalog.get(feature_key)
  -> AgentFactory
  -> DeepAgents native Agent 或官方 Swarm
```

- Browser、CLI、Session 不直接选择 Agent、Skill、MCP 或 graph。
- GA 只解析 worker 内置 FeatureCatalog，不读取 System 私库来决定运行结构。
- Music、Chat 等产品由独立 Feature key 表达；同一 Agent 可以被多个 Feature 复用。
- tenant、subject、Skill 可见性和权限只能对已选 Feature 做 owner-side 动态收窄，不能偷偷替换 Agent 组合。
- 若确实是全新的产品能力或不兼容的 Agent 组合，分配新的 FeatureKey；Session 仍只保存 FeatureKey，不保存版本/binding。

## Session 与 GA 的事实分离

```text
Session: feature_key、用户可见消息/run、生命周期
GA:     ExecutionIdentity -> RuntimeNamespace、DeepAgents checkpoint、RunLedger、chat_events
```

同一 Session 的普通新消息在上一 Run terminal 后继续同一 native checkpoint；fork 才建立新的 Session/thread/state。
GA 不定义 `DeepAgentState`、`CompiledGraph`、`WorkflowDigest` 或 `FeatureClaimGate`。

## 不变量

```text
FeatureKey 是产品能力 identity，不是实现版本或图选择器。
GA 只从 feature_key 取得受信 Feature；caller 不提交 Agent/graph 配方。
Session 不保存 Agent、member、release、version 或 binding。
不同产品组合使用不同 FeatureKey；同一 Agent 可复用。
```
