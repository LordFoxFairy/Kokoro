# Task A · TODO（2026-11-04）

**当前：T‑11 已验收；C‑4 的精确配对、正式原生 E2E 和本机同步测试已通过。全产品、单库 owner schema 与既有 Root 治理红项未关闭；A‑01/A‑02/A‑07 仍未开始。机器 Goal 已清除。** 本页是执行清单；[技术方案](docs/superpowers/plans/2026-11-01-task-a-c1-c4-technical-plan.md)保留设计与逐项证据，[CURRENT](docs/CURRENT.md)只汇总当前事实。已验证的旧组合不等于最终组合。

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
| IAM #6 / Capability #13 / Agent #46 | 原 PR 精确 head `b6a9745` / `5e607fd` / `40effb2`；已验受影响工程门、真实依赖与 Agent 自然超窗 | 仅随对应产品切片扩大验收 |
| BFF #18 / App #50 | 原 PR `d166a51` / `e726cd61`；完整工程门通过，BFF 默认门的两项条件 PG 已另在真库补齐 | 不重复现有终态验证 |
| Root #66 | 精确 gitlinks、拓扑、checkpoint、现役 relay 来源通过；合同兼容仍有 13 条已声明破损边，来源差额已消除；结构审计仍 FAIL（381 条既有规则告警、2 个工具链未验证；较前置基线没有新规则问题，仅 SQL 行号位移） | 既有红项保持显式；无新增风险不扩大此次 PR，不据此宣布全仓治理通过 |
| I‑15 / 运行范围 | T‑15 原生正式和保留环境都使用隔离测试资源；全 owner 单库 schema 组合、全站浏览器、CI/部署未运行 | 单库按 owner installer/URL 盘点和一次真实组合补证；只在影响对应产品时补该路径，不重跑已通过旅程 |

## 已收口的阶段（保留证据，不重跑）

- [x] **G0 / G1 / T‑05 / C‑1.3：** Root `4e603743` 原冻结组合已验真实原生认证旅程及负控；新组合另在 T‑15 验。
- [x] **T‑17：** BFF `09f44fe` 本地已提交；正常信号退出 0、端口冲突退出 1、真实锁下约 30 秒断流及 31 秒硬退出已实测。
- [x] **T‑11：** 旧入口、dispatcher 和退役 producer 已清理；四项归并为 StableId `f7d1e69`、两个 AgentRuns reader `76f2d04`、Personalization `335dbe3`；三个拆分为 ScheduledTask `368e65e`、Chat `fb3cfa4`、Projects `32357c0`。主控按切片验过有效行为；BFF 清理提交在本地，最终 PR 配对归 C‑4。
- [x] **T‑11 环境：** 原 Docker/MinIO 卷已恢复写入，登记空测试桶已回收；现役 ingress、感染拒绝、ACK 丢失恢复及 R336 已验；未清卷、未重建。

## 后续产品待办：G3 未结项前不实施

- [ ] **A‑01** 会话创建/恢复、**A‑02** Agent 过程/详情；两项之后进入 **A‑07** Project Todo。
- [ ] 保留 **A‑03** 输入与运行控制、**A‑04** 执行恢复、**A‑05** 长上下文、**A‑06** 项目上下文。
- [ ] 保留 **A‑08** 附件、**A‑09** 资料库、**A‑10** 文件/Canvas、**A‑11** 首页、**A‑12** 自动化、**A‑13** 外部聊天、**A‑14** 语音、**A‑15** 体验性能、**A‑16** 交付与运行配对。按原范围验收，不默认从零做，也不冒称完成。

**更新规则：** 主控独占 TODO 和 Git 集成，子代理并行核对独立 owner 或来源证据。每有实际验证、候选提交、精确 pin 或阻塞变化，立即更新对应条目；只复跑有新增证据的验证。当前没有机器 Goal；G3 剩余范围明确后再推进产品待办，不把此次正式认证旅程当作全产品验收。
