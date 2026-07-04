# 存储保留策略（Retention）设计稿（2026-07-04，提案待批）

> 状态：设计先行。现状：checkpoint（langgraph thread）、run_state（含 tool_results/token_totals）、
> 记忆 store、redis 事件流、mongo session_events 全部无限增长。单机开发无感，生产必须有闸。

## 分层保留（各数据的"何时可删"语义不同）

| 数据 | 权威性 | 建议保留 | 清理机制 |
|---|---|---|---|
| redis per-run 事件流 | 非权威（mongo session_events 才是回放真源） | 已有 maxlen 修剪 + 终态删 control 流；补：终态 N 天后删 events 流 | worker 终态时设 redis EXPIRE（一行） |
| run_state 行（终态） | 幂等/租约用，终态后仅防重放 | 终态后 30 天 | 后台清扫（每日一次 DELETE WHERE terminal AND age） |
| tool_results / token_totals | 随 run 终态失效 | 随 run_state 同期清 | 同上（外键式同扫） |
| checkpoint threads | 会话续聊依赖——**产品决策**：会话多久算死 | 建议 session 最后活跃 90 天 | langgraph saver 无原生 TTL：按 thread_id 前缀扫删（sqlite delete / mongo TTL 索引可行性先实证） |
| 记忆 store | 长期资产，**默认永久** | 仅按 namespace 显式删除（租户下线） | 管理面操作，不自动清 |
| mongo session_events/messages | 会话史资产 | 随会话删除级联 | session 已有会话删除入口，补级联即可 |

## 实施要点

- 全部阈值走 env（KOKORO_RETENTION_*），0=关闭（默认关——保留期限是产品决策，不擅代）。
- 清扫器归属：run_state/redis 归 agent worker（数据是它写的）；session_events 级联归 session。
- 先实证：mongo TTL 索引对 langgraph checkpoint collection 的兼容性；sqlite VACUUM 时机。

## 验收（届时）

- 清扫幂等/边界矩阵（恰好过期/未过期/暂停中 run 永不清）；清扫后 resume 历史会话行为明确
  （checkpoint 没了=新会话语义，snapshot 仍有消息史）；e2e 回归。
