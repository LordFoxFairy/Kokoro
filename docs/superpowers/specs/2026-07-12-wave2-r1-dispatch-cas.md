# Wave 2 · R1 子 spec——run_dispatch CAS 与 durable claim 后 ACK

状态:执行稿(上级=总设计稿 D5/§5.2/§7/§8.3,已获批)。前置:R0 钉1(strict xfail)在位=先红起点。
仓面:kokoro-session(写 dispatch intent+超时收口)+kokoro-agent(claim CAS+ACK 后置)+根契约(本文冻结)。

## 契约(storage.yaml 增,本 spec 随附落地)

```yaml
  - name: RunDispatchDoc        # 投递竞争单文档 CAS(D5):session 写 pending,agent 抢 claimed,超时改 expired
    fields:
      - {name: run_id, ...}                      # unique
      - {name: session_id / namespace, ...}
      - {name: fence, type: string_nonempty}     # 本次投递围栏 id(重发同 run 同 fence 不二次执行)
      - {name: status, type: enum:dispatch_status}   # pending|claimed|expired
      - {name: deadline_at, type: int}           # pending 有效期(ms epoch);KOKORO_DISPATCH_MAX_AGE_MS 缺省 15min
      - {name: claimed_by, ..., optional+nullable}   # consumer 名
      - {name: created_at/updated_at, type: int}
```
enum `dispatch_status: [pending, claimed, expired]`;collection `run_dispatches` unique [run_id]。

## 语义(纲领原文工程化)

- session 受理:persist run 后、XADD 前写 `pending+deadline+fence`;XADD 失败→intent 已在,对外 202 dispatch_pending,后台重发(重发同 fence)。
- agent serve:parse 合法帧→**先 CAS pending→claimed(条件 status=pending ∧ deadline 未过 ∧ fence 匹配)**;赢→ACK+执行(既有 lease/heartbeat/checkpoint takeover 全保留);输(已 claimed 同 fence=重复投递/已 expired=迟到帧)→ACK 丢弃不执行。CAS 前崩溃→未 ACK,PEL 重投(=R0 钉1 翻绿)。transport 噪声(不可解析)→DLQ 记录后 ACK(纲领 quarantine 简版:R1 先落 DLQ 集合 dispatch_dlq{raw_hash,source,reason,at},识别 identity 的畸形帧留给 R5 quarantine)。
- session 超时 reconciler:扫 pending ∧ deadline 过→CAS pending→expired;赢→合成 run.failed dispatch_exhausted(session 唯一合法终态权场景)+billing release;输(已 claimed)→不动(执行中,lease 兜底)。
- `run.started` 最小 durable outbox(纲领 R1 范围):agent claim 成功即写 ledger outbox 行{run_id,event=run.started,published:false},publish 成功置 true;worker 启动 scanner 补发 unpublished(幂等:session 对 run.started 本就不投影浏览器,重复无害)。完整 durable_seq/receipt 体系留 R4/R5,本项不做。

## 验收

- R0 钉1 转 XPASS→去 xfail 收口为正式绿钉。
- 故障矩阵(§8.3 首三行):读出后 claim 前崩溃(未 ACK 可重投)/claim 后 ACK 前崩溃(重投帧 CAS 输→ACK 丢弃,不双执行)/XADD 后 dispatch 落库前(session 侧:先写 intent 再 XADD,该窗口消失——测试证明顺序)。
- 并发:pending→claimed 与 pending→expired 赛跑只一方赢;expired 后迟到帧永不执行;claimed 后超时方不写失败终态。
- 双仓全量只增不减;e2e 全绿(行为对 happy path 透明)。
