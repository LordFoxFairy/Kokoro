# 39. GA Agent 评测与运行证据

状态：当前评测方案，2026-08-27。

本页只说明如何验证 GA 的真实 Agent/Feature 链路，不引入独立的评测 runtime。总架构以
[42 GA 核心架构](42-ga-core-architecture.md) 为准。

## 1. 评测对象

```text
EvalCase(feature_key, input, fixture_identity, expected_product_events)
  -> 同一 FeatureCatalog
  -> 同一 AgentFactory
  -> DeepAgents native Agent / official Swarm
  -> 同一事件、RunLedger、checkpoint 与 client 边界
```

评测只使用脱敏 fixture，不读取生产 Session、checkpoint、账本或外部私库。测试 profile 可以
替换模型和 public clients，但不能替换 Agent loop、state、事件投影或恢复路径。

## 2. 证据分层

| 证据 | owner | 内容 |
|---|---|---|
| Agent/Feature 结果 | GA evaluation | 输出质量、工具选择、handoff、native subagent 结果 |
| Run 事实 | GA RunLedger | claim、lease、control、effect、invocation、terminal |
| 产品事件 | GA `chat_events` | 安全的 delta、activity、approval、delivery、terminal |
| 用户历史 | GA `chat_messages` | canonical assistant/user 消息 |
| 框架状态 | DeepAgents/LangGraph checkpoint | 原生 messages、interrupt、subagent 或 `SwarmState` |
| 外部结果 | Capability/Storage/Studio/Billing receipt | public contract 的幂等回执 |

框架 raw event、prompt、secret、sandbox 路径、provider 响应和内部 tool 参数不直接进入产品
事件或评测报告。

## 3. 必测矩阵

### Agent 与 Feature

- `chat`、`music` 单 Agent 走 `create_deep_agent`。
- 组合 Feature 只复用已有 Agent；peer handoff 走官方 `langgraph_swarm`。
- Agent 声明的 Skill/MCP 缺失时在构造前明确失败，不静默换能力。
- Feature/Agent 不接受 namespace、thread、graph、版本、binding 或 `deps` 参数。

### Run 与恢复

- 同一 Session 的普通新消息仅在前一 Run terminal 后继续同一 native checkpoint。
- fork 创建新 Session/thread/state；运行中普通文本不创建第二个 Run。
- HITL resume 必须匹配当前 native interrupt；cancel、lease reclaim 和重复消息保持幂等。
- worker 重启后只恢复已有 checkpoint/RunLedger，不重复 provider invocation 或外部 effect。

### 能力和副作用

- GA default Skill、`find_skills/load_skill` 在 Capability/Storage 不可用时仍能支持不依赖外部能力
  的 Feature。
- 外部 Skill/MCP/Storage/Studio 调用只通过对应 public client，并验证 owner 回执。
- effect tool 经过审批、journal 和恢复策略；失败不会产生重复副作用。
- S3-compatible Workbench 只存 GA 工作文件；Artifact 仍由 Storage owner 管理。

### 事件、交付和计费

- `chat_events` 先 durable 写入，再发布 Redis；断线可按 seq replay。
- `chat_messages` 只保存用户可见历史；LangChain message/checkpoint ID 不映射为产品 ID。
- Studio Job 可同时投影 direct view 与 session card，迟到 link 只合并同一 JobRef 卡片。
- provider accepted invocation 使用稳定 `invocation_id` 幂等结算；token 仅用于上下文和限额。

## 4. 质量门

每个新增 Agent/Feature 必须通过：

1. 静态声明校验（key、入口、handoff、工具和必需能力）；
2. DeepAgents 构造与 native state/checkpoint smoke test；
3. tool policy、HITL、subagent/handoff 和失败恢复测试；
4. chat history/event replay 与 AG-UI 投影测试；
5. 外部 client 缺席、超时、重复回执和 owner 拒绝测试；
6. lint、类型、契约生成和跨仓集成门禁。

评测结果只决定该 Agent/Feature 是否进入 worker-local catalog；运行中的 Session、checkpoint
和 Run 不被评测或 Builder 改写。

## 5. 禁止项

不创建第二套 prompt runner、Agent loop、state、scheduler、事件表或编排对象；不以评测分数、
模型偏好或外部 client 状态修改用户 Session 的 Feature 选择。
