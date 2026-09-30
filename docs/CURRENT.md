# Root 当前组合

状态日期：2026-09-30。这里只记录当前组合和已验证边界；执行任务见 [task.md](task.md)，逐轮证据及失败历史见 [progress.md](progress.md)。旧 CURRENT 时间线保存在 Git `51bd4a2f40aab98b253329c0a5e9d110b7e77211`，不是并列的当前方案。

## 已锁定的组合

下表与本次 Root 集成提交的 gitlink 一致，不代表正在修改的子仓工作树或常驻预览的加载版本。Root 是 Git superproject，`.gitmodules` 的 branch 只是提示，精确发布来源由 gitlink 与 owner artifact digest 锁定。

| 路径 | 固定 commit |
| --- | --- |
| `apps/kokoro-agent` | `58b59cf7cdc4132042d25460b4928d71a66ae7ec` |
| `apps/kokoro-app` | `79f19df3167e56d1d3ed517266427443363d5005` |
| `apps/kokoro-bff` | `c4c4cbccee68eee95c1b89548abb6302b80e58e6` |
| `apps/kokoro-billing` | `63e0ab6e61b397f23f7ab71f5d6dc9df3d6de0fa` |
| `apps/kokoro-capability` | `6519ae9a7dba63586474d2860f6725d3165b701e` |
| `apps/kokoro-iam` | `e3c035b99cf9479ac8357c7d38147f1541dcbcac` |
| `apps/kokoro-mori` | `ca76c2e12861a2e4a6af3049f6df8c34b417c158` |
| `apps/kokoro-scheduler` | `975dee59616a1e0eda609aa69283401344900d83` |
| `apps/kokoro-storage` | `16a6c1ce95832df6dc839e0d50e957405c5c7005` |
| `apps/kokoro-system` | `c0a76a3a7614bf46ea6e665e523f24261862436f` |
| `libs/kokoro-web-shared` | `0c4e87ace01340aaa07bc57935f1d98b8e77af14` |

`apps/kokoro-app` 是本轮唯一正式前端；Mori 不参与本轮业务重构。当前物理名称仍为 `apps/kokoro-capability`，业务目标为 Platform，重命名/cutover 未完成；不使用 `apps/kokoro/` alias。模型目录归 System，不新建 kokoro-model。

**当前用户链仍为P0：** 独立Chromium对实际3310正常提交登录已进入/app、正常确认退出也通过；不是用户右侧IAB已验。浏览器中途刷新发现助手文本分片次序异常，且临时验收脚本未严格等待终态/误标passed已撤销，真实终态和刷新一致性仍须返验；整体尚未闭环。主控不再要求用户辨认按钮，不以重启或继续改样式代替故障证据。

## 最新验收边界

| 能力 | 当前证据 | 尚未证明 |
| --- | --- | --- |
| 非空 typed Skill Source | Root `4aef9d1c` 正常原文件入口真实 IAM/BFF/Platform/Storage/Agent/PG/Redis/MinIO/ClamAV，exit0/PASS；安装、原字节、native metadata、只读、停用拒读/重新启用、旧 lease 拒读、IAM 执行撤权均通过；receipt31→34/outbox2；resources clean、Redis15=0。日志 `/tmp/kokoro-source-window-real-composition.log` | 标准 worker＋真实模型的非空 Skill 运行、个人 Product 安装 UI、正式激活。native name 与 opaque 目录不匹配警告仍开放 |
| 普通 Chat/作品 | 历史固定组合已验真实 Chromium 登录、标准 worker、durable AG-UI、live Delivery、刷新、Canvas 下载、GC/410 恢复与个人私有性；历史 `5b1b9a5e` 还验真实 System→已有 Ollama→worker→Storage 作品链，精确来源/边界见 progress | 历史普通 Chat 或空选择模型结果不替代当前非空 Skill 模型运行，也不证明所有产品能力 |
| 个人 Skill 安装 | Platform runtime `d93e8a59` 已独立审查0缺陷＋RootNode24全门1185pass/243依赖skip＋真实ownedPG安装事务27/27（含ACKlost/CAS），自有库已回收。旧v5机器候选发现List has_more与唯一Proto optional next_cursor矛盾，已在6519ae9以5.0.1纠正，Root全门1196pass/243skip与独立0缺陷；仍inactive | Product owner runtime切片已验收；机器wire窄片已验收，BFF public固定消费、Web UI 和真实产品验收仍待完成；runtime单仓通过不是全产品可用 |
| 当前 3310 | 一组受管65687/launcher7399/Web7874，真实IAM/System/BFF/Web与标准Agent HTTP/worker、已有Ollama。Root当前HTTP全链PASS：正规表单登录→消息202→10帧非空AG-UI终态→同键不重复→刷新持久→自身logout200。日志 `/tmp/kokoro-current-chat-http-acceptance.log`；System resolveModel success | 右侧IAB控制再次超时、DOM未验；HTTP不是浏览器交互。已将Web9590a74三生产文件精确同步受管dev snapshot，未重启BFF加载在途代码；同步后当前HTTP登录→真实模型回复→持久消息/刷新→自身logout再次PASS，仍非右侧DOM。Skills空选择、Storage未装配，完整能力体系仍待逐片接通 |

Root Source-only 高请求量测试在 Run/lease 前主线程等待现 IAM60秒窗口；默认模式不等待，SIGTERM可中断。没有改生产限流、权限、凭据或 Redis 计数；这是测试资源礼让，不是应用重试/fallback。

## 当前优先级与正在推进

- Platform 原负责人：runtime已验收提交d93e8a59；已提交6519ae9未激活v5候选5.0.1 wire矛盾纠正，唯一Proto/Schema/runtime源码冻结，无兼容字段/双轨。
- BFF负责人：三面已通过c4c4cbc，五安装消费在途；独立4P1（同预算/稳定错误/精确OpenAPI/严格输入）已拦截返修，最终固定Platform6519ae9/5.0.1，读projection/写catalog分离。真实组合未验。
- Web原负责人：已纯复现同run snapshot/segment不同ID导致前缀倒序，获现core/mapper五源码＋五测试窄片授权，先稳定RED后修复；不改UI/BFF协议或丢partials。
- Root主线：当前3310可见登录→app→基本真实聊天；暂停新研究面，测试/生成物不冒充产品交付。并行只读梳理用户新增首页/输入框/会话-专案-任务语义；继续统一审查、shared index、真实组合资源/进程和跨仓集成；已结束的 Source ownedPID53717/session80848均终态消费，当前65687保持运行，只由Root管理。

同仓单writer；worker不自行启动共享PG/Redis或重置数据。子仓 CURRENT 中“候选待Root”属于交付时快照，Root已验收状态以本表和绑定commit的task/progress为准；在owner下一代码切片同步文档，不因纯文案制造另一轮依赖升级。

## 未闭环清单

1. 当前个人安装链的 machine→owner runtime→BFF→Web→真实端到端及Platform原子命名/激活cutover。
2. 非空Skill真实worker/模型、MCP执行与其他Agent能力；不以Source helper读取替代真实运行。
3. Browser signed PUT/CORS：已探测本地MinIO返回501；HTTP Source GET/PUT或预览Playwright不替代浏览器发布门。Storage orphan retirement/quarantine 等生命周期仍开放。
4. System 部分 installer 仍锁 public/整库空白；同库owner schema组合边界须继续修正。Team DOM/邀请邮件/写操作、Scheduler调用/恢复与其他Product surface均须按owner闭环。
5. 最近全仓标准门136项违规，来源库存16边/13 declared broken；这些是仍开放队列，不因局部PASS改绿。完整goal仍active，Billing最后。
6. 最新Root IAM relay门FAIL：BFF policy iamOwnerCommit仍4d981441而IAM gitlink为e3c035b；这是未完成来源对齐，不能把HTTP通过当作此门通过。BFF当前个人安装切片不抢改IAM相关source，后续独立精确pin修复需保持机器bytes验证与Web消费同步。
7. 工作树任务外Root `uv.lock` 变化保留不暂存；不称全体clean。本轮12仓本地/远程均只有main；完整main-only门因Root任务外uv.lock及Web/BFF/Platform在途修改FAIL，不称全体clean，不新建分支/PR。

## 验证和归属

- 当前Root运行runtime集成后checkpoint/topology/相关95项PASS；最近全量Root `scripts/tests`：1049 passed/3 native依赖skip/354subtests、111.60秒，日志 `/tmp/kokoro-platform-v5-current-entrance-root-tests.log`；当前topology/checkpoint PASS。该门只支持对应Root代码，不等于全仓门。
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
