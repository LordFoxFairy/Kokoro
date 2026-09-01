# kokoro-session 设计卡

## 定位

浏览器面向的会话编排和传输运行时，不是通用业务领域服务。

## 架构等级

运行管道架构，不使用 L0/L1/L2 DDD 分类。

## 目标目录

```text
src/
├── ingress/             HTTP command admission
├── relay/               Agent wire -> session event
├── projection/          snapshot/pending pause projection
├── persistence/         Mongo store、seq、幂等
├── transport/           Redis live bus、SSE attach
├── recovery/            未终态 run recovery
├── contract/
├── config/
└── main.ts
```

## 关键边界

- Session 不执行 Agent。
- Session 不写 Credit、Payment、IAM 主表。
- 持久先于广播，store 是排序和幂等 owner。
- Session record 固化 immutable tenant + execution subject；每次**新 Launch**的服务端构造 `ExecutionIdentity(tenant_ref, actor, subject, identity_assertion_ref)` 必须与它匹配；Cleanup 只使用已接受 delete 写入 durable outbox 的 tenant-subject lifecycle envelope。Session 不保存、转发或选择 namespace/threadId；GA ingress 仅首次 target bootstrap（普通 Launch claim 或 fork `ForkConversation` prepare） 从 tenant + subject 派生内部 `RuntimeNamespace` 并固化 locator，后续新 Launch 验证后复用，Cleanup 校验 locator/fence，已 claim recovery/control 只用 ledger/locator，再以 `thread_id=session_id` 调用 LangGraph。项目 subject 可由不同已授权 actor 发起。
- 当前 actor access 由 Session/IAM 在产品入口判定：snapshot/history/SSE attach 要 `read`，新消息/Launch 要 `write`，matching HITL/cancel 要 `control`，delete 要 `delete`。fork 同时需要 source `read` 与 target `write`：Session 先创建同 scope/key target，再发最小 `ForkConversation(source terminal Run, target identity)`；GA private seed不返回产品面。SSE 的短期 decision 到期或收到成员撤销传播即关闭，重连重新授权。撤销不改写 GA checkpoint/locator；若需停止已 claim Run，System 走显式 cancel。已接受 delete 的 Cleanup retry 由 Session workload 用 delete-time durable lifecycle envelope 继续，不依赖原 actor后续仍是成员，也不构成新的 Launch/Tool/外部 owner 授权。
- 每次已认证的 matching HITL/cancel 在同一 Session transaction 写 `ControlAudit(actor, authorization_decision_ref, action, occurred_at)`；Root `ApplyControlRequest` 只携带其 opaque `control_audit_ref`，GA RunLedger 关联 ref/command receipt。它保留“谁控制了本次 Run”的审计链，不把 control 变成新的 ExecutionIdentity、namespace、Billing subject 或 GA membership query。
- `ProductSession.status=deleting/tombstoned` 是 Session projection 的最终 transaction predicate：deleting 只消费 matching active Run Terminal 推进 cleanup，tombstoned 对 GA ProductEvent/StudioJobEvent 一律 ack/drop；消息/run/card/cursor/SSE 不得被晚到 event 复活。最小 tombstone lifecycle row 覆盖 source redrive/replay 窗口，不是 Agent/graph 配置。
- Redis 是 Session transport/live bus 的运行时硬依赖；Redis 不可用时 Session 不接收新 run，不走内存替代，不伪造成功。

## 100 分证据

- relay、store、transport、recovery 的所有权和生命周期测试存在。
- SSE replay/live attach、断线、重复 event、终态恢复可验证。
- Agent wire contract 只在入站边界校验。
- 生成 Root command 不含 caller namespace/thread selector；个人/项目/服务 subject 均由可信 ExecutionIdentity 进入，Session record 固化 immutable tenant + subject，且 **Session record 不出现 RuntimeNamespace**。`billing_ref` 只可绑定 tenant + subject + Feature，GA accepted invocation 回执由 Billing 独立结算。
- Session 不出现业务扣费、模型路由或用户主数据逻辑。
- project 成员撤销矩阵可验证：后续 read/write/control 拒绝、已连 SSE 关闭且重连拒绝；已 claim GA Run 仍可独立 recovery，System cancel 才会中止它；撤销发生在 delete 已受理后不阻断同一 cleanup_id 的 Cleanup retry。
- 两个已授权 project actor 分别 Launch/Control 时，Launch actor 只进 admission audit，后续 control actor 只进 Session `ControlAudit` + opaque `control_audit_ref`；GA 不产生第二 namespace、Billing subject 或 IAM query。
- delete、CleanupThread、晚到 Launch 与晚到 ProductEvent/StudioJobEvent 的乱序均有正反例：GA cleanup fence 防 execution state 回生，Session tombstone gate 防展示投影回生。
- 当前 `src/relay/store/transport/http` 到目标目录的映射明确。


## 当前落地证据与迁移门禁

当前代码证据（只证明现状，不等于目标已完成）：

- `kokoro-session/src/relay`
- `kokoro-session/src/store`
- `kokoro-session/src/transport`
- `kokoro-session/src/http`

迁移完成前必须同时具备：

- schema 与唯一 owner / runtime writer 清单一致；
- 公开 contract、生成物和 consumer 清单一致；
- architecture test 能阻止越界 import、跨表写入和旧入口回流；
- unit、integration、contract test 覆盖本卡的核心不变量；
- 旧入口或旧写面已删除，或有明确的兼容截止版本和回滚方案。
