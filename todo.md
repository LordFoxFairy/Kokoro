# Kokoro · 当前维护与暂存 TODO

## 当前裁决与范围

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
- [ ] **Capability 外部依赖**：原 #13 `24094960` 仍以他人 #12 staging 为 base；保留两 PR 和远端分支。待 #12 负责人收口后再把 #13 正常合入 main；不 retarget 偷带 Task B。Root 继续固定已验精确 #13 提交，本次不声称它已合 main。
- [ ] **A‑15 体验余量**：保留冷态约 303～306ms 对 100ms 目标差距及历史偶发可用性诊断，按下一轮需求排序，不无休止扩展本次验收。

## 清理保护边界

- Task B Root #67、App #49，及独立 BFF #17／Storage #2／Capability #12 和其他人的 Skills／MCP 工作树不动。
- 继承的 Billing／System 精确 pin 不在各自 main，不借 Task A 合并其独立工作；保持 Root 锁定版本。
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
