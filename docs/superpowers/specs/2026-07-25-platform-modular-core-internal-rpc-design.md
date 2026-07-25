---
artifact: architecture-design
version: "1.0"
created: 2026-07-25
status: internal-review-active
scope: platform-modular-core-transaction-port-remote-rpc-event-workload-identity-extraction
implementationAuthorized: false
gaRuntimeSemanticChangeAuthorized: false
---

# Platform Modular Core 与 Internal RPC

## 1. Decision summary

Kokoro采用“模块化Platform Core + 独立执行process roles”，但不承诺本地interface能原样替换为RPC：

```text
same bounded context + same database transaction
  → transaction-scoped application port
  → one Unit of Work / one commit

cross bounded context or process
  → versioned remote command/query contract
  → owner-local transaction
  → outbox/inbox facts or explicit saga
```

未来提取服务必须重画aggregate owner、consistency、failure state与recovery；禁止用network adapter伪装原子本地事务。

本文不创建`operation-kernel`或万能service layer。Operation、Job、Credit、Payment、Session、Trust等继续由各自owner管理。

## 2. Runtime containers

```text
Platform API / Worker process
  modules/
    identity
    site_fleet
    workspace_project
    catalog_offering
    commerce
    credit_usage
    model_control
    trust
    notification
    data_governance
    admin_facade
  shared/
    request_security_context
    transaction_uow
    outbox_inbox
    contract_runtime
    observability

Independent process roles
  Session
  Job Worker / Scheduler
  Model Gateway
  Capability Runtime / Hub write plane
  GA Runtime
  Artifact/Asset workers where isolation requires
```

- 目录表达logical owner，不自动等于deployment service。
- Platform modules同process、同PostgreSQL cluster但schema/table ownership隔离；跨module读取使用owner port/projection。
- Session、Job、Gateway、Capability、GA因伸缩、故障或effect边界使用remote contracts。
- 一个process可托管多个role，但每个role仍使用独立workload audience、queue、quota与health signal。

## 3. In-process transaction ports

### Contract

- 仅同一bounded context/application workflow可传`TransactionContext`或`UnitOfWork`。
- port输入输出为strict domain/application types，不接受HTTP envelope、raw dict、ORM entity或transport error。
- repository只在owner module可见；禁止跨module import Prisma client/model、private table或transaction handle。
- workflow在一个UoW中完成需要强一致的aggregate变化、domain events和outbox append。
- port不能执行unbounded network I/O；Provider/RPC intent先durable，commit后由worker推进。
- nested transaction只允许明确savepoint policy；默认加入现有UoW，不能偷偷独立commit。

### Failure

- validation/conflict/policy deny在commit前返回typed domain error。
- DB serialization/deadlock按相同command identity有界重试；业务conflict不自动重试。
- commit outcome unknown先查询idempotency receipt，不重新生成command ID。

## 4. Remote command/query contract

### Command envelope

```text
RpcCommandEnvelope {
  contractId / schemaVersion
  commandId / idempotencyKey / requestDigest
  callerWorkload / audience
  immutable siteId or explicit platform scope
  actor/delegation safe refs
  correlationId / causationId / traceContext
  expectedVersion?
  issuedAt / deadline / attemptOrdinal
  restriction/security epochs
  payload
}
```

- caller不能自签Site/actor/scope；边缘从RequestSecurityContext派生，内部delegation逐hop收窄。
- owner在effect point验证audience、workload、Site、scope、epoch、deadline、digest与expectedVersion。
- 同command/idempotency identity相同digest返回同receipt；不同digest拒绝。
- timeout只表示caller未收到结果，不证明owner未commit。下一步必须`GetCommandReceipt`或owner-specific reconcile。
- command response只表示accepted/committed/rejected/unknown和owner receipt，不把queue accepted冒充业务completed。

### Query envelope

- query携带audience、Site/scope、field policy、consistency/freshness要求、deadline和pagination cursor。
- cross-Site unauthorized与not-found采用non-disclosure profile。
- projection query返回source owner、revision、observedAt、freshness与partial/unknown；不能伪装strong read。
- cursor绑定Site、query digest、sort/schema revision与expiry，不跨caller复用。

## 5. Error and retry profile

统一safe error taxonomy：

| Class | Example | Retry |
|---|---|---|
| validation | schema/unsupported parameter | no；修正请求 |
| unauthorized/non-disclosing | audience/scope/Site | no；security audit |
| conflict | expectedVersion/digest | no automatic；refresh/reconfirm |
| throttled | quota/concurrency | only after bounded retry-after |
| unavailable_pre_effect | owner not accepted | transport retry with same identity |
| accepted_pending | durable intent exists | query receipt；do not resubmit new identity |
| outcome_unknown | commit/effect uncertain | reconcile same identity；no fallback |
| terminal_failed | canonical owner failure | new visible operation only if product permits |

- retry classifier是contract registry字段，不由client按HTTP 5xx猜测。
- deadline沿调用链只收紧；下游必须留出receipt persistence和response budget。
- circuit breaker只阻止新admission，不把unknown effect重路由到另一个owner/provider。

## 6. Workload identity and transport

- service-to-service使用短期workload credential、mTLS或等价authenticated channel与audience-bound token。
- identity绑定service/role/environment/region/release revision；pod IP、network location或shared API key不是identity。
- key/certificate rotation支持overlap window、revocation和old-key negative tests；secret只以SecretRef进入runtime。
- production/staging/local audiences严格分离；相同siteId/commandId不能跨environment replay。
- ingress、service mesh或gateway只提供transport identity；domain owner仍执行Site/resource/epoch authorization。
- payload size、compression、decompression ratio、header count、concurrency和deadline均有边界。

V1可使用HTTP/JSON或Connect/gRPC，但contract source、semantics和auth不依赖具体framework。选择标准：

- Browser/public edge：HTTP/JSON/SSE。
- 内部request/response、typed streaming：Connect/gRPC或严格HTTP adapter。
- durable facts：owner outbox→transport→consumer inbox。
- 不为同process Platform modules做self-RPC。

## 7. Event contract

```text
DomainEventEnvelope {
  eventId / eventType / schemaVersion
  producer / environment / region
  immutable siteId or platform scope
  aggregateType / aggregateId / aggregateVersion
  occurredAt / recordedAt
  correlationId / causationId
  securityClassification
  payload
}
```

- event只陈述owner已提交事实，不发“请消费者完成owner事务”的伪事件。
- producer transaction原子append outbox；consumer以eventId+consumer+handlerRevision inbox去重。
- partition key确保同aggregate必要顺序；跨aggregate无全局顺序承诺。
- duplicate、out-of-order、late和replay必须由versioned reducer处理，禁止last-write-wins覆盖authority。
- retention、DLQ、max attempts、poison quarantine、replay owner和authorization进入machine-readable registry。
- DLQ不是terminal；每项有user impact、owner、next safe action和SLA。
- replay只重建projection/participant，不重复Provider、Payment、Grant、Notification delivery或target command effect。

## 8. Schema evolution and generated contracts

- OpenAPI/JSON Schema/protobuf之一作为每条boundary的唯一source；TS/Python clients生成，不手工双维护。
- additive optional字段必须有明确default/absence语义；required、enum、oneof、numeric unit变化需要新version。
- unknown-field policy按boundary冻结：security/effect command默认forbid；forward-compatible facts可保留或忽略但必须测试。
- producer先发布可双读schema，consumer升级后才切新required字段；删除旧version需通过consumer inventory。
- rolling window内至少支持current与previous compatible version；超过窗口返回upgrade_required，不silent coercion。
- contract digest、generator version与consumer evidence进入SiteRelease/ServiceRelease certification。

## 9. Extraction rules

只有满足以下触发之一才评估从Platform提取独立service：

- 独立scaling/latency/region或security isolation需求有数据证明。
- 故障域需要独立release/rollback。
- ownership/team/on-call已能承担独立SLO、storage、migration和incident。
- effect/provider runtime不能安全留在API process。

提取步骤：

1. 画当前aggregate、transaction、read/write和outbox edges。
2. 选择唯一data owner；禁止双主写。
3. 把原跨module强事务重构为owner command+saga，冻结intermediate/user-visible states。
4. 建立backfill/dual-read shadow evidence；除迁移协议外不长期dual-write。
5. 发布remote contract、workload identity、quota、SLO、runbook和DR。
6. cutover后删除旧repository access和transaction port；架构gate阻止回流。

禁止：“实现同一个interface，换RPC adapter即可拆服务”、共享数据库跨服务写表、分布式事务掩盖错误owner、每请求多hop chatty
repository或为了未来假设提前微服务化。

## 10. Platform workflow and saga rules

- same-context workflow可用transaction port原子完成，例如Redeem消费Code并创建Fulfillment intent/Grant acquisition（在已裁决owner内）。
- cross-context workflow先持久化root identity与state，再发送typed command；participant receipts逐步推进。
- saga coordinator只拥有workflow state，不拥有participant domain facts。
- compensation是新domain command/fact，不删除原Payment/Grant/Usage/Decision。
- unknown participant保持reconciliation_required；不能跨库手工标成功或重新发effect。
- 每个step冻结idempotency、deadline、retry safety、receipt和Support/Admin command。

## 11. Observability and operations

- metrics：RPC latency/accepted/unknown/error class、deadline exhaustion、receipt lookup、outbox lag、inbox duplicate、DLQ age、replay rate、
  schema/version mismatch、auth reject和per-Site fairness。
- trace传播correlation/causation但不传播raw token、prompt、Code、PII或Provider payload。
- logs记录contract/command/event safe refs、release、owner和error class；跨Site搜索需explicit GlobalScope。
- health分liveness/readiness/dependency degradation；readiness不能因一个非关键projection依赖失败而无限抖动，也不能在owner store
  不可durable时继续接受effect。
- runbooks覆盖unknown commit、outbox stuck、poison event、schema rollback、credential rotation、region failover和noisy Site。

## 12. Acceptance criteria

### AC-RPC-01 — Remote extraction cannot preserve false atomicity

```gherkin
Given an in-process workflow previously committed two module changes in one UnitOfWork
When one owner is extracted to a remote service
Then the design introduces explicit command, intermediate state, receipt and saga recovery
And it does not pass a transaction handle or claim an adapter swap preserves atomic commit
```

### AC-RPC-02 — Timeout queries the same command

```gherkin
Given an owner may have committed before the caller times out
When the caller recovers
Then it queries the same command and request digest for an authoritative receipt
And it does not create a new command identity or fallback owner
```

### AC-RPC-03 — Cross-Site and cross-environment replay fails

```gherkin
Given a valid command, event or cursor belongs to one Site and environment
When it is replayed into another Site, environment, audience or region outside scope
Then authorization rejects before read, commit or existence disclosure
And the mismatch is safely audited
```

### AC-RPC-04 — Event replay never repeats external effect

```gherkin
Given an outbox event is delivered twice, late or replayed during projection rebuild
When consumers process it
Then inbox/reducer semantics converge to the same projection or participant state
And no Provider, Payment, Grant, Notification or target action effect repeats
```

### AC-RPC-05 — Schema rolling window is executable

```gherkin
Given current and previous compatible service releases run simultaneously
When commands, queries and events cross versions
Then generated contract tests prove accepted and rejected fields for both versions
And an incompatible client receives upgrade_required rather than silent coercion
```

## 13. Verification and release gates

- architecture：import graph、repository/table owner、transaction-port scope、no self-RPC、no cross-service DB write。
- contract：generated TS/Python parity、strict boundary matrix、current/previous rolling compatibility、digest determinism。
- security：mTLS/workload/audience/environment/Site/epoch/key rotation和non-disclosure negative matrix。
- resilience：commit-response crash、deadline/circuit、duplicate/out-of-order event、DLQ/replay、region failover和backpressure。
- operations：SLO/dashboard/alert/runbook、schema rollback、credential rotation、projection rebuild与Support/Admin receipt。

No-Go：remote transaction handle；shared DB cross-service write；RPC adapter等价本地事务；retry classifier由HTTP猜；timeout新建identity；
unknown fallback；event replay触发effect；shared static service key；跨环境token；schema silent coercion；无owner/SLO/runbook提取服务。

## 14. Related documents and approval boundary

- [Platform/Web/Session target architecture](2026-07-25-platform-web-session-target-architecture-design.md)
- [Platform/Web/Session P0 closure](2026-07-25-platform-web-session-p0-contract-closure-design.md)
- [Wave 0 repository foundation](2026-07-25-wave-0-repository-contract-foundation-design.md)
- [PRD-10 Admin](2026-07-25-prd-10-admin-operating-console.md)

本文批准不授权实现。GA仍通过现有control/wire边界协作；任何GA graph、checkpoint、tool、Handoff、cancel、terminal或namespace
变化必须专项对齐，不能以“统一RPC”为名实施。
