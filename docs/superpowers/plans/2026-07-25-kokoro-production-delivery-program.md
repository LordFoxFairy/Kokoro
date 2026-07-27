# Kokoro Production Delivery Program Implementation Plan

repositoryTopology: federated-submodules-v1

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement each approved child plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在永久保留四个独立子仓及其独立部署能力的前提下，将 Kokoro clean replace 为可直接上线的多 Site AI 产品，并以 `redeem_only` 完成首个真实 acquisition→Fulfillment→Grant→Usage 生产闭环。

**Architecture:** 本文件是实施总控索引，不授权直接修改业务代码。整体按依赖拆成 15 个可独立评审的
Wave/cut，每个 cut 都有独立子 Spec 和精确实现计划；只有依赖、测试证据、INDEX/文档与同波旧实现清理
全部完成后退出。Platform 使用模块化 Core，Session/Job/Capability/Model Gateway/GA 等保持独立运行边界，
一 Site 一 Web Project，共享后端。

**Tech Stack:** Node.js 24 LTS、pnpm 11、TypeScript 5.9、Next.js 16.2、React 19.2、Zod 4、Vitest 4.1、Prisma 7、PostgreSQL 18；Python 3.12、uv、Ruff、Pyright、Pydantic 2；MongoDB、Redis、S3-compatible storage、Secret Manager、OpenTelemetry。

---

## 1. Authority and Completion Rule

执行事实源：

1. `docs/superpowers/specs/2026-07-25-platform-web-session-target-architecture-design.md`
2. 当前 Wave 已批准子 Spec
3. 当前 Wave implementation plan
4. 相邻 `INDEX.md`
5. 代码、测试和 Release Evidence

冲突时按上述顺序裁决；历史 handoff、旧 handbook 和旧实现不能覆盖新方案。

同一 Wave 内，已评审 child Spec 是 Umbrella 对该 scope 的强制细化：它不能改变 Umbrella 的全局 owner/不变量，
但对目录、锁、切换顺序和验收细节拥有优先解释权。Wave 0 保持四个 `kokoro-*` 独立仓库并由根仓 pin；
独立 production Site Project 的 source/lock/CI/artifact/release authority 不得因共享 Web capability source 被根仓吸收，
也不得用 root compatibility evidence 冒充 Fleet 已完成。

`Core Production Launch` 与 `Advanced Agent Program` 分开验收：首发 Site 只需对其冻结
`LaunchProductProfile/EnabledSurfaceInventory` 中启用的 P0 旅程完成生产认证；未启用的 6A-6D 高级能力不
阻塞 Core Launch。任何高级能力一旦进入 production SiteRelease，仍须通过对应完整门。整体 Transformation
Program 只有在以下条件同时成立时 complete：

- [ ] 本 Program 表中的 Wave 0、1、2A、2B、3、5A、4、5B、6A-6D、7-9 全部退出。
- [ ] 启用的用户、Admin 和 Support 旅程不存在 stub/mock/手工数据库步骤。
- [ ] `redeem_only` production certification 与完整 Release Checklist 通过。
- [ ] 旧代码、表、env、header、兼容 adapter、测试和失真 INDEX/文档清零。
- [ ] Production RC 通过 security、load、soak、chaos、backup restore、rollback 和 Go/No-Go。

Wave 8/9 是可重复的 profile-scoped release gate。Core pass 生成 `CertificationInstance` 并可授权对应
SiteRelease 上线，但 Wave 8/9 保持 active；2B、5B、6A-6D 与全部目标 profile 完成后再执行
`transformation-final` pass，只有该 instance 通过才把 Wave 8/9 与本 Program 标记 complete。

## 2. Mandatory Child Spec and Plan Set

每行必须依次完成 `产品子 PRD → 产品红队 → child architecture Spec → 架构/可靠性/安全评审 → 用户书面复审
→ writing-plans child plan → implementation → evidence → cleanup`；Wave 0 作为工程地基不需要业务产品子 PRD。

| Wave | Mandatory PRD IDs | Child Spec filename | Child implementation plan filename | Production-capable exit |
|---|---|---|---|---|
| 0 | none | `2026-07-25-wave-0-repository-contract-foundation-design.md` | `2026-07-26-wave-0-repository-contract-foundation-implementation-plan.md` | Federated repositories、独立 locks/CI/releases、root contract/Infra/compatibility/pin promotion gate |
| 1 | PRD-00、PRD-01、PRD-02、PRD-11、PRD-12、PRD-14、PRD-15、PRD-16 core contracts | `2026-07-25-wave-1-platform-identity-site-policy-design.md` | `2026-07-25-wave-1-platform-identity-site-policy-implementation-plan.md` | Identity/Auth、Workspace/Project、RequestSecurityContext、PlatformUnitOfWork、ActivationAttempt、Restriction token/epoch |
| 2A | PRD-03 | `2026-07-25-wave-2a-commerce-redeem-credit-design.md` | `2026-07-25-wave-2a-commerce-redeem-credit-implementation-plan.md` | Account/Redeem、Catalog/Subscription/Fulfillment/Credit/Usage 与 Redeem-only certification |
| 2B | PRD-04 | `2026-07-25-wave-2b-payment-provider-enablement-design.md` | `2026-07-25-wave-2b-payment-provider-enablement-implementation-plan.md` | Checkout/Payment/Refund/Dispute/dunning 与真实 Provider certification；非 Core redeem-only blocker |
| 3 | PRD-05/06 intake contract | `2026-07-25-wave-3-session-admission-projection-design.md` | `2026-07-25-wave-3-session-admission-projection-implementation-plan.md` | Session 商业逻辑清零、typed parts、branch、reconnect、AuthorizationSegment |
| 5A | PRD-05 model/capability annex | `2026-07-25-wave-5a-model-capability-production-spine-design.md` | `2026-07-25-wave-5a-model-capability-production-spine-implementation-plan.md` | Gateway/Capability、AuthorizedModelRoute/ExecutionGrant、AttemptUsageFact、Core 最小 GA adapter；触及 GA 前专项批准 |
| 4 | PRD-06、PRD-07、PRD-08I、PRD-08M、PRD-08V、PRD-09、PRD-16 modality annex | `2026-07-25-wave-4-operation-job-artifact-studio-design.md` | `2026-07-25-wave-4-operation-job-artifact-studio-implementation-plan.md` | Direct/Agent Operation、durable Job、ArtifactVersion 与每个启用 Studio 专业闭环 |
| 5B | PRD-A1 | `2026-07-25-wave-5b-advanced-agent-handoff-safety-design.md` | `2026-07-25-wave-5b-advanced-agent-handoff-safety-implementation-plan.md` | 经专项用户批准的 AgentRevision、真实 Handoff、高级 effect/epoch safety |
| 6A | PRD-A2 | `2026-07-25-wave-6a-target-permission-interaction-design.md` | `2026-07-25-wave-6a-target-permission-interaction-implementation-plan.md` | Target/Device/Permission/Interaction |
| 6B | PRD-A3 | `2026-07-25-wave-6b-developer-workspace-context-design.md` | `2026-07-25-wave-6b-developer-workspace-context-implementation-plan.md` | Developer Workspace/Context/Memory/多端 |
| 6C | PRD-A4 + PRD-15 runtime | `2026-07-25-wave-6c-automation-connector-taskview-design.md` | `2026-07-25-wave-6c-automation-connector-taskview-implementation-plan.md` | Routine/Connector/Plugin/TaskView/最小 Notification 生产链 |
| 6D | PRD-A5 | `2026-07-25-wave-6d-agent-team-application-runtime-design.md` | `2026-07-25-wave-6d-agent-team-application-runtime-implementation-plan.md` | AgentTeam/Wide Research/Application Runtime |
| 7 | PRD-10、PRD-11、PRD-12、PRD-13、PRD-15、PRD-16 | `2026-07-25-wave-7-core-admin-governance-operations-design.md` | `2026-07-25-wave-7-core-admin-governance-operations-implementation-plan.md` | Site Fleet、Admin/Support、Risk/Safety、Growth、Data Rights、Notification；高级治理随 6A-6D |
| 8 | PRD-00、PRD-14 + enabled PRDs | `2026-07-25-wave-8-clean-cutover-documentation-design.md` | `2026-07-25-wave-8-clean-cutover-documentation-implementation-plan.md` | 当前 profile 旧事实源清零，handbook/ADR/INDEX/CODEBASE_MAP/runbook 与唯一实现一致 |
| 9 | PRD-00、PRD-14 + enabled PRDs | `2026-07-25-wave-9-production-certification-launch-design.md` | `2026-07-25-wave-9-production-certification-launch-implementation-plan.md` | profile-scoped EvidenceBundle、Go/No-Go、canary、rollback、on-call |

不得预创建空 child 文件。开始某 Wave 时完整设计并复审，避免占位文档伪装成完成。

## 3. Wave Execution Protocol

每个 Wave 都执行相同步骤；child plan 必须进一步拆成 2-5 分钟动作、精确文件、测试和 commit。

- [ ] **Step 1: Freeze the child scope**

  从 Umbrella Spec 复制该 Wave 的对象、状态、不变量、接口、事件、失败场景、删除清单和退出门；明确非目标和依赖。

- [ ] **Step 2: Inspect actual code and adjacent INDEX files**

  读取真实 imports/exports、schema、migration、test、deployment entrypoint。记录要保留、替换和删除的准确路径，不从旧文档推测代码。

- [ ] **Step 3: Write and product-red-team the child PRD**

  使用 Product PRD Registry 中的精确文件名；冻结 Journey、UserVisibleState、RecoveryAction、metric target、
  scope 与 Support/Admin 旅程。P0 产品 finding 清零后才能写 architecture child Spec。

- [ ] **Step 4: Write and review the child architecture Spec**

  子 Spec 必须冻结数据 owner、合法状态转移、command/event schema、幂等键、transaction boundary、security/recovery 和 cutover；用户批准前不写实现计划。

- [ ] **Step 5: Generate the exact child implementation plan**

  使用 `superpowers:writing-plans`；每个代码步骤给出完整 snippet、精确命令和预期失败/成功，采用 TDD 和小 commit。

- [ ] **Step 6: Create an isolated implementation worktree**

  使用 `superpowers:using-git-worktrees`；多个 worker 只按互不重叠的文件/模块切分，禁止共同修改同一 migration、contract 或 barrel export。

- [ ] **Step 7: Execute with two-stage review**

  推荐 `superpowers:subagent-driven-development`；每个任务先审 spec compliance，再审 code quality。子代理成功不替代主仓 verification。

- [ ] **Step 8: Run the Wave evidence matrix**

  至少包含 static、unit/property、component、contract、integration、targeted E2E、failure/security；涉及 runtime/transaction 的 Wave 不能只靠 mock。

- [ ] **Step 9: Clean cut in the same Wave**

  删除被替代的代码、表、env、header、compat、注释、测试和 INDEX 描述；`rg` 和 dependency tests 证明不存在旧入口。

- [ ] **Step 10: Update architecture maps and reports**

  同 commit 更新受影响 INDEX、生成契约、runbook、ADR/CODEBASE_MAP 和 Wave report；不得留下两个当前事实源。

- [ ] **Step 11: Exit only with fresh main-worktree verification**

  在主工作树重新运行 child plan 的全部 gate，生成 commit/image/contract digests 和证据索引；失败则 Wave 保持 active。

## 4. Dependency and Parallel Cuts

```text
Wave 0
  → Wave 1
      → Wave 2A ────────────┐
      → Wave 3 (read contracts may parallel 2A)
            └───────────────→ Wave 5A
                                 → Wave 4
                                     ├→ Wave 7 → Wave 8/9 Core certification instance
                                     └→ Wave 5B → Wave 6A/6B/6C/6D
                                                      → Advanced profile delta certification
All planned cuts ────────────────────────────────────→ Wave 8/9 transformation-final instance
```

允许并行：

- Wave 2A 领域实现与 Wave 3 只读 contract/projection 设计，在 Admission/Rating contract 冻结后并行。
- Wave 2B 可在 2A 后独立推进，不阻塞 redeem-only 首发。
- Wave 4 的非 GA 文件树与 Wave 5B 设计可并行；真实 Studio 必须先通过 5A Gateway/Capability contract gate。
- Wave 6A-6D 的 Target/Permission、Developer Workspace、Automation/TaskView、AgentTeam/Application Runtime 在共同 contract 冻结后按包并行。
- 每个 Site Web Project 可以在共享 Surface contract 冻结后并行，但同一 Site 的 route/release owner 唯一。

禁止并行：

- 根 contract schema 与生成物的两个写者。
- 同一数据库 migration chain 的两个写者。
- PlatformUnitOfWork/Fulfillment/CreditJournal authority 的并行替代实现。
- Site active Release pointer、root compatibility/BOM manifest、barrel export 和 CODEBASE_MAP 的无 owner 并发写。

## 5. Vertical Release Slices

各 Wave 必须保持可测试，但以下 slice 才形成用户价值：

### Slice A — Trusted Site Bootstrap

Wave 0-1 后证明：两个独立 Web artifact 只能交换自己的 SiteContext，Release compile/promote/rollback 可审计，未实现功能不可见且 API fail closed。

### Slice B — Redeem Acquisition

Wave 2A 后证明：生产形态无 Payment secret 也能启动，用户兑换 Code 原子取得 Subscription/Entitlement/Credit；Admin 可生成、一次性导出、暂停、compromise、撤销和补发。

### Slice C — Usable AI Product

Wave 3、5A、4 后证明：用户从兑换额度进入 Chat/Studio，Run/Job 可恢复，Artifact 可追踪，Model/Capability 副作用安全，Credit 可结算。5A 包含 Core 所需最小 GA adapter cutover；任何实际 GA runtime 行为变化先走专项用户批准门，但不把真实 Handoff 等高级能力塞入 Core Launch。

### Slice D — Advanced Agent Product

Wave 5B、6A-6D 后证明：Local/Cloud Target、Worktree、Permission、Routine、TaskView、多端和 AgentTeam 复用同一业务/执行体系；每个 cut 同波交付其 Admin/Support/治理面和 production certification。

### Slice E — Operable Production

Core profile 在 Wave 7-9 后证明：运营、Support、Risk、Deletion、Notification、on-call、DR、rollback、文档和 RC evidence 全部闭环，才允许真实流量。高级 profile 只需对新增 Surface 做 delta certification，不复用过期 Core evidence。

## 6. INDEX.md Deliverables by Wave

| Wave | Mandatory INDEX/document changes |
|---|---|
| 0 | 创建根 `INDEX.md`、每个 service/package public root INDEX、`config/architecture/index-roots.yaml`、`docs/templates/INDEX.md`、`scripts/architecture/check-index-coverage.ts`/`check-dependencies.ts`；重写失真的 `kokoro-web/INDEX.md`，建立 CODEBASE_MAP 链接规则 |
| 1 | Platform root、site/workspace/risk/growth modules、publish/authorize workflows |
| 2A/2B | 2A：catalog/commerce/subscription/fulfillment/credit/usage/redeem；2B：payment/refund/dispute/dunning 与 Provider adapter |
| 3 | Session root、message/branch/projection/admission/control modules；删除 billing/hub/model 旧职责描述 |
| 4 | Job、Artifact、Operation SDK、各 Studio/Library Surface |
| 5A/5B | 5A：Model Gateway、Capability Runtime、Core GA adapter；5B：AgentRevision/Handoff/effect safety |
| 6A-6D | Execution Runtime、Device Gateway、Developer Workspace、Automation、Task Projection、Application Runtime |
| 7 | Admin、notification、data governance、Support/reconciliation/runbook roots |
| 8 | 全仓 dead-link/old-owner/old-env 扫描，迁入 handbook，CURRENT 只指向正式事实源 |
| 9 | 生产入口、部署/rollback/incident runbook、真实验证命令和 Release Evidence 索引 |

INDEX 只描述当前代码；历史保留在 Git 和正式 ADR，不在“当前陷阱”中长期保留已删除架构。

## 7. Verification Ownership

| Evidence | Accountable role | Blocking Waves |
|---|---|---|
| Federated pins/compatibility/INDEX/contract | Architecture + Foundation | 0-9 |
| Unit/property/invariant | Domain Lead + QA | 1、2A/2B、3、5A、4、5B、6A-6D、7 |
| Transaction/migration/reconciliation | Platform/Data | 1、2A/2B、3、7、8/9 instances |
| Runtime/lease/effect/chaos | Runtime/Reliability | 3、5A、4、5B、6A-6D、9 instances |
| Multi-Site/Web/Studio/a11y | Web/Product QA | 1、3、5A、4、7、9 instances |
| Redeem-only certification | Commerce/Security/Support | 2A、7、Core 9 instance |
| Security/privacy/governance | Security/Privacy | 所有实现 cut 与 certification instance |
| Load/soak/DR/rollback | SRE/Data | 每个 8/9 certification instance |

## 8. Implementation Start Gate

第一个允许进入 `superpowers:writing-plans` 精确代码任务的目标是 Wave 0。开始前必须：

- [ ] 用户确认 Umbrella Spec v1.5 与 Product Requirements Governance v1.0 的 ownership、Profile/Journey/PRD Registry、Core/Advanced launch、production/redeem/verification/INDEX addendum。
- [ ] 完成 Wave 0 v2.0 child Spec 与 2026-07-27 执行计划，并按 federated repository 策略列出四个 gitlink 的 provenance、恢复锚点和 pin promotion 步骤。
- [ ] 确认根目录目标和第一批受管 INDEX roots。
- [ ] 确认 CI/部署环境可运行 Node 24、pnpm 11、Python 3.12 和 PostgreSQL 18 测试。
- [ ] 仓库所有者书面确认四个来源仓属于同一 Kokoro 项目的自有内部代码，可登记批准的内部 LicenseRef。

无论上述门禁是否满足，均不得删除 gitlink/`.gitmodules`、导入普通源码树、合并子仓 lock 或关闭子仓
CI/release。门禁只授权 federated pin/contract/Infra/compatibility 工作和其后的业务 Wave。
