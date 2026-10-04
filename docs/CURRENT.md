# Kokoro 当前执行事实

核对日期：2026-10-04，R194。完整 **Wave 0–7 goal active，整体尚未闭环**。本文件只保留当前事实；历史轮次、失败与资源收据在 [progress.md](progress.md)（含R189逐字归档原CURRENT），不以历史GREEN覆盖当前失败。

## 1. 唯一计划与质量入口

- [task.md](task.md)：既有Wave 0–7、owner依赖与唯一任务卡；当前执行卡在末尾R194，不另建计划中心。
- [test-cases.md](test-cases.md)：逐页/模块系统级业务测试矩阵，记录预置、步骤、预期、优先级、类型、实际结果/证据及未验项。
- [CODEBASE_MAP.md](CODEBASE_MAP.md)、[AGENTS.md](../AGENTS.md)：目录、owner、工程规范与调用方向。
- 子仓的 tests 不迁入 Root。`scripts/tests/` 只覆盖 Root 治理脚本；跨仓集成/浏览器验收属于 `verification/` 与现有具名Root driver。组件、mock、工程门通过不冒用户业务闭环。

## 2. 当前源码与发布边界

|Owner|当前基线/候选|当前可证明范围|
|---|---|---|
|Web `apps/kokoro-app`|main `21ad177b7af61a3b4ee1c10f6c7262f3c3d20439`（正式Move A contract/client/adapter 28路径本地已提交、未push）加保留的混合候选；B UI仍未提交，原3310未启用Move|R188冻结工作树工程门2454通过、build0；三个真实Next/Chromium用例通过。当前runtime尚未包含Move候选；新增只同步rename2source+正式双操作CSS，当前真实BFF改名/刷新和桌面/640px命中已限定通过。R189 AppFrame view fence与反馈代际隔离完整源码门2457通过、独审0；Files导航片已实际浏览器验收并窄同步运行副本；Library数据503仍OPEN。|
|BFF `apps/kokoro-bff`|main `8e33bc0a64d2f92ab2fcd113b1951f490487a8d3` 加D18 Project DELETE本地事务候选|真实PG/Redis完整182通过；本地事务不等于public DELETE/Storage释放/关联定时任务业务闭环。canonical Run上下文及Direct/创建错误边界已同完整183真PG/Redis门恢复；R190真实两连接Message/Move双顺序与client-created同identity竞争已执行；完整184真PG/Redis通过。四次scope耗尽、发布/live消费仍OPEN。|
|Agent `apps/kokoro-agent`|main `c3bf769`（A3a实现2a9491e后四D0终态设计提交），本地未push；A3b只有测试候选，源码冻结未授，Root gitlink未更新|R192真实PG全部281pass/0skip；完整工程2178pass/379资源deselected，lock/frozen-sync/ruff/types/contract/build0；纯artifact规则与675行事务adapter已分离，canonical腐坏RED→GREEN。仅持久授权与许可边界，不等于provider真正外发、usage/finalizer或Billing费用链。|
|其它运行owner|IAM0537b2d、System9a4e98e、Storage14f2bc9、Platform物理kokoro-capability da813ed、Billing9eeabf3（experimental候选本地commit）、Scheduler e8dca48|这些是本轮实际checkout短SHA，不证明远端发布/全门/用户链。Billing已有任务外变更必须保留。物理Platform cutover及所有owner组合验收仍按既有目标推进。|

Root正式Storage组合切片已本地提交 `8f8f12d80b455f42f91cb149bf89cb50361a42ca`（未推送、不等于原3310已启用）。Root本片起始基线为main `03734b57fcdb1ab383e0f6a175a481a7a9c971f4`，历史台账提交由Git历史绑定；Root不暂存未发布子仓gitlink以伪装组合完成。远端/消费者发布必须另取得证据。

## 3. 最近实际验收

|范围|实际结果与终态|证据边界|
|---|---|---|
|Web|Root22564真实Next/Chromium3pass；Root81224 complete check exit0：258contract、50architecture、lint/types、2454pass/0fail/0skip、Next build0|Direct拒绝改名/非active删除/草稿、旧Move ACK结束busy、unknown同key重试。不能关闭全部CRUD、原IAB、Settings或post-confirm竞态。日志 `/tmp/kokoro-r188-web-full-check-root.log`。|
|Agent|Root86926真实schema58pass；Root16750全database254pass/0fail29.64s；Root49017默认2175pass、352资源deselected、ruff/types/build0；lock/frozen-sync/contract0|352 deselection非业务通过。manifest `/var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-r188-agent-schema-l1q_ndx5/manifest.json`；自库回收/源码不变。schema提交500c2c26不证明模型或费用链。|
|BFF|Root16750真实PG/Redis182pass/0fail/0skip45.28s；schema/build/check/format0，默认743pass+1既定资源skip|manifest `/var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-r185-bff-full-m48kffdh/manifest.json`；自库回收/源码不变/Redis保持。仅本地owner门。|
|R189当前门|Web Root65931 Node22完整2457pass/0skip，contract258/architecture50/lint/types/build0；Agent Root27104全部database267pass73.23s；BFF Root34000完整真PG/Redis183pass0skip46.21s（前两轮181/2、182/1错误不隐去）|Web view source45039523独审0；BFF Direct invalid与创建错误回归已同门关闭、专门scope竞争门/发布仍OPEN；Agent2174pass1fail原cast门保留历史，最终18098已2175pass/365资源deselected且build0；当前BFF本地owner完整门已通过，不等于用户链/发布。|
|Root治理|CURRENT收口后拓扑测试7pass；实际topology FAIL（两未发布gitlink）；此前两治理测试文件17pass/1fail|历史w1e IAM checkpoint与当前owner gitlinks189项漂移仍OPEN。Root完整78556已实际1720pass/1fail/3skip；标准60633实际153violations/0unverified，topology原两gitlink差异FAIL，子仓新窄片提交后实际三gitlink差异FAIL，不宣布全绿。|

测试70组原统计仍11通过/6失败/14待复测/38未验/0旧待决/1支付后置，不因局部门上调。新增“删除项目时独立定时任务的保留/暂停/解绑规则”等待用户决定，单独记录，不阻塞其它切片。

### R190 最新分层结果（当前候选，不等于已发布组合）

- **BFF**：Root35227真实HTTP/PG两case通过；Root60244完整184pass/0fail/0skip45.45s，schema/build/check/format0、743pure+1既定资源skip。Move先/Message先锁图与client-created同key竞争均真实观察；新case清理异常完整重抛。源码未提交/消费，四次scope重解耗尽待验。
- **Storage组合**：新增Root `scripts/dev/local_storage_runtime.py`，复用正式Storage14f2bc9、单应用库独立schema、既有MinIO/ClamAV。Root4389治理40pass/32subtests；Root83744真实owner九项业务检查及同库BFF schema前置共10项通过，签PUT→真实CLEAN→非空列表→下载bytes/digest→其他subject404/非法credential401，自有桶/进程/库收回、源码hash同、Redis6隔离观察同。原3310未启用该profile，Library用户路径仍OPEN。Root43009补真实INFECTED隔离，14项检查通过；Root5631真实scanner unavailable/readiness拒绝与自有清理三项通过，两次exit0/cleanup[]/源码同/Redis6同。build/stopfailure/桶ACK未知等仍未穷尽。
- **Web**：改名三生产/相邻测试路径冻结，最终独审0P0/0P1/2P2；真正Next/Chromium发现commit丢ACK不GET的业务RED后修复，Root83186最终scoped两例PASS25.21s（67名称过滤非执行）、完整`pnpm check` exit0：258contract/50architecture/lint/types、2469pass/0skip（包含69真正Next系统case）、build0。前90201完整2468/1是C post-ACK GET抢先消费D测试故障，仅收紧真实网络次序后通过，未加timeout/sleep/force。2072d0a两生产source已同hash窄同步原3310；实际正规IAM/当前BFF普通改名/权威读回/硬刷新/恢复原题通过。另发现正式双action重叠并按HEAD独立CSS修复a854a81，当前桌面/640px真实点击通过。原IAB历史加载异常的全面恢复/全部CRUD、signal0重挂与parse未知HTTP专项仍OPEN。
- **当前3310 Settings**：正规IAM表单→callback→Home实际渲染；13个可用tab导航/读取观察，不是持久保存或CRUD通过。Billing summary/by-model/ledger/plans503、agents404、MCP与Skills503仍实际失败；Teams读200不是邀请/角色写操作通过。Get help源码明确disabled，误点击产生的测试Timeout保留并纠正为错误测试操作，不当产品缺陷。`/tmp/kokoro-r190-settings-runtime-reads.json`。截至R190原用户IAB同标签未取得恢复证据；R191已取得当前原tab1会话/项目刷新成功正控，历史全部异常仍未关闭。
- **Billing前置**：沿R80-W06/ADR033已冻结14路径experimental artifact3.0.0-experimental.1及personal HTTP闭集registry配对。Root77175初门1279pass/2fail证明旧43/new42启动回归；返修后Root59378最终Node24完整verify/generated drift均0，1347pass/411资源skip，独审0P0/P1/P2。started必须有首次authorized决策，unknown不猜零。契约README过期并列事实已收敛；Root17061最终再完整verify/generated均0（1347pass/411skip22.55s），12实际changed路径已精确本地提交9eeabf3，原5D0+3codec不夹带/源hash保持。未push/tag或消费者pin/Admission与Evidence运行链/实际预占结算释放仍OPEN，机器门不冒正规费用业务闭环。

Root78556完整治理门自然exit1：1720pass/1fail/3skip126.34s，唯一历史w1e IAM checkpoint与现owner gitlinks189差项；未弱化门禁或修改历史checkpoint，不称Root全绿。原launcher45606/Web46036保留；自有验收浏览器已close，无新永久服务。R191另关闭3个无用IAB页，仅保留原项目页。现完整70组统计不因本段局部结果上调。

## 4. 当前开放缺口与推进顺序

1. **Web当前页面与会话**：R191原IAB同会话/项目刷新正控已取得；历史无限加载全部异常与恢复路径仍未关闭。R187仅独立真实登录Chromium验证原会话正文/输入/10s网络挂起可恢复/硬刷新草稿；不是原IAB恢复。R189 AppFrame confirmed/rejected视图隔离102 UI与完整工程门通过，未同步当前runtime。账户Files→/docs404经正规登录真实点击复测已修为/app/library；两tab数据读取503仍OPEN。
2. **Project/Conversation业务**：公开完整项目CRUD、Project DELETE后Storage durable释放、关联独立任务政策未闭合；项目与独立会话须清晰分离。Message canonical上下文正控通过，Direct explicit invalid和创建错误码边界已本地同门验收；新锁路径scope双锁序及同identity竞争已本地验收；四次耗尽、发布与用户链仍未验收；保持Move/删除锁序与exact幂等重放。
3. **Agent执行与能力展示**：真实prepare/ordinal/fence/evidence/finalizer→正式provider→Todo/Tools/Skills/MCP/审批→durable AG-UI恢复→取消/完成→Billing实际费用链未整体通过。先接A1事务，再依已批准owner顺序推进，不改协议为兼容fallback。
4. **Settings**：真实通知与快捷键切tab重置；Personalization无正式owner且404静默；Billing summary/ledger/by-model读失败/缺公开契约；agents404、项目resources503仍开放。Library503已定位当前launcher缺Storage runtime/config，Root正式Storage组合模块已实现并完成自有真实RPC/PG/S3/ClamAV正控；原3310未切换、用户Library仍503，不伪装空库。不得隐藏按钮或伪造本地保存后称完成。
5. **其它页面/能力**：Home提示、独立定时任务、文件作品、审批、Skills/MCP、账号/权限、积分流水逐页验收未齐。支付渠道最后，部署运维不纳入研发扩展。

R189已交接负责人：Web agent4_lifecycle_review已冻结view fence/Files导航，Root仅Files窄片已验收提交；Agent agent_mainline_qa_owner已交接prepare窄片81bc，后继运行接线依旧待验；BFF storage_release_r175_gate_review已冻结canonical scope修复，后继真正scope竞争专门门。原生agent_prepare_final_review最终81bc typed-boundary独审0新增问题，先前4P2证据缺口保留。每仓单writer，Root资源/Git/集成验收。

## 5. 资源与业务约束

- 原组合launcher PID45606、Web PID46036本轮已实际确认live；3310运行目录 `/Users/nako/WebstormProjects/github/thefoxfairy/kokoro-local-login-cda7wvjx/next`。无重复服务、无重启、无共享数据重置。本轮自有浏览器已关闭，测试资源已回收；BFF/Storage/Web已列句柄均终态；Root78556已消费实际exit1，唯一历史checkpoint189差项保留。
- 运行副本仅已批准窄同步：正规auth首屏、R187 snapshot总期限/分页helper/pagehide草稿、R189已验Files导航单文件、R190已验rename协调2source及正式双操作CSS（HEAD独立patch，不复制混合Move）；Move候选没有同步。源码通过与用户运行态分开记账。
- 一个PG实例/一个应用数据库、同一凭据、owner独立schema；一个Redis实例/独立namespace；禁止跨owner SQL或清空共享状态。
- 默认个人私有、显式分享；普通用户/管理员业务权限由IAM执行，不向普通登录堆原始内部scope展示。
- 正式积分：授权赠送→余额→预占→仅核实实际消耗结算→释放其余→流水；unknown不猜零、不提前结算，不造免费完成声明。费率由Billing owner计算，Web只展示正式结果。
- 任务外Root uv.lock SHA256 `f7e1c30d59d5743493ac6d14d02ff2ec7111c94587470fe721d50f8c08dee7b4` 保持；其它owner未交接修改不覆盖或暂存。

## 6. 闭环退出标准

所有明确页面/模块主链、边界、异常、权限、生命周期、刷新/重放、真实owner和浏览器完整用户路径通过，未解决P0/P1清零，当前commit与发布组合相符，必要完整门有真实终态，才宣布完整Wave0–7完成。Root goal保持active。

### R190 当前逐页验收推进边界

沿现70组和R187–R190矩阵完成实际路由/可见操作映射，报告 `/tmp/kokoro-r190-page-coverage-map.md`（8f03645b），涵盖登录/Home/Composer、Direct/Project列表与CRUD/Move、独立Schedules、Library、Agent过程/审批、Skills/MCP及Settings13tab。映射不是执行通过：每项必须有主链、边界、异常、权限、生命周期、刷新与跨窗口证据。Settings设备偏好最小片已只读设计（`/tmp/kokoro-r190-settings-next-cut.md`），没有实施或以禁用/隐藏虚假能力清零。Agent授权观察/唯一dispatch CAS下一片已设计，现表的请求事实范围与replay不得重复外发仍待Root精确收敛，未授运行接线。

本轮原IAB控制工具再次12s超时/kernel reset，未操作标签或证明原页恢复；独立测试浏览器不能冒同标签证据。原45606/46036保留，测试句柄59378/83186均自然exit0已消费；uv.lock f7e1保留。

当前3310真实鼠标验收发现双操作32px矩形完全重合，随后Root仅HEAD→独立双操作CSS patch（6新增/2删除）修正，未复制Move布局/其它未交接source；当前混合CSS29967d字节保留。Root6172真实十项检查PASS，正规IAM→Home可编辑→鼠标/键盘改名、删除取消→实际BFF rename→硬刷新→UI恢复原题→640px两44px命中区无交集，恰2PATCH/0DELETE/0模型调用，browser finally关闭。证据 `/tmp/kokoro-r190-live-rail-verification-result.json` 与窄屏截图；仅限定子例通过，不升70组。一次错误textbox英文名、刷新后折叠行与错误dialog而实际alertdialog的等待失败均明确是Root oracle错误，不混作产品缺陷。

### R191 原用户浏览器当前事实

原IAB工具本轮重新可用，URL精确匹配旧ambient未命中后按真实库存绑定原tab1；没有新开浏览器标签。原QA会话消息与输入已实际渲染，侧栏→用户project_93b2011d项目成功，硬刷新限时等真实标题后亦渲染。此前“未取得同标签恢复证据”是历史边界，现仅该正向路径已有原标签证据；不据此证明历史无限加载所有根因已消除。

项目仍有实际交互缺陷：孤立“专案会话”按钮点击进入新conv草稿路由、与现新对话入口语义重复；网站选择器实际显示launch.example.test示例地址，已取消；刷新瞬态把加载写成“专案不可用”。原生Web/Settings只读负责人分别核owner/handler/持久化与下个修复片，Agent负责人继续A2 tests-first，不宣称运行费链完成。三独立面已续派，Git/资源/台账仍Root独占。

按用户清理要求关闭两空草稿重复页及一旧rp_transaction_rejected回调页，真实库存仅tab1项目页。原服务45606/46036保留live、无新服务/模型调用/共享重置。证据/tmp/kokoro-r191-iab-project-after-reload.png及test-cases R191。原70组完成数不变。

R191 Web孤立入口切片已由Root精确提交main3310351（3路径19+/51-），混合Move CSS和其它test差异继续保留。Root8271 Node22完整check自然exit0：contract258/architecture50/lint/types、2469pass0skip164files151.16s、Next build0；是冻结混合工作树门，不冒clean HEAD组合全绿。当前3310仅同hash备份同步navigation68c1d及独立HEAD CSS4a5eec，不复制Move，无重启；原IAB真Project orphan count0/明确新建入口1，该入口仍能生成Project草稿，返回概览成功。截图/tmp/kokoro-r191-iab-orphan-removed-green.png；网站假保存/Skills/Project CRUD/Settings仍开放。原70组不变。
Agent A2源码87f06+model0898候选仍未提交；Root多轮真实PG校验暴露非法fixture、UUID/SQL参数错误与owned锁图的direct/传递边oracle问题，逐一保失败收据、不放宽schema或预算。grant错ref换绑/advanced begin两P1已源码返修并只读复审0P1，但完整矩阵/最终资源门未收口，lostACK/runtime/provider/Billing仍OPEN。

R191 Agent最终Root门终态（候选未提交/未运行接线）：2138 scoped真PG66pass6.17s；86156全database277pass0skip31.21s，manifest T/kokoro-r191-agent-full-2h40hz61/manifest.json自库absent/sourcehashsame；48540完整工程自然exit0，lock/frozen-sync/ruff全仓/pyright/contract0，2175pass/375资源deselected109.20s，wheel/sdist build0。源model0898c86/repository87f06f6/test0b469f0冻结；只读最终审0P0/0P1/2P2，canonical同步篡改防御和新三transition完整authority/digest/回滚矩阵仍待补。没有runtime/provider/lostACK/Billing费用用户旅程完成声明。所有Root具名测试句柄已消费终态、没有遗留自有测试进程；原45606/46036保持。Source/必要D0同步及最终切片提交待后继，不夹带未完成P2冒零债务。


### R192 当前分层事实（覆盖前述历史候选状态，不扩大验收范围）

- **Agent**：Root已精确九路径提交 `865afb266915f002470e20f0341055271f7c870e`，独立职责/API审查完成；真PG `281pass/0skip/32.90s`，默认工程 `2178pass/379资源deselected/112.54s`，完整lock/frozen-sync/ruff278files/types/contract与wheel/sdist均exit0。四D0最终同步后再build0。真正provider、usage evidence append/finalizer、Billing Admission/结算释放、lost-COMMIT-ACK与用户费用旅程仍OPEN；授权许可不是外部调用或费用证据。
- **Web绑定**：确认只有一个Conversation和nullable project_ref；Root真正Next/Chromium业务RED（返回/刷新Direct owner GET已无A，但本地仍合成A）后修来源缓存失效，正常旅程五case GREEN；storage异常的两业务RED已窄修，owner confirmed不再因本地cache异常误变unknown，dispose继续清理。最终冻结machine97aacfe/testf2c029/UI0c5/system8db6，Root88427当前完整 `pnpm check`自然exit0：contract258、architecture50、lint/types0、164files/2474pass/0fail/0skip/157.66s、Next build0；包含真实Next/Chromium系统用例。不是另外`pnpm test:e2e`或真实BFF/provider/原IAB全部业务验收。作者旧Project-idem一次timeout保留历史，不猜flaky。
- **Web剩余与运行边界**：独审0P0/0P1/1P2仅对本片；导航不dispose、storage阻断后的刷新、跨scope unknown身份与迟到ACK后对账仍OPEN。实际63路径（61 tracked＋2 untracked）混合候选未整片提交；原3310未同步Move，本轮不宣称用户当前页面已启用修复。原负责人只读清点最小可提交/可启用依赖，禁止打包未交接修改。
- **Root治理与资源**：本轮standard实际153violations/0unverified、topology三gitlink差异均exit1；完整Root scripts/tests是此前1720/1/3历史收据，不冒本轮通过。原45606/46036仍live，88427已消费终态，无重复常驻服务/共享PG Redis重置，Root uv.lock f7e1与任务外修改保护。
- **后继**：原Web负责人Move集成只读盘点与原Agent负责人A3 evidence/finalizer设计门并行；同仓仍一writer，Root独占资源/Git与台账。原70组11通过/6失败/14待复测/38未验/1支付最后不变，完整Wave0–7 goal active。

R192后继设计门收据：Agent四D0已Root逐读放置、包内immutable append command/receipt、strict完整JCS/受信时间/DB-safe int64/active successor与terminal只读边界，精确docs-only提交d5cac24；没有A3a实现或新PG通过声明，A2实际源码仍865afb2。Web原writer仅既有R158/R170三D0段收敛，去掉这两段后的内容hash前后相同；保护其它任务段。下一步Agent仅真实PG失败行为tests-first，Web正式Move闭集hunk抽取/当前3310 actual BFF7.1探测，未获证据不散同步。


### R193 最新实测与用户规则（此前轮次保留为历史证据）

- 会话归属只有一份BFF事实：Conversation的可空项目归属（公开project_id，BFF持久化project_ref）；移入/移出不复制消息，不新建关联实体，不启动Agent。前端项目列表和独立会话列表据同一事实刷新，网络恢复保护不得变成多余用户流程。
- Web正式A已本地提交21ad177，固定owner public7.1/5e119cd。Root clean HEAD+A+3真实Next adapter补片（tree d3acc0a）Node22 contract258/architecture50/lint/types0、2434pass0skip；完整check先因Root临时node_modules越root symlink导致build失败，独立clone依赖后Root86951单build自然exit0，产品配置/源码未改。mixed原63路径字节保持。B25path候选patch49b7仅抽取，crossscope未知结果及迟到确认对账P1未闭合，因此当前不提交/同步3310。
- Agent A3a首真实RED70pass/10fail→候选79/1 terminal错误分类→ee9cbc窄修80pass；QA强化0c15004后Root31333实际81pass8.19s，完整database69606实际292pass0skip34.32s，两临时库absent/sourcehashsame。两真实PG PID阻塞图与terminal exact replay全快照零写正控已有；完整工程44134已自然exit0：2178pass/390资源deselected、lock/frozen-sync/ruff280files/pyright/contract/build0；最后四D0同步后6645再build0，正式Agent九路径提交2a9491e。未接provider/运行caller/Billing/finalizer，不冒费用与用户聊天闭环。
- Root真实浏览器库存本轮仅原会话tab1；getTab控制15s timeout/kernel reset没有实际操作，未证明原tab新问题已恢复。原永久45606/46036保持live，不因观察超时重启。Root uv.lock f7e1与未交接owner变更保留。原70组11/6/14/38/1不变，完整goal active。

## R194 当前限定修复与真实失败

- 会话与项目仍只有BFF唯一绑定；Move不复制Conversation/Message/File，不新增“项目会话”实体。Root已亲验Web真实Next/Chromium同scope四旅程：97553为1pass/3fail（迟ACK不GET、503/in_progress无同key恢复），same oracle771964与a3321eb4/8605365d修复后62663为4pass/0fail、69选择外未运行，27.29s；独审W1 0P0/0P1。完整Web首93813 lint失败，窄修后8560仍2479pass/1fail：R192 oracle晚取baseline，build未执行；前移到Project navigation前后Root57706同生产5pass/0fail28.99s；最终Root6435完整2480pass/0fail/0skip161.43s、contract258/arch50/lint/types/build0；UI B未提交且原3310未启用，不把fixture GREEN称用户整链闭环。
- W2跨scope真实engine dispose丢冻结command/迟ACK仍全局P1；最小后继是页面内单槽非持久command恢复，不park完整engine，不创造绑定真源。verified主体复用现session probe→projectReadBoundary；actor/anonymous/logout/pagehide清理、双scope owner GET与storage失效尚待真实测试。
- Agent四D0正式main c3bf769：已批准现终态同cursor封存/严格head验证方向，无DDL/wire/provider/Billing变化；源码候选实施中、未验收。Root25837/80363为recipe/typed字段fixture错误，99556另expiry oracle错误，均保留；修正后21678真实4业务fail/2finalizer owned lock expiry/cancel控pass，4.19s，source已限三现文件授GREEN，86131原六case6pass4.02s，但Root＋独审发现sealed SQL投影未全对artifact、合法authorization_denied误拒两个P1；原writer补同integration测试，source冻结待真实负控，尚不放行。自有数据库已回收/source hash相同，原错误收据保留。
- IAB库存仅原tab1/app；getTab20秒超时kernel reset，未新增/操作标签。工具控制失败不是产品成功或失败证据。原45606/46036保持live，Root uv f7e1和未交接BFF/Billing修改保留。原70组11/6/14/38/1不变，完整goal active。

R194收尾：Webtmp Bf1b5/Cf439c35只有clean apply-check，源码完整门是mixed冻结树，不跨证据冒认；Root五QA文档保持同一台账，未新建计划中心/目标。所有本轮Root测试进程已终态，Agent新增two-P1 test writer仍具名执行，source冻结；Root不stage子仓gitlinks/uv.lock或未交接owner文件。

R194-A3b two-P1新增真实RED：Root88885自然exit1，10执行6pass/4fail，126选择外5.96s；三个schema合法投影漂移未拒绝、合法denied错误拒绝均实复现。test8ca77/source52add/61c/f7f冻结；manifest `T/kokoro-r194-agent-schema-hhshlagx/manifest.json` 自库absent/hashsame，catalog10校验0。原六正控继续通过不是新缺口通过；原writer仅补authorization SQL state与canonical bytes错配负控，source继续冻结、Root先验证再授GREEN。无永久进程/共享重置，完整目标及70组不变。

R194-A3b auth一致性负控Root72070真实RED：test76d1冻结，11执行6pass/5fail，126选择外6.54s；追加SQL CHECK合法但typed denied bytes不符的state被错误接受。manifest `T/kokoro-r194-agent-schema-ev_8g_gd/manifest.json` 自库absent/sourcehashsame。后继R194-A3b-P1-GREEN派原Agent唯一writer，仅现model/call_evidence.py与infrastructure/postgres_model_call_evidence.py；test76d1/run_leases f7f冻结；补strict frozen authorization与全sealed投影，精确denied状态映射。Root资源/Git/独审，未批准DDL/provider/Billing/新文件；交付前不称修复，所有Root资源句柄终态。
