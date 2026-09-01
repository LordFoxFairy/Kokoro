# Agent 文档地图

状态：2026-08-27。

本页只解决一个问题：评审 `kokoro-agent` 时，哪些文档是当前架构，哪些只是专题参考。整体
架构不需要拼读多份过程稿。

## 整体架构只读两份

```text
1. 42-ga-core-architecture.md          GA 闭环底座、Agent/Feature、owner 与目录
2. 36-ga-final-agent-technical-plan.md GA 落地链路、DeepAgents、Swarm、状态、能力与验收
```

这两份已经回答：

- 一个 Music 或 Chat site 如何复用同一个 GA 底座；
- Agent、Feature、AgentFactory 和 Run 分别是什么；
- 为什么 GA 严格使用 DeepAgents；
- 什么时候使用官方 Swarm；
- 为什么 Session 不保存 Agent 配置、版本或绑定；
- 为什么外部请求不携带 namespace、thread、Skill、MCP 或依赖句柄。

## 专题文档

| 主题 | 文档 | 说明 |
|---|---|---|
| Swarm handoff | [ADR-020](../decisions/ADR-020-native-framework-compatibility-and-swarm-adapter.md)、[35](35-ga-langgraph-swarm-architecture.md) | 所有 peer 仍由 DeepAgents 创建，handoff 只走官方 Swarm |
| Capability/Storage | [29](29-capability-storage-runtime-architecture.md)、[33](33-ga-first-skill-runtime-architecture.md) | Skill、MCP、Artifact、S3-compatible Workbench owner 边界 |
| 身份与动态能力 | [38](38-ga-public-runtime-contract.md)、[ADR-022](../decisions/ADR-022-run-execution-attestation-and-dynamic-capability-resolution.md) | ExecutionIdentity、内部 RuntimeNamespace、public contract |
| 事件与交付 | [ADR-016](../decisions/ADR-016-orchestration-policy-and-product-event-projection.md) | ProductEvent、chat_events、Session 投影与回复归属 |
| 长任务与并行 | [40](40-ga-work-profiles-and-bounded-fanout.md) | 仅在真实需求出现时使用 DeepAgents subagent 或官方 LangGraph 原语 |
| 结果质量与评测 | [39](39-ga-evaluation-and-evidence-architecture.md)、[41](41-feature-outcome-contracts-and-quality-gates.md) | Feature 结果、成本和质量门禁 |
| 产品体验 | [37](37-product-experience-agent-studio-architecture.md) | Chat、Music、Studio 和组合 Feature 的产品入口 |
| 当前子仓实现 | `kokoro-agent/docs/agent/architecture.md`、`technical-plan.md` | GA 子仓局部目录、owner、接线和测试 |

专题文档只能细化 42/36，不能新增 Agent 类型或覆盖整体命名。

## 对象字典

```text
Agent        = 完整、可独立运行的 DeepAgents 能力
Feature      = 对外产品能力的 Agent 组装入口
AgentFactory = GA 内部唯一装配器
Run          = 一次调用的生命周期事实
Worker       = Redis 接入与 Run 生命周期进程
```

```text
Feature -> AgentFactory -> create_deep_agent
Feature -> AgentFactory -> create_deep_agent(每个 peer) -> official create_swarm
```

GA 不另定义 Role、Team、Workflow、Graph、State、Router 或第二个编排对象。`music` Agent 既可
作为 `music` Feature 单独运行，也可被组合 Feature 复用。

## 目录裁决

```text
kokoro_agent/
├── agents/          完整 Agent 定义
├── features/        对外 Feature 组装
├── agent_factory.py 唯一装配入口
├── swarm.py         官方 Swarm 薄接线
├── execution/       Run 执行、恢复、HITL、事件
├── worker/          Redis ingress、claim、recovery
├── tools/           GA 固定工具与 middleware
├── skills/          GA 默认 Skill、find/load、workbench mount
├── clients/         Capability/Storage/Studio/Billing/Model 客户端
├── sandbox/         DeepAgents backend、S3-compatible Workspace
├── storage/         RunLedger、LangGraph Store、checkpoint adapter
├── mcp/             MCP 连接与工具接线
├── model/           模型选择与 provider adapter
├── prompts/         静态 prompt 资产
└── observability.py 诊断、metrics、trace
```

禁止新增 `ga/`、`framework/`、`compiler/`、`runtime/`、`ports/`、根目录 `agent.py`、自定义
State/Graph、Binding、Release/Version 或请求级 `deps`。

## 阅读规则

```text
整体 Agent 架构             -> 42 + 36
DeepAgents / Swarm           -> ADR-020 + 35
Feature / Music / Studio     -> 37 + 42
Skill / MCP / Storage        -> 29 + 33 + 38
身份 / namespace / Billing   -> 38 + ADR-022
事件 / Chat / AG-UI          -> ADR-016 + 38
当前代码职责                -> kokoro-agent/docs/agent/* + modules/kokoro-agent
```

历史材料仅用于考古，不用于生成新目录、请求字段或 Agent 运行语义。
