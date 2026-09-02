# Kokoro 阶段 2：全仓库与跨仓闭环计划

日期：2026-09-02
范围：Root、Web、BFF、Agent、IAM、System、Model、Billing、Capability、Storage、Scheduler。
目标：在不重新引入废弃仓库、不跨仓复制实现、不共享业务数据库的前提下，完成 API-first 的
跨仓契约、owner 接线、真实本地 E2E、各仓单元/集成/契约门禁和可审计测试报告。

## 1. 固定架构裁决

    kokoro-app (Web)
      -> same-origin /api/*
      -> kokoro-bff (Chat + business BFF)
      -> explicit owner adapters
      -> kokoro-agent HTTP ingress
      -> kokoro-scheduler internal dispatch

- Root 只保留跨仓 API 契约、Protobuf/OpenAPI 生成、拓扑索引、文档、部署入口和验证工具。
- 每个正式仓库独立维护源码、测试、Dockerfile、CI、API contract、迁移和 runbook。
- Web 不直连任何 owner、Agent、PostgreSQL 或 Redis；浏览器不提交 X-Domain 作为信任依据。
- Chat 是 BFF 的内部业务模块；Session 是 BFF v1 API 概念，不创建独立 Session/Chat 服务。
- Credit 是 Billing 的 bounded context；Model、IAM、System、Scheduler 保持各自 owner 边界。
- PostgreSQL 保存业务事实；Redis 只做 cache、stream、queue、lease、限流和协调；对象字节归 Storage
  的 S3-compatible ObjectStore。
- kokoro-session、kokoro-gateway、kokoro-platform、旧 kokoro-web、独立 kokoro-credit 和旧 Site
  不得重新加入 Root、Compose、CI、manifest 或新代码。

## 2. 仓库责任矩阵

| 仓库 | 责任 | 真实接线结果 |
|---|---|---|
| kokoro | Next.js Web、同源 API、页面状态和 SSE | 只消费 BFF v1；本地生产构建通过 |
| kokoro-bff | Chat、业务聚合、鉴权、幂等、owner projection | live 接入六类 owner + BFF facts + Scheduler |
| kokoro-agent | Run、执行、HITL、恢复、事件、HTTP ingress | BFF 只走 HTTP ingress，不直连 Agent 存储 |
| kokoro-iam | 身份、Tenant、认证、授权、审计、ExecutionIdentity | tenant-binding v1 HTTP 入口和契约通过 |
| kokoro-system | Site、Workspace、Runtime Manifest、系统策略 | runtime manifest 由 BFF 经 IAM binding 接入 |
| kokoro-model | Catalog、Provider、Availability、Policy | BFF model catalog projection 接入 |
| kokoro-billing | Payment、Subscription、Checkout、Refund、Credit、Ledger | BFF catalog/checkout projection 接入 |
| kokoro-capability | Skill、MCP Connector 控制面 | BFF read projection 接入；未接写操作 fail-closed |
| kokoro-storage | Upload、Asset、Artifact、ObjectStore 引用 | BFF library read projection 接入 |
| kokoro-scheduler | Go 调度、lease、retry、misfire、dispatch | BFF 注册/更新/删除/dispatch/replay 接入 |

## 3. 已执行的阶段 2 收口

### 3.1 契约先于 SQL

Root 已冻结跨仓 JSON 契约：

- HTTP 成功：data + meta.request_id；可分页资源在 data.next_cursor 返回不透明游标；
- HTTP 错误：error.code + error.message + meta.request_id；
- 外部 HTTP 使用 snake_case；owner 内部字段只在 BFF transport adapter 中映射一次；
- mutation 使用 Idempotency-Key；服务调用使用 service credential、X-Request-Id、x-kokoro-request-id
  和标准 Forwarded；
- 浏览器提供的 X-Domain、X-Forwarded-*、Host 不覆盖 IAM 派生的 tenant context；
- Scheduler occurrence 使用 job_name + occurrence 生成稳定幂等键。

Root authority：

- contract/goal2-cross-repository-contract-v1.json
- contract/goal2-repository-contract-manifest.json
- contract/slice-a-contract-manifest.yaml

### 3.2 BFF 与 owner 事实边界

- Project 与 ScheduledTask 的业务定义和用户状态归 BFF PostgreSQL/Redis business store。
- Scheduler 只持有通用 ScheduleJob、lease、retry、misfire、pause/resume 与执行触发，不读任何业务表。
- BFF 将 ScheduledTask 转成 Scheduler job；Scheduler 回调 BFF internal dispatch；BFF 再以保存的身份
  调用 Agent admission；相同 occurrence replay 原始 receipt，不创建第二个 Run。
- System runtime manifest 通过 IAM tenant-binding 再请求 System；Model、Billing、Capability、Storage、
  Agent 均由显式 BFF adapter 投影。
- 不存在 owner ingress 的写操作返回明确的 503/稳定错误，不静默落入 mock 或 generic pass-through。
- BFF→Agent mutation body 发送 Content-Length，保证 stdlib Agent ingress 正确读取 JSON。

### 3.3 废弃治理

本地已移除旧 checkout、旧 gitlink、旧 Compose/k8s/部署入口和旧运行时；GitHub 上
kokoro-session、kokoro-gateway、kokoro-platform、kokoro-web 保持 archived。Credit 和旧 Site
没有正式 remote，不进入 active manifest。

## 4. 验收波次

### Wave A：Root 和每个子仓自洽

- Root contract、topology、backend-design、legacy boundary 门禁通过。
- 每个 active repo 在自身 checkout 通过 typecheck/lint/build/unit/contract/integration/smoke 中适用项。
- 每个 repo 的 Dockerfile 使用生产启动命令；本地 dev 直接运行 dev 命令。
- 普通 push/PR 只做质量检查，v*.*.* tag 才发布 GHCR 生产镜像。

### Wave B：真实 owner health

由 scripts/e2e/run_stage2_owner_health.py 启动隔离的 PostgreSQL/Redis、所有 10 个 active child
checkout 和生产编译入口，验证健康、就绪、Web 根页面和服务存活。每个 owner 使用独立 PostgreSQL
database 和 Redis logical database，避免 E2E 因跨仓 schema 污染而产生假阳性。

### Wave C：真实业务链路

当前已验证：

1. BFF → IAM tenant binding → System runtime manifest；
2. BFF → Model catalog；
3. BFF → Capability skills；
4. BFF → Storage library；
5. BFF → Billing plans；
6. BFF → BFF Project fact；
7. BFF Chat → Agent HTTP admission；
8. BFF ScheduledTask fact → Scheduler job registration；
9. Scheduler dispatch → BFF state gate → Agent admission；
10. 相同 occurrence replay → durable receipt；
11. Scheduler unregister → BFF business fact deletion。

后续增量接线仍按相同 contract-first 方式扩展：先在 owner contract 和 BFF adapter 增加请求/响应/
错误/权限/幂等用例，再改持久化结构；任何新跨仓 surface 必须增加 JSON evidence。

## 5. 测试与证据命令

Root：

    python3 scripts/verify-repository-topology.py
    python3 scripts/verify-backend-design.py
    pnpm exec buf lint contract
    uv run --frozen pytest contract/tests scripts/contract/tests -q
    python3 scripts/goal2/mock_cross_repository_closure.py
    python3 scripts/e2e/run_stage2_owner_health.py --evidence docs/reports/2026-09-01-stage2-owner-health.json

子仓：

    (cd kokoro && pnpm check)
    (cd kokoro-bff && pnpm check && pnpm test:integration)
    (cd kokoro-agent && uv run --frozen pytest -q && uv run --frozen ruff check . && uv run --frozen pyright)
    (cd kokoro-iam && pnpm verify)
    (cd kokoro-system && pnpm verify)
    (cd kokoro-system && TEST_DATABASE_URL=... TEST_REDIS_URL=... pnpm test:integration)
    (cd kokoro-model && pnpm check && pnpm verify:release)
    (cd kokoro-billing && pnpm verify)
    (cd kokoro-capability && npm run verify)
    (cd kokoro-storage && npm run verify)
    (cd kokoro-scheduler && go test ./... && go test -race ./... && go vet ./...)

测试报告必须同时记录：命令、仓库 HEAD、GitHub CI run、用例 ID、预期/实际状态、证据文件、已知环境
边界以及本地临时资源清理结果。

## 6. 完成定义

阶段 2 只有在以下条件同时满足时标记完成：

- Root 和 10 个 active child repository 的本地 HEAD、GitHub main、CI、工作树状态均有记录；
- 4 个历史 GitHub 仓库保持 archived，本地不存在废弃 checkout、旧部署或旧基础设施运行时；
- Root contract 与各 owner contract、生成 consumer provenance、错误/分页/幂等规则通过；
- BFF 每个当前公开 v1 route 都是显式 BFF-owned 实现或显式 owner adapter，没有静默 generic success；
- Agent、Scheduler、Capability、Storage 的真实 ingress/command 有各自仓内测试；
- Web → BFF → owner → Agent/Scheduler 的真实网络 E2E 有健康、成功、幂等 replay、状态门禁和错误证据；
- 最终报告包含测试用例、实际命令、CI 链接、镜像/tag 规则、部署配置和尚未开放的明确边界；
- Root 与所有 active child worktree 最终 clean，且 local HEAD == origin/main。

当前完成证据与仓库状态见：

- docs/reports/2026-09-02-stage2-final-test-report.md
- docs/reports/2026-09-01-stage2-owner-health.json
- docs/reports/2026-09-01-stage2-repository-audit.md
- docs/REPOSITORY_STATUS.md
