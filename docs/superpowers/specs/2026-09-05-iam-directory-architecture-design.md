# IAM 目录架构方案：先对齐结构，再实施

状态：**供用户整体确认的草案；不是实现授权。** 本轮只写文档，不改 IAM 代码、不合并 worktree、不运行应用测试。

## 1. 先说明你实际看到的是什么

| 对象                | 本次核对结果                                                                            |
| ------------------- | --------------------------------------------------------------------------------------- |
| 日常打开的 IAM 仓库 | `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-iam`                     |
| 主目录 commit       | `c5c7a0c3b4638988b9dc9d7eb55629d913607f1d`，工作树干净，仍是旧四层                      |
| 独立 worktree       | `/Users/nako/.config/superpowers/worktrees/kokoro-iam/engineering-alignment`            |
| 未合入候选 commit   | `3f7f0c59eaf292de5e249313e7180417fc879f37`，工作树干净，已改为 module-first             |
| 当前执行边界        | 原实现与审查 Agent 已停止；旧任务板中的继续实施授权由本次用户要求收回，等待目录方案确认 |

之前的交付问题是：改动留在独立 worktree，但汇报没有清楚区分“候选提交”和“你打开的目录已经改变”。
这份方案同时审视旧目录和候选目录，不把已经写出的候选当作必须接受的答案。

依据是 [Root AGENTS](../../../AGENTS.md)、[TS 手册第 4–6、9 节](../../kokoro-handbook/standards/08-typescript-backend-engineering.md)
和本仓现有六个 RPC、三个 HTTP 入口与真实调用关系。它是 IAM 的具体取舍，不宣称存在所有公司的唯一目录模板。

## 2. 当前结构的问题，不只是目录名不好看

### 主目录：一个业务要跨四层寻找

例如 Magic Link 登录：请求在 `interfaces/rpc`，用例在 `application/authentication/services`，
状态与身份类型在 `domain/authentication`，SQL 和投递在 `infrastructure`。同一条业务阅读路径被技术分类打散。

同时存在两种容易混淆的“Repository”：domain 下的抽象与 infrastructure 下的实现；
多个单方法 Clock/UUID/Token 类、ports、value-objects 等细目录进一步增加跳转，而不是解释业务。

### worktree 候选：方向改善了，但还值得重新整理

- `auth` 根目录仍有 **17 个文件**，混放 RPC、安全审计、授权和五个 command-receipt 文件；找代码仍要先猜前缀。
- `magic-links` 平放 10 个文件，签发/消费与后台投递是两条不同的阅读路径，应看得出边界。
- 两处 `request-context.ts` 职责不同：runtime 中实际是 traceparent 解析，auth 中是 RPC 关联和日志拦截。
- `.protection.ts`、`.secret.ts` 等命名表达实现手段不一致；应使用一致、直接的职责名称，而不是再增加包装类。

**这些问题用业务分组、准确命名和真实职责边界解决，不用“测试通过”替代结构评审。** 文件数量只是提醒，
不是“超过几个文件就建一层”的规则。

## 3. 三种可行方案与推荐

| 方案                                                       | 优点                                           | 对当前 IAM 的问题                                                                            | 结论                   |
| ---------------------------------------------------------- | ---------------------------------------------- | -------------------------------------------------------------------------------------------- | ---------------------- |
| 全仓 controllers/services/repositories                     | 角色熟悉、入门直观                             | 仍按技术角色拆散同一业务；只是把旧四层换一套名字                                             | 不选                   |
| principals/authentication/authorization/audit 各成一级模块 | 产品边界独立时，团队归属清楚                   | 当前身份建档、会话、审计共处认证事务；没有独立身份管理或审计查询产品，容易制造跨模块内部访问 | 以后确有独立能力再评审 |
| 一个 auth 模块，内部按现有子能力与共同机制分组             | 登录、会话、授权容易定位；同一认证事务保持内聚 | 必须约束内部公共机制，不让 auth 成为整个 IAM 的万能目录                                      | **本草案推荐**         |

`auth` 是目前已实现的认证与授权能力，不代表未来 IAM 所有业务只能塞在这里。
仅仅数据库中存在 tenant、role、permission 表，不等于今天就需要创建它们的管理模块和空 Service。

### 为什么建议增加这些内部目录

| 内部目录                  | 真实职责与阅读路径                                     | 为什么不是为了凑层                                                         |
| ------------------------- | ------------------------------------------------------ | -------------------------------------------------------------------------- |
| `principals/`             | 登录主体、首次建档、组织候选选择、父资源有效性查询     | 三个既有角色共同变化；不是通用 users CRUD                                  |
| `magic-links/`            | 链接签发、消费、nonce/redirect 规则与链接记录          | 是现有登录方式，有自己的状态和输入规则                                     |
| `magic-links/deliveries/` | 投递任务、provider 调用、加密载荷、重试和 worker       | 六个既有文件组成独立后台执行生命周期，不与请求内签发混放                   |
| `sessions/`               | 凭据签发、会话读取、续期、注销与公钥发布               | 修改会话语义时沿这一条路径阅读                                             |
| `authorization/`          | 当前会话的 scope/permission 判定                       | 类型和规则成对共置；不新建不存在的权限管理 Repository                      |
| `audit/`                  | 认证安全事件与落库                                     | 只保存现有事件定义和写入，不扩展成日志平台或新服务                         |
| `idempotency/`            | 四个认证命令共用的结果记录、绑定保护和重放             | 五个既有文件有共同的数据格式与保留语义；是 auth 内部机制，不是新的业务模块 |
| `rpc/`                    | 两组 RPC handler 及共同上下文、workload 校验、错误映射 | 五个既有传输文件共享接入生命周期；不是每个业务机械套一个 rpc 目录          |

这里的 `rpc/` 和 `idempotency/` 是有实际内容的内部职责组，不是恢复全仓技术分层。
它们不拥有独立进程、数据库或对其他模块的公开 API。若你希望内部只按业务分组，也可以把这两组文件留在 auth 根，
代价是恢复较长的根目录；本草案建议用这两个明确分组降低查找成本。

## 4. 推荐目标：完整手写源码目录

以下路径均相对 IAM 仓库根；这是**目标草案**，不是当前主目录。所有文件都对应既有职责，不包含未来功能占位。

```text
src/
  server.ts                           # 唯一进程入口、启动与信号处理
  app.ts                              # 装配应用和依赖，不主动监听端口
  health.routes.ts                     # health/ready 运维入口
  http.protocol.ts                     # 现有 HTTP envelope 与关联 header

  config/
    env.ts                            # 环境配置读取与校验的唯一入口

  runtime/
    create-runtime.ts                 # 共享连接、日志、密钥组件等资源的装配
    shutdown.ts                       # 现有启动/关闭协调，不承载认证用例
    readiness.ts                      # 进程就绪与依赖状态
    request-logger.ts                  # 结构化日志能力与实现
    trace-context.ts                   # traceparent 解析，不是第二套 RPC request ID

  modules/
    auth/
      auth.ts                         # 认证事务所需的分组能力类型，不汇总所有模型
      auth.error.ts                   # 业务错误；不依赖 HTTP/Connect 错误对象
      auth.transaction.ts             # 同连接事务装配与认证命令的提交恢复

      principals/
        principal.ts                  # 主体、登录身份和组织候选的内部类型
        principal.service.ts          # 新/旧身份分流、组织选择
        principal.repository.ts       # 身份图查询、创建与父资源锁

      magic-links/
        magic-link.ts                 # 链接类型、状态规则与用例输入结果
        magic-link.policy.ts          # nonce、redirect 与签发策略
        magic-link.service.ts         # 签发/消费编排，不负责发送邮件
        magic-link.repository.ts      # 链接记录查询与更新
        deliveries/
          delivery.ts                 # 投递记录、claim、结果及窄依赖类型
          delivery.repository.ts      # enqueue、claim 与结果落库
          delivery.processor.ts       # 单次投递处理、失败分类与重试决策
          delivery.worker.ts          # poll、取消与 drain，不重复处理业务规则
          delivery.client.ts          # 外部投递 provider 协议适配
          delivery.crypto.ts          # 现有投递载荷加解密，不重新设计算法

      sessions/
        auth-session.ts               # 会话状态、输入结果及凭据相关内部类型
        session.service.ts            # refresh/logout/getSession
        session.repository.ts         # 会话与当前有效身份投影
        session-credentials.service.ts # consume/refresh 共用的唯一签发与结果释放
        session-token.ts              # JWT/refresh token 的具体实现
        jwks.routes.ts                # 标准公钥集 HTTP 入口

      authorization/
        authorization.ts              # 授权输入与 allowed/reason 结果
        authorization.service.ts      # scope/permission 规则，读取会话窄能力

      audit/
        security-event.ts             # 认证安全事件定义与构造
        security-event.repository.ts  # 事件写入；不决定业务授权

      idempotency/
        receipt.ts                    # 认证命令结果记录及绑定/保护能力类型
        receipt.service.ts            # 输入绑定、去重与重放期限规则
        receipt.repository.ts         # 原子 claim、读取及完成记录
        receipt.crypto.ts             # 现有 keyring、HMAC/AEAD 格式与实现
        receipt.parser.ts             # 解码结果校验与时间/业务结果恢复

      rpc/
        authentication.rpc.ts         # 五个认证 RPC，委托 links/sessions 用例
        authorization.rpc.ts          # Authorize RPC
        request-context.interceptor.ts # RPC request ID 与日志接入职责
        workload-auth.interceptor.ts  # 调用服务凭据检查，不代替用户权限判定
        error.mapper.ts               # 业务错误 -> Connect code / ErrorDetail

  generated/
    proto/                            # 原四个只读生成文件，结构与内容均保留
```

目标共 **46 个手写 TS 文件**，与当前 worktree 候选数量相同。这不是通过增加文件实现“分层”；
主要改变候选中的分组和少数不清楚的名字。相比主目录的 53 个手写文件，减少的是重复壳和过度细分，而不是删除能力。

### 顶层为什么这样安排

- `server.ts` 和 `app.ts` 分别回答“进程怎样启动”和“依赖怎样组成应用”。不并存 main/bootstrap/application 三套装配入口。
- `runtime/` 有实际共享资源和关闭顺序，因此有必要；不是又一层 infrastructure，也不放业务 SQL。
- health/ready 是进程运维接口，放 `health.routes.ts`；JWKS 由会话密钥负责，和 sessions 共置。
- 这一轮保留当前 Node HTTP/Connect-node 行为。目录确定不等于 Fastify 已切换；未来框架改动复用这些职责位置。
- 不创建 `plugins/`、`entrypoints/`、`integrations/` 等暂时没有独立内容的目录。

## 5. 命名规则如何具体落到 IAM

| 类型               | 规则                             | 本方案例子                                            |
| ------------------ | -------------------------------- | ----------------------------------------------------- |
| 资源集合           | 复数                             | `principals`、`sessions`、`magic-links`、`deliveries` |
| 能力/机制          | 不机械加 s                       | `auth`、`authorization`、`audit`、`idempotency`       |
| 技术协议           | 使用既有术语                     | `rpc`，不是 `rpcs`                                    |
| 文件               | 单一业务主题 + 必要角色          | `principal.service.ts`、`session.repository.ts`       |
| 同一上下文内的机制 | 利用路径表达归属，避免重复长前缀 | `auth/idempotency/receipt.repository.ts`              |

- `.repository.ts` 直观表示数据访问，不再同时叫 repo/store/dao；这里也不是 Git 仓库的意思。
- 数据库已选定，因此文件不加 postgres 前缀，也不建立每业务一套 postgres/redis/prisma 目录。
- `.crypto.ts` 在本仓表示具体密码组件；它不是纯业务 Service，也不被强行包装成通用安全框架。
- `session-credentials.service.ts` 确有共同签发/重放规则，不是只转发的 Service 壳。
- `receipt.parser.ts` 的边界是“不可信解码结果 -> 已校验的业务结果”，不把解析错误混入 Repository。
- 没有跨模块消费者就不添加 `index.ts`；同模块的子目录可以直接引用明确内部文件。
- 状态联合类型和小型规则就近放业务文件，不再机械建立 dto/enums/models/value-objects 集合目录。

## 6. 依赖关系：目录不是允许随便相互调用

```text
server -> config + app + runtime lifecycle
app -> runtime + RPC/HTTP + 用例 + 具体 Repository/client/crypto + auth.transaction

auth/rpc -> generated + 业务用例 + auth.error
magic-link.service -> principal.service + session-credentials + receipt 规则 + 事务能力
session.service -> session-credentials + receipt 规则 + 事务/会话读取能力
authorization.service -> 会话读取窄能力

auth.transaction -> 在同一 client 上装配各 Repository，向用例提供分组能力
repository -> pg + 对应中性业务类型
delivery.processor -> 投递数据访问/发送/解密的窄能力
delivery.worker -> delivery.processor
delivery.client -> 外部 HTTP
crypto / session-token -> 对应密码实现或 SDK
```

Service 接收自己实际需要的方法，不导入具体 Repository、Pool、完整配置、Connect message 或框架 Request。
`auth.ts` 只描述这组认证事务的共同能力，不成为全仓 DTO/type 集合或新的 Port 目录。

### 跨目录但同一事务：必须保持的例子

消费链接涉及 link、principal、session、receipt、audit。这些文件分开存放，但事实写入仍由同一认证事务协调。
不允许每个 Repository 自己拿新连接、自己 commit；不因为分出 `deliveries/` 就在数据库事务内调用 provider。

父身份锁由 principal 数据访问组件拥有，session 通过装配注入复用。会话签发由 credentials Service 拥有，
consume 与 refresh 都调用它，不各复制一份签发逻辑。目录结构应该直接反映这些共享关系。

## 7. API、SQL 与仓库其他目录的边界

| 对象                          | 位置/owner                                                            | 本次目录方案的影响                              |
| ----------------------------- | --------------------------------------------------------------------- | ----------------------------------------------- |
| 六个 RPC 的字段、方法与服务名 | 本仓 `contract/proto/`                                                | 不因源码目录分组改名、改字段编号或新增接口      |
| 三个 HTTP 入口                | health/ready 及 JWKS 对应 handler；当前机器文档在 `contract/openapi/` | URL、响应语义保持；目录重构不偷偷切换事实源     |
| 只读生成类型                  | `src/generated/proto/`                                                | 不复制进各业务目录；不将 generated 作为业务模型 |
| 唯一 DDL                      | `database/schema.sql`                                                 | 本片不改表、索引、约束、数据或安装方式          |
| 参数化 SQL、Row、锁           | 各业务 `.repository.ts`                                               | 随业务 owner 移动，不把 SQL 再拆到一套技术目录  |
| PG/Redis 连接                 | app/runtime                                                           | 复用现有资源，不新增实例或业务数据库            |
| 跨仓 owner                    | 保持现状                                                              | 不新增身份服务、审计服务或共享 DTO 包           |

PostgreSQL、无外键、canonical schema 等已确认规则继续引用 [SQL 手册](../../kokoro-handbook/standards/03-sql-and-postgresql.md)。
这份文档不复制 SQL 规范，也不借目录改造引入 Prisma、变更软删除或新增约束。

仓库根仍保留 `contract/`、`database/`、`docs/`、`scripts/`、`test/` 和现有配置文件；不整体翻新根目录。
`dist/` 与 `node_modules/` 是构建/安装产物，不是人工组织的业务架构。

`test/` 保留 unit/integration/contract/architecture/fixtures/doubles 的现有分类；有真实启动用例后才出现 smoke。
本轮不执行这些测试，不以测试报告代替对目录的确认。后续搬迁造成的路径引用随搬迁同步，具体验证放到实施阶段。

## 8. 完整旧路径处置表

下表覆盖主目录全部 53 个手写源码文件。路径省略共同的 `src/`；多个目标表示按既有职责拆分，
“删除壳”表示能力保留为注入函数，不是删业务行为。不存在“剩下的文件看着办”。

| 主目录旧路径                                                                            | 目标或处置                                                                                                 |
| --------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| `main.ts`                                                                               | `server.ts`                                                                                                |
| `bootstrap/production.ts`                                                               | 合入 `server.ts`，保留进程启动职责                                                                         |
| `bootstrap/process-lifecycle.ts`                                                        | 合入 `server.ts`，保留信号与生命周期协调                                                                   |
| `bootstrap/container.ts`                                                                | `app.ts` + `runtime/create-runtime.ts`                                                                     |
| `bootstrap/authentication.ts`                                                           | `app.ts`，不保留重复认证装配壳                                                                             |
| `bootstrap/runtime.ts`                                                                  | `runtime/shutdown.ts`                                                                                      |
| `config/iam-config.ts`                                                                  | `config/env.ts`                                                                                            |
| `application/authentication/dto/authentication-dto.ts`                                  | `modules/auth/magic-links/magic-link.ts` + `sessions/auth-session.ts`                                      |
| `application/authentication/errors.ts`                                                  | 事务恢复相关内容合入 `modules/auth/auth.transaction.ts`                                                    |
| `application/authentication/mappers/command-receipt-parser.ts`                          | `modules/auth/idempotency/receipt.parser.ts`                                                               |
| `application/authentication/policies/configured-magic-link-issuance-policy.ts`          | `modules/auth/magic-links/magic-link.policy.ts`                                                            |
| `application/authentication/ports/authentication-ports.ts`                              | 共享 token 能力归 `sessions/auth-session.ts`；时间/ID/随机性改为消费方函数依赖                             |
| `application/authentication/ports/magic-link-issuance-policy.ts`                        | 合入 `modules/auth/magic-links/magic-link.policy.ts`                                                       |
| `application/authentication/services/authentication-service.ts`                         | 按现有职责拆至 magic-link/session/principal/credentials/receipt 五个 Service                               |
| `application/authentication/services/magic-link-delivery-processor.ts`                  | `modules/auth/magic-links/deliveries/delivery.processor.ts`                                                |
| `application/authorization/dto/authorization-dto.ts`                                    | `modules/auth/authorization/authorization.ts`                                                              |
| `application/authorization/ports/authorization-ports.ts`                                | 授权消费方就近声明会话读取能力；删除独立壳                                                                 |
| `application/authorization/services/authorization-service.ts`                           | `modules/auth/authorization/authorization.service.ts`                                                      |
| `application/observability/ports/request-logger.ts`                                     | 合入 `runtime/request-logger.ts` 的窄日志类型                                                              |
| `domain/audit/models/security-event.ts`                                                 | `modules/auth/audit/security-event.ts`                                                                     |
| `domain/audit/repositories/security-event-repository.ts`                                | 所需写入方法归 `modules/auth/auth.ts` 分组事务能力；删除重复接口文件                                       |
| `domain/authentication/enums/authentication-status.ts`                                  | 链接、会话状态分别就近归 magic-link.ts / auth-session.ts                                                   |
| `domain/authentication/errors/authentication-error.ts`                                  | `modules/auth/auth.error.ts`                                                                               |
| `domain/authentication/models/auth-session.ts`                                          | 按语义拆至 principals/principal.ts、magic-links/magic-link.ts、sessions/auth-session.ts                    |
| `domain/authentication/models/magic-link-delivery.ts`                                   | `modules/auth/magic-links/deliveries/delivery.ts`                                                          |
| `domain/authentication/repositories/authentication-repository.ts`                       | 分组事务能力归 auth.ts；receipt 模型归 idempotency/receipt.ts；删除总 Repository 抽象                      |
| `domain/authentication/repositories/magic-link-delivery-repository.ts`                  | 所需处理能力就近归 `modules/auth/magic-links/deliveries/delivery.ts`                                       |
| `domain/authentication/value-objects/magic-link-issuance.ts`                            | `modules/auth/magic-links/magic-link.policy.ts`                                                            |
| `domain/authorization/errors/authorization-error.ts`                                    | 合入 `modules/auth/auth.error.ts`，保留错误语义                                                            |
| `infrastructure/clients/http-magic-link-provider.ts`                                    | `modules/auth/magic-links/deliveries/delivery.client.ts`                                                   |
| `infrastructure/observability/json-request-logger.ts`                                   | `runtime/request-logger.ts`                                                                                |
| `infrastructure/readiness/readiness.ts`                                                 | `runtime/readiness.ts`                                                                                     |
| `infrastructure/repositories/audit/postgres-security-event-repository.ts`               | `modules/auth/audit/security-event.repository.ts`                                                          |
| `infrastructure/repositories/authentication/authentication-transaction.ts`              | `modules/auth/auth.transaction.ts`                                                                         |
| `infrastructure/repositories/authentication/postgres-authentication-repository.ts`      | 按 SQL owner 拆至 principal/session/magic-link/delivery/receipt Repository；事务装配归 auth.transaction.ts |
| `infrastructure/repositories/authentication/postgres-magic-link-delivery-repository.ts` | `modules/auth/magic-links/deliveries/delivery.repository.ts`                                               |
| `infrastructure/security/aes-gcm-secret-box.ts`                                         | `modules/auth/magic-links/deliveries/delivery.crypto.ts`                                                   |
| `infrastructure/security/jwt-token-service.ts`                                          | `modules/auth/sessions/session-token.ts`                                                                   |
| `infrastructure/security/receipt-protection.ts`                                         | `modules/auth/idempotency/receipt.crypto.ts`                                                               |
| `infrastructure/security/secret-box.ts`                                                 | 合入 delivery.crypto.ts；用例消费窄加解密能力，不依赖具体实现类型                                          |
| `infrastructure/time/random-token-generator.ts`                                         | 删除单方法类，app 注入 newToken 函数                                                                       |
| `infrastructure/time/system-clock.ts`                                                   | 删除单方法类，app 注入 now 函数                                                                            |
| `infrastructure/time/uuid-generator.ts`                                                 | 删除单方法类，app 注入 newId 函数                                                                          |
| `infrastructure/workers/magic-link-delivery-worker.ts`                                  | `modules/auth/magic-links/deliveries/delivery.worker.ts`                                                   |
| `interfaces/http/protocol.ts`                                                           | `http.protocol.ts`；删除无消费者的错误类型                                                                 |
| `interfaces/http/server.ts`                                                             | 装配归 app.ts；处理分别归 health.routes.ts / sessions/jwks.routes.ts                                       |
| `interfaces/observability/request-context.ts`                                           | trace 归 runtime/trace-context.ts；RPC 关联归 auth/rpc/request-context.interceptor.ts                      |
| `interfaces/rpc/authentication-service.ts`                                              | `modules/auth/rpc/authentication.rpc.ts`                                                                   |
| `interfaces/rpc/authorization-service.ts`                                               | `modules/auth/rpc/authorization.rpc.ts`                                                                    |
| `interfaces/rpc/errors.ts`                                                              | `modules/auth/rpc/error.mapper.ts`                                                                         |
| `interfaces/rpc/request-logging.ts`                                                     | `modules/auth/rpc/request-context.interceptor.ts`                                                          |
| `interfaces/rpc/server.ts`                                                              | `app.ts` 注册两个既有 RPC service，不增加一个只负责转发的入口                                              |
| `interfaces/rpc/workload-auth.ts`                                                       | `modules/auth/rpc/workload-auth.interceptor.ts`                                                            |

四份 generated 原文件全部原位保留。旧 application/domain/infrastructure/interfaces/bootstrap 和旧 main 路径在实施完成后删除，
不留 re-export、兼容入口或原总 Service/Repository 转发门面。

## 9. 与 worktree 候选的差异，避免重新全写一遍

已有候选仅供复用审查，不直接整份合入：

1. 授权的类型和 Service 归 `authorization/`，RPC 接入归 `rpc/`。
2. 五个 command-receipt 文件归 `idempotency/receipt.*`；保护实现明确命名为 `.crypto.ts`。
3. 两个 security-event 文件归 `audit/`。
4. 两个 RPC handler、request context、workload interceptor、错误映射归 `rpc/`。
5. 六个 delivery 文件归 `magic-links/deliveries/`；`.secret.ts` 改为 `.crypto.ts`。
6. 共同签发/重放文件使用 `session-credentials.service.ts`；runtime 的 trace 解析使用 `trace-context.ts`。
7. 其他文件沿用已拆清的实际职责，不为了这份树重新设计加密、事务或引入新框架。

这几项都是草案选择，尚未修改候选代码。现有源码中的请求 ID、deadline、校验及其他已登记问题仍存在；
在文档里给文件写上职责，不等于这些行为已实现或已修复。

## 10. 整体对齐与后续边界

请整体确认三个问题，而不是逐个文件反复决定：

1. **业务组织**：一个 auth 模块，内部区分主体、链接、会话、授权，不按表创建一批一级模块。
2. **阅读粒度**：投递再分一组；RPC、幂等、安全事件各有明确内部位置，避免候选根目录继续堆文件。
3. **命名习惯**：业务词 + role suffix；不增加数据库品牌目录、Port、总 Repository 或抽象执行器。

确认之后，先同步 IAM 的 TECHNICAL_DESIGN、API_CONTRACT、DATA_MODEL 与 INDEX，再进行目录及必要依赖调整；
技术/API/SQL 三份文档继续由 IAM 自持，本 Root 草案不成为第二份长期实现手册。

后续实施汇报必须分别列明：候选位置、是否已进入日常主目录、实际当前目录树。只有主目录真的改变，才说“目录已落地”。
本轮不推进新业务、SQL 变更、依赖升级、其他仓库或下一轮自动派工；等待本方案的用户反馈。
