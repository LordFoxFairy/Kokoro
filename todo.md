# Kokoro · 当前执行 TODO

更新：2026-11-13。唯一执行清单；Task B接管基线Root `1092d99b`（当前候选沿原#67），不重开已交付Task A，不重复扫描凑问题。

## 当前任务：Task B 正式接管（2026-11-12）

用户已把 Task B 移交本主控，历史“Task B 不动”仅约束当时 Task A／UI 批次，不再排除本任务。沿[原功能交接](docs/handoffs/2026-10-30-task-b-capabilities-account.md)和[既有有效计划](docs/superpowers/plans/2026-09-03-kokoro-production-closure.md)推进，不重开已交付 Task A、不另起任务中心。以下是接管后的真实剩余队列，不把原15个功能域当15个新故障。

- [x] B-T0 接管：确认原 Root #67、App #49、BFF #17、Capability #12 及当前 main；主控保原PR历史、全部12个已验 main gitlink和正常运行源，不盲激活旧组合。Root原分支已合入当前main；原468行Task B记录保留。
- [x] B-T1／R-07（writer api_perf_audit；主控验收，独审 app_merge_gate）：Capability contract check 改为只读；显式generate仍能写。临时生成后完整集合／字节比较，覆盖漂移与异常回收；不改 wire、Schema、生成器算法或正常服务。已沿原Capability #12提交推送 `c040dda8`；主控8 PASS／真实contract check、类型／相关lint／格式通过，803个输入SHA／mtime／mode不变，四实现测试输入冻结核等。本片源码及后继候选组合已验收待PR合并，不冒整PR／Task B验收或merge。
- [x] B-T1a（已合Agent main／Capability原PR待收尾，api_perf_audit验证／主控集成）：Agent `281bde49` 顶层provenance及3处常量／断言精确配对Capability `573a8f00`，四Proto／生成物及独立历史pin不变。正规generator／Ruff／Pyright／wheel安装smoke通过，主控正常Python3.14.3四contract文件129 PASS／contract-check，四SHA核等。先52 Run均终态／pending0再SIGTERM三个相关进程，正式HTTP／Worker／Platform已恢复，health／ready200、Worker消费；原数据和两笔未知财务记录保持。Agent原需求PR #48已正常合main `b7867212`，merge树等已验281bde49，自有local／remote topic已清；4条CI红因账户账单／额度未启动，未绕保护。后继Root `db28020c` 固定Agent main与App34c51204，inventory按131真实提交blobs重算150引用，拓扑／15边0违例／原checkpoint通过，未放宽门禁。managed隔离工具未返回，实际验证使用ignored源码archive fixture，正常应用由主控受控完成。
- [x] B-T2／R-14（源码及候选组合已验待PR合并，api_perf_audit实现／app_merge_gate独审／主控验收）：OAuth DNS pin 限定一次有界操作，保同操作DNS漂移拒绝、实际IP连接／Host／SNI／取消，不清共享Map冒修复；现设计／factory装配已完成，沿原#12提交推送 `573a8f00`；writer相关63例、主控两直接文件17例／完整types／scope lint-format通过，五输入冻结核等、独审CLEAR。HTTPS仅socket替身、取消保真实loopback；未跑真实Provider／PG／全默认。本项源码收口，不冒实际授权／整个PR完成。
- [x] B-T3（首片已验，完整原PR仍待后继范围收口；composer_ui_audit实现／app_merge_gate独审／主控验收）：App原#49保留双方历史并合入main，候选 `a0512901` 已提交推送；机器契约保现28.35及22个正规生成检查。主控完整lint／非增量TS／build通过；rail首轮290 PASS/5 FAIL，按当前行为修正后295 PASS。完整默认实测6753 PASS/2 FAIL，两处旧oracle修正后原两文件48 PASS；未重跑全默认，不拼成全绿。主控native-auth实测API创建201→fresh exact详情→刷新恢复、JSON两项import201→显式选择B→fresh connector/server详情→取消未保存编辑→刷新原值，均通过；未执行Connect／Prepare，秘密未回显。用户已确认删除3项登记测试配置，真实三DELETE200＋硬刷新仅剩原Context7，不动原配置。Root `ae480fb9` 精确配对App，真实blob inventory／拓扑／15边0违例／原checkpoint通过。BFF原#17后继已保历史收口609并正常激活，细节见B-T3b；不激活旧29.3。
- [x] B-T3a／B-14 本片（composer_ui_audit实现、api_perf_audit独审CLEAR／主控验收）：bootstrap隐藏未读模型误报；MCP详情／管理／配置／JSON接现t及本片九语言，不改框架／契约／认证。App `8208882d` 主控四文件443 PASS／build，正常English详情→JSON非法反馈零MCP写、取消回焦与390px内收通过；真实French320又复现默认词条中文回退／English占位，后继 `34c51204` 只修10个现有key及原测试，主控117 PASS／build／8输入核等、独审CLEAR。最终正常French320空白MCP表单真实标题／保存／icon提示均已本地化，宽288／scrollWidth288，无创建提交；恢复en／视口。本片不冒全站翻译或九语言全视觉QA，Custom API与目录其它旧占位随B-02/B-14统一承接；后继浏览器network缓冲发生eviction，不将留存零写冒完整network证据。
- [x] B-T3b（BFF/App当前源码消费与normal子旅程已验；供应商末端交B-01、整PR仍待）：主控联合候选 `0a2c98ae` 已提交推送，Share GET／现IAM既有delete_series枚举／MCP显式重新授权同片337相关例、完整build/types/lint、216semantic、两正规check通过，114输入冻结、独审CLEAR。真实ChatModule/Nest＋隔离PG7 PASS／0 SKIP，准入显式double、无Redis；URL漏owner schema与deleted seed漏deleted_at两次失败保留，仅修接线/fixture，不改生产约束，三个自有测试库均已DROP。新private profile旧Bearer改真实native；初始Session期间断连/0预算真实4 FAIL→4 PASS，退役后manage/owner0，已发Session仍原timeout边界保留。原#17已普通保历史集成到 `609b0e93` 并快进推送，源树核等0a2；82冲突及无冲突混入按具名语义组处置，移除重复旧测试/退役层/未发行旧pins，不复活RSS旁路或旧8.11 context；B08当时待核；本轮后继已按当前8.17实装并完成native，见上方B-08。App已固定blob0a2正规消费Public28.37和new private profile，提交推送 `ebc36617`；主控23生成检查／60文件1216 PASS／build，独审后3缺口修正再验6文件185 PASS／types／SDK check／build，110输入冻结核等、独审CLEAR。Share不确定命令在同主体tenant恢复时保原key、坏provider ACK拒绝、Shared SDK必需path.id均已承接；正常BFF609b0e93／Appebc36617已受控激活，health与页面200、原生会话刷新恢复。真实Share打开仅GET200/零POST；MCP自建空配置Disconnect→显式reauthorize200→不同新connector pending/disabled/version1→exact Connector/Server GET200→硬刷新保持未连接，零自动Prepare/OAuth，原Context7不动。整PR仍Draft，未冒供应商末端或完整Task B完成。
- [x] B-T4／Storage #2（已合main并清本轮分支）：真实PG核对否证原fresh1d60→0f480假设，已撤回未提交兼容分支；生产工具／canonical不改。现仅修历史FINAL工具/helper/993aede目标Schema的测试冻结、当前workspace_output枚举oracle与测试URL GUC隔离；原业务行／no-op／ArtifactsStore断言保留。主控真实6 PASS、格式／ESLint／types／独审CLEAR，两SHA核等；3个注册probe库及fixture自有库均回收、正常DB未改。`47bf19d` 两文件修复已提交，普通保原add2历史集成 `31a7c89`，完整树等已验47bf19d；原#2正常合main `7155093c`，树等已验源；本轮local／remote topic已清，其他dirty工作树不动。远端CI因账户账单／额度未启动，未绕保护，不带未获实证的旧兼容配对。
- [ ] B-01／B-02：当前消费者／正常源已配对；本次真实MCP显式断开→新身份→鲜读→刷新已验，Prepare／外部授权末端与Custom API缺失冲突／撤权／迟到及秘密边界按原缺口承接。新增1项无密钥QA配置已登记，待用户单项删除确认，不将此前3项已使用的删除授权重复挪用。已有真实Docker成功／取消／刷新不重跑；完整云E2B沿已接受边界暂存。
- [ ] B-03～B-05（composer_ui_audit只读已核）：ZIP/GitHub导入、安装启停／下载／移除重装、v1→v2→撤回→历史恢复新UID/v3→系列删除及作者/同团队负控既有计划记载真实收据且已核源码祖先在当前（旧原件本次未重定位，不据此整体提升验收）；11-12真实Skill→MCP→Docker→FINAL也已验，不重跑模型。剩余只补广场／Settings／Project三入口exact身份与读历史一致性、后台／管理员撤权与跨tenant边界。AI创作／录制当前为fresh Composer prompt-starter，不冒实际录制/自动产包成功，不因旧待领取状态重造Skill框架。 现Root3389/Appbf8正常浏览器新增：Settings安装/作者当前版本历史/广场source_ref、revision1、包目录及正文完全核等；只读RPC非生命周期写，原Settings pin保持。当前无Project、该作者仅v1，故Project现行关联和旧版恢复仍未重跑，不造新版本/项目凑证据。
- [x] B-02材料边界补验（api_perf_audit聚焦核验／主控执行）：Capability573当前真实PG4 PASS（执行准入double、自有随机库回收）；Agentb786 Python3.14.3客户端／执行环境／秘密产物出口＋真Factory接缝107 PASS（sandbox/model doubles），BFF609当前独立checkout单文件7 PASS。复用既有Docker成功／取消／刷新；未跑云E2B或重复模型。只读核验未发现具体Acquire明文新出口，不制造每载体重复测试；不冒任意编码/外网的通用DLP、全存量日志扫描或真实IAM撤权。
- [x] B-08当前已批准手工个性化/知识范围（已验待原PR完整交付）：BFF代码143/文档abbfd78，App代码c044/文档bf8ef938；无新owner/协议/表/认证/记忆服务。原事务可信actor同snapshot冻结、原key零重读/regen原快照、1MiB/取消及闭集生成主控68/真实PG5/现Agent21、两独审通过；知识启停/删除/跨主体/失败风险按这些最低层级承接，不每组合重复模型。**Root21e833c4精确组合native已验**：真实UI onBlur保存临时偏好→新消息本身不含标记→正常配置模型一次调用实际按偏好回复→AI SDK展示→硬刷新同一条回复恢复。BFF私有context与Agent request_json完全相等、owner核等、userMessage/trace不复制原材料，双Message/Run终态、financial ACK存在；原四空字段经正常UI恢复revision2，原两未知财务记录保持。最终DocOnly owner后继与此代码无差，冻结组合317真实blobs/383引用重算，拓扑/15边0违例/原checkpointPASS。公开产品一页/导航/9语hint、47/types/门户build+62页20513链接/App build均验；自动长期记忆/外部导入未开放如实说明，不新增该扩展，不冒全TaskB完成。
- [ ] B-09／B-10／B-11／B-12原差额：旧计划具体记录及源码祖先已核，旧E目录原件本次未定位，不整体关闭。B09主动leave仍只有组件覆盖；B10 Chat/Skill已有计划实证与现metadata读，Project ACL未有缩范围裁决，不能用复制URL代替；B11/B12既有B08 Run精确模型/冻结报价/结算/账本已在下方只读补证，**当前活动政策已只读补证（见下），对应后台完整管理及其它原缺口仍待**。不重跑模型、不强释旧unknown。B06/B07当前差额已补验；真实支付关闭，不新增内部OAuth/认证层。
- [x] B-11/B-12已存在B08 Run绑定/结算补读（主控只读、composer_ui_audit核schema）：不新调用模型、不变更资金，只对同一已验Run分owner只读查询。唯一dispatch/attempt/admission，可信actor/payer、call/ordinal/三摘要、精确模型revision/digest及冻结报价完全配对；actual=verified，最新evidence/ACK绑定核等，ACK/admission/hold=captured，usage/settlement=settled；真实usage debit金额与capture、allocation和capture/release守恒核等。首摘要UUID类型比较误报已纠正并保留，不是生产缺陷。只证明该Run，不冒今天活动政策/所有旧unknown/全部后台已完成。
- [x] B-11/B-12当前活动政策只读补证：Billing正式选择语义（DB时钟，先tenant整revision、effective_from<=now，再按effective/revision倒序，最后过滤精确模型）；只读repeatable-read实查活动rate v3/policy v2，与latest一致/非未来，rate行数与header一致、profile配对、已验模型exact revision/digest仍覆盖且币种与policy一致。只证明该时点/该模型，不冒新执行、后台publish或全部模型可计价；无报价/资金写或历史快照重算。
- [x] B-06当前会话管理缺失接线与实测（主控配置/正常native，app_merge_gate定位）：仅补normal IAM/BFF既有account_sessions专用路径，独立随机profile/固定正常tenant，原配置私有备份；源码/协议/Schema不改。原503复现后，两端受控重启healthz200，真实浏览器列表200→只撤本轮自建独立Session DELETE200→fresh列表200目标消失，原当前/原另一Session保持；被撤Session auth=false且业务GET401。另一新QA Session仅fixture缩短expires_at至8秒，正式GET先true/真实expiry一致→墙钟经过后false/业务401，无先logout/全局TTL改变；不是七天浸泡或浏览器自动倒计时实测。两测试Session均正式logout/自有Cookie回收，53Run终态/pending0、旧两财务记录保持，不新跑模型/全默认。
- [x] B-07缺失双标签CAS主旅程（主控正常native，Root3389/Appbf8/BFF9cc，无源码变化）：两页同revision2，A PUT expected2→200，B PUT expected2→409且草稿保留；显式Reload→展示权威A→Use server profile→硬刷新仍A；按新revision3 PUT恢复原四空字段→200，原标签硬刷新核空；另新原生Session正式CSRF表单重登GET200/revision4全空，随后仅退出新Session/删除自有Cookie。原工作Session保持，无模型/工具/知识开关写。三个写阶段网络证据完整；首A读取collector未捕获、旧response body后被evict如实保留，A outgoing expected2及B初始GET2证明基线，不冒全程trace完整。只是本缺失旅程，不等于B06自然到期/独立设备或全TaskB完成。
- [x] B-14 Skills语言本片（composer_ui_audit实现／api_perf_audit独审／主控验收）：en两现key补齐、两日期调用显式locale，其他八语言不改。主控5输入冻结41 PASS／types／build；正常英文桌面＋320px文本内收/日期正确、无横溢/长标签自然换行。原#49代码844fbbcb＋文档0c6078e3已推，正常App同源激活，不重跑全默认/九语截图矩阵。
- [ ] B-13后台（主控验收；原Admin #7/e7f2f79）：成员目录读取/本页筛选/中英UTC、390px标题换行、撤权403清空及重新核对已验；原正常临时角色恢复false/v6，测试Session清理，原工作会话保持。模型/标签与计价写后回读的缺失旅程本轮已补，详见下一子项。剩余只按原具名范围：Skills管理员审核→用户可见性、Provider/MCP/API管理、用户/团队邀请角色及对应owner审计，以及本轮确定的草稿发布UX修复；不扩任意User360/退款/统一跨owner日志平台。PR继续Draft，整后台未宣称闭环。原第六次ENOSPC失败/人工回收记录留CURRENT与原计划，本轮第七次已自动回收，不再将旧磁盘预算列作现阻塞。
  - 最新实测：Root58215eca精确六owner第七run，r1空bounds发布409保留；r2显式8192/1024草稿201/发布200、label201→两次CAS200别名修改恢复、rate/policy各201、硬刷新/正式GET/原body-key replay通过，五表资金/Run均0。原driver恰1revision oracle FAIL保留、cleanup PASS；主控独立补充实录verifier PASS，不冒原driver或全部B13绿。正常数据/报价不变，无模型/Provider执行。前文ENOSPC与预算为第六次历史；当前容量恢复，未新复制源码/依赖。
  - [ ] 源码已交付、native补验待收口：BFF原#17/396897b8（Public28.38/217），主控真实Nest/loopback owner与契约190 PASS；原整contract1400/2旧oracle失败保留、两原oracle准确修正后不重跑全套。Admin原#7/df7883d固定46ops、退役旧唯一vendor，原草稿PATCH/CAS/unknown/onPrepared退休/取消/不rebase接通，最终全363/0skip、全lint/types/contract/build/post-types和独审通过。App原#49/c1444ee0桥接，主控56/build通过。三仓已推原PR，normal App/Admin/BFF按原配置恢复。Root精确组合拓扑/15边0违例/原checkpoint PASS，未合main/部署。
  - [ ] 下一检查点：隔离native真实同一草稿编辑补齐→publish→刷新（仅本缺口，不重复费率/模型/支付）；准备接线遵新轻量复制规则，不复用旧node_modules/venv复制配方。此前r2另建成功不代替该路径。
  - [x] B14随片两组件/Ant默认双语：Admin原#7/87c228c，60自定义key zh/en，现Shell单一ConfigProvider随locale选择官方语言；主控全367/0skip、全lint/build/posttypes与九SHA独审通过，保护原业务，非整个后台文案/视觉完成。source-only native driver四ignored文件已纯检查/四SHA主控核等；实际sourcecopy/install/native仍待主控启动，不冒静态为成功。

- [ ] B-14／B-15：视觉／多语言／性能与文档、原PR、精确组合随每片关闭。PERF-02已收口（见下）；模型目录取消已随PERF-03收口，icon404已核为可选媒体缺省回退，见下；不为非缺陷新增代码。侧栏有限切片已沿App原#49提交推送00334cbe：32既有key/九语言、15实现测试输入冻结，主控160 focused/相关lint/完整非增量TS/正常production build、独审CLEAR；真实French项目标题与空态正确并恢复English。此次实际1000px，未冒新390通过；旧15-key阶段窄屏单列。无locale框架/导航资格/协议扩展，不冒全站翻译闭环。manifest caller取navigator而非设置locale另记事实，影响待定向核验，不冒System内容错误。

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
