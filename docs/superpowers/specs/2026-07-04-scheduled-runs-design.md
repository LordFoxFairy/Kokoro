# 定时任务（Scheduled Runs）设计稿（2026-07-04，提案待批）

> 状态：设计先行，未实施。这是"前置改参 normalizer"的首个真实用例载体。

## 定位与所有权

- **触发器归 session**（它拥有 session/run 生命周期）：调度器只是"到点替用户发一条消息"，
  复用 POST messages 全链（幂等/409/暂停/事件），agent 零新机制。
- **创建路径归 agent 工具**：`schedule_task` 工具（对话式创建，"每天早上 9 点帮我总结邮件"），
  这就是前置改参的用例——时区/歧义时间的确认走**既有 HITL edit**（审批卡改参放行），
  确定性归一（cron 解析/tz 换算）用代码，不用模型。

## 数据与执行

- mongo `schedules`：`{schedule_id, namespace, session_id, entry?, content, cron, timezone,
  next_fire_at, enabled, created_by_run}`；namespace 隔离与既有一致。
- session 单实例 ticker（V1）：到点 POST messages，**幂等键 = schedule_id + fire_time**
  （天然去重，多实例竞争也安全）；活跃 run 撞 409 → 按策略跳过本次并记录（不排队，避免风暴）。
- 到点暂停无人应答：pending_pauses 本就跨时存活，用户回来再答——无需新机制；
  可选 P2：schedule 声明 `hands_off: true` 时把 ask_user 从工具集摘除。

## agent 侧改动（很小）

- `schedule_task` / `list_scheduled_tasks` / `cancel_scheduled_task` 工具（通用原语，
  存取经 session HTTP 管理面，不直连 mongo——工具体内零基础设施）。
- 默认进 approval_tools（创建定时任务=未来的自动执行授权，必须人批）。

## 验收（届时）

- 对话创建（含时区歧义 → HITL edit 改参）→ 到点触发 → 幂等重放矩阵 → 409 跳过记录 →
  namespace 隔离断言；跨栈 e2e 场景 + 真模型场景。

## 不做（明确边界）

- 不做分布式调度器（V1 单 ticker 足够，多实例靠幂等键安全）；
- 不做任意 shell/webhook 触发（消息触发一种，其余等真实需求）。
