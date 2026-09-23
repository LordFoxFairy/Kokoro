# Kokoro 后端闭环任务总表

状态日期：2026-09-23。本文是本轮后端闭环的**唯一任务状态表**；历史任务由 Git 历史保存，不再与当前任务混排。主控 Agent 维护状态、依赖、负责人和验收证据，子 Agent 只更新自己获准任务卡中的交付信息。

## 1. 总目标与权威入口

- Goal：按已批准设计依次完成 Wave 0–7；Root 主控负责架构裁决、派工、双重审查、集成与最终验收，子 Agent 按 owner 逐仓实施；Billing 最后处理。
- 设计事实源：[`superpowers/specs/2026-09-20-kokoro-backend-closure-design.md`](superpowers/specs/2026-09-20-kokoro-backend-closure-design.md)
- 当前执行计划：[`superpowers/plans/2026-09-23-wave-1c-web-oidc-and-same-origin.md`](superpowers/plans/2026-09-23-wave-1c-web-oidc-and-same-origin.md)
- 已验收 Wave1B：[`superpowers/plans/2026-09-22-wave-1b-bff-admission-and-privacy.md`](superpowers/plans/2026-09-22-wave-1b-bff-admission-and-privacy.md)
- 已验收 Wave1A：[`superpowers/plans/2026-09-22-wave-1a-iam-session-admission.md`](superpowers/plans/2026-09-22-wave-1a-iam-session-admission.md)
- 已验收 Wave0B：[`superpowers/plans/2026-09-21-wave-0b-hard-link-closure.md`](superpowers/plans/2026-09-21-wave-0b-hard-link-closure.md)
- 已验收计划：[`superpowers/plans/2026-09-21-wave-0a-governance-and-contract-gates.md`](superpowers/plans/2026-09-21-wave-0a-governance-and-contract-gates.md)
- 证据账：[`progress.md`](progress.md)
- 本轮启动 Root 基线：`1bc74ae536d8a2da48f76045da95c2d5c2877750`
- 范围：`apps/kokoro-app` 与八个后端 owner；`apps/kokoro-mori` 和其他前端不参与业务改造。

### 1.1 主控优先看这里

- 当前关键路径：**W1C Web OIDC/同源接线 → Web→BFF→IAM真实浏览器组合 → W1D Web Product generated consumer/AG-UI → Storage owner与消费边界**；BFF `cd1c260…`/IAM `b838853…` 当前pin的旧owner真实回归与首次OAuth 15/15已复验，Root runner待发布；这些均不代表Web或完整聊天执行链已闭环。具体状态与唯一写入负责人见本文Wave1C执行卡。
- 后续按能力依赖推进 Storage → Platform → 聊天执行链 → System；支付最后。聊天的完成定义以本文第7节能力矩阵为准，包含消息落库、流式恢复、取消、HITL、附件/产物，而不是仅页面能展示文本。
- 每片交付必须是可运行代码、对应行为测试和必要契约/SQL更新；文档整理或生成客户端不单独等于功能完成。
- 当前不深入部署、生产角色隔离、镜像、SLO、网络硬化和重复全仓审计；这些进入统一发布收尾。身份/越权、事务、幂等、取消和故障恢复属于产品正确性，继续随代码验证。
- 用户本轮资源裁决：开发应用目标只复用**一个 PostgreSQL 实例、一个数据库、一套应用账号**和现有 Redis；每个数据 owner 使用独立 schema/连接 URL 与代码写入边界，表名前缀不替代 schema。不建多 role 或长期独立库。当前部分 owner 的 `public`/整库空白 installer 尚未适配，单库应用组合**未通过**；按 owner 代码切片收敛，不做运维专项。现有测试 fixture 临时库/前缀仅用于测试隔离且只清理自身，不是应用并发或数据库角色限制。

### 1.2 能力边界（不互相代写事实）

| Owner | 负责 | 明确不负责 |
| --- | --- | --- |
| `kokoro-app` | 页面、交互状态、浏览器会话、同源adapter、AG-UI视图映射 | 不直连内部owner、不保存业务数据库事实 |
| `kokoro-bff` | Conversation/Message/Share/Project/ScheduledTask、资源权限、durable AG-UI投影 | 不执行模型/工具、不读取其他owner数据库 |
| `kokoro-iam` | 登录、会话、租户/成员与身份授权事实 | 有效会话不等于能读同团队其他人的聊天 |
| `kokoro-agent` | Run、工具执行、HITL/Approval、Checkpoint、执行事件/Evidence | 不另建Conversation/Message或公开事件账本 |
| `kokoro-storage` | 上传、Blob/Asset/Artifact、对象生命周期与访问边界 | BFF/Agent不复制存储模型或绕过文件授权 |
| Capability → Platform | Skills/MCP控制面与授权能力供给；按既定切片原子更名 | 不作为任意共享代码/业务的收容仓；当前名称仍为Capability |
| `kokoro-scheduler` | Schedule/Occurrence、触发、投递、重试与receipt | 不拥有BFF产品任务或Agent Run |
| `kokoro-system` | 站点/运行控制、模型目录与路由配置 | 不作为任意key/value配置中心 |
| `kokoro-billing` | 支付、订阅、额度、账本、计量与对账 | 本轮其他核心能力开发不被支付实施阻塞 |

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
| W0B-7R2 | P0 | 修复真实 PostgreSQL 同名新键 create 的可持久化冲突结果 | Scheduler / `w0b7r2_scheduler_conflict_writer` | W0B-10 真实联调缺陷 | 新键重复 create 返回409并写receipt；重启replay；Go/PG/Redis全门；Root真实HTTP复验 | 已验收 |
| W0B-8 | P0 | 冻结 BFF Scheduler 控制/回调设计与 artifact | BFF / `w0b8_bff_scheduler_designer` | W0B-7 | control/receiver 边界、trusted tenant、opaque key + semantic digest、恢复语义确定 | 已验收 |
| W0B-9 | P0 | 实现 Scheduler generated control 与 receiver | BFF / `w0b9_bff_scheduler_writer` | W0B-8 | 旧协议删除；generated validation、专用 receipt/CAS、幂等与恢复测试通过 | 已验收 |
| W0B-9V | P0 | 修复基线已失败的两处 AG-UI fixture | BFF / `w0b9v_agui_fixture_writer` | W0B-9 全量门暴露 | 第二Run遵循admission；delete传requestId；原断言保持；独立PG复验通过 | 已验收 |
| W0B-10 | P0 | 实现 Scheduler↔BFF 隔离真实进程 smoke | Root / `w0b10_scheduler_bff_smoke_writer` | W0B-9、W0B-7R2 | 最终BFF c5e9b3c + Scheduler975dee59；真实11case通过，loopback/资源清理通过，Agent为receipt stub | 已验收 |
| W0B-5R | P0 | 修复Capability smoke同源资源/HTTP生命周期缺陷 | Root / `w0b5r_capability_smoke_writer` | W0B-10代码审查通过、writer停写 | 已创建DB/Redis确认丢失、预存保护、HTTP线程回收回归；新BFF pin；真实8case与清理通过，独立提交；最终9c88d0d/c5e9b3c监听前置及8case通过；105行fixture例外已关闭 | 已验收 |
| W0B-2B | P0 | 补齐Capability owner显式监听地址与loopback验收 | Capability / `w0b2b_capability_listener_writer` | Root发现main.ts硬编码0.0.0.0 | runtime配置/入口/测试/docs一致；实际监听loopback；release先apply后check；修复Root复现的并行receipt fixture隔离；owner门通过；新release后consumer pin刷新（Root集成另计） | 已验收 |
| W0B-10R | P0 | 修复Scheduler smoke无ownership marker的预存Redis prefix保护 | Root / `w0b10r_scheduler_prefix_writer` | W0B-5R同源审查 | 预存prefix无SET/UNLINK；未知inventory fail-closed；现有生命周期不退化 | 已验收 |
| W0B-11 | P0 | 集成并激活 Scheduler 双向 edge | Root / 主控 + 独立双审 | W0B-10、W0B-5R、W0B-2B、W0B-10R | BFF consumer generator/Node + Scheduler producer Go 证据固定；`w0b-exit` 通过 | 已验收 |
| W0B-12 | P0 | 冻结 BFF Storage fail-closed 与 W1/W2 前置 | BFF / `w0b12_14_bff_storage_preflight` 转任同仓实现 | W0B-2B 已验收；Root批准22文件与文档门 | `GET /v1/library` 固定 503；授权矩阵、IAM admission、scope/pagination owner 明确 | 已验收 |
| W0B-13 | P0 | 将 Storage 前置绑定到 Root W1/W2 | Root / 主控 | W0B-12 | task/progress 记录 BFF docs SHA 与五项验收前置 | 已验收 |
| W0B-14 | P0 | 删除 BFF `/internal/bff/library` 运行链 | BFF / 同一 Storage 子 Agent | W0B-13 | 不打开 upstream socket；旧 URL/config/projector 全删；BFF 全门通过 | 已验收 |
| W0B-15 | P0 | 集成 Storage 死链删除但不激活 Storage | Root / 主控 + 独立双审 | W0B-14 | 所有 BFF fan-out 更新；Storage edges 继续 broken；`w0b-exit` 与双 smoke 通过 | 已验收 |
| W0B-16 | P0 | W0B 双审与证据冻结 | Root / 主控 + 独立审查 | W0B-15 | SPEC/QUALITY `0/0/0`；4 active / 12 broken / 1 illegal 精确门；Root/子仓 clean main-only | 已验收 |
| W1 | P0 | IAM → BFF → Web 身份、授权与 same-origin 闭环 | IAM → BFF → Web，串行 | Wave 0 | admission、CSRF、tenant/actor/subject、越权负例与生成客户端通过；Storage消费必须先有BFF IAM admission | 进行中 |
| W2 | P0 | Storage v2 完整命令、查询、幂等与数据闭环 | Storage → consumers | Wave 1 | Proto/runtime/generated drift、真实 PostgreSQL/ObjectStore、恢复测试通过；先固定default-deny caller×operation×scope、Capability scope与Agent可信ExecutionIdentity映射、Library分页，且依赖W1 admission | 待派工 |
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


## 6. Wave 1 启动任务卡（2026-09-22）

批准依据为整体设计 Wave1；Root 基线 `136e12d7f751b7b77c5a16f8a36fa1df32f97b50`。以下为已完成盘点的冻结任务卡；当前执行授权以 Wave1A 执行卡和精确计划为准，不扩展总架构或恢复 W0B 旧工作。

| ID / 目标 / 优先级 | Owner / Agent / 模型 / 模式 | 基线与绝对工作目录 | 范围 / 依赖 / 验证 / 交付 |
| --- | --- | --- | --- |
| W1-P1：确认 IAM admission/workload 契约与 SQL 差距；P0 | IAM / `w1_iam_owner_auditor` / gpt-5.6-sol high / 只读，Root 审查 | `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-iam`；main `35d868a410c06731362bd1e8bcc3e602d01875f8`，clean | 读取三文档/contract/schema/身份代码与测试；不改文件/Git/基础设施；依赖批准设计和三大手册；输出精确 operation、缺陷证据、最小实现文件集及无破坏验证命令；Root 后续唯一提交人 |
| W1-P2：核实 Web same-origin 与核心聊天验收面；P0 | Web / `w1_web_chat_auditor` / gpt-5.6-sol high / 只读，Root 审查 | `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-app`；main `ce4e466c960c4b40a87a7be38b5a56f265f7a12f`，clean | 只读 session/CSRF/AG-UI/聊天/工具/审批/历史/附件/测试；排除 Mori；不改文件/Git/基础设施；与 P1 独立并行；区分真实、替身、缺失，输出浏览器验收矩阵与文件证据；Root 后续唯一提交人 |
| W1-P3：确定 BFF admission 及交接边界；P0 | BFF + Root / 主控 / 当前模型 / 只读分析，Root 控制文档唯一 writer | `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff`；main `c5e9b3cc8eb134ff72e37f56ac1f95ebec4f42e7`，clean | 核对 auth/routes/projection/contract 与真实 owner 依赖；P1/P2 完成后冻结 Wave1 精确实施计划；现阶段不改子仓，不启动共享服务 |

验收方向：用户核心是可运行的完整对话体验。后续统一验收矩阵覆盖发送/流式/取消/重连/历史、结构化工具进度与结果、HITL 审批/恢复、附件/产物、错误与跨 tenant 隔离；W1 先交付可信身份入口，AG-UI/执行/Storage 完整闭环仍按 W2–W4 依赖实施。对照体验不等于宣称复制任何外部产品全部能力。

用户已确认（2026-09-22）：聊天和文件默认个人私有，显式分享才开放。当前验收同时覆盖同 tenant 不同用户与跨 tenant 负例；Project/Share 不自动授予 Run control/HITL/未分享文件访问。详见批准设计 §1.1。


### Wave1A 执行卡

| ID | 目标 / 状态 | Owner / Agent / 模型 | 基线 / 范围 / 验证 / 交付 |
| --- | --- | --- | --- |
| W1A-1 | 发布用户session admission；已验收 | IAM / w1_iam_owner_auditor / gpt-5.6-sol high；Root审查 | main35d868a4，绝对目录及精确文件集见当前计划；P1/P2盘点完成，682测试基线；不写Root/BFF/Web/schema；真实撤销矩阵+全门；Root唯一Git提交人 |
| W1A-2 | Root review/组合；已验收 | Root主控 + 独立审查 | 依赖W1A-1停写交付；计划Task2精确Root集成范围，edge状态不变，main-only/remote/clean真实审计 |

## 7. 核心聊天体验验收矩阵（P2 盘点，不是完成证据）

| 面 | 当前可验证代码事实 | 必须交付的真实闭环 | 后续owner |
| --- | --- | --- | --- |
| 身份入口 | Web旧magic-link直连IAM，无Auth.js/OIDC；CSRF缺Origin放行 | 当前issuer→BFF→Web同源，cookie/refresh/logout、无origin拒绝、身份撤销 | W1 IAM/BFF/Web |
| 发送与流式 | 已有AgUiChatTransport和durable BFF Chat；现验收主要fixture | 真实用户发送→Agent执行→持久消息→逐帧UI；刷新后结果一致 | W4 BFF/Agent/Web |
| 取消与恢复 | 本地stop、retry存在；UI缺完整queued/resuming/cancelling/reconnecting态 | 后台真正取消、竞态/重复、断网恢复、cursor过期回补，不生成重复消息 | W4 |
| 工具与HITL | mapper/多项staging有代码，主要fake测试 | 工具输入/进行中/结果、全部pending一次resume、刷新与重复审批、权限负例 | W3/W4 |
| 附件/产物 | 输入消息无attachment字段；文件展示主要fixture | 私有上传/扫描/下载、产物关联与恢复、同tenant他人拒绝、显式分享撤销 | W2/W4 |
| 编辑/重新生成 | 当前未实现，不能当现有能力 | 单独冻结branch/重生成语义与幂等、历史，后续契约切片实施 | W4 |
| 隐私 | BFF chat已有owner predicate；Project查询/缓存、ScheduledTask列表仅tenant，尚未个人隔离 | 同tenant A/B 与跨tenant列表/详情/事件/控制/文件/项目负例全通过 | W1/W2/W4 |
| 浏览器体验 | Playwright主要preview/login/axe/viewport | live聊天桌面/移动端、键盘IME、loading/error/partial/disabled、无障碍与恢复 | W4/W7 |

W1A-R：只读规格/质量审查，由 `w1a_task_reviewer`（gpt-5.6-sol/high）执行；范围为 IAM 基线35d868a4至冻结43文件，manifest/diff位于本计划scratch；不写代码/Git，不启动共享服务。Root并行复跑owner门，审查报告后统一裁决。

W1A-F：最终组合只读审查，由 `w1a_final_reviewer`（gpt-6-astra/high）执行；范围为Root当前计划集成diff与IAM35d868a4→30f7dbf两提交，重点consumer发布证据、gitlink/inventory和未完成边界；不重跑owner全门、不写仓库、不改index。

### Wave1B 执行卡（先文档门，再逐片实现）

当前节奏（用户2026-09-22裁决）：以功能代码、针对性测试和最小真实联调推进；运维加固、部署、镜像、SLO及重复全仓审计后置。身份/私有资源负例与数据正确性继续作为开发验收，不扩张成运维项目。

Owner为BFF；前置IAM release `259a66e6a569889c030734f380e99685d8b9e21c`、OpenAPI0.2.0已可固定消费。主控先冻结BFF三文档与精确文件集，再派同仓唯一负责人。目标是Node22 generated admission、删除自报header身份来源、明确public share/Scheduler服务边界，并承接已确认的同tenant私有资源权限缺口；Web OIDC/CSRF接线随后推进。不重复已验收W0B/W1A，也不提前激活edge。

| ID / 目标 | Owner / Agent / 模型 / 模式 | 基线与范围 | 完成条件 / 交付 |
| --- | --- | --- | --- |
| W1B-P：私有资源访问矩阵复核 | BFF / `w1b_privacy_reviewer` / gpt-5.6-sol high / 只读 | `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff`，main `c5e9b3cc8eb134ff72e37f56ac1f95ebec4f42e7`，clean；Project/Task/ScheduledTask/Chat/Share/AG-UI 的路由、repository、schema、cache、receipt、测试；排除其他仓写入与所有 Git/基础设施操作 | 每个缺口绑定具体文件和调用路径，给出最小修改集、同 tenant / 跨 tenant 负例以及服务回调例外；Root 定义最终架构与审查；状态：已验收（只读审查交付，不代表缺陷已修复） |

Root 并行负责 IAM admission、bootstrap/service 例外与 Node22 generated client 的实施设计；这里只扩展已有任务台账，不改变业务职责或授权运行代码重写。

| ID / 优先级 | Owner / Agent / 模型 | 基线 / 范围 | 验收 / 状态 |
| --- | --- | --- | --- |
| W1B-1 / P0 | BFF / `w1b_bff_owner` / gpt-5.6-sol high / 唯一写入 | main c5e9b3c → a898c90fe2b5447178a76fb04b0fedf9fa98e0d5，绝对目录同上；64个精确文件，Root提交 | SPEC/QUALITY通过；Root最终227标准/35真实integration、静态门通过；代码切片已验收，跨仓组合归W1B-3 |
| W1B-1R / P0 | BFF / `w1b1_task_reviewer` / gpt-5.6-sol high / 只读；Root集成验证 | c5e9b3c + 最终冻结64文件，与a898c90提交字节一致；未操作Git/基础设施 | 首轮2 Important均已修复；增量复核SPEC Compliant/QUALITY Approved，0未决；状态：已验收 |
| W1B-2 / P0 | BFF / 原`w1b_bff_owner`额度中断后Root唯一写入、`w1b2_privacy_review`只读复核 | `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff`，main a898c90 → `6238599667110fbfbc2d5ef3a9d53731f2623cfe`，35文件，已推送、clean；原Task2范围加批准的旧fixture修复 | Root Node22 format/lint/typecheck/contract25/标准231/schema4/build/fresh PG+Redis integration37全绿；独立审查2条P2已修复复核无新阻断；自有DB回收、Redis8不变；BFF owner切片已验收，跨仓组合归W1B-3 |
| W1B-3 / P0 | Root主控 + 独立审查 | IAM/BFF owner及Root `7b6e486b…`组合已推送main，旧smoke均接线且通过 | 真实IAM↔BFF 7/7、Capability8/8、Scheduler11/11、System组合PASS；新checkpoint5/11/1与main-only/clean PASS；状态：已验收（仅本组合切片，W1/Web未完成） |
| W1B-3P / P0 | IAM测试入口 / `w1b3_iam_fixture_reader` / gpt-5.6-sol high / 只读；Root审查 | `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-iam`，main 259a66e6；仅既有HTTP fixture/consumer测试/API入口，不写文件/Git、不启动服务、不操作数据库；与BFF Task2独立 | 已定位真实PKCE/session/在线membership与自有资源fixture；Root可复用本地测试CLI，不需IAM部署改造；状态：已验收（只读预检，不是联调通过） |
| W1B-3A / P0 | IAM测试入口 / `w1b3_iam_host_owner` / gpt-6-sol / 唯一写入；Root复验提交 | `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-iam`，main 259a66e6→`b2ad9dd6906b73f275b96d570dad66eae86e97e9`，两文件，已推送clean；不碰生产入口/schema/contract/lockfile | NDJSON真实IAM host与3项聚焦integration、Node24 typecheck/format/lint均通过；Root独立资源快照确认零新DB/Redis键；独立复审P1/P2均关闭。IAM测试入口已验收，Root消费仍归W1B-3B |
| W1B-3B / P0 | Root真实IAM↔BFF组合 / `w1b3_root_iam_smoke_writer` / gpt-6-sol / 仅两脚本写入；Root审查与Git唯一负责人 | Root `77c9c5db`→`1d1c4df85fd7b7d39a8465d9746ac2be59b5ba4d`，IAM gitlink→`b2ad9dd…`，BFF `6238599…`不变；两脚本、台账与106 BFF/3 IAM机械fan-out已推送 | Root提交后无过渡参数真实HTTP **7/7**，SHA/clean/gitlink均匹配，w0b-exit checkpoint通过；独立P1/P2已关闭，自有资源清理通过。IAM edge仍broken待W1B-3C/D；状态：已验收 |
| W1B-3C / P0 | Root旧Capability/Scheduler smoke准入改造 / `w1b3_legacy_smoke_writer` / gpt-6-sol / 唯一脚本writer；Root审查、Git与台账负责人 | Root `1d1c4df…`→`0295fbdda439a4008cb114c8d726cf893694fc4b`已推送main；9个获授权脚本/测试，新增共享IAM wire stub，未改子仓/System | Root聚焦**110/110**、全scripts **524/524**，真实Capability **8/8**、Scheduler **11/11**及自有资源清理均通过；独立审查2项P2已修复复核无新阻断，w0b-exit与topology PASS。stub只供旧owner回归；状态：已验收 |
| W1B-3D / P0 | Root System跨仓smoke新准入与路径修复 / `w1b3_legacy_smoke_writer`（续任）/ gpt-6-sol / 唯一脚本writer；Root审查与Git负责人 | Root `0295fbdd…`→`9fa6d2cd68d06dbd9dc235da520ba4c15089b1e1`已推送main；仅System runner与对应测试，子仓不改 | Root聚焦**23/23**、全scripts **525/525**、真实System/BFF/Agent组合PASS、独占PG/Redis/临时文件零残留；独立审查1项P2 gitlink门已修复复核无新阻断；状态：已验收 |
| W1B-3E / P0 | Root激活BFF→IAM精确契约edge / Root唯一writer + `w1b3_edge_release_review`独立只读审查 | Root `9fa6d2cd…`→`7b6e486b630a40ff825736299ef02720cbfbef6a`已推送main，IAM `b2ad9dd…`/BFF `6238599…`clean；只改Root inventory/checkpoint/test/文档 | 唯一IAM edge broken→active，31个consumer blob与IAM0.2.0 contract/旧vendor字节一致，2项版本断言；checkpoint **5 active/11 broken/1 illegal**、聚焦81/81、全Root526/526、topology及main-only（Root+11仅main/clean）PASS；独立SPEC/QUALITY0/0。状态：已验收 |
| W1C-P / P0 | Web同源登录依赖预检 / `w1c_web_auth_reader` + `w1c_iam_oidc_readiness` / 只读；Root裁决 | Web `apps/kokoro-app` main `ce4e466c…`，BFF `apps/kokoro-bff` main `6238599…`，IAM `b2ad9dd…`；仅读Web auth/session/cookie/CSRF route及BFF/IAM协议，不改文件/Git/资源 | 已确认IAM Code+PKCE与精确allowlist已运行；BFF尚无`/iam` relay，Web旧IAM直连且多数BFF代理缺Bearer；两份只读报告已交付，未运行测试；状态：已验收（只读预检） |
| W1C-1 / P0 | BFF受控`/iam`原生协议relay / `w1c_bff_relay_owner`实现、来源重pin由Root集成 | BFF `cd1c2600…`、IAM `b838853a…`及Root `bb60a6a…`已推送main | 精确path/method服务例外、原生HTTP/cookie/redirect保持；BFF Node22标准248/248、contract25/25；当前pin真IAM7/Capability8/Scheduler11/System及首次OAuth15/15均复验，自有资源0；1H脚本已发布。状态：IAM→BFF relay切片已验收，Web浏览器链另验 |
| W1C-1F / P0 | IAM test-owned Web OIDC首次流fixture / `w1c_iam_flow_owner`唯一IAM writer；Root审查 | IAM `f0bb18e6…` fixture、`c9a27721…`退出URI修正均已推送main；仅测试文件，生产API/schema/contract未改 | HTTPS公开origin、未预consent RP client、真实sign-in→authorize首次重定向；Root聚焦5/5、退出URI修正后5/5，自有DB/Redis零残留，独立初轮复审0 P1/P2；完整Code+S256/tenant/consent/token/userinfo/logout仍归Root组合，状态：已验收（测试入口） |
| W1C-1G / P0 | Root从gitlink commit blob核验BFF relay↔IAM发布证据 / `w1c_root_relay_verifier`实现、独立审查，Root集成 | Root脚本 `070b0589…`、新IAM/BFF/Web gitlink及库存 `a5ca0afc…`已推送main | 固定IAM allowlist/snapshot与BFF policy的commit/digest、route/method子集/disabled负例；最新pin真实CLI/checkpoint/topology PASS，Root全量545 passed+10 subtests，独立库存审查0 P1/P2；状态：已验收（来源门，不替代OAuth正向行为） |
| W1C-1H / P0 | Root真实IAM→BFF relay首次OAuth正向组合 / 原脚本writer与首修writer、`w1c_oidc_runner_fix2`唯一Root脚本writer；Root与独立审查 | IAM `b838853…`、BFF `cd1c260…`及Root `bb60a6a466c73940ce7e1f19d7efcb0742571dea`已推送main | 第二轮四项P1/P2均修复、独立复审0 P1/P2；Root独立真HTTP首次无session登录→签名continue→tenant→consent→Code+S256/token/userinfo/revoke/logout **15/15**，Root全scripts **563 passed、56 subtests**，自有资源0；发布后relay policy/checkpoint/topology PASS。无hint HTML logout只单测，归1J；状态：已验收（仅IAM→BFF，不是Web浏览器闭环） |
| W1C-1I / P0 | IAM test-owned OIDC host精确public JWKS回环 / `w1c_iam_flow_owner`唯一IAM writer；Root审查/Git | IAM `b838853a81ff34bd0f7a079ccc75ba6abd61d1ec`已提交推送main，BFF机械policy来源`cd1c260…`已发布 | 仅IAM两测试文件，精确issuer `/jwks`→fixture loopback；Root独立Node24真实登录→带hint退出聚焦5/5、format/lint/typecheck、资源0；独立审查0 P1/P2，非阻断P3 restore直接断言缺口；生产代码/contract/schema不变。Root组合15/15已复验；状态：IAM owner切片已验收 |
| W1C-1J / P1 | BFF relay无hint退出metadata只读审查 / `w1c_bff_logout_metadata_reader`；Root裁决 | BFF main `cd1c260…`、IAM `b838853…`、Root `85e06c53…`，未改BFF/Web | Better Auth在无hint且非导航时返回400；BFF/Web已保留`Accept`但不透传`sec-fetch-*`。Web带server-only `id_token_hint`的主路径已真HTTP15/15；无hint HTML确认为单独可选验收，不阻断2B/3，不为此改BFF。状态：只读审查已验收 |
| W1C-2 / P0 | Web Auth.js RP、同源adapter与Product Session / Web单仓分片唯一writer；Root审查/Git | Web三文档、2A、2B-1及2B-2源码已分别发布，最新Web `14e23e602a5631009584d84f58871e51d32b821c`；BFF `a4dbc333…`/IAM `6bc9b19…`来源固定 | 三页同源交互与CSRF已有Web owner证据；Auth.js Code+S256 callback、Product Session、全代理Bearer、旧IAM直连删除未完成，Root gitlink/真实三服务组合待集成。状态：部分完成，不是登录闭环 |
| W1C-2A / P0 | Web固定policy来源与同源只读`/iam`入口 / `w1c_web_get_relay_owner`唯一Web源码writer，Root审查与Git负责人 | Web `38683a5…`→`85b4bad25769efcca8f417e0232fdaa6c485bf01`、Root `6f7b31c29f019f1306e6ebd03b7ccca725c729b3`已推送main；BFF `cd1c260…` policy digest `457909cd…`字节相同 | 两轮审查发现的P1/P2全修，增量独立复审0 P1/P2；Root独立Node22 `pnpm check`（1259 tests）与Playwright6/6、Root 563脚本、policy/checkpoint/topology通过，真实Next HTTP含chunked拒绝/零BFF及隔离目录清理。Root发布后main-only/topology/policy/checkpoint PASS、全12仓clean。GET窄子集已发布；Auth.js/POST/userinfo/end-session仍未接线，浏览器登录不成立；状态：Web与Root集成均已验收 |
| W1C-2B-1 / P0 | Web交互POST/CSRF与最小真实续接 / `w1c_web_post_foundation_owner`唯一writer；Root审查/Git | Web `85b4bad25769efcca8f417e0232fdaa6c485bf01`→`d619f2c06951cb2decdb1eeac48547e3bcf40361` 已推送main且clean；27文件，含Redis server-only依赖/lock、env/CI与现有原生Location策略定点扩展 | 独立复审原1 P1/2 P2已修复0 P1/P2，P3 302回归亦补；Root Node22 `pnpm check` contract52/architecture32/标准1297与lint/typecheck/build、Playwright6/6，Redis9 0→0。仅sign-in交互，Auth.js/Product Session/旧IAM直连仍待后续；Root gitlink/库存已随`20112fcb…`集成；完整Web→BFF→IAM浏览器登录仍待RP。状态：Web owner与Root来源集成已验收 |
| W1C-2B-2 / P0 | Web Tenant选择与Consent两页安全续接 / `w1c_web_post_foundation_owner`唯一writer；Root审查/Git | Web `d619f2c…`→`14e23e602a5631009584d84f58871e51d32b821c`，17文件已推送main且clean；BFF `a4dbc333…` policy原字节、IAM `6bc9b19…`来源 | 独立初审1 P1（issuer cookie Path）及终审2 P2（删除cookie后CSRF、HEAD/OPTIONS）均按TDD修复，最终0 P0/P1/P2。Root Node22 `pnpm check`：contract52、architecture32、标准1320、lint/typecheck/build均PASS；Playwright6/6。真实Next+Path-aware CookieJar/session-required BFF fixture证明三页续接、静态路由、删除cookie及405零BFF/Redis；RP callback受控503，非真实IAM/RP闭环。Root gitlink/库存已随`20112fcb…`集成；状态：Web owner与Root来源集成已验收，RP/真浏览器组合待办 |
| W1C-2C / P0 | Web Auth.js RP + server-only token/userinfo / Web下一唯一writer；Root先核当前IAM client与Auth.js兼容后派工 | 前置：2B-2 Web `14e23e6…`与Root来源集成；当前旧`auth.ts`仍直连IAM，最终callback仍503 | 按Code+S256/state/nonce/固定URI与唯一resource完成可信RP transaction，先测试callback/code重放、错误/凭据清洗，再实现Product Session；不得用旧sealed envelope双轨冒充登录。状态：待派工 |
| W1C-DB / P1 | 单开发数据库的 owner-schema 代码适配 / 各数据owner逐仓唯一writer，Root按依赖集成 | 用户明确一个应用库/一套账号；BFF `a4dbc33…`与IAM `6bc9b19…` owner代码已发布，Root同库双schema installer已验；其他数据owner尚未完成 | 每仓连接只指向自己的schema、fresh install只检查本schema，统一同一物理应用库真HTTP组合；不建多角色/长期子库，测试临时资源仍归fixture。状态：BFF/IAM部分完成，Root组合及其余owner待办 |
| W1C-DB-BFF / P1 | BFF单应用库owner-schema首个代码切片 / `w1c_bff_logout_metadata_reader`唯一writer；Root审查/Git | BFF `cd1c2600…`→`06a478403c92eeede0c54ed1f53022f0ff60d79e` 已推送main且clean；29文件，canonical SQL/OpenAPI/package/lock未变 | 独立复审0 P1/P2；Root Node22 format/check 253/253、真实schema 6/6、独占PG+Redis integration 37/37通过，自有DB已删、Redis8 0→0。Root gitlink/库存已集成、真IAM准入/OIDC/Capability/Scheduler/System组合通过；全量catalog drift另片，不宣称所有owner单库完成；状态：BFF owner及Root组合已验收 |
| W1C-DB-BFF-ROOT / P1 | Root跨仓smoke消费BFF新schema / `w1c_oidc_runner_rereview`脚本writer；Root修复/审查/Git | Root `762e7a6…`上五runner、窄URL helper及测试候选；BFF pin更新`a4dbc333…`，仅Root文件，其他owner URL不变 | Root独立聚焦**152 passed/56 subtests**、Ruff/diff-check；审查0 P0/P1/P2。发现并修复`psql`不能使用含`?schema`应用URL：观测保留raw URL、BFF环境用owner URL，直接SQL限定`kokoro_bff`。Root `20112fcb…`已发布，首次Scheduler smoke暴露case SQL未限定owner schema，已定点修复并加回归；当前IAM准入7/7、OIDC15/15、Capability8/8、Scheduler11/11、System组合PASS，自有资源清理通过。状态：Root脚本/五条真组合已发布复验，Scheduler新SQL发布后11/11 |
| W1C-DB-IAM / P1 | IAM owner-schema适配前置只读设计审查 / `w1b3_iam_fixture_reader`；Root裁决 | IAM main `b838853a81ff34bd0f7a079ccc75ba6abd61d1ec` clean；只读postgres-url/Prisma/fresh installer/runtime/fixture/CI与三设计文档 | 已交17 Prisma model/public、整库installer、readiness与raw SQL差距及四项真实验收方案；不改文件/Git/资源。状态：只读审查已验收，不等于IAM代码可同库运行 |
| W1C-DB-IAM-D / P1 | IAM单库目标三文档门 / `w1b3_iam_fixture_reader`唯一writer；Root审查/Git | IAM `b838853a…`→`d415ddbe565ec6c09e432945624e72c4b86d7a78` 已提交推送main且clean；仅三设计文档 | 固定`kokoro_iam` schema、Prisma canonical、事务化DDL/owner-only fresh gate、运行查询/ready与四项真实测试；API wire无变化明确。Root独立审查diff与一致性、diff-check通过；文档仅目标态不冒称代码完成。状态：设计文档门已验收 |
| W1C-DB-IAM-C / P1 | IAM单库owner-schema代码实现 / `w1b3_iam_fixture_reader`唯一writer；Root审查/Git | IAM `d415ddbe565ec6c09e432945624e72c4b86d7a78`→`6bc9b190c359b8109238626ff689ce9839e858b5`，38文件已推送main且clean；canonical 17 models/固定URL/installer/readiness/fixture/CI文档，API wire未变 | 独立复审原3 P2定点修正后0 P0/P1/P2；Root Node24 Prisma validate、`pnpm verify` **704/704**、串行真实integration **183/183**，测试DB/Redis1 0→0；Root同库双schema install已真测BFF16表+IAM17表/0FK。默认并行integration旧全局库存fixture竞态仍须单独修，不归因应用并发；Root gitlink/库存已集成、真IAM→BFF准入7/7及OIDC15/15通过；同库installer证据不等于所有owner应用同库运行。状态：IAM owner及当前组合已验收 |
| W1C-DB-IAM-BFF-PIN / P1 | BFF relay政策来源机械re-pin / `w1c_bff_logout_metadata_reader`唯一writer；Root审查/Git | BFF `06a4784…`→`a4dbc3339448c7ee8763b0f82d1c0ae4c213bf87` main clean；IAM `6bc9b19…`；Web `14e23e6…`已复制BFF policy原字节 | IAM allowlist/snapshot blob digest不变；BFF/Web policy同为SHA-256 `ba1e63083b4b2ed0f3eb42308e632bc502cb4f07fcb99a2ea04586f7faa123ad`。Root独立BFF Node22 contract25/标准253/真实schema6与Web contract52；Root gitlink/库存与跨仓真HTTP已集成复验。状态：owner来源pin及Root组合已验收 |
| W1C-3 / P0 | Root Web→BFF→IAM真实登录组合 / Root主控+独立审查 | W1C-1与W1C-2 release | 登录/刷新/退出/失效/越权真HTTP、隔离资源清理与固定SHA/digest；本片不激活尚缺Product generated consumer的EDGE-WEB-BFF；状态：待派工 |
| W1D / P0 | Web全量BFF Product OpenAPI generated consumer与单一AG-UI接线 / Web唯一writer；Root集成 | W1C-3；BFF public contract先冻结 | Web消除手写Product wire和旧网络协议，固定BFF contract/generator/runtime/digest；Web owner全门+组合验证后才激活EDGE-WEB-BFF；状态：待派工 |

W1C-1设计门通过报告（实施前，不等于代码验收）：当前BFF commit `6238599667110fbfbc2d5ef3a9d53731f2623cfe`，唯一writer修改 `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/docs/TECHNICAL_DESIGN.md`、`/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/docs/API_CONTRACT.md`、`/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/docs/DATA_MODEL.md`；独立设计审查初轮1 P1/2 P2均修正复核0 P1/P2。未决项为IAM既有`/iam/error`未开放（仅错误分支，不以BFF通配修补）、Web OAuth client注册URI与Auth.js版本/`resource`行为待W1C-2实测。本阶段`git diff --check`通过；机器`pnpm contract:check`、`pnpm schema:check`与真实IAM HTTP尚未运行，留W1C-1实现门。批准写入仅限BFF现有三文档，新增`src/http/routes/iam-protocol-relay.{policy,transport}.ts`与`src/http/routes/iam-protocol-relay.ts`、`contract/iam-relay-policy.json`、`scripts/generate-iam-relay-policy.mjs`、对应`test/iam-protocol-relay-{policy,transport}.test.ts`及独立真实HTTP integration fixture/test、`src/bootstrap/server.ts`、`src/config/runtime.ts`、`package.json`脚本、必要`docs/CURRENT.md`/`contract/README.md`。首轮全量test **241/242**，唯一失败为旧`test/contract-governance.test.mjs`精确断言`contract:check`脚本字符串；Root批准仅调整此测试的对应断言，将新`contract:check:iam-relay`纳入机器门，其他断言不放宽。`database/schema.sql`、IAM/Web、lockfile、BFF public OpenAPI禁止改；如确需越界先报Root。Root保留Git index/提交/推送/gitlink；BFF writer先RED→GREEN并交文件清单、命令与真实结果。

W1C-1代码首轮审查（未验收）：writer报告Node22标准242/242、contract25/25、architecture27/27、schema4/4及真实IAM基础HTTP1/1；Root只读代码/测试，独立审查定级1 P1/3 P2：真实IAM正向Code+PKCE/三页签名续接/logout未证明，超限上游未取消、入站slow body无截止、policy provenance仅硬编码自比。writer按RED→GREEN修两个超时/取消P2；本地复制IAM私有源码的vendor方案虽可做SHA门，但独立审查指出跨owner源码耦合。Root最终裁决**撤销该vendor扩围**：BFF只维护自身policy→JSON字节漂移，IAM固定来源/route子集由W1C-1G Root gitlink commit-blob机器门验证。P1需IAM test-owned fixture/Root真实组合，不让BFF复制IAM源码或把错误authorize/token当成功。未复验前W1C-1保持进行中。

W1C-1G放置门与替代裁决：Root拥有跨仓gitlink与证据，不拥有IAM OAuth字段或BFF policy。候选A在Root既有`verification/contracts`机器门旁新增窄`iam_relay_policy`治理helper/CLI/测试（采用，只用于跨repo固定blob核验，不变更16-edge公共API矩阵）；候选B由BFF vendor并动态import IAM私有`src`（淘汰，破坏只消费owner contract的边界）。IAM `auth-routes.constants.ts`与Better Auth snapshot只由Root `git --no-replace-objects show`固定IAM gitlink commit读取做来源证据，BFF单一TS policy派生只读JSON，Root固定BFF gitlink读取JSON并核对声明SHA及IAM route/method子集/disabled。新增Root `scripts/governance/iam_relay_policy.py`、`scripts/verify-iam-relay-policy.py`、`scripts/tests/test_iam_relay_policy.py`，不建新顶层目录，不修改业务schema/contract；失败应保持非零而不访问基础设施。Owner/依赖方向与允许文件集已确定；Root writer只写三脚本，Root主控负责task/progress/index/Git/集成。实际BFF/IAM gitlink发布前预期真实CLI红，不冒称闭环。

W1C-1H放置门：Root只拥有跨仓真实HTTP验收，IAM拥有OAuth用户/client/session/consent事实，BFF拥有relay策略与传输。当前IAM test-owned `web-oidc-flow-host.ts`提供独立临时资源和NDJSON凭据，Root已有`run_bff_iam_session_smoke.py`进程/清理模式；Web交互页源码尚未实现，因此本门仅验证IAM→BFF native协议，不冒充Web浏览器E2E。候选A在Root现有`scripts/e2e/`新增窄`run_bff_iam_oidc_smoke.py`及`scripts/tests/test_bff_iam_oidc_smoke.py`（采用：OAuth链和原admission七用例各有变化原因）；候选B把OAuth步骤塞入原session smoke（淘汰：同一文件混合两条独立协议状态机）；候选C在BFF复制IAM测试fixture（淘汰：跨owner事实与临时资源被consumer持有）。新增两个文件、不新建顶层目录；只通过IAM host管道及HTTP访问owner，不import子仓源码、不写IAM SQL，不新增生产schema/contract/generated或长期数据库。按精确gitlink验证进程，复用现有PG/Redis实例但只建/删fixture自有临时资源；先TDD验证协议/错误/清理，再实跑首次Code+S256/tenant/consent/token/userinfo/logout，明确已证明与Web待证明的边界。Root保留Git index/提交与最终组合验收。

W1C-1I放置门：IAM拥有测试fixture中的issuer和退出验收入口，Root/BFF不应替IAM伪造JWKS事实。当前`test/consumer/auth-flow.consumer.test.ts`已在测试范围对精确issuer `/jwks`映射本地fixture fetch，生产API/Schema未改；真实跨仓host目前只声明不可回环的公网HTTPS issuer，故带hint logout报`invalid_token`。候选A仅在现有`web-oidc-flow-host.ts`建立同一精确URL的测试私有fetch映射，配套现有host integration测试并在stop/EOF/启动失败恢复（采用，复用owner已有模式）；候选B在Root runner捕获401后跳过logout（淘汰，假PASS）；候选C更改生产issuer/JWKS行为或部署DNS（淘汰，扩大边界）。只有该host进程内部可命中，其他URL仍走原fetch；不新增数据库/契约/generated、不改生产代码；聚焦Node24测试必须覆盖映射和资源/全局状态清理，Root再用真实BFF relay链验证。IAM当前单仓临时DB/Redis由fixture自行清理，不触碰预存应用数据。

W1C-2A放置门与任务卡：owner `kokoro-app` Web同源adapter，唯一writer为Web源码Agent；基线Web main `38683a5…` clean，Root `a5ca0afc…`原锁BFF `1fae01e3…`/IAM `c9a27721…`，本片最终目标重pin BFF `cd1c260…`/IAM `b838853…`，无原有未提交Web变更。当前`src/lib/server/upstream-http.ts`会合并多个`Set-Cookie`，不能作为原生IAM中继；Web尚无`/iam` route，旧IAM直连/旧Product会话保持原样但不在本片扩写。候选A把BFF固定policy只读快照放现有`src/generated/`，校验与来源manifest归`src/lib/server/`、原生HTTP传输与路由分别归`src/lib/server/`和`src/app/iam/[...path]/`（采用：已有server/route/generated边界，变化原因独立）；候选B复用`upstream-http.ts`（淘汰：多cookie语义丢失）；候选C把policy放Web `contract/`当可编辑owner契约（淘汰：BFF才是来源owner）。允许Web只改`src/generated/iam-relay-policy.json`、相关只读provenance、`src/lib/server/iam-relay-*.ts`、`src/app/iam/[...path]/route.ts`、对应`tests/server|app|contract|system`聚焦测试及`docs/CURRENT.md`/`INDEX.md`；另批准对既有`docs/TECHNICAL_DESIGN.md`、`docs/API_CONTRACT.md`、`docs/DATA_MODEL.md`的来源SHA/digest与确实变化的当前状态作精确修正，并同步相邻`src/lib/server/INDEX.md`。独立审查后追加允许全部5份`.env*.example`的固定server-only Web origin配置、`docs/RUNBOOK.md`/`docs/SECURITY.md`/`docs/deployment.md`准确安全边界及新`tests/system/iam-relay-next-http.integration.test.ts`；不能从请求Host推导可信origin。该真实Next测试必须隔离构建输出和自有资源、启动失败可清理；若Next/Fetch入站raw target/body在路由前已规范化，测试与文档必须诚实记录可见边界、不得以伪造`request.url`充当真实HTTP证明，也不为此新建运维系统。新增文件仅因policy/protocol/route的不同变化原因，不新建顶层业务模块/数据库。唯一依赖是固定BFF policy字节，禁止Web直连IAM、子仓源码相对import或绕过BFF；GET只开放明确无mutation且无需浏览器Bearer的policy交集，userinfo/end-session与所有browser POST先拒绝，不能把后续CSRF/RP计划伪装成已实现。入站只透传符合IAM快照的issuer cookie，出站保持合法多Set-Cookie、status/Location、安全头，不透传Product/Auth.js cookie、浏览器Authorization/secret；服务身份由Web server提供，路径/编码/大小/超时/取消fail closed。无SQL、事务、generated client或Product API改动，旧IAM直连由后续Auth.js切片删除，不建立第二套兼容代理。验收Web Node22`pnpm lint/typecheck/test/build`、policy digest与BFF固定commit blob对照、unknown/POST/cookie/header/多Set-Cookie/超限/断连负例；Root审查后由Root串行提交，真实浏览器登录仍留W1C-2B/3。

W1B-3A放置门：owner为IAM test fixture、唯一writer为本片负责人；当前已有`test/fixtures/internal-http-application.ts`真实PKCE/Nest/独占资源，Root无IAM SQL写入权。候选A在IAM `test/fixtures/`扩展本地管道入口及`test/integration/`验证（采用：只变化测试联调生命周期），候选B在Root `scripts/e2e/`复制身份引导/数据库操作（淘汰：跨owner事实与双实现）。新增host与聚焦测试两个文件而非模块；只依赖既有fixture，不引入生产服务/跨仓源码import。测试删除Member仅作用于fixture自建IAM库并显式标注失效注入；无Schema/HTTP contract/generated变化、无旧路径需保留。验证为Node24脚本启动/命令/清理、IAM typecheck与聚焦integration、Root经真实HTTP观察BFF状态和拒绝后无业务副作用。

W1B-3B放置门：Root拥有跨仓行为验收，不持有IAM/BFF业务事实。当前三条旧smoke的认证fixture还依赖旧header；本片先独立做真实IAM组合，不让替身smoke冒充激活证据。候选A在Root既有`scripts/e2e/`增加窄组合runner与`scripts/tests/`行为测试（采用，代码地图已有Root组合职责），候选B塞入BFF或IAM单仓测试（淘汰，不能证明两个真实HTTP owner运行组合）。两个文件不建新模块；Root只通过IAM host管道和HTTP通信、只对自有BFF DB安装schema和读断言，不导入子仓源码或直接访问IAM数据库。无生产Schema/contract/generated变化、无双轨兼容；先验证实际联调，再按固定vendor/consumer版本决定checkpoint edge与既有smoke更新。

W1B-3C放置门：Root拥有组合smoke；现有Capability/Scheduler runner共用BFF `c5e9…` pin和自报header身份，BFF `623859…`已改为在线IAM准入，原8/11行为需要保持。候选A在Root `scripts/e2e/`放一个窄的受信IAM admission stub并由两个现有runner复用（采用：一处wire契约、分别保留其owner集成）；候选B在每条runner复制HTTP stub（淘汰：协议漂移与重复生命周期），候选C让两个owner smoke均启动真实IAM（淘汰：本片已由W1B-3B单独证明真实IAM，重复基础设施使旧owner回归成本过高）。新增共享fixture文件与聚焦测试，不建新顶层目录；只映射固定token到测试tenant/user，严格回`data.allowed/tenant_id/user_id/session_id/client_id`、`Cache-Control:no-store`和合法request-id，关闭线程；不读取IAM SQL、不变更业务contract/schema/generated、不保留旧header身份兼容。Capability/Scheduler原case与回调独立服务凭据不删。本机hostname只解析RFC1918而不解析loopback，旧callback固定loopback前置不符当前本机事实；采用在已有`scheduler_bff_smoke_http.py`仅让response-drop proxy绑定hostname解析且本机拥有的单一精确私有IPv4、/32 allowlist，原BFF upstream仍loopback，拒绝公网、多私有地址歧义与0.0.0.0，不改系统hosts或共享网络。验证为聚焦pytest、真实8/11及自有DB/Redis/进程清理。System旧smoke另列W1B-3D串行修复。

W1B-3D放置门：Root已有`scripts/e2e/run_system_owner_smoke.py`及聚焦测试，但其`ROOT/owner`路径和BFF旧header身份与当前九仓gitlink/BFF IAM准入相冲突。候选A只扩展现有System runner与现有测试，复用3C已提交共享wire stub（采用，System/BFF/Agent进程及资源生命周期已有位置）；候选B在System子仓复制Root组合测试（淘汰，跨仓进程/资源不属于System owner），候选C再建新runner（淘汰，双轨）。不新建目录/Schema/contract或第二IAM fixture。System owner admin/BFF/Agent服务凭据保持独立；仅BFF普通models请求使用测试IAM固定token身份，runtime manifest维持受信server tenant而非header自报；错误/空结果及发布release断言不删。验证聚焦pytest、真实独占PG/Redis HTTP组合、全部自有资源清理与Root集成门。

W1B-3E放置门：Root是跨仓依赖清单、checkpoint与当前组合文档owner；IAM拥有0.2.0机器contract，BFF拥有vendor/generated client与runtime，不在Root复制可编辑业务contract。当前IAM/BFF各自main及真实7case、Capability8/Scheduler11/System组合均已通过，inventory仍将唯一待激活的`EDGE-BFF-IAM`标broken。候选A增加`verification/contracts/checkpoints/w1b-iam.json`并在现有inventory更新该edge（采用，历史w0b-exit保持不变）；候选B直接改w0b-exit历史checkpoint（淘汰，会篡改已验收基线）；候选C新建跨仓contract目录（淘汰，违反owner唯一事实源）。新增一个checkpoint文件而不建目录/模块；只读取owner commit blob及consumer commit blob固定digest/version，禁止引用脏工作树或另仓相对import。无数据库/运行API变更，不保留旧broken reason；`docs/CURRENT.md`和`scripts/INDEX.md`同步真实当前态。验证compatibility期望只余11个broken+1非法、w1b-iam精确checkpoint、focused与全Root测试、真实smoke证据、topology/main-only及最终提交后清洁状态。
