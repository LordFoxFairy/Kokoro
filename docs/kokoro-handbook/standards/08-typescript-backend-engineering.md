# TypeScript 后端成熟工程规范

状态：正式团队规范，2026-09-07 修订。框架目标不等于现有子仓已经切换；各仓的实际依赖、代码和验收以本仓 CURRENT 为准。

适用：Kokoro 的 TypeScript 后端服务、BFF 和 worker。本文是唯一 TS 规范；AGENTS 只引用，不复制。
Java 的职责划分与依赖注入经验值得借鉴，但不照搬其包层级、接口实现双份、getter/setter 和继承体系。
“必须/禁止”表示 Kokoro 合并要求；工具语义、企业公开经验、项目约定分别说明，不宣称行业唯一或“100 分认证”。

## 阅读导航

第一次阅读建议按“职责 → 来源 → 目录 → DTO/Mapper → 文件粒度”的顺序，不必从头阅读全部运行治理条款。

| 想弄清的问题                                                     | 直接查看                                                                              |
| ---------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| Controller、Service、Repository、DTO、Model、Mapper 分别做什么？ | [§1.1 职责速查](#11-名词和职责)                                                       |
| 示例来自真实项目，还是团队自己的设计？                           | [§2.1 来源与取舍对照](#21-真实实践与本项目取舍对照)                                   |
| 一个仓库的基本目录是什么？                                       | [§4.1 仓库骨架](#41-默认形态)                                                         |
| 普通业务模块如何放文件？                                         | [§5.1 小模块与 HTTP 职责示例](#51-小模块)                                             |
| 文件越来越多时如何展开子目录？                                   | [§5.2 模块成长](#52-成长模块)                                                         |
| shared/common/commands 可以用吗？                                | [§4.2 公共能力](#42-公共能力怎么放)、[§5.4 Commands](#54-commandsqueries-与-handlers) |
| DTO、Zod、class 会不会重复定义字段？                             | [§6.6 DTO 与 Schema](#66-dto-与-schema)                                               |
| Mapper 放哪、用 class 还是函数？                                 | [§6.7 Mapper](#67-mapper)                                                             |
| 一个 TS 文件什么时候拆、什么时候共置？                           | [§8.4.6 职责判断](#846-判断一个文件承载过多能力的方法)                                |
| 文件名、复数目录、相对 import 怎么统一？                         | [§9 命名规则](#9-文件与目录命名)                                                      |

## 1. 核心决策

```text
按业务能力组织模块
+ NestJS 管理应用模块、依赖注入与生命周期
+ HTTP 使用官方 FastifyAdapter
+ Controller / Service / Repository / Client 优先 class
+ Zod 管理 JSON 边界；Proto 管理 RPC 边界
+ PostgreSQL 为持久事实源；每仓仅一份 canonical schema
+ 严格类型、显式依赖、可验证事务与清晰文件角色
```

- 手写 Service、Repository、Client 的默认实现是 class；同一角色不再随作者偏好混用 factory object、散落函数和 class。
- model 有状态、不变量或行为时优先 class；纯数据仍使用 type/interface/schema inference。
- 工具函数、schema、常量不是业务组件，不为了统一外观包装静态工具类。
- Nest `useFactory` 仍可用于配置、第三方实例和异步初始化；这不代表业务 Service 又可以任意写成工厂对象。
- DDD 用于分析 owner、业务词汇、状态和不变量；不要求出现 `domain/application/infrastructure` 目录。
- Nest 是后端默认目标，不要求 Web UI、SDK、纯工具包或无 HTTP 的小型 worker 套应用框架。
- 现有非 Nest 仓库先完成技术/API/数据设计门，按独立切片切换；本次手册更新不授权同时重写全部子仓。

### 1.1 名词和职责

| 名称                     | 查什么 / 负责什么                                             | 默认表达                                            | 不负责什么                              |
| ------------------------ | ------------------------------------------------------------- | --------------------------------------------------- | --------------------------------------- |
| Module                   | 组件装配、imports/providers/controllers/exports、模块公开边界 | Nest Module class                                   | 业务规则、SQL、重复的手工容器           |
| Controller / RPC handler | 协议参数、经过验证的输入、用例调用和响应                      | Nest Controller / 本仓 RPC adapter class            | 数据库访问、业务事务、核心状态转换      |
| Service                  | 内聚用例、业务授权、事务和副作用编排                          | 构造注入的 class                                    | 自研协议 parser、wire DTO、Row 定义     |
| Repository               | 具名查询、持久化、租户范围、数据库错误归一                    | 封装 ORM/driver 的 class                            | HTTP 状态、用户权限决策、外部网络       |
| DTO                      | API 请求/响应的数据契约                                       | Schema 推导类型；确需 runtime metadata 时派生 class | 数据库操作、业务状态机；不是 ORM Entity |
| Schema                   | 对不可信数据做运行时结构校验                                  | Zod / 已选机器协议 schema                           | 签名验证、授权和并发完整性              |
| Model                    | 业务状态、不变量和合法转换                                    | 有行为时 class；纯数据 type/interface               | I/O、框架装配、HTTP 协议                |
| Mapper                   | 协议对象、内部对象、持久化对象之间的显式转换                  | 纯函数；需注入转换依赖时 class                      | I/O、权限判断、业务状态变化             |
| Client                   | 外部 owner/provider 的协议调用、预算及失败归一                | 依赖成熟 SDK 的 class                               | 对方数据库访问、本仓业务编排            |
| Contract / SDK           | owner 发布的跨进程协议及消费者工具                            | 版本化 artifact / client 包                         | 跨仓共享业务源码或 ORM schema           |

Repository 是职责，不是 ORM 的另一个名字；使用 Prisma 等工具也需要明确数据访问边界。
DTO 是传输契约，Model 是业务对象，Mapper 是转换职责：三者不是必须每次齐全的流水线，也不是 Java 专属。

## 2. 实践依据与取舍

采用的不是“class 越多越成熟”，而是稳定分工、模块封装、显式依赖和经过验证的故障处理。

| 方案                                        | 收益                                                                   | 本项目取舍                                              |
| ------------------------------------------- | ---------------------------------------------------------------------- | ------------------------------------------------------- |
| NestJS + 业务模块 + class 组件              | 原生 DI、模块导出面、Guard/Pipe/Filter/Interceptor、测试装配与生命周期 | 默认目标；减少自研基础装配                              |
| 裸 Fastify + plugin + 手工 composition root | 轻量、显式，适合有既定约定的团队                                       | 合理方案，但不再作为本次 IAM 的目标；已有服务按切片调整 |
| 强制全仓 DDD 四层 + Interface/Impl          | 在部分复杂领域有价值                                                   | 不作为通用树；容易引入空层、类型复制和导航成本          |

Nest 官方提供机制；Google TS 指南提供类型/导出/工具函数经验；公开项目提供组织方式参考。它们没有规定同一棵目录树。
class 默认、命名后缀、目录准入和下述职责文件边界是 Kokoro 团队决定，不能反向说成 Nest 的全部强制要求。

### 2.1 真实实践与本项目取舍对照

**本文目录树是有依据的项目建议，不是某家公司仓库的原样复制。** 下列项目按 2026-09-07 读取到的 commit 固定链接，
只证明对应源码的组织事实，不证明其全部实现适合 Kokoro，更不是性能、安全或版本兼容性认证。

| 真实来源                                                                                                                      | 实际可见结构 / 机制                                          | 借鉴什么                               | 不照搬什么                                                |
| ----------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------ | -------------------------------------- | --------------------------------------------------------- |
| [Nest 官方 starter](https://github.com/nestjs/typescript-starter/tree/c8fb6bc4b01792ce7016a9b0c6bd7f3dbd5f0416/src)           | main、app.module、app.controller、app.service                | 框架入口与组件装配                     | 入门例子没有复杂业务边界，不能当完整服务模板              |
| [Nest Feature modules](https://docs.nestjs.com/modules#feature-modules)、[Providers](https://docs.nestjs.com/providers)       | 业务模块聚合 controller/service/dto；依赖注入与显式 exports  | 模块内聚、class provider、构造注入     | 官方没有规定每个模块必须有 Repository/Mapper/Model 全家桶 |
| [Novu subscribers](https://github.com/novuhq/novu/tree/49e4b308eeba9a5ab86605ee2eac8fd882110e0a/apps/api/src/app/subscribers) | dtos、usecases、utils、query-objects，以及 controller/module | 真实业务模块内可按契约、用例和工具展开 | 不逐字复制其文件名、测试目录、数据库和用例数量            |
| [Vendure core](https://github.com/vendurehq/vendure/tree/523b57304c5850b86069de30a97b723a3f4da284/packages/core/src)          | api、service、entity、common、config、connection             | 成熟工程也可采用不同的职责组织         | 不是全部 Nest 项目都必须使用 modules 或同一套文件树       |

下列明确是 Kokoro 的决定：后端默认 Nest/class；业务优先；集合目录自然复数；common/shared 的依赖区分；
具名 constants/error/mapper 文件按职责展开；现有 SQL-first 与 clean-slate 约束。行业没有统一的目录名称认证。
规范维护时继续分开记录“框架事实、开源实践、项目取舍”，不要把一张合成目录图标成“大厂官方标准”。

## 3. 技术选型与版本

| 能力                     | 默认方向                                     | 实施要求                                                                  |
| ------------------------ | -------------------------------------------- | ------------------------------------------------------------------------- |
| Node / pnpm / TypeScript | 受支持 LTS、最新稳定兼容版本、ESM + NodeNext | 精确版本记录在本仓 manifest/lock/工具链文件，不把手册日期当安装证据       |
| 应用框架                 | NestJS + 官方 Fastify adapter                | 框架主要依赖匹配版本；不用 Express 专用插件冒充 Fastify 兼容              |
| RPC                      | 现有 ConnectRPC + Protobuf-ES                | 保持已确定协议；Connect 不是 Nest 原生 gRPC，见 §11.3                     |
| JSON 校验                | Zod                                          | HTTP、配置、provider 响应、持久化 JSON 使用具名 schema；见 §8.4           |
| SQL                      | PostgreSQL；当前仓按已批准 `pg` + SQL-first  | Repository class 封装访问；ORM 是另一个选型，不是 Repository 的替代概念   |
| JWT/JWS/JWK              | 优先成熟 `jose` 等标准实现                   | 固定算法、issuer/audience/key policy；业务 claims、恢复和轮换仍由本仓负责 |
| Redis                    | node-redis                                   | 只在真实缓存/协调用例中使用，不为“有 Redis”制造业务依赖                   |
| 测试/静态检查            | Vitest、ESLint typed lint、Prettier          | 真实执行，见 §13–14                                                       |

### 3.1 版本治理

1. 每次进入子仓重构或升级，核验 registry、官方 release/security/peer support，记录日期、精确版本和命令。
2. `packageManager` 固定 pnpm 精确版本，直接依赖按统一精确版本策略，提交唯一 `pnpm-lock.yaml`；CI frozen install。
3. Node 本地/CI/镜像同 major，`@types/node` 匹配实际 runtime。最新发布不等于已经兼容，不使用浮动 `latest`。
4. manifest 范围、lock 实际解析、正在运行的二进制分别记录；通过安装不等于 lint/build/启动兼容。
5. 核心替换写 ADR：候选、维护状态、许可证/供应链、故障语义、性能验证、退出路径。升级与无关业务变化分开。
6. 依赖构建显式 allowlist、严格未知构建检查；对 pnpm 对应版本核验 `allowBuilds`/`strictDepBuilds` 的支持。
   不全局放行安装脚本；结合发布观察窗口，紧急安全修复保留具名例外。

### 3.2 公共命令

`dev`、`start`、`format:check`、`lint`、`typecheck`、`test`、`build`、`contract:check` 是统一入口；有数据库才有
`db:apply-schema`。实现命令由仓库记录，禁止复制没有对应脚本的示例并声称通过。

- dev 从源码运行，生产 start 运行已构建 JS；装饰器 metadata、NodeNext、开发执行器和生产编译链必须一致。
- Nest constructor DI 依赖运行时 token/metadata。不要假定现有 tsx/esbuild 开发方式会自动产生与 tsc 相同的装饰器 metadata。
- 核验 `experimentalDecorators`/`emitDecoratorMetadata` 与选定 Nest/TS 组合；也可显式 token，但不靠类型断言解决启动失败。
- 构建同时验证 generated import、package exports、资源复制及真实输出路径；不能仅 typecheck 后运行源码 smoke。

### 3.3 PostgreSQL、ORM 与 Repository

PostgreSQL 是数据库，`pg` 是驱动，Prisma 是 ORM，Repository 是代码职责。Service 用 class 不要求更换驱动，使用 ORM 也仍需业务边界。

当前 SQL 手册固定 `database/schema.sql`。本轮 IAM 保留 `pg`，不是把 Prisma 判为不成熟；未经单独设计不增加第二个 schema/连接池。
以后选 Prisma、Drizzle、Kysely 时必须明确：唯一 schema 的方向、无外键模式的真实限制、参数化/锁/事务、Row 映射、批量查询、
JSON/decimal/bigint、取消、驱动错误、生成与 clean-slate 空库安装。若改变 canonical schema，先一起修订 SQL 手册和本仓 ADR。
ORM 原生 raw query 可以是同一事务中的必要能力；禁止的是另起独立 Pool 导致一个业务事务被拆成两条提交链。

## 4. 仓库级组织

### 4.1 默认形态

以下是有多个业务模块的 Nest 后端**示意**，不是批量创建目录的脚手架：

```text
contract/                         # 本仓机器契约
  proto/
  openapi/
  generated/typescript/           # 有生成链时的推荐唯一输出

database/schema.sql              # 当前 SQL-first owner 才有
src/
  main.ts                         # 启动 Nest、监听、信号；不写业务
  app.module.ts                   # 组合根
  config/                         # 环境装载、schema、typed 配置
  modules/
    <business>/                   # 业务能力
  common/                         # 已有跨模块用途的框架/进程公共组件
  shared/                         # 按需：无框架依赖的稳定公共结构
  utils/                          # 按需：具名纯技术函数
scripts/                          # 生成/验证/空库安装工具，不处理业务请求
sdk/typescript/                   # 有发布消费者时才创建
test/
  unit/
  integration/
  contract/
  architecture/
  smoke/
  fixtures/
  doubles/
```

`common/shared/utils` 都是可选的，角色不同才并存。现有 `server.ts` 也是合理入口名；切换 Nest 时若采用 `main.ts`，
必须一起更改 package/CI/镜像/测试并删除旧入口，不能只是为了命名加转发文件。

### 4.2 公共能力怎么放

| 对象                                        | 推荐归属                                                                             | 依赖边界                                           |
| ------------------------------------------- | ------------------------------------------------------------------------------------ | -------------------------------------------------- |
| Database/Cache/Logging 的连接与生命周期     | `common/database`、`common/cache`、`common/logging`，有模块+资源类等实际内容才建目录 | 不放业务 SQL、key 或权限规则                       |
| HTTP 全局错误 filter、请求上下文、公共 Pipe | `common/http/` 或更准确主题                                                          | 可以依赖框架；不反向引入所有业务 Service           |
| 多模块纯基础类型/错误结构                   | `shared/<subject>` 或具名文件                                                        | 不依赖 Nest/数据库，不包含 Tenant/Session 事实副本 |
| 纯编码、时间格式等工具                      | `utils/<subject>.ts`                                                                 | 无 I/O、无隐藏状态，先用标准库或成熟库             |
| 真正全局常量                                | `constants/<subject>.constants.ts`                                                   | 有明确 owner；不收集所有模块业务值                 |
| 业务模型集合                                | 所属模块的 `models/`                                                                 | 全局 `models/` 只在确有共同生命周期时评审采用      |
| 外部 owner SDK 的业务适配                   | 单模块内 client；多模块共用时 `integrations/<owner>/`                                | 不复制 wire DTO、网络重试或对方数据库模型          |

全局目录名不是禁词。进入公共层要说明公共职责、实际消费者、稳定语义、维护 owner 和单向依赖，并提供与职责相称的验证。
已有多个独立消费者是复用证据，不是“凑够两处调用才允许”的门槛：进程级日志、错误出口、请求上下文等从第一处装配起就有公共职责。
相反，Tenant 的权限规则即使有十个调用方，仍由 Tenant owner 维护，不因此搬进 shared。

`common` 与 `shared` 的上述区分是本项目约定，不是 Nest 保留目录名；若两个目录承担同一职责，只保留一个。
模块内部也可用 `shared/` 承接多个子能力真正共有的结构，但优先使用能说明主题的名字，且不因“以后可能复用”提前上移。
shared 不是绕开模块边界的通道：在本项目约定下不 import 业务模块内部文件、不注册业务单例、不读取环境、不执行数据库或网络 I/O。
业务组件的复用通过所属 Nest Module 的显式 exports/imports 完成；不靠 `@Global()` 或万能 SharedModule 让所有依赖隐式可见。
`runtime/` 也并非错误名称，但不是必需层；Nest 服务默认用具名模块/资源 provider 管理生命周期，避免再建一套平行 runtime 容器。

### 4.3 多进程与插件

只有真实独立部署/扩缩容需求才新增 worker/HTTP/RPC 进程入口。两个 listener 不等于两个进程或两套 Pool。
Fastify plugin 仅用于真实框架适配；业务 Service 不包一层 plugin。Nest 模块元数据是有效职责，不因文件短就删除。

## 5. 业务模块和子目录

### 5.1 小模块

```text
modules/sites/
  sites.module.ts
  site.controller.ts              # 有 HTTP 时
  site.service.ts
  site.repository.ts              # 有本仓持久化时
  site.schema.ts                  # JSON 边界及其推导类型
  site.types.ts                   # 语义不同的内部数据，确有需要才建
  site.error.ts                   # 有独立业务错误时
```

不是每个模块都必须有这些文件。Controller 默认调用 Service；无业务规则的纯投影可直接注入具名 Query 组件，
但不能借此在入口写 SQL/授权/事务，也不为凑层级建立全原样转发的 Service。

#### 5.1.1 HTTP 模块的职责文件示例

当一个模块已有多个请求/响应契约时，展开 DTO 集合能让查阅更直接。下面用 Site 表达职责，并非 IAM 当前代码树，
也不授权增加 Site 业务；框架不要求一次性生成图中的所有文件。

```text
modules/sites/
  sites.module.ts                 # 装配与公开 provider
  site.controller.ts              # HTTP 协议入口
  site.service.ts                 # 内聚业务用例
  site.repository.ts              # 本仓数据访问
  site.mapper.ts                  # 确有输入/响应表示差异时

  site.model.ts                   # 确有业务状态和行为时
  site.constants.ts               # 本模块固定值、限制
  site.error.ts                   # 本模块业务异常

  dtos/
    create-site.dto.ts            # 创建请求的单一契约
    update-site.dto.ts            # 更新请求；不机械 Partial<Create>
    site-response.dto.ts          # 显式公开字段，不透传 Row
```

这里 `.dto.ts` 命名的是 **API 契约职责**，不要求一定是手写 class。Kokoro 的 code-first JSON DTO 可以在该文件
定义一份 Zod schema 并导出推导类型；一般配置、cursor、provider 等非 API 数据继续用 `.schema.ts`，具体规则见 §6.6。
由小模块的 `site.schema.ts` 展开为 `dtos/` 时移动原有定义及引用，不保留两套可编辑的相同 shape。
采用 Proto/OpenAPI schema-first 的服务仍以机器契约为唯一事实源，不为套这张图重新手写 DTO。

查请求看 Controller/DTO；查业务看 Service/Model；查数据看 Repository；查表示转换看 Mapper；
查固定值和异常看 Constants/Error。这个定位习惯比“文件必须分成多少层”更重要。

### 5.2 成长模块

先按子业务，再按角色组织；当同类文件已经形成稳定集合时，可展开 `services/`、`repositories/`、`models/`、
`schemas/`、`errors/` 等复数目录。模块根不无限平铺几十个不同职责文件。

```text
modules/authentication/
  authentication.module.ts
  authentication.rpc.ts
  sessions/
    session.service.ts
    session.repository.ts
    session.model.ts
    session.types.ts
    session.error.ts
  magic-links/
    magic-link.service.ts
    magic-link.repository.ts
    magic-link.schema.ts
    deliveries/                    # 真实投递生命周期/worker 子能力
```

这是组织原则，不是 IAM 的完整目标树；IAM 自己的技术方案决定实际对象。单文件子目录没有近期明确职责集合时不创建，
但也不为了“最少文件”把 schema、错误、业务类、SQL 合在一起。

#### 5.2.1 从平铺到子能力的展开条件

| 当前信号                                       | 优先调整                                                                | 避免的做法                                        |
| ---------------------------------------------- | ----------------------------------------------------------------------- | ------------------------------------------------- |
| 一个小业务，有少量职责文件                     | 模块根保留具名角色文件                                                  | 每种角色只有一个文件也先套一层目录                |
| 请求/响应契约已经形成集合                      | 展开 dtos；每个文件表达一个契约或紧密关联契约族                         | 全仓共用一个 dto.ts，或 schema/DTO 双写           |
| 用户资料、凭据、邀请等流程分别演进             | 在同一业务 owner 下按 profiles/credentials/invitations 等真实子能力聚合 | 一个全能 Service，或直接拆成多个微服务            |
| 同一子能力中已有多组 Service/Repository/Mapper | 按持续职责集合展开 services/repositories/mappers 等目录                 | 几十个角色文件永远平铺，或固定“第N个文件必须搬家” |
| 多模块需要同一业务能力                         | 从该 owner 导出公开 Service/Query                                       | 把整个业务模型复制到 shared                       |

子能力名称按实际业务确定，上表不是必建清单。Service 的多个内聚方法可以共存；只有独立变化原因出现时才拆，
不是每个 CRUD 方法都配一个目录、一个 Command、一个 Handler。移动时一并更新导出、调用、测试与文档，旧路径退出。

### 5.3 模块公开面

- Nest `imports/exports` 控制 provider 可见性，TS 显式导出控制源码 API；两者不是同一检查，需要同时约束。
- 跨模块调用公开 Service/查询能力；不 deep-import 对方 Repository、Row、私有 schema。
- 多模块同库事务通过批准的事务装配组件连接公开的事务能力，不让每个 Service 自己开连接。
- 高频双向调用/循环注入先重画边界，不默认靠 `forwardRef`、service locator 或事件总线遮掩循环。
- 一个模块不是一张表；不存在接口/生命周期的机制不升格为一级模块。

### 5.4 `commands/`、`queries/` 与 `handlers/`

这些目录允许使用；是否采用取决于用例组织和分发机制，不是名字看起来“高级”或“复杂”。

| 场景                                   | 建议组织                                                                        | 不额外引入什么                                     |
| -------------------------------------- | ------------------------------------------------------------------------------- | -------------------------------------------------- |
| 普通 CRUD，一组内聚操作由 Service 完成 | 具名 Service 方法；内部输入按需放 `.types.ts`，JSON 输入以 schema 推导          | 不为每个方法复制 DTO、Command、Handler 三层        |
| 多个稳定写用例需要分别命名、审查或组合 | 模块内 `commands/` 保存具名命令输入；执行由明确的 Service 或用例组件负责        | 目录存在不代表必须安装 CQRS 包                     |
| 已有真实 CommandBus/QueryBus 分发需求  | 使用官方 `@nestjs/cqrs`；Command/Query 与 Handler 分文件，Handler 作为 DI class | 不自研另一套 command bus，不同时保留重复的执行入口 |
| 消息队列或跨进程命令                   | wire schema 归 owner contract；consumer/processor 校验后调用应用用例            | 不把内存 Command class 直接当网络协议或持久化格式  |
| 构建、生成、运维 CLI 命令              | 仓库 `scripts/` 或有独立入口的 CLI 包                                           | 不混入业务 `commands/`                             |

采用 CQRS 时，可在已有业务模块中按下列方式组织；这是局部示例，不是每个模块的必选模板：

```text
commands/
  create-site.command.ts           # 操作意图与只读输入，不执行 SQL
  create-site.handler.ts           # 对应该用例的编排 class
  disable-site.command.ts
  disable-site.handler.ts
```

Command/Handler 配对共置有利于按用例阅读；同类 Handler 已形成集合时也可使用独立 `handlers/`，模块内选定一种即可。
此处保留 `.command.ts` / `.handler.ts` 是为了区分相邻文件角色，不是机械消除路径中的一切重复词。
正式 CQRS 的 Query 同样使用 `.query.ts` 与 `.handler.ts`；模块技术方案区分 Query 消息和直接执行 SQL 的查询组件。

- 普通命令输入可用 readonly 结构类型；依赖 Nest bus 的运行时类型身份时用 class，即使它只携带字段也有实际职责。
  这属于 §8.2 的明确例外，不是为了装字段而使用 class。命令类与 Handler 分文件，不能把执行方法塞进输入对象。
- 同一用例只能有一处编排权威：Handler 可以直接编排 Repository/Model，也可以调用已有 Service；后一种情况下
  Handler 只负责分发适配，不再复制校验、事务与业务规则。不要为了凑层数同时创建空转发 Service 和 Handler。
- HTTP/RPC 调用与内部调度都需经过同一业务授权和事务边界；不能因为换成 bus 就跳过受信上下文或幂等校验。
- CQRS 不要求独立数据库或 Event Sourcing；Nest 的内存 bus 本身不提供持久队列、崩溃恢复或 exactly-once 保证。
  涉及异步可靠交付时另行设计 receipt/outbox/消费重试，不从目录名推断已经具备这些能力。

机制依据见 [Nest CQRS](https://docs.nestjs.com/recipes/cqrs)；采用范围和目录粒度由本仓设计决定。

## 6. class 与职责

### 6.1 应用组件

| 角色                     | class 负责                                  | 不负责                                        |
| ------------------------ | ------------------------------------------- | --------------------------------------------- |
| Controller / RPC handler | 协议映射、已校验输入、Service 调用与响应    | SQL、业务状态机、外部 provider 编排           |
| Service                  | 内聚用例、授权决策、事务边界、结果语义      | 手写 JWT/JSON parser、环境读取、wire/Row 定义 |
| Repository               | 具名查询/写入、driver 错误归一、持久化映射  | HTTP 状态、用户权限决策、外部网络             |
| Client                   | provider/owner SDK 调用、预算、协议失败归一 | 本仓业务状态机、跨 owner 数据访问             |
| Model                    | 不变量、受保护状态、合法转换                | 网络/数据库访问、框架装饰器                   |
| Worker / Processor       | 消费、claim/ACK、停止接活与调度业务用例     | 偷藏第二份核心业务规则                        |

手写 Service/Repository/Client 用 class；worker 等有依赖和生命周期的组件同样优先 class。
单个组件只有一个实现时，直接注册/注入具体类；不默认生成 `IRepository`、`RepositoryImpl`、`BaseRepository<T>`。

### 6.2 构造注入与生命周期

- 依赖用构造函数 `private readonly` 注入，业务方法不 `new` Repository、Client 或 Pool。
- Service 的 Nest `@Injectable()` 等 DI 元数据属于允许的框架装配；禁止的是 HTTP request、Connect generated、ORM/driver 类型穿透业务参数。
- type/interface 在运行时消失；抽象能力需要 token 时显式注册。只为确有多个实现/隔离需求的能力定义窄接口或抽象类。
- 单例不保存当前请求 tenant/actor/token。可信上下文显式传参，或使用有严格生命周期/传播测试的上下文机制。
- 事务绑定 Repository 由事务组件在 callback 内创建并释放，不把 PoolClient 写回单例字段；构造函数一般不启动 I/O。
- 只依赖声明的公开方法，少用继承；测试通过 Nest overrideProvider 或明确结构替身，不复制生产实现。

### 6.3 Service

Service 默认一个 class，方法可以覆盖一组内聚 CRUD 或生命周期动作，不是每个操作都创建一个 UseCase 文件。
有独立复杂流程时再拆另一个 Service；共享的步骤若只是当前算法私有部分，可作为 private method。
不因长度尚未超标就混入 codec/schema/Error；也不把散落函数原封不动包入一个全能 class。

### 6.4 Repository

Repository class 封装选定 ORM/driver，方法表达实际数据能力。显式 tenant、字段选择、排序和返回空值语义。
SQL/必要 raw query 属于 Repository/Query；独立 Row 结构和复杂映射放具名 Row/mapper 文件，ORM 能推导时不再手抄 Row。
同一表只保留一个 writer；跨表聚合查询合理，但不能因此永久吞并其他业务能力的全部写入。

### 6.5 Client、Cache、Publisher

有依赖、状态或 I/O 生命周期的业务适配优先 class。用成熟 SDK/client 而不是重复造 HTTP/JWT/Redis 驱动。
包装只增加本仓真正需要的认证、错误、预算或业务适配，不为每个 SDK 方法创建同名转发 wrapper。
外部 SDK 类型停在 Client 边界；业务只接收所需语义，不拿 `Record<string, unknown>` 当通用返回结果。

### 6.6 DTO 与 Schema

DTO 描述传输数据，Schema 描述并验证其结构，二者可以共享一个定义；它们不是必须分别手抄的一对对象。

| 情形                                | 唯一可编辑事实源与文件角色                           | 使用方式                                                              |
| ----------------------------------- | ---------------------------------------------------- | --------------------------------------------------------------------- |
| 小型 code-first JSON 边界           | 少量紧密相关定义可在 `<subject>.schema.ts`           | 导出 schema 和推导 DTO 类型                                           |
| 已形成集合的 code-first HTTP DTO    | `dtos/<operation>.dto.ts`，文件中定义对应 Zod schema | `CreateSiteDto` 等类型从该 schema 推导；不再建同字段的 schema 文件    |
| Nest 集成确需 DTO class metadata    | 同一 schema 派生的 DTO class，与该契约共置           | 使用经过验证的 bridge；不再手写另一套字段装饰器和约束                 |
| Proto / OpenAPI schema-first        | 本仓 contract 的机器定义                             | 使用生成类型/验证器；适配层仅处理真实语义差异，不维护第二份输入 shape |
| 内部 Service 参数、配置或持久化 Row | 各自的 types/config/row/model 职责                   | 不因为是对象就全部命名 DTO                                            |

- schema 与其推导 type 同文件是同一事实，不是“一个 TS 什么都有”；此文件不包含 Service、SQL、密码算法或业务权限判断。
- `z.infer` / `z.output` 表达解析后的类型，`z.input` 表达解析前类型；有 transform/coerce/default 时不能把两者混为一谈。
  输入经过实际 parse 后再调用业务；标注 `CreateSiteDto` 或 `as CreateSiteDto` 本身不会验证 JSON。
- 新增与更新的字段语义分别设计：省略表示不修改，null 是否清空由契约明确；只读字段、租户和身份字段不靠 `Partial` 自动放开。
- 响应只暴露允许的字段；DTO 类型声明和 Zod 校验都不自动完成响应脱敏。显式 Mapper/序列化与响应契约测试共同验证。
- Mapper 在边界把 wire 名称转换为内部参数；同语义、同表示的数据不机械复制 DTO/Command/Domain/Row 多层结构。
- Nest 的 class DTO＋ValidationPipe 是框架支持的路线；本项目已选 Zod，接入与 OpenAPI/metadata 行为需要明确验证，
  不把 ValidationPipe 当作自动运行 Zod，也不在同一输入上再维护 class-validator 的同字段约束。

机制依据：[Nest Validation](https://docs.nestjs.com/techniques/validation)、[Zod 类型推导](https://zod.dev/basics#inferring-types)。
DTO 文件的目录与后缀是团队约定，选定后在模块内一致执行，不为外观来回改名。

### 6.7 Mapper

Mapper 负责明确的表示转换，不负责业务决策，也不是每两层之间都必须创建的中转站。

| 真实差异                                        | Mapper 负责                             | 归属                      |
| ----------------------------------------------- | --------------------------------------- | ------------------------- |
| 请求 `site_key` 与内部 `siteKey`                | 显式字段映射，使用已经解析的输入        | 模块协议边界              |
| 内部 Date 与响应 UTC 字符串；内部对象含敏感字段 | 明确时间表示、字段白名单、null/省略语义 | 模块响应映射              |
| 数据库可空字段、存储表示与业务 Model 不同       | 持久化转换、调用合法重建入口            | Repository 所属持久化职责 |
| 字段、类型、语义本来相同                        | 不增加无意义复制                        | 直接使用语义合适的数据    |

简单模块可使用具名 `<subject>.mapper.ts`；真实出现请求/响应和持久化两种不同演进方向时，再拆
`<subject>-response.mapper.ts`、`<subject>-persistence.mapper.ts` 等明确角色，或在已有边界目录中放置。
不要让一个全局 Mapper 同时依赖全部业务 Model、ORM、HTTP 和其他 owner 的 SDK。

- 无依赖的确定性映射优先具名纯函数；需要注入转换策略或配置时可用 class。纯映射不包装静态工具类。
- Mapper 不读取环境、查库、发请求、判断权限、修改状态或隐式创建新业务对象；这些仍属于各自组件。
- JSON、DTO 与 Row 不是 class Model 实例，不能依靠类型断言“转成”Model；有行为的对象走明确构造/恢复入口。
- 字段白名单、时间精度、bigint/decimal、缺失/null、未知枚举等按实际差异测试；禁止一个通用 object spread 冒充边界设计。

## 7. class 风格示例：看职责，不复制脚手架

以下两个代码块分别属于不同文件，仅展示 DI，不构成完整鉴权/API 实现。

`modules/sites/site.service.ts`：

```ts
import { Injectable } from "@nestjs/common";
import { SiteRepository } from "./site.repository.js";
import { SiteNotFoundError } from "./site.error.js";
import type { Site } from "./site.types.js";

@Injectable()
export class SiteService {
  constructor(private readonly siteRepository: SiteRepository) {}

  async getActive(tenantId: string, siteId: string): Promise<Site> {
    const site = await this.siteRepository.findActive(tenantId, siteId);
    if (!site) throw new SiteNotFoundError();
    return site;
  }
}
```

`modules/sites/sites.module.ts`：

```ts
import { Module } from "@nestjs/common";
import { DatabaseModule } from "../../common/database/database.module.js";
import { SiteService } from "./site.service.js";
import { SiteRepository } from "./site.repository.js";

@Module({
  imports: [DatabaseModule],
  providers: [SiteService, SiteRepository],
  exports: [SiteService],
})
export class SitesModule {}
```

`DatabaseModule` 在实际仓中提供并导出数据库 provider，Repository 构造注入它；其他模块只导入 SitesModule 的公开 Service。
service 文件不再顺手定义 `Site`、`SiteNotFoundError`、正则、分页值、schema、Row。纯模型与异常也不因为 Nest DI 就加 `@Injectable()`。

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

| 构造             | 使用原则                                                                |
| ---------------- | ----------------------------------------------------------------------- |
| class            | 默认 Service/Repository/Client；有不变量或行为的 Model；业务异常        |
| type             | schema inference、只读数据、判别联合、字面量与函数签名                  |
| interface        | 对象能力、框架扩展、确有必要的依赖契约                                  |
| as const + union | 简单有限值集合，常量及其类型来自一处                                    |
| enum             | 可以使用有明确 runtime 需求的字符串 enum；generated enum 保留生成器输出 |

普通数据默认不写空 class/getter/setter；确需运行时类型身份或框架 metadata 的 Command/Query/DTO class 属于明确例外，
见 §5.4 与 §8.4.1.1。业务组件不再以“TS 原生”为理由放弃 class 与依赖管理。
`Readonly<T>` 是浅只读的编译期约束，不等于运行时深冻结。外部数据用 unknown 接收并验证，unknown 不是 any 的同义词。

### 8.3 导出与复杂度

默认具名导出、纯类型用 `import type`；DI 用作运行时 token 的 class 正常导入，不能误改成 type-only。
只导出真实消费者需要的符号。禁止宽泛 any、双重断言、非空断言和 `@ts-ignore` 隐藏边界缺陷。
编译错误负例可用具名说明的 `@ts-expect-error`；`satisfies`/schema inference 优先于强制转换，不堆叠难读类型体操。

### 8.4 一个手写 TypeScript 文件只承载一个主要变化原因

这是职责规则，不是“一文件只能出现一种 TS 语法”。**class 优先与职责分离同时成立**，不是把常量、schema、错误和 SQL 搬进 class 就算完成。

#### 8.4.1 类型、schema、class、service 的放置规则

| 内容                      | 默认文件                                                 | 边界                                                               |
| ------------------------- | -------------------------------------------------------- | ------------------------------------------------------------------ |
| Service/Repository/Client | `<subject>.service.ts` / `.repository.ts` / `.client.ts` | 一个主要 class 及其职责内方法                                      |
| 业务 Model                | `<subject>.model.ts`                                     | 受控构造、真实行为与状态；无 I/O                                   |
| 内部结构/组件选项         | `<subject>.types.ts` / `.options.ts`                     | 有实际消费者才存在；优先构造注入减少 options 大包                  |
| JSON schema / API DTO     | 非 API 使用 `.schema.ts`；HTTP DTO 集合见 §6.6           | schema 与推导类型允许同文件；不在 schema/DTO 文件中双写相同 shape  |
| 模块常量                  | `<subject>.constants.ts`                                 | 版本、限制、业务固定值，不混入 Service                             |
| 状态集合                  | `<subject>.status.ts` 或相应 constants/schema            | 选一处事实源；不再复制 enum/union/schema 三份                      |
| 错误                      | `<subject>.error.ts`                                     | 异常类及错误语义；错误码表独立增长/被多角色使用时 `.error-code.ts` |
| 持久化形状/映射           | `<subject>.row.ts` / `.mapper.ts`                        | 真实类型差异或复杂映射才建，不手抄 ORM 推导类型                    |
| 协议 codec                | `<subject>.codec.ts`                                     | 编解码算法；schema/公开配置/业务指纹按各自职责拆出                 |
| 纯技术工具                | 具名主题文件                                             | 纯函数及紧密相关的私有算法细节                                     |

#### 8.4.1.1 校验与 Model

HTTP、环境变量、第三方响应、持久化 JSON 使用具名 Zod schema；Proto/RPC 使用 Proto + Protovalidate。
一个输入只能有一个可编辑 shape 事实源，不再用一套 class-validator 与另一套 Zod 同时定义同字段约束。

```text
不可信输入 -> 协议/schema 校验 -> 具名内部输入 -> Service -> 有行为的 Model / Repository / Client
```

- `z.infer` 不再手写同形 DTO；确需 Nest DTO metadata 时选择 schema-derived bridge，并验证运行时和 OpenAPI，避免重复装饰器字段。
- UUID、UTC 时间、数值范围等复用已有 schema API；只有更严格业务子集才加具名 refinement，不散落复制正则。
- Zod 只证明结构，不证明签名、身份、权限、引用存在或并发正确性。
- 解析重构保留缺失/null、精度、严格/宽松对象、coerce、默认值、字节上限、错误码和脱敏语义。
- union narrowing、`instanceof Error`、库适配的具名 type guard 是正常 TS；禁止的是在业务代码反复猜外部对象形状，不做全文 `typeof` 禁令。
- schema 负责合法输入，Model 方法保护合法状态转换；普通 JSON 不是 class 实例，不能用 `as Model` 伪造方法和不变量。

#### 8.4.1.2 角色文件硬边界

Service/Repository/Client 默认是 **imports + 一个主要 class**。独立顶层 options/type、业务常量、enum、schema、Error class、
codec 不顺手放入其中；按上表有明确 owner 的职责文件承接。构造注入已能表达依赖时不再额外声明一份 dependencies 对象。

允许的紧密共置：schema + 推导类型；同一错误概念的少量 code/type + Error；常量集合 + 其 union；纯工具函数 + 算法私有细节；
方法内部局部 const。SQL 文本可以留在 Repository 方法内；大段可读 SQL 本身不是业务职责混杂。

这些例外不授权 Service 携带独立 schema/错误体系，也不授权 cursor 把管理授权范围计算、key 配置、payload schema 和签名算法堆成一体。
遇到多个独立职责，即使只有 80 行也拆；一个清晰 schema/异常/模块声明只有 10 行仍可独立，不再用“少于 20 行必须合并”抵消职责规则。

#### 8.4.2 常量、有限值与默认值

- 模块协议版本、业务限制、公共默认值放具名 constants/schema/config；运行配置由 typed config 注入，不改成源码魔法数字。
- 一个方法里的计数、布尔分支或算法局部常量保留方法内；不是每个数字都需要全局常量。
- 共享先找 owner，不因为出现两次就全局化。状态/code 的 union 从同一个常量/schema 推导，generated enum 不人工复制。
- 禁止把所有常量、类型、错误归入全局单文件；集合目录中的文件也必须有主题名。

#### 8.4.3 Model 的职责

当构造有效性、状态转换、规范化表示或敏感状态需要集中保护时，使用 class Model；私有状态由有业务含义的方法修改。
DTO/Row/配置通常是数据，类型推导或结构类型即可。Repository 恢复 Model 必须走明确重建规则，不误触发“创建新业务对象”的副作用。
Model 不依赖 Nest decorator、ORM 或网络；业务规则也不藏进 DTO transform。

#### 8.4.4 审查反例

- `tenant.service.ts` 同时定义正则、分页值、输入 schema、上下文类型、Error 和业务类：职责混合。
- 为每个局部常量建一文件、为每个 CRUD 方法建 UseCase、每层复制同字段 DTO：机械碎片化。
- 把上述所有内容放进 `TenantManager` 的 static 方法：只是换外观，职责问题仍在。
- 因为当前测试锁死文件清单就坚持旧目录：应把门禁改为依赖/导出/职责正反例，不用测试保卫历史偶然结构。

#### 8.4.5 公共对象

公共框架能力进入 common，无框架共享结构进入 shared，纯工具进入 utils；见 §4.2。
Tenant/Session/Permission 即使被多个模块调用，仍是业务 owner 的模型，不复制到全局 models。

#### 8.4.6 判断“一个文件承载过多能力”的方法

先列职责再数行数；`const`、`type`、`class` 是语法，不是单独的架构层。下面的判断必须能在具体调用和依赖中得到验证：

| 判断问题                     | 可以共置                                             | 应拆分的信号                                          |
| ---------------------------- | ---------------------------------------------------- | ----------------------------------------------------- |
| 修改原因是否一致？           | 同一 schema 及其推导类型随输入契约一起变             | 分页协议、签名密钥策略与租户状态规则分别演进          |
| 是否同一职责的完整算法？     | codec 的编码函数及私有字节处理 helper                | Service 顺带实现通用 JSON canonicalization 或密码算法 |
| 是否同一组用例？             | SiteService 的创建、更新、停用及私有业务步骤         | 同一 class 同时管理登录、租户、计费和邮件投递         |
| 消费者是否需要整份公开能力？ | 某个错误类及该错误专属的小型 code/type               | 其他模块为用一个类型而 import 整个业务 Service 文件   |
| 依赖和测试装配是否一致？     | Repository 的 SQL 与该查询结果的直接映射             | 测试纯规则却必须配置 HTTP、密钥、数据库和队列         |
| 文件的真实角色是什么？       | Nest Module 的注册、imports 与 exports；测试场景装配 | 在 app.module/main 等装配文件内实现业务规则           |

审查顺序：先明确 owner/主要角色，再列独立变化原因，最后选择拆文件、建子能力目录或保留私有方法。
若一个文件已同时承担 Service、schema、错误体系、codec、SQL 访问，直接判定需要拆分，行数短也不例外。
若只有同一 schema + `z.infer`，或方法内几个局部常量，不按语法种类强拆。生成代码遵循生成器；测试可共置场景所需的局部样本。
角色文件仍遵守 §8.4.1.2 的团队默认，以上不是放宽为“只要作者觉得相关就全塞进去”。

拆分验收要检查公开 import 和调用链：无循环、无重复类型/规则、旧路径已删除、职责内测试可独立执行。
AST/Lint 可检查 import 和角色组合；“是否同一变化原因”仍需人工审查，不靠文件名、导出数量或行数单独打分。

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
.dto.ts
.model.ts
.types.ts
.constants.ts
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
.handler.ts
.interceptor.ts
```

命名语法固定为：

- 连字符连接业务词：`scheduled-task`；点号分隔文件角色：`scheduled-task.repository.ts`。
- `use-cases/` 已经表达角色，文件直接使用动词-对象：`authorize-payment.ts`，不写 `authorize-payment.use-case.ts`。
- `domain/` 内的核心对象使用 `payment.ts`；其他角色仍显式使用 `payment.policy.ts`、`payment.error.ts`。
- 非 CQRS 模块的 `*.query.ts` 表示优化的只读数据访问/投影；正式 CQRS 的 Query 消息/Handler 按 §5.4 命名。
  同模块出现两种查询角色时，在技术方案和位置上明确区分，不让同一文件兼任消息与数据库访问组件。
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

`<subject>.ts` 只保留给“模块唯一且足够清晰的中性业务对象”。当类型、model class、schema 或错误已经各自拥有独立
变化原因时，使用 `.types.ts`、`.model.ts`、`.schema.ts`、`.error.ts`，不要继续使用一个没有角色的长文件。

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

行数是复核信号，不是公司级通用定律：普通手写文件约400行、方法约60行、模块根约12个文件时主动检查职责与阅读成本。
安全边界即使短也可独立；一个清晰SQL/状态表不因长就机械拆分。合并门阻断的是混合职责、循环依赖、复杂且不可测试的分支，
不是“第401行出现”。确需保留复杂实现时记录owner、理由、测试与后续收敛条件；生成物单独对待。

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

本仓 dev/test/installer 必须显式实现上述装载顺序，并用优先级测试锁定；不依赖 IDE 恰好注入环境。

### 10.2 唯一读取点

环境读取集中在 `config/` 的一个明确入口；schema 位于 `environment.schema.ts`，装载函数只处理来源/映射，
Nest 配置 provider 对外提供已验证的具名只读配置。Service 不直接读 process.env，也不散落 `config.get<string>('任意键')`。

Nest ConfigModule、Node `--env-file`、dotenv 只选一个负责文件装载，测试验证 §10.1 的优先级。
选择 Nest envFilePath 时按框架“较前文件优先”语义实现本项目 local 覆盖规则，不照搬 Node 多文件参数次序。
生产显式禁用仓库 env 文件；配置缺失/非法在启动时失败且脱敏。测试不读取开发 `.env.local`。
密钥来自 secret 引用和 resolver，不硬编码、不打印；时间、重试、分页、连接池预算说明单位和上限。

## 11. API、HTTP/RPC、错误与 SDK

### 11.1 契约与 HTTP

契约归本服务 owner。public HTTP 以批准的 OpenAPI 为事实源；internal HTTP 可以 schema-first 或 code-first，但只维护一份字段定义。
JSON 使用 snake_case，内部用 camelCase；显式映射响应，避免 Row/ORM model 直接作为公开 API。

Nest 正常请求链是 Middleware → Guard → Interceptor 入站 → Pipe → Controller/用例 → Interceptor 出站；
未捕获异常交给匹配的 Filter，不把 Filter 当成每次成功请求都会执行的处理步骤。
Guard 先于 Pipe，不能假定已经拿到 Pipe 解析的 body；业务授权和事务内有效性重验仍在 Service/用例。
配置 Nest ValidationPipe 并不会自动执行 Zod，需明确 Zod Pipe 集成。
OpenAPI 生成器不保证自动识别 Zod：选定集成后以实际生成/响应测试证明；schema 解析也不自动等于输出序列化/脱敏。

成功/错误 envelope、版本、分页、幂等、权限和事件遵守 [API 专项](05-api-rpc-and-error-contracts.md)。
health、JWKS、文件、SSE、HEAD、204 等使用各自协议，不统一套 JSON envelope。

### 11.2 错误 owner

| 对象                              | owner                                                       |
| --------------------------------- | ----------------------------------------------------------- |
| Tenant/Session 等业务 Error class | 所属模块 errors 或具名 `.error.ts`                          |
| 可共享的基础错误形状              | shared/errors，仅确有跨模块用途                             |
| HTTP 错误到 status/envelope       | common/http 的 Filter/mapper                                |
| Connect 错误到 code/details       | RPC 集成边界的 interceptor/mapper                           |
| SDK ApiError                      | SDK 自己的错误类，从 wire code 构造，不 import 服务端 class |

错误码集合是数据，mapper 是转换逻辑，Error class 是异常行为，三者不是用 enum 相互替代。
固定业务码、可公开信息和可重试语义；未知错误记录脱敏 cause，统一服务端失败，不把 SQL/stack/secret 原样传给消费者。

### 11.3 Connect 与 Nest

Connect 的官方 Fastify 插件可注册 RPC，但它不是 Nest 的原生 gRPC transporter。
直接注册的 Connect route **不自动经过 Nest Guard/Pipe/Filter/Interceptor**，即使业务 Service 是 Nest provider。

继续使用 Connect 的仓库必须明确：

1. 一个 Nest 容器管理 Service/Repository/资源；Connect handler 从已装配实例调用，不再手工 new 第二份 Service。
2. RPC 自己的 Connect interceptor 负责服务身份、上下文、Protovalidate、错误、deadline/取消及日志；公共安全业务服务可复用。
3. Nest HTTP 与 Connect RPC 的同等安全策略分别测试，不能用 HTTP Guard 单测冒充 RPC 已认证。
4. listener/HTTP2/health/端口、启动失败清理、worker drain 和 pool 关闭要有真实进程证据。
5. 接入官方插件还是继续使用官方 connect-node listener，由本仓 ADR 决定；不为套装饰器手写一套 Nest transporter。

`*.rpc.ts` 是本项目 Connect 适配角色，不伪装成能自动触发 Nest gRPC 装饰器的 Controller。

### 11.4 Generated

`generated` 表示可再生文件，不是业务层。默认推荐仓库根 `contract/generated/typescript/`，现有 `src/generated/` 在切片完成前仍是当前事实。
只保留一个 output；移动要同步生成配置、provenance、import、tsconfig rootDir/include、package exports、build/start/SDK 和 drift gate。
不手改生成文件或把独立生成依赖当作无用目录删除。Proto package/import 的命名需求与输出位置分开评审。

### 11.5 SDK

owner 有稳定消费者时发布版本化 SDK；当前无发布链的仓库不能仅凭 generated 目录就声称 SDK 完成。

```text
contract/proto + contract/openapi -> 唯一 generated artifact
                                       -> 服务端协议适配
                                       -> sdk/typescript -> 消费方业务适配
```

SDK未发布前消费者可使用固定版本的owner-generated artifact，不需要等待空壳SDK。
SDK 的公开 Client 优先 class，提供 endpoint/auth/deadline/AbortSignal/request ID、经过证明的重试和错误归一。
直接复用生成的 wire types，不复制服务器 Model/Row/DTO；SDK 错误独立于服务端 class。
内部调用官方 generated factory 是合理实现细节，不要求修改生成代码变成 class。

包必须有受控 exports、semver、contract digest/provenance、构建安装后的 consumer contract test；
请求失败不能自动生成新的幂等键，同一逻辑重试保留原身份，遵守结果未知和重放窗口。
服务端不反向 import 自己的 SDK；消费者不复制一份认证/序列化/重试实现。无消费者时不创建空 SDK 工程。

## 12. 事务、缓存、错误与可靠性

### 12.1 事务边界如何注入

多步写入由 Service/use case 决定事务边界，但不接触 `pg.PoolClient`。在具名事务类型文件定义模块专用 callback shape，由事务 Service class 提供：

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

错误按四个边界管理：

`ModuleErrorCode` 表示模块内部业务标识，`WireErrorCode` 表示 owner contract 的契约机器码；此处是角色称谓，不要求新建这两个名字的
枚举、公共目录或重复错误表。内部更细粒度错误由 transport 映射到 wire code；wire 枚举单一事实源为 Proto/OpenAPI，SDK 只消费该契约。

| 层级         | 位置                                                        | 责任                                                                        |
| ------------ | ----------------------------------------------------------- | --------------------------------------------------------------------------- |
| 全局基础错误 | `src/shared/errors/`（可选）                                | `ApplicationError`、依赖不可用、配置错误、预算错误等无业务 owner 的基础结构 |
| 模块业务错误 | `src/modules/<owner>/<subject>.error.ts`                    | 本模块 code、业务语义、retryable 分类和安全 message                         |
| 协议错误映射 | Nest HTTP Filter / RPC handler或interceptor，位置见本仓方案 | module error → HTTP/Connect code、wire details、request ID                  |
| SDK 错误     | `sdk/typescript/src/api-error.ts`                           | wire error → 消费方稳定异常；不 import 服务端 Error class                   |

不要创建一个收集所有业务错误的全局 `errors.ts`。一个模块的 error code、code union 和 Error class 可以放在同一个
`<subject>.error.ts`，因为它们属于同一错误事实；但 HTTP/RPC 状态映射必须停留在协议适配角色。错误 message 不是稳定 API，
客户端只按 machine code 分支；details 不得泄漏 SQL、stack、secret、token 或原始请求。

Nest HTTP 的 Filter/默认路由边界统一格式，Connect 使用自己的错误 interceptor；只对白名单错误公开固定 code/message，不按任意异常的
`statusCode` 或 `message` 原样输出。各仓为真实使用的情况配置：400 输入、401 未认证、403 未授权、404 不存在、
409 业务冲突、412 条件写失败、413 过大、415 介质、429 限流、500 内部错误、503 依赖不可用、504 上游超时。
PG 按 SQLSTATE + 已知约束名映射，不解析自然语言报错；未知异常只在边界记录一次脱敏 cause。

HTTP body、请求接收、handler 执行、连接空闲、代理与下游 I/O 分别配置预算；流式接口另设空闲/总体策略。
`requestTimeout` 不等于业务执行期限。只接受配置的受信代理，request ID 自生成或校验可信来源；鉴权与速率限制先于昂贵工作。
取消沿调用链传播到支持的 client；对无法撤销的写入以幂等身份查询结果。HTTP client 限制重定向、响应大小和并发，防止意外访问内部地址。

### 12.5 可观测性、健康与退出

- 框架集成的结构化日志包含 service、operation、request_id、trace_id、result、duration_ms；禁止 secret、连接串及完整敏感 payload。
- 优先框架/pg/HTTP 自动 instrumentation；仅为有业务意义的用例加 span，不为每个转发方法制造重复瀑布。高基数 ID 不作 metric label。
- `/livez` 不依赖外部服务；`/readyz` 检查启动完成、schema 匹配、draining 与关键依赖，探测有短超时和频率上限。
- 启动入口明确唯一信号 owner。采用 Nest 信号处理时显式 `app.enableShutdownHooks()`；不再并行注册另一套业务 SIGTERM 关闭链。
  测试/程序主动退出使用一次 `app.close()`；它会触发 hooks 和框架连接关闭，不是在这些步骤之前另做的一项操作，hook 内不递归调用它。
- 生命周期协调明确阶段：`onModuleDestroy` 设置 draining/readiness 503、拒绝新业务及停止 worker 接活；
  `beforeApplicationShutdown` 有界排空自建 Connect listener、worker 和其他框架外任务；Nest 随后关闭 HTTP adapter 的连接；
  `onApplicationShutdown` 在上述使用者结束后释放 Redis/Pool 等依赖并结束观测输出。资源 provider 不抢先在 destroy 阶段关闭连接池。
  单仓技术方案可细化协调组件，但不靠模块 import 顺序推测关闭依赖；各步骤幂等，异常清理/超时仍走同一关闭路径。
- 关闭有总期限；长连接/未结束 I/O 需显式取消或强制终止策略，超时记录未完成项并非零退出。
  验证真实 SIGTERM、主动 close、部分启动失败和连接泄漏；Nest 不自动排空自建 listener，`app.close()` 本身也不保证 Node 进程退出。
- SSE/AG-UI 关闭前保留可恢复 cursor；lease/task 清理不能依赖进程一定有机会运行 finally，重启仍从持久事实恢复。

## 13. 测试策略

| 层次         | 验证内容                                    | 默认方式                                       |
| ------------ | ------------------------------------------- | ---------------------------------------------- |
| unit         | Service、policy、状态机分支                 | Vitest + Nest testing/局部结构替身             |
| integration  | `pg` SQL、事务、锁、Redis、provider adapter | 真实共享 PostgreSQL/Redis，测试数据隔离        |
| contract     | OpenAPI/Proto、producer/consumer、breaking  | schema lint、generated drift、handler contract |
| architecture | import、模块公开面、env/ORM/SQL 泄漏        | ESLint boundary rule + 专用测试                |
| smoke        | build 后启动、health/ready、最小请求        | 真实进程，不使用 fake app                      |

规则：

- Fake/Fixture/InMemory 只在 `test/fixtures/`、`test/doubles/`。
- 简单 CRUD 的价值主要来自真实 PostgreSQL integration test，不为了 mock 而再造四层接口。
- tenant 越权、唯一冲突、乐观锁、重复命令、事务回滚和 Redis 故障必须覆盖。
- Nest 测试模块验证 DI；HTTP 可通过 Fastify `inject()`；Connect、真实 socket/TLS/代理由 contract/smoke 覆盖。
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

1. 未经设计的平行实现层、循环依赖、无 owner 的公共目录；不按 `common/utils/models` 目录名一刀切；
2. route/connect handler 直接执行 SQL 或 Redis 命令；
3. Service/Model import HTTP/Connect generated/driver 类型或读取 `process.env`；Service 的 Nest DI decorator 是明确允许项；
4. 模块 A deep-import 模块 B 的内部文件；
5. `src/` 中出现 Fake/Fixture/InMemory；
6. `any`、双重断言、非空断言掩盖输入和空值设计；
7. 同仓出现 Prisma + `pg` 双写、两个 canonical schema 或兼容 fallback；
8. 每个业务模块机械生成 `postgres/`、`redis/`、`ports/` 或空目录；
9. 无明确分发职责的万能 `command-executor`、无实际抽象需求的 `BaseRepository`、万能 Service 或无 owner 的公共层；
10. 违反 SQL、API、tenant、时间和可靠性专项手册；
11. public OpenAPI、Proto、Zod/DTO 出现两个以上可编辑字段事实源。
12. 新建无用途 wrapper，或只转发调用制造层数；Nest module 的依赖元数据有实际职责，不按文件短误判。
13. 手写业务组件偏离 class 默认，或把独立 schema/常量/模型/错误/解析器混入角色类文件。

门禁检查依赖事实，不要求每个模块必须包含某个目录，也不只按 `commands/shared` 等名称拦截；空目录和 README-only 层同样不合格。
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

这些来源支持各自框架、类型和 feature cohesion 原则；Kokoro 的 Nest/class 默认与当前 SQL-first 选择由本文明确，
不声称任何单一开源项目就是“大厂唯一模板”。

补充运行时依据：

- [Fastify server / timeout / shutdown](https://fastify.dev/docs/latest/Reference/Server/)
- [node-postgres Pool API](https://node-postgres.com/apis/pool)
- [Redis 官方 Node client 指南](https://redis.io/docs/latest/develop/clients/nodejs/)
- [Redis client 生产注意事项](https://redis.io/docs/latest/develop/clients/nodejs/produsage/)
- [pnpm dependency build policy](https://pnpm.io/settings/build)

### 17.1 本轮核验（2026-09-06 至 2026-09-07）

| 来源                                                                                                                                                      | 核验用途                           | 不据此推导                           |
| --------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------- | ------------------------------------ |
| [Nest Providers](https://docs.nestjs.com/providers)、[Modules](https://docs.nestjs.com/modules)                                                           | class provider、构造注入、模块封装 | 全部数据必须 class、目录必须照抄样例 |
| [Nest Fastify](https://docs.nestjs.com/techniques/performance)、[Lifecycle](https://docs.nestjs.com/fundamentals/lifecycle-events)                        | 官方 adapter 与资源 hooks          | 换框架自动解决关闭/性能              |
| [Nest Validation](https://docs.nestjs.com/techniques/validation)                                                                                          | Pipe、运行时验证边界               | ValidationPipe 自动支持 Zod          |
| [Connect server plugins](https://connectrpc.com/docs/node/server-plugins/)                                                                                | 官方 Node/Fastify 接入             | Connect 自动执行 Nest Guard          |
| [Google TS](https://google.github.io/styleguide/tsguide.html)                                                                                             | 导出、类型与避免静态工具容器       | Google 要求所有组件 class            |
| [Zod](https://zod.dev/basics)、[jose](https://github.com/panva/jose)                                                                                      | shape 推导、标准密码协议复用       | schema 替代权限，库替代业务密钥策略  |
| [Novu API](https://github.com/novuhq/novu/tree/next/apps/api/src/app)、[Vendure core](https://github.com/vendurehq/vendure/tree/master/packages/core/src) | 真实公开 TS 工程的组织对照         | 其目录/内部 API 是所有企业标准       |

本次是语义与架构资料核验，不是依赖升级。浮动分支链接仅作阅读入口，不作为可复现的版本兼容证据；核心依赖实施时再固定版本/commit。

2026-09-07 补核：[Nest CQRS](https://docs.nestjs.com/recipes/cqrs) 支持可选 Command/Query/Handler 机制，
[Modules](https://docs.nestjs.com/modules) 说明 provider 的 imports/exports 复用边界，
[Request lifecycle](https://docs.nestjs.com/faq/request-lifecycle) 核对 Guard/Pipe/Interceptor/Filter 的执行关系。
这些机制不规定必须创建 `commands/` 或 `shared/`，也不支持以目录名作为合并门唯一证据。
