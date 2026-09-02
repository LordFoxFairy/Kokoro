# Kokoro repository status

状态：2026-09-02 · 阶段 2 全仓治理与真实本地闭环基线

本文件是 Root 对本地目录、GitHub 仓库和代码归属的唯一索引。Root 只保存跨仓契约、
文档、部署编排与验证工具；业务实现必须留在对应独立仓库。子仓之间只通过 Root 发布的
HTTP/OpenAPI/Protobuf/internal command 契约交互，不通过相对路径导入源代码、数据库或 ORM。

## 正式仓库与 GitHub 映射

| 本地目录 | GitHub 仓库 | 事实/业务边界 | 当前 HEAD |
|---|---|---|---|
| kokoro | LordFoxFairy/kokoro-app | Web 产品、同源 /api/*、页面状态/SSE | e49cd44 |
| kokoro-bff | LordFoxFairy/kokoro-bff | Chat、业务 BFF、Project/Task/ScheduledTask、适配/幂等 | e4a2e4d |
| kokoro-agent | LordFoxFairy/kokoro-agent | Run、执行、HITL、恢复、事件投影、HTTP ingress | 90fd3e1 |
| kokoro-iam | LordFoxFairy/kokoro-iam | 身份、Tenant、认证、授权、审计、ExecutionIdentity | 8f532a2 |
| kokoro-system | LordFoxFairy/kokoro-system | Site、Workspace、Runtime Manifest、系统策略 | b907fc2 |
| kokoro-model | LordFoxFairy/kokoro-model | Model Catalog、Provider、Availability、Policy | 11c0fc2 |
| kokoro-billing | LordFoxFairy/kokoro-billing | Payment、Subscription、Checkout、Refund、Credit、Ledger | f659000 |
| kokoro-capability | LordFoxFairy/kokoro-capability | Skill、MCP Connector 控制面 | 82a7afe |
| kokoro-storage | LordFoxFairy/kokoro-storage | Upload、Asset、Artifact 元数据与 ObjectStore 引用 | 06221f3 |
| kokoro-scheduler | LordFoxFairy/kokoro-scheduler | 通用 Go 调度、lease、retry、misfire、dispatch | d9fa0e1 |

Root + 10 个 active child checkout 均为独立 Git root，当前分支均为 main，且本地与 GitHub
origin/main 已对齐；每个 GitHub 仓库的远端分支也只保留 main。Root 的 gitlink
kokoro-agent 指向 90fd3e1；其余 9 个目录是同目录独立 checkout，不是 Root 的业务子目录。
最终提交后用 scripts/audit-repository-state.py --github --json 复核 clean、main 和分支状态。

## 归属裁决

- Chat 是 kokoro-bff 的内部业务模块；Session 是 BFF v1 API 概念，不存在独立
  kokoro-chat 或 kokoro-session 运行仓。
- Project 的 instruction、resource、task 语义归 BFF；不要将它们伪装成 System Workspace。
- ScheduledTask 定义与业务状态归 BFF；Scheduler 只拥有通用 ScheduleJob、occurrence lease、
  retry/misfire/pause/resume 和 dispatch，不读 Billing、BFF 或其他业务数据库。
- Credit 属于 kokoro-billing，与 Payment、Subscription、Checkout、Refund、Ledger 同仓，
  但保留独立 bounded context、repository、表 owner 与事务边界。
- IAM、System、Model 保持独立；System 不持有 IAM 授权事实、Model provider secret 或 Billing ledger。
- 正式业务仓统一 PostgreSQL + Redis。PostgreSQL 保存业务事实；Redis 仅作 cache、stream、
  queue、lease、限流和协调；对象字节归 Storage 的 S3-compatible ObjectStore。
- Web 不直连任何 owner、Agent、PostgreSQL 或 Redis；浏览器 X-Domain、X-Forwarded-* 和
  Host 不作为租户身份来源。BFF 从 KOKORO_DOMAIN 生成标准 Forwarded，向 IAM 完成身份/权限 admission，
  再向 System 发送受信 tenant_id + Host；Site/Host binding 由 System 自己校验，再向 owner 发送受信服务上下文。

## 运行链路

    kokoro-app Web
      -> same-origin /api/*
      -> kokoro-bff /v1/*
      -> IAM/System/Model/Billing/Capability/Storage owner contracts
      -> kokoro-agent HTTP ingress
      -> kokoro-scheduler internal command and occurrence replay

BFF live 已接入 System runtime manifest、Model catalog、Billing catalog/checkout、
Capability skill/MCP read projection、Storage library projection、Agent Chat
launch/control/replay/detail/session-list。BFF 自有 PostgreSQL/Redis business store 保存 Project/
ScheduledTask，并同步 Scheduler 注册、dispatch 和 durable receipt。未提供 owner ingress
的写操作显式返回稳定的未接线错误，不回退成 mock 成功。

## 契约规则

Root machine-readable authority：

- contract/goal2-cross-repository-contract-v1.json：跨仓 wire、可信上下文、owner、错误和
  Scheduler dispatch authority。
- contract/goal2-repository-contract-manifest.json：7 个领域 owner 注册表和契约索引；Agent
  的 runtime wire 由 Root cross-repository contract 单独登记。
- contract/slice-a-contract-manifest.yaml：Root 生成 consumer 的 provenance 基线。

HTTP v1 成功 envelope（列表响应示例）：

    {"data": {"items": [], "next_cursor": "CURSOR_OR_NULL"}, "meta": {"request_id": "REQUEST_ID"}}

HTTP v1 错误 envelope：

    {"error": {"code": "STABLE_ERROR_CODE", "message": "LOG_SAFE_MESSAGE"}, "meta": {"request_id": "REQUEST_ID"}}

外部 HTTP 字段使用 snake_case；owner 内部类型可以使用 camelCase，但 BFF 只做一次明确
transport projection。每个 mutation 必须携带 Idempotency-Key；BFF/owner 保存 durable receipt。
服务间使用 service credential、X-Request-Id、x-kokoro-request-id 与 Forwarded；浏览器身份字段
不会覆盖 IAM-derived context。

## 子仓自洽门禁

每个 active repository 必须在自身 checkout 内完成：

1. README、API contract、integration/runbook/acceptance/risk 文档；
2. 本仓 unit、integration、contract、architecture/smoke 测试；
3. push/PR 只执行质量门禁；
4. 只有 v*.*.* tag 触发 GHCR 生产镜像发布，普通 push 不发布镜像；
5. Dockerfile 使用生产启动入口；本地开发直接使用本仓 dev/test 命令；
6. 不读取 sibling source，不共享 sibling database/table/schema，不信任浏览器自定义域名 header。

## 已废弃并归档

| 名称 | GitHub 状态 | 当前处理 |
|---|---|---|
| kokoro-session | LordFoxFairy/kokoro-session archived | 不在 Root、Compose、CI、manifest |
| kokoro-gateway | LordFoxFairy/kokoro-gateway archived | 不在 Root、Compose、CI、manifest |
| kokoro-platform | LordFoxFairy/kokoro-platform archived | 不在 Root、Compose、CI、manifest |
| kokoro-web | LordFoxFairy/kokoro-web archived | 旧 monorepo，不再作为 Web 入口 |
| kokoro-credit | 无正式远程仓 | Credit 已并入 Billing |
| kokoro-site-kokoro | 无正式远程仓 | 旧 Site 占位目录已移除 |

归档远程仓保留历史提交；本机不保留旧仓源码、旧部署、旧全栈 Compose、旧 MySQL/Mongo
运行时或旧 infrastructure 容器。历史 handbook/report 只作迁移考古，并明确标记为历史材料。

## 证据

- 阶段 2 最终测试报告：docs/reports/2026-09-02-stage2-final-test-report.md
- live owner health：docs/reports/2026-09-01-stage2-owner-health.json
- 仓库审计：docs/reports/2026-09-01-stage2-repository-audit.md
- 跨仓 mock closure：scripts/goal2/mock_cross_repository_closure.py
- 本地/GitHub 审计：scripts/audit-repository-state.py
- 子仓库架构与规范审计：docs/repository-architecture-review-v1.md
