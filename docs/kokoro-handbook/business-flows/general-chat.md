# General Chat 链路

状态：当前 Feature-first 产品链路，2026-08-22。整体架构见
[36 GA 总体方案](../technical/36-ga-final-agent-technical-plan.md)、
[37 统一入口与产品架构](../technical/37-product-experience-agent-studio-architecture.md) 与
[38 公共运行契约](../technical/38-ga-public-runtime-contract.md)。

## 产品语义

General Chat 是 Chat App 的 `FEATURE_KEY_GENERAL_ASSIST` Feature。用户选择“聊天”这个产品功能，不选择 `general`、`music`、
`creative` 等 Agent 名；当前 `FEATURE_KEY_GENERAL_ASSIST` 是只包含 `general` Agent 的静态 Feature；需要隔离工作时使用 DeepAgents native subagent。

## 主流程

```text
1. Browser/Entry 选择 Chat App 的 FEATURE_KEY_GENERAL_ASSIST Feature，提交消息、附件和可选模型标签。
2. Session 校验 App/Feature/权限/计费资格；创建或读取 Session(feature_key=FEATURE_KEY_GENERAL_ASSIST)。
3. Session 落用户消息、assistant placeholder、run admission，并投递最小 Root command。
4. GA ingress 规范化为 canonical RunRequest；ledger claim 后取得 worker-local Feature 与 checkpoint。
5. GA 从 FeatureCatalog 取得 `general` Agent，由 DeepAgents native runtime 继续；其后台工作只使用 DeepAgents native subagent，不写自有 `active_agent`。
6. General Assistant 按 Agent/Feature 的固定工具与 Skill/MCP grant 调用能力或 Studio command；`FEATURE_KEY_GENERAL_ASSIST` 不发生 Swarm handoff。
7. GA 将安全 ProductEvent 写入 `chat_events` 并发布 Redis live；Session 查询/replay 后投影消息、活动、HITL、Job/Artifact card 与 terminal，再 SSE 给 Browser。
8. provider 接受的每次 ModelInvocation 以 invocation_id 结算；Studio Job 与 Artifact 各自走 owner 的生命周期。
```

## Chat 内组合专业能力

```text
用户：为新品发布准备文案、海报和配乐
  -> General Assistant 使用 DeepAgents native subagent 完成文案、视觉和音乐辅助工作
  -> 已获允许的 Image / Music task 通过 Studio public command 创建 Job
  -> Job / Artifact 状态经 GA event -> Session card 返回
  -> General Assistant 汇总结果
```

这些 target 是 private task，不是 Session Agent 或 Swarm peer；它们不生成 `active_agent`，也不直接写 SSE。仍然只有
`FEATURE_KEY_GENERAL_ASSIST` 的同一 GA native conversation state；用户打开完整 Music Studio 时才创建 `FEATURE_KEY_MUSIC_CREATE` Feature 的新 Session/thread。

## 恢复、HITL 与 fork

- 前一 Run terminal 后的普通后续消息继续同一 checkpoint；active Run 的普通文本返回 `run_active`，不入队、不写 checkpoint。只有 matching HITL/cancel 作为同一 `run_id` 的 control，Session 不重新选 Agent 或重建图。
- HITL control 由 Session 验证和投递；GA 使用同一 Run 的 ExecutionIdentity 与同一 checkpoint 恢复。
- fork 创建固定同一 `feature_key=FEATURE_KEY_GENERAL_ASSIST` 与 immutable tenant + subject 的 target Session。GA 的 `ForkConversation` 只从
  source terminal Run 提取可展示 user/final-assistant text 为一次性 private `ConversationSeed`；首个 target Run 写入 fresh state。它不复制
  `active_agent`、native messages、workbench、动态 Skill、执行记录或 graph/checkpoint，首次 Launch 重新受理 actor/assertion。
- Browser 断线后从 Session snapshot/SSE 恢复；GA ledger/checkpoint 的恢复不依赖 Browser 在线。

## 计费与失败

| 情况 | 结果 |
|---|---|
| provider 接受模型请求 | 以 `invocation_id` 计一次；reconciliation/recovery/outbox replay 不双扣。 |
| dynamic Skill/Asset 不可用 | default-only Chat 继续；该工具返回可解释失败。 |
| Studio Job 失败 | Job 自己终态；GA 返回 Job/Artifact 状态，不冒充完成。 |
| Feature/Agent 装配失败 | 模型调用前 terminal；不产生外部 effect。 |
| V1 optional `S3Archiver` archive 失败 | sandbox 本地写结果保留；不等同 Artifact 失败，也不是 target durable-workbench recovery。 |

## 验收

```text
Chat UI 不提交 Agent、Skill、MCP、graph 或 provider 配方。
Session DB 没有 Agent/runtime snapshot；GA `ConversationState` 是唯一 Agent conversation state。
FEATURE_KEY_GENERAL_ASSIST 只使用静态 Agent 声明与 native subagent；外部能力不超过 Agent/Feature/RunScope 交集。
断线、HITL、worker restart、effect replay 与 billing invocation 都可幂等恢复。
完整 Music Studio 走新 Feature Session，不污染原 Chat thread。
```
