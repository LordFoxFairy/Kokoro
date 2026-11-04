# Task A · 当前 TODO（2026-11-04）

此文件是执行清单；[技术方案](docs/superpowers/plans/2026-11-01-task-a-c1-c4-technical-plan.md)保留设计和验证明细，[CURRENT](docs/CURRENT.md)记录当前事实。新机器 Goal 已按本清单建立，状态 `active`；不把阶段通过算作 Task A 完成。

## P0：先收口 T‑11（BFF 原 PR #18）

- [x] **StableId 归并**：BFF 本地 `f7d1e69` 删除独立 Port 与无用传递链；保持唯一 SHA-256、原输入、前缀和截断。源码 lint、构建、定向测试、真实 PG/Redis 的 Chat 同键重放、Scheduler 接管与时钟夹具通过；资源清单复位，未推送。
- [x] **两个 AgentRuns reader 归并**：BFF `76f2d04` 直接注入现 `BFF_DATABASE`，删 Outbox 转发和两个独立 Port；SQL、期限和取消不变。生产 Nest 注入图、R146 授权/取消、R148 回滚、Submitted Run 历史恢复均通过，未推送。
- [x] **Personalization 归并**：BFF `335dbe3` 沿现 PG 实现收窄类型，保 Account token 和事务。真实 R257 读写、并发 CAS、COMMIT 结果未知、锁等待期间 HTTP 取消通过，未推送。
- [x] **ScheduledTask 拆分**：BFF `368e65e` 移除旧宽接口，现行读取、mutation、callback 各用具名能力，共用原 Pool、在线 SQL 和事务。真实 current read、DELETE 回执、callback 新旧 revision、终态及 outbox 通过；outbox 首次同库组跑有全局 claim 夹具干扰，独立空库补验通过。
- [ ] **Chat 拆分**：剩 Chat 本地宽聚合退出；按私有读/写、Archive、Shared list、Feedback、Move 的实际消费者收窄。
  - [x] BFF `c005e27`：RunDisplay 改用 Chat 会话归属与 AgentRuns 终态的具名读取，删除 Chat 的终态转发；原 SQL、准入复判与取消时序不变。构建、lint、变更文件格式、真实 Nest 接线/受控 HTTP、取消及隔离 PG 终态绑定通过；未推送。
  - [x] BFF `2ef307e`：AG‑UI 直接拥有 process/head，AgentRuns 只用窄会话授权与 head；Chat 快照沿原同一 RR client。R124 固定 watermark/快照、R57 控制准入与 ACK、R237 底层权限先于 cursor 解析均通过；未推送。
- [ ] **Projects 拆分**：按原 G0 分 Project/Pin/Recommendation/Task；Chat、ScheduledTask、Skill/MCP 等仅注入现有具名窄能力。保 Pool、SQL、锁和事务，不造兼容层或第二实现。
- [ ] 主控按子切片验收。只跑变化触及的真实行为；同 SHA 的归并前基线已通过，不重跑相同基线。共享 Nest 入口、架构断言和数据库 fixture 串行维护。

## P1：C‑4 最终组合（T‑11 通过后）

- [ ] **T‑09 终态配对**：确认跨仓写区后，Agent #46 原件 → BFF #18 公开契约、domain、canonical SQL → App #50 唯一 public 快照。承接 `context_window_exceeded / retryable: false`，不启用 `personal_context`，保 Scheduled 原拒绝边界。使用原生成器；证明原始终态可持久化、回放、显示且不提示重试。
- [ ] **最终版本与 owner 门**：IAM #6、Capability #13、Agent #46、BFF #18、App #50 各沿原 PR。Agent #46 远端 head 为 `codex/agent-run-lifecycle`；Capability #13 保持原 PR #12 为 base。验收后的精确子仓提交在原 PR 可达后，再由 Root #66 更新 gitlinks；不冻结已知不兼容组合。
- [ ] **组合验收**：核 Root 拓扑、受影响 owner 正式门及实际原生浏览器旅程（固定域登录、异租户拒绝/恢复、登出、撤权）。补受影响业务接缝的真实验收；明确记录失败、跳过、未运行。
- [ ] **T‑15 同步环境**：正式验收后，用现原生前台入口按支持范围交接；记录入口、可测旅程、日志索引、启停和回收负责人。临时 smoke 退出不等于同步环境；现旧 HTTP/`--chat` 不算原生入口。

## 已验阶段与仍在的遗留项

| 项目 | 证据或未完成原因 |
| --- | --- |
| C‑1.3 / G1 | Root `4e603743` 原冻结组合有真实认证旅程和负控；新版组合未验。 |
| T‑17 | BFF `09f44fe` 本地已提交；实测正常信号退出、端口冲突和 31 秒硬期限。 |
| T‑11 基线 | BFF `45a2989` 的 R146、R189、Submitted Run、ScheduledTask outbox 真库回归通过；不是新代码验收。原 MinIO 卷已恢复，登记空桶已回收，未清卷重建。 |
| C‑4 候选 | IAM `b6a9745`、Capability `5e607fd`、Agent `40effb2` 有各仓证据；BFF 正式 `check` 首轮有权限夹具失败，原负控另行补过，`45a2989` 仅格式。App `197f1102` 尚未消费新终态。 |
| Root 差额 | 四个 gitlink 尚未跟上本地候选；结构审计仍失败。区分已存在的规则告警、未核实工具链、接入 Capability 上游后新增的文件粒度告警与本次真实阻断；不为清数字而改业务或放松审计。单库 owner schema 与最终常驻环境仍待实证。 |
| 运行边界 | 默认 HTTP/Chat 旧探针不计验收，当前无最终组合的同步端到端环境；CI/部署未运行。历史测试去重仅验证已盘点范围，不用数量代替行为验收。 |

## P2：门控的原 Task A 产品待办

- [ ] C‑1.3～C‑4 闭环后才开始 **A‑01 会话创建/恢复、A‑02 Agent 过程/详情**，随后 **A‑07 Project Todo**。
- [ ] 保留 **A‑03 输入与运行控制、A‑04 执行恢复、A‑05 长上下文、A‑06 项目上下文**。
- [ ] 保留 **A‑08 附件、A‑09 资料库、A‑10 文件/Canvas、A‑11 首页、A‑12 自动化、A‑13 外部聊天、A‑14 语音、A‑15 体验性能、A‑16 交付与运行配对**。按原方案逐项核量，不按全部从零估时，也不标已完成。

每仓只沿自己的 PR，不合并 `main`、不部署。每轮只更新实际推进项和证据；完成条件是 T‑11 处置通过、C‑4 精确组合及受支持端到端已验证，非测试数量或文档提交数。
