# Task A · TODO（2026-11-05）

**当前：G0～G3／C‑1～C‑4 前置清理闭环。** 当前 Root 精确组合提交 `48c5d801` 配对 Agent `92e235e`、BFF `40bed71`、App `b1c2c1e`；已发布契约 15/15、八个数据 owner 同库同时 ready；已验登录和 Run 主链复用原收据。**A‑01 和 A‑02 已验收，A‑07 已通过原生浏览器，A/B 已在本地正式登记**；Task A 产品项未闭环。唯一执行清单在本页，[技术方案](docs/superpowers/plans/2026-11-01-task-a-c1-c4-technical-plan.md)保留设计与逐项证据，[CURRENT](docs/CURRENT.md)只汇总当前事实。

**本次窗口：** 24 小时内按原门交付，前 6 小时检查实际已验、剩余缺口及待裁决项（起点 2026‑11‑05 02:36 UTC）。不重复已验旅程；确认无现役调用或独立证据价值的旧代码／测试直接删除，不加兼容层、不降低有效断言。**唯一排除真实支付**：购买继续关闭；其余 A‑01～A‑16 不缩减，外部渠道留在 A‑13。

## 2026-11-05 进度同步（主控唯一台账）

- **Goal：ACTIVE（已恢复）。** 仍以本文件为唯一 TODO；不合并 `main`、不部署，各仓沿原 PR。
- **本轮已提交/已推送：** Agent #46 `92e235e782178b7002f0bd68daa143b507db870d`（8.12 project instruction contract）；BFF #18 `40bed716edf43c937c5f6e5ef2143a437ed412e4`（项目指令在 launch 同事务冻结、重放保持首值、1 MiB 保护）；App #50 `b1c2c1e8ca53095bccf50a92cb0d88be8ce8`（website preview 仅在 capability=true 且无 task 时显示）。三仓各自 PR 分支已推送。
- **Root 已提交/已推送：** `48c5d801` 配对三个 gitlink 与 inventory；`fc74d02d` 设计门、`376f1a0d` 台账刷新、`38eed837` Goal 状态记录、`de5e47d0` 恢复 ACTIVE。`verify-repository-topology.py`、`verify-contract-compatibility.py`、`verify-contract-checkpoint.py --expected verification/contracts/checkpoints/task-a-agent-web-runs.json` 均 PASS。
- **实际验证证据：** App UI 41 passed、ESLint、typecheck；BFF Agent dispatch 23 passed、display contract 7 passed、contract:check:agent 18 files、typecheck/lint/build；真实隔离 PG/Redis 的 A‑06 project-instruction integration 1 passed；Storage RPC/信任边界/生命周期/Scoped file 定向 37 passed，Agent Storage generated/delivery/transport 定向 53 passed。BFF 全量 `contract:check` 仍有 5 个既有 closure inverse 失败，未冒称全绿。
- **当前闭环状态：** A‑01/A‑02/A‑03/A‑04/A‑07 已验；A‑05、A‑08～A‑16 仍 OPEN。A‑06 仅完成排序与指令跨仓候选，website 正式 owner/readback 仍缺，不能勾选完成。
- **下一执行顺序：** A‑08 先由 Storage/Agent owner 交付窄的 run-scoped read contract，再接 BFF 事务冻结和 App 选择；复用现有 Storage/CLEAN。随后把同 Run 引用保持接入 A‑05；之后按 A‑09～A‑16 逐项收口。
- **不重复/不扩张：** 不以测试数量代替闭环，不重跑已验旅程；只补实际缺口，旧入口/无消费者测试直接删除并保留有效断言。

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
| IAM #6 / Capability #13 / Agent #46 | 原 PR 精确 head `b6a9745` / `2409496` / Agent `92e235e`；Agent 8.12 project-instruction contract 已推送 | 随 A-05/A-08 读取资格切片扩大验收 |
| BFF #18 / App #50 | 当前候选 BFF `40bed71`、App `b1c2c1e`；A-06 project-instruction freeze 与 website preview gate 已推送并定向复验 | A-08 wire/owner slice 后再扩展组合验证 |
| Root #66 / G3 治理 | Root `fc74d02d` 的 topology、contract compatibility（15 edges/0 violations）和 `task-a-agent-web-runs` checkpoint 均 PASS；历史严格结构审计仍保留原 exit 1：408 条、0 未验证。比 388 基线多出的 20 条均是 BFF 固定 IAM 0.21 字节副本，逐条同 IAM 原件历史诊断；没有新增未处置项，也没有改门禁。 | 已发布契约 15 active／0 declared broken／0 illegal；A‑13 setup 独立；八 owner 已同时 ready |
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
- [x] **A‑04 执行恢复**（主控 · 已验收，原 PR/Root 精确配对）：Agent #46 `815ef5c`、BFF #18 `99f946e`、App #50 `c17810c3`，精确 Root `d03d7c51`；Storage `4a99061`、Billing `b7c98588`。证据按真实边界分列：
  - **运行中断、租约、重投**：主控在精确 Agent `815ef5c` 重用原两进程夹具，真 PG/Redis/Worker，旧进程在工具结果持久后 SIGKILL；自然等 3326 ms 后旧 lease 失效，第二进程 generation 1→2 接管且 Redis 同请求重投不重复，旧代续租和工具 journal 写入被拒绝；独立 PG checkpoint、文件副作用、PG/Redis 各唯一终态与终稿，PEL 为 0，全部资源回收。收据 `bf56ed4c4b64…fe808`；仅此负控模型为离线替身、零 Billing 派发。
  - **Swarm 与真实用量链**：旧 `3a9ccb7` 真原生桥丢回复导致 `internal_error`，修复回复后阶段验证仍因退役 peer 的叶 task 判 unknown；按原冻结 recipe 和同 attempt 根后继修复。定稿 `815ef5c` 真 Worker/PG/Redis/BFF/Billing `522b06ea8595…c104`，跨 peer 同键 `native_consumed`、四次精确派发/封存及四笔隔离结算、零额外派发、唯一最终结果。模型及用量为离线夹具；首 reserve IAM 决策与 System resolver 受控。另保真实本地 Ollama `qwen3:8b` 的原组合 `2d3e9b5c5d26…bf32a`：真实 7897/246 用量、单 attempt ACK、Billing 扣 2；不是此 Swarm/浏览器 Run。真实支付关闭。
  - **当前产品浏览器**：R9 `8dfd5e705e2aab50797af6cf`（SHA `09e1b8584030…a02e`），原生 IAM/Chromium 一次真实 Message 202/live SSE；真 Worker `write_file → deliver → final`，实际 Storage/MinIO/ClamAV、Canvas 下载原字节 SHA `c87901769c61…e7b3`，刷新同 Run/artifact/asset 各唯一，PG 仅一条 delivery 与终态，同 Run 三个真实 Billing 封存 ACK。离线模型 3 次，合成 36/12 tokens；模型替身和 IAM fixture 如实保留。早轮的 Redis 映射/JWKS 路径/Storage 配置/旧测试代理缓冲无限 SSE 为私有配线失败，均未当产品通过；R9 未改生产。凭据扫描与自有 PG、Redis、测试桶回收全通过。
- [ ] **A‑05** 长上下文：复用同字节的真 PG 摘要恢复与历史真实模型压缩证据；当前 native factory/公开投影仍需一条真实长会话保原引用、刷新/重放/分享不泄私有摘要，另以已派发摘要时停止的一个负控核取消与无后继主模型。T‑09 超窗不等于压缩。修正私有 SDK 历史预填后，精确 Agent `71cbbf0` 的真实 PG/Redis/Worker 取消负控已通过：摘要真正派发一次后 Stop、原 provider 调用被取消、零后继主模型、旧历史保留且 Agent 公开投影无私有 marker。成功例首次因夹具未提供 SDK 自然发起的第二个摘要而 `model_unavailable`；R4 改正夹具后，精确 Agent `71cbbf0` 真实 PG/Redis/Worker 通过：五次主调用与两次 SDK 摘要，压缩前后同一真实 Skill 文件读、真实 checkpoint 与唯一终态，Agent 公开帧无私有 marker。模型与 Billing 是离线替身，隔离资源已回收。独立原生 IAM `b6a9745`、BFF `99f946e`、Agent `71cbbf0` 的公开 R5 `f6e136557b8612e3e7a1a4d4` 已过：同 Run 公开 22 帧与全重放完全一致，Last-Event-ID 只返后缀，snapshot ordered parts 与无浏览器 Cookie 的实际分享读到同一终稿，私有 marker 不外泄，撤销后 404。隔离资源回收并核凭据日志。上轮私有夹具按旧 flat content 读取失败，修正为正式 parts，非生产变更；未运行 App/浏览器或真实供应商/Billing。原 handoff 逐项复核：选中 Skill 指令原字节、工具结果与后继模型已证；用户附件仍依赖 A‑08 正式提交/读取资格，真实产物引用不等于另一条 A‑04 Run 的收据。真实压缩后重启 R2 `ef6424fd5794…61f6` 已验：精确 Root `d03d7c51`、Agent `815ef5c`／BFF `99f946e`／Billing `b7c98588`。原摘要封存且已计费后进入真实 pause 释放 lease，旧 Worker SIGKILL，另一 PID 在同一 Run generation 2 从独立 PG 读原 capsule/offload，正式 resume 后后继模型只读一次非空回复，canonical PG 终稿/终态同 ID；真实 Billing 三 attempt/usage/settlement 一一对应，原摘要只收费一次。模型为离线夹具，首 IAM 决策受控；真实支付关闭。R1 因误在不存正文的 critical outbox 查终稿而失败，R2 改读 canonical Chat，隔离资源均回收。不重跑公开 replay/share；原长会话的附件／既有产物引用实际保持仍待与 A‑08 合并覆盖，A‑05 未闭环。
- [ ] **A‑06 项目上下文**：已盘点排序只在当前视图、指令历史可能错误标当前、指令未进入 Agent 任务、网站仅预览且缺正式 owner。现有菜单、读写和逻辑释放证据复用。指令历史的小修复已在隔离 App 源码以同毫秒旧条排首复现：原实现标两条当前；按 owner `current` 渲染与默认选中后，原定向套件通过。App #50 独立提交 `2a7d4b16`，主控在正式 Node 22 重跑相关套件、ESLint 与 TypeScript 通过，随已验 App `c17810c3` 沿原 PR 推送，未跑指令历史的原生浏览器。排序优先左栏项目条目，复用已准入用户的现有浏览器偏好，概览会话继续 owner 最近排序，不新建 BFF 表；排序在精确 App `c17810c3` 实际 RED：同账号重挂载丢排序。私有实现和独审补两条真 RED（pin 未读完锁全部排序、同主体失效标记更新后旧手势仍写）；现在按已准入 tenant/subject 存仅本机排序、保持 owner pin、列表变化不造数据，取消或迟到失效不写。主控在正式 Node 22 重跑相关三套、ESLint/TypeScript 通过，本地 App `eb6c3819` 已过原生 App/IAM/BFF/PG/Chromium R2 `75789be73cbeb1c69ee20fe4`：两笔真实 Project POST、确认前零写、Space 正好一次本地写、硬刷新原序、Escape 零写、BFF 原顺序与两个真实既有会话顺序不变；无 Agent/Storage、无非许可写或外源，资源全回收。R1 是私有探针读会话 envelope 失败，未计通过；R2 用 Node22 开发源码服务；主控再以同提交独立冻结依赖和正式 `pnpm build` 通过、构建后 Git 源字节不变。首轮私有 node_modules 外链被 Turbopack 拒绝，恢复三条本工作树依赖链接后使用真私有离线安装通过，未改产品；App #50 已推并由 Root 组合固定。主控在精确 BFF `99f946e` 独立真实 Nest/PG 重现：A 写入、改 B、原键正确重放、下一新 Run／直聊／错主体入口正常，但原 Run 的 durable launch 缺 A 原文（`undefined`）；临时 PG/Redis 已回收。Agent owner 的 additive 合同候选在私有副本，BFF 先等正式 artifact，不动现公开协议或调度；正式网站关联与实际 owner 仍待核。
- [ ] **A‑08 附件与引用**：设计门已通过，进入最小实现：App 只提交 opaque `selected_resource_refs`，BFF 在现有消息/Run 事务内解析并冻结 canonical asset/artifact/version，Agent 仅按同一 Run 资格只读 Storage；不新增表/列、不信任 URL/正文/客户端 digest、不扩大个人库权限。现真实上传／CLEAN／owner 下载基线已复跑（App 326 项；BFF project-resource/chat-input 60 项全通过）。当前硬缺口已定位：BFF 只有 `scope=project` 的 CLEAN metadata/download facade，Agent 只有 Run-fenced Artifact delivery，没有个人 Asset/FINAL Artifact read RPC；因此暂不加假 UI 或 signed URL 旁路，下一写区先交 Storage/Agent 窄 read contract。
- [ ] **A‑09 资料库**：保留现上传、扫描和原字节下载；核真实文件／作品筛选、搜索／分页、收藏／删除、失败恢复和来源回跳，复用 A‑08 的同 owner 资源，不另存文件事实。
- [ ] **A‑10 文件／Canvas**：复用 A‑04 当前组合的真实产物与原字节下载；仍需现文件树、Markdown／文本／表格、详情与来源、窄屏及只读／权限的独有证据，不把一个产物旅程扩大成整个 A‑10。
- [ ] **A‑11 首页与创建场景**：核已支持场景实际提交／返回与空白／草稿状态；当前缺口明确标识，不展示假的创建结果；原参考对照待验。
- [ ] **A‑12 自动化**：先核原 writer；Scheduler 独立重启幂等已验，仍缺当前产品浏览器 CRUD／日历／更新页签和到点结果可追、时区 DST／暂停恢复／重投不重复，不用 Scheduler 单仓结果替代。
- [ ] **A‑13 外部聊天**：App setup 有实际 UI；Agent 当前无对应路由。保留 Telegram／LINE／Slack 原范围，查正式 owner／真实 callback 和断开、过期、迟到状态，不当作现有成功或死代码。
- [ ] **A‑14 语音**：复用已删除演示文字注入；真麦克风／转写、授权拒绝／不支持、取消与编辑/发送闭环待验。已确认当前 Next 通用和服务端头都声明 `microphone=()`，与语音入口存在配置冲突嫌疑；待真实浏览器分清媒体权限与识别服务行为，不先放宽全站策略。
- [ ] **A‑15 体验性能**：随各片量实际冷／热和可访问性，留 A‑03 两次已完成 Run 的硬刷新终稿 DOM 偶发缺失；以真实 /parts 状态定位，确认前不加盲目重试。
- [ ] **A‑16 交付与运行配对**：主控沿每仓原 PR、Root 精确 gitlink、记录真实验收与遗留；本窗口不合并 main、不部署，不把历史交付记录当当前全任务通过。

**更新规则：** 主控独占 TODO 和 Git 集成，子代理并行核对独立 owner 或来源证据。每次只推进清单中最前的未关闭项，记录 owner、受影响提交、实测结论和下一步。验收输入不变就复用旧收据；只有输入变化、失败定位或缺失证据才补定向验证。C‑4 Goal 已验收，产品 Goal 仍需逐项核对原 A‑01～A‑16（真实支付除外）。各仓沿原 PR，不合并 main、不部署。
