# Web 架构

三仓 V1 运行时总方案见：
[Agent / Session / Web V1 运行时技术方案](11-agent-session-web-v1-runtime.md)。
三仓通用聊天链路见：
[Agent / Session / Web 通用聊天运行链路](../business-flows/agent-session-web-general-chat-runtime.md)。

## 定位

`kokoro-web` 是三仓里的界面层。它负责 SiteContext 注入、聊天 UI、
SSE 消费、事件严格解析、本地 reducer、HITL 控件和本地 UI 缓存。

目标态还负责 session snapshot 加载、Skills/MCP 管理入口和 artifact 展示。
当前代码尚未完成 snapshot-first hydrate，也尚未完成 Skills/MCP 管理入口。

它不拥有 session 真源，不执行 agent，不直接写 Mongo/Redis。

## V1 目标能力范围

V1 web 必须支持：

- General Chat UI。
- session list / session snapshot / messages 展示。
- 发送用户消息。
- active run SSE 消费。
- agent activity 展示：thinking、tool、todo、subagent、HITL。
- Skill 手动触发入口和基础管理入口。
- MCP 连接/授权/工具可见性的基础管理入口。
- 刷新恢复：snapshot + attach active run。

当前已实现聊天 UI、POST message、`/stream` EventSource、strict parse、
eventId 去重、append-order reducer、HITL approve/reject/cancel 和 simulator fallback。
未完成项以 [kokoro-web 模块文档](../modules/kokoro-web.md) 为准。

V1 不要求：

- 三仓运行时之外的完整业务产品 UI。
- 三仓运行时之外的运营能力。
- Web 直接调用 agent 或 provider。

## 分层

```text
app
  Next.js route/layout/styles

interfaces
  session shell / thread / activity / composer / skill-mcp management views

application
  session stream reducer
  conversation store
  transport orchestration
  local persistence

infrastructure
  HTTP/SSE client
  Zod transport schema
  event mapper

domain
  render event union
  UI state model
```

## 数据流

发送：

```text
composer submit
  -> POST /sessions/:sessionId/messages
  -> optimistic user message
  -> active run state
  -> open SSE
```

刷新：

```text
page load
  -> GET /sessions/:sessionId
  -> render messages snapshot
  -> if activeRun open SSE
```

SSE：

```text
EventSource
  -> strict parse
  -> map transport event to render event
  -> reducer apply by eventId idempotency
  -> render thread/activity
```

## Web 不维护业务 cursor

Web 不保存 `lastResumeId`，不拼 `?after=<id>` 作为产品 API。

允许存在的只有浏览器和服务端之间的标准 SSE 传输能力：

- EventSource 自动重连。
- 浏览器可带 `Last-Event-ID`。
- Web domain state 不读取、不展示、不依赖它。

刷新和换设备以 snapshot 为准。

## Reducer

Reducer 接收 browser-facing session events：

```text
session.created
run.created
message.delta
message.completed
thinking.delta
tool.invoked
tool.awaiting_approval
tool.returned
todo.updated
subagent.started
subagent.finished
run.completed
run.failed
```

规则：

- `eventId` 去重。
- 事件到达顺序由 SSE 保证；不反解 cursor/seq。
- `message.completed` 覆盖最终 assistant 内容。
- terminal run event 关闭 streaming 状态。
- 单条 malformed event skip-and-continue，不崩整个 UI。

## Skills UI

V1 web 的 Skills 是 agent 扩展入口，不是公开商业广场。

需要支持：

- `/` 菜单手动触发 skill。
- Skill 管理页：查看官方/用户/workspace skill，启用/禁用。
- Skill 详情页：description、允许工具、需要权限、版本。
- 创建/编辑用户 skill 的基础表单。

Web 不做：

- 直接执行 skill。
- 绕过 session 把 skill prompt 发给 agent。
- 默认安装未审核第三方 skill。

## MCP UI

V1 web 的 MCP 是外部工具连接入口。

需要支持：

- 连接 HTTP MCP server。
- 展示 server tools/prompts/resources。
- OAuth 或 token 授权流程入口。
- 按 site/workspace/project 启用或禁用。
- 第一次高风险工具调用走 HITL。

Web 不做：

- 保存明文密钥到 localStorage。
- 直接从浏览器调用 MCP tool。
- 将所有 MCP schema 塞进浏览器状态。

## SiteContext

所有请求必须带服务端认可的 SiteContext。Web 只能携带当前上下文，不决定最终授权。

Web/gateway 不能绕过 SiteContext。

## 本地缓存

允许缓存：

- 当前 active session id。
- UI 折叠态。
- 未提交草稿。
- 最近 snapshot 的非权威副本。

不允许缓存为权威：

- 账务。
- run terminal status。
- MCP 凭据明文。
- session replay cursor。

## 风险

- 把 Web reducer 当事实源。
- Web 直连 agent。
- Web 自己拼接 MCP tool schema 和 prompt，绕过 manifest。
- localStorage strict schema 过窄，导致运行态刷新丢失。
- 过度把 every feature 放进侧栏，而不是通过能力入口/管理页组织。
