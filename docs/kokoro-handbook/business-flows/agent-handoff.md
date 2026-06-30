# Agent Handoff 链路

## 目标

让通用 Agent 在一次 run 内编排专业能力（skill、MCP tool、内置工具、
子代理），并保持上下文、归属和扣费一致。handoff 是 agent 编排能力，
不是前端跳转。

多期 agent 业务编排模型见
[Agent 业务编排多期技术方案](../technical/13-agent-business-orchestration-roadmap.md)。

## 参与模块

```text
kokoro-agent    主 agent 判定并调用子能力，承载编排和事件。
kokoro-session  归一化 tool/subagent 事件，保留 subagent 归属。
kokoro-credit   子调用的 quote/hold/capture。
kokoro-model    子调用涉及 AI 时解析模型。
```

## 前置条件

```text
主 run 已启动，AgentRunInput 已就绪。
被调用的 skill/MCP server/tool 已在 manifest 启用且权限允许。
业务 capability 已在 AgentRunInput.capabilities 中声明。
```

## 主流程

```text
1. 主 agent 推理判定任务需要某能力（搜索/工具/子代理/专业 agent）。
2. 发起 capability invocation，继承上下文：siteId/userId/workspaceId/sessionId/runId、
   jobId、credit context、artifact/project context。
3. 若子调用涉及 AI：重复 credit.quote -> hold -> model.resolve -> provider -> capture；
   子调用 usage 通过 jobId 归并到主任务。
4. 产出事件：subagent.* 通道承载子代理输出；tool 事件携带 subagent_id 以保留归属，
   不被归一化为顶层 tool（否则归属丢失）。
5. 子调用返回结果，主 agent 继续推理或调用下一能力。
6. 全部完成，主 run 终态 run.completed。
```

专业能力不直接让 agent 写业务库。agent 只能调用 capability adapter；
job、artifact、credit、model 仍由 owning service 持有。

## 异常流程

```text
工具/子代理失败    该步标记 failed，主 agent 可重试或降级。
预算不足           子调用 hold 失败 -> release，返回产品语言错误。
重复调用           tool 级 idempotencyKey 命中 -> 返回已有结果，不重复扣费。
```

## 数据变化

```text
session_events    新增 tool.* / subagent.* 事件（Mongo，带 subagent_id）。
UsageRecord       子调用记录，jobId = 主任务，idempotencyKey = 子调用键（MySQL）。
LedgerEntry       子调用 capture（MySQL）。
```

## 幂等和一致性

```text
jobId            主任务关联，子 usage 归并锚点。
idempotencyKey   每个子调用独立，防重复 quote/hold/capture。
归属             subagent_id 必须从 agent 透传到 session 再到 web，不在归一化层丢弃。
```

## 用户可见结果

```text
活动流中子代理/工具步骤挂在对应 subagent 节点下，而非顶层。
失败步骤可见且可重试。
扣费合并到本次任务总用量。
```

## 验收标准

```text
子代理内的工具调用在 web 上归属正确，不表现为顶层工具。
子调用失败只回滚自身冻结，不误扣。
一次 run 内可编排多能力且共享 credit/artifact 上下文。
```

相关：[general-chat](general-chat.md)、
[general-chat-to-music-entry](general-chat-to-music-entry.md)、
[credit-reserve-commit-refund](credit-reserve-commit-refund.md)、
[../decisions/ADR-004-agent-orchestration.md](../decisions/ADR-004-agent-orchestration.md)、
[../modules/kokoro-agent.md](../modules/kokoro-agent.md)。
