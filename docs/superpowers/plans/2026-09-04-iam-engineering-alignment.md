# IAM 工程规范对齐：主控任务板

状态：2026-09-05 UTC，**用户明确要求“设置目标，开始动手”，IAM 单仓目标已恢复 active。**
主控采纳[目录方案](../specs/2026-09-05-iam-directory-architecture-design.md)，负责内部技术取舍；先目录落地，
再 SQL、API/运行治理，最后单仓完整验收。当前写入与派工以第 12 节为准，旧暂停记录保留历史含义。

R1 已落地：日常主目录源码 `e938b91`，当前 HEAD `1d78be6`（文档状态收口）；工作树干净。Boyle 实现与 Locke 两段
独立质量审查完成，主控集成并在主目录复验。下一步为 R2 SQL 细化/实施；当前无写入中的 Agent，历史任务卡不自动变更范围。

本轮重点按 SQL 设计、API 契约、目录架构与职责划分检查，不以目录搬迁或文档完成替代行为验收。

## 1. 目标与职责

用户已确认：规范收敛后，从后端 `kokoro-iam` 开始逐仓重构。Root 发起任务，为每个当前子仓指定负责人 Agent；
先完成技术方案、API 契约和 SQL/数据设计对齐，再按业务切片实现、验证、提交。IAM 验收闭环前不铺开其他子仓。

- 主控：本 Root 会话，负责整体边界、任务拆分、独立审查、主仓复验、提交和放行。
- 首轮 IAM 负责人（历史；当前见第 12–14 节）：Ohm，原生子 Agent ID `01a06e48-9d74-7531-b697-2946ab0890e3`。
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

| 任务    | 范围与交付                                                                                        | 状态                         |
| ------- | ------------------------------------------------------------------------------------------------- | ---------------------------- |
| IAM-R1D | IAM 三面文档与 INDEX 承接采纳树；纠正失效路径、源码职责和状态说明；机器契约/DDL 零变更            | ac04ecf，主控文档门通过      |
| IAM-R1  | 在原候选上完成 auth 内部分组、准确命名、真实职责边界；独立审查后集成日常主目录                    | e938b91 已审查集成复验       |
| IAM-R2A | 只读复核 SQL 精简/索引/UTC/无外键方案，提交带源码证据的实施清单                                   | Nietzsche 只读审查完成       |
| IAM-R2  | 先完善 DATA_MODEL，再逐片对齐 canonical SQL、查询映射、UTC、完整性/保留与 catalog；不操作既有数据 | 下一阶段：细化 SQL 文档/切片 |
| IAM-R3  | API/框架/依赖治理：先定契约和预算，再验证输入、请求关联、取消、共享生命周期等既有缺口             | 等待目录与相关 SQL 边界      |
| IAM-R4  | 主目录完整验证、目录/SQL/API 整体审查、文档事实收口、小粒度提交；缺少的外部证据明确记录           | 等待以上切片                 |

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

## 13. IAM-R2A 审查结果与主控收敛

Nietzsche 在主目录精确 `c5c7a0c3b4638988b9dc9d7eb55629d913607f1d` 完成只读审查，无文件/DB/服务写入，已回收。
以下为后续 SQL 设计输入，不是已实现或验证通过；行号只绑定该旧布局 commit。

| 结论                                   | 精确证据与实施边界                                                                                                                                                                                                                                                                          |
| -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 本表 PK 统一 id，外部身份不变          | 15 张保留表同步 INSERT/SELECT/UPDATE/RETURNING/排序/GROUP BY/Row/fixture；iam_tenant.id 仍 TEXT。Proto 资源字段、JWT session 身份、delivery ID/AAD 的值不变，不用字符串全局替换引用列。                                                                                                     |
| 确定无用项可精简                       | iam_identity 无生产读写；principal/org generation 仅默认值；contact email 与 normalized 同写一个值；security-event payload 唯一构造恒为 {}。membership generation 被 Authorize 消费，family generation 参与 successor/唯一性，均保留。                                                      |
| 删除状态不是仅增加列                   | 认证 Repository 的 lockPrincipal:435–440、登录投影:457–473、session 投影:395–417 均需 principal/org deleted_at IS NULL；保留 disabled/suspended 与同 tenant。refresh digest 定位保留历史 rotated/revoked 行，避免破坏重放/Logout。                                                          |
| 闲置索引与缺失查询索引分开             | ix_iam_magic_link_lookup / ix_iam_auth_session_family / ix_iam_security_event_scope 当前无对应查询；contact:290 历史检索缺非 partial tenant/email 索引；membership:298/450 历史检索及锁缺合适 tenant/principal 路径。新增前用代表性数据和默认 planner 证明收益，不通过关 seqscan 证明性能。 |
| 强制 UTC 与 catalog 尚缺               | Pool 只设 search_path，安装 Client 也未强制 TimeZone；不是 TIMESTAMPTZ 存错了 instant。每连接配置及重建连接验证；canonical schema 衍生 catalog 预期，完整比较表/列/类型/NULL/default/约束/索引，不再维护第二份可编辑 DDL。                                                                  |
| 清密文前先设计 receipt 形态            | 当前 committed CHECK 强制 envelope 非空；直接清 NULL 会违约。结果清除、去重 tombstone、双窗口和过期拒绝需一致，不以 GC 是否跑过决定业务合法性。                                                                                                                                             |
| 清 session 不能只看 refresh expiry+24h | Logout 可在过期 session 上生成新 24h receipt；当前 receipt 无精确 session 关联列。主控不把“粗略跳过有活跃 receipt 的 tenant”直接当最终并发保证，须先确定可检索关联和与新命令一致的锁内重验。                                                                                                |
| 撤销历史不默认 GC                      | 删除最后一个 revoked contact 会让登录分流把邮箱视为新身份；身份/审计不可逆删除不属工程自动默认。outbox/link/receipt 清理必须保护存续引用、终态和 replay 窗口。                                                                                                                              |
| orphan 最小只读边界                    | 现 DATA_MODEL 三条无界 count 只是草案；后续采用受限 tenant/主键分页、固定扫描边界、时间预算和每批快照，区分合法 NULL/全局权限/历史撤销，不自动修复或删除。                                                                                                                                  |

主控已接受以上风险与精简方向。后续按 R2-1 数据字段与查询映射、R2-2 删除状态及父锁、R2-3 UTC/查询计划、
R2-4 有界关系检测与引用安全保留拆片；必要的 Schema/契约设计先写入 IAM 自持文档，再授予具体实现文件集。
当前仍先完成 R1，不让 SQL 审查反过来拖延已经确定的目录落地。

恢复时只读环境探测：空闲磁盘约 61.5 GB；PG5432 TCP 可达（不等于 SQL 验收）；Redis56380 原实例 PING 2s 超时。
未重启 Docker、未创建第二个实例、未修改业务库；完整 Redis/smoke 门保留待验。

### IAM-R1D 主控文档门与 R1 源码放行

Boyle 交付 `ac04ecfe8b0511c1f19860871531cb3043fc2059`，精确 12 份既有 Markdown；主控复核 HEAD/干净状态，
对 `3f7f0c5` 的 src/test/database/contract/generated/scripts/依赖/lockfile/CI/Docker diff 为空。
主控重新运行 12 文档 Prettier check、diff check、去代码块后的 293 本地链接存在性（21 Root 布局映射），均通过；
TECHNICAL_DESIGN 的 46 文件目标树与 Root 采纳树逐字一致。作者另计 294 链接/12 锚点和 12 职责断言，不混为主控结果。
已人工核对 GetSession/会话 SQL/邮箱/TTL/父锁/事务恢复的真实 owner，API/SQL 当前与目标区分正确。三面设计通过本目录片的门，
不宣称 SQL/框架目标已实现；日常主目录仍 c5c7a0c。

现续派 Boyle 执行 IAM-R1，起始 ac04ecf。允许手写 src 按采纳映射移动、必要命名/import 整理；原架构 checker/fixture
加入 receipt/crypto 新角色及业务反向入口、Service→Route/client、Repository→Service 的解析后依赖负例；同步直接受影响测试与
上片既有文档当前链接/状态。删除旧候选路径，不留 alias，保留原四命令事务/凭据/父锁/投递业务行为。
不改机器源、DDL、依赖/lockfile/CI/配置策略/端口，不新造库或通用抽象。无需新的源码目录方案。

实施顺序：新角色/目标分组断言应先对旧候选失败，再落目录与依赖；完成目标结构后验证 lint/typecheck/contract/build 和
架构/业务回归。可用既有主控驱动 `verify-database.mjs --pg-only` 在指定 worktree创建随机隔离库、空库安装并验证后清理；
复用唯一 PG，无 Redis/Docker 起停或全量清理。以当前 commit 报告 Redis 两项显式排除、其他实际计数、AST SQL 保留结果与文档验证。
Boyle 提交后停止写入；主控规格审查、独立质量审查后串行集成日常主目录并重新验证，未通过前不进入 SQL 源码切片。

### R1 独立质量审查卡：分两段绑定不可变提交

主控已对既有 S3b 源码与 R1D 完成规格核对；因旧 S3b 独立质量审查曾被用户中断，本轮补齐这段审查，
不把旧作者自报当作独立通过。只读审查员 Locke（`01a070cb-f51a-73f1-b600-c0852276a1cd`）先绑定 `c5c7a0c..ac04ecf` 的 Git 对象读取源代码/测试/文档，
不读写实施者变化中的文件、不执行写入型命令或 DB 验证；不得编辑、提交或启动服务。
重点审查拆分后的同 client 事务/父锁、错误与重放、唯一 credentials owner、Service窄依赖、原断言保留和实际职责。
已登记的既有 API/runtime/SQL 缺口不作为目录回归重新混片，但新回归/删弱断言必须报告；代码质量判断独立进行。
R1 新提交出来后续派同一审查员核对 ac04ecf..新提交及完整新树/角色门禁，第一段结果不代表最终候选已通过。
报告须绑定精确 SHA、原路径与行号、问题优先级、是否新引入、最小修复和测试要求；无问题也明确审查范围与剩余风险。

## 14. R1 已落地：独立审查、主目录复验与续接

### 实际交付与验收边界

- Boyle：R1D `ac04ecfe8b0511c1f19860871531cb3043fc2059`、R1 `e938b913fb7ef7b7b405446ca47150ade2dc48f2`；已停写并回收。
- Locke：两段只读审查 c5c7a0c..ac04ecf..e938b91，无新增 findings；独立确认 46 文件映射/符号/引用、33 非架构测试除 import 外正文相同及文档链接。已回收，不把其只读审查说成复跑测试。
- 主控规格复核：新树与职责符合已采纳方案；ac04ecf..e938b91 的 46 份源码除 import 外 AST 正文多重集合一致；c5c7a0c..e938b91 的 36 种 SQL 字面量无增删。机器源/DDL/generated/lockfile/CI/scripts 零 diff。
- 旧主目录在 clean 状态下从 c5c7a0c 快进到 e938b91；随后主控在日常主目录完成以下复验。旧四层实际删除，auth 根仅 auth.ts/auth.error.ts/auth.transaction.ts，7 组内部目录含 deliveries，runtime/lifecycle 与 trace-context 已就位。
- 主目录当前 `1d78be6`（`docs(iam): record verified main-directory integration`），仅 9 份 Markdown 的当前状态和证据收口；AGENTS 不再复制阶段进度，统一指向 CURRENT/任务板。源码字节与已验 e938b91 一致。

| 主控实际验证                                                                             | 结果                                                                                                           |
| ---------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| 候选 e938b91 的 lint/typecheck/contract/build、29 architecture、AST 保留、built provider | 全部对应命令 exit 0；candidate 不替代以下主目录复验                                                            |
| 主目录 pnpm lint / pnpm typecheck / pnpm contract:check / pnpm build                     | 各 exit 0，日志独立保存                                                                                        |
| 主目录隔离库驱动 db:apply-schema + PG-only test                                          | 27 文件、351 passed、0 failed、0 skipped；Redis 2 项收集前明确排除；仅清理自身随机库                           |
| 主目录 built provider                                                                    | 301/302/303/307/308 均按非重试错误拒绝，redirect sink 0 请求；本地 HTTP 模拟非供应方集成                       |
| 主目录 Root IAM-only 预检                                                                | exit 1、余 9 项；原两个目录项已消失；未修改检查器放宽门禁                                                      |
| 文档收口 1d78be6                                                                         | 9 Markdown 格式通过，284 本地链接/锚点零错误；依赖/部署 33 个用例通过，生产/测试/DDL/契约等零 diff，工作树干净 |

主控日志在 `/tmp/kokoro-iam-goal/r1-main-review-e938b91/`；作者 RED/GREEN/PG-only 在 `/tmp/kokoro-iam-r1-ac04ecf/`。
作者 RED 为 11 失败/18 通过，GREEN 为 29 通过；351 相对旧 340 增加 11 架构案例，不代表新增 11 个业务用例。
完整证据由 [IAM ACCEPTANCE](../../../kokoro-iam/docs/ACCEPTANCE.md#r1-主目录集成与主控复验) 自持，Root 不复制业务实现。

### 明确未完成项

R1 是目录与职责切片验收，不是整个 IAM 完成。Redis2项、完整进程/镜像启动、真实邮件供应方与 BFF/Web 消费者未验。
Root 预检九项分别为 engines、strictDepBuilds、format:check、三个 TS 严格开关、skipLibCheck、target、lib，留 R3。
SQL id/deleted_at/无用结构、UTC、catalog、关系检测/retention 与 API 输入/关联/取消/生命周期等仍按第 13 节及历史预审待办推进。
未升级依赖、未重复启动共享服务、未重启 Docker、未清理任何已有业务数据库；任务外 kokoro-agent/.tmp 保留。

### 下一步精确续接点

1. 主控保留眼前关键路径：将 R2A 清单收敛为 R2-1 的写入卡和三面文档，先做本表 id 与确定无用表/列/闲置索引，不把删除状态/retention/框架升级混成一次大改。
2. 唯一 IAM owner 继续使用原 worktree；重新续派前确认双方干净，将 worktree 从 e938b91 快进到主目录 1d78be6，逐片明确 writer/审查/SQL 查询与 Row/测试影响。
3. 先同步 IAM DATA_MODEL/TECHNICAL_DESIGN/API_CONTRACT 的具体切片，主控审查机器源影响后实施。tenant TEXT 与其他引用名称/Proto字段不变；保留 membership/family generation 和真实唯一不变量。
4. R2-1 只在新隔离数据库安装目标 SQL，不运行 ALTER/迁移或删除现有业务表。测试 seed/Row 逐处按本表与引用语义改，不以全局替换资源名完成；catalog/UTC/删除过滤未完成项不伪报通过。
5. 继续同一 active goal，无需再问用户是否喜欢内部命名，不新建其他子仓目标，不把已完成 R1 当整个 goal complete。

## 15. IAM-R2-1：主键与确定无用结构清理

上一轮分类：**progress**，目录真实落地、主目录复验并提交，不是等待。当前重新核实主目录 1d78be6 干净，
Root 33a683db 保留任务外 kokoro-agent/.tmp。主控已将原 worktree e938b91 快进到 1d78be6（源码不变），开始 SQL 切片。
本节是当前任务入口；第 13 节 R2A 与 ADR-030 是设计依据，不递归重读全量历史。

### 设计门：本片边界

| 项        | 主控决定                                                                                                                         |
| --------- | -------------------------------------------------------------------------------------------------------------------------------- |
| Owner     | IAM/auth；唯一写入负责人续派 Boyle，原 worktree/codex/iam-engineering-alignment；主控审查与主目录集成                            |
| 基线      | 主/候选均 1d78be6；R1 已验源码 e938b91；已有16表、无FK、唯一schema、六RPC三HTTP                                                  |
| 目标职责  | 数据库本表身份一致、删除确无用结构；不改变公开资源身份、用例行为或目录                                                           |
| 位置比较  | 扩展唯一 database/schema.sql 与各现有业务.repository.ts；不建迁移/兼容视图/数据库品牌目录或第二可编辑DDL                         |
| 粒度      | 按一次自洽schema+查询/Row+fixture切片；不能先只改DDL让全部查询断裂，也不夹带删除状态/GC/框架升级                                 |
| 依赖/事务 | 保留同client装配、父锁及锁序、scope/receipt/未知提交/claim-fencing语义；Service/handler不写SQL                                   |
| API       | 机器Proto/OpenAPI/generated/provenance零变更；对外tenant/资源字段、JWT、deliveryRef及AAD所用ID值不变                             |
| 验证      | 更新静态schema断言、新真实PG catalog/数据断言、现有登录/授权/并发/重放/投递回归、lint/typecheck/contract/build；只使用随机隔离库 |

### 确定改动清单

1. 删除无生产读写的 iam_identity 及其专用唯一索引/CHECK。
2. 其余15表本表PK统一 id：iam_tenant.id 仍 TEXT；其余为UUID。其他表的 tenant_id/principal_id/organization_id 等引用列保持语义原名；不全局字符串替换。
3. 删除 iam_principal.generation、iam_organization.generation、iam_contact.email、iam_security_event.payload；同步唯一写入与局部类型/测试。保留 email_normalized、审计事件其余事实和用户profile。
4. 删除无对应生产访问的 ix_iam_magic_link_lookup、ix_iam_auth_session_family、ix_iam_security_event_scope。保留剩余真实UNIQUE/CHECK、两worker claim索引（将本表PK尾列变为id）、PK自动索引；本片不新增查询索引。
5. 保留 membership.generation 与 family_generation、原status/deleted语义/时间/NULL/默认值；global permission仍无tenant；不引入deleted_at/retention字段，不改nonce/token/receipt加密协议。
6. 查询按表角色逐处改INSERT、SELECT、JOIN、WHERE、锁排序、GROUP BY、RETURNING；Row使用正确本表列/明确语义投影并映射原业务ID。SQL投影的语义AS不是保留旧数据库列的兼容层；禁止造兼容view/列/双读。

### 文件集、阶段门与提交

**R2-1D先文档**：允许既有 docs/DATA_MODEL.md、docs/TECHNICAL_DESIGN.md、docs/API_CONTRACT.md、docs/CURRENT.md；
按已定清单补一个聚焦切片说明与表→查询/Row联动，不把整份文档改成进度报告，不重刷历史段。CURRENT仍残留一句
“主目录仍未集成”，应删去并保留单一真实R1主目录事实；这是主控上一文档收口遗漏，不是目录源码未落地。
先format/link/diff、四文件聚焦commit，主控审查后才续派源码。主控可直接技术裁决，不再询问用户内部SQL命名。

**R2-1源码续派后**：允许 database/schema.sql；src/modules/auth 下六个既有.repository.ts 与 audit/security-event.ts；
以及直接联动的 test/{contract,unit,integration,fixtures,doubles} 和上述四文档/ACCEPTANCE/INDEX 的当前事实。
新建 test/integration/schema.integration.test.ts 用于本片真实catalog/最小业务事实断言（不是生成manifest或完整运行drift），
需要共享fixture时只放test/fixtures；不新建生产源码文件/目录。存量architecture/业务断言不删弱，精确46手写树仍成立。
禁改auth.transaction、service/policy/crypto/client/worker实现、机器契约/generated、package/lockfile/CI/Docker/配置和其他仓。
如测试暴露超出字段映射的已有缺陷，报告主控分片，不借修复之名扩大范围或吞错。

真实PG验收必须覆盖：精确15表与各id的PK/类型；被删表/列/索引反断言；保留引用列、membership/family代际与关键唯一性；
新邮箱建档、授权投影、nonce消费、四命令重放/未知提交、父锁、claim/fencing及审计写入。SQL/Row变化不再要求旧SQL字符串全相同，
须解释语义diff，保留参数绑定/tenant谓词/同连接与顺序。完整catalog manifest、每连接UTC、deleted_at、查询计划、orphan/retention仍待后续。

使用既有主控 verify-database.mjs --pg-only 驱动与同Node/pnpm/已装依赖；驱动只创建/清理随机库并复用PG5432。
Redis原实例不重启/另起/flush，2项显式排除；不删除已有数据，不把空库schema替换包装成生产migration。
交付聚焦commit后停写，主控规格审查、独立质量审查、主目录集成复验；当前三面设计提交不等于自动获准源码。

### R2-1D 文档门通过与源码放行

Boyle 提交 `38c73586036308d79910a8628692fcd142131e84`，精确四份既有设计/当前文档。主控重新核对逐表 PK 与引用、
六 Repository/审计类型联动、API 值与加密身份不变及排除项；四文档格式、145 本地链接/锚点（8 Root 映射）、diff 均通过。
生产源码、测试、DDL、机器契约、依赖与脚本零 diff；未执行 DB。三面设计在本片范围内一致，现放行上述 R2-1 源码文件集。
唯一 writer 仍 Boyle，起始 38c7358；先补失败断言，再自洽实施 Schema/查询/Row/测试并按本节验证，聚焦提交后停写。
主控另外准备基线到候选的真实 catalog 语义比较，以检测指定改名/删除以外的类型、默认值、约束及索引漂移；此为本片审查证据，
不冒充待实现的运行时 drift 命令。双方各自使用随机隔离库，不触碰已有业务数据；最终仍由主目录复验。

### R2-1 候选与主控规格审查

Boyle 交付 `1a081ab88368004b650a6e60d5445206fea5da18`（基线38c7358），25个授权文件、已停写且干净。
主控复核 DDL/六Repository/审计类型、静态与新增真实PG断言：改名按本表与引用区分，scope/锁序/Row/资源ID及加密身份不变；禁改范围零diff。
独立临时catalog驱动在PG18.4安装Git绑定的前后schema，比较表/列/类型/NULL/default/约束/索引：目标15表、125列、145约束（含PG18自动NOT NULL）、31索引，仅指定删除/改名。
驱动先对旧schema RED；候选首次比较发现审查脚本未归一PG18的PK自动NOT NULL名称和已删列约束，补齐精确归一后通过；不是候选缺陷，不放宽业务约束。
随机数据库均已清理；日志 `/tmp/kokoro-iam-goal/r2-review/`，不代替生产drift实现或主目录复验。
现进入独立质量审查：Parfit（01a07105-de9a-7d22-abf9-818e5d3d20b2），使用用户授权的gpt-5.6-sol，只读不可变38c7358..1a081ab，不操作DB、服务或文件；重点复核SQL/Row/业务和测试回归。主控并行准备主目录验证。

## 16. R2-1 已集成复验与下一片入口

本轮分类：**progress**。用户新增选模与旧实现清理偏好已固化到 Root AGENTS（570cacec）；不改变主窗口模型。
Boyle 在途任务未中断，交付1a081ab后已回收；独立审查使用Parfit/gpt-5.6-sol，无P0/P1/P2 findings并已回收。
当前没有其他子仓实施或并行写入者；Root任务外kokoro-agent/.tmp保持不动。

- IAM 主目录已从1d78be6快进到源码 `1a081ab88368004b650a6e60d5445206fea5da18`，后续文档提交0d11f48、`8a4372c0fa3dd711807bd9eabc95f9ed516bd335`；最终干净。
- 原worktree仍1a081ab且干净；下一次续派前先同步主目录两文档提交。R1目录46手写文件/4生成物不变；本片只改六Repository及审计类型，不新增生产抽象层。
- 删除无用途identity表及自有结构、四闲置列和三查询索引；15表本表PK统一id，引用列/业务ID值不变。真实唯一不变量、状态、同client、tenant/父锁序、幂等/claim/fencing均保留。
- 主控候选和主目录各自重跑lint/typecheck/contract/build、随机空库安装及PG-only357项；主目录最终28文件/357通过/0失败/0skip，2Redis明确排除。
- 主控真实catalog差异核验通过；built provider五类3xx拒绝且sink0；Root预检仍9项，具体日志及范围见IAM ACCEPTANCE，未放宽门禁或改原Redis/Docker。
- 主控接管文档收口时补充README（原25文件片未授权作者改README）的16表旧说明；最终七份Markdown241本地链接/锚点通过。CURRENT精简一度漏固定兼容边界原文导致1个文档门失败，已恢复原文不改测试，聚焦36及全PG-only357重新通过；失败证据保留。
- 所有生产/DDL/机器源/测试/依赖字节仍绑定已审查1a081ab；完整证据由 [IAM ACCEPTANCE](../../../kokoro-iam/docs/ACCEPTANCE.md#r2-1-主目录集成与主控复验) 自持。

### 下一步：R2-2 删除语义（先文档，不沿用R2-1写入授权）

1. 主控保持架构决策；以当前8a4372c/源码1a081ab为基线，先收敛DATA_MODEL/TECHNICAL_DESIGN/API_CONTRACT的删除边界与验证清单，明确本片文件集。
2. 仅principal/organization承接已采纳deleted_at语义：默认NULL，TIMESTAMPTZ(3)，与disabled/suspended分离；不为所有表机械加列，不新增删除/恢复管理API或自动硬删。
3. 活跃身份路径同时检查父status与deleted_at：principal锁内校验、登录候选、session/permission投影；保留contact历史阻止失效身份重建、同tenant和父锁顺序。
4. refresh digest的历史定位保留，不能用活跃父/行过滤破坏合法Refresh重放或Logout；credential replay仍检查结果session和父资源，Logout成功receipt不套凭据释放条件。
5. 先用真实PG失败用例证明active但deleted_at非NULL也拒绝登录/GetSession/Authorize/新Refresh与凭据重放；原disabled/suspended及合法Refresh/Logout重放仍通过。父删除UPDATE与关系写入使用相同行锁协议，验证并发等待后重验，不仅静态扫列名。
6. 本片不夹带UTC/索引/完整catalog/GC/框架。Schema、两身份Repository、直接相关测试与三面文档自洽交付，最终仍由主控审查/独立质量/主目录复验。
7. 按用户新选模策略，复杂实现或独立审查优先gpt-5.6-sol；新负责人必须接收明确commit/任务卡，原writer停写后再派，单仓始终单writer。小任务可luna，疑难升级astra；不因模型切换丢失安全/验证门。

SQL UTC/查询计划、完整drift、关系检测/引用安全保留，及R3 API/运行治理仍后续推进；Redis2项、完整进程/镜像/真实provider/消费者未验。
本片验收不是整个goal完成，继续同一active目标；无需再次询问用户是否允许删除已确认无用结构或内部技术命名。

## 17. R2-2 身份删除切片任务卡

上一轮为progress：主目录R2-1已交付复验。本轮重新确认Root6d6c92ee、IAM8a4372c、原worktree1a081ab；双方干净，Root仅任务外kokoro-agent/.tmp。
主控先完成眼前架构/文档关键路径，提交IAM `5cb9e91df08899d6ef9693239d2f89cc16f262a0`：4份已有设计文档新增聚焦边界，生产/Schema/测试/机器契约零diff。
文档格式、245本地链接/锚点与diff通过；只通过本地文档验证，尚未实施删除标记。Root CURRENT改为导航本仓CURRENT/ACCEPTANCE，删除过期复制的commit/测试计数。

| 项        | 本片决定                                                                                                                                                        |
| --------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Owner     | IAM/auth；主控本轮先写三面设计后停写，独立设计审查由Parfit/gpt-5.6-sol承担；实现负责人在审查后命名派发                                                          |
| 代码基线  | 1a081ab；主目录当前设计5cb9e91；原worktree续派前快进到同基线；codex/iam-engineering-alignment                                                                   |
| 目标      | principal/org各加nullable TIMESTAMPTZ(3) deleted_at，默认NULL；两个原CHECK移除deleted状态，分别保留active/disabled与active/suspended                            |
| 位置/粒度 | 现有principal/session repository承接有效身份过滤，对比另造deletion Service后选择不新建生产代码/层；46文件树保留                                                 |
| 契约      | 机器源/生成物/六RPC三HTTP不变；失效身份Unauthenticated；Request不增加账号存在性反馈；历史refresh定位及Logout语义保留                                            |
| 并发      | 锁历史父行并在锁内重验，登录/有效session投影加双父删除条件；双向并发证明等待、提交后重验及回滚，不假装交付管理删除writer                                        |
| 测试位置  | 新test/integration/identity-deletion.integration.test.ts；复用原transaction fixture，允许窄typed helper；旧lifecycle已超500行，只改直接受影响输入不再堆整套场景 |
| 禁区      | 不改Service/transaction/crypto/client/worker实现、非两身份Repository、目录/依赖/lock/CI/config/机器源；不加UTC/索引/GC/其他仓改动                               |

设计依据：IAM DATA_MODEL§1.2、TECHNICAL_DESIGN§8.2、API_CONTRACT§7.2及ADR-030。当前5cb9e91仅设计审查，不自动授权源码。
审查绑定8a4372c..5cb9e91，确认删除条件覆盖登录/权限/GetSession/Refresh/replay、历史定位不被过滤、无新API/错误、两个父资源SQL与测试一致；只读，不运行DB/服务或改文件。
设计通过后允许：database/schema.sql、src/modules/auth/principals/principal.repository.ts、sessions/session.repository.ts；test/contract/schema.test.ts、test/integration/schema.integration.test.ts、authentication-lifecycle.integration.test.ts、新identity-deletion.integration.test.ts、test/fixtures/authentication-transaction-fixture.ts；确有直接QueryRow匹配影响的既有unit/fixture可局部调整并列明。
文档仅更新三面/CURRENT/ACCEPTANCE/INDEX/README中本片事实；不得重写历史证据，不移除CURRENT已有nonce兼容边界固定文字。

验收至少包括：精确两列/类型/NULL/default、两个状态CHECK的新集合与旧deleted拒绝；active但deleted_at非空时登录、GetSession/Authorize、新Refresh、Consume/Refresh普通重放与未知提交恢复均拒绝且无新增事实；删除父资源下Logout新命令/原回执保持原窗口行为；原未删身份/disabled/suspended/successor重放全保留。
两个父资源、login/refresh的锁竞争方向都应覆盖：删除先持锁→等待提交后认证拒绝；认证先持锁→删除等待，随后旧token读取拒绝。利用事务屏障与真实锁证据，不靠sleep推测；测试写方同时设deleted_at/updated_at，回滚不留下误删标记。
执行既有Node24.20.0/pnpm11.25/已装依赖，RED→实现→lint/typecheck/contract/build与verify-database.mjs --pg-only；随机隔离库、复用PG5432，Redis2项明确排除。无DB/Redis/Docker起停/flush或已有数据清理。
作者自洽commit后停写，主控规格复核、独立质量审查、主目录集成重跑；后续仍是完整IAM目标，不将该片冒充全部完成。

### R2-2 设计审查修正

Parfit绑定5cb9e91提出P2：首次Consume在组织删除后零候选由原PrincipalService返回FailedPrecondition，原文笼统要求Unauthenticated与“不改Service”矛盾。
主控核对principal.service和原no-valid-organization断言后采纳修正，提交 `012ebba969686f48f0b5a46553daef7fe51b4fb1`（三文档、无源码/DDL变化）。
明确：principal删除首次Consume仍Unauthenticated；组织删除仅剔除该候选，剩余有效组织照常选择，零候选/歧义保留FailedPrecondition。
目标session的双父删除才拒绝GetSession/Authorize/新Refresh/凭据重放；无关组织删除不连带失效。新增测试包括混合有效/已删组织，不以统一错误码改写原用例。
格式、245本地链接/锚点及diff通过；原worktree已快进012ebba，待同一审查员复核后才派实现者。
模型记录：本审查原派发指定gpt-5.6-sol，Parfit续派报告平台实际切换为GPT-6；主控工具没有回传实际型号，按“指定值/审查员报告”区分，不声称已独立核实实际模型。

### R2-2 设计门通过、源码放行

Parfit复核5cb9e91..012ebba：P2闭合、无新增findings；三面设计已一致，未运行DB。主控已核对实际Service与错误映射，现按本节文件集放行源码，基线012ebba。
为按用户新选模策略推进，旧负责人Boyle已交付停写，新负责人指定gpt-5.6-sol处理这一本界明确但含并发/重放的实现；主控不同时写IAM。
要求先记录旧Schema的RED，再在目标Schema已安装但两Repository仍旧逻辑时运行行为RED，证明测试能检出缺失删除条件，而非只因缺列失败；随后实现过滤与映射并全量验证。
独立catalog审查驱动已在旧源码基线上RED；最终只接受两个新增nullable列与两个CHECK状态集合变化，其他结构保持。
代码候选提交后停止写入，主控先规格复核，再续派独立审查员，最后主目录集成/复验。此放行不包含其他SQL/框架/运行治理。

本片实现负责人：Carver（01a0711d-0de8-7241-9c59-3305fb2c4863），派发指定gpt-5.6-sol；唯一worktree写入者，012ebba起始，接收上列明确文件集和两阶段RED/最终验收责任。主控停写IAM，保留审查、Root治理与隔离验证。

### 主控并行证据（不扩大 R2-2 文件集）

本轮只读重探测：原Redis56380的PING 2s超时，原Docker容器状态命令3s超时；没有重启/重复实例/flush，仍保留两个Redis待验。
为后续R2-3做现有pg驱动真实连接验证：当前runtime的search_path配置下TimeZone实际为America/New_York；显式UTC options时为UTC；
连接URL内若带options=TimeZone=Asia/Tokyo，会覆盖Client对象options，实际Tokyo且search_path也失去runtime显式值。
故后续“每连接UTC”不能只加一个可能被连接URL覆盖的对象属性；需定义受控连接参数与URL保留/拒绝规则，并验证连接重建与Pool/installer两入口。
日志在 `/tmp/kokoro-iam-goal/r2-2-review/shared-dependencies-probe.json`、utc-policy-probe.jsonl；只改连接自身session参数并读取设置，没有改角色/数据库配置或业务数据。

### R2-2 主控规格复核与返修

Carver交付候选 `33603ffd0c763d5b3e4bb31dd9f0610a319f276c`，主控尚未集成。生产变更限于唯一Schema及两个Repository，46手写文件与机器契约不变。
主控以012ebba和33603ff的不可变DDL分别安装随机空库，实际PG18.4 catalog对比通过：15表、127列、145约束、31索引；仅两列和两个CHECK集合变化，其余结构一致。两个自建库已清理，日志catalog-green-33603ff.log。
规格复核发现新增测试的真实锁等待观察存在竞态，部分失败路径未保证释放屏障/收束认证Promise；另有未到COMMIT即拒绝的测试被描述为恢复验证。
已续派同一writer修正有界屏障与清理，补删除回滚、拒绝不新增事实、无关组织不影响既有session、未知提交确实进入恢复的断言，并删除新增测试中的分支强转/空凭据fallback。
候选保持未放行，修正后才进入独立代码审查及主目录复验；作者报告的381通过不是该门已通过的依据。

后续UTC连接设计的官方依据已核验：[pg Client options](https://node-postgres.com/apis/client)、[PostgreSQL连接默认项](https://www.postgresql.org/docs/18/runtime-config-client.html)。
TimeZone是连接的时间解释/显示设置，不因列为TIMESTAMPTZ就自动固定为UTC；当前驱动的URL覆盖行为另由上述本机连接探针证明。
这项仅形成后续设计证据，不在R2-2修改连接配置或启动共享依赖。

### R2-2 独立审查通过与主目录集成

Carver先以06b5884补强测试；主控独立PG重跑384通过，但标准Prettier发现3份文档不合格。原作者format自报只指CRLF/尾空白检查，已在67e8683按标准CLI修正，并恢复初候选381与补强384的正确历史日志绑定。
Parfit对固定06b5884独立审查提出P2：auth先启动，writer连接获取失败却在try/finally外，会遗漏barrier释放并悬挂pool清理。110c7fa最小修复测试控制流，Parfit绑定该commit复核闭合，无新增findings。
主控完成规格审查后于本轮将日常IAM从012ebba快进到 `110c7faf77c7dbffb4c49aa67b2b5bda67260baa`；Carver和Parfit均已回收，主控接管文档收口，保持同仓单写。生产/DDL来自33603ff，契约、目录、依赖和其他仓未变。
主目录fresh PG-only：29文件/384通过，0失败/0skip，Redis两项排除；lint/typecheck/contract/build各exit0；7份标准Prettier与244本地链接通过。固定DDL实库catalog对比仅两列/两CHECK差异，15表127列145约束31索引。Root IAM-only预检仍9项失败，未降低门禁。
主控核查早期14个RED时发现部分是fixture TypeError，故另取06b5884临时副本、目标Schema和两个旧Repository重新证明：22个删除行为断言失败/96通过，无缺列、fixture异常或超时。首次pnpm驱动触发依赖检查不是RED，改直接Node执行既有Vitest后取得有效结果。正式工作树未为实验改动。
证据及失败边界归IAM ACCEPTANCE的R2-2主目录复验节，日志 `/tmp/kokoro-iam-goal/r2-2-review/`；只创建/删除自己的随机数据库，没有启停共享依赖/flush/修改已有业务数据。本片完成不代表完整IAM目标结束。

IAM收口提交 `c9d1d35e8f36a832a9db0a261b5a884038f321c4` 仅更新七份当前文档，已删除过期1a081ab/Boyle及R2-2待集成状态；生产/DDL/测试保持110c7fa字节。标准Prettier七份、246本地链接、三文件36项聚焦门通过，日常主目录干净；Root任务外kokoro-agent/.tmp保持原状。下一轮为progress续接UTC三面设计，不提前派源码，也不因Redis未恢复标记整个goal受阻。

### 下一片 UTC 只读设计输入（尚未放行实现）

Arendt（01a07130-214a-73f2-908d-281b41a11fba，派发指定gpt-6-astra）只读核查IAM主目录012ebba及已给探针，未读取writer变化或写DB，现已回收。
调查推荐在现有config下设窄database.ts配置函数，runtime Pool和空库installer Client两个真实消费者共用，避免导入整个runtime及复制URL解析器；不新建postgres层或连接框架。
每个物理连接以startup options固定UTC/search_path，不用异步connect事件或一次pool.query代表全池；URL原串保留交pg解析，对冲突options/超时及未知键明确策略，保留TLS/编码凭据/IPv6等支持，错误脱敏，不改角色或全局DB配置。
主控下一步须核对本地pg8.23.0/connection-string2.14.0的实际可接受键及环境优先级，收敛三面设计/文件放置门后再放行；调查中的完整白名单、PGOPTIONS策略与installer超时仍是候选建议，不能直接当已批准实现。
验证目标包括首条SQL前UTC、并发新连接/归还再借/销毁补建、真实installer和非法配置失败；主动SET/RESET污染与外部连接池模式须单列保证边界。其他索引/GC/框架改动不混入此片。

## 18. R2-3 每连接 UTC 与共用配置任务卡

上一轮为progress：R2-2已集成复验，IAM c9d1d35。当前Root c00b2905后续仅任务板；IAM源码/DDL/测试仍110c7fa。主控已读实际pg8.23.0/connection-string2.14.0、runtime/installer/config及架构门，完成眼前设计关键路径，提交 `4975b89527bce128dbb689e835f9a8b469124d25`（四文档，无代码变更）。标准Prettier七份、246本地链接、三文件36项聚焦门通过。

| 项 | 本片边界 |
| --- | --- |
| Owner/writer | IAM；主控完成当前设计后停写IAM，Arendt续派只读设计审查；通过后续派单一实现负责人 |
| 基线 | 日常IAM 4975b89；worktree仍110c7fa，续派writer前先快进同一文档基线并确认干净 |
| 三面 | TECHNICAL_DESIGN §8.3、API_CONTRACT §7.3、DATA_MODEL §7.1；当前为待审查设计，不冒充UTC已上线 |
| 放置 | 新src/config/database.ts供runtime Pool及installer Client共用；提取env数据库读取，不让installer导入全runtime，不建技术品牌目录/Pool框架 |
| 协议 | startup固定UTC/search_path；显式有限connect/operation预算；受控URI/键白名单、options/timeout冲突失败，原URL交pg解析，既有TLS语义不改 |
| 生产文件 | 新database.ts，现env.ts、runtime/create-runtime.ts、scripts/apply-schema.ts；其余生产/DDL/contract/generated/依赖/CI不动 |
| 测试文件 | 新unit/database-config.test.ts、integration/database-connection.integration.test.ts；必要时新fixtures/database-connection-fixture.ts；现config.test与architecture dependency-graph/dependencies/architecture-fixtures |
| 文档 | 七份当前文档按当前事实更新；保护已验基线/历史日志及CURRENT中的nonce边界，不编造现有format:check或drift命令 |
| 删除项 | 两入口分散的连接参数构造、installer直接读process.env；原Schema/查询/业务时间与认证/授权行为保留 |
| 明确非目标 | 不改全局角色/数据库设置，不升级Node/库/框架，不改TLS验证模式，不改业务SQL/时间序列化，不加入索引/GC/其他仓 |

设计审查使用固定c9d1d35..4975b89；特别检查URL parser实际覆盖与编码/重复键、PGOPTIONS/PGCONNECT_TIMEOUT优先级、错误脱敏、TLS保留、startup时序、installer权限与清理、共享函数与测试/架构证明范围。
只读审查Arendt（01a07130-214a-73f2-908d-281b41a11fba，原派发指定gpt-6-astra）；不写文件/运行DB或服务。审查通过后才单一writer实施，主控不并发写IAM。
实现要求先让旧runtime/installer未固定UTC及参数覆盖成为有效RED，再实现并green；使用Node24.20/pnpm11.25已装依赖，真实PG复用5432，随机测试库需要测试身份CREATEDB，不提权生产角色。真实验证包含配置单测、AST反例、多PID/补建/复用、实际runtime、实际installer空库/非空/回滚及query/statement budget；清理只认自身创建记录，不碰传入基准库或共享Redis。
最终lint/typecheck/contract/build、标准Markdown/link、全PG-only/真实入口由作者先验、独立审查后主控主目录集成重跑；Redis仍明确待验，不包装为全IAM完成。

### R2-3 设计门通过、实现放行

Arendt绑定c9d1d35..4975b89确认三面设计通过，无P1/P2；现已回收。主控停止IAM写入，worktree从110c7fa快进4975b89且干净。
唯一实现负责人续派Carver（01a0711d-0de8-7241-9c59-3305fb2c4863，原指定gpt-5.6-sol），仅允许上表生产/测试/文档文件集；每次新文件都按已审职责落点，不扩围。源码候选完成停写后，主控规格复核、独立代码审查、主目录集成/实跑。
主控以当前built runtime和生成的临时测试密钥实测三个不同PG PID，首条读取均为America/New_York，证明问题位于真实runtime而非手写示例对象；日志 `/tmp/kokoro-iam-goal/r2-3-review/runtime-red.log`。探针关闭自身Pool并清理临时密钥，无业务/Schema改动，未连接Redis或启动listener/worker。
本轮原Redis56380只读PING仍TimeoutError，记录redis-probe.json；没有重启/新建/flush。此项不阻止UTC配置与PG验证继续推进。

主控另对实际installer做只观察的connect hook，未替换配置/查询结果：首个应用SQL前TimeZone仍New_York，随后正常安装15表，自有新库已清理；installer-red.log证明第二入口同样待修。
实际同一PG连通性探针确认IPv6的query-host形式和Unix query-host形式可连接；已装驱动保留IPv6 authority的方括号，authority形态此轮连接失败。实现者已收到事实：原串交pg规则不变，不在UTC片自研补偿或升级依赖；API的IPv6支持须列明已验query-host形式，语法合法不等于驱动直连已验，authority缺口留运行/依赖治理。日志transport-forms-probe.json；只读SQL/自有连接，无全局配置变更。

### R2-3 候选审查与独立复验

Carver交付 `a1ae65d1937ab65b05e399981f5322d4dfc877c8`，已停写；18文件严格限于4生产、7测试、7文档，Schema/业务SQL/机器源/generated/依赖/CI没有变化。主控已读生产与测试diff，规格复核未发现阻断项；候选仍未合入日常主目录4975b89。
独立代码审查由Kant（01a07171-47f3-7291-a450-40a9fb373111，派发指定gpt-5.6-sol）承担，固定4975b89..a1ae65d，只读源码/设计与本地驱动，不连接数据库、不写文件。主控并行重跑候选lint/typecheck/contract/build、标准格式/link及完整PG-only，作者自报495通过不替代主控结果。
主控已独立运行候选built runtime与实际installer探针：三个不同PID首条读取均UTC；实际installer首个SQL前UTC、随后真实安装15表；只清理探针自己创建的数据库与测试密钥。日志 `/tmp/kokoro-iam-goal/r2-3-review/candidate-entry-green-a1ae65d.log`。这一通过不代替完整进程/Redis/TLS/消费者验收。

候选主控复验已完成：31文件495通过、Redis两项明确排除；lint/typecheck/contract/build、7份Markdown与4新增TS标准Prettier、257链接均通过，日志candidate-gates-a1ae65d.log。main-scope-check.json证明18文件授权集准确且Schema字节未变。Carver已回收；IAM继续等独立审查后才集成。Root IAM-only预检对主目录4975b89仍为原9项失败，未降低规则。

### 下一数据片的实测输入（不授权 R2-3 扩围）

主控从当前principal.repository的AST提取两条原SQL，在同一PG的随机自有库安装canonical Schema，建立每表10万行合成contact/membership及一致父资源，9万行为单一tenant，其余分散到10个tenant，含20% revoked/removed历史。历史邮箱查找和按principal取membership均Seq Scan、过滤99999行，分别1440/1429 shared hit blocks；只在该自有库加两个完整非唯一B-tree访问索引后均Index Scan、4 hit blocks，仍返回同一历史行。
原Schema/Repository未修改，自有库已删除；日志及完整JSON计划位于 `/tmp/kokoro-iam-goal/r2-4-review/query-plan-probe.log`、query-plan-evidence.json。该证据是单机合成访问路径对比，不是线上负载、容量或延迟SLO证明。下一片先更新三面设计再审查放行，评估完整历史读取索引；不得通过收窄status谓词、删除历史或扩大UNIQUE语义来换计划。其他JOIN/claim查询仍需单独代表性证据。

### R2-3 独立审查放行与非 UTC 测试补强

Kant固定4975b89..a1ae65d审查PASS，无P1/P2；P3指出当前UTC回归在默认已UTC的CI上可能失去辨识度。Carver已停写回收，主控接管日常IAM，先从干净4975b89快进a1ae65d，再仅补强两测试文件，不改生产/DDL/依赖。
补强限定test/fixtures/database-connection-fixture.ts及test/integration/database-connection.integration.test.ts：只对成功CREATE并登记的随机自有fixture数据库设置非UTC default，先用无共享配置的Client实际断言该默认，再让runtime多PID与真实installer证明显式UTC覆盖。不ALTER传入数据库、共享role或实例设置；临时库仍由原登记集统一清理。原三面文档中的不改全局配置规则保留，这是隔离测试前置条件，不是部署配置变更。主控先真实验证并提交该小补强，再交同一独立审查员只读复核；整个R2-3尚待主目录最终复验与文档收口。
