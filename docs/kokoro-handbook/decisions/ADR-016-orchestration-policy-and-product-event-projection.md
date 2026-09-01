# ADR-016 Feature 组装与 ProductEvent 边界

状态：已废止；当前以 [42 GA 核心架构](../technical/42-ga-core-architecture.md)、
[36 GA 技术方案](../technical/36-ga-final-agent-technical-plan.md) 为准。

## 当前决策

GA 的业务组装只有 `Feature`，运行时只有 DeepAgents。Feature 可以声明一个或多个完整 Agent；
需要同一会话交接时声明 official Swarm handoff。后台并行或隔离工作使用 DeepAgents native
subagent，不增加 `Workflow`、`flow`、角色层、reply-owner router 或自定义 execution policy。

```text
Feature -> AgentFactory -> create_deep_agent
                     -> (optional) official langgraph_swarm.create_swarm
```

工具权限、Skill/MCP grant、HITL 和 sandbox 是 Agent/Feature 的静态装配数据；请求只带
`feature_key`、`ExecutionIdentity` 与输入。Session 不选择 Agent、不保存图或版本。

GA 将可安全展示的 ProductEvent 写入 `chat_events`，再发布 Redis live；Session 负责查询、
replay、AG-UI/SSE 投影。raw thinking、工具内部参数、subagent 控制和 sandbox 事实不进入产品事件。

## 明确不做

```text
Workflow / flow mode / WorkflowCompiler / CompiledGraph
自定义 router、reply-owner state、WorkItem graph、Session graph binding
Session 侧 runtime policy 或请求级 Agent/Tool/Skill 配方
```
