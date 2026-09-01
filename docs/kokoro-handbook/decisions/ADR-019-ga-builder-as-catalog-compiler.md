# ADR-019 动态组装与产品 Feature 边界

状态：已废止；当前决策以 [42 GA 核心架构](../technical/42-ga-core-architecture.md) 为准。

## 结论

业务组装只有一个概念：`Feature`。它选择一个或多个完整 `Agent`，指定入口 Agent，必要时声明
official Swarm handoff。GA 不新增 `Workflow`、`WorkflowDraft`、`WorkflowCompiler`、`flow`
模式或 `CompiledGraph` 目录。

```text
Agent      = 可复用的 DeepAgent 能力
Feature    = 对外产品能力的组装声明
AgentFactory = 唯一内部构造入口
```

### 当前代码组装

```python
music = Feature(key="music", agents=(MUSIC_AGENT,), entry_agent="music")
music_chat = Feature(
    key="music_chat",
    agents=(GENERAL_AGENT, MUSIC_AGENT),
    entry_agent="general",
    handoffs=(("general", "music"), ("music", "general")),
)
```

单 Agent Feature 直接走 `deepagents.create_deep_agent`；多个 peer 由同一 Factory 创建多个
DeepAgent，再交给官方 `langgraph_swarm.create_swarm`。后台隔离任务使用 DeepAgents native
subagent，不增加角色目录。

### 未来可视化组装

可视化 Builder 只编辑已注册 Agent、固定工具、Skill/MCP grant 和 handoff 边，最终生成同一套
`Feature` 声明。Builder 不写 Session、RunRequest、checkpoint，不提交任意 graph JSON，也不能
改变运行中的 Agent。Builder 不可用时，代码内置 Feature 继续运行。

## 明确不做

```text
Session 选择 Agent/图
每个 Session 保存 release/version/binding
GA 自定义 Graph、State、Router、Compiler
composer/arranger/reviewer 角色拆分
```
