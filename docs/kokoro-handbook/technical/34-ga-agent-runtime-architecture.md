# 34. GA Agent Runtime

状态：42/36 的执行细节，2026-08-27。

## 1. Runtime 归属

DeepAgents 是 GA 的 Agent runtime，拥有 agent loop、native state、subagent、middleware、
interrupt 和 checkpoint。GA 只负责 worker、RunLedger、产品聊天事实、工具策略、workbench 和
外部 public-contract client。

```text
Feature -> AgentFactory -> create_deep_agent
Feature -> AgentFactory -> official create_swarm
```

不定义 GA 自有 `runtime/`、`compiler/`、Graph 或 State wrapper。

## 2. 启动与恢复

```text
LaunchRunRequest
  -> Redis worker
  -> RunLedger claim
  -> FeatureCatalog(feature_key)
  -> AgentFactory.build(...)
  -> native Agent invoke/resume
```

worker 启动时创建 AgentFactory，并把模型、checkpointer、RunLedger、workbench 和部署注入的可选 public clients
放进 Factory 实例。标准 CLI 不直读 owner 私库；Run 只提交输入，不重新选择 Agent 或组装图。叶子模块不接收整个 WorkerServices，只接收自身窄参数。

同一 Session 的普通新消息在上一 Run terminal 后继续同一 native checkpoint；fork 才建立新的
Session/thread/state。`ExecutionIdentity` 的 `tenant_ref + subject` 用于稳定 namespace 派生；完整 identity 继续用于入口授权、审计和计费，actor/assertion 轮换不改变隔离键。

## 3. 状态与聊天

- 单 Agent/native subagent 使用 DeepAgents 原生 state。
- Swarm 使用 official `SwarmState`；`active_agent` 只属于该官方 state。
- GA 不继承或包装 DeepAgents 原生 state，也不定义自有 state。
- LangChain checkpoint/native IDs 与 GA `chat_messages`、`chat_events` IDs 分离。
- GA 持久化 `chat_events`；Session 经 Root Chat query boundary 负责查询、replay
  和 AG-UI/SSE。GA 不把 internal safe envelope 写入 Session 已有 browser-live stream。

## 4. Workbench 与外部 owner

Agent 声明的 Skill 由 Capability client 解析，并通过只读 backend route 交给 DeepAgents 原生
SkillsMiddleware / `read_file`；MCP/Storage/Studio/Billing 通过各自 public contract。`S3Workspace` 是 GA workbench 的 S3-compatible adapter，MinIO 只是
当前实现，不拥有 Artifact 生命周期。
