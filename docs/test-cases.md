# Kokoro 测试任务总台账

状态：当前测试计划，2026-10-02 / R121实际复验；复用既有文件，不建立第二开发计划中心。

- 本页唯一维护**测试任务、验收标准和最新结果**；[task.md](task.md)维护派工/依赖，[progress.md](progress.md)保存实际运行证据，[CURRENT.md](CURRENT.md)说明当前组合。
- 范围：批准Wave0–7全部研发能力与九owner；其他前端、历史Session/Mongo、部署多角色/网络策略不在本轮。支付渠道后置，不删除目标。
- 本表每行是测试任务组，不是一个自动化断言；各owner用例留本仓。未验不等于没有代码，历史通过不等于当前组合通过。
- 状态：通过 / 失败（最近执行） / 执行中 / 待复测（有历史证据或版本变更） / 未验 / 阻塞（明确决策缺失） / 后置。
- 完成条件：绑定commit或冻结hash、实命令/环境、pass/fail/skip、证据和清理；本行必需分支被跳过则本行不得通过；明确拆至其他测试ID的资源分支仍记未验，不影响限定纯门，但绝不计为资源通过。相关source/contract/pin变更后移回待复测。修复提交不直接关测试，Root复测成功才关闭。
- 当前状态以本页R121/R120实跑、R119/R118摘要、下方测试矩阵与具名证据为准；最新代码变化回待复测。历史发布组合cc7bfb78/Webddd38c5的E53正规登录与严格两轮聊天保留，不代表当前七标签页或所有用户能力已验证；E49具体安装缺陷已E76复验关闭，T-Q03整体门仍未验收。

## 当前测试看板（测试任务，不是开发任务）

|状态|测试组数|
|---|---:|
|已通过（仅记录版本和范围）|13|
|最新执行失败|0|
|待复测|13|
|尚未完整验证|41|
|待业务决策|2|
|支付后置|1|
|合计|70|

**已通过13组：** T-Q01 Web工程门、T-Q02 BFF工程门、T-Q04 IAM工程门、T-Q05 System工程门、T-Q08 Storage工程门、T-Q11测试工具诊断、T-L01登录正向、T-C01后端会话过滤、T-C06两轮真实模型聊天、T-C11前端流连接生命周期、T-K01连接器不显示假成功、T-B01定价纯规则、T-R01具名测试资源隔离。登录/聊天是E53记录的历史发布组合和本地模型，不代表当前全部能力或用户提供的模型网关通过。

**有问题且尚未关闭：** E75整体标准扫描152条报告待逐条裁决/修复；Todo正式消费、Skill运行phase契约及安全过程硬刷新存在已记录缺口；当前完整浏览器旅程未验。最新执行失败为0只是70组当前状态计数，绝不是“零问题”。T-Q03 Agent纯测/安装切片通过，整组仍待复测。

**计划完整度：** 70组覆盖目录已建立；全部逐用例步骤尚未展开完成。每组须沿原ID展开子用例：前置数据、操作、预期、实际结果、证据/版本、缺陷、修复提交及Root复测。先覆盖正向，再补权限/错误、重复/并发、取消/断线/刷新/恢复；必需分支未验或跳过不得整组通过。现有T-C09详细子用例作为记录方式，不新增第二测试计划中心。

**待决策：** T-C05项目移动/归档/删除的关联生命周期；T-B07失败/取消/部分输出/未知成本的收费资格。接续优先正式Agent→BFF→Web消费与当前登录/聊天/刷新，再验证项目和独立会话、Home/输入框、Skills/MCP/过程交互、任务/作品，最后正式积分链与支付后置项。

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

本页70组是**覆盖目录**，不是已经写完或跑完的完整用例集。已有T-C09详细子项；其余未展开组仍需在执行前补齐步骤、预期、正负例和恢复场景，不能将目录齐全称为测试计划全部完成。沿现组ID增加子编号，不另建计划中心；owner自动测试继续留在各自仓。

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

共 **70组：通过12、失败1、执行中0、待复测13、未验41、阻塞2、后置1**。通过仅限具名范围/版本；本次未重跑全部业务测试，整体产品尚未闭环。

## 本次已完成与未完成（可直接巡检）

- **通过12组**：T-Q01/Q02/Q04/Q05/Q11、T-L01、T-C01/C06/C11、T-K01、T-B01、T-R01。T-Q05为E74当前候选119纯测与Root十门/独立审通过；其他各行原具名证据/范围不扩大，登录/聊天E53仍仅既有发布组合及本地qwen3:8b，不含用户网关、正式收费或全部Agent/UI能力。
- **失败1组**：T-Q03，E87生产自建S3客户端终态未释放已Root复现；修复尚未实施。原E49缺资源已E76关闭、E78缺示例已E80关闭、E79 fixture回收已E82关闭；失败历史仍在，但未验分支不勾通过。整体规范检查E75仍失败，归T-Q10待复测追踪。
- **执行中0组**：具名Root测试命令终态，原WIN03已交付并idle；候选等待复测不计整组测试执行中。
- **待复测13组**：T-Q06–10、T-L02–05、T-F01–02、T-K02–03。Agent剩余必需分支及其他历史/版本变化均按当前组合重验。
- **未验41组**：项目与独立会话交互、队列/恢复完整分支、独立任务、完整作品、Skill/MCP实际选择调用、Todo/工具/审批展示、正式积分、Home/输入框/布局、全部owner组合等，逐行见矩阵；局部PG/HTTP/纯测不替整条用户路径。
- **阻塞2组**：T-C05项目移动/归档/删除生命周期、T-B07失败/部分输出/未知成本收费规则；T-B08支付后置。

**下一测试批次**：E80配置及E82 fixture已验，不反复重跑已关闭定点；E84–86安装正负向及限定installed DDL已验；先处理E87资源释放缺陷与测试覆盖，再推进installed HTTP/资源门及正式owner组合，随后逐ID验证项目/独立会话与任务、Home/输入框、Skills/MCP/Todo/HITL、正式积分。支付最后。

## 范围与记录方式

70组覆盖：工程/契约12、登录权限5、会话与项目11、独立定时任务5、文件作品5、Skills/MCP7、Agent过程6、积分支付8、界面4、可靠性安全4、System2、Platform身份cutover1。

每组下的正例、负例、异常、恢复和权限分支按该行验收条件执行；70是测试任务组数量，不是全部自动化用例数量，也不代表已有70组实现。开发task不能代替本台账；发现缺陷→关联原测试ID与开发任务→修复版本→Root复测→全部必需分支通过后才关闭。失败历史保留，版本变化须复测，测试本身出错也单独分类。

### 每组执行记录与关闭规则

同一ID下逐步补齐正例、负例、异常、恢复、权限用例，不另建计划中心。每次执行记录：测试ID/分支、前置条件与测试账号角色、操作步骤、预期结果、实际结果、执行时间、commit或冻结hash、环境/命令、pass/fail/skip、脱敏证据、缺陷/修复版本、回收结果和复测结论。未展开或未执行的必需分支保持待验，不能仅凭70行目录称“完整测试已完成”。

缺陷发现可来自测试、浏览器或代码审查：审查发现但未复现须标注“待RED”，不改写成已有测试失败；同一测试的修复候选保持待复测，Root重跑并完成审查后才验收。版本变更使相关通过组回待复测。测试计划随着新增真实分支扩充，但保留稳定ID与失败历史。

## 当前已发现问题（不另算任务完成数）

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

| ID | Owner/层级 | 测什么与通过条件 | 状态 | 最新证据/未完成原因与下一动作 |
|---|---|---|---|---|
| T-Q01 | Web | 本仓format/lint/types/unit/contract/architecture/build；跳过逐项说明 | 通过 | E41：Webddd38c5正式发布，Root84433 exit0，249contract/50architecture/2328tests及lint/typecheck/build通过，独立0、八hash匹配。format脚本N/A；Root新组合386已验且fa4525e4已发布，真实浏览器另未验，T-U01浏览器另行未验。E37真实RED历史保留 |
| T-Q02 | BFF | 本仓format/lint/types/unit/contract/architecture/build；跳过逐项说明 | 通过 | E01：仅BFF离线纯门 |
| T-Q03 | Agent | uv锁与frozen依赖/Ruff/Pyright/pytest/wheel；HTTP contract与架构；skip说明 | 待复测 | E95当前Root自有1960纯node1960pass/0fail/0skip、七静态0/独立三路径0，E93 inline-ignore失败关闭；E96新源码wheel/sdist/full115 runtime安装十步0、origin/CLI/371源保持/回收通过，新artifact四布局64负向/219步骤已终态通过；仅此生命周期分支，不扩大至构造/排空/取消或真实S3。 E80配置11项/四门通过、dbaf4f9本地提交，E82 fixture Root真实2 RED→17file/172local GREEN、forced_close0/独立0、2653bcc本地提交；E83当前pure1937pass/0skip/615warning保留。E49具体缺OpenAPI已E76四安装正向布局关闭。E84当前重建source-wheel实际十步安装门通过；E85 installed DDL单venv首次/拒重入/所列目录与六漂移/精确回收通过。E86四布局64负例/219步骤、actual origin/恢复/零远端网络已Root通过；installed HTTP、其他DDL布局/漂移、真实S3/Docker/production close、HTTP5候选发布及消费者未验；其他源/contract/锁候选未混提交，不称完整Agent闭环 |
| T-Q04 | IAM | 本仓format/lint/types/unit/contract/architecture/build；跳过逐项说明 | 通过 | E14：Root本次verify938通过；仅该纯门，host51另记有限资源证据，非全部IAM integration/登录 |
| T-Q05 | System | 本仓format/lint/types/unit/contract/architecture/build；跳过逐项说明 | 通过 | E74当前候选source da4675b9/test45bd5286/helper efd2f061，Root99279十纯门exit0，9files119pass/0fail/0skip，197hash保持/owned进程组终态/OS禁网，独立审0/0/0。E72先12fail/2control，连接URL正控缺口已补强并Root复现；只未发布候选纯门，真实PG/Redis/freshschema/runtime/provider/image另未验；E77单owner真实PG fresh 23断言/22表与精确回收已验，Redis/业务HTTP及其他owner组合仍未验 |
| T-Q06 | Billing | 本仓format/lint/types/unit/contract/architecture/build；跳过逐项说明 | 待复测 | 历史门不能证明新组合；按owner ACCEPTANCE重跑 |
| T-Q07 | Platform | 本仓format/lint/types/unit/contract/architecture/build；跳过逐项说明 | 待复测 | 历史门不能证明新组合；按owner ACCEPTANCE重跑 |
| T-Q08 | Storage | 本仓format/lint/types/unit/contract/architecture/build；跳过逐项说明 | 通过 | E94 Root当前74c4b59默认491pass/156PG skip/0fail，format/lint/types/build与contract/Prisma生成+正规normalize0；280源/17generated恢复原bytes/clean，owned资源终态正常；独立终审7d8eaee1为0P0/0P1。限定工程门；156PG明确拆至T-Q12、文件真实资源T-F01–05仍未验，不称完整Storage闭环 |
| T-Q09 | Scheduler | gofmt/vet/test/build；OpenAPI/event protocol/schema/架构；skip说明 | 待复测 | 历史门不能证明新组合；按owner ACCEPTANCE重跑 |
| T-Q10 | Root | 精确gitlink、main-only、发布contract/version/digest/client drift、fresh clone | 待复测 | E12原IAM缺提交分支已由E14发布及同fresh目录真实初始化0关闭，E13消费RED已由E15收口；新Root组合及完整fresh/主分支检查仍待验，不计整行通过；E75本轮topology exit0，但补充整体标准检查exit1/152规则报告，须Root逐条裁决及owner修复/复测 |
| T-Q11 | Root | 发送失败诊断有界/脱敏、两轮归属、失败仍非零退出、原硬断言不变 | 通过 | E51：Root93085实际9fail/583pass，37740修复后592pass/13.34s及Nodecheck0、独立0；本Run合法UI文本前零snapshot，terminal/observer/deadline封闭；原所有硬断言与控制保留，session_rate_limited闭集补齐。仅当前冻结driver b83525de/test fee45056测试工具门，不是T-C06真实用户旅程通过 |
| T-Q12 | 各数据owner | 同应用库独立schema fresh install/drift/拒重入/零跨owner SQL/失败回滚 | 未验 | E32仅Agent fresh7通过；E77 System单owner真实fresh23断言/22表/catalog/拒重入及精确临时库回收通过。E85新增Agent source-wheel installed CLI/目录/六漂移单owner门；全部数据owner同一应用库schema组合与零跨owner访问仍待验，不关闭整行 |
| T-L01 | IAM→Web→BFF | 真实IAM表单→授权→callback→HttpOnly session→/app；无中转/整页重试 | 通过 | E53：本轮fresh owner/member两账号真实IAM表单200/nativeconsent200+一次303提交/callback303/HttpOnly+Secure+Lax cookie/session200与app200；浏览器精确导航与单次计数验证无可见中转，独立终态0。仅正向入口；其他登录/权限负例另T-L02–05待复测 |
| T-L02 | IAM→Web→BFF | 错误密码/CSRF/state/nonce/PKCE/redirect篡改拒绝且无session | 待复测 | W1C/W1D历史隔离浏览器证据；新组合正式旅程未验 |
| T-L03 | IAM→Web→BFF | 刷新/到期/退出/退出后重登与后退；禁止过期签名URL无限重试 | 待复测 | W1C/W1D历史隔离浏览器证据；新组合正式旅程未验 |
| T-L04 | IAM→Web→BFF | 固定tenant准入、撤销/禁用、同tenant另一用户及跨tenant隔离 | 待复测 | W1C/W1D历史隔离浏览器证据；新组合正式旅程未验 |
| T-L05 | IAM→BFF→Web | 成员/邀请/角色权限与审计：读写、分页、重复命令、撤权即时失效；无管理员越权 | 待复测 | W1C-Team历史owner切片，当前完整用户权限矩阵待复测 |
| T-C01 | BFF | 独立/project/全集列表、tie keyset limit1/2、跨主体/租户/deleted、冲突400 | 通过 | E03：真实PG+生产HTTP，仅后端过滤切片 |
| T-C02 | Web→BFF | 新建独立/项目会话、URL/back/forward/刷新、草稿和消息不串scope | 未验 | 先Web固定BFF6，再真实浏览器 |
| T-C03 | Web→BFF | 重命名/删除等待ACK；延迟/503/切换scope不复活、不污染新页 | 未验 | R82已知delete fire-and-forget竞态 |
| T-C04 | BFF→Web | 显式分享/撤销；私有链接不冒充公开分享；另一用户不可读/控制 | 未验 | R82分享文案与真实权限不一致；正负例都需验 |
| T-C05 | BFF→Web | 移动/归档/删除项目时会话、活动Run、任务及作品的生命周期 | 阻塞 | 产品删除/移动规则与正式API未裁决；不猜级联行为 |
| T-C06 | Root六owner | 正式登录后两轮真实模型聊天：两POST/四Message/全文/刷新/作品hash/他人404 | 通过 | E53：Rootcc7bfb78六owner fresh/clean/发布hash，原58200实际exit0；两POST202/四completed、真实模型全文SHA、首轮保留、active非空文本硬刷新+同watermark续流、真实作品下载hash/刷新一卡/另一用户三404；五owned残留0/子terminal/桶删除404，独立终态0。实际模型为本地Ollama qwen3:8b，不含Billing/Agent5候选或用户OpenAI网关；E48失败历史保留 |
| T-C07 | BFF→Agent | 同会话FIFO/同key重放/双tab同时提交；一活动head，无重复执行 | 未验 | 队列正常也须竞争负例；跨会话允许并行 |
| T-C08 | Web→BFF→Agent | Stop/steer/取消/重复控制；ACK不冒充terminal，输入和队列正确收口 | 未验 | 按现owner契约；资源验收不能用UI按钮存在替代 |
| T-C09 | BFF→Web | 活动/终态刷新：同事务Message/执行head/过程与event_watermark一致 | 未验 | E53已证明活动硬刷新与同watermark续流；R117只读审指出R43/R57两race不能拼成四事实同快照实证。R118详细子项见本页：E91 Root新组合例1/1、完整projection39/39且0skip，限定后端四事实RR/replay证据已验收，BFF02276b6本地提交；浏览器及全分支仍待验，不关闭本行 |
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
| T-A01 | Agent→BFF→Web | 简单聊天只回复；复杂任务Todo完整表更新、不被子Agent覆盖 | 未验 | E35 Root真实PG65pass/独立0（原59+新增完整/空Todo、并发lostACK、漂移、围栏/expiry/terminal、live失败耐受6项）；owned库回收0；E47 HTTP完整36通过，新Todo实际PG→HTTP/分页/replay/身份隔离成立；BFF/Web安全过程呈现与复杂任务策略未验，不关闭整行 |
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
| T-U01 | Web | Home提示只填草稿、零自动POST/计费；真实模型/套餐/能力，无错误营销卡 | 未验 | E33局部发布/E37语义11真实RED/E41完整纯门接受/E42已发布ddd38c5，网站/More/零POST正控保护；Root新组合fa4525e4已发布；完整Home真实浏览器未验 |
| T-U02 | Web | Composer多行/中文输入法/Enter与Shift+Enter/附件/发送禁用与Stop；无内嵌方框 | 未验 | 真实浏览器+截图/axe/视觉；UI纯测或借用shadcn不替代验收 |
| T-U03 | Web | 桌面与窄屏对话/侧栏/项目/作品布局，长文本/代码/表格/错误均可用 | 未验 | 真实浏览器+截图/axe/视觉；UI纯测或借用shadcn不替代验收 |
| T-U04 | Web | 键盘/focus-visible/axe/reduced-motion、全部loading/empty/error/partial状态与视觉/bundle门 | 未验 | 真实浏览器+截图/axe/视觉；UI纯测或借用shadcn不替代验收 |
| T-R01 | Root | 本次BFF隔离测试临时库精确创建/删除、无共享PG/Redis reset | 通过 | E03：removed=true/cleanup=[]；仅该run，不代表全进程治理 |
| T-R02 | 各owner→Root | 实际进程启动/health/ready/超时/取消/graceful shutdown/worker drain/故障恢复 | 未验 | E88现System19真实资源/HTTP切片通过；Agent旧close失败已在E93/E95限定纯生命周期回归关闭，当前installed HTTP/真实S3/Docker/SIGTERM与全owner恢复仍未验，不把纯测修复当资源门通过。 原句柄追踪、不重复启动、不把观察超时当进程已停 |
| T-R03 | Root/各owner | 权限矩阵/输入边界/敏感日志/依赖secret/source扫描/跨owner禁止访问 | 未验 | 同tenant不同人+跨tenant正负例；报告不含凭据 |
| T-R04 | Root | 全owner当前门+组合真实E2E+隔离fixture backup/restore（持久事实/幂等/未决outbox恢复）+可追溯release smoke/image SHA清单 | 未验 | Wave7最终研发验收；SLO目标不冒充压测，不扩展部署运维 |
| T-S01 | System→IAM/BFF | Site/Host/Workspace/Runtime/Policy具名身份与生命周期；disabled/unknown/expired拒绝、secret零泄漏 | 未验 | E88现System单仓lifecycle19真实通过，只启动/HTTP deadline/schema资源切片；完整业务/消费者待验。 owner HTTP/PG→消费者，不建任意配置桶 |
| T-S02 | System→Agent/BFF | 模型目录/选择/路由revision与digest；实际gateway/credential；重试故障不静默换未授权模型 | 未验 | 技术配置不等于实际调用证明；消费固定owner artifact |
| T-G01 | Platform→BFF/Agent→Root | capability到platform身份/Proto/remote/path/env/DB/Redis一次cutover；旧alias/fallback删除 | 未验 | Wave3正式验收，现物理仍kokoro-capability，不冒称已改名 |

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

1. T-Q03：E80配置/E82 fixture/E83 pure与E84–86安装正负向/限定installed DDL已验；E87新增生产终态close RED已Root复现，先补有效控制与生命周期分支、修复复测，再推进HTTP、剩余资源及HTTP5发布消费者，不用重跑已关闭定点代替推进。
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
