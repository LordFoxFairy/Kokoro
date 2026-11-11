# Kokoro · 当前维护与暂存 TODO

## 当前优先级纠偏：远程 PR 与 main 交付收尾（2026-11-11）

用户指出远程PR仍多，当前先收口交付债务，不继续扩展新代码。**“本轮PR已合并／Root固定组合已验”不等于“所有子仓都已完成main交付”。** 全部13仓初查8个OPEN，现已将System #2／Billing #4正常合main，并按用户确认将我们的Capability #13合入原接收分支，余5个均为Task B／其配对依赖；明细见[报告§11](docs/reports/2026-11-11-typescript-auth-admin-audit.md#11-远程pr收尾复核2026-11-11)。Task B按原负责人保留，不为清零擅自合并／关闭。

- [x] 主控：逐仓查OPEN、fetch精确main／head／base，核Root当前pins；8个head均未成为main祖先，没有仅凭PR数量可直接关闭的依据。
- [x] 主控：承认Capability #13是我们的Task A遗留；修正其PR描述中“最新base未集成”等过时内容，保持真实stack，不伪写合并状态。
- [x] Task A收尾：用户确认按原目标合入Capability #13，正常merge `e068fcaaeb0c40e1119ce88760f568a94bf0859c`；#12保持OPEN／Draft，不合main。合并树与已验源码 `24094960` 完全一致且包含该提交，Root精确pin不变；自有远程分支 `codex/task-a-c1-capability` 已删，本地无该分支。接收分支仅按本次授权前进，其他人的PR元数据和分支不操作。
- [x] 主控：System #2／Billing #4已通过原PR正常合main，merge分别 `0a4e7932`／`43a60920`；196／426个交付输入逐项核Git相等，复用精确历史验收，独立代码审查／最终文档复核完成。CI因账户账单未启动不称通过，未绕保护、未重复真实资金旅程；两个候选远端分支已清理，Root原已验源码pins不变且现已在main可达。
- [x] 在手维护：原已停写IAM候选经主控验收与原PR #7合main，Root #72已完成组合交付和自有分支清理；未增加新切片。Capability #13按上项独立授权收口，本次仅补收尾文档。

## 当前执行：IAM 可用性与会话撤销修复（2026-11-11）

用户同意继续修复，复用[审计报告§10](docs/reports/2026-11-11-typescript-auth-admin-audit.md#10-iam后继修复设计门2026-11-11)，不新建第二套任务中心。IAM唯一writer负责源码／对应测试／owner当前说明，主控负责边界、资源与验收；另外两名agent只读复核。Task B保持其PR和功能写区，不部署。

- [x] 主控：Root／IAM clean、fetch后main身份已核；IAM当前无open PR，main树与原已验pin相同。本轮沿codex/iam-maintenance短分支实施，不直接写main。
- [x] IAM writer／主控：R-01普通BFF owner可信actor分桶100/60、R-02同事务keyset批量撤销、R-04读取5秒／HTTP响应30秒及迟到结果退休已实现，独审与主控验收通过；保其它认证分支、rotation/CAS、墓碑子token、整批回滚及unknown副作用边界。
- [x] Root治理writer／主控：不变SDK发行锚与runtime pin解耦，原独立归档摘要、SDK整树／合同相等、祖先／lock／SRI／dirty／repack负控保持；相关153项、Ruff和当前真实15条契约边／0违例、原checkpoint通过。不改Task B消费者或伪造provenance。
- [x] 主控：前置格式／lint／类型／合同生成／breaking／SDK检查通过；首次默认唯一失败为旧源码Math.min字面oracle，保留AST唯一writer并由现行为／真PG承接后默认1631通过、build通过；真实隔离PG3文件24通过，库存102→102，无共享数据重置。未用源码字符串迁就旧逐行SQL。
- [x] IAM 原PR #7已正常合main，精确已验源码 `cee88df4`；Root本次PR固定该提交并承载报告／TODO，最终自有分支清理以主控Git回执确认。未部署、不合Task B；新核的get-session源IP容量仍OPEN，不声称所有候选已全修。

新核实的边界：官方get-session按源IP／路径100/60计数，BFF汇聚请求可能继续共享；它与普通业务actor桶是两层。本轮不随意把阈值调高、不伪称整条准入限流已全修，后续需按真实拓扑／容量明确策略。后台功能接线仍归Task B。

## 当前执行：认证边界与旧代码维护（2026-11-11）

已交付Task A不重开，Task B保持原负责人。本轮用户已要求从只读报告进入最小修复；依据[审计及本轮执行范围](docs/reports/2026-11-11-typescript-auth-admin-audit.md#8-后续执行2026-11-11)，不再新建第二份计划／任务表。

- [x] 主控：核准13仓／10个TS子仓的组合事实；完整分页核BFF PR17的598条文件范围，避开其幂等测试／package／README／CURRENT等重叠写区。
- [x] BFF writer：R-12用现个人上传接线先RED（Map 1≠0），持久提交成功后直接返回；主控定向14例、独立纯Map commit／快照／回放／冲突探针、lint／类型／build通过，独审CLEAR。原PR #20已合main，精确源码 `00a9ebee`。
- [x] Admin writer：R-10删除无消费者的旧独立登录env、专属测试与未使用传输包装，101行；主控9文件64例、lint、正规typegen／非增量types、webpack build和构建后types通过，独审CLEAR。原PR #6已合main，精确源码 `9bed3d2a`；实际登录、菜单与Task B不动。
- [x] 主控：纠正BFF现役AGENTS的旧IAM0.7／人类Bearer叙述；修正Root漏Admin和main-only过期入口。
- [x] 认证审计负责人：逐实际caller未发现普通内部机器换票活链，保留真实外部OAuth与业务在线权限。旧Admin OAuth不可达允许表与Task B重叠、Billing旧总factory仅测试消费者，列报告§9后继，不抢写。最近日志止于10/20且无源码SHA，只作历史诊断。
- [x] 主控：停写diff、消费者及交叉只读审查完成；子仓按原授权逐PR合main，来源按290项引用／232个实际Git blobs重核，不改机器契约。
- [x] 主控：Root精确组合、15条契约边／0违例、原checkpoint、相关拓扑回归与文档来源链接核验通过，由本轮Root PR承载；最终合并和自有分支清理以关联PR及主控Git回执为准，不代表IAM／Admin后继候选已修。不部署、不操作Task B PR。

后继候选：IAM R-01／R-02／R-04先与Task B确认当前实现和写权；Admin功能接线归B-13；Mori、shared包、contract check分别按owner排期，不因OAuth关键字或扫描数字机械删除。

失败口径保留：Admin初次types因旧Next生成物引用已删登录路由失败，只私有归档两份过期类型并正规重生成后通过；未改tsconfig或恢复旧路由。Root在暂存新gitlink前的组合检查正确拒绝旧index／新来源不配对，暂存精确pins后重新验证；未放宽校验。现有Vite config-loader提示为非阻断旧警告，未声称全部工具噪声已清。

## 已交付 Task A 的裁决与范围

用户最新确认：**本地 Docker E2B 协议验收通过后，Task A 按本次开发交付口径完成；其余真实账号／语音验收暂存下轮 TODO。** 本轮通过原 PR 合入 `main` 并清理 Task A 本地分支／工作树，不部署、不做真实支付。Task B 由其他人负责，不接手其 PR、分支或工作树。

这不等于所有外部生产环境验收通过。原逐项历史证据保留在[当前技术总览](docs/kokoro-handbook/technical/00-system-overview.md)和 Git 历史（本清单整理前 `1213099a`）；不再把旧执行记录叠加为第二份 TODO。Task A Goal 已按本次用户确认的开发交付口径完成，不恢复旧阶段顺序为当前阻塞。

## 本次开发交付

- [x] G0～G3／C‑1～C‑4 清理、原生认证切换及正式组合；A‑01/A‑02/A‑03/A‑04/A‑05/A‑06/A‑07/A‑08/A‑09/A‑11/A‑12/A‑15 按记录范围验收。A‑15 冷态超过 100ms 的实测差距保留，不冒称达标或已修所有历史偶发。
- [x] A‑08 真实认证浏览器选附件 → 独立 Agent Worker 实读 → Vercel AI SDK 展示终稿 → 刷新恢复；历史 FINAL／无产物答案引用、直聊／Project 草稿与同 Run 恢复已验。当前源码组合的历史答复再验收据 `f4fb90ddc132b4cb6e69af5b`，整轮及回收通过。
- [x] A‑10 State、Docker／Local 已支持路径的原始字节与不可变版本链有记录证据；本轮补真实 E2B SDK → 官方 envd Docker → 独立 Worker → Storage CLEAN → Canvas 两版／硬刷新恢复。
- [x] A‑13 Telegram／LINE／Slack 开发与本地协议／浏览器闭环；三个真实外部账号按用户裁决暂存下轮。
- [x] A‑14 原生麦克风非空转写进入可编辑草稿；本人编辑并发送按用户裁决暂存下轮，不写作发送已通过。
- [x] Agent `a902131`：默认单元／契约 3605 PASS、24 资源用例未选；另外指定真实 PG／Redis 终态两例 PASS。BFF `6eaa143`：默认 2429 PASS、2 条件跳过；fresh PG 约束验收 PASS。App `28343edd`：Node 22 默认 6519 PASS。格式／类型／契约／构建与独审见对应 PR；不以数量代替产品验收，不重复全量。
- [x] 原 PR 合入各自 `main`：IAM #6 `86f2ed7`、Admin #5 `b6e37fa`、Storage #3 `635b18f`、Agent #46 `87577ea`、BFF #18 `8bead5c`、App #50 `af86159b`。全部保留已验精确子提交可达性。
- [x] A‑16／精确交付组合：Root 原 #66 承载最终固定版本、本清单与收据索引；拓扑、15 条契约边／0 违例及原 checkpoint 通过。最终合并状态以该 PR 及主控收尾回执为准，不另设功能门。
- [x] Task A 专属 envd 容器／镜像、旧验证环境、4 个私有 runner 目录、Task A Root 工作树与两个 Agent 验证工作树已清退；唯一验收资料已迁至权限受限的私有归档并核 SHA。原仓 12 个子仓已按精确 gitlink 同步，本地分支仅 `main`；不移动他人工作树。
- [x] TODO 与 Goal 的本次完成口径已对齐；Task A 每小时自动任务已删除。Goal 在下述原 PR 合并与最终 clean 检查通过后转 complete，不受旧 objective 的历史顺序误导。

**随本 PR 合并执行的 Git 收尾**：Root 原 #66 正常 merge（不绕保护），原仓切回并快进 `main`，仅删除本任务已合并且无后继的分支，再核工作区 clean／精确 pins。此发布时序的事实回执由 GitHub PR 与主控最终核验给出；Capability 外部依赖和下轮真实验收不伪装成已做。

## E2B 本地真实协议收据

- Root `1213099accd3178d28714a67929147af4d319ee3`；Agent `a9021318`／BFF `6eaa143c`／App `28343edd`，子仓干净且与 Root gitlink 精确配对。
- 收据 `884f6bcbb5676f512bf67b6c`，SHA‑256 `6812937fe8ece3c1f4619110896f598cbcc17fb9c017bd26c9ea56eb0d6e08d1`；整轮 PASS、native exit 0、cleanup PASS。
- 官方 envd `0.10.0` arm64，官方二进制 SHA‑256 `ef4ddfd0797a3793a87c5e2a4bdb4167afd60f0c6c604bd918d7ca6c77dce894`，锁定 E2B SDK debug 模式；1 CPU／384 MiB／128 PID、loopback 单端口、无宿主挂载。
- 同一真实 Run 原生 `write_file`／`edit_file` 产出 85／109 字节两个 opaque 版本，实际 Storage 两次上传且 CLEAN；浏览器各取原 SHA，选旧版后刷新保留该版。IAM／Chromium／BFF／PG／Redis／Storage／Scanner／Agent HTTP 与独立 Worker 为真实进程；System／模型／预算／Platform 是明示确定性协议夹具。
- Docker 容器已独立停止并删除，端口关闭；物理清理收据 SHA‑256 `63d700609ab7228198274f0eafff04fb4f81cfe66596d0ab20c0aa923ea155d5`。SDK debug 跳过云控制面，**未验证云创建／回收，不冒称云生命周期通过**。
- 前轮 `b8bd95c9410bf0513094bf5e` FAIL／cleanup PASS：薄测试镜像缺少 `/usr/bin/python3`，补镜像路径后本轮通过。未改生产代码、未放宽产品断言。

## 下轮暂存 TODO（不阻塞本次开发交付）

- [ ] **A‑13／真实渠道账号**：Telegram、LINE、Slack 各补真实账号授权／收发／撤销主路径。本地协议通过不等于真实供应商账号通过。
- [ ] **A‑14／本人语音**：用户主动说短句，编辑转写草稿并显式发送；已有真实非空转写证据复用。不保留录音和口述原文。
- [ ] **可选 E2B 云／完整自托管生命周期**：当实际使用该目标时补创建、重连与独立回收。本轮用户要求的 Docker envd 协议链已通过，不再卡本次开发交付。
- [x] **Capability 自有PR交付**：原 #13 `24094960` 已按用户确认合入原staging接收分支（merge `e068fcaa`），自有分支已清理。#12的后续main交付由其owner管理，本任务不接管、不列为Task A未完成项；Root继续固定已验精确源码，不声称Capability main已包含它。
- [ ] **A‑15 体验余量**：保留冷态约 303～306ms 对 100ms 目标差距及历史偶发可用性诊断，按下一轮需求排序，不无休止扩展本次验收。

## 清理保护边界

- 不操作他人的Root #67、App #49、BFF #17、Storage #2、Capability #12 PR元数据／合并／清理及其工作树。唯一已确认例外：我们的Capability #13按原base正常合入，使#12接收分支前进到e068fcaa；#12本身保持Draft，不合main。
- Billing／System精确源码pins保持；2026-11-11另按独立owner证据通过原PR #4／#2完成main交付，不据此勾掉Task B产品范围。
- 原仓 App 登录失败页的既存未提交修改已保存完整文件、基线与二进制补丁；先核摘要再仅恢复该路径，不整仓 reset。
- 唯一私有验收资料、失败证据与必要复跑脚本迁出任务工作树后再清理，机密不进 Git。GitHub CI 因账户账单／额度未启动，未称 CI 通过、不绕分支保护。

## 文档维护（本次后续收尾）

已用当前产品指南／技术总览承接 Task A结论，退役四份执行方案与两份错误旧拓扑，旧证据从固定 Git版本追溯。App既有 VitePress 门户新增产品使用指南，生成 API参考固定到当前 BFF28.35原件；只更新文档，不增加功能、不部署，不改 Task B。门户 Node22正式 `pnpm check` 通过：lint／类型、54条文档测试、精确来源、确定性参考生成、本地示例、发布策略、构建和站内链接全部通过；Root相关治理302条通过，拓扑／15条契约边／原checkpoint通过。业务源码未改，不重跑已验业务全量。App文档PR #51已合main，Root固定已验 `2b2522b7` 并按原contract证据实际Git blobs重核来源，最终配对随本次Root文档PR交付。

## 对外文档分层（本轮）

- [x] Web公开门户：产品功能按五个子目录分层，API物理目录独立；内部工程资料不发布。
- [x] 导航、搜索输入、生成参考路径、代码示例引用及构建链接检查通过；Node22门户完整检查通过，旧输出路径／symlink／发布负控保留，构建产物分区侧栏及旧页面缺席另核通过。
- [x] App文档PR #52已合main，Root固定已验精确提交 `1fed28b8`，93项App来源用实际Git blobs核对；拓扑、15条契约边／0违例、原checkpoint及相关Root治理通过。

本轮Root文档PR正常合并后同步main并清理仅本轮自有分支，最终状态以该PR／主控收尾回执为准；不动Task B，不部署。

## 仓库维护首批（2026-11-11，独立于已交付 Task A）

范围只含确认无消费者的删除与模块导出收敛，不新增层／协议／Schema，不重开Task A，也不接手Task B。

- [x] Root：退役3个失效或仅报错占位的验证入口及其过时暂停测试，修正脚本入口索引。
- [x] BFF：删除旧Agent列表投影死链及两个无消费者路由判断包装；现役读取／AG-UI／System投影保持，原PR #19已合main，精确已验提交 `0895e254`。
- [x] Web：删除未使用的定时时间formatter，两个仅模块内使用的门户函数不再export；原PR #53已合main，精确已验提交 `b93acbd8`。
- [x] 相关验证：BFF lint／类型／build和330项定向Chat／AG-UI／Nest架构回归通过；Web相关lint、108项定时/UI、类型与门户完整检查通过；Root治理／checkpoint312项及最终拓扑6项通过。入口调用最初漏tsx loader，按正规命令重跑通过；无源代码迁就测试。

用户已确认沿用各仓PR合main并清理本轮分支。Root固定上述精确交付、按383项App/BFF来源引用读取实际Git blobs；15条契约边／0违例及原checkpoint通过。Root最终合并与分支清理由本轮PR／主控收尾回执确认。

开发缓存：App旧Next dev生成类型引用三条已退役认证路由；确认无dev lock占用后只归档移除这份过期类型缓存，正规typegen／类型检查通过。不修改tsconfig、不恢复旧认证、不动其它预览／共享资源。

不动：完整分页核对发现BFF `infrastructure/clients/agent/projection.ts` 与Task B PR #17重叠，故本轮排除；Skills／MCP／Custom API／账户／团队／管理等Task B业务与其PR保留。其它所谓legacy入口若仍有真实调用，不因命名删除。
