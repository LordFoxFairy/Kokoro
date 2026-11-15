# Kokoro · 当前执行 TODO

更新：2026-11-15。此文件只列当前动作、条件项和交付入口；完成过程不再混作待办。

## 当前结论与执行边界

- 已批准的 Task A、Task B、两笔无预占恢复残留、R-06，以及 A-15 非首屏设置 JS 切片已分别交付。
- 本轮 **A-15 真实环境 Project 冷首屏定位已完成**；开发态启动主线程阻塞段已证，生产源码修复净收益未证，因此没有改业务代码。
- 下方仍保留 **8 项条件性遗留／可选增强**，不是 8 个新故障。A-15 本轮诊断不冒生产提速；更广优化、运行环境和长期审计不自动扩项。
- 不为保持“推进”而重复扫描已交付代码、补重复测试、扩建审计平台或擅定性能指标。条件具备后，只做对应缺口。
- 本轮 Goal：真实环境定位一个瓶颈，有明确收益才保留最小修复；相关验证后 PR→main，清理本轮分支。其他条件项不动。

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
| A-15后续生产性能优化／本轮诊断已验 | App＋BFF | 开发态启动主线程瓶颈已定位，未证明生产源码修复收益；只有代表性production＋真实owner单变量对照明确净收益后才改，不自动扩全站 |
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
