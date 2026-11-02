# Task A 当前进度、问题与 C-1～C-4 闭环技术方案

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 先完成 G0 / C-1～C-4 的认证切换、旧实现删除和真实验证，再进入 A-01/A-02，随后 A-07；保留 A-03～A-16 的完整产品责任，不以清理完成代替 Task A 产品闭环。

**Architecture:** IAM 唯一拥有人类 session、active tenant 与权限；App 同源适配 → BFF Nest feature → owner API/RPC。Nest `AppModule` 是唯一运行时组合根；旧 raw server/runtime、dispatcher 和无边界 aggregate 在消费者迁移后删除。有效的事务、幂等、取消、恢复、lease/outbox 语义必须承接，不机械删除 Repository 或新增空层。

**Tech Stack:** 现有 TypeScript/NestJS/pnpm、PostgreSQL/Redis、owner generated clients、Python Root 治理；各仓 Node/Python/Go 版本以其 manifest/lockfile 为准。

**当前检查点：** G0已通过。App e1be73e0已独审、Root完整门6407pass/0skip，真实冷登录和App退出HTTP/旧cookie拒绝通过；完整四旅程仍待。Capability f515已Root完整门3051pass/678skip及真实PG接收方验证，Root配套退休配置已提交。PR13与最新PR12基线有冲突及publication接缝待T-09；G1/G2/G3保持OPEN，不进入A功能。

---

## 当前执行摘要（2026-11-02 再对齐）

- **暂停与当前交接分开记**：此前会话记录出现`User set goal status: "paused"`及中断事件；本记录不据此推断谁操作或客户端原因。2026-11-02主窗口重新调用`get_goal`确认**active**。当前IAM worker已交付tests-only候选，等待Root运行真实RED；不是正在执行长测，也不是已经验证失败。此处是主控待接收的执行步骤，不需要用户再次批准既定方案。
- **Goal边界**：机器Goal仍是C-1.3～C-4前置闭环，不是“A全部完成”。阶段G0通过，G1认证/G2删除/G3最终组合验收均OPEN；完成当前Goal后才进入原A-01～A-16产品验收。复用原Goal，不另建重叠目标。
- **当前完成量不按百分比表述**：18条TODO中11条仅为已验切片/前置；T-05/T-17进行中、T-16开放，T-14接收方切片已验但最新基线整合仍待T-09，T-09/T-11/T-15等待依赖，T-10门控。不同条目的规模不等，切片数量不等于Task A完成比例。
- **已解决的前置阻断**：原BFF静态门未覆盖DI装配；4d6d17b补真实容器回归并修五处owner模块可见性，Root535e7071 minimal native4pass/cleanup PASS。当前下一步是T-05永久四旅程；T-14接收方已验，最新base整合归T-09，不重复处理旧启动失败；完整生命周期仍未验。
- **闭环判定**：当前没有完整浏览器固定域登录/异域会话拒绝与恢复/登出/撤权收据，没有完成raw/聚合删除，也没有交付可保留同步测试环境。PR存在、单测通过和失败后资源回收均不等于这些完成。
- **工期口径**：此前3～7个工作日只是C-1.3～C-4的低置信度工作量预算，不是Task A全部交付日期，也不因每次续接自动重置倒计时。原0.5～1日启动修复预算对应的最小启动项已完成；冷登录/退出HTTP与T-14接收方现已验收，但永久四旅程、生命周期、raw迁移及新base整合仍开放。3～7日仅保留为历史暂定预算，**不是从今日起的剩余工期或承诺日期**；待四旅程结果与迁移规模复核后重估。前提是持续投入、没有新增owner契约/数据迁移或重大回归。A-01～A-16只有功能责任清单，尚无逐项剩余量和估时，现无可信完整Task A日期；下一估算动作是只读核A项剩余切片/依赖，不提前实施A代码。

## 0. 当前结论与唯一入口

**Task A 尚未闭环，C-1.3 / C-2 / C-3 / C-4 均未达到最终完成条件。** G0已有审阅通过证据。本轮起点Root HEAD为`4f7514b2`，与已验源码组合`1e6c3a22`的子仓pins一致；App e1be/BFF4d6/IAMe6/Capabilityf515的证据范围见下表。IAM新host已双审、Root两host66pass/0skip与完整verify1566pass，已提交推送1ee8d156（原draft PR6）；永久driver已双审与Root82定向/1931治理通过；本次接收精确pin后实跑，真实四旅程仍待。没有可交给用户常驻同步测试的完整应用组合与四旅程收据。

本文件是当前问题、分阶段 Goal 和 TODO 的**唯一可变台账**。`docs/task.md`、`docs/CURRENT.md` 只保留摘要与链接；旧方案/问题台账保留设计和历史证据，不再维护第二份当前状态。

规范来源：
- [原 Task A 完整任务表](../../handoffs/2026-10-30-task-a-workspace-execution.md)；[原清理执行顺序](2026-10-30-task-a-cleanup-refactor-execution.md)。
- [清理设计](../specs/2026-10-30-task-a-cleanup-refactor-design.md)、[逐项 disposition 与测试矩阵](../specs/2026-10-30-task-a-cleanup-inventory.md)。
- [ADR-036：Nest 收敛](../../kokoro-handbook/decisions/ADR-036-bff-nestjs-convergence.md)、[ADR-035：内部 direct credential](../../kokoro-handbook/decisions/ADR-035-direct-internal-service-authentication.md)。
- [当前实施证据](../evidence/2026-10-31-task-a-c1-cleanup-implementation.md)、[历史 native 收据](../evidence/2026-10-31-task-a-c1-3-native-receipt.md)、[历史问题台账](../evidence/2026-10-31-task-a-issue-register.md)。

### 0.1 当前组合与未提交范围

执行目录：`/Users/nako/.codex/worktrees/task-a-c1-cleanup/Kokoro`；Root 分支 `codex/task-a-c1-cleanup`。不要把原 checkout 的 `main` 当成本轮执行树，也不要把 HEAD 当作包含未提交候选。

| 仓 / 范围 | 已提交基线 | 当前候选与证据层级 |
| --- | --- | --- |
| Root | `1e6c3a22dbb046531143ec67de5d1c6a6dc27e5b`（已验源码组合） | App e1be/BFF4d6/IAMe6/Capabilityf515精确pin；前三owner实际native/冷登录/退出HTTP和cleanup通过，Capability接收方独立真PG通过；不是全owner同起或完整四旅程 |
| App | `e1be73e08bb1bd4c9c554c9e319f6b079006fdb5` | PR50；Root完整check452/50/6407、lint/types/build通过；真实冷登录303/authenticated=true、退出200后匿名/cookie0、项目401/旧cookie401。Settings实际点击、异域恢复与独立撤权仍待 |
| BFF | `4d6d17b651a8d0e472dbabe67872c856185ae61b` | 五DI修复+真实容器回归；Root完整门contract1344/default2344pass+2skip/build；PR18已推送/Root535e7071已pin，minimal native4pass/cleanup PASS，完整四旅程待验 |
| IAM | `1ee8d156252cc1c19ba6951546552e9b01123979` | 原draft PR6新增test-only exact browser session协议；双审、Root两host66pass/0skip与verify121files/1566pass/build通过，536输入hash不变；本次Root接收精确pin，不等于跨仓UI验收 |
| Agent | `c761fad3dba2b56cd7fe4da7683a9ac2f208243f` | C-1.2 清理已提交；最终完整 owner gate 仍待 |
| Capability（物理路径仍为 kokoro-capability） | `f515e22596357e2dd6c05cfa47a1c2f54b99f202` | receiver-only源码及真实PG已验，独立draft PR13依赖PR12；远端基线2ad5c9e未集成且PR冲突，保留原已验组合不覆盖新增提交，最终合并门OPEN |
| 其他组合成员 | 当前 Root gitlinks | 仅按受影响边界纳入验证；本轮未启动、未刷新全套运行健康状态 |

### 0.2 进度与验证事实

| 阶段 | 已有成果 | 当前结论 / 缺口 |
| --- | --- | --- |
| G0 | ADR-036 Accepted；2026-10-31 reviewer 放行；native artifact 1.0.0 / SHA256 `5cf59df4b7bd9853edfd2eabb31afc236c0ec0db371f9737706fc129484fd83f` 已固定 | 设计门已通过；新的具体写区仍须按本文局部设计确认，不把设计批准当运行验收 |
| C-1.1 / C-1.2 | BFF schema-evolution 旧入口、App hash/legacy 展示分支、Agent legacy_failed 推断等已删除；保留 canonical localDraft / journal / replay | 已提交切片；最终零消费者复核及 App/BFF/Agent 完整门待 C-4 |
| C-1.3 | native准入、冷登录及退出HTTP已真实验证；Capability direct receiver与退休配置已交付 | 固定域异tenant拒绝/恢复、独立session/membership撤权及UI/迟到响应未齐；新base集成仍开放 |
| C-2 | Nest 生产图已移除 LegacyRoutes；named feature 路由接管；generic configured-owner proxy tail 已删除 | raw server/runtime 与测试消费者仍存；生产 Nest shutdown 语义待核；入口隔离候选不等于删除完成 |
| C-3 | BffBusinessStore / BffApplicationServices / PostgresBffRepositories 旧 aggregate 已清理多片；global ports 仅留 idempotency contract | raw composition / owner-resource 聚合工厂和 feature disposition 仍待最终审计，不以类名删除代替边界证明 |
| C-4 | App e1be/BFF4d6/IAMe6/Capabilityf515各有对应工程门；Root治理/真实限定链路有证据 | Agent全门、最新base整合、全受影响真实I/O及最终组合E2E/常驻同步环境未齐；678skip不算通过 |

证据严格分层：
- **已提交旧基线**：BFF `228e3d6` 默认测试 2298 total / 2296 pass / 2 skip / 0 fail；该时默认入口未纳入两套 Nest 架构测试。IAM `a1457be` verify 为 120 files / 1561 pass / build PASS。Root 上次 topology PASS，治理 1846 pass / 3 skip / 502 subtests。这些不是当前 dirty tree 全绿证明。
- **App 历史T-07基线9ba，Root复验结果（当前e1be见§0.1）**：Node 22.23.4；contract 48 files / 452 pass、architecture 50 pass、完整 test 354 files / 6373 pass / 0 skip；typecheck/lint/build/diff-check 通过。旧基线50个契约失败已收敛，Root完整check exit0且56路径前后SHA一致；已提交4260f698、集成origin/main空树merge为9ba65343并推送App draft PR #50。Root已pin；真实四旅程仍待。
- **BFF 历史173e026切片，Root复验结果（当前4d6见§0.1）**：Node24.20.0下format/check exit0；contract1344pass，默认2343pass/0fail/2skip，lint/types/build通过。两项原数据库条件skip另补整文件真实PG schema15pass/0skip，覆盖共存/回滚与R237。原architecture73/focused123为辅助证据；未完成完整业务integration/当前native链路，字面依赖扫描不称完整AST图。
- **Root runner历史→当前**：最初close函数缺失1pass/2fail，后续独审发现五项清理/收据缺陷，均已在T-13修复并以Root60定向/IAM真实62及成功/失败退出验证。现Root六文件T-14配套候选另有154定向、完整治理1879pass/3skip/506subtests；真实Capability receiver现已验（f515，见§0.1）；完整四浏览器旅程仍未验。
- **历史真实链路**：旧组合有 IAM 集成 12 pass、IAM→BFF 7 case、HTTPS native smoke 4 case。保留其对应 SHA/范围；不外推到当前 Nest/候选组合，也不将历史 OIDC 验证作为目标 native 链路。

---

## 1. 已知问题全量表（本次 Task A 审计范围）

这里只把本次可核验的问题标为当前事实；历史或任务外问题保留归属，未核验不等于无问题。

| ID | 问题 / 当前证据 | 处理与关闭条件 | TODO |
| --- | --- | --- | --- |
| I-01 | 原精确源码/dirty/gitlink阻断已解决：Root1e6精确App e1be/BFF4d6/IAMe6，Capability f515另已pin | 已验组合source门保持；后续IAM fixture或base整合新候选必须重新停写/提交/精确pin，不绕过门禁 | T-04/T-13/T-05/T-09 |
| I-02 | MCP denied icon mutation 曾在拒绝后调用 Platform | `228e3d6` 已补 manage admission，focused42与基线 full已证；最终组合继续保护零副作用 | T-02（已验证切片） |
| I-03 | Skill installation Chat invalid-owner error 曾被 fixture 缺失掩盖 | `228e3d6` 补最小 receipt seam，focused24与基线 full已证；保持 typed error，不放宽断言 | T-03（已验证切片） |
| I-04 | BFF原32文件格式warnings已机械修复；Root完整格式门通过 | 重跑确切清单，仅处理本任务受影响文件；不做无关全仓格式化；门未绿前 C-4 保持 OPEN | T-06 |
| I-05 | App Public28.18 pin/generator/历史逆证已正规修复并经Root完整门，已提交独立draft PR | 候选已修，原件/旧父链独审通过；Root 复验并集成后关闭，不手改快照或历史 hash | T-07 |
| I-06 | IAM SDK drift | `a1457be` 已正规生成并 verify；更改消费者后仍核 fixed artifact，不引入手写第二契约 | T-08（已验证切片） |
| I-07 | 全部 owner 的受影响全门、真实 I/O、当前 E2E 收据未齐 | 按停写组合串行验收，逐项记录 fail/skip；不把 health/static/fixture 当产品闭环 | T-09/T-15/T-16 |
| I-08 | A 任务产品缺口尚在，容易被清理完成误标关闭 | A-01/A-02/A-07 保持门控；A-03～A-16 保留完整 backlog；不新增本轮产品代码 | T-10 |
| I-09 | raw server/runtime、composition 与聚合 fixture 仍在 | 56 test files / 148 direct calls；helper18 files / 42 calls；composition3 files / 4 calls；owner-resource9 suites / 102 calls，集合有重叠不可相加。按 feature 迁移，再零消费者删除 | T-11 |
| I-10 | 默认 test/check 曾遗漏 Nest 架构门 | 候选已在 test 与 test:architecture 各接两套 Nest suites 一次；主方复验默认入口；静态扫描不冒充完整依赖图 | T-12 |
| I-11 | smoke teardown 吞 process/proxy 异常，缺 IAM 前后 inventory；失败日志在临时目录退出时消失 | 所有自有资源尽力回收、失败可见、未停进程不删依赖；增加脱敏 stage/cleanup 收据和泄漏负控；红测保留至真实修复 | T-13 |
| I-12 | Capability `global_register` 仍用 IAM workload introspection，最新 TODO 曾遗漏 | policy 声明 caller 为 kokoro-system，但 System 当前源码未定位实际 producer；先核消费事实，再复用 direct credential verifier。无需求不新增 System 注册功能 | T-14 |
| I-13 | Nest 生产只 enableShutdownHooks；旧 installBffSignalHandlers 仅被测试消费，数据库 close 尚无明确 Nest hook 接线 | 验证并补齐 readiness关闭→worker drain/取消→连接释放的有界生命周期；实际 Nest app.close/SIGTERM 与真实 PG/Redis 证明后才删 raw shutdown | T-17 |
| I-14 | 新旧计划/问题台账/日期混用，App旧失败、G0待批准、资源缺失等曾覆盖当前态 | 本计划唯一当前台账；旧文件加历史/导航标记；候选/已提交/Root复验分列，状态变化再同步摘要 | T-01 |
| I-15 | 单数据库 owner schema 组合、Redis namespace、自有 fixture 回收尚无当前共同证据 | fixture 临时库只是隔离，不证明应用单库组合；逐 owner 核 installer/URL/schema，禁止跨 owner SQL/共享 reset | T-04/T-09/T-15 |
| I-16 | Agent 最终全门及全局规范审计未刷新；旧问题台账记录过224条任务外 violation | 本轮不把历史计数当当前结果；C-4核受影响项，任务外问题保留 owner/backlog，不放宽适用门禁或宣称全仓无问题 | T-09/T-16 |
| I-17 | 原runner遗漏必需的Web Redis输入已修复并提交，实际无cookie注入冷登录已通过 | 此配置不是退休项；隔离注入/归属/回收与冷登录证据已验。后续永久四旅程保留该回归，不以默认preview替代 | T-04/T-13/T-05 |
| I-18 | 原BFF engines与pin/生成链/CI/Docker存在Node24/22漂移；173e026已统一并通过Root当前完整静态门 | 保留两轮RED与真实修复证据；七条正规生成/双检及当前完整门通过，106generated不变；未实跑CI/Docker，不以配置对齐冒称容器验收 | T-18 |
| I-19 | 原Nest启动失败已解决：BFF4d6修复五处DI可见性，Root535最小native成功；完整关闭矩阵仍缺证 | 已加真实生产容器compile/关键token单实例回归；后续验证drain/SSE/worker/PG/Redis，不重复领取旧启动修复 | T-17 |
| I-20 | 本计划曾要求同App正向双tenant切换，但App/BFF/IAM当前三面设计与G0都明确固定Product tenant；属于台账错误 | 已按有效裁决纠正T-05；用异tenant会话拒绝/固定域恢复验证隔离，禁止删BFF授权门或新增TaskB切换器 | T-01/T-05 |
| I-21 | 真实Chromium冷登录RED：表单303后session/projects401；App缺固定tenant set-active，fixture预设会话曾掩盖 | 五文件727已获独审与Root完整门（6401pass）；Root4fdb实际冷登录GREEN，I-21缺陷闭合，仍不等于四旅程全部完成 | T-05 |
| I-22 | LocalPlatformRuntime先生成单projection文件，随后聚合多surface凭据以同名O_EXCL创建，真实文件装配抛FileExistsError | Root候选已改独立聚合文件名，真实临时目录RED→GREEN并保持0600/回收；独审及Root154定向通过，已随c08c提交并配对f515；此文件装配缺陷闭合，同步环境仍待T-15 | T-14/T-15 |
| I-23 | Capability现部分R317/R336 opt-in测试与release workflow仍有此前OAuth/旧execution配置欠账 | 保留原触发开关与业务断言，标清既存/本片新增；本片只迁退休resource-server消费者并真实验证global receiver，未触及的旧catalog/CI链不冒称已可运行 | T-14/T-16 |
| I-24 | 已修复退出两层缺陷：显式POST body与owner JSON媒体类型/空对象规范化 | App e1be完整门6407/0skip及Root真实退出200、cookie清除、项目/旧cookie均401；I-24在此HTTP范围闭合，完整T-05仍OPEN | T-05 |
| I-25 | Capability原PR12基线由44fcc前进至2ad5c9e，4提交/73路径含契约和Schema；本Task A PR13与其存在实际合并冲突 | 保留双方提交，不force、不整树择一；在独立集成区审边界/冲突后重新完整门和真实receiver，再更新精确Root组合。当前仅已验f515候选 | T-09/T-16 |

---

## 2. Goal 与原 Task A 对齐

### 2.1 机器 Goal 与阶段目标

本轮主窗口 `get_goal` 核验：既有 Goal 为 **active**，目标是“完成 Task A 的 C-1.3～C-4 闭环，先冻结问题/目标/约束/TODO，完成 native-session 与旧实现清理和串行全量验证，A-01/A-02/A-07 保持停写”。复用这一 Goal，不创建重叠 Goal，不提前 complete。

| 阶段目标 | 状态 | 可核验的完成条件 |
| --- | --- | --- |
| G0 设计门 | 已通过 | 有效 ADR / owner artifact / disposition / reviewer 证据存在；当前目标不漂移 |
| G-DOC 当前方案与追踪 | VERIFIED（文档基线） | 初始17问题/17TODO及A-01～A-16已独审；执行中新发现T-18同步登记，状态持续更新；不算产品完成 |
| G1 C-1.3 认证切换 | OPEN | 当前 App→BFF→IAM 四旅程与负控；Capability遗留认证处置；旧入口零生产消费者 |
| G2 C-2/C-3 清理 | OPEN | 迁移有效测试风险，Nest生命周期承接，raw/dispatcher/无边界aggregate零消费者并删除；保留层有职责理由 |
| G3 C-4 与同步端到端 | OPEN | 主方在冻结组合完成 owner全门/真实I/O/Root治理/健康与浏览器旅程收据；skip不计成功 |
| G-A 产品后续 | GATED | 先完成G1～G3，再A-01/A-02、后A-07；其他A任务按原优先级领取，不从本清理Goal中消失 |

### 2.2 A-01～A-16，不缩小原任务

| 原任务 | 功能 | 本轮定位 / 后继验收 |
| --- | --- | --- |
| A-01 | 会话创建与恢复 | GATED；先 localDraft→owner create/retry→URL/刷新/前后退/多标签/迟到响应 |
| A-02 | Agent过程与详情展示 | GATED；唯一AG-UI/RunDisplay，live/终态/历史一致，真实详情不补造 |
| A-03 | 输入框与运行控制 | 后续backlog；IME、队列、审批、停止/继续、重连与一次意图一次执行 |
| A-04 | 执行正确性与恢复 | 后续backlog；worker/lease/checkpoint/journal/outbox恢复不重复副作用 |
| A-05 | 长上下文压缩 | 后续backlog；当前长会话/工具/取消/恢复，私有capsule不进入公开面 |
| A-06 | 项目概览与上下文 | 后续backlog；指令/pin/资源/Skill引用、菜单、删除释放与回读 |
| A-07 | Project Todo | GATED，A-01/A-02之后；BFF项目任务CRUD/权限/CAS/幂等→generated client→App，不把Run Todo改名 |
| A-08 | 附件与上下文引用 | 后续backlog；选择→发送→Run资格→真实内容→刷新恢复 |
| A-09 | 资料库 | 后续backlog；上传/扫描/分页/下载/删除/来源回跳 |
| A-10 | 文件/产物/Canvas | 后续backlog；正确Run/版本/权限、完整内容、窄屏与键盘 |
| A-11 | 首页与创建场景 | 后续backlog；只交付真实支持入口，Manus同状态对照 |
| A-12 | 自动化 | 后续backlog，先核原writer；CRUD/时区/DST/到点执行/重投结果闭环 |
| A-13 | Agent与外部聊天应用 | 后续backlog；已有能力真实owner/callback/过期状态，不增加未裁决能力 |
| A-14 | 语音输入 | 后续backlog；真实麦克风/转写/拒绝/取消，不用演示文本 |
| A-15 | 体验与性能 | 随产品切片验收；响应式/回焦/真实延迟，不藏加载或伪造成功 |
| A-16 | 文档、PR、合并与运行配对 | 随片交付；Root/App/BFF/IAM/Capability各自draft PR，Root已精确pin当前子仓；限定真实链路已验，完整产品验收/运行配对仍待；未merge或上线 |

Task B 继续拥有能力配置/授权/安装、账户协作等业务；Task A 使用其固定契约与真实资格。`global_register` 属原 C-1.3 已批准清理依赖，不借此接管整个 Task B。

---

## 3. 技术方案与逻辑闭环

### 3.1 C-1.3：人类身份链与机器身份分别闭环

```text
Browser → App same-origin adapter → BFF native admission → IAM fresh session/tenant/membership
                                  → named feature → owner API/RPC → owner facts
                                  ← canonical result / receipt ←
Browser ← App UI 与刷新后的同一事实
```

- IAM拥有cookie/session/active tenant/revocation；App只转发allowlist cookie、Origin、request-id与取消；BFF冻结可信身份，body自报身份不参与授权。原生认证协议不强套业务API命名。
- 四旅程按既有固定Product tenant裁决验收：真实冷登录→固定域session/业务读取；由IAM合法测试通道使会话进入异tenant→当前App/BFF立即拒绝且不读写外域，返回固定tenant后恢复；App登出→旧cookie失效；独立撤销session/membership→已开页面下一次请求拒绝。跨标签迟到响应不串身份。不是同App跨tenant正向产品切换，不新建已删除的Team selector。
- T-05测试协议纠偏（2026-11-02真实RED＋owner源码/数据设计确认）：原生退出将Session到期并撤销派生凭据，保留expired tombstone；不能以物理row消失作为退出条件。私有inspect保留exists=物理row，并加unexpired=该exact row的expiresAt>now；退出应为exists=true/unexpired=false及原生get-session null、BFF旧cookie401。独立fixture exact-session删除为exists=false/unexpired=false；仅撤fixed membership时B session仍exists/unexpired=true、member=false且业务拒绝。owner active_tenant按物理row记录，不因到期伪改none。此变更限测试协议与oracle，不修改生产撤销语义。
- App当前native投影没有tenant标记；同subject切tenant后的页面与在途请求退休是待验证风险，不据源码直接认定正确或新增一套身份协议。IAM `verify`不含真实integration；App默认Playwright开启session preview，另设真实配置旅程后才能引用为认证证据。
- 负控：匿名、错Origin、伪造tenant/subject、失效/错surface服务身份、重复登出、撤权后旧请求、IAM不可用；拒绝时零越权owner写入，未知结果不补成功。
- 当前 `run_web_native_session_smoke.py` **只是三服务最小HTTP smoke**：fixture给现成native cookie→`/api/auth/session`→`/api/session/projects`→fixture直接IAM signout后401，加日志检查共4case。不是浏览器登录，不覆盖tenant切换、App登出、独立revocation或全部owner。
- `global_register`：先核真实producer与接收方写区。Capability复用既有direct service credential校验与无tenant/caller/surface规则，承接注册授权/幂等/取消，再删除该surface的OAuth分支及专用消费配置；第三方MCP OAuth、IAM公共OAuth与Billing资金授权保持。调用方待证不新增无需求服务。
- T-14盘点补充：Capability当前RPC接收方真实可写，但冻结v9 manifest仍inactive/routable=false，注册profile身份段还是operator_machine。认证切换需owner单一当前auth profile明确替代旧身份语义并校验provenance，不修改冻结v9或借机激活它；三面设计已审；实现已以f515提交并完成Root完整门及真实接收方验证，派生auth-source索引/原policy与schema单一事实源已纳入；最新base整合仍须重新验证。System当前src/scripts/contract未见producer，仅receiver与测试client存在，证据称接收方切换，不称System业务链完成。
- T-14局部取消风险：已提交44fcc5d的register handler/service未传caller boundary，PrismaMcpTransaction.runGlobal使用无caller取消的transaction request。现冻结候选已传递既有boundary，并补授权后/provider等待中取消→零入库的回归并承接现有boundary；其余MCP业务不顺手重写。direct credential没有TTL字段，不凭空增加过期机制；测试覆盖旧OAuth拒绝与文件删除/轮换即时失效。
- 本片不新增数据模型、第二认证协议、token镜像或Root可编辑contract；需要变更wire/schema时先由owner补相应设计面和机器契约，再串行交给消费者。

### 3.2 C-2：从入口隔离走到真正删除

1. 已提交173e026承接原11文件候选，Root已确认该子集只去掉`main.ts` raw re-export/两处type倒依赖、迁6个测试import并补默认门；不把它写成最终删除。
2. 先核Nest生命周期：`src/main.ts`、`src/common/database/database.module.ts`及现Redis/worker provider。用真实`TestingModule`/应用关闭验证停止接收、worker drain、SSE取消、超时上界、池与监听释放；不新增第二bootstrap或万能Lifecycle总管。
   BFF4d6已加入真实生产AppModule的`TestingModule.compile()`与关键token单实例回归；该启动/装配证据不替代实际应用shutdown、drain与资源释放行为。
   2026-11-02只读复核（BFF4d6，非运行验收）：当前main未启锁定Nest adapter的return503OnClosing；worker只接onApplicationShutdown，处于HTTP dispose之后；数据库owner仅普通close无Nest hook，pool.end失败可能阻止Redis关闭；旧signal31秒上界只被raw测试消费。先在生产Nest上复现关闭准入/SSE/worker失败与卡住/PG-Redis释放，保留旧风险保障；不因本静态发现提前实施G1后的清理或新增万能lifecycle总管。
3. 依据原provider图按feature迁移测试消费者到Nest入口/override provider。每个批次明确旧测试风险→新测试位置：身份、错误、body/SSE、取消、幂等、并发、恢复一项不丢。通用helper只承载启动关闭，不暴露global business store。
4. 最后扫描生产、test、scripts、package默认入口，零消费者后删除`src/bootstrap/server.ts`、`src/bootstrap/runtime.ts`、旧dispatcher/相关helpers。不要把旧文件搬到test目录永久保留另一套运行时。
5. 编译、contract、真实I/O及新图行为共同验收；源码字面扫描仅辅助，不靠名字改动或注释匹配证明边界。

### 3.3 C-3：Repository / Service / Port 按真实职责处置

复用原[完整disposition](../specs/2026-10-30-task-a-cleanup-inventory.md)和[provider census](../evidence/2026-10-31-task-a-c3-provider-census.md)，逐项更新结论，不另建一套DTO/层。

| 当前对象 | 目标处置 | 保留风险与验收 |
| --- | --- | --- |
| `createBffComposition` / `BffRuntimeStore` / raw dispatch | 消费者迁移后删除 | 不能只删旧class后改名保留aggregate |
| `createPostgresBffOwnerResources`及9套integration消费者 | 审计聚合职责，改为显式feature/test资源装配后消除无边界locator | 不靠工厂改名完成；每个pool/notify/receipt调用归到实际owner |
| Chat/Projects/ScheduledTask/AG-UI/Idempotency等复杂Repository | 保留必要feature-local持久化边界 | 事务、锁/CAS、lease/outbox、ledger/replay、复杂查询真实存在 |
| 仅转发一次的Service/Port、简单CRUD重复层 | 并入当前feature provider或删除 | 保留授权/错误/取消策略，不因“一实现”删除真实边界 |
| 全局idempotency contract | 审核为有真实跨feature语义的共享契约或迁到合适位置 | 不按目录名机械清零，不再塞其他业务能力 |

删除闭环为：**列消费者→确认替代事实→迁移风险测试→切生产与测试引用→删除旧项→零引用/编译/行为复验**。缺替代事实时保持OPEN，不造空实现或删断言换绿色。

### 3.4 C-4：契约、默认门与运行资源

- App Public28.18 原件来自BFF `091cd5022cf517d243a6390b933f9dded7e3b4a9`，SHA256 `35a86f91e44beb1aeb6b17eca41d3bfdc79f11a43633662113a1778b4fab6082`。增量只有profile GET/response schema/version，原199操作顺序保持，新版200。候选使用原生成器与严格全文28.18→28.17逆证，旧父hash、private/policy快照不动。
- BFF默认入口纳入现有两套Nest架构测试；删除实现耦合/失效测试前证明风险已由当前行为测试承接。格式失败是门失败，不降格“非阻断历史”。
- Node必须匹配owner engines。App候选门用22.23.4，runner候选已更新App为22.23.4、BFF/IAM24.20.0；BFF七条生成链/CI/Docker已对齐24.20.0并通过Root完整门。收据另分期望与实际版本，失败阶段不伪造已验证版本。
- 复用受管PostgreSQL/Redis。前序只读连接/PING成功仅证明可连接；不证明当前完整配置、Schema、身份与业务就绪。凭据只在私有配置，不写文档/参数日志/收据。
- 应用目标是一实例、一数据库、一套应用credential、每owner独立schema；测试临时库只是隔离。核installer/URL对schema的支持，禁止跨owner表访问或reset共享DB/Redis。
- T-13资源归属补充设计：现native IAM fixture只随机分配资源，Root全局前后差集会误归属并发测试。复用IAM fixture现有`resourceId/resourceOwnerToken`、Redis NX marker和named DB机制，允许`bff-session-admission-host`在固定webOrigin下传入两环境字段；旧Web host行为保持。Root只核该run精确DB/prefix与匹配owner marker，不删除未知身份资源。写区限`test/fixtures/bff-session-admission-host.ts`、`test/fixtures/internal-http-application.ts`及现有host integration测试；无公开API/Schema/业务变更，真实I/O由Root验收。补充批准`test/unit/bff-session-admission-host-resources.test.ts`仅覆盖无资源非法env的子进程fail-fast/脱敏；真实named资源/碰撞/中断仍由integration验证。
- 复用现有runner/资源helper补清理，不新建通用编排平台。全部进程/proxy/reader/自有DB/Redis均尝试关闭且汇总失败；未quiescent时保留其依赖资源并报告。收据保存source SHA、stage、结果、资源清理状态，去掉cookie、secret与敏感payload；失败也留脱敏索引。

### 3.5 分层端到端与同步测试交付

| 层级 | 依赖 / 验收 | 结论边界 |
| --- | --- | --- |
| L0 静态/契约 | owner完整命令、生成物、架构图 | 不证明进程运行 |
| L1 隔离最小native | 复用PG/Redis → IAM fixture → BFF → App；真实同源HTTP | 只证明所测session/projects/signout检查，不替代四旅程 |
| L2 C-1.3完整旅程 | 同一冻结组合的真实App浏览器固定域登录/异tenant拒绝与恢复/登出/撤权与负控；Capability接收方独立真实fixture | 形成当前认证闭环；不扩为全产品验收 |
| L3 受影响业务组合 | 按具体旅程增加System/Capability/Storage/Billing/Scheduler/Agent worker等实际依赖，Admin/Mori仅有受影响路径时加入 | health与业务结果分别记录；不为“全部启动”盲开服务，不假定每个owner都支持匿名readyz |
| L4 用户同步测试 | Root交付已验证源码组合、无秘密的访问入口/可测范围、私有日志索引、启动/停止归属、已知缺口 | 临时smoke已退出的进程不算常驻可测环境；本轮尚未交付该状态 |

启动顺序由实际调用依赖和owner README决定，先提供方后消费者；关闭反向且只停止本任务拥有的进程。已有用户预览与共享基础设施不重启。同步环境的保留/清理策略在后续运行阶段明确，不把PID/凭据写进版本文档。

---

## 4. 执行顺序、并行写区与检查点

保持用户指定次序：**先C-1.3，再C-2/C-3，最后C-4全量验收，再A任务**。允许独立只读调查和已冻结候选审查并行；不以并行之名提前开展后继业务写入。前置例外为本任务候选门禁所需的T-06机械格式修复、T-18已复现的Node运行/生成工具链修复，以及真实native运行复现的T-17最小启动/关闭缺陷；它们不等待G1，避免验证依赖成环，也不授权提前批量迁移raw消费者。

### Chunk 1：当前方案与既有候选接收

- [x] T-01：Root完成本文/摘要/历史入口整理，独审、文档验证通过；冻结的是本轮方案，不是业务已验组合。
- [x] T-06/T-07/T-12/T-18既有候选接收：Root完成冻结复核/静态完整门及BFF真实schema补测，子仓独立draft PR与Root精确gitlink已交付；仅闭合原切片，不替代新候选和最终组合门。
- [x] T-04/T-13：原runner/source/Redis注入与清理修复完成；真实失败退出和Root535最小成功退出均cleanup PASS，只关闭此smoke范围。
- [x] T-17前置子项：BFF4d6五DI修复、真实容器回归及Root535最小native通过；完整生命周期子项仍开放，不据此放行raw删除。

### Chunk 2：先关闭C-1.3

- [ ] T-05：T-17前置子项发现的阻断已解决、最小native smoke通过后，补真实四旅程与独有负控；记录owner/request/receipt关联、最终HTTP与UI状态。
- [x] T-14接收方切片：producer盘点、三面设计、receiver-only实现与取消负控已交付f515；Root独审、完整门/真实接收方及Root六文件精确配对完成。最新PR12基线整合另属T-09，未据此关闭G1/G3。
- [ ] Root复查旧RP/Product Session/first-party workload OAuth的处置与零生产引用；G1满足后才推进下一chunk。

### Chunk 3：C-2/C-3最终清理

- [ ] T-17完整子项：在前置运行保障基础上，补全Nest drain/SSE/worker与真实PG/Redis释放矩阵；它是T-11最终删除的前置，不把前置最小修复当整个T-17完成。
- [ ] T-11：每批指定feature与精确文件，迁raw tests/fixture，更新重叠census；公共入口/Schema/lockfile始终单writer。
- [ ] T-11：全部风险承接后删除raw server/runtime/旧dispatcher/无边界aggregate，重跑零消费者、contract与真实I/O。
- [ ] T-06复验：前置格式门已处理；本批新触及文件若再有格式失败，只作机械修正并复验无行为改动。

### Chunk 4：C-4整体验收与A门交接

- [ ] T-09/T-16：全部相关写区停写，Root按仓串行跑完整门，记录新失败/既存失败/环境缺口；集成后再核精确gitlinks。
- [ ] T-15：运行当前组合真实跨仓/浏览器旅程，交付可同步测试入口与关闭规则，记录仍未支持范围。
- [ ] 仅当G1/G2/G3全部满足，结束当前清理Goal；再按原任务开启A-01/A-02、之后A-07，不预写A代码。

### 并行职责

| 角色 | 唯一写区 / 范围 | 排除 / 交接 |
| --- | --- | --- |
| Root主控 | 本计划、task/CURRENT/evidence；Git index/提交/组合/进程资源/最终验收；Root runner按本轮明确派工 | 不同时修改worker写区；受影响owner完整门由主窗口串行执行 |
| App worker | 后续获准的App固定consumer/native adapter及对应测试 | 不动BFF/IAM契约或Root任务表；原56文件已提交并pin；当前冷登录五文件已停写待Root验收 |
| BFF worker | 后续按feature授予的BFF生产/测试窄切片 | 公共入口/package/lockfile单writer；原11路径加格式32/工具链21已提交，后续另授写区 |
| 独立reviewer | 只读规格/代码/证据、缺陷与门禁核验 | 不实现、不提交，不把worker退出码当Root通过 |
| IAM/Capability专项owner | 到相应阶段替换空闲worker slot，先contract再consumer | 不新增并行contract writer；不同时铺开全仓重写 |

2026-11-02当前交接：`iam_browser_session_fixture`新增integration已获Root真实RED，继续已批准test-only host协议；`native_browser_driver`独立Root三路径永久编排已完成双审/Root82定向及1931治理，冻结后接收组合再实跑；`native_journey_ui_audit`只读UI路径及断言审计已交付；`task_a_status_audit`只读复核原A范围与估时依据。Root唯一维护任务表/Git/真实资源/完整门。本轮按用户要求整理进度，不新增业务实现；后续既定T-05无需重复审批。

---

## 5. TODO 台账（后续持续更新）

状态：`OPEN`未做；`IN_PROGRESS`正在执行；`REVIEW_PENDING`候选已有证据、待主方复验；`VERIFIED`仅该切片已验；`WAITING`依赖未满足；`GATED`后继停写。未运行、skip和设计通过都不记为功能完成。

| ID | 事项 / owner | 状态 | 依赖、下一动作与完成证据 |
| --- | --- | --- | --- |
| T-01 | 方案/问题/Goal/TODO统一；Root | VERIFIED（文档） | 三个只读角色审计；两项依赖循环已修；独审、链接/diff通过，后续状态变化继续更新 |
| T-02 | MCP denied icon零owner副作用；BFF | VERIFIED | `228e3d6`、focused42、旧基线full；最终组合继续回归 |
| T-03 | invalid-owner typed error；BFF | VERIFIED | `228e3d6`、focused24、旧基线full |
| T-04 | 资源/Node/source/schema preflight；Root | VERIFIED（已提交组合前置） | Root535精确App9ba/BFF4d6/IAMe6及Node/source门已过；Root41b仅文档后继。新dirty候选要重新精确配对，不继承当前source clean结论 |
| T-05 | 当前native四旅程；Root+IAM/BFF/App | IN_PROGRESS（冷登录/退出HTTP已验） | 精确App e1be：真实冷登录303/session认证true/projects200，退出200后session匿名/cookie0/projects401，旧cookie401。余下Settings UI点击、异tenant拒绝/固定域恢复、独立session/membership撤权及迟到状态未验。IAM1ee8d156已双审/Root完整verify1566及两host66pass/0skip并推PR6；永久driver双审/Root82定向与1931治理通过，精确pin后实跑四旅程 |
| T-06 | BFF格式门；BFF | VERIFIED（候选） | Root format exit0，AST/注释等价32/32；独审确认原11候选byte不变、1068tracked符合冻结；后续改动再复验 |
| T-07 | App Public28.18消费修复；App/Root | VERIFIED（切片） | Root完整check：contract452/architecture50/full6373，lint/types/build通过；App9ba65343已推送PR50并由Root精确pin；四旅程待T-05 |
| T-08 | IAM SDK与verify；IAM | VERIFIED（当前候选） | IAM1ee8d156 / 原PR6已推送；Root verify121files/1566pass/build，真实两host66pass/0skip；本次Root接收新pin，不代表跨仓native端到端 |
| T-09 | Root/各受影响owner最终串行门；Root | WAITING | G1/G2、T-06/T-07/T-12/T-13/T-16收敛；精确冻结SHA+pass/fail/skip |
| T-10 | A-01/A-02/A-07及其余A backlog；Root | GATED | G1/G2/G3全部闭合；原16任务责任和优先级保持 |
| T-11 | raw/global/剩余Repository-Service-Port；BFF | WAITING | G1后，先T-17；feature迁消费者→删旧实现→零引用/真实行为 |
| T-12 | Nest默认架构门与入口隔离；BFF/Root | VERIFIED（切片） | 173e026；Root第三轮format/check exit0、contract1344/default2343pass+2skip/build通过；两资源skip另真实PG15pass/0skip；raw最终删除仍属T-11 |
| T-13 | native smoke清理与脱敏证据；Root | VERIFIED（最小smoke范围） | 六路径双审；Root60相关/1876治理、IAM真实62；旧组合两失败退出和Root535e7071新组合成功4checks退出均cleanup passed/quiescent、无保留文件；不覆盖完整生命周期/常驻环境 |
| T-14 | global_register direct credential；Capability/Root | VERIFIED（接收方切片） | Capability f515e225 / 独立draft PR13，Root最终format/lint/verify/Prisma/build全0（3051pass/678skip）；真实receiver1pass，Root配套六文件154定向/1879治理。原PR12新增基线导致PR13冲突，后继整合归T-09，不能合并或称全组合完成 |
| T-15 | 当前组合同步E2E可用性；Root | WAITING | 区分临时smoke与可保留测试环境；健康/受支持旅程/日志索引/回收归属齐全 |
| T-16 | Agent与原C-1删除项最终复核；Agent/Root | OPEN | `c761fad`仅focused130历史证据；当前全门及旧语义零生产引用；任务外治理问题留owner |
| T-17 | Nest启动/shutdown/drain/pool释放；BFF | IN_PROGRESS（完整生命周期待验） | 前置已验：BFF4d6d17b五DI修复/真实容器回归、Root完整check2344pass+2skip，Root535e7071 minimal native4pass/cleanup PASS；完整drain/SSE/worker/PG/Redis矩阵仍在G1后、T-11删除前 |
| T-18 | BFF Node24运行/生成工具链一致；BFF/Root | VERIFIED（切片） | 173e026；21路径独审/1068tracked hash匹配；Root第三轮format/check exit0，106generated与原43路径保持，7正规生成/双检通过；两轮RED保留，CI/Docker未实跑不称通过 |

---

### 5.1 下一检查点与工期口径（2026-11-02）

1. **已执行／Root**：IAM新测试真实RED，唯一选择器`binds only fresh browser sessions and isolates tenant, signout and revocation journeys`，exit1，1fail/10未选；ready成功后旧host拒绝browser_fixture并退出。已交原writer实现。下一动作是接收Root永久driver tests-only RED与IAM候选独审/真实GREEN，不重复等待用户继续。
2. **T-05／IAM→Root**：owner只实现已批准的test-only有限session绑定/tenant/revoke协议及有界关闭；主方独审、真实GREEN、owner门、独立PR和Root精确pin后，永久browser模式验四旅程、UI退休/迟到响应。凭据仅私有管道，Root不写IAM SQL。
   **组合依赖边界**：G1按当前已冻结、已验证的Capability f515组合判断认证门，不等待最新base整合；I-25/T-09整合在最终G3前完成，新组合重跑受影响G1回归。这样不形成G1等待T-09、T-09又等待G1的循环。
3. **G1→T-17/T-11／BFF**：生命周期真实释放通过后，按feature迁移原消费者并删除raw/aggregate；不提前删除测试或创建第二套运行时。
4. **T-09/T-16/T-15／Root与owner**：保留双方更新整合Capability publication冲突，完成Agent及受影响owner最终门、组合E2E和可同步环境。每仓独立PR，未完成前不合main。
5. **原A产品阶段**：G1～G3通过后才进入A-01/A-02→A-07；其余原A任务继续保留。当前原16项没有逐项剩余工作量与已配对端到端验收，故尚无可信完整完成日期；不把“未验收”解释为全部从零实现。下次估时须标明范围、基线、依赖、实际剩余量和置信度，而不是滚动重复3～7日。

本次Goal保持active，未创建重叠目标或将任何未验条目标complete。后续交接注明“主控下一动作”，不将worker等待当作需要用户再次发送“继续”。

## 6. 验证与风险控制

### 本轮文档交付

- `git diff --check`；本轮改动Markdown的本地链接检查。
- 独立review核“当前/历史、候选/Root验证、C/A边界、问题→TODO→关闭证据”一致。
- 仅为核验半成品运行native runner单测（1pass/2fail），没有启动业务服务。文档轮不重跑全部业务门、不安装Schema。

### 后续执行与最终验收

命令在对应owner目录执行，先核manifest/CI，不假定每仓同脚本：

| 范围 | 命令 / 证据 |
| --- | --- |
| BFF | `pnpm format:check`、`pnpm lint`、`pnpm typecheck`、`pnpm test:architecture`、`pnpm contract:check`、`pnpm test`、`pnpm build`；默认脚本已覆盖的步骤避免无意义重复；真实PG/Redis条件测试另列 |
| App | `pnpm check`（contract、architecture、lint、typecheck、test、build）；真实浏览器使用关闭preview的native模式，默认preview E2E不替代认证验收 |
| IAM | `pnpm sdk:check`、`pnpm verify`与相关真实native/profile/撤权integration；核verify覆盖后不重复等价全门 |
| Agent | `uv lock --check`、`uv sync --frozen`、`uv run ruff format --check .`、`uv run ruff check .`、`uv run pyright`、`uv run pytest`、`uv build`，资源marker按真实依赖补跑 |
| Capability及实际受影响owner | 读取各自AGENTS/README/manifest，执行格式/lint/types/contract/test/build及本次真实I/O；未触及的owner不无端重写 |
| Root | `python3 scripts/verify-repository-topology.py`（组合变化后）、`python3 -m pytest scripts/tests`（治理/runner完整交付）、相关规范审计及gitlink/consumer digest核验 |
| 真实链路 | 精确source/clean preflight、owner health/readiness、认证与业务负控、持久事实回读、取消/重试/恢复、全部自有资源回收 |

暂停入口 `verify-ten-repository-full.sh` / `run_stage2_owner_health.py` 不作完成证明；System smoke只证明自己的链路。

回滚使用原切片/精确gitlink与前一已验组合；不覆盖其他人未交接修改。凭据/共享数据不回滚或重置。仅在原有风险被承接或需求正式废止后删除测试；不删失败断言、加timeout、改历史hash或恢复fallback来通过门禁。用户本轮明确授权按仓各自PR交付，未完成前不merge到main；候选可提交/推送并维护draft PR，Root只更新已推送子仓精确gitlink。发布部署不在本轮范围。

## 7. Goal / TODO 后续更新规则

1. **触发时机**：新问题、写区/依赖变化、切片停写、测试结果变化、提交/pin变化、阶段验收时更新。纯对话无状态变化不制造新计划或重复全量运行。
2. **每条TODO记录**：原ID、owner、状态、依赖、精确基线/候选manifest、命令与exit/pass/fail/skip、未运行范围、下一动作。发现问题先登记再修，不让代码走在方案前面。
3. **唯一writer**：Root更新本表及阶段Goal；worker交接文件/结果/风险，reviewer只读核验。`task.md`/`CURRENT.md`同步简报，证据文件追加本次事实，旧证据不改写成当前成功。
4. **主方完成判定**：worker报告→独审→停写后的Root相关门→真实受影响旅程→精确组合。少任一必要层，只标REVIEW_PENDING/OPEN，不标VERIFIED整体。
5. **机器Goal**：每次阶段交接用`get_goal`核验；当前目标未完成时保留active。只在用户明确要求暂停时设paused；同一外部阻塞连续至少三个goal turns且无可推进工作才按工具规则blocked；G1/G2/G3全部达到才complete。不要为了更新文案虚假complete或重复create_goal。
6. **下一轮默认动作**：T-17前置与T-13最小成功/失败清理已完成，不重复领取。现在先接收IAM tests-only候选的真实RED并完成T-05永久四旅程；T-14接收方已验，不再重复实施；G1闭合后T-17完整生命周期→T-11删除→T-09/T-16最终组合门→T-15同步环境。A功能继续门控。

### 历史暂停后续接检查点（已被下方 active 状态更新）

用户已明确继续。工具Goal记录仍显示paused；继续请求已撤销此前暂停指令，本轮不伪造状态切换，也不创建重叠Goal。阶段目标仍G1/G2/G3 OPEN，A门保持。

T-13五项修复已获规格/质量双审，六路径hash停写匹配；Root相关60pass/31subtests、完整治理1876pass/3skip/502subtests（exit0）。IAM真实两个host文件62pass/0skip，完整verify121files/1566pass/build通过，已推送e6a01cf与本仓draft PR #6。App/BFF原已验候选保持。三精确gitlink暂存后topology PASS；暂存前因旧pin的三项预期mismatch保留为阶段记录。当前等待Root提交后实际最小native，不把宿主测试或临时数据库隔离视为应用单库组合/浏览器四旅程。

### 历史阶段：首次真实 native 失败与当时下一动作

Root已提交/推送b2f9a59c，精确pin App9ba65343/BFF173e026/IAMe6a01cf。两次最小native在source clean/gitlink、Node、BFF build/schema及IAM host之后，于BFF startup失败，completed_checks=0；两次cleanup passed/quiescent=true、无保留workdir。诊断复现定位UnknownExportException：ChatModule导出CHAT_TURN_SERVICE，但该token由AgentDispatchModule拥有。此为T-17允许的前置启动修复，不等待G1，不扩展为raw消费者批量迁移。Skills/Projects导出与ProjectAccess/Billing数据库导入为只读同类候选，尚未逐个实测。

下一步由BFF唯一writer核对真实owner/module可见性，补实际Nest容器compile/启动回归（不只源码字符串断言），最小修复后Root完整门与精确pin再跑native。最小HTTP仍不替代四浏览器旅程；T-13清理仅在本次失败路径有实测证据，成功路径待后续。G1/G2/G3继续OPEN。

### 历史阶段：T-17 前置实现写区与接收过程

BFF唯一writer `bff_node24_generation`，基线173e026；限定chat.module、skills.module、projects.module、project-access.module、billing.module五个现有生产文件及现有nest-runtime-architecture测试。先真实生产AppModule容器compile RED，逐项纠正owner/module可见性；仅替换测试配置与外部资源，保留真实DI图/factory，不auto-mock缺失token、不重复provider、不global Database。新增文件/默认门接线需求先报告；生产写区外的新阻断先报告。worker不做Git/真实服务/完整门，停写双审后Root串行全门与native。T-14由独立只读角色完善owner局部设计，与BFF不重叠。

T-17范围补充：真实生产AppModule compile已依次复现五个RED（Chat/Projects/Skills非法导出，ProjectAccess缺BFF_DATABASE，Billing缺BFF_POOL），五处修复后compile GREEN。扩architecture出现72pass/2fail，系旧nest-feature-architecture两断言强制引用已删除的非法re-export；批准只将两断言核对迁至真实provider owner/模块导入，既有行为/路由断言保留，由真实DI及单实例回归承接风险。写区最终5生产+2既有测试，不改package/依赖；尚待停写双审与Root全门，不据worker GREEN称已可启动。

T-17前置候选已通过独立规格/质量审阅及Root冻结hash复核。Root完整format/check exit0：contract1344pass、default2344pass/0fail/2原资源skip、lint/types/build通过；不是全真实I/O。BFF实现4d6d17b沿原PR18交付，下一步精确Root pin后真实native。T-14 owner三面设计独立推进，只改三文档，不并行写生产。

### 已验阶段：Root535e7071 最小链路及当时T-14文档门

BFF4d6d17b / IAMe6a01cf / App9ba65343的exact SHA、clean、Root gitlink及实际Node均通过。诊断包装只在失败时捕获内存脱敏信息，不替换成功路径行为；本次生产BFF启动、App同源session/projects、fixture直接IAM signout后401及日志扫描共4checks PASS，cleanup PASS/quiescent，无保留workdir。仅最小HTTP，未覆盖真实登录/切tenant/App登出/独立撤权；不把process组退出当完整Nest drain/池优雅关闭证明。

T-14三面门已Root复核：复用policy/schema，当前auth-source摘要派生索引绑定接收分流，旧contract-only combined/冻结v9/既有BFF-Agent pin不动；caller取消保证不扩大到COMMIT已发后的原子零写，不宣称补全历史R328。仅三owner文档dirty，后继代码待独立writer按门实施。

### T-05验收纠偏与T-14实施写区

只读证据：App TECHNICAL_DESIGN §固定部署tenant（约3203–3228）明确删除Team selector与/api/team/switch；IAM设计约850–872允许第二tenant membership用于负例；BFF设计约3626–3634及user-admission.ts固定tenant不符即403；本轮G0设计spec约409仍固定Product tenant。因此纠正的是本计划“正向切双tenant”错误，不变更已批边界、不缩减当前隔离/撤权要求。新跨tenant产品能力不属于本清理片。

T-14 Capability唯一writer按三面门实施；Root已在44fcc5d建立codex/task-a-c1-capability，Node24.20.0/pnpm11.25 frozen install成功且lock不变。批准额外现unit/mcp-p3b的register取消负控及现skill-admin-admission测试迁至有效单用途准入oracle；任何业务/冻结协议扩区继续先报告。另Root独立writer仅处理三旧配置消费者及对应低层测试：不再要求/注入resource-server配置、不再生成其文件；IAM公开OAuth fixture协议及Root收到的secret保护保持。两写区互不重叠，完整门/真实服务/Git只由Root执行。

### T-05真实冷登录RED与Root消费者候选

Root使用现精确组合和全新Chromium context实测/login表单，不向浏览器注入fixture cookie。浏览器登录凭据仅从当前自有IAM fixture的get-session与公开测试密码在内存取得，走stdin，不留凭据日志；诊断收据仅状态。结果：form_present=true、signin303、session401、projects401。该诊断独立于原最小HTTP4checks，后者仍PASS且该run最终cleanup PASS/quiescent、无保留文件；不能拿原4PASS覆盖浏览器RED。App单writer按现固定Product语义准备修复，尚未源码验收。

Root三旧resource配置消费者候选6文件已停写并独审CLEAR；Root实际定向154pass/141subtests，源冻结在本地manifest。顺带同文件真实O_EXCL同名冲突已先RED后修复，未mock文件装配过门；IAM公共OAuth fixture接收字段/secret保护保持。Capability仍实现中，Root不先宣称该组合已可运行。

T-05 App修复局部门已确认：现sign-in路由内sign-in/email→新issuer cookie合并→原生set-active→现admittedNativeSession最终准入，才303进入产品。tenant沿现BFF/IAM credential opaque词法（1..255且无空白/控制字符），绝不新增UUID限制/浏览器选择。坏配置在凭据发送前拒绝；上游全序列共用一个有界deadline/取消信号，不每步重置预算。签入后续失败退休本次flow/CSRF、不发新issuer cookie、不清除请求既存issuer cookie、不自动重发密码/额外signout；新未交付session由现IAM TTL回收。成功按每cookie名称最后合法值发送，删除项不带入后继Cookie header。限现route、native-sign-in测试、env例和TECHNICAL_DESIGN/CURRENT；新helper/其他写区须报告。独立App writer，Root保留真实浏览器RED；最终完整门和浏览器GREEN由Root完成。

### T-05冷登录候选Root完整门与精确交付

App727cd674fd45487d3d9becc685701546623865b1：Root Node22.23.4/pnpm11.25.0完整pnpm check exit0，contract452、architecture50、full354files/6401pass/0skip、lint/types/build通过；1494tracked输入前后hash一致，独审CLEAR。仅五明确路径提交并沿原draft PR50推送，本次Root提交精确pin；未合main。浏览器冷登录GREEN/完整四旅程待验，不沿用原fixture4checks替代。

Capability71路径另获Root独立只读审查CLEAR及hash核验，完整format/lint/verify/Prisma/build按序运行中；终态以实际exit为准，不以worker123替代。

### 当前验收推进：冷登录GREEN、T14全门RED与后继设计

Root4fdb2ede精确App727/BFF4d6/IAMe6 source/clean/gitlink通过。全新Chromium context未注入cookie，真实表单303、session200、projects200；独立冷登录诊断与原最小HTTP4checks均PASS，cleanup PASS/quiescent/无保留资源。仅关闭I-21冷登录缺陷，不关闭T-05四旅程。

Capability首次Root完整门format/lint/Prisma validate/build均0，verify退出1：3049pass/678skip/2fail。两项为本次旧OAuth删除/有效Agent错用途导致的旧oracle：preflight期待泄露ENOENT但现execution reader抛sanitized错误；generated-client期待Code16但应为有效credential错surface的Code7。只授权两现测试精确承接typed失败、无监听/零写，保留RED，生产不因此改宽。待重新冻结后Root真实receiver及完整门。

I-24退出局部修复授权App唯一writer：现iam route、现真实transport测试（必要时原route测试）及CURRENT；先loopback真实RED，再按已批准空体POST补明确零长度Uint8Array，不放宽transport或新建helper。当前冷登录源码已提交，不在验收中重写。

T-05余下旅程的后继最小设计：沿现IAM native host增加test-only浏览器fixture、session绑定slot和有限switch/revoke命令；cookie从浏览器自然签发只在私有pipe/内存交接，owner验签并核本fixture同user、非seed exact session后才绑定；Root不SQL IAM。另建同一user合法第二tenant membership验证固定Product拒绝及真实重登恢复；App UI退出须核exact session消失；独立A/B浏览器分别验exact session撤销仅影响A、membership撤销时B session仍存在但准入拒绝。保持原最小smoke模式，新driver/模式显式扩四旅程；先停Chromium再Web/BFF/IAM，保现精确资源回收。具体写区限IAM native host/其integration、Root native runner/新Chromium driver/现runner测试。此处为当时设计记录。2026-11-02新增IAM单integration测试候选，真实RED尚未运行；host实现与永久四旅程编排仍未交付。

### I-24主方静态门与T14真实接收方GREEN

App1d54eedd4d67482c789ae3f7dd60807302732b24三文件退出修复已独审并经Root完整check exit0（contract452/architecture50/full6403/0skip、lint/types/build；1494hash保持），沿原PR50交付。本次Root仅更新App精确pin；真实sign-out及旧cookie重放另验，T-05仍OPEN。

Capability72路径修正canonical ownership断言后，Root真实HTTP→production receiver→隔离PG组1pass；13项为本次-t未选择，不计本组覆盖。System成功/自然重放/冲突/disabled不复活、BFF/Agent/未知凭据拒绝、文件删除后撤销、ownerTenantId/ownerUserId均null、零receipt/outbox/IAM请求均过；数据库inventory前后相同，Redis仅connect/ping/quit无key写入。不是System producer链。最终完整owner门再次串行运行中，尚不提前标全绿。

T14实际交付：Capability f515e225，PR13 OPEN/draft，base为原PR12候选分支；GitHub实际mergeable=CONFLICTING，明确不合并。Root配套六文件hash保持，再跑154定向/141subtests通过（前轮完整治理1879/3skip/506同源码）；本次Root提交精确pin f515并配对退休配置删除。I-25记录最新基线集成，不借旧已验组合否认他人四个新提交。

I-25只读集成调查已完成：共同基线44fcc；9重叠中5处文本冲突为provenance与四份设计/current文档，另checker/product-mcp.rpc/mcp.ports/architecture需语义复核。更重要的是远端mcp-private-server-v2-contract.ts从冻结父重建整份provenance，会拒绝/生成时删除T14认证索引；后继必须保v2精确contract发行及认证索引独立严格校验，并补生成保留/只读不写负控，不能重签父快照或删除索引。新Schema的global currentConnectorId=NULL需真实T14重验；B01 private/personal、fresh/父升级/回滚/代际撤权及Custom API真PG均随新组合重验。新B01消费者发布/正常Schema激活归其owner，不在本片擅自实现Task B；当前f515证据不继承到新合并树。本轮只读调查未合并、写对象或修改base分支。

App媒体类型修复e1be73e08bb1bd4c9c554c9e319f6b079006fdb5已Root独审与完整check exit0：contract452/architecture50/full6407/0skip、lint/types/build，1494输入hash不变。仅三文件沿PR50交付；本次Root精确pin后再次验真实App sign-out/旧cookie重放。I-24在真实GREEN前仍OPEN。

### I-24真实退出最终GREEN（Root1e6组合）

同一新Chromium未注入cookie，真实表单303、session200且authenticated=true、projects200；浏览器实际调用App sign-out返回200，session200且authenticated=false、issuer session cookie数量0，projects401，内存旧cookie独立HTTP重放401。原最小smoke4checks与cleanup passed/quiescent/无保留文件均过，原RED和匿名状态错误oracle留证。无cookie时session接口既有契约为200/false，不是401；修正临时driver为精确false+cookie0+业务401+旧cookie401，未放宽生产或删负控。仅关闭I-24及冷登录HTTP缺陷；本次不是Settings按钮点击，也未运行异tenant恢复/独立撤权完整四旅程。
