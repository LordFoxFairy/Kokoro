---
artifact: architecture-readiness-assessment
version: "1.1"
created: 2026-07-25
status: superseded-by-v1.4-internal-review
scope: kokoro-production-target
---

# Kokoro Target Architecture Readiness Assessment

## Executive Verdict

本报告 v1.0 的 design-pass 结论已被 2026-07-25 第二轮多角色红队取代。目标方向仍成立：不新增万能后端、
第二套支付/卡密链或第二套 Claude Code/Manus runtime；`redeem_only` 仍可成为真实首发 acquisition
channel。但在 Parent Spec v1.4 完成内部复审前，不再声称整体设计已经通过。

当前仓库仍是 **No-Go for production**：Wave 尚未实现和认证。只有
`docs/reports/2026-07-25-kokoro-production-launch-readiness-checklist.md` 的 Must Have 全部签署，才可把状态
从 design-pass 改成 production-ready。

v1.4 已修订 Run/Usage/Model 唯一 ownership、Job finalization、RequestSecurityContext、Site ActivationAttempt、
RPC/deployable matrix、root budget topology、产品 P0 旅程以及 2A/2B、5A→4→5B 分波。内部复审结果应写入
新的 assessment revision；本文件其余评分仅保留为 v1.0 历史快照，不再作为实现授权证据。

## Requirement Assessment

| 用户要求 | 结论 | 设计证据 | 当前实现状态 |
|---|---|---|---|
| 实施完成即可直接上线 | Pass at design level | Production topology、分层验证、EvidenceBundle、Go/No-Go、rollback、maintenance、Wave 9 | Not started |
| 未接支付时用卡密取得同等产品能力 | Pass | FulfillmentSource union、redeem_only SalesPolicy、同 UoW Redemption/Fulfillment/Grant、source reversal | Not started |
| 功能完整 | Pass with SiteRelease rule | production_ready revision、四层关闭未完成功能、Wave 0-9 completion rule | Not started |
| 验证和测试完整 | Pass | static/property/contract/integration/E2E/chaos/load/security/DR/UAT matrix | Not started |
| 可长期维护 | Pass | SLO/on-call/runbook/restore/patch SLA/contract lifecycle/incident review | Not started |
| CLAUDE.md 的 INDEX.md 规划 | Pass | root/service/package/surface 分层、coverage manifest/CI、同 commit 更新、Wave 8 dead-doc 清理 | Not started |

## Architecture Scorecard

评分表示设计清晰度和边界完备度，不表示代码完成比例。

| Dimension | Score | Rationale |
|---|---:|---|
| Multi-Site / SiteRelease | 9.5/10 | 一 Site 一 Web Project、可信 DeploymentBinding、双 Release drain、rollback recheck 完整 |
| Platform modularity | 9.5/10 | 模块化 Core、UnitOfWork、workflow、API/Worker process role 与独立执行 context 边界明确 |
| Commerce / Credit | 9.5/10 | Fact→Fulfillment→Grant、Journal/Hold/Segment/Slice、refund/dispute/reconciliation 可证明 |
| Redeem-first | 9.5/10 | 无假 Payment、原子 claim/issuance、term/source lineage、availability fencing、reversal/replacement 完整 |
| Session / Job / Artifact | 9.5/10 | Run≠Job、typed parts/branch、Direct/Agent Operation、ArtifactVersion provenance 与恢复闭环 |
| GA / Agent product | 9.5/10 | GA 商业零感知、Manifest/Handoff/effect safety、Target/Permission/Routine/Team/TaskView 完整 |
| Security / Governance | 9.0/10 | Restriction epoch、ExecutionGrant、CredentialLease、Deletion participants、LegalHold 已冻结 |
| Verification / Operations | 9.5/10 | RC evidence、chaos/load/DR/rollback/on-call/maintenance 均为上线 blocker |
| Documentation governance | 9.0/10 | INDEX 分层和 CI 已设计；当前仓实际地图仍需 Wave 0/8 清理 |
| Current implementation readiness | 1.0/10 | 目标代码、schema、deploy 和 RC 尚未实施，不能与设计分数混淆 |

没有给出 10/10，是因为字段级 schema、API payload、migration、provider-specific adapter 和 UI behavior
必须在各 child Spec 中结合真实代码冻结；把这些全部塞进 Umbrella Spec 会降低而不是提高可实施性。

## Redeem-first Logic Check

```text
可信 Site/User/BillingAccount
→ SalesPolicy/Program/Batch/Code/Risk recheck
→ Program→Batch→Code ordered locks + availability epoch
→ one PlatformUnitOfWork
→ Redemption + FulfillmentTransaction
→ SubscriptionTerm/EntitlementGrant/CreditGrant
→ Outbox
→ Admission/Usage/Journal/Artifact
```

通过条件：

- Code 与 Grant 不会部分成功。
- 同 Code 并发最多一个成功。
- suspend/compromise 命令返回后不再有新兑换成功。
- 每个 SubscriptionTerm/FulfillmentCycle/Grant 有独立 root source。
- Redemption reversal 不触碰其他 Payment/Redemption/ProgramWindow 来源。
- Payment 后续接入不复制 Fulfillment、Credit、Subscription 或 Web 成功链。

因此，“和支付买一样”应准确理解为**取得权利后的结构和体验相同**，而不是制造一笔不存在的
Payment/Invoice/Refund。

## INDEX.md Current-state Gap

当前仓共有 28 份 INDEX：`kokoro-agent` 4、`kokoro-session` 4、`kokoro-web` 20、`kokoro-platform` 0；
根仓也没有 INDEX。现有 `kokoro-web/INDEX.md` 仍描述版本分裂、Admin DB 直连和旧部署方式，不能作为
目标架构事实。

正确处理顺序：

1. Wave 0 创建根/受管 public-root INDEX、template、manifest 和 CI checks。
2. 各领域 Wave 在真实边界切换时同 commit 重写局部 INDEX。
3. 不提前把“目标设计”写进尚未改变的当前代码 INDEX，避免再次制造假事实。
4. Wave 8 删除旧 owner/path/env/trap，CODEBASE_MAP 只保留高层导航和真实验证命令。
5. Wave 9 以 INDEX/CODEBASE_MAP 与 RC image/contract digest 一致作为 Go/No-Go blocker。

## Remaining Gates, Not Architecture Holes

- Wave 0 child Spec：pinned snapshot import、root workspace、contract generation、INDEX CI 的精确文件方案。
- 每个 Wave 的表字段、合法 transition、API/event schema、migration/cutover 和测试代码。
- 真实 Model/Storage/Notification/MCP adapter 的 sandbox certification；真实 Payment adapter 不属于首发 blocker。
- 具体 production cloud、capacity、domain、legal text、Site assortment、Model/Agent assignment 和 Code batch。
- 实施后的安全测试、load/soak、backup restore、rollback rehearsal 和 on-call 签署。

这些项目不会要求推翻总边界，但任何一项缺失都可能阻止生产上线。

## Final Decision

- **Architecture direction:** Pass.
- **Business logic completeness:** Pass at Umbrella level.
- **Redeem-only launch design:** Pass, subject to Wave 2 certification.
- **Production implementation:** No-Go; not started.
- **Next authorized design unit:** Wave 0 Repository/Contract/Documentation Foundation child Spec.
