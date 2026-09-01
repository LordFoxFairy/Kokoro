# Kokoro repository status

状态：2026-09-01 · 阶段 2 全仓治理基线

这份文件是 Root 对本地目录、GitHub 仓库和代码归属的唯一索引。Root 只保存跨仓契约、文档、部署编排与验证工具；业务实现必须留在对应独立仓库。子仓之间只通过 Root 发布的 HTTP/OpenAPI/Protobuf 契约交互，不通过相对路径导入源代码、数据库或内部模块。

## 正式仓库

| 本地目录 | GitHub 仓库 | 角色 | 状态 |
|---|---|---|---|
| `kokoro` | `LordFoxFairy/kokoro-app` | Web 产品，Next.js；浏览器只访问同源 `/api/*` | active |
| `kokoro-bff` | `LordFoxFairy/kokoro-bff` | Web-facing BFF；Chat 是其内部模块，承接业务适配 | active |
| `kokoro-agent` | `LordFoxFairy/kokoro-agent` | Agent worker；执行、HITL、恢复、事件投影 | active |
| `kokoro-iam` | `LordFoxFairy/kokoro-iam` | 身份、租户、认证、授权、审计、ExecutionIdentity | active · contract-first baseline |
| `kokoro-system` | `LordFoxFairy/kokoro-system` | Site、Workspace、Runtime Manifest、系统配置与策略 | active |
| `kokoro-model` | `LordFoxFairy/kokoro-model` | Model Catalog、Provider、Availability、Model Policy | active |
| `kokoro-billing` | `LordFoxFairy/kokoro-billing` | Payment、Subscription、Checkout、Refund、Credit、Ledger | active |
| `kokoro-capability` | `LordFoxFairy/kokoro-capability` | Skill 与 MCP Connector 控制面 | active |
| `kokoro-storage` | `LordFoxFairy/kokoro-storage` | File、Upload、Asset、Artifact 元数据与 ObjectStore 引用 | active |
| `kokoro-scheduler` | `LordFoxFairy/kokoro-scheduler` | 通用 Go 调度、lease、retry、misfire、pause/resume | active |

`kokoro-iam` 当前以 contract-first baseline 独立维护：健康/就绪端点、环境契约、Protobuf snapshot、构建、测试与发布入口已经在本仓收口；身份业务端点按 `docs/API_CONTRACT.md` 继续分批实现，不把未实现端点伪装成已完成能力。

## 明确归属

- Chat 不再是独立仓库；它位于 `kokoro-bff` 的 Chat 业务模块边界，负责 Web-facing session/message/SSE 的业务适配。Agent 仍负责执行事实，BFF 不直接读取 Agent 数据库。
- Session 不再是独立仓库；旧 ProductSession/SSE 原型归入 BFF/Web 的迁移材料，新的对外会话 API 由 BFF v1 契约承接。
- Credit 属于 `kokoro-billing`，与 Payment、Subscription、Checkout、Refund、Ledger 在同一个 Billing 仓库内，但保持独立 bounded context、repository、表 owner 和事务边界。
- `kokoro-scheduler` 保持独立 Go 仓库；它只触发目标业务的内部 command，不读取 Billing 或其他业务数据库。
- `kokoro-system` 是系统控制面，不是所有业务仓库的父仓，也不持有 IAM 凭据、授权事实或 Model Provider 密钥。
- Storage 的对象字节由 S3-compatible ObjectStore 保存，PostgreSQL 保存生命周期与引用元数据，Redis 只做 cache/coordination/lease。
- 所有正式业务仓统一采用 PostgreSQL + Redis；禁止新增 MySQL/Mongo 运行时。

## 阶段运行入口

当前可运行的三仓 Phase 1 入口是：

```text
kokoro-app (Web) -> kokoro-bff (Chat/业务 BFF) -> kokoro-agent (worker)
                                  \\-> Goal 2 业务仓 HTTP/RPC contracts
```

本地三仓启动文件是 [`deploy/docker-compose.phase1.yml`](../deploy/docker-compose.phase1.yml)，生产镜像入口是各仓自己的 Dockerfile。Root 外的 `Kokoro-archive-2026-09-01/root-legacy/` 保存历史迁移夹具；Root 内不再保留旧 Compose、k8s 或全栈 provisioning 入口。

## 已废弃并归档

以下目录和仓库不再加入新功能，也不再作为依赖：

| 本地目录 | GitHub 仓库 | 处理 |
|---|---|---|
| `kokoro-session` | `LordFoxFairy/kokoro-session` | archive；移出 Root 工作区 |
| `kokoro-gateway` | `LordFoxFairy/kokoro-gateway` | archive；移出 Root 工作区 |
| `kokoro-platform` | `LordFoxFairy/kokoro-platform` | archive；移出 Root 工作区 |
| `kokoro-web` | `LordFoxFairy/kokoro-web` | archive；旧 pnpm monorepo，由 `kokoro-app` 替代 |
| `kokoro-credit` | 无正式远程仓库 | 移出 Root 工作区；Credit 已并入 Billing |
| `kokoro-site-kokoro` | 无正式远程仓库 | 删除空/占位目录 |

归档 GitHub 仓库不删除提交历史；归档副本统一放在 Root 之外的 `Kokoro-archive-2026-09-01/`，只供考古和回滚，不加入当前工作区、Compose、CI 或 contract consumer。

## 仓库自洽门禁

每个正式仓库必须在自身目录完成：

1. `README`、API contract、runbook、acceptance/risk 文档；
2. 本仓单元测试、集成测试和 smoke 测试；
3. `CI` 在 push/PR 上只做质量检查；
4. `v*.*.*` tag 才触发 GHCR 生产镜像发布，普通 push 不发布镜像；
5. Docker 使用生产启动入口，开发使用本地 `dev`/测试命令，不用 Docker 代替开发启动；
6. 本仓只读取受信服务上下文，不接受浏览器伪造的域名/tenant header 作为身份依据。

## Root 不允许出现的依赖形态

- `kokoro-*` 子仓库之间的源代码复制、跨目录 import、共享数据库表或共享 ORM schema；
- 新的 `kokoro-chat`、`kokoro-session`、`kokoro-gateway`、`kokoro-platform`、`kokoro-credit` 业务实现；
- MySQL、MongoDB、旧 `site_id` writer 或浏览器直接访问业务服务；
- 将历史文档、旧 Compose、旧 generated consumer 名称误标成当前运行入口。

历史文档可以保留在 Root 的 handbook/reports 中，但必须标注 `历史/迁移材料`，并且不能出现在当前入口、CI、默认 Compose 或 active repository manifest 中。
