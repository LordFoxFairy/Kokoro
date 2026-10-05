# Kokoro 当前执行事实

核对：2026-10-05，R240。完整 Wave 0–7 goal 保持 active；研发与完整用户旅程尚未闭环。本文件只保留当前事实，旧 CURRENT 的 510 行全文逐字归档于 [progress.md](progress.md) 的“R228 CURRENT 原文归档”，不与本页当前结论并列。

## R240 当前正式交付与运行差异

Web Root已将认证/恢复切片精确19路径提交本地main `5e0963648db0cb0e1a60de42ea025670b32aba85`（parent1e8ce99c），所有Git bytes绑定63257完整工程与最终独审，原19protected bytes/modes保持；现在Web仅三D0和既有system测试4个mixed路径，生产源码没有未提交差异。收据`/tmp/r240-web-commit-receipt.json`。未push/Root gitlink发布/重启3310；本次原浏览器getTab仍在focus命令31.6秒超时，未取DOM，不据此断言应用原因或恢复。

纠正此前“用户完全旧源码”过宽措辞：3310仍同受管副本/PID，不是新正式全owner组合；Root逐12路径实际hash核9相同、2production不同（use-session-state/app-frame中Move协调尚缺）、1INDEX不同。认证主要源码已在副本，文件相同不证明编译/浏览器当前状态；不能再仅凭副本创建日期归因。其next server实际为dev模式，正在只读核安全源码热更新闭包，避免为换Web毁掉临时用户数据/session。

BFF项目改名contract前置原owner正于fresh cdad0ad6 artifact推进，public7.2.0/91ops及输入/error规则已批准，不授生产rename/schema；Agent/Billing单attempt接线只读审计并行。70业务组11/6/14/38/1保持，当前页面/完整CRUD/Settings/费用与Wave0–7仍OPEN。

## R239 前一阶段记录

BFF active资格前置已由Root完整复验并精确14路径提交本地main `cdad0ad6580dcbca18b75fdfbdbac4aa61f750d2`：schema12/0、真实PG/Redis217pass/0fail/0skip，工程check/format/contract/build0、源码及四D0独审0。Git对象等冻结、原20protected bytes/mode保持，收据`/tmp/r239-bff-commit-receipt.json`；没有Project生产删除writer/改名完整能力，后继name PATCH三面正由原owner只读收敛。

Web最终system `e82340fc`：Root63257完整工程已终态0（136.164秒），258contract、50architecture、lint/typecheck、165文件2473测试与build全部通过；默认套件包含全部73真实Next/Chromium/Redis系统例。先前Root31212独立完整73/0/0skip亦保留，46637的R195 URL观察点失败与窄修记录不删除。12source冻结、源码/前一测试独审0，最终R195窄hunk和三D0独审0P0/P1/P2（/tmp/r239-web-final-freeze-review.md），候选尚未Git交付/启用3310。IAM/BFF为controlled peers，不是正式owner或收费全链完成。Settings13分栏只读盘点已完成：通知/快捷键仅内存、个性化缺GET且吞PATCH失败、Integration可本地假connected、Computer/Deployment未闭资源生命周期；不计PASS。

完整Wave0–7及70业务组状态11/6/14/38/1保持；新候选未启用3310，Root六gitlink尚未提交，Web19/BFF20/Billing5mixed及uv保持。原用户持续加载/CRUD/正式积分仍开放。

## R238 前一阶段记录（由R239当前事实替代）

BFF clean候选已补Project deleted_at/active partial index、六TS25资格谓词和统一HTTP request-ID。Root真实schema完整12/0/0skip、同8业务组35父子统计pass/0fail/0skip，源码独审0。business新片格式修正后，Root54939最终完整check与format均exit0（743pass/2资源skip，lint/types/contract/build0）；最新格式版本的完整真实集成仍待验，未提交/启用用户组合。

Web clean候选12既有source/4tests已冻结，三D0及源码独审0；Root真实五目标5pass/68名称过滤，首次匿名server redirect、撤权datafree native handoff及held snapshot有界恢复全到达。完整73系统Root35695已终态exit1：67pass/6fail/0skip，81.827秒。六项覆盖冷启动/刷新、focus认证更新、主题与语言偏好读取拒绝、认证探针挂起与503恢复；需区分旧测试观察点失配和真实产品缺陷，未定根因前不放宽断言或宣称修复。最新候选完整工程及用户3310仍待验。setup缺helper与旧readiness失败独立保留，不冒业务失败；实际收据见progress R238。

原BFF20/Web19mixed、六gitlink与用户3310保持；70整组11/6/14/38/1不变，完整CRUD/费用/原页面验收仍OPEN。

## R236 当前切片交付

Web本地main `1e8ce99c46d0e0bf87824af321cd45f6d5fa5081` 精确两路径交付缓存读拒绝修复与系统反例；全部已提交字节等于冻结候选，原20路径字节/模式保持，现19mixed。Root有效RED→原恢复与认证负控2pass→完整68真实Next/Chromium/Redis系统0fail/0skip→原工程258contract/50architecture/lint/types/2460test/build全0，独审0。IAM/BFF为controlled peers，不是用户3310/正式费用整链。所有本轮资源句柄终态；准确manifest与六依赖链接隔离修正保留在progress R236。Root组合未更新/未push/未重启3310，T-U04仍失败。

BFF四当前D0短前缀已独审0，仅必要active资格设计准入；20mixed保留，未授新SQL/代码、rename和完整删除仍后继。

## 1. 产品验收总览

现 [test-cases.md](test-cases.md) 70 组状态：**11通过 / 6失败 / 14待复测 / 38未验 / 1支付后置**。通过项包含限定工程/业务切片，不是11个完整页面、子仓库或完成百分比。系统/真实 owner/浏览器各层证据分别记录，不互相替代。

- 唯一当前 PRD：[kokoro-handbook/product/09-v2-prd.md](kokoro-handbook/product/09-v2-prd.md)。
- 原任务/owner/准入：[task.md](task.md)；代码入口：[CODEBASE_MAP.md](CODEBASE_MAP.md)。
- 实际失败、终态句柄、SHA与资源收据：[progress.md](progress.md)；不另建计划中心。

## 2. 仓库与运行组合

子仓的 tests 不迁入 Root；`scripts/tests/` 只覆盖 Root 治理脚本，`verification/` 承接跨仓行为验收，不创建应用测试总目录。

Root和11物理子仓现场均只有本地main，远端本轮未核验。Root仍有6个gitlink差异及受保护uv.lock，Web4/BFF20与部分owner文档含未提交修改；整体工作树非clean。不得覆盖或混提这些修改。

|物理仓库|当前本地HEAD|已确认的有限交付 / 尚未闭环|
|---|---|---|
|apps/kokoro-app|5e096364|认证/恢复19路径已提交，完整73系统与2473工程通过，当前4个mixed路径保留、未发布正式运行组合；Git-only缓存修复两路径已交付、完整68系统与2460工程通过；修正fixture与完整URL等待后，Root最终隔离系统81pass/0fail，修复Conversation缓存读拒绝初始化SecurityError（未证原3310原因）；含两项目会话删除case，非真实BFF项目本身删除；用户页面/CRUD/Settings与正式模型费用链未全验|
|apps/kokoro-bff|cdad0ad6|Message事务/故障与active资格切片已提交，最新217真实PG/Redis通过；20个protected路径保留，项目改名/完整删除与组合用户链未全验|
|apps/kokoro-agent|cb645370|System3.0消费、单completion/输出界和客户端生命周期已提交；原始usage基线完整peer179项已有证据；新生产捕获及SDK完成标记已冻结，Root完整真实SDK/自有HTTP peer310pass/0fail、默认2253pass、工程/build/installed通过、源码独审0P0/P1/P2，现精确8路径本地提交、工作树clean；可信输入界/Admission/收费Run仍OPEN|
|apps/kokoro-iam|c9a9872c|登录/managed first-party provisioning局部已验；当前组合登录回调、退出/撤权/多窗口整旅程待验|
|apps/kokoro-system|955bd587|模型目录3.0与技术执行参数切片已提交；当前组合实际调用/费用链未闭环|
|apps/kokoro-billing|e5d83db0|私有rate选择已按10路径本地提交；六source/test精确绑定115真实PG/1361辅助十门0及独审，四docs只接批准前缀，五旧mixed全文保持，现5dirty docs；未启用3310，policy/quote/Admission/预占结算释放/流水UI仍OPEN|
|apps/kokoro-capability|da813ed4|Skills/MCP owner局部组件有证据；物理名尚非kokoro-platform，cutover及实际消费者整链未验|
|apps/kokoro-storage|14f2bc9c|owner局部门；真实浏览器上传/扫描/下载/作品/项目释放整链待验|
|apps/kokoro-scheduler|e8dca489|owner局部门；独立任务页面CRUD→触发→Agent结果整链待验|
|apps/kokoro-mori|ca76c2e1|本轮未修改或完整复验，不作为新完成项|
|libs/kokoro-web-shared|0c4e87ac|本轮未修改或完整复验，消费方UI组合仍待验|

原3310 Web PID46036仍运行受管非Git副本，认证主要源码样本已相同，但尚未核完整正式组合或当前浏览器渲染；不同源码与owner pins仍须核对。本轮未push、更新gitlink或重启用户服务。Billing/Web自有验收句柄6274、46388、74057、95636、67616均终态；无重复PostgreSQL/Redis、共享reset、实际资金或provider调用。

## 3. 当前页面与能力缺口

|模块|仍须完成的完整业务验收|
|---|---|
|登录/工作区|原用户持续加载根因与修复；正常登录回调、刷新、退出、撤权、多窗口|
|Home/Composer|真实能力入口、样式、多行/IME/附件、发送Stop竞态，无假营销连接或免费文案|
|会话/项目|外部会话与项目绑定关系；创建/改名/归档/移动/删除/刷新；项目删除连同会话与文件生命周期|
|独立定时任务|CRUD、暂停恢复、时区/DST、真正触发、执行结果、异常恢复|
|Agent过程/审批|真实Todo/Skill/工具/子Agent/作品；审批恢复、取消、断线续流与终态|
|Skills/MCP|安装/授权/选择→真实执行→撤权与错误恢复|
|文件/作品|上传字节、扫描、引用、预览下载、过期和权限、清理|
|正式积分|授权赠送、余额、预占、核实实际用量结算/释放、流水，失败取消actual-only，unknown不填0|
|Settings|13个分栏逐项读取→保存→刷新→重新登录；历史通知/个性化/快捷键及404/503问题待复测|

## 4. 当前交付证据与实际失败

- **Agent本地交付**：main `cb64537048d34ce6db5bea5f2e12e182ba88092c`，精确8路径Git objects同冻结、工作树clean。Root当前29architecture/310真实SDK与自有HTTP/contract全0；完整默认2253pass、717按marker过滤、795既有警告的R233收据绑定同核心源码。四D0/源码独审0，archive构建0，新wheel所有entry bytes与已安装18step验收wheel相同。收据 `/tmp/r234-agent-commit-receipt.json`。仍不是native/Billing收费链完成。
- **Web完整工程复测**：Root46156终态0，258contract/50architecture/lint/typecheck/165file2481pass/0fail/build全部通过，161.421秒；manifest `/var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-r234-web-engineering-q7b13zmn/manifest.json`，source/config/Redis集合保持。单文件预算提交main `680c8db8c7c118d083bc64ba7362dff6f62fcecf`，其他20mixed字节/模式保持；收据 `/tmp/r234-web-worker-budget-commit-receipt.json`。本门绑定冻结混合工作树，不冒Git-only组合或用户3310。
- **原Web失败不删除**：R233默认2478/3（邀请桌面、移动、注册5000ms超时）和未build历史保留。同源码单文件4/0、CLI4worker全套2481/0后，仅固化maxWorkers4；文件仍并行，deadline/断言/测试集合不变，独审0。不声称精确卡在launch或原用户加载根因。
- **工作区缓存异常**：实际选择性Conversation key读拒绝导致SecurityError，已最小修复并通过完整81真实Next/Chromium/Redis系统用例；IAM/BFF为受控peer。manifest `/var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-r233-web-full-eeam4wb3/manifest.json`。原用户3310原因与修复仍未证实。
- **Root治理仍失败**：旧全门153规则违反、组合checkpoint不一致保留；现组合6个gitlink差异未更新。当前测试归属局部7pass不替代全治理复验。
- **用户浏览器取证未完成**：原/app只读getTab在15秒工具期限超时、kernel reset；没有取得DOM/网络证据，未刷新/新开标签/重启用户服务，不推定应用故障原因。

R233/R234各次失败、复测、SHA及资源终态集中保留在 [progress.md](progress.md)；本页只列当前事实，不将旧候选描述并列为当前状态。

## 5. 当前下一行动与执行边界

1. Web认证/恢复19路径已交付；保护剩余4mixed，核现dev副本源码闭包与正式组合，再真实浏览器验收持续加载及逐项CRUD/Settings，工程绿不是页面全可用。
2. BFF active资格前置已提交cdad0ad6；项目改名 `PATCH /v1/projects/{projectId}/name` 三面只读审计已交付。下一阶段为owner契约/文档与真实失败用例，name与现receipt同事务、ID/slug不变、旧key不覆盖新名、LWW不新增version/表；改名实现尚未完成。
3. Agent已交付观察切片；继续与Billing按owner接真实授权、预占、核实用量、结算/释放和流水，不使用fake grant/known-zero/免费文案。

所有本轮Root资源验证句柄均终态，不重复启动服务或共享数据库/Redis；后继原生owner按同task表续派，主控保留集成与Git职责。完整Wave0–7 goal保持active，支付最后。

R240 Root治理最新实际仍失败：standard153违反，topology6个gitlink/HEAD不一致；只限定topology脚本7/0通过，不冒全门。Web dev源闭包静态508文件472同/36异，live generated public7.0 vs正式Web7.1，原源码9/12样本相同不能当全组合一致；未执行热覆盖/清用户数据/重启。
