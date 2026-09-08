# Kokoro repository status

状态：2026-09-08 · System 完整源码/消费者 HTTP 已验；镜像 RC 环境待验

> 按 [ADR-031](kokoro-handbook/decisions/ADR-031-system-http-nestjs-convergence.md)，Model 业务归 System。
> 本表是活动运行仓清单，不是所有磁盘目录清单。旧 Model checkout/remote 保留作历史源，不归 archived。
> 各仓行内旧 SHA 只作先前基线，最新可运行/已验事实见各仓 CURRENT；System/BFF/Agent 本轮具体 SHA 与边界见 Root CURRENT。

本文件是 Root 对本地目录、GitHub 仓库和代码归属的唯一索引。Root 只保存仓库拓扑、架构文档、部署编排与验证工具；API contract、Schema、生成代码和业务实现必须留在对应独立仓库。子仓之间只通过各 owner 仓库发布的
HTTP/OpenAPI/Protobuf/internal command 契约交互，不通过相对路径导入源代码、数据库或 ORM。

## 正式仓库与 GitHub 映射

| 本地目录 | GitHub 仓库 | 事实/业务边界 | 历史基线（当前见本仓 CURRENT） |
|---|---|---|---|
| kokoro | LordFoxFairy/kokoro-app | Web 产品、同源 /api/*、页面状态/SSE | e1d9eeb |
| kokoro-bff | LordFoxFairy/kokoro-bff | Chat、业务 BFF、Project/Task/ScheduledTask、适配/幂等 | 26eec011 |
| kokoro-agent | LordFoxFairy/kokoro-agent | Run、执行、HITL、恢复、事件投影、HTTP ingress | e24b4aa |
| kokoro-iam | LordFoxFairy/kokoro-iam | 身份、Tenant、认证、授权、审计、ExecutionIdentity | 531816e |
| kokoro-system | LordFoxFairy/kokoro-system | Sites/Hosts/Policy、Workspaces、Products、Runtime Manifest、Model Catalog | 280d5d0（业务d7257aa） |
| kokoro-billing | LordFoxFairy/kokoro-billing | Payment、Subscription、Checkout、Refund、Credit、Ledger | fd80ec4 |
| kokoro-capability | LordFoxFairy/kokoro-capability | Skill、MCP Connector 控制面 | 1de0bf5 |
| kokoro-storage | LordFoxFairy/kokoro-storage | Upload、Asset、Artifact 元数据与 ObjectStore 引用 | a2d05a0 |
| kokoro-scheduler | LordFoxFairy/kokoro-scheduler | 通用 Go 调度、lease、retry、misfire、dispatch | 2f7a3e8 |

Root + 9 个 active child checkout 各为独立 Git root。仅 Agent 是 Root gitlink；其余活动仓为
同目录独立 checkout。当前任务使用各自 `codex/` 分支，不能沿用历史“全是 main/clean”的声明。
`kokoro-model/` 是保留的非活动历史 checkout；本次不删除目录、不归档 GitHub、不改 remote。
用 scripts/audit-repository-state.py 显式读取当前 SHA/分支/dirty，旧报告不等价于本次验收。

## 归属裁决

- Chat 是 kokoro-bff 的内部业务模块；Session 是 BFF v1 API 概念，不存在独立
  kokoro-chat 或 kokoro-session 运行仓。
- Project 的 instruction、resource、task 语义归 BFF；不要将它们伪装成 System Workspace。
- ScheduledTask 定义与业务状态归 BFF；Scheduler 只拥有通用 ScheduleJob、occurrence lease、
  retry/misfire/pause/resume 和 dispatch，不读 Billing、BFF 或其他业务数据库。
- Credit 属于 kokoro-billing，与 Payment、Subscription、Checkout、Refund、Ledger 同仓，
  但保留独立 bounded context、repository、表 owner 与事务边界。
- IAM 与 System 保持独立；System 拥有模型目录与路由，但不持有 IAM 授权事实、provider 明文 secret 或 Billing ledger。
- 正式业务仓统一 PostgreSQL + Redis。PostgreSQL 保存业务事实；Redis 仅作 cache、stream、
  queue、lease、限流和协调；对象字节归 Storage 的 S3-compatible ObjectStore。
- Web 不直连任何 owner、Agent、PostgreSQL 或 Redis；浏览器 X-Domain、X-Forwarded-* 和
  Host 不作为租户身份来源。BFF 从 KOKORO_DOMAIN 生成标准 Forwarded，向 IAM 完成身份/权限 admission，
  再向 System 发送受信 tenant_id + Host；Site/Host binding 由 System 自己校验，再向 owner 发送受信服务上下文。

## 运行链路

    kokoro-app Web
      -> same-origin /api/*
      -> kokoro-bff /v1/*
      -> IAM/System/Billing/Capability/Storage owner contracts
      -> kokoro-agent HTTP ingress
      -> kokoro-scheduler internal command and occurrence replay

BFF live 已接入 System runtime manifest 与 model-catalog、Billing catalog/checkout、
Capability skill/MCP read projection、Storage library projection、Agent Chat
launch/control/replay/detail/session-list。BFF 自有 PostgreSQL/Redis business store 保存 Project/
ScheduledTask，并同步 Scheduler 注册、dispatch 和 durable receipt。未提供 owner ingress
的写操作显式返回稳定的未接线错误，不回退成 mock 成功。

## 契约归属

Root 不保存跨仓 machine-readable contract、Proto、OpenAPI、JSON Schema 或生成器。每个 active repository
在自己的 `docs/api/`、`docs/agent/`、`contract/` 或等价目录维护本仓边界，具体目录由该仓 README 声明。

- Web 的 AG-UI 解析和同源 API 契约由 `kokoro` 自己维护；
- BFF 的公开 HTTP、SSE、Chat 和 AG-UI projection 契约由 `kokoro-bff` 自己维护；
- Agent 的 ingress、Redis command/event protocol 和执行事实契约由 `kokoro-agent` 自己维护；
- 六个业务 owner 各自维护 API、canonical SQL schema、client facade、contract tests、Docker 和 CI。

Root 只做 topology、architecture 和 loopback E2E 编排，不生成、复制或发布 sibling contract。历史报告中的 Root
contract、manifest 和 generator 路径均为迁移记录，不是当前实现入口。

HTTP envelope 以各 owner 的已发布契约为准，不由 Root 复制一套字段。System 成功为 `{data}`，
错误为 `{error:{code,message,retryable}}`，request ID 在 `x-request-id`；BFF 对外投影仍遵循其自身契约。

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
- Root topology/E2E：`scripts/verify-repository-topology.py` 与 `scripts/e2e/`
- 本地/GitHub 审计：scripts/audit-repository-state.py
- 子仓库架构与规范审计：docs/repository-architecture-review-v1.md
