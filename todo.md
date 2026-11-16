# Kokoro · 当前执行 TODO

更新：2026-11-16（America/New_York）。仅维护下一动作、进入条件和完成边界；详细完成过程由固定 Git 历史保留。

## 当前结论

- 已批准的 Task A／Task B、两笔无预占恢复残留、R-06、核心链质量修复及 H-01 metadata 窄切片已交付。
- 剩余 **8 项条件性遗留／可选增强** 见下表；当前没有已确认、已授权且可脱离这些条件独立实施的代码项。它们不是 8 个新故障，也不因暂存而视作已经完成。
- A-15 已定位生产启动成本，唯一候选净收益不足已撤销；不重复该试验，不为保持推进而扫描已交付代码或新增设计、缓存、测试矩阵。
- H-01 只交付本人草稿 metadata 编辑与 fresh 读回。**cover／discard／AI 仍排除**；不从旧代码或 API 的存在推导新增产品承诺。

## 本轮收口：执行清单与交付事实一致

本轮唯一写区为 Root `todo.md`、`docs/CURRENT.md`。主控负责编辑、验证与 Git；两只读 agent 分别核遗留进入条件及精确交付记录，不检查业务源码或重跑旧旅程。

- [x] 仅核现有8项遗留和H-01排除边界，区分外部条件、产品决定与已完成事项。
- [x] 登记 Root #104／#105 和 App #67 的实际合并出口，删除旧 worktree／分支仍待清理的陈旧提示；不把归档引用当活跃工作。
- [x] 已完成长过程改为下方固定 Git 历史入口，保留原失败与证据，不制造第二套台账。
- [x] 文档diff／8个本地链接与锚点／2个固定历史对象检查通过；直接相关Root治理测试8 PASS，独立复核CLEAR。本轮沿Root文档PR交付，不扩大验证范围。

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

## 最近交付与证据入口

| 交付 | 已观察到的出口与范围 |
| --- | --- |
| H-01 本人草稿 metadata | [App #67](https://github.com/LordFoxFairy/kokoro-app/pull/67) → `a516cfcb991a080baaf51fef1c070ff57854db0c`；[Root #105](https://github.com/LordFoxFairy/Kokoro/pull/105) → `3c66f1739f8fff950acd630fd5b78d6238e97d10`。精确 gitlink、保存／读回／刷新及中法语窄屏已验；不扩封面／discard／AI。开发角色临时QA权限已还原，不修改默认成员权限。原失败与子步骤边界见 CURRENT |
| 历史源码／旧 worktree 收拢 | [Root #104](https://github.com/LordFoxFairy/Kokoro/pull/104) → `5a6c895cec76f0278a7488605604c1229c024418`；[逐项报告](docs/reports/2026-11-15-historical-work-reconciliation.md)。旧 checkout 已退役，源码通过 Git 归档保留；不整批恢复旧代码 |
| 真实浏览器核心链 | [Root #103](https://github.com/LordFoxFairy/Kokoro/pull/103) → `138201388931a8fa3198c9298eb7f9cf341e1c02`。当前组合任务→工具→产物下载→刷新恢复已验；资金授权、原失败和未验边界仍由原收据承接，不重复执行 |
| Task A／Task B 已批准范围 | [Root #67](https://github.com/LordFoxFairy/Kokoro/pull/67)；[系统总览](docs/kokoro-handbook/technical/00-system-overview.md)、[Task B 原功能交接](docs/handoffs/2026-10-30-task-b-capabilities-account.md)保留范围，不据旧 OPEN 文字重新开工 |
| 两笔无预占恢复残留 | [Root #93](https://github.com/LordFoxFairy/Kokoro/pull/93)；[报告§7](docs/reports/2026-11-14-historical-financial-unknown-readonly.md#7-2026-11-15-实际闭环与交付收据)。防迟到与独立审计关闭，不改资金、不造零用量 |
| R-06 GitHub 单一发行 | shared #2／App #64／[Root #94](https://github.com/LordFoxFairy/Kokoro/pull/94)；`@lordfoxfairy/i18n@0.1.0`，无 CNB 活接线；[方案](docs/superpowers/plans/2026-11-15-r06-i18n-publication.md) |
| A-15／后续代码质量批次 | [已交付详细记录（固定基线）](https://github.com/LordFoxFairy/Kokoro/blob/3c66f1739f8fff950acd630fd5b78d6238e97d10/todo.md)、[报告](docs/reports/2026-11-11-typescript-auth-admin-audit.md)保留实际收益、撤销试验、失败、具名验证和各仓出口；诊断不冒提速 |

[CURRENT](docs/CURRENT.md)维护时间序列；旧段仅代表记录当时，当前交付和清理结论以上述后继事实为准。[更早完整清单](https://github.com/LordFoxFairy/Kokoro/blob/8f68f9a3eb6d67b9f35c5e49e1f40d1955f7a07a/todo.md)继续保留，不复制历史为新待办。

## 本地保留与清理边界

- 上轮最终回执已核 Root／App 同步 main、工作区干净、本轮远近 topic 清理及精确 gitlink；不从“PR已合并”单独推导整个机器无遗留。
- 七个旧 worktree 与已核过时分支名已清理，不再列作占用待交接。源码 archive refs、私有配置、ignored 证据保留；它们不是活跃分支或待合 PR。
- 历史源码恢复入口见专项报告，不删 archive refs、不做 GC／历史重写、不把旧树整批合回 main。
- Mori／System 等固定 detached pin 不等于脏仓，不为整理擅自切换或更新 gitlink。
- 不删除 ignored 运行配置、验证收据、数据库／数据卷、聊天记录或归属未明的工作；本轮不操作业务服务、模型、权限、资金或部署。
