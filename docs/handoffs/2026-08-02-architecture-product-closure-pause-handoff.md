# Kokoro 架构与产品闭环暂停交接

日期：2026-08-02  
状态：用户要求停止实现并交接给下一位主控  
性质：现场冻结交接；不替代已批准 spec、implementation plan、handbook 或 Git/CI 证据

## 1. 唯一正确工作树

不要在默认项目目录或 `main` 重做。当前真实代码、未提交切片和验证证据都在：

```text
/Users/nako/.config/superpowers/worktrees/Kokoro/feat/lordfoxfairy/wave-0-foundation
```

Root：

```text
branch  feat/lordfoxfairy/wave-0-foundation
HEAD    62a9c90087c3f373873fe49d7a401dca74a695d3
remote  origin/feat/lordfoxfairy/wave-0-foundation 指向同一 commit
```

接管后先完整阅读：

1. `docs/CODEBASE_MAP.md`
2. `docs/task.md`，但注意其中 candidate 表已落后，不能当实时 commit 事实源
3. `docs/superpowers/specs/2026-08-02-commerce-credit-authority-hard-cut-design.md`
4. `docs/superpowers/plans/2026-08-02-commerce-credit-authority-hard-cut.md`
5. 本交接

## 2. 用户最终目标与不可破坏边界

- 目标是能直接上线的多 Site AI SaaS，而不是只完成 contract、测试或单个 RPC pilot。
- 每个外部 Site 是独立 Web Project、品牌、账户、artifact、部署和回滚单元；Platform、Session、Agent 后端共用，服务端从受信上下文解析隔离维度。
- 不同 Site 默认不共享账户；未来共享身份走 OAuth/OIDC linking。
- 四个 `kokoro-*` 永久保持独立子仓、CI、artifact、deploy、release；Root 只负责 contract、Infra、compatibility、BOM 与 pin promotion。
- 跨仓只走版本化 HTTP/SSE/ConnectRPC/Protobuf 或 durable transport；禁止 sibling source import、共享私库和跨服务直连数据库。
- AG-UI 只统一 Agent → Session → Web 的展示事件语义，不替代内部业务 RPC、checkpoint、HITL durable evidence、billing 或 owner receipt。
- Agent 保留原生 DeepAgents 核心；未经用户再次对齐，不得重构 graph、checkpoint、control、terminal、handoff 核心语义。
- Agent 只消费 opaque `namespace`，不引入第二条 site/user/workspace 身份轴。
- 不创建顶层 Generation、通用 Job 或 `kokoro-generation` 子仓。Image/Music/Video 后端能力归 Platform Media，Artifact 拥有产物；Agent 通过窄工具端口编排。
- 商业首发为 `redeem_only`：卡密必须复用未来支付相同的 Fulfillment → SubscriptionTerm/EntitlementGrant/CreditGrant 链；Payment provider 保持 feature-off。
- 底层 Model Catalog 单一事实源；Chat、Image、Music、Video 通过产品 ModelOption/SiteRelease 自由组合，Session 内置主模型也从同一控制面获取。
- 默认本地 Infra 只保留 PostgreSQL、MongoDB、Redis、MinIO；不要启动额外常驻业务/测试 Pod。
- 用户明确要求多 Subagents 按独立仓库并行，主控负责边界、review、集成和最终复验；不得再长期只写文档。
- 旧实现和旧数据不是兼容目标，可以向前硬切；但实际执行删除/重建 persisted schema 前仍需明确确认具体破坏性范围。

## 3. 暂停时进程与 Infra

所有本轮实现/评审 Subagents 已由主控 interrupt：

- `agent_activity_quality_review`
- `session_activity_authority_migration`
- `commerce_plan_reviewer` 的实现 follow-up

另一个旧任务 `platform_memory_task5_repair` 因额度错误退出，没有可交付代码。

暂停时 `docker ps` 只有四个默认基建：

```text
kokoro-infra-postgres-1  healthy
kokoro-infra-mongo-1     healthy
kokoro-infra-redis-1     healthy
kokoro-infra-minio-1     healthy
```

没有额外容器。由于本机权限限制，主控不能通过 `ps` 再枚举宿主进程；Subagent 均已 interrupt，未启动新的 Docker workload。

## 4. Root 当前状态

已提交并推送：

- `d1416ba feat(contract): hard-cut AG-UI activity authority`
- `62a9c90 fix(contract): close canonical time and memory surface`
- AG-UI 专项 59/59；Root contract Node 测试最后一次为 210/210。

Root remote CI 仍在入口处被用户侧缺少 `KOKORO_SUBMODULE_TOKEN` 阻塞。不得自行签发凭据；Root CI 未绿前不得创建最终 BOM tag。

Root dirty：

```text
M contract/proto/kokoro/platform/credit/v1/credit_catalog.proto
M kokoro-agent
M kokoro-platform
M kokoro-session
M kokoro-web
```

其中 proto 是未归属本切片的格式化/并行改动，未审查，不要顺手提交。四个子仓 dirty 主要表示工作树 HEAD 与 Root index pin 不同，不能直接 `git add .`。

Root index 仍固定旧 pins：

| Child | Root index pin | 当前 child HEAD |
|---|---|---|
| Agent | `1819907` | `cd0c265` |
| Platform | `b32e002` | `cec57d8` + dirty |
| Session | `2096f2f` | `752adb2` + dirty |
| Web | `a141f40` | `43029c9` + 既有制品 dirt |

在子仓完成独立审查、CI、annotated tag 和真实 compatibility evidence 之前，不要提升 Root pins/BOM。

## 5. Agent：已完成，缺最后质量门与 tag

仓库：`kokoro-agent`  
分支：`codex/execution-context-authority`  
HEAD/remote：`cd0c265752270c2fd27969ba1b0e2a0691ede382`，clean 且已推送

提交链：

- `c933024 feat(agent): own AG-UI activity authority`
- `cd0c265 fix(agent): reject ambiguous presentation state`

已实现：

- Agent 只生产 safe-summary、tool-preview、pending HITL、plan、subagent、notice、error 七类 Activity，不伪造 media/artifact/cost。
- 使用官方 `ag_ui` 外层模型；Activity durable owner version/state、semantic duplicate 幂等、changed `+1`、terminal fail closed。
- HITL 私有 domain-separated refs 和 complete decision group。
- 新 validator 在 dict 化前拒绝 duplicate owner/group key，并验证 placement、derived refs、HITL identity membership，关闭 stale duplicate 复活 terminal 的 P1。
- DeepAgents 核心 graph/checkpoint/control/terminal/handoff 文件未改。

验证证据：

- 独立规格复审最终 `PASS`。
- 主控最后全量：ruff green、pyright 0、pytest 849 passed / 6 skipped。
- remote CI `30737429076` success。

暂停点：独立代码质量 reviewer 正在工作时被用户要求停止，尚无最终 PASS/ISSUES 输出。因此下一位只需重新派一个只读质量 reviewer；若 PASS，再创建唯一 annotated tag（建议语义 `agui-activity-authority`），不要重做实现或规格复审。

## 6. Session：已提交主切片，验证修复 dirty 未完成

仓库：`kokoro-session`  
分支：`codex/media-projection-foundation`  
HEAD/remote：`752adb2315e8a70e90b44358f35c274f68cea985`

已提交：

- `752adb2 feat(session): enforce AG-UI activity authority`
- 前序 `eb81bc3 feat(session): own AG-UI presentation identities`

已实现主能力：

- 完整七类 Agent Activity admission；拒绝 year 0000；pending HITL 不带 terminal receipt。
- Activity 不依赖 TEXT binding。
- Session 使用 `randomBytes(32)` 生成公开 opaque presentation refs；私有映射存在 append-only PostgreSQL 表。
- 映射 key 绑定 site/session/epoch/kind/private ref；forced RLS、projector 最小权限、immutable UPDATE/DELETE trigger。
- mapping、candidate、projection 在同一 Serializable Unit of Work。

已提交主切片的最后证据：lint/typecheck green、repository 97/97、Vitest 692/692、remote CI `30737123829` success。

独立规格 reviewer 随后发现两个真实 P1：

1. compatibility setup/真实 verifier 未给 owner binding、owner projection、private reference 完整权限，provider 会 permission denied。
2. 没有真实 PostgreSQL 证明 random mapping rollback、并发重复稳定、跨 epoch/kind、malformed existing mapping 和 browser unreadability。

暂停时 dirty 文件：

```text
M scripts/agui-compatibility-setup-core.ts
M scripts/verify-agui-compatibility-provider-postgres.ts
M scripts/verify-agui-presentation-postgres.ts
M tests/agui-compatibility-setup.test.ts
M tests/agui-presentation-postgres-contract.test.ts
```

当前 dirty 已补：

- owner binding/projection/private-reference 的 SELECT+INSERT；owner projection UPDATE。
- compatibility provider 加入无 TEXT pending HITL Activity，并验证私有 Agent refs 不泄露。
-主 PG verifier 正在补随机映射、重复/并发稳定、跨 kind/epoch、rollback、browser/API 不可读的真实证据。

停止时未运行最新 dirty 的默认 PostgreSQL verifier、全量测试或 CI；不得宣称已修复。恢复后先 review diff，再完成 focused/static 测试和默认 PostgreSQL verifier；通过后提交、推送、remote CI、同一规格 reviewer re-review，再派独立质量 reviewer。

此切片之后仍缺独立功能：Session 必须在同一 human-decision Serializable UoW 原子持久化 terminal HITL Activity → Control v1 → Receipt v1 exact ancestry。现有 `human_decision_owner_projection`、`human_decision_repository`、`owner-activity.ts` 可复用，但不得用 fixture/fake 冒充 runtime。

## 7. Platform：Commerce/Credit hard cut 半成品，不能提交

仓库：`kokoro-platform`  
分支：`codex/media-image-foundation`  
HEAD：`cec57d8a1f91767ad16ca6650d77b0be22c0fac6`  
remote branch：`9905b1b14229723e5496c103301f55a3bc41d26b`；本地已有 20 个既有 commit 未推送，不要在不审计历史时强推。

当前批准设计/计划就是第 1 节两份 2026-08-02 Commerce 文档。核心 owner 划分：

- Commerce：Product/Plan/SubscriptionTerm/Entitlement/Fulfillment/CardCode/Program/Catalog/Revision/Acquisition policy。
- Credit：account/journal/bucket/hold/settle/release/reconcile/expiry；不拥有 Program 定义。
- Card code 与未来 Payment 都进入同一个 Fulfillment，不建立第二套发放链。

dirty 切片正在把 Program/catalog/service/contracts/codec/repository/reader 从 `modules/credit` 移到 `modules/commerce`，并更新 composition、admin、redemption 与 architecture tests。当前统计只计算 tracked diff：30 files，约 +101/-1210；另有 11 个以上 untracked Commerce 新文件/目录，必须一并审查，不能用 tracked stat 误判为纯删除。

主要 untracked 新树：

```text
src/modules/commerce/application/contracts/credit-program-*.ts
src/modules/commerce/application/credit-program-catalog-service.ts
src/modules/commerce/domain/credit-program-catalog.ts
src/modules/commerce/infrastructure/postgres/credit-program-*.ts
src/modules/commerce/infrastructure/protobuf/
```

最后一次 focused 测试（新一轮实现 agent 接管前）为 108 tests、105 pass、3 expected red：

1. architecture test：Commerce 仍访问旧物理 `platform.credit_*` 表。
2. commerce schema test：期待 `platform.commerce_credit_program_window_acquisition`，migration 仍为旧名。
3. catalog test：fake 期待 `commerce_credit_program_catalog_*`，实现仍使用旧 table name。

这三个红是诚实 schema hard-cut 缺口，不能改回旧 owner 或篡改测试期望伪绿。新实现 agent 只完成了加载技能/审计，尚未产生可确认的新完成点即被 interrupt。

恢复顺序：

1. 先完成 TypeScript application/domain/composition owner hard cut，并确认 Credit 不再 import/own Program。
2. 明确批准后，把旧 Credit Program 表、索引、约束、触发器、权限和引用一次性硬切为 Commerce-owned fresh schema；不写 ALTER RENAME 兼容 migration，不支持旧服务混跑。
3. 完成 permanent/period/daily acquisition、frozen SubscriptionTerm identity、expiry bounds、reconcile/replay、Admin reason/audit、card-code → Fulfillment → Grant 全链。
4. Node 24 下跑 lint/typecheck/full tests；默认 PG 只在代码审查完成后进行一次真实验证，不启动额外 Pod。

实际执行 persisted schema 删除/重建前，建议向用户取得直接确认：

> 批准将旧 Credit Program 的表、索引、约束、触发器、权限和引用全部硬切为新的 Commerce-owned fresh schema；旧数据库删除后按新 schema 重建，不保留旧数据、不提供迁移、不支持旧服务混跑。

## 8. Web：稳定基线，产品闭环仍未完成

仓库：`kokoro-web`  
分支：`codex/wave0-round18-admin-openapi`  
HEAD/remote：`43029c9b9ac739167919ded81d526a1fb38fb355`

已完成 owner/terminal projection 与 dormant strict AG-UI consumer 基础，最新 remote CI 为 green。暂停时没有本轮新 Web 实现。

必须保留的既有本地制品：

```text
M packages/session-client/src/generated/control.ts
?? packages/site-app-kit/dist/
?? packages/site-scaffold/dist/
```

不要由无关任务提交或删除。Web 仍缺：真实 Session provider 激活接线、Chat 完整交互、Studio/Artifact/Memory/Admin 产品级 UX、两个独立 Site E2E。AG-UI 必须继续由 Session 投影，Web 不得自行恢复 Agent 私有 ref 或 durable authority。

## 9. 当前真实完成度

以“可直接上线闭环”为分母，不是以文档/测试数量为分母：

| Surface | 估算 | 说明 |
|---|---:|---|
| Agent | 88% | 实现/CI/规格复审完成，缺质量复审和 tag |
| Session | 74% | Activity authority 主切片完成；PG 证据修复和 terminal HITL 原子链未完成 |
| Web | 82% | owner/consumer 基础较强；真实激活和完整产品面未闭环 |
| Platform | 48% | owner 设计正确但商业 schema/三桶/Fulfillment 仍是主风险 |
| Root | 80% | contract 较强；CI token、pins/BOM/rollback 未闭环 |

整体上线成熟度约 62%，架构与核心底座约 75%。不要把这个估算写成 release 证明。

## 10. 下一位主控的并行恢复顺序

先冻结 writer ownership，同一仓同一切片只能一个 writer：

1. Agent reviewer：只读完成质量审查；PASS 后 tag，不改核心。
2. Session owner：完成当前 PG evidence dirty；主控复验/review/提交后，再启动 terminal HITL 原子链。
3. Platform owner：继续 Commerce/Credit hard cut；schema writer 唯一，获得明确 destructive approval 前不执行数据库删除/重建。
4. Web owner：待 Session public provider contract 固定后，完成真实 consumer 激活和 Chat/Studio/Artifact/Memory/Admin vertical，不提前复制 Session authority。
5. Root 主控：只负责 contract drift、review、remote CI、compatibility、pins/BOM/rollback；不要抢写子仓业务代码。

推荐主链：

```text
Agent quality PASS/tag
  + Session PG evidence commit/re-review/tag
  + Platform Commerce/Credit/Fulfillment hard cut
      ↓
Session terminal HITL → Control → Receipt
      ↓
Session → Web 真实 AG-UI compatibility
      ↓
Chat / Studio / Artifact / Memory / Admin 双 Site vertical
      ↓
四仓 CI + runtime compatibility + clean clone + atomic pins/BOM + rollback rehearsal
```

每个独立切片遵循：设计边界先固定 → 生产代码 → focused evidence → 独立规格审查 → 独立质量审查 → 主控复验 → commit/push/CI/tag。全量 Docker/clean-clone 只在候选 promotion 集中运行，不要在代码明显未闭环时反复消耗时间。

## 11. 第一组恢复检查

```bash
cd /Users/nako/.config/superpowers/worktrees/Kokoro/feat/lordfoxfairy/wave-0-foundation
git status --short
git ls-files -s kokoro-agent kokoro-platform kokoro-session kokoro-web
git -C kokoro-agent status -sb
git -C kokoro-platform status -sb
git -C kokoro-session status -sb
git -C kokoro-web status -sb
docker ps --format '{{.Names}}\t{{.Status}}'
```

然后按第 10 节并行恢复。不要先重跑所有测试、不要提升 Root pins、不要把 Platform/Session dirty 当作已完成提交，也不要清理 Web 的既有生成制品。
