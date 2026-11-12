# Kokoro · 当前执行 TODO

更新：2026-11-12。唯一执行清单；本轮基线Root `07241f03`，不重开已交付Task A，不重复扫描凑问题。

## 当前 Goal：Agent 真实闭环 → AG-UI单轨呈现 → 工作台首页

机器 Goal 已创建为 **active**（动态状态以工具为准）。首要目标不是再造框架，而是把现有可插拔Backend、Skills/MCP、Storage及事件链正确接齐，完成正常持久环境的一条真实任务。Task B／Mori／部署不动。

| 阶段 | 当前状态／完成条件 | 负责人／写区 |
| --- | --- | --- |
| G0 设计与范围 | **设计已独审通过，待书面审阅**：已定向核源码／依赖／Task B实际hunk；[首片候选方案](docs/superpowers/specs/2026-11-12-agent-runtime-closure-design.md)待审阅。明确复用BackendProtocol／原registry，不新沙箱平台 | 主控唯一writer；agent_runtime_closure／agui_closure_design／workbench_home_design只读调查 |
| G1 正常运行＋Agent首纵切 | **待设计门**：持久配置／队列归属核实后恢复正常服务与Worker；普通任务不选Custom API也能用已配隔离backend。真实模型→文档型Skill→已授权MCP→普通execute真实文件→CLEAN/FINAL→浏览器结果／刷新；不能用协议fixture替代模型 | Agent现配置／Factory／profile／sandbox；Root管实际资源与验收；不改Task B控制面 |
| G2 产物来源闭合 | **待G1**：过程文件与FINAL两种事实分别验收，exact run/version/bytes可恢复；不把scratch output_path与同名workspace文件冒同源。指定过程版本直接交付同字节FINAL需沿原owner API裁决后再实施，不暗加复制／工具入口 | Agent／Storage现交付与不可变版本消费者；主控把控设计增量 |
| G3 AG-UI／AI SDK | **候选方向已核**：live目前丢SDK chunks、正文仍自拼，历史才使用SDK。推荐现decoder→mapper→SDK reader唯一正文装配；engine仍管命令／cursor／恢复。活动显示按稳定业务ID收敛；不暴露raw reasoning/tool payload、不再造useChat提交／恢复链 | App独立切片；同文件Share实际hunk保护，现contract默认不增量 |
| G4 首页与文档／集成收口 | **候选方向**：/app保持单Composer，通用任务先行、工具按需展开；补真实加载／错误、窄屏／键盘／长草稿。参考Manus公开说明，可视对照尚未做。更新产品/API适用文档，停写验收后自有PR合main／清本轮topic | App首页已有组件/CSS，Root精确组合；不改后台／营销站或重做品牌 |

验证只补本次独有缺口：首片配置与冻结/lease、真实Docker隔离与回收、FINAL字节、正常浏览器主旅程；AG-UI再承接断线／刷新／审批／取消／迟到的现有必要风险，不另铺测试平台。不以数目、ready或fixture冒真实供应商闭环。

### 已确认的边界

- 沙箱本来可插拔：已有state／local_shell／docker／e2b／custom与SDK接口。修的是普通任务装配耦合；产品不新增宿主执行兜底。
- 原Agent HTTP私有持久配置仍在；缺目标位置的.env.local不等于全部配置丢失。Worker配置按正式字段合齐，旧process registry仅历史，不当当前启动证据。原配方在装配前核request／lease并fail closed，保留它，不为首片增新repository读取或跨配置迁移。
- Skill虚拟路径不等于容器挂载；首片不造任意包脚本自动执行平台。MCP复用现连接和授权，不接管Task B配置/管理。
- AG-UI已有safe activity／interaction／delivery，先用已有事实；未公开VM生命周期就不画假“已启动/回收”。
- Task B #49首页候选5文件无file diff；client.ts有Share hunk、conversation-thread有props hunk，实施与集成前再核，不能整文件覆盖。

## 上批已交付，不重跑

App #58、Root #86已合main；Root main07241f03／App026a7d12，已清本轮分支／预览与临时目录，证据归档。门户产品/API分层、来源/生成/示例/导航与实际浏览器已验；A-15当前Project两对与阶段补口已验，冷rAF252～276ms未达100ms。它是后续体验余量，不挡本轮真实Agent主线，也不冒性能达标。详情见[报告§23](docs/reports/2026-11-11-typescript-auth-admin-audit.md#23-a-15当前观测与公开文档收拢)。

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
| A-15体验余量 | App owner；当前Project两对冷rAF252～276ms，100ms冷目标未达。保留已定位DCL→hydration／首GET区间，本轮只随首页真实影响补验，不抢Agent闭环主线 |
| IAM共享源IP额度／非合作写入取消 | 原owner容量与运行语义边界；代表性负载核验另定，不随意抬限流，不宣称HTTP取消等于事务硬回滚 |

真实支付关闭，未部署；上述不作为本轮独立代码故障或新增阻塞。

## 已交付事实入口

上轮统一维护的两个独立缺陷已通过App #56／BFF #26／Root #83交付并清理自有分支；本轮不重跑其完整门。[报告§21](docs/reports/2026-11-11-typescript-auth-admin-audit.md#21-统一维护goal与集中批次)保存RED／GREEN与验证边界；更早R-01～R-16及上传入口结果见报告§13～20。Task A产品收据见[技术总览](docs/kokoro-handbook/technical/00-system-overview.md)和[CURRENT](docs/CURRENT.md)，历史不再平铺为当前TODO。
