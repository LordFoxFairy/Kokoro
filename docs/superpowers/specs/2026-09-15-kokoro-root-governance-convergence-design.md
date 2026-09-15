# Kokoro Root 规范收敛设计

状态：独立规格审查通过，待用户书面审阅；设计基线为 Root `b0a143499b571b39f38a4112f47c83aa5548ad11`，2026-09-15。本文是 Root 规范与入口的收敛设计，不是九仓 Submodule cutover、分支删除或全仓发布完成报告。

## 1. 目标与边界

Root 只回答四类问题：正式组合包含哪些独立仓、业务事实与契约由谁拥有、当前组合实际处于什么状态、怎样验证和提升该组合。运行服务的 TypeScript/Python/Go 源码、数据库 Schema、机器契约、内部单测及依赖锁文件均由子仓拥有。

本切片的成果是把 Root 的权威入口、当前事实和目标态写成一条无矛盾的阅读链，并以现有治理测试证明九仓清单、owner、语言规范、测试归属和路径状态一致。不调整任何子仓内部目录，不移动 Git checkout，不更改数据库、API、镜像或分支引用。全九仓可复现与 `main` 收尾是后续独立切片；本切片不得用文档宣称两者已经实现。

## 2. 经核对的当前事实

Root `Kokoro/` 是治理主仓，不是 Next.js Web。Web 目前是本地 `Kokoro/kokoro/` 独立 Git 仓，远端名 `LordFoxFairy/kokoro-app`；当前不存在 `Kokoro/apps/kokoro/`。九个正式运行仓为 Web、BFF、Agent、IAM、System、Billing、Capability、Storage、Scheduler；System 已吸收 Model，Capability→Platform 仍是目标 cutover。旧 Model checkout 保留历史，不是第十个正式运行仓。

当前 `.gitmodules` 只声明 Agent；其他八仓是同目录的独立 checkout。`deploy/clone-active-repositories.sh` 对这些仓未固定 SHA；Root `.github/workflows/governance.yml` 允许缺失子仓并只运行静态治理；`scripts/verify-ten-repository-full.sh` 明确退出 2。因此 Root 静态拓扑 PASS 不等于九仓组合可复现、跨仓联调或发布 PASS。Root 及 Web 等多个仓有现存未提交修改；任何后续切片都不得覆盖、重置或暂存它们。

## 3. 规范唯一事实源与阅读链

| 问题 | 唯一权威 | 其他文件的职责 |
|---|---|---|
| 跨仓 owner、执行规则、设计门与验收 | Root `AGENTS.md` | 子仓 `AGENTS.md` 只补本仓事实 |
| 系统调用方向与目标九仓职责 | Root `docs/ARCHITECTURE_STANDARD.md` | `CODEBASE_MAP` 不重写系统规范 |
| TypeScript 后端的 NestJS 工程 | Root `docs/kokoro-handbook/standards/08-typescript-backend-engineering.md` | 子仓技术设计选择 feature 位置、ORM 与协议 |
| Python Agent 工程 | Root `docs/kokoro-handbook/standards/09-python-backend-engineering.md` | Agent 设计只说明其实际能力包 |
| PostgreSQL/SQL | Root `docs/kokoro-handbook/standards/03-sql-and-postgresql.md` | 数据 owner 选择本仓唯一 canonical Schema |
| 当前活动仓、物理路径与 remote | Root `docs/REPOSITORY_STATUS.md` | `CODEBASE_MAP` 只导航，不另立仓库清单 |
| 当前 commit、命令与未闭环证据 | Root `docs/CURRENT.md` | 历史报告不反向覆盖近期实测 |
| 代码入口和跨仓导航 | Root `docs/CODEBASE_MAP.md` | 由 `AGENTS`、架构、仓库状态与 CURRENT 派生 |
| 服务内部技术/API/数据/验收 | 各 owner 仓 `docs/TECHNICAL_DESIGN.md`、`docs/API_CONTRACT.md`、`docs/DATA_MODEL.md`、机器 `contract/` | Root 只引用版本、来源和 digest |
| 多步骤任务与提交切片 | 现有有效实施计划 | 不另建并行任务中心 |

Root README 是五分钟导航，先说明“当前工作区”再链接“目标结构”；不能把目标 `apps/` 当作现有路径。`docs/CURRENT.md` 只保留近期可核对事实、当前 commit/实际命令与未闭环项；旧报告与已替代 ADR 必须显式标为考古材料。文档收敛按来源优先级更新，不复制三份专项手册的章节到 Root `AGENTS.md` 或子仓。

冲突裁决顺序为当前用户裁决 → Root `AGENTS.md` 与三份专项手册（语言/数据）→ `ARCHITECTURE_STANDARD`（系统目标）→ `REPOSITORY_STATUS`（当前仓库集合/路径）→ `CURRENT`（近期实测）→ `CODEBASE_MAP`（派生导航）。例如当前 `CODEBASE_MAP` 把 Scheduler 写成“Optional Redis occurrence lease; no business DB”，与 Root `AGENTS.md` 的 PostgreSQL Schedule/Occurrence/Receipt/Outbox 权威事实冲突；本切片直接更正 `CODEBASE_MAP`，而不把旧描述提升为架构例外。

## 4. 目标工作区与测试归属

目标拓扑是 Root 主控仓加九个独立 Git Submodule。`apps/` 是部署单元容器，正式路径将在单独的拓扑 ADR 与路径清单中冻结；当前 `kokoro/` 不因本文被视作已移动。目标建议仍沿用当前本地子仓名，例如未来 `apps/kokoro/` 对应 Web 远端 `kokoro-app`，不引入第二个 Web 仓。

子仓可单独 clone/install/test/build/release。Web 自己保留 Next.js `src/app/`、`src/features/`、仓内 `packages/` 与 `pnpm-workspace.yaml`、自己的 `tests/`、contract 和 CI；该 pnpm workspace 绝不覆盖全部子仓。NestJS 后端各自保留 `package.json`/`pnpm-lock.yaml`、feature module、`test/` 与自己批准的 Schema 技术栈；Python Agent 使用 PyPA src layout、`uv.lock` 与 `tests/`；Go Scheduler 使用自己的 go.mod/go.sum 和测试。`apps/` 的 Git 路径变化不授权内部代码目录重写。

Root 不放子仓 unit test。Root 自有治理脚本由相邻的 `scripts/tests/` 测试；目标组合验证另由 Root 拥有独立的 `verification/` 责任面，覆盖锁定组合的 provider↔consumer 行为契约、跨服务集成、Browser→Web→BFF→owner 的关键用户旅程及已测镜像 digest smoke。这不是第二个 owner 契约仓，也不复制各子仓的 E2E。`verification/` 的新顶层目录、资源隔离与 CI 接入必须在独立实现切片中经过 Root 设计门；本文不预建目录。

## 5. TypeScript 工程裁定

Root Git 组合结构不等于一个覆盖九仓的 TS workspace。TS 后端按现行手册采用 NestJS 原生 Module、Controller、Provider/Service 与业务 feature 聚合；`src/<feature>/` 或 `src/modules/<feature>/` 由本仓技术设计择一。Repository、Mapper、Domain Model、CQRS 和通用子目录仅在有独立变化原因、事务/查询复杂度或真实消费者时创建。Controller 不拥有 SQL/Redis 或核心业务状态转换；Service 不向内部暴露 HTTP Request、ORM Row 或驱动类型；跨 feature 通过 Nest module exports 和受限 TypeScript 公开入口。运行时 wire schema、业务对象和持久化 Row 只在语义或生命周期不同才分开。

Web `kokoro` 不机械套用 NestJS 后端手册。它只拥有 UI、浏览器状态、HttpOnly session、同源 adapter 与 AG-UI→AI SDK 的仓内投影；浏览器只访问 Web `/api/*`，Web 不拥有 PostgreSQL/Redis，也不把 owner SDK 暴露给浏览器。每仓使用本仓锁文件、CI、contract 和文档；Root 不放覆盖全部子仓的 `pnpm-workspace.yaml` 或共享业务 lockfile。

## 6. `main` 分支政策与收尾条件

`main` 是每个活动仓唯一长期维护与发布的分支；为满足当前 `AGENTS.md` 的小切片审查，执行期间允许临时 `codex/` 任务分支。任务结束后，只有在所有被保留提交已集成到该仓 `main`、主工作树完成当前 commit 的验证、远端 `main` 可获取、未提交修改有明确 owner 与交接、且不再有依赖该分支的活跃任务时，才可清理临时分支。删除本地引用与删除远端引用是不同操作，远端范围须按用户确认执行。

当前审计显示 Root 当前任务分支有 339 个未合入本地 `main` 的提交，Web/BFF/Agent/Billing 等也有未合入提交和多个脏工作树；直接切换或删除分支不符合上述收尾条件。现有 `scripts/audit-repository-state.py` 把“执行中出现临时分支”也视为违规，与 `AGENTS.md` 冲突；后续脚本切片应区分只读工作状态审计与 release-clean 收尾门禁，不能通过放宽发布门禁把当前状态伪装成通过。

## 7. 方案比较与切片次序

严格单 Git monorepo 会消除各 owner 独立 Git/CI/发布边界，不选。仅用手写九仓 SHA manifest 可先阻断浮动 clone，但长期要同时校验实际 checkout，作为过渡锁使用。目标采用九仓 gitlink 固定源码，Root 发布 manifest 从 gitlink 派生源码 SHA 并增加契约、SDK（若存在）、镜像、工具链、验证证据和回滚引用；不得维护两个手工可编辑的源码锁。

次序为：

1. Root 规范入口与当前事实收敛（本文范围）；按明确文件集提交，不触碰 dirty SQL 手册、Agent gitlink、Web 或其他子仓。
2. 独立拓扑 ADR 与九仓 gitlink cutover；保护现有 checkout，在隔离目录验证全新递归 clone、远端 SHA、子仓独立构建和所有路径引用。
3. 锁定组合的资源隔离验证与 CI；unknown dependency/contract drift fail closed，不能用各仓 CI 状态代替真实交互测试。
4. 各仓提交与 `main` 集成验收后逐仓清理临时分支；不靠强制删除掩盖未合入提交。
5. 平台组合发布与 rollback 演练；测试和部署使用同一镜像 digest，数据库恢复条件单独验证。

## 8. 本切片验收与不变量

本切片的唯一任务表仍是 `docs/superpowers/plans/2026-09-03-kokoro-production-closure.md`；其中旧“十仓”导航须按九个正式运行仓修正并保留历史语境。允许修改的文件集仅为 Root `README.md`、`docs/CURRENT.md`、`docs/CODEBASE_MAP.md`、`docs/REPOSITORY_STATUS.md`、`docs/superpowers/plans/2026-09-03-kokoro-production-closure.md`、`scripts/tests/test_repository_topology.py`、`scripts/tests/test_engineering_handbooks.py` 及本文规格。`AGENTS.md`、三份专项手册、`docs/ARCHITECTURE_STANDARD.md` 是只读权威输入；现存 dirty SQL 手册、`uv.lock`、Agent gitlink、`.tmp/`、所有子仓及任务外目录均排除。若实施发现权威输入本身必须变更，应停止该切片并重新审查设计门，不自行扩大写入集。

先运行 `git status --short` 记录基线。新增/修订 `scripts/tests/test_repository_topology.py` 的断言必须确认九仓集合、Model 非活动、Web 当前路径与目标 `apps/` 分离、Scheduler PostgreSQL 权威事实在 `CODEBASE_MAP` 中存在；`scripts/tests/test_engineering_handbooks.py` 应改为检验手册来源与示例语义，不继续依赖过期的 18 个示例数量或单一旧标题。基线（2026-09-15，Root `b0a14349`）为 `python3 scripts/verify-repository-topology.py` PASS、`python3 -m pytest scripts/tests -q` 82 PASS / 2 FAIL、`python3 scripts/verify-ten-repository-standard.py --format json` 九仓 244 个现有违规。本切片放行须满足 topology PASS、`scripts/tests` 全 PASS、`git diff --check` PASS、标准审计仍覆盖九仓且没有本切片新增违规；比较违规须使用 repository/rule/detail 的稳定明细集合，不能只比较总数。244 个子仓既有违规必须如实列为未闭环，不以此切片宣称九仓全绿。实施后复核 Root README、CURRENT、CODEBASE_MAP、REPOSITORY_STATUS 和有效计划，任何“当前九仓”声明必须一致；任何 `apps/`、全九仓 CI、release manifest 或“only main clean”声明必须明确标为目标或待验。

本文通过只意味着规范设计可执行。九仓 gitlink、真实组合 CI、候选镜像、分支删除和完整发布均分别需要其自身 commit、命令与证据。
