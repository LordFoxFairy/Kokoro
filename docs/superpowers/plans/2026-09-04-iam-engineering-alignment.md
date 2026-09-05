# IAM 工程规范对齐：主控任务板

状态：2026-09-05 UTC，**用户明确要求“设置目标，开始动手”，IAM 单仓目标已恢复 active。**
主控采纳[目录方案](../specs/2026-09-05-iam-directory-architecture-design.md)，负责内部技术取舍；先目录落地，
再 SQL、API/运行治理，最后单仓完整验收。当前写入与派工以第 12 节为准，旧暂停记录保留历史含义。

恢复基线：日常主目录 `c5c7a0c`，独立候选 `3f7f0c5`；均干净。旧候选不直接整份合入，
先完成批准分组与 lifecycle 命名，并经过审查及主目录复验。只在主目录真实改变后才报告“已落地”。

本轮重点按 SQL 设计、API 契约、目录架构与职责划分检查，不以目录搬迁或文档完成替代行为验收。

## 1. 目标与职责

用户已确认：规范收敛后，从后端 `kokoro-iam` 开始逐仓重构。Root 发起任务，为每个当前子仓指定负责人 Agent；
先完成技术方案、API 契约和 SQL/数据设计对齐，再按业务切片实现、验证、提交。IAM 验收闭环前不铺开其他子仓。

- 主控：本 Root 会话，负责整体边界、任务拆分、独立审查、主仓复验、提交和放行。
- IAM 负责人：Ohm，原生子 Agent ID `01a06e48-9d74-7531-b697-2946ab0890e3`。
- SQL/事务只读审查：Ramanujan，`01a06e5c-20f4-7652-9b0e-7402959a14fd`。
- API/认证语义只读审查：Franklin，`01a06e5c-2153-7f71-aca8-41673f15dc80`。
- 首次派工基线：Root `1deeb5204a26b0d4dab0413fdc25f369ce62e54a`；IAM `23a0b65e0e361d474d9afed491379df45a36f574`；当前切片以对应任务卡为准。
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
| IAM-03 | 按获准业务切片重构，不一次性搬空仓库                          | IAM-02 通过；逐片补齐任务卡 | IAM 负责人     | 恢复；先执行 IAM-R1        |
| IAM-04 | 真实依赖、契约、架构与运行验证；评审提交和剩余风险            | 对应实现切片完成            | 主控及独立审查 | 待新候选审查与主目录复验   |

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

### S2b 空间故障与恢复

负责人首次运行事务 RED 为 8 失败/6 通过，随后新源码文件及测试临时目录遇到 ENOSPC，按要求停止，未提交。
主控核对保留的 TECHNICAL_DESIGN 与 unit 修改，没有回滚。检查时 APFS 已重新有部分空间；主控只删除本次自己
生成的 52,813,331-byte Node 下载归档和约 61 MiB framework-spike/node_modules，保留已核验 Node 24 runtime、
spike 源码/manifest/lockfile、业务与数据库数据，不清全局缓存、Docker 数据或 Root 的既有 `.tmp/`。

随后本次临时文件的 1 MiB write/flush/fsync 通过，free 为 3,830,960,128 bytes；既有 PG 上独立 session 的临时表
写入/读取/ROLLBACK 通过。Redis RESP PING 与 Docker 只读查询仍超时，未重启。主控已恢复原 S2b 任务，负责人确认
事务 unit 首组 14 项通过，继续真实 PG 故障断言；这不是 S2b 已验收。再次 ENOSPC 时停止并报告，不扩大清理范围。

### S2b 交付、P1 修正与集成（完整环境门禁仍待验）

Ohm 已提交 `55000e6a1292da351b189c991cfa4ccf7a8dfe91`，17 文件；工作树干净，停止写入，无 push。
主控核对改动范围、四命令调用点、事务生命周期、只读 receipt 恢复路径及真实并发故障模型；没有 Schema、Proto、
依赖、CI 或整个目录搬迁。独立质量审查 Anscombe（`01a06f52-3e10-7e30-adf1-85806e5a3a89`）发现下述 P1，
其余本片范围没有新增可行动问题。

主控在该 worktree/commit 执行 lint、typecheck、contract:check、build、隔离空库安装和 `--pg-only`，均退出 0；
24 文件、280 测试通过、0 skip，独立测试库已删除。新事务 integration 21 项包含四命令 COMMIT 后丢确认、
提交前中断、未知提交实际回滚、真实 PG 40001/40P01、结果期限/父失效/绑定或 envelope 损坏；未用伪造 SQLSTATE
冒充并发验证。七份变更文档 Prettier 与 git diff --check 通过。2 项 Redis 仍明确排除；本节尚未宣称独立审查通过、
主工作树集成或完整验收。

**P1：checked-out client 的 error 事件无人接管。** pg-pool 在借出连接时移除 idle error listener；事务 helper
没有添加 client listener。真实 pg 的 `_handleErrorEvent` 除拒绝 query Promise 还 emit error，导致进程直接退出，
现有 pool.on(error) 与 Promise 故障 fixture 都覆盖不到。主控读已安装驱动源码，并用 55000e6 built helper + 真实 pg
的无网络子进程独立复现：无 listener 时 exit 1 / Unhandled error / 未 release；加 listener 的对照 exit 0 / 一次
release(true) / 原错误保留。这是受控驱动事件测试，不是网络断包实验；不访问共享数据。

已交回 Ohm 在原 worktree 聚焦修正 helper、必要 tests/doubles 与事务事实文档；接管借出连接完整 error 生命周期，
保留原因并销毁坏连接，区分 BEGIN/业务/未知 COMMIT，避免 listener 泄漏和释放交接窗口。不能只添加永久吞错
listener。补事件级子进程 RED/GREEN、原 receipt 只读恢复与真实 PG 回归，再由 Anscombe 复审。主工作树仍为
4481d39，S3 未派工；不因现有 280 项通过而越过这条缺陷。

修正提交为 `3579ec7ddfd09a94d126f106daeec759440a2acf`，8 文件，交接时干净；事件级 RED 7 失败/30 通过，
修正后对应单测 37 项通过。Anscombe 复审核实同步 acquire、首因、destroy、release 交接和监听清理，独立执行
8 项事件子进程与 3 项监听保留/清理检查后确认原 P1 关闭，无新增可行动问题，已关闭审查 Agent。
关于 release 失败后 end 同步报错的替身窗口，实际已安装 pg/Node stream 三条窄路径均异步报错、保留原 release
cause，没有生产可达证据，不据同步替身扩大实现；后续驱动升级须保留这些生命周期回归。

主控分别在修正 worktree 与 fast-forward 后的 IAM 主工作树执行 lint/typecheck/contract/build/空库安装/PG-only，
两处均 24 文件、293 项通过、0 skip，测试库各自清理，工作树干净，无 push。新测试区分真实提交后的驱动事件
注入与仅终止自有测试 backend，后者验证真实 PG 断连，未触及他人连接。2 项 Redis 仍排除，built-JS smoke 与最终
完整门禁仍必做。主控据此放行独立 S3a，保留环境欠项，不把上述部分复验当成整仓验收。

本次环境复测：Redis56380 PING、Docker 只读查询继续超时；free 降为 867,233,792 bytes。已询问用户释放空间或
指定可清理缓存，尚无答复；不重复实例、不重启 Docker、不清业务数据。S3a 不下载新依赖或构建镜像，ENOSPC 时
保留工作并报告。S4 的依赖/镜像步骤需要先解决空间与基础设施状态。

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

### S3 投递预审与范围收敛

Avicenna（`01a06ec0-a475-7120-ac0f-d9c1f1b5f4da`）在 4481d39 只读审查后已关闭；没有修改源码或共享数据。
主控核对两处缺陷：已提交 claim 在 Repository 映射中解密，故障发生在 Processor 的次数/expiry 判断之前，导致
poison row 反复 lease 恢复；provider 调用和 markDelivered 共用 catch，SQL 故障会误标 provider_unknown。

主控另在主工作树 4481d39 的 built JS、独立 PG 空库及真实 AES 上复现：过期投递在 maxAttempts=1 时连续三次
claim 仍为 processing、provider 零调用；provider stub 已接受后注入未提交 markDelivered 故障，实际落库 failed /
provider_unknown 并清凭据。只删除本次临时库；这是真实 PG 与受控故障模型，不是实际供应方或网络断包实验。

主控采纳 [ADR-030 §5.1](../../kokoro-handbook/decisions/ADR-030-iam-engineering-boundaries.md#51-magic-link-投递的密钥与终态证据)：
加密 claim 返回业务中性模型、Processor 先检查预算/期限再解密、分离三种错误边界；保留 terminal 清凭据及元数据，
单 key 用停签发排空轮换，不声称支持混合 key 热轮换。淘汰在 Repository 返回解密结果/错误 union 的方案（预算仍晚于
解密且职责混杂），也不把 provider 或解密重试策略放进长数据库事务。先同步本仓三面文档，S2b 验收前不实施 S3。

S3a 的后续最小验证范围已明确：真实 AES key/cipher/tag/AAD 故障且 provider 零调用、有界终止、expiry/cap 先于解密；
多 client claim/fencing/取消/lease；provider 接受后响应丢失的同 delivery ID/payload/reply 去重 fixture；
markDelivered 未提交与已提交但确认丢失分别验证，不伪装 provider 错误或覆盖终态；旧 key 排空与新 key 签发。
本地 provider fixture 只证明 IAM 侧语义，实际供应方 sandbox 仍单独列证据缺口。

主控在主工作树 4481d39 的 built provider client 与两个自建临时 HTTP listener 上另复现默认 fetch 跟随 307：
不同 origin 的目标收到 POST token body，尽管 Authorization 未转发，client 仍接受目标 receipt 并返回成功。
S3a 一并明确关闭所有 3xx 跟随，保留稳定非重试 provider 错误，覆盖 301/302/303/307/308 及目标零请求；不做
“仅去掉 Authorization 就安全”的断言。临时 listener 已关闭。已异步询问实际供应商或测试环境入口，不索取聊天明文
凭据；当前通用 HTTP 协议/占位地址不证明已经接入任何真实邮件服务。

S3 拆为两个提交边界；S3a 已在第 9 节放行，S3b 待其验收：

- **S3a：投递故障闭环。** 继续使用现有路径，唯一 writer 修改 delivery 中性模型、Repository、Processor、
  SecretBox 窄输入输出、装配与相关测试/文档；不混入全仓 rename、Schema、Proto 或依赖替换。先同步技术/API/数据
  的终态与 key 语义，再补 RED；业务+enqueue 同事务、SKIP LOCKED、claim token fencing 和 provider 的原 delivery ID
  保持不变。SQL 状态写入故障原样交给 worker 错误边界；不得尝试把这次故障再次改写成 provider retry/failed。
- **S3b：业务聚合与物理目录收敛。** 在 S3a 验收后，按现有目标树把 auth 放到一个 modules/auth，内分
  principals/magic-links/sessions。Auth Service 按用例及依赖拆分；具体 Repository 按查询/写入事实拆分，
  auth.transaction 在同一个 client 上装配窄能力，禁止保留旧全功能 Repository 作为转发门面。receipt 绑定/加解密、
  session 签发和结果重放的共同规则各自只有一个 owner，不能在两个 Service 中复制。消费方定义最小结构化依赖，
  共享语义类型放中性业务文件，不从具体 Repository/Service 实现反向取类型。

S3b 文件集合由负责人先给出最终 old→new 放置表，主控审查后再写；优先同一切片清除旧业务/传输/启动路径，
使用 server/app/runtime/config 的实际职责而不是保留入口 alias。入口路径影响 package scripts、Docker、CI smoke
时同片更新，依赖版本不混改；Fastify/运行时行为升级仍为 S4。测试按真实类别搬迁并换成 AST 依赖门禁与反例，
README/INDEX/AGENTS 删除已过期的 IAM-01 文档阶段限定。目标树缺少的新共同能力先说明职责与两个可行位置，
不为满足目录模板创建空层，也不把职责拆分降格成批量重命名。

### 目录依赖门禁预验

主控在仓外临时脚本用 TypeScript AST 跑过 17 个正反 fixture，覆盖静态 import、type import、re-export、
dynamic import/require、业务 Service 引入驱动/具体 Repository、route 直连数据库、跨模块内部路径，以及
process.env 的属性/下标/解构读取；注释和普通字符串示例不误报。当前 52 个手写源码文件共 167 条 import 边，
环境变量读取只命中 config/iam-config.ts。此结果不是目标模块架构通过；旧架构测试仍需在目录切片替换。

该探针只处理相对路径模型，正式门禁须使用 tsconfig/module resolution 处理别名并检查循环依赖，保留可执行的
违规 fixture；不拿 import AST 冒充 SQL 参数化、租户隔离或运行时行为证明。没有向 IAM 仓提交临时探针。

主控随后用独立 resolver 探针补齐可行性证据：读取实际 tsconfig，使用 TypeScript module resolver 得到真实文件，
6 项 fixture 覆盖 alias 指向 Repository、公有 index、未解析 import、Node builtin、type-only cycle 和无环图。
主工作树 4481d39 的 52 文件/167 import 均成功解析，无本仓循环；两项探针尚未组合为正式角色门禁，仍不等于目标
目录通过。临时 fixture 文件夹已清理，IAM 源码未改。

### 启动失败清理预验

主控用 4481d39 的实际 built runtime 创建独立子进程，注入 readiness 拒绝和永不完成的 closeRedis（不连接或改动
共享 Redis）。观察到 startup catch 等待无界 Promise.allSettled，forceClose 与上层错误日志均未执行，子进程退出 0。
这独立证明启动失败清理缺少完成期限；不据此宣称已定位真实 Redis 内部故障。S4 须保留原启动错误、对清理设置
有引用的期限、超时执行 force close 并非零退出；测试包含这个无活动 handle 的子进程场景，不能只测单元 Promise。

2026-09-05 主控补充 S4 可行性预验（独立于正在实施的 S3b）：在原仓外 framework-spike 恢复其 frozen lockfile
依赖，沿用上表精确组合、严格 peer 和 1440 分钟 release-age；临时 spike 不执行安装脚本。63 项下载/5 项缓存
复用，出现三次 registry ECONNRESET 后工具成功重试。没有改变 IAM 的 manifest/lockfile、源码或全局工具版本；
该次临时依赖恢复不把 S3b 扩大成依赖升级。

`pnpm exec tsc && node dist/probe.js && node dist/lifecycle-probe.js` 退出 0，原 HTTP/Proto 验证链复跑通过；新增：

1. 用自有占用端口使第二个 Fastify listen 得到 EADDRINUSE，等两次 listen 的结果 settle 后统一清理；两个 adapter
   均停止、worker 未启动、资源 owner 关闭一次。实际生产还须覆盖启动期限和在途 listen 的停止竞争。
2. 两个实际 loopback listener 共用一个资源对象；draining 后 readiness 返回 503，再关闭入口。分别验证在途 unary
   RPC 正常完成且未触发取消、总体取消信号触发后 RPC 中止；两条路径均在 adapter 排空后才关闭资源一次。
   资源计数是测试替身，不是 PG/Redis 验收。
3. 无活动 handle 的 Node 子进程对照：unref 清理期限使程序在记录原错误/force close 前退出 0；有引用期限时实际
   执行 force-close 标记、保留 STARTUP_PRIMARY 并退出 1。这是候选策略验证，不意味着 IAM 已经修复启动路径。

已核对安装包 connect-fastify 2.1.2 源码：设置 shutdownTimeoutMs 会在 preClose 启动独立定时器；原生插件也接受
shutdownSignal。S4 应优先由共享 runtime 拥有一个有引用的总体关闭期限及取消信号，避免每个 adapter 重开完整预算
或遗留插件定时器；该方案已由上述实际 RPC 验证。优雅关闭仍须允许预算内完成，只有到期/强制阶段取消在途请求。

同日 registry 只读复核：pnpm 11.25.0、Fastify 5.12.3、Zod 4.5.4、Connect 2.1.2、Protobuf 2.14.1、
Protovalidate 1.2.0、pg 8.23.0、redis 6.2.1、typescript-eslint 8.69.0；TypeScript latest 为 7.0.2，而
typescript-eslint 的 peer 仍要求 TypeScript <6.1。Node 官方当前 LTS 为 24.20.0，@types/node latest 26.4.1
不等于 Node24 的类型选择，24.13.3 定点元数据可读。Fastify 5.12.3 发布时间为 2026-09-04T08:21:57.526Z，
进入 S4 时重新判定观察窗口；没有因此现在升级。TypeScript 全量/6.0.3 定点 registry 请求曾失败（URLError），实际 frozen
6.0.3 安装与严格编译成功；元数据、实际兼容、供应链审查与正式仓验收分别记账。

参考：[Node release policy](https://nodejs.org/en/about/previous-releases)、
[Connect Fastify plugin](https://connectrpc.com/docs/node/server-plugins/#fastify)、
[TypeScript 当前下载](https://www.typescriptlang.org/download/)。最终切片仍核验具体 release notes、安全与锁文件，
不把本预验当所有依赖已完成升级或质量认证。

## 9. IAM-S3a 投递闭环任务卡（已审查集成）

Owner 为 IAM 的 Magic Link 投递子能力，唯一 writer 仍为 Ohm，原独占 worktree。只修复既有投递行为，
不搬整个目录、不换框架/工具链、不新增邮件产品或管理 API。起始 SHA 为已复审并集成的
`3579ec7ddfd09a94d126f106daeec759440a2acf`，原 worktree 干净，分支 `codex/iam-engineering-alignment`。

### 资源压力、保留与恢复

S3a 曾因 Root 写入失败暂停。负责人保留了 4 份文档/3 份测试（14 RED、18 通过），生产代码尚未修改，
没有遗留测试进程；主控核对 Root 文件与 HEAD 一致、未损坏。随后原 Root 文件补丁及自有 64 KiB write/fsync
复验通过，恢复小型源码工作；低于 1 GiB 时新建 PG 库/批量写入验证仍暂停，不把 unit 当成完整验收。

主控只清理本任务的可重建资源：早期手册临时 fixture 的 node_modules 保留 Prettier 3.9.6 原路径（零依赖），
保留 source/manifest/lockfile；独立 Node 下载目录仅移除闲置 include 构建头文件，bin/lib/许可证等保持。
Prettier 与 Node/crypto 启动验证通过，没有改项目依赖、业务/数据库数据或全局缓存。清理旧依赖时实测可用量由
297,754,624 变为 336,076,800 bytes，未拿 du 的共享块大小冒充实际释放量。

删除头文件前，外部空间已回升至 4,500,647,936 bytes；头文件清理仅额外释放约 64 MB，不将整个回升归因于本任务。
最新复测为 4,656,467,968 bytes；已有 PG session 的自有临时表写入/读取/ROLLBACK 通过，已恢复原 S3a 的 PG-only。
独立验证驱动新增建库前检查：不足 1 GiB 直接失败且不创建数据库；恢复后真实 Schema/PG 检查仍全部必做。
Redis PING 与 Docker 只读查询继续超时；重启/清理确认尚无答复，无新实例。空间继续逐批检查，不开启新依赖或镜像下载。

### 写入集与设计门

- 当前 delivery model/Repository 中性声明；delivery Processor、必要认证错误/窄依赖 shape；具体 delivery
  Repository、provider client、SecretBox/AES 实现、worker 中与本片错误分类有关的部分，以及 container 的依赖装配。
- 认证 Repository 仅在 enqueue 与加密 claim 类型对齐确有需要时修改；不再调整 S2b transaction helper、四命令
  receipt、登录选择或 session 状态。其他生产文件需要先报告原因，不顺带扩大切片。
- 复用已有 delivery Processor/Repository/provider/worker/AES 六个单测文件与 delivery integration；新的真实
  数据库恢复断言可以聚合为一个 `test/integration/magic-link-delivery-recovery.integration.test.ts`，去重 HTTP
  fixture 只放现有 `test/fixtures/`。先比较扩展旧文件和新增聚焦套件，不把所有故障堆进 authentication lifecycle。
- 只同步实际变化的 INDEX、TECHNICAL_DESIGN、API_CONTRACT、DATA_MODEL、CURRENT、ACCEPTANCE、
  RELIABILITY、RUNBOOK；不重复历史长报告。先把三面文档的 key、terminal、provider 接受语义与 ADR-030 §5.1 对齐。
- 排除 Schema、Proto/OpenAPI/generated、依赖/lockfile/CI、Root 和其他子仓。保持现有 outbox 列与 CHECK、
  两个 claim 索引、六 RPC/三个 HTTP 路径、单进程/双端口。若发现必须改变机器源的原因，先交主控裁决。

### 行为与验收

1. claim 原子提交后返回中性加密数据，Processor 在解密前判断取消、到期和次数；不把 pg Row/连接/驱动类型
   透传到用例。解密依赖按最小结构化能力注入，不增 Secret Port 目录、通用 CryptoService 或第二套密钥配置。
2. 错 key/坏 ciphertext/tag/AAD 的稳定类别为 delivery_decryption_failed，provider 零调用；现有预算内有限重试，
   到期/耗尽终止并按原 SQL 清凭据、留元数据；不签发替代 token、不记录秘密、不删除 outbox 行。
3. provider、解密、SQL completion 分开捕获。SQL 写入失败记录受限关联信息并向 worker 边界传播，不能再发出
   provider retry/failed 写入；分别测试写入未提交与已提交后确认丢失，既有 terminal 不被覆盖。
4. 301/302/303/307/308 均不跟随、目标收到零请求，稳定归为非重试 provider 错误；保持原 timeout、取消、
   16 KiB 响应上限、严格 receipt 解析。provider 正确响应只代表 accepted，不承诺邮件送达收件箱。
5. 真实 PG 多 client 证明原子 claim、旧 claim token 的三类状态写入均失效、取消后的 lease 恢复；同一 delivery ID
   与 payload 重试不变。自有本地 HTTP fixture 持久于测试服务生命周期的 dedupe ledger 模拟“接受后响应丢失”，
   返回同逻辑 receipt；与真实供应方 sandbox 证据明确分开，不把 fixture 称实际邮件集成。
6. 单 key 维护流程验证旧 key 排空/过期终止/新 key 新投递，保留 terminal 的业务证据与 SQL 密文空值约束。
   维护窗口阻断签发入口，旧 worker 继续排空后停止旧实例；不为这个测试新增热轮换、暂停 endpoint 或另起一套应用。
7. 先 RED 再 GREEN；执行 lint/typecheck/contract/build/空库 PG-only 与聚焦故障测试，记录 exact SHA 和范围。
   Redis 完整门禁仍欠；不重复启动、flush 或清理共享实例。磁盘不足时保留修改并报告，不扩大缓存/数据删除。

完成后小粒度 commit、停止写入，主控规格审查、独立质量审查、主仓复验后才进入 S3b 目录切片。

### S3a 审查、集成与证据边界

交付 commit `c5c7a0c3b4638988b9dc9d7eb55629d913607f1d`，20 文件，653 行新增/115 行删除；没有修改
Schema、机器契约、依赖/CI 或其他仓。主控逐项核对本节规格与写入集，无未解决的规格差异。

独立质量审查 McClintock（`01a0705a-5adf-7781-bb62-a8fc8662b3ea`）以 `3579ec7..c5c7a0c` 精确差异
及调用链完成审查，未发现可复现的新增 P 级缺陷；独立串行五个聚焦套件 40 通过/0 skip，已回收审查 Agent。
主控在原 worktree 及 fast-forward 后 IAM 主工作树分别执行：

```bash
pnpm lint
pnpm typecheck
pnpm contract:check
pnpm build
node /tmp/kokoro-iam-goal/verify-database.mjs --pg-only
```

两次均退出 0；每次 25 文件/326 项通过/0 skip，独立空库安装、catalog 无 FK，随后只删除该次随机数据库。
主控另对两处实际 built JS 启动自有 loopback HTTP 验证 301/302/303/307/308，五次均非重试拒绝，跨 origin
目标收到零请求；这是 provider client 验证，不是整个服务 built-JS 启动 smoke。

SQL UPDATE 后回滚/提交后抛错是受控故障注入，不写成真实网络断连；本地 dedupe ledger 不证明真实供应商、
跨进程持久保留或收件箱送达；单 key fixture 也不是多实例维护演练。两项 Redis、真实 provider、实际启动/镜像、
后续目录/运行/Schema 及完整验收仍欠。IAM 主工作树 HEAD 为 c5c7a0c，干净，未 push。

Ohm 仅获准准备 S3b 的只读完整放置表：纳入 S2a/S2b/S3a 后新增的职责、事务共享、类型和测试/入口路径，
不先搬文件。主控采纳后另以本任务板明确物理 cutover 写入范围。

## 10. IAM-S3b 目录与职责切片（历史放行，现已暂停）

主控采纳 Ohm 在 c5c7a0c 的 53 个手写源码/4 个 generated 盘点与放置方案，以下为正式写入卡。
Owner、唯一 writer、独占 worktree 不变；起点 `c5c7a0c3b4638988b9dc9d7eb55629d913607f1d`，两工作树干净。
本片是 IAM 内部单次自洽 cutover，不是同时改所有子仓。先同步本仓技术/API/数据的职责与路径说明，再改实现；
不扩大业务、Schema、机器契约、进程或版本选型。

### 采用的目录与职责

| 现有职责组                | 采纳的目标位置与动作                                                                                                                                                                                                                    |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| main 与 bootstrap 五文件  | `server.ts` 唯一启动入口；`app.ts` 用例/worker/HTTP+RPC 装配且不 listen；`runtime/create-runtime.ts`、`shutdown.ts` 管进程资源。仍是 Node HTTP/Connect-node，Fastify 留 S4                                                              |
| config                    | `config/env.ts` 唯一生产环境读取，保留现有配置名、算法与失败语义；本片不增加 Zod 或改变环境加载                                                                                                                                         |
| HTTP                      | 装配归 app；`health.routes.ts`、`modules/auth/sessions/jwks.routes.ts` 拥有真实处理；`http.protocol.ts` 保存现有响应协议。删除确无消费者的 HttpRequestError                                                                             |
| logging/context/readiness | `runtime/request-logger.ts`、`request-context.ts`、`readiness.ts`；通用 trace 与进程日志不依赖认证 RPC。RPC request ID/拦截器仍在 auth，不能把 Connect 带入纯日志类型                                                                   |
| RPC                       | `modules/auth/authentication.rpc.ts`、`authorization.rpc.ts`、`rpc-error.mapper.ts`、`workload-auth.interceptor.ts`、`request-context.ts`；app 完成 Connect 注册，handler 注入实际用例而非总 Service facade                             |
| 大认证 Service            | `magic-links/magic-link.service.ts` 拥有签发/消费，`principals/principal.service.ts` 拥有登录建档/组织选择，`sessions/session.service.ts` 拥有 refresh/logout/getSession；删除原总 Service                                              |
| 共享会话签发/重放         | `sessions/session-credentials.ts` 拥有 issue/replay，不在 consume/refresh 复制 TTL、凭据签发、结果解析及当前有效性校验；session model/结果放 `auth-session.ts`                                                                          |
| receipt                   | auth 根 `command-receipt.ts`、`.service.ts`、`.protection.ts`、`.repository.ts`；原 parser 按 `command-receipt.parser.ts` 共置。分别拥有中性类型、绑定/窗口/重放规则、现有 keyring/HMAC/AEAD、SQL、快照解析；不建 receipt 业务模块      |
| 认证事务                  | `auth.transaction.ts` 保留单连接生命周期和现有 receipt retry/recovery，并装配同一个受作用域保护的 executor；普通 callback 不重试。共享回调能力确需跨 Service/装配时用中性的 `auth.ts`，不让 Service 导入具体事务/Repository 类型        |
| 具体数据访问              | principal、magic-link、session、delivery 各在对应子能力的 `.repository.ts`；receipt/security-event 在 auth 根。真实 SQL 与私有 Row/map 随 owner 拆分；enqueue 归 delivery，不留旧总 Repository 或全能转发壳                             |
| 中性规则                  | principal 登录候选放 `principals/principal.ts`；link 状态/输入放 `magic-links/magic-link.ts`；nonce/redirect/policy 合置 `magic-link.policy.ts`；audit 放 `security-event.ts`；授权输入/结果放 `authorization.ts`、规则放 `.service.ts` |
| 错误与安全                | 稳定认证/授权错误合置 `auth.error.ts`，保留 code/cause/RPC 映射；JWT 归 `sessions/session-token.ts`；delivery/加密 claim/有限 provider 错误归 `magic-links/delivery.ts`，AES/SecretBox 合入 `delivery.secret.ts`，删转发别名            |
| 投递与无状态依赖          | `magic-links/delivery.processor.ts`、`.client.ts`、`.worker.ts` 保留 S3a 行为；composition root 注入 now/newId/newToken，删除三个单方法 time 类，不增加 Clock/UUID wrapper 层                                                           |
| generated                 | 4 份生成文件原位原字节，Proto/OpenAPI/provenance 不因手写目录调整而变化                                                                                                                                                                 |

选择 auth 内三个子能力而不是拆三套 authentication/authorization/audit 一级模块：当前认证事务共同维护这些事实，
尚无独立管理产品。receipt 前缀共置而不是再建 receipts 子目录，沿用已有技术方案且不放大内部机制的业务地位。
session-credentials 合置而不是拆 issuer/replay，当前两者共享凭据释放的不变量；auth.transaction 而非 runtime
事务框架，是因为其未知提交恢复具有认证 receipt 语义。中性 auth.ts 只描述必要的分组事务能力，不重新汇总所有 DTO、
模型、SQL 或每个方法实现，也不建 Port 目录；除此之外消费方仍就近声明实际使用的窄结构。

### 必须保留的行为与依赖

- 四命令的 receipt/outbox/audit/业务事实在同一连接事务中，Repository 自身不另开 BEGIN/COMMIT；provider 不进事务。
- PrincipalService 仍区分 missing/invalid/existing、候选去重/唯一候选/唯一 personal，不把组织选择移进 SQL LIMIT 1。
- 父状态、同 tenant JOIN、固定父锁、session 锁以及未知提交重放次序按已验证实现保留；共享父锁能力由 principal
  Repository 拥有，session 注入调用，不复制一套查询或改变锁序。跨子能力共享中性数据，避免 principals 回引 session Service。
- receipt UUID 规范化、HMAC/AAD/双期限、原 token 字节、refresh successor 重验、logout 单 session 语义保持；不合并成
  通用 CommandBus，不改变加密格式或稳定错误。新共同 credentials 只有一个签发与认证结果释放实现。
- 保留 S2b 的 pg client 事件所有权、release 恰一次、损坏连接销毁、scope 结束后 executor 失效、普通事务不重试与
  最多三次 receipt 回收；具体 auth.transaction 可以依赖 Repository 来装配，Service 不反向导入它获取实现类型。
- Service/中性模型不依赖 pg/Redis/完整配置/generated；RPC 和 HTTP 不写 SQL。基础设施 Row 不通过工具类型或
  `Parameters<typeof ConcreteRepository>` 泄漏到用例；无消费者的 barrel/层/接口直接删除。
- 当前粒度预算用于判断真实拆分原因，不按行号拆文件；遇到未经表覆盖的新职责先简述 owner/位置/验证，新增一级
  owner、机器契约或不可逆数据决定仍交主控，不自授 S4/S5。

### 写入集与排除

- 允许本仓手写 src 依上述表移动/拆分/删除；test 根平铺套件按 unit/contract/architecture 分类，原五个 integration
  保留分类及所有安全/事务/投递断言；doubles 按共享内存状态的分组事实调整，fixtures 保留测试语义。没有独立 smoke
  内容就不建空目录，模拟 runtime/provider 仍不称真实启动或真实供应方集成。
- 替换旧 `test/architecture.test.ts`：正式门禁用 TypeScript AST 与实际 tsconfig/module resolver，检查静态/类型 import、
  export-from、import-type expression、字面量 dynamic import、require/import-equals；非字面量生产动态依赖明确报错。
  以解析后的文件识别角色和边界，纳入 type-only 循环并输出链路；generated 不豁免手写 importer。
- architecture 虚拟源码 fixture 覆盖 alias、.js→.ts、re-export、type-only cycle、动态入口、未解析依赖、Service driver、
  route SQL、跨模块内部引用及 environment 访问绕过；注释/普通字符串不误报。process.env 属性、下标、解构及简单别名
  纳入验证，但不宣称实现任意 JS 全程序污点分析；SQL 参数化/tenant/故障正确性由行为与真实 PG 另证。
- package.json 仅更新 dev/start 的唯一 server 路径，Dockerfile 仅更新 CMD 与必要的路径接线；沿用现有构建布局，
  目标暂为 `dist/src/server.js`，不借搬迁升级依赖/构建输出。scripts/config/CI 若确有硬编码路径才修改，并验证引用；
  现有生成脚本与 workflow 不要求为形式改动。保留所有验证/安全步骤，不降低门禁以适配重构。
- 同步本仓 AGENTS/README/INDEX/docs/INDEX/CURRENT/TECHNICAL_DESIGN/API_CONTRACT/DATA_MODEL/ACCEPTANCE
  与实际受影响的 RELIABILITY/RUNBOOK/SECURITY/SLO 活跃链接；删除九文档/IAM-01 等失效阶段约束。历史证据只标旧
  commit，不批量改旧行号；机器 contract 与 database/schema.sql 完全不变。
- 禁止改 Root、其他仓、依赖/lockfile、Proto/OpenAPI/generated、DDL、Redis/provider 产品、Fastify/运行时新行为。
  删除 application/domain/infrastructure/interfaces/bootstrap 与旧 main/config 路径，不留 re-export 或兼容总门面。

### 验证与提交门

先观察新目录/依赖负例失败，再实现单次自洽 cutover；保留原测试行为，修改构造/路径而非删掉难测断言。
执行 lint/typecheck/contract/build、单元与新 architecture 正反例、主控隔离库驱动 PG-only；Redis 文件保持原位置，
临时排除仍明确不计通过。新增/合并测试导致计数变化必须说明，0 skip 的 PG-only 不替代 Redis/完整启动门。
contract 与 Schema 的 diff 必须为空；新路径由源码和 built-JS 引用共同核对。真实 built 进程、发布镜像依赖恢复后补验。

复用现有 PostgreSQL/Redis、不重启/新建/flush；主控最新只读探测磁盘约 64 GiB 可用，但 Redis/Docker 仍超时，
不把空间恢复当成共享服务已恢复。验证驱动保留 1 GiB preflight；本片不安装依赖或下载镜像。
小粒度以这次自洽的“职责与物理目录 cutover”为一个可审查提交，不提交中间双轨；交付后停写，主控审查与独立质量
审查、主仓复验后再另行授权 S4/S5。Root 只记录治理证据，不拥有 IAM 业务实现。

## 11. S4 API 与治理预审（尚未放行实现）

Euclid（`01a0707a-0ac8-7f60-a76c-c959f8c3d5fc`）在主 IAM 精确 `c5c7a0c` 做只读 API 审查，
主控随后独立重跑其 loopback 探针：21 个真实 HTTP/RPC 请求、34 个断言通过，退出 0。断言用于确认现有缺陷，
不是修复验收；用例使用 Service/readiness stub，不代表真实身份、PG、Redis 或端到端启动。审查 Agent 已回收。

| 范围       | 已复现事实                                                                                                                                | 后续实施要求                                                                                                  |
| ---------- | ----------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| Proto 校验 | nonce/command UUID/digest 的非法组合进入 Service stub；现有链未执行 Protovalidate                                                         | 按实际 input descriptor 执行单例 validator；业务邮箱规范化、redirect allowlist、tenant/状态校验仍各归原 owner |
| request ID | 成功 RPC 无关联 header；workload 早错生成两个 UUID；空 body、有 header 时 detail 为空；超长/Unicode/空白可导致分叉或无 detail 的 Internal | 一个请求 Context；先建立安全候选，解码后定稿；handler/error/log/成功 metadata 使用同一结果，不反射非法原文    |
| 协议早错   | JSON/timeout 解析错误及截断 binary 发生在 interceptor 之前，无 IAM 关联日志                                                               | 在实际适配边界覆盖结束日志/header；按下述协议决定区分原生错误与业务 detail，不重复解析正文                    |
| deadline   | 客户端声明 5ms，100ms Service stub 仍执行完成并返回 200                                                                                   | 服务端执行预算与下游取消实际接线；仅配置客户端 deadline 或 Promise.race 不证明事务已停止                      |
| 治理       | IAM-only Root preflight 11 项失败                                                                                                         | S3b 收敛两个目录项；另九项工具链/类型/格式门在 S4 处理，不改 Root 检查来迁就旧实现                            |

原始探针及主控复验仅在 `/tmp/iam-s4-review.YO4sOO/`，不作为仓内长期测试依赖。S4 实现必须将成功、
非法输入、早错、大小/压缩、deadline/断开、序列化失败的断言落入本仓真实 socket 测试。

### 实施前必须明确的窄决策

- 保留六方法、字段编号和三 HTTP 的产品范围。request ID 的 ASCII/长度、重复 header、body/header 优先级；
  tenant/permission/opaque token 的新增长度上限，须写进 owner 契约后再实现。tenant 不改为 UUID，不规范化大小写。
- `request_digest` 当前上限是 UTF-16 code units；Protovalidate `max_len` 是 Unicode 码点，二者不等价。
  直接执行邮箱注解也可能改变 trim/lowercase 后的既有接受集合；须明确规则位置，避免框架升级偷偷改变业务行为。
- Connect-Fastify **2.1.2** 的原生解析/编码早错不进入 interceptor，也不抛给 Fastify error handler；该版本没有
  官网新示例中的 `requestGate`。审查现有承诺后决定原生协议错误的 detail 边界，不用 onSend 重写帧或第二次 body parse。
- `Canceled/DeadlineExceeded/ResourceExhausted` 不应被通用 mapper 误写成 Internal 或业务 RATE_LIMITED；
  原生协议码与业务错误枚举分别建模。断开的 socket 与原始 HTTP parser 错误不承诺客户端收到响应 metadata。
- `maxTimeoutMs` 只约束客户端传入上限，不提供无 header 时的默认执行预算；Fastify HTTP handlerTimeout 的 503
  不直接套在 Connect RPC。RPC 的大小/压缩由 Connect raw-stream reader 负责，HTTP Zod 不解析第二遍 RPC。
- 候选预算：RPC read 64KiB/write 1MiB、执行 10s；HTTP health/JWKS 2s、ready 15s；header 16KiB、接收 10s、
  inactivity 20s、keep-alive 5s。这些是待真实负载和取消验证的起始取舍，不是实测 SLO 或已经采用的 API 上限。
- Node、pnpm、TypeScript/ESLint、Fastify/Connect/Zod 的精确版本在 S4 开始时重核稳定兼容与 release-age；
  已有临时框架安装、类型与共享 shutdown 预验见第 8 节，不把 registry latest 或临时 probe 当作本仓升级已通过。

Root preflight 由现有 common/delivery/typescript 检查限定 IAM 运行，失败即退出 1；未扫描或修改其他子仓。
除两个目录项外，剩余为 engines、strictDepBuilds、format:check、三项 TS 检查开关、skipLibCheck、ES2024 target/lib。
未命中 SQL 文本规则不代表 SQL 设计、catalog drift、retention 或真实并发已完成 S5 验收。

## 12. 恢复执行：目录优先的 IAM 单仓目标

用户已将技术方案评估交给主控，并明确授权实施。沿用现有 active goal，不重复创建目标或任务中心。
过去 Ohm 与审查员均已停止；本轮重新指定一名 IAM 写入负责人，主控不抢写其 checkout。

### 顺序与完成条件

| 任务    | 范围与交付                                                                                        | 状态                     |
| ------- | ------------------------------------------------------------------------------------------------- | ------------------------ |
| IAM-R1D | IAM 三面文档与 INDEX 承接采纳树；纠正失效路径、源码职责和状态说明；机器契约/DDL 零变更            | 待派工                   |
| IAM-R1  | 在原候选上完成 auth 内部分组、准确命名、真实职责边界；独立审查后集成日常主目录                    | 等待 R1D 文档门          |
| IAM-R2A | 只读复核 SQL 精简/索引/UTC/无外键方案，提交带源码证据的实施清单                                   | 可与 R1D 并行            |
| IAM-R2  | 先完善 DATA_MODEL，再逐片对齐 canonical SQL、查询映射、UTC、完整性/保留与 catalog；不操作既有数据 | 等待 R1 主目录落地及 R2A |
| IAM-R3  | API/框架/依赖治理：先定契约和预算，再验证输入、请求关联、取消、共享生命周期等既有缺口             | 等待目录与相关 SQL 边界  |
| IAM-R4  | 主目录完整验证、目录/SQL/API 整体审查、文档事实收口、小粒度提交；缺少的外部证据明确记录           | 等待以上切片             |

### IAM-R1D / IAM-R1 写入负责人任务卡

- Owner：IAM/auth；执行 Agent：Boyle（`01a070b9-32ab-79b2-a7f4-22e1b6e4bca3`）。主控为规格审查与 Git 集成负责人，另配独立只读质量审查。
- 工作目录：`/Users/nako/.config/superpowers/worktrees/kokoro-iam/engineering-alignment`。
- 分支：`codex/iam-engineering-alignment`；起始 `3f7f0c59eaf292de5e249313e7180417fc879f37`，干净。
- 日常主目录：`/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-iam`，`codex/production-closure-docs`，`c5c7a0c3b4638988b9dc9d7eb55629d913607f1d`，仅主控集成。
- 第一阶段只写既有 AGENTS/README/INDEX/docs/INDEX/CURRENT/TECHNICAL_DESIGN/API_CONTRACT/DATA_MODEL/ACCEPTANCE，以及确有活跃路径受影响的 SECURITY/RELIABILITY/RUNBOOK/SLO；先返回三面文档 commit，主控审查后续派源码。
- 技术设计采用目录方案第 4–6/8–9 节：一个 auth 模块；principals、magic-links/deliveries、sessions、authorization、audit、idempotency、rpc 分组；`runtime/lifecycle.ts` 同时协调启动与关闭，`trace-context.ts` 专管 trace。
- 文档必须区分当前 worktree、日常主目录与待实施目标；修复旧候选机械替换导致 GetSession 指向 magic-link.service、会话 SQL 指向 principal.repository 等错误，活动链接不沿用失效行号。
- 目录片不改机器 Proto/OpenAPI/generated/DDL/依赖/lockfile/配置策略/运行端口/业务行为；无 Root、其他子仓或基础设施写权限。
- R1D 验证：diff check、Markdown 格式/链接与源码职责核对，机器契约/DDL 零 diff。R1 验证：lint/typecheck/contract/build、架构正反例及原安全/事务/投递回归；PG-only 与 Redis/完整 smoke 证据分开。
- R1 交付保留原 46 手写文件所需真实职责，不造额外层/总 Service/Repository facade；4 generated 原字节；原 53 手写文件逐一有去向，旧四层与兼容入口删除。
- 提交：独占 worktree 的负责人按明确路径提交；源码候选停写后主控先规格审查、再独立质量审查，最后主目录集成复验。

### IAM-R2A SQL 只读任务卡

- Owner：IAM；审查 Agent：Nietzsche（`01a070b9-338f-7ab1-b6e4-528700da017e`）。只读主目录精确 `c5c7a0c3b4638988b9dc9d7eb55629d913607f1d`，不写文件、不提交、不连接/重置 DB、不启动服务。
- 读取 Root SQL/TS 手册、ADR-030、CODEBASE_MAP 及 IAM schema/DATA_MODEL/相关生产查询。
- 输出按表/字段/索引的保留或删除结论、业务不变量、源码证据、SQL 改动后必须联动的查询/API 类型；不重复撰写通用规范。
- 重点防止误删 membership generation、refresh digest/family 唯一性、活跃邮箱唯一性、授权关联与全局 permission catalog；principal/org 的 deleted_at 与停用分离。
- 明确 UTC 连接配置、无外键并发/删除协议、闲置索引与缺少索引的实际访问路径；retention/orphan 检测不补造管理 API、不默认硬删身份/审计。
- Schema 当前与目标区分；R2A 结论由主控评估进入后续任务卡，不自动授权改表。

### 基础设施和交付边界

复用唯一现有 PG/Redis；先只读探测，不重启 Docker、不另起实例、不 flush。随机隔离库仅在验证阶段创建，
并只清理本次资源；共享 Redis 若仍不可用，保留明确缺口，不用 mock 冒充通过。真实邮件 provider sandbox
尚未提供，不把本地 provider ledger 当供应方验收。Root 原有 kokoro-agent 与 .tmp/ 修改保持不动。
