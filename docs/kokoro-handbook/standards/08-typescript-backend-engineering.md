# TypeScript 后端工程手册：NestJS 原生基线与生产实践

状态：正式手册，2026-09-07 核验。本文描述可独立用于普通 TypeScript 后端的成熟实践；Kokoro 只引用它，不把项目私有取舍伪装成行业标准。

适用：以 NestJS 为主要应用框架的 TypeScript HTTP、RPC、BFF 与 worker。Web 前端、纯 SDK、一次性脚本和极小型无服务工具不机械套用应用框架。

## 阅读导航

| 需要解决的问题                                    | 查看位置                                                            |
| ------------------------------------------------- | ------------------------------------------------------------------- |
| 真实 NestJS 项目最基础的目录是什么？              | [§2 官方原生基线](#2-nestjs-官方原生基线)                           |
| `modules/`、`common/`、`shared/` 是否必须？       | [§4 仓库组织](#4-仓库级组织)                                        |
| Controller、Service、Repository、DTO 分别做什么？ | [§6 class 与职责](#6-class-与职责)                                  |
| 公开方法的入参与出参怎样设计？                    | [§6.7 入参与出参](#67-公开方法的入参与出参)                         |
| Prisma 项目是否必须再包 Repository？              | [§7 持久化](#7-prismaorm-与-repository)                             |
| 一个 `.ts` 文件为什么不该什么都放？               | [§8.4 文件职责](#84-一个手写-typescript-文件只承载一个主要变化原因) |
| 文件、目录、单复数和 import 如何命名？            | [§9 命名](#9-文件与目录命名)                                        |
| 哪些是通用实践，哪些是项目自己的决定？            | [§1 证据等级](#1-文档定位证据等级与规范语气)                        |

## 1. 文档定位、证据等级与规范语气

成熟工程不是一棵被所有公司统一采用的目录树。本文把结论分成四类，避免把个人偏好写成“顶级标准”：

| 标记             | 含义                                                               | 例子                                                   |
| ---------------- | ------------------------------------------------------------------ | ------------------------------------------------------ |
| **[Nest]**       | NestJS 官方概念、生命周期或 CLI 真实生成结果                       | Module、Controller、Provider、`nest g resource`        |
| **[TS]**         | TypeScript、Node.js 或 typescript-eslint 的语言/工具事实           | `strict`、类型擦除、ESM 解析、typed lint               |
| **[Production]** | 从公开生产项目和长期维护经验抽取的建议；有取舍，不冒充框架强制规则 | feature-first、按需 Repository、架构测试、显式错误边界 |
| **[Project]**    | 某个仓库基于业务、数据库和交付方式作出的决定                       | ORM、外键、迁移策略、API 协议、软删除、缓存一致性      |

本文中的“必须/禁止”只约束被团队采纳后的合并门；来源仍按上表区分。目录示例是职责示意，不是创建空目录的脚手架。

需要先固定六个事实：

1. **[Nest]** 官方稳定核心是 Module、Controller、Provider/Service、依赖注入和显式模块导入导出。
2. **[Nest]** 官方 CRUD generator 会生成 Module、Controller、Service、DTO、Entity 和测试，但不会替项目决定 ORM、Repository、Mapper、DDD 分层。
3. **[Production]** 中大型服务通常按 feature/business capability 聚合；`src/users/` 与 `src/modules/users/` 都可使用，`modules/` 只是可选容器。
4. **[Production]** `common/`、`shared/`、`utils/` 可以存在，但不是 Nest 保留层，也不应同时承担相同职责。
5. **[Production]** Repository、Mapper、Domain Model、CQRS 只在解决真实复杂度时增加；“文件齐全”不等于架构成熟。
6. **[Project]** 数据库、外键、schema/migration、协议、Zod/class-validator 和 ORM 选择必须由目标仓技术方案或 ADR 裁决。

## 2. NestJS 官方原生基线

### 2.1 官方 starter 与 feature module

Nest 官方 starter 的核心非常小：

```text
src/
  main.ts
  app.module.ts
  app.controller.ts
  app.controller.spec.ts
  app.service.ts
test/
  app.e2e-spec.ts
```

当应用出现业务功能时，Nest 官方 Modules 文档把相关 Controller 与 Service 放进同一个 feature module。官方
`nest g resource users` 进一步生成接近下面的结构：

```text
src/
  main.ts
  app.module.ts

  users/
    users.module.ts
    users.controller.ts
    users.controller.spec.ts
    users.service.ts
    users.service.spec.ts
    dto/
      create-user.dto.ts
      update-user.dto.ts
    entities/
      user.entity.ts
```

这是最接近框架原生的目录基线。它说明：

- `users/` 是业务 feature，不是技术层；
- Controller、Service、Module 使用 Nest 的角色后缀；
- DTO 和 Entity 在形成集合时放入子目录；
- generator 的 Service 与具体 ORM 解耦，只提供待实现占位；
- `repository/`、`mapper/`、`domain/`、`application/`、`infrastructure/` 都不是官方必建目录。

官方生成结果是起点，不是生产系统的完成状态。Entity 名称只是资源形状示例；接入 Prisma、TypeORM、MikroORM 或纯 SQL 后，
持久化模型放置应遵循对应工具和实际边界，不能为了保留生成目录而重复定义一份模型。

### 2.2 官方运行时职责

| Nest 概念       | 官方语义                                                         | 工程中的直接结论                                             |
| --------------- | ---------------------------------------------------------------- | ------------------------------------------------------------ |
| Module          | 组织 providers/controllers/imports/exports；provider 默认封装    | 每个 feature 用模块声明依赖和公开能力                        |
| Controller      | 接收传输请求并把复杂任务委托给 provider                          | 不承载 SQL、事务和核心业务状态转换                           |
| Provider        | 注册到 DI 容器并按 token 注入；支持 class/value/factory/existing | 业务组件通常用 class；配置、外部实例和异步初始化可用其他形式 |
| Pipe            | 转换或校验入口参数                                               | 不可信输入在到达业务用例前完成结构校验                       |
| Guard           | 决定当前请求是否允许进入                                         | 认证/粗粒度访问判断，不替代事务内业务授权                    |
| Interceptor     | 包围调用，处理日志、计时、映射等横切逻辑                         | 不把业务规则都塞进 interceptor                               |
| ExceptionFilter | 把异常映射为传输层响应                                           | 业务错误与 HTTP/RPC 状态映射分开                             |

Nest Module 的 `exports` 是 provider 公开面。跨模块复用优先通过 owner module 的 imports/exports，而不是把业务
Service 搬进全局 `shared/` 或把所有 provider 标成 `@Global()`。

### 2.3 90% 场景默认决策

| 场景                                       | 默认做法                                                           |
| ------------------------------------------ | ------------------------------------------------------------------ |
| 新建普通 Nest 后端                         | `main.ts` + `app.module.ts` + feature modules                      |
| 一个简单 CRUD feature                      | Module + Controller + Service + DTO；接入已选 ORM                  |
| NestJS 12 新建 schema-first HTTP API        | Zod + `StandardSchemaValidationPipe` + `@nestjs/swagger`           |
| Service 只有简单 Prisma CRUD               | 可直接注入 `PrismaService`；不机械创建 Repository                  |
| 查询复杂、数据源可能变化或事务边界需要隔离 | 增加具名 Repository provider                                       |
| API、业务对象、持久化对象确实不同          | 增加 Mapper；只有一个形状时不复制类型                              |
| 有业务行为与不变量                         | 增加 Model/Entity class；纯数据继续用 schema/type                  |
| 写用例很多且独立演进                       | 拆分 application services/use-cases；只有真实 bus 才引入 CQRS      |
| 多个模块复用某能力                         | 从 owner module 显式 export provider                               |
| 框架级横切能力                             | 按主题建立 `common/http`、`common/logging`；不建万能 CommonService |

### 2.4 工具链与版本治理

- Node.js 使用仍受官方支持的 LTS；本地、CI、镜像和 `@types/node` 对齐同一运行时 major。
- `packageManager` 固定实际使用的 pnpm 精确版本并提交唯一 `pnpm-lock.yaml`；CI 使用 frozen install。
- 新增或升级依赖时选择**当时最新稳定且互相兼容**的版本，核对官方 release、peer dependency、Node 支持范围和安全公告；
  不把文档日期或浮动 `latest` 当兼容证据。
- manifest 版本范围、lockfile 实际解析版本和运行中的二进制是三类事实；安装成功后仍要执行 lint、typecheck、test、build 和 smoke。
- Renovate/Dependabot 负责持续提出升级，不绕过 review、变更记录和回归门。框架 major、ORM、协议生成器等核心升级单独成切片。
- Nest CLI、编译器、测试运行器和 ESM/CommonJS 组合以新建或升级时的官方文档为准；不要把旧 starter 配置永久复制到新仓。

## 3. 架构选择：从 Nest 原生模块开始，按复杂度演进

`domain/application/infrastructure/interfaces` 不是 TypeScript 后端的必选顶层目录，也不是“像大厂”的凭证。
三种成熟形态都存在：

| 形态                                  | 适用场景                           | 主要收益                        | 主要风险                                   |
| ------------------------------------- | ---------------------------------- | ------------------------------- | ------------------------------------------ |
| Nest feature module                   | 大多数 CRUD、BFF、内部服务         | 框架原生、导航直接、样板少      | Service 变大后需要继续拆职责               |
| feature + application/data components | 用例、查询、第三方调用开始独立演进 | 保持 feature 内聚，同时细化角色 | 提前创建空层会增加跳转                     |
| feature 内部 Clean/Hexagonal/DDD      | 复杂状态机、多适配器、长期核心领域 | 业务规则独立于框架和数据库      | 全项目机械四层化会产生接口/Mapper 大量复制 |

默认从第一种开始。复杂度出现后，在**当前 feature 内部**演进，而不是先建立四个全局大目录：

```text
src/orders/
  orders.module.ts
  api/
  application/
  domain/
  persistence/
```

这棵树只有在 Order 确实有复杂规则、多种入口或数据适配器时才成立。简单 Users CRUD 继续保持 Nest 原生结构更成熟。

## 4. 仓库级组织

### 4.1 框架原生默认形态

```text
src/
  main.ts                         # bootstrap；不实现业务规则
  app.module.ts                   # composition root
  config/                         # 已验证的 typed configuration

  users/                          # feature module
  sessions/                       # feature module
  permissions/                    # feature module

test/                             # e2e/integration/contract/architecture
package.json
pnpm-lock.yaml
nest-cli.json
tsconfig.json
tsconfig.build.json
```

业务 feature 直接位于 `src/` 最接近 Nest 官方示例，适合顶层 feature 数量可控的服务。

### 4.2 `src/modules/` 是可选容器

当 `src/` 同时存在 config、common、generated、多进程入口等稳定顶层类别，使用
`src/modules/<feature>/` 可以提高扫描性：

```text
src/
  main.ts
  app.module.ts
  config/
  common/
  modules/
    users/
    sessions/
    permissions/
```

这是真实生产项目常见扩展，但不是 Nest 强制结构。一个仓选定一种即可；不要同时出现 `src/users/` 与
`src/modules/users/` 两套业务根，也不要为了只有一个 feature 创建没有信息增益的 `modules/` 容器。

### 4.3 `common/`、`shared/`、`utils/`、`constants/`、`models/`

这些目录都可以创建，前提是它们描述真实、稳定的职责：

| 目录         | 合理内容                                                       | 不应放入的内容                            |
| ------------ | -------------------------------------------------------------- | ----------------------------------------- |
| `common/`    | Nest/进程级横切能力：filters、guards、logging、database module | 某个 feature 的权限规则、DTO、Repository  |
| `shared/`    | 跨 feature 的无框架稳定结构；有明确 owner 和消费者             | “暂时不知道放哪”的业务代码                |
| `utils/`     | 按主题命名的无状态纯函数                                       | 网络、数据库、环境读取或业务编排          |
| `constants/` | 真实全局协议/平台常量；按主题拆文件                            | 所有 feature 的状态、错误码和魔法数字集合 |
| `models/`    | 确有共同生命周期和语义的共享模型                               | ORM Row、DTO、Domain Model 的无差别混合   |

生产默认不同时创建 `common/` 与 `shared/`。若两者边界无法用一句话区分，保留一个；
业务 provider 的共享优先使用 Nest Module exports。

`common/` 也不得作为扁平收容区：数据库 client、Redis client、readiness、日志、request context、时钟、ID 生成和业务 token
若同时直接平铺在其中，说明目录已经失去单一 owner。此时应按真实主题建立明确模块/目录，或把只被一个 feature 使用的能力移回该
feature；不能仅把 `common` 改名为 `core`、`foundation` 或 `infrastructure`。

### 4.4 `contract/`、`generated/`、`scripts/`、`sdk/`

- `contract/`：仅在仓库拥有 OpenAPI、Proto、JSON Schema 等机器契约时创建；不存 ORM 模型或业务源码。
- `generated/`：合法且常见，表示工具可重复生成、禁止手改的代码。位置服从生成器、构建和包边界；截至 2026-09-07，
  NestJS v12 当前 Prisma recipe 示例输出到 `src/generated/prisma`，它是示例路径而非框架强制目录。每项生成产物必须有明确的
  事实源、生成配置、owner 和消费入口；允许 Prisma Client、RPC types、SDK 等不同用途的多个产物，禁止同一用途存在来源不明、
  版本不一致或被消费者混用的重复副本。
- `scripts/`：只存构建、生成、验证、数据库安装和运维脚本；运行中的 `src/` 不反向依赖 scripts。
- `sdk/`：有真实消费者、发布和版本治理时才创建；服务端不反向 import 自己的 SDK。

数据库/缓存目录按**代码职责**命名，不按产品名机械创建。`common/database/prisma.service.ts` 是连接生命周期组件；
`users/users.repository.ts` 是 Users 数据访问。不要在每个业务模块下固定生成 `postgres/`、`redis/`。

### 4.5 推荐的 NestJS 生产目录基线

下面是本文对普通中大型 NestJS 服务的**默认推荐**，不是另造一套 Kokoro 专用架构：

```text
src/
  main.ts                         # 唯一进程入口
  app.module.ts                   # composition root

  config/                         # 环境 schema 与 typed config
  database/                       # ORM client 的进程生命周期
  health/                         # liveness/readiness
  http/                           # 全进程 filter/interceptor 等 HTTP 横切能力；确有需要才创建

  modules/                        # feature 较多时使用的可选容器
    users/
      users.module.ts
      users.controller.ts
      users.service.ts
      users.repository.ts         # 出现独立数据访问边界时才创建
      user.model.ts               # 出现业务行为/不变量时才创建
      user.error.ts
      schemas/                    # schema-first 路径
        create-user.schema.ts
        update-user.schema.ts
        user-response.schema.ts

  generated/
    prisma/                       # Prisma 配置指定的只读生成输出

test/
  unit/
  integration/
  contract/
  architecture/
  smoke/
```

选择规则：

1. feature 数量少时可把 `users/` 直接放在 `src/`；feature 与技术目录较多时再增加 `modules/`。
2. `config/database/health/http` 是按运行职责命名的技术目录，不是全局 `infrastructure` 四层模板。
3. feature 内优先保持 Nest 原生的 Module、Controller、Service；只有出现真实复杂度才增加 Repository、Model、Mapper、Policy、Client。
4. schema-first 项目使用 `schemas/`；class-validator 项目使用 `dto/`。同一个 wire shape 不同时维护 Zod schema 和重复 DTO class。
5. feature 变大后优先按 `sessions/`、`credentials/`、`members/` 等子能力拆分；不按 `services/`、`repositories/` 机械纵向分层。
6. 目录树是结果，不是目标。没有文件、没有 owner、没有近期增长的目录不预建。

## 5. 业务模块与子目录

### 5.1 简单 CRUD：不要过度设计

使用 Prisma 的简单 Users feature 可以是：

```text
src/users/
  users.module.ts
  users.controller.ts
  users.service.ts
  dto/
    create-user.dto.ts
    update-user.dto.ts
    user-response.dto.ts
```

`UsersService` 可直接注入 `PrismaService`。这与 Nest 官方 Prisma recipe 一致，不因为 Java 常见 Repository
就强制多包一层。Controller 做协议处理，Service 做用例和数据调用；当 Service 开始堆复杂查询、跨数据源、事务细节或难以隔离测试时，
再抽 Repository。

上例是 Nest CLI 的 class DTO 形态。NestJS 12 的 Zod schema-first 等价结构为：

```text
src/users/
  users.module.ts
  users.controller.ts
  users.service.ts
  schemas/
    create-user.schema.ts
    update-user.schema.ts
    user-response.schema.ts
```

Controller 把 schema 传给 Nest route decorator，进程注册 `StandardSchemaValidationPipe`；`@nestjs/swagger` 使用同一 Standard Schema
生成 OpenAPI。类型由 schema 推导，不再复制一套 class-validator DTO。

### 5.2 生产扩展：按真实职责增加文件

```text
src/users/
  users.module.ts
  users.controller.ts
  users.service.ts
  users.repository.ts              # 数据访问边界确有价值时
  users.mapper.ts                  # 表示确实不同时
  user.model.ts                    # 有业务行为/不变量时
  user.error.ts                    # 业务错误
  user.constants.ts                # 本 feature 的公开固定规则
  dto/
    create-user.dto.ts
    update-user.dto.ts
    user-response.dto.ts
```

不是每个 feature 都要有全家桶：

- ORM 生成类型足够时，不再手写同形 `row.ts` 或 Entity；
- API 输出与内部对象相同时，不创建只做字段复制的 Mapper；
- 只有数据没有行为时，不把 interface 强行包装成 class；
- 只有一个文件且看不到稳定增长时，不提前创建 `repositories/`、`mappers/`、`models/` 子目录。

### 5.3 feature 变大时先按子能力拆

```text
src/identity/
  identity.module.ts
  authentication/
    authentication.controller.ts
    authentication.service.ts
  sessions/
    sessions.service.ts
    sessions.repository.ts
  credentials/
    credentials.service.ts
    credentials.repository.ts
  dto/
```

优先按 authentication、sessions、credentials 这类业务词汇拆分，再在子能力中按角色增加目录。不要让一个
`identity.service.ts` 同时负责登录、会话、角色、审计和邮件，也不要因为文件多就立即拆成多个微服务。

### 5.4 `commands/`、`queries/`、`handlers/` 与 use-cases

这些名称是可选组织，不是成熟度徽章：

| 实际需求                             | 建议                                                         |
| ------------------------------------ | ------------------------------------------------------------ |
| 普通 CRUD                            | Service 的具名方法                                           |
| 独立用例多、每个用例有不同依赖和事务 | `use-cases/` 或多个 application service                      |
| 已决定采用官方 `@nestjs/cqrs`        | Command/Query 与 Handler 分文件，注册到 Nest provider        |
| 跨进程消息                           | 机器 contract + consumer/processor；不复用内存 Command class |

没有 CommandBus/QueryBus 时，不建立 `command-executor.ts` 或自研总线。采用 CQRS 时，同一用例只有一处编排权威，
Handler 与 Service 不重复业务逻辑。CQRS 本身不提供持久化、重试或 exactly-once。

### 5.5 模块公开面

- 跨模块只注入 owner module 显式 export 的 provider；不 deep-import 对方 Repository、内部 DTO 或 ORM 类型。
- TypeScript export 与 Nest Module export 都要控制；二者不是一回事。
- 循环依赖先重新划分 owner，不把 `forwardRef()` 当默认解法。
- 一个 module 表达一组紧密相关能力，不等于一张表或一个 endpoint。

## 6. class 与职责

### 6.1 何时优先 class

Nest 官方运行时组件及常见生产角色如下；只有需要运行时身份、DI 或生命周期管理的组件默认使用 class。
“来源”说明角色本身来自框架还是生产扩展；“负责/不负责”列均是本文的 **[Production]** 边界建议。

| 来源         | 角色                          | 负责什么                                 | 不负责什么                     |
| ------------ | ----------------------------- | ---------------------------------------- | ------------------------------ |
| [Nest]       | `*.module.ts`                 | imports/providers/controllers/exports    | 业务算法、SQL                  |
| [Nest]       | `*.controller.ts`             | 路由、参数、调用 Service、响应语义       | 事务、数据访问、核心规则       |
| [Nest]       | `*.service.ts`                | 内聚用例、业务授权、事务与副作用编排     | wire parser、ORM Row、环境读取 |
| [Production] | `*.repository.ts`             | 具名查询、持久化、租户范围、错误归一     | HTTP 状态、用户权限、外部网络  |
| [Production] | `*.client.ts`                 | 第三方/owner SDK、认证、预算、错误归一   | 本仓状态机与数据库写入         |
| [Production] | Mapper                        | 纯同步转换用具名函数；需要注入时用 class | I/O、授权、业务状态变化        |
| [Nest]       | Guard/Pipe/Filter/Interceptor | Nest 请求生命周期中的单一横切职责        | 业务 Service 的替代品          |
| [Production] | Worker/Processor              | 消费、停止接活、ACK/重试接线             | 第二份核心业务规则             |

构造依赖使用 `private readonly` 注入。单个实现时直接注入具体 class，不机械创建
`IUserRepository` + `UserRepositoryImpl`、`BaseRepository<T>` 或 getter/setter 层。
只有多个实现、插件边界或测试隔离确有价值时才引入 token/窄接口。

### 6.2 哪些对象不应为了统一外观包装成 class

- Zod schema 与由其推导的 type；
- union、mapped type、函数签名和配置 shape；
- 无状态纯函数；
- 常量集合；
- ORM/Proto/OpenAPI 生成类型；
- 只有字段、没有不变量或行为的内部数据。

TypeScript 的成熟写法不是“所有东西 Java 化”。class 用于运行时身份、依赖注入、封装状态和行为；type/schema 用于数据与边界。

### 6.3 Service

一个 Service class 可以包含同一 feature 的一组内聚操作。不要每个 CRUD 方法都创建一个 UseCase；也不要把身份、租户、计费、通知
长期塞进一个 Service。Service 决定业务事务边界，但不暴露 `Prisma.TransactionClient`、`pg.PoolClient`
或 HTTP Request 给业务方法。

### 6.4 Repository

Repository 是可选的数据访问边界，不是 ORM 的别名。其方法使用业务语言，例如 `findActiveByEmail()`、
`saveSession()`，而不是把 ORM 的所有 `findMany()` 参数原样向上泄漏。
Repository 可由 Prisma、TypeORM、MikroORM、Kysely 或 `pg` 实现。

### 6.5 DTO、Schema 与 Model

三者语义不同，但不机械复制字段：

| 对象   | 语义                       | 推荐表达                                         |
| ------ | -------------------------- | ------------------------------------------------ |
| DTO    | 网络输入/输出边界模型      | class DTO 或 schema 推导类型，按边界选一种事实源 |
| Schema | 可执行的运行时结构定义     | Zod、Valibot、ArkType 等 Standard Schema 对象    |
| Model  | 业务状态、不变量、合法转换 | 有行为时 class；纯数据 type/interface            |

截至 2026-09-07，NestJS v12 当前官方文档同时提供：

1. `ValidationPipe` + class-validator/class-transformer；
2. `StandardSchemaValidationPipe` + Zod、Valibot、ArkType 等 Standard Schema 工具。

每个传输边界选择一个主路径。Schema-first 路径以 Standard Schema 对象为运行时事实源；Class DTO 路径以 DTO class 与
class-validator decorators 为运行时事实源。若采用 Zod，schema 与 `z.infer` 类型可以共置，不再手写同字段的 class-validator DTO。
若依赖装饰器元数据和 `@nestjs/swagger` class DTO，则使用 class 路径，并通过验证/生成测试保持契约一致。目标仓采用前必须核对
实际 Nest major；旧 major 不以本文 API 名称替代版本升级验证。

Model class 只在业务行为存在时使用，例如 `Session.revoke()`、`Subscription.cancel()`；
不要让 ORM Entity、API DTO 和 Domain Model 互相冒充，也不要对普通 JSON 使用 `as UserModel` 假装拥有 class 方法。

### 6.6 Mapper

Mapper 不是 Nest 官方必备组件。仅当 API DTO、业务对象和持久化对象语义不同，或转换规则复杂且需要独立测试时创建。

- 纯同步映射优先具名函数；
- 需要注入时钟、加密器、配置等依赖时使用 `@Injectable()` class；
- Mapper 不查数据库、不做授权、不改变业务状态；
- 同形对象不要经过 `DTO -> Command -> Model -> Row -> Response` 五次机械复制。

### 6.7 公开方法的入参与出参

Controller/RPC 的入参和出参服从 wire contract，使用生成 request/response、DTO class 或运行时 schema 推导类型。Service、Repository、
Client 的内部 API 不直接复用 wire DTO，也不把 Prisma input、driver row 或第三方 SDK response 暴露给调用方。

以下情况使用具名 `Readonly` 参数对象，而不是不断增加位置参数：

- 有两个以上同类型 primitive，调用处难以判断顺序；
- 参数包含分页、筛选、scope、expected state、幂等身份或多个可选项；
- 方法预计会增加参数，或同一组参数需要跨调用传递；
- 参数本身表达 command/query/options 等稳定业务概念。

简单且无歧义的 `findById(id: UserId)`、`remove(sessionId: SessionId)` 可以保留单参数；不为每个 primitive 机械包装对象。
内部对象按语义命名为 `<Operation>Command`、`<Operation>Query`、`<Operation>Input` 或 `<Operation>Options`，只有网络传输对象使用
`Dto`。输入对象负责表达数据，不把业务执行逻辑塞入参数 class。

输出包含 items、cursor、是否命中、变更结果或其他元数据时，返回具名 `<Operation>Result`/`<Subject>Page`，不要用裸数组、tuple、
模糊 boolean 或 `Record<string, unknown>` 隐藏语义。Repository 的“多取一条判断下一页”必须通过 `hasNextPage` 等字段显式表达，
不能只返回 `T[]` 让 Service 猜测内部查询策略。

```ts
type FindTenantPageQuery = Readonly<{
  afterId: string | null;
  limit: number;
  tenantScope: readonly string[] | "*";
}>;

type FindTenantPageResult = Readonly<{
  items: readonly Tenant[];
  hasNextPage: boolean;
}>;
```

分页需要区分边界语义：API/RPC 与 Application Query 使用 `limit + cursor`，其中 cursor 是 opaque wire value；Application 负责校验
limit 并把 cursor 解码为内部 keyset。Repository 只接收 `afterId + limit` 等已解析查询条件，返回 `items + hasNextPage`；它不解析
签名 cursor，也不生成对外 `nextCursor`。Application 再根据查询结果编码 `nextCursor`。这样协议 codec 与 Prisma 查询不会互相穿透。

具名 input/result type 与其唯一方法契约具有同一变化原因时可以共置；有多个消费者、需要作为 feature 公开 API 导出或文件已出现
第二个主要角色时，再提取到 `<operation>.types.ts` 或语义明确的 contract 文件。不要建立全局 `inputs/`、`outputs/` 垃圾桶。

## 7. Prisma、ORM 与 Repository

### 7.1 先区分概念

| 概念       | 作用                                               |
| ---------- | -------------------------------------------------- |
| PostgreSQL | 数据库                                             |
| Prisma     | schema、生成类型和 type-safe client                |
| TypeORM    | Data Mapper/Active Record 风格 ORM 与 Nest 集成    |
| Kysely     | type-safe SQL query builder                        |
| `pg`       | PostgreSQL driver                                  |
| Repository | 应用代码中的数据访问职责；是否单独存在由复杂度决定 |

### 7.2 Prisma 的成熟落地

Nest 官方 Prisma recipe 建议用 `PrismaService` 管理 client，并展示 `UsersService`
直接调用生成 client。这说明 Repository 不是使用 Prisma 的前置条件。

增加 `UsersRepository` 的典型信号：

- 多个 Service 重复相同查询、租户过滤、字段投影或错误归一；
- 复杂事务需要把可用数据操作收窄；
- 业务方法不应依赖 Prisma 的 `WhereInput`、`UncheckedCreateInput` 等持久化类型；
- 存在多个数据源/实现，或需要稳定的数据访问 seam；
- 查询复杂度已经妨碍 Service 阅读和独立测试。

不增加 Repository 的典型场景：少量直接 CRUD、一个 Service 唯一使用、Prisma 类型没有越过 feature 边界。

### 7.3 ORM 选择与 schema 管理是项目决定

Prisma、TypeORM、MikroORM、Drizzle、Kysely、`pg` 都可能是成熟选择；根据查询复杂度、迁移方式、类型生成、事务、
团队经验和退出成本决定。通用 TypeScript 规范不规定是否使用外键、是否保留 migration、是否软删除，也不规定唯一 schema 文件位置。
这些必须写入目标仓 DATA_MODEL/ADR，并由真实数据库 integration test 证明。

同一业务事务只能使用同一连接/transaction context；不能因为同时使用 ORM raw query 和 client API 就悄悄建立第二个 Pool 或提交链。

## 8. 类型设计

### 8.1 TypeScript 严格基线

新项目启用 `strict`，并根据代码库成熟度评估开启：

```json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noImplicitOverride": true,
    "useUnknownInCatchVariables": true,
    "forceConsistentCasingInFileNames": true
  }
}
```

不要用 `any`、双重断言、非空断言或宽泛 `Record<string, unknown>` 穿透系统。
`unknown` 只存在于真正未知的边界，随后立即用 schema、协议生成器或窄 type guard 收窄。

### 8.2 class、interface、type、enum、const 的选择

| 构造        | 适用场景                                                    |
| ----------- | ----------------------------------------------------------- |
| `class`     | Nest provider、运行时身份、状态封装、业务行为               |
| `interface` | 可扩展对象契约、依赖能力、公开对象 shape                    |
| `type`      | union、intersection、mapped type、函数签名、schema 推导结果 |
| `as const`  | 需要运行时值和字面量 union 的有限集合                       |
| `enum`      | 外部协议/框架明确要求，或运行时枚举对象确有价值             |

不要同时维护 enum、string union、Zod enum 和数据库状态四份列表。选一份事实源并推导其余表示；生成协议枚举不再人工复制。

### 8.3 边界校验

HTTP body/query/params、环境变量、消息、第三方响应和持久化 JSON 都是不可信输入，必须在边界解析。优先使用成熟 schema/协议工具，
不要在业务文件里反复散落 `typeof value === ...` 来猜结构。

`typeof`、`instanceof` 与具名 type guard 仍是正常语言能力，可用于局部 narrowing；问题是无统一 schema、
重复猜外部 shape，而不是出现 `typeof` 三个字。

### 8.4 一个手写 TypeScript 文件只承载一个主要变化原因

“一个文件一个职责”不等于“一个文件只能出现一种语法”。判断依据是 owner、变化原因、依赖和测试方式。

这是一条 **Production 工程约定**，不是 TypeScript language specification，也不是 NestJS 强制目录。TypeScript 官方定义语言、
类型系统和模块语义；NestJS 官方定义 Module/Controller/Provider 等框架角色；Repository、Model、Schema、Error、Client、Generator
是否独立，必须由当前项目的变化原因决定。团队采用本约定后，再通过 lint/architecture test 变成仓库合并标准。

因此，“Service、Repository、Model、Schema、Error、Client、Generator 分离”的准确含义是：**独立演进的职责不得长期混在同一
角色文件里**，而不是看到七个名词就机械创建七个文件或七个目录。

这些角色也不是每个 feature 都必须配齐的“七件套”：简单 CRUD 通常只有 Module、Controller、Service、DTO/schema 和
Prisma 调用；没有行为不变量就不建 Model class，没有独立持久化边界就不建 Repository，没有外部系统就不建 Client，
没有可替换的 ID/token/key 生成策略就不建 Generator。这里的 Generator 指 `IdGenerator`、`TokenGenerator` 之类可注入能力，
与 `generated/` 下的 Prisma/Proto 生成代码不是同一概念。

#### 8.4.1 角色文件默认形态

Service、Repository、Controller、Client 默认是：

```text
imports
+ 一个主要导出的角色 class
+ 与实现紧密相关的 private method / file-local helper
+ 少量只服务该实现的 file-local constant
```

以下独立事实不顺手塞入角色文件：

| 独立职责          | 默认文件                 |
| ----------------- | ------------------------ |
| API 输入/输出     | `dto/<operation>.dto.ts` |
| 通用运行时 schema | `<subject>.schema.ts`    |
| 业务模型          | `<subject>.model.ts`     |
| 业务错误          | `<subject>.error.ts`     |
| feature 公开常量  | `<subject>.constants.ts` |
| 持久化映射        | `<subject>.mapper.ts`    |
| 外部协议 codec    | `<subject>.codec.ts`     |
| provider options  | `<subject>.options.ts`   |

#### 8.4.2 合理共置

以下内容属于同一事实或算法，可以共置：

- Zod schema + 从它推导的 type；
- 一个错误类 + 该错误专属的小型 code union；
- `as const` 有限值集合 + 从它推导的 union；
- 纯函数 + 只服务该算法的私有 helper；
- class 的 private methods 与方法内部局部常量；
- Repository 方法中的短 SQL 与直接映射。

#### 8.4.3 角色是否拆文件的判定表

| 组合 | 默认 | 原因 |
| --- | --- | --- |
| Service class + private method + 只服务该 class 的局部常量/type | 共置 | 同一实现、同一测试与变化原因 |
| Zod schema + `z.infer` type | 共置 | schema 是唯一运行时事实源，type 由其推导 |
| `as const` 状态集合 + 推导 union | 共置 | 同一有限集合，避免两份事实 |
| Error class + 该错误专属 code union | 共置 | 同一错误契约；错误很多且独立时再建 `errors/` |
| Service + Repository 查询/Prisma persistence | 默认拆 | 用例/事务与数据访问通常有不同依赖、测试和演进节奏；简单单表 CRUD 可直接 Prisma |
| Service + HTTP/RPC DTO/schema | 拆 | wire contract 变化不应迫使业务编排文件变化 |
| Service + 有行为的 Model class | 拆 | Model 维护不变量/状态转换，Service 编排用例 |
| Service + 外部网络 Client | 拆 | Client 独立负责认证、timeout、重试、响应解析和错误归一 |
| Service + 随机 ID/token/key Generator | 通常拆 | 可替换、可注入、可独立测试；仅一次局部调用时可直接使用标准库 |
| Repository + 只服务该查询的短映射 helper | 共置 | 没有独立公共语义，拆出只会增加跳转 |
| 业务常量 + Service | 局部值共置；公开不变量拆 | `const RETRY_LIMIT = 3` 若只服务一个算法可留本文件；状态集合/wire version/多消费者规则独立维护 |

拆分触发条件满足任一即可：

1. 该对象有独立消费者或需要被 feature public API 导出；
2. 修改它的原因与当前主 class 不同；
3. 它拥有独立 I/O、生命周期、认证、错误或测试边界；
4. 它是运行时事实源（Zod/schema、业务状态集合、配置）且会被多个角色消费；
5. 文件已经让读者无法在 30 秒内回答“谁拥有它、它做什么、它依赖什么”。

不拆分条件：只有一个消费者、没有独立语义、只服务一个算法、拆出后只剩转发层。成熟工程追求低变化耦合，不追求文件数量。

不要把每个数字、每个 type、每个 helper 都拆成文件。拆分目标是减少变化耦合，不是追求文件数量。

#### 8.4.4 明确需要拆分的组合

- Service class + API DTO/schema + 业务错误体系；
- Repository SQL + HTTP 状态映射 + 权限判断；
- cursor codec + 密钥配置 + tenant 授权 + 列表用例；
- Controller + Service + Model class；
- 一个文件同时导出多个互不依赖的 public class；
- 其他模块为了一个 type 被迫依赖整个业务实现文件；`import type` 虽不产生运行时加载，仍可能暴露不合理的源码依赖和公开契约耦合。

即使文件只有 80 行，只要存在多个独立变化原因也应拆；即使超过 400 行，生成代码或一个完整状态表也不能只按行数机械切碎。

#### 8.4.5 文件审查问题

1. 能否用一句业务语言说明该文件的 owner 和角色？
2. 修改 API shape、业务规则、数据库和密码算法时，是否会同时改这个文件？
3. 测试一个纯规则是否被迫启动 HTTP、数据库或密钥配置？
4. 消费者能否只 import 它需要的公开能力？
5. 拆分后是否减少耦合，而不是只增加转发层？

### 8.5 typed lint

**[TS]** 使用 typescript-eslint type-aware 配置，并明确启用 unsafe assignment/call/member access、floating promise、Promise 误用等
具体规则；需要 `switch` 穷尽性时显式启用 `switch-exhaustiveness-check` 并固定选项。**[Production]** 受限 import、循环依赖、
跨 feature deep import 和无理由 disable 由独立 ESLint 规则或 architecture test 验证。每项门禁应有执行命令和正反例，不能把
“启用 type-aware preset”当作已覆盖全部架构规则的证据。Prettier 只负责格式，不替代语义 lint。

## 9. 文件与目录命名

### 9.1 Nest 官方角色与 CLI 命名

| 对象                 | 形式                       | 示例                         |
| -------------------- | -------------------------- | ---------------------------- |
| feature 目录         | `kebab-case`，自然业务名称 | `users/`、`scheduled-tasks/` |
| Nest Module          | `<feature>.module.ts`      | `users.module.ts`            |
| Controller           | `<feature>.controller.ts`  | `users.controller.ts`        |
| Service              | `<feature>.service.ts`     | `users.service.ts`           |
| 单个 Entity          | `<entity>.entity.ts`       | `user.entity.ts`             |
| DTO                  | `<action>-<entity>.dto.ts` | `create-user.dto.ts`         |
| Guard/Pipe/Filter    | `<subject>.<role>.ts`      | `auth.guard.ts`              |
| 测试                 | `<subject>.<role>.spec.ts` | `users.service.spec.ts`      |
| class/type/interface | `PascalCase`               | `UsersService`、`User`       |
| 函数/变量            | `camelCase`                | `createUser`、`tenantId`     |

Nest CLI 默认使用 `.spec.ts`；团队可以统一为 `.test.ts`，但不要同仓混用。
目录是否复数由自然业务词和框架生态决定，不是所有单词机械加 `s`：`users/`、`sessions/` 常见，
`auth/`、`billing/`、`identity/` 本身就是能力名称。

### 9.2 常见生产角色命名

以下是可读、常见的生产约定，不是 Nest CLI 强制后缀：

| 对象                | 形式                      | 示例                  |
| ------------------- | ------------------------- | --------------------- |
| Repository provider | `<feature>.repository.ts` | `users.repository.ts` |
| 业务 Model          | `<entity>.model.ts`       | `user.model.ts`       |
| Schema              | `<subject>.schema.ts`     | `cursor.schema.ts`    |
| Mapper/Client       | `<subject>.<role>.ts`     | `user.mapper.ts`      |
| Error/Constants     | `<subject>.<role>.ts`     | `user.error.ts`       |

### 9.3 常用角色后缀

```text
.module.ts        .controller.ts    .service.ts       .repository.ts
.dto.ts           .entity.ts        .model.ts         .schema.ts
.mapper.ts        .client.ts        .guard.ts         .pipe.ts
.filter.ts        .interceptor.ts   .error.ts         .constants.ts
.command.ts       .query.ts         .handler.ts       .processor.ts
```

路径已经表达上下文，不把实现技术和多个机制全部串进文件名。避免：

```text
postgres-command-receipt-repository.ts
tenant-management-authentication-service.ts
scheduled-task-command-executor.ts
```

改为让目录承担上下文、文件承担角色，例如 `authentication/commands/command.repository.ts`、
`tenants/management/tenant-authenticator.ts`、`scheduled-tasks/scheduled-task.service.ts`；如果仍无法命名，通常说明 feature
边界没有设计清楚。不要把 `Service` 当成所有可注入 class 的统一后缀：client、repository、generator、resolver、authenticator、
worker 和 application state 应使用自己的真实角色名。

### 9.4 import 与 `index.ts`

- 同一 feature 内优先短相对 import；跨 feature 通过公开 module/package API。
- Node ESM/NodeNext 使用运行时能解析的扩展名；仅编译期使用的声明采用 `import type`。作为 Nest DI token、DTO 运行时校验或
  其他装饰器元数据输入的 class 必须保留值导入，或改用显式 runtime token/schema。
- path alias 必须被 dev、test、build、start、lint 全链路理解；不要只让 IDE 能解析。
- `index.ts` 只在确有公开 API 时创建，显式导出；不在每个目录机械 `export *`。
- 不通过当前目录自己的 barrel import 自己，避免循环依赖。

## 10. 环境变量与配置

`process.env` 是 Node 的最终进程环境接口；`.env`、`.env.local`、`.env.test`
是可选的本地输入文件。Nest/Node 不会替所有项目统一这些文件的覆盖顺序，因此每个仓必须明确并测试装载策略。

生产建议：

- `process.env` 只在 config/bootstrap 边界读取；Service 不直接读取；
- 使用 `@nestjs/config`、Node `--env-file` 或其他 loader 中的一种，不叠加三套；
- 用 Zod/Joi/Standard Schema 等在启动时校验并输出 typed config；
- `.env.example` 可提交，真实 secret 与 `.env.local` 不提交；
- 生产从部署环境/secret manager 注入，不依赖仓库中的 `.env.production`；
- test 使用确定性配置，不意外读取开发者 `.env.local`；
- 配置错误启动即失败，日志不打印 secret、连接串或完整 token。

`.env.local` 是否覆盖 `.env`、`.env.test.local` 是否存在，是 **[Project]** 决定，
不是 TypeScript 行业固定语义。

## 11. API、RPC、错误、generated 与 SDK

### 11.1 API 边界

- Controller/RPC adapter 只处理协议、验证、受信上下文、调用 Service 和响应映射；
- DTO/Schema 定义并校验运行时传输边界，不把 ORM Entity/Prisma model 直接公开；
- 对外 wire contract 由版本化 OpenAPI、Proto、GraphQL/JSON Schema 或经过验证的 code-first 生成结果发布；
- tenant、actor、service identity 来自受信中间件/Guard/interceptor，不从 body 自报；
- 分页、幂等、并发条件、错误 envelope 与 breaking strategy 写入 API 契约。

### 11.2 错误规划

| 错误类型         | 推荐位置                                          |
| ---------------- | ------------------------------------------------- |
| feature 业务错误 | 当前 feature 的 `<subject>.error.ts` 或 `errors/` |
| HTTP 映射        | `common/http/filters/` 或当前 transport adapter   |
| RPC 映射         | RPC adapter/interceptor                           |
| SDK 错误         | SDK 自己的 `ApiError`，只消费 wire error code     |

业务错误码、HTTP status、Error class 是不同职责。有限业务码可由 `as const` + union 或 schema 管理，
不因为“像 Java”就必须 enum。客户端只按稳定 machine code 分支；服务端不泄漏 SQL、stack、secret 和原始第三方错误。

### 11.3 generated 与 SDK

generated code 的规则：每项产物的事实源、生成器、版本、owner 和消费入口可追溯，CI 检查 drift，禁止手改。允许同一事实源
生成不同用途、语言或发布目标的产物并分别验证；禁止同一用途存在来源不明、版本不一致或消费者混用的重复生成副本。生成物必须
由其 owning package 的 typecheck/build 或等价生成验证覆盖；若作为独立 artifact 发布，由独立 pipeline 验证，消费方验证版本、
digest 和兼容性。

SDK 只在有真实消费者与发布流程时建立。SDK 使用 generated wire types，不复制服务端 Domain Model、ORM schema 或内部 DTO；
对外 Client class 统一 endpoint、认证、deadline、AbortSignal、请求 ID、错误与经过证明的重试语义。

## 12. 事务、并发、缓存与可靠性

### 12.1 事务

- Service/application use-case 决定事务边界；Repository 执行数据操作；
- 同一事务使用同一 ORM transaction/client，不让每个 Repository 自己提交；
- 事务内避免等待外部 HTTP/RPC；可靠发布采用 outbox 等明确模式；
- 只在完整操作可安全重放时重试 serialization/deadlock；加入上限、退避和 jitter；
- 提交结果未知时按幂等身份查询，不盲目再次执行写入。

### 12.2 并发与幂等

幂等不是“用了 Redis”。权威业务写入通常由数据库唯一性、版本条件、事务和持久 receipt 共同保证；Redis 可做限流、缓存、通知、
短期协调，但其丢失不能破坏权威事实。具体机制根据操作语义设计并做并发 integration test。

### 12.3 I/O 与生命周期

- 数据库、Redis、HTTP client 通常每进程维护受控连接资源，由 Nest provider 管理生命周期；
- 设置连接、排队、查询、锁、响应体和总调用预算；取消沿支持的调用链传播；
- 有限重试只用于可安全重放操作；指数退避、jitter 和 retry budget 缺一不可；
- `/livez` 只证明进程存活；`/readyz` 反映启动、draining 和关键依赖状态；
- 使用 Nest lifecycle hooks 与唯一信号 owner 实现有界 drain、资源关闭和部分启动失败清理；
- 结构化日志包含 service、operation、request_id、trace_id、result、duration，不记录 secret。

## 13. 测试策略

| 层次         | 主要验证                                              |
| ------------ | ----------------------------------------------------- |
| unit         | Service、policy、Model、Mapper 的分支                 |
| integration  | 真实 ORM/SQL、事务、锁、Redis、provider adapter       |
| contract     | OpenAPI/Proto、generated drift、producer/consumer     |
| architecture | feature 边界、受限 import、env/ORM 类型泄漏、循环依赖 |
| e2e/smoke    | build 后真实启动、health、认证和最小业务请求          |

- Nest `TestingModule` 用于 DI 组件测试；对 provider 使用 override，而不是复制生产实现。
- 简单 CRUD 的关键价值通常来自真实数据库 integration test，不是再造四层 mock。
- 测试覆盖权限失败、tenant 越权、唯一冲突、乐观锁、重复命令、事务回滚、超时/取消和恢复。
- Fake/Fixture/InMemory 放测试目录，不进入生产 `src/`。
- 并行测试隔离数据库/schema、Redis prefix 和端口；只清理自身资源。

## 14. 工程门禁

TypeScript/Nest 服务至少提供并真实执行：

```bash
pnpm install --frozen-lockfile
pnpm format:check
pnpm lint
pnpm typecheck
pnpm test
pnpm build
```

有 contract、数据库或 e2e 时增加相应命令。CI 重点阻断：

1. Controller 直接执行 SQL/Redis 或核心业务规则；
2. Service 暴露 HTTP Request、ORM input、driver client 或直接读取 `process.env`；
3. 跨 feature deep import、循环依赖和无 owner 的公共目录；
4. `any`/不安全调用、floating promise、未处理的异步错误；
5. 手写业务文件同时承担 Service、DTO/schema、Error、Repository 和 codec；
6. 生成物被手改、两个可编辑契约来源，或存在同一用途但失去版本/owner/消费治理的重复生成副本；
7. 生产 `src/` 中出现 Fake、Fixture、InMemory；
8. 空测试/lint 脚本、只 typecheck 不 build、以历史结果冒充当前 commit 证据。

门禁检查职责与依赖，不按 `common`、`shared`、`repository` 等目录名一刀切。
架构 lint 需要正反例测试，Markdown 自述不是验收。

## 15. 创建目录或文件前的设计门

新增文件/目录或调整模块边界前，先回答：

| 项       | 必须明确的结论                                                 |
| -------- | -------------------------------------------------------------- |
| Owner    | 哪个服务、哪个 feature 拥有该事实和写入权                      |
| 当前态   | 现有入口、相邻文件、import、contract、schema、测试             |
| 职责     | Module/Controller/Service/Repository/DTO/Model/Client 中哪一种 |
| 方案比较 | 复用现有文件、新建角色文件、新建子能力目录至少比较两项         |
| 粒度     | 为什么当前职责需要新文件/目录，不是模板预建                    |
| 依赖     | 可以 import 什么、由谁公开和消费                               |
| 数据/API | 是否影响事务、tenant、幂等、缓存、contract、generated 或 ORM   |
| 删除项   | 被替代的旧路径、重复 shape、alias、fallback                    |
| 验证     | unit/integration/contract/architecture/build/smoke 如何证明    |

简单局部修改可用一句话说明 owner 与验证；新顶层目录、业务模块、运行进程或跨服务 owner 需要技术设计/ADR。

## 16. 重构顺序

1. 盘点行为、目录、依赖、契约、schema 与真实门禁结果；
2. 先确定 feature owner、API/data contract 与目标目录，不先全仓搬文件；
3. 以一个可运行的业务切片调整 Controller → Service → 数据/外部依赖；
4. 只在复杂度证据出现时增加 Repository、Mapper、Model、use-case 或 CQRS；
5. 清理已失去用途的重复实现；仍承担有效契约的旧入口按迁移方案明确退役顺序和期限；已批准的 clean-slate 项目范围则在同一
   切片删除被替代路径、alias 和 fallback，不建立兼容双轨；
6. 更新 import/architecture tests、文档和生成配置；
7. 执行 format、lint、typecheck、unit、integration、contract、build、e2e/smoke；
8. 每个 commit 表达一个可审查业务目的，不夹带无关依赖升级或全仓格式化。

## 17. 真实来源与核验记录

### 17.1 官方资料

- [NestJS Modules](https://docs.nestjs.com/modules)：feature module、封装、imports/exports、shared/global module 语义。
- [NestJS Providers](https://docs.nestjs.com/providers)：Service、Repository、Factory、Helper 作为可注入 provider；Controller 委托复杂任务。
- [NestJS CLI](https://docs.nestjs.com/cli/usages#nest-generate)：starter、resource/module/controller/service 等真实 generator 能力。
- [NestJS CRUD generator](https://docs.nestjs.com/recipes/crud-generator)：Module、Controller、Service、DTO、Entity 与测试的生成边界。
- [NestJS Validation](https://docs.nestjs.com/techniques/validation)：ValidationPipe 与 StandardSchemaValidationPipe 两条官方路径。
- [NestJS OpenAPI](https://docs.nestjs.com/openapi/introduction)：NestJS 12 从 route decorator 读取 Standard Schema，并支持通过
  `zod-openapi` 转换 Zod schema，避免维护重复 Swagger DTO。
- [NestJS Prisma recipe](https://docs.nestjs.com/recipes/prisma)：PrismaService、generated client 与 Service 直接数据访问示例。
- [NestJS CQRS](https://docs.nestjs.com/recipes/cqrs)：Command/Query/Handler 是可选机制，不是所有模块的基础层。
- [TypeScript strict](https://www.typescriptlang.org/tsconfig/strict.html) 与
  [typescript-eslint typed linting](https://typescript-eslint.io/getting-started/typed-linting/)：严格类型与类型感知 lint。

### 17.2 企业公开工程约定

- **[Production 参考]** [Google TypeScript Style Guide](https://google.github.io/styleguide/tsguide.html)：用于比较语言构造、导出、
  工具函数和可读性取舍，不作为 TypeScript 语言限制或 NestJS 框架要求。

### 17.3 真实公开代码库

以下链接固定到 2026-09-07 核验的 commit，只证明目录和代码组织事实，不代表某家公司为所有项目发布的强制标准：

| 项目                    | 固定源码                                                                                                                       | 可观察事实                                                        |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------- |
| Nest TypeScript starter | [commit `c8fb6bc4`](https://github.com/nestjs/typescript-starter/tree/c8fb6bc4b01792ce7016a9b0c6bd7f3dbd5f0416/src)            | 根 Module/Controller/Service 的最小框架结构                       |
| Novu API subscribers    | [commit `49e4b308`](https://github.com/novuhq/novu/tree/49e4b308eeba9a5ab86605ee2eac8fd882110e0a/apps/api/src/app/subscribers) | 真实 feature 内按 dtos、usecases、query-objects、utils 等需要展开 |
| Vendure core            | [commit `523b5730`](https://github.com/vendurehq/vendure/tree/523b57304c5850b86069de30a97b723a3f4da284/packages/core/src)      | 成熟 Nest 生态项目也会采用 api/service/entity/common 等不同组织   |

结论不是“抄其中一棵树”，而是：遵守框架原生组件语义，以 feature 聚合业务，按真实复杂度增加角色和层次，并用门禁保持边界。

## 附录 A：项目覆盖规则如何接入

一个具体项目可以在本手册之上增加 **[Project]** 规则，但必须放在项目技术方案、DATA_MODEL、API_CONTRACT 或 ADR 中，
不得反写为所有 TypeScript/Nest 项目的通用事实。例如：

- 是否使用 Prisma、TypeORM、Kysely 或 `pg`；
- 是否使用数据库外键、migration、soft delete 或单一 schema；
- 使用 HTTP、ConnectRPC、gRPC、GraphQL 或消息协议；
- 使用 Zod Standard Schema 还是 class-validator DTO；
- 选择 `src/<feature>` 还是 `src/modules/<feature>`；
- public API、SDK、generated 输出和发布方式。

无外键并非 Kokoro 独有：[Alibaba Java 开发手册](https://github.com/alibaba/Alibaba-Java-Coding-Guidelines) 把禁用外键/级联列为强制项，
[Vitess](https://vitess.io/docs/faq/getting-started/compatibility/are-foreign-keys-supported-in-vitess/) 也明确不鼓励在分片 keyspace 使用外键约束；
这是高并发、分布式和分库分表系统中成熟且常见的治理路线。它仍不是所有公司、所有单库 PostgreSQL 场景的统一规则——例如
[Google Cloud Spanner](https://cloud.google.com/spanner/docs/foreign-keys/overview) 当前文档在适用场景默认建议 enforced foreign key。
Kokoro 明确选择无外键作为硬规则，并按
[SQL 手册](03-sql-and-postgresql.md) 补齐应用层完整性、事务、删除影响检查与 reconciliation；clean-slate、canonical schema、
ConnectRPC 等其余决定分别以 [API 手册](05-api-rpc-and-error-contracts.md)、根 AGENTS 与各子仓 ADR 为准。
