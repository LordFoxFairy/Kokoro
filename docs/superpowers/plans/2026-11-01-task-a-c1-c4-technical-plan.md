# Task A 当前进度、问题与 C-1～C-4 闭环技术方案

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 先完成 G0 / C-1～C-4 的认证切换、旧实现删除和真实验证，再进入 A-01/A-02，随后 A-07；保留 A-03～A-16 的完整产品责任，不以清理完成代替 Task A 产品闭环。

**Architecture:** IAM 唯一拥有人类 session、active tenant 与权限；App 同源适配 → BFF Nest feature → owner API/RPC。Nest `AppModule` 是唯一运行时组合根；旧 raw server/runtime、dispatcher 和无边界 aggregate 在消费者迁移后删除。有效的事务、幂等、取消、恢复、lease/outbox 语义必须承接，不机械删除 Repository 或新增空层。

**Tech Stack:** 现有 TypeScript/NestJS/pnpm、PostgreSQL/Redis、owner generated clients、Python Root 治理；各仓 Node/Python/Go 版本以其 manifest/lockfile 为准。

**前一文档轮已完成：** 问题、方案、TODO/Goal已独审并冻结。当前按用户Goal续接Chunk 1：T-06/T-07/T-12/T-18候选主方门已完成、App/BFF各自draft PR已推送；T-04/T-13审修与Root静态/宿主真实门已通过，最小native运行待验，T-14只读盘点已完成、owner局部设计待做。没有把文档轮的交付状态当作产品完成，也不进入A功能。

---

## 0. 当前结论与唯一入口

**Task A 尚未闭环，C-1.3 / C-2 / C-3 / C-4 均未达到最终完成条件。** G0 已有审阅通过证据，不重新发明架构；App 与 BFF 当前候选已完成主方静态完整门；App 已推送独立 draft PR，BFF 已推送独立 draft PR #18。真实 I/O、Root 精确 gitlink 与跨仓集成尚未齐备。当前组合也没有可交给用户同步测试的完整启动、健康检查与浏览器旅程收据。

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
| Root | `4715d2b7c17ea4f9e879e3223fd9d703997df2e0` | 本轮文档及 native runner/单测候选；清理已实现，Root 相关三套单测52通过，五项独审修复已停写且双审通过，Root60相关/1876治理通过；完整native待验 |
| App | `9ba653433c75dd3919bcc3de3cafc778fda4b975` | T-07实现4260f698；Root完整check通过后集成origin/main空树merge，源码不变；已推送独立draft PR #50，尚未Root pin/真实四旅程 |
| BFF | `173e0263f21e2cc7499a67592b4526d811dde693` | 64路径代码候选加当前摘要已提交；Root format/check通过、contract1344/default2343pass+2skip；另真实PG schema15pass/0skip；独立draft PR #18已推送，Root pin待做 |
| IAM | `e6a01cf7f1aeef0cfd5a63efe78e194b50ad1e9b` | 4个fixture/回归路径经Root真实两host62pass、verify121files/1566pass；独立draft PR #6已推送；不等于跨仓UI验收 |
| Agent | `c761fad3dba2b56cd7fe4da7683a9ac2f208243f` | C-1.2 清理已提交；最终完整 owner gate 仍待 |
| Capability（物理路径仍为 kokoro-capability） | `44fcc5da599b4a5cec3077e41aaef4375fe4add2` | `global_register` workload OAuth 尚存，先盘点真实调用方再切换 |
| 其他组合成员 | 当前 Root gitlinks | 仅按受影响边界纳入验证；本轮未启动、未刷新全套运行健康状态 |

### 0.2 进度与验证事实

| 阶段 | 已有成果 | 当前结论 / 缺口 |
| --- | --- | --- |
| G0 | ADR-036 Accepted；2026-10-31 reviewer 放行；native artifact 1.0.0 / SHA256 `5cf59df4b7bd9853edfd2eabb31afc236c0ec0db371f9737706fc129484fd83f` 已固定 | 设计门已通过；新的具体写区仍须按本文局部设计确认，不把设计批准当运行验收 |
| C-1.1 / C-1.2 | BFF schema-evolution 旧入口、App hash/legacy 展示分支、Agent legacy_failed 推断等已删除；保留 canonical localDraft / journal / replay | 已提交切片；最终零消费者复核及 App/BFF/Agent 完整门待 C-4 |
| C-1.3 | IAM native admission、App/BFF 原生消费、profile read、旧 RP/Product Session 清理已有实现；IAM SDK drift 已修 | 当前组合四旅程缺证；Capability global_register 未切；服务启动/资源清理未闭环 |
| C-2 | Nest 生产图已移除 LegacyRoutes；named feature 路由接管；generic configured-owner proxy tail 已删除 | raw server/runtime 与测试消费者仍存；生产 Nest shutdown 语义待核；入口隔离候选不等于删除完成 |
| C-3 | BffBusinessStore / BffApplicationServices / PostgresBffRepositories 旧 aggregate 已清理多片；global ports 仅留 idempotency contract | raw composition / owner-resource 聚合工厂和 feature disposition 仍待最终审计，不以类名删除代替边界证明 |
| C-4 | BFF 两个行为失败已修；IAM 全门通过历史基线；App 契约修复候选已绿 | App/BFF当前候选静态完整门已通过；Root runner审查修复、IAM候选/Agent最终门、完整真实I/O/端到端仍未完成 |

证据严格分层：
- **已提交旧基线**：BFF `228e3d6` 默认测试 2298 total / 2296 pass / 2 skip / 0 fail；该时默认入口未纳入两套 Nest 架构测试。IAM `a1457be` verify 为 120 files / 1561 pass / build PASS。Root 上次 topology PASS，治理 1846 pass / 3 skip / 502 subtests。这些不是当前 dirty tree 全绿证明。
- **App 已提交候选，Root 复验结果**：Node 22.23.4；contract 48 files / 452 pass、architecture 50 pass、完整 test 354 files / 6373 pass / 0 skip；typecheck/lint/build/diff-check 通过。旧基线50个契约失败已收敛，Root完整check exit0且56路径前后SHA一致；已提交4260f698、集成origin/main空树merge为9ba65343并推送App draft PR #50。Root pin/真实旅程仍待。
- **BFF 已提交候选，Root 复验结果**：Node24.20.0下format/check exit0；contract1344pass，默认2343pass/0fail/2skip，lint/types/build通过。两项原数据库条件skip另补整文件真实PG schema15pass/0skip，覆盖共存/回滚与R237。原architecture73/focused123为辅助证据；未完成完整业务integration/当前native链路，字面依赖扫描不称完整AST图。
- **Root runner阶段实测**：初始1pass/2fail（close函数未实现）保留为RED；后续实现后Root三套runner相关测试52pass/31subtests。独审发现Node收据混淆期望/实测、部分连接失败回收、inventory异常阻断强杀、保留资源恢复身份、source失败收据丢已验SHA五项，修复中；此前GREEN不替代修复后停写验收。
- **历史真实链路**：旧组合有 IAM 集成 12 pass、IAM→BFF 7 case、HTTPS native smoke 4 case。保留其对应 SHA/范围；不外推到当前 Nest/候选组合，也不将历史 OIDC 验证作为目标 native 链路。

---

## 1. 已知问题全量表（本次 Task A 审计范围）

这里只把本次可核验的问题标为当前事实；历史或任务外问题保留归属，未核验不等于无问题。

| ID | 问题 / 当前证据 | 处理与关闭条件 | TODO |
| --- | --- | --- | --- |
| I-01 | 当前native smoke精确源码组合/资源清理尚未完成；App/BFF已提交且clean，但Root gitlink待更新，IAM fixture仍dirty，继续保持source门 | 先完成候选精确gitlink集成，再注入私有配置；保留 exact SHA/clean 门，不以绕过门禁跑“成功” | T-04/T-13 |
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
| I-17 | 原runner移除了必需的Web Redis输入（冷登录缺值503）；候选已恢复精确隔离注入/清理，待最终审查与真实冷登录 | 不是已退休配置；候选已补隔离注入与key归属/清理，仍需真实冷登录覆盖。现session探针不触发该路径，默认Playwright又开启preview，均不足以发现此缺口 | T-04/T-13/T-05 |
| I-18 | 原BFF engines与pin/生成链/CI/Docker存在Node24/22漂移；173e026已统一并通过Root当前完整静态门 | 保留两轮RED与真实修复证据；七条正规生成/双检及当前完整门通过，106generated不变；未实跑CI/Docker，不以配置对齐冒称容器验收 | T-18 |

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
| A-16 | 文档、PR、合并与运行配对 | 随片交付；App/BFF独立draft PR已推送，Root pin/真实配对/最终验收未完成；未merge或上线 |

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
- 正向四旅程：真实登录→同源session/业务读取；通过App切换两个tenant→后续请求和页面事实换域；App登出→旧cookie失效；独立撤销session/membership→已开页面下一次请求拒绝。跨标签迟到响应不串身份。
- App当前native投影没有tenant标记；同subject切tenant后的页面与在途请求退休是待验证风险，不据源码直接认定正确或新增一套身份协议。IAM `verify`不含真实integration；App默认Playwright开启session preview，另设真实配置旅程后才能引用为认证证据。
- 负控：匿名、错Origin、伪造tenant/subject、失效/错surface服务身份、重复登出、撤权后旧请求、IAM不可用；拒绝时零越权owner写入，未知结果不补成功。
- 当前 `run_web_native_session_smoke.py` **只是三服务最小HTTP smoke**：fixture给现成native cookie→`/api/auth/session`→`/api/session/projects`→fixture直接IAM signout后401，加日志检查共4case。不是浏览器登录，不覆盖tenant切换、App登出、独立revocation或全部owner。
- `global_register`：先核真实producer与接收方写区。Capability复用既有direct service credential校验与无tenant/caller/surface规则，承接注册授权/幂等/取消，再删除该surface的OAuth分支及专用消费配置；第三方MCP OAuth、IAM公共OAuth与Billing资金授权保持。调用方待证不新增无需求服务。
- T-14盘点补充：Capability当前RPC接收方真实可写，但冻结v9 manifest仍inactive/routable=false，注册profile身份段还是operator_machine。认证切换需owner单一当前auth profile明确替代旧身份语义并校验provenance，不修改冻结v9或借机激活它；具体文件与三面设计先由Capability owner交付再审。System当前src/scripts/contract未见producer，仅receiver与测试client存在，证据称接收方切换，不称System业务链完成。
- T-14局部取消风险：当前register handler/service未传caller boundary，PrismaMcpTransaction.runGlobal使用无caller取消的transaction request。后续同一注册切片须补授权后/provider等待中取消→零入库的回归并承接现有boundary；其余MCP业务不顺手重写。direct credential没有TTL字段，不凭空增加过期机制；测试覆盖旧OAuth拒绝与文件删除/轮换即时失效。
- 本片不新增数据模型、第二认证协议、token镜像或Root可编辑contract；需要变更wire/schema时先由owner补相应设计面和机器契约，再串行交给消费者。

### 3.2 C-2：从入口隔离走到真正删除

1. 已提交173e026承接原11文件候选，Root已确认该子集只去掉`main.ts` raw re-export/两处type倒依赖、迁6个测试import并补默认门；不把它写成最终删除。
2. 先核Nest生命周期：`src/main.ts`、`src/common/database/database.module.ts`及现Redis/worker provider。用真实`TestingModule`/应用关闭验证停止接收、worker drain、SSE取消、超时上界、池与监听释放；不新增第二bootstrap或万能Lifecycle总管。
   当前测试树尚无实际`TestingModule/createNestApplication`消费证据，静态架构测试和raw生命周期测试不替代Nest DI/路由/关闭行为。
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
| L2 C-1.3完整旅程 | 同一冻结组合的真实App浏览器登录/切tenant/登出/撤权与负控；Capability接收方独立真实fixture | 形成当前认证闭环；不扩为全产品验收 |
| L3 受影响业务组合 | 按具体旅程增加System/Capability/Storage/Billing/Scheduler/Agent worker等实际依赖，Admin/Mori仅有受影响路径时加入 | health与业务结果分别记录；不为“全部启动”盲开服务，不假定每个owner都支持匿名readyz |
| L4 用户同步测试 | Root交付已验证源码组合、无秘密的访问入口/可测范围、私有日志索引、启动/停止归属、已知缺口 | 临时smoke已退出的进程不算常驻可测环境；本轮尚未交付该状态 |

启动顺序由实际调用依赖和owner README决定，先提供方后消费者；关闭反向且只停止本任务拥有的进程。已有用户预览与共享基础设施不重启。同步环境的保留/清理策略在后续运行阶段明确，不把PID/凭据写进版本文档。

---

## 4. 执行顺序、并行写区与检查点

保持用户指定次序：**先C-1.3，再C-2/C-3，最后C-4全量验收，再A任务**。允许独立只读调查和已冻结候选审查并行；不以并行之名提前开展后继业务写入。前置例外为本任务候选门禁所需的T-06机械格式修复、T-18已复现的Node运行/生成工具链修复，以及真实native运行复现的T-17最小启动/关闭缺陷；它们不等待G1，避免验证依赖成环，也不授权提前批量迁移raw消费者。

### Chunk 1：当前方案与既有候选接收

- [x] T-01：Root完成本文/摘要/历史入口整理，独审、文档验证通过；冻结的是本轮方案，不是业务已验组合。
- [x] T-06/T-07/T-12/T-18候选接收：Root核冻结hash/diff、串行完整静态门及BFF真实schema补测；App PR #50、BFF PR #18均为独立draft，未合并main。Root精确gitlink与后续真实组合仍待，不以该切片通过替代最终合并门。
- [ ] T-04/T-13：核runner版本/source guard与真实登录Redis注入，补资源清理红测和实现、失败收据；先定向验证再真实运行。
- [ ] T-17前置子项：若T-04/T-13的真实native运行复现Nest启动/关闭/泄漏缺陷，先做最小运行保障修复与验收，不等待G1，也不扩raw测试迁移；无复现时保留风险与后继完整验收。

### Chunk 2：先关闭C-1.3

- [ ] T-05：T-17前置子项发现的阻断已解决、最小native smoke通过后，补真实四旅程与独有负控；记录owner/request/receipt关联、最终HTTP与UI状态。
- [ ] T-14：并行只读确认global_register实际producer；固定接收方最小设计/写区后切direct credential，配对验证授权/错误/零副作用/幂等。
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
| App worker | 后续获准的App固定consumer/native adapter及对应测试 | 不动BFF/IAM契约或Root任务表；当前56文件已提交，Root pin待做 |
| BFF worker | 后续按feature授予的BFF生产/测试窄切片 | 公共入口/package/lockfile单writer；原11路径加格式32/工具链21已提交，后续另授写区 |
| 独立reviewer | 只读规格/代码/证据、缺陷与门禁核验 | 不实现、不提交，不把worker退出码当Root通过 |
| IAM/Capability专项owner | 到相应阶段替换空闲worker slot，先contract再consumer | 不新增并行contract writer；不同时铺开全仓重写 |

文档轮三只读角色审计已完成。当前派工：`bff_node24_generation`完成21路径T-18候选并停写，`bff_format_gate`完成其独审；Root串行完整门通过并提交。原`native_smoke_cleanup`已退出live列表，原6文件写区交接给`native_cleanup_review_fixes`，只处理五项review问题；`global_register_gate_audit`完成T-14只读盘点后复核T-13规格。Root维护文档、Git与最终真实资源/完整门；worker禁止Git提交、服务/数据库操作和任务表写入。

---

## 5. TODO 台账（后续持续更新）

状态：`OPEN`未做；`IN_PROGRESS`正在执行；`REVIEW_PENDING`候选已有证据、待主方复验；`VERIFIED`仅该切片已验；`WAITING`依赖未满足；`GATED`后继停写。未运行、skip和设计通过都不记为功能完成。

| ID | 事项 / owner | 状态 | 依赖、下一动作与完成证据 |
| --- | --- | --- | --- |
| T-01 | 方案/问题/Goal/TODO统一；Root | VERIFIED（文档） | 三个只读角色审计；两项依赖循环已修；独审、链接/diff通过，后续状态变化继续更新 |
| T-02 | MCP denied icon零owner副作用；BFF | VERIFIED | `228e3d6`、focused42、旧基线full；最终组合继续回归 |
| T-03 | invalid-owner typed error；BFF | VERIFIED | `228e3d6`、focused24、旧基线full |
| T-04 | 资源/Node/source/schema preflight；Root | IN_PROGRESS | 三子仓已验证/推送，Root精确gitlinks已暂存且topology PASS；待Root提交后保留exact source门执行minimal native |
| T-05 | 当前native四旅程；Root+IAM/BFF/App | WAITING | T-04/T-13、已复现的T-17前置阻断及候选Root复验；最小4case与完整浏览器四旅程分列 |
| T-06 | BFF格式门；BFF | VERIFIED（候选） | Root format exit0，AST/注释等价32/32；独审确认原11候选byte不变、1068tracked符合冻结；后续改动再复验 |
| T-07 | App Public28.18消费修复；App/Root | VERIFIED（待集成） | Root Node22.23.4/pnpm11.25完整check exit0：contract452/architecture50/full6373，lint/types/build通过；56路径前后SHA一致；4260f698实现/9ba65343候选已推送App draft PR #50，Root pin待做 |
| T-08 | IAM SDK与verify；IAM | VERIFIED | `a1457be`、120files/1561pass/build；不代表native端到端 |
| T-09 | Root/各受影响owner最终串行门；Root | WAITING | G1/G2、T-06/T-07/T-12/T-13/T-16收敛；精确冻结SHA+pass/fail/skip |
| T-10 | A-01/A-02/A-07及其余A backlog；Root | GATED | G1/G2/G3全部闭合；原16任务责任和优先级保持 |
| T-11 | raw/global/剩余Repository-Service-Port；BFF | WAITING | G1后，先T-17；feature迁消费者→删旧实现→零引用/真实行为 |
| T-12 | Nest默认架构门与入口隔离；BFF/Root | VERIFIED（切片） | 173e026；Root第三轮format/check exit0、contract1344/default2343pass+2skip/build通过；两资源skip另真实PG15pass/0skip；raw最终删除仍属T-11 |
| T-13 | native smoke清理与脱敏证据；Root | REVIEW_PENDING（真实smoke） | 六路径停写双审通过；Root相关60pass/31subtests、治理1876pass/3skip/502subtests，IAM真实host62pass及verify1566pass；待当前最小native退出收据，不等于浏览器四旅程 |
| T-14 | global_register direct credential；Capability/Root | OPEN（盘点完成） | 已证receiver/测试client存在、未见第一方producer；先固定owner认证artifact及取消边界处置，再direct cutover；不新增System功能 |
| T-15 | 当前组合同步E2E可用性；Root | WAITING | 区分临时smoke与可保留测试环境；健康/受支持旅程/日志索引/回收归属齐全 |
| T-16 | Agent与原C-1删除项最终复核；Agent/Root | OPEN | `c761fad`仅focused130历史证据；当前全门及旧语义零生产引用；任务外治理问题留owner |
| T-17 | Nest shutdown/drain/pool释放；BFF | OPEN | 前置子项：native运行复现的启动/关闭/泄漏阻断先修；完整子项：G1后/T-11前补drain/SSE/worker/PG/Redis矩阵；两项均满足才关闭 |
| T-18 | BFF Node24运行/生成工具链一致；BFF/Root | VERIFIED（切片） | 173e026；21路径独审/1068tracked hash匹配；Root第三轮format/check exit0，106generated与原43路径保持，7正规生成/双检通过；两轮RED保留，CI/Docker未实跑不称通过 |

---

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
| App | `pnpm contract`、`pnpm test:architecture`、`pnpm lint`、`pnpm typecheck`、`pnpm test`、`pnpm build`，以及受影响浏览器/E2E入口 |
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
6. **下一轮默认动作**：先核本表/diff，T-04/T-13五项审修与IAM真实integration/verify已完成，三子仓独立draft PR已推送；完成Root精确pin提交→最小native，处理实测发现的T-17前置阻断。再做T-05四旅程和T-14 owner局部设计/cutover（只读盘点已完成）。G1闭合后执行T-17完整矩阵/T-11批量清理；A功能继续门控。

### 最新暂停后续接检查点

用户已明确继续。工具Goal记录仍显示paused；继续请求已撤销此前暂停指令，本轮不伪造状态切换，也不创建重叠Goal。阶段目标仍G1/G2/G3 OPEN，A门保持。

T-13五项修复已获规格/质量双审，六路径hash停写匹配；Root相关60pass/31subtests、完整治理1876pass/3skip/502subtests（exit0）。IAM真实两个host文件62pass/0skip，完整verify121files/1566pass/build通过，已推送e6a01cf与本仓draft PR #6。App/BFF原已验候选保持。三精确gitlink暂存后topology PASS；暂存前因旧pin的三项预期mismatch保留为阶段记录。当前等待Root提交后实际最小native，不把宿主测试或临时数据库隔离视为应用单库组合/浏览器四旅程。
