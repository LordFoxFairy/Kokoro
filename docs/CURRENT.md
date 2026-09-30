# Root 当前组合

状态日期：2026-09-30。这里只记录当前组合和已验证边界；执行任务见 [task.md](task.md)，逐轮证据及失败历史见 [progress.md](progress.md)。旧 CURRENT 时间线保存在 Git `51bd4a2f40aab98b253329c0a5e9d110b7e77211`，不是并列的当前方案。

## 已锁定的组合

下表与本次 Root 集成提交的 gitlink 一致，不代表正在修改的子仓工作树或常驻预览的加载版本。Root 是 Git superproject，`.gitmodules` 的 branch 只是提示，精确发布来源由 gitlink 与 owner artifact digest 锁定。

| 路径 | 固定 commit |
| --- | --- |
| `apps/kokoro-agent` | `58b59cf7cdc4132042d25460b4928d71a66ae7ec` |
| `apps/kokoro-app` | `752aff9d0744cd55c556079a08a2a28e393e50e4` |
| `apps/kokoro-bff` | `67755d16ff0f40ea02d71a6dad7108507a04766a` |
| `apps/kokoro-billing` | `63e0ab6e61b397f23f7ab71f5d6dc9df3d6de0fa` |
| `apps/kokoro-capability` | `6519ae9a7dba63586474d2860f6725d3165b701e` |
| `apps/kokoro-iam` | `e3c035b99cf9479ac8357c7d38147f1541dcbcac` |
| `apps/kokoro-mori` | `ca76c2e12861a2e4a6af3049f6df8c34b417c158` |
| `apps/kokoro-scheduler` | `975dee59616a1e0eda609aa69283401344900d83` |
| `apps/kokoro-storage` | `16a6c1ce95832df6dc839e0d50e957405c5c7005` |
| `apps/kokoro-system` | `c0a76a3a7614bf46ea6e665e523f24261862436f` |
| `libs/kokoro-web-shared` | `0c4e87ace01340aaa07bc57935f1d98b8e77af14` |

`apps/kokoro-app` 是本轮唯一正式前端；Mori 不参与本轮业务重构。当前物理名称仍为 `apps/kokoro-capability`，业务目标为 Platform，重命名/cutover 未完成；不使用 `apps/kokoro/` alias。模型目录归 System，不新建 kokoro-model。

**当前用户链状态：** 3310已唯一有序切换到用户指定外部`gpt-5.6-luna`；正规IAM登录→app原生发送202→正式System resolveModel success→标准Agent真实可见回复。独立首轮捕获流式前缀并途中刷新，但terminal严格组合断言E_FLOW，原失败保留。同一会话后验GET两份完整snapshot稳定、DOM全文一致、原生logout成功；不能以后验改称首轮全通过，途中刷新的瞬态断言仍待定位。右侧IAB操作被平台URL policy拒绝，未绕过，独立Chromium不是右侧IAB已验。

**当前运行更新（本轮权威观测）：** session53033已exit1，launcher30171与原六子PID均不存在、3310无监听；日志末尾serving failed。已停止，不属于观察超时。现日志只证明进入有序清理，周期性Agent receipt_state_lost此前已存在，停止触发尚未确定；不要把历史成功回复或旧PID当当前服务在线。未自动重启，先窄查触发及owned回收边界。

## 最新验收边界

| 能力 | 当前证据 | 尚未证明 |
| --- | --- | --- |
| 非空 typed Skill Source | Root `4aef9d1c` 正常原文件入口真实 IAM/BFF/Platform/Storage/Agent/PG/Redis/MinIO/ClamAV，exit0/PASS；安装、原字节、native metadata、只读、停用拒读/重新启用、旧 lease 拒读、IAM 执行撤权均通过；receipt31→34/outbox2；resources clean、Redis15=0。日志 `/tmp/kokoro-source-window-real-composition.log` | 标准 worker＋真实模型的非空 Skill 运行、个人 Product 安装 UI、正式激活。native name 与 opaque 目录不匹配警告仍开放 |
| 普通 Chat/作品 | 历史固定组合已验真实 Chromium 登录、标准 worker、durable AG-UI、live Delivery、刷新、Canvas 下载、GC/410 恢复与个人私有性；历史 `5b1b9a5e` 还验真实 System→已有 Ollama→worker→Storage 作品链，精确来源/边界见 progress | 历史普通 Chat 或空选择模型结果不替代当前非空 Skill 模型运行，也不证明所有产品能力 |
| 个人 Skill 安装 | Platform runtime `d93e8a59` 已独立审查0缺陷＋RootNode24全门1185pass/243依赖skip＋真实ownedPG安装事务27/27（含ACKlost/CAS），自有库已回收。旧v5机器候选发现List has_more与唯一Proto optional next_cursor矛盾，已在6519ae9以5.0.1纠正，Root全门1196pass/243skip与独立0缺陷；仍inactive | Product owner runtime切片已验收；机器wire窄片已验收，BFF public固定消费、Web UI 和真实产品验收仍待完成；runtime单仓通过不是全产品可用 |
| 最近3310留证（现已停止） | 原受管session53033/launcher30171：IAM30877/System31271/Agent HTTP31307/worker31309/BFF31346/Web31351。精确Web14a54b4/BFF67755d16/Systemc0a76a3a/Agent58b59cf7；用户指定gpt-5.6-luna，经私有profile正式System路由/标准Agent。首轮正常登录和UI消息202、非空流式prefix/中途刷新、可见真实回复；同一会话后验两条完整owner内容及ID750ms稳定、DOM全文一致、原生logout/session=false。证据`/tmp/kokoro-gpt56-ui.CsnuNA`（首轮FAIL）和`/tmp/kokoro-gpt56-diag.hVEygz`（只读诊断PASS）。 | 首轮严格terminal E_FLOW未存当时shape/hash，历史具体子断言不可后验臆定；不能称首轮E2E PASS。Root新增正式快照全文/身份/watermark证据门仅纯测试通过，真实模型门尚未重跑。右侧IAB未验，Skills空选择/Storage未配置/完整产品未闭环。 |

Root Source-only 高请求量测试在 Run/lease 前主线程等待现 IAM60秒窗口；默认模式不等待，SIGTERM可中断。没有改生产限流、权限、凭据或 Redis 计数；这是测试资源礼让，不是应用重试/fallback。

## 用户指定真实外部模型

用户选择 `gpt-5.6-luna`，指定HTTPS接口真实 `/chat/completions` 已200、返回该ID及非空回复，
结果 `/tmp/kokoro-gpt56-luna-probe.json`（0600、无key/body）。Root现组合工具支持显式私有profile，
七源码/测试文件独立0缺陷、Root87tests/36subtests与Ruff通过；不改System/Agent owner API或原Ollama guard。
当前3310已切换外部profile：正式System→标准Agent→UI已产生真实回复；完整首轮E2E仍FAIL，后验持久态/DOM一致不改写历史失败。旧7399及其六直接子进程已全部退出、session65687已回收，首启动因3310临时bind占用exit1，等原guard释放后再成功启动，无kill-all/端口guard放宽。

## 当前优先级与正在推进

- Platform 原负责人：runtime已验收提交d93e8a59；已提交6519ae9未激活v5候选5.0.1 wire矛盾纠正，唯一Proto/Schema/runtime源码冻结，无兼容字段/双轨。
- BFF消费者67755d16已独立0缺陷与Root Node22全门验收提交；五本人安装路由固定Platform6519/5.0.1，读projection/写catalog分离，默认新增测试已纳入，413/504真实状态契约。真实IAM→BFF→Platform组合与Web安装UI仍未验。
- Web原负责人：个人安装consumer已提交752aff9d，29文件独立0/0/0、Root contract109/architecture37/lint/typecheck/test1773/build通过；五client/严格同源adapter/UI未知同key/currentGET/分页取消已验纯门。真实owner组合与浏览器仍待验，常驻3310未加载本片。完整Project typed全集及任务关联仍后继切片。
- Root主线：gpt-5.6-luna正式链真实回复已见，首轮中途刷新严格断言失败待精确定位；已完成的Web/BFF候选统一提交并加载，唯一受管session53033只由Root管理。继续按owner推进非空Skill/安装Web、Project真实全集及全产品闭环，不把直接provider probe/后验快照冒充完整E2E。

同仓单writer；worker不自行启动共享PG/Redis或重置数据。子仓 CURRENT 中“候选待Root”属于交付时快照，Root已验收状态以本表和绑定commit的task/progress为准；在owner下一代码切片同步文档，不因纯文案制造另一轮依赖升级。

## 未闭环清单

1. 当前个人安装链的 machine→owner runtime→BFF→Web→真实端到端及Platform原子命名/激活cutover。
2. 非空Skill真实worker/模型、MCP执行与其他Agent能力；不以Source helper读取替代真实运行。
3. Browser signed PUT/CORS：已探测本地MinIO返回501；HTTP Source GET/PUT或预览Playwright不替代浏览器发布门。Storage orphan retirement/quarantine 等生命周期仍开放。
4. System 部分 installer 仍锁 public/整库空白；同库owner schema组合边界须继续修正。Team DOM/邀请邮件/写操作、Scheduler调用/恢复与其他Product surface均须按owner闭环。
5. 最近全仓标准门137项违规（旧136非当前），来源库存16边/13 declared broken；这些是仍开放队列，不因局部PASS改绿。完整goal仍active，Billing最后。
6. 最新Root IAM relay门FAIL：BFF policy iamOwnerCommit仍4d981441而IAM gitlink为e3c035b；这是未完成来源对齐，不能把HTTP通过当作此门通过。BFF当前个人安装切片不抢改IAM相关source，后续独立精确pin修复需保持机器bytes验证与Web消费同步。
7. 工作树任务外Root `uv.lock` 变化保留不暂存；不称全体clean。历史12仓main-only来源记录不替代当前门；本轮Web/BFF/Platform工作树clean且main，Root任务外uv.lock保留，不称全体clean，不新建分支/PR。

## 验证和归属

- Root当前d4b49c88组合checkpoint/topology PASS；全量`scripts/tests` **1062 passed/3 native依赖skip/377 subtests**，111.65s，日志`/tmp/kokoro-snapshot-root-full-tests.log`。全仓标准门仍FAIL137/0 unverified：相对旧136，Agent平台契约文件>800与Platform README provenance两项显现，Web app-frame>500已消除；不更改门禁清零。
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
