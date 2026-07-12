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

## 工作台形态

web 采用三栏工作台形态（形态提炼自 [specs/2026-07-11-capability-hub-and-polish](../../superpowers/specs/2026-07-11-capability-hub-and-polish.md) §4，此处记为当前有效界面骨架）：

- **三栏 IA**：折叠式单列侧栏（导航/会话）+ 事件序穿插的会话流 + 可拖拽/全屏的 **Canvas 工作区**。Canvas 由事件总线开合，产物点击即进 Canvas（非弹窗），开合状态带会话级记忆。
- **四卡**（会话流内的结构化卡片）：
  - 工具胶囊 pill：状态映射语义色，loading 流光，点击入 Canvas。
  - 计划链卡：逐项状态、可折叠。
  - 审批卡 = 动态表单：schema 驱动，与 HITL `kind=input` 契约天然对齐（`input_schema` 已上 wire）。
  - 交付物文件卡：骨架占位 → 实体卡，支持下载与二次加工。
- **语义 design tokens**：全色走 `--k-*` 语义变量（text 四级 / bg 多层 / 语义色三梯度），组件零裸色值；暗色主题换色相而非反色。
- **登录闸**：整站入口由登录闸（`login-gate`）把守，未登录不进会话。当前 web 端换签为 dev-login + localStorage token 形态；AUTH-P0（[specs/2026-07-12-wave1-auth-p0](../../superpowers/specs/2026-07-12-wave1-auth-p0.md)）落地后改为 **BFF 密封 httpOnly cookie + 同源 `/api/session` 代理**，浏览器不再持 bearer，localStorage token 途径删除。

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

## i18n

能力边界与静态/动态双源判断见 [14-web-i18n-capability](14-web-i18n-capability.md)。
现状（2026-07 更新）：静态 i18n 层已落地（src/i18n：zh 真源+en 增量+useT，i18n 门禁测试钉硬编码回归）；实现细节由 web 侧
落地时自行设计，本手册只锁能力与边界。
