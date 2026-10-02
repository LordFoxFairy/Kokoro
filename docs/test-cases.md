# Kokoro 测试任务总台账

状态：当前测试计划，2026-10-02 / R101；复用既有文件，不建立第二开发计划中心。

- 本页唯一维护**测试任务、验收标准和最新结果**；[task.md](task.md)维护派工/依赖，[progress.md](progress.md)保存实际运行证据，[CURRENT.md](CURRENT.md)说明当前组合。
- 范围：批准Wave0–7全部研发能力与九owner；其他前端、历史Session/Mongo、部署多角色/网络策略不在本轮。支付渠道后置，不删除目标。
- 本表每行是测试任务组，不是一个自动化断言；各owner用例留本仓。未验不等于没有代码，历史通过不等于当前组合通过。
- 状态：通过 / 失败（最近执行） / 执行中 / 待复测（有历史证据或版本变更） / 未验 / 阻塞（明确决策缺失） / 后置。
- 完成条件：绑定commit或冻结hash、实命令/环境、pass/fail/skip、证据和清理；本行必需分支被跳过则本行不得通过；明确拆至其他测试ID的资源分支仍记未验，不影响限定纯门，但绝不计为资源通过。相关source/contract/pin变更后移回待复测。修复提交不直接关测试，Root复测成功才关闭。
- 截至本次盘点：Root2472a05d已发布；严格真实旅程E40终态失败。Home冻结七文件候选经Root完整纯门与独立审接受（E41），尚未提交发布/纳入Root组合；T-Q01仅限该纯门。Agent E35真实PG65通过仍不关闭BFF/Web整链。本次只核已有终态证据和当前hash，没有重新执行全部测试。

## 当前完成度（任务组计数，不是整体百分比）

共 **70** 组：**通过9**；**失败1**；**执行中0**；**待复测16**；**未验41**；**阻塞2**；**后置1**。

通过仅限下表具名范围；完整用户两轮真实聊天E40最新复测失败、E28失败历史保留，**整个产品尚未闭环**。本次整理没有重新执行全部测试，读取已有实测输出并核对当前source hash；最近执行时间/版本以证据记录为准。

## 本次已完成与未完成（可直接巡检）

**已通过9组**：T-Q01 Web冻结候选纯门、T-Q02 BFF纯门、T-Q04 IAM纯门、T-Q11诊断纯门、T-C01后端会话列表过滤、T-C11前端共享owner生命周期、T-K01移除假连接成功、T-B01积分定价纯codec、T-R01本次BFF自有资源回收。各自只覆盖矩阵具名范围，不是九服务或用户全链全部完成。

**失败1组**：T-C06，E40严格真实旅程终态exit1，第二轮活动观测阶段snapshot GET非200；具体status/code未保留，待补最小诊断后定位。不把已越过提交步骤计为整组成功。

**执行中0组**：原31330已经结束，台账不再展示为live。

**待复测16组**：T-Q03、T-Q05–10、T-L01–05、T-F01–02、T-K02–03；历史证据或版本变化都须按当前组合重验。

**未验41组**：详见矩阵。Todo新增六项实际PG通过（总65）是T-A01的局部证据；复杂任务策略/HTTP/BFF/Web仍未验。Home语义纯测通过不关闭T-U01浏览器验收。

**阻塞2组**：T-C05项目移动/归档/删除生命周期、T-B07失败/部分输出/未知成本收费业务规则；T-B08支付后置。

**当前下一步**：snapshot非200诊断/修复与原ID复测；Web候选发布及真实浏览器；Agent HTTP5、消费者过程展示。原Home/诊断/Todo writer已停写，Root负责集成；整组执行中只在真实启动后记录。

## 范围与记录方式

70组覆盖：工程/契约12、登录权限5、会话与项目11、独立定时任务5、文件作品5、Skills/MCP7、Agent过程6、积分支付8、界面4、可靠性安全4、System2、Platform身份cutover1。

每组下的正例、负例、异常、恢复和权限分支按该行验收条件执行；70是测试任务组数量，不是全部自动化用例数量，也不代表已有70组实现。开发task不能代替本台账；发现缺陷→关联原测试ID与开发任务→修复版本→Root复测→全部必需分支通过后才关闭。失败历史保留，版本变化须复测，测试本身出错也单独分类。

## 当前已发现问题（不另算任务完成数）

|关联测试|问题|状态与下一动作|
|---|---|---|
|T-C06 / R94-W01-GREEN|终态旧SSE关闭后仍reconnecting，第二次发送没有POST|真实RED已复现；E24修复完整纯门与审查通过并发布；新组合已按E28严格复测，仍失败于second-partial-active，T-C06不关闭|
|T-Q01、T-C02 / R94-GATE-FAILURE-READ|Root完整门中欢迎页重进后项目路由未达预期|E20/E22保留；E24原配置完整复跑通过，不称已证明历史波动根因；复现时仍按原ID追踪，不增timeout/删断言|
|T-A01 / R94-W03-GREEN|todo.updated缺持久Row decoder分支|真实纯回归失败已复现；源阶段已由E21 Root复验/独立0接受；E35新增6项实际PG验证与独立0已通过；BFF/Web过程消费仍未验|
|T-A06、T-R02 / R94-W03-GREEN|生产者先失败时内部子任务未全部取消并等待|真实纯回归失败已复现；源阶段已由E21 Root复验/独立0关闭原P1；递归/nonmodel错误分支及运行链仍待验|
|T-U01 / R94-HOME-READ|提示入口切本地模式、未绑定owner套餐、硬编码模型档位|E29行为RED保留；E33正式Home局部修复与完整纯门已验并发布；E37错配已真实11 RED，E41四source GREEN已Root纯门/独立审接受，未发布，真实浏览器未验，不关闭T-U01|
|T-Q03 / R95-AGENT-MACHINE-RED|HTTP4缺新安全过程decoded mapping；raw重复键/整表字节预算校验尚未被完整执行|E25真实132行为RED有效；E30 Root候选654contract/1406隔离unit/静态/build与独立0通过，原raw校验缺口已在限定机器切片闭合；E31/E32限定PG已验；真实HTTP/发布/消费者仍待验，不另加整组完成数|
|T-Q03、T-R01|既有archive测试导入时尝试探测ObjectStore，资源归属缺确证|已排除整模块避免纯测访问资源；原事件保留，不声称已清理；后继独立隔离修复|

## 测试任务矩阵

| ID | Owner/层级 | 测什么与通过条件 | 状态 | 最新证据/未完成原因与下一动作 |
|---|---|---|---|---|
| T-Q01 | Web | 本仓format/lint/types/unit/contract/architecture/build；跳过逐项说明 | 通过 | E41：b497+Home冻结七文件候选，Root84433 exit0，249contract/50architecture/2328tests及lint/typecheck/build通过，独立0、八hash匹配。format脚本N/A；候选未提交发布/纳入Root gitlink，T-U01浏览器另行未验。E37真实RED历史保留 |
| T-Q02 | BFF | 本仓format/lint/types/unit/contract/architecture/build；跳过逐项说明 | 通过 | E01：仅BFF离线纯门 |
| T-Q03 | Agent | uv锁与frozen依赖/Ruff/Pyright/pytest/wheel；HTTP contract与架构；skip说明 | 待复测 | E30限定纯门、E32 fresh schema7、E35真实PG65与独立0通过；frozen sync/archive隔离/owner HTTP/安装后smoke/retention/发布及消费者仍未验，不能宣称完整Agent闭环 |
| T-Q04 | IAM | 本仓format/lint/types/unit/contract/architecture/build；跳过逐项说明 | 通过 | E14：Root本次verify938通过；仅该纯门，host51另记有限资源证据，非全部IAM integration/登录 |
| T-Q05 | System | 本仓format/lint/types/unit/contract/architecture/build；跳过逐项说明 | 待复测 | 历史门不能证明新组合；按owner ACCEPTANCE重跑 |
| T-Q06 | Billing | 本仓format/lint/types/unit/contract/architecture/build；跳过逐项说明 | 待复测 | 历史门不能证明新组合；按owner ACCEPTANCE重跑 |
| T-Q07 | Platform | 本仓format/lint/types/unit/contract/architecture/build；跳过逐项说明 | 待复测 | 历史门不能证明新组合；按owner ACCEPTANCE重跑 |
| T-Q08 | Storage | 本仓format/lint/types/unit/contract/architecture/build；跳过逐项说明 | 待复测 | 历史门不能证明新组合；按owner ACCEPTANCE重跑 |
| T-Q09 | Scheduler | gofmt/vet/test/build；OpenAPI/event protocol/schema/架构；skip说明 | 待复测 | 历史门不能证明新组合；按owner ACCEPTANCE重跑 |
| T-Q10 | Root | 精确gitlink、main-only、发布contract/version/digest/client drift、fresh clone | 待复测 | E12原IAM缺提交分支已由E14发布及同fresh目录真实初始化0关闭，E13消费RED已由E15收口；新Root组合及完整fresh/主分支检查仍待验，不计整行通过 |
| T-Q11 | Root | 发送失败诊断有界/脱敏、两轮归属、失败仍非零退出、原硬断言不变 | 通过 | E36：Root61613当前550纯测通过/9.25s、Nodecheck0、独立最终0；原actual finished wrapper/race/invalid messages/0/1计数漏测已补，不等于发送成功 |
| T-Q12 | 各数据owner | 同应用库独立schema fresh install/drift/拒重入/零跨owner SQL/失败回滚 | 未验 | E32仅Agent fresh install/拒重入/catalog drift7通过；未证明所有数据owner单应用库组合与零跨owner访问，逐owner继续验证 |
| T-L01 | IAM→Web→BFF | 真实IAM表单→授权→callback→HttpOnly session→/app；无中转/整页重试 | 待复测 | W1C/W1D历史隔离浏览器证据；新组合正式旅程未验 |
| T-L02 | IAM→Web→BFF | 错误密码/CSRF/state/nonce/PKCE/redirect篡改拒绝且无session | 待复测 | W1C/W1D历史隔离浏览器证据；新组合正式旅程未验 |
| T-L03 | IAM→Web→BFF | 刷新/到期/退出/退出后重登与后退；禁止过期签名URL无限重试 | 待复测 | W1C/W1D历史隔离浏览器证据；新组合正式旅程未验 |
| T-L04 | IAM→Web→BFF | 固定tenant准入、撤销/禁用、同tenant另一用户及跨tenant隔离 | 待复测 | W1C/W1D历史隔离浏览器证据；新组合正式旅程未验 |
| T-L05 | IAM→BFF→Web | 成员/邀请/角色权限与审计：读写、分页、重复命令、撤权即时失效；无管理员越权 | 待复测 | W1C-Team历史owner切片，当前完整用户权限矩阵待复测 |
| T-C01 | BFF | 独立/project/全集列表、tie keyset limit1/2、跨主体/租户/deleted、冲突400 | 通过 | E03：真实PG+生产HTTP，仅后端过滤切片 |
| T-C02 | Web→BFF | 新建独立/项目会话、URL/back/forward/刷新、草稿和消息不串scope | 未验 | 先Web固定BFF6，再真实浏览器 |
| T-C03 | Web→BFF | 重命名/删除等待ACK；延迟/503/切换scope不复活、不污染新页 | 未验 | R82已知delete fire-and-forget竞态 |
| T-C04 | BFF→Web | 显式分享/撤销；私有链接不冒充公开分享；另一用户不可读/控制 | 未验 | R82分享文案与真实权限不一致；正负例都需验 |
| T-C05 | BFF→Web | 移动/归档/删除项目时会话、活动Run、任务及作品的生命周期 | 阻塞 | 产品删除/移动规则与正式API未裁决；不猜级联行为 |
| T-C06 | Root六owner | 正式登录后两轮真实模型聊天：两POST/四Message/全文/刷新/作品hash/他人404 | 失败 | E40：Root2472a05d六发布owner原31330已exit1；第二轮活动观测snapshot GET可解析JSON非200，last-success为active-match/4messages/pending-empty，未见finish。具体status/code待诊断，不推断根因；cleanup=[]。E39启动及E28/E17/E04历史保留，不含Billing或Agent5候选 |
| T-C07 | BFF→Agent | 同会话FIFO/同key重放/双tab同时提交；一活动head，无重复执行 | 未验 | 队列正常也须竞争负例；跨会话允许并行 |
| T-C08 | Web→BFF→Agent | Stop/steer/取消/重复控制；ACK不冒充terminal，输入和队列正确收口 | 未验 | 按现owner契约；资源验收不能用UI按钮存在替代 |
| T-C09 | BFF→Web | 活动/终态刷新：同事务Message/执行head/过程与event_watermark一致 | 未验 | 完整用户旅程仍未通过 |
| T-C10 | BFF→Web | SSE断线/cursor replay/重复/间隙/过期与GC；不丢字、不双气泡 | 未验 | 真实断连/重启，禁止localStorage成为事实源 |
| T-C11 | Web | 同scope真实重挂/双owner/StrictMode；最后卸载才close SSE；injected不被释放 | 通过 | E11：Root真实RED→完整门及独立审，已提交/推送a52a623；仅生命周期组件切片，不证明W2 |
| T-P01 | BFF→Scheduler→Agent | 独立任务不进入会话列表；project_id仅关联；创建/修改/暂停/删除/权限 | 未验 | 按现ScheduledTask/Occurrence owner契约，真PG/Redis/HTTP组合 |
| T-P02 | BFF→Scheduler→Agent | IANA timezone/DST、周期/一次、边界时间与misfire | 未验 | 按现ScheduledTask/Occurrence owner契约，真PG/Redis/HTTP组合 |
| T-P03 | BFF→Scheduler→Agent | 重复唤醒/投递、幂等receipt、ACK unknown与Outbox恢复 | 未验 | 按现ScheduledTask/Occurrence owner契约，真PG/Redis/HTTP组合 |
| T-P04 | BFF→Scheduler→Agent | 进程崩溃/lease到期/重启、旧worker失fence；不重复Occurrence执行 | 未验 | 按现ScheduledTask/Occurrence owner契约，真PG/Redis/HTTP组合 |
| T-P05 | BFF→Scheduler→Agent | 暂停/删除不伪造已接纳任务终态；串行dispatch/Agent terminal释放 | 未验 | 按现ScheduledTask/Occurrence owner契约，真PG/Redis/HTTP组合 |
| T-F01 | Storage→BFF→Web/Agent | 个人与项目上传：真实字节/MIME/大小/clean scan/感染与取消 | 待复测 | W2个人上传下载有历史切片证据；完整新组合待验 |
| T-F02 | Storage→BFF→Web/Agent | 附件列表/分页/重启读取/下载hash；他人及跨project拒绝 | 待复测 | W2个人上传下载有历史切片证据；完整新组合待验 |
| T-F03 | Storage→BFF→Web/Agent | Agent生成作品→Storage receipt→卡片/预览/下载→刷新仍同作品 | 未验 | 真实ObjectStore/scanner/receipt；不以fixture作品冒充 |
| T-F04 | Storage→BFF→Web/Agent | 失败发布/超时/URL过期/重试：不生成伪作品、不泄密、不重复完成 | 未验 | 真实ObjectStore/scanner/receipt；不以fixture作品冒充 |
| T-F05 | Storage→BFF→Web/Agent | 删除/retention/引用保护/GC，有限回收只删本owner资源 | 未验 | 真实ObjectStore/scanner/receipt；不以fixture作品冒充 |
| T-K01 | Web | Plugins无owner回执时不出现本地Add/Remove/Connected假成功 | 通过 | E06：已发布5e538f69，两组件/test字节仍匹配；不等于MCP接通 |
| T-K02 | Platform→Storage→BFF | Skill草稿/整包上传/校验/发布/读回；恶意ZIP与非法路径拒绝 | 待复测 | W3历史owner组合证据；按当前pin复跑 |
| T-K03 | Platform→BFF→Web | 个人安装/启用/禁用/移除/重装持久；版本/重复/另一用户拒绝 | 待复测 | 已有personal installation切片；新组合待验 |
| T-K04 | Web→BFF→Agent | Composer选择精确Skill refs→提交冻结→真实加载；禁用/撤权拒绝 | 未验 | formal selector与执行展示未贯通 |
| T-K05 | Platform→BFF→Web | MCP connect/scopes/授权回执/撤销/需重连；目录不等于连接 | 未验 | 正式管理mutation与凭据/audience边界待实现发布 |
| T-K06 | Web→BFF→Agent→Platform | MCP opaque refs选择、每次调用fresh授权、args identity；撤销零调用 | 未验 | 旧free-text mcp_servers需owner-first替换，无fallback |
| T-K07 | Platform→Agent | 工具schema closed profile/输入输出校验/超时取消/越权/注入 | 未验 | 不能把协议profile文档当执行测试 |
| T-A01 | Agent→BFF→Web | 简单聊天只回复；复杂任务Todo完整表更新、不被子Agent覆盖 | 未验 | E35 Root真实PG65pass/独立0（原59+新增完整/空Todo、并发lostACK、漂移、围栏/expiry/terminal、live失败耐受6项）；owned库回收0；BFF/Web安全过程呈现与复杂任务策略未验，不关闭整行 |
| T-A02 | Agent→BFF→Web | 真实Skill resolving/loading/ready/failed；不从选中状态伪造已加载 | 未验 | E09：Root R90已裁定枚举/字段/容量/轮次身份；原owner四D0收敛待核，机器/运行链尚无本切片业务测试 |
| T-A03 | Agent→BFF→Web | 友好tool running/completed/failed摘要；无raw args/result/stack/token/隐藏推理 | 未验 | E09：Root R90已裁定枚举/字段/容量/轮次身份；原owner四D0收敛待核，机器/运行链尚无本切片业务测试 |
| T-A04 | Agent→BFF→Web | 完整多项HITL pause→一次决策→resume；stale/重复/unknown/刷新正负例 | 未验 | E09：Root R90已裁定枚举/字段/容量/轮次身份；原owner四D0收敛待核，机器/运行链尚无本切片业务测试 |
| T-A05 | Agent→BFF→Web | Todo/Skill/tool/HITL/delivery五时点刷新：恢复同水位，无重复或丢失 | 未验 | E09：Root R90已裁定枚举/字段/容量/轮次身份；原owner四D0收敛待核，机器/运行链尚无本切片业务测试 |
| T-A06 | Agent→BFF→Web | 子Agent身份/状态/失败/取消/汇总；不混入主回复或泄露私有过程 | 未验 | E09：Root R90已裁定枚举/字段/容量/轮次身份；原owner四D0收敛待核，机器/运行链尚无本切片业务测试 |
| T-B01 | Billing | 定价revision纯codec：strict格式/不可变摘要/整数/rational/边界/恶意结构 | 通过 | E07：772 unit/静态通过，仅冻结3文件；未验真实收费 |
| T-B02 | System→Agent | 实际provider/model/route revision绑定；逐call/attempt证据，不补零/猜用量 | 未验 | ADR-033；System仅技术路由，Agent仅事实证据 |
| T-B03 | Billing→BFF→Web | 授权赠送/余额/流水/撤权；前端只读owner结果，无假充值/免费补偿 | 未验 | 真实Billing命令+持久ledger；不直接改数据库充当授权 |
| T-B04 | Billing→Agent | provider调用前预占、余额不足、并发预算、同key重放、ACK unknown恢复 | 未验 | 实际attempt授权，禁止一次许可放行整Run |
| T-B05 | Billing | 采购成本×冻结可配置7/5倍率、币种积分换算/舍入/版本；前端零独立计价 | 未验 | ADR-033；7/5是加价40%，不是净利润率 |
| T-B06 | Agent→Billing | 真实usage→幂等结算/增额/释放/对账；超时、失fence、晚结果不重扣 | 未验 | 未知成本保留reconcile，不把Run terminal当费用结案 |
| T-B07 | Billing | 失败/取消/部分输出/未知成本的收费资格与账务分支 | 阻塞 | 收费业务策略待确认；不预设一律免费、一律release或一律收费 |
| T-B08 | Billing | 支付/订阅/checkout/refund/webhook验签去重及sandbox对账 | 后置 | 用户已明确支付最后；渠道配置属运维，不阻当前聊天研发 |
| T-U01 | Web | Home提示只填草稿、零自动POST/计费；真实模型/套餐/能力，无错误营销卡 | 未验 | E33局部发布/E37语义11真实RED/E41候选完整純门接受，网站/More/零POST正控保护；新候选发布、Root组合及完整Home真实浏览器未验 |
| T-U02 | Web | Composer多行/中文输入法/Enter与Shift+Enter/附件/发送禁用与Stop；无内嵌方框 | 未验 | 真实浏览器+截图/axe/视觉；UI纯测或借用shadcn不替代验收 |
| T-U03 | Web | 桌面与窄屏对话/侧栏/项目/作品布局，长文本/代码/表格/错误均可用 | 未验 | 真实浏览器+截图/axe/视觉；UI纯测或借用shadcn不替代验收 |
| T-U04 | Web | 键盘/focus-visible/axe/reduced-motion、全部loading/empty/error/partial状态与视觉/bundle门 | 未验 | 真实浏览器+截图/axe/视觉；UI纯测或借用shadcn不替代验收 |
| T-R01 | Root | 本次BFF隔离测试临时库精确创建/删除、无共享PG/Redis reset | 通过 | E03：removed=true/cleanup=[]；仅该run，不代表全进程治理 |
| T-R02 | 各owner→Root | 实际进程启动/health/ready/超时/取消/graceful shutdown/worker drain/故障恢复 | 未验 | 原句柄追踪、不重复启动、不把观察超时当进程已停 |
| T-R03 | Root/各owner | 权限矩阵/输入边界/敏感日志/依赖secret/source扫描/跨owner禁止访问 | 未验 | 同tenant不同人+跨tenant正负例；报告不含凭据 |
| T-R04 | Root | 全owner当前门+组合真实E2E+隔离fixture backup/restore（持久事实/幂等/未决outbox恢复）+可追溯release smoke/image SHA清单 | 未验 | Wave7最终研发验收；SLO目标不冒充压测，不扩展部署运维 |
| T-S01 | System→IAM/BFF | Site/Host/Workspace/Runtime/Policy具名身份与生命周期；disabled/unknown/expired拒绝、secret零泄漏 | 未验 | owner HTTP/PG→消费者，不建任意配置桶 |
| T-S02 | System→Agent/BFF | 模型目录/选择/路由revision与digest；实际gateway/credential；重试故障不静默换未授权模型 | 未验 | 技术配置不等于实际调用证明；消费固定owner artifact |
| T-G01 | Platform→BFF/Agent→Root | capability到platform身份/Proto/remote/path/env/DB/Redis一次cutover；旧alias/fallback删除 | 未验 | Wave3正式验收，现物理仍kokoro-capability，不冒称已改名 |

## 九owner验收层级覆盖（同一任务矩阵的覆盖检查，不另算完成数）

|Owner|纯门/契约|真实依赖integration|实际进程smoke|跨owner/浏览器消费|
|---|---|---|---|---|
|Web|T-Q01冻结候选限定纯门通过（E41），未发布；E20/E22失败历史保留|无业务数据库；真实session/adapter待验|T-R02未验|T-L/C/K/A/U未验或最近失败|
|BFF|T-Q02通过限定纯门|T-C01过滤切片通过；全owner资源套件未验|T-R02未验|T-Q10/T-C02 Web消费者未验|
|Agent|T-Q03待复测|真实PG/Redis/checkpointer/lease待验|T-R02未验|真实模型T-C06最新E40失败；安全过程T-A未验|
|IAM|T-Q04本次通过限定纯门|现host51通过；全部真实schema/PG/Redis/OAuth矩阵待复测|T-R02未验|T-L固定tenant浏览器链待复测|
|System|T-Q05待复测|真实PG/HTTP/身份/路由T-S未验|T-R02未验|BFF/Agent实际绑定T-S02未验|
|Billing|T-Q06待复测；T-B01纯codec通过|真实钱包/ledger/T-B03–07未验或决策阻塞|T-R02未验|正式收费未验；支付后置|
|Platform|T-Q07待复测|真实PG/IAM/Storage/Connect授权待验|T-R02未验|Skills/MCP使用T-K未验；身份cutover T-G01未验|
|Storage|T-Q08待复测|真实PG/ObjectStore/scan T-F待复测/未验|T-R02未验|BFF/Agent/Platform新组合未验|
|Scheduler|T-Q09待复测|真实PG/Redis/lease/outbox T-P未验|T-R02未验|BFF callback/Agent dispatch未验|

## 已执行证据与版本绑定

|证据|绑定版本/范围|实际结果/存档入口|
|---|---|---|
|E01|BFF bb610ea production冻结源；本轮Root check/format/schema|contract231pass；unit688pass/0fail/1既定资源skip（含28architecture）；schema8pass/0fail/1资源skip；静态/build0。R87 progress、/tmp/kokoro-r87-root-bff-{check,format,schema}.log。未跑完整owner integration|
|E02|Root诊断3c94bea9；driver6275077b/test1cd84579冻结hash本次仍匹配|575pass/98subtestpass/0fail；R86 progress、/tmp/kokoro-r86-root-diagnostic-adjacent-confirmed.log。诊断不是聊天修复|
|E03|BFF bb610ea，public6 canonical75ef9f7a；真实PG/HTTP过滤|1pass/0fail/0skip；本次独有临时库删除确认，cleanup=[]；R87 progress、/tmp/kokoro-r87-bff-direct-pg.tap、/tmp/kokoro-r87-bff-owned-resource.json。IAM为测试替身，不是登录E2E|
|E04|Root d52da34/Web52fdd8e/BFFb1ea063原W2六owner旅程|exit1，REAL_MODEL_FAILURE:product-send-click；R84 progress、/tmp/kokoro-r84-root-real-w2.log，evidence /Users/nako/WebstormProjects/github/thefoxfairy/kokoro-w2-web-project-u2fpdtuc.evidence.json。本行是最近失败，不声称新组合也已测|
|E05|Web5e538f69+tests-only frozen2fd0d1ed；修复尚未验收|Root1fail/1pass/88filtered；/tmp/kokoro-r87-root-web-lifecycle-red.log。真实旧cleanup处置新owner，但fixture仍1POST，非W2根因证明|
|E06|Web5e538f69 Plugins/source+test两字节本次与commit匹配|Root发布前完整check2299test/246contract/50architecture及静态/build0；R85 progress、/tmp/kokoro-r85-root-web-truth-full-check.log。当前全Web dirty，不能沿用全仓GREEN|
|E07|Billing e04bff9+3纯codec未发布，完整hash记录在R86证据|24files772unit pass/0fail/0skip，format/lint/两个no-emit门0；/tmp/kokoro-r86-root-billing-verification.json及对应log。无DB/provider/真实扣款|
|E08|Web5e538f69+冻结生命周期3文件；完整SHA记录在R89 progress|Root Node22 pnpm check exit0：246contract/50architecture/2302tests，lint/typecheck/build通过；/tmp/kokoro-r89-root-web-lifecycle-check.log，原28836已终态。独立审0P0/1P1/0P2，/tmp/kokoro-r89-web-lifecycle-final-review.md；未commit render仍泄漏资源，T-C11不关闭。未执行本轮format、真实浏览器或W2|
|E09|Agent17c73541+冻结安全过程四文档D0；仅设计审查|独立审0P0/1P1/0P2；/tmp/kokoro-r89-agent-progress-d0-review.md。四hash/旧全文/370外围保护匹配；R90 Root已裁定闭集并经独立0/0/0复核，owner四D0收敛/运行测试仍待验，无本切片业务测试通过|
|E10|Web5e538f69+tests-only cb138727；production仍E08的8ceb/9428|Root Node22原12482实际exit1：2failed/91filtered，/tmp/kokoro-r90-root-web-aborted-render-red.log；aborted render factory/storage/snapshot/SSE各1与cache残留，delayed commit前factory/storage各1。fake一次POST正常，不称W2根因；已授原writer精准GREEN，尚未最终验收|
|E11|Web正式a52a6230e4f8e54f95b1f0322adbf1f187aacaae；三source/test hash见R90 progress与review|Root Node22原47394实际exit0：246contract/50architecture/2306tests及lint/typecheck/build；/tmp/kokoro-r90-root-web-full-check.log。独立Sol0P0/P1/P2，/tmp/kokoro-r90-web-final-review.md；原P1闭合，四路径精确提交/推送；无format脚本，未做本轮浏览器/W2|
|E12|Root已发布eaeaa86b4d92b44c1a70789b95e0219651f191e9；独立fresh Root与六owner初始化|原86929终态exit128；Root clone成功、六owner初始化在IAM gitlink获取失败，远端返回not our ref。/tmp/kokoro-r92-w2-source-prep.json与.log；当时phase=source-preparation-failed，runtime_resources_created=false，原失败保存attempts；R93同目录复跑结果见E14，原日志不删除。非新一轮聊天运行失败|
|E13|Web a52a623+R91冻结五D0/八测试；仍旧public5 snapshot，目标已发布BFF bb610ea/public6|Root原81402终态exit1：8测试文件、13失败/123通过/136总计，2.52s；/tmp/kokoro-r92-root-web-public6-red.log。消费版本/digest/scope契约RED真实成立，尚未完成生成GREEN，不增加测试组数或当作用户聊天通过|
|E14|IAM实现e3c035b不变；只doc新70a2b01554eee39520a9dc2b27cbb649954cf413普通推送远端main|Root Node24原27902完整verify exit0：102files938pass0fail0skip及format/lint/types/contract/breaking/SDK/build；/tmp/kokoro-r93-root-iam-verify.log。原73738现host真实PG/Redis51pass0fail0skip/71.80s，/tmp/kokoro-r93-root-iam-host.log；独立Sol最终0，/tmp/kokoro-r93-iam-publish-final-review.md。原54930同fresh目录六owner初始化exit0，manifest attempts保原失败；运行资源仍未创建，非浏览器登录|
|E15|Web正式a6c651b1c22a86cacfe282486193d743fca3ca3a；正规BFF bb610ea/public6 canonical75ef消费|Root Node22原81297完整pnpm check exit0：249contract/50architecture/2309tests（163files）及lint/types/build；/tmp/kokoro-r93-root-web-public6-check.log。独立Sol0及17授权/735外围hash与owner原bytes匹配，/tmp/kokoro-r93-web-public6-review.md；Root仅补CURRENT摘要后精确17路径commit/push。Team15/lifecycle三源不变，无format脚本N/A；不替真实Web→BFF列表或W2|
|E16|Root6d68bcc3+两gitlink Weba6c651b/BFFbb610ea及235已发布来源迁移；其余owner pin不变|原70947三组合pure测试终态exit0：95pass/0fail/48.88s，/tmp/kokoro-r93-root-composition.log；topology PASS，compat原99544 exit1仅13declaredbroken/16edges/0violations，无新错误。独立Astra0，304引用/234去重blob核正确，/tmp/kokoro-r93-composition-review.md。仅来源组合验收，最终fresh与浏览器/广泛契约边仍待验|
|E17|Root820eb8c472936d5accdd05e8ac92439f38eea3a6；六发布owner pins见owned manifest；600s严格两轮旅程不变|原3023/PID47969已终态exit1：REAL_MODEL_FAILURE:product-send-click-t2-req0-res0-fail0-net-none-ui-blocked-admission-rejected-conn-reconnecting；/tmp/kokoro-r93-root-real-w2.log、/tmp/kokoro-r93-root-w2-owned.json及其中evidence。cleanup=[]，bucket_cleanup_exit=0且删除后404确认；不含Billing收费，不把第二轮失败之前的步骤计成整组通过，具体根因待定位。|
|E18|Web a6c651b+R94 tests-only f45cd3f610；生产候选当前0928eaa5，完整hash见progress|Root原12962 exit1：134项1fail/133pass，1.05s；/tmp/kokoro-r94-root-web-second-send-red.log。终态quiet snapshot后连接残留reconnecting、第二submit false且仅1POST；successor/failed/null控制仍有效。候选已交接，不表示真实浏览器复测通过|
|E19|Agent17c73541+R93冻结源0295ba70及R94两追加测试84f16d8e/e2c35c7e|Root32024源阶段1397pass/1skip/18deselected，51793静态0；独立审0P0/2P1/0P2。追加回归Root71909 exit1：4fail/104pass/4deselected；/tmp/kokoro-r94-root-agent-failure-red.log。worker新候选f0cdcdf1/930c8611报108focused/1406unit通过，原WIN03 idle，manifest /tmp/kokoro-agent-r94-green-h75elxn2/manifest.json；尚未Root复验，不计任务通过，无真实PG|
|E20|Root c76195bc工作树；Web a6c651b+machine0928eaa5/test f45cd3f610冻结候选|原58933实际exit1：249contract/50architecture、lint/types通过；163files unit2312pass/1fail。失败tests/ui/app-frame.smoke.test.tsx:1215，欢迎页重进后预期/app/project/project_welcome-a，实为/；build因前项失败未执行。/tmp/kokoro-r94-root-web-full-check.log SHA256 8a7c92a0d06030e3b9e4e241fc01ae1a547e1464d231802584f90aaa274c91e4。失败类别待定位，禁止worker GREEN替Root失败或称修复已发布|
|E21|Agent17c73541+冻结R94源 f0cdcdf1/930c8611；两RED tests84f16d8e/e2c35c7e，374文件门前门后匹配|Root76640实际exit0：focused108pass/4deselected、隔离unit1406pass/1skip/18deselected，Ruff/267format/Pyright0；/tmp/kokoro-r95-root-agent-source-gate.log。独立Astra0P0/P1/P2，/tmp/kokoro-r95-agent-source-final-review.md，两P1闭合。contract-check另实际exit1 provenance stale /tmp/kokoro-r95-root-agent-machine-baseline.log；源阶段接受，不计整仓/PG/发布通过|
|E22|Web a6c651b+两冻结engine候选0928eaa5/f45cd3f610，Root402df94d|原25421完整app-frame95pass/exit0/7.65s；原55271单worker全Vitestexit1、163files2312pass/1fail/207.09s，仅OIDC pending-refresh tombstone30s超时。/tmp/kokoro-r95-root-web-project-smoke.log与/tmp/kokoro-r95-root-web-unit-single-worker.log；原E20不删、不称完整check/build成功。Sol只读安全diagnostic缺口0P0/1P1/0P2，/tmp/kokoro-r95-web-http-failure-read.md，产品或fixture归因待实际诊断|
|E23|同Web候选、原OIDC测试未修改；独有temporary Next/端口与精确状态清理|Root23020定点pending-refresh例实际exit0：1pass/38名称过滤skip/5.87s；/tmp/kokoro-r95-root-web-oidc-focused.log。单例通过不关闭完整文件顺序超时；原WIN01仅测试诊断后继。不以过滤skip当其余38通过|
|E24|Web正式85403f340b6565aeb11d9aa6f90ea7d2ff906fe6；OIDC诊断独立commit6da8602；production0928eaa5/engine test f45cd3f610/OIDC test8cb206b0|Root原29612完整pnpm check终态exit0：249contract/50architecture、163files2313tests、lint/typecheck/build通过；/tmp/kokoro-r95-root-web-final-check.log SHA256 ed7c2ad16fa901b248400e428cb6484407ab8f48e189c22b96c171d2c86aa1f7。独立Sol0P0/P1/P2 /tmp/kokoro-r95-web-final-review.md。Root原77117精确两commit/普通push exit0，现HEAD=origin/main且clean；format脚本N/A。E20/E22不删；Root gitlink/provenance尚旧、真实W2与Billing不计通过|
|E25|Agent17c73541+冻结两contract tests c3fd0e5d/d1267230，源阶段E21不变；manifest8c72ba7e|Root原55117终态exit1：132fail/92pass/1.94s；/tmp/kokoro-r95-root-agent-machine-red.log SHA256 5a3fcdc9c60800987986536ead4bd3ce3d4f7eb0aefba326084372b3a3f7975b。独立Astra0P0/1P1/0P2 /tmp/kokoro-r95-agent-machine-red-review.md；真实版本/闭集映射/非法字段RED，1P1是raw duplicate-key与canonical预算未走owner checker。初13case503/误连尝试及Root相对路径setup错误不算行为RED；最终guard隔离、374hash/372外围保持。机器GREEN/真实PG/发布未完成|
|E26|Root d7775567+Web gitlink85403f3和49发布blob来源候选；其他owner pin不变|Root原49710终态exit0：95pass/0fail/42.58s；/tmp/kokoro-r97-root-composition.log SHA256 7225a21f3318fd8d7f2e13349970e01eebc925e76e92fad625b356af100ead27。topology PASS，compat exit1仅13declaredbroken/16edges/0violations；独立Astra0P0/P1/P2、49refs/45blob匹配；此为发布前证据，fresh/新W2待验。T-Q10整体仍待复测，不用组合纯门关真实聊天|
|E27|已发布Root88a874174f6daa9d0464fed17f2bf4f2a39c0e62与六owner精确pins见owned manifest；Web85403f3，Agent仍17c73541|原97257同fresh源准备exit0；原3421/child PID4643实际live经ps确认，/tmp/kokoro-r97-root-real-w2.log及owned.json。原harness/600s/两POST四Message/刷新/全文/作品hash/他人404/回收不变；新独有bucket创建通过，未终态，T-C06执行中，原E17失败保留；不含Billing收费|
|E28|正式Root88a87417/Web85403f3、其他五owner同E27 pins；严格600s/原harness不变|Root原3421/PID4643终态exit1，REAL_MODEL_FAILURE:second-partial-active；/tmp/kokoro-r97-root-real-w2.log SHA256 610783f465a5475280dac704b08540aa7d8ee30fd65a9152690864b6b41de31c、/tmp/kokoro-r97-root-w2-owned.json及其中evidence。越过second submit/receipt，但partial active读取/活动刷新及后继完整链未通过；catch仅给阶段，不断言具体根因。cleanup=[]/独有桶清理exit0且404；不含Billing收费，T-C06失败、原E17/E27记录保留|
|E29|Web85403f3+Home tests-only三冻结文件，基线与hash见/tmp/kokoro-r97-web-home-red-final.json|Root原93588 exit1，7fail/135pass/142total/9.64s；/tmp/kokoro-r98-root-web-home-red.log。草稿/无owner套餐/假档位行为RED成立。后继worker局部GREEN141pass/1旧假模型断言冲突，仅待验交付；/tmp/kokoro-r98-web-home-green-blocked.json，不代Root完整门或浏览器|
|E30|Agent17c73541+冻结机器候选manifest b72cf61a；8路径匹配，独立审绑定同diff40c72ba7|Root原28685终态exit0：contract654pass/1资源deselected/10.11s，隔离unit1406pass/1skip/18deselected/84.83s；uv lock/checker/codegen/Ruff/267format/Pyright0/build通过。/tmp/kokoro-r98-root-agent-machine-gate.log为原句柄捕获输出，工具截断中间build复制行，未伪造完整原始日志。独立Sol0P0/P1/P2 /tmp/kokoro-r98-agent-machine-final-review.md；本次未执行frozen sync，archive模块收集前排除避免资源访问；真实PG/HTTP/发布/下游未验，T-Q03不关闭|

|E31|Agent17c73541+冻结R94源/R97机器；三个既有真实PG integration文件，源码总digest afc3b6680af427c14fb255887b10c34ad73d7d8ea1b24d7d39f365a4f2785991|Root原69992终态exit0，59pass/55warnings/7.48s；uv run --offline --no-sync --frozen pytest -m integration执行test_run_outbox_filter/test_run_interaction_transactions/test_delivery_outbox。/tmp/kokoro-r99-agent-owned-pg.json与.log SHA616f37fe5923d43cc9b4d6e63e03c63a74859faadb6b2c452c42cbc1d1c68461；独有临时fixture库created/deleted均true、cleanup=[]、源hash不变，无Redis/ObjectStore/provider服务；不含尚在追加的Todo专属测试|
|E32|同Agent冻结源；唯一canonical schema现测试test_schema_installation.py|Root原2035终态exit0，7pass/0.76s；fresh install/拒重入/六catalog drift分支。/tmp/kokoro-r99-agent-schema-pg.json与.log SHA63aef428b6b6cdf5d5276d6deb64de6d8cbc4b0909961118f54dc0b91dd2df15；独有fixture库created/deleted=true、cleanup=[]、源不变。仅Agent schema文件，不代表九owner应用组合|
|E33|Web正式main b49797b1e8ee659b7593429aa09e9455a3ad5485=origin/main且clean；Root gitlink仍85403f3|Root原21275终态exit0：完整pnpm check249contract/50architecture/163files2320tests及lint/typecheck/build；/tmp/kokoro-r99-root-web-home-check.log，752冻结hash前后不变；独立审/tmp/kokoro-r99-web-home-final-review.md 0P0/P1/P2。原81868普通push exit0；format脚本N/A；首次Root cwd check不存在为setup错误非产品RED。Home语义错配/真实浏览器/Root新组合仍未验|
|E34|Root569b7d6b+诊断driver c65d7e8a75ffc775b13e6afd427fc223f1221921f3f108e45c0923f86dd970b5/test257c22489ea668bbcda8e8a40cf76ac48c098f8d886f54cc6538616fa329128f；未提交候选|Root原新15项12fail/3pass/531filtered、exit1，/tmp/kokoro-r99-root-partial-red.log；worker GREEN manifest/tmp/kokoro-r99-partial-diagnostic-green.json报546纯测通过，Root尚未重跑/最终审查。runner/helper冻结、不新启动资源、不放宽严格旅程；T-Q11移待复测，T-C06仍E28失败|

|E35|Agent17c73541+R94/R97冻结源与Todo test f1e20936e5a7e9be7156ec97ada6236171b8374b558860a3f959dccddcd90666|Root85723终态exit0，三个integration PG文件65pass/55warnings/10.11s（原59+新6）；/tmp/kokoro-r101-agent-todo-pg.json/.log，SHAe8352ce1c6362577a4353ae884934e65597951c2357bc72cf062e492f16f533a；created/deleted=true、cleanup=[]、源hash不变。Root静态36406 format/lint/Pyright0，独立/tmp/kokoro-r101-todo-pg-review.md 0P0/P1/P2。系统Python缺psycopg首轮为setup错误、未访问资源；随后现Agent venv正确执行。只PG/live边界故障，不称真实Redis/BFF/Web通过|
|E36|Root3f70b7a2+diagnostic driver c65d7e8a/test dfe9ec93a671abbc4428605e0ac2eb0c62ead91cb269b3be6244801d2dc203f0，runner/helper不变|Root67847原546pass/8.61s后独立1P1/1P2发现harness缺actual finished race及非array/0/1向量；原WIN10仅test追加4向量、原expected0改动，Root61613终态550pass/9.25s、Nodecheck0，/tmp/kokoro-r101-root-diagnostic-final.log。最终独立审/tmp/kokoro-r101-diagnostic-final-review.md 0P0/P1/P2；只关闭T-Q11诊断，不改变T-C06产品失败或600s/原硬门|
|E37|Web正式b49797b1+仅三tests RED 607ba25f/92e0d886/5b437bf5，四source/share冻结|Root28466三聚焦Vitest真实exit1：11fail/142pass/153total/7.96s，/tmp/kokoro-r101-root-home-semantics-red.log；三主卡草稿/描述、三个新keys/九locale缺口成立，网站/More/零POST正控通过。原worker额外全unit2320pass但shell status保留变量exit1为setup；不当本次阶段验收。现四source GREEN在途、T-U01未关，无浏览器证据|

|E38|Root3f70b7a2+精确8路径stage：Web gitlinkb497/49commit refs和诊断两文件/四台账；其他owner不变|Root67468终态386pass/47.22s/exit0，/tmp/kokoro-r101-root-composition-final.log SHAcf7b37770df0495ed18d40b235dbd941715f8babeb20b1f9b1292e861c626915；topology-final PASS、compatibility-final exit1仅13declaredbroken/16edges/0violations，独立0，49refs/45blob核实。首84178 1fail/385pass和prestage旧gitlink导致50额外unexpected errors保留；不改checker清零，实际发布/fresh旅程后继，T-Q10整组仍待复测|

|E39|已发布Root2472a05d1f6ac086be57d12c6044df535c7e599f/六owner pins见/tmp/kokoro-r101-root-w2-owned.json，Webb497，Agent仍17c73541|源准备原87477 exit0/全clean+精确gitlink+四harness hash；原31330/child PID75097真实live经ps核，/tmp/kokoro-r101-root-real-w2.log与owned.json；模型库存preflight通过/无pull/独有桶创建通过。600s与原两POST四Message/活动硬reload/全文/作品/隐私/清理不变，未终态，T-C06执行中，E28历史保留；非Billing收费或新Agent5消费验收|
|E40|已发布Root2472a05d/六owner同E39；Webb497，严格旅程断言不变|Root原31330/PID75097终态exit1；REAL_MODEL_FAILURE:second-partial-active-cause-snapshot-http-head-active-match-messages-4-partial-pending-empty-finish-absent。/tmp/kokoro-r101-root-real-w2.log SHAa955f0233490d444f0a400aee35767e9d516fc937b367d89012b209c351ba851、owned.json及其中evidence；cleanup=[]/bucket_cleanup_exit0。只读调查/tmp/kokoro-r101-snapshot-http-read.md确认可解析JSON非200，具体status/code无证据。E39仅启动时记录，不是当前live；不含Billing收费或新Agent5消费|
|E41|Webb497+Home七冻结文件，manifest /tmp/kokoro-r101-home-semantics-green.json SHA7675335b7b1fe4338f942b70ed4a78d15e32806cbcc1b97c211a8246ada7934b；候选未提交发布|Root原84433完整pnpm check终态exit0：249contract/50architecture/163files2328tests、lint/typecheck/build；/tmp/kokoro-r101-root-home-final-check.log。独立/tmp/kokoro-r101-home-final-review.md P0/P1/P2均0；本次8源/测试保护hash仍匹配。原E37 RED保留，format脚本N/A。仅T-Q01纯门，T-U01真实浏览器/Root新组合未验|

`/tmp`是当前机器运行证据位置，不保证永久保留；本页与progress已提交保存版本、结果与失败分类。后继运行须在同progress追加脱敏摘要，长期验收报告归既有reports目录；不得仅留临时路径或截图口头宣称。

## 每次执行/复测必须填写

```text
测试ID / owner / 执行者 / 时间
基线commit与当前dirty范围（必要时冻结SHA256）
资源与环境 / 命令或浏览器入口与步骤
预期 / 实际结果 / exit / pass-fail-skip及原因
失败类别：产品行为 / 测试代码 / 环境 / 决策依赖
缺陷关联开发task / 修复commit / 复测结果
证据位置 / 原进程句柄 / 自有资源回收结果 / 下一owner
```

同一次执行关联多个ID时引用一份证据，不重复充数；一行含多个分支时所有分支都验过才能置通过。浏览器入口失败即保留失败，不能用HTTP替身、删断言、换免费流程或按钮隐藏完成整行。

## 下一测试批次（依赖顺序）

1. T-C11已在Web a52a623按真实RED→GREEN/Root完整门/独立审验收；E05/E08/E10原失败保留历史。正规BFF6消费已由E15验收发布；不把生命周期或契约验收当真实聊天通过。
2. T-Q10/T-C02：IAM缺提交发布与Web正规BFF6消费已有限复验；E16/E14旧组合来源和同fresh初始化已有限通过；E26新Web发布后的Root组合95pure有限通过，独立0且Root88a87417已发布，fresh已同步；整行main-only等仍待验，完整main-only与独立/项目浏览器列表仍待验。不重复clone或启动服务。
3. T-C06/T-C09/T-C10/T-F03：E17严格真实旅程第二轮失败；定位与对应Web回归已由E18/E24收口发布；E26已发布组合并按E28真实复测，现失败于second-partial-active；下一先补有界脱敏原因诊断并验证，沿原ID修复/复测，不盲跑或放宽预算与断言。
4. T-K04–07/T-A01–06：按owner artifact先后接选择/授权/安全过程，实际Skill/MCP/审批/作品与五时点刷新。
5. T-B02–07：真实证据→授权赠送/余额→预占→结算或恢复；支付T-B08最后。其余矩阵随对应切片持续复测，不能遗忘到最后。

## 历史验证矩阵（已归档、禁止作为当前门禁）

以下旧L1–L5原文仅考古；旧仓、Mongo、旧协议/命令/模型/数量均不是当前执行依据，不恢复历史runner。


以下内容保留为历史证据索引，不是当前 Root 的验证入口。

## L1 单元 / 契约套件（秒级，无外部依赖*）

*store-mongo / transport-redis 检测到本机服务才跑，否则 skip 并显式标注。

| 仓 | 命令 | 覆盖域 |
|---|---|---|
| kokoro-agent（pytest ~434） | `uv run pytest -q` | 契约门禁（raw 18 kind 逐字段）、HITL 中间件（审批/问答/结果审核）、steering、subagent HITL 透传、supervisor、memory/MCP 挂载、资产域（local/s3 资产源快照装载 + skills 渲染 + 配置矩阵，minio 实测；`tests/test_assets.py`）、run-scope state、storage/streams（mongo ledger 矩阵含 sandbox 绑定 + redis stream；实测真 redis+mongo，服务缺失 fail-loud 不 skip）、docker/e2b/custom 编排（连接器注册表+枚举覆盖守卫；resume 重连/keep-first）、统一配置树（yaml 摊平+env 覆盖+凭据禁入）、workspace S3 归档（minio 实测）、架构分层守卫、边界 pragma 审计、LocalFake 全链（`tests/e2e/test_local_fake_run.py`） |
| kokoro-session（vitest ~194） | `npm test` | 契约门禁（browser 20 kind + HTTP 形状）、relay 归一化、message.user 合成、control 裁决/幂等、SSE 续传、恢复扫描、store（memory+mongo）、transport（memory+redis）、namespace profile 解析（含 swarm 成员校验矩阵） |
| kokoro-web（vitest ~176） | `npm test` | reducer（20 kind 折叠幂等）、水合=全量回放语义、engine 状态机（开流/重连/adopt user id）、HITL staging、持久化、投影、UI smoke（session-shell 刷新重建线程） |

类型/静态：`pyright`（agent 0 error）、`tsc --noEmit`（session/web 0 error）、`ruff check`。

---

## L2 确定性跨栈 e2e（`scripts/e2e-v21-gate.py`，LocalFake，~1 分钟）

真 redis+mongo+双进程（session npm start + agent worker），LocalFake hitl 脚本：ask_user → write_file（审批+结果审核双暂停）→ 文本流。

**多底座同一套断言**：文件面默认 local（目录直读），`E2E_WORKSPACE_BACKEND=s3` 切 S3 归档档
（agent 写时归档 → minio → session S3 reader）；执行沙箱默认 local_shell，
`E2E_SANDBOX_BACKEND=docker` 切容器隔离档（execute 进容器、文件面留宿主）；两轴可组合（docker+s3 组合档）。minio 前置：

```bash
docker run -d --name kokoro-minio -p 9100:9000 \
  -e MINIO_ROOT_USER=kokoro -e MINIO_ROOT_PASSWORD=kokoro-secret \
  cgr.dev/chainguard/minio:latest server /data
```

| ID | 用例 | 预期 |
|---|---|---|
| E2E-01 | POST messages | 202 + receipt（run_id/user_message_id/assistant_message_id） |
| E2E-02 | 同 idempotency_key 重发 | 重放同 receipt，不开新 run |
| E2E-03 | SSE 合成事件 | session.created → run.created 领衔 |
| E2E-04 | **message.user 合成** | event_id=user_message_id，content=原文（事件史即线程真源） |
| E2E-05 | ask_user_question 暂停 | tool.awaiting_approval(kind=ask_user_question) |
| E2E-06 | 活跃 run 期间新消息 | 202 转 steer，归属活跃 run 同 assistant 占位 |
| E2E-07 | steer 幂等 | 同 key 重发同 receipt |
| E2E-08 | **steer 消息进事件史** | 第二条 message.user（event_id=steer message_id） |
| E2E-09 | snapshot 暂停点 | pending_pauses 恰 1 条 ask_user_question |
| E2E-10 | respond 提交 + decision_id 幂等 | 202/202；tool.returned(responded=true) |
| E2E-11 | write_file 审批暂停 | kind=tool_approval，allowed_decisions 含 approve 无 respond |
| E2E-12 | respond 用于审批工具 | 400 族拒绝 |
| E2E-13 | approve → 结果审核 | result_review 暂停带已执行 result，allowed=[approve,respond,reject] |
| E2E-14 | 审核 respond 替换 | tool.returned.result=替换文本 + responded=true |
| E2E-15 | 文本流与终态 | message.delta → message.completed → run.completed(completed) |
| E2E-16 | 终态 snapshot | active_run 清零、无 pending、assistant completed |
| E2E-17 | **snapshot.files** | 含 plan.md（mime=text/markdown，bytes>0，真目录 walk） |
| E2E-18 | **files 端点直读** | GET files/plan.md → 200 + 原文字节 + MIME |
| E2E-19 | **files 路径穿越** | `..%2F..%2Fetc%2Fpasswd` → 404 |
| E2E-20 | Last-Event-ID 续传 | 从中段续传只收水位后事件，拿到终态 |
| E2E-21 | **seq=0 全量回放（刷新水合语义）** | message.user ×2 + 全事件面可完整重建线程 |
| E2E-22 | 终态后新 run | 202 新 run_id 并跑到终态 |
| E2E-23 | entry=poet 具名入口 | wire 上人格 system_prompt + 其余预设为下属 + 租户 namespace |
| E2E-24 | entry 未知 | 400 unknown_entry |
| E2E-25 | run.cancel | 202 → run.completed(status=cancelled) |
| E2E-26 | 事件面覆盖 | 首连收齐 8 类核心 kind |
| E2E-27 | **会话软删除（终态会话）** | DELETE→202 deleted；snapshot/新消息→410 session_deleted；重删幂等 202；工作区文件仍在磁盘（agent 侧零变化） |
| E2E-28 | **暂停中删除** | ask_user 暂停中 DELETE→202 + run 收敛 cancelled + snapshot 410 |
| E2E-29 | **Skills V2 供给物化** | namespace 授权技能 → run 工作区 /.skills/main/<name>/SKILL.md 整包落地；点前缀不进 snapshot.files |
| E2E-30 | **鉴权负例（gate 全程 auth-on）** | 无 token→401；他人 token→403 session_forbidden；其余全部断言在强制模式下通过 |

---

## L3 崩溃混沌（`scripts/chaos-verify.py`，ledger/checkpoint=mongo 生产跨 pod 形态）+ trace（`scripts/trace-verify.py`）

| ID | 用例 | 预期 |
|---|---|---|
| CH-01 | 认领 worker 在 HITL 暂停期间 SIGKILL | 另一 worker 心跳收养 control 流，resume 续走到终态 |
| CH-02 | session 进程在暂停期间 SIGKILL | 重启后 snapshot 暂停现场完好，审批续走到终态 |
| CH-03 | 双 session 实例（多 pod 形态） | B 实例跨读 snapshot（活跃 run+暂停点）、跨发插话归属同 run、跨发 resume 收敛终态 |
| TR-01 | HITL 暂停/恢复多执行段 | Langfuse 上同 session trace ≥2 且同 kokoro_run_id（langfuse:3310 可达才跑，否则 SKIP） |

---

## L4 真模型跨栈（`scripts/real-model-verify.py`，glm-5，走钱）

| ID | 场景 | 预期 |
|---|---|---|
| RM-A | 明令 task 委派 researcher 子代理 | subagent.started/finished、子代理文本流、子代理内工具事件成对且带 subagent_id |
| RM-B | 普通提问 | thinking.delta ≥1、message.completed 非空、token_usage 上 wire |
| RM-C | web_search 真调用 | tool.invoked/returned 且结果非错误（searxng 不可达则 SKIP） |
| RM-D | namespace 挂载 skill（渐进披露：prompt 只见 description，正文按需 read_file） | 模型输出遵循 skill 标记约定 |
| RM-E | local_shell 下 execute 审批 | approve 后真 shell 输出回流 |
| RM-F | 运行中插话（steering） | 202 归属同 run，产出反映插话内容 |
| RM-G | 真模型 write_file 文件面 | 审批 → 落盘 → snapshot.files 含 note.md → files 端点回读原文 |

---

## L5 浏览器 UI 走查（真栈 + Playwright，视觉/交互终审）

栈：`KOKORO_WORKSPACE_ROOT` 同根 + LocalFake hitl（确定性）或真模型；session:3913 / web:3014。

| ID | 用例 | 步骤 | 预期 |
|---|---|---|---|
| UI-01 | 完整 HITL 轮 | 发消息 → ask_user 卡片选项答复 → write_file 审批批准 | 过程块实时展开：问答标记"已人工答复"、工具行 done、最终文本流出 |
| UI-02 | **run 完成后刷新** | UI-01 跑完 → 浏览器刷新 | user 消息 + 全部过程块 + 最终文本经 seq=0 回放完整重建，无空气泡 |
| UI-03 | **run 进行中刷新** | 暂停点（审批待决）刷新 | 待审批卡片恢复、可继续裁决走到终态 |
| UI-04 | 文件 chip → canvas 预览 | 展开 write_file 行点 plan.md chip | 右侧 canvas 打开，markdown 渲染真实内容（MIME/字节数正确） |
| UI-05 | canvas 文件树 | canvas 切"文件"tab | 工作区文件列表（路径+大小），点选切预览 |
| UI-06 | 运行中插话 | run 进行中输入框再发一条 | 消息立即上屏归属同轮，不开新气泡 |
| UI-07 | 本地 echo 对齐 | 发消息后观察 | 本地乐观消息与回放 message.user 不出现双份（receipt adopt） |
| UI-08 | 会话切换/新建 | 侧栏切换会话再切回 | 线程各自独立完整，无串台 |

存证要求：每次走查至少 1 张关键状态截图（walkthrough 铁律）。

---

## 已知边界（显式不在本表）

- e2b backend：编排结构就位（fake SDK 单测钉死生命周期语义），真栈行为待 key 复核；无 key 选 e2b 即 fail-loud。
- custom backend（ADR-010 BYO）：`pkg.module:factory` 引用自带实现，契约/加载/生命周期绑定已单测钉死；BYO 实现本身的正确性归其作者。
- state 盘档（backend=state）：诚实降级无文件面，snapshot.files=[]。
- trace-verify 依赖自托管 langfuse，默认 SKIP 不算失败。
