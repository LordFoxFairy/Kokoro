# Task A · TODO（2026-11-04）

**当前：正式原生验收已通过；八个数据 owner 同库安装通过，BFF→IAM 业务 HTTP 已正式配对 0.21，BFF→System 6.1 已关闭；Agent→System 真调用与 Python 治理、Capability→IAM 0.21 真授权与归档治理均已验收。G3 整体仍未结项；A‑01/A‑02/A‑07 未开始。机器 Goal 已启用（active），范围为 G3/C‑4 收口。** 本页是执行清单；[技术方案](docs/superpowers/plans/2026-11-01-task-a-c1-c4-technical-plan.md)保留设计与逐项证据，[CURRENT](docs/CURRENT.md)只汇总当前事实。已验证的旧组合不等于最终组合。

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
| IAM #6 / Capability #13 / Agent #46 | 原 PR 精确 head `b6a9745` / `2409496` / `91c80f7`；已验受影响工程门、真实依赖与 Agent 自然超窗 | 仅随对应产品切片扩大验收 |
| BFF #18 / App #50 | 原 PR `12ca1bf` / `e726cd61`；完整工程门通过，BFF 默认门的两项条件 PG 已另在真库补齐 | 不重复现有终态验证 |
| Root #66 / G3 治理 | 实际锁定编译器补齐后，严格结构审计 FAIL：388 条、0 个未验证；新增可见的 7 条全是既有 Billing TS 配置差额，System 无新增。合同余项按实际调用、来源和业务缺口区分，不把全部标成运行故障 | 现行 7 active／9 declared broken／0 illegal；结构审计既有红项及其他现役边继续单列 |
| I‑15 / 运行范围 | Root `430ce075`：八个数据 owner 用同一连接角色在一个新隔离数据库串行执行正式 installer，全通过；每次邻 schema catalog 未变，`public` 不变、跨 schema FK 为零，临时库已回收。随后 BFF 仅改 IAM 生成来源，installer/canonical SQL 原字节保持 | 同库安装已验；八仓同库同时运行、Redis/业务旅程未验，按实际涉及的产品链补证。未运行全站浏览器、CI、部署 |

## G3 剩余验收

- [x] **I‑15 同库安装**：BFF、IAM、Capability、Agent、Storage、System、Billing、Scheduler 八个正式安装器全部实际通过；不把安装收据当服务联合运行。
- [x] **结构工具链补证**：原 System、Billing 两个未验证已使用本仓锁定依赖补齐，实际 FAIL 保留，不降门。
- [x] **BFF→IAM 合同边**：BFF #18 `12ca1bf` 生成自 IAM `b6a9745` 的 0.21 原件；22 项引用闭包、16 个生成文件及生产源码保持，原 0.20 仅作独立 relay 锚。Root `98b6a9d9` 的真 IAM/BFF/App 同源链：profile／会话列表 200，自撤 409 且当前会话保留，Team 匿名 401、成员读取 200、删除不存在的成员返回 404 且列表不变；临时资源已回收。该步 checkpoint 为 4 active／12 declared broken／0 illegal；保留原件。
- [x] **System 现役读链**：精确 System `49a5f8e` 的真 Nest、隔离 PG/Redis 上，Agent 现有 client 验证默认／指定模型解析、精确凭据、跨租户和错误 digest 拒绝；Agent #46 `91c80f7` 固定 6.1 来源，业务客户端、Worker 和 lock 保持。BFF `12ca1bf` 的实际目录与运行清单处理器通过：他租户无目录数据／清单 404、server envelope 缺失 403、凭据不进投影。BFF 另验 6.1 管理发现：管理员 200、非管理员 403、只发一次本地 metadata GET、无密钥泄露或目录写入。使用处理器级隔离接线，不冒称 Web／IAM 整链或其它管理写入验收。临时 DB/Redis 已核无余量；未启动 Worker、推理。
- [x] **BFF→System 合同边**：在精确组合的真实 System 补齐 16 个生成模型操作及独立手写 manifest。实际覆盖创建/重放/恢复、不泄露凭据、跨租户 404、缺发布条件 428、合法发布、陈旧路由 409 且状态不变、标签更新与五类列表；管理发现只访问本地 metadata。生成器与 Node 版本断言按 BFF Git 原件固定，精确边恢复 active。
- [x] **P0 · Agent→System 治理证据**：精确核对 System `49a5f8e` 6.1 OpenAPI、owner provenance 与其 23 个 Git 源文件、Agent `91c80f7` 的唯一手写消费收据与 `uv.lock` 直接运行依赖 `httpx@0.28.1`。具名例外只适用这条边，错来源、仅传递依赖与有条件锁记录均拒绝；历史 checkpoint 不变。真实路由／凭据收据的 Agent 运行基线仍为 `40effb2`，客户端、Worker、锁在 `91c80f7` 未变，直接复用、不重跑。
- [x] **P1 · Capability→IAM**：Capability #13 `2409496` 使用独立 clean IAM `b6a9745` 0.21 归档（SHA‑256 `458da2ba…cad9`），Root 同时核归档、owner Git 来源、pnpm 安装和 zod 的实际来源，拒绝带真 provenance 的重包与依赖覆盖。真实 IAM 对同一生产 verifier/proof 先允许精确绑定，撤权后拒绝；审计记录 `DIRECT_USER_CURRENT` 与 `PERMISSION_NOT_CURRENT`，隔离 PG/Redis 零新增残留。Capability 生产源码不变，只证明这一条边，未重跑 R336。
- [ ] **P2 · BFF→Capability（下一条现役边）**：BFF `12ca1bf` 和 Capability `2409496` 的 HTTP 7.0 原件同字节；先按具名运行入口梳理现有组合收据，再只补缺失的身份、操作与拒绝场景。P1 只完成 Capability→IAM，不冒称反向或 BFF 全边验收。
- [ ] **P3 · 其余现役边与 G3 退出项**：逐条明确实际 owner、缺的证据和完成条件。Billing checkout 的 503、Scheduler→Agent 的旧批准拓扑须经各 owner 明确处置，不补假实现。已有结构告警与新增问题分别记录，不靠改状态代替验收。

## 已收口的阶段（保留证据，不重跑）

- [x] **G0 / G1 / T‑05 / C‑1.3：** Root `4e603743` 原冻结组合已验真实原生认证旅程及负控；新组合另在 T‑15 验。
- [x] **T‑17：** BFF `09f44fe` 本地已提交；正常信号退出 0、端口冲突退出 1、真实锁下约 30 秒断流及 31 秒硬退出已实测。
- [x] **T‑11：** 旧入口、dispatcher 和退役 producer 已清理；四项归并为 StableId `f7d1e69`、两个 AgentRuns reader `76f2d04`、Personalization `335dbe3`；三个拆分为 ScheduledTask `368e65e`、Chat `fb3cfa4`、Projects `32357c0`。主控按切片验过有效行为；BFF 清理提交在本地，最终 PR 配对归 C‑4。
- [x] **T‑11 环境：** 原 Docker/MinIO 卷已恢复写入，登记空测试桶已回收；现役 ingress、感染拒绝、ACK 丢失恢复及 R336 已验；未清卷、未重建。

## 后续产品待办：G3 未结项前不实施

- [ ] **A‑01** 会话创建/恢复、**A‑02** Agent 过程/详情；两项之后进入 **A‑07** Project Todo。
- [ ] 保留 **A‑03** 输入与运行控制、**A‑04** 执行恢复、**A‑05** 长上下文、**A‑06** 项目上下文。
- [ ] 保留 **A‑08** 附件、**A‑09** 资料库、**A‑10** 文件/Canvas、**A‑11** 首页、**A‑12** 自动化、**A‑13** 外部聊天、**A‑14** 语音、**A‑15** 体验性能、**A‑16** 交付与运行配对。按原范围验收，不默认从零做，也不冒称完成。

**更新规则：** 主控独占 TODO 和 Git 集成，子代理并行核对独立 owner 或来源证据。每次只推进清单中最前的未关闭项，记录 owner、受影响提交、实测结论和下一步。验收输入不变就复用旧收据；只有输入变化、失败定位或缺失证据才补定向验证。G3 依原退出条件验收后才完成当前 Goal，再按顺序转入 A‑01/A‑02、A‑07。各仓沿原 PR，不合并 main、不部署。
