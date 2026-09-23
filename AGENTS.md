# Kokoro Agent 执行控制手册

本文件只定义跨仓 owner、规范路由、执行流程和验收证据。TypeScript、Python、PostgreSQL 的完整规则只维护在
三份专项手册中，不在这里复制第二份，避免不同文档长期漂移。

## 0. 必读顺序与权威性

每次任务按顺序读取：

```text
1. 系统/平台指令与当前用户要求
2. 本 AGENTS.md
3. 与任务相关的专项手册
4. docs/CURRENT.md、docs/CODEBASE_MAP.md、目标仓 README/INDEX/docs/CURRENT.md
5. 目标仓 contract、TECHNICAL_DESIGN、DATA_MODEL、有效 ADR
6. 历史报告与已废止设计（只用于考古）
```

三份唯一语言/数据事实源：

- [PostgreSQL 与 SQL 工程规范](docs/kokoro-handbook/standards/03-sql-and-postgresql.md)
- [TypeScript 后端成熟工程规范](docs/kokoro-handbook/standards/08-typescript-backend-engineering.md)
- [Python 后端成熟工程规范](docs/kokoro-handbook/standards/09-python-backend-engineering.md)

任务涉及 TypeScript、Python 或 SQL 时，必须先读取对应手册。TypeScript 设计先核对手册第 1、4–6、8.4 节的当前决定；
历史示例与已替代 ADR 不作为并行实现依据，子仓技术方案必须明确当前态与目标态。子仓 `AGENTS.md` 只能补充本仓 owner、入口、契约、
验证命令和例外 ADR，不得复制或覆盖上述手册。旧文档中的强制四层、`ports/`、`postgres/`/`redis/` 业务目录、
机械 DTO/Command/Domain/Row 五层和旧 SQL 规则均不再作为实现依据。

补充专题（与三份手册冲突时，以三份手册为准；历史目录示例不作为新建模板）：

- 事务、并发与幂等：`docs/kokoro-handbook/standards/04-transaction-repository-idempotency.md`
- API/RPC/错误：`docs/kokoro-handbook/standards/05-api-rpc-and-error-contracts.md`
- 测试与门禁：`docs/kokoro-handbook/standards/06-testing-and-quality-gates.md`
- 当前总架构：`docs/ARCHITECTURE_STANDARD.md`

## 1. 全局工程原则

1. 一个业务事实只有一个 owner 和一个写入边界；服务只访问自己的数据库事实。
2. 先确认 owner、契约、状态机、事务、失败恢复和依赖方向，再创建目录和文件。
3. 代码按业务能力聚合；框架、数据库、缓存和 provider 类型不得穿透业务规则。
4. 简单业务保持简单；复杂业务才使用 Domain Model、CQRS、Repository abstraction 或状态机。
5. 一个文件有一个清晰变化原因；一个目录有一组持续存在的职责，禁止空层和模板式脚手架。手写 TypeScript 不得把
   schema/type、常量、model class、错误体系、解析 helper 和 Service 编排混成一个文件；具体例外与拆分规则以
   [TypeScript 手册 §8.4](docs/kokoro-handbook/standards/08-typescript-backend-engineering.md#84-一个手写-typescript-文件只承载一个主要变化原因) 为准。
6. Wire schema、内部业务对象、数据库 Row 和生成类型只有在语义/生命周期不同时才分开；不为凑层数复制类型。
7. 时间瞬时点统一使用 UTC；本地日历时间和周期任务的 IANA timezone 显式建模。
8. 规则必须落在代码、测试、架构检查和 CI；Markdown 自述不是完成证据。
9. Clean-slate 重构删除旧路径、旧 schema、旧 API、fallback、alias 和双轨实现，不建立兼容层。
10. “生产级、顶级、完成”只能绑定当前 commit 与真实 lint/typecheck/test/build/schema/smoke 输出。

## 2. 目标服务拓扑与 owner

目标拓扑为九个正式运行仓：

| 仓库               | 唯一职责                                                                                         |
| ------------------ | ------------------------------------------------------------------------------------------------ |
| `kokoro`           | Web UI、浏览器交互状态、HttpOnly session、同源 adapter                                           |
| `kokoro-bff`       | Conversation、Message、Share、Project、ScheduledTask、公开 Product API、durable AG-UI projection |
| `kokoro-agent`     | Run、Checkpoint、Lease、Tool Journal、执行事件、HITL/Approval、Evidence                          |
| `kokoro-iam`       | Tenant、Identity、Authentication、Authorization、Role、Permission、Audit                         |
| `kokoro-system`    | 系统控制面：Site、Host、Workspace、Runtime、Policy、模型目录与路由配置                           |
| `kokoro-billing`   | Payment、Subscription、Checkout、Refund、Credit、Ledger、Metering、Reconciliation                |
| `kokoro-platform`  | Agent Capability Control Plane；首批只包含 Skills 与 MCP 两个一级业务域                          |
| `kokoro-storage`   | Blob、Upload、Asset、Artifact、Scan 与对象生命周期 metadata                                      |
| `kokoro-scheduler` | Schedule、Occurrence、Lease、Retry、Outbox、Dispatch                                             |

已裁决的 clean-slate 收敛方向：

```text
kokoro-model       -> 合入 kokoro-system/modules/model-catalog，保持清晰业务词汇、表前缀和契约边界
kokoro-capability  -> 重命名为 kokoro-platform
kokoro-platform    -> modules/skills + modules/mcp；历史归档代码不得直接恢复
```

当前物理仓库尚未完成上述 cutover 时，文档必须明确“当前态/目标态”；不得通过兼容代理、双写、复制 contract 或长期
保留旧服务来假装完成。仓库移动、contract owner、数据库、Redis namespace、服务身份和消费者更新必须在独立目标中
一次闭环。

`kokoro-system` 不是万能配置中心。新增配置先归入拥有该业务事实的模块，例如 Site 配置属于 `sites`，模型路由属于
`model-catalog`，运行参数属于 `runtimes`。只有出现独立身份、生命周期、权限、契约和查询模型时才新建一级模块；
禁止每新增一种配置就创建 `<something>-config` 模块，也禁止建设任意 key/value 的 `configs` 垃圾桶。

### 2.1 Platform 防止成为垃圾桶

`kokoro-platform` 可以承载后续中间平台能力，但新增一级模块必须同时满足：

1. 有清晰业务能力名、事实 owner、数据生命周期和公开/内部契约；
2. 服务对象主要是 Agent/BFF/其他内部 runtime，而不是任意共享代码；
3. 与现有 Skills/MCP 共享控制面、身份、发布或运维边界具有实际收益；
4. 不属于 IAM、System、Billing、Storage、Scheduler 或 Agent 的既有 owner；
5. 有 ADR 比较“放入现有 owner / Platform 新模块 / 独立服务”三种方案；
6. 有独立模块测试、观测、权限和未来拆分边界。

`common`、`utils`、SDK wrapper、数据库 helper 和“暂时不知道放哪”的代码不得成为 Platform 模块。

### 2.2 固定调用与数据方向

```text
Browser -> Web same-origin adapter -> BFF -> System/IAM/Platform/Billing/Storage/Agent/Scheduler
```

- Web 不直连内部 owner 服务。
- BFF 不读取任何 owner 数据库。
- Agent 通过 Platform/Storage 的 contract 获取授权能力和保存 artifact，不复制其业务模型。
- Scheduler 只处理通用调度事实，不拥有 BFF ScheduledTask 或 Agent Run。
- 跨仓只使用 owner 发布的版本化 contract、API/RPC 或事件；不共享 ORM schema、SQL、业务 DTO 或相对路径 import。

## 3. Contract、API 与协议

1. OpenAPI/Proto/JSON Schema 只由事实 owner 仓库维护；Root 不建立跨仓可编辑 contract 中心。
2. 由本仓 API 技术设计选择 schema-first 或 code-first 的唯一方向。BFF public OpenAPI 与 RPC Proto 在
   `contract/` 编辑；内部 HTTP 可由运行时 schema 生成只读契约。`generated/` 只放生成物，不维护重复可编辑 DTO。
3. 消费方使用固定版本、commit 和 digest 的 generated client/artifact；不得手改生成文件。
4. HTTP 使用显式 `/v1`，资源名词化；动作在确有 command 语义时显式命名。
5. 外部 JSON 使用 `snake_case`，内部 TypeScript/Python 遵循各语言命名。
6. 成功与错误 envelope、稳定 error code、request ID、分页、幂等和并发条件按 API 专项手册执行。
7. tenant、actor、subject、service identity 来自受信上下文，不从 body 自报。
8. `contract/` 不存数据库 schema、ORM model、Domain Model、Application input 或别仓 API 副本。

协议可见性：

| 可见性            | 范围                           |
| ----------------- | ------------------------------ |
| `public`          | BFF 对开发者开放的 Product API |
| `browser-private` | Web 同源 adapter               |
| `internal-owner`  | 内部 owner 服务 API/RPC        |
| `event-protocol`  | owner 发布的异步消息           |

### 3.1 AG-UI 与 Vercel AI SDK

- Web 与 BFF 的 Agent 网络事件只使用 AG-UI；删除 legacy SSE envelope、双读和 fallback。
- BFF 拥有 durable AG-UI ledger、单调 cursor、replay、断线恢复、retention 与 GC；Redis stream 不是公开事实源。
- Web 的 `AgUiChatTransport` 把 AG-UI 映射为 Vercel AI SDK `UIMessage`/parts；不得形成第二套网络协议。
- HITL 使用结构化 interrupt/resume；resume 携带同 thread、全部未决项、幂等身份和校验结果。
- UI 显式建模 submitting、queued、streaming、awaiting approval、resuming、cancelling、reconnecting、completed、failed。

## 4. 本地基础设施与运行

- 本地与 CI 的应用目标是一个 PostgreSQL 实例、一个数据库和一套应用 role/credential；每个数据 owner 在同库使用独立 schema 与指向该 schema 的连接 URL。代码、Schema、查询、事务和测试继续禁止跨 owner SQL/JOIN、表引用、ORM model 与 canonical schema 共享；表名前缀不代替 owner schema。现有部分 installer/URL 仍锁定 `public` 或整库空白，须由 owner 代码切片改为 schema 边界后才能宣称单库应用组合通过。测试 fixture 临时库只是运行隔离，不是新增应用数据库或角色。每 owner 独立 production role、GRANT/REVOKE、数据库 mTLS 和 NetworkPolicy 属于部署阶段，不是当前开发门禁。
- 本地所有仓共享一个 Redis 实例；先探测复用，缺失时才启动。Web 不拥有数据库。
- Redis 使用独立 namespace/logical DB；目标拓扑 cutover 时由单独 ADR 重新分配，禁止旧新服务同时占用并双写。
- 应用开发从源码运行：TypeScript `pnpm dev`、Python `uv run`、Go `go run`。
- Docker 应用容器只用于 release candidate smoke，不替代本地 lint/test/dev。
- worker/Agent 不得自行重复启动 PostgreSQL/Redis，也不得清理非自己创建的数据。

## 5. Scheduler 约束

- Scheduler 以 PostgreSQL 保存 Schedule/Occurrence/Receipt/Outbox 权威事实；Redis 只协调 lease/通知/缓存。
- `github.com/go-co-op/gocron/v2` 仅作为可替换 timer/wakeup dependency，不得把其类型泄漏到业务模型和 contract。
- 重启、重复唤醒、misfire、崩溃和 Redis 丢失的正确性由持久化状态机、幂等和恢复测试证明。
- 当前依赖版本按 Scheduler 自身 ADR/go.mod 固定；升级遵守稳定、兼容、可维护和完整门禁，不追浮动 `latest`。

## 6. 测试、可靠性与安全

测试目录遵循语言手册：TypeScript 使用 `test/`，Python 使用 `tests/`。必须覆盖 unit、integration、contract、
architecture、smoke；只有真实 PostgreSQL/Redis/ObjectStore/provider sandbox 才能称 integration。

共同门禁：

- timeout、取消、有限重试、指数退避、jitter、graceful shutdown、worker drain；
- tenant 越权、权限失败、幂等重放、并发冲突、事务回滚、重复投递和恢复；
- 结构化日志包含 service、operation、request_id、trace_id、result、duration；不记录 token、密码和敏感 payload；
- 依赖、源码、配置、secret、镜像扫描；GitHub Actions 固定完整 SHA；镜像非 root、有 HEALTHCHECK、SBOM/provenance；
- 每仓维护 SLO、错误预算、告警和 runbook；目标值不得冒充实测结果。

依赖采用“最新稳定且兼容”，manifest/lockfile 固定实际版本。新核心依赖或重大替换必须记录维护状态、候选比较、
许可证、供应链、性能、故障语义和退出路径；Renovate/Dependabot 只提出可审查 PR。

规范维护必须区分三类证据：官方文档说明工具语义；企业公开指南/源代码提供工程经验；Kokoro ADR 记录项目取舍。
不得凭目录名称、star 数或品牌背书宣称“行业唯一/顶级”。版本与选型证据记录核验日期、来源、精确版本和验证命令；
每次升级或进入子仓重构前重新核验，旧报告不证明当前兼容。尚未执行的检查明确列为待验，不用文字承诺替代。

Web 额外覆盖 design token、focus-visible、reduced motion、loading/empty/error/disabled/reconnecting/partial/success、
移动端、Playwright、axe、视觉回归与 bundle budget。

## 7. 文档基线

每个正式仓至少维护：

```text
README.md
INDEX.md
docs/INDEX.md
docs/CURRENT.md
docs/TECHNICAL_DESIGN.md
docs/API_CONTRACT.md
docs/DATA_MODEL.md
docs/SECURITY.md
docs/RELIABILITY.md
docs/ACCEPTANCE.md
docs/SLO.md
docs/RUNBOOK.md
docs/ADR/
contract/README.md            # 有机器契约时
```

`README` 负责五分钟启动，`INDEX` 负责代码地图，`CURRENT` 只记录当前事实和证据，`TECHNICAL_DESIGN` 解释架构，
`API_CONTRACT` 链接机器事实源而不复制字段。Root Developer API 门户只发布 BFF public contract。

## 8. 创建目录和文件前的强制设计门

Agent 新建文件/目录、调整模块边界或开展重构前，必须先检查目标仓并输出以下放置表。已有设计可直接引用；
仅修改现有文件且不改变职责/契约的局部修复，用一句话说明归属与验证即可，不重复整张表：

| 项       | 必须给出的结论                                                 |
| -------- | -------------------------------------------------------------- |
| Owner    | 仓库、业务模块、唯一 writer                                    |
| 当前事实 | 现有目录、入口、import、contract、schema、测试和未提交变更     |
| 目标职责 | 新对象解决什么问题，公开 API 是什么                            |
| 目录方案 | 至少比较 2 个可行位置，说明采用与淘汰理由                      |
| 粒度     | 为什么扩展现有文件、新建文件、新建子目录或新建模块             |
| 依赖     | 允许 import、禁止 import、调用方向和生命周期                   |
| 数据/API | schema、事务、tenant、幂等、缓存、contract、generated 影响     |
| 删除项   | 被替代的旧路径、重复实现、alias、fallback                      |
| 验证     | unit/integration/contract/architecture/build/schema/smoke 命令 |

强制规则：

1. 先读目标仓，不从通用模板盲目生成目录。
2. 新顶层目录、新一级业务模块、新进程、新跨仓 owner 必须有技术设计或 ADR。
3. 普通文件不要求 ADR，但必须能用一句业务语言解释位置和变化原因。
4. 一个目录只有一个文件且没有近期明确增长时，默认不创建该目录。
5. 不因使用 PostgreSQL、Redis、Prisma、Fastify 就创建同名业务目录。
6. 不因看见 `command` 就创建 CQRS/command bus，不因看见数据库就创建 BaseRepository。
7. 目录重构必须同时更新 import 门禁、测试、文档并删除旧路径；只移动文件不算架构优化。
8. 方案已被本手册或 ADR 明确时直接执行，不重复询问；出现真正的新 owner/contract/不可逆决策才请求确认。

### 8.1 子仓实现前的文档门

每个子仓必须先把下列三个设计面收敛成一致的当前方案，再开始目录搬迁或业务重写：

| 设计面   | 必须完成的文件                                  | 通过条件                                                                                       |
| -------- | ----------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| 技术方案 | `docs/TECHNICAL_DESIGN.md`                      | owner、模块、进程、依赖、状态机、事务、失败恢复和目标目录已确定                                |
| API 契约 | `docs/API_CONTRACT.md` + `contract/` 机器事实源 | owner、visibility、version、请求/响应、错误、幂等、分页、事件和 breaking 策略已对齐            |
| SQL/数据 | `docs/DATA_MODEL.md` + 本仓唯一 canonical schema | 表 owner、字段、软/物理删除、无外键完整性、查询、索引、事务、retention 和 fresh install 已对齐；SQL-first 使用 `database/schema.sql`，ORM-first 使用技术方案批准的唯一 schema |

无数据库的仓库在 DATA_MODEL 中明确“无持久化 owner”及理由，不为通过门禁创建空 schema；无对应传输边界时也不创建空 contract。
三者必须相互一致：API 的资源、状态和幂等不得与技术方案/Schema 矛盾，Schema 不得出现没有 owner 用例的表或索引。
Agent 在文档门未通过时只能盘点、补文档、评审契约和验证设计；不先批量搬目录、改表或重写实现。

通过报告必须列出三份文档的绝对路径、未决项、契约/Schema 验证命令和当前 commit。历史评审、过期版本号和“将来会做”
不构成通过证据；发现旧方案时直接更新或归档，不与当前规范并列。

## 9. Agent 执行与多 Agent 协作

用户已明确要求参考本地 `libtv` 专案的任务计划、优先级清单与逐切片提交方式。这里固化的是协作机制，
不复制 LibTV 前端 mock 项目的目录、依赖版本、数据实现或验收结果；后续会话默认执行，无需用户重复提醒。

默认由 Root 主 Agent 发起子仓任务，为当前子仓指定一名负责人 Agent；后续子仓沿用相同机制。负责人负责本仓
审计、方案、实施切片、测试和交接，主 Agent 负责跨仓边界、审查、放行与最终验收，不直接抢写已派出的文件。
同仓后续阶段优先续派给该负责人；每次续派仍明确写入范围、阶段门和提交责任，不一次性授予所有子仓的修改权。
Agent 会话结束或更换时，以任务记录和 commit 交接续接；长期保持的是仓库责任与执行机制，不假设旧 Agent 永久在线。

### 9.1 主控、实现与审查分工

1. 开始前读取本文件、相关三大手册、`docs/CODEBASE_MAP.md` 和目标仓文档。
2. 检查 Git 状态；不覆盖、回滚或格式化其他 Agent/用户的修改。任务外或尚未交接的变更不得暂存；
   主 Agent 按第 9.3 节接收并审查的 worker 交付可以统一提交。
3. 主 Agent 先完成第 8 节整体设计与文档门，再拆任务、确定依赖顺序、派工、裁决边界、审查和集成；
   不把总体架构决定分别丢给多个 worker，也不只转述 worker 的完成报告。
4. 默认一次推进一个子仓，验收闭环后再进入下一个；一个仓同一时刻只有一个写入 Agent，主 Agent 也计入。
   并行优先用于独立调查、契约审查、代码审查和隔离验证，不等于同时重写全部子仓。
5. 出现至少两个独立工作面时，主动说明并行分工并使用可用的原生子 Agent；小修复、单文件编辑或紧密依赖的
   任务由主 Agent 直接完成，不为凑人数派工。主 Agent 保留眼前关键路径，不重复实现已委派任务。
6. 每个 Agent 启动时公开角色和任务范围，例如“SQL 设计审查”“API 契约审查”“实现”“回归验证”；并行数量
   由独立任务数和机器资源决定，不追求开满。已完成的 Agent 及时回收，失败任务由主 Agent 判断重派或接管。
7. 只读审查员不得改文件、提交、重置测试数据或启动共享服务；审查已完成切片应绑定 commit，审查变化中的
   工作树必须标注基线。独立审查结论与主 Agent 的集成验证共同作为放行依据。

### 9.1.1 主控与子 Agent 选模

主窗口保持用户当前选择的模型担任主控，不因派工自动切换。用户已授权子 Agent 按任务需要选择：

| 模型           | 默认适用任务                                   |
| -------------- | ---------------------------------------------- |
| `gpt-6-astra`  | 架构设计、跨仓边界、疑难问题及能力升级后的任务 |
| `gpt-5.6-sol`  | 复杂实现、独立代码审查及多文件协调             |
| `gpt-5.6-luna` | 边界明确、验收条件清楚的小任务                 |

- 先按任务复杂度选模，不把所有子任务固定到最强或最轻模型；任务卡记录角色、模型、文件集和验收条件。
- 出现能力瓶颈时由主控缩小任务或升级模型，保留已验证成果与交接证据；更换写入负责人前先让原负责人停写。
- 选模不改变责任与依赖：独立任务并行、依赖任务串行、同仓单一 writer，主控统一审查、集成并重跑验证。
- 以派发工具当时实际可用的模型为准；模型不可用时记录替代选择，不冒称已使用指定模型。
- 除关键歧义或不可逆决策外，主控自主推进，不为常规选模、内部命名或已确定方案反复询问用户。

### 9.2 先任务卡，再派工

多 Agent 或多步骤工作在当前有效计划中维护一份任务表；优先复用已有计划，不另建重复任务中心。
简单修改无需新建文档。计划引用第 8 节设计和三份专项手册，不把规范全文复制给每个 worker。

每个任务至少记录：

| 项目 | 内容                                                  |
| ---- | ----------------------------------------------------- |
| 任务 | ID、业务目标、优先级、完成条件                        |
| 归属 | owner 仓库、执行 Agent、审查人、只读或写入            |
| 基线 | 工作目录绝对路径、分支、起始 commit、已有未提交变更   |
| 范围 | 允许创建/修改/删除的文件集、排除路径、共享文件负责人  |
| 依赖 | 前置任务、已确定的 API/SQL/类型契约、可并行项、阻塞项 |
| 验证 | 行为基线、实际命令、预期结果、所需隔离资源            |
| 交付 | commit 负责人、交付 SHA、验证证据、风险与后续 owner   |

- Worker prompt 使用中文，附任务卡、`docs/CODEBASE_MAP.md`、相关手册与目标仓文档入口；只给完成本任务
  必要的上下文，不把整个项目历史当作任务描述。
- 跨仓 contract 先由 owner 完成并提交，消费者再更新；存在依赖的任务串行，不让多个 Agent 发明同一契约。
- 共享 contract、Schema、lockfile、公共入口和任务表指定唯一编辑负责人；worker 发现需要越界修改时先报告，
  由主 Agent 调整任务卡，不自行扩大写入集。
- 先记录保留行为的测试基线和批准变更的契约断言，再按业务切片替换；clean-slate 不等于跳过行为验证。
- 已确认无用途或已被替代的旧代码、目录、Schema 和文档入口随切片删除，同时清理调用、配置和生成引用；
  不保留兼容层或两套实现。不合理但仍承担有效职责的旧代码应重构承接，不因“旧”而误删安全或一致性保障。
- 并行测试隔离数据、输出目录和运行资源，复用现有 PostgreSQL/Redis 实例；不得 reset 他人数据库、清空共享
  Redis、重启用户预览进程，或在仍被编辑的工作树上声称获得最终验收结果。

### 9.3 小切片提交，主控集成验收

1. 一个任务交付一个可审查的业务切片，必要时拆成数个自洽 commit；实现、对应测试、契约与必要文档可以同提。
   不逐文件机械提交，也不等全部子仓完成后一次打包。
2. 使用 `codex/` 分支和清晰的 `type(scope): 变更目的` 提交标题；无关依赖升级、格式化与功能变更分开。
3. 提交权限在派工前明确：独占 checkout 的 worker 可以按任务卡提交；共享 checkout 的 Git index、commit、
   分支切换与集成操作由主 Agent 串行执行，其他 Agent 交付文件清单，不并发操作同一个 Git index。
4. 提交前检查 diff 与暂存区，按明确路径暂存；不使用 `git add .` 或 `git add -A` 打包混合工作区。
   只提交本切片文件，不夹带缓存、coverage、构建产物、临时数据库、凭据、任务外或尚未交接的变更。
5. Worker 的“已提交”只表示交付待验收。主 Agent 复核范围、命名、目录、API/SQL 一致性与测试，在主工作树
   重跑相关验证；独立工作树的提交先审查再按依赖顺序集成，原始 SHA 与集成后的 SHA 都要记录。
6. 完成状态依次为：待派工 → 进行中 → 待审查 → 待集成验证 → 已验收；阻塞项记录具体原因和后续 owner。
   Worker 退出码、测试数量、历史截图或口头完成不替代当前 commit 的证据，失败项不靠放宽门禁清零。
7. 每波收尾更新同一任务表：任务、Agent、仓库、文件集、提交、验证、未解决风险；再决定下一波。
   主 Agent 对最终结果负责，已知未闭环项明确保留，不以“多个 Agent 都说完成”宣称完成。

Worker 完成报告格式：

```text
任务：<ID / owner / Agent 角色>
状态：已提交 / 部分完成 / 被阻塞
基线：<工作目录 / 分支 / 起始 SHA>
commit：<交付 SHA 或由主 Agent 提交的原因；已集成时附集成 SHA>
修改文件：<绝对路径>
验证：<命令 -> 实际结果>
审查：<审查人 / 对应 SHA / 结论或待审查>
未完成与风险：<明确列出>
后续 owner：<仓库/Agent/主控>
```

## 10. 默认验证命令

Root：

```bash
python3 scripts/verify-ten-repository-standard.py
python3 scripts/verify-repository-topology.py
python3 -m pytest scripts/tests
```

旧 `scripts/verify-ten-repository-full.sh` 与 `scripts/e2e/run_stage2_owner_health.py` 已暂停：原实现的
共享状态清理未隔离，当前入口只诊断并退出 2，不访问基础设施，不列入默认可执行门禁。
全仓隔离编排由 Root 后续重建；期间逐仓执行 owner 自有完整门禁。System 跨仓 HTTP 验收使用
`scripts/e2e/run_system_owner_smoke.py`（独立临时数据库/缓存前缀、分别指定 Node 24/22），
该 smoke 不替代全仓浏览器、外部存储、真实推理或镜像验收；静态门的实际失败仍需如实记录。

TypeScript：

```bash
pnpm format:check
pnpm lint
pnpm typecheck
pnpm test
pnpm build
pnpm db:apply-schema       # 数据 owner
```

Web：

```bash
pnpm lint
pnpm typecheck
pnpm test
pnpm build
pnpm test:e2e
```

Python Agent：

```bash
uv lock --check
uv sync --frozen
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest
uv build
```

Go Scheduler：

```bash
gofmt -l .              # 验证时输出必须为空；格式化修改另行执行
go vet ./...
go test ./...
go build ./...
```

完成报告必须列出当前 commit、实际执行命令、通过/失败数量、未运行原因、已知风险和后续 owner。
