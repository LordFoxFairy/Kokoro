# Wave 2 · R4 子 spec——agent critical/terminal outbox(head-of-line + first-terminal fence)

状态:执行稿(上级=总设计稿 D5/§5.4/§6 Wave2-5/§8.3,已获批)。仓面:kokoro-agent。
契约(已冻结 6329f8a):raw 信封可选 {durable_seq,event_id};RunEventReceiptDoc/RunReceiptManifestDoc
(agent 侧消费面);R0 钉2(终态帧 publish 失败静默丢)= 本项先红起点。

## 语义

- **critical 集(V1)**:run.started / run.control.receipt / run.completed / run.failed。per-run
  durable_seq 从 1 连续分配(ledger 原子计数),critical 帧发布必带 {durable_seq, event_id=evt_ 前缀
  cuid};live 帧(delta/tool 过程帧)不占 seq、不进 outbox,丢了可由 checkpoint 重建。
- **outbox**:发布前先落 ledger outbox 行{run_id, durable_seq, event_id, kind, payload_json,
  status: queued}→publish→置 published。**严格 head-of-line**:只发布"最小的未确认 seq";前一 seq
  经 session 回执(run_event_receipts 行 status=persisted)确认后才发布下一 seq。publish 失败/崩溃→
  行留 queued,启动 scanner 补发(=R0 钉2 转绿)。R1 的 run_started_published 布尔位收编进本体系
  (started=seq 1 惯例,迁移语义:旧布尔位读侧兼容一版,写侧废止)。
- **first-terminal fence**:终态帧分配时 CAS 设 ledger terminal_fence_seq(仅当未设);fence 已设→
  更大 seq 不再分配;本地已排队 seq>fence 的行原子改 superseded(留 kind+event_id 摘要,payload 删),
  永不发布。
- **consume/close 握手**(同库部署,直读直写契约文档,写者分域见 storage.yaml 注):agent 读
  run_event_receipts 确认 persisted→本地行置 consume_requested→CAS 推进 manifest.consumed_seq
  (按 seq 顺序,校验 event_id 一致)→硬删本地行 payload。回执 status=rejected(quarantine NACK)→
  停止执行与分配,消费该 NACK(同步 fence=min(existing, rejected_seq)),按 contract_incompatible
  终局收口。终态回执 consumed 且无可发布行→persist producer_close_requested→CAS 置 manifest
  producer_close_requested=true(producer_closed 由 session 设)。manifest 行缺失且未 close=
  receipt_state_lost:不删 outbox,ERROR 日志告警。
- 现 emitter 的 per-run index(live/UI 序)不动;durable_seq 独立并行,互不影响浏览器面。

## 验收

- R0 钉2 转 XPASS→去 xfail 收口。故障矩阵(§8.3):terminal publish 失败→outbox 补发(固定
  event_id/durable_seq 不漂移);发布后回执前崩溃→重发幂等(session 按 [run_id,durable_seq] unique
  去重);fence 后分配拒绝+后缀 superseded 不发布;rejected NACK→停止+收口。
- agent 全量只增不减三绿;e2e 全绿(浏览器面行为透明)。与 R5 跨仓联测归 R5 验收(session 侧落齐后)。
