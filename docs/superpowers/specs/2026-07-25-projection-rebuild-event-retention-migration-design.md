---
artifact: architecture-design
version: "1.0"
created: 2026-07-25
status: internal-review-active
scope: outbox-inbox-event-retention-projection-rebuild-backfill-snapshot-schema-migration-cutover-dr
implementationAuthorized: false
gaRuntimeSemanticChangeAuthorized: false
---

# Projection Rebuild、Event Retention 与 Migration

## 1. Purpose

Kokoro的Session页面、TaskView、Library/Search、Admin timeline、Notification状态、Usage/Cost、Credit balance、Fleet和Support均使用
read projection。本文冻结projection的source、watermark、event retention、snapshot/backfill、双版本consumer、校验、限速、切换和DR，
防止“数据库migration成功”被误当成产品状态可恢复。

## 2. Invariants

1. projection不是业务真源，不拥有mutation、authorization或external effect。
2. 每个projection字段可追溯到owner aggregate/event/schema revision和source watermark。
3. rebuild/replay只重算projection/participant，不重复Provider、Payment、Grant、Notification delivery、Target或GA effect。
4. event duplicate/out-of-order/late/replay以aggregateVersion和inbox reducer确定性收敛。
5. consumer schema升级支持current/previous窗口；不兼容数据fail/quarantine，不silent drop/coerce。
6. cross-Site events、snapshots、indexes、cursors和backfill jobs严格partition且不泄漏存在性。
7. cutover必须有shadow comparison和可回滚authority switch，不能长期双主写。

## 3. Projection inventory

每个ProjectionDefinitionRevision登记：

```text
projectionId / revision / owner / purpose
source aggregate+event types / accepted schema versions
partition key / site scope / ordering requirements
reducer+code digest / storage schema+index revision
field lineage / security classification / redaction policy
freshness+completeness SLO / retention
snapshot strategy / rebuild command / throttle policy
validation invariants / comparison tolerance
consumers / API+cursor versions
runbook / dashboard+alerts / Data Rights participant
```

最低inventory：

- SessionSnapshot/Message/Run/Interaction projection。
- TaskView/Task timeline/search。
- Library/Lineage/Search/Quota/Share projection。
- Credit Balance/Grant↔Usage/Hold aging。
- Usage/Cost/Settlement projection。
- Notification Request/Delivery/Preference projection。
- Admin safe timeline/queues/approvals/audit search。
- Site Fleet/Release/DeploymentObservation。
- Support Case safe timeline和Data Rights coordinator status。
- Model/Capability health、assignment和route explanation。

## 4. Event and source contract

- owner transaction原子提交domain facts+outbox；projection不能从业务表轮询猜change作为唯一机制。
- event envelope使用eventId、siteId/platform scope、aggregateId/version、occurred/recorded time、schema、correlation/causation和classification。
- source aggregate version单调；同version不同payload digest是P0 integrity incident。
- consumer inbox key=`consumerId + eventId + handlerRevision`，receipt记录processed/skipped/quarantined和resulting watermark。
- cross-aggregate join projection分别保存source watermarks/partial state，不伪造global atomic snapshot。
- event只陈述已提交fact；`send_email`、`retry_provider`等command不能伪装成可安全replay的domain event。

## 5. Retention tiers

### Owner facts

按domain/legal/accounting policy长期保留，是rebuild最终authority。例如Credit Journal、Payment Fact、ArtifactVersion、Run terminal。

### Transactional outbox

至少保留到所有required consumers确认并超过最大rebuild/DR窗口；归档前生成range manifest、count/hash和storage receipt。

### Transport log

Redis Streams/JetStream等只是delivery层，可短于owner/outbox retention；不能作为唯一rebuild source。

### Consumer inbox

保留覆盖producer replay和incident窗口的dedupe identity；压缩/归档仍需证明旧event不会重触发effect。

### UI/SSE journal

有界reconnect evidence；过期后完整snapshot，不依赖全历史SSE。

- 每tier冻结duration、region、encryption、LegalHold、Data Rights、archive/restore和destruction receipt。
- 删除event payload前验证是否仍有projection只能依赖该payload；缺owner source则retention不能缩短。
- schema registry和decoder必须至少保留所有仍可replay/retained event版本。

## 6. Rebuild protocol

```text
CreateProjectionRebuildCommand
→ freeze ProjectionDefinition + target schema + source cut watermark
→ create isolated shadow storage/index
→ load owner snapshots/backfill pages at stable read watermark
→ replay outbox/events after snapshot watermark
→ catch up live dual-consume into shadow inbox
→ validate counts/hashes/invariants/sample diffs
→ canary reads/shadow compare
→ authority switch CAS
→ monitor / rollback reads if needed
→ retire old projection after compatibility+retention window
```

- rebuild identity+definition digest幂等；response loss查询same job，不创建两个shadow authority。
- source snapshot使用repeatable read/exported snapshot、owner pagination watermark或领域定义的consistent scan。
- pagination按stable primary key/version，不使用offset在并发写中跳/重。
- live events arriving duringbackfill进入shadow inbox并按aggregateVersion等待/应用，不能漏gap。
- gap detection列出missing aggregate/version range并从owner/outbox补取；不能用“最新值覆盖”隐藏缺失历史。
- rebuild output隔离，未通过validation不服务production reads。

## 7. Reducer and ordering

- reducer是pure/idempotent对`current projection + owner fact/event`的确定性转换，外部effect禁止。
- aggregate event按version应用；duplicate同digest no-op，不同digest quarantine。
- late event若被新erversion supersede，仍验证lineage/invariants并记录handled reason，不last-write-wins。
- delete/tombstone/retention/legal hold/restore使用explicit fact，不通过row missing猜测。
- clock/time字段不用于业务ordering，occurredAt可晚到；recordedAt只作观测。
- cross-source projection定义join completeness和staleness budget，例如Job completed但Cost pending、Share revoked但Purge partial。

## 8. Schema and consumer migration

- storage migration采用expand→backfill→dual-read/shadow→switch→contract，不直接rename/drop breaking field。
- producer event新required语义先发布newversion；current/previous consumers通过contract matrix后再切producer default。
- generated TS/Python schemas与decoder digest进入release evidence；手工mapper必须有golden/negative tests。
- unknown security/effect-critical字段fail closed；optional display字段可保留unknown/omit但显示partial/freshness。
- backfill写使用owner-independent projection tables/index，不触发业务outbox、updatedAt、notifications或hooks。
- contract阶段前验证没有旧client/consumer/read path；consumer inventory是machine-readable gate。

## 9. Authority switch and rollback

- switch对象冻结old/new projection revisions、watermarks、validation report、API/cursor compatibility和expected active revision。
- canary按Site/tenant/partition，不用同request随机读两个authority产生闪烁。
- rollback只切read routing回old projection；不撤销owner facts或重放external effects。
- switch后new projection持续比较old/owner samples至少一个发布窗口；差异有severity/owner/SLA。
- cursor/index token绑定projection revision；switch时compatible translate或返回snapshot/query restart，不silent错页。
- old projection在retention/rollback/incident窗口后由Data Governance计划删除。

## 10. Large backfill and fairness

- backfill按Site/partition公平调度，有read IOPS/CPU/DB replica/index/write/event catch-up budgets。
- interactive production traffic优先；lag超过阈值自动pause/throttle，不把primary压垮。
- hot Site拆分bounded ranges但保持aggregate ordering；不能一个大Site阻塞所有Site。
- progress以known denominator/watermarks表示，不用不可信百分比。
- cancel只停止future pages；已写shadow可resume/expire cleanup，不影响active projection。
- paid Provider/GA/Connector不参与backfill；任何需要重新计算AI output必须新visible Operation而非migration。

## 11. Validation

最低validation：

- source aggregate counts、version ranges、tombstones、required participant coverage。
- partition/siteId、authorization/redaction字段完整性。
- deterministic range hash/Merkle或domain-specific balance proof。
- Credit double-entry、Hold allocation守恒、Usage settlement uniqueness。
- Session message/run/interaction/branch ordering和terminal exactly once。
- TaskAnchor唯一、child lineage和ownerRef可解析。
- Artifact lineage DAG、Blob refs、retention/Share restriction。
- Notification source intent→request→delivery状态不重复。
- sampled API response diff、cursor pagination和freshness。

tolerance只能用于非authority display/浮点derived metric并有owner批准；money/Credit/Site/permission/terminal/Decision差异为0 tolerance。

## 12. Disaster recovery

- backup包含owner DB、outbox archive、schema/decoder registry、projection definition和必要projection snapshots。
- restore先恢复owner truth与high-water，再决定projection restore或全rebuild；不能只恢复cache/index宣称可用。
- DR提升新region前fence old writers、outbox producers和projection switch epoch。
- old cursor/inbox/lease跨restore boundary按epoch失效或显式迁移。
- RPO gap产生known missing range/reconciliation，不生成默认success/zero balance/empty Session。
- DR演练证明target RPO/RTO、rebuild throughput、external effect dedupe和two-Site isolation。

## 13. Data Rights、retention and security

- projection是Export/Delete participant；coordinator按field/source policy删除、deidentify或保留，并收participant receipt。
- owner fact被LegalHold保留时projection可删除敏感display字段但保留safe hold status；不复制raw evidence到read models。
- rebuild worker使用least-privilege、environment/region/Site-scoped workload identity；无Provider/Payment/GA effect credential。
- shadow storage与debug diff同等级加密/访问/retention；不能因“临时迁移”复制全量PII到工程bucket。
- Admin查询跨Site rebuild需GlobalScope+reason+audit；普通operator只看Site/queue safe projection。

## 14. Operations and commands

- typed commands：StartProjectionRebuild、Pause/ResumeRebuild、ValidateProjectionCandidate、SwitchProjectionAuthority、
  RollbackProjectionRead、QuarantineEventRange、ReplayAuthorizedRange、RetireProjectionRevision。
- switch/rollback/retire/mass replay使用maker-checker、dry-run、expectedVersion、blast radius和per-partition receipt。
- 禁止直接改watermark、跳过missing range、清Inbox后重放、在active table手工补row或将validation差异mark ignored无expiry。
- metrics：source/outbox/transport/inbox lag、rebuild throughput/ETA、gap/quarantine、validation diff、shadow freshness、switch errors、
  DB/index load、Site fairness和Data Rights backlog。

## 15. Acceptance criteria

### AC-PROJ-01 — Full rebuild converges without effects

```gherkin
Given an empty shadow projection and retained owner facts/outbox
When snapshot, replay and live catch-up complete
Then validation proves the same authority-derived state and watermarks
And no Provider, Payment, Grant, Notification delivery, Target or GA effect is invoked
```

### AC-PROJ-02 — Backfill/live race loses no version

```gherkin
Given an aggregate changes while its snapshot page is being copied
When the shadow consumer catches up
Then stable snapshot and aggregateVersion ordering apply every required version exactly once semantically
And gaps or digest conflicts quarantine instead of latest-value overwrite
```

### AC-PROJ-03 — Cross-Site data never enters candidate

```gherkin
Given two Sites have matching aggregate IDs, emails, hashes or timestamps
When backfill, event replay, index build and validation run
Then every row, key, cursor and query remains in the immutable source Site partition
And no count, content, permission or timing signal crosses Sites
```

### AC-PROJ-04 — Authority switch is reversible

```gherkin
Given a validated candidate serves canary reads
When an unexpected read regression appears after switch
Then routing can return to the old projection revision by CAS without changing owner facts
And cursors receive an explicit compatible translation or restart requirement
```

### AC-PROJ-05 — Credit and terminal facts have zero tolerance

```gherkin
Given candidate validation compares Credit, Usage, Run and Job projections
When any balance, allocation, settlement, terminal or Site authorization differs
Then switch is blocked and the exact source/version gap is reported
And no accepted-risk tolerance can promote the candidate
```

### AC-PROJ-06 — Data Rights survives rebuild

```gherkin
Given a subject deletion, restriction or LegalHold is active during rebuild
When candidate projection materializes and switches
Then current deletion/redaction/hold rules apply with participant receipts
And shadow or archived data cannot resurrect removed fields or access
```

## 16. Verification and release gates

- property：random event duplicate/order/gap/tombstone/replay、deterministic reducer和range hash。
- integration：large owner snapshot+live writes、schema current/previous、cursor/index switch和throttled backfill。
- domain：Credit balance, Session/TaskView, Library/Artifact, Notification, Admin/Support, Fleet/Model projections。
- chaos：worker crash、outbox/transport/index outage、switch failure、DR restore、region fence和Data Rights race。
- security：cross-Site/environment, shadow access, PII/redaction, workload scope, archive/decoder integrity。
- operations：production load/fairness、pause/resume/cancel、maker-checker、dashboard/alert/runbook和RPO/RTO。

No-Go：projection写真源；replay触发effect；全历史SSE作唯一source；offset分页backfill；latest覆盖gap；长期dual-write；
silent schema coercion；money/terminal差异容忍；跨Site shadow；手改watermark；只恢复index；迁移临时bucket无治理。

## 17. Related documents and approval boundary

- [Platform Modular Core/Internal RPC](2026-07-25-platform-modular-core-internal-rpc-design.md)
- [Session HTTP/SSE Transport](2026-07-25-session-http-sse-production-transport-design.md)
- [PRD-10 Admin](2026-07-25-prd-10-admin-operating-console.md)
- [PRD-15 Data Rights](2026-07-25-prd-15-notification-preferences-and-data-rights.md)

本文批准不授权migration、replay或authority switch。projection方案不得修改GA runtime；GA只作为RunExecution/Agent event的owner
source之一，rebuild不能请求GA重跑graph、tool、model或checkpoint。
