# 服务通信技术方案

## 通信类型

```text
HTTP internal API   平台服务之间的初期调用方式。
SSE                 session -> browser 的实时输出。
Redis Stream/Live Bus  agent -> session、session 内部实时广播。
Provider API        model/music/video/image/payment 等第三方调用。
Webhook             支付和生成 provider 回调。
```

## SiteContext 传递

入口层先解析 `SiteContext`，业务子仓只消费 siteId，不自己从 host 推断站点：

```text
x-kokoro-site-id
x-kokoro-site-key
x-kokoro-app-key
x-kokoro-surface
x-kokoro-request-id
x-kokoro-user-id
x-kokoro-workspace-id
```

## requestId 和 idempotencyKey

```text
requestId        链路追踪和日志关联。
idempotencyKey   防止重复扣费、重复下单、重复发放、重复处理 webhook。
```

必须有 idempotencyKey 的场景：

```text
payment order create / payment event process / credit grant /
credit hold / credit commit·release / job create / provider callback process
```

## Agent 事件链路

```text
kokoro-agent   产出原始 AgentEvent（event / request_id / timestamp / data）。
kokoro-session strict parse、normalize、去重、DB-first 持久化、发布 SSE。
kokoro-web     strict parse、eventId 去重、append-order reducer、渲染 thread 和活动流。
```

```text
eventId 是去重锚点，不承担排序。
AgentEvent request_id 当前等同 runId，不是排序字段。
agent 原始终态是 agent_done / agent_error。
session/browser-facing 终态是 run.completed / run.failed。
cancelled/timeout 是 run.completed.status，不是独立 event kind。
浏览器不直接消费 agent 原始事件。
排序真源是 session 写入 Mongo 的追加顺序和 SSE 单连接发送顺序。
P0：session agent_run_input manifest 与 agent Python RunRequest 必须合流。
```

详见 [agent 架构](03-agent-architecture.md)、
[session 架构](04-session-architecture.md) 和
[三仓 V1 运行时技术方案](11-agent-session-web-v1-runtime.md)。

## Platform API

```text
kokoro-site:4201  kokoro-user:4211  kokoro-model:4221  kokoro-credit:4231  kokoro-payment:4241
```

```text
初期 HTTP 足够，后续可升级 RPC，但业务边界不变。
不跨模块直接读表。
不把共享类型做成 kokoro-contracts。
```

## 错误处理

```text
错误响应至少含：code、message、requestId、details?。
用户可见错误转换为产品语言。
内部错误不暴露 provider secret、stack、SQL。
```

## 超时和重试

```text
可重试：provider 临时失败、network timeout、webhook 重放、session relay 重投。
不可盲目重试：payment capture、credit commit、side-effect tool。
所有重试写操作必须依赖 idempotencyKey。
```

相关：[deployment](08-deployment.md)、[observability](10-observability.md)。
