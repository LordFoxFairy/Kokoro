# Feature 结果契约与质量门

状态：当前方案，2026-08-27。执行边界以 [42 GA 核心架构](42-ga-core-architecture.md) 为准。

## 1. 两个 owner

`kokoro-system` 定义产品结果契约：输入/输出、展示面、Job/Artifact 交付、价格与产品权限。
`kokoro-agent` 定义执行 Feature：一个或多个 Agent、固定工具/Skill/MCP grant、入口 Agent 与可选
official Swarm handoff。两者只通过 `feature_key` 对齐，不复制 Agent 配方。

```text
ProductOutcomeContract(system)
  feature_key / input / delivery / cost / permission
        |
        v
Feature(GA)
  agents / entry_agent / handoffs
        |
        v
AgentFactory -> DeepAgents native Agent 或 official Swarm
```

## 2. 结果事件

GA 只把安全结果写入 `chat_events` 并发布 Redis live：assistant delta/final、activity、approval、
ArtifactReady、StudioJobLinked、terminal。raw thinking、工具参数/结果、subagent 内文和 sandbox
路径不进入 ProductEvent。

`chat_messages` 保存用户可见的最终 user/assistant 消息；LangChain checkpoint 与这两类数据完全分离。

## 3. 质量门

每个 Feature 共享同一条 DeepAgents 执行与恢复路径，评测不创建第二个 Agent runtime：

1. **契约门**：输入、必需交付、失败/拒绝状态和事件 payload 符合 ProductOutcomeContract。
2. **能力门**：Agent/Feature 声明的 Skill、MCP、工具和 sandbox 权限只可被 owner 当前授权收窄。
3. **可靠性门**：HITL、worker reclaim、checkpoint resume、effect 幂等、Redis 断线 replay 均可恢复。
4. **交付门**：Studio Job/Storage Artifact 使用各自 public contract；GA 只发稳定 JobRef/ArtifactRef。
5. **计费门**：每个 provider accepted invocation 以稳定 `invocation_id` 计一次；replay 不重复扣费。
6. **质量门**：在固定 fixture 上验证用户约束覆盖、结构化输出和媒体结果；必要时人工 rubric 复核。

## 4. 组合规则

- 单 Agent Feature：直接调用 DeepAgents。
- 多 Agent Feature：只有需要同一会话 peer 接手时才声明 handoff 并使用官方 Swarm。
- 一个 Agent 需要后台隔离工作：使用 DeepAgents native subagent。
- 不增加 composer/arranger/reviewer 角色、lead/flow 模式、typed port、WorkItem graph 或自有 router。

## 5. 示例

```text
FEATURE_KEY_MUSIC_CREATE
  -> Feature(agents=[music], entry_agent=music)
  -> 生成 StudioJobLinked(JobRef) 或可解释失败

FEATURE_KEY_GENERAL_ASSIST
  -> Feature(agents=[general], entry_agent=general)
  -> 可按 Agent 声明调用 native subagent，但用户只看到最终 assistant/Job/Artifact 结果

FEATURE_KEY_MUSIC_CHAT
  -> Feature(agents=[general, music], entry_agent=general, handoffs=[...])
  -> official langgraph-swarm peer handoff
```

未来可视化 Builder 只生成同一套 Feature/Agent 声明，经同一 AgentFactory 构造；不写 Session、Run、
checkpoint，也不热改运行中的 Agent。
