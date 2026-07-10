# Agent 文档地图

本页只解决一件事：把 `kokoro-agent` 相关文档按阅读顺序收拢，避免你在
多个页面之间来回跳。

## 先读顺序

```text
0. 19-current-runtime-capability-review-plan（当前 runtime/capability 主线）
1. ADR-004 agent 编排边界
2. 11-agent-session-web-v1-runtime
3. 03-agent-architecture
4. 12-agent-hitl-tool-interception
5. modules/kokoro-agent
6. business-flows/agent-handoff
```

## 每份文档负责什么

### ADR-004

定义三仓边界，回答“agent 编排应该发生在哪里，不应该发生在哪里”。

### 19-current-runtime-capability-review-plan

当前 namespace / capability / skills / MCP / context / sandbox / artifact 主线的人类评审入口。

### 11-agent-session-web-v1-runtime

定义三仓 V1 的正式运行时，回答“agent / session / web 如何连起来”。

### 03-agent-architecture

定义 agent 子仓内部结构，回答“kokoro-agent 的目录、执行链路、职责边界怎么放”。

### 12-agent-hitl-tool-interception

定义工具拦截、HITL、ask_user_question、暂停点和 resume，回答“哪些动作需要暂停、如何恢复”。

### modules/kokoro-agent

定义 agent 子仓的完整技术方案，回答“这个仓到底拥有什么、不拥有什么、如何实现”。

### business-flows/agent-handoff

定义一次 run 内的能力编排链路，回答“主 agent 如何调用 skill / MCP / subagent / tool”。

## 你看文档时的判断方式

```text
只想知道边界和原则 -> 看 ADR-004。
只想知道三仓总线 -> 看 11。
只想知道 agent 仓内部怎么组织 -> 看 03 和 modules/kokoro-agent。
只想知道 HITL / 工具拦截 -> 看 12。
只想知道业务编排和能力接入 -> 看 agent-handoff。
```

## 不要再把这些文档当成不同版本

它们不是互相竞争的方案，而是同一套方案的不同层次：

```text
ADR = 决策
11   = 三仓正式运行时
03   = agent 仓结构
12   = HITL 专项
module = agent 仓完整说明
flow   = agent 业务编排链路
```
