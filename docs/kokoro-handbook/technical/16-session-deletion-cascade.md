# 会话删除（V2-M1 实施规格：软删除）

- 状态：实施规格（2026-07-06 裁定修订：**软删除**——session 打状态位即完成；
  **agent 侧一概不动**（checkpoint/工作区/ledger 原样保留，磁盘不是稀缺项）；
  冷数据归档不做）
- 取代 technical/15 §2A 的硬删级联 saga（该方案作为"若未来需要物理清除"的
  留档，不实施）
- 报告：`docs/reports/m1-session-deletion-*.md`

## 1. 设计一句话

**删除 = sessions 文档上的一个状态位。** 一次 Mongo 条件更新，天然幂等、
天然多 pod 安全（任何副本执行同一更新收敛同一结果），零分布式协调、零新流、
零 agent 改动。数据全部保留（可恢复/可审计），物理清除永远是将来另一个
显式决策。

## 2. 契约

```text
http.yaml 增一：DELETE /sessions/{session_id} → 202 {status: "deleted"}
  路径与 snapshot 相同（snapshotPath 复用），幂等：不存在/已删除同样 202。
control/streams/events：零改动。agent 契约面零改动。
```

## 3. session 侧

```text
DELETE 受理：
  ① 有 activeRunId → 发既有 run.cancel（进行中的 run 正常收口，不留孤儿流）
  ② sessions doc 置 status="deleted"（幂等条件更新）
  ③ 202 {status:"deleted"}
读写闸（deleted 会话四路 410 session_deleted）：
  POST messages / GET snapshot / GET events / GET files
  （control 无需专闸：cancel 后无活跃 run，既有校验自然拒绝）
文档保留：messages / session_events / pauses / runs 全部原样——软删语义。
```

## 4. web 侧

```text
deleteConversation：本地乐观移除照旧 + fire-and-forget DELETE（失败仅
console.error；列表真源仍在本地，服务端列表化随 P1 鉴权主线）。
```

## 5. 多 pod 论证（软删后全部平凡化）

```text
删除时 run 在别的 pod 跑   run.cancel 走既有链（chaos 已实证）；即使 cancel 帧丢失，
                          run 跑完终态写入的是"已软删的会话"文档——无害，数据本就保留。
并发重复删除              条件更新幂等，任意副本任意次数同一结果。
删除与新消息并发          写闸在受理点 410。
需要恢复                  status 位翻回即可（数据未损）。
```

## 6. 测试用例矩阵

```text
L1-session  SD-S1 DELETE：活跃 run 收到 cancel + status=deleted + 202
            SD-S2 幂等：重复 DELETE / 删除不存在的会话 → 同样 202
            SD-S3 deleted 会话：POST messages / snapshot / events / files → 410 session_deleted
L1-web      SD-W1 deleteConversation 触发 client.deleteSession；本地移除不依赖网络成败
L2-e2e      E2E-27 终态会话删除：DELETE 202 → snapshot 410 → 新消息 410 →
                  工作区文件仍在磁盘（软删不动产物，agent 侧零变化的显式断言）
            E2E-28 暂停中删除：ask_user 暂停 → DELETE → run 收敛 cancelled →
                  snapshot 410，worker 无异常
L5          走查：侧栏删除 → 刷新不复活（服务端 410 而非仅本地遗忘）+ 截图存证
```
