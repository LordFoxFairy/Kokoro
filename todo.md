# Kokoro · 当前执行 TODO

更新：2026-11-13。唯一执行清单；Task B接管基线Root `1092d99b`（当前候选沿原#67），不重开已交付Task A，不重复扫描凑问题。

## 当前任务：Task B 正式接管（2026-11-12）

### 当前最短收口队列（2026-11-13）

1. **资源恢复与原命令**：共享Docker `_ping` 于23:54 UTC仍4秒超时，等待单项重启确认；保原卷，恢复后鲜验Storage数据路径，只续Skills restore和Project install原body/key。
2. **组合旅程**：资源恢复后只补共享Run→安全FINAL/Artifact/peer过程缺失旅程，不重跑已验模型、取消、权限矩阵。
3. **确认与交付**：本轮三项已登记QA（Custom API治理、Provider目录、MCP重授权占位）的不可逆动作待合并清理确认（原来“两项”漏计MCP；并非新增数据）；六个owner原PR均已main：IAM#9/71ad4ed5、Agent#49/49901fd7、Capability#12/448a8804、Admin#7/cf71291a、BFF#17/c43457ba、App#49/f7ccd733；仅Root#67仍OPEN，待组合/清理收据后交付。当前相关十个owner仓OPEN均0。远端各自topic已清；本地App旧feat/mcp-api-management因既有rail-test-scope worktree占用保留（bf8已合/clean），不碰未交接工作区，其余本轮local topic已清。

本轮确定代码差额已收口：Admin33bf2f0恢复页/菜单多语言，B02分层规则及当前IAM两条真实撤权。MCP QA是example.com占位HTTP地址，未Prepare/启用、不当新产品故障；真实外部端点/授权、完整云E2B和真实支付关闭沿已接受边界暂存。Provider状态/receipt不冒专用审计，原交接未单列长期Provider审计平台，不为此新扩建。



用户已把 Task B 移交本主控，历史“Task B 不动”仅约束当时 Task A／UI 批次，不再排除本任务。沿[原功能交接](docs/handoffs/2026-10-30-task-b-capabilities-account.md)和[既有有效计划](docs/superpowers/plans/2026-09-03-kokoro-production-closure.md)推进，不重开已交付 Task A、不另起任务中心。以下是接管后的真实剩余队列，不把原15个功能域当15个新故障。

- [x] B-T0 接管：确认原 Root #67、App #49、BFF #17、Capability #12 及当前 main；主控保原PR历史、全部12个已验 main gitlink和正常运行源，不盲激活旧组合。Root原分支已合入当前main；原468行Task B记录保留。
- [x] B-T1／R-07（writer api_perf_audit；主控验收，独审 app_merge_gate）：Capability contract check 改为只读；显式generate仍能写。临时生成后完整集合／字节比较，覆盖漂移与异常回收；不改 wire、Schema、生成器算法或正常服务。已沿原Capability #12提交推送 `c040dda8`；主控8 PASS／真实contract check、类型／相关lint／格式通过，803个输入SHA／mtime／mode不变，四实现测试输入冻结核等。本片源码及后继候选组合已验收待PR合并，不冒整PR／Task B验收或merge。
- [x] B-T1a（已合Agent main／Capability原PR待收尾，api_perf_audit验证／主控集成）：Agent `281bde49` 顶层provenance及3处常量／断言精确配对Capability `573a8f00`，四Proto／生成物及独立历史pin不变。正规generator／Ruff／Pyright／wheel安装smoke通过，主控正常Python3.14.3四contract文件129 PASS／contract-check，四SHA核等。先52 Run均终态／pending0再SIGTERM三个相关进程，正式HTTP／Worker／Platform已恢复，health／ready200、Worker消费；原数据和两笔未知财务记录保持。Agent原需求PR #48已正常合main `b7867212`，merge树等已验281bde49，自有local／remote topic已清；4条CI红因账户账单／额度未启动，未绕保护。后继Root `db28020c` 固定Agent main与App34c51204，inventory按131真实提交blobs重算150引用，拓扑／15边0违例／原checkpoint通过，未放宽门禁。managed隔离工具未返回，实际验证使用ignored源码archive fixture，正常应用由主控受控完成。
- [x] B-T2／R-14（源码及候选组合已验待PR合并，api_perf_audit实现／app_merge_gate独审／主控验收）：OAuth DNS pin 限定一次有界操作，保同操作DNS漂移拒绝、实际IP连接／Host／SNI／取消，不清共享Map冒修复；现设计／factory装配已完成，沿原#12提交推送 `573a8f00`；writer相关63例、主控两直接文件17例／完整types／scope lint-format通过，五输入冻结核等、独审CLEAR。HTTPS仅socket替身、取消保真实loopback；未跑真实Provider／PG／全默认。本项源码收口，不冒实际授权／整个PR完成。
- [x] B-T3（首片已验，完整原PR仍待后继范围收口；composer_ui_audit实现／app_merge_gate独审／主控验收）：App原#49保留双方历史并合入main，候选 `a0512901` 已提交推送；机器契约保现28.35及22个正规生成检查。主控完整lint／非增量TS／build通过；rail首轮290 PASS/5 FAIL，按当前行为修正后295 PASS。完整默认实测6753 PASS/2 FAIL，两处旧oracle修正后原两文件48 PASS；未重跑全默认，不拼成全绿。主控native-auth实测API创建201→fresh exact详情→刷新恢复、JSON两项import201→显式选择B→fresh connector/server详情→取消未保存编辑→刷新原值，均通过；未执行Connect／Prepare，秘密未回显。用户已确认删除3项登记测试配置，真实三DELETE200＋硬刷新仅剩原Context7，不动原配置。Root `ae480fb9` 精确配对App，真实blob inventory／拓扑／15边0违例／原checkpoint通过。BFF原#17后继已保历史收口609并正常激活，细节见B-T3b；不激活旧29.3。
- [x] B-T3a／B-14 本片（composer_ui_audit实现、api_perf_audit独审CLEAR／主控验收）：bootstrap隐藏未读模型误报；MCP详情／管理／配置／JSON接现t及本片九语言，不改框架／契约／认证。App `8208882d` 主控四文件443 PASS／build，正常English详情→JSON非法反馈零MCP写、取消回焦与390px内收通过；真实French320又复现默认词条中文回退／English占位，后继 `34c51204` 只修10个现有key及原测试，主控117 PASS／build／8输入核等、独审CLEAR。最终正常French320空白MCP表单真实标题／保存／icon提示均已本地化，宽288／scrollWidth288，无创建提交；恢复en／视口。本片不冒全站翻译或九语言全视觉QA，Custom API与目录其它旧占位随B-02/B-14统一承接；后继浏览器network缓冲发生eviction，不将留存零写冒完整network证据。
- [x] B-T3b（BFF/App当前源码消费与normal子旅程已验；供应商末端交B-01、整PR仍待）：主控联合候选 `0a2c98ae` 已提交推送，Share GET／现IAM既有delete_series枚举／MCP显式重新授权同片337相关例、完整build/types/lint、216semantic、两正规check通过，114输入冻结、独审CLEAR。真实ChatModule/Nest＋隔离PG7 PASS／0 SKIP，准入显式double、无Redis；URL漏owner schema与deleted seed漏deleted_at两次失败保留，仅修接线/fixture，不改生产约束，三个自有测试库均已DROP。新private profile旧Bearer改真实native；初始Session期间断连/0预算真实4 FAIL→4 PASS，退役后manage/owner0，已发Session仍原timeout边界保留。原#17已普通保历史集成到 `609b0e93` 并快进推送，源树核等0a2；82冲突及无冲突混入按具名语义组处置，移除重复旧测试/退役层/未发行旧pins，不复活RSS旁路或旧8.11 context；B08当时待核；本轮后继已按当前8.17实装并完成native，见上方B-08。App已固定blob0a2正规消费Public28.37和new private profile，提交推送 `ebc36617`；主控23生成检查／60文件1216 PASS／build，独审后3缺口修正再验6文件185 PASS／types／SDK check／build，110输入冻结核等、独审CLEAR。Share不确定命令在同主体tenant恢复时保原key、坏provider ACK拒绝、Shared SDK必需path.id均已承接；正常BFF609b0e93／Appebc36617已受控激活，health与页面200、原生会话刷新恢复。真实Share打开仅GET200/零POST；MCP自建空配置Disconnect→显式reauthorize200→不同新connector pending/disabled/version1→exact Connector/Server GET200→硬刷新保持未连接，零自动Prepare/OAuth，原Context7不动。整PR仍Draft，未冒供应商末端或完整Task B完成。
- [x] B-T4／Storage #2（已合main并清本轮分支）：真实PG核对否证原fresh1d60→0f480假设，已撤回未提交兼容分支；生产工具／canonical不改。现仅修历史FINAL工具/helper/993aede目标Schema的测试冻结、当前workspace_output枚举oracle与测试URL GUC隔离；原业务行／no-op／ArtifactsStore断言保留。主控真实6 PASS、格式／ESLint／types／独审CLEAR，两SHA核等；3个注册probe库及fixture自有库均回收、正常DB未改。`47bf19d` 两文件修复已提交，普通保原add2历史集成 `31a7c89`，完整树等已验47bf19d；原#2正常合main `7155093c`，树等已验源；本轮local／remote topic已清，其他dirty工作树不动。远端CI因账户账单／额度未启动，未绕保护，不带未获实证的旧兼容配对。
- [ ] B-01当前控制面/末端：当前消费者/正常源已配对，显式Disconnect→新身份→鲜读→刷新已验；只补具体QA/端点的Prepare与外部授权未就绪末端，不新造配置或重跑模型。Prepare ready本身会active/enabled，不把它当只读/承诺enabled保持false；本轮Chrome已鲜读确认QA是HTTP＋example.com/task-b-reauthorization/mcp，无query/userinfo；仅编辑视图读取后Cancel，未Prepare/Save/Enable/OAuth，不再等待占位目标成功。原Context7不动；新增QA待原单项删除确认。缺授权外部末端/完整云E2B沿已接受边界暂存。
- [x] B-02冲突/撤权/迟到规则分层收口／主控核原件、shared_project_run_display_audit只读：573真实PG4已证Describe/Acquire同名env冲突、跨主体/tenant、旧版本/删除缺失和解密后rotation/delete、晚准入/取消清bytes；当前efe verifier/binding/environment/test四路径逐字承接。当前治理真实PG6的35输入SHA核等、正常数据不改且库回收，承接Q/restore/revoke两runtime gate/CAS/回滚。主控当前IAM main71原正式HTTP文件只筛permission撤权/成员移除两case：真实PG/Redis2 PASS、10筛除、526输入起终exact、数据库库存无新增/缺失。原Docker成功/取消及材料边界证据复用；不冒本轮正常CustomAPI+IAM+Docker联合撤权/完整E2B或任意编码DLP，也不再为该组合重复模型。旧“4次verify”原件未定位，另8次历史原件明确不当当前冻结证明。
- [ ] B-03～B-05（composer_ui_audit只读已核）：ZIP/GitHub导入、安装启停／下载／移除重装、v1→v2→撤回→历史恢复新UID/v3→系列删除及作者/同团队负控既有计划记载真实收据且已核源码祖先在当前（旧原件本次未重定位，不据此整体提升验收）；11-12真实Skill→MCP→Docker→FINAL也已验，不重跑模型。剩余只补广场／Settings／Project三入口exact身份与读历史一致性、后台／管理员撤权与跨tenant边界。AI创作／录制当前为fresh Composer prompt-starter，不冒实际录制/自动产包成功，不因旧待领取状态重造Skill框架。 现Root3389/Appbf8正常浏览器新增：Settings安装/作者当前版本历史/广场source_ref、revision1、包目录及正文完全核等；只读RPC非生命周期写，原Settings pin保持。当次无Project、作者仅v1是历史阶段；现原QA Project已存在，主控已从我的技能看到同source/revision候选。实际安装POST503/unknown，原body/key私有保存、未第二次安装；fresh native列表200/0项、selection200/空只是当前观察，不冒原写ACK。源码确定安装本身先verifyPackage→Storage GetPackageReference，故包依赖恢复后只继续原命令，不新发布版本/包/项目。
- [x] B-02材料边界补验（api_perf_audit聚焦核验／主控执行）：Capability573当前真实PG4 PASS（执行准入double、自有随机库回收）；Agentb786 Python3.14.3客户端／执行环境／秘密产物出口＋真Factory接缝107 PASS（sandbox/model doubles），BFF609当前独立checkout单文件7 PASS。复用既有Docker成功／取消／刷新；未跑云E2B或重复模型。只读核验未发现具体Acquire明文新出口，不制造每载体重复测试；不冒任意编码/外网的通用DLP、全存量日志扫描或真实IAM撤权。
- [x] B-08当前已批准手工个性化/知识范围（已验待原PR完整交付）：BFF代码143/文档abbfd78，App代码c044/文档bf8ef938；无新owner/协议/表/认证/记忆服务。原事务可信actor同snapshot冻结、原key零重读/regen原快照、1MiB/取消及闭集生成主控68/真实PG5/现Agent21、两独审通过；知识启停/删除/跨主体/失败风险按这些最低层级承接，不每组合重复模型。**Root21e833c4精确组合native已验**：真实UI onBlur保存临时偏好→新消息本身不含标记→正常配置模型一次调用实际按偏好回复→AI SDK展示→硬刷新同一条回复恢复。BFF私有context与Agent request_json完全相等、owner核等、userMessage/trace不复制原材料，双Message/Run终态、financial ACK存在；原四空字段经正常UI恢复revision2，原两未知财务记录保持。最终DocOnly owner后继与此代码无差，冻结组合317真实blobs/383引用重算，拓扑/15边0违例/原checkpointPASS。公开产品一页/导航/9语hint、47/types/门户build+62页20513链接/App build均验；自动长期记忆/外部导入未开放如实说明，不新增该扩展，不冒全TaskB完成。
- [ ] B-09／B-10／B-11／B-12原差额：旧计划具体记录及源码祖先已核，旧E目录原件本次未定位，不整体关闭。B09邀请/接受/主动leave旧原件已核销，角色/移除/重邀重发撤销当前native补缺已通过（见独立子项），不再等待缺失旧E原件；B10 Chat/Skill已有计划实证与现metadata读；用户11-13委托主控自行裁决Project ACL，现选同团队viewer/editor共享明确项目资料/聊天/任务安全结果，个人内容/Secrets/Connection/资金不继承。BFF三设计已写目标态，独审指出的ScheduledTask委托P1歧义已在三设计修正；BFF源码及具名演进已发行，正常激活/双身份ACL主片见下方B10；共享Run/FINAL与后台剩余部分不冒完成；B11/B12既有B08 Run精确模型/冻结报价/结算/账本已在下方只读补证，**当前活动政策已只读补证（见下），对应后台完整管理及其它原缺口仍待**。不重跑模型、不强释旧unknown。B06/B07当前差额已补验；真实支付关闭，不新增内部OAuth/认证层。
- [x] B-11/B-12已存在B08 Run绑定/结算补读（主控只读、composer_ui_audit核schema）：不新调用模型、不变更资金，只对同一已验Run分owner只读查询。唯一dispatch/attempt/admission，可信actor/payer、call/ordinal/三摘要、精确模型revision/digest及冻结报价完全配对；actual=verified，最新evidence/ACK绑定核等，ACK/admission/hold=captured，usage/settlement=settled；真实usage debit金额与capture、allocation和capture/release守恒核等。首摘要UUID类型比较误报已纠正并保留，不是生产缺陷。只证明该Run，不冒今天活动政策/所有旧unknown/全部后台已完成。
- [x] B-11/B-12当前活动政策只读补证：Billing正式选择语义（DB时钟，先tenant整revision、effective_from<=now，再按effective/revision倒序，最后过滤精确模型）；只读repeatable-read实查活动rate v3/policy v2，与latest一致/非未来，rate行数与header一致、profile配对、已验模型exact revision/digest仍覆盖且币种与policy一致。只证明该时点/该模型，不冒新执行、后台publish或全部模型可计价；无报价/资金写或历史快照重算。
- [x] B-06当前会话管理缺失接线与实测（主控配置/正常native，app_merge_gate定位）：仅补normal IAM/BFF既有account_sessions专用路径，独立随机profile/固定正常tenant，原配置私有备份；源码/协议/Schema不改。原503复现后，两端受控重启healthz200，真实浏览器列表200→只撤本轮自建独立Session DELETE200→fresh列表200目标消失，原当前/原另一Session保持；被撤Session auth=false且业务GET401。另一新QA Session仅fixture缩短expires_at至8秒，正式GET先true/真实expiry一致→墙钟经过后false/业务401，无先logout/全局TTL改变；不是七天浸泡或浏览器自动倒计时实测。两测试Session均正式logout/自有Cookie回收，53Run终态/pending0、旧两财务记录保持，不新跑模型/全默认。
- [x] B-07缺失双标签CAS主旅程（主控正常native，Root3389/Appbf8/BFF9cc，无源码变化）：两页同revision2，A PUT expected2→200，B PUT expected2→409且草稿保留；显式Reload→展示权威A→Use server profile→硬刷新仍A；按新revision3 PUT恢复原四空字段→200，原标签硬刷新核空；另新原生Session正式CSRF表单重登GET200/revision4全空，随后仅退出新Session/删除自有Cookie。原工作Session保持，无模型/工具/知识开关写。三个写阶段网络证据完整；首A读取collector未捕获、旧response body后被evict如实保留，A outgoing expected2及B初始GET2证明基线，不冒全程trace完整。只是本缺失旅程，不等于B06自然到期/独立设备或全TaskB完成。
- [x] B-14 Skills语言本片（composer_ui_audit实现／api_perf_audit独审／主控验收）：en两现key补齐、两日期调用显式locale，其他八语言不改。主控5输入冻结41 PASS／types／build；正常英文桌面＋320px文本内收/日期正确、无横溢/长标签自然换行。原#49代码844fbbcb＋文档0c6078e3已推，正常App同源激活，不重跑全默认/九语截图矩阵。
- [ ] B-13后台（主控验收；原Admin #7/e7f2f79）：成员目录读取/本页筛选/中英UTC、390px标题换行、撤权403清空及重新核对已验；原正常临时角色恢复false/v6，测试Session清理，原工作会话保持。模型/标签与计价写后回读的缺失旅程本轮已补，详见下一子项。剩余只按原具名范围：Skills管理员审核→用户可见性、Provider/MCP/API管理、用户/团队邀请角色及对应owner审计，以及本轮确定的草稿发布UX修复；不扩任意User360/退款/统一跨owner日志平台。PR继续Draft，整后台未宣称闭环。原第六次ENOSPC失败/人工回收记录留CURRENT与原计划，本轮第七次已自动回收，不再将旧磁盘预算列作现阻塞。
  - [x] B13 Custom API owner 生产切片已交付：Capability `efe18a1f` 推原 #12，主控真实PG状态/CAS/并发/审计回滚/精确父演进通过、自有库回收；60路径冻结核等、HTTP/契约及owner最终门通过。该条为 owner 源码阶段；正常演进及成对激活现已完成，治理 native 当前证据见下；不将条件跳过当通过。
  - [ ] B13 消费与native验收：BFF个人治理74117ac/专用RPC d875e3bd后继完整38d47c9已正式发布六公共Admin HTTP，Public29/227及33source和最终240 focused/102历史contract通过；App个人治理ebf97674已验。Admin页面153c875已发布并完成主控源码门，App六同源桥与协作源f32b707a已发布并通过工程门；三个旧writer额度终止后由主控接管、两只读agent复核（见B10队列）；正常新组合已激活，完整后台native仍待。
  - 最新实测：Root58215eca精确六owner第七run，r1空bounds发布409保留；r2显式8192/1024草稿201/发布200、label201→两次CAS200别名修改恢复、rate/policy各201、硬刷新/正式GET/原body-key replay通过，五表资金/Run均0。原driver恰1revision oracle FAIL保留、cleanup PASS；主控独立补充实录verifier PASS，不冒原driver或全部B13绿。正常数据/报价不变，无模型/Provider执行。前文ENOSPC与预算为第六次历史；当前容量恢复，未新复制源码/依赖。
  - [x] 同一草稿修正源码与缺失native已收口：BFF原#17/396897b8（Public28.38/217），主控真实Nest/loopback owner与契约190 PASS；原整contract1400/2旧oracle失败保留、两原oracle准确修正后不重跑全套。Admin原#7/df7883d固定46ops、退役旧唯一vendor，原草稿PATCH/CAS/unknown/onPrepared退休/取消/不rebase接通，最终全363/0skip、全lint/types/contract/build/post-types和独审通过。App原#49/c1444ee0桥接，主控56/build通过。三仓已推原PR，normal App/Admin/BFF按原配置恢复。Root精确组合拓扑/15边0违例/原checkpoint PASS，未合main/部署。
  - [x] 主控真实native收据 `9634eda90cfe493517b5394b`／Root`89de6a62`：唯一definition201、r1空bounds201；缺限额Publish仅本页反馈/零请求；同ID仅PATCH8192/1024、CAS1→200/version2；显式publish CAS2→200/version3；硬刷新详情同ID/digest/限额，Published且无编辑操作。原PATCH重放保持原version2回执，鲜读仍published3；owner读回/七Billing资金/计价表与BFF dispatch均0/正式logout/cleanup/credential-log-check均PASS。前两次安装请求超时及字体编译FAIL保留，均cleanup PASS，不拼旧证据；无模型/Provider执行或价格/资金写。
  - [x] B14随片两组件/Ant默认双语：Admin原#7/87c228c，60自定义key zh/en，现Shell单一ConfigProvider随locale选择官方语言；主控全367/0skip、全lint/build/posttypes与九SHA独审通过，保护原业务，非整个后台文案/视觉完成。source-only native driver四ignored文件已纯检查/四SHA主控核等；静态不冒native成功；实际English表单/确认/Ant默认文案随上项native已验；zh仍为原renderer证据，不冒全后台本地化。

- [x] B14 Models展示源码片（原Admin #7/`79b14599`）：六现源码/两现测试补108 zh/en key，页头/说明/四tabs/表单/详情关闭/分页与状态提示接原LocaleProvider；用户/协议/技术字段与原始诊断不翻，未改生命周期/请求/CAS/journal。主控8输入核等、七文件46 PASS、非增量types/scopedlint、真实Turbopack build/posttypes与独审通过。正常Admin同配置恢复；本片浏览器/窄屏对照未新增，随后继真实后台旅程补，不冒全B14闭环。

- [ ] B-14／B-15：视觉／多语言／性能与文档、原PR、精确组合随每片关闭。PERF-02已收口（见下）；模型目录取消已随PERF-03收口，icon404已核为可选媒体缺省回退，见下；不为非缺陷新增代码。侧栏有限切片已沿App原#49提交推送00334cbe：32既有key/九语言、15实现测试输入冻结，主控160 focused/相关lint/完整非增量TS/正常production build、独审CLEAR；真实French项目标题与空态正确并恢复English。此次实际1000px，未冒新390通过；旧15-key阶段窄屏单列。无locale框架/导航资格/协议扩展，不冒全站翻译闭环。manifest caller取navigator而非设置locale另记事实，影响待定向核验，不冒System内容错误。

- [x] B-09本人leave缺口（主控真实native／Root`5097b9b0`／run`497bcd810c3f33b82fe06ce8`）：仅IAM40c/BFF396/Appc144。owner正式invite200→recipient邀请原生登录/CSRF接受→Product登录/本人Member→原生独立observer鲜读有效且业务200→UI Confirm leave DELETE200 exact member_id/status:left→自动退出/浏览器团队GET401→owner重新登录鲜读目标消失且owner保留。另一同ID未过期observer Session仍真实native200，但原业务资格403 product_tenant_forbidden；不以401代替撤权。strict真实副本tsconfig通过，owner读回/dispatch0/正式退出/cleanup/凭据日志PASS，不改生产认证/正常tenant，无模型/资金。此片只补当前缺口，旧roles/分页/移除/重发撤销记录及原件边界仍分列，不冒全B09/Task B完成。

- [x] B13 旧全局Approvals伪入口退役（pricing_fixture_review实现／models_ui_review独审／主控验收）：Admin `44ec4e9f` 已推原#7；无owner接口的旧页/菜单/overview卡/nav词条删除，不造审批队列或alias。主控相关21 PASS、ESLint、正式Next build/后置非增量types通过，旧同源页面/API均404；native Hub16项、原技能详情/治理控件可用，无旧侧栏入口。原生成路由类型失败留存，正式build刷新后通过；不等于整个B13完成。

- [x] B15 认证元数据旧账纠偏（models_ui_review只读／主控验收）：BFF28.38/217、Admin同SHA/46消费、App28.37/216逐操作静态核等，普通业务native、skill.list独立Key例外；主控现BFF已有contract102 PASS、App已有消费断言1 PASS。不新增认证代码/契约版本/pin更新；整个B15文档与交付仍随其它片推进。
- [x] B13 Skills早拒绝网关修复：BFF `c40315b9` 原#17已推/正常激活，两native wrapper各提前设现request-id；主控65 focused/非增量types/正式build及独审通过。正常无管理资格由旧502恢复403 skill_forbidden、UUID响应ID/JSON/no-store完整；Admin服务端自产新ID，首个外部ID回显断言错误保留并按现adapter规则纠正，不放宽生产校验。
- [x] B14 Admin Models显示补验：既有79b源片补正常native en/zh目录/修订/详情关闭及390px中文空表单取消；page/main均390无横溢，原技术键/用户名保持，未新增模型或扣费。截图留ignored，恢复en/默认视口；不冒全后台翻译。
- [x] B14 文档语言唯一writer（sidebar_i18n_finish实现／models_ui_review独审／主控验收）：App58ba5ecf已推原#49，删除Runtime Manifest覆盖html.lang的effect，现LocaleProvider唯一维护；原manifest请求locale/scope/取消/期限不改。真实迟到en-GB受控RED→31 PASS，主控31/types/scopedlint/正式App build、六输入SHA核等；正常native French/fr→硬刷新保持→原English/en恢复。不冒正常System支持en-GB或已解决metadata请求语言映射。
- [x] B15 前阶段公开API门户（28.38，后继 Public29 见下）：App58ba5ecf消费已发布BFF396897b8/Public28.38原blob，App业务client保持28.37；修正首页过时Bearer警告及明确Secure/plain互斥cookie，补模型草稿条件PATCH参考。主控门户lint/provenance/55 tests/正式build/确定性reference211 public operations/architecture/62页20603links通过；初始路径、旧pin相对当前checkout、旧空白及缺Secure例失败留存，未删断言。
- [ ] B10 真实Project协作（主控验收；正常组合已激活，双身份ACL主片已验）：BFF核心135路径已正式推原#17 `38d47c9`（Public29/227、Agent8.18正式消费）；主控停写SHA核等、focused240/0skip、历史contract102/0skip、generator/build及独审通过。buffered read实际RR资格降权P1已修，前一229/11夹具失败保留并修后完整focused重跑；阶段真实PG原件与各自回收保持，不冒当前整链完成。
  - [x] BFF已知源码与完整默认收口／主控（非正常激活或native收口）：精确父演进`690a787`已提交，主控真实PG保值/拒绝未知混态/矛盾回滚/noop通过、输入SHA保持且自有库回收；正常库未演进。pins/Skills源码片`fbc2025`已沿原#17提交推送（见下）；本人RunDisplay后继`5cb7b13`及输入/聚合后继`6b1d8a4`均已验推原#17；原六处已知源码接线已齐，该阶段正常库未演进/新源未激活，现由下方正常切换收据覆盖。Public29稳定；不新owner/认证层。
  - [x] BFF pins／Skills源码片／主控实施、shared_project_pin_skills_review独审CLEAR：`fbc2025c`推原#17，个人pins复用read资格、只改本人偏好、锁后鲜验grant；Skills GET/包/spec/exact download走read，安装四写走edit且body解析后RPC前重验，真实actor不变，无Schema/协议增量。主控focused183、Nest/DI74、真实PG2均0失败/0跳过；build/lint/types/12路径format通过，自有PG库DROP+absence。PG先1/1、接线2失败、半包竞态及DI两轮失败原件保留，不冒全默认或native。shared_project_run_display_audit已只读给最小后继方案，主控接着实施，正常资源未激活。
  - [x] BFF本人RunDisplay源码片／主控实施、shared_project_run_display_audit独审CLEAR：`5cb7b13d`推原#17，readable lookup与Project edit gate同时接入，exact actual Run actor不变；RR内FINAL binder核current/edit并绑dispatch.subject=actor=caller，不借creator。原verified spool/Agent后发头前鲜验保留；peer/viewer/迟到降权零私人内容。主控相关三文件123 PASS/0skip、creator→editor→creator真实PG完整片1 PASS/0skip、build/lint/types/7路径format通过，c25e4c3a库已DROP+absence、SHA保持；新HTTP404和PG editor final=null的RED保留。selected FINAL函数未改，无协议/Schema/认证增量；native仍待。
  - [x] BFF输入／聚合及control源码片／主控，selected/aggregate/control三独审CLEAR：`6b1d8a4`推原#17（20路径）。同Project当前read选peer确认FINAL/Artifact、保真实来源且目标锁内edit；regen原key replay不被fresh latest/active预读误拦。owner聚合删除全creator canonical成员及owner-bound legacy，补已deleted producer fence，data creator/cleanup actor分开，peer admitted/unknown不冒取消，N+1所有ACK齐才released。新cancel/resume需edit，原actor安全ACK仍先重放。主控最终11相关完整文件163/0skip、真实PG/Nest输入11和聚合1均0fail/0skip，16源码测试+8dist SHA保持；build/lint/types/format通过，自有DB均DROP+absence。先完整默认2556 PASS/21 FAIL/2条件SKIP保留，失败组修复后134定向及163相关通过；后继最终冻结完整默认2578 PASS/0 FAIL/2条件SKIP，24输入SHA保持；两条件跳过不冒全integration通过。两个真实逻辑RED（replay/新cancel）及临时ACK早拒RED保留；无Schema/public合同增量，正常组合/native未验。
  - [x] 最终默认／只读切换预检／主控：BFF源码6b1d8a4上正式完整默认2578 PASS/0 FAIL/2条件SKIP，2580总项、24源码测试/compiled输入核等；不是native/全部integration。`38e8e7a`仅CURRENT收据后继，生产树等已验6b。正常BFF53 terminal、取消/到期派发空、enabled Tasks0/consumer lease0；Agent53 terminal/lease0，历史claimed53全部对应terminal Run、event outbox全published；四核心listener各1，已实查受管worker活着。仅记录read-only snapshot，不清状态、不停服务；切换前必须再核quiet/进程身份。后台专用候选配置和App/Admin候选输出按既有清单成对激活，Docker共享VM待答独立保留。
  - [x] App源码工程片／主控接管：`f32b707a`已推原#49，正式Public29、真实Grant/角色、原snapshot→AI SDK单轨终态、原CAS Scheduled写入与六具名Admin桥已接。143paths受控，最终142输入SHA保持，完整默认6865/0skip、lint/正式checks/Next build/posttypes通过；首6771/94FAIL及修复历史保留。旧URL复制测试/纯自比常量断言退休，原sealed父SHA不改；不是native或整个B10完成。
  - [ ] Admin／主控：`153c875`已推原#7，原Hub Custom API tab、52项正式消费、列表/详情/删除后审计、Q/restore/revoke与原命令恢复源码已验。主控修正错误status/code组合终局误判；focused10/默认380零skip、lint/types/contract/生产build/posttypes通过。原normal编译输出恢复，真实浏览器/owner组合及剩余B13仍待，不冒完整后台完成。
  - [x] 正常owner演进与配对激活／主控：受控停6个本任务进程前复核当次quiet与实际PID/cwd；必要配置/两owner私有备份完成，不复制依赖/缓存。Capability正式精确父升级成功；BFF实库先暴露物理列布局误判，再暴露合法queued帧无Agent source行，两次均整事务拒绝且原36表摘要不变。只修owner演进工具，`1086a4f`/`509597f`已推原#17；既有真实PG用例增量RED→GREEN、最终1 PASS/0skip＋规则3 PASS、lint/两文件format及两独审CLEAR，原负控/保值/noop保留，不改canonical SQL/HTTP/认证。最终正常升级成功：BFF36/Capability25表原行SHA核等，来源cursor保值精确搬迁。正式9项Platform/1项BFF专用admin配置成对安装，原8项保留；Cap/BFF readyz200、Agent正式Worker consuming，其裸readyz401为未认证响应。旧App/Admin产物保留，进程登记当场核验；共享Docker/其他owner和两笔财务unknown未动。
  - [x] 正常双身份ACL主片／主控：原Chrome owner＋独立IAB真实普通成员，UI创建专用QA Project→Viewer鲜读/指令readonly→Editor实际保存→owner硬刷新回读同值→降Viewer→真实native Session PATCH精确403/project_edit_forbidden且Project完全不变→owner撤销→成员硬刷新列表消失/直达“项目不可用”且旧名/指令退休。首次负控把应有403误期望404，原件保留后按现contract核对；无模型/资金调用、未把mock当native。QA Project/指令保留供剩余链，唯一grant已撤销，不共享原个人资料。初始强制production前端与本地HTTP/IAM普通Cookie不匹配导致502；已恢复原环境对应的App源码next dev，真实登录通过，生产Secure规则未改。App仅Next自动生成next-env.d.ts开发types路径未提交；Admin现候选next start，后续完整管理native仍待。
  - [ ] 主控剩余：共享项目成功Run/安全FINAL/Artifact输入与peer过程边界→Admin剩余治理/审计→完整原PR正常main与本轮分支清理。Portal29/API/Project文档源码已交付，不再作为待实施项。只补缺口，不重跑旧模型/财务链；TaskB整体未完成，Goal active。
- [ ] B13 真实管理员Custom API及对应审计：Capability owner治理/审计/runtime gate已提交 `efe18a1f` 原#12且主控验收；models_ui_review现消费正规producer pin/generated与个人browser-private治理状态，历史ACK缺值省略而非active。六项新 Admin HTTP／后台已配对激活，正常 quarantine／restore／两事件审计已验，永久 revoke 待本轮单项用户确认。Provider六CRUD/可选托管包已存在不重造，不代理本人RPC、不读取秘密、不建全局审计平台。
- [x] B15 Public29 门户后继：App `08bc30b6` 已推原 #49，九个门户路径消费 BFF `509597f` 的正式 Public29；221 个 public 操作／22 个生成文件，六个 browser-private 排除（完整 owner 227，勿混计）。Project/Scheduled API 概念、产品分层导航与可用边界已同步；writer lint/types/55 tests/provenance/reference/examples/architecture/build、62页21475链接通过，主控九 SHA 核等和 provenance/reference/links 独立复验。后继 BFF runtime 不改 wire，门户 pin 不浮动；原大 chunk 警告保留，不重跑全 App 门。
- [x] B13 正常 Custom API 可逆治理主片／主控：仅新建 `Task B governance QA 20261113`，一项随机假标记，无真实凭据/外部调用。原 purpose 配对后还缺正式 `custom-api-admin` surface，私有备份并仅追加该 flag、重载 Capability 后列表由503恢复200。真实 Admin quarantine security_review：v1→2／owner硬刷新只读；restore review_completed：v2→3／owner硬刷新可编辑。fresh safe 七字段/两条具名审计/真实actor与owner/独立原命令核等，owner只读确认原sealed材料仍活跃，不解密或回显值。临时平台管理员 false8→true9→原false10、仅本轮Session正式logout及Cookie回收；旧工作会话保持，撤权后台GET403。**永久 revoke 尚未提交，待本轮针对唯一新QA配置的用户确认**；不挪用已用过的三项删除授权。其余后台原范围仍OPEN。
- [x] B14 Project Skills九语言词条组／shared_project_pin_skills_review实现、shared_project_run_display_audit独审、主控验收：App `98ebcdc6` 先补en空态，后继 `f942f35c` 将现35个projectSkills.*＋emptyState在9locale各自覆盖，并仅退役本组34项英语fallback/8spread，不改组件/通信/其它fallback/zh/ProjectTodo。主控最终10SHA＋zh源核等，新增组真实RED后同文件58 PASS/0skip、scopedlint/非增量types及独审CLEAR。正常English空态、French整弹窗/项目卡片已验；390px document390/390、dialog371/371，恢复原en/默认viewport。其余七语为resolver/插值而非全截图矩阵；不为翻译重复全默认/build，不冒全站本地化。
- [x] B09既有邀请/接受/leave原件核销／主控＋只读审核：497bcd810c3f33b82fe06ce8原receipt outcome/cleanup/credential检查passed，exact收件人→接受→self-leave、owner鲜读缺席、同原生Session有效而Product200→403已有。主控重核receipt SHA，App TeamPanel及BFF team route/iam窄client与已验旧源三路径逐字相同，不重跑这个完整旅程。该run为真实隔离PostgreSQL/原生装配，不冒正常持久IAM运行；角色/remove/resend/cancel旧E原件仍缺，按下项只补这些。
- [x] B09角色/remove/邀请撤销补缺／主控真实浏览器、shared_project_pin_skills_review独审CLEAR：Root `05e41af2` 精确IAM/BFF/App，真实隔离PG/native run `6b3033901c1c791ac9fd39a3`。UI invite/accept→member/admin/member→remove取消零DELETE/确认移除→同收件人重邀→同新ID resend→cancel，7业务写均200；同一独立observer原生Session始终有效，邀请读403/200/403、移除后Product403。最终pending0/两旧context404/dispatch0、owner保持，浏览器正式logout/authenticated=false；outcome/cleanup/credential检查passed，主控另核测试DB不存在/三份源码副本回收。邮件为fixture捕获，same-session权限由独立observer证明，不冒正常持久IAM/SMTP/全部Admin。首run `03664478a87a6059fd7ef39c` private scope漏正式accept而403/页面503的FAIL保留，cleanup passed；仅两ignored helper exact路径修复及负控后新run，无生产权限/正常团队/模型/资金写。
- [x] B13 Provider元数据正常native补缺／主控浏览器、shared_project_run_display_audit独审CLEAR：唯一无凭据QA目录项POST201/v1，立即停用PUT200/v2，只改名PATCH200/v3，硬刷新保持，再启用/停用各200至v5。独立自有native Session经Admin BFF→Capability fresh GET200核exact key/name、disabled/v5、origins/scopes空且仍需授权；无OAuth/Prepare/Connection/工具调用，旧两项不改。临时admin原false/v10→true/v11→false/v12，撤权GET403/页面目录清退，自己的Session正式logout/Cookie回收。源码/Schema/协议未改，不重跑既有162恢复例。CDP正文eviction和首helper误读顶层字段KeyError保留，正式schema下仅重读GET成功。**本轮唯一QA仍disabled登记，永久移除未提交**；不冒Provider专用治理审计或外部授权端到端。
- [x] B13 IAM审计窄接线／主控验收：Root `806cd1dd` 精确组合IAM814/BFFbec/Admin615/App0d38已完成真实Chrome原生链。25行首/次页共50个互异id与IAM当前tenant原事实逐项核等；键盘下一页、上一页原序、硬刷新恢复通过，native独立GET200仅14安全字段。临时平台admin false12→true13→原false14后，同一自建Session仍authenticated且审计403，Chrome刷新旧rows=0；自建Session正式logout/Cookie回收，原Chrome不注销。en/zh切换及中文390关闭菜单document390/390通过；**语言下拉展开397/390的7px越界为独立UI缺口，未冒通过**。四仓源码与Root门已验且推原PR，原FAIL保留；私有收据 `var/dev/task-b-takeover/b13-audit-native-receipt.private.json`。只闭合当前tenant IAM安全审计读，不冒Provider专用审计/全部后台或TaskB完成。
- [x] B14 Admin语言菜单390px边界／主控：Admin `1ed8083`沿原#7已推。真实RED展开397/390后，仅现语言Select增横向shift；原hydration4/非增量types/单文件lint/Next build/posttypes及独审通过。真实Chrome en/zh展开popup right371、document390/390，键盘选择/关闭通过；en/default视口已恢复、自建页关闭。临时admin恢复原false/v16、仅自建Sessionlogout/Cookie回收。未重跑全默认/加组件/隐藏溢出；Root补同一Admin3个证据commit，原420blobs逐字核等。
- [x] B14 Admin恢复页多语言／主控＋shared_project_pin_skills_review实现＋独审CLEAR：Admin `33bf2f0`沿原#7已推。四硬编码正文接现zh/en，两个互斥server失败分支包现Provider；AppShell/恢复effect/权限/取消保持，无新store/cookie/布局/协议。原两test先6FAIL后14PASS，主控独立14/完整默认388 PASS/0skip、types/scopedlint/Next build/posttypes过，7SHA核等。真实Chrome已准入→临时role恢复false→Refresh：English标题/提示/Retry/产品链接正确、private rows0；原false16→true17→false18，自建Session仍authenticated后正式logout/Cookie回收，原Chrome保持，自建页关闭。首cold非管理员直链本按原guard回产品，不冒该次触达恢复页；两个独立失败分支为layout测试/构建证明，未注入正常IAM故障。仅Admin构建前受控停止并恢复200。
- [x] 最终默认门固定源码／主控：BFFbec `pnpm test` 2591 PASS/2条件SKIP（原schema安装/nullable tombstone条件例），1322 tracked起终SHA相同；App0d38 6885 PASS/0skip、1593输入核等；Admin1ed默认387 PASS/0skip（workers=2仅并发约束）、203输入核等；Agentce57原默认3650 PASS/955按原marker排除、541输入核等，3455 SDK实验/弃用warning保留。各为同一停写基线完整终态，不拼接旧focused，不冒真实integration全部通过。已有合同/构建/types/门户精确来源证据沿用，不重复跑。
- [x] 六owner原PR出口／主控＋两只读owner审查CLEAR：Capability#12、Admin#7、BFF#17、App#49已正常merge main448a8804/cf71291a/c43457ba/f7ccd733，前继只各补一份过时交付说明；各merge完整树等最终Doc候选，业务源码等已验efe/33/bec/0d38，无重复默认/模型链。各远端topic清除，主要checkout均local main；App既有占用worktree的旧local topic保留，不删工作树/未交接状态。原两owner IAM/Agent已main，相关十仓gh OPEN均0，唯一Root#67 OPEN。只完成独立owner出口，Storage/共享成功FINAL/原unknown与三QA确认仍OPEN。
- [x] Root Connect发行来源治理／主控验收：原实际15边检查因Platform receipt发行efe与runtime merge448的错误相等要求FAIL；两合法doc/双父merge RED后，仅复用已有Storage canonical发行祖先＋四Proto/owner provenance全字节相同检查，原vendor/combined/codegen/精确版本/其它负控保留，原Agent receipt/生成物不改。主控停写两SHA核等、完整相关174 PASS/0skip、Ruff/格式通过、独审CLEAR；真实topology/15边0违例/原checkpoint均PASS。420提交证据blob核等，426引用只更新四owner main提交，全部摘要不变；原FAIL保留，不以重新签名或回退owner pin消绿。
- [x] Agent独立owner PR出口／主控、b13_audit_independent_review CLEAR：原#49正常merge main `49901fd7`，完整树等已验ce57，无新source/Schema差额；本地未占用main先CAS前移再切同源码树，避免运行源短暂回到旧树；本轮local/remote topic已清。fast/service-acceptance实际未启动，annotation为账单/额度，未绕保护/伪报CI绿。正常进程同源码不重启；Root/BFF/Storage共享成功Run→FINAL仍待，不冒整个TaskB完成。
- [x] B10 装配期取消缺陷与主路径／主控＋shared_project_pin_skills_review实现＋shared_project_run_display_audit独审：Agent `b61234b` 已推原 #49，仅现装配等待续租与listener时序，保 fence/manager/清理，不增状态表/框架。主控最终 test_main9、相关191 PASS/5integration未选、完整Ruff/Pyright0/wheel/sdist及独审通过；首次误选资源测试5 setup ERROR保留。正式 HTTP/Worker 成对重载后，新的真实 Run 在 Docker 装配时点击 Stop，175ms terminal cancelled、原命令 succeeded、model0/未绑sandbox、唯一 run.completed(cancelled)；硬刷新 Stopped。前一活跃 Run 期间修改运行源触发 StaticRecipeIncompatible 是真实失败，旧Stop仅admitted，不混为取消成功、不削弱配方门。后继只读 Worker Docker子进程0，但daemon version5秒超时，**未证容器不存在或共享Docker恢复**。
- [x] B10 正常 SSE 503 缺陷／主控修复＋独审：BFF `adf31d9` 已推原 #17，仅 frame_page 透传 source_subject_id。现有 creator→editor→creator 真PG replay先RED42703后GREEN，最终格式化后1 PASS/0skip，四纯文件91 PASS/0skip、build/types/lint/format及独审通过，自有PG库DROP+absence，未重跑完整默认。仅受控重载 BFF，正常 native Session→同源Web→BFF SSE实际200/text-event-stream及真实id/data帧，自己的Session正式退出、Cookie回收、角色不变；Chrome硬刷新恢复 Stopped并保旧失败。最新55Run全终态/pending0/旧两笔财务unknown保留，绑定此次只读快照，不作为今后重载依据。
- [x] B10 grant真实墙钟到期／主控：复用原QA Project/原普通成员，正式 native PUT viewer＋20秒UTC到期；期限前access/Project均200，真实墙钟经过后均404/project_not_found、成员列表移除，owner仍200。未改库/系统时钟/TTL，原grant已正式恢复revoked，两个自建Session均200退出；收据本地ignored。只关闭HTTP期限事实，不冒全浏览器倒计时或共享成功执行。
- [x] B10 Scheduled协作本片／shared_project_pin_skills_review实现、shared_project_run_display_audit独审、主控验收：`ef9e64e` 推原#17，middleware仅既有READ预检＋repository锁内EDIT；主控整HTTP/Nest文件15 PASS/0skip、types/lint/build/两SHA核等，owner/private lookup不变。Root `72bffec1` 精确组合受控重载BFF后，真实双native Session：成员创建远期2030 QA任务200、creator实际执行人；另一editor保存强制paused/清executor，显式启用绑定当前actual actor；viewer读200/写403原定义不变，旧revision409，最终暂停/删除。首轮源404、private role键错误、后继把异步pending/null误当必须立即next_run_at的oracle FAIL均保留；两轮自有QA均已正式retire、原grant恢复revoked、各自Session200退出。只证明协作定义/身份/CAS，不冒自然到点或浏览器倒计时。
- [x] B10 正常 Scheduler 进程恢复／主控：native后核到旧PID登记失效、8087无listener，BFF剩9条自有QA outbox，不冒只是瞬间pending。只读确认原Scheduler2项paused、active0/未完occurrence与dispatch0，原service token配对；仅从既有clean源码/原config启动缺失Scheduler，readyz200，不改代码/Schema/卷、不停其它进程。原worker按原命令自然交付后：两个QA delete回执succeeded，BFF任务0/自有pending0，真实Scheduler对两个名字GET404/schedule_not_found；先前3条失败历史回执保留，不手改状态/重置重试。云E2B/共享Docker依赖及共享成功Run仍独立OPEN。
- [ ] 当前／B-13 Skills治理→用户可见性：正常native既有QA current v5已完成audience catalog→owner→catalog三端鲜读，quarantine200后非owner目录200空/详情404；restore503明确来自Storage GetPackageReference196ms内依赖失败。S3 HeadBucket200但List500 InternalError/0 drives provided，Docker daemon _ping/version/containers各4秒timeout；当前VM日志含11-12 22:53 I/O/journal中止/只读重挂载（不冒05:44新内核事件）。等待共享Docker VM受控重启裁决；不清卷/重建，不新发版本。QA当前仍quarantined/state8，原restore正文/key已私有登记，恢复资源后只重放原命令并鲜读同id。临时平台管理员true/v7已正式恢复原false/v8并注销自建Session，原工作会话保持。其余独立工作继续，Goal active，不把整体标blocked。

- [x] 正常运行恢复：九个已登记owner监听及Agent正式Worker恢复；只读确认Run全终态/pending0，复用现有purpose凭据进程内配对后观察到正式consuming。不是本轮新模型全链验收；原配置/持久资源保留。App仅Next dev自动生成的next-env路径diff未提交，不是遗漏业务源码。

主控唯一管理Root台账／Git／资源／最终验收；两agents先独立调查，R-07单writer。每仓沿原PR，完整验收后正常合main并清本轮分支；不部署、不清卷、不删除归属未明worktree。用户2026-11-12已明确要求设置目标，机器Goal现为active：完成Task B已批准剩余功能及原PR/main/精确组合出口。按本TODO持续推进，局部依赖只约束对应动作，不自行暂停或误标整体完成。

## 上批已交付：Composer体验＋页面请求性能

[诊断与最小方案](docs/reports/2026-11-12-composer-ui-and-api-performance.md)。主控先真实采样再修根因，不把单截图通过冒全站UI完善；不为“性能”增加cache／新认证层。

- [x] UI-05：模型菜单定位／间距／checked／长名称；composer_ui_audit负责独立Composer写区。
- [x] UI-06：成功空目录与锁定选择缺席时不误标另一个默认模型；同一writer，保草稿／选择／命令。
- [x] PERF-01：删除未打开Settings/目录的无用connector预热，保现Composer/default/restore/chips；api_perf_audit负责独立overlay与相关测试。
- [x] 主控验收：停写后相关回归、正常读路径对照、首次打开/重开与菜单浏览器验收；文档与精确组合已验。本地已验：focused411／完整lint、非增量TS、build／预览E2E8通过；正常页17→raw15（含独立session1），可比页面读14，三次无用目录读消除。首次Settings三目录200、重开复用，原菜单／Esc通过；自有PR／main清理以本批Root PR最终出口核验为准。不把最初截断片段或单样本当p95。
- [x] PERF-02（源码/正常激活已验，原PR整体交付仍待）：BFF原#17 `9cc7171`，GET完整准入3→1/真实HTTP peer六跳RED→两跳GREEN；保首Session/current_membership、本人tenant SQL及expiresAt/断连/绝对预算，PUT三校验与写后unknown不变，无cache/新认证层/协议/SQL变化。主控四输入冻结核等、51 focused PASS/完整types/diff-check，writer最终build/scoped lint-format通过，独审CLEAR。正常BFF在53 Run终态/pending0后同原配置受控重启，旧两财务记录保持；真实IAM/p95未测，不冒全TaskB/原PR完成。Root精确组合232真实blobs/290引用更新，拓扑/15边0违例/原checkpoint均PASS。
- [x] PERF-03（源码/定向验证已收口，正常原PR待整体交付）：BFF原PR17已推aad81e7，4生产路径+2现测试仅修GET /v1/models一次deadline/signal；首完整Session+membership保持，退役零后续System/在途socket关闭/剩余预算/同步最终send，删本GET无用幂等Map。原真实逻辑RED1/9→最终34 PASS，主控最终六SHA/34/完整types，独审原六文件CLEAR；零预算header补口由主控发现、原子例RED后最小修并复核，其余四SHA不变。writer最终build/scoped lint通过，测试既有全文件format告警不冒绿。正常空闲后受控切aad、healthz200，53终态/pending0/旧两财务未知保持；只证明HTTP peer/本方取消，不冒System回滚或p95。Root按232真实提交blobs/290引用重算；本轮拓扑PASS、兼容15边/0违例、原checkpoint PASS。
- [x] icon404观察项核验（无代码修复）：当前native同一Context7 server详情200且未保存icon绑定，独立媒体404；本次挂载1次媒体GET，打开详情没有重读，UI保首字母C/Connected，目录200。对应BFF正式可选字段/无绑定404和App不重试源码/已有定向覆盖一致。旧布尔测量没有exact URL，未倒称原次根因；本次404响应body被CDP回收，仅保status/详情字段，不冒完整trace。无需新增cache/协议/代理。

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

## 接管前遗留归属（Task B已接管项以上方当前队列为准）

| 项目 | 负责人／阻断点与下一动作 |
| --- | --- |
| R-06在用i18n正式迁移 | shared发行owner＋App consumer owner；先确认`@kokoro`包scope／现有registry／不可变版本和读权限／发布授权，再原子切manifest-lock-Docker并删i18n副本；当前不以本地bridge冒正式发行 |
| R-03 Admin菜单／旧页面正式接线 | Task B Admin owner；沿原后台PR完成真实业务，不接管、不造成功页 |
| R-07 Capability contract-check写副作用余项 | Capability owner／Task B #12；normalizer与现组合生成物相连，需在该组合做只读check。Storage部分已完成，不重复修 |
| R-14 MCP OAuth DNS pin生命周期 | Capability owner／Task B #12；client无直接hunk不代表composition无依赖，不从独立main小补丁冒称Root组合已修 |
| BFF canonical认证metadata／README／INDEX清理 | 2026-11-13已核销旧待办：Public28.36起已纠正，当前28.38/217操作和Admin46消费均正确native；App28.37同样正确。主控现BFF contract102 PASS/App消费1 PASS，普通业务无旧Bearer，唯一skill.list为独立User API Key/OpenApp例外。历史inverse保持，不再重复改认证或机械升级pin；门户其它文档随原B15范围收口 |
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
