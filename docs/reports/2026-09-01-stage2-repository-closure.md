# 阶段 2：Kokoro 全仓与子仓库收口报告

日期：2026-09-02
范围：Root Kokoro、kokoro-app、kokoro-bff、kokoro-agent、7 个业务 owner。
状态：阶段 2 当前目标已完成；最终 clean 状态以提交后的 repository audit 复核为准。

## 1. 最终仓库拓扑

    kokoro-app (Web)
      |
      v
    kokoro-bff (Chat + business BFF)
      +--> IAM / System / Model / Billing / Capability / Storage
      +--> kokoro-agent HTTP ingress
      +--> kokoro-scheduler internal command

Root 只承载跨仓契约、文档、部署入口、审计和测试编排，不承载子仓业务实现或数据库 schema。
10 个 active child GitHub repositories（另有 Root Kokoro）：

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

## 2. 归属裁决

- Web 只访问同源 /api/*；不直连 owner、Agent、PostgreSQL 或 Redis。
- Chat 是 kokoro-bff 内部业务模块；Session 是 BFF v1 API 概念，不创建独立 chat/session 仓。
- Project 的 instruction/resource/task 业务事实归 BFF，不等同于 System Workspace。
- ScheduledTask 定义与业务状态归 BFF；Scheduler 只负责通用 ScheduleJob、lease、retry、
  misfire、pause/resume、dispatch 和 execution receipt。
- Credit 属于 Billing，与 Payment、Subscription、Checkout、Refund、Ledger 同仓，
  但保留 bounded context、表 owner 和事务边界。
- IAM、System、Model 是独立 owner；System 不吸收 IAM 或 Model。
- 统一 PostgreSQL + Redis；Storage 保存对象引用与生命周期，ObjectStore 保存对象字节。

## 3. API-first 契约

Root authority：

- contract/goal2-cross-repository-contract-v1.json：跨仓 wire、trusted context、owner、
  BFF ownership、error、idempotency 和 Scheduler dispatch。
- contract/goal2-repository-contract-manifest.json：7 个 Goal 2 owner 注册表。
- contract/slice-a-contract-manifest.yaml：Root consumer provenance 基线。

HTTP v1：

    success = {data, meta:{request_id, next_cursor?}}
    error   = {error:{code,message}, meta:{request_id}}

外部 HTTP 使用 snake_case；BFF 对 owner camelCase 只做一次 transport projection。
mutation 必须有 Idempotency-Key；服务间使用 service credential、X-Request-Id、
x-kokoro-request-id 和 Forwarded。浏览器的 X-Domain、X-Forwarded-* 和 Host 不构成信任输入。

## 4. 真实接线与事实流

- BFF → IAM tenant binding → System runtime manifest。
- BFF → Model catalog。
- BFF → Capability skill/MCP read projection。
- BFF → Storage library projection。
- BFF → Billing catalog/checkout projection。
- BFF business store 保存 Project/ScheduledTask，并使用 Redis 做缓存/协调。
- BFF → Agent HTTP ingress 完成 Chat launch/control/replay/detail。
- BFF → Scheduler 完成 ScheduleJob register/update/delete/retry。
- Scheduler dispatch → BFF state gate → Agent admission。
- 同一 Scheduler occurrence replay 返回原 durable receipt，不启动第二个 Agent Run。
- 所有未接入的写操作显式 fail-closed，不静默 generic pass-through 或伪造 mock 成功。

## 5. 废弃处理

本地 active topology 已移除：

- kokoro-session
- kokoro-gateway
- kokoro-platform
- kokoro-web
- kokoro-credit
- kokoro-site-kokoro

GitHub 的 kokoro-session、kokoro-gateway、kokoro-platform、kokoro-web 保持 archived。
kokoro-credit 和 kokoro-site-kokoro 没有正式 remote。旧 Compose、k8s、deployment、MySQL/
Mongo 运行时不在当前启动路径；历史文档只作迁移考古。

## 6. 测试结论

- Root contract：82 passed；Buf lint、JSON validation、topology、backend-design、mock closure PASS。
- Web：114 test files / 1133 tests PASS；Next production build PASS。
- BFF：28 unit/contract + 1 integration PASS。
- Agent：501 passed，6 skipped，61 deselected；ruff、pyright PASS。
- IAM：contract 1 + tests 11 PASS；build PASS。
- System：contract 1 + service tests 38 + SDK tests 11 PASS；integration smoke PASS。
- Model：127 tests PASS；production release verification PASS。
- Billing：66 passed、52 skipped integration；SQL naming 37 migrations；OpenAPI parity 48 routes。
- Capability：123 tests PASS。
- Storage：83 passed、1 skipped。
- Scheduler：go test、race、vet PASS。
- BFF mock E2E：43/43 PASS。
- Live owner E2E：18/18 health/readiness endpoints、11/11 process、11/11 business cases PASS。

完整测试矩阵和逐用例说明见 docs/reports/2026-09-02-stage2-final-test-report.md；
可重复 JSON 证据见 docs/reports/2026-09-01-stage2-owner-health.json。

## 7. 发布与部署

- 每个 active 仓库独立维护 Dockerfile、CI、deploy.md/runbook。
- 普通 push/PR 只执行质量门禁；v*.*.* tag 才执行 GHCR production image workflow。
- Dockerfile 使用生产编译入口；本地开发直接使用 dev，不使用 preview image 作为线上版本。
- Cloudflare/DNS、JWKS、provider、webhook、数据库、Redis 和 ObjectStore 凭据由部署环境注入。
- GHCR package visibility 本轮不做隐式变更；本机 GitHub CLI 没有 read:packages scope，不宣称
  package 已 Public。

## 8. 最终收口动作

提交 Root 本轮契约、脚本、文档、报告和 kokoro-agent gitlink 后：

    python3 scripts/audit-repository-state.py --github
    git status --short --branch

预期：audit PASS；Root 与 10 个 active child checkout 的 local main == origin/main；Root 与所有 child
worktree clean；没有废弃路径或临时基础设施容器残留。
