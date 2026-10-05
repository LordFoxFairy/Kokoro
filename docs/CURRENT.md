# Kokoro 当前执行事实

核对：2026-10-04，R229。完整 Wave 0–7 goal 保持 active；研发与完整用户旅程尚未闭环。本文件只保留当前事实，旧 CURRENT 的 510 行全文逐字归档于 [progress.md](progress.md) 的“R228 CURRENT 原文归档”，不与本页当前结论并列。

## 1. 产品验收总览

现 [test-cases.md](test-cases.md) 70 组状态：**11通过 / 6失败 / 14待复测 / 38未验 / 1支付后置**。通过项包含限定工程/业务切片，不是11个完整页面、子仓库或完成百分比。系统/真实 owner/浏览器各层证据分别记录，不互相替代。

- 唯一当前 PRD：[kokoro-handbook/product/09-v2-prd.md](kokoro-handbook/product/09-v2-prd.md)。
- 原任务/owner/准入：[task.md](task.md)；代码入口：[CODEBASE_MAP.md](CODEBASE_MAP.md)。
- 实际失败、终态句柄、SHA与资源收据：[progress.md](progress.md)；不另建计划中心。

## 2. 仓库与运行组合

子仓的 tests 不迁入 Root；`scripts/tests/` 只覆盖 Root 治理脚本，`verification/` 承接跨仓行为验收，不创建应用测试总目录。

Root和11物理子仓现场均只有本地main，远端本轮未核验。Root仍有5个gitlink差异及受保护uv.lock，Web/BFF与部分owner文档含未提交修改；整体工作树非clean。不得覆盖或混提这些修改。

|物理仓库|当前本地HEAD|已确认的有限交付 / 尚未闭环|
|---|---|---|
|apps/kokoro-app|ce40cecc|有19个mixed路径；R229完整OIDC系统78pass，当前用户页面/CRUD/Settings与正式模型费用链未全验|
|apps/kokoro-bff|7289b3a4|有限Message准入、事务/故障与182真实PG/Redis已有证据；20个protected路径保留，组合用户链未全验|
|apps/kokoro-agent|f3050fcc|System3.0消费、单completion/输出界和客户端生命周期已提交；原始usage观察四D0独审通过、待真实SDK tests-first，可信输入界/Admission/收费Run仍OPEN|
|apps/kokoro-iam|c9a9872c|登录/managed first-party provisioning局部已验；当前组合登录回调、退出/撤权/多窗口整旅程待验|
|apps/kokoro-system|955bd587|模型目录3.0与技术执行参数切片已提交；当前组合实际调用/费用链未闭环|
|apps/kokoro-billing|8f091d40|rate-only canonical/pure codec/module-private publication已本地提交；仅五旧mixed文档dirty，事务内rate选择尚有两项事务设计P1；policy/quote/Admission/预占结算释放/流水UI仍OPEN|
|apps/kokoro-capability|da813ed4|Skills/MCP owner局部组件有证据；物理名尚非kokoro-platform，cutover及实际消费者整链未验|
|apps/kokoro-storage|14f2bc9c|owner局部门；真实浏览器上传/扫描/下载/作品/项目释放整链待验|
|apps/kokoro-scheduler|e8dca489|owner局部门；独立任务页面CRUD→触发→Agent结果整链待验|
|apps/kokoro-mori|ca76c2e1|本轮未修改或完整复验，不作为新完成项|
|libs/kokoro-web-shared|0c4e87ac|本轮未修改或完整复验，消费方UI组合仍待验|

原3310 Web PID46036仍运行受管旧组合副本，未自动消费这些新提交/候选。本轮未push、更新gitlink或重启用户服务。Billing/Web自有验收句柄6274、46388、74057、95636、67616均终态；无重复PostgreSQL/Redis、共享reset、实际资金或provider调用。

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

## 4. 本轮新增证据与范围

**Billing：**本地main `8f091d40bd3695144861e88159e88d9d767112c1`，20明确路径。Root10静态/生成/契约步骤exit0；9文件真实PG107pass（含publication14），39辅助文件1361pass；测试标题every→representative只改覆盖口径、原断言保持，Root另231pass。真实audit UUID与NUMERIC78读取两P1已修复。publication与当前D0独审0P0/P1/P2。

15 non-doc Git objects与冻结SHA一致；5docs只接RootR228+已审R227/R223+原HEAD，其他protected mixed正文逐字留在工作树。收据 `/tmp/r228-billing-commit-receipt.json`；最终系统证据 `/var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-r227-billing-final-lrk72u3z/manifest.json`。这些不证明HTTP/真实COMMIT网络ACK、policy、Admission、结算或用户收费通过。

**Web R229：**冻结系统测试504ca8cf；Root完整 **78pass / 0fail / 0skip，116.022秒**。真实隔离Next/Chromium/Redis，IAM/BFF为受控peer。新增storage-free冷deep-link首次snapshot真实503→错误界面可见、loading消失→人工Retry恢复同会话→reload仍同会话，零会话创建POST；仅测试新增91行，未改生产实现。原77例全部保留，独审0P0/P1/P2，source与Redis key集合保持。证据 `/var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-r229-web-full-8zwiqgvn/manifest.json`。

旧3310副本已经有10秒session fetch+JSON Abort；“旧副本缺超时”不是已证根因。原用户持续加载仍未复现定位，上述冷503测试也不能冒充修复。当前IAB唯一标签定向读取focus超时未取得DOM；已请用户仅重开标签，未盲刷新、另开窗口或重启服务。匿名有界HTTP /app307、session200 authenticated=false、login302仅证匿名入口，不是登录用户旅程。

## 5. 当前治理失败（未清零）

Root本轮standard真实153规则违反、topology5个gitlink差异。scripts全门1719pass/2fail/3skip：checkpoint冻结证据的gitlink漂移仍开放；CURRENT精简遗漏测试归属说明已补回，相关7例复验通过，但未重跑完整scripts。原失败与日志见progress R228，不放宽门禁、改测试或偷改组合指针换绿。

## 6. 当前推进与真实外部待决

1. Root已接收并提交Billing rate-only切片；下一依赖为policy/selection/quote与Agent正式artifact/Admission，不能用旧quantity1或免费fallback凑闭环。
2. 原Agent owner四现D0 raw usage观察设计已按独审回填为自有不可变缓冲区两遍有界解码；最终独审0P0/P1/P2，设计门通过，后继需另授真实SDK tests-first，source/tests/contract/schema/lock冻结；有限预算、单响应/调用作用域、EOF/取消/冲突、隐私与digest材料须Root审查后tests-first实做。SDK missing→0不是实际known_zero。
3. 原页面加载/正规登录、会话项目CRUD、Settings、独立能力验收可按原卡独立并行；同仓单writer，Root独占集成/资源/Git。
4. 真实采购费率/币种与现金→Credit换算值或现配置位置仍待用户明确。已确认倍率7/5=1.4成本加价40%，非利润9.4倍；失败/取消仅结算已核实实际消耗，释放可确认未使用预占。基础代码可继续，不捏造应用价格/充值/免费。
5. 支付渠道最后；部署运维隔离、生产角色与环境配置不抢研发主线。
