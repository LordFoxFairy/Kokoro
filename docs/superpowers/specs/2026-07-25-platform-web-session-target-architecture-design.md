---
artifact: prd-and-architecture-spec
version: "1.5"
created: 2026-07-25
status: internal-review-active
scope: kokoro-overall-business-runtime-and-agent-product-capabilities
---

# Kokoro 整体业务、Platform、Web、Session 与 Agent 产品目标架构

## 0. 文档定位

本文定义 Kokoro 未上线阶段的一次性整体目标架构，覆盖业务能力、Platform、Web、Session、Agent
产品能力，以及它们与 GA、Job、ExecutionTarget、Automation、Capability、Model Gateway、Artifact
的边界。本文同时承担总 PRD 和跨仓 Umbrella
Spec，后续每个实施波次必须拆出独立子 Spec 和实现计划。

本文描述的是**目标状态**，不是当前实现事实。代码、旧 handoff、旧 Plan/三桶实现和旧 handbook
与本文冲突时，在本文完成书面复审并迁入 handbook 后，以本文为新目标；迁入前不得把目标状态
误写成“已经落地”。

产品需求治理、具体 Reference Launch Profile、Journey/State/Recovery/Metric Catalog 与 Mandatory PRD
Registry 由 `2026-07-25-product-requirements-governance-and-prd-registry-design.md` 承载；模块到 Journey/Spec/
Evidence 的完整追踪由 `2026-07-25-kokoro-module-capability-coverage-audit.md` 承载。二者不能修改本文的
领域 ownership 和运行时不变量。

快速复审路径：先读 §0、§2、§2.5、§3.3、§4、§5、§7.4、§16、§17、§19.1、§23、§25、§27，
可在二十分钟内判断产品目标、系统边界、Redeem 首发、主链、验证/维护和实施顺序；领域负责人再进入
对应详细章节。

已确认的不可变前提：

- 一个 Site 是一个用户无感知的独立产品站点。
- 一个 Site 对应一个独立 Web 项目、部署、域名和回滚周期。
- 不同 Site 默认不共享账户、登录态、Workspace、套餐、积分、订阅和历史。
- 业务后端、Session、Job、GA、Model Gateway 和 Capability Runtime 只有一套。
- `siteId` 是 Platform 业务隔离上下文；`namespace` 是 GA 唯一 opaque 隔离键。
- GA 不接收 `userId`、`ownerId`、`workspaceId` 或 `siteId` 作为第二隔离轴。
- 系统未上线，允许 clean replace；切换后删除旧代码、旧表、旧注释和兼容分支。

## 1. 问题与为什么现在解决

### 1.1 当前问题

Kokoro 已经有扎实的 Chat、SSE、HITL、LangGraph/DeepAgents、sandbox 和基础能力装配，但整体
产品架构仍有五个结构性问题：

1. Platform 按模块拆成多个小服务和数据库，Catalog、Payment、Credit、Site、Model 的事实链被
   网络边界割裂；同时 Plan、价格、积分和 Site 配置混在可变记录里。
2. Session 同时承担会话、Site、Hub resolve、模型选择、Credit saga 和 Provider 改写，已经成为
   错误的跨域编排中心。
3. GA 直接承担部分 Provider、MCP 连接、delivery 存储等外部后端职责，真实 Model Gateway、
   Capability Runtime、Job 和 Artifact 边界没有完全成立。
4. 当前 Web 仍以一个 `apps/user` 加 Host 解析承载多站点，与“一 Site 一独立产品项目”的增长目标
   冲突；Chat 有底座，但缺分支、后台 Job、Project、ArtifactVersion 和专业 Studio。
5. 当前三桶余额只能表达日/周期/永久的余额视图，不能精确表达购买来源、退款、争议、撤销、
   Grant scope 和失败 Provider Attempt 的完整账务事实。

### 1.2 为什么现在

- 尚未上线，没有生产兼容负担，是重建边界、数据模型和目录的最低成本窗口。
- 后续增长依赖快速创建独立 Site，继续依赖单 Web 项目和 Site 特判会指数级放大维护成本。
- Image、Music、Video、后台 Job 和 Claude Code 类客户端都会同时放大 Session 与 GA 的职责混乱。
- Payment、Subscription、Credit、Redeem 均为成熟领域，应采用标准事实链和不可变版本模型，
  不应继续扩展临时抽象。

## 2. 目标、指标与非目标

### 2.1 目标

1. 建立“模块化 Platform Core + 独立执行服务”的稳定边界。
2. 让一个新 Site 能以独立 Web 项目快速创建、独立发布和回滚，同时复用全部后端能力。
3. 让 Session 只负责对话、消息、Run、HITL、分支、投影和浏览器传输。
4. 保留 GA 的成熟执行底座，只重做不可变 Manifest、真实 Agent Handoff、外部能力 adapter 和
   副作用恢复安全。
5. 统一 Direct Studio 与 GA Tool 的 Operation、Job、ArtifactVersion 和 Usage 业务链。
6. 建立标准 Catalog、Offering、Payment Fact、Fulfillment、EntitlementGrant、CreditGrant 和
   CreditJournal 模型。
7. 建立可运营的标准 Admin，而不是以通用数据表替代发布、财务和运行恢复流程。
8. 统一 Backend/Admin/共享 Web capability source 的 TypeScript 工具链、契约、lockfile 和服务装配方式；每个Site Web
   Project保留独立source、lock、CI、artifact与release authority，并只消费已签名发布包。
9. 建立 Claude Code 类开发代理与 Manus 类行动代理共用的 ExecutionTarget、Permission、Routine、
   TaskView、多端继续和多 Agent 产品底座，不复制第二套 Runtime。
10. 以 production-ready、redeem-first 纵切完成首次真实上线；即使未接 Payment Provider，也能通过卡密
    原子取得与购买等价的 Subscription/Entitlement/Credit，并具备验证、回滚、运维和文档治理。

### 2.2 成功指标

| 指标 | 当前基线 | 目标验收 | 验收阶段 |
|---|---|---|---|
| 新 Site 后端特判 | 依赖 Host/Site 配置与共享 app | 核心代码新增 Site 特判为 0 | Site Fleet 验收 |
| Site 发布隔离 | 单 app、多 Host 思路 | 两个 Site 可独立 build、deploy、rollback | Site Fleet 验收 |
| 浏览器伪造 Site | Header/配置链仍可构造 | 伪造或缺失绑定均 fail closed | 安全验收 |
| Session 商业职责 | 含 model/credit/hub 逻辑 | Session 中商业决策为 0 | Runtime 验收 |
| GA 商业字段 | 仍有间接 Provider/业务装配 | GA wire 中 Site/Plan/Price/Secret 字段为 0 | Runtime 验收 |
| Job 恢复 | 无独立产品 Job | 断线、Session 重启后 Job 可恢复 | Job 验收 |
| Chat 分支 | 无 | edit/regenerate 不覆盖历史 | Web 验收 |
| Artifact lineage | delivery/hash 为主 | 每个版本有 Operation/Job/Attempt provenance | Artifact 验收 |
| Credit 可逆性 | 只能按桶归还 | 可按源 Grant 精确撤销和退款 | Commerce 验收 |
| Provider 事实覆盖 | 终态 usage 为主 | 每个 terminal Attempt 与本地 AttemptUsageFact 原子持久化，canonical UsageEvidence 无重复 | Model/Usage 验收 |
| 工具链漂移 | 多 TS/Vitest/Zod/lockfile | 共享source workspace单catalog/lock；每个Site Project独立锁定已发布兼容版本 | Toolchain 验收 |
| 跨 Site 数据泄漏 | 尚无目标架构级证明 | 安全矩阵中跨站越权成功数为 0 | 安全验收 |
| 重复履约/重复扣费 | 当前按局部幂等实现 | webhook/replay/chaos 矩阵重复数为 0 | Commerce 验收 |
| 高风险后台操作审计 | 各模块覆盖不一致 | 定义范围内 mutation 审计覆盖率 100% | Admin 验收 |
| Redeem 原子性 | 尚无 production 链 | 并发/故障注入下 Code 与 Grant 部分成功数为 0 | Commerce 验收 |
| Production 可恢复 | 当前局部验证 | restore/rollback/chaos 达到 RPO/RTO，重复 effect/Grant 为 0 | Wave 9 |
| 架构文档漂移 | INDEX/CODEBASE_MAP 已失真 | 受管 public root coverage 100%，dead path/old owner 为 0 | Wave 0/8/9 |
| 首个价值时间 | 尚无生产基线 | 注册或兑换后到首个成功 Run/Job 的 p50/p95 可观测，并由首发 Site 冻结目标 | Core Launch |
| 用户成功率 | 尚无统一口径 | Redeem、Chat Run、Studio Job、Artifact export 分别有成功/恢复/放弃漏斗 | Core Launch |
| Support contact rate | 尚无生产基线 | 每千次 Redeem/Run/Job 的 Case 数可按 Site 与原因审计 | Core Launch |

### 2.3 非目标

- 不自建媒体模型。
- 不把每个 Platform 领域模块部署成微服务。
- 不为每个 Studio、Provider、Operation 或 Worker 新建 Git 仓库。
- 不把所有同步工具机械升级为 Job。
- 不建立一个万能 Task aggregate 替代 Session、Run、Operation 和 Job。
- 不把 Studio 做成同一个 JSON 动态表单。
- 不在第一阶段引入复杂税务、实体商品、库存、物流和完整会计总账。
- 不在本 Spec 直接确定套餐价格、促销文案或 Site 是否开放某个产品入口；这些由 Site assignment
  和已版本化 Offering 决定。
- 不因为重构 Platform/Web/Session 而重写 GA 的 LangGraph/DeepAgents 核心。

### 2.4 非功能目标与设计容量

以下是架构验收 envelope，不是业务增长预测：

- 在不改变领域模型的前提下支持 100 个独立 Site、10,000 条并发 SSE 连接、100 Run admission/s
  和 20 个媒体 Job start/s；压力测试覆盖 5 倍短时突发。
- Platform/Session/Job API 月可用性目标 99.9%；外部 Provider 故障单独计量，不掩盖为本系统成功。
- Site bootstrap 在已缓存有效 manifest 时 p95 小于 200 ms；Platform admission 自身处理时间 p95
  小于 250 ms，不包含外部模型或支付 Provider 时间。
- instance/AZ 故障下，Order、Payment Fact、Fulfillment、CreditJournal 已确认事务 RPO 为 0、服务 RTO
  小于 5 分钟。redeem-only 首发的完整 region loss 目标为 PostgreSQL WAL/Object version 异地复制
  RPO 不高于 5 分钟、服务 RTO 不高于 60 分钟；若要宣称 region-loss RPO 0/RTO 30 分钟，必须另行提供
  同步跨区复制、warm standby、DNS/Secret/Object failover 与演练证据。
- 已接受的 Run/Operation/Job 不因单 Worker、Session 实例或浏览器退出而丢失。
- Artifact Blob 使用校验和、版本化/对象锁策略和生命周期规则；数据库备份不替代对象存储备份。
- 所有关键链路可按 correlationId 在五分钟内定位到 Site、Admission、Run/Job、Attempt、Usage 和
  Fulfillment 时间线，同时不暴露敏感内容。

### 2.5 Production-ready 与“功能完整”的定义

本方案的完成态是可直接承载真实用户的 production release，不存在“先以 Demo/半成品上线，再补核心
安全、账务和恢复”的中间完成口径。

- 只有通过对应 Wave 全部 contract、integration、E2E、security、load、recovery 和 operation gate 的
  Capability/Surface revision 才能进入 production SiteRelease。
- SiteRelease 只能引用 `production_ready` revision；未实现、仅 mock、仅管理员手工补偿或没有 runbook 的
  功能必须在 route、bootstrap、API authorization 和后台入口四层同时关闭，不能只隐藏按钮。
- SiteRelease compile 生成 machine-readable `EnabledCapabilityInventory`：每个 Surface/route/API/Admin
  mutation/Capability 绑定 revision、P0 journey、test report digest、runbook、dashboard/alert owner、accepted
  risk/expiry 和 production-ready attestation。unknown、stub、证据缺失/过期或只隐藏 UI 的 entry fail closed。
- “功能完整”按已发布 Site 的用户承诺判断：注册/登录、套餐展示、权益取得、Credit、Chat/Studio、Job、
  Artifact、Library、错误恢复、Admin/Support、删除导出与通知形成闭环；不能出现能进入但无法完成的旅程。
- Claude Code/Manus 类 P1/P2 能力可以由 Site assignment 分阶段开放，但任何一项一旦对真实用户开放，就
  必须以完整 Target/Permission/Usage/TaskView/Recovery 链上线，不使用实验性旁路。
- `Core Production Launch` 与 `Advanced Agent Program` 是两个不同完成口径。Core Launch 只要求首发
  `LaunchProductProfile` 中启用的 Identity、Account/Redeem、Chat、Studio/Library、Admin/Support 与对应
  后端纵切完成生产认证；未进入 profile 的 Target/Developer Workspace/Routine/AgentTeam/Application
  Runtime 不阻塞 Core Launch。
- `Advanced Agent Program` 在 6A-6D 全部退出后完成；任一高级 Surface 一旦进入 SiteRelease，仍必须通过
  自身完整安全、恢复、计费、通知和运维门，不存在 beta 旁路。
- 每次候选发布必须生成 `EnabledSurfaceInventory`，逐项绑定 route、API、Admin command、revision、P0
  journey、owner、测试证据、runbook 与 kill switch。`LaunchProductProfile` 只引用该 inventory 和冻结的
  SiteRelease，不靠文档中的笼统 P0/P1 标签决定上线范围。
- 整体 Transformation Program 只有在全部计划 Wave、clean cutover 与目标高级能力退出后才完成；它与
  “某个 Core Site 已可生产上线”不是同一个状态。
- Wave 8/9 是可参数化、可重复执行的 release gate，不是首次通过即永久完成的布尔值。每次执行生成
  `CertificationInstance(profileId, enabledSurfaceInventoryDigest, source/contract/image digests, evidence,
  validUntil, supersedes)`。Core instance 通过可授权该 profile 上线，但 Wave 8/9 保持 active；2B、5B、6A-6D
  和全部目标 profile 完成后再运行 `transformation-final` instance，才正式退出 Wave 和整体 Program。
- 首个工程认证基线为 `core-redeem-chat`：启用 Site-bound Identity、personal Workspace/Project、Account/
  Redeem/Credit、General Chat、最小 Artifact/Library、Notification、Support、Core Admin 与 Data Rights；
  Payment、专业 Studio、Public Share、Workspace Collaboration 和 Advanced Agent 默认四层关闭。具体 Site
  可使用 Music/Image 等 Profile，但必须绑定同等级 Core journey 和证据。

## 3. 用户与核心产品旅程

### 3.1 目标用户

- Site 终端用户：在一个独立品牌产品中使用 Chat 或专业 Studio。
- 创作者：在 Project 中反复生成、比较、编辑和导出 ArtifactVersion。
- 高级 Agent 用户：在 Chat 中查看计划、工具、浏览器、文件和后台 Job，但不进入另一套账户层级。
- Site 运营人员：管理本站发布、Offering、用户支持、模型和运行状态。
- Platform 运营人员：跨站管理 Catalog、Provider、模型、Capability、财务事实和系统健康。
- 支持人员：在严格 Site scope、理由、审批和审计下处理用户问题。

### 3.2 关键用户故事

| ID | 用户故事 | 优先级 |
|---|---|---|
| US-01 | 作为站点用户，我只能看到并购买当前站点发布的 Offering | P0 |
| US-02 | 作为站点用户，我刷新或断线后仍能恢复 Chat、Run、Job 和 Artifact 状态 | P0 |
| US-03 | 作为 Chat 用户，我可以 edit/regenerate 并保留原分支历史 | P0 |
| US-04 | 作为 Chat 用户，我可以在对话中启动 Image/Music/Video Job，并在关闭页面后继续运行 | P0 |
| US-05 | 作为 Studio 用户，我可以不经过 GA 直接提交与 Agent 工具相同的 OperationSpec | P0 |
| US-06 | 作为创作者，我可以查看作品版本、来源、参数、父版本和导出记录 | P0 |
| US-07 | 作为用户，我看到的是可解释的余额来源、重置时间、预留、消费和失败状态 | P0 |
| US-08 | 作为运营人员，我可以 preview、approve、promote 和 rollback 一个不可变 SiteRelease | P0 |
| US-09 | 作为财务运营人员，我可以从 Payment Fact 追踪到 Fulfillment、Grant 和退款撤销 | P0 |
| US-10 | 作为模型运营人员，我可以 dry-run 路由并解释最终 Deployment 选择 | P1 |
| US-11 | 作为 Agent 产品设计者，我可以发布 AgentRevision 并配置明确的 Handoff edge | P1 |
| US-12 | 作为用户，我可以选择临时云环境、持久云电脑、本地电脑或浏览器作为 ExecutionTarget | P1 |
| US-13 | 作为开发者，我可以在隔离 Worktree 中查看 diff、checkpoint、rewind、commit 和 PR | P1 |
| US-14 | 作为用户，我可以创建一次性或周期 Routine，并查看每次运行、费用、错误和产物 | P1 |
| US-15 | 作为用户，我可以在 Cloud Browser、Local Browser 和人工 Takeover 之间安全切换 | P1 |
| US-16 | 作为团队用户，我可以在 ProjectContextRevision 中共享 instructions、files、skills、connectors 和输出标准 | P1 |
| US-17 | 作为高级用户，我可以发起 Wide Research/Agent Team，并看到子任务、预算、进度和聚合结果 | P2 |
| US-18 | 作为用户，我可以在 Web、CLI、Desktop、Mobile、IDE 之间继续同一任务，而不复制执行状态 | P2 |
| US-19 | 作为管理员，我可以治理 Plugin、Hook、Connector、Memory、ExecutionTarget 和长期 Routine | P2 |

### 3.3 业务能力架构

Kokoro 的业务层不是“Site + Payment + GA”三个大模块，而是七层能力和一条闭环价值链：

```text
Experience & Growth
  Site / SiteRelease / Surface / SEO / Feature Flags / Experiment Assignment

Identity & Collaboration
  User / Workspace / Membership / BillingAccount / Project / ProjectContextRevision

Product & Commerce
  Catalog / Offering / Quote / Order / Payment / Subscription / Redeem / Fulfillment

Access & Economics
  EntitlementGrant / CreditGrant / Admission / Rating / Usage / Risk Policy

Execution & Automation
  Session / Run / Agent / Operation / Job / ExecutionTarget / Routine / Connector

Content & Delivery
  Asset / ArtifactVersion / Share / Deployment / Notification

Operations & Governance
  Admin / Audit / Approval / Reconciliation / Trust & Safety / Retention / Export / Deletion
```

标准业务价值链：

```text
SiteRelease 选择 Surface、Offering、Agent、Model、Capability 和 Sales Policy
→ User/Workspace/Project 建立独立产品上下文
→ Payment/Redemption/Program Window 进入 Fulfillment
→ EntitlementGrant/CreditGrant 形成可执行权利
→ Admission 编译 ExecutionManifest/OperationAuthorization 并 reserved Hold
→ Run/Operation 在 ExecutionTarget 上执行
→ Model/Capability/Job 原子产生 AttemptUsageFact，Job finalizer 创建 ArtifactVersion
→ Platform usage-rating 摄取 canonical UsageEvidence
→ Rating/Settlement 完成 CreditJournal
→ Library/Share/Deployment/Notification 交付结果
→ Admin/Risk/Reconciliation/Retention 处理长期治理
```

业务规则：

- Site 差异只能通过 Release、Assignment、Policy 和独立 Web composition 表达，不能进入共享核心特判。
- Acquisition source、Execution surface 和 Provider adapter 都不能绕过统一 Fulfillment、Admission、
  Usage、Artifact 和 Audit 链。
- Trust & Safety 可以实时冻结账号、Connection、ModelDeployment、Capability 或 ExecutionTarget，但不得
  修改历史 Fact；恢复使用追加解除事实。
- Notification 由领域事实驱动，不能由页面临时拼装；通知失败不回滚已完成业务事务。
- Retention、Export、Deletion 按 Site policy、法律保留和对象 lineage 执行，不能只删除 UI 行。

## 4. 总体架构决策

### 4.1 采用方案

采用“模块化 Platform Core + 独立执行服务”。

```text
多个独立 Site Web
        │
        ├── Platform API / Worker
        ├── Session
        ├── Job / Workers
        ├── Capability Hub / Runtime
        ├── Model Gateway
        ├── GA
        └── Artifact
```

Platform API 与 Platform Worker 是同一 Platform bounded context 的两个 process role：共享模块代码、
Platform 数据库和事务语义，但可以独立部署、扩缩容。Platform 内模块本地调用，不做 self-RPC。
跨独立 bounded context 使用版本化 RPC 契约；异步事实使用 Outbox/Inbox 和可重放传输。

### 4.2 不采用的方案

| 方案 | 拒绝原因 |
|---|---|
| 每个 Platform 模块一个服务/数据库 | 交易与 Grant 链需要强事务和简单一致性，当前规模不值得承担分布式事务与运维成本 |
| 所有能力塞进 GA | Web、Session、后台和 Direct Studio 都需要调用；Provider、Job、Artifact、Payment 不是 Agent 领域 |
| 一个大单体包含 Session/Job/GA | 运行模型、扩缩容、恢复语义和安全凭据边界不同 |
| 每 Site 复制一套后端 | 造成业务分叉，阻断统一升级和模型/能力运营 |
| 单 Web 项目按 Host 换皮 | 无法实现真实独立 IA、部署、版本、回滚和安全绑定 |

### 4.3 依赖与装配原则

- 每个领域模块输出窄 Application Interface，不暴露数据库模型。
- 跨领域流程由 `workflows/` 编排，不允许模块 A 直接写模块 B 的表。
- Factory 只装配依赖与公开 use case，不持有领域规则。
- transaction-scoped本地application port与remote RPC contract是两类接口：前者只在同一bounded context/UoW内使用；
  后者拥有独立command identity、deadline、receipt和failure semantics。未来提取服务必须重画owner/transaction/saga，
  不承诺“换adapter即可拆分”。
- 不使用 `operation-kernel`、service locator 或全局 mutable registry。
- 不使用 `ports/` 目录；接口放在模块的 `application/contracts` 或 `application/interfaces`。
- 跨语言单源继续使用根 `contract/`，不新增第二个 contracts 仓库。

## 5. 部署单元和数据所有权

| Component / Process Role | 拥有的真源 | 明确不能做 |
|---|---|---|
| Platform API | 通过 Platform modules 读写 Site、Identity、Workspace、Project、ExecutionSpace/Target Assignment、Catalog、Offering、Order、Payment/Refund/Dispute Fact、Fulfillment、Subscription、Entitlement、Credit、Model/Agent、Risk/Growth/DataGovernance、Notification records/policy | 不执行 Agent、Job Worker 或 Provider 模型调用 |
| Platform Worker | 通过同一 Platform modules 执行 webhook inbox、outbox、fulfillment、settlement、reconciliation、周期 materialization 和 notification delivery | 不拥有第二套领域真源，不复制领域规则 |
| Session | Session、Message、MessagePart、Branch、RunLaunchProjection/RunView、Approval/Interaction/PlanProposal projection、SessionEvent、ControlOutbox | 不拥有 RunExecution 或 standalone Proposal，不 resolve 套餐/模型/Capability，不扣积分，不执行 Job |
| Task Projection component（V1 由 Session process 托管） | TaskView read model、跨域 timeline/search projection | 不接受领域 mutation，不成为 Run/Job/Artifact 真源 |
| GA | RunExecution、Checkpoint、RunLease/Epoch、EffectRecord、AgentEventOutbox | 不知道 Site/Plan/Payment，不持有 Artifact/Provider 商业真源 |
| Job | Operation、Job、JobAttempt、WorkerLease、Progress、provider-independent finalization；非模型 adapter 的 callback state | 不拥有 Model Provider callback，不写 Session Message，不修改余额 |
| Execution Runtime component（V1 由 Job process 托管） | TargetRegistration/Connection/CapabilityObservation、Lease、Environment、BrowserSession | 不拥有 Workspace/Project Assignment，不解释 Site/Plan，不持有长期 OAuth/Provider secret 明文 |
| Developer Workspace component（V1 由 Job process 托管） | RepositoryBinding/Revision、Worktree、ChangeSet、CodeCheckpoint、Commit/PR/CI references | 不拥有 Git Provider secret 明文，不把 Worktree 当 ExecutionTarget |
| Automation component（V1 由 Job process 托管） | Routine、Revision、Trigger、Schedule、RoutineRun | 不绕过 Admission，不直接执行 GA |
| Device Gateway | local_device/local_browser 长连接、在线状态、scoped channel | 不读取 Workspace/Credit 领域表，不信任设备自报权限 |
| Capability | Skill/Connector/Plugin/Hook/Command Revision、Package、Connection、SecretRef、CapabilityCall | 不解释套餐和积分 |
| Model Gateway | ModelInvocation、ModelAttempt、ResolutionRecord、runtime HealthObservation、AttemptUsageFact | 不拥有 canonical UsageEvidence，不维护用户余额，不决定客户价格或 Model Catalog |
| Media Resource component（V1 workers可由Job process托管） | Asset module拥有upload/scan/AssetVersion/AssetGrant；Artifact module拥有Artifact/ArtifactVersion/Lineage/Rendition；Blob/Lifecycle module拥有physical reference/retention/GC | 不执行Agent/Provider，不因托管process让Job拥有资源表，也不把scanner evidence当Trust Decision |
| Application Runtime component（V1 由 Job process 托管） | Application/Revision、EnvironmentDeployment、DeploymentRollout、ServiceInstance、health/log reference | 不等同 SiteRelease/Routine/Job，不获得 Platform 内部凭据 |
| Site Web | 路由、品牌、SEO、UI composition、Cookie、浏览器草稿 | 不拥有业务数据，不报价、不写余额 |
| Admin Web | 管理 UI、只读聚合视图、命令入口 | 不直连任何业务领域表 |

Media Resource V1允许workers与Job同部署，但Asset、Artifact和Blob/Lifecycle分别拥有明确application interface、表和对象模型；
Job只编排finalization并消费receipt。相同Blob不合并业务identity，Artifact作为输入使用DerivedInputVersion而非复制bytes。
详见[Asset、Artifact、Blob Ownership、Promotion 与 GC](2026-07-25-asset-artifact-ownership-promotion-gc-design.md)。

唯一权威补充：

- GA 的 `RunExecution` 是 Run 唯一写真源；Session 中 admission 之前的对象明确叫
  `RunLaunchProjection`，不得以 Run 状态机名义接受 terminal/cancel mutation。
- Platform `usage-rating` 是 `CanonicalUsageEvidence`、`RatingSnapshot`、`RatedUsage` 与 `Settlement`
  的唯一 Owner。Model Gateway、Job、Capability Runtime 只拥有本地 `AttemptUsageFact`。
- Platform `model-control` 拥有 ModelDefinition、ProviderAccount metadata/SecretRef、Deployment、CostRate、
  Profile、Pool、RoutePolicy 与 Assignment；Gateway 只拥有实际 invocation/attempt/resolution/health 事实。
- Platform `admin` 是 application façade，不拥有独立业务表；它调用各领域受控 command 并组合只读视图。
- `Project` 归 Platform workspace 模块；Session、Job、Artifact、Developer Workspace 只保存 opaque ProjectRef。
- Payment、Refund、Dispute、Redemption、Fulfillment、SubscriptionTerm、Grant、Hold、Usage、Settlement 必须
  保留不可变 `originSiteId`、BillingAccount、法律责任主体和 source provenance。允许 GlobalScope 查询不等于
  这些事实是无 Site 授权语义的“全局事实”。

## 6. Platform Core 设计

### 6.1 模块

```text
site
identity
workspace
catalog
offering
commerce
subscription
fulfillment
entitlement
credit
usage-rating
payment
model-control
agent-registry
risk-policy
data-governance
growth
notification
audit
admin
```

### 6.2 统一入口和 Factory

```text
createPlatform(dependencies)
  ├── createSiteModule()
  ├── createIdentityModule()
  ├── createCatalogModule()
  ├── createCommerceModule()
  ├── createCreditModule()
  ├── createModelControlModule()
  ├── createRiskPolicyModule()
  ├── createDataGovernanceModule()
  ├── createGrowthModule()
  ├── createNotificationModule()
  └── createAdminModule()
```

`createPlatform()` 返回公开 use cases 和 transport handlers。任何模块不得通过 factory 获取任意其他
repository；跨域只能由显式 workflow 注入所需 use case。

跨模块强事务使用显式 `PlatformUnitOfWork`：

```text
PlatformUnitOfWork.execute(workflow)
  → begin transaction
  → create transaction-scoped application interfaces
  → workflow invokes module interfaces
  → persist domain writes + idempotency record + Outbox
  → commit once
```

- 参与模块不能自行 commit，也不能在同一 workflow 内开启独立业务事务。
- Workflow 只能通过 transaction-scoped application interface 写入，不直接访问其他模块表。
- Fulfillment 可在一个 Unit of Work 中原子创建 Subscription、EntitlementGrant、CreditGrant、
  source idempotency record 和 Outbox event。
- 外部 Provider 调用永远不在 PlatformUnitOfWork 内；先记录 intent/inbox/fact，再由后续事务推进状态。
- API 与 Worker 都使用同一个 UnitOfWork implementation 和 Platform schema。
- `PlatformUnitOfWork`不得跨Session、Job、Gateway、Capability、GA或未来提取service边界传播；跨process使用版本化RPC与
  owner-local transaction/outbox。完整规则见
  [Platform Modular Core 与 Internal RPC](2026-07-25-platform-modular-core-internal-rpc-design.md)。

### 6.3 Site 与可信上下文

核心对象：

```text
Site
SiteProjectBinding
DomainBinding
SiteConfigRevision
AssortmentRevision
SiteRelease
SiteDeploymentBinding
DeploymentObservation
```

配置真源必须唯一：Web 项目拥有 route、品牌资产、SEO、营销页和渲染后的法务内容；Platform 的
SiteConfigRevision 拥有运行时功能、入口开关和业务 assignment。SiteRelease 只记录 Web artifact
及其品牌/法务 manifest digest，不在 Platform 再维护一份可编辑品牌或法务副本。

`SiteProjectBinding` 表示部署身份，不是用户或业务租户：

```text
siteId
provider
providerProjectRef
environment
workloadIdentityRef
allowedScopes
status
```

Site Web BFF 使用 workload identity 或 binding 独立凭据，向 Platform 交换短期签名 `SiteContext`：

```text
bindingId
siteId
releaseId
environment
audience
scopes
issuedAt
expiresAt
```

`SiteContext` 只证明产品部署，不证明操作者身份。所有受保护请求统一使用：

```text
RequestSecurityContext
  trustedProductContext
  actorPrincipal (AnonymousPrincipal | UserPrincipal | OperatorPrincipal | WorkloadPrincipal)
  optional delegatedExecutionGrant
  correlationId / audience / issuedAt / expiresAt
```

- Web BFF：Site workload binding + 本地用户 session/access principal。
- 注册、登录、验证、找回等 pre-auth endpoint 使用 Site-bound `AnonymousPrincipal`，包含匿名会话/设备/risk
  refs，但不伪造 UserPrincipal；成功认证后才升级为本地 UserPrincipal。
- CLI/Desktop/IDE：绑定单 Site registered client 的 OAuth PKCE 或 device flow，不持有 Web workload secret。
- Admin：独立 `OperatorPrincipal` + `SiteScope | GlobalScope`；高风险命令要求 step-up、reason 与 maker-checker。
- Worker：`WorkloadPrincipal`，只能调用自身 audience 的 command。
- GA 调用 Job/Capability/Model：使用 effect-specific `DelegatedExecutionGrant`，不把 User/Site 作为 GA 第二身份轴。
- 每个 mutation 和最终副作用点重新验证 product、actor、audience、scope、expiry、restriction epoch；不得只信
  BFF 转发字段或上游“已验证”的布尔值。

规则：

- 浏览器不得提交可信 `siteId`。
- Host 只能用于路由和诊断，不能成为业务隔离证据。
- SiteContext 交换失败时，所有登录、下单、生成和写操作 fail closed。
- 不回退默认 Site、默认品牌或默认权限。
- Site-scoped repository 自动注入 `siteId`；唯一约束和缓存键包含 Site scope。
- Global Catalog、Provider、Payment Fact 等全局对象不得机械增加 Site filter。
- Admin 跨站必须进入显式 GlobalScope，具备权限、理由和审计。

### 6.4 SiteRelease

`SiteRelease` 是不可变产品发布快照，原子引用：

```text
webArtifact/deploymentRef
siteConfigRevision
assortmentRevision
modelAssignmentRevision
agentAssignmentRevision
capabilityAssignmentRevision
siteFeatureFlagRevision
experimentAssignmentRevision
salesPolicyRevision
legalRevision
contractCompatibility
configDigest
actor/reason/timestamps
```

状态机：

```text
draft → validating → ready → activating → active → retired
   └───────────────→ failed ←──────────────┘
```

`validating` 内完成 effective manifest compile、schema/cross-domain validation、preview deployment 和
smoke/a11y/business-flow tests；`ready → activating` 执行 risk-based approval；`activating → active`
使用 active pointer CAS 并 promote traffic/domain；旧 active 在 drain 完成后进入 retired。

激活不是数据库指针与外部流量提供商之间的伪原子事务。Site 模块拥有 `ActivationAttempt`，记录
provider idempotency key、expected active version、candidate/current/draining deployment set、每一步 observation
与最终 commit receipt。外部 promote 完成后写入 `DeploymentObservation`，reconciler 在 crash 后查询 provider
真实状态并继续同一 Attempt；只有满足冻结 commit predicate 才 CAS active pointer。失败不得创建第二个
Attempt 来掩盖未知结果，旧 Release 在确认 candidate 可承接流量前保持 current。

任何校验或激活失败进入 `failed` 并保留原因。`SiteDeploymentBinding(providerDeploymentRef, releaseId,
artifactDigest)` 将可信部署身份绑定到确切 Release；SiteContext 必须通过这个绑定解析 releaseId，不能由
Web 请求任意声明。激活窗口允许 current/candidate 两个 Release 同时通过验证，但每个部署只能命中自己
绑定的 Release。

审批由 environment/risk policy 决定：preview/dev 可自动化；production 中涉及法律、Merchant、Price、
Entitlement、Model safety 或跨站范围的变更强制 maker-checker。

Site 本身具有独立于 SiteRelease 的产品生命周期：

```text
requested → provisioning → configuring → preview_ready → active
active ↔ suspended
active/suspended → decommissioning → decommissioned
```

- provision 原子关联 owner、独立 Web app/project、domain/certificate、SiteProjectBinding、brand/legal refs 和
  baseline LaunchProductProfile；部分失败可恢复或显式 teardown，不留下可交换 SiteContext 的 orphan binding。
- suspend 是安全/运营命令，冻结新登录/购买/生成策略，但已运行 Job、历史 Artifact、Support/Data Rights 的
  行为由冻结 policy 决定，不能简单整站 404。
- decommission 先阻止新写入，完成用户通知、数据导出、Subscription/Case、retention/LegalHold、domain redirect
  与 certificate/secret 处置，再删除可删资源；不等于直接删除 Site 行。
- domain/certificate 失效、provider project 丢失和 workload identity 撤销有独立 observation/alert/runbook。

失败和回滚：

- 新 Release 未通过全部 gate 时，旧 Release 继续生产服务。
- 回滚前重新执行当前 kill switch、secret revocation、contract/schema compatibility 和安全策略检查；
  通过后以 CAS 重新激活旧不可变 Release，不修改历史交易或已运行 Job。
- 已启动 Run/Job 固定其 ExecutionManifest/OperationSpec，不因 Site 回滚换模型重跑。
- kill switch、账号冻结、secret 撤销和严重安全策略可实时覆盖旧 Release。
- 旧 Tab 在 drain 窗口继续使用原 Release；超过兼容窗口要求刷新。
- `salesPolicyRevision` 冻结 Merchant 和 Payment eligibility；Provider 故障转移只能在同一法律
  Merchant 和冻结 eligibility 内进行，不能因实时健康跨 Merchant 收款。

### 6.5 Growth、Experiment 与 Analytics 边界

```text
AcquisitionAttribution
Experiment
ExperimentRevision
ExperimentAssignment
ExperimentDecisionSnapshot
ExposureFact
OutcomeMetricDefinition
```

- Growth 模块拥有实验定义、版本、确定性 allocation 和 exposure；Analytics/Warehouse 只消费事实并计算
  指标，不成为 SiteRelease、Entitlement、Quote 或 Credit 的授权真源。
- ExperimentRevision 冻结 eligibility、variants、allocation salt、start/end、mutual-exclusion group、primary/
  guardrail metrics；SiteRelease 只引用已验证 Revision，不内嵌可变实验 JSON。
- Assignment 使用可信 Site/User/anonymous subject scope 和稳定 hash；登录前后的 identity stitch 必须显式，
  不能造成用户在一次购买或 Run 中途换 variant。
- Exposure 只在用户真正看到或执行对应变体时以幂等 ExposureFact 记录；页面 render 计划不能冒充 exposure。
- ExperimentDecisionSnapshot 只冻结 experiment/revision/assignment/variant/decisionAt；Quote、Admission 和
  需要可复现的产品操作只引用 Snapshot ID。后发生的 ExposureFact 引用 decisionSnapshotId 与真实
  surface/operation/event，Outcome fact 再引用 ExposureFact；禁止为补 exposure 回写不可变 Snapshot。
- GA 只看已经编译的 Manifest 行为，不接收实验原因。
- Web 内容变体引用 Site Web 项目声明的 typed content slot/key 和 Release artifact digest；Platform 不保存
  第二份可编辑品牌文案，未知 key 在 Release compile 阶段失败。
- 实验可以选择 Surface、文案、排序或已批准的 Offering/Model/Agent assignment，但不能绕过 Catalog、
  Admission、Risk、Rating 和审计。涉及 Price、Merchant、Entitlement 或安全策略的实验仍经过 Release gate。
- AcquisitionAttribution 和分析事件遵守 consent、retention、Site scope 和数据最小化；跨 Site 汇总只能是
  去标识化 Platform analytics，不建立跨站用户身份。
- 后续 Coupon、Referral、Affiliate 只扩展版本化 Quote adjustment、Attribution 或 Fulfillment source；
  免费奖励仍经 FulfillmentProgram → Grant，不能由 Growth 直接改 Price、Subscription 或 CreditJournal。

### 6.6 Identity、Workspace、BillingAccount 与 ExecutionSpace

核心对象：

```text
User
Credential
FederatedIdentity
Workspace
Membership
BillingAccount
Project
ExecutionSpace
```

- User 是 Site-scoped 本地用户，邮箱唯一约束为 `(siteId, normalizedEmail)`。
- 不同 Site 的相同邮箱创建不同 User、Workspace、BillingAccount 和权限记录。
- Cookie、session audience、OAuth redirect 和 CSRF scope 都限定到具体 Site/domain。
- 未来跨站登录使用标准 OAuth/OIDC：`FederatedIdentity(issuer, subject)` 连接到各 Site 的本地 User，
  不自动合并 Workspace、Subscription、Credit 或历史。
- Workspace 是权限与协作主体；Membership 承载角色，不能把 User ID 直接当 Workspace ID。
- BillingAccount 是 Commerce/Credit 的计费主体；它属于一个 Site-scoped Workspace。
- Project 是 Session、Artifact 和产品设置的用户可见容器。
- ExecutionSpace 是 Platform 对执行隔离空间的映射，持有 opaque `namespace`；GA 只消费 namespace，
  不知道它映射到哪个 Site、Workspace 或 Project。
- ExecutionSpace 是逻辑身份/数据隔离边界；ExecutionTarget 是一次运行使用的物理或远程环境。二者正交，
  更换本地/云 Target 不得改变 namespace，也不能把 Target ID 当第二身份轴。
- 默认一个 Project 一个 ExecutionSpace；未来需要共享执行空间时通过显式 Project binding 配置，
  不改变 GA 契约。

### 6.7 Identity/Auth P0 产品闭环

Wave 1 必须以独立产品子 PRD 冻结并验收以下旅程，不能只交付 User/Credential 表：

- 注册、邮箱验证、登录、登出、忘记密码、凭据轮换、账户恢复与删除前重新认证。
- OAuth/OIDC state、redirect allowlist、link/unlink、冲突处理；未来跨站 issuer/subject 复用不自动合并本地 User。
- MFA enrollment/challenge/recovery、异常登录提醒、会话与设备列表、单会话及全设备撤销。
- 所有 token、Cookie、邮件链接、模板、redirect、CSRF 与 rate-limit key 绑定 Site/domain/audience。
- `(siteId, normalizedEmail)` 隔离；相同邮箱在 Site A/B 的注册、找回、邮件、会话和 Support 搜索互不可见。
- 风险依赖不可用时，注册/恢复/敏感变更按冻结 policy fail closed，不退化成仅本机限速。

最低浏览器 E2E 必须覆盖：同邮箱双站注册与找回、过期/重放验证链接、OAuth callback 串站、被盗会话撤销、
MFA recovery、删除前 re-auth。Identity 未通过这些旅程，Core Launch No-Go。

## 7. Catalog、Offering、Payment、Subscription 与 Fulfillment

### 7.1 Catalog

领域模型：

```text
Product
ProductVersion
Feature
Plan
PlanVersion
Price
OfferingVersion
FulfillmentProgramVersion
EntitlementTemplateVersion
CreditProgramVersion
SiteOfferingAssignment
AssortmentRevision
```

规则：

- Product/Plan 是稳定身份；Version、Price、OfferingVersion 发布后不可变。
- ProductVersion 是 `free | credit_pack | subscription | bundle` 的 discriminated union；subscription
  ProductVersion 引用可复用 PlanVersion，其他种类直接引用对应 FulfillmentProgramVersion。
- PlanVersion 是周期、权益和 renewal/upgrade 行为模板，不与 ProductVersion 建立第二套互相竞争的
  商品版本树。
- UI 可以把积分包和订阅统称“套餐”，领域中仍区分产品、权益计划、价格和可售 Offering。
- Catalog 全局定义，不按 Site 复制。
- Site 通过 `SiteOfferingAssignment` 选择展示、购买资格、排序、文案覆盖和生效窗口。
- 关闭 Offering 只阻止新购买，不修改旧 Order 和生效 Subscription 的历史版本。
- Quote 必须冻结 `siteReleaseId`、`billingAccountId`、OfferingVersion、Price、currency、
  `merchantAccountId`、eligible PaymentProviderAccount set、payment routing policy revision、
  FulfillmentProgramVersion、RefundAllocationPolicy、tax/rounding snapshot、相关 ExperimentDecisionSnapshot、
  过期时间和 quote digest。确切 `paymentProviderAccountId` 由 CheckoutSession/PaymentAttempt 选择并冻结，
  不能伪装成 Quote 时已经发生的事实。
- 创建 Checkout 和每次 PaymentAttempt 前重新校验当前 merchant/account kill switch、Risk/Restriction、
  Offering availability 和 Quote expiry；实时安全禁用可以拒绝旧 Quote，但不得把它重路由到另一法律 Merchant。

### 7.2 交易事实链

支付控制对象：

```text
MerchantAccount
PaymentProvider
PaymentProviderAccount
CheckoutSession
PaymentAttempt
Payment
ProviderFact
```

- MerchantAccount 表示法律收款和结算主体。
- PaymentProvider 表示 adapter 类型；PaymentProviderAccount 表示 Merchant、environment 和凭据边界。
- Provider secret 只存 Secret Manager，领域表保存 secret ref 和安全 metadata。
- Site/Offering 通过 assignment 选择允许的 MerchantAccount/PaymentProviderAccount，不能把 Payment
  Provider 配置塞进 Site JSON。

```text
OfferingQuote
→ Order
→ CheckoutSession / PaymentAttempt
→ ProviderFact
→ Payment
→ FulfillmentTransaction
   ├── Subscription
   ├── EntitlementGrant
   └── CreditGrant
```

必须分离的状态：

- Order：用户购买意图和履约总状态。
- PaymentAttempt：一次 Provider IO 尝试。
- Payment：已确认的收款事实投影。
- FulfillmentTransaction：基于某事实签发权益和积分的幂等事务。
- Subscription：持续服务关系及周期。
- Invoice/InvoiceLine：本地应收/账单投影；通过 ProviderObjectMap 关联外部 invoice，不把 Provider
  对象直接当本地域模型。
- ProviderObjectMap 的外部唯一性至少包含 `paymentProviderAccountId + environment + objectType +
  externalId`，避免不同 Provider object type 或账号复用 ID 时误合并。

Order 不使用一个万能 status；至少保持三个正交投影：

```text
paymentStatus
fulfillmentStatus
disputeStatus
```

Wave 2A/2B 子 Spec 分别冻结自身合法状态转移，最低状态集合如下：

```text
CheckoutSession: created | ready | completed | expired | canceled | failed
PaymentAttempt: created | requires_action | processing | succeeded | failed | canceled | unknown
FulfillmentTransaction: pending | running | succeeded | failed | reversing | reversed | reconciliation_required
RefundReservation: reserved | submitted | pending | succeeded | failed | canceled | unknown
Dispute: open | under_review | won | lost | late_won | closed
Subscription: pending | trialing | active | past_due | paused | cancel_scheduled | canceled | expired
```

`unknown` 和 `reconciliation_required` 不能自动映射为 failed；它们必须阻止可能重复的外部副作用，
直到 Provider object retrieval、人工 reconciliation 或确定性 Fact 收口。
`FulfillmentTransaction.running` 表示 durable workflow 正在推进；真正的 Subscription/Grant issuance 或
reversal apply step 仍在单个 PlatformUnitOfWork 中原子提交，不存在“半张 Grant 已签发”的可见状态。

Risk/Restriction 在 PaymentAttempt 已提交后生效，不能拒收随后到达的 ProviderFact。成功 Fact 仍记录
`paymentStatus=paid`，但未完成 Fulfillment 进入 `blocked_risk_review`，由 Moderation/Recovery Case 决定
继续履约或按原 Payment 路由退款；不得把已收款事实伪装成失败或静默吞掉。

Redirect 或前端 success page 不能确认支付成功。Webhook 处理：

```text
WebhookInbox(paymentProviderAccountId, providerEventId)
→ normalized ProviderFact
→ Order/Payment projection
→ idempotent FulfillmentTransaction
```

`PaymentProviderAccount + environment + objectType + externalId` 共同构成外部 ID 命名空间，不能只按 provider
字符串去重。Money 一律使用 ISO currency + integer minor units，禁止 float。

Credit 是 closed-loop、不可转让、不可提现的产品使用额度，不与 Money 混账，也不把 CreditJournal
伪装成法定货币总账。

Fulfillment 使用 discriminated acquisition source，统一后半链但不伪造前半链：

```text
FulfillmentSource =
  PaymentAcquisition {
    paymentFactId, orderId, offeringVersionId, priceId
  }
  | RedemptionAcquisition {
    redemptionId, redeemProgramVersionId, batchId, codeId,
    siteId, billingAccountId, productVersionId, planVersionId?,
    fulfillmentProgramVersionId, liabilityMerchantAccountId,
    termApplicationPolicy
  }
  | AdminGrantAcquisition {
    adminGrantCommandId, actor, reason, approvalRef
  }
  | ProgramWindowAcquisition {
    creditProgramVersionId, subjectRef, windowKey, materializationId
  }
```

Payment source 必须引用 Order/Payment/Offering/Price；Redemption source 禁止制造零金额 Price、Order、
Payment、Invoice 或 Refund。两者只在 FulfillmentTransaction 之后共享 Subscription/Grant/Admission/Usage。
每个 FulfillmentTransaction、FulfillmentCycle、SubscriptionTermAllocation、EntitlementGrant 和 CreditGrant
都保留 root source ref；daily/period window 也不能成为“无来源自动加余额”。

### 7.3 Subscription

- Subscription 是持续关系，只保存稳定 subject、Plan identity、current billing binding 和
  `createdByFulfillmentTransactionId`，不能用单一 acquisitionSource 代表整个生命周期。
- 每个 `FulfillmentCycle/SubscriptionTermAllocation` 引用确切 PlanVersion、FulfillmentProgramVersion 和
  FulfillmentSource；`offeringVersionId/priceId` 仅 PaymentAcquisition source 必填，RedemptionAcquisition
  source 必须为空。续费、第二张 Code、Admin extension 分别形成独立 source lineage。
- PlanVersion 只冻结允许的 renewal modes、DunningPolicy 和 GracePolicy 模板；Fulfillment source 创建
  Subscription 时冻结实际 `SubscriptionBillingBinding(subscriptionId, authority, providerAccountId?,
  externalSubscriptionRef?, scheduleRef?, revision)`，其中 authority 为 `platform | payment_provider | none`。
- provider authority 由规范化 Subscription/Invoice/Payment Fact 驱动 FulfillmentCycle；platform authority
  由 scheduler 创建幂等 RenewalIntent/Invoice/PaymentAttempt；none 表示不会自动续费。authority/account
  迁移必须显式发布新 binding revision，并保证同一周期只有一个 authority 可发起扣款。
- 取消默认只关闭续费，权益持续到当前 period end。
- 降级默认下周期生效；升级是否即时由已冻结 UpgradePolicy 决定。
- 每个续费周期产生独立 FulfillmentCycle 和 Grant provenance。
- renewal identity 至少绑定 Subscription、period、authority 和 attempt ordinal；Invoice、PaymentAttempt、
  FulfillmentCycle 各自幂等。past_due、grace、pause、cancel 的 entitlement/credit 行为由冻结 policy 决定，
  不能由 webhook handler 临场判断。
- Provider webhook 可乱序且不假定所有 Provider 提供 sequence/version。每个 adapter 使用 provider-specific
  reducer，综合 event identity、canonical object retrieval、occurred/received time、状态优先级和本地
  aggregate version；无法确定时进入 reconciliation。
- Payment succeeded 但 Fulfillment 失败时，保持 `paymentStatus=paid` 与
  `fulfillmentStatus=failed|pending_retry`，后台重试并告警，不重复收费。
- 首发同一 `(billingAccountId, serviceScope)` 最多一个 effective base Subscription；相同 Plan 的第二张卡
  采用 `extend_from_max(now,currentPeriodEnd)`，不同 Plan 默认拒绝并要求显式 `ChangePlan` workflow。
  `credit_pack` 只创建独立 Grant，不创建 Subscription。upgrade/downgrade、Term allocation 和旧 Grant
  处理必须由已发布 policy 决定，禁止 Redeem handler 隐式覆盖 active Plan。

### 7.4 Redeem/Card Code

```text
RedeemProgramVersion
RedeemProgramAvailability
RedeemBatch
RedeemBatchAvailability
RedeemCode
RedemptionAttempt
Redemption
RedemptionRevocationFact
RedemptionRevocationCampaign
ReplacementCodeIssuance
SecretDeliveryArtifact
BatchExportArtifact
SecretDeliveryClaim
FulfillmentTransaction
```

- Code 使用 CSPRNG 且至少 128-bit 随机熵；数据库只存带 key version 的 keyed HMAC 和安全 fingerprint，
  不存可恢复明文。除批准的一次性加密 SecretDeliveryArtifact 外，Code 原文不得进入普通 export、event、
  log、trace、analytics、Admin 或 Support。
- 用户 token 使用版本化、可规范化的人类输入格式：public format/key selector + ≥128-bit secret + typo
  checksum；HMAC domain separator 绑定 environment/Site/Program/Batch，防止跨环境或跨批次复用。Secret
  Manager 保留 active Code 所需旧 HMAC key 到 Program retention 到期，rotation 不使未兑换 Code 失效。
- 批量明文只允许一次性加密导出，带 TTL、recipient/distributorRef、maker-checker 和 download audit；
  平台之后不可再次展示。
- Redemption 通过唯一约束和 CAS 原子占用。
- Redeem 不直接改余额，只触发同一 FulfillmentTransaction。
- Program 冻结 ProductVersion、可选 PlanVersion、FulfillmentProgramVersion、liabilityMerchantAccountId、
  Site/用户资格、生效窗口、termApplicationPolicy、stacking limit 和兑换次数，不能在兑换时读取当前 Merchant。
- Redeem 只接受可信 SiteContext 下已登录 User/BillingAccount 的 CSRF-protected command；没有匿名试码接口。
- 枚举攻击统一返回安全错误，并按 Site、账号、IP、设备、Batch 和失败速度多维限速。
- 全局 velocity/risk/revocation 依赖不可用时 Redeem fail closed 为统一 `REDEEM_TEMPORARILY_UNAVAILABLE`，
  Code 不 claim；禁止无声降级为进程内计数或跳过 Risk。Redis 可承载限速状态但不是业务真源，恢复后仍由
  Program/Batch/Code/Risk 的 Platform transaction 决定兑换事实。

Redeem-first production launch 是正式销售模式，不是支付 mock：

```text
SalesPolicyRevision
  acquisitionMode = redeem_only | payment_only | payment_and_redeem | free
  legalMerchantAccountId
  allowedRedeemProgramVersionIds
  eligiblePaymentProviderAccountIds
  paymentRoutingPolicyRevision?

RedeemCode submitted
→ verify SiteContext/User/BillingAccount/CSRF
→ keyed-HMAC lookup + eligibility/current RestrictionEpoch/rate-limit
→ PlatformUnitOfWork
   → recheck SalesPolicy/Program/Batch/Code/Risk epoch
   → CAS claim code
   → Redemption
   → FulfillmentTransaction(source=redemption)
   → optional SubscriptionBillingBinding(authority=none)
   → EntitlementGrant/CreditGrant
   → idempotency + Outbox
→ same entitlement/balance/product projection as paid acquisition
```

- `redeem_only` Site 不要求 Payment Provider account 或 secret；Checkout/payment mutation 在 bootstrap、路由
  和 API Admission 中以 `ACQUISITION_CHANNEL_DISABLED` fail closed，UI 提供独立兑换入口，不把失败支付
  自动改写成兑换。该模式要求 legalMerchantAccountId、至少一个 production-ready Program，且 eligible
  PaymentProviderAccount 集合为空；法律责任 Merchant 可以没有 Payment Provider account。
- SiteRelease compile 校验 SalesPolicy、Program、Site、Merchant liability、Product/Plan、Fulfillment、
  Grant unit 全部兼容，并强制 `Program.liabilityMerchantAccountId == SalesPolicy.legalMerchantAccountId`；
  eligible ProviderAccount 全部属于同一 Merchant/environment 并满足冻结 currency/capture/refund capability，
  payment routing policy 只能是该集合子集。
  Program/Batch live suspension、Restriction 和紧急 kill switch 可覆盖旧 Release。
- RedeemProgramVersion 引用与购买相同的 ProductVersion/PlanVersion/FulfillmentProgramVersion，因此最终
  Subscription、EntitlementGrant、CreditGrant、Usage、Artifact 能力完全相同；差异只在 acquisition source。
- 不创建零金额假 Order、假 Payment 或假退款。Redemption 自身就是取得凭证；如需用户收据，展示
  Redemption/Fulfillment/Grant provenance。
- 卡密 claim、Redemption、Fulfillment 和 Grant issuance 位于同一 PlatformUnitOfWork；任一写入失败全部
  回滚，不能出现“卡已用但权益未到账”。`(siteId,billingAccountId,idempotencyKey)` 重试返回同一
  Redemption；同一 Code 并发最多一个事务成功，其他账号只收到统一失败，不泄漏已用/跨站/过期状态。
- 幂等记录同时绑定 canonical requestDigest，至少覆盖 environment/Site、BillingAccount、Program、Code
  HMAC/fingerprint、term policy 和 command schema version；同 key 同 digest 返回原 Redemption，同 key 不同
  digest 返回 `IDEMPOTENCY_CONFLICT`，不得错误返回旧用户/旧 Code 的结果。
- 卡密签发的 fixed-term Subscription 使用 `authority=none`，到期不自动续费；续期通过新 Redemption 或
  后续真实购买形成新 FulfillmentCycle，不能由 cron 擅自延长。
- Program 必须冻结 `termApplicationPolicy = new_subscription | extend_from_max(now,currentPeriodEnd) |
  reject_if_active`，以及 duration、anchor、Plan mismatch、stacking limit 和 max expiry；第二张订阅卡不能
  由 handler 临场决定覆盖或重叠周期。
- Risk 在 redeem transaction commit 前发生变化时，整个 UoW 回滚且 Code 保持 available；commit 后的新
  Restriction 不改写 Redemption/Grant，只阻止后续 Admission，除非另有正式追加撤销事实。
- 需要人工审核时只创建 RedemptionAttempt 和 RiskCase，不 claim/预留 Code。Attempt 状态为
  `received | evaluating | pending_review | approved | denied | expired | superseded`；批准生成绑定 attemptId、
  requestDigest、review decision、expiry、RestrictionEpoch 的 single-use RedeemApprovalGrant。继续兑换仍重新
  校验 Site/Program/Batch/Code/Risk/余额并运行完整 UoW；期间 Code 被他人使用则安全失败，批准不保证成功。
- 已兑换 Code 永不恢复成可再次使用。售后撤销链固定为：

```text
RevokeRedemption
→ RedemptionRevocationFact
→ FulfillmentReversalTransaction(source=redemption)
   → revoke unused source SubscriptionTermAllocation / recompute effective term
   → revoke remaining EntitlementGrant/CreditGrant
   → consumed amount → RecoveryCase
→ optional ReplacementCodeIssuance / AdminGrant
```

- 撤销只处理该 Redemption 来源的 TermAllocation 和剩余 Grant，不缩短其他 Payment/Redemption/Admin 来源
  已取得的 term；若该 source 是 Subscription 唯一有效来源，effective status 才可投影为 expired/canceled。
  误绑不能转移 owner，使用撤销 + 新 Code/Grant。Replacement 引用原 Redemption/Revocation，并经过 maker-checker。
- 外部售卡方的金钱退款不创建 Platform Payment/Refund Fact；只保存受控、审计后的 external reference，并
  触发 Redemption reversal。Platform 不声称处理了外部资金。
- Payment adapter 后续接入时只新增 ProviderAccount/adapter 和启用 sales policy；不得复制 Catalog、
  Fulfillment、Subscription、Entitlement、Credit 或用户成功页逻辑。

状态机：

```text
RedeemProgramVersion: draft → validating → ready → published
RedeemProgramAvailability: inactive → active ↔ suspended → retired
RedeemBatch: draft → generated → exported
RedeemBatchAvailability: inactive → active ↔ suspended
                         active/suspended → compromised/revoked/expired
RedeemCode: available → redeemed
          available → revoked/expired
BatchExportArtifact: staged → ready → claimed → delivered → destroyed
                   staged/ready/claimed → failed/expired/unknown → destroyed
```

Redemption 是不可变完成事实，不通过 mutable status 重新开放 Code；撤销和补发均为追加事实。
Batch `exhausted` 是所有 Code 均 redeemed/revoked/expired 的可重建 projection，不是与 live Availability
竞争的 mutable terminal state。
Batch suspend/compromise/revoke 立即阻止未兑换 Code；不能自动抹掉已完成 Redemption。对已兑换用户的处理
必须由 scoped Case 生成可审计 RedemptionRevocationFact，避免一次误操作批量吞掉正常用户权益。
- 若 compromised Batch 确需处理多个已兑换用户，创建 maker-checker 的
  `RedemptionRevocationCampaign(planned → approved → running → completed/partially_completed/failed/canceled)`；
  Campaign 冻结 scope/reason/policy，按 RedemptionId 幂等执行独立 reversal，持久化 cursor/result/Case，
  可暂停和恢复。不得在一个大事务中批量删 Grant，也不得把 partial failure 伪装成整批完成。

Secret export/delivery 协议：

- 获批的 `BatchExportArtifact` 是唯一允许短暂包含 Code 原文的载体：生成隔离进程将 plaintext 直接以
  recipient public key/KMS envelope 加密后上传，数据库只保存 encrypted blob ref、cipher/hash、recipient、
  TTL 和 audit metadata；普通 export 永远不含原文。
- `SecretDeliveryClaim` 以 CAS 绑定 artifact、recipient、actor、single-use token、expiry 和 download audit；
  claimed 后只允许同一 claim 在 TTL 内恢复，不签发第二个 claim。确认 delivered 后删除密文并写 GC receipt。
- 进程在 upload/ready 前崩溃时 Batch 保持 inactive；无法证明密文是否安全交付时进入 unknown、自动 suspend
  Batch，并由安全 workflow revoke 未兑换 Code/生成新 Batch，不能重新构造原文。
- encrypted object upload 成功但 DB ready record 失败时，以 object tag/intention id 识别 orphan 并由 GC 删除；
  DB 已生成 HMAC inventory 但 artifact 丢失/损坏时 Batch 永不 activate，只能 revoke 后生成新 Batch，不能从
  HMAC、日志或备份“恢复” plaintext。所有 crash point 都有幂等 resume/GC receipt。
- TTL 到期由 GC 删除 encrypted object 并记录 receipt；ReplacementCode 使用同一 SecretDeliveryArtifact/
  Claim 协议。除这些批准的一次性加密 artifact 外，DB、log、event、trace、Admin、Support 和用户数据导出
  中 Code 原文命中数必须为 0。

Live availability 使用单调 epoch 和数据库锁形成线性化点：

- Program/Batch 的版本化内容不可变，独立 Availability 行保存 `status、availabilityEpoch、reason、actor、
  updatedAt`；suspend/compromise/revoke 在 Platform DB 事务中锁行、推进 epoch、写 Audit/Outbox 后提交。
- Redeem UnitOfWork 以固定顺序取得 `Program Availability FOR SHARE → Batch Availability FOR SHARE → Code
  FOR UPDATE`，验证 expected/current epoch、active status、SalesPolicy 和 Restriction 后才 claim Code。
- Availability update 使用排他锁并等待已经取得 share lock 的兑换事务完成。语义是：可能有一个在停用命令
  线性化之前已获锁的 Redemption 先提交；停用事务 commit/返回之后，不得再有新 Redemption 成功。
- 锁顺序固定为 Program → Batch → Code，所有 publish/suspend/redeem/revoke workflow 共用，避免死锁；
  serialization/deadlock retry 复用原 idempotency key，不生成第二次 Redemption。
- Runtime cache 只能加速读，不能批准兑换；紧急 kill 后即使 cache 未刷新，事务内 availability lock/recheck
  仍 fail closed。事件传播时延只影响 UI，不影响兑换正确性。

### 7.5 Refund、Dispute 与 Reconciliation

真实 Payment 属于 Wave 2B。V1 Provider adapter 默认只支持 automatic capture；若 provider/Offering 需要
manual capture，必须先扩展 `requires_capture/partially_captured` 状态和 CaptureAttempt/Fact，不能把 authorization
当作 paid。同一 Order 的 PaymentAttempt 按 ordinal 串行；存在 unknown Attempt 时禁止再发可能双收款的新
Attempt。redirect success 只表示浏览器返回，不确认付款；webhook 必须按 ProviderAccount/environment 验签，
原始 payload 先进入 Inbox 后异步 normalize/reduce。late success、overpayment、unknown、callback 乱序都进入
append-only Fact + reconciliation，不通过覆盖旧 Attempt 收口。

退款链：

```text
RefundRequest
→ RefundReservation
→ Provider refund request
→ RefundFact
→ source-specific Fulfillment reversal
```

- Pending/failed Provider refund 不能提前宣告退款完成。
- Provider refund request 必须使用原 Payment 冻结的 `paymentProviderAccountId + provider object ref`；
  SiteRelease、Merchant route 或当前健康变化不能把退款切到另一 Provider/account。原账号不可用时进入
  unknown/reconciliation 并告警，不伪造成功。
- 对同一 Payment 始终满足 `successfulRefundAmount + activeRefundReservationAmount ≤ capturedAmount`；
  RefundReservation 创建使用事务锁或 aggregate version CAS。
- RefundReservation 必须把已知 Dispute exposure 纳入可主动退款额度，避免对同一 captured amount 主动
  双退；但 Provider 入站 Dispute Fact 是外部事实，无论本地 refundable amount 是否足够都必须原样入账，
  不得被 invariant 拒绝。超额或并发暴露形成 DisputeCase/RecoveryExposure 投影。
- Provider outcome unknown 时保留 RefundReservation，只有确定失败 Fact 才释放。late win 和多个 Dispute
  只能追加补偿事实，不能改写历史 Fact。
- 只撤销对应 Payment/Fulfillment 来源的剩余 EntitlementGrant 和 CreditGrant。
- Partial refund 对 Grant 的撤销数量使用交易时冻结的 RefundAllocationPolicy 计算，不能由当前套餐
  或当前价格反推。
- 不得为了退款扣除其他购买、免费赠送或其他 Subscription 的 Grant。
- 已消费超过可撤销余额时，普通主动退款按产品策略拒绝或部分退款；Provider 强制 dispute 则记录
  Recovery/Risk Case，不伪造负余额或静默吞掉其他 Grant。
- 一个 Payment 可拥有多个 partial Dispute Fact。
- ProviderBalanceTransaction、Payout/Settlement 和 ReconciliationCase 独立于 Order 状态。
- payment 模块拥有 ProviderBalanceTransaction/Payout/Settlement facts 与 ReconciliationCase；Case 最低状态为
  `open | matched | variance | investigating | resolved`，Resolution 追加证据和 adjustment refs，不改写 Provider Fact。

## 8. Entitlement、Credit 与 Usage Rating

### 8.1 Entitlement

`EntitlementGrant` 的 issuance 是带来源和有效期的不可变事实：

```text
featureKey
subject
sourceRef
effectiveAt/expiresAt
limits
grantTerms
```

Plan 模板与实际 Subscription/Manual override 分开。Platform Admission 解析所有有效 Grant，产出
`AuthorizationDecision`，不把商业原因传给 GA。

撤销使用追加 `EntitlementRevocationFact`，人工覆盖使用新的 `EntitlementGrant` 并引用 override source；
effective status 由 issuance、revocation facts 和时间窗口投影，不原地修改 Grant 历史。

### 8.2 Credit 权威模型

三桶仅是面向用户的余额投影，不是账务 authority。Wave 2A clean replace 当前 decrement-at-hold/
`creditBack()` 机制，权威模型固定为 `CreditGrant + append-only CreditJournal + CreditHoldAllocation`；不在旧
三桶表上继续叠加套餐、卡密或支付逻辑。

Journal 至少有以下 ledger account type：

```text
grant_source_or_liability
customer_available
customer_reserved
customer_consumed
expired
revoked
adjustment
recovery
```

Grant、reserve、capture、release、expiry、revoke 均以同单位借贷平衡的 JournalTransaction 过账；历史 Entry
不可更新，纠错使用引用原交易的 reversal + correction transaction。Release 必须按原 HoldAllocation 回到仍
有效的 Grant，已过期/撤销部分进入对应终结账户，不能复活也不能污染其他来源。

执行预算拓扑只有一棵树：

```text
ExecutionRoot
  → AuthorizationBudget
  → AuthorizationSegment
  → one CreditHold per liability account
  → UsageAllocation / DelegatedBudgetAllocation
```

- Chat Run 创建 root Hold；GA 内 Model/Capability 调用消费其 allocation，不重新预留。
- GA 发起 Job 时授予 `DelegatedBudgetAllocation`；Job 不再按 Direct Studio 流程创建第二份 Hold。
  AgentTeam 的 `ChildBudgetSlice` 是它的受约束子类型，继续服从同一 parent ceiling/守恒协议。
- Direct Studio 是新 ExecutionRoot，独立 admission 与 Hold。
- retry 可产生多个 AttemptUsageFact，但客户承担哪些 Attempt 由冻结 RatingPolicy 决定。
- Hold 不足时只能截断、停止或创建经重新授权的新 Segment，禁止透支和静默换 liability。
- V1 一个 ExecutionRoot 只使用一个 liability account；跨 liability multi-hold 延后，避免含混结算。
- Gateway、Capability、Job、AgentTeam与Target不能各自拿root完整ceiling。Platform Credit owner先以CAS从parent
  `unassigned`原子切出audience-bound child allocation；active children、committed与captured总和永不超过parent。
  unknown额度不可return/reuse，child return必须fence全部descendants。完整协议见
  [Execution Budget Allocation Protocol](2026-07-25-execution-budget-allocation-protocol-design.md)。

```text
CreditAccount
CreditGrant
CreditJournalTransaction
CreditJournalEntry
CreditHold
HoldAllocation
BurnPolicy
BalanceProjection
```

- CreditAccount 以 `BillingAccount + credit unit + liabilityMerchantAccountId` 唯一定位；`originSiteId`
  用于归因，可消费范围由独立 GrantScopePolicy 明确表达，不能把 origin、法律 liability 与 eligibility
  混为一个字段。
- 一个 CreditHold 及其 AuthorizationSegment 只能引用一个 CreditAccount，因此 credit unit 和
  liabilityMerchantAccountId 单一确定；不得在一笔 Hold 中跨 unit 或跨法律 liability 混配 Grant。
- Merchant/Offering assignment 变更只影响新 Quote/Admission；旧 Grant 仍归原 liability account，并按冻结
  GrantScopePolicy 消费或退款。禁止为了新 Merchant 可用性把旧 Credit 静默迁账；确需迁移必须是可审计的
  liability transfer/regrant workflow，不属于普通路由 fallback。
- V1 不实现一次 Admission 跨多个 liability account 的 multi-Hold funding plan；同一 Site + credit unit 对
  正常 acquisition/admission 只能有一个 active liabilityMerchantAccountId。SiteRelease 切换 Merchant 前，
  旧可消费 Grant 必须已用尽/过期，或完成法律批准、Journal 守恒、source provenance 保留的
  LiabilityTransfer/Regrant workflow；否则 compile 阻断。
- BalanceProjection 和 Web 必须按 CreditAccount/liability 展示 `spendableForCurrentSite`，不可把不能共同为
  一次 Operation funding 的旧/新 account 简单相加成虚假“总可用余额”。
- CreditJournalTransaction 内同一 credit unit 的 signed entries 必须和为 0；BalanceProjection 只是可重建缓存。

`CreditGrant` 至少记录：

```text
sourceType/sourceId
originalAmount
effectiveAt/expiresAt
burnPriority
grantScopePolicy
liabilityMerchantAccountId
```

CreditGrant issuance 同样不可变；撤销使用追加 CreditRevocationFact，expiration/exhaustion/effective status
由 issuance、Journal、revocation facts 和时间窗口投影。

三桶语义：

- daily、period、permanent 作为 UX 分类和读模型保留。
- 权威事实是具体 CreditGrant、Journal 和 HoldAllocation，不是三个 mutable 总数字。
- Daily/period 使用访问时惰性 materialization，只为活跃账户创建当前窗口 Grant，不做全量 cron。
- Recurring CreditProgramVersion 必须冻结 calendar zone、period anchor 和 rollover policy；默认
  calendar zone 为 UTC，展示层可转成本地时区。
- 消费排序固定为 `expiresAt ASC NULLS LAST → burnPriority ASC → issuedAt ASC → grantId ASC`；较小的
  burnPriority 先消费，永久 Grant 自然排在有期限 Grant 之后。

CreditHold 生命周期与 Grant 额度去向必须分开：

```text
reserved → committed → settled(capturedAmount, releasedAmount)
    └────→ released/expired

committed → reconciliation_required → settled
```

- 只有 `reserved` Hold 可以因 Admission TTL 释放；执行前必须由 `FinalizeRunAuthorization` 或
  `FinalizeOperationAuthorization` CAS 为 `committed`。
- committed Hold 不得由普通 TTL 自动释放；未发现执行结果时进入 reconciliation_required。
- HoldAllocation 分别记录 reserved/captured/released amount，并指向确切 CreditGrant。
- Grant 在 committed 后过期或被撤销，不阻止已 committed allocation 的合法 capture；未消费释放部分
  根据 release 时 Grant 状态转入 available、expired 或 revoked journal destination。
- 不使用“夹紧三个桶”恢复权威余额。

长运行和等待通过可关闭的执行授权段管理，不让一笔 Hold 覆盖无限生命周期：

```text
AuthorizationSegment
  segmentId/executionRef/manifestId/ratingSnapshotId/holdId
  startedAt/closedAt
  status = reserved | committed | rating_pending | settled | reconciliation_required
```

- Pre-start wait（target/interaction prerequisite 未满足）不得 dispatch，Hold 保持 reserved；短 TTL 到期可
  正常释放。prerequisite 恢复后以同一业务 dedupe identity 重新 Prepare/Finalize，不复制 Run/Operation。
- Mid-execution 进入长期等待前必须关闭当前 Segment：持久化 Evidence、capture 已确定 Usage、release 明确
  未使用额度；只有 outcome unknown 的具体 Attempt/Effect allocation 进入 reconciliation_required。
- Resume 保留原 Manifest、Agent/Context/Rating revision，并重新校验当前 entitlement、余额、Target、
  Connection revocation 和 managed deny，再创建新 Segment/Hold 从 checkpoint 继续。
- 每个等待都有 deadline、notification 和 expiry policy；到期关闭 Segment 并进入 failed/canceled，不静默
  approve、skip 或重放外部 effect。

### 8.3 Usage & Rating

客户计费与 Provider 成本分离：

```text
AttemptUsageFact
→ CanonicalUsageEvidence
→ RatingSnapshot
→ RatedUsage
→ capture/release CreditHold
```

- Admission 冻结客户计费规则、估算、buffer、最小扣费和上限。
- Model Gateway、Job Worker、Capability Runtime 在本地事务中原子保存 terminal Attempt、原始
  `AttemptUsageFact` 和 Outbox；它们不写 canonical UsageEvidence。
- Platform `usage-rating` 以 `producerKind + producerContext + attemptId + evidenceKind + revision` 唯一去重，
  拥有 canonical UsageEvidence、Rating 与 Settlement；修正通过新 revision/correction fact，禁止覆盖历史。
- 每个 Provider Attempt，包括失败 Attempt，都产生独立 Evidence 和成本事实。
- 是否把失败 Attempt 计入客户费用由冻结的产品 RatingPolicy 决定，不由 Gateway 决定。
- Session 的终态 token usage 只用于 UI/观测，不是计费真源。
- Evidence、RatedUsage、Journal 使用稳定 idempotency key；重复事件不得重复 capture。
- Admission 已 reserved 但未 finalize 的 Hold 由 TTL 释放；已 committed 但未观察到执行结果的 Hold 进入
  reconciliation，不得按普通 timeout 直接释放。
- 实际计价不得静默超过已授权 Hold：可预测操作在执行前精确 authorize；可变操作达到预算前必须停止、
  请求增量授权或按冻结 policy 截断。余额不得因运行超支被动变成负数。
- Run/Job 在本地 terminal outcome 与 AttemptUsageFact 已持久化后可展示 `completed / cost_pending`；Rating/Settlement
  异步完成后更新 cost projection。结算失败进入 retry/reconciliation，不得重跑已完成的 Provider side effect。

## 9. Model Control 与 Model Gateway

### 9.1 唯一模型目录

```text
ModelDefinition
ProviderAdapter
ModelProviderAccount
ModelDeployment
ProviderCostRate
DeploymentHealth
ModelProfile
ModelPool
RoutePolicy
PlanModelGrant
ModelAssignment
ModelBundleRevision
ModelOptionRevision
SurfaceModelAssignmentRevision
GatewayConfigRevision
ModelEvaluationSuiteRevision
ModelPromotionDecision
AuthorizedModelRoute
ResolutionRecord
ModelInvocation
ModelAttempt
AttemptUsageFact
```

`ModelDefinition` 是 canonical logical model；`ModelDeployment` 是某 ModelProviderAccount 上的真实部署。
Site、Plan 和 Surface 不复制 ModelDefinition，只通过 assignment 引用 Profile/Pool。

Platform `model-control` 是目录和配置权威；Provider secret 只以 SecretRef 出现在 Control Plane。Admission
根据 SiteRelease、PlanModelGrant、Surface/Agent role 与当前 restriction 编译带 audience/expiry 的
`AuthorizedModelRoute`。Model Gateway 验证授权后才在允许集合中选择 Deployment，并拥有 Invocation、
Attempt、ResolutionRecord、HealthObservation 与 AttemptUsageFact。LiteLLM 只能是 Gateway 内可替换的
provider adapter/router engine：其 DB、virtual key、budget、model list 与 fallback 配置都不是 Kokoro 业务
真源，并受 contract test、kill switch、shadow/canary 与直连 adapter fallback 保护。

模型、Route、Prompt 或 Agent candidate 不能靠人工“试一下”上线。model-control/agent-registry 拥有版本化
EvaluationSuite/Policy 与 PromotionDecision；Evaluation Dataset 只保存受治理的 Artifact/DataRef、许可、PII
与 safety metadata。评测通过普通 `model.evaluate` Operation/Job 调用 Gateway，产生 AttemptUsageFact 和
不可变报告 Artifact；Platform Worker 汇总 quality/safety/latency/cost/parameter/fallback guardrail 后形成
signed decision。candidate 只有经过 offline evaluation → provider contract certification → shadow/canary →
activation 才能进入 assignment；报告失败、数据权利不明或 evidence 过期均阻断 promote。评测不扣用户
Credit，但 Provider cost 必须进入成本事实。

Admission 冻结的是 `ModelProfile + ModelPool + RoutePolicy` revision 和授权 route token，不冻结某个健康
状态瞬变的 Deployment。Model Gateway 在每个 ModelAttempt 开始前选择实际 Deployment，并写
ResolutionRecord；这样既能恢复审计，又能在允许的部署集合内做健康 failover。

### 9.2 模型角色

Agent/Surface 声明角色，不声明 Provider：

```text
assistant.primary
assistant.fast
assistant.reasoning
assistant.summarizer
research.primary
music.assistant
music.generation
image.generation
video.generation
```

组合层使用 `ModelBundleRevision(roleKey → ModelProfileRevision)`；`SurfaceModelAssignmentRevision` 冻结某
Site/Surface 的 default bundle、用户可见 `ModelOptionRevision` 与 hidden internal roles。General Chat、Music、
Video 共用底层 ModelDefinition/Deployment，不复制 model list：Music/Video 的 orchestrator 可复用 Chat 类
Profile，而 generation role 指向专业 Pool。普通用户只选择可见 generation/chat option，内置主模型和
summarizer/orchestrator 可以隐藏但必须在 Release compile 时通过 role completeness 校验。

- General Chat 有自己的内部默认主模型 Profile。
- 用户可见 ModelOption 映射到允许的 Profile，不暴露 Deployment ID。
- Music/Video 同时拥有“理解/编排主模型”和“专业生成模型”。
- SiteRelease 与 PlanModelGrant 决定某站点、产品、套餐可见和可用的 ModelOption。

### 9.3 路由规则

1. 未知、禁用、无权模型 fail closed，不静默回默认。
2. 同 canonical model 的 Deployment failover 优先于跨模型 fallback。
3. 跨模型 fallback 必须由 RoutePolicy 显式允许并满足等价性、隐私和参数约束。
4. 已输出 token、Artifact 或产生 Tool side effect 后，不允许无感跨模型续接。
5. Image/Music/Video 使用 Job 级 equivalence policy，不把不同模型结果假装成同一次 Attempt。
6. Provider secret 只存在于 Vault/Secret Manager 和 Gateway runtime。
7. GA 只调用一个 Gateway adapter，不出现 OpenAI/Anthropic/LiteLLM Provider 分支。

## 10. Session、Run、Operation、Job 与 Artifact

### 10.1 对象定义

| 对象 | 语义 |
|---|---|
| Project | 用户作品、Session、Asset 和默认执行设置的容器 |
| Session | 持续对话容器 |
| Message | 一次用户或助手表达 |
| MessagePart | 可版本化的 typed UI part |
| ConversationBranch | 由 parentMessage 和 active leaf 构成的追加分支 |
| Run | 一次 Agent 图执行 |
| RunActivity | Run 内模型轮、短工具或同步子代理步骤 |
| ChildRun | 有独立生命周期的异步 Agent 子执行 |
| Operation | 用户或 Agent 发起的一次产品能力请求 |
| Job | Operation 下可租约、恢复、排队和重试的异步执行单元 |
| JobAttempt | 一次 Worker/Provider 的真实尝试 |
| Artifact | 用户作品的稳定逻辑身份 |
| ArtifactVersion | 不可变作品版本和 provenance |
| Asset | 用户上传、导入或被 Artifact 引用的可复用输入资源 |
| Blob | 内容寻址的二进制对象 |

`Run` 的唯一权威实现是 GA `RunExecution`。发起者可生成 proposed `runId`，但 GA 必须以
`(namespace, launchIdempotencyKey)` 幂等创建并校验 `runId + executionManifestDigest`；同 key/同 digest 返回
同一 Run，同 key/不同 digest 或相同 runId/不同 launch identity 返回冲突。GA 拥有 started/paused/
terminal、cancel expectedVersion、runEpoch 与最终事件。Platform 只拥有 Admission/Hold，Session 只拥有
`RunLaunchProjection/RunView` 和 ControlOutbox；admission_pending/waiting_prerequisite 不是第二套 Run 状态机。

### 10.2 Job 成立条件

满足任一条件时使用 Job：

- 跨浏览器连接继续。
- 跨进程或 Worker 恢复。
- Provider 原生异步或 callback。
- 需要 queue、priority、progress、retry、reconciliation。
- 结果可能在 Run 结束后产生。
- 需要独立 cancel、timeout 或 lease。

普通模型轮、短同步工具、普通 LangGraph node、同步 subagent 和单纯 UI loading 不创建 Job。

### 10.3 Direct Studio 与 GA Tool

两条入口只在 Admission 前不同：

```text
Direct Studio
  Web → Job.submitOperation façade
      → Platform.prepareOperation
      → signed OperationAuthorization + reserved Hold
      → persist Operation/Job(admission_pending)
      → acquire required TargetLease / pre-start interaction
      → Platform.finalizeOperationAuthorization
      → Job CAS queued + dispatch outbox

Agent Tool
  GA → Job.submitOperation façade with delegated execution grant
     → same prepare/persist/finalize/queue sequence
```

Admission 失败不得持久化可执行 Operation/Job；若为审计保留 rejected request，它必须与 Job queue 隔离。
Finalize 成功但 Job queue CAS/outbox 失败时，reconciler 必须以同一 idempotency identity 完成 queue，或在
确认无 Attempt 开始后通过 Platform reconciliation 释放 committed Hold；不能创建第二个 Operation。

Admission 后统一：

```text
OperationSpec
→ Operation
→ Job
→ JobAttempt
→ Provider Request
→ ArtifactVersion
→ AttemptUsageFact → canonical UsageEvidence
```

Job 的跨 Context 完成使用可恢复 finalization saga：

```text
persist provider outcome + terminal JobAttempt + AttemptUsageFact + outbox
→ Job = finalizing
→ CreateArtifactVersion(jobId/attemptId, idempotencyKey)
→ persist Artifact receipt + local AttemptUsageEvidenceReceipt
→ Job = completed + cost_pending | completed + cost_final
→ async canonical Usage ingest → Rating → Settlement/Correction
```

- Artifact 是该 Operation 的必需产出时，没有 Artifact receipt 不得标 completed。
- Usage 已有 raw fact 但 Rating 未完成时允许 `completed/cost_pending`；没有 raw fact 不允许假完成。
- finalizer crash只重试validation、Blob/Artifact/Trust与producer-local Usage receipt，不重跑Provider effect；canonical
  ingestion/rating/settlement outage不阻塞合格作品completed，但committed allocation不得因timeout释放。
- Provider outcome unknown 保持 Job/Attempt unknown 并由 reconciler 查询，不能进入 finalizing。
- cancel 与 finalization 使用 expectedVersion；late callback 按相同 Attempt/inbox 去重并进入确定性 reducer。

Agent 创建 Job 时显式选择：

- `attached`：Run 等待 Job；Run cancel 可请求 cancel Job；结果回到当前 tool call。
- `detached`：Job 可在 Run 结束后继续；tool 立即返回 JobHandle；Web 展示 durable Job card。

### 10.4 Artifact

```text
Artifact
  stable work identity

ArtifactVersion
  artifactId
  parentVersionId
  operationId/jobId/attemptId
  blobRefs
  parameters/provenance
  mime/dimensions/duration
  createdBy/source
  contentHash
```

- `contentHash` 只标识 Blob 完整性和去重，不标识作品或版本。
- 相同字节来自不同 Operation、授权或作品时仍是不同 ArtifactVersion。
- GA `deliver` 目标改为调用 Artifact API promote workspace file；GA 不持有 Artifact store credential。
- Session 只保存 Artifact/Job 引用和展示投影，不拥有作品库。
- Chat → Studio 使用同一个 `artifactId/versionId`，不复制文件。

## 11. Session 目标设计

### 11.1 Session 拥有

```text
Session
Message
MessagePart
ConversationBranch
RunView
ApprovalProjection
PlanProposal projection
SessionEvent
ControlOutbox
RunJobLink projection
```

Session 不再执行：

- Site、Plan、Entitlement、Credit 解析。
- Hub/Capability 授权解析。
- Provider/模型路由选择。
- 客户价格计算或积分 capture。
- Job Worker 和 Artifact 存储。

Session 发起 Run launch 时调用 Platform `PrepareRun`，保存 `RunLaunchProjection` 与
`manifestId/configurationRevisionId`；Finalize 后以稳定 launchId 调用 GA `LaunchRunExecution`。只有 GA
幂等创建 `RunExecution` 后 Run 才成立，Session 不得自行宣告 Run terminal。

`PlanProposal` 不是 Session 专属真源。它携带 `ownerRef = RunRef | OperationRef | RoutineRunRef |
AgentTeamRunRef`，由真实 initiating aggregate 拥有 lifecycle；Session 只保存对话场景 projection，TaskView
负责聚合，Accept/Reject 命令按 ownerRef 路由。

### 11.2 Typed Message Parts

首批 part 类型：

```text
text
reasoning
citation
tool-call
approval
plan
job
artifact
cost
notice
error
```

- 持久化 projection 返回完整 Message.parts。
- SSE 发送 part create/patch/complete 和 Run/Job 引用更新。
- 浏览器刷新先加载 projection，再 attach active Run/Job；不靠重放全部原始事件重建页面。
- part schema 有独立 version；未知 version 明确降级为 unsupported card，不丢弃消息。

### 11.3 Branch、Edit 与 Regenerate

```text
Message.parentMessageId
Run.triggerMessageId
Session.activeLeafMessageId
```

- Edit 创建新用户消息分支，不修改原消息。
- Regenerate 从同一 trigger 创建新 Run 和助手分支。
- 原工具调用、Job、Approval 和 Artifact provenance 永久保留在原分支。
- 用户切换 active leaf 只改变读视图，不重写历史。

### 11.4 Durable 与 Live 分离

```text
DurableRunEvent
  runId, durableSeq, eventId, runEpoch, schemaVersion, kind, payload

LiveRunDelta
  runId, attemptId, segmentId, offset, kind, payload
```

- Durable event 通过 outbox/inbox、at-least-once 和消费者去重。
- Live delta 明确 best effort，由 durable completed event 收口。
- Session 投影不兼容不得反向把 GA 标记为业务失败；进入 DLQ/告警并保留原事件。

## 12. GA、AgentRevision 与 Handoff

### 12.1 保留范围

保留并加固现有：

- LangGraph/DeepAgents 执行图。
- checkpoint、memory、sandbox。
- HITL、decision ID、control outbox/inbox。
- Skills progressive disclosure。
- Tool effect journal 思想。
- streaming 和 terminal projection 收口。

外围工作可由总体架构直接推进：Platform model-control、独立 Model Gateway/LiteLLM adapter、usage-rating、
Session 投影、Job/Artifact finalization、RequestSecurityContext/RPC，以及 Gateway 提供兼容 GA 当前调用形态的
endpoint。以下任何一项进入实现前必须单独通知用户并取得批准：GA RunLedger/dispatch/terminal/lease/
runEpoch，graph/assembly/swarm，Agent/Prompt/Tool/Skill/MCP 装配，Provider factory/streaming/reasoning 行为，
effect claim/tool journal/unknown recovery，checkpoint schema/activeAgentRevision，namespace key，durable event kind/
terminal semantics，以及 GA 调用 Job delegated grant 的 tool 行为。

### 12.2 ExecutionManifest

Platform Admission 产出不可变 `ExecutionManifest`。GA 只消费：

```text
manifestId/revision
runId/threadId, optional sessionId
opaque namespace
graphRevision
agentTeamRevision
activeAgentRevision
promptRevision
capabilityRevision/grants
model role bindings
projectContextRevision/contextSnapshot
executionTargetPolicy/targetGrant
permissionPolicyRevision
opaque policyDecisionTokenRefs/restrictionEpoch
sandbox/filesystem limits
token/time/tool limits
HITL policy
schemaVersion
trace context
```

Manifest 不包含 Site、User、Workspace、Plan、余额、价格、Provider secret 或授权商业原因。
OperationAuthorization 和各 effect-specific ExecutionGrant 同样携带最小 audience/scope 的 opaque
PolicyDecisionToken/ref 与 RestrictionEpoch，使 Job、Capability、Model Gateway、Artifact publish 和
Execution Runtime 都能在最终副作用点执行同一 revocation 语义，而不暴露商业身份字段。

### 12.3 Agent 与 Handoff

```text
AgentDefinition
AgentRevision
  instructionsRevision
  toolPolicy
  skillRequirements
  mcpRequirements
  modelRoleBindings
  sandboxPolicy
  outputContract

AgentTeamRevision
  agents
  handoffEdges
  initialAgentRevisionId
  contextTransferPolicy
```

- 当前仅替换 prompt 的 swarm 行为正名为 Persona Switch，不作为目标 Handoff。
- Handoff 后接收 Agent 使用自己的 instructions、model roles、skills、tools 和 policy。
- `activeAgentRevisionId` 写入 checkpoint，并产生 durable `agent.handoff` 事件。
- 只能使用 Manifest 中已编译的 handoff edge，不能扫描部署目录自动发现候选。
- Delegation/Subagent 保持父 Agent 主导；Handoff 转移主导权，两者不可混名。

### 12.4 恢复安全

- lease reclaim 递增 `runEpoch`。
- checkpoint write、effect claim、event outbox 和 terminal claim 都校验 expected epoch。
- 旧 Worker 在 lease 转移后的所有写操作由数据库拒绝。
- Tool side effect 必须先 `claimEffect(toolCallId, epoch)`；CAS 输家不得执行工具。
- 已存在 terminal effect 时重放结果；running/unknown effect 不自动重试。
- 新部署恢复旧 Run 时继续使用冻结的 Agent/Prompt/Tool/Model revision。

## 13. Capability Hub 与 Runtime

```text
Capability Control Plane
  Skill/MCP catalog, revision, package, connection, secret refs, admin CRUD

Capability Runtime
  immutable fetch, revocation, discovery, MCP connection/call, audit, interaction
```

- Platform Admission 根据 Site/Plan/Agent assignment 编译 signed CapabilityGrant。
- Session 不直接 resolve Hub 授权。
- GA 不读取 Hub 数据库；通过 immutable bundle/content ref 获取 SkillRevision。
- 高风险 Capability 支持 live revocation epoch。
- MCP secret 只在 Secret Manager 和 Capability Runtime。
- 小型 MCP 授权集向模型暴露冻结的 typed tool schema。
- 大型授权集先 deferred discovery，发现后把 exact typed schema 固定进 Run binding。
- `mcp_call(server, tool, dict)` 只作兼容/兜底，不作为唯一生产工具面。
- 危险工具 approval 发生在调用前。
- Mid-call elicitation 不允许通过从头重跑非幂等 MCP call 恢复；无法保持 ExternalCall/connection
  状态时标记 unknown outcome 或拒绝继续。

## 14. Web 产品架构与 PRD

### 14.1 一 Site 一 Web Project

每个 Site app 独立拥有：

- route tree、首页产品形态和导航。
- 品牌资产、SEO、营销内容、法务文案。
- analytics 和实验入口。
- build、deployment、domain、release 和 rollback。
- Site binding credential。

每个 production Site app/environment 只允许绑定一个 active SiteProjectBinding；不能通过运行时参数把
同一部署切换成另一个 Site。

共享 package 只提供无品牌能力，禁止：

- import 任何具体 Site app。
- 包含品牌文案、Logo 或营销 IA。
- `if (siteId === ...)`。
- 用一个万能 JSON 配置强制所有 Site 使用同一路由和页面壳。

### 14.2 不存在“高级用户工作台产品”

- Chat 始终是 Chat。
- Studio 是 Image/Music/Video 等专业 Surface，不是高级账户模式。
- Chat 遇到复杂任务时可展开 plan、files、browser、Job、Artifact 侧栏；这是同一 Session 的自适应
  工作区，不新增 Work/Task aggregate。
- 一个 Site 可以只开放 Music Studio，完全不显示 General Chat。
- Studio 可提供上下文助手抽屉，但不能退化成 Chat 页面换皮。

### 14.3 Chat P0

- typed MessagePart 和持久 projection。
- SSE reconnect、Run/Job reattach。
- edit、regenerate、branch selector。
- HITL approval/input/review。
- PlanProposal 执行前确认。
- attached/detached Job card。
- Artifact side panel 和 Chat → Studio。
- attachments、citation、tool trace 的分层展示。
- model option、agent profile、effort 的产品级选择；不暴露 Provider ID。
- 余额不足、策略拒绝、Provider 失败、超时、部分完成和 unknown outcome 的可解释错误。
- 移动端可用，复杂工作区按抽屉/分层导航降级。

### 14.4 专业 Studio

共享：

- Studio shell、Project、Operation SDK、Job lifecycle、ArtifactVersion、compare、export。
- schema-driven 基础参数控件。
- prompt assistant、历史、费用估算和运行状态。

专业实现：

- Image：reference、mask、inpaint/outpaint、batch candidates、compare、upscale、版本谱系。
- Music：lyrics、播放器/波形、extend、remix、stem、版本树。
- Video：shot/storyboard、素材引用、长 Job queue、upscale/export。

### 14.5 Library 与 Project

- Project 聚合 Session、Artifact、Asset、收藏和默认执行设置。
- Library 支持按 Project、类型、来源、创建时间、版本和 Job 状态筛选。
- Share 是 Site-bound、可撤销、有过期和访问策略的引用。
- 删除区分软删除、retention、法律保留和对象存储 garbage collection。

### 14.6 Core Web P0 旅程与 Site Fleet

能力清单不能代替可上线旅程。对应 child PRD 必须冻结：

- Chat：onboarding/示例/空状态，新建、列表、搜索、重命名、归档、删除/恢复；Stop、cancel、continue、
  regenerate 的对象和时机语义；刷新、断网、重复提交与 terminal event 丢失恢复。
- Attachment/Asset：选择、客户端预检、分片上传、服务端类型/大小校验、恶意文件扫描、quarantine、配额、
  retry/cancel；未通过扫描的输入绝不创建可执行 Run/Job。
- Studio：draft、autosave version、提交 idempotency、queue、cancel、retry、unknown outcome、compare、export；
  重复点击不创建重复 Operation。
- Library：版本历史、trash/restore、retention、storage quota、rendition/export、Share 的创建/撤销/过期；
  生成成功但 moderation 禁止分享时，生成、分享与费用状态分别解释。
- Account/Redeem：当前 Plan/source/start/end、`authority=none` 不自动续费、Entitlement、三桶投影、available/
  reserved/cost_pending、Grant/Hold/usage receipt、Redeem history、stacking preview、响应丢失恢复和 Support 入口；
  Redeem-only 站点不得显示假 Order/Invoice/Payment/Refund。
- i18n/a11y：locale fallback、时区、数字/Credit 格式、RTL、法务/通知模板版本、keyboard/screen reader、
  browser/mobile matrix 均进入 Release evidence。

多 Site 采用共享 scaffold 而不是复制后漂移：`create-site-app` 生成独立 app/INDEX/release manifest；模板版本、
dependency policy、brand token schema、domain/TLS、preview 环境和 fleet drift 由 Site Fleet 检查。升级通过可审阅
codemod/模板 diff 逐 Site 合入，不在运行时强迫所有 Site 同版发布。

## 15. Admin 产品架构

Admin 通过 Admin BFF 调用 Admin API/RPC，不 import Platform Prisma 或业务表。Admin API 每次重新执行
operator 状态、RBAC、Site scope、审批和审计，不能只相信 email header 和共享 secret。

### 15.1 信息架构

```text
Overview
Site Fleet
Catalog / Offering
Customers / Workspaces
Orders / Payments
Subscriptions / Fulfillment
Credit / Grants / Journal
Redeem Programs
Model Control
Agent / Capability
Session / Run / Job
Artifact / Trust
Reconciliation
Audit / Approval
System Health
```

### 15.2 专用工作流

通用 ResourceTable 仅用于低风险 CRUD。以下必须使用专用 UI 和命令：

- Site provision、domain verification、release preview/publish/rollback、config diff。
- Refund、Dispute、Webhook Inbox、Provider Fact、Settlement、Reconciliation。
- Redeem Program publish、Batch generate/export/activate/suspend/compromise/revoke、Redemption timeline、
  source reversal 和 replacement。时间线展示 Program → Batch → Code fingerprint → Redemption → Fulfillment
  → Subscription/Grant → consumption/reversal，永不展示完整 Code。
- Redemption pending-review queue 支持 approve/deny/expire 和 approval replay audit；compromised Batch 的
  RedemptionRevocationCampaign 支持 dry-run、maker-checker、pause/resume、逐项进度、partial failure/Case。
- CreditGrant provenance、Journal、HoldAllocation、adjust/revoke。
- Model deployment health、cooldown、routing dry-run、Site assignment。
- Session/Run/Job 卡死诊断、cancel、retry、DLQ、ExecutionManifest。
- AgentRevision 发布、Capability revocation、MCP connection/OAuth。
- Artifact 分享撤销、内容治理、retention。

所有 mutation：

```text
idempotencyKey
reason
expectedVersion
actor
site/global scope
correlationId
approvalPolicy
```

高风险财务、跨站访问、发布和 secret 操作要求 step-up authentication、maker-checker 和完整审计。

### 15.3 Trust、Risk 与 Data Governance

```text
RiskPolicyRevision
RiskSignal
RiskDecision
Restriction
RestrictionEpoch
PolicyDecisionToken
ModerationCase
Appeal
RetentionPolicyRevision
ExportRequest
DeletionRequest
DeletionPlan
DeletionParticipantReceipt
LegalHold
```

- RiskSignal 只记录证据；RiskDecision 引用冻结 policy 和 decision reason；Restriction 以追加事实限制
  signup、purchase、redeem、admission、share、deployment 或 connector，不修改历史交易。
- risk-policy 模块拥有 RiskDecision、Restriction 和每个 subject/resource scope 的 monotonic RestrictionEpoch。
  Admission 签发短期 PolicyDecisionToken；Job、Capability、Model Gateway、Artifact publish 和 Execution
  Runtime 在副作用前校验 token，并订阅带签名的 revocation feed 或执行 live check。它们不直读 Platform DB。
- Restriction 生效是安全控制链，不等待 Admin Wave：contract、epoch、fail-closed 和传播时延 gate 必须在
  Wave 1/对应执行 Wave 同步落地；Wave 7 只补齐 Case、Appeal 和运营工作流。
- 内容安全分别在输入、模型/Capability 调用前、Artifact 发布前执行；内部生成完成与公开分享可以有不同
  policy，不能把 moderation failure 伪装成 Provider failure。
- `ContentPolicyProfile` 按 text/upload、Image、Music/Voice、Video/Likeness、Code/Execution、Public Share
  冻结输入权利、年龄/地域、NSFW、版权/许可、声音克隆明示同意、人物肖像/深伪、水印/披露、moderation、
  retention 与 appeal SLA。Site policy 只能在 Platform 法律/安全基线上收紧，不能放宽；对应 Profile 未经
  产品/Legal/Security 批准不得进入 SiteRelease。
- 生成权、下载权和公开分享权是三个可独立决定的状态；moderation 限制分享时，用户仍看到生成终态、费用
  处理、原因类别和申诉入口，不能用模糊 Provider error 隐藏政策决定。
- 用户申诉创建 Appeal 和新的 RiskDecision，不覆盖原决定。
- Export/Deletion 覆盖 Identity、Session、Artifact、Connection、Memory、Payment metadata 和 Audit 的可导出/
  可删除分类；Financial/Audit/LegalHold 按法定 retention 保留最小记录并去标识化。
- 删除是有状态 workflow：request → verify → plan → execute → object GC → verify → completed/failed；
  不允许只删入口表后留下 Blob、Memory、Share 或 Connector token。
- data-governance 模块拥有 RetentionPolicyRevision、Export/DeletionRequest、LegalHold、DeletionPlan 和
  participant receipts；Platform Worker 只运行 workflow。Identity/Workspace、Commerce、Growth、Risk、
  Notification、Session、GA/Memory、Job/Artifact、Automation/Routine、ExecutionTarget/Device、Capability
  等 context 各自实现 versioned export/delete participant API，返回幂等 receipt，不允许 coordinator 跨库删表。
- LegalHold 和 retention 先编译进 DeletionPlan。执行期间，用户主动创建的新内容由 deletion subject
  tombstone 拒绝或纳入同一 request；Payment/Dispute/Subscription cancellation、Audit、LegalHold 等强制
  入站事实始终接收，并以 surrogate/deidentified subject 保留法定最小字段，不能因删除流程拒收。
- 新用户重注册创建新的 subject generation，不被旧 tombstone 永久封锁。只有所有 mandatory participant
  与对象 GC 都有可验证 receipt 后才能 completed；partial/unknown 保持可恢复，不把“请求已接收”展示成
  “数据已删除”。
- DeletionPlan 冻结 `legalHoldEpoch/retentionPolicyRevision`，每个 participant 执行前及 coordinator 宣告
  completed 前重新校验；处理中新增 LegalHold 必须暂停/重算，不得沿用旧计划继续不可逆删除。
- Site 独立意味着导出、删除和 Restriction 默认限定当前 Site；Platform 全局封禁必须使用显式全局 policy、
  高权限和审计。

### 15.4 Admin RBAC 与 Support 产品模型

角色至少区分 `SiteSupport`、`SiteCommerceOperator`、`SiteFinanceApprover`、
`PlatformCommerceOperator`、`RiskOperator`、`SecurityApprover`、`DataGovernanceOperator`、`Auditor` 与
`BreakGlassOperator`；每个 command 登记允许角色、Site/Global scope、step-up、maker-checker、队列 owner
和 SLA。角色不是前端菜单权限，API 必须独立执行授权。

Support 使用正式 aggregate：

```text
SupportCase
CaseMessage
CaseEvidenceRef
CaseTimelineProjection
CaseSla
Escalation
Resolution
```

- Case 必须 Site-scoped；按邮箱搜索不得泄露其他 Site 是否存在同一用户。
- 处理前完成身份核验；受控 impersonation/break-glass 必须短期、只读优先、reason/approval/audit 齐全。
- 标准 case kind 覆盖 Redeem 误绑/未到账/泄漏、余额争议、Run/Job unknown、Artifact moderation/share 申诉、
  删除/导出与安全事件。
- 补偿不允许直接写 Journal：赠送走 AdminGrant acquisition，撤销走 source-specific reversal，纠错走
  CorrectionTransaction，补发走 replacement workflow。
- maker-checker、用户通知与用户可见最终 Resolution 是关闭财务/安全 Case 的必要条件。
- Admin façade 只路由领域 command 和聚合 read model；SupportCase 自身只拥有支持协作状态，不复制业务事实。

## 16. Agent Product Capability Plane

本层补齐 Claude Code 类“深度开发者代理”和 Manus 类“广义行动代理”的共同产品底座。它不改变
Platform/Session/GA 已定义的职责，而是在 Project、Job、Capability 和 Web 之上增加执行环境、长期
自动化、开发者工作空间和多端控制能力。

### 16.1 设计原则

- Client、ExecutionTarget、Agent 和业务 Site 正交：同一 Run 可以从 Web 发起、在本地电脑执行、由
  Mobile 继续控制，但 Site/Workspace/Entitlement 不因此改变。
- Job 是一次执行实例，Schedule/Routine 是长期触发定义，两者不能合并。
- Task 是跨 Session/Run/Job/Artifact 的产品 read model，不成为新的写入 aggregate。
- ProjectContextRevision 是可复现的上下文快照；Memory 是可审计知识，不是权限来源。
- 本地电脑、浏览器和持久云电脑都是高风险 ExecutionTarget，必须显式授权、可撤销和可接管。
- Coding Agent 与 General Agent 复用 Session、Run、Capability、Model、Job、Artifact，只增加
  Developer Workspace Surface 和代码专用 policy。

### 16.2 ExecutionTarget 与环境生命周期

```text
ExecutionTarget
ExecutionEnvironmentRevision
TargetRegistration
TargetCapabilityObservation
TargetConnection
ExecutionTargetLease
WorkspaceMount
BrowserSession
TakeoverLease
TargetHealthObservation
```

Platform `workspace` 模块拥有业务授权对象：

```text
ExecutionTargetAssignmentRevision
  site/workspace/project/repository scope
  referenced targetId or allowed target class
  allowed actions/sharing mode
  managed restrictions/effective window
```

Execution Runtime 拥有技术注册、Capability observation、connection、health 和 lease；Platform 不调度实例，
Runtime 不解释套餐或 Workspace membership。

首批 target kind：

```text
cloud_ephemeral       临时隔离 sandbox，Run/Job 结束后按 retention 回收
cloud_persistent      持久云电脑，文件、进程和服务跨 Session 保留
local_device          用户桌面/服务器，通过 Device Gateway 连接
cloud_browser         云端隔离浏览器，可保存受控登录会话
local_browser         浏览器扩展连接用户现有登录态和本地 IP
```

Worktree 不是第六种 ExecutionTarget，而是 Developer Workspace 在任一支持 filesystem 的 cloud/local
Target 上创建的隔离 checkout；Target 决定“在哪里执行”，Worktree 决定“在哪份代码视图中执行”。

`ExecutionTarget` 记录稳定技术身份和 kind；`ExecutionTargetAssignmentRevision` 表示 Project/Repository
对具体 Target 或 Target class 的允许关系；`Lease` 表示某次 Run/Job 的独占或共享使用权。Target secret、
device token、browser cookie 不进入 Platform、Session、GA Manifest 或事件。

目标选择：

```text
Platform Admission validates Site/Plan entitlement + AssignmentRevision + permission/risk
→ signed TargetAuthorization
→ Execution Runtime validates authorization
→ selects exact online/healthy/capable Target
→ acquires fenced ExecutionTargetLease
→ Platform finalizes Run/Operation authorization
```

- Platform Admission 决定“是否允许使用哪类 Target”，Execution Runtime 决定具体健康实例。
- Job service 内的 Execution Runtime component 拥有 target registry、lease 和 worker scheduling；本地设备
  长连接由可独立扩缩的 Device Gateway 承载，但同一 Monorepo、同一 application contract。
- Device Gateway 只验证设备身份、维护 scoped channel 和转发带签名 action digest/lease epoch 的 TargetCommand；
  它不计算 PermissionPolicy，也不解析 Capability/OAuth secret。Execution Runtime 校验云端 grant，本地
  sandbox/extension 再执行强制校验，二者任一拒绝都不得执行。
- Connector OAuth 默认只由 Capability Runtime 解密和调用；只有显式声明 `local_execution` 的 Connector
  才能由 Secret Broker 根据 ExecutionGrant 签发单次、最小 scope 的 `CredentialLease`：绑定 secretRef、
  target/runtime audience、operation/resource、expiry、revocationEpoch，并标记 `nonPersistable=true`。
- Device Gateway 只转发端到端加密的 CredentialLease material，不读取明文；本地执行器只在 action 生命周期
  内物化，不得写入 workspace、checkpoint、event、log 或 TaskView。长期 Platform/Provider secret 永不进入
  用户 Target。
- cloud_persistent 的运行进程必须有资源、网络、费用、idle、suspend、backup 和 destroy policy，不能
  仅靠 Job TTL 管理。
- local_device/local_browser 离线时进入 waiting_target，不静默切换到云端；跨 target fallback 必须用户或
  RoutePolicy 明确允许。
- 用户 Take Over 创建短期 TakeoverLease，Agent 暂停冲突操作；归还控制权后从明确 checkpoint 继续。

### 16.3 Developer Workspace、Git 与 Checkpoint

```text
RepositoryBinding
RepositoryRevision
Worktree
BranchPolicy
ChangeSet
CodeCheckpoint
CommitReference
PullRequestReference
CIObservation
```

- RepositoryBinding 连接 Project、Git provider/repository、credential ref 和允许分支策略。
- 并行写任务默认每个 ChildRun/AgentTeam member 使用独立 Worktree；共享工作目录必须显式声明并处理冲突。
- ChangeSet 是代码变更的领域记录，引用 base revision、diff summary、测试证据和产生它的 Run/Agent。
- CodeCheckpoint 同时记录 conversation leaf、workspace snapshot/worktree commit、ExecutionManifest 和
  Artifact refs；Rewind 创建新分支/restore action，不删除后续历史。
- Commit、push、PR、merge 属于有外部副作用的 CapabilityCall，遵循 PermissionPolicy、idempotency 和
  BranchPolicy，不由 GA 直接拼接 Provider token。
- Cloud → Local continue、Local → Cloud remote execution 传递的是 RepositoryRevision、ContextSnapshot
  和 Session/Task reference；不复制未提交本地文件，除非通过受控 Workspace Transfer Operation。

### 16.4 PermissionPolicy、ApprovalGrant 与 Interaction

```text
PermissionPolicyRevision
ResourceSelector
ActionClassification
ExecutionGrant
ApprovalRequest
ApprovalGrant
InteractionRequest
```

决策结果：

```text
allow | ask | deny
```

可匹配维度：

```text
tool/capability/operation
filesystem path
network domain
repository/branch
connector/account
execution target
side-effect/risk class
```

ApprovalGrant 合法 scope：

```text
once
current_run
current_operation
current_routine_run
current_agent_team_run
resolved_resource
```

- managed deny 和 sandbox 强制边界不能被用户级 allow 覆盖。
- PermissionPolicy 决定动作是否可以被授权；ExecutionGrant 才是执行点消费的授权证明。模型可见性、prompt
  和 tool schema 都不是安全边界；OS/container/browser sandbox 仍独立强制文件、网络和进程边界。
- ApprovalGrant 绑定 exact action digest、target、resource scope、actor、expiry 和 policy revision；参数变化
  后旧批准失效。
- TaskView 不是授权主体，不存在 `current_task` Grant。跨对象批准必须绑定 TaskRootRef 展开的真实 Run、
  Operation、RoutineRun、AgentTeamRun 和 resolved resource references。
- “此 Project 以后允许”创建新的 PermissionPolicyRevision/PermissionAssignment，并重新经过 managed
  policy、risk、确认和审计；不能通过延长 ApprovalGrant TTL 实现。`persistent_managed` 只属于管理员发布
  的 managed policy，不属于用户 ApprovalGrant。
- URL login、MFA、CAPTCHA、付款确认、浏览器/VS Code 接管使用 InteractionRequest，不伪装成普通消息。
- 无人值守 Routine 只能使用事先批准的 managed policy；需要交互时暂停并通知，不能默认跳过。

```text
ExecutionGrant
  grantId
  audience = capability_runtime | execution_runtime | model_gateway | job
  subjectExecutionRef
  exactActionDigest
  resolvedTargetAndResourceIds
  permissionPolicyRevision/approvalGrantId
  leaseEpoch/controlEpoch/revocationEpoch
  issuedAt/expiresAt
  singleUseOrBoundedUse
```

- Capability Runtime、Execution Runtime、Device local enforcer、Model Gateway 和 Job Worker 在副作用提交前
  校验 audience、digest、resource、epoch、expiry、revocation 和 use count；once Grant 以原子 CAS 消费。
  GA 只携带 grant ref，不自行解释 policy。
- Action digest 使用版本化 canonical encoding 并绑定解析后的真实资源：文件绑定 canonical path/file handle，
  网络绑定最终 scheme/host/port/redirect policy，Git 绑定 repository/branch/base revision，防止 TOCTOU。

### 16.5 Project Context、Instructions 与 Memory

```text
ProjectContextRevision
InstructionSource
ContextSnapshot
MemoryEntry
MemoryRevision
MemoryFeedback
```

ProjectContextRevision 原子引用：

```text
instructions
files/assets
repository bindings
skills/plugins
connectors
model/agent preferences
output standards
execution target defaults
```

- 新 Run/Task 固定 ContextSnapshot；Project 后续修改只作用于新执行或显式 rebase。
- Instruction scope 至少支持 managed organization/site、Workspace、Project、Repository、path 和 user
  preference；优先级明确，低层不能覆盖 managed security policy。
- MemoryEntry 带 source、scope、confidence、createdBy、lastValidatedAt 和 revision；用户可以查看、编辑、
  删除或禁用自动记忆。
- Memory 不能携带 secret、浏览器 cookie 或未经授权的跨 Site 内容。
- Compaction/summary 不能改变冻结 policy、approval、task graph 和未完成 effect；这些保存在结构化状态，
  不依赖自然语言摘要。

### 16.6 Multi-Agent、Wide Research 与 TaskGraph

现有概念保持区分：

```text
Handoff       同一 Run 中主导 Agent 转移
Subagent      父 Agent 委派一个隔离子执行并收回结果
ChildRun      有独立生命周期、控制和费用的 Agent 执行
AgentTeamRun  多个独立 Agent/ChildRun 共享任务图和协作协议
```

新增对象：

```text
AgentTeamRun
TaskGraph
TaskNode
TaskDependency
TaskClaim
TeamMessage
TeamBudgetEnvelope
ChildBudgetSlice
AggregationPlan
```

- Wide Research 是 AgentTeamRun 的一个 Product Profile：自动拆分可并行 TaskNode、为每个节点分配模型、
  Capability、预算、时间和输出 contract，再由 AggregationPlan 合并和去重。
- Agent Team 创建前由用户确认或 Site policy 预授权；不能因为模型认为并行更快就无限扩张。
- AgentTeam Admission 只从 CreditAccount reserved 一次 root CreditHold，并创建 TeamBudgetEnvelope；每个
  ChildRun/Job 在 dispatch 前以 `Prepare/FinalizeChildRunAuthorization` 从 root Hold 原子划出
  ChildBudgetSlice，不得再从账户创建与 root Hold 重叠的独立 Hold。
- TeamBudgetEnvelope 同时限制 credits、token、Job、wall time 和并发；TaskNode retry、新增节点、动态
  fan-out 和 Aggregation Agent 都必须先取得 Slice，子任务不能借用未授权预算。
- 守恒式固定为 `authorized = unallocated + active slices + captured + released`；任一 Slice 的 limit 必须
  完整分解为 active/committed、captured、released 和 reconciliation_required。重分配前先 CAS 释放旧 Slice。
- TaskClaim、concurrency slot 和 ChildBudgetSlice 在同一 Team transaction/CAS 中获得；缺任一项都不得
  dispatch。AttemptUsageFact/canonical UsageEvidence 携带 teamRun/taskNode/childRun/segment/slice refs；
  AgentTeamRun 只聚合，不二次扣费。
- TaskNode 使用 claim/lease/epoch，失败节点按 retry policy 处理；整体可 partial success，不因单节点失败
  丢弃已完成证据。
- 代码类 AgentTeam 默认 Worktree 隔离；媒体/研究类成员通过 Project/Artifact refs 协作，不共享可变目录。
- TeamMessage 和共享 TaskGraph 是结构化 durable state；Agent 之间自由聊天不能成为唯一协调真源。

### 16.7 Schedule、Routine 与事件触发

```text
Routine
RoutineRevision
Trigger
Schedule
RoutineRun
DeliveryPolicy
```

Trigger kind：

```text
one_shot
cron/calendar
webhook
github_event
domain_event
manual
```

RoutineRevision 冻结 prompt/operation、ProjectContextRevision、Agent/Profile、Connector、ExecutionTarget
policy、预算、approval policy、timezone、retry、delivery policy，以及：

```text
concurrencyPolicy = forbid | queue | replace | parallel(maxConcurrent)
interactionDeadline/targetWaitDeadline
maxQueuedRuns
```

- 每次触发创建独立 RoutineRun，再通过正常 Admission 创建新 Run/Operation；Scheduler 不直接执行 GA。
- `same_task` 只表示将新 Run 关联到同一 root Session/Project context；`new_task` 创建新的 Session 或
  root Operation，并由投影生成新的 TaskView，不能复用同一个 active Run。
- Schedule 记录 next fire、jitter、pause、expiry 和 misfire policy；RoutineRun 记录完整历史、费用、错误和
  Artifact refs。
- webhook/event trigger 使用签名、replay protection、dedupe 和 source scope。
- 新 Trigger 在创建 RoutineRun 的同一 dedupe transaction 中应用 concurrencyPolicy。`replace` 只请求取消
  旧执行；旧 side effect 进入 canceled/unknown/reconciliation 并释放互斥资源后，新实例才可取得该资源。
- trusted Routine 可以预授权有限副作用，但 Payment、secret、跨站和高风险发布仍遵守 managed deny/ask。
- Automation component V1 与 Job service 同部署，数据模型和 application interface 独立；规模需要时可拆
  process，不新建 Git 仓库。

RoutineRun 将执行和费用拆成两个正交投影：

```text
executionStatus = triggered | admission_pending | waiting_prerequisite | running | paused |
                  completed | failed | canceled
blockerKind = none | target | interaction
costStatus = none | reserved | committed | rating_pending | settled | reconciliation_required
```

### 16.8 Connector、Plugin、Hook 与 Command

```text
ConnectorDefinition
Connection
OAuthGrantReference
ConnectorRevision
PluginPackageRevision
HookDefinition
CommandDefinition
MarketplaceListing
```

- Capability Control Plane 统一管理 Skill、MCP、Connector、Plugin、Hook 和 Command 的发布、审核、
  assignment、撤销和审计，但保留不同运行语义。
- Connection 是 Site/Workspace/User scoped 的授权关系；OAuth token 只在 Secret Manager，Connection 保存
  scope、subject、expiry、revocation 和 interaction state。
- Hook 绑定明确 lifecycle event，可调用 script、HTTP、prompt、subagent 或 operation；必须声明 failure
  policy、timeout、幂等性和是否阻断主链。
- PluginPackageRevision 可以组合 skills、agents、MCP/connector requirements、hooks、commands 和 UI
  contributions；安装前展示权限清单，升级需要 compatibility/revocation 检查。
- Marketplace 是发行与治理 Surface，不改变 Capability Runtime 的授权真相。

### 16.9 TaskView、多端继续与通知

`TaskView` 是只读聚合。每次用户意图只有一个 `TaskAnchor`：

```text
TaskRootRef = session | operation | routine_run | agent_team_run

Session 内启动 Run/Operation/AgentTeam  → anchor = Session
Routine 触发 Run/Operation/AgentTeam     → anchor = RoutineRun
standalone AgentTeam                     → anchor = AgentTeamRun
standalone Direct Studio                 → anchor = root Operation
```

子对象可以生成可导航 SubtaskView，但不得同时成为另一个顶层 TaskView。

```text
TaskView
  taskRootRef
  site/workspace/project authorization index
  ProjectContext
  optional Session/active branch
  PlanProposal
  Run/ChildRun/AgentTeam progress
  Operation/Job status
  Interaction/Approval
  ArtifactVersion
  Usage/cost projection
```

- TaskView 不拥有任何状态；写操作路由回对应 aggregate/application interface。
- TaskView identity 由 TaskAnchor 唯一派生，不创建承担业务状态的 Task 表。Direct Operation、Routine 或
  Team 可以完全没有 Session；可选 Session 只提供对话 Surface，不能成为 standalone 路径的 lifecycle owner。
- site/workspace/project 字段只是投影授权索引；读取仍以可信 SiteContext 和当前 subject 权限校验，不成为
  第二身份或业务真源。
- Web、CLI、Desktop、Mobile、IDE 和 Browser Extension 使用相同 Session/Task contract，根据设备能力展示
  不同控制面。
- Remote Control 只转发输入、状态和审批；实际 local target 继续在本机执行，浏览器不能获得文件系统凭据。
- Cloud/Local continue 必须明确目标迁移语义：attach 原执行、从 checkpoint fork，或以 ContextSnapshot
  创建新执行；UI 不能把三者混成“继续”。
- Notification 订阅 durable facts，支持 in-app、email、push 和 connector channel；包含 deep link、Site
  scope、去重、偏好、quiet hours 和 delivery attempt，不把通知成功当业务完成条件。

Notification 的权威边界固定为 Platform `notification` 模块：

```text
NotificationPreference
NotificationTemplateRevision
NotificationRequest
NotificationDelivery
NotificationDeliveryAttempt
```

```text
NotificationRequest: accepted | suppressed | expanding | expanded | expanded_with_suppression | failed
NotificationDelivery: pending | queued | sending | provider_accepted | delivered | failed | canceled | unknown
NotificationDeliveryAttempt: created | submitted | accepted | rejected | unknown
```

- 领域只发布事实或显式 NotificationRequest，不直接调用邮件/Push Provider；Platform Worker 根据冻结模板、
  用户偏好、quiet hours、locale 和 Site brand binding 创建 Delivery/Attempt。
- Request 冻结触发事实、recipient scope、source SiteReleaseId、TemplateRevision、brand/legal binding 和 locale；
  历史通知不能因当前 Site 文案改变而换内容。Provider accepted 只表示受理，不等于最终 delivered；没有
  delivery receipt 的 channel 保持 provider_accepted，并以产品定义的可观测状态展示。
- 模板只能引用白名单 payload，不读取其他领域数据库；重试使用 channel-specific idempotency，永久失败进入
  DLQ/运营时间线。In-app inbox 是持久投影，email/push/connector 是可失败交付渠道。
- 安全告警、付款事实和法律通知可以按 Policy 绕过普通 quiet hours/marketing opt-out，但不能绕过法定
  consent 或错误 Site/recipient scope。

### 16.10 Application、Deployment Rollout 与长期服务

```text
Application
ApplicationRevision
EnvironmentDeployment
DeploymentRollout
ServiceInstance
EnvironmentVariableReference
DeploymentObservation
```

- Application 是用户创建的长期产品身份；ApplicationRevision 冻结 Artifact/Repository revision、启动命令、
  端口、配置 schema 和 secret refs；EnvironmentDeployment 记录某 environment/target 的 desired/active
  revision、domain、scale 和 lifecycle policy。
- DeploymentRollout 是将某 ApplicationRevision 应用到 EnvironmentDeployment 的一次变更请求：
  `Rollout → Operation → build/deploy/reconcile Jobs → ServiceInstance observations → active pointer CAS`。
- Job 只表示一次 build/deploy/rollback/reconcile 执行，Job completed 不表示长期 ServiceInstance 停止；
  ExecutionTarget 是承载位置，不是 Deployment；Routine 是触发定义，不是 daemon。
- 一次性脚本用 Job，周期脚本用 Routine，持续监听服务用 EnvironmentDeployment。回滚创建新的 Rollout
  指向旧 ApplicationRevision，不改写历史；失败 Rollout 不覆盖上一 healthy active revision。
- SiteRelease 是 Kokoro 自身某 Site 的 Web/商业/配置原子发布，继续使用 SiteDeploymentBinding，绝不复用
  用户 Application 表。用户 Application 不能引用 Site workload identity 或 Platform internal credential。
- EnvironmentVariableReference 只保存 SecretRef；运行时通过短期 CredentialLease 物化。应用内 Schedule
  仍创建受限 Routine/Trigger，不允许生成绕过 Kokoro Admission 的隐形 cron。

### 16.11 本层验收门

- 同一 Task 可在 Web 发起、local_device 执行、Mobile 审批，namespace 和权限不漂移。
- local_device/browser 离线不静默切 cloud target；Takeover 前后无双重控制和重复副作用。
- 两个代码 ChildRun 在独立 Worktree 工作，合并冲突可见且不会覆盖用户未提交修改。
- Rewind 创建可审计 fork，恢复 conversation、workspace revision 和 Manifest，不删除后续历史。
- allow/ask/deny 与 sandbox 组合满足 managed deny 不可覆盖、批准参数变化即失效。
- Routine 在浏览器关闭后继续；重复 trigger 不重复 Run；每次运行都有费用、结果和错误历史。
- Wide Research 的每个 TaskNode 有预算、lease、progress、来源和输出 contract，部分失败仍可聚合。
- ProjectContext 修改后旧 Run 继续使用原 snapshot，新 Run 使用新 revision。
- Connector 撤销后旧 token 不能调用；等待 interaction 的 Routine/Job 不从头重复外部副作用。
- TaskView 任一投影丢事件后可从各领域真相重建，不成为第二写入真源。

## 17. 关键业务主链

### 17.1 Chat Run

```text
Browser
→ Site BFF verifies session and exchanges SiteContext
→ Session.createMessage
→ Platform.prepareRun
   → membership/site release/entitlement check
   → agent/capability/model role resolution
   → rating snapshot + CreditHold
   → ExecutionManifest
→ if required, Execution Runtime acquires TargetLease from signed TargetAuthorization
→ Session persists RunLaunchProjection + manifest ref
→ Platform.finalizeRunAuthorization CAS reserved Hold to committed
→ GA.LaunchRunExecution(runId, launchId, manifest digest, RunStartAuthorization)
   → atomically persist RunExecution + launch receipt + dispatch outbox
→ Model Gateway / Capability / Job
→ AttemptUsageFact → canonical UsageEvidence
→ Session durable completion projection
→ completed / cost_pending
→ Platform asynchronous rating + settlement
```

失败补偿：

- Admission 失败不创建可执行 Run。
- Target/required pre-start interaction 未满足时，RunLaunchProjection 可持久化为 waiting_prerequisite，但不得 finalize 或
  dispatch；reserved Hold 按短 TTL 释放，恢复时以同一 Run identity 重新 Admission。
- RunLaunchProjection 持久化后必须 finalize authorization 才能调用 GA。Finalize 前失败可释放 reserved
  Hold；Finalize 后 GA 不可达时只重试同一 launchId/runId。只有 GA authoritative lookup 证明不存在
  RunExecution、Attempt 或 effect 后才能释放 committed Hold；不能创建第二个 Run。
- GA unknown outcome 不自动重做外部副作用。
- Session 漏事件时从 durable event/Job 真相重建 projection。

### 17.2 Direct Studio

```text
Browser → Site BFF → Job.submitOperation façade
→ Platform.prepareOperation → reserved authorization
→ persist Operation + Job(admission_pending)
→ acquire required TargetLease / pre-start interaction
→ Platform.finalizeOperationAuthorization
→ Job queued + dispatch outbox
→ Worker / Model Gateway
→ persist ProviderOutcome + AttemptUsageFact + finalization intent
→ idempotent ArtifactVersion receipt + Usage ingestion receipt
→ Job completion + Library projection + cost_pending
→ Platform asynchronous rating + settlement
```

### 17.3 GA 媒体 Tool

```text
GA invoke_operation
→ delegated execution grant
→ same Job.submitOperation
→ delegated ChildBudgetSlice from root AuthorizationBudget
→ same Operation/Job/ArtifactVersion without a second account Hold
```

GA 不携带 Site/Plan/Account；Job/Platform 使用 signed delegated grant 关联原 Run authorization。

### 17.4 支付与卡密

```text
Payment Fact ─┐
Redemption ───┼→ FulfillmentTransaction → Subscription/EntitlementGrant/CreditGrant
Admin Grant ──┤
Account/Program Window ─┘
```

所有来源使用各自 idempotency identity；Fulfillment 按 source 唯一，重复 webhook/兑换请求不重复签发。
免费默认权益、欢迎积分、daily/period window 也通过版本化 Program 和 Fulfillment/Grant 进入统一事实链，
不得由注册、登录或定时脚本直接修改余额。

### 17.5 本地电脑/浏览器与多端继续

```text
Desktop/Browser Extension establishes Device Gateway channel
→ user binds local_device/local_browser to Project
→ Platform.prepareRun resolves allowed target kind
→ Execution Runtime acquires scoped TargetLease
→ GA/Job sends effect commands through Device Gateway
→ local sandbox/permission layer enforces path/domain/action
→ Web/Mobile attaches TaskView and can approve/steer
→ TakeoverLease pauses Agent control when user intervenes
```

TargetConnection、ExecutionTargetLease 和 Takeover 分别使用单调递增的 `connectionEpoch`、`leaseEpoch`
和 `controlEpoch`。每次 Gateway 重连必须推进 connectionEpoch 并立即废弃旧 channel；重新获取执行权推进
leaseEpoch；Agent/User Takeover 的授予和归还都推进 controlEpoch，不能复用旧 epoch。

```text
TargetCommand
  commandId/targetId
  connectionEpoch
  leaseId/leaseEpoch
  controlEpoch
  executionGrantId/actionDigest
  sequence/issuedAt/expiresAt
  payload
```

Gateway 验证 channel、签名和 epoch，本地执行器在副作用前再次验证；任一旧 epoch 的在途命令都拒绝。
Takeover 不是旁路锁：授予时原子切换 `controlMode=user`，归还时切回 `agent` 并从明确 checkpoint 建新命令
序列。设备断线时，未开始命令可取消；已开始但无终态回执的命令进入 unknown/reconciliation，除非能力
具备稳定幂等 identity，否则重连不自动重发。设备自报 capability 只作 observation，最终权限来自
PermissionPolicy、ExecutionGrant 和本地 sandbox。

waiting_target 使用 §8.2 的 AuthorizationSegment：pre-start 时 Hold 不 finalize，mid-run 时先关闭当前
Segment，只让具体 unknown allocation 进入 reconciliation。重连后在同一 Run/Job lineage 重新校验并创建
新 Segment，不让一笔 committed Hold 无限占用余额。

### 17.6 Routine

```text
User/Admin creates RoutineRevision
→ validate ProjectContext/Connector/Target/Permission/Budget
→ Schedule or event Trigger fires with dedupe key
→ create RoutineRun
→ normal Platform Admission
→ create Run or Operation/Job
→ Artifact/Usage/Notification facts
→ Routine history projection
```

Trigger 重放只命中同一 RoutineRun；Schedule 变更创建新 Revision，已运行实例继续引用旧 Revision。
waiting_interaction 不重复执行触发前后的外部副作用。RoutineRevision 冻结 max wait、budget expiry、
interaction/target wait deadline 和 AuthorizationSegment policy；RoutineRun 自身不长期持有一笔 CreditHold。

### 17.7 Wide Research / Agent Team

```text
User goal
→ PlanProposal with decomposition/budget
→ Platform Admission
→ AgentTeamRun + TaskGraph + root Hold/TeamBudgetEnvelope
→ atomic TaskClaim + ChildBudgetSlice
→ parallel ChildRuns/Jobs
→ durable evidence/ArtifactVersion per node
→ AggregationPlan validates, deduplicates and cites sources
→ TaskView partial/final result
→ asynchronous settlement per attempt and team budget
```

取消 Team 时停止未开始节点、请求取消 attached 执行，并保留已完成结果；失败节点不会让已完成研究证据
消失。代码类 Team 额外绑定 Worktree/merge policy。每个节点以 Slice/Evidence 独立 settlement，Team cost
仅为聚合投影；节点重试或预算转移不得越过 root Hold，也不得对同一 Evidence 二次扣费。Team 可以先进入
completed/partially_completed + cost_pending，全部 Slice settled/released/reconciliation-owned 后 cost 才 final。

## 18. 接口与事件

### 18.1 传输原则

- Browser/BFF：HTTP/JSON；流式浏览器传输继续使用 resumable SSE。
- 内部同步：根 `contract/` 下 protobuf/JSON Schema 单源生成 TypeScript/Python 客户端。
- 内部异步：服务本地事务 Outbox → Redis Streams 初期传输 → 消费者 Inbox 去重。
- Redis 不是长期真源；事件可从数据库 Outbox 和领域记录重建。
- 若实际吞吐和多消费者需求超过 Redis Streams，再以同一事件契约迁移 NATS JetStream；不提前引入。
- Task projection 提供 root-kind aware read/event API，例如 `GET /tasks/{rootKind}/{rootId}` 和 events；
  mutation endpoint 只做 typed target routing，必须携带真实 ownerRef/expectedVersion，不能直接修改 TaskView。

每条跨 Context 调用都必须进入 machine-readable RPC/Event registry，字段为：caller、owner、sync/async、
schema source、security audience、deadline、retry class、idempotency key/body digest、receipt、failure owner、
allowed degradation、forbidden fallback。首批权威矩阵：

| 调用 | 模式 / audience | 幂等与恢复 | Failure owner / 禁止 fallback |
|---|---|---|---|
| Site BFF → Platform `ExchangeSiteContext` | sync / `platform.site-context` | binding + request key；只重试 transport failure | Platform；禁止 Host/default Site |
| Site BFF → Session HTTP/SSE/read/control | `SessionAccessGrant` / `session.*` | command key+digest；cursor绑定Site/session/subject generation；snapshot重建 | Session；禁止namespace=owner shortcut、浏览器直连GA或全历史SSE作真源 |
| Session → Platform Prepare/FinalizeRun | sync / `platform.admission` | admission key；Finalize CAS | Platform；禁止 Session 自行授权/扣费 |
| Session → GA LaunchRunExecution/CancelRunExecution | control RPC + async facts / `ga.run-control` | launch key + digest、expectedVersion | GA；禁止 Session 自判 terminal；pre-create cancel 由 launch projection 收口，GA accepted 后只认 GA cancel |
| GA → Model Gateway InvokeModel | streaming / `model-gateway.invoke` | 只在首 token/effect 前按 RoutePolicy retry | Gateway；禁止 GA 直连 Provider |
| GA → Capability Runtime | sync/stream / `capability.invoke` | 按 capability-declared retry safety | Capability；禁止 GA 获取 MCP secret |
| Web/GA → Job SubmitOperation | sync / `job.submit` | operation key + spec digest；delegated slice | Job；禁止 GA 自建后台任务/重复 Hold |
| Job Worker → Model Gateway InvokeModel | sync/async/stream / `model-gateway.invoke-operation` | OperationAuthorization + attempt key；callback 归 Gateway | Gateway/Job finalizer；禁止 Worker 直连模型 Provider |
| Job Worker → Capability Runtime | sync/async / `capability.invoke-operation` | effect-specific ExecutionGrant + attempt key | Capability/Job finalizer；禁止 Worker 获取 connector secret |
| Job → Artifact CreateVersion | sync idempotent / `artifact.write` | attempt + output ordinal；timeout 后查 receipt | Job finalizer；禁止重跑 Provider |
| Attempt producer → usage-rating | outbox/inbox / `usage.ingest` | producer/attempt/kind/revision | usage-rating；禁止 producer 直接 capture |
| 各真源 → Session/TaskView | async facts / `projection.consume` | eventId + aggregateVersion | Projection owner；禁止投影写回真源 |
| Platform → deployment provider | durable intent/reconcile | ActivationAttempt provider key | Site reconciler；unknown 时禁止再次 promote |
| Provider callback → owning Context | inbox/fact | provider account/environment/event id | Domain owner；callback 禁止跨域直接写表 |

`SessionAccessGrant`由Platform根据BFF workload identity、server-resolved SiteContext、AuthSession/actor、workspace/project
membership与current epochs签发；Session在每个HTTP/SSE/read/control effect point使用同一evaluator，并维护最小授权projection。
Session snapshot是完整长期页面projection，SSE只传增量。具体claims、revocation、cursor、non-disclosure与GA opaque boundary以
[Platform/Web/Session P0 Contract Closure](2026-07-25-platform-web-session-p0-contract-closure-design.md)为准。

统一事件 envelope 至少包含 `eventId/eventType/schemaVersion/producer/aggregateType/aggregateId/
aggregateVersion/occurredAt/recordedAt/correlationId/causationId/securityClassification/payload`，并登记 partition
key、Inbox 唯一键、retry/DLQ owner、replay 授权与 compatibility window。Replay 必须证明不会重触发 Provider
副作用。

Usage ingestion 虽走异步 Outbox/Inbox，Job finalizer 仍需确定性 receipt：usage-rating 成功后发布
`usage.evidence.ingested` 并提供按 evidence identity 查询 receipt 的只读接口；event 丢失/timeout 时先查询，
DLQ 由 usage-rating owner 恢复。Wave 4 子 Spec 冻结等待期限、receipt schema 与 cost_pending 条件。

### 18.2 关键命令

```text
ExchangeSiteContext
PrepareRun
FinalizeRunAuthorization
PrepareOperation
FinalizeOperationAuthorization
CreateOperation
CancelJob
RetryJob
AuthorizeModelRoute
InvokeModel
PromoteWorkspaceFile
CreateArtifactVersion
CreateCheckout
FulfillSource
RequestRefund
PublishRedeemProgram
ActivateRedeemProgram
SuspendRedeemProgram
RetireRedeemProgram
CreateRedeemBatch
ExportRedeemBatchOnce
ActivateRedeemBatch
SuspendRedeemBatch
MarkRedeemBatchCompromised
RevokeRedeemBatch
RedeemCode
ApproveRedemptionAttempt
DenyRedemptionAttempt
RevokeRedemption
IssueReplacementCode
CreateRedemptionRevocationCampaign
PauseRedemptionRevocationCampaign
ResumeRedemptionRevocationCampaign
BindExecutionTarget
AcquireExecutionTargetLease
RequestTakeover
GrantApproval
AcceptPlanProposal
RejectPlanProposal
CreateCodeCheckpoint
RewindToCheckpoint
CreateAgentTeamRun
PrepareChildRun
FinalizeChildRunAuthorization
CreateRoutine
PauseRoutine
TriggerRoutine
PublishExperimentRevision
RecordExperimentExposure
EvaluateRisk
ApplyRestriction
LiftRestriction
RequestDataExport
RequestDataDeletion
ExecuteDeletionParticipant
RequestNotification
InstallPlugin
ConnectConnector
RevokeConnection
```

### 18.3 关键事实事件

```text
site.release.activated
site.release.failed/rolled_back
experiment.revision.published/assigned/exposed
payment.attempt.started/succeeded/failed/unknown
payment.fact.recorded
refund.reserved/submitted/succeeded/failed/unknown
dispute.opened/won/lost/late_won
fulfillment.completed/failed/reversed
redeem.program.published/availability_changed/retired
redeem.batch.generated/exported/availability_changed/compromised/revoked
redeem.secret_delivery.ready/claimed/delivered/expired/destroyed/unknown
redemption.completed/revoked/replacement_issued
redemption_attempt.pending_review/approved/denied/expired/superseded
redemption_revocation_campaign.started/progressed/partially_completed/completed/failed
subscription.period.started/changed/cancel_scheduled/canceled
entitlement.granted/revoked
credit.granted/reserved/committed/captured/released/expired/revoked
authorization_segment.reserved/committed/rating_pending/settled/reconciliation_required
run.admitted/started/paused/completed/failed
agent.handoff
operation.created
job.started/progressed/completed/failed/unknown
model.attempt.started/completed/failed
usage.evidence.recorded
usage.rated/settlement.succeeded/settlement.failed
reconciliation.opened/resolved
risk.restriction.applied/lifted
data_export.requested/completed/failed
data_deletion.requested/planned/participant_completed/completed/failed
artifact.version.created
execution_target.connected/disconnected/leased/released
takeover.requested/granted/returned/expired
code_checkpoint.created/rewound
agent_team.started/completed/partially_completed/failed
task_node.claimed/completed/failed
routine.created/changed/paused/triggered
routine_run.admission_pending/started/waiting_target/waiting_interaction/resumed/completed/failed/canceled
routine_run.cost_settled/reconciliation_required
connection.connected/revoked/expired
plugin.installed/upgraded/revoked
notification.requested/suppressed/expanded
notification.delivery.queued/provider_accepted/delivered/failed/unknown/dead_lettered
application.revision.created
environment_deployment.desired_revision_changed
deployment_rollout.started/completed/failed/rolled_back
service_instance.started/stopped/health_changed
```

事件 schema 必须版本化；event ID 用于幂等，领域顺序使用 aggregate version/durable sequence，不使用时间戳猜测。

## 19. 目标目录

```text
apps/
  admin/
  <brand-a>-web/
  <brand-b>-web/

services/
  platform-api/
  platform-worker/
  session/
  job/
  capability-hub/
  capability-runtime/
  model-gateway/
  device-gateway/
  ga/

workers/
  media/
  browser/
  sandbox/
  deployment/

packages/
  application-runtime/
    domain/
    application/
    infrastructure/

  automation/
    domain/
    application/
    infrastructure/

  artifact/
    domain/
    application/
    infrastructure/

  developer-workspace/
    domain/
    application/
    infrastructure/

  execution-runtime/
    domain/
    application/
    infrastructure/

  platform/
    modules/
      site/
      identity/
      workspace/
      catalog/
      offering/
      commerce/
      subscription/
      fulfillment/
      entitlement/
      credit/
      usage-rating/
      payment/
      model-control/
      agent-registry/
      risk-policy/
      data-governance/
      growth/
      notification/
      audit/
      admin/
    workflows/
      publish-site/
      checkout/
      fulfill-source/
      authorize-run/
      authorize-operation/
      settle-usage/
      refund/
      publish-experiment/
      apply-restriction/
      export-subject-data/
      delete-subject-data/
      deliver-notification/

  web/
    bff-runtime/
    platform-client/
    session-client/
    job-client/
    artifact-client/
    task-surface/
    developer-surface/
    chat-surface/
    image-studio/
    music-studio/
    video-studio/
    library-surface/
    commerce-surface/
    design-system/
    i18n/
    telemetry/
    testing/

  runtime/
    contracts/
    operation-sdk/
    capability-sdk/
    execution-target-sdk/
    routine-sdk/
    repository-sdk/
    model-sdk/
    artifact-sdk/
    observability/

  task-projection/
    application/
    infrastructure/

contract/
  spec/
  generated/
```

这是一个 polyglot Monorepo。独立 deployable 不等于独立 Git 仓库。新增 Image/Music/Video 只新增
Surface、Operation definition 和 Worker adapter，不新增子仓库。

### 19.1 INDEX.md 与架构地图治理

`INDEX.md` 是贴近代码的当前架构契约，不是 README 副本、任务进度或历史说明。目标层级：

```text
/INDEX.md                         跨仓依赖、deployable、事实源和入口
apps/<site>/INDEX.md              本 Site route/brand/release ownership 与允许依赖
apps/admin/INDEX.md               Admin BFF、认证和禁止 DB import
services/<service>/INDEX.md       process role、启动入口、公开 transport、数据 owner、运行约束
packages/<bounded-context>/INDEX.md
                                  domain/application public API、事件、表 ownership、禁止依赖
packages/web/<surface>/INDEX.md    Surface contracts、状态归属、扩展方式
```

只在存在公开入口、稳定跨目录 import、持久化、副作用、运行时装配或复杂扩展规则的目录建立 INDEX；不为
每个 route/component/table 机械创建。每份 INDEX 必须包含：

```text
职责 / 非职责
公开 API、exports、transport entrypoints
上游调用方与下游依赖
owned data / emitted-consumed events
runtime、security、idempotency、recovery constraints
扩展位置与禁止 import
仍然有效的 traps
验证命令
```

治理规则：

- 改变目录职责、public export、schema/transport、持久化、副作用或依赖方向时，相关 INDEX 与代码同一
  commit 更新；移动代码同时更新来源与目标 INDEX。
- clean replacement 后直接删除或重写旧 INDEX 中的 Host 多 Site、Session billing、GA Provider、Admin
  DB import、旧版本工具链等描述；不保留“旧方式已废弃”的历史段，Git 已承担历史。
- 根 `docs/CODEBASE_MAP.md` 只保留仓库/deployable/事实源与真实验证命令，并链接相邻 INDEX；不复制包内
  文件清单。`docs/CURRENT.md` 只指向已批准 handbook/spec，不让旧 handoff 重新成为事实源。
- CI 的 `index-coverage` 检查受管 public root 均有 INDEX、INDEX 中路径/命令存在、禁止依赖规则与实际
  import graph 一致；语义准确性由每 Wave 架构 review 和 CODEOWNERS 负责，不能假装纯脚本可理解文字。
- Wave 0 固定治理入口为 `config/architecture/index-roots.yaml`、`docs/templates/INDEX.md`、
  `scripts/architecture/check-index-coverage.ts` 和 `scripts/architecture/check-dependencies.ts`。Manifest 覆盖
  package.json/pyproject/public barrel/transport/migration/process entry roots；豁免必须带 owner、reason、expiry。
- PR diff 若改变受管 root 的 public export、contract/schema、migration、process entry 或 dependency rule，
  `index-coverage` 要求同 PR 修改对应 INDEX；这只能证明“有同步动作”，最终语义仍由 owner review 签署。
- Wave 0 建立根 INDEX、coverage manifest 和校验脚本；后续每个 Wave 的退出条件都包含受影响 INDEX、
  CODEBASE_MAP、handbook/ADR 同步。Wave 8 最终扫描不得留下指向已删除文件、旧 env 或旧 owner 的描述。

## 20. 数据与技术栈

### 20.1 数据存储

目标选择：

- PostgreSQL 18：Platform、Session、Job、Artifact、Automation、Execution Runtime 和 Developer
  Workspace metadata 的事务真源。每个 bounded context 使用
  独立 database/schema owner，不跨 context 直接查询表。Platform API 与 Platform Worker 是明确例外：
  它们是同一 bounded context 的两个 process role，共享 Platform schema 和 UnitOfWork，可使用不同
  database role 收敛权限，但不能拆成两套数据。
- MongoDB：GA checkpoint/memory 在本轮保留，避免为了数据库统一重写成熟 GA；其 access 继续通过
  adapter。是否以后迁移不属于本轮目标。
- S3-compatible Object Storage：Blob、Skill package、workspace archive、Artifact binary。
- Redis：cache、rate limit、短租约、device presence、live fanout、初期 Streams transport；不作业务真源。
- Secret Manager：Provider、MCP、Site binding 和内部服务凭据。

该目标明确覆盖旧 handbook 中“Platform 必须 MySQL、当前不引入 PostgreSQL”的旧决策。覆盖原因：

- 未上线，无生产迁移包袱。
- Platform 的版本化 Catalog、partial unique constraint、JSONB snapshot、Journal、Outbox 和复杂事务
  更适合统一到 PostgreSQL。
- Session 的 typed parts、branch、approval、projection 和 Job link 需要可靠关系约束与事务。
- 保留 GA Mongo 避免无收益重写，体现“按领域选择”而不是机械统一。

在本文书面复审完成前，不修改旧 ADR；正式批准后必须同步更新 handbook、ADR、CODEBASE_MAP 和
运行手册，不能长期保留双事实源。

### 20.2 工具链

```text
Node.js 24 LTS
pnpm 11
TypeScript 5.9
Next.js 16.2
React 19.2
Zod 4
Vitest 4.1
Prisma 7 stable（后端）
PostgreSQL 18

Python 3.12
uv
Ruff
Pyright
Pydantic 2
```

- 根 `package.json`、`pnpm-workspace.yaml`、catalog 和单一 lockfile只锁定Backend、Session、Platform、Admin与共享Web
  capability source。独立Site Web Project不属于根workspace，拥有自己的lock/CI并只消费registry中已签名immutable package。
- Python packages 使用根 uv workspace 和单一 `uv.lock`；GA 特殊 native dependency 必须显式分组，
  不允许服务各自维护不可解释的 Python 版本漂移。
- Admin、Session、Platform与共享package不允许各自漂移TS/Zod/Vitest major；Site Project必须满足发布包compatibility floor，
  但升级通过逐Project lock diff/candidate完成，不由根lock隐式改变。
- Next/React 可因安全修复统一升级 patch，不允许 Site 私自升级 major。
- Prisma 只用于后端；Web app 不生成或 import Platform Prisma Client。
- AI SDK 仅作为 Web typed-part/stream primitive，Session contract 仍是系统真相。
- 对外 Site Web 使用 headless primitives + semantic tokens；Admin 可以继续使用 Ant Design。

### 20.3 Production 部署基线

- 每个 Site Web、Admin、Platform API/Worker、Session、Job、Capability、Model Gateway、Device Gateway、
  GA 产出独立、不可变、带 SBOM 和 provenance 的 OCI image；以 digest 部署，不使用 mutable latest。
- 初始可单区域部署，但 PostgreSQL/Redis/Mongo/Object Storage/Secret Manager 使用托管或具备等价 HA、
  encryption、backup 和 restore 能力的服务；生产凭据与 dev/staging 完全隔离。
- API、stream、worker、scheduler 和 migration 是不同 process role；migration 使用一次性、互斥、可前滚
  job，Web/API 启动不得隐式改 schema。
- 所有 process 实现 startup/readiness/liveness、graceful shutdown、lease drain 和 bounded retry；readiness
  只在依赖可安全承接新工作时通过，不能把外部 Provider 故障等同进程死亡。
- 外部入口经 TLS、CDN/WAF/rate limit；内部调用使用 workload identity、短期凭据和 audience-bound token。
  staging 与 production 拓扑同构，仅容量和 Provider account 不同。
- 发布顺序遵守 expand → compatible deploy → backfill/verify → contract；数据库回滚默认前滚修复。Site Web
  rollback、backend rollback、schema compatibility 和 active Release pointer 分别演练。
- 首发允许 `redeem_only` 且无 Payment Provider，但不允许无 Secret Manager、无备份恢复、无告警、无
  Admin/Support 或用测试 Code batch 进入生产。

每个 child Spec 必须维护 `deployables.yaml`，把目录、数据 Owner 与实际运行单元一一映射，至少登记：

```text
deployable / imageBuildRoot / processRole / command / linkedPackages
ownedSchemaAndDatabaseRole / inboundTransport / outboundDependencies
secretClasses / scalingKey / readiness / leaseAndDrain / releaseOwner
```

覆盖每个 Site Web、Admin、Platform API/Worker、Session API/SSE/projection worker、Job API/scheduler/
reconciler、media/browser/sandbox/deployment worker、Capability Hub/Runtime、Model Gateway、Device Gateway、
GA 当前 control/worker 与 migration one-shot role。同一 image 不等于同一 process role；API、stream、scheduler、
worker、reconciler、migration 必须有独立 command、伸缩、readiness 与 drain 语义。Worker 通过 owner service 的
claim/lease/receipt 工作，不因独立部署获得领域表 ownership。

## 21. 安全、可靠性与可观测性

### 21.1 安全

- Site workload credential 只能交换绑定 SiteContext，Site A 调用 Site B 必须 403。
- 用户身份、Workspace membership、Site scope 在每个写命令重新校验。
- Site-scoped cache、rate limit、idempotency 和 object key 均包含可信 scope。
- Provider/MCP secret 不进入 Session、GA Manifest、event、log 或浏览器。
- local device/browser credential 和 filesystem handle 只停留在 Device Gateway/本地强制层；Web/Mobile 只持
  短期控制 token。
- Plugin/Hook/Connector 安装必须展示 permission manifest，并支持组织级 deny、签名验证和紧急撤销。
- Admin 使用标准 OIDC/SAML 或独立 Admin Session；高风险操作 step-up。
- 所有跨站读取、break-glass、财务调整、发布和 secret 操作写审计。

### 21.2 一致性与恢复

- 本地事务 + Outbox，不在数据库事务中调用外部 Provider。
- 所有外部 command 使用稳定 idempotency key。
- webhook/callback 先落 Inbox/Fact，再推进 projection。
- Job Provider 超时且结果未知时进入 `unknown`/reconciliation，不盲目重试非幂等操作。
- lease 使用 epoch fencing；旧 Worker 写入被拒绝。
- ArtifactVersion 和 canonical UsageEvidence ingestion 在重放时幂等。
- Site release 激活失败不影响旧 Release。
- Routine trigger、Target command、AgentTeam TaskClaim 和 Notification 均有独立 idempotency/epoch；一个
  子系统重放不能复制另一个子系统的副作用。

### 21.3 可观测性

- OpenTelemetry 贯通 Site request、Session、Run、Operation、Job、ModelAttempt、Usage、Payment 和
  Fulfillment correlation。
- 指标至少覆盖 admission latency/deny reason、SSE reconnect、run recovery、job queue/age、
  provider error、model fallback、usage lag、hold age、fulfillment lag、webhook DLQ、release health、
  target online/lease/wait age、routine misfire、interaction wait、team fan-out/budget、redeem success/failure/
  CAS conflict/risk deny/fulfillment lag/batch anomaly/reversal failure 和 notification delivery。
- 日志只记录 opaque ref 和安全 metadata，不记录 prompt secret、Provider key、卡密明文和原始支付敏感字段。
- Admin 提供按 correlationId 聚合的业务时间线。
- 每个 SLO 在对应 Wave 冻结 SLI numerator/denominator、窗口、排除项、数据源、owner、page/ticket 阈值和
  error-budget release policy：Wave 1 覆盖 SiteContext/Auth/Admission，2A 覆盖 Redeem/Fulfillment/Settlement，
  3/5A/4 覆盖 SSE/Run/Gateway/Job。Wave 9 只验证，不能临时补指标定义。
- metrics label 禁止 userId、prompt、Code fingerprint、raw provider error 等高基数/敏感值；Payment/Redeem/
  unknown/reconciliation/security failure trace 强制保留，普通成功链可按冻结策略采样。
- 超过容量 envelope 时使用有界 admission shed/429、per-Site fairness、SSE quota、Job max queue age、Provider
  concurrency 与 worker lease saturation；不得以跳过 Risk/Admission/Usage、丢 Outbox 或无限延长 Hold 降级。

## 22. 失败与边界场景

| 场景 | 预期行为 |
|---|---|
| 浏览器夹带 Site ID | 忽略；只采用签名 SiteContext |
| SiteContext 服务不可用 | 写路径 fail closed，不回退默认 Site |
| Release 引用不存在的 Offering/Model/Agent | Compile 阶段阻断发布 |
| 新 Web 与旧 Platform contract 不兼容 | Compatibility gate 阻断 promote |
| Job 完成时 Site 已回滚 | 按冻结 OperationSpec 完成、结算并创建版本 |
| Provider callback 重放 | Inbox/idempotency 去重，不重复产物和扣费 |
| Payment succeeded、Fulfillment 失败 | paymentStatus=paid、fulfillmentStatus=pending_retry/failed，后台重试和告警 |
| Refund Provider 请求失败 | 保持 pending/failed，不提前撤销 Grant |
| 已消费购买积分后申请全额退款 | 按策略拒绝/部分退款；不扣其他来源 Grant |
| Model 首 token 前失败 | 允许在 RoutePolicy 内 failover |
| Model 首 token 后失败 | 不跨模型拼接；返回部分结果或明确失败 |
| Run cancel 遇到 attached Job | 按 cancel policy 请求取消并等待确认 |
| Run cancel 遇到 detached Job | Job 独立继续，Session 保留 Job card |
| GA lease 被接管 | 旧 epoch 所有写入被拒绝 |
| MCP elicitation 前已产生副作用 | 不从头重跑；保持 ExternalCall 或标 unknown |
| SSE 丢失 Job 完成事件 | 页面从 Job 真相读取并修复 projection |
| Regenerate | 新建分支，不覆盖旧 Job、Tool、Artifact |
| 相同内容来自两个 Operation | Blob 可去重，ArtifactVersion 不合并 |
| Admin 跨站查询 | 必须显式 GlobalScope、权限、理由和审计 |
| local_device/local_browser 离线 | waiting_target；不静默转移到云端，不重复已开始 effect |
| 用户 Take Over 浏览器/IDE | Agent 暂停冲突命令；TakeoverLease 到期或归还后从 checkpoint 恢复 |
| managed deny 与用户 allow 冲突 | managed deny 胜出，拒绝执行并解释 policy source |
| ProjectContext 在 Run 中更新 | 旧 Run 保持冻结 snapshot；新 Run 使用新 revision |
| Schedule/Webhook 重放 | 命中同一 RoutineRun，不重复创建 Run/Job |
| Routine 等待 MFA/登录 | waiting_interaction 并通知；恢复时不重放已完成副作用 |
| Wide Research 单节点失败 | 保留已完成节点和证据，按 AggregationPlan 产出 partial result |
| Agent Team 两成员修改同文件 | Worktree 隔离；merge conflict 显式交给协调/用户，不覆盖 |
| Connector/Plugin 运行中被撤销 | 新调用立即拒绝；进行中 effect 按 revocation policy cancel/unknown/reconcile |
| Code Rewind | 创建可审计 fork/restore，不删除之后的会话、diff 和 Artifact 历史 |
| 实验配置在活跃购买/Run 中变更 | 当前 Quote/Admission 继续使用冻结 assignment；新旅程使用新 Revision |
| Restriction 在已签发 Manifest 后生效 | 副作用前因 RestrictionEpoch/revocation 检查拒绝；已发生 effect 进入正常 Evidence/reconciliation |
| 删除流程中某 context 不可用 | Request 保持 partial/failed 可恢复；不得提前显示 completed 或跳过 mandatory receipt |
| Routine/本地 Target 长期离线 | 证明无 Attempt 后以 reconciliation 零 capture 收口；恢复时重新 Admission，不按 TTL 释放 committed Hold |
| Team 节点重试和预算转移并发 | CAS 保证 parent ceiling；旧 allocation 未释放前不得创建超额 Hold |
| redeem_only Site 调用 Checkout API | fail closed；不要求 Payment Provider，也不创建 Order/Payment |
| 两个请求并发兑换同一 Code | 同一 UnitOfWork/CAS 只有一个成功；另一个返回统一已使用结果，不重复 Grant |
| Code claim 后 Grant 写入失败 | 整个 UnitOfWork 回滚，Code 仍可安全重试；不存在已用未到账 |
| 已兑换卡密被管理员撤销 | Code 仍保持 redeemed；追加 source-specific reversal/revocation，不回写历史 |
| RC 仅在 mock/fake Provider 通过 | 对应 adapter 不得进入 production assignment；redeem_only 不伪造 Payment 认证 |

## 23. 测试与验收门

所有 gate 必须登记 scope，避免 Core Launch 被未启用能力错误阻塞：

- `core-always`：Identity/Site、Redeem、Credit/Usage、Session/Run、Gateway、启用的 Chat/Studio/Library、
  Core Admin/Support、Risk/Governance/Notification、可靠性与安全。
- `if-enabled`：真实 Payment/Refund/Dispute、某个 Studio/Provider/Share/Connector 等，只有进入该
  EnabledSurfaceInventory/assignment 才阻塞该 certification instance。
- `advanced-cut`：Handoff、ExecutionTarget、Developer Workspace、Automation、Application Runtime、AgentTeam、
  多端等；阻塞对应 5B/6A-6D 与包含它的 profile，不阻塞未启用它们的 Core profile。
- `transformation-final`：全计划能力、旧实现/文档/exception 清零和全部目标 profile delta certification；
  只阻塞整体 Program completion。

下文未显式标注的基础架构/安全项默认 `core-always`；Payment 系列默认 `if-enabled`；Agent/Execution/
Developer/Automation/Application/Multi-Agent/多端系列默认 `advanced-cut`；“所有目标能力/全仓清零”默认
`transformation-final`。每份 Release Evidence 必须列出 applied/skipped gate 及 scope reason，禁止 silent skip。

### 23.1 架构测试

- Dependency rule 阻止共享 package import Site app。
- CI 扫描核心代码中的具体 Site 特判。
- Session 包禁止 import Catalog/Credit/Payment/Provider decision 模块。
- GA contract 负向断言 Site/User/Plan/Price/Secret 字段不存在。
- Web/Admin 负向断言不 import 业务 Prisma。

### 23.2 合约和业务测试

- Protobuf/JSON Schema generate-check 零漂移。
- Platform workflow 使用真实 PostgreSQL transaction/outbox 集成测试。
- PlatformUnitOfWork 在 Subscription、EntitlementGrant、CreditGrant、idempotency 和 Outbox 任一写入失败时
  全部回滚，API/Worker 两个 process role 结果一致。
- Credit 使用 property-based test 验证 Journal 守恒、HoldAllocation、expiry、refund 和并发。
- Admission 测试 reserved TTL、finalize CAS、committed 不自动释放、reconciliation 和只有 queued Job 可执行。
- Payment 测试 webhook 重放、乱序、partial refund/dispute、paid-but-unfulfilled。
- Checkout/Subscription 测试 Quote eligible set 与 Attempt exact account 分离、live kill/risk recheck、三种
  SubscriptionBillingBinding authority、同 Plan 的 provider/platform/card-code none、binding migration、
  renewal idempotency、dunning/grace 和同周期不重复扣款。
- Refund/Dispute 并发测试始终满足 refundable amount invariant，unknown reservation 不被提前释放。
  Provider 强制 Dispute 即使造成 RecoveryExposure 也必须入账，不能被本地 invariant 拒绝。
- Redeem 测试 Program/Batch/Code 状态机、128-bit/HMAC key version、一次性加密 export、wrong-site/统一错误、
  多维限速/依赖不可用 fail-closed、并发 CAS、四组 idempotency digest、Risk review/race/UoW rollback、
  Outbox recovery、term stacking、Program/Batch availability 线性化、固定锁序/deadlock retry、export 每个
  crash point/single-use claim/TTL/orphan GC、source-specific TermAllocation reversal/replacement、可恢复
  Campaign，且除批准密文 artifact 外扫描 DB/log/event/trace/Admin/Support/普通 export 无 Code 原文。
- SiteRelease Commerce compile 测试 Program liability、SalesPolicy legal Merchant、Provider account
  Merchant/environment/currency/capture/refund capability、routing subset、单 active liability 任一不匹配均阻断。
- Credit merchant migration 测试旧/新 account 不虚假求和、未完成 Transfer/Regrant 时 Release 被阻断、
  Journal/source provenance 守恒和单 Hold 不跨 liability。
- Risk/Commerce 交错测试分开证明：PaymentAttempt 后的 Provider Fact 永远入账并可 blocked review；Redeem
  commit 前 Risk epoch 变化使整个 UoW 回滚、Code 仍 available，commit 后 Restriction 只限制后续 Admission。
  Payment 退款只走原 provider account，账号不可用进入 reconciliation。
- Model 测试 deployment failover、跨模型 policy、首 token 边界和每 Attempt Evidence。
- Model/Agent promotion 测试 dataset rights/PII metadata、quality/safety/latency/cost guardrail、evidence expiry、
  candidate/shadow/canary/rollback；任一失败或缺失 decision 时 assignment compile 必须拒绝。
- Job 测试 lease reclaim、epoch fencing、unknown outcome、callback replay。
- Session 测试 typed parts、projection + attach、branch/regenerate、approval CAS。
- GA 测试 effect claim CAS、旧 epoch 拒写、冻结 revision 恢复、真实 Handoff。
- Web 使用 Playwright 覆盖两个 Site app 的独立 build、Cookie、品牌、路由、购买和生成链。
- SiteRelease 测试 current/candidate drain、active pointer CAS、失败不切流和回滚前重新验证。
- Release inventory 测试 Surface/route/API/Admin/Capability 全量枚举、revision/evidence/runbook/alert/risk expiry；
  故意启用 hidden route、stub API 或无/过期 Evidence entry 时 compile 必须失败。
- Growth 测试 assignment 稳定性、互斥实验、登录前后 identity stitch、真实 exposure 幂等、consent/retention
  和实验无法绕过 Price/Entitlement/Risk gate。
- Risk 测试 RestrictionEpoch 单调、revocation 传播时延、旧 PolicyDecisionToken 在副作用前被拒绝、跨服务
  fail-closed 与解除限制不改写历史决定。
- Data Governance 测试 LegalHold precedence、DeletionPlan 全 participant、partial/unknown 恢复、执行中新增
  对象、删除中强制 payment/dispute/legal fact、subject generation 重注册、Blob/Share/Memory/Connector token
  GC 和 completed receipt 可验证。
- Notification 测试 Site/recipient scope、偏好/quiet hours、源 Release/模板/brand/legal revision、payload
  白名单、provider_accepted 与 delivered 分离、channel 幂等、重试/DLQ，并证明失败不回滚源业务事务。
- ExecutionTarget 测试 Assignment/TargetAuthorization 分离、connection/lease/control 三重 fencing、旧 channel
  在途命令、设备断线 unknown、capability 欺骗、禁止隐式 fallback 和 Takeover。
- Developer Workspace 测试 Worktree 隔离、用户脏工作区保护、checkpoint/rewind、commit/PR permission。
- Permission 测试 managed deny precedence、TaskView 不作 grant scope、canonical action digest/TOCTOU、once CAS、
  audience/resource/revocation/use-count 执行点校验、CredentialLease 不落盘和 sandbox 逃逸失败。
- ProjectContext/Memory 测试 revision snapshot、scope precedence、secret 拒绝、用户删除和 compaction 恢复。
- Automation 测试 cron jitter/misfire、webhook replay、RoutineRevision、waiting_interaction 和运行历史。
- Agent Team 测试 TaskGraph dependency、TaskClaim+Slice 原子性、root Hold/ChildBudgetSlice 守恒、动态
  fan-out/retry、Aggregation Slice、partial success、取消、cost_pending 和聚合 provenance。
- Connector/Plugin/Hook 测试 OAuth revocation、permission manifest、升级兼容、hook timeout/failure policy。
- 多端 contract 测试 Web/CLI/Desktop/Mobile 对同一 TaskView 的 attach/fork/new-run 语义一致。

### 23.3 必须通过的最终验收

以下是完整能力目录，不代表每个 certification instance 无条件执行全部条目；按 §23 scope 和冻结
EnabledSurfaceInventory 选择。Core instance 不含 `if-enabled/advanced-cut` 时必须证明其 route/API/Admin/
assignment 四层关闭；Transformation-final instance 才要求所有计划条目均有最终证据。

```text
Multi-Site
  两个独立 Site app 可独立部署和回滚；无跨 Site 数据、Cookie、缓存或品牌串味。

Commerce
  Quote → Payment Fact → Fulfillment → Grant 可完整追踪；退款按 source 精确逆转。
  RedeemProgram/Batch/Code → Redemption → 同一 Fulfillment/Grant 可完整追踪；无 Payment adapter 也可启动，
  claim/issuance 原子，reversal/replacement 不影响其他 acquisition source。

Runtime
  Direct Studio 与 GA Tool 产生同结构 Operation/Job/ArtifactVersion。
  浏览器、Session、GA、Worker 任一重启后可恢复。

Agent
  Agent A handoff 后 Agent B 使用自己的模型、skills、tools、policy。
  副作用前后 crash 不产生重复写。

Execution
  cloud ephemeral/persistent、local device/browser 使用同一 Target contract；Worktree 通过 Workspace binding
  运行在支持 filesystem 的 Target 上，不冒充 Target kind。
  离线、Takeover、lease reclaim 和 permission change 不产生双重控制。

Developer
  Repository/Worktree/ChangeSet/Checkpoint/Rewind/Commit/PR 形成可审计闭环。
  并行 Agent 不覆盖用户脏工作区或其他 Agent 变更。

Automation
  Schedule/Event → RoutineRun → Admission → Run/Job 全链幂等、可暂停、可审计。
  ProjectContext、Connector、Target、Budget 和 ApprovalPolicy 均按 Revision 冻结。

Application
  ApplicationRevision → DeploymentRollout/Job → EnvironmentDeployment active pointer 可恢复、可回滚。
  SiteRelease、Routine、Job、ExecutionTarget 与长期 ServiceInstance 生命周期不混淆。

Multi-Agent
  Handoff、Subagent、ChildRun、AgentTeamRun 语义不混淆。
  TaskGraph、TeamBudgetEnvelope/ChildBudgetSlice 守恒、partial success 和 Aggregation provenance 可验证。

Knowledge & Extension
  ProjectContext/Memory 有 scope、revision、provenance 和删除能力。
  Connector/Plugin/Hook/Command 有授权、撤销、升级和运行审计。

Growth & Governance
  Experiment assignment/exposure 可复现且不绕过业务 gate；Restriction 可在执行副作用前实时生效。
  Export/Deletion/LegalHold 有跨 context receipt；Notification 失败不改变源业务终态。

Web
  typed parts、branch、regenerate、HITL、background Job、Chat ↔ Studio 闭环。
  TaskView 在 Web/CLI/Desktop/Mobile/IDE 上保持同一状态语义。

Admin
  零业务 DB import；所有高风险操作有 reason、idempotency、approval、audit。

Toolchain
  单根 catalog/lock；Node/TS/Zod/Vitest 无未批准漂移；所有 Site 独立 build。
```

Redeem-only Production Certification 额外要求：

- 无 PaymentProviderAccount、Payment secret 或 Payment SDK 仍能完整启动、发布和运维。
- Checkout/Payment/Refund route、bootstrap entry、API 和 Admin mutation 四层 fail closed。
- 两个并发用户兑换同一 Code 恰好一个成功；UoW 任一点失败后 Code 未消耗、Grant 未部分签发。
- commit 后进程崩溃由 Outbox 恢复，不重复 Redemption/Fulfillment/Grant。
- wrong-site、expired、revoked、suspended、compromised、restricted Code 安全拒绝且响应不泄漏状态。
- Program/Batch suspend/compromise command 返回后新兑换成功数为 0；与在途兑换的先后关系可由 lock/
  availabilityEpoch/audit timeline 唯一解释。
- fixed-term authority=none；第二张 Code 严格按冻结 stacking/term policy 生效。
- Subscription 每个 FulfillmentCycle/TermAllocation 都有 root source；reversal 只撤销原 Redemption 的剩余
  term/权利，已消费部分进入 Case；replacement 全链审计。
- 除批准的一次性加密 BatchExport/Replacement SecretDeliveryArtifact 外，Code 原文不出现在
  DB/log/event/trace/Admin/Support/普通 export；single-use claim、TTL/GC/crash recovery、compromise/mass
  revoke 均有 maker-checker、告警和演练过的 runbook。
- 成功后的 Admission、Usage、CreditJournal、Artifact 与等价 Payment acquisition 后半链结构一致。
- 切换到 `payment_and_redeem` 不新增第二套 Catalog/Fulfillment/Subscription/Credit/Web success flow；
  Payment refund 不碰 Redemption Grant，Redemption reversal 不碰 Payment Grant。

### 23.4 分层验证策略

| 层级 | 必须证明 | 运行环境与门槛 |
|---|---|---|
| Static/Architecture | 类型、schema、生成物、依赖方向、Site 特判、secret/import 禁令、INDEX coverage | 每 PR；任一错误阻断 |
| Unit/Property | 状态转移、Money/Credit/Journal/Hold/Slice 守恒、policy precedence、canonical digest | 每 PR；关键领域 mutation/property seed 可复现 |
| Component | 单 process role 的 HTTP/SSE/worker/lease/recovery、错误映射、graceful shutdown | 每 PR；真实 runtime + isolated dependencies |
| Contract | TypeScript/Python generated clients、向前/向后兼容、event schema、unknown version | 每 PR；producer/consumer 双向矩阵零漂移 |
| Integration | PlatformUnitOfWork、PostgreSQL constraint/outbox、Redis replay、Mongo checkpoint、S3 lifecycle、Secret lease | 每 PR/nightly；使用真实数据库/兼容 emulator，不以 repository mock 证明事务 |
| End-to-End | 两个独立 Site 的注册、redeem、Chat、Studio、Job、Artifact、Admin、删除导出 | RC；浏览器 + 全服务；跨 Site 越权成功数为 0 |
| Provider Certification | 每个 Model/MCP/Storage/Notification/未来 Payment adapter 的 sandbox account、callback、unknown、限流 | adapter 上线前；未认证 adapter 不可进入 assignment |
| Failure/Chaos | process crash、lease steal、事件重复/乱序/丢失、DB failover、Target 离线、Provider unknown | nightly/RC；无重复 effect/Grant/Credit capture |
| Performance/Soak | §2.4 基线、5 倍 burst、24h SSE/worker soak、queue recovery、成本 envelope | RC；p95/SLO/资源与 backlog gate 全通过 |
| Security/Privacy | SAST/SCA/SBOM/secret/license、DAST、SSRF/path/command、RBAC/Site scope、deletion/retention | 每 PR + RC；Critical/High 未处置为 No-Go |
| Data/DR | migration dry-run、backup restore、PITR、Object restore、reconciliation rebuild、projection rebuild | RC；达到 RPO/RTO，恢复后 invariants 全通过 |
| UX/UAT | error/empty/loading、mobile/browser、a11y、i18n、Support/Admin 操作和真实用户旅程 | RC；P0 journey 无阻断，全球最低 WCAG 2.2 AA；Site 只能收紧 |

测试工程规则：

- Test pyramid 不能退化为“全 mock 单测”或“只跑 happy-path E2E”。交易、Credit、Admission、Job 和删除
  必须同时有 property/integration/chaos 证据。
- 时间、ID、Provider response、callback 和随机故障使用可注入 deterministic fixture；失败时记录 seed、
  contract revision、image digest 和 correlationId，保证可重放。
- Adapter fake 只证明本方状态机；Provider Certification 必须使用真实 sandbox/测试账号。首发无 Payment
  adapter 时不伪造认证结果，而是证明 `redeem_only` 全链和 payment path fail closed。
- Redeem launch 必测：HMAC 查找、枚举限速、并发双兑、事务中途 crash、重复请求、Program expiry、Site/
  user eligibility、fixed-term authority=none、source reversal，以及“Code claim/Grant 要么都成功要么都失败”。
- Release test data 使用独立 Site、账号、Code batch 和 Provider sandbox，绝不复制生产 secrets/PII；生产
  smoke 使用专用 synthetic tenant/Code，并在测试后按 workflow 清理。

### 23.5 Production Certification 与 Release Evidence

每个候选版本生成不可变 `ReleaseEvidenceBundle`，至少引用：

```text
source commit / contract digest / dependency lock digest
EnabledCapabilityInventory digest and per-entry evidence refs
OCI image digests / SBOM / signatures / vulnerability and license reports
migration and rollback-forward rehearsal
unit/property/component/contract/integration/E2E/chaos/load/security/DR reports
SiteRelease compile + preview + a11y + business-flow evidence
known issues / accepted risks / owner / expiry
runbook and alert coverage
backup restore proof / canary plan / rollback decision
```

Bundle 必须绑定 `CertificationInstance` 的 profile、inventory digest、evidence schema version、generatedAt/
validUntil、producer identity/signature 与 supersedes ref。Core certification 通过后 Wave 8/9 仍保持 active；
后续高级 profile 生成 delta instance，所有目标 cut 完成后再生成 transformation-final instance 并退出。

Go/No-Go blockers：

- 任一 P0 journey 不完整，或启用 route/API 仍指向 stub/mock。
- Credit/Payment/Redemption/Grant/Usage/Team budget invariant 失败或无法 reconciliation。
- 跨 Site 越权、secret 泄漏、Critical/High 可利用漏洞、删除/LegalHold 错误。
- migration/restore/rollback 未演练，SLO/load/soak 不通过，关键告警和 runbook 缺失。
- INDEX/CODEBASE_MAP/handbook 与实际 public contract、入口或 owner 不一致。
- 无值班负责人、无回滚权限，或 production batch/credentials 未执行双人核验。

通过后先发布 backend compatible revision，再发布 candidate SiteRelease；使用 synthetic smoke → internal
tenant → 小流量/allowlist → 全量的渐进步骤。任何安全、账务、重复副作用、数据丢失或错误 Site 内容触发
立即停止 promote，并按已演练路径回滚 Release/traffic；已发生不可逆外部事实走 reconciliation，不伪造回滚。

### 23.6 上线后的维护机制

- 每个 SLO 有 owner、dashboard、page/ticket threshold、error budget 和用户影响定义；外部 Provider 与本系统
  可用性分开度量。
- Runbook 至少覆盖：SiteRelease 回滚、Platform/Session/GA/Job 卡死、queue/DLQ、CreditHold aging、
  Redemption 异常、Provider unknown、secret revocation、Target takeover、数据删除失败和跨站安全事件。
- 日常自动检查 backup、certificate/domain、queue age、hold/reconciliation、provider health、storage
  lifecycle、notification DLQ 和 capacity；每周审阅 reconciliation/成本异常，每月审阅依赖与容量。
- PostgreSQL/Mongo/Object restore 至少季度演练，区域 DR 至少半年演练；演练必须从备份真正恢复并运行
  business invariant/E2E，不以“备份任务成功”代替恢复证明。
- Critical exploitable vulnerability 4 小时内完成缓解决策、24 小时内修复或隔离；High 默认 7 天。secret
  泄漏立即 revoke/rotate，并审计受影响 audience、event/log 和 Artifact。
- Contract/schema 采用兼容窗口和 consumer inventory；删除字段、event kind、env 或公开 export 前先证明
  所有消费者迁移。未上线阶段 clean replace，正式上线后遵循 expand/migrate/contract。
- 每次 incident 形成 timeline、root cause、invariant breach、检测缺口、永久修复和回归测试；不把手工数据
  修复当最终方案。Support compensation 只能走正式 Admin workflow。
- 每次 release 同步受影响 INDEX、runbook、ADR/CODEBASE_MAP、API/event docs；季度清理失效说明、owner、
  feature flag、Site assignment 和过期兼容层，防止文档和运行时再次分叉。

## 24. 迁移与清理原则

由于系统未上线，采用 clean replacement，不维护长期 dual-read/dual-write：

1. 先冻结目标契约和数据模型。
2. 建立新 schema、workflow 和 service composition。
3. 使用 fixture/seed 和必要的数据转换脚本验证，不为无生产价值的数据设计复杂迁移。
4. 逐条切换消费方，并通过跨仓 contract/E2E gate。
5. 切换完成后同一波删除旧表、旧 service、旧 env、旧 header、旧注释、旧测试和兼容 adapter。
6. 更新 handbook、ADR、CODEBASE_MAP、运行手册和部署配置，确保只有一个事实源。

Submodule → true Monorepo 采用 pinned snapshot import：

- Wave 0 记录每个 gitlink 的 origin URL、pinned commit、tree hash、license 和验证命令；在一个可 review 的
  cutover series 中移除 gitlink/`.gitmodules`，把确切 pinned tree 作为普通目录纳入根仓，排除嵌套 `.git`。
- 不把四个子仓完整历史强行 merge/filter 进主仓，避免无关历史和 rename 推断污染；旧历史仍由原 remote
  和根仓历史 gitlink commit 可追溯。导入后的第一个根仓 commit 是新权威 lineage 起点。
- 原 remote 在 cutover 后归档/read-only，禁止继续合并或发布；CI、release、issue/PR 入口和开发文档只指向
  根仓。任何必须带入的未提交变更在 import 前先于来源仓形成明确 commit，不复制脏工作树。
- Wave 0 先允许以现有 `kokoro-*` 普通目录接入根 workspace，后续领域 Wave 按 §19 移动到最终
  `apps/services/packages`；每次移动同步 exports、contracts、tests、deploy、INDEX，Wave 8 清零旧路径。

明确删除目标：

- 单 Web app 的 Host 多 Site fallback。
- `KOKORO_SITE_ID` 作为共享 Session 全局常量。
- 可伪造 `x-kokoro-site-id` 作为信任边界。
- Session 内 Hub/Model/Credit 业务决策。
- GA 的 Provider 直连分支和 Artifact store credential。
- `Plan(siteId, price, credits)` 可变混合模型。
- mutable 三桶作为 Credit authority。
- Payment redirect 成功投影和 provider 字符串级去重。
- contentHash 作为 Artifact 身份。
- Persona Switch 冒充 Agent Handoff。
- Admin 业务 DB import 和万能 ResourceTable 覆盖高风险流程。
- 多个 pnpm lockfile 和工具链版本漂移。

## 25. 实施分解与里程碑

本方案不能作为一个超大实现计划一次执行。后续按以下顺序分别完成子 Spec → 用户复审 → 实现计划：

| Wave | 子方案 | 退出条件 |
|---|---|---|
| 0 | Repository/Toolchain/Contract/Documentation Foundation | 单 Monorepo、根 catalog/lock、生成契约、根/受管 INDEX、coverage manifest、CI 边界门成立 |
| 1 | Platform Core、Identity/Auth、SiteContext、SiteRelease 与 Cross-cutting Policy | Auth 产品旅程、RequestSecurityContext、UnitOfWork、ActivationAttempt、RestrictionEpoch 和双 Release drain 闭环 |
| 2A | Commerce Core、Account/Redeem、Subscription、Fulfillment、Credit、Usage | Account/Redeem PRD、单基础订阅规则、复式 Journal、root budget topology、Redeem-only Production Certification 闭环 |
| 2B | Payment Provider Enablement | Checkout/Attempt、webhook reducer、Payment/Refund/Dispute、renewal/dunning 与 provider certification；不阻塞 redeem-only Core Launch |
| 3 | Session Projection、Branch、Admission Boundary | reserved→committed Admission、Session 商业逻辑清零，typed parts/branch/reconnect 闭环 |
| 5A | Model Gateway 与 Capability Runtime Production Spine | Model ownership、AuthorizedModelRoute/ExecutionGrant、AttemptUsageFact、最小真实 adapter 与 Core 所需 GA Model/Capability adapter cutover；不修改 graph/checkpoint/Handoff/effect 语义，触及 GA 前走专项批准 |
| 4 | Operation、Job、Artifact、专业 Studio | 依赖 5A；Direct/Agent Operation、finalization saga、ArtifactVersion 与专业产品 PRD 闭环 |
| 5B | Advanced AgentRevision/Handoff Safety | 经单独用户对齐后处理真实 Handoff、AgentRevision 与高级 epoch/effect safety chaos gate；不承担 Core 必需 adapter |
| 6A | ExecutionTarget、Permission、Interaction | cloud/local/browser/worktree target、sandbox、Takeover 和 scoped approval 闭环 |
| 6B | Developer Workspace、Context、Memory、多端 | Repository/Worktree/Checkpoint/Rewind 与 ProjectContext revision、多端 attach 闭环 |
| 6C | Automation、Connector、Plugin、TaskView | Routine concurrency/Segment、Connection、Hook/Plugin、Notification 状态/源 Release binding 与唯一 TaskAnchor read model 闭环 |
| 6D | AgentTeam、Wide Research、Application Runtime | TaskGraph/root Hold/Slice/聚合与 ApplicationRevision → Rollout → EnvironmentDeployment 长期服务闭环 |
| 7 | Site Fleet、标准 Admin 与业务治理 | 发布、财务、模型、运行恢复、Growth assignment/exposure analytics、Risk Case/Appeal、全 participant Export/Deletion/Retention/LegalHold epoch 专用流程全部可审计 |
| 8 | Clean Cutover 与 Handbook 收口 | 旧代码/表/env/header/compat/INDEX 清零，CODEBASE_MAP/ADR/runbook 单事实源，全仓 E2E 通过 |
| 9 | Production Certification 与 Launch | redeem_only 真实纵切、RC EvidenceBundle、security/load/soak/DR/rollback、on-call/Support 和 Go/No-Go 全通过 |

Wave 3 与 Wave 2A 的只读契约设计可以并行；Wave 5A 依赖 Wave 1 的安全上下文和 Wave 2A 的 Usage
contract。Wave 4 依赖 Wave 2A、Wave 3 与 Wave 5A，禁止用旧 GA Provider 或 fake adapter 冒充生产链。
Wave 5B 可与 Wave 4 非 GA 文件树并行，但任何 GA graph/checkpoint/control/effect/Handoff 行为变更必须先与
用户单独对齐。Wave 6A 依赖 Wave 4/5B；6B 可在 6A Target contract 冻结后并行；
6C 依赖 Admission、Capability 和 Wave 3 的 Task Projection 基础 contract；6D 依赖 6A/6B 的隔离和
6C 的长期运行/通知。Risk enforcement contract 必须在 Wave 1 冻结，并随每个执行 Wave 接入；不能等到
Wave 7 Admin 才补。Data Governance participant contract 在 Wave 1 冻结，各 context 在自身 Wave 实现，
Wave 7 只完成跨 context coordinator 和运营面。Wave 8 不接受“旧代码暂留后续删除”；Wave 9 只认证
已经 clean cutover 的唯一实现，不在 RC 阶段补领域功能。

## 26. 依赖与风险

| 风险 | 可能性 | 影响 | 缓解 |
|---|---|---|---|
| Umbrella 方案范围过大 | 高 | 高 | 强制拆 Wave 子 Spec，不允许一个计划覆盖全系统 |
| 重构期间出现新旧双事实源 | 高 | 高 | 每个 Wave 定义明确切换点和同波删除清单 |
| Platform 模块化退化成大泥球 | 中 | 高 | dependency rules、workflow ownership、禁止跨模块表访问 |
| SiteRelease 与 Web deployment 混版 | 中 | 高 | releaseId、compatibility gate、drain window、签名 manifest |
| Credit/Payment 极端状态遗漏 | 中 | 高 | property test、事实 timeline、reconciliation 和财务红队 |
| Job/GA 副作用重复 | 中 | 高 | epoch fencing、effect claim CAS、unknown outcome、不盲重试 |
| MCP/Provider secret 泄漏 | 中 | 高 | Secret Manager、scoped token、契约负向测试、日志扫描 |
| 专业 Studio 被万能配置限制 | 中 | 中 | 共享生命周期，不共享专业编辑器；分别验收专业 UX |
| PostgreSQL 切换分散注意力 | 中 | 中 | 先 Platform/Session 新 schema；GA Mongo 保留，不机械迁移 |
| Admin 再次退化为 CRUD 表格 | 中 | 高 | 高风险领域必须专用 workflow 和 maker-checker 验收 |
| ExecutionTarget 扩成万能远控服务 | 中 | 高 | target capability contract、最小 binding/lease、按 kind 独立 adapter 和强制 sandbox |
| 本地设备/浏览器扩大安全面 | 高 | 高 | Device Gateway、workspace trust、scoped grant、Takeover、managed deny、零凭据上云 |
| Schedule 绕过正常业务链 | 中 | 高 | 每次 RoutineRun 强制 Admission；Scheduler 无 GA/余额直写权限 |
| ProjectContext/Memory 污染权限 | 中 | 高 | Memory 只作上下文；权限与 policy 独立、结构化、managed precedence |
| Agent Team 无限并发和费用失控 | 中 | 高 | PlanProposal、root Hold、ChildBudgetSlice 守恒、并发上限和统一 cancel |
| Plugin/Hook 供应链风险 | 中 | 高 | 签名、permission manifest、审核、版本锁、撤销、sandbox、兼容 gate |
| TaskView 变成第二业务真源 | 中 | 高 | read-only projection、写命令回源、rebuild test、禁止 Task 表承载领域状态 |
| Risk 到后期才接入导致前序契约返工 | 中 | 高 | Wave 1 冻结 RestrictionEpoch/PolicyDecisionToken；每个 effect boundary 同波验收 |
| 删除工作流只删入口、遗漏跨域数据 | 中 | 高 | Data Governance coordinator、participant API、LegalHold、tombstone、可验证 receipt |
| 实验导致同一用户旅程配置漂移 | 中 | 中 | Revision、稳定 assignment、真实 exposure、Quote/Admission snapshot 和 guardrail |

## 27. 已裁决事项

产品方向性决策已经批准，但本文仍等待用户完成书面 Spec 复审；在复审前不得进入 Wave 实现计划。
以下架构方向已经裁决：

- Platform 采用模块化 Core，不采用 Platform 微服务优先。
- 一 Site 一独立 Web Project，但同一 Monorepo。
- 不同 Site 默认账户和权益完全独立；未来互通走标准 OAuth/OIDC，本地 User 仍独立。
- GA 保留成熟底座，商业、Provider、Job、Artifact 后端能力移出。
- Job 独立于 Run；仅符合异步恢复条件的工作创建 Job。
- Direct Studio 与 Agent Tool 共享 Operation/Job/ArtifactVersion。
- 三桶保留为 UX 投影，Grant/Journal/HoldAllocation 成为 Credit authority。
- ModelCatalog 全局唯一，产品通过 Profile/Pool/Assignment 组合。
- Admin 不直连业务 DB，高风险领域使用专用工作流。
- 目标 Platform/Session/Job 使用 PostgreSQL；GA checkpoint 本轮保留 MongoDB。
- 初期异步传输保留 Redis Streams，但数据库 Outbox/Inbox 是 durable authority。
- ExecutionTarget 统一 cloud ephemeral/persistent 与 local device/browser；离线不隐式换环境。
- Worktree 是 Developer Workspace 隔离资源，不是 ExecutionTarget kind；它绑定到支持 filesystem 的
  cloud/local Target。
- TaskView 是 Session/Run/Job/Artifact/Team 的只读聚合，不新增万能 Task aggregate。
- Routine/Schedule 是长期触发定义，Job 是单次执行实例；每次触发仍走 Platform Admission。
- PermissionPolicy 与 OS/container/browser sandbox 双层强制，managed deny 不可被用户 allow 覆盖。
- ProjectContextRevision/Memory 有 scope、revision 和 provenance，但永远不是权限真源。
- Handoff、Subagent、ChildRun、AgentTeamRun 四种协作语义保持独立。
- Experiment/Growth 有版本化 assignment/exposure，但永远不能绕过 Release、Commerce、Admission 和 Risk。
- Risk enforcement 是所有执行边界的早期横切契约；Data Governance 用跨 context participant workflow，
  Notification 由领域事实驱动且不改变源业务终态。
- 首发可以不接真实 Payment Provider，Site 通过 SalesPolicyRevision 使用 `redeem_only`；Redemption 与购买
  复用同一 Fulfillment/Grant，绝不创建假 Payment 或第二套 Credit 路径。
- “完成”以 Production Certification 为准：启用功能无 stub/mock、恢复/安全/运维证据齐全，Wave 9
  Go/No-Go 通过后才可宣告直接上线。
- INDEX.md 是贴近代码的当前架构契约；Wave 0 建治理和 CI，每个 Wave 同 commit 更新，clean cutover 删除
  旧描述，不以历史兼容说明污染新实现。
- Claude Code 类 Developer Surface 与 Manus 类 Task Surface 共用底层执行体系，不拆两套 GA/Job。

具体 Site 套餐价格、开放的 Surface、模型池内容、Provider 和 Merchant 配置属于运营数据，不是架构
开放问题。各 Wave 的完整状态转移、字段约束、API schema 和 migration/cutover checklist 必须在对应
子 Spec 冻结并通过用户复审，不能由实现者临场决定。

## 28. 相关材料

- `docs/superpowers/specs/2026-07-25-product-requirements-governance-and-prd-registry-design.md`
- `docs/reports/2026-07-25-kokoro-module-capability-coverage-audit.md`
- `docs/handoffs/2026-07-24-credit-three-bucket-l3.1.md`
- `docs/reports/2026-07-25-kokoro-production-launch-readiness-checklist.md`
- `docs/superpowers/plans/2026-07-25-kokoro-production-delivery-program.md`
- `docs/superpowers/specs/2026-07-24-capability-and-studio-architecture.md`
- `docs/superpowers/specs/2026-07-24-unified-plan-monetization-design.md`
- `docs/kokoro-handbook/technical/20-kokoro-v1-technical-plan.md`
- `docs/kokoro-handbook/technical/21-platform-mainchain-closure.md`
- `docs/kokoro-handbook/technical/22-capability-hub.md`
- `docs/kokoro-handbook/technical/23-platform-ops-console.md`

这些材料用于说明当前实现和历史决策；与本文目标冲突的内容将在 Wave 0/8 的文档治理中明确替换，
不得继续作为新实现依据。

## 29. 修订记录

| 版本 | 日期 | 变更 |
|---|---|---|
| 1.0 | 2026-07-25 | 汇总多轮讨论、三路独立源码审查和用户批准的目标架构方向；等待书面 Spec 复审 |
| 1.1 | 2026-07-25 | 关闭 Commerce 红队 P0：Platform process role/UoW、Hold finalize、Operation admission、Release/交易状态与复审门 |
| 1.2 | 2026-07-25 | 补齐顶级 Agent 产品能力与业务能力地图；经 Runtime/Commerce 红队关闭 ExecutionGrant、Target fencing、AuthorizationSegment、Team budget、Growth/Risk/Governance/Notification 等边界问题 |
| 1.3 | 2026-07-25 | 冻结 production-ready、redeem_only source/term/availability/export/reversal 正式首发链、分层验证/RC Evidence/Go-No-Go/维护机制、INDEX.md/Monorepo 治理与 Wave 9 上线门 |
| 1.4 | 2026-07-25 | 经产品、Commerce、Agent/Model/LiteLLM、架构与可靠性多路红队：冻结 Core/Advanced launch profile、Identity/Account/Chat/Studio/Support PRD、Run/Usage/Model 唯一 owner、root budget topology、Job finalization、RequestSecurityContext、ActivationAttempt、RPC/deployable matrix，并调整 2A/2B、5A→4→5B 与 6A-6D 分波 |
| 1.5 | 2026-07-25 | 经产品旅程覆盖红队补齐：具体 `core-redeem-chat` Reference Profile、Canonical Journey/State/Recovery/Metric/Operator/Content Policy 治理、Mandatory Product PRD Registry、Workspace/Site lifecycle、WCAG 2.2 AA 全局下限与全模块追踪审计 |
