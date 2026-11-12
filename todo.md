# Kokoro · 当前维护 TODO

核对日期：2026-11-12（America/New_York）。本轮基线 Root `6a61e1bf`；本文件是唯一执行清单。只推进已批准的 A-15 观察与对外文档收拢，不重新扫描凑问题、不重开已交付 Task A。机器 Goal 当前查询为空，以下是本轮执行目标，不冒称另有 active／blocked Goal。

## 本轮目标：当前性能证据与可读的公开文档

主控负责取舍、写入、验收、Git 与本台账；只读代理 `r09_governance_calibration` 复核 A-15 证据，`a03_read` 复核公开文档与真实认证边界。Task B／Mori／部署不动。

- [x] A-15旧证据重新定性：约303～306ms是已有登录态新context的页面可用耗时，不是单API／进程冷启动或生产p95；不据此先改认证缓存。
- [x] 当前精确组合真实Project两对采样：Root6a61／Appc3b09／BFF7c503／IAM40cda；冷306／296ms、热15／14ms，native/browser/cleanup通过。关键GET在+193／183ms发起，headers+237／234ms；缺精确request-id不硬归因BFF/IAM。非关键owner未配置503明确保留。
- [x] 文档最小片实现并验收：App #58源码818141e9、merge026a7d12同树，已合main；产品功能目录保留，外部skill.list与第一方任务参考分开；改旧Bearer／上传响应／未声明control；生成资源目录与操作深链，保209操作／446schemas。门户check及真实浏览器／窄屏／浅深代码对比度通过，独审CLEAR。
- [x] A-15阶段缺口已补：原业务oracle与source gate保留；Roota5b9／App818141的两对收据c1694f00整体／cleanup通过。document首字节18～22ms、DCL52～55ms，精确GET发起198～203ms，rAF UI-ready252～276ms；原断言315～320ms。只定位，不把观测开销算作生产固定等待，也不编造优化收益。
- [x] 集成与清理门已验：App #58已合main／自有topic已清；Root [#86](https://github.com/LordFoxFairy/Kokoro/pull/86)固定App026a7d12，93项来源／85个Git blobs重核、拓扑／15边0违例／原checkpoint通过。私有证据已归档、预览与两处本轮临时目录已回收；Root合入状态以该PR为准，最终本地main／topic出口由主控回执确认，不为PR自己的状态再造后继文档PR。

本轮证据与范围见[报告§23](docs/reports/2026-11-11-typescript-auth-admin-audit.md#23-a-15当前观测与公开文档收拢)。100ms冷态目标尚未达成，不因脚本PASS冒称性能闭环。文档与owner契约认证声明纠正是两项事实，不伪装全部接入已经统一。

## 本轮外已交付

R-06未使用web-core分片（App #57／Root #85）已交付；归档登录失败页WIP已由main祖先承接，不恢复旧补丁。原审计分类依据见[报告§22](docs/reports/2026-11-11-typescript-auth-admin-audit.md#22-剩余todo归属与下一轮goal)，不重复完整验证。

## 需原 owner 承接，不进入本轮写区

| 项目 | 负责人／阻断点与下一动作 |
| --- | --- |
| R-06在用i18n正式迁移 | shared发行owner＋App consumer owner；先确认`@kokoro`包scope／现有registry／不可变版本和读权限／发布授权，再原子切manifest-lock-Docker并删i18n副本；当前不以本地bridge冒正式发行 |
| R-03 Admin菜单／旧页面正式接线 | Task B Admin owner；沿原后台PR完成真实业务，不接管、不造成功页 |
| R-07 Capability contract-check写副作用余项 | Capability owner／Task B #12；normalizer与现组合生成物相连，需在该组合做只读check。Storage部分已完成，不重复修 |
| R-14 MCP OAuth DNS pin生命周期 | Capability owner／Task B #12；client无直接hunk不代表composition无依赖，不从独立main小补丁冒称Root组合已修 |
| BFF canonical认证metadata／README／INDEX清理 | Task B BFF owner／#17；普通产品security仍是旧Bearer，与native Cookie／Origin运行不符；版本行及部分文档有实际重叠hunk，交原PR版本化纠正。本轮门户显式披露，不手改生成security，不按旧清库指导操作数据 |
| Admin回环／Hub职责收敛 | Task B App／BFF／Admin owner；需统一共享登录、管理权限和路由映射，不加Admin BFF或万能proxy |

Capability Root pin `24094960`来自已交付#13，已合入#12头`e068fcaa`但未合main；比main多37提交。仅看同名文件或零patch都不足以判定可独立交付；本轮不动其PR／分支／工作树，也不把Task B带入main。

原审计15项主线编号仍为**11项收口／4项遗留**（R-03、R-14待原owner，R-06／R-07部分完成）；上表两条文档／链路交接与编号存在重叠，不叠加成新故障总数。Mori R-05不属本轮。

## 已接受边界与产品暂存

| 项目 | owner／恢复前置 |
| --- | --- |
| A-13真实外部渠道 | 渠道owner；Telegram／LINE／Slack真实账号授权、收发、撤权条件齐备后验收，当前本地协议证据不冒真实供应商 |
| A-14本人语音 | 用户＋App owner；用户方便时主动口述、编辑并显式发送，沿此前“稍后验收”，不保留录音／原文 |
| 可选完整E2B生命周期 | Agent／运行环境owner；实际采用云或完整自托管时补创建／重连／独立回收，既有官方envd Docker证据不重跑 |
| A-15体验余量 | App owner；本轮当前两对冷306／296、热15／14ms，已补浏览器阶段，rAF252～276ms；下一独立性能切片仅沿DCL→hydration／首关键GET定位，100ms冷目标未达，未证明需要改IAM／缓存／架构 |
| IAM共享源IP额度／非合作写入取消 | 原owner容量与运行语义边界；代表性负载核验另定，不随意抬限流，不宣称HTTP取消等于事务硬回滚 |

真实支付关闭，未部署；上述不作为本轮独立代码故障或新增阻塞。

## 已交付事实入口

上轮统一维护的两个独立缺陷已通过App #56／BFF #26／Root #83交付并清理自有分支；本轮不重跑其完整门。[报告§21](docs/reports/2026-11-11-typescript-auth-admin-audit.md#21-统一维护goal与集中批次)保存RED／GREEN与验证边界；更早R-01～R-16及上传入口结果见报告§13～20。Task A产品收据见[技术总览](docs/kokoro-handbook/technical/00-system-overview.md)和[CURRENT](docs/CURRENT.md)，历史不再平铺为当前TODO。
