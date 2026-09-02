# 阶段 2 全仓审计

日期：2026-09-02
范围：Root Kokoro、10 个 active child repository、4 个 archived GitHub repository。
执行方式：只读审计本地 Git root、origin/main、GitHub repository metadata、active boundary 和废弃路径；
不会归档、删除、推送或修改 package visibility。

## 1. Active repository 状态

| 本地目录 | GitHub | HEAD | 状态 |
|---|---|---|---|
| Root | LordFoxFairy/Kokoro | final audit output | active |
| kokoro | LordFoxFairy/kokoro-app | 00a2139 | clean，main 对齐 |
| kokoro-bff | LordFoxFairy/kokoro-bff | b3c3994 | clean，main 对齐 |
| kokoro-agent | LordFoxFairy/kokoro-agent | a8284b3 | clean，main 对齐 |
| kokoro-iam | LordFoxFairy/kokoro-iam | 02743c1 | clean，main 对齐 |
| kokoro-system | LordFoxFairy/kokoro-system | 34131f6 | clean，main 对齐 |
| kokoro-model | LordFoxFairy/kokoro-model | 794648a | clean，main 对齐 |
| kokoro-billing | LordFoxFairy/kokoro-billing | aca1412 | clean，main 对齐 |
| kokoro-capability | LordFoxFairy/kokoro-capability | b5dc19e | clean，main 对齐 |
| kokoro-storage | LordFoxFairy/kokoro-storage | 5d5669e | clean，main 对齐 |
| kokoro-scheduler | LordFoxFairy/kokoro-scheduler | 90d9776 | clean，main 对齐 |

Root 只维护跨仓契约、文档、部署入口、审计和测试编排；kokoro-agent 是唯一 Root gitlink，
其余 active child 是同目录独立 Git checkout。最终状态使用：

    python3 scripts/audit-repository-state.py --github

复核，输出必须是 PASS、Root 与 10 个 active child checkout clean、local HEAD == origin/main。

## 2. GitHub 与废弃仓库

已确认 active GitHub repositories：

- LordFoxFairy/Kokoro
- LordFoxFairy/kokoro-app
- LordFoxFairy/kokoro-bff
- LordFoxFairy/kokoro-agent
- LordFoxFairy/kokoro-iam
- LordFoxFairy/kokoro-system
- LordFoxFairy/kokoro-model
- LordFoxFairy/kokoro-billing
- LordFoxFairy/kokoro-capability
- LordFoxFairy/kokoro-storage
- LordFoxFairy/kokoro-scheduler

已确认 archived：

- LordFoxFairy/kokoro-session
- LordFoxFairy/kokoro-gateway
- LordFoxFairy/kokoro-platform
- LordFoxFairy/kokoro-web

kokoro-credit 和 kokoro-site-kokoro 没有正式 GitHub remote；它们已从本地 active topology、
Compose、CI 和 manifest 移除。历史提交和 Root handbook 中的迁移材料不属于运行时依赖。

## 3. 结构与边界审计

- active topology 只有 Web、BFF、Agent 和七个业务 owner。
- 不存在旧 session/gateway/platform/web/credit/site 的 active checkout 或默认启动入口。
- Root manifest 注册 7 个 Goal 2 owner；Root cross contract 注册 IAM、System、Model、Billing、
  Capability、Storage、Agent、Scheduler。
- Project/ ScheduledTask 业务事实归 BFF；Scheduler 只持有 ScheduleJob 和 occurrence lease。
- Credit 归 Billing；Chat/Session 归 BFF 内部模块/API 概念；IAM 与 System、Model 保持独立。
- 没有跨仓 source import、共享 ORM/schema、BFF 直读 Agent 数据库或浏览器直连 owner。
- 默认数据基线是 PostgreSQL + Redis；对象字节经 Storage ObjectStore。
- BFF 出站使用服务凭据、X-Request-Id、x-kokoro-request-id 和标准 Forwarded；
  浏览器 X-Domain 不作为信任上下文。

## 4. 机器门禁与测试证据

已通过：

- scripts/verify-repository-topology.py
- scripts/verify-backend-design.py
- pnpm exec buf lint contract
- uv run --frozen pytest contract/tests scripts/contract/tests -q：82 passed
- scripts/goal2/mock_cross_repository_closure.py
- 10 个 active child 仓的本仓 unit/integration/contract/build gates
- BFF mock E2E：43/43
- owner-health + live business E2E：18/18 endpoint、11/11 process、11/11 business cases
- git diff --check

真实 live E2E 证据：

    docs/reports/2026-09-01-stage2-owner-health.json

测试明细：

    docs/reports/2026-09-02-stage2-final-test-report.md

## 5. CI 与发布审计

最新已观测成功 CI：

| 仓库 | Run |
|---|---|
| Root Contract | 33578709364 |
| kokoro-app | 33589696494 |
| kokoro-bff | 33591015699 |
| kokoro-agent | 33589593922 |
| kokoro-iam | 33582528538 |
| kokoro-system | 33589051942 |
| kokoro-model | 33590093329 |
| kokoro-billing | 33588668697 |
| kokoro-capability | 33588430522 |
| kokoro-storage | 33588402389 |
| kokoro-scheduler | 33586539316 |

每个 active child 都有独立 CI 和 release-image workflow。普通 push/PR 只做质量检查；
只有 v*.*.* tag 发布生产 GHCR 镜像。Dockerfile 使用生产启动入口，本地开发使用本仓 dev
命令。GHCR package visibility 本轮没有修改；本机 GitHub CLI 没有 read:packages scope，
所以审计不将 packages:write 推断为 Public。

## 6. 结论

仓库拓扑、归属、Root contract、子仓自洽门禁、BFF live 接线、Agent HTTP ingress、
Scheduler registration/dispatch/replay 和废弃路径已经完成本轮阶段 2 收口。Root 最后提交后，
必须再次运行只读 audit，确认 Root 本身和所有 active child 均 clean；此审计不替代真实生产
凭据、Cloudflare/DNS、JWKS、provider 或 GHCR visibility 的部署授权验证。
