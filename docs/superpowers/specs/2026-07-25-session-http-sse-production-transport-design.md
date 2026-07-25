---
artifact: architecture-design
version: "1.0"
created: 2026-07-25
status: internal-review-active
scope: session-http-snapshot-sse-cursor-auth-backpressure-drain-retention-observability
implementationAuthorized: false
gaRuntimeSemanticChangeAuthorized: false
---

# Session HTTP/SSE Production Transport

## 1. Purpose

本文冻结Site Web BFF到Session的生产HTTP、snapshot与SSE合同。它替换当前“snapshot省略messages、非法cursor全量回放、
浏览器依赖全历史SSE重建”的行为目标，但不在当前阶段授权代码修改。

Session仍只拥有Session/Message/Run/Interaction/Event projection与浏览器传输，不执行GA、不路由模型、不扣Credit、不解释
Site商业配置。GA runtime wire、event kind/order、terminal、checkpoint、cancel与namespace语义不在本文修改范围。

## 2. Current evidence and target correction

当前`kokoro-session/src/http/INDEX.md`明确：

- `owner=namespace=payload.sub`。
- 属主snapshot省略messages。
- Web依靠SSE事件史全量回放重建。
- 非法Last-Event-ID退化为全量回放。

这些是当前实现事实，不是目标合同。目标态必须：

1. 使用SessionAccessGrant和独立authorization projection，不再把namespace当owner。
2. snapshot是完整长期页面projection。
3. SSE只负责snapshot watermark之后的增量与有界replay。
4. malformed、expired、cross-Site cursor返回typed recovery，不触发无界历史扫描。

## 3. API surface

```text
GET  /v1/sessions?cursor&limit&projectRef&state
POST /v1/sessions
GET  /v1/sessions/{sessionId}
POST /v1/sessions/{sessionId}/messages
POST /v1/sessions/{sessionId}/runs/{runId}/controls
GET  /v1/sessions/{sessionId}/runs/{runId}/controls/{decisionId}
GET  /v1/sessions/{sessionId}/snapshot
GET  /v1/sessions/{sessionId}/events?after={eventCursor}
```

- BFF到Session使用audience-bound SessionAccessGrant和workload identity；浏览器不得直接提供siteId/namespace作为证据。
- mutation统一支持idempotency key、body digest、expectedVersion（适用时）与safe receipt query。
- response envelope冻结`requestId/correlationId/errorCode/retryClass/safeDetails/freshness`；不返回堆栈、存在性或内部owner ID。
- 401/403/404对未授权资源使用non-disclosure profile；合法主体才可区分deleted/gone/conflict。
- 所有不可信入参使用strict runtime schema；unknown fields、limit、cursor size、body size在BFF和Session双重限制。

## 4. Complete snapshot contract

```text
SessionSnapshotRevision {
  siteId-scoped server identity
  session metadata + current revision
  ordered Message projections and typed parts
  Run summaries + current active/terminal states
  pending Interaction/HITL projections
  referenced Job/Artifact handles and safe state
  branch graph/current branch
  cost projections/freshness refs
  projectionVersion
  snapshotWatermark = durable session event sequence
  generatedAt / retention+schema revision
}
```

- snapshot必须在干净浏览器、无local state和无历史SSE时完整还原当前页面。
- snapshot内容来自Session owner projections；不可通过请求GA checkpoint或重跑模型补齐。
- messages可分页，但首屏snapshot必须冻结明确window、before/after cursor与完整性标记；客户端不能猜“遗漏=不存在”。
- typed parts保留stable message/part/tool/interaction IDs；受限内容使用owner-issuedredacted projection，不泄漏raw payload。
- snapshot读取与watermark必须具有一致性边界：事务snapshot、read timestamp或可证明的high-water protocol。客户端先应用snapshot，
  再只应用`seq > snapshotWatermark`事件，竞态不能漏或重复effect。
- schema不兼容返回typed `client_upgrade_required`或supported migration，不发送浏览器无法解释的部分snapshot。

## 5. SSE event and cursor contract

### 5.1 Durable ordering

- 每个Session有单调durable `sessionEventSeq`；event在广播前先append成功。
- transport可能重复发送，客户端按`sessionId + seq + eventId`幂等应用；系统不承诺网络exactly-once。
- live-only token delta若不durable，不能成为恢复后唯一业务事实。Message/tool/interaction/terminal最终projection必须durable。
- terminal event每Run只由Session对GA canonical terminal投影一次；SSE断线、BFF重连或deploy不能创造terminal。

### 5.2 Opaque cursor

`EventCursor`是签名/认证opaque token，绑定：

- siteId、sessionId、subjectGeneration、streamEpoch。
- last durable seq、snapshot/schema revision、issued/expiry。
- audience、key revision与optional grant family。

客户端不得修改seq或跨Session/Site/subject复用。HTTP`Last-Event-ID`可携cursor，query`after`为fetch/polyfill兼容；两者同时存在
且不一致时返回`cursor_conflict`，不选择“更大值”。

### 5.3 Cursor failures

| Failure | Response |
|---|---|
| malformed/signature invalid | 400 `invalid_cursor`；不回放 |
| wrong Site/session/subject | non-disclosing 404/403 profile；security audit |
| seq ahead of durable head | 409 `cursor_ahead`；重新snapshot |
| replay retention expired | 409 `snapshot_required` + safe snapshot URL |
| stream epoch/schema incompatible | 409 `snapshot_required`或`client_upgrade_required` |
| valid cursor, no new event | 建立tail并heartbeat，不立即关闭 |

非法cursor绝不退化成从seq 0扫描；这既防止误重复，也防止历史放大DoS。

## 6. Connection lifecycle

### 6.1 Headers and proxy profile

- `Content-Type: text/event-stream; charset=utf-8`。
- `Cache-Control: no-store, no-transform`，禁止CDN缓存/压缩/内容变换。
- reverse proxy buffering关闭，flush headers和每帧及时flush。
- `Connection`、HTTP/2/3行为按ingress认证；不依赖hop-by-hop header穿透。
- CORS只允许当前Site origin；目标态浏览器经same-origin BFF，不向公共Internet暴露Session workload endpoint。

### 6.2 Heartbeat and idle

- comment heartbeat默认15s，必须小于最短已认证proxy idle timeout的一半；不推进event cursor。
- heartbeat jitter避免pod同步尖峰；连续write/transport失败立即释放subscription和authorization resources。
- client inactivity不等于Run cancel。SSE断开只结束view transport；Run/Job按owner command收口。
- server可发送typed`stream.draining`控制frame，给出reconnectAfter和last durable cursor，但不是业务event。

### 6.3 Backpressure and slow consumer

- 每connection使用有界byte/event buffer；不得让Node writable queue或Redis subscriber无限增长。
- durable events达到high-water时暂停读取或关闭slow consumer；不能丢弃terminal/HITL/Message事实后继续假装同步。
- token delta可按协议coalesce，但不能跨message/tool-call ID、改变顺序或覆盖durable boundary。
- 关闭使用typed reason/metric；客户端以last acknowledged durable cursor重连。server不得为追赶slow consumer重跑GA。
- per-connection、per-subject、per-Site、per-IP与global quotas由SiteRelease/Support tier冻结；返回429含safe retry-after。
- interactive用户与后台observer使用独立quota class，防止一个Site/noisy tab耗尽全部connections。

## 7. Authentication、revocation and reconnect

- SSE建立和每个sensitive control/read使用SessionAccessGrant；长连接在heartbeat/epoch update处检查expiry/revocation。
- grant轮换不改变session cursor identity；新grant必须覆盖同Site/session/subject generation和action。
- membership remove、subject generation、AuthSession revoke、Site suspend与restriction epoch更新在发布SLO内终止旧connection。
- BFF workload credential和user grant分别认证，任一缺失失败；不能用CORS代替auth。
- reconnect使用指数退避+jitter与server retry hint；401/403/409/426不盲目自动循环。
- 多tab默认复用浏览器leader/shared connection或计入明确quota；tab takeover保持cursor和focus/read anchor，不复制control mutation。

## 8. Retention and replay

- Session Message/Run/Interaction是真源；SessionEvent replay journal是有界transport evidence，不是永久data lake。
- retention必须覆盖发布的offline reconnect window、deploy drain和常规incident recovery；具体时长由Profile/region/data policy冻结。
- journal过期后snapshot恢复，不回退GA event history。LegalHold/Data Rights分别作用于真源和journal participant。
- purge按siteId/session partition并有receipt；不能因删除transport journal破坏Message/Run权威或审计required facts。
- replay读使用bounded page/byte/time budget；大backlog先snapshot再tail，不一次把全部历史压入connection。

## 9. Deploy、drain and disaster recovery

- readiness false先停止接新connection，再发送draining frame，等待短grace后关闭；不终止Run/Job。
- rolling deploy期间新pod可从durable store+live bus接续；pod memory不是cursor/terminal authority。
- event append成功但broadcast前crash：reconnect从durable seq补发。
- broadcast前append失败：不得广播业务event；producer/reconciler按owner identity恢复。
- Redis/live bus outage：durable append继续或按capacity fail admission；现有connection不得伪造丢失事件，恢复后按seq catch up。
- Mongo/event store outage：不能接受需要durable event的新Run/Message；返回typed unavailable，不切换memory truth。
- DR restore冻结restored high-water、stream epoch和cursor invalidation；旧cursor不能越过restore boundary静默继续。

## 10. Observability and SLO

最低metrics：active/open/close connections、open latency、heartbeat/write failure、buffer bytes、slow consumer、429、reconnect、
cursor errors/expiry、replay events+bytes+latency、snapshot size/latency、append-to-visible lag、revocation lag、drain duration和leak count。

- dimensions包括Site/Profile/region/client class/schema revision，但不含user/session/message ID高基数label。
- trace使用safe correlation refs，不记录grant/cursor/raw event content。
- 目标基线：10k并发/24h soak无unbounded memory/fd/subscription leak；p99 append-to-visible和reconnect由Profile冻结。
- alert必须连接runbook：proxy buffering、replay storm、cursor signing failure、revocation lag、slow-consumer surge、Redis/Mongo outage。

## 11. Verification matrix

- snapshot：empty/large/branched/HITL/Job/media/restricted/cost-pending，干净浏览器无需历史SSE完整水合。
- cursor：malformed/ahead/expired/wrongSite/wrongSubject/key rotation/schema epoch/Last-Event-ID与query冲突。
- race：snapshot与append、append与broadcast crash、terminal与disconnect、control与revocation、drain与reconnect。
- transport：HTTP/1.1/2、ingress/CDN、buffering、idle、mobile background、network switch、multi-tab、slow reader。
- load：10k/24h、per-Site noisy neighbor、backlog catch-up、heartbeat jitter、rolling deploy与live bus outage。
- security：CORS bypass、grant/cursor replay、cross-Site enumeration、log/metric leakage、oversized body/cursor/backlog DoS。
- accessibility：reconnect/progress/terminal live region不重复轰炸，focus/read anchor稳定，reduced-data提示可用。

## 12. Rollout and compatibility

1. 先增加完整snapshot与watermark，不删除旧SSE重建路径。
2. Web双读对比projection，记录不一致但不双写control/effect。
3. 发布opaque cursor与typed snapshot-required；验证BFF/proxy/client compatibility。
4. 切Web authority到snapshot+incremental SSE。
5. 观察完整retention window后删除全历史回放依赖与owner=namespace auth shortcut。
6. 每阶段可按SiteRelease回滚client/projection；不得回滚到跨Site或无auth模式。

## 13. Related documents and approval boundary

- [Platform/Web/Session P0 closure](2026-07-25-platform-web-session-p0-contract-closure-design.md)
- [Platform/Web/Session target architecture](2026-07-25-platform-web-session-target-architecture-design.md)
- [PRD-05 Chat](2026-07-25-prd-05-chat-conversation-run-and-interaction.md)
- [PRD-15 Data Rights](2026-07-25-prd-15-notification-preferences-and-data-rights.md)

本文批准不授权实现。任何为了cursor/replay而修改GA event kind/order、checkpoint、terminal、cancel或namespace的方案必须停止并
进入GA专项审批；本文预期所有改动均留在Web/BFF/Session transport与projection边界。
