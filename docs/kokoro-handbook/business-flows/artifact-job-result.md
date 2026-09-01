# Artifact 与 Job Result 链路

状态：当前 Storage/Studio 产物链路，2026-08-23。Storage 的 owner、ObjectStore port 和 S3Workspace 分界见
[29 Storage/ObjectStore](../technical/29-capability-storage-runtime-architecture.md)；App/Feature/Studio 总图见
[37 App、Feature 与 Studio 架构](../technical/37-product-experience-agent-studio-architecture.md)。

## 一句话

```text
Studio owns Job and provider result.
Storage owns bytes, scan, Asset and Artifact lifecycle.
GA owns the Agent-side effect/evidence and only emits a durable JobRef link.
Session owns the user-visible projection/SSE card.
```

同一 MinIO/S3 集群可以存 sandbox 归档和用户产物，但它们不是同一种业务对象：GA `S3Workspace` 是可选
sandbox/workbench adapter；用户可见音频、图片、视频、代码或导出文件必须成为 Storage finalized Artifact。
Session、GA 或 Browser 都不读取/保存 bucket key、presigned URL 或 Storage 私表。

## 参与模块

| 模块 | 唯一职责 | 明确不负责 |
|---|---|---|
| Studio | Project、Job、provider submit/callback、Job terminal、safe JobSnapshot/JobEvent 与专业 UI command。 | Blob/Artifact 生命周期、GA checkpoint。 |
| Storage | Upload admission、scan、Asset、Artifact、ObjectStore、retention/delete。 | provider Job 状态机、Agent graph。 |
| GA | 在 Workflow policy 内创建 Studio Job，写 effect/evidence，投影 `StudioJobLinked(JobRef)`。 | Asset/Artifact 私表、bucket/object key、provider 生命周期、Job watcher。 |
| Session | 将安全 ArtifactRef/JobRef 投影成消息/card/SSE。 | Storage read/write、sandbox workspace、Studio provider state。 |
| System | App/Feature exposure、产品显示/权限。 | Artifact bytes 或 Agent runtime recipe。 |

## Studio Job 产生用户 Artifact

```text
1. GA Agent Feature 的已声明 CreateJob effect 以稳定 effect_id 和 operation-bound attestation 调用 Studio CreateJob。
2. Studio durable 创建 Job，选择 provider 并返回 opaque JobRef；同 effect_id 的重试返回同一 JobRef。
3. GA 记录 effect_id -> JobRef 并写安全 StudioJobLinked(JobRef) ProductEvent；GA 至此结束对该 Job 的运行时责任。
4. Session 为 JobRef 建立 Job card，先读 Studio JobSnapshot，再消费/replay StudioJobEvent(job_ref, event_id, revision, safe state)。
5. provider 输出可交付内容时，Studio 向 Storage 申请 CreateUpload/受控写入资格。
6. Storage 接收字节，CompleteUpload 后执行 scan，建立/更新 opaque AssetRef。
7. Studio 以通过 scan 的 AssetRef 请求 CreateArtifact -> FinalizeArtifact；Storage 写 canonical ArtifactRef，Studio 在后续 JobEvent 中关联它。
```

`ArtifactRef` 是跨仓唯一交换形态：opaque `artifact_id`、安全显示元数据和必要 digest/scan 状态。它不含 object key、
provider output URL、sandbox path 或签名下载 URL；需要内容时由 Storage public reader 重新授权。

## 读取、发布、导出与删除

```text
读取/下载  -> Storage 根据 Artifact lifecycle、visibility、caller 重新授权受控 reader/download。
Studio 展示 -> Studio 读取 Job/Project；Session 只展示 JobRef 所投影的安全 card。
发布/分享  -> System/Studio 的产品规则请求 Storage 改变 Artifact visibility/retention；不改 GA checkpoint。
导出       -> 以 finalized ArtifactRef 走 Storage export/download；不从 GA S3Workspace 或临时 sandbox 拿文件。
删除       -> owner 发 Storage retention/delete request；Storage 决定 bytes/metadata 清理时机。
```

Session delete/fork/archive 不携带 Artifact-delete 指令。Session delete 只在 active run terminal 后以 `CleanupThread`
让 GA 清理同一 Session 的 checkpoint/workbench/lock/private evidence，并 tombstone Session 自己的 Job card/cursor；Storage Artifact、Studio Job 和 Billing settlement
仍按各自 retention 留存。

## 一致性、计费与失败

| 情况 | 正确结果 |
|---|---|
| Provider 成功但 scan/finalize 失败 | Studio Job 记录交付失败或待处理；不伪造 ArtifactReady，GA/Session 只展示安全状态。 |
| ProductEvent/Studio Job event 乱序或重放 | Session 以 JobRef snapshot + replay 收敛；GA 依 event identity/seq 去重，Studio 以 JobRef/event_id 去重并以 revision 防倒退。 |
| GA/Session 断线 | Studio/Storage 的 Job/Artifact lifecycle 继续；Session 恢复后重读 snapshot/replay安全 event，GA 不必重开 Run。 |
| 旧 provider callback / Job state 冲突 | Studio owner 维持 canonical snapshot/revision；Session 不覆盖较高 revision 或 terminal-safe状态，记录可审计投影错误。 |
| Session delete 与 Job event 竞争 | Session 在 deleting 时停止 Job/Browser card 投影，只允许 matching active Run Terminal 推进 cleanup；tombstoned lifecycle row 令所有晚到 Job/Product event ack/drop，不复活 Session card/Run/SSE，Studio Job/Artifact 仍由 owner lifecycle 处理。 |
| parent Run cancel (`detached`) | GA terminal，但不取消已创建 Job；Studio 成功/失败继续以 JobEvent 投影。 |
| parent Run cancel (`request_cancel`) | GA 以 stable cancel-effect id 请求 Studio cancel；Studio/provider 决定实际 Job terminal，任何后续 event 不复活 Run。 |
| GA sandbox archive 失败 | 不影响已经 finalized 的 Storage Artifact；只记录 GA sandbox observability。 |
| Artifact delete | Storage 依生命周期执行；Job、ModelInvocation、effect/Billing evidence 按各自审计/结算策略保留。 |
| 计费 | GA reasoning 按 accepted ModelInvocation 计；GA usage receipt 以 `billing_subject`/可选 `billing_ref` 交给 Billing 结算，RuntimeNamespace 不参与 payer 选择；Studio Job 按 quote/hold/capture/release 计；用不同幂等 identity 防双扣。 |

## 验收

```text
任一用户可见文件都经过 Storage CreateUpload -> CompleteUpload/scan -> CreateArtifact -> FinalizeArtifact。
GA、Session、Browser contract 中不存在 Storage bucket/object key、sandbox path 或 provider raw output URL。
Agent Feature 与 Studio direct control 共享一套 Studio Job/Storage Artifact lifecycle。
StudioJobLinked、StudioJobSnapshot/StudioJobEvent 只含 canonical ArtifactRef/JobRef 和安全 card metadata；Session restart/SSE reconnect/replay 不重复或回滚卡片，也不泄露 execution evidence。
Run terminal 后 Studio Job event 只更新已关联 card，不能复活 Run 或发送 assistant 文本；Session delete/fork/archive tombstone 自己的 card/cursor 而不递归删除 Artifact，delete 后的晚到 ProductEvent/StudioJobEvent 由 Session tombstone gate ack/drop；GA target S3Workspace workbench 失败只影响 `durable_required` 的 GA execution，不影响已交付 Artifact；V1 `S3Archiver` archive 缺席或失败同样不影响 Artifact。
```
