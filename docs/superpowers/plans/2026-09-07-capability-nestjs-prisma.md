# Capability → Platform：NestJS + Prisma 实施任务板

状态：P0、P1a、P1b、P2a、P2b、P2c、P3-D、P3a、P3b、P4-D 已验收；P4a receipt 原子性/fencing 实施卡已通过双审并由同一 child writer 推进，P4b–P4e 与 P5 待依赖顺序续派。用户已批准总体方案并授权推进（2026-09-07），并再次强调 Skills/MCP typed identity、Manus 设计与 NestJS + Prisma 唯一技术路线（2026-09-10）。本任务板是本轮唯一推进记录。

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
| P3 / P0 | MCP connector/server/connection/authorization 模块闭环 | capability-owner / gpt-5.6-sol / 分片授权 | MCP 源码/测试/必要契约文档 | P2；不实现 Agent runtime | P3-D、P3a、P3b 已验收 |
| P4 / P0 | receipt/outbox 崩溃恢复、有限重试、retention 和可观测性 | capability-owner / gpt-5.6-sol / 分片授权 | 本仓实际用例涉及文件，实施前细化 | P2/P3 | 仅 P4-D 设计门已放行；实现未授权 |
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

## P3 MCP 设计门与任务卡（2026-09-08）

P3-D 使用三个并行只读角色审计同一 clean baseline：capability_owner_p1b 负责实现/import/删除面，contract_review 负责 wire/identity/replay，database_review 负责schema/transaction/concurrency；Root裁决并写现有设计文档与本任务板。三方一致确认：当前是5个MCP Connect service/17个method/1个HTTP projection，不是历史清单的7个service；tenant mutation无actor proof、caller digest可伪造、tool receipt重放越权、complete/revoke竞态、UUID“最新授权”、随机grant/audit和无界declaration必须在P3收口。源码写入在设计双审通过前保持未授权。

### P3 放置表

| 项       | 已裁决结论                                                                                                                                                                                                                                           |
| -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Owner    | `kokoro-capability` 当前唯一writer，业务模块`mcp`；secret/provider、IAM、Agent runtime事实继续由各owner持有，P5才切`kokoro-platform`物理拓扑。                                                                                                       |
| 当前事实 | 基线`e63b56518b51dbf1ad1c172f709b19231b4bfaa3`；`CapabilityServices/Context`、`application/mcp`、legacy RPC factory、`PrismaMcpRepository`/state forwarding store承接唯一现行实现；四张MCP表，server global，其余tenant-owned。                      |
| 目标职责 | `src/modules/mcp/{provider,connector,server,connection,authorization}`原生Nest feature，逐方法attestation/binding/digest/typed errors，current authorization状态、声明policy和短期tool decision。                                                    |
| 目录方案 | 采用已批准`src/modules/mcp`而非继续扩展全局四层；不提前拆进程/切服务名，也不先提交只搬目录且保留安全缺口的中间态。                                                                                                                                   |
| 粒度     | P3a关闭provider/connector/consent及其additive wire/schema、拆除HTTP projection wide bag依赖与统一client lifecycle；P3b迁server/connection/declaration/tool authorization并把已用窄reader的HTTP controller物理归位。RPC始终单handler，无alias/双写。 |
| 依赖     | feature-owned Prisma repository/transaction与IAM/provider/secret/declaration窄token；保留共享receipt/outbox/pagination/bounded HTTP/drain。禁止`OWNER_ADAPTERS`宽bag、Skills反向依赖、别仓DB和provider SDK泄漏。                                     |
| 数据/API | 七mutation additive attestation；17方法exact operation+full request binding；stable command digest服务端重算。Connector explicit pending/active auth pointer、authorization account/times、connector/connection revoke event/time；不新增通用表/FK。 |
| 删除     | P3a删除`CapabilityServices`、`CapabilityContext`、`OWNER_ADAPTERS/createRuntimeAdapters`、全局MCP models/ports与state转发并移除无用connector secret字段；P3b删除feature内remainder、旧server/connection/tool service、legacy RPC factory与`PrismaMcpRepository`旧名。 |
| 验证     | 每片TDD、contract/provenance/Buf breaking、format/lint/typecheck/build、architecture、真实PG并发/事务/分页、真实HTTP JSON+protobuf/HTTP projection、smoke/production smoke；Root最后重跑全局三门。                                                   |

### P3 安全/状态裁决

1. 所有MCP请求使用API_CONTRACT第11节逐方法operation与canonical request binding；七个mutation在CommandIdentity外添加proof。Global register只接受IAM exact`mcp.admin.register_server`，tenant owner scope不构成admin。
2. Receipt lookup前重验当次proof/IAM/current owner/resource/policy并重算command digest。Tool replay从response `audit_ref`按tenant读取同事务outbox，核对event/aggregate及原始run/session/resource/tool/connection/declaration/arguments/approval digest后再对照current state；cached expiry不续期。
3. Connector以pending/active authorization pointer取代UUID排序；reauthorization切换account/scopes同transaction，complete外部返回后最终重读，revoke先提交不得复活。Complete request handle进入proof/digest、经SecretStore验证后持久化且同authorization不可更换，provider response不产生handle，cleanup只用stored request handle。No-consent provider直接生成approved metadata并active。
4. Server保持global；当前HTTP-only declaration driver拒绝不可发现的stdio；HTTP origin显式allowlist/no redirect。Declaration页/item/connection/concurrency有界且全连接selector冲突fail closed；required scopes来自本地provider catalog的versioned provider/server/selector policy与canonical digest，`defaultScopes`只供consent，缺失/非法配置阻止readiness，缺rule/digest漂移fail closed。
5. Connection policy用canonical JSON数组digest，保存首次revocation event。Tool grant是authenticated Connect上的短期run/session-bound opaque decision ID，不是Platform bearer token；verified run/session参与服务端receipt identity/digest/replay/audit，跨execution复用key不能命中旧决定；真实audit_ref为同transaction内部outbox event。Agent invoke/P5与publisher/recovery/P4边界不混入。
6. Pending自然到期是transaction内使用时谓词；唯一feature-owned transaction clock通过Prisma执行固定无参数`clock_timestamp()`，每次P2034 retry重读，architecture gate禁止扩大raw。Connector revoke清pending、把active auth标记revoked并保留pointer/account为永不授权的tombstone。Complete provider success后的本地business/pointer/account/outbox/codec/receipt同transaction，P2034不重复provider；并发输家若same active+相容结果只完成receipt，不重复outbox；漂移使connector fail closed且绝不cleanup current。其他quarantine必须先证明authorization未被active引用，commit未知保持processing并留P4恢复。
7. P3a即由`McpModule`拥有全部MCP共享model/repository/narrow token并删除`CapabilityServices/Context`与`OWNER_ADAPTERS/createRuntimeAdapters`；现有MCP HTTP controller改注入feature-owned reader，P3b才物理归位。Skills/MCP分别单实例构造窄client并向共享registry登记，RuntimeResources在全部登记后探测，partial-startup/正常关闭均逆序close feature后再关Redis/Prisma；未迁十方法只有feature内单一`legacy/mcp-remainder`，P3b删除。
8. 17方法使用同一个lowerCamelCase/presence/enum/bytes/page canonical helper和逐方法business object，contract fixture固定expected digest。P3a只验收provider/connector七方法，剩余十方法旧鉴权缺口明确保留到P3b，不能提前宣称完成。
9. No-consent provider只允许空default/requested/required scope，用tenant+owner+provider+type稳定hash主键并保持account NULL，不构造provider/secret client；provider port是同authorization ID的at-least-once幂等契约，不宣称exactly-once。
10. 按Manus v2已复核原则，task先从list获得opaque typed ID：Kokoro Skill明确series/revision/source/installation，MCP明确provider/connector/server/connection/grant；任务只持已安装/启用pool返回的Skill source reference与active connector reference，installation ID只用于管理，不用display/provider key/URL/selector代替。

### P3 实施任务卡（设计复审通过后才改变状态）

| ID    | 目标/完成条件                                                                                                                                  | Owner/角色/模型/权限                                             | 文件集与排除                                                                                                                                                                                                                                     | 依赖、RED与交付                                                                                                                          |
| ----- | ---------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------- |
| P3-D  | 三审计+Root收敛TECHNICAL_DESIGN/API_CONTRACT/DATA_MODEL/ADR/CURRENT/SECURITY/RESOURCE_NAMING、Root Manus对齐页和本任务板，独立复审通过                                           | Root写文档；contract_review+database_review只读                  | 仅上述现有文档；不改proto/schema/src/generated                                                                                                                                                                                                   | 已验收；child commit `aa56cbf4623cead8810489bc2fdaabff04867ec3`，SPEC/DATA/EXECUTABLE均PASS，现放行P3a                                                        |
| P3a-I | 原生McpModule的provider/connector/consent；connector mutation additive proof、binding/digest/typed errors；current auth schema/事务/撤销闭环   | capability_owner_p1b / gpt-5.6-sol / 子仓唯一writer；Root独占Git | `src/modules/mcp/{provider,connector,authorization,legacy}`、全部MCP shared model/repository/token/transaction clock、对应legacy删除、`src/http/projection.controller.ts`窄reader接线、main/Runtime/App/RPC/readiness registry与Skills窄client provider/token必要接线、`owner-adapters.provider.ts`/wide token删除、connector proto/generated/provenance、Prisma MCP字段/generated/installer/drift、facades/tests/docs/config/format清单；不得改P3b业务语义、P4/P5/其他仓 | 已验收；child commit `4c363e24e1ba0e42a8db2a2a46016c65304282c8`；SPEC/QUALITY PASS；Root fresh schema/full real gates PASS |
| P3b-I | 迁server/connection/declaration/tool authorization并物理归位HTTP；admin proof/network预算/trusted scope/current replay/audit；删除全部legacy aggregate | capability_owner_p1b / gpt-5.6-sol / 子仓唯一writer；Root独占Git | `src/modules/mcp/{server,connection,authorization}`、已改窄reader的MCP HTTP controller物理迁移、剩余RPC/adapter/repository、server/connection proto/generated、connection revoke schema、facades/tests/docs/config/format清单与`legacy/mcp-remainder`删除；不得改Agent invoke/public event publisher/P5消费者 | 已验收；child commit `0f7dc1a95c84760612e4a96023f42149fe84cd0c`；SPEC/QUALITY PASS；Root fresh schema/full real/post-commit gates PASS |
| P3-R  | 每片先规范审查、再数据/代码质量审查，所有blocking/important回原writerRED→GREEN                                                                 | contract_review + database_review / 只读                         | 冻结diff/commit与tests；不改文件/Git/服务/共享数据                                                                                                                                                                                               | 两审PASS且Root复验后才验收；P3b后确认legacy删除与单一DI实例                                                                              |

### P3-D 验收证据（2026-09-09）

设计冻结基线为child HEAD `e63b56518b51dbf1ad1c172f709b19231b4bfaa3`、七文档diff `0784865dbb50963d2455d290e48652ed2237cca89edfbc882d030f1a9f105e80`及Root HEAD `baba9cea59023a9afaf4a8213f456ff27db132fe`、Manus对齐页+任务板diff `c280350c99978d9d8ce229955c384d2ecf3b9c05d41da56187793175197647be`。`contract_review`、`database_review`、`capability_owner_p1b`分别给出SPEC PASS、DATA PASS、EXECUTABLE PASS，均为0 blocking/important/minor并在审前审后复核hash未漂移。Child按精确七路径提交`aa56cbf4623cead8810489bc2fdaabff04867ec3`；没有改proto/schema/src/generated。

Root在Node 24.20.0、pnpm 11.25.0实跑`format:check`、lint、typecheck、contract check、Prisma validate、build均exit 0；普通`pnpm test`为47 files passed/6 skipped、244 tests passed/31 skipped，skip是未设置真实integration环境，不冒充P3实现或真实PostgreSQL故障注入。日志为`/tmp/kokoro-p3d-r3-doc-gates-20260909.log`与`/tmp/kokoro-p3d-r3-static-gates-20260909.log`。P3a现为唯一授权实现片；P3b继续等待P3a验收，P4 lease/fencing/reaper、provider cleanup重投、publisher/dead-letter/retention和P5 consumers/service/schema namespace cutover继续串行等待。

### P3a 最终交接与验收（2026-09-10）

- 任务/owner：P3a / `kokoro-capability` / capability_owner_p1b（gpt-5.6-sol）唯一实现 writer；Root 独占 Git index、提交与集成复验。设计基线 `aa56cbf4623cead8810489bc2fdaabff04867ec3`，最终实现提交 `4c363e24e1ba0e42a8db2a2a46016c65304282c8`（`feat(capability): migrate MCP connector control plane`）。
- 结果：原生 `McpModule` 承接 provider/connector/consent 七个 RPC 方法、Prisma repository 与 Serializable transaction；删除 wide `CapabilityServices/Context`、`OWNER_ADAPTERS/createRuntimeAdapters`、旧 connector/provider service 及 state forwarding store。未迁移的十方法只保留一个 feature-owned `legacy/mcp-remainder`，不冒充 P3b 完成。
- 标识：Skill 继续区分 `series_id`、不可变 `skill_id` revision、task `source_ref` 与安装生命周期 `installation_id`；MCP 继续区分 provider/connector/server/connection/grant。No-consent connector 使用五字段 canonical `{tenantId,ownerKind,ownerId,providerKey,connectorType}` 派生 `mcp-nc:<digest>`，authorization 再从 connector identity 派生 `mcp-nca:<digest>`；不用 provider key、URL、selector 或 installation ID 替代 task resource ID。
- 安全/一致性：四个 mutation 的 proof/operation/binding/digest 为 additive wire；Begin/Complete receipt replay 重验当前 owner/connector/authorization 与 cached-result binding；provider 成功后的本地故障通过 transaction 内 quarantine 处理，cleanup 仅在证明同 tenant/provider 无 active current 共享 stored handle 后写入，外部 revoke 在 commit 后执行。该查询最终使用固定 100 行 keyset 批次、bounded `IN` 与 Map/Set 线性关联，异常 fail closed。
- 独立审查：contract_review 最终 `SPEC PASS`，database_review 最终 `QUALITY PASS`，均无 blocking/important/minor；审查绑定 HEAD `aa56cbf...`、tracked diff `8541e9ae842c0973404f1a4733a6c8dfba1d5fc58a3a702ec057218eb9878845`、untracked aggregate `7f3dad10711d715c5ede9a84ea667bb3265dd7e177e03ac1f71c50eacffcb851`，审前审后未漂移。

Root 在最终提交 `4c363e24e1ba0e42a8db2a2a46016c65304282c8`、Node 24.13.0、pnpm 11.25.0、PostgreSQL 18.4 的独立 fresh database 和既有 Redis 的空 DB 14 上重跑：

| 命令 | 实际结果 |
|---|---|
| `pnpm install --frozen-lockfile`、`pnpm db:apply-schema` | exit 0；仅创建/删除本任务 fresh database |
| `pnpm format:check`、`pnpm lint`、`pnpm typecheck` | 全部 exit 0 |
| `pnpm prisma:validate`、`pnpm prisma:generate`、`pnpm schema:check` | 全部 exit 0；public 物理外键 0 |
| `pnpm contract:check` + 相对 `aa56cbf...` 的 `buf breaking` | exit 0；contract digest `642e1c29248fadc8407dd4098b19db1ce03c41d9b97577261fa793c7c1ce5f16` |
| `pnpm build` | exit 0 |
| `REQUIRE_REAL_INTEGRATION=1 pnpm test` | 57 files / 352 tests passed，0 failed、0 skipped |
| `REQUIRE_REAL_INTEGRATION=1 pnpm test:integration` | 14 files / 106 tests passed，0 failed、0 skipped |
| `REQUIRE_REAL_INTEGRATION=1 pnpm smoke` | 2 files / 14 tests passed，0 failed、0 skipped |
| `pnpm smoke:production` | pass；真实 PostgreSQL/Redis + 本地 Storage/IAM/Secret/MCP provider 协议 stub |
| `git diff --check` / clean child worktree | 通过 |

提交后完整日志为 `/tmp/kokoro-p3a-root-postcommit-4c363e2-20260910.log`，真实 smoke 补充日志为 `/tmp/kokoro-p3a-root-real-smoke-20260910.log`；日志是本机证据，不纳入仓库。Docker 镜像与真实外部 owner sandbox 联调未验，不冒充生产级全链路通过。P4 的 processing lease/fencing/reaper、provider cleanup 重投、publisher/dead-letter/retention 和 P5 cutover 继续待后续分片。

Root 全局三门同步实跑：`verify-repository-topology.py` exit 0；`verify-ten-repository-standard.py` exit 1，当前全拓扑 222 项违规，其中 Capability 23 项，包含 checker 尚未承认已批准 ORM-first canonical/generated 边界、P3b 尚存 remainder/RPC/facade 粒度及 TypeScript 配置的真实后续项；`python3 -m pytest scripts/tests` 为 82 passed / 2 failed，失败仍是当前手册示例数 11 与旧断言 18、以及旧固定标题“参考依据”与新手册不一致。日志为 `/tmp/kokoro-p3a-root-standard-20260910.log`、`/tmp/kokoro-p3a-root-topology-20260910.log`、`/tmp/kokoro-p3a-root-script-tests-20260910.log`。本片不修改或放宽 Root 治理门禁，也不暂存 SQL 手册、`kokoro-agent` 或 `.tmp/` 的其他任务变更。

P3a 已验收后放行的 P3b-I 现亦已完成；以下验收记录取代本段原“P3b 待实施”状态。

### P3b 最终交接与验收（2026-09-10）

- 任务/owner：P3b / `kokoro-capability` / capability_owner_p1b（gpt-5.6-sol）唯一实现 writer；Root 独占 Git index、提交和集成复验。实现基线 `4c363e24e1ba0e42a8db2a2a46016c65304282c8`，最终 child 提交 `0f7dc1a95c84760612e4a96023f42149fe84cd0c`（`feat(capability): complete MCP control plane`）。
- 结果：原生 `McpModule` 承接 server/connection/declaration/tool authorization 剩余十个 RPC，17 个 MCP method 仍由单一 Connect handler/DI 方向注册。HTTP projection 物理归位 feature；`legacy/mcp-remainder`、旧 repository/reader/controller 和 wide facade 实现已删除或按变化原因拆分，不保留 alias、fallback 或双轨路径。
- 标识与 Manus 对齐：Skill 仍区分 `series_id`、不可变 revision `skill_id`、task `source_ref` 和管理用 `installation_id`；MCP 仍区分 `connector_id`、`server_id`、`connection_id`、`grant_id`。provider key、URL、selector 和 tool name 不冒充资源 ID。Tool grant 是 run/session-bound opaque UUIDv4 decision ID，由 receipt 稳定重放，audit 用 digest 绑定原始决定并不保存 raw approval reference。
- 安全/一致性：register 需 exact admin operation；wire URL proof 与 normalized stable identity 分离。HTTP-only declaration 使用 DNS pinning、Host/SNI、no redirect 和 global-address fail-closed；单 RPC 共享 10s deadline、2,000 raw-item 和 4-worker 预算，单 connection 仍限 100 页/单调用 3s。取消覆盖锁等待、IAM、DNS/HTTP、Serializable transaction/retry、receipt completion 和最终校验；可明确回滚窗口不提交，已发送 COMMIT 继续保持 unknown-outcome 语义。
- 预算/并发：32 connection 边界保留 same-identity replay/convergence，新建及 policy mismatch 在最终事务内按 typed error 失败。Provider policy 在规范化、排序后一次预编译完整 digest 与 selector index；declaration 用批量 server 读取和请求级 raw 预算，没有 N+1 或 tool×rule 重复全量编译。
- 独立审查：首轮 SPEC/QUALITY FAIL 及 R2/R3 对抗审查均回原 writer 按 RED→GREEN 修复。最终 contract_review `SPEC PASS`、database_review `QUALITY PASS`，共同绑定提交前 HEAD `4c363e24...`、tracked diff `73d4da7fee1fdd8aec8f2c766a6d2f6a2e779bb8e960bbcc4617f4db0114c70a`、untracked aggregate `9ae56f0e79a48aeb33f258205f911f563a2c6e83deb6deb5b45d86beba624d4f`，审前审后未漂移。

Root 在最终提交 `0f7dc1a95c84760612e4a96023f42149fe84cd0c`、Node 24.13.0、pnpm 11.25.0、PostgreSQL 18.4 独立 fresh database 和既有 Redis 空 DB 14 上提交前/提交后都完成全套复验；提交后结果为：

| 命令 | 实际结果 |
|---|---|
| `pnpm install --frozen-lockfile`、`pnpm db:apply-schema` | exit 0；仅创建/删除本任务 fresh database；Redis DB 14 前后均为 0 |
| `pnpm format:check`、`pnpm lint`、`pnpm typecheck` | 全部 exit 0 |
| `pnpm prisma:validate`、`pnpm prisma:generate`、`pnpm schema:check` | 全部 exit 0；public 物理外键 0 |
| `pnpm contract:check` + 相对 `4c363e24...` 的 `buf breaking` | exit 0；contract digest `6eb170d12bd046aa70b2a1b8aa775c6303e46ffc997cb4193f77fc230072d3b5` |
| `pnpm build` | exit 0 |
| `REQUIRE_REAL_INTEGRATION=1 pnpm test` | 60 files / 442 tests passed，0 failed、0 skipped |
| `REQUIRE_REAL_INTEGRATION=1 pnpm test:integration` | 15 files / 113 tests passed，0 failed、0 skipped |
| `REQUIRE_REAL_INTEGRATION=1 pnpm smoke` | 2 files / 14 tests passed，0 failed、0 skipped |
| `pnpm smoke:production` | pass；真实 PostgreSQL/Redis + 本地 Storage/IAM/Secret/MCP provider 协议 stub |
| `git diff --check` / clean child worktree | 通过 |

提交后完整日志为 `/tmp/kokoro-p3b-root-postcommit-0f7dc1a-20260910.log`；日志是本机证据，不纳入仓库。Docker 镜像、真实外部 owner/provider sandbox 仍未验；P4 的 processing lease/fencing/reaper、provider cleanup 重投、publisher/dead-letter/retention 和 P5 cutover 仍是真实待办。

### P4-D 设计门授权（2026-09-10）

P3b 已验收，现仅授权 P4-D：相对 child 提交 `0f7dc1a95c84760612e4a96023f42149fe84cd0c` 盘点 Skills/MCP 的 command receipt、outbox、provider cleanup 与关闭生命周期，收敛 processing lease/fencing/reaper、有限重试/jitter、dead-letter、retention、外部副作用恢复和可观测语义。P4-D 只允许审计并更新现有 `TECHNICAL_DESIGN`、`API_CONTRACT`、`DATA_MODEL`、`RELIABILITY`、`RUNBOOK`、`SECURITY`、`CURRENT` 及本任务板；不改 proto/schema/generated/src/test，不写 P5 消费者仓，不启动 P4 实现。三设计面、状态机、事务/失败恢复和验收矩阵通过独立复审后，Root 才拆 P4 实现任务卡。Goal 保持 active。

Root 在 P3b 验收记录提交 `fe63c14e` 后同步实跑全局三门：`verify-repository-topology.py` exit 0；`verify-ten-repository-standard.py` exit 1，共 220 项拓扑违规，其中 Capability 20 项（P3a 后为 23 项；P3b 已消除 legacy/file-granularity 对应项，剩余含 checker 尚未承认的 ORM-first canonical/generated 边界、模块/依赖方向与 TypeScript 配置项）；`python3 -m pytest scripts/tests` 为 82 passed / 2 failed，仍是手册样本实际 11 与旧断言 18 不一致、TypeScript 手册新标题没有旧固定“参考依据”字样。日志为 `/tmp/kokoro-p3b-root-standard-20260910.log`、`/tmp/kokoro-p3b-root-topology-20260910.log`、`/tmp/kokoro-p3b-root-script-tests-20260910.log`。本片没有修改或放宽 Root checker/test，也未暂存 SQL 手册、`kokoro-agent` 或 `.tmp/` 的其他任务变更。

### P4-D 只读审计与设计裁决（2026-09-10）

三名 Agent 已在同一冻结 child 基线 `0f7dc1a95c84760612e4a96023f42149fe84cd0c` 完成只读审计；审前、审后 child 工作树均 clean，未修改文件、Git、数据库或服务：

| 任务 | Agent / 角色 | 审计面 | 结论 |
| --- | --- | --- | --- |
| P4-D-IMPL-AUDIT | capability_owner_p1b / 当前实现与删除面 | receipt/outbox/provider cleanup/worker lifecycle | 六个 Skills catalog mutation 尚未把 business/outbox/codec/completed receipt 合入同一事务；先补原子性，才能允许 stale processing takeover |
| P4-D-CONTRACT | contract_review / contract、identity、replay | wire/error/event/Manus typed ID/owner | 现有 Skills 与 17 个 MCP RPC wire 保持不变；恢复机制不得泄漏到业务请求；无真实 consumer/broker 前不发布伪 event-protocol |
| P4-D-DATA | database_review / PostgreSQL、Prisma、并发 | schema/lease/fence/retirement/retention | 推荐 Prisma typed query + conditional update/CAS；cleanup completion 不能用 outbox published 代替，需 MCP feature-owned durable retirement 状态 |

Root 结合已批准的 NestJS + Prisma 路线裁决采用 **Platform 内置、DB-native 的 NestJS worker + canonical Prisma schema + typed CAS**。不建设手写 SQL 队列，不把恢复状态交给 Scheduler，不增加独立进程或第二持久化事实源；若未来吞吐证明确需 `SKIP LOCKED`，必须另立 ADR、限定为 claim 短事务并补 raw 白名单/真实 PostgreSQL 并发证明，不能借现有 DB clock 例外扩大 raw SQL。

#### P4-D 放置表

| 项 | 结论 |
| --- | --- |
| Owner | 当前仓为 `kokoro-capability`，目标业务 owner 为 `kokoro-platform`；Skills command receipt、MCP authorization recovery/credential retirement、owner outbox 均由本仓唯一写入。Agent 继续拥有 run/session/live invoke，IAM 拥有身份与授权判断，Storage/SecretStore 拥有各自资源生命周期，Scheduler 不拥有本仓恢复事实。 |
| 当前事实 | `command_receipt` 只有 processing/completed/failed、digest/result/createdAt；installation 与 MCP 本地 success 已同事务，六个 Skills catalog mutation 仍为业务提交后另行 complete。`outbox_event` 只有 pending/published；unit dispatcher 未装配生产 publisher。Begin/Complete 有稳定 authorization identity 与部分 quarantine，但无跨崩溃 recovery stage。cleanup-requested outbox 只证明 durable intent，不证明 provider cleanup 完成。 |
| 目标职责 | command receipt 提供 lease owner/epoch/fencing、同身份精确 replay、local reclaim 与 external reconciliation；MCP retirement 以 credential identity 阻止新绑定并记录 cleanup 实际完成；owner outbox 在真实 destination 确定后提供 fenced at-least-once delivery、backoff/DLQ；worker 受 Nest lifecycle、readiness、bounded drain 管理。 |
| 目录方案 | 采用现有业务模块内聚：receipt/outbox 留在 application + infrastructure repository，Skills 原子事务留在 `modules/skills`，authorization recovery/retirement 留在 `modules/mcp/authorization`，生命周期由现有 Runtime registry 装配。淘汰独立通用 job 模块（会成为垃圾桶）和 Scheduler 托管方案（形成跨 owner 双事实）；cleanup 也不与公开 outbox delivery 混为同一状态机。 |
| 粒度 | 先更新既有 TECHNICAL_DESIGN/API_CONTRACT/DATA_MODEL/RELIABILITY/RUNBOOK/SECURITY/CURRENT，不新建顶层目录。实现按 P4a receipt 原子性/fencing、P4b provider recovery、P4c cleanup retirement、P4d event delivery、P4e1 receipt retention/supervision、P4e2 retirement GC、P4e3 delivery/event GC 切片；每片才依据实际职责决定少量新文件。 |
| 依赖 | 业务事务只 import Prisma transaction-facing repository/token，不 import transport/provider 实现；外部 I/O 永不进入数据库事务。worker 只经 typed repository/port 操作，Redis 仅可作通知/节流，不能决定 claim/fence/recovery 正确性。 |
| 数据/API | 保持现有 Skills 与 17 个 MCP RPC wire；`command_id` 只作命令幂等 identity。Skill `series_id`/`skill_id`/`installation_id`，MCP `connector_id`/`server_id`/`connection_id`/`authorization_id`/`grant_id`，以及 event/recovery/retirement identity 均独立 typed，禁止互换或用 provider key、URL、selector、tool name 代替。receipt/outbox/retirement 都使用 tenant-scoped CAS、DB clock、stable identity 与 fenced ACK。 |
| 删除项 | Skills 六 mutation 原子化后删除 generic action-then-complete production 路径；生产 worker接通后删除 unit-only dispatcher；未赋予语义的 `result_ref` 在 schema 片删除；修正文档中失真的 `PrismaCapabilityTransaction`、全局事务外 completion、Storage upload-abort 描述。不建立 alias、fallback 或双轨 worker。 |
| 验证 | 真实 PostgreSQL RED/GREEN 覆盖双 owner claim、lease takeover、ABA/旧 fence 拒绝、business/outbox/codec/receipt 原子回滚、commit reply lost、provider 四崩溃点、cleanup/new-binding race、publish ACK lost、DLQ redrive、retention/replay/GC race；再跑 format/lint/typecheck/contract/Prisma validate+generate+schema/fresh install/full test/build/smoke、独立 SPEC/QUALITY 双审和 Root post-commit 复验。 |

#### 已固定的状态与协议

1. Receipt 不是任意 executable command log，不保存 attestation/token/完整请求。纯本地命令在 lease 过期后只允许携带新合法授权的同 command caller 通过 CAS 接管；六个 Skills catalog mutation 重验当前 trusted workload/tenant/owner 契约，Skill installation 与 MCP 分别重验其现有 attestation/IAM/exact binding，不为统一恢复虚构新 wire。外部副作用只由 operation-specific durable recovery stage 按原 `authorization_id`/provider operation identity reconcile。只有证明请求尚未发出或 authoritative inspection 证明无效果才可转 retryable failed；发送后 timeout/disconnect/lost response 保持 `external_unknown` fail closed，不执行盲补偿。
2. 初始 claim 可在业务事务外；本地 business、0/1 outbox、encoded success 与 fenced completed receipt 必须在同一事务。active processing 的机器稳定结果为 Connect `ABORTED`，持续未知为 `UNAVAILABLE`，digest/operation 漂移为 `ALREADY_EXISTS`，expired 为 `FAILED_PRECONDITION`；`command_in_progress`、`command_outcome_unknown`、`command_replay_expired` 仅是内部 telemetry code，不经 message substring 伪装成 wire 子码。terminal typed error 精确重放。`lease_epoch` 从建行起是永久非 NULL 的 64-bit fence counter，每次 acquisition/reclaim/reconcile 按旧值 CAS 后原子递增，释放只清 owner/expiry，溢出 fail closed；所有 complete/fail/heartbeat/reaper/redrive/ACK 均比较 tenant、identity、owner 与 epoch，避免同 owner ABA。
3. P4a 先覆盖六个 Skills catalog mutation，再给所有 receipt 增加 Prisma 字段与 CAS：lease owner/epoch/expiry、attempt、failure kind/code、terminal/recovery/retention 时间与必要的版本化 recovery kind/ref/phase。扫描分别使用 stale-processing、due-retry、retention 索引；PostgreSQL 时钟为唯一期限事实。
4. MCP cleanup 新增 feature-owned credential retirement/cleanup 状态，以 `(tenant, provider, credential_identity_digest_v1)` 唯一化；v1 对 SecretStore/provider 保证至少 128-bit 不可猜的已验证 opaque handle ref 与 tenant/provider 使用域分离、长度前缀 canonical bytes 做 SHA-256，碰撞 readback 再比较 exact ref 并 fail closed。不能满足高熵前提的 provider 在 P4c readiness 拒绝启用，另立 HMAC/key-rotation ADR。表中保存 handle ref 只用于 provider revoke，不保存 credential secret/token，日志/事件不输出原值。pending/processing/dead/completed 都永久阻止新 binding，completed fence 不被普通 GC 删除；provider revoke 在事务外执行，fenced ACK 才表示 cleanup 完成。跨 tenant/provider 的相同字符串不互相阻断。
5. `outbox_event` 的 immutable envelope/payload 与 mutable delivery metadata 分离；同 event ID 冲突时核对 tenant/type/aggregate/payload/time/version，漂移 fail closed。只有真实 broker、destination 与 consumer/version/dedupe contract 确定后才装配生产 publisher；cleanup intent、安全 audit、可公开 business event 先分类，绝不无差别外发。投递为 at-least-once并保留原 event ID；同 aggregate 是 strict-dead-blocks 还是 gap-tolerant 必须由真实 consumer owner 在 P4d 解锁前二选一写入版本化 contract/fixtures，当前不提前承诺顺序。
6. owner 配置的 receipt replay window 不得短于 30 天；每条 receipt 在进入 terminal 时用 DB clock 固化不可变 `retention_expires_at=terminal_at+当时窗口`，配置变更只影响之后终态 receipt。`now < retention_expires_at` 精确 replay，`now >= retention_expires_at` 压缩为不可重新执行的轻量 expired tombstone，不静默释放 command identity。processing、external_unknown、pending/dead cleanup、dead-letter 及仍被 receipt/audit 引用的记录不做普通 GC；removed installation 与 revoked connector/connection identity tombstone 不删除。
7. Nest worker 不在 constructor 启动隐形循环；启动时经现有 Runtime registry 完成依赖 readiness 后运行，关闭顺序为 stop-acquire → bounded drain in-flight → 停 heartbeat/标记可识别 unknown → 关闭 provider/Redis/Prisma。worker 正确性只依赖 PostgreSQL；并发、batch、attempt、backoff+jitter、deadline 和 drain 全部有界。

#### P4 实现切片与授权状态

| 任务 | 依赖/owner | 允许范围 | 验收重点 | 当前状态 |
| --- | --- | --- | --- | --- |
| P4-D-DOC | capability_owner_p1b / child 唯一 writer；Root 独占 Git | 仅既有 `docs/{TECHNICAL_DESIGN,API_CONTRACT,DATA_MODEL,RELIABILITY,RUNBOOK,SECURITY,CURRENT}.md`；不得改 proto/schema/generated/src/test | 三设计面一致，清除旧事实，完整状态机/事务/失败恢复/typed ID/retention/worker 验收矩阵；冻结 diff 双审、Root 文档门 | 已验收；child `720acb999f6759a4fd2dca579c7aebdaaeb2d1c5` |
| P4a-I | capability_owner_p1b / child 唯一 writer；Root 独占 Git | receipt schema/repository/config/typed errors；共享 Prisma DB clock；Skills catalog/installation transaction+RPC；MCP transaction fence；对应 generated/check/tests/docs | 六个 Skills mutation 原子 success；local-only takeover、双 owner/同 owner ABA/旧 epoch/commit unknown/fresh schema；无网络进事务 | 已放行，进行中；plan `7f0ced0e` |
| P4b-I | P4a 验收后续派 | MCP authorization operation-specific recovery stage、provider port/repository、tests/docs | Begin/Complete 稳定 identity、provider call 前后崩溃、unknown outcome、late result/expiry/revoke race | 未授权 |
| P4c-I | P4b 验收后续派 | MCP feature-owned credential retirement/cleanup worker、Runtime lifecycle、tests/docs | new-binding retirement fence、shared handle/tenant/provider隔离、重复 revoke、DLQ、drain | 未授权 |
| P4d-I | P4-D consumer/broker contract 与真实 destination 确定后 | outbox delivery metadata/repository、真实 publisher、event contract、worker/tests/docs | 双 worker、ACK lost、consumer dedupe、最终 contract 的 partition key，以及已裁决的 strict-predecessor 或 gap-tolerant fixture、redrive identity | 设计阻塞；不造 fake publisher |
| P4e1-I | P4a 验收后 | receipt result compaction、expired tombstone、worker supervisor/metrics、tests/docs | 每条冻结窗口（配置>=30日）的 T-ε/T/T+ε、不可重执行、keyset/batch、readiness/fatal health、进程重启 | 未授权 |
| P4e2-I | P4c 验收后 | retirement GC/compaction、tests/docs | pending/processing/dead不删、completed fence保留、parent/reference/redrive竞态 | 未授权 |
| P4e3-I | P4d 验收后 | delivery/event GC、tests/docs | consumer dedupe窗口、dead-letter/redrive、receipt/audit引用顺序 | 依赖P4d，未授权 |

P4-D-DOC 已在 child `720acb999f6759a4fd2dca579c7aebdaaeb2d1c5` 闭环；后续只按下述 P4a 实施卡续派同一 capability_owner_p1b。contract_review 与 database_review 先对计划同一冻结 diff 分别作 SPEC/QUALITY 复审；双审前不开始 child schema/src/test 写入。

### P4-D-DOC 最终验收与 P4a 实施计划（2026-09-10）

P4-D-DOC 已由 Root 提交为 child `720acb999f6759a4fd2dca579c7aebdaaeb2d1c5`（`docs(capability): define crash recovery design`）。提交前最终冻结 diff SHA-256 为 `3dd01e5801cc85a7a2d0ac6140d37b1cf995b13db6f8a13068d71e8851e3aa19`；contract_review 最终 `SPEC PASS`、database_review 最终 `QUALITY PASS`，均为 Blocking/Important/Minor 0，并复算同一 HEAD/hash/status。Root 在 Node 24.20.0、pnpm 11.25.0 对最终提交前与提交后各自实跑 format、lint、typecheck、contract generate/check、Prisma validate、schema check、build、contract 20 tests、architecture 29 tests 与 diff check，全部 exit 0；提交后日志 `/tmp/kokoro-p4d-doc-root-postcommit-720acb9-20260910.log`。本设计验收不冒充 P4 schema/src/test 已实现。

P4a 复用本任务板，不另建第二计划。执行必须遵守 TDD：每组 production 变化前先写最小 RED、运行并确认因缺失行为失败，再写 GREEN；generated Prisma 文件只由 `pnpm prisma:generate` 产生。P4a 不实现 provider reconciliation、retirement worker、publisher、GC loop 或 P5 cutover。

#### P4a 文件职责

- 修改 `prisma/schema.prisma`：只增加已批准的 receipt enum/字段/索引并删除无语义 `result_ref`；不改 Skills/MCP resource identity、outbox 或其他表。
- 修改 `scripts/check-schema.ts` 与 `test/{architecture,integration}` schema fixtures：验证 enum、列、NULL/default/index、fresh install/drift、无 FK/CHECK；不增加第二 SQL schema。
- 修改 `src/application/command-receipt.ts`，按单一变化原因新增至多一个 `src/application/command-receipt.error.ts`：定义 codec、identity、lease、claim/state、窄 `CommandReceiptCoordinator` 与 transaction-facing receipt port、typed error；不把 telemetry code 变成 wire/message 子码。
- 将 `src/modules/mcp/mcp-transaction-clock.ts` 的唯一固定 `clock_timestamp()` 能力归位为共享 `src/database/prisma-transaction-clock.ts`，同步 MCP import 与 architecture raw 白名单；不新增第二 raw query 或手写 claim SQL。
- 修改 `src/infrastructure/repository/capability/prisma-command-receipt.repository.ts`：所有持久化仅用 generated Prisma delegate、interactive transaction 与 conditional update/CAS；实现 claim/replay/local takeover、owner+epoch renew/lock、fenced complete/retryable fail/terminal fail、inspect 与 corrupt-state fail closed。
- 修改 `src/config/injection-tokens.ts`、`src/config/runtime.ts`、`.env.example`、`src/runtime.module.ts` 及必要配置测试：以唯一 token `COMMAND_RECEIPT_COORDINATOR` 替代 `COMMAND_RECEIPTS`；固定 `KOKORO_CAPABILITY_COMMAND_RECEIPT_LEASE_MS`（默认 30000，正整数且最大 300000）与 `KOKORO_CAPABILITY_COMMAND_RECEIPT_REPLAY_WINDOW_DAYS`（默认 30，整数且范围 30–3650）。P4a 只在进入 terminal 的 transaction 内从 DB clock 固化每行 `retention_expires_at`，配置变更不回写旧行；只解析并拒绝测试预置的 `expired` tombstone，不执行 completed/terminal→expired transition，不清理 result，实际压缩与扫描仍归 P4e1。
- 修改 `src/modules/skills/skill-transaction.ts`、`src/modules/skills/catalog/skill-catalog.service.ts`、`src/modules/skills/skill-rpc.service.ts`、`src/modules/skills/skills.module.ts` 与必要窄类型/测试：RPC 先完成 Redis/Storage/输入准备，稳定 resource/event identity 在 retry 外生成；transaction 内重读 owner 事实并原子提交 business、0/1 outbox、protobuf codec result 与 fenced receipt。允许在既有 `catalog/` 内新增一个只承载 prepared local mutation 的文件；禁止网络 I/O 或嵌套 transaction。
- 修改 `src/modules/skills/installation/skill-installation.transaction.ts`、`src/modules/mcp/mcp-transaction.ts`、`src/modules/mcp/mcp.ports.ts`、`src/modules/mcp/mcp-rpc.service.ts` 及对应 module/test fixture：把 claim 返回的 lease 显式传过每个 transaction/failure path。Begin/Complete 标为 external recovery class，P4a 不允许 stale-processing generic takeover；已原子化的 local mutation 才允许 caller-driven takeover。
- 修改 `src/rpc/rpc-handler.ts` 与测试：typed active-processing=`ABORTED`、external-unknown=`UNAVAILABLE`、expired=`FAILED_PRECONDITION`、identity drift=`ALREADY_EXISTS`；只删除 `CommandReceiptStore.execute`、`rpc-handler.executeCommand`、Skills/MCP production generic action-then-complete fallback及旧 `COMMAND_RECEIPTS` token，禁止 message substring 承载新判定。初始 claim 的窄 coordinator DI 必须保留。
- 新建 `test/integration/command-receipt-postgres.integration.test.ts` 与 `test/integration/skill-command-receipt-postgres.integration.test.ts`：前者只证明 receipt lease/fence/state，后者用 `createPrismaClient`、真实 `PrismaSkillTransaction`/receipt/outbox 与独立 tenant fixture 证明六个 catalog mutation 的 durable 原子性；`REQUIRE_REAL_INTEGRATION=1` 且缺 PostgreSQL 配置时必须失败。既有 `test/integration/capability-service.test.ts` 只保留 service/Connect 与 double 行为，不冒充数据库证据。
- 修改 P4a 实际受影响的现有 README/INDEX/CURRENT/TECHNICAL_DESIGN/API_CONTRACT/DATA_MODEL/RELIABILITY/RUNBOOK/SECURITY 与测试清单；只把已通过本片验证的 receipt/Skills/fence 写为 current，P4b–P4e 仍列真实缺口。

#### P4a 最终 DI、owner 与 import 图

1. `src/application/command-receipt.ts` 是唯一抽象 owner：`CommandReceiptCoordinator` 只暴露事务外 initial claim/replay、带 lease 的 retryable-failure bookkeeping 与只读 inspect；transaction-facing port 只暴露 `assertOwned`、`complete`、`failTerminal`。两者都不 import Nest、Prisma 或 feature 类型。
2. `src/config/injection-tokens.ts` 只保留新 token `COMMAND_RECEIPT_COORDINATOR`；旧 `COMMAND_RECEIPTS` 删除。`src/runtime.module.ts` 是唯一长生命周期构造点：用 generated `PrismaClient`、共享 DB clock 和已校验 policy 构造 `PrismaCommandReceiptRepository`，以窄 coordinator interface export；不得注册第二 receipt provider/token。
3. Skills catalog 只有 `SkillRpcService` 直接注入 `COMMAND_RECEIPT_COORDINATOR`，负责 initial claim/replay 后把 lease 传给 `SKILL_TRANSACTION`。`SKILL_INSTALLATION_TRANSACTION` provider 注入同一 coordinator 并传给 `SkillInstallationTransaction`；`SkillInstallationRpcService` 不再直接取得任何 receipt token。
4. MCP 的 `MCP_MUTATION` provider 注入同一 coordinator并传给 `PrismaMcpTransaction`；`McpRpcService` 不再注入 receipt token，production mutation path 必须经非 optional 的 `McpMutationPort`。测试 double 也实现该窄 port，不保留 RPC service 内 generic fallback。
5. `PrismaSkillTransaction`、`SkillInstallationTransaction`、`PrismaMcpTransaction` 在 interactive transaction 内只构造 transaction-scoped `PrismaCommandReceiptRepository` adapter，使用同一 immutable policy；该 adapter不是 Nest provider，也不执行 initial claim。feature service/module 只 import application port/token；只有 transaction infrastructure implementation 可以 import concrete Prisma adapter，禁止手工 `new PrismaClient`、第二 clock query或 nested transaction。

目标核心类型/方法形状固定为：

```ts
type CommandReceiptLease = Readonly<{ ownerId: string; epoch: bigint }>;
type CommandReceiptClaim<T> =
  | Readonly<{ kind: "claimed"; lease: CommandReceiptLease }>
  | Readonly<{ kind: "replayed"; result: T }>;

interface CommandReceiptCoordinator {
  claim<T>(identity, codec, { recoveryClass }): Promise<CommandReceiptClaim<T>>;
  inspect<T>(identity, codec): Promise<CommandReceiptState<T>>;
  markRetryableFailure(identity, lease, failureCode): Promise<boolean>;
}

interface TransactionalCommandReceiptPort {
  assertOwned(identity, lease, transactionTime): Promise<void>;
  complete(identity, lease, value, codec, transactionTime): Promise<void>;
  failTerminal(identity, lease, failure, transactionTime): Promise<void>;
}
```

`lease_epoch` 建行初始 0、永久非 NULL；首次 acquire 与每次 reclaim 都以旧值 CAS 原子 `+1`，大于 64-bit signed 最大值前 fail closed。释放只清 owner/expiry；attempt 独立。`assertOwned` 必须以 conditional update/renew 取得 receipt row 的事务串行化点，使随后 business/outbox/codec/complete 都受同一行锁与 epoch 保护；affected count 非 1 时整笔事务回滚。纯本地 stale processing/`failed+retryable+SQL NULL` 才可由带当前授权的 caller 接管；Begin/Complete 的 stale processing 只返回 outcome unknown，等待 P4b operation-specific reconcile。

#### P4a RED → GREEN 执行卡

每张卡都先只写指定 RED 测试并运行列出的聚焦命令；记录“因目标行为尚不存在”而失败后，才改列出的最小 GREEN 文件。每卡 GREEN 后冻结一次 working-tree checkpoint（HEAD、目标 diff hash、命令与结果），但不操作 Git index/commit；Root 最终只在整片双审后串行提交。

- [ ] **P4a-1 Schema contract。**Test：`test/architecture/prisma-persistence.test.ts` 新增 `models the fenced command receipt without result_ref`；`test/integration/schema-installer.integration.test.ts` 新增 `installs the fenced command receipt schema`；`scripts/check-schema.ts` 增加同一 enum/列/default/index/FK/CHECK 断言。RED：`pnpm vitest run test/architecture/prisma-persistence.test.ts -t "models the fenced command receipt without result_ref"`，预期旧 schema 缺字段/索引且仍含 `result_ref`；真实 PG 命令 `REQUIRE_REAL_INTEGRATION=1 KOKORO_POSTGRES_URL=<unique-db-url> pnpm vitest run test/integration/schema-installer.integration.test.ts -t "installs the fenced command receipt schema" --no-file-parallelism` 同因失败。GREEN：只改 `prisma/schema.prisma` 并生成 client；跑 `pnpm prisma:validate && pnpm prisma:generate && pnpm schema:check`、上述两条 test 与 fresh isolated `pnpm db:apply-schema`，public FK/CHECK 必须为 0。
- [ ] **P4a-2 Typed state/error mapper。**Test：`test/unit/command-receipt.test.ts` 新增 `maps every durable receipt state without message matching` 表驱动项，覆盖 active processing、external unknown、identity drift、completed、terminal failure、SQL NULL 与 JSON null、malformed/overflow fail closed、seeded expired tombstone。RED：`pnpm vitest run test/unit/command-receipt.test.ts -t "maps every durable receipt state without message matching"`，预期缺新类型/状态与 typed errors。GREEN：只改 `src/application/command-receipt.ts`、可选 `command-receipt.error.ts` 及 repository mapper；聚焦命令变绿。这里的 expired 仅是预置 tombstone mapping，不做按时间转态或 result 清理。
- [ ] **P4a-3 Initial claim/replay。**Test：新建 `test/integration/command-receipt-postgres.integration.test.ts`，先写 `acquires epoch one once and replays only an exact completed identity` 与 `rejects active and external recovery claims with typed outcomes`。RED：`REQUIRE_REAL_INTEGRATION=1 KOKORO_POSTGRES_URL=<unique-db-url> pnpm vitest run test/integration/command-receipt-postgres.integration.test.ts -t "acquires epoch one once|rejects active and external recovery claims" --no-file-parallelism`，预期旧 create-only claim 无 lease/recovery class/typed outcome。GREEN：实现 coordinator `claim/inspect` 的 typed Prisma insert+CAS/readback和 DB-time lease；不得加入 raw claim SQL。
- [ ] **P4a-4 Lease/fence concurrency。**Test：同一 PG 文件新增 `serializes takeover against the receipt row lock` 与表驱动 `rejects every obsolete receipt epoch and overflow`。前一 fixture 必须让 A 在 interactive transaction 内持有 receipt row serial point跨过 lease expiry，B takeover 同时发起并等待；A commit 时 B 只能 replay，A rollback 时 B 才以新 epoch acquire。后一 fixture覆盖双 client、same-owner ABA、旧 epoch late complete/fail/renew、failed+retryable+SQL NULL reclaim、epoch overflow。RED：`REQUIRE_REAL_INTEGRATION=1 KOKORO_POSTGRES_URL=<unique-db-url> pnpm vitest run test/integration/command-receipt-postgres.integration.test.ts -t "serializes takeover against the receipt row lock|rejects every obsolete receipt epoch and overflow" --no-file-parallelism`，预期旧实现不能等待/比较 epoch/拒绝溢出。GREEN：repository 用 interactive transaction、`updateMany` old-value CAS 与 shared DB clock；断言 durable business/outbox/receipt 行数，不以 callback 调用次数代替提交事实。
- [ ] **P4a-5 Transactional terminal policy。**Test：同一 PG 文件新增 `freezes terminal replay expiry from transaction database time` 与 `rolls back business when fenced completion loses ownership`，覆盖 completed/typed terminal 的 immutable expiry、配置改变不回写、codec failure、commit response unknown。RED：`REQUIRE_REAL_INTEGRATION=1 KOKORO_POSTGRES_URL=<unique-db-url> pnpm vitest run test/integration/command-receipt-postgres.integration.test.ts -t "freezes terminal replay expiry|rolls back business when fenced completion" --no-file-parallelism`，预期缺 transaction-facing port/expiry/fence。GREEN：实现 `assertOwned/complete/failTerminal/markRetryableFailure` 最小方法；P4a 不扫描或压缩到期结果。
- [ ] **P4a-6 Config 与唯一 DI。**Test：`test/integration/production-composition.integration.test.ts` 新增 `constructs one narrow command receipt coordinator`，`test/unit/skills-module.test.ts` 新增 `routes receipt ownership through the narrow coordinator`，`test/architecture/architecture.test.ts` 新增 `has one receipt provider and no generic executor`；并在既有 runtime config test 所在 `test/integration/production-composition.integration.test.ts` 表驱动 lease/replay默认值与边界。RED：分别运行 `pnpm vitest run test/integration/production-composition.integration.test.ts -t "constructs one narrow command receipt coordinator|validates command receipt policy"`、`pnpm vitest run test/unit/skills-module.test.ts -t "routes receipt ownership through the narrow coordinator"`、`pnpm vitest run test/architecture/architecture.test.ts -t "has one receipt provider and no generic executor"`，预期旧 token、双用途 store、缺 config。GREEN：改 `injection-tokens.ts`、runtime config/module、Skills/MCP provider wiring、`.env.example`；此卡只建立窄 DI 与 mandatory MCP mutation port，业务行为留后续卡。
- [ ] **P4a-7 Skill installation lease。**Test：`test/unit/skill-installation-transaction.test.ts` 新增 `propagates one lease through every retry and finalization`；`test/integration/skill-installation.integration.test.ts` 新增 `rejects an obsolete installation fence without partial business or outbox state`。RED：`pnpm vitest run test/unit/skill-installation-transaction.test.ts -t "propagates one lease through every retry and finalization"`；真实 PG 使用 `REQUIRE_REAL_INTEGRATION=1 KOKORO_POSTGRES_URL=<unique-db-url> KOKORO_REDIS_URL=<isolated-redis-url> pnpm vitest run test/integration/skill-installation.integration.test.ts -t "rejects an obsolete installation fence without partial business or outbox state" --no-file-parallelism`，预期旧无 lease 签名/旧 owner仍能完成。GREEN：最小修改 installation transaction/RPC/module fixture，P2034 每个 attempt 重读 DB clock/fence，失败时 durable business/outbox/receipt counts 保持原子。
- [ ] **P4a-8 MCP local/external fence。**Test：`test/unit/mcp-transaction.test.ts` 新增 `propagates the lease and refreshes the fence on a serialization retry`、`test/unit/mcp-p3a.test.ts` 新增 `does not generically take over stale Begin or Complete authorization`；真实 PG 在 `test/integration/mcp-p3a-postgres.integration.test.ts` 新增 `rejects an obsolete MCP fence without partial state`。RED：`pnpm vitest run test/unit/mcp-transaction.test.ts -t "propagates the lease and refreshes the fence on a serialization retry"`、`pnpm vitest run test/unit/mcp-p3a.test.ts -t "does not generically take over stale Begin or Complete authorization"`、`REQUIRE_REAL_INTEGRATION=1 KOKORO_POSTGRES_URL=<unique-db-url> KOKORO_REDIS_URL=<isolated-redis-url> pnpm vitest run test/integration/mcp-p3a-postgres.integration.test.ts -t "rejects an obsolete MCP fence without partial state" --no-file-parallelism`；预期旧 claim 无 lease且 RPC fallback可绕过 mutation port。GREEN：最小修改 MCP transaction/ports/RPC/module fixture，删除 McpRpcService receipt DI和 generic fallback；保持 17 方法、request binding、Manus `connector_id/server_id/connection_id/authorization_id/grant_id`、provider调用次数、取消与 unknown-commit 语义。
- [ ] **P4a-9 Skills create mutations。**Test：`test/unit/skill-transaction.test.ts` 新增 `atomically commits create draft and version receipts`；新建真实 PG suite `test/integration/skill-command-receipt-postgres.integration.test.ts`，以 `createPrismaClient`、`PrismaSkillTransaction`、真实 receipt/outbox 新增 `atomically persists create draft and version receipts in PostgreSQL`，表驱动 create draft/create version × business/outbox/codec/receipt-completion fault，并断言 durable table counts、same-command exact replay、稳定 `series_id/skill_id`。suite 为每例创建独立 tenant并只清理自身数据，`REQUIRE_REAL_INTEGRATION=1` 缺 URL 时必须失败。RED：`pnpm vitest run test/unit/skill-transaction.test.ts -t "atomically commits create draft and version receipts"`、`REQUIRE_REAL_INTEGRATION=1 KOKORO_POSTGRES_URL=<unique-db-url> pnpm vitest run test/integration/skill-command-receipt-postgres.integration.test.ts -t "atomically persists create draft and version receipts in PostgreSQL" --no-file-parallelism`，预期旧 `executeCommand` 在业务提交后才完成 receipt。GREEN：只实现 create draft/version 的 prepare→single Serializable transaction；UUID/event identity 在 retry 外生成，transaction内重读 owner，不改变 `series_id`/`skill_id` 语义。
- [ ] **P4a-10 Skills validate/publish mutations。**Test：同一 unit 与真实 PG suite 新增 `atomically commits validate and publish receipts`、`atomically persists validate and publish receipts in PostgreSQL`，表驱动 validate/publish × 四故障点并断言 durable table counts、final transaction重读 current draft/owner；既有 `test/integration/capability-service.test.ts` 新增 `keeps Storage verification outside the final skill transaction`，只作为 service/Connect double 的调用边界证明。RED：`pnpm vitest run test/unit/skill-transaction.test.ts -t "atomically commits validate and publish receipts"`、`REQUIRE_REAL_INTEGRATION=1 KOKORO_POSTGRES_URL=<unique-db-url> pnpm vitest run test/integration/skill-command-receipt-postgres.integration.test.ts -t "atomically persists validate and publish receipts in PostgreSQL" --no-file-parallelism`、`pnpm vitest run test/integration/capability-service.test.ts -t "keeps Storage verification outside the final skill transaction"`，预期旧路径部分提交或 Storage/transaction边界不受约束。GREEN：只迁移 validate/publish；Storage I/O 必须在 transaction 外，package identity只作 prepared input。
- [ ] **P4a-11 Skills withdraw/set-status mutations。**Test：同一 unit 与真实 PG suite 新增 `atomically commits withdraw and set-status receipts`、`atomically persists withdraw and set-status receipts in PostgreSQL`，表驱动 withdraw/set-status × 四故障点并断言 durable table counts、并发 takeover/旧 fence、same-command exact replay；SetSkillStatus 明确覆盖 wire 数值不变的 ACTIVE(2)↔DISABLED(5) 合法转换、重复/no-op与非法 enum/source-state 拒绝。RED：`pnpm vitest run test/unit/skill-transaction.test.ts -t "atomically commits withdraw and set-status receipts"`、`REQUIRE_REAL_INTEGRATION=1 KOKORO_POSTGRES_URL=<unique-db-url> pnpm vitest run test/integration/skill-command-receipt-postgres.integration.test.ts -t "atomically persists withdraw and set-status receipts in PostgreSQL" --no-file-parallelism`，预期旧 action-then-complete留下部分状态。GREEN：迁移最后两 mutation，并在六个方法都已过卡后删除 `rpc-handler.executeCommand` 与 `CommandReceiptStore.execute` production 定义/使用；不改 Proto 或 wire enum，不新增 RPC、attestation、alias或第二 service。
- [ ] **P4a-12 删除面与文档真实性。**Test：先扩 `test/architecture/architecture.test.ts` 的 `has one receipt provider and no generic executor`，显式搜索旧 `COMMAND_RECEIPTS`、旧 MCP clock path、`result_ref`、production `.execute(` 与无 lease transaction signature；RED 应因残留失败。GREEN：移动唯一 clock 文件并更新 raw 白名单/import，更新受影响 README/INDEX/CURRENT/TECHNICAL_DESIGN/API_CONTRACT/DATA_MODEL/RELIABILITY/RUNBOOK/SECURITY；只写已实现事实，保留 P4b–P4e gap。运行 `pnpm vitest run test/architecture/architecture.test.ts -t "has one receipt provider and no generic executor"`、`rg -n "COMMAND_RECEIPTS|mcp-transaction-clock|result_ref|executeCommand" src prisma test scripts` 并人工区分历史 fixture/doc，不以盲目字符串清零替代 architecture assertion。
- [ ] **P4a-13 Writer 全门。**Node 24 下运行 `pnpm format:check`、`pnpm lint`、`pnpm typecheck`、`pnpm contract:check`、`pnpm prisma:validate`、`pnpm prisma:generate`、`pnpm schema:check`、`pnpm build`、`pnpm test:unit`、`pnpm test:contract`、`pnpm test:architecture`。使用唯一 fresh PostgreSQL database 与独立 Redis namespace运行 `REQUIRE_REAL_INTEGRATION=1 KOKORO_POSTGRES_URL=<unique-db-url> KOKORO_REDIS_URL=<isolated-redis-url> pnpm test:integration`、同变量下的 `pnpm smoke`，再运行 `KOKORO_POSTGRES_URL=<unique-db-url> KOKORO_REDIS_URL=<isolated-redis-url> pnpm smoke:production`；production smoke 使用脚本自建的 IAM/Storage/provider owner stubs，明确不冒充真实外部 provider sandbox。不得重启共享服务或清他人数据；报告每张卡的 RED 失败原因、GREEN 数量、未运行项。
- [ ] **P4a-14 冻结审查。**writer 停写并给 HEAD、tracked/untracked hash、绝对文件清单与每卡 checkpoint；contract_review 与 database_review 对同一最终 hash 分别 SPEC/QUALITY，任何 blocking/important 回原 writer新增最小 RED修复并重新冻结；双 PASS 后 Root 才按绝对精确路径暂存、提交，并在 child commit 上重跑完整 post-commit 门禁。

P4a-I 基线为 child `720acb999f6759a4fd2dca579c7aebdaaeb2d1c5`，负责人仍为 capability_owner_p1b；允许范围只限上述 receipt/Skills/MCP transaction/config/generated/schema/test/必要文档文件。禁止改 proto/OpenAPI/outbox delivery/retirement/provider recovery worker/P5/其他仓，禁止新增 raw queue SQL，禁止 writer 操作 Git index/commit/branch。发现必须越界时先报告 Root 调整任务卡。

P4a 实施卡冻结 diff `b2823c735d19d1fe19fc3900407eb718c7af4783a9226b4ed9454c2d36401f10` 已由 contract_review `PLAN SPEC PASS`、database_review `PLAN QUALITY PASS` 独立复核，Blocking/Important/Minor 均为 0；Root 将该计划提交为 `7f0ced0e` 后续派 capability_owner_p1b。该记录只表示实施授权，不表示 P4a 代码已验收。

#### P4a 首轮实现审查修复卡（2026-09-10）

首个实现候选冻结为 child HEAD `720acb999f6759a4fd2dca579c7aebdaaeb2d1c5`、tracked diff `524af52abc72afb56780e9c15b417714af74629d6daebf1617ef1aace2342ecc`、untracked manifest `1c47499f9527b86870b4fe34101220f4f0c9e84f434df4cd1a3c492c6d1d6da4`、full candidate `6225a91ca7a82cd5fe0e893930a7d871829f92a0e57cab07b25904bbfdc855ce`。contract_review 为 SPEC FAIL（Blocking 2 / Important 3），database_review 为 QUALITY FAIL（Important 5）；因此候选未验收、未提交。原 writer 只按以下 RED 修复，不扩大至 P4b：

1. Receipt acquisition 先区分 active lease：无论 local/external 都为 `ABORTED`；lease stale 后 external processing 与 external failed-retryable 均为 `UNAVAILABLE` 且 epoch/attempt不变，只有 local可CAS接管。所有 processing/failed/inspect/assert/fail路径用 Prisma `DbNull` predicate 区分 SQL NULL 与 JSON null；codec success encode 为 null/JSON null时在business transaction内拒绝并整体回滚。
2. `markRetryableFailure` 在短 Prisma transaction 内重读 DB clock，并要求 tenant+identity+owner+epoch+未过期 lease+SQL NULL；过期旧owner即使尚无新owner也不能写。Ownership lost显式映射 `ABORTED`；epoch overflow/corrupt只输出净化 `INTERNAL`。seeded expired tombstone按 DATA_MODEL 同时验证 terminal/retention、completed-vs-terminal failure、failure/recovery/null矩阵。
3. Skills 六个 catalog mutation 在receipt lookup前重算并常量时间校验 stable command digest，绑定 trusted tenant、完整method与全部业务字段，排除request_id/command identity自身；允许新增唯一文件 `src/modules/skills/catalog/skill-catalog.request-binding.ts` 承载 canonical算法/方法字段，不复用MCP identity helper。claim前做无副作用shape/current tenant resource/owner admission，completed replay后逐方法核对 response `skill_id/source_ref/status/digest` 与本次请求/current事实；不新增attestation或wire字段，不改变 `series_id/skill_id/source_ref/installation_id` 语义。
4. Skills catalog 与 installation 对本地事务明确区分 callback失败和 COMMIT response unknown：known rollback才fenced mark retryable；callback已结束但commit返回不可判定时inspect durable receipt，completed返回首次结果，确认未提交才标retryable，inspection不可读或仍不可判定抛 `UNAVAILABLE`。不得把该本地readback扩展成P4b provider reconcile。
5. 真实 PostgreSQL RED 补齐：六 mutation 每个都覆盖business、codec、receipt-completion rollback；publish/withdraw另覆盖outbox failure，其余四个断言0 outbox；逐例独立读取受影响字段、outbox与receipt，不只看行数。row-lock A/B commit/rollback fixture加入同事务business/outbox并在结束后读取durable counts；catalog与installation各有commit-response-lost fixture。修正fault case的operation/实际mutation一致。
6. 修复后先跑聚焦 JSON-null/external active-vs-stale/digest substitution+current replay/commit-unknown/六mutation PG矩阵，再跑原P4a-13全门；冻结新三hash后由同两名 reviewer 对同一对象重审，Root不得以首轮466 tests通过替代反例闭环。

#### P4a 第二轮实现审查修复卡（2026-09-10）

首审整改候选冻结为 child HEAD `720acb999f6759a4fd2dca579c7aebdaaeb2d1c5`、tracked diff `25cff55d6f3f9206dfe3d67126261ca7beea8e1777ca2623e7a480ce19b0fcc8`、untracked manifest `1ef716d8e1056ca27b9ca21621f0c087825eaaa57f7e812a68d2c828c9133160`、Root 可复现 full candidate `6c4853ad1ed406c420352b9e793b14dd24c44a83b27371e9c6861f11bcbdd98a`。contract_review 为 SPEC FAIL（Blocking 1 / Important 1），database_review 为 QUALITY FAIL（Important 3）；冻结对象未验收、未提交。原 writer 继续只做以下最小 RED→GREEN，不扩大范围：

1. Root client 的 `inspect()` 必须在一个 RepeatableRead（或更强）Prisma snapshot 内读取 receipt 与 `result_json IS SQL NULL` 判定；已处于 transaction client 时复用现有 transaction，不嵌套事务。增加固定时序回归，证明 processing/SQL NULL 与并发 completed transition不能拼接成 corrupt/INTERNAL。
2. Skill installation 的 commit-response-unknown readback 只有在 `markRetryableFailure()` CAS 返回 `true`、已证明旧事务未提交时才抛原错误；返回 `false` 代表 lease/状态已变化，必须再次证明 completed 或以 `CommandReceiptOutcomeUnknownError` fail closed。反转当前固化 `mark=false` 仍返回原 ownership error 的测试，并保留 catalog 同语义。
3. Receipt row-lock 真实 PostgreSQL fixture 的 A 事务同时写入真实业务表、outbox 与 receipt；commit/rollback 两个结局分别读取业务字段/count、outbox count、receipt status/epoch，不能只用 callback 或 outbox 代替完整 durable 证据。
4. 同片修正文档当前态自相矛盾：`TECHNICAL_DESIGN` 前部不能仍称六个 Skills catalog mutation 为业务提交后另行 completion；`API_CONTRACT` 对 proto3 `bytes metadata_json` 只描述实际 wire value，不宣称不存在的 scalar presence。不得借此更改 proto/wire 或 canonical digest字段。
5. 聚焦 RED/GREEN 后重新执行原 P4a-13 全门与真实 PostgreSQL integration；重新冻结 HEAD/tracked/untracked/full 三hash，由同两名 reviewer 对同一候选复审，双 PASS 前 Root 不暂存 child 文件。
