# Wave 2 · R2 子 spec——control outbox/inbox 与 receipt 闭环

状态:执行稿(上级=总设计稿 D5/§5.3/§7/§8.3,已获批)。前置:R0 钉3(control 误报已发布)在位;R1 已落。
契约(本文随附冻结):control.yaml run.resume/run.cancel/run.steer 增 `decision_id`(steer 用 message_id 作等价幂等锚,不加;resume/cancel 加);events.yaml 增 **internal-only raw kind** `run.control.receipt{decision_id,status}`(status: persisted|applied;不入 browser_order,session 消费进 receipt 存储,永不投影浏览器)。

## 语义

- **session command outbox**:applyControl 受理(守门通过)后先落 control_outbox 文档{session_id,run_id,decision_id,body,status:pending_publish,created_at}→XADD control 流→置 published。XADD 失败:对外仍 202(control pending),启动即扫 pending_publish 重发(幂等键=decision_id)。「已记录」与「已发布」分离=R0 钉3 翻绿。
- **agent control inbox**:consume control 帧→先落 ledger inbox{run_id,decision_id,fingerprint(interrupt 指纹),status:persisted}→ACK→apply(Command resume/cancel)→checkpoint 后置 applied。重复 decision_id(重发/重投)→inbox 命中→ACK 丢弃不重放。重启 pending scanner:persisted 未 applied 的 command 续办(fingerprint 校验当前 interrupt 匹配才 apply;不匹配=stale→标 superseded 不 apply)。
- **receipt**:agent 在 persisted 与 applied 两时点各发 `run.control.receipt`(internal raw kind,经既有事件流);session 消费→control_outbox 文档状态推进(published→persisted→applied)。HTTP 面:POST control 响应体不变(契约冻结),新增同属主 `GET /sessions/:id/runs/:rid/control/:decisionId`(纲领 §7:receipt 查询端点,返回 {decision_id,status:pending|persisted|applied|failed})——http.yaml 端点随附冻结。
- Redis XADD/流存在/live publish 不作为任何清理条件(纲领);control 流删除门=R4/R5,本项不动清理。

## 验收

- R0 钉3 转绿收口;新故障矩阵:outbox 落库后 publish 前崩溃(重启补发)/agent inbox 后 apply 前崩溃(scanner 续办,fingerprint 不匹配不 apply)/重复 decision_id 不双放;receipt 两时点可查(HTTP 端点)。
- 双仓全量只增不减;e2e 全绿(HITL 各段行为不变;gate 可加 receipt 端点断言一条:approve 后查 status=applied)。
