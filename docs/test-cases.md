### R259 T-K03 首片真实验收与尚未接通边界

- 子例 ADMISSION：现Skills读取绑定真正probe boundary；辅助 held GET/POST/fresh恢复已绿，真实撤权/多主体页仍未验，不从副本绿当越权消除。
- 子例 POLL：Root实际失败详情被120秒probe关闭→df2c08a后真实同tab详情跨auth/session200保留，原我发布的视图未重置。首片PASS，证据与exact轮询时间见CURRENT；并未取消授权重核。
- 子例 PERSONAL-VIEW：正常硬刷新默认已安装、准确安装空态；发布列表真实名称/简介，技术ID不在卡片；设置技能独立reader无重复标题/无重复“我的技能”。正向子路径PASS，未冒全CRUD/窄屏/fault全组合。
- 子例 INSTALLED-METADATA：Platform c94909f正式producer+真实PG33/0已过，BFF/Web待消费、normal owner未重载；整页保持RETEST/未验收，不能用“暂无名称”占位文案结案。
- 完整70组计数不变，无新增完整组PASS，旧失败证据保留。Root当前335辅助绿不当用户验收数量。

### R259-SKILLS-POLL：真实浏览器新增P1，首片暂缓放行

Root在最终cd31b1dc freeze正常tab21：我发布的→详情GET200(.370,t1225316)→例行auth/session200(.371,t1225359)后dialog消失并回已安装，installedGET200(.375)。相邻probe恰120s，零用户关闭/退出与源码改动；证据r259-skills-poll-reset.json。独审/286组件绿没有覆盖这个真正用户持续操作，首片不算已验收。

最窄裁决：现probe请求序号只作迟到fence，与用户可信scope代际分离。仅已明确pass、同trusted subject/index、非unavailable/recovery/suspended的例行pending保留最后确认boundary，成功同subject不换代；任何确定unknown/负向/索引失可信/离页立即撤准入及换代，恢复fresh GET，不续旧写。每次业务请求server当前session仍授权，platformAdmin在途不沿用true。不新增auth store/协议，不改refreshUnconfirmed/false分类，不放宽首次/恢复或取消预算。

原Web writer唯一写集在原22集外增现src/ui/auth/use-session-state.ts、tests/ui/use-session-state.test.tsx、tests/ui/app-gate.test.tsx；现Skills assembled test加routine timer+true稳定view/detail/draft与真实unknown撤退对照，原安全断言保留。先更新三D0自有R259 prefix，再有效RED后窄实现；Root独审/Node22门/正常120s真实轮询验收，零API/owner/凭据/服务改动。不能仅靠hidden CSS保旧私有projection或无限加载避重核。

### R259 Skills 对标与实际失败子例

|子例|实际步骤/结果|验收与状态|
|---|---|---|
|T-K03.R259-DISPLAY|正常技能页只有个人发布源，默认published；重复我的技能→Settings reader层级，卡片露source_ref，单页disabled分页；before截图已保存|展示审查已完成；推荐两明确视图/真实名称简介/详情技术信息，待用户选定方向，未实现，不升PASS|
|T-K03.R259-ADMISSION|从有卡片页点我的技能→登录状态不可确认、侧栏不可用；单次重试auth/session200 authenticated:false，旧发布卡仍可见、Settings未打开|真实失败保留；需现可信boundary/context传入reader并退役旧读/投影，不能false简单改anonymous或以CSS隐藏冒权限修复；正式回读/过期恢复/撤准入/跨人回归待验|
|R259-REFERENCE|Manus既有登录态实际技能浏览、个人已添加空态与技能详情；无新授权/安装/任务/资金|仅竞品观察，不是Kokoro功能验收；不复制未接搜索/官方目录/虚假使用量|

证据同Root现var/dev/r255-preserve/r259-*；完整组不提升，模型/CRUD当前优先级不变。

### R258 当前页面用户子路径补证（不增加完整组PASS）

|现用例/子路径|本次真实结果|未闭环项|
|---|---|---|
|项目页前置 / T-C05关联规则|正常项目指令保存/历史/硬刷新同文本；Web bf2bee9当前页面三个普通CRUD区显示|完整项目删除/关联清理与撤权仍待验|
|T-F01 / 项目资源正向|100B真实上传200、scan clean、权威GET hash一致、硬刷新两QA文件在；r258-project-final-frozen-browser.json|下载/单项删除未接，跨主体与服务端取消未验|
|T-K03 本人安装控制|本人纯清单技能安装/暂停/启用/移除/重装/最终移除回初始空态|不当技能执行/版本冲突/完整组PASS|
|T-P01/T-P02 编辑与刷新|自有QA标题PATCH200→GET200→刷新保持；paused/next null/原timezone规则保持，r258-schedule-name-update.json|恢复/Scheduler当代接纳/删除/跨身份/到期执行仍未验|
|T-K05/T-U04 创建MCP|正常本人连接空态GET200；创建实际404 bff_route_not_found，错误UI不冒Connected|Server与Connection生产缺口仍FAIL|
|T-R02 正常依赖可用|九入口与PG/Redis/MinIO/ClamAV读核、真实S3上传扫描，不reset|健康不当各功能/Agent worker/全页面PASS|

完整70组仍11 PASS /8 FAIL /14 RETEST /36 UNVERIFIED /1 PAYMENT-LAST。Storage契约工具修复5b15fe3只辅助工程，D1 missing handler失败与typecheck2保留，绝不记用户删除PASS。

### R258 页面CRUD当前实测补录（完整组计数不变）

当前用户重排页面CRUD优先、Agent执行后置；原70用例ID继续，11 PASS/8 FAIL/14 RETEST/36 UNVERIFIED/1 PAYMENT-LAST。真实positive子路径不得把完整组未验负控清零。

|既有组/业务|实际行为与证据|本轮状态/未验|
|---|---|---|
|项目页前置 / T-C05关联规则|正常自有QA创建、名称保存owner回读、硬刷新；指令保存→project/history200→当前历史→刷新同值；r258-project-positive-browser.json|正向子链已验；候选仍2P1修复中，删除/取消/未知/跨身份完整分支未验，整组不改|
|T-F01/F02 文件|QA专案110B真实上传200、scan clean、资源GET/hash、刷新可见；r258-project-resource-refresh.jpg|上传/列表正向已验；此页无下载/单项删除，扫描负控/跨人/取消/并发未验，完整CRUD未过|
|T-K03 本人技能安装|源合法published纯清单安装→停用→刷新→启用→remove→removed筛选禁写→同ID重装→remove恢复installed空；r258-skill-installation-crud.json|正向控制CRUD已验；源技能保留，权限撤回/unknown/双tab冲突/执行采用未验，不整组PASS|
|T-K05/T-U04 MCP|本人连接真实GET200空；自订MCP保存POST404 bff_route_not_found，取消草稿不产生授权；r258-mcp-create-red.jpg|真实FAIL保留；Server注册/Connection命令消费者缺口，九服务在运行不能解决源码缺失|
|T-R02 依赖/运行|9应用进程存活；PG/Redis/ClamAV/S3实际认证读通过；r258-normal-infrastructure-read.json|只实际接线健康，不等全部最新源码/worker或功能通过；BFFaccepted/loaded仍不同|

独审r258-project-visibility-review.md两P1与后继有效RED单独保留；Root首次201工程辅助绿不作业务验收标准。QA项目/文件只新增自有对象，原数据保留，无推理/资金/永久清理。

### R257 管理子链实际验收更新（2026-10-06 16:20 UTC）

|用例ID/类别/标题|预置条件|步骤|预期结果|实际/证据|优先级|类型|
|---|---|---|---|---|---|---|
|R256-ADMIN-03.HTTP / 主链 / 正式管理员读取保存确认|自有真实PG、IAM CLI资格/Audit/CodePKCE/current session，BFFbac0cbf/System3.0|三个具名列表读取→单row visible CAS更新→owner和BFF回读|同tenant/label、版本2、完整目标字段相同|PASS仅owner子链：Root75617/r257-admin-http-committed-real-owner.json；正常浏览器未验|P0|真实owner系统集成|
|R256-ADMIN-03.REPLAY / 状态/异常 / owner幂等与冲突|同owner临时row、已保存原key/body/precondition|原key重放→同key异body→新key旧version|原结果不再递增，异body409与version409，权威row不变|PASS同75617；不是管理员撤权重放验证|P0|真实持久化/异常|
|R256-ADMIN-03.SECURITY / 权限 / 坏Session拒绝|真实IAM/现四管理operation|换invalid-session读取→回读System|401、稳定error envelope、owner不变|PASS子例同75617；合法普通Session403、撤权后原key、正常管理员入口仍UNVERIFIED|P0|安全/系统集成|
|R256-ADMIN-03.HEADERS / 边界 / 正式HTTP层不误拒|BFF当前source/正式System3.0header语义|无body GET带JSONmedia头；owner成功不带Cache头|200且BFF public仍no-store，body/CAS/错scope仍拒绝|真实400/502有效RED后75617绿；15辅助纳默认829中，不代替页面|P1|边界/真实owner辅助|

70完整组仍11/8/14/36/1，新增整组0；旧失败证据与所有未验项保留。后台页面、正常数据/双身份完整路径通过前不关闭T-U04或全面宣称上线。

## R257 本轮最新用户与机器验收（2026-10-06 15:29 UTC）

完整70组状态不变；下列是当前**子路径**证据，不借局部通过关闭整个页面/能力组。以下历史失败保留。

|用例 ID|标题|预置条件|测试步骤|预期结果|实际结果/状态|优先级|测试类型/类别|
|---|---|---|---|---|---|---|---|
|T-C-R257-FORWARD|浏览器前进地址/内容一致|正常IAM用户、Web8bb02d6、原R243两历史|硬刷新→已排程→后退→前进→任务页|后退原会话；前进真实排程，不显示聊天|PASS子路径：两markers→heading=true/chat0；真实QA paused23:58；forward-final-browser.json/jpg|P1|用户E2E/状态流|
|T-C-R257-SETTINGS-HISTORY|设置深链与历史恢复|同原会话、设置hash|打开设置→Back→Forward→硬刷新→关闭|保会话query；modal随hash；关闭清hash|PASS子路径：原两历史保留、hash恢复/关闭清空、普通人管理入口0；无偏好写|P1|用户E2E/边界/状态流|
|T-C-R257-PROJECT-DIRECT|文件夹子历史与外部会话常驻|本人两个现专案与原历史|展开5251folder→子会话→Direct|所属leaf正确，外部列表常驻，不串历史|PASS读导航子路径：R145→R243两历史；scope-browser.json/direct-project.jpg。完整CRUD/触屏滚动未验|P0|用户E2E/主链|
|R256-ADMIN-03.CONTRACT|管理机器契约闭合|BFF4238460、System固定3.0 artifact|RootNode22完整check+独审原四P2|99ops、old95exact、错误界/headers/strict均一致|PASS机器切片：contract264/0、主814/0/2skip、工程0；不是Admin页面/HTTP成功|P1|合同/安全/辅助|
|R256-ADMIN-03.HTTP|真实管理员正向后台路由|正式CLI资格+CodePKCE、System合法routing|current me=true→owner读200→BFF管理GET|合法200且受当前资格/tenant约束|FAIL/有效RED仍OPEN：实际三owner BFF404；纠正fixture后真实HTTP辅助6例2PASS/4FAIL均404。两具名生产文件已准原owner实施，shared入口Root接线；未称页面通过|P0|系统集成/主链|

**退出判据不变：** 同完整用户主链、边界、异常、权限与状态回归及真实owner/数据回读均通过，P0/P1清零后才称完整闭环；模型/账务必须正式预占→已核实实际结算/余释放→流水，无fake/free路径。

## R257 本轮真实交互验收与新失败（2026-10-06 15:06 UTC）

|用例 ID / 类别 / 标题|预置条件|测试步骤|预期结果|实际结果与证据|优先级|测试类型|
|---|---|---|---|---|---|---|
|T-S-R257-CONTROL / 主链 / 正常排程控制接纳|正常IAM Session、BFF43ca000与真实Scheduler；新QA仍暂停|真实页面编辑标题→保存→真实owner回读→硬刷新|同task/rev4 command成功，Scheduler同名paused；页面新标题/23:58保持；不发生执行|PASS仅此控制子路径：r257-schedule-normal-owner-ack.json；succeeded/paused/occurrences0；真实页面截图同名current.jpg。完整执行仍UNVERIFIED|P0|真实浏览器/跨owner系统|
|T-S-R257-FAIL / 异常 / 终止失败不假运行|自有真实PG、合法当前lease/fence/revision，正式BFF HTTP|register/replace收到closed永久拒绝→GET；旧revision/paused/delete/retry/rollback负控|当前active/enabled终止failed+next=null；其他事实不误改，原子回滚|源修43ca000已验；本方PG/HTTP157/0及全8文件277/0，响应替身不冒真实Scheduler故障/正常页面执行|P0|真实持久化/异常辅助|
|T-C-R257-FORWARD / 状态机 / 浏览器前进内容与地址一致|硬刷新正式Web四冻结候选；正常R243两历史|点击R243→侧栏排程→Back→Forward；再次fresh硬刷新重跑|Back保持同ID两消息；Forward显示排程而非聊天，地址/高亮/内容同owner|**FAIL P1**：Back通过，Forward URL scheduled/heading false/chat log true稳定重现；r257-standalone-forward-frozen-repeat.json。原owner接定位/测试/源修，不能用182辅助绿关闭|P0|真实浏览器/路由状态机|
|T-C-R257-STANDALONE / 边界 / 目录不消费会话参数|正常本人、scheduled目录自有tab=list与非当前conversation|复合URL进入目录→读网络→硬刷新|保目录tab，自有参数正确，非法目标不GET；不偷Direct历史|窄子例PASS：r257-standalone-normal-browser.json；目标GET0。记忆activeId一次hydrate另OPEN；五页面实际均未全验|P1|真实浏览器/边界|
|R256-ADMIN-03.RED / 权限/主链 / 正式管理员路由|自有真实IAM/BFF/System，各正式owner；正式CLI资格与CodePKCE|当前me资格true→System合法row读200→BFF admin routing GET|目标200、data数组与真实owner exact、meta闭合，读后owner不变|**FAIL**：Root58122目标404；正常账号零授权，资源cleanup保持。正式两测试commit53bb60a/b81793f7，真实route研发缺失不以菜单/健康替代|P0|真实owner组合/权限辅助，非Admin浏览器|

退出条件保持：完整页面读写/权威回读/刷新/异常恢复/权限与同步后台管理真实通过，才关闭完整组。70组仍11/8/14/36/1；本輪整组新增0。辅助工程门不作为最终用户验收。

## R257 最新正常页面验收（2026-10-06 14:21 UTC，仅子路径不关闭70整组）

下表是实际执行账；下方旧轮次状态保留历史，不能用旧候选/旧失败覆盖本节最新证据。每个完整页仍须完整主链、边界、异常、安全、状态流与对应后台管理才能关闭。

|用例ID/标题|预置条件|测试步骤|预期结果|实际结果/证据|优先级|类型/类别|
|---|---|---|---|---|---|---|
|T-U04-R257-NORMAL 正式偏好保存|正常IAM本人、批准结构已切换、正式Web/BFF|打开设置→改昵称→失焦→显式保存→回读→硬刷新→恢复原值重开|失焦不写；保存与权威回读一致；刷新保持|PASS子路径：PUT/GET200、刷新保持、正式恢复原空值；normal-settings-browser-journey。双标签冲突/失败/撤权未验|P1|用户E2E/主链|
|T-C04-R257-CURRENT 专案各自挂会话且外部常驻|本人两专案及既有Direct/项目历史|展开各folder→点自有leaf→点外部R243|child只在所属folder，Direct一直可达，同ID历史正确|PASS读导航子路径：项目R145、Direct R243两历史；paired-sidebar-current截图。提交CRUD/全部滚动仍待验|P0|用户E2E/主链|
|R257-SCHED-RESTORE 精确删除授权边界|唯一旧暂停测试target及3失败command、Root维护停写|私有备份→恢复比事实→仅清目标→两列DDL→独立回读|删task1/command3；其余数据/原receipt不变|PASS限定维护：receipt flags全部真、原3receipt保留、独立恢复exact，未删新QA|P0|恢复/边界|
|R257-SCHED-CRUD 提交编辑暂停刷新|正常本人当前空排程表、既有正式页面|页面创建→编辑标题与23:58→暂停→硬刷新|HTTP保存后权威读一致且刷新保持|PASS子路径：新task paused/rev3/23:58；Node24首次后纠正Node22重读通过；browser-node22-paused-current。resume/delete/执行未验|P0|用户E2E/状态机|
|R257-SCHED-REJECT 调度拒绝不能称运行中|正常Scheduler实际开启且目标当前配置|创建有效任务→等待owner拒绝→读页面与owner|终止失败真实显示failed，无虚假运行中|FAIL：3command invalid_schedule、next=null；原active曾显示运行中；真实private literal+空allowlist拒绝。唯一owner准备窄修，未关闭SSRF|P0|异常/状态机|
|R257-SCHED-ROUTE 带会话的模块刷新|本人scheduled URL携conversation参数|真实排程页硬刷新|留在排程模块不偷跳/app|FAIL观察待复现定位：带conversation曾跳/app；独立tab=list保持，不把两个场景混为成功|P1|边界/竞态|
|R256-ADMIN-NORMAL 普通用户隔离|正常IAM platform_admin=false|设置查入口→直接/admin|入口隐藏且服务端拒绝|PASS普通用户子路径：入口0、HTTP404；Cache-Control/Vary的Next dev P2仍FAIL，管理员正向/撤权浏览器未验|P0|权限/安全|
|R256-ADMIN-03-REAL 正式管理员管理列表|Root自有IAM CLI CAS/Audit+真实CodePKCE、System owner真实发布route，非normal授资格|current /me=true→System读200→BFF管理GET→System未变→清自有资源|合法请求200且只当前tenant管理投影，资源零泄漏|有效RED/FAIL：62795管理GET404，前置全真、cleanup passed、77→77/0→0；real-red-root-result。非后台页面成功|P0|系统集成/主链|
|R257-PAGES-READ 能力页实际读取|正常本人、真实Platform/Storage|导航技能发布/安装→本人连接→文件/作品|权威读成功、空态非假数据、不持续loading|PASS仅列表读：技能发布既有1项/安装空、本人连接空、文件123B/作品空；无授权invoke或新作品成功声明|P1|用户E2E/主链|
|T-A01-R257-FINAL-CURRENT 封口证据只读|自有真实Agent PG、有正式sealed evidence、专用Billing caller|正式receipt封口→真实HTTP读取→鉴权/bytes/绑定负控|可信证据仅正确专用caller读取|PASS限定owner读切片6a21f7d：Root HTTP1/PG90/纯186及工程已过；正常模型/余额预占结算释放/完整用户聊天仍OPEN|P0|系统集成/安全|

**退出标准：** 当前每页完整用户链与异常/权限实测、当前源码独审与Root门、真实owner及数据回读全部通过，未决P0/P1清零；财务只已核实实际消耗结算/余预占释放。后台入口/HTTP200/空态/工程数量不能单独判整页或整组完成。付款仍最后。

## R257 当前验证状态（正常用户验收不冒通过）

|用例ID/标题|预置条件|测试步骤|预期结果|实际状态/证据|优先级|类型|
|---|---|---|---|---|---|---|
|R257-RECOVERY 恢复与具名演进|正常IAM/BFF同snapshot、仅Root自有隔离DB|真实备份恢复→两owner check/apply/check/replay→比原事实→清自有资源|原身份/会话/业务事实保持，仅批准字段和表变化|PASS限定恢复演练：43表1850行、零新增管理员/偏好；38284 receipt；normal未apply，非用户E2E|P0|恢复/异常|
|T-U04-R257-SAVE 正式偏好保存与刷新|当前普通用户正式Settings、正式BFF owner已接新表|读本人→编辑→blur→显式保存→权威回读→关重开/硬刷新|blur零写，CAS一致后反馈；失败保草稿，不假成功|RETEST准备：31路径冻结，Root正确Node22组件60/Hub147辅助通过；当前正常页原FAIL保留，未执行正式owner浏览器|P1|完整用户E2E/状态机|
|T-A01-R257-FINAL 合法封口后证据读取|自有真实PG、正式repository已有final evidence、专用caller|prepare/grant/dispatch/append→真实HTTP exact GET|原append可用，exact sealed head/身份/bytes一致且鉴权先行|FAIL：96350在append receipt字段回归拒绝，尚未到GET；另独审head/身份/host边界缺口，原writer续修；不将186纯门称链路通过|P0|系统集成/安全|

## R257 侧栏用户行为增量（完整组不关闭）

|用例ID/标题|预置条件|测试步骤|预期结果|实际状态/证据|优先级|类型|
|---|---|---|---|---|---|---|
|T-C04-R257-OVERVIEW 总览不偷选|正常本人，专案有既有会话|从历史点击专案标题→硬刷新|只显示overview，子会话未pressed，不持续loading|PASS子例：normal5416bc9/tab13实际渲染；r257-r141-normal-live.json；未测试overview发新任务|P0|用户E2E/状态机|
|T-C04-R257-LEAF/DIRECT 两列表常驻|同正常本人有专案与Direct历史|点folder子会话→点外部R243|同canonical历史正确，外部聊天列表一直在|PASS子例：project KOKORO_R145_E2E，Direct两KOKORO_R243_CHAT_OK；project/direct-history.jpg；未新调用|P0|用户E2E/主链路|
|T-C04-R257-DELETE-LATE 迟到Move不抢导航|现组件辅助fixture，Move pending|确认删除→删除ACK→释放旧Move结果|不导航回已删除会话、索引淘汰|辅助254PASS含该有效RED修后断言；正常提交删除CRUD仍UNVERIFIED，非用户链PASS|P0|异常/竞态|

## R256 用户交互与后台准入验收补充（沿同一测试账）

|用例ID/标题|预置条件|测试步骤|预期结果|实际状态/证据|优先级|类型|
|---|---|---|---|---|---|---|
|T-C04-R256-01 标题不误触改名|真实IAM本人/原P下有会话，717窄窗|普通点击项目会话标题两次|进入同ID历史，不打开改名|实际RED两次rename→单CSSGREEN同conv_ffd7历史/rename0；red与green receipt|P0|用户E2E/交互|
|T-C04-R256-02 工具独立|同本人P与Direct，各工具可见|改名→Escape；移动→Escape；删除→取消；转Direct|每次仅对应动作，取消无持久改动；两列表均保留|本轮真实通过取消/切换子路径；不冒实际CRUD提交通过|P0|异常/状态机|
|T-C01-R256-03 响应式命中/滚动|正常页，390×640与1200×460|测title/三action中心命中→Tab→上下滑→刷新|命中自身，手机44px，滚动可达，历史恢复|四命中全true；桌面32/窄屏44；Tab rename；113.5→204→0；viewport reset；物理触摸未验|P1|边界/交互|
|R256-ADMIN-01 管理员入口与直链|正式IAM资格与BFF投影已发布；真实管理员/普通用户|各自Settings→后台；普通用户直接打开/admin|仅管理员见入口；普通用户直链/API拒绝；业务owner逐次授权|UNVERIFIED：IAM d24aa2b已发布当前资格/管理contract0.8，真实owner34/0；BFF ac3cd1d当前资格投影已发布并经Root owner门，normal仍旧组合；Web当前资格/Settings入口/server gate在隔离候选，Root全系统70PASS/7FAIL，后继定向3PASS/4FAIL仍未放行；同期切换/后台实际模块未接，帐号待用户，不猜email角色|P0|权限/系统E2E|
|R256-ADMIN-02 撤权立即失效|合法管理员当前session，正式撤权命令/审计|访问后台→正式撤权→旧页/API/新标签/刷新|旧资格不复活、拒绝访问且审计可查|UNVERIFIED：隔离issuer同旧token正式撤权HTTP已拒资格；正常浏览器后台/旧页/API/新标签尚未验，不按token自然到期冒验收|P0|安全/状态机|
|R256-PAGES-01 个性化保存失败|正式非preview Settings；BFF正式preferences operation缺口|修改普通测试偏好→保存/blur→观察请求/反馈→重开|ACK/回读才显示保存，失败可解释且草稿不丢|FAIL：R257正常IAM浏览器，昵称QA-R257→blur实际PATCH404（22555.164）/界面无error；硬刷新昵称空。BFF399e70d已正式提供GET/显式PUT CAS并有隔离PG11/0，Web正式consumer/正常单表演进仍未接；页面FAIL保持，不用后端门清零|P1|异常/完整交互|

|T-C01-R257-READ 单一当前会话列表读取|正式Next/Chromium，当前Direct/Project与展开非当前folder，当前Session准入|打开当前页→观察列表读取→模拟503/unfinished→只显式Retry→切scope/撤准入|当前scope只一个live controller；Retry只新增一次，非当前folder独立且晚结果退役|窄例PASS：5416bc9当前controller复用；Root75287真实Next/Chromium相关R141/R183/R195通过（全系统76/1，另认证500仍OPEN）；正常overview硬刷新→leaf→Direct历史与两列表常驻实证通过。全部CRUD/撤权用户链仍待验|P1|系统交互/加载/竞态|

退出标准：每页读写→真实owner回读→刷新→异常恢复与角色权限通过；后台管理同步完成对应owner操作/审计。后端纯门/只读盘点、健康200/菜单可见不替代。当前完整70组不增PASS。

### R255 用户原标签后补实证（2026-10-06）

原tab7现已恢复同步：不注入cookie/preview，实际管理页原h1+h2=2且error可见，同时两个servers响应200（4de46d06/23f3d070）；CDP response body不可取，无法据此确定是旧schema/缓存/HMR哪个原因。保留error截图/metadata。正常reload当前源码并自动恢复既有settings hash后，原同tab1标题/正常空态/error0，两个真实servers200（2a7d008c/d1d78292）。这证明当前原页面读取呈现恢复，不代表Server→本人Connection/创建授权调用缺口已修。

所有Root临时页9/10均已close，原user7/8保留，viewport/touch override已清；原tab最终截图connectors-user-original-final.png/JSON。先前“原tab超时/故障未同次复现”是前置观察记录，由本后补证续接，不能删旧错误或断言后台所有能力通过。辅助与完整70组计数保持。当前T-P02按既有Platform3.2.0本人projection→BFF固定artifact消费接续，不新造目录模型。

## R255 本次系统用户路径补充（完整组不关闭）

| 用例 ID / 标题 | 预置条件 | 测试步骤 | 预期结果 | 实际结果/证据 | 优先级 | 测试类型 |
|---|---|---|---|---|---|---|
|T-C04-R255-01 / 重核保展开|正常IAM本人，两folder，非preview|展开P/Q→实际会话重核200→恢复可见侧栏|两folder保持展开；未知/换人不复活私有分支|前RED已收起；修后true/true/Direct常驻；browser-red/green.json；身份负控仅辅助case，真实换人待验|P0|功能/状态机|
|T-C04-R255-02 / 自然密度|正常本人两个空folder|逐个展开，测child与状态文案|反馈可见且无重复占高|43.52→26.80px；后段P有真实会话/Q空，真实行保留；sidebar-new receipt|P1|视觉/边界|
|T-C01-R255-03 / 短窗口上下滑|正常本人，1200×460，P/Q展开|项目行起wheel到末尾→反向回顶|唯一content滚动，Direct最后行可达，头尾固定|0→204→0；346.55<356.80；宽276/scroll276；final-scroll.json/png；撤准入后位置恢复未修|P0|交互/边界|
|T-P01-R255-04 / 正常连接器读取|正常IAM与九owner实际运行|Plugins→管理连接器→等待settled|真实响应通过严格验证；真实空而非失败兜底|servers200、真实空态；原截图失败同次根因未验；目录不是本人Connection|P0|功能/异常|
|T-P01-R255-05 / 嵌入单标题|正常管理连接器页|加载投影观察标题与空态|一个已新增标题，读/空/异常不受影响|原2→现1，真实截图connectors-heading-final.png；现69辅助回归；创建启用调用未闭环|P1|视觉/状态|
|T-P02-R255-06 / 完整本人连接链|正规owner artifact、正常本人授权、真实MCP endpoint|创建→授权→handshake→启用→Agent调用→撤销再调用|本人资源隔离；结果有真实证据；撤销后拒绝|UNVERIFIED/研发缺口：BFF6d46ec8已发布本人connections GET；正常UI本人同源GET200、connections=[]仅空读（r257-mcp-live-read），不计本组通过；Web8f73e94消费者已提交，三缺陷与cursor循环真实RED后修；Root最终459/0、真实正常刷新connections200/空态/单标题仅读取子路径（r257-mcp-cursor-final-live）。旧非GET503/registerRPC未实现，不冒完整成功|P0|系统E2E/权限/生命周期|

所有子例须以本轮当前源码与真实页面判定；真实触屏、跨主体浏览器、故障分页/全CRUD仍待验。9探针成功只证明进程入口，不代替本表完整链。70组汇总11/8/14/36/1保持。

## R255 当前切片行为证据（2026-10-06；完整70组不变）

| 原卡/测试点 | 前置与操作 | 实际期望/结果 | 优先级/状态与边界 |
|---|---|---|---|
|T-C01/C04 folder滚动|正常IAM既有用户；两folder展开；1200×460真实上下wheel|0→262→0，Direct底低于footer顶，无横溢/loading|P0 本子例PASS；全CRUD未验|
|T-C01/C04 touch|同正常页390×640；模拟从project链接纵向滑动|pan-y、scroll0→194、body0、Direct在|P0 模拟子例PASS；物理触屏/用户原IAB待验|
|T-C04 route/历史|硬刷新→项目P→既有外部QA会话|外部Direct常在，同ID/两历史marker/loading0|P0 本子例PASS；无新推理/费用|
|T-B07 FG1 HUMAN|真实PG/provider；列名非operator/无Member/UI选null→authorize/显式consent/Basic+PKCE/JWKS|原误送select-tenant RED；现准确scope/audience/sub/sid/fixedtenant/300s、无refresh/idtoken|P0 owner切片PASS；非浏览器赠送E2E|
|T-B07 FG1撤名/漂移|23独立fixture；新code；三时点正规CAS撤名及身份/资源/凭据单变|实际拒绝无token、0opaque/refresh行；完整三文件44/0|P0 子例PASS；宽4xx不冒每原因码实证，全部漂移/DB故障待验|
|T-B07 FG2在线grant target|尚缺专用machine/operation/verified exp/SDK与Billing接入|必须重核旧JWT/current roster与target，再正规gift/余额/流水|P0 UNVERIFIED；不凭FG1或纯门关闭|

## R255 当前左栏复验与 FG1 原生发行切片（2026-10-06 08:26 UTC）

- **本轮判定 progress，非整体闭环。** Web仍bf04df7（侧栏实现9e1c8c3），Root正常IAM既有session真实页面再次两folder展开、1200×460 wheel0→262→0，content宽276无横溢、Direct底346.8<footer356.8、branch43.52px/loading0。390×640触屏模拟从project行起滑0→194，pan-y、body0、content宽260无横溢；硬刷新/项目P→原外部会话，Direct始终在、同ID两历史marker保持。仅UI偏好操作，无新模型/资金/会话数据。自有页已close；用户IAB getTab20s超时，不称已控制其标签/物理设备。新截图sidebar-current-full-height.png，console本人Billing未开户404不冒侧栏错误；首次两click工具字段错未执行，纠正target后重跑。
- **IAM bb4663ac24a13b6f171936d4c7879eaa6388c22f**：原owner四生产路径+现lifecycle与五事实文档精确10路径；三D0仅原自有prefix、原suffix exact。合法列名非operator/Member0/activeOrg=null原select-tenant有效RED→正式authorize/consent/Basic+PKCE/JWKS正向GREEN1/35filtered、2.16s；真实lifecycle/fixed-Web/session44/0、40.63s，398source/test冻结exact与PG77→77 exact。23独立负控真handler/新code、三时点正式CAS撤名、漂移/凭据错/无refresh，不将宽4xx冒逐稳定原因码通过。原12安全正文除批准临时总拒块外字节exact、管理CAS/Audit writer不改。
- Root38903最终Node24 pnpm verify+Prisma exit0，102纯文件938/0及format/lint/types/contract/breaking/SDK/build/schema通过；独审c3b53298五hash exact无新增确定P0/P1/P2，原两worker均STOP。本证据是自有真实PG+provider handler，**非正常浏览器/TCP/资金E2E**；另一UI tenant正控/显式refresh/全部注册漂移/DB故障/并发撤权窗口未验。
- FG2旧JWT在线当前名单、verified exp、专用machine/grant-target/artifact、初始financial创建CLI、Billing正规赠送与可信消耗完整资金链仍OPEN；付款最后，不把支付/System价格/Agent用量误设为独立赠送前置。九原开发root/listener仍alive，registry/uv保持，不重启正常服务/PG/Redis/reset，无正常资格或资金写。原Web四mixed、其他owner候选/gitlinks保持，IAM交付clean；Root不提交gitlinks或uv。
- 完整Wave0–7 active；70组仍11 PASS/8 FAIL/14 RETEST/36 UNVERIFIED/1 PAYMENT-LAST，新增完整组0；handler工程绿仅关闭本FG1切片，所有页面CRUD及完整能力不冒完成。证据沿现ignored var/dev/r255-preserve/fg1-provider-{red,green,regression}.json/log、fg1-final-verify.log、r255-fg1-source-final-review.md、sidebar-current-reverification.json；下一沿原T-B07做FG2授权，左栏CRUD/页面独立验证不串行等待。

## T-B07.R255-FG1 真实发行流程回归（2026-10-06）

|用例ID/类别|标题|预置条件|测试步骤|预期结果/当前实际|优先级|测试类型|
|---|---|---|---|---|---|---|
|T-B07.R255-FG1-HUMAN 主链/权限|列名财务HUMAN无需操作租户Member|隔离真实IAM PG、正式注册client/名单；本人真实Session；非operator、Member0、activeOrg=null|真实authorize+S256+显式consent→Basic+PKCE换码→真实JWKS验签→核sub/sid/fixedtenant/exactscope/audience/expiry、无refresh/Member副作用|当前真实RED：302到/auth/select-tenant而非/auth/consent，1FAIL/12非匹配/exit1、PG77→77；后半尚未执行，不冒成功；原owner实施中|P0|正式provider handler/真实PG系统流程，非浏览器/TCP全链|
|T-B07.R255-FG1-REVOKE 状态/安全|当前名单撤销与独立code|FG1候选冻结后，合法真实operator roster CAS及真实HUMAN code|分别authorize前/consent前/有效code后撤名，独立重复流程；未列名operator/空名单；核无新token/refresh|预期全部拒绝且无身份提升，旧JWT在线撤权留FG2；当前未运行，UNVERIFIED|P0|真实状态机/授权撤销|
|T-B07.R255-FG1-DRIFT 边界/异常|发行依赖漂移不发token|真实Session/User/Tenant/client/resource/binding|独立各流程设置自有过期/缺失/disabled/错误binding，错Basic/PKCE/redirect/resource|预期fail closed、无token/refresh，普通Web登录/refresh保持；当前UNVERIFIED，不用单例RED证明整矩阵|P0|真实依赖/凭据负控|
|T-B07.R255-FG2-CURRENT 状态/安全|旧已签JWT撤权在线拒绝|FG2专用machine与grant-target contract/SDK正式发布后|合法新grant-target决策→名单撤销→原JWT再验证→target跨tenant/removed/会话撤销→Audit故障|预期403/404/503无allow/零账务I/O；当前未实现/UNVERIFIED，不把FG1或自然expiry当在线撤权|P0|后继跨owner系统与资金前置|

通过条件：FG1完整正负矩阵及普通流程回归、代码冻结独审和Root重跑；这只放行issuer切片。整用户闭环仍须FG2正式artifact→Billing调用→单次授权赠送→本人余额/刷新→模型预占/实际消费结算或释放→流水。当前完整70组不增PASS。

## R255 最新左栏与未开户验收（2026-10-06，Web 9e1c8c3/bf04df7）

核心风险：draggable行吞纵向touch pan；展开folder重复标题/工具行导致低信息密度；未开户错误被当网络失败。真实正常3310/IAM/BFF用户，非preview/mock；touch是Chromium模拟，不冒物理终端。完整70组11/8/14/36/1保持，仅以下子例验收。

|用例ID/类别|标题|预置条件|测试步骤|预期结果/实际证据|优先级|测试类型|
|---|---|---|---|---|---|---|
|T-C01.R255-TOUCH 异常/状态|项目/会话行可起手滚动|正常IAM本人两Direct，390×640 touch/coarse Sheet，原内容高660/窗488|从项目行向上滑→从会话文字向下滑→打开原历史|原RED项目0→0而library0→171.5；pan-y后同项目0→171.5、会话171.5→101.5；最终CSS硬刷新项目0→234.5，body0/URL不误导航、原历史保持，本模拟子例PASS|P1|真实浏览器手势模拟E2E|
|T-C04.R255-DENSITY 主链/边界|folder内不重复名称与工具行|正常P/Q owner列表200空、1200px桌面|展开两folder→核自身反馈/工具→打开sort→Escape→Space单独收起P|项目名只在folder行一次，children77.92→43.52px，原新建/排序点击区域真实命中；sort实际菜单可达；P false/Q true/Direct2保留，本子例PASS，不冒已有有数据/CRUD全闭|P1|真实页面/键盘/几何|
|T-C01.R255-SCROLL-FINAL 边界/状态|短高单滚动与底部会话可达|最终CSS/真实用户，1200×460，头账户固定|鼠标置左栏wheel至底→核Direct→wheel回顶|top0→262→0，宽276/scrollWidth276、Direct底346.8<footer356.8，body不滚；PASS本短高子例|P1|真实浏览器滚动|
|T-C04.R255-TOOL-HIT 边界/状态|移动folder工具不挡名称|最终CSS、390×640 Sheet两folder展开|核原+与sort的矩形/命中→点Q sort→Escape→点Direct可见文字|四工具44×44/center hittrue、名称留空间、sort正常显示“最近更新/按名称”，选原Direct关闭Sheet保原history；PASS本模拟子例。默认整行center位于既有rename按钮区的观察timeout单列，不强制点击掩盖|P1|真实触屏布局/正常按钮|
|T-B07.R255-MISSING 主链/异常|未开户是业务状态不是加载失败|normal Billing真实暂无本人credit account；正式owner/两读开启|正常用量与计费→等待两读→硬刷新→关闭再打开|actual正规404经strict body/meta/header才“尚未开通积分账户”status×2，Retry0/假0为0，loading解除；PASS展示子例；不冒赠送/收费链|P1|正常跨owner用户页面|
|T-B07.R255-MISSING-NEG 权限/异常/状态|缺账户不遮真实失败/旧actor|冻结production真实client+native响应补充门|401/403/503同code、generic404、缺meta/错requestid/非JSON/未知键/慢断流/卸载/换actor|保error或cancel/timeout、独立两面、旧响应不覆盖；现原44+新增26=70/0，辅助测试通过，不是全owner安全E2E|P0|辅助边界验证/待真实故障注入|

E2E主判据仍正常登录→真实列表→具体操作→owner事实→刷新/重入一致→异常恢复；所有持久CRUD、真实有数据folder、长分页/故障/物理终端/原IAB更新仍待完整验收。全systemfixture/全页Playwright/axe/视觉/bundle本轮未跑。仅CSS/显示状态写，未造资金余额、推理或数据库回填。实际证据在var/dev/r255-preserve/sidebar-billing-browser-final.json及最终两commit，相邻事实同步，不新QA中心。

## R255 当前正常浏览器复核与正规积分读取（2026-10-06 07:25 UTC）

|原用例/类别|预置条件|实际步骤|预期/实际结果|优先级/状态|
|---|---|---|---|---|
|T-C01.R255-SCROLL 边界|正常IAM、两原项目展开、1200×460|鼠标wheel下700→点原Direct QA→wheel上700|top0→331→0、宽276无横溢出、固定footer、原2回答/Direct2/loading0；布局子例通过，不冒CRUD|P1/子例PASS|
|T-C04.R255-TREE 主链/状态|同正常账号、原P/Q|展开两folder→P概览→Q→P→外部QA|各空列表200/自身反馈、外部2条保持/正文不丢；额外draft snapshot404未作为list失败，原scope索引已证ID对应|P1/读取子例PASS，完整组OPEN|
|T-B07 正规本人两读 异常/状态|正常Billing已正式装schema并启动，未创建账户|页面点用量与计费→等待两个终态→点重新加载|实际summary/ledger404 billing_account_not_found，loading0、重试同终态；当前通用加载失败文案不正确表达未开户，未有余额/扣款/流水PASS|P0/正式读取接通，页面与完整资金链OPEN|

根源分别为已修CSS布局/有界滚动与独立未开户UI语义；项目额外404是恢复local draft而非列表失败，不追加无证race修复。两旧label/折叠状态假设导致30s观察失败保留；实际状态重选后成功。真实UI与浏览器同源只读补核分开，辅助46/0不替代用户验收。现截图和sidebar-billing-current-browser.json记录；Root自有页已关，用户IAB未动。

## R255 侧栏树与滚动用户验收（2026-10-06，T-C01/T-C04，正常浏览器已复测）

不新增70组分母；正常3310既有IAM会话、既有P/Q与两条Direct，0会话/项目/模型/资金写入。风险：项目children横排溢出、被裁列表无wheel可达、nested滚动与头尾互相抢空间。

|用例ID/类别|标题|预置条件|步骤|预期结果|优先级/类型|实际状态|
|---|---|---|---|---|---|---|
|T-C04.R255-TREE/主链|每项目自身纵向子列表|正常IAM、两个现项目|依次展开P/Q，再折叠P，不打开正文|每children位于自身header下且缩进/不溢出；空态可见；Q独立、Direct区保持|P1/真实UI|真实RED保留；GREEN两folder children.y=各header.bottom/right=288，content276/scroll276，空反馈可见、Enter/Space不改URL|
|T-C01.R255-SCROLL/边界|短窗口单侧栏滚动|1200×460，展开Q|真实wheel向下到Direct→向上到导航，测header/footer与主区|content top改变；头尾固定、Direct可点击、无nested纵滚/横溢出，页面不滚|P1/真实UI|真实RED保留；最终GREEN content289/542，wheel到top253、Direct bottom346.68<固定footer356.8，原会话可点击/正文保持；上滚回0|
|T-C01.R255-NARROW/边界|窄栏/临时窄屏展开|现宽栏偏好expanded|700×460展开→滚轮到聊天→恢复1200→hard-refresh|无裁切/横溢出；wide偏好保留、无永久loading|P1/真实UI|PASS（下述实际证据限本子例）|
|T-C04.R255-KEY/状态|disclosure键盘与scope隔离|现P/Q/既有QA正文|聚焦toggle用Enter/Space展开折叠→点P概览→点外部QA会话→刷新|toggle不改URL/草稿/正文；概览导航准确；Direct一直存在/历史不丢|P1/真实UI|PASS（下述实际证据限本子例）|
|T-C01.R255-COMPACT/边界|图标栏短高入口可达|1200×320、收起|轮滚到底→最后入口可见→展开返回正常|图标轨道能滚且不挤压头/账户，展开后内容可访问|P1/真实UI|PASS（下述实际证据限本子例）|
|T-C01.R255-ERROR/异常|列表故障仍局部|原已有失败处理测试/真实可控owner故障|读取超时/拒绝后重试，不改身份数据|局部明确反馈、其他组保留、无整页永久loading|P1/系统UI|本次不主动停owner；历史辅助断言回归与正常空态分开，真实故障注入未验|

本次实际：700×460 fine-pointer窄屏展开 top0→265，header/footer固定；回1200刷新展开/原4条历史/Direct2保留；252px栏宽等动画完成后content228/scroll228，恢复300；1200×320 compact top0→170、项目入口y136可达；项目概览→外部原QA正文通过。两观察错误保留：初tree locator误匹配disclosure+sort；700错误假设dialog导致30秒超时，真实为fine-pointer rail而非Sheet；首次resize动画中测量后明确等settled重测，不算产品失败。

空Direct旧CSS隐藏规则也按已批准R254退役；真实本账号2条Direct保留，0条账号/触屏Sheet、真实列表故障注入/长分页尚未验。原项目概览导航另见会话conv_807... GET404、正常Billing503仍OPEN，不用局部导航通过抹掉。源仅三rail路径，独审e0829f2b无新增确定问题；适当工程门是辅助，不当业务闭环。退出条件仅本次正常主链/树结构/滚轮/窗口切换子例通过，不以此宣称项目/会话全CRUD、全部页面或完整Wave上线。

06:12 收口：Web `df609a0a0bb511a1c2c2f5a6456994c4efaa73c6` 已提交并接收旧preset消费者退役源码片。Root有效Settings RED→最窄退役；首宽回归566/1漏旧fixture及次567断言全绿但exit1卸载异常均保留，最后同567/0真exit0/types/lint0；Node22非system153文件2663/0、contract275/0、architecture50/0、build0，提交后新5/0（154非匹配未跑），36实际blob/工作树exact，独审2d1d234c。正常工作区/Settings/各刷新及提交后真实页旧agents请求0、models200、loadingfalse、原Direct/历史保持；真实模型目录为空，默认同值点击未保存，不冒模型可调用/切换保存、推理/资金/完整Agent通过。原3文档mixed suffix及OIDC修改未暂存，Root40精准路径无外带；Billing39/0仍未提交/normal OFF/两旧types失败。文件真实123B下载hash通过，单Asset删除三层未实现、新文件只选未传；完整70组11/8/14/36/1不变。原8服务复用、无正常模型/资金/owner文件/schema/reset/重启，自有页关闭，用户IAB未动。详情同0612 receipt与原任务卡；后继Billing旧13caller/正常两读激活、System现模型目录与费用/授权主链、Storage单文件生命周期，独立工作可并行，不等Agent setup阻塞其他页面。

## R255 06:12 系统质量与真实文件/旧目录验收增量

风险：文件页面看似能用但单文件删除owner协议缺失；旧preset目录请求不存在导致静默空selector；正常Billing候选尚未正式激活。完整70组11 PASS/8 FAIL/14 RETEST/36 UNVERIFIED/1 PAYMENT-LAST不因以下子例变化。

|ID/类别|标题|预置条件|测试步骤|预期结果与实际状态|优先级/类型|
|---|---|---|---|---|---|
|T-F01.R255-DOWNLOAD 主链/状态|页面下载字节与刷新一致|正常3310/IAM本人既有123B clean文件|点原文件下载→等待浏览器download完成→读真实本地bytes/hash→硬刷新列表|实际123B/c7888098…与owner SHA一致，同asset仍一行200/Direct常在/loadingfalse；本READ子例PASS，非新上传/全CRUD|P1/真实用户下载E2E子例|
|T-F02.R255-DELETE 异常/生命周期|单个人文件删除入口与owner协议|同正常页面，113B本轮文件仅选择尚未上传|核删除controls→独审正式Web/BFF/Storage操作→确认completed Upload中止不是删除|应可正式删除本人单Asset且不删同Blob兄弟；实际按钮0且三层均缺协议，FAIL/OPEN；停止新上传，正常owner写0，不借整scope/SQL清理；既有文件保持|P1/真实页面缺陷、owner协议审查|
|T-C01.R255-PRESET 主链/异常|工作区及Settings不消费无owner目录|正常3310会话；旧source，合法模型目录|真实hard-refresh观察网络→组件Settings正常模型选存后要求零旧目录请求|实际浏览器两次agents404；组件真实调用导致assert FAIL构成RED。另AppFrame label未匹配为fixture观察错误，不冒第二产品失败；退役源码实施待RootGREEN|P1/真实网络、交互辅助反例|
|T-C01.R255-PREF 边界/状态|严格model-only偏好，无旧兼容|新model-only及旧model+agent/null两形状|新选择保存/重挂载→旧形状回默认→新选择只写model|已冻结对应反例/保留控制，尚未跑完GREEN；待验，不迁移旧model、不碰其他storage/session/draft|P1/浏览器偏好边界|
|T-B07.R255-RESTART 异常/状态|原main同端口持久事实重启|自有隔离真实PG/现canonical账户/有限JWKS、env无Redis/provider|main启动→ready200+同账户200→SIGTERM自然0→同PG/port再main→两body exact→SIGTERM自然0→回收|Root39/0组合、19freeze/77集合exact，本可靠性子例通过；8config与mock严格拒绝1/0独立记。窄format/lint0、全types仍2旧栈FAIL，不是正常积分用户链|P1/真实owner启动辅助|

E2E：正常资料库→页面原文件下载→实际本地length/SHA→硬刷新同asset；新文件选入未提交，完整删除缺口保留。退出标准仍上传/扫描/读回/下载/取消与删除/越权/恢复完整真实用户路径，以及正式费用余额/预占/已核消耗唯一结算释放/流水一致；开发测试数、真实空态、健康探测都不替代它。自有浏览器已关闭，用户IAB未动，无新推理/资金/owner文件写。

## R255 05:44 系统质量与真实用户验收增量

核心风险：正式presentation误把管理页面当执行Feature导致入口隐藏；BFF公开setup存在但实际生产无接线；正常Billing未启与旧栈工程门未清。完整70组仍11 PASS/8 FAIL/14 RETEST/36 UNVERIFIED/1 PAYMENT-LAST，新增整组0。以下只更新原组子例，不以可靠性30项充业务数量，历史0522导航FAIL由本轮子例正控续接而非删除失败历史。

|用例ID/类别|标题|预置条件|测试步骤|预期结果与实际状态|优先级/测试类型|
|---|---|---|---|---|---|
|T-U01.R255-NAVIGATION 主链/状态|正规五页入口恢复|正常3310/IAM session200，原中文空导航，原chat feature关联|正规System两locale presentation CAS→同key回放/回读→正常侧栏逐点五页→各硬刷新→回原R243历史|五入口可见可达、刷新保Direct列表/loadingfalse；实际本子例PASS；chat/主题/namespace/release/flags未改，非全模块CRUD通过|P0/跨owner配置与真实浏览器|
|T-U01.R255-NAV-POLICY 权限/异常|普通页面导航不授执行权限|上例普通page feature_key:null、chat受控，site允许en-US/zh-CN|读两locale manifest并与before差分→zh/en别名负控→核feature/exposure|两正式locale200、别名403；feature/exposure不变，页内仍owner授权；实际PASS本子例；跨tenant每operation未在本轮重测|P0/安全、真实系统|
|T-A02.R255-NORMAL-SKILL 主链/状态|本人Skill列表刷新|既有本人R255清单version1|点击技能→等待本人card→硬刷新→读实际同源self/skills|现真实card与固定version1恢复、200、loading解除；READ子例PASS；本轮未发布/安装/执行加载|P1/真实浏览器、读取恢复|
|T-A03.R255-NORMAL-MCP 主链/边界|连接器管理真实空态|本人当前无MCP连接|点击连接器→管理连接器→Settings MCP→等待现server读→关闭并硬刷新页面|200本人真实空列表、非加载失败；READ子例PASS；营销catalog不算连接成功，connect/callback/disconnect仍待完整真实验证|P1/真实浏览器、空态|
|T-P01.R255-NORMAL-SCHEDULE 主链/状态|本人暂停排程可读|已有本人已暂停QA排程，正常schema仍原待激活项|点击已排程→等本人card→硬刷新calendar|实际已暂停卡可见/200/loadingfalse；READ子例PASS；暂停卡仍落calendar的产品状态与next投影未关闭，未调用恢复/执行/删除|P1/真实浏览器、状态展示|
|T-F01/F03.R255-NORMAL-LIBRARY 主链/边界|文件与作品独立读取|本人已有text/plain123B文件，无作品|点击资料库→文件card→硬刷新→Agent作品tab→读kind=file/artifact|file200真card/123B、artifact200真空态，loading解除；READ子例PASS；未新上传/下载hash/生成作品，不以空态冒交付能力|P1/真实浏览器、空态恢复|
|T-U04.R255-AGENT-SETUP 异常/状态|开始体验真实setup失败|上例Agent可达，平台telegram|点开始体验→等待实际GET setup→记录code/request-id与UI→关闭|应有权威有效setup；实际404 route_not_found/92ad9434-002e-4b1d-83de-09d5349fe0e0，实时配置暂不可用；**FAIL/OPEN**，BFFcontract与生产upstream断裂；独立目录404不合并、不假二维码|P1/真实用户缺陷|
|T-B07.R255-LOG 异常/安全/状态|实际请求完成日志与原始无泄漏|原main源码、自有真实PG/JWKS，合法BFF五因素+fixture秘密|strict坏query真实400/no-store/request-id→自然关闭code0后读raw32KiB→关联唯一safe6字段→扫描原始秘密boolean→资源回收|原日志无输出RED5/1；最终30/0/9.13s、18freeze/77库集合exact；本可靠性子例通过，非正常资金用户E2E。窄format/lint0，整tsc旧6exit2仍FAIL，不跳过有效断言|P1/真实owner故障、安全辅助|

E2E证据：0544-normal-browser-journey.json与视检导航截图，正常3310复用合法session，无cookie注入/seed/新推理/资金。五入口与全部硬刷新后仍有外部聊天、最终原会话同ID/旧两轮历史；Root自有浏览器关闭，用户IAB未动。账务实际退出线仍正式授权赠送→余额/流水→真实执行前预占→已核用量唯一结算/释放→刷新一致；页面完整CRUD、跨人/tenant拒绝、unknown ACK/重连/移动/axe等原退出标准不因本片降低。

05:22 正规控制面只读取证补齐：同System admin通道现web application ba84cee9/site dbc22d78/product226e1ee1；现feature列表及app exposure均仅chat enabled。en-US user-web presentation200/version1/navigation[chat]；zh-CN同surface与NULL变体均404（没有中文展示），两locale同release e94969ff/configVersion1，中文navigation空。证据0522-normal-product-navigation-read.json，不是前端rail修复删除菜单。下一准入应沿现Products正规feature/exposure/presentation管理补批准完整五入口、保主题/locale/release其他事实与权限，Root真实页面逐入口回归；不得强开Web flags或凭空声明执行已实现。仅只读，尚无导航配置写/新发布；该P0保持OPEN，39行只读b4105134给发布/binding风险，不据此删旧binding或共享release。

## R255 05:22 系统质量、真实用户子例与剩余风险

完整70组仍11 PASS /8 FAIL /14 RETEST /36 UNVERIFIED /1 PAYMENT-LAST，新增整组0。核心风险：首次偏好同步被StrictMode取消；正式产品配置隐藏能力入口；正常积分owner未启且旧栈未清。接口/组件数只作诊断，退出线仍完整真实用户链。

|ID/类别|标题|预置条件|测试步骤|预期结果/实际|优先级/类型|
|---|---|---|---|---|---|
|T-C01.R255-RAIL-PERSIST 主链/状态|宽屏偏好跨刷新|正规3310/IAM既有会话、1200宽、默认collapsed|真实点击展开→核cookie=true→硬刷新等待正文/loading解除；收起→刷新；重新展开恢复|展开/收起均按保存值，正文保留；实际旧RED刷新仍collapsed、新Web aaf577d两方向PASS；不当全部布局通过|P1/正常浏览器交互|
|T-C01.R255-RAIL-COMPACT 边界/状态|compact不覆盖宽屏偏好|上例expanded=true，真实fine-pointer浏览器|1200→700→真实展开→核cookie不变→回1200→硬刷新|窄屏临时展开可达且不覆wide；实际cookie始终true，回宽与刷新expanded、loadingfalse PASS；其他移动/触摸/axe待验|P1/正常浏览器交互|
|T-U01.R255-LOCALE 主链/异常/权限|正常中文manifest准入|同product/surface/hop、正常Site既有public=true/kokoro允许|en-US/zh-CN/zh/en GET差分→正规owner只读policy→同Site仅追加zh-CN CAS→幂等回放/回读→真实页面reload|原en-US200/中文403精确locale缺失；CAS1→2/replay200无新变更/zh-CN真正页面200；zh/en仍403，未放开public/tenant/用户角色；此子例PASS|P1/真实跨owner配置与浏览器|
|T-U01.R255-NAVIGATION 异常|live导航缺失能力入口|上例manifest200、正常authenticated页面|观察侧栏与正规manifest只读projection|应有已批准能力入口；实际navigation=[]、flags仅chat，Agent/Skills/MCP/排程/资料库入口不在；**FAIL仍开放**，System product正式projection配置定位，禁止前端硬开|P0/真实系统交互|
|T-P01/T-B07.R255-READ 异常|目录与积分入口|同正常会话/当前服务|实际页面requests，安全只提取code/request-id|agents404 route_not_found；summary503 billing_unavailable仍FAIL；正常Billing OFF，不伪空列表或免费|P0/真实业务缺陷|
|T-B07.R255-READY 异常/状态|已连接PG响应黑洞有界失败恢复|原source main、自有owner PG/局部TCP relay，无正常资金/模型|ready200→同已有socket上行增长/下行gate/无新握手→期待3500ms内真实503→旧socketclose→release→新socketready200|旧Root93797真实Abort有效4/1；ping窄修后26240同5+24=29/0，503/body/旧close/新200与77目录exact。仅可靠性辅助，不是正规用户资金E2E|P1/真实owner故障集成|

辅助RAIL28358第五fixture错误不当产品FAIL；合法fixture80103两有效FAIL/3PASS→完整rail+smoke26718 173/0，postcommit26909 5/0（62非匹配未执行）；窄lint与直接types0。Billing61943 types6旧栈错误exit2保留，未skip删有效断言；日志/fullbuild/cutover及收费Agent链尚未关闭。独立review cafca64c（Billing）与Web两hash无新增已证问题，均非完整产品认证。

正常Site配置一次正规业务变化/侧栏偏好操作已记；模型/资金/schema/reset/服务重启0，Root自有浏览器close成功，用户IAB未动。图/动作见ignored0522-normal-browser-journey.json，实际输入/历史仅旧QA会话，未生成新推理或假结算。

## R255 05:03 当前真实用户子例与未关闭的质量门

完整70组仍**11 PASS /8 FAIL /14 RETEST /36 UNVERIFIED /1 PAYMENT-LAST**；本轮新增完整组0。正常浏览器子例与开发可靠性门分开记录，不以28项owner绿代用户收费链。

|子例/分类|标题|预置条件|实际步骤|预期与实际结果|优先级/类型|
|---|---|---|---|---|---|
|T-C01.R255-NORMAL-LOGIN 主链|正常IAM进入工作区|八原正常服务、保留合法QA账号、可用Playwright既有空白页|/app→真实可见IAM表单填邮箱密码→登录→/app|可信/session200与欢迎页可见；实际完成，无cookie注入/seed；不证明所有认证异常|P0/真实浏览器E2E子例|
|T-C04.R255-NORMAL-FOLDER 主链/状态|独立项目folder与外部会话列表|正常已登录、既有P/Q、两条Direct、展开rail|Home展开P/Q→P概览→既有QA会话Direct→P→Q→Direct→硬刷新/恢复展开|三真实move200、同ID/文本保持，源列表移除/目标新增，外部区仍在，最终原2Direct恢复；实际完成本路线，未验其他CRUD/并发/草稿|P0/真实用户交互子例|
|T-C01.R255-OBSERVATION 边界/异常|刷新/折叠的观察前提|同正常浏览器|textarea刚可见比较→再等对话记录和loading隐藏；Q/rail折叠时等待行→显式展开|初次过早比对false与两15s超时保留；后续真正终态/展开后正确，不把观测修正当生产源码修复或宽屏偏好通过|P1/状态与QA记录|
|T-P01/T-B07/T-U01.R255-NORMAL-READ 异常|正常页面后台能力缺口|正规session与当前owner组合|正常页面真实请求agents/summary/manifest，核网络状态|实际404/503/403，仍FAIL待owner定位；不假列表/免费/放宽权限清零|P0/真实系统缺陷|
|T-B07.R255-DRAIN 异常/状态|已接受读完成后正规关闭|真实隔离owner PG合法账户、原source main、受控签名JWKS；不当正常IAMowner|JWKS入站屏障→SIGTERM→实际ECONNREFUSED且child活→release→消费响应→退出|有效RED22101为503；顺序修5718先200但deadline，native idle回收后65723同4+24=28/0，200/no-store/精确4560000与code0/signalnull、77库exact；只可靠性门，不是完整Billing用户链|P0/真实owner故障集成辅助|

正常E2E no新模型/资金/schema/永久删除，原QA绑定恢复、Root自有浏览器关闭，用户IAB untouched。截图/脱敏动作/网络和失败修正证据0503-normal-browser-journey.json；完整用户退出线未改。Billing窄lint0、整仓tsc同6旧栈FAIL、候选未提交/normal OFF；readiness客户端截止/日志/旧有效断言迁移/完整门及后继19operation继续待验。源码审查f70c7dde/冻结hash不代替浏览器付款、真实模型/队列/审批/文件/Skills/MCP验收。

04:40 最终冻结补证：runtime测试只修4处lint类型/异常包装后SHA8c17c056；Root59457同3+24重跑27/0、5.48秒、16freeze/PG77exact，Root75376九生产+runtime lint0。Root53849最终直接tsc仍同6旧栈错误；不冒全工程通过。独审55f43483绑定前一测试e8e5054e及两源码，最终4处测试类型差异由Root复核，业务断言/预算/屏障保持；不冒独审已覆盖后修测试。

## R255 04:40 子例实测（普通用户整组仍不新增PASS）

|用例ID/类别|标题/优先级/类型|预置条件|行为步骤|预期|当前实测与限制|
|---|---|---|---|---|---|
|T-C04.R255-FASTACK 异常/状态|未知创建重进保原意图，P0/交互|实际AppFrame/SessionEngine UI fixture，首次立即503、第二立即200|A网站草稿→失败→改B→同菜单重进→回Direct|同key/body、导航canonical A项目、A/B各草稿不串|原步骤断言全保，仅finally清stub；本轮宽73file中114ms通过；历史16file失败保留，normal/browser根因未证|
|T-C04.R255-DEFERACK 状态|明确ACK阶段诊断，P1/交互|第二POST受控响应、合法创建receipt|菜单关闭→重进→观察第2POST同身份→释放ACK→导航→回Direct|ACK前不导航、ACK后A/B归属正确|独立新case153ms通过，不替代快ACK/真实产品验收；Webad918391|
|T-B07.R255-SOURCE-READ 主链|正规本人读入口，P0/owner组合|原main child、真实隔离PG、合法fixture账户、五因素BFF身份|source启动→两本人GET→关自有资源|200/no-store、真实账本结果，正常数据零改|旧404有效RED→现1/0；read HTTP矩阵另24/0；normal Billing仍OFF，用户积分链未闭环|
|T-B07.R255-INITFAULT 异常|DI错误传回并清理，P1/进程|语法合法config与故意错误resource audience、真实DI|config解析→factory→真实verifier拒绝→caller catch|不由Nest提前抢exit；caller取得原错误|实际RED→abortOnError:false后GREEN；当前fixture child不是普通IAM登录|
|T-B07.R255-SHUTDOWN 异常/生命周期|最终deadline有界退出，P1/可靠性|原main、有效EdDSA请求已进入受控JWKS并挂起、deadline250ms|确认在途→SIGTERM→观测1500ms内退出|最终错误退出code1/signalnull，不以cleanup SIGKILL计成功|实际RED→main明确强退后GREEN；预算未放宽；graceful drain/readiness黑洞仍未验|

Root56132同3runtime+24读27/0、5.51秒、16freeze保持、PG77→77 exact/own资源回收。Web全部UI/engine73files1426/0与lint/tsc0；这些研发辅助彼此有重叠，不换算用户完成比例。Billing直接tsc仍6旧栈错误、工程cutover/正式资金/真实浏览器均OPEN。70组仍11PASS/8FAIL/14RETEST/36UNVERIFIED/1PAYMENT-LAST，完整用户PASS新增0。

## R255 04:19 子例记录（不增加70组分母或整组PASS）

|用例ID/分类|标题与优先级/类型|预置条件|测试步骤|预期结果|实际结果/后续|
|---|---|---|---|---|---|
|T-C01.R255-LOAD-ERR 异常|深链拒绝后备用读取失败，P0/交互|已有B历史会话；原URL A；A拒绝/B网络失败|打开A→A被拒回退B→B读取失败→点原会话重试→A恢复|水合结束不再spinner、不显B正文、原A URL保留、重试A且不新建执行|真实AppFrame+SessionEngine UI fixture先1FAIL→Web521841d定向PASS；normal browser/owner尚未执行，**整组未闭环**|
|T-C01.R255-LOAD-PENDING 状态机|待水合与同会话已有正文保护，P0/交互|A读取未返回；另有同route正文失败状态|观察请求中→终态→相同/不相同route切换|pending仍loading；终态error不被错route遮蔽；同route已有正文仍局部错误|现shell/engine宽回归461PASS/1其他项目FAIL，未把数字当本行全用户通过；非空错route仅静态核对|
|T-C04.R255-PROJECT-RETRY 异常|创建未知后重进保原意图，P0/交互|现正式欢迎页，提交A草稿503未知，后改B草稿|首次创建失败→B草稿→菜单重进→核canonical项目导航及A/B草稿|同key/body只重试原意图，无假导航，回原页保B草稿|宽回归1590行路径/失败；定向同freeze通过，尚未证原因，**保持待核而非覆盖失败**|
|T-B07.R255-RUNTIME 主链路|本人余额/流水正式入口，P0/owner组合|真实隔离owner PG、合法账户及五因素认证、原source main|启动原main→health→两本人GET→关闭所有owned资源|账户/流水200及no-store，关闭回收，不改正常资金|真实source/TCP先1FAIL（账户404）、health200、PG77→77 exact；canonical候选实施中，**正常用户未通过**|

Root实际辅助：两路径lint/直接tsc0、contract274/0、architecture50/0；宽16files461/1、定向2/0/103filter未执行，各有重叠不累加。未跑全量test/build/Playwright/axe/移动视觉；浏览器控制超时，不能当应用根因或通过。八原进程未重启；证据同0419原台账/ignored收据，正常资金/模型/schema写0，支付仍最后。

### R255 03:40 正常读取入口准入状态更新

Billing四D0已提交261a20f0：总24operation退出不变，但不再把赠送/全部支付能力作为现两GET开发启动前置。正常runtime仍未实现/启动，T-B07.R255-NORMAL-READ仍未执行；下一先实际原src/main.ts+隔离PG/TCP的composition RED，不拿404当完整用户业务结果。70组状态不变。

## R255 03:40 T-B07 名单切片辅助记录（不增加70个完整用户组）

**统计保持11 PASS /8 FAIL /14 RETEST /36 UNVERIFIED /1 PAYMENT-LAST；本轮完整用户PASS新增0。** IAM mainc2014a3d。

|子例ID/类别|标题|预置条件|测试步骤|预期结果|实际结果|优先级/类型|
|---|---|---|---|---|---|---|
|T-B07.R255-ROSTER 主链/边界|正式CLI名单替换与读回|真实operator Session、合法managed financialclient、activeTenant/真实User、Root自有PG|原CLI替换→官方/持久读回→实际read CLI→核名单摘要与Audit/注册不变量；canonical/no-op/空集合|只名单变更且同txAudit，授权read可返回canonical IDs，原注册不变|旧mode_missing有效RED→单例1/0；随后三file20/0含此例；不是正常赠送|P0/真实owner接口集成辅助|
|T-B07.R255-ROSTER-CAS 状态/异常/权限|双writer与真实Audit冲突回滚|同合法fixture，测试连接持exact行锁，两个生产事务|观察PG两writer等待→释放→核一个成功一个CONFLICT；stale expected但desired=current、未知User/非operator反例；复用实际Audit identity制造冲突→回读|CAS先no-op、只有一名单成功；Audit冲突整事务回滚，拒绝无越权效果|冻结实际三file20 pass/0fail，17.14秒，PG77→77 exact；不求和重复计数|P0/真实PG异常/状态辅助|
|T-B07.R255-ROSTER-UNKNOWN 异常/状态|提交/输出确认丢失|冻结代码，但无故障注入|stdout ACK、DB COMMIT ACK、postcommit官方read失败→持久事实与调用结果对照|不自动重写/还旧名单；未知不冒失败已回滚|**未执行**，仅静态核fail-closed；不得计PASS|P0/故障系统待验|
|T-B07.R255-NORMAL-READ 主链/权限/恢复|正常个人积分余额与流水页面|正式Nest main/owner schema/正常WebIAM会话/合法既有账户；目前组合缺口|UI积分页→Web/BFF→Billing两v2GET→刷新/分页/异常恢复→核无写入；无账户404不seed|金额精度/cursor/auth/no-store及持久事实一致，读取零账务效果|**未执行**：已证main仍旧v1与两v2GET未组合，独立于财务grant/费用/支付，不应串行等待后者|P0/完整用户E2E待验|

Root verify938纯项/Prisma0与独审96946524只辅助源码。正常browser观察getState超时/内核reset，没有DOM/像素结果，不算产品PASS或FAIL；原八探针200只可用性。剩余authority/drift/超量输入、全integration、真实用户赠送/余额/收费、axe/移动视觉仍按原组待验。BFF快照读审已撤回将route-scope当新owner权限的误判，跨tab旧URL归属先真实复测，不预设404。

## R255 03:15 T-B07 注册安全辅助证据与正式业务待验（沿原70组）

**统计仍70组：11 PASS /8 FAIL /14 RETEST /36 UNVERIFIED /1 PAYMENT-LAST；新增用户PASS=0。** IAM源码main 4bfef00d。下列PG是真隔离PostgreSQL+实际BetterAuth/API，但不是正常用户资金E2E，不能改T-B07整组状态。

|用例ID/类别|标题|预置条件|步骤|预期结果|本轮实际|优先级/类型|
|---|---|---|---|---|---|---|
|T-B07.R255-REG 主链/状态|显式财务human受管注册|真实operator Session、active tenant、准确User集合、IAM resource；Root自有PG fixture|managed创建→官方/持久双读→核ownership、单scope、Code/PKCE/Basic/false consent及唯一绑定|只注册精确metadata，不向普通client授scope，不默认operator有赠送权|旧source合法请求拒的RED；最终三file18/0含本例，目录77→77 exact。仅源码辅助|P0/业务接口集成|
|T-B07.R255-RESERVED 权限/异常|普通/admin升级与财务名单变更拒绝|真实普通client与financialclient，具名operator Session|native普通client升级financial、错误financial注册facts、合法financial通用名单修改；回读原事实|稳定拒绝、原数据不变；不能靠metadata变更取得财务权|旧源码两负控真实成功（有效FAIL）；修后通过。非operator/未知User旧schema已拒，不冒新权限RED。清空metadata/rotation/inactive/empty/多ID/101独立实跑仍待补|P0/安全集成辅助|
|T-B07.R255-ZERO-ISSUE 状态/异常|注册期间明确禁止financial新发行|合法注册，真实Code+PKCE+consent与current metadata|真实authorize→Code→token，显式/省略token resource；读access/refresh记录|精确403/access_denied、Financial grant issuance is not enabled、零token新增；普通登录不改变|实际两兑换明确拒且零新增。省略resource继承Code资源，不等实跑opaque；全新建接缝静态已核，defaultscope/旧refresh replay未冒通过|P0/安全生命周期辅助|
|T-B07.R255-ORDINARY 回归|普通受管OAuth/固定Web与Session生命周期保持|原合法ordinary/Skill profile、真实fixtureSession/PG|完整运行client lifecycle、fixed Web、session lifecycle三原文件|Code/refresh、固定所有权、Skill升级与撤销仍按原语义，普通scope不加financial|Root三文件18 pass/0 fail，13.22秒；本例与上述同一结果重叠，不求和。全IAMintegration未跑|P0/真实owner回归辅助|
|T-B07.R255-NORMAL-GRANT 主链/边界/权限/状态|正规管理员授权赠送及个人余额完整链|正常IAM current资格/名单CAS及machine verifier、Billing v2正式入口、真实两个用户；当前尚缺|正规登录→具名赠送actor授权→选当前tenant target及显式reason/amount→同幂等提交→UI余额/流水→刷新→重放→取消资格后重试→跨tenant反例|一次入账/可核audit，重放不重复；资格撤销即时拒，target隔离；UI与权威余额/流水一致|**本轮未执行**：issuer故意关闭、CLI/SDK/Billingcaller未接，未赠送/充值/资金调用。注册绿不关闭本例|P0/完整系统E2E待验|

主窗口Node24 pnpm verify（102纯文件938项）/prisma:validate均0只补研发门；独审f3c76480/15冻结exact零阻塞问题但不当运行证据。创建/link/readback非整体原子，残留不返凭证且仍拒签，后续正式管理恢复应单独验。八健康200不代表页面通过，browser控制/关闭自有tab超时未观察DOM与像素，不新增产品失败或成功；Playwright/axe/移动/视觉/bundle、真实模型和收费结算本轮未跑。完整退出仍正常UI→owner权威事实→刷新/错误恢复→权限/资金一致；证据同0315-iam-root-{red,boundary-red,integration,gates}、commit-receipt和browser-observation-block，不另建QA中心。

## R255 02:44 排程消费者验证记录（T-P02 子例，非新测试中心）

系统验收统计仍70组11 PASS/8 FAIL/14 RETEST/36 UNVERIFIED/1 PAYMENT-LAST；本波用户PASS+0。工程辅助不替代下表正常系统路径。

|用例ID/类别|标题|预置条件|步骤|预期结果/实际|优先级|类型|
|---|---|---|---|---|---|---|
|T-P02.R255-NEXT-WEB-01 主链/状态|owner null与确认时间投影|冻结Web022e820、actual Response辅助输入，不是正常网络|接收paused/null及active/confirmed string→client→列表→日历|null原样保持、无time/无calendar event；string原样显示/分组。Root旧实现四文件148/139/9失败；冻结修后及提交后148/0。仅辅助通过，真实页面未验|P0|契约/交互辅助|
|T-P02.R255-NEXT-WEB-02 边界/异常|缺字段和旧next输入拒绝|现wire十required与owner45e67f0固定artifact|逐required字段去除→strict parse；合法/非法UTC anchor；旧next create/PATCH；核exact snapshot/pins|缺失不当null、旧next/未知属性拒；合法optional anchor接受。Rootfullcontract274/0、非system2657/0；不是完整系统E2E|P1|边界/契约一致性辅助|
|T-P02.R255-NEXT-02 主链/生命周期|正常排程创建/确认/暂停恢复/刷新|正常IAM/BFF/Scheduler；先安全局部schema激活，再browser控制可观察|正规登录→weekly08:00创建→待owner确认→列表/日历/硬刷新→暂停→刷新→恢复→确认→刷新→观实际执行与下一次|pending/null、confirmed owner正确UTC、暂停null不保旧日期，持续next/执行事实一致。**本波未执行**：schema请求一次待答、BFF旧loaded；browser focus超时无页面证据，T-P02整组仍原FAIL而非新PASS|P0|完整系统E2E待验|

正常HTTP健康200仅资源检查；浏览器CDP focus timeout归观察阻塞、不归产品loading失败。未跑全system/Playwright/axe/视觉/移动/bundle或真实provider，不用辅助数量冒最终上线条件；退出仍需真实用户完整路径/异常恢复与权威结果。证据同0244-web-root-{red,contract,non-system,postcommit-focused}.log、0244-web-commit-receipt.json及0244-browser-observation-block.json。

## R255 02:02 排程源修复证据与正式用户复测待办（沿T-P02）

**验收状态不变：70组11通过/8失败/14待复测/36未验/1支付后置。T-P02仍FAIL。** 本轮没有浏览器操作、真实Scheduler执行或真实模型费用，以下正式用户路径尚未重新执行，不能用175工程断言代替。

|用例ID/分类|标题/优先级/测试类型|预置条件|真实用户步骤|预期结果/本轮实际|
|---|---|---|---|---|
|T-P02.R255-NEXT-UI 主链路|周任务持久规则与下次时间，P0/系统E2E|BFF候选已发布，Web固定消费者对齐，批准的局部schema激活，真实IAM/Scheduler；当前尚未满足|正规登录→排程页创建weekly、08:00与IANA时区→等保存结束→看列表→硬刷新→重新打开|规则/anchor稳定；pending不得编造时间，confirmed next与Scheduler一致；刷新字段/身份不变。**未复测**，此前创建瞬时点当08:00的FAIL保留|
|T-P02.R255-NEXT-EDIT 状态机|编辑/暂停/恢复后显示一致，P0/交互E2E|同上述，仅本次QA任务|打开编辑改时间→保存→看真实回执→刷新；暂停→刷新；恢复→刷新|提交有界/防重复，修改后旧next立即失效；暂停next为空/不显示运行中；恢复只展示当前规则确认next；无整页永久loading。**未复测**，此前保存收尾子例已通过不扩张|
|T-P02.R255-NEXT-TZ 边界|时区/周锚点/DST边界，P1/业务E2E|真实任务UI/API、确定规则及可观测真实Scheduler；任务不触发外部资金/工具|比较本地UTC边界与IANA时区；创建/编辑跨日期周规则；有DST时验证过渡日前后|时区与weekday按owner原锚点规则，UTC瞬时点/本地展示分开；无Web自算两份事实、非法值明确拒绝。**未复测**，原weekly语义没因字段分离改规则|
|T-P02.R255-NEXT-ERROR 异常|网络失败/错误回执后恢复，P0/系统异常|受控局部故障，既有正常服务/数据保护；任务自己的数据|保存期间断网→恢复→重开列表；受控owner拒绝/无效receipt→重试→刷新|不显示伪成功/旧确认next；错误可恢复且有限重试；同幂等任务只一份。**未复测**；内部PG/HTTP负控仅支撑实现|
|T-P02.R255-NEXT-PRIVATE 权限|跨主体/租户隔离，P0/安全E2E|两个正规独立用户，授权与owner真实|另一用户打开QA task URL/列表尝试编辑→原用户刷新核事实|无泄露/他人写入、错误稳定，原数据不变。**未复测**；不能用SessionAdmissionDouble当真实权限通过|
|T-P02.R255-NEXT-EXEC 状态机|到期执行及持续next刷新，P0/完整业务E2E|正规费用许可、真实Scheduler→BFF→Agent→provider与durable终态；当前尚缺|安全任务到期→观察执行/Agent事件→刷新任务→核下一次→取消/失败验证余额及流水|执行无重入，同轮事实唯一，next随当前Scheduler事实更新；已核实实际费用结算/余占释放/流水一致。**未执行且持续next读取仍需实现**，不能关闭完整排程组|

**辅助源码证据（不是上述用户PASS）**：BFF e603bd55、verified index77c81139；旧真实PG8 tests/1pass/7fail（父fail计入），修后混合5文件174/0，再精确index5文件175/0/0skip并保HEAD R237 catalog；真实PG/共享既有Redis无reset，自有库目录77→77 exact。Scheduler/Agent/IAM为localhost/in-process doubles或替身，真实provider未用。纯门默认779pass/2资源skip、schema10pass/2skip、完整contract242pass/0fail。原mixed工作树format1保留，干净index format0分别记账，不冒仓库整体干净。

**测试问题归因纠正**：生成ACK validator已有，负控13/13无生产改动即通过，不是有效新RED；前次validator P1撤回。fence0、过去claim时间、URL options属于fixture错误，原日志保留；修正后有效stale反例在success前确认仍leased/next=null再正控成功。最终暂存独审625092a8零问题。现正常schema仍旧、一次局部重建请求待答，normal服务未重载/Web pin未更新，产品状态不变。IAM aab41820只是财务授权D0，未充值/赠送/调用模型/结算。

所有证据仍Root ignored var/dev/r255-preserve/0202-*，任务/缺陷沿原同卡。退出标准必须上述完整用户路径真实通过、错误可恢复且owner资金/权限一致；不靠断言数量/接口200清零缺陷。

## R255 01:41 QA子例结果：真实owner事务回归，不冒完整用户E2E

下列仍归既有T-B07/T-P02；不新增第71组。当前正常70组保持11通过/8失败/14待复测/36未验/1支付后置。Billing前置均为abd809a1现服务层+真实隔离PG fixture及可信tx actor，无mock/正常余额写入；主链系统验收必须另走真实管理员入口→目标授权→赠送→本人余额流水→聊天预占/结算，现未通过。

|用例ID/分类|用例标题|预置条件|测试步骤|预期结果/本次实际|优先级|测试类型|
|---|---|---|---|---|---|---|
|T-B07.R255-REASON-01 主链|赠送原因保持原文且可审计|现Credit effect、本人账户、合法含中文/emoji及两端空格原因|合法grant→读journal/receipt/audit→用相同身份/同键/同payload重放→再次读账|原文reason一致、v2 digest/version=2、一次账务效果；真实PG通过。非正常管理员页面E2E|P0|业务事务集成|
|T-B07.R255-REASON-02 异常/幂等|同键只改原因不重复入账|已成功grant及原receipt|其他字段保持、修改reason后以原key重试→核receipt/余额/journal/audit|幂等冲突且无第二次effect；真实PG通过|P0|异常/账务一致性|
|T-B07.R255-REASON-03 边界|原因1及500个Unicode码点合法，501与空原因拒绝|新自有账户/命令identity|依次提交1/500码点合法原因；独立key提交missing/nonstring/empty/whitespace/501/NUL/单surrogate→查各账务事实|合法两边界保存原文；非法请求零grant/journal/audit/receipt变化；真实PG通过，原RED曾缺/空/超长仍入账|P1|边界/数据完整性|
|T-B07.R255-REASON-04 状态/回滚|effect非法原因被catch仍令外层回滚|外层真实PG事务及effect直入口|先在同事务产生写入→调用非法reason effect→捕获异常并尝试commit→查库；另验audit失败尾部回滚|不得partial commit；所有当前事务事实回滚，真实PG通过|P0|生命周期/事务容错|
|T-P02.R255-NEXT-CONTRACT-01 边界|锚点输入/next输出机器候选|BFF1d9c5e61 public8.0.0尚未发布；原92ops|现canonical schema检查→破坏nullable/required/date-time/回退旧字段→同semantic入口检查|合法机器候选通过、四破坏拒绝；Root focused77/0/fullcontract242/0；仅辅助，不是正常路由行为通过|P1|契约一致性|
|T-P02.R255-NEXT-02 主链/状态|正常weekly08:00确认与刷新|原真实3310/IAM/Scheduler及现任务；当前source/SQL仍旧实现|正常创建→观察pending next→等Scheduler确认→列表/硬刷新→编辑→再确认→暂停→刷新|待确认应null，确认应owner正确08:00，暂停应null、旧ACK不覆盖；当前原创建next=创建瞬时点反例仍FAIL，本轮未重跑/未关闭|P0|完整系统E2E（待实现复验）|

Root154PG通过/12legacy skip与诊断9通过仅支持上列内部修复；不拿skip/工程数量充当业务完成。不执行同共享库reset；隔离库目录前后77 exact。测试通过标准仍是当前正式页面的完整交互+权威持久结果+异常恢复，截图/ready/contract绿均不足。

## R255 01:26 MCP列表有限修复复验（不关闭T-K05整组）

|用例ID/分类|标题/优先级/类型|预置条件|真实步骤|预期与实际|
|---|---|---|---|---|
|T-K05.R255-LIST-02 主链/异常|正常目录空态恢复，P1系统E2E|同IAM/3310、Platform9ab3b653正常持久四surface、既有projection凭据|外挂→管理连接器→等终态→关闭设置|真实GET200、body data.servers=[]；合法空态，无加载错误；关闭回外挂。只证明server目录，不证明本人连接/实际provider接通|
|T-K05.R255-LIST-03 状态机|硬刷新后重读，P1系统E2E|同配置与正常服务，关闭modal|硬刷新→等页面→管理连接器→读取→关闭|再次实际GET200（70268.2745）且同servers=[]，UI空态可关闭；通过该子例。刷新期间短暂workspace loading随后已渲染，不当无限loading修复证据|

证据0126-mcp-green-response.json、0126-mcp-refresh-response.json、0126-mcp-green-refresh.{md,png}；无cookie注入/隐藏fetch/mock/数据库填空。Root受控Platform旧会话exit0后单副本重载，八探针200仅资源检查。MCP注册/授权连接/撤销/重连/执行与server目录混用UI尚未闭环，T-K05整体继续失败，70组11通过/8失败/14待复测/36未验/1支付后置。下段为本轮真实RED历史，不覆盖当前列表子例。

## R255 01:26 MCP管理实际失败（归T-K05）

|用例ID/类别|标题与优先级|预置条件|步骤|预期/实际|
|---|---|---|---|---|
|T-K05.R255-LIST-01 主链/异常|本人连接器列表，P1系统E2E|正常IAM会话、3310及Platform原进程|外挂→管理连接器→连接器设置→重试→关闭设置|应真实列表或合法空态；实际502 skill_response_invalid/加载失败，重试仍失败；关闭设置恢复原页面，非无限loading。未创建或改变任何连接权限|

证据var/dev/r255-preserve/0126-mcp-response.json及0126-mcp-settings-red.{md,png}。T-K05未验→失败，70组11通过/8失败/14待复测/36未验/1支付后置；T-K01防假Connected旧pass不变。新失败尚未修，不填空列表冒成功。

## R255 01:14 排程真实行为用例（归T-P01/P02，不新增组）

|用例ID/类别|标题/优先级/类型|预置条件|真实用户步骤|预期与实际|
|---|---|---|---|---|
|T-P01.R255-SAVE-01 主链/状态机|保存终态收尾，P1/系统E2E|正常IAM/3310，单次本QA任务|建立→填标题/提示词/每周08:00→保存→等接口与UI|旧create/list200但saving/取消disabled永久保留，为有效RED；本次仅保存生命周期修复。未重新创建另一任务作GREEN（已知排程时间错误），不声称完整创建复测通过|
|T-P01.R255-SAVE-02 主链/状态机|编辑成功自动退出，P1/系统E2E|同QA已暂停；冻结Web97a79d45|任务菜单编辑→改QA标题→保存→等弹窗hidden→刷新|PATCH/list200、弹窗自动关闭；标题保存且paused保持；真实GREEN。新内容未从preview/mock来|
|T-P01.R255-SAVE-03 边界/取消|空白标题不可提交、取消无写，P1/UI E2E|同已保存paused QA|编辑→标题填空格→核保存disabled→取消|实际保存disabled，取消退出且列表仍已保存标题；通过。迟到回包/卸载错误分支仅独审，未完整网络故障实测|
|T-P01.R255-PAUSE-01 状态机|正常暂停持久，P0/系统E2E|本次唯一QA任务active，autoApprove=false|菜单暂停→等200→硬刷新|已暂停且刷新保持；通过。不认为UI此前运行中=真实Agent已执行；未恢复/永久删|
|T-P02.R255-NEXT-01 异常/时区|每周08:00不显示创建时刻，P0/系统E2E|同真实每周08:00 America/New_York输入|创建一次→读取响应/list→核页面当地时间|实际next_run_at=2026-10-06T01:16:12.377Z，当地21:16不是08:00；FAIL未修，T-P02从未验改失败。BFF丢owner receipt与周锚点混用确证；不私改前端补算/默认值|

Root现8文件79辅助通过与lint/types/build0不替代上述行为；独审3c0b9d11只源码放行。唯一QA scheduled_18ce2a4c0b2745e247fce557562be15b保持paused，Root未删除/恢复任务、主动调用模型或写入资金；未据此断言后台执行次数为零。现70组统计11通过/7失败/14待复测/37未验/1后置；其余历史统计为当时事实。任务卡与handoff旧T-S01.R255名称属于worker切片，现系统组T-S01不受影响；用户用例归既有T-P01/P02。

## R255 01:03 正常聊天失败复现（沿T-C01，不增加统计组）

|用例ID/类别|标题/优先级/类型|预置条件|真实用户步骤|预期与实际|
|---|---|---|---|---|
|T-C01.R255-NORMAL-SUBMIT 主链路|正常新会话真实模型回答，P0/系统E2E|当前Web2dece456/BFF97a99d35，正规IAM Session；八现owner alive|新对话→输入非敏感1+1→发送一次→等终态|预期正式积分许可后回答与durable终态；实际POST503 agent_not_configured、无回答，**FAIL**。当前false开关在持久提交前拒绝；未声称模型已被调用/扣费|
|T-C01.R255-NORMAL-REFRESH 状态机/异常|未接受消息刷新不伪装已存会话，P1/交互E2E|第一条提交已失败、仅本地临时conv与提示|硬刷新原conversation URL→读界面和实际snapshot响应|实际snapshot404，URL仍临时ID而界面空Home；记恢复/提示UX待对齐，不能视为已接受消息丢失或证明snapshot事务错误。不得据此放行发送→刷新续流|
|T-C01.R255-NORMAL-DEPENDENCY 异常|缺依赖不以免费fallback发送，P0/安全链路待验|当前BFF开关false，Agent现代码缺Billing consumer|只读核打开开关后的完整调用序|源码会202后到Agent dependency_unavailable，零provider send；这是只读判断，未实际打开/运行worker，不计E2E PASS|

本轮提交观察前已启Network，稳定error body与PNG留存；第一条提交Network未启、刷新capture静态事件truncated，两观察局限明确保留。agents GET404实际route_not_found、billing summary503、runtime-manifest403只列观测，不凭无body推相同根因。没有并发启动/重置/绕过收费许可，八探针200不是聊天通过。70组11/6/14/38/1保持，源代码修复与正常模型回答、正规积分结算、断线续流退出门均仍OPEN。

## R255 00:45 正常Skills页面与无效包组内验收

|用例ID/分类|标题/优先级/类型|预置条件|真实用户步骤|预期与实际|
|---|---|---|---|---|
|T-U01.R255-INSET-01 主链路|正式页边距，P2/UI E2E|Web2dece456，1280×720正常IAM/八owner|技能页读完→展开/折叠侧栏|原h1贴左0px为RED；修后24px，折叠960px居中，页面无横溢；通过|
|T-U01.R255-INSET-02 边界|360px页头与发布入口，P1/UI E2E|同候选、临时360×720尺寸|读技能→发布→核提交状态→关闭|内容328px/16px边距，保既有展开按钮56px标题净空，按钮换行无溢出；缺字段提交disabled，弹窗关闭返回；通过，尺寸已clear|
|T-U01.R255-INSET-03 状态机|设置技能不被页面host污染，P1/E2E|正常已发布本次QA源|我的技能→等待Settings技能读完→关闭|同原合法技能行，有shared reader无personalPage新wrapper，设置不横溢、关闭回原页；通过；其他Settings标签未验|
|T-K02.R255-N04 异常/边界|V1 manifest明确拒绝，P0/系统E2E|普通本地无执行ZIP，正常IAM与Platform/Storage|发布→选无效包→填写→提交→等终态→关闭→硬刷新|真实Validate 400、明确owner拒绝且有新尝试按钮，无ACTIVE/安装假成功；原合法源保留；通过。未验证失败草稿GC/所有恶意包/tenant隔离|

Root当前既有7文件141辅助通过、lint/types/build0，冻结独审0问题只作辅助；70组统计保持11/6/14/38/1，不关闭T-U01/T-K02整组。高级尺寸接口超时为工具观察限制，文档支持CDP模拟成功并已恢复1280×720；早前文件选择工具超时未实际提交，本次选择上传真实成功到校验拒绝。证据同ignored var/dev/r255-preserve/page-inset-root-commit-receipt.json与DOM/PNG。

## R255 00:30 正常3310 Skills本人主链实测（T-K02/T-K03组内证据）

| 用例 | 前置 | 用户步骤 | 预期/实际 | 优先级/分类 |
|---|---|---|---|---|
| T-K02.R255-N01 | 正常IAM登录，正式Platform/Storage/BFF持久组合 | 技能→本人已发布 | 合法空态，实际正常终态；旧加载失败已解除 | P1/主链路 |
| T-K02.R255-N02 | 同上；393B普通manifest V2+SKILL.md ZIP | 发布个人技能→选包→填名称简介标签→上传并发布 | 上传/扫描/Validate/Publish真实owner200，UI ACTIVE发布回执与列表；实际通过 | P1/主链路 |
| T-K03.R255-N01 | 本次已发布revision1 | 安装→本人安装→停用→硬刷新→本人安装 | installed/enabled→disabled，刷新仍disabled；实际通过 | P1/状态机 |
| T-K03.R255-N02 | 本次disabled安装 | 启用→移除安装→硬刷新→本人安装→本人已发布 | 安装合法空态、发布源仍保留；实际通过 | P1/状态机 |
| T-K02.R255-N03 | Platform正常listener，不带认证 | GET /v1/skills | 实际401；仅匿名负控，不冒tenant隔离全验 | P0/安全 |

最终PNG确认主区标题/卡片贴左，间距/视觉一致性作为T-U01后继P2，未因功能通过抹掉。

以上是正常开发页面而非旧隔离fixture，唯一技能skill:e493e093-84c4-40df-bbcd-e7426a985e44/revision1；只新增本次QA发布源，安装已正规移除，可重新安装。0模型/资金调用，不删除用户既有数据。证据var/dev/r255-preserve/browser-normal-skills-journey-receipt.json和8终态DOM/最终PNG。恶意包/超限ZIP/越权/ACK未知/详情撤回/Agent真正加载执行/MCP尚未验；整组T-K02/T-K03不关闭，70组11通过/6失败/14待复测/38未验/1支付后置不变。

## T-F01.R255-NORMAL：正常持久源代码资料库用户验收（组内子例）

|用例ID/类别|标题/优先级/类型|预置条件|真实测试步骤|预期结果/实测状态|
|---|---|---|---|---|
|T-F01.R255-NORMAL-01 主链路|本人文本上传与扫描，P0/系统E2E|正常IAM用户；当前Web/BFF/Storage、共享MinIO/ClamAV；本次唯一123B UTF-8 QA文件|资料库→选择文件→上传→等扫描与权威行|仅CLEAN后成功，filename/MIME/123B真实行显示；本次通过，不证明感染/unknown/撤权分支|
|T-F01.R255-NORMAL-02 主链路/状态机|持久读回与下载一致，P0/系统E2E|上例文件成功，不更改身份或数据|硬刷新→等资料库行→点击下载→核原生保存字节|文件仍可见，每次合法下载不借旧URL，123B与原SHA/bytes相等；本次通过。工具download事件超时但已真实保存核对，记录工具局限|
|T-F01.R255-NORMAL-03 边界/异常|总上传请求超限，P1/系统E2E|已上传原123B文件；本次1048577B非敏感文本|选择超限文件→上传→读明确错误→刷新|明确总multipart≤1MiB错误，无无限loading、原行保留；本次通过。恰好边界/零字节/特殊文件名另待验|
|T-F01.R255-NORMAL-04 状态机|文件与作品互不串槽，P1/系统E2E|正常资料库；本人文件已上传|作品标签→等待终态→返回个人文件→刷新|两数据与选择隔离，加载有限；本次仅观察作品初始loading后返回，不计作品empty/成功，完整子例待验|
|T-F01.R255-NORMAL-05 权限/异常|跨主体与未知上传恢复，P0/系统E2E|两正式账号/可控ACK未知或扫描pending；不同tenant正负数据|A上传未知→保原key显式重试→正规切B→A迟到→B读取/下载|不重复资产、不串本人资料、撤权不下载、同意图恢复有界；本次未执行，不用历史组件/owner测试关闭|

证据：ignored var/dev/r255-preserve/browser-normal-library-journey-receipt.json及最终PNG。只完成本人小文本主链/超限子例，不关闭T-F01异常/权限/项目文件/Agent作品整组，70组11/6/14/38/1保持。用户资料未删，正常服务句柄复用，测试文件仍留资料库用于后继复验。

## R255 23:41真实浏览器子例（不新增70统计组）

|用例ID/类别|标题/优先级/类型|预置条件|真实用户步骤|预期结果与实际证据|
|---|---|---|---|---|
|T-A01.R255-LOGIN 主链路|正式登录刷新，P0/E2E|现正常IAM/Web持久配置，已有账号|从/login填写既有账号→登录→/app→硬刷新→打开原会话|进入工作区、正文/输入框正常；实际通过该子旅程，无cookie注入/改密码，尚未覆盖整个认证异常组|
|T-C05.R255-MOVE 状态机|直接与项目归属迁移，P0/E2E|既有R243直接会话/项目5251c78c|移动到项目→点文件夹叶子→核原正文→硬刷新→移动到直接会话|叶子挂正确文件夹，外部直接列表常驻，正文保持无重复，原scope恢复；实际通过该子例，非删除/全部项目CRUD|
|T-C05.R255-RENAME 主链路|非当前会话改名保持，P1/E2E|同原直接会话|行改名→Enter→硬刷新展开侧栏→恢复原名称|名称落库刷新保持、UI原名称恢复ACK；实际通过，原改名数据已恢复，无永久删除|
|T-B03.R255-NO-OWNER 异常|资金未知不伪造免费，P0/E2E|Billing正常入口未启|账户菜单→设置账户→积分|应有限错误且不免费/每日赠送；原假免费/每日文案真实失败已修，冻结源真实菜单/账户不再虚构，积分实际错误→重新加载→错误→关闭回工作区通过子路径；资金成功旅程待验|
|T-P01.R255-SKILL 异常|技能池读取，P0/E2E|Platform正常入口未启|点击技能→等待数据完成|实际技能池加载失败，不冒空池/CRUD通过；正常owner与发布/安装/执行仍待验|

证据：ignored var/dev/r255-preserve/browser-normal-user-journey-receipt.json及同目录DOM/截图。代码变化中的热更新错误不算冻结最终验收；70组11/6/14/38/1不变。

## R255 T-B03 本轮有限证据 / 用户验收仍OPEN

以下是T-B03组内子例，不新增统计组；全部完整用户路径仍待验，组件/合同反例只辅助定位。

|用例ID/类别|标题/优先级/类型|预置条件|用户行为步骤|预期结果/当前状态|
|---|---|---|---|---|
|T-B03.R255-CREDIT-01 主链路|本人余额与流水一致，P0/业务E2E|正常IAM用户、唯一正常Billing进程、正式账户和授权owner流水|设置→积分→查看可用/预占→加载下一页→关闭重开→硬刷新|显示owner精确值与原序，只有两GET，无Free/quota/daily/by-model伪值；待真实owner/浏览器|
|T-B03.R255-CREDIT-02 边界|大数与最小单位，P1/边界E2E|合法one-micro、>2^53值/负delta、UTC时刻账本|查看余额和每项/日期→分页→刷新|BigInt显示准确，micros换显示单位不是费用倍率，UTC按locale无符号精度丢失；待验|
|T-B03.R255-CREDIT-03 异常|缺账户/过期/停机不假零，P0/异常E2E|正常准入、合法零账户与缺账户分别准备；可由Root控制owner停止|分别读取→过期→正规重登→owner不可用→恢复→用户重试|合法空、404、401与503区分，有限退出加载，旧余额不当实时成功，不伪造充值/免费；正常HTTP503/过期401只是辅助观察|
|T-B03.R255-CREDIT-04 状态机/权限|刷新分页与主体隔离，P0/交互安全E2E|两正常账号，分页游标和可控迟到读取|A加载更多途中刷新/关闭→正规切B→旧A迟到→B再打开→终页|旧结果退役，下一页单flight/原opaque cursor/null终页，失败明确可重试不循环、不串主体；待验|

Billing54a64427当前真实owner PG publication/联合选版38/38/0skip，原public catalog误查3fail已仅固定kokoro_billing；此测试切片不是Credits正常用户旅程，不改变70组统计。正常BFF32914已装载97a99d，正式IAM HTTP session200，两实际同源GET503 billing_unavailable/private-no-store/request-id；无Billing normal host，不能把合法无账户/空态或赠送/扣款当通过。WebD0 d51a0c3已发布，当前Root新增6有效consumer/组件RED（68pass/6fail/0cancel、types/lint0）已定位旧strict shape/free/quota/by-model，独审6有效但尚缺取消/预算/分页/身份/adapter覆盖1P1，尚待先行门补齐/实现/真实browser。原上下文无限loading、folder/direct与费用用户验收保持原状态；不以38后台测试把T-B03关闭。

## R255 T-B03消费者源码交付，不关闭整组用户用例

BFF97a99d35真实当前工程默认777/0/1schema skip、controlled HTTP target70/70，独审928f5b29零问题；旧有效反例41/19→强化41/25及中途安全网P1保留。caller取消实际关闭owner请求、总header/body cap、持续body总deadline、redirect二receiver零调用/凭据零转发已锁；本机peer不是正式Billing/IAM组合或真实浏览器。正式余额/流水、授权赠送、预占/结算/释放、实际模型消费和UI展示一致仍按原T-B03/B07退出门待验；不为源码绿更新70组通过数。正常BFF79304未载新源码，完整Wave0–7/70组11/6/14/38/1保持。

## R255 T-B03消费者工程反例与正常页读取（不增70组）

Root stage2 HTTP受控peer60例41pass/19fail用于接线定位，不是正式Billing/真实用户PASS。独审额外锁：owner401/403服务credential故障映射503而非登出本人、caller cancel必须观察owner请求结束、cursor原样/单值与严格limit、空身份零ownerI/O。原writer只强化现test，源码待Root新RED确认。用例退出仍T-B03.R255-I01正常登录→实际余额/流水→分页/硬刷新→授权赠送及资金链对账；没有真实owner启动/浏览器/收费证据仍OPEN。

正常Library个人文件/作品、项目列表、独立排程四GET自然过期401后，正规IAM表单/OAuth重登200/private no-store，收据var/dev/r255-preserve/normal-fixed-page-owner-read-sweep{,-expired}.json。只关闭读取反例观察，不关闭整页CRUD/下载/排程执行/加载状态子例；缺request-id另核Web实际合同。0新增完整浏览器PASS，70组11通过/6失败/14待复测/38未验/1支付后置保持。

## R255 Chat有限提交回归子例（归入既有T-C01，不新增组）

|用例|标题/预置|真实用户步骤|预期结果|优先级/类型|当前证据与状态|
|---|---|---|---|---|---|
|T-C01.R255-TURN-BUDGET-01|提交等待有限且不中断其他会话；正规登录/本人两会话、owner测试可控锁/延迟、正常Agent/Billing前置|会话A提交→注入BFF提交锁等待→观察加载退出→切B再返回A→刷新→按正式反馈重试原请求|BFF沿唯一有界事务；超时/取消不留下半条Message/outbox，不把未知提交报成功；UI退出无限loading且草稿保留；A的迟到结果不抢B；重试身份不复制消息/收费|P0/异常、状态机、交互|默认门发现旧mixed无界旁路，已恢复HEAD唯一4500ms helper、Root747/0/1skip；没有真实浏览器/PG锁旅程，待执行，不计PASS|

四collection scope fixture缺setHeader仅工程安全网错误，不作为该用户子例失败证据或完成证明。阶段3目标82/0与clean默认747/0/2skip仅辅助；两schema资源skip没有执行。完整70组11通过/6失败/14待复测/38未验/1支付后置保持。

## R255 项目改名真实运行反例与修复记录（子例，不新增第71组）

|用例ID/标题|预置条件|行为步骤|预期结果|优先级/类型|实际结果/状态|
|---|---|---|---|---|---|
|T-C05.R255-RENAME-01 / 改名入口可达与幂等|当前固定3310；原账号正常IAM表单/OAuth登录；现本人项目；名称原值不改；全owner持久数据|①读取项目②原name+新key PATCH/name③同key同body重放④同key改body⑤重新读取项目|首次200且receipt精确；重放同200；漂移409且不改名；no-store/request-id；原name保持|P1 / 功能、异常、状态机|Root22:19有效503RED；仅三HEAD seam恢复+独审+Node22 type/build0，BFF同源重启；22:21真实正常HTTP链200/200/409、读回保持。**HTTP子例通过，完整浏览器操作与真实改名刷新待验，不关闭整组**。证据var/dev/r255-preserve/normal-fixed-project-rename-red.json与green.json|

本轮已有cookie首次401只记录为准入过期，正常表单重新登录后才运行上述有效业务反例。不操作他人项目、不给SQL注资、不冒整个页面闭环。0新增完整浏览器PASS，70组11/6/14/38/1保持。

## R255 正常运行组合已切换：用户用例不由HTTP门代替

同既有T-C.R255-P01/P02、T-Q/T-B03与TC-R254-C01..09，不新增第71组。7源码owner ready200、正常HTTP登录与同源列表200；真实右侧新tab8的/login已直接显示IAM账号密码表单，无中转重试。等待原密码浏览器登录后继续操作，0新增完整用户用例PASS，完整70组11/6/14/38/1保持。

|分类 / 用例|预置条件|用户步骤|预期|优先级/类型|本次状态|
|---|---|---|---|---|---|
|主链 / T-C.R255-P01|固定源码3310、原账号/项目/聊天保留|IAM表单提交→工作区→普通列表→逐folder展开→CRUD/Move→硬刷新|身份/归属不变，普通会话常驻，folder独立，无永久loading|P0/系统端到端|仅登录入口显示实观；HTTP登录/2普通/2项目/空project list200为辅助；整例待验|
|异常/状态 / T-C.R255-P02|同正常组合；真实断连/恢复在Root资源边界内|打开既有正文→刷新/断连→恢复→重新打开|同会话正文、单调cursor、loading退出、无重复/跨scope迟到覆盖|P0/端到端状态机|待验；模型worker关闭不当续流通过|
|异常 / 原排程用例|Scheduler已正常ready；现BFF callback为loopback|正式创建排程→到点执行→查看结果/取消|owner政策与真实callback一致、持久状态/实际调用可核对|P0/系统功能异常|真实启动曾拒IP allowlist，保原空策略ready；callback链尚未验收，不关闭SSRF|
|主链 / 原T-B03|Billing/BFF/Web个人读取正式接线后|真实用户打开Credits→余额/流水分页→刷新|owner micros精确一致，无假零/旧比例计算|P0/系统业务|仅BFF D0已提交/独审；Billing未运行、D1实施未验，不称积分通过|

资源/HTTP/数据接续收据在同CURRENT；退出标准仍为完整真实交互旅程与异常路径实测、原缺陷复测，不以工程测试数量增加完成率。

## R255 当前 canonical 接续与正规身份：辅助实证不关闭用户用例

仍沿T-C.R255-P01/P02、T-Q与T-B03，不新加第71组。原3310真实HTTP表单/OAuth+get-session200；正式operator client正负Basic验证通过。Agent/BFF当前fresh schema＋旧数据44表269行投影exact，System旧published缺输出界实际拒绝，正常源码切换仍OPEN。**本波新增浏览器PASS为0，70组11/6/14/38/1保持。**

|分类 / 子例|预置条件|真实用户步骤|预期 / 退出条件|优先级 / 类型|当前证据与状态|
|---|---|---|---|---|---|
|主链 / T-C.R255-P01|固定源码同3310、原身份历史恢复、正常IAM client与当前schema|真实浏览器登录→普通列表→展开各项目→CRUD/Move→刷新原会话|历史归属保持，普通区常驻，每folder独立；当前auth/proof/AG-UI正常，无整页永久loading|P0 / 端到端功能|待验；原HTTP登录不是此例PASS，正常组合未切换|
|边界 / T-Q.R255-P03 当前模型能力缺失|开发模型revision缺当前正式输出上限、原模型路由/原数据已备份|经正常控制面配置已验证能力并发布→重开聊天→真实执行与积分核对；同时缺界/旧digest负控|缺界不得发布/dispatch；不能拿context_window/default伪充cap、不改immutable历史；合法新发布才准入|P0 / 边界、安全、业务状态|owner数据恢复真实失败ck_model_revision_published_bound，用户链未验；System blocker保留|
|异常/状态机 / T-Q.R255-P02|原归档、target尚无用户新写、失败切换可诊断|模拟受控正常交接失败→完整恢复→正规重新登录和历史深链|无source reset、半态服务、账号丢失或伪会话；新写后禁止盲还原旧archive|P0 / 恢复、生命周期|Agent/BFF独立恢复演练通过仅辅助；System失败已留、原78库exact、target回收；整体用户例待验|
|权限 / T-B03.R255-I02|正常发行issuer、本人/他人账号和current profile|真实owner用户token积分读取/错tenant拒绝→重新登录恢复|当前用户余额/流水正确，错误凭据拒绝；不存在免费/known-zero或机器冒用户fallback|P0 / 安全、端到端|新introspection正确Basic200/inactive与错Basic401仅凭据控制，不是active用户token/积分/browser PASS|

## R255 保数据交接：准备证据与用户退出门分开（2026-10-05）

沿原T-Q/T-C/T-B03生命周期子例，不增加第71组。Root已实际备份/恢复96表（IAM808行、APP3654行），snapshot内容摘要及列/索引/枚举/序列相等；17对CHECK文本差异先失败记录后逐对语义审查，最终metadata严格复核0。收据var/dev/r255-preserve/final-online-rehearsal.json只证明online归档可恢复，不是最终切换/浏览器PASS。

|子例/标题|预置条件|完整用户步骤|预期结果|优先级/类型|当前状态|
|---|---|---|---|---|---|
|T-C.R255-P01 固定源码重启保账号/项目/普通会话|已验证完整归档、最终停写/恢复与正常.env.local、同3310origin；原身份与会话ID记录|正常登录→普通历史→展开各项目历史→刷新→正常停启源码→重新登录并重开原深链|原账号/项目/会话/消息身份与归属保持；普通列表常驻、项目会话挂各folder；无重seed/无限loading；过期session正规登录|P0/主链、生命周期|未执行；online准备通过不关整例|
|T-Q.R255-P02 交接失败与回退保数据|最终归档可恢复、无新用户写入的切换边界及rollback决定|在真实受控交接失败点停止切换→按归档恢复→原账号/历史深链检查|不清邻库/Redis、不造账号/延TTL；恢复失败可诊断，已有数据不覆写丢失；新写后禁止盲回退旧备份|P0/异常、恢复、安全|未执行；自有恢复验证库已回收、78原库集合保持仅为准备证据|

退出门仍是完整用户链，normal main配置/最终drain/实际浏览器验收前不加业务PASS。该时点Web Redis session key0，仅记录自然观测，不生成替代cookie或延长过期。

## R255 Billing身份源码与最终业务测试分栏（2026-10-05）

沿既有T-B03/B05子例，不新增第71组；Billing源码main244b281。Root真实PG消费端HTTP24/24是认证接线安全网（本地JWKS签名），**不是实际IAM签发/BFF/browser PASS**。原正确profile401与unsafe iat200两反例已修，普通/机器隔离、完整profile与zero-write矩阵由consumer锁住；用户端原余额/流水FAIL保持，完整70组11/6/14/38/1不变。

|用例ID/标题|预置条件|真实E2E操作|预期/验收标准|优先级/类型|当前状态|
|---|---|---|---|---|---|
|T-B03.R255-I01 正常登录查看积分与流水|固定正式源码组合、正常IAM账号和Billing授权可追溯赠送，非直接SQL/测试免费|浏览器正常登录→设置/积分→余额→流水→详情→硬刷新并重新登录|实际本人tenant/subject一致；金额、流水来自Billing；无403/503/无限loading；刷新不写账本、不造余额|P0/主链、权限|未验；local签名HTTP正控仅辅助|
|T-B03.R255-I02 错误身份失败恢复|两个本人/他人测试账号、正式IAM issuer及可撤销会话，owner提供受控坏profile|用第二账号/过期会话打开原积分深链→查看错误及重新登录；正式owner授权负控核machine/operator/cnf/旧tenant/坏scope-aud拒绝|无他人余额/流水或读写；错误分支停止加载且可正常恢复，机器和普通用户不fallback；正常会话正控仍可读|P0/异常、安全、状态机|未验；consumer矩阵通过不冒整条用户旅程|
|T-B03.R255-I03 正常重启保身份和账本|固定.env.local/单库owner schema及稳定origin，正式历史余额/流水/用户ID已记录|先查看→仅重启正常源码服务，不installer/reset→正常登录→原积分/流水深链及刷新|原身份和账本保持；正确owner认证/profile仍有效；不造新租户/余额/伪session，过期按正规登录处理|P0/生命周期、恢复|未验；原3310保数据切换未执行|

退出标准：上述完整真实用户路径与owner事实核对通过才关对应业务子例；Billing尚未启动、源码未接入、IAM issuer/BFF前置缺失时记录阻塞，不把后端数量改成页面完成率。

## R254 专案文件夹与常驻普通会话：系统验收子例（2026-10-05）

沿既有T-C01–05新增以下子例，不增加第71测试组。用户明确新规则已更新当前PRD §3/product05；源码已交付Web main e8ff7599a62b045b0e7a3d20e8fd50894b31a099，Root工程复验通过、四mixed保留，但正式运行3310仍旧副本尚未发布此片。以下仍全部待真实系统验收；组件/后端门或静态报告不冒PASS，70组状态不变。完整只读QA设计 `/tmp/r254-project-folder-user-qa.md` SHA c83567fac65274943ea28c6ae210c32b63526654860d7f47c30e09791b51fa4b。

统一预置：正常IAM用户U，已有本人普通持久会话D1/D2、项目A/B及各自会话A1/A2、B1/B2，正文marker可区分；QA自有空项目E。使用既有真实owner数据，费用未经正式准入不为准备列表偷偷发送模型。破坏性步骤只用明确允许删除的QA数据。

|用例ID / 原组|标题|预置条件|测试步骤|预期结果|优先级 / 测试类型|结果|
|---|---|---|---|---|---|---|
|TC-R254-C01 / T-C01,C05|三清单并存|统一预置|Home展开A/B→选择A1→进入Library→返回|D1/D2普通区始终在；A1/A2只挂A，B1/B2只挂B；无独立当前专案会话重复区，无ghost/复制ID|P1 / 主链、交互|待执行|
|TC-R254-C02 / T-C02,C05|展开与选择分离|D1当前，A/B折叠|展开A→展开B→折叠A→重新展开A→点A名称|展开不改URL/正文/草稿、不POST/调用模型；A/B状态独立；名称进入A noquery概览，未切入旧会话|P1 / 状态机|待执行|
|TC-R254-C03 / T-C02,U04|跨组选择/刷新/历史|三类草稿和正文各异|点A1→B1→D2→分别硬刷新及Back/Forward；D当前点击A文件夹新会话，分别在等待中离开/撤准入及目标忙碌时检查|项目叶子带正确project/conv；D2普通路由；原正文/对应草稿与active叶一致，普通区不消失；非当前文件夹plus新ID来自目标engine真实本地草稿，不对随机未知ID取快照、不POST/Run/计费；离开/撤准入/忙碌不晚new或取消旧执行；不默认创建持久会话|P1 / 主链、恢复|待执行|
|TC-R254-C04 / T-C01|局部加载/空/错误|A慢、B读失败、E权威空、D正常|同时展开A/B/E→只重试B|各自状态，E只有成功后空；B错误不阻塞D/A；失败不假空，重试有限，不整页永久加载|P1 / 异常、边界|待执行|
|TC-R254-C05 / T-C01,C02|独立分页与迟到响应|D/A/B各多页，A请求延迟|A加载更多→折叠A→展开B加载更多→选D→A旧响应到达|cursor/hasMore/loadingMore各自独立；不串页/重复提交/重新展开A或抢active；身份及读代际失效不采用旧响应|P1 / 并发、状态机|待执行|
|TC-R254-C06 / T-C03,C05|移动归属不复制|统一预置，自有可移动数据|D1移A→A1移B→B1移普通；观ACK前后并刷新|ACK前不假成功；后刷新原+目标组，原ID/历史不变，不跨组重复；晚ACK不抢后来选择/草稿|P1 / 主链、状态机|待执行|
|TC-R254-C07 / T-C03|非当前组CRUD|A2未在engine打开，当前D1|在A2子行改名→读回→删除先取消再确认→刷新|操作对准A2，不删除D1/错scope；有成功/失败反馈，取消无写入；末行删除后A正确空态，D/B不消失|P1 / 功能、异常|待执行|
|TC-R254-C08 / T-C04,L04|身份与访问隔离|U已展开A，存在无权V/他tenant|A读在途时切V/撤销A权限→等旧响应|旧U项目行/会话不泄露给V；401/403为拒绝非空，旧generation不回写；默认个人私有保持|P0 / 权限、安全|待执行|
|TC-R254-C09 / T-U01,U03|键盘/窄屏/长名|重名/长名项目与会话|Tab→Enter/Space展开→子会话选择→窄屏折叠再打开|独立可辨accessible name/aria-expanded，焦点可见；不误导航、遮挡菜单或裁掉普通区，重名靠ID归属而非名称绑定|P1 / 可用性、边界|待执行|

退出标准：上述P0/P1以固定正式组合真实IAM/BFF用户路径和权威列表/URL/消息/回执证据通过；异常与竞态可先用受控系统反例定位，但必须与真实owner主链证据分栏。页面源码未部署、身份/模型/费用前置缺失时保留阻塞，不改测试成功定义。当前70组11/6/14/38/1不变。

## R252 真实用户验收增量（2026-10-05；不变更70组统计）

|用例|预置条件|真实步骤|预期结果|实际与证据|优先级/类型|
|---|---|---|---|---|---|
|TC-R252-AUTH-01 首页输入登录恢复|固定9d6bc5c4五owner、未登录Chrome无痕、Web16945fe|首页填自有QA提示→开始→正规IAM邮箱密码→/app|本次显式提示完整预填，不自动发起会话/模型|有限PASS，实际Home与提示可见，未观察自动发送；没有网络零mutation计数，不能扩成计费证明。/tmp/r252-home-login-draft-real.jpg|P0/系统、交互、状态机|
|TC-R252-AUTH-02 项目退出后重新登录恢复|同正常用户已正常创建项目82511c9d、两行未发送草稿|项目硬刷新→产品退出→IAM确认→访问原项目URL→再次邮箱密码登录|仍原项目/合法空态/两行草稿，可编辑，不跳普通聊天|有限PASS；/tmp/r252-project-login-return-real.jpg。原3310未更新，真实普通持久会话query/跨主体/BFCache/自然TTL均未验|P0/系统、恢复、状态机|
|TC-R252-DRAFT-03 普通/项目与概览边界|历史Web169/当前Web1ed160b组合72d83c5e，正常用户新local未发会话、root与Home独立草稿|新会话写入/刷新→Home写普通草稿→侧栏项目无query概览→Home|各既定scope按PRD和URL一致恢复|历史FAIL：overview曾显示B而非root，原图保留。当前Web1ed160b/组合72d83c5e native正常IAM→项目root两行→新localB另稿→Home另稿→侧栏root/刷新正确恢复；有限PASS，不冒durable CRUD/原3310。/tmp/r252-project-draft-scope-real-user-journey.json 与 /tmp/r252-project-overview-draft-fixed-real.jpg|P1/交互、竞态、状态机|
|TC-R252-DRAFT-04 显式会话刷新及重开|Web1ed160b/组合72d83c5e，正常用户创建项目和本地未发送B|新建会话→确认初始空→填B草稿→刷新→Home/root→访问原B URL|显式B只恢复B草稿，不复制root或Home；不更换query|有限PASS；/tmp/r252-project-explicit-conversation-draft-real.jpg。未发送，不证明durable会话列表|P1/系统、主链路、状态机|
|TC-R252-DRAFT-05 浏览器历史与Home隔离|同候选，已分别写root/B/Home草稿|B URL→浏览器后退root→前进B→Kokoro Home|URL与输入scope一致；root/B/Home逐字独立，不观察额外query|有限PASS；真实AX步骤及receipt、/tmp/r252-home-independent-draft-fixed-real.jpg；不推定已触发BFCache或跨tab|P1/交互、状态机|

当前草稿子链receipt SHA19ae7142，独立实图审6e5ab748，17336已正常收尾。未发模型/未测试费用/持久CRUD；完整T-C05/T-U04与70组11/6/14/38/1保持。Agent307db318仅设计，不新增收费测试PASS。

总收据 `/tmp/r252-auth-return-real-user-journey.json`；真实IAM/BFF/Platform/Storage，不是mock或unit。独立证据复审 `/tmp/r252-auth-user-proof-qa-review.md`（8822ef60）已核五截图与有限结论，完整T-C05/T-U04及其它页面仍保持原状态。21499已正常收尾，原3310不动。源码与辅助测试只作为回归安全网，不为完整用户验收替代品。

## R252 本轮真实页面验收与资源收尾（2026-10-05）

- **Skills有限主链通过**：独立五owner固定组合Root9e36000/Web475f24fe/BFFf3c64d90/Platform494b118/IAMc9a9872/Storage14f2bc9；实际Chrome无痕正规IAM登录→普通474B二字段V2 ZIP选包→上传并发布→已发布列表→安装/停用→硬刷新仍停用→启用→移除→刷新确认安装为空、发布源仍存在。服务端sourceRef/revision由正常产品流程生成，未向包塞后台ID；证据 `/tmp/r252-skills-real-user-journey.json` 与 `/tmp/r252-skills-native-published.jpg`。没有逐段网络状态码捕获，恶意包、越权、ACK未知、详情/撤回、Agent真正加载执行仍未验，**不关闭整组T-K02，不冒原3310通过**。
- **Library有限主链通过**：同正常用户在资料库选择本次57B普通文本→上传显示扫描通过与权威文件行→硬刷新文件仍在→点击下载、原生保存完成，下载SHA与原文件相同（d1cd348a…）。证据 `/tmp/r252-library-real-user-journey.json` 与 `/tmp/r252-library-refresh-download.jpg`。本轮未精确测量自然300秒边界、感染/超限/取消、项目/他人文件或Agent作品，T-F01原异常及整组仍待复测。
- **登录回原项目修复进行中**：Root实际8failed/12passed行为RED已取得；唯一Web writer获既定9源/8test窄授权，复用state/固定callback/PKCE/nonce/一次消费与verified-subject草稿隔离，不建新认证框架。代码尚未冻结/审查/集成，真实原深链FAIL保持，T-C05/T-U04未验收。只读QA与安全预审并行，Root不抢写。
- **资源已收尾，不留闲置后台**：正常Ctrl-C23266实际exit0，launcher报告owned resources removed；Root复查3311无监听、私有凭据已移除、原3310的45606/46036仍alive。本轮无痕测试窗口已执行关闭，未动原用户预览/模型/积分/共享资源。收据 `/tmp/r252-capability-release-preparation.json`。首次缺IAM生成物/第二次错误Python工具链的失败保留，未以重试成功抹掉历史。

有限用户证据已独立只读复审 `/tmp/r252-user-proof-qa-review.md`（715480d4）：Skills发布归T-K02、安装管理归T-K03，远端包digest/filehash尚未独立读回。

完整Wave0–7与唯一70组 **11通过/6失败/14待复测/38未验/1支付后置** 保持；有限用户子例不是整页验收。原goal保持blocked、不新建重复目标。下一动作：原Web负责人冻结最窄登录返回修复→独审/Root复验→固定候选真实重新登录回原项目/会话；其他页面按原卡并行推进，不深入运维。

## R252 真实登录回跳失败与技能消费者交付（2026-10-05）

- **真实用户路径 FAIL，根因已定位到登录返回目标丢失**：原3310项目深链经正常IAM SSO，Document链为项目307→/login302→/iam/oauth2/authorize302→/api/auth/callback/kokoro-iam303→/app200；最终普通会话、无Project区域。受管CDP同cursor完整分页，hasMore=false/truncated=false；未改clock/cookie/token，未伪造登录。安全receipt `/tmp/r252-original-deeplink-login-return-red.json`、截图 `/tmp/r252-original-deeplink-login-return-red.jpg`。有效session对照：项目硬刷新200且项目/两行草稿均保留，已精确清掉本次QA草稿；对照receipt `/tmp/r252-original-project-refresh-control.json`。这替代R251“尚无跳转链证明”的当前结论，但不宣称所有间歇根因已穷尽。T-C05/T-U04仍未验收。
- Web唯一ZIP V2 consumer已精确本地main **475f24fe74edf68b45754e13c657361fb2857e70**：20冻结现文件+三D0仅批准prefix，共23path；原四mixed保持。Root先实际RED2failed/10passed，再冻结重跑97182实际1869passed/107files及生成/lint/types/build全部exit0；独审7a7605b无新增确定P0/P1/P2。BFF正式f3c64d90/public8/SHA278fc0a6固定，Team15输出逐字不变、生产仅现schema V1→V2，不加旧值域兼容。收据 `/tmp/r252-web-v2-commit-receipt.json`、Root门 `/tmp/r252-root-web-v2-gates.log`。**这是源码交付，不是Publish/Install/整页通过**，T-K02仍OPEN，原3310未更新。
- 下一动作并行且同仓单writer：原Web owner接最小标准同源返回目标修复（现state/PKCE/nonce/一次消费、安全身份fence保持，不增中转cookie/认证框架）；Root接固定五owner真实普通登录→原生ZIP→上传扫描→Validate→Publish→Install/启停/移除→刷新。组合只读a8a8c2bc已核依赖/工具链/原PID保护，必须独立cookie jar，不能仅换端口伪称隔离。

完整Wave0–7和70组 **11通过/6失败/14待复测/38未验/1支付后置** 保持，goal仍原blocked；未push、未暂存Root gitlinks/uv/任务外mixed，不把工程测试数量冒最终用户验收。本条记录时自有Web门97182已完成，release构造21804在途，尚未启动新服务或做模型/积分操作；原3310句柄保留。

## R251 验收状态续录（2026-10-05）

BFF消费者正式source交付f3c64d90不计产品用例通过：public8.0/zip-v2完整工程检查只辅助，资源skip2不是实测。T-K02待Web正式消费后真实用户二字段ZIP→扫描→Validate→发布→安装/启停/移除→刷新；当前原3310Skills/Library读取FAIL及项目刷新FAIL保持。登录目标能力缺口只读已证，实际跳转根因未证，不清零。70组11通过/6失败/14待复测/38未验/1支付后置不变。

## R251 真实用户路径复测与修复边界（2026-10-05）

|既有用例/子例|预置条件|用户步骤|预期结果|实际状态与证据|优先级/类型|
|---|---|---|---|---|---|
|正规登录→工作区|原3310现有本地IAM账号/普通表单，受管Chrome已恢复|正常输入既有凭据→点击登录→Home|callback正常，Home及输入可见，无整页重试中转|PASS有限子链；/tmp/r251-original-login-workspace.jpg。未验退出/撤权/自然期限，不关闭整体登录组|P0/主链路|
|既有会话打开/刷新|本人已有R243两轮聊天，未发送新消息|侧栏展开→点该会话→硬刷新→等待正文|同会话两轮正文和输入恢复，加载退出|PASS此例；未关闭原另会话间歇跳转FAIL，未验真实推理/扣款|P0/状态机|
|T-C05 项目合法空态|已有本人项目d93d8972，清单合法空|点项目→等侧栏/中心清单|明确无会话，无永恒loading|PASS此子例；/tmp/r251-original-project-empty.jpg。创建/删除/移动与其它项目能力仍待验|P1/边界、状态机|
|T-F01 当前个人文件读取|原3310正常登录后，同侧栏|点资料库→等读取结束|本人文件或合法空态|FAIL：个人文件加载失败；/tmp/r251-original-library-read-failed.jpg。未上传、未猜具体HTTP原因；自然300s新修复待正式组合复验|P0/主链路、异常|
|T-K02 当前技能读取|同正常登录|点技能→等读取结束|本人发布清单/合法空态|FAIL：技能池加载失败；/tmp/r251-original-skills-read-failed.jpg；正式owner/consumer新组合未上线预览|P1/主链路、异常|
|T-C05/T-U04 项目硬刷新不被普通会话覆盖|原3310先打开普通conv586，再侧栏进项目d93d8972，原草稿空|输入两行QA草稿但不发→项目hard reload→看URL/正文→侧栏返回|保项目URL/视图/草稿，不跳remembered普通聊天|FAIL：项目region未恢复，跳conv586及其原正文；返回项目原草稿仍保留。本次QA草稿已恢复空值；/tmp/r251-original-project-reload-redirect-red.jpg。导航/restore只读定位中|P1/真实系统、竞态、状态机|
|T-C05 创建请求总期限/恢复|当前正式Web小切片，真实owner页面待装配|创建P→headers/body停滞10s→解除pending→显式原key重试；切主体/route/卸载分别检查|单总预算，unknown不重复新建，晚结果不抢新意图/草稿，资源释放|Root16299有效8fail35pass→第一冻19407422辅助；独审锁bodyP2已Root408343fail48pass，原2path补。最终Root32292同422辅助/lint/types/build0、独审2f1ea9e6 P2闭；正式Web仅4path交付b3f588e4，真实页面未验，不冒PASS|P1/竞态、异常、状态机|
|T-K02 consumer唯一V2|Platform494生产者已交付；BFF5042830隔离D0|正常HTTP Validate消费合法V2；旧V1及坏digest拒绝|V2合法ACK→200，旧格式→502，原tenant/idempotency/attempt保护|Root原HTTP8pass6fail证实consumer不匹配；现唯一writer改现route/public8正常生成与固定proof，非浏览器publish/install通过|P1/契约安全网，非产品验收|

原70组11通过/6失败/14待复测/38未验/1支付后置保持。真实复测收据/tmp/r251-original-browser-journey-receipt.json无凭据；原预览未更新、无模型/积分/上传/删除，本轮实际浏览器恢复与历史阻挡分开记录。

## R250 已有用例的局部交付与产品待验（2026-10-05）

|既有用例|预置/用户路径及验收|本轮实际证据与状态|优先级/类型|
|---|---|---|---|
|T-C03 删除|本人列表有未打开B、当前A有草稿；B行确认删除应单DELETE/严格ACK后消失，A不切换|Root84485辅助行为RED实际0DELETE；Web0786df4窄修交付/Root56032局部GREEN。替身安全网，真实页面仍未验|P1/功能、状态机|
|T-C05/T-U04 创建与切换|本人A发起创建P，在ACK前切Q输入新草稿；合法ACK后列表权威GET更新但仍Q，不抢导航|Root84485辅助RED实际Q抢为P；Web0786df4修并保A→Q→A/actor/dispose/unknown原key/catch/finally。Root164/230辅助、独审无新阻塞，真实产品仍OPEN；创建总timeout/项目DELETE仍缺|P1/竞态、状态机|
|T-K02 发布与安装|预先选二字段V2 ZIP→Draft→真实上传/扫描→Validate→Publish→显式安装/启停/移除/刷新|Platform494b118五runtime/V7 proof局部交付，初机器1P1/2P2已修/七真实工程反例最终拒；Root全纯门1266+278skip和另真实PG30不代产品。BFF/Web未切，原页面412仍OPEN|P1/主链路、异常、安全|
|T-F01 自然续期|正常IAM登录停留Library>300s，选File不丢、同session generation推进、单次上传/刷新|Chrome扩展UI阻挡未解除，后继GREEN未执行；原真实401/上下文丢失FAIL保持|P0/主链路、状态机|

原70组11通过/6失败/14待复测/38未验/1支付后置不变。67772/84485/50401/93133/56032均终态；未启动3311组合，原3310保持，真实PG原库清单保持，无用户文件/会话或共享Redis清理。局部源码已提交≠当前浏览器交互通过。

## R249 修复交付后的验收状态（2026-10-05）

既有T-F01自然到期FAIL保持。新候选8985e928/Web710b3f2真实五owner启动；正常/login已显示IAM表单，但Chrome扩展UI阻挡后续全部控制，未输入账号或点击提交；自然300s/同session generation+1/Library原File保留及上传刷新均 **BLOCKED / 未执行**，不是PASS或新产品FAIL。已请求用户关闭弹窗。资源47785exit0/3311无监听/凭据移除/Redis13=0/原PID保持；自有Chrome1715212225关闭调用同被阻挡，未记关闭通过。

Web代码独审与Root135辅助、15 fixture、lint/typecheck/build通过不代产品验收；全check实际1fixture失败后取消130，该fixture后继正确wire复验15通过但完整全门仍未完成。Platformf290256仅三D0/格式通过，源码V2及正式BFF/Web consumer、T-K02发布/安装CRUD尚未验。70整组统计保持。

## R249 T-F01认证边界实际复现（2026-10-05）

|既有用例/子例|预置条件|步骤|预期|实际/证据|优先级/类型|
|---|---|---|---|---|---|
|T-F01 有效凭证正控|33b9dfb2/Web b8c3360b五owner、独立Chrome正常IAM登录|上传54B→扫描→列表→硬刷新→读取session body→上传53B|同主体可连续提交，持久列表存在|PASS此短子链；两upload200，刷新authenticated:true。/tmp/r249-library-auth-pre-expiry.jpg；不关闭Library整组|P0/主链路|
|T-F01 自然access到期|同正常登录、IAM现300s、总体会话仍active/gen0；未改时钟或身份记录|正常等待原access到期→选择新File→上传→观察下一probe导航|正常续期保持页面/意图；真实过期/撤权明确恢复，不盲重发|FAIL：12:47:32 POST401正文unauthenticated、通用错误/提交disabled，owner无该业务请求；随后自动SSO回/app丢Library。/tmp/r249-library-natural-expiry-red.json及.jpg；旧R248未知401不冒已定|P0/异常、状态机|
|TC-QA-R247-002本轮资源|仅Root35175/自有3311/独立QA页|原句柄Ctrl-C→观察退出→核监听/私有凭据/DB13/原PID|只回收自有资源，保原用户环境|PASS本轮exit0、监听无、凭据已移除、DB13=0、QA页已关闭、原45606/46036存活|P1/生命周期|

实现/组件门不算系统验收。消费者修复冻结后必须Root同自然300s停留Library/原选File→有真实generation推进→提交/刷新，及后台返回、失败/撤权/账号切换负控；当前均未验。70整组统计不变。

## R248-CSP 实际修复复验（2026-10-05，既有T-K02发布子链）

预置：候选33b9dfb2/Web b8c3360b/Root1d51949a，真实五owner与独立Chrome。动作：正规登录→技能→选择预制原ZIP→填写名称→上传并发布。结果：**上传子链PASS**（OPTIONS204、PUT200、Complete200、CLEAN、hash一致）；**发布仍FAIL**（Validate412/skill_precondition_failed/request_id8c93624a-1f5d-4fd9-a2b2-37d047a0f321，无Publish成功）。优先级P1，功能/异常/状态机。未用后台生成含新ID的包规避普通用户路径。精确开发origin修复没有扩大生产策略；真实412不冒内部具体package错误码。证据/tmp/r248-upload-fixed-browser-receipt.json、/tmp/r248-skills-upload-fixed-validate-red.jpg。70整组统计不变。

## R248 最新真实用户复测（2026-10-05，覆盖下方历史状态）

共用前置：独立Chrome（与原IAB不同身份）+真实IAM/BFF/Platform/Storage/Web，候选 `4c974d53abfe42335eb9eb445097e53a83c2e60d`。不含Agent/System/Scheduler/Billing，不冒这些能力已验。

|既有用例/子例|实际用户动作与预期|当前结果|优先级/类型|
|---|---|---|---|
|TC-AUTH-R247-001|正常/login→邮箱密码提交→callback→app|PASS此组合登录子路径，原用户环境不据此全绿|P0/主链路|
|TC-SKILL-R247-003|侧栏Skills→本人安装；合法结果须无503|PASS合法空列表读取子例；未安装/启停/移除，不关闭整组|P1/功能|
|T-K02 发布|选择普通ZIP→填写名称→发布→同次重试；应真实上传扫描校验发布|FAIL：Begin201后实际CSP阻止PUT，截图/tmp/r248-skills-publish-red.jpg；未到Validate，随机manifest身份为独立源码P1|P1/主链路/异常|
|TC-FILE-R247-002/003|个人文件58B上传→scan→列表→硬刷新→卡片下载；与原文件字节相等|PASS本次正常文件交付子链：实际Downloads落盘58B、SHA b8653670d43bd37c986c61ecd8c572510182c906aa97d1b6cea509382156487a与源一致。Cua事件超时单列观察缺口，不认下载未交付|P1/主链路|
|T-F01 刷新后二次上传|刷新后再次选择新文件名→提交；应保持合法认证或可明确恢复|FAIL：POST library/files实际401、通用错误/终态禁提交；GET session200不证明authenticated，401来源未取稳定码，不猜过期/本地或upstream归因|P0/恢复/状态机|
|TC-QA-R247-002|停止49143→核监听/凭据/ownedRedis及原进程|PASS本次回收子例：exit0、3311无监听、凭据移除、DB13=0；原两进程存活、QA Chrome已关闭|P1/生命周期|

实际证据 `/tmp/r248-browser-real-receipt.json`。仅子例状态变化，70业务组统计不变；CSP源码修复尚待Root当前commit+真实浏览器复验，不以guard成功关闭发布。

## R247 真实页面复验终态（2026-10-05）

|用例|真实步骤与验收|实际终态/未验边界|
|---|---|---|
|TC-SKILL-R247-002|同3311错误页HTTP200→同两client修复→已发布合法空态→硬刷新|PASS读取子例，截图/tmp/r247-skills-real-fixed.jpg；安装/发布不借此通过，原3310未装配全owner|
|TC-SKILL-R247-003|同3311点击本人安装→等待终态|FAIL实际503；已定位surface+candidate关闭，source窄修待新组合重跑，不fake空列表|
|TC-FILE-R247-002|选58B非敏感QA文件→提交→scan通过→列表→硬刷新|PASS上传/扫描/列表/刷新子例，截图/tmp/r247-library-upload-refreshed.jpg|
|TC-FILE-R247-003|下载按钮→content200→等待落盘|待复测：15秒download事件超时，字节未核；HTTP200不冒下载完成|
|TC-QA-R247-001|同域两个port测试后回原3310|返回需登录，已正常登录恢复原conv586/两回复；不同port不隔离cookie，下一需独立hostname/profile，自动/app观察因果仍OPEN|
|TC-QA-R247-002|停止自有94387→核监听/credentials/Redis|exit0且3311无监听，随后发现旧scanner漏4ProductSession keys；真实RED0/4，仅确认本origin4keys精确回收后0。源修复下一完整生命周期/他origin保护待验|

用户业务70组统计不变。数据库角色/部署调整不在本轮门禁；不新增服务重复启动、不清共享数据。最新状态与原历史FAIL同时保留。

## R247 真实组合QA续测记录（2026-10-05）

|用例ID/标题|预置条件|步骤|预期|实际状态|优先级/类型|
|---|---|---|---|---|---|
|TC-AUTH-R247-001 正规登录|自有3311真实IAM+BFF+Web、现QA账号|/login→邮箱密码→登录→callback→/app|正规会话建立、进入工作区|PASS子路径；不等于原3310登录全组通过|P0/主链路|
|TC-SKILL-R247-002 正常读取响应|同3311已登录、真Platform|侧栏技能→重试→观察网络与settled状态|HTTP200显示本人列表/合法空态，不误报错误|FAIL：200但复合no-store被exact比较拒绝；唯一Webwriter修复中|P0/主链路、异常|
|TC-FILE-R247-002 上传扫描刷新|同3311真Storage/S3/ClamAV，58B非敏感QA文本|资料库→选择文件→上传→等待扫描及列表→硬刷新|扫描通过、文件身份尺寸一致、重载不丢失|PASS子路径，截图/tmp/r247-library-upload-refreshed.jpg；其他边界/越权待验|P0/主链路、状态机|
|TC-FILE-R247-003 真实下载|上一例已scan clean文件|点击下载→等待浏览器下载→核落盘字节摘要|下载完成且字节与源相同|待复测：contentHTTP200、UI idle，但download事件15秒超时；落盘未核，不能PASS|P1/主链路、异常|
|TC-FILE-R247-004 文件作品切换|同3311已登录|个人文件→Agent作品|标签/URL同步、未生成时合法空态|PASS标签/空态子例；真实作品生成预览下载未验|P1/状态机|

上述均新自有QA组合，不假称原3310用户环境已修；原失败保留。70组统计不变。后台辅助45/32不计算用户完成率。

## R247 页面级QA复测记录（2026-10-05）

|用例ID/标题|预置条件|自然测试步骤|预期|实际/下一步|优先级/类型|
|---|---|---|---|---|---|
|TC-UI-R247-001 项目侧栏settled-empty|真实3310本人登录、d93d8972项目没有会话|侧栏点击项目→等待项目清单200/加载结束→观察侧栏与中心|有明确空态，不空白、不借其他项目数据|原FAIL已修；现tab7实际PASS子例/截图/tmp/r247-project-empty-verified.jpg。Web5c73af71；不关闭项目CRUD整组|P1/主链路、状态机|
|TC-SKILL-R247-001 本人技能读取|同真实本人session|从侧栏进入技能→等待加载结束|当前本人列表或合法空态；认证失败有正规恢复，不能无限重试|FAIL：GET self/skills实际401；body/code未得，原因待分层。无假空列表|P0/异常、权限|
|TC-FILE-R247-001 个人文件读取|同真实本人session|侧栏资料库→个人文件→等待终态|当前本人文件列表；合法空态与依赖失败区分|FAIL：GET library?kind=file实际503；缺Storage组合已核，但此次typed code未得。上传/clean/下载/删除/刷新未验|P0/主链路、异常|
|TC-MCP-R247-001 目录不冒连接|本人已登录|外挂目录→管理连接器→真实授权→owner读回→撤销|catalog与本人已连接分离，无装饰卡片假成功|截图/源码证明目录静态；本人授权/connection读回/撤销未验，Platform组合缺口|P1/主链路、权限、生命周期|
|TC-TASK-R247-001 排程完整旅程|本人已登录、独立ScheduledTask与Scheduler可用|创建→刷新读回→暂停/恢复→到期→执行结果→删除规则验证|outbox注册/持久状态与UI一致；创建ACK不冒运行|本次欢迎页不判FAIL/PASS；真实CRUD/调度未验，当前无受管Scheduler|P1/主链路、状态机|

辅助系统反例修复完整77集成功只作上述UI窄片安全网；Agent589工程辅助不计用户旅程。边界/异常/他人权限/取消/多窗口/恢复按既有70组继续，状态11/6/14/38/1不变。用户页/资源状态与正式main交付区分，当前不称全面闭环。

## R246 系统测试执行记录（2026-10-05）

TC-CHAT-R245-002及原74/新增直接刷新case所在完整76集合：Root15037实际76通过/0失败/0跳过，101.277秒，manifest /var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-r246-web-system-full-05nftq07/manifest.json，日志91092585、源码/Redis保持、own group已退出。这只是受控IAM/BFF的真实Next/Chromium诊断回归；TC-CHAT-R245-001实际3310间歇跳会话仍OPEN，当前浏览器控制超时导致本轮未复验，不记业务PASS或新FAIL。Agent实施中未冻结，TC-AGENT-R245-001暂保既有有效RED而不预报GREEN。70组状态11/6/14/38/1不变。

## R245 最终实际运行记录

|用例|预置/操作|预期|实际/边界|优先级/类型|
|---|---|---|---|---|
|TC-CHAT-R245-002 两tab remembered A 与URL B冲突|合法同subject两page；A在途snapshot请求暂停，B正文/URL稳定，A request continue；只读shared A且含A/B、B仍正文URLB后hard reload|B URL/正文保持，不出现A|Root36180 PASS该受控排程；1/75过滤，源码Redis保持。不是已取得200的response hold，不关闭TC-CHAT-R245-001真实间歇FAIL|P1/系统、状态机、多窗口|
|TC-AGENT-R245-001 最终真实wire必须先于调用prepare|原production Factory/native SDK、真PG、合法local owner peer，缺Billing；透明观察现唯一HTTPX hook与真实PGprepare顺序|原ND/零provider/unknown完整事实保持，hook→prepare→committed|Root52891有效FAIL：原安全事实通过，sequence缺hook；1fail/1.77秒，源/全DB保持/自库已回收。仅开发控制链反例，不是用户推理/费用PASS|P0/系统、生命周期、SQL一致性|

Agent已审3D0仅本地main29a7a18；producer实现/所有解析界/claim取消/PG replay/closure和完整用户链仍待。Web两个新case共76候选尚未全回归/Git交付；原70组11/6/14/38/1不变。

## R245 刷新用例复测边界

TC-CHAT-R245-001：第二次真实3310同B hard reload恢复原B及R145正文，未改服务/代码，不覆盖首次跳A FAIL。受控新增单文档系统case1pass，但其persisted active在reload前已是B，未形成所需A/B冲突前置；不能据它关闭用户组或准修导航。原源码审查565dfa8d的P1为判据不足，具体用户因果仍待真实乱序反例。下一两tab case需合法200、自然写回A、shared entries含A/B且reload前B URL/body未变，不注入storage/延长10秒。

Agent3D0独审0与原合同17pass仅设计安全网，不算native、PG或费用用户PASS。完整矩阵70组保持11/6/14/38/1。

## R245 新发现的真实刷新反例（不升级整组PASS）

|用例ID/标题|预置条件|测试步骤|预期结果|实际结果|优先级/类型|
|---|---|---|---|---|---|
|TC-CHAT-R245-001 直达会话刷新不能被 remembered 会话覆盖|真实3310本人已登录；B=conv_ffd7…有R145回复，另有本地remembered A=conv586…|直达B→等B正文与输入可用→硬刷新→等待原B正文15秒→核URL/正文|URL持续B，正文仅B；加载有界退出，不借另一会话掩盖失败|FAIL：原正文未出现，URL改A且显示A的R243两回复；两详情GET200；实际截图已观察|P1/系统、状态机、异步竞态|

导航/helpers正式与runtime hash相同，故不以‘只是旧预览’排除此反例；具体根因待隔离真实Next/Chromium反例与独审。禁止将工程2495计作用户完成率。旧tab5关闭控制超时仍存在，新6保留，没有删除用户数据或新模型请求。

## R244 工程交付复验与用户链状态隔离

|验收对象|预置与步骤|实际结果|状态边界|
|---|---|---|---|
|Web精确交付保护|父5e096364、冻结43path+CURRENT；逐Git对象核44集合→核原四mixed bytes/modes/index→主树完整check→再核保护|c8b863264对象一致；Root91331完整门0（263/50/2495/build），源/Redis保持、owned55385无残留|工程交付PASS，不关闭用户功能组|
|正式用户Project改名链|正规IAM→持久BFF本人Project→更多改名→canonical GET/列表→刷新同对象/会话/草稿|本轮未执行；原R243controlled-owner子链证据保留，当前3310未换源码|待验，不按后台测试数算用户PASS|
|Agent真正final request冻结|真实native SDK→合法child final hook→prepare同wire摘要→缺许可零transport|独审发现same-task与scope self-wait两提案错误；最终17d443dd经9a0fd123文字复核纠正，本轮未运行native反例|两P1设计已静态复审纠正；资源profile/三D0/native动态未准，无provider/资金变化|

原加载/Settings昵称丢失、完整CRUD/权限/多语言/焦点交错与正式费用链未关闭。完整70组仍11通过/6失败/14待复测/38未验/1支付后置。

## R243 最终完整回归与用户验收边界

Root89903最终localized冻结原完整check终态0：contract263、architecture50、lint/types、默认2488（现74系统在集内）、build均实际通过，source/Redis保持，日志SHA回读吻合。manifest `/var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-r243-web-rename-engineering-localized-185ixsi4/manifest.json`，loga574725e035dfbb1fe3e3444758a4b9a80bc369e727a8ca57721fedf3d13e7a1。43path冻结 `/tmp/r243-web-final-integrated-freeze.json`，源码独审232093fc确定P0/P1/P2=0。原两轮contract/缺译FAIL历史保留，未弱化测试或95%门。

这是工程安全网/受控owner系统行为，不算2488用户旅程或当前3310发布。真实3310双行草稿刷新全文保留且测试草稿已清空；现场昵称关闭重开丢失仍FAIL。原加载根因、完整项目/Settings、正式费用/外部模型、跨scope focus交错/真实多语言UI仍待验；70组11/6/14/38/1不变。

## R243 多行草稿真实操作与完整回归续验

实际3310 conv_586d8b9f：原输入空→“R243 草稿保留第一行”→真实Shift+Enter→“第二行不发送”，只读DOM value确认精确\n/2行；未提交，原两轮消息不增。intentional硬刷新经历短暂booting后同会话正文/可用输入恢复，value逐字相同/2行。已显示实际截图并将QA草稿清为空，未发送新模型请求、改权限/积分/账号；此为输入/刷新子证据，不关闭T-U04原用户旧页或全输入模块。

Root28998完整repin版门仍FAIL：contract263/0、architecture50/0、lint/typecheck0，test2487/1（ko1506/1598覆盖94.24%低于现95%），build未跑。原新rename中文13条仅en译的遗漏交给原唯一writer补七现locale词典，不降低阈值/删测试。manifest `/var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-r243-web-rename-engineering-repin-khsutjy4/manifest.json`，log204d51845a7a0c1bcb0d4e689cf37044021c9fadec910117e6197ae165765ebe，source/Redis保持。2487辅助通过不算2487用户旅程或整体完成；70组11/6/14/38/1保持。

## R243 当前 token 版子旅程与完整门实际失败

- 当前三file token freeze：Root41237真实Next/Chromium/Redis原旅程1通过/73名称过滤；取消零PATCH、键盘归焦重开、唯一改名PATCH、ACK后canonical B/list、成功归焦、刷新全部原条件成立。manifest `/var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-r243-web-focus-scope-final-a_xh2c44/manifest.json`，logde2f3a3e7a81e6e35d6abc65aa951c8a30a58a1baedcca8f844696c64a0d2ab0，source/Redis保持。受控owner不冒3310真实持久链；跨scope交错仍待验。
- 四fixture正规header修正后Root12045三现相邻文件95/0；manifest `/var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-r243-web-adjacent-final-6_njw7se/manifest.json`，log5f063a7cea894d2a6b92c883cdb6c432b08245805818f8c5d5cc5514ace2b599，source/Redis保持，原93/2历史不删。该辅助安全网不是95用户路径PASS。
- Root3894完整工程实际contract首门1fail/262pass：R76 exact artifact仍断言旧7.1/784f，实际formal886a25a1 artifact是7.2/bf64且two generator check正确。manifest `/var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-r243-web-rename-engineering-final-c5gkxs55/manifest.json`，log6a8913c6416cae66576aba114dcec15d8cb58d251d20803834797d04c67a9129。后续architecture/lint/types/test/build未跑，零新增产品组PASS；只准现该文件两字面repin，业务assert/90cases保持后Root全门重验。
- 70组11通过/6失败/14待复测/38未验/1支付后置不变；既有Settings资料真实失败、正式费用/外部模型与原加载根因OPEN。

## R243 原keyboard反例修复后终态

Root30636真实Next/Chromium/Redis同原bounded旅程PASS：取消Dialog后归焦、Enter重开、改名ACK后canonicalB/list、成功后归焦及reload，单write/route/draft/thread保持。manifest `/var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-r243-web-focus-after-9q4n1n9m/manifest.json`，logc4e6effeaf02cb452bcbb7b68426ca442495142d7fb2676f98df4d4696e5af6e。controlled owner只证明该交互子链，sameURL跨主体/routeEpoch风险仍OPEN，三file围栏未静态/动态放行；此前10秒false实际RED保留。UI四fixture已改但原相邻95case尚未重跑，后继先冻结再复验；70组不变。

## R243 keyboard生命周期新反例（独立于已通过的改名主链）

预置为冻结新Project改名UI、真实Next/Chromium/Redis及受控owner；步骤：更多→改名Dialog→取消→Dialog卸载→既有10秒内观察原更多trigger焦点，随后预期键盘重开并改名成功后仍归焦。首次立即断言false不作为稳定RED；改为同预算expect.poll后Root62162仍满10秒false，实际FAIL，源/Redis保持。现menu来源ref恢复已派，原modal/pending/ACK/GET/deadline不放宽。manifest `/var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-r243-web-keyboard-settled-hmaxi8p9/manifest.json`。此用户键盘反例不把73名称过滤算通过，也不取消前述主链局部PASS；完整项目组仍未PASS。

## R243 本人会话改名刷新子例（仍不关闭T-C03整组）

预置：真实3310已登录，新测试conv_586d8b9f-00ea-415e-a437-da3b09a22849有两回复；步骤：展开侧栏→该行重命名→输入“R243 用户交互验收”→Enter→硬刷新→重新展开。期望：同ID、新标题和原两回复保持、输入可用。实际PASS；没有删除对象或调用新模型。此前因侧栏在操作间关闭的no-match只属未操作，不算rename产品失败；恢复实际入口后该完整子路径执行成立。

候选Project改名原系统journeyRoot86903亦通过（controlled owner，不是上述直接会话，也非当前3310）；当前仍有待复验UI fixture与待实证keyboard风险，不能按它关闭完整项目CRUD。Billing源码ccd4cb0f新前置精确交付，正式费用整链没有用户PASS。

## R243 新增真实Settings失败及改名网络失败（不改变70组）

|用例引用|预置与步骤|验收标准|本次实际|优先级/类型|
|---|---|---|---|---|
|TC-SETTINGS-R191-007–010相关个性化子例|已登录真实3310、原昵称空；账户→个性化→输入QA昵称→职业失焦→关闭→重开|合法编辑有明确保存语义/结果，重开从权威源保留；失败可见而非静默丢失|FAIL：昵称重开为空，无保存/结果反馈；只是局部输入可见。R257实际同源PATCH404、无GET/吞失败已定位：BFF正式preferences operation缺失（catch-all可达），四字段GET/显式PUT CAS设计已审，源码进行中；Root46862真实HTTP/PG普通/me200后GET404，1FAIL/0skip，不替代正常浏览器验收，尚未修复|P1/用户系统、状态机|
|T-C05/T-U03项目改名子例|冻结候选、真实Next/Chromium/Redis及受控ownerpeer；合法menu→Dialog→单PATCH→200|owner no-store与browser-private规范各自正确验证，200后canonical读回，不误判unknown|Root57315 FAIL于实际private,no-store,max-age=0；共用parser拒合法ACK，source窄修已派。当前用户3310尚未启该候选|P1/用户系统、异常、协议边界|

Billing Root70536两文件285通过与独审0只作开发前置证据；正式Credit赠送/预占/逐attempt调用/核实消耗结算释放/流水以及当前用户页仍未PASS。没有关闭任何完整业务组。

### R243下一段执行队列（引用现用例，非新增测试中心）

独立QA/UI清单 `/tmp/r243-next-ui-acceptance-checklist.md` 已交（12自然操作，完整预置/步骤/成功与异常权限oracle）。依次沿 T-C05/T-C02 项目创建概览→TC-R192-C01–03 Move→T-C05/T-U03改名→T-C03会话CRUD→T-C05指令/资源关联→TC-SETTINGS-R191-007–010 Settings→T-B03–07正式Credits；每项只按实际执行回填，不将清单、源码或后台门算通过。涉及项目物理删除的最终确认与新权限扩张遵守当前操作确认，不因QA角色绕过。当前两轮UI与项目菜单/积分错误只覆盖已描述子路径。

## R243 实际用户子路径证据补录（2026-10-05；不改变70组状态）

- T-C06/T-U02子路径：真实3310同新conv586两次自然发送，新assistant标记均到达；终态硬刷新两回复保留、同conversation URL、输入可用。只UI基础子路径；当前launcher本机qwen3:8b/零Billing装配，不称指定外部模型/正式费用闭环，活动续流/取消/权限/作品仍未验。
- T-C05/T-U03子路径：进入既有项目后loading退出/空会话；header更多菜单实际只有账户/升级，缺项目CRUD操作，仍失败。Web候选源码在实现中，不等于实际页面已修。
- T-B03/T-B04相关用户页：账户积分入口打开用量与计费，余额与积分历史各从loading退出为加载失败/重新加载；没有假零余额、免费或赠送声明。当前无Billing组合是已知装配缺口，具体HTTP错误尚未关联；不把后台持久化门改计用户PASS。
- Root42390 formal Billing3f05e6c5 policy持久化11门终态0/日志hash全核；Root97969新增真实Nest+PG缺policy业务RED1fail/24过滤。两项属于开发前置/回归证据，不替代以上用户交互结果。
- Root只用一实际临时tab5；原tab1本轮未取证，现在inventory只有tab5，Root没有删除用户原tab。无Root导航的dialog关闭/回到聊天仅待复现观察，不以tool超时或猜测判根因。

## R243测试证据补充（2026-10-05；不改变整组状态）

项目改名新真实Next/Chromium journey在正常登录/Project/detail/thread/draft前置后，唯一菜单缺失失败（1fail/73名称过滤）；完整后半ACK/fresh-read/reload尚未执行，不冒当前3310或完整CRUD验收。Billing policy SQL候选Root全11门117真实PG/1361辅助通过并精确11路径交付3f05e6c5，正式主工作树复验在途；仅持久化/Schema保护，不替代T-B04/05/06/07正式计价与收费业务组。原失败保留，唯一70组11/6/14/38/1不变；实际收据详Root progress R243。

# Kokoro 系统级测试与业务验收台账


## R241 项目改名实际子例状态（不改变70整组计数）

共同预置：BFF886a25a1已提交的R241冻结生产切片、真实HTTP/PostgreSQL/Redis，IAM受控准入边界；非用户3310。

新增生命周期冻结b480f9d2的Root78534执行：基础五组仍通过；10新组/17叶向量按父子TAP统计总27项25pass/2fail/0skip。唯一叶L6 receipt失败，所属父组随失败，不冒两个独立缺陷。原4.5秒预算等保护不变，生产窄修后必须重跑，不由旧222通过代替。

|用例ID|标题|预置条件|测试步骤|预期结果|优先级|类型|实际结果|
|---|---|---|---|---|---|---|---|
|TC-BFF-R241-L6|真实SQL中用户取消|共同预置；精准Project锁/receipt PgSleep、exact checked-out client与已UPDATE可观测|发rename→观测真实等待PID→HTTP Abort→核client归还/监听/PID/全facts→同key恢复|无成功响应、exact client毁弃一次且监听卸载，backend及时消失，事务零partial facts且pool可恢复|P0|异常、状态机、系统|78534原receipt叶FAIL保留；aa4da6fc窄修后Root7719同b480测试lock/receipt皆PASS，约317ms且facts/pool/recovery到达；Root82423最终完整真实244/0/0skip记录及886a25a1提交绑定；用户页面未验|

|用例ID|标题|预置条件|测试步骤|预期结果|优先级|类型|实际结果|
|---|---|---|---|---|---|---|---|
|TC-BFF-R241-01|改名、权威读与重启|共同预置；本人active项目|创建→改名→GET/列表/旧slug读→重启→读回|ACK与权威名称一致，仅name/必要updated_at变；ID/归属/其他事实保持|P0|主链路、生命周期|基础组PASS|
|TC-BFF-R241-02|no-op与旧key重放|共同预置；合法terminal receipt|same-name→trim等价重放→异body冲突→A/B→旧A重放|no-op updated_at不变；冲突零写；旧A返回原ACK但不覆盖B|P0|幂等、状态机、异常|基础组PASS|
|TC-BFF-R241-03|名称与raw请求边界|共同预置；合法raw Host正控|合法上界→超界/Unicode/NUL/重复JSON/header/query逐向量→全facts比对|合法65536字节与128key可达；非法稳定闭集400且全owner事实零差|P0|边界、异常|基础组PASS；原缺Host失败保留为fixture前置问题|
|TC-BFF-R241-04|当前权限先于receipt|共同预置；本人/另一主体/另一tenant/active或墓碑项目|成功提交→切身份/资格/IAM拒绝→旧key和新请求|当前准入与资格先重放；401/403/404/429/503闭集且零非法写|P0|安全、权限、状态机|基础组PASS|
|TC-BFF-R241-05|缺配置tenant在IAM前拒绝|共同预置；先有合法receipt，再重启空配置|旧key/新key提交→核error/header/IAM调用数与全facts|503 product_tenant_not_configured；retryable/no-store/request-ID；IAM不增加、零事实变化|P0|异常、安全|基础组PASS；原独审P1关闭|

Root83477五组5pass/0fail/0skip；格式单hunk后Root60631完整owner真实PG/Redis222pass/0fail/0skip及check745pass/2资源skip、format/build/contract/lint/types0，manifest见progress R241；源与资源保持。此段222是前版历史记录；最终Root82423新冻结完整真实244/0/0skip，Root7719改名/生命周期27/0/0skip，已提交886a25a1。新增same-key并发、LWW、资格锁竞争、receipt回滚、实际COMMIT后应用侧ACK丢弃与有界取消的限定子例有记录；并非全部故障向量/真实网络ACK丢失已验，正式Web消费与完整CRUD仍待验。不升级70整组。

## R240 已交付切片（不关闭完整用户组）

Web认证/恢复已由Root精确19路径提交main `5e0963648db0cb0e1a60de42ea025670b32aba85`：正式Git对象与73真实系统/2473完整工程冻结字节一致、最终独审0；原19mixed内容保持，当前4mixed。BFF active资格cdad0ad6/217真实集成保持。用户3310原标签尚未取得DOM验收，70唯一业务组11通过/6失败/14待复测/38未验/1支付后置不变。进程副本含主要当前认证源码，不能仅凭旧启动时间归因；正式组合与dev源闭包需分别验证。实际收据和工具失败见progress R240。

## R239 最新测试执行状态（2026-10-05；不改变整组计数）

70唯一业务组现场重算：**11通过 / 6失败 / 14待复测 / 38未验 / 1支付后置**。六失败为T-Q10、T-C03、T-C09、T-C10、T-A05、T-U04；不是整体开发完成率。

- Web候选system e82340fc：Root63257原完整工程通过，258合同/50架构/lint/types/2473默认测试/build0；默认包含73真实Next/Chromium/Redis系统例。独立全73结果亦通过，IAM/BFF为受控peer，候选未提交/启用用户3310，不关闭当前用户持续加载、CRUD/Settings/模型费用整链。原46637工程1失败及测试oracle窄修保留在progress。
- BFF本地main cdad0ad6：217真实PG/Redis集成、完整工程和schema门通过；active资格前置已交付，不冒项目改名/删除全闭环。
- Settings13栏盘点已完成但只读源码不是测试通过：通知/快捷键持久化、个性化ACK/GET、Integration正式读回、Computer/Deployment生命周期仍缺；Team/Skills/MCP双身份与实际owner旅程待执行。

完整命令、SHA、失败历史与资源终态见同一progress/task/CURRENT，不另建测试计划。


## R236 Git-only缓存拒绝切片（不变70整组状态）

|用例ID/标题|预置条件|测试步骤|预期结果|优先级|类型|实际结果与边界|
|---|---|---|---|---|---|---|
|TC-WEB-R236-CACHE / 非权威缓存拒绝恢复|HEAD680c8db8 archive、真实Next/Chromium/Redis、controlled IAM/BFF；唯一Conversation getItem拒绝，身份存储可用|认证成功→目标读取拒绝实际命中→权威snapshot/正文/可编辑输入→reload同路径→核零POST|原12秒预算内恢复；无SecurityError与假创建；全storage拒绝仍身份fail-closed|P0|系统、异常、状态机、安全|Root52643有效RED1fail/67过滤（认证true、拒绝2、SecurityError、snapshot/body/input0）；read窄修后Root19270原case+原R150负控2pass/66过滤。完整68系统10171终态68pass/0fail/0skip；工程22777全0（2460默认测试）；本地main1e8ce99c两路径已交付/用户3310未验证，T-U04仍失败。两先前fixture setup失败不计产品RED；准确manifest见progress R236。|


## R232 最新系统实测（整组状态不虚增）

- Billing私有费率选择已按main e5d83db0本地提交，六source/test与115真实PG/1361辅助十门0冻结完全同；只是T-B01/后续报价前置，不把T-B03–B07置通过。
- TC-WEB-R231-PROJECT-DELETE-ACK与503：修正合法snapshot fixture后Root真实2pass/78过滤；完整80为79pass/1fail，唯一旧R195等待竞态在窄修，完整门仍失败。真实Next/Chromium/Redis、BFF/IAM受控peer，未关闭T-C03/T-C05或原用户3310加载。
- TC-AGENT-R232-SDK-COMPLETION（P0；异常/状态/系统）：完整raw JSON正常invoke却未mark、SSE raw含final/DONE但只取首chunk后aclose；真实锁定SDK/owned HTTP peer单POST且n1/输出界合法；预期unresolved/sdk_consumption_incomplete、无digest，Root实际两例均complete/None，**2failed/294过滤**。正在实现已审显式完成标记，未调用未存在方法制造RED；无资金或真实provider。
- 用例、冻结SHA、真实manifest/日志摘要与scope详见progress R232；70产品组11通过/6失败/14待复测/38未验/1支付后置保持。

## R231 费率选择与项目会话删除系统切片（70产品组状态保持）

|用例ID/标题|预置条件|测试步骤|预期结果|优先级|类型|实际结果与边界|
|---|---|---|---|---|---|---|
|TC-BILLING-R231-SELECTION / 当前费率选择及损坏恢复|Billing8f091d40+冻结六路径，现完整canonical与owned真实PostgreSQL/Nest/Prisma fixture|发布并选择生效版本→核绑定/profile/tenant/all/range边界与冻结结果→注入2/2 canonical漂移→真实SQL故障与事务回滚→恢复读|选择唯一合法费率；漂移按owner错误拒绝；query首因保持、事务回滚且后续可恢复；无余额/资金写入|P0|系统、边界、异常、隔离、状态|原真实RED1fail/21pass；最终Root十门0、115真实PG/1361辅助，独审0P0/P1/P2，仅私有rate选择候选，不增加正式积分/收费整组PASS|
|TC-WEB-R231-PROJECT-DELETE-ACK / 项目会话删除等待ACK|Webce40cecc+系统测试b4bc4c9c，隔离真实Next/Chromium/Redis、受控IAM/BFF peer|进入项目会话A并核canonical正文→延迟DELETE并核草稿/归属稳定→ACK后重读与刷新|ACK前不假删除；ACK后canonical项目关系移除A、不影响独立会话C、刷新不复活|P0|系统、主链、状态、边界|FAIL于DELETE前正文预置，未执行删除；已定位fixture snapshot误附project_ref，生产合法无query；待测试前置修正后实跑，不能冒删除有效RED|
|TC-WEB-R231-PROJECT-DELETE-503 / 项目会话删除503重试|同上|进入A核正文→DELETE503→核原会话保留→显式重试→ACK后刷新|失败不假成功、不自动无限重试；显式重试正规提交后才移除|P0|系统、异常、恢复|FAIL于DELETE前正文预置；原78例名称过滤未跑，不算通过或业务skip|

本轮回读终态与日志摘要：Billing manifest `/var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-r231-billing-final-qz_5w_d3/manifest.json`；Web manifest `/var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-r231-web-project-delete-xea8ba4s/manifest.json`。源及自有资源集合保持，未升级3310、调用真实provider或改变余额。70组仍11通过/6失败/14待复测/38未验/1支付后置；局部结果不代替整页面/整仓闭环。

## R229 冷会话深链接真实故障恢复（不增加70产品组通过数）

|用例ID/标题|预置条件|测试步骤|预期结果|优先级|类型|实际结果与边界|
|---|---|---|---|---|---|---|
|TC-WEB-R229-COLD-DEEP-LINK / 冷深链接503后手动恢复|Web ce40cecc+冻结系统测试504ca8cf；真实隔离Next/Chromium/Redis、受控IAM/BFF HTTP peer；全新无storage context完成正规fixture准入|首业务document直接访问会话A→snapshot peer真实503→观察error/loading→切peer200点击Retry→刷新；核HTTP序列、URL、正文及POST|503后error可见且loading结束；Retry及reload保留同A且正文恰1，响应[503,200,200]；零session创建POST，资源与源码保持|P0|主链、异常、状态机、系统|Root定点1pass/77过滤；完整78pass/0fail/0skip，116.022秒；独审0P0/P1/P2。原实现此路径已能恢复，不是用户3310持续加载根因或生产修复。|

完整manifest `/var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-r229-web-full-8zwiqgvn/manifest.json`，log SHA `71e155a9f571f0d6819ae4ea159a9e481954b8bb28a15a150c29741d5ddb248e`，source_same/redis_keyset_same均true。原77 case及原断言保留，仅现系统测试91行插入；没有真实provider/费用或原用户DOM结果。70组仍11通过/6失败/14待复测/38未验/1支付后置。

## R228 Root默认治理门真实失败及CURRENT回归修正

原8264已终态：ten-repository-standard153规则违反exit1；topology5个gitlink/checkout HEAD差异exit1；scripts/tests 1719pass/2fail/3skip，126.96秒。两失败为contract checkpoint evidence gitlink与冻结清单不一致，以及本轮CURRENT压缩漏保活跃测试归属说明。Root未放宽test或更新组合指针凑绿；补回“子仓的 tests 不迁入 Root；scripts/tests仅治理、verification跨仓”的当前职责后，同topology测试文件实际7pass/0fail，/tmp/r228-root-topology-tests-green.log。完整scripts未重新全跑，checkpoint差异仍开放。真实诊断 /tmp/r228-root-checkpoint-diagnostic.json，源码/旧receipt的组合发布需独立验证，不把历史checkpoint当当前通过。标准153、拓扑5与checkpoint失败明确保留；三日志/tmp/r228-root-standard.log、/tmp/r228-root-topology.log、/tmp/r228-root-script-tests.log。

## R228 真实Web协议/恢复执行记录（不增加70产品组PASS）

|用例ID/标题|预置条件|测试步骤|预期结果|优先级|类型|实际结果与范围|
|---|---|---|---|---|---|---|
|TC-WEB-R228-AUTH-RECOVERY / 正规登录协议与工作区故障恢复邻门|Web冻结935b1ea7、隔离真实Next/Chromium、现Redis15自有身份、受控IAM/BFFpeer；非用户3310|完整执行现OIDC系统77case：登录回调/状态与CSRF、refresh/退出/撤权负例、session body挂起→deadline→人工Retry→旧尾段隔离、正常刷新恢复；核owner调用及资源回收|业务正确拒绝/恢复、不泄露数据/凭据、不无限探针、迟到结果不污染当前状态；源码与Redis集合保持|P0|主链、边界、异常、权限、状态机、系统|77pass/0fail/0skip，116.259秒；manifest见本页R228事实。真实owner组合/用户3310根因/实际收费未验|

## R228 已提交费率切片与完整 Web 协议系统门（2026-10-04；当前事实）

上一回合归progress：Root承接真实Web1项终态并核Billing107/1361日志、沿同台账续派五D0。不缩小完整Wave0–7。

Billing Root按20明确路径本地main提交 **8f091d40bd3695144861e88159e88d9d767112c1**：两rate canonical表/正规派生、pure codec、module-private publication、永久receipt/replay/audit与真实系统测试已交付。15 non-doc Git objects精确等Root冻结（仅旧pure测试标题every→representative，原全部断言保持，Root231pass）；5docs仅接RootR228+已审R227/R223+原HEAD，受保护旧mixed全文保持工作树，不夹带入提交。最终publication/source与五doc审0P0/P1/P2，107真实PG/1361辅助门绑定同生产源码，index空，现仅五D0 dirty。收据`/tmp/r228-billing-commit-receipt.json`。未push/Root gitlink/3310启用，没有实际价格、充值、余额或provider动作。policy、选择/quote、正式Admission、原始实际usage、结算/释放/流水与用户收费整链仍开放。

Web Root原74057终态：同现oidc-rp-next-http.integration.test.ts完整 **77 passed / 0 failed / 0 skipped**，116.259秒；是真实隔离Next/Chromium/现Redis15与受控IAM/BFF peers，不是用户3310或实际模型收费。冻结935b1ea7、source_same=true、Redis key集合same，所有新资源句柄终态。manifest `/var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-r228-web-full-zcb2hf4x/manifest.json`，日志SHA98313ad6bdca4124fc85ba156ce3937b988f4f253b92167c3bd7a98f93e55269。完整协议/首屏故障恢复邻门不证明原用户加载根因已修；现IAB tab1定向focus仍超时未取DOM，未绕过/新开/刷新/重启。

原Agent owner独立推进原始usage观察四D0设计门，只准现文档当前前缀，source/schema/contract/lock冻结；missing不能从SDK归一0当实际zero、单物理response/invocation-local、有限解析/EOF/取消/隐私/digest材料待Root审，不提前放开正式native Run或收费。70产品矩阵仍11通过/6失败/14待复测/38未验/1支付后置，未将77协议或107PG当新增整页面PASS。

本轮format首次从Root以pnpm --dir调用遭Corepack选择12.3.4而非固定11.25.0拒绝；未放宽engine/package。转正确Billing cwd后Node24.20.0/pnpm11.25.0及format真实exit0。错误命令不当产品逻辑RED，历史记录保留。

## R227 最新已执行结果与用户进度口径（2026-10-04；覆盖本轮下方早期候选描述）

整体研发/浏览器用户旅程仍未闭环；70产品验收组现场重算保持 **11通过 / 6失败 / 14待复测 / 38未验 / 1支付后置**，不把工程用例数换算成页面或仓库完成率。Root与11物理子仓仅本地main；Web19/BFF20/Billing20 dirty，8仓clean，Root五gitlink与受保护uv.lock保持；未新核远端。原3310 PID46036仍运行旧组合，未把新候选自动启用到用户页面。

Billing Root原6274现已终态：10工程/生成/契约步骤全部exit0；9文件真实PG **107 passed**（含publication14），39文件纯/契约/架构/http **1361 passed**。本轮真实发现并修复audit UUID关联、NUMERIC78 Decimal科学计数读回两项P1；最终独审0P0/P1/P2。source/正规派生保持、自有库回收/邻库集合保持。manifest：`/var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-r227-billing-final-lrk72u3z/manifest.json`。rate-only module-private切片仍为待提交候选；完整PUB矩阵、HTTP/真实COMMIT网络ACK、policy、Admission、原始usage、正式预占/结算/释放/流水及用户UI仍开放，不改实际价格余额。

Web Root承接原46388，真实隔离Next/Chromium与现Redis系统测试 **1 passed / 76名称过滤skipped**，20.108秒。200 headers已到但JSON body持续不结束时，现10秒deadline实际中断；人工Retry同document恢复，关闭的旧transport尾段不污染新状态。source与Redis key集合保持；独审0P0/P1/P2。manifest：`/var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-r227-web-body-6hkrs2xf/manifest.json`。IAM/BFF为受控peer，不是原3310用户浏览器或真实模型/费用验证；76未跑不计通过，原用户无限加载根因/修复仍未证实。本片只新增系统测试，无生产UI修改。

Root已续派原Billing owner仅五D0当前证据前缀回填，旧全文保护；两资源句柄均终态，无重复服务、共享reset或provider费用。当前主瓶颈是固定组合用户加载复现、Agent可信执行与Billing授权/用量接线、逐页面CRUD及Settings验收，沿原任务表推进。

共同预置：当前Billing canonical34表及冻结pure codec，Root自有真实PostgreSQL/Prisma fixture、真实编译Nest module-private provider；受信BillingAdminContext只在包内入口使用，不冒真实IAM管理员HTTP。无生产价格、资金、provider操作。原4schema子例完整保留。

|用例ID/标题|预置条件|测试步骤|预期结果|优先级|类型|当前状态|
|---|---|---|---|---|---|---|
|TC-BILLING-R227-PUB-01 / 正规发布与永久结果|共同预置、合法1..64个QA合成tariff|private provider publish→查header/rates/receipt/key/audit→同key重放→换key同identity重放|一次发布/audit、闭集7字段原bytes/revision不变、各ordinary字段/digest与canonical一致；仅换key可新增绑定|P0|主链、幂等、系统集成|有限通过：首发/原key及新key重放/7字段/64行已由Root真实执行；不等于正式报价或费用链|
|TC-BILLING-R227-PUB-02 / 数量精度和时间边界|合法最大Unicode/NUM78/range及过去/未来/同instant draft|发布最大合法draft→精确读回→发布同effective及两tenant→revision极值/溢出|合法不截断、不浮点算钱；DB publishedAt一次UTCms，draft effective保持，tenant独立递增；溢出整组rollback|P0|边界、数据、生命周期|部分通过：Unicode/range/NUMERIC78/64行与溢出已验；全effective时间组合和跨tenant独立生成序列仍待补|
|TC-BILLING-R227-PUB-03 / 失败恢复和并发|两个独立真实连接、完整事实快照|同identity不同key竞争；不同identity同tenant竞争；深层真实SQL失败；已commit调用者丢返回后重放|正确锁序，无第二效果；SQL失败rate/receipt/key/audit零新增；丢返回模型不冒COMMIT网络故障，重放原结果|P0|异常、并发、恢复|部分通过：同identity并发、audit故障全回滚已验；不同identity序列/真实COMMIT网络ACK/重启恢复未验|
|TC-BILLING-R227-PUB-04 / 授权在所有副作用之前|null/wrongrole/tenant/drafttenant/operator受控负例、合法DB|提交越权与payload组合→实际数据库查询计数及全事实快照；合法主体再提交|固定FORBIDDEN；codec/transaction/SQL之前拒绝，零查零写；无新scope/header/HTTP绕过|P0|授权、安全、系统集成|部分通过：所列不可信binding拒绝及DB关闭时FORBIDDEN、独立facts零写已验；完整逐SQL调用观测待补|
|TC-BILLING-R227-PUB-05 / durable事实和replay生命周期|一次成功发布，fixture独占SQL篡改或删除|分别改header/rate/digest/count/顺序/结果字段、同key/换key重放、读取全facts|CORRUPT/CONFLICT固定安全文本，无返回篡改数据、无第二rate/audit或新key残留；prepared/succeeded永久receipt在同事务闭合|P0|状态机、异常、安全|部分通过：ordinary drift、两类receipt腐化原/新key回滚已验；完整header/count/order等篡改矩阵待补|

这是正式publication片验收，不关闭policy/Admission/积分/用户页面任务。

## R226 限定系统用例GREEN与产品边界

Agent单completion用例已Root实跑GREEN：现单文件147case包含57个R225参数case，以下两行旧RED保留作历史；默认/显式n1、五override n2、sync/async×stream/nonstream、invalid scalar和raw缺n全部按正式hook验证，非法零POST、合法exact n1。六邻门451、默认2253不重复加总为用户功能。Agent已localmain f3050fcc；完整输入/reader/Billing/provider/3310用户路径仍OPEN。

Billing下方四schema子例现d7d29精确oracle与fba45f68 canonical均Root实跑4pass；先缺表RED和oracle修复历史保留。正规Prisma旧derived stale RED→fresh生成/check GREEN，数量32→34旧断言实际2fail/66pass后精确修复，最终完整68pass/0fail/0skip，source/generated/邻库集合同。不得以此关闭发布授权/replay/rollback、报价/资金或页面收费组。完整70任务矩阵状态仍11/6/14/38/1。

## R225 Agent单completion执行界真实系统RED（2026-10-04）

同一70组不增加产品PASS。共同预置：Agent d50bde5f+仅现peer test a43c5f10；锁定SDK、真实自有loopback HTTP、固定System response与owned clients，无正式Billing许可，不是当前用户付费Run。Root原13839实际2pass/5fail/90名称过滤0.83秒、source hash同；manifest `/var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-r225-agent-n-red-nz9jjq64/manifest.json`。

|用例ID/标题|预置条件|测试步骤|预期结果|优先级|类型|实际结果与边界|
|---|---|---|---|---|---|---|
|TC-AGENT-R225-N1 / 默认与显式单completion|共同预置；两个参数case|正式resolve→锁定SDK默认/显式n=1 ainvoke→真实peer→核model/O/path/request数与client close|一物理请求、结果ok、output cap来自route；GREEN后默认也须wire显式整数n=1|P0|主链、契约、生命周期|2pass；RED默认允许省略n，不冒默认gateway语义验证；GREEN收紧现候选尚未实跑。|
|TC-AGENT-R225-N2 / 五公开override外发前拒绝|共同预置；invoke/bind/bind_tools/extra_body/native五case|以各公开seam设置n=2且O合法→记录peer原bytes/实际count→检查本方guard和close|固定单completion，不扩大bound或静默改请求；0POST、固定safe ValueError、owned两client closed|P0|异常、边界、安全、系统集成|5fail；每例实际POST1、原wire n=2/cap128合法，在expected0/actual1失败。正确业务RED，不是setup或SDK自拒；原owner现factory+test GREEN在写。|

输入C的完整billable覆盖、technical bound/reader、真实Billing Admission/provider/用户Stop与流水仍OPEN，单completion修复不替这些门。

## R224 Rate canonical系统测试（2026-10-04；不增加70任务组通过数）

共同预置：Billing main87cbe82f的完整现canonical schema；Root自有真实PostgreSQL fixture、逐case回收；冻结测试98483b9e，不seed生产价格/更改余额或调用模型。原句柄16996实际4失败/4，setup健康，失败是两rate表缺失；日志manifest `/var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-r224-billing-rate-red-dgr6b1np/manifest.json`，源与数据库集合保持。

|用例ID|标题|预置条件|测试步骤|预期结果|优先级|类型|实际结果|
|---|---|---|---|---|---|---|---|
|TC-BILLING-R224-01|正式费率持久结构|共同预置|完整fresh安装→读取columns、CHECK、全部索引→核两表ordinary字段及窄索引|类型/精度/nullability、约束语义与effectivity DESC严格符合D0，无最长Unicode绑定宽索引|P0|集成、契约、数据|FAIL：columns=[]。独审P1指出当前oracle只核CHECK名及索引列，未完全核正文/DESC；正在补强，不能准SQL GREEN。|
|TC-BILLING-R224-02|最大合法Unicode与数值边界|共同预置；production codec合法synthetic QA draft|五独立255个4byte Unicode绑定（5100byte）先通过codec→真实insert/readback MAX BIGINT与78位约分有理数|完整保存、不截断、不发生宽btree错误、无数值精度损失|P0|边界、集成|FAIL：revision表缺失。价格仅synthetic fixture，不是采购价配置。|
|TC-BILLING-R224-03|非法形状与数值拒绝|共同预置；合法all/range正控|提交错误nullable形状、空range、ordinal64、分母0、revision0/溢出及NUMERIC溢出→核PG拒绝|稳定CHECK/数值拒绝，无非法持久事实|P0|异常、边界、集成|FAIL：revision表缺失。独审P2要求补count/digest/text/key/currency/negative等代表性负控，整组仍OPEN。|
|TC-BILLING-R224-04|租户与revision唯一性|共同预置；A/B租户与两revision|同租户重复revision、ordinal、digest；换tenant正控insert/readback|本scope重复拒绝，不同tenant可独立存在；ordinary事实不被摘要代替|P0|隔离、幂等、集成|FAIL：revision表缺失；publisher auth/replay/rollback仍需另外正式旅程。|

上述是schema边界系统子例，不能代替授权发布、quote、预占、结算/释放、流水或浏览器收费闭环。待原writer补强测试oracle、Root自然RED复验及独审后才授SQL-only。

## R220 系统验收状态更新（2026-10-04）

R221提交绑定补记：上述冻结源码已按21路径提交Agent d50bde5f5b19dc89f6a56640c9e464174dc52ab4；17source/machine/tests和已验bytes一致，四D0只更新前缀，Git object21/21一致。Root再验固定来源/contract/源format/lint及clean artifact build通过。首次build/lib format和首次scratch路径错误保留在progress；没有新增当前用户浏览器/模型费用PASS，也不虚增70产品组。

R218两真实反例已在冻结R219候选复验关闭：System3.0严格消费与SDK实际输出界、覆盖参数/流式/客户端释放取得394定点通过，其中90真实本地HTTP/锁定SDK场景。306真实PG、3生命周期与2253默认工程门通过；默认497资源deselected不算通过。安装制品18步骤的正常检查、RECORD篡改拒绝、修复RECORD后的固定来源语义篡改拒绝与恢复检查均实际通过。独立源码审查0P0/P1/P2；所有结果仅绑定冻结候选，不把工程测试计为产品组。

70产品组仍11通过/6失败/14待复测/38未验/1支付后置；没有新的当前3310浏览器用户验收。正式Billing许可、核实实际用量/扣款与余额流水、项目全CRUD、独立任务、工具审批、Skills/MCP、文件作品、Settings13tab仍须各自系统用户流。下方R218的NOT_FIXED为当时RED记录，保留但不代表当前候选。实际证据与失败历史见progress R220。

## R218 System元数据与Agent真实消费者反例（2026-10-04）

|用例ID/标题|预置条件|测试步骤|预期结果|优先级|类型|实际与边界|
|---|---|---|---|---|---|---|
|TC-AGENT-R218-A / 正规3.0 response接收绑定|现公开SystemModelClient、owned真实HTTP peer、合法同response identity+两bound|正式resolve请求→peer核exact路径/body/1request→返回3.0→核完整内部identity与bound|接收required严格界，同一revision绑定，不丢字段|P0|主链、契约、集成|Root87510正确RED MODEL_RESPONSE_INVALID；当前源码仍2.0，NOT_FIXED。|
|TC-AGENT-R218-B / 锁定SDK真实输出界|现LiteLLM constructor、真实owned completion peer，无生产Billing许可|实际ainvoke→peer先核ok/path/model/1request→读取JSON cap/冲突别名|正式动态owner bound落实为max_completion_tokens，不能由测试向裸SDK注入128自证|P0|边界、集成、安全|Root87510正确RED None≠128；这是现无界wire缺口，NOT_FIXED；此独立probe不是完整System→factory→SDK或Billing正控。旧14case通过。|
|TC-SYSTEM-R218-META / 已实施owner与pending消费者元数据|真实生成OpenAPI/provenance/README，版本3.0|分别核description、唯一Agent pending+历史2.0 baseline、两actual文件digest；正规重生后复验|机器文字与实际阶段一致，19source/operation/schema不漂移；未消费不冒已验|P1|契约、数据真实性、状态|Root3failed/11passed RED→check/16contract/205全测试/fresh23断言22表GREEN；本地commit955bd58。仅metadata，不冒Agent或UI闭环。|

两Agent反例SHA87797089，Rootowned peer/source391全保持；System6path独审a246527a归零、完整资源终态保持，TTL自然过期而非清共享缓存。完整70组11/6/14/38/1不升；Root91992辅助28边界+13收据声明/篡改门实际18failed/23passed/124deselected12.79s，source_same true；缺required/missingboth漏拒/11tamper未拒/inventory缺失为正确RED，23负例旧extra拒绝不当完整GREEN。源码原子Green已授原owner，完整decoder/SDK override/ownership/installed/nativePG/真实provider与积分链仍须实际验收。

## R217 四故障系统矩阵（2026-10-04；不改变70产品组）

预置共同边界：正式受信Message HTTP、真实owned PostgreSQL/现Redis、冻结BFF候选；Root资源独占，最后commit7289b3a4运行树395项与已验候选完全一致。原3310未升级，本轮没有浏览器全链验收。

|用例ID/标题|预置条件|测试步骤|预期结果|优先级|类型|实际结果|
|---|---|---|---|---|---|---|
|TC-BFF-R217-M1 / SQL错误与真实断链回滚|自有DB/实际backend PID/完整事实基线|正式提交触发SQL错误；下一断链子路径terminate准确backend；取全facts，观察exact client listener/release与替换backend|有限503、零部分事实；坏client release(true)，operation listener卸载、原PID消失、健康后续成功；无进程uncaught|P0|异常、事务、生命周期|Root51194真实uncaught RED；5864修复后Root24434此例通过，独审归零。|
|TC-BFF-R217-M2 / COMMIT成功但ACK丢失|真实COMMIT可被fixture传输故障打断响应|真正提交后丢ACK→503→同key同body重放→核canonical dispatch/Run/Message/全事实|一次提交、原身份恢复、零重复写；unknown client精确销毁，不伪造generic receipt|P0|异常、幂等、恢复|Root24434四矩阵及82959完整182门通过。|
|TC-BFF-R217-M3 / 四scope变化共享总界|真实双连接/coordinator SQL延迟、owned scope fixture|观测四次真实预读/scope变化、累计物理延迟>4.5秒→等待终态/迟到query收束→核产品零后写及fixture还原|一个4.5秒预算、HTTP<4900ms/503；无按重试重置期限、无迟到提交|P0|边界、并发、状态机|Root24434及完整182门通过，未放宽时限。|
|TC-BFF-R217-M4 / 提交后通知throw/迟到|真实通知已触发，随后可控throw/late|正规Message提交→通知故障→核成功事实、有限响应、replay与恢复|持久提交保持、通知故障不反转业务提交/重复写，无第二deadline|P0|异常、容错、恢复|Root24434及完整182门通过。|

真实RED3/1→GREEN4/0/0（5.462s）；完整182/0/0（58.539s）。manifest `/var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-r217-bff-full-ygz0gcao/manifest.json`；自库absent/源码/Redis/secondary同。743默认+1既定skip、236contract不算产品验收组。70组仍11通过/6失败/14复测/38未验/1支付后置；主动HTTP取消、当前页面加载、Project DELETE、Agent/Billing完整旅程继续开放。下方R215等为历史，不覆盖R217。

## R215 限定系统验收（2026-10-04）

|用例ID/标题|预置条件|步骤|预期结果|优先级|类型|实际与未验边界|
|---|---|---|---|---|---|---|
|TC-BFF-R211-POOL / 池饱和及幂等恢复|正式authenticated Message HTTP、真实max10池、自有DB；三source793c/546e/71ec与测试3b3f冻结|持满10→发送→等待有限503→归还一个观察late Client→第二全facts快照→全部归还→同key健康202→同key重放|<4900ms/503/header/no-store；两个窗口零事实、pool精确10/10/0；正式dispatch与Run/Message IDs一致；generic receipts不变；重放全facts不增|P0|异常、幂等、资源、状态机|Root20543完整178/0/0真实门通过；修上轮generic receipt错误oracle。原shared/current3310未集成，新四组transaction faults未跑，不关闭整产品组。|
|TC-SYSTEM-R215-CACHE / 合法checksum非法执行界|真实Nest/自有PG/Redis namespace；健康route、合法key/generation/TTL；output101/context100|首次HTTP200→按生产checksum写真实毒cache→同HTTP→清ownedkey→恢复请求→核完整revision/fences|503 SYSTEM_UNAVAILABLE；清key后200；DB/generation零差，无静默回源接受|P0|异常、安全、边界、恢复|61854仅setup409不计RED；36499实际200错误为正确RED。唯一schema31b6后Root41905完整202/0/0门通过，System bd09253本地提交；不代表SDK/Agent/Billing/current UI链。|

System canonical draft/publish/partial-merge/int32/immutable/digest边界在同真实owner门执行，fresh23/22完整catalog通过。工程数量不当产品用例组；70组保持11/6/14/38/1，新增四组BFF故障矩阵和真实用户页面后继仍开放。

## R214 验收状态核对（2026-10-04）

本轮没有重新浏览器验收，不增加产品通过组；原70组仍11通过/6失败/14待复测/38未验/1支付后置。最新BFF隔离全门177/1：pool候选已达503与4503.5ms及双零事实/静止pool/健康202，但最后generic receipt错误oracle未修复复验，不能整例标通过。System199/1及fresh失败；补fixture与真实缓存关系负例仅作者交付，Root复验待执行。逐页覆盖与缺口参CURRENT R214，所有CRUD必须UI操作→正式owner ACK→权威GET→刷新一致，并覆盖主链/边界/异常/权限/生命周期；组件/fixture数量不充当产品验收数。

## R209 TC-BFF-R207-003 限定GREEN与后继（2026-10-04）

原error.request_id oracle不符合正式contract，改为x-request-id后Root39229真实FAIL证明响应头也missing。仅reply入口补受信header后Root45503同HTTP/PG1pass1.266s，完整锁图/503/业务期限/全facts双窗口零写/同pool健康202全部执行；源码、测试冻结，ownedDB和Redis保持。manifest T/kokoro-r207-bff-blocker-red-jtyr2af9/manifest.json。这只关闭该限定子例，原R207完整有界资源组仍OPEN；新增R209累积SQL真实trigger反例在途，不用单例GREEN上调70组。

## R208 执行状态补记（2026-10-04）

TC-BFF-R207-003 当前候选由Root20681真实HTTP/PG复验：1fail/1.248s，503/code/时限/no-store断言已通过，随后request_id断言actual null/expected true；错误字段定位须先核正式契约，不能先猜产品根因。完整事实双窗口零差及同pool后续202尚未执行。manifest `/var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-r207-bff-blocker-red-70m7u84a/manifest.json` 自有DB已回收/source和Redis保持。此例仍FAIL，既有70组统计不变；本轮没有浏览器页面重测。

## R207 取消与进程生命周期限定验收（2026-10-04）

|用例ID/标题|预置条件|测试步骤|预期结果|优先级|类型|实际结果与边界|
|---|---|---|---|---|---|---|
|TC-AGENT-R207-001 / 不合作driver超时fail-stop|冻结68a64a2b系统测试及真实Supervisor/invoke/pump；自有子进程、受控bus/repository/runnable|serve消费Run→公开RunCancel→不响应cancel的iterator→固定settle deadline；cleanup若触发即挂起负控；观察退出marker|stop-intake、cleanup零调用、实际exit70；非法fatal callback返回仍exit70；不生成假的终态/费用结论|P0|异常、生命周期、进程系统|Root43772实际两fatal case通过；作者旧cleanup反例先FAIL保留。受控依赖非真实PG/provider/资金用户链；整组不因此关闭。|
|TC-AGENT-R207-002 / production SIGTERM共用入口正常退出|同自有子进程，production私有shutdown入口、真实Supervisor及合作invoke|parent等真实readiness后发SIGTERM→同budget取消serve→合作task/context退出→drain→检查进程状态|正常exit0、drain true、零fatal；同一production signal代码无测试复制|P0|状态机、生命周期、恢复|Root43772与上述两case共3pass4.60s；真实PG306同时通过，scope执行源码提交92b802e。不是完整main外部资源装配或浏览器Stop证明。|
|TC-BFF-R207-003 / Message Project锁等待有界零写|clean8e33+R189；真实HTTP/ownedPG双连接，测试81f35482|锁本人Project→body project_ref发送→观察owned blocker PID→响应前/后完整事实对比；fixture5.2s安全释放→同pool后续正常Message|内部4.5s有限失败/HTTP503而非迟到成功；完整事实零差、pool可复用|P0|异常、事务、资源、业务系统|Root48540真RED：实际202预期503/case5.297s；ownedDB absent/source_same/Redis_same，原owner实现GREEN在途。未通过，不关闭锁预算组；后续pool/unknownCOMMIT/rollback/四轮预算另须实测。|

306真实PG/2192默认工程门不是306/2192条产品验收。原70组11通过/6失败/14复测/38未验/1支付最后保持，费用与当前3310实际旅程仍OPEN。

## R205 原生取消限定系统验收（2026-10-04）

|用例ID/标题|预置条件|测试步骤|预期结果|优先级|类型|实际结果与边界|
|---|---|---|---|---|---|---|
|TC-AGENT-R205-001 / prepare等待时取消与返回后零后写|冻结312bb9d测试；原生SDK/AgentFactory；真实自有PG Run/checkpointer/store schema；无正式Billing许可|独立PG连接持Run锁→实际观察prepare锁等待→取消invoke并await→取完整DB/checkpoint快照→释放锁并等prepare结束→比全快照；隔离旧四guard负控与新guard重复同流程|原CancelledError；provider0、prepare cancelled；Agent四表完整零差；返回前仅一个精确__error__/CancelledError()审计，移除后原pending值顺序/完整tuple全等；返回后全快照无差|P0|异常、生命周期、事务、原生集成|Root23099旧guard2pass/1fail5.50s、cancel→release9叶后写；Root7813新guard3pass/0fail5.31s，canonical10CHECK0，两个ownedDB absent/clone及原源码同。此case通过仅cooperative取消；不合作driver/fatal全链、真实provider/Billing及当前3310用户Stop仍待验。manifest见progress R205。|

R206补验：Root64906对显式owned/shield driver候选重跑同312bb9d真PG三例，3pass/80warnings5.14s，ownedDB absent/clone与明确原source闭集SHA保持。完整fatal链独审仍有sandbox cleanup先于fatal的P1，当前用户Stop未验，不关闭整组。

沿原70组统计11/6/14/38/1不升；整组要继续覆盖不合作退出、恢复和完整用户费用路径，不以此限定系统门结案。

## R191 原浏览器逐页业务验收（2026-10-04）

沿既有70组，不增加虚假完成数。每个可见操作分别覆盖：主链、边界、异常、权限、状态机、刷新/跨页/跨窗口；必须取得UI终态与事实owner证据，页可打开不算CRUD通过。实际运行态为现3310窄同步组合，源码态与该组合分开记录。

|用例ID / 标题|预置条件|测试步骤|预期结果|优先级|类型|实际结果与未验边界|
|---|---|---|---|---|---|---|
|TC-UI-R191-001 / 原IAB会话与项目刷新|原有tab1合法Product session；用户本人QA会话与项目|读取原会话→展开侧栏→点项目→硬刷新→限时等待真实项目标题|消息/可编辑输入及项目正确显示；加载有终态，不错误覆盖数据|P0|主链、状态机、刷新|原tab1实际会话消息及输入已渲染；项目实际进入并刷新后标题可见。仅当前正向路径通过，不证明历史所有无限加载根因已修/过期session/503/跨窗口异常通过。刷新瞬态先显示“专案不可用/正在加载专案”，属于加载与错误状态混用待修。截图/tmp/kokoro-r191-iab-project-after-reload.png|
|TC-UI-R191-002 / 项目会话入口语义与空态|001同项目暂无会话|点击Project列表下孤立“专案会话”气泡→观察URL/内容/焦点→返回项目概览|会话列表与新建动作明确区分；空态无幽灵会话，不把创建动作标列表导航|P1|交互、状态机、空态|实际进入带新conv ID的草稿路由，主区仍空会话/新对话；没有发送消息。初次实际FAIL保留；Root精准删除孤立shortcut，原IAB再验count0/明确新建入口1，新建仍到正确project草稿且可回概览。main3310351、完整冻结工程2469pass/build0；未发送模型。仅语义子例关闭，持久零写/首次消息创建/全部CRUD仍需owner/网络核验|
|TC-UI-R191-003 / 项目网站选择器真实来源|001同项目、正式用户入口|点网站新增→读取资源选项→取消，不保存|仅真实授权资源可选；不暴露开发示例，不用内存保存冒持久关联|P1|功能、数据真实性、异常|原IAB实际选项含产品发布页launch.example.test；已Cancel。数据来源/owner/save持久化由Web只读负责人核查；弹窗可打开不算网站功能通过|
|TC-UI-R191-004 / 清理无用浏览器标签|原4个IAB标签：同会话两重复、旧callback、当前原tab1|读取重复textarea为空→核旧callback错误→关闭3个无用tab→重新列库存|保留当前用户页与草稿，无多余测试窗口，不误删数据|P2|资源、交互|实际关闭两个空草稿重复页和rp_transaction_rejected旧callback页；库存仅tab1项目页，未新开tab/模型调用/永久服务。该callback失败只记观察，不猜原因|

### R191 独立深审发现与系统待执行矩阵

只读审查不冒运行测试。Web审计 c3f37cd、Settings审计262afdda绑定maina854及受保护工作树；下面明确区分原IAB实际观察、源码确定缺口、待执行用户流。System/BFF/Platform/Billing/IAM各自拥有事实，Web不另造本地事实补假成功。

|用例ID / 标题|预置条件|测试步骤|预期结果|优先级|类型|状态/Owner|
|---|---|---|---|---|---|---|
|TC-PROJECT-R191-005 / 网站关联真实保存|正式项目，System网站目录与BFF关联契约发布；本人可用网站|新增→选择→保存→owner ACK/GET→硬刷新→解除→刷新|仅授权真实网站，关联持久且隔离，无静态示例或纯内存成功|P1|主链、权限、生命周期|FAIL源码确认：正式preview=false仍读previewWebsites；Save只setLinkedWebsiteId。原IAB样本观察真实，保存/刷新尚未运行；contract前置BLOCKED，Web/BFF/System。不得隐藏后标PASS|
|TC-SKILL-R191-006 / 项目技能两入口一致|真实Project安装技能版本、Platform/BFF写契约可用|Switch与More启停分别操作→GET→刷新；403/503后再回读|同一owner mutation，ACK后权威状态；失败回滚且可见，缺handler不假成功|P0|主链、异常、权限、状态机|FAIL源码：Switch optional handler缺失可假成功；More纯setState，静态Skill Builder单卡。真实用户写链未验；Web/BFF/Platform/Agent|
|TC-SETTINGS-R191-007 / 个性化保存和读回|正式session；目标账号级偏好owner GET/显式PUT已发布后执行（当前未发布）|唯一值输入→显式保存→状态码/ACK回读→关重开→硬刷新；404/503/跨subject/陈旧revision冲突|失败明确保草稿/可重试，不假保存；成功同subject权威GET可读|P1|主链、异常、权限|真实FAIL：正常昵称blur PATCH404、无错误提示、硬刷新空（r257-personalization-red）；正式 BFF owner operation 缺失（同源 catch-all 可达）、PATCH不查response.ok且无GET。Root46862隔离真实PG/Redis+受控IAM边界，普通me200后GET404，1FAIL/0skip；GET/PUT CAS源码进行中，正常Web显式保存/失败反馈与硬刷新仍未验；不造localStorage账号事实|
|TC-SETTINGS-R191-008 / 通知偏好实际生效|Web设备偏好、已授权Notification，真实awaiting审批事件|关闭→切tab/刷新→产生事件；明确点击开启→权限拒绝/允许→再事件|关时零通知且持久；权限仅用户手势，拒绝不假授权；声音须实际producer|P1|功能、权限、生命周期|源码FAIL：4toggle内存；producer不读开关并业务路径requestPermission。设备browser/sound归Web；账号通信订阅owner待定，实机通知NOT_RUN|
|TC-SETTINGS-R191-009 / 快捷键编辑影响实际动作|可编辑实际New chat/Search/Sidebar动作|重绑/清空/reset→新旧键→关重开/刷新/第二tab；IME/repeat/editable/冲突|仅新键一次动作，清空无动作，持久一致，录制与全局监听无重复|P1|交互、边界、竞态|源码FAIL：UI内存与硬coded dispatcher双事实，Sidebar显示与实际键不同；不支持Plan/Voice不算实现。Web负责人后继最小片已设计，真实全矩阵NOT_RUN|
|TC-SETTINGS-R191-010 / 默认模型Agent跨主体安全|A/B合法session、不同可用目录；同浏览器|A保存selector→登出→B登录新会话；目录404/503/撤权|B只可用自身已核验selector或默认，加载失败显式错误，不吞空注入旧值|P1|权限、异常、生命周期|源码FAIL：全局chat-prefs key且agents404吞空；跨主体实际用户流NOT_RUN。Web/System/Agent/BFF；不是认证已可用就通过|
|TC-SETTINGS-R191-011 / Computer和Integrations正式错误收口|相应owner contract与同源adapter已发布；无实际付款|打开计划/连接→提交至owner sandbox→404/503/unknown→重试/刷新|金额取Billing/正式quote，未知不重复/不假成功，错误就近可见，终态有界|P1|异常、幂等、主链|源码FAIL：两个POST route不存在、void async无catch/UI；Computer金额前端常量。付款后置/不触发真实支付，System/集成owner/Billing/Web依赖未闭|
|TC-SETTINGS-R191-012 / 所有远端tab有限加载与晚回包|Credits/Plans/Skills/MCP/Teams/Chat真实读，controlled header/body延迟|逐页hold超预算→切tab→重挂载→释放旧包→Retry|预算后error/retry，卸载取消，迟到回包不污染当前tab/主体|P1|异常、加载态、竞态|源码缺统一可证明总timeout；当前503/404已观察，header/body hold专项NOT_RUN。Web各consumer独立门，不拿一次终态代全部|
|TC-AGENT-R191-013 / 首次dispatch和重放唯一许可|正式Agent fresh schema/真实PG两连接、合法prepare/grant|begin/grant/dispatch→精确及advanced replay；两连接竞争；wrongtenant/fence/terminal/ref/digest/timeout|恰一次newly_started=true，持久timestamp/计数不重复，unknown不可重外发；拒绝零写、超时回滚|P0|状态机、并发、权限、事务|Root63612真实RED56pass/3fail5.54s：具体repository三操作缺失，自库absent/hashsame。GREEN实现中；只有owner内部事务，Billing真实性/provider/runtime系统主链仍OPEN|

Settings13页逐项库存：General（通知FAIL/主题语言待实测）、Account（正式仅logout，其余禁用不计CRUD）、Credits（503）、Shortcuts（FAIL）、Chat（404与跨subject风险）、Personalization（route/读写缺失）、Subscription（503/支付后置）、MCP（503/写版未发布）、Skills（503/写版未发布）、Computer（route缺失/无可见reject）、Deployment（仅composer导流/升级不计资源CRUD）、Integrations（route缺失）、Teams（读取200、邀请/角色/移除/退出/刷新与权限NOT_RUN）。见现T-U04/R187和TC-SETTINGS-R190-007，不另建任务中心。

### 全页/全模块深度退出门

1. 每页每个按钮/菜单/快捷键有现TC映射、owner、执行结果和当前版本；没有handler/契约的能力明确FAIL或BLOCKED，不用隐藏把它清零。
2. 每个CRUD执行创建→读回→修改→刷新→删除/恢复（永久删除须确认），验证空/长/重复输入、迟到响应、失败回滚和越权；缺一不得关闭该业务组。
3. Agent旅程必须真实首发→排队/唯一执行→过程展示→完成或审批/取消→刷新续流；Billing核实实际消耗、余额和流水需独立真实闭环，不以工程门代替。
4. Settings逐项保存→切tab→刷新→退出重登→跨窗口对账，核对实际动作变化；本地偏好与账号事实明确分开，保存失败不可假成功。
5. 当前发布组合一致，P0/P1清零、所有必要用例通过且清理证据完整，才关闭整组。原70组仍11通过/6失败/14复测/38未验/1支付最后。

---

## R190 系统级业务执行收据（2026-10-04）

复用原70组与下方逐页库存，以下是细化子例，不增加整组完成数。当前源码候选、真实owner、Next系统fixture、用户3310运行组合分别记录；完整用户路径未通过的组保持开放。

|用例ID / 标题|预置条件|测试步骤|预期结果|优先级|类型|实际结果/未验边界|
|---|---|---|---|---|---|---|
|TC-BFF-R190-001 / 消息与Move的双方锁序|本人P/Q项目、真实HTTP/PG双连接、canonical会话|Move先占父锁后发送省refMessage；反向先Message再Move；观察精确blocking图，解自有barrier|每次whole-attempt权威scope冻结，原P不改、新Q准确，无倒序锁/重复消息|P0|并发、状态机、数据一致性|Root35227两case及60244完整184真实集成PASS；未发布/未串Agent/browser；四次scope耗尽待验|
|TC-BFF-R190-002 / client-created同identity竞争|同受信用户、同key/body，真实两HTTP/backend|首创建停自有INSERT barrier→第二同identity提交→观察实际unique等待→放行→回读|两202同receipt；一outbox/两Message，无权限串写；清理故障完整报告|P0|幂等、并发、异常|同真实R190case PASS；不是低层mock。最终test38a0cecb；全owner184pass/0skip；原混合D18未冒公开CRUD完成|
|TC-STORAGE-R190-003 / 真实个人文件生命周期|正式Storage14f2，owned单应用库独立schema，既有S3/ClamAV，合法BFF credential|空列表→创建upload→签PUT→Complete真实scan→非空列表→download并比bytes/digest|合法对象CLEAN可见可下载，原字节准确；自有资源可回收|P0|主链、生命周期、数据一致性|Root83744九业务检查+同库schema前置共10项PASS、cleanup[]/hashsame/Redis6同；仅owner RPC组合。原3310Library仍503，未经Web上传/刷新，不关闭T-F组|
|TC-STORAGE-R190-004 / 文件主体与服务身份隔离|003实际CLEAN asset；另subject及坏credential|另subject列表和download；坏workload credential List|另subject无数据、download404；坏credential401；不泄露正文|P0|权限、安全|真实owner RPC通过，未替代跨tenant/分享/Project资源全权限门|
|TC-UI-R190-005 / 连续改名成功后失败|A/B queued rename；真实列表owner可控响应|A200、B失败→等待owner权威GET→刷新|最终保留已确认A或owner最终值，不永久preA缓存、不伪称B成功|P1|异步竞态、异常、状态机|真实Next/Chromium已执行：A held→Bqueued→A200/B503→owner GET/reload A；Root83186 scoped两例PASS25.21s及完整2469pass/0skip、build0。只有fixture控制流，不是现3310真实BFF闭环|
|TC-UI-R190-006 / 对账后旧overlay不得复活|rename ACK后GET返回canonical C|随后GET失败→恢复GET D→切scope/client|错误态不复活旧rename值，恢复展示D，旧回执不污染新scope；跨hook不能复用preACK请求|P1|状态同步、异常恢复、生命周期|最终源码独审0P0/0P1/2P2；真实Next C对账→D GET503→Retry D通过。Root90201完整2468pass/1fail为C GET抢先消费D故障的fixture时序；仅等待C真实200再注入，Root83186原期限完整2469pass/0skip。signal0重挂、parse/未知HTTP精确负控仍OPEN|
|TC-SETTINGS-R190-007 / 所有tab读与加载收口|当前3310正规IAM session；13可用tab|逐tab导航、观察实际UI/HTTP；对异常页随后重试/刷新/切回；disabled Help不click|读失败可见且有界、可恢复，不假空页/假保存；disabled语义准确|P0|逐页功能、异常、状态机|13导航/内容READ_OBSERVED，仅初步库存，不是完整读写通过。Billing4类503、agents404、MCP/Skills503仍FAIL；部分Loading瞬时未等terminal，不据此关闭加载门。Get help误点击Timeout已注明oracle错误。证据/tmp/kokoro-r190-settings-runtime-reads.json|
|TC-BILL-R190-008 / 正式逐attempt计费契约|既有ADR033/R80-W06、Agent已发布usage1.0.0|校验attempt/admission/evidence immutable身份、version/digest、unknown/verified；再由正式消费者对接|仅核实实际消耗结算，释放确认余量；202入箱不冒settled；owner计算费率|P0|契约、状态机、账务一致性|Root59378 Node24完整verify+生成drift均0：1347pass/411资源skip；最终独审0P0/P1/P2。started必须authorized，三非法组合真实Ajv RED→GREEN。experimental artifact未发布/消费，runtime/充值/结算/流水用户链OPEN|
|TC-UI-R190-009 / 改名已提交但回执丢失|真实Next/Chromium、正式UI/same-origin、fixture可提交后断socket|UI改名→owner先保存→销毁响应连接→观察一次权威GET→硬刷新|只有一次PATCH，不猜失败回滚、不自动重发；标题最终为owner持久值|P0|异常、幂等、状态恢复|Root33810真实业务RED：commit后GET仍1；修复后Root85523两例PASS，再Root83186同例及完整69系统case通过。不是当前真实BFF/原IAB闭环|
|TC-STORAGE-R190-010 / 恶意文件隔离|003同正式owner及真实ClamAV，owned隔离桶/数据库|签PUT标准扫描测试文件→Complete→等真实INFECTED→List/Download|扫描感染对象不进入可用列表，download404；正常文件仍可用，零主体泄露|P0|安全、异常、生命周期|Root43009自然exit0共14项检查；真实INFECTED、list仅CLEAN、download404；manifest T/kokoro-r190-storage-runtime-11u1jnpb/manifest.json，cleanup[]/源码同/Redis6同；浏览器恶意上传仍未验|
|TC-STORAGE-R190-011 / scanner故障不可伪ready|同库正式BFF/Storage schema；真实未监听的自有loopback scanner port|启动正式Storage→观察ready失败→组合finally停止已登记进程/回收自有桶与库|owner期限内拒绝ready，不冒健康；真实进程身份不丢，自有资源可回收、共享资源不动|P1|异常、资源生命周期|Root5631自然exit0三项检查；manifest T/kokoro-r190-storage-runtime-z2ihtlh4/manifest.json，cleanup[]/源码同/Redis6同；build/stop失败与桶ACK未知分支仍OPEN|
|TC-UI-R190-012 / 当前正式双操作命中与读回|当前3310正规IAM/BFF；本人既有QA会话；正式HEAD双action CSS|桌面普通click改名/Esc、删除/Cancel；键盘改名；UI改名→owner GET→硬刷新→UI恢复原题；640px重复命中|改名/删除不互相截获；取消零写；确认改名持久且可读回；窄屏44px命中区不重叠；零模型调用|P1|真实主链、交互、生命周期、响应式|真实RED两个32px按钮rect完全同位，Delete拦截Rename；正式双操作CSS窄修后Root6172自然exit0十项检查PASS，桌面交集0/窄屏两44px交集0，owner持久/硬刷新/原题恢复；恰2PATCH、0DELETE/0model。Web source2072d0a+CSSa854a81本地提交/运行窄同步；完整Project/Move/unknown ACK/更多触摸与200%缩放仍OPEN。证据/tmp/kokoro-r190-live-rail-verification-result.json，ownedBrowserClosed=true|

退出要求沿原矩阵：每页CRUD/刷新对账、边界/异常/权限/生命周期均有真实证据；P0/P1清零且发布组合一致后关闭整组。原70组统计保持11通过/6失败/14待复测/38未验/1支付后置。

---

## R189 当前逐页深度验收（2026-10-04）

完整 Wave 0–7 不缩小；以下细化原70组，不增加虚假完成数。每页按主链/边界/异常/权限/状态机执行，另覆盖刷新、后退、键盘、窄屏、晚响应和加载收口。工程门、组件交互、真实owner与真实浏览器四层分别记账；只在完整用户路径及所有必要子例通过后关闭整组。

|用例ID / 标题|预置条件|测试步骤|预期结果|优先级|类型|当前实际结果与证据|
|---|---|---|---|---|---|---|
|TC-UI-R189-001 / 移动完成后新视图隔离|A正在Move；真实Engine与owner合法ACK；已committed新Project scope|形成matching回执→替换scope/active或卸载→继续旧UI回调|旧回调不刷新列表、不导航、不在新scope提示；无projection不发Move/retry|P0|状态机、异步竞态|Root67609真实交互RED：旧ACK把新scope0202导航回0201；修后Root96648 UI101通过。最终Root65931 Node22完整2457通过/contract258/architecture50/lint/types/build0；未同步3310，不冒真实运行页已通过|
|TC-UI-R189-002 / 拒绝提示不得复活|当前A会话；正式ConversationMoveError拒绝|A Move拒绝出现alert→切B→切回A|旧拒绝提示不复活；当前新操作可重新显示正确反馈|P1|异常、生命周期|Root95255正确RED 1fail/101名称过滤；新source45039523+test6eb88b7d候选，独审7425470e无P0/P1/P2；Root完整门2457通过，Root47026四真实Next/Chromium邻例通过23.57s（63名称过滤非通过）。前37768错筛选全skip不计通过|
|TC-BFF-R189-003 / 每次发送冻结项目上下文|本人P/Q项目及独立会话；正式HTTP+PG|P省略project_ref发送→Move Q→新key省略发送；再测Direct无ref|首次outbox冻结P，下一Run冻结Q，旧payload P不改，Direct字段缺省|P0|主链、数据一致性|Root74251真实RED：P trace.project_ref缺失。修复候选9f3e86fc，Root34000最终完整183真PG/Redis全部通过46.21s；不是浏览器/Agent全链完成|
|TC-BFF-R189-004 / Move后精确消息重放|显式P首发已提交，再Move Q|原key/body重放→同key改正文→新key旧P|原回执和原payload不改；漂移409；新key过期P404且零写，tenant/owner权限不放宽|P0|幂等、权限、异常|与003同一真实HTTP用例；Direct invalid/null负控Root62952真RED202!=404后恢复，Root34000完整183GREEN；完整Message×Move/Delete邻门未以这一个case替代|
|TC-AGENT-R189-005 / prepare事务与lease|正式fresh schema、受信Run/recipe、真实双PG连接|首次/精确重放→同call并发attempt→跨Run同attempt→旧/过期/终态fence→ordinal耗尽/锁超时|不可变receipt、ordinal集合恰1/2且身份不串，授权失败零写、typed冲突、有限等待完整回滚|P0|主链、边界、并发、权限|Root首轮45pass1fail UUID重放；返修后第二轮55pass1fail是错误gather顺序oracle，修成身份/DB回读而不串行。第三轮56pass5.37s；全database Root27104 267pass73.23s，自库收回/hashsame。只prepare持久边界；lost-ACK真实网络未验|
|TC-AGENT-R189-006 / 实际消耗知识分类|合法sealed not_dispatched及真实runtime_profile_plan recipe|重算计数；合法subagent/handoff与非法feature/peer正反控；后态replay|未调用不算unknown，损坏latest不能假complete，receipt不回滚后续状态，peer基于冻结recipe|P0|状态机、知识完整性、权限|最终81bc源码56真PG通过5.49s；267属于此前9df候选。最终typed boundary独审0新增问题，完整工程2175pass/365资源deselected及build0。全ND知识complete正反控与race输家/全面超时恢复专门门仍OPEN。provider/admission/evidence finalizer/Billing接线尚未通过，不称正式费用闭环|
|TC-NAV-R189-007 / 账户Files正式入口|当前3310正规IAM登录，不发模型消息|账户菜单→Files；随后直接/app/library→Personal files/Agent artifacts|Files进入正式Library而非404；文件/作品读取有真实owner结果或可见重试|P1|导航、异常、主链|真实Chromium先确认Files→/docs404；修复后正规IAM→账户Files进入/app/library且Library可见，窄片c5e92567已本地提交（未push）。两tab/api/hub/library503仍OPEN，不能关闭文件主链；截图/tmp/kokoro-r189-library-runtime.png，报告/tmp/kokoro-r189-runtime-page-qa.json（197449b8）|
|TC-HOME-R189-008 / Home提示与创建模式|当前3310正规账号，无active会话|四提示逐个点击→校验草稿/焦点→Dismiss creation mode；More六项|只填草稿、不自动提交或扣费；创建模式可退出；焦点回composer|P1|功能、交互、状态机|当前真实Chromium逐个可填与聚焦；Game即时读取误判经稳定焦点断言纠正。不关闭首发/所有Home能力；0模型发送，测试context/browser已关闭|

### 当前页面覆盖与退出门

唯一逐页库存复用下方R187主链表及Settings13-tab记录：登录/退出；Home/Composer；独立及项目会话与列表CRUD/Move/Share；项目CRUD；独立定时任务；Agent/Todo/Tools/Skills/MCP/审批；个人文件/作品/项目资源；所有Settings页；普通用户/管理员；积分/流水/正式结算。每一项须记录预置、实际行为、owner结果、UI终态、刷新对账、权限/异常以及执行SHA；未实现/缺契约/接口503不能以隐藏、占位或内存值标PASS。支付后置，运维不扩入研发验收。

当前真实运行组合额外仍见Billing summary503、agents404；并未证明它们导致原IAB加载。原IAB控制超时，未取得同标签恢复证据，T-U04继续OPEN。原70组统计暂保持11通过/6失败/14待复测/38未验/0旧业务待决/1支付后置；独立定时任务随项目删除政策另有待决项，不隐去。

---

R188绑定：Agent schema验收源提交 `500c2c26e303065e8811989336aa20701330f4f3`（本地未发布）；Web/BFF本轮测试绑定冻结工作树，未冒提交态或当前运行态。

R188工程门补记：Agent默认2175通过/352资源deselected，不能替代系统级用例；真实database254通过只证明owner持久化门。Web三个真实浏览器用例已通过，但Move候选未同步当前3310。逐页业务矩阵状态和70组完成统计不因此上调。

## R188 当前深度验收结果（2026-10-04）

沿原70组展开，不新建计划中心、不改变统计为虚假完成。系统fixture证明真实Next/Chromium交互，但不等于现3310真实owner/原IAB同页；纯门不替代用户链。每页/模块仍须主链、边界、异常、权限、状态机及刷新对账全部执行。

|用例ID|标题|预置条件|测试步骤|预期结果|优先级|类型|实际结果/证据|
|---|---|---|---|---|---|---|---|
|TC-UI-R188-001 / T-C02|Direct侧栏交互与拒绝恢复|正规Product session、真实Next/Chromium、fixture owner A/B|A/B打开→各输入草稿→切回→B改名503→刷新→A active时删B→新建空composer|草稿逐会话保留、拒绝改名回滚canonical、删B不抢A焦点/URL、不生成幽灵历史|P0|主链、异常、状态机|Root22827稳定editing定位后PASS；Root22564同case再次PASS。不覆盖rename200、首次模型发消息或Project scope。旧定位失败保留，不当业务RED|
|TC-UI-R188-002 / T-C04|旧Move合法回包结束busy|A→P真实POST held；可切B|发A Move→切B→释放合法ACK→检查动作/URL/列表|旧busy结束，B active/URL保持，不旧导航或列表刷新，单POST|P1|异步竞态、状态机|Root48623正确RED：全Move仍disabled10s。窄machine修复后Root22564 PASS，system580b/source d2357c20。不关闭post-confirm/pre-continuation既有AppFrame窄竞态|
|TC-UI-R188-003 / T-C04|旧Move未知结果保幂等身份|同A/B；owner socket-close故障可恢复|A Move→切B→断owner响应→原A菜单显式Retry→合法ACK|busy结束、unknown保原path/key/body，只有A可重试；B不抢焦点、无自动请求|P0|异常恢复、幂等、状态机|Root22827正确RED→Root22564 PASS；相同path/key/body与单一Retry已断言。不是丢未知命令后造新请求|
|TC-DB-R188-004 / T-B07|Agent attempt/evidence持久边界|Root独占临时PG、正式fresh installer、批准A1 R2|装canonical→验八态/知识/bytes/digest/时间/计数边界→改CHECK(TRUE)/删PK/index/列→verify拒绝|fresh严格通过，非法组合与catalog漂移被拒；自有资源收回|P0|数据契约、边界、异常|Root80705 43pass15fail：rawDDL/deparse误拒fresh。规范化定义修复后Root86926全部58pass4.85s，ownDBabsent/sourcehashsame。只schema/SQL边界；repository/Run producer/Billing/provider链仍未实现|
|TC-BFF-R188-005 / T-C05|Project DELETE与消息准入双锁序|同P的A/B canonical会话；具名自有PG advisory barrier|分别Message先、DELETE先；采精确PID锁边→释放→检查成员、正文、dispatch、取消、不可变事件、同键零改写|合法父锁串行、删除原子、非head不得伪造新queued head；无未处理拒绝|P0|并发、事务、生命周期|Root93713 180pass2fail：fixture漏projectRef/PID观测错误与迟绑rejection。修正后Root90911 181pass1fail；Root65921 spec明确非head错误oracle（0!=1）。加强两个seed head绑定+完整before/after events相等后，Root16750完整BFF真PG/Redis182pass0fail0skip45.28s；限定本地owner PASS。public DELETE/Storage dispatcher/关联task政策仍OPEN|

R188 Web完整工程Root81224 exit0：258contract、50architecture、lint/typecheck、164files2454pass/0fail/0skip149.25s与Next build。日志`/tmp/kokoro-r188-web-full-check-root.log` SHAe1a91e4d。工程通过不是所有页面/Settings/真实模型完成；当前运行副本未带Move，本轮零重启/零新永久服务，自有独立登录浏览器已关闭，0模型请求。

Root16750 Agent全部database邻门254pass/0fail29.64s（55条第三方弃用/Beta warnings保留），自DBabsent/sourcehashsame；独审schema/catalog0P0/P1/P2。Root本轮限定治理18项17pass1fail，历史w1e IAM checkpoint绑定旧owner gitlink，与现inventory不一致（189差项），保留OPEN，不弱化断言；先前一次误写不存在测试文件路径exit4/no tests不计执行通过。

Settings已实证的通知/快捷键切tab重置、Personalization404静默、Billing读503仍FAIL；所有未发布owner能力留待实现，不因隐藏/disabled算完成。BFF default optional project_ref的父锁及Run/project上下文一致性新缺口待D0/真实行为切片，不称同owner问题为已证越权。

## R187 当前页面与模块系统验收清单（2026-10-04）

此清单细化原70组，不另建测试计划或增加完成组数。**源码盘点不算执行、组件/Mock绿色不算业务通过、fixture BFF不算真实owner全链通过。** 原70组统计保持11通过/6失败/14待复测/38未验/0业务待决/1支付后置；以下子例逐项单独记录证据，整组必须全部必要子例满足才更新。

### 策略与范围

重点风险：①身份/项目/会话切换与迟到响应串数据；②loading、未知ACK、断线及取消错误收口；③按钮或内存值假装owner已保存、执行或收费。以普通用户与管理员、同团队不同人及跨tenant为权限维度，使用正式登录与同源adapter。默认个人私有；队列串行属于同会话约束，不阻止验证双窗口提交、其他会话并行及重复请求幂等。研发验收不扩展生产运维。

共同前置：冻结Web/BFF及目标owner commit、contract version/digest；正式测试账号与获授权资源；明确自有fixture数据与清理；不得清空共享PG/Redis。测试边界取当前owner契约的min/max，逐项测min−1/min/max/max+1及空/Unicode，不凭QA计划发明限制。每个页面都执行直接URL、导航进入、刷新、前进后退、键盘、窄屏、200%缩放、loading/empty/error/disabled/retry与迟到响应；缺入口、缺契约或未实现仍记缺口，不因隐藏标通过。

### 主链路与逐模块能力（以下“待验”不是成功）

|用例ID / 标题 / 归属原组|预置条件|测试步骤|预期结果|优先级 / 类型|当前状态及缺口|
|---|---|---|---|---|---|
|T-L01.R187 登录与工作区|正式IAM、固定tenant、无Product session|表单登录→callback→工作区→输入→刷新→退出→重登|一次正式认证回链；无可见连接/整页重试中转；正确主体、可编辑；退出不复活私有内容|P0 / 主链路、状态机|待当前完整组合复验；原用户loader仍OPEN|
|T-U01.R187 Home提示|已登录、无active会话|逐个点输入框下提示/More→编辑→清空；打开能力外链|仅填草稿，不自动发送或扣款；无模板变量、虚假营销或未配置连接成功|P1 / 功能、交互|待验；用户原展示问题未以静态修改关闭|
|T-U02.R187 Composer|独立与项目会话；可用模型|多行中文/IME→Enter与Shift+Enter→发送/Stop；附件取消；空文本操作|组合输入不误发；合法一次提交；清空/disabled/Stop按真实Run；没有内嵌方框/遮挡|P0 / 功能、边界、交互|待真实浏览器/截图与Run验证|
|T-C01.R187 会话列表|独立、项目P/Q、同时间分页数据|独立/P/Q逐个读→两页→刷新→切scope|归属与标题准确，无icon-only未命名幽灵行；不漏重、不把任务当会话|P0 / 功能、分页|后端历史限定证据；截图项目/空行当前待核|
|T-C02.R187 会话创建与打开|P/Q与独立入口、不同草稿|三个入口创建→首发→切换→后退/前进→硬刷新|canonical会话归属、URL、正文与草稿一致；切换不取消其他Run|P0 / 主链路、状态机|待两scope完整浏览器旅程|
|T-C03.R187 会话重命名/删除|本人active与nonactive会话、独立/P两scope|重命名确认/取消→刷新；删除确认/取消→ACK前后列表与正文检查|ACK前保原事实，失败可重试；ACK后仅目标改变，删除当前项安全导航，刷新不复活|P0 / CRUD、异常|待当前全部分支；不得凭本地删行通过|
|T-C05.R187 会话Move|本人P/Q与独立、active/非active|P→Q→独立；保持草稿与消息；验证菜单与刷新|confirmed才导航/更新；历史Run/正文不变；pending全局禁竞；unknown原行原key恢复|P0 / CRUD、状态机|Root39260 pending/unknown子例通过；拒绝提示文案匹配仍待核；非真实BFF终验|
|T-C05.R187 项目CRUD|本人项目、项目会话/文件、已批准删除政策|列表→创建→打开→改名→取消删除→确认删除→刷新|项目是独立资源；改名/删除owner ACK与GET一致；项目及所属会话/仅项目文件删除，已移出会话及独立资源保留|P0 / CRUD、生命周期|Project rename/delete正式UI消费缺失；linked task/active Run分支需owner闭环|
|T-P01.R187 独立任务|正式ScheduledTask/Scheduler；独立与P关联|列表→创建→改名/编辑→暂停/恢复→删除→刷新；查发生记录|任务独立于会话，关联P不改变资源身份；重复触发一次执行，状态来自owner|P0 / CRUD、主链路|待真实Scheduler/Agent组合|
|T-A01.R187 Agent过程/Todo|真实简单聊天与复杂工具Run|发送→queued/streaming→Todo更新→tool完成→终态→刷新|简单聊天不伪造计划；复杂Todo全值准确；友好摘要，无raw参数/隐藏推理；刷新同水位|P0 / 主链路、状态机|运行UI存在但当前全链待验|
|T-A02.R187 Skill实际加载|已安装授权Skill；真实Run|选能力→发送→resolving/loading/ready或failed→刷新|安装/选中不冒加载；执行记录绑定实际版本，失败可解释且不假ready|P0 / 主链路、异常|待Platform→Agent→BFF→Web整链|
|T-A04.R187 审批与继续|多项未决HITL、合法与其他用户|完整决策→一次resume→重复/旧决策→刷新与重连|同thread全部未决项处理；合法继续一次；旧/越权拒绝；ACK不冒Run完成|P0 / 权限、状态机|待真实HITL用户旅程|
|T-F01/F02.R187 文件与Library|真实Storage/scanner；本人、P与其他人文件|上传→扫描→列表/分页→预览/下载hash→刷新→取消/删除|真实字节/hash/状态一致；过期或恶意文件拒绝；跨人/项目隔离|P0 / CRUD、安全、主链路|外部存储/扫描整链待验|
|T-F03.R187 作品|真实Agent生成并经Storage提交作品|运行→交付卡→预览→下载→刷新；重复事件|一份权威作品、一张卡；hash一致，失败不生成假作品|P0 / 主链路、幂等|待真实资源链，不用fixture卡通过|
|T-C04.R187 分享|本人私有会话、获授权显式分享、另一用户|创建分享→另context读→撤销→旧URL再读|默认私有；公开链接范围明确；撤销后无继续读取/控制|P0 / 功能、安全|待当前真实owner全旅程|
|T-U04.R187 Settings壳|正式登录、13 tabs与深链|账户打开→逐tab→More/搜索→nested dialog→Esc→重开/刷新|tab/URL一致，焦点返回、无遮挡、晚响应不写新tab；未知tab安全归一|P1 / 导航、无障碍、状态机|库存完成，实际浏览器待验|
|T-U04.R187 外观与通知|Appearance正式入口、localStorage可用/拒写|语言/主题三态→关闭→重开→刷新；四通知开关同流程|语言/主题按Web真实偏好恢复；通知若承诺保存必须持久化，不假保存|P1 / 功能、边界|语言/主题有实现；四通知仅内存，缺持久化|
|T-L03.R187 Account|普通用户正式Product session|查看身份→升级链接→退出→后退/刷新；退出失败重试|身份由可信owner投影；未实现写动作诚实禁用；退出后私有数据零残留|P0 / 权限、状态机|身份字段占位，资料写未闭环；退出当前复验待执行|
|T-U04.R187 快捷键|Settings shortcuts与工作区|五项录制/冲突/Esc/reset→关闭→重开→工作区触发→刷新|不截获IME/系统保留键；承诺保存则持久并真实执行|P1 / 功能、交互|目前仅组件内存、无全局注册；未完成|
|T-S02.R187 聊天默认模型/Agent|有效、失效候选；新旧会话|选择→关闭→新建→核首条wire→刷新→Follow profile；旧会话对照|新会话消费真实选择，旧会话不改写；失效/503可见错误，不假保存|P1 / 功能、状态机|候选读失败降空无Retry，需修；真正发送待验|
|T-U04.R187 个性化|正式Personalization、已发布owner写/读契约|编辑blur→owner ACK→重开/刷新；知识添加/编辑/删除与导入|只有成功响应才宣称保存；GET恢复；失败保输入且可重试|P1 / CRUD、异常|缺canonical操作与GET，PATCH未检查response.ok；未完成|
|T-S01.R187 Computer/部署|正式Computer/Deployment；无真钱动作|方案/slider→确认取消；Website/App目标；Domains升级取消|无契约不冒创建成功；取消零资源/扣费；无callback明确不可用|P1 / 功能、边界|Cloud创建契约/错误反馈缺失；Deployment入口未等于生命周期闭环|
|T-A02.R187 Skills页/设置|本人ACTIVE安装、正式Platform/Storage|列表/详情/分页→合法ZIP发布→ACK→刷新；坏ZIP/scan失败|本人权威安装、固定版本；unknown同key恢复；无preview假写控件|P0 / 主链路、异常、安全|静态正式read存在；当前真实ZIP/发布闭环待验|
|T-A03.R187 MCP/连接器|正式Platform MCP投影；连接供应商许可|MCP列表/分页/详情/错误Retry；连接→正式callback→重开→断开|MCP正式只读不泄secret/URL；connected必须owner读取确认，连接/断开有真实事实|P0 / 安全、主链路|MCP正式read待验；Slack/Telegram/LINE无正式操作/读回，缺URL可假connected|
|T-L05.R187 Team|普通成员与管理员；邀请/成员测试对象|普通人读/拒写；管理员邀请/取消/重发、改角色/移除、最后管理员、leave；刷新|无提权，成功后权威refetch；409需刷新；自退出清私有scope；命令幂等|P0 / 权限、CRUD、状态机|正式client存在，当前真实双身份旅程待验|
|T-B03/B05.R187 积分与流水|Billing授权赠送及真实账本；冻结7/5定价revision|授权赠送→余额/流水→两页过滤→刷新→一次模型执行前后比对|前端只显示owner金额；赠送可追溯；一次费用唯一流水，倍率/舍入由Billing决定|P0 / 主链路、财务|当前summary503仍OPEN；不得改DB假充值/免费|
|T-B04/B06/B07.R187 正式费用|正式逐attempt admission/evidence/receipt、真实provider|预占→执行→已核用量结算；失败/取消→仅核实消耗结算→其余确认释放；unknown核对|调用前许可；重复不重扣；unknown不补0、不按Run终态结案|P0 / 状态机、异常、幂等|Agent runtime接线与Billing已发布逐attempt操作缺失，P0未闭环|
|T-B08.R187 Subscription/支付|真实plan目录；未配置渠道正控|目录/错误Retry→双击checkout→401/未配置；返回/刷新|未配置诚实禁用；HTTPS合法跳转；不伪造订单或支付成功|P1 / 功能、异常|目录/错误可验；真实渠道最后，未执行真钱|
|T-U04.R187 Help/Agents入口|正式路由与能力声明|导航/直接URL→正常/404/503→重试/返回|无可用能力需诚实说明；模型与Agent清单来自owner，无credential泄露|P1 / 功能、异常|Help未实现；当前agents404，待owner定位|

### 边界值、异常、安全与状态机专项（应用到上表每个可操作模块）

|用例ID / 标题 / 归属原组|预置条件|测试步骤|预期结果|优先级 / 类型|当前状态|
|---|---|---|---|---|---|
|T-R03.R187-B 名称/输入/分页边界|每owner当前schema限制、合法正控|空/空白/Unicode/超长；limit min/max越界；金额0/大值；不合法cursor|稳定错误、输入保留；不截断假成功、不溢出/漏重，不把合法空态当错误|P1 / 边界|各页面逐项待验，不以通用表算覆盖完成|
|T-U04.R187-E 网络/解析故障|可控浏览器HTTP边界与owner正控|依次headers/body pending、断网、坏JSON、401/403/404/409/429/503→显式恢复|既有期限内收口；私有数据failclosed；保草稿/已读部分，零假成功；Retry有界|P0 / 异常|Root39260 snapshot故障子例通过；其他模块未验|
|T-L04.R187-S 私有与管理员隔离|同tenant A/B、跨tenant C；各自项目/会话/文件|改ID/深链/直接mutation/旧cursor/撤权后续流；普通人触发管理员操作|统一拒绝、零非法写；默认个人私有，显式分享之外不可读；无secret/raw tool data|P0 / 权限、安全|每资源与操作待完整组合验证|
|T-C07/R03.R187-S 重复与未知ACK|真实owner幂等契约、两窗口|双击/同key同body重放/异body冲突；响应丢失同key查询恢复|一命令一事实；未知不换key重复执行；同会话FIFO单head，其他会话独立|P0 / 幂等、竞态|后端局部证据；浏览器全用户旅程待验|
|T-C02/C09/A05.R187-T 切换与恢复|A/B会话、P/Q与active Run、合法水位|输入立刻硬刷新；快速切换；旧请求晚到；各Todo/Skill/tool/审批/作品时点刷新|草稿exact key保留；旧generation零写；不重复正文/卡片；权威水位续接、状态有界|P0 / 状态机、竞态|Root39260草稿/snapshot子例通过；五时点真实Run待验|
|T-U03/U04.R187-A 视觉与可访问性|桌面/窄屏、200%缩放、reduced motion|逐页面截图、键盘与读屏、菜单/弹窗焦点、长代码/表格/部分错误|无指针覆盖/截断/方框；focus-visible、正常滚动，loading/error状态可读|P1 / UX、无障碍|逐页截图/axe/视觉回归待验|

### 执行与退出标准

执行记录绑定上述ID，包含commit/pin、角色、步骤、真实预期与实际、PASS/FAIL/BLOCKED/NOT_RUN、脱敏日志/截图及自有资源清理。先正确失败证据，再最小修复，再相同路径与邻接回归；准备错误不算业务RED，观察超时不算进程终止。正式owner组合与真实provider路径必须另验，不把fixture或纯门挪作证据。

研发可交付：当前范围P0/P1为0开放缺陷；全部必要主链路与权限/失败恢复PASS；各页面CRUD/API与权威刷新一致；正式用量、余额、预占、结算/释放和流水闭合；已批准删除与取消政策被真实验证；当前commit工程门、完整系统矩阵、无障碍/视觉/bundle门有实际结果且无未解释skip。后置支付明确排除真实渠道验收，不声称商业支付可上线。未实现能力及缺owner契约必须逐项保留阻塞/后续owner，不能靠隐藏或宣称“已完成”达退出门。

R187最终工程复验：旧英文filter纠正后Root48115同三system3pass/61名称过滤37.05s；撤回无证据layout-effect修改，所有业务断言/期限不变。Root32229 Node22完整check自然exit0：258contract、50architecture、lint/types、164files2450pass0fail0skip143.09s、Next build0。日志`/tmp/kokoro-r187-web-full-check.log` SHA16b8da1b。仅工程门和该故障子链通过；既有confirmed Move视图副作用风险尚需晚响应测试，不标全部Move通过。

### R187 当前真实运行组合的实际页面验收

基线原3310当前IAM/BFF/System、Web main9b42的运行副本；Root先逐字核三运行文件等于HEAD，精确备份后仅同步snapshot函数及10s常量、helper与草稿pagehide。运行adapter SHA98358d65（没有混入Move），helper f1ce8201、draft4d2e75c7；备份manifest `/var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-r187-runtime-backup-828qjs5z/manifest.json`。未重启/清数据/改model；自有独立Chromium+context最终已关闭，未新建IAB页。

|用例ID / 标题|前置条件|实际步骤|预期|优先级 / 类型|结果/证据|
|---|---|---|---|---|---|
|T-L01.R187-REAL / 正式登录|当前真实owner、本地授权验收帐号|表单CSRF submit→固定tenant→callback→app|正确正式回链、工作区可编辑|P0 / 主链路|PASS限定正向；真实303/302/303/callback303；首帧disabled仅booting，后续实际enabled，不把瞬时pending当永久失败|
|T-C05.R187-REAL-P / 用户截图项目空间|相同帐号与project93b2011d，不写业务数据|真实URL→等待owner list→核标题/行数/输入/截图|canonical名称/项目scope、无幽灵空会话行|P0 / 功能|settled名称“新建专案 5251c78c”、0canonical会话行、输入enabled，截图`/tmp/kokoro-r187-current-project.png` SHA992bc7c4；resources503独立FAIL。初读“Project unavailable”为尚未settled，不计错误根因；不是原IAB旧截图原因证明|
|T-U04.R187-REAL-TABS / 全设置库存|正式cookie，Settings实际modal|通过账户菜单进入→逐个tab→核控件与disabled|全部模块可达或诚实禁用，非preview|P1 / 导航|13可交互+1disabled Help实际核查；只证明入口/控件库存，不证明每模块读取/CRUD成功|
|T-U04.R187-REAL-N / 通知不保存|General Browser notifications=false|click变true→Shortcuts→General|若设置已生效，切tab保留|P1 / 状态机|FAIL：false→true→false，真实重置；未触发浏览器权限或owner写|
|T-U04.R187-REAL-K / 快捷键不保存|New task初值⌘⇧O|Clear→General→Shortcuts|显式清除应保存，不复活旧键|P1 / 状态机|FAIL：初值→Not set→原⌘⇧O；非真实全局注册验证|
|T-U04.R187-REAL-PREF / 个性化假保存|正式Nickname为空、真实adapter|填QA marker→blur→观察响应→切tab重开|错误可见/输入保留；成功需GET恢复|P1 / 异常、CRUD|FAIL：PATCH404、0可见alert、留内存marker、重开为空。marker未写owner；明确不是保存成功|
|T-B03.R187-REAL-READ / 积分读失败|正式cookie、Billing未闭合|Credits→等待真实summary/by-model/ledger响应与UI|权威账本可读；失败有恢复入口|P0 / 主链路、异常|业务FAIL：三503；UI实际2alert与Reload，不误称无Retry（旧英文locator“Retry”不匹配实际“Reload”，属测试oracle问题）|
|T-U04.R187-REAL-SNAPSHOT / 真实owner挂起恢复|重新正式登录且session authenticated=true；原conv_ffd7两真实message-scroller items|输入后立即hardreload，hold exact首snapshot→10s error→显式Retry→释放旧route→reload→全文/草稿对比→清测试草稿|不永久loader；真实正文/草稿不丢，不采纳旧请求覆盖|P0 / 异常、状态机|PASS限定链：10.236s error，Retry正文逐字同原，hardreload两消息逐字同原/草稿保存，0模型发送；截图`/tmp/kokoro-r187-real-owner-recovery.png` SHA9c008052。独立context，不关闭原IAB T-U04|

实测证据 `/tmp/kokoro-r187-real-page-qa.json` SHA8275438c。首次driver将仅助手`data-slot=message`误当全部消息，1而非2（实际scroller items=2）；属于定位前置错误。另第一次故障旅程Retry前session已authenticated=false、请求401，未计恢复成功，重新正规登录后同完整路径才通过；不据此猜TTL或刷新根因。页面HTTP/库存已据实更新，所有其它未执行分支保留待验。Agent Root95067另仅真实schema合同2fail1pass0.40s，自库回收与源hash保持，不计T-B运行费用通过。

## R186 / T-U04 首次历史读取永久 pending：当前系统验收（2026-10-04）

|用例 ID / 标题|预置条件|测试步骤|预期结果|优先级 / 类型|实际结果 / 状态|
|---|---|---|---|---|---|
|T-U04-R186-SNAPSHOT / 历史网络挂起有界收敛|真实Next/Redis Product Session/Chromium、fixture BFF会话A，正常权威正文及真实草稿已成功|只hold浏览器exact snapshot→reload A→确认请求started/BFF计数不增→等待error→显式Retry第二GET→权威正文/草稿→释放旧请求→再reload|一次10s总读取预算涵盖全部分页；不永久loading、不采纳partial；手动Retry恢复，草稿保存，旧请求无写权|P0 / 异常、状态机、主链路|Root1934，test b15ee2e2：1fail/63名称过滤33.10s，失败明确为12s未出现error。正确业务RED→Root52521 GREEN 1pass/63过滤32.36s，重试/正文/草稿/reload/旧响应隔离全过；完整门与原runtime/用户同页待验。不是原IAB因果证明|
|T-U04-R186-ORIGINAL / 用户当前标签|原3310/conv_ffd7，保cookie/正文，不新开标签|读取原标签闭集DOM与错误/网络阶段|当前原会话正文和编辑区可见，非永久loader|P0 / 用户验收|DOM命令dispatch前4s失败，事件读取8s未返回；原页面恢复未证明，FAIL/OPEN|

首测试25591 composer前置错误（loading阶段查不存在的composer，30s失败）已保留日志但不计为业务RED。公共匿名HTTP仅证明正式IAM路径响应；R184新Chromium真实当前组合正常旅程不冒原标签恢复。全70组状态不变，完整Wave0–7目标不变。

## R180 / T-U04 原会话持续加载：当前系统验收记录

原70组统计不变。原用户首屏仍失败/开放，不以同步、构建或其它fixture关闭。

|用例ID/标题|预置条件|测试步骤|预期结果|优先级/类型|实际结果|
|---|---|---|---|---|---|
|T-U04-R180-CURRENT / 当前可见原标签|原3310、原帐号与conv_ffd7，不清cookie/聊天|读取selected标签→DOM→原标签reload→正文/编辑区|不是永久loading；正文与输入可用|P0 / 主链路、状态机|selected=tab1；DOM4s超时，reload15s超时；未证明刷新或恢复，FAIL/OPEN|
|T-U04-R180-ANON / 真实匿名登录链|同一运行服务，无cookie独立请求|GET session→GET原app，核follow redirect最终HTML|匿名进入正式IAM表单，不假授权工作区|P0 / 权限、主链路|session22ms200 anonymous；app132ms最终正式IAM表单；仅HTTP匿名链，不证明原用户UI|
|T-U04-R179-CANDIDATE / 已审认证开发候选|冻结3source、原运行副本精确旧hash|备份→同步→新旧hash验证；独立build；完整check|准确记录范围及真实失败，不混入其它dirty|P1 / 回归、配置|三hash一致、build0；完整check2435pass10fail，均R170 Move待实施。未发布/不关闭原用户FAIL|
|T-U04-R177-HANDOFF / 无可见重试中转|真实Next/Chromium、正规认证fixture与受控HTTP故障|hold匿名native→零业务safe shell→release原请求→真实302/302/303→新app/reload/输入|零owner泄露、一次login、正式回链、输入启用；不复活整页Retry|P0 / 异常、安全、状态机|Root50681严格1pass34.19s；旧R165不合新PRD oracle已正式退役，历史失败保留。不是原3310用户页面|

R176补充：T-U04因果对照在原生pending导航下观察通道超时但纯HTML heartbeat继续，原R165仍红/原IAB恢复未证；Storage producer发布14f2/BFF consumer8e33已固定门验证，只解除contract前置，不代表T-C05本地删除/worker或T-F03外部资源/全链已通过。完整70组状态保持。

R175 T-U04补充（非整体验收）：serverAdmitted→focus anonymous真实RED1fail已得到，AppGate匿名无整页loader修复后Root86705 Node22六相关真实Next/Chromium病例通过（R175+R147/R150），auth15/lint/types/build0；已窄同步原3310。原25实际DOM读取仍14s超时，用户原页恢复未证；原R165保留，完整60矩阵31815实际59pass/1fail/98.16s，唯一R165恢复门失败，不改70组整体状态。

R174最终系统复验：Root27115 58pass/1fail/59、96.51s，test ca327877，日志 /tmp/kokoro-r174-root-auth-state-matrix-final.log。R150偏好、pending与503正式恢复通过；唯一R165 native登录跳转在途恢复失败，12s closedDOM unavailable，无alert真实证明。原24原因未定，T-U04整体失败/开放，不能凭新25或58个fixture节点关闭。Redis15回收0。

## R174 / T-U04 原会话当前用户验证（2026-10-03）

同组增补，不改变原70组总体状态。原旧标签未取得恢复证据，整组保持开放。

|用例ID/标题|预置条件|步骤|预期|优先级/类型|实际结果|
|---|---|---|---|---|---|
|T-U04-R174-COLD / 同一真实用户原会话冷开|原3310、browser3原登录状态、conv_ffd7；无清cookie/数据库、无重启|旧24读DOM/截图超时后，同browser仅新建一临时25打开原会话|真实历史与编辑区可用，不永久整页loading|P0 / 用户·主链路·状态机|25真实旧两条历史可见、输入启用；浏览器error/warn记录为空；首次booting仅禁用实际Composer，下一读取Runtime已接管|
|T-U04-R174-INPUT / 原会话输入|同25，正常ready|填写“输入交互检查，不提交”→查发送启用→清空|编辑可用、发送按内容启用；不创建新消息或扣款|P0 / 用户·交互|通过，发送isEnabled=true；无提交|
|T-U04-R174-RELOAD / 原会话刷新|同25原真实登录|reload→booting→读取Runtime/原两条历史/启用输入|刷新有界完成、历史不丢、编辑可用|P0 / 用户·生命周期|通过；截图 /tmp/kokoro-r174-original-conversation-restored.jpg，SHA938fe6f035543adcccf3aaab267f6a3cf1d7bc822173351b8dcc91627276ff3d|
|T-U04-R174-STALE / 旧标签恢复及清理|原24以及重复21–23|24 DOM读取、截图、close各有限尝试|有现场恢复/成功关闭证据，故障根因可解释|P0 / 异常·恢复|DOM焦点准备14s超时、截图15s超时、close15s超时；未声称已关闭/原旧页已修，保持开放|

R173五source与受管runtime本轮逐字SHA相同，原45606/46036运行不变。新25标记deliverable以保留可用入口；新文档成功不证明旧文档失响应原因或所有故障已根治。Root完整59节点Next系统故障矩阵本轮已启动，最终结果另记录。

## R173 / T-U04 首屏状态机当前证据（2026-10-03）

不增加原70验收组，不将独立fixture冒充原用户页面；T-U04整体仍未验收。

|用例 ID / 标题|预置条件|测试步骤|预期结果|优先级 / 类型|本轮结果|
|---|---|---|---|---|---|
|T-U04-R173-SSR / 脚本未启动时真实首屏|真实Next/Redis，正规签名Product cookie；IAM/BFF严格HTTP fixture|GET /app核HTML；同cookie Chromium关闭JavaScript打开/app|200；实际main/Composer可见且禁用；两种整页loader均不存在；不授予客户端身份|P0 / 系统·边界·安全|Root81387通过；属于独立fixture，不是3310原用户页|
|T-U04-R173-PENDING / 首probe未回时零业务挂载|同fixture与受控HTTP proxy|hold首次session probe；观察实际main/禁用Composer；8次focus；release可信200|pending期间会话/model/agent等 /api/session/* 与live manifest请求0；heartbeat继续、仅一个probe；release后booting消失、Runtime/编辑区接管|P0 / 系统·竞态·状态机|Root81387通过；原12s预算、focus与响应断言保留|
|T-U04-R173-READY / 冷启与刷新可编辑|同fixture正规认证|cold /app→真probe完成→输入文字并清空→reload再次执行|每stage12s内booting卸载、编辑区启用；本阶段至少一个session请求、所有响应200且等数；输入可编辑|P0 / 系统·主链路·生命周期|Root81387通过；不以SSR可见替代真实ready|
|T-U04-R173-USER / 原右侧会话|原3310、conv_ffd7、原tab24；服务45606/46036不变|限定同步经审查5source→尝试刷新原页→读取真实正文/输入与再刷新|原用户同页历史与编辑器可用；有界失败恢复|P0 / 用户端到端|原页reload/读取20s超时，未取得新DOM，保持失败/开放；无新增tab/清数据|

来源：`/tmp/kokoro-r173-root-final-convergence.log`，2pass/57名称过滤/23.09s；过滤不是测试通过。13个auth邻门、定向lint/typecheck/build当前通过；完整59 HTTP故障矩阵/全Web门/原IAM+BFF+真实模型+积分旅程未在本轮执行，不声明整体闭环。前序fixture错误与ready语义纠正记录于同progress。独审当前0P0/0P1，仅此五文件。

## R153 T-U04 原用户页面与实际启动器复验

本增补沿原70组编号，不改变任何总组状态。

| 用例/标题 | 前置与步骤 | 预期 | 优先级/类型 | 当前结果 |
|---|---|---|---|---|
| T-U04/R153 原会话首屏 | 原帐号、conv_ffd7、tab21；读DOM/错误并刷新原标签，不清Cookie或改帐号；验证正文、输入与reload | 有界离开loader，正文和输入可操作；明确故障不永久等待 | P0/主链路、异常、状态机 | DOM/错误/刷新均focus超时，事件读取也超时；无用户证据，仍FAIL/根因未定 |
| T-U04/R153 启动器单变量 | 同正式Product Session HTTP与Next/Chromium fixture；固定同R147 cold/reload oracle，webpack和programmatic两启动器分别跑 | 每导航12s内工作台、session200、输入填入清空；所有旧assert保持 | P0/主链路、边界、恢复 | Root38725与43049分别1pass、各52名称过滤；21.98s/7.07s。非原用户页面 |
| T-U04/R153 programmatic系统矩阵 | 同当前运行方式的隔离Next；完整53现OIDC/刷新/异常/拒写/正文/删除ACK节点 | 所有断言保持、资源只回收自有 | P0/系统、异常、安全、状态机 | Root21527 53pass/0skip55.45s；Redis15恢复0、自有目录0。旧signout500未复现，根因仍unknown；全产品E2E不由此替代 |

退出标准：原帐号原页面实际正文/输入/reload验证通过，且永久loader故障有可复现原因及修复证据；其他fixture或公共200不满足原页退出门。

## R151 / 系统验收矩阵与已发布限定切片（2026-10-03）

Root本轮全仓标准门真实exit1：153项规范违规/0未核实，不能称全仓合规。新发现本切片引入的BFF chat-repository.ts增长671→979行，越800行门，列R152具体架构P1；不将153项一概称历史。Root治理298pass3.06s。拓扑初验因两个已发布owner未更新Root index而2项失败；Root精确stage Web65be18a/BFF0333两gitlink后复验exit0/PASS（9个运行模块），没有改检查器或其他gitlink。剩余标准债务仍按原owner波次收敛，不修改检查器/阈值放绿。

沿用原70组及编号；原组状态仍11通过/6失败/14待复测/38未验/0业务待决/1支付后置，不凭限定切片转整组通过。

| 用例ID/标题 | 预置条件及行为步骤 | 预期结果 | 优先级/类型 | 当前实际结果 |
|---|---|---|---|---|
| T-U04 原用户初始化 | 原3310/conv_ffd7/tab21；刷新原页、检查在线session和正文/输入、再次刷新 | 有界进入可操作工作区，失败显式可恢复，不永久占位 | P0 / 主链路、状态机 | 仍缺同页DOM/API证据；控制focus超时，用户刷新反馈未得。保持失败，不由下面fixture代替 |
| T-U04 偏好存储读写被拒 | 真实Next/Chromium已认证fixture；分别拒theme/locale、通过Settings切换，再reload | 正文和输入可操作，显式切换保内存；reload保原系统/协商默认，不抛页面异常 | P0 / 边界、异常、状态机 | Root3真实RED→3GREEN；最终完整53system0skip80.69s、2360工程0skip105.83s；source65be18a发布。仅此缺陷通过，不绑定原页因果 |
| T-U04 全localStorage被拒 | 同fixture全部Storage访问抛错，真实在线session返回认证结果 | 认证索引failclosed，有明确可恢复alert，无私有工作区/无限loading | P0 / 安全、异常 | 最终53中的正式节点通过；未放宽认证守卫 |
| T-U04 pending刷新期间退出 | 正规Productcookie、真实Next+Redis及严格IAM/BFF边界；保持刷新在途后单次signout | tombstone阻止晚凭据恢复，不用stale凭据revoke，HTTP200 | P0 / 竞态、生命周期 | 本轮53与2360中均过，但R150真实500/Next JSON.parse来源未知仍开放；新有限脱敏诊断仅取证，不冒根治 |
| T-C05 Move完整producer | 真HTTP/PG/Redis新自有库；本人Project↔外部归属、samekey重放/异义、撤权、交错Message、COMMIT断socket | 同事务归属+唯一receipt；当前IAM重验；历史Run/Message/Share/AGUI不变；未知COMMIT丢坏连接并同key恢复 | P0 / 主链路、安全、异常、竞态 | 正式九焦点9pass14.051s＋八文件173pass0skip37.305s，源码284b/docs0333发布；Web消费者/DELETE仍未验 |

退出标准仍要求原用户实际登录→工作区→输入发送→流终态→刷新稳定及正式积分/权限/项目等完整旅程；当前未达到整体退出门。RootCURRENT记最终commit、命令与其他owner开放项。

## R150 / 系统验收结果与仍失败的原用户页面（2026-10-03）

用户原 conv_ffd7 / tab21 的永久“正在加载工作区”仍未验收。本次原页控制再次在 Emulation.setFocusEmulationEnabled 超时（31.68s），未取得该用户 DOM/session/hydration 时间线；没有重启原32044组合、创建新页或重置数据。已明确请求用户只刷新原页一次并反馈，不把公共200或其他fixture通过当作恢复。

已复现并修复的独立缺陷：Locale/Theme Provider 同步读取偏好存储抛出 SecurityError 会中断客户端初始化；Root32448三个真实Next/Chromium系统用例3fail，最小两源修后Root18955同三用例3pass/23.90s。读失败保原语言协商/系统主题，本次切换保内存override；认证索引仍fail-closed。两源SHA a114ef30/0532b66b已同步原runtime copy，无进程或登录数据重建；实际公开Turbopack chunk b64fb212含两处try/catch（/tmp/kokoro-r150-runtime-provider-served-guards.json）。仅证明代码已服务，不证明原页面触发此原因。

Web早版完整门Root45587为164files/2360pass/0skip，contract256/architecture50/lint/types/build0；增强真实Settings setter后Root41843为2358pass/2新增fixture fail，原因是reload已恢复Settings overlay却再次点击其背后账户按钮。只修两测试交互，最终4517f6cb冻结。Root72301最新完整pnpm check exit1：164files中163pass/1fail、2359pass/1fail/0skip、111.32s；53系统52pass/1历史pending-refresh signout500（Next内部JSON.parse Unexpected end、五manifest前后均有效，来源仍unknown），新增Storage三项含setter全过；contract256/architecture50/lint/types通过，build因测试失败未到。未重复跑凑绿、不发布；诊断方案续派原Web负责人只读。独立增量审3d01f379绑定当前Web三SHA和BFF两SHA，0P0/P1/P2。

BFF真实未知COMMIT连接缺陷：Root64310真实COMMIT后断socket，release实际false而非true，反例失败；最小source219c2268在committing异常时销毁lease。Root43114最终九项真HTTP/PG9pass/0skip/14.051s；ownedDB absent、源hash不变、Redis key集合相同。原完整172 integration是修改前证据，不冒当前全门或消费者闭环；BFF Move当前候选尚未发布；Project DELETE消费闭环仍开放。Storage R150新增仅三设计文档候选（既有在途代码保留），未授权schema/index/source改动，物理S3未验。

原70组仍11通过/6失败/14待复测/38未验/0待业务决策/1支付后置；原suffix831a2160、uv.lock f7e1c30d与任务外Billing候选保持。Wave0–7 goal不缩小；原用户首屏为当前关键路径。

## R149 / 系统测试执行与未关闭的用户首屏（2026-10-03）

Root R149治理门：`python3 -m pytest scripts/tests/test_repository_topology.py scripts/tests/test_ten_repository_standard.py -q` 原67150自然exit0、298pass/3.11s，日志`/tmp/kokoro-r149-ledger-governance.log`；仅Root工具/台账门，不关闭当前用户加载、signout根因或业务旅程。

本增补属于原70组，不新建计划中心、不改变编号/汇总。状态仍11通过/6失败/14待复测/38未验/0业务待决/1支付后置。

| 用例ID/标题 | 预置条件与测试步骤 | 预期结果 | 优先级/测试类型 | 实际执行结果 |
|---|---|---|---|---|
| T-U04/R149 原用户工作区加载 | 现3310及用户原conv_ffd7/tab21；读取原页、核同源脚本/CSP及runtime source，用户原页刷新后取session/hydration时间线 | 有界进入正文与可操作输入框；明确失败可恢复，不永久空壳；以同用户同页证据判定 | P0 / 主链路、异常、状态机、系统交互 | 读取20s超时，未得用户DOM/session/heartbeat。public45JS200、CSP56nonce匹配、7copy源相同只排局部。仍失败/根因未定，用户刷新反馈未得 |
| T-U04/R149 认证cold/reload及安全诊断 | 真实Next/Chromium/Redis独占origin fixture、严格IAM/BFF HTTP doubles；执行49系统行为，包括登录、cold/reload12s、pending refresh退出与synthetic onRequestError | 正式断言保持；超时/故障诊断有限且不泄露；不将fixture当真实所有owner | P0 / 主链路、边界、异常、状态机 | 初49=48pass/1新fixture隐私失败；修fixture不弱断言，精确2pass/47filtered；最终Root57758 49pass/0skip74.89s，e6770ec1 hash相同、独立0。生产未修，历史signout500/用户页不关闭 |
| T-C05/R149 Message↔Move和同key并发 | 真BFF HTTP+fresh owner PG；精确source Project与Conversation锁链控制双顺序；两同key请求通过真实传递阻塞链重放 | 下一admission新Project；两200同body、唯一receipt；历史Message/Run/AG-UI/Share不改；IAM逐请求 | P0 / 主链路、竞态、状态机 | 漏选filter只6；完整初8=7pass1fixture等待图失败；修观测后Root34202 8pass/0skip13.903s。manifest eq4wf02v DBabsent/hashsame/Rediskeys同，独立0；Delete/消费者及整体组仍未验 |
| T-C05/R149 Storage跨key读谓词 | PG18.4 fresh正式安装，120k合法owner facts+ANALYZE；8 hit/miss自然plan；两个不同key执行原helper raw Serializable→生产wrapper→精确cleanup | 区分索引访问、SSI锁、冲突分类、实际callback重进；成功只说明本诊断，不降低隔离/加retry掩盖 | P0 / 边界、并发、异常恢复 | 两seed fixture错保留非产品RED。Root36594最终exit0/源same/DBabsent；Upload IndexScan170/167blocks，另三Seq；四处relation SIReadLock，raw1 classified冲突（PrismaCode null），wrapperA2/B1新xid两commit。原全门漏P2034唯一因果/索引根治仍未证 |

退出门：T-U04必须原用户同页实际登录/工作区正文/输入/刷新均可操作且loading有界；诊断自测、fixture49及public资源200都不满足该门。BFF/Storage维持原owner发布、消费者pin和完整用户旅程门，Billing正式费用与S3物理终态另待验。

### R148 T-F03 补充执行证据（不变更原组状态）

原全门意图串行但argv双--未生效，真实并行698/1证据保留。修仓外验证argv后Root16615在新自有PG执行原filters、原全部assert：63focused＋73file699pass/0skip/43.69s、installer/drift/contract/format/lint/type/build0，hash相同/自有库absent。只关闭串行owner工程门；此前并行P2034、全球objectKey谓词访问路径/真实attempt及物理S3仍未验，T-F03不据此转整体通过。Web/User原页故障不受影响。

## R148 系统级测试执行矩阵增补（2026-10-03）

同原70组不新增/重排编号；以下是既有组的执行证据，不用pure数量替代用户闭环。

| 用例ID/标题 | 预置条件与自然语言步骤 | 预期结果 | 优先级/类型 | 当前实际状态 |
|---|---|---|---|---|
| T-U04 / 原用户页面无限loading | 原3310、原conv_ffd7及tab21；加载→读取页面状态；复查恢复tab22 | 有界完成正文与输入框渲染，失败不永久加载，当前用户页有真实证据 | P0 / 功能、异常、生命周期 | 未解决；用户截图RED；本轮tab22 DOM与截图控制超时，无新UI证明，待用户刷新结果 |
| T-U04 / 正规cold与reload | 真Next/Chromium、Product cookie、strict HTTP owner fixture；匿名SSR仅编译准备→新context cold→reload，各12s内分别session200/正文/composer→填写/清空 | 每阶段独立成功，旧session计数不替代当前阶段，异常有界 | P0 / 主链路、状态机 | Root98722当前full中此case过，但完整2355仍一signout失败；非真实全owner用户路径通过 |
| T-Q03 / signout与pending refresh | 正规登录cookie→阻塞refresh→发signout→解除refresh→查tombstone及revoke | 退出200、不将stale credential revoke，迟到refresh不复活会话 | P0 / 异常、权限、竞态 | Root98722真实Next500 JSON失败；52211a7 collector修正后Root94352单case1过/47名称过滤，间歇根因未关 |
| T-C05 / Move未知COMMIT与事务回滚 | 自有PG正式HTTP Move；COMMIT已落库后fixture丢ACK；原key重放；独立SQL trigger fault再移除恢复 | 未知503可恢复，事实/receipt唯一；SQL失败零partial写入 | P0 / 异常、状态机、幂等 | Root99373现6通过0skip；非socket故障，Move-message/DELETE/Run交错待验 |
| T-F03 / cleanup身份与锁顺序 | 自有PG/Connect，既有cleanup key/version/etag/notBefore损坏；Create/Complete与Release自有PID/key barrier竞争 | 损坏metadata全业务rollback；scope先于key，无跨scope/tenant物理误删除 | P0 / 安全、边界、异常 | Root44750 55pass8fail→46216相同63全过；实际S3物理删除/全部崩溃矩阵未验 |
| T-F03 / 完成上传重放和canonical竞争 | 同owner正规completed replay；旧canonical A观察后winner B提交；健康/不可用winner再观察、不同MIME共享同ownerBlob | 正规replay不被新key拒；stale走已有重观察而非foreign；跨owner禁止 | P0 / 主链路、状态机、竞态 | Root28791相同完整699中这些case当前通过；原并行门698pass1fail，后继串行699通过见顶端；并行feature-state另一路Complete P2034待定位，不冒全仓通过 |

退出门：当前用户原页可用＋正规登录/刷新/退出完整旅程当前commit通过；Storage完整owner零失败且canonical/key/fence恢复矩阵证实；BFF producer发布与消费者正式pin、Move/delete完整交错验证后才关闭对应组。当前均尚有未满足项，正式Billing和其他能力另按原任务继续。

## R147 / T-U04 首屏加载执行记录（2026-10-03）

原70组/编号不变，T-U04不因新页或fixture通过而转绿。

| 用例 | 预置与操作 | 预期结果 | 优先级/类型 | 本次实际结果 |
|---|---|---|---|---|
| T-U04 / R147 用户原页 | 现3310、原tab21、原conv_ffd7；用户打开后持续加载，Root读取/尝试关闭 | 有界进入可用工作区；失败提供可恢复入口，不永久loading | P0 / 系统用户路径、状态机 | 用户截图失败；页面读取/关闭超时，未取得根因，仍开放 |
| T-U04 / R147 同会话新页 | 同服务/浏览器身份，仅新tab22；打开原会话→reload→填入/清空输入框 | 原正文恢复、工作台可操作，刷新不丢消息 | P0 / 系统交互 | IAB限定通过，截图/tmp/kokoro-r147-workspace-interactive.png；不是旧页已修/已关闭 |
| T-U04 / R147 认证cold/reload系统门 | 真Next/Chromium、真实ProductSession签发、严格owner HTTP fixture；cold及reload各12s，分别核本阶段session200→app/composer可见→填入/清空 | 两阶段都收敛，无永久SSR loader；失败诊断资源/hydration/session边界且不输出凭据 | P0 / 系统功能、异常、生命周期 | 初版5聚焦通过但审出2P1证明缺口；修后Root37618完整48/48、0skip通过。生产源码未修改；真实IAM/BFF全组合及旧页根因仍未关闭 |

## R146-B07 正式费用链系统验收（12条，全部未验）

### 证据边界

- Billing基线：`main e04bff`；沿用 `/tmp/kokoro-r146-b07-qa-owner-audit.md`（SHA `9037ab12f6023d6f80e30722d2d9eed25ce6d8af9e72076ef083e47c284592eb`）的owner/source审计。
- Agent `main 2d2ad9bb4d261bee6c71e35f0d68f419a785bf9c` 已发布 `contract/usage/v1` strict typed离线artifact；以下证据输入必须直接使用该正式schema/vectors，不另造attempt shape。
- Agent离线42项、2174 pure及wheel正负门不计作runtime/provider→Billing链通过。
- 用户规则：failed/cancelled仅结算已核实实际消耗；仅释放可确认未使用的预占；unknown持久pending等待核实/对账，绝不映成zero或整笔release。
- 全部案例执行状态：**未验**。本增补属于既有T-B07测试组，不增加或重排原70组，不是新计划中心。

### 主链路

#### B07-E2E-01 — completed单attempt按冻结价格结算

- **预置：** 账户有足够正式Credit；Billing已发布价格revision R1及倍率/换算；hold H绑定R1、model/provider/pricing account与attempt authorization；Agent runtime实际调用provider并产生符合正式artifact的completed sealed evidence，usage为verified nonzero。
- **步骤：** 用户发起一次会产生真实provider调用的Run；系统reserve H；provider完成；Agent持久并投递正式evidence；Billing认证、按R1自行计价并结算；用户在前端查看Credit变化与ledger。
- **权威预期：** Billing不接受caller金额替代证据；仅capture R1计算的actual，release `H-actual`；hold、allocation、settlement、journal、receipt/outbox/audit同一业务结果且exactly once；前端只显示Billing结果，不重算费用。
- **Priority / Type / Status：** P0 / 主链路·真实provider+Agent+Billing+Web E2E / 未验。

#### B07-E2E-02 — failed attempt仍结算verified actual

- **预置：** hold active；provider已接受调用后返回错误；正式evidence outcome=failed、seal有效且usage/actual attribution为verified nonzero。
- **步骤：** 用户运行任务；provider失败；Agent记录失败与实际usage并提交；Billing结算；用户查看失败状态和账务。
- **权威预期：** Run失败不等于免费；Billing只扣已核实actual并释放确认unused部分；不得按reservation全扣，也不得整笔释放。重复失败通知不产生第二笔debit。
- **Priority / Type / Status：** P0 / 主链路·失败计费E2E / 未验。

#### B07-E2E-03 — mixed attempts逐attempt计价后final settle

- **预置：** 同一业务执行有attempt A失败但verified usage>0，attempt B重试成功且verified usage>0；两者各有正式identity/revision/seal，最终集合seal证明本次执行attempt闭集；reserve足够。
- **步骤：** 系统执行A后重试B；Agent可按任意网络到达顺序投递A/B revision及最终seal；Billing恢复并结算；用户查看唯一最终费用。
- **权威预期：** Billing逐attempt使用冻结revision计价并分别执行`attempt-ceil-v1`，再形成唯一settlement；A消耗不遗漏，B不重复；只有闭集已知后释放unused；ledger/audit能关联两个attempt但前端不自行求和。
- **Priority / Type / Status：** P0 / 主链路·多attempt恢复E2E / 未验。

### 边界

#### B07-BND-04 — cancelled且verified no-call释放全部预占

- **预置：** hold active；Agent正式evidence证明authorization/dispatch状态与outcome一致，provider调用未开始，actual为verified zero而非unknown。
- **步骤：** 用户在provider dispatch前取消；Agent封存no-call/verified-zero事实；Billing消费并结算。
- **权威预期：** capture 0，release全部H；保存可审计的verified-zero依据；cancel字符串本身不作为释放证据。
- **Priority / Type / Status：** P0 / 边界·取消前零调用E2E / 未验。

#### B07-BND-05 — cancelled与provider完成竞态

- **预置：** hold active；cancel与provider response并发；provider调用已经开始并最终有verified usage。
- **步骤：** 用户发出取消；provider同时完成或失败；Agent按正式revision规则合并观察并seal；Billing消费重复/乱序事件。
- **权威预期：** 只按最终不可替换的verified actual扣费并release余量；cancel不得覆盖已观察dispatch/usage；无双扣、负release或两个terminal settlement。
- **Priority / Type / Status：** P0 / 边界·双连接/竞态E2E / 未验。

#### B07-BND-06 — verified zero与unknown严格区分

- **预置：** 两个独立hold：Z有完整known-zero observations与seal；U缺少可核实usage、totals_state/actual保持unknown。
- **步骤：** 分别投递Z和U正式evidence；触发Billing消费、重启与reconcile；查看两账户状态。
- **权威预期：** Z可capture 0并release确认unused；U保持pending，资金不capture也不release；两者状态、receipt、audit不可互换，null/缺字段不得降级为0。
- **Priority / Type / Status：** P0 / 边界·知识状态隔离 / 未验。

#### B07-BND-07 — 价格revision冻结，后续上调不追溯旧hold

- **预置：** hold在R1有效时创建并固定R1完整pricing snapshot/digest；执行期间发布更高价格R2；同一Agent usage可用两revision算出不同结果。
- **步骤：** reserve后发布R2；完成旧attempt并结算；再创建新hold执行相同usage。
- **权威预期：** 旧hold严格按R1结算，新hold按R2；不能结算时重新查latest；倍率、采购率、Credit换算、舍入版本均可由持久字段重算和审计；前端只显示Billing ledger。
- **Priority / Type / Status：** P0 / 边界·价格不可变性 / 未验。

### 异常与恢复

#### B07-ERR-08 — unknown持久pending并在重启后对账

- **预置：** provider调用可能已发生，但Agent只有unknown outcome/usage revision；hold仍保留；reconcile稍后可获得verified evidence或verified no-call。
- **步骤：** 投递unknown；重启Agent/Billing worker；重复投递相同revision；随后提交合法successor与final seal；执行对账。
- **权威预期：** unknown阶段不扣、不释放、不标zero；pending身份和hold跨重启保留；合法successor最终exactly-once settle，非法替换/跳revision拒绝；若最终仍unknown则继续待核实而非TTL整笔释放。
- **Priority / Type / Status：** P0 / 异常·崩溃恢复/对账E2E / 未验。

#### B07-ERR-09 — duplicate、乱序与ACK丢失

- **预置：** 一个attempt有连续revision和final seal；网络会重复、倒序、在Billing commit后丢ACK。
- **步骤：** 先发后继/terminal，再发前驱；重放相同event；篡改同identity digest；模拟结算commit后客户端超时并重试。
- **权威预期：** 缺前驱保持可恢复pending或按正式契约拒绝，不latest-wins；同revision同digest no-op；同identity异digest冲突；ACK丢失重放返回原结果；始终只有一个settlement/debit/outbox/audit业务事实。
- **Priority / Type / Status：** P0 / 异常·幂等/乱序/恢复 / 未验。

#### B07-ERR-10 — actual超过reservation

- **预置：** verified sealed attempts按冻结revision算得actual>H；账户可能有额外available Credit，也可能不足。
- **步骤：** Billing消费最终证据并尝试结算；分别覆盖余额足够/不足；重试同一证据。
- **权威预期：** **产品/资金策略待Root设计裁决**；在裁决前必须fail closed/pending，不截断成H、不产生负release、不部分提交journal/hold/settlement，也不得擅自二次reserve或透支。最终规则须先落三设计和机器契约，再将此例具体化。
- **Priority / Type / Status：** P0 / 异常·待设计资金边界 / 未验。

### 安全与审计

#### B07-SEC-11 — foreign/tampered evidence零资金变化

- **预置：** 合法hold H；准备wrong tenant/subject/run/attempt/authorization binding、错误provider/model/pricing account、坏digest、非连续revision及未认证caller样本；另有合法控制。
- **步骤：** 通过正式Billing ingress逐项提交；随后提交合法控制。
- **权威预期：** 所有非法样本在资金写前拒绝，不泄漏foreign hold/evidence存在性；hold/allocation/account/journal/settlement/outbox/audit业务行零变化；合法控制仍可完成，证明不是fixture全拒绝。
- **Priority / Type / Status：** P0 / 安全·跨租户/篡改/认证 / 未验。

#### B07-SEC-12 — grant allocation与audit可追溯且不造免费Credit

- **预置：** 账户同时含购买grant与既有正式bonus grant，burn priority/expiry明确；reserve跨多个grant；verified actual小于H。
- **步骤：** 完成结算并重放；查询本人ledger和受权audit；再尝试重复/异义证据。
- **权威预期：** 只按既定allocation顺序capture/release；不新建bonus、充值或隐式免费额度；journal总额、hold allocation、settlement、audit关联一致，重放不重复；用户前端只读展示，不拥有计价或ledger写权。
- **Priority / Type / Status：** P1 / 安全·会计审计/权限 / 未验。

### 状态机覆盖索引

- `reserved → verified completed/failed/cancelled → settled`：B07-E2E-01/02/03、B07-BND-04/05。
- `reserved → unknown → pending → reconciled settled/no-call`：B07-ERR-08。
- revision/replay/ACK恢复：B07-ERR-09。
- pricing freeze：B07-BND-07。
- 未裁决资金状态：B07-ERR-10保持待设计，不以测试先造行为。
- 权限与会计不变量：B07-SEC-11/12。

实施续接现R80 Billing设计与既有任务卡；不复制Agent schema、不新增计划中心，也不把本文“未验”改成离线artifact测试已过。


### T-B07 系统费用验收退出标准

上述12条逐项有当前版本、真实操作、资金前后对比、实际结果与证据；所有P0通过，P1未解决项不得涉及资金/权限完整性。至少覆盖真实provider非零费用、failed/cancelled、verified-zero、unknown跨重启恢复、重复/乱序/ACK丢失及冻结价格。余额、预占、扣减、释放、ledger/allocation与settlement核对一致；无双扣、凭空Credit、未知当零或前端计价。超预占策略先由Billing三设计收敛，再按规则执行B07-ERR-10。离线artifact、unit/mock、单次成功、接口启动或worker报告均不替代此门；支付渠道仍最后验收。当前12条全未验，未达到退出标准。

## R146 资源生命周期系统验收矩阵（核心已复验，完整旅程未验）

完整70组计数不变，以下是T-C05下的资源owner前置；不得只凭Storage通过关闭Project浏览器全旅程。Root明确批准Project Artifact行为变化：不是存在任意Artifact就失败，而是在scope锁内验证完整同域graph，一致关系按用户项目删除规则释放，损坏关系仍全事务回滚；无remediation RPC/新表/兼容入口。Artifact title及CreateArtifact历史receipt内title是用户内容，释放时同事务清空；最小身份审计不成为可读文件或URL。Root已实际39/39窄GREEN，锁前receipt快照原P0已因实际Serializable全事务重试及Root40绿色纠偏撤回，但仍需精确barrier/retry证明与损坏objectKey安全门，以下整组仍未验。

|用例ID / 标题|预置条件|测试步骤|预期结果|优先级 / 类型|状态|
|---|---|---|---|---|---|
|T-C05.C01 会话完整资源释放|C有final/draft作品、普通Asset、pending/completed/aborted Upload及同域Blob|Given真实Storage Connect/PG链，When已授权BFF释放C并重放原命令，Then查用户读/资源和回执|scope released；active Upload aborted而终态保留；Asset不可读、Blob退役，全部staging/canonical cleanup与回执同事务；作品title清空/最小审计保留；重放稳定|P0 / 主链路、状态机|未验|
|T-C05.C02 授权/身份与异义|BFF/Agent/Platform独立凭据，两tenant/subject/scope|When错误caller、非conversation scope、body自报身份、同command异义、跨域同ID|仅可信BFF+目标scope允许；body不代言身份；异义冲突；别域事实不变，不泄露内容|P0 / 安全、边界|未验|
|T-C05.C03 ACK后全部入口与旧回执|已释放C，既有Agent upload/create/finalize和BFF读/download历史receipt|When各入口新调用与旧回执重放，包括签名后最终fence|不签新URL、不读旧作品、不创建/完成/Finalize；release自身原命令可恢复；不得旧receipt穿透|P0 / 生命周期、安全|未验|
|T-C05.C04 跨域同摘要与共享引用|C多个作品/Asset复用Blob；其他conversation/project/personal/skill_package有同摘要|When释放C并重放，Then核其他域实际读与本域cleanup数|仅C受影响，Blob cleanup按identity去重，别域原字节和可见性保留；无跨scope去重删除|P0 / 边界、数据完整性|未验|
|T-C05.C05 释放与Agent在途竞态|真实两个PG连接；Create/Finalize/Complete/Scan在途|When分别令写入先提交/释放先提交并重试、重启|先写则release纳入其结果；先release则后写失败，不复活Asset/Artifact/Blob；未知结果同命令恢复，非新ID补写|P0 / 竞态、状态机|未验|
|T-C05.C06 晚PUT/签名未知|已签PUT尚未完成；provider一次missing、晚写入、delete成功后再晚写|When释放→reconcile→晚PUT→再次reconcile|expiry持久、cleanup持续可恢复pending；晚对象不能Complete成Asset；一次missing/delete不假物理终态|P0 / 异常、恢复|未验|
|T-C05.P01 Project一致Artifact graph|Project内异常历史但完整同scopeArtifact/Asset/Blob图，多个Artifact可复用|When按正式项目删除授权调用ReleaseProjectScope→重放|一致图同锁释放、title清空、最小审计保留；无永久blocked，无额外修复API；计数稳定|P0 / 主链路、恢复|未验|
|T-C05.P02 Project损坏graph回滚|每次独立fixture：跨scope/孤儿Asset或Blob、错误purpose、摘要/状态矛盾、partial deletion|When调用release，Then核全部业务事实/cleanup/回执|拒绝且业务全回滚，其他scope无变；失败claim可原command再试但不是completed；不得仅删除失败Artifact绕过|P0 / 安全、异常、事务|未验|
|T-C05.X01 BFF项目总体完成|Project成员集合在删除事务内冻结；Storage新契约已发布/pin|When202后断线、ACK乱序/重复/超时、worker重启；读取项目状态|N个成员conversation+Project稳定命令全部logical ACK才完成；单Project ACK不覆盖成员资源；physical pending独立展示；Web失败不丢未确认事实|P0 / 跨仓主链路、恢复|未验|

## R145 当前界面窄验与业务矩阵纠偏（2026-10-03）

当前70组11通过/6失败/14待复测/38未验/0业务待决/1支付后置保持，未把单次正常登录/回答换算整组通过。编号计划suffix原bytes保持。

|关联组/子路径|实际操作与结果|证据/限制|
|---|---|---|
|T-L01 当前正常首方登录|正式/login，账号密码提交，自动callback→/app，工作区退出加载；未显示内部scope consent或整页连接/重试设计|Root受管32044及当前IAB tab21；未验第三方/prompt/退出/旧账号恢复，不关闭整组|
|T-C06 新会话真实回答/终态刷新|实际发送一个数学问题，queued→非空KOKORO_R145_E2E回答、Stop0；刷新前后记录完整相等|截图/tmp/kokoro-r145-login-chat-refresh.png SHA c8781b03...；qwen3:8b，不是5.6-luna/流式中途恢复/正式账本/全能力|
|T-C05 Storage owner矩阵|Root31616/93381分别暴露非法limit与错误receipt零行期待，纠正测试协议不改业务源码；两正式测试最终freeze，72179项目6/6、Upload9/9、全门659/0skip通过，发布Storage2f855816；BFF项目删除和成员Conversation资源释放未实现|不是产品RED或ProjectDELETE闭环；含成功删除其他scope文件保全、异常业务回滚/幂等/8入口封锁；关联文件为project-scope-release和upload-reference-gate，sign/complete请求交错不冒称持锁等待|
|T-B07 失败/取消费用|用户再次确认仅结算核实消耗、释放剩余预占；unknown待核实，Billing权威|仅规则对齐与Agent已发布offline artifact前置；实际非零扣款/释放/流水仍未验|

## R145 新实证不冒充完整组通过（2026-10-03）

完整70组仍11通过/6失败/14待复测/38未验/0待业务决策/1支付后置。T-B07业务规则已确认，Agent离线usage42与安装正负门通过只作为其前置；真实provider→Billing预占/按核实消耗结算/剩余释放/unknown待核实/流水仍未验。IAM owner实际12个节点通过与工程938通过不替代T-L01当前浏览器callback/app。Storage真实PG+Connect及installer完整194通过，新增晚PUT durable遗失P0真实RED保留，T-C05未验、物理GC不称完成。原编号计划全部bytes保留。

## R144 系统交互失败记录与当前看板（2026-10-03）

当前70组 **11通过/6失败/14待复测/38未验/0待业务决策/1支付后置**。T-C03从未验改失败：这次实际达到合法会话snapshot与DELETE，非前两轮fixture前置失败。下方R143及以前的“当前”计数均是当时快照，以本节为准；通过组不能解释为全部用户旅程完成。

| 用例ID / 标题 | 预置条件 | 测试步骤 | 预期结果 | 优先级 / 类型 | 实际与证据 |
|---|---|---|---|---|---|
|T-C03.R144-D1 删除确认等待ACK|真实Next/Chromium、正规fixture OIDC、严格BFF HTTP fixture，独立会话A/B，A有已加载正文及草稿；代理扣住DELETE尾段|打开A→输入草稿→删除菜单→确认→观察未释放ACK→释放严格200deleted|单次DELETE带scope=direct；ACK前会话/正文/草稿/确认框不变，pending防重且不刷新；ACK后一次移除和权威刷新|P0 / 系统功能、竞态、状态机|失败：合法GET snapshot1/DELETE1，但DELETE无query（1457断言），诊断确认dialog提前关闭/list提前GET。修复后Root60241同2例及35964完整47系统限定通过；最终Root86341完整2354测试/0skip及build通过，已发布Web49721a5。不是BFF真实PG或当前IAB验收 |
|T-C03.R144-D2 明确删除失败保全|同正式Web链；A已加载，独立草稿，BFF fixture返回503|确认删除→观察错误/草稿/list/cancel请求→恢复后人工重试|失败保原会话/草稿/正文、显示可恢复错误；无cancel、提前刷新或自动重发|P0 / 系统异常、用户数据完整性|失败：1528草稿变空，snapshot1/DELETE1、dialog提前消失，列表提前GET；修复后同2例与完整47限定通过，最终Root86341完整门通过，发布Web49721a5；未知/当前IAB与完整T-C03仍未验 |

Root实际命令为Node22/pnpm11.25.0下现OIDC system file过滤R143，2失败/45名称过滤，31.967秒，753源前后未变。证据目录 `/var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-r144-web-delete-ack-red-v3-thohj__u`，manifest SHA27f322eb7a58b1381433fbd49a087e7055e6d2ac7e223efcf895700b938dc376、log SHA35ae952f2eb249ae4e1fdb13b398541925163347c5b5f08489df666fc823f341。两具体系统用例最终回归通过并已发布Web49721a5；T-C03完整组保留失败待Project/晚ACK及真实owner复测，不以两个系统fixture通过替代真实owner/完整70组/正式费用链。

## R143 两项业务裁决已确认；未执行不计通过（2026-10-03）

用户已答复 T-C05「参考ChatGPT一样的规则」与 T-B07「仅结算已核实的实际消耗，释放其余预占」。两组由待决策改为**未验**，不是通过；当前70组 **11通过/5失败/14待复测/39未验/0待业务决策/1支付后置**。旧轮次计数与原70ID编号计划是历史，以下补充取代旧计划中这两组的待裁决描述，不删除其历史bytes。

项目参考已于2026-10-03核对 [OpenAI官方Projects说明](https://help.openai.com/en/articles/10169521-projects-in-chatgpt) 的 Delete a project / Move an existing chat：删除项目移除其会话、指令及仅存于项目的文件，不可撤销；独立保存在Library的文件不受删除影响；会话可先移出项目。Kokoro采用相同用户语义，不凭外部产品说明宣称本仓已实现，也不照搬未批准的项目分享/记忆/数据保留期限。独立ScheduledTask不因此被级联删除；关联处理、活动Run取消与作品生命周期由BFF/Agent/Scheduler/Storage现owner契约门落实，不跨ownerSQL或物理删共享blob。

Billing规则：completed/failed/cancelled都只按可核实的实际attempt用量及冻结费率、倍率/换算版本结算，不能按输出是否展示判断免费；未发provider调用不扣。已确认未用预占释放；存在unknown attempt时，只有证据能确认的未用部分可以释放，未知部分持久待核实/对账，不当0、不直接整笔release、不换key补扣。相同证据重复/乱序/晚到与取消竞态只能产生一次有效账务结果。前端只展示Billing权威结果。

### T-C05 / T-B07补充系统验收矩阵（均未执行）

|用例ID / 标题|预置条件|测试步骤|预期结果|优先级 / 类型|状态|
|---|---|---|---|---|---|
|T-C05.D01 删除项目主链路|本人项目P含会话A/B、指令、独占文件F，另有外部会话C|Given上述资源，When从项目菜单删除、阅读影响范围并确认，Then刷新侧栏与各原详情/分享入口|P/A/B及指令/F不再可访问，不把A/B自动搬到外部；C不变；不可撤销提示准确|P0 / 功能、状态机|未验|
|T-C05.D02 先移出再删除|P含A/B|Given A可移动，When移出A→核普通会话列表→删除P→刷新，Then重新打开A/B|A身份/消息保留且不复制，B随P删除；列表与路由一致|P1 / 功能、边界|未验|
|T-C05.D03 取消/空项目/重复确认|空P或含A的P|Given确认框，When取消→重复点击确认→重复命令，Then核资源和操作记录|取消零删除；空项目可删除；重复动作幂等，UI pending防重，不产生多次cleanup|P1 / 边界、状态机|未验|
|T-C05.D04 无权与失败回滚|另一身份B；owner可观察删除事务失败|Given P属A，When B直接请求或A遇删除失败，Then重开列表/会话|无权不泄露或删除；明确失败不提前移除本地事实；错误可恢复；unknown不谎报成功|P0 / 安全、异常|未验|
|T-C05.D05 运行/任务/迟到事件|P有active Run、关联独立ScheduledTask及在途输出|Given上述状态，When确认删除、重启相关owner并重投事件，Then核任务/Run/作品|已删会话不被晚事件复活、分享失效；Run取消按ownerdurable流程收敛，不提前伪造终态；独立任务不级联删除，不再调度到已删上下文。关联策略先契约冻结|P0 / 生命周期、恢复|未验|
|T-C05.D06 独立保存/共享文件|F只属于P；G同时独立保存或被其他有效资源引用|Given两类资源，When删除P→访问独立资源与下载，Then核授权/清理记录|F移除项目可见性，Storage按有效引用清理；G及其他引用保留，不物理删共享blob|P0 / 安全、数据完整性|未验|
|T-B07.D01 失败/取消有已知用量|正式授权余额/预占及非零可核实attempt，费率版本固定|Given已产生用量，When分别供应商失败/用户取消/部分输出，Then查余额、预占、结算、流水并刷新|只结算已核实实际消耗、释放可确认剩余；同证据同金额，无前端算价/失败免费特判|P0 / 功能、财务|未验|
|T-B07.D02 未发生调用/核实零|provider观测为零调用；另有明确reported-zero证据|Given两类场景，When取消或失败，Then查正式账本|不扣积分、释放可确认预占；零有证据，缺字段不伪装零|P0 / 边界、财务|未验|
|T-B07.D03 未知/晚到用量|一个known attempt及一个unknown attempt，重启后可补严格证据|Given混合用量，When失败→重启→晚证据抵达→对账，Then多次查流水|仅核实部分可结算；未知部分不提前结清/免费/全释放；证据到齐后按同冻结版本幂等收敛|P0 / 异常、状态机|未验|
|T-B07.D04 重投/取消结算竞态|同attempt证据、取消与结算并发可控|Given原授权，When乱序/重复投递与并发cancel/capture，Then重启并核账本|单一有效结算/释放，无重复扣费、超额释放或未授权透支，余额/流水一致|P0 / 并发、恢复|未验|
|T-B07.D05 越权/坏证据/事务失败|其他付款主体、坏revision/digest、owner事务失败条件|Given合法预占，When提交越权/坏证据或注入真实事务失败，Then核provider与账本|拒无效证据/自报金额，零非法变动；失败原子回滚且可恢复，不调用未授权provider|P0 / 安全、异常|未验|

关闭标准：以上必需分支及原组有效分支在固定发布组合、真实owner与正式UI路径通过，证据绑定版本/实际结果/回收；只记录业务答复不满足退出条件。支付渠道仍最后。

## R143 当前组合QA纠偏与五条并行旅程（2026-10-03）

当前看板明确 **11通过/5失败/14待复测/37未验/2待决策/1支付后置=70**。修正旧看板4失败/38未验与矩阵5失败不一致；将历史E53登录T-L01/聊天T-C06移回待复测，历史证据保留。通过中的工程/规则/限定后端门不是11条完整用户路径。测试任务统计不得当开发完成百分比。

R143-QA只读审定位五条可执行旅程：①IAM发布后普通登录/退出/权限（T-L01–05，不等Agent）；②独立与项目会话/ACK/分享/刷新（T-C02–04/U04，不等Agent）；③定时任务控制面CRUD/权限与执行恢复分别验（T-P01–05，阶段A不等Agent）；④Skill/MCP管理的真实安装/连接/撤销（T-K02/03/05，不等Agent）；⑤正式Agent队列/过程/HITL/作品/费用（T-C07–10/A01–06/F03/B02–06，固定契约后实际串链）。每条完整前置/步骤/预期/异常权限/状态机/证据沿原逐组计划；不新测试ID、单测或第二计划中心。

独立产品审指出误写T-M01–05与项目分享主语歧义，已改为现T-K01–07与Conversation显式分享，未新增Project分享/级联规则。项目删除与失败费用两待决已分别询问用户，其余研发不等待。当前用户整页加载、六重复页清理和完整费用链仍未关闭。

## R141 两个列表子例限定GREEN（2026-10-03）

Root有效RED后同2节点通过，完整45 OIDC系统节点通过；最终96991完整工程门自然0：256contract/50architecture/lint/typecheck/2352tests0skip/build通过。Web已发布7df55c3且原3310仅两runtime源精确更新，不重启。系统证据使用真实Next/Chromium与严格BFF HTTP fixture，不是所有真实数据库owner组合；当前用户IAB/原会话未验收，signout500间歇根因仍未知。独立七路径审0，实际manifest与失败历史见progress R141。

当前完整70组为13通过/5失败/12待复测/37未验/2待决策/1支付后置：T-U04从未验校正为失败，依据用户当前整页无限加载已实际报告且未关闭；两个列表子例通过不把整组转绿。历史各轮统计原样保留，逐组用例计划不变。IAM内部scope consent正常入口偏差仍待修，不执行旧批准请求。

## R141 有效RED定位更新（2026-10-03）

严格列表作用域/展开侧栏后的Root47705实际2失败：200成功body尾段held1超过15s仍loading；503真实error/Retry已渲染却被空列表隐藏类遮住。原collapsed/全页Retry误定位不作为产品根因。两个子例现由原Web writer窄修，Root同例复验中，不改整组或当前用户IAB完成状态。IAM首次consent不代grant；按既有第一方受信client政策收敛，第三方与逐请求权限继续验证。

## R141 列表异常与恢复的系统用例执行（2026-10-03）

| 用例ID / 标题 | 预置条件 | 测试步骤 | 预期结果 | 优先级 / 类型 | 当前实际 |
| --- | --- | --- | --- | --- | --- |
| T-U04 / R141-U01 会话列表body未结束 | 真实Next/Chromium正规fixture OIDC，现browser→Next HTTP边界扣住真实成功响应最后字节 | 打开/app→确认list实际tail hold→观察15s→错误与Retry→恢复网络并点击Retry | rail加载有界，显式错误可重试；列表恢复，无自动风暴/登录误跳 | P1 / 系统 / 边界 / 状态机 | 展开路径修正后有效RED；10s全body预算窄修后Root同例及完整45、完整2352节点通过，限定列表片验收，不关闭当前IAB整组 |
| T-U04 / R141-U02 列表503可恢复 | 同正式Web链，owned BFF HTTP fixture给合法503 envelope | 打开/app→503→观察rail错误与Retry→恢复200→手动Retry | 保工作台，不把失败当空成功；Retry后权威列表可见 | P1 / 系统 / 异常 / 状态机 | 展开路径有效RED定位emptyDirectList隐藏error/Retry；class窄修后Root同例及完整45、完整2352节点通过，真实手动Retry恢复 |
| T-L01 / R141-L01 当前IAM第一方入口偏差 | 复用现3310实际IAM，独立系统browser正常表单，无session注入 | /login→现fixture账号正常输入/提交→观察权限确认 | 自家可信client正常认证后直接工作台；第三方/显式consent才走授权，保逐请求权限；不代grant | P1 / 安全 / 生命周期 | 当前账号密码成功，但fixture十scope consent不符正常第一方入口；旧批准请求撤回不执行。R142受控provisioning真实RED、未GREEN，工作区/原用户页全链未验 |

Root原31535自然exit1，2失败/43名称过滤，非完整45节点回归；详细hash/资源见progress。此只补原70组子例，不扩大通过组数。当前用户旧会话持续加载与重复7页尚未闭合。

## R140 最新用户截图：加载缺陷仍未关闭（2026-10-03）

| 用例ID / 标题 | 预置条件 | 测试步骤 | 预期结果 | 优先级 / 类型 | 当前实际与状态 |
| --- | --- | --- | --- | --- | --- |
| T-U04 / R140-U01 当前旧会话工作区启动 | 原3310、现Web6267c1e、用户原会话与浏览器身份 | 当前页刷新→正规登录或复用有效session→进入工作区→打开原会话 | 有界加载后进入可用工作区；失败可恢复、不整页永久转圈；不丢输入 | P1 / 系统业务 / 异常 / 状态机 | 用户截图仍加载，当前路径失败未关闭；IAB观察控制超时，等待手动刷新反馈与实际复验 |
| T-L01 / R140-L01 现运行入口匿名启动正控 | 新独立匿名Chromium，无cookie注入，复用3310且不启动服务 | /app→浏览器自然发session→跳正规IAM表单 | 明确匿名才登录，表单可见，无永久工作区loader | P1 / 系统功能 | 实际session1、document200、sign-in表单可见，限定通过；非已认证/原会话/当前IAB或整个T-L01当前全旅程通过 |
| T-R02 / R140-R01 重复页面清理复核 | 七页均原会话URL、保留当前13 | 关闭重复页→盘点剩余→确认当前输入与页面 | 只保留所需页且保留输入 | P2 / 交互 / 生命周期 | close控制超时，最终实际仍7；未成功清理 |

R139限定工程与故障系统证据保留，不据其将R140当前用户失败改绿。70组及完整逐组用例计划保持；本轮独立浏览器已回收，原98977保持，无共享reset。实际证据与根因假设反证见progress R140。

# Kokoro 测试任务总台账

## R139 最新系统回归（整组仍待用户验收）

最新Root完整工程门已通过：2350/2350、0skip，含下表四真实页面行为和OIDC43/IAMrelay68，Web发布6267c1e；原3310八runtime源已更新且无CookieHTTP200。当前用户IAB/六重复页关闭仍未验证，完整T-U04/T-R02不凭源码发布转绿，70组原状态保持。此前lint/typecheck/十旧断言失败保留在progress，未删测试或放宽门禁。

| 用例 / 优先级 / 类型 | 预置条件与操作步骤 | 预期结果 | 最新实际 |
| --- | --- | --- | --- |
| T-U04-R138-U01-pending / P1 / 边界与异常 | 真Next/Chromium，owned代理保持session；打开app并聚焦，待有界截止，恢复网络点Retry。 | 不永久加载、不请求风暴；有重试入口，恢复正规登录/工作台，旧请求不覆盖。 | Root完整43节点中通过，初始有效失败仍保留如下。 |
| T-U04-R138-U01-503 / P1 / 异常与状态机 | 同真实页面仅session返回503，恢复后Retry。 | 服务故障不是匿名，不自动反复登录；人工重试可恢复。 | 通过；不等于真实IAM/BFF全链故障恢复。 |
| T-U04-R138-U01-anonymous / P1 / 主链路 | 真实Next返回200 anonymous；访问app。 | 唯一允许自动启动正规登录的结果，不fail-open。 | 通过；正式用户账号密码/模型/积分仍待当前组合验证。 |
| T-U04-R139-same-subject-tabs / P1 / 状态与交互 | 真登录后首tab新建会话、填未发送草稿；同browser第二tab访问app。 | 两页工作台可见，首草稿与索引不丢，不发模型/收费请求。 | 原27238实际失败，marker修复后Root完整43节点通过。 |
| T-R02-R138-S02 / P2 / 资源生命周期 | 用户当前7页，保留当前页，关闭六个重复页，再核数量。 | 保留用户当前页，其余重复页真正关闭。 | 关闭控制超时；尚未通过，未创建新用户tab。 |

Root原15326系统完整43通过/0失败/0跳过，前序工程门lint/typecheck/旧断言失败均保留于progress；最终原84601工程门全通过，已发布并更新原3310八源。用户当前页与关闭六重复页未验，整组不冒充通过。跨actor草稿/跨文档身份并发/list-snapshot deadline后继，70组及下方逐组计划保持。完整命令/manifest见progress R139。

## R139 有效业务失败（前序阶段，历史保留）

| 用例 / 优先级 / 类型 | 预置、步骤 | 当前实际 / 验收 |
| --- | --- | --- |
| T-U04-R138-U01-pending / P1 / 状态机与异常 | 真Next+Chromium、owned网络代理保持session请求；打开/app并聚焦两次，观察12s，再人工Retry恢复。 | 当前session1/login0但一直loader，无Retry，失败。应有界故障、无请求风暴，Retry恢复且旧响应不覆盖。 |
| T-U04-R138-U01-503 / P1 / 异常流 | 同真实页面代理仅session503；打开/app，随后恢复网络并Retry。 | 当前23次session/46次login循环，失败。应留当前页、故障不当匿名，单次重试按真实响应恢复。 |
| T-U04-R138-U01-anonymous / P1 / 主链路 | 同页面真实Next session200 anonymous，非伪造浏览器返回。 | 本节点通过，正常启动正规登录；不代表账号密码/聊天完整旅程通过。 |
| T-R02-R138-S02 / P2 / 资源生命周期 | 保留当前页面、关闭六个重复页并核对数量。 | 仍7页，关闭控制超时；未通过，未创建新页。 |

此前CSS编译500与测试代理缺CONNECT均是独立阻塞，不冒充上述业务RED。最新Root3节点2失败/1通过，原70组状态及逐组执行计划保持；实现、完整复测与当前用户浏览器验收见task/progress后继。

## R139 当前系统验证记录（不变更70组状态）

T-U04/R138-U01：pending/503/真实匿名三系统节点首版Root3fail，但/app未bootstrap/session请求未到达，属于测试夹具失败，不能冒充产品RED或完成；仅测试细化后Root17900终态仍3个/app500/session0夹具失败，生产修复待有效RED。
T-R02/R138-S02：仍7重复页；已有句柄close超时，未成功关闭，不记通过。
T-Q10：库存错位组件已更新已发布源268refs/37字段，Root100工具通过、topology/checkpoint通过；compat仅13declared broken，整体依赖用户旅程未闭合，保失败。完整字段计划及原失败历史不改，详细hash/句柄见progress R139。


## R137 / E117 当前工程检查与系统验收边界

最新冻结复验：Root完整工程门256contract/50architecture/lint/types/2346tests/build通过；随后桌面+移动六页面同例6/6再次通过，官方typecheck恢复Next生成文件。T-Q01仅本次工程门转通过，70组13通过/4失败/12待复测/38未验/2决策/1支付后置。六页面是明确development preview，非正式服务/真实模型/积分链；完整用户组仍保持待验。实际命令、manifest、原失败与资源终态见progress E117。

E117早期失败历史：当时完整工程门2344通过/2旧preview raw断言失败（contract256/architecture50/lint/types已通过，build未到达）。桌面与移动六页面行为E116通过只限UI演练；T-Q01及正式用户组不据此整体转通过。沿原writer迁移既有断言，后续Root同门复验；不新增底层测试或替代70组系统验收计划。

状态：当前测试计划，2026-10-03 / R142；最新限定工程与列表系统证据至R141，IAM R142 v2真实RED待GREEN。复用既有文件，不建立第二开发计划中心。

- 本页唯一维护**测试任务、验收标准和最新结果**；[task.md](task.md)维护派工/依赖，[progress.md](progress.md)保存实际运行证据，[CURRENT.md](CURRENT.md)说明当前组合。
- 范围：批准Wave0–7全部研发能力与九owner；其他前端、历史Session/Mongo、部署多角色/网络策略不在本轮。支付渠道后置，不删除目标。
- 本表每行是测试任务组，不是一个自动化断言；各owner用例留本仓。未验不等于没有代码，历史通过不等于当前组合通过。
- 状态：通过 / 失败（最近执行） / 执行中 / 待复测（有历史证据或版本变更） / 未验 / 阻塞（明确决策缺失） / 后置。
- 完成条件：绑定commit或冻结hash、实命令/环境、pass/fail/skip、证据和清理；本行必需分支被跳过则本行不得通过；明确拆至其他测试ID的资源分支仍记未验，不影响限定纯门，但绝不计为资源通过。相关source/contract/pin变更后移回待复测。修复提交不直接关测试，Root复测成功才关闭。
- 当前状态以本页最新看板、progress最新R141/R142实际证据与下方测试矩阵为准；E117等与旧R编号仅历史，最新代码变化须复测。历史发布组合cc7bfb78/Webddd38c5的E53正规登录与严格两轮聊天保留，不代表当前七标签页或所有用户能力已验证；E49具体安装缺陷已E76复验关闭，T-Q03整体门仍未验收。

## R138 当前用户“持续加载”与多标签页缺陷记录

|用例ID / 标题|预置条件|测试步骤|预期结果|优先级 / 类型|实际与状态|
|---|---|---|---|---|---|
|T-R02 / R138-S01 唯一入口服务恢复|原3310无listener；现PG/Redis可用，无其他launcher|核端口与原句柄→严格已发布源preflight启动一次→有限请求/app/session/login|唯一3310服务正常响应，不重复基础设施；只称服务恢复|P1 / 系统可用性|原98977运行、三HTTP200；当前浏览器及真实登录聊天未验|
|T-U04 / R138-U01 会话探针长期pending或503|正式Next页面；可控自有下游故障，不使用preview/网络替身返回|打开/app→下游延迟或503→观察限定deadline→用户重试→晚响应隔离|loading有界，故障可见可重试；不误归匿名/跳login，不采用旧响应|P1 / 异常流 / 状态机|源码只读确认无deadline/误归anonymous；真实系统RED待执行，整组未验|
|T-R02 / R138-S02 重复标签页清理|实际7页均同旧会话URL，保留当前页|识别6重复页→关闭→重新盘点并核保留页|只留当前所需页，未保存输入不丢失，不多开页|P2 / 交互 / 生命周期|绑定/关闭控制超时；最新仍7，未成功清理，不虚报通过|

以上沿原70ID补子例，不增加组数、不用HTTP200代表浏览器验收。服务目录/句柄/回收责任与源码发现来源见progress R138。

## 当前测试看板（测试任务，不是开发任务）

|状态|测试组数|
|---|---:|
|已通过（仅记录版本和范围）|11|
|最新执行失败|5|
|待复测|14|
|尚未完整验证|37|
|待业务决策|2|
|支付后置|1|
|合计|70|

**已通过11组（限定证据范围）：** T-Q01当前Web工程门（R141）、T-Q02 BFF工程门、T-Q04已发布IAM工程门（当前候选另待Root完整门）、T-Q05 System工程门、T-Q08 Storage工程门、T-Q11测试工具诊断、T-C01后端会话过滤、T-C11前端流连接生命周期、T-K01连接器不显示假成功、T-B01定价纯规则、T-R01具名测试资源隔离。T-L01正常登录与T-C06真实两轮聊天的E53属于历史发布组合，本轮按相关pins已变更移回待复测，不能当当前用户入口/模型/积分通过；其他工程门也不等于完整用户能力。

**有问题且尚未关闭：** E112 Root七完整file371/371通过，E109十五及E111四具体失败在限定纯复测关闭，原失败历史保留。T-C09/C10/A05完整用户组仍待复验，当前浏览器/五过程恢复矩阵未验，不把纯测当整组通过。T-Q10当前组合仍失败；E110工具误分类修复并82回归通过不等于组合发布/checkpoint通过。E75标准报告、BFF契约lint4warning及正式收费待验保留。

**计划完整度：** 70组均已在下方“逐组执行用例计划”展开前置、编号步骤、预期、权限/异常/恢复分支和证据要求。具体当次测试账号、fixture ID、命令/节点及版本须执行前绑定；展开计划不是执行结果。每组须沿原ID展开子用例：前置数据、操作、预期、实际结果、证据/版本、缺陷、修复提交及Root复测。先覆盖正向，再补权限/错误、重复/并发、取消/断线/刷新/恢复；必需分支未验或跳过不得整组通过。原T-C09.1–5保持编号与证据；所有组在同页维护，不新增第二测试计划中心。

**待决策：** T-C05项目移动/归档/删除的关联生命周期；T-B07失败/取消/部分输出/未知成本的收费资格。接续优先正式Agent→BFF→Web消费与当前登录/聊天/刷新，再验证项目和独立会话、Home/输入框、Skills/MCP/过程交互、任务/作品，最后正式积分链与支付后置项。

## R137 / E116 最新界面验收状态

Root桌面+移动同三场景六浏览器节点全部通过；闭合额外forming回答框、首token空窗、审批终态工具仍running三个具体UI缺陷。保持1正文streaming/0第二forming/无空窗，Approve与Reject均实际展开活动核可见终态并有截图。没有新增unit/mock/网络返回替身；明确开发预览而非真实owner组合。原失败保留，完整证据见progress E114–116。

原T-U04/T-A04整组尚未完整正式验收，不提升整组通过；下一正式发布/当前用户旅程与深层恢复、正规积分。当前完整工程门原12347当时运行，现已自然exit1，见E117，观察超时不重启；不能拿E113旧门证明本次源修改后的完整门。以下E114表保存最初失败，最新子例复测以本节为准。

## R137 / E114 系统界面交互实际失败与复测卡（2026-10-03）

执行环境：Root Node22/真实桌面Chromium，现完整Web页面及既有开发预览交互。没有unit/mock函数、网络返回替身、事件注入、sleep/控制时钟；观察器仅记录实际DOM。开发预览不证明正式IAM/BFF/provider/Billing链，三个案例不新增顶层测试组。当前Root实测0通过/3失败/0跳过，原判定保持待修复→复测。

|用例ID/标题|预置条件|测试步骤|预期结果|优先级/类型|实际结果与后继|
|---|---|---|---|---|---|
|T-U04 / E114-UI01 正文与安全过程并存的流式状态|本次自有预览Web，英文locale，空独立会话；正常消息触发现有safe Skill和正文流|①打开/app；②输入普通消息并发送；③只读观察正文初次出现时DOM；④等待完成|在途唯一正文streaming，无额外forming回答框；完成后正文完整|P1/系统交互/状态机|streamingCount=1但formingCount=1，真实失败；同writer assistant-turn修复后Root复测|
|T-A04 / E114-UI02 批准后工具状态收敛|同环境；!hitl已有完整审批，唯一safe Tool call running|①发送!hitl；②确认running；③点击Approve；④观察同工具活动终态|同活动completed、不留running；审批消费及正文结果正常|P1/系统交互/审批生命周期|仍running非completed，真实失败；preview resume同safe活动更新待修复|
|T-A04 / E114-UI03 拒绝后工具状态收敛|同上，独立新会话|①发送!hitl；②确认running；③点击Reject；④观察同活动终态|同活动failed、不留running；拒绝正文与审批消费正常，不假称真正外部工具已执行|P1/系统交互/异常状态|仍running非failed，真实失败；同切片修复及复测|

结果证据在progress E114/E115；E115批准/拒绝桌面+移动4节点复测通过，正文两节点误计滚动容器导致失败，正精确校正文范围并补首token空窗。源码修复不直接关整个组，后继6节点与完整工程门待执行。三系统用例不能代替70组当前正式用户旅程验收，状态计数仍12/5/12/38/2/1；T-Q01工程最新E113已通过但候选UI在修、整组状态待冻结复验，不能把历史失败直接擦除。

## R136 / E112 最新限定复测（2026-10-03）

Root冻结交付候选七完整file实际371通过/0失败/0跳过；E109-F01–15及E111-F01–04具体断言均在该范围通过，原19个失败记录保留历史。交付65文件hash前后保持、进程自然结束，证据见progress E112；不是浏览器/真实服务或正式发布验收。

|测试切片|最新实测状态|尚需验收|
|---|---|---|
|public7快照/安全事件与mapper|原失败限定复测通过|完整工程门、正式组合、用户展示|
|过程恢复、全值替换、分页/410/abort|原失败及四新增边界限定复测通过|深层恢复/换scope矩阵、真实浏览器刷新|
|Web全部工程门|worker自测2346通过，Root尚未重跑|Root完整check及独立终审|
|登录/真实聊天、项目/独立会话、Home/输入框、Skills/MCP/Todo/作品/积分|按原70组保持历史版本或待验状态|当前正式用户路径逐组执行|

整体70组仍12/5/12/38/2/1；保留整组最近失败状态直到完整验收，不能用371条重叠自动断言作为371个新测试任务。下方E111/E109是失败发生时的事实，最新限定复测以本节为准。

## R136 / E111 最新子用例进展（2026-10-03）

Root在停写候选独立两个完整file154pass/4fail/0skip，753源保持，当前70组状态仍12-5-12-38-2-1。E109-F10–15原六client/engine节点本次限定纯复测通过，其他9尚未Root复验；原失败历史保留，不关闭整个用户组或认定当前浏览器通过。源无正式修复commit，变更后须再验。

|本轮子用例|预期/实际|状态与后继|
|---|---|---|
|E111-F01 / D-R136-W01 / client真实裸page200|同源已解包，严格接受合法page；实际因缺data/meta解析拒绝|失败；同writer窄fix，Root复测待执行|
|E111-F02 / D-R136-W02 / 再包裹200与503 code|拒绝二次envelope、503保owner code；实际接受envelope，后继503未到达|失败；无双读/fallback，Root复测待执行|
|E111-F03 / D-R136-W03 / 初始重复身份next=null|不采用重复集合/0SSE/error；实际开1SSE，后继未达|失败；所有初始页identity gate待修复复测|
|E111-F04 / D-R136-W04 / 初始重复身份next非null|同上，不能用Set静默去重；实际开1SSE，后继未达|失败；同切片，原断言保留|

上述4测试在现client.test/engine.test，Root真实入口与manifest/版本见progress E111。正规工程门/consumer组合、真实浏览器、剩余五过程恢复及全部其他能力仍按原编号待验。R136窄GREEN已授与UI自然状态/旧keys清理继续；worker此前367/2342等自测非Root证据。

## R136 / E110 接续状态（2026-10-03，历史阶段）

已沿E109十五失败授权原Web writer正式实现public7，当前原生句柄running、源码变化中；Root复测/发布/浏览器尚未执行，状态仍12通过/5失败/12待复测/38未验/2决策/1后置。不能把“开始修复”记为通过或整组最终验收执行中。

Root独立诊断缺陷D-R136-01已关闭：npm evidence blob不可读被误报json_checks为空，真实RED1fail/4controls后，仅现分支修复，完整工具file82pass/0skip、Ruff与独立审通过。缺失blob仍拒、empty/non-list仍拒；T-Q10实际组合失败与inventory/gitlink未更新，整体状态不变。完整版本/命令/日志见progress E110；不是Web或产品复测。E109十五节点继续待修复/Root复测，下面当次事实保留。

## R135 / E109 最新Web测试结果（2026-10-03，历史执行阶段）

当前 **70组：12通过 / 5失败 / 12待复测 / 38未验 / 2业务决策 / 1支付后置**。没有整组最终验收执行中；Web负责人已交测试并停写，源码修复尚未授权。计划完整不等于全部执行，历史通过保留版本边界。

|测试子项/缺陷|实际结果|任务归属与下一动作|
|---|---|---|
|D-R135-01 public7快照和安全事件消费|合法execution_process及safe CUSTOM未正确接受，旧raw事件未拒绝|T-Q01；Web owner按正式BFF7消费，保正负控制，Root复测|
|D-R135-02 过程恢复与全值替换|snapshot恢复无executionProcess，activity整体替换状态缺失；终态过程未恢复|T-C09/T-A05；实现正式水合，补A→B→A′顺序与正文不变控制|
|D-R135-03 页耗尽后续流与过期恢复|未发过程分页请求，410未取得新快照；深层页集合/SSE断言尚未到达|T-C10/T-C09/T-A05；同W页耗尽后续流，有限410恢复；重复cursor/身份错误待实跑|
|D-R135-04 取消与scope隔离|snapshot请求signal未传递，dispose未观察真实abort|T-C09/T-A05；真实abort并保护代际，补换scope后迟成功/迟失败控制|

Root Node22实际七文件367项 **352通过/15失败/0跳过、自然exit1**；不是浏览器/PG/真实模型测试。此前九文件397通过是未加新目标的行为基线，和本次重复范围不相加。冻结752文件前后保持，所有测试进程终态，无新服务或共享数据操作。Web基线ddd38c5+四设计文档/八测试候选，生产/pin仍BFF6；正式BFF7 a68cbe5已发布。独立有效性审0P0/0P1/1P2，首次位置控制待补；完整命令、manifest/hash见progress E109。

**未执行分支：** 当前组合浏览器正规登录/两轮聊天/活动刷新，五过程暂停点、权限/错误分页/循环cursor/重复410/换scope迟到响应，项目与独立会话、独立定时任务、Home/输入框布局、Skills/MCP、文件作品及正规积分链。按既有70组编号继续，不用“代码已写”或旧测试数量关闭它们。

### E109 十五个实际失败节点（本轮运行编号，不新增顶层测试组）

共同前置：Webddd38c5+冻结752文件、BFF public7正式契约；状态均为**失败/待修复，修复commit无、Root复测未执行**。352通过节点的完整名称与实际结果保留在E109 vitest.log，不以此推出更深分支通过。以下英文标题对应仓内测试节点，可按文件与标题直接复跑；聚合缺陷与owner见上表。

|编号|文件（Web仓内）/实际节点|缺陷|
|---|---|---|
|E109-F01|tests/core/hydration.test.ts / restores selected process independently from a queued successor head|D-R135-02|
|E109-F02|tests/core/reducer.test.ts / replaces a safe activity as a whole while preserving its first position|D-R135-02；首次位置深层控制待补|
|E109-F03|tests/contract/agui-events.test.ts / accepts whole-value Skill updates and rejects inherited failed-only fields|D-R135-01；合法接收首断言失败，后继拒绝分支未到达|
|E109-F04|tests/contract/agui-events.test.ts / rejects old raw process aliases instead of accepting a second wire|D-R135-01|
|E109-F05|tests/contract/chat.test.ts / accepts the required nullable process without making messages required|D-R135-01|
|E109-F06|tests/contract/chat.test.ts / distinguishes unobserved todos from an explicit ordered clear|D-R135-01；合法process首断言失败|
|E109-F07|tests/contract/chat.test.ts / accepts the closed safe tool activity and rejects raw private fields|D-R135-01；合法接收首断言失败，raw拒绝分支待到达|
|E109-F08|tests/contract/chat.test.ts / counts todo content by Unicode scalar and enforces the Skill conditional shape|D-R135-01；合法接收首断言失败，边界分支待到达|
|E109-F09|tests/engine/agui-event-mapper.test.ts / maps safe activity as process state without emitting UIMessage text|D-R135-01/02|
|E109-F10|tests/engine/client.test.ts / accepts the public7 required nullable snapshot process|D-R135-01|
|E109-F11|tests/engine/client.test.ts / propagates an AbortSignal to the real snapshot request|D-R135-04|
|E109-F12|tests/engine/engine.test.ts / exhausts one anchored process page before opening the stream|D-R135-03；页调用首断言失败，resolve后集合/续流待到达|
|E109-F13|tests/engine/engine.test.ts / aborts an in-flight process page when scope is disposed|D-R135-04|
|E109-F14|tests/engine/engine.test.ts / discards an expired anchored page and performs one bounded fresh snapshot|D-R135-03|
|E109-F15|tests/engine/engine.test.ts / restores a terminal process without inventing a live subscription when no head exists|D-R135-02|

## R134 / E108 历史验收与正式切片发布（2026-10-03）

当前 **70组：13通过 / 1失败 / 12待复测 / 41未验 / 2业务决策阻塞 / 1支付后置**。这不是产品完成率；通过行也仅限其具名版本与范围。70原ID与70编号用例计划不改、不漏，历史RED保留。

|本次实际验证|结果|测试状态影响|
|---|---|---|
|BFF真实PG/HTTP三个资源文件|完整74/74，0失败/0跳过；另焦点15/15与其重叠，不相加|E107 Todo缺帧、activity跨anchor provenance、真实partial-GC三具体失败关闭；T-A05/T-C10整组仍未验|
|BFF默认纯门与四pure|默认736通过/1既定PG schema资源跳过；四pure149通过，范围重叠|资源skip另归T-Q12，非通过|
|完整format、lint、typecheck、build及contract pipeline|全部exit0；233 contract通过/0跳过，包含全部37变更TS/MJS格式；4条lint warning保留|T-Q02限定工程门通过；不代替全部BFF资源或产品E2E|
|正式BFF owner发布|main `a68cbe55cde709f9b21f3d5803bfbd3ca5d14e2b`；普通push后独立远端main同SHA、本仓clean|Agent HTTP5/public7切片发布；Web仍ddd38c5/BFF6，Root gitlink组合待接续，不称消费者已打通|

所有Root运行自然终态、源码保持，自有库独立确认不存在、Redis自有marker移除且空，无共享reset/重复服务。期间timestamp双new Date、权限fixture受umask影响及public7示例缺字段各经历真实失败→窄修→复测；不删原失败或放宽生产安全。两限定源码独立终审均0/0/0。准确命令、环境、manifest/hash与版本映射见[progress.md E108](progress.md)。

**下一验收批次：** Web正式消费public7，先同snapshot锚定页耗尽再续流，随后浏览器验证正规登录→两轮真实聊天→活动/终态刷新→Todo/Skill/tool/审批恢复，再逐组项目/独立会话/任务/Home/文件/Skills/MCP和正规积分。该批次尚未通过；支付渠道最后。下面E107及更早仅历史，不能覆盖本次结果。

## R128 / E107 最新实际资源结果（2026-10-02执行，2026-10-03核对）

Root真实执行三个资源文件：**74项71通过/3失败/0跳过**，其中原71项全部通过，新增3项全部明确失败；焦点14项11通过/3失败，和完整回归重叠，不相加。projection46/46、HTTP12/15、chat-facts13/13。BFF main02276b6+冻结候选，尚未正式发布或被Web消费。

|缺陷|实际结果|所属测试组|当前处理|
|---|---|---|---|
|Todo来源缺帧|应拒绝损坏过程503，实际返回200|T-A05|R129原BFF owner修复，Root复测待执行|
|activity跨锚完整性|当前latest大于旧anchor且其来源帧缺失，应503，实际200；first缺帧503正控已到达|T-A05|同一完整性切片；后续身份与恢复矩阵未完整到达|
|真实分批GC|旧Run START被实际batch1回收、terminal anchor尚存，应410过期，实际404|T-C10|R129修退休过程保留与过期判定；后续unknownRun/当前Run/全回收控制待达|

新RED源冻结hash9a8e19db，manifest8d1e3baa；准确绝对路径/命令/清理见progress E107。源码未被测试改动、全部子进程自然终态、临时库另连接确认不存在、自有Redis marker移除且空。独立有效性审0P0/0P1/1P2，P2为恢复finally可能覆盖首因，随R129修复保真。旧SQL首阻断及错误fixture/跨请求request_id/跨tenant错预期均已限定复测关闭，不靠改生产权限放宽门禁。

当前70组 **12通过/3失败/13待复测/39未验/2决策/1支付后置**。本次核对并记录已运行结果，不宣称刚完成新的产品实跑；开发修复交付后仍须Root原例和回归。下面E106及更早保留历史。

## R128 / E106 当前实际修复与测试进展（2026-10-02）

Root实际修复验收：只一列CTE修复后同11+71资源9/2及65/6，fixture/每请求request_id错断言纠正后再执行10/1及70/1，所有skip/cancel均0。projection完整46/46、chat-facts13/13、HTTP11/12；唯一HTTP失败是cross-tenant预期404，而生产固定tenant准入合法403 product_tenant_forbidden，保same-tenant other subject与foreignRun404。该错预期已授最小修正但尚未Root新复测，不能宣称71/71。

原42703、subject未注册/START process缺失fixture、第二不同START错成功预期及跨请求request_id错相等均经真实用例复测限定关闭；T-C07/C09/C10/A05因此回未验，不上调完整用户组通过。最新70组12通过/1失败/13待复测/41未验/2决策/1后置。新provenance/GC三节点正在补有效RED，源尚冻结；页面cursor发行链P1已撤（不是新增server页状态/secret）。E105契约工具失败及其他owner/浏览器/正式积分未验保持。

Root原两资源session65132/3768皆自然终态，自有库独立absent、Redis自有marker删除且空、源保持、forced/cleanup空，未重启共享服务。完整证据见progress E106，版本BFF02276b6+冻结候选未发布。

## R127 / E105 本轮Root工具回归（2026-10-02）

Root实际执行 `python3 -m pytest scripts/tests -q`，自然终态exit1：1709通过/1失败/3跳过，另455 subtests通过，118.12秒。失败为 `test_w1e_iam07_bff_pin_marks_iam_composition_pending`：当前checkpoint校验返回217项不匹配，首项历史证据gitlink `17c73541ae5d9f123d85cf531a79503df5c463bd` 与当前正式Agent `79bf98c5aa63b9bace207afdf42d8c7aefee4fe8` 不符。T-Q10由待复测转失败；尚未裁定全部217项均为过期证据，不放宽门禁或称已修复。3个跳过仍非通过。

最新70组：12通过/5失败/13待复测/37未验/2决策/1后置。E104产品资源与E105工具检查分别记录，不相加成产品完成数量。本轮没有业务源码修改；测试工具进程已结束，无本轮后台遗留。

## R127 / E104 当前测试结果与问题（2026-10-02）

测试计划70原ID与70逐组编号计划已展开；计划完成不等于测试完成。当前候选BFF main `02276b623f8390288fbf86d6efaa0f5152256afa` + 27路径未提交实现，冻结hash `bbe0b6f24242d7248076e879eda2f6c37e8eb08732fc6b7e408d69ee2986d9f4`，不是正式发布组合。

|实际执行范围|结果|验收边界|
|---|---|---|
|Root build/生成/lint/typecheck、四pure|四pure149通过/0失败/0跳过，四静态步骤exit0|strict HTTP5消费切片；非浏览器或真实模型|
|Root完整默认纯门|736通过/0失败/1 PG schema跳过|原五pure缺陷关闭；必需资源另验，T-Q02待复测|
|真实PG/HTTP焦点11项|4通过/7失败/0跳过|第二START拒绝及精确重放、Todo非空约束和空表正控、SQL fault事务回滚、会话删除过程行通过；其余被42703/503阻断|
|真实三个资源文件完整回归71项|43通过/28失败/0跳过|与焦点重叠，不相加；主失败为SQL42703/HTTP503，另PROCESS_PROJECTION_UNAVAILABLE/AGUI_PROCESS_SUBJECT_MISSING待逐项定位|
|当前浏览器/全部owner/正式积分与真实网关|未验|不由默认绿色或子代理完成报告替代|

当前实跑缺陷 `D-R127-01`：过程页SQL引用CTE未输出的 `positioned.latest_sequence`，导致snapshot失败，BFF owner负责；修复未交付、Root复测未执行。独立只读审另报 `D-R127-02` 分批GC历史过程过期语义、`D-R127-03` compact↔ledger/provenance完整性、`D-R127-04` cursor边界校验疑点，尚待Root裁决与有效行为验证，不算额外已运行失败。原历史失败保留，修复不能直接关闭测试。

全部自有进程自然终态，源hash保持，精确临时库另连接确认不存在，Redis自有marker删除且空、cleanup_errors与forced_stop均空。详细命令、manifest与hash见progress.md E104；未重启共享服务或清共享数据。

## R124 / E101 当前消费修复复测（2026-10-02）

Root独立冻结新候选六步：build/Agent正规双次生成18files/lint/typecheck均exit0；四pure149pass/0fail/0skip（原148+新fatal UTF8节点），完整package默认732项731pass/0fail/1既定PG schema skip。skip另归T-Q12，不记资源通过。另format、两个新file format、public合同lint/semantic均0，合同lint2既有warning保留。440路径前后保持、owned child自然终态/forced_stop空，独立终审0/0/0；原default机械旧vendor测试路径失败08af2db0保留，仅正式owner路径更新后重跑。

已关闭的是HTTP5合法Todo/Skill/tool/subagent strict消费及旧raw/非法payload拒绝的E100具体缺陷。public7、SQL compact、START保存、锚定分页/GC、Web正式消费与浏览器均未验；生产候选尚未正式发布，保留T-Q02待复测与T-A01–03/A06未验。下一R124-RED-B同owner只写七tests，Root执行真实资源，不以14拟用例或worker完成声明增加通过数。

## R126 / E103 当前明确RED与实现阶段（2026-10-02）

Root真实重跑现九资源节点：9显式失败/0跳过/0cancel，缺process/table/route为当前首RED，无旧undefined TypeError；同自有库canonical安装成功，438实际源保持/全部进程自然终态/精确回收。RR并发、GC锁后重查、101锚定变更、historical及fault重试/provenance恢复断言已补入现用例，但尚被首RED阻断，不计深层通过。新增contract snapshot4字段与page5字段已按D0校正。

同owner正在完整GREEN-C实现，后继Root真实资源跑到深层、正式发布和Web浏览器验收；不将编写/实施当测试完成，70组状态不变。最新manifest与失败保留在progress.md E103。

## R125 / E102 当前过程恢复测试（2026-10-02）

Root独立现四pure文件108项102通过/5新增行为失败/1既定PG schema skip，build0、440路径保持/自然终态。实际失败为public7版本/operation inventory、snapshot缺required execution_process、canonical两过程表未实现及旧tool_call_ids未删；T-Q02记最新失败，不将预期RED当产品通过。

Root另真正运行三个资源文件现9节点：0pass/9fail/0skip，当前canonical安装成功；精确自有库已回收并新连接确认absent、Redis自有marker已删且空、438实际源保持、所有进程组自然终态/forced空。旧cache/缺表显式断言与HTTP503前置已记录，但三缺process TypeError及fault/delete缺表不当深层行为证明；RR并发、101锚定深层、GC锁后重查、historical/expiry/rollback仍未到达。原私有runner漏USER的准入失败450f6894保留，不算产品测试；仅修runner后重跑e33547f6，不改角色/共享资源。

Root已续派原owner R125-RED-B-STRENGTH三个资源测试补显式首断言与真实并发/恢复正控；尚未交付。完整用户路径仍未闭环，下一Root有效资源RED→既定GREEN-C public7/SQL/START/GC→正式BFF/Web消费→真实浏览器。70组12通过/1最新失败/13待复测/41未验/2决策/1后置。

## R123 / E100 BFF消费真实RED（历史；已由E101限定复测）（2026-10-02）

Root独立Node22 build exit0，四现pure files实际148项：120pass、28fail、0skip；28全部是HTTP5消费行为缺口，不是导入、工具或测试自身错误，独立spec/quality审0/0/0。436文件保持、两个child自然终态、forced_stop空，仅测试自有回环HTTP，不访问PG/Redis/provider/浏览器。当前T-Q02、T-A01–03/A06转失败，其余当前组状态不扩充。同owner四D0澄清已交付；下一strict decoder/安全CUSTOM修复→Root复测；SQL/分页/浏览器后继分开验。

测试计划本次补齐70组结构化编号用例；尚待执行的保持原状态。当前组计数12/5/0/13/37/2/1，不与E100前核对混读。

## R123 测试任务核对（E100前的历史状态，2026-10-02）

Root实读当前矩阵，70行/70唯一ID，状态计数与看板一致；只读审查也确认上述范围。发现页头、重复完成度摘要、下一批次及T-Q03行混有旧状态，已校正当前段落；旧失败/运行证据保留，不作为最新失败。此次没有新增产品测试结果。

开发派工的R123 BFF四份设计文档及HTTP5消费清单已交付待Root审查，**不计测试完成**。每个测试组仍需按稳定ID展开子用例：前置/账号 → 操作 → 预期 → 实际/证据 → 缺陷及修复版本 → Root复测；尚未展开的用例保持未验。当前仅T-C09有明确逐步子用例表，完整逐用例计划仍需补齐，不以70组目录冒称完成。

## R122 当前资源测试增量（2026-10-02）

E97：当前新wheel的installed CLI fresh/重复拒绝/catalog及六漂移真实PG回滚通过，Root8实际步骤、21表/206列/216constraints/42indexes，owned库精确回收并另连接确认不存在；源371保持/venv删除/进程终态。初次cache工具失败保留后新runner复验，不当产品缺陷。T-Q03仍待复测，T-Q12全部owner同应用库schema仍未验；不由单包DDL推导整体闭环。E98随后同currentwheel installed HTTP真实36pass/0skip，已装origin与精确清理通过；不是外部provider/E2E或console进程，Agent当前59路径已正式提交/推送79bf98c并远端核验；正式BFF/Web消费者仍未验。

## R121 当前测试增量（2026-10-02）

E95：Root独立当前1960纯nodes **1960通过/0失败/0跳过**、七静态门0，独立三路径审0/0/0；原E93 inline-ignore失败关闭，T-Q03转待复测，资源/安装HTTP/发布消费者分支仍未验。worker报告命名Root不当Root独立结果，使用本次Root自有manifest/进程证据。

E96：当前源码新wheel/sdist与115完整runtime依赖安装十步全0，仓外origin/RECORD/实际CLI、371源保持/私有venv删除；同新artifact的sdist重建/四布局64负向矩阵已由Root终态完成：219步骤全0、重建entry bytes一致、篡改拒绝/恢复通过、371源保持、私有安装目录删除；记录E96当前manifest。仍不包含installed HTTP/真实backend/发布消费者。历史包结果不替当前包，也不称整个Agent/用户链通过。

70组当前 **13通过 / 0失败 / 13待复测 / 41未验 / 2决策阻塞 / 1支付后置**；0整组最终验收执行中，当前安装矩阵已结束。失败历史、修复与Root重跑证据全部保留在progress.md E95/E96，详细既有ID不变。

## R120 实跑增量（覆盖下方人类状态核对）

E93：Root四file213pass(5真实资源未选)、runtime104pass/七静态0，原7RED/control逐项GREEN；随后完整当前1960纯节点实际1959pass/1fail/0skip，失败为新测试两inline type-ignore违反现工程门。原生命周期失败已有限关闭，但T-Q03整组仍失败；原owner限两test/必要worker/main内部命名修复，不改检查器/豁免清单。

E94：Storage完整默认491pass/156PG skip/0fail，format/lint/type/build、contractcheck/Prisma validate/generate/正规normalize通过；最终280源/17generated原bytes/clean。独立证据终审7d8eaee1为0P0/0P1，T-Q08限定工程门已验收；156PG另归T-Q12、外部S3/scanner/全部文件用户路径T-F01–05仍未验。工具层与私有guard误拒owned EADDRINUSE的失败历史保留，不当产品缺陷。

测试70组当前**13通过/1失败/12待复测/41未验/2阻塞/1后置**；新增通过为T-Q08 Storage限定工程门，不代表完整Storage业务链。具体pass/fail/skip、hash与进程/资源回收见progress.md E93/E94。修复待Root复验，未将子代理报告或派工提升为通过。

## R120 人类测试计划核对（历史阶段；后续实跑见上方）

本次明确区分：**开发交付 ≠ 测试通过；测试组目录齐全 ≠ 逐用例计划全部展开；历史版本通过 ≠ 当前完整组合通过。** 测试计划继续只维护在本页，70组ID保持，子仓自动测试留本仓；不将开发task当验收清单。

Root实际逐行核对70唯一组：12通过、1失败、13待复测、41未验、2决策阻塞、1支付后置；0整组最终验收执行中。所有“通过”仍绑定原行版本及范围，不推算产品完成百分比。当前完整浏览器旅程未验。

- **T-Q03 Agent：修复已交付、待Root复测。** Root本次实际核对9源/4测试/3设计共16路径与交付manifest hash一致；独立源码终审报告为0P0/0P1/0P2，仅该冻结生命周期切片。owner报告213四文件测试及91 runtime测试不是Root运行证据，原E92失败保留，整组仍失败。下一动作按task.md的R120-AGENT-GREEN-ROOT复验，真实资源/进程/发布消费者分支另待验。
- **T-Q08 Storage：待复测。** 准入尝试止于pnpm工具层，未跑业务测试；不记产品失败或通过。严格诊断方案已查本机源码，尚未执行验证。
- **T-C09：后端子项已验、完整用户组未验。** E91同事务四事实快照与replay、完整投影文件39通过保留；浏览器刷新与完整过程恢复尚待执行。

每个子用例必须保留 `步骤/预期 → 实际结果 → 缺陷 → 修复提交 → Root复测 → 证据/版本`。修复不覆盖原失败，跳过不算通过。其余尚未展开的组须先补正向、负向、并发和恢复步骤再执行；“完整测试用例计划已完成”目前不成立。

## R119 测试增量（整组状态不变）

E92：Root在当前冻结Agent候选独立精确6失败/1转交正控通过/0跳过。失败为resume/recovery未转交handle泄漏、blocked construction不被drain等待、Docker半构造client/new container泄漏；542文件保持、0资源、自然终态。独立RED/三设计门接受，原owner正在九现源GREEN，修复尚未Root复测，T-Q03保持失败。

Web静态审发现Todo正式source、Skill过程契约、普通安全过程硬刷新三缺口，T-A01–06保持未验；不是新增实跑失败数。当前右侧浏览器CDP读取两次超时，3310实际无listener/HTTP拒连；本次未得到DOM/截图或执行用户动作，T-U/T-C09浏览器分支未验。不得拿旧标签/截图、历史登录或子代理报告替代当前验收。详细证据只记录progress.md E92，派工只记录task.md。

## R118 测试进度速览（历史阶段；当前见R120）

|状态|任务组数|含义|
|---|---:|---|
|通过|12|仅各行具名版本与必需分支验收通过，不代表整个产品已完成|
|失败|1|T-Q03 Agent：资源生命周期缺陷已复现，候选修复尚未Root验收|
|执行中|0|没有整组进入最终验收；局部实施/补测试不计整组通过|
|待复测|13|有历史结果，但当前组合仍需重跑|
|未验|41|尚无本组完整必需分支的验收证据；部分已有通过切片|
|待决策|2|T-C05项目生命周期；T-B07失败/取消/部分输出/未知成本收费策略|
|后置|1|T-B08支付渠道，按用户要求最后处理|

**已通过的12组：** T-Q01 Web工程门、T-Q02 BFF工程门、T-Q04 IAM工程门、T-Q05 System工程门、T-Q11聊天测试工具诊断、T-L01正规登录正向、T-C01后端会话过滤、T-C06正式两轮真实模型聊天（E53历史发布组合/本地模型）、T-C11前端流连接生命周期、T-K01连接器不显示假成功、T-B01定价纯规则、T-R01具名测试资源隔离。版本/局部边界以矩阵为准；不据此宣称当前浏览器、真实扣款或全部Skills/MCP能力通过。

最新增量：E91 BFF新快照组合例1通过、完整投影文件39通过，限定T-C09.1–3后端证据；T-C09浏览器/完整用户路径仍未验。Agent原七源候选已交但仍有独立审查指出的生命周期缺口，T-Q03保留失败。整体研发与测试闭环尚未完成。

### 逐用例记录与缺陷闭环

本页70组都有编号执行计划，**计划已展开不等于测试已执行**。执行前绑定实际账号、版本、资源ID和命令/测试节点；执行后逐子用例登记实际结果、缺陷和复测证据。T-C09已有逐项结果，其余以本页矩阵及progress具名证据为准，不用整组标签推定所有子例通过。沿现组ID维护，不另建计划中心；owner自动测试继续留在各自仓。

每个具体子用例登记：`测试ID/业务路径 → owner与执行人 → commit或冻结hash及环境 → 前置条件/测试数据 → 操作步骤/预期结果 → 实际结果/pass-fail-skip → 日志或截图证据 → 缺陷与修复提交 → Root复测结果/日期`。未执行明确写未验，skip必须说明；修复完成后仍待复测，原失败保留。涉及真实用户路径还需真实浏览器证据，不用单测或截图外观替代功能验收。

接续顺序：Agent当前资源生命周期失败修复与Root复验 → 当前正式owner组合/登录聊天及刷新 → 会话与项目独立交互、Home/输入框 → Skills/MCP/Todo/HITL、定时任务和文件作品 → 正式积分链与最终组合验收；独立切片按既有owner任务卡并行，支付最后。任务依赖和派工仍维护task.md，实跑证据仍维护progress.md。

## R118 / T-C09 当前组合并发验收步骤（后端切片已验，用户全组未验）

本组原E53活动刷新证据保留，但不当四事实原子性证明。R117只读审ddade487确认现RR实现同client；原R43与R57分别未同时断言安全过程或Message。原BFF负责人只补现integration测试，Root独占真实资源执行E90失败与E91复测：新增1/1、完整projection file39/39且0skip，当前test SHA01ae22f3 / BFF本地main02276b6；这是已实现RR行为的组合证据，不是新增生产修复或浏览器通过。原失败为测试预期缺合法AGUI元数据，仅补精确全envelope后重跑，失败历史保留。

|子项|操作与预期|当前结果|
|---|---|---|
|T-C09.1 同次授权快照|真实提交并admit Run，production ingest建立非空assistant与完整waiting revision；可信owner读到Message、同Run waiting head、全部pause items、非空opaque watermark，身份/内容/状态逐项锁定|E91新增真实组合例通过；既有分段正控未拼接冒充|
|T-C09.2 并发旧集合|同一真实RR reader在Conversation授权后暂停；另一连接以同一production ingest事务提交Message更新与合法完整interaction新revision。writer必须真正完成commit，随后释放reader；旧读四事实全部等于旧集合，不出现新Message+旧过程或旧Message+新cursor|E91同一真实并发实例通过；未mock结果或拆两次证明|
|T-C09.3 新集合与续流|提交后fresh snapshot四事实全部为新集合，Message identity与Run不变、内容确有推进、状态正确、完整revision无merge/丢item，watermark变化；从旧opaque cursor生产replay精确包含本批公开frames，直到fresh watermark，无缺漏/重复|E91同例通过，精确含新delta/full CUSTOM全envelope；只现BFF，未消费Agent新候选|
|T-C09.4 回收与有效性|reader、pending promise、store与pool在失败/成功都结束，真实等待barrier有界；全file无必需skip，仓内非目标hash保持，Root自有fixture库精确清理。移除RR或Message拆到第二连接应使组合断言失败，后继可隔离验证变异而不改正式源码|E91正常fixture结束/PGID自然终态/库精确清理/源保持通过；隔离变异未执行，不能记本子项所有分支通过|
|T-C09.5 用户刷新展示|正式发布组合浏览器验证文本、head、完整过程及同watermark恢复，waiting/resuming/active/terminal与断线/重挂覆盖；旧数据不串项目或其他会话|未验；BFF组合例即使通过也不关闭本项或整个T-C09|

## R117 接续实际结果（2026-10-02，历史阶段）

新增E88：System真实现Nest HTTP/PG/Redis lifecycle完整19通过/0跳过，14自有fixture库原测试精确清理且独立不存在；包含schema隔离/漂移、HTTP deadline与无late commit、启动失败/握手drain。只本owner切片，不关闭全部T-S01/T-R02/T-Q12；Node24.20实际版本与197源hash绑定，Redis仅连接/PING非业务key恢复。

新增E89：Root独立完整Factory file2失败/54通过/0跳过，锁真实backend构造自然终态与partial swarm close=0、原异常/state正控。三面文档/契约门核后原owner已实际开始七现源GREEN；尚无交付/修复验收。当前70组12/1/0/13/41/2/1不变，失败保留，详细命令/hash/环境失败与回收见progress.md，不以子agent派工或新增断言充完成数。

## R117 测试进度核对（2026-10-02，历史阶段）

70稳定测试组现 **12通过 / 1失败 / 0整组执行中 / 13待复测 / 41未验 / 2决策阻塞 / 1支付后置**。这是测试验收状态，不是开发完成率。已通过的版本与范围见各行，其他必需分支继续待验；详细用例尚未展开的组必须先补操作步骤/预期与负例，70行能力目录不等于完整测试已经执行。

**E87 / T-Q03：新增生产客户端释放缺陷已由Root真实复现，整组从待复测转失败。** 原owner交付tests-only，Root独立执行精确新回归及既有正控：1失败/1通过/0跳过，失败为任务自然完成后自建S3客户端close次数0、预期1；不是导入或网络错误。生产源码未修改，尚未修复。测试注入预建真实backend，因此不覆盖生产backend构造；未接入执行路径的caller-owned对象不算有效正控，完成事件快照不证明进行中native任务排空。记录这些测试覆盖缺口，不扩大RED结论。实际命令、hash、守卫与终态证据见progress.md的E87。

R116安装/负向包/单owner数据库切片已完成；下一补齐本片有效控制与资源所有权回归、修复后Root复测，再推进尚未通过的正式组合和用户交互。整体规范E75的152条报告仍未关闭。完整Wave0–7尚未闭环，支付最后。

## R116 当前推进（2026-10-02，历史）

本轮新增实际证据E84–86：当前候选重建包十步安装门全0；source-wheel已安装CLI首次成功/重复拒绝，21表/206列/216constraints/42index definitions与规范一致，六recipe漂移拒绝及rollback、自有fixture库精确回收通过。完整115依赖/370源冻结，原WIN03 idle，没有共享服务重启。详细manifest/hash/实际失败历史与边界仅维护在progress.md的R116，不再在每份文档复制完整运行日志。

70稳定测试组仍 **12通过 / 0失败 / 0整组执行中 / 14待复测 / 41未验 / 2决策阻塞 / 1支付后置**。T-Q03仍待复测；E86当前四布局64真实安装负例/219步骤已由Root79158终态通过，installed HTTP/S3/Docker/生产archiver close/HTTP5发布消费者、全部owner同库schema与完整用户能力尚未闭环。当前DDL只覆盖source-wheel venv及所列catalog属性/六漂移，不将其当全部数据库恢复或四布局DDL门。父级admin SQL包络有界性后继待验，E75标准152规则报告仍在。完整Wave0–7保持active，支付最后。

R116核心安装负向独立终审已接受（57ba751a / P0P1P2=0）；详细证据见progress.md。原source writer仍待按R117 RED授权接续，不将任务卡当运行完成。

## R115 当前验收推进（2026-10-02）

上一goal回合为progress：Rootc2eebe91提交测试台账。本波真正实施、复测并提交自洽子仓切片，完整Wave0–7保持active。70稳定组现 **12通过 / 0失败 / 0整组执行中 / 14待复测 / 41未验 / 2决策阻塞 / 1支付后置**；T-Q03从失败转待复测，不提升为完整Agent通过。本节覆盖下方历史摘要。

- **E80 / T-Q03 配置GREEN：** Root完整file11pass/0fail/0skip/resource0，Ruffformat/check/Pyright各0，8文件hash保持；manifest `/tmp/kokoro-r115-agent-example-root.json` SHA95b4ef5bc8719ee535f6f013e67b030b3992f1c44815859ffae11ca21b1746ab。独立审2a18fb4f为0/0/0；原E78缺文件失败关闭。Agent本地main提交`dbaf4f9`（新owner YAML、README/INDEX、现测试）。Root工作树旧Agent样本已删、README精确改指owner，不保留双轨；Root组合提交/远端发布另记，不将工作树收敛冒称fresh clone验收。
- **E81 / T-Q05 System切片：** Root重跑原十纯门全0，unit98/contract12/architecture9合计119pass/0skip、197tracked保持/owned终态，manifest `/tmp/kokoro-r115b-system-pure-root.json` SHAcb0dc907c96d41023bfc4e03f381ea814e486ab05903f928ca29cfb6fd0e35ec。最初临时HOME缺Corepack缓存而registry ENOTFOUND退出1保留为验证环境失败（ff5e414b），后续显式复用原pnpm12.3.4缓存并禁网，不改依赖或放宽门禁。同源码E77真实PG23断言22表证据复核，非本轮重跑PG；独立源码审31519cb2为0/0/0。System本地main提交`9a4e98e`，仅fresh脚本/现测试/CURRENT，自身工作树干净；业务HTTP/Redis/runtime与全owner组合未验。
- **E82 / T-Q03、T-R02 fixture RED→GREEN：** Root先真实2call fail/0skip/blocked0，manifest `/tmp/kokoro-r115-webfetch-red-root.json` SHA968849291e5d904863d579ee0bb7b8ca90cacd0b50a0924d60fe991621de7e60，原RED审603aa94d。原owner只在现base_url加try/finally、shutdown/server_close/join，全部原业务断言与新增回归保持。Root完整file17pass+Ruff/类型四门0，manifest `/tmp/kokoro-r115-webfetch-file-root.json` SHA6513cf7ff1dd8c318c854f19b286c8de77f60458ad5128f6db3af248b2091898；原170+新增2项local Root172pass/0skip/blocked0，336hash保持、28child/170thread终态、87端口回绑、98socket forced_close=0、仓内/私有fixture残留0，manifest `/tmp/kokoro-r115-agent-local-root.json` SHA9420b6486a1f7321f71ad6dc83901f68cbf2e88a6e97c2b72bb34bd47e7768c0。独立终审463f927f为0/0/0，原E79生命周期P1关闭；Agent本地main提交`2653bcc`，仅现fixture测试文件，不混入HTTP5/Todo/contract/锁候选。handler请求异常片段保留，不冒称stderr完全无异常。
- **E83 / T-Q03 当前pure：** Root原1937节点全部1937pass/0fail/0skip，resource_attempts0、进程组终态、370明确保护文件保持（含新YAML/helper）；manifest `/tmp/kokoro-r115-agent-pure-default-root.json` SHA3f5c1ab15b596c06bb197ce11a2ebd347f0f467b2f8e14a9f7eec74a9cfb6f2b。与E82的172在同冻结候选分别执行，不混同两次输出为单次测试；615原三方warning仍保留。配置skip及fixture回收已修，但完整负向安装/当前重建artifact/installed DDL与HTTP/S3/Docker/生产archiver close/HTTP5发布消费者仍未验，T-Q03保持待复测。

Root原42054/8470/32322/6712/16230/35603均已终态，原WIN03 GREEN turn01a0feb4-8643-7031-9456-7445bbdcd09e已completed/idle；未重复启动服务或重置共享PG/Redis。三个子仓commit均为本地提交，尚未推送；生产候选和Root uv.lock等任务外修改保持。下一沿现测试矩阵推进安装负向/installed DDL与HTTP、正式owner组合及项目/独立会话/Home/Skills/MCP/Todo/HITL/正式积分真实消费，不回头反复运行已关闭的定点门代替能力推进，支付最后。

R115收口验证：Root现三套工程/规范/拓扑工具测试实际305pass/2.57s/exit0，日志 `/tmp/kokoro-r115-root-governance.log` SHAaf2dda928d5ad17ef7acc324eb49160a21dfbb31821051e78ae943c1880d9a7a；70ID/12-0-0-14-41-2-1与历史归档suffix保持。两次Agent运行节点集合互斥、原1937+原170及新增2无重漏，保护清单交集hash同值；只称分别执行的当前2109节点分段，未伪造单次输出。工具测试绿色不改写E75整体标准扫描152规则失败，其他产品/资源门继续未验。

## R114 测试进度核对（历史）

当前70稳定测试组：**12通过 / 1失败 / 0整组执行中 / 13待复测 / 41未验 / 2决策阻塞 / 1支付后置**。不以自动化断言数量推导产品完成率，完整Wave0–7尚未闭环。本节覆盖下方R113及更早摘要；历史结果保留但不冒充当前组合验收。

- **E76 / T-Q03：安装正向切片已验。** Root实际构建source wheel和sdist，sdist重建wheel全部entry路径/内容相同；source/rebuilt wheel分别在独立venv与target四种布局安装完整115包runtime，installed origin/RECORD/contract通过，venv另有实际console与inspect。两个批次10+16步骤均exit0，临时安装目录已删除，独立终审0/0/0。原E49缺OpenAPI具体缺陷已复验关闭，不再列为当前安装错误；完整负向篡改、installed DDL/HTTP、发布/消费者与资源门尚未验。证据绑定当时冻结artifact，后续README/示例变化不冒充重建后已验。
- **E77 / T-Q12、T-R02：System单owner真实PG切片已验。** Root运行原fresh入口，23 assertions/22 tables/catalog匹配，重复安装拒绝；自有临时库已由原入口删除，独立精确查询确认不存在，197 tracked hash保持、进程组终态、独立终审0/0/0。不证明全部owner同应用库组合、Redis/业务HTTP或全组恢复。
- **E78 / T-Q03：配置示例修复待Root复测。** 原skip改为真实测试后Root10pass/1缺文件fail/0skip；原WIN03现已completed/idle交付Agent本仓示例和README/INDEX，owner报告11pass/0skip。该GREEN尚未Root独立复跑/验收，不能用worker报告关闭失败；Root旧样本删除与引用收敛也尚未实施。
- **E79 / T-Q03、T-R02：170 local测试体已验，回收缺陷未关。** Root170pass/0fail/0skip、510phase通过/blocked0，336保护文件保持、28child/168thread终态、85端口可重绑定；但web_fetch fixture漏server_close，1socket由外层守卫补偿关闭。独立审P1=1明确保留，不以测试体绿色宣称fixture生命周期正确；后继原owner tests-first修复并Root复测。
- **整体规范检查仍失败。** E75实际152条规则报告保持；R114只读分类不是修复/重新通过。当前无整组测试在跑；原WIN03仅交付待验候选，未重复启动共享服务。本次进度核对没有新跑浏览器或真实模型，不扩大E53历史发布组合的正向登录/严格两轮聊天范围。

测试计划唯一入口仍为`docs/test-cases.md`，开发派工`docs/task.md`，运行证据`docs/progress.md`，组合摘要`docs/CURRENT.md`。接续顺序：配置候选Root复验→fixture回收缺陷→Agent剩余安装/资源及owner组合门；随后逐ID验项目/独立会话与任务、Home/输入框、Skills/MCP/Todo/HITL及正式积分。T-C05项目生命周期、T-B07失败/部分输出/未知成本收费规则待对齐，T-B08支付最后。

R114本次测试进度核对补充：Root现三套工程/规范/拓扑工具测试实际305pass/2.64s/exit0（`scripts/tests/test_engineering_handbooks.py`、`test_ten_repository_standard.py`、`test_repository_topology.py`）；日志 `/tmp/kokoro-r114-test-progress-governance.log` SHAe761dd984fd133e07fc0b0e950788345352169cff73fd7b712d0e0c6bead4c57。仅工具回归与台账核对，不是本次新增业务E2E；70ID/状态及历史归档保持，任务外子仓/uv.lock不提交。

## R113 当前验收推进（历史）（2026-10-02）

上一goal回合为progress：Root c29acd6b已提交测试计划当前态与真实工具测试证据。本回合完成两个独立owner切片的实现与Root实测，完整Wave0–7不缩小。70组当前 **12通过 / 1失败 / 0整组执行中 / 13待复测 / 41未验 / 2决策阻塞 / 1支付后置**，仅恢复T-Q05当前候选限定纯门，不是产品完成率。

- E72 / T-Q05、T-Q12、T-R02：Root原14 fresh-name测试真实12fail/2control/13未选（manifestf1d3f36f）；独立审指出合法名未锁第二Client，原owner保旧assert补强后Root再次12fail/2control/13未选，197hash保持、owned进程组终态。补强RED /tmp/kokoro-r113-system-name-assert-red-root.json SHAabb63265a86364cd4d4ed8d065105de3e450b2da4f0569f284992a80e0f1817b；复审2238c848为0。仅现fresh脚本追加严格42 ASCII测试库名称输入，undefined随机、空/Unicode/换行拒绝，Client/CREATE/URL/DROP同身份、错误不回显；原SQL/23行为/cleanup原因不改，不扩数据库角色或运维。
- E73 / T-Q03：默认pure1937第一实际1930pass/6fail/1skip，5项是验证包络误拒绝原DNS而非业务错误（manifestbe8c3481）；唯一本包资源清单遗漏distribution_assets.py已Root单node真实1fail/0资源（manifestb56d95a9）后由原WIN03仅composition有限列表加一行。Root随后同1937节点实际1936pass/1skip/46.79s，369hash保持、blocked0；原5精确host/port=None原生解析允许且不改参数/返回，其余socket/PG/Redis/child拒绝与OS禁网保持。manifest /tmp/kokoro-r113-agent-pure-default-root.json SHA76c58d3a5cdd78e15c0446b99df4d90ac125b408ab47a20d361bafb44b089dce；完整Ruffformat/lint/Pyright/checker/Failure五静态门Root各0（/tmp/kokoro-r113-agent-runtime-static-root.json SHA43fc887a799ca7f9ea8084f834de103d63ca748db32b234ec14bb7b49872c8aa）。独立source终审ac2b0eae为0/0/0。原170 local、真实安装/E49仍未验，T-Q03失败不关闭。配置example缺本仓fixture造成原1skip，审计8dae2c99禁止直接指回漂移Root旧样本；615 warning为2条LangChain v3 beta与613条三方asyncio弃用，保留风险、不抹日志、不冒称零债务。
- E74 / T-Q05：原WIN05仅fresh source严格名称校验GREEN，Root99279十纯门全exit0，9files119pass/0fail/0skip（unit98/contract12/architecture9），197文件hash前后保持，各owned进程组终态，OS禁网；Rootmanifest /tmp/kokoro-r113-system-pure-root.json SHA16277868630e382dfefa2b0faad27214b6c194bd51eba0fc04757db37cbba015。独立source终审 /tmp/kokoro-r113-system-name-final-review.md SHA72e176b965682b64eb8b9ba108a6efc7fc551d8bbd7864e3179ac8e8c0cbacde，0/0/0。当前 source da4675b9/test45bd5286/helper efd2f061；只是未发布候选纯门，真实PG/Redis/fresh install/provider/runtime/image仍未验，不关闭T-Q12/T-R02。

- E75 / Root 补充规范检查：当前工作树真实运行 `python3 scripts/verify-ten-repository-standard.py` exit1，152条规则报告、0未核项；按扫描所在仓分布为Agent11、Web14、BFF37、Billing34、Platform当前物理名capability12、IAM30、Scheduler3、Storage11。包含目录/文件粒度、TypeScript严格项、HTTP/OpenAPI、SQL命名与wire边界等；扫描发现不等于152个用户功能bug，也尚未逐条裁决真实实现缺陷或检查器与当前规范的偏差。vendor契约问题须先回事实owner确认，不改生成物或放宽门禁清零。`python3 scripts/verify-repository-topology.py` exit0，仅拓扑检查通过，不证明main-only/fresh clone/完整组合或当前浏览器。manifest /tmp/kokoro-r113-root-structure-checks.json SHA6229c7ff60fdb440f2f143c8026e65c1752372a907deb729970ddc6e5163a56e；standard日志SHAd98e0e8351f03098a0f329384637762daa3a7c6e3316746c4a2253ec207367da，topology日志SHAbe9b368b505978266ed3d8321a971f15466ed3d5cce582136ff241bd94ae3c4d。原76091已终态；此补充检查不重跑或推翻具名限定纯门，T-Q10仍待完整组合复测，70组计数不变；整体标准检查失败明确保留，后继Root逐条裁决后派原owner修复与复测。

Agent/System原writer均实际completed/idle；Root执行60837/67381/99279均终态，没有新增共享服务或业务进程。worker错误路径exit4、pnpm wrapper71、初次format1各保留诊断且不当业务失败。后继按现任务：Agent本仓example去skip、170 local和真正构建/安装；System已准备可事前登记精确名称的真实fresh单门；再按owner顺序推进项目/独立任务/文件/Skills/MCP/Todo/HITL/正式积分及浏览器。两业务决策仍未定、支付最后，不将基础门替代用户能力。Root本轮源切片均按冻结hash验收，子仓依赖切片尚未完整发布，不单独提交会缺依赖的源码；保留其他候选和uv.lock。以下仅保留历史，不覆盖本摘要。

## R112 测试计划核对（历史）

测试总台账仍为 docs/test-cases.md，开发派工与测试验收分开。当前 **70组：通过11 / 失败1 / 执行中0 / 待复测14 / 未验41 / 阻塞2 / 后置1**。这是具名测试组状态，不是产品完成率；整体Wave0–7尚未闭环。本次未重新执行全部业务测试。

- E70 / T-Q03：Root13953已独立复跑Docker导入修复的十门，全部exit0；五次选定测试运行合计161通过（1 import、2 Docker纯例、15 archive、3 architecture、140相关回归）。369文件hash保持，守卫resource_attempts0，独立源码审0/0/0。只关闭E69导入副作用切片；8真实Docker、5真实S3、生产archiver关闭、完整安装仍未验。manifest /tmp/kokoro-r112-agent-docker-root.json SHA4be255d71288b46a0cc663f208631627247cdaef404e8af394408ac423d366fe；独立审 /tmp/kokoro-r112-agent-docker-green-review.md SHA186f866011c7a34b8b7c738580bf365cd74986826e7ce3569ed2619ec61b81c7。
- E71 / T-Q03：Root71108实际collect-only两门exit0：全部2408、默认2107选中/301未选，369文件hash保持、resource_attempts0。只收集用例，未执行测试体/fixture。最初强制importlib的32个support导入错误来自验证包装选择，不冒称产品失败；已恢复pyproject实际默认prepend，无修改源码/marker/PYTHONPATH。Rootmanifest /tmp/kokoro-r112-agent-full-collection-root.json SHA4a01314e6e9870170d7a42a64b0368c798ae87711a976c57da017c0738314685；原错误manifest378c73bb保留。只读分段1937 pure+170 local=2107，不重不漏，全部仍须真实执行；报告 /tmp/kokoro-r112-agent-default-partition.json SHA81914ecd0c9403f43ccda3e538c2aea44ef9ca76a9e4a59566f2976ecd02a3b4，不把分段准备当通过。
- T-Q05退回待复测：System新增fresh-name tests-only候选已停写；owner报告12失败/2正控通过/13未选，Root尚未独立复现或接受源码修复。原106纯门通过留作历史，不证明新候选。manifest /tmp/kokoro-r112-system-fresh-name-red.json SHA8c8be970c312b07ee101a701b242d00e3d6e067c64f350e713580881021eb323；源脚本366b886b仍冻结。owner初次zsh包装错误后覆盖同日志的证据缺口保留说明，后继Root须新独有日志，不补造历史输出。真实PG/Redis门未运行。

测试管理责任：Root维护同四台账、独立复测及Git；原Agent/System owner负责各自代码，审查员只读。当前无整组业务测试运行，不把owner开发或collect-only计为执行中。项目生命周期T-C05、失败收费T-B07待决策；支付T-B08后置。以下R111及更早章节仅保留当时证据，不覆盖本摘要。

R112测试台账核对终态：Root `.venv/bin/python -m pytest scripts/tests -q` 实际exit0，1710通过/3跳过/121.25s；日志 /tmp/kokoro-r112-test-status-governance.log SHA9e6f5ed8cea24e303681994d468571173de4d3b7bfbca08e938fabe33ba0ca09。三跳过为SourceNativeComponentTests需要Agent .venv，Root精确类补核skip原因（3 skipped）日志 /tmp/kokoro-r112-root-native-skip-reason.log SHA45c1db61973daa38eb9ae4632b4da88dbcc47636e9cb697d027e144125ef40a1；再以Agent .venv在Root工作树精确类、OS禁网实际补跑exit0，3通过/52 subtests/0.46s，日志 /tmp/kokoro-r112-root-native-complement.log SHA5322a4b73276d287b76664c0de6e75020d2323bd841643c4616c155b88703e72。两环境分别记录，不伪造单次1713通过，也不把测试工具门冒充业务E2E。独立台账初审发现两处旧覆盖态P2已窄修，最终审0/0/0（/tmp/kokoro-r112-test-status-final-review.md SHAff4fb855df783ed6dcff1ec2f0daac5bd408d9b4090ca2008a592747c6996f65，绑定追加本终态说明前四docs）。70组状态不变，历史归档suffix不变；Root仅提交四台账，子仓/uv.lock保留，未启动业务或共享服务。

## R111 推进记录（历史）

完整Wave0–7保持active。上一goal回合R110为progress（真实回归、codegen、HTTP验证及f775be11提交）；随后的人类测试进度答复仅核对状态、不计新增progress。本回合重新核实原WIN03已completed/idle交付，Root实际复测archive切片并启动后继Docker import tests-first，不以等待或计划充当完成。

- E68 / T-Q03、T-R01：Root42165九门实际exit0：import回归1、默认archive15通过/5 integration未选、原架构3、四文件140通过；Ruff/类型/checker/Failure均0，369文件hash前后相同、守卫resource_attempts0，Failure generator精确6调用。默认真实boto3 client构造1/close1/失败0，仅构造不是S3请求。manifest /tmp/kokoro-r111-agent-archive-root.json SHA9752df1925f7c18f3c1f8b1f9d3d196d6c85f588c573369649082914e8f54b54。
- 独立spec/quality审0/0/0：/tmp/kokoro-r111-agent-archive-review.md SHAfc7d14329cbfc79f8514ea5eb2f4824934ab7283ab44c585e8d48682ea175424；审报告误引worker历史Root b298已以独有绑定更正 /tmp/kokoro-r111-agent-archive-review-binding.md SHA50eb9143c204ac59c9d8efaa949391340217b14ead27a06bd2cd585484f00d9e 核实实际Root f775be11/Agent17c73541与target f1a5f88f，原报告未覆盖。E66导入行为失败在该测试切片关闭；五真实S3/清理失败组合和生产S3Archiver close仍未验，不关闭T-Q03/E49。
- 后继原WIN03 architecture RED turn01a0fe47-e667-76a2-8a38-de2e718e7085已completed/idle，Root实际复现后仅授现Docker test GREEN；不重复派工/启动服务。独立System fresh资源前置静态审已交，仍不运行共享资源。

- E69 / T-Q03：Docker collection原静态缺口已Root1597真实RED，原node成功import后calls非空导致1行为fail/0setup/0resource attempts，369hash保持；manifest /tmp/kokoro-r111-agent-docker-red-root.json SHA9731a502173acbc4ad8060b18d1ccc26ab5f21e3f47e7cea665c6d1282e6095d，独立RED审0/0/0 SHAa755444cc6a6eb75d9e5ecac678940b9a69e4a79bce66755a29b67ed465a70a9。初始wrapper argv索引错误在执行测试前失败，修正后才该真实RED，不伪称产品失败。已续派原owner仅Docker test lazy fixture GREEN，尚未Root GREEN。
- System真实fresh门前置静态方案已交 /tmp/kokoro-r111-system-fresh-preflight.md SHA00f30efdfe060b597d0c6fc89393f53b4c9730bedb0090713ba21351693f3252；仅核配置键存在/非空，未连接PG/Redis或运行新服务。下一资源单门须事前登记精确UUID库身份与owned进程终态，不扫描/删除他人资源，也不扩部署角色。

70稳定组仍12通过/1失败/0整组执行中/13待复测/41未验/2决策阻塞/1支付后置。源码切片实际运行与整组验收分别记录；完整安装/真实owner组合和其他用户能力继续按现测试矩阵推进。以下保留历史，不覆盖本节。

R111台账收口：Root63619治理309pass/22.01s；E69更新后Root99160同门再跑exit0/309pass22.10s，日志 /tmp/kokoro-r111-test-ledger-final-governance.log SHA65b0afd5ed11f3a15947189da84985e94323bfdb7fa6d1073910c00c0fab8cfa。最初计数wrapper以Counter与含0键dict比较误报，在测试执行前修正，不改变70状态也不当产品失败。独立最终台账审0/0/0，/tmp/kokoro-r111-test-ledger-final-review.md SHAa4d76955f6d26cf516f8749d967fcef07c2b77d7919ec80363324c927a4bb918，绑定追加此终态说明前四docs。只台账治理，不是全部用户链复测；原Docker GREEN writer继续现实际句柄，未复启共享设施，任务外修改保留。

## R105 最新测试切片

E51：Root实际9 RED→592 GREEN（37740 exit0/13.34s）、Nodecheck0与独立0；仅测试探针在真实UI文本前零snapshot，原活动刷新/全文/作品/隐私硬门不变。T-C06原E48失败已由E53本轮严格旅程通过关闭，T-L01本轮正向登录通过；其余能力不据此关闭。E52：Agent安装设计唯一P1已修复复审0；tests-only已冻结交付，R106独立审查0，Root复现待执行，T-Q03/E49安装失败仍未关闭。E51/E52本身不增加业务通过组；E53实际严格旅程新增关闭T-C06、T-L01两组。

## R107 候选与版本变化（历史，后继见R108）

- E56 / T-Q03：Root73736实际exit0，定点81通过、1 generator未执行；Ruff/直接Node类型检查均0，独立源码审0。证据 `/tmp/kokoro-r107-agent-installed-green-root.json`，log SHA b176226339ea138b86c4f7cd10a400082098821c633dc3feb39d65f307371e1a。完整源树、wheel/sdist/安装门未通过，不关闭T-Q03。
- E57 / T-Q03：原WIN03单行inventory同步后完整proof文件实际57通过/1失败，checker 214行违反原<200模块边界断言；原断言未放宽。manifest `/tmp/kokoro-r107-agent-proof-inventory-green.json` 名称不代表GREEN；其实际exit1。owner已停写，Root复现/审查待执行。
- E58 / T-R02、T-Q12、T-Q05：原WIN05真实fresh-schema入口的纯mock回归1失败/2通过/5旧例未选；database.end失败使DROP/admin.end短路并丢失setup原因。manifest `/tmp/kokoro-r107-system-fresh-cleanup-red.json`。生产脚本未改、无真实资源门；Root复现待执行。测试候选已变化，T-Q05回待复测，E55历史97通过不删除。

## R108 最新验收与缺口（历史，后继见R109）

- E59 / T-Q03：Root先复现完整proof 57通过/1失败，原负责人按职责迁移修复、断言不变；Root30506实际exit0，139通过/1 generator未执行、Ruff与类型0，独立源码审0/0/0。完整source/generator、构建和安装未验，E49安装后缺OpenAPI失败仍未关闭。
- E60 / T-Q05、T-R02、T-Q12：Root先复现cleanup七分支5失败/2通过，原负责人修复；Root58556实际10纯门exit0、9文件104通过/0失败/0跳过，全tracked hash不变，OS deny network。独立审发现primaryFailure以undefined兼作无失败哨兵，会漏掉throw undefined；该未覆盖分支尚未RED复现，不伪称104测试失败，也不接受整组。T-Q05保持待复测，真实PG/Redis/fresh-schema/integration与T-R02/T-Q12仍未验。
- E61 / T-Q03准备：Python3.11.14 runtime锁依赖缓存准备115包、hash校验/兼容检查通过，原离线缓存缺失失败保留，独有供应venv已删除。没有安装Agent wheel，不计任何业务任务通过。
- 整组执行中0：上述原句柄均已终态；当前是候选审查/台账整理，不把等待修复记成正在执行测试。

## R109 最新验收与缺口（历史，后继见R110）

- E62 / T-Q05：unknown异常两支Root RED为2失败/1正控通过；修复后Root17470实际10门exit0，9文件106通过/0失败/0跳过，197文件hash不变且当前重新核对相符，独立源码审0/0/0。恢复限定纯门通过；真实PG/Redis/fresh-schema/integration/runtime/image仍未验，不关闭T-R02/T-Q12。
- E63 / T-Q03：Root46970完整contract实际3行为失败/669通过/6被资源守卫拒绝的loopback setup error/1按原marker未选。三失败为Platform artifact路径归属、metadata cast、acceptance inline ignore；原WIN03新turn已completed/idle并交付精确五文件候选，owner报告原3例/140回归通过，尚未Root复测与审查。六HTTP回环测试须单独真实运行，Platform/Storage两codegen尚未到字节比对；archive导入副作用、完整unit/wheel/sdist/安装仍待验，E49失败保留。
- 整组测试运行0：原17470/46970已终态；Agent修复进行中不计整组验收正在执行。完整Wave0–7仍未闭环。

## R110 最新切片（历史）

E64：Root原3项架构失败修复已3/3复测，四文件140/140及完整Ruff/类型/checker/Failure check通过，369hash保持、独立源审0。E65：固定工具缓存供应后，Root真执行Platform/Storage两个generator --check各exit0，generated/pin不变、私有builder环境残留0；原offline cache缺失失败保留，不是wheel安装。E67：Root原6个loopback真实HTTPtransport6通过/1PG未选，6端口/线程回收确认；非正式IAM/Platform服务。

E66：archive真实import成功后calls非空Root1行为失败，原WIN03测试fixture修复实际active但尚未Root复测；不能将fixture回收当生产S3Archiver close实现。Docker collection凭据/probe新审查P1待RED。T-Q03/E49安装失败仍未关闭，70组计数不变；下一先archive→完整source/default收集→wheel/sdist/安装/owner组合，真实S3另门。全部修复候选停写后Root复跑才更新验收。

## 当前完成度（任务组计数，不是整体百分比）

共 **70组：通过12、失败3、执行中0、待复测13、未验39、阻塞2、后置1**。R128/E107按70唯一ID核对。通过限记录的版本与范围，不换算整体完成百分比；历史登录/聊天不证明当前组合。

## 本次已完成与未完成（可直接巡检）

- **通过12组**：T-Q01/Q04/Q05/Q08/Q11、T-L01、T-C01/C06/C11、T-K01、T-B01、T-R01。登录/聊天是E53历史发布组合及本地模型，不含用户网关、正式收费或所有Agent/UI能力。
- **最新失败3组**：T-A05过程来源完整性、T-C10分批GC过期、T-Q10契约checkpoint一致性。原71资源项当前全部通过，新3失败归两个业务组；原失败和修复历史均保留。
- **整组最终验收执行中0组**：已记录Root资源运行全部终态；原BFF writer已接R129源码修复。修复实施不计整组验收通过，当前没有新增浏览器执行证据。
- **待复测13组**：T-Q02/Q03/Q06/Q07/Q09、T-L02–05、T-F01–02、T-K02–03。
- **未验39组**：完整项目/独立会话交互、独立任务、作品、Skill/MCP真实调用、Todo/工具/审批展示、正式积分、Home/输入框/布局、所有owner组合等，详下方矩阵；局部通过不关闭完整用户组。
- **待决策2组**：T-C05项目生命周期、T-B07失败/部分输出/未知成本收费规则；T-B08支付后置。

**接续关键路径**：BFF三个有效RED修复→Root同一资源用例和74项回归→正式BFF7发布→Web消费→当前真实登录/聊天/刷新。随后沿原ID推进项目/独立会话、任务、Home/输入框、Skills/MCP/Todo/HITL及正规积分；外部资源和最终组合单列，支付最后。

## 范围与记录方式

70组覆盖：工程/契约12、登录权限5、会话与项目11、独立定时任务5、文件作品5、Skills/MCP7、Agent过程6、积分支付8、界面4、可靠性安全4、System2、Platform身份cutover1。

每组下的正例、负例、异常、恢复和权限分支按该行验收条件执行；70是测试任务组数量，不是全部自动化用例数量，也不代表已有70组实现。开发task不能代替本台账；发现缺陷→关联原测试ID与开发任务→修复版本→Root复测→全部必需分支通过后才关闭。失败历史保留，版本变化须复测，测试本身出错也单独分类。

### 每组执行记录与关闭规则

同一ID下逐步补齐正例、负例、异常、恢复、权限用例，不另建计划中心。每次执行记录：测试ID/分支、前置条件与测试账号角色、操作步骤、预期结果、实际结果、执行时间、commit或冻结hash、环境/命令、pass/fail/skip、脱敏证据、缺陷/修复版本、回收结果和复测结论。未展开或未执行的必需分支保持待验，不能仅凭70行目录称“完整测试已完成”。

缺陷发现可来自测试、浏览器或代码审查：审查发现但未复现须标注“待RED”，不改写成已有测试失败；同一测试的修复候选保持待复测，Root重跑并完成审查后才验收。版本变更使相关通过组回待复测。测试计划随着新增真实分支扩充，但保留稳定ID与失败历史。

## 已发现问题历史与追踪（不另算任务完成数）

下表保留发现时及阶段性记录，不能将旧“尚未修复/未发布”句子当最新状态。当前E87/E93限定修复与HTTP5发布见R122及上方看板；完整用户链未验仍保留。

|关联测试|问题|状态与下一动作|
|---|---|---|
|T-Q03、T-R02 / R114-LOCAL|web_fetch fixture未server_close，测试体通过但socket需外层补偿|E82 Root2真实RED后现fixture try/finally，17file与172local通过且forced_close0/全部owned终态，独立0；生命周期P1已关闭，2653bcc本地提交，原失败/补偿历史不删|
|T-C06 / R94-W01-GREEN|终态旧SSE关闭后仍reconnecting，第二次发送没有POST|真实RED已复现；E24修复完整纯门与审查通过并发布；E28/E40/E48失败历史保留；E51修复探针访问后，E53实际严格两轮旅程通过，T-C06具名范围已关闭；其他会话分支不据此关闭|
|T-Q01、T-C02 / R94-GATE-FAILURE-READ|Root完整门中欢迎页重进后项目路由未达预期|E20/E22保留；E24原配置完整复跑通过，不称已证明历史波动根因；复现时仍按原ID追踪，不增timeout/删断言|
|T-A01 / R94-W03-GREEN|todo.updated缺持久Row decoder分支|真实纯回归失败已复现；源阶段已由E21 Root复验/独立0接受；E35新增6项实际PG验证与独立0已通过；BFF/Web过程消费仍未验|
|T-A06、T-R02 / R94-W03-GREEN|生产者先失败时内部子任务未全部取消并等待|真实纯回归失败已复现；源阶段已由E21 Root复验/独立0关闭原P1；递归/nonmodel错误分支及运行链仍待验|
|T-U01 / R94-HOME-READ|提示入口切本地模式、未绑定owner套餐、硬编码模型档位|E29行为RED保留；E33正式Home局部修复与完整纯门已验并发布；E37错配已真实11 RED，E41四source GREEN已Root纯门/独立审接受，E42已发布ddd38c5且Rootfa4525e4已纳入；真实浏览器未验，不关闭T-U01|
|T-Q03 / R95-AGENT-MACHINE-RED|HTTP4缺新安全过程decoded mapping；raw重复键/整表字节预算校验尚未被完整执行|E25真实132行为RED有效；E30 Root候选654contract/1406隔离unit/静态/build与独立0通过，原raw校验缺口已在限定机器切片闭合；E31/E32限定PG已验；E47限定HTTP36已通过，正式发布/消费者与其他整门仍待验，不另加整组完成数|
|T-Q03 / R108-AGENT-PROOF-BOUNDARY-GREEN|checker职责超界导致完整proof边界断言失败|原Root57通过/1失败保留；E59迁移后Root139通过/1 generator未执行、独立0；E76已关闭具体安装缺资源，但完整负向/DDL/HTTP/发布门仍待验|
|T-Q05、T-R02、T-Q12 / R108-SYSTEM-FRESH-CLEANUP-GREEN|fresh清理短路、原setup原因丢失；后继unknown异常哨兵缺口|原七支5失败/2通过历史保留；E62 unknown两支Root2失败/1正控→修复后Root106纯测通过、独立审0，T-Q05限定关闭；E77单owner真实fresh与精确回收已验，T-R02/T-Q12全组仍未验|
|T-Q03 / R109-AGENT-THREE-FAIL-GREEN|完整contract三行为失败、六回环setup被禁网守卫拒绝，两codegen未到比对|E64 Root三项3/3复测与独立源审0，E65两codegen真check0，E67六回环真HTTP6/6通过；原失败历史保留，完整source/安装仍未验|
|T-Q03 / R110-FULL-SOURCE-PREFLIGHT|Docker integration文件collection先读取MinIO凭据和docker info，marker生效晚；生产S3Archiver无显式close入口|Docker import已E69 Root真实1 behavior RED/成功导入/0资源，E70 Root十门/161选定用例与独立审接受现test lazy GREEN；生产S3Archiver close仍未修；配置env读取本身无输出/连接不升格为新缺陷，不扩大配置重构|
|T-Q03、T-R02 / R117-ARCHIVER-RED|自然完成后自建S3客户端未释放；测试caller-owned正控未接入、真实drain未覆盖|E87 Root独立1 fail/1 pass/0 skip，资源尝试0，生产源码不变；仅接受自然终态泄漏RED，补有效控制及其他所有权分支后修复复测，不以worker或测试对象创建冒充覆盖|
|T-Q03、T-R01|既有archive测试导入时尝试探测ObjectStore，资源归属缺确证|E66真实1行为fail保留；E68 Root九门与独立0接受现file lazy UUID fixture，15默认纯实际通过/5资源未选、原cases保留；真实S3与生产close未验，不以排除整模块或测试tracker冒称生产生命周期修复|

## 测试任务矩阵
|测试ID|owner|验收范围|当前状态|具名证据/版本与边界|
|---|---|---|---|---|
| T-Q01 | Web | 本仓format/lint/types/unit/contract/architecture/build；跳过逐项说明 | 通过 | R234 Root46156在冻结工作树完整原pnpm check exit0：258contract/50architecture/lint/typecheck、165file2481pass/0fail/build通过，161.421秒；仅显式maxWorkers4保持文件并行、原5000ms与所有case，独审0。预算已精确单文件提交main680c8db8，其他20mixed保留；本工程结果绑定冻结当前树，不冒仅Git-only发布或用户3310。manifest /var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-r234-web-engineering-q7b13zmn/manifest.json，log1af68e9c。R233默认2478/3与未build历史保留，未声称精确超时阶段；另81真实隔离系统通过不替代真实owner/模型/积分完整旅程。 |
| T-Q02 | BFF | 本仓format/lint/types/unit/contract/architecture/build；跳过逐项说明 | 通过 | E108：正式main a68cbe5，Root默认736pass/1既定PG schema skip、四pure149pass、完整contract233pass/0skip；format含37变更TS/MJS、lint/types/build/全部固定owner生成check通过，两独立限定审0/0/0。真实三资源74/74另有具名证据，但完整BFF其他资源/镜像及Web组合未验；资源skip属T-Q12，4条lint warning保留。 |
| T-Q03 | Agent | uv锁与frozen依赖/Ruff/Pyright/pytest/wheel；HTTP contract与架构；skip说明 | 待复测 | E95 Root当前1960纯节点全部通过/0skip，七静态门及独立审通过，原E87生命周期与E93规范失败限定回归关闭；E96新包完整115 runtime安装、四布局64负向/219步骤通过；E97 installed CLI/真实PG/catalog/六漂移回滚通过，E98 installed HTTP36pass/0skip及151origin核验通过；E99最终包211entries与资源已测包同bytes、sdist重建一致。Agent已正式发布main79bf98c、远端同SHA。正式BFF/Web消费者、真实S3/Docker/SIGTERM及完整Agent整组仍未验；完整失败历史与各次包身份保留在progress.md，不拿历史包替当前包，不称完整Agent闭环 |
| T-Q04 | IAM | 本仓format/lint/types/unit/contract/architecture/build；跳过逐项说明 | 通过 | E14：Root本次verify938通过；仅该纯门，host51另记有限资源证据，非全部IAM integration/登录 |
| T-Q05 | System | 本仓format/lint/types/unit/contract/architecture/build；跳过逐项说明 | 通过 | E74当前候选source da4675b9/test45bd5286/helper efd2f061，Root99279十纯门exit0，9files119pass/0fail/0skip，197hash保持/owned进程组终态/OS禁网，独立审0/0/0。E72先12fail/2control，连接URL正控缺口已补强并Root复现；只未发布候选纯门，真实PG/Redis/freshschema/runtime/provider/image另未验；E77单owner真实PG fresh 23断言/22表与精确回收已验，Redis/业务HTTP及其他owner组合仍未验 |
| T-Q06 | Billing | 本仓format/lint/types/unit/contract/architecture/build；跳过逐项说明 | 待复测 | 历史门不能证明新组合；按owner ACCEPTANCE重跑 |
| T-Q07 | Platform | 本仓format/lint/types/unit/contract/architecture/build；跳过逐项说明 | 待复测 | 历史门不能证明新组合；按owner ACCEPTANCE重跑 |
| T-Q08 | Storage | 本仓format/lint/types/unit/contract/architecture/build；跳过逐项说明 | 通过 | E94 Root当前74c4b59默认491pass/156PG skip/0fail，format/lint/types/build与contract/Prisma生成+正规normalize0；280源/17generated恢复原bytes/clean，owned资源终态正常；独立终审7d8eaee1为0P0/0P1。限定工程门；156PG明确拆至T-Q12、文件真实资源T-F01–05仍未验，不称完整Storage闭环 |
| T-Q09 | Scheduler | gofmt/vet/test/build；OpenAPI/event protocol/schema/架构；skip说明 | 待复测 | 历史门不能证明新组合；按owner ACCEPTANCE重跑 |
| T-Q10 | Root | 精确gitlink、main-only、发布contract/version/digest/client drift、fresh clone | 失败 | E105 Root本轮完整scripts/tests实际1709pass/1fail/3skip、455 subtests pass；test_w1e_iam07_bff_pin_marks_iam_composition_pending在verify_checkpoint报告217项不匹配，首项历史evidence gitlink17c7354与当前Agent79bf98c不符。当前checkpoint/消费者证据一致性失败，须区分过期证据与真实兼容缺口，不放宽校验器或伪改已通过。E75原标准152报告及完整fresh clone/main检查继续未验。 |
| T-Q11 | Root | 发送失败诊断有界/脱敏、两轮归属、失败仍非零退出、原硬断言不变 | 通过 | E51：Root93085实际9fail/583pass，37740修复后592pass/13.34s及Nodecheck0、独立0；本Run合法UI文本前零snapshot，terminal/observer/deadline封闭；原所有硬断言与控制保留，session_rate_limited闭集补齐。仅当前冻结driver b83525de/test fee45056测试工具门，不是T-C06真实用户旅程通过 |
| T-Q12 | 各数据owner | 同应用库独立schema fresh install/drift/拒重入/零跨owner SQL/失败回滚 | 未验 | E32仅Agent fresh7通过；E77 System单owner真实fresh23断言/22表/catalog/拒重入及精确临时库回收通过。E85新增Agent source-wheel installed CLI/目录/六漂移单owner门；全部数据owner同一应用库schema组合与零跨owner访问仍待验，不关闭整行 |
| T-L01 | IAM→Web→BFF | 真实IAM表单→授权→callback→HttpOnly session→/app；无中转/整页重试 | 待复测 | 当前组合已变更，E53仅历史证据，须用当前发布pins重新验证；E53：本轮fresh owner/member两账号真实IAM表单200/nativeconsent200+一次303提交/callback303/HttpOnly+Secure+Lax cookie/session200与app200；浏览器精确导航与单次计数验证无可见中转，独立终态0。仅正向入口；其他登录/权限负例另T-L02–05待复测 |
| T-L02 | IAM→Web→BFF | 错误密码/CSRF/state/nonce/PKCE/redirect篡改拒绝且无session | 待复测 | W1C/W1D历史隔离浏览器证据；新组合正式旅程未验 |
| T-L03 | IAM→Web→BFF | 刷新/到期/退出/退出后重登与后退；禁止过期签名URL无限重试 | 待复测 | W1C/W1D历史隔离浏览器证据；新组合正式旅程未验 |
| T-L04 | IAM→Web→BFF | 固定tenant准入、撤销/禁用、同tenant另一用户及跨tenant隔离 | 待复测 | W1C/W1D历史隔离浏览器证据；新组合正式旅程未验 |
| T-L05 | IAM→BFF→Web | 成员/邀请/角色权限与审计：读写、分页、重复命令、撤权即时失效；无管理员越权 | 待复测 | W1C-Team历史owner切片，当前完整用户权限矩阵待复测 |
| T-C01 | BFF | 独立/project/全集列表、tie keyset limit1/2、跨主体/租户/deleted、冲突400 | 通过 | E03：真实PG+生产HTTP，仅后端过滤切片 |
| T-C02 | Web→BFF | 新建独立/项目会话、URL/back/forward/刷新、草稿和消息不串scope | 未验 | 下一Web正式固定BFF7，再真实浏览器验证；当前消费者尚未更新。 |
| T-C03 | Web→BFF | 重命名/删除等待ACK；延迟/503/切换scope不复活、不污染新页 | 失败 | R144 Root真实Next/Chromium两例有效RED：DELETE无exact scope；失败后草稿清空且提前刷新。ACK窄源码处理中，真实BFF/PG及完整分支未验 |
| T-C04 | BFF→Web | 显式分享/撤销；私有链接不冒充公开分享；另一用户不可读/控制 | 未验 | R82分享文案与真实权限不一致；正负例都需验 |
| T-C05 | BFF→Web | 移动/归档/删除项目时会话、活动Run、任务及作品的生命周期 | 未验 | 用户批准按ChatGPT删除：删除项目及其会话/指令/仅项目文件，保独立保存资源；移动出项目后保留。当前owner契约/关联任务与Run恢复尚待实现验证，见顶部裁决补充 |
| T-C06 | Root六owner | 正式登录后两轮真实模型聊天：两POST/四Message/全文/刷新/作品hash/他人404 | 待复测 | 当前组合已变更，E53仅历史证据，须用当前发布pins重新验证；E53：Rootcc7bfb78六owner fresh/clean/发布hash，原58200实际exit0；两POST202/四completed、真实模型全文SHA、首轮保留、active非空文本硬刷新+同watermark续流、真实作品下载hash/刷新一卡/另一用户三404；五owned残留0/子terminal/桶删除404，独立终态0。实际模型为本地Ollama qwen3:8b，不含Billing/Agent5候选或用户OpenAI网关；E48失败历史保留 |
| T-C07 | BFF→Agent | 同会话FIFO/同key重放/双tab同时提交；一活动head，无重复执行 | 未验 | E108真实chat-facts13/13及完整三资源74/74，原snapshot42703首阻断限定关闭；双tab/同key重放及浏览器完整用户组仍未验。 |
| T-C08 | Web→BFF→Agent | Stop/steer/取消/重复控制；ACK不冒充terminal，输入和队列正确收口 | 未验 | 按现owner契约；资源验收不能用UI按钮存在替代 |
| T-C09 | BFF→Web | 活动/终态刷新：同事务Message/执行head/过程与event_watermark一致 | 失败 | E109 Web恢复无executionProcess、分页未请求、signal未传递，属D-R135-02–04；源码修复/Root复测及浏览器未执行。E108后端projection46/46、T-C09.1–5历史范围保留，不由后端绿关闭Web失败。  E112：Root七完整file371/371，原15及新增4具体失败限定复测关闭；整组状态保留，完整工程/深层恢复/当前浏览器仍待验。 |
| T-C10 | BFF→Web | SSE断线/cursor replay/重复/间隙/过期与GC；不丢字、不双气泡 | 失败 | E109 Web过程410未fresh snapshot且分页未请求（D-R135-03），深层重复过期/错误cursor/浏览器未到达。E108后端74/74已关闭E107 partial-GC缺陷，保留该限定证据；不同层新失败尚未修复复测。  E112：Root七完整file371/371，原15及新增4具体失败限定复测关闭；整组状态保留，完整工程/深层恢复/当前浏览器仍待验。 |
| T-C11 | Web | 同scope真实重挂/双owner/StrictMode；最后卸载才close SSE；injected不被释放 | 通过 | E11：Root真实RED→完整门及独立审，已提交/推送a52a623；仅生命周期组件切片，不证明W2 |
| T-P01 | BFF→Scheduler→Agent | 独立任务不进入会话列表；project_id仅关联；创建/修改/暂停/删除/权限 | 未验 | 按现ScheduledTask/Occurrence owner契约，真PG/Redis/HTTP组合 ；R255正常UI创建200后saving永久pending已修，编辑200自动关闭/刷新标题与paused保持/空白disabled及取消通过；删除/恢复/越权/真实执行未验，不关闭整组 |
| T-P02 | BFF→Scheduler→Agent | IANA timezone/DST、周期/一次、边界时间与misfire | 失败 | R255正常3310每周08:00 America/New_York创建200，next_run_at却创建当时01:16Z/当地21:16；BFF默认now/周锚点混用并丢Scheduler权威next_due_at，尚未修复。QA已正规paused；不把HTTP200/源码查阅称时区通过，后继owner contract+真实Scheduler→BFF→Web复验 |
| T-P03 | BFF→Scheduler→Agent | 重复唤醒/投递、幂等receipt、ACK unknown与Outbox恢复 | 未验 | 按现ScheduledTask/Occurrence owner契约，真PG/Redis/HTTP组合 |
| T-P04 | BFF→Scheduler→Agent | 进程崩溃/lease到期/重启、旧worker失fence；不重复Occurrence执行 | 未验 | 按现ScheduledTask/Occurrence owner契约，真PG/Redis/HTTP组合 |
| T-P05 | BFF→Scheduler→Agent | 暂停/删除不伪造已接纳任务终态；串行dispatch/Agent terminal释放 | 未验 | 按现ScheduledTask/Occurrence owner契约，真PG/Redis/HTTP组合 |
| T-F01 | Storage→BFF→Web/Agent | 个人与项目上传：真实字节/MIME/大小/clean scan/感染与取消 | 待复测 | R252当前五owner真实无痕用户普通57B上传扫描→刷新→下载原字节SHA一致，/tmp/r252-library-real-user-journey.json；自然300秒边界/项目/感染/取消/越权未复验，原3310未同步，整组保持 |
| T-F02 | Storage→BFF→Web/Agent | 附件列表/分页/重启读取/下载hash；他人及跨project拒绝 | 待复测 | W2个人上传下载有历史切片证据；完整新组合待验 |
| T-F03 | Storage→BFF→Web/Agent | Agent生成作品→Storage receipt→卡片/预览/下载→刷新仍同作品 | 未验 | 真实ObjectStore/scanner/receipt；不以fixture作品冒充 |
| T-F04 | Storage→BFF→Web/Agent | 失败发布/超时/URL过期/重试：不生成伪作品、不泄密、不重复完成 | 未验 | 真实ObjectStore/scanner/receipt；不以fixture作品冒充 |
| T-F05 | Storage→BFF→Web/Agent | 删除/retention/引用保护/GC，有限回收只删本owner资源 | 未验 | 真实ObjectStore/scanner/receipt；不以fixture作品冒充 |
| T-K01 | Web | Plugins无owner回执时不出现本地Add/Remove/Connected假成功 | 通过 | E06：已发布5e538f69，两组件/test字节仍匹配；不等于MCP接通 |
| T-K02 | Platform→Storage→BFF | Skill草稿/整包上传/校验/发布/读回；恶意ZIP与非法路径拒绝 | 待复测 | R252当前五owner真实无痕IAM→普通二字段ZIP发布/读回/安装启停移除刷新有限主链PASS，/tmp/r252-skills-real-user-journey.json；恶意包/越权/未知ACK/执行仍未验，原3310未同步，整组不关闭 |
| T-K03 | Platform→BFF→Web | 个人安装/启用/禁用/移除/重装持久；版本/重复/另一用户拒绝 | 待复测 | R252真实无痕五owner安装→停用→刷新同版本仍停用→启用→移除→刷新安装筛选为空且发布源保留；重装/多版本/跨账号/并发/未知ACK未验，/tmp/r252-skills-real-user-journey.json与独审715480d4；整组不关闭 |
| T-K04 | Web→BFF→Agent | Composer选择精确Skill refs→提交冻结→真实加载；禁用/撤权拒绝 | 未验 | formal selector与执行展示未贯通 |
| T-K05 | Platform→BFF→Web | MCP connect/scopes/授权回执/撤销/需重连；目录不等于连接 | 失败 | R255 01:26真实502已定位并在正常持久composition启用现mcp-server；同入口与硬刷新再读200合法servers空态，加载子例恢复。目录非本人连接，UI语义、现注册Unimplemented与连接/撤销/执行生命周期仍未闭环；整个组继续失败，不凭列表200转PASS。 |
| T-K06 | Web→BFF→Agent→Platform | MCP opaque refs选择、每次调用fresh授权、args identity；撤销零调用 | 未验 | 旧free-text mcp_servers需owner-first替换，无fallback |
| T-K07 | Platform→Agent | 工具schema closed profile/输入输出校验/超时取消/越权/注入 | 未验 | 不能把协议profile文档当执行测试 |
| T-A01 | Agent→BFF→Web | 简单聊天只回复；复杂任务Todo完整表更新、不被子Agent覆盖 | 未验 | E101严格HTTP5 reader/decoder/safe CUSTOM149 pure通过；E108进一步真实验证BFF过程持久化、public7、锚定分页、provenance/GC（完整三资源74/74）并发布a68cbe5。仅后端切片；当前正式Web及浏览器完整能力未验，不提升整组；历史失败保留。 |
| T-A02 | Agent→BFF→Web | 真实Skill resolving/loading/ready/failed；不从选中状态伪造已加载 | 未验 | E101严格HTTP5 reader/decoder/safe CUSTOM149 pure通过；E108进一步真实验证BFF过程持久化、public7、锚定分页、provenance/GC（完整三资源74/74）并发布a68cbe5。仅后端切片；当前正式Web及浏览器完整能力未验，不提升整组；历史失败保留。 |
| T-A03 | Agent→BFF→Web | 友好tool running/completed/failed摘要；无raw args/result/stack/token/隐藏推理 | 未验 | E101严格HTTP5 reader/decoder/safe CUSTOM149 pure通过；E108进一步真实验证BFF过程持久化、public7、锚定分页、provenance/GC（完整三资源74/74）并发布a68cbe5。仅后端切片；当前正式Web及浏览器完整能力未验，不提升整组；历史失败保留。 |
| T-A04 | Agent→BFF→Web | 完整多项HITL pause→一次决策→resume；stale/重复/unknown/刷新正负例 | 未验 | E09：Root R90已裁定枚举/字段/容量/轮次身份；原owner四D0收敛待核，机器/运行链尚无本切片业务测试 |
| T-A05 | Agent→BFF→Web | Todo/Skill/tool/HITL/delivery五时点刷新：恢复同水位，无重复或丢失 | 失败 | E109 Web过程水合/全值替换/分页及abort明确失败（D-R135-02–04）；与T-C09/C10共用同次15fail，不重复计自动测试数。E108后端74/74关闭两provenance失败的证据保留。五暂停点浏览器/完整恢复链仍未验，源码修复后须Root复测。  E112：Root七完整file371/371，原15及新增4具体失败限定复测关闭；整组状态保留，完整工程/深层恢复/当前浏览器仍待验。 |
| T-A06 | Agent→BFF→Web | 子Agent身份/状态/失败/取消/汇总；不混入主回复或泄露私有过程 | 未验 | E101严格HTTP5 reader/decoder/safe CUSTOM149 pure通过；E108进一步真实验证BFF过程持久化、public7、锚定分页、provenance/GC（完整三资源74/74）并发布a68cbe5。仅后端切片；当前正式Web及浏览器完整能力未验，不提升整组；历史失败保留。 |
| T-B01 | Billing | 定价revision纯codec：strict格式/不可变摘要/整数/rational/边界/恶意结构 | 通过 | E07：772 unit/静态通过，仅冻结3文件；未验真实收费 |
| T-B02 | System→Agent | 实际provider/model/route revision绑定；逐call/attempt证据，不补零/猜用量 | 未验 | ADR-033；System仅技术路由，Agent仅事实证据 |
| T-B03 | Billing→BFF→Web | 授权赠送/余额/流水/撤权；前端只读owner结果，无假充值/免费补偿 | 未验 | 真实Billing命令+持久ledger；不直接改数据库充当授权 |
| T-B04 | Billing→Agent | provider调用前预占、余额不足、并发预算、同key重放、ACK unknown恢复 | 未验 | 实际attempt授权，禁止一次许可放行整Run |
| T-B05 | Billing | 采购成本×冻结可配置7/5倍率、币种积分换算/舍入/版本；前端零独立计价 | 未验 | ADR-033；7/5是加价40%，不是净利润率 |
| T-B06 | Agent→Billing | 真实usage→幂等结算/增额/释放/对账；超时、失fence、晚结果不重扣 | 未验 | 未知成本保留reconcile，不把Run terminal当费用结案 |
| T-B07 | Billing | 失败/取消/部分输出/未知成本的收费资格与账务分支 | 未验 | 用户批准仅结算已核实实际消耗、释放其余可确认未使用预占；unknown待证据/对账，不按零释放。正式owner账务链/并发恢复未验，见顶部裁决补充 |
| T-B08 | Billing | 支付/订阅/checkout/refund/webhook验签去重及sandbox对账 | 后置 | 用户已明确支付最后；渠道配置属运维，不阻当前聊天研发 |
| T-U01 | Web | Home提示只填草稿、零自动POST/计费；真实模型/套餐/能力，无错误营销卡 | 未验 | E33局部发布/E37语义11真实RED/E41完整纯门接受/E42已发布ddd38c5，网站/More/零POST正控保护；Root新组合fa4525e4已发布；完整Home真实浏览器未验 |
| T-U02 | Web | Composer多行/中文输入法/Enter与Shift+Enter/附件/发送禁用与Stop；无内嵌方框 | 未验 | 真实浏览器+截图/axe/视觉；UI纯测或借用shadcn不替代验收 |
| T-U03 | Web | 桌面与窄屏对话/侧栏/项目/作品布局，长文本/代码/表格/错误均可用 | 未验 | 真实浏览器+截图/axe/视觉；UI纯测或借用shadcn不替代验收 |
| T-U04 | Web | 键盘/focus-visible/axe/reduced-motion、全部loading/empty/error/partial状态与视觉/bundle门 | 失败 | 用户当前整页无限加载未闭；R141两个列表子例限定通过不替代整组；真实浏览器+截图/axe/视觉待完成 |
| T-R01 | Root | 本次BFF隔离测试临时库精确创建/删除、无共享PG/Redis reset | 通过 | E03：removed=true/cleanup=[]；仅该run，不代表全进程治理 |
| T-R02 | 各owner→Root | 实际进程启动/health/ready/超时/取消/graceful shutdown/worker drain/故障恢复 | 未验 | E88现System19真实资源/HTTP切片通过；Agent旧close失败已在E93/E95限定纯生命周期回归关闭，当前installed HTTP/真实S3/Docker/SIGTERM与全owner恢复仍未验，不把纯测修复当资源门通过。 原句柄追踪、不重复启动、不把观察超时当进程已停 |
| T-R03 | Root/各owner | 权限矩阵/输入边界/敏感日志/依赖secret/source扫描/跨owner禁止访问 | 未验 | 同tenant不同人+跨tenant正负例；报告不含凭据 |
| T-R04 | Root | 全owner当前门+组合真实E2E+隔离fixture backup/restore（持久事实/幂等/未决outbox恢复）+可追溯release smoke/image SHA清单 | 未验 | Wave7最终研发验收；SLO目标不冒充压测，不扩展部署运维 |
| T-S01 | System→IAM/BFF | Site/Host/Workspace/Runtime/Policy具名身份与生命周期；disabled/unknown/expired拒绝、secret零泄漏 | 未验 | E88现System单仓lifecycle19真实通过，只启动/HTTP deadline/schema资源切片；完整业务/消费者待验。 owner HTTP/PG→消费者，不建任意配置桶 |
| T-S02 | System→Agent/BFF | 模型目录/选择/路由revision与digest；实际gateway/credential；重试故障不静默换未授权模型 | 未验 | 技术配置不等于实际调用证明；消费固定owner artifact |
| T-G01 | Platform→BFF/Agent→Root | capability到platform身份/Proto/remote/path/env/DB/Redis一次cutover；旧alias/fallback删除 | 未验 | Wave3正式验收，现物理仍kokoro-capability，不冒称已改名 |



## 逐组执行用例计划（70原ID，不另计任务数）

本表为Root审查后的执行计划，非已执行结果；来源是R123只读草案，Root核70ID集合/顺序与当前矩阵一致，并校正版本冲突、定价codec和锚定分页语义。每格.n对应本组子用例；具体正式endpoint/错误码/预算取执行版本owner机器契约，账号与自有资源ID、命令/自动节点须在执行记录中固定。T-C05/T-B07仍待业务裁决，T-B08后置；原T-C09.1–5不重编号。

通用前置：A本人、B同tenant另一主体、C另一tenant皆为具名隔离fixture；绑定commit/dirty hash及owner artifact。资源由Root登记并只清自身。每子例回填操作/预期/实际/证据/缺陷/修复版本/Root复测，真实资源不能以stub替代。完成全部必需分支才关闭整组。

|ID（原owner）|前置：账户/身份/fixture|正向操作与可观测预期（子用例）|权限/异常及重复、取消、断线恢复（子用例）|验证层级与脱敏证据|未决项/既有证据边界|
|---|---|---|---|---|---|
|T-Q01（Web）|冻结Web及BFF pin；Node/pnpm按owner ACCEPTANCE|.1 执行现pnpm check及其lint/types/unit/contract/architecture/build，逐命令exit0、生成drift0；不存在format脚本记N/A而非伪运行|.2 锁定错误响应/断流/权限反例仍入套件；.3 记录skip与浏览器门分拆，构建失败不得发布|owner工程门；命令/log SHA、测试逐项统计、bundle清单；UI真实证据归U/C|沿Web ACCEPTANCE；历史E41不代替新pin复测|
|T-Q02（BFF）|冻结BFF源码、public/Agent contract pin及工具链|.1 按ACCEPTANCE执行format/lint/types/unit/contract/architecture/build，验证生成client与固定artifact无drift|.2 畸形payload/跨身份/重复receipt控制仍有效；.3 默认PG跳过明确另排真实integration，不称0skip资源通过|owner工程门；命令/JSON结果/生成前后hash|HTTP5消费变更后必须新门；E01仅历史限定范围|
|T-Q03（Agent）|正式Agent79bf98c及对应wheel/lock；原source、pure/local、installed入口分区清单|.1 按ACCEPTANCE跑锁/frozen依赖/Ruff/Pyright/全默认与contract、构建并核wheel/sdist；.2 仓外完整依赖四布局安装、origin/RECORD、CLI/DDL/HTTP行为与包身份同源|.3 missing/tamper拒绝零资源；真实S3/Docker关闭/构造失败及SIGTERM drain另实跑，失败或skip不充整组；异常保原原因/无悬挂资源|纯/本机真实I/O/真实PGRedisHTTP/provider分层；node清单、artifact SHA、原失败与复测、回收记录|E95–99已测切片引用不重计；剩余backend/进程/消费者正式门未验|
|T-Q04（IAM）|IAM固定commit、具名账户fixture与工具链|.1 按IAM ACCEPTANCE执行verify及静态/contract/build，生成与规范无漂移|.2 会话签名/权限/重复命令反例保留；.3 integration URL缺失记未验，真实授权/退出归L组|owner工程门；各子命令exit/skip、schema及artifact摘要|E14限定工程门；新组合按变化范围复测|
|T-Q05（System）|System固定源与现ACCEPTANCE；owned Node进程fixture|.1 跑format/lint/types/build/contract与纯测试，源hash保持；.2 fresh与资源lifecycle用现单独真实入口|.3 setup失败/unknown抛出/end与DROP独立失败保原对象并完成其他清理；不得以纯mock充PG通过|工程/真实PGHTTP分列；日志SHA、node状态与资源账|E74/E77/E88引用具名切片；完整System业务归S/R/Q12|
|T-Q06（Billing）|Billing冻结候选及现ACCEPTANCE；不触其他writer|.1 执行pnpm verify（含format/lint/types/test/build/sql:check/contract:check），所有门有结果|.2 缺CHECK/partial predicate漂移的db:verify-schema拒绝且无写；.3 integration缺URL的skip另列，重复扣费负例不得排除|工程+自有真实PGRedis；SQL目录差异/测试结果/脱敏ledger ID|历史B01纯规则不等于Billing整门或收费通过|
|T-Q07（Platform）|Platform现物理kokoro-capability冻结pin及ACCEPTANCE|.1 跑format/contract/prisma validate/生成drift/schema/type/test/lint/build；.2 真PGRedis REQUIRE_REAL_INTEGRATION=1与production smoke单列|.3 生成差异停交owner；缺凭据/权限/retry反例入套件，provider stub不充外部授权|工程+真实资源；生成前后SHA、HTTP状态/清理|物理更名归G01；消费Storage等当前pin需闭环|
|T-Q08（Storage）|Storage74c4b59或后继冻结版本；严格匹配已安装pnpm配置|.1 沿ACCEPTANCE跑format/lint/types/unit/contract/architecture/default/build/contract与Prisma正规生成归一，源和生成物drift0|.2 默认156PG skip另执行integration/compiled，真实S3scanner另F组；.3 错配置/guard工具失败与业务失败分开保留|工程/owned loopback/真实资源分层；log、生成diff与回收|E94已限定通过；新版本重验，不抹原skip|
|T-Q09（Scheduler）|Scheduler固定Go/锁/ACCEPTANCE；自有资源|.1 检查gofmt -l输出空、go mod verify/vet/test/race/build及architecture/schema；.2 integration/redis/smoke按现入口|.3 旧lease/重复wake/ACK未知反例仍入真实PGRedis；不运行gofmt -w掩盖检查前状态|工程+race+资源；命令exit、逐包结果与run ID|历史门不替当前组合；调度业务P组另验|
|T-Q10（Root）|当前九owner正式main refs、Root gitlink与artifact manifest|.1 新隔离clone按固定refs初始化；核gitlink/remote提交存在、机器version/digest/client一致；.2 运行Root topology/标准检查与现契约兼容门|.3 注入隔离坏digest/不存在ref须拒绝且不fallback；恢复后复测；不得把declaredbroken当兼容通过|静态/生成/新clone；SHA清单、drift报告、逐条裁决|E75 152报告保持待裁；不猜部署流程|
|T-Q11（Root）|冻结现真实旅程driver及纯测试；脱敏失败样本|.1 正常两轮归属、terminal/observer/deadline通过；.2 401/429/timeout/malformed诊断输出稳定code且exit非零|.3 重连/缺消息/未terminal不得靠增加轮询绕过；assert两POST/全文/作品等原硬门未删；secret canary不出日志|测试工具纯门；注入向量结果、原assert与hash|已有E51限定通过；不把工具通过算C06实际旅程|
|T-Q12（各数据owner）|同实例同credential自有隔离库，所有数据owner独立schema及canonical安装入口|.1 逐owner fresh安装并比较tables/columns/constraints/index definitions；重复安装按各contract拒绝/幂等，既有数据不变|.2 缺表/约束/索引定义漂移拒绝；.3 安装中失败回滚、另一owner schema不变、SQL访问审计零越界|真实PG/实际installed或owner CLI；catalog差异、事务结果、精确回收|部分owner仍整库空白约束需先改为schema边界；单ownerE97不关整组|
|T-L01（IAM→Web→BFF）|真实IAM owner/member两测试账户，授权Web回调与BFF同源组合|.1 浏览器表单登录→授权→callback→/app，授权提交和callback各一次；session200且Cookie HttpOnly/Secure/SameSite正确|.2 双击提交/刷新callback不增session或循环中转；.3 同源会话成功后一次受权BFF查询，跨身份仍按L04拒绝|真实浏览器+IAM/BFFHTTP；脱敏跳转序列/状态/Cookie属性（无值）|E53正向历史已验，当前组合变化复测|
|T-L02（IAM→Web→BFF）|L01账户；独立浏览器上下文与一次性授权code|.1 合法state/nonce/PKCE/redirect建立session作正控；.2 错密码、缺CSRF及分别改四字段得到contract错误且无session|.3 重放code/重复callback/中途取消不登录他人或无限重试；恢复新合法流程才成功|浏览器+真实IAMHTTP；错误code、session计数和脱敏HAR|错误具体status按当前owner机器契约固定，不预写猜测|
|T-L03（IAM→Web→BFF）|已登录测试账户、可控会话到期fixture|.1 刷新仍同主体；主动退出后session失效，后退受保护页重检；重新登录正常|.2 token/session实际到期拒绝旧请求；.3 并发tab退出/刷新、过期签名URL不无限重试、不复活旧session|真实浏览器/HTTP；请求次数、受保护内容隐藏、session状态|期限用owner测试时钟/真expiry入口，不sleep当过期证明|
|T-L04（IAM→Web→BFF）|同tenant A/B与不同tenant C，已创建各自会话/项目|.1 A访问自有资源；.2 B/C替换资源ID/tenant参数读写控制均拒绝且无副作用|.3 撤销成员/禁用账户后旧session再次访问即时按契约失败，续流/重连不保留权限；恢复授权另测|真实IAM+BFFHTTP+浏览器；权限矩阵、拒绝码、写入计数|禁用/撤销确认点按现contract，不造运维角色|
|T-L05（IAM→BFF→Web）|IAM owner/有权成员/无权成员三身份及邀请对象|.1 正式邀请接受→成员列表分页与读写权限正确；.2 同key重放同结果/冲突payload拒绝|.3 无权邀请/提权/改他人role拒绝；撤权后旧token及分页游标不越权，审计一条业务命令不重复|真实IAMHTTP/PG+Web；主体化审计、分页集合、权限变化|沿现role业务规则；不赋新部署管理角色|
|T-C01（BFF）|A/B/C账户；独立、项目P/Q、同timestamp及deleted会话fixture|.1 真实列表分别独立/P/全集，limit1/2遍历无漏重且tie keyset稳定|.2 冲突filter400、另主体/租户/deleted不返回；.3 翻页期间插入按既有cursor语义无重复|真实BFFHTTP/PG；完整ID集合与cursor、错误码|E03仅后端已验，UI scope见C02|
|T-C02（Web→BFF）|登录A，有P/Q项目和独立入口|.1 三入口各新建会话发送不同marker，URL和归属正确；.2 back/forward/刷新恢复各自消息与草稿|.3 快速切scope、双tab、提交未ACK换页不把草稿/响应写到新会话；无权项目不能新建|真实浏览器+BFF；路由轨迹、请求scope和页面marker|BFF/Web固定正式兼容pin后执行|
|T-C03（Web→BFF）|A的独立/P会话；可控真实HTTP延迟/503切面|.1 重命名/删除等待正式ACK后列表和详情一致；刷新不复活|.2 延迟或503保原事实且可重试；.3 请求中切scope/重复删除/旧响应晚到不污染新页，B无权删除0写|浏览器+真实BFFHTTPPG；前后列表/ACK时点、请求计数|已知fire-and-forget竞态先真实RED后修复|
|T-C04（BFF→Web）|A私有会话、B与未登录浏览器；可分享fixture|.1 正式创建share得到明确共享链接，按contract另身份可读取许可范围；撤销后同链接拒绝|.2 私有详情URL不变公开链接；无权创建/控制拒绝；.3 重复撤销/并发访问不泄漏撤销后新内容|真实浏览器/HTTP；share ID/状态与资源边界，不记录secret token|公开分享范围按现契约，缺正式mutation则先实现而非文案假成功|
|T-C05（BFF→Web）|项目含会话/active Run/任务/作品；A/B身份|.1 待业务明确移动/归档/删除各对象及活动Run结果，再冻结前后关联集合和API预期|.2 待裁后加入无权/关联冲突/重复命令/并发Run与失败回滚向量；.3 复原或永久删除策略按裁决验|计划阻塞；仅记录待决对象/接口，不执行破坏性动作|必须裁关联生命周期，禁止猜cascade/停止/保留规则|
|T-C06（Root六owner）|正式发布兼容六owner、真实模型可用、A/B账户与owned文件空间|.1 正规登录后第一POST完成，第二POST同会话完成；严格两POST/四Message、首轮不变、全文摘要可核|.2 活动非空文本硬刷新从同watermark续接；真实作品下载hash和刷新一卡；.3 B访问相关三资源拒绝，失败保原非零与日志|真实模型+全链浏览器；请求计数/全文SHA/作品SHA/截图/清理|E53只本地qwen3:8b历史范围；其他网关/新HTTP5组合另跑，不加免费替身|
|T-C07（BFF→Agent）|同会话两tab、另会话；真实可暂停执行fixture|.1 同时提交两合法请求按正式FIFO串行、一active head；另会话可并行|.2 同key同payload重放同receipt、不增Run；异payload冲突；.3 ACK丢失重发/worker重启后顺序不乱、无重复模型执行|真实BFF/Agent PGRedisHTTP；admission序号、Run/head、执行计数|完整scope/fence设计与实现须先闭合，不用UI排队代替|
|T-C08（Web→BFF→Agent）|active及queued Run，Web可Stop/steer；A/B身份|.1 发送steer归同Run；Stop ACK后等待真实terminal，输入/队列仅按事实收口|.2 双击/重放control不重复terminal；无权/旧Run控制拒绝；.3 取消与自然完成竞争唯一winner，断线后查询恢复正确终态|真实浏览器+BFFAgent；control receipt/terminal identity/副作用计数|采用现owner控制契约；ACK不得当终态|
|T-C09（BFF→Web）|沿原C09.1–5的同一授权会话、真实双PG连接barrier与浏览器|.1–.3 原编号不变：同次四事实snapshot→真实writer提交后旧RR集合→fresh新集合与旧cursor精确replay|.4 原编号回收/变异有效性不改；.5 原编号浏览器五状态刷新、断线重挂、scope隔离；无权快照拒绝且不暴露水位|原C09.1–5逐项引用现表；PG并发+HTTP+浏览器，完整对象/metadata/截图|E91只后端组合；C09.4隔离变异及.5全用户路径待验，不改名或合并充数|
|T-C10（BFF→Web）|已发多delta和terminal的会话，明确retention游标fixture|.1 SSE中断后用原cursor重连，仅补缺失frames，拼接全文与未断线一致|.2 重复frame不双气泡，gap触发明确恢复而非跳号；.3 cursor过期/GC/进程重启按contract重取快照，另一身份cursor拒绝|真实HTTP断连/PGRedis+浏览器；seq/ID/digest集合、全文SHA|localStorage非事实源；过期策略按正式contract|
|T-C11（Web）|同scope两个真实挂载owner、StrictMode及外部injected连接|.1 第一个卸载仍保连接，最后owner卸载才close一次；重新挂载正常续流|.2 injected连接不被框架释放；.3 scope切换/重复effect清理不多开SSE、不传旧消息|Web真实组件生命周期+浏览器连接计数；close调用与network记录|E11限定已验；不代C10真实网络恢复|
|T-P01（BFF→Scheduler→Agent）|A/B、项目P、正式Scheduler可达、一次任务fixture|.1 正式创建独立ScheduledTask，列表不进入Conversation，P仅关联；修改/暂停/删除由owner回执持久|.2 B不能操作；同key重放不多建；.3 mutation失败/刷新/重复点击不本地假成功|真实BFFSchedulerHTTPPGRedis+Web；Task/Occurrence身份与列表|正式pin与用户入口前置；不把聊天消息当任务|
|T-P02（BFF→Scheduler→Agent）|可控业务时间的Scheduler fixture、UTC与DST IANA时区|.1 一次/周期计算next occurrence，对比春跳/秋回/跨日边界的已批准expected instants|.2 无效zone/ambiguous本地输入按contract拒绝或显式消歧；.3 停机跨misfire窗口按策略补/跳且无重复|纯时间边界+真实Scheduler恢复；UTC时刻序列/zone与occurrence IDs|DST/misfire具体策略若contract缺失先裁，不能凭宿主时区推断|
|T-P03（BFF→Scheduler→Agent）|正式Task、可断ACK的Scheduler→BFF/Agent传输|.1 同一occurrence重复wake/重复投递仅一个业务执行receipt|.2 同身份漂移payload冲突零副作用；.3 durable outbox提交后进程中断/ACK未知，重启读取重放同结果不新建Run|真实PGRedisHTTP；outbox/receipt/Run关联与计数|只用可控传输故障，不mock持久事实|
|T-P04（BFF→Scheduler→Agent）|两worker连接同owned schedule与可验证DB lease时间|.1 worker1认领后终止，lease到期worker2恢复同occurrence|.2 worker1旧generation晚提交被拒；.3 两worker竞争和重启无双执行/双receipt；DB时间而非sleep猜过期|真实进程+PG/Redis；claim/fence/执行日志、清理|Root独占进程资源；不杀共享worker|
|T-P05（BFF→Scheduler→Agent）|含已接纳及未接纳occurrence的Task|.1 暂停/删除停止未来调度；已接纳Run按其真实终态完成，串行dispatch只terminal后释放|.2 暂停与admission竞争保唯一结果；.3 重复暂停/删除/terminal投递不造取消或多放行|真实三ownerHTTPPG；task state/receipt/head关联|删除已接纳任务语义按现contract；缺失先裁不伪终态|
|T-F01（Storage→BFF→Web/Agent）|A个人/P项目权限；真实ObjectStore与scanner、owned上传对象|.1 上传已知字节/MIME/大小并scan clean，readback hash一致、正式可用|.2 超限/错MIME/无权项目拒绝；感染fixture隔离不下载；.3 上传取消/断线重试不留下伪ready或重复blob|真实StorageHTTP对象存储scanner+浏览器；对象hash、scan状态/回收|scanner double单列，不算真实感染验收|
|T-F02（Storage→BFF→Web/Agent）|F01已ready附件、另一用户B和项目Q|.1 列表limit1遍历无漏重；服务重启后原附件可下载同hash|.2 B/Q越权引用和过期URL拒绝；.3 重复刷新/断线下载恢复按contract，不扩大授权或串项目|真实Storage/BFFHTTP+浏览器；附件ID集合/授权码/下载SHA|URL签名不落报告，仅脱敏属性与expiry|
|T-F03（Storage→BFF→Web/Agent）|真实Agent任务产生已知内容作品，Storage正式receipt|.1 执行生成→发布receipt→BFF/Web卡片→预览/下载，artifact/asset/hash同一事实|.2 重复delivery不多卡，另一用户拒绝；.3 完成及活动时刷新后同作品，真实对象存储重连仍可读|真实模型或明确执行fixture+Storage/scanner+浏览器；receipt/bytes SHA/卡片数|fixture静态预置作品不充Agent生成；E53仅旧限定切片|
|T-F04（Storage→BFF→Web/Agent）|可控制发布超时/scan失败/过期签名URL的owned作品|.1 正常发布作控制；超时显示待处理/失败而非完成卡|.2 无权重签/错误receipt拒绝；.3 ACK未知重试返回同artifact、过期URL正规重新授权，有界且不泄漏底层URL/token|真实StorageHTTPObjectStore；发布次数/receipt身份/安全错误截图|不增加永久重试或凭空成功receipt|
|T-F05（Storage→BFF→Web/Agent）|带活引用/无引用/到retention边界的owned asset/artifact|.1 正式删除与GC按既有保留策略处理，仅可删eligible对象，活引用仍读一致|.2 非owner删除拒绝、跨项目引用保护；.3 GC与新引用竞争/失败重试不误删，物理对象与metadata最终一致|真实PGObjectStore；DB时间、引用集合、精确对象existence|retention若未裁先阻该分支，不forever skip或共享清桶|
|T-K01（Web）|无正式Platform回执的插件卡片、延迟与失败响应|.1 点击Add/Connect仅pending；成功必须真实receipt才标状态|.2 503/拒绝/无endpoint不得显示Connected；.3 重复点击/取消/刷新不靠local状态假成功|Web组件+浏览器；请求/回执与标签时序|E06限定已验，真实MCP接通另K05|
|T-K02（Platform→Storage→BFF）|有权发布Skill的A、整包fixture和真实Storage/Platform|.1 草稿→整包上传→校验→发布→读回版本/digest/文件hash一致|.2 zip穿越/绝对路径/符号链接或炸弹/错hash拒绝且无发布；B无权；.3 ACK未知重试同版本不重复发布|真实HTTPPGObjectStore+contract；manifest摘要与拒绝码|沿当前ZIP profile，不恢复旧裸URL或body自报tenant|
|T-K03（Platform→BFF→Web）|A/B账户、已发布Skill两版本|.1 安装/启用/禁用/移除/重装后fresh GET与Web显示同owner结果|.2 B改A安装拒绝、未知版本拒绝；.3 同key重放同身份，重复/并发改变按owner正式幂等/冲突规则（未定义先裁），刷新不复活已移除项|真实PlatformBFFHTTP+浏览器；installation ID/version/状态|历史personal切片不替当前消费者pin|
|T-K04（Web→BFF→Agent）|已安装启用Skill refs，有真实可加载包及撤权入口|.1 Composer按序选择refs并提交，Run冻结集合与真实加载阶段一致|.2 禁用/撤权/另主体ref拒绝零工具加载；.3 发送后改选择不修改已接纳Run，重放receipt同refs，[]不伪造Skill进度|真实Web→BFF→Agent→Platform；admission/phase/加载证据|HTTP5正式消费者前置；选中UI不当ready|
|T-K05（Platform→BFF→Web）|A可授权MCP连接、provider测试账户/服务及B|.1 connect→scope consent→owner receipt，目录、已连、需重连三态有据|.2 拒绝scope/错audience/他人connection拒绝；.3 撤销后刷新失效、重连新receipt，ACK未知不双建|真实Platform/providerHTTP+Web；opaque connection ID/安全状态|正式mutation/凭据边界未实现先实现；不保存token到证据|
|T-K06（Web→BFF→Agent→Platform）|K05合法opaque MCP ref、Agent执行与可撤销授权|.1 选择ref后每次实际tool call取得fresh授权，args绑定真实身份|.2 撤销后下一调用0 provider请求；错ref/注入tenant/复用过期proof拒绝；.3 重试/取消不复用失效授权|真实PlatformAgent/provider；逐call authorization与provider计数|旧free-text mcp_servers单轨替换后执行，无fallback|
|T-K07（Platform→Agent）|正式tool closed schema/profile、权限与可慢响应工具fixture|.1 合法输入执行并校验输出；.2 额外字段/类型错/越权/恶意提示不突破工具权限|.3 超时取消有限，晚结果不再次投递；schema漂移与错误输出fail closed并给安全code|contract+真实工具transport/授权；输入摘要/调用数/安全错误|受控工具fixture不等于外部provider可用性，分别列层级|
|T-A01（Agent→BFF→Web）|同会话简单提问与需计划复杂任务，含子Agent|.1 简单任务仅回复；复杂任务主Todo完整替换、有序状态推进，[]清空|.2 101项/超限/非法status拒绝不推进水位；.3 子AgentTodo不覆盖主表，重复/并发/replay/刷新保同Run事实|Agent真实PGHTTP→BFF持久投影→Web；列表/seq/截图|E35/E98只owner切片；正式消费者与策略待验|
|T-A02（Agent→BFF→Web）|有Skill refs的实际Run及可控制resolve/load失败|.1 resolving→loading→ready来自真实阶段，展示同activity/preflight身份|.2 failed有closed error_code，非failed带error/null拒绝；无选择不伪ready；.3 重试新preflight不串旧phase，刷新一致|真实ownerHTTP→BFFPG→浏览器；阶段源seq/identity|HTTP5 source_refs活动min1、顺序/唯一性/容量按机器门|
|T-A03（Agent→BFF→Web）|真实工具成功/失败/慢调用；安全canary原始payload|.1 显示running/completed/failed与固定display_code，activity/segment不混assistant身份|.2 raw args/result/stack/token/隐藏推理不进入public ledger或页面，越界字段整帧拒绝；.3 cancel/重连不伪completed或双行|真实调用+PG投影+浏览器；closed对象、源seq/网络脱敏/截图|不要用空TOOL_CALL_ARGS/RESULT冒充详情；HTTP5消费者前置|
|T-A04（Agent→BFF→Web）|同Run多个group/item的waiting完整pause，A/B身份|.1 同次提交全部required decisions→accepted→native consumed→继续执行，完整revision恢复|.2 stale pause/缺项/非法decision/校验错明确拒绝，B0写；.3 同key重放、ACK未知、刷新重试不重复工具副作用|真实Agent checkpoint/PG与BFFWeb；pause/revision/receipt/执行计数|resume回执不当native已消费；unknown需查询恢复|
|T-A05（Agent→BFF→Web）|各有Todo更新、Skill loading、tool running、HITL waiting、delivery ready的五暂停点|.1 五点分别硬刷新，先耗尽同snapshot anchor的有界process页，再严格从同watermark续流还原完整集合；terminal及后继queued仍保最近START过程|.2 另一scope不可见；.3 断线重挂/重复frames/后台完成不丢Todo清空或旧phase，不多作品卡|真实浏览器+生产HTTPPG；每时点前后完整状态、cursor/截图|复用C09一致快照机制，但五点必须逐一实际运行|
|T-A06（Agent→BFF→Web）|主Agent委派两个子Agent，一成功一可失败/阻塞|.1 安全opaque身份/segment区分并发子任务，主回复只包含正式汇总|.2 私有prompt/tool raw不公开；.3 子任务失败/用户取消时所有owned任务有界退出，重连不把子文本拼到主回复|真实执行/线程进程+HTTPPG+Web；状态/汇总/终态计数|纯native cleanup已验不等真实provider取消；每种backend另记|
|T-B01（Billing）|冻结price revision codec、整数/rational边界向量|.1 合法revision canonical digest相同，7/5有理数精确编码（实际成本计算归B05）；.2 小数格式/溢出/负值/额外字段/恶意结构拒绝|.3 同revision不同内容冲突，序列化重读不改变数值/摘要|纯规则/contract；输入分类、expected整数与hash|E07限定通过，真实收费另B04–07|
|T-B02（System→Agent）|System正式route/model/provider revision、实际模型可用|.1 每call/attempt记录实际route digest/model/provider与usage来源，重试独立attempt|.2 未授权route拒绝零provider调用；.3 失败/晚usage/缺用量保持unknown，不补0或猜tokens|真实SystemAgent/provider；attempt ID与脱敏usage/proof|技术route不是调用证明；凭据值不落证据|
|T-B03（Billing→BFF→Web）|Billing授权赠送权限A、普通B、明确账户余额|.1 正式赠送命令→持久ledger→余额/流水Web一致；重复同key一条入账|.2 B赠送/越权账户拒绝；.3 撤权后旧会话0入账、ACK未知按receipt恢复，刷新不假充值|真实BillingHTTPPG+BFFWeb；ledger ID/金额/余额等式|禁止直改DB充账、免费补偿绕余额|
|T-B04（Billing→Agent）|实际attempt前余额充足/不足两账户，可控并发调用|.1 每attempt调用前有reserve，余额不足0provider请求|.2 并发reserve总额不超预算、跨账户拒绝；.3 同key重放/ACK未知查receipt后再调用，不一张许可跑整Run|真实BillingAgentPG/provider；许可→调用时序/余额与预占等式|各attempt规则按正式授权接口，不猜全Run预算|
|T-B05（Billing）|冻结采购价/币种换算/revision与不同舍入边界|.1 采购成本×7/5再按批准换算/舍入结算，前端只展示owner值|.2 非法币种/负值/越界ratio拒绝；.3 中途改价不改已冻结attempt，重放同结果|Billing规则+真实PG命令；整数分项/版本与总额|7/5是加价40%；具体舍入/汇率顺序以ADR/contract，无规则先裁|
|T-B06（Agent→Billing）|已有reserve与真实usage evidence、可控晚结果及失fence|.1 正式结算/增额/释放保持余额+预占+流水守恒；重复证据不重扣|.2 跨attempt/漂移usage拒绝；.3 结算ACK未知、旧worker、晚usage、进程重启由reconcile闭环而非terminal强结|真实AgentBillingPGHTTP；证据/ledger幂等键、对账差异|unknown成本保持待对账，收费资格依B07裁决|
|T-B07（Billing）|失败/取消/部分输出/unknown成本四类真实事实样本|.1 先冻结每类收费资格、保留/释放/结算与通知业务规则，再给精确余额预期|.2 待裁后覆盖无权/重复证据、并发取消与晚usage；.3 重启对账不改变已裁资格|决策阻塞；当前只整理事实样本与待决问题，不执行收费结论|禁止预设全免费、全release或全收费|
|T-B08（Billing）|用户要求的最终支付阶段；渠道sandbox与有权账户|.1 后置执行订阅/checkout成功及refund，owner账与sandbox对账相同|.2 webhook坏签名/错账户拒绝；.3 重复/乱序/ACK未知通知不重复入账，取消checkout不假充值|真实渠道sandbox+BillingHTTPPG+浏览器；脱敏事件ID/金额与对账|支付最后；未到阶段不以mock算支付通过|
|T-U01（Web）|已登录A、正式套餐/模型目录与Home提示入口|.1 点提示只写草稿，POST/Run/计费计数均0；明确发送后才admit|.2 不可用模型/能力不作营销假承诺；.3 More/返回/切项目/刷新保正确草稿且不自动发送|真实浏览器+网络计数+owner查询；截图/0mutation证据|E41纯门不替浏览器；正式模型/套餐owner前置|
|T-U02（Web）|中文IME、桌面/窄屏，文本与合法/非法附件fixture|.1 多行输入Shift+Enter换行、Enter按配置发送，IME composition Enter不误发；外观无多余内嵌方框|.2 空/超限/上传中禁发且提示明确；.3 pending双击不双POST、Stop不丢草稿，取消上传恢复输入|真实浏览器/键盘IME+axe/截图；POST数和focus|视觉确认按用户ChatGPT偏好，不凭组件库名算验收|
|T-U03（Web）|桌面/窄屏、多项目/会话、长文本代码表格与失败消息|.1 对话/rail/作品布局可读可滚动，长内容不遮composer，失败footer靠近所属正文|.2 窄屏操作无不可达按钮/横向溢出；.3 切会话/开作品/返回保滚动与scope，错误不生成假retry|浏览器不同viewport/截图+可点击区域检查|公开terminal retry未有API不放假按钮；设计确认与功能证据分开|
|T-U04（Web）|已实现loading/empty/error/disabled/reconnecting/partial/success状态fixture|.1 全键盘完成登录后导航/输入/控制，focus-visible顺序合理，axe无违例|.2 屏幕阅读标签/错误关联/reduced-motion不漏状态；.3 离线重连/取消弹层恢复焦点，视觉与bundle满足既定预算|真实浏览器axe/键盘/视觉+build预算；报告与截图|预算阈值取Web现ACCEPTANCE，缺阈值先定不临时放宽|
|T-R01（Root）|Root登记的自有UUID库/key前缀/进程组，共享资源只读基线|.1 正常执行结束仅自己资源删除，库absent/自有keys0/PGID终态|.2 setup半失败/cleanup一项失败仍尝试其他独立回收并报错；.3 ACK未知按fsync intent精确查，不扫描删除unknown|真实资源包络验证；owned ledger、cleanup与共享基线|E03仅该次隔离已验，每新执行仍独立记录，不新运维体系|
|T-R02（各owner→Root）|各owner正式可执行产物/现ACCEPTANCE及owned进程资源|.1 启动health/ready条件正确；实际请求超时/取消后无late commit；SIGTERM有界drain|.2 启动半失败/依赖断连不ready，旧lease拒写；.3 active/queued/native/backend构造中退出后恢复事实、无悬挂资源|真实进程HTTPPGRedis及所需backend；PID/时间线/terminal与回收|现System/Agent片段不充全owner、真S3Docker/模型分支|
|T-R03（Root/各owner）|A/B同tenant与C跨tenant、恶意输入、secret canary与固定依赖|.1 每公开/内部受信入口权限矩阵正控；.2 ID置换/注入/oversize/错proof拒绝0副作用|.3 重放/过期/撤权/日志异常无token/raw泄漏；源码/依赖/secret扫描保全部结果，跨ownerSQL门0越界|contract+真实HTTP+扫描；安全code/脱敏canary命中数/报告SHA|扫描工具缺失记未验，不拿lint代scan或创建部署角色|
|T-R04（Root）|全部owner当前验收完成、兼容pin冻结；只自有备份恢复fixture|.1 正式组合真实用户旅程与release smoke绑定同构建image/artifact SHA；.2 备份/恢复自有持久事实后比对identity/幂等receipt/未决outbox并恢复执行|.3 恢复中断/重复恢复/依赖失败不重扣不重复执行，资源完整回收；失败不得以历史绿色替代|真实组合/浏览器/PG恢复/镜像smoke；SHA清单、前后事实摘要|Wave7最终门；SLO目标非压测实测，不扩部署工作|
|T-S01（System→IAM/BFF）|System具名Site/Host/Workspace/Runtime/Policy及A/B授权|.1 正式HTTP创建/读/变更/禁用按version与生命周期持久，消费者看相同revision|.2 unknown/disabled/expired/越权拒绝，secret字段不返回；.3 重复命令、并发版本冲突、撤销后重读不复活|真实SystemPGHTTP→IAM/BFF；实体ID/revision/错误与0写|E88只lifecycle切片；不新建万能configs|
|T-S02（System→Agent/BFF）|正式模型目录、两授权路由及可控故障gateway|.1 用户选择实际模型，Agent按固定revision/digest调用对应gateway，结果来源可核|.2 不可用/越权模型拒绝；.3 重试/故障切换仅获授权范围，超时取消不静默换模型，重放冻结revision不漂移|真实SystemAgent/BFF/provider；route/attempt摘要与调用目的地|模型配置存在不等真实调用成功，用户网关单独验|
|T-G01（Platform→BFF/Agent→Root）|当前Platform及所有BFF/Agent消费pin、remote/path/env/schema/Redis映射清单|.1 在批准cutover切片一次替换正式身份，所有消费者构建/调用/读持久事实成功|.2 旧capability alias/path/proto/env不再可达或被明确拒绝；.3 中断回收后仅一个正式写入身份，无旧新双写|静态引用/contract生成+真实ownerHTTPPGRedis；身份清单与0旧路径|物理当前kokoro-capability事实保留至真迁移；不冒称改名完成|


## 九owner验收层级覆盖（同一任务矩阵的覆盖检查，不另算完成数）

|Owner|纯门/契约|真实依赖integration|实际进程smoke|跨owner/浏览器消费|
|---|---|---|---|---|
|Web|T-Q01正式ddd38c5限定纯门通过（E41/E42）；E20/E22失败历史保留|无业务数据库；E53正向session/adapter真实通过，其他分支待验|T-R02全组未验|T-L01/T-C06具名范围通过；其余L/C/K/A/U按原矩阵|
|BFF|T-Q02通过限定纯门|T-C01过滤切片通过；全owner资源套件未验|T-R02未验|T-Q10/T-C02 Web消费者未验|
|Agent|T-Q03待复测：E80配置/E82 fixture修复已本地提交；当前pure1937与local172分别通过、无skip/forced_close；E76四安装正向切片已验但不是最新README重建artifact|历史限定PG/HTTP切片保留；完整负向安装/installed DDL/HTTP/S3/Docker/production close未验|T-R02全组未验，仅fixture生命周期已验|历史发布HTTP4限定旅程保留；HTTP5/Todo/安全过程候选及消费者未发布闭环|
|IAM|T-Q04本次通过限定纯门|现host51通过；全部真实schema/PG/Redis/OAuth矩阵待复测|T-R02全组未验|E53固定tenant正向浏览器T-L01通过；T-L02–05负例/权限仍待复测|
|System|E81当前119纯测/十门与源码独立审通过，9a4e98e本地提交|E77同源码单owner真实PG fresh23断言22表通过；业务HTTP/Redis/路由组合仍未验|T-R02全组未验|BFF/Agent模型绑定T-S02未验|
|Billing|T-Q06待复测；T-B01纯codec通过|真实钱包/ledger/T-B03–07未验或决策阻塞|T-R02未验|正式收费未验；支付后置|
|Platform|T-Q07待复测|真实PG/IAM/Storage/Connect授权待验|T-R02未验|Skills/MCP使用T-K未验；身份cutover T-G01未验|
|Storage|T-Q08待复测|E53限定真实作品/下载hash通过；完整上传/scan/故障/GC T-F待复测或未验|T-R02全组未验|E53发布组合BFF/Agent限定旅程通过；完整T-F与Platform消费未验|
|Scheduler|T-Q09待复测|真实PG/Redis/lease/outbox T-P未验|T-R02未验|BFF callback/Agent dispatch未验|

## 已执行证据与版本绑定

|证据|绑定版本/范围|实际结果/存档入口|
|---|---|---|
|E80|Rootc2eebe91/Agent17c73541候选→dbaf4f9配置本地提交|Root11pass/0skip+Ruff/类型四门0/8hash保持，manifest /tmp/kokoro-r115-agent-example-root.json SHA95b4ef5bc8719ee535f6f013e67b030b3992f1c44815859ffae11ca21b1746ab；独立审2a18fb4f 0，E78缺文件关闭；Root旧模板删除/链接改指，发布/fresh另验|
|E81|Systemaa4e42e5候选→9a4e98e本地提交，source da4675b9/test45bd5286|Root十门0/119pass/197hash保持/owned终态，/tmp/kokoro-r115b-system-pure-root.json SHAcb0dc907c96d41023bfc4e03f381ea814e486ab05903f928ca29cfb6fd0e35ec；同源码E77实际PG证据核同非新跑PG；独立审31519cb2 0，原Corepack验证环境失败ff5e414b保留；其他System资源未验|
|E82|现fixture test1971ccb5 RED→f4a8238e GREEN→2653bcc本地提交|Root2callfail manifest96884929；完整17file/四门0 manifest6513cf7f；原170+新2 local172pass/0skip/blocked0/336freeze，28child170thread终态/87port rebind/forced_close0，/tmp/kokoro-r115-agent-local-root.json SHA9420b6486a1f7321f71ad6dc83901f68cbf2e88a6e97c2b72bb34bd47e7768c0；独立终审463f927f 0，原E79 P1关闭，不关闭全T-R02|
|E83|配置/fixture均冻结的1937 pure原节点；提交前同候选|Root1937pass/0fail/0skip/615warning/resource0，370明确文件含YAML/helper前后同，进程组终态；/tmp/kokoro-r115-agent-pure-default-root.json SHA3f5c1ab15b596c06bb197ce11a2ebd347f0f467b2f8e14a9f7eec74a9cfb6f2b。和E82分开执行，不伪造单次2109；完整installed负向/DDL/HTTP/发布未验|
|E76|Rootdf781255/Agent17c73541+冻结候选；四正向安装布局|Root实际10+16步骤0，115 runtime/source wheel与sdist rebuilt wheel、venv/target均安装；E49具体缺陷关闭。/tmp/kokoro-r114b-agent-installed-root.json SHAfd96561df2f523c05eaf60a35882e3d089e031f5a443ca8e6bff1c8d0943a621；/tmp/kokoro-r114d-agent-installed-matrix-root.json SHA81f6da0d4cbf521a9a60fdcc004ff6ecc2d51decd4374ea0ff286491466455c8；独立终审d13a7f25为0/0/0。完整负向/DDL/HTTP/发布未验|
|E77|Rootdf781255/Systemaa4e42e5+source da4675b9/helper efd2f061/schema df339b00；单owner真实PG|原entry exit0/23断言22表/catalog/拒重入，精确临时库后查不存在，197hash保持、owned终态；manifest /var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-r114-system-fresh-dlt4tpud/manifest.json SHAcaec26bf5ee8616f654acd3e9fe0b2bcdd2d3fc9e91d18ad1f52f93db426218d；独立终审f3867b76为0/0/0。其他owner组合/业务HTTP/Redis未验|
|E78|现配置test4044d9fb；Root真实RED、owner GREEN待Root|Root10pass/1缺文件fail/0skip，/tmp/kokoro-r114-agent-example-red-root.json SHA40c56966762247388f646b2f70ca49ebe7540c75b996b6e86a21030fd41785de；owner /tmp/kokoro-r114-agent-example-green.json报告11pass/0skip，原turn01a0fe9e-3834-7010-bdc6-ef06d001fe79 completed/idle。未Root复跑不接受GREEN，不冒称Root旧模板已删|
|E79|Rootdf781255/原partition81914ecd local170；336明确保护文件|Root170pass/510phasepass/blocked0，child28/thread168终态与85port rebind；/tmp/kokoro-r114d-agent-local-root.json SHA5e64c47a563b643c6a7549b47ef60adcb12e3d45eea91fd49d82e2688f9594dc；独立终审939abc49，web_fetch漏close为P1，1socket外层强制close不证明fixture正确。原379口径已纠正336；不关完整T-Q03/T-R02|
|E64|Rootb2983007/Agent17c73541+五文件c07dfbd0manifest；源码切片|Root20085七门0/3架构+140回归通过/369hash保持；/tmp/kokoro-r110-agent-three-fail-root.json SHA4cb16756af58e8c9d721d27cbcb209b1a6e2e93a6d094efde97f9ded9963e990，log321a62552b0849c38b0c5783d51c415b8fec4d020d0fee893ec9bde1ceedc85a；源审 /tmp/kokoro-r110-agent-three-fail-final-review.md SHA3fae1846d45fc627c67561dc0abd2f47214a664ec80e5d39b7f58e2068c901de，0/0/0；仅该切片不关安装|
|E65|固定Python3.11工具pin+两原consumer生成器；源码/生成字节比对|Root89877两check exit0，manifest /tmp/kokoro-r110-agent-codegen-root.json SHA83b4a0c7933bd6b7dcd8aa3741736655f621d57777e053177e351319a69fd212，log03cd5a0cdbe8085eb662283fbc477bb5d57ce8979eace89fa035624b0842325b；源码/generated保持与builder残留0。原离线准备失败566af123/后供应95c7d928独立记录，不把供应当比对或Agent安装|
|E66|现architecture93000280新增import recorder/原archivec679af03；只RED|Root84765实际1行为fail/0setup/guard0/369hash保持；/tmp/kokoro-r110-agent-archive-red-root.json SHA f5989e5555f980299705a820a3b43f7b1e60a4c7c87ecb9b0421a135a37b9487，log5293e22d2469996a4b2ce1e8e8e4dd0d0becab6255c0d015a4ad043176379b62；独立RED审e1c3f57c…0/0/0；archive测试fixture候选在途，实际S3未验|
|E67|现Platform transport6个loopback fixture原cases，源/pin冻结|Root32696实际6pass/1PG未选/3.46s；/tmp/kokoro-r110-platform-loopback-root.json SHAa3ff1d3b3eca520e7e41223358b5adfb721cc04075f98578ca43af5bfcf68979，loge01442564cb10f5f700a0c545759f35eecfbb7ed4326ee60f43c377de31dd5f4；fixture6listener关闭/线程终态/端口rebind、blocked0、frozen保持。fake owner配真实HTTP，不当正式owner或Skills/MCP用户链|
|E62|Root5e25035d/Systemaa4e42e5+source366b886b/teste97a5e00/helper efd2f061；纯门|Root17470实际10gates exit0/106pass，manifest /tmp/kokoro-r109-system-pure-root.json SHA15e349a995d95feca73b86cd46fcf0f516d5e5b8a62077c9a2899bd4da6b9fb7；log SHA7b62b88ba7330524e7153f5cc29168fbfa12c7be954c88a88d285d67e02baba5；独立源码审 /tmp/kokoro-r109-system-unknown-final-review.md SHAeff656ac1a2cb75a56e4c7df74489af4b10822b58cf366bd50b43b7b3e052dbe，0/0/0。审报告先于Root终态，Root随后独立核终态，不称审员预见输出；197文件当前相符，真实资源未验|
|E63|Root5e25035d/Agent17c73541+冻结源候选；完整contract RED|Root46970实际test exit1，669pass/3行为fail/6guarded setup/1deselected；pytest14.25s、wrapper16.256s；369 Gittracked+nonignored文件前后hash相同。manifest /tmp/kokoro-r109-agent-contract-red-root.json SHAbdc5debc6eda21139ce5527b9c43310cced532f1b66fbe5f8093bd4f7e827af4；log SHA4517efa15b5f7b09816b3a4a2874c4a7e28d47466d3ceb8be86c4641edb31d31；Failure generator精确6调用（1正5负）实际运行，不是6次成功；两codegen未到比对，完整unit/安装未验|
|E59|Agent17c73541+冻结三源码473c54dd/cc46248d/924ab9ea与四test；Rootda04f2ad|Root原30506exit0，139pass/1 generator未执行/10.14s，Ruff/直接Node类型0；manifest /tmp/kokoro-r108-agent-proof-green-root.json SHA03e568041f1222da8fda87bfee04f0ba65abf385261ca34d2605c1e959d1d1fb，log SHA1b60a61b0c7302318d7026098625877d91777699b2ceb84e71290b1b0c65a26e；独立报告/tmp/kokoro-r108-agent-proof-green-final-review.md SHA58394f2b0c5b8d04ae71e8f3b7df948710a5f5ed4e1130735d18a6d851559d59、0/0/0。原Root58 proof57pass/1fail及边界修复保留；不是完整source/安装门|
|E60|Systemaa4e42e5+source da1fa288/test2f7dc98e/helperefd2f061；Rootda04f2ad|Root原58556实际10纯门exit0，9files104pass/0fail/0skip；全tracked前后保持，OS deny network、无真实资源。manifest/tmp/kokoro-r108-system-pure-root.json SHA54b87aba62e1f072e3b6c8443de6c1e99434161f19a112c79c4e9865a104319a，log/tmp/kokoro-r108-system-pure-root.log SHAb0a4b379369bea0ae0c06b796db503d66332628698b52ccb30fc7fe55a486108。独立审/tmp/kokoro-r108-system-green-final-review.md SHA78430667ea2d81a1f84c3f011a95629578a7e8176b481f8fa7372b5d05d67648、0/1/0，undefined哨兵P1待RED；不把审查缺口假称104测试失败，不关闭T-Q05/R02/Q12|
|E61|Agent frozen runtime lock，Python3.11.14；仅依赖准备|Root29970exit0，115锁定runtime包require-hashes/only-binary、兼容检查0；owned供应venv删除。manifest/tmp/kokoro-r108-agent-locked-supply.json SHAe162239dcca9a9651b246a6c55b98fecf260cd4425ace6b25fa9b59218b7f9a6，log SHA54af48efba15776a99521dda2ebc2841547206447e6ed3cbf4a0fb6e4a07a0a3。原离线缓存annotated-types缺失失败保留；没有Agent安装或业务测试|
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

|E42|Web正式main ddd38c5bdc1eab01f802e1fc993f7b597d707a64；七Home源/test+Web CURRENT精确8路径|Root7822新定点153pass/3files/7.93s，/tmp/kokoro-r102-root-home-focused.log；748外围和八hash保护通过；原66387 commit/普通push终态exit0，HEAD=origin/main=remote main且clean。E41完整纯门/独立0仍绑定相同冻结源；Root gitlink/provenance尚b497，Home真实浏览器未验|
|E43|Root84255f24+test575eb52bb8dee54012187b3a0c8947fa7e36f13ef56338b8a2ba088e0fd9dfe8；driver c65d7e8a不变|Root54404现整文件真实33fail/549pass/12.07s，/tmp/kokoro-r102-root-snapshot-http-red.log SHA46fe555d482acc67aaa7ce15413f851cd7289495f961800dec021af35c092190；32向量实际readSnapshot→until→partial→finished→formatter→catch，两probe精准，无raw敏感；原1 HTTP expected升级，其余控制保留。独立/tmp/kokoro-r102-snapshot-http-red-review.md 0。GREEN另授，不是产品根因或W2通过|

|E44|Root84255f24+driver00a12288de69ea3d0dc331b6fdd2efe9d87e72c502ff0f5e964093d56d70ce8d/test575eb52b；runner/helper/uv.lock不变|Root52486整文件582pass/11.51s、Nodecheck0，/tmp/kokoro-r102-root-snapshot-http-green.log SHAbbaf1411d04fbe5aa722215017bf37cc1772e6fd255c9a4412651b6cc71b4bcf；独立/tmp/kokoro-r102-snapshot-http-final-review.md 0。32 actual HTTP/status-code正负与原550控制，原1expected仅HTTP后缀升级、无敏感/新增I/O/硬门变化；本行仅诊断纯门，真实T-C06仍失败|
|E45|Root84255f24+Webddd38c5 gitlink/49发布commitrefs（45blob）、两诊断文件及四台账组合候选；其他owner不变|Root73614四组合pure386pass/45.98s，/tmp/kokoro-r102-root-composition.log；topology PASS、compat exit1仅13declaredbroken/16edges/0violations，49refs已核committedblob digest不变。精确8路径最终审/Root发布/fresh严格旅程待后继，不算T-Q10整组或T-C06通过|

|E46|Agent17c73541+冻结源/机器及HTTPtest6b71e3de5e0061e0a194aa53d209b0668227fcb9b0b8319478abfb5041ff747a；最终fixture/Root wrapper独立0|Root78231/child7938终态exit1，36项1fail/35pass/100warnings/11.44s；原log记录SHA2960116c0f8eb0abf934425d4706edc06cba6db47a0b6a055a1ca72501abed82；审计更正：该raw文件后被Root第二wrapper误覆，现文件不再匹配原SHA；原owned.json与当时工具捕获保留，不重建伪原log。唯一fail旧stale直接await抛ProgressAuthorityLost；新增Todo正式RunEmitter→PG→HTTP分页/replay/tenant+subject隔离通过。owned库deleted=true/DB15endempty=true/childterminal=true/sourceunchanged=true/cleanup=[]。已另授typed expect迁移，未全36通过，不关闭T-Q03/T-A01|

|E47|Agent17c73541+原冻结源/机器；现HTTPtest2884a4fb7d4ab04e7e4849105fd78a64327b6e7d0366df27333ff8383fd8e0f4；typed-only import/raises，不改production|Root97725终态exit0：36pass/100warnings/11.21s；/tmp/kokoro-r102b-agent-http.log SHA66c0da0e763a4be339cdbe4bcd22100d275b6f06f50f78a5526fd9290d89015a、owned.json。created/deleted=true、DB15首尾空、childterminal/sourceunchanged=true、cleanup=[]。原RED rawlog误覆审计缺口见E46；GREEN字节核验另存且manifest明确collision，wrapper加防覆盖guard。仅本文件真实PG/Redis/HTTP，typed最终只读审 /tmp/kokoro-r103-agent-http-typed-review.md：代码0/0/0、审计P2=1（原RED rawlog覆盖缺口）；不关闭T-Q03/T-A01、不含真实外部模型/BFF/Web展示|
|E48|正式Rootfa4525e48961bcc6954f453643e3a4c6dfea3b62、Webddd38c5及其余五owner固定版本，见/tmp/kokoro-r102-root-w2-owned.json；同fresh源准备2010 exit0，四harness hash匹配|Root99439终态exit1：REAL_MODEL_FAILURE:second-partial-active-cause-snapshot-http-status-429-code-other-head-active-match-messages-4-partial-pending-empty-finish-absent。/tmp/kokoro-r102-root-real-w2.log SHA3db31d9dedd9346293cfb31a1f62a244b12f84a04342393b9e29286fba4fa9de、owned.json及其中evidence；cleanup=[]、bucket_cleanup_exit0且404。原600s/两POST四Message/活动刷新/全文/作品hash/他人404不变，不含Billing或AgentHTTP5候选。429已观测，不臆断唯一产品根因；T-C06继续失败，原历史保留|

|E49|Agent17c73541+冻结候选，现wheel230b41bc0038927f5ad5abf588c6ffa6f5fd22dbe7c78472fd810749e4692c25；167 Python文件/DDL与现源匹配，机器资源未随包|Root私有r104b实际exit1：安装exit0、已安装checker入口/独有target origin验证/checkout外cwd与Python -I，missing-installed-openapi、network_attempts=0；/tmp/kokoro-r104b-installed-checker-red.log SHA745410339bbac33ba78c00a400ffbb599e79199864fc68607d4fd3dcf775881d及.json，临时target已删。依赖复用现venv/Python3.14.3，非独立完整依赖安装门；只证安装checker真实失败，T-Q03转失败，PG65/HTTP36局部结果保留。首r104缺ValueError分类日志保留，不冒充业务额外通过；source/Git/共享资源未改|

|E50|Rootfa4525e4 fresh/IAMe3c/BFFbb610ea/Webddd38c5正式组合；私有quota wrapper eee87d8289b63f6b3ad6ef745b52f65cdfdd53c0fd5af2555e262e705f6016d8，独立资源门最终0|Root58343实际exit0，正规IAM登录及列表200/snapshot404正控后，25ms GET-only第97个本轮样本429/session_rate_limited/Retry-After存在、4.933s/零mutation；三Node组terminal、BFF/IAM/Web自有资源清理verified。/tmp/kokoro-r104-snapshot-quota-probe.log SHA39b122ff6768d0b06eb92d4c71701968e7a7f85aec0f1f59168a0bbaf4fb4de4、.json SHA6c3bc9f7978619711f8fb206f8aa6795d4cdd79fb5ba2400737d1e323bc517a1。expected_cutoff只准入诊断，不称完整Product Session或Chat通过、不拿404当200快照；原E48仍失败。资源审初错基类P1已正式撤回，最终0；wrapper记录成功创建库字段，不制造实际setup失败|

`/tmp`是当前机器运行证据位置，不保证永久保留；本页与progress已提交保存版本、结果与失败分类。后继运行须在同progress追加脱敏摘要，长期验收报告归既有reports目录；不得仅留临时路径或截图口头宣称。

## R106 新执行证据

|证据|绑定版本/范围|实际结果/存档入口|
|---|---|---|
|E54|Root e59f8688；Agent17c73541+冻结候选，三test与374快照保持|Root16649实际exit1：12fail/69pass/1generator未执行/9.17s/guardresource0；/tmp/kokoro-r106-agent-installed-red-root.log SHA9c3dc9bf1666aeb577fe3f0c069d003e763568ffac52d5d1660c7dbb6af48d03及.json。独立RED0后授权原WIN03精确7源码GREEN；T-Q03安装仍失败|
|E55|Systemaa4e42e5 clean；Node24.20.0；当前A–E全部纯门|Root43682同checkout实际exit0：10gates、9files97pass/0fail/0skip；197tracked hash保持。/tmp/kokoro-r106-system-pure-root.log SHA409299d54c9e397df41bb5400b9fb3db461842f9747d6762b32d1212e7618d18及.json；独立最终审0P0/0P1/1非阻断措辞P2（/tmp/kokoro-r106-system-pure-final-review.md）；不包含10资源入口/integration/freshschema/provider/runtime/image，T-Q05仅当前纯门已关闭|

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

1. T-C09、T-A01–06：Agent HTTP5已正式发布；沿R123 BFF设计裁决→真实行为RED→正式消费/持久安全过程快照→Root纯门/真实PG→BFF发布→Web消费。R123四设计文档与只读审查只记待审查，不提升为测试通过。T-Q03剩余真实外部资源/进程分支另待验，不用重跑已关闭定点代替推进。
2. T-Q05现候选E74纯门119与E77单owner真实fresh23断言/22表已通过；System业务HTTP/Redis/runtime T-S/T-R资源门与全部owner同应用库schema组合仍待验。所有新资源继续登记精确owned身份与终态回收，可与Agent独立推进。
3. T-C02–05、T-C07–10、T-L02–05、T-U01–04：项目/独立会话、路由和草稿、竞争/取消/恢复、登录负例、真实Home/输入框/布局。T-C06、T-L01已按E53关闭具名范围；不反复等待结束句柄或重测已关闭路径来替代推进其他分支。
4. T-P01–05、T-F01–05、T-K02–07、T-A01–06：按owner artifact与依赖顺序验证独立任务、上传/作品、Skill/MCP选择与授权、Todo/工具/审批/子Agent及五时点刷新。E53限定作品证明不覆盖整组T-F03及其他失败恢复分支。
5. T-S01–02、T-G01、T-Q10/12、T-R02–04：当前契约组合、单应用库owner schema、系统模型路由、Platform身份收敛及全owner最终研发验收。
6. T-B02–07：真实证据→授权赠送/余额→预占→结算或恢复；失败收费规则待确认，支付T-B08最后。每个切片都回填同一测试ID，不新增重复计划。

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


## R182 原用户加载故障：真实帐号 HTTP 边界，未冒浏览器恢复

- 原用户会话 conv_ffd7 保持 T-U04 P0 FAIL/OPEN。Root IAB确认 selected tab1；Page.stopLoading 在焦点准备超时，冗余tab关闭调用也超时，均未取得成功状态。未新增页面、重启共享组合、清浏览器/PG/Redis数据；原45606/46036 live。原页缺同document DOM/网络证据，不能归因为React、网络或IAM。
- 原Web负责人只读 /tmp/kokoro-r182-loader-callchain.md（2b1a183b）：同文案包括认证前整页loader、首次Runtime mount和会话hydrate壳内loader；effect/commit不前进与snapshot pending必须以互斥DOM及同document请求区分。加载关键9文件source/runtime相同；未同步Move差异不冒该故障原因。
- Root本次不是匿名探针：私有凭据只在内存使用，正式 /login302 → authorize302 → IAM form200/CSRF submit303 → fixed tenant continuation303 → callback303 → /app200，无权限扩展、无模型调用、无业务写入。随后 /api/auth/session200 authenticated=true；原会话SSR200/35ms、server-admitted=true、两loader标记false；原会话snapshot200/36ms、合法顶层字段且无error；该HTML列出的47个同源脚本/样式均200。证据 /tmp/kokoro-r182-authenticated-read.json，读取脚本 /tmp/kokoro-r182-authenticated-read.py 不保存cookie/credential/body。
- 初次资产检查因现HTTPhelper禁止percent-path而退出SmokeError，尚未请求资产；后继使用仅HTML列出的/_next/同源、有限大小资产请求完成47/47。没有弱化生产路径校验。API成功不等于原IAB标签可用，T-U04不转绿；下一行动需要恢复原页控制并取得互斥DOM/同document请求，禁止继续blind timer/重试设计。
- 补记 R181冻结门：Root Web31556完整check最终 exit1，contract258/architecture50/lint/types0、默认2444pass/1fail/164files/121.98s；唯一ko覆盖率1503/1584=94.886%低于既定95%，此前10个Move失败已消失但不称全Web绿，build未到。生产Move仅候选未同步原runtime，UI真实用户Move旅程仍待。
- 补记 R181 BFF：Root29955 Project deadline/replay正确RED23pass2fail，Root73154相同25真实PG门GREEN25pass0skip/23.008s；e7253单调期限+c812cb receipt身份/自有清理，独审0P0/P1/P2。manifest ya2ypnrz亲建DBabsent/sourcehashsame/Redis同；Project专属锁竞争/UNKNOWN COMMIT、publicDELETE/Storage dispatcher/linked-task规则仍未闭环。不得将同文件既有Move COMMIT门冒Project删除证明。
- 完整70组状态不因上述局部门改绿；完整Wave0–7目标不变，任务外Billing/uv保持。


## R183 后端删除赢家与前端验收收口
- Root49260对新test1d143f64真实canonical installer/build后运行 Project same-key 双backend竞争：1pass0skip，135.484ms（process437.676ms），日志/tmp/kokoro-r183-bff-project-winner-root.log；manifest project-winner-1xde1eh8亲建库absent/sourcehashsame/Rediskey同。完整facts第三重放不变与N+1成立；仅该case，不冒Project专属UNKNOWN COMMIT、Move/Delete/Message/Delete两序或public/Storage远端链已验。
- 原BFF单writer正在现chat-facts新增Project-specific真实COMMIT后断socketcase4，生产e7253不变；Root资源串行。新增case1 cleanup最初吞错已被Root拦截，1d143f64收全部清理错误及原业务error，并断assistant恰2，非放宽oracle。
- Web原writer七现locale共14真译文修复新增Move漏译：六locale从1503/1584低95%恢复1505/1584，ja也补新key；源/阈值/fallback/tests未改。worker27pass/lint/types0，只待Root27092全check；完整门尚运行不冒通过。独审32de9ff6区分既有缺译与本轮新增未译。
- 独立Web Move源码审/tmp/kokoro-r183-web-move-review.md：0P0/1P1/1P2。明确owner拒绝被AppFrame丢弃无可见反馈，global busy未禁非目标行的无效Move入口，故本轮Move用户旅程不可放行；unknown Retry实际已绑定目标行，不虚报扩散。原Web writer只读给真正Next/Chromium业务操作RED设计，Root门期间整Web冻结。
- Root当前拓扑verify-repository-topology exit0、doc diff-check0；不据此宣称业务全闭环。原IAB首屏P0未验，完整Wave0–7 goal active。


R183最终已有门实证：Root27092 Node22完整Web pnpm check自然exit0，contract258/architecture50/lint/types、默认164files2445pass0skip120.51s、Next build0；本轮七locale真译文修复95%失败，不是放宽门。独审Move仍0P0/1P1/2P2，第二P2明确普通Move Button错复用itemRename，<=960 translateY上移及collapsed可见性错配，真实overlap待布局证据。Web单writer现仅两个真Next用户菜单系统RED测试编写，生产冻结，不称用户Move已闭环或同步原运行。
Root80167对冻结a1d0dcfa/e7253 installer/build0，全部chat-facts27pass0skip22.758s；包含Project-specific真实双backendsamekey赢家与实际COMMIT成功后断socket/readWinner/release(true)/旧PID淘汰/新PID可query/同key恒定/newkey冲突。manifest /var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-r183-project-full-5vyhh8og/manifest.json，自库absent/sourcehashsame/Redis同，日志/tmp/kokoro-r183-bff-chat-full-root.log。后继Move×DELETE/Message×DELETE两序、全owner资源门/public/Storage执行/linkedtask仍开放。Root已保存前轮四台账commit c469fb73（仅Rootdocs，不含子仓/uv/Billing，未push）；本轮后续实际事实待合并台账。完整Wave0–7 active，原用户首屏P0未验收。


## R184 原工作区持续加载：真实浏览器旅程与原标签证据边界

- 基线：Root c469fb73；Web main9b42acbc的现运行副本、BFF main8e33bc0；原launcher45606/Web46036继续live，没有重启/清数据。Web源码与候选未写。原负责人只读报告 `/tmp/kokoro-r183-runtime-init-investigation.md`（d23d51ea）：未见Provider/effect/external-store确定性自激；persisted-store首次读取未catch、解析无大小上界是待验证风险，不能作为原页根因或借机盲改。
- Root使用一个独立Chromium和**当前3310真实IAM/BFF/System组合**，本地既有验收帐号正规表单CSRF submit303→固定tenant continuation→callback303→Product Session。非HTTP-only、非fixture认证、无新权限/模型调用/聊天发送；随后导航原conv_ffd7，2条历史可见、输入启用且实际接受草稿（随后清除未发送），真实reload后2条全文逐字一致，runtime-loader/booting-shell/frame-loader均false。证据 `/tmp/kokoro-r184-real-workspace.json`（2c3c1cbf）、截图 `/tmp/kokoro-r184-real-workspace.png`（d46418ca）。自有验收context/browser已关闭，不留后台窗口。
- 原IAB定向清单仍4个同URL标签，实际selected为tab2（不能沿用前轮tab1）。闭集DOM读取4s在command dispatch前超时；仅显示已有浏览器pane后再读取仍同结果。没有原DOM、刷新/关闭成功、原用户恢复证据；不以控制超时归因React，不用独立浏览器成功关闭T-U04。停止该轮控制重试，没有新增IAB标签。
- 实际当前组合还出现 `/api/session/billing/summary`503与`/api/session/agents`404；workspace仍渲染，故它们是独立业务失败而非已证loader因果。应沿现Billing/BFF任务排查，不虚称整体能力通过。
- 前轮Web系统Root71243 actual exit1：2fail/61名称过滤/81.93s，失败在fixture把Move按钮误定位为data-conversation-id选择按钮的后代，尚未发Move。另Case2漏先选A，不足验证active导航。不是业务RED；8353候选冻结，生产未授权，后继只修真实row scope与active前置，不放宽assertion/budget。用户加载优先。
- BFF原writerCase2仅现chat-facts追加真实Move-first/Delete-first advisory barrier＋blocking graph两个case，冻结79447abe（含COMMIT精确scope加强），syntax/lint/types/diff0，仅候选。独审与Root现真实PG全file串行运行，Message×DELETE/全owner/publicDELETE/远端Storage/linked-task仍开放。
- 验收：**原用户页面**会话正文、输入可用且刷新稳定，才能关闭T-U04。独立当前栈旅程只证明同帐号/同会话在独立Chromium可用；完整70组与Wave0–7不冒整体完成。

R184实际收尾：Root43518自然exit0，冻结79447abe/e7253 canonical installer/build0，全chat-facts29pass0skip23.375s，新增Move×DELETE两序真实图通过；manifest `/var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-r184-project-full-n8ayzyis/manifest.json` 自库absent、sourcehashsame、Rediskeys same。日志 `/tmp/kokoro-r184-bff-chat-full-root.log`。独审 `/tmp/kokoro-r184-bff-move-delete-review.md` 0P0/P1/1P2（完整deletion身份与B lifecycle/Share/Run精度待补），只接收当前局部证据，不冒全计划断言、public/Storage远端或全owner完成。原用户加载仍P0开放；uv.lock原f7e1与任务外Billing不暂存。


R191精确Web切片收据：3310351只提交导航孤立入口删除、死CSS选择器、5精准test迁移，保留原混合Move/CSS/test任务外差异；最终Root8271 Node22完整2469pass0skip/contract258/architecture50/lint/types/build0，真实原IABProject orphan0/明确新建1/Project scoped草稿/返回概览通过。不要把源码/单入口的GREEN升级T-C05完整Project CRUD或网站/Skills通过。
R191 Agent PG失败履历：63612 56pass3fail是能力缺失；94183 64pass2fail是非法evidence state/terminal fixture；14528 64pass2fail是UUID类型与LIKE参数oracle；51716 65pass1fail是owned锁图direct edge误当传递链。各次源hashsame/自库absent，后继明确修oracle/源P1不改schema/预算，最终门待收口，不删除失败记录。

R191 Agent最终Root门终态（候选未提交/未运行接线）：2138 scoped真PG66pass6.17s；86156全database277pass0skip31.21s，manifest T/kokoro-r191-agent-full-2h40hz61/manifest.json自库absent/sourcehashsame；48540完整工程自然exit0，lock/frozen-sync/ruff全仓/pyright/contract0，2175pass/375资源deselected109.20s，wheel/sdist build0。源model0898c86/repository87f06f6/test0b469f0冻结；只读最终审0P0/0P1/2P2，canonical同步篡改防御和新三transition完整authority/digest/回滚矩阵仍待补。没有runtime/provider/lostACK/Billing费用用户旅程完成声明。所有Root具名测试句柄已消费终态、没有遗留自有测试进程；原45606/46036保持。Source/必要D0同步及最终切片提交待后继，不夹带未完成P2冒零债务。


## R192 系统验收增量：同一会话的项目绑定与 Agent 授权边界

原70组统计不因本增量自动更新。owner PG验证、受管Next/Chromium＋owner HTTP fixture、原运行组合浏览器分别记录，不互相替代。

|用例 ID / 标题|预置条件|测试步骤|预期结果|优先级 / 类型|当前证据与状态|
|---|---|---|---|---|---|
|TC-R192-C01：移动仅改变绑定，返回来源不复活|本人Direct会话A已有消息，项目P可访问；正规登录|普通菜单将A移入P；在P核同ID/历史；返回Direct；硬刷新；回P|一次绑定写，Direct列表/主区无A，P有同一A；消息ID/正文不变，无新会话/模型调用|P0 / 主链路、状态机|Root80229真实Next/Chromium正确RED；34321正常五case GREEN，最终97aacfe完整88427含此case且2474通过。限定owner HTTP fixture；原3310未同步Move，导航/storage故障仍OPEN|
|TC-R192-C02：跨scope响应丢失保原操作身份|A→P请求可在owner提交后丢ACK|发起移动→切项目Q→回Direct→owner commit后断响应→显式恢复|不抢当前会话；仅原key/body恢复最终receipt或可证提交后的owner对账，无第二意图；绑定列表一致|P1 / 异常、竞态|当前同scope4项Root21887通过不覆盖此跨scope旅程；OPEN|
|TC-R192-C03：迟到ACK只失效列表，不抢导航|Direct A/B、项目P；移动A请求hold|发起A→P→切B→在owner提交前完成来源GET→释放确认|保持B及草稿，同时提交后权威列表对账最终Direct无A、P有A|P1 / 边界、状态机|现oracle仅不抢导航；完整后提交对账未验，OPEN|
|TC-R192-A01：授权观察非canonical腐坏拒绝|owned真实PG、合法Granted；stored bytes被改为空白格式并同步digest|从同一request_ref重放begin；读回attempt/Run|typed identity conflict；原字节/状态/时间/计数不变，不产生外发许可|P1 / 安全、异常|Root9303正确RED69/1→8134真PG70通过；最终71547全database281/0skip，865afb2已提交。不是provider/费用验证|
|TC-R192-A02：过期身份与超时零写、唯一外发许可|owned真实PG准备/待授权/已授权attempt，持有Run锁|错误lease/planned/ref负控；锁竞争与真实deadline；两连接dispatch后读Run|负控事务零写；恰一newly_started=true，另一false；同原timestamp；Run计数1/1/0/0且unknown，不猜零费用|P1 / 权限、异常、并发|最终真实PG281、当前默认2178/379资源deselected，865afb2已提交；矩阵仍selected非穷举，provider/E2E收费OPEN|

本切片退出条件：新增真实失败复现后修复、冻结source Root重跑资源与工程门、独审无未解决阻断、来源/目标与URL一致用户路径通过。跨scope两风险及原用户真实组合未验时，不把C01或局部绿色扩成全部Conversation CRUD、全部Agent或整项目通过。


|用例 ID / 标题|预置条件|测试步骤|预期结果|优先级 / 类型|当前证据与状态|
|---|---|---|---|---|---|
|TC-R192-C04：本地缓存失败不改变已知owner结果或阻断清理|A→P收到matching owner确认；来源本地存储/同步observer写失败|非active A确认后观察状态；active A确认后路由卸载，观察关闭流/取消/unsubscribe；禁止重发owner操作|两者owner结果仍confirmed；保B/草稿，不授权重复Move；dispose无抛出且完成清理。磁盘写阻断不得伪称持久成功|P1 / 异常、状态机|Root两负控真实RED2fail→最终97aacfe完整88427 GREEN。磁盘旧值hard reload及无dispose导航P2仍OPEN；此项内部故障注入，不冒真实原IAB storage异常通过|

R192终态：Root完整Web门2474通过/0skip，Agent完整真PG281通过/0skip；工程数量不换算成70组完成数。当前3310 Move尚未启用；跨scope/迟到对账/blocked disk刷新与收费路径未验项保留。


## R193 系统级验收增量：会话绑定与执行用量持久事实

会话产品规则：同一Conversation最多绑定一个Project（也可无项目），移动不复制Conversation/Message、不启动模型；来源列表与项目列表按同一owner事实读取。技术保护不新增用户授权页面或操作步骤。旧70组不因工程门数量增加自动改为通过。

|用例 ID / 标题|预置条件|测试步骤|预期结果|优先级 / 类型|实际结果与边界|
|---|---|---|---|---|---|
|TC-R193-C01：正式会话绑定接口接受移入/移出|正规Product Session、拥有会话/项目访问权；clean Web public7.1|经真实Next同源接口提交项目ID，再提交空归属；核请求与回执|只转发精确method/path/key/body；匹配会话及归属的回执返回；cookie不外泄|P0 / 主链路、权限|正式A提交21ad177；Node22完整2434pass包含3真实Next adapter用例；owner为HTTP fixture，不是真BFF用户移动，也非3310启用|
|TC-R193-C02：非法输入与坏回执不改变绑定|同上；可控owner坏响应|提交非空query/错误媒体类型，随后注入错ID/错归属/额外字段/不合法状态回执|非法本地输入零owner请求；坏回执fail-closed，不合成成功；非Move envelope规则不放宽|P1 / 边界、异常、安全|正式A真实Next R162/R164已随2434全门通过；跨scope unknown/late ACK的UI对账仍OPEN|
|TC-R193-A01：首次用量证据与投影原子写入|真实PG owned schema，合法Run lease/已dispatch Attempt|持久化完整sealed canonical证据；同事务后读Evidence、Attempt、Run|恰一Evidence，head/status/seal及Run五项一致；receipt不是外发许可|P1 / 主链路、状态机|Root31333最终scoped81pass8.19s；仅owner持久事实，不冒provider调用/扣费|
|TC-R193-A02：双真实连接重放与冲突|同上；第三连接持有owned Run锁|两独立repository同时提交同revision，观察两个PG PID阻塞图，释放；再提交同identity漂移字节|实际两连接串行；一新增/一原receipt重放，只有一行；漂移冲突零写|P1 / 并发、边界、异常|Root31333真实81pass；精确owned递归阻塞图，不以gather/时间推断竞争|
|TC-R193-A03：权限/期限失败零写|真实PG；错误lease/冻结digest/terminal或锁阻塞|逐项错误身份/已终态新写/总deadline负控；前后读Evidence/head/Run|稳定authority/conflict错误；事务回滚、零副作用，不猜费用为零|P1 / 权限、异常|先90325能力RED70/10；75279 terminal错误码79/1；ee9cbc窄修后97101 80pass，31333强化81pass；保留失败履历|
|TC-R193-A04：未知用量后继与terminal只读恢复|真实PG已有unknown rev1与其原时间、full bytes/digests|写合法normalized rev2核历史；另Run终态后重读已提交rev1，再提交新revision/漂移|合法连续后继保历史；终态exact返回原receipt且所有行/时间零写；新revision拒绝；不准再次外发|P1 / 状态机、生命周期|31333全快照正控及负控通过；后终态新用量reconciler、finalizer/Billing用户链仍OPEN|

退出标准：本片当前代码与冻结hash资源门通过、独立审查无未解P0/P1，才接收owner局部切片。前端B已抽取但跨scope结果丢失/迟到ACK来源对账仍P1，尚未提交或同步3310；因此会话CRUD/所有页面/完整费用旅程不称闭环。原用户浏览器本轮清单显示1个会话页，getTab控制超时未操作成功，不把工具超时归因产品或称原tab恢复。

R193 owner最终验收：Agent nine-path main2a9491e，81scoped/292full真实PG与2178默认/390资源deselected门均实跑，独审0P0P1/1P2；WebA21ad177 clean2434/3trueNext/build0。上述通过不关闭UI B的crossscope/lateACK P1、原3310Move及完整聊天费用业务；70组不自动涨数。

## R194 T-C04/T-C05 同scope Move 系统验收

复用原70组，不新增完成组；真实Next/Chromium＋严格HTTP owner fixture只证明Web交互，非原3310/真实BFF数据库链。冻结system771964、source a3321/860536。Root97553 1pass/3fail→62663 4pass/0fail（69选择外未运行），27.29s。R188-002历史“迟ACK不刷新”oracle由本轮纠正：不导航抢B但必须后提交GET，原失败与历史结果不删除。

|用例ID/标题|预置条件|测试步骤|预期结果|优先级|类型|执行状态/证据|
|---|---|---|---|---|---|---|
|TC-UI-R194-001 / 迟matching ACK与新active保全|正规Product session、Direct A/B、真实Next/Chromium、held Move响应|A移动P→切B输入草稿→记GET数→owner commit/release ACK→观察新GET/列表/URL/draft|ACK后新Direct GET仅B；A来源消失；B URL/草稿/焦点不被旧projection抢回，单POST|P1|主链、异步竞态、状态机|真实RED→GREEN；Root62663，非跨scope|
|TC-UI-R194-002 / 已提交但socket关闭|同一scope，fixture先commit A→P再close响应|发Move→socket close→仅A显式Retry→比较第一次/第二次path/key/body→读取目标message|保原command，仅显式一次恢复，同Conversation ID/message history，不重建/复制，不发Run/model|P0|异常恢复、幂等、生命周期|Root97553与62663均PASS；same-scope，不冒新engine恢复|
|TC-UI-R194-003 / typed503未知结果|正式typed business_store_unavailable503，原A可访问|A Move→503→菜单Retry→恢复matching ACK→比较wire|503不证明未commit；unknown可见，原key/body恢复，无mount/focus自动重发|P0|异常、状态机、边界|真实RED→GREEN，Root62663|
|TC-UI-R194-004 / 幂等处理中|正式409 idempotency_in_progress|A Move→409→显式Retry→matching ACK|处理中不是终局拒绝；原key/body保留，single-flight且不抢其它active|P0|异常、幂等、状态机|真实RED→GREEN，Root62663|
|TC-UI-R194-005 / 跨scope与身份清理|同subject两个Project；真实page engine生命周期；owner迟ACK/unknown可控|发Move→导航另scope→释放迟ACK/503→显式恢复→anonymous/subject变化/logout/pagehide；再次检查请求和所有列表|旧engine资源释放；原command跨scope仅人工恢复；双scope新GET、不抢页面；换身份零旧command重发，无持久绑定副本|P1|权限、安全、生命周期、异步竞态|OPEN/NOT_RUN；same-engine注入邻测不能替代；Web owner后继W2|

Agent A3b新增四真PG case先执行25837：fixture assembly_recipe_bytes为None使4fail/126选择外未运行，1.21s；canonical catalog10检查通过，自库absent/sourcehashsame。此结果不是finalizer缺能力的业务RED，writer修fixture后须Root重跑，终态封存/真实收费仍未验收。

R194完整门8560补记：system73例72pass/1fail；整体164files2479pass/1fail，175.43s；失败为既有R192用户链（Move→Direct返回/刷新→再打开Project）在新snapshot GET断言3==3，不是本轮四例被skip。build未跑。该交互仍FAIL/待根因，不按一次历史GREEN认定全Move通过；Root同冻结重复及独立只读根因调查继续。
Agent fixture修正后21678实际6例4业务fail/2owned finalizer expiry/cancel正控pass，126选择外4.19s；数据回收/hashsame。A3b源码限现三文件实施中，provider/Billing链未验。

R194错误oracle修正（不是删/弱化用例）：Project engine mount已经新GET，旧测试到route后才取baseline，点击已active A合法no-op，Root63137重复同错。前移baseline到Project navigation前且严格核原tuple，system222a6b；Root57706 R192＋四R194共5pass/0fail、68选择外28.99s，业务source不变。全门继续重跑，W2与真实3310未通过仍保持OPEN。

R194完整Web收尾6435：contract258/architecture50/lint/types/build全部通过；164files2480pass/0fail/0skip161.43s。现mixed源码证据，不等于clean B+C或原3310；W2P1与原70业务统计未升级。Agent原sixcase86131 6pass4.02s后独审新发现sealed metadata投影不一致与authorization_denied误拒两个P1，必须追加真实PG正反控，不以sixcase全绿宣称穷尽或收费闭环。

|用例 ID / 标题|预置条件|测试步骤|预期结果|优先级 / 类型|当前证据与状态|
|---|---|---|---|---|---|
|TC-R194-A04：终态严格证据与数据库投影一致|真实PG owned schema、已sealed合法unknown证据|分别改SQL revision/head、call_id、合法usage/outcome投影而保canonical bytes；提交终态，读回model/public全快照|每项typed冲突；全事务回滚，无新Evidence/终态消息/费用推断|P1 / 安全、异常、状态机|Root88885三负控实际失败，缺完整projection校验，未验收|
|TC-R194-A05：合法拒绝授权的sealed终态与重放|真实PG、canonical denied授权、not_dispatched sealed head|首次finalize后精确重放；核原event/bytes/完整快照|合法状态通过；原Evidence仅一份，重放不写新证据或变化预算|P1 / 主链路、状态机|Root88885实际误拒失败；原six case仍6pass，源保持冻结待窄修|

|TC-R194-A06：授权SQL state与canonical bytes一致|真实PG、合法denied sealed head|只把SQL state/status改为CHECK允许的requested_unknown/not_dispatched，保denied bytes/digest，提交终态|typed冲突及model/public全事务回滚，不把拒绝授权误报为未请求|P1 / 权限、安全、异常|Root72070真实DID NOT RAISE，5fail/6pass；test76d1冻结，窄GREEN待Root复验|

R194-A04/A05/A06同strict业务断言真正RED→GREEN：Root35202共11truePG pass6.62s；仅test类型narrowing后Root3648全database303pass39.33s/sourcehashsame。局部用例通过，整体A3b仍被explicit resource闭包工程失败阻断，provider/收费/用户路径未验。Conversation same-scope 5旅程已随clean B+C2463完整门通过并窄提交a75345f，当前3310未启用与W2跨scopeP1保持，不增加原70组完成数。

工程门补充：Run terminal import所需strict证据代码必须在既有runtime resource闭包里且生成descriptor可读；Root62052纠正测试路径后44pass3.07s/build0。首完整默认工程2177/1原缺闭包失败保留，当前5resource新manifest后的完整门待复验，不能以44局部通过关闭Agent用户链。

## R195 跨页面绑定与内部终态验收

|用例 ID / 标题|预置条件|测试步骤|预期结果|优先级 / 类型|实际结果 / 状态|
|---|---|---|---|---|---|
|TC-R195-W01：跨项目切页后的移动确认|真实Next/Chromium，Direct会话A，Project A/B，owner持有Move响应|移动A→Project A；响应前进入Project B并输入草稿；释放matching ACK；返回Direct、打开Project A|B路由/草稿不抢；Direct无A、Project A有同ID及原消息；source/target重新读取唯一绑定|P1 / 主链路、状态机、竞态|53415真实RED：Direct仍有1条A；当前失败|
|TC-R195-W02：跨页后提交成功但丢ACK|相同环境，owner提交后关闭连接|发Move后进入B；返回Direct的A；显式重试原command|切页/挂载/聚焦不自动POST；保原key完整body；人工retry恰一次，最终同ID绑定一致|P1 / 异常、幂等、状态机|53415真实RED：原行无Retry菜单10s；当前失败|
|TC-R195-W03：跨页后typed503未知结果|相同环境，明确typed unavailable响应|发Move→B；返回A并人工retry；核POST次数和body|未知不当拒绝、无自动重发；保原key/body；用户可以恢复，不复制Conversation|P1 / 异常、容错、生命周期|53415真实RED：原行无Retry菜单10s；当前失败|
|TC-R195-A01：终态与全部调用证据原子封存|真实PostgreSQL独立自有schema及既有Run authority|四open状态/已sealed/denied各终态及exact replay；合法SQL投影/授权bytes腐坏负控；锁等待取消/过期；读取全事务快照|开放调用保守seal；unknown不猜零；canonical/SQL不一致全回滚；合法denied通过；精确重放零写|P1 / 主链路、异常、安全、状态机|54838全PG303/0skip39.35s及此前11case GREEN；限定内部owner已验，8c08ea4；真实provider/Billing/user费用链未验|

W01首轮65252在B GET尚未完成前立即断言是测试oracle问题，与真正业务RED分开。原writer只收紧B实际GET等待，不提高10s预算/睡眠/放宽绑定断言；53415随后实际失败在Direct残留。原R192/R194系统用例字节保护。工程2178/303计数不提升70组业务完成数。

## R196 当前复验（不改变70组整体统计）

|用例 ID / 标题|预置条件|业务步骤|预期结果|优先级 / 类型|实际结果与下一门|
|---|---|---|---|---|---|
|TC-R196-W01 跨scope matching ACK|Web候选真实Next/Chromium、Direct A、项目A/B、持有owner响应|A移动到项目A→去B输入草稿→释放ACK→回Direct→项目A→B|B草稿/路由不抢；source无A/target同ID消息；返回B完成canonical读|P1 / 主链路、状态机|Root75557 source/target与草稿阶段已过；最终B GET裸断言1!=2，独审认为等待次序缺口，保exact计数并用原10s poll，尚未关闭|
|TC-R196-W02 丢ACK跨页人工retry|同环境，owner commit后连接丢失|A移动→B→到已归属A项目行→点击原command Retry|不自动POST，同key/body单次retry；显式打开该会话，URL包含原conversation|P1 / 异常、幂等|Root75557 retry已显示且同key重发，路径到A但query null；源缺口原writer修复中|
|TC-R196-W03 typed503跨页人工retry|同环境，owner typed unavailable|A移动→B→Direct原会话行→人工retry|matching ACK后定位目标项目与原会话，旧pending ACK不抢其他draft|P1 / 异常、生命周期|Root75557仍/app，源缺口原writer修复中|
|TC-R196-A01 模型失败不隐式重复调用|当前Agent锁定SDK+自有loopback HTTP peer，无真实模型或积分|五构造分别500/429/断连，实际计完整请求；200/流式正控；取消及调用者timeout清理|每次执行最多1物理请求；错误传播、成功stream不损，资源结束|P1 / 异常、生命周期|Root87413真实RED五故障每例3请求；factory仅五处retry0后Root94390 14pass1.15s，限定SDK协议sandbox；整体provider/费用用户路径未验|

独审c641a1补充三P1尚未关闭：pending Move后同scope New Chat迟ACK抢导航；BFCache第二pagehide不revoke；scopeVersions无界/主体切换未reset。需各行为RED→最小源fix→Root复验，不以已有14/84/103数量冲销缺口。

R196最新复验93393：TC-R196-W03已在本候选真实Next/strict BFF fixture完整通过，尚非3310 live owner验收；W01加原10s网络poll后暴露返回B三GETvs预期二，源失败继续OPEN；W02准确URL/query后原Message未显示，继续OPEN。独审新增三导航/生命周期P1静态已修，真实浏览器专项未新增关闭。TC-R196-A01由814e929六路径提交，完整工程2178通过及独审0P0/P1，未关闭真实模型/收费测试组，70统计不升。

R196 Root42824最后真实Next三case全部3pass24.49s（19路径冻结hash）；TC-W01/W02/W03在strict BFF fixture级当前候选均通过，including source/targetcanonical tuple、返回B只一次GET、exactretry后的原Message和URL。完整门15820待验，formalclean release/live owner未启用，因此不升级70整体组或原3310状态。

R196完整回归15820：新增三旅程通过，但既有R188‘未知Move切到B后重试A仍保B’失败，整体Web未放行；需retry遵守当前显式selection，仅无canonical selection/当前命令会话才随绑定导航，不抢B。2475pass/1fail、build未执行，原案例不弱化，下一四trueNext＋完整门。

R196最终正式切片：Webce40cecc基于clean候选17paths完整2459pass0skip125.05s，contract/architecture/lint/types/build0；独审0P0/P1/P2，包含旧R188显式B选择保护和三R195system业务旅程。此是formalcommit+真实Next/strict owner fixture，不是原3310 live BFF/真实费用；TC-W01/02/03到候选层已验，70组11/6/14/38/1仍不改变，live复验另明确任务卡。


### R197 绑定能力发布验收准备（不提升70组业务通过数）

- 既有T-C05.R187会话Move用户链仍待复测：正式ce40源码、Rootf750双pin、clean release build/source预检已通过，旧3310仍public7.0无Move。须在实际运行版本正规登录并建立/保留真实Conversation/Message基线后测Direct→Project→Direct、source/target列表、刷新、同key未知恢复及不抢其它选择；预构建不算通过。
- 新发现发布状态生命周期：旧launcher退出清理run自有IAM/应用库，再启用新subject/secret；用户是否保留当前测试数据待确认，禁止擅自shutdown。当前不要求用旧cookie验证新run保持登录；不同run不假称同Conversation保留。
- Root新release构建5owner0、Agent初offline缓存miss后正规frozen网络安装/真实模块src origin0；receipt8a76f2c9。仅装配通过，不证明登录/模型/Billing。
- Agent native无Billing许可零provider请求系统baseline已Root真实失败（见下表），未授GREEN，不列通过。

|用例 ID/标题|预置条件|测试步骤|预期结果|优先级|类型|实际结果|
|---|---|---|---|---|---|---|
|TC-R197-A01 / native调用在费用授权缺席时不外发|Agent814e＋唯一未提交test6760；Root自有fresh PG，现正式factory/SDK，Billing consumer未装配；System/模型协议loopback sandbox|正规enqueue/claim Run Lease→factory封存recipe→原生DeepAgents stream→计完整provider请求→查询attempt/evidence→清理fixture|无owner许可零模型外发，不能生成成功/免费授权；有界安全失败与资源回收；dispatch/evidence不得凭猜测补零|P1|安全、主链路、异常、生命周期|FAIL：Root37791真实1物理请求!=0、1fail/45warnings1.71s；其后两SQL断言未执行，恢复错误终态未验。自有库absent/sourcehashsame；manifest原址见CURRENT。不是正式Billing/外部模型/用户费用验收，未授生产GREEN|

70组11通过/6失败/14待复测/38未验/1支付后置保持：上表是原模型/费用组的明确失败子例，不重计新增组。TC-R195-W01–03/TC-R196-W01–03原RED行保留为历史；最终ce40限定fixture四旅程/clean2459门已通过，但对应3310 live组仍待验，不能混写全绿。


### R198 系统级准入/归属验收增量（不新增70组计数）

|用例 ID/标题|预置条件|测试步骤|预期结果|优先级|类型/分类|实际结果与未验|
|---|---|---|---|---|---|---|
|TC-R198-A01 / 主调用缺费用准入时安全终止|Agent59034f4（已验17path；前置8a3169bd）；自fresh PG与正式native SDK；Billingconsumer缺席；System/provider仅loopback协议，非付费模型|enqueue/claim→冻结recipe→factory native stream→正式invoke_once/terminal事务→记录物理provider请求并读取Run/Attempt/Evidence/outbox→关闭handle与自库|provider0；attempt1 prepared/not_requested后ND sealed；run.failed dependency_unavailable nonretryable；Evidence unresolved/missing_usage/actual unknown不造零费用；无残留自有资源|P1|安全/异常/状态机|Root81548 RED1fail→54105 GREEN1pass1.58s，canonical10 CHECK0、自库absent/sourcehashsame；仅main负例。其它caller/recovery、实际Billing/provider与原浏览器未验|
|TC-R198-B01 / Admission归属闭集边界|Billing364f4ba，experimental.2机器schema与owner generated产物；非运行HTTP入口|合法user/project/organization/service＋255ref；依次缺subject/kind/ref、未知kind、空/256ref、嵌套未知payer与body payer字段|四kind合法；required/closed/长度边界拒绝；billing_subject仅归属，不授权caller自报payer/金额|P1|边界/安全/契约|真实Ajv RED合法请求拒绝→final clean verify1117pass/411资源skip及generated0；限定contract片独审0。IAMtoken验证、真实AdmissionHTTP/余额/事务不因此通过|
|TC-R198-A02 / 实际子调用与恢复不绕过准入|同正式native工厂；GP/catalog/Swarm合法cycle、多入边与checkpoint恢复；无Billing许可|实际启动各子节点；重复恢复相同checkpoint；检查独立peer-path/稳定call与attempt、物理请求数、terminal/evidence、取消与资源回收|每个调用先owner prepare；无许可均provider0；同节点恢复无重复identity/外发，合法图不误拒；取消有权威终态|P1|主链/异常/状态机|待执行：当前仅recipe/path静态装配与main负例；不拿mock/unit/独审替代native系统路径|
|TC-R198-C01 / 会话只有项目绑定关系|实际已启用Webce40/BFF8e33的同一用户运行组合；存在Direct会话与原消息及项目|Direct→项目→Direct；两列表切换、刷新、返回；lostACK同key重试时选择其它会话|同Conversation ID/原Message不复制；project_ref唯一权威，列表无幽灵/重复；不抢用户其它选择、不永久loading|P1|主链/交互/异常/状态机|候选四真实Next旅程已验；旧3310仍旧consumer，无本轮原页执行。runtime切换的数据保留待答，当前不能关闭live组|

完整门退出要求不变：当前版本真实用户路径、各owner实际依赖与异常/权限/生命周期通过，P0/P1清零；局部负例或schemaGREEN不等于全研发闭环。

R198-A01最终绑定Agent59034f4：Root50248全真PG304pass/0skip（含该main负例）、默认2182pass/416资源deselected及所有工程/build门0；候选源SHA不变，后四D0contract/build0。A02实际子调用/恢复和C01原3310绑定仍待执行，B01只是contract；总70组统计不改变。


## R199 实际系统/构建准入回归（2026-10-04）

|用例ID/标题|预置条件|步骤|预期结果|优先级/类型|实际结果与范围|
|---|---|---|---|---|---|
|TC-R199-A01 / prepare真实锁等待取消|正式Agent59034＋唯一41fe系统case；自有fresh PG/正式Run lease/recipe/SDK/checkpointer，Billing缺席|正式started→显式transaction锁Run→initial=False；observer确认prepareSQL/PID锁图→本地task.cancel→await→释放blocker→全Run/Attempt/Evidence/outbox/checkpoint比较|CancelledError原样，无finalizer/物理provider/新attempt/取消后的checkpoint；本地cancel不是持久用户终态|P1 / 异常、竞态、状态机|**FAIL**：Root98757锁/取消观察成立但完整prepared/not_requested attempt后写；305其他database通过不能关闭本case。此前17166是autocommit fixtureTimeout，94202仅中间freeze，均留痕。不接受sleep/放宽oracle/删除审计|
|TC-R199-A02 / terminal公开Supervisor重复恢复|同正式main failclosed已terminal，先publicserve发布旧outbox后取权威bytes基线|publicSupervisor.serve重复同RunRequest/bus；核ACK及DB/checkpoint、System/provider计数|sameidentity、provider0、DB/checkpoint字节零差量；不build或读native；可ACK旧消息但不新增durable seq|P1 / 主链、幂等、生命周期|Root98757当前case PASS；系统bus是测试传输，PG/checkpointer真实。仅terminalSupervisor replay，不是Redis、SDKmodelnode retry、GP/catalog/Swarm、lostACK或费用链|
|TC-R199-B01 / portableIAM owner artifact准入|Billing26aeec6 cleanconsumer，IAM0537正规0.7.0pack、Node24/Corepack11|frozenoffline install→根IamClientimport→正常完整verify/generated；真实修改archive/provenance/nested未知/primary缺失或错pin/四组alias/第二tgz后逐执行architecture门再恢复|合法1通过；全部10错误自然拒绝，完整bytes恢复，禁止sibling/tmp/workspace/双包；owner身份/contract/digest/许可完整|P1 / 架构、供应链、边界、异常|Root36987正式1122pass/411资源skip、generated0、十负控全部拒绝，源hashsame；两先前P1漏报和semver治理FAIL已真实复验修，不冒业务线上IAM/余额/Admission/扣费。manifest CURRENT同路径|

70业务组整体统计保持11/6/14/38/1；这些细分case证据附入原owner任务，不新增完成百分比。真实取消缺陷保持P1开放；会话绑定候选与原3310运行旅程分开，只有当前浏览器完整路径可关闭live项。


## R200 需求覆盖核对（非业务测试完成）

现PRD的FR-01–19映射原全部70唯一组，Root展开检查70/70、missing[]/extra[]；完整主链/边界/异常/权限/状态机的执行结果仍在本台账，不能将PRD覆盖或审查换算为产品通过。当前11通过/6失败/14复测/38未验/1支付后置保持。

Root文档门第一轮真实发现handbook README两历史子仓链接失效（AssertionError），不是用户业务故障；改为现BFF API/Billing README后，最终205本地链接0失效、diffcheck0，证据/tmp/kokoro-r200-prd-root-verification.json。系统源码/原3310浏览器/真实账务本轮未执行，不冒修复。

T-C05项目删除按用户“参考ChatGPT”批准语义收敛：项目会话/指令/仅项目文件删除，单独Library文件保留，删除需明确确认不可恢复；2026-10-04核验官方https://help.openai.com/en/articles/10169521-projects-in-chatgpt。独立ScheduledTask关联政策仍待裁决，C05/P05不关闭。T-B07 actual-only/unknown保持ADR033，不以旧失败全释放收口。


### R201 IAM授权前置证据（不提升系统用例状态）

IAM0537真实billing authorization HTTP16pass/0fail，Root49764，manifest `T/kokoro-r201-iam-billing-alsk5tbv/manifest.json`；own DB/Redis清理、source不变。Billing production adapter/Admission/预占/Agent dispatch/evidence/实际结算尚未组合，T-B03–B07保持原状态；cancel late prepare仍RED。70组11/6/14/38/1不变，局部owner16不是16组用户旅程通过。


### R201 系统授权前置增量（不提升完整70组）

|用例ID|标题|预置条件|测试步骤|预期结果|优先级|类型|实际结果与边界|
|---|---|---|---|---|---|---|---|
|TC-BILL-R201-001|正规IAM授权与归因绑定|真实IAM billing fixture、Code+PKCE消费token、tenant machine、compiled Billing adapter|分别user/project/organization/service授权；换tenant/user；撤销本人membership后重用token|合法归因均绑定真实payer；错绑定与撤权拒绝，单次物理验证，无secret输出|P0|系统主链、权限、生命周期|Root94978相应7例通过；非实际积分/账本，通过不关闭T-B04/B06/B07|
|TC-BILL-R201-002|授权异常有界收口|同上；Root owned网络故障代理|503、stall至期限、caller取消、module shutdown|无自动重试；闭集UNAVAILABLE/ABORTED/SHUTTING_DOWN，无挂起，资源恢复|P0|异常、取消、状态机|Root94978相应4例通过；总11/11、每例physical_requests=1，host_exit0/resources_restoredtrue；仅adapter|
|TC-IAM-R201-003|测试host退出与资源生命周期|真实IAM owned fixture；共享PG/Redis仅观察|ready stop/EOF/SIGTERM、startup stop/SIGTERM|不提前exit泄漏自有库；cleanup后自然结束；共享inventory不变|P1|系统异常、资源生命周期|首次ready-stop真失败保留；Root74712修后五例PASS，test-only不冒正式登录通过|
|TC-AGENT-R201-004|实际native取消版本对照|正式PG/DeepAgents native链、原41fe oracle、独立固定候选SDKenv|等待prepare真实锁→取消invoke并等返回→释放锁→完整快照核对|取消后的model operation有限停止，无晚prepare写|P0|系统取消、数据一致性|1.2.12仍真实FAIL（2pass/1fail）；原锁tracer三例PASS但prepare仍pending，仅诊断调度变化。生产未改，本用例不关闭|

### R209累计SQL真实系统RED

TC-BFF-R209-004（P0，事务/异常/资源生命周期）：Root46499真实HTTP+PG，owned tenant两BEFORE INSERT trigger各3s，outbox和user-message两个PgSleep同backend成立；期望503且HTTP<4900ms、双窗口全facts零差、backend销毁、同pool后续健康请求。91e95测试实际FAIL/case6.101s：HTTP期限assert false/true且生产未消费Connection terminated拒绝。manifest T/kokoro-r209-bff-absolute-red-ebyrdmgy/manifest.json ownDBabsent/source/Redis同。该真实失败后授GREEN，新test将加强PID彻底消失及pool计数回baseline，未执行不得冒GREEN；完整组状态不变。

R209新候选后继Root10139已自然exit1：最终事务3e2209c7/测试f7ebafdf，两真实HTTP/PG case为1pass1fail，累计case11.114s，generic waitFor Error被Aggregate包裹；不能猜失败在backend销毁或poolbaseline。manifest T/kokoro-r209-bff-absolute-green-yjzg1y8_/manifest.json 自库absent/source/Redis同。本次未记录旧unhandledRejection，但不能据此宣布全缺口关闭。原writer仅补安全phase/HTTP elapsed/pool数字观测，源码冻结不重复盲修；新独审0P0/1P1/1P2，未派发COMMIT的过期被内部误标unknown及双marker负载敏感性待继续。Root暂无活动测试句柄，不重启原3310、不更新混合gitlinks。


R209 Root37507 phase复验自然exit1：1pass/1fail，累计HTTP4504.97ms，两个owned PgSleep同backend成立；503/header/no-store、响应及backend消失后的完整facts零差、健康202/恰两Message一dispatch均已执行。最终失败明确在pool-baseline：起始total8/idle1/waiting0，终态total9/idle9/waiting0；起始仍有7个占用，须追实际启动调用链，不能凭这些数字宣布泄漏或盲改源码。manifest `/var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-r209-bff-absolute-green-pr0a58gp/manifest.json` 自有DB absent/source/Redis/secondary库集合保持。Source3e2209/testa457冻结，原BFF负责人只读查baseline；页面审查员独立更新逐页库存，不接管写入。无新运行资源或当前3310升级，70组仍11通过/6失败/14待复测/38未验/1支付后置。


R210真实系统复验：Root1383 exit0，source3e2209/test301fe387两HTTP/PG用例2pass/0fail/0skip7.678s；累计SQL用例完整503/HTTP<4900ms/全facts两窗口零差/ownedPID消失/后续202与静止pool精确相等。manifest `/var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-r209-bff-absolute-green-g3cse5ra/manifest.json` 自有DB absent、source/Redis/secondary库保持；独审测试补丁0P0/P1/P2。原基线是遗漏两个任务外4并发worker的瞬时checkout，修正显式idle与真实只读HTTP暖机，不放宽任何产品oracle。COMMIT未dispatch仍误标unknown的生产P1、pool late/中段故障/COMMIT ACK/四scope矩阵及完整owner门继续OPEN；不关闭70组或当前3310。


## R210 当前已取得证据与后继（2026-10-04）

上一goal轮归类为进展：Root37507定位pool-baseline并提交112d3a7e。本轮修正fixture任务外worker隔离/真实HTTP暖机，不放宽oracle；Root1383两实际HTTP/PG case2pass/0fail/0skip。具名事务COMMIT派发身份P1已窄修，独审最终0P0/P1/P2；首完整27496仍7个旧测试fixture/放置失败，全部如实保留。原writer只维护三现邻门，未改生产为容忍double。

最终Root1737对冻结BFF候选8f04afa9/resource301fe387和三邻门执行完整门：**177真实PG/Redis通过、0fail/0skip、47.018s；743默认通过/1既定资源skip；236contract通过；lint/typecheck/check/format/schema/build0**。manifest `/var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-r210-bff-full-tgpff8ke/manifest.json` 自有DB absent、source/Redis/secondary库保持。候选仅在既有clean archive，原BFF main8e33及22mixed未改变/集成；必要pool迟到、中段rollback/断链、真实COMMIT ACK、四scope/notify临界矩阵仍OPEN，不以既有177代替未覆盖行为。当前3310未升级/未重新浏览器验收。

System已由Root精确四D0提交 **032ff52419fe651c76b115e9fe20aafbba2ef051**，最终独审0P0/P1/P2。Root86018 Node24.20.0现2.0契约12pass/83business+2probe/19source provenance且所有非docs tracked bytes保持；目标3.0执行界仍未实现。当前可信resolve执行上限字段仍0。批准现model-catalog revision/resolve发布technical context与output硬界，不含Billing价格/账户/费率，canonical published非NULL检查、immutable/digest/generation同事务与正规生成/pin已设计。仅设计门通过，不是model收费链。

两个独立后继原生owner继续并行：**R211-BFF-POOL-RED** 只新增真实HTTP池饱和/late acquire用例，必须经过现Message前置findConversation，不绕过授权；**R211-SYSTEM-EXECUTION-RED** 只在现integration/contract新增publish缺界与目标3.0断言，先正确实际业务RED再源码。Root独占资源/审查/Git；未启动新常驻服务或重置共享PG/Redis。原45606/46036/45926/45942仍live；uv SHA f7e1保持。当前topology真实FAIL四项Agent/IAM/System/Billing gitlink差，未更新指针假装组合发布。

完整Wave0–7与既有70组保持：**11通过/6失败/14待复测/38未验/1支付后置**。正式模型dispatch、Agent owner reads/execution-bound、Billing授权赠送/余额/预占/核实结算/释放/流水、项目CRUD/独立任务/工具审批/Skills/MCP/Library/Settings以及真实用户旅程继续未闭环。

## R232 本轮最新验收补记（2026-10-04）

- Root26514 Web完整80pass/0fail/0skip，118.785秒；固定test569540dc，source_same、Redis keyset保持。前一完整79/1失败留存，仅修R195原10秒的完整canonical URL等待；生产不变。系统fixture为真实Next/Chromium/Redis、IAM/BFF controlled peers，不是用户3310或真实后端能力闭环。
- Web manifest `/var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-r232-web-final-pg9ku5_g/manifest.json`，log SHA256 `437fa8ca1461737699d728a86dc918c9816349b17e014c777b9448fa4bbb6b59`。两项目会话DELETE覆盖ACK前保留、成功后权威GET/刷新、503与显式重试，不等于项目DELETE合同已发布。
- Root69377 Agent完整310pass/0fail，5.39秒、8SDK弃用/畸形值警告，source_hashes_equal=true；固定observer77f5df7f/factory4cd6e1b1/inventorye2fd087b/peere13f0853。此前无完成marker两真实RED Green。锁定SDK与自有HTTP，原179+新增131；未访问共享DB/Redis/provider/资金，也没更新用户3310。
- Agent manifest `/var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-r232-agent-full-b_prfjxk/manifest.json`；源码独审 agent_usage_r232_review 完成0P0/P1/P2，报告 /tmp/r232-agent-usage-source-review.md（SHA256 f5c701b1ca46bf293cde0ce5ea27b23d61d08beb00ddc1385e3de69b09286adc），工程/installed后继待验；不提前提交或宣称正式收费证据完成。
- 系统70组保持11通过/6失败/14待复测/38未验/1支付后置；当前HEAD/工作树与用户旧运行组合分开，历史Settings异常不冒本轮重新复现。

## R233 最新源码/系统实际结果（2026-10-04）

Web新缓存拒绝系统反例Root50904真实1fail/80filtered：认证成功、拒绝2、SecurityError，正文/输入0；read最小捕获后Root37212原case1pass/80filtered（7.863秒），再Root45144完整81pass/0fail/0skip（120.255秒），原12秒预算/旧80/认证全storage拒绝负控保持。冻结source16136175/teste2f5afe9，source与Redis keyset保持，独审0P0/P1/P2。manifest /var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-r233-web-full-eeam4wb3/manifest.json，log05862492346d8832926bcf4d1a59628521667269419f6d644473adc853e9ad56。源码是非权威local cache初始化修复；原3310原因仍未知，不冒用户恢复。主仓Web20mixed包含旧19，未整体提交；Root10121完整工程已终态exit1：258contract/50architecture/lint/typecheck通过，默认2478pass/3fail（IAM邀请页桌面/移动端/注册三项5000ms超时），build未执行；T-Q01从历史通过改为当前失败，根因待诊断，不放宽期限。

Agent架构cast真实FAIL经单文件_JSONObject runtime hook窄修，Root12295九工程步骤0（29architecture/310真实SDKHTTP/默认2253pass717filtered795warnings），source保持；build36640 wheel/sdist0；installed33857 v3 pass（18step含两应拒绝负控、安装origin/RECORD/新observer/factory/assembly精确hash），自有venv删除。源码b8bc3c81等四路径独审0；四D0证据回填在途，Root随后精确八路径提交，不夹带其他内容。正式native/Billing/sealedEvidence与用户3310未闭环。

70组业务状态仍11通过/6失败/14待复测/38未验/1支付后置。资源测试数量不当产品完成数。

## R233 当前进度复核补记

本轮消费原10121，不重复启动。Web完整工程真实失败，T-Q01已更新；70组当前为10通过/7失败/14待复测/38未验/1支付后置，下面或前文11/6仅此前时点。隔离系统81项与Agent工程/安装是限定证据，用户3310旧运行组合仍未验收；三原生子代理均完成交接，不冒称正在后台运行。

## R234 当前真实交付与并行诊断（2026-10-04）

Agent Root精确8路径本地main提交cb64537048d34ce6db5bea5f2e12e182ba88092c，parent f3050fcc，Git objects逐项等冻结，工作树clean；四当前D0独审0。Root本轮29architecture/310真实SDK HTTP/contract全0，manifest /var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-r234-agent-engineering-db5xcdvu/manifest.json；重新archive构建wheel/sdist0，manifest /var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-r234-agent-build-c6_5i21z/manifest.json。新wheel逐zip entry bytes与R233 installed18step已验wheel全同，包含RECORD，不能用zip打包时间导致的文件hash不同冒新源码；原完整2253/717marker过滤/795warnings证据绑定四核心SHA不变。receipt /tmp/r234-agent-commit-receipt.json。未push、更新Root组合指针或用户3310；native/Billing仍OPEN。

Web原三浏览器超时单文件原5000ms实跑4pass（1.936s），同源完整只设CLI maxWorkers4为2481pass/0fail（126.463s），后者manifest /var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-r234-web-four-workers-3t2tm2gg/manifest.json，source/Redis保持。原默认2478/3真实FAIL留存；没有证实卡在Chromium哪一阶段或原3310根因。按最小资源预算裁决原writer只把现config固化maxWorkers4（2586c52d），维持文件并行和原全部断言/deadline；Root46156原pnpm check完整门仍在途，未先改T-Q01通过。Web当前21mixed，旧20保护。独立配置审查和BFF项目改名三D0/契约方案只读并行。

IAB原/app只读getTab在15秒工具deadline超时并kernel reset，没有取得用户DOM；未刷新、新tab或重启服务，不把工具失败当应用根因。当前70组10通过/7失败/14待复测/38未验/1支付后置保持。

## R234 最终工程终态与本地交付

Root46156已终态exit0：完整原pnpm check的258contract/50architecture/lint/types/165file2481pass/0fail/Next build全通过，161.421秒。manifest /var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-r234-web-engineering-q7b13zmn/manifest.json，日志SHA1af68e9c606893f477b2d95b690f5e00790585297c9546327676543068bfb9b0，source/config/Redis keyset保持；新4-worker预算独审0，并未延长原5000ms、重试或过滤测试。Root只提交clean config路径为main680c8db8c7c118d083bc64ba7362dff6f62fcecf，其他20mixed bytes/mode/status全保持；收据/tmp/r234-web-worker-budget-commit-receipt.json。工程绿只绑定当前冻结混合树，不能冒Git-only组合发布或原3310修复。R233默认2478/3历史留存。

T-Q01有限工程组复测通过，70组当前11通过/6失败/14待复测/38未验/1支付后置；之前10/7是本轮复测前时点。Root组合实际变为6个gitlink差异，未更新指针/uv或push/重启3310。Agent cb645370本地已交付并clean。Root治理归属小门7pass，仅该范围，旧全仓标准/组合checkpoint问题保留。所有本轮测试句柄均终态，无未登记验证任务。

BFF改名设计只读报告/tmp/r234-bff-project-rename-d0-review.md已回读：选择字段PATCH /v1/projects/{projectId}/name，保instruction路径/ID/slug，name与现receipt同事务、旧key不覆盖新名、LWW不新增version/表；三D0及active前置交付必须先审，尚未写合同/源码或验证业务。正式登录/原页面持续加载、CRUD/设置、native与Billing用户费用链仍OPEN。

## R238 项目资格 fresh catalog 反例（不改变70整组统计）

|用例ID/标题|预置条件|步骤|预期结果|优先级|类型|实际结果与范围|
|---|---|---|---|---|---|---|
|TC-BFF-R238-ACTIVE-SCHEMA / Project删除资格数据前置|HEAD7289b3a4 clean artifact，正规canonical installer、owned真实PG临时库；冻结新增schema test810a|安装空owner schema→限定Project catalog读字段及全部索引→检查合法创建默认null→finally回收自有库|deleted_at nullable timestamptz(3)/无default；原owner_list exact partial IS NULL，既有PK/slug索引不变|P0|系统、数据、边界|Root真实1fail/0skip：字段查询[]，尚未执行后续索引/default断言。完整数据库集合保持；已准schema两hunk但未GREEN，不冒HTTP资格/项目删除/当前页面闭环。manifest见progress R238。|

Web认证/恢复三D0已审并明确R177替代旧watchdog；仅tests-first准入，当前没有本片系统实跑通过。原T-U04/原用户加载保持失败；70组11/6/14/38/1不变。

R238复测补记：TC-BFF-R238-ACTIVE-SCHEMA RootGREEN1/0及完整schema12/0/0skip已通过（限定前置）；HTTP/PG八顶层业务组仍失败，TAP35为含父/子统计，非35独立缺陷。墓碑可见/Message与Move非法接纳/inner与锁竞态有效RED，六部分负控先停header缺失，为另HTTP transport P1。Web五例中四ReferenceError不计业务RED，R186 held snapshot12秒无error为有效反例；helper修复待重跑。70整组11/6/14/38/1不变。


## R238 完整回归终态补记（不改变70业务组状态）

- Web原73例完整系统回归：67通过、6失败、0跳过。失败覆盖冷启动/刷新、focus认证更新、主题/语言偏好拒绝、挂起与503认证探针恢复；根因尚未分别确认，保持失败，不以五个目标用例通过代替完整门。真实Next/Chromium/Redis、IAM/BFF controlled peers，不是用户3310或正式模型费用链。manifest `/var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-r238-web-auth-full-wv094_yg/manifest.json`。
- BFF格式修正后完整工程check与format均通过，743通过/2资源跳过；最新格式版本完整真实集成尚待执行。已有schema12与8业务组35父子统计通过仍按原范围记录，不冒完整项目删除/CRUD验收。manifest `/var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-r238-bff-pure-final-zvbgljcd/manifest.json`。
- 70整组仍11通过/6失败/14待复测/38未验/1支付后置；当前用户加载、逐页CRUD、Settings与正式积分链仍OPEN。


## R239 认证状态机与BFF资格切片复验（业务70组不变）

- Web最新完整原73系统例全部通过/0fail/0skip，含旧六回归及最终强化的checking→unavailable卸载→显式Retry→authenticated状态、零私有IO/零误登录、主题/语言降级、冷启动刷新、有界snapshot。真实Next/Chromium/Redis、controlled IAM/BFF，非用户3310/正式费用整链；原67/6及安全oracle1/1失败按阶段保留，不删。最终manifest见progress R239；候选工程仍待终态，T-U04仍失败。
- BFF最新完整217真实PG/Redis通过/0skip，schema12通过，工程0；精确14路径已本地提交main cdad0ad6，保护20mixed。只关闭active资格前置切片，不关闭项目改名/完整删除、T-C05或当前用户页面/费用组。
- 70组保持11通过/6失败/14待复测/38未验/1支付后置，组件测试数量不换算功能完整度。
