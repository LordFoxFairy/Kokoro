# 44. GA Agent 架构外部校准

状态：设计校准记录，整体结论以 [42](42-ga-core-architecture.md) 和
[36](36-ga-final-agent-technical-plan.md) 为准，2026-08-27。

本页只提炼 DeepAgents、LangGraph、Claude Code、Manus、ChatGPT 和 OpenAI Agents SDK 中值得
借鉴的产品边界，不把它们的目录、session log、plugin runtime 或 task protocol 搬进 GA。

## 1. 吸收的共同原则

| 外部产品常见做法 | GA 采用方式 |
|---|---|
| Agent 是完整可运行能力，产品能力可以组合多个 Agent | `agents/` 定义完整 Agent，`features/` 负责组合 |
| Agent loop、state、checkpoint 由框架提供 | 直接使用 DeepAgents，不重复实现 runtime/state |
| Handoff 与后台 subagent 是两种不同协作语义 | peer 会话交接使用 official Swarm；后台隔离工作使用 DeepAgents native subagent |
| Skills/MCP/hooks 是不同扩展面 | GA Skill、MCP、工具策略和 public client 分开管理 |
| 权限、sandbox、审批分层 | GA 工具策略 + native interrupt + sandbox，各自只做一件事 |
| 长上下文使用渐进加载和工作区 | GA `find_skills/load_skill` + Workbench；不建第二份消息状态 |
| 事件与历史需要断线恢复 | GA `chat_events` durable/replay，Redis 只做实时传输 |
| Builder 只负责 authoring，不拥有 runtime | 未来 Builder 生成同一套 Feature/Agent 声明，由 AgentFactory 组装 |

## 2. 明确不采用

- 不复制 Claude Code 的本地 JSONL transcript、plugin marketplace、agent team 或第二个 scheduler。
- 不复制 Manus/ChatGPT 的产品会话、项目记忆和 UI 状态到 GA。
- 不复制 DeepSeek Harness 的 agent-loop/inbox、mailbox、task board 或 plugin tree。
- 不把外部框架的 外部框架的编排对象 变成 GA 根对象；Feature 已经是业务组装层。
- 不把 provider model preference、Agent 选择、Skill/MCP 配方或 namespace 变成 Session/Run 参数。

## 3. 对 Kokoro 的直接结论

```text
Feature -> Agent(s) -> AgentFactory -> DeepAgents / official Swarm -> Run
```

Factory 实例在 worker 启动时持有共享服务；外部 API 只传 `feature_key`、输入和受信身份。
单 Agent 直接走 `create_deep_agent`；只有 peer handoff 才调用 `create_swarm`。这样既保留了
Claude Code/Manus 的“一个能力快速组装”和“能力可复用”，又不偏离 DeepAgents 原生执行路径。
