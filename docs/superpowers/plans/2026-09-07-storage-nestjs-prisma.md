# Storage NestJS + Prisma Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 Storage 收敛为 NestJS + Prisma，在保留上传完整性、扫描、权限、幂等和对象生命周期保障的前提下退出手工框架与 SQL CRUD。

**Architecture:** Storage 独占 Blob/Upload/Asset/Artifact/Scan/receipt 事实。Nest 原生 feature module 与 provider 管理入口和生命周期；Prisma 是唯一数据建模与访问栈。现有 internal-owner Connect RPC 与 library 消费边界保持，任何 breaking change 先走 owner contract。

**Tech Stack:** NestJS、Prisma、PostgreSQL、Redis、S3-compatible SDK、ClamAV、ConnectRPC/Protobuf；精确兼容版本在 ST-D1 记录官方核验，不复制历史版本。

## 基线与权限

- Root: `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro`，起始 SHA `7170a1ff3da0e1cdb82809223cd5b6fda1f5cac5`。
- Storage: `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-storage`，分支 `codex/production-closure-docs`，起始 SHA `6cd6e77`。
- Storage 现有 37 个 tracked 修改及 5 个 untracked 文件；这些是接收审查基线，不自动归本轮所有，不覆盖、暂存或提交未交接内容。
- Root 原有 SQL 手册、Agent gitlink、`.tmp/` 修改不属本轮，不暂存。IAM/System/Capability 等其他仓由既有任务推进。
- 单仓单 writer。ST-A/ST-C 只读；Root 当前仅维护本计划与通过盘点后的 Storage 设计文档。业务写入在设计门和交接门通过后单独派发。
- Git index、commit 由 Root 串行管理。只按明确文件路径暂存。

## 规范入口

- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/AGENTS.md` §8–9。
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/docs/CODEBASE_MAP.md`。
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/docs/kokoro-handbook/standards/08-typescript-backend-engineering.md`，尤其 §1、4–7、8.4。
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/docs/kokoro-handbook/standards/03-sql-and-postgresql.md`。
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/docs/kokoro-handbook/standards/04-transaction-repository-idempotency.md`。
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/docs/kokoro-handbook/standards/05-api-rpc-and-error-contracts.md`。
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/docs/kokoro-handbook/standards/06-testing-and-quality-gates.md`。
- Storage 的 `AGENTS.md`、`README.md`、`INDEX.md`、`docs/CURRENT.md`、`docs/TECHNICAL_DESIGN.md`、`docs/API_CONTRACT.md`、`docs/DATA_MODEL.md`、`contract/README.md`。旧子仓强制四层不覆盖 Root 当前手册。

## 任务卡

以下文件集均以 Storage 绝对根目录为基准；只读范围并非写入授权。主控持有总体架构决定，不由审查员分别发明契约。

| ID / 优先级 | 目标 / 完成条件 | Agent / 模型 / 权限 | 文件集 | 依赖与验证 | 状态 / 交付 |
|---|---|---|---|---|---|
| ST-A / P0 | 接收数据与并发修改；列出 Prisma 替换必须保留的行为和阻断项 | `storage_data_review` / gpt-5.6-sol / 只读；Root 审查 | `database/`、`src/application/storage/`、`src/infrastructure/repositories/`、`test/integration/`、数据设计 | 绑定 `6cd6e77` 加当前 dirty tree；不启动服务、不改数据、不提交 | 首审与最终文档复审完成 |
| ST-C / P0 | 审查 RPC/安全 dirty diff 与 Nest 接入边界；列出契约不变量 | `storage_contract_review` / gpt-5.6-sol / 只读；Root 审查 | `contract/`、`src/interfaces/`、`src/config/`、`src/infrastructure/clients/`、`test/contract/`、API 设计 | 与 ST-A 并行；只读，无共享服务与 Git 操作 | 首审与最终文档复审完成 |
| ST-B / P0 | 记录工作区归属证据、可执行测试基线与已存在失败 | Root / 当前模型 / 运行验证；不改业务 | 现有 package scripts、工作区状态、任务证据 | 复用依赖；真实集成仅用独立数据库/任务前缀；不把 skip 当 pass | 现状基线完成；交接待用户确认 |
| ST-D1 / P0 | 技术/API/数据设计及 ADR 对齐；明确版本、目标目录、事务替换、删除和验收 | Root / 当前模型 / 文档 writer；ST-A、ST-C 复审 | `AGENTS.md`、`INDEX.md`、`docs/{TECHNICAL_DESIGN,API_CONTRACT,DATA_MODEL,CURRENT,INDEX}.md`、`docs/ADR/`；Root 本计划 | ST-A/ST-C/ST-B；未通过前不改业务与 schema | 文档复审通过；实施门仍未通过 |
| ST-I1 / P1 | Nest/Prisma 底座与首个可运行业务切片 | Storage 单一实现负责人 / 待按复杂度指派 / 未授权写入 | 设计门通过后列精确路径；不概括授权全仓 | ST-D1 + 工作区交接；RED/GREEN、DI、schema、contract、主仓复验 | 待派工 |
| ST-I2 / P1 | 上传完整性、扫描、去重、事务与幂等切片 | 同一负责人 / 未授权写入 | ST-D1 后确定精确路径 | ST-I1；真实并发/回滚/重放测试 | 待派工 |
| ST-I3 / P1 | Asset/Artifact/reference/library/reconciliation 收敛并删除旧实现 | 同一负责人 / 未授权写入 | ST-D1 后确定精确路径 | ST-I2；消费者 contract + ObjectStore/ClamAV smoke | 待派工 |
| ST-V / P0 | 独立审查、Root 集成验证与逐片提交 | Root + 只读审查员 | 当前切片文件集 | 绑定 commit，未完成/未运行项原样保留 | 待前置 |

## Chunk 1: 接收与设计门

- [x] 用户确定 NestJS + Prisma，批准推进；不重复询问框架或常规命名。
- [x] 读取 Root/Storage 基线并公开放置表。
- [x] ST-A 与 ST-C 独立只读首审完成；绑定 dirty-tree 基线及风险，主控复核并将canonical轮换由内容完整性问题调整为P1可用性/成本风险。
- [x] ST-B 运行现状 lint/typecheck/test/build、contract与真实PG/Redis基线；记录初次search_path失败和重跑。
- [ ] ST-B 修改归属完整交接：已向用户发异步确认，回复前不覆盖/暂存37+5原有修改。
- [x] 核验Nest/Prisma/Connect官方adapter与registry候选版本/peer/engines；来源/日期见Storage ADR。实际目标栈安装、ESM/DI/测试兼容尚待实施证明。
- [x] ST-D1 更新三份设计、CURRENT、AGENTS/INDEX和栈切换ADR；比较旧四层与feature-first。
- [x] 明确CHECK保护层变化、Prisma relations/Restrict、server fingerprint、稳定CreateUpload receipt、官方db push空库链；ADR仍Proposed。
- [x] 当前schema/API与设计完成只读一致性复核；Prisma生成/空库属于ST-S1隔离验证，尚不冒称通过。
- [x] 两位审查员最终复审通过，文档可交付，可进入隔离Schema验证；业务写入仍待交接。文档提交仅暂存本轮明确路径。

## Chunk 2: 实施门（设计审查后细化，不作为当前写入授权）

- [ ] 用精确文件集、行为测试和失败断言补齐 ST-I1 任务卡。
- [ ] 单一 writer 按切片 RED → GREEN → 清理旧路径 → 交付文件清单。
- [ ] Root 先审契约符合性、再审代码质量、重跑主仓验证，逐切片提交。
- [ ] 数据 owner 仅在任务专属空库显式 apply；无外键、无历史迁移账本、Prisma 单一事实源。
- [ ] 实际校验所有约束/索引；Prisma 表达能力缺口必须先裁决，不静默丢失数据库保障，也不恢复手写 CRUD。

## 验证命令与证据规则

工作目录固定 `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-storage`：

```sh
pnpm lint
pnpm typecheck
pnpm test
pnpm build
pnpm contract:lint
pnpm contract:check
pnpm test:architecture
# 接入后才存在/生效，以下不得当现有通过项：
pnpm format:check
pnpm exec prisma validate
pnpm exec prisma generate
pnpm db:apply-schema
pnpm test:integration
pnpm smoke:infra
pnpm smoke:s3
pnpm smoke:scanner
pnpm smoke:production-runtime
```

Root 当前默认门禁：`python3 scripts/verify-ten-repository-standard.py`、`python3 scripts/verify-repository-topology.py`、`python3 -m pytest scripts/tests`。旧full/owner-health runner已暂停，退出2且不接触基础设施；不执行或把它计入可执行门禁。全局失败区分Storage与其他owner，不放宽门禁。

`contract:check` 会生成文件；须在明确生成物归属/基线后执行，禁止借生成覆盖已有工作。构建/测试只能证明当时工作树；最终证据需绑定提交与主控复验。

## 当前风险与交接

- 现有 Storage dirty diff 的作者和完整交付状态待核对。
- Root CURRENT 的“仅 IAM”与用户最新多仓推进方向不同；本计划只记录 Storage，不代其他主控更新共享总状态。
- 旧子仓设计与 Root Nest/ORM-first 手册不一致；完成文档门之前不开始批量目录/业务改写。
- 当前证据见下方本轮交付记录；历史测试数量不作为本轮验收。

## 2026-09-07 本轮交付证据（设计/接收阶段）

- 两名只读审查员：`storage_data_review` / `storage_contract_review`，实际均 gpt-5.6-sol；未改文件、提交或启动服务。Root为唯一文档writer。
- 原 tracked业务diff SHA-256：`248277674c5c40a2239fbc014b11bcf53222130d57024532d23b06726b1ed6b9`（`git diff --binary`接收时，不含本轮新增文档）。
- 原新增文件：`src/application/storage/command-support.ts`、`src/application/storage/object-integrity.ts`、`src/infrastructure/repositories/storage-row-mapper.ts`、`test/integration/immutable-upload.test.ts`、`test/integration/owner-visibility.test.ts`，全部保持原样。
- Storage cwd Node24.20.0/pnpm11.25.0。lint/typecheck/build、contract lint/check与生成drift通过；未注入DB的test=114通过/5跳过。
- 复用PostgreSQL18.4 `127.0.0.1:5432`与Redis `127.0.0.1:6379/6`，仅本任务随机空库。schema apply通过，6表/0FK/25CHECK（现有SQL，不是Prisma）。
- 初次真实测试relation missing：本机role search_path为kokoro,pg_catalog而schema在public。只为测试URL增加`options=-csearch_path%3Dpublic%2Cpg_catalog`，未改全局/role。重跑integration=33通过、全集119通过，无skip；其中两个真实PG套件共5个测试，其余大量double不算真实integration。
- Root结构门禁exit1：218项，其中Storage14项。包含缺format、toolchain/TS、配置边界、旧模块目录；检查器强制src/modules与当前手册的可选容器有漂移，交治理owner，不擅改共享脚本或制造绿色。
- 未执行真实S3/ClamAV、镜像、安全扫描、十仓完整脚本和发布breaking（缺最后发布baseline），原因详见Storage CURRENT。
- 日志 `/tmp/kokoro-storage-baseline.gXiFa9/`；提交后仅文档证据，无Nest/Prisma代码交付声明。

## Chunk 2a: 下一实施卡的精确拆分（未派发、未授权写入）

### ST-I0：接收问题的契约回归

前置：dirty交接 + 设计/机器验证门。只读基线仍绑定6cd6e77和原dirty哈希，后续提交记录接收SHA。

- 拟修改：Storage `src/interfaces/rpc/errors.ts`、`src/interfaces/rpc/service.ts`、`src/application/storage/command-support.ts`、`src/application/storage/storage-application.ts`及对应contract/unit测试；这些目前属于待交接集，先不写。
- 先RED：错误metadata/detail与Connect状态一致；同command/caller digest但换payload拒绝；跨owner不互相replay；CreateUpload过期URL重签。
- 目标内部busy使用现有CONFLICT+Aborted+retryable=true，避免common Proto不存在的metadata-only code；不扩Proto编号。
- server fingerprint需与Prisma receipt schema原子落地，不能临时添加第二个SQL字段来源；因此此卡先固定RED断言，GREEN与ST-I1数据切换串行集成。
- 验证：`pnpm test:contract`、对应目标tests、`pnpm contract:check`、generated drift。

### ST-S1：Prisma schema设计验证（先于业务改写）

- 拟创建：Storage `prisma/schema.prisma`、`prisma.config.ts`、只读generated Prisma client；拟修改 package/lockfile 仅在明确授权后。
- 表/enum/键/relations/semantic_fingerprint见DATA_MODEL，不引入SQL canonical或migration账本。
- RED断言：真实catalog无FK、compound unique/native enum正确、typed relation允许tenant限定；不把删除的CHECK当仍存在。
- validate/generate/空库db push/catalog，失败恢复与连接schema显式；独立审查/主控复验。
- 设计验证可在任务隔离目录执行，未通过前不替换现有运行时schema/业务。

ST-I1/I2/I3文件集在前置验证后依业务实际拆分，禁止将此待办概括为全仓写入权限。

### ST-S1 临时设计验证授权（2026-09-07，非业务写入）

数据设计复审已确认文档可交付、允许继续Schema设计验证。角色 `storage_data_review` 续任“Prisma schema隔离验证”，模型仍gpt-5.6-sol。
仅允许在自行创建的 `/tmp/kokoro-storage-prisma-probe.*` 目录写实验schema/config/generated/log；允许复用PG5432创建自己命名的随机空库并最终清理。禁止写Storage/Root任何文件、package/lockfile/index，禁止启动/重启共享服务、修改共享role或他人数据。
具体任务：精确Prisma/client/adapter-pg7.10.0；按DATA_MODEL六表/枚举/tenant关系验证schema validate/generate/db push/catalog无FK/原生enum/unique；仅验证可行性，不声称业务移植。schema候选保留临时artifact交Root，最终canonical落地仍需后续明确写入授权。


## 文档切片交付

- Storage commit：`d715de89458a6fb15328d3cb6ac297e3acfab23a`，`docs(storage): define NestJS and Prisma cutover gates`。
- 文件集：Storage `AGENTS.md`、`INDEX.md`、`docs/INDEX.md`、`docs/CURRENT.md`、三份设计、`docs/ADR/README.md`、`docs/ADR/0001-nestjs-prisma.md`，共9文件；无业务、schema或原dirty文件被提交。
- 独立审查：ST-A/ST-C最终文档复审均无阻断；完整业务实施门仍未通过。
- Root在此提交+原dirty工作树重跑lint/typecheck/build/contract:check、生成drift、任务空库apply与真实PG/Redis全集：全部exit0，30文件/119 tests通过。此证据绑定dirty hash，不冒称干净commit单独具备dirty行为。
- 原tracked业务diff SHA-256复核仍为`248277674c5c40a2239fbc014b11bcf53222130d57024532d23b06726b1ed6b9`，原5新增文件未变；Storage仍42项原dirty内容。
- 9份文档本地Markdown链接检查与git diff --check通过。

## ST-S1 隔离实验交付与主控复验

- 状态：隔离可行性已验收；正式Schema切片未实施。执行人storage_data_review（gpt-5.6-sol），主控独立复验，实验产物已停止写入。
- 基线：Storage文档commit `d715de89458a6fb15328d3cb6ac297e3acfab23a`；原业务dirty hash保持不变。唯一实验目录 `/tmp/kokoro-storage-prisma-probe.8flQ8t`，没有修改仓库package/lockfile或运行时Schema。
- Prisma/client/adapter-pg 7.10.0；主控在自己创建的随机PG空库运行validate/generate/db push，各exit 0；8项runtime断言与6项catalog断言通过，日志 `/tmp/kokoro-storage-baseline.gXiFa9/prisma-main-*`。
- 证明范围：6表、0FK、7原生枚举、owner/digest唯一性、Artifact复合PK、fingerprint CHAR(64) NOT NULL、typed查询和checked复合connect。无生产事务/性能/失败恢复证明。
- 风险实证：unchecked scalar create产生跨tenant orphan；正式切片增加事务存在性/owner检查、写入边界architecture test及真实PG负向测试，不能只禁止UncheckedCreateInput类型名。
- 实验新增tenant/asset关系索引仍是候选，正式采用须以查询/EXPLAIN为据。早期安装失败与未限定schema的查询失败保留为实验失败证据；主控最终复验固定工具路径并使用schema-qualified catalog查询，不混算成功。
- 清理：主控自己的随机库已drop，worker两个实验库名称查无残留；未动共享role/Redis或启动新服务。
- 后续owner：Root完成原37+5文件交接确认，再向Storage唯一writer派发正式Schema/测试切片；临时实验代码不直接视为已审查生产实现。
- 证据提交：Storage `ec10e111a2dab74e9e0c9754dccbdcbd261d3288`，仅CURRENT与DATA_MODEL两份文档。storage_contract_review对稳定日志/文档独立复审无阻断；主控diff检查、三份文档链接检查通过，原tracked hash和5个新增文件hash逐项未变。

## 2026-09-08 目标启动与正式写入卡（优先于上方历史待交接状态）

用户在上一轮明确列出的交接/迁移下一步之后要求“设置目标，推进”。本任务据此接收现有Storage相关工作，不再重复询问常规接收权限。其他owner与Root共享治理修改不属本任务。

- 当前goal：完成Storage NestJS+Prisma正式迁移、可靠性与真实验收；不以隔离实验结束。
- 接收commit：Storage `93f7dd009ae65c5a2d300d2da555af16e3777cd5`，42文件原样保存。已知缺陷仍保留在CURRENT/计划中，接收不等于发布验收。
- 本轮复跑：lint/typecheck/build/contract:check、generated drift、独立空库SQL apply、PG/Redis test全集全部exit0，30文件119测试无跳过。日志 `/tmp/kokoro-storage-goal-baseline.rejrKJ`；接收前业务hash与上一轮相同。测试随机库已清理。
- 单一writer使用现有Storage独立checkout与codex分支，避免移动已接收成果；Root只写Root任务表、串行操作Git并审查，不与writer并写Storage。
- 设计门：TECHNICAL_DESIGN、API_CONTRACT、DATA_MODEL及ADR在ec10e11完成独立复审；Schema候选已由官方validate/generate/db push+catalog在空库复验。允许原子替换正式schema/运行时；目标行为的RED/GREEN是实现验收门，不构成等待实现后才允许实现的循环条件。
- 三份路径：`/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-storage/docs/TECHNICAL_DESIGN.md`、`/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-storage/docs/API_CONTRACT.md`、`/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-storage/docs/DATA_MODEL.md`。
- 未决项：正式并发/失败恢复、Nest单listener/DI/取消退出、真实ObjectStore/ClamAV、工程/供应链门禁。由以下顺序推进，无新增owner或wire breaking。

### ST-I1 / P0：核心运行时与唯一数据栈原子切换

| 项 | 授权与验收 |
|---|---|
| Owner | kokoro-storage；storage_data_review续任实现负责人，gpt-5.6-sol；Root负责集成，storage_contract_review后续只读审查 |
| 基线 | Storage独立checkout，codex/production-closure-docs，93f7dd0；本卡登记后新增的文档门提交一并作为基线 |
| 目标 | 已有十RPC+library完整运行在Nest官方FastifyAdapter/Connect插件和Prisma唯一数据栈；不是旧服务外包Nest外壳 |
| 放置 | 直接沿用TECHNICAL_DESIGN §2放置表与目标目录；feature service拥有用例，数据库provider只管理连接。淘汰全局四层/全能Repository/自制ORM，必要复杂事务组件在实际owner内 |
| 允许写入 | package.json、pnpm-lock.yaml、pnpm-workspace.yaml、tsconfig*.json、eslint.config.js、vitest.config.*、.gitignore；prisma/schema.prisma、prisma.config.ts；src/main.ts、app.module.ts、config、database、uploads、assets、artifacts、integrations、common、transport、clients、generated/prisma；删除已替代src/bootstrap、application、domain、infrastructure、interfaces与database/schema.sql并同步所有引用；test现有各主题套件和对应新回归；scripts/apply-schema.ts、reconcile-objects.ts及专用schema检查；README、INDEX、AGENTS、docs中受影响的Storage入口/设计/验收/runbook |
| 排除 | Root全部文件、其他owner、contract/proto与provenance、generated/proto手工编辑、.github/CI、Docker/compose与docker-smoke脚本（后续门禁切片）；不新增public API，不改Proto字段 |
| 数据 | 全六表一次转换避免可编辑schema双轨；Prisma7.10.0配套client/adapter。tenant/owner、claim/fence、幂等/rollback保留；fingerprint与receipt envelope随schema原子落地，CreateUpload仅存稳定ID并每次重签/终态拒绝 |
| 安全 | Connect插件自有认证/错误/取消边界，HTTP共用可信身份验证；错误detail/metadata一致；业务校验拒绝unchecked跨tenant引用；不得以类型断言/测试double模拟ORM完整性 |
| 生命周期 | Nest负责实例与启动/关闭，只有一个listener与signal owner；bootstrap无自动apply；依赖超时/取消有界，无业务SQL或provider原文泄漏 |
| 验证 | 先RED：fingerprint变payload、busy/detail、稳定receipt、Prisma单schema/旧路径退出、DI/单listener。GREEN：lint/typecheck/test/build/contract、真实PG并发/回滚、空库apply且非空拒绝、catalog无FK/native enum、生成drift；不删旧行为断言以凑绿色 |
| 资源 | 复用PG5432/Redis6379，必须自身随机库；不得启动共享服务/改role/reset他人库/flush Redis。可写任务/tmp日志；测试配置显式schema/search_path |
| 交付 | 不操作Git index/commit/branch；交付稳定文件清单和RED/GREEN日志后停止写入，Root按符合性→质量→主仓验证提交 |
| 状态 | 已派发；核心通过后再派ST-I2对象完整性/恢复与ST-V工程/真实smoke，不提前声称目标完成 |

### ST-E / P1：真实依赖验收准备（并行只读）

storage_contract_review（gpt-5.6-sol）读取现有ObjectStore/ClamAV/production smoke与运行手册，绑定93f7dd0提出隔离资源/命令、危险清理点和缺失断言。只读Storage源码与公开本机进程/端口信息；不编辑、不启动服务、不接触secret、不做Git写入。Root据报告准备资源/后续门禁，不重复worker实现。
