# Wave 2 · R5 子 spec——session persisted/projected 双水位 + quarantine/NACK + finalization

状态:执行稿(上级=总设计稿 D5/§5.4/§6 Wave2-6/§8.3,已获批)。仓面:kokoro-session。
契约(已冻结 6329f8a):同 R4。R0 钉5(recover reprojection)=先红起点之一。前置:R4 语义(agent 只
head-of-line 发布 critical 帧,必带 durable_seq/event_id)。

## 语义

- **inbox/回执**:relay 消费 raw 帧,带 durable 身份位的 critical 帧走 durable 通道:落位(session
  既有 session_events 追加保持)→写 run_event_receipts 行{run_id,durable_seq,event_id,persisted}
  (unique [run_id,durable_seq] 天然去重:重复投递→回执已在,幂等)→CAS 推进 manifest.persisted_seq
  (仅当连续 slot 全被 persisted|rejected 占据)。**先回执后 ACK**(§2.3:durable inbox 前不 ACK)。
- **projected 水位**:投影(浏览器面 append/live publish/终态收口)只允许按 CAS current+1 逐 seq
  推进 manifest.projected_seq;中间 seq 缺失而 terminal 先到→不得 finalize,等补齐。
- **quarantine/NACK**:identity 可信(run_id/durable_seq/event_id 齐)但 payload 校验失败的
  critical 帧→回执行置 rejected(占据该 slot,不伪装 persisted)→contract-failure reconciler 原子
  投影 run.failed{code: contract_incompatible} 并 CAS terminal_fence_seq=min(existing, seq)
  (session 除 dispatch expire 外唯一终态权场景)。信封都解不开的噪声→只进既有 DLQ 语义,不占 seq。
- **superseded 后缀**:fence 收窄后,已持久或晚到的 seq>fence 回执行置 superseded,永不投影;
  manifest.superseded_from 记起点。persisted_seq 可越过 fence,projected_seq 恰停 fence。
- **finalization reconciler**:扫「terminal 已投影未 finalized」的 run,收敛 projection/active
  slot/pause/message/billing 全清(=R0 钉5 转绿:recover 后重投影一次且只一次);终态 consumed+
  producer_close_requested→置 producer_closed(此后 manifest 可 GC,V1 不做自动 GC 只留门)。
- run.started 特例保持:persisted 后可查回执,仍不投影浏览器(R1 语义收编)。

## 验收

- R0 钉5 转绿收口。故障矩阵(§8.3):persisted 与 projected 各推进点前后崩溃重启收敛;乱序/重复/
  跳号帧不投影不 finalize;quarantine→contract_incompatible 终局且旧会话侧后缀全 superseded。
- **跨仓联测**(R4+R5 合验,gate 增断言):终态经 outbox→回执→投影→finalized 全链;kill agent 于
  publish 后回执前→重启补发→浏览器终态恰一次。
- session 全量只增不减三绿;e2e 全绿。**注意:R6 同改 session run schema,本项合流后才开 R6(纲领:
  R5/R6 必须串行)。**
