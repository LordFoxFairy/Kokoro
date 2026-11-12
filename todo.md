# Kokoro · 当前维护 TODO

核对日期：2026-11-12（America/New_York）。本轮基线Root `b24b6146`；本文件是唯一执行清单，历史实施与证据见[维护报告](docs/reports/2026-11-11-typescript-auth-admin-audit.md)。不重新扫描源码凑问题，不重开已交付Task A。

## 本轮 Goal：既有遗留收口与 R-06 独立分片

机器Goal动态状态以工具为准；本批只收口现有队列归属、WIP与可独立交付分片，不以此宣布R-06整体迁移完成。主控负责设计取舍、验收、Git与本台账，不动Task B／Mori／部署／共享数据。

- [x] 核上轮出口：App #56、BFF #26、Root #83均已MERGED；Root main `b24b6146`，12子仓clean／精确配对。不是“等待上轮合并”。
- [x] 核原未完成项的真实文件与分支依赖，按“可独立／原owner／已接受暂存”分类；只读角色分别为`a03_read`（归档WIP）、`r09_governance_calibration`（R-06／R-07／R-14）。
- [x] 归档WIP对照完成：原生登录失败页意图早已进入main；不恢复旧补丁，保留私有归档。
- [x] R-06前置核验：web-core／i18n源码与入口等价，无Task B实际hunk；正式包发行方式尚未确定，tsconfig也非等价副本。
- [x] **R-06最小方案已收敛**：未使用web-core不必先发行，直接退役App副本；在用i18n沿既定私有包／精确版本／lock目标，需shared发行owner提供可核验版本与读取权限后再迁。裸sibling bridge不满足现单仓CI／Docker；不新建registry／产物平台，不自动发布。
- [x] **独立代码分片已交付**：App #57源码c3b09e4b已合main并清理topic，删未用web-core依赖／三文件副本／Docker COPY，保shared／Mori／i18n／tsconfig。offline frozen安装、相关67项／lint／types／build及独审通过；无sibling仅验证frozen锁解析、Docker仅静态COPY检查，不冒镜像或完整独立安装。Root本PR配对精确源并核组合；最终Goal只在合入与clean出口后结束。

本轮分类与依据见[报告§22](docs/reports/2026-11-11-typescript-auth-admin-audit.md#22-剩余todo归属与下一轮goal)。R-06现为部分完成，在用i18n余项交发行owner，不在本Goal中无条件发布；不重复创建Goal或为暂存项标blocked。

## 我们可独立推进

| 项目 | 状态／下一动作 |
| --- | --- |
| R-06无消费者分片 | **已交付**。App #57移除未使用web-core；未切在用i18n，未扩运行边界。正式发行余项见下方owner门 |
| 登录失败页归档WIP核实 | **已完成**。目标`src/app/auth/sign-in/failed/page.tsx`；de40f9c3已落地，后继dead1843／bfb749c3完成native-only与canonical消费，均为当前App祖先；保留归档，不恢复旧fallback |
| 上轮最终回执／本轮台账整理 | **已核实**。当前队列去除过期“待合并／待核实”，完成记录收至报告；Root #84承接分类，当前Root PR配对App #57精确源码与来源 |

## 需原 owner 承接，不进入本轮写区

| 项目 | 负责人／阻断点与下一动作 |
| --- | --- |
| R-06在用i18n正式迁移 | shared发行owner＋App consumer owner；先确认`@kokoro`包scope／现有registry／不可变版本和读权限／发布授权，再原子切manifest-lock-Docker并删i18n副本；当前不以本地bridge冒正式发行 |
| R-03 Admin菜单／旧页面正式接线 | Task B Admin owner；沿原后台PR完成真实业务，不接管、不造成功页 |
| R-07 Capability contract-check写副作用余项 | Capability owner／Task B #12；normalizer与现组合生成物相连，需在该组合做只读check。Storage部分已完成，不重复修 |
| R-14 MCP OAuth DNS pin生命周期 | Capability owner／Task B #12；client无直接hunk不代表composition无依赖，不从独立main小补丁冒称Root组合已修 |
| BFF README／INDEX首读清理 | Task B BFF owner／#17；过期当前态／旧版本／清库指导有实际重叠hunk，随原PR收敛，不按旧文字操作数据 |
| Admin回环／Hub职责收敛 | Task B App／BFF／Admin owner；需统一共享登录、管理权限和路由映射，不加Admin BFF或万能proxy |

Capability Root pin `24094960`来自已交付#13，已合入#12头`e068fcaa`但未合main；比main多37提交。仅看同名文件或零patch都不足以判定可独立交付；本轮不动其PR／分支／工作树，也不把Task B带入main。

原审计15项主线编号仍为**11项收口／4项遗留**（R-03、R-14待原owner，R-06／R-07部分完成）；上表两条文档／链路交接与编号存在重叠，不叠加成新故障总数。Mori R-05不属本轮。

## 已接受边界与产品暂存

| 项目 | owner／恢复前置 |
| --- | --- |
| A-13真实外部渠道 | 渠道owner；Telegram／LINE／Slack真实账号授权、收发、撤权条件齐备后验收，当前本地协议证据不冒真实供应商 |
| A-14本人语音 | 用户＋App owner；用户方便时主动口述、编辑并显式发送，沿此前“稍后验收”，不保留录音／原文 |
| 可选完整E2B生命周期 | Agent／运行环境owner；实际采用云或完整自托管时补创建／重连／独立回收，既有官方envd Docker证据不重跑 |
| A-15体验余量 | App／BFF／IAM owner；下一轮产品性能范围明确后处理冷态约303～306ms与100ms目标差距，不先改缓存／架构 |
| IAM共享源IP额度／非合作写入取消 | 原owner容量与运行语义边界；代表性负载核验另定，不随意抬限流，不宣称HTTP取消等于事务硬回滚 |

真实支付关闭，未部署；上述不作为本轮独立代码故障或新增阻塞。

## 已交付事实入口

上轮统一维护的两个独立缺陷已通过App #56／BFF #26／Root #83交付并清理自有分支；本轮不重跑其完整门。[报告§21](docs/reports/2026-11-11-typescript-auth-admin-audit.md#21-统一维护goal与集中批次)保存RED／GREEN与验证边界；更早R-01～R-16及上传入口结果见报告§13～20。Task A产品收据见[技术总览](docs/kokoro-handbook/technical/00-system-overview.md)和[CURRENT](docs/CURRENT.md)，历史不再平铺为当前TODO。
