# Kokoro 后端闭环任务总表

状态日期：2026-09-22。本文是本轮后端闭环的**唯一任务状态表**；历史任务由 Git 历史保存，不再与当前任务混排。主控 Agent 维护状态、依赖、负责人和验收证据，子 Agent 只更新自己获准任务卡中的交付信息。

## 1. 总目标与权威入口

- Goal：按已批准设计依次完成 Wave 0–7；Root 主控负责架构裁决、派工、双重审查、集成与最终验收，子 Agent 按 owner 逐仓实施；Billing 最后处理。
- 设计事实源：[`superpowers/specs/2026-09-20-kokoro-backend-closure-design.md`](superpowers/specs/2026-09-20-kokoro-backend-closure-design.md)
- 当前执行计划：[`superpowers/plans/2026-09-21-wave-0b-hard-link-closure.md`](superpowers/plans/2026-09-21-wave-0b-hard-link-closure.md)
- 已验收计划：[`superpowers/plans/2026-09-21-wave-0a-governance-and-contract-gates.md`](superpowers/plans/2026-09-21-wave-0a-governance-and-contract-gates.md)
- 证据账：[`progress.md`](progress.md)
- 本轮启动 Root 基线：`1bc74ae536d8a2da48f76045da95c2d5c2877750`
- 范围：`apps/kokoro-app` 与八个后端 owner；`apps/kokoro-mori` 和其他前端不参与业务改造。

## 2. 工作规则

状态只使用：`待派工 → 进行中 → 待审查 → 待集成验证 → 已验收`；真正无法继续时使用 `阻塞`，并写明阻塞条件和 owner。

1. 一个子仓同一时刻只有一个写入 Agent；Root 不抢写已派出的文件。
2. owner contract 先提交并推送，consumer 再切换；每个切片删除被替代路径，不保留双轨、alias 或 fallback。
3. 子 Agent 的测试与 commit 只是待验收交付；Root 必须重新审查 diff，并在冻结 SHA 上复跑对应门禁。
4. 子仓 commit/push 完成后，Root 才提升 gitlink；精确路径暂存，不使用 `git add .` 或 `git add -A`。
5. `docs/progress.md` 只记录已执行证据。设计、计划、口头报告和历史结果不算完成证据。

## 3. 当前任务卡

| ID | 优先级 | 业务目标 | Owner / 写入 Agent | 依赖 | 完成条件 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| W0A-0 | P0 | 建立 Goal、任务表、进度账和 Wave 0A 计划 | Root / 主控 | 已批准设计 | 四个入口互链；Root 文档门通过；当前 diff 与验证写入证据账 | 已验收 |
| W0A-1 | P0 | 统一数据库角色、协议矩阵与当前 Capability 身份的治理表述 | Root / `w0a1_governance_writer` | W0A-0 | `AGENTS.md`、架构标准、SQL 标准、CURRENT 无矛盾；治理测试锁定决定 | 已验收 |
| W0A-2 | P0 | 实现从 gitlink commit blob 校验 contract/evidence 的机器门 | Root / `w0a2_contract_verifier_writer` | W0A-1 | schema、gitlink、commit blob digest、状态与非法旁路负向测试通过；脏工作树不能影响结果 | 已验收 |
| W0A-3 | P0 | 冻结完整调用矩阵与 consumer inventory | Root / `w0a3_inventory_writer` | W0A-2 | 16 条批准 edge 与 Web→IAM 非法旁路完整登记；绑定 contract version、generator/runtime version 和 evidence digest | 已验收 |
| W0A-4 | P0 | 完成 Wave 0A 独立审查和 Root 集成验证 | Root / 主控 + `w0a_final_spec_reviewer` + `w0a_final_quality_reviewer` | W0A-1、W0A-2、W0A-3 | 规格审查与质量审查通过；Root 三项门禁和 compatibility 红门有当前输出 | 已验收 |
| W0B-0 | P0 | 冻结 W0B 执行计划与控制面 | Root / 主控 | W0A-4 | 计划 SPEC/EXECUTION 双审 `0/0/0`；task/progress/INDEX 切换完成；Root 门通过 | 已验收 |
| W0B-1 | P0 | 增加 consumer/producer 版本与精确 edge checkpoint 机器门 | Root / `w0b1_governance_writer` | W0B-0 | `.node-version`/`go.mod`/producer assertion 负例通过；三个 checkpoint 逐 edge 验证 | 已验收 |
| W0B-2 | P0 | 验证并修复 Capability 当前 HTTP owner release | Capability / `w0b2_capability_owner_verifier` → `w0b2a_capability_owner_writer` → 双审与独立复验 | W0B-1 | 四个 `/v1/*` GET、contract/runtime/docs/schema 一致；canonical `query`、参数边界与标准错误 envelope 锁定；全门通过；remote 可达 | 已验收 |
| W0B-3 | P0 | 冻结 BFF Capability 设计与 owner artifact | BFF / `w0b3_bff_capability_designer` | W0B-2 | commit-blob vendor/provenance 固定；三文档门通过；只接受 `query` | 已验收 |
| W0B-4 | P0 | 实现 BFF Capability generated consumer | BFF / `w0b3_bff_capability_designer`（续任） | W0B-3 | 四路由、身份、查询、错误、timeout/body cap 与生成漂移门通过；旧 `/bff/*` 删除 | 已验收 |
| W0B-5 | P0 | 实现 Capability↔BFF 隔离真实进程 smoke | Root / `w0b5_capability_bff_smoke_writer` | W0B-4 | 独占 DB/Redis/port/process；8 个 case 通过；失败也只清理自有资源 | 已验收 |
| W0B-6 | P0 | 集成并激活 `EDGE-BFF-CAPABILITY` | Root / `w0b6_capability_integration_writer` | W0B-5 | 子仓推送、gitlink/fan-out/version/evidence 更新；`w0b-capability` 精确通过 | 已验收 |
| W0B-7 | P0 | 验证 Scheduler owner release | Scheduler / `w0b7_scheduler_owner_auditor`（只读） | W0B-6 | `/schedules`、event header/RFC3339、幂等/重试与 docs/schema 一致；Go 全门通过 | 已验收 |
| W0B-7R | P0 | 修复 Scheduler 稳定错误机器契约与边界证据 | Scheduler / `w0b7r_scheduler_contract_writer` | W0B-7 审计 drift | OpenAPI/breaking policy/runtime parity锁定两个稳定错误；Nano与opaque key证据；完整 Go门通过 | 已验收 |
| W0B-7I | P0 | 集成 Scheduler 修复后的 owner release | Root / `w0b7i_scheduler_integration_writer` | W0B-7R | gitlink/全部 Scheduler fan-out/测试 pin/计划一致；edge 状态不变；Root checkpoint 通过 | 已验收 |
| W0B-7R2 | P0 | 修复真实 PostgreSQL 同名新键 create 的可持久化冲突结果 | Scheduler / `w0b7r2_scheduler_conflict_writer` | W0B-10 真实联调缺陷 | 新键重复 create 返回409并写receipt；重启replay；Go/PG/Redis全门；Root真实HTTP复验 | 进行中 |
| W0B-8 | P0 | 冻结 BFF Scheduler 控制/回调设计与 artifact | BFF / `w0b8_bff_scheduler_designer` | W0B-7 | control/receiver 边界、trusted tenant、opaque key + semantic digest、恢复语义确定 | 已验收 |
| W0B-9 | P0 | 实现 Scheduler generated control 与 receiver | BFF / `w0b9_bff_scheduler_writer` | W0B-8 | 旧协议删除；generated validation、专用 receipt/CAS、幂等与恢复测试通过 | 已验收 |
| W0B-9V | P0 | 修复基线已失败的两处 AG-UI fixture | BFF / `w0b9v_agui_fixture_writer` | W0B-9 全量门暴露 | 第二Run遵循admission；delete传requestId；原断言保持；独立PG复验通过 | 已验收 |
| W0B-10 | P0 | 实现 Scheduler↔BFF 隔离真实进程 smoke | Root / `w0b10_scheduler_bff_smoke_writer` | W0B-9、W0B-7R2 | 真实 Scheduler/BFF/DB/Redis；11 个 case；response-unknown + restart 不重复创建 | 进行中 |
| W0B-11 | P0 | 集成并激活 Scheduler 双向 edge | Root / integration 子 Agent | W0B-10 | BFF consumer generator/Node + Scheduler producer Go 证据固定；`w0b-exit` 通过 | 待派工 |
| W0B-12 | P0 | 冻结 BFF Storage fail-closed 与 W1/W2 前置 | BFF / Storage 子 Agent | W0B-11 | `GET /v1/library` 固定 503；授权矩阵、IAM admission、scope/pagination owner 明确 | 待派工 |
| W0B-13 | P0 | 将 Storage 前置绑定到 Root W1/W2 | Root / 主控 | W0B-12 | task/progress 记录 BFF docs SHA 与五项验收前置 | 待派工 |
| W0B-14 | P0 | 删除 BFF `/internal/bff/library` 运行链 | BFF / 同一 Storage 子 Agent | W0B-13 | 不打开 upstream socket；旧 URL/config/projector 全删；BFF 全门通过 | 待派工 |
| W0B-15 | P0 | 集成 Storage 死链删除但不激活 Storage | Root / integration 子 Agent | W0B-14 | 所有 BFF fan-out 更新；Storage edges 继续 broken；`w0b-exit` 与双 smoke 通过 | 待派工 |
| W0B-16 | P0 | W0B 双审与证据冻结 | Root / 主控 + 独立审查 | W0B-15 | SPEC/QUALITY `0/0/0`；4 active / 12 broken / 1 illegal 精确门；Root/子仓 clean main-only | 待派工 |
| W1 | P0 | IAM → BFF → Web 身份、授权与 same-origin 闭环 | IAM → BFF → Web，串行 | Wave 0 | admission、CSRF、tenant/actor/subject、越权负例与生成客户端通过 | 待派工 |
| W2 | P0 | Storage v2 完整命令、查询、幂等与数据闭环 | Storage → consumers | Wave 1 | Proto/runtime/generated drift、真实 PostgreSQL/ObjectStore、恢复测试通过 | 待派工 |
| W3 | P0 | `kokoro-capability` → `kokoro-platform` 原子切换 | Platform → Agent/BFF → Root | Wave 2、IAM workload auth | remote/path/package/service/env/Proto/数据库/Redis/consumer 同一窗口切换；旧身份删除 | 待派工 |
| W4 | P0 | BFF / Agent / Scheduler 事实 owner、投影、outbox 与恢复闭环 | BFF → Agent → Scheduler | Wave 3 | Conversation/Message 唯一归 BFF；Run/Evidence 唯一归 Agent；调度重复投递可恢复 | 待派工 |
| W5 | P1 | System generated HTTP client 与模型目录/运行控制闭环 | System → BFF/Agent | Wave 4 | owner contract、runtime parity、consumer pin 和 SQL 门通过 | 待派工 |
| W6 | P1 | Billing 最终契约、账本、支付与对账闭环 | Billing → BFF | Wave 5 | 唯一 runtime contract、幂等账本、webhook/reconciliation 和失败恢复通过 | 待派工 |
| W7 | P0 | Root 组合 E2E、release manifest 与最终验收 | Root / 主控 | Wave 1–6 | fresh clone、main-only、全 owner 门禁、跨仓 E2E、digest/image/SHA 清单全部绑定 | 待派工 |

## 4. W0A-0 当前变更范围

| 项 | 结论 |
| --- | --- |
| Owner | Root 治理；唯一 writer 为主控 Agent。 |
| 当前事实 | 旧 `docs/task.md` 混合数月历史，`.superpowers/**/progress.md` 被 Git 忽略，缺少可追踪的当前证据账。 |
| 目标职责 | `task.md` 只维护任务状态与依赖；`progress.md` 只维护执行证据；实施细节进入版本化 plan。 |
| 目录方案 | 采用已存在的 `docs/` 与 `docs/superpowers/plans/`；淘汰被忽略的 `.superpowers/` 作为权威台账，也不新建第二个 task 目录。 |
| 粒度 | 两份短期控制文档职责不同，计划单独版本化；不把全部内容塞回 `CURRENT.md`。 |
| 依赖 | 只链接 Root 权威文档；不复制 owner contract、Schema 或业务 DTO。 |
| 数据/API | 本切片不改变运行数据、Schema 或 API。 |
| 删除项 | 删除旧任务文件中的历史混排；历史仍可由 Git 查阅。 |
| 验证 | Markdown 链接检查、`verify-repository-topology.py`、`pytest scripts/tests`、精确 diff。 |

## 5. 每次交付必须写入的证据

```text
任务：<ID / owner / Agent 角色>
状态：已提交 / 部分完成 / 被阻塞
基线：<绝对路径 / main / 起始 SHA>
commit：<子仓 SHA；Root 集成后再补 Root SHA>
修改文件：<绝对路径清单>
验证：<命令 -> 实际退出码与通过/失败数>
审查：<规格审查 / 质量审查 / 对应 SHA>
未完成与风险：<明确列出>
后续 owner：<仓库 / Agent / 主控>
```
