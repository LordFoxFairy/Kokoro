# Kokoro · 当前执行 TODO

更新：2026-11-12。唯一执行清单；本轮基线Root `07241f03`，不重开已交付Task A，不重复扫描凑问题。

## 当前 Goal：Agent 真实闭环 → AG-UI单轨呈现 → 工作台首页

机器 Goal 已创建为 **active**（动态状态以工具为准）。首要目标不是再造框架，而是把现有可插拔Backend、Skills/MCP、Storage及事件链正确接齐，完成正常持久环境的一条真实任务。Task B／Mori／部署不动。

| 阶段 | 当前状态／完成条件 | 负责人／写区 |
| --- | --- | --- |
| G0 设计与范围 | **已收敛、分片实施**：[实施方案](docs/superpowers/specs/2026-11-12-agent-runtime-closure-design.md)沿现BackendProtocol／registry；运行中发现的准入补口已过§12独审，不引入新owner／公开字段／Schema | 主控唯一台账/Git/集成；G3生产按SDK引擎与UI终态隔离写区，具名agent独审，资源apply主控串行 |
| G1 正常运行＋Agent首纵切 | **阶段通过**：正常native登录、真实模型/Skill/MCP/Docker/FINAL与刷新首片已验；普通脚本生成→失败后同会话仅交付补缺已验，分别保留两Run事实。现chat-default已沿原policy指向已验revision，正常resolve及新任务Default chat已核。不抹去历史失败或额外路径检查exit1 | Agent现配置／Factory／profile／sandbox；Root恢复既有本地材料／资源与实际验收；不动Task B控制面 |
| G2 产物来源闭合 | **首片阶段通过**：真实报告过程版本与FINAL分别取证，同字节下载/刷新已核；普通脚本源到FINAL的跨Run恢复已到下载。不把scratch output_path与同名workspace文件冒同源。指定过程版本直接交付同字节FINAL需沿原owner API裁决后再实施，不暗加复制／工具入口 | Agent／Storage现交付与不可变版本消费者；主控把控设计增量 |
| G3 AG-UI／AI SDK | **推进中／设计§13已收敛**：live目前丢SDK chunks、正文仍自拼，历史才使用SDK。推荐现decoder→mapper→SDK reader唯一正文装配；engine仍管命令／cursor／恢复。活动显示按稳定业务ID收敛；准入失败文案应覆盖资金／权限，不把资金拒绝只解释成模型权限；不暴露raw reasoning/tool payload、不再造useChat提交／恢复链 | SDK引擎：agent_runtime_closure；UI终态/文案与集成：主控；独审：agent_spec_review。同文件Share实际hunk保护，现contract默认不增量 |
| G4 首页与文档／集成收口 | **候选方向**：/app保持单Composer，通用任务先行、工具按需展开；补真实加载／错误、窄屏／键盘／长草稿。参考Manus公开说明，可视对照尚未做。更新产品/API适用文档（Agent内部API文档2处已存历史v2 proto链接在此收尾，不恢复旧协议），停写验收后自有PR合main／清本轮topic | App首页已有组件/CSS，Root精确组合；不改后台／营销站或重做品牌 |

验证只补本次独有缺口：首片配置与冻结/lease、真实Docker隔离与回收、FINAL字节、正常浏览器主旅程；AG-UI再承接断线／刷新／审批／取消／迟到的现有必要风险，不另铺测试平台。不以数目、ready或fixture冒真实供应商闭环。

### 本轮实际运行进展（2026-11-12）

- **已推源码候选**：Agent `ea20468`（生产修复 `c2c563e`，后继仅README）／原[Draft #47](https://github.com/LordFoxFairy/kokoro-agent/pull/47)；BFF `ee62845`／原[Draft #27](https://github.com/LordFoxFairy/kokoro-bff/pull/27)。Root候选 `6d94d170`／[Draft #87](https://github.com/LordFoxFairy/Kokoro/pull/87)精确记录两gitlink；App仍main `026a7d12`，只有Next自动类型引用差异。源组件门沿已冻结证据，不重复全默认；Root拓扑／15 edges兼容／原checkpoint通过，不等于全部Goal交付。
- **正常持久环境已恢复**：七个核心HTTP owner ready，独立官方Worker运行；复用原PG/Redis/MinIO/Scanner，不清卷/重建。专用开发账号原IAM注册/SMTP验证/正常浏览器登录，非platform admin，仅现动态Skill创作/安装角色。本地Storage备份后按Prisma exact diff补枚举/两列，后置diff为空；Capability精确已知parent经正式installer回填原唯一绑定，后置canonical通过。现MCP元数据/授权两surface缺项亦已补齐；恢复原keyring，不新建认证层。
- **真实Skill/MCP已接入**：structured-report经正常导入安装并enabled；真实Context7握手/发现两工具/连接与本次实际文档查询成功。站点策略只补App已支持的`en`，解决浏览器locale导致manifest403而隐藏入口；正式navigation配置只补现mcp入口，不改App默认fallback。正常Composer可显式选择Skill、MCP和模型。
- **首份真实报告已闭合**：`conv_49012e43`首次因未注册surface assembly_failed/模型0派发，保留失败；补配置后Regenerate completed，冻结新模型/Skill1/MCP1/Docker，12次真实模型派发封存。报告由native write_file落实际workspace并deliver；FINAL/CLEAN **1469bytes**，工作区版本/实际文件/浏览器下载SHA `de656263…ae12cf4`核等，正文与交付刷新保持；容器已清理。额外绝对`/outputs`命令检查exit1/路径错误如实保留，未冒所有工具通过。
- **普通脚本补缺已到交付**：`conv_c84850da` plain execute（无Custom API/output_path）exit0，实际`/workspace/outputs`生成108bytes/SHA `49daae46…7cde86e`。随后余额不足造成明确not_dispatched拒绝，不归脚本失败；只补一次收尾dev额度后，同会话新请求仅deliver既存文件，不重跑脚本/MCP。下载与原脚本/跨失败Run保留文件同字节，刷新保持；收尾Run completed、仅deliver1/execute0/MCP0，2次调用capture8/release12/pending0，cleanup完成；不把两Run写成单Run成功。
- **资金边界**：累计130个有receipt/ledger/audit的非现金开发积分，不是真实支付。首成功Run12项ACK全部captured，capture54/release66/pending0；脚本失败Run前5项capture17/release33，随后余额拒绝明确封存。原供应商overload的held30与两条旧requested_unknown依原恢复语义保留，不猜零/退款、不混算成当前成功Run成本。正常chat-default原policy已指向已验revision，display名为Default chat；旧默认标志一直为true，无空窗，不造两label原子切换API。
- **下一执行**：G1/G2收据已收拢，进入G3 SDK实时正文单轨、历史终态/余额拒绝展示；再做G4首页/产品API文档/自有PR合main收尾。真实历史可复用，不重跑MCP或全量测试凑数。Task B／Mori／部署不动；所有凭据、备份、操作脚本和原始收据仅本地ignored。

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
