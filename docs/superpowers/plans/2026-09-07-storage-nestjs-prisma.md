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

### ST-E 交付与Root治理基线（2026-09-08）

- storage_contract_review固定72ab5dd只读审查完成；没有启动/清理依赖或修改源码。发现旧docker-smoke固定container名并无条件rm -f，RUNBOOK固定project down --volumes，production smoke直接SQL读object key绕过presigned PUT；后续切片必须删除这些测试旁路并隔离资源。
- ST-V资源策略：任务唯一RUN_ID、随机空DB、唯一bucket/对象前缀、唯一Compose project/container标签/host端口；仅清理创建记录内且owner标签匹配的资源。Redis6379/6仅PING；不重复启动PG/Redis。
- ST-V生产链路必须经真实API：CreateUpload→返回URL PUT→CompleteUpload→GetPackageReference→返回URL GET并验证bytes；测试不读取业务SQL/object key，不把direct provider/DB旁路称端到端。
- 后续授权文件为Dockerfile、docker-compose.integration.yml、scripts/docker-smoke.sh、.github/workflows/ci.yml及release相关workflow、对应smoke tests/docs；当前尚未派发，与核心writer串行。
- Docker CLI与Desktop/backend进程存在，但daemon API两次有界version和unix socket /_ping均未回应；39190/43310等旧MinIO/ClamAV端口关闭。目前没有真实外部依赖或镜像通过证据。已异步询问用户是否允许重启可能影响既有容器的Docker；未确认前保持原服务状态，源码推进不等待此项。
- Root治理基线（并行工作树快照，不是本任务最终commit）：standard exit1共197项，其中Storage14项；topology exit0；scripts/tests为72通过/2失败，失败属于旧手册提取与“参考依据”标题断言。日志沿用/tmp/kokoro-storage-goal-baseline.rejrKJ/root-*；不修改其他任务负责的Root治理文件。

### ST-I1 依赖切分裁决（2026-09-08，优先于原卡原子框架+数据合并范围）

实现负责人提出核心卡同时迁移六表事务、十RPC/目录与Nest过宽。Root接受收窄：同一writer依次I1a（Prisma/apply/catalog）→I1b（claim/fingerprint/Upload）→I1c（Asset/Artifact/library）→I1d（Nest/feature入口）。当前授权先连续完成I1a/b/c，再交付一个无SQL双轨的可运行数据切片；I1d另续派。
I1a的候选schema只处于未提交的实施工作树，不作为第二份已交付canonical；I1c完成时删除旧SQL/schema/Row mapper、所有运行时数据查询用Prisma后再提交。每行为先RED/GREEN，不要求一次性写数千行；每阶段日志保留，不为提交颗粒度制造兼容层或双canonical。
当前唯一旧Node/Connect入口允许在数据切片继续运行，状态明确为“Prisma已切换，Nest待I1d”；本片不假装Nest完成。数据组件分属目标uploads/assets/artifacts，共享claim/fence在common/commands，PrismaService只管理连接与typed事务，不成为全能业务Repository。
曾因看到其他pnpm进程误判同仓writer冲突；Root以lsof确认PID67492/67733 cwd是kokoro-capability，与Storage无写入冲突，未中断他仓。Storage安装命令固定Homebrew Node24.20.0与已知corepack pnpm脚本，避免shell继承Node22造成误判。

### ST-I1b/c writer交接与选模调整

storage_data_review已交付部分RED/GREEN后停止写入，Root调用interrupt确认previous status=completed。已有修改保留不提交：Prisma候选/初步apply、PrismaService、fingerprint helper与CreateUpload回归；其他operations临时fingerprint尚不合约，旧SQL仍在，明确非可交付。
因本片涉及跨六表事务/并发与无FK保护重构，Root将唯一实现writer交接给原生storage_implementation（gpt-6-astra），不同时保留两个writer。原data reviewer回归只读角色，后续在稳定产物上审查。新writer沿本卡I1a/b/c的数据收敛范围，不顺带做Nest I1d；Root继续主控与独立验证。

### ST-V 生产依赖闭包预验证（Root隔离实验，未改Storage）

- 候选package/lock快照（lock SHA256 `018bef3b3834645b26815015d2af3579951a90864485933713f40444531c8779`）在 `/tmp/kokoro-storage-dependency-audit.yKoP9L`：`pnpm audit --json` 8项（1critical/3high/4moderate）。旧Vitest2.1.9/Vite是开发UI/API条件风险；Prisma7.10.0 CLI传递deepmerge-ts7.1.5/mysql2 3.15.3也被标入prod peer链，不宣称服务端已暴露。
- 实际 `pnpm install --prod --ignore-scripts --frozen-lockfile` 仍经@prisma/client可解析prisma CLI与TypeScript，原Docker“只有生产依赖即无CLI”假设不成立。首轮因漏复制workspace而触发Connect2.2.0 release-age gate；复制真实workspace后重跑通过，未修改全局policy。当前精确minimumReleaseAgeExclude仍需到ST-V按发布时间复审移除，不扩白名单。
- 精确peer override '-'实验未移除这两个optional peer；不推荐未经验证的override解法。
- 官方 `--prod --no-optional --ignore-scripts --frozen-lockfile` 在新目录 `/tmp/kokoro-storage-prod-minimal-probe.r6Er9d` 成功：断言CLI/TypeScript不可从client解析，Prisma runtime/adapter、S3 SDK、Nest core/Fastify、Connect plugin import全部通过；`pnpm audit --prod --no-optional --json`为138项依赖、0漏洞。仅证明该快照最小依赖闭包，不是最终镜像/编译后查询/S3实际功能通过。
- 后续Docker优先验证这一标准CLI选项而非自写pnpm hook/修改生成物；实际构建+PG/S3/ClamAV全链路须覆盖可选native包移除的功能影响。完整dev audit整改仍待Vitest/工具链升级与Prisma CLI传递依赖评估，不以prod结果掩盖dev高危。
- 2026-09-08 registry额外候选：Vitest5.0.0、Vite8.2.2、Prettier3.9.6、deepmerge-ts8.0.2、mysql2 3.24.4；仅版本元数据，未安装验收。官方依据： https://pnpm.io/cli/install 、 https://github.com/vitest-dev/vitest/security/advisories/GHSA-5xrq-8626-4rwp 。

ST-V闭包补充：同一prod/no-optional目录使用外部构建阶段Prisma7.10.0生成器与TS6.0.2编译器生成/编译ESM，运行阶段仅node加载dist（无tsx/CLI），在Root新建随机库真实create/count断言通过；日志generate.log、compile-node.log、apply-compiled.log、compiled-query.log。首次独立编译未显式lib而带入DOM造成URLPattern声明冲突；按后端规范显式lib ES2024后通过，未用skipLibCheck。两个实验数据库均由Root清理。该证据仍不是最终服务镜像或外部S3/ClamAV链路。

I1c必要生成接线授权：原scripts/normalize-generated.ts遍历整个src/generated，会在contract生成后修改Prisma官方生成物尾部。Root授权仅收窄遍历根至src/generated/proto并加owner隔离断言；不手改两类生成物。验收contract:check→prisma:generate→contract:check顺序无交叉漂移。此文件加入当前writer允许集。

### ST-I1a/b/c 主仓验证与复审修复卡（2026-09-08）

- 稳定83文件交付hash与主仓一致；Root在自身随机空库独立执行 prisma:validate、db:apply-schema、lint、typecheck、test、build、contract:check、prisma:generate与contract交叉生成隔离、编译后Prisma真实查询、diff --check，均通过；38文件147测试、0skip。日志 `/tmp/kokoro-storage-main-data-verify.WsAoQB`，任务DB已清理。format:check仍52历史文件失败，留ST-V，不称全门禁通过。
- 符合性审查 storage_contract_review 确认数据owner/唯一schema/七fingerprint/receipt/fence/事务/授权过滤；发现CreateUpload replay初读pending后异步签名与终态转换窗口。Root与审查员共同裁决：签名事务外执行，其后Prisma短事务按tenant/owner/upload/state=pending条件写作为发放线性化gate；受影响行0时不外发URL，返回FailedPrecondition。同一row写序排序terminal与发放，不引入网络I/O事务、签名租约或schema字段。
- “终态不再发PUT”指上述线性化点，不承诺数据库终态与网络bytes送达全局原子；此前已发出的有效URL不撤销。签后但从未外发的URL不构成发放。既有ETag/version固定扫描与promote保持不变。
- 修复卡ST-I1R：唯一writer storage_implementation（gpt-6-astra），基线72ab5dd+83文件交付hash；允许现有UploadsStore、Application/ports/test double、相应integration/unit测试与四份Storage设计状态文档。新增同职责普通测试文件允许；不改schema/Proto、他仓、Docker/CI。先RED/GREEN覆盖sign barrier两种终态/发放顺序、七operation固定摘要及逐字段变化，修正文档过期“待补”。完成后停止写入并更新交付清单/hash；Root复审→质量审查→重跑主仓验收→串行提交。
- apply取消疑点经固定Prisma7.10源码审查：db push采用CLI进程内WASM/JS executor，child close后释放lock有依据，非当前阻断；SIGTERM/partial DB负例记录为后续补充。DatabaseModule尚未消费、DI需I1d通过；不称Nest已验收。

### ST-I1d 后继卡（待数据切片验收提交后派发）

| 项 | 边界与完成条件 |
|---|---|
| Owner | kokoro-storage；沿用storage_implementation单一writer，Root集成/提交；数据片验收SHA为起点 |
| 目标 | Nest真实拥有feature provider/配置/生命周期，FastifyAdapter与Connect plugin单listener；删除旧全局application/domain/infrastructure/interfaces/bootstrap，不用转发外壳 |
| 放置依据 | TECHNICAL_DESIGN §2目标目录与§3、6；uploads负责上传三命令与status，assets负责可见性/scan/引用，artifacts负责发布/library；复杂事务保留各feature内具名store，不创BaseRepository/每表Module |
| 允许 | 原I1卡src与test、package/lock/workspace、tsconfig、受影响scripts（reconcile/import）和Storage文档；新普通文件须有单一变化原因。共享Proto/provenance固定不变；Docker/CI由后续ST-V单独切片 |
| 类型/依赖 | typed业务错误替代message.includes分类；生成Proto只在transport/client边界；生成Prisma限制数据组件。HTTP/Connect共用身份验证，不假设插件走Nest Guard。官方ConfigModule与显式typed config注入；Prisma连接由factory/provider消费配置，解决原始URL参数DI |
| 行为 | 10RPC与library路径不变；同一listener auth/error/detail/request-id、一致busy CONFLICT+Aborted+retryable，取消/DeadlineExceeded保持协议code；七命令fingerprint/receipt/CAS已验收行为不回退 |
| I/O | facade CallOptions、Connect HandlerContext.signal贯穿S3/scanner、限时/取消；query10/30秒、普通command30/60秒、Complete300秒、lease600秒；1MiB RPC与8KiB HTTP URL，provider调用不进入Prisma事务 |
| 生命周期 | Nest init/start失败清理、ready四依赖、draining拒新请求、唯一signal owner、30秒有界drain和幂等close；禁止bootstrap自动apply；不重复启动共享PG/Redis |
| 验证 | 原行为全回归+Nest TestingModule/真实Fastify listener+编译后plain Node DI/配置/启动失败/单listener/关闭；错误detail与metadata/unauthorized/cancel/deadline/oversize回归；Prisma真实PG保持147+新增且0skip。外部S3/ClamAV暂缺则明确测试double范围，不冒称真实集成 |
| 交付 | 先RED后GREEN，每个职责迁移同时清除旧import路径；稳定manifest/hash后停写，符合性→质量→Root主仓验证→scoped commit。不得一口气扩I2或ST-V，遇无法保持运行的小切片向Root裁决 |

2026-09-08 Root重新核验框架官方API：Nest FastifyAdapter示例、Lifecycle hooks与Connect官方fastify插件；已安装@connectrpc/connect-fastify2.2.0类型确有routes/contextValues/shutdownTimeoutMs，继承ConnectRouterOptions。来源 https://docs.nestjs.com/techniques/performance 、 https://docs.nestjs.com/fundamentals/lifecycle-events 、 https://connectrpc.com/docs/node/server-plugins/ 。核验是API语义与本地类型证据，不替代后续实际Nest集成测试；没有采用文档中的性能宣传作为本仓实测。

### ST-I1R 复验与ST-I1Q质量修复（2026-09-08）

- 上传发放gate补修交付85文件，原83项74不变、9授权变更、2新增测试；符合性复审storage_contract_review通过。Root随机空库重跑prisma validate/apply、lint/typecheck/test/build/contract，全通过：40文件189测试0skip，日志 `/tmp/kokoro-storage-main-i1r.c3be9M`，自建库已删除。尚未提交数据片。
- 质量审查storage_data_review发现2P1：Artifact不同command竞争同复合主键时P2002未按已定replay/conflict恢复；claimed receipt损坏state/response或非正fence未在持久化读回检查。另ADR当前数据状态过期P2。Root代码核实后要求修复，不以189绿测试代替缺失并发/损坏负例。
- ST-I1Q修复卡：沿用storage_implementation(gpt-6-astra)唯一writer，基线72ab5dd+85hash；允许common/commands、database/transaction-errors、artifacts.store及相应tests、四Storage设计文档和ADR/0001的当前证据修正。优先保持checked关系create，在真实双client RED确认实际P2002 target后仅对artifact复合identity增加有限整事务重试并重读同值/异值；不采用全P2002重试，不以catch后继续已abort事务，非必要不换unchecked createMany。
- receipt在使用已存行前验证state/response/fence不变量；同时审查assert/complete/release的CAS，防止活跃claim行被破坏后被静默覆盖。JSONB SQL NULL与JSON null边界须由实际Prisma/PG行为证明，不写类型断言掩盖；无schema/custom CHECK扩展。
- 验证：两个client确定性同Artifact identity竞争、同值仅一次insert/另一次replay且两receipt闭环，异值稳定conflict无孤儿receipt完成；claimed+response与fence<=0损坏活跃/过期行fail-closed且无覆盖，正常claim/release/replay不回退。RED/GREEN、全套与lint/typecheck/build、独立复审后Root再跑主仓。Nest/I2/STV仍排除。文档ADR更新当前数据工作树证据而非自称已验收commit。

ST-I1d并行只读准备：storage_contract_review(gpt-5.6-sol)绑定72ab5dd+当前旧transport/config未变路径，预审Nest单listener的auth/error/detail/取消/退出接线与测试迁移风险，产出最多5条具体约束供后继writer；不修改当前数据切片、不跑共享服务、不创建第二writer。Root继续数据审查关键路径。

ST-I1d生命周期预审裁决：本地Nest12真实close顺序为OnModuleDestroy→BeforeApplicationShutdown→Fastify close/dispose→OnApplicationShutdown，Prisma/Redis不可在OnModuleDestroy断连抢在drain前。资源释放使用OnApplicationShutdown；BeforeApplicationShutdown标记draining并启动唯一可清理timer；Connect使用官方shutdownSignal而非插件shutdownTimeoutMs，enableShutdownHooks作为唯一signal owner。Root无listener/无外部依赖的真实Nest/Fastify小探针确认事件顺序；插件shutdownTimeoutMs=30000在app.close已resolve后仍留timer导致子进程4秒未退出（Root仅杀自己探针）；换shutdownSignal后子进程0.264秒正常exit0。该证据只证明框架hook/timer语义，不是Storage运行时验收。30秒drain依赖全链路协作取消，不承诺忽略AbortSignal的任意代码也有应用内绝对硬退出；最后硬上限由编排器保障。

ST-I1Q证据纠偏：完整ArtifactsStore双PrismaService/同identity predicate-read barrier在PostgreSQL18.4实际竞争产生P2034，已有有限事务重试正确实现同值replay/异值conflict；没有本路径P2002可重复反例。Root与质量审查员共同把原Artifact P1降为P2测试缺口，并保留两条真实并发回归，不增加生产重试分类。无prior read的单独checked create确可产生P2002但不是该用例路径，只保留观察日志，不冒称复现漏洞。确认P1只剩receipt损坏读取/接管/执行/完成/释放边界，现writer报告修复后216测试，待稳定复审。

ST-I1Q主仓最终验证未放行：89文件hash/精确dirty路径集合全部匹配，质量复审通过后，Root在独立空库默认并行全suite得到216pass/2fail（artifact两例事务attempts期望>=2实际1）；日志 `/tmp/kokoro-storage-main-i1q.VFvarG`。prisma validate/apply、lint/typecheck通过，test失败后build/contract/compiled/format因set-e未执行；自建库已drop，没有提交。次数断言先于业务error输出，现不能判定P2002/其他适配器错误；Root重新授权原writer只在实际完整路径加诊断并复现，不删断言凑绿，按真实error形态裁决。先前单跑P2034结论不覆盖该全并行失败。

ST-I1d启动补充：配置/DI factory只构造typed配置与lazy资源，不在NestFactory.create阶段并发建立外部连接（该阶段失败可能拿不到app供close）；外部就绪操作在生命周期hook，bootstrap拿到app后对init/listen失败执行同一关闭路径。每个资源provider必须处理自身部分初始化失败，测试覆盖连接中失败/成功资源随后释放；不默认Nest会回滚任意异步factory的副作用。保持官方Module/Provider生命周期，不引入自制DI/第二runtime。

### ST-I1a/b/c 已接收：33093fed09d28e9fc2de9292d47e7ec2cbb30e26

- Root默认并行全suite复跑两个独立随机空库，**每轮42文件220测试通过、0skip**；prisma validate/apply、lint/typecheck/build/contract、编译后plain Node ESM真实PG claim/receipt/replay通过。日志 `/tmp/kokoro-storage-main-data-final.UPcBUU`；两库均已drop。格式仍51历史文件失败，不称全门禁或生产完成。
- 主仓并行失败最终在完整ArtifactsStore路径复现P2002，质量复审根据新证据恢复并关闭P1：只匹配实际PrismaKnown P2002、StorageArtifact/table/index/23505/adapter形态走原有5次/10秒整事务重试。实现方另3轮独立空库默认并行220/220，Root2轮独立通过；未移除并发结果/attempt/receipt断言。
- 符合性storage_contract_review、质量storage_data_review最终均无本数据片剩余P0/P1；上传发放gate、损坏receipt读取/CAS、Artifact实际并发恢复完成。Nest/I2/STV仍未交付。
- Git按manifest显式路径暂存并提交；89物理路径被Git识别为88条变更（pg测试fixture rename）。暂存后集合检查未关闭rename检测造成断言失败，外层命令未及时停止而继续提交；Root立即以--no-renames独立复核commit精确89路径、所有commit blob hash与已验证交付一致、工作树clean，确认没有漏项/越界项。后续提交脚本统一set-e且使用--no-renames，避免此类检查误报被继续执行。
- 后置完整commit diff --check发现Prisma官方只读生成物的尾随空格/EOF空行；先前unstaged diff未覆盖新生成文件，不能声称全commit whitespace通过。排除官方Prisma生成目录后的手写diff check通过；原始失败日志commit-diff-check.log保留。不手改生成物或放宽手写源码门禁，ST-V按生成artifact独立治理。
- 当前代码commit：`33093fed09d28e9fc2de9292d47e7ec2cbb30e26`，标题refactor(storage): move metadata lifecycle to Prisma。数据当前唯一canonical/Client已切换，旧SQL CRUD/Row mapper退出生产；原Node入口明确等候I1d。

### ST-I1d 正式派发

沿上方后继卡现在放行：storage_implementation（gpt-6-astra）唯一Storage writer，起点33093fed与clean工作树；Root仍唯一Git index/commit负责人。行为基线更新为220测试，主仓数据证据与两轮复审已完成。先同步Storage CURRENT/设计状态引用该接收SHA，再按feature/transport有序切換真实Nest单listener与生命周期，保持数据已验收行为。准备只读预审与Roothook/timer实测约束一并作为本卡依据；不进入I2/CI/Docker供应链扩展。

### ST-I2 准备（并行只读，不授权业务修改）

storage_data_review（gpt-5.6-sol）绑定Storage commit33093fed，仅使用git show读取完整固定代码与设计，评估canonical健康复用/仅missing-mismatch repair CAS的最小API/事务和可靠性测试切片。不得读取活动Nest重构当固定证据、不写文件、不运行/清理服务DB、不操作Git index。输出owner不变的最小能力边界、明确failure分类/旧identityCAS/丢失竞争者候选恢复、最多8项可执行验收条件，供Root裁决后续I2卡。Root同时准备ST-V工具链/部署，不与当前Nest writer并写。

2026-09-08数据接收后Docker只读探测：既有socket /_ping再次3秒超时。此前重启授权问题仍未收到回复，继续保持Docker与容器原状态；不影响Nest源码实施，真实MinIO/ClamAV与镜像尚无验收证据。

ST-V/依赖例外再验证：Root从33093fed复制package/lock/workspace到 `/tmp/kokoro-storage-release-age.h7vYVA`，仅在隔离副本移除Connect精确minimumReleaseAgeExclude。全新 `pnpm install --prod --no-optional --ignore-scripts --frozen-lockfile` 12.2秒通过，470 lock entries通过供应链策略，生产Nest/Prisma/Connect imports通过，prod/no-optional audit 0漏洞。未改Storage；通知I1d writer在授权workspace范围删除已无必要例外并真实验证。registry少量ECONNRESET由pnpm有限重试后成功，无policy降级。另33093fed实际connect/connect-node为2.1.2、fastify plugin2.2.0；I1d必须区分实际/目标，不冒称全2.2，按ADR统一时需精确pin与peer/完整回归。

### ST-I2 Root设计裁决草案（等I1d接收后先收敛三文档门，不是当前writer授权）

- Owner不变：Storage assets/blob生命周期；普通feature provider+Prisma事务，不新增服务、Scheduler/outbox或通用Repository。选择healthy复用、只有确定missing/mismatch才repair；timeout/auth/403/429/5xx/DNS/cancel都是availability，不能用catch-all转missing。检查在事务外，完整旧key/version/etag/blob/digest/size/tenant/owner snapshot CAS在事务内；CAS败者必须重新读取并实际检查赢家，不能直接信任；重试有有限次数和总请求预算。
- canonical Content-Type固定application/octet-stream，Asset MIME仅用于响应Content-Type。对provider实际返回的version严格核对，删除缺VersionId时用请求version回填的假确认；key/etag/size与可用sha一并核对。AWS官方HEAD可能只给通用HTTP错误，403也可能来自不可见的不存在对象，不能猜missing；typed adapter分类须保持这种不确定性。来源 https://docs.aws.amazon.com/AmazonS3/latest/API/API_HeadObject.html （2026-09-08核验）。
- candidate private key增加claimId（UUID）确保不同command相同fence也不会共用key；此前uploadId+fence不足以证明execution独占。败选/未知提交candidate不即时delete，以免DB查询到未引用后另一个在途提交引用而误删；无法证明退役年龄的final orphan只报告，不伪称已完成自动GC。
- 只读评审最初建议“无schema+lastModified>=1h即可回收旧canonical”被Root否决：LastModified是creation age，不是retirement age，一个月前对象刚repair后即可被旧CLI立刻删。删除前重查引用不能补退休时间。对于已知retired canonical，Root选择新增Storage-owned Prisma退役记录（A）；相较完全不增schema并永久保留全部final orphan（B），A多一表但能证明退休grace与崩溃重试，属于现owner对象生命周期元数据而非新业务模块。
- 后续正式设计应使repair CAS同事务写入旧对象key/version/etag/tenant/owner与retiredAt；CLI仅对retiredAt已过>=1h、再次确认未引用的确切identity执行删除，成功/确定已不存在才移除退役记录，权限/超时/未知结果保留。S3有VersionId时删该版本，不能只传Key造成delete marker却未回收版本；新表/索引/native数据/空库catalog门会从6表相应更新，不假装无schema变更。未知final orphan（包括未持久化退役证据的crash candidate）仍仅报告；不为自动扫净一切而推断ownership或creation age=retirement age。
- 不增加历史migration或碰现有用户数据库；canonical schema/TECHNICAL_DESIGN/API_CONTRACT/DATA_MODEL/新ADR必须在I2代码写入前同步并通过文档门。Proto不需要变化；consumer不接触retirement事实。
- 验收保留8组：healthy不promote且同digest不同MIME各Asset正确；跨tenant/owner隔离；missing/mismatch完整CAS；不确定provider错误零promote/零业务完成（允许claim创建/释放，不能误要求receipt绝对零变化）；两个repair竞争只一胜且败者重新检查赢家；absent竞争同理；stale fence/DB回滚不改变canonical或完成receipt；GET只对healthy签URL，刚退休老对象即使LastModified很旧也不得立即删，过retirement grace才按确切版本删除且失败重试。具体可执行测试分组由I2卡在Nest新目录上细化。

### I1d必要打包接线范围调整（优先于原Dockerfile排除项，仅此文件）

writer发现deployment architecture把旧Docker CMD与package入口相互验证。Root不采用删除/放宽这一有效一致性断言来让源码绿：将 **Dockerfile** 的最低必要运行接线加入当前唯一writer范围（必要时仅对应.dockerignore构建上下文），仍不改CI/compose/docker-smoke运行脚本或启动Docker服务。同步Node24基础镜像、Prisma canonical/generate构建输入、dist/main.js入口，以及已由隔离实验验证的prod --no-optional依赖闭包；保留非root、HEALTHCHECK、external infra、无CLI/dev源码运行时安全断言。旧Node bootstrap的文本断言改为新Nest实际等价行为，但image/package入口一致性继续检查。

Root从Docker Hub官方registry获取node:24.20.0-bookworm-slim OCI index：sha256:ba849c60be29959425b8734d57b8b4b7d56f98edd9504c9af091d5281095a71e，含linux/amd64与arm64；记录 `/tmp/kokoro-storage-node24-index.json`。docker manifest --verbose最初CDN config读取EOF，随后直接官方auth/registry只读index成功；这只是tag/digest/平台证据，不是镜像build/运行通过。Docker daemon仍无响应，完整image/外部依赖验收仍ST-V明确待验。

### ST-I1d 稳定交付与审查卡（2026-09-08）

- writer于08:53 UTC停止写入，基线33093fed，交付188物理路径（M71/A93/D24）。Root独立核验164文件SHA256、24删除、完整dirty集合和空index一致；manifest `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-storage/.tmp/st-i1d-logs/handoff-manifest.json`，SHA256 `715e5034d256afa3f50d23d6c5a1c55aa650a3a2701480b67d581124d9765909`。尚未验收或提交。
- writer报告真实随机PG默认并行50文件242测试、编译后NestFactory2测试通过；源码/真实PG与Redis、HTTP/TCP对象及scanner doubles明确区分。主仓仍需独立重跑。根HTTP parser与Connect JSON parser实际启动冲突已保留RED/GREEN；readiness响应预算与实际后台工作drain分离，取消不提前释放资源。
- ST-I1d-S（P1符合性）：storage_contract_review(gpt-5.6-sol)只读上述固定manifest，按I1d卡/三文档/手册核对Nest真实owner、十RPC/HTTP契约与错误/取消/生命周期、旧路径删除与授权范围。允许读代码与日志、不写文件、不启动服务或数据库、不操作Git；输出具体文件行号/P级/证据/待验项。Root主控集成提交。
- ST-I1d-Q（P1质量）：符合性通过后续派storage_data_review(gpt-5.6-sol)，同一固定manifest，聚焦竞态、资源清理、失败恢复、tenant/fence/事务已验收行为与测试真实性。相同只读限制，独立审查不是复述writer结论。
- Root并行工作面：固定manifest范围审计、独立随机空库apply与全套/compiled/schema/contract/frozen验证；仅清理自身数据库与临时产物。已知13个未改文件format失败、完整dev工具链audit和真实S3/ClamAV/image/CI留ST-V，不混充本片全门禁成功。发现本片阻断问题只续派原writer明确文件范围，更新manifest后复审。

### ST-I1d-R 符合性补修卡

- Root在 `/tmp/kokoro-storage-main-nest-verify.7pwGV5` 独立随机空库复跑frozen/apply/prisma validate/lint/typecheck/default-parallel test/build/compiled/contract→generate→contract通过：50文件242测试、compiled2测试；13历史format失败。数据库已drop，复跑后188 manifest全hash不变，schema/contract/generated与基线一致。仍未放行，因为审查发现有效缺口。
- 符合性审查绑定715e5034：P1旧docker-smoke仍检查已删除dist/bootstrap/main.js；P1缺失/空白caller request-id时hook新UUID与RPC空metadata/detail不一致；P2contract README旧facade路径。Root额外确认library controller也生成第二UUID，导致日志与HTTP header/meta不同，归入同一correlation修复。
- 唯一writer仍storage_implementation(gpt-6-astra)，基线33093fed+188稳定manifest，Root仅Git负责人。允许修改configure-transport、storage-rpc.service、LibraryController以及同transport职责的普通correlation context文件，必要http-context接线；相关unit/contract/真实listener/compiled/architecture tests；API_CONTRACT/CURRENT/ACCEPTANCE所需证据。特批scripts/docker-smoke.sh仅修编译入口literal及contract/README.md仅修真实facade链接，不改Proto/provenance/generated/Schema；不执行仍有共享清理风险的docker-smoke，不扩大到ST-V。
- 行为：每个请求仅有一份transport correlation，响应header/RPCmetadata/ErrorDetail/HTTPmeta/结构化日志一致；caller原header缺失/空白仍按原认证契约拒绝，禁止把生成ID回填身份凭证来绕过校验。优先测试缺失/空白两条真实listener RED与现有有效ID保留；复用官方Connect contextValues与Fastify请求上下文，不新造第二身份系统。
- 先RED/GREEN修两P1及P2，再真实PG全套、compiled、lint/typecheck/build/contract与精确新增manifest。停写→原符合性审查员复审→质量审查→Root重新独立验证后提交。本片以外的固定容器名/无条件rm、完整工具链/外部依赖继续待ST-V。

### ST-I1d-Q 最小HTTP边界补修

- I1d-R稳定manifest变为192物理路径，SHA256 `ef609c0ca24528c984f2b7321c3e37980783ce8e28ad4f21544cdde15ebea1c9`，Root核验原188仅14授权文件变化，符合性复审已放行。Root `/tmp/kokoro-storage-main-nest-final.q5PFKB` 新随机空库248测试+compiled2测试、lint/typecheck/build/validate/apply/contract/frozen通过，隔离最终prod/no-optional安装audit138依赖0漏洞、无CLI/TS/tsx/Vitest和编译入口import/真实Prisma查询通过；库已drop，manifest复验不变；format仍13失败。
- 质量审查storage_data_review发现P1：library非GET的畸形JSON在Nest parser先返回默认400，绕过API已定405/Allow/envelope；现compiled测试400断言是缺口不是契约授权。P2：结构化日志将全部4xx记success。Root接受两项并维持未放行。
- 唯一writer storage_implementation(gpt-6-astra)，固定192manifest为起点；只允许configure-transport/LibraryController/必要同transport职责普通HTTP方法门、相关真实listener/compiled/日志测试和API/CURRENT证据。将精确library路由非GET在body parsing前返回同correlation的405+Allow:GET+Storage envelope，不关闭Nest根JSON parser、不改变RPC parser子scope、不放宽认证、不建自制路由器。测试含畸形body、正常body/query与其他路由不受影响，原真正根parser生效断言须保留。4xx及5xx日志明确failure，至少401/405覆盖。
- 先RED/GREEN后完整真实新空库/compiled/lint/typecheck/build/contract；固定manifest停写→原质量审查员复审（涉及contract变化再由符合性复核）→Root重跑并提交。禁止扩大I2/STV或运行docker-smoke；Root仍Git负责人。

### ST-I1d 已接收：2b5107517a680adc41ef5eb6faae6d20898aed3c

- 最终193物理路径manifest `9d130435347d6853cba588377df606c81771f469dc19f19393a774635258660d`，相对192仅7授权文件；独立质量与增量符合性均放行。Root `/tmp/kokoro-storage-main-nest-accepted.QbdvoI` 再建随机空库，frozen/validate/apply/lint/typecheck/build/contract通过，默认并行52文件256测试、实际编译后NestFactory2测试通过，无skip。数据库已drop。
- Root以set-e与--no-renames执行精确暂存、193路径/逐blob hash/空index基线审核、cached diff check再提交；commit后再次核验193路径和全部已提交blob等于验收manifest，工作树clean。Git显示191条变更是两个rename折叠，不是缺文件。完整commit diff --check通过。
- Prisma数据与Nest feature/runtime已正式切换，旧Node入口与全局五目录退出。当前代码SHA为2b510751，标题refactor(storage): run owner features on NestJS。之前两轮Root旁证和prod闭包验证见上文；不冒称真实S3/ClamAV/image已验收。
- 尚未闭环：I2 canonical健康复用/repair/退役安全；ST-V 13历史format、完整dev依赖审计/工具链、隔离部署脚本/CI与真实provider/image/SLO。目标继续active。

### ST-I2-D 设计与Schema准备卡（不授权业务重写）

| 项 | 边界 |
|---|---|
| 任务 | P1，对象健康复用、确定repair与有证据的退役回收，先通过三文档/Schema门 |
| Owner/执行 | Storage assets/blob生命周期；storage_implementation(gpt-6-astra)唯一writer，Root架构/提交，原审查员只读 |
| 基线 | /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-storage；codex/production-closure-docs；2b5107517a680adc41ef5eb6faae6d20898aed3c，clean |
| 设计依据 | 本计划ST-I2 Root设计裁决草案与本轮公开放置表；Root TS/SQL手册及Storage三设计文档。选择既有assets业务owner、integrations只封装provider；不增一级模块/服务 |
| 允许文件 | TECHNICAL_DESIGN/API_CONTRACT/DATA_MODEL/CURRENT/ACCEPTANCE、必要INDEX/ADR README、一个新ADR解释canonical复用/退役方案；prisma/schema.prisma、官方generated/prisma；apply-schema与schema-bootstrap/catalog/architecture的最低必要7表接线。普通其他文件需求先报告，不扩写 |
| 排除 | 业务Service/store/SDK/CLI回收行为重写（门通过后另卡）；Proto/provenance/generated proto；其他仓/Root；CI/Docker/compose/共享服务 |
| Schema | 六表→新增一个已知canonical退休metadata表（不建通用job/outbox/多态垃圾桶）；明确tenant/owner/blob逻辑归属、旧key/version/etag、UTC retiredAt、唯一身份和按退休时间+稳定cursor的有界查询索引，无FK。API仍十RPC不变。不能靠object LastModified充退休时间；只定义本owner真实用例所需字段/索引 |
| 事务/失败 | healthy原canonical复用；确定missing/mismatch才完整snapshot CAS，旧identity退役记录同事务写入。provider不确定错误失败不改业务完成事实；CAS败者重读并实际检查赢家；candidate key加claimId保证执行独占；删除精确版本，失败保留记录；未知final orphan只report，不立即删除 |
| 文档门 | 三文档明确当前2b510751/目标I2、状态机/事务/无FK完整性/retention/查询/API错误与幂等；新ADR比较退役表A与全部未知对象永久保留B并记录Root选择A；不把Schema准备称业务已完成 |
| 验证 | 先验证6→7表catalog门能捕捉差异，再官方prisma validate/generate、独立随机空库apply+catalog无FK+drift、现有256与compiled2/contract/build。只调整准确表清单，不改为宽泛>=6；不手写DDL/历史migration/重置共享库 |
| 交付 | 先给精确模型/索引与三文档一致性结论；完成授权Schema准备后稳定manifest/hash并停写，Root审查/主仓验证/小切片提交。业务I2实施需随后明确放行，不自行越过此门 |

I2验收须额外明确：回收查询有界分页，retirement grace最少1h；只有当前canonical明确退出才可写已知retirement；退役key不会被后续repair重新采用，防止“查询未引用→另一个在途提交引用”的删除竞态。删除条件版本与provider实际返回值一致，不给缺VersionId回填请求值；无版本对象保持执行唯一key且按明确identity删除。不通过更改现有user数据库或部署服务验证候选Schema。

ST-I2-D设计摘要已由Root核对：retirement UUID身份、tenant/owner/blob、旧key/version/etag、retiredAt；逻辑(tenantId,blobId)关系、unique(tenantId,objectKey)、稳定(retiredAt,retirementId)分页及关系索引，未来事务显式验证owner。唯一约束仅防队列内重复退休，不能重置retiredAt；出队后仍由永不重用key协议保证安全。候选分页默认100/max1000、单轮10000有界。Root发现旧uploadId是upload:sha256共71字符，直接在现最大约483字符finalKey再追加claim UUID可能超过varchar512；要求候选key去掉冗余uploadId/fence段，保留tenant/ownerDigest/claimId/sha且证明长度，claim/fence仍由DB guard承担，不靠扩text掩盖。

ST-I2-D必要文档同步扩围：允许README.md、docs/SCHEMA_BOOTSTRAP.md、docs/SCHEMA_OWNER_INVENTORY.md仅更新六→七精确表清单、已接收Nest SHA与本片Schema-only说明，不修改运行步骤/CLI或提前声称healthy/repair/GC完成。writer已报告六表schema对新名单RED、加表后旧apply六表catalog再次RED，再改精确七表集合；实际交付与Root验证仍待完成。

ST-I2-D稳定审查卡：基线2b510751+25物理路径manifest `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-storage/.tmp/st-i2-d-logs/handoff-manifest.json`，SHA256 `a532ab2c6ae3b31048b38bf18a01defa34a229d3a2ff1173b6b38085567c6845`；Root核验25hash/dirty集合一致，writer已停写。storage_data_review(gpt-5.6-sol)只读Schema/索引/无FK完整性/未来CAS+retirement事务与删除安全，storage_contract_review(gpt-5.6-sol)只读三文档/新ADR的current-target/API/错误/幂等/退役宽限一致性，允许并行；两者不运行测试或共享服务、不写文件/Git。Root保留主树真实随机库schema/catalog/drift/全套与compiled验证，唯一提交owner。writer报告257+compiled2、七表零FK通过仅为旁证；generated官方空白与13历史format如实待ST-V，不手改生成物。后继业务卡必须等本门真正放行。

### ST-I2-D 已接收：347e6dd55afbedc207d3f46f8f44c5d9384ac2f4

- 数据设计与契约设计两名只读审查员均放行，无阻断模型/索引未决；Root `/tmp/kokoro-storage-main-i2-design.jCYebZ` 在新随机空库执行validate/apply精确七表七enum/0FK/drift、lint/typecheck/build/contract→generate→contract通过；默认并行52文件257测试、compiled2测试、编译新delegate真实count=0通过。自建库已drop，业务writer确未启动。
- Root重新核验25hash/dirty与官方再生成一致，按25路径显式暂存、手写cached diff check、全部staged blob hash后提交；commit后逐路径/逐blob验证相符、工作树clean。提交347e6dd5为feat(storage): define canonical object retirement metadata。
- raw staged diff check exit2，41处全部为官方generated/prisma空白；日志staged-raw-diff-check.log，手写排除生成物的diff通过。13历史format仍失败。不手改生成物、不把失败隐藏为完整格式通过。
- 三文档门对应Storage绝对路径已在交付/本轮用户报告列出，技术/API/数据当前方案一致，正式放行以下业务卡；Schema准备本身不证明healthy复用或回收安全已实现。

### ST-I2-B 业务实现卡

| 项 | 边界与验收 |
|---|---|
| 任务/优先级 | P1：完成canonical健康复用/有限repair CAS/已知退休安全回收，删除旧无条件轮换与LastModified删除 |
| Owner/基线 | Storage assets/blob；storage_implementation(gpt-6-astra)唯一writer，Root审查/提交；/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-storage，codex/production-closure-docs，347e6dd55afbedc207d3f46f8f44c5d9384ac2f4 clean |
| 放置 | assets拥有canonical判定与retirement用例/store；uploads保留CompleteUpload编排与一个完整事务边界，必要数据helper只在数据组件协作。integrations/object-store仅provider协议/typed failure；CLI只编排现有owner能力，不创造第二套业务或SQL层 |
| 允许 | src/assets、src/uploads相应Service/store/types/module与必要同职责普通文件；integrations/object-store的typed接口/AWS/local/失败分类；scripts/reconcile-objects.ts及相应CLI用例、相关unit/integration/contract/architecture/smoke fixture/tests；Storage设计/CURRENT/ACCEPTANCE/README/INDEX/RUNBOOK/ADR当前证据。CLI若需官方Nest application context只能限定已有owner、不得启动HTTP listener或无关scanner依赖 |
| 排除 | Prisma canonical新字段或新表（非必要不再改schema/generated）；Proto/provenance/generated proto；框架/工具链依赖升级、CI/Docker/compose、Root/其他owner；共享基础设施启停和既有数据清理 |
| 对象协议 | 原扫描固定source etag/version/hash/size/cancel保障保留；healthy同owner/digest canonical只复用不promote，Asset MIME独立；确定missing/mismatch才有限repair；缺实际VersionId等不确定结果是availability，绝不请求值回填或catch-all missing；GET只检查不repair |
| 原子性 | 完整旧snapshot含nullversion CAS，影响行1，同Prisma事务写retirement+Upload/Asset/Scan/receipt，任何失败全回滚；复用/首次创建也验证tenant/owner/expected snapshot。CAS/absent竞争败者重新读取且实际检查赢家，最多3轮受Complete300秒预算；数据库网络/未知提交不盲目重试 |
| 重试细节 | 若真实首次Blob竞争出现P2002，先双client完整路径RED确认实际Prisma错误shape，只对明确canonical identity冲突做外层重新观察，不全P2002重试、不在已abort事务中继续；已有claim/fence、数据10秒有限重试保持 |
| 回收 | 只持久化已退出canonical的完整旧identity，不upsert/update刷新retiredAt，拒绝owner/blob/snapshot不一致、空version/etag、新旧key相等。claimId key428字符且执行唯一、永不重新使用。已知退休按固定cutoff/grace>=1h、100/1000/10000二键分页，删除前重查完整scope/current引用，确切version/identity删除成功或确定不存在才删记录；失败与unknown保留。未知final/crash/loser candidate只报告，不即时删，不留旧LastModified apply旁路 |
| 验证 | 8组既定验收：healthy+不同MIME共Blob；owner隔离；missing/mismatch CAS；不确定provider零promote/零业务完成；双repair/absent竞态检查赢家；stale fence/rollback无污染；GET仅healthy签URL；retiredAt非creation age、确切version回收失败恢复/引用保护/未知report-only。加key最长/claim唯一与有界分页。真实PG只自建随机库；provider doubles明确标注，真实S3/ClamAV另ST-V |
| 交付 | 按职责TDD，小步收敛，不在中间提交unsafe旧CLI仍可删除新退休对象的半片；必要拆片先向Root裁决。lint/typecheck/full257基线+新增/build/compiled/schema/contract、scope/hash后停写，符合性→质量→Root真实验证再提交；所有Git仍Root负责 |

### ST-V Root只读快照预检（绑定2b510751，非活动I2源码）

- 将完整已接收commit归档至 `/tmp/kokoro-storage-typed-lint-probe.nj8QcB`，只在临时副本增加type-aware ESLint候选配置，复用已安装依赖，不修改Storage源码/config。广泛recommendedTypeChecked preset得到40文件158诊断，其中125是require-await（多为async测试double），另有unsafe assignment/return/call/member、enum比较、unbound method等。此数量是该候选配置的诊断，不等于158个行为漏洞；ST-V须保留手册明确的unsafe/floating/misused门禁，不通过放宽它们清零。
- pnpm exec在临时目录输出了自动frozen安装检查（Already up to date）前缀，首次JSON解析因此失败；保留原始输出并从实际ESLint JSON提取 `typed-lint-clean.json`。后续探针直接用Node执行已安装CLI，避免wrapper副作用；未安装新依赖版本或改业务文件。
- 同一快照用当前TS5.9工具加 `--skipLibCheck false` exit2：Connect2.2声明缺全局HeadersInit、Vite5/rollup exactOptionalPropertyTypes与Worker环境类型冲突。日志typecheck-full-libs.log。该额外实验不是现有typecheck失败；Node24 types/新测试工具链/官方类型兼容要在ST-V实测，不手改node_modules或生成物来遮盖。Root TS手册要求typed lint与Node major对齐，不把未批准的额外flag冒充既有强制门禁。

### ST-V 独立工具链候选实测（2026-09-08，尚未应用 Storage）

- Root 将已提交347e6dd完整归档到 `/tmp/kokoro-storage-toolchain-candidate.G3G8WB`，独立安装依赖，不使用活动I2工作树或共享node_modules；registry证据在 `/tmp/kokoro-storage-toolchain-metadata.F3dZiu`。本节是后继选型输入，不代表活动源码的门禁已修复。
- 兼容候选：TypeScript6.0.3、@types/node24.13.3、typescript-eslint8.69.0、Vitest5.0.0（Vite8.2.2）、Prettier3.9.6；Nest12/Prisma7.10/Connect2.2保持。TS7超出eslint当前peer <6.1，Prisma latest为8.0 RC不取；eslint8.70及mysql2 3.24.4在核验时未满足24h发布冷却。启用minimumReleaseAgeStrict且无exclude；初次pnpm add自动写入临时豁免已回退、恢复基线lock后重新解析，不把豁免带入方案。
- TS6首次build实际RED TS5011；给build配置显式rootDir=src后保持dist/main.js输出且GREEN。直接依赖@smithy/node-http-handler4.12.0安装时提示内存泄漏弃用，候选更新已过冷却的4.12.1。
- 初始完整审计3条：Prisma CLI传递deepmerge-ts7.1.5递归图栈耗尽，以及mysql2 3.15.3认证降级/解压DoS。仅临时候选添加精确parent scoped overrides：`@prisma/config@7.10.0>deepmerge-ts:8.0.2`、`prisma@7.10.0>mysql2:3.24.3`。最终完整audit 0；不可盲目复制到正式仓，须ST-V ADR记录deepmerge8的Map合并等breaking行为、本项目普通配置对象覆盖证据与Prisma正式修复后删除override的退出路径。
- 精确候选frozen/validate/generate/typecheck/build/lint/contract通过；新自建空PG精确七表/七enum/零FK与drift通过，52文件257测试、实际编译后NestFactory2测试通过。隔离prod/no-optional安装audit0，编译入口import、retirement delegate真实查询count0及CLI/TS/tsx/Vitest不可解析通过；自建数据库已drop。证据为候选目录scoped-*.log和scoped-override-audit.json，仍非真实S3/ClamAV或镜像验收。
- 额外全声明实验：当前候选加入官方ES2024,DOM,DOM.Iterable并skipLibCheck=false后，只剩测试ZIP函数过宽Uint8Array<ArrayBufferLike>返回类型。该临时函数本来分配普通ArrayBuffer，精确标注Uint8Array<ArrayBuffer>后完整声明typecheck与lint通过（无cast、无node_modules补丁）。这是可行候选而非既定门禁；若采用DOM声明需评估服务端browser globals的lint约束，不能冒称原手册强制这些flag。
- 依据：[Vitest迁移说明](https://vitest.dev/guide/migration/)、[typed lint](https://typescript-eslint.io/getting-started/typed-linting/)、[deepmerge发布说明](https://github.com/RebeccaStevens/deepmerge-ts/releases)、[deepmerge公告](https://github.com/advisories/GHSA-ggr8-5vv4-36mx)、[mysql2公告一](https://github.com/advisories/GHSA-3f6p-5ww8-9rcr)、[mysql2公告二](https://github.com/advisories/GHSA-rgwj-5xj2-c3m3)；精确版本与发布年龄以当日npm metadata和实际pnpm11.25行为验证，不套用浮动latest。

ST-I2-B CLI生命周期裁决：允许薄composition root直接装配同一owner service/store及现有Prisma/ObjectStore，不为ApplicationContext创建空协调provider。所有资源创建/connect由try/finally覆盖，部分启动失败逆序释放已创建资源，单个关闭失败不得阻断其他资源；不启动listener/Redis/scanner、不复制业务规则/SQL/DI框架。需CLI参数与失败生命周期测试、技术设计同步；无消费者的reconciliation.module删除，不留双轨启动路径。Storage唯一writer继续负责，Root仅本计划和Git操作。

ST-V-T只读候选审查卡：storage_contract_review(gpt-5.6-sol)审查Root固定347e6dd临时工具链候选及registry证据，不审查正在写入的I2、不改任何文件/lock/配置、不执行安装/共享服务/Git。范围为Node/TS/eslint/Vitest兼容、24h年龄策略、两条精确Prisma overrides的语义风险/正式ADR与退出条件；依据CODEBASE_MAP、TS手册8.5及本节日志。交付明确阻断项与可采纳条件，不把候选0audit或257测试推广为活动I2验收。Root继续准备typed-lint门禁与I2最终集成，原writer仍唯一Storage写入人。本审查不替代后继正式实现的符合性与质量审查。

ST-V-T审查结论与Root核验：版本组合可采纳；正式落仓先有override ADR，不能原样接受候选。准确依赖名为eslint10.9.1及typescript-eslint8.69.0。审查员要求仓内显式1440；Root核对[官方pnpm11发布说明](https://github.com/pnpm/pnpm.io/blob/main/blog/releases/11.0.md)确认固定pnpm11本身默认1440，所以历史结果不是未知用户配置的唯一解释，仍采用显式配置作为可审计/防升级漂移门。Root独立HOME、XDG_CONFIG、空store及固定11.25 CLI实测：1440+strict/no-exclude下年轻mysql2 3.24.4解析失败，成熟3.24.3解析及空store frozen安装通过，证据 `/var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-storage-release-age-isolated.ylp7tfto`。未修改Storage。

Root候选typed-lint虚拟正反例：ESLint.lintText对项目内虚拟src/main.ts解析，安全unknown窄化正例0诊断；不安全JSON.parse值/浮动Promise/void回调Promise/遗漏union分支的负例实际命中unsafe-assignment、unsafe-call、unsafe-member-access、no-floating-promises、no-misused-promises、switch-exhaustiveness-check六规则。证据候选目录typed-rule-fixtures.log，未写业务源码。正式配置必须保留这些真实规则回归，不靠字符串检查配置冒充效果；全preset多出的require-await及根配置projectService范围分别处理。

ST-I2-B回归诊断仍未验收：writer首次全套316/317出现旧dedup P2034；第二次共享库失败转移到新canonical用例，旧dedup孤立4/4。Root要求保留原同业务双client竞争断言、不得提高生产重试或关闭默认并行。全库retirement扫描及新增canonical高写入套件改用各自官方bootstrap自有随机空库，writer报告317通过仅为待交接旁证，仍须固定manifest、独立审查及Root新库验证。不能把SSI相关性当作生产性能结论。

### ST-I2-B 稳定交付审查卡

- 扩围仅Storage AGENTS.md、SCHEMA_OWNER_INVENTORY.md、SCHEMA_BOOTSTRAP.md中Schema-only旧状态/已接收SHA/本片待验收事实同步；不改规范或其他运行流程。最后必要provider修复含确切删除拒绝wildcard/空白ETag且保留合法opaque引号值，以及HEAD缺实际ContentLength/ContentType fail-closed，不补0/octet-stream。
- 基线347e6dd+52物理路径（34M/18A），稳定时间2026-09-08T10:45:48.465005Z，manifest `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-storage/.tmp/st-i2-b-logs/handoff-manifest.json` SHA256 `01890e0097eceeba9a38f884aa472e72037c6a4c193998f151df06e783a20642`。Root逐一核验52当前/原始hash、dirty集合、HEAD和空index一致；writer已停写。
- storage_contract_review(gpt-5.6-sol)先只读符合性审查：已定I2三文档/ADR、8组验收、原十RPC与错误/幂等/tenant、CLI生命周期、scope/删除项，不跑安装/测试/生成/Git/基础设施；放行后storage_data_review(gpt-5.6-sol)质量审查完整snapshot CAS/真实P2002有限重新观察/retirement并发与精确删除安全。两者绑定此manifest，任何必要修复重新固定。Root保留主树独立新库验证与唯一提交，不修改writer文件。
- writer三轮322/322+compiled2、schema/contract/generator/lint/typecheck/build与真实local CLI为旁证，Root尚未验收；52定向format过、全仓13历史format失败留ST-V。Schema/generated/Proto/package/CI/Docker无差异，所有writer自建库已删除。handoff-evidence.md保留早期失败及最终命令，不冒充S3/ClamAV/镜像实测。

### ST-I2-B 已接收：b5ad3e0440a819a074c48d68d97af9afe0d48527

- 符合性和质量两名只读审查员顺序放行，均无可证P0/P1/P2。Root `/tmp/kokoro-storage-main-i2-lifecycle.YqAsd8` 两个独立新主库默认并行各58文件322测试，compiled2、lint/typecheck/build/validate、精确七表七enum零FK/apply/drift、contract→generate→contract通过，官方产物无变化。
- Root首次误将全库CLI验证放在已含state suite metadata的测试库，CLI正确报告另外3个missing对象并exit2，harness失败保留cli-local.log；随后只在独立新CLI库运行，两次apply均0，真实local旧创建时间不越过retiredAt宽限、过龄确切删除/current与unknown保留。修正的是Root资源编排，不修改源码/断言。
- 隔离prod/no-optional冻结安装、无CLI/TS/tsx/Vitest、编译Nest与reconciliation owner import、真实Prisma retirement count0通过。`pnpm audit --prod`仍将未安装的optional Prisma CLI链列入并报3条既知告警；按实际安装闭包`--prod --no-optional`为138依赖0告警。两个输出都保留，不把后者当完整供应链已清零。所有Root创建的主库/CLI库/prod查询库均已drop。
- 52文件定向format与diff check通过，全仓13历史format失败仍列明。Root提交前核验52dirty、基线/空index/逐hash，显式暂存52路径、staged blob/diff再提交；提交后全部52blob与manifest一致且Storage树clean。b5ad3e0标题feat(storage): reuse canonical objects and retire replaced identities safely。

### ST-V1 工具链与质量门卡（先设计门）

| 项 | 范围与条件 |
|---|---|
| 任务 | P1：固定兼容工具链、type-aware lint实际门禁、格式与完整依赖审计；不扩到部署重写 |
| Owner/执行 | Storage工程门禁；storage_implementation(gpt-6-astra)继续唯一writer，Root架构/审核/提交；原两审查员只读 |
| 基线 | /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-storage；codex/production-closure-docs；b5ad3e0440a819a074c48d68d97af9afe0d48527，clean |
| 当前事实 | Nest/Prisma运行与I2通过；TS5/@types-node22/Vitest2及非type-aware ESLint尚在；完整audit3既知Prisma CLI链告警，13历史format失败。Root候选基于旧347e6dd，不能照搬测试结果 |
| 目录比较 | A扩展现有package/workspace/tsconfig/eslint/vitest、test/architecture和现有测试，ADR解释核心选型；B新建tooling顶层/第二测试工具或万能helper无持续业务职责，淘汰。只新增有真实验证责任的普通测试文件及一份ADR，不建新业务模块/owner |
| 设计门文件 | 先更新TECHNICAL_DESIGN、API_CONTRACT、DATA_MODEL明确当前b5ad3e0与目标工具链、API/数据不变；一个新ADR记录候选比较、维护/许可/供应链、精确版本/官方依据/时间、失败语义与退出路径；必要CURRENT/ACCEPTANCE/INDEX引用。先报告三文档绝对路径、当前SHA、未决项和验证计划，Root核对后才改配置/代码 |
| 候选 | Node24.20/pnpm11.25保持；TS6.0.3、@types/node24.13.3、typescript-eslint8.69.0、ESLint10.9.1、Vitest5/Vite8.2.2、Prettier3.9.6、handler4.12.1；Nest12/Prisma7.10/Connect2.2不升级。其他直接依赖固定当前lock已核验精确版本，不浮动latest、不额外major升级 |
| override门 | 仅@prisma/config@7.10.0>deepmerge-ts8.0.2及prisma@7.10.0>mysql2 3.24.3；ADR显式承认前者跨major：实际Prisma config普通对象配置，Map/Set/数组差异评估，本仓不把MySQL/Studio作为生产数据路径。真实config validate/generate/db push/read-only diff及配置解析回归，供审查；Prisma上游修复/批准升级立即移除两条scope并重验lock/audit，禁止泛全图override |
| 冷却 | 仓内显式minimumReleaseAge:1440 + strict:true，不设exclude；独立配置/空store正反例，frozen实际安装。Root探针是选型证据，落仓还要验证当前配置 |
| typed lint | 使用projectService/type-aware，显式unsafe-assignment/call/member、floating/misused及所需exhaustiveness固定选项；unsafe-return/argument随采用preset保持。六规则真实lintText正负例及现有import边界回归。解析JSON到unknown后窄化、保持Promise/abort语义，不靠any cast、通用disable或改变测试行为清零；可选require-await与async双桩的适用范围在ADR说明，任何例外具体且不触碰上述强制规则 |
| 类型/build | TS6显式build rootDir=src保dist/main.js；Node类型major与runtime对齐。全声明skipLibCheck=false+DOM只是Root可行实验，非强制扩大本片；不手改node_modules/generated。根prisma/vitest配置的projectService覆盖可在既有tsconfig纳入，build仍只src |
| 允许实施集 | 门通过后package.json/pnpm-lock/pnpm-workspace、eslint/tsconfig/vitest/prettier相关配置、当前13format文件（compose仅格式无运行语义）、为typed lint所需的既有src/test/scripts定点类型修正与架构门正反例、相应文档/ADR；contract/provenance仅格式且JSON语义字段/digest不变，contract/Proto内容不变 |
| 排除 | 业务状态机/API/SQL/schema/generated变化，CI/Docker/compose功能/依赖服务编排重写，其他owner/Root、用户数据、共享服务启停、真实SLO宣称。必要越界先报Root |
| 验证/交付 | 先RED/策略反例，完整format/lint/typecheck、322基线+新增默认并行独立PG、compiled2、build/validate/七表apply/drift、contract→Prisma generate→contract隔离、完整audit及prod/no-optional冻结闭包/真实查询。预留版本和生成物检查，不取消失败门。固定manifest停写→符合性→质量→Root主树复跑/小片提交，Git仍Root独占 |

ST-V后继仍须独立卡：唯一资源拥有权的部署/CI/compose/生产API smoke、真实S3/ClamAV/ObjectLock/镜像和信号验收；Docker socket目前只读仍超时，未获得重启答复，不擅自重启。工具链完成不代表整个Storage目标完成。

ST-V2-P只读依赖调查卡：storage_data_review(gpt-5.6-sol)调查真实S3测试provider的可维护选择，不改任何仓/配置/lock、不安装/启动服务、不访问用户数据。基线Storage b5ad3e0的S3 adapter/现compose；Root在2026-09-08核对[MinIO官方仓](https://github.com/minio/minio)已归档且社区只发源码，历史二进制不维护；[最后安全发布](https://github.com/minio/minio/releases)要求源码构建，故不能直接把minio/minio:latest当当前维护中的稳定fixture。限比较保留固定MinIO源码仅隔离测试、一个维护中的开源S3实现、用户提供AWS sandbox三路，重点VersionId/HEAD/conditional Delete If-Match与ObjectLock证据、维护许可/精确版本/镜像可用性；只给下一片ADR输入，不擅自替换provider或要求用户现在给凭据。Root并行核对ClamAV官方维护版本/OCI metadata及隔离部署边界，writer继续V1设计门。交付官方来源、实际支持与未验项分开，既有MinIO profile/API不在本研究改动。

ST-V2-P结果与Root裁决输入（未批准provider替换）：MinIO[官方issue21677](https://github.com/minio/minio/issues/21677)报告2025-09版本忽略DeleteObject条件头；Root进一步只读[最后2025-10安全tag的DeleteObject handler](https://raw.githubusercontent.com/minio/minio/RELEASE.2025-10-15T17-29-55Z/cmd/object-handlers.go)亦未见IfMatch接线，而同文件PUT明确接线；这是静态风险线索而非实际重现，足以拒绝用旧MinIO基本PUT/GET通过冒充条件版本删除合格。只读审查给出的维护中候选为[Ceph RGW20.2.4](https://docs.ceph.com/en/latest/releases/tentacle/)，但MON/MGR/OSD/RGW很重、不是单容器替身，版本+IfMatch组合尚须真实412/对象保留验证，Root未授权默认启动或更换profile。用户日后自备AWS sandbox可提供最直接语义证据，当前未请求凭据。下一片需明确provider资格测试与不支持条件删除时的失败边界，不能仅换品牌或伪造兼容。

Root ClamAV核验（2026-09-08，metadata-only）：[官方发布](https://blog.clamav.net/2026/)当前安全补丁为1.5.4/1.4.6；[官方Docker仓](https://github.com/Cisco-Talos/clamav-docker)区分Alpine amd64与Debian多架构。registry OCI index与arm64 child/config逐字节SHA256已核验，日志 `/var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-storage-clamav-metadata.elkeykcw`。候选 `clamav/clamav-debian:1.5.4@sha256:4c975c439fcb7ab9cbdd72162c2802f5efcb4a11dcf5b0b37da1d746474ef20e` 含amd64/arm64/ppc64le；arm64 config创建于2026-09-07T07:24:05Z，官方healthcheck为clamdcheck.sh、startPeriod360s。1.4.6 Debian index为`sha256:6a7d6f2d65398bfafb0cb171a9746ac8868fae6c56f188e90b34ddb0caf8d5dc`。预载签名的正式镜像可避免每次空容器下载全部数据库，4GB内存预算按[官方Docker说明](https://docs.clamav.net/manual/Installing/Docker.html)评估；尚未pull/run/扫描或采用，不将metadata视为真实ClamAV测试。后继更新须显式digest及签名/基镜扫描与刷新规则，不能永久冻结后宣称安全。

### ST-V1-D 已接收并放行实施

- 8文档稳定manifest `2e4b6aaa10dcab0ca5a9b18c26df31dac5f23277fc3d08842f29a87ff17b6331`，Root核验原始b5ad3e0/空index/dirty与逐hash。ADR0003明确真实Prisma普通对象配置域、跨major风险、两scope移除条件、精确peer/许可与年龄、typed lint选项和Vitest5语义；无新owner/API/数据决策未决。
- Root `/var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-storage-main-v1-design.h4aq3ctr` 8文档format、prisma validate、contract check与生成物/Schema无差异、diff通过；无数据库连接。显式8路径暂存、逐staged/committed blob核验后提交 `cd66be53cc4d357a1180e6146259f608fc0d27fd`，Storage clean。设计批准与实现验证区分，ADR在后继实施时同步Accepted（方案已批准、尚待实际验收），不宣称工具链已完成。
- ST-V1-I沿用上表全部实施范围/排除与验证，基线改为cd66be5，唯一writer仍storage_implementation(gpt-6-astra)，Root Git/集成，正式放行。先重新记录322行为基线/typed规则RED，registry重新核验再精确依赖；网络失败保留实际日志、做其余可推进部分，不用关闭年龄门或偷偷改源规避。六typed规则正反例、Prisma真实配置解析及官方CLI、mock生命周期/原并发语义均需验证，不能只复制旧347候选结果。
- 待完整fixed manifest停写，仍符合性→质量→Root新库/生产闭包独立验收后提交。只格式治理既有compose，不顺手替换S3/ClamAV镜像；ST-V2 provider风险已由Root另行调查，本片不扩进程/配置资格协议。

ST-V1-I定点规则裁决：writer报告旧基线新库322通过、typed门10测试8RED/2pass后接线初步GREEN、压缩registry重取成功与10候选均>24h，未压缩大metadata超时原日志保留；这些仍待固定交付。Root批准仅四处可选规则行级例外：LocalObjectStore两个签名URL async方法require-await（验证错误保持Promise rejection而非同步throw），ConcurrencyGate/RequestLifecycle两处reject(signal.reason)的prefer-promise-reject-errors（标准AbortSignal允许任意reason且保留身份）。具体理由注释和时机/身份回归必需，unused-disable仍报告，所有强制typed规则不豁免。安装仍提示传递Smithy handler4.12.0：先查父路径/range；只有父声明已接受4.12.1时可定向刷新同已批准patch的lock，不升级AWS/其他包、不全图dedupe，固定旧patch父依赖则另报Root，不擅自加override。

ST-V1-I补充：三父client-s3@3.1124.0、nested-clients@3.997.44、credential-provider-http@3.972.72均声明handler ^4.11.3；writer用官方定向update仅收敛handler4.12.1、无新override/父升级，最终须交父range与lock证据。Root另批准既有readiness测试两处、request-lifecycle测试两处、clamav测试一处abort回调的prefer-promise-reject-errors行级例外，同样保持原reason identity；总计9处例外单独列清单，不扩测试全域或强制规则，unused-disable与行为回归保持。

ST-V1-I格式扩围：Prettier3.9.6全仓RED除原13债和本片编辑外，另需三个旧源码打印变化；Root仅批准src/assets/object-retirements.store.ts、src/common/commands/receipt-codec.ts、src/integrations/object-store/aws-sdk.ts的官方formatter纯格式输出，语义/常量/import不变，manifest标format-only，Root最终逐diff核对。不据此授权无关格式或generated改动。

ST-V1-I另特批docs/ACCEPTANCE_AND_RISKS.md仅新版Prettier格式、无状态措辞修改，与上3源码组成4个额外format-only路径。冷安装首次180s外层超时，Root允许最多600s有界续跑与只清理自有进程组；禁止换源/放宽年龄/allowBuilds，首轮输出未保存需如实记证据不足，续跑不能称单次纯冷成功。

### ST-V1-I 稳定审查卡

- 2026-09-08T11:32:57.744982Z固定，基线cd66be5+50物理路径（45M/5A、14标format-only）；manifest `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-storage/.tmp/st-v1-logs/handoff-manifest.json` SHA256 `dca94012307798227861fbd203e4c586737b96f3530a65d7ca25b302af4221cd`。Root逐hash/原始hash/dirty/空index/HEAD核验相符，writer停写。
- storage_contract_review(gpt-5.6-sol)先只读符合性：ADR0003/精确版本/两个scope/1440严格无豁免/六typed规则真实正反例与9特批例外/Vitest5语义/原API数据不变/format-only范围。放行后storage_data_review(gpt-5.6-sol)质量审查生产和测试类型修正是否改变Promise/abort/竞态、配置loader真实回归、cold/frozen/audit证据及门禁有效性。两者不写/安装/测试/Git/基础设施，绑定manifest；Root同时保留主树独立验证。
- writer两新库347+compiled2、完整format/lint/typecheck/build/schema/contract/生成隔离和完整443 audit0为旁证；独立生产全新store24.3s、139audit0、编译真实查询通过，完整隔离cold起点180s超时后同store68s续跑成功，明确非单次全冷成功。尚未Root接收或提交。50路径不含Schema/generated/Proto/CI/Docker功能，全部自建库与安装子进程已清理；ST-V2仍独立未验。


ST-V1-I 独立审查与 Root 复验（待冷闭包收尾提交）：符合性 storage_contract_review 与质量 storage_data_review 均绑定 dca94012 manifest、无可行动 P0/P1/P2，未自行安装/测试/写入。Root `/tmp/kokoro-storage-main-v1-tooling.cPd5W1` 在原主树默认并行两独立随机主库各 63 文件/347 pass/0 skip，compiled 2、format/lint/typecheck/build/frozen/完整 audit 443依赖0告警、三个自有空库 schema apply/validate/contract→generate→contract/生成无变更、独立CLI两次0、50文件hash/diff检查通过，所有自有库清理。Root另逐字验证14个format-only文件等于 Prettier3.9.6 对原基线的输出。另开独立 HOME/XDG/空store 的完整安装和生产安装闭包，日志 `/var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-storage-root-v1-closure.d3deawub`，仍执行中；不把主树缓存frozen替代cold结果。

本轮 Root 治理实跑 `/tmp/kokoro-storage-root-governance.BgzFGJ`：standard exit1/208条（Storage24），topology exit0，scripts/tests 82 pass/2 fail（既有手册示例数/参考依据标题断言）。Storage记录包含旧SQL canonical、src/modules拓扑、generated Prisma被误判wire/config、旧strictDepBuilds/精确engine和编译策略等与当前手册/批准ADR不一致项，以及HTTP契约待查项，不能直接按旧checker恢复SQL/旧层或手改generated；原始失败保留，未宣称全仓门绿，Root通用checker修订不在本Storage写入范围。只读Docker `_ping` 3秒仍超时，未重启。

### ST-V2-D 下一片设计准备（只读，尚未放行写入）

| 项 | 决定/范围 |
|---|---|
| Owner | Storage test/deployment；不新增服务、业务writer、定时器或跨仓owner |
| 当前事实 | V1稳定50路径尚待提交；旧production-runtime测试绕过返回签名URL并直接SQL清理，docker-smoke按固定名称先删容器，CI/compose默认共享资源且依赖陈旧，均未实际运行 |
| 目标职责 | 分两小片：A真实RPC返回URL上传/下载与外部S3资格；B唯一run资源隔离、CI/RC和扫描。代码通过与真实provider/镜像通过分开记录 |
| 目录比较 | 采用现有 test/smoke、test/fixtures 与 scripts，各自测试/资源编排职责；不放src业务Service或新顶层e2e工程，避免生产附带测试和第二实现 |
| 粒度 | 优先改现有测试；多个smoke共享的有界资源生命周期可在既有fixtures添普通文件，不搭通用框架；新具体文件集等只读盘点后确定 |
| 依赖 | 测试消费现有owner generated client、Prisma和AWS官方SDK；应用仍Nest构建入口，禁止SQL CRUD绕过、修改I2事务语义或新开PG/Redis实例 |
| 数据/API | Proto/schema不变；每run数据库、tenant、bucket/object版本和容器ID须显式owned；共享实例只复用，清理仅成功创建的资源，AlreadyExists不得据此认领 |
| Provider决定 | 不默认换Ceph或启动已归档MinIO；显式外部配置资格测试缺参非零失败，不skip报绿。VersionId+IfMatch错误412/保留对象、正确仅删指定版本、ObjectLock失败保留retirement必须实测；不支持则资格失败，不加不安全HEAD-delete fallback |
| 删除项 | 按片删除SQL取objectKey/手写清理、绕过签名URL、固定container预清理、固定compose down和旧默认凭据资源；不预先批量改配置 |
| 验证 | 各片RED/GREEN与全默认测试/typed/构建/契约schema保护；模拟命令可验证隔离失败恢复，但不冒充真实S3/ClamAV/OCI/部署证据；Docker API当前无响应为后继真实执行限制 |

准备负责人 storage_implementation（gpt-6-astra）仅只读盘点最小两片文件集和复用入口，不写/安装/服务/DB/Git；Root保留当前V1验收关键路径。V1提交后才补三设计文档/ADR并通过第8.1门，再按单writer放行实现。


### ST-V1-I 已验收

- Storage提交 `030d2c1fb1d3d09117757e5592eee5a1a65e067e`，50物理路径（45M/5A）按manifest逐原始/当前/staged/committed hash核验，提交后clean。符合性与质量审查均无P0/P1/P2，主树验证见上；不把worker报告单独视为完成。
- Root真正全冷隔离安装单次264.0秒成功：全新HOME/XDG/store、原1440/strict/allowBuilds、388包及官方三个postinstall完成，下载慢/重试原输出完整保留；冷快照typecheck/build通过。与worker首次180秒超时+续跑事实分别记录。独立生产另一空store单次88.2秒成功，`--prod --no-optional --ignore-scripts --frozen-lockfile`实际139依赖/0告警，plain Node加载Nest owner与ReconcileObjectsService并真实Prisma retirement count0，CLI/TS/tsx/Vitest不可解析。日志 `/var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-storage-root-v1-closure.d3deawub`。
- Root生产probe首次把reconcile-objects.service写成reconciliation.service，真实报ERR_MODULE_NOT_FOUND（prod-query.log）且自有DB已清理；只纠正临时probe导入路径后另建新库再次官方apply/query通过（prod-query-corrected.log），未改源码、断言或依赖闭包。该失败属于Root harness接线错误，不计生产缺陷。所有本次自有DB已删除，最终50hash不变。
- 全部已验功能：Prisma数据owner、实际Nest运行与取消/drain、canonical复用/repair CAS/退休GC、兼容工具链typed门。未闭环：V2实际S3条件版本/ObjectLock、ClamAV、OCI/RC/CI、内部HTTP机器契约、容量/SLO及Root全仓checker一致性。总目标保持active，不宣称完整生产验收。


### ST-V2-D 文档门任务卡（放行文档，未放行业务/测试改写）

| 项 | 决定 |
|---|---|
| 任务/优先级 | P1；确定两个最小可审查切片：A返回签名URL真实链及版本/锁定资格，B部署资源拥有权、剩余smoke与CI/RC；三设计一致后Root放行 |
| Owner/Agent | kokoro-storage；storage_implementation(gpt-6-astra)唯一writer，Root架构/审查/提交；两个reviewer后继只读 |
| 基线 | /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-storage，codex/production-closure-docs，030d2c1fb1d3d09117757e5592eee5a1a65e067e，clean |
| 允许路径 | docs/TECHNICAL_DESIGN.md、API_CONTRACT.md、DATA_MODEL.md、CURRENT.md、RUNBOOK.md、ACCEPTANCE.md、INDEX.md、ADR/README.md；新增docs/ADR/0004-isolated-provider-qualification.md；AGENTS.md只修已验收状态入口，不复制规则 |
| 排除 | src/test/scripts/contract/prisma/generated/package/lock/CI/Docker/compose全部不得改；其他仓不在范围；Root计划只由Root编辑 |
| 固定决定 | 承接上表；不更换默认provider、不默认启动MinIO或重型Ceph；ClamAV候选digest仅设计采用而未实跑。外部资格测试显式配置独立fixture bucket和可撤销自有version legal hold，缺失配置或不支持412条件删除即失败；不自动创建bucket或开启用户bucket versioning/ObjectLock、不设置compliance retention、不绕过用户锁、不修改I2失败保留语义 |
| 所有权 | bucket本身外部提供、只读检查所需能力，不认领/删除bucket；写入前每run高熵唯一tenant/key prefix，登记自己创建的确切key/version；只解除本测试亲自设置的legal hold。创建/清理失败明确非零并保留资源清单，单项失败继续其他资源释放。自建DB由创建者删除，不以名称前缀认领既有DB；PG/Redis本地复用 |
| A目标文件集 | 修改test/smoke/production-runtime.e2e.test.ts、capability-package.e2e.test.ts、s3.integration.test.ts；必要共享fixture smoke-provider.ts（配置/资源生命周期）与storage-roundtrip.ts（真实RPC URL链）和对应unit；若职责需要再拆普通文件先报告，不在一文件混schema/type/常量/fixture编排；依赖/Schema/Proto不变 |
| B边界 | 后继单卡精确授权docker-smoke/compose/CI/release、scanner/infra smoke、deployment/quality架构门及命令double测试。一个token双端传递、可达签名endpoint、容器ID创建登记、随机端口和有界逆序cleanup；同OCI产物scan+smoke之后发布。GitHub job自身PG/Redis不等同本地共享实例，不先重启当前Docker |
| 文档门验证 | 文档format/diff、Prisma validate、contract check及原始Schema/generated/Proto无变化；给三份绝对路径、commit、未决执行项和对应命令。无DB/服务/镜像/云操作；先固定manifest停写，Root审查提交后才A实施 |
| 交付 | Root唯一Git index/commit负责人；writer交精确路径/hash与文档门证据。当前S3/ClamAV/ObjectLock/OCI/SLO未验，HTTP机器契约单独后继处理，不在A/B偷偷扩契约 |

只读盘点还确认docker-smoke容器与RPC客户端默认token不同、生产URL默认files.example.test；旧测试SQL取key+SDK PUT恰会绕过URL可达性。A须删旁路，B须同一token与真实可达public endpoint；现有capability-package旧PUT重放不改变final字节断言应保留。组件scanner直接SDK PUT属于fixture不是生产旁路，SELECT1属于探针不是业务SQL CRUD；避免机械误删有效职责。


ST-V2-D设计细化裁决：Root于2026-09-08重新核对[AWS DeleteObject](https://docs.aws.amazon.com/AmazonS3/latest/API/API_DeleteObject.html)、[PutObjectLegalHold](https://docs.aws.amazon.com/AmazonS3/latest/API/API_PutObjectLegalHold.html)与[ObjectLock管理](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock-managing.html)。fixture bucket预检查需versioning/ObjectLock已启用且无DefaultRetention；不得自动设置bucket不可逆属性。针对本run确切version读回状态、设置legal hold与清理，未知设置结果不冒称确认成功。只登记的确切key写入意图可用于有界恢复该key未知响应生成版本；未知Complete final candidate仍只报告，不从tenant prefix推导删除授权。

批准未来A最小范围补充（尚未代码放行）：test/fixtures/smoke-provider.schema.ts单独配置解析；test/fixtures/smoke-provider.ts仅对象版本/自设hold生命周期；storage-roundtrip.ts仅RPC返回URL链。现有test/fixtures/isolated-prisma.ts增加显式preserveDatabase选项及对应unit：默认close仍删自己成功创建的库；外部cleanup失败保留库/retirement证据但关闭连接，不认领任意既有数据库，重复close与部分init失败须验证。保留资源必须非零并打印非敏感DB/key/version和后续owner，不称全清。三设计仍只按既有10文档范围执行。


ST-H0只读后继调查卡：storage_contract_review(gpt-5.6-sol)在Storage030d2c1源码基线调查Library HTTP机器契约缺口；只读src/transport、src/library、现有runtime schema和contract生成入口、手册与API_CONTRACT。目标列出现有唯一请求/响应/错误事实源、可行的两种单向生成方式（官方Nest/OpenAPI或成熟schema生成器）及最小影响/是否新核心依赖；若给版本/兼容结论先核对官方来源。本任务不改任何文件、安装、测试、服务、DB或Git，不扩V2A/B契约，不伪称当前无机器契约为已满足。允许只读研究与V2文档writer并行，Root保留总体裁决与提交；交付建议/证据/未决，由Root后续单卡才放行。


ST-V2-D 首次固定10文档manifest ffff95def91882fdfae2809208cfa1ccac39ba37957a3a92f3741f3d718538d4（030d2c1基线）已收到；Root符合性审查发现运行时readiness自动建桶与方案只读边界矛盾，故未提交/未放行A。当前aws-sdk.ts ensureReady会HeadBucket 404后CreateBucket并吞AlreadyOwnedByYou/AlreadyExists，不能仅凭fixture凭据预期无建桶权限保证无副作用。

Root明确A定点扩展：src/integrations/object-store/aws-sdk.ts的ensureReady只保留HeadBucket，删除自动CreateBucket与Already*成功分支；环境owner预置桶，missing/auth/timeout保持readiness失败及原signal/cause/Nest生命周期，不新增配置开关/兼容fallback，不改对象promote/上传/事务/CAS/retirement。test/unit/object-store.test.ts新增SDK调用RED/GREEN，证明404/NoSuchBucket/403/timeout/abort零建桶、成功仅HEAD、init失败仍destroy。先由writer在原10文档范围记录行为改变/删除项/测试范围并重交manifest，此时仍禁止源码改动。

ADR凭据澄清：当前显式KOKORO_OBJECT_STORE AK/SK客户端无sessionToken字段；临时凭据仅指aws profile官方默认链保留AWS_SESSION_TOKEN，不宣称custom显式AK/SK也支持。A不扩生产凭据schema，fixture和真实运行必须同来源，禁止混用导致资格通过而runtime丢token。

ST-H0调查已返回，尚未采用：当前Library请求是URL解析、响应mapper/envelope而非完整运行时schema，确实缺机器OpenAPI。官方Swagger11.4.6 peers仅Nest11，不可直接称兼容本仓Nest12；Zod3兼容生成器zod-to-openapi7.3.4已非活跃支持线，不能只因能生成就批准新核心依赖。后继应比较批准升级Zod及受维护生成器/等待兼容稳定Nest companion的范围和退出，不能无审查引入遗留桥；不混本V2A/B，Proto保持。只读报告官方来源归后继设计输入，当前不安装/试验/改HTTP。


ST-V2-D第二版879ab7d8已由Root独立format/Prisma validate/contract/diff及全部非文档hash验证通过，日志 `/var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-storage-root-v2-design.vgmr7oov`，未连DB。随后storage_data_review质量审查发现1项P1，未放行提交：原同key v1/v2后用旧v1 ETag条件删除非current v1成功的矩阵，与[AWS conditional deletes](https://docs.aws.amazon.com/AmazonS3/latest/userguide/conditional-deletes.html)明确只评估current version的语义冲突，Root已独立核对官方Note并接受，不以API参数同时存在推断组合一定成功。

**最新矩阵裁决（取代此前同key删旧v1的要求）**：按生产final key不复用输入域，key A只有一个current v1；错ETag+VersionId实际412并保留，正确current ETag+VersionId实际删除且无delete marker；独立control key B/version字节前后不变。不得移除生产IfMatch或借current新ETag删除已退休旧identity；外部同key写入导致current ETag不同返回412时保留retirement。不要泛称全部non-current情况恒为412，同ETag需按实际条件判断。此为纠正Root早期测试假设，不是降低provider门。

正常roundtrip旧签名URL再次PUT会产生多个staging版本，fixture成功cleanup须停止写入后逐次以provider真实current identity核对registry，再携该确切VersionId+ETag条件DELETE；出现未登记current保留key/DB，不能按VersionId字符串/客户端回执次序猜current，也不能先删非current旧版本期待其ETag仍匹配。HEAD用于选择已登记当前identity，不替代条件DELETE、不移除IfMatch。writer仅修同10文档并重交，质量审查员保持只读待新manifest，源码继续未授权。


### ST-V2-D 已验收 / ST-V2-A0 放行

- D提交 `341a9889a0d957d728d6efa9bf4474859211d22c`；最终9d8b5123 manifest、10物理路径逐原始/staged/committed hash验证、提交后clean。Root符合性审查与storage_data_review质量复查通过，原current-only矩阵P1关闭；Root最终 `/var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-storage-root-v2-design.km1g0v60` 文档format/Prisma validate/contract/diff与所有非文档tracked hash不变通过，无DB连接。D通过仅批准设计，非外部provider或实现通过。

| 项 | ST-V2-A0任务卡 |
|---|---|
| 任务/优先级 | P1；ObjectStore readiness只读化，移除自动建桶副作用，先独立闭环再A1 |
| Owner/Agent | Storage integrations/object-store；storage_implementation(gpt-6-astra)唯一writer，Root符合性/Git/集成，storage_data_review后继独立质量审查 |
| 基线 | /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-storage，codex/production-closure-docs，341a9889a0d957d728d6efa9bf4474859211d22c，clean |
| 写入 | src/integrations/object-store/aws-sdk.ts仅ensureReady与移除不用import；test/unit/object-store.test.ts仅相关回归。原D十文档允许仅更新A0当前状态/设计Approved/实际证据及必要行为说明，不改A1/B方案、不增新文档；不为了凑文件修改 |
| 禁止 | A1 fixtures/其余测试/scripts/CI/compose/Docker/Schema/Proto/generated/package/lock/其他src/其他owner；不连接任何用户S3或建桶/启动Docker |
| 行为 | ensureReady成功仅HEAD；404/NoSuchBucket/403/timeout/abort失败且零CreateBucket，保留原signal/cause和Nest启动失败destroy；不改变其他对象方法/事务/I2，不新增create开关或fallback |
| 验证 | 先新回归在341a988 RED证明缺陷；GREEN后format/lint/typecheck/build、默认并行347+新增且显式新随机PG、compiled2、Prisma validate/官方仅自有空库apply/contract→generate→contract及protected hash。共享PG/Redis复用，无S3/ClamAV/镜像证明；Root主树重跑后验收 |
| 交付 | 不stage/commit；固定精确文件hash+实际RED/GREEN/全门日志后停写，Root独立质量审查/主树验证/按路径提交；A1不抢先实施 |

放置理由沿ADR0004：这是现object-store adapter readiness职责的局部修复与现unit回归，不建立新模块/抽象；missing bucket从“尝试自建”变为启动/就绪失败，部署预置职责明确。


ST-H0继续只读调查：为避免新增已非活跃支持的Zod3生成桥，storage_contract_review比较“统一升级当前Zod4稳定版 + 受维护的zod-to-openapi稳定版”与先前方案；仅官方精确版本/peer/维护/许可证/发布时间、静态现有zod导入和API用法/潜在语义变化/最小文件范围，不安装、生成、测试或改任何文件/配置。与A0单writer独立，不构成升级授权；Root后继设计需实际回归/契约不变和依赖审核，未证明兼容前不声称可直接升级。


### ST-V2-A0 已验收 / ST-V2-A1a 放行

- A0提交 `9b609671dfe31a6d899e4c3d9613e40ecf4a6240`，b89f71d6 manifest的12M逐原始/staged/committed hash核验，提交后clean。Root符合性及storage_data_review独立质量审查无P0/P1/P2；Root `/var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-storage-root-a0.2sjrkpnc` 实跑format/lint/typecheck/build/audit443依赖0、自有随机新库官方apply、默认并行63文件360/360无skip、compiled2、validate/contract→generate→contract/diff及所有范围外tracked字节不变。自有DB已删除；source仅HEAD-only，无外部provider声明。

| 项 | ST-V2-A1a任务卡 |
|---|---|
| 任务/优先级 | P1；先实现外部资格所需的显式配置、确切对象/hold资源登记和自有数据库失败保留；下一片A1b才接真实URL与外部smoke消费者 |
| Owner/Agent | Storage test/fixtures，storage_implementation(gpt-6-astra)唯一writer；Root方案/Git/集成，后继独立spec/质量审查 |
| 基线 | /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-storage，codex/production-closure-docs，9b609671dfe31a6d899e4c3d9613e40ecf4a6240，clean |
| 放置 | 沿已批准ADR0004：既有test/fixtures而非src/common/新测试框架；schema只解析/派生，provider fixture只资源生命周期，isolatedPrisma仍唯一亲建DB句柄，不新增业务repository |
| 允许代码 | 新test/fixtures/smoke-provider.schema.ts、smoke-provider.ts、test/unit/smoke-provider.test.ts、test/unit/isolated-prisma.test.ts；改既有test/fixtures/isolated-prisma.ts仅preserveDatabase/close可靠性。需要持久journal独立schema或过大文件等真实拆分先向Root给职责/文件名，不自行扩大 |
| 允许文档 | 既有ADR0004及D原十文档只状态/本片接线与证据；不改A/B已批准语义，不添新文档。新的helper已有真实unit消费者，外部smoke接线A1b明确待办，不冒称A1已完成 |
| 排除 | 全src、其余test/smoke/roundtrip/compiled-entry、scripts/CI/compose/Docker、Prisma/Proto/generated、package/lock/其他owner；不安装新依赖，不实际访问任何外部S3/ClamAV/云资源或Docker |
| 数据/API约束 | bucket只读preflight及current-only矩阵/registry/hold四态/预算/失败preserveDB均以ADR最终current-only修正为准。scope prefix不是删除授权；ON未知不解除，未知current/marker/冲突保留且非零；SDK/client和默认AWS凭据链同源，custom显式AK/SK混session token拒绝 |
| 验证 | RED→GREEN真实SDK命令spy/有界网络double可证明请求形状与resource逻辑，不称providerintegration；缺参零I/O、桶无配置写、404/auth fail、按registry current原子VersionId+IfMatch、同key多版本顺序/未知停止、hold未知、分页重复/预算、0700/0600无secretjournal、单close失败继续释放、DB仅亲建者DROP与preserve/repeatedclose/init未知。完整format/typed/typecheck/build/defaultparallel360+新增/compiled2/官方自有新库apply/双生成保护；测试资源隔离 |
| 交付 | writer不stage/commit，固定路径hash+RED/GREEN/全门证据停写交Root；A1b（真实URL与三smoke）不抢写，成功后单独续派，外部provider缺配置不因源码通过计绿 |

H0维护中候选只读输入：zod4.4.3 + zod-to-openapi9.1.0，生成器peer Zod4/MIT，需另卡完整官方版本/冷却/传递审计与18个旧zod导入面的行为迁移实验；未采用、未安装、不混A1。旧单参record、nativeEnum、coerce.bigint、recursive JsonValue、defaults/refine与datetime等均需保留行为回归，不能用升级顺手改变receipt/config边界。


ST-V2-A1a普通文件扩展批准：test/fixtures/smoke-provider-journal.ts仅承接本run独占0700目录/0600文件、非敏感allow-list记录的顺序落盘和close；不提供旧journal恢复/认领、自动删日志或通用resource框架。provider.ts仍SDK/registry/hold/cleanup，schema.ts仍生产schema派生配置；测试留已批准smoke-provider.test.ts。关联外部副作用必须等待日志写入/必要FileHandle.sync完成，串行写失败后不得继续后续写入；独占创建、不覆盖既有路径，不序列化env/config/SDK原对象/credential/签名URL。明确进程崩溃与整机掉电边界，不宣称日志与外部S3有跨系统原子事务；失败留证非零且释放自有句柄。


外部资源进度：Root已异步询问用户后继真实S3使用的独立测试环境名称（预置versioning/ObjectLock、无默认保留期；凭据只经环境变量、不进聊天）。目前无答复；不暂停A1a源码/本地门禁，不擅自建云资源或重启Docker，也不把外部资格计为通过。


ST-V2-A1a普通文件扩展批准：test/fixtures/smoke-provider-inventory.ts承接同一实际SDK/adapter的只读版本分页、current或确切version HEAD及有界字节digest观察；不创建client、不删除对象、不修改hold、不授予registry所有权。客户端生命周期仍由provider fixture唯一管理，传递相同signal和预算；同时校验KeyMarker/VersionIdMarker完整游标及进展，page上限/不完整结果/delete marker显式失败或留证。只有与请求Key完全一致的版本观察能用于登记判定，Prefix命中的相邻key不推导所有权；不复制current-only cleanup策略，不增加src/依赖/contract。此普通文件拆分将只读观察与资源写入生命周期分离，沿已批准fixtures位置及既有unit验证，无新增模块/ADR。


ST-V2-A1a已固定待审：9b609671基线，17路径（11M/6A），manifest cbaf518c845568cf0fbd02e55c93cfbde838c1c516f073e9f0bc3b441697b033，2026-09-08T13:06:09Z。writer停写，无Git操作；Root已阅读全部新helper并核对批准职责/三设计一致性，开始主树真实门禁。storage_data_review负责独立只读质量审查（沿用gpt-5.6-sol），范围仅此manifest及相关既有adapter/runtime/ADR与test，不改文件/Git/测试数据/共享服务；重点current-only/未知hold与receipt、durable journal、方法级drain、DB亲建/未知证据和测试真实性。引用Root CODEBASE_MAP与TypeScript/SQL手册及当前三设计，交付绑定manifest和基线的P0/P1/P2或无可行动项；Root自行复验、裁决和提交，A1b继续未授权。


### ST-V2-A1a 已验收 / A1b 接线盘点

- Storage提交 `839c9a9f7fa575435ab6934aceb6f1adf22e550d`，17物理路径（11M/6A）逐原始/staged/committed hash与精确路径核验，提交后clean。Root符合性与storage_data_review独立质量均无可行动P0/P1/P2。
- Root `/var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-storage-root-a1a.frl8gt8y` 真实新库默认并行65文件424/424无skip、compiled2/2，format/lint/typecheck/build、audit443依赖0、官方apply/validate/contract→Prisma generate→contract、17hash及范围外241tracked字节不变。Root另真实调用isolatedPrisma创建两库：preserve+重复close库仍存在，默认并发close库已删除；Root只凭本次成功创建receipt删除自己的保留验收库，所有本次亲建库已清。没有外部S3/ClamAV/Docker操作。
- 已关闭Root预审发现：空页变化cursor与缺失IsTruncated、非合作SDK超时、未知CREATE/DROP非敏感诊断、方法跨journal await时close提前清理。修复前失败与worker修复前422输出保留，不冒充最终424证据。

| 项 | ST-V2-A1b-R 接线只读盘点任务卡 |
|---|---|
| 目标/优先级 | P1；落实ADR0004已批准真实URL链与三个smoke消费者，先核对A1a基础helper到实际Nest/Prisma消费者的最小文件范围 |
| Owner/Agent | Storage test，storage_implementation(gpt-6-astra)只读；Root最终范围/共享计划/提交 |
| 基线 | /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-storage，codex/production-closure-docs，839c9a9f7fa575435ab6934aceb6f1adf22e550d，clean |
| 只读范围 | 三smoke（production-runtime/capability-package/s3）、已接收smoke-provider相关fixtures、compiled-entry、storage-client、Prisma schema/receipt/完成事务/真实Nest启动入口、对应test及三设计；其他owner禁止 |
| 确定方案 | 精确返回PUT URL→Complete→GetPackageReference→精确GET验证bytes，旧PUT重用不变final；production-runtime不再SQL取key+SDK PUT。capability-package真实Nest/plain Node，不用TestingModule替换provider。先停止app/在途再对象cleanup，成功后才释放自有DB；容器DB由B拥有不能越权DROP。单资格120秒/RPC420秒，传播同一signal，保留生产Complete300秒 |
| metadata proof | A1b成功Complete只能以同一自有DB中tenant/owner/upload/asset/command已提交关联确认canonical，再真实HEAD/version/ETag/bytes核对登记；不凭prefix/调用者字符串或事后beginWrite授予权限。未知Complete candidate report-only；metadata只读用实际Prisma、不新增SQL CRUD/第二repository |
| 待核定普通文件 | storage-roundtrip.ts只RPC/返回URL流程；必要typed metadata proof在现fixtures普通文件而非src/common，避免provider.ts继续混持久化查询；对应unit和真实自有Prisma integration。若原手写skillZip需替换，用成熟工具生成确定性有效fixture、无新手写ZIP协议/依赖，先给文件名与验证 |
| 排除/交付 | 本R无任何写入/生成/安装/DB/服务/外部provider/Git；交付精确M/A/D文件集、现有复用入口、准备的RED/保留行为、A1a可能需补的public hold释放/confirm接口及未决。Root同一计划明确放置表/范围后才续派写入；不混B部署/CI、H0契约或其他owner |

资料入口继续Root CODEBASE_MAP、TypeScript/SQL专项手册、Storage三设计与ADR0004；既有设计决定不重新向用户询问。真实外部环境仍待配置，不把本地double当provider验收。


### ST-V2-S0-D：A1b前置staging精确清理设计门

只读盘点确认并由Root复核：当前UploadsService Complete359与Abort425使用key-only DELETE，AWS adapter不带VersionId；Enabled bucket会生成staging marker，与已批准fixture未知marker保留规则冲突。该结果为源码及S3协议分析，未做真实provider复现。不能让fixture按prefix认领marker来掩盖生产行为，A1b先等待此前置闭环。

| 放置项 | Root裁决 |
|---|---|
| Owner/当前事实 | kokoro-storage uploads唯一业务writer；839c9a9基线clean，已验收Nest/Prisma/424+compiled2。生产Complete/Abort两处key-only清理，deleteExact当前仅final，其他owner不动 |
| 目标职责 | 已确认业务事务后的best-effort staging精确清理，保持已提交receipt/业务返回与原取消语义，不产生无VersionId marker；不建设完整staging历史GC |
| 目录比较/粒度 | 采用现uploads.service.ts编排+现object-store adapter/validation能力；淘汰新staging-cleanup模块/进程，因为无新业务身份、事实owner或状态机。预计仅现文件局部改动，不新增目录/通用helper框架 |
| 依赖 | 复用ObjectReference/deleteExact；内部删除key输入域只扩为合法uploads或final，不接受任意目录。promote/download final守卫不动，retirement store的tenant/final、snapshot和所有current引用复查不动 |
| 数据/API | 无Prisma schema/SQL/Proto/generated/公开API变化。Complete使用已扫描source，不另HEAD借用后来版本ETag；Abort在已提交abort后有界HEAD并以此次观察identity条件删。原signal贯穿；清理missing/auth/412/timeout保留对象，不回滚或改写receipt；重放不重复清理 |
| 版本决定 | 新staging清理只有观察到非空且非字符串null VersionId才执行，必须VersionId+原ETag/IfMatch。缺版本时保留，非版本bucket仍可Complete/Abort但不宣称完成此清理；不添加bucket状态推断/假版本。既有final retirement nullable-version删除协议不顺带改变 |
| 有界性 | 复用现请求生命周期，staging清理设置最多10秒操作signal，Abort HEAD+DELETE共享预算，不调整Complete300秒；及时取消SDK且finally清timer。未合作底层仍由真实在途/原deadline-drain承担，不用丢弃promise伪称工作已结束 |
| 删除项 | 替换生产Complete/Abort key-only调用；当前三smoke仍使用AwsSdk.delete，A1b负责同步移除其旧调用再清理无用途生产方法，不抢改未授权消费者。Local的测试损坏模拟delete保留明确测试职责 |
| 验证 | 新回归RED旧key-only/拒绝staging exact；SDK精确VersionId+IfMatch、未知版本零DELETE、覆盖竞态保留新对象、原signal/失败cause、退休staging拒绝、真实Prisma完成/abort/receipt重放/取消；主树完整format/lint/typecheck/test/build/apply/validate/compiled/双生成保护 |

| 项 | S0-D文档任务卡（当前仅放行文档） |
|---|---|
| Agent/基线 | storage_implementation(gpt-6-astra)唯一writer；/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-storage，codex/production-closure-docs，839c9a9f7fa575435ab6934aceb6f1adf22e550d，clean；Root审查/提交 |
| 允许 | docs/TECHNICAL_DESIGN.md、API_CONTRACT.md、DATA_MODEL.md、ADR/0004-isolated-provider-qualification.md、CURRENT.md、RUNBOOK.md、ACCEPTANCE.md；只此设计及已接收A1a状态。不新建ADR/文档 |
| 后继预计实现范围 | src/uploads/uploads.service.ts；integrations/object-store/{object-store.types.ts,validation.ts,aws-sdk.ts,local.ts}；test/unit/object-store.test.ts；test/integration/{prisma-command-lifecycle.test.ts,object-retirement.test.ts}，共8原文件。尚未授权写源码/测试 |
| 排除/交付 | 不写其余文件、Schema/Proto/generated/package/lock/CI/Docker/其他owner；不安装/DB/服务/provider/Git。文档format/diff、Prisma validate、contract保护检查，给三设计绝对路径/未决/当前SHA和精确manifest，停写后Root审查再放行S0-I |

A1b-R其余只读交付已保留：未来storage-roundtrip、smoke-storage-metadata、smoke-runtime及对应unit/真实Prisma integration、Python标准库生成固定有效research-package.zip；成功canonical proof核对完整scope/receipt semantic fingerprint/clean关系并实际HEAD/GET，不用于上传旁路；public亲设hold释放与严格登记的资格负例写入后继才授权。Root未放行这些文件写入，B/H0仍另片。


S0-D固定质量复查任务：storage_data_review只读839c9a9基线+7M manifest 3dcae37ca32c30baf11509004175c9d1cd607e37f127622c6a6c5d88d6575917；核对三设计/ADR与上述Root裁决、当前源码边界，不写/安装/生成/测试/DB/服务/Git。Root已独立七文档format/Prisma validate/contract/diff及251范围外hash通过，日志 /var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-storage-root-s0-design.sy5ybfug；该结果不证明S0已实现。质量结论绑定manifest，Root收结论后按路径提交再派S0-I。


### S0-D已验收 / ST-V2-S0-I实施放行

S0-D提交 `7735511c66d7ac1f92fef57796d4869f4ed3b8dc`，7M逐原始/staged/committed hash和路径核验、提交后clean；Root三设计符合性及storage_data_review独立设计质量无P0/P1/P2。Root七文档format/Prisma validate/contract/diff及251范围外hash不变通过，未连DB；实施/真实provider尚未计绿。

| 项 | ST-V2-S0-I任务卡 |
|---|---|
| 任务/owner | P1；uploads在事务提交后按确认的staging版本条件清理，解除A1b正常marker前置；不改其他owner |
| Agent/基线 | storage_implementation(gpt-6-astra)唯一Storage writer，Root审查/主树复验/Git，后继storage_data_review只读质量；/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-storage，codex/production-closure-docs，7735511c66d7ac1f92fef57796d4869f4ed3b8dc，clean |
| 允许代码 | 仅8现有文件：src/uploads/uploads.service.ts；src/integrations/object-store/object-store.types.ts、validation.ts、aws-sdk.ts、local.ts；test/unit/object-store.test.ts；test/integration/prisma-command-lifecycle.test.ts、object-retirement.test.ts |
| 文档 | S0-D七文档仅当前实施/实际证据及必要解释。新普通文件或其他测试确实需改先报告；不机械修改所有文件，不新模块/表/框架 |
| 固定行为 | 完整沿S0-D三设计/ADR。合法uploads|final exact域；staging adapter也拒绝缺/空/字符串null版本，不只依赖调用者自律；source原ETag+VersionId，final可选version协议保留。Complete scan source，无新HEAD；Abort提交后HEAD+DELETE共享10秒原signal组合预算，finally清timer；真实pending/原deadline-drain不丢 |
| 事务/重放 | 网络不进入数据库事务；提交前失败零清理；事务成功后的missing/auth/412/cleanup timeout不改变receipt和正常返回，原request取消仍传播。同command receipt重放和新command观察到已完成/aborted的replayed结果均不再次清理 |
| 保护/删除 | promoter/download final guard、retirement tenant/final+全snapshot+current引用、Schema/Proto/generated/依赖/lease/业务事务不动。删除两处生产key-only调用；旧smoke调用及AwsSdk剩余方法A1b再闭环，Local损坏模拟delete保留 |
| 禁止 | A1b fixtures/三smoke/zip/runtime接线、scripts/CI/Docker/compose/package/lock、新依赖、其余src、其他owner；不访问外部S3/ClamAV/云/Docker，不重启共享PG/Redis |
| 验证/交付 | 先RED旧实现，GREEN SDK请求真实命令+Local及真实新库Prisma事务/receipt/覆盖/版本缺失/取消/共享预算回归；完整format/typed/typecheck/build/defaultparallel424+新增、compiled2、官方亲建空库apply/catalog/drift、validate/contract→generate→contract及保护hash；复用PG/Redis，只清亲建资源。固定manifest+RED/GREEN/全部日志停写，无Git写入，Root独立审查复验后精确提交 |

不把S0称为完整staging历史GC，无版本bucket业务可继续但staging保留；A1b/B/H0与真实provider仍待后继。


### S0-I已验收 / A1b1与B运行生命周期分界

- Storage提交 `a07b4d47266ae35b6cc35749974d83d51a417aa4`，15M逐基线/当前/staged/committed SHA256与路径核验、提交后clean。Root符合性与storage_data_review独立质量无P0/P1/P2。
- Root `/var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-storage-root-s0-i.ynr1vq42` 实跑format/lint/typecheck/build、audit443依赖0、官方亲建新库apply、默认并行65文件463/463无skip、compiled2/2、validate/contract→Prisma generate→contract/diff与全部15hash及243范围外tracked不变；亲建库已DROP。S0不会按key删除production staging；无版本bucket仍可提交但staging保留，未建设历史GC。
- 后继只读核对发现原A1b三smoke同片存在运行生命周期耦合：capability可持有plainNode child句柄、s3可直接持有fixture；production-runtime仅有B容器URL，没有本进程创建/停止句柄。ADR要求停止实际服务/在途后才cleanup，不能靠新增任意docker-stop或跨进程journal恢复蒙混。因此拆A1b1（两消费者+共享基础）与B/production-runtime（同一owner进程持容器/provider registry/DB，普通stopAndDrain回调）；停服未知保留对象/DB并非零。禁止新建文件IPC协议或从prefix/日志恢复认领。该调整是同owner顺序，不扩服务/Schema/公开API。

| 放置项 | A1b1 Root固定决定 |
|---|---|
| Owner/当前事实 | Storage test；a07b4d4 clean，Nest/Prisma/S0生产能力已验463+compiled2。A1a登记helper只支持预先写入意图，旧capability仍TestingModule/手写ZIP，s3仍建桶/无版本cleanup；production旧SQL+SDK PUT保持已知B后继 |
| 目标职责 | 两个真实外部smoke消费者+共享原样URL链，真实Nest/plainNode及Prisma已提交metadata proof，无第二业务实现 |
| 目录比较 | 采用现test/fixtures与unit/integration；淘汰src/common与新e2e工程，测试资源/进程不是新业务owner。复用既有compiled-entry.mjs close协议，不新进程协议或框架 |
| 粒度/新文件 | storage-roundtrip.ts仅RPC/原样URL bytes；smoke-storage-metadata.ts仅同自有Prisma库短只读事务关联证明；smoke-runtime.ts仅本run亲建Node child启动/停止/退出；research-package.zip由Python标准库zipfile生成固定顺序/1980时间/权限/ZIP_STORED有效样本，不手写ZIP、不加依赖。对应unit/storage-roundtrip.test.ts、unit/smoke-runtime.test.ts、integration/smoke-storage-metadata.test.ts各有明确消费者 |
| 依赖/证明 | metadata不得用于PUT旁路：PUT始终返回URL，staging key只供写前登记。成功Complete canonical proof需tenant/owner(受信subject)/upload/create-command/asset、Complete receipt复合identity+state/fence/digest/semantic fingerprint/现codec、clean scan/purpose/blob/digest/size关联；provider持具体证明能力后再实际HEAD/GET同key/version/ETag/bytes核对登记，不接受裸字符串/事后beginWrite授权。无业务写查询复制，无Schema变更 |
| 资源 | 资格120秒/RPC420秒outer signal，Complete300秒不变；SDK小对象64KiB/10秒，cleanup60秒；先停本runNode/所有写入，后fixture conditional cleanup，客户端全关且无失败再亲建者DROP。close失败继续其他资源释放；缺配置显式非零，不skip计绿。production容器与DB生命周期在B同一owner编排闭环 |
| fixture能力 | 增加仅亲设ON可releaseLegalHold并读回OFF/inflight、已提交canonical登记、仅有durable确切意图的资格小对象SDK写入用于外部违规final覆盖负例，不放宽production put/promote守卫、不另建SDKclient。S0可能已删除staging：RPC前beginDelete，后完整列表+指定版本HEAD确认；还存在则保留登记，不抹unknown状态 |
| 删除/验证 | 删除两smoke旧建桶/default/skip/SQL CRUD/TestingModule/手写ZIP/key-only吞错cleanup；production-runtime及其AWS.delete旧消费者留B同步移除，未称全部smoke完成。RED→GREEN原URL原headers/bytes/取消/错误URL真失败、真实Prisma错scope/receipt/rollback/identity、亲建child生命周期与fixturehold，完整463+新增/compiled2/静态/schema生成保护；外部资源实际执行另列 |

| 项 | ST-V2-A1b1-D任务卡（只放行文档） |
|---|---|
| Agent/基线 | storage_implementation(gpt-6-astra)唯一Storage writer，Root三设计/审核/Git；/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-storage，codex/production-closure-docs，a07b4d47266ae35b6cc35749974d83d51a417aa4，clean |
| 写入 | 原S0七文档TECHNICAL_DESIGN/API_CONTRACT/DATA_MODEL/ADR0004/CURRENT/RUNBOOK/ACCEPTANCE；同步A1b1/B顺序、准确fixture职责与ZIP替代、已接收S0。更新旧“复用手写ZIP/三smoke同A1b”描述，不保留当前方案冲突。无新增文档 |
| 预计代码文件集 | 后继M：test/smoke/capability-package.e2e.test.ts、s3.integration.test.ts，test/fixtures/smoke-provider.ts，test/unit/smoke-provider.test.ts；A：上述4fixtures（含zip）+3unit/integration。需要额外普通文件先报告；此时均未授权写入 |
| 禁止/交付 | 全src/其余test/production-runtime/scripts/CI/compose/Docker/Schema/Proto/generated/package/lock/其他owner不动，不安装/DB/服务/provider/Git。先七文档format/Prisma validate(port1)/contract+全部保护hash/diff，固定精确manifest停写，Root收敛文档门后再放行A1b1-I |

B部署/production-runtime具体同owner执行文件/普通stopAndDrain回调由B独立任务卡确定；不要提前做B或H0。外部S3环境仍无用户回复，Docker未获重启许可；源码/本地门继续，外部资格不计通过。


A1b1-D补充实现边界已批准并写入三设计：既有provider.close增加preserveObjects选项，停服/drain未知时零hold/对象副作用、即使空registry也非零且preserveDatabase；仍释放自有句柄，第一次close模式固定，重复close不得改回默认删除。默认A1a行为不变，无新文件/协议。

固定D质量复查卡：storage_data_review只读a07b4d4基线+7M manifest 1db06c8e2dd4de38a61526c532b6745d20e2b05a400bde604374b36f09c9d77b，复核同owner生命周期、metadata具体证明能力与事务外观察、原URL/ZIP职责、保留失败和固定矩阵；只读三设计/ADR及必要源码，无写/测试/生成/安装/DB/服务/Git。Root已实跑七文档format/validate(port1)/contract/diff、251范围外hash保护，日志 /var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-storage-root-a1b1-design.l2fcb828；该证据只支持文档门。writer停写，Root收独立结论后按路径提交再派I；其他owner不动。


### ST-V2-A1b1-D 已验收 / A1b1-I 实施放行

- 文档提交 `f47801f726cc402b3bea099d237f73afeeb61586`；7M 基线/工作树/staged/committed hash 与精确路径均核验，提交后 Storage clean。Root 符合性及 storage_data_review 固定 manifest 独立质量无 P0/P1/P2。
- Root 文档门日志 `/var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-storage-root-a1b1-design.l2fcb828`：七文档 format、Prisma validate（port1，不连DB）、contract、diff、251 范围外 hash 通过。该结果不是 A1b1 实现或外部 provider 验收。

| 项 | ST-V2-A1b1-I 任务卡 |
|---|---|
| 目标/owner | P1，Storage 两个真实外部 smoke 消费者接入 Nest/plainNode + Prisma 证明 + 原样签名 URL；不复制业务写入或手工 ZIP/协议 |
| Agent/基线 | storage_implementation（gpt-6-astra）唯一 Storage writer；Root 符合性/集成验证/Git，后继 storage_data_review 只读质量。工作目录 /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-storage，codex/production-closure-docs，f47801f726cc402b3bea099d237f73afeeb61586，clean |
| 允许修改 | test/smoke/capability-package.e2e.test.ts、test/smoke/s3.integration.test.ts、test/fixtures/smoke-provider.ts、test/unit/smoke-provider.test.ts（4现有文件）；上述七设计文档仅必要当前状态/实际证据 |
| 允许新增 | test/fixtures/storage-roundtrip.ts、smoke-storage-metadata.ts、smoke-runtime.ts、research-package.zip；test/unit/storage-roundtrip.test.ts、test/unit/smoke-runtime.test.ts；test/integration/smoke-storage-metadata.test.ts（7文件） |
| 依赖/固定职责 | 完整沿已验三设计/ADR0004与上一放置表，不再发明 owner/框架/协议。roundtrip 只 RPC+原 URL/headers/bytes 和显式阶段回调；metadata 绑定亲建库 Prisma/固定 tenant+trusted subject，原 codec/schema/fingerprint 短只读事务证明；provider 持具体证明能力再事务外 HEAD/GET 登记。ZIP 用 Python 标准库固定字节，runtime 复用 compiled-entry 的 closed+exit |
| 状态/副作用 | 每次 PUT 前确切 durable 意图，Complete 前 beginDelete；S0 删除后双观察确认缺失才 confirmDeleted。成功 canonical 全关系/receipt/identity/bytes 证明，未知候选只报告；亲设 hold 才释放读回，资格 SDK 写入口只用原 client、确切本次意图、小对象、覆盖前全部版本归属，不用于上传旁路。stop/drain 未知 preserveObjects 零对象写、非零并保库，首 close 模式固定；正常 closed+exit 后 current-only cleanup |
| 验证 | 先 RED 再 GREEN：原 URL/headers/全字节/取消/错误 URL，真实 Prisma 错 scope/receipt/rollback/关联身份，亲建 child 启停/失败/drain 与 fixture close/hold/资格写入。完整 format/lint/typecheck/build/default parallel463+新增、compiled2、官方亲建空库 apply/catalog/drift、validate/contract→generate→contract 与范围外 hash；验证 ZIP CRC/内容/元数据/SHA/重生成一致。外部配置缺失显式非零并在资源初始化前失败，不 skip 计绿 |
| 排除 | 全 src、其余 test（含 production-runtime/compiled-entry/isolated-prisma）、Schema/Proto/generated、package/lock、scripts/CI/compose/Docker、其他 owner；额外普通文件或越界需要先报告归属/理由。无新依赖，无外部 S3/ClamAV/云/Docker 操作，无共享服务重启/清库/flush |
| 资源/交付 | 复用现 PG/Redis；仅亲建随机库、只按自己 CREATE 成功句柄清理，失败保留。资格120秒/RPC420秒、生产Complete300秒不改、SDK10秒/小对象64KiB、cleanup独立60秒。固定精确 manifest、RED/GREEN/完整日志、文件清单后停写；worker 不碰 Git，Root 独立审查复验后逐路径提交 |

状态：A1b1-I 进行中；B/production-runtime 生命周期、H0 HTTP 机器契约和真实外部资格仍待后继，不用两消费者接线冒充全链发布完成。
