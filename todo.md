# Kokoro · 当前执行 TODO

更新：2026-11-12。唯一执行清单；当前批次基线Root `4d6c29f4`，不重开已交付Task A，不重复扫描凑问题。

## 当前任务：Task B 正式接管（2026-11-12）

用户已把 Task B 移交本主控，历史“Task B 不动”仅约束当时 Task A／UI 批次，不再排除本任务。沿[原功能交接](docs/handoffs/2026-10-30-task-b-capabilities-account.md)和[既有有效计划](docs/superpowers/plans/2026-09-03-kokoro-production-closure.md)推进，不重开已交付 Task A、不另起任务中心。以下是接管后的真实剩余队列，不把原15个功能域当15个新故障。

- [x] B-T0 接管：确认原 Root #67、App #49、BFF #17、Capability #12 及当前 main；主控保原PR历史、全部12个已验 main gitlink和正常运行源，不盲激活旧组合。Root原分支已合入当前main；原468行Task B记录保留。
- [ ] B-T1／R-07（进行中，api_perf_audit）：Capability contract check 改为只读；显式generate仍能写。临时生成后完整集合／字节比较，覆盖漂移与异常回收；不改 wire、Schema、生成器算法或正常服务。
- [ ] B-T2／R-14（后继）：OAuth DNS pin 限定一次有界操作，保同操作DNS漂移拒绝、实际IP连接／Host／SNI／取消，不清共享Map冒修复；先补局部生命周期设计。
- [ ] B-T3（只读盘点中，composer_ui_audit；集成主控）：App/BFF原PR与最新main按真实功能合并，保原 Task B成果和Task A修复；不整树择一、不强推。共享入口／契约先由owner交付。
- [ ] B-01／B-02：消费者与当前实际加载源配对后，只补MCP显式断开→新授权→Prepare→刷新／删除，以及Custom API缺失的冲突／撤权／迟到与秘密边界验证。已有真实Docker成功／取消／刷新不重跑；完整云E2B沿已接受边界暂存。
- [ ] B-03～B-05：核Skills已有作者／版本／安装／使用收据与当前源码，仅补入口一致性、剩余权限及后台缺口，不重新造功能。
- [ ] B-06～B-13：按原表核账户会话、设置／个性化、团队／分享、模型／积分和对应Admin；复用已有成果，补实际缺口后逐片交付。真实支付继续关闭，不新增内部OAuth／认证层。
- [ ] B-14／B-15：视觉／多语言／性能与文档、原PR、精确组合随每片关闭。原PERF-02 pins重复准入、模型目录取消和icon404纳入当前owner核验，不再以“Task B不动”为由搁置，也不抢跑改未核明的事实。

主控唯一管理Root台账／Git／资源／最终验收；两agents先独立调查，R-07单writer。每仓沿原PR，完整验收后正常合main并清本轮分支；不部署、不清卷、不删除归属未明worktree。机器Goal当前为空，本轮先以唯一TODO推进，未从普通任务隐式创建Goal。

## 上批已交付：Composer体验＋页面请求性能

[诊断与最小方案](docs/reports/2026-11-12-composer-ui-and-api-performance.md)。主控先真实采样再修根因，不把单截图通过冒全站UI完善；不为“性能”增加cache／新认证层。

- [x] UI-05：模型菜单定位／间距／checked／长名称；composer_ui_audit负责独立Composer写区。
- [x] UI-06：成功空目录与锁定选择缺席时不误标另一个默认模型；同一writer，保草稿／选择／命令。
- [x] PERF-01：删除未打开Settings/目录的无用connector预热，保现Composer/default/restore/chips；api_perf_audit负责独立overlay与相关测试。
- [x] 主控验收：停写后相关回归、正常读路径对照、首次打开/重开与菜单浏览器验收；文档与精确组合已验。本地已验：focused411／完整lint、非增量TS、build／预览E2E8通过；正常页17→raw15（含独立session1），可比页面读14，三次无用目录读消除。首次Settings三目录200、重开复用，原菜单／Esc通过；自有PR／main清理以本批Root PR最终出口核验为准。不把最初截断片段或单样本当p95。
- [ ] PERF-02交Task B原owner：pins GET重复准入（源码3次／6 IAM），实际hunk交叉，本批不写。
- [ ] PERF-03后继：模型BFF请求取消／绝对期限传递，需独立HTTP peer回归，不冒已修。
- [ ] 观察项：Settings既有MCP icon404；owner待核，不冒三目录读取失败或本批已修，不越界Task B。

App [#62](https://github.com/LordFoxFairy/kokoro-app/pull/62)已正常合main `59d412c9`，树核等已验源 `179b6412`；本轮App local／remote topic已清（远端引用另核）。本次CI annotation确认账户账单／额度导致任务未启动，不冒测试绿；未调整付费或绕保护。Root精确组合拓扑／兼容15边0违例／原checkpoint通过；Root自有 [#90](https://github.com/LordFoxFairy/Kokoro/pull/90)负责交付，最终出口核对MERGED／main clean及本轮topic已清，不以文档先行勾选代替。

Task B／Mori／后台／部署不动。GUI与API问题一起列明完成边界，不用大量旧测试或假成功页面代替收口。

## 上批已交付：Skills 操作区内容适配

Root基线 `1eb7a427`／App `a2bb4a4d`。正常登录设置页复现：Browse skills文字85.45px溢出pointer:fine下72px按钮；Create另有84／116px反复覆盖，嵌入工具栏锁两行32px。仅改Skills局部布局，清除固定尺寸／冲突覆盖，搜索与操作、筛选按容器自然换行；共享Button、业务hook／权限／创建／导入协议、Task B不动。

- [x] UI-04：移除Skills操作固定宽度／行高约束，保完整文案、搜索可用、筛选独立一行和键盘回焦。
- [x] 复用原内容布局E2E，覆盖中英法桌面／320px窄屏；原Connector用例保留，避免再复制一套测量。相关Skills单测／TS／build与正常页测量后按自有PR收口。

App [#61](https://github.com/LordFoxFairy/kokoro-app/pull/61)已正常合main `46ea8bc3`，树等已验 `0501f81d`。主控最终Skills中英法1000／320六例、相关UI101／ESLint／完整非增量TS／build通过；最终两个修改输入SHA核等。前序原Connector六例＋Skills六例共12已过，法语筛选词视觉补口后只复跑受影响Skills六例，不把两阶段拼成一份最终全套证据。新增search容器高度、filters独立行、法语单词不硬拆断言；正常英文另实测72px→101.45px完全容纳85.45px文案。独审已修手机column风险并最终CLEAR，非全站／全部译文验收。

主控唯一writer／Git／验收，单个紧密耦合CSS问题不强行拆并行写区；停写后具名agent只读审查。之前两处截图修复仍已交付，不把本项发现冒成全站扫描或重开Task B。

## 上批已交付：截图缺陷与相邻代码瘦身

基线 Root `3054825b`／App `dcc0faff`。本轮只修已复现的设置页缺陷，不把上一轮核心链路验收当成全部UI完善；不做无边界十轮扫描，Task B／Mori／后台／业务协议不动。

| TODO | 根因与最小方案 | 状态／owner |
| --- | --- | --- |
| UI-01 连接器操作挤压 | 正常设置页实测Browse文字126.74px、按钮86px，现gap8px；删除86/64px固定width和冲突的单行锁定，让操作按内容定宽、搜索有可用下限并随容器换行。保现Button／menu／hook，不增基础组件或新断点平台 | 已实现／主控3语浏览器回归通过；ui_toolbar_diagnosis实现，ui_memory_diagnosis交叉独审CLEAR |
| UI-02 记忆底栏白块 | 正常页实测footer90px，按钮42px、上下padding48px且背景白色；保sticky与正常流占位，改为紧凑一致的面板背景／间距，不造fixed底栏或第二滚动容器 | 已实现／原末字段与焦点回归通过；ui_memory_diagnosis实现，ui_toolbar_diagnosis交叉独审CLEAR |
| UI-03 相邻失效代码 | 删除本surface不存在的CSS module class引用、无消费者的样式和不匹配DOM的选择器；不为残留名字补空层，不顺手改业务hook／状态机 | 已核实并删除；原wrapper／业务hook保持 |

验收绑定这两处布局：桌面与窄屏、英文及长译文文本内收／按钮不相交、搜索可用；footer缩紧且末字段可滚到其上方，弹窗键盘／取消回焦保持。复用原UI与responsive E2E，只补缺失几何断言，不跑模型／资金／沙箱／完整默认套件。沿各仓本轮自有PR交付，正常合main／清本轮分支。

设计思想：业务行为继续归原feature hook／组件，局部CSS只管布局；操作尺寸由内容决定、容器负责重排；复用已有组合边界而非新增继承体系。截图之外的架构重构须先有具体重复／耦合证据，单列后续，不将模式数量当优化成果。

**本批交付**：App [#60](https://github.com/LordFoxFairy/kokoro-app/pull/60) 已合main `a2bb4a4d`，树核等停写已验源 `52503adf`。主控相关UI454 PASS／完整非增量TS／相关ESLint／build通过；原Playwright预览runner 12 PASS（中／英／德1000与320px＋原footer三视口亮暗主题），normal native-auth英文另实测。六个生产／测试修改输入在门禁与build前后SHA核等；不重跑默认／模型／账务／沙箱。九语言布局策略不等于九语言全部词条翻译已验。

GitHub App本次CI annotation明确任务因账户账单／额度问题未启动（不是测试执行失败），未调整付费／额度或绕保护；交GitHub账户管理员处理。Root只更新精确App gitlink与实际Git blob inventory，Task B同文件其它hunk／PR未修改或合入。

本批两个截图问题已收口，不标记全站UI完善；后续只按真实页面证据继续修交互／布局和相邻冗余，不做无边界架构重写。

## 上轮已交付：Agent 真实闭环 → AG-UI 单轨呈现 → 工作台首页

**本轮实现与验收已收口，Git 最终出口以自有 Root [PR #87](https://github.com/LordFoxFairy/Kokoro/pull/87) 的 MERGED／main clean 为准。** 机器 Goal 在最终出口核对前保持 active；不重开历史 Task A，不接管 Task B／Mori，不部署。

| 阶段 | 结果与边界 | owner |
| --- | --- | --- |
| G0 设计 | [实施方案](docs/superpowers/specs/2026-11-12-agent-runtime-closure-design.md) §12～14；复用原可插拔后端、owner与协议，无新框架／OAuth层／Schema | 主控设计与集成；具名 agents 分区实现／独审 |
| G1 真实主链 | native IAM＋真实模型＋structured-report Skill＋Context7 MCP＋Docker＋Storage FINAL＋浏览器已验，原失败与个别命令 exit1保留。普通脚本生成后资金拒绝，再同会话仅交付恢复也已验，不拼成一个Run成功 | Agent／BFF既有边界；主控正常持久资源 |
| G2 产物来源 | 报告1469bytes，原workspace版本／FINAL／下载 SHA `de656263…ae12cf4`核等；普通脚本108bytes／SHA `49daae46…7cde86e`跨显式失败恢复后同字节交付。两终态容器已回收，不混同scratch版本和可变路径 | Agent／Storage现接口 |
| G3 正文与终态 | live／paged同一AI SDK reader，reducer只采用绝对snapshot；采用先于cursor／terminal／错误，同会话reopen退休旧queue。exact Run旧未决Skill中性结束，资金文案不冒权限唯一原因。主控冻结门及独审通过 | SDK agent_runtime_closure；UI／集成主控；agent_spec_review独审 |
| G4 首页／文档 | 保留单Composer，仅补模型／连接器可见读取反馈和既有模型重试。真实菜单／Esc回焦、390×844单textarea／scrollWidth390通过。公开产品子目录／API分层保持，产品指南／内部当前设计已同步 | Composer agui_closure_design；文档／最终浏览器主控 |

### 精确交付与实际验证

- **Agent #47 → main `16984caf`**，树等于已验 `75c0b6b`（生产 `c2c563e`）；**BFF #27 → main `05a10749`**，树等于已验 `ee62845`；**App #59 → main `dcc0faff`**，树等于已验 `61af3848`。三仓main干净，本轮local／remote topic已清。远端CI均有失败状态，已逐PR披露；不冒CI绿、不绕保护。
- **App冻结验收**：主控默认6533 PASS（含contract／architecture行为），全ESLint、非增量TS、22个固定生成检查与生产build通过。57个修改输入在门禁前后逐文件SHA核等；后继只有3份当前文档。SDK／Composer／UI独审CLEAR。不是拿数量代替验收；具体风险沿原定向RED→GREEN承接，不再重跑后端／全量资源。
- **真实浏览器**：复用报告与脚本交付真实历史；失败、成功正文／card及硬刷新恢复。脚本读取初次遇429，窗口后原只读重载两条消息成功，随后硬刷新无缺页；不放宽限流、不重发任务／模型。原Skill不再永久Loading，资金拒绝明确涵盖积分／权限。独立preview test:e2e未重跑，受影响正常认证UI直接实测，不冒全产品或Manus像素等同。
- **公开文档**：产品任务／文件指南Markdown、门户build与61页面／20402条内部链接通过；API原canonical不变。VitePress原大chunk warning保留，未冒新性能达标。
- **Root精确组合**：三个owner上述main已固定，inventory从363个真实已提交Git blobs重算440个引用；拓扑、15 edges／0 violations与原checkpoint结果以本轮实际验证为准。其他gitlink尤其Task B Capability保持不动。
- **运行与资金边界**：原PG／Redis／MinIO／Scanner复用，未清卷／重建；正常HTTP＋官方独立Worker运行，App仅为build短暂停后恢复。累计130非现金开发积分有原owner receipt／ledger，非真实支付。旧供应商overload的held30／unknown evidence保留，不猜零／退款；当前成功Run单独封存。凭据、备份、原始收据和机器操作脚本只在本地ignored，保留恢复资料，不进PR。

### 已确认的边界

- 沙箱本来可插拔：已有state／local_shell／docker／e2b／custom与SDK接口。修的是普通任务装配耦合；产品不新增宿主执行兜底。
- 原Agent HTTP私有持久配置仍在；缺目标位置的.env.local不等于全部配置丢失。Worker配置按正式字段合齐，旧process registry仅历史，不当当前启动证据。原配方在装配前核request／lease并fail closed，保留它，不为首片增新repository读取或跨配置迁移。
- Skill虚拟路径不等于容器挂载；首片不造任意包脚本自动执行平台。MCP复用现连接和授权，不接管Task B配置/管理。
- AG-UI已有safe activity／interaction／delivery，先用已有事实；未公开VM生命周期就不画假“已启动/回收”。
- Task B #49首页候选5文件无file diff；client.ts有Share hunk、conversation-thread有props hunk，实施与集成前再核，不能整文件覆盖。

## 上批已交付，不重跑

App #58、Root #86已合main；Root main07241f03／App026a7d12，已清本轮分支／预览与临时目录，证据归档。门户产品/API分层、来源/生成/示例/导航与实际浏览器已验；A-15当前Project两对与阶段补口已验，冷rAF252～276ms未达100ms。它是后续体验余量，不挡本轮真实Agent主线，也不冒性能达标。详情见[报告§23](docs/reports/2026-11-11-typescript-auth-admin-audit.md#23-a-15当前观测与公开文档收拢)。

## 需原 owner 承接，不进入本轮写区

| 项目 | 负责人／阻断点与下一动作 |
| --- | --- |
| R-06在用i18n正式迁移 | shared发行owner＋App consumer owner；先确认`@kokoro`包scope／现有registry／不可变版本和读权限／发布授权，再原子切manifest-lock-Docker并删i18n副本；当前不以本地bridge冒正式发行 |
| R-03 Admin菜单／旧页面正式接线 | Task B Admin owner；沿原后台PR完成真实业务，不接管、不造成功页 |
| R-07 Capability contract-check写副作用余项 | Capability owner／Task B #12；normalizer与现组合生成物相连，需在该组合做只读check。Storage部分已完成，不重复修 |
| R-14 MCP OAuth DNS pin生命周期 | Capability owner／Task B #12；client无直接hunk不代表composition无依赖，不从独立main小补丁冒称Root组合已修 |
| BFF canonical认证metadata／README／INDEX清理 | Task B BFF owner／#17；普通产品security仍是旧Bearer，与native Cookie／Origin运行不符；版本行及部分文档有实际重叠hunk，交原PR版本化纠正。本轮门户显式披露，不手改生成security，不按旧清库指导操作数据 |
| Admin回环／Hub职责收敛 | Task B App／BFF／Admin owner；需统一共享登录、管理权限和路由映射，不加Admin BFF或万能proxy |

Capability Root pin `24094960`来自已交付#13，已合入#12头`e068fcaa`但未合main；比main多37提交。仅看同名文件或零patch都不足以判定可独立交付；本轮不动其PR／分支／工作树，也不把Task B带入main。

原审计15项主线编号仍为**11项收口／4项遗留**（R-03、R-14待原owner，R-06／R-07部分完成）；上表两条文档／链路交接与编号存在重叠，不叠加成新故障总数。Mori R-05不属本轮。

## 已接受边界与产品暂存

| 项目 | owner／恢复前置 |
| --- | --- |
| A-13真实外部渠道 | 渠道owner；Telegram／LINE／Slack真实账号授权、收发、撤权条件齐备后验收，当前本地协议证据不冒真实供应商 |
| A-14本人语音 | 用户＋App owner；用户方便时主动口述、编辑并显式发送，沿此前“稍后验收”，不保留录音／原文 |
| 可选完整E2B生命周期 | Agent／运行环境owner；实际采用云或完整自托管时补创建／重连／独立回收，既有官方envd Docker证据不重跑 |
| A-15体验余量 | App owner；当前Project两对冷rAF252～276ms，100ms冷目标未达。保留已定位DCL→hydration／首GET区间，本轮只随首页真实影响补验，不抢Agent闭环主线 |
| IAM共享源IP额度／非合作写入取消 | 原owner容量与运行语义边界；代表性负载核验另定，不随意抬限流，不宣称HTTP取消等于事务硬回滚 |

真实支付关闭，未部署；上述不作为本轮独立代码故障或新增阻塞。

## 已交付事实入口

上轮统一维护的两个独立缺陷已通过App #56／BFF #26／Root #83交付并清理自有分支；本轮不重跑其完整门。[报告§21](docs/reports/2026-11-11-typescript-auth-admin-audit.md#21-统一维护goal与集中批次)保存RED／GREEN与验证边界；更早R-01～R-16及上传入口结果见报告§13～20。Task A产品收据见[技术总览](docs/kokoro-handbook/technical/00-system-overview.md)和[CURRENT](docs/CURRENT.md)，历史不再平铺为当前TODO。
