# Capability → Platform：NestJS + Prisma 实施任务板

状态：P0、P1a、P1b、P2a、P2b、P2c 已验收；P3 设计门已放行，P3 实现及 P4–P5 待推进。用户已批准总体方案并授权推进（2026-09-07）。本任务板是本轮唯一推进记录。

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
| P1 / P0 | 原生 Nest/Prisma 底座及现有持久化行为切换，单一生产路径、生成 Client、fresh schema 与真实启动验证 | capability-owner / gpt-5.6-sol / 写入，需 Root 放行 | 子仓 src、prisma、prisma.config.ts、package/lock/tsconfig、构建配置、scripts、test、必要 docs；不改机器 wire contract/其他仓 | P0-R 通过；实现和只读审查分离 | 已验收：P1a `d32631f`，P1b `8606f87` |
| P2 / P0 | Skills 发布/版本/来源/安装业务模块闭环；承接安全与分页断言 | capability-owner / gpt-5.6-sol / 后续授权 | Skills 源码/测试/必要契约文档；共享文件由任务卡另定 | P1；owner 契约先于消费者 | P2a/P2b/P2c 已验收 |
| P3 / P0 | MCP connector/server/connection/authorization 模块闭环 | capability-owner / gpt-5.6-sol / 后续授权 | MCP 源码/测试/必要契约文档 | P2；不实现 Agent runtime | 设计门审计已放行；实现待设计通过 |
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
- [x] P1a：先新增并运行失败测试：Prisma 唯一 schema、无业务 pg SQL、tenant/并发/分页/事务基线。
- [x] P1a 值域 gate：逐项验证 owner_kind、skill/connector/server/connection/authorization/installation/receipt/outbox status、connector type、transport、capability kind、effect 的生成 PostgreSQL enum，非法值在数据库写入时被拒绝；旧 CHECK 语义不丢失。
- [x] P1b：先新增并运行 Nest 生命周期、HTTP/Connect raw-body/auth/route 失败测试。
- [x] 建立生成 Client 与 ORM schema；无外键生成结果实测，不保留两份可编辑 schema。
- [x] P1b：Nest 管理进程与资源；Connect 保持官方协议 adapter，不另开平行服务，不自动假设 Nest Guard 覆盖 Connect 请求。
- [x] 用 Prisma 接替现有持久化，保持契约、安全检查和有效业务行为；P2/P3 仍待收敛部分如实列明，不把中间切片当最终架构。
- [x] 空库安装必须先检测非空并拒绝破坏；独占安装锁；drift 检查列/类型/默认值/约束/索引。
- [x] 承接测试并删除仅固定旧目录的断言，新增实际依赖方向断言；不得靠删安全测试让门禁通过。
- [x] 负责人交付文件清单和 red/green 证据；独立规范审查通过后进行代码质量审查。
- [x] Root 重跑验证、按明确路径暂存并提交；更新同一任务板。

## 验证命令与资源规则

在子仓运行：`pnpm lint`、`pnpm typecheck`、`pnpm test`、`pnpm build`、`pnpm contract:check`、`pnpm schema:check`。
P1 新增：`pnpm format:check`、`pnpm prisma:validate`、`pnpm prisma:generate`，以及仅对新建隔离数据库执行 `pnpm db:apply-schema`。
真实依赖：`REQUIRE_REAL_INTEGRATION=1 pnpm test:integration`，使用现有共享 PostgreSQL/Redis，独立 database/schema/tenant/namespace；不清空用户或其他 Agent 数据。
Root：`python3 scripts/verify-ten-repository-standard.py`；完整跨仓验证需各仓当前环境齐备，缺失时如实记待验，不触发其他仓安装、覆盖或重启。

## 证据与交接

P0 与 P1a 已完成本轮验收，实际命令、提交、审查与剩余 owner 见下方记录。Root 既有脏文件未纳入提交。

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

### 当前派工（P1a）

capability-owner / gpt-5.6-sol，基线 c86d3cef2222f94a49dbb1a3e9f12c652b936f0d；只授权上方 P1a 文件集，共享 index/commit 由 Root 管理，交付后独立审查与主控重跑。
contract-review / gpt-5.6-sol 同时只读准备 P1b 装配/HTTP/Connect 测试清单；读取 c86d3ce 固定源码，不写文件，不在变化工作树运行最终验收。

### Root 集成复验矩阵

| 关注点 | 所需证据 | 阶段 |
|---|---|---|
| 单一 schema/数据库访问 | SQL canonical 删除，业务 src 无 pg Pool/raw CRUD；Prisma生成可重复 | P1a |
| 旧值域承接 | PostgreSQL enum/类型/constraints catalog；非法值拒绝 | P1a |
| tenant 写保护 | 同 ID 跨tenant写拒绝，不仅测试跨tenant读取 | P1a |
| 业务事务 | mutation后outbox失败一起回滚，同一 Prisma transaction client | P1a |
| connection 竞争 | 同identity同policy重放/不同policy冲突，真实并发写入 | P1a |
| receipt 基线 | digest/operation漂移拒绝、重放codec、failed重试；不冒称crash原子 | P1a |
| 安装边界 | 独立新空库成功、非空拒绝、并发安装仅一次、故意加列/索引/constraint/enum drift拒绝 | P1a |
| 无丢失协议行为 | 既有 HTTP/Connect/attestation/pagination/status 回归 | P1a / P1b |
| 生产装配 | 构建生成物路径正确、真实DB/Redis启动及依赖失败不监听 | P1a / P1b |
| 原生Nest入口 | 同listener、Connect原始stream未被parser吞掉、两套auth分离、controller无SQL | P1b |

完整 Root full.sh 本轮尚不执行：该脚本编排所有正在由其他负责人修改的仓和发布资源，不是当前单仓稳定验收面；Root standard 已记录215项基线失败，最终再次只读核验。

### P1b 准备性只读审查（待 P1a 验收后授权）

contract-review 固定基线 c86d3ce：Nest Express单listener，bodyParser:false，在parser消费原stream前装官方Connect middleware；精确服务路径分派，不吞掉health/BFF路由。
P1b 必须由Nest DI管理Prisma/Redis/各owner clients/readiness/HTTP controller/guard/filter；main不得手工new整图。仅允许注入依赖后构建现有CapabilityServices的单点中间factory，P2/P3按业务拆除。
必验：真实HTTP protobuf与JSON Connect调用、BFF/RPC两套鉴权各自失败/成功、unknown v1=404/nonGET=405/no-store/request-id、缺失tenant、动态attestation、启用surface依赖、启动失败不监听、关闭幂等/drain/deadline。
P1b按已接受方案修改入口/构建/容器/相关测试和文档；不顺带改wire或业务状态机，不引入第二server。

### P1a 变化中工作树预审（非验收）

Root 与 contract-review 已反馈并要求回归：ownerScopes/query/cursor 的 OR 条件必须 AND 组合；tenant检查与写入须原子；事务内唯一冲突不得继续使用已abort事务；receipt仅归一明确冲突、影响行数必须校验、JSON不得as never；空库安装要覆盖非表对象并明确public-only/目标schema；enum/约束/catalog drift完整检查。
Root批准为保留旧concat(name,' ',summary)搜索语义增加同owner内部派生searchText列（每次Skill写入同步派生），不改wire、不得raw SQL或先分页后内存过滤；实现负责人更新ADR/DATA_MODEL及跨字段搜索组合过滤测试。
要求恢复所有旧receipt digest/operation/processing/failed/codec断言，补tags包含全部、最新approved scope、授权NULL expiry fail-closed、同identity connection并发、安装并发/失败回滚。此记录不表示整改完成，最终看固定交付快照及主控实跑。

### P1a 数据专项预审任务卡与结果

角色 database-review / gpt-6-astra / high / 只读，基线c86d3ce之后的变化中工作树；范围scripts安装/drift、Prisma config/schema、transaction/receipt/connection。不得运行数据写入或修改文件，Root审查与实际验证后才放行。
发现并派capability-owner整改：P1启动仅$connect未真实DB probe；P2空库检查漏function/procedure；P2运行/安装/drift的URL schema范围不一致；P2Prisma diff忽略额外view/trigger，需要catalog对象白名单。
Root批准生命周期内固定SELECT1作为唯一health raw例外，普通业务仍禁raw；要求启动不可达DB不监听回归、ADR与架构限定一致。
Root供应链核验：`docker buildx imagetools inspect node:24.13.0-bookworm-slim` exit0，multiarch index digest `sha256:4660b1ca8b28d6d1906fd644abe34b2ed81d15434d26d845ef0aced307cf4b6f`；交实现负责人固定两FROM，不能从旧pin退为tag。

### P1a 最终交接与验收（2026-09-08）

- 任务/owner：P1a / kokoro-capability / capability-owner（gpt-5.6-sol）实现；Root 独占 Git index、集成与复验。实现负责人已交付并停止写入。
- 基线：`/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-capability`，`codex/production-closure-docs`，`c86d3cef2222f94a49dbb1a3e9f12c652b936f0d`。
- 实现提交：`10d97612d4d8a74697dae0be1a2f3a186a4b1f68`；生成规范化提交/最终验收 SHA：`d32631fa04b36a57f00c464bd78fcdde3ec10f1f`。共享 checkout 由 Root 提交，无 cherry-pick SHA。
- 文件集：子仓唯一 `prisma/schema.prisma`、Prisma 配置/生成物、database client/transaction、现有 capability repository 实现、bootstrap 数据连接、安装/drift/build/CI、相关测试与设计/当前文档。完整精确清单以这两个 commit 的 `git show --name-only` 为准；未改 wire contract、其他 owner 仓或 Root 既有脏文件。
- 结果：删除旧 SQL canonical 与手写 pg CRUD；typed Prisma 承接 tenant、组合过滤/分页、数据库值域、本地 mutation/outbox 原子性及 receipt 现有语义。仍保留的聚合 data-access port 与旧 ingress 是 P1b/P2/P3 明确待替代项，不是最终 Nest 架构。
- 独立规范审查：contract-review / gpt-5.6-sol，整改后通过。独立数据/代码质量审查：database-review / gpt-6-astra，整改后通过、无未闭环 P1/P2。审查绑定提交前交付工作树，Root 复核并提交为 10d9761；后续 d32631f 仅生成流水线/ADR及其自动输出，Root 单独审查并全量复验。
- 生成修正：暂存检查发现上游 Prisma 输出尾随空白；后续固定生成命令执行仓内固定版本 Prettier，未手改生成物或关闭 whitespace gate。17 个生成文件重复执行前后 SHA-256 清单完全一致，`git diff c86d3ce --check` 通过。

Root 在最终提交相同工作树、Node 24.13.0 下执行（全部 exit 0）：

| 命令 | 实际结果 |
|---|---|
| `pnpm prisma:generate` + 生成文件 SHA-256 对比 | 重复生成一致；build 复用同一生成入口 |
| `pnpm format:check` | P1a 明确文件范围通过，不冒称全仓格式化完成 |
| `pnpm lint` / `pnpm typecheck` | 通过 |
| `pnpm prisma:validate` / `pnpm schema:check` | Prisma 有效、真实 PostgreSQL schema 无 drift |
| `pnpm contract:check` | 通过，wire digest 仍为 `8650a846cef411f503398996d8a4340acd791b5bb8fb65b1071b74fc7e2aceca` |
| `REQUIRE_REAL_INTEGRATION=1 pnpm test` | 42 files / 162 passed，0 failed、0 skipped |
| `REQUIRE_REAL_INTEGRATION=1 pnpm test:integration` | 9 files / 56 passed；包含组件测试，不把 56 项全部称为真实外部集成 |
| `pnpm build` | 通过 |
| `pnpm smoke:production` | 编译后入口 + 真实 PostgreSQL/Redis 通过；Storage/IAM/Secret/MCP provider 为本地协议 stub |
| `git diff c86d3ce --check` | 包含实现与规范化的整体差异通过 |

真实数据库专项共 12 项（repository 9、installer 3）；另外已完成首次隔离空库 `pnpm db:apply-schema`、非空拒绝/并发安装/DDL 回滚、坏 DB 启动拒绝、额外 view/CHECK/materialized view drift 注入拒绝及清理后复验。只操作本任务专属数据库和随机测试数据库，未重启或清空共享 PostgreSQL/Redis。
最新主控完整日志：`/tmp/kokoro-p1a-codegen-final-20260908.log`；前次完整/专项证据：`/tmp/kokoro-p1a-root-final-20260907.log`、`/tmp/kokoro-p1a-root-verification-20260907.log`。日志为本机临时验收证据，不作为仓库正式工件。

### P1a 验收时的未完成、风险与后续 owner

1. P1b 已在后续切片以 `8606f876e8cce0c7affa346049f62910218793b0` 验收；P2 Skills、P3 MCP、P4 receipt/outbox 崩溃恢复和 retention、P5 Platform cutover 仍待实施。
2. 当前 receipt 完成写与业务提交未合并为一个事务，外部副作用的崩溃恢复没有闭环；留 P4，未以本轮 Prisma 替换冒称解决。
3. Root standard 最新实跑 exit 1：214 violations，其中 Capability 16；记录 `/tmp/kokoro-p1a-root-standard-20260907.json`。Root 后续独立切片修正 checker 对 ORM canonical 与只读生成物的识别（repository_checks 仍强制 SQL schema，typescript_checks 扫描 Prisma generated），同时继续保留真实目录/工具链缺口的失败门禁；不以放宽规则清零。
4. Docker daemon `/info` HTTP 500，镜像 build/smoke 未运行；官方 Node 镜像 digest 已实查并固定。完整跨仓 `./scripts/verify-ten-repository-full.sh` 未运行：其他 owner 正在修改，缺少稳定联合验收面及可用 Docker。Root 负责后续协调，不干扰其他任务进程。
5. 下一阶段需完成真实 IAM/Storage 等 owner sandbox 联调；本轮 smoke 的协议 stub 只证明本仓装配行为。

当时状态：P1a 已验收；总体计划未完成。后续 P1b 的实际交付与验收见本任务板后文。

## Goal 续接与 P1b 任务卡（2026-09-08）

用户要求先设置 Goal 再推进，Goal 已创建且 active，目标覆盖既有 P1b–P5 顺序，不把一次切片完成当作总目标完成。
本轮新基线：Root `4c958c969fa41f52e514744f6362a9aae95f9856`（大量其他任务未提交变更）；Capability `d32631fa04b36a57f00c464bd78fcdde3ec10f1f`，分支 `codex/production-closure-docs`，子仓干净。Root 只写本任务板，不接管 System 正在更新的 Root 文档/治理工具。
最新 AGENTS 第10节替代历史默认门禁：执行 standard、topology、`python3 -m pytest scripts/tests`；旧 full.sh/owner-health 已暂停（只诊断退出2），不再列为待恢复执行命令。全仓隔离编排由 Root 独立任务重建。

| ID | 目标/完成条件 | Owner/角色/模型/权限 | 文件集/资源 | 依赖与交付 |
|---|---|---|---|---|
| P1b-D | 刷新当前态、细化 Nest 装配与关闭顺序，三设计一致 | Root / 设计 / 当前模型 / 写入 | 子仓 TECHNICAL_DESIGN/API_CONTRACT/DATA_MODEL/ADR；Root仅本任务板 | 已批准大方向；设计刷新后才授权实现，Root提交 |
| P1b-R0 | 固定 d32631f 核对 HTTP/Connect 既有行为及新方案必验矩阵 | contract_review / gpt-5.6-sol / 只读 | 子仓src/test/contract/docs；不改文件、不启动服务、不写数据库 | 与Root设计并行；报告准确路径与行为，不实现 |
| P1b-I | Nest唯一入口/DI/生命周期，原生HTTP Controller、Guard/Filter及官方Connect同listener；旧入口删除 | capability_owner / gpt-5.6-sol / 唯一writer（P1b-D通过后授权） | 子仓src/main.ts/app.module.ts/config/database/health/http/rpc；旧bootstrap与interfaces必要删除/引用；package/lock/tsconfig/vitest/build/CI/Docker/scripts/test/必要docs；不改canonical schema/wire契约/其他仓/Root | 先失败测试、再实现；Git由Root独占；只用既有worker专属PG库与Redis5，不重建实例 |
| P1b-R1 | 先规范审查后独立质量审查，阻断整改 | contract_review / database_review / 只读 | 实现停写快照或交付commit，禁止重置数据/服务 | Root先复核范围，再重跑本仓门禁与最新Root门禁；验收后精确路径提交 |

允许保留一个注入完依赖后的 CapabilityServices 中间factory，P2/P3按业务拆除；不允许把旧createRuntime包进单provider冒充Nest原生。不得以Nest Guard默认保护middleware RPC。生成物只通过唯一脚本更新。子仓schema与wire不变，任何新增owner/契约决定先报告Root。


### P1b-D 通过与 P1b-I 放行

2026-09-08，contract_review对三设计当前差异复核通过，无blocking。Root复核ADR今日版本/生命周期证据。
通过文件：
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-capability/docs/TECHNICAL_DESIGN.md`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-capability/docs/API_CONTRACT.md`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-capability/docs/DATA_MODEL.md`
未决项仍为P2安装契约/P4publisher恢复/P5拓扑切换，均不阻挡P1b。
Root在d32631f实现基线上重新执行：pnpm test=162 passed/0 failed/0 skipped；contract:check、prisma:validate、真实schema:check exit0，日志 `/tmp/kokoro-p1b-child-baseline.log`。
Root最新工作树静态基线：standard exit1/197 violations；topology exit0；pytest scripts/tests=72 passed/2 failed（handbook测试仍期待18示例及固定标题“参考依据”，当前实际11示例/新标题）。日志 `/tmp/kokoro-p1b-root-{standard,topology,tests}-baseline.log`。这些Root文件由其他任务修改，不在本片抢写或降低断言。
现在只授权P1b-I任务卡文件集；沿用现有干净codex分支/shared-checkout单writer模式，不另起重复实现worktree，Root独占index/commit。capability_owner负责失败测试、实现、文件清单与验证交付，后续规范/质量审查通过后Root重跑并提交。

P1b-D 设计提交：`7c9367e20de0bb1de8fc8b7b25c94a8b1b7c7ccd`；P1b-I 已续派 capability_owner，当前状态进行中。


### P1b 实现负责人交接

原 capability_owner 报告上下文耗尽，仅完成盘点，尚无文件写入；已结束并停写。Root确认子仓7c9367e工作树仍干净后，替换为新原生代理 capability_owner_p1b / gpt-5.6-sol / 独立精简上下文（fork none）。继承同一P1b-I任务卡与写入范围/验证/Root独占Git规则；旧负责人不再写入，不并行两个实现。此前接单不记实现进度或验收成果。


P1b-I 首个RED（capability_owner_p1b 实跑，主控尚未验收）：`PATH=/Users/nako/.nvm/versions/node/v24.13.0/bin:$PATH pnpm vitest run test/integration/nest-ingress.test.ts` exit1，1 failed suite，目标AppModule未创建导致import失败。现进入最小GREEN实现，旧行为基线仍为7c9367e之前主控162/162。Nest/Connect依赖已安装；供应链release-age精确例外须由实现负责人说明并经Root审查，尚未算通过。

### P1b-R1 第一轮审查（冻结未提交工作树）

- 规范审查 contract_review / gpt-5.6-sol：SPEC PASS；唯一Nest入口、同listener、HTTP/RPC协议/鉴权/surface/readiness/drain/telemetry及删除项均符合P1b范围。
- 质量审查 database_review / gpt-6-astra：QUALITY FAIL，4项P1生命周期阻断：deadline等待取消完成而失去期限；资源flags在连接失败/关闭pending阶段漏掉force cleanup；readiness ping超时永久disconnect导致不可恢复；socket close提前释放执行计数但handler可能继续写库。
- Root未接收首轮实现。capability_owner_p1b已按同一任务卡续接修复，要求取消挂起、坏Redis有界退出、quit挂起force、readiness恢复及client abort后等待业务handler settle的RED→GREEN测试。规范已通过，修复后仍由同一质量审查员复审，Root最后复验。


### P1b 最终交接与验收（2026-09-08）

- 任务/owner：P1b / kokoro-capability / capability_owner_p1b（gpt-5.6-sol）唯一实现 writer；Root 独占 Git index、提交与集成复验。实现负责人在冻结交付后停止写入。
- 设计基线：`7c9367e20de0bb1de8fc8b7b25c94a8b1b7c7ccd`；最终实现提交：`8606f876e8cce0c7affa346049f62910218793b0`（`refactor(capability): adopt native Nest composition`）。
- 结果：`src/main.ts`/`src/app.module.ts` 成为唯一 Nest 入口和组合根；Prisma、Redis、owner clients、readiness 与 shutdown 通过 DI/lifecycle 管理；原生 Nest health/projection 与官方 Connect Express 共享一个 raw-stream listener；删除旧 bootstrap、自建 HTTP/RPC router 和 Fastify 依赖，不保留双入口。
- 协议/安全：BFF Guard 与 RPC workload interceptor 分离，动态 attestation 绑定 operation/tenant/scopes；禁用 surface 不注册路由或实例化 owner client；Connect JSON/protobuf、1 MiB 限制、精确 path/method、request/trace id 与 stable error mapping 已回归。
- 生命周期：启动依赖未就绪不监听；shutdown 先拒绝新请求并等待 transport 与实际 handler 执行，再关闭 listener/资源；并发关闭共享 Promise。直接可执行入口在有界日志刷新后以 exit 1 终止残留 Prisma adapter I/O，import/library 路径只 reject、不擅自退出宿主。
- 独立规范审查：contract_review / gpt-5.6-sol，SPEC PASS，无 blocking/important。
- 独立质量审查：database_review / gpt-6-astra，前两轮分别指出 4 项 lifecycle 缺陷与 Prisma 活跃 query 退出缺口；实现负责人按 RED→GREEN 修复，第三轮 QUALITY PASS。真实 PostgreSQL 认证代理会观察 `SELECT 1` 后吞掉响应，并要求进程自然 exit 1，不以 SIGKILL 冒充。

Root 在最终提交 `8606f876e8cce0c7affa346049f62910218793b0`、Node 24.13.0/pnpm 11.25.0、真实 PostgreSQL/Redis 环境重跑：

| 命令 | 实际结果 |
|---|---|
| `pnpm install --frozen-lockfile` | 通过，lockfile 无漂移 |
| `pnpm format:check` / `pnpm lint` / `pnpm typecheck` | 全部 exit 0 |
| `pnpm prisma:validate` / `pnpm prisma:generate` / `pnpm schema:check` | 全部 exit 0，真实 schema 无 drift |
| `pnpm contract:check` | exit 0；digest 保持 `8650a846cef411f503398996d8a4340acd791b5bb8fb65b1071b74fc7e2aceca` |
| `REQUIRE_REAL_INTEGRATION=1 pnpm test` | 46 files / 192 tests passed，0 failed、0 skipped |
| `REQUIRE_REAL_INTEGRATION=1 pnpm test:integration` | 10 files / 67 tests passed；包含组件测试，不把全部项目称为外部集成 |
| `pnpm build` / `pnpm smoke:production` | exit 0；真实 PostgreSQL/Redis + 本地 owner 协议 stub；SIGINT/SIGTERM 与失败启动路径通过 |
| `git diff --check` / clean worktree | 通过 |

提交前冻结工作树日志：`/tmp/kokoro-p1b-root-final-20260908.log`；提交后绑定最终 SHA 的完整日志：`/tmp/kokoro-p1b-postcommit-8606f87.log`。日志是本机证据，不纳入仓库。

Root 最新全局门禁如实记录：`python3 scripts/verify-ten-repository-standard.py` exit 1（202 rule violations）；`python3 scripts/verify-repository-topology.py` exit 0；`python3 -m pytest scripts/tests` 为 82 passed / 2 failed，失败均为当前工程手册提取/引用格式断言。对应日志 `/tmp/kokoro-p1b-root-{standard,topology,tests}-final-20260908.log`。Capability 仍有 checker 对 ORM canonical、Prisma generated、strict dependency build、目标模块目录与 TypeScript 选项的真实缺口；P2/P3 会收敛业务目录，其余由相应治理切片处理，本片不放宽门禁。

Docker daemon `/info` 仍返回 HTTP 500，未执行镜像 build/smoke；外部 IAM/Storage/provider 仍是协议 stub，完整 owner sandbox 联调留后续。Goal 保持 active，下一切片为 P2 Skills；P3 MCP、P4 恢复、P5 Platform cutover 均未完成。

## P2 Skills 设计门与任务卡（2026-09-08）

Goal 继续保持 active。P2 先完成设计门，再依次实施 P2a 模块/状态/版本系列、P2b 安装机器契约/数据身份、P2c 事务/投影/旧实现删除；P2a 验收前不并行写 P2b/P2c。

### P2 放置表

| 项 | 已批准结论 |
|---|---|
| Owner | `kokoro-capability` 当前为唯一 writer；业务模块 `skills`。目标 P5 才把服务拓扑名切为 `kokoro-platform`，本片不复制 owner。 |
| 当前事实 | 基线 `8606f876e8cce0c7affa346049f62910218793b0`；Skills 仍分散在 `src/application/skill`、全局 models/ports、Prisma capability repository、聚合 RPC/HTTP，generic installation/authorization 尚未接入，catalog 仍有 `installed:true` 占位。 |
| 目标职责 | `SkillsModule` 先承接既有 catalog/source，再由 additive `SkillInstallationService` 提供 tenant/attested owner scope 下的安装、升级、启停、移除和查询；HTTP 保持 read-only projection。 |
| 目录方案 | 采用批准的 `src/modules/skills/{catalog,source,installation}` 按真实子能力聚合；淘汰继续扩展全局四层，因为会让 Skills/MCP 共享聚合类型和组合对象。暂不拆独立服务，避免提前做 P5 拓扑切换。 |
| 粒度 | 三个可审查业务切片：P2a 只迁现有 surface 并修状态/series；P2b 同片落 owner proto/generated/schema/repository；P2c 才接 projection、原子事务并删除孤立 helper。 |
| 依赖 | `SkillsModule` 可依赖 Prisma、Storage/IAM owner client 和共享 ingress/telemetry；禁止读取别仓数据库、把 Prisma/generated 类型穿透 wire、反向依赖 MCP、保留第二套安装实现或兼容 alias。AppModule 只 import feature；P3 才拆 MCP 聚合。 |
| 数据/API | `skill_id` 仍是版本 ID，新增内部 `series_id`；安装唯一身份为 tenant + target owner scope + skill series。Install 输入只含 source_ref/target scope，asset/digest 服务端派生并复验。P2b 先更新唯一 proto，P5 才切 BFF/Agent consumers。 |
| 删除项 | P2a 移除迁走后的旧 Skills service/repository/RPC/HTTP/global type/port；P2b 真实安装替换后删除 generic installation/authorization table/enum；P2c 删除孤立 installation/package/source-import helper 与只覆盖旧路径的 tests，不保留 fallback。 |
| 验证 | 每片先 RED，再执行 format/lint/typecheck/Prisma generate+validate/schema、contract、unit/integration/build/smoke、architecture 与 diff；schema/state/concurrency 使用隔离真实 PostgreSQL，复用现有 Redis。Root 最后执行当前三项全局门禁并如实保留既有失败。 |

### P2-D 设计通过报告

- 子仓设计提交：`83350ec2a4d89992ba89d17231af13e749ee4f0a`（`docs(capability): define Skills implementation slices`），基线 `8606f876e8cce0c7affa346049f62910218793b0`。
- 通过文件：`/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-capability/AGENTS.md`、`docs/ADR/ADR-001-nestjs-prisma.md`、`docs/API_CONTRACT.md`、`docs/CURRENT.md`、`docs/DATA_MODEL.md`、`docs/TECHNICAL_DESIGN.md`。
- 独立契约审查：contract_review / gpt-5.6-sol，P2-R2 `SPEC PASS`；安装输入信任边界、method-specific operation、统一 mutation response field/presence/enum、内部事件名、cursor 与 P2/P5 边界均一致。
- 独立数据审查：database_review / gpt-6-astra，P2-R2 `DATA PASS`；series/state/时间/no-op/降级、升级与 command drift、事务边界、removed tombstone/retention 均无剩余重要阻断。
- Root 在 docs-only 最终差异执行 `pnpm contract:check`、`pnpm prisma:validate`、`pnpm schema:check`、`pnpm test`、`git diff --check`，全部 exit 0；46 files：43 passed/3 skipped，192 tests：178 passed/14 skipped。跳过项是未提供真实集成环境的既有测试，因此该次只证明设计未破坏当前静态/组件基线，不替代实现验收。契约 digest 仍为 `8650a846cef411f503398996d8a4340acd791b5bb8fb65b1071b74fc7e2aceca`，日志 `/tmp/kokoro-p2-design-gate-r2-20260908.log`。
- 设计门已通过但 P2 实现尚不存在；CURRENT 明确保留旧路径、generic table 和 projection 占位现状。P4 的 public event/publisher/recovery/GC 与 P5 consumers/cutover 仍是后续 owner。

### P2 实施任务卡

| ID | 目标/完成条件 | Owner/角色/模型/权限 | 文件集与排除 | 依赖、验证与交付 |
|---|---|---|---|---|
| P2a-I | 建立原生 `SkillsModule`，迁移既有 catalog/source/RPC/HTTP projection/repository；增加 `series_id`、版本族和状态转换不变量；wire 行为不变 | capability_owner_p1b / gpt-5.6-sol / 子仓唯一 writer；Root 独占 Git | 可写 `src/modules/skills/**`、AppModule/必要共享 ingress 注册、迁出后的旧 Skills 路径、Prisma schema/generated/installer/drift、对应 test/docs/package script；不得改 proto/OpenAPI、installation schema/行为、MCP业务、其他仓 | 先写终态不可复活、非draft不可换包、同series owner/name、真实PG并发版本与状态竞争 RED；完成后停写交 Root/双审，Root 重跑完整本仓门禁并精确路径提交 |
| P2a-R | 对冻结 P2a 快照执行规范与数据/质量审查 | contract_review + database_review / 只读 | 只读 P2a diff/source/test/docs；不改文件、Git、共享资源 | SPEC/DATA 均 PASS 后 Root 才接收；任何 blocking/important 回同一 writer 整改 |
| P2b-I | 新增 `SkillInstallationService` 唯一 proto/generated/provenance/surface 与 `skill_installation` schema/repository；替换并删除 generic table/enum | P2a 验收后续派同仓唯一 writer | contract/proto+generated、Prisma schema/installer/drift、`src/modules/skills/installation/**`、对应 tests/docs；不改消费者仓/HTTP mutation/P4 publisher | 机器契约先 RED；覆盖 response presence/enum、operation互换拒绝、tenant/owner、unique/upgrade/reinstall/no-op/降级、fresh schema/drift与真实PG并发；独立双审+Root提交 |
| P2c-I | 接通真实 install/pool/catalog，删除 `installed:true` 与孤立 helper；本地 business/outbox/success receipt 原子提交 | P2b 验收后续派同仓唯一 writer | Skills transaction/projection/Storage client、旧 installation/package helper 删除、tests/docs；不做 P4 crash recovery/public event 或 P5 consumer alias | 覆盖 clean/digest、rollback/replay/event、catalog/pool、cursor scope/filter；完整本仓门禁、双审、Root提交 |

P2a 当前放行基线为 `83350ec2a4d89992ba89d17231af13e749ee4f0a`；沿用 `codex/production-closure-docs` shared checkout 和同一隔离资源纪律。Root/其他 Agent 在 writer 进行中不写该子仓；writer 不执行 Git add/commit/branch/reset，不扩大到 P2b/P2c。

### P2a 最终交接与验收（2026-09-08）

- 任务/owner：P2a-I / kokoro-capability / capability_owner_p1b（gpt-5.6-sol）唯一 writer；Root 独占 Git index、提交与集成复验。设计提交 `83350ec2a4d89992ba89d17231af13e749ee4f0a`，实现提交 `af9ac7bf611f2bbf1c49bf157a5acb7f55a02f34`（`refactor(capability): establish native Skills module`）。
- 结果：`SkillsModule` 原生承接 catalog/source、Skills RPC/HTTP projection、Prisma repository 与 Serializable transaction；旧 Skills service/repository、全局 Skill model/port 和重复 RPC/HTTP handler 已删除。根级非 global `RuntimeModule` 与 `AppModule`/`SkillsModule` 显式共享同一 dynamic module，Prisma/Redis/owner adapter 单次构造；Skills 只注入 package/attestation 窄 token，MCP legacy aggregate 留 P3。
- 数据与状态：`skill` 增加内部稳定 `series_id`、`created_at`、`updated_at` 与 `(tenant_id, series_id, revision)` 唯一约束；版本创建固定 series owner/display name，draft/validated package/publish/withdraw/enable/disable 在最终 transaction 内重读，withdrawn/quarantined 不复活。真实 PostgreSQL 并发创建得到 revision 2/3；固定 latch 分别验证 publish-first 拒绝后续换包、validate-first 发布新包的两种合法串行结果。
- 继承缺陷同片修复：HTTP catalog 的 limit/cursor 现在传入业务 `page`，真实 HTTP 连续两页无重复，identity/filter 变化拒绝旧 cursor；disabled 异常行缺 asset 或 digest 时不可重新激活，状态/updated_at 不变且不发 Storage 调用。
- 首轮审查：contract_review 指出 `src/config/runtime.module.ts` 越层和 Skills 反向依赖 `OWNER_ADAPTERS`；database_review 指出 flaky concurrency 断言、重新激活包完整性回归及继承的 HTTP pagination 缺陷。均由同一 writer 以 RED→GREEN 修复。最终 contract_review `FINAL SPEC PASS`、database_review `FINAL QUALITY PASS`，绑定 tracked diff `057f7fc927644a8167454798a9f9ff173109cb2efdcb9aafda6b7b6500a5c89a` 与同一 untracked 集合。

Root 使用 Node 24.13.0、pnpm 11.25.0、专属数据库 `kokoro_capability_p2a_20260908_root_r2` 和 Redis DB 6，在最终提交 `af9ac7bf611f2bbf1c49bf157a5acb7f55a02f34` 重跑：

| 命令 | 实际结果 |
|---|---|
| `pnpm install --frozen-lockfile`、fresh `pnpm db:apply-schema` | exit 0；未修改 lockfile；新库安装成功 |
| `pnpm format:check` / `pnpm lint` / `pnpm typecheck` | 全部 exit 0 |
| `pnpm prisma:validate` / `pnpm prisma:generate` / `pnpm schema:check` | 全部 exit 0；生成前后差异稳定，真实数据库 No difference detected |
| `pnpm contract:check` | exit 0；digest 保持 `8650a846cef411f503398996d8a4340acd791b5bb8fb65b1071b74fc7e2aceca` |
| `REQUIRE_REAL_INTEGRATION=1 pnpm test` | 49 files / 208 tests passed，0 failed、0 skipped |
| `REQUIRE_REAL_INTEGRATION=1 pnpm test:integration` | 11 files / 71 tests passed，0 failed、0 skipped |
| `pnpm build` / `pnpm smoke` / `pnpm smoke:production` | exit 0；smoke 2 files / 12 tests；真实 PostgreSQL/Redis + 本地 owner 协议 stub |
| `git diff --check` / clean worktree | 通过 |

提交前/后日志：`/tmp/kokoro-p2a-root-final-precommit-20260908.log`、`/tmp/kokoro-p2a-postcommit-af9ac7b.log`。日志为本机证据，不纳入仓库。

Root 当前全局门禁：standard exit 1（208 violations，其中 Capability 20；包括 checker 尚未识别 Prisma canonical/generated 与 feature 内 transport、以及 strict build/tsconfig/剩余旧目录等真实或治理缺口）；topology exit 0；Root tests 为 82 passed / 2 failed，仍是手册示例数量与“参考依据”标题断言。日志 `/tmp/kokoro-p2a-root-{standard,topology,tests}-final-20260908.log`，未通过放宽门禁或改其他 owner 清零。

Docker daemon 既有 `/info` HTTP 500，镜像 build/smoke 未验；production smoke 的 IAM/Storage/provider 为本地协议 stub。P2a 已验收，Goal 仍 active；现在仅放行 P2b-I，以 `af9ac7bf611f2bbf1c49bf157a5acb7f55a02f34` 为基线，P2c/P3/P4/P5 继续串行等待。

### P2b 最终交接与验收（2026-09-08）

- 任务/owner：P2b-I / kokoro-capability / capability_owner_p1b（gpt-5.6-sol）唯一实现 writer；Root 独占 Git index、提交与集成复验。实现基线 `af9ac7bf611f2bbf1c49bf157a5acb7f55a02f34`；最终提交 `119dbe36d2b44080d6be825ca84c98471e63467e`（`feat(capability): add Skill installation owner service`）。
- 结果：唯一 owner proto 新增 `SkillInstallationService` 五个 RPC 与统一 mutation response；`skill-installation` 作为独立 runtime surface 接入 Nest/Connect 同一 listener。Prisma canonical schema 新增真实 `skill_installation`，删除 generic `installation`、`capability_authorization` 及专属 enum/generated model；feature-owned repository 与 Serializable transaction 承接 tenant、target+series 唯一身份、初装/升级/重装/启停/移除/tombstone/no-op/降级状态机。
- 信任边界：Install 仅接收 source ref 与 target scope，服务从当前 tenant-scoped active source 派生 package identity，Storage 二次验证 clean/digest 后在事务内重读。三个 mutation 使用服务端重算的稳定业务 command digest；五方法 proof request binding 覆盖完整当次业务字段和 optional presence。receipt 命中前重验当前 proof/IAM/operation/binding/scope/resource/source 状态，返回缓存结果前再核对资源身份，字段替换、跨方法重放、撤权后 receipt 泄露均被回归拒绝。
- 并发与错误：Skill version 的 P2002 仅对 `uq_skill_series_revision` 做最多五次全事务重试；installation 同样只重试目标+series 唯一竞争，其他 P2002 立即抛出。typed application errors 固定映射鉴权、授权、不可见资源、前置条件与依赖失败；downgrade 为 `FAILED_PRECONDITION`。Buf 的统一 response 例外由仓内 policy checker 收窄到三个批准 mutation。
- 独立规范审查：contract_review / gpt-5.6-sol。R1/R2 分别发现 receipt 绕过当次授权、请求未真实绑定、source current-state 漏检与 auth code 错误；同一 writer 按 RED→GREEN 修复。R3 `SPEC PASS`，绑定提交前 tracked code diff `0dbfe2df73bcc9b0b124fe91d0dada70d568b51cb99e9a8de00b0e26d45da651`，无 blocking/important/minor。
- 独立数据/质量审查：database_review / gpt-6-astra。R1/R2 发现可恢复 P2002、降级错误码及跨 target/installation receipt 参数替换；R3 `QUALITY PASS`，同样绑定 `0dbfe2df…`，无 blocking/important。保留一个已记录 minor：非法 owner scope kind 在部分 legacy boundary 仍可能落 `INTERNAL`，后续 typed boundary 收口，不在本片扩大修改面。

Root 使用 Node 24.13.0、pnpm 11.25.0、专属 fresh PostgreSQL 数据库 `kokoro_capability_p2b_f2_20260908_root_post119dbe3` 与 Redis DB 8，在最终提交 `119dbe36d2b44080d6be825ca84c98471e63467e` 重跑：

| 命令 | 实际结果 |
|---|---|
| `pnpm install --frozen-lockfile`、fresh `pnpm db:apply-schema` | exit 0；lockfile 无漂移；全新库安装成功 |
| `pnpm format:check` / `pnpm lint` / `pnpm typecheck` | 全部 exit 0 |
| `pnpm prisma:validate` / `pnpm prisma:generate` / `pnpm schema:check` | 全部 exit 0；生成后工作树保持 clean；真实数据库无 drift |
| `pnpm contract:check` | exit 0；新 digest `6e0bbfc7974692b20f13ef9aac8440c50a6b1be2466e90a020b0e2cb5197fd8b` |
| `buf breaking` 相对 `af9ac7b` | exit 0；新增 proto 为 additive |
| `REQUIRE_REAL_INTEGRATION=1 pnpm test` | 55 files / 266 tests passed，0 failed、0 skipped |
| `REQUIRE_REAL_INTEGRATION=1 pnpm test:integration` | 12 files / 77 tests passed，0 failed、0 skipped |
| `pnpm build` / `pnpm smoke` / `pnpm smoke:production` | exit 0；smoke 2 files / 13 tests；真实 PostgreSQL/Redis + 本地 owner 协议 stub |
| `git diff --check` / clean worktree | 通过 |

提交前日志：`/tmp/kokoro-p2b-f2-root-precommit-20260908.log`；提交后绑定最终 SHA 的日志：`/tmp/kokoro-p2b-postcommit-119dbe3-20260908.log`。日志为本机证据，不纳入仓库。

Root 最新全局门禁如实记录：`python3 scripts/verify-ten-repository-standard.py` exit 1（212 violations，其中 Capability 20）；`python3 scripts/verify-repository-topology.py` exit 0；`python3 -m pytest scripts/tests` 为 82 passed / 2 failed，仍是手册示例数量与“参考依据”标题断言。对应日志 `/tmp/kokoro-p2b-root-{standard,topology,tests}-final-20260908.log`。未通过修改其他 owner、当前 SQL 手册脏文件或放宽门禁清零。

P2b 的 installation + outbox 已在本地业务事务内原子提交，但 success receipt 仍由 outer wrapper 在事务外完成；崩溃窗口、stale processing receipt 与恢复保持真实缺口。Docker 镜像及真实 IAM/Storage owner sandbox 联调未验。Goal 保持 active。

### P2c-I 放行（2026-09-08）

P2c 现在以 `119dbe36d2b44080d6be825ca84c98471e63467e` 为唯一实现基线，续派同一 capability_owner_p1b 作为子仓唯一 writer；Root 继续独占 Git。允许修改 Skills transaction/projection、Storage client、receipt repository/transaction contract、旧 `src/application/installation` 与 package/source-import helper、对应 tests/docs/必要 schema/generated；禁止改 P3 MCP 业务、P4 publisher/reaper/retention、P5 消费者仓/服务名/alias、其他仓和 Root 文件。

完成条件：

1. catalog/pool 的 installed projection 从可信 BFF subject 对应唯一 user target 下的真实 `skill_installation` 查询导出，删除 `installed:true` 占位；cursor、tenant、owner scope 与现有只读 HTTP/Connect contract 保持。
2. 三个安装 mutation 的本地业务变化、outbox 和 completed success receipt 使用同一 PostgreSQL transaction；same-command replay 返回首次结果，digest/operation drift 保持冲突。failed/processing 的跨崩溃恢复、lease/reaper、publisher 和 retention 仍留 P4，不以本片原子 success path 冒充完整恢复。
3. 删除已被真实 owner flow 替代且没有生产入口的孤立 installation/package/source-import helper、测试与 import；不保留 fallback、alias 或双轨实现。Storage package clean/digest 边界继续保留。
4. 先写 projection/rollback/receipt crash-window RED，再最小实现；真实 PostgreSQL 覆盖业务/outbox/receipt 同事务回滚、并发 replay、catalog/pool target scope 与 cursor 隔离。完成后冻结工作树，独立规范/数据质量双审、Root fresh schema 与完整本仓门禁通过后方可提交。

### P2c 最终交接与验收（2026-09-08）

- 任务/owner：P2c-I / kokoro-capability / capability_owner_p1b（gpt-5.6-sol）唯一 writer；Root 独占 Git index、提交与集成复验。实现基线 `119dbe36d2b44080d6be825ca84c98471e63467e`；最终提交 `e63b56518b51dbf1ad1c172f709b19231b4bfaa3`（`feat(capability): complete Skills installation projection`）。
- 结果：`/v1/skills` 保持 active source 行为；catalog 按可信 BFF subject 对应的 exact-version user-target installation 派生 installed/enabled，pool 使用 Prisma relation predicate 在 keyset/`limit + 1` 前过滤。Prisma 的 relation include 两次读取被显式包含在 RepeatableRead snapshot，避免并发 disable/remove 导致资格与返回 flags 不一致；optional subject 的既有 tenant fallback 保持。
- 事务与重放：三个 installation mutation 在事务外完成当前 IAM/Storage 校验与 receipt claim，claim winner 在一个 Serializable transaction 中重读 receipt/source/installation，并原子提交业务、0/1 outbox、wire codec result 与 completed receipt。business/outbox/codec/completion 四个故障点均回滚本地事实；processing/corrupt completed fail closed，同 command 与 failed reclaim 并发只产生一个 durable transition/event。通用 receipt action 已成功后的 codec/completion 故障保持 processing，阻止原业务被自动重做。
- 删除：孤立 `src/application/installation/service/*`、ZIP/package/source-import 与旧 Storage 多用途 adapter 已删除；真实使用的 bounded `ConnectStoragePackageClient` 迁入 `src/modules/skills`，继续校验 clean、asset/digest、deadline 与受控 read URL。Prisma 只增加 `relationMode=prisma` 逻辑 relation，fresh schema 物理外键数为 0。
- 独立审查：contract_review 最终 `SPEC PASS`，无 blocking/important/minor；database_review 首轮发现通用 receipt 重执窗口、projection 非一致快照及内存替身先分页后三项问题，同一 writer 以 RED→GREEN 修复，复审 `QUALITY PASS`，无新增阻断。

Root 在最终提交 `e63b56518b51dbf1ad1c172f709b19231b4bfaa3`、Node 24.13.0、pnpm 11.25.0、独立 fresh PostgreSQL 数据库 `kokoro_capability_p2c_post_e63b565_20260908` 与 Redis DB 10 重跑：

| 命令 | 实际结果 |
|---|---|
| `pnpm install --frozen-lockfile`、fresh `pnpm db:apply-schema` | exit 0；lockfile 无漂移；全新库安装成功 |
| `pnpm format:check` / `pnpm lint` / `pnpm typecheck` | 全部 exit 0 |
| `pnpm prisma:validate` / `pnpm prisma:generate` / `pnpm schema:check` | 全部 exit 0；生成后工作树 clean；真实数据库无 drift、物理外键数 0 |
| `pnpm contract:check` / `buf breaking` 相对 `119dbe3` | exit 0；digest 保持 `6e0bbfc7974692b20f13ef9aac8440c50a6b1be2466e90a020b0e2cb5197fd8b`，无 wire breaking |
| `REQUIRE_REAL_INTEGRATION=1 pnpm test` | 53 files / 275 tests passed，0 failed、0 skipped |
| `REQUIRE_REAL_INTEGRATION=1 pnpm test:integration` | 13 files / 87 tests passed，0 failed、0 skipped |
| `pnpm build` / `pnpm smoke` / `pnpm smoke:production` | exit 0；smoke 2 files / 13 tests；真实 PostgreSQL/Redis + 本地 owner 协议 stub |
| `git diff --check` / clean worktree | 通过 |

提交后完整日志：`/tmp/kokoro-p2c-root-postcommit-e63b565-20260908.log`。Root 最新全局门禁：standard exit 1（212 violations，其中 Capability 20）；topology exit 0；Root tests 为 82 passed / 2 failed，仍是工程手册示例数量与“参考依据”标题断言。日志 `/tmp/kokoro-p2c-root-global-20260908-{standard,topology,tests}.log`。未通过修改其他 owner、当前 SQL 手册脏文件或放宽门禁清零。

Docker 镜像及真实 IAM/Storage owner sandbox 联调仍未验；P4 processing lease/fencing/reaper、publisher/retention 仍是真实缺口。Goal 保持 active。现在只放行 P3-D：以 `e63b56518b51dbf1ad1c172f709b19231b4bfaa3` 为唯一基线，先审计 MCP 当前 owner/API/schema/state/transaction/删除面并收敛 TECHNICAL_DESIGN、API_CONTRACT、DATA_MODEL 与本任务板；P3 实现、P4、P5 尚未授权写入。
