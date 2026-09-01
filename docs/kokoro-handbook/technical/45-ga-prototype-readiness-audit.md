# 45. GA 原型就绪审计

状态：当前源码与首发闭环审计，2026-08-27。

总体对象以 [42 GA 核心架构](42-ga-core-architecture.md) 和
[36 GA Agent 最终技术方案](36-ga-final-agent-technical-plan.md) 为准。GA 直接以目标契约和
DeepAgents 运行路径实现，不保留平行入口或第二套状态系统。

## 1. 必须成立的闭环

```text
Root LaunchRunRequest(feature_key, message_id, content, ExecutionIdentity)
  -> Redis internal envelope input={message_id,content}
  -> Redis worker
  -> RunLedger claim
  -> FeatureCatalog.get(feature_key)
  -> AgentFactory
  -> create_deep_agent / official Swarm
  -> native checkpoint + GA chat facts
  -> chat_events durable write -> Redis live -> Session/AG-UI
```

- Root/Session 只提交受信 Feature 和身份，不提交 namespace、thread、Agent、Skill、MCP、工具
  或 graph 配方。
- GA 从 `ExecutionIdentity` 派生内部 `RuntimeNamespace`；namespace 不上 wire。
- DeepAgents/LangGraph 原生 state 与 checkpoint 由框架拥有；GA 的 RunLedger、聊天事实和
  workbench 各自独立。
- Capability、Storage、Studio、Billing 只在 Feature 声明的操作需要时调用。

## 2. 当前代码的收口点

| 位置 | 必须达到的事实 |
|---|---|
| `agents/` | 每个文件只定义一个完整 Agent，不定义角色或运行 loop。 |
| `features/` | 只声明 Agent 组合、入口和 peer handoff；`music` 可单独运行。 |
| `agent_factory.py` | 是唯一构造入口；单 Agent 直接调用 `create_deep_agent`，peer 只通过官方 Swarm。 |
| `execution/` | 只消费 DeepAgents 的公开调用/事件/状态接口，不包装自有 state。 |
| `worker/` | 只负责 Redis、claim、lease、recovery、control 和事件投影。 |
| `skills/` / `clients/` | GA default/find/load 与 Capability/Storage public contract 边界清晰，外部 client 可缺席。 |
| `chat_messages` / `chat_events` | 用户历史与实时 replay 的 GA 事实；不修改 LangChain checkpoint 表。 |

## 3. 验收场景

1. `chat` 和 `music` 单 Agent Feature 可直接构造并运行。
2. `music_chat` 只在声明 handoff 时构造官方 Swarm。
3. native subagent 的后台失败不会复制 Session 或 parent Run 终态。
4. 同一 Session 只有前一 Run terminal 后才继续同一 native checkpoint；fork 使用新的 state。
5. Capability/Storage/Studio/Billing 不可用时，不依赖它们的 Feature 仍能运行。
6. GA 先落 `chat_events` 再发 Redis；Redis 丢失可按 seq replay。
7. provider accepted invocation 以稳定 `invocation_id` 结算，token 不作为用户计费单位。

## 4. 禁止项

不新增第二套产品装配对象、自有 Graph/State wrapper、Session 配置对象或 Agent 版本机制；
`deps`、`compiler/`、`runtime/` 或自定义 handoff router。可视化 Builder 只生成已有
Agent/Feature 声明，仍由同一个 AgentFactory 构造。

## 5. Capability snapshot prototype boundary

`kokoro-capability/src/modules/runtime-snapshot/` 当前不存在；`ResolveRuntimeSnapshot` 仅作为
Root 迁移期兼容 descriptor 保留，Capability 不挂载该 RPC，也不新增 snapshot writer。当前方案
没有 target snapshot、revision、Session binding 或一次性运行配方；GA 通过 Capability 的
attested source-read contract 获取当前可见 Skill/MCP 事实，并在 GA 自己的 Run 边界内装配。
