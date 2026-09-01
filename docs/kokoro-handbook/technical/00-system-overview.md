# Kokoro 系统总览

状态：目标架构首读页，2026-08-27。

详细 Agent 方案以 [42 GA 核心架构](42-ga-core-architecture.md) 和
[36 GA 技术方案](36-ga-final-agent-technical-plan.md) 为准；Root API/AIP 以
[38 公共运行契约](38-ga-public-runtime-contract.md) 和根仓 `contract/` 为准。

## 一句话

Kokoro 是统一产品入口和一个自闭环 GA 执行底座。用户进入 `Feature`，Feature 组装一个或多个
完整 `Agent`，GA 直接调用 DeepAgents；需要会话级 peer 接手时使用官方 `langgraph-swarm`。
Capability、Storage、Studio、Billing 是按需调用的外部 owner。

```text
Feature
  -> AgentFactory
  -> deepagents.create_deep_agent(...)
     或每个 peer create_deep_agent(...) -> official langgraph-swarm
  -> native state/checkpoint
  -> GA RunLedger + workbench + chat_messages/chat_events
  -> Session Chat API / AG-UI / SSE
```

## 六条规则

1. 用户选择 Feature，不选择 Agent 配方；Session 不保存 Agent、成员、图、版本或能力快照。
2. Feature 是唯一业务组装入口，不增加 Role、Team 或第二个编排对象。
3. DeepAgents 拥有 loop、state、subagent、interrupt 和 checkpoint；GA 不复制这些能力。
4. 同一 Session 只有上一 Run terminal 后的新消息才继续同一 native checkpoint；fork 才建立新 Session/thread/state。
5. GA 默认 Skill 与 `find_skills/load_skill` 由 GA 提供；用户/项目/session Skill CRUD 由 Capability，
   package bytes/Artifact 生命周期由 Storage 提供。
6. GA 持久化 `chat_messages` 和 `chat_events`；Redis 只做实时传输，LangChain checkpoint 完全独立。

## Owner 边界

| Owner | 负责 | 不负责 |
|---|---|---|
| App/System | 产品入口、Feature exposure、输入输出、权限、价格与交付定义 | Agent loop、checkpoint、Run 事实 |
| Session | ProductSession、鉴权、Chat API、历史查询、replay、AG-UI/SSE | Agent 组装、native state、GA 聊天 canonical facts |
| GA | Agent/Feature 声明、AgentFactory、RunLedger、workbench、HITL、chat facts、ProductEvent | 用户主数据、Artifact/Job/Billing owner |
| DeepAgents/LangGraph/Swarm | 原生 Agent 执行、state、checkpoint、interrupt、peer handoff | 产品权限、外部 owner 数据 |
| Capability/Storage/Studio/Billing | 各自 public contract 与业务事实 | GA native state、Session、Feature |

## 从入口到出口

```text
1. App/Session 根据站点和 IAM 结果选择可信 feature_key。
2. Session 生成本次 ExecutionIdentity，提交 session_id、输入和 opaque AssetRef。
3. Root LaunchRunRequest 进入 GA Redis；请求不携带 namespace、thread、Agent、Skill、MCP 或图配方。
4. GA 派生内部 RuntimeNamespace，写 RunLedger claim/lease/thread gate。
5. FeatureCatalog 取出内置 Feature；AgentFactory 按其声明构造 DeepAgents native runnable。
6. DeepAgents 或官方 Swarm 执行；GA 记录 invocation/effect/terminal facts。
7. 用户可见结果写入 chat_messages/chat_events，再发布 Redis live event。
8. Session 查询/replay 并投影 AG-UI/SSE；浏览器断线不影响 GA Run。
```

## Feature 与 Agent

```text
chat       -> general Agent
music      -> music Agent
music_chat -> general Agent + music Agent + handoff edges
```

Music Agent 可单独对外，也可被组合 Feature 复用。无需 composer、arranger、reviewer 等角色文件。
一个 Agent 需要后台隔离工作时使用 DeepAgents native subagent；不同 Agent 接管同一会话时才使用官方 Swarm。

## 状态、身份与存储

```text
DeepAgents/LangGraph checkpoint -> native state / messages / interrupt
GA RunLedger                   -> claim / lease / control / invocation / effect / terminal
GA chat_messages               -> 用户可见历史
GA chat_events                 -> 用户可见实时与 replay 事实
Redis                          -> live transport
```

`ExecutionIdentity(tenant_ref, actor, subject, identity_assertion_ref)` 用于授权、审计和计费归属；GA
从它派生内部 `RuntimeNamespace`。caller 永远不传 namespace 或 LangGraph `thread_id`。

LangChain 的 `Message.id`、`checkpoint_id`、`tool_call_id` 与 GA 的 `chat_message_id`、`chat_event_id`
分离。GA 不创建 `conversation_messages`、`run_events` 或独立 `event_outbox`。

## Skill、Storage 与 Workbench

```text
GA default Skill + find/load -> GA
用户/项目/session Skill   -> Capability public contract
package bytes / Artifact   -> Storage public contract
S3Workspace               -> GA Workbench 的 S3-compatible adapter
```

S3Workspace 当前可接 MinIO，后续可切换 AWS S3、Ceph RGW 等兼容实现；它不拥有 Storage Artifact。
外部 client 暂不可用时，不依赖该 client 的 Feature 仍可执行和恢复。

## 部署与可视化组装

Compose/Kubernetes 只注入 Redis、checkpointer、RunLedger、model、workbench、secret handle 和可选
public clients；不决定 Feature、Agent 或 handoff 关系。

未来可视化 Builder 只生成同一套 `Agent`/`Feature` 声明，交给同一个 AgentFactory；Builder 不成为
运行时，不把图、成员、版本或绑定写入 Session。
