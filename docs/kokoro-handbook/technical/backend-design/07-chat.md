# kokoro-chat 设计卡（历史独立分仓方案）

状态：**历史独立 Chat 分仓方案**，2026-08-22。该卡记录 SQL-first 阶段把 Conversation/Message/Run projection 独立为
`kokoro-chat` 的提议；它不是当前 Feature-first GA 架构的目标 owner。

当前目标收敛为一个产品 Session runtime：`kokoro-session` 持有 Session admission、产品消息/run projection、HITL control、
snapshot/SSE 与 lifecycle；GA 持有 execution/checkpoint/HITL/effects；Session 不读取 GA checkpoint。权威入口：

- [Session 生命周期](../../business-flows/session-lifecycle.md)
- [kokoro-session 模块设计](../../modules/kokoro-session.md)
- [36 GA 整体 Agent 技术方案](../36-ga-final-agent-technical-plan.md)
- [38 GA 公共运行契约](../38-ga-public-runtime-contract.md)

```text
Product Session  -> admission / messages / Run projection / ProductEvent projection / SSE / lifecycle
GA               -> RunLedger / AgentState checkpoint / workbench / HITL execution / effects
```

因此，不新增 `kokoro-chat` runtime、Chat-to-Session 双写、Conversation/Run 的第二 writer，或一套与 Session 并行的
projection/control/outbox。当前 Root `kokoro-chat` Proto consumer 仅是 V1 generated closure；目标公共契约将它
收敛为 Session/GA 的唯一公开 consumer closure，再删除旧 reader/writer。

旧 SQL 表、Proto 和实施计划只用于历史取证：它们既不定义 Session Agent 选择、CapabilitySnapshot，也不覆盖
FeatureKey、DeepAgents 原生 state、single-active-Run 或 safe ProductEvent 的目标决策。
