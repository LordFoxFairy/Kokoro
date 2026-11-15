# Kokoro · 当前执行 TODO

更新：2026-11-15。此文件只列当前动作、条件项和交付入口；完成过程不再混作待办。

## 当前结论与执行边界

- 已批准的 Task A、Task B、两笔无预占恢复残留、R-06，以及 A-15 非首屏设置 JS 切片已分别交付。
- 上一轮 **A-15 开发态真实环境 Project 冷首屏定位已完成**；开发态启动主线程阻塞段已证，生产源码修复净收益未证，因此没有改业务代码。
- 下方仍保留 **8 项条件性遗留／可选增强**，不是 8 个新故障。A-15 本轮诊断不冒生产提速；更广优化、运行环境和长期审计不自动扩项。
- 不为保持“推进”而重复扫描已交付代码、补重复测试、扩建审计平台或擅定性能指标。条件具备后，只做对应缺口。
- 上轮production诊断／试验已沿Root #98合main `8f266a15`并清本轮资源；当前执行下方代码质量批次，不重跑该实验。

## 本轮已验：执行结果到持久事件／恢复展示

主控唯一writer／Git／台账／验收；agent_event_persistence_review只读Agent持久化与发布错误边界，bff_replay_review只读BFF纯映射／恢复payload。仅沿执行结果→持久事件→恢复展示，不回扫已修输入匹配／scan轮询／Project，不纳入基础设施／运维。

- [x] Agent确认critical stage及前置fence查询普通异常被pump误吞，暂停期无已确认queued行可补；BFF限定映射／replay无确认缺陷，不改不扩扫描。
- [x] 公开invoke暂停路径分别复现stage RED1/PASS1、相邻fence RED1/PASS3（各15未选）；普通OSError归一化、既有typed保identity。stage就地包装，租约查询归一化下沉既有helper，不加层；False／None／已落账网络降级／mark／取消不变。
- [x] 停写输入相关三文件125PASS，4项integration marker排除、409条既有SDK Beta警告；全Ruff／format404／Pyright0错误、offline lock、contract和wheel/sdist通过，包源码核等；两独审CLEAR。不称全默认或真实E2E。
- [x] Agent[#52](https://github.com/LordFoxFairy/kokoro-agent/pull/52)已合main `3c49705d`，树等审定97c24f69，owner topic远近已清。Root59字段精确配对，424真blob／518引用重核、摘要不变，拓扑／15边0违例／checkpoint通过；TODO／CURRENT同步。本Root PR承接最终main与Root topic清理；仅本轮打包输出已清，保留收据和既有build/dist/venv。

## 本轮已验：Agent 核心业务链质量

主控唯一writer／Git／台账／验收；input_tool_review只读输入／工具执行，artifact_terminal_review只读产物／终态。仅沿当前Run→工具／沙箱→FINAL链，不回扫已交付Project，不纳入基础设施／运维／部署。

- [x] 两面各确认一组实质问题：输入glob／grep假空、产物scan尾响应漏判。主控范围内流投影未另确认新问题，不扩扫描。
- [x] 最小用例先RED10／PASS1，60未选；仅修匹配与扫描循环。匹配复用锁定SDK同款wcmatch10.1（已有lock／runtime fingerprint、MIT、Python>=3.9），显式声明既有依赖不升级，不手写glob子集；scan保11读／10次0.5秒预算。
- [x] 两文件71／最终四相关文件102PASS，完整Ruff lint／format404、固定Pyright显式现venv0错误、contract／lock检查、wheel/sdist及两源码／metadata打包核等通过；两独立复核CLEAR，不重复真实外部／全默认。
- [x] Agent[#51](https://github.com/LordFoxFairy/kokoro-agent/pull/51)已main `2aeef82a`、树等审定aa8f0459，两自洽提交且topic远近已清。Root59字段／424真blob／518引用重核，三处实际摘要更新，拓扑／15边0违例／checkpoint通过。本Root PR承接最后main／本轮分支；专用验证产物已清，保留原收据，不清理既有build/dist/venv。

## 本轮已验：Project 业务代码质量（不含基础设施／运维）

用户批准持续打磨业务代码、架构和可维护性；不按模式数量／文件长度制造重构，不重复已交付的性能实验。
本轮只审 Project 主链：主控唯一 writer／Git／验收，startup_quality_review 只读启动依赖，project_state_review 只读读取与状态职责。[报告§27](docs/reports/2026-11-11-typescript-auth-admin-audit.md#27-project-业务代码质量事实退休与数据ui职责2026-11-15)保留具体证据和边界；两项已修，无新的已确认待修项，不冒全仓零缺陷。

- [x] 两个独立面审查完成：rename ACK后精确404漏退休；启动warm函数依赖完整Skills UI且pool读取重复。不扩全仓，不重试已弃拆包。
- [x] rename三等价类先RED1／PASS2（43筛除）后最小分阶段404修复；warm两数据规则先基线通过，再移到同feature具名resource模块复用，不留旧reexport，不改cache/key/准入。
- [x] 相关四文件523PASS，最终hook46／resource13复验、全lint／最终types／architecture50／隔离build通过，两独立复核CLEAR。初次测试夹具类型错误保留后仅修夹具；不跑无关native／模型／性能／默认全量。
- [x] App#66已main f8215c10且树等审定源、App topic远近已清；1582输入冻结核等，单一验证副本已回收。Root精确gitlink／424真blob／97commit引用与拓扑／兼容／checkpoint已验，最终Root出口由本PR承接。

## 本轮已验：A-15 生产构建＋真实后端

[报告 §26](docs/reports/2026-11-11-typescript-auth-admin-audit.md#26-a-15-生产构建连接真实后端单边界试验已撤销2026-11-15)记录接线、两个基线／候选样本与独立CPU归因；没有保留业务源码改动。

- [x] 独立App-only副本production build，复用真实BFF/IAM／已有native开发会话；自有透明代理保canonical origin，不改认证／Cookie，不覆盖正常dev的.next。
- [x] 同Project各2个冷context、间隔65秒，草稿与access200分别记录；API均200、pageerror0、requestfailed0，不冒production登录／进程冷启动／p95。
- [x] 定位启动长任务64～66ms；唯一Skills页面dynamic候选只少4454B压缩JS、script21→22，草稿一快一慢，无一致净收益，已撤销。正常App源码不改，不转试其它页面。
- [x] 恢复副本原源码后一次CPU采样核module factory实例化成本；构建／收据／链接定向检查及只读复核，不跑无关业务全量门。
- [x] TODO／CURRENT／报告同步，三个预览端口关闭、临时会话退出；本Root PR承接最终main／分支及本轮构建副本清理，证据保留。

## 本轮已验：A-15 真实环境 Project 冷首屏

[报告 §25](docs/reports/2026-11-11-typescript-auth-admin-audit.md#25-a-15-真实环境-project-冷首屏定位2026-11-15)记录当前环境、实际数值、失败与不改代码的理由。

- [x] 复用现有真实Web/BFF/IAM，确认Next dev；原开发身份正式native临时会话，逐轮logout，不改账号／权限／业务数据。
- [x] 正确区分真实标题＋可编辑草稿与access200；骨架误判、429及connector502失败样本保留并剔除，不抬限流。
- [x] 一个有效非profile样本：Project GET335.5→374.6ms，草稿443.9ms，启动长任务135ms、解压JS22,143,937B；一次CPU采样核开发态初始化阻塞。不作p95／100ms或生产收益结论。
- [x] 无明确生产修复净收益，保留源码；不删权限、不加缓存、不扩全站。只查相应边界／数值／文档链接，不跑无关全量门。
- [x] TODO／CURRENT／报告同步，独立只读复核测量终点；正常Root PR承接最终main与本轮分支清理，不预写未来merge SHA。

## 上轮已收口：执行清单交接

- [x] 仅核现行遗留表与已记录交付事实，没有重扫业务源码或重跑旧成功链。
- [x] 将已完成过程移出当前 TODO 视图；原记录由下方固定 Git 基线完整保留，不另复制一份历史任务中心。
- [x] 按现有 8 项逐项保留 owner、进入条件和完成边界，不伪称已完成或取消需求。
- [x] 补齐上轮 App #65／Root #95 已合 main 的最终事实；清理旧“本轮待合／机器 active”对当前状态的误导。

本次文档变更经本 Root PR 交付；合入后只清本轮分支，不动业务服务、数据、既有工作树或其他人的工作。

## 条件性遗留（本轮不自动开工）

| 项目／状态 | owner | 下一动作与完成边界 |
| --- | --- | --- |
| 真实MCP／Provider授权末端／条件暂存 | Capability＋目标Provider | 有真实端点及账号授权后，只补真实授权→调用→撤权末端；占位QA已删，不拿example.com造故障。已验控制面/材料边界不重跑 |
| A-13外部渠道／条件暂存 | 渠道owner | Telegram/LINE/Slack按实际使用的渠道，账号授权齐备后补收发/撤权；本地协议证据不冒供应商实测 |
| A-14本人语音／用户择时 | App＋用户 | 用户主动口述→编辑→显式发送；不保留录音或口述原文，沿“稍后验收”安排 |
| 完整E2B生命周期／可选运行环境 | Agent＋环境owner | 确认实际采用云或完整自托管后补创建/重连/独立回收；官方envd Docker已有证据保留，不当完整云验收也不重复跑 |
| A-15后续性能优化／production单边界试验已验 | App＋BFF | 真实owner production启动成本已定位，唯一Skills候选净收益不足已撤销；不把诊断当提速，不自动扩试其它页面／认证／缓存 |
| IAM共享源IP额度／非合作取消语义／容量边界 | IAM及对应写入owner | 有代表负载再核容量；不随意抬限流，不将HTTP取消等同事务硬回滚，不为已验功能再造组合矩阵 |
| 远端CI账单／额度／运维事项 | GitHub账户管理员 | 处理Actions账户条件后让正常CI运行；既存“未启动”不改写绿色、不绕分支保护、不重复push等CI |
| Provider专用长期审计／可选增强 | Capability＋Admin | 只有明确产品需求后立项；当前状态/receipt不称长期审计，现IAM/CustomAPI审计不重做 |

**保持关闭／不纳入本轮**：真实支付未接入，不部署；Mori无本轮任务。

非合作取消的已知边界保留：HTTP 取消不等于下游事务硬回滚；不为此扩建取消框架或声称任意下游均可回滚。
两笔无预占恢复残留已审计关闭，旧 usage unknown／空 ACK 原事实保留，不伪造零用量。
历史 30 积分资金事项另案保留，不与这两笔无 admission 候选混算，不自动扩查、追加或回收资金。

## 已交付入口（不重复开工）

| 交付 | 最终出口与证据 |
| --- | --- |
| Task A／Task B 已批准范围 | [Root #67](https://github.com/LordFoxFairy/Kokoro/pull/67) 已合 main `91b54d74`；[技术总览](docs/kokoro-handbook/technical/00-system-overview.md)、[原 Task B 功能交接](docs/handoffs/2026-10-30-task-b-capabilities-account.md)、下方历史基线保留具名旅程和接受的边界 |
| 两笔无预占恢复残留 | [Root #93](https://github.com/LordFoxFairy/Kokoro/pull/93) 已合 main `3960b351`；[报告 §7](docs/reports/2026-11-14-historical-financial-unknown-readonly.md#7-2026-11-15-实际闭环与交付收据)；原命令防迟到和独立审计关闭，不改资金／不造零用量 |
| R-06 GitHub 单一发行 | shared #2／App #64／[Root #94](https://github.com/LordFoxFairy/Kokoro/pull/94) 已合 main；`@lordfoxfairy/i18n@0.1.0`，无 CNB 活接线；[方案与验证](docs/superpowers/plans/2026-11-15-r06-i18n-publication.md) |
| A-15 非首屏设置 JS 切片 | App #65／[Root #95](https://github.com/LordFoxFairy/Kokoro/pull/95) 已合 main `8f68f9a3`；[报告 §24](docs/reports/2026-11-11-typescript-auth-admin-audit.md#24-a-15-project-首屏非关键设置-js2026-11-15)。受控 production 首屏少 39,126B encoded JS；不是 live/p95/冷100ms 或完整 A-15 达标；Root/App 本轮分支与临时验证副本已清 |
| 更早 R-01～R-16／UI／文档收口 | [既有报告](docs/reports/2026-11-11-typescript-auth-admin-audit.md)与固定历史基线承接，不把历史“未验／待合”当当前状态 |

[精简前完整 TODO（固定交付基线 8f68f9a3）](https://github.com/LordFoxFairy/Kokoro/blob/8f68f9a3eb6d67b9f35c5e49e1f40d1955f7a07a/todo.md)保留逐项过程、失败与收据边界；[CURRENT](docs/CURRENT.md)保留时间序列，历史状态只代表记录当时，不覆盖本清单。

## 本地保留与清理边界

当前交付 checkout 的干净／gitlink 配对结论以各轮最终回执为准，不声称整台机器所有旧工作区为空。

- 不删除 ignored 运行配置、验证收据、数据库／数据卷、聊天记录或归属未明的旧 worktree。
- App 旧 `feat/mcp-api-management`、BFF 旧 `codex/task-b-owner-current` 被既有 worktree 占用，保留待交接，不是未结束的远端 PR。
- BFF 归档 `codex/archive-bff-mcp-closure-777325d` 有 main 未包含提交；其他旧 App／Storage 工作区有未交接 diff 或独有提交，均不动。
- Mori／System／Billing 按固定 gitlink 的 detached 不等于脏仓，不为整理擅自切换。
