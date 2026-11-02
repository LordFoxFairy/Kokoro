# Task A 当前进度、问题与 C-1～C-4 闭环技术方案

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 先完成 G0 / C-1～C-4 的认证切换、旧实现删除和真实验证，再进入 A-01/A-02，随后 A-07；保留 A-03～A-16 的完整产品责任，不以清理完成代替 Task A 产品闭环。

**Architecture:** IAM 唯一拥有人类 session、active tenant 与权限；App 同源适配 → BFF Nest feature → owner API/RPC。Nest `AppModule` 是唯一运行时组合根；旧 raw server/runtime、dispatcher 和无边界 aggregate 在消费者迁移后删除。有效的事务、幂等、取消、恢复、lease/outbox 语义必须承接，不机械删除 Repository 或新增空层。

**Tech Stack:** 现有 TypeScript/NestJS/pnpm、PostgreSQL/Redis、owner generated clients、Python Root 治理；各仓 Node/Python/Go 版本以其 manifest/lockfile 为准。

**当前检查点：** I-37 SDK Bearer 自动填 Cookie 的局部回归已由本地 `2cb9864` 修复，独审和主方完整 verify / 外部 consumer 通过，未推送。I-38 内部会话传递设计仍待用户裁决，不实施引用方案、不发行 native2 或更新 Root gitlink。Goal active；G1/G2/G3 OPEN，A 功能停写。

---

## 当前执行摘要（2026-11-02，IAM owner 候选与测试价值审计）

- **Goal**：active；已确认旧预期、弱断言及 SDK 凭据隔离回归，按风险处置。未暂停或完成 Goal。
- **文档更新基线**：Root `a8a149ca`；IAM 本地 `1d9bd95` 尚未推送，Root 仍固定 `5fffe60`。正式四旅程证据仍绑定旧 Root `aec5775a` 组合，不外推 native2。
- **主方证据**：native 当前事实 15 PASS；完整 integration 48 文件 / 484 PASS；完整 verify 默认 125 文件 / 1651 PASS，格式、lint、类型、契约、SDK 与 build 成功。其后外部 consumer 两轮分别暴露旧 Billing OAuth 预期与 I-37 Cookie 污染，失败记录保留；b2f28d4/2cb9864 修复后主方完整 verify 默认 1654 PASS，clean-commit 外部 consumer 2 PASS（23.92s），542 输入未变。不是全产品或新 native2 组合验收。
- **当前动作**：I-38 三路只读盘点与 §3.6 候选方案已完成；建议 B 并明确新增 BFF 委托信任，已询问用户，未获裁决前不实施。独立于该选择的 I-37 局部修复已双审，主方 verify exit0、完整外部 consumer 2 PASS；I-36 六测试文件已在本地1d82fa2清理并双审；主方格式/lint/types、architecture10与真实SMTP/Skills/Audit三文件31通过，Skills去掉无效audit计数后单文件16重验。第二批1d9bd95四处contract结构、两项纯转发删除和两标题纠正已双审及主方定向验证；本次已识别问题完成处置，不冒全量测试审计，I-38继续待裁决。
- **TODO**：38 累计问题，18 个原 TODO 不另建任务中心；T-05/T-09 纳入 I-36 测试价值处置，G1/G2/G3 保持 OPEN。A-01/A-02/A-07 停写，每仓原独立 draft PR，不 merge main、不部署。
- **证据边界**：484/1651 是两类 IAM 套件执行计数，既非新增用例数，也非独立需求数；本轮只读抽样并非全量测试价值审计。临时三服务旅程不是全部仓库常驻同步环境。

## 0. 当前结论与唯一入口

**Task A 尚未闭环。** 最近正式浏览器证据绑定旧 Root aec5775a，native 四旅程通过；I-30/I-34与Root编排切片已双审和主方完整门。G1仍欠I-29完整native生产切换、I-31其余负控，G2/G3仍OPEN。没有常驻同步测试组合，不把四旅程、工程门或cleanup通过扩张成全产品完成。

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
| Root | `a8a149ca`（本轮文档编辑基线；正式实跑为 `aec5775a`） | App fdbb49f1/BFF105024d/IAM5fffe60精确pin；driver c142c49c，Root2005治理/3skip；正式4/4及cleanup/credential scan通过 |
| App | `fdbb49f17bfbb09684cd5c3cfaea1c1678306697` | 原PR50；I-34最终复验不可用不误报401，Root完整452contract/50architecture/6411default、0skip，lint/types/build与双审通过；当前Root正式4/4通过；原组件门范围不扩大 |
| BFF | `105024d33611dfaccc9a072d04f0864d03015ef9` | 原PR18；源码f81f271正规native消费，Root contract1345/default2350pass+2skip/format/lint/types/build；本HEAD仅I-29三面D0通过，不冒native2实现 |
| IAM | Root pin / PR6 `5fffe60`；本地候选 `1d9bd95` | native2 owner cc3fbaf1；Billing 旧测试 b2f28d4、SDK Bearer 隔离 2cb9864。主方 verify 默认1654与外部consumer2通过；原server integration484绑定cc3源码；1d82fa2仅测试清理，主方architecture10/真实3文件31及Skills最终16通过，不冒完整默认套件重跑。未推送、未配对，I-38待裁决 |
| Agent | `c761fad3dba2b56cd7fe4da7683a9ac2f208243f` | C-1.2 清理已提交；最终完整 owner gate 仍待 |
| Capability（物理路径仍为 kokoro-capability） | `f515e22596357e2dd6c05cfa47a1c2f54b99f202` | receiver-only源码及真实PG已验，独立draft PR13依赖PR12；远端基线2ad5c9e未集成且PR冲突，保留原已验组合不覆盖新增提交，最终合并门OPEN |
| 其他组合成员 | 当前 Root gitlinks | 仅按受影响边界纳入验证；本轮未启动、未刷新全套运行健康状态 |

### 0.2 进度与验证事实

| 阶段 | 已有成果 | 当前结论 / 缺口 |
| --- | --- | --- |
| G0 | ADR-036 Accepted；2026-10-31 reviewer 放行；native artifact 1.0.0 / SHA256 `5cf59df4b7bd9853edfd2eabb31afc236c0ec0db371f9737706fc129484fd83f` 已固定 | 设计门已通过；新的具体写区仍须按本文局部设计确认，不把设计批准当运行验收 |
| C-1.1 / C-1.2 | BFF schema-evolution 旧入口、App hash/legacy 展示分支、Agent legacy_failed 推断等已删除；保留 canonical localDraft / journal / replay | 已提交切片；最终零消费者复核及 App/BFF/Agent 完整门待 C-4 |
| C-1.3 | native准入、冷登录及退出HTTP已真实验证；Capability direct receiver与退休配置已交付 | 正式四旅程/私有UI退休已验；IAM owner action/事务保障已在本地 cc3fbaf1 实现，尚未正式消费；BFF 生产 Bearer 回退未删除，I-31其余负控及新base整合仍开放 |
| C-2 | Nest 生产图已移除 LegacyRoutes；named feature 路由接管；generic configured-owner proxy tail 已删除 | raw server/runtime 与测试消费者仍存；生产 Nest shutdown 语义待核；入口隔离候选不等于删除完成 |
| C-3 | BffBusinessStore / BffApplicationServices / PostgresBffRepositories 旧 aggregate 已清理多片；global ports 仅留 idempotency contract | raw composition / owner-resource 聚合工厂和 feature disposition 仍待最终审计，不以类名删除代替边界证明 |
| C-4 | App e1be/BFF4d6/IAM1ee8/Capabilityf515各有对应工程门；Root治理/真实限定链路有证据 | Agent全门、最新base整合、全受影响真实I/O及最终组合E2E/常驻同步环境未齐；678skip不算通过 |

证据严格分层：
- **已提交旧基线**：BFF `228e3d6` 默认测试 2298 total / 2296 pass / 2 skip / 0 fail；该时默认入口未纳入两套 Nest 架构测试。IAM `a1457be` verify 为 120 files / 1561 pass / build PASS。Root 上次 topology PASS，治理 1846 pass / 3 skip / 502 subtests。这些不是当前 dirty tree 全绿证明。
- **App 历史T-07基线9ba，Root复验结果（最新基线见§0.1）**：Node 22.23.4；contract 48 files / 452 pass、architecture 50 pass、完整 test 354 files / 6373 pass / 0 skip；typecheck/lint/build/diff-check 通过。旧基线50个契约失败已收敛，Root完整check exit0且56路径前后SHA一致；已提交4260f698、集成origin/main空树merge为9ba65343并推送App draft PR #50。Root当时已pin；该历史阶段真实四旅程仍待，最新正式4/4见§0.1。
- **BFF 历史173e026切片，Root复验结果（最新基线见§0.1）**：Node24.20.0下format/check exit0；contract1344pass，默认2343pass/0fail/2skip，lint/types/build通过。两项原数据库条件skip另补整文件真实PG schema15pass/0skip，覆盖共存/回滚与R237。原architecture73/focused123为辅助证据；未完成完整业务integration/当前native链路，字面依赖扫描不称完整AST图。
- **Root runner历史阶段（不是最新验收结论）**：最初close函数缺失1pass/2fail，后续独审发现五项清理/收据缺陷，均已在T-13修复并以Root60定向/IAM真实62及成功/失败退出验证。现Root六文件T-14配套候选另有154定向、完整治理1879pass/3skip/506subtests；真实Capability receiver后续已验（f515，见§0.1）；该历史阶段完整四浏览器旅程仍未验，最新正式4/4见§0.1。
- **历史真实链路**：旧组合有 IAM 集成 12 pass、IAM→BFF 7 case、HTTPS native smoke 4 case。保留其对应 SHA/范围；不外推到当前 Nest/候选组合，也不将历史 OIDC 验证作为目标 native 链路。

---

### 0.3 测试价值审计与处置（I-36，2026-11-02）

范围：IAM `cc3fbaf1`，两路只读 Agent 分别抽查 integration/consumer 与 unit/architecture/smoke，Root 复核具体源码并抽查 contract。没有完成全部 484/1651 用例价值审计，不设置数量削减目标。下面复用 T-05/T-09，不新增任务中心。

| 处置 | 当前证据与独有风险 | 状态 / 下一动作 |
| --- | --- | --- |
| 重写 SDK consumer 旧凭据 | `test/fixtures/sdk-consumer/src/real-consumer.ts` 用 tenant OAuth 调 Billing；现 `billing-authorization-http.test.ts` 明确该凭据应 401。打包、外部安装/编译/真实调用仍有独有价值 | VERIFIED（此测试切片）：b2f28d4 修旧凭据，2cb9864 修独立 SDK 回归后主方完整 consumer 2 PASS；其余 I-36 处置不据此关闭 |
| 合并 SMTP 正例 | 两个邀请正例原本重复收件人/subject/path，第二例独有 origin/唯一query ID/PG状态 | VERIFIED（1d82fa2）：独有断言已并入真实HTTP正例并绑定响应invitation ID，删除直接调用重复例；拒收/pending、注册验证、magic-link、TLS原例保持。主方原SMTP整文件真实通过 |
| 替换 Skills 源码顺序断言 | 全文件indexOf可能因-1假通过且不绑定路由 | VERIFIED（1d82fa2）：删除弱位置比较；保重复key/JSON/权限/413，补原始非法UTF8字节400/no-store/request ID。正常成功也不写audit，新增计数断言无独有价值已删除；最终Skills真实16通过，不宣称证明service未调用或具体解析分支 |
| 删除 Audit 机械清单/重复字符串检查 | 精确query/maintenance文件清单锁布局，tenant源码包含不证明隔离，原HTTP宽松schema会剥未知字段 | VERIFIED（本片1d82fa2）：删两文件清单与tenant字符串检查，保Nest/schedule边界；真实两页strict schema+exact IDs/tenant/sentinel/keyset承接wire。details/resultSlot两条原弱检查暂保留，不把wire脱敏说成SQL最小读取保证，不新增未有设计要求的DB读取门 |
| 强化 contract 结构断言 | `session-authorization.openapi.test.ts` 等 stringify 后 contains 字段名，不证明类型、必填或所在位置 | VERIFIED（1d9bd95）：四处改结构断言，properties/required按集合，保closed/type/nullable与绑定，去掉重复request-id contains。既有SwaggerParser仅本地dereference，容许等价$ref；主方6文件39通过，内存等价变换4通过/22名称过滤，不复制整Schema/日期regex或新增框架 |
| 复核转发用例/重复 fixture 与命名 | native unit 的部分纯 mock 转发重复，guard 装配重复；MCP 的 “native signed user token” 实为 OAuth，kernel “every” 实仅六入口 | VERIFIED（1d9bd95，本片）：删Skills/publisher两项纯mock转发，由原真实guard→事务复读矩阵承接，主方native15通过；保Account/MCP政策。纠正OAuth/代表性入口标题。guard重复fixture保留，不因风格新增通用框架 |
| 保留真正跨层证据 | native guard 后撤权→事务复读零写；provider refresh 竞态；profile CAS/审计回滚；真实 socket 断连与已提交未知结果；unit 的确定性时窗 | RETAIN：不同入口/层级有独有风险，非按同名判重复；mock 提交不描述成真实数据库提交 |

本次抽样已识别项已完成保留/合并/删除/重写处置，实际删改有风险承接、双审与主方定向验证。I-36仅此有界发现集闭合；全部484/1651用例价值未逐项审计，两条Audit敏感列源码弱检查仍明确保留，不宣称无冗余或整体Task A完成。

## 1. 已知问题全量表（本次 Task A 审计范围）

这里只把本次可核验的问题标为当前事实；历史或任务外问题保留归属，未核验不等于无问题。

| ID | 问题 / 当前证据 | 处理与关闭条件 | TODO |
| --- | --- | --- | --- |
| I-01 | 原精确源码/dirty/gitlink阻断已解决：Root1e6精确App e1be/BFF4d6/IAMe6，Capability f515另已pin | 已验组合source门保持；后续IAM fixture或base整合新候选必须重新停写/提交/精确pin，不绕过门禁 | T-04/T-13/T-05/T-09 |
| I-02 | MCP denied icon mutation 曾在拒绝后调用 Platform | `228e3d6` 已补 manage admission，focused42与基线 full已证；最终组合继续保护零副作用 | T-02（已验证切片） |
| I-03 | Skill installation Chat invalid-owner error 曾被 fixture 缺失掩盖 | `228e3d6` 补最小 receipt seam，focused24与基线 full已证；保持 typed error，不放宽断言 | T-03（已验证切片） |
| I-04 | BFF原32文件格式warnings已机械修复；Root完整格式门通过 | 重跑确切清单，仅处理本任务受影响文件；不做无关全仓格式化；门未绿前 C-4 保持 OPEN | T-06 |
| I-05 | App Public28.18 pin/generator/历史逆证已正规修复并经Root完整门，已提交独立draft PR | 原问题已按T-07切片关闭：原件/旧父链独审、Root完整门与精确集成已验；后继组合继续保护，不手改快照或历史hash | T-07 |
| I-06 | IAM SDK drift | `a1457be` 已正规生成并 verify；更改消费者后仍核 fixed artifact，不引入手写第二契约 | T-08（已验证切片） |
| I-07 | 全部 owner 的受影响全门、真实 I/O、当前 E2E 收据未齐 | 按停写组合串行验收，逐项记录 fail/skip；不把 health/static/fixture 当产品闭环 | T-09/T-15/T-16 |
| I-08 | A 任务产品缺口尚在，容易被清理完成误标关闭 | A-01/A-02/A-07 保持门控；A-03～A-16 保留完整 backlog；不新增本轮产品代码 | T-10 |
| I-09 | raw server/runtime、composition 与聚合 fixture 仍在 | 56 test files / 148 direct calls；helper18 files / 42 calls；composition3 files / 4 calls；owner-resource9 suites / 102 calls，集合有重叠不可相加。按 feature 迁移，再零消费者删除 | T-11 |
| I-10 | 默认 test/check 曾遗漏 Nest 架构门 | 候选已在 test 与 test:architecture 各接两套 Nest suites 一次；主方复验默认入口；静态扫描不冒充完整依赖图 | T-12 |
| I-11 | smoke teardown 吞 process/proxy 异常，缺 IAM 前后 inventory；失败日志在临时目录退出时消失 | 所有自有资源尽力回收、失败可见、未停进程不删依赖；增加脱敏 stage/cleanup 收据和泄漏负控；红测保留至真实修复 | T-13 |
| I-12 | Capability `global_register` 原用 IAM workload introspection且曾被TODO遗漏；f515接收方切片已替换并验证 | policy caller为kokoro-system；System当前未见实际producer，已验范围仅direct credential receiver。最新base整合归T-09，无需求不新增System注册功能 | T-14 |
| I-13 | Nest 生产只 enableShutdownHooks；旧 installBffSignalHandlers 仅被测试消费，数据库 close 尚无明确 Nest hook 接线 | 验证并补齐 readiness关闭→worker drain/取消→连接释放的有界生命周期；实际 Nest app.close/SIGTERM 与真实 PG/Redis 证明后才删 raw shutdown | T-17 |
| I-14 | 新旧计划/问题台账/日期混用，App旧失败、G0待批准、资源缺失等曾覆盖当前态 | 本计划唯一当前台账；旧文件加历史/导航标记；候选/已提交/Root复验分列，状态变化再同步摘要 | T-01 |
| I-15 | 单数据库 owner schema 组合、Redis namespace、自有 fixture 回收尚无当前共同证据 | fixture 临时库只是隔离，不证明应用单库组合；逐 owner 核 installer/URL/schema，禁止跨 owner SQL/共享 reset | T-04/T-09/T-15 |
| I-16 | Agent 最终全门及全局规范审计未刷新；旧问题台账记录过224条任务外 violation | 本轮不把历史计数当当前结果；C-4核受影响项，任务外问题保留 owner/backlog，不放宽适用门禁或宣称全仓无问题 | T-09/T-16 |
| I-17 | 原runner遗漏必需的Web Redis输入已修复并提交，实际无cookie注入冷登录已通过 | 此配置不是退休项；隔离注入/归属/回收与冷登录证据已验。后续永久四旅程保留该回归，不以默认preview替代 | T-04/T-13/T-05 |
| I-18 | 原BFF engines与pin/生成链/CI/Docker存在Node24/22漂移；173e026已统一并通过Root当前完整静态门 | 保留两轮RED与真实修复证据；七条正规生成/双检及当前完整门通过，106generated不变；未实跑CI/Docker，不以配置对齐冒称容器验收 | T-18 |
| I-19 | 原Nest启动失败已解决：BFF4d6修复五处DI可见性，Root535最小native成功；完整关闭矩阵仍缺证 | 已加真实生产容器compile/关键token单实例回归；后续验证drain/SSE/worker/PG/Redis，不重复领取旧启动修复 | T-17 |
| I-20 | 本计划曾要求同App正向双tenant切换，但App/BFF/IAM当前三面设计与G0都明确固定Product tenant；属于台账错误 | 已按有效裁决纠正T-05；用异tenant会话拒绝/固定域恢复验证隔离，禁止删BFF授权门或新增TaskB切换器 | T-01/T-05 |
| I-21 | 真实冷登录原表单303后session/projects401，App缺固定tenant set-active，fixture预设会话曾掩盖 | App e1be及Root旧组合已完成真实冷登录/退出HTTP验证；此原缺陷闭合，不等于当前完整四旅程通过 | T-05 |
| I-22 | LocalPlatformRuntime先生成单projection文件，随后聚合多surface凭据以同名O_EXCL创建，真实文件装配抛FileExistsError | Root候选已改独立聚合文件名，真实临时目录RED→GREEN并保持0600/回收；独审及Root154定向通过，已随c08c提交并配对f515；此文件装配缺陷闭合，同步环境仍待T-15 | T-14/T-15 |
| I-23 | Capability现部分R317/R336 opt-in测试与release workflow仍有此前OAuth/旧execution配置欠账 | 保留原触发开关与业务断言，标清既存/本片新增；本片只迁退休resource-server消费者并真实验证global receiver，未触及的旧catalog/CI链不冒称已可运行 | T-14/T-16 |
| I-24 | 已修复退出两层缺陷：显式POST body与owner JSON媒体类型/空对象规范化 | App e1be完整门6407/0skip及Root真实退出200、cookie清除、项目/旧cookie均401；I-24在此HTTP范围闭合，完整T-05仍OPEN | T-05 |
| I-25 | Capability原PR12基线由44fcc前进至2ad5c9e，4提交/73路径含契约和Schema；本Task A PR13与其存在实际合并冲突 | 保留双方提交，不force、不整树择一；在独立集成区审边界/冲突后重新完整门和真实receiver，再更新精确Root组合。当前仅已验f515候选 | T-09/T-16 |
| I-26 | Root dd447正式四旅程cold_login已303并到/app，但账户入口不可见而超时；诊断14次HMR WebSocket Upgrade均404，代理缺101双向转发 | 已交付实现与原断言保持；Root aec5775a/run2a960804正式4/4通过，本项在真实旅程范围闭合。对应RED/修复/组件门与历史失败见实施证据，不重复领取 | T-05/T-13 |
| I-27 | Root50ac正式旅程已过cold_login UI/profile，进入异tenant旅程后profileBarrier的route.fetch在TLS握手前失败；Playwright Node请求不继承Chromium域名/443映射，私有同请求loopback诊断200 | 已交付实现与原断言保持；Root aec5775a/run2a960804正式4/4通过，本项在真实旅程范围闭合。对应RED/修复/组件门与历史失败见实施证据，不重复领取 | T-05 |
| I-28 | bad205正式异tenant旅程已取得真实profile barrier，但driver错误要求projects401；实际session401/native_session_required、projects403/product_tenant_forbidden，符合固定tenant隔离实现 | 已交付实现与原断言保持；Root aec5775a/run2a960804正式4/4通过，本项在真实旅程范围闭合。对应RED/修复/组件门与历史失败见实施证据，不重复领取 | T-05 |
| I-29 | BFF4d6生产authorizeUserRequest在缺native配置/verifyNative时回退Bearer→admission.verify；Nest真实feature可达，不只是raw/test残留 | G1前按owner处置旧浏览器准入消费者，缺配置fail-closed；逐项承接ownerSessionAuth/authorizeSkillAction有效权限，不批量误删公共skill.list或IAM公开OAuth | T-05 |
| I-30 | 原BFF漏生成native operation且自写response，已由f81f271正规生成24 operations并删除重复schema，unknown error fail-closed | 本片已闭合：双审、Root完整门1345contract/2350default（2skip）；现固定原件不升级。I-29后继artifact再正式固定/生成，I-30不代表授权闭环 | T-05 |
| I-31 | G1负控证据不齐：BFF默认test遗漏native-session-admission文件已由I-30补齐；IAM direct-service矩阵不含session_admission；重复登出/native IAM不可用/native mutation零写未有当前完整映射 | 复用既有测试承接具体风险并纳入正确默认入口；登记case/SHA/result/零副作用，缺项定向补证，不拿sibling purpose或Bearer/raw证据代替native | T-05/T-12 |
| I-32 | cc405正式run在focusProbe等待session超时；锁定Playwright默认启用focus emulation，抑制bringToFront真实事件。私有禁用两页override后trusted事件/session401与前三旅程顺序走通 | 已交付实现与原断言保持；Root aec5775a/run2a960804正式4/4通过，本项在真实旅程范围闭合。对应RED/修复/组件门与历史失败见实施证据，不重复领取 | T-05 |
| I-33 | 同请求首次/me429→App503已证，场景累计负载触及既有共享配额；Root c142c49c仅在独立场景边界尊重窗口 | Root2005治理/3skip与双审；aec5775a正式4/4通过，本编排缺陷闭合。未抬配额/缓存/重试，不冒产品容量证明 | T-05 |
| I-34 | App最终鲜验原catch成null误判401，已由fdbb49f1删除吞错，依赖不可用沿503且无资料泄漏 | 本局部缺陷已闭合：先3项真实loopback RED，Root App完整6411/0skip、contract452/architecture50/lint/types/build，1494输入稳定且双审CLEAR；当前aec5775a正式4/4已通过，整体G1另验 | T-05/T-12 |

| I-35 | IAM 完整 integration 原 15 失败：schema digest 非 id 主键、Session 物理删除旧预期、CLI 资源身份缺口 | 已修旧 oracle 并保留数据保全/撤销断言；CLI 仅显式采用同管理连接实际 role，不改产品/权限。主方原整套 48 文件 / 484 PASS，无 skip；纳入本地 cc3fbaf1，不代表消费者或 G1 完成 | T-05/T-09 |
| I-36 | 测试价值抽样发现 SDK Billing 旧成功路径、SMTP 重复正例、源码位置/文件清单耦合与弱契约断言 | §0.3 有界发现集已处置：consumer、1d82fa2首批及1d9bd95结构/转发/命名均双审、主方定向通过；保留项注明风险，不宣称全部套件无冗余，不按数量减测，不冒I-38批准或全产品完成 | T-05/T-09 |
| I-37 | SDK 在新增双认证 scheme 后把 bearerToken 同时填入 Cookie，OAuth 请求误入 native 并 503 | 局部已验：2cb9864 仅 transport/既有 SDK 测试；HTTP Bearer-only scheme callback，Basic/默认/调用覆盖保持，generated/guard/contract不改。双审CLEAR，主方verify默认1654/consumer2 PASS且542输入未变；未推送，不决定I-38 | T-05/T-09 |
| I-38 | 用户质疑内部 Cookie 透传与 SDK/客户端层次的必要性、复杂度和维护成本 | 重新打开受影响认证传递设计门：区分服务身份与人类会话证明，盘点 browser→Web→BFF→IAM 各跳及真实 SDK 消费者；不得仅改 header 名或另造 token/SDK 层。IAM writer 已停写，无 live 验收；不继续 native2 消费/发行。其余独立工作与完整 Goal 保留 | T-01/T-05 |

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
- `run_web_native_session_smoke.py`的**默认模式仍只是三服务最小HTTP smoke**：fixture给现成native cookie→`/api/auth/session`→`/api/session/projects`→fixture直接IAM signout后401，加日志检查共4case。不是浏览器登录，不覆盖tenant切换、App登出、独立revocation或全部owner。 显式`--browser-journeys`已在d309加入永久四旅程，dd447加入脱敏失败位置；最早cold_login失败见I-26，当前正式运行已进入第四旅程并由I-33续接；不把模式已实现当验收通过。
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

### 3.6 I-38：认证边界与客户端层次重新收敛（待用户裁决，不是已批准替代方案）

**审阅状态。** IAM/BFF 两名独立只读 reviewer 已确认本节与源码边界一致（CLEAR）；这不是用户批准。主方 diff/本地链接/三 owner 输入未变验证通过。

**触发与范围。** 用户质疑内部 Cookie 传播、SDK 层次和维护成本。原 G0 的 owner/事务/权限原则继续有效；只重新打开 C-1.3 身份传递设计，不将质疑解释成删除在线授权，也不继续按原 D0 扩散 native2。三 owner 只读调查由 Root 收敛为本节，候选尚未发行。独立 I-37 修复后续已在本地2cb9864双审及主方verify/consumer通过；它修 SDK 错误，不决定本节架构方案。

#### 已核事实：不是所有内部调用都需要 Cookie

| 跳 / 范围 | 当前材料与验证 | 结论 |
| --- | --- | --- |
| Browser → Web | 浏览器 issuer Cookie；Web 同源/Origin、输入、CSRF 边界 | 浏览器会话边界应保留，不因内部认证简化而删除 |
| Web → BFF | allowlisted issuer Cookie、配置的 Origin、Web 专用服务 envelope；BFF 校服务身份与固定 Product tenant | Cookie 尚被 BFF 用作送往 IAM 的人类会话材料，不是 Web 服务身份 |
| BFF → IAM 专用 admission | 专用 `session_admission` 服务凭据 + Cookie + Origin；IAM Better Auth 核会话，再查当前 Session/User/active tenant/member | 机器调用者与人类会话分别验证；返回已有真实 `session_id`，不是新发可缓存 grant |
| BFF → IAM 业务 | 原 D0 的 19 个业务 HTTP 操作（Account/Team/Skills/MCP/publisher/OpenApp）再传同类 Cookie proof；业务事务仍复核事实和原政策 | 用户质疑的主要扩散点；不是仅登录端点带 Cookie |
| BFF → 其他 owner | 各接收方直接服务凭据与受信业务上下文；本 owner 验用途/tenant/资源 | 不应传播 IAM Cookie；资金/Run/execution proof 是独立业务授权，不随本片删除 |

当前 BFF `SessionAdmissionClient` 解析到 IAM 回包后只留下 user/tenant/admin，丢弃真实 `session_id`。App `NativeSessionClaims` 有 `id/issuerSessionId = "native-session"`、空 access、固定 generation 等过渡形状；它们不是可发给 IAM 的 Session 引用。若选择引用方案，仅 BFF 请求内保存 IAM 返回的真实 ID，不默认新增 Web `/me` 字段或把 ID 暴露给浏览器。App 的旧形状另按实际消费者删减；原末端鲜验和私有 UI 退休风险须先承接。

源码入口：
- [Web native 入口](../../../apps/kokoro-app/src/lib/server/product-bff.ts)、[profile 请求链](../../../apps/kokoro-app/src/lib/server/account-profile.ts)。
- [BFF admission](../../../apps/kokoro-bff/src/auth/user-admission.ts)、[admission client](../../../apps/kokoro-bff/src/auth/session-admission.client.ts)、[Web 服务身份](../../../apps/kokoro-bff/src/auth/browser-service-credential.policy.ts)。
- [IAM 会话验证](../../../apps/kokoro-iam/src/modules/auth/native-session/native-session-admission.service.ts)、[IAM 当前事实](../../../apps/kokoro-iam/src/modules/auth/native-session/native-session-admission.repository.ts)。

#### SDK 与生成客户端：按真实消费者收敛，不按名称删包

本轮扫描 `.gitmodules` 登记仓的 tracked 源码/manifest：BFF 无 `@kokoro/iam-client` 依赖，使用固定 vendor OpenAPI 生成本仓客户端并有具名适配；IAM SDK 有两个已知生产消费仓：

- [Billing](../../../apps/kokoro-billing/src/modules/metering/iam-billing-authorization.client.ts)：固定 0.17，以 direct-service 凭据调用资金执行意图验证，不负责浏览器会话。
- [Capability](../../../apps/kokoro-capability/src/infrastructure/iam/iam.providers.ts)：固定 0.18，以 direct-service 凭据调用现执行授权；保 Run/proof/请求绑定。
- IAM 的外部 SDK consumer fixture 是包交付验证，不是第三个产品消费者；仓外未知消费者未调查，不推断全世界零依赖。

因此不把 BFF 迁入另一个手写 SDK，也不删除 Billing/Capability 正在使用的包。保留唯一 owner contract 与生成来源；BFF 具名适配中的总期限、取消、响应大小、禁止 redirect/Set-Cookie、主体绑定和错误映射有独有职责。Team、SessionAdmissionTransport 中与 generated operation 重复的路径/body 构造是候选删除项，先选唯一请求构造来源再迁，不新造通用 Client/Port/DTO 层。I-37 的通用字符串 auth 自动填 Cookie 必须独立消除，不能把错误当需求。

#### 两个可行方向与推荐

| | A：维持 Cookie proof 到每次 IAM 业务调用 | B：Cookie 限于专用准入，业务传受信 Session 引用 |
| --- | --- | --- |
| 人类身份来源 | 每次由 IAM 验原生 Cookie | 首次由 IAM 验 Cookie；BFF 保留该次返回的真实 Session 引用 |
| 后续内部请求 | BFF 服务凭据 + Cookie + Origin | 受限 BFF 服务凭据 + Session ID 引用；不接受自报权限/管理员值，user 与 active tenant 由 IAM 当前 Session 派生 |
| IAM 当前授权 | 原业务事务复读 Session/成员/角色/资格 | 同样保留；不是信任一次准入快照，也不缓存 allowed |
| 简化效果 | 不新增信任决定，但浏览器协议继续进入业务参数链 | Cookie 不再穿过业务 helper/分页/owner adapter；可删除重复 Cookie/Origin 搬运，仍保服务身份与业务当前校验 |
| 明确代价 | 分发面与认证分流复杂度较高 | BFF 成为获准代言会话的受信调用方；获该服务身份且知道有效 Session ID 的调用者可尝试以该会话执行 |
| 凭据与状态 | 现有 Cookie + 服务凭据 | 不新增 JWT、token exchange、会话票据、认证缓存或持久 admission 表；Session ID 不是秘密凭据 |

**推荐 B，但须明确接受其 BFF 委托信任边界。** IAM 可证明 Session 当前有效、服务用途/tenant/目标资源匹配及权限成立；在不新增签名证明或 admission 记录的前提下，IAM不能独立证明“这个 ID 刚由本请求通过 Cookie 得到”。不能把这一差别说成等价优化。若要求 IAM 每次独立验证调用者持有会话凭据，则应选 A；仅换 Header 名并未消除凭据传播，另造短期票据则增加了用户明确质疑的体系复杂度，本片不采用。

#### B 的最小边界（仅设计候选）

1. BFF 只从 IAM admission 成功回包构造请求内会话引用，不从浏览器 body/header、Web 占位 claims 或全局 cache 恢复。失败时无业务调用；异 Product tenant 保 403，不误注销。
2. IAM 仅允许明确的 BFF caller/用途/操作闭集使用引用，鲜读接收方凭据并限制 tenant；普通服务身份、公共 OAuth/API Key 和执行/资金入口不自动获得代言权。具体 wire/schema 在裁决后由 IAM 单一 owner 定义，当前不先造新 header/DTO。
3. IAM 从 Session 派生 user 与 active tenant，校当前 expiry/tombstone/User/member、固定 tenant 和目标资源。Account/Team 保原事务重核；Skills/MCP/operator/OpenApp 保各自原政策，不能由 BFF 布尔值代替。跨页/final recheck、超时/取消/未知提交保障保留。
4. Cookie 与引用不成为两个第一方 fallback。owner 正式发行后固定配对迁消费者，删除旧第一方模式探测、空 token、重复 Bearer 提取和已无消费者的 Cookie 搬运；公开 OAuth/第三方身份独立保留。
5. App 同源/CSRF/logout/真实登录保持。`/me → business → /me` 等重复校验按各自风险核对：入口准入、owner 事务授权、交付前鲜验不是同一检查；只有风险已在正确边界承接时才删，不能为了少请求丢掉撤权或私有响应退休。

#### TODO / 验收与未决点

- [x] Root 与三只读角色盘点调用链、SDK 实际消费者及新增信任差别；源码入口见上文，未运行服务或改 owner 生产代码。
- [ ] **T-01 / I-38：用户裁决 A 或 B 的信任边界。** 这是当前唯一新架构选择；原 Goal、A-01～A-16 和 G1/G2/G3 不缩减。
- [ ] 裁决后更新 IAM/BFF/App 受影响三面设计；IAM 定 wire/operation/error，再生成并固定消费者。无新增数据模型就不造空 Schema，不以 Root 文字代替 owner 机器合同。
- [ ] T-05：沿选定方案迁移全业务链并同步删除旧路径；单 writer、各仓原独立 PR、不 merge main。未配对前不更新 Root IAM gitlink。
- [ ] T-05/T-09：具名验证服务凭据错用途、浏览器伪造引用、跨 tenant、Session 撤销/切换、guard 后状态变化、业务零写、分页/final recheck，以及公开 OAuth/资金/执行不误伤；B 额外验证 Cookie 不出业务传输、只使用受信回包引用。测试只增独有证据，不建组合爆炸矩阵。
- [ ] 主方停写验证、独立审查与精确组合四旅程后关闭局部设计实施门；C-2/C-3 生命周期和删除、C-4 全量门/同步环境仍按原依赖推进。

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
| App worker | 后续获准的App固定consumer/native adapter及对应测试 | 不动BFF/IAM契约或Root任务表；原56文件已提交并pin；冷登录/退出修复已随e1be提交并通过Root对应门；当前不保留待验收写区 |
| BFF worker | 后续按feature授予的BFF生产/测试窄切片 | 公共入口/package/lockfile单writer；原11路径加格式32/工具链21已提交，后续另授写区 |
| 独立reviewer | 只读规格/代码/证据、缺陷与门禁核验 | 不实现、不提交，不把worker退出码当Root通过 |
| IAM/Capability专项owner | 到相应阶段替换空闲worker slot，先contract再consumer | 不新增并行contract writer；不同时铺开全仓重写 |

2026-11-02当前交接：I-33正式四旅程已交付，不再领取。`iam_i29_owner_impl`是IAM唯一writer，基线5fffe60，实施native2、显式native proof及原业务事务复核、四operation和正规0.19 artifact；不改Schema/依赖、不接真实资源。`bff_i29_consumer_cut`已交只读生产消费者清单，继续只读核量原A；`iam_i29_test_acceptance`已交真实PG/HTTP负控矩阵。Root独占任务表/Git/资源，候选停写后独审和重跑门禁，正式owner artifact固定后再启动BFF写入。

---

## 5. TODO 台账（后续持续更新）

状态：`OPEN`未做；`IN_PROGRESS`已开工尚未闭环，不代表当前有运行worker（实时执行另见当前交接）；`REVIEW_PENDING`候选已有证据、待主方复验；`VERIFIED`仅该切片已验；`WAITING`依赖未满足；`GATED`后继停写。未运行、skip和设计通过都不记为功能完成。

| ID | 事项 / owner | 状态 | 依赖、下一动作与完成证据 |
| --- | --- | --- | --- |
| T-01 | 方案/问题/Goal/TODO统一；Root | IN_PROGRESS（I-38 局部设计重开） | 原统一文档切片已验；当前 §3.6 已核调用链/真实 SDK 消费者与两种信任模型，待裁决后更新 owner 契约，不以旧 G0 放行新设计 |
| T-02 | MCP denied icon零owner副作用；BFF | VERIFIED | `228e3d6`、focused42、旧基线full；最终组合继续回归 |
| T-03 | invalid-owner typed error；BFF | VERIFIED | `228e3d6`、focused24、旧基线full |
| T-04 | 资源/Node/source/schema preflight；Root | VERIFIED（当前原生组合前置） | aec5775a正式run三owner clean/gitlink配对、实际Node符合；隔离fixture正常建立/回收。不外推所有owner schema或常驻运行；后继新候选重新配对 |
| T-05 | 当前 native 四旅程与生产切换；Root+IAM/BFF/App | IN_PROGRESS | 旧组合四旅程已验；IAM本地2cb9864修I-37后verify/外部consumer通过，未推送。I-38局部设计待用户裁决；I-36抽样发现已处置并定向验证，非全量测试审计，BFF全部消费/回退删除、I-31负控仍待，不关闭G1 |
| T-06 | BFF格式门；BFF | VERIFIED（候选） | Root format exit0，AST/注释等价32/32；独审确认原11候选byte不变、1068tracked符合冻结；后续改动再复验 |
| T-07 | App Public28.18消费修复；App/Root | VERIFIED（消费切片） | App fdbb49f1主方完整contract452/architecture50/default6411、0skip及lint/types/build；当前正式native4/4。I-29后继owner版本另按影响固定消费，不将此项当全产品验收 |
| T-08 | IAM SDK与verify；IAM | VERIFIED（1ee8已验切片，非I-29候选） | IAM1ee8d156 / 原PR6已推送；Root verify121files/1566pass/build，真实两host66pass/0skip；Root d309已接收新pin，不代表跨仓native端到端 |
| T-09 | Root/各受影响owner最终串行门；Root | WAITING | G1/G2、T-06/T-07/T-12/T-13/T-16收敛；精确冻结SHA+pass/fail/skip |
| T-10 | A-01/A-02/A-07及其余A backlog；Root | GATED | G1/G2/G3全部闭合；原16任务责任和优先级保持 |
| T-11 | raw/global/剩余Repository-Service-Port；BFF | WAITING | G1后，先T-17；feature迁消费者→删旧实现→零引用/真实行为 |
| T-12 | Nest默认架构门与入口隔离；BFF/Root | VERIFIED（切片） | 173e026；Root第三轮format/check exit0、contract1344/default2343pass+2skip/build通过；两资源skip另真实PG15pass/0skip；此项只覆盖Nest架构默认门，native默认测试遗漏归T-05/I-31；raw最终删除仍属T-11 |
| T-13 | native smoke清理与脱敏证据；Root | VERIFIED（隔离smoke/browser清理） | 既有成功/失败回收证据保留；aec5775a正式4/4收据cleanup PASS/quiescent/无保留文件、credential scan PASS。不替代生产Nest生命周期或常驻同步环境 |
| T-14 | global_register direct credential；Capability/Root | VERIFIED（接收方切片） | Capability f515e225 / 独立draft PR13，Root最终format/lint/verify/Prisma/build全0（3051pass/678skip）；真实receiver1pass，Root配套六文件154定向/1879治理。原PR12新增基线导致PR13冲突，后继整合归T-09，不能合并或称全组合完成 |
| T-15 | 当前组合同步E2E可用性；Root | WAITING | 区分临时smoke与可保留测试环境；健康/受支持旅程/日志索引/回收归属齐全 |
| T-16 | Agent与原C-1删除项最终复核；Agent/Root | OPEN | `c761fad`仅focused130历史证据；当前全门及旧语义零生产引用；任务外治理问题留owner |
| T-17 | Nest启动/shutdown/drain/pool释放；BFF | IN_PROGRESS（前置已开工；完整生命周期当前等待G1） | 前置已验：BFF4d6d17b五DI修复/真实容器回归、Root完整check2344pass+2skip，Root535e7071 minimal native4pass/cleanup PASS；完整drain/SSE/worker/PG/Redis矩阵仍在G1后、T-11删除前 |
| T-18 | BFF Node24运行/生成工具链一致；BFF/Root | VERIFIED（切片） | 173e026；21路径独审/1068tracked hash匹配；Root第三轮format/check exit0，106generated与原43路径保持，7正规生成/双检通过；两轮RED保留，CI/Docker未实跑不称通过 |

---

### 5.1 下一检查点与工期口径（2026-11-02）

**当前立即动作（覆盖下方历史交接）**：按 §0.3 修复 SDK consumer 并处置已证测试问题，主方停写验证后正式发行 IAM native2 artifact，再由 BFF 完整迁移消费者与删除旧浏览器回退，保有效 action/事务/取消与公共身份。正式四旅程已由 aec5775a/run2a960804 完成，不重复 I-33 调试。I-31仅native默认入口随I-30完成，其余凭据用途/重复登出/依赖不确定/零写等风险映射继续补证；G1未关闭。T-17/T-11完整生命周期与删除仍在G1后。

**历史 I-29 首版接收检查点（2026-11-02，当时候选未提交；当前见 §0.3）**：IAM首次55文件停写清单hash `c4a505dc3a5bb86dced0be78302a71166c86cdcc500c2c1b56c5f0bdabb4a90c`；主方确认native1原件hash不变。真实native新suite 11PASS/13.38s，完整verify 124files/1613PASS/exit0；两次541输入无漂移。随后完整真实integration为43files pass/5fail、464pass/15fail/421.62s，输入仍不变，归I-35。通过范围不覆盖失败项，不作owner发行依据。

双审发现两项D0内缺口，统一归I-29不重建问题中心：resendTenantInvitation实际接受native但正规生成操作清单与新真实矩阵遗漏；native请求未真正接同一入口期限/HTTP断连，非协作依赖可能超预算且迟到抛500。唯一writer已获窄返修：resend正规生成/正负控；原lifetime＋具名native ingress/窄interceptor/guard/service共享预算，admission原504、business取消/unknown503，OAuth及服务身份不改，不承诺撤销已提交业务。主方所有测试已终态后才交还写区；后继重新冻结、双审、完整门和真实I/O，BFF仍待正式owner artifact。

I-35诊断续证：在私有临时`git archive 5fffe60`源码快照复用未变依赖/Prisma生成物，原3个CLI真实测试3FAIL；最小私有类别诊断见底层P1010→FAILED_TO_GET_SESSION，未保存原始凭据/异常payload。受管测试admin URL未显式user，父进程有默认USER但CLI按设计只用显式env，造成身份漂移。仅从同一管理连接读取current_user并将其私有地明确到测试URL，原基线/原断言3PASS、46非选、15.56s。快照已清理，不修改全局配置/CLI、不新增账号或扩大child env。验收wrapper后续固定此资源身份；3份旧oracle修订仍待主方真实GREEN，完整15失败记录保留至整套重验。

**历史首版返修时的进度重盘点 / 工期边界（不作为实时 worker 状态）**：

- **暂停问题**：机器Goal为active；上轮验收进程确已结束，当前IAM实现正在运行。Goal状态、worker运行、测试服务存活是三个不同事实。现无待用户批准事项；具体桌面暂停原因没有调度日志证据，不能归因于权限或环境。主控须在每次阶段交付同步当前writer、下一动作和依赖，避免把“有计划”写成“正在执行”。
- **历史候选交付预测（首版候选现已交付，进入返修，不作剩余倒计时）**：本次记录时刻`2026-11-02T03:24-05:00`；IAM writer在本轮报告候选实现/定向检查尚需约45～70分钟，低置信度、仅本轮时点预测；不含真实PG、独审、全门、提交/固定artifact、BFF消费或整个A。已报native2/guard/current-facts/Team定向结果仅为阶段证据，尚有原测试actor断言待承接，不写VERIFIED。
- **剩余关键路径**：IAM owner及正式artifact → BFF共享认证/生成消费 → Skills、Account/Team/Admin/Billing、MCP实际链与负控 → I-31/G1 → T-17生命周期 → T-11旧实现删除 → T-09/T-16最终组合 → T-15同步环境 → 原A产品项。依赖契约和共享文件保持单writer；消费者清单与原A只读核量可以并行。
- **当前Goal完成定义**：G1认证生产切换、G2生命周期/删除、G3冻结组合验证和同步环境全部达到退出条件；这是C前置Goal，不是原A01～16产品完成。11/18的VERIFIED是切片状态，不计算为Task A完成率。
- **当前运行环境**：正式4/4收据再次读取确认passed，cleanup/quiescent通过且无保留文件；没有据此交付常驻同步E2E。当前文档盘点不启动服务，后继T-15独立交付入口/支持旅程/健康与回收归属。

**本轮I-30实施写区（BFF唯一writer）**：固定IAM497900/0.18原件不升级；include新增verifyNativeSession（23→24 operation），使用generated native响应与既有ApiErrorResponse闭集，删除重复手写schema/arbitrary code fallback。仅openapi-ts.iam.config.ts、必要的既有generator精确保真normalizer、正规src/generated/iam-http生成物、依赖manifest、session-admission.client.ts、两份相关测试与package.json；16生成文件allowlist/双生成/owner digest不变。对owner closed object和RFC3339 offset语义补最低充分回归，native suite纳入默认入口。无Schema/lockfile/业务授权改动。已由f81f271交付，主方format/check全0，contract1345/default2350pass+2skip；1068输入无漂移，双审CLEAR。I-29后继owner artifact升级仍须重新固定/生成，不将此版本永久冻结。

**I-29历史静态发现（后续 owner 实现见 §0.3）**：当前BFF native client从permissions字符串推platformAdmin，而IAM原生permissions来自organizationRole，不等于User.platformAdmin事实；此项不能以I-30生成替换冒关闭。与Skills/MCP/publisher/OpenApp的原user-delegated资格一起由IAM owner明确当前事实与native决定，先更新相应设计/机器契约再消费。withSkillActionAdmission丢失verifyNative也须迁移；公共skill.list身份和服务身份不误删。

**历史 I-29 独立设计复核：当时 owner 三面 D0 通过、实现待交付；当前见 §0.3**。建议 native profile 2.0 删除无有效业务消费者的permissions、增加required platform_admin（当前User.platformAdmin事实，版本合法性留owner内，不增加无消费者wire）；旧1.0原件只读保留，新版正式生成/固定后原子切换，无兼容fallback。当前admission本身已核active tenant，缺口是业务事务helper/Team list未复核，以及Team Members/Roles/Invitations把Session/native proof丢失；必须承接exact Session/User/active tenant/current member，不只加四operation guard。角色政策按原owner承接：Skills/MCP检查角色完整性，Account/普通publisher不暗加全局角色门。现native admission的异tenant→BFF403既有语义保持。新增消费清单包括app-skill-bindings二次Bearer、skill-admin/installations regex enrich、managed-personal-skills/publisher、Billing成员分页/末端复核。IAM5fffe60/BFF105024d已明确这些写区/资格/错误/事务与零DDL并通过规格/质量双审，后继可实施；设计通过不冒实现完成。native2唯一必要新增native_session_service_unauthenticated（owner401→BFF既有503），human失效401保持，未归属401为503；原native1不改，不增加SLO/部署门。公共skill.list/第三方OAuth/服务资金与执行身份保持；事务内复读不承诺跨owner全局撤权原子性。

**I-33历史定位实验（已运行，结果见下）**：仅在隔离Web代理转发精确GET /api/account/profile时设置单个随机x-kokoro-request-id，以其入站hash→响应hash桥接App的两次/v1/me与业务profile请求；只留状态/错误类别/计时/hash，不留body/cookie。已读源码确认header用于关联而非身份，原driver、限流和预算不变。IAM native admission按caller/credential/operation共享100/60s bucket的静态事实已确认；仍需同请求证据判断本失败与429的关系。当时在BFF停写并精确配对后运行；后继同请求因果与窗口对照见下。

**I-33已取得因果与私有对照**：Root75f6e1ce/BFFf81的run7890d310同profile请求hash匹配首次/me429 session_rate_limited（2ms）→App503（11ms），业务profile未调用；cleanup PASS。单变量私有driver在旧context.close后、创建独立撤权A/B前等60,001ms，run3dbb48c3完整4/4、0次429、五次profile200、cleanup PASS。仅证明测试场景累计负载跨窗口后可通过；不称正式收据/产品容量验收。正规写区限Root driver及既有native测试；保持175秒总预算、3秒/4.5秒退休、同fixture的A/B、无重试与原断言。Node计时只要求完整60秒，sleep请求含1ms余量；不足剩余预算提前拒绝，不扩大watchdog。上述正规调度现已交付并通过主方停写门，aec5775a正式4/4通过；本段保留当时设计，不再指示重复运行。

**I-34局部修复写区**：App account-profile.ts、现有account-profile-admission.integration.test.ts及相邻server/INDEX.md精确条目。既有final null/身份改变/过期401和同主体200覆盖复用；补真实loopback最终429/503/断连→503、无资料泄漏。无owner/Schema/wire变化，先RED再删除局部catch。与Root编排writer路径独立；完整门和真实资源仍由Root串行。

**已交付I-32：当时检查点与写区**：cc405正式run6cb4509024b133f193c0ddc7在focusProbe172等待session响应超时，cleanup PASS。Playwright1.62.1源码默认Emulation.setFocusEmulationEnabled=true；主控私有副本仅在focusProbe起始对page/peer关闭该override，ecfbb0f5659e34406c291314实证trusted事件＋401，继而完成异tenant退休/恢复与UI退出全段，第四旅程新context登录账户入口超时。该副本不是正式4/4验收，不修改旧收据0/4。当时限定driver＋native测试两路径实现此focus纠偏，保全部原事件/预算/退休断言，不靠synthetic dispatchEvent；该修复已精确提交并复跑，后继第四旅程失败由I-33承接。

**I-31最小负控证据映射（只读审计，未新增运行结果）**：

| 风险 | 可复用当前测试与基线 | 缺口 / 后继 |
| --- | --- | --- |
| 匿名 | App e1be product-bff/session-proxy；IAM1ee8 native-session-admission unit，分别已有6407/1566默认门 | 旧cookie拒绝及当前UI另以正式旅程为准 |
| 错Origin | App native-sign-in route零relay调用；IAM native unit；BFF4d6 native-session-admission真实loopback零IAM调用 | BFF f81f271已纳默认入口，Root2350pass覆盖该native文件；后继新增风险仍单独补证 |
| 伪造tenant/subject与零写 | App session-proxy丢弃伪造身份；BFF user-admission已有零receipt/route oracle | BFF相关fixture仍Bearer/raw，I29时承接到native生产准入；body自报身份单独核，不外推header测试 |
| 失效/错surface服务凭据 | IAM direct-service-authenticator现有rotation/malformed/unknown矩阵 | 参数当前只Billing/execution，无session_admission；沿现矩阵与host补该purpose真实接线 |
| 重复登出 | IAM真实host长旅程仅一次sign-out | 私有重复revoke命令不是重复登出；沿原logout补重复请求/终态/旧cookie保持拒绝，状态按owner契约 |
| 撤权旧请求 | IAM1ee8两host66pass覆盖tombstone/旧cookie/SID重放；BFF旧replay零额外route | native化承接现幂等回放拒绝风险；UI/跨标签迟到独有证据归正式旅程 |
| IAM不可用 | App mock BFF unavailable；BFF旧Bearer/缺配置fail-closed | native配置齐全但IAM连接失败/超时仍待BFF现loopback补503/有限时间/无重试/零业务调用，不关共享服务 |

矩阵不新增任务中心或自动生成重复测试；I-29/I-30/31都在G1前收口，G2生命周期/旧实现删除保持后继。

**I-28已复现与最小纠偏**：bad205正式run c2e12b5a失败于异tenant双401断言；私有40e265df实证session401/native_session_required、projects403/product_tenant_forbidden。只读沿IAM→BFF→App证实该403正确；其他exact session删除/成员撤销仍401，退出匿名仍200/false。唯一writer仅driver/native runner/现native测试，先补typed code/status拒绝负控，再同步三处精确oracle；不改产品、不允许泛化401|403。I-27传输修复已过主方108定向及正式真实profile barrier，该完整旅程仍待I-28后重验。

**G1额外收口，不能只看四旅程4/4**：I-29旧Bearer生产回退仍待，I-30受控native contract消费已完成；后继owner新版仍按契约重新生成；另将§3.1负控逐项映射已有case/精确SHA/实际结果/零副作用oracle，缺项才补测。IAM PlatformWorkloadController与fixed-Web OAuth测试需补保留/退休disposition，不按字符串误删公共OAuth或当前native guard仍用的IAM_PRODUCT_WEB_CLIENT_ID。Capability f515 receiver-only已验足够此切片，最新base整合仍归G3。后继T-17/T-11不提前实施。

**历史运行检查点（已由I-33续接）**：I-26修复已提交50ac142b并完成Root完整门；正式run8160b600已越过cold_login UI/profile而在tenant_rejection_recovery失败，整体收据仍0/4（失败路径不输出部分成功计数）。I-27主控私有诊断确认原fetch“TLS建立前连接断开”、upstream_status=null，同一真实请求经自有loopback/原Host/cookie返回200；不是认证失败。以下第1项实现已交付，第2项重验发现的新阻断由I-27承接。

**I-27最小写区与验证**：只修改既有Chromium driver和native runner测试文件；将config传入profileBarrier，route.fetch显式指向`https://127.0.0.1:<owned port>/api/account/profile`，保留原request.allHeaders及固定原origin Host、4500ms/maxRetries0并禁redirect；现有App profile GET适配器自身拒绝上游Set-Cookie且成功响应不返回Set-Cookie；本driver不建立新的cookie投影。保原真实response/status/subject与fulfill，不绕过owner或造成功。主方已获得实际RED/同请求200对照，接收最小行为回归后实现、独审、停写门、精确提交再正式复跑。

1. **已交付设计／Root／T-05＋I-26**：在既有共享smoke代理增加仅Web实例启用、精确`GET /_next/webpack-hmr`的Upgrade路径；固定自有Next上游，严格握手/101双向转发、有限连接/空闲/总时长预算和断开回收。不支持任意CONNECT或动态目标，不记录frame/cookie；普通HTTP/SSE、body上限与默认smoke行为不变。先查现有可复用实现，再在现有代理测试补握手/双向/EOF/关闭/禁用负控RED，随后实现与独审；不关闭React debug channel或增加登录等待掩盖问题。
2. **主控验证／T-05**：代理定向及Root相关完整门→停写提交→正式四旅程原断言重跑。保持自然签发cookie、精确owner绑定与凭据私有管道；若HMR已通而UI仍不就绪，继续定位实际挂载原因，不先关闭I-26或G1。写区限定共享代理、其现有测试及native runner必要的显式启用接线；无App/IAM生产、Schema、依赖或lockfile变更。
   **组合依赖边界**：G1按当前已冻结、已验证的Capability f515组合判断认证门，不等待最新base整合；I-25/T-09整合在最终G3前完成，新组合重跑受影响G1回归。这样不形成G1等待T-09、T-09又等待G1的循环。
3. **G1→T-17/T-11／BFF**：生命周期真实释放通过后，按feature迁移原消费者并删除raw/aggregate；不提前删除测试或创建第二套运行时。
4. **T-09/T-16/T-15／Root与owner**：保留双方更新整合Capability publication冲突，完成Agent及受影响owner最终门、组合E2E和可同步环境。每仓独立PR，未完成前不合main。
5. **原A产品阶段**：G1～G3通过后才进入A-01/A-02→A-07；其余原A任务继续保留。当前原16项没有逐项剩余工作量与已配对端到端验收，故尚无可信完整完成日期；不把“未验收”解释为全部从零实现。下次估时须标明范围、基线、依赖、实际剩余量和置信度，而不是滚动重复3～7日。

**本次I-29消费者核量（不是全A总工期）**：基于BFF105024d实际Nest生产调用链的只读盘点，原先owner+BFF合计1.5～3人日低估了隐蔽消费者和认证测试迁移。修正为BFF本片约**5～10工程人日，中低置信度**；以熟悉本仓的工程师有效投入衡量，不是Agent墙钟承诺，也不除以Agent数换日历天。

| I-29 BFF工作包 | 剩余工程人日 | 核量依据 |
| --- | --- | --- |
| 固定artifact/共享认证底座 | 1～2 | 正规生成、必需native接口/显式proof、严格解析与服务401分类、wrapper/shared double |
| Skills实际消费者 | 1.5～3 | action/import、publisher enrich/specification、download/share末验、App binding第二Bearer |
| Account/Team/Admin/Billing | 1～2 | 共享Team client、全部成员分页、Billing末验及typed错误 |
| MCP消费者 | 0.5～1 | 现闭集helper/DI及原公共OAuth/service-only负控 |
| 本片集成/审查/返修 | 1～2 | 真Nest HTTP/实际IAM配对、零副作用/末验、完整相关门 |

前提为IAM正式artifact满足D0且可运行、既有资源可用，无新增owner/Schema/协议裁决。该量包含本片认证fixture迁移，**不包含**IAM剩余、其他owner的I-31、T-17、T-11剩余raw全删、Capability整合、Agent全门、G3环境或A01～16；后续T-11核量须扣除本片已迁测试。首条wrapper＋publisher＋Billing分页真实链闭合后据实收窄，而不是每轮重新启动“5～10天”倒计时。

**历史容量预算（I-30/I-33交付前的工程判断，非当前剩余）**：当时替代未纳入 I-29～31/I-33 的旧5～12人日，仅估C前置阶段而非整个Task A。现I-30/I-33已交付、I-29设计已通过；下表保留估算基准，不把已关闭工作继续计为剩余，也不重新滚动倒计时。当前剩余以T-05中的I-29/I-31、T-17/T-11、T-09/T-16/T-15为准，首批IAM实现后据实际工作量再更新。

| 当时C阶段工作包 | 当时估计工程人日 | 退出条件 |
| --- | --- | --- |
| I-33定位/最小修复/正式四旅程 | 0.5～2 | 同请求因果证据、回归、原断言四旅程完整通过 |
| I-29 owner授权适配与生产回退删除 | 1.5～3 | 先IAM设计/artifact，再BFF消费；有效权限承接且旧浏览器入口零消费者 |
| I-30受控native生成消费 | 0.5～1 | 正规生成/重复schema删除/contract保护/默认入口纳入 |
| I-31 native负控补证 | 1～2 | 风险→case→SHA→结果→零副作用映射齐全，不重复已足够的测试 |
| T-17真实生命周期 | 1～2 | shutdown/drain/SSE/worker/PG/Redis释放与失败边界 |
| T-11 raw/无边界聚合删除 | 2～4 | 按feature迁消费者、风险承接、旧项删除、零引用及行为复验 |
| T-09/T-16/T-15集成与同步环境 | 2～4 | 保留双方更新整合、最终owner/组合门、可同步环境及回收说明 |
| **当时C阶段合计（非当前剩余）** | **约9～18人日** | G1/G2/G3均达到退出条件才关闭当前Goal |

前提：持续有效投入、既有资源可用、I-33属局部问题、没有新增owner/Schema裁决。I-29～31共享部分BFF写区，G1→生命周期→删除→最终组合有串行依赖；不能除以Agent数得到日历天数。复用已验成果，不把历史未验项目都算作重做。其中I-33根因与IAM授权D0现已明确；首批IAM实现/消费者及raw迁移有实绩后，再按实际剩余消费者重估，不是每次会话重新倒计时。

**完整A的估时缺口（原16项未缩减）**：

| 原A范围 | 当前可确定的剩余类型 | 还需核量 |
| --- | --- | --- |
| A-07 / A-08 | 明确缺Project Todo写操作、附件发送/Run绑定/读取资格 | 设计、契约和消费者具体改动；不拿Run Todo/导航代替 |
| A-01/02 | 已有实现且有明确语义/展示待修边界，不是仅缺测试 | localDraft/retry/retire、导航/多标签/迟到；RunDisplay分组/身份/历史/回焦的当前case与实际缺陷量 |
| A-04/05/09/10/14 | 已有实现或历史子链，当前恢复/压缩/资料库/产物/语音完整验收未齐 | 当前commit的实现—case—收据映射；未验不等于全量重写，也不承诺无代码修复 |
| A-06 | 项目上下文已有部分成果，菜单/排序/删除释放等支持面未核量 | 逐动作实际差距，不按页面名称计算完成 |
| A-03/11/12/13 | 当前支持面和剩余量未逐项核实；A-12需原writer交接，A-13对应外部末端有条件依赖 | 输入控制、实际支持场景、自动化DST/重投/结果、外部账号callback/过期；不将末端条件扩大为全A阻塞 |
| A-15 / A-16 | 体验缺陷未按页面量化；已有多仓draft PR，仍须随片验收/配对 | 缺陷与性能基线、交付成本；当前不merge main、不发布 |

完整A当前没有有依据的总日期。本次已完成原16项文档证据分类，A-07另窄核canonical OpenAPI仅listProjectTasks及repository列表读；A-08原handoff明确缺选择→发送→Run绑定/读取资格。没有任何完整A行因本次盘点新增标完成。上述分类不是全产品源码审计；原 **0.5～1工程人日只读盘点预算** 尚须补支持动作/缺陷量及当前case映射才能给全A总范围，可与C实施并行，不提前写A功能。

本次Goal保持active，未创建重叠目标或将任何未验条目标complete。后续交接注明“主控下一动作”，不将worker等待当作需要用户再次发送“继续”。

## 6. 验证与风险控制

### 本轮文档交付

- `git diff --check`；本轮改动Markdown的本地链接检查。
- 独立review核“当前/历史、候选/Root验证、C/A边界、问题→TODO→关闭证据”一致。
- 本轮只核现有提交/收据并更新文档，未运行业务测试或启动服务；旧1pass/2fail属于初始文档轮历史，不作为本轮结果。文档轮不重跑全部业务门、不安装Schema。

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
6. **下一轮默认动作**：正式四旅程已通过，I-26/I-27/I-28/I-30/I-32/I-33/I-34不重复实施；先按已通过D0实施I-29 owner→消费者并补I-31/G1负控。T-14接收方不重复实施。G1闭合后T-17完整生命周期→T-11删除→T-09/T-16最终组合门→T-15同步环境；A功能继续门控。

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

### 历史验收推进：冷登录GREEN、T14全门RED与后继设计

Root4fdb2ede精确App727/BFF4d6/IAMe6 source/clean/gitlink通过。全新Chromium context未注入cookie，真实表单303、session200、projects200；独立冷登录诊断与原最小HTTP4checks均PASS，cleanup PASS/quiescent/无保留资源。仅关闭I-21冷登录缺陷，不关闭T-05四旅程。

Capability首次Root完整门format/lint/Prisma validate/build均0，verify退出1：3049pass/678skip/2fail。两项为本次旧OAuth删除/有效Agent错用途导致的旧oracle：preflight期待泄露ENOENT但现execution reader抛sanitized错误；generated-client期待Code16但应为有效credential错surface的Code7。只授权两现测试精确承接typed失败、无监听/零写，保留RED，生产不因此改宽。待重新冻结后Root真实receiver及完整门。

I-24退出局部修复授权App唯一writer：现iam route、现真实transport测试（必要时原route测试）及CURRENT；先loopback真实RED，再按已批准空体POST补明确零长度Uint8Array，不放宽transport或新建helper。当前冷登录源码已提交，不在验收中重写。

T-05余下旅程的后继最小设计：沿现IAM native host增加test-only浏览器fixture、session绑定slot和有限switch/revoke命令；cookie从浏览器自然签发只在私有pipe/内存交接，owner验签并核本fixture同user、非seed exact session后才绑定；Root不SQL IAM。另建同一user合法第二tenant membership验证固定Product拒绝及真实重登恢复；App UI退出须核exact session消失；独立A/B浏览器分别验exact session撤销仅影响A、membership撤销时B session仍存在但准入拒绝。保持原最小smoke模式，新driver/模式显式扩四旅程；先停Chromium再Web/BFF/IAM，保现精确资源回收。具体写区限IAM native host/其integration、Root native runner/新Chromium driver/现runner测试。此处为当时设计记录；其中“退出session消失”已被§3.1的expired tombstone oracle替代。host与driver后续均已交付，当前结果见§0与T-05，不使用本历史交接状态驱动执行。

### I-24主方静态门与T14真实接收方GREEN

App1d54eedd4d67482c789ae3f7dd60807302732b24三文件退出修复已独审并经Root完整check exit0（contract452/architecture50/full6403/0skip、lint/types/build；1494hash保持），沿原PR50交付。本次Root仅更新App精确pin；真实sign-out及旧cookie重放另验，T-05仍OPEN。

Capability72路径修正canonical ownership断言后，Root真实HTTP→production receiver→隔离PG组1pass；13项为本次-t未选择，不计本组覆盖。System成功/自然重放/冲突/disabled不复活、BFF/Agent/未知凭据拒绝、文件删除后撤销、ownerTenantId/ownerUserId均null、零receipt/outbox/IAM请求均过；数据库inventory前后相同，Redis仅connect/ping/quit无key写入。不是System producer链。最终完整owner门再次串行运行中，尚不提前标全绿。

T14实际交付：Capability f515e225，PR13 OPEN/draft，base为原PR12候选分支；GitHub实际mergeable=CONFLICTING，明确不合并。Root配套六文件hash保持，再跑154定向/141subtests通过（前轮完整治理1879/3skip/506同源码）；本次Root提交精确pin f515并配对退休配置删除。I-25记录最新基线集成，不借旧已验组合否认他人四个新提交。

I-25只读集成调查已完成：共同基线44fcc；9重叠中5处文本冲突为provenance与四份设计/current文档，另checker/product-mcp.rpc/mcp.ports/architecture需语义复核。更重要的是远端mcp-private-server-v2-contract.ts从冻结父重建整份provenance，会拒绝/生成时删除T14认证索引；后继必须保v2精确contract发行及认证索引独立严格校验，并补生成保留/只读不写负控，不能重签父快照或删除索引。新Schema的global currentConnectorId=NULL需真实T14重验；B01 private/personal、fresh/父升级/回滚/代际撤权及Custom API真PG均随新组合重验。新B01消费者发布/正常Schema激活归其owner，不在本片擅自实现Task B；当前f515证据不继承到新合并树。本轮只读调查未合并、写对象或修改base分支。

App媒体类型修复e1be73e08bb1bd4c9c554c9e319f6b079006fdb5已Root独审与完整check exit0：contract452/architecture50/full6407/0skip、lint/types/build，1494输入hash不变。仅三文件沿PR50交付；本次Root精确pin后再次验真实App sign-out/旧cookie重放。I-24在真实GREEN前仍OPEN。

### I-24真实退出最终GREEN（Root1e6组合）

同一新Chromium未注入cookie，真实表单303、session200且authenticated=true、projects200；浏览器实际调用App sign-out返回200，session200且authenticated=false、issuer session cookie数量0，projects401，内存旧cookie独立HTTP重放401。原最小smoke4checks与cleanup passed/quiescent/无保留文件均过，原RED和匿名状态错误oracle留证。无cookie时session接口既有契约为200/false，不是401；修正临时driver为精确false+cookie0+业务401+旧cookie401，未放宽生产或删负控。仅关闭I-24及冷登录HTTP缺陷；本次不是Settings按钮点击，也未运行异tenant恢复/独立撤权完整四旅程。
