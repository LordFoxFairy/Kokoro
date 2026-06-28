# Session 生命周期

## 目标

定义 conversation 从创建到删除的状态、与 siteId 的绑定、单 active run 准入，以及刷新/断线后的快照恢复与续传语义。

## 参与模块

```text
kokoro-session  conversation/message/run 真源，快照与 replay。
kokoro-web      创建会话、加载快照、attach active run。
kokoro-user     提供 userId/workspaceId 鉴权（经 SiteContext）。
```

## 前置条件

```text
SiteContext 已解析，User 已登录。
```

## 主流程

```text
创建   POST /conversations（siteId/userId/workspaceId/appKey/surface）-> status=active。
活跃   POST /conversations/:id/messages；单 session 同时只允许一个 active run。
快照   GET /sessions/:id 返回当前消息、run 状态、浏览器事件；web 以此为恢复真源。
续传   有 active run 时打开 SSE，先读 MessageStore(Mongo) 历史，再 tail kokoro:session:{id}:live。
存档   POST /conversations/:id/archive -> status=archived，停写允读。
删除   DELETE /conversations/:id -> 删 Message/AgentRun/ToolCall；UsageRecord 与 LedgerEntry 保留以审计。
```

## 异常流程

```text
重复发起 run    单 active run 准入拒绝第二个并发 run。
断线/刷新       不靠浏览器保存 cursor；重新拉 snapshot 后 attach active run。
live 窗口过期    Redis live 仅短窗口（约 512 条），缺口由 Mongo 历史补齐。
跨站访问        他站用户不能访问本站 conversation。
```

## 数据变化

```text
Conversation   状态 active|archived，siteId/workspaceId 绑定（Mongo）。
Message / AgentRun / session_events   追加（Mongo）。
删除时          UsageRecord/LedgerEntry 保留（MySQL，审计与对账）。
```

## 幂等和一致性

```text
siteId/workspaceId   会话内不可中途切换。
eventId              去重锚点，不排序。
排序真源              Mongo 追加顺序 + SSE 单连接发送顺序；不要求浏览器反解游标。
Mongo 长期真源        Redis 只负责实时传输与短期锁。
```

## 用户可见结果

```text
刷新后会话完整恢复，进行中的 run 继续流式。
存档会话只读可查，删除后历史消失但账务/审计留存。
```

## 验收标准

```text
刷新/换设备后能从 snapshot 恢复并续接 active run。
同 session 不出现两个并发 active run。
取消/超时等终态在 replay 后不退化为普通完成。
跨站隔离生效。
```

相关：[general-chat](general-chat.md)、[../technical/04-session-architecture.md](../technical/04-session-architecture.md)、[../modules/kokoro-session.md](../modules/kokoro-session.md)。
