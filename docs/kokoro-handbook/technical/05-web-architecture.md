# Web 架构

三仓 V1 运行时总方案见：
[Agent / Session / Web V1 标准运行时方案](11-agent-session-web-v1-runtime.md)。
三仓通用聊天链路见：
[Agent / Session / Web 通用聊天运行链路](../business-flows/agent-session-web-general-chat-runtime.md)。

## 定位

`kokoro-web` 是三仓里的界面层。它负责 SiteContext 注入、聊天 UI、
session snapshot 加载、EventSource、事件严格解析、本地 reducer、
HITL/ask_user_question UI、Skills/MCP 管理入口。

它不拥有 session 真源，不执行 agent，不直接写 Mongo/Redis。

## V1 能力范围

```text
General Chat UI。
session list / snapshot / messages 展示。
发送用户消息。
active run EventSource 消费。
agent activity 展示：thinking、tool、todo、subagent、HITL。
ask_user_question 问答 UI。
Skill 基础管理入口。
MCP 连接/授权/工具可见性入口。
刷新恢复：snapshot + attach active run。
```

## 分层

```text
app
  Next.js route/layout/styles

interfaces
  session shell / thread / activity / composer / skill-mcp views

application
  reducer / transport orchestration / local cache

infrastructure
  HTTP/SSE client / schema / mapper

domain
  render event union / UI state model
```

## 数据流

发送：

```text
composer submit
  -> POST /sessions/:sessionId/messages
  -> GET /sessions/:sessionId
  -> EventSource /sessions/:sessionId/events
```

刷新：

```text
page load
  -> GET /sessions/:sessionId
  -> render snapshot
  -> if activeRun open EventSource
```

SSE：

```text
EventSource
  -> strict parse
  -> map to render event
  -> reducer eventId dedupe
  -> render thread/activity
```

## Web 不维护业务 cursor

Web 不保存 `lastResumeId`，不拼 `?after=<id>`。

允许存在的只有浏览器和服务端之间的标准机制：

```text
EventSource 自动重连。
浏览器可带 Last-Event-ID。
SSE id 不进入 domain state。
```

刷新和换设备以 snapshot 为准。

## Reducer

规则：

```text
eventId 去重。
按 SSE 到达顺序应用。
不反解 cursor/seq。
message.completed 覆盖最终 assistant 内容。
run.completed.status 保留 completed/cancelled/timeout。
terminal run event 关闭 streaming 状态。
单条 malformed event skip-and-continue。
```

## HITL 和 ask_user_question

HITL 工具审批展示：

```text
tool name
arguments
description
allowed decisions
risk/source
```

普通危险工具：

```text
approve / reject / edit / cancel
```

`ask_user_question` 是独立问答 UI，用户回答后使用 LangGraph HITL `respond` 恢复。
不要把 `respond` 做成所有工具的通用拒绝/答复按钮。

## Skills UI

V1 Web 提供：

```text
Skill 列表。
Skill 详情。
启用/禁用。
创建/编辑用户 skill。
手动触发 skill。
```

Web 不执行 skill，不绕过 session 把 skill prompt 发给 agent。

## MCP UI

V1 Web 提供：

```text
连接 HTTP / streamable HTTP MCP server。
OAuth/token 授权入口。
展示 tools/prompts/resources。
启用/禁用 server/tool。
展示高风险工具审批。
```

Web 不直连 MCP tool，不保存明文密钥。

## 本地缓存

允许：

```text
activeSessionId
draft input
UI collapsed state
recent snapshot cache
```

禁止作为权威：

```text
run terminal status
MCP secret
session replay cursor
seq/cursor 排序
```

## 风险

```text
把 Web reducer 当事实源。
Web 直连 agent。
Web 直连 MCP tool。
localStorage 保存权威 run 状态。
run.completed.status 被 mapper 丢弃。
所有能力都堆进一个侧栏，导致主体验失焦。
```
