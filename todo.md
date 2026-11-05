# Task A · TODO（2026-11-05）

**当前：G0～G3／C‑1～C‑4 前置清理闭环。** 精确组合 `6db2028d` 的已发布契约 15/15、八个数据 owner 同库同时 ready；已验登录和 Run 主链复用原收据。**A‑01 和 A‑02 已验收，A‑07 已通过原生浏览器，A/B 已在本地正式登记**；Task A 产品项未闭环。唯一执行清单在本页，[技术方案](docs/superpowers/plans/2026-11-01-task-a-c1-c4-technical-plan.md)保留设计与逐项证据，[CURRENT](docs/CURRENT.md)只汇总当前事实。

**本次窗口：** 24 小时内按原门交付，前 6 小时检查实际已验、剩余缺口及待裁决项（起点 2026‑11‑05 02:36 UTC）。不重复已验旅程；确认无现役调用或独立证据价值的旧代码／测试直接删除，不加兼容层、不降低有效断言。**唯一排除真实支付**：购买继续关闭；其余 A‑01～A‑16 不缩减，外部渠道留在 A‑13。

## C‑4 交付检查点

1. [x] **T‑09：对齐 Agent → BFF → App 终态。** 主控负责验收；Agent #46 提供现有 8.11 原件，BFF #18 承接持久和公开契约，App #50 消费已提交的 BFF 快照。跨仓写区已确认，范围只含 `context_window_exceeded / retryable: false`，不启用 `personal_context`，继续拒绝它进入 Scheduled 保存输入。不加 SDK、兼容码或备用路由。
   - [x] **已定位 HTTP 接缝：** Agent `40effb2` 在隔离真 PG/Redis 的原 acceptance 夹具注入实际 typed error，真实 HTTP 回放保留新 tuple。BFF `32357c0` 接受同一页外壳、拒绝新码映射；同一页只换回旧码即可映射。App 旧枚举也拒绝新码。
   - [x] **已验 Agent 自然触发：** 隔离环境直连 Agent HTTP，真实 Redis 消费与 PG 租约驱动 `RunSupervisor/AgentFactory` 自然超窗；只产一个不可重试终态，PG、Redis 与 HTTP 回放一致，模型供应商和资金授权零调用。诊断未经过 BFF，未启用产品 `personal_context`。
   - [x] **已复现持久化缺口：**在 BFF `32357c0` 的私有副本只给原 AG‑UI 集成夹具追加新 tuple。真实隔离 PG/Redis 中，现行投影落库报 `23514 / ck_bff_message_agent_failure`（1 失败、0 跳过）；资源已回收，主工作树 BFF 源码未改。这是持久化负控，不是原始 Agent wire 或正式组合端到端。
   - [x] **完成：** BFF `d166a51` 原 #18、App `e726cd61` 原 #50，Public 28.19 唯一 YAML 同字节。真 PG/Redis 验持久、回放、快照和禁止 `retryable: true`；App 保正文、无重发。两条保存命令仍拒绝 `personal_context`。
2. [x] **T‑09 / T‑16：完成受影响 owner 门并交原 PR。** 主控复核停写后的候选。复用同提交或受影响输入不变的证据；BFF/App 新候选跑正式相关门，BFF 两项条件 PG 用例按最终输入核对已有真库收据，缺失才补。Agent #46 推到原远端 head `codex/agent-run-lifecycle`；Capability #13 保留原 PR #12 为 base。五仓已逐仓沿原 PR 交付并核对远端 head 精确相等。
3. [x] **T‑09：Root #66 精确组合与来源差额。** 主控在子仓提交已可从各自 PR 获取后更新 gitlinks，重核拓扑、合同 inventory 和现役 IAM relay 来源。先核 Browser→Web、BFF→Scheduler、Scheduler→BFF 三条活跃边；两条 Scheduler 边共用现役 vendor。Web→BFF、BFF→IAM 在旧清单仍为破损，不能按字节近似直接标绿。历史破损边、既有结构告警与此次新增阻断分列，不改历史 hash、不下调门禁、不为清数字扩大改动。
   - [x] **来源清单预检：** 私有候选已按当前真实 Git blobs 重取路径，原 checkpoint 通过；兼容性仍只报原 13 条 broken。Scheduler 测试已从硬钉旧 1.0 版本改为断言同一 owner 契约；正式清单与五个 gitlinks 已固定在 Root 本地 `4cb91169`；拓扑、checkpoint、relay 通过，历史 checkpoint 保持。Root 沿原 #66 交付，未合并。
4. [x] **T‑15：正式原生 E2E 与同步交接。** 精确组合 Root `4cb91169` 的现有 Chromium 旅程 5/5 通过：冷登录、跨租户拒绝与恢复、登出、独立撤权、同会话 Admin 准入与撤权。收据 `116d7c62ab4aa5e90f2076d4` 的凭据扫描和全部临时资源回收通过。首次运行退出 1（0/5，收据 `928147cc7f37fd650ee37b43`）；同环境定位为 PostgreSQL URL 缺显式角色，复用现有本机 URL 归一化后通过，未改 IAM 或放宽门禁。主控另保留 IAM/BFF/App/Capability（MCP/Custom API）/Admin 同步实例；以实际 Chromium 登录 303、会话及 Project 列表 200、Admin me 200 验收。入口、启停与私有日志索引交本机说明；该实例不含真实 Chat、Skills 安装或账单。

## 版本与遗留项

| 仓库 / 检查 | 当前事实 | 剩余动作 |
| --- | --- | --- |
| IAM #6 / Capability #13 / Agent #46 | 原 PR 精确 head `b6a9745` / `2409496` / `163b38a`；已验受影响工程门、真实依赖与 Agent 自然超窗 | 仅随对应产品切片扩大验收 |
| BFF #18 / App #50 | 原 PR `3b3039c` / `4ac9d83d`；BFF Storage 来源更新后仅复验受影响门，原完整门及两项条件 PG 收据保留 | 不重复现有终态验证 |
| Root #66 / G3 治理 | 最终精确源码组合 `6db2028d` 严格结构审计 exit 1：408 条、0 未验证。比 388 基线多出的 20 条均是 BFF 固定 IAM 0.21 字节副本，逐条同 IAM 原件历史诊断；没有新增未处置项，也没有改门禁。 | 已发布契约 15 active／0 declared broken／0 illegal；A‑13 setup 独立；八 owner 已同时 ready |
| I‑15 / 运行范围 | Root `430ce075`：八个数据 owner 用同一连接角色在一个新隔离数据库串行执行正式 installer，全通过；每次邻 schema catalog 未变，`public` 不变、跨 schema FK 为零，临时库已回收。随后 BFF 仅改 IAM 生成来源，installer/canonical SQL 原字节保持 | 同库安装、八仓联合 readiness、Redis 隔离及回收已验；未称八仓业务全部跑通。未运行全站浏览器、CI、部署 |

## G3 验收收据

- [x] **I‑15 同库安装**：BFF、IAM、Capability、Agent、Storage、System、Billing、Scheduler 八个正式安装器全部实际通过；不把安装收据当服务联合运行。
- [x] **结构工具链补证**：原 System、Billing 两个未验证已使用本仓锁定依赖补齐，实际 FAIL 保留，不降门。
- [x] **BFF→IAM 合同边**：BFF #18 `12ca1bf` 生成自 IAM `b6a9745` 的 0.21 原件；22 项引用闭包、16 个生成文件及生产源码保持，原 0.20 仅作独立 relay 锚。Root `98b6a9d9` 的真 IAM/BFF/App 同源链：profile／会话列表 200，自撤 409 且当前会话保留，Team 匿名 401、成员读取 200、删除不存在的成员返回 404 且列表不变；临时资源已回收。该步 checkpoint 为 4 active／12 declared broken／0 illegal；保留原件。
- [x] **System 现役读链**：精确 System `49a5f8e` 的真 Nest、隔离 PG/Redis 上，Agent 现有 client 验证默认／指定模型解析、精确凭据、跨租户和错误 digest 拒绝；Agent #46 `91c80f7` 固定 6.1 来源，业务客户端、Worker 和 lock 保持。BFF `12ca1bf` 的实际目录与运行清单处理器通过：他租户无目录数据／清单 404、server envelope 缺失 403、凭据不进投影。BFF 另验 6.1 管理发现：管理员 200、非管理员 403、只发一次本地 metadata GET、无密钥泄露或目录写入。使用处理器级隔离接线，不冒称 Web／IAM 整链或其它管理写入验收。临时 DB/Redis 已核无余量；未启动 Worker、推理。
- [x] **BFF→System 合同边**：在精确组合的真实 System 补齐 16 个生成模型操作及独立手写 manifest。实际覆盖创建/重放/恢复、不泄露凭据、跨租户 404、缺发布条件 428、合法发布、陈旧路由 409 且状态不变、标签更新与五类列表；管理发现只访问本地 metadata。生成器与 Node 版本断言按 BFF Git 原件固定，精确边恢复 active。
- [x] **P0 · Agent→System 治理证据**：精确核对 System `49a5f8e` 6.1 OpenAPI、owner provenance 与其 23 个 Git 源文件、Agent `91c80f7` 的唯一手写消费收据与 `uv.lock` 直接运行依赖 `httpx@0.28.1`。具名例外只适用这条边，错来源、仅传递依赖与有条件锁记录均拒绝；历史 checkpoint 不变。真实路由／凭据收据的 Agent 运行基线仍为 `40effb2`，客户端、Worker、锁在 `91c80f7` 未变，直接复用、不重跑。
- [x] **P1 · Capability→IAM**：Capability #13 `2409496` 使用独立 clean IAM `b6a9745` 0.21 归档（SHA‑256 `458da2ba…cad9`），Root 同时核归档、owner Git 来源、pnpm 安装和 zod 的实际来源，拒绝带真 provenance 的重包与依赖覆盖。真实 IAM 对同一生产 verifier/proof 先允许精确绑定，撤权后拒绝；审计记录 `DIRECT_USER_CURRENT` 与 `PERMISSION_NOT_CURRENT`，隔离 PG/Redis 零新增残留。Capability 生产源码不变，只证明这一条边，未重跑 R336。
- [x] **P2 · BFF→Capability HTTP 7.0**：BFF `12ca1bf` 与 Capability `2409496` 原件同字节，16 个生成文件复现一致。真 Capability Nest／隔离 PG/Redis 验六条现役读：非空目录、本人列表/详情/两页历史、MCP 服务与本人连接；补五个非空 BFF 生产入口及目录到实际 Connect 当前版本的精确绑定；本人列表入口复用 Sandbox 收据。他主体/租户隔离、无凭据/错用途/租户错配拒绝。BFF Session/MCP 授权、用量读为受控边界，不称真实 IAM 登录旅程；三个无生产 caller 的生成读与旧 R336 不重跑。
- [x] **P3 · 其余现役边与 G3 退出项**。
  - [x] **BFF／Agent→Storage v3**：分别沿原 PR 固定 Storage `4a99061`。BFF `3b3039c` 的真实 Projects 模块与 Storage 同一隔离库分 schema、真实 MinIO／Redis；同摘要第二次上传完整流过 ClamAV，仅将回执置为非 clean，BFF 返回 `409 storage_upload_conflict`，原 Asset／Blob／Scan、对象版本及原字节保持。Project 与 Conversation 两条持久 ACK 匹配 BFF outbox，DELETE 重放仍为 202，物理回收未验。Agent `6231f0b` 只再生新枚举，7 条现役请求字节及运行依赖保持；复用 Agent `4bfb5cc` × Storage `4a99061` 的真交付收据 `3d0ef92752028538c5d81e36`，未重跑整条。
  - [x] **Capability→Storage**：精确 `2409496` × `4a99061` 真 Nest／PG／Redis／MinIO／ClamAV，带版本 PUT、CLEAN 24×24、原 PNG、取消/重放均通过；他主体 404、错误 Storage scope 403，Capability intent 和 Storage 资产持久回收，自有桶及数据库已清理。独立 MCP package profile 与生成描述符通过现有检查，未重跑 R336。
  - [x] **Agent→Capability**：Agent #46 `163b38a` 正规再生四份当前 Platform Proto，12 个允许 RPC 描述符不变，独立 profile／运行客户端／锁保持。真实 Agent transport 与签名器→Capability `2409496`→IAM `b6a9745`；有效绑定只发一次持久 grant，owner 撤权后同键／新键拒绝，IAM 审计仍判当前，排除 IAM 误拒。隔离 PG/Redis 无新增残留；声明发现和 Run lease 输入受控，零模型或工具调用。
  - [x] **Web→BFF、BFF→Agent（已发布 Run 主链）**：App `4ac9d83d`（Node 22）实际 Session adapter→BFF #18 `2dcb75c` 同运行字节→Agent `163b38a` 真 HTTP／PG／Redis。Message 202 同键回放；SSE 游标对同一持久事件，续读不重放首帧，未知游标 400；真 Agent 认领、BFF Run Display 200／异用户 404；取消 202 同键回放只写一条 Agent PG 命令和一帧 Redis 控制，摘要一致。18 份 BFF 生成文件再生同字节；Web Public 28.19 原样。Session 准入受控；没有重跑登录、模型、Worker 或取消终态；自有资源已回收。
  - [x] **BFF→Billing（Billing、BFF/App 契约 owner）**：BFF #18 `b65cf76` 固定 Billing `b7c98588`，16 个生成文件及生产源码保持。真实 BFF/Billing HTTP 与隔离 PostgreSQL 两个 schema，目录、本人账户／摘要／账本、管理定价发布／回读／积分入账、模型预占／恢复／结算共 11 项通过。一次扣 1、释放 9，同键重放仍只有一笔结算；临时资源已回收。Session/IAM 与 Agent evidence 为受控输入，不称真实支付或模型执行。公开 checkout 仍 503；App `4ac9d83d` 仅删除无调用客户端、预览桩与专属重复覆盖，禁用 UI／公开契约保留。
  - [x] **Scheduler→Agent 直边退役**：现有本地持久 Scheduler 库以只读事务核对，active schedule 0、未完 outbox 0、可恢复 paused 2 条全为 BFF callback，Agent direct 与未分类均 0；未更改数据。实际链仍是 Scheduler→BFF 持久接收→BFF worker→Agent `/v1/runs`。仅退役当前 Root 直连边，历史 checkpoint 保留，未增加处理器。本轮主控从本机配置自主只读复核，同样为 0 active、0 未完、2 暂停且均为 BFF callback、0 直连、0 未分类；未启动持久排程。精确 Scheduler `cfb2502` 以正式源码二次启动、ready、重启原键返回同 receipt，隔离 PG 只一条排程和回执。425→202 定向首轮被真集成库名前缀守卫拒绝，改用自有临时 PG 库后通过、已核回收；该次目标 HTTP 为替身，A‑12 的正式 BFF/Agent 到点结果仍待。
  - [x] **G3 结构差分**：精确 `6db2028d` 严格审计仍 exit 1（408／0 未验证）；对 388 基线新增的 20 条全部与原本已红的 IAM canonical 相同，按字节及逐条归属，新增未处置为 0；不改历史基线或降低门禁。
  - [x] **I‑15 / G3 最终运行范围**：主控在组合 `6db2028d` 上实跑，八个生产 owner 入口的 `/readyz` 同时通过。同一隔离 PostgreSQL、一个角色、八个 schema，0 跨 schema FK，`public` 无业务关系；Redis／自有桶／PG 和进程全部回收。Agent 仅 HTTP，未启动 Worker，不重复登录或全产品旅程。

## 已收口的阶段（保留证据，不重跑）

- [x] **G0 / G1 / T‑05 / C‑1.3：** Root `4e603743` 原冻结组合已验真实原生认证旅程及负控；新组合另在 T‑15 验。
- [x] **T‑17：** BFF `09f44fe` 本地已提交；正常信号退出 0、端口冲突退出 1、真实锁下约 30 秒断流及 31 秒硬退出已实测。
- [x] **T‑11：** 旧入口、dispatcher 和退役 producer 已清理；四项归并为 StableId `f7d1e69`、两个 AgentRuns reader `76f2d04`、Personalization `335dbe3`；三个拆分为 ScheduledTask `368e65e`、Chat `fb3cfa4`、Projects `32357c0`。主控按切片验过有效行为；BFF 清理提交在本地，最终 PR 配对归 C‑4。
- [x] **T‑11 环境：** 原 Docker/MinIO 卷已恢复写入，登记空测试桶已回收；现役 ingress、感染拒绝、ACK 丢失恢复及 R336 已验；未清卷、未重建。

## 另记：本人 MCP 读链简化

- [ ] 当前入口已核登录和租户成员，`mcp_personal/read` 又单独查 IAM。独立处理该冗余接线，保留可信 `userId`、租户和资源归属，以及确有独立策略的管理员操作；本轮未改认证或授权行为，不用既有验收为重复调用背书。

## 当前产品待办

- [x] **A‑01 会话创建与恢复**：App #50 `065caaa3` 将 Back 与显式 New 分开，迟到 ACK／拒绝只落原提交。Chromium trace `d35c3302ca62b74ae667227d` 定位了 App 在 Forward 抢先清 URL；原 PR `2bc82211` 只允许清除已从同一视图索引移除的任务 URL，普通 404 与真实跨标签索引边界保留，未改认证或公开契约。定向 RED→GREEN、ESLint、TypeScript 与生产 build 通过。
  - 真原生 App/IAM/BFF/Agent、隔离 PG/Redis：`ab56f252348a8afe4d74b6d5` 实测 Back／Forward／硬刷新／第二标签同一 owner Run、零取消和零写；`a76bd75d3bd10350e6efe542` 的直聊首发唯一 202、刷新与原生重登 303 后读回同一会话正文和 Run 通过，之后未到项目写入；`98d76353be75b0242267d2a2` 实际项目创建、项目首发唯一 202、硬刷新回读和删除后 404 子步骤通过。
  - `029d8b22f0f0e342e24bec6e` 实际改名、搜索、移动与归档回执/归档列表/原 rail 隐藏通过；该组合末尾额外的活跃列表 GET 被限流（429，整轮不是 PASS）。仅在新隔离 fixture 补归档后活跃列表，`fc985f40ddafed1b5db52874` 真浏览器归档、owner/归档列表与活跃列表 200 不含该 ID 均通过。五轮均收资源；无外部模型、Worker 或部署。
- [x] **A‑02 Agent 过程与详情**：App #50 `673292d2` 删除纯文本历史的无用 RunDisplay 请求；`3c6a68aa` 将面板内 Escape 接到现有关闭与按 activity ID 回焦，面板外不消费。原生 App/BFF/Agent 同一 Run 的真实 PG/Redis、Agent `ls /` 非空详情与 canonical final：Chromium 实测首开／硬刷新同一动作，正文顺序不变、终稿只出现一次、详情 200，Escape 关闭并回原动作，零写入；临时资源已回收。受控生成，未调用外部模型。
- A‑01/A‑02 合并候选 App `pnpm check` 全过；独审补的迟到明确拒绝只重跑受影响的导航／恢复／引擎、类型和 lint；浏览器差额另用一条会话链验证，不重复 T‑15。主控验收与 Git，`p0_review` 独立复核。
- [x] **A‑07 Project Todo**（主控 · 已验收，原 PR 交付）：[D0](docs/superpowers/plans/2026-11-01-task-a-c1-c4-technical-plan.md) 沿原 Project 表与权限、零 DDL。BFF #18 `846821ae` 真 PG 验创建／重放／权限／并发／ABA／父墓碑，App #50 `85752044` 消费精确 Public 28.20。原生 Chromium 收据 `2f5123a6b6d7297ba1a0e2cb`：同一任务创建后刷新、两标签更新与 412 保草稿、审核零写入后显式保存、删除 204 后刷新读空、390px 键盘焦点；全部验收临时资源已回收。Root `b1fa258a` 固定两仓精确提交，拓扑及 15 条现役契约通过。另在留存的隔离本地实例走正式登录、先查重、正式 CRUD 登记两组原始任务，项目页及 GET 各读回两条唯一记录；旧同步实例未动。
- [x] **A‑03 输入与运行控制**（主控 · 已验收，原 PR 交付）：App #50 `c17810c3`、BFF #18 `99f946e`（Public 28.22）、Agent #46 `815ef5c` 均已核原远端 head。原业务路线不变，不加第二套控制协议。证据分列，不拼成单次全旅程：
  - **FIFO / IME / 打断 / Stop**：`937b817da5993a434df8b2c1` 真 Chromium 验 IME Enter 零写、多行原文、后续 202 丢失后刷新零自动写、显式同键同 body 返回原三 ID、无第二个后继；该次未启动 Worker。真 Worker+Chromium `e7d8150a022eb8ab81adaee4` 验精确旧 Run 被取消，只有旧持久终态后才启动唯一后继，刷新唯一。保留原 Stop 路由及晚到定向负控，不拿打断代替全部 Stop 证据。
  - **同 Run 补充**：`dc117ba57713283151abe699` 真 Chromium、IAM、PG/Redis 和 Worker：首 202 故意丢失、原键同 scope/目标/正文恢复同 Message，未到下一模型时保持 pending，独立 checkpoint 与下一模型各一条，只有一 Run/assistant/steer、零 cancel，公开 parts 200、硬刷新唯一终稿。该收据 Agent 为 `71cbbf0`；最终 `815ef5c` 只把数组 cast 换成等价 TypeGuard，另含 Swarm HITL 分支，不改补充规则/协议。R4/R5 偶发硬刷新终稿 DOM 未出（owner 已 completed），未证明根因或修复；A‑15 留一条真实诊断，R6 不覆盖失败历史。
  - **审批／回复／断流**：HITL R7 `8663731781f1edf9edb3e8a2` 为上述最终四仓精确候选。原 Run 一个暂停组/两个 owner item，审批暂存零写、非空 Unicode 回复和审批同一次真实 Control POST，BFF 与 Agent 202；真实 Worker/PG exact 回复与工具各一次、同一 Run/assistant 唯一终稿、零取消。R5 `876d2b77ddd53a5d9f47f197` 单独真实观察 TLS 截流、同一原连接游标重连、段落和未发送草稿保持、重放后两控件可用；该轮总体失败（私有 oracle 误识原生 respond item），R6 502 亦为 relay 误读规范位置，未计通过；R7 修正夹具，所有自有资源回收。
- [ ] **A‑04 执行恢复**（owner 阶段通过）：Agent `163b38a` 两个真实 Worker 进程／PG checkpoint／Redis；旧进程在工具结果持久后被 SIGKILL，租约实到期约 3.3 秒、generation 1→2，旧代续租／写入均拒、工具副作用及 PG/Redis 终态各一次；自有资源已回收。收据摘要 `28fdfadde03b…cfa39`。使用离线模型替身，真实供应商／用量链、Swarm 和产品浏览器仍待。精确 `0b5a3873` 组合已验三方同一 attempt：真实 Agent 封存证据 HTTP→BFF→Billing 扣 1、释放 9，持久 ACK 与原键重放只有一笔结算，隔离 PG/Redis 已回收；收据 `daa09e934c02…152c8`。首次预留用 IAM 夹具、用量合成，未启动 Worker 或模型、真实支付保持关闭。首轮夹具漏 Billing schema URL，修正后通过。在同一精确 Root 上实际本地 Ollama `qwen3:8b`＋正式 Worker 已通过：仅一条模型 POST、一个派发及封存 attempt，真实 7897/246 输入/输出用量，Agent completed 与原 attempt ACK captured，Billing 一笔用量/一笔结算、扣 2。首次预留验证真实签名与绑定但 IAM 决策用夹具，System resolver 单独注入，未开支付；自有库与 Redis keys 均回收。收据 `2d3e9b5c5d26…bf32a`。首次 Redis /9 已有数据，门禁拒绝且零模型调用，改已确认空闲 /8 后通过；未清旧数据。Swarm 真 Worker/正式 `music_chat` 已实到跨 peer 暂停及原键 resume。旧 Agent 真 `run.failed/internal_error`：native resume 已发，因 raw LangChain 桥丢 `respond` 文本未发生后继模型。Agent 本地候选 `71cbbf0` 修后定向通过、真实后继模型已到四个完整封存 attempt，但持久 resume 完成仍待；R6 重建探针在 resolver 私有上限先退出，不把四次封存称为单终态。R7 已实证 leaf resume 向量精确匹配、无错误或 interrupt 但保留一个 task，现恢复 owner 仍 unknown；`a04_proofs` 独立读取已实证可信 root 锚点、同 attempt 原生 handoff、精确 root 终态无任务，两处既有 reader/owner 校验承接该单组根见证，普通和多组 HITL 保持原规则。子代理的隔离真验通过后主控补严格类型并复跑，最终收据 `522b06ea8595…c104`：真 Worker、PG、Redis、BFF/Billing，同一恢复键持久为 `native_consumed`，四次派发/封存及四笔隔离结算、无额外派发、唯一终态和精确最终正文；所有自有资源已核回收。模型及用量为离线夹具，IAM 决策与 System resolver 受控。首个主控运行真通过后，架构门抓出 3a 已有的 checkpoint cast；换同语义 TypeGuard，根祖先字段由现 PG JSON 查询读取，相关架构/交互/HITL、Ruff、Pyright 全通过。首次定稿隔离资源门拒绝非空 Redis /10，零启动，未清他人数据；换已确认空闲的 /8 后完整真验通过。主控核最终源码同字节后提交 Agent #46 `815ef5c`，已推原 PR；只交 Swarm owner 修复，A‑04 产品门仍开。首个私有候选因夹具从不保存 final 的 outbox 查正文而报失败，纠正为 scoped PG Chat/Redis 后通过；不把该项称浏览器验收。`a04_proofs` 只补工具→产物→下载的产品浏览器差额。
- [ ] **A‑05** 长上下文：复用同字节的真 PG 摘要恢复与历史真实模型压缩证据；当前 native factory/公开投影仍需一条真实长会话保原引用、刷新/重放/分享不泄私有摘要，另以已派发摘要时停止的一个负控核取消与无后继主模型。T‑09 超窗不等于压缩。修正私有 SDK 历史预填后，精确 Agent `71cbbf0` 的真实 PG/Redis/Worker 取消负控已通过：摘要真正派发一次后 Stop、原 provider 调用被取消、零后继主模型、旧历史保留且 Agent 公开投影无私有 marker。成功例首次因夹具未提供 SDK 自然发起的第二个摘要而 `model_unavailable`；R4 改正夹具后，精确 Agent `71cbbf0` 真实 PG/Redis/Worker 通过：五次主调用与两次 SDK 摘要，压缩前后同一真实 Skill 文件读、真实 checkpoint 与唯一终态，Agent 公开帧无私有 marker。模型与 Billing 是离线替身，隔离资源已回收。独立原生 IAM `b6a9745`、BFF `99f946e`、Agent `71cbbf0` 的公开 R5 `f6e136557b8612e3e7a1a4d4` 已过：同 Run 公开 22 帧与全重放完全一致，Last-Event-ID 只返后缀，snapshot ordered parts 与无浏览器 Cookie 的实际分享读到同一终稿，私有 marker 不外泄，撤销后 404。隔离资源回收并核凭据日志。上轮私有夹具按旧 flat content 读取失败，修正为正式 parts，非生产变更；未运行 App/浏览器或真实供应商/Billing。原 handoff 逐项复核：选中 Skill 指令原字节、工具结果与后继模型已证；用户附件仍依赖 A‑08 正式提交/读取资格，真实产物引用不等于另一条 A‑04 Run 的收据。现真 PG 已证摘要封存与新 lease 读取，但由夹具换 lease，仍缺一次真 Worker 进程恢复后同 Run 审批／继续、封存摘要不重复、用量不重复；把必要的真 Billing 和产物引用并入该旅程，不重跑公开 replay/share。A‑05 未闭环。**A‑06** 项目上下文：已盘点排序只在当前视图、指令历史可能错误标当前、指令未进入 Agent 任务、网站仅预览且缺正式 owner。现有菜单、读写和逻辑释放证据复用。指令历史的小修复已在隔离 App 源码以同毫秒旧条排首复现：原实现标两条当前；按 owner `current` 渲染与默认选中后，原定向套件通过。App #50 本地独立提交 `2a7d4b16`，主控在正式 Node 22 重跑相关套件、ESLint 与 TypeScript 通过，未推、未跑本切片的原生浏览器。排序优先左栏项目条目，复用已准入用户的现有浏览器偏好，概览会话继续 owner 最近排序，不新建 BFF 表；排序持久化由 `a03_atomic_read` 在精确 App `c17810c3` 私有 Node 22 复现：键盘操作当次正确，但同账号重挂载丢排序，owner 删除/新增仍准确；已进同一窄切片的私有实现与对照，未改共享 App；主控已将项目指令 owner、冻结时点、隐私及验收草案记入方案，先核现有容量与生成物，不动现公开协议或调度；正式网站关联与实际 owner 仍待核。
- [ ] 保留 **A‑08** 附件、**A‑09** 资料库、**A‑10** 文件/Canvas、**A‑11** 首页、**A‑12** 自动化、**A‑13** 外部聊天（App setup 有真实 UI；Agent 尚无对应路由，保留并单独交付，不当作现有成功或死代码）、**A‑14** 语音、**A‑15** 体验性能、**A‑16** 交付与运行配对。按原范围验收，不默认从零做，也不冒称完成。A‑15 新增具名观察：保留 A‑03 两次已完成 Run 的硬刷新终稿 DOM 偶发缺失记录；以实际 /parts 状态定位，确认前不加盲目重试。

**更新规则：** 主控独占 TODO 和 Git 集成，子代理并行核对独立 owner 或来源证据。每次只推进清单中最前的未关闭项，记录 owner、受影响提交、实测结论和下一步。验收输入不变就复用旧收据；只有输入变化、失败定位或缺失证据才补定向验证。C‑4 Goal 已验收，产品 Goal 仍需逐项核对原 A‑01～A‑16（真实支付除外）。各仓沿原 PR，不合并 main、不部署。
