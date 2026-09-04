# IAM 工程规范对齐：主控任务板

状态：2026-09-04，S1 已验收；S2a 已修正复审并集成，233 项主仓复验通过、Redis/启动门禁待环境恢复；S2b 放行。完整 goal 仍在进行。

本轮重点按 SQL 设计、API 契约、目录架构与职责划分检查，不以目录搬迁或文档完成替代行为验收。

## 1. 目标与职责

用户已确认：规范收敛后，从后端 `kokoro-iam` 开始逐仓重构。Root 发起任务，为每个当前子仓指定负责人 Agent；
先完成技术方案、API 契约和 SQL/数据设计对齐，再按业务切片实现、验证、提交。IAM 验收闭环前不铺开其他子仓。

- 主控：本 Root 会话，负责整体边界、任务拆分、独立审查、主仓复验、提交和放行。
- IAM 负责人：Ohm，原生子 Agent ID `01a06e48-9d74-7531-b697-2946ab0890e3`。
- SQL/事务只读审查：Ramanujan，`01a06e5c-20f4-7652-9b0e-7402959a14fd`。
- API/认证语义只读审查：Franklin，`01a06e5c-2153-7f71-aca8-41673f15dc80`。
- 当前派工基线：Root `1deeb5204a26b0d4dab0413fdc25f369ce62e54a`；IAM `23a0b65e0e361d474d9afed491379df45a36f574`。
- IAM 工作目录：`/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-iam`；分支 `codex/production-closure-docs`。
- 派工时 IAM 工作树干净。Root 已有 `kokoro-agent` 与 `.tmp/` 的任务外变更，不覆盖、不暂存。

规则依次引用 [AGENTS](../../../AGENTS.md)、[TypeScript 手册](../../kokoro-handbook/standards/08-typescript-backend-engineering.md)、
[SQL 手册](../../kokoro-handbook/standards/03-sql-and-postgresql.md) 和 [仓库地图](../../CODEBASE_MAP.md)。
本文件是本轮唯一任务板；历史任务清单和旧四层示例不作为本轮实施依据。主控维护，负责人只读。

## 2. 任务顺序

| 任务   | 目标                                                          | 前置条件                    | 负责人         | 当前状态                   |
| ------ | ------------------------------------------------------------- | --------------------------- | -------------- | -------------------------- |
| IAM-01 | 审计，修正规范入口，形成相互一致的技术/API/数据候选方案       | 读取当前代码与手册          | Ohm            | 文档提交 `2401523`，已验收 |
| IAM-02 | 独立审查候选方案，主控确认目录、边界、数据/API 影响与验收矩阵 | IAM-01 交接                 | 主控组织审查   | ADR/S1 设计已通过          |
| IAM-03 | 按获准业务切片重构，不一次性搬空仓库                          | IAM-02 通过；逐片补齐任务卡 | IAM 负责人     | S2a 已集成；S2b 放行       |
| IAM-04 | 真实依赖、契约、架构与运行验证；评审提交和剩余风险            | 对应实现切片完成            | 主控及独立审查 | S2a 部分复验，最终未完成   |

后两项是阶段占位，不构成预先写入授权。具体任务、文件集、行为断言和提交粒度由 IAM-01 的实际证据确定。

## 3. IAM-01 任务卡

### 允许写入

以下路径均相对 IAM 工作目录：

```text
AGENTS.md
README.md
INDEX.md
docs/INDEX.md
docs/CURRENT.md
docs/TECHNICAL_DESIGN.md
docs/API_CONTRACT.md
docs/DATA_MODEL.md
docs/ACCEPTANCE.md
```

位置选择：复用子仓已有权威文档，不新建与其重复的审计手册；本 Root 计划只保存任务分工与状态，不拥有 IAM
业务契约或 Schema。Root 的历史大任务表混有旧拓扑，因此使用既有 plans 目录中的本轮聚焦计划。

### 排除范围

- 不修改业务源码、测试、脚本、机器 contract、SQL Schema、依赖、lockfile、CI 或其他子仓。
- 不搬目录、不新增业务功能、不启动服务、不重置数据，不读取或打印真实环境凭据。
- 不执行 Git 暂存、提交、切换或重置；本阶段交接后由主控审查并独立提交。

### 完成条件

1. 审计以当前文件、行号和行为为依据，区分已实现、缺失和设计问题。
2. 技术方案提供最小目标目录、当前到目标放置表、组织方案取舍、依赖/事务/失败恢复与实施切片。
3. API 文档准确引用本仓机器契约，数据文档逐类解释实际表、查询、索引、不变量和删除/保留规则。
4. 当前态与目标态分开；未修改的 contract/Schema、未执行的测试不得描述为已经通过对齐。
5. 子仓 AGENTS 只引用公共手册并补充 owner、入口和验证，不保留与现行手册冲突的旧强制四层规则。
6. 同步 INDEX/CURRENT/README/ACCEPTANCE，检查链接、文件引用与 diff；运行过的命令附真实结果。

文档门由主控评审放行。存在业务语义、API 或 Schema 未决项时，记录差异和后续切片，不由负责人自行进入重写。

## 4. 验证与交接

- IAM-01 最低检查：`git diff --check`、Markdown 链接、源码/契约/Schema 引用一致性。
- 源码门禁可作为只读基线按实际脚本选择运行，未执行项目明确记录原因；不为文档阶段安装或升级依赖。
- 后续实现使用真实 PostgreSQL/Redis 时，先探测并复用现有实例，隔离本任务数据，不重复启动实例。
- 主控在交接后复核完整 diff、规范符合性和实际设计质量，重跑相关检查，才记录交付 SHA 与验收结论。
- IAM-01 九文档交付 commit：`2401523c854f8c004749d8f6d2ce31758bdbcc69`。
- SQL/API 审查均确认 ADR-030 及 S1 范围无阻断；两位只读审查 Agent 已结束本阶段，不持有写入权。
- 主控复验：九文档 Prettier、266 个本地链接及代码围栏、`git diff --check` 全部通过；IAM 四组静态测试 16 通过，
  Root pytest 28 通过。该证据仅验收文档与基线，不表示 IAM 已完成重构。

## 5. 主控独立基线验证

以下基线的源码为 `23a0b65e0e361d474d9afed491379df45a36f574`；后续九文档提交 `2401523` 未修改源码。
以下为本次主控实际执行，不沿用历史报告：

- Node `22.22.2`、pnpm `11.25.0`、TypeScript `5.9.3`：当前旧实现基线，不是目标工具链已达标。
- `pnpm lint`、`pnpm typecheck`、`pnpm build`、`pnpm contract:check` 均退出 0。
- 未配置数据库 URL 的 `pnpm test`：20 文件、104 测试通过；2 个集成文件、6 测试跳过。跳过不计验收通过。
- 随后在已有本机 PostgreSQL `18.4` 上创建本次专用空数据库，复用已有 Redis 的 `56380` 监听，未启动新实例。
- 在该隔离库实际执行 `pnpm db:apply-schema` 和 `pnpm test:integration`：2 文件、6 测试通过、0 跳过。
- 安装后检查 catalog：16 个主键、22 个 CHECK、无外键；索引用途与字段必要性仍由 SQL 审查逐项判定。
- 正式 app 的 HTTP/RPC 启停及本地 provider 测试已随上述集成执行；不等于已验证真实外部 provider 或 BFF 跨仓链路。
- 完成后删除且只删除该次新建数据库，Redis 未清空，现有实例及用户预览进程保持不动。
- 新审计发现的父状态过滤、receipt 明文、摘要绑定等问题尚未修复；旧测试通过不抵消这些缺口。

## 6. IAM-S1 放行任务卡

设计依据：[ADR-030](../../kokoro-handbook/decisions/ADR-030-iam-engineering-boundaries.md)。两位独立审查已确认
本设计及首片边界无阻断。Ohm 已交付本片，主控完成独立审查、集成及复验，见本节末。

- 目标：修复有效主体查询、登录建档/组织确定性及授权错误分类；不混入目录搬迁、Schema/Proto 改动或依赖升级。
- Writer：仍为 IAM 负责人 Ohm；主控不在该 worktree 修改业务文件。
- 独立 worktree：`/Users/nako/.config/superpowers/worktrees/kokoro-iam/engineering-alignment`。
- 分支：`codex/iam-engineering-alignment`；已同步 IAM-01 已审查文档提交 `2401523`，派工前工作树干净。
- 当前 worktree 基线安装：Node `24.20.0` 官方归档 SHA-256 校验；frozen pnpm 安装并启用严格依赖构建策略，
  仅执行仓内已允许的 Buf/esbuild 安装脚本；lint/typecheck/build 与 104 普通测试通过，6 项 integration 未配置 URL 时跳过。
- 源码写入范围：认证 Service、认证 Repository 与其窄类型、TokenService/JWT、授权 Service、认证错误与 RPC 错误映射。
- 测试写入范围：上述行为的现有 unit/doubles/integration/RPC 测试，新增 `test/integration/authentication-lifecycle.integration.test.ts`。
- 文档写入范围：本片直接影响的 IAM CURRENT/ACCEPTANCE/API/TECHNICAL_DESIGN/DATA_MODEL，更新事实而非继续扩写历史。
- 排除：其他子仓、Root、SQL DDL、Proto/generated、package/lockfile/CI、无关源码、目录移动。
- Git：独占 worktree 中负责人只暂存本片并提交；主控审查后 fast-forward 或 cherry-pick 到 IAM 主工作树，
  记录实际集成 SHA，再做主仓复验。负责人不修改主工作树。

必须新增并观察失败、修正后再通过的断言：

1. tenant disabled/missing、organization suspended/deleted/missing/跨 tenant、principal/membership 无效时拒绝会话与续期；
   失败 refresh 不留下 successor，也不部分旋转原 session。
2. JWT 的 session/sub/tenant/organization 与权威行一致；有效主体的权限撤回和 scope mismatch 仍走明确拒绝语义。
3. 既有失效 contact 不被当新注册；候选按 organization 去重，唯一 team、唯一 personal 优先和多候选歧义均可复现。
4. 组织选择发生在 Service，SQL 不用无排序 LIMIT 1 决定业务；登录建档锁基础父行并在同一连接事务内重验。
5. 身份无效为 Unauthenticated，有效身份但无权限为 allowed=false；依赖故障与未知异常不吞成 PermissionDenied。
6. 保留 Magic Link request/consume、refresh rotation、logout 单 session、既有六 RPC 与三 HTTP 的行为基线。

真实数据库验证复用 `/tmp/kokoro-iam-goal/verify-database.mjs`：该主控临时驱动仅允许两个指定 IAM 工作目录，
每次新建独立数据库、安装 Schema、运行集成后清理自己创建的库。它不属于持久测试资产；本仓持久测试仍须自带
明确的隔离要求，不能依赖主控临时路径才运行。

### S1 验收证据

- 交付/集成 SHA 同为 `b6c6581583e4d712bb106f5939c41da9f0793760`；IAM 主工作树 fast-forward，未改写历史。
- 主控逐项规范审查：20 个变更文件均在授权集合，Schema/Proto/依赖/目录未动；六条断言对应源码与持久测试。
- Beauvoir（`01a06e8f-24b7-7721-af03-6f7765ed0681`）独立质量审查无新增实质性缺陷，0 阻断；
  审查后核心源码/测试 SHA-256 与最终 commit 一致，审查员已关闭。
- 主控先在 worktree、再在集成后的 IAM 主工作树分别执行 lint/typecheck/contract/build、随机空库
  apply-schema 及全量串行测试：两处均 23 文件、162 测试通过、0 skip；各自临时库已删除，未清 Redis。
- 主控独立的原父状态探针也通过：有效 session 返回；disabled tenant、suspended/missing organization 被拒绝。
- 九入口 207 个本地链接/53 个行号范围、五文档格式和 diff 检查通过。S1 的其他验证细目以 IAM ACCEPTANCE 为准。
- S1 完成不表示整体 IAM 已闭环；receipt 安全、全局目录/Schema/框架/运行治理仍为明确后续范围。

## 7. IAM-S2a 安全重放任务卡（已派工）

前置已满足：S1 实现通过规范与质量审查，并在主工作树复验。负责人仍为 Ohm，在同一独立 worktree 从 b6c6581 续作。
本片修复四个认证命令的安全重放，不捎带全部数据主键改名、Fastify 切换或整个目录搬迁。

- 已有证据：主控在源码基线运行服务层 test-double 探针，观察到同 identity/digest 换 email 仍重放、
  换 consume token/nonce 仍释放原凭据、原 access expiry 后仍释放 receipt。该探针不是数据库集成证据。
- 源码范围：四命令及其 receipt 读取/完成/解析、认证配置/密钥装配和必要错误映射；采用 ADR-030 的
  服务端 HMAC 绑定与版本化 AEAD。具体新增文件先按技术方案放置表列明，不引入通用 CommandBus。
- 数据范围：仅 `iam_command_receipt` 的绑定、密文快照与两个期限；移除明文结果和未实现的 failed 分支。
  契约输入/字段号保持，所有 schema/test/docs 与实现同一自洽提交；只支持新空库，不改现存数据库。
- 明确区分结果重放期限与去重保留期限，结果过期不可执行原命令第二次。认证凭据按结果 session/父身份校验；
  refresh 检查 successor，logout 重放允许目标已 revoked。
- 绑定编码覆盖操作、权威 tenant、调用方 digest、有效业务输入，不含 request/trace ID；同身份不同 payload
  在读取敏感结果前冲突。旋转后按 receipt 记录的 key ID 校验旧绑定，而非用当前 key 算出不同摘要后误报冲突。
- 密钥经启动配置读取，明确 active key 与仅解密/校验旧结果的保留 key；用途隔离、长度校验、无日志泄漏，
  AAD 防止跨 tenant/command/operation/版本替换。完整性错误、缺 key、结果过期采用稳定但不同的错误类别。

验收必须持久化到仓内测试：

1. 四命令相同 identity 的并发只产生一份事实；同 identity 换 payload/secret/会话时冲突。
2. replay 返回相同 token 字节和原 expiry，不重新签发；原输入 rotated 的 refresh 可合法重放，已 revoked 的
   logout 可重放；结果 session 撤销、父停用、到期时不释放认证快照。
3. SQL 行、异常与日志没有明文凭据；密文篡改、跨行搬移、未知版本拒绝；新旧 key 轮换与保留窗口可测。
4. 结果到期但 tombstone 未到期时拒绝重执行；过期检查不依赖清理任务先运行。
5. rollback/commit 故障恢复另以 S2b 聚焦提交：保留原 cause、损坏连接销毁、有限整事务重试、未知提交按原
   identity 恢复，不把不可判定结果映射成功；不把临时探针作为最终验收资产。

本片已放行现有认证 service/repository/窄类型/receipt parser/error mapping，以及 receipt 表、配置密钥装配、
`.env.example`、直接受影响的测试与文档。新增窄加密组件复用当前 security 边界，创建前记录职责与放置理由；
密钥环通过必需配置文件提供，旧 key 覆盖重放窗口，绑定和加密用途隔离。
禁止改其他表主键/deleted_at、Proto/generated、依赖/lockfile、整体目录/框架、跨仓功能或管理 API。
发布接线的窄补充授权：仅在既有 release-image workflow 新增临时随机 keyring 生成和路径注入，避免新增必需配置
导致 candidate 启动必然失败；不升级 Action/镜像或重写其他 CI 行为。接线静态断言不冒充实际镜像 smoke。
结果窗口要考虑 JWT 秒级 expiry，不让 Date 毫秒差释放实际已经过期的结果。事务恢复留 S2b 独立提交。
精确文件清单、最终 Schema 和测试证据在交接时复核，不由派工宣称实现已通过。

### S2a 交付审查与集成（环境完整门禁待复验）

- 负责人提交 `8a19608de8e4d58280265730e617cb9f41ec40ba`，34 个文件，交接时工作树干净。
- 主控规格核对通过；主控在该 commit 实际执行 lint、typecheck、contract:check、build、空库安装与全量串行测试：
  24 文件、231 测试通过、0 skip。复用 PG18.4/Redis56380，不清空共享实例，临时数据库已清理。
- 独立质量审查 Boole（`01a06eac-1690-75b0-8f50-d04f2ffd8cd8`）发现 P2：合法大写 command UUID
  首次参与 HMAC/AAD，但 PostgreSQL 读回小写，使原请求重放冲突。已要求 Ohm 统一 UUID identity，补四命令真实
  PG 大写首次/原样重试/大小写等价重试与 changed-payload 断言。
- 修正提交 `4481d391c28874be799052bc52283271aef849b0`；Boole 复审确认 P2 关闭、没有新增可行动问题，随后关闭
  审查 Agent。主控核对 4 文件补丁，并 fast-forward 到 IAM 主工作树，工作树干净，无 push。
- 主控在修正后的 worktree 和集成后的主工作树分别实际执行 lint/typecheck/contract:check/build、空库安装和
  排除单个 Redis 集成文件的测试：23 文件、233 项通过。该文件中的 2 项 Redis 测试明确未计入通过；不是全量绿色。
  负责人已在实际全量中观察这两项各 30 秒超时及 ECONNRESET。四命令 UUID 回归为真实 PG，不只模拟 UUID 字符串。
- 主控额外执行 built-JS 独立进程探针，尚未通过：23:10 UTC 前后既有 Redis56380 出现连接重置/超时，
  独立 node-redis/RESP PING 也失败，Docker 只读查询超时。未重启或新建任何实例。该启动路径在依赖故障时
  退出 0 且没有完成启动日志，需要在运行时切片验证启动失败/资源清理与非零退出；不把这次失败记为 smoke 通过。
- 已异步询问用户是否允许重启现有 Docker；没有答复前不重启、不新建依赖。为避免无关 Redis 环境故障停住 SQL
  修正，主控调整顺序：允许 S2b 在已审查的 4481d39 上继续隔离实现；S2a 的 2 项 Redis 与 built-JS 启动、最终全量
  验收保留为必做项，不删除、不改成永久 skip，也不把部分复验重新命名为完整验收。

### S2b 恢复任务卡

主控在 S1 主工作树基线独立复现两个问题：ROLLBACK 抛错掩盖原业务异常；COMMIT 连接错误后连接仍以普通
release 返回池。先用纯生命周期 test double 证明异常流，再在独立 PG18.4 数据库执行真实 RequestMagicLink，
由测试 wrapper 在实际 COMMIT 成功后抛出 ECONNRESET。调用方收到错误，但 receipt 已提交；使用原命令身份
重试获得原 receipt，link/outbox/audit 各仅一行。未调用外部 provider，完成后只删除自己创建的数据库。
这验证了“提交完成但响应丢失”的应用恢复模型，不冒充真实网络丢包实验。

后续实现需保持该原子性与命令身份：未知提交销毁不确定连接，使用新连接恢复；自动重试只用于明确已受 receipt
保护的命令，不能让任意 transaction callback 自动重做可能已提交的副作用。ROLLBACK 故障保留原 cause，
失败恢复次数有界；结果仍不确定时返回明确错误，不伪装成功。

当前授权：Ohm 在原独占 worktree、4481d39 基线实现，提交后停止；不修改主工作树/Root。

- 源码：认证 Repository 的事务生命周期、四个 Service 调用点、现有窄类型与必要 RPC 错误映射。复杂度需要时，
  在现有认证 Repository 目录提取一个有职责的 transaction 文件；先说明复用原文件与提取的取舍，不新建技术层。
- 测试：现有事务/认证 unit/doubles；新增聚焦 transaction integration 文件与必要 fixtures，避免继续把所有行为塞入
  lifecycle 文件。文档只更新实际受影响的 TECHNICAL_DESIGN/API/RELIABILITY/RUNBOOK/ACCEPTANCE/CURRENT/INDEX。
- 不修改 Schema、Proto/generated、依赖/lockfile/CI、整个目录/框架、provider、其他子仓或新增产品功能。
- 普通事务不自动重跑 callback；只有四个已经 receipt 保护的完整认证命令显式 opt-in。未知提交先销毁不确定连接，
  使用新连接、原 identity/input 确认 receipt；若复用受保护命令入口恢复，必须在任何业务副作用前原子解析 receipt，
  不能当作盲目重跑一般 callback。原 token、去重和双期限语义保持不变。
- 40001/40P01 只在 opt-in 操作中有限次重试整个事务，包含退避/jitter；重试耗尽、缺失/过期结果、仍不确定时返回
  稳定错误，不伪造成功。默认拒绝嵌套事务，不静默复用外层事务；业务代码不让绑定 Repository/client 逃逸 callback。
- 验证 BEGIN/COMMIT/ROLLBACK 故障、release 恰一次、坏连接销毁、原错误保留、普通 callback 不被自动重做。
  COMMIT 返回 ROLLBACK 结果也不是成功；业务/完整性错误不重试。
- 真实 PG 至少覆盖“实际 COMMIT 后丢确认”的新连接 receipt 恢复、提交前中断/回滚后的完整重试、四命令事实唯一与
  原结果重放；40001/40P01 需要真实并发故障依据，不能只有伪造 error.code。所有故障 fixture 只作用于本次隔离库。
- 复用主控独立库驱动。Redis 故障期间 `--pg-only` 明示排除 2 项依赖测试，只证明本片 SQL/非 Redis 行为；依赖恢复后
  必须补全 `--all`。主控继续独立评审与主仓验证，不以负责人 self-review 或命令退出 0 替代。

## 8. 主控并行预验（不修改 IAM 实现）

### SQL 查询计划

在本机已有 PG18.4 的独立临时库，使用 canonical schema，构造 20,000 条 delivered、20 条 pending、
20 条 lease 到期 processing outbox，ANALYZE 后执行当前真实 claimNext CTE + UPDATE 的
`EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)`；`enable_seqscan=on`，没有强制 planner 选索引。
实际走两个部分索引的 BitmapOr，候选 40 行，最终按 PK 更新 1 行。执行后只删除本次临时库。
这支持保留 pending/recovery 索引，不证明任意负载下都最优，也不作为生产吞吐/SLO 结论。

### 框架与 RPC 验证链

在仓外临时 fixture 验证以下**精确组合**，没有改 IAM manifest/lockfile 或正式路由：

- Node 24.20.0、pnpm 11.25.0、TypeScript 6.0.3、Node types 24.13.3。
- Fastify 5.12.1、Zod 4.5.4、fastify-type-provider-zod 7.0.0、@fastify/swagger 9.8.1、openapi-types 12.1.3。
- Connect/connect-node/connect-fastify 2.1.2、Protobuf 2.14.1、Protovalidate 1.2.0。
- 安装启用严格 peer 检查和 24 小时 release-age 门禁，临时 fixture 不执行依赖安装脚本；供应链检查 68 项通过。
- TS strict + exactOptionalPropertyTypes/noUncheckedIndexedAccess、完整依赖类型检查通过。
- 实际启动两个本地临时 Fastify listener，验证 HTTP health、从 Zod 生成 OpenAPI、真实 Connect unary 调用、
  现有 Proto nonce 注解由 Protovalidate 在 handler 前拒绝无效输入、成功/错误 request ID；完成后关闭两个 listener。
- 验证 interceptor 顺序为 context → validation，两次请求只有一次调用业务 stub；这是框架可行性测试，
  不是 IAM 鉴权、数据库或完整 RPC 契约验收，也不是 BFF 接入证据。

核验日期为 2026-09-04；正式升级切片仍须重新检查版本/peer/lockfile 与全部行为。当天新发布的 Fastify 5.12.3
尚不满足 24 小时 release-age，因此本预验选择兼容且已过观察期的 5.12.1，而不关闭供应链门禁追 latest。
[官方 Connect validate](https://github.com/connectrpc/validate-es) 仍标注 unstable，npm 当前 0.2.0；
暂不作为核心稳定依赖候选。该预验直接使用稳定 Protovalidate 1.2.0 和窄 Connect interceptor，
只适配 IAM 现有 unary/错误边界，不自行实现字段验证规则。最终采用在工具链切片登记，不由此预验隐式升级。

### Catalog 校验只读审查

Bohr（`01a06e7c-90de-7d22-8d98-c058f55353a6`）完成只读审查后已关闭，未改代码或数据库。主控采纳方向：
从独立空参考库安装同 commit canonical SQL，生成只读 catalog manifest；目标库只读比较，禁止反向接受目标库
作为预期。CI 重生成并检查 SQL digest/提取格式；安装在提交前比较，运行时不创建参考数据库。
比较必须覆盖双向对象集合、列类型/默认值/空值、约束、索引定义/谓词及有效性；忽略 OID/统计/物理位置，
通过真实变异测试证明能发现 drift，不只用“原样库等于自己”证明正确。

环境差异待数据/工具链切片显式收敛：当前 IAM CI/候选镜像 smoke 使用 PG16，本机实测 PG18.4；
[官方版本表](https://www.postgresql.org/support/versioning/) 在本次核验时列最新稳定系列为 18、补丁为 18.6。
PG18 的 catalog 与 PG16 不同，不能把本机输出无条件固化后宣称跨版本通过。正式支持 major、生成基线与 CI
必须一致或有明确版本适配验证；不为追补丁擅自重启/升级正在被其他任务使用的共享实例。

### 机器契约 owner 闭包审查

Meitner（`01a06e9c-6159-7832-9294-fec62ff67e9e`）只读审查 b6c6581 后已关闭。IAM 六个 RPC 的精确闭包为
12 个请求/响应、common 的 CommandIdentity/PrincipalContext、google Timestamp；RPC typed error 另含
ErrorDetail/ErrorCode。现有方法、可达消息身份、字段类型/presence/编号须保留，不为目录清理改 namespace 或重编编号。

common.proto 中 DecisionKind/ControlStatus/IdentityRef/ExecutionIdentity/ControlDecision，以及
Conversation/Interaction/Agent 错误值 30/31/32/40 不属于 IAM 当前 RPC 用例，进入 API 切片的遗留定义清理候选。
PageRequest/PageResult 也不在 IAM 闭包，但 Capability 的固定 dependency snapshot 和客户端有实际消费；
Storage/Web 也有 common 冻结分发证据。它们不是 IAM 当前六 RPC 的消费者证明，也不等于可顺手删除其他仓快照。
Capability common snapshot 缺 upstream commit，IAM 本地 provenance 也不等于已发布 artifact；发布/消费者范围需
在机器契约切片明确记录，不能凭“当前 src 没引用”宣称全局没人用。

保留可达 ErrorDetail 的现有字段；未输出的 5/8/9/11 错误值与 current_generation 不混入死类型清理。
后续 Buf breaking 必须明确审计基线与发布基线，逐项解释有意 clean-slate 删除，不用改规则集或 namespace 隐藏变化。
本节是审查记录，不向 S2a 授予 Proto/generated 或其他仓写入权。
