# Capability → Platform：NestJS + Prisma 实施任务板

状态：进行中。用户已批准总体方案并授权推进（2026-09-07）。本任务板是本轮唯一推进记录。

**Goal:** 将当前 Capability 的有效 Skills/MCP 控制面收敛为 NestJS + Prisma 原生实现，补齐失败恢复，最后独立闭环 Platform 拓扑切换。
**Architecture:** Root 裁决边界；子仓单一 writer；Skills/MCP 是两个一级业务域。沿用 owner 发布的契约，不复制 IAM、Storage 或 Agent 事实，不恢复历史 Platform。
**Tech Stack:** NestJS、Prisma、PostgreSQL、Redis、Connect RPC；精确版本需核验后记录。

## 设计依据与基线

- Root: `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro`，分支 `codex/production-closure-governance`，起始 commit `7170a1ff3da0e1cdb82809223cd5b6fda1f5cac5`。
- 子仓: `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-capability`，分支 `codex/production-closure-docs`，起始 commit `637cc8bc473bfa9080bb2731161e7b0e1aaa8eda`，开始时无未提交变更。
- Root 已有未提交修改：SQL 手册、kokoro-agent gitlink 和 `.tmp/`。这些不属于本切片，不暂存、不覆盖。
- 必读：Root AGENTS、`docs/CODEBASE_MAP.md`、SQL 手册 03、TypeScript 手册 08、ADR-029，以及子仓 README/INDEX/CURRENT/TECHNICAL_DESIGN/API_CONTRACT/DATA_MODEL。
- 用户已确认 IAM 等仓独立推进；本任务不接管其他仓、不用 Root 旧 IAM-only 导航阻断本仓设计。
- 当前态：49 个源码文件；Node HTTP/Connect 组合根、SQL-first + pg；现有 HTTP projection、7 个 RPC surface、9 张表和测试需逐项承接。manifest 有 Fastify 不等于当前 ingress 使用 Fastify。

## 放置表（AGENTS §8）

| 项 | 决定 |
|---|---|
| Owner | Capability/目标 Platform；Skills/MCP 唯一 writer 为本仓实现负责人，Root 只写计划和集成记录 |
| 当前事实 | 以以上 commit、源码清单、契约和 schema 为行为基线；测试实跑证据另录 |
| 目标职责 | Nest 组合/DI/生命周期，Prisma 数据访问，Skills/MCP Service 明确业务状态与失败恢复 |
| 目录方案 | 采用 `src/modules/skills`、`src/modules/mcp`；相比直接 `src/skills`，与 config/database/health/generated 类别分离更清晰，符合 ADR-029 |
| 粒度 | 现有聚合式 application/ports/models 按真实变化原因拆分；简单 Service 直接用 Prisma，不机械造 Repository/DTO 五层或空目录 |
| 依赖 | 传输→业务 Service→Prisma/owner client；禁止跨 owner 数据库、跨仓相对 import 和生成数据库类型穿透公开契约 |
| 数据/API | 唯一 Prisma schema；无外键、受信 tenant、幂等摘要/操作校验、稳定分页、原子本地 mutation/outbox/成功 receipt；外部操作有持久化恢复阶段 |
| 删除 | 被替代 bootstrap、pg CRUD、SQL schema、旧分层与无效架构断言随实现退出；不删除仍有效安全检查；不留兼容服务/双写 |
| 验证 | format/lint/typecheck/unit/contract/architecture/build/Prisma validate+generate/schema drift/integration/smoke；真实依赖独立资源 |

## 任务卡与单一写入授权

共享 checkout 的 Git index、分支和 commit 由 Root 串行管理；worker 不提交。新建源码/改 schema 前必须先通过 P0 文档门。同一负责人后续按卡续派，不默认获得全部阶段授权。

| ID / 优先级 | 目标、完成条件 | Agent / 模型 / 权限 | 文件集 | 依赖 / 并行 | 状态 / 提交 |
|---|---|---|---|---|---|
| P0-A / P0 | 盘点协议、安全/状态机与消费者依赖，提出必须保留的行为与切换风险 | contract-review / gpt-5.6-sol / 只读 | 子仓 contract/src/test/docs，BFF/Agent 消费入口只读 | 可与 Root 设计并行 | 已交付只读报告 |
| P0-D / P0 | TECHNICAL_DESIGN、API_CONTRACT、DATA_MODEL、子仓 AGENTS/ADR/CURRENT 对齐，记录版本证据与未决项 | Root / 当前模型 / 写入（派实现前） | 子仓上述现有文档、ADR 新文件；Root 本任务板 | 参考 P0-A；不改源码/机器契约/schema | 已审查并提交 |
| P0-R / P0 | 独立检查三份文档与计划的一致性、可执行性 | contract-review / gpt-5.6-sol / 只读 | P0-D 文档与当前 contract/schema | P0-D 完成后 | 已通过（三项整改复审） |
| P1 / P0 | 原生 Nest/Prisma 底座及现有持久化行为切换，单一生产路径、生成 Client、fresh schema 与真实启动验证 | capability-owner / gpt-5.6-sol / 写入，需 Root 放行 | 子仓 src、prisma、prisma.config.ts、package/lock/tsconfig、构建配置、scripts、test、必要 docs；不改机器 wire contract/其他仓 | P0-R 通过；实现和只读审查分离 | 待派工 |
| P2 / P0 | Skills 发布/版本/来源/安装业务模块闭环；承接安全与分页断言 | capability-owner / gpt-5.6-sol / 后续授权 | Skills 源码/测试/必要契约文档；共享文件由任务卡另定 | P1；owner 契约先于消费者 | 待派工 |
| P3 / P0 | MCP connector/server/connection/authorization 模块闭环 | capability-owner / gpt-5.6-sol / 后续授权 | MCP 源码/测试/必要契约文档 | P2；不实现 Agent runtime | 待派工 |
| P4 / P0 | receipt/outbox 崩溃恢复、有限重试、retention 和可观测性 | capability-owner / gpt-5.6-sol / 后续授权 | 本仓实际用例涉及文件，实施前细化 | P2/P3 | 待派工 |
| P5 / P1 | Platform 服务/仓名、schema namespace、身份、部署、owner contract 发布和消费者一次 cutover | Root 协调各仓负责人 / 后续授权 | 独立切换任务卡，未授予其他仓写权 | P1–P4；跨仓串行交接 | 待派工 |

## 实施检查清单

### P0：设计门
- [x] 实跑当前 lint/typecheck/test/build/schema/contract 基线：均 exit 0，141 passed / 4 skipped；真实连接尚未配置。
- [x] 核验 Nest/Prisma/Node/Connect manifest engines/peers；Node 24.13.0、Prisma 7.10.0、Nest 12.0.1、Connect Express 2.2.0，详细记录见 ADR-001；安装及运行实测留 P1。
- [x] 更新现有三份设计、ADR、子仓指令与 CURRENT；不新建平行设计中心。
- [x] 独立审查 P0：contract-review 三项整改复审通过；三份绝对路径与 commit 见下方通过报告。
- [x] Root 逐路径提交 P0 文档；仅授权 P1a。

### P1a / P1b：可独立审查的底座子切片

P1a 负责人权限：允许创建 `prisma/schema.prisma`、`prisma.config.ts`、`src/generated/prisma`、`src/database`；替换 `src/infrastructure/repository/capability/postgres-*.ts` 为具名 Prisma 组件；修改现有 bootstrap 的数据连接/关闭装配、package/lock/tsconfig/eslint/vitest/build/Docker 配置、scripts 与相应 test/docs。删除旧 SQL schema 和被替代 pg CRUD。禁止改 wire contract、业务状态机/owner 语义、其他仓和 Root 文件；保持当前唯一 ingress。生成类型只生成。Root 独占 Git 操作。
P1a 仍使用现有业务 data-access port 是明确的中间依赖，P2/P3 退出聚合 port；不可新建另一套空架构。
P1b 在 P1a 验收后另授权：Nest 原生 composition/lifecycle、health/projection controller、Connect 官方 middleware 同 listener，删除旧 bootstrap/router。业务 Feature 原生 DI 继续 P2/P3 按用例收敛。
P1a 的 red/green 必须覆盖 typed Prisma 读写、tenant 隔离、同库 mutation/outbox 回滚、connection policy 并发、receipt replay/digest/operation、复合分页、fresh-install/refuse/drift；缺失的恢复用例明确列 P4。

### P1：底座与持久化切片
- [ ] P1a：先新增并运行失败测试：Prisma 唯一 schema、无业务 pg SQL、tenant/并发/分页/事务基线。
- [ ] P1a 值域 gate：逐项验证 owner_kind、skill/connector/server/connection/authorization/installation/receipt/outbox status、connector type、transport、capability kind、effect 的生成 PostgreSQL enum，非法值在数据库写入时被拒绝；旧 CHECK 语义不丢失。
- [ ] P1b：先新增并运行 Nest 生命周期、HTTP/Connect raw-body/auth/route 失败测试。
- [ ] 建立生成 Client 与 ORM schema；无外键生成结果实测，不保留两份可编辑 schema。
- [ ] P1b：Nest 管理进程与资源；Connect 保持官方协议 adapter，不另开平行服务，不自动假设 Nest Guard 覆盖 Connect 请求。
- [ ] 用 Prisma 接替现有持久化，保持契约、安全检查和有效业务行为；P2/P3 仍待收敛部分如实列明，不把中间切片当最终架构。
- [ ] 空库安装必须先检测非空并拒绝破坏；独占安装锁；drift 检查列/类型/默认值/约束/索引。
- [ ] 承接测试并删除仅固定旧目录的断言，新增实际依赖方向断言；不得靠删安全测试让门禁通过。
- [ ] 负责人交付文件清单和 red/green 证据；独立规范审查通过后进行代码质量审查。
- [ ] Root 重跑验证、按明确路径暂存并提交；更新同一任务板。

## 验证命令与资源规则

在子仓运行：`pnpm lint`、`pnpm typecheck`、`pnpm test`、`pnpm build`、`pnpm contract:check`、`pnpm schema:check`。
P1 新增：`pnpm format:check`、`pnpm prisma:validate`、`pnpm prisma:generate`，以及仅对新建隔离数据库执行 `pnpm db:apply-schema`。
真实依赖：`REQUIRE_REAL_INTEGRATION=1 pnpm test:integration`，使用现有共享 PostgreSQL/Redis，独立 database/schema/tenant/namespace；不清空用户或其他 Agent 数据。
Root：`python3 scripts/verify-ten-repository-standard.py`；完整跨仓验证需各仓当前环境齐备，缺失时如实记待验，不触发其他仓安装、覆盖或重启。

## 证据与交接

尚未有本轮实现或验收结论。每波记录实际命令、exit code、pass/fail/skip、提交 SHA、审查人与剩余 owner；Root 现有脏文件不纳入提交。

### P0-A 只读审查交接

审查员 contract-review / gpt-5.6-sol，基线 637cc8b。确认 7 个 RPC/4 个 HTTP projection、两套鉴权、动态 attestation、tenant、state、cursor 与 receipt identity 必须承接。
新发现：BFF owner routes 当前请求 `/bff/skills*`、`/bff/mcp/servers`，Capability 只发布 `/v1/...`，P5 必须由消费者负责人修正并 contract-test，禁止添加 alias。Agent 配置/client owner 交接在 P5，不抢写。
旧基线完整门禁：lint/typecheck/test/build/schema/contract 均 exit 0；37 test files passed、2 skipped；141 tests passed、4 skipped；contract digest `8650a846cef411f503398996d8a4340acd791b5bb8fb65b1071b74fc7e2aceca`。

### Root 门禁基线与环境

2026-09-07 `python3 scripts/verify-ten-repository-standard.py` -> exit 1，215 rule violations，跨仓既有目录/工具链/配置等缺口；本轮不通过修改其他 owner 或放宽检查清零。
本地只读探测：已有 PostgreSQL 18.4 监听 5432、Redis 监听 6379 且 PONG；不启动第二套服务。Node 24.13.0 显式 PATH 下已重跑 contract/schema/architecture，22 architecture tests passed。

### P0 通过报告

子仓设计 commit：`c86d3cef2222f94a49dbb1a3e9f12c652b936f0d`。独立审查：contract-review / gpt-5.6-sol，P0-R 三项整改复审通过，Root diff --check 通过。
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-capability/docs/TECHNICAL_DESIGN.md`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-capability/docs/API_CONTRACT.md`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-capability/docs/DATA_MODEL.md`
当前契约/schema 检查 exit 0，Node24 下 architecture 22 passed；Prisma schema 尚待 P1a 创建验证，本报告只放行该实现设计，不表示 ORM/框架切换已验收。
未决项：P2 安装 API、P4 实际事件消费者/publisher 与保留策略、P5 跨仓路由/身份更新，均由对应后续切片处理，不阻挡 P1a。
资源：Root 新建专用 `kokoro_capability_p1a_20260907_worker` 与 `kokoro_capability_p1a_20260907_root` 数据库，复用 PostgreSQL5432/Redis6379；worker仅使用worker库，不清空Redis。
