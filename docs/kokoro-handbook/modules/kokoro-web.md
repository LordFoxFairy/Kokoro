# kokoro-web 技术方案

## 定位

`kokoro-web` 是 Kokoro 三仓运行时的界面层。它负责 General Chat UI、session snapshot、SSE 消费、agent activity 展示、Skill/MCP 管理入口和用户交互。

它是会话事实的消费者，不是事实源。

## 业务职责

### Owns

```text
General Chat 页面。
Session list / message thread / composer。
SSE EventSource 连接。
Transport schema 严格解析。
Render reducer。
Agent activity UI。
HITL approve/reject/cancel UI。
Skill 手动触发入口。
Skill 基础管理入口。
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
三仓运行时之外的业务管理模块。
```

## 上游和下游

```text
上游：
  用户浏览器。
  SiteContext/gateway。

下游：
  kokoro-session HTTP/SSE。
```

Web 不直接调用 `kokoro-agent`，不直接调用 MCP server，不直接调用 provider。

## 核心对象

```text
SessionSnapshot
  session + messages + activeRun。

SessionStreamState
  Web 本地渲染状态。

RenderEvent
  从 session event 映射后的 UI 事件。

ThreadItem
  用户消息、assistant turn、tool、thinking、todo、subagent。

SkillViewModel
  skill 列表、详情、启用状态。

McpConnectionViewModel
  server、tools、prompts、resources、授权状态。
```

## 数据模型

Web 本地只存非权威 UI 状态：

```text
localStorage/sessionStorage
  activeSessionId
  draft input
  UI collapsed state
  最近 snapshot cache（可丢弃）
```

禁止存：

```text
MCP 明文密钥。
账务余额。
run terminal 权威状态。
业务 resume cursor / lastResumeId。
```

## API / RPC / Events

调用 session：

```text
POST /sessions/:sessionId/messages
GET  /sessions/:sessionId
GET  /sessions/:sessionId/events
POST /sessions/:sessionId/runs/:runId/control
```

浏览器事件：

```text
EventSource named events
data: browser-facing session event JSON
id: internal SSE id, Web domain 不读取
```

幂等：

- Web reducer 按 `eventId` 去重。
- POST message 使用 `idempotencyKey`。

## 运行时管理

V1 Web 只提供面向用户的基础管理入口：

```text
Skill 列表/详情/启用/禁用/创建用户 skill。
MCP server 连接/授权/启用/禁用/tool 可见性。
Session run cancel。
```

三仓运行时之外的运营能力不属于本文范围。

## 业务链路

`kokoro-web` 只参与三仓运行链路：

```text
用户在 Web 输入消息。
kokoro-web 调用 kokoro-session 创建消息和 run。
kokoro-web 加载 session snapshot。
kokoro-web 通过 SSE 消费 session events。
kokoro-web 渲染 message thread、agent activity、HITL controls、Skill/MCP 入口。
```

Web 不维护通用产品业务链路文档；涉及平台、账务、市场、后台的链路不在本文维护。

## 部署

```text
服务名        kokoro-web
运行时        Next.js + Bun
端口          3000
环境变量      NEXT_PUBLIC_KOKORO_SESSION_BASE_URL
              KOKORO_SITE_CONTEXT_MODE
多实例        无状态；权威状态在 session/Mongo。
```

## 测试

```text
单测：
  transport schema、event mapper、reducer、local storage parser。

组件：
  thread、activity、composer、HITL controls、Skill/MCP management views。

集成：
  send message -> snapshot/live SSE -> terminal。
  refresh active run -> snapshot + attach。
  malformed event skip-and-continue。

反例：
  duplicate eventId 不重复渲染。
  localStorage 脏数据不崩。
  SSE 失败后可重新 snapshot。
  未授权 MCP/Skill 不可触发。
```

## 风险和边界

```text
禁止 Web 直连 agent。
禁止 Web 直连 MCP tool。
禁止 Web 保存 MCP 密钥明文。
禁止 Web 自己维护 lastResumeId / 业务 cursor。
禁止把 localStorage 当权威状态。
禁止把所有能力都堆进侧栏。
```

## 后续任务

```text
P0  Snapshot-first session load。
    去掉 lastResumeId 产品状态。
    Skill 手动触发入口。
    MCP HTTP server 连接入口。
    HITL control UI 对齐 session API。

P1  Skill 创建/编辑表单。
    MCP tools/resources/prompts 管理页。
    agent activity UI 与 run terminal status 完整展示。

P2  专业运行时入口 UI。
    Skill/MCP 更完整的管理 UI。
    多设备 active run 协同体验。
```
