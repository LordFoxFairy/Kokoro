# kokoro-web 技术方案

本文只约束 `kokoro-web` 子仓。三仓总链路见
[Agent / Session / Web V1 运行时技术方案](../technical/11-agent-session-web-v1-runtime.md)，
聊天链路见
[Agent / Session / Web 通用聊天运行链路](../business-flows/agent-session-web-general-chat-runtime.md)。

## 定位

`kokoro-web` 是三仓运行时的浏览器界面层。它负责聊天 UI、composer、
SSE 消费、agent activity 展示、HITL 控件和本地 UI 缓存。

它是 session facts 的消费者，不是聊天消息、run 状态或 session events 的权威事实源。

## 当前实现状态

已实现：

```text
Next.js 聊天壳。
POST /sessions/:sessionId/messages 启动 live run。
EventSource GET /sessions/:sessionId/stream。
transport event Zod strict parse。
render event mapper。
SessionStreamState reducer。
eventId 去重。
stepsByRun append-order 渲染。
thinking / tool / todo / subagent / text 展示。
HITL approve/reject/cancel UI。
local simulator fallback。
localStorage conversation store。
reattachLiveSession：刷新后直接重订阅 /stream，并用 eventId 去重。
```

尚未完整实现，不能写成已完成：

```text
snapshot-first session hydrate。
GET /sessions/:id DTO 到 web state 的正式 hydrator。
Skill/MCP 管理入口。
edit/respond HITL UI。
服务端 session list。
多设备权威会话同步。
```

## 业务职责

### Owns

```text
General Chat UI。
Composer。
Session rail 本地列表体验。
SessionTransport：POST message + EventSource stream。
Transport schema strict parse。
Render reducer。
Thread/activity projection。
HITL approve/reject/cancel 控件。
Preview simulator fallback。
Local UI cache。
```

### Does Not Own

```text
Session messages 权威存储。
Agent 执行。
MCP tool 实际调用。
Skill 实际执行。
Mongo/Redis 写入。
积分、支付、价格、后台管理。
```

## 上游和下游

```text
上游：
  用户浏览器。
  未来的 SiteContext/gateway。

下游：
  kokoro-session HTTP/SSE。
```

Web 不直接调用 `kokoro-agent`，不直连 Redis，不直连 Mongo，不直连 MCP server。

## 核心对象

```text
SessionStreamEvent
  Web domain event，camelCase，来自 session transport event 映射。

SessionStreamState
  本地渲染状态：messages、stepsByRun、todos、seenEventIds、runStatus。

SessionStep
  run 内 append-order 展示步骤：text / thinking / tool / subagent。

ConversationStore
  本地会话列表 UI cache：activeId、conversations、pendingInput、pendingRunId。

LiveSessionHandle
  EventSource 句柄 + 当前 runId + 本地 rejected 工具标记。
```

## 数据模型

Web 本地状态不是权威事实源。

允许本地存：

```text
active conversation id。
draft / local conversation list。
pendingInput / pendingRunId，用于刷新后重订阅 active run。
UI collapsed state。
seenEventIds，用于本地 replay 去重。
```

禁止本地存：

```text
MCP 明文密钥。
账务余额。
权威 run terminal status。
业务 cursor / lastResumeId。
服务端 session event 排序锚点。
```

旧 localStorage schema 不应驱动服务端兼容。脏数据可以丢弃并从 session snapshot 重建。

## API / RPC / Events

### Web -> Session

```text
POST /sessions/:sessionId/messages
  JSON body:
    idempotencyKey
    content
    executionStyle
    permissionMode?

GET /sessions/:sessionId/stream
  EventSource named events。

POST /sessions/:sessionId/runs/:runId/control
  run.cancel
  run.resume(approve/reject decisions)
```

当前 `GET /sessions/:sessionId` snapshot API 已在 session 存在，但 web 尚未把它作为
正式 hydrate 主入口。P0 必须补齐。

### Transport 语义

```text
event_id -> eventId
  幂等去重锚。
  不排序。

SSE id / Last-Event-ID
  浏览器传输层机制。
  Web domain 不读取、不保存、不展示。

stepsByRun[runId]
  append-order 展示结构。
  tool.returned/subagent.finished 就地更新原 step，不移动位置。
```

`EventSource` 新建连接不能手动设置 `Last-Event-ID` header。刷新后的恢复策略是：

```text
1. 目标态：先 GET /sessions/:id snapshot hydrate。
2. activeRun 存在时打开 /stream。
3. session 可全量或从服务端水位 replay。
4. web 用 eventId 去重。
```

当前实现尚未完成第 1 步，仍是直接 reattach `/stream`。

## Admin 管理

Web V1 只做用户侧入口：

```text
HITL approve/reject/cancel。
后续 Skill/MCP 入口。
```

官方后台、账务、模型、站点、用户管理不属于 `kokoro-web` 子仓本文范围。

## 业务链路

```text
1. 用户输入消息。
2. web 生成 idempotencyKey。
3. web POST /sessions/:id/messages。
4. session 返回 runId。
5. web 打开 EventSource /sessions/:id/stream。
6. web 对每条 SSE data strict parse。
7. mapper 转成 SessionStreamEvent。
8. reducer 用 eventId 去重。
9. reducer 按收到顺序 append text/thinking/tool/subagent step。
10. terminal run event 后关闭本轮 handle。
```

HITL：

```text
1. tool.awaiting_approval 渲染批准/拒绝按钮。
2. 同帧多个待批工具在本地暂存到齐后发一次 run.resume。
3. control POST 失败时保持 awaiting，用户可重试。
4. 本地 reject 只做乐观展示；权威结果仍等 session event 回流。
```

Preview fallback：

```text
session 后端不可达时使用 simulator。
simulator 只能用于本地 UI 预览，不能写入服务端事实。
```

## 部署

```text
服务名        kokoro-web
运行时        Next.js + Bun
端口          3000
Session API   NEXT_PUBLIC_KOKORO_SESSION_BASE_URL
```

Web 多实例应无状态。权威状态在 session/Mongo。

## 测试

必须覆盖：

```text
transport schema 拒绝 malformed event。
event mapper 字段转换。
reducer eventId 去重。
steps append-order。
message.completed 覆盖 delta。
tool awaiting/returned/rejected/responded。
subagent started/text/finished。
HITL control body。
localStorage 脏数据丢弃。
snapshot hydrate。
EventSource 重连不使用业务 cursor。
```

## 风险和边界

必须明确禁止：

```text
重新引入 seq。
按 eventId 排序。
保存 lastResumeId 作为产品状态。
Web 直连 agent。
Web 直连 Redis/Mongo/MCP provider。
localStorage 当聊天事实源。
为了旧缓存保留污染代码。
```

## 后续任务

### P0

```text
实现 snapshot-first hydrate：GET /sessions/:id -> SessionStreamState。
把 direct reattach 改成 snapshot 后 attach active run。
统一 /stream 路径命名，若改为 /events 必须 session/web 一次性改净。
补 edit/respond HITL UI 或从公开 UI 能力中明确隐藏。
补 session run request 契约修复后的端到端 smoke。
```

### P1

```text
Skill/MCP 管理入口。
服务端 session list。
更完整 agent activity 状态。
SSE 错误可恢复提示。
```

### P2

```text
多设备同步体验。
专业 agent / studio 入口。
更完整 MCP resources/prompts UI。
```
