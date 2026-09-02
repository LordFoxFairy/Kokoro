# 阶段 2 最终测试报告

日期：2026-09-02
范围：Root Kokoro、Web、BFF、Agent、7 个业务 owner。
测试方式：先接口契约与边界门禁，再执行各仓实现测试，最后通过独立 checkout 启动真实本地网络链路。
结论：当前提交集合已通过本地 API-first、仓内测试和真实 Web → BFF → owner → Agent/Scheduler
业务闭环。

## 1. 测试环境与隔离

- Web：kokoro-app，Next.js dev/production build。
- BFF：kokoro-bff，production compiled entry，KOKORO_BFF_MODE=live。
- Owner：IAM、System、Model、Billing、Capability、Storage、Scheduler。
- Agent：kokoro-agent worker + Agent HTTP ingress 两个进程。
- 数据依赖：一次性 PostgreSQL 16 + Redis 7；每个 owner 使用独立 PostgreSQL database
  和 Redis logical database，避免跨仓 schema 污染。
- Storage object bytes：本地 disposable ObjectStore fixture。
- 域名上下文：KOKORO_DOMAIN=dev.kokoro.localhost；BFF 生成标准 Forwarded。
- 浏览器的 X-Domain、X-Forwarded-*、Host 不作为 tenant 选择或授权依据。
- E2E finally 会停止临时进程、删除临时 PostgreSQL/Redis 容器并恢复 Web 生成 shim。

## 2. Root contract 与治理用例

| 用例 ID | 覆盖 | 命令 | 结果 |
|---|---|---|---|
| ROOT-001 | 10 个 active child checkout、GitHub remote、废弃目录边界 | python3 scripts/verify-repository-topology.py | PASS |
| ROOT-002 | Root backend design manifest 与文档/源码边界 | python3 scripts/verify-backend-design.py | PASS |
| ROOT-003 | Buf contract lint 与 Root/consumer contract tests | pnpm exec buf lint contract；uv run --frozen pytest contract/tests scripts/contract/tests -q | PASS，82 passed |
| ROOT-004 | Goal 2 七仓文档、Root wire、request_id、幂等、cursor | python3 scripts/goal2/mock_cross_repository_closure.py | PASS |
| ROOT-005 | 两个 machine-readable contract JSON | python3 -m json.tool ... | PASS |
| ROOT-006 | Root 文档和脚本 diff hygiene | git diff --check | PASS |

## 3. 子仓 unit/integration/contract/build

| 仓库 | 用例与命令 | 实际结果 |
|---|---|---|
| kokoro | pnpm check | PASS：112 test files，1120 tests；Next production build 17/17 pages |
| kokoro-bff | pnpm check；pnpm test:integration | PASS：51 tests；覆盖 live adapter、scheduler durable fact/replay、Content-Length |
| kokoro-agent | uv run --frozen pytest -q；ruff check；pyright | PASS：520 passed，6 skipped，61 deselected；ruff/pyright 0 errors |
| kokoro-iam | pnpm verify | PASS：contract 1、unit 11；typecheck/lint/build |
| kokoro-system | pnpm verify | PASS：contract 1、service tests 38、SDK tests 11；typecheck/lint/build |
| kokoro-system | TEST_DATABASE_URL=... TEST_REDIS_URL=... pnpm test:integration | PASS：listener、SDK、tenant isolation、precedence、cache identity、HTTP errors |
| kokoro-model | pnpm check；pnpm verify:release | PASS：127 model tests；production HTTP、Prisma/contract provenance、architecture |
| kokoro-billing | pnpm verify | PASS：45 passed，52 skipped integration；SQL naming 37 migrations；OpenAPI parity 17 routes |
| kokoro-capability | npm run verify | PASS：125 tests，31 test files；contract/typecheck/build |
| kokoro-storage | npm run verify | PASS：86 passed，1 skipped；24 passed test files |
| kokoro-scheduler | go test ./...；go test -race ./...；go vet ./... | PASS：unit、race、vet |

子仓最终提交：

| 仓库 | HEAD |
|---|---|
| kokoro-app | e1d9eeb |
| kokoro-bff | e4a2e4d |
| kokoro-agent | 90fd3e1 |
| kokoro-iam | 8f532a2 |
| kokoro-system | 705fe41 |
| kokoro-model | d8ae5a7 |
| kokoro-billing | f659000 |
| kokoro-capability | 212f51f |
| kokoro-storage | 4d73dd9 |
| kokoro-scheduler | 2f7a3e8 |

## 4. BFF mock 与 live 业务用例

BFF mock evidence：docs/reports/2026-09-01-stage2-bff-mock-e2e.json
结果：43/43 HTTP cases PASS，覆盖鉴权、Project、Skill/GitHub import、MCP、Scheduler、
Agent setup、Library、Billing、Chat/SSE/share/delete、幂等与错误边界。

BFF live evidence：docs/reports/2026-09-01-stage2-owner-health.json

### 健康/就绪

18/18 endpoint checks PASS，11/11 local processes remain running：

- IAM health/ready
- System health/ready
- Model health/ready
- Billing health/ready
- Capability health/ready
- Storage health/ready
- Agent HTTP health/ready
- Scheduler health/ready
- BFF live ready
- Web root

### 真实业务链路

| 用例 ID | 链路 | 预期 | 结果 |
|---|---|---|---|
| LIVE-001 | BFF → IAM admission → System Site/Host binding → runtime manifest | 200，product_id=kokoro | PASS |
| LIVE-002 | BFF → Model catalog | 200，data.models | PASS |
| LIVE-003 | BFF → Capability skills catalog | 200，data.skills | PASS |
| LIVE-004 | BFF → Storage library projection | 200，data.items | PASS |
| LIVE-005 | BFF → Billing plans | 200，data.plans | PASS |
| LIVE-006 | BFF-owned Project fact store | 200，data.projects | PASS |
| LIVE-007 | Chat → Agent HTTP POST /v1/runs | 202，稳定 run_id | PASS |
| LIVE-008 | ScheduledTask fact → Scheduler ScheduleJob register | 200，返回 task id | PASS |
| LIVE-009 | Scheduler dispatch → BFF state gate → Agent | 202，稳定 run receipt | PASS |
| LIVE-010 | 相同 occurrence replay | 202，返回同一 durable receipt | PASS |
| LIVE-011 | Scheduler unregister → BFF ScheduledTask delete | 200，业务事实删除 | PASS |

## 5. 本轮发现并修复的真实问题

1. E2E 所有 owner 复用一个 PostgreSQL database，Model Prisma migration 会遇到
   schema not empty；测试编排改为每个 owner 独立 database/Redis logical database。
2. Agent worker 与 Agent HTTP ingress 并发初始化同一个 Agent schema，可能竞争创建 PostgreSQL
   type；编排先完成 worker schema bootstrap，再启动 HTTP ingress。
3. BFF 到 Agent 的 Node http client 默认使用 chunked body，而 Agent stdlib ingress 只读取
   Content-Length，导致 JSON body 被读成空对象并返回 400；BFF transport 现在明确设置
   Content-Length，并在 live Chat test 中锁定该行为。
4. Root owner-health evidence 只记录失败检查，成功检查没有写入 JSON；脚本已改为记录每一项
   endpoint 的实际状态，报告现在可审计 18/18。
5. Goal 2 manifest 的 Billing/Scheduler root_wire 使用 fragment URI，但 mock gate 只接受文件；
   两者统一引用 Root cross contract 文件，具体 owner fragment 仍由 JSON 的 owner_contracts 提供。
6. Web 全量测试在并行高负载下曾出现一次 Radix/jsdom 3 秒 handoff timeout；单独顺序运行
   kokoro pnpm check 为 114/114 files、1133/1133 tests PASS，当前没有复现。

## 6. CI、镜像与部署

10 个 active child repository 都有独立 CI。普通 push/PR 运行质量门禁；所有 release-image workflow
仅匹配 v*.*.* tag，才执行 GHCR production image publish。Dockerfile 使用生产编译入口，
本地开发使用 dev 命令，不使用 preview image 作为线上镜像。

已观测的最新成功 CI：

- Root Contract：33578709364
- kokoro-app：33589696494
- kokoro-bff：33591015699
- kokoro-agent：33589593922
- kokoro-iam：33582528538
- kokoro-system：33589051942
- kokoro-model：33590093329
- kokoro-billing：33588668697
- kokoro-capability：33588430522
- kokoro-storage：33588402389
- kokoro-scheduler：33586539316

GHCR package visibility 本轮没有修改；当前本机 GitHub CLI 未授予 read:packages，因此不把
“workflow 有 packages:write”误写成“package 已 Public”。这不影响普通 CI、tag 发布规则或本地闭环。

## 7. 最终判定

阶段 2 的当前验收目标已达到：

- active 仓库边界清晰；
- API v1 contract 与 owner contract 有 Root machine-readable authority；
- Web、BFF、Agent、IAM、System、Model、Billing、Capability、Storage、Scheduler 各自闭环；
- BFF live adapter、BFF business facts、Agent ingress、Scheduler register/dispatch/replay 已真实运行；
- 单元、集成、契约、架构、构建和真实网络 E2E 均有证据；
- 废弃仓库不再出现在本地启动路径、manifest、Compose 或 CI；
- Root 最终提交并重新 audit 后，Root 与所有 active child worktree 必须保持 clean 且
  local HEAD == origin/main。
