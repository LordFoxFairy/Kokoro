# Kokoro 后端闭环任务总表

状态日期：2026-09-22。本文是本轮后端闭环的**唯一任务状态表**；历史任务由 Git 历史保存，不再与当前任务混排。主控 Agent 维护状态、依赖、负责人和验收证据，子 Agent 只更新自己获准任务卡中的交付信息。

## 1. 总目标与权威入口

- Goal：按已批准设计依次完成 Wave 0–7；Root 主控负责架构裁决、派工、双重审查、集成与最终验收，子 Agent 按 owner 逐仓实施；Billing 最后处理。
- 设计事实源：[`superpowers/specs/2026-09-20-kokoro-backend-closure-design.md`](superpowers/specs/2026-09-20-kokoro-backend-closure-design.md)
- 当前执行计划：[`superpowers/plans/2026-09-22-wave-1b-bff-admission-and-privacy.md`](superpowers/plans/2026-09-22-wave-1b-bff-admission-and-privacy.md)
- 已验收 Wave1A：[`superpowers/plans/2026-09-22-wave-1a-iam-session-admission.md`](superpowers/plans/2026-09-22-wave-1a-iam-session-admission.md)
- 已验收 Wave0B：[`superpowers/plans/2026-09-21-wave-0b-hard-link-closure.md`](superpowers/plans/2026-09-21-wave-0b-hard-link-closure.md)
- 已验收计划：[`superpowers/plans/2026-09-21-wave-0a-governance-and-contract-gates.md`](superpowers/plans/2026-09-21-wave-0a-governance-and-contract-gates.md)
- 证据账：[`progress.md`](progress.md)
- 本轮启动 Root 基线：`1bc74ae536d8a2da48f76045da95c2d5c2877750`
- 范围：`apps/kokoro-app` 与八个后端 owner；`apps/kokoro-mori` 和其他前端不参与业务改造。

### 1.1 主控优先看这里

- 当前关键路径：**W1B-1/R 准入收尾 → W1B-2 私有资源权限 → W1B-3 最小真实联调 → Web 登录/同源接线**。具体状态与唯一写入负责人见本文 Wave1B 执行卡。
- 后续按能力依赖推进 Storage → Platform → 聊天执行链 → System；支付最后。聊天的完成定义以本文第7节能力矩阵为准，包含消息落库、流式恢复、取消、HITL、附件/产物，而不是仅页面能展示文本。
- 每片交付必须是可运行代码、对应行为测试和必要契约/SQL更新；文档整理或生成客户端不单独等于功能完成。
- 当前不深入部署、生产角色隔离、镜像、SLO、网络硬化和重复全仓审计；这些进入统一发布收尾。身份/越权、事务、幂等、取消和故障恢复属于产品正确性，继续随代码验证。

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
| W1B-2 / P0 | BFF / `w1b_bff_owner`续任 / gpt-5.6-sol high / 唯一写入；Root审查与提交 | `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff`，main a898c90fe2b5447178a76fb04b0fedf9fa98e0d5，开始时clean；计划Task2精确范围，排除其它仓/生成物/lock；额外fixture写前列明 | Project/ScheduledTask/Run control/Project关联与分享负例通过；新随机PG库/现有Redis，Root唯一Git；状态：进行中 |
| W1B-3 / P0 | Root主控 + 独立审查 | 依赖BFF两片停写、完整门；Root单独组合任务卡 | 真实证据、smoke回归、gitlink/inventory、main-only；不以fixture激活IAM；状态：待派工 |
