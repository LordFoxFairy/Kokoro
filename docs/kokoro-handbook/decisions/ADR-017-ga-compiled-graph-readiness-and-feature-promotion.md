# ADR-017 GA Feature 就绪与 DeepAgents 构造边界

状态：已废止；当前决策以 [42 GA 核心架构](../technical/42-ga-core-architecture.md)、
[36 GA 技术方案](../technical/36-ga-final-agent-technical-plan.md) 和
[ADR-020](ADR-020-native-framework-compatibility-and-swarm-adapter.md) 为准。

## 结论

GA 不维护 `CompiledGraphRegistry`、`WorkflowDigest`、`FeatureClaimGate` 或自有
`WorkflowCompiler`。这些名字会把 DeepAgents 再包装成第二套运行时，也会诱导 Session 保存图引用。

Worker 启动时只注册代码内置的 `Feature`，由 `AgentFactory` 直接调用：

```text
Feature
  -> AgentFactory
  -> deepagents.create_deep_agent(...)
  -> 单 Agent 或官方 langgraph-swarm
```

就绪检查只验证依赖可导入、Feature 声明合法、模型/存储连接可用；它不产生新的 Graph/State
对象，也不向外暴露图摘要。部署平台只负责进程健康、流量和滚动重启。

## 恢复规则

- 同一 Session 的普通下一次调用在上一 Run terminal 后继续 DeepAgents 原生 checkpoint。
- fork 才创建新 Session/thread/state。
- worker reclaim 使用当前 Feature 定义重建 DeepAgent；若原生 checkpoint 无法由当前声明确定恢复，
  Run 进入明确失败，而不是在 Session 中增加 graph/version/binding 字段。
- Swarm 的 `active_agent` 只属于官方 `SwarmState`。

## 被禁止的概念

```text
CompiledGraphRegistry / WorkflowCompiler / WorkflowDigest / FeatureClaimGate
Session graph binding / release / version snapshot / custom router / custom state
```

这些概念不属于 GA V1。未来确有动态编排需求时，仍只能生成同一套 Feature/Agent 声明，
由同一 AgentFactory 构造，不能热改运行中的 checkpoint。
