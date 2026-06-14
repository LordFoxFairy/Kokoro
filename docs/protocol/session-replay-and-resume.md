---
status: 🟢 accepted
version: 1.0.0
producer: kokoro-session
consumers:
  - kokoro-web
backward-compatibility: Cursor semantics are stable within v1; changing ordering or idempotency rules requires a major version.
---

# Session Replay & Resume

> 定义断线重连、刷新、恢复时，浏览器如何从 `kokoro-session` 拉回缺失事件并继续当前 run。

## IDs

- `session_id`: 一个可恢复会话
- `conversation_id`: 一个用户线程，可容纳多个 run
- `run_id`: 一次执行
- `event_id`: 单个事件唯一标识
- `cursor`: 会话流中的有序位置

命名规则：
- 所有 ID 全局唯一，不暴露数据库自增主键
- `cursor` 只表达流顺序，不承担业务语义

## Ordering

- 同一 `run_id` 内，事件必须按 `cursor` 单调递增
- `message.delta` 必须按同一 `message_id` 的生成顺序 replay
- `run.completed` / `run.failed` 必须晚于该 run 的所有普通增量事件

## Replay cursor

客户端保存 `latest_acknowledged_cursor`。

重连时：
- 若带 cursor，请求 replay `cursor` 之后的所有事件
- 若不带 cursor，服务端返回最近一次可恢复窗口内的完整事件序列

## Resume invariant

A client that reconnects with the latest acknowledged cursor must be able to:
1. replay missing events in order
2. detect run completion without duplicate rendering
3. continue streaming from the same logical run

## Idempotency

- 客户端必须按 `event_id` 去重
- `message.completed` 覆盖对应 `message_id` 的最终内容
- `run.completed` / `run.failed` 重复到达时只收敛状态，不重复渲染 toast / banner
- 若未来把 `artifact.available` 升格进当前 session stream contract，则同一 `artifact_id` 的重放只应更新已有卡片，而不是重复插入

## Error envelopes

### stale cursor
```json
{
  "error": "stale_cursor",
  "message": "The replay cursor is older than the retained replay window.",
  "action": "restart_from_snapshot"
}
```

### expired run
```json
{
  "error": "expired_run",
  "message": "The run is no longer resumable.",
  "action": "show_completed_state"
}
```

### missing run
```json
{
  "error": "missing_run",
  "message": "The requested run does not exist in this session.",
  "action": "reload_session"
}
```

## UI expectations

- 页面刷新后，最近一次会话必须能回到正确的消息流位置
- 若 run 仍在进行，SSE 恢复后必须继续在同一逻辑 run 上追加
- 若 run 已结束，客户端必须进入稳定 completed / failed 态，而不是重新进入 loading
