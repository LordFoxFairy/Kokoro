# 阶段 2 全仓审计

日期：2026-09-01
范围：Root `Kokoro`、10 个 active repository、6 个 archived repository。
状态：本地拓扑、Goal 2 mock closure、Root contract 与 architecture gate 已验证；Root GitHub Contract CI 已通过。

## Active repositories

以下记录来自本地 `HEAD`、`origin` 和 `origin/main`；10 个仓库的 `origin/main` 与本地
`HEAD` 一致，所有工作树 clean。

| 本地路径 | GitHub remote | 当前 HEAD | 本地状态 | GitHub 状态 |
|---|---|---|---|---|
| `kokoro` | `LordFoxFairy/kokoro-app` | `018ad870f5af23e0bdced9c28a1f0c2e9f25e1ae` | clean | active / main |
| `kokoro-bff` | `LordFoxFairy/kokoro-bff` | `876dfba1c012cbfe41efe1b120468d797cf026b9` | clean | active / main |
| `kokoro-agent` | `LordFoxFairy/kokoro-agent` | `4091fb2f41d9076696eddb2dc4623e30ebaab131` | clean | active / main |
| `kokoro-iam` | `LordFoxFairy/kokoro-iam` | `b662fce3b95e5d3d778f7c940ac94466fd44c5e3` | clean | active / main |
| `kokoro-system` | `LordFoxFairy/kokoro-system` | `2c4635f74666a06482973b40bbd534874673308a` | clean | active / main |
| `kokoro-model` | `LordFoxFairy/kokoro-model` | `aa8c395b9537af4138eaa8008e5b95299d6a0384` | dirty: 2 generated files | active / main |
| `kokoro-billing` | `LordFoxFairy/kokoro-billing` | `f2a947a7a7b78af6fea5e4de56ccab24cf0b8875` | clean | active / main |
| `kokoro-capability` | `LordFoxFairy/kokoro-capability` | `dd2d0718911b211812dbcf61f7c838c95f7f1f0d` | clean | active / main |
| `kokoro-storage` | `LordFoxFairy/kokoro-storage` | `cebeb7a9465e9e87d09b2a2956f97d49db1c5e87` | clean | active / main |
| `kokoro-scheduler` | `LordFoxFairy/kokoro-scheduler` | `5bd04209493c0b70134562bedb500a3833a1dd2f` | clean | active / main |

Root 本地 HEAD 为 `7c07268d95291f0ec1dcb7ed0372dffb0db67b59`，remote 为
`https://github.com/LordFoxFairy/Kokoro.git`，当前 `origin/main` 一致，工作区 clean。

## Archived repositories

| 本地/历史名称 | GitHub 状态 |
|---|---|
| `kokoro-session` | `LordFoxFairy/kokoro-session` archived；不在 Root |
| `kokoro-gateway` | `LordFoxFairy/kokoro-gateway` archived；不在 Root |
| `kokoro-platform` | `LordFoxFairy/kokoro-platform` archived；不在 Root |
| `kokoro-web` | `LordFoxFairy/kokoro-web` archived；不在 Root |
| `kokoro-credit` | 无正式 remote；历史副本在 Root 外；Credit 归 Billing |
| `kokoro-site-kokoro` | 无正式 remote；历史/占位目录不在 Root |

## 本轮清理结果

- Root 工作区不再包含 `kokoro-session`、`kokoro-gateway`、`kokoro-platform`、旧 `kokoro-web`、
  `kokoro-credit` 或 `kokoro-site-kokoro`；旧 GitHub 仓库 `kokoro-session`、`kokoro-gateway`、
  `kokoro-platform`、`kokoro-web` 已 archived。
- 旧 Root database、Native Slice A、旧部署/验证入口保留在 Root 外的
  `Kokoro-archive-2026-09-01/`；归档副本已移除 node_modules、dist、`.next` 和测试缓存，只保留考古所需源文件与提交历史。
- 本机 Docker 只保留当前 Model 的 PostgreSQL 16 + Redis 7 容器和对应服务；已移除旧 MySQL/Mongo/PG18/Redis
  容器、卷、网络、旧 Gateway/Chat 镜像及已完成的迁移容器。
- 10 个 active 仓库均为独立 Git root，`origin/main` 与本地 HEAD 一致；Root 只把 `kokoro-agent` 作为
  gitlink，其余子仓库保持同目录独立 checkout，避免跨仓源码和数据库耦合。

## Machine gates and test thresholds

- Root architecture: `python3 scripts/verify-backend-design.py` 必须返回 0。
- Root topology: 本地完整 checkout 使用 `python3 scripts/verify-repository-topology.py`，必须检查当前十个
  direct Git repository paths、origin remote、active boundary、6 个 archived paths、Phase 1 storage
  boundary 和 Goal 2 manifest，并返回 0。Root CI 使用 `--allow-missing-active-checkouts`，因为七个 owner
  仓库当前是私有 GitHub 仓库，各自 CI 负责自身源码门禁。
- Goal 2 closure: 本地完整 checkout 使用 `python3 scripts/goal2/mock_cross_repository_closure.py`，必须检查七个
  owner 的 API/技术/BFF/验收/风险文档、Root wire 文件、request ID、幂等和 cursor 标记；Root CI 使用
  `--manifest-only` 检查七仓注册表与 Root wire 文件，避免通过未授权的私有仓克隆掩盖或阻塞契约门禁。
- Root contract: manifest parity、renderer `--check`、Buf format/lint/breaking、Redocly lint，
  以及 `uv run --frozen pytest contract/tests scripts/contract/tests -q` 必须通过。
- Hygiene: `git diff --check` 必须通过。各 active repository 的实现、测试、构建和 Docker/CI
  仍由各自仓库门禁负责，不由 Root 复制源码代替。

## Known real-closure gaps

1. 当前 Root gate 是 topology、文档/契约和 mock boundary gate；尚未把 Web→BFF→Agent→七个
   owner 的真实网络编排作为一次生产式联调验收。
2. 生产 PostgreSQL、Redis、S3-compatible ObjectStore、JWKS、provider 和 webhook 配置由部署
   环境注入；本地 fixture 不证明生产依赖或生产凭据可用。
3. IAM shutdown contract test 仍需显式 listener lifecycle 环境；Docker/真实基础设施 smoke
   仍是部署前独立证据，不把环境阻塞记为通过。
4. 新增的 owner health smoke 已验证一次性 PostgreSQL + Redis 下 Web、BFF live、Agent、Scheduler、
   IAM、System、Model、Billing、Capability、Storage 的进程/健康链路；它不等同于业务 API 全量 live
   联调。BFF 的 live path adapter 与 Agent HTTP ingress 仍按各自 v1 contract 分批接线。

## Verification record

本报告对应的 Root 变更包含 Contract CI 的私有仓 manifest-only 运行模式、拓扑门禁的未初始化
submodule 识别，以及本报告；另外 `kokoro-scheduler` 补充了 `.env.example`。未记录任何 secret。

本轮验证结果：

- architecture、完整 checkout topology、CI manifest-only topology、完整 checkout mock closure、CI
  manifest-only closure 均返回 0；
- Root contract pytest `83 passed`；稳定契约源提交 `afd367db387e11172150e64b8c5278918c47cd24` 的
  9 个 consumer `--check` 通过；
- Web `pnpm check`：113 个测试文件、1127 个测试、生产构建通过；
- Stage 2 BFF mock E2E：43/43 HTTP 用例通过，证据文件为
  `docs/reports/2026-09-01-stage2-bff-mock-e2e.json`；
- Stage 2 owner health：14/14 health/readiness/root checks 与 9/9 local processes 通过，证据文件为
  `docs/reports/2026-09-01-stage2-owner-health.json`；脚本已在 finally 中删除临时 PostgreSQL/Redis
  容器和本地对象目录。
- Root GitHub Contract run `33571850888`（commit `7c07268d`）通过；Capability、Storage、Scheduler
  最新独立 CI 也在各自 `main` 提交上通过。Redocly 的 4 个既有 warning 不改变退出码，未修改契约文件。
