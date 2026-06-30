# General Chat 链路

## 目标

用户在通用对话里发一条消息，系统稳定地完成一次 agent run：选模型/技能/工具、执行、流式产出、落库、可刷新恢复，并按实际用量扣费。

## 参与模块

```text
kokoro-web      发消息、消费 SSE、reducer 折叠 thread。
kokoro-session  建 conversation/active run、组装 manifest、归一化事件、持久化、发 SSE。
kokoro-agent    按 manifest 执行 LangChain/LangGraph，产出原始执行事件。
kokoro-model    解析可用 model binding。
kokoro-credit   quote / hold / capture / release。
```

## 前置条件

```text
SiteContext 已解析（siteId/userId/workspaceId）。
能力可用（entitlement 允许 general.chat）。
余额充足。
```

## 主流程

```text
1. web POST 用户消息到 session；session 建/取 Conversation，落 user Message，创建唯一 active run。
2. session 组装 AgentRunInput（site/user/workspace/session/run 身份、context、
   model runtime、permission mode、backend policy、skills、MCP servers/tools、
   内置工具、trace context），
   写 run.request 到 Redis（kokoro:runs:requests）。
3. agent 取请求，credit.quote -> credit.hold（idempotencyKey）。
4. agent model.resolve（按 SiteModelPolicy），调用 LiteLLM 或 direct provider。
5. agent 产出原始执行事件（message/tool/todo/subagent/thinking/run.*）到 kokoro:run:{run_id}:events。
6. session strict parse + normalize + 去重，写 Mongo（messages/runs/session_events），
   经 kokoro:session:{id}:live 经 SSE 推给 web。
7. run 结束按实际用量 credit.capture，写 ledger + usage；run.completed 终态。
8. web reducer 折叠为 assistant 消息和活动流。
```

## 异常流程

```text
余额不足        hold 失败 -> 402，提示充值。
模型未授权      resolve 空 -> 403。
provider 失败    credit.release 释放冻结，run.failed。
超时            hold 过期自动释放，run.completed(status=timeout)。
断线/刷新       web 重新 GET /sessions/:id snapshot，再 attach active run 续收。
```

## 数据变化

```text
Conversation / Message      Mongo。
AgentRun / session_events   Mongo（eventId 去重，segment_id 分段）。
CreditHold / LedgerEntry / UsageRecord   MySQL（见 credit-reserve-commit-refund）。
```

## 幂等和一致性

```text
requestId        全链路追踪。
idempotencyKey   hold/capture/release。
eventId          会话事件去重锚点，不承担排序。
排序真源         session 写 Mongo 的追加顺序 + SSE 单连接发送顺序。
单 active run     同 conversation 同时只允许一个 active run。
```

## 用户可见结果

```text
流式 assistant 回复、工具/子代理活动流（默认折叠）、artifact card。
失败转产品语言错误并允许重试。
余额按实际用量减少，usage 可见。
```

## 验收标准

```text
30 秒内可开始第一轮有效任务。
刷新/断线后能恢复并继续 active run。
扣费按实际用量、幂等、可审计。
浏览器不直接消费 agent 原始事件。
```

相关：[credit-reserve-commit-refund](credit-reserve-commit-refund.md)、[model-resolution](model-resolution.md)、[agent-handoff](agent-handoff.md)、[../technical/03-agent-architecture.md](../technical/03-agent-architecture.md)、[../technical/04-session-architecture.md](../technical/04-session-architecture.md)。
