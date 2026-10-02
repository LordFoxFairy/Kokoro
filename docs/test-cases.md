# Kokoro 测试任务总台账

状态：当前测试计划，2026-10-02 / R88；复用既有文件，不建立第二开发计划中心。

- 本页唯一维护**测试任务、验收标准和最新结果**；[task.md](task.md)维护派工/依赖，[progress.md](progress.md)保存实际运行证据，[CURRENT.md](CURRENT.md)说明当前组合。
- 范围：批准Wave0–7全部研发能力与九owner；其他前端、历史Session/Mongo、部署多角色/网络策略不在本轮。支付渠道后置，不删除目标。
- 本表每行是测试任务组，不是一个自动化断言；各owner用例留本仓。未验不等于没有代码，历史通过不等于当前组合通过。
- 状态：通过 / 失败（最近执行） / 执行中 / 待复测（有历史证据或版本变更） / 未验 / 阻塞（明确决策缺失） / 后置。
- 完成条件：绑定commit或冻结hash、实命令/环境、pass/fail/skip、证据和清理；本行必需分支被跳过则本行不得通过；明确拆至其他测试ID的资源分支仍记未验，不影响限定纯门，但绝不计为资源通过。相关source/contract/pin变更后移回待复测。修复提交不直接关测试，Root复测成功才关闭。
- 截至本次盘点：Root c68c111e；BFF bb610ea/public6已发布但Root/Web未同步；Web5e538f69存在lease修复dirty；Agent17c73541文档D0进行中；Billing e04bff9纯codec冻结未发布。活动工作树不作为最终验收源。

## 当前完成度（任务组计数，不是整体百分比）

共 **70** 组：**通过6**；**失败2**；**执行中0**；**待复测18**；**未验41**；**阻塞2**；**后置1**。

通过仅限下表具名范围；完整用户两轮真实聊天最近失败，**整个产品尚未闭环**。本次整理没有重新执行全部测试，读取已有实测输出并核对当前source hash；最近执行时间/版本以证据记录为准。

## 测试任务矩阵

| ID | Owner/层级 | 测什么与通过条件 | 状态 | 最新证据/未完成原因与下一动作 |
|---|---|---|---|---|
| T-Q01 | Web | 本仓format/lint/types/unit/contract/architecture/build；跳过逐项说明 | 待复测 | 历史门不能证明新组合；按owner ACCEPTANCE重跑 |
| T-Q02 | BFF | 本仓format/lint/types/unit/contract/architecture/build；跳过逐项说明 | 通过 | E01：仅BFF离线纯门 |
| T-Q03 | Agent | uv锁与frozen依赖/Ruff/Pyright/pytest/wheel；HTTP contract与架构；skip说明 | 待复测 | 历史门不能证明新组合；按owner ACCEPTANCE重跑 |
| T-Q04 | IAM | 本仓format/lint/types/unit/contract/architecture/build；跳过逐项说明 | 待复测 | 历史门不能证明新组合；按owner ACCEPTANCE重跑 |
| T-Q05 | System | 本仓format/lint/types/unit/contract/architecture/build；跳过逐项说明 | 待复测 | 历史门不能证明新组合；按owner ACCEPTANCE重跑 |
| T-Q06 | Billing | 本仓format/lint/types/unit/contract/architecture/build；跳过逐项说明 | 待复测 | 历史门不能证明新组合；按owner ACCEPTANCE重跑 |
| T-Q07 | Platform | 本仓format/lint/types/unit/contract/architecture/build；跳过逐项说明 | 待复测 | 历史门不能证明新组合；按owner ACCEPTANCE重跑 |
| T-Q08 | Storage | 本仓format/lint/types/unit/contract/architecture/build；跳过逐项说明 | 待复测 | 历史门不能证明新组合；按owner ACCEPTANCE重跑 |
| T-Q09 | Scheduler | gofmt/vet/test/build；OpenAPI/event protocol/schema/架构；skip说明 | 待复测 | 历史门不能证明新组合；按owner ACCEPTANCE重跑 |
| T-Q10 | Root | 精确gitlink、main-only、发布contract/version/digest/client drift、fresh clone | 待复测 | BFF6已发布，Web/Root组合尚未迁移；旧95仅历史 |
| T-Q11 | Root | 发送失败诊断有界/脱敏、两轮归属、失败仍非零退出、原硬断言不变 | 通过 | E02：诊断纯门，不是发送成功 |
| T-Q12 | 各数据owner | 同应用库独立schema fresh install/drift/拒重入/零跨owner SQL/失败回滚 | 未验 | 逐owner实资源；不增加应用角色，不用单仓结果代替组合 |
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
| T-C06 | Root六owner | 正式登录后两轮真实模型聊天：两POST/四Message/全文/刷新/作品hash/他人404 | 失败 | E04：最近W2 product-send-click；当前新组合还未复跑 |
| T-C07 | BFF→Agent | 同会话FIFO/同key重放/双tab同时提交；一活动head，无重复执行 | 未验 | 队列正常也须竞争负例；跨会话允许并行 |
| T-C08 | Web→BFF→Agent | Stop/steer/取消/重复控制；ACK不冒充terminal，输入和队列正确收口 | 未验 | 按现owner契约；资源验收不能用UI按钮存在替代 |
| T-C09 | BFF→Web | 活动/终态刷新：同事务Message/执行head/过程与event_watermark一致 | 未验 | 完整用户旅程仍未通过 |
| T-C10 | BFF→Web | SSE断线/cursor replay/重复/间隙/过期与GC；不丢字、不双气泡 | 未验 | 真实断连/重启，禁止localStorage成为事实源 |
| T-C11 | Web | 同scope真实重挂/双owner/StrictMode；最后卸载才close SSE；injected不被释放 | 失败 | E05：Root已复现1fail/1pass；原WIN01 lease GREEN尚待冻结验收 |
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
| T-A01 | Agent→BFF→Web | 简单聊天只回复；复杂任务Todo完整表更新、不被子Agent覆盖 | 未验 | R87安全过程D0并行中；现HITL局部实现不证明整链 |
| T-A02 | Agent→BFF→Web | 真实Skill resolving/loading/ready/failed；不从选中状态伪造已加载 | 未验 | R87安全过程D0并行中；现HITL局部实现不证明整链 |
| T-A03 | Agent→BFF→Web | 友好tool running/completed/failed摘要；无raw args/result/stack/token/隐藏推理 | 未验 | R87安全过程D0并行中；现HITL局部实现不证明整链 |
| T-A04 | Agent→BFF→Web | 完整多项HITL pause→一次决策→resume；stale/重复/unknown/刷新正负例 | 未验 | R87安全过程D0并行中；现HITL局部实现不证明整链 |
| T-A05 | Agent→BFF→Web | Todo/Skill/tool/HITL/delivery五时点刷新：恢复同水位，无重复或丢失 | 未验 | R87安全过程D0并行中；现HITL局部实现不证明整链 |
| T-A06 | Agent→BFF→Web | 子Agent身份/状态/失败/取消/汇总；不混入主回复或泄露私有过程 | 未验 | R87安全过程D0并行中；现HITL局部实现不证明整链 |
| T-B01 | Billing | 定价revision纯codec：strict格式/不可变摘要/整数/rational/边界/恶意结构 | 通过 | E07：772 unit/静态通过，仅冻结3文件；未验真实收费 |
| T-B02 | System→Agent | 实际provider/model/route revision绑定；逐call/attempt证据，不补零/猜用量 | 未验 | ADR-033；System仅技术路由，Agent仅事实证据 |
| T-B03 | Billing→BFF→Web | 授权赠送/余额/流水/撤权；前端只读owner结果，无假充值/免费补偿 | 未验 | 真实Billing命令+持久ledger；不直接改数据库充当授权 |
| T-B04 | Billing→Agent | provider调用前预占、余额不足、并发预算、同key重放、ACK unknown恢复 | 未验 | 实际attempt授权，禁止一次许可放行整Run |
| T-B05 | Billing | 采购成本×冻结可配置7/5倍率、币种积分换算/舍入/版本；前端零独立计价 | 未验 | ADR-033；7/5是加价40%，不是净利润率 |
| T-B06 | Agent→Billing | 真实usage→幂等结算/增额/释放/对账；超时、失fence、晚结果不重扣 | 未验 | 未知成本保留reconcile，不把Run terminal当费用结案 |
| T-B07 | Billing | 失败/取消/部分输出/未知成本的收费资格与账务分支 | 阻塞 | 收费业务策略待确认；不预设一律免费、一律release或一律收费 |
| T-B08 | Billing | 支付/订阅/checkout/refund/webhook验签去重及sandbox对账 | 后置 | 用户已明确支付最后；渠道配置属运维，不阻当前聊天研发 |
| T-U01 | Web | Home提示只填草稿、零自动POST/计费；真实模型/套餐/能力，无错误营销卡 | 未验 | 真实浏览器+截图/axe/视觉；UI纯测或借用shadcn不替代验收 |
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
|Web|T-Q01待复测|无业务数据库；真实session/adapter待验|T-R02未验|T-L/C/K/A/U未验或最近失败|
|BFF|T-Q02通过限定纯门|T-C01过滤切片通过；全owner资源套件未验|T-R02未验|T-Q10/T-C02 Web消费者未验|
|Agent|T-Q03待复测|真实PG/Redis/checkpointer/lease待验|T-R02未验|真实模型T-C06失败；安全过程T-A未验|
|IAM|T-Q04待复测|真实schema/PG/Redis/OAuth负例待复测|T-R02未验|T-L固定tenant浏览器链待复测|
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

1. T-C11：原WIN01 lease修复冻结→Root独立审查/真实RED→GREEN/完整Web门；原失败记录保留。
2. T-Q10/T-C02：Web正规固定BFF6→Root组合provenance/机器门→独立与项目浏览器列表。
3. T-C06/T-C09/T-C10/T-F03：原严格两轮真实模型旅程，含活动/终态刷新、全文、receipt下载及另一用户拒绝；不放宽预算与断言。
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
