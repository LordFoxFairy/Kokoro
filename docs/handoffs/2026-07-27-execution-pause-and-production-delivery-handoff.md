# Kokoro 实现暂停与生产交付交接

日期：2026-07-27  
状态：用户要求暂停新实现，先完成交接  
性质：短期执行交接，不替代 handbook、已批准 Spec 或 Production Delivery Program

## 1. 首先进入正确工作树

不要在默认项目目录的 `main@31ed730` 继续实现。当前代码与验证证据在：

```text
/Users/nako/.config/superpowers/worktrees/Kokoro/feat/lordfoxfairy/wave-0-foundation
```

Root 分支：`feat/lordfoxfairy/wave-0-foundation`  
Root HEAD：`ca41b103d9661174db07d6e17499279ea6f23859`  
Root remote：`origin/feat/lordfoxfairy/wave-0-foundation` 已指向同一 commit  
暂停时 Root 与四个子仓 tracked worktree 均为 clean。

启动后只读：

1. `docs/CODEBASE_MAP.md`
2. `docs/CURRENT.md`
3. `docs/superpowers/plans/2026-07-25-kokoro-production-delivery-program.md`
4. `docs/superpowers/specs/2026-07-27-contract-transport-and-internal-rpc-design.md`
5. `docs/reports/2026-07-27-contract-foundation-admin-auth-pilot-verification.md`
6. 本交接

`docs/superpowers/plans/2026-07-26-wave-0-repository-contract-foundation-implementation-plan.md`
已标记 superseded，其当前执行入口是
`docs/superpowers/plans/2026-07-27-federated-repository-governance-correction-implementation-plan.md`。

## 2. 用户意图与不可破坏边界

- 目标是可直接上线的多 Site AI SaaS，不是只完成一个 RPC pilot。
- 一个 Site 对应一个独立、用户无感的 Web Project/部署产物；后端与 GA 共用，业务请求默认携带并强制解析后的 `siteId` 隔离。
- 不同 Site 默认不共享账户；未来共享身份时走正式 OAuth/federation，不直接共表。
- Root 永久保留 `.gitmodules` 和四个 mode-`160000` gitlink。子仓独立拥有 source、lock、CI、artifact、deploy、release 和 rollback。
- 跨仓使用版本化 RPC/HTTP/SSE/异步协议；禁止 sibling source import 和跨服务直连私有数据库。
- Platform 是模块化业务 Core。模块可通过内部 port/facade 组装，未来可独立部署；不是每个模块都新建 Git 子仓。
- GA 只专注 agent runtime，只消费 opaque `namespace`；不接收 `siteId/userId/ownerId/workspaceId` 第二身份轴。
- GA graph/checkpoint/control/terminal/handoff 核心改造前必须先与用户对齐。其他通用业务模块可以主动重构或重写。
- 首发使用 `redeem_only`：无真实 Payment secret 也必须能通过卡密原子获得 Subscription/Entitlement/Credit。支付 Provider 后续对接复用同一 Fulfillment，不建第二套发放逻辑。
- 必须多 subagent 按独立模块并行；主控负责契约、冲突、review 和主仓复验。不得再用长时间只写文档代替代码交付。

## 3. 当前精确 pins 和恢复锚点

| Repository | Pin | Branch / state | Recoverable ref |
|---|---|---|---|
| Agent | `c2a92c85dcf68e5fe0da9fd5bba84131c9d9e537` | Root 中 detached pin | 已有 Wave 1/federated CI tag |
| Platform | `0463513cb9dc04a9fe7fea4f06f098fc1f890845` | `codex/admin-auth-rpc`，与 origin 一致 | `kokoro-admin-auth-connect-2026-07-27-platform` |
| Session | `ffc9b39c993d4272f6d115de411a133ea1290a70` | `codex/platform-admission-port`，与 origin 一致 | `kokoro-platform-admission-boundary-2026-07-27-session` |
| Web | `da320354262befea51e9d868def8bcd8532a1762` | `codex/admin-auth-rpc`，与 origin 一致 | `kokoro-admin-auth-connect-2026-07-27-web` |

Root 的 Admin Auth promotion commits：

- `cf6126b feat(contract): promote admin auth Connect pilot`
- `ca41b10 docs(report): verify admin auth Connect pilot`

## 4. 已实现的代码（不要重做）

### Root Contract / ConnectRPC

- Proto/Buf 为 Admin Auth 契约单一事实源。
- Admin Auth effect 使用方法专属 message。
- digest 算法冻结为 `SHA256_PROTOBUF_V1`：`type name + NUL + normalized known-field protobuf bytes`，丢弃 unknown fields，输出小写 64 位 SHA-256。
- Root generator 生成 Platform/Web 共用逻辑，两端已删除手写 `JSON.stringify` digest。
- 字段上限与 MySQL `VARCHAR(191)` 对齐。
- source digest：`49fbec7964214d82ce189e479b014edc846d7cd0d1ef1facd355b0a80fea6293`
- artifact digest：`e4c0f68e5891c9f83a26b8a6c74552931f5d6d6c559c3d35a036aa3e53f90267`

### Platform

- Admin Auth 已通过 generated Connect/Fastify provider 提供 6 个 RPC。
- Platform 拥有 operator、verification-token effect、auth event 与 command receipt。
- 已实现 workload/audience/environment auth、secret rotation、Protovalidate、typed safe errors。
- command 具备 transaction receipt、幂等键/digest 冲突、并发竞争与 timeout-after-commit reconcile。
- digest algorithm 持久化并有 migration。
- 已加低基数 Prometheus RPC metrics 与 fail-open 安全审计，不记录 secret/email/payload/commandId/digest/requestId。
- 本轮约 1,178 行手写运行时代码、1,311 行测试；大量 diff 是生成的 Protovalidate/Protobuf mirror，不是业务代码。

### Web

- Admin Web 已删除 Platform Admin Prisma/schema/DB credential 所有权。
- Auth.js adapter/events 通过 server-only generated Connect client 调用 Platform。
- 已实现 bounded receipt reconcile 和 live provider/consumer compatibility probe。
- runtime env 改为 lazy resolution，production build 不依赖构建期 secret。
- 本轮约 593 行手写运行时代码、744 行测试。

### Session

- 新增窄的 `PlatformAdmissionPort`，公共 port 不再暴露 `WireEvent`。
- 新增 application-level `RunTerminalOutcome`、Prepare/Finalize receipt 分型，Finalize 可表达 `committed`。
- Model/Credit/Hub 旧调用已收敛到 `legacy-admission-adapter.ts`。
- 该 adapter 仍是过渡实现：`prepareRun/finalizeRun` 还会返回 `outcome_unknown`，receipt query 还会返回 `not_found`。不得宣称 Admission RPC 已完成。
- 本轮约 374 行手写生产代码、323 行测试；新用户业务功能为 0。

### Agent

- GA runtime 未修改。
- 只完成独立 CI 依赖补齐与少量测试整理。

## 5. 已获得的验证证据

权威报告：
`docs/reports/2026-07-27-contract-foundation-admin-auth-pilot-verification.md`  
当前文件 SHA-256：`3dc9434180c7286bbcef921a057100274588e068406a8e6cd975f24bfa368da1`

报告记录的主验证：

- Platform：1,082 tests，typecheck/lint，fresh MySQL 6 migrations，Connect + Prisma integration 12/12。
- Web Admin：41 tests，typecheck/lint/build。
- Session：372 passed、27 skipped，typecheck/lint；规格 reviewer APPROVED。
- Root pinned runtime gate：MySQL/Redis/Mongo/MinIO/LiteLLM 健康，5 个跨仓场景全部通过。
- combination digest：`3f53cf566acfdb03eced966de9d386f9a2d6be94d4d86bf40015b992fff7b4f8`
- machine evidence：`tmp/admin-auth-compatibility.json`。

最后的 clean-clone 检查状态要如实处理：

- Root/Contract/Session 的 clean-clone install 和对应静态/测试门已运行。
- Platform 输出显示 tests/typecheck/lint 通过，Web 输出显示 build 完成；原终端 session 未留下新的总结报告，不要把它们另外写成一次完整认证。
- Agent clean clone 的 `uv sync --frozen` 成功，`pyright` 与 `ruff` 通过。在用户要求删除验证容器后误跑全量 pytest，因 Redis/Mongo 不可达而失败/中断（中断时 305 passed、4 skipped、1 failed、16 setup errors）。这是缺少必需 Infra，不是新代码回归；也不是 clean-clone 全量 PASS 证据。
- clean clone 临时目录已用 `trash` 移入废纸篓。
- 暂停时 `docker ps` 为空；不要在没有 root Infra lease 的情况下自行新建临时容器。

已知未处理风险：Session `npm ci` 报告 2 个 high-severity vulnerabilities。必须在生产依赖治理中审计，不得忽略或盲目升级。

## 6. 明确未完成的范围

Admin Auth pilot 通过不等于 Wave 0 退出，更不等于 Production Delivery Program 完成。

Wave 0 仍缺失的明确产物：

- Root `INDEX.md`
- `config/architecture/index-roots.yaml`
- `docs/templates/INDEX.md`
- `scripts/architecture/check-index-coverage.ts`
- `scripts/architecture/check-dependencies.ts`
- `config/repository/bom.json`
- 可核验的 remote required-check 证据
- Root BOM tag
- promotion rollback rehearsal 的最终证据
- 对 `docs/reports/evidence/wave-0/federated-repository-baseline.md` 中旧 baseline reds 的最终收敛证明

产品/业务层未完成：

- Wave 1：Identity/Site/Workspace/Project/Policy/PlatformUnitOfWork。
- Wave 2A：Catalog/Plan/Subscription/Redeem/Fulfillment/Credit/Usage 原子闭环。
- Wave 2B：Payment/Refund/Dispute/Dunning Provider enablement。它不阻塞 redeem-only 首发。
- Wave 3：真实 Platform Admission RPC、Session 去商业逻辑、typed message/branch/projection/reconnect。
- Wave 5A：Model Control/Gateway/LiteLLM/Capability 生产主干。
- Wave 4：Direct/Agent Operation、durable Job、Artifact，以及 Image/Music/Video Studio 闭环。
- Web Chat 的完整交互、独立 Site Web Project/Fleet 发布与 Admin/Support 生产面。
- Wave 5B/6A-6D/7-9 的高级 Agent、治理、运维和生产认证。

## 7. 为什么用户认为 12 小时什么都没做

用户的判断在产品交付层面成立：

1. 实现放在隔离 feature worktree 和子仓分支，默认主目录 `main` 看不到。
2. 主控把 Root contract → Platform → Web → Session → 全栈验证做成了过度串行的单条 pilot。
3. subagent 并行调度不合格：Platform 负责人编码，Session 大量时间用于评审，Web worker 最后停在 `pending_init`。
4. 重复运行了过多全量/真实依赖/clean-clone 验证。它们应在 promotion 时集中运行，不应阻塞所有模块开发。
5. effect digest 契约在 provider/consumer 实现后才最终冻结，造成明显返工。

下一位主控不得用总行数回避这个问题。本轮只交付了高质量基础切片，没有交付用户可见的商业化或 Chat 新功能。

## 8. 恢复实现后的正确调度

用户解除暂停后，先使用 `superpowers:using-superpowers`、
`superpowers:subagent-driven-development`、`superpowers:test-driven-development`。现有全局 worktree 已满足隔离要求，不要再新建平行 Root worktree。

### 先收口 Wave 0，但要并行

- Root owner：唯一写者，补 INDEX/dependency coverage、BOM/promotion/rollback/remote CI evidence。
- Platform owner：只审计并修复 Platform 子仓 Wave 0 剩余 gate；不改 Root 契约。
- Session owner：只审计 dependency security/CI 剩余 gate；不借机改 GA wire。
- Web owner：只审计并修复 Web lock/lint/build/Site artifact authority 剩余 gate。

每个子仓以独立 commit/push 交付，Root 每收到一个经评审 pin 就更新可见状态。全量 Docker/runtime/clean-clone 仅在候选组合 promotion 时运行一次，验证后立即停止并删除测试容器，不删 volumes/images/dev data。

### Wave 0 退出后的业务并行线

依赖规则以 Production Delivery Program 为准，不能直接跳过 Wave 1。

1. 先冻结 Wave 1 的 Identity/Site/Workspace/RequestSecurityContext/PlatformUnitOfWork 最小契约。
2. Platform 执行 Wave 1 业务实现；Web 同时做不依赖未冻结写面的 Site Project/runtime 隔离和已有 Session HTTP/SSE 用户面；Session 做独立 transport/snapshot 基础。
3. Admission/Rating contract 冻结后，Wave 2A Platform 商业化与 Wave 3 Session read/projection 并行。
4. Wave 2A 的第一个可见闭环必须是：卡密兑换 → Subscription/Entitlement → Credit Journal → Admin 查询/补发/撤销。
5. 完成 Wave 3 后再进入 Model Gateway/LiteLLM/Capability 生产主干；任何真实 GA adapter 语义变化先向用户提案。

### 执行节奏约束

- 每个实现任务先看 RED，再写生产代码，最后 GREEN。
- 子代理报告成功后，主控必须检查 diff 并在主工作树重跑相应 gate。
- 同一 migration chain、Root contract source、barrel export、BOM/pin manifest 只能有一个 writer。
- 聚焦测试跟随小 commit；全量矩阵只在阶段 promotion 运行。
- 文档只在契约/INDEX/证据必须同步时修改；不得再单独花长时间打磨过程文档。
- 每个大模块必须有可见 branch/commit/push，不得等到整个 Program 才合并或汇报。

## 9. 暂停点

- 没有正在运行的实现 worker。
- Platform 审计 worker 已完成，结论是本轮约 69% Platform diff 为生成物，真实手写运行时约 1.2k 行。
- Session 审计 worker 已完成，结论是本轮几乎全是边界/安全/验证，新用户业务功能为 0。
- 原 Web worker 一直为 `pending_init`，已在用户要求暂停后 interrupt，不应认为它交付了新工作。
- 当前 plan 的“启动下一批独立模块实现”应视为暂停，用户解除暂停后再继续。

## 10. 第一个恢复命令序列

```bash
cd /Users/nako/.config/superpowers/worktrees/Kokoro/feat/lordfoxfairy/wave-0-foundation
git status --short
git submodule status
git rev-parse HEAD
git rev-parse origin/feat/lordfoxfairy/wave-0-foundation
docker ps --format '{{.ID}}\t{{.Names}}\t{{.Status}}'
```

先核对本交接的 pins 和 clean 状态，然后恢复 Wave 0 多模块并行收口。不要在默认 `main`
上重做已完成的 Admin Auth pilot，不要先重跑全套 Docker 验证，也不要跳过 Wave 0/1 直接声称商业化已完成。
