# 阶段 2：Kokoro 全仓与子仓库收口报告

日期：2026-09-01
范围：Root `Kokoro`、三个阶段 1 运行仓和七个阶段 2 业务仓。
状态：本地拓扑、边界、契约、提交和 GitHub main 已收口；阶段 2 owner 健康链路已验证。真实业务联调仍按 BFF live adapter 与 Agent HTTP ingress 两个缺口继续推进。

## 1. 最终仓库拓扑

Root 只承载跨仓契约、文档、部署入口和验证工具，不承载任一子仓的业务实现或数据库 schema。

```text
kokoro-app (Web)
       |
       v
kokoro-bff (Chat + business BFF)
       |
       +--> kokoro-iam
       +--> kokoro-system
       +--> kokoro-model
       +--> kokoro-billing (Payment + Credit + Ledger)
       +--> kokoro-capability (Skill + MCP)
       +--> kokoro-storage (metadata + S3-compatible ObjectStore)
       +--> kokoro-scheduler (generic Go scheduler)
       |
       v
kokoro-agent (execution worker; PostgreSQL + Redis)
```

正式仓库及 GitHub 映射：

| 本地目录 | GitHub | Owner |
|---|---|---|
| `kokoro` | `LordFoxFairy/kokoro-app` | Web 产品与同源 `/api/*` |
| `kokoro-bff` | `LordFoxFairy/kokoro-bff` | Chat、业务适配、鉴权、幂等、错误和 SSE 投影 |
| `kokoro-agent` | `LordFoxFairy/kokoro-agent` | Agent 执行、HITL、恢复和事件投影 |
| `kokoro-iam` | `LordFoxFairy/kokoro-iam` | 身份、Tenant、认证、授权、审计、ExecutionIdentity |
| `kokoro-system` | `LordFoxFairy/kokoro-system` | Site、Workspace、Runtime Manifest、系统策略 |
| `kokoro-model` | `LordFoxFairy/kokoro-model` | Model Catalog、Provider、Availability、Policy |
| `kokoro-billing` | `LordFoxFairy/kokoro-billing` | Payment、Subscription、Checkout、Refund、Credit、Ledger |
| `kokoro-capability` | `LordFoxFairy/kokoro-capability` | Skill 与 MCP Connector 控制面 |
| `kokoro-storage` | `LordFoxFairy/kokoro-storage` | Upload、Asset、Artifact 元数据与对象引用 |
| `kokoro-scheduler` | `LordFoxFairy/kokoro-scheduler` | Go 调度、lease、retry、misfire、pause/resume |

本轮 main 提交（均已 push）：

| 仓库 | main SHA |
|---|---|
| `kokoro` | `018ad87` |
| `kokoro-bff` | `876dfba` |
| `kokoro-agent` | `4091fb2` |
| `kokoro-iam` | `b662fce` |
| `kokoro-system` | `2c4635f` |
| `kokoro-model` | `aa8c395` |
| `kokoro-billing` | `f2a947a` |
| `kokoro-capability` | `dd2d071` |
| `kokoro-storage` | `cebeb7a` |
| `kokoro-scheduler` | `5bd0420` |

## 2. 归属裁决

- Chat 是 `kokoro-bff 的 Chat 内部业务边界` 内部业务模块，不存在独立 Chat 仓库。
- Session 是 Chat/BFF 的 API 概念，不创建独立 `kokoro-session` 服务。
- Credit 是 Billing 的 bounded context，与 Payment、Subscription、Checkout、Refund、Ledger 同仓但分模块、分表 owner 和事务边界。
- Scheduler 保持独立 Go 仓库，只调用目标业务的内部 command，使用 Redis 做 occurrence lease，不读取 Billing 或其他业务数据库。
- Model 是独立业务 owner，不归并到 System；System 只维护产品/站点/Workspace/Runtime Manifest 和系统策略。
- IAM 是独立身份 owner，不归并到 System；BFF 只消费 IAM 派生的受信服务上下文。
- 所有正式业务仓采用 PostgreSQL + Redis。Redis 仅用于 cache、queue、stream、lease、限流和协调；对象字节走 Storage 的 S3-compatible ObjectStore。
- Web 不直连 Agent、IAM 或 Goal 2 业务仓，业务请求统一经过 BFF。

当前 live 适配裁决：BFF 先保留 Web-facing v1 的稳定响应模型；各 owner 的内部 HTTP/Connect/command
协议由 BFF adapter 显式映射，不用通用路径拼接冒充已经完成的业务接线。没有对应 owner ingress 的路由
（例如 Agent session/event、Capability Connect、Scheduler command）继续以 mock/health 证据标记为待接线。

## 3. 已废弃处理

Root 工作区已移除旧目录和 gitlink：

- `kokoro-session`
- `kokoro-gateway`
- `kokoro-platform`
- `kokoro-web`（旧 monorepo）
- `kokoro-credit`
- `kokoro-site-kokoro`

GitHub 上的 `LordFoxFairy/kokoro-session`、`kokoro-gateway`、`kokoro-platform`、`kokoro-web`
均保持 archived，不再参与 CI、Compose、contract consumer 或默认启动路径。旧 Root Compose、旧 k8s、旧验证脚本和遗留环境文件也已从当前 Root 与本机归档目录清除；活动 worktree 只保留当前正式仓库，已失效的 worktree 元数据已 prune。

## 4. 契约与边界门禁

Root 机器索引：

- `contract/goal2-repository-contract-manifest.json`
- `contract/slice-a-contract-manifest.yaml`
- `contract/consumers.yaml`
- `docs/CODEBASE_MAP.md`
- `docs/REPOSITORY_STATUS.md`

每个正式仓库自持：`API contract`、技术设计、BFF 集成说明、验收、风险、单元/集成测试、Dockerfile 和 CI。
跨仓只通过 HTTP/OpenAPI/Protobuf；不复制源码、不共享数据库表、不共享 ORM schema。

镜像发布规则：每个正式仓的 release workflow 只由 `v*.*.*` tag 触发；普通 push/PR 只运行质量检查。Dockerfile 使用生产启动入口，本地开发使用本仓 `dev` 命令。

## 5. 本轮本地验证记录

已通过或已验证：

- `python3 scripts/verify-repository-topology.py`：10 个 active repo、6 个 archived repo 均符合本地拓扑；边界扫描通过。
- `python3 scripts/goal2/mock_cross_repository_closure.py`：BFF→七个 owner、Billing→Scheduler、Capability→Storage 闭环通过。
- `uv run --frozen python scripts/e2e/run_stage2_bff_mock.py --evidence /tmp/kokoro-stage2-bff-mock-e2e.json`：通过真实 `kokoro-bff` 生产编译进程运行 43 个 HTTP 用例，覆盖 auth、projects、skills/GitHub import、MCP、scheduler、Agent setup、library、billing、Chat/SSE/share/delete、幂等和错误边界；逐用例证据见 [`2026-09-01-stage2-bff-mock-e2e.json`](2026-09-01-stage2-bff-mock-e2e.json)。
- `python3 contract/validate_slice_a_manifest.py contract/slice-a-contract-manifest.yaml`：通过。
- `uv run python scripts/contract/render_slice_a.py --manifest contract/slice-a-contract-manifest.yaml --check`：通过。
- Web `pnpm check`：通过（113 files、1127 tests、production build）；补充 jsdom/Radix Event 构造器对齐，消除跨文件 FocusScope 延迟错误。
- BFF `pnpm check`：通过。
- IAM `pnpm verify`：通过；当前为 contract-first baseline，未实现端点按 API contract 分批推进。
- System：lint、typecheck、test、build 通过。
- Model：`pnpm verify:release` 通过（architecture 1、unit 125）；verify release 已包含 `prisma generate`，standalone checkout 不依赖本地残留生成目录。
- Billing：`pnpm verify` 通过；真实数据库集成测试按环境条件执行/跳过并单独记录。
- Capability：`npm run verify` 通过。
- Storage：`npm run verify` 通过。
- Scheduler：gofmt、`go test ./...`、`go test -race ./...`、`go vet ./...`、生产 build、`go mod verify` 通过。
- Root contract consumers：9 个消费者生成与 `--check` 均通过，生成物 provenance 指向 Root `afd367d`。
- Stage 2 owner health：14/14 health/readiness/root checks、9/9 local processes 通过，证据为
  `docs/reports/2026-09-01-stage2-owner-health.json`。
- GitHub main CI：10 个正式仓库最新 main 提交均为 success；Web、System、Billing 以及各业务仓的生产构建步骤均已在 GitHub runner 通过。

## 6. 证据备注与下一阶段

1. 已完成：10 个独立仓分别 commit，并验证 `git ls-remote origin refs/heads/main` 与本地提交一致；最新 CI 修复包含 Web 错误面板断言作用域、IAM/System pnpm build allowlist、Billing PostgreSQL migration 安装流程，以及 Model consumer 对齐 Root v1 Proto 生成物。
2. 已完成：Root 提交拓扑、contract、文档、Agent gitlink、9 个生成消费者和本报告；当前 Root 为
   `7c07268d`，Root generator baseline 仍为 `afd367d`，避免非契约文档提交造成生成物漂移。
3. 旧 Native Slice A runner 及 Root 的集成 SQL/PG18 fixture 已从活动 Root 和本机归档目录清除：它们绑定已废弃的 Session/旧 Site 表/IAM gRPC/独立 Chat 进程模型，不能作为当前阶段 2 证据；需要考古时从 GitHub archived 历史提交读取。
4. 当前 E2E 证据改由 Root 的 Stage 2 BFF mock runner 产生；它只启动子仓生产编译产物并通过 HTTP 验证，不共享业务数据库或复制源码。
5. Dockerfile 本地 build 已启动；Docker Hub metadata 请求在当前本机网络挂起，已停止残留 build 进程，本次仅记录为环境阻塞，不记为镜像构建通过。生产镜像仍只从 v*.*.* tag workflow 发布。
6. GHCR package visibility 未修改；GitHub CLI 当前没有 `read:packages`，因此只记录 workflow `packages: write`，不把它等同于 package public。
7. 已完成本轮收口：Root 生成 consumer/report 已提交、构建产物已清理、Root gate 已复跑，所有正式子仓工作树 clean；当前 GitHub 上 10 个正式仓均保留 `main`，4 个历史远程仓保持 archived。
8. 阶段 2 收口后重新冻结了 Root 的当前 v1 breaking image：旧 baseline（commit `1a993fac`，对应已废弃的旧拓扑）已从活动 Root 移除并仅保留在 Git 历史；活动 Root 的同名 baseline 现在与最终 Stage 2 v1 descriptor 一致，后续普通演进继续由 Buf breaking 门禁约束。修复后的 Root `Contract` workflow 已在提交 `ade5f0bc` 的 GitHub run `33567800858` 通过。

## 7. 尚未宣称完成的真实闭环

1. BFF 的 live adapter 需要把 Web-facing `/v1` 资源显式映射到 System、Model、Billing、Capability、Storage
   的 owner ingress，并统一 envelope、错误、request ID、幂等回执和超时策略；当前 generic proxy 只验证了
   上游转发和失败归一，不作为业务联调完成证据。
2. Agent 当前以 PostgreSQL + Redis worker 运行，尚未提供供 BFF 使用的 HTTP session/run/events ingress；需要
   先在 `kokoro-agent` 内完成自己的 v1 ingress 与测试，再由 BFF 接入，保持仓库边界不跨越。
3. Scheduler 的 v1 是内部 command/配置协议，不是公开资源 CRUD；BFF 对 scheduled-tasks 的 live 接入需通过
   目标业务 command，不直接读取 Scheduler 或 Billing 数据库。
4. 下一次闭环必须启动独立 checkout 的生产构建进程和 disposable PostgreSQL/Redis/ObjectStore，逐条执行
   Web → BFF → owner → Agent/Scheduler 的真实网络用例，并同时保存请求、响应、状态转换、幂等重放、故障恢复
   和测试报告。完成这些证据后再更新本报告状态。
