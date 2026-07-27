---
artifact: launch-checklist
version: "1.1"
created: 2026-07-25
status: planned
scope: kokoro-redeem-first-production-launch
---

# Launch Checklist: Kokoro Redeem-first Production

## Launch Overview

| Field | Value |
|---|---|
| What | 完整 Kokoro production release；首发 Site 使用 `redeem_only`，启用的 Chat/Studio/Library/Admin 全链可用 |
| Launch Date | T0：Wave 9 Go/No-Go 获批后的预定发布窗口 |
| Launch Type | Major Release / First Production Launch |
| Launch Owner | Product Owner + Engineering Lead |
| Go/No-Go Decision | Product、Engineering、SRE、Security 对各自 blocker domain 共同签署；任一安全/账务/数据 blocker 可否决 |
| Architecture Authority | `docs/superpowers/specs/2026-07-25-platform-web-session-target-architecture-design.md` v1.5，内部批准并由用户复审后迁入 handbook |

`T` 表示相对生产切流时间；每项 owner 是必须承担签署责任的角色，不以“全体工程师”代替。

每项状态必须按顺序留下四类独立证据：`Design approved → Implemented → RC verified → Signed`。设计文档、
自报标签、UAT 截图或人工说明不能替代实现与 RC 证据。本文在实现获批前所有执行项均保持 `Not started`。

## Scope Freeze

| Item | Owner | Due | Status | Evidence |
|---|---|---:|---|---|
| [ ] 冻结首发 Site、域名、`LaunchProductProfile`、`EnabledSurfaceInventory`、Agent、Model、Capability、Offering 与 `redeem_only` SalesPolicyRevision | Product Owner | T-21d | Not started | SiteRelease manifest diff |
| [ ] Profile 的 CanonicalJourney、UserVisibleState、RecoveryAction、ProductMetric 与 ContentPolicy revision 全部冻结 | Product Owner | T-21d | Not started | Product contract bundle |
| [ ] 每个启用 capability/surface revision 均有有效 `CapabilityQualificationAttestation`；compile/build/preview 后的 candidate 再取得 digest 完全匹配的 `ReleaseCertificationInstance` | Engineering + Release | T-21d | Not started | Qualification set + Release certificate DAG |
| [ ] 未启用能力在 route、bootstrap、API authorization、Admin 四层均关闭 | Web + Platform Leads | T-14d | Not started | Negative E2E report |
| [ ] 真实 Payment Provider 明确不在首发 scope；Checkout/payment mutation fail closed | Commerce Lead | T-14d | Not started | Contract/E2E evidence |
| [ ] Redeem-only 在 route/bootstrap/API/Admin/domain effect/secret/egress 七层关闭新 Payment acquisition；生产 Site 无 Merchant/Provider binding、Payment secret 或可调用 Provider IO | Commerce + Security | T-14d | Not started | Negative matrix + binding/secret/egress inventory |
| [ ] 外部售卡退款只记录 external reference 并走 Redemption source reversal/replacement；不伪造 Platform Order/Payment/Invoice/Refund，历史 Payment duty 若存在仍可收口 | Commerce + Support | T-14d | Not started | Source-lineage E2E |
| [ ] 已知问题逐项记录 owner、用户影响、缓解和接受期限；无未接受 blocker | Product Owner | T-2d | Not started | Accepted-risk register |

## Engineering Readiness

| Item | Owner | Due | Status | Evidence |
|---|---|---:|---|---|
| [ ] Wave 0-8 退出条件全部通过，旧代码/表/env/header/adapter/注释清零 | Engineering Lead | T-14d | Not started | Wave evidence index |
| [ ] 根 lock/catalog、Python lock、generated contracts 零漂移 | Foundation Lead | T-14d | Not started | CI artifact |
| [ ] PlatformUnitOfWork、Outbox/Inbox、epoch fencing、Effect/Grant 幂等全部通过 | Platform + Runtime Leads | T-14d | Not started | Integration/chaos reports |
| [ ] Redeem 并发双兑、事务 crash、重复请求、Program expiry、reversal 全部通过 | Commerce Lead | T-14d | Not started | Redeem certification report |
| [ ] 两个 production-like Site 使用不同产品源码根、lockfile、CI、artifact、deployment、domain、workload identity 与 SiteProjectBinding；单站升级/回滚不改变另一站，且无 Cookie/cache/brand/data 串站 | Web + Fleet + Security | T-14d | Not started | Multi-Site provenance + negative E2E |
| [ ] Session branch/reconnect、GA recovery、Job callback/unknown、Artifact lineage 全部通过 | Session + Runtime Leads | T-14d | Not started | Runtime E2E/chaos |
| [ ] 干净浏览器只凭完整 Session snapshot + watermark 恢复 large/branched/HITL/media/cost-pending 页面，不依赖 GA checkpoint 或全历史 SSE | Session + Web | T-14d | Not started | Snapshot conformance trace |
| [ ] SSE cursor malformed/ahead/expired/wrong-Site/wrong-subject/schema/epoch 均 typed fail，无 seq-0 fallback；append-before-broadcast、slow consumer、grant revoke、proxy drain、Redis/Mongo outage 通过 | Session + SRE + Security | T-14d | Not started | Transport chaos report |
| [ ] Admin 零业务 DB import；财务、发布、支持、治理使用专用 workflow | Admin Lead | T-14d | Not started | Architecture test + UAT |
| [ ] Admin Web/BFF 无业务 DB role、SQL/script/generic mutation bypass；privileged auth、scope、environment/region、epoch revoke、maker-checker、JIT access 与 audit fail-closed 负向矩阵全过 | Admin + Security | T-14d | Not started | Static/runtime boundary proof + AC-ADM matrix |
| [ ] 所有 migration 完成 expand/compatibility rehearsal，contract step 有 consumer inventory | Data Lead | T-7d | Not started | Migration report |
| [ ] 每个 projection 有 definition/source/retention/rebuild runbook；空 shadow 从 owner truth 重建、live catch-up 无 gap、replay 无 effect、Credit/terminal 零差异，authority switch/rollback 可逆 | Data + Domain Owners | T-7d | Not started | AC-PROJ-01..06 report |
| [ ] OCI image 使用 digest、签名、SBOM/provenance；无 mutable production tag | Release Engineer | T-7d | Not started | Image manifest |
| [ ] 根/受管目录 INDEX、CODEBASE_MAP、handbook/ADR、runbook 与实际入口一致 | Architecture Owner | T-7d | Not started | index-coverage + review |

## Redeem/Card Code Readiness

| Item | Owner | Due | Status | Evidence |
|---|---|---:|---|---|
| [ ] Production RedeemProgramVersion 引用正确 Product/Plan/FulfillmentProgram 和 Site eligibility | Commerce Lead | T-7d | Not started | Program review |
| [ ] Code 使用 CSPRNG；数据库只存 keyed HMAC；HMAC key 在 Secret Manager | Security + Commerce | T-7d | Not started | Security inspection |
| [ ] Production batch 双人批准；明文只一次性加密导出；导出后平台不可回显 | Security + Operations | T-3d | Not started | Batch audit event |
| [ ] Test/staging Code batch 无法在 production 兑换，production Code 不进入日志/analytics/support ticket | Security Lead | T-3d | Not started | Isolation test |
| [ ] 兑换成功产生 Redemption、Fulfillment、SubscriptionBinding(authority=none)、Grant 和 Outbox | Commerce Lead | T-3d | Not started | Production-like E2E |
| [ ] Code claim 与 Grant issuance 原子；失败可安全重试；重复请求返回同一结果 | Platform Lead | T-3d | Not started | Fault-injection test |
| [ ] 同 key/同 digest 重试复用结果；同 key/不同 Code/digest 返回 IDEMPOTENCY_CONFLICT | Platform Lead | T-3d | Not started | Idempotency matrix |
| [ ] Program/Batch suspend/compromise 与在途兑换完成线性化测试；命令返回后新成功兑换为 0 | Platform + Commerce | T-3d | Not started | Availability race report |
| [ ] 多次 Payment/Redemption/ProgramWindow 的 Cycle/Term/Grant 都能追溯独立 root source，撤销不串源 | Commerce Lead | T-3d | Not started | Lineage/reversal report |
| [ ] pending review 不预占 Code；approve 后重验 Program/Batch/Risk，过期/重放/期间被兑换均安全收口 | Risk + Commerce | T-3d | Not started | Review race report |
| [ ] Batch/Replacement 密文 artifact 的错误 recipient、重复下载、每个 crash point、TTL/orphan GC 已验证 | Security + Commerce | T-3d | Not started | Secret delivery report |
| [ ] Risk/velocity dependency 不可用时 fail closed，Code 未 claim，未退化为本机限速 | Security + SRE | T-3d | Not started | Dependency failure test |
| [ ] 用户能看到到账权益、Credit 来源、有效期和兑换记录；没有假 Payment/Refund 文案 | Web + Product | T-3d | Not started | UAT screenshots |
| [ ] 丢失/泄漏/误发/作弊的 batch revoke、source reversal 和补偿 runbook 已演练 | Support + Commerce | T-2d | Not started | Tabletop record |

## QA & Verification

| Item | Owner | Due | Status | Evidence |
|---|---|---:|---|---|
| [ ] Static/type/lint/schema/generate/dependency/index gates 全绿 | QA Lead | T-7d | Not started | CI run |
| [ ] Unit/property tests 覆盖 Credit/Journal/Hold/Slice/Money/permission invariants | QA + Domain Leads | T-7d | Not started | Seeded report |
| [ ] Credit chaos/property 证明单 root Hold、child allocation CAS 守恒、delegated Job 无第二 Hold、unknown 不释放、fenced return、exact-source settlement、provider overage 不形成静默客户债务 | Credit + Runtime + QA | T-7d | Not started | AC-BUD-01..06 + journal proof |
| [ ] 真实 PostgreSQL/Redis/Mongo/S3-compatible integration suite 全绿 | QA Lead | T-7d | Not started | Integration report |
| [ ] TypeScript/Python producer-consumer compatibility matrix全绿 | Contract Owner | T-7d | Not started | Contract matrix |
| [ ] 全服务 E2E 覆盖注册→兑换→Chat/Studio→Job→Artifact→再次登录恢复 | QA Lead | T-5d | Not started | E2E trace |
| [ ] Chaos 覆盖 process crash、lease steal、重复/乱序事件、Provider unknown、Target offline | Reliability Lead | T-5d | Not started | Chaos report |
| [ ] `LaunchCapacityProfileRevision` 冻结并发、5 倍 burst、p95/p99、queue/DB/storage ceiling；SSE 10k/24h、Job queue、DB pool、对象存储达到该 revision | Performance Owner | T-5d | Not started | Capacity profile + load/soak report |
| [ ] Chrome/Safari/Firefox + mobile breakpoints + keyboard/screen reader；所有 Core P0 Journey 达到 WCAG 2.2 AA | Web QA | T-5d | Not started | Browser/a11y report |
| [ ] Staging 使用 production topology 与独立 secrets 完成 RC rehearsal | Release Engineer | T-3d | Not started | RC deployment record |

## Security, Privacy & Legal

| Item | Owner | Due | Status | Evidence |
|---|---|---:|---|---|
| [ ] SAST/SCA/secret/license/container/DAST 完成；Critical/High 无未处置项 | Security Lead | T-5d | Not started | Security bundle |
| [ ] Site A→B、Admin GlobalScope、BFF forged siteId、IDOR、CSRF/Origin、rate limit 全部验证 | Security Lead | T-5d | Not started | Pen-test matrix |
| [ ] SSRF/path traversal/command injection/plugin/package/connector/ExecutionGrant 逃逸验证 | Security Lead | T-5d | Not started | Abuse-case report |
| [ ] Privacy Policy、Terms、Acceptable Use、Credit/Card Code 条款、退款不适用说明与 Site 法务版本批准 | Legal + Product | T-7d | Not started | LegalRevision |
| [ ] Export/Deletion/Retention/LegalHold participant 全链通过；强制财务事实不会被删除拒收 | Privacy Owner | T-5d | Not started | Governance E2E |
| [ ] Media GC 仅执行有效 GCPlan，effect 前按 watermark/epoch 重验 active grant/job/share/lineage/LegalHold/backup refs；same Blob 多资源安全，delete timeout 保持 unknown，所有 target 有 DestructionReceipt | Media + Data Governance + SRE | T-5d | Not started | GC race/DR/provider-unknown report |
| [ ] 生产访问权限最小化、break-glass、step-up、maker-checker 和审计验证 | Security + SRE | T-3d | Not started | Access review |

## Operations & Infrastructure

| Item | Owner | Due | Status | Evidence |
|---|---|---:|---|---|
| [ ] DNS/TLS/CDN/WAF/rate limit、domain binding 和 canonical URL 正确 | SRE | T-5d | Not started | Edge checklist |
| [ ] PostgreSQL/Mongo/Object Storage backup、PITR 和从备份恢复演练达到 RPO/RTO | Data + SRE | T-5d | Not started | Restore proof |
| [ ] DR 同时恢复 owner DB、outbox archive、schema/decoder registry、projection definitions/snapshots；fence old writers 后处理 cursor/inbox/lease epoch，证明 known-gap reconciliation、effect dedupe 与 two-Site isolation | Data + SRE + Domain Owners | T-5d | Not started | Timed DR exercise |
| [ ] Event retention manifest 冻结 owner/outbox/transport/inbox/UI-SSE 各 tier 的 duration、archive/restore、decoder、LegalHold/Data Rights/destruction policy，覆盖 reconnect/rebuild/DR 窗口 | Data Governance + SRE | T-5d | Not started | Signed retention manifest + restore/replay proof |
| [ ] Readiness/liveness/graceful shutdown/lease drain 在 rolling deploy 中无丢单 | SRE | T-5d | Not started | Rollout test |
| [ ] capacity、autoscaling、DB connection、queue concurrency、storage lifecycle 与配额已冻结 | SRE | T-3d | Not started | Capacity plan |
| [ ] dashboards/alerts 覆盖 SLO、queue age、hold/reconciliation、redeem、run/job、provider、storage、errors | Observability Owner | T-5d | Not started | Alert inventory |
| [ ] 观测清单显式覆盖 SSE buffer/replay/cursor/drain、projection lag/gap/diff/fairness、allocation unknown/overage、GC partial/unknown、audit fail-closed、Trust purge/reporting 与 Data Rights backlog | Observability + SRE | T-5d | Not started | Metric/alert/runbook rehearsal bundle |
| [ ] 每个 page alert 有 owner、runbook、权限和 rehearsal；on-call rotation 已确认 | SRE Lead | T-2d | Not started | On-call schedule |
| [ ] SiteRelease、backend、migration-forward、Code batch、secret compromise 回滚/处置已桌面演练 | Incident Commander | T-2d | Not started | Tabletop report |

## Product, UX & Support

| Item | Owner | Due | Status | Evidence |
|---|---|---:|---|---|
| [ ] Landing、auth、redeem、balance、Chat/Studio、Library、settings、support IA 完成 Design QA | Product Design | T-7d | Not started | Design QA report |
| [ ] loading/empty/error/partial/unknown/cost_pending/insufficient/restricted 状态均有可解释 UX | Product Design | T-7d | Not started | State inventory |
| [ ] OperatorCommandMatrix 的 role/scope/step-up/maker-checker/notification 与 API enforcement 一致 | Admin + Security | T-5d | Not started | Command matrix UAT |
| [ ] Text/Image/Music/Voice/Video/Upload/Share ContentPolicy、rights consent、appeal 和 SLA 已认证 | Trust + Legal | T-5d | Not started | Content policy certification |
| [ ] i18n、SEO、social metadata、legal/footer、email/push Site brand binding 正确 | Web + Content | T-5d | Not started | Content review |
| [ ] Support 可按 correlationId 查看 User/Redemption/Grant/Run/Job/Artifact 时间线 | Support Lead | T-5d | Not started | Support UAT |
| [ ] FAQ 和 canned responses 覆盖卡密无效/已用/过期、未到账、生成失败、额度、删除和安全限制 | Support Lead | T-3d | Not started | Support pack |
| [ ] 补偿只能经正式 Admin Grant/Reversal workflow；Support 无数据库写权限 | Support + Security | T-3d | Not started | Permission test |
| [ ] 用户状态页、incident communication 和 escalation path 已准备 | Communications Owner | T-2d | Not started | Communication pack |

## Marketing & Communications

| Item | Owner | Due | Status | Evidence |
|---|---|---:|---|---|
| [ ] Landing/pricing/redeem 文案只承诺首发已启用能力，不宣传未开放 Payment/P2 Surface | Product Marketing | T-7d | Not started | Claims review |
| [ ] Card Code 分发渠道、recipient/distributor、过期/遗失/售后责任和安全传递方式已批准 | Growth + Security | T-7d | Not started | Distribution plan |
| [ ] Release notes、FAQ、status page 初始公告和 incident 模板已通过 Product/Legal/Support 复核 | Communications Owner | T-3d | Not started | Communication pack |
| [ ] SEO/canonical/social assets 和 analytics campaign attribution 不跨 Site 拼接用户身份 | Growth + Privacy | T-3d | Not started | Site campaign review |
| [ ] 发布窗口内 Marketing 不临时启用 Offering/Experiment/Code batch；所有变更走 SiteRelease/Admin workflow | Product Owner | T-1d | Not started | Change freeze audit |

## Analytics & Business Observability

| Item | Owner | Due | Status | Evidence |
|---|---|---:|---|---|
| [ ] 注册、兑换、首个成功 Run、Studio/Job、Artifact、留存漏斗事件有 consent/Site scope | Growth Owner | T-5d | Not started | Event catalog |
| [ ] Exposure/Outcome、Usage/Cost、Grant liability、Code batch redemption rate 可审计 | Data + Commerce | T-5d | Not started | Dashboard links |
| [ ] launch success/error/SLO baseline 与告警阈值在 RC 前冻结 | Product + SRE | T-3d | Not started | Baseline report |
| [ ] analytics failure 不阻塞交易/生成；PII/Code/secret 不进入 event payload | Privacy + Data | T-3d | Not started | Payload audit |

## Go/No-Go Criteria

### Must Have — 任一失败即 No-Go

| Criterion | Owner | Due | Status |
|---|---|---:|---|
| [ ] Scope、SiteRelease、image/contract digests 和 production Code batch 冻结并双人批准 | Product + Release + Security | T-2d | Not started |
| [ ] 所有启用用户旅程真实全链通过，无 stub/mock/数据库手工步骤 | Engineering + QA | T-2d | Not started |
| [ ] Redeem 原子、Credit/Grant/Usage 守恒、跨 Site 隔离和 deletion/legal invariants 全通过 | Commerce + Security + Privacy | T-2d | Not started |
| [ ] Critical/High 风险、数据丢失、重复副作用、账务不一致 blocker 为 0 | Security + Engineering | T-1d | Not started |
| [ ] Load/soak、backup restore、rolling deploy、Site/backend rollback 已实际演练 | SRE + Data | T-2d | Not started |
| [ ] Dashboard、page alert、runbook、on-call、Support 和权限全部就绪 | SRE + Support | T-1d | Not started |
| [ ] INDEX/CODEBASE_MAP/handbook/API/event docs 与 RC 一致且构建可复现 | Architecture + Release | T-1d | Not started |

### Should Have — 缺失需 Product/SRE 书面接受

| Criterion | Owner | Due | Status |
|---|---|---:|---|
| [ ] 非关键渠道 Notification delivery receipt 完整 | Notification Owner | T-2d | Not started |
| [ ] 第二个真实 production Site 在其独立发布窗口完成同等级演练（首发前的双 Site production-like 隔离认证已属于 Must Have） | Web + SRE | Post-launch scoped release | Not started |
| [ ] 非首发语言营销内容完成本地化复核 | Content Owner | T-2d | Not started |

### Nice to Have — 不影响首发

| Criterion | Owner | Due | Status |
|---|---|---:|---|
| [ ] 真实 Payment Provider adapter | Commerce Lead | Post-launch scoped release | Not started |
| [ ] 未在首发 SiteRelease 开放的 P2 AgentTeam/Application Runtime Surface | Agent Product Lead | Post-launch Site release | Not started |

## Rollback Plan

### Trigger Conditions

- 跨 Site 数据/品牌/Cookie 泄漏或权限绕过。
- 同一 Code 重复 Fulfillment、Credit/Grant/Journal 不守恒或用户余额大面积错误。
- 已受理 Run/Job 丢失、重复 Provider side effect、Artifact 数据丢失。
- Critical 可利用漏洞、secret 泄漏或失控本地设备/浏览器命令。
- 新版本错误率、延迟、queue age 或资源耗尽超过冻结阈值并持续两个观察窗口。
- Migration/Release incompatibility 导致无法安全读取旧数据或恢复旧 Tab。

### Rollback Steps

1. Incident Commander 宣告停止 promote，冻结 candidate SiteRelease 和非必要 Admin mutation。
2. Platform 以 active pointer CAS 恢复上一个已重新验证的 SiteRelease；CDN/domain 切回旧 Web artifact。
3. Backend 若仍 contract-compatible，保留当前版本并关闭有问题 assignment；必须回滚时按 rehearsal 切回旧
   image digest。禁止逆向破坏性 migration，使用 forward repair。
4. 暂停受影响 Job/Target/Capability 新 dispatch；保留 Inbox/Outbox、Evidence、unknown Attempt 和 Hold，
   由 reconciler 收口，不删除事实或重复调用 Provider。
5. Code batch 泄漏时只 revoke 未兑换 Code；已兑换事实和 Grant 由 source-specific case/reversal 处理，
   不能批量改写历史。
6. 运行 Multi-Site、Redeem/Credit invariant、Session/Job recovery、Artifact 和 smoke suite，确认稳定。
7. 发布用户/Support 状态更新，建立受影响 subject/transaction 清单；补偿只走 Admin workflow。
8. 关闭 incident 前记录 timeline、root cause、修复 commit、回归测试和下一次 Go/No-Go 条件。

### Rollback Owners and Targets

| Scope | Owner | Target |
|---|---|---:|
| SiteRelease/Web traffic | Web Release Owner + SRE | 15 minutes |
| Backend image/assignment | Runtime/Platform Lead + SRE | 30 minutes |
| Secret/Code batch containment | Security + Commerce | 15 minutes |
| Financial/Usage reconciliation | Commerce + Platform | 用户进一步消费立即受控；最终收口时间由 Case 明示 |

## Check-in Schedule

| Checkpoint | Attendees | Required Output |
|---|---|---|
| T-21 scope freeze | Product、Architecture、Domain Leads | SiteRelease scope 与 owners |
| T-14 engineering readiness | Engineering、QA、Security、SRE | blocker list 与 RC candidate |
| T-7 full readiness | 全部 owner | EvidenceBundle draft、rollback rehearsal |
| T-2 Go/No-Go pre-read | Decision makers | 仅剩零 blocker或书面 should-have risk |
| T0 launch sync | Product、Engineering、SRE、Security、Support | signed Go、live dashboard、rollback owners |
| T+1h / T+24h / T+7d | 同上按需缩减 | health review、incident/metric/feedback、正式复盘 |

## Open Issues Policy

Launch checklist 不预填虚构 issue。任何新 issue 必须记录 `severity、owner、discoveredAt、affected
release/site/journey、mitigation、decision、expiry`；Blocker 未关闭时不得签署 Go。
