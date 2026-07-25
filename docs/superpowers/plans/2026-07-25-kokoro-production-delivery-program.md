# Kokoro Production Delivery Program Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement each approved child plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 Kokoro 从当前多子仓/旧边界 clean replace 为可直接上线的多 Site AI 产品，并以 `redeem_only` 完成首个真实 acquisition→Fulfillment→Grant→Usage 生产闭环。

**Architecture:** 本文件是实施总控索引，不授权直接修改业务代码。整体按 Wave 0-9 拆成十份独立子 Spec 和十份精确实现计划；每个 Wave 只在依赖、测试证据、INDEX/文档与同波旧实现清理全部完成后退出。Platform 使用模块化 Core，Session/Job/Capability/Model Gateway/GA 等保持独立运行边界，一 Site 一 Web Project，共享后端。

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

Program 只有在以下条件同时成立时 complete：

- [ ] Wave 0-9 全部退出。
- [ ] 启用的用户、Admin 和 Support 旅程不存在 stub/mock/手工数据库步骤。
- [ ] `redeem_only` production certification 与完整 Release Checklist 通过。
- [ ] 旧代码、表、env、header、兼容 adapter、测试和失真 INDEX/文档清零。
- [ ] Production RC 通过 security、load、soak、chaos、backup restore、rollback 和 Go/No-Go。

## 2. Mandatory Child Spec and Plan Set

每行必须依次完成 `child Spec → 用户书面复审 → writing-plans child plan → implementation → evidence → cleanup`。

| Wave | Child Spec filename | Child implementation plan filename | Production-capable exit |
|---|---|---|---|
| 0 | `2026-07-25-wave-0-repository-contract-foundation-design.md` | `2026-07-25-wave-0-repository-contract-foundation-implementation-plan.md` | 真 Monorepo、根 lock/catalog、contract generation、INDEX governance、CI architecture gate |
| 1 | `2026-07-25-wave-1-platform-site-policy-design.md` | `2026-07-25-wave-1-platform-site-policy-implementation-plan.md` | PlatformUnitOfWork、SiteContext/Release、Experiment、Restriction token/epoch、双 Release drain |
| 2 | `2026-07-25-wave-2-commerce-redeem-credit-design.md` | `2026-07-25-wave-2-commerce-redeem-credit-implementation-plan.md` | Catalog/Subscription/Fulfillment/Credit/Usage 与 Redeem-only certification |
| 3 | `2026-07-25-wave-3-session-admission-projection-design.md` | `2026-07-25-wave-3-session-admission-projection-implementation-plan.md` | Session 商业逻辑清零、typed parts、branch、reconnect、AuthorizationSegment |
| 4 | `2026-07-25-wave-4-operation-job-artifact-studio-design.md` | `2026-07-25-wave-4-operation-job-artifact-studio-implementation-plan.md` | Direct/Agent Operation、durable Job、ArtifactVersion、Image/Music/Video Studio |
| 5 | `2026-07-25-wave-5-model-capability-agent-safety-design.md` | `2026-07-25-wave-5-model-capability-agent-safety-implementation-plan.md` | 单 Model Gateway、Capability Runtime、真实 Handoff、effect/epoch safety |
| 6 | `2026-07-25-wave-6-agent-product-plane-design.md` | `2026-07-25-wave-6-agent-product-plane-implementation-plan.md` | Target/Permission/Workspace/Memory/Routine/TaskView/AgentTeam/Application Runtime |
| 7 | `2026-07-25-wave-7-admin-governance-operations-design.md` | `2026-07-25-wave-7-admin-governance-operations-implementation-plan.md` | Site Fleet、财务/运行专用流程、Risk Case、Export/Deletion、Notification、Support |
| 8 | `2026-07-25-wave-8-clean-cutover-documentation-design.md` | `2026-07-25-wave-8-clean-cutover-documentation-implementation-plan.md` | 旧事实源清零，handbook/ADR/INDEX/CODEBASE_MAP/runbook 与唯一实现一致 |
| 9 | `2026-07-25-wave-9-production-certification-launch-design.md` | `2026-07-25-wave-9-production-certification-launch-implementation-plan.md` | RC EvidenceBundle、真实 redeem-only 纵切、Go/No-Go、canary、rollback、on-call |

不得预创建空 child 文件。开始某 Wave 时完整设计并复审，避免占位文档伪装成完成。

## 3. Wave Execution Protocol

每个 Wave 都执行相同步骤；child plan 必须进一步拆成 2-5 分钟动作、精确文件、测试和 commit。

- [ ] **Step 1: Freeze the child scope**

  从 Umbrella Spec 复制该 Wave 的对象、状态、不变量、接口、事件、失败场景、删除清单和退出门；明确非目标和依赖。

- [ ] **Step 2: Inspect actual code and adjacent INDEX files**

  读取真实 imports/exports、schema、migration、test、deployment entrypoint。记录要保留、替换和删除的准确路径，不从旧文档推测代码。

- [ ] **Step 3: Write and review the child Spec**

  子 Spec 必须冻结数据 owner、合法状态转移、command/event schema、幂等键、transaction boundary、security/recovery 和 cutover；用户批准前不写实现计划。

- [ ] **Step 4: Generate the exact child implementation plan**

  使用 `superpowers:writing-plans`；每个代码步骤给出完整 snippet、精确命令和预期失败/成功，采用 TDD 和小 commit。

- [ ] **Step 5: Create an isolated implementation worktree**

  使用 `superpowers:using-git-worktrees`；多个 worker 只按互不重叠的文件/模块切分，禁止共同修改同一 migration、contract 或 barrel export。

- [ ] **Step 6: Execute with two-stage review**

  推荐 `superpowers:subagent-driven-development`；每个任务先审 spec compliance，再审 code quality。子代理成功不替代主仓 verification。

- [ ] **Step 7: Run the Wave evidence matrix**

  至少包含 static、unit/property、component、contract、integration、targeted E2E、failure/security；涉及 runtime/transaction 的 Wave 不能只靠 mock。

- [ ] **Step 8: Clean cut in the same Wave**

  删除被替代的代码、表、env、header、compat、注释、测试和 INDEX 描述；`rg` 和 dependency tests 证明不存在旧入口。

- [ ] **Step 9: Update architecture maps and reports**

  同 commit 更新受影响 INDEX、生成契约、runbook、ADR/CODEBASE_MAP 和 Wave report；不得留下两个当前事实源。

- [ ] **Step 10: Exit only with fresh main-worktree verification**

  在主工作树重新运行 child plan 的全部 gate，生成 commit/image/contract digests 和证据索引；失败则 Wave 保持 active。

## 4. Dependency and Parallel Cuts

```text
Wave 0
  → Wave 1
      → Wave 2 ─────────────┐
      → Wave 3 (read contracts may parallel Wave 2)
            └───────────────→ Wave 4
Wave 4 + Wave 5 safety contract
  → Wave 6A/6B/6C/6D implementation cuts
  → Wave 7
  → Wave 8
  → Wave 9
```

允许并行：

- Wave 2 领域实现与 Wave 3 只读 contract/projection 设计，在 Admission/Rating contract 冻结后并行。
- Wave 4 Job/Artifact 与 Wave 5 GA 内部 epoch/effect safety 按不同文件树并行；Gateway/Capability 切换必须串行过 contract gate。
- Wave 6 的 Target/Permission、Developer Workspace、Automation/TaskView、AgentTeam/Application Runtime 在共同 contract 冻结后按包并行。
- 每个 Site Web Project 可以在共享 Surface contract 冻结后并行，但同一 Site 的 route/release owner 唯一。

禁止并行：

- 根 contract schema 与生成物的两个写者。
- 同一数据库 migration chain 的两个写者。
- PlatformUnitOfWork/Fulfillment/CreditJournal authority 的并行替代实现。
- Site active Release pointer、root lock/catalog、barrel export 和 CODEBASE_MAP 的无 owner 并发写。

## 5. Vertical Release Slices

各 Wave 必须保持可测试，但以下 slice 才形成用户价值：

### Slice A — Trusted Site Bootstrap

Wave 0-1 后证明：两个独立 Web artifact 只能交换自己的 SiteContext，Release compile/promote/rollback 可审计，未实现功能不可见且 API fail closed。

### Slice B — Redeem Acquisition

Wave 2 后证明：生产形态无 Payment secret 也能启动，用户兑换 Code 原子取得 Subscription/Entitlement/Credit；Admin 可生成、一次性导出、暂停、compromise、撤销和补发。

### Slice C — Usable AI Product

Wave 3-5 后证明：用户从兑换额度进入 Chat/Studio，Run/Job 可恢复，Artifact 可追踪，Model/Capability/GA 副作用安全，Credit 可结算。

### Slice D — Advanced Agent Product

Wave 6 后证明：Local/Cloud Target、Worktree、Permission、Routine、TaskView、多端和 AgentTeam 复用同一业务/执行体系。

### Slice E — Operable Production

Wave 7-9 后证明：运营、Support、Risk、Deletion、Notification、on-call、DR、rollback、文档和 RC evidence 全部闭环，才允许真实流量。

## 6. INDEX.md Deliverables by Wave

| Wave | Mandatory INDEX/document changes |
|---|---|
| 0 | 创建根 `INDEX.md`、每个 service/package public root INDEX、`config/architecture/index-roots.yaml`、`docs/templates/INDEX.md`、`scripts/architecture/check-index-coverage.ts`/`check-dependencies.ts`；重写失真的 `kokoro-web/INDEX.md`，建立 CODEBASE_MAP 链接规则 |
| 1 | Platform root、site/workspace/risk/growth modules、publish/authorize workflows |
| 2 | catalog/commerce/subscription/fulfillment/credit/usage/payment/redeem workflows 与 Admin redeem surface |
| 3 | Session root、message/branch/projection/admission/control modules；删除 billing/hub/model 旧职责描述 |
| 4 | Job、Artifact、Operation SDK、各 Studio/Library Surface |
| 5 | Model Gateway、Capability Runtime、GA assembly/execution/Handoff/effect safety |
| 6 | Execution Runtime、Device Gateway、Developer Workspace、Automation、Task Projection、Application Runtime |
| 7 | Admin、notification、data governance、Support/reconciliation/runbook roots |
| 8 | 全仓 dead-link/old-owner/old-env 扫描，迁入 handbook，CURRENT 只指向正式事实源 |
| 9 | 生产入口、部署/rollback/incident runbook、真实验证命令和 Release Evidence 索引 |

INDEX 只描述当前代码；历史保留在 Git 和正式 ADR，不在“当前陷阱”中长期保留已删除架构。

## 7. Verification Ownership

| Evidence | Accountable role | Blocking Waves |
|---|---|---|
| Architecture/import/INDEX/contract | Architecture + Foundation | 0-9 |
| Unit/property/invariant | Domain Lead + QA | 1-7 |
| Transaction/migration/reconciliation | Platform/Data | 1-3, 7-9 |
| Runtime/lease/effect/chaos | Runtime/Reliability | 3-6, 9 |
| Multi-Site/Web/Studio/a11y | Web/Product QA | 1, 3-4, 7, 9 |
| Redeem-only certification | Commerce/Security/Support | 2, 7, 9 |
| Security/privacy/governance | Security/Privacy | 1-9 |
| Load/soak/DR/rollback | SRE/Data | 8-9 |

## 8. Implementation Start Gate

第一个允许进入 `superpowers:writing-plans` 精确代码任务的目标是 Wave 0。开始前必须：

- [ ] 用户确认 Umbrella Spec v1.3 的 production/redeem/verification/INDEX addendum。
- [ ] 完成 Wave 0 child Spec，并按 Umbrella Spec 冻结的 pinned snapshot import 策略列出四个 gitlink
  provenance、归档和 cutover 步骤。
- [ ] 确认根目录目标和第一批受管 INDEX roots。
- [ ] 确认 CI/部署环境可运行 Node 24、pnpm 11、Python 3.12 和 PostgreSQL 18 测试。

未满足上述四项时，不执行 gitlink 删除、目录迁移、lockfile 重建或业务代码修改。
