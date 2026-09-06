# TypeScript 后端成熟工程规范

状态：正式规范，2026-09-04。

适用范围：Kokoro 的 TypeScript HTTP/RPC 服务、BFF、worker 与模块化后端。本文给出可直接落地的
TypeScript/Node.js 规范，不把 Java 包结构、教科书 DDD 或某个开源仓库的目录逐字复制过来。

本文中的“必须/禁止”属于默认合并门禁；例外必须在目标仓技术设计或 ADR 中说明收益、风险、owner 和退出条件。

阅读路径：先读 1–6 节确认取舍与目录；7 节看示例；8–10 节查类型/命名/配置；11–16 节用于 API、运行和重构评审。

## 1. 核心决策

Kokoro TypeScript 后端采用：

```text
业务模块优先（package by feature）
+ 模块内部使用熟悉的 Route/Service/Repository/Schema 角色
+ Fastify/ConnectRPC 的原生生命周期
+ Zod 边界校验
+ PostgreSQL + pg 的 SQL-first 持久化
+ TypeScript strict 与结构化类型
+ 复杂业务才引入 DDD/CQRS，不预建空层
```

明确不采用：

```text
全仓 domain/application/infrastructure/interfaces 四层目录
每个用例机械拆一个文件
每个模块建立 postgres/、redis/、prisma/ 技术目录
默认 ports/、adapters/、value-objects/、commands/、queries/
通用 BaseRepository、BaseService、command-executor、service locator
Prisma 与 pg 双轨访问同一业务数据
```

真正要稳定的是业务边界、依赖方向、事务、契约和测试，而不是让每个目录长得像架构文章。

这是一条 **Kokoro paved road**，不是宣称所有团队只能使用同一棵目录树。对 Kokoro 当前多个业务能力并存的
服务，module-first 比全仓横向分层更容易定位变更；若未来某个仓只承载一个复杂 bounded context，确有证据时
可以通过项目级 ADR 采用其他物理组织，但必须同时修订本手册和根级门禁。子仓不得用局部 ADR 单方面绕过基线；依赖、契约、
事务和测试边界仍必须等价成立。

### 1.1 本手册中的词到底指什么

| 词          | 本手册的含义                                                | 不表示                                           |
| ----------- | ----------------------------------------------------------- | ------------------------------------------------ |
| module      | 一组高内聚业务能力的代码包                                  | NestJS `@Module()`、微服务或 DDD bounded context |
| schema      | Zod 请求/响应/外部输入校验                                  | PostgreSQL schema                                |
| service     | 业务用例、授权、事务与副作用编排                            | 全能类、DI token 或空转发层                      |
| repository  | 当前模块的 PostgreSQL 数据访问组件                          | Git 仓库、ORM、抽象基类或必选 interface          |
| plugin      | 一个真正参与 Fastify 注册/封装/生命周期的对象               | 所有业务文件的包装层                             |
| runtime     | Pool、Redis client、logger、tracer 等进程级资源的创建与关闭 | 业务逻辑层                                       |
| integration | 被多模块共用的外部 owner/provider 协议适配                  | 全局 `common` 或本仓业务真源                     |
| contract    | OpenAPI/Proto/JSON Schema 等机器可校验的 wire 事实源        | DTO 大杂烩、数据库模型或跨仓拷贝中心             |

某个名词没有对应的真实职责时，就不建该文件或目录。

## 2. 为什么这才是 TS-native

成熟 TypeScript 工程通常同时具备以下特点：

1. **按业务能力聚合**：查看或修改 Site、Payment、Skill 时，主要文件在同一个模块内。
2. **使用框架原生机制**：Fastify route/plugin encapsulation、Connect handler、Node 生命周期，不自研 Java 式容器。
3. **数据对象轻量**：Zod schema 推导 wire 类型，普通 `type`/`interface` 表达数据，class 只承载真实行为和状态。
4. **依赖使用结构化类型**：消费方只声明实际用到的方法，不为每个实现创建 `IPort`/抽象基类。
5. **按复杂度展开**：小模块允许数个清晰文件；大模块按子业务继续切分，而不是按数据库品牌堆目录。

Fastify 官方把 plugin/encapsulation 作为模块化机制；TypeScript 官方和 Google 风格规范关注类型安全、导出面、
命名与可读性，都没有要求固定 DDD 文件树。大型开源 TS 后端也只能证明“高内聚模块”这一共同原则，不能证明
某一棵 `postgres/store/port` 文件树是行业标准。

## 3. Kokoro TypeScript 技术基线

| 能力               | Kokoro 默认                           | 落地规则                                                          |
| ------------------ | ------------------------------------- | ----------------------------------------------------------------- |
| Runtime            | Node.js 24 LTS                        | 本地、CI、镜像保持同一 major；镜像固定安全 patch 与 digest        |
| Package manager    | pnpm 11.25.0                          | `packageManager` 固定精确版本，只保留 `pnpm-lock.yaml`            |
| Language           | TypeScript 6.0.3                      | 当前完整 lint/build 兼容基线；ESM、NodeNext、strict               |
| HTTP               | Fastify                               | 每个业务模块注册自己的 route/plugin；schema 同时约束输入和输出    |
| RPC                | ConnectRPC + Protobuf-ES              | Proto 是 owner 的 wire contract；generated code 只在 RPC 边界使用 |
| Validation         | Zod + `fastify-type-provider-zod`     | HTTP、配置和第三方 payload 在边界解析；一个仓不混多套 validator   |
| Database           | PostgreSQL                            | 每仓唯一 `database/schema.sql`                                    |
| DB access          | `pg`（node-postgres）                 | Pool 生命周期集中管理，值使用 `$n` 参数绑定，Row 显式映射         |
| Cache/coordination | `redis`（node-redis）                 | 只承担缓存、lease、通知、stream；不成为业务真源                   |
| Test               | Vitest                                | 单元、集成、契约、架构、smoke 分层                                |
| Lint               | ESLint + typescript-eslint typed lint | `lint` 与 `typecheck` 各自真实执行，不互相冒充                    |
| Format             | Prettier                              | 只负责确定性格式；不与 ESLint 重复维护排版规则                    |

### 3.1 版本与依赖治理

- 开始每个子仓重构前，先核验 Node LTS、pnpm、TypeScript、框架和直接依赖的**最新稳定兼容版本**；预发布版不
  冒充稳定版。
- `package.json#packageManager` 固定精确 pnpm 版本，直接依赖采用仓库统一的精确版本策略，`pnpm-lock.yaml`
  必须提交；CI 使用 frozen lockfile。
- `@types/node` 跟随实际 Node runtime major，而不是无条件安装 registry 上更高 major；编译器、类型包、框架和
  provider 必须作为一个兼容矩阵验证。
- “使用最新”表示在变更时重新查询 registry、官方 release notes、安全公告和兼容矩阵，不在手册里永久写死一个
  会过期的 `latest`。
- major 升级、架构迁移和业务重构分开提交。升级先看 breaking changes 与传递依赖 diff，再跑完整门禁；不能只因
  版本号更新就宣称更先进。
- 生产依赖必须有明确 owner 和真实用途。新增 DI container、ORM、CQRS bus、mapper generator 或缓存 wrapper
  前，先证明现有框架原生能力不足。

以上版本是 2026-09-04 核验的兼容基线，不表示永久最新版。以正式 peer support、安装解析和真实 lint/build 验证为准；
本仓依赖升级记录保存精确矩阵及输出，不把过期的候选失败结论永久写成禁用规则。TypeScript 升级必须同时确认 typed lint 支持。

pnpm 依赖构建使用显式审查策略：`strictDepBuilds: true`，在 `allowBuilds` 中逐项允许必要构建，禁止
`dangerouslyAllowAllBuilds`。不以全局 `--ignore-scripts` 取代审查，也不允许未审查的 install script 自动执行。

最新稳定兼容版本还须满足本仓安全公告与发布缓冲策略（minimumReleaseAge）；新发布但尚未过观察窗口的版本不自动进入基线。
紧急安全修复需要具名审查和例外记录，不用全局关闭供应链检查。

### 3.2 `package.json` 公共入口

各仓命令名统一，具体参数可以按仓调整：

```json
{
  "private": true,
  "type": "module",
  "packageManager": "pnpm@11.25.0",
  "engines": { "node": ">=24 <25" },
  "scripts": {
    "dev": "node --watch --env-file-if-exists=.env --env-file-if-exists=.env.local --import=tsx src/server.ts",
    "format": "prettier --write .",
    "format:check": "prettier --check .",
    "lint": "eslint . --max-warnings=0",
    "typecheck": "tsc -p tsconfig.json --noEmit",
    "test": "vitest run",
    "test:integration": "vitest run --config vitest.integration.config.ts",
    "contract:check": "tsx scripts/check-contract.ts",
    "build": "tsc -p tsconfig.build.json",
    "start": "node --enable-source-maps dist/server.js",
    "db:apply-schema": "node --env-file-if-exists=.env --env-file-if-exists=.env.local --import=tsx scripts/apply-schema.ts"
  }
}
```

`lint`、`typecheck`、`test`、`build` 必须执行不同的真实工作，禁止彼此 alias 来凑门禁。`dev` 可以使用 TS
runtime；生产 `start` 只运行已经构建的 JS，不以 `tsx` 代替构建产物。

### 3.3 PostgreSQL、`pg`、Prisma、Repository 不是一回事

```text
PostgreSQL   数据库产品
pg           Node.js PostgreSQL driver
Prisma       ORM / typed database toolkit
Repository   代码中的数据访问职责或业务持久化抽象
```

Kokoro 当前大多数 TypeScript owner 已采用 PostgreSQL + `pg` + `database/schema.sql`，因此本文把它锁为统一
paved road。Prisma、Drizzle 和 Kysely 都是可用工具，但它们不自动代表更好的架构：

| 方案             | 与 Kokoro V1 的关系                                                         |
| ---------------- | --------------------------------------------------------------------------- |
| `pg`             | 直接执行 canonical SQL，不增加第二份 schema；当前选定                       |
| Kysely           | 查询构建与类型层候选；只有实际查询复杂度证明收益时再引入                    |
| Prisma / Drizzle | 通常希望自己的 schema 成为事实源，与当前唯一 `database/schema.sql` 规则冲突 |

因此，当前子仓不得自行加入 Prisma/Drizzle 或并存第二份 schema。未来若改变数据访问基线，必须先用项目级
ADR 修订 SQL 事实源规则，再整仓切换并删除旧写路径。同一业务事务永远不混用独立 ORM client 和独立
`pg.Pool`。

## 4. 仓库级目录

### 4.1 单进程 HTTP/RPC 服务

```text
contract/                       # 本仓拥有的 OpenAPI/Proto/JSON Schema；有才创建
database/
  schema.sql                    # 唯一可编辑数据库 schema
src/
  modules/                      # 业务代码主入口
    <business-module>/
  config/
    env.ts                      # 唯一 process.env 读取和校验点
  generated/                   # 有生成物时创建，只读
  app.ts                        # 构建 Fastify/Connect 应用、装配依赖；不 listen
  server.ts                     # 唯一进程入口、signal、listen、graceful shutdown
test/
  unit/
  integration/
  contract/
  architecture/
  smoke/
  fixtures/
  doubles/
```

没有真实内容的目录不创建。数据库连接池和 Redis client 在 `app.ts` 的 composition root 创建；当装配代码确实
增长时，才提取 `src/bootstrap.ts` 或 `src/bootstrap/`。不要仅为放一个 `pool.ts` 预建 `database/`、
`infrastructure/`、`postgres/`、`redis/` 四层包装。

### 4.2 运行时资源与多进程入口

单进程服务先在 `app.ts` 组装 Pool、Redis client、日志和外部 client。当这些进程级资源已经有独立创建、健康检查、
关闭顺序或共享测试时，可以提取：

```text
src/runtime/
  create-runtime.ts
  close-runtime.ts
  database.ts                  # Pool 配置/事务 helper，不放业务 SQL
  cache.ts                     # Redis 连接与生命周期，不定义业务 key
```

`runtime/` 是进程资源边界，不是新的业务层。只有一个无独立生命周期的 `pool.ts` 时仍留在 `app.ts`，不为对称性提前拆目录。

只有同仓确实构建多个独立进程时使用：

```text
src/
  entrypoints/
    http.ts
    rpc.ts
    worker.ts
  runtime/                     # 各入口共用的进程级资源
  modules/
  config/
  generated/
```

`runtime/` 只持有进程级依赖和生命周期；业务代码仍属于模块。单进程服务不提前套用这棵树。

### 4.3 `plugins/` 的使用条件

`plugins/` 只保存真正的 Fastify plugin，例如 request context、authn hook、rate limit 或 tracing 集成：

```text
src/plugins/
  request-context.plugin.ts
  authentication.plugin.ts
```

普通业务 Service、Repository、Redis key、SQL 和 provider client 不因 Fastify 存在就放进 `plugins/`。

### 4.4 跨模块共享对象放在哪里

不创建全局 `common/` 或 `utils/` 并不意味着复制代码。按“谁拥有语义”放置：

| 对象                                        | 默认位置                                            |
| ------------------------------------------- | --------------------------------------------------- |
| 只被一个业务模块使用的 client/cache/helper  | 与该模块共置                                        |
| 多个模块共用的外部 owner/provider client    | `src/integrations/<owner>/`，仅放协议适配与错误归一 |
| Pool、Redis 连接、logger、tracer 等进程资源 | `app.ts` or `src/runtime/`                          |
| Fastify hook/decorator/request context      | `src/plugins/`                                      |
| 多模块共享的业务规则                        | 先确认真实 owner；归入 owner 模块，不放 `shared/`   |
| 无业务语义且有多仓消费者的稳定工具          | 证明独立 API 和版本需求后再做 package               |

`integrations/` 也是按外部 owner 命名，例如 `integrations/iam/iam.client.ts`，而不是
`integrations/http/clients/` 这种技术套娃。它只在真实跨模块复用时存在；否则 client 仍属于具体业务模块。

## 5. 模块目录：先小而清晰，再按业务增长

模块不是一张表、一个 ORM Entity 或一个 endpoint 的目录镜像。它应该包含一组共同业务词汇、用例、权限和变更原因，可以拥有多张表和
多个对象。只有两部分已经拥有独立生命周期、权限、契约或稳定调用边界时才拆模块；若它们频繁互相 deep-import、共同事务且总是一起变更，
应先合并或重画边界，而不是再加一层 interface。

### 5.1 简单 CRUD：默认形态

System 的 Site 这类模块使用熟悉、可搜索的 role suffix，不拆成四个十几行“用例文件”，也不创建单文件
`postgres/`、`redis/`、`rpc/` 目录：

```text
src/modules/sites/
  [site.ts]                    # 被多个角色共用的稳定内部业务类型
  [site.schema.ts]             # 有 HTTP/外部输入时的 Zod schema
  [site.repository.ts]         # 本模块拥有 PostgreSQL 事实时
  [site.service.ts]            # 有授权/事务/状态/编排时
  [site.routes.ts]             # 提供 HTTP 时；本身就是 Fastify plugin
  [site.rpc.ts]                # 提供 RPC 时
  [index.ts]                   # 有跨模块消费者时的公开面
```

方括号表示按需，不是文件名。模块只创建真正需要的角色：

| 场景                               | 默认调用方向                                       |
| ---------------------------------- | -------------------------------------------------- |
| 纯读取且无业务规则                 | Route/RPC -> 注入的明确 Query/Repository           |
| 有授权、状态变化、事务、幂等或编排 | Route/RPC -> Service/use case -> Repository/Client |
| 只调用外部 owner/provider          | Route/RPC -> Service/use case -> Client            |
| 没有本仓持久化事实                 | 不创建 Repository                                  |
| Service 只原样转发                 | 删除空壳，合并至现有职责或使用明确 Query           |

规则：

- `site.service.ts` 可以包含一组高度内聚的 CRUD 方法；`service` 不是禁词。
- `site.repository.ts` 直接使用注入的 `Pool`/transaction client；因为数据库已统一，不再命名
  `pg-site-repository.ts` 或放进 `postgres/`。
- 一个 transport 文件时保留在模块根；只有出现真实的共同变更与阅读路径时才展开子目录，不按文件数自动触发。
- 被两个以上角色共享的稳定内部业务类型放在 `site.ts`；不把 Service 实现文件变成共享类型中心，也不为它创建全局 `types/`。
- `site.routes.ts` 已符合 Fastify plugin contract 时，禁止再包一层只调用 `register()` 的 `site.module.ts`。
- 只有一个模块需要组合多组 routes/hooks/dependencies 时，才增加语义明确的 `sites.plugin.ts`。
- 某个操作拥有独立授权、事务、幂等、外部依赖、失败恢复或测试生命周期时，才拆为 `use-cases/authorize-site.ts` 一类动词-对象文件。

### 5.2 中型模块：先按业务子能力展开

文件多到模块根难以扫描时，先把共同变更的业务子能力放在一起，不先切回 `routes/services/repositories` 横向分层：

```text
src/modules/projects/
  project.ts
  project.schema.ts
  project.service.ts
  project.repository.ts
  project.routes.ts
  memberships/
    membership.ts
    membership.schema.ts
    membership.service.ts
    membership.repository.ts
    membership.routes.ts
  [projects.plugin.ts]
  [index.ts]
```

`memberships/` 拥有自己的词汇、权限和变更路径，所以它比一组横向目录更好定位。只有大量同类对象确实共享生命周期时，才在某个子能力内建
`events/`、`policies/`、`mappers/` 等集合目录。即使有三个文件也可以平铺；数字只是复核信号，共同变化、owner、阅读路径和 import graph 才是拆分依据。

### 5.3 大模块：先按子业务切分

复杂的 Scheduled Tasks 不应把几十个文件都平铺，也不应先按 PostgreSQL/Redis 分组。先按业务语义拆：

```text
src/modules/scheduled-tasks/
  definitions/
    schedule.schema.ts
    schedule.service.ts
    schedule.repository.ts
  occurrences/
    occurrence.service.ts
    occurrence.repository.ts
  dispatch/
    dispatch.service.ts
    dispatch.publisher.ts
  history/
    history.query.ts
  scheduled-tasks.routes.ts
  scheduled-tasks.plugin.ts     # 需要模块级组合时创建
  index.ts
```

业务阅读路径是“定义 -> occurrence -> dispatch -> history”，而不是“先去 postgres，再猜是哪段业务”。缓存实现写成
`schedule.cache.ts`，消息发布写成 `dispatch.publisher.ts`，lease 写成 `dispatch.lease.ts`；目录按职责命名，
不按 Redis 品牌命名。

### 5.4 富领域模块

支付、账本、授权策略等确有复杂不变量时，可以在所属模块内部增加 `domain/` 和 `use-cases/`：

```text
src/modules/payments/
  domain/
    payment.ts
    payment.policy.ts
    payment.error.ts
  use-cases/
    authorize-payment.ts
    capture-payment.ts
    refund-payment.ts
  payment.repository.ts
  ledger.repository.ts
  payment.routes.ts
  payment.schema.ts
  [payments.plugin.ts]
```

这不是全仓模板。领域对象必须拥有不变量、状态迁移或策略；只有字段和 getter 的 class 不叫领域建模。
`commands/`、`queries/` 只在该模块正式采用 CQRS 且读写模型明显分离时出现。

| 形式           | 使用条件                                                                                                            |
| -------------- | ------------------------------------------------------------------------------------------------------------------- |
| 模块 Service   | 少量高内聚操作共享依赖、授权或事务策略                                                                              |
| Use case       | 某一业务操作有独立授权、事务、幂等、外部依赖、失败恢复或变更节奏                                                    |
| Domain         | 不依赖 Fastify/pg/Redis/SDK 的不变量、状态迁移和纯业务策略已经值得独立测试/复用                                     |
| Domain service | 纯领域运算无法自然归属单个业务对象；使用 `pricing.policy.ts`、`credit-decision.ts` 等业务名，不创建 `DomainService` |

Service 开始包含大量互不相关的公开方法，也是拆 Use case/子能力的信号，不需要等到已经出现巨型状态机。

### 5.5 模块命名的单复数

不机械给所有目录加 `s`。模块名使用产品统一语言中的正式业务名，不从 HTTP 路径或表名反推。Kokoro 的本地约定是：

```text
资源集合：sites/、projects/、payments/、scheduled-tasks/
能力或不可数概念：auth/、billing/、search/、model-catalog/、mcp/
职责集合（只在确有多个同类文件时）：policies/、mappers/、clients/、events/
协议/技术术语：http/、rpc/、sql/、api/（不写 https/、rpcs/、sqls/）
```

同一仓同一概念只选一种形式。不能同时出现 `site/` 与 `sites/`、`model/` 与 `models/` 两套目录来表达同一边界。
默认不创建全局或模块级 `enums/`；有限值优先使用 Zod enum、string literal union 或就近常量。只有多个独立 runtime enum 具有同一 owner 时才建集合目录。

## 6. 各角色的明确职责

### 6.1 Route / RPC handler

负责：

- 读取 path/query/header/body；
- Zod/Proto 校验；
- 从受信 middleware/context 读取 tenant、actor、request ID；
- 调用 Service/use case；
- 映射状态码、响应 envelope 和稳定错误码。

禁止：SQL、Redis 命令、业务权限决策、状态机修改、跨 provider 编排。

### 6.2 Schema

- HTTP request/response 使用 Zod 或本仓唯一 validator。
- Wire 使用 `snake_case`；进入 Service 时映射为内部 `camelCase`。
- schema 是运行时验证，不等同于 Domain Model 或数据库 Row。
- 若 OpenAPI 是机器事实源，schema 生成/一致性测试必须防止二者漂移；不得维护两份互不校验的字段定义。

### 6.3 Service

Service 是一组高度内聚的业务用例与事务编排，可以是 class、factory 或纯函数。默认职责：

- 业务授权和状态校验；
- 事务边界；
- Repository、cache、client、publisher 的调用顺序；
- 幂等、并发冲突和结果组装；
- 业务错误。

一个 Service 至少要拥有上述一项稳定责任。若全部方法只是原样转发参数和结果，不要为了三层外观创建空壳
`FooService`：可以合并进现有内聚 Service，或让简单只读 route 通过注入的窄 `*.query.ts`/Repository 能力读取。
这个例外不允许在 route 中写 SQL、事务、授权决策或多步编排；一旦出现这些职责就应收敛到 Service/use case。

禁止建立全仓 `services/` 或 `AppService`。`site.service.ts` 在 `modules/sites/` 内很清楚；根目录的
`src/services/service.ts` 才是问题。

### 6.4 Repository

Repository 在本手册中就是**模块的数据访问组件**，不是 Git repository，也不必是 DDD Repository。

默认规则：

- `site.repository.ts` 是当前唯一 `pg` 实现，负责参数化 SQL、tenant predicate、Row mapping、锁和 affected rows。
- 不默认再创建 `ISiteRepository`、`SiteRepositoryPort`、`PgSiteRepository` 三份同构代码。
- Service 若需要单元替身，在消费处声明最小结构化接口，具体 Repository 无需 `implements`。
- Aggregate 持久化、跨表锁、稳定共享语义出现后，才把 Repository 接口单独提取。
- 复杂只读 projection 使用 `*.query.ts` / `queries/`，不强迫伪装成 Repository。
- `store` 只用于 KV、session、blob、checkpoint 等真正 store 语义，不与 Repository 随意互换。

禁止：`BaseRepository<T>`、任意表名 CRUD、`findAll(filters: any)`、返回 driver Row/transaction client 给 Route。

### 6.5 Client / Cache / Publisher

- 外部 HTTP/RPC/provider 调用使用 `*.client.ts`。
- 缓存使用 `*.cache.ts`，Redis 只是实现细节。
- 事件或消息使用 `*.publisher.ts` / `*.consumer.ts`。
- lease 使用 `*.lease.ts`。
- 所有外部 I/O 明确 timeout、取消、重试条件、响应大小、错误归一和观测字段。

只有真实存在多个同类文件时，才展开 `clients/`、`caches/`、`events/`。不建立 `redis/` 业务目录。

### 6.6 默认依赖方向

```text
routes/rpc ----------> schema + service/use-case
service/use-case ----> 消费方定义的最小 dependency shape
repository ----------> pg
client --------------> 外部 SDK/HTTP/RPC generated types
cache/lease/event ---> Redis 或消息客户端

app -----------------> route + service + concrete repository/client/runtime
server --------------> config + app
```

箭头表示“左侧可以 import/调用右侧”，不是请求流程图。`app.ts`/`server.ts` 只负责装配和生命周期，不被业务模块 import。

- Route 不被 Service/Repository 反向 import。
- Service 不 import Fastify、Connect generated message、`pg`、Redis client 或 provider SDK。
- 两个以上角色共享的稳定业务类型依赖模块内中性业务文件，例如 `site.ts`；Repository 不从 Service 实现文件取共享模型。
- 有跨模块消费者时，对方模块必须通过 `index.ts` 声明唯一公开面；没有 `index.ts` 的模块视为私有，只允许 composition root 导入其装配入口。
- 跨模块不导入对方的 Repository、Row、Schema 和其他内部实现；不为打破一次类型 import 就创建全局 `types/`。

## 7. 简单模块示例：从输入到数据库

本节演示内部 HTTP 的 code-first 路径、真实授权入口和单语句写入。公开 BFF 使用第 11.2 节的 design-first 生成方向。
分页、更新、删除、幂等 receipt 等不属于本节示例，具体用例按本仓契约增加；示例不是整套服务脚手架。

### 7.1 共享的稳定内部类型

```ts
// src/modules/sites/site.ts
export type SiteActor = Readonly<{
  tenantId: string;
  actorId: string;
}>;

export type Site = Readonly<{
  id: string;
  tenantId: string;
  siteKey: string;
  displayName: string;
  createdAt: Date;
  updatedAt: Date;
  deletedAt: Date | null;
}>;

export type NewSite = Readonly<{
  id: string;
  tenantId: string;
  siteKey: string;
  displayName: string;
  now: Date;
}>;
```

`Site`/`NewSite` 同时被 Service 和 Repository 使用，因此放在中性的 `site.ts`。这不是又建一个 `models/` 层，也不放 wire DTO 或 Row。

### 7.2 Service 消费最小依赖

```ts
// src/modules/sites/site.service.ts
import type { NewSite, Site, SiteActor } from "./site.js";

export type CreateSiteInput = Readonly<{
  actor: SiteActor;
  siteKey: string;
  displayName: string;
}>;

export interface SiteServiceDependencies {
  repository: {
    insert(input: NewSite): Promise<Site>;
    findById(tenantId: string, siteId: string): Promise<Site | null>;
  };
  canCreate(actor: SiteActor): Promise<boolean>;
  newId(): string;
  now(): Date;
}

export class SiteForbiddenError extends Error {
  constructor() {
    super("site creation is not permitted");
    this.name = "SiteForbiddenError";
  }
}

export class SiteNotFoundError extends Error {
  constructor(siteId: string) {
    super(`site ${siteId} was not found`);
    this.name = "SiteNotFoundError";
  }
}

export class SiteService {
  readonly #dependencies: SiteServiceDependencies;

  constructor(dependencies: SiteServiceDependencies) {
    this.#dependencies = dependencies;
  }

  async create(input: CreateSiteInput): Promise<Site> {
    if (!(await this.#dependencies.canCreate(input.actor))) {
      throw new SiteForbiddenError();
    }
    return this.#dependencies.repository.insert({
      tenantId: input.actor.tenantId,
      siteKey: input.siteKey,
      displayName: input.displayName,
      id: this.#dependencies.newId(),
      now: this.#dependencies.now(),
    });
  }

  async get(tenantId: string, siteId: string): Promise<Site> {
    const site = await this.#dependencies.repository.findById(tenantId, siteId);
    if (site === null) throw new SiteNotFoundError(siteId);
    return site;
  }
}
```

最小依赖 shape 就近放在消费它的 Service 中；具体类只需结构匹配。这是 TypeScript structural typing，不需要
额外创建 `ports/`、`ISiteRepository` 和同构接口文件。依赖方法增长或被多个用例稳定复用后，再提取具名接口。

### 7.3 当前唯一 `pg` Repository

```ts
// src/modules/sites/site.repository.ts
import type { QueryResult, QueryResultRow } from "pg";

import type { NewSite, Site } from "./site.js";

interface Queryable {
  query<Row extends QueryResultRow>(
    text: string,
    values: unknown[],
  ): Promise<QueryResult<Row>>;
}

interface SiteRow extends QueryResultRow {
  id: string;
  tenant_id: string;
  site_key: string;
  display_name: string;
  created_at: Date;
  updated_at: Date;
  deleted_at: Date | null;
}

function toSite(row: SiteRow): Site {
  return {
    id: row.id,
    tenantId: row.tenant_id,
    siteKey: row.site_key,
    displayName: row.display_name,
    createdAt: row.created_at,
    updatedAt: row.updated_at,
    deletedAt: row.deleted_at,
  };
}

export class SiteRepository {
  readonly #db: Queryable;

  constructor(db: Queryable) {
    this.#db = db;
  }

  async findById(tenantId: string, siteId: string): Promise<Site | null> {
    const result = await this.#db.query<SiteRow>(
      `SELECT id, tenant_id, site_key, display_name,
              created_at, updated_at, deleted_at
         FROM system_site
        WHERE tenant_id = $1
          AND id = $2
          AND deleted_at IS NULL`,
      [tenantId, siteId],
    );

    const row = result.rows[0];
    return row === undefined ? null : toSite(row);
  }

  async insert(input: NewSite): Promise<Site> {
    const result = await this.#db.query<SiteRow>(
      `INSERT INTO system_site (
         id, tenant_id, site_key, display_name, created_at, updated_at
       ) VALUES ($1, $2, $3, $4, $5, $5)
       RETURNING id, tenant_id, site_key, display_name,
                 created_at, updated_at, deleted_at`,
      [input.id, input.tenantId, input.siteKey, input.displayName, input.now],
    );

    const row = result.rows[0];
    if (row === undefined) throw new Error("site insert returned no row");
    return toSite(row);
  }
}
```

SQL 就在 `site.repository.ts`；不需要 `postgres/site-store.ts`。如果该文件因复杂查询增长，再按业务拆成
`site.repository.ts` 与 `site-search.query.ts`，而不是按数据库品牌增加层级。

`query<SiteRow>()` 是静态声明，不是运行时 Row 校验。Schema drift 测试需验证列、NULL 和 driver 映射；
JSONB、外部写入数据、枚举、NUMERIC/BIGINT 等高风险字段在 mapper/parser 校验。PG bigint/numeric 默认通常返回字符串，
不要通过 `as number` 改写事实；Wire 显式选择十进制字符串或安全整数。时间转 RFC 3339，原生 `bigint` 不直接 JSON 序列化。

### 7.4 Zod Schema

```ts
// src/modules/sites/site.schema.ts
import { z } from "zod";

export const createSiteBodySchema = z.strictObject({
  site_key: z.string().min(1).max(80),
  display_name: z.string().min(1).max(200),
});

export const createSiteResponseSchema = z.object({
  data: z.object({
    site_id: z.uuid(),
    site_key: z.string(),
    display_name: z.string(),
  }),
  meta: z.object({ request_id: z.string().min(1) }),
});

export const errorResponseSchema = z.object({
  error: z.object({ code: z.string(), message: z.string() }),
  meta: z.object({ request_id: z.string() }),
});
```

### 7.5 Fastify Route

```ts
// src/modules/sites/site.routes.ts
import type { FastifyPluginCallback, FastifyRequest } from "fastify";
import type { ZodTypeProvider } from "fastify-type-provider-zod";

import {
  createSiteBodySchema,
  createSiteResponseSchema,
  errorResponseSchema,
} from "./site.schema.js";
import type { SiteService } from "./site.service.js";
import type { SiteActor } from "./site.js";

export interface SiteRoutesOptions {
  siteService: SiteService;
  getActor(request: FastifyRequest): SiteActor;
}

export const siteRoutes: FastifyPluginCallback<SiteRoutesOptions> = (
  app,
  options,
  done,
) => {
  const server = app.withTypeProvider<ZodTypeProvider>();

  server.post(
    "/v1/sites",
    {
      schema: {
        body: createSiteBodySchema,
        response: {
          201: createSiteResponseSchema,
          default: errorResponseSchema,
        },
      },
    },
    async (request, reply) => {
      const site = await options.siteService.create({
        actor: options.getActor(request),
        siteKey: request.body.site_key,
        displayName: request.body.display_name,
      });

      return reply.code(201).send({
        data: {
          site_id: site.id,
          site_key: site.siteKey,
          display_name: site.displayName,
        },
        meta: { request_id: request.id },
      });
    },
  );
  done();
};
```

### 7.6 Composition root

```ts
// src/app.ts
import { randomUUID } from "node:crypto";

import Fastify, { errorCodes } from "fastify";
import type { FastifyInstance, FastifyRequest } from "fastify";
import {
  hasZodFastifySchemaValidationErrors,
  serializerCompiler,
  validatorCompiler,
} from "fastify-type-provider-zod";
import { Pool } from "pg";

import type { AppConfig } from "./config/env.js";
import { SiteRepository } from "./modules/sites/site.repository.js";
import { siteRoutes } from "./modules/sites/site.routes.js";
import {
  SiteForbiddenError,
  SiteNotFoundError,
  SiteService,
} from "./modules/sites/site.service.js";
import type { SiteActor } from "./modules/sites/site.js";

export interface SiteSecurity {
  authenticate(request: FastifyRequest): Promise<SiteActor | null>;
  canCreate(actor: SiteActor): Promise<boolean>;
}

function configureErrorHandlers(app: FastifyInstance): void {
  app.setErrorHandler((error, request, reply) => {
    let failure = {
      status: 500,
      code: "INTERNAL_ERROR",
      message: "Internal error",
    };
    if (error instanceof SiteForbiddenError) {
      failure = {
        status: 403,
        code: "FORBIDDEN",
        message: "Permission denied",
      };
    } else if (error instanceof SiteNotFoundError) {
      failure = {
        status: 404,
        code: "SITE_NOT_FOUND",
        message: "Site not found",
      };
    } else if (
      hasZodFastifySchemaValidationErrors(error) ||
      error instanceof errorCodes.FST_ERR_CTP_INVALID_JSON_BODY ||
      error instanceof errorCodes.FST_ERR_CTP_EMPTY_JSON_BODY
    ) {
      failure = {
        status: 400,
        code: "INVALID_REQUEST",
        message: "Invalid request",
      };
    } else if (error instanceof errorCodes.FST_ERR_CTP_BODY_TOO_LARGE) {
      failure = {
        status: 413,
        code: "BODY_TOO_LARGE",
        message: "Body too large",
      };
    } else if (error instanceof errorCodes.FST_ERR_CTP_INVALID_MEDIA_TYPE) {
      failure = {
        status: 415,
        code: "UNSUPPORTED_MEDIA_TYPE",
        message: "Unsupported media type",
      };
    }
    if (failure.status === 500) {
      request.log.error({
        event: "request_failed",
        error_type: error instanceof Error ? error.name : "non_error_throw",
      });
    }
    return reply.code(failure.status).send({
      error: { code: failure.code, message: failure.message },
      meta: { request_id: request.id },
    });
  });
  app.setNotFoundHandler((request, reply) => {
    return reply.code(404).send({
      error: { code: "NOT_FOUND", message: "Resource not found" },
      meta: { request_id: request.id },
    });
  });
}

export function buildApp(config: AppConfig, security: SiteSecurity) {
  const app = Fastify({
    logger: true,
    bodyLimit: 64 * 1024,
    requestTimeout: 10_000,
    handlerTimeout: 15_000,
    connectionTimeout: 20_000,
    keepAliveTimeout: 5_000,
    trustProxy: false,
    requestIdHeader: false,
    genReqId: () => randomUUID(),
  });
  const pool = new Pool({
    connectionString: config.databaseUrl,
    max: config.databasePoolMax,
    connectionTimeoutMillis: 2_000,
    idleTimeoutMillis: 30_000,
    statement_timeout: 5_000,
    query_timeout: 6_000,
    lock_timeout: 1_000,
    idle_in_transaction_session_timeout: 5_000,
    application_name: "kokoro-site-example",
    options: "-c timezone=UTC",
  });
  pool.on("error", (error) => {
    app.log.error({ event: "database_pool_error", error_type: error.name });
  });
  const siteRepository = new SiteRepository(pool);
  const siteService = new SiteService({
    repository: siteRepository,
    canCreate: (actor) => security.canCreate(actor),
    newId: randomUUID,
    now: () => new Date(),
  });

  app.setValidatorCompiler(validatorCompiler);
  app.setSerializerCompiler(serializerCompiler);
  configureErrorHandlers(app);
  app.register((scope, _options, done) => {
    const actors = new WeakMap<FastifyRequest, SiteActor>();
    scope.addHook("onRequest", async (request, reply) => {
      const actor = await security.authenticate(request);
      if (actor === null) {
        return reply.code(401).send({
          error: {
            code: "UNAUTHENTICATED",
            message: "Authentication required",
          },
          meta: { request_id: request.id },
        });
      }
      actors.set(request, actor);
    });
    scope.register(siteRoutes, {
      siteService,
      getActor(request: FastifyRequest) {
        const actor = actors.get(request);
        if (actor === undefined)
          throw new Error("authentication context missing");
        return actor;
      },
    });
    done();
  });
  app.addHook("onClose", async () => pool.end());
  return app;
}
```

认证 hook 与 routes 处于父子 Fastify scope，不靠兄弟 plugin 自动共享 hook。示例用局部 WeakMap 保存受信上下文；
成熟仓库已有 typed request decorator 时复用既有机制，不再建第二套。`security.authenticate` 必须真实验证凭证和 tenant 绑定；
`canCreate` 由 owner 的权限策略实现，测试替身只在 `test/doubles/`。

示例时间预算仅用于说明配置位置，不是全业务统一数值。生产 TLS、完整错误映射、取消、连接预算、health/drain 和脱敏诊断按第 11–13 节落实。
`app.ts` 不 listen；`server.ts` 读取配置、装配真实 security、监听和处理退出。单条 INSERT 本身原子，多步写入使用第 12.1 节事务能力。

## 8. 类型设计

### 8.1 `tsconfig` 基线

```json
{
  "compilerOptions": {
    "target": "ES2024",
    "lib": ["ES2024"],
    "types": ["node"],
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noImplicitOverride": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "useUnknownInCatchVariables": true,
    "forceConsistentCasingInFileNames": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmitOnError": true,
    "skipLibCheck": false,
    "verbatimModuleSyntax": true,
    "module": "NodeNext",
    "moduleResolution": "NodeNext"
  }
}
```

`noUnusedLocals`/`noUnusedParameters` 可由 TypeScript 或 ESLint 负责，但只能有一个明确 owner，CI 必须阻断。

### 8.2 构造选择

| 构造                 | 默认用途                                         |
| -------------------- | ------------------------------------------------ |
| `type`               | union、schema inference、只读数据、函数签名      |
| `interface`          | 对象能力、依赖 shape、框架 declaration merging   |
| `class`              | 需封装依赖、状态、不变量或生命周期的对象         |
| discriminated union  | 每种状态携带不同 payload 的有限状态机            |
| string literal union | 简单有限值集合                                   |
| `enum`               | generated protocol 或确需 runtime enum object 时 |

规则：

- 外部值从 `unknown` 开始，经 Zod/协议 parser 后进入业务代码。
- 禁止宽泛 `any`、双重断言和非空断言掩盖边界问题。
- 使用 `satisfies` 验证结构；`as const` 可用于字面量收窄。
- `IUserRepository`、`IPaymentService` 这类 `I` 前缀不使用。
- ID 极易混淆时可使用轻量 branded type；不为每个 string 创建 Value Object class。
- Wire DTO、Service input、Domain Model、DB Row 在语义或生命周期不同时分开；完全同语义的内部只读类型不复制五份。
- Service 可以是函数、factory object 或 class。只有封装依赖/状态/生命周期能提高可读性，或框架 DI 真有要求时才使用 class；class 不是“更企业级”的标志。

### 8.3 导出面与类型复杂度

- 默认使用 named export；不使用 default export，让符号拥有稳定可搜索名称。
- 只导出真实消费者需要的符号；内部 helper、Row 和 mapper 保持文件私有。
- 优先直接、可读的类型；避免跨文件叠加深层 conditional/mapped type。少量重复通常比难以调试的类型体操便宜。
- `@ts-ignore`、`@ts-nocheck` 禁止；确需证明编译期失败的测试可局部使用带错误码/原因的
  `@ts-expect-error`。
- 不因“一 class 一文件”而拆散只服务于一个实现的私有类型，也不把多个独立业务对象堆进 `models.ts`。

### 8.4 一个手写 TypeScript 文件只承载一个主要变化原因

“按模块聚合”不等于“把模块里所有东西塞进一个文件”。一个模块可以高内聚，但同一个手写文件仍然必须有一个
清晰的主要职责和变化原因。以下组合默认视为设计问题：

```text
同一文件同时包含：
  wire schema / DTO 类型
  业务常量或协议版本
  domain model class
  Error class / 错误码
  crypto、序列化、解析 helper
  Service 用例编排
```

允许同文件共存的前提是它们都是同一个实现的私有细节，例如一个小型纯函数可以和只被它调用的私有类型、私有常量
放在一起。只要其中任一部分拥有独立的消费者、测试生命周期、发布协议或变化原因，就必须拆成有语义的文件，而不是
按 `models.ts`、`constants.ts`、`utils.ts` 建无主人的垃圾桶。

#### 8.4.1 类型、schema、class、service 的放置规则

| 内容 | 默认位置 | 规则 |
| --- | --- | --- |
| HTTP/配置/第三方输入 schema | `<subject>.schema.ts` | Zod schema 是运行时边界；类型用 `z.infer` 推导，不再另外维护同字段 DTO class |
| Proto 输入校验 | `contract/` + transport interceptor | 使用 Proto/Protovalidate 的唯一事实源；不得为同一 RPC 再复制一套 Zod schema |
| 稳定内部数据形状 | `<subject>.ts` 或 `<subject>.types.ts` | 用 `type`/`interface`；只有多个角色稳定共享时才导出 |
| 具有不变量/状态迁移的对象 | `<subject>.ts` 或模块内 `domain/<subject>.ts` | 使用 class 或带命名的纯函数；class 必须保护状态，不是字段容器 |
| 业务用例与事务编排 | `<subject>.service.ts` 或 `use-cases/<verb>-<subject>.ts` | 不放 schema、数据库 Row、协议 message 或底层解析实现 |
| 错误类型与错误码 | `<subject>.error.ts` | 错误语义有独立消费者时集中管理；不要在 Service 文件尾部顺手定义错误体系 |
| 持久化 | `<subject>.repository.ts` | SQL、Row 类型和 Row mapper 只服务本模块持久化；不放 HTTP/RPC 常量 |
| 协议适配 | transport 下的 handler/interceptor/mapper | 负责 wire ↔ 内部输入/错误映射，不承载业务规则 |

#### 8.4.2 常量、有限值与正则表达式

不要把“出现了 `const`”误判为必须新建文件，也不要把所有值都集中到全局常量目录：

1. 只被一个函数使用的默认值、正则或解析标记，可以保持文件私有，并紧邻其消费者。
2. 被多个文件使用且属于同一业务 owner 的值，放入 `<subject>.constants.ts`；文件名必须带 owner，禁止无主人的
   `constants.ts`、`common.ts`、`utils.ts`。
3. 协议版本、字段名、错误码和状态集合必须有明确事实源。外部协议优先从 Proto/OpenAPI/Zod schema 推导；不要再
   手写一份相同的字符串表。
4. 简单有限值优先使用 `z.enum`、`as const` 加 string literal union 或就近常量。默认不使用 TypeScript `enum`；
   只有需要真正的 runtime enum object、反向映射，或代码生成器明确要求时才使用。
5. 相同的底层谓词不得复制到多个文件。像 `typeof value === "number" && Number.isSafeInteger(value)` 这类
   结构只有在跨用例复用且拥有稳定语义时才提取为 `isNonNegativeSafeInteger` 等命名函数；提取后必须保留 owner，
   不创建无意义的 `number-utils.ts`。

#### 8.4.3 class model 的使用边界

业务 model class 至少要满足下列一项：

- 构造时校验并保持不变量；
- 通过方法执行合法状态迁移；
- 隐藏敏感状态或规范化表示；
- 拥有明确生命周期，且方法需要共享受保护状态。

只有字段、getter 和 `constructor` 的 class 不是领域模型；只有把 `type` 改成 `class` 也不会提高质量。DTO、数据库 Row、
配置对象和 Zod 推导输入默认使用结构化类型。Service 可以是纯函数、factory 或 class，依据依赖和生命周期选择，
不因为“大厂”三个字机械增加 class。

#### 8.4.4 具体反例与重构信号

当一个文件同时出现“导出多个业务类型 + 一组协议常量 + Error class + 多个 parser + 一个公开 Service 函数”时，
它已经跨越多个变化原因，即使未超过行数阈值也必须重构。重构顺序是：先识别 owner 和调用图，再拆类型/常量/错误/纯解析
与业务编排；最后由 transport 或 composition root 装配。不能通过把同一批内容机械搬到 `domain/`、`application/`、
`infrastructure/` 来制造分层。

### 8.5 ESLint typed lint 基线

typescript-eslint 使用 type-aware 配置（当前推荐 `projectService`），至少阻断：

```text
显式 any 与不安全 assignment/call/member access/return
floating promise 与错误的 async callback
Promise 误用、非 Error throw、未穷尽的状态 switch
业务层受限 import、模块 deep import、生产代码 console/debugger
无规则名或无原因的 eslint-disable
```

Lint 处理语义风险，Prettier 处理排版；不在两者中配置相互冲突的缩进、引号和换行规则。生成目录使用单独 override，
不能为了第三方类型问题关闭整个仓的 typed lint。

## 9. 文件与目录命名

### 9.1 固定形式

| 对象                 | 形式                       | 示例                            |
| -------------------- | -------------------------- | ------------------------------- |
| 文件和目录           | `kebab-case`               | `scheduled-tasks/`              |
| 中性业务文件         | `<subject>.ts`             | `site.ts`                       |
| 角色文件             | `<subject>.<role>.ts`      | `site.service.ts`               |
| class/type/interface | `PascalCase`               | `SiteService`, `SiteRepository` |
| function/variable    | `camelCase`                | `createSite`, `tenantId`        |
| test                 | `<subject>.<role>.test.ts` | `site.service.test.ts`          |

常用 role suffix：

```text
.routes.ts
.rpc.ts
.schema.ts
.service.ts
.repository.ts
.query.ts
.mapper.ts
.client.ts
.cache.ts
.publisher.ts
.consumer.ts
.lease.ts
.worker.ts
.job.ts
.plugin.ts
.policy.ts
.error.ts
```

命名语法固定为：

- 连字符连接业务词：`scheduled-task`；点号分隔文件角色：`scheduled-task.repository.ts`。
- `use-cases/` 已经表达角色，文件直接使用动词-对象：`authorize-payment.ts`，不写 `authorize-payment.use-case.ts`。
- `domain/` 内的核心对象使用 `payment.ts`；其他角色仍显式使用 `payment.policy.ts`、`payment.error.ts`。
- `*.query.ts` 表示优化的只读数据访问/投影；正式 CQRS 的 Query 放在 `queries/` 并使用业务操作名，两者不混用。
- RPC adapter 统一使用 `*.rpc.ts`；ConnectRPC 是当前库，不把库名写成持久文件角色。

路径已经表达上下文，不再造：

```text
postgres-command-receipt-repository.ts
capability-mcp-server-provider-client.ts
scheduled-task-command-executor.ts
replay-receipt.ts
```

幂等 receipt 通常是所属业务模块的内部机制，不默认创建名为 `command-receipts/` 的顶级业务模块。只有 Receipt
本身拥有独立生命周期、公开契约和团队 owner 时，它才可能成为模块。避免把多个机制名词串成文件名；应回到
业务动作与职责，例如 `run-replay.service.ts`、`event-replay.query.ts` 或所属 Repository 内的幂等方法。

### 9.2 `index.ts`

- 只在模块确实有跨模块公开 API 时创建。
- 显式 `export {}` / `export type {}`；禁止不加审查的 `export *`。
- 模块内部使用直接相对 import，避免通过自己的 barrel 形成循环依赖。
- 不在每个子能力或集合目录都创建 barrel。

### 9.3 ESM import

- NodeNext 相对 import 使用运行时能解析的扩展名，编译到 JS 时通常写 `.js`。
- 纯类型使用 `import type`。
- 不依赖只有 IDE/tsc 认识的 path alias；需要别名时优先 `package.json#imports`，并由 dev/test/build/start 一起验证。

### 9.4 代码粒度预算

阈值用于触发设计复核，不用于按行数机械切文件：

| 对象             |  复核信号 |               默认阻断线 |
| ---------------- | --------: | -----------------------: |
| 普通手写源码文件 | 约 400 行 |                   800 行 |
| 函数/方法        |  约 60 行 |                   100 行 |
| 圈复杂度         |        10 |                       15 |
| 嵌套深度         |      4 层 |                     5 层 |
| 模块根手写文件   |  约 12 个 | 先按子业务与共同变更复核 |

超过复核信号时先检查是否混入多个变化原因；超过阻断线必须拆分，或在 architecture exception 中登记 owner、
理由、替代方案和到期日。Generated code、静态协议表和可再生数据可以豁免，但不得混入手写业务逻辑。
表中数字只触发复核，不自动触发建目录或拆文件；最终依据始终是共同变更、owner、阅读路径和 import graph。

## 10. 环境变量与配置

### 10.1 `process.env` 与 `.env.*`

`process.env` 是 Node 读取最终进程环境的 API；`.env`、`.env.local`、`.env.test` 是本地装载来源，不是替代 API。
Node 后端不会自动继承 Next/Vite 的文件优先级，必须由启动脚本明确。

Kokoro 固定：

```text
development: .env -> .env.local -> shell/IDE environment（最高）
test:        .env.test -> .env.test.local -> test runner environment（最高）
production:  只读真实 process environment / secret manager，不加载仓库 env 文件
```

| 文件                | 是否提交 | 用途                           |
| ------------------- | -------- | ------------------------------ |
| `.env.example`      | 是       | 完整键名、无 secret 示例、说明 |
| `.env`              | 否       | 本机基础开发值                 |
| `.env.local`        | 否       | 本机覆盖与 secret              |
| `.env.test.example` | 是       | 测试键和确定性假值说明         |
| `.env.test`         | 默认否   | 本机测试值                     |
| `.env.test.local`   | 否       | 本机测试覆盖                   |
| `.env.production`   | 否       | 生产不从仓库文件加载           |

Node LTS 可用 `--env-file` / `--env-file-if-exists` 显式加载多个文件；已有 shell 环境优先级必须有测试。不要同时
叠加 Node env loader、dotenv、框架 loader 三套机制。

第 3.2 节的 `dev` 与 `db:apply-schema` 命令已明确按 `.env` -> `.env.local` 加载。测试仓要在 Vitest 配置或 Node
启动命令中只选一处实现 `.env.test` -> `.env.test.local`，并用一个配置优先级测试锁定行为；不依赖开发者 IDE
“刚好注入了”某些值。

### 10.2 唯一读取点

除 `src/config/env.ts` 外，生产源码禁止读取 `process.env`：

```ts
import { z } from "zod";

const environmentSchema = z.object({
  APP_ENV: z.enum(["development", "test", "production"]),
  PORT: z.coerce.number().int().min(1).max(65_535),
  DATABASE_URL: z.url({ protocol: /^(postgres|postgresql)$/ }),
  DATABASE_POOL_MAX: z.coerce.number().int().min(1).max(100),
  REDIS_URL: z.url({ protocol: /^rediss?$/ }).optional(),
});

export type AppConfig = Readonly<{
  environment: "development" | "test" | "production";
  port: number;
  databaseUrl: string;
  databasePoolMax: number;
  redisUrl?: string;
}>;

export function loadConfig(source: NodeJS.ProcessEnv = process.env): AppConfig {
  const env = environmentSchema.parse(source);
  return Object.freeze({
    environment: env.APP_ENV,
    port: env.PORT,
    databaseUrl: env.DATABASE_URL,
    databasePoolMax: env.DATABASE_POOL_MAX,
    ...(env.REDIS_URL === undefined ? {} : { redisUrl: env.REDIS_URL }),
  });
}
```

启动时一次校验并 fail fast；业务模块只接收需要的 typed config，不接收整个环境对象。Secret 无真实默认值、
不写日志、不进入错误响应。

## 11. API、RPC 与框架边界

### 11.1 Fastify

- `app.ts` 创建可供 `fastify.inject()` 测试的应用；`server.ts` 才监听端口。
- route 模块使用 Fastify plugin encapsulation；依赖通过 plugin options 或窄 typed decorator 注入。
- 不把万能 container 挂到 Fastify instance。
- request 和 response 都有 runtime schema；认证 hook 与业务授权分开。
- request cancellation、body limit、response serialization 和 error handler 显式配置。
- 使用 Zod 时配置唯一 Fastify type provider/validator/serializer；禁止 route 内手动 `parse()` 一次、框架 schema
  再维护一次。

### 11.2 Contract 事实源

每个仓只能选择一种字段级事实源方向：

```text
BFF public HTTP：contract/openapi 是可编辑事实源 -> 生成/校验 route types 与文档
内部 RPC：contract/proto 是可编辑事实源 -> 生成 Connect types
仅内部 Fastify HTTP（若存在）：Zod route schema 是可编辑事实源 -> 生成 OpenAPI artifact
```

不得同时手改 OpenAPI、Zod 和 TypeScript DTO 三份同字段定义。生成链必须在实现前通过小型验证：请求/响应、required/optional、nullable、enum、错误状态均可表达。
字段重复手写加一致性测试仍是双源，不作为落地终态；若生成工具覆盖不足，先在 API 技术设计选择可用方向，再写业务。

每个 operationId 稳定唯一；成功与错误状态显式定义，生成输出固定路径、记录来源并通过 drift/breaking 检查。
内部 code-first OpenAPI 必须只读，生成插件在 routes 前注册，`app.ready()` 后导出。SSE/AG-UI、文件下载与 204 无正文
响应使用各自协议，不机械套 JSON envelope。

### 11.3 ConnectRPC

仓库必须在技术方案中选择一种明确拓扑：

```text
单进程默认：Fastify + @connectrpc/connect-fastify，共用端口和生命周期
单进程双 listener：两个 Fastify 实例区分 HTTP/RPC 监听，共享唯一 runtime 和业务 Service
独立进程：entrypoints/http.ts + entrypoints/rpc.ts，复用 runtime 构造逻辑与业务代码，各进程拥有自己的资源
```

双 listener 只在已有调用地址、运维/网络隔离或明确协议需求下采用，并记录理由；使用 Fastify 不要求合并端口。
一个实例只调用一次 `listen()`；双实例不重复创建 Pool、Redis、JWT 或 worker，由共同生命周期协调部分启动失败、
draining 和关闭顺序。独立进程不共享内存中的连接池，也不因目录对称性额外拆进程。

Generated Proto 类型只在 `*.rpc.ts` 和 mapper 中出现，不传入 Service/Domain。deadline、cancellation、
metadata、service identity 与错误码必须向下传播。

### 11.4 DTO

使用 Zod 时 DTO 通常由 schema 推导，不创建空 class：

```ts
export const createSiteBodySchema = z.strictObject({
  site_key: z.string().min(1).max(80),
});
export type CreateSiteBody = z.infer<typeof createSiteBodySchema>;
```

只有整个仓采用 NestJS + class-validator 且 class metadata 真有价值时使用 class DTO。不要同时混 Nest controller、
裸 Fastify routes 和自研 decorator/DI。

## 12. 事务、缓存、错误与可靠性

### 12.1 事务边界如何注入

多步写入由 Service/use case 决定事务边界，但不接触 `pg.PoolClient`。在消费处定义模块专用 callback shape：

```ts
interface RenameSiteDependencies {
  inTransaction<T>(
    work: (records: {
      rename(tenantId: string, siteId: string, name: string): Promise<void>;
      appendEvent(siteId: string): Promise<void>;
    }) => Promise<T>,
  ): Promise<T>;
}
```

具体装配只在需要事务时获取 client，在 callback 内构造绑定**同一 client** 的 Repository/Outbox 能力，再注入上述接口。
不创建全局 `ports/`、泛型 UnitOfWork 框架或每个 Repository 各自开事务。实现必须满足：

1. 同一 client 上 `BEGIN -> callback -> COMMIT`；出错时尝试 `ROLLBACK`，`finally` 释放。
2. 回滚失败、连接协议失效或提交结果未知时销毁连接，保留原始 cause；未知提交结果先按幂等身份查询，不盲重试。
3. client 和事务绑定对象不逃逸 callback；默认不嵌套事务，确需时显式 savepoint。
4. `40001`/`40P01` 仅在完整操作可安全重试时，有限次重试整个事务并加入 jitter；不只重试最后一条 SQL。
5. 事务内不等待外部 HTTP/RPC/provider。需要可靠发布时，业务事实和 outbox row 同事务写入，dispatcher 在提交后投递。
   可丢的诊断或可重建缓存不机械使用 outbox。

### 12.2 PostgreSQL 连接与数据边界

- 每个进程通常一个有上限的 Pool；最大副本数 × pool.max 加其他连接及运维保留必须低于数据库预算。
- 连接/排队等待、SQL、锁等待、idle transaction 都有上限；`Promise.race` 仅停止等待，不代表服务端 SQL 已取消。
- `pg` 的 `query_timeout` 与服务端 `statement_timeout` 分别验证；没有验证过的驱动取消 API，不宣称支持 AbortSignal。
- 每个新连接用 role 配置/启动 options 或已验证的初始化 API 设置 UTC，不在任意一次 `pool.query('SET ...')` 后假设全池生效。
- 监听 idle client error，记录脱敏错误分类、连接状态和 pool saturation；观察 total/idle/waiting 与等待耗时。
- 生产 TLS 校验证书/主机名，不把 `rejectUnauthorized: false` 当默认；连接串与 TLS 配置冲突需有启动测试。

### 12.3 Redis 按语义治理

默认采用 Redis 官方推荐的 node-redis（npm `redis`）。单仓固定一种主要 client；更换前独立验证连接、重连、关闭和命令行为。

- 普通命令、Pub/Sub 订阅、阻塞 Streams 消费分离连接；这是连接用途，不是新建多个 Redis 服务实例。
- 必须监听 error，设置 connect/command deadline、重连退避与 jitter；非幂等命令和 lease 不默认离线排队。
  关闭 offline queue 也不证明上次写入未成功，仍按操作身份处理未知结果。
- cache 定义 tenant/key version、TTL、最大值、失效与回源并发控制；丢失后重建，不损坏 PostgreSQL 权威事实。
- Pub/Sub 只承载可丢通知。Streams 明确 ACK、pending reclaim、毒消息、保留和幂等消费，不承诺天然 exactly-once。
- lease 若保护权威写入，使用 fencing/原子条件写等防止过期持有者继续提交；仅重复计算的 cache rebuild 不机械加 fencing。
- Redis 失败是 fail-closed 还是可降级，由能力声明；权限、配额、幂等不因“缓存失败”自动放行。

### 12.4 错误与 I/O 预算

根级 `setErrorHandler`、`setNotFoundHandler` 统一格式；只对白名单错误公开固定 code/message，不按任意异常的
`statusCode` 或 `message` 原样输出。各仓为真实使用的情况配置：400 输入、401 未认证、403 未授权、404 不存在、
409 业务冲突、412 条件写失败、413 过大、415 介质、429 限流、500 内部错误、503 依赖不可用、504 上游超时。
PG 按 SQLSTATE + 已知约束名映射，不解析自然语言报错；未知异常只在边界记录一次脱敏 cause。

HTTP body、请求接收、handler 执行、连接空闲、代理与下游 I/O 分别配置预算；流式接口另设空闲/总体策略。
`requestTimeout` 不等于业务执行期限。只接受配置的受信代理，request ID 自生成或校验可信来源；鉴权与速率限制先于昂贵工作。
取消沿调用链传播到支持的 client；对无法撤销的写入以幂等身份查询结果。HTTP client 限制重定向、响应大小和并发，防止意外访问内部地址。

### 12.5 可观测性、健康与退出

- Fastify/Pino 日志包含 service、operation、request_id、trace_id、result、duration_ms；禁止 secret、连接串及完整敏感 payload。
- 优先框架/pg/HTTP 自动 instrumentation；仅为有业务意义的用例加 span，不为每个转发方法制造重复瀑布。高基数 ID 不作 metric label。
- `/livez` 不依赖外部服务；`/readyz` 检查启动完成、schema 匹配、draining 与关键依赖，探测有短超时和频率上限。
- 退出只触发一次：设为 draining、readiness 503 -> 停止 worker 接新任务 -> `app.close()` -> 关闭/排空长连接与在途工作 ->
  `onClose` 逆序释放 client/Pool。信号处理设置总体截止时间，超时记录未完成项并非零退出。
- SSE/AG-UI 关闭前保留可恢复 cursor；lease/task 清理不能依赖进程一定有机会运行 finally，重启仍从持久事实恢复。

## 13. 测试策略

| 层次         | 验证内容                                    | 默认方式                                       |
| ------------ | ------------------------------------------- | ---------------------------------------------- |
| unit         | Service、policy、状态机分支                 | Vitest + 局部 object/function double           |
| integration  | `pg` SQL、事务、锁、Redis、provider adapter | 真实共享 PostgreSQL/Redis，测试数据隔离        |
| contract     | OpenAPI/Proto、producer/consumer、breaking  | schema lint、generated drift、handler contract |
| architecture | import、模块公开面、env/ORM/SQL 泄漏        | ESLint boundary rule + 专用测试                |
| smoke        | build 后启动、health/ready、最小请求        | 真实进程，不使用 fake app                      |

规则：

- Fake/Fixture/InMemory 只在 `test/fixtures/`、`test/doubles/`。
- 简单 CRUD 的价值主要来自真实 PostgreSQL integration test，不为了 mock 而再造四层接口。
- tenant 越权、唯一冲突、乐观锁、重复命令、事务回滚和 Redis 故障必须覆盖。
- Fastify route 先用 `inject()`，真正 socket/TLS/代理行为由 smoke/e2e 覆盖。
- 每个测试 run/worker 使用独立数据库或 schema、Redis key prefix；只清理自身资源，禁止共享实例 `FLUSHALL`。
- schema 从空库安装；并发锁测试使用多个独立 client，不全部包在同一个 rollback transaction 中。
- 按本仓能力补测 auth scope、伪造 tenant、错误脱敏、超时/断连、pool 饱和、回滚/未知提交、Redis 重连和 Streams reclaim。
- integration/contract/architecture/smoke 的执行入口与 CI job 明确列出；若 `pnpm test` 未聚合其中某类，独立命令必须执行，
  不以一项绿色 unit test 替代整个测试矩阵。

## 14. 架构门禁

每个 TypeScript 服务至少运行：

```bash
pnpm install --frozen-lockfile
pnpm format:check
pnpm lint
pnpm typecheck
pnpm test
pnpm build
pnpm db:apply-schema        # 数据 owner
```

CI 阻断：

1. 顶层 `domain/application/infrastructure/interfaces/ports/adapters` 或
   `controllers/services/repositories/models/dtos/utils` 重新成为横向重复实现树；
2. route/connect handler 直接执行 SQL 或 Redis 命令；
3. Service/domain import Fastify、Connect generated message 或全局 `process.env`；
4. 模块 A deep-import 模块 B 的内部文件；
5. `src/` 中出现 Fake/Fixture/InMemory；
6. `any`、双重断言、非空断言掩盖输入和空值设计；
7. 同仓出现 Prisma + `pg` 双写、两个 canonical schema 或兼容 fallback；
8. 每个业务模块机械生成 `postgres/`、`redis/`、`ports/` 或空目录；
9. 新增 `command-executor`、`BaseRepository`、万能 Service 或无 owner 的 `common/utils/types`；
10. 违反 SQL、API、tenant、时间和可靠性专项手册。
11. public OpenAPI、Proto、Zod/DTO 出现两个以上可编辑字段事实源。
12. 新建无用途 wrapper/plugin/module 文件，或仅为了“看起来分层”转发一次调用。

门禁检查依赖事实，不要求每个模块必须包含某个目录；空目录和 README-only 层同样不合格。
根级静态审计是预检，不替代执行证据；AST import 检查、typed ESLint、真实 contract/integration/smoke 由子仓 CI 落实。
必须用违规样本测试门禁（如 Service import pg、空 lint 命令、跨模块内部 import），而不只搜索配置中出现了关键字。

## 15. 创建目录或文件前的设计门

Agent 新建文件/目录或调整边界前输出简短放置表；既定方案引用即可。现有文件内不改职责/契约的局部修复，仅说明 owner 与验证：

| 项         | 必须回答                                                                    |
| ---------- | --------------------------------------------------------------------------- |
| 业务 owner | 属于哪个仓和哪个业务模块                                                    |
| 当前结构   | 相邻代码和框架原生模式是什么                                                |
| 职责       | Route、Schema、Service、Repository、Client、Cache、Event 或 Domain 中哪一种 |
| 放置理由   | 为什么放这里，为什么现有文件不能承载                                        |
| 展开条件   | 为什么需要新目录而不只是新文件；目录内是否至少有持续存在的一组职责          |
| 依赖方向   | 它可以 import 什么，谁可以 import 它                                        |
| 数据/契约  | 是否影响 schema、API、事务、tenant、幂等或 generated code                   |
| 替代方案   | 至少比较“复用现有模块 / 新文件 / 新子模块”，说明淘汰理由                    |
| 验证       | 哪些 unit/integration/contract/architecture 命令证明正确                    |

特别规则：

- 新顶层目录、新业务模块、跨仓 owner 或运行进程必须有技术设计/ADR；普通文件无需 ADR，但仍需完成放置判断。
- 不从模板批量生成空目录。
- 不因为用到 PostgreSQL/Redis 就创建同名业务目录。
- 不因为一个方法叫 command 就创建 command bus/CQRS。
- 无法用一句业务语言解释文件名时，先重新划分职责再写代码。

## 16. 重构执行顺序

一次只处理一个子仓、一个可验证业务切片：

1. 盘点当前实现与门禁，记录真实失败，不把历史绿色结果当基线；
2. 先完成 AGENTS 规定的技术方案、API、数据设计门；保留行为补 characterization test，批准变更写新契约断言；
3. 明确目标模块、依赖与公开入口，再按完整业务切片替换 Route/Service/Repository，而非全仓逐层移动；
4. Redis/client 与复杂规则回归真实 owner；只在有价值时增加 domain/use-cases；
5. 切片通过目标行为测试后删除旧路径、重复实现、alias 和 fallback，再加入防回流检查；
6. 执行格式、lint、typecheck、unit、integration、contract、architecture、build、schema、smoke；
7. 一次只处理一个子仓；每个 commit 一个逻辑切片，依赖升级单独提交。未通过项保持显式，不通过放宽门禁归零。

## 17. 参考依据

- [Fastify plugin guide](https://fastify.dev/docs/latest/Guides/Plugins-Guide/)
- [Fastify type providers](https://fastify.dev/docs/latest/Reference/Type-Providers/)
- [fastify-type-provider-zod compatibility and usage](https://github.com/turkerdev/fastify-type-provider-zod)
- [Fastify encapsulation](https://fastify.dev/docs/latest/Reference/Encapsulation/)
- [Fastify testing guide](https://fastify.dev/docs/latest/Guides/Testing/)
- [ConnectRPC for JavaScript/TypeScript](https://github.com/connectrpc/connect-es)
- [TypeScript strict mode](https://www.typescriptlang.org/tsconfig/strict.html)
- [typescript-eslint typed linting](https://typescript-eslint.io/getting-started/typed-linting/)
- [Google TypeScript Style Guide](https://google.github.io/styleguide/tsguide.html)
- [Node.js release status](https://nodejs.org/en/about/previous-releases)
- [Node.js environment variables](https://nodejs.org/api/environment_variables.html)
- [node-postgres: Pooling](https://node-postgres.com/features/pooling)
- [node-postgres: Transactions](https://node-postgres.com/features/transactions)
- [Medusa modules](https://github.com/medusajs/medusa/tree/develop/packages/modules)
- [Novu API feature modules](https://github.com/novuhq/novu/tree/next/apps/api/src/app)
- [Backstage catalog backend](https://github.com/backstage/backstage/tree/master/plugins/catalog-backend/src)
- [Vendure core](https://github.com/vendure-ecommerce/vendure/tree/master/packages/core/src)

这些来源支持框架、类型和 feature cohesion 原则；Kokoro 的具体目录与 PostgreSQL + `pg` 选择由本文明确，
不声称任何单一开源项目就是“大厂唯一模板”。

补充运行时依据：

- [Fastify server / timeout / shutdown](https://fastify.dev/docs/latest/Reference/Server/)
- [node-postgres Pool API](https://node-postgres.com/apis/pool)
- [Redis 官方 Node client 指南](https://redis.io/docs/latest/develop/clients/nodejs/)
- [Redis client 生产注意事项](https://redis.io/docs/latest/develop/clients/nodejs/produsage/)
- [pnpm dependency build policy](https://pnpm.io/settings/build)
