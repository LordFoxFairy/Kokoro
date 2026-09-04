# IAM 工程规范对齐：主控任务板

状态：2026-09-04，IAM-01/02 文档与设计审查已完成；IAM-S1 已派工。完整重构验收 goal 仍在进行，尚未最终验收。

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
| IAM-03 | 按获准业务切片重构，不一次性搬空仓库                          | IAM-02 通过；逐片补齐任务卡 | IAM 负责人     | S1 已派工，其余逐片放行    |
| IAM-04 | 真实依赖、契约、架构与运行验证；评审提交和剩余风险            | 对应实现切片完成            | 主控及独立审查 | 未开始                     |

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
本设计及首片边界无阻断；这不是目标实现已通过。Ohm 已完成九文档交接，当前执行本片。

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
明确的隔离要求，不能依赖主控临时路径才运行。S1 交付 SHA 与新测试结果待实际执行后记录。
