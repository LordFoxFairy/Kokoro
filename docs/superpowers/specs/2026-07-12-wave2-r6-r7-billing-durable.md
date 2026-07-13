# Wave 2 · R6/R7 子 spec——billing hold journal 与 settle/release durable compensation

状态:执行稿(上级=总设计稿 §5.4/§6 Wave2-7/-8/§8.3,已获批)。仓面:kokoro-session(billing 客户面;
platform credit API 不改契约——其 hold/settle/release 已有幂等键面)。R0 钉4(settle 无持久重试)=
R7 先红起点。纲领:R5/R6 同改 session run schema,R5 合流后才动 R6;R7 依 R6 journal。

## R6:hold journal(hold 成功但 handle 未落库 / enqueue failure 收敛)

- session 受理计费 run:调 credit hold **前**先落 billing journal 行{run_id, phase: hold_pending,
  idempotency_key(=run_id 派生,与现 hold 调用一致), at}→hold 成功→置 held+存 hold_handle→
  继续受理。崩溃窗口收敛(reconciler):
  - hold_pending 无 handle→按 idempotency_key 向 credit 查询(既有幂等面:同 key 重放返回原 hold)
    →adopt(补 handle 置 held)或确认未成→置 hold_failed。
  - held 但 run 未受理成功(enqueue failure/dispatch 未写)→release+置 released(现 enqueue 失败
    释放路径收编进 journal,不再裸调)。
- journal 为 session 私有集合(billing_journal,inline 名),不进根契约。

## R7:settle/release durable compensation(R0 钉4 转绿)

- run 终态收口时 settle/release 不再"一次调用尽力而为":journal 行置 settle_pending|release_pending
  →调用成功→settled|released(终局)。失败/崩溃→行留 pending,**compensation scanner**(随既有
  reconciler 节奏)按幂等键重试,重试上限后仍败→行置 compensation_stuck+ERROR 告警日志(占位 OBS-1,
  不静默),不阻塞 run 投影终态(纲领:业务终态≠saga 完成)。
- hold 临期策略:scanner 对 held 且 run 仍 active 的临期 hold(阈值 env,缺省 hold TTL 的 80%)
  ERROR 告警(V1 不自动续期,防双花);credit TTL sweeper 仍是最后保险,不是成功证明。
- billing:`held -> settle_pending|release_pending -> settled|released`全程可查(journal 即真源);
  finalization(R5)要求 billing phase 到达终局或 compensation_stuck 才算 finalized(stuck 不阻塞
  终态投影,只阻塞 finalized 标记,reconciler 持续追赶)。

## 验收

- R0 钉4 转绿收口。故障矩阵(§8.3 末三行):hold 成功落 handle 前崩溃→adopt 不双扣;settle 调用
  成功回执丢失→重试幂等不双结;release 与 settle 互斥(同 run 只一相);enqueue 失败必释放。
- session 全量只增不减三绿;E2E-40 计费段行为不变+可加断言:kill session 于 settle 前→重启
  scanner 收敛 ledger 落账恰一次。
