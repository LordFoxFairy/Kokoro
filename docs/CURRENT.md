## AGENT-FAILURE-3.0 与 Run 首事件已完成 owner 验收（2026-09-30）

Root 来源集成 commit `e2ef2866fd9a3de9b1b1ae2cef107bb9282d8fdc` 后，正式 IAM relay、repository topology、
指定 `w1e-iam07-bff-pin` checkpoint 均 actual PASS/exit0，session62704 已消费；
证据 `/tmp/kokoro-agent3-root-{relay,topology,checkpoint}-final.json`。只提交本片5项，
Agent/BFF/Web子仓clean；Billing五docs与Root uv.lock仍未提交，不称全体clean。本段仅追加验收记录。

Agent main `da056b0103cced10188cdc1f5baef841d8333889` 已由 Root 按冻结 29 文件精确提交、子仓 clean。
独立最终 review P0/P1/P2=0/0/0、29/29 hash 吻合；Root fresh 完整离线门 actual exit0：
Ruff251/Pyright0/generator/contract/lock/frozen sync、1518 passed/6既有skip/174deselect/364warnings（58.74s）、wheel/sdist。
日志 `/tmp/kokoro-agent-evidence-cursor-root-final-gates.log`。
Root 完整真实 PG/Redis/HTTP owner acceptance 22 passed/100warnings/7.31s、exit0、无跳过，
包含安全失败 true/false、index0 terminal replay、tenant/fence；System/model 为 test doubles，不是外部推理 E2E。
自有 fixture 数据库和 Redis15 残留均0/cleanup_errors[]，不触活跃 DB10/共享schema。
证据 `/tmp/kokoro-agent-evidence-cursor-root-real-acceptance-all{.log,-result.json}`。
旧 after_seq0 漏 index0 及此前 driver 解析失败记录为历史，未伪造 START、重排索引或放宽断言。

Root 仅更新当前 Agent owner/source 指针与 commit blob 摘要；BFF 的实际 2.0 vendor/generated 不改写成3.0，
库存维持3active/13broken。BFF 精确失败持久化及公开契约、Web严格消费、受管服务协调发布仍未完成；
现3310组仍原Agent58b/BFF15e组合，没有热加载半套契约。Billing五docs与Root uv.lock保留。
后续在清除本片新增两项粒度问题后进入 BFF 文档门及严格消费，不以 owner acceptance 代替整个产品闭环。

Root 冻结来源后完整 `python3 -m pytest -q scripts/tests` 实测1103 passed/3既有skip/455 subtests，
123.78s exit0，日志 `/tmp/kokoro-agent3-root-final-tests.log`；先前变化中定点131pass只作历史，未用作最终放行。
Root fresh全仓标准门 actual FAIL：139 violations/0 unverified，比既有137新增Agent
`execution/events.py`806行与`execution_proof_contract.py`804行两项800行粒度违例。
因此本片仅行为/契约来源验收，不宣称整个Agent工程标准清零。先按变化原因清这两项再BFF发布；
不得压空行、挤tuple或豁免阈值冒充修复，独立只读后继设计审查已派发。
原标准输出 `/tmp/kokoro-agent3-root-standard-first.log`（text），首次摘要读取误当JSON保留为调用错误；
显式JSON格式复验 `/tmp/kokoro-agent3-root-standard.json`。Billing/Root uv.lock未暂存。

本轮再验正式 IAB：聚焦 textarea border0/box-shadow none/透明outline；composer x282/768px，无横向溢出。
原问题重复提问仍真实可见，不隐藏数据冒充布局修好；截图 `/tmp/kokoro-chat-layout-current-verified.jpg`。
只读追踪确认当前终态“重试”调用普通createMessage新key，BFF创建第二user/assistant/run；不是CSS重复。
目标采用BFF正式同user重试command，复用原user、冻结输入/选项，只创建新assistant/run/outbox；
先完成failure profile再明确server retryable=true准入，不让Web猜失败文案。未知POST结果恢复继续原key，
与终态重试分开；原重复数据不隐藏、删除或合并，不建立兼容分支。命令路径与机器契约由BFF文档门确定。

## WEB-READING-AXIS-ALLWIDTH 已验收（2026-09-30）

Web main `30545c55625fb257ac17ce2199e8fa1000f3ecae` 已由Root按五文件精确提交，子仓clean；只改现AppFrame阅读轨、两测试及两文档。Root独立Node22完整check实际exit0（contract109/architecture37/1800 tests/lint/typecheck/build），日志 `/tmp/kokoro-web-reading-axis-root-final-check.log`，独立最终审查0/0/0及5/5冻结hash核对。

正式3310原生IAB十宽度/侧栏真实矩阵全过：390/640漂移0.40625px，其余641/700/767/768/800/960/961/1280均0、无横向溢出；800/960收起，961/1280展开。焦点内框仍透明、圆角shell可键盘定位，全文数组未变。只同步自有runtime一个CSS、不重启、不调用模型或计费；窗口/侧栏恢复原状。截图 `/tmp/kokoro-web-reading-axis-desktop-final.jpg`、`/tmp/kokoro-web-reading-axis-mobile-final.jpg`，数据 `/tmp/kokoro-web-reading-axis-real-matrix-final.json`。

保留两类真实失败：首候选纯1800pass但960px漂移54px，追加RED后修form的48rem上限；返修worker完整首跑既有HTTP5s超时1799/1800，隔离3/3与完整重跑1800、Root独立全门均通过。没有放宽断言或timeout。新增Preview Playwright几何源码未执行，不冒称自动浏览器全套PASS。重复user、空/失败状态、sidebar列表加载错误及query-only深链仍开放；本片不是所有能力闭环。

Root本片38个Web来源指针与34个commit blob路径重新核对，digest没有变化，现有broken依赖不改绿。Root相关三文件治理测试54pass（39.18s，`/tmp/kokoro-web-reading-axis-root-integration-tests.log`）。Root集成commit `2b9d6379` 后，strict IAM relay、repository topology、指定w1e-iam07-bff-pin checkpoint三门均actual PASS/exit0，session32068已消费；证据 `/tmp/kokoro-web-reading-axis-root-{relay,topology,checkpoint}.json`。独立Root最终0/0/0；本段为验收记录补充，代码/gitlink/库存未再变。task/progress保留未完成后端与Agent/Billing/uv.lock在途状态。

## 历史用户页面复验（Web 7c2b4d7，已由30545c55后继）

以下为修复前Web `7c2b4d700c8a4399fae68012c1db7423d790abd7` 的历史证据：当时重新操作正式3310原生IAB，而非只检查源码。桌面 textarea 为透明 outline、无内层 box-shadow；form/content 同 x282、768px。390px 窄屏 form x16/358px、content x15.59/358.81px，无横向溢出。Shift+Enter 保留两行并增高至51px，没有提交消息；清空测试草稿、恢复默认窗口，原 article 全文数组严格不变。截图 `/tmp/kokoro-chat-layout-current-desktop.jpg`、`/tmp/kokoro-chat-layout-current-mobile.jpg`；新 Node22 定点 Composer/AppFrame/architecture **164 passed / 6 files / 7.22s / exit0**，日志 `/tmp/kokoro-chat-layout-current-tests.log`。本轮未重跑完整 build/Playwright，也未调用模型或充值。

仍可见重复提问与历史空失败轮次；不是以 CSS 隐藏或去重解决的布局事实。深链、重试身份及精确安全失败的 Agent→BFF→Web 持久消费仍待闭环，不称完整产品完成。Agent cursor 已由唯一 writer 实现并冻结、独立审查0/0/0；Root纯门1518pass与build已过，真实PG/Redis/HTTP复验尚未执行成功，未发布切换当前受管2.0组合。

## WEB-COMPOSER-VISUAL-ALIGN 已验收（2026-09-30）

Web main `7c2b4d700c8a4399fae68012c1db7423d790abd7` 六文件已提交；Root本片已固定该gitlink与38个consumer证据指针，原契约摘要无变化。内部直角框移除、键盘token焦点在圆角shell、thread与composer统一48rem、手机viewport不误用桌面32px。Root Node22.22.2 `pnpm check` exit0（contract109/architecture37/全量1800/lint/typecheck/build）；日志 `/tmp/kokoro-web-composer-align-root-node22-check.log`。独立只读返修后0/0/0；单独prettier六文件检查FAIL、未全仓格式化，不称全格式门通过。

真实 IAB：桌面两轴x282/w768，390px content x15.59/w358.81与form x16/w358、无横向溢出，欢迎/线程聚焦均无可见内框；多行38→100→38，Shift+Enter不提交，Tab可达。owned runtime仅两CSS同步并核对旧baseline，无重启/新模型调用。原消息全文数组在恢复原conversation并reload后与修前严格相等。截图 `/tmp/kokoro-composer-desktop-after.jpg`、`/tmp/kokoro-composer-mobile-after.jpg`、`/tmp/kokoro-composer-welcome-after.jpg`。

新发现同pathname query-only导航漏接，new conversation后URL可能被stale eviction清空；显式goto+reload已重新恢复原conversation，非owner删除或丢数据。原Web负责人已只读定位，后继需deferred snapshot RED与严格失败清理断言，暂未授写。重复user/空failed assistant、完整failure契约与整个Wave0–7仍未闭环；未隐藏消息冒充布局完成。Agent cursor docs/tests已冻结RED，源码未授写。保留任务外Agent/Billing/Root uv.lock变更。

# Root 当前组合

**Agent当前来源（2026-09-30）：** 已验收提交 `da056b0103cced10188cdc1f5baef841d8333889`，完整22例真实owner HTTP acceptance与Root1518纯门均通过，详见顶部。此前safe failure两例因Run初始cursor漏index0失败的记录为历史；Run-only -1修复保留Chat0、索引与fence。BFF/Web未切新版，运行组仍2.0，重复提问语义未完成。

**BFF已验收组合（Root `7c13378e3e752b72c170cfdf3629cca743db5b81`，Web新片另见下段）：** BFF `15e07fa44670bc13705ce3f6f700e73afcb72ccc` 已验收、clean并集成。Root提交后strict relay/checkpoint/topology均独立exit0；完整 `scripts/tests` **1103 passed / 3 native依赖skip / 455 subtests**，108.74秒。新全仓标准门实际exit1，仍137违例/0 unverified；main-only实际exit1，主仓和11子仓本地/远端均只有main，但Billing五docs候选及任务外Root `uv.lock` 未提交，不称全体clean。此前BFF pure506pass1skip、fresh install/target8/full47真实owner integration通过及fixture失败历史保留；来源库存仍3active/13broken。


**Web最新owner验收（2026-09-30）：** `5058ae2c400dd8be1964bba5df03fd7ce5b52133` 已由Root精确提交八文件，子仓clean。独立最终review0/0/0、8/8冻结hash一致；Root显式Node22.22.2完整 `pnpm check` exit0：contract109、architecture37、lint/typecheck、162文件1799tests、build；隔离3387 Web治理Playwright11pass/1既定mobile rail skip（8.3s），不是真实IAM/模型E2E。首Root check误用Node24，保留原日志而不当Node22验收；worker首typecheck与非pending pause RED缺陷已严格修复。仅恢复owner snapshot绝对尾failed assistant且无active_run/未决pause的通用failed/error=null，不自动重跑、无新contract/SQL/兼容层。Root组合库存38个Web来源指针重钉，34路径raw digest原bytes，3active/13broken不变；Root集成`1e7b721b7b725166570da844ec8b3fee0e7b634f`后strict relay/checkpoint/topology分别actual0；完整Root1103pass/3native依赖skip/455subtests（119.07s），均实际终止。


**本轮原生窄闭环：** Root只将自有受管Web复制处hydration.ts从经bytes确认的840更新为accepted5058，其他服务/权限/登录/配置/进程不变。原IABtab3焦点超时，新同browser3 tab5正常/app同会话；真实失败generic提示与retry在reload后保持。一次手动retry得到真实中文追问回答和END标记，Stop消失，terminal reload前后3article全文数组一致。新发现刷新后同追问用户泡泡exact count2；retry当前按新turn提交的持久语义仍须BFF/Web只读审查，不称完整retry产品PASS。精确failure合同、流式中途reload、全部能力/计费仍未闭环。Agent四文档冻结已通过独立0/0/0及Root逐hash/SQL原bytes核对；当前2.0 checker实际exit0、四tests baseline101pass，仅作为现态证据。原owner已获四tests-only RED，机器/source仍2.0/runtime58，未发布3.0。

**当前运行与原生浏览器：** 唯一受管组session29394/launcher65119已正常启动3310，workspace `/Users/nako/WebstormProjects/github/thefoxfairy/kokoro-local-login-xm_q35q2`，启动时加载固定Web840/BFF15e/Agent58b/Systemc0a来源（Web后继仅hydration受管copy更新见上文），用户指定gpt-5.6-luna私有profile；空Skills、Storage未配置。新原生IAB tab3走正式 `/login`，账号提交通过。经用户明确同意首次权限，原签名过期后重新进入同范围新签名并完成consent/callback，已实际回到 `/app`。原生UI首消息得到30条建议及END标记，终态Stop消失；刷新前后回答全文453个JS字符口径（string.length）一致、article唯一。这仅证明新登录/真实回答/终态刷新子门，未捕获流式中途刷新，历史terminal DOM失败不改为PASS。同会话追问实际失败：曾显示“空间配置有误”/Agent run failed，后续状态观察中失败卡与重试入口消失，仅留下用户消息；续问及失败持久展示门FAIL。同期System日志有unknown与resolve error，但未取得同Run身份关联，不能确认本次根因。原生IAB访问正式同源snapshot被浏览器ERR_BLOCKED_BY_CLIENT拒绝，未换通道绕过。全部能力、正式积分链仍未闭环。下文较早运行停止/候选记录为历史，不是当前派工。

**历史候选复验（BFF activeRun，Root604dc12f）：** 12文件冻结hash核对，独立最终源码审查0/0/0、无infra聚焦20pass；Root Node22 format/lint/typecheck/contract191/architecture27/test506pass1skip/build全部exit0，日志`/tmp/kokoro-bff-active-run-root-final-gates.log`。真实自有PG首次GREEN尝试为7pass/1fail/0skip（`/tmp/kokoro-bff-active-run-real-pg-green.log`）：newer-run终态因fixture只有consumer registration、缺正常ChatTurn assistant/dispatch绑定而触发`AGUI_ASSISTANT_BINDING_MISSING`。未放宽生产guard，原owner仅修fixture和CURRENT；自有库/新增库0、Redis新增0/baseline保留。仍未验收/提交BFF、未启动3310、未通过浏览器全文门。Billing只读核查确认新Metering当前按功能quantity=1定价，无成本倍率规则；1.4与9.4基准待用户确认，未写配置或执行账务。

**本轮后置更新（Root代码9e77ac17）：** checkpoint/topology分别实际exit0；使用用户指定私有profile，一次真实免费库存GET成功、未调用推理。BFF tests-only已冻结，Root复用现PG/Redis在唯一自有临时库执行真实RED：3pass/5fail/0skip、2.31s，均缺active_run或缺非法marker拒绝；自有库0、Redis新增0/baseline保留，日志`/tmp/kokoro-bff-active-run-real-pg-red.log`，原owner已获GREEN源码授权。Billing五docs修订独立0/0/0，但IAM任意target能力未发布，源码/入账仍阻塞。用户要求的当前线程每10分钟检查并推进heartbeat `kokoro-10` 已创建ACTIVE并回读；静默无变化、实质进展/失败/偏差/决策通知。3310仍未重启，完整goal未闭环。

## 本轮最新：开发入口稳定性与竞品交互对齐（2026-09-30）

Root `6fdcba6e` 基线的三文件生命周期切片已由原writer停写、独立复审0/0/0、Root主树完整纯门 **1103 passed / 3 native依赖skip / 455 subtests**（114.87s，session2944 exit0已消费）后验收。日志 `/tmp/kokoro-provider-lifecycle-final-root-tests.log`；Ruff check/format/diff均exit0。外部周期库存的预期传输/格式失败只写System `unknown`，继续原两ownership续租、health CAS与严格status/observed_at/provider/generation回执；不伪造healthy，不退出独立IAM/Web。下一正常60s周期可恢复healthy。配置/代码、owned进程、ownership、CAS/回执错误仍fatal，启动两个preflight和Ollama严格不变，无后台保活/自动重试/付费健康推理。

首候选1102pass仍被独立审查1P1拒绝：回执只验证provider/generation，接受了与unknown命令不一致的healthy。追加RED16场景后补齐真实System回执绑定，最终聚焦58pass/114subtests；原FAIL和首候选日志保留。三文件最终hash已Root核对；这里仅证明工具代码/测试，不证明真实周期故障恢复、已重启3310或完整浏览器Chat成功。**3310仍未重新启动，真实Chat terminal DOM门仍FAIL。**

官方ChatGPT Projects、Manus Projects/Connectors及Scheduled Tasks参照和Kokoro验收取舍已进入既有 `docs/task.md` 顶部：会话/项目/调度定义/Run身份分离、默认个人私有显式分享、真实文件与结果；不另建UI/计划中心。BFF四文档修复独立0/0/0通过，原2P1/1P2关闭，仅恢复既有v1 running的同RR snapshot方案已放行测试RED阶段；OpenAPI原字节、不改enum/消费者契约，源码与真PG/浏览器尚未验收。Billing五文档修订候选已停写，200command ACK/1Credit=1e6micros/reason贯穿已统一，IAM任意target能力明确owner-first阻塞；未充值、未计费E2E，文档待复审。

状态日期：2026-09-30。这里只记录当前组合和已验证边界；执行任务见 [task.md](task.md)，逐轮证据及失败历史见 [progress.md](progress.md)。旧 CURRENT 时间线保存在 Git `51bd4a2f40aab98b253329c0a5e9d110b7e77211`，不是并列的当前方案。

## 已锁定的组合

下表与本次 Root 集成提交的 gitlink 一致，不代表正在修改的子仓工作树或常驻预览的加载版本。Root 是 Git superproject，`.gitmodules` 的 branch 只是提示，精确发布来源由 gitlink 与 owner artifact digest 锁定。

| 路径 | 固定 commit |
| --- | --- |
| `apps/kokoro-agent` | `58b59cf7cdc4132042d25460b4928d71a66ae7ec` |
| `apps/kokoro-app` | `30545c55625fb257ac17ce2199e8fa1000f3ecae` |
| `apps/kokoro-bff` | `15e07fa44670bc13705ce3f6f700e73afcb72ccc` |
| `apps/kokoro-billing` | `63e0ab6e61b397f23f7ab71f5d6dc9df3d6de0fa` |
| `apps/kokoro-capability` | `6519ae9a7dba63586474d2860f6725d3165b701e` |
| `apps/kokoro-iam` | `e3c035b99cf9479ac8357c7d38147f1541dcbcac` |
| `apps/kokoro-mori` | `ca76c2e12861a2e4a6af3049f6df8c34b417c158` |
| `apps/kokoro-scheduler` | `975dee59616a1e0eda609aa69283401344900d83` |
| `apps/kokoro-storage` | `16a6c1ce95832df6dc839e0d50e957405c5c7005` |
| `apps/kokoro-system` | `c0a76a3a7614bf46ea6e665e523f24261862436f` |
| `libs/kokoro-web-shared` | `0c4e87ace01340aaa07bc57935f1d98b8e77af14` |

`apps/kokoro-app` 是本轮唯一正式前端；Mori 不参与本轮业务重构。当前物理名称仍为 `apps/kokoro-capability`，业务目标为 Platform，重命名/cutover 未完成；不使用 `apps/kokoro/` alias。模型目录归 System，不新建 kokoro-model。

**历史用户链证据（当前组另见下文）：** 3310曾唯一有序切换到用户指定外部`gpt-5.6-luna`；正规IAM登录→app原生发送202→正式System resolveModel success→标准Agent真实可见回复。独立首轮捕获流式前缀并途中刷新，但terminal严格组合断言E_FLOW，原失败保留。同一会话后验GET两份完整snapshot稳定、DOM全文一致、原生logout成功；不能以后验改称首轮全通过，途中刷新的瞬态断言仍待定位。右侧IAB操作被平台URL policy拒绝，未绕过，独立Chromium不是右侧IAB已验。

**历史运行更新（已被当前29394组替代）：** Root ee22bacd原受管session92720/launcher39290/Web39688已exit1且3310无监听，workspace`kokoro-local-login-he2cz0xc`保留。固定安全日志明确实际失败分支`stage=provider`，即模型库存观测失败导致整组清理；并非已经证明真实推理失败或具体HTTP状态。该组实际曾加载Web752/BFF677、emptySkills/Storage未装配。后继须隔离模型库存观测与独立IAM/Web生命周期，不放宽ownership/CAS或伪造healthy，不盲目重复重启。

**历史真实Chat失败验收：** 新独立产品Chromium第二轮已越过真实login/UI202/非空prefix途中reload/RUN_FINISHED、owner completed、Stop detached、两份正式terminal snapshot全文/ID/run/status/watermark比较；FAIL精确为`terminal_dom_full_content`，最后owner有效、Stop0/user1/markdown-message2。这两DOM parts不等同重复Message；已纯当前源码对照复现：BFF snapshot缺active_run时无法认领同run前缀，补合法active_run则一段。真实轮reload瞬间shape未捕获；后继BFF同RR projection文档门进行，不加Web猜测或盲拼START。证据`/var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-gpt56-await-proof.h4b1tsvz`，非右侧IAB。原首轮及历史E_FLOW失败保留，无完整E2E PASS。

**真实Product安装当前：** Root `c3fa42710334bf1b9dc00f9be0f8b6a21a647e78` 原入口`run_bff_skill_draft_sandbox_smoke.py --product-installation`已真实exit0/PASS（session78975），日志`/tmp/kokoro-product-installation-real-surface.log`。固定IAMe3c/BFF677/Platform6519/Storage16a6，复用现PG/Redis/MinIO/ClamAV，五public操作、same-key历史ACK→GET当前、false筛选/opaque两页、移除/稳定ID重装、撤权五方法在owner前拒绝均通过；两不同已发布Skill、39receipt/2publish事件，resources clean。此前native依赖缺失与Root误开legacy surface的真实FAIL保留。此为后端组合，不是浏览器安装UI、同租户第二用户或标准worker非空Skill模型验证；Agent关闭仅结构证据，不冒充Run数据库观测。

## 最新验收边界

| 能力 | 当前证据 | 尚未证明 |
| --- | --- | --- |
| 非空 typed Skill Source | Root `4aef9d1c` 正常原文件入口真实 IAM/BFF/Platform/Storage/Agent/PG/Redis/MinIO/ClamAV，exit0/PASS；安装、原字节、native metadata、只读、停用拒读/重新启用、旧 lease 拒读、IAM 执行撤权均通过；receipt31→34/outbox2；resources clean、Redis15=0。日志 `/tmp/kokoro-source-window-real-composition.log` | 标准 worker＋真实模型的非空 Skill 运行、个人 Product 安装 UI、正式激活。native name 与 opaque 目录不匹配警告仍开放 |
| 普通 Chat/作品 | 历史固定组合已验真实 Chromium 登录、标准 worker、durable AG-UI、live Delivery、刷新、Canvas 下载、GC/410 恢复与个人私有性；历史 `5b1b9a5e` 还验真实 System→已有 Ollama→worker→Storage 作品链，精确来源/边界见 progress | 历史普通 Chat 或空选择模型结果不替代当前非空 Skill 模型运行，也不证明所有产品能力 |
| 个人 Skill 安装 | Platform runtime `d93e8a59` 已独立审查0缺陷＋RootNode24全门1185pass/243依赖skip＋真实ownedPG安装事务27/27（含ACKlost/CAS），自有库已回收。旧v5机器候选发现List has_more与唯一Proto optional next_cursor矛盾，已在6519ae9以5.0.1纠正，Root全门1196pass/243skip与独立0缺陷；仍inactive | owner runtime、机器wire、BFF固定消费者、Web纯门与真实后端五API组合已验；浏览器安装、正式激活、非空Skill模型运行仍待验，不是全产品可用 |
| 最近3310留证（现已停止） | 原受管session53033/launcher30171：IAM30877/System31271/Agent HTTP31307/worker31309/BFF31346/Web31351。精确Web14a54b4/BFF67755d16/Systemc0a76a3a/Agent58b59cf7；用户指定gpt-5.6-luna，经私有profile正式System路由/标准Agent。首轮正常登录和UI消息202、非空流式prefix/中途刷新、可见真实回复；同一会话后验两条完整owner内容及ID750ms稳定、DOM全文一致、原生logout/session=false。证据`/tmp/kokoro-gpt56-ui.CsnuNA`（首轮FAIL）和`/tmp/kokoro-gpt56-diag.hVEygz`（只读诊断PASS）。 | 首轮严格terminal E_FLOW未存当时shape/hash，历史具体子断言不可后验臆定；不能称首轮E2E PASS。Root新增正式快照全文/身份/watermark证据门仅纯测试通过，真实模型门尚未重跑。右侧IAB未验，Skills空选择/Storage未配置/完整产品未闭环。 |

Root Source-only 高请求量测试在 Run/lease 前主线程等待现 IAM60秒窗口；默认模式不等待，SIGTERM可中断。没有改生产限流、权限、凭据或 Redis 计数；这是测试资源礼让，不是应用重试/fallback。

## 用户指定真实外部模型

用户选择 `gpt-5.6-luna`，指定HTTPS接口真实 `/chat/completions` 已200、返回该ID及非空回复，
结果 `/tmp/kokoro-gpt56-luna-probe.json`（0600、无key/body）。Root现组合工具支持显式私有profile，
七源码/测试文件独立0缺陷、Root87tests/36subtests与Ruff通过；不改System/Agent owner API或原Ollama guard。
历史3310外部profile经正式System→标准Agent→UI已产生真实回复；最新受管组另见上文，完整首轮E2E仍FAIL，后验持久态/DOM一致不改写历史失败。旧7399及其六直接子进程已全部退出、session65687已回收，首启动因3310临时bind占用exit1，等原guard释放后再成功启动，无kill-all/端口guard放宽。

## 当前优先级与正在推进

- Platform 原负责人：runtime已验收提交d93e8a59；已提交6519ae9未激活v5候选5.0.1 wire矛盾纠正，唯一Proto/Schema/runtime源码冻结，无兼容字段/双轨。
- BFF消费者67755d16已独立0缺陷与Root Node22全门验收提交；五本人安装路由固定Platform6519/5.0.1，读projection/写catalog分离，默认新增测试已纳入，413/504真实状态契约。真实IAM→BFF→Platform安装组合已PASS；Web安装浏览器仍待验。
- Web原负责人：个人安装consumer已提交752aff9d，29文件独立0/0/0、Root contract109/architecture37/lint/typecheck/test1773/build通过；五client/严格同源adapter/UI未知同key/currentGET/分页取消已验纯门。真实后端组合已PASS；新3310启动时加载本片后退出，浏览器安装仍待验。完整Project typed全集及任务关联仍后继切片。
- Root主线：gpt-5.6-luna正式链真实回复已见，首轮中途刷新严格断言失败待精确定位；已完成的Web/BFF候选统一提交并加载，旧session53033/14183已退出，旧92720已退出；当前29394唯一受管组已加载BFF15e07fa4，并按顶部记录做原生IAB验证。继续按owner推进非空Skill/安装Web、Project真实全集及全产品闭环，不把直接provider probe/后验快照冒充完整E2E。

同仓单writer；worker不自行启动共享PG/Redis或重置数据。子仓 CURRENT 中“候选待Root”属于交付时快照，Root已验收状态以本表和绑定commit的task/progress为准；在owner下一代码切片同步文档，不因纯文案制造另一轮依赖升级。

## 未闭环清单

1. 当前个人安装machine→owner runtime→BFF真实后端组合已验；Web浏览器安装、Platform原子命名/激活cutover仍开放。
2. 非空Skill真实worker/模型、MCP执行与其他Agent能力；不以Source helper读取替代真实运行。
3. Browser signed PUT/CORS：已探测本地MinIO返回501；HTTP Source GET/PUT或预览Playwright不替代浏览器发布门。Storage orphan retirement/quarantine 等生命周期仍开放。
4. System 部分 installer 仍锁 public/整库空白；同库owner schema组合边界须继续修正。Team DOM/邀请邮件/写操作、Scheduler调用/恢复与其他Product surface均须按owner闭环。
5. 最近全仓标准门137项违规（旧136非当前），来源库存16边/13 declared broken；这些是仍开放队列，不因局部PASS改绿。完整goal仍active，Billing最后。
6. BFF d654a1bc已完成IAMe3来源重钉，16SDK与owner inputs原bytes，policy语义不变；Root3bdf27db已集成；提交后relay实际FAIL（BFF四文档候选仍dirty），前一组合命令尾部git status掩盖前面退出码，原PASS描述已纠正；预提交HEAD/index不一致FAIL也保留。checkpoint/topology须独立记录，不以整段shell末尾exit0推定。Web仍更旧a4/0.6 relay消费者，后继原字节消费未完成，不把BFF provenance PASS当Web闭环。
7. 工作树任务外Root `uv.lock` 变化保留不暂存；不称全体clean。本轮实际main-only核对主仓+11子仓本地/远端全仅main、当时11子仓clean；当前BFF文档候选和Web修复在途，整体gate因Root在途改动及任务外uv.lock FAIL，后者保留，不称全体clean，不新建分支/PR。

## 验证和归属

- 最新Root `a0b95a31`发布组合：独立checkpoint/topology实际exit0；完整`scripts/tests` **1094 passed / 3 native依赖skip / 409 subtests**，100.52s（session75632 exit0已消费），日志`/tmp/kokoro-web-billing-root-full-tests.log`。严格IAMrelay门仍FAIL：BFF候选四文档dirty；不以Root纯门PASS将该门改绿、不称整体clean或收费已完成。Web840完整owner门1784/162无skip已独立验收；受管3310仍未重新启动。

- Root当前`c3fa4271`组合checkpoint/topology PASS；同handle91663全量`scripts/tests` **1090 passed/3 native依赖skip/395 subtests**，117.49s，exit0已消费，日志`/tmp/kokoro-product-final-root-tests.log`。Product selector独立0/0/0、聚焦86/98subtests，原入口真实owned组合PASS；3个native skip不以Agentvenv真实组合覆盖为本runtime全绿。全仓标准门最近仍FAIL137/0 unverified，不更改门禁清零。
- Root `4aef9d1c` 提交后的topology9runtime/checkpoint通过。新增候选仍须独立验收和最终集成复验。
- 子仓的 tests 不迁入 Root；`scripts/tests/` 只覆盖 Root 治理脚本（含Root自有组合driver边界），业务unit/integration/contract/build仍在owner仓。`verification/` 保存跨仓来源库存与检查点，不复制业务测试。
- 本地应用使用一个PG数据库/一套credential、独立owner schema和共享Redis namespace；测试临时库用于运行隔离，不是多应用角色/部署方案。禁止跨owner业务SQL。

当前可执行门：

```bash
python3 scripts/verify-repository-topology.py
python3 scripts/verify-contract-checkpoint.py --expected verification/contracts/checkpoints/w1e-iam07-bff-pin.json
python3 scripts/verify-iam-relay-policy.py
python3 scripts/verify-main-only.py
python3 -m pytest scripts/tests
```

旧 `verify-ten-repository-full.sh` 与 `run_stage2_owner_health.py` 的共享状态编排暂停，不能当作全仓验收；完整单仓门、真实模型和浏览器门按task依赖逐片执行。

## 正式积分流程最新核对（2026-09-30）

用户已授权当前测试帐号后台积分入账；尚未执行，不称已充值。Web“本次由 Kokoro 承担费用，不消耗点数”是 taskTitle 条件下的静态 Badge，未消费计费 owner 决策，九语言对收费说法矛盾；删除片已提交Web840fa7e0、独立0/0/0、Root重跑完整1784tests/162files、contract109/architecture37/lint/typecheck/build PASS；未启动预览/未真实浏览器验收，placeholder亦已中性。Billing `63e0ab6` 已有32表 canonical 与新 CreditService 的事务组件，但生产主入口仍旧 pg/旧表，新 grant/operator入口与 Run准入/结算未接，CURRENT明确M3/M4前不可部署。Web余额 DTO 与BFF public契约及标准402 error code消费也有缺口，不能以移除Badge宣布账务闭环。支付渠道仍最后；积分正式赠送、reserve/capture/release 和余额/流水按owner后续逐片验收。

## WEB-BILLING-TRUTH 集成证据

Web `840fa7e0ff9c4d241daca0c297b120f34821018e`：16现文件已冻结hash核验、独立0/0/0与Root Node22主树完整门后提交。Root日志 `/tmp/kokoro-web-billing-truth-root-gates.log`；162文件1784通过（含worker未跑的8个integration命名文件119项，无skip），contract109/architecture37/lint/typecheck/build/diff PASS。这里的测试名称integration不据此冒充真实Billing/provider组合；未充值、未Run扣费/浏览器验收。Root后继只更新Web gitlink/来源库存/blob digest与driver固定SHA，不改任何业务或放宽门。BFF active文档独立2P1/1P2（版本策略、非法stream矩阵、永久失败测试允许集）尚未通过，未授权源码；Billing新正式admin grant五文档门进行中。

### a0b95a31 后置门事实修正

Root已集成Web840fa7e0；relay门实际FAIL `apps/kokoro-bff: child worktree is dirty`，由尚未通过独立审查的BFF四文档候选触发。首前置shell尾部git status曾掩盖门exit1，Root读取原JSON后已纠正全部本轮relay PASS断言。原失败日志保留，严格门不放宽，也不回滚/覆盖worker候选。Web1784/162完整owner测试/构建为独立已实跑exit0，和Rootdirty gate分别记录。Root随后各门独立执行，不再以shell最后命令冒充前面门通过。
