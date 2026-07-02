# kokoro-web 技术方案

三仓 V1 运行时总方案见：
[Agent / Session / Web V1 标准运行时方案](../technical/11-agent-session-web-v1-runtime.md)。
HIL、`ask_user` 和暂停点 UI 方案见：
[Agent HIL 与工具拦截标准方案](../technical/12-agent-hitl-tool-interception.md)。
三仓通用聊天链路见：
[Agent / Session / Web 通用聊天运行链路](../business-flows/agent-session-web-general-chat-runtime.md)。

## 定位

`kokoro-web` 是三仓运行时的界面层。它负责 General Chat UI、
session snapshot、EventSource、agent activity 展示、HITL 用户操作、
Skill/MCP 管理入口和本地非权威 UI 状态。

它是会话事实消费者，不是事实源。

## 业务职责

### Owns

```text
General Chat 页面。
Session list / message thread / composer。
POST message / GET snapshot / EventSource。
Transport schema strict parse。
Render reducer。
Agent activity UI。
HITL approve/reject/edit/cancel UI。
ask_user 提问 UI。
Skill 管理入口。
MCP 连接/授权/工具列表入口。
Local UI cache。
```

### Does not own

```text
Session messages 权威存储。
Agent 执行。
MCP tool 实际调用。
Skill 实际执行。
Mongo/Redis 写入。
MCP secret 明文。
三仓运行时之外的后台运营能力。
```

## 上游和下游

```text
上游：
  用户浏览器。
  SiteContext/gateway。

下游：
  kokoro-session HTTP/SSE。
```

Web 不直接调用 `kokoro-agent`，不直接调用 MCP server，不直接调用 model provider。

## 核心对象

```text
SessionSnapshot
  session + messages + activeRun + activity + eventWatermark。

SessionStreamState
  Web 本地渲染状态，非权威。

RenderEvent
  从 session event 映射后的 UI 事件。

ThreadItem
  用户消息、assistant turn、thinking、tool、todo、subagent。

SkillViewModel
  skill 列表、详情、启用状态、风险提示。

McpConnectionViewModel
  server、tools、prompts、resources、授权状态。
```

`SessionSnapshot` 是服务端读取模型，不是 Web 自己构造的事实源。

## 数据模型

Web 本地只存非权威状态：

```text
activeSessionId
draft input
UI collapsed/expanded state
recent snapshot cache（可丢弃）
```

禁止存：

```text
MCP 明文密钥。
账务余额。
run terminal 权威状态。
业务 resume cursor / lastResumeId。
seq/cursor 排序信息。
```

## API / RPC / Events

调用 session：

```text
POST /sessions/:sessionId/messages
GET  /sessions/:sessionId
GET  /sessions/:sessionId/events
POST /sessions/:sessionId/runs/:runId/control
```

删除旧调用：

```text
POST /sessions/:sessionId/runs
GET  /sessions/:sessionId/stream
```

SSE：

```text
EventSource named events
id: internal SSE id，Web domain 不读取
data: browser-facing session event JSON
```

幂等：

```text
POST message 使用 idempotencyKey。
Reducer 使用 eventId 去重。
```

## Reducer

Reducer 规则：

```text
eventId 去重。
按 SSE 到达顺序应用。
不按 seq/cursor 排序。
message.delta 追加临时内容。
message.completed 覆盖最终 assistant 内容。
run.completed.status 保留 completed/cancelled/timeout。
run.failed 进入失败态。
malformed event skip-and-continue。
```

Browser-facing events：

```text
message.delta
message.completed
thinking.delta
tool.invoked
tool.awaiting_approval
tool.returned
todo.updated
subagent.started
subagent.finished
subagent.text.delta
subagent.text.completed
run.completed
run.failed
```

## HITL UI

`tool.awaiting_approval` 必须展示：

```text
tool name
arguments
description
allowed_decisions
risk/source
```

默认动作：

```text
approve
reject
edit（工具参数可安全编辑时）
cancel run
```

`respond` 不作为普通危险工具按钮。`respond` 只在 `ask_user` 工具里表现为
用户回答问题。

## ask_user UI

V1 需要单独的用户提问组件：

```text
模型调用 ask_user。
Agent 产生 awaiting event。
Web 显示问题、可选项、输入框。
用户提交后走 control resume/respond。
```

这不是审批 UI 的“人工答复标记”，而是 Agent 主动向用户索取信息的工具。

## Skills UI

V1 Web 提供基础管理入口：

```text
查看官方/用户/workspace/project skills。
启用/禁用。
查看 description、版本、风险、允许工具、需要 MCP。
创建/编辑用户 skill。
手动触发 skill。
```

Web 不做：

```text
直接执行 skill。
绕过 session 把 skill prompt 发给 agent。
保存第三方 skill 源码到浏览器。
默认安装未审核第三方 skill。
```

## MCP UI

V1 Web 提供 MCP 连接入口：

```text
连接 HTTP / streamable HTTP MCP server。
展示 tools/prompts/resources。
OAuth 或 token 授权入口。
启用/禁用 server 或 tool。
展示高风险 tool 的审批状态。
```

Web 不做：

```text
直接调用 MCP tool。
保存明文 token 到 localStorage。
把全部 MCP schema 放进浏览器状态。
```

## 部署

```text
服务名        kokoro-web
运行时        Next.js
包管理        pnpm 或 npm
端口          3000
环境变量      NEXT_PUBLIC_KOKORO_SESSION_BASE_URL
              KOKORO_SITE_CONTEXT_MODE
多实例        无状态；权威状态在 session/Mongo。
```

V1 不使用 Bun 作为标准运行约束。

## 测试

```text
单测：
  transport schema、event mapper、reducer、local storage parser。

组件：
  thread、activity、composer、HITL controls、ask_user、Skill/MCP views。

集成：
  send message -> snapshot -> EventSource -> terminal。
  refresh active run -> snapshot + attach。
  malformed event skip-and-continue。

反例：
  duplicate eventId 不重复渲染。
  run.completed status 不丢。
  localStorage 脏数据不崩。
  未授权 MCP/Skill 不可触发。
  Web 不读取 cursor；seq 只作同一 run 内 UI 交错。
```

## 风险和边界

```text
禁止 Web 直连 agent。
禁止 Web 直连 MCP tool。
禁止 Web 保存 MCP 密钥明文。
禁止 Web 维护 lastResumeId / 业务 cursor。
禁止把 localStorage 当权威状态。
禁止把 run.completed.status 丢掉。
禁止把所有能力都堆进一个侧栏。
```

## 后续任务

```text
P0  Transport 改为 POST message + GET snapshot + EventSource /events。
    去掉 /runs /stream 调用。
    Reducer 删除 seq/cursor 排序。
    run.completed.status 展示。
    HITL 展示 description + allowed_decisions。
    ask_user UI。
    Skill/MCP 基础管理入口。

P1  Skill 创建/编辑表单。
    MCP tools/resources/prompts 管理页。
    activity UI 完整 terminal status。

P2  专业 agent 入口 UI。
    多设备 active run 协同体验。
```
