# Capability → Platform：NestJS + Prisma 实施任务板

状态：P0、P1a、P1b、P2a、P2b、P2c、P3-D、P3a、P3b、P4-D 以及 P4a-ADMISSION-I-1 至 I-12 已验收；P4b MCP authorization operation-specific recovery 实施计划已经 SPEC/QUALITY 双审，P4b-1 typed provider/recovery contract、P4b-2 atomic prepare 与 P4b-3 recovery CAS/state 及其粒度整改均已验收（`f9dc3a3` + `9f237f9`）。`IAM-ATTESTATION-D` 文档设计门已由 IAM owner 提交 `bf160be` 并通过双审；下一个串行 P0 是 Agent proof/JWKS owner contract，之后才是 IAM verifier/OpenAPI/generated SDK 与 Platform consumer。P4b-4 在该 owner-first 链闭环前不放行，P4c–P4e 与 P5 待依赖顺序续派。用户已批准总体方案并授权推进（2026-09-07），并再次强调 Skills/MCP typed identity、Manus 设计与 NestJS + Prisma 唯一技术路线（2026-09-10）。本任务板是本轮唯一推进记录。

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
| P4 / P0 | receipt/outbox 崩溃恢复、有限重试、retention 和可观测性 | capability-owner / gpt-5.6-sol / 分片授权 | 本仓实际用例涉及文件，实施前细化 | P2/P3 | P4a 已验收；P4b-1 `b507451`、P4b-2 `4e26112`、P4b-3 `f9dc3a3` + `9f237f9` 已验收；IAM 文档门 `bf160be` 已验收；等待 Agent proof/JWKS → IAM verifier/SDK → Platform consumer，P4b-4 暂不放行 |
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
- 标识与 Manus 对齐：Skill 仍区分 `series_id`、不可变 revision `skill_id`、task `source_ref` 和管理用 `installation_id`；MCP 仍区分 `connector_id`、`server_id`、`connection_id` 与 wire `invocation_grant`。provider key、URL、selector 和 tool name 不冒充资源 ID。`invocation_grant` 是 run/session-bound opaque UUIDv4 decision value，而不是另一项 `grant_id` 资源或 alias；它由 receipt 稳定重放，audit 用 digest 绑定原始决定并不保存 raw approval reference。
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
| 数据/API | 保持现有 Skills 与 17 个 MCP RPC wire；`command_id` 只作命令幂等 identity。Skill `series_id`/`skill_id`/`installation_id`，MCP `connector_id`/`server_id`/`connection_id`/`authorization_id`、wire `invocation_grant`，以及 event/recovery/retirement identity 均独立 typed，禁止互换或用 provider key、URL、selector、tool name 代替；不存在附加 `grant_id` 字段或 alias。receipt/outbox/retirement 都使用 tenant-scoped CAS、DB clock、stable identity 与 fenced ACK。 |
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
| P4a-I | capability_owner_p1b / child 唯一 writer；Root 独占 Git | receipt schema/repository/config/typed errors；共享 Prisma DB clock；Skills catalog/installation transaction+RPC；MCP transaction fence；singleton admission、atomic installer、generated/check/tests/docs | 六个 Skills mutation 原子 success；local-only takeover、双 owner/同 owner ABA/旧 epoch/commit unknown/fresh schema；cross-replica 0 zero-winner；无网络持slot | 已验收；最终 child `b21f9c7a22dc5de095eb79cb9e6afea0983fe12c` |
| P4b-I | P4a 验收后续派 | MCP authorization operation-specific recovery stage、provider port/repository、tests/docs | Begin/Complete 稳定 identity、provider call 前后崩溃、unknown outcome、late result/expiry/revoke race | 实施设计已起草，双审前未授权 |
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

- [x] **P4a-1 Schema contract。**Test：`test/architecture/prisma-persistence.test.ts` 新增 `models the fenced command receipt without result_ref`；`test/integration/schema-installer.integration.test.ts` 新增 `installs the fenced command receipt schema`；`scripts/check-schema.ts` 增加同一 enum/列/default/index/FK/CHECK 断言。RED：`pnpm vitest run test/architecture/prisma-persistence.test.ts -t "models the fenced command receipt without result_ref"`，预期旧 schema 缺字段/索引且仍含 `result_ref`；真实 PG 命令 `REQUIRE_REAL_INTEGRATION=1 KOKORO_POSTGRES_URL=<unique-db-url> pnpm vitest run test/integration/schema-installer.integration.test.ts -t "installs the fenced command receipt schema" --no-file-parallelism` 同因失败。GREEN：只改 `prisma/schema.prisma` 并生成 client；跑 `pnpm prisma:validate && pnpm prisma:generate && pnpm schema:check`、上述两条 test 与 fresh isolated `pnpm db:apply-schema`，public FK/CHECK 必须为 0。
- [x] **P4a-2 Typed state/error mapper。**Test：`test/unit/command-receipt.test.ts` 新增 `maps every durable receipt state without message matching` 表驱动项，覆盖 active processing、external unknown、identity drift、completed、terminal failure、SQL NULL 与 JSON null、malformed/overflow fail closed、seeded expired tombstone。RED：`pnpm vitest run test/unit/command-receipt.test.ts -t "maps every durable receipt state without message matching"`，预期缺新类型/状态与 typed errors。GREEN：只改 `src/application/command-receipt.ts`、可选 `command-receipt.error.ts` 及 repository mapper；聚焦命令变绿。这里的 expired 仅是预置 tombstone mapping，不做按时间转态或 result 清理。
- [x] **P4a-3 Initial claim/replay。**Test：新建 `test/integration/command-receipt-postgres.integration.test.ts`，先写 `acquires epoch one once and replays only an exact completed identity` 与 `rejects active and external recovery claims with typed outcomes`。RED：`REQUIRE_REAL_INTEGRATION=1 KOKORO_POSTGRES_URL=<unique-db-url> pnpm vitest run test/integration/command-receipt-postgres.integration.test.ts -t "acquires epoch one once|rejects active and external recovery claims" --no-file-parallelism`，预期旧 create-only claim 无 lease/recovery class/typed outcome。GREEN：实现 coordinator `claim/inspect` 的 typed Prisma insert+CAS/readback和 DB-time lease；不得加入 raw claim SQL。
- [x] **P4a-4 Lease/fence concurrency。**Test：同一 PG 文件新增 `serializes takeover against the receipt row lock` 与表驱动 `rejects every obsolete receipt epoch and overflow`。前一 fixture 必须让 A 在 interactive transaction 内持有 receipt row serial point跨过 lease expiry，B takeover 同时发起并等待；A commit 时 B 只能 replay，A rollback 时 B 才以新 epoch acquire。后一 fixture覆盖双 client、same-owner ABA、旧 epoch late complete/fail/renew、failed+retryable+SQL NULL reclaim、epoch overflow。RED：`REQUIRE_REAL_INTEGRATION=1 KOKORO_POSTGRES_URL=<unique-db-url> pnpm vitest run test/integration/command-receipt-postgres.integration.test.ts -t "serializes takeover against the receipt row lock|rejects every obsolete receipt epoch and overflow" --no-file-parallelism`，预期旧实现不能等待/比较 epoch/拒绝溢出。GREEN：repository 用 interactive transaction、`updateMany` old-value CAS 与 shared DB clock；断言 durable business/outbox/receipt 行数，不以 callback 调用次数代替提交事实。
- [x] **P4a-5 Transactional terminal policy。**Test：同一 PG 文件新增 `freezes terminal replay expiry from transaction database time` 与 `rolls back business when fenced completion loses ownership`，覆盖 completed/typed terminal 的 immutable expiry、配置改变不回写、codec failure、commit response unknown。RED：`REQUIRE_REAL_INTEGRATION=1 KOKORO_POSTGRES_URL=<unique-db-url> pnpm vitest run test/integration/command-receipt-postgres.integration.test.ts -t "freezes terminal replay expiry|rolls back business when fenced completion" --no-file-parallelism`，预期缺 transaction-facing port/expiry/fence。GREEN：实现 `assertOwned/complete/failTerminal/markRetryableFailure` 最小方法；P4a 不扫描或压缩到期结果。
- [x] **P4a-6 Config 与唯一 DI。**Test：`test/integration/production-composition.integration.test.ts` 新增 `constructs one narrow command receipt coordinator`，`test/unit/skills-module.test.ts` 新增 `routes receipt ownership through the narrow coordinator`，`test/architecture/architecture.test.ts` 新增 `has one receipt provider and no generic executor`；并在既有 runtime config test 所在 `test/integration/production-composition.integration.test.ts` 表驱动 lease/replay默认值与边界。RED：分别运行 `pnpm vitest run test/integration/production-composition.integration.test.ts -t "constructs one narrow command receipt coordinator|validates command receipt policy"`、`pnpm vitest run test/unit/skills-module.test.ts -t "routes receipt ownership through the narrow coordinator"`、`pnpm vitest run test/architecture/architecture.test.ts -t "has one receipt provider and no generic executor"`，预期旧 token、双用途 store、缺 config。GREEN：改 `injection-tokens.ts`、runtime config/module、Skills/MCP provider wiring、`.env.example`；此卡只建立窄 DI 与 mandatory MCP mutation port，业务行为留后续卡。
- [x] **P4a-7 Skill installation lease。**Test：`test/unit/skill-installation-transaction.test.ts` 新增 `propagates one lease through every retry and finalization`；`test/integration/skill-installation.integration.test.ts` 新增 `rejects an obsolete installation fence without partial business or outbox state`。RED：`pnpm vitest run test/unit/skill-installation-transaction.test.ts -t "propagates one lease through every retry and finalization"`；真实 PG 使用 `REQUIRE_REAL_INTEGRATION=1 KOKORO_POSTGRES_URL=<unique-db-url> KOKORO_REDIS_URL=<isolated-redis-url> pnpm vitest run test/integration/skill-installation.integration.test.ts -t "rejects an obsolete installation fence without partial business or outbox state" --no-file-parallelism`，预期旧无 lease 签名/旧 owner仍能完成。GREEN：最小修改 installation transaction/RPC/module fixture，P2034 每个 attempt 重读 DB clock/fence，失败时 durable business/outbox/receipt counts 保持原子。
- [x] **P4a-8 MCP local/external fence。**Test：`test/unit/mcp-transaction.test.ts` 新增 `propagates the lease and refreshes the fence on a serialization retry`、`test/unit/mcp-p3a.test.ts` 新增 `does not generically take over stale Begin or Complete authorization`；真实 PG 在 `test/integration/mcp-p3a-postgres.integration.test.ts` 新增 `rejects an obsolete MCP fence without partial state`。RED：`pnpm vitest run test/unit/mcp-transaction.test.ts -t "propagates the lease and refreshes the fence on a serialization retry"`、`pnpm vitest run test/unit/mcp-p3a.test.ts -t "does not generically take over stale Begin or Complete authorization"`、`REQUIRE_REAL_INTEGRATION=1 KOKORO_POSTGRES_URL=<unique-db-url> KOKORO_REDIS_URL=<isolated-redis-url> pnpm vitest run test/integration/mcp-p3a-postgres.integration.test.ts -t "rejects an obsolete MCP fence without partial state" --no-file-parallelism`；预期旧 claim 无 lease且 RPC fallback可绕过 mutation port。GREEN：最小修改 MCP transaction/ports/RPC/module fixture，删除 McpRpcService receipt DI和 generic fallback；保持 17 方法、request binding、Manus `connector_id/server_id/connection_id/authorization_id/invocation_grant`、provider调用次数、取消与 unknown-commit 语义，且不新增 `grant_id` 字段或 alias。
- [x] **P4a-9 Skills create mutations。**Test：`test/unit/skill-transaction.test.ts` 新增 `atomically commits create draft and version receipts`；新建真实 PG suite `test/integration/skill-command-receipt-postgres.integration.test.ts`，以 `createPrismaClient`、`PrismaSkillTransaction`、真实 receipt/outbox 新增 `atomically persists create draft and version receipts in PostgreSQL`，表驱动 create draft/create version × business/outbox/codec/receipt-completion fault，并断言 durable table counts、same-command exact replay、稳定 `series_id/skill_id`。suite 为每例创建独立 tenant并只清理自身数据，`REQUIRE_REAL_INTEGRATION=1` 缺 URL 时必须失败。RED：`pnpm vitest run test/unit/skill-transaction.test.ts -t "atomically commits create draft and version receipts"`、`REQUIRE_REAL_INTEGRATION=1 KOKORO_POSTGRES_URL=<unique-db-url> pnpm vitest run test/integration/skill-command-receipt-postgres.integration.test.ts -t "atomically persists create draft and version receipts in PostgreSQL" --no-file-parallelism`，预期旧 `executeCommand` 在业务提交后才完成 receipt。GREEN：只实现 create draft/version 的 prepare→single Serializable transaction；UUID/event identity 在 retry 外生成，transaction内重读 owner，不改变 `series_id`/`skill_id` 语义。
- [x] **P4a-10 Skills validate/publish mutations。**Test：同一 unit 与真实 PG suite 新增 `atomically commits validate and publish receipts`、`atomically persists validate and publish receipts in PostgreSQL`，表驱动 validate/publish × 四故障点并断言 durable table counts、final transaction重读 current draft/owner；既有 `test/integration/capability-service.test.ts` 新增 `keeps Storage verification outside the final skill transaction`，只作为 service/Connect double 的调用边界证明。RED：`pnpm vitest run test/unit/skill-transaction.test.ts -t "atomically commits validate and publish receipts"`、`REQUIRE_REAL_INTEGRATION=1 KOKORO_POSTGRES_URL=<unique-db-url> pnpm vitest run test/integration/skill-command-receipt-postgres.integration.test.ts -t "atomically persists validate and publish receipts in PostgreSQL" --no-file-parallelism`、`pnpm vitest run test/integration/capability-service.test.ts -t "keeps Storage verification outside the final skill transaction"`，预期旧路径部分提交或 Storage/transaction边界不受约束。GREEN：只迁移 validate/publish；Storage I/O 必须在 transaction 外，package identity只作 prepared input。
- [x] **P4a-11 Skills withdraw/set-status mutations。**Test：同一 unit 与真实 PG suite 新增 `atomically commits withdraw and set-status receipts`、`atomically persists withdraw and set-status receipts in PostgreSQL`，表驱动 withdraw/set-status × 四故障点并断言 durable table counts、并发 takeover/旧 fence、same-command exact replay；SetSkillStatus 明确覆盖 wire 数值不变的 ACTIVE(2)↔DISABLED(5) 合法转换、重复/no-op与非法 enum/source-state 拒绝。RED：`pnpm vitest run test/unit/skill-transaction.test.ts -t "atomically commits withdraw and set-status receipts"`、`REQUIRE_REAL_INTEGRATION=1 KOKORO_POSTGRES_URL=<unique-db-url> pnpm vitest run test/integration/skill-command-receipt-postgres.integration.test.ts -t "atomically persists withdraw and set-status receipts in PostgreSQL" --no-file-parallelism`，预期旧 action-then-complete留下部分状态。GREEN：迁移最后两 mutation，并在六个方法都已过卡后删除 `rpc-handler.executeCommand` 与 `CommandReceiptStore.execute` production 定义/使用；不改 Proto 或 wire enum，不新增 RPC、attestation、alias或第二 service。
- [x] **P4a-12 删除面与文档真实性。**Test：先扩 `test/architecture/architecture.test.ts` 的 `has one receipt provider and no generic executor`，显式搜索旧 `COMMAND_RECEIPTS`、旧 MCP clock path、`result_ref`、production `.execute(` 与无 lease transaction signature；RED 应因残留失败。GREEN：移动唯一 clock 文件并更新 raw 白名单/import，更新受影响 README/INDEX/CURRENT/TECHNICAL_DESIGN/API_CONTRACT/DATA_MODEL/RELIABILITY/RUNBOOK/SECURITY；只写已实现事实，保留 P4b–P4e gap。运行 `pnpm vitest run test/architecture/architecture.test.ts -t "has one receipt provider and no generic executor"`、`rg -n "COMMAND_RECEIPTS|mcp-transaction-clock|result_ref|executeCommand" src prisma test scripts` 并人工区分历史 fixture/doc，不以盲目字符串清零替代 architecture assertion。
- [x] **P4a-13 Writer 全门。**Node 24 下运行 `pnpm format:check`、`pnpm lint`、`pnpm typecheck`、`pnpm contract:check`、`pnpm prisma:validate`、`pnpm prisma:generate`、`pnpm schema:check`、`pnpm build`、`pnpm test:unit`、`pnpm test:contract`、`pnpm test:architecture`。使用唯一 fresh PostgreSQL database 与独立 Redis namespace运行 `REQUIRE_REAL_INTEGRATION=1 KOKORO_POSTGRES_URL=<unique-db-url> KOKORO_REDIS_URL=<isolated-redis-url> pnpm test:integration`、同变量下的 `pnpm smoke`，再运行 `KOKORO_POSTGRES_URL=<unique-db-url> KOKORO_REDIS_URL=<isolated-redis-url> pnpm smoke:production`；production smoke 使用脚本自建的 IAM/Storage/provider owner stubs，明确不冒充真实外部 provider sandbox。不得重启共享服务或清他人数据；报告每张卡的 RED 失败原因、GREEN 数量、未运行项。
- [x] **P4a-14 冻结审查。**writer 停写并给 HEAD、tracked/untracked hash、绝对文件清单与每卡 checkpoint；contract_review 与 database_review 对同一最终 hash 分别 SPEC/QUALITY，任何 blocking/important 回原 writer新增最小 RED修复并重新冻结；双 PASS 后 Root 才按绝对精确路径暂存、提交，并在 child commit 上重跑完整 post-commit 门禁。

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

第三轮冻结候选（tracked `25a2774d76be3233660011eb90005d4c1ac26f1c9249505a023d0bd9c3da6aa2`、untracked manifest `b8481d5644de2cbb09a7df43704af67e63dc2e9adb20cff4133530ae4eced9b6`、full `5e611e26f3c03e5ffd177d22dc259e21146be8c3e5c20a559658890d5aa66a65`）已取得 contract_review `SPEC PASS` 与 database_review `QUALITY PASS`，两者均为 0/0/0；但 Root precommit 仍是最终放行门。Root 在 Node 24.20.0、fresh PostgreSQL `kokoro_capability_p4a_root_pre_20260910_134804_86686` 与 Redis DB 15 的真实全量中复现同一并发 installation 新 receipt 的 0 winner：一方在 receipt completion 遭 P2034、另一方 active claim 返回 in-progress，结果 1/516 failed；日志 `/tmp/kokoro-p4a-root-precommit-resume2-20260910_134804_86686.log`。这与 writer 曾披露的一次同类失败相同，不能按偶发忽略。P4a 因此仍未验收、未暂存；原 writer 先按 systematic debugging 只调查并给出根因与最小 RED，Root 确认后再授权单一 GREEN 修复和重新双审。

系统化调查已把根因定位为 PostgreSQL Serializable SSI 在并行小表上选择 status-leading receipt 索引后产生跨 identity 冲突，而 Skills 两条本地事务只有固定、同相位的 5 次/75ms 重试，多个执行者会锁步耗尽；串行聚焦 20/20 通过，16 并行进程仅 6/16 通过，32 个不同 tenant 单 caller/无 outbox 仍有 25/32 在恰好第 5 次失败，排除 duplicate claim、outbox 与 commit-readback为必要条件。临时单变量实验在保持同一 lease、每次重读 DB clock/fence的前提下加入有界随机退避并追加 5 次后，32 个独立 tenant 和 16 组同 command 均无双败，durable completed/outbox仍唯一。证据在 `/tmp/kokoro-p4a-debug-focused-loop.log` 与 `/tmp/kokoro-p4a-receipt-diag-*.json`。

#### P4a Root gate retry 修复卡（2026-09-10）

1. 先加 RED：Skills catalog 与 installation transaction 都固定前 5 次抛 P2034、第 6 次成功，断言仍是同一 receipt lease、每 attempt 重新读取 DB clock并执行 fence，且第 6 次前不落 failed；真实 PostgreSQL barrier 同时启动至少 12 个不同 tenant 的本地 fenced command，断言全部在有界预算内完成、每个 receipt completed且每个 command仅有预期0/1 outbox。保留现有同 command 双 caller断言，不改为容忍双败。
2. GREEN 只收敛 Prisma 本地可安全重放 transaction 的重试策略：receipt claim、Skills catalog、Skill installation、MCP transaction统一为 10 次上限、指数退避、full jitter与单次 delay cap；最大等待总预算必须显式受限且不超过现有 MCP 10 秒总 deadline。每次重试仍重开 Prisma transaction、重读 DB clock/current facts/fence；不在事务内 sleep，不更换 command/lease/resource identity，不把 P2034 当 commit-unknown。
3. 共享 retry 算法若独立成文件，只能放 `src/database/prisma-transaction-retry.ts`，因为它唯一负责 Prisma transaction conflict 的 attempt/delay policy；淘汰各 repository/feature 内重复的固定 sleep/attempt常量，不并入 `prisma-errors.ts` 混合错误分类与等待策略，也不新建通用 utils/retry 模块。测试用注入点只服务确定性 clock/jitter断言，不进入 Nest/wire。
4. 不改 receipt schema/index、proto/OpenAPI、业务 ID、external provider recovery 或 P4b；本片不以 `ANALYZE`、index hint、放宽成功断言、加全局互斥或增大数据库 transaction timeout遮盖 SSI。更新 CURRENT/RELIABILITY/TECHNICAL_DESIGN/RUNBOOK 的实际 retry budget与Root复现事实。
5. 聚焦 stress 至少连续三轮通过后重新跑 fresh PG/isolated Redis 的 P4a-13 全门；若仍出现一次同类 P2034 0-winner即保持失败并返回调查。重新冻结三hash、双审、Root全门，全部通过前不暂存。

#### P4a post-commit 失败调查卡（2026-09-10）

retry 修复后的最终冻结对象为 child HEAD `720acb999f6759a4fd2dca579c7aebdaaeb2d1c5`、tracked `2a5eb3a538c9235386ea943c040aaa82023f24ebe2c7a27fcddac7d5fae27e97`、untracked manifest `f50bec5a5df5ea23865c089b50a0b2cab5924b69d2882bdc7ed62149b52f0afe`、full `2b8b880bc28cdbf61387931e221cd3f6a3adb117aec418e144f7e7efc2166bcf`。contract_review 最终 `SPEC PASS`、database_review 最终 `QUALITY PASS`，均为 Blocking/Important/Minor 0；Root 在 fresh PostgreSQL `kokoro_capability_p4a_root_final_20260910_141924_93929`、Redis DB 15 上完成两轮真实全量、17/160 integration、12-tenant stress 三轮、same-command 三轮、production smoke、fresh schema/drift 与全部静态门，日志 `/tmp/kokoro-p4a-root-final-20260910_141924_93929.log`。Root 随后按精确路径提交 child `4c28d46adb5ef4c72258aceb135f487e3f81022e`（`feat(capability): fence atomic command receipts`）。

该提交尚未验收。第一次 post-commit 脚本遗漏 `REQUIRE_REAL_INTEGRATION=1`，虽然命令退出 0，但明确出现 10 个 receipt integration 与 1 个 production-entry skip，日志 `/tmp/kokoro-p4a-postcommit-20260910_142321_95877.log` 只作无效门禁记录。Root 随即在 fresh PostgreSQL `kokoro_capability_p4a_postcommit_real_20260910_142432_97449`、Redis DB 13 和 `REQUIRE_REAL_INTEGRATION=1` 下重跑；首轮 `pnpm test` 于 `allows one business executor for a concurrent failed receipt claim` 复现 0 winner：一方在 outbox upsert 遭 P2034，另一方返回 `CommandReceiptInProgressError`，结果 1/520 failed，日志 `/tmp/kokoro-p4a-postcommit-real-20260910_142432_97449.log`。因此 P4a-I 状态回到待修复，P4b 保持未授权；已提交 SHA 只是失败基线，不能作为验收提交。

原 capability_owner_p1b 先只做 systematic debugging，不改文件：以 `4c28d46adb5ef4c72258aceb135f487e3f81022e` 为基线，串行/并行重复该 failed-receipt case，区分 receipt claim、business/outbox transaction、fenced retryable mark 与第二 caller active-lease 观察的时序；核对各层是否统一使用共享 10-attempt full-jitter policy，以及 commit-response unknown 是否被误分类为已知 rollback。输出可复现次数、attempt/epoch/status/durable business/outbox/receipt 证据、根因与一个最小 RED。Root 确认后才授权 GREEN；禁止放宽 winner 断言、盲增 attempt/delay、改 schema/index/proto、扩到 provider recovery/P4b 或操作 Git。

调查已确认 24/48 个不同 tenant 的 new/failed command 在 fresh PostgreSQL 18 下均可因 relation/page SIREAD pivot 冲突耗尽 10 次；失败 attempt 全部回滚，receipt 最终不存在或回到 fenced retryable failed，business/outbox 均为 0。现有四条生产路径确实统一使用 10-attempt full-jitter helper，P2034 的 COMMIT 失败被 PostgreSQL 明确回滚，未发现 commit-response unknown 误分类。进程内 cap 4 只缓解单实例；跨进程无上界。singleton Serializable gate 的 typed 原型反而形成 retry herd：24/48 对多 client 的 new/failed 用例持续出现 3–19 个 zero-winner、20 个 active connection 和最高 19 个 row-lock waiter；Prisma timeout/外层 AbortSignal 也不能终止底层锁等待。证据为 `/tmp/kokoro-p4a-postcommit-failed-*.log`、`/tmp/kokoro-p4a-failed-receipt-diag-*.jsonl`、`/tmp/kokoro-p4a-gate-E2-*.json` 与 `/tmp/kokoro-p4a-gate-timeout.json`。

#### P4a-ADMISSION-D 跨副本 Prisma admission 设计验证卡（2026-09-10）

| 项 | 结论 |
| --- | --- |
| Owner | `kokoro-capability` 当前唯一 writer、目标 `kokoro-platform`；admission 只是本 owner 的数据库运行协调事实，不拥有 command、Skill、MCP、IAM 或 Scheduler 业务事实。 |
| 当前事实 | receipt acquisition、Skills catalog、installation、MCP 各自直接打开 Serializable transaction；有限 retry 保证原子回滚但不保证有界负载下存在 winner。Prisma pool 每进程最多 10，Redis 不参与正确性；child `4c28d46a` 为失败基线。 |
| 目标职责 | 在打开业务 Serializable snapshot 前，以 PostgreSQL DB clock 和 Prisma typed CAS 获得跨副本固定容量资格；资格 token 与业务 receipt fence 独立，确保到期/崩溃/同 owner ABA、排队取消、deadline 与 shutdown 均有稳定语义。 |
| 目录方案 | 采用现有 `src/database` 的窄 admission service/model、`RuntimeModule` 唯一 provider，并由 feature transaction 注入；不放进 Skills/MCP 任一业务模块。淘汰 A 进程内 semaphore（跨副本无效）、C 全面 ReadCommitted+CAS（需重证全部读集）、D index/ANALYZE/增 retry（概率优化）与 E Serializable singleton gate（稳定制造 P2034 herd）。 |
| 粒度 | 先做 `/tmp` 隔离 spike，再由原 writer 只更新现有 ADR-001、TECHNICAL_DESIGN、DATA_MODEL、RELIABILITY、RUNBOOK、CURRENT；同一冻结文档经 SPEC/QUALITY 双审后，Root 才新增 schema/src/test。不得直接从调查跳到实现。 |
| 依赖 | 只依赖 Prisma client、现有固定 PostgreSQL clock、Nest lifecycle 与现有 typed error mapper。禁止 Redis lock、advisory/raw lock SQL、Scheduler、provider SDK、通用 job/queue、跨仓数据库或网络 I/O 持有资格。 |
| 数据/API | 候选是固定有界的内部 admission slot：`slot_id`、永久 `lease_epoch`、成对可空 `lease_owner/lease_expires_at`；acquire/release 为短 ReadCommitted Prisma CAS，旧 epoch 不能释放新 holder。每个业务 attempt 在同一 transaction client 内先 fenced guard/renew并持有该 slot 行锁，外部调用前已释放。`command_id`、event/recovery/retirement ID、Skill `series_id/skill_id/installation_id` 与 MCP `connector_id/server_id/connection_id/authorization_id/invocation_grant` 均不复用为 slot identity；不存在附加 `grant_id` 字段，Proto/OpenAPI 不变。 |
| 删除项 | 不保留 per-feature retry/admission 双轨、进程内正确性 semaphore、singleton Serializable gate、raw SQL lock 或 provider 调用期间的 holder。统一 retry helper继续处理准入后剩余的安全 P2034。 |
| 验证 | fresh PG18、至少两组独立 Prisma client/Nest composition，new/failed×24/48不同 tenant、same-command、Skills/installation/MCP、holder pause/rollback/connection death、expired takeover/旧 epoch release、acquire/commit/release ACK unknown、取消/deadline/shutdown/pool saturation；记录实际业务 overlap、P2034、waiter、durable receipt/business/outbox。最终才跑 P4a-13、双审与 Root post-commit。 |

两名只读 reviewer 一致拒绝 A/C/D/E 并有条件推荐上述 B，但当前仍有两个设计阻断：其一，expired takeover 不能只看时间，业务 transaction 必须用同一 client fenced guard 并持 slot row lock到 COMMIT/ROLLBACK，否则暂停的旧 holder 会与新 holder并行；其二，多 slot 小表自身可能改变 SSI 冲突形态，cap 4 的旧原型不是证明。spike 必须先比较 cap 1 与 cap 4：cap 1 作为 correctness-first 默认候选，只有 cap 4 在 cold/warm 表、多 client连续压力都无 0 winner且 deadline/连接上界成立才可采用。固定 slot 集合不得由各副本自行扩容；本片可固定容量而不新增公开配置，未来扩容必须走受控设计/Schema变更。

spike 通过条件：资格在 RC transaction 外排队，wait/sleep 不持 transaction 或连接；acquire COMMIT unknown先按 token readback，未证明取得不得执行业务；一次完整 retry operation持同一 token，每个 attempt 重新用 DB clock核对/续租；总 wall-clock deadline覆盖排队、attempt与退避，slot lease严格长于该硬上限；成功 transaction内释放资格，known rollback/final failure用 fenced RC release，业务 commit unknown仍只按 receipt/current facts裁决，release结果不是业务提交证据。Nest shutdown先 stop-acquire、再 bounded drain，异常退出靠DB clock expiry。若 typed Prisma 无法证明底层等待可取消，acquire只用非阻塞条件CAS+事务外轮询，不能等待锁；业务 guard的数据库 transaction hard timeout与lease关系必须在文档中给出可验证不等式。P4b继续未授权。

spike 在 `/tmp/kokoro-p4a-admission-b` 与独立 fresh DB 完成并选择 correctness-first `capacity=1`。Prisma `updateMany` 在 RC 确定性竞争中会让两位申请者都报告成功，禁止用于 admission CAS；带唯一 `slot_id` 加旧 owner/epoch/expiry 扩展谓词的 typed `update()` 由 P2025 表示输家，5/5 轮保持单赢家。capacity 4 在 120 个 command 中仍出现 8 个 zero-winner 和 11 个最终 P2034，拒绝；capacity 1 则在单进程 new/failed 各 48、多进程 8 clients/48 failed、Skills/installation/MCP 混合 48 与 100 次 warm acquire/guard/release 中全部通过，跨进程实际 business overlap 恒为 1。日志以 `/tmp/kokoro-p4a-admission-b/*.log` 为证。

设计固定以下不可配置初值与不等式：`lock_timeout=10ms < PostgreSQL transaction_timeout=2s < admission operation deadline=8s < admission lease=12s < command receipt lease=30s`。数据库 server timeout 通过 PrismaPg session options 施加；业务 transaction 必须在同一 Prisma client 内以 guard/renew 为第一项状态操作，并持 slot row lock到 COMMIT/ROLLBACK。短 acquire attempt 在每进程内串行，只是减少连接/轮询，不承担正确性；等待、退避和取消均在 transaction 外，数据库锁等待最多由 10ms lock timeout收敛。timeout 分类、projection/startup查询影响、连接恢复和所有绕过 Serializable 入口均需 RED。cap 1 当前吞吐证据约为 15ms fixture 35 commands/s、40ms多进程 fixture 17.5/s；公平性非 FIFO，8秒耗尽 fail closed。未来增容必须重新走 ADR/schema与 cold/warm、多副本 SSI 全矩阵，capacity 4 当前已满足拒绝条件。

P4a-ADMISSION-D 现授权同一 capability_owner_p1b 仅更新 child 既有 `docs/ADR/ADR-001-nestjs-prisma.md`、`docs/TECHNICAL_DESIGN.md`、`docs/DATA_MODEL.md`、`docs/RELIABILITY.md`、`docs/RUNBOOK.md`、`docs/CURRENT.md`；不得改 schema/generated/src/test/package/env/proto/OpenAPI 或 Git。文档必须写清固定slot初始化/校验、typed update CAS、DB-clock/epoch/expiry/NULL不变量、acquire/guard/renew/release/unknown outcome、数据库timeout不等式、8秒总deadline、Nest stop-acquire/drain、所有 transaction入口、网络不持slot、指标/SLO/runbook、cap 1吞吐代价与增容退出路径。冻结后由 contract_review/database_review 对同一 hash分别作 SPEC/QUALITY；双 PASS 后 Root 才提交文档并拆 P4a-ADMISSION-I 的逐RED实现卡。

首个文档候选冻结 tracked/full `641a4dab0345a3e5616b45b9c090a168729a05a499d980125c0e84654052c4c8`、无 untracked。contract_review 为 `SPEC FAIL`（Blocking 2 / Important 2），database_review 为 `QUALITY FAIL`（Important 3 / Minor 1）；候选不提交。原 writer 只修六文档：

1. 先用真实 Prisma 7.10/adapter-pg fixture固定 holder 争用下 typed unique update 的 lock-timeout error shape；只允许 admission acquire 将精确的 PostgreSQL lock-timeout 分类为普通 contention 并退出 RC transaction 后 poll，P2025仍只表示旧谓词 CAS 输家。guard/release/业务SQL、非 lock-timeout 和畸形错误不得宽吞。
2. receipt claim 在 admission 前及排队期间做无副作用、identity-bound authoritative inspect；已存在 active lease 必须优先维持现有 `ABORTED`，completed/terminal/expired/external-unknown也按既有typed状态裁决。只有 missing、已过期 local processing或due local failed需要slot；取得slot后在transaction内再次读取并裁决。无active receipt的全局容量耗尽才是`UNAVAILABLE`。
3. effective deadline固定为 `min(admissionStart+8s, caller existing absolute deadline)`；caller取消为`CANCELED`、caller deadline为`DEADLINE_EXCEEDED`、内部8秒预算耗尽才为`UNAVAILABLE`。明确Prisma pool/connection checkout与adapter网络黑洞不受server lock/transaction timeout单独约束：实现需固定并验证短pool/maxWait/query/connection预算；caller边界可返回但晚到Promise不得启动新business。late acquire success只fenced release，late business/COMMIT仍按receipt/current facts readback，底层清理和客户端响应deadline分开，不以Promise race冒称query取消。
4. 新spike揭示现有 `markRetryableFailure()` 是 RC `updateMany` fence，同样可能在等待completed commit后按旧选中ID把completed写回failed。P4a-ADMISSION-I必须把它改为复合唯一receipt identity+完整owner/epoch/status/expiry/SQL-NULL扩展谓词的typed `update()`，P2025返回false；增加completed-vs-failure-mark固定时序真实PG RED。其他Serializable业务CRUD不机械替换。
5. 启动配置把command receipt lease下界收紧为30秒，保留当前30秒默认及既有上界；非法低值RED并同步env/runbook，不能只依赖默认值满足`slot lease 12s < receipt lease`。DATA_MODEL顶部改为`4c28d46a`已提交但P4a未验收。旧Redis“request admission”统一改称availability/readiness gate，明确不拥有transaction capacity/lease/fence/recovery。

修复后重新冻结六文档三hash并由相同两名 reviewer双审；仍不得改schema/src/test/package/env或Git。P4b保持未授权。

#### P4a-ADMISSION-D 最终验收与 installer atomicity spike（2026-09-10）

六文档最终冻结 tracked/full hash 均为 `d67f52354611baf1ecb5d7c08608b7929923a3f139879731249c0148e7397c60`，无 untracked；contract_review 的最终 `SPEC PASS` 与 database_review 的最终 `QUALITY PASS` 均为 Blocking/Important/Minor 0。Root 在同一冻结对象上复跑 `pnpm format:check`、`pnpm lint`、`pnpm typecheck` 与范围 diff 检查通过，随后提交 child `394dce695083b7ea76ced7004679a5c383a47981`（`docs(capability): design transaction admission`）；提交后同三项静态门、范围 diff 与 clean-worktree 检查再次通过。该提交只验收 admission 设计，不代表 `4c28d46a` 的 P4a 实现已恢复验收，也不授权 P4b。

实施前新发现一个 installer 原子性阻断：现有 `scripts/apply-schema.ts` 由 node-postgres `PoolClient` 开启事务并执行 Prisma migrate diff 生成的 DDL，而 PrismaPg 的公开 API 不能把 typed Prisma client 绑定到该外部 `PoolClient` 事务；固定 `TransactionAdmissionSlot` 又必须由 installer 用 typed Prisma 初始化，并与 fresh schema 安装保持单事务原子性。不得改成手写 `INSERT`、runtime create-if-missing、两阶段 DDL+seed、adapter 私有连接或未经验证的分号切分。

当前只授权 capability_owner_p1b 做 `/tmp` 隔离 spike，不修改 workspace、Git、共享数据库或共享 Redis：

1. 基于 child `394dce695083b7ea76ced7004679a5c383a47981` 的临时副本生成带 `TransactionAdmissionSlot` 的 Prisma client 与 canonical DDL，在 fresh PostgreSQL 上验证 Prisma 7.10 + adapter-pg 的 interactive `ReadCommitted` transaction 能否执行完整 generated DDL 并在同一事务内调用 typed `transactionAdmissionSlot.create`。
2. 若 `$executeRawUnsafe(generatedDdl)` 不接受多 statement，必须找出对受限 Prisma migrate-diff 输出可靠、可验证且不以 naive `split(";")` 猜 SQL 边界的执行方式；不得引入第二份手写 schema 或使用 adapter 私有 `PoolClient`。
3. 同一 Prisma transaction 内验证 installer advisory lock、nonempty/schema safety check、generated DDL、typed fixed-row create 与 post-create invariant check的可组合性；installer client 不继承 runtime 的 2 秒 query/transaction timeout。
4. 用 fault injection 证明 DDL 中点、typed create 前后、最终 invariant check 与 commit 前失败都回滚 schema/slot；验证并发 installer 单一成功、进程终止后的可恢复状态，以及 COMMIT acknowledgement unknown 的可判定/重跑语义。若 PostgreSQL DDL 事务在强制进程终止下只留下全有或全无，也必须以 catalog/typed readback记录，而非口头假设。
5. schema checker 还必须拒绝 fixed slot 缺失、多行、`slot_id` 非约定常量、owner/expiry 单边 NULL、held row 的 epoch 非正数等损坏；spike只报告事实、命令、数据库名与 `/tmp` 产物，不提前写 production code。

spike 结论先回 Root。只有证实一条基于公开 Prisma API 的原子安装路径后，Root 才补充六文档的 installer 细节并再次冻结双审，然后拆 P4a-ADMISSION-I 的逐 RED 实施卡。若原子路径不成立，则先回到设计门比较可恢复 installer 协议，不以兼容层或 runtime 自愈绕过。Skills 与 MCP 的 identity 继续锁定：Skill 家族 `series_id`、不可变 revision `skill_id`、task selector `skill:<skill_id>`、安装生命周期 `installation_id`；MCP task reference `connector_id`，并分别保持 `server_id`、`connection_id`、`authorization_id` 与 wire `invocation_grant`。provider key、URL、selector、tool name 不得冒充资源 ID；不存在附加 `grant_id` 字段或 alias；`command_id` 只作幂等身份，event/recovery/retirement/delivery 各有独立 ID。Manus 对齐事实源仍是 `docs/MANUS_API_ALIGNMENT.md` 及已核对的 `skill.list`、`connector.list`、`task.create`、Connectors API 文档。

独立 contract 审查已确认上述主要 typed identity 边界与实现一致，但发现 child `docs/API_CONTRACT.md` 和 `docs/TECHNICAL_DESIGN.md` 仍把 wire `invocation_grant` 误写为另一项 `grant_id`。该项为 Important 文档漂移：P4a-ADMISSION-I 前必须由原 writer 在 installer 设计补充时一并改成“`invocation_grant`（MCP invocation decision）”，明确不新增 SQL/wire `grant_id` 或兼容 alias，并加入 architecture/contract assertion 固定 Proto/OpenAPI digest、`skill:<skill_id>` exact reference、installation/current revision不互换。机器契约与现有实现不因文档修订而改变。

#### P4a-ADMISSION-INSTALLER-SPIKE 结论与文档补充授权（2026-09-10）

只读 spike 在 child `394dce695083b7ea76ced7004679a5c383a47981`、Node 24.13.0、Prisma/client/adapter-pg 7.10.0、pg 8.16.3 与 PostgreSQL 18.4 上通过；child 前后 clean。证据目录为 `/tmp/kokoro-p4a-installer-atomicity-20260910-160315-16069`，报告 SHA-256 `5020bb26a9782e9d364c9f42fa4a40a2a34c4e998b205e3e3ef23e10e8f37abe`，唯一 fresh DB 为 `kokoro_capability_p4a_installer_atomicity_20260910_160315`。Root 已复核报告、JSON 结果、DDL hash 与 child clean 状态；独立 database_review 结论为 Blocking 0 / Important 2（实施前验证门）/ Minor 0。

验证事实：9,537 bytes、258 lines 的原样 canonical generated DDL（SHA-256 `2b98d7950bb9c70f7dfb26ffa95b8088a050a210a3457dd1269188e6bcd2c861`）可由 public Prisma interactive ReadCommitted transaction 中单次 `$executeRawUnsafe` 执行，并在同一 transaction 以 typed `transactionAdmissionSlot.create` 初始化固定行；结果为9 tables、12 enums、30 indexes与唯一`slot_id=1/lease_epoch=0/owner+expiry SQL NULL`。DDL中点、create前后、invariant后与commit前五个故障点均回滚为0/0/0；并发installer 10/10为一方安装、一方在advisory lock后识别authoritative exact state；partial schema fail closed。SIGKILL 3/3留下全无并可重装。透明proxy各3轮证明commit发送前断链与commit已生效但ACK丢失产生相同transport error，只有fresh connection readback能区分empty与exact installed。七类fixed-row损坏全部拒绝。installer client的transaction/statement timeout为0且2.3秒事务探针通过，未继承runtime 2秒预算。

由此选定公开 Prisma API 的单事务 installer 路径，不引入SQL splitter、手写seed、adapter私有连接、两阶段补行或runtime self-heal。现续派原 capability_owner_p1b 仅修改 child 既有：`docs/ADR/ADR-001-nestjs-prisma.md`、`docs/TECHNICAL_DESIGN.md`、`docs/API_CONTRACT.md`、`docs/DATA_MODEL.md`、`docs/RELIABILITY.md`、`docs/RUNBOOK.md`、`docs/SECURITY.md`、`docs/CURRENT.md`；不得改 schema/generated/src/scripts/test/package/env/proto/OpenAPI 或 Git。必须收敛：

1. 事务外生成唯一 canonical Prisma DDL；installer-only PrismaClient/PrismaPg不复用runtime timeout options；单一 ReadCommitted transaction 依序执行search path、cast为受支持标量的transaction advisory lock、authoritative nonempty判定、完整受信DDL单次执行、typed fixed-row create、完整schema+slot invariant与Prisma-managed commit，最终不依据`$executeRawUnsafe`返回0或对象count冒充schema正确。
2. 版本绑定完整multi-statement路径为 Prisma/client/adapter-pg 7.10.0 + pg 8.16.3；依赖升级必须重跑fresh install、mid-DDL rollback、typed seed、并发与ACK-loss。generated DDL必须拒绝transaction-control/COPY等超出已验证边界的语句；本切片不预造parser。
3. installer state matrix：empty才执行DDL；exact canonical schema+合法fixed row在并发等待、重跑或commit-unknown readback中收敛为成功/already-present；partial、额外对象、schema drift、slot缺失/额外/非法ID、owner-expiry单边NULL、非法epoch、unreadable均fail closed且不自动补行/修表。修改旧“任何nonempty一律拒绝”的绝对表述，仅为exact current canonical postcondition开放幂等识别。
4. callback-known failure依赖事务回滚；transport/COMMIT acknowledgement unknown不按error shape猜结果，必须用fresh installer client authoritative readback：empty可重试、exact视为已完成、partial/corrupt/unreadable为unknown/fail closed。slot本身不证明任意未来migration成功，完整schema checker/digest/object invariant才是证据。
5. installer有独立有界transaction/checkout/connection预算且不使用runtime 2秒transaction/query配置；运行期仍从不create-if-missing。文档列出DDL中点、create前后、invariant、commit前、concurrent installer、SIGKILL、ACK-loss与corruption作为实现RED。
6. 全部八文档把不存在的`grant_id`改为wire `invocation_grant`（概念类型MCP invocation decision）；保留`mcp-grant:<uuid-v4>`为值格式描述，不新增SQL/wire字段或alias。继续固定Skill `series_id/skill_id/source_ref=skill:<skill_id>/installation_id`、MCP `connector_id/server_id/connection_id/authorization_id/invocation_grant`、command/event/recovery/retirement/delivery typed identity不互换及Manus list/discover→opaque typed reference原则。writer发现原范围外`docs/SECURITY.md:73`尚有同一旧术语后先停在边界，Root据此把该既有文件加入唯一允许范围；除此之外不得扩大。

writer 只跑文档格式、lint/typecheck与范围diff，冻结HEAD/tracked/untracked/full hash。contract_review 与 database_review 对同一冻结对象分别作 `SPEC`/`QUALITY`；两者都须重新检查installer语义和`invocation_grant`零wire变更。双PASS后Root才提交文档并编写P4a-ADMISSION-I逐RED实现卡；P4a实现和P4b仍未授权。

首个补充候选冻结为 child HEAD `394dce695083b7ea76ced7004679a5c383a47981`、tracked/full `4f361154c8744a30529a8beb9480c243a9a4231e46b9ff8e2444f03c98a90f20`、untracked `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`。database_review 为 `QUALITY PASS` 0/0/0；contract_review 为 `SPEC FAIL`（Blocking 0 / Important 1 / Minor 0）：`docs/ADR/ADR-001-nestjs-prisma.md` 的 raw SQL allow-list 遗漏了同文已强制的 installer 固定 `SET LOCAL search_path = public`。原 writer 只在该 ADR allow-list 补入“installer固定、无请求输入的SET LOCAL search path”并明确同一 architecture allow-list；不得借机修改其他内容。修复后重跑文档门、冻结新hash并让两名 reviewer对同一对象重新双审，首轮QUALITY PASS不跨冻结沿用。

修复后的最终文档候选冻结为 child HEAD `394dce695083b7ea76ced7004679a5c383a47981`、tracked/full `efbd5258208d5fa9d6057e6fcbd7812ad2c2930a8068e85778a2b67b3d1de8e8`、untracked `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`；contract_review `SPEC PASS`、database_review `QUALITY PASS`，两者均为 Blocking/Important/Minor 0。Root 在同一冻结对象上复跑 `pnpm format:check`、`pnpm lint`、`pnpm typecheck` 与 diff/range 检查通过，提交 child `122a3a5bf09792c7ef11a52de05188f444678d6e`（`docs(capability): define atomic admission installer`）；post-commit 同三门、精确8文件commit scope与clean工作树再次通过。该提交验收设计与身份术语，不代表production schema/installer/admission已实现。

### P4a-ADMISSION-I 具体放置与实施门（2026-09-10）

| 项 | 结论 |
| --- | --- |
| Owner | 当前 `kokoro-capability`、目标 `kokoro-platform`；数据库transaction admission是owner内部运行协调能力，唯一writer为 capability_owner_p1b，Root独占Git。Skills、MCP、IAM、Storage与Scheduler事实owner不变。 |
| 当前事实 | child `122a3a5b`；P4a业务/receipt fence提交`4c28d46a`仍为失败基线。四类入口可直接开Serializable；schema无slot，installer由pg持有事务，runtime client无10ms/2s session硬限，receipt lease仍接受1ms，`markRetryableFailure`仍为RC `updateMany`。Proto/OpenAPI与Manus alignment不变。 |
| 目标职责 | 固定capacity=1的Prisma singleton admission；atomic fresh installer；同一Nest provider；所有本地Serializable attempt先guard/renew并持slot row lock；有界deadline/cancel/drain；receipt优先状态、Skills/MCP身份和外部网络边界保持。 |
| 目录方案 | coordinator port/typed error放`src/application`，Prisma实现与固定client policy放现有`src/database`；不用Skills/MCP目录承载共享slot。installer/catalog checker放`scripts`并由`apply-schema`与`check-schema`复用；不用runtime provider或第二SQL schema。测试进入既有unit/integration/architecture/smoke。淘汰把实现塞进receipt repository（会让MCP/Skills transaction反向依赖receipt）和新建单文件目录。 |
| 粒度 | 允许新增`src/application/transaction-admission.ts`（纯port/type）、`src/application/transaction-admission.error.ts`（typed错误）、`src/database/prisma-transaction-admission.ts`（唯一有状态coordinator）、`scripts/canonical-schema-state.ts`、对应测试；其余扩展现有文件。不建`admission/`或`installer/`空层。 |
| 依赖 | application只定义opaque token/operation/result与typed errors，不import Prisma/Nest/Connect；database实现依赖generated Prisma与现有clock/retry。feature只依赖application port；RuntimeModule唯一装配。禁止Redis/advisory/raw business lock、provider SDK、网络I/O、进程内semaphore承担正确性。installer固定raw例外受architecture allow-list。 |
| 数据/API | 只加`transaction_admission_slot` canonical Prisma model和generated client；固定行由installer typed create。无tenant、FK/CHECK、proto/OpenAPI或新配置。`slot_id`/owner/epoch不复用业务ID；wire只有`invocation_grant`，不存在`grant_id`。receipt lease合法范围收紧为30,000–300,000ms。 |
| 删除项 | 删除pg-owned installer transaction、所有绕过共享admission的production Serializable入口、重复feature admission/retry包装和任何临时splitter/self-heal。保留pg仅作为Prisma adapter底层与测试/catalog工具；不机械替换普通业务CRUD。 |
| 验证 | 每卡先RED后GREEN；Prisma validate/generate/schema drift；真实PG18 installer faults、CAS/fence/timeout、同进程及多进程cold/warm压力；isolated Redis；unit/contract/architecture/build/smoke/production smoke；同冻结双审与Root post-commit。 |

#### P4a-ADMISSION-I RED → GREEN 实施卡

共同约束：每卡先新增最小、命名明确的RED并运行到“因本卡能力缺失而失败”，记录命令与错误后才写GREEN；不得先改production再补测试。generated Prisma只由`pnpm prisma:generate`产生。所有deadline使用单调时钟裁决wall budget、PostgreSQL clock裁决lease；测试可注入clock/random/wait，但测试钩子不进入Nest/wire。一个本地command从initial claim到最终business commit不得在中间释放slot让另一个command的Serializable claim/transaction插入；external flow在provider/Storage/IAM/SecretStore/declaration网络前必须释放，下一本地phase重新acquire。P4b provider reconcile、P4c retirement、P4d delivery、P4e GC和P5均不在本片。

I-5验收后的编译依赖复核表明：若直接把root-only `claim()`改成transaction-bound claim，Skills catalog、Skill installation与MCP三类消费方必须同时迁移；保留旧claim、新增optional参数/alias或让permit逃出`TransactionAdmissionPort.run()`都会形成双协议或破坏I-4/I-5生命周期。因此先以I-6A完成唯一Nest provider的编译前置；I-6至I-9作为一个编译原子wave，各自保留命名RED/GREEN checkpoint，但中间不冻结、不提交、不宣称单卡生产完成；三surface都删除旧claim消费面并全量typecheck/test通过后才共同冻结双审。

- [x] **ADMISSION-I-1 canonical slot schema。**先在`test/architecture/prisma-persistence.test.ts`写`models exactly one internal transaction admission slot`，只验证canonical Prisma model与生成DDL shape的字段、类型、NULL/default、table map及无tenant/relation/index/FK/CHECK；运行聚焦命令应因model/DDL table不存在失败。GREEN只改`prisma/schema.prisma`并生成`src/generated/prisma/**`：`TransactionAdmissionSlot`映射`transaction_admission_slot`，`slot_id Int @id`、owner nullable varchar、epoch non-null BigInt default0、expiry nullable timestamptz(3)，无tenant/relation/index/FK/CHECK。运行`pnpm prisma:validate && pnpm prisma:generate`并重跑本卡全部RED至GREEN；不得手写generated。fixed row初始化、缺失/损坏drift与真实installer行为全部留给I-2，不在本卡预期通过。
- [x] **ADMISSION-I-2 public-Prisma atomic installer/checker。**在`test/integration/schema-installer.integration.test.ts`先写`atomically installs canonical schema and typed slot`、`recognizes only exact installed state`、`rolls back every installer fault`、`recovers commit acknowledgement ambiguity`与`serializes concurrent installers`，覆盖5故障点、partial/extra/drift、七类slot损坏、SIGKILL、commit发送前断链/ACK吞掉；在architecture test先写固定raw allow-list/禁止`split(";")`、手写slot INSERT和adapter private client。RED必须证明旧pg-owned installer/无slot失败。GREEN改`scripts/apply-schema.ts`、`scripts/check-schema.ts`并允许新增唯一复用文件`scripts/canonical-schema-state.ts`：transaction外生成并校验trusted DDL；installer-only PrismaPg/PrismaClient；一个ReadCommitted transaction执行固定SET LOCAL、cast advisory lock、state check、完整DDL单次执行、typed create、同transaction完整catalog+slot invariant；finally disconnect。success/transport unknown都用fresh client执行完整postcondition，empty重试、exact收敛、其他fail closed；不能用return0/counts代替schema diff/invariant。安装budget独立有界且不继承runtime2s。真实fresh DB聚焦命令至少连续三轮通过。
- [x] **ADMISSION-I-3 runtime Prisma policy与配置门。**先扩`test/integration/production-composition.integration.test.ts`的runtime config表，RED固定receipt lease `29_999`拒绝、30,000/300,000接受；新增真实PG`applies bounded runtime Prisma session policy`，以实际锁等待和长事务证明10ms lock/2s transaction/query、pool10、connection5s、interactive maxWait1s生效，production不加SHOW。GREEN改`src/config/runtime.ts`、`src/database/prisma-client.ts`及必要test fixture；把固定常量集中在database client policy，不做环境配置，不影响installer client。
- [x] **ADMISSION-I-4 opaque port、typed errors与RPC映射。**先建`test/unit/transaction-admission.test.ts`的契约RED，固定：capacity不在port/config暴露；opaque token只有slot/owner/epoch；operation输入携带signal与可选caller absolute deadline；typed错误分别表示cancel、caller deadline、内部耗尽/stop-acquire、corrupt/overflow/ownership lost。GREEN精确新增`src/application/transaction-admission.ts`和`src/application/transaction-admission.error.ts`，只定义无状态port/type/error，不import Prisma/Nest/Connect；扩`src/rpc/rpc-handler.ts`做`CANCELED`/`DEADLINE_EXCEEDED`/`UNAVAILABLE`/`INTERNAL`/`ABORTED` typed映射，禁止message matching。本卡不实现queue、timer、in-flight或drain，相关行为归唯一数据库coordinator I-5。
- [x] **ADMISSION-I-5 Prisma acquire/guard/release与operation lifecycle。**在`test/unit/transaction-admission.test.ts`继续先写有状态RED：effective deadline=`min(start+8s, caller absolute deadline)`；queue等待不持transaction/connection；所有已启动Promise同步登记并吸收late resolve/reject，late token只release；`stopAccepting`与`drain`幂等。在新`test/integration/transaction-admission-postgres.integration.test.ts`先写RED：free acquire、unexpired poll、DB-clock expired takeover、P2025 CAS loser、精确P2039/model/postgres55P03 acquire contention、畸形shape fail closed、epoch overflow、same-owner ABA、旧epoch renew/release、新epoch takeover、acquire/release ACK unknown；`guard/renew is the first state access and holds the row lock through commit`同时写业务fixture证明无overlap。GREEN新增唯一有状态实现`src/database/prisma-transaction-admission.ts`：acquire为短RC typed unique `update()`旧值CAS，事务外poll/full-jitter；每进程只串行短acquire attempt作为pool优化；guard/release同样unique extended predicate，guard使用同一business tx+DB clock、续12s并持锁，success同tx清owner/expiry；operation lifecycle、deadline、late settlement与drain均在此实现。只有acquire完整P2039 shape与P2025为contention；guard/release任何异常fail closed。禁止`updateMany`/`updateManyAndReturn`/raw lock/Redis。
- [x] **ADMISSION-I-6A RuntimeModule唯一admission provider前置。**先扩`test/integration/production-composition.integration.test.ts`或既有Nest fixture的命名RED，固定新injection token只由`RuntimeModule`使用唯一`PRISMA_CLIENT`构造一个`PrismaTransactionAdmission`、并对Skills/MCP导出同一reference；不连线feature、不开第二listener/client、不提前改readiness/shutdown。GREEN只允许`src/config/injection-tokens.ts`、`src/runtime.module.ts`和该测试/必要Nest fixture；本卡单独typecheck/test、冻结双审与提交。
- [x] **ADMISSION-I-6 receipt admission contract、transactional claim与failure-mark race。**作为I-6至I-9编译原子wave的共享contract checkpoint，先扩`test/unit/command-receipt.test.ts`及真实`test/integration/command-receipt-postgres.integration.test.ts`：授权/digest后排队前和每poll使用同一PostgreSQL snapshot+DB clock无副作用重读；active processing优先ABORTED，external stale/failed/unknown为UNAVAILABLE且epoch/attempt不变，completed/terminal/expired保留现状，只有missing/stale local/due local返回既有`TransactionAdmissionPreAcquireResult`的`acquire`。修改`src/application/command-receipt.ts`、`command-receipt.error.ts`与现有`src/infrastructure/repository/capability/prisma-command-receipt.repository.ts`：root coordinator只提供`decideAdmission`、`inspect`和`markRetryableFailure`；transaction-bound port的`claim`在每次Serializable attempt内按`guard → DB clock → receipt/current facts`重裁决，返回既有claimed/replayed typed result，不复制第二套state/outcome union。同卡将RC failure mark改为复合唯一typed `update()`，where包含tenant+command、digest/operation、processing owner/epoch、DB-clock未过期和SQL NULL；只捕获该update的P2025，退出transaction后在fresh snapshot readback再返回false或安全typed错误。真实定序固定winner持row lock→failure mark已发出并确认等待→winner completed commit→loser P2025 false→fresh readback completed不覆写；另验runtime 10ms P2039不得冒充false。删除root-only `requiredRootDatabase/claim/acquireExisting`，不保留optional/alias/兼容adapter；不改receipt/wire identity，不把slot状态当commit证据。
- [x] **ADMISSION-I-7 Skills catalog同token闭环。**作为同一原子wave的Skills checkpoint，先在`test/unit/skill-transaction.test.ts`与`test/integration/skill-command-receipt-postgres.integration.test.ts`写RED：六mutation的`TransactionAdmissionPort.run(preAcquire=receipts.decideAdmission)`包住initial transactional claim→所有P2034 attempts→business/outbox/codec/completion，permit不逃出run，每attempt第一项guard，success同tx release；known rollback/final failure由coordinator fenced release，commit unknown只按receipt/current facts；排队cancel/deadline不执行业务，Storage validation在acquire前且无网络持slot。GREEN最小改`src/modules/skills/skill-rpc.service.ts`、`skill-transaction.ts`、`skills.module.ts`及必要context/port fixture，由I-6A token传递同一coordinator、Connect signal/absolute deadline与permit；彻底删除该surface旧root claim路径，保持`series_id/skill_id/source_ref=skill:<skill_id>/installation_id`和六方法request binding/replay校验不变。
- [x] **ADMISSION-I-8 Skill installation同token闭环。**作为同一原子wave的installation checkpoint，先扩`test/unit/skill-installation-transaction.test.ts`与真实`test/integration/skill-installation.integration.test.ts`，RED覆盖三mutation、同一permit跨retry、每attempt guard-first、成功transaction release、failure mark+coordinator release、commit unknown、same-command双caller、cancel/deadline及IAM/Storage在slot外。GREEN最小改`skill-installation.transaction.ts`、`skill-installation.rpc.ts`、`skills.module.ts`与fixtures，删除该surface旧root claim；authorization与exact source/current install校验保持，`installation_id`不变且永不成为task Skill reference。
- [x] **ADMISSION-I-9 MCP local/external phase闭环。**作为原子wave的最后checkpoint，先扩`test/unit/mcp-transaction.test.ts`、`test/unit/mcp-p3a.test.ts`、`test/integration/mcp-p3a-postgres.integration.test.ts`与必要P3b integration：local mutation的同一run持permit跨transactional claim→final tx；Begin/Complete external initial claim在同tx release并让run返回后才调provider/SecretStore/declaration，bind/finalize/reject各自新run/acquire并同tx release；网络期间真实0 held；all mutation handler传播`context.signal`与既有10s absolute deadline；cancel/deadline/late promise/commit unknown保持typed。GREEN最小改`mcp-transaction.ts`、`mcp.ports.ts`、`mcp-rpc.runtime.ts`、`mcp-rpc.service.ts`、三个feature RPC factory及`mcp.module.ts`/fixtures，删除`claimCommand/runClaimedCommand/completeClaimedCommand/markCommandFailed/failClaimedCommand`旧optional协议与runtime completeness fallback。I-9后才对I-6至I-9共同跑全量门、冻结双审和单一业务切片提交。17 RPC、Proto/OpenAPI digest、`connector_id/server_id/connection_id/authorization_id/invocation_grant`及`mcp-grant:<uuid-v4>`值格式零变化，不出现`grant_id`。
- [x] **ADMISSION-I-10 readiness、shutdown与同实例生命周期。**I-6A已提供唯一RuntimeModule coordinator；本卡先扩`test/integration/production-composition.integration.test.ts`、`test/unit/runtime-resources.test.ts`、`test/unit/runtime-lifecycle.test.ts`与`test/smoke/production-entry.test.ts` RED：所有四入口仍取得同一reference；Prisma连接后、listener前验证fixed slot；ongoing readiness识别corruption；shutdown顺序严格`stop-acquire → queued callers settle → admitted/business+HTTP/RPC bounded drain → listener/resources close`，重复close同Promise；startup失败逆序清理。GREEN改`src/runtime.module.ts`、`src/database/runtime-resources.service.ts`、`src/main.ts`、必要`app.module.ts`/tokens/health；不得创建第二listener、第二Prisma client或Redis lock，日志/快照不含owner token/payload。
- [x] **ADMISSION-I-11 跨副本压力、timeout与绕过门。**新增/扩真实PG integration与architecture RED，至少覆盖：2+独立Prisma/Nest composition；new/failed各24/48不同tenant；same-command双caller；Skills catalog/installation/MCP混合48；warm100；实际business overlap恒1；0 zero-winner；P2034安全重试后仍同permit；holder pause/rollback/connection death/12s expiry；pool饱和、maxWait、connection/query黑洞、late settle/reject零unhandled且pool恢复；任何production Serializable入口无admission guard即architecture失败。GREEN只修发现的本片实现缺口，不增attempt/deadline/capacity、不放宽断言。stress连续三轮，记录吞吐只作fixture证据非SLO。

#### ADMISSION-I-11 放置门与执行卡（2026-09-11）

| 项 | I-11 结论 |
| --- | --- |
| Owner | `kokoro-capability` 的 runtime transaction admission；目标仍为 `kokoro-platform`。唯一writer为 capability_owner_p1b，Root独占Git。Skills/MCP只作为已接入的业务压力面，不改变其事实owner。 |
| 当前事实 | child `8c26e6cfa850e9b3bb2a3724ee48f81b0ce2e46a` clean；I-1至I-10已验收。现有 `transaction-admission-postgres.integration.test.ts` 证明单coordinator机制，Skills catalog、installation、MCP与production composition各有独立行为测试，但尚无跨surface、跨Nest composition的统一overlap/winner/timeout压力证据。 |
| 目标职责 | 本卡只建立真实PostgreSQL并发、超时、故障恢复与production绕过门；吞吐数据仅是fixture证据，不是SLO。RED若证明生产缺口，先向Root报告最小变化面，Root补充本卡后才进入GREEN。 |
| 目录方案 | 采用新建单一 `test/integration/transaction-admission-stress.integration.test.ts` 聚合跨surface/跨composition压力；相比继续扩充机制级 `transaction-admission-postgres.integration.test.ts`，可避免把单coordinator语义与端到端压力生命周期混成一文件。architecture绕过断言扩展既有 `test/architecture/architecture.test.ts`，不新建第二architecture入口。淘汰把同一overlap/winner fixture分别复制进Skills与MCP测试。 |
| 粒度 | 新文件只有一个变化原因：证明所有已接入mutation共享capacity=1 admission及其故障恢复；近期I-12全门会继续复用。共用测试fixture仅在至少两个测试文件确有复用时扩展既有 `test/fixtures/**`，不新建单文件目录。 |
| 依赖 | 测试只通过既有Nest/RuntimeModule/public provider与真实Prisma入口组装2+独立composition；不增加production test hook，不以进程内counter/semaphore替代数据库事实。architecture静态分析沿现有解析/allow-list机制，禁止按方法名字符串造成误报豁免。 |
| 数据/API | 使用唯一fresh隔离PostgreSQL database和独立Redis namespace；不改Prisma schema、Proto、OpenAPI、typed identity或wire digest。Skill固定 `series_id`/`skill_id`/`source_ref=skill:<skill_id>`/`installation_id`；MCP固定 `connector_id`/`server_id`/`connection_id`/`authorization_id`/`invocation_grant`，值格式保持 `mcp-grant:<uuid-v4>`，不存在 `grant_id`。`command_id`仍只表示命令幂等身份。 |
| 删除项 | 初始无production删除项；若RED暴露重复fixture，只在同一切片删除被新共享fixture完全替代的测试代码，不保留两套压力算法。 |
| 允许文件 | 可新增 `test/integration/transaction-admission-stress.integration.test.ts`；可修改既有 `test/integration/transaction-admission-postgres.integration.test.ts`、Skills/MCP相关integration、`test/architecture/architecture.test.ts`及必要既有test fixture。未预授权production、schema/generated、package/lock、Proto/OpenAPI、文档或其他仓写入。 |
| 验证 | 先取得命名RED；GREEN后聚焦unit/architecture/integration，stress在同一fresh DB上连续三轮；再执行Node 24全静态门、全真实integration、smoke与production smoke。每轮记录winner、zero-winner、最大business overlap、late rejection/unhandled、pool恢复和fixture吞吐；验证后确认PostgreSQL/Redis隔离资源残留为0。 |

I-11 首个architecture RED在child `8c26e6cfa850e9b3bb2a3724ee48f81b0ce2e46a`以TypeScript AST逐个检查production `$transaction(... Serializable)` callback，且不接受方法名或字符串豁免。命名门 `guards every production Serializable transaction through admission` 实际发现三个绕过：`src/modules/skills/skill-transaction.ts` 的optional fence分支、`src/modules/skills/installation/skill-installation.transaction.ts` 的public `run()`、`src/modules/mcp/mcp-transaction.ts` 的generic retry；exit 1，1 failed / 16 skipped。writer按范围门停写，dirty仅该architecture RED，tracked hash `376c4a31f2666b0481ad40c8853d508b045854ae7160156bb1a37c681d319732`。

R1裁决不删除或收窄现有业务Service API，也不把direct/internal mutation伪装成带`command_id`的receipt命令；三个class已由Nest注入同一Root admission provider，因此采用最小闭环：public `run()` 以固定无副作用`preAcquire => acquire`进入既有`TransactionAdmissionPort.run`，取得一次permit并在全部P2034 attempts复用；每个attempt把同一transaction client的`guard`作为第一项数据库操作，成功时把`releaseInTransaction`作为最后一项。已有command路径继续使用其tenant+command+digest+operation receipt预裁决，不增加alias或第二协调器。该direct/internal入口仍受固定8秒内部deadline、2秒transaction timeout和12秒lease约束，不新增参数、capacity、attempt或wire身份。

由此R1补充授权唯一production文件：`src/modules/skills/skill-transaction.ts`、`src/modules/skills/installation/skill-installation.transaction.ts`、`src/modules/mcp/mcp-transaction.ts`；对应既有`test/unit/skill-transaction.test.ts`、`test/unit/skill-installation-transaction.test.ts`、`test/unit/mcp-transaction.test.ts`与本卡已允许integration/architecture可修改。禁止扩到context/service/module/tokens/schema/generated/package/lock/Proto/OpenAPI/docs/其他仓；若这三个文件内无法在不复制算法的前提下闭环，writer再次停写报告。先为三种public run补命名RED，随后才改production并继续原I-11 stress卡。

- [ ] **ADMISSION-I-12 删除面、当前文档与全门冻结。**先扩architecture/contract assertion，搜索并拒绝pg-owned installer transaction、slot `updateMany`、feature自建admission/semaphore/Redis lock、production绕过guard、`grant_id`/wire漂移、runtime create-if-missing与未登记late Promise。GREEN删除旧路径/重复fixture并只更新实际受影响README/INDEX/CURRENT/TECHNICAL_DESIGN/API_CONTRACT/DATA_MODEL/RELIABILITY/RUNBOOK/SECURITY/ADR，准确区分已实现P4a与待实施P4b–P5。writer在Node24上跑：`pnpm format:check`、`pnpm lint`、`pnpm typecheck`、`pnpm contract:check`、`pnpm prisma:validate`、`pnpm prisma:generate`、`pnpm schema:check`、`pnpm build`、`pnpm test:unit`、`pnpm test:contract`、`pnpm test:architecture`；唯一fresh PostgreSQL+隔离Redis且`REQUIRE_REAL_INTEGRATION=1`跑`pnpm test:integration`、`pnpm smoke`、`pnpm smoke:production`、fresh install/drift/ACK-loss与三轮stress。冻结HEAD/tracked/untracked/full hash与RED/GREEN证据；双reviewer对同一对象PASS后Root精确暂存、提交并在commit上重跑完整post-commit门。任一次0-winner、skip真实integration、hash漂移或门禁失败都保持P4a未验收。

I-12 首个收口候选把 admission 专项 AST helper/断言继续叠加到既有 `test/architecture/architecture.test.ts` 后达到1,053行，超过 TypeScript 手册与 Root checker 的800行硬门。由此补充精确测试放置：允许新建同目录 `test/architecture/transaction-admission.test.ts`，承接 I-11/I-12 的 Serializable guard、slot owner/write、Promise lifecycle fingerprint及其反例；既有 `architecture.test.ts` 保留其余 Capability 总体拓扑断言。相比继续扩单文件，专项文件有独立变化原因且已形成持续增长的 transaction-admission 架构门；相比新建子目录，不增加只有一个文件的目录。只移动本轮相关 helper/test并更新重复import，不改production、机器契约、schema、package/lock或测试语义；两个文件都必须低于800行，architecture计数不减少。该拆分由同一writer执行，Root仍独占Git，冻结后重新双审。

实施允许范围仅限上述明确文件面及其同目录既有测试/fixture、generated Prisma和实现后必要文档；禁止package/lock/proto/OpenAPI/BFF/Agent/IAM/Storage/Scheduler/P4b–P5。若实现确需任务卡未列出的production文件，writer先停写报告，由Root更新本任务板；不得自行扩面或操作Git。此计划先冻结并由contract_review作`PLAN SPEC`、database_review作`PLAN QUALITY`，双PASS后才续派writer开始ADMISSION-I-1。

I-6至I-9 R2冻结审查发现 `mcp.ports.ts -> mcp-rpc.runtime.ts -> mcp.ports.ts` 的源码循环，且 Prisma transaction adapter 因复用 runtime helper 而反向依赖 Connect transport。R3 在不改 wire 的前提下按以下放置门执行：

| 项 | R3 结论 |
| --- | --- |
| Owner | `kokoro-capability/modules/mcp`；它是 MCP 请求本地执行边界，不是 Connect 或 Prisma 的业务事实。 |
| 当前事实 | boundary type/绝对单调 deadline/await helper 与 HandlerContext 构造、Connect error 混在 `mcp-rpc.runtime.ts`；ports 与 transaction 反向 import runtime。 |
| 目标职责 | 纯内部 contract 只持有 `signal + callerDeadlineMonotonicMs`，以 application typed cancellation/deadline error 做同步最终裁决并吸收晚到 Promise；RPC runtime 只从 HandlerContext 构造 boundary。 |
| 目录方案 | 采用新建单文件 `src/modules/mcp/mcp-request-boundary.ts`，因为 type+typed assertion+await helper 有同一变化原因且同时被 RPC/runtime/transaction/ports 复用；淘汰塞入 `mcp.ports.ts`（混入有状态 helper）和留在 `mcp-rpc.runtime.ts`（保留反向 transport 依赖）。 |
| 粒度 | 新文件承载一个可复用的纯 request-boundary contract；不新建目录、alias或第二套算法。 |
| 依赖 | boundary 文件只允许依赖 application typed admission errors；`mcp.ports.ts`/transaction/RPC runtime 单向依赖它。禁止 boundary import `@connectrpc/connect`、Prisma、`mcp.ports.ts`或 `mcp-rpc.runtime.ts`。 |
| 数据/API | 无 schema、Proto、OpenAPI、identity、receipt 或 provider 语义变化；RPC 由既有 `runRpc` 统一映射 typed error。 |
| 删除项 | 从 `mcp-rpc.runtime.ts` 删除纯 type/assert/await 实现，删除 ports/transaction 对 runtime 的 import；不保留 re-export/compat alias。 |
| 验证 | 先加 architecture RED 拒绝 ports/transaction import `mcp-rpc.runtime` 或 `@connectrpc/connect`，再重跑 MCP boundary/cancel/deadline unit、typecheck/lint/architecture/contract/build 及同一 fresh PostgreSQL 完整门。 |

R3 唯一新增 production 路径授权为 `src/modules/mcp/mcp-request-boundary.ts`；可修改本 wave 既有 MCP production/test/architecture 文件以删除循环并迁移 import，其余边界不变。

首个实施计划冻结于Root HEAD `cf1e9b67d264ba419995de7302a78ab0e01722bb`、diff `e8a81bb6bbb0e136abaaa040d38dab1eef149cde4d33eaf382e1a78abcb105f2`。contract_review 为 `PLAN SPEC PASS` 0/0/0；database_review 为 `PLAN QUALITY FAIL`（Blocking 0 / Important 1 / Minor 1）：I-1把fixed-row/drift integration RED放在只改schema/generated的GREEN之前，无法逐卡转绿；I-4又把纯application port/error与有状态queue/deadline/drain实现混在一起。Root已将I-1缩成model/generated-DDL shape并把fixed-row/drift全移到I-2，同时固定`src/application/transaction-admission.ts`为无状态port、`src/application/transaction-admission.error.ts`为typed错误、`src/database/prisma-transaction-admission.ts`为唯一有状态coordinator，queue/deadline/late promise/drain RED/GREEN全部归I-5。修复后冻结新diff并由两名reviewer重新全审；首轮PASS不跨冻结沿用。

修复后的实施计划冻结于同一Root HEAD、diff `786766bc1b429956a78b73e371001f011e265f1d42bc01684ac8c86fe26b723b`；contract_review 最终 `PLAN SPEC PASS`、database_review 最终 `PLAN QUALITY PASS`，两者均为 Blocking/Important/Minor 0 且审前后hash一致。由此授权 capability_owner_p1b 从 child `122a3a5bf09792c7ef11a52de05188f444678d6e` 严格按ADMISSION-I-1至I-12逐卡实施；任何越界文件、门禁失败或设计新歧义先回Root，不得自行扩面。

#### ADMISSION-I-1 验收（2026-09-10）

capability_owner_p1b 在 child `122a3a5bf09792c7ef11a52de05188f444678d6e` 先取得因 model/generated DDL table 缺失而失败的命名RED，再只修改 canonical Prisma schema、architecture test 与 `pnpm prisma:generate` 生成物。首个候选经 database_review `QUALITY PASS` 但有 Minor 1（存在性断言未拒绝额外非tenant标量字段）；原 writer 只加固为顺序/空白无关的精确四字段与四列断言。最终冻结 tracked `f3712e48129ea59d0e9ee0a403d80b30629b02d90e7368a19b0c65d6b357c604`、untracked manifest `09ca73b6ead3a52c6cd0a1ff2904c37c36786d60f79904d36396ef40b657954d`、full `2a5e6378c1ec2c598e8f882d3e5c468c56543a69fe7c4d45bbab9648b494be34`；contract_review `I1 SPEC PASS` 与 database_review `I1 QUALITY PASS` 均为 Blocking/Important/Minor 0。

Root 在同一冻结对象上复跑 Node 24.20.0 的 `pnpm prisma:validate`、`pnpm prisma:generate`、聚焦test、`pnpm test:architecture`（7 files / 32 tests）、`pnpm format:check`、`pnpm lint`、`pnpm typecheck` 与diff/range检查通过，提交 child `43578625e3bc7be5c62510cd09e77c1fad2d799b`（`feat(capability): define transaction admission slot`）；提交后重新generate保持clean，同静态/architecture门再次通过。I-1仅验收model/generated shape；fixed row、installer、drift与真实PostgreSQL语义仍属于I-2。

#### ADMISSION-I-2 验收（2026-09-10）

capability_owner_p1b 在 child `43578625e3bc7be5c62510cd09e77c1fad2d799b` 先取得旧 pg-owned installer、缺少 typed slot/exact rerun、并发及ACK recovery失败的architecture/integration RED，再实现 public Prisma 单一 `ReadCommitted` transaction、typed fixed-row create、同transaction catalog+slot invariant、fresh unknown readback与独立installer budgets。首候选经双审未通过：一是错误地把正常业务使用后free epoch>0与合法held/expired slot判为corrupt，二是catalog遗漏standalone composite/collation等public对象和table durability，三是fresh readback可能在认证后响应黑洞无界等待，四是SIGKILL helper失败路径未回收子进程。R1分离fresh seed/general slot invariant，扩完整catalog/durability fingerprint，加入client/query/readback期限并清理test child；其后database_review又用真实PG证明失败的concurrent unique index会留下同定义但`indisvalid/indisready`为false的残留，而Prisma diff与旧digest均误接纳。R2把`indisvalid/indisready/indislive`纳入digest和显式fail-closed门，并加入真实失败建索引、不修复的RED/GREEN。

最终冻结为 child HEAD `43578625e3bc7be5c62510cd09e77c1fad2d799b`、tracked `dff55c899094d5fc06685507e61c27535e52aa34b71565ddeff1f582aec51aae`、untracked manifest `7856c50abea10a054eb105eb628abc1a254a3440a0202eb87cab7c8438d073cd`、full `6a8e17ab9660a9d74fa06f85e82c31d0ff22587872b17444f4d2d7c375727ad1`；contract_review `I2 SPEC PASS` 与 database_review `I2 QUALITY PASS` 均为 Blocking/Important/Minor 0。writer连续三轮10/10真实installer integration通过；独立database reviewer以自有DB跑architecture 7与真实integration 10全部通过且资源剩余0。

Root 在同一冻结对象上以Node 24.20.0复跑Prisma validate/generate、architecture 33、format/lint/typecheck、真实installer integration 10/10、fresh `db:apply-schema`+`schema:check`、slot virgin invariant、30个index全valid/ready/live与数据库清理剩余0，随后提交 child `1f824f21418d7e73ba6d486b5e51842969d3159b`（`feat(capability): install canonical schema atomically`）。提交后再次generate保持clean，并重跑同静态/architecture及真实installer 10/10通过。I-2至此验收；runtime Prisma 10ms/2s policy、receipt lease下限和业务admission仍属于I-3以后。

#### ADMISSION-I-3 验收（2026-09-10）

capability_owner_p1b 在 child `1f824f21418d7e73ba6d486b5e51842969d3159b` 先取得receipt lease 29,999被旧配置错误接受及runtime row-lock等待超过500ms的RED，再把pool10、connection5s、lock10ms、query/statement/PG transaction与Prisma interactive timeout2s、interactive maxWait1s固定在唯一runtime Prisma factory；真实PG覆盖锁、长query、默认及caller延长到10秒后的PG transaction硬上限、10连接饱和/第11 acquire与认证前blackhole。首候选双审发现connection URL的`options`/timeout query可在pg解析时覆盖固定值；R1在建socket前按解码后lowercase参数名fail closed所有policy覆盖入口，逐项校验重复`schema=public`，保留`sslmode`等非policy参数并用固定无secret错误。database reviewer另证实`connectionTimeoutMillis`/`poolSize` query在当前pg JS/adapter路线不覆盖Pool的显式5s/10配置，真实黑洞仍约5秒拒绝。

最终冻结为tracked/full `ca73e9c47f501ee1c1fe0227b558911647a2fbca35f227e2867a378f6a5ee4df`、无untracked；contract_review `I3 SPEC PASS`与database_review `I3 QUALITY PASS`均为Blocking/Important/Minor 0。writer连续三轮production composition 5/5及installer2.3秒回归通过；Root在同一对象以Node24.20复跑Prisma validate/generate、真实production composition 5/5、installer2.3秒、architecture 33、format/lint/typecheck/build、范围/hash与I3数据库剩余0后提交 child `3339e0fe7d9171a857152b4cf01fc3e6f67d3c12`（`feat(capability): bound runtime prisma sessions`）。提交后重新generate保持clean，并重跑真实production composition 5/5与静态/architecture/build门通过。I-3验收；opaque admission port/error与RPC映射仍属于I-4。

#### ADMISSION-I-4 验收（2026-09-10）

capability_owner_p1b 在 child `3339e0fe7d9171a857152b4cf01fc3e6f67d3c12` 先取得application module缺失的契约RED，再新增纯application permit/operation/typed errors并扩typed RPC映射。首冻 tracked `ea86f1cebf2fe765c68356e795d0fcb32fc98f789ae9c2032764a115d8c2ca49`、untracked manifest `18b0cc4b9577c019207ab05c24c5583554099e663d441dedf453e587dca02e9a`、full `430649aad482580b04624ac59e9f474dd6cd5d184c69b97d55a65bea77eb761c` 未通过双审：contract_review 指出三方法port无法让feature仅经application contract在同一business transaction执行guard/release；database_review指出缺少排队前和每次poll的请求级receipt重检通路。候选未提交。

R1先以test-only RED固定generic transaction context与pre-acquire decision，再把port收敛为`TransactionAdmissionPort<TransactionContext>`：permit仍只有readonly `slotId/ownerId/epoch`；operation input必须带`AbortSignal`、可选absolute monotonic deadline和无状态generic `preAcquire`，其结果只表达继续acquire或直接返回既有结果；port声明同context的`guard`/`releaseInTransaction`，而application仍不import Prisma/Nest/Connect。七类typed error分别映射`CANCELED`、`DEADLINE_EXCEEDED`、`UNAVAILABLE`、`INTERNAL`与`ABORTED`，固定安全消息且generic同文Error不会获得admission分类。R1冻结 tracked `ea86f1cebf2fe765c68356e795d0fcb32fc98f789ae9c2032764a115d8c2ca49`、untracked manifest `7c844b5b89aaff73a3807d61efe61b6fee953f103565e2ef1366bc761ad3344f`、full `dde4dbd0a5bf7d41f7179beedab9cd6bdd278401e9f9077a29d1dff03236d271`；contract_review `I4 R1 SPEC PASS`与database_review `I4 R1 QUALITY PASS`均为Blocking/Important/Minor 0。

Root在同一冻结对象以Node24.20.0复跑聚焦12/12、unit 33 files/307 tests、architecture 7 files/33 tests、format/lint/typecheck/build与diff检查通过，按精确四文件提交 child `4a67fb9b9186784e1fe9bda20711d8806b6f0ab8`（`feat(capability): define transaction admission contract`）。提交后再次生成Prisma保持clean，并重跑相同静态、unit、architecture和build门通过。Skills `series_id/skill_id/source_ref=skill:<skill_id>/installation_id`、MCP `connector_id/server_id/connection_id/authorization_id/invocation_grant`与`mcp-grant:<uuid-v4>`零变化，仍不存在`grant_id`。I-4仅验收无状态契约与错误边界；实际queue/poll/deadline/late Promise、Prisma acquire/guard/release及drain属于I-5。

#### ADMISSION-I-5 验收（2026-09-10）

capability_owner_p1b 在 child `4a67fb9b9186784e1fe9bda20711d8806b6f0ab8` 先取得 Prisma coordinator module缺失的unit/integration RED，再实现唯一有状态coordinator：effective deadline、cancel/stop/drain、不持长事务的本地acquire串行、DB-clock lease、typed unique CAS/fence、P2025与精确P2039/55P03 contention、same-owner epoch ABA、ACK readback和outside fenced cleanup。首个冻结候选经独立真实PostgreSQL审查发现成功响应前未重检deadline，且已回滚attempt的release布尔证明会污染后续attempt；R1改为最终单调deadline裁决、同Prisma transaction context release proof与action完成后durable slot readback。R1双审又证明durable readback的raw adapter错误可经RPC fallback泄漏；R2将该数据库边界收敛为固定`TransactionAdmissionCorruptError`，保留cause但不改写action业务错误语义。

R2最终冻结为 child HEAD `4a67fb9b9186784e1fe9bda20711d8806b6f0ab8`、tracked `4bf0a5bf6284d733060995d975283591b733401b8d0f098d2c5edd13fe35e85f`、untracked manifest `bdc488f34977f01bb8adec00521fe0e151a7e756cb58dc00bfbcf299d5d2c31d`、full `c51f2feab9261bc621e907ee4c9cca520be70425623d0cea30551a447027ecb8`；contract_review `I5 R2 SPEC PASS`与database_review `I5 R2 QUALITY PASS`均为Blocking/Important/Minor 0。Root在同一冻结对象以Node24.20.0复跑聚焦35/35、真实PostgreSQL integration连续三轮8/8（共24/24）、unit 33 files/330 tests、architecture 7 files/33 tests、format/lint/typecheck、fresh canonical apply+persisted schema check、build、diff及资源清理，按精确三文件提交 child `84bff1afc6c8c30b48955f7e03701a94a02caf25`（`feat(capability): coordinate prisma transaction admission`）。提交后同样复跑聚焦35/35、三轮真实PostgreSQL 24/24、unit 330/330、architecture 33/33、静态门、fresh persisted schema和build通过，测试数据库剩余0，child工作树clean。Skills、MCP、Proto/OpenAPI和Manus identity alignment未变；I-5仅验收coordinator，receipt/Skills/MCP/Nest生产接线分别仍属于I-6至I-10。

#### ADMISSION-I-6A 验收（2026-09-10）

capability_owner_p1b 在 child `84bff1afc6c8c30b48955f7e03701a94a02caf25` 先以真实Nest TestingModule取得缺少`TRANSACTION_ADMISSION_COORDINATOR` token/provider的RED，再只修改injection token、RuntimeModule与production composition test：唯一provider从既有`PRISMA_CLIENT`构造`PrismaTransactionAdmission`并由RuntimeModule导出；直接RuntimeModule与完整AppModule composition的重复lookup、export probe及`each: true`均证明各自容器内只有同一reference，且构造持有override后的同一Prisma对象。候选冻结tracked/full `1e58a16c77ff09b67d235f1278b6ee2e4528b0791ab5dbc81614116bab5dfd6b`、无untracked；contract_review `I6A SPEC PASS`与database_review `I6A QUALITY PASS`均为Blocking/Important/Minor 0。

Root在同一冻结对象以Node24.20.0复跑聚焦Nest composition 1/1（该文件其余5项真实基础设施用例按既有环境门控skip，不计作I-6A证据）、unit 33 files/330 tests、architecture 7 files/33 tests、format/lint/typecheck/build及diff/hash检查通过，按精确三文件提交child `c6ab8ea7c580930613d11768630a1addf4ade720`（`feat(capability): provide transaction admission`）；提交后同样复跑并保持child clean。该卡未连接Skills/MCP，未连接数据库或listener，也未提前实现readiness/shutdown；I-6至I-9原子wave与I-10生命周期仍待实施。

#### ADMISSION-I-6 至 I-9 原子 wave 验收（2026-09-10）

capability_owner_p1b 从 child `c6ab8ea7c580930613d11768630a1addf4ade720` 按已批准顺序完成 receipt、Skills catalog、Skill installation 与 MCP local/external phase 的 RED→GREEN。R0/R1/R2 审查分别暴露并修复 receipt/commit-unknown/cancel-deadline 边界；R2 仍因 `mcp.ports.ts -> mcp-rpc.runtime.ts -> mcp.ports.ts` 循环及 Prisma transaction 反向依赖 Connect 而未通过。Root先补充本任务板放置表并提交 `ada63e51`，R3 再新增唯一纯边界文件 `src/modules/mcp/mcp-request-boundary.ts`，删除循环与 transport/persistence 反向依赖。

R3最终冻结为child HEAD `c6ab8ea7c580930613d11768630a1addf4ade720`、tracked `2dbd48e69c35acec7a04552ea70449d2a835c53b7e431328a0a9b4170309b578`、唯一新文件 `c4008fcb0d585157fc4008bc928e0fb0eb60df25381de29bc6d7b77b928b8c55`、untracked manifest `3d0ead1679353484ff530047ff7d218eb8b07dc299e1ab3b7307ae5488bdbc27`、full `a0c869a658471bd33a293ce27e68fd12e6c40f50cc96504fa22042afd38c784a`。contract_review `SPEC PASS` 与 database_review `QUALITY PASS` 均为 Blocking/Important/Minor 0，审前审后 hash 一致；reviewer保持只读且未访问共享基础设施。

Root在同一冻结对象以Node24.13.0/pnpm11.25.0完成format/lint/typecheck、unit 33 files/365 tests、architecture 7 files/34 tests、contract 5 files/20 tests、build、Prisma validate、fresh schema、contract digest `6eb170d12bd046aa70b2a1b8aa775c6303e46ffc997cb4193f77fc230072d3b5`与diff检查；fresh PostgreSQL+Redis DB15下完整测试65 files/621、integration 18 files/188和production smoke均通过，数据库删除前连接0、删除后不存在，Redis前后0。随后按精确37路径提交child `d6d32ce08229fcc1961f85687537984961f1d446`（`feat(capability): fence mutations with transaction admission`）。

提交后首个脚本把`schema:check`错误排在测试数据库创建之前，因目标数据库不存在而退出1；该日志 `/tmp/kokoro-capability-i6-i9-postcommit-d6d32ce-20260910.log` 只记录无效验收编排，不归因于代码。Root随即在新fresh PostgreSQL上按正确顺序完整重跑：静态门、unit365、architecture34、contract20、full621、integration188、production smoke、schema/contract/build均通过，child保持clean；日志 `/tmp/kokoro-capability-i6-i9-postcommit-d6d32ce-real-20260910.log`，数据库与Redis残留均为0。

本wave未改package/lock/schema/Proto/OpenAPI/docs。Skills继续固定`series_id`、不可变`skill_id`、`source_ref=skill:<skill_id>`与管理用`installation_id`；MCP继续固定`connector_id/server_id/connection_id/authorization_id/invocation_grant`，其中值格式为`mcp-grant:<uuid-v4>`，不存在`grant_id`或alias；`command_id`仍只作幂等身份。外部owner/provider真实sandbox与Docker镜像未验证，I-10 readiness/shutdown、I-11压力/绕过门和I-12文档收口仍待实施。

Root当前全局门如实保留：standard exit1/220 violations，topology exit0，`python3 -m pytest scripts/tests`为82 passed/2 failed；两项失败仍是变化中的工程手册示例数量与固定标题断言，不在Capability切片覆盖或放宽。日志 `/tmp/kokoro-i6-i9-root-{standard,topology,tests}-20260910.log`。

#### ADMISSION-I-10 验收（2026-09-11）

capability_owner_p1b 从child `d6d32ce08229fcc1961f85687537984961f1d446` 先取得同实例注入、startup/readiness fixed-slot probe、admission stop/drain缺失的RED，再只修改RuntimeResources、main lifecycle与四个既有测试面。首冻tracked/full `793f09ea5ba53f1e86cd15e4918ec4d2bec11428efc8a7caf000c2d24770652e` 未通过：contract_review `SPEC FAIL`为0/2/0，database_review `QUALITY FAIL`为0/1/1，定位到关闭时暂时无人处理的rejected Promise及后续listener错误覆盖首错。R1新增跨tick `unhandledRejection=0` 与多错误仍保留首错的RED，改用普通failure集合并让main所有阶段保持`failure ??=`；清理仍全部继续。

R1冻结为HEAD `d6d32ce08229fcc1961f85687537984961f1d446`、6个tracked文件、0 untracked、tracked/full `32f9900735ccdabfbd2900939c8fe9bee164c7b4a0bcdf56dec54e04a27ec246`、空manifest `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`。contract_review `I10 R1 SPEC PASS`与database_review `I10 R1 QUALITY PASS`均为Blocking/Important/Minor 0，审前审后hash一致；database reviewer的15个fixed-slot状态样本与coordinator invariant全部一致。

Root以Node24.13.0/pnpm11.25.0在同一冻结对象复跑format/lint/typecheck、unit33 files/370、architecture7/34、contract5/20、build、Prisma validate、fresh schema、contract digest `6eb170d12bd046aa70b2a1b8aa775c6303e46ffc997cb4193f77fc230072d3b5`；fresh PostgreSQL+Redis DB12下full65 files/628、integration18 files/189、smoke2 files/15和production smoke全部通过，资源残留0。随后按精确6路径提交child `8c26e6cfa850e9b3bb2a3724ee48f81b0ce2e46a`（`feat(capability): integrate admission lifecycle`）。提交后在另一fresh PostgreSQL+Redis DB11上完整重跑同一门与计数通过，数据库删除前连接0、删除后不存在、Redis前后0，child clean；日志 `/tmp/kokoro-capability-i10-{r1-root-precommit,postcommit-8c26e6c}-20260911.log`。

本卡确认RuntimeModule唯一coordinator由同一Prisma client构造并被Skills catalog、Skill installation、MCP local/external与RuntimeResources共享；启动在listener前、readiness每次重验唯一fixed slot且不repair；关闭先拒绝admission，再并行等待admission与HTTP/RPC业务drain，随后关闭Nest listener和资源，重复close复用同一Promise，startup失败逆序清理。未改schema/generated/Proto/OpenAPI/package/Skills/MCP identity；Docker与真实外部owner/provider sandbox仍未验证。Root全局门仍为standard exit1/220、topology exit0、pytest82 passed/2 failed，日志 `/tmp/kokoro-i10-root-{standard,topology,tests}-20260911.log`。

#### ADMISSION-I-11 验收（2026-09-11）

capability_owner_p1b 从 child `8c26e6cfa850e9b3bb2a3724ee48f81b0ce2e46a` 先取得 production Serializable transaction 绕过门 RED，定位到 Skills catalog、Skill installation 与 MCP 三个 public/direct `run()` 未进入共享 admission。Root 只补充授权这三个既有 transaction 文件及对应 unit；writer 以同一注入 coordinator 执行固定 `preAcquire → acquire`，一个 permit 跨全部 P2034 attempt，每次 transaction 内 guard-first、release-last。command 路径仍保留 receipt 预裁决，未增加第二协议、capacity、attempt、deadline 或 wire 字段。

首轮压力候选经双审先后发现并闭环：active holder connection death fixture、failed48 durable 断言与清理缺口；pre-final-transaction cancel/deadline 被误包装成 commit-unknown；AST 门对 catch 吞错、动态 options、shorthand/accessor/method、重复属性和未知 property access 存在假绿。最终门只放行静态字符串 `ReadUncommitted`、`ReadCommitted`、`RepeatableRead`；其他 isolation 表达式均 fail closed，所有 production Serializable callback 必须以 exact nonoptional awaited admission guard 作为首项并保持异常重抛。

最终冻结为 child HEAD `8c26e6cfa850e9b3bb2a3724ee48f81b0ce2e46a`、tracked `2ce69a0b9eb028bc69ff4192009d89a43a352034ead5eaaac52c3bc813dda6f4`、唯一 untracked stress `1cd4c2ea4a9a8edb4a7704b856f51ae01b2ffde4a9bae109f5e9ab0dd034fca9`、full `e6ffb62e01120bd9e94515bce6651f6b1e24ca61ab1bf35b07037eb1f09abacd`。contract_review `I11 R5 SPEC PASS` 与 database_review `I11 R5 QUALITY PASS` 均为 Blocking/Important/Minor 0，审前审后 hash 一致。独立 QUALITY 在真实 PostgreSQL 重跑 admission+stress 10/10、unit+architecture 131/131，资源残留0。

Root 在同一冻结对象以 Node 24.13.0/pnpm 11.25.0 重跑 format/lint/typecheck、Prisma validate/generate、contract check与Buf breaking、build、unit 33 files/381、architecture 7 files/38；fresh PostgreSQL+Redis DB12 下 full 66 files/645、integration 19 files/191、smoke 2 files/15、production smoke、schema check、三次独立 stress 与 admission PostgreSQL 9/9 全部通过。数据库删除前连接0、删除后不存在，Redis DB12 为0。随后精确提交9个文件为 child `357dc9b2a94892fd1e8f1eae544286fc0e2e9018`（`feat(capability): close admission stress gate`）。

提交后 Root 在另一 fresh PostgreSQL+Redis DB14 上重复完整静态、生成、contract/Buf、build、unit381、architecture38、full645、integration191、smoke15、production smoke、schema、三次独立 stress 与 admission9/9，全部 exit 0；数据库删除前连接0、删除后不存在，Redis DB14 为0，child 工作树 clean。日志为 `/tmp/kokoro-admission-i11-root-{static,real,postcommit}.log`。

本卡未改 package/lock/schema/generated/Proto/OpenAPI/docs。Skills 继续固定 `series_id`、不可变 `skill_id`、`source_ref=skill:<skill_id>` 与安装管理用 `installation_id`；MCP 继续固定 `connector_id/server_id/connection_id/authorization_id/invocation_grant`，值格式为 `mcp-grant:<uuid-v4>`，不存在 `grant_id` 或 alias；`command_id` 只作幂等身份。该边界与 Root `docs/MANUS_API_ALIGNMENT.md` 及已核对的 Manus `skill.list`、`connector.list`、`task.create` 设计保持一致。Root 全局门本次仍为 standard exit1/220、topology exit0、pytest 82 passed/2 failed；两项失败仍来自当前工程手册示例数量和固定标题断言，日志 `/tmp/kokoro-i11-root-{standard,topology,tests}-20260911.log`，本卡不改或放宽。Docker 与真实外部 owner/provider sandbox 仍未执行；I-12 只做删除面、当前文档与全门冻结，P4b–P5 继续保留为后续 owner。

#### ADMISSION-I-12 验收（2026-09-11）

capability_owner_p1b 从 child `357dc9b2a94892fd1e8f1eae544286fc0e2e9018` 完成 P4a 删除面、当前文档与架构冻结。盘点确认生产目录已无第二套 receipt executor、旧 clock、旧 token 或旁路 transaction 路径，因此本卡不伪造 production 删除；改为把 README/INDEX 与七份设计/运行文档收敛到 P4a 已实现当前态，同时把 P4b–P4e/P5 保留为明确缺口。architecture suite 拆为 354 行基础门和 791 行 admission 门，后者用 TypeChecker fail closed 动态 Prisma delegate 选择，并以规范化 AST SHA-256 冻结唯一 `PrismaTransactionAdmission` 语义，注释/import/格式变化不误报、业务类变化必失败。contract test 额外固定 machine contract 只使用 `invocation_grant`，明确拒绝 `grant_id`/`grantId`。

最终冻结为 child HEAD `357dc9b2a94892fd1e8f1eae544286fc0e2e9018`、tracked `6aad12be7618df40c0c97f4b67f01c795dc90970f536184e957a5d4fabc97037`、唯一新文件 `6b02f169ee9a8e3db8014b6c3f3c74b47a2027f049a27ba726b1ae72cb5f839d`、untracked manifest `8f9e4dbadc2db7186e6ae037f1f7094efbf9470612d059ff4f0896d8c040f0fd`、full `be379b353eeb30e8efecd9f0fbeeee4dc0f607111709ce9f6920f701ba4d0e70`。contract_review `R7 SPEC PASS` 与 database_review `R7 QUALITY PASS` 均为 Blocking/Important/Minor 0，审前审后 hash 一致；QUALITY 独立执行 37 个正反例、TypeChecker 真实仓扫描、architecture+contract 68 tests 与静态检查，全部通过且未访问共享资源。

Root 在同一冻结对象上以 Node 24.20.0/pnpm 11.25.0 完成 frozen install、format/lint/typecheck、Prisma validate/generate、contract check与Buf breaking、build、unit 33 files/381、contract 5/21、architecture 8/47；fresh PostgreSQL+Redis DB13 下 full 67 files/655、integration 19/191、smoke 2/15、production smoke、schema check、三次独立 stress 与 admission PostgreSQL 9/9 全部通过，数据库删除前连接0、Redis DB13为0，日志 `/tmp/kokoro-admission-i12-root-precommit.log`。Root 随后按精确13路径提交 child `b21f9c7a22dc5de095eb79cb9e6afea0983fe12c`（`docs(capability): close admission implementation`）。

提交后 Root 在另一 fresh PostgreSQL `kokoro_capability_i12_post_1789112536_31670` 与 Redis DB14 上重复完整静态、生成、contract/Buf、build、unit381、contract21、architecture47、full655、integration191、smoke15、production smoke、schema、三次独立 stress 与 admission9/9，全部 exit 0；数据库删除前连接0、Redis DB14为0，child 工作树 clean，日志 `/tmp/kokoro-admission-i12-root-postcommit.log`。package/lock/schema/generated/Proto/OpenAPI均无变化。

P4a 至此验收完成。Skills identity 继续固定 `series_id`、不可变 `skill_id`、`source_ref=skill:<skill_id>` 与安装生命周期 `installation_id`；MCP identity 继续固定 `connector_id/server_id/connection_id/authorization_id/invocation_grant`，其中 grant 值为 `mcp-grant:<uuid-v4>`，不存在 `grant_id` 或 alias；provider key、URL、selector、tool name 均不是资源 identity，`command_id` 仍只作幂等身份。Root 全局门为 standard exit1/220、topology exit0、pytest 82 passed/2 failed；两项失败仍是未交接 SQL/TypeScript 工程手册的示例数量与固定标题断言，日志 `/tmp/kokoro-i12-root-{standard,topology,tests}-20260911.log`，本卡未修改或放宽。Docker 与真实外部 owner/provider sandbox仍未执行；下一片先收敛 P4b 的 operation-specific provider recovery 任务卡与双审，再授权唯一 writer。

### P4b MCP Authorization Recovery 实施设计（已双审并授权）

P4a 验收提交 `b21f9c7a22dc5de095eb79cb9e6afea0983fe12c` 是本片唯一 child 基线。三路只读审计确认当前 machine wire 和 Prisma schema 已预留足够字段，但生产实现仍有四个缺口：provider port 没有 authoritative inspection；receipt claim 与 Begin pending/Complete handle binding 分两次提交；`providerMayHaveStarted` 只是进程内布尔值；receipt mapper/CAS 尚不能取得、等待和终结 `external_unknown` recovery。P4b 先在本任务板闭环设计，不把审计报告当实现证据。

#### P4b 放置表

| 项 | 结论 |
| --- | --- |
| Owner | 当前 `kokoro-capability`、目标 `kokoro-platform/modules/mcp/authorization`；MCP authorization 与其 command recovery 由本仓唯一写入。Provider owner只返回 authoritative operation outcome；IAM/SecretStore不转移所有权，Scheduler/Agent不保存本仓 recovery fact。 |
| 当前事实 | 17个MCP RPC和Begin/Complete wire已稳定；`command_receipt`已有status/lease/epoch/due/failure/recovery三元组，`mcp_connector_authorization`已有requested scopes、stored handle、account与状态。当前claim不写recovery，Begin authorization ID在后续事务生成，Complete handle另事务绑定，provider只有begin/complete/revoke且HTTP错误不能证明未执行。 |
| 目标职责 | 同一精确RPC重试在重新完成attestation/IAM/tenant/resource/digest检查后，以caller-driven方式取得recovery lease；原子提交initial receipt claim与Begin pending或Complete verified-handle binding及recovery pointer；持久化provider call intended/response observed；用原authorization identity authoritative inspect并只重试本地finalization。进程重启由新Nest app/Prisma client对同一DB和provider事实重放同command证明，不新增后台scan loop。 |
| 目录方案 | 采用既有`src/modules/mcp/authorization/`新增两个单一职责文件：`mcp-authorization-recovery-state.ts`是多消费方共享的纯typed phase/pointer/codec事实源，`mcp-authorization-recovery.ts`只负责caller-driven orchestration。继续使用唯一`PrismaCommandReceiptRepository`执行receipt CAS，并从`mcp-rpc.runtime.ts`移出旧外部命令编排。相比`src/application/recovery`通用框架，此方案不把MCP provider语义污染公共层；相比新worker/job模块，不提前建设P4e1 supervisor。现有769行authorization service只保留本地业务规则，新增恢复逻辑不得继续堆入该文件。 |
| 粒度 | `mcp-rpc.runtime.ts`只负责Connect请求边界/精确重放入口，`mcp-transaction.ts`只负责admitted Prisma transaction，纯state/codec文件只负责持久状态解析与不变式，orchestration文件只负责phase/provider outcome编排，HTTP adapter只负责bounded provider协议。新增测试使用独立P4b文件，不继续膨胀现有2245/1154/1641行测试。 |
| 依赖 | transport → authorization recovery orchestration → typed provider port + MCP transaction port → Prisma receipt/MCP repositories。Repository/transaction只可依赖纯recovery state/codec，不得import orchestration service；provider outcome由`mcp.ports.ts`维护，不反向依赖编排。禁止provider/IAM/SecretStore HTTP进入Prisma transaction、P2034 callback或持有transaction-admission slot；禁止Prisma/Connect类型进入纯state codec。 |
| 数据/API | 优先复用当前canonical Prisma schema与两条stale/due索引；`recovery_kind=mcp_connector_authorization`，`recovery_ref=<authorization_id>`，phase使用严格`v1.begin.*`/`v1.complete.*` codec。公开Proto/OpenAPI/17方法/field号/digest零变化。Provider operation identity固定为原`authorization_id`及既有snapshot；Complete只用数据库已绑定且本次重新经SecretStore验证的exact handle。 |
| 删除项 | 验收时删除独立claim→bind崩溃窗、`providerMayHaveStarted`内存裁决、可能发送后mark retryable、generic external reclaim、optional `transact/bind/finalize/reject` production fallback与重复provider identity生成路径；不删除P4c所需cleanup intent，不把best-effort revoke写成durable完成。 |
| 验证 | unit/contract/architecture + fresh真实PostgreSQL双pool/CAS/回滚/旧epoch + parent持久provider fixture和新app/process重启 + cancellation/blackhole/drain；再跑P4a完整静态、schema、integration、smoke、production smoke、三轮admission stress，SPEC/QUALITY双审和Root pre/post-commit。 |

#### P4b 内部 provider 与 recovery 合同

1. `McpConnectorAuthorizationPort` 增加operation-specific、无副作用的 `inspectBegin` 与 `inspectComplete`（或等价的严格discriminated API）。输入只含 `provider_key`、`connector_id`、原 `authorization_id`、精确requested-scope snapshot；Complete另含数据库stored exact handle。两方法结果只允许 `not_sent | pending | succeeded(normalized result) | rejected | unknown`。`not_sent`必须是provider authoritative no-effect证据，最终一致性的暂时404不是证据；transport/schema/unreadable/unsupported一律归`unknown`并保持fail closed。
2. `succeeded` 对Begin返回完整且规范化的provider display、consent scopes、authorization URL；对Complete返回approved scopes与external account。`rejected`只生成现有净化terminal typed结果；`pending/unknown`返回Connect `UNAVAILABLE`。调用者不能提交phase、provider result或替换identity。Provider owner不支持该inspect合同的部署只能保持`UNAVAILABLE/external_unknown`，不得以本地fixture冒充生产可恢复。
3. provider begin/complete是以同一authorization ID与相同snapshot执行的at-least-once operation，不宣称exactly-once。只有authoritative `not_sent`才可用同一identity安全重发一次；每个RPC attempt最多一次inspect和一次经no-effect证明的provider调用，继续pending/unknown时写等待due，不在进程内无界轮询。
4. Skills identity保持`series_id`、不可变`skill_id`、`source_ref=skill:<skill_id>`与安装生命周期`installation_id`。MCP保持`connector_id/server_id/connection_id/authorization_id/invocation_grant`，grant值为`mcp-grant:<uuid-v4>`；`command_id`只作幂等identity。不存在`grant_id`/alias，provider key、display、URL、selector、tool name均不替代resource ID。该设计只采用Manus `skill.list`/`connector.list`→opaque typed reference原则，不复制其wire。

#### P4b IAM 跨仓对齐门

2026-09-11 固定当前事实：`kokoro-iam` clean HEAD `834fdc9ef93c817a61255e417c8b0f7f2e920b43`的`contract/`与`src/`没有`RunExecutionAttestation`、`expected_operation/request_binding`或`owner_scopes`的machine contract；已验收`POST /internal/v1/authorization/check`只回答当前token在`tenant/read | audit/read`的同tenant decision，不接受tenant/subject/actor自报，也不能替代Capability当前`HttpAttestationVerifier`所假定的operation-bound run/session/request-binding验证。因此Capability的本地IAM fixture只是保留行为证据，不冒称跨仓已对齐。

- IAM仍是tenant、principal、authentication/authorization与current permission fact的唯一owner；Agent只能拥有Run/Checkpoint/Execution evidence及attestation的签发语义。Root需要在两owner间独立裁决“Agent签发、IAM发布验证contract”或等价的唯一方案，不允许Capability自己成为第二个identity/permission owner。
- 对齐合同必须版本化并固定：issuer/audience信任，签名/key rotation，`tenant_ref/subject/run_id/session_id/owner_scopes`，exact operation与request-binding SHA-256，issued/expiry/nonce/replay，caller workload identity，以及400/401/403/409/503与`allowed=false`的区分。外部JSON采用snake_case；Capability必须使用owner发布的固定版本generated client/artifact，不继续手写一份漂移wire。
- `actor`与`subject`必须作为不同受信身份建模：Agent签发的execution evidence绑定原始actor、represented subject、run/session与request，但IAM在验证时仍需重验当前delegation/impersonation关系、caller service identity和owner scope；Capability不得从body自报或自行推断代表关系。IAM拥有authentication/authorization/delegation decision audit，Agent拥有attestation签发及Run/Checkpoint evidence，Platform只拥有Capability调用与recovery状态迁移审计；三方只用request/trace/run等稳定引用关联，不复制token、完整attestation或别仓审计payload。
- P4b-2 atomic prepare与P4b-3 receipt CAS是Capability内部事务/并发事实，可在不改IAM wire时继续。P4b-4/5可先用现有fixture完成本地RED/GREEN，但在上述owner contract、consumer contract test与真实IAM sandbox证据完成前，不得标记生产对齐、P4b整体验收或P5 cutover ready。
- 本任务不修改IAM文件/schema，不把`authorization/check`扩成任意permission袋，不共享Prisma schema/DTO；IAM owner另行实现并提交机器契约后，Root再以独立消费者切片替换Capability HTTP fixture约定。

#### P4b 持久状态与事务边界

```text
missing
  -- one admitted Serializable transaction:
     claim receipt + create/reuse Begin pending OR bind verified Complete handle
     + recovery pointer/phase + slot release --> processing/prepared

processing/prepared
  -- fenced short transaction --> processing/provider_call_intended
  -- provider I/O, no DB transaction/slot held
  -- fenced short transaction --> processing/provider_response_observed
  -- final admitted Serializable transaction --> completed | terminal failed
  -- may-have-sent/unknown --> external_unknown/waiting

expired processing or due external_unknown/waiting
or lease-expired external_unknown/held
  -- exact caller retry + fresh auth + CAS old epoch to N+1 --> external_unknown/held
  -- authoritative inspect --> succeeded/rejected/not_sent/pending/unknown
  -- local finalize/terminal | same-ID safe invoke | waiting with persisted due
```

- 不持久化standalone `claimed`：initial claim、本地pending/handle事实和完整recovery三元组在同一transaction提交；该transaction失败则三者全无，commit ACK unknown只做fresh readback。Begin授权ID在transaction retry外生成候选，但transaction内若复用现有合法pending则recovery ref必须使用该authoritative ID；任何首次提交最终只有一个ID。
- 唯一持久`recovery_kind`精确冻结为`mcp_connector_authorization`；版本进入phase而不另造kind alias。Phase固定为`v1.begin.pending_committed`/`v1.complete.handle_bound`、`*.provider_call_intended`、`*.provider_response_observed`、`*.local_finalizing`；非法operation/phase/ref组合在repository边界fail closed。response-observed只证明进程见过响应，不是可跨重启信任的result；重启仍inspect。
- recovery acquisition使用DB clock。入口同时包含expired `processing`、due `external_unknown/waiting`，以及`lease_expires_at <= DB now`的stale `external_unknown/held`；三者都比较tenant+command+digest+operation+status+完整pointer+旧owner/epoch/expiry/due，CAS epoch `+1`并增加独立attempt。旧holder在inspection/provider/finalize的任意迟到结果都不能写入。`external_unknown` held/waiting映射显式区分；等待只清owner/expiry、写DB-clock due并保留epoch/pointer。
- 每个RPC只做一次reconcile acquisition、最多一次inspection，并且只有authoritative `not_sent`才再做一次同identity provider invoke；不在一次请求内循环。每次成功acquisition先把`reconcileAttempt`+1，起点为1；延迟精确为`delay = reconcileAttempt >= 7 ? 60_000 : min(60_000, 1_000 * 2^(reconcileAttempt - 1))`，先以整数分支饱和再计算，jitter在`[delay/2, delay]`。attempt只在超过32-bit signed上限时拒绝新acquisition；长期unknown在此前始终保持60秒cap，不计算可溢出指数。due使用DB clock，jitter注入点只用于确定性测试，不进入Nest/wire或环境配置。
- 每个phase/等待/终态写都比较当前owner+epoch+完整pointer。最终transaction重验connector/pending-or-active pointer、authorization、requested scopes、stored handle、expiry/revoke/account；business、0/1 outbox、codec、receipt terminal和slot release同事务。`completed`与terminal `failed`均必须原子清空recovery kind/ref/phase、owner/expiry/due，terminal mapper明确验证这一不变式；随后的fresh replay只返回持久terminal result/error，不再inspect/invoke provider。旧epoch晚到的response不能写business/outbox/receipt或调用revoke。
- P2034只重试完整本地transaction并重读DB clock/current facts/fence；provider调用不在retry callback。P2025必须fresh readback分类。先复用现有stale/due索引，不改schema/generated/installer；真实query plan证明不足时停止并由Root另授权schema片。
- 本片明确使用**同一精确RPC的caller-driven reconcile**，没有constructor隐形循环、scan worker或新进程。authorization recovery orchestration是provider inspection/invoke的唯一owner：它通过`HttpDrainService`的新增thunk-based settlement tracking API在启动原始provider Promise之前登记，并仅在该原始Promise真实settlement后释放；`awaitMcpRequest`因caller cancel/deadline提前返回不得提前释放这个跟踪。`createRuntimeClose`依旧先begin draining，再等`HttpDrainService.waitForIdle()`，因此必须等跟踪集合中的provider原始Promise结束后才关闭Nest/Prisma/Redis；全局shutdown deadline超时才走现有force-close。该装配只允许修改`src/app.module.ts`、`src/runtime.module.ts`、`src/http/http-drain.service.ts`和`src/modules/mcp/mcp.module.ts`，不通过持有transaction-admission slot或RPC interceptor lease来偷换跟踪。P4e1才建设通用receipt supervisor/scan/metrics。没有client重试时unknown durable fact保留，不盲目重发。
- Begin/Complete入口拆分fresh与recovery admission：两者都必须先通过fresh attestation/IAM、tenant、owner visibility、exact operation/request binding和digest；只有fresh path在initial atomic transaction要求pending/active生命周期前置条件。已revoke/expired/pointer变化的recovery仍必须获准读取原recovery fact并做authoritative inspect，随后在fenced finalization中fail closed/quarantine；不得因旧pre-receipt current-state校验过早退出而永久阻塞对账。

#### P4b RED → GREEN 执行卡

每卡先冻结并运行因目标行为缺失而失败的RED，再写最小GREEN；writer不操作Git。测试不得只用重建in-memory mock冒充跨崩溃恢复。

- [x] **P4b-1 Typed provider/recovery contract。**新增独立unit/contract/architecture RED，固定Begin/Complete inspection union、authorization ID/snapshot、strict normalization、unavailable/unsupported→unknown、no-effect与eventual-not-found区别；固定Proto digest、17 RPC、field号、operation/binding和`invocation_grant`零变化，源码/machine contract无`grant_id|grantId`。GREEN只改MCP port、HTTP adapter并新增纯`mcp-authorization-recovery-state.ts`；repository只可import该纯事实源，不得import orchestration，不得改public proto。
- [x] **P4b-2 Atomic prepare。**unit与真实PG RED覆盖receipt claim提交后、本地pending/handle前切断，预期旧实现留下无target receipt；GREEN把initial claim、Begin pending创建/复用或Complete verified handle binding、recovery pointer和slot release合入一个admitted Serializable transaction。SecretStore/IAM/catalog均在transaction前完成，transaction内重验current事实；commit ACK unknown用fresh receipt+authorization readback，不重新生成ID。
- [x] **P4b-3 Recovery CAS/state。**真实PG RED覆盖stale processing、due unknown与lease-expired `external_unknown/held` acquisition；固定A取得held后进程死亡、lease到期后B/C双pool单winner、旧A迟到不能写且最终可completed或waiting。同时覆盖waiting/held空值矩阵、same-owner ABA、epoch overflow、A持行锁跨expiry的commit/rollback两结局、unknown→held→waiting两轮所有旧epoch拒绝；带recovery pointer进入completed/terminal failed必须原子清空recovery全部字段，fresh replay只读terminal result/error且provider inspect/invoke为0。equal-jitter用确定随机源固定attempt 1、首次达60秒cap、长期cap与32-bit计数上限四类测试。GREEN只扩唯一receipt coordinator/repository、纯recovery state/codec与MCP transaction port；无第二lease/recovery表，无raw claim SQL。
- [ ] **P4b-4 Begin recovery。**持久provider fixture + 新Nest app/Prisma client重启RED覆盖prepared后/intended前、intended后/call前、provider success后/observed前、observed后/final前、final ACK lost。GREEN用原authorization ID inspect；succeeded只完成本地receipt，rejected terminal，authoritative not_sent才同ID重发，pending/unknown等待；不得创建第二authorization或相信phase即结果。
- [ ] **P4b-5 Complete recovery。**同样四崩溃点与重启RED，另覆盖stored handle不可换、scope/account/provider result drift、并发Complete compatible replay、expiry/revoke/active pointer两种顺序、late success quarantine与active-current cleanup guard。GREEN只重用原authorization ID和stored verified handle；provider success后只重试本地finalize，cleanup intent保留给P4c，不能把best-effort revoke当完成。
- [ ] **P4b-6 Boundary/stress。**RED覆盖provider timeout、caller cancel、response blackhole、durable inspect不可读、late Promise、final commit unknown、provider I/O期间`pg_stat_activity`无idle transaction/slot无holder、双实例并发reconcile及三轮压力。额外固定RPC已因cancel/deadline返回但provider原始Promise仍挂起时，close不能提前drained；原始Promise迟到成功/失败都必须被消费，不产生unhandled rejection，shutdown deadline force路径有界。GREEN保证每RPC至多一次inspect+一次authoritative-not-sent后的invoke，有限backoff/due，并由orchestration用thunk-based API把每个原始provider Promise登记到`HttpDrainService`；不依赖会随cancel提前释放的RPC execution lease。
- [ ] **P4b-7 删除面、当前文档与全门。**删除旧memory boolean、separate claim/bind和generic external retryable路径；更新README/INDEX/CURRENT/TECHNICAL_DESIGN/API_CONTRACT/DATA_MODEL/RELIABILITY/RUNBOOK/SECURITY，仅把实际caller-driven recovery写为current并保留P4c–P5缺口。运行format/lint/typecheck、Prisma validate/generate、contract+Buf、schema/fresh install、build、unit/contract/architecture、fresh真实PG/Redis full/integration/smoke/production smoke、P4b restart/stress及三轮既有admission stress；Docker与真实provider sandbox若未运行如实列明。
- [ ] **P4b-8 冻结双审与Root验收。**writer给HEAD、tracked/untracked/full hashes、绝对文件清单、每卡RED/GREEN和资源残留并停写；contract_review/database_review在同一hash上分别SPEC/QUALITY，任何blocking/important回原writer补最小RED。双PASS后Root精确路径提交，并在child commit上用另一fresh DB/Redis完整重跑。

#### P4b 文件权限与禁止扩面

唯一writer继续为 capability_owner_p1b。允许修改 `src/application/command-receipt*.ts`、唯一Prisma receipt repository、`src/modules/mcp/{mcp.ports,mcp-transaction,mcp-rpc.runtime,mcp-rpc.service,mcp.module}.ts`、`src/modules/mcp/authorization/`、`src/infrastructure/clients/mcp/http-authorization.ts`、为原始provider Promise跟踪所必需的`src/app.module.ts`、`src/runtime.module.ts`、`src/http/http-drain.service.ts`、必要test doubles/fixtures，以及对应独立unit/integration/contract/architecture测试和既有当前文档。authorization目录只允许新增`mcp-authorization-recovery-state.ts`与`mcp-authorization-recovery.ts`两个实现文件，在test既有目录可新增独立P4b测试/持久provider fixture。

禁止修改 `prisma/schema.prisma`、generated、package/lock、public Proto/OpenAPI、Skills业务、outbox delivery、credential retirement表/worker、P4e1 supervisor、P5消费者和其他仓；若真实query plan或类型边界证明必须越界，先停写报告Root。P4b完成只代表本方fixture证明协议与恢复；真实provider owner对inspection/idempotency的sandbox证据仍单独列为上线门，不用本地fixture冒充。

#### P4b 实施计划双审与授权（2026-09-11）

Root 先冻结 child `b21f9c7a22dc5de095eb79cb9e6afea0983fe12c` clean 基线与 Root HEAD `08c4a0cf778742225ec3c47dfa8052fd4f201d7f`。首轮 QUALITY 以失效held接管、原始provider Promise drain、state/codec与编排职责、terminal recovery清理、equal-jitter精确计算为 3 Important/2 Minor 未放行；Root 全部回写本计划后重新冻结为 diff `7a7ea34b6d429c190e9326ef55aeaae8c69b8f142d5f27683c70c6464f442b80`、文件 `b7ad1bdb459dd6fdf0c105910677ff0054464472aea802bddccab4d9f572c40b`。contract_review `P4b PLAN R2 SPEC PASS` 与 database_review `P4b PLAN R2 QUALITY PASS` 均为 Blocking/Important/Minor 0，审前审后hash与child clean一致。

双审只放行上述 P4b-1 至 P4b-8、两个单一职责新文件及明列装配/测试/文档路径，不表示代码已验收。唯一writer为 capability_owner_p1b，从 P4b-1 RED 开始逐卡推进；writer不操作Git，P4c–P5、schema/generated/package/lock/public wire/Skills和其他owner仍未授权。

#### P4b-1 验收（2026-09-11）

capability_owner_p1b 从 child `b21f9c7a22dc5de095eb79cb9e6afea0983fe12c` 以 RED 证明纯recovery state与required inspection port缺失，再实现独立必需`McpConnectorAuthorizationRecoveryPort`、同时实现execution/recovery两port的bounded HTTP adapter与纯phase/pointer codec。Root裁决两port是任务板“或等价严格API”的接口隔离实现；inspect不得optional，P4b-2/4生产装配必须显式需要两port。provider authoritative `not_sent`与`pending/succeeded/rejected/unknown`被严格解析，404/unsupported/malformed/unreadable/transport/timeout/abort均fail closed为unknown；Proto/OpenAPI、17 MCP RPC、digest与typed identity零变化。

首轮候选冻结tracked `8214bc2050b79e38f6b69b8e373d4f3d31a8212e0ab6e71dd1c959954308bbd0`、untracked manifest `f6137e7213b08b246d2fd9aea106c84cc7e4d8a2a0bb09d9ca4feb5c8cfe8897`。contract_review `SPEC PASS 0/0/0`，database_review独立发现`keyof` union遗漏Begin/Complete两个初始阶段，因此`QUALITY FAIL 0/1/0`未放行。原writer先用八阶段实际类型赋值得到两个TS2322 RED，再按Begin/Complete分别提取value union、使用类型谓词且删除phase强转，补全八阶段round-trip。R1冻结为tracked `8214bc2050b79e38f6b69b8e373d4f3d31a8212e0ab6e71dd1c959954308bbd0`、manifest `ab7030e0748af9635d19bb4025ef4f660d221bb3a9d8b5efd39f103a8c2761ba`，contract_review `R1 SPEC PASS`与database_review `R1 QUALITY PASS`均为 Blocking/Important/Minor 0。两审对full hash的分隔符公式不同，Root只以两者一致复核的HEAD、tracked、manifest与逐文件SHA作冻结事实，不冒称full值一致。

Root 在提交前与提交后分别重跑 Node 24.13.0/pnpm 11.25.0 的format、lint、typecheck、unit 34 files/408、contract 5/22、architecture 9/49、build/Prisma generate与diff/clean检查，全部 exit 0，日志`/tmp/kokoro-p4b1-r1-root-{precommit,postcommit}-20260911.log`。Root精确提交6个文件为child `b50745186ce10cf6fba0b190c0563e1366ff11de`（`feat(capability): define mcp recovery contract`），child clean。本卡未访问PostgreSQL/Redis/服务，未运行Docker或真实provider sandbox；只验收P4b-1内部合同checkpoint，恢复编排和真实PG事务从P4b-2续推。

#### P4b-2 首轮候选审查修复卡（2026-09-11）

P4b-2 首轮候选冻结为child HEAD `b50745186ce10cf6fba0b190c0563e1366ff11de`、tracked `7a5bec004ddc64036e08e11bd24830a37c560b1b6710c57e375d7904adb3de69`、untracked manifest `adb36618899274f1da4b4ba8a24ba5bf731f624c55ee376c35f69aca73b55e8d`、full `2c16b2091c8401297b3e7067ebbdd740898246fb12cde95d43be42ef3faeaabd`。SPEC独立审查为 Blocking/Important/Minor 0；QUALITY为 Blocking 1 / Important 2 / Minor 0，因此候选未验收、未提交。原writer只按以下三项先加RED后修最小GREEN：

1. 新增真实PostgreSQL statement-level serialization conflict：atomic transaction已读admission slot后，另一client更新并提交，使首次`guard`或`releaseInTransaction`的Prisma statement产生`P2034`。`PrismaTransactionAdmission`只把`P2025`映射为ownership lost，对`P2034`保留原错透传，由外层已有`retryPrismaTransaction`重跑整个prepare transaction；同一permit/receipt owner/候选authorization ID、重读DB clock，最终只一receipt/一authorization且slot释放。本修复卡额外授权修改`src/database/prisma-transaction-admission.ts`及其对应unit/architecture/真实PG测试；不改capacity/lease/deadline/schema。
2. 在MCP transaction/repository边界消费P4b-1唯一纯`decodeMcpAuthorizationRecoveryPointer`：从identity operation导出exact Begin/Complete，对wrong kind、cross-operation phase、blank/trim ref全部fail closed，并在同一atomic transaction回滚receipt、pending/handle与slot。通用`PrismaCommandReceiptRepository`不import MCP orchestration/HTTP；不以任意字符串类型或强转绕过codec。同步翻转旧测试中接受非版本phase的fixture。
3. 真实PG通过实际`ConnectorAuthorizationService`/RPC路径预置一个有效pending authorization，再用不同随机候选执行Begin；receipt `recovery_ref`、connector pointer和provider operation identity必须全部使用数据库authoritative pending ID。另在该生产路径首次transaction制造P2034，确认新建候选ID跨retry稳定、最终只一authorization；不用两caller预先共享同一ID代替证据。

修复仍由原 capability_owner_p1b 单一写入，禁止Git操作，不扩到P4b-3 acquisition/jitter、P4b-4/5 orchestration、schema/generated/package/public wire/Skills/IAM或其他仓。修复后使用fresh隔离PG重跑聚焦矩阵与完整静态/integration/smoke，重新冻结后由SPEC/QUALITY对同一对象双审；双PASS之前Root不暂存子仓文件。

P4b-2 R1 候选冻结为child HEAD `b50745186ce10cf6fba0b190c0563e1366ff11de`、tracked `a8b8177df3fe73e31f728963a351a60a931730872b339852886f6ee8f914586a`、untracked names `9901064f75ab607afa5417f556dbf00d60602f954924d15a638ba2e2c109173c`、untracked manifest `198c068b96698dc3a620797718c66948c232ed78a5b4f23d0523dd1cc1d5a631`。SPEC R1 为 Blocking/Important/Minor `0/0/0`；QUALITY R1 为 `0/1/0`，因此仍未验收、未提交。唯一剩余修复仅允许修改 `test/integration/mcp-atomic-prepare.integration.test.ts`：在真实 `McpRpcService -> ConnectorAuthorizationService` 路径包装 `preparation.plan` 记录每次返回的 `authorizationId`，把真实 PostgreSQL 冲突安排到 `releaseInTransaction`，证明失败 attempt 已经完成 plan/claim/pending 写入，并断言至少两个 attempt 的 ID 完全相同；用把 `randomUUID()` 移入 plan 的 mutation 证明该测试会失败。不得借此修改生产实现、扩大 wire/IAM/Skills/P4b-3 范围或弱化既有断言；完成后重新冻结同一候选并由 SPEC/QUALITY 双审。

P4b-2 R2 仅修改 `test/integration/mcp-atomic-prepare.integration.test.ts`，冻结为同一child HEAD、tracked `a8b8177df3fe73e31f728963a351a60a931730872b339852886f6ee8f914586a`、untracked names `9901064f75ab607afa5417f556dbf00d60602f954924d15a638ba2e2c109173c`、untracked manifest `0d1c9605b435bbbf5bf34fa69145129df4a36b09618b4f0ebef5fabb5717c02e`，该integration文件SHA为 `55b1f9b5e75ae9b3e4f79caea5bdf2466628b8c700e4854ed7de58a135759f0e`。新增证据在真实 RPC/service 路径逐attempt记录plan返回的authorization ID，并在失败attempt已完成plan、receipt claim、pending写入和readback后，于`releaseInTransaction`制造真实statement-level P2034；mutation为每次plan改写随机ID时该唯一用例按预期失败，恢复后聚焦6/6。writer在fresh隔离PG/Redis上得到full 71 files/699、integration 20/197、unit 35/415、contract 5/22、architecture 9/50、smoke 15/15，另独立integration 20/197；format/lint/typecheck/contract/Prisma/schema/build/production smoke/diff check均exit 0。数据库已删除，Redis DB13为0 key。该证据仍待R2双审与Root独立复验，不能直接作为验收结论。

#### P4b-2 验收（2026-09-11）

P4b-2 R2 的 SPEC 与 QUALITY 双审均为 Blocking/Important/Minor `0/0/0`，审前审后 HEAD、tracked/untracked manifest 和两份新增测试 SHA 一致。Root 在冻结对象上使用 Node 24.20.0、pnpm 11.25.0、本机 PostgreSQL 18.4 和 Redis 8.8.0，以 fresh 数据库与空 DB14 完成 pre-commit：format/lint/typecheck、contract digest `6eb170d12bd046aa70b2a1b8aa775c6303e46ffc997cb4193f77fc230072d3b5`、Prisma validate/generate、fresh schema、full 71 files/699 tests、独立integration 20/197、smoke 2/15、build、production smoke、public FK=0 和diff check均exit 0。Root精确暂存19个获准文件，提交child `4e26112848d11afd5d02d2b9d12553da35bf2016`（`feat(capability): make mcp authorization prepare atomic`）。

提交后Root改用另一fresh数据库与空Redis DB15重复同一完整矩阵，仍为full 699/699、integration 197/197、smoke 15/15且所有静态/contract/Prisma/schema/build/production smoke门通过；两次数据库均在0连接后删除并确认不存在，Redis最终0 key，日志为`/tmp/kokoro-p4b2-r2-root-{precommit-20260911065306,postcommit-20260911065721}.log`。P4b-2只验收atomic prepare：未运行Docker或真实IAM/provider/SecretStore sandbox，不解除IAM owner contract门，不进入recovery acquisition/orchestration。

#### P4b-3 Recovery CAS/State 实施授权卡（待双审）

| 项目 | 结论 |
| --- | --- |
| 任务 | P4b-3 / P0：在现有`command_receipt`上实现caller-driven recovery acquisition、held/waiting状态、epoch fence、phase CAS、等待退避与terminal清理；完成条件是下述unit/真实PG RED全部转GREEN且无provider I/O。 |
| 归属 | owner为`kokoro-capability`/目标`kokoro-platform modules/mcp/authorization`；执行人为原capability writer，Root审查并提交；IAM、Agent、provider与Scheduler均非本卡writer。 |
| 基线 | child绝对路径`/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-capability`，分支`codex/production-closure-docs`，clean commit `4e26112848d11afd5d02d2b9d12553da35bf2016`；Root保留SQL手册、`kokoro-agent`和`.tmp/`未交接变更。 |
| 文件集 | 允许修改`src/application/command-receipt.ts`、确有新typed error时的`src/application/command-receipt.error.ts`、唯一`prisma-command-receipt.repository.ts`、`mcp-authorization-recovery-state.ts`、`mcp-transaction.ts`、`mcp.ports.ts`、必要`test/doubles/command-receipt.ts`和既有architecture测试；新增独立`test/unit/mcp-recovery-cas.test.ts`与`test/integration/mcp-recovery-cas-postgres.integration.test.ts`。不得修改RPC/service/runtime、HTTP provider adapter、Nest装配、schema/generated/package/lock/docs或其他仓。 |
| 依赖 | 只允许MCP transaction port → typed receipt coordinator/repository → Prisma/DB clock，以及repository → 纯recovery codec；repository不得import orchestration/provider/HTTP，纯codec不得import Prisma/Connect。P4b-4才调用inspect/invoke，P4b-6才接drain tracking。 |
| API/结果 | 在`CommandReceiptCoordinator`/`McpMutationPort`增加或以严格等价typed接口实现四个方法族：recovery acquisition、fenced phase CAS、mark waiting、recovery terminal success/failure。每个写方法接收`identity + lease + expected exact pointer`；acquisition/readback结果显式区分`acquired / held / waiting / replayed / failed_terminal / ownership_lost`，expired抛既有replay-expired typed error。不得以boolean或message matching吞掉分类。 |
| 数据/事务 | 复用唯一`command_receipt`及既有stale/due索引，无新表/列/raw claim SQL。eligible仅为：带合法exact recovery pointer的expired external `processing`、due `external_unknown/waiting`、lease-expired `external_unknown/held`。CAS同时比较tenant+command+digest+operation+status+完整pointer+旧owner/epoch/expiry/due；成功以同一transaction读取的DB clock统一落为`external_unknown/held`：owner/expiry非NULL、due为NULL、`failure_kind=unknown`、`result_json=SQL NULL`、terminal字段为空并保留exact pointer。stale processing首次转换固定净化`failure_code=provider_outcome_unknown`，waiting/held重取保留原合法failure code；epoch+1且仅此时增加一次attempt counter。P2034重用同一新owner ID重试完整transaction，每次重读DB clock/current row。 |
| CAS readback | P2025仅表示CAS未命中，必须退出失败transaction后以fresh RepeatableRead、fresh DB transaction time和同一strict decoder重读。同owner幂等`acquired`必须完整匹配该attempt的postcondition：目标新epoch、`attempt_count=expected_old_attempt_count+1`、exact pointer、合法held NULL矩阵，并且`DB transaction_time < lease_expires_at`；等于或超过expiry返回`ownership_lost`，同owner/目标epoch但attempt不符则fail closed。completed为`replayed`；terminal failed为`failed_terminal`；expired抛replay-expired；其他owner/更新epoch且未过期为`held`；合法not-due无owner为`waiting`；exact pointer仍处于可取得stale/due状态为`ownership_lost`。missing、identity drift、pointer drift/partial/corrupt及其他未分类状态抛`CommandReceiptCorruptError`；不得用CAS前snapshot，不得把loser返回acquired。行锁commit后contender必须败并fresh-readback，rollback后contender按新的DB clock重新判断并可成功。 |
| 状态/退避 | mapper/API显式区分`external_unknown/held`（owner+expiry，due NULL）与`external_unknown/waiting`（owner/expiry NULL，due非NULL），其余组合fail closed。初始external receipt的`attempt_count=1`不计作reconcile；成功acquisition后的`reconcile_attempt=attempt_count-1`，首次为1。delay为attempt>=7时60,000ms，否则`min(60,000,1000*2^(attempt-1))`；`lower=delay/2`，注入`randomIntInclusive(lower,delay)`且返回必须为闭区间内整数，`next_attempt_at=DB transaction_time+jitter_ms`，非法依赖值fail closed。端点为attempt1 `500..1000ms`，attempt7及长期cap `30000..60000ms`。当旧`attempt_count=2_147_483_647`时新acquisition会溢出，必须先拒绝；旧值为上限减一时仍可原子增加到上限。 |
| Phase/Fence | 纯state冻结合法迁移：Begin `pending_committed`或Complete `handle_bound` →同operation `provider_call_intended`；intended→`provider_response_observed`；initial/intended/observed→`local_finalizing`；`local_finalizing`无phase后继。全程operation/kind/ref不变，逆向、跨operation、same phase和跳出图均fail closed。phase、waiting、completed、terminal failed均在同一transaction读取DB clock，以tenant+command+digest+operation+status+owner+epoch+exact pointer+`lease_expires_at > transaction_time` CAS；`DB now >= expiry`即使未takeover也失败且行不变。上述写不增加attempt counter，失败CAS、rollback和P2034 attempt也不得产生已提交增量。 |
| Fence/终态 | 旧holder/旧epoch/same-owner ABA在phase、waiting与两种terminal写均为loser。waiting清owner/expiry、写DB-clock due并保留epoch/pointer；terminal success/failure在同一transaction清空owner/expiry/due与recovery kind/ref/phase。terminal replay只读持久result/error，不产生recovery acquisition。 |
| 删除/禁止 | 删除或停止使用任何generic external failed reclaim、仅按owner/epoch不比pointer的recovery写路径、含糊的external_unknown lease映射；不实现provider inspection/invoke、Begin/Complete orchestration、后台scan/worker、指标、IAM contract、P4c cleanup或P5 cutover。 |
| 验证 | 先保存旧实现RED，再最小GREEN。运行format/lint/typecheck、unit/contract/architecture、Prisma validate/generate/schema check、fresh真实PG双pool矩阵、完整integration/full/build/smoke/production smoke；冻结后SPEC/QUALITY双审，Root在pre/post-commit各用不同fresh DB/Redis复验并清理。 |

P4b-3 的强制RED矩阵：stale processing、due waiting与expired held三种acquisition并断言成功后完整数据库shape一致；A取得held后死亡，lease到期后B/C双pool仅一winner且旧A所有写失败；same-owner ABA；epoch与signed-Int attempt边界；A持receipt行锁跨expiry后commit/rollback两种结局；unknown→held→waiting→held两轮中每个旧epoch均拒绝；P2025 winner分别停在held、转waiting、completed、terminal failed时loser得到上述确定readback结果；幂等readback对同owner/目标epoch/exact pointer分别覆盖未过期且`attempt_count=expected+1`返回acquired、expiry等于DB now与早于DB now均返回ownership_lost、attempt不符抛corrupt，provider spy均为0且readback不改行；无contender但DB now等于/超过expiry时phase、waiting、completed、terminal四类写全部拒绝，另有未过期正向路径；wrong kind、cross-operation phase、partial/blank pointer、held/waiting非法空值组合fail closed；合法phase图各边通过，逆向/same/cross-operation/`local_finalizing`后继全部失败；phase CAS比较exact pointer。completed与terminal failed原子清全部recovery/lease/due且fresh replay不acquire。equal-jitter以确定随机源覆盖attempt1上下端点、attempt7上下端点、长期cap、非整数/越界随机值和计数上限。所有失败CAS、rollback/P2034及非acquired readback均不增加已提交attempt；本卡没有provider port调用，相关spy必须为0或不存在。

本授权卡通过双审前不派写；双审只评估上述边界、可实现性、并发/事务正确性、测试可证伪性和与既有P4b计划的一致性。发现Blocking/Important先由Root修卡重审，不让writer自行裁决；通过后只授权本卡文件集与RED→GREEN，不默认授权P4b-4/5。

P4b-3 R0授权卡审查结果为SPEC `0/3/1`、QUALITY `0/2/1`，未放行。R1已吸收全部问题：冻结四个typed方法族与结果union、P2025 fresh readback矩阵、合法phase图、所有held写的DB-clock未过期CAS、三类acquisition统一落库shape、attempt只在成功acquisition增加，以及equal-jitter整数闭区间与端点RED。R1仍不授权实现，需对同一Root commit重新双审。

P4b-3 R1授权卡的SPEC与QUALITY均为 `0/1/0`，共同发现同owner幂等readback未证明lease在fresh DB clock下仍有效，因此仍未放行。R2补充完整acquisition postcondition：目标epoch、expected attempt增量、held NULL矩阵、exact pointer和`DB now < expiry`缺一不可；过期为typed ownership-lost，attempt漂移为corrupt，并加入等于/早于expiry及attempt drift的最小RED。SPEC另确认IAM仍需对齐但不进入P4b-3，Root已把actor/subject代表关系重验和三方审计owner加入P4b总体生产门。R2仍需在同一Root commit上重新双审。

P4b-3 R2任务板冻结为Root `aec22bee44657446bac542839d28c10f77df8b9d`、文件SHA `9a11d71b56505231777b9d8bb9320ea7b707e2b763dad4ea5f6e3558b071ec19`，child保持clean `4e26112848d11afd5d02d2b9d12553da35bf2016`。SPEC R2与QUALITY R2均为Blocking/Important/Minor `0/0/0`，确认方法/result union、三类CAS、fresh readback、lease validity、phase图、attempt/jitter、terminal清理与IAM分界均可实施。仅据此放行P4b-3任务卡所列文件与RED→GREEN；不授权P4b-4/5、provider I/O、Nest装配、IAM或其他仓。

#### P4b-3 首轮候选冻结（2026-09-11）

writer从clean child `4e26112848d11afd5d02d2b9d12553da35bf2016`新增unit RED 33/33失败和真实PG compile/collect RED，再在获准范围实现typed acquisition/result union、三类recovery CAS、DB-clock lease与epoch/attempt fence、fresh P2025 readback、合法phase图、waiting equal-jitter、两种terminal原子清理及独立`McpRecoveryMutationPort`委托。候选仅修改6个tracked并新增2个测试：`src/application/command-receipt.ts`、唯一Prisma receipt repository、纯recovery state、`mcp-transaction.ts`、`mcp.ports.ts`、`test/architecture/mcp-p4b.test.ts`，以及新unit/真实PG integration；无IAM/provider/RPC/schema/generated/package/wire改动。

冻结为HEAD `4e26112848d11afd5d02d2b9d12553da35bf2016`、tracked `f8d99feedeefc8c0a19bee7607ac194892009493a0dd3e798c41884bf51a08`、untracked names `3ee685a51c8e44e988a95d677cb49ae54fad960ec3bcd82e43bbc2b530990022`、untracked manifest `dfdc870b71bafc1c762585282cfabe8287c82997eea38c90174be5b2fb679eff`；新integration SHA `06fd3b4dff575179615486c60c4a28a74cd5934a9f4c9e3dfc57f7df6786528f`、新unit SHA `dfda796b9c3627bb00bc07aeadb8d5d7a4c2f63f9b5fddeada1ff797d3963594`。writer验证：unit 36 files/449、architecture 9/51、integration 21/227、full 73/764、smoke 2/15均0失败/0 skip；format/lint/typecheck/contract digest/Prisma/schema/build/production smoke/diff check全exit 0。fresh数据库删除并确认不存在，Redis DB11为0 key。

审查必须裁决一个显式风险：当前`markRecoveryWaiting()`按`attempt_count-1`推导reconcile attempt，标准recovery acquisition先把初始1增至2，首次等待正确为attempt1；但该API也接受仍为`processing/held`且`attempt_count=1`的fresh provider-unknown路径，此时推导0并fail closed。P4b-3任务卡的phase/waiting写允许processing，而P4b总体状态机要求fresh provider may-have-sent能进入unknown waiting；不得靠P4b-4隐式先acquire未过期processing lease。SPEC/QUALITY需判断本片是否应增加显式fresh-unknown transition/明确attempt1语义，或缩窄现API并把独立fresh transition写入P4b-4卡。双审前候选不提交。

首轮候选SPEC为Blocking/Important/Minor `0/1/0`，QUALITY为`0/2/0`，未放行。原writer只修以下两项并重新冻结：

1. `markRecoveryWaiting`按持久状态选择backoff attempt：合法fresh `processing + attempt_count=1`使用backoff attempt1，但返回`reconcileAttempt=0`；已acquired的`external_unknown/held`继续使用`attempt_count-1`。两者都不增加attempt/epoch，清owner/expiry、保留exact pointer并以DB clock写due；`external_unknown/held`的reconcile attempt 0仍fail closed。新增真实PG RED覆盖fresh processing intended→waiting、500/1000ms两端、attempt仍1，并保留held attempt2→reconcile attempt1回归；不得先acquire未过期processing或改计数规避。
2. 新增真实PostgreSQL P2034 rollback/retry证据：acquisition的首个transaction callback完成CAS后制造精确P2034使其整体回滚，第二attempt成功；断言相同recovery owner、至少两次DB clock/current-row读取、最终epoch与attempt各只`+1`。另对`runRecoveryWrite`选择`markRecoveryWaiting`制造同类P2034，断言失败attempt的due/phase/terminal写全部回滚，成功due来自第二attempt DB clock且attempt不变。不得手造错误跳过实际transaction callback，也不得加入provider编排。

整改优先只改唯一Prisma receipt repository与新`mcp-recovery-cas-postgres.integration.test.ts`；若现有typed retry委托无法注入真实P2034，可在已授权`mcp-transaction.ts`内做不改变公开API的最小修正，但必须先报告。其他7文件保持冻结，IAM/provider/RPC/schema/generated/package/wire仍禁止。修复后以fresh PG重跑聚焦与完整门禁，重新冻结并对同一对象双审。

P4b-3 R1按授权仅继续修改唯一Prisma receipt repository和新真实PG测试，`mcp-transaction.ts`无需再改。旧逻辑下fresh processing lower/upper两例RED失败；GREEN后聚焦35/35，确认fresh processing使用backoff attempt1但返回reconcileAttempt0、attempt/epoch不增，held仍按`attempt_count-1`且0 fail closed。真实acquisition P2034在首callback完成CAS后由数据库产生并整体回滚，第二attempt以同owner重读DB clock/current row，最终epoch与attempt只+1；真实mark-waiting P2034通过`PrismaMcpTransaction`证明失败due回滚、第二attempt due来自新DB clock且计数不变。

R1冻结为child HEAD `4e26112848d11afd5d02d2b9d12553da35bf2016`、tracked `61f93a9d30110799e87342215ed3c36341caf54756488506a83376ad15a3cc3b`、untracked names `3ee685a51c8e44e988a95d677cb49ae54fad960ec3bcd82e43bbc2b530990022`、untracked manifest `1cc074eb7592e6b0cdd41b23289396fb98e815937f036f59c944dbdcbab07588`；repository SHA `989729c5c925540cf55d2245ff8995e2675ddcdb58a821531d4c24d892afd0c3`、integration SHA `ebfb14225e076dce5a49b70e1e6b8d85be6b19f608247d07ce30ff2fb7872fb3`、unit SHA不变`dfda796b9c3627bb00bc07aeadb8d5d7a4c2f63f9b5fddeada1ff797d3963594`。writer最终门为unit449、contract22、architecture51、integration232、full769、smoke15且0 skip，format/lint/typecheck/contract/Prisma/schema/build/production smoke/diff check均exit0；两个fresh数据库已删除，Redis DB12为0 key。一次开发中聚焦复跑的既有row-lock rollback用例因固定10ms lock timeout偶发P2039，未改实现/用例后复跑35/35；QUALITY必须判断其是否暴露不稳定fault harness，不能用复跑直接豁免。R1仍待双审与Root复验，未提交。

R1候选SPEC为`0/0/0`；QUALITY为`0/1/0`，确认上述P2039是实际recovery acquisition缺口而非可豁免抖动。生产Prisma固定`lock_timeout=10ms`，原30ms holder用例若contender及时发出CAS会收到`P2039`/PostgreSQL `55P03`，而当前acquisition retry只接受P2034。原writer只在唯一Prisma receipt repository与新真实PG测试补最小RED/GREEN：用barrier确认contender已发出CAS，holder保持锁直至捕获至少一次真实`P2039 + modelName=CommandReceipt + database error 55P03`后再释放；commit分支最终fresh-read为held，rollback分支最终acquired，同owner且DB clock/current row重读，epoch/attempt只提交一次。仅recovery acquisition边界增加严格classifier并纳入现有有界transaction retry；畸形P2039、错误model和非55P03必须原样透传。不得扩大通用`isPrismaTransactionWriteConflict`，不得让phase/waiting/terminal或provider路径宽吞lock timeout。修复后重新冻结与双审。

P4b-3 R2按上述最小范围完成：仅继续修改唯一Prisma receipt repository与新真实PG测试。RED在真实CAS已经发出后稳定取得commit/rollback两分支的`P2039 + modelName=CommandReceipt + PostgreSQL 55P03`；GREEN只在recovery acquisition边界严格重试该组合，缺adapter metadata、错误model及非55P03均原样透传。完整recovery PostgreSQL文件连续三轮均为38/38，证明commit分支最终held、rollback分支最终acquired，均为同owner、两次transaction attempt、重新读取DB clock/current row且epoch/attempt只提交一次。

R2冻结为child HEAD `4e26112848d11afd5d02d2b9d12553da35bf2016`、tracked `5b3e0a9fa01050b16d033fc3791c531d39526c7a5e253254b8d2d140d68bc905`、untracked names `3ee685a51c8e44e988a95d677cb49ae54fad960ec3bcd82e43bbc2b530990022`、untracked manifest `0c5bd9676e8d6f651b5d508d27dca8e28e5c10c984bfb5510910b130f812239d`；repository SHA `16eab33746b2c56cab3ff34a20fd834863911c75b58b5685a6aeeb0f6aff4ce9`、integration SHA `90b03846e05bd7dadcd59076b02443af3511adf7240d98189741f02d8a88c1ff`、unit SHA不变`dfda796b9c3627bb00bc07aeadb8d5d7a4c2f63f9b5fddeada1ff797d3963594`。writer已通过format/lint/typecheck、unit 449/449、contract 22/22、architecture 51/51与fresh schema apply；contract digest、Prisma validate、schema drift、完整integration/full、build、smoke/production smoke与diff check尚待Root独立完整矩阵，不能作为候选验收证据。writer遗留数据库`kokoro_p4b3_r2_full_20260911_1010`经Root确认0连接后删除并确认不存在，Redis DB13为0 key。R2仍待同一冻结对象SPEC/QUALITY双审；不授权P4b-4、IAM/provider/SecretStore、Nest装配、schema/generated/package/wire或其他仓。

R2候选SPEC为`0/0/0`；QUALITY为`0/1/0`，未放行。`acquireRecovery()`在ReadCommitted transaction内先`findUnique`取得receipt行，再用独立`findFirst`判断`result_json IS SQL NULL`；两次statement之间若合法winner提交completed或terminal failed，旧行与新SQL NULL判定会被组合并误报corrupt，不能进入fresh terminal readback。原writer只修唯一Prisma receipt repository与新真实PG测试：用barrier暂停首次row read后、SQL NULL判定前，由另一pool原子完成success或terminal failure，旧实现RED必须得到corrupt，GREEN必须返回`replayed`或`failed_terminal`且provider调用为0。实现必须让row内容与SQL NULL事实来自同一数据库快照，或用完整旧值谓词把变化分类为acquisition contention并在transaction外fresh readback；不得宽吞corrupt、降低CAS谓词、扩大到provider/IAM/RPC/schema/generated/package/wire或其他文件。修复后重新冻结并对同一对象双审，Root仍不提前运行验收矩阵或提交。

P4b-3 R3最终仍只修改唯一Prisma receipt repository与新真实PG测试。真实PG RED为completed与terminal failed各一例，均在首次`findUnique`返回后由另一pool提交终态，旧实现稳定得到`CommandReceiptCorruptError`；直接把主acquisition改为RepeatableRead的中间方案导致完整文件8例失败并已完全撤销。最终GREEN保留ReadCommitted，通过完整旧row谓词把第二次SQL NULL查询前的合法变化分类为局部`RecoveryAcquisitionReadContentionError`，退出原事务后使用既有fresh RepeatableRead readback；completed返回replayed、terminal failure返回failed_terminal且无provider port/I/O。完整recovery PG连续三轮40/40，既有P2025/P2034、严格P2039/55P03、fresh processing、lease/epoch/attempt fence全部保留。

R3冻结为child HEAD `4e26112848d11afd5d02d2b9d12553da35bf2016`、tracked `b18eb703080eb2bd3dcce51692cc2cda0d35e40979a20222e561e4fa5d96283f`、untracked names `3ee685a51c8e44e988a95d677cb49ae54fad960ec3bcd82e43bbc2b530990022`、untracked manifest `487f88bbb02c52fc0986a4703c846ae42086da4182126685bab09e8b9ce72942`；repository SHA `688fce4a8648a37abd6aaf2bc58973f65ef6e765b40e0afdd4dce6b1c4d4e812`、integration SHA `e04a6093c5ea2ff475e7d9110c16f06b4689273ca6cdc3d7d2fda221c183bd52`、unit SHA不变`dfda796b9c3627bb00bc07aeadb8d5d7a4c2f63f9b5fddeada1ff797d3963594`。writer报告format/lint/typecheck、contract digest、Prisma validate、schema、build、production smoke与diff check均exit0；unit449、contract22、architecture51、integration237、full774、smoke15均0失败/0 skip。writer创建的全部`kokoro_p4b3_%`数据库已删除并确认不存在，Redis DB13/14均0 key。上述仍仅为writer证据，R3待同一冻结对象SPEC/QUALITY双审与Root独立pre/post-commit复验；IAM attestation owner contract仍是P4b整体与P5 cutover门，不属于本卡。

#### P4b-3 验收（2026-09-11）

R3 的 SPEC 与 QUALITY 双审均为Blocking/Important/Minor `0/0/0`，审前审后HEAD、tracked/untracked manifest及三份重点文件SHA一致。Root使用Node 24.20.0、pnpm 11.25.0、本机PostgreSQL 18.4与Redis 8.8.0，在fresh数据库`kokoro_p4b3_r3_root_pre_20260911_093218`和空DB15完成pre-commit：format/lint/typecheck、contract digest `6eb170d12bd046aa70b2a1b8aa775c6303e46ffc997cb4193f77fc230072d3b5`、Prisma validate/generate、schema、unit449、contract22、architecture51、integration237、full774、build、smoke15、production smoke、public FK=0与diff check均exit0。Root精确暂存8个获准文件，提交child `f9dc3a3d6e5f382cd1d609b4e604b2429991e67e`（`feat(capability): add MCP recovery CAS`）。

提交后Root改用fresh数据库`kokoro_p4b3_r3_root_post_20260911_093648`与空DB14重复同一完整矩阵，仍为integration237/237、full774/774、smoke15/15且全部静态/contract/Prisma/schema/build/production smoke门通过；两个Root数据库均在0连接后删除并确认不存在，Redis最终0 key，日志为`/tmp/kokoro-p4b3-r3-root-{precommit-20260911_093218,postcommit-20260911_093648}.log`。首次pre-commit启动脚本因shell变量转义错误只运行到Prisma generate，Root立即中止并精确删除其创建的字面名数据库，源码冻结hash保持不变，该次不计验收。P4b-3只验收caller-driven recovery CAS/state，不包含provider recovery orchestration、Docker或真实IAM/provider/SecretStore sandbox；IAM版本化attestation contract、generated consumer与真实sandbox仍阻塞P4b整体验收和P5 cutover。

#### P4b-3 架构状态校正与粒度整改门（2026-09-11）

Root 在记录上述功能验收后补跑仓库级 `python3 scripts/verify-ten-repository-standard.py`，实际为 exit 1 / 223 项；其中 Capability 的真实新增阻断包含 `prisma-command-receipt.repository.ts` 1626 行与 `mcp-transaction.ts` 905 行均超过 800 行。该结果推翻“P4b-3 已完成架构验收”的表述，但不推翻 `f9dc3a3` 已通过的行为、事务、并发和契约证据。基线日志为 `/tmp/kokoro-p4b3-remediation-baseline-20260911.log`。Root topology 仍通过；Root pytest 为 82 passed / 2 failed，两项既有失败分别是工程手册示例数断言与 TypeScript 手册旧固定标题断言。

P4b-3 当前状态因此校正为“功能提交完成、架构粒度整改待验收”。整改仅拆分 recovery persistence/CAS 与 recovery transaction delegation，保持 `f9dc3a3` 行为、Prisma schema/generated、17个RPC、provider/IAM/SecretStore/Nest装配、公开契约和全部 Skills/MCP typed identity 不变；`P4b-4` 在整改经双审、Root 完整 pre/post 矩阵及仓库标准门差异复核前不放行。IAM 对齐仍按本节既有跨仓门串行推进：IAM owner 先发布版本化机器契约，Capability 后续只消费固定版本 generated client，不在本整改内手写或复制 IAM wire。

#### P4b-3-G 粒度整改放置表与任务卡

| 项 | 结论 |
| --- | --- |
| Owner | `kokoro-capability` 当前、`kokoro-platform/modules/mcp/authorization` 目标；command receipt 通用事实仍由 Capability owner 写入，MCP authorization recovery 是唯一当前 recovery consumer。原 `capability_owner_p1b` 继续作为子仓单一 writer，Root 独占 Git。IAM/Agent/provider/SecretStore owner 不变。 |
| 当前事实 | Root `17063692`、child clean `f9dc3a3`；功能矩阵已通过，但 `prisma-command-receipt.repository.ts` 1626 行、`mcp-transaction.ts` 905 行触发 Root `file-granularity`。Recovery persistence 直接堆入通用 receipt repository，五个 recovery delegate 直接堆入通用 MCP transaction。 |
| 目标职责 | 通用 receipt repository 只负责 admission/claim/inspect/local terminal；纯 row-state 文件只负责 Prisma row 到 typed receipt state 的不变式映射；recovery acquisition 文件只负责 DB-clock acquisition、P2025/P2034/严格 P2039-55P03 与 fresh readback；recovery repository 只负责完整 pointer/fence 下的 phase/waiting/completed/terminal CAS；MCP authorization recovery transaction 只负责 request boundary、typed pointer decode 与 recovery repository 委托。 |
| 目录方案 | 采用既有 persistence 目录新增 `prisma-command-receipt-state.ts`、`prisma-command-recovery-acquisition.ts`、`prisma-command-recovery.repository.ts`，采用既有 MCP authorization 目录新增 `mcp-authorization-recovery.transaction.ts`。相比把全部文件放入 `src/modules/mcp`，通用 receipt row/state 不被错误归为 MCP 资源；相比继续扩展两个原文件，变化原因和 800 行门无法闭环；相比新建 `recovery/` 子目录，当前四个文件已有稳定职责且无需单文件目录。P5 再随物理 Platform cutover 处理 transitional `infrastructure` 路径，不在本片搬全仓。 |
| 粒度 | 四个新文件均有独立变化原因和多个调用/测试点；不建立 BaseRepository、CQRS、DTO 或 optional compatibility facade。`PrismaCommandReceiptRepository` 停止实现 recovery port；新增 `PrismaCommandRecoveryRepository` 实现既有 `CommandReceiptRecoveryCoordinator`；`PrismaMcpTransaction` 仅实现既有 `McpMutationPort`，新增 `PrismaMcpAuthorizationRecoveryTransaction` 实现既有 `McpRecoveryMutationPort`。本切片触及和新增的手写 production TypeScript 文件均不超过 800 行；既存 `connector-authorization.service.ts` 850 行违规另片治理，不据此扩大本片。 |
| 依赖 | receipt state 仅依赖 application typed contract、generated Prisma row/JSON sentinel与 typed errors；两份 recovery persistence 可依赖 state、Prisma clock/retry和纯 `mcp-authorization-recovery-state`，不得依赖 orchestration/RPC/provider/IAM/Nest；MCP recovery transaction 依赖既有 typed port、request boundary与 recovery repository。禁止循环 import、复制 mapper/CAS、raw SQL、第二 Prisma client或新 injection token。 |
| 数据/API | Prisma schema/generated、transaction isolation、完整 CAS predicate、lease/epoch/attempt/backoff、terminal cleanup与 `f9dc3a3` 测试语义零变化；Proto/OpenAPI/17 RPC/digest零变化。Skills 保持 `series_id/skill_id/source_ref=skill:<skill_id>/installation_id`；MCP 保持 `connector_id/server_id/connection_id/authorization_id/invocation_grant=mcp-grant:<uuid-v4>`，不存在 `grant_id`。 |
| 删除项 | 从原 receipt repository 删除 recovery imports/helpers/implementation，从原 MCP transaction 删除 recovery port实现与 pointer decode helper；同步删除测试对旧类承载 recovery 职责的依赖。不保留 re-export alias、delegating compatibility methods或双实现。 |
| 验证 | 先加 architecture RED 固定职责、依赖方向、无重复实现和本切片触及/新增 production 文件 <=800；更新既有独立 unit/真实PG recovery测试到新 owner并完整通过。随后 format/lint/typecheck/contract/Prisma validate+generate/schema/unit/contract/architecture/real integration/full/build/smoke/production smoke/public FK/diff；Root 重跑 standard/topology/pytest，对比 Capability `file-granularity` 至少减少2且不得新增违规；同一冻结对象 SPEC/QUALITY 双审和 Root pre/post-commit。 |

任务 `P4b-3-G / P0`：基线为上述 Root/child commit；writer 只可修改原 `prisma-command-receipt.repository.ts`、原 `mcp-transaction.ts`、新增四个放置表文件、`test/architecture/mcp-p4b.test.ts`、`test/unit/mcp-recovery-cas.test.ts`、`test/integration/mcp-recovery-cas-postgres.integration.test.ts` 及确因 constructor/import 编译所需的既有 MCP transaction 测试。上述触及/新增 production 文件必须全部不超过800行。禁止修改 schema/generated/package/lock/contract/RPC/service/runtime/module/provider/IAM/SecretStore/其他仓与子仓文档；既存 `connector-authorization.service.ts` 粒度违规不在本片。若需要越界，先停写报告。交付状态依次为进行中、待审查、待集成验证、已验收；P4b-4 保持阻塞。

IAM 后续独立切片 `IAM-ATTESTATION-CONTRACT / P0` 串行位于 P4b-3-G 之后、P4b 整体验收之前：IAM owner 先裁决 Agent 签发 evidence 与 IAM 当前授权/委托验证边界，发布 `internal-owner` 版本化 machine contract、生成 artifact 和真实 sandbox；Capability 再以独立消费者切片替换手写 `HttpAttestationVerifier` wire。该切片不得复用 `authorization/check` 充当万能 permission bag，不共享 Prisma schema/DTO，也不得改变上述 Skills/MCP resource identity。Manus v2 `skill.list` 与 `connector.list` 的当前官方文档再次确认“先 list 获取 opaque ID，再由 task.create 引用”的原则；Kokoro 只借鉴该生命周期，不复制 Manus wire 或混淆安装/展示/provider字段与资源 ID。

#### P4b-3-G 验收（2026-09-11）

P4b-3-G 候选严格限定为授权的9个文件，SPEC 与 QUALITY 对同一冻结对象均为 Blocking/Important/Minor `0/0/0`。四个新职责文件为299/532/426/169行，原 receipt repository 与 MCP transaction 缩减为557/740行；未改schema/generated/contract/RPC/module/runtime/provider/IAM/SecretStore，Skills/MCP typed opaque identity 不变。Root精确暂存9个路径并提交child `9f237f95b90c5699f8bc54eb202fb0639c5d47fa`（`refactor(capability): split MCP recovery persistence`）。

Pre-commit 在Node 24.20.0、pnpm 11.25.0、fresh PostgreSQL与Redis DB15上通过format/lint/typecheck/contract/Prisma/schema、unit449、contract22、architecture52、integration237、full775、build、smoke15与production smoke；验收harness最后把含Prisma `?schema=public` 的URL直接传给`psql`，因`invalid URI query parameter: schema`以exit2结束，未计为完整harness PASS。Root随后独立确认该临时数据库已删除、Redis DB15为0 key、generated无漂移。

Post-commit 首次运行因PostgreSQL URL未显式携带本机角色，在`schema:check`得到Prisma P1010并由trap清理，不计通过；修正为显式`nako@localhost`后，Root使用fresh数据库`kokoro_p4b3_g_root_post2_20260911_102810_54253`与空Redis DB14重跑完整矩阵：format/lint/typecheck/contract digest `6eb170d12bd046aa70b2a1b8aa775c6303e46ffc997cb4193f77fc230072d3b5`/Prisma validate+generate/schema、unit `449/449`、contract `22/22`、architecture `52/52`、integration `237/237`、full `775/775`、build、smoke `15/15`、production smoke、public FK=0与generated/contract diff均通过，log为`/tmp/kokoro-p4b3-g-root-postcommit2-20260911_102810.log`。trap后数据库不存在、Redis DB14为0 key。

Root standard从223项降为221项，精确消除本片引入的两个粒度违规；Capability只剩既存`connector-authorization.service.ts` 850行粒度项。Root topology为PASS；Root pytest为`82 passed / 2 failed`，两项仍是已记录的手册示例数量与TypeScript手册标题断言失配，不在本片文件集内。据此 P4b-3-G 进入“已验收”，下一个串行任务为 `IAM-ATTESTATION-CONTRACT / P0`，P4b-4 仍不放行。

#### IAM-ATTESTATION-CONTRACT 跨仓设计门与文档授权卡（2026-09-11）

| 项 | 结论 |
| --- | --- |
| Owner | Agent独占Run/Checkpoint/execution evidence、签发语义与签名proof/JWKS契约；IAM独占caller workload authentication、当前identity/membership/permission、已支持的代表关系验证与decision audit；Platform独占Skills/MCP资源、operation/request-binding、provider policy、receipt/recovery/outbox。BFF仍拥有Project，不把Project事实复制到IAM。 |
| 当前事实 | IAM `main@834fdc9` clean，已是NestJS 12 + Prisma 7.10、单一`prisma/schema.prisma`、code-first internal OpenAPI与generated `@kokoro/iam-client`；`authorization/check`只支持token-self `tenant/read|audit/read`，ADR-004明确V1禁用impersonation。Agent `e24b4aa` clean，`ExecutionIdentity`保留typed actor/subject与assertion ref，但无attestation signer/JWKS。Capability `9f237f9` clean，当前自有`RunExecutionAttestation` wire及手写camelCase、无Bearer、裸响应verifier，丢失actor/subject kind并无条件追加`user:<subject>`。 |
| 目标职责 | Agent从canonical Run、当前execution identity与lease generation签发短期、exact audience/operation/request-binding的版本化proof；IAM在具名用例中验证proof和Platform caller，每次重验当前IAM事实并记录decision audit；Platform从实际请求重算binding，只使用IAM返回的typed identity/effective owner scopes/decision reference。 |
| 目录方案 | 采用IAM既有`src/modules/authorization/execution-authorizations/`放Controller/schema/Service/Policy，由`AuthorizationModule`装配，机器契约继续由现有internal OpenAPI生成并进入现有SDK。淘汰把完整用例塞入`auth/internal-access`（该处只认证caller）、新建顶层attestation模块/第二套Proto生成链，以及把现有`authorization/check`改造为任意resource/action/subject permission bag。 |
| 粒度 | 先只授权IAM三面文档、SECURITY/CURRENT与单一ADR；文档双审后再分Agent signer owner、IAM verifier owner、Platform generated-client consumer三个串行实现片。不在文档片预先授权schema/generated/source。 |
| 依赖 | 唯一方向为Agent evidence artifact/JWKS → IAM verifier/OpenAPI/SDK → Platform adapter；Agent另消费Platform固定版本operation/binding contract以构造请求。生成类型只在adapter终止，禁止跨仓Prisma schema/DTO、相对import、请求body自报tenant/actor/subject或三仓各维护一份proof fields。 |
| 数据/API | IAM候选新路径为`POST /internal/v1/execution-authorizations/verify`，visibility=`internal-owner`，使用caller Bearer与独立endpoint scope；strict snake_case request只携Agent owner的opaque signed proof、`expected_operation`和`expected_request_binding_sha256`。成功统一`{data}`返回`allowed`、typed actor/subject、tenant/run/execution-session、effective scopes、expiry与decision/audit reference。初片不新建nonce receipt或delegation表：nonce作proof identity，exact binding+短TTL+每次当前授权复验+已有command receipt定义同请求replay-safe；若后续要求single-use，另立schema/ACK-unknown ADR。 |
| 身份范围 | 契约保留typed `user|project|service` actor/subject，但当前V1只放行IAM可用当前事实证明的direct `user -> user`；actor≠subject在版本化delegation assertion/owner完成前显式deny，project/service在对应owner resolver contract完成前显式deny，不得默认或强转为user。IAM只返回其可以当前证明的scope；Platform不根据subject猜测owner scope。 |
| 错误/审计 | 400为schema/operation/digest非法，401为caller或proof authentication失败，403为caller无endpoint资格，已认证proof但当前授权拒绝返回200 `allowed=false`+稳定reason code，409沿用`TENANT_DISABLED`，429为限流，503为验签依赖/审计持久化失败且fail closed。日志/审计不保存proof、token、signature、完整binding或request body，三方用request/trace/run/decision引用关联。 |
| 删除项 | Platform消费片删除手写IAM request/response schema、camelCase裸wire、无Bearer路径和`user:<subject>`猜测；将Capability自有的signed-proof字段事实收敛为Agent owner artifact/opaque proof引用。不保留fallback、alias或双协议。 |
| 验证 | 文档门先由SPEC/QUALITY核对TECHNICAL_DESIGN/API_CONTRACT/DATA_MODEL/ADR一致。实现后要求真实Agent signer → IAM verifier → Platform RPC → PostgreSQL receipt sandbox，覆盖caller/proof两层认证、跨tenant、operation/binding篡改、direct user、actor≠subject/project/service deny、撤权后replay、同proof同请求重试、key rotation/unknown kid/alg/TTL/skew、审计失败回滚、已完成receipt撤权后仍拒绝与无敏感日志。 |

`IAM-ATTESTATION-D / P0`文档writer只可修改IAM的`docs/TECHNICAL_DESIGN.md`、`docs/API_CONTRACT.md`、`docs/DATA_MODEL.md`、`docs/SECURITY.md`、`docs/CURRENT.md`、`docs/ADR/README.md`并新建`docs/ADR/ADR-005-execution-authorization-contract.md`。禁止修改IAM source/schema/generated/OpenAPI/SDK/package/lock/test，禁止修改Agent/Capability/BFF或Root其他文件。交付必须列出三份核心文档绝对路径、未决项、契约/schema验证命令和当前commit；SPEC/QUALITY双审前不放行Agent signer、IAM source或Platform consumer。Skills/MCP继续使用`series_id/skill_id/installation_id`与`connector_id/server_id/connection_id/authorization_id/invocation_grant`；Manus v2官方`skill.list`/`connector.list`只确认list返回opaque ID后供`task.create`引用，不发生wire或IAM owner关系。

#### IAM-ATTESTATION-D 验收（2026-09-11）

IAM 文档候选首轮审查发现 operation 只做字符串绑定、会使普通成员的合法 proof 放宽 `mcp.admin.register_server`，disabled Tenant 的 Guard 早拒绝与事务内 decision audit 冲突，以及 known-key JWKS 缓存没有撤销上界；首轮候选因此未提交。R2 由 IAM 单一 writer 在原 7 文件范围内修正并冻结为完整 dirty diff `77334dd07ca1d73cf0d566aa799c57ae9ac58453ee48965ab248f7767eb68aaf`，SPEC 与 QUALITY 对同一对象均为 Blocking/Important/Minor `0/0/0`。

R2 固定封闭 catalog：5 个 Skill installation 与除 global register 外的 16 个 tenant MCP operation 逐项映射 IAM 当前 `platform:execute`；reserved `mcp.admin.register_server` 在 global permission owner contract 出现前返回 `GLOBAL_OPERATION_UNSUPPORTED`，generic `read`、六个 Skill catalog mutation与未知 operation返回`OPERATION_UNSUPPORTED`，权限撤销返回`PERMISSION_NOT_CURRENT`。`organization:<tenant>` 只是 Platform 二次资源范围，不替代 operation permission。Execution verifier 使用 endpoint-specific deny-only passage：bad proof + disabled 先返回401且不写 authenticated decision，valid proof + disabled 在短 Prisma Serializable transaction 审计提交后返回409，审计或commit unknown返回503。JWKS只从部署固定issuer映射获取，拒绝header URL改源，固定30秒freshness、2秒/64KiB/no-redirect/single-flight与无stale fallback。

Root 精确提交 IAM 7 个文档为 `bf160be173ef473bebe8e4a93b74ec52c230f180`（`docs(iam): define execution authorization contract`）。提交前后 Prettier、`git diff --check`、`pnpm contract:check` 与 `pnpm prisma:validate` 均 exit 0；IAM 工作树干净。该提交只验收设计门，`platform:execute` code fact、Agent signer/JWKS、IAM endpoint/OpenAPI/generated SDK、Platform consumer与真实三仓 sandbox 尚未实现；严格顺序为 Agent owner → IAM owner → Platform owner，P4b-4 继续阻塞。

#### AGENT-EXECUTION-PROOF-D 跨仓设计门与文档授权卡（2026-09-11）

| 项 | 结论 |
| --- | --- |
| Owner | `kokoro-agent` 独占 proof schema、canonical claims、Ed25519 signer、active signing key 与 public key rotation/JWKS；IAM 只按 `bf160be` 验证固定 issuer/JWKS 与当前 IAM facts，Platform 只从其 owner contract计算 operation/binding并转发 opaque proof。 |
| 当前事实 | Agent `codex/production-closure-agent-p0@e24b4aab05ee6df811c21089effbe1f91d7c2f2c` clean；typed `ExecutionIdentity` 位于 `protocol/control.py`，数据库 fencing 的 `LeaseFence.generation` 位于 `domain/run/models.py`。现有两个 `is_lease_current` 路径都在等待连接前取应用clock，再以旧时间比较expiry；连接排队跨expiry时可能误报current，不能直接作为proof fresh gate。现有唯一 HTTP machine fact 为 `contract/openapi/v1/openapi.json`，没有 proof JSON Schema、signer、JWKS route或对应 provenance。 |
| 目标职责 | 每次调用 Platform 前，用 canonical Run request、execution session、typed actor/subject 与 fresh current lease generation，对 Platform owner contract给出的 exact operation/request-binding即时签发 `typ=kokoro-agent-execution+jwt`、EdDSA/Ed25519、最长60秒的compact proof；不缓存proof，不把旧generation继续用于新调用。发布只读public JWKS供IAM固定配置拉取。 |
| 目录方案 | 采用既有 `src/kokoro_agent/execution/` 承载纯proof claims与signer，key material reader按实际多文件职责放在同一业务上下文或既有启动装配；JWKS handler复用 `interfaces/http/` 与唯一HTTP runtime。淘汰新建顶层`auth/attestation`、把签名塞进`protocol/`、在worker supervisor内拼JWT、由IAM反向读取Run或由Platform自行签名。 |
| 粒度 | 先只收敛 Agent `TECHNICAL_DESIGN/API_CONTRACT/DATA_MODEL/SECURITY/CURRENT`、ADR索引与一个proof ADR；双审后再拆 machine artifact/contract RED、signer/key/JWKS GREEN、调用点/lease race与全门。文档片不预先授权source/OpenAPI/schema/package/lock/test。 |
| 依赖 | signer只依赖注入clock、nonce source、key provider与消费方定义的最小current-lease reader；该reader必须在数据库statement执行时用数据库clock核对run+owner+generation+unexpired+nonterminal，不使用连接排队前应用clock。operation/binding由Platform owner发布并在其generated client/adapter终止，Agent不复制Platform业务资源或operation policy。IAM/Platform不获得私钥，Agent不消费IAM数据库或permission graph。 |
| 数据/API | proof claims固定包含contract version、issuer/audience、tenant、typed actor/subject、run ID、execution session ID、跨语言安全范围内的正整数lease generation、exact operation、lowercase binding SHA-256、iat/exp/jti。初片不改`database/schema.sql`或Redis。worker只加载受控private key与public manifest，独立HTTP进程只加载public manifest；active private/public key必须一致。正常轮换按全部HTTP副本发布old+new → 全部worker切active signer → 从最后一次old签名起至少70秒后全部HTTP移除old，阶段未收敛不得前进。JWKS路径、认证可见性、cache/ETag和provenance由本设计门裁决后才进入机器契约。 |
| 失败边界 | run-scoped proof supplier绑定canonical RunRequest与本次LeaseFence，并在每一次真实Platform outbound call紧邻发送前做数据库执行时刻current read后即时签发；不得只在Agent build时签发、缓存proof或把mutable current run放入共享client。无法证明current、clock/key损坏或配置漂移均fail closed，不签发。该检查不宣称零在途撤销：`exp-iat <= 60s` 是claim TTL，IAM另有5秒接收clock-skew容差，真实墙钟边界须连同时钟误差说明；更强实时撤销需新增Agent assertion/introspection contract，不由IAM或Platform猜测。日志禁止private key、compact proof、signature、完整binding与identity assertion。 |
| 删除项 | 后续Platform consumer片删除Capability自有`RunExecutionAttestation`与手写IAM wire；Agent若出现临时claims/JWT组装，随正式signer片删除，不保留双schema、alias、fallback或多套key loader。 |
| 验证 | 文档先做跨IAM `bf160be`、Agent当前Run/lease/HTTP contract一致性SPEC/QUALITY双审。实现后执行`uv lock --check`、`uv sync --frozen`、Ruff format/check、Pyright、unit/contract/architecture、真实PostgreSQL lease race、HTTP JWKS acceptance、contract/provenance、wheel/sdist；覆盖连接/查询排队跨expiry、canonical request漂移、并发run不串identity、每次调用新nonce、pause/terminal/takeover/same-owner ABA、sign前后lease race、canonical JWS bytes、跨语言整数、alg/typ/kid/aud/iss/TTL+5秒skew边界、rotation overlap与混合多副本、malformed key、敏感日志和真实Agent→IAM sandbox。 |

`AGENT-EXECUTION-PROOF-D / P0`文档writer只可修改Agent的`docs/TECHNICAL_DESIGN.md`、`docs/API_CONTRACT.md`、`docs/DATA_MODEL.md`、`docs/SECURITY.md`、`docs/CURRENT.md`、`docs/ADR/README.md`并新建一个execution-proof ADR。禁止修改Agent source、database schema、Redis protocol、OpenAPI/provenance、package/lock/test，禁止修改IAM/Capability/Platform/BFF或Root其他文件。writer必须先核对`bf160be`而不复制其全文，明确当前态/目标态、JWKS route认证与多副本rotation、proof canonicalization/current-lease race及后续机器artifact路径；交付冻结hash后由独立SPEC/QUALITY审查，双审前不放行实现。

#### AGENT-EXECUTION-PROOF-D 验收（2026-09-11）

Agent 文档候选首轮双审得到 `0 Blocking / 2 Important / 0 Minor`：真实 Platform client 接线缺少 Platform owner artifact 前置门，proof integer profile 未限制 Python/JavaScript 可无损范围，且正常轮换没有显式切换 HTTP active descriptor。原 writer 在相同 7 文件范围内修正后，Root 重新冻结并运行 Prettier、`git diff --check` 与 `uv run kokoro-agent-contract-check`；SPEC 与 QUALITY 对同一 R2 对象及最终状态文本复核均为 Blocking/Important/Minor `0/0/0`。

R2 固定 `lease_generation=1..9007199254740991`、`iat/exp=0..9007199254740991` 的 strict JSON integer 边界，拒绝 bool、float、`2^53` 及以上值且不做 coercion；固定 worker private key 与 HTTP public ring/descriptor 的进程隔离和五阶段多副本轮换；固定每次调用前使用 PostgreSQL statement 时刻核对 current lease，承认签后在途 race、60 秒 claim TTL 与 IAM 5 秒 verifier skew。Skills/MCP 的 typed opaque reference 继续由 Platform owner 管理，只进入其 canonical request binding，不成为 proof claim；Manus v2 仍只作为 list-first/reference-by-ID 设计参考。

Root 精确提交 Agent 7 个文档为 `9cc24b2384b0aa66ca239ddefaa9009c0a60fac3`（`docs(agent): define execution proof owner contract`）。提交后 Agent 工作树 clean，Prettier、`git diff --check` 与 `uv run kokoro-agent-contract-check` 均 exit 0。该提交只验收设计门；proof schema/provenance、signer/key/JWKS、真实 PostgreSQL race、IAM verifier/OpenAPI/generated SDK、Platform compact-proof wire/consumer和三仓 sandbox均未实现。

下一条串行链固定为：Agent machine artifact/signer/JWKS/run-scoped supplier独立验收 → IAM ADR/API/安全设计按 Agent artifact同步 safe-integer/profile与六段交付门，再实现NestJS + Prisma verifier/OpenAPI/generated SDK → Platform以NestJS + Prisma发布最终compact-proof wire/request-binding/generated helper → Agent真实Skills/MCP client逐call接线 → Platform删除旧手写wire并闭环receipt → Root sandbox。P4b-4继续阻塞，禁止临时wire、fallback或三仓并行发明同一契约。

#### AGENT-EXECUTION-PROOF-A1 machine artifact / contract RED 任务卡（2026-09-12）

| 项 | 结论 |
| --- | --- |
| 任务 | `AGENT-EXECUTION-PROOF-A1 / P0`；发布 Agent owner-authored decoded proof schema 与跨语言 conformance vectors，先证明 contract RED，再闭环 artifact/checker/provenance GREEN。本片不实现 signer/JWKS/lease reader/Platform client。 |
| 归属 | owner=`kokoro-agent`；单一 writer=`agent_execution_artifact_writer`；Root 独占 Git/index/commit；完成候选由独立 SPEC 与 QUALITY 审查。 |
| 基线 | `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-agent`，`codex/production-closure-agent-p0@9cc24b2384b0aa66ca239ddefaa9009c0a60fac3`，writer 启动前 clean。Root 为 `5662423325a070a1b07d01f1fde381b88555fd81`，Root 既有 SQL 手册、agent gitlink与`.tmp/` dirty不属于本片。 |
| Owner/当前事实 | 当前只有`contract/openapi/v1/openapi.json`与自报`source_files`的aggregate provenance；不存在`contract/execution-proof/v1/*`。现有Pydantic parser会丢duplicate member；JSON Schema `integer`单独不能拒绝`1.0`；stdlib `json.dumps`不是通用RFC 8785。 |
| 目录方案 | 采用`contract/execution-proof/v1/schema.json + vectors.json`：同一版本下两个持续存在的owner artifacts，分别承载字段事实与conformance evidence。淘汰把schema写进测试/Pydantic、把vectors写成测试常量、复制到IAM，或把claims塞入OpenAPI。现有`contract/`正是机器事实目录，不能新建顶层auth/attestation。 |
| 粒度/依赖 | `schema.json`唯一描述decoded `{protected_header,claims}`；`vectors.json`不重新定义字段约束，只给exact raw/canonical/base64url/signing-input/signature/JWK/thumbprint及负向stage。checker可直接依赖当前稳定`jsonschema>=4.26.0`与精确RFC8785实现`rfc8785>=0.1.4`并更新lock；记录截至2026-09-12的版本、许可证、维护风险、候选比较与退出路径。PyJWT/cryptography直接依赖、数学验签和production canonicalizer留给A2。 |
| 数据/API | 不改`database/schema.sql`、Redis、Run/protocol、OpenAPI route。schema Draft 2020-12，version=`1.0.0`，root及nested object均strict；精确header/14 claims、typed actor/subject、safe-integer/token扩展、TTL/pair/canonical/base64url/16KiB metadata与stable `$id`。Skills/MCP opaque IDs不进入claims。 |
| Provenance | checker硬编码完整有序owner inventory，拒绝缺失/重复/乱序/额外source；provenance升级为逐artifact schema/vector digest加aggregate digest，保留OpenAPI/protocol现有事实。IAM后续固定`repository+commit+version+schema path/hash+vectors path/hash`消费，不使用会随无关协议变化的aggregate作为proof digest。 |
| RED/GREEN | 先新增contract test并在schema/vector不存在、inventory/digest未升级时取得预期失败，记录命令/失败点；再添加artifacts、strict raw parser/meta-schema/JCS/base64url/vector及provenance gate直至通过。expected signature由独立oracle固定，测试不得调用未来production signer生成expected；A1至少检查段重组、canonical bytes、长度与tamper fixture，A2再以直接cryptography验证数学签名。 |
| 验证 | `uv lock --check`、`uv sync --frozen`、Ruff format/check、Pyright、`uv run pytest -q tests/contract/test_execution_proof_artifact.py`、完整contract tests、`uv run kokoro-agent-contract-check`、unit/full非integration、`uv build --wheel --sdist`、`git diff --check`。mutant必须覆盖删/改artifact后重算aggregate、inventory乱序/重复/越界、duplicate member、float/bool/unsafe integer、非canonical bytes、padding、version/digest漂移。 |
| 文件范围 | 只可新增`contract/execution-proof/v1/schema.json`、`vectors.json`、`tests/contract/test_execution_proof_artifact.py`，修改`contract/provenance.json`、`contract/README.md`、`src/kokoro_agent/contract_check.py`、`pyproject.toml`、`uv.lock`、`docs/CURRENT.md`、`docs/ADR/ADR-004-agent-execution-proof-and-jwks.md`。禁止其他文件、Git mutation、source signer/key/JWKS/lease/Platform/IAM/Capability变更。越界先停写报告。 |
| 交付 | writer交付文件清单、RED与GREEN真实输出、依赖核验、逐文件hash、完整dirty diff hash、未验项；Root冻结后双审、主仓复验并精确提交。A1通过不等于execution proof可签发或IAM已对齐。 |

`AGENT-EXECUTION-PROOF-A1` 首轮冻结对象 `da1a0935128022f110ce50983bc7bad28642a99ee2e6d0c9240b800c5e1e8c80` 未放行：SPEC 为 `2 Blocking / 2 Important / 1 Minor`，QUALITY 为 `0 Blocking / 4 Important / 1 Minor`。Root 对照当前 `RunRequest/ExecutionIdentity`、ADR 与mutation实测后接受 findings：schema 删除未由canonical ingress事实支持的`kid/iss/tenant_ref/opaque_ref/run_id/execution_session_id` pattern/max，只保留已裁决非空与整体16KiB gate；JTI固定canonical 16-byte base64url末字符集合并执行decode/re-encode；vectors新增一bit signature tamper、nested/header duplicate、三数字字段float/bool/unsafe矩阵、key-source header与noncanonical JTI，且每个negative固定专属error kind、JSON pointer/keyword或单一差异，不能用同stage任意错误冒充；checker锁定全部normative metadata。

Fix R1 继续由原 writer 单一写入。除原10文件外，新增授权`src/kokoro_agent/execution_proof_contract.py`承载strict JSON/JCS/schema/vector/provenance细节，让`contract_check.py`只保留OpenAPI与薄编排；新增授权`docs/API_CONTRACT.md`、`docs/TECHNICAL_DESIGN.md`、`docs/SECURITY.md`同步A1 artifact已落地、A2及IAM/Platform仍未实现的当前态，并把`docs/CURRENT.md`日期改为2026-09-12。测试同步覆盖同stage替换、normative metadata与当前合法Run/identity映射。仍禁止其他文件、Git/OpenAPI route/signer/key/JWKS/lease/Platform/IAM/Capability；修订后重新冻结并只对首轮finding与fix diff做复审。

Fix R1 冻结对象 `43eb0aed2f0689f17a9999211cf6499789959baee82d19deb2eb3197e638a9ae` 仍未放行：SPEC 与 QUALITY 均为 `0 Blocking / 3 Important / 0 Minor`。Root 在临时副本重算 schema/vector/per-artifact/aggregate digest 后复现并接受三类 finding：exact-schema gate 必须拒绝删除 operation/binding `type` 以及向 root/object/identity/numeric/token schema 注入同版本隐藏收窄；tamper 的声明 byte index/mask 必须与实际 XOR 差异相等；31 个 named negative 必须硬绑定各自 stage、component、error kind、pointer/keyword/value/token/difference，unsafe maximum raw、pair raw 和 base64/JTI difference 不得靠同阶段失败或自报 metadata 通过。

Fix R2 仍由 `agent_execution_artifact_writer` 单一写入，只授权修改 `contract/execution-proof/v1/vectors.json`、`contract/provenance.json`、`src/kokoro_agent/execution_proof_contract.py` 与 `tests/contract/test_execution_proof_artifact.py`，并更新既有 SDD 报告。实现必须：按 approved V1 schema 对象逐节点锁定允许 key/value；由 signature bytes 推导并核对 tamper metadata；使用 hard-coded named-negative spec 核对完整 metadata 与字段集；maximum 从 positive canonical raw 做 exact token replacement，pair 校验 canonical raw/实际唯一非 no-op pointer，`ttl_over_60` 只声明真实变化，padding/JTI alias metadata 与实际差异一致。先为两审列出的 drift mutants 取得 RED，再修 GREEN；禁止修改 schema 当前事实、其他文档、package/lock、OpenAPI、数据库、Redis、signer/key/JWKS/lease、IAM/Platform/Capability 与 Git/index。R2 完成后重新冻结，SPEC/QUALITY 对新对象复审清零前不提交、不进入 A2。

Fix R2 冻结对象 `0ad70e0ea42e24f919aedd34ec2b6986c95e75ebf0df20b62209d3a533503a36` 仍未放行：SPEC 为 `0 Blocking / 3 Important / 0 Minor`，QUALITY 为 `0 Blocking / 2 Important / 0 Minor`。Root 接受四个待闭环事实：Python 普通 equality 会把 JSON `true/1` 与 `integer/float` 当作相等，导致 schema metadata 与 named-negative metadata 类型漂移在重算全部 digest 后通过；tamper 顶层 `name` 和未知字段未被锁定；31 项安全 negative policy 被压入最长 1008 字符的分隔符 DSL，使 798 行形式上低于门槛但不可审查且重复 name 可静默覆盖。

Fix R3 继续由原 writer 单一写入。只授权修改 `src/kokoro_agent/execution_proof_contract.py`、`tests/contract/test_execution_proof_artifact.py`，新增 focused `src/kokoro_agent/execution_proof_negative_specs.py`，并追加既有 ignored SDD 报告；仅当测试证明现有 artifact 本身错误时，先停写报告 Root，不得自行修改 schema/vector/provenance。实现必须先取得 RED，再加入递归 JSON type-exact comparator（每层先比较 exact Python JSON type，再比较 object/list/value）并覆盖所有 load-bearing exact comparison；tamper 对象固定完整字段集与 `name=signature_one_bit_tamper`；negative policy 使用可审查的 typed immutable ordered records，显式拒绝重复 name且不得保留 separator DSL或超长压行。测试至少覆盖三项 schema `bool/int/float` 漂移、两项 negative metadata 类型漂移、tamper name删除/重命名/未知字段、inventory顺序/唯一性/不可变性与 source max-line-length门，同时保持全部既有 digest-recomputed mutants。禁止修改 contract artifact/provenance、docs、package/lock、contract checker入口、OpenAPI、数据库/Redis、signer/key/JWKS/lease/runtime、IAM/Platform/Capability与 Git/index；R3 必须重新冻结并由同一 SPEC/QUALITY 审查清零。

#### AGENT-EXECUTION-PROOF-A1 验收（2026-09-12）

Fix R3 冻结对象 `c67194882d47588397079e1eab3e757c4d0234cd4e1b3366981e6974cf9daf1f` 为 163035 bytes/15 files；SPEC 与 QUALITY 对同一对象均为 Blocking/Important/Minor `0/0/0`。两审独立复算 digest 并证明 schema 与 named-negative 的 JSON `bool/int/float` 类型漂移、tamper name/unknown field、重复 negative name、同stage替换、unsafe raw/pair/JTI metadata 漂移全部 fail closed；31 项 policy 已移入 typed immutable ordered focused module，无压缩 DSL，validator/spec/test 分别为 800/341/798 行且最大行长 89/87/88。

Root 精确提交 Agent 15 文件为 `cd2e698c3c8b55a0136746977dbbca0c38cf308d`（`feat(agent): publish execution proof artifact`）。提交前后 `uv lock --check`、`uv sync --frozen`、三文件 Ruff format、全 Ruff check、Pyright、contract checker、artifact 57、contract 176、full default 668 passed/6 skipped/77 deselected、wheel/sdist build与`git diff --check`均通过，Agent 工作树 clean；完整 repo Ruff format仍有授权外既有79文件失败。本片只发布schema/vectors/provenance与checker，未实现签名、key/JWKS、lease supplier、IAM verifier或Platform consumer。

#### AGENT-EXECUTION-PROOF-A2 runtime signer / key / JWKS / supplier 设计与任务卡（2026-09-12）

| 项 | 结论 |
| --- | --- |
| 任务 | `AGENT-EXECUTION-PROOF-A2 / P0`；在已提交 A1 owner artifact 上分三片实现 runtime profile+Ed25519 signer、进程隔离的private/public key与JWKS、数据库statement-time current lease+run-scoped supplier。真实Platform Skills/MCP call-site继续阻塞，不在A2伪造operation/binding。 |
| 归属 | owner=`kokoro-agent`；同仓同一时刻只允许一个writer，Root独占Git/index/commit；每片RED/GREEN、冻结、SPEC/QUALITY、Root复验和独立commit后才授权下一片。 |
| 基线 | Agent `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-agent`，`codex/production-closure-agent-p0@cd2e698c3c8b55a0136746977dbbca0c38cf308d` clean。A1 schema SHA `264f2a86230ccdc20c46ff8664407c2a6f382c664970539274cca569f178ab5f`，vectors SHA `a65b9b4a1c6da8c25bf012ec0aa9c04de037f5e166c1cd7cbee7df340dc17c41`。现有 `kokoro-agent-http`仍指向`worker.main:http_main`并加载完整`AppConfig`；现有`is_lease_current`在等待数据库连接前取应用clock，不能作为proof fresh gate。 |
| 目标职责 | A2只让Agent能够按A1 exact profile安全签发短期proof、从独立HTTP进程发布public JWKS，并在每次调用前用数据库执行时刻证明同run/owner/generation仍current。Agent拥有签发与Run/lease事实，不拥有IAM permission或Platform resource/binding policy。 |
| 目录方案 | 采用现有`execution/`放纯profile/signer/private-key/supplier，现有`infrastructure/`放专用PostgreSQL lease reader，现有`interfaces/http/`放public-ring/JWKS与HTTP composition root；更新各既有INDEX。否决顶层`auth/attestation/keys/ports`、把JWT塞入`protocol/`、让HTTP加载worker私钥配置、把全部逻辑塞进`server.py`或复用A1 checker作runtime。 |
| 粒度 | A2a=`execution_proof_profile.py + execution_proof_signer.py + 新unit/contract tests + direct deps`；A2b=`execution_proof_keys.py + execution_proof_jwks.py + interfaces/http/main.py + 独立HTTP config/server + worker旧HTTP入口删除 + OpenAPI/provenance/checker/entrypoint/docs/tests`；A2c=`CurrentLeaseObservation + ExecutionProofLeaseReadPort + postgres_execution_proof_lease.py + execution_proof_supplier.py + unit/real-PG/fake-client tests`。三个切片分别提交；A2c不做生产worker/client composition，避免无消费者dead supplier或提前发明Platform wire。 |
| 依赖 | runtime profile只依赖stdlib/Pydantic/RFC8785与已提交A1事实的contract tests；signer使用PyJWT顶层公开`jwt.encode(..., json_encoder=...)`和cryptography Ed25519，不导入`jwt.api_*`私有API。A2开写时重新核验最新稳定兼容版本、许可证和Python3.11，`pyproject.toml`声明PyJWT/cryptography直接依赖并由lock固定。Signer immutable config只拥有issuer、kid与private Ed25519 key，`contract_version/typ/alg/aud`为代码常量；其公开输入只含supplier从canonical Run/fence与注入clock/nonce产生的动态值，不接受caller覆盖issuer/audience/version/kid。PostgreSQL adapter只实现domain窄port；supplier只依赖RunRequest/LeaseFence、clock/nonce/signer/lease port。Production中只有`execution_proof_supplier.py`可调用signer签发方法，composition root/key loader只构造并注入，private-key固定challenge自检只能调用key primitive；未来Platform adapter只能看到supplier Protocol。HTTP不得导入private-key provider或完整AppConfig。 |
| 数据/API | 不改`database/schema.sql`、不建proof/key/nonce表、不加Redis protocol。JWKS唯一新route为`GET|HEAD /v1/execution-proof/jwks`，机器OpenAPI/provenance/checker由A2b owner同步。200使用`application/jwk-set+json`和预计算JCS UTF-8 bytes；错误复用既有`{error,meta.request_id}`且使用`application/json; charset=utf-8`。缺失/非法ring时JWKS与ready为503、health仍200；route在bearer/identity/body/Redis/PostgreSQL前分派。 |
| 失败边界 | signer与key/profile异常fail closed且错误/日志不含key path/bytes、proof/signature、JTI或完整binding。A2只交付private loader/config的独立组件，真实worker private config的pre-side-effect装配与supplier注入留给Platform generated-client接线片，禁止先构造未消费对象。独立`AgentHttpConfig`保留host/port、stream/database/schema/internal bearer等现有HTTP业务依赖并组合public `HttpExecutionProofConfig`，但不存在任何worker/model/sandbox/provider/private-key字段；非法ring形成immutable degraded state而不阻止health监听。supplier immutable绑定canonical RunRequest+LeaseFence，每次调用重新执行lease read、生成新JTI并即时签发，不缓存proof或mutable current run；签后在途race仍由TTL与Platform/IAM重验边界承担。 |
| 删除项 | A2b删除`worker.main:http_main`与HTTP加载完整AppConfig路径，script改到独立HTTP root；配置日志由全字段+SecretStr前后缀改为显式安全allowlist。A2c不删除旧通用lease API，只新增proof专用statement-time port；最终Platform接线片再删除一次性build proof、名称选择、deployment fallback与Capability旧expanded attestation。 |
| 验证 | 每片执行lock/sync、targeted format、全Ruff check、Pyright、unit/contract/architecture/full default、checker、build/diff；A2b做socket级JWKS GET/HEAD与HTTP对象图/旧业务route回归；A2c以有界总deadline和隔离真实PostgreSQL `ACCESS EXCLUSIVE`表锁构造真实statement等待跨expiry，证明释放后不签发。A2最终只称本仓 signer/key/JWKS/supplier独立组件验收；worker签发装配、Platform owner artifact与transmitted-proof测试前不得称Skills/MCP已接线。 |

##### A2a：runtime exact profile 与 Ed25519 signer

- 新建`src/kokoro_agent/execution/execution_proof_profile.py`和`execution_proof_signer.py`，更新`execution/INDEX.md`；新增focused unit test及独立`tests/contract/test_execution_proof_runtime.py`验证runtime输出与owner vector exact compact bytes一致，不继续扩张已达798行的A1 artifact test。
- Profile固定exact header/14 claims、opaque ref非空但无额外pattern/max、safe integer token范围、operation/binding/JTI、`exp>iat`且TTL最多60秒、JCS UTF-8、canonical unpadded base64url与16KiB总长度。Skills/MCP typed IDs不进入claim。
- Signer使用注入的immutable issuer/kid/Ed25519 key与PyJWT公共API；`contract_version/typ/alg/aud`由代码固定，调用方只提供tenant、typed actor/subject、run/session/fence、operation/binding与已派生time/JTI，不能覆盖任何header、issuer、audience或version。签发前独立预计算header/payload JCS，签发后必须检查恰好3个非空segment、前两段解码与预计算bytes完全相等、每段canonical、signature恰64 bytes、总长上限，并用派生public key自验。
- 固定RFC8032 Ed25519 KAT、A1 positive exact proof、one-bit header/payload/signature tamper、wrong key/curve/alg、Unicode不规范化、bool/float/unsafe integer、63/65-byte signature、敏感错误文本。禁止A2a读环境、文件、数据库、网络或修改HTTP/worker。

##### A2b：key material、process config 与 JWKS

- Private reader使用同fd `os.open(O_RDONLY|O_CLOEXEC|O_NOFOLLOW)`/`fstat`，仅接受euid owner、regular、精确0400或0600、非空且最多16384 bytes、读取前后inode/size/mtime/ctime不变、exact single unencrypted PKCS#8 PEM且块外只允许约定ASCII空白、Ed25519类型、derived JWK/thumbprint与active descriptor constant-time一致，并做固定challenge sign/verify自检；成功后只构造进程生命周期immutable signer。
- Public ring必须是absolute path；reader从`/`开始以dirfd逐级`O_DIRECTORY|O_NOFOLLOW`打开并`fstat`父目录，owner只允许root/euid且`mode & 0022 == 0`，再以最终parent dirfd no-follow打开regular文件。文件owner只允许root/euid，mode只允许`0400/0440/0444/0600/0640/0644`。读取最多`65536+1` bytes，前后`fstat`精确比较device/inode/uid/mode/size/mtime_ns/ctime_ns；保留parent dirfd时可在加载点复核pathname dev/inode，但明确采用完整snapshot语义：in-place/partial mutation必须unavailable，atomic rename只允许得到完整old、完整new或unavailable，不能冒称能检测检查后的所有rename；deployment gate以各副本实际JWKS keys阻止旧snapshot推进。内容必须strict UTF-8、拒绝duplicate member、root exact `{keys}`且非空；每个JWK exact `{kty,crv,use,alg,kid,x}`=`OKP/Ed25519/sig/EdDSA/nonempty/canonical 32-byte x`，拒绝`d/x5*|jku|jwk|crit`及任意extra、duplicate kid，active descriptor必须命中kid+RFC7638 thumbprint。所有JWK string在排序/JCS前拒绝lone surrogate `U+D800..U+DFFF`，编码/canonical异常统一映射为脱敏unavailable。keys数组按`kid.encode('utf-8')`字节序排序后预计算immutable canonical response；RFC8785不替数组排序，也不做Unicode normalization。
- `WorkerExecutionProofConfig`与`HttpExecutionProofConfig`互不继承且非superset；独立`AgentHttpConfig`只组合后者与现有HTTP业务配置，HTTP root保留全部run/session/control/evidence行为且不加载worker/private字段。单进程readiness只验证worker private key/descriptor或HTTP public ring/descriptor本地一致；全replica五阶段顺序与`last_old_signature_at+70s`属于deployment-owned rollout gate，A2记录runbook/阻塞证据但不冒称本地进程能判断fleet。紧急轮换先停受影响signer。
- A2b明确允许修改`AGENTS.md`、`config.py`、`interfaces/http/{main,server,execution_proof_jwks}.py`、`worker/main.py`、`contract/{README.md,openapi/v1/openapi.json,provenance.json}`、`contract_check.py`、`pyproject.toml`、`uv.lock`、`.env.example`、相关INDEX/当前docs及focused unit/contract/acceptance/architecture tests；实际续派时再给精确清单。新增匿名JWKS为additive HTTP contract `1.1.0`，同步OpenAPI/provenance/checker/README；Agent治理改为worker与HTTP各自只在composition root单次解析独立配置。`kokoro-agent-http`必须只指向新HTTP root，删除`worker.main:http_main`，wheel/AST/治理门拒绝残留；不得在A2b把private signer/supplier作为未消费对象装入worker。
- JWKS先判exact known path，再判method：任何非GET/HEAD method（含POST/PUT/PATCH/DELETE/OPTIONS/TRACE与未知token）无论query/body均固定405 `execution_proof_jwks_method_not_allowed`、不读body并带`Allow: GET, HEAD`；GET/HEAD的query/body/chunked或tenant/identity/assertion输入固定400 `execution_proof_jwks_invalid_request`；随后ring unavailable固定503 `execution_proof_jwks_unavailable`，否则200。不得落入stdlib 501/HTML/`send_error`。未知path保留既有`route_not_found`语义。200为预计算JCS bytes与JWK media type，错误为稳定既有JSON envelope；200/400/404/405/503均`no-store`且无ETag/redirect，`If-None-Match`仍返回完整200。所有HEAD零body，status、Content-Type、Cache-Control与Content-Length等于对应GET representation；OpenAPI/checker同时锁GET、HEAD、permission metadata和错误响应。合法JWKS不触发auth/identity/PG/Redis；非法ring不发布部分keys，ready在连接依赖前503而health保持200；新入口下全部现有HTTP测试保持。

##### A2c：statement-time lease 与 run-scoped supplier

- 新增窄`CurrentLeaseObservation(database_now, lease_expires_at)`与`ExecutionProofLeaseReadPort`，不扩宽broad lifecycle port；reader deadline必须是非bool、finite numeric且`0 < seconds <= 2.0`（默认2秒），配置失败在connection acquisition前拒绝；同一总deadline包住connection acquisition+statement+row decode，内部timeout脱敏fail closed，外部cancellation在关闭/丢弃连接后继续传播`CancelledError`且不留backend。SQL在取得连接后只执行一条statement，用`WITH db_clock AS MATERIALIZED (SELECT clock_timestamp())`的同一值核对并返回run、owner、generation、安全范围、非空且未过期lease与nonterminal；返回值必须timezone-aware。连接/statement/row/timeout失败均不签。
- 真实PG race固定由另一事务执行`LOCK TABLE <qualified-run-table> IN ACCESS EXCLUSIVE MODE`，再启动普通SELECT reader；必须用`pg_stat_activity.wait_event_type='Lock'`证明真实排队，并由独立connection确认DB time已跨expiry后才释放。锁保持超过总deadline时有界失败、无签名/send/悬挂backend；释放后not-current。另覆盖run/owner/generation错配、paused（lease null）、terminal/expired、same-owner ABA、unsafe generation，并用mutation证明改回statement前app clock会使race test失败；row lock不得冒充该证据。
- Supplier绑定immutable RunRequest+LeaseFence；每次`issue(operation,binding)`都先fresh read，再在read返回后取得timezone-aware app instant，拒绝naive datetime，并要求`abs(app_now-database_now) <= 5s`。生成fresh 16-byte CSPRNG JTI，令`iat=floor(app_now)`、`exp=min(iat+60,floor(lease expiry))`；除`exp>iat`外，还要求`exp - max(app_now.timestamp(), database_now.timestamp()) >= 1.0`，精确覆盖0.001/0.999/1.000秒及正负5秒skew边界。每次调用都重新read/nonce/sign，signer失败不触发外部send，并发run不得串tenant/actor/subject/run/session/fence。
- A2c只提供supplier/factory、专用PG adapter、unit/真实PG/fake-client proof；architecture gate证明生产Skills/MCP client、`AgentFactory`与`WorkerDependencies`尚未引用supplier且不存在constructed-but-unused实例。真实worker注入与call-site等待Platform final Proto、21项operation manifest、逐RPC request-binding profile/vector及generated Python helper，再证明每次真实send前紧邻read/sign。

##### IAM 与 Platform 后续硬门

IAM 必须对齐，不扩宽现有`/internal/v1/authorization/check`。A2完成后维护两个独立不可变consumer pin：A1 proof profile固定repository+`cd2e698...`+`1.0.0`+schema/vector direct path/hash；A2b JWKS HTTP固定repository+最终A2b commit+HTTP `1.1.0`+`contract/openapi/v1/openapi.json` direct SHA，不能用会随无关protocol变化的aggregate代替。七份IAM设计先同步这两个owner artifact，再以NestJS模块、Prisma current-fact transaction、成熟JOSE/JWKS client实现`POST /internal/v1/execution-authorizations/verify`与generated SDK；不手写ORM/SQL事务、不复制editable Agent schema/vector、不复用Better Auth Jwks表、不建nonce/decision表。IAM pin gate对JWKS path/GET/HEAD/media/error/version任一漂移都必须在编译前失败。IAM V1 exact profile必须拒绝extra/`nbf`、duplicate、non-JCS、noncanonical base64/JTI、bool/float/unsafe integer及非exact public JWK；保持bad proof+disabled为401无authenticated audit、valid proof+disabled审计提交后409、审计或commit unknown为503。

Platform必须先裁决当前三个SkillSource Agent read RPC：推荐Agent退出source-read链，改为list/get installation获得typed `installation_id + skill_id + package_asset_ref + digest`；若保留source RPC，则Platform先发布精确operation/binding，再由IAM owner扩封闭catalog，禁止继续用IAM明确unsupported的generic `read`。Platform最终以NestJS+Prisma发布opaque `execution_proof` Proto、FQ RPC→operation manifest、逐RPC binding schema/vector及TS/Python generated helper；typed `series_id/skill_id/installation_id`与`connector_id/server_id/connection_id/authorization_id/invocation_grant`只能list-first/reference-by-ID，display/provider/URL/tool name不能替代ID。`mcp.admin.register_server`继续是global reserved。P4b-4在owner artifact、IAM SDK、Platform contract、Agent逐call接线与真实三仓sandbox前继续阻塞。

A2计划首轮冻结commit `d1194b75f9e2e0f4e5c5d36846595f600f2a4182`、plan SHA `1418188a90370c704c8b208759b5007be85f359789f32f040086bfdac430c453` 未放行：SPEC为`1 Blocking / 5 Important / 2 Minor`，QUALITY为`0 Blocking / 6 Important / 1 Minor`。Root接受public ring本地文件完整性、HTTP业务配置保留、fleet rollout owner、trusted claim来源与supplier-only调用、A2b必改文件、JWKS exact error wire、数据库总deadline/真实表锁、实际一秒寿命及A2c dead composition等finding并回写R1。R1冻结commit `90b8030eeaf8094ac804a84122d818dc754b949a`、plan SHA `ed358e8f8dcd1626e0ca2cc2dd0c225c1e0b4ecfe57180025304dd80e9da0bf0` 仍未放行：SPEC `0/3/0`、QUALITY `0/5/0`。Root再接受supplier-only不含composition调用、Agent治理/contract README与HTTP 1.1.0、IAM双pin、anchored dirfd完整snapshot语义、deadline finite/bool上界、任意HTTP method优先级与lone-surrogate拒绝等finding并回写上述R2计划。R2重新冻结并由同一独立SPEC/QUALITY只读审查；双审`0/0/0`前不授权A2a写入。即使计划通过，也只先授权A2a文件集，A2b/A2c仍需按前一卡commit与证据重新续派。
