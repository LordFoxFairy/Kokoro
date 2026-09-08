# Capability → Platform：NestJS + Prisma 实施任务板

状态：P0、P1a 已验收；P1b–P5 待推进。用户已批准总体方案并授权推进（2026-09-07）。本任务板是本轮唯一推进记录。

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
| P1 / P0 | 原生 Nest/Prisma 底座及现有持久化行为切换，单一生产路径、生成 Client、fresh schema 与真实启动验证 | capability-owner / gpt-5.6-sol / 写入，需 Root 放行 | 子仓 src、prisma、prisma.config.ts、package/lock/tsconfig、构建配置、scripts、test、必要 docs；不改机器 wire contract/其他仓 | P0-R 通过；实现和只读审查分离 | P1a 已验收（d32631f），P1b-I 进行中（7c9367e设计基线） |
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
- [x] P1a：先新增并运行失败测试：Prisma 唯一 schema、无业务 pg SQL、tenant/并发/分页/事务基线。
- [x] P1a 值域 gate：逐项验证 owner_kind、skill/connector/server/connection/authorization/installation/receipt/outbox status、connector type、transport、capability kind、effect 的生成 PostgreSQL enum，非法值在数据库写入时被拒绝；旧 CHECK 语义不丢失。
- [ ] P1b：先新增并运行 Nest 生命周期、HTTP/Connect raw-body/auth/route 失败测试。
- [x] 建立生成 Client 与 ORM schema；无外键生成结果实测，不保留两份可编辑 schema。
- [ ] P1b：Nest 管理进程与资源；Connect 保持官方协议 adapter，不另开平行服务，不自动假设 Nest Guard 覆盖 Connect 请求。
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

### 未完成、风险与后续 owner

1. P1b：capability-owner 续接 Nest 原生 DI/生命周期/HTTP/Connect 单 listener；Root 先刷新工作树与任务卡，再授权写入。P2 Skills、P3 MCP、P4 receipt/outbox 崩溃恢复和 retention、P5 Platform cutover 仍待实施。
2. 当前 receipt 完成写与业务提交未合并为一个事务，外部副作用的崩溃恢复没有闭环；留 P4，未以本轮 Prisma 替换冒称解决。
3. Root standard 最新实跑 exit 1：214 violations，其中 Capability 16；记录 `/tmp/kokoro-p1a-root-standard-20260907.json`。Root 后续独立切片修正 checker 对 ORM canonical 与只读生成物的识别（repository_checks 仍强制 SQL schema，typescript_checks 扫描 Prisma generated），同时继续保留真实目录/工具链缺口的失败门禁；不以放宽规则清零。
4. Docker daemon `/info` HTTP 500，镜像 build/smoke 未运行；官方 Node 镜像 digest 已实查并固定。完整跨仓 `./scripts/verify-ten-repository-full.sh` 未运行：其他 owner 正在修改，缺少稳定联合验收面及可用 Docker。Root 负责后续协调，不干扰其他任务进程。
5. 下一阶段需完成真实 IAM/Storage 等 owner sandbox 联调；本轮 smoke 的协议 stub 只证明本仓装配行为。

状态：P1a 已验收；总体计划未完成。后续 owner：Root（边界/派工/主仓门禁/最终验收），capability-owner（按下一任务卡续接 P1b）。

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
