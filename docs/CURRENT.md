# Root 当前组合

状态日期：2026-09-30。这里只记录当前组合和已验证边界；执行任务见 [task.md](task.md)，逐轮证据及失败历史见 [progress.md](progress.md)。旧 CURRENT 时间线保存在 Git `51bd4a2f40aab98b253329c0a5e9d110b7e77211`，不是并列的当前方案。

## 已锁定的组合

下表与本次 Root 集成提交的 gitlink 一致，不代表正在修改的子仓工作树或常驻预览的加载版本。Root 是 Git superproject，`.gitmodules` 的 branch 只是提示，精确发布来源由 gitlink 与 owner artifact digest 锁定。

| 路径 | 固定 commit |
| --- | --- |
| `apps/kokoro-agent` | `58b59cf7cdc4132042d25460b4928d71a66ae7ec` |
| `apps/kokoro-app` | `840fa7e0ff9c4d241daca0c297b120f34821018e` |
| `apps/kokoro-bff` | `d654a1bc6ce0347e28dd90a0ce0ee1553b8d67ed` |
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

**当前运行更新：** Root ee22bacd原受管session92720/launcher39290/Web39688已exit1且3310无监听，workspace`kokoro-local-login-he2cz0xc`保留。固定安全日志明确实际失败分支`stage=provider`，即模型库存观测失败导致整组清理；并非已经证明真实推理失败或具体HTTP状态。该组实际曾加载Web752/BFF677、emptySkills/Storage未装配。后继须隔离模型库存观测与独立IAM/Web生命周期，不放宽ownership/CAS或伪造healthy，不盲目重复重启。

**当前真实Chat验收：** 新独立产品Chromium第二轮已越过真实login/UI202/非空prefix途中reload/RUN_FINISHED、owner completed、Stop detached、两份正式terminal snapshot全文/ID/run/status/watermark比较；FAIL精确为`terminal_dom_full_content`，最后owner有效、Stop0/user1/markdown-message2。这两DOM parts不等同重复Message；已纯当前源码对照复现：BFF snapshot缺active_run时无法认领同run前缀，补合法active_run则一段。真实轮reload瞬间shape未捕获；后继BFF同RR projection文档门进行，不加Web猜测或盲拼START。证据`/var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-gpt56-await-proof.h4b1tsvz`，非右侧IAB。原首轮及历史E_FLOW失败保留，无完整E2E PASS。

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
- Root主线：gpt-5.6-luna正式链真实回复已见，首轮中途刷新严格断言失败待精确定位；已完成的Web/BFF候选统一提交并加载，旧session53033/14183已退出，最新92720已退出、当前无受管在线组；BFF新pin不得宣称其已加载。继续按owner推进非空Skill/安装Web、Project真实全集及全产品闭环，不把直接provider probe/后验快照冒充完整E2E。

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
