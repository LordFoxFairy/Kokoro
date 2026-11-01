# Task A 问题台账、目标与闭环规则（2026-10-31）

## 1. 文档定位与对齐关系

本台账把此前 Task A 的设计、盘点、执行计划和当前实现证据合并成一份可执行的事实表。它不替代既有裁决：

- 总设计：[Task A 清理与重构技术方案](../specs/2026-10-30-task-a-cleanup-refactor-design.md)
- 只读盘点：[Task A 清理与重构清单](../specs/2026-10-30-task-a-cleanup-inventory.md)
- 原执行顺序：[Task A 清理与重构执行计划](../plans/2026-10-30-task-a-cleanup-refactor-execution.md)
- 当前收敛方案：[C-1.3～C-4 收敛实施方案](../plans/2026-10-31-task-a-c1-c3-convergence.md)
- C-3 provider/service 当前盘点：[C-3 provider census](2026-10-31-task-a-c3-provider-census.md)
- 已交付证据：[C-1 清理实施证据](2026-10-31-task-a-c1-cleanup-implementation.md)
- C-2/C-3 路由与边界盘点：[C-2/C-3 inventory](2026-10-31-task-a-c2-c3-inventory.md)
- C-1.3 profile-read cutover：[profile-read evidence](2026-10-31-task-a-c1-3-profile-read-cutover.md)
- Chat archive/share route cutover：[Chat cutover evidence](2026-10-31-task-a-chat-route-cutover.md)
- Projects pin route cutover：[Projects pin evidence](2026-10-31-task-a-project-pin-cutover.md)
- Projects deletion-status route cutover：[Project deletion-status evidence](2026-10-31-task-a-project-deletion-status-cutover.md)
- Projects rename route cutover：[Project rename evidence](2026-10-31-task-a-project-rename-cutover.md)
- Projects delete route cutover：[Project delete evidence](2026-10-31-task-a-project-delete-cutover.md)
- Projects resource-list route cutover：[Project resource-list evidence](2026-10-31-task-a-project-resource-list-cutover.md)
- Projects resource-delete route cutover：[Project resource-delete evidence](2026-10-31-task-a-project-resource-delete-cutover.md)
- Projects resource-read/download route cutover：[Project resource-read evidence](2026-10-31-task-a-project-resource-read-cutover.md)
- Projects resource-upload route cutover：[Project resource-upload evidence](2026-10-31-task-a-project-resource-upload-cutover.md)
- ScheduledTask current-read route cutover：[Scheduled read evidence](2026-10-31-task-a-scheduled-read-cutover.md)
- AgentRuns internal route cutover：[AgentRuns evidence](2026-10-31-task-a-agent-runs-cutover.md)
- C-4 contract inverse 与全量复验：[C-4 evidence](2026-10-31-task-a-c4-contract-inverse.md)
- IAM native profile receipt：[native receipt evidence](2026-10-31-task-a-c1-3-native-receipt.md)
- 产品任务边界：[Task A workspace handoff](../../handoffs/2026-10-30-task-a-workspace-execution.md)

当前停写代码基线为 `f17bf828`；其后 Root `18b59a43`、`17d49259` 为文档同步，Root `f4202a5e` 固定 IAM profile-read owner，`c7af342b` 固定 BFF/App profile-read consumers。App 子仓 `dde9fa6`、BFF 子仓 `3ca1525`（含 `b3a9ab5`、`4e794ce`、`2ce0296`、`2df4bcc`、`caccdc9`、`a677cd2`、`6874034`、`ef1c53b`、`6de89c7`、`108a0bc`、`4667506`、`96806f4`、`39d5481`、`7f61218`、`2a504c0`）、IAM 子仓 `d461b82`（基于 `f4f1585`）已完成 profile-read 与 root-scoped issuer cookie cutover；BFF account native bundle（profile/sessions/team/me/personalization）、System runtime-manifest、Chat archive/share/feedback、Projects pin、ScheduledTask current-read、Agent internal admission/binding 与 run-display bundle 已由 feature middleware/adapter 接管，旧 `server.ts` 对应业务分支已移除；personalization、Chat、Project pin、ScheduledTask read 与 AgentRuns reader/provider 已从 global route dispatch 解耦，raw-server seam 使用显式 provider，partial test composition 仍保持兼容。native route HTTP fixtures 已切换到 build output，78 项 feedback/run-display/project-binding focused tests 全部通过；C-4 contract inverse 与 IAM 0.18/profile-read governance 已收敛，BFF 串行全量为 2309 tests / 2307 pass / 0 fail / 2 skip。IAM native profile read/update 与撤权集成 fixture 已在本地 PostgreSQL/Redis 上串行 12/12 通过；Root real IAM→BFF session smoke 7/7 已在 cookie cutover 后复验通过，OIDC smoke 42/42 仅为 cutover 前历史证据，需按新 cookie policy 重跑；真实跨 App→BFF→IAM native sign-in/sign-out/tenant-switch/revocation 旅程仍未形成。本台账只整理问题、目标、约束、TODO 和验收，不把 A-01/A-02/A-07 提前写入实现。

本次继续推进后的精确停写 pins：BFF `06ae1a6`（前序 `a09176a`、`b7b30e5`、`a725bdc`、`509f3f0`、`34899e0`、`86c714b`、`7cf1312`、`e1f2b81`）、IAM `e1f537b02cb326cfb3751316b1591fa82313f70a`、App `9cde5640`；BFF 已将 Health、IAM relay、`GET /v1/me`、项目集合/详情/revisions/deletion-status/rename/delete/resource-list/resource-delete、public share projection、`GET /v1/connector.list`、MCP provider/package admin、browser project publication、browser Custom API CRUD、App skill-bindings、Skill specification reads、全部 Skill package inspection、exact Skill download POST/GET opaque-handle、`/v1/mori/**` Music owner adapter、Message regeneration/ChatTurn service、direct Chat read middleware、direct no-`project_ref` Chat title/delete/share mutations 与 direct AG-UI events、project-scoped Chat owner access 与 Chat POST、Agent run-control、Agent internal admission/binding 与 Run display、Library/artifact/personal-file 与 Personal MCP 路由移入 feature middleware/provider，并从旧 dispatcher 删除三类 Skill download/Mori 分支、owner model/Billing/Platform projection 与重复 Library 分支；同时删除 `BffBusinessStore` 上的 `projectService`、`chatService`、`chatTurnService` 全局字段；`SKILL_EXACT_DOWNLOAD_SOURCE`/`PROJECT_EXACT_DOWNLOAD_SOURCE`/`MUSIC_IDEMPOTENCY`/`CHAT_TURN_SERVICE`/`AGENT_DISPATCH_OUTBOX` feature seams；本次新增 `PUBLIC_SHARE_SERVICE`、`SCHEDULED_TASK_READ_SERVICE`、`SCHEDULED_TASK_SERVICE`、`CHAT_SERVICE`、`CHAT_TURN_SERVICE`、`PROJECT_SERVICE`、`PROJECT_SKILL_SELECTION_PROVIDER`、`PROJECT_MCP_RECOMMENDATIONS_PROVIDER`、`SKILL_EXACT_DOWNLOAD_SOURCE`、`SKILL_SPECIFICATION_SOURCE`、`CUSTOM_API_CLIENT` 显式 provider handoff，store/service fallback 仅保留给未迁移 raw/test composition；`7cf1312` 进一步将未知 System/Skills path 的 retired 503 fallback 固定在对应 feature middleware，不再流入 LegacyRoutes；`86c714b` 让 transitional raw/test composition 复用 named `SkillShareRepository` seam，R357 Skill specification contract/focused 现为 110/110；`34899e0` 让 raw exact-download composition 复用同一 seam，Project exact-download/package inspection focused 现为 18/18；`a725bdc` 关闭 System admin/public Share raw seam；`b7b30e5` 关闭 browser Custom API raw seam；`a09176a` 关闭 ScheduledTask mutation 对全局 `services` aggregate 的生产读取；`06ae1a6` 关闭 Scheduler callback 对全局 `services` aggregate 的生产读取，Scheduler/mocks/architecture focused 84/84，BFF `pnpm test` 现为 2317 tests / 2315 pass / 0 fail / 2 skip。Root topology PASS，Root `python3 -m pytest scripts/tests` 现为 1846 passed / 3 skipped，最新 Music focused 12/12、Message regeneration 4/4、Chat+Scheduler focused 156/156、Project pin/skill focused 12/12、MCP recommendation/publication focused 60/60、exact-download HTTP/policy/unit 22/22、connector-list HTTP 5/5、MCP provider/package admin HTTP 12/12、App skill-bindings/Open App management 12/12、package inspection unit 47/47（4 个环境 skip），BFF mock contract 25/25，Nest architecture 24/24，BFF architecture 34/34。

## 2. 已设置 Goal

**Goal（active）**：完成 Task A 的 C-1.3～C-4 闭环：先整理并冻结全部问题、目标、约束与 TODO；完成有证据的 IAM native-session/App/BFF 链路；按 feature 迁移并删除 LegacyRoutes、旧 dispatcher、global composition 与无边界 Repository/Service/Port；串行完成 Root/子仓全量验证。A-01/A-02/A-07 在 C-1～C-4 完成前保持停写，禁止无意义代码和越界改动。

Goal 的完成条件不是“目录改名”或“测试数量增加”，而是下表中的 G1～G4 均有实现证据、行为证据和串行门禁；随后才开启 G5（A-01/A-02/A-07）。

## 3. 问题总表

### 3.1 C-1.3 native-session 链路

| ID | 当前问题 | 影响 | 闭环证据 | 状态 |
|---|---|---|---|---|
| TA-C1.3-01 | App 已为 `/api/session/*`、App SSR shell、`/api/auth/session` probe 增加同源 native-session adapter，但登录、登出、租户切换、撤权还未与 IAM admission 成对验收。 | first-party auth 旧入口仍需保留回滚边界。 | App adapter contract/HTTP/E2E；sign-in、sign-out、tenant-switch、revocation、多标签 late-response 全部通过。 | 进行中 |
| TA-C1.3-02 | App 仍存在 Auth.js/OIDC RP、Product Session access/refresh 与 `/iam/oauth2/*` 旧链路。 | 形成第二套身份事实和双读风险。 | native consumer 先通过，再删除旧 RP、token/refresh store、relay 和只保护它们的测试；反向 import 为零。 | 未完成 |
| TA-C1.3-03 | BFF native consumer 已存在；account profile/sessions/team 已切换到 native Cookie + direct credential owner transport，旧 bearer 仅被独立未迁移 owner authorization surface 使用。 | 若误删旧入口会造成无身份请求；若保留无条件双读会造成协议分叉。 | 每个 owner surface 有 native/direct-credential 等价边界；native 启用时无浏览器 bearer 双读；旧 bearer consumer 清单归零。 | 进行中 |
| TA-C1.3-04 | IAM native contract/runtime 已交付，App `/api/session/*`、SSR shell、probe、account profile/sessions/team adapters 已通过 BFF 接入 native identity proof。 | 只有 controller/unit 和 probe 通过还不足以证明完整用户旅程闭合。 | `run_web_native_session_smoke.py` 在 test-owned HTTPS origin 验证真实 cookie、Origin、tenant/subject、`/api/auth/session`、`/api/session/projects`、signout 后 401；tenant switch/permission/revocation UI 仍待补。 | 进行中 |
| TA-C1.3-05 | App profile read 已切换到 BFF GET；IAM/BFF canonical GET owner contract、generated artifacts 和 App/BFF focused tests 已落地。 | 旧 RP/userinfo relay 仍需等待 profile read 的真实 native owner receipt 与其它 native 旅程收据后再删除。 | IAM `d461b82`、BFF `3ca1525`、App `dde9fa6`；subject/no-store/final re-admission 与 Web native session receipt 已有测试；profile read 浏览器 owner receipt 待补。 | 进行中 |
| TA-C1.3-06 | IAM issuer cookie 原先默认 `Path=/iam`，已按 G0 contract 切为统一同源 `Path=/`；App/BFF policy 与 logout cookie 校验同步更新。 | 旧 RP/Product Session 删除前仍需完整 native sign-in/tenant-switch/revocation 旅程，不可只依赖手工 Cookie fixture。 | IAM `e1f537b`、BFF `3ca1525`、App `dde9fa6`；IAM/BFF integration、cookie path assertion 与 policy tests 通过；`run_web_native_session_smoke.py` 4/4 验证 HTTPS `/api/auth/session`、`/api/session/projects`、signout 401 与资源清理。 | 完成 |

### 3.2 C-2 BFF Nest 与 LegacyRoutes

| ID | 当前问题 | 影响 | 闭环证据 | 状态 |
|---|---|---|---|---|
| TA-C2-01 | `src/modules/legacy-routes/legacy-routes.runtime.ts` 仍创建 `createBffComposition()` 并委派 `handleBffRequest`；剩余业务 path 仍在 `src/bootstrap/server.ts`。 | 业务事实仍由旧 dispatcher 持有，Nest feature graph 不是唯一运行边界。 | C-2/C-3 inventory 已冻结入口/route family；Health、Account native bundle、IAM relay、public share、System runtime-manifest、Chat archive/share/feedback、Projects pin/collection/detail/revisions/deletion-status/rename/delete/resource-list/resource-read/resource-download/resource-delete/skill-selection/MCP recommendations/project/personal skill-installations/managed personal Skill reads、ScheduledTask current-read、Agent internal admission/binding 与 run-display 已切到 feature middleware/adapter，后续每条 path 迁移必须同时改 `server.ts`、feature graph 和 negative test。 | 进行中，LegacyRoutes 仍保留 |
| TA-C2-02 | 旧 `bootstrap/server.ts`、`bootstrap/runtime.ts` 与 global composition 路径仍有生产引用；`app.module.ts`、`main.ts`、shutdown provider 也在删除链上。 | 存在第二 composition root 和隐藏依赖。 | BFF `a2f1579` 已删除旧 dispatcher 的 `/v1/me` 分支，`2c683c4` 将 IAM native relay 移入 `IamRelayModule` middleware，`cb02934` 将 `GET /v1/projects` 集合读取、`e8d9a27` 将项目详情读取、`b9294ab` 将 instruction-revisions 读取、`fd74e02`/`8448a7e` 将 public share projection 与 test-only reader fallback、`fb27e75` 将 Health 处理收敛到 feature/compat adapter、`7afbaff` 将 project deletion-status 处理收敛到 `ProjectsModule`/native adapter、`1db4e51` 将 project rename 处理收敛到 `ProjectsModule`/native adapter、`1817bd9` 将 project delete 处理收敛到 `ProjectsModule`/native adapter、`52eeff7` 将 project resource-list 处理收敛到 `ProjectsModule`/native adapter、`14aa232` 将 project resource-delete 处理收敛到 `ProjectsModule`/native adapter、`525a150` 将 project resource-read/download 处理收敛到 `ProjectsModule`/native adapter、`2dd93ca` 将 project skill-selection 处理收敛到 `ProjectsModule`/native adapter、`9310aa6` 将 project MCP recommendations 处理收敛到 `McpModule`/native adapter、`d9a8a24` 将 project skill-installations 处理收敛到 `ProjectsModule`/native adapter、`1153be7` 将 personal skill-installations 处理收敛到 `SkillsModule`/native adapter、`7aa092b` 将 managed personal Skill reads 处理收敛到 `SkillsModule`/native adapter；canonical `HealthModule`/`AccountModule`/`IamRelayModule`/`ProjectsModule`/`ChatModule`/`McpModule`/`SkillsModule` 成为对应 handler。反向搜索 `LegacyRoutes*`、`createBffComposition`、`handleBffRequest`、`createBffServer` 仍需在剩余 route census 清零后完成。 | 进行中 |
| TA-C2-03 | 已有 feature module 仍有部分只声明 graph/ownership 的空壳风险。 | 机械建模块会增加无意义代码，掩盖未迁移行为。 | 每个 module 至少承接真实 route/provider/owner client；无 route、无 provider、无测试证据的模块不保留。 | 进行中 |

### 3.3 C-3 Repository / Service / Port

| ID | 当前问题 | 影响 | 闭环证据 | 状态 |
|---|---|---|---|---|
| TA-C3-01 | `BffBusinessStore` 同时承载 Chat、Project、Agent、Scheduler、AG-UI、Artifact 等事实。 | 巨型 Port 隐藏 owner 和依赖，导致运行时缺失分支。 | C-2/C-3 inventory 已完成字段/owner 候选；按 slice 拆 provider，旧 global Port 生产 import 为零。 | 盘点完成，迁移未完成 |
| TA-C3-02 | `PostgresBffRepositories` 是服务定位器，`BffApplicationServices` 是全局聚合器。 | 组合根无法表达真实依赖，Repository/Service 无法按 owner 审计。 | BFF `4e76866`/`2cc1c1b` 删除 Chat/Project 重复字段，`a3fd669` 删除 ChatTurn 字段，`33a1bf0` 删除 ScheduledTask 字段；runtime 统一从 feature provider 或 `services.*` 兼容读取；复杂事务/CAS/lease/outbox/owner boundary 继续迁入具名 feature-local provider。 | 进行中 |
| TA-C3-03 | `src/application/ports/**` 尚有全局 Port；其中既有薄转发、单实现，也有需要保留的事务边界。 | 机械删除会丢失并发、幂等、outbox 或权限保障；全部保留又延续过度分层。 | 对每个 Port 给出 keep/move/merge/delete 证据；删除条件为新 provider 编译通过、旧 import 为零、行为测试已迁移。 | 未完成 |
| TA-C3-04 | 部分 Service/Repository 只做一层 `return repository.method(...)` 转发。 | 无独立变化原因，增加抽象和测试负担。 | 并入 feature Service/Provider；公开行为测试保留，私有调用顺序测试删除。 | 未完成 |
| TA-C3-05 | 类型、错误映射、wire/domain DTO 可能存在镜像。 | 同一事实在多个 owner 漂移。 | 保留 canonical contract 与必要边界类型；重复 DTO/错误映射反向搜索为零。 | 未完成 |

### 3.4 C-4 测试、脚本与验证

| ID | 当前问题 | 影响 | 闭环证据 | 状态 |
|---|---|---|---|---|
| TA-C4-01 | 旧 `legacy`/`fallback`/`schema-evolution`/旧 dispatcher 测试及 fixture 尚未全部按 canonical 行为清理。 | 默认门禁继续保护已删除语义，阻碍删除生产代码。 | 删除生产消费者、测试、fixture、helper 和脚本的成组变更；保留权限、幂等、CAS、lease、outbox、replay、取消、恢复测试。 | 未完成 |
| TA-C4-02 | BFF/IAM 已有完整门禁，但 App/Agent 仍有各自 baseline/环境缺口；全 Root 证据尚未形成一份最终收据。 | 局部绿不能宣称 C-1～C-4 通过。 | 停写后串行执行 Root、IAM、BFF、App、Agent owner gates，并分列 pass/fail/skip/baseline。 | 进行中 |
| TA-C4-03 | 并行 build/test 曾出现 dist 竞争，部分 PostgreSQL 测试受资源门禁跳过。 | 结果不可直接作为全量通过。 | worker 停写后按 build→focused→full 顺序串行重跑；skip 只记录为环境缺口，不计为通过。 | 进行中 |

### 3.5 A 任务与范围边界

| ID | 当前问题 | 处理规则 | 状态 |
|---|---|---|---|
| TA-A-GATE-01 | A-01 会话创建恢复、A-02 Agent 展示、A-07 Project Todo 仍有产品缺口。 | C-1.3、C-2、C-3、C-4 全部关闭前停写；不以局部实现或页面假数据提前关闭。 | 停写 |
| TA-A-BACKLOG-02 | A-03～A-16 仍属于 Task A 后续产品 backlog（输入控制、执行恢复、压缩、项目上下文、附件、资料库、产物、自动化、外部聊天、语音、体验与交付）。 | 继续沿 `docs/handoffs/2026-10-30-task-a-workspace-execution.md` 管理，不混入 C-1～C-4 清理代码。 | 待领取 |
| TA-SCOPE-01 | `docs/CURRENT.md` 中还有 Task B、账户/Skills/MCP、视觉、后台、外部协议和历史治理问题。 | 只记录为外部 backlog；除非直接阻塞 C-1.3/C-2/C-3/C-4，否则不在本 Goal 写代码。 | 排除 |

### 3.6 既有基线与环境缺口（不伪装为本次修复）

| ID | 事实 | 处理 |
|---|---|---|
| TA-BASELINE-01 | App 全仓 typecheck 仍有 `app-frame-main-surface.tsx:onReconnect` 既有类型错误。 | 单独记录 baseline；C-1 清理不扩大范围。若影响 native adapter 触达路径，再由对应切片提出最小修复。 |
| TA-ENV-01 | BFF 2 个真实 PostgreSQL 条件测试因资源门禁 skip。 | 不计为通过；配置隔离资源后补跑，或在最终收据中明确环境缺口。 |
| TA-BASELINE-02 | Root 全局规范审计现有 224 条历史/任务外 violation。 | 只修本 Goal 直接命中的 BFF Nest、C-1.3 和 Task A clean-slate 项；其余留在治理 backlog。 |
| TA-BASELINE-03 | App 停写后全量 `pnpm test` 为 6890 pass / 2 skip / 7 fail；失败集中在既有 process/activity UI 断言、sign-out 页面文案契约，另有 stored-session fixture 缺少 `KOKORO_TEST_REDIS_URL`。 | 作为独立 baseline/环境缺口记录；不以 focused native proof 冒称 App 全量通过，也不在 C-1.3 中顺手扩展 UI 语义。 |
| TA-BASELINE-04 | Root `python3 -m pytest scripts/tests -q` 串行结果为 1844 passed、2 failed、3 skipped、502 subtests；失败为 `test_serve_local_login.py::test_occupied_port_is_not_reused_or_terminated` 与 Storage smoke 缺少 `@aws-sdk/client-s3`，均未命中本切片代码。Root topology verifier 通过，BFF focused gates 通过。 |
| TA-BASELINE-05 | BFF `2dd93ca` 后，skill-selection/architecture/contract focused 组合为 144/144；完整 `pnpm test` 在既有 Artifact/Project MCP 环境失败与长运行 contract 边界处未形成新绿证据。 | C-4 BFF 全量仍不计为通过；focused 证据仅覆盖本切片，2 个 PostgreSQL 条件 skip、其他 owner baseline 与全局 LegacyRoutes/Repository/Service/Port 仍未完成。 |

## 4. 目标与 TODO

### G1：完成 C-1.3 native-session 闭环

- [ ] 盘点 App 当前 Auth.js/OIDC/Product Session/relay 的生产 import 和请求边界。
- [ ] 实现 App same-origin native adapter：allowlisted Cookie、Origin、request-id、取消预算；禁止 body/Authorization 自报 tenant/subject。
- [x] `/api/session/*`、`/app` SSR admission、`/api/auth/session` probe、archived/shared task、session archive/share 和 sign-in failure recovery 已复用同一 native identity proof；native probe 不再发 Product refresh。
- [x] 为 account profile/profile update、account sessions、team 固定 IAM native owner contract：BFF direct `session_admission` credential + allowlisted Cookie + fixed Origin；IAM fresh session/tenant/membership proof；account self operations 保留 CAS/事务/Audit，Team owner snapshot 保留 role permission；未迁移 consumer 继续 fail-closed。
- [x] 补齐 App profile read 的 owner contract；App 已从 `/iam/oauth2/userinfo` relay 切到 BFF GET，旧 RP/Product Session 仍保留回滚边界。
- [x] 设计并冻结 `GET /internal/v1/account/profile` owner contract：IAM 返回 `subject/name/email/email_verified` 的 canonical projection；native proof 与 legacy bearer 共用同一 owner schema，BFF 仅做 admission/transport/error projection，App 不再解析 OAuth userinfo。
- [x] 生成并 pin IAM OpenAPI/SDK 与 BFF client；IAM contract/unit、BFF client/HTTP、App profile-read focused tests 已通过；真实 cookie→BFF→IAM receipt 待 `IAM_TEST_ADMIN_URL` 可用后补跑并关闭 TA-C1.3-05。
- [ ] 对齐 sign-in、sign-out、active-tenant switch、revocation、multi-tab late response 的 contract/HTTP/E2E。
- [x] 补真实 HTTPS `/api/auth/session`、`/api/session/*` cookie→BFF→IAM receipt；4/4 cases 通过，收据脚本和资源清理已固定。
- [x] App `GET /api/auth/session` native read、`POST /api/auth/signout` issuer handoff 与 browser `endProductSession` client 已与旧 RP config 解耦：native issuer cookie 通过 allowlisted adapter → BFF `/v1/me` → `mode:native` projection，client 直接走 native signout，legacy 才读取 CSRF；focused 37/37 通过。
- [x] 当前 checkout focused revalidation：IAM native admission unit 3/3；App native-session/BFF adapter、native auth route、sign-in flow、tenant-route 22/22；App account profile/session/Team 与 sign-in/sign-out failure/recovery 145/145。
- [ ] 固定 IAM artifact/version/digest，BFF/App 消费同一 artifact；补完整链路收据。
- [ ] 只有 consumer proof 成立后，删除旧 RP、Product Session、refresh reservation、旧 relay 和专属测试。
- [ ] 逐项关闭仍依赖 bearer 的 owner authorization surface；未完成者保持 fail-closed。

### G2：LegacyRoutes 全量退出

- [x] 建立 path/method → handler → target module → owner → test → status 的 route census；盘点覆盖 `server.ts`、`app.module.ts`、`main.ts`、shutdown provider 和 LegacyRoutes wrapper。
- [x] 每批先补 red HTTP/architecture test，再实现 feature-local adapter/provider；personalization 复用既有 CAS provider，不新增 Service/Repository。
- [x] Account native bundle（profile/sessions/team/me/personalization）与 System runtime-manifest 已从 `handleBffRequest` 分派移出；feature middleware 负责各自的 admission/owner transport、输入边界、预算和 error envelope，旧 dispatcher 只保留 raw `createBffServer` 的显式兼容入口。
- [x] Chat archive/share bundle（`GET /v1/account/archived-tasks`、`GET /v1/account/shared-tasks`、`GET/POST /v1/sessions/:id/{archive,restore}`）已由 `ChatModule` 的 `ChatMiddleware`/`chat-native` adapter 接管；旧 dispatcher 分支已移除，复用同一 `ChatApplicationService` provider，不复制持久化边界。
- [x] Projects pin bundle（`GET /v1/self/project-pins`、`PUT /v1/projects/:id/pin`）已由 `ProjectsModule` 的 `ProjectPinMiddleware`/`project-native` adapter 接管；旧 dispatcher 分支已移除，复用现有 `ProjectService`/ProjectRepository owner，不新增 receipt 或第二 SQL 边界。
- [x] ScheduledTask current-read bundle（`GET /v1/scheduled-tasks[/:id]`）已由 `ScheduledTasksModule` 的 `ScheduledTaskReadMiddleware`/`scheduled-task-native` adapter 接管；旧 dispatcher 分支已移除，复用现有 `ScheduledTaskReadService`/Scheduler owner read、5 秒预算和 re-admission。
- [x] Agent internal bundle（`POST /internal/v1/model-admissions[/:id/settle|recover]`、`POST /internal/v1/project-execution-bindings/verify`）已由 `AgentRunsModule` 的 `AgentRunsMiddleware`/`agent-runs-native` adapter 接管；旧 dispatcher 分支已移除，复用现有 durable reader、dedicated credential 与 Billing/IAM owner boundary。
- [x] Agent run-display bundle（`GET /v1/sessions/:id/runs/:run/display`）已由 `AgentRunsModule` 的 `RUN_DISPLAY_PROVIDER`/`AgentRunsMiddleware` 接管；旧 dispatcher 分支已移除，复用 submitted-run reader、Chat owner read、AG-UI/Agent transport 与 final admission。
- [x] Chat message-feedback bundle（`GET/PUT /v1/sessions/:id/messages/:message/feedback`）已由 `ChatModule` 的 `CHAT_SERVICE`/`ChatMiddleware` 接管；旧 dispatcher 分支已移除，复用既有 feedback CAS/owner read，不复制 Repository 或 receipt。
- [x] 已迁移 Chat path 的 LegacyRoutes bypass（public share、archive/shared tasks、direct reads、feedback、regeneration、move）已由 `LegacyRoutesMiddleware` 锁定；Chat POST/events/title/delete/share 与 project-scoped reads 继续保留旧入口并由负向测试保护。
- [x] Chat direct no-`project_ref` title/delete/share mutations 已由 `ChatModule` 的 `CHAT_IDEMPOTENCY` + `handleChatMutationRequest` 接管；project-scoped variants 与 Chat POST/events 仍保留旧入口。
- [x] Chat direct no-`project_ref` events 已由 `ChatModule` + `AguiModule` 接管；project-scoped events、Chat POST 与 LegacyRoutes projector worker 仍保留 transitional ownership。
- [x] Chat project-scoped title/delete/share/events 已复用 `ProjectAccessModule` 的唯一 `PROJECT_SERVICE` owner；Chat POST 与 LegacyRoutes projector worker 仍保留 transitional ownership。
- [x] Chat POST messages 已由 `ChatModule` 接管；复用 `SkillInstallationAccessModule`、`ProjectAccessModule`、`ChatTurnApplicationService`、Agent outbox 与 idempotency，LegacyRoutes 不再接收该 POST。
- [x] Agent run control 已由 `AgentRunsModule` 接管；复用 shared Chat/Project owners、AGENT_CONTROL_IDEMPOTENCY 与 `liveAgentSession`，LegacyRoutes 不再接收 run-control POST。
- [x] AgentRuns internal admission/binding 与 Run display 的 LegacyRoutes bypass 已接入；`AgentRunsMiddleware` 继续唯一处理 credential/method/owner-read/error contract，LegacyRoutes 不再接收这些已迁移 path（`ba8ab60`）。
- [x] Agent dispatch/cancellation outbox worker 的 repository、delivery 与 start/stop lifecycle 已由 `AgentDispatchModule` 拥有；LegacyRoutes 仅保留显式 raw composition shutdown seam，production 不再重复创建或启动 worker（`ba8ab60`）。
- [x] AG-UI projector 的 repository/source reader 构造与 start/stop lifecycle 已由 `AguiModule` 拥有；LegacyRoutes 不再启动 projector，显式 null 防止生产重复实例，raw/test composition 仍保留兼容 fallback（`ba8ab60`）。
- [x] ScheduledTask outbox 的 repository、Scheduler delivery 与 start/stop lifecycle 已由 `ScheduledTasksModule` 拥有；LegacyRoutes 不再启动同一 worker，raw/test composition 通过显式 seam 保持兼容（`ba8ab60`）。
- [x] Project-scope release outbox 的 repository、Storage client 与 start/stop lifecycle 已由 `ProjectsModule` 拥有；storage 未配置时显式不创建 worker，LegacyRoutes 不再启动同一实例（`ba8ab60`）。
- [x] Scheduled Agent dispatch/terminal 的 repository、Agent delivery/source 与 start/stop lifecycle 已由 `ScheduledTasksModule` 拥有；Agent/upstream 未配置时显式不创建 worker，LegacyRoutes 不再启动同一实例（`ba8ab60`）。
- [x] Project-scoped Chat collection/session/message/parts/process reads 已由 `ChatModule` 接管；复用 `ProjectAccessModule` 的唯一 `PROJECT_SERVICE` owner，LegacyRoutes 不再接收该 `project_ref` read family（`ba8ab60`）。
- [x] Scheduler callback（`POST /internal/bff/scheduled-tasks/dispatch`）已由 `ScheduledTasksModule` 接管；复用唯一 ScheduledTaskService、receipt repository 与 scheduled-Agent repository，LegacyRoutes 不再接收 callback path（`ba8ab60`）。
- [x] ScheduledTask create/update/delete/retry 与 project-scoped create mutation 已由 `ScheduledTaskMutationMiddleware`/`scheduled-task-mutation-native` 接管；Nest 与 raw `createBffServer` 共用同一 repository/service/idempotency owner，旧 `live-bff.ts` 已删除，LegacyRoutes 不再接收这些 mutation path（`e1f2b81`）。
- [x] Project create/instruction command 已由 `ProjectsModule` 的 `ProjectMutationMiddleware` 接管；新增 `PROJECT_IDEMPOTENCY` 只作为该 feature 的 receipt provider，`ProjectService`/`ProjectRepository` 仍是唯一 owner，Nest 与 raw `createBffServer` 共用同一 `project-mutation-native` adapter（`e1f2b81`）。
- [x] Project tasks read（`GET /v1/projects/:id/tasks`）并入 `ProjectPinMiddleware` 的 core-read adapter；`liveBffBusiness` 的重复 tasks 分支已删除，复用既有 `ProjectService.tasks` owner（`e1f2b81`）。
- [x] Personal Billing owner routes（summary/ledger/credit-account/plans/checkout）已由 `BillingModule` 的 `BillingPersonalMiddleware`/`billing-personal-native` 接管；`BILLING_IDEMPOTENCY` 为唯一 feature receipt provider，`owner.ts` Billing 分支已删除，原有 owner transport/error/query/cancellation 语义保持不变（`e1f2b81`）。
- [x] System model catalog（`GET /v1/models`）已由 `SystemModule` 的 `SystemModelCatalogMiddleware`/`system-model-catalog-native` 接管；Nest 与 raw `createBffServer` 共用 owner projection/validation/error adapter，`owner.ts` model branch 已删除（`e1f2b81`）。
- [x] MCP platform projections（`GET /v1/mcp/servers`、`GET /v1/mcp/connections`）已由 `McpModule` 的 `PlatformProjectionMiddleware` 接管；`owner.ts` Platform projection branch 已删除，retired System/Skills fallback 已隔离为单独 adapter（`e1f2b81`）。
- [x] 共享 owner transport helper 已从 `owner.ts` 收敛为 `owner-request.ts`；System model catalog/Music 只依赖明确 transport helper，`liveOwnerBusiness` dispatcher 已删除（`e1f2b81`）。
- [x] Browser-private Personal MCP 全部路由已由 `McpModule` 的 `McpPersonalMiddleware` 接管；`mcpPersonalRoute`/MCP icon route 改为窄 provider，不再依赖 LegacyRoutes 的完整 composition（`e1f2b81`）。
- [x] Library/artifact/personal-file route family 已由 `AccountModule` 的 `LibraryMiddleware`/`library-native` 接管；artifact repository 与 upload receipt provider feature-owned，raw server 不再保留重复 library branches（`e1f2b81`）。
- [x] Project deletion-status read（`GET /v1/projects/:id/deletion`）已由 `ProjectsModule` 的 `PROJECT_SERVICE`/`ProjectPinMiddleware` 与 `project-native` adapter 接管；旧 `projectDeletionStatusRoute`、server path 判定及 source file 已删除，保留 deletion error contract、no-store、request-id 与既有 repository read 边界。
- [x] Project rename command（`PATCH /v1/projects/:id/name`）已由 `ProjectsModule` 的 `PROJECT_SERVICE`/`ProjectPinMiddleware` 与 `project-native` adapter 接管；旧 `projectRenameRoute`、server path 判定及 source file 已删除，保留 idempotency/CAS/receipt 与严格输入边界。
- [x] Project delete command（`DELETE /v1/projects/:id`）已由 `ProjectsModule` 的 `PROJECT_SERVICE`/`ProjectPinMiddleware` 与 `project-native` adapter 接管；旧 `projectDeleteRoute`、server path 判定及 source file 已删除，保留 202/Location、idempotency、scope-release/outbox 与取消边界。
- [x] Project resource collection read（`GET /v1/projects/:id/resources`）已由 `ProjectsModule` 的 `PROJECT_SERVICE`/`ProjectPinMiddleware` 与 `project-native` adapter 接管；旧 `projectResourceListRoute`、server dispatcher 分支及 source file 已删除，保留 canonical Project scope、Storage pagination、request-id 与取消预算。
- [x] Project resource metadata/download read（`GET /v1/projects/:id/resources/:asset_id[\/download]`）已由 `ProjectsModule` 的 `ProjectPinMiddleware`/`project-native` adapter 接管；旧 `projectResourceReadRoute` 的 server dispatcher 分支已删除，保留 verified bytes/hash、owner recheck、spool cleanup、request-id 与取消预算。
- [x] Project resource upload（`POST /v1/projects/:id/resources`）已由 `ProjectsModule` 的 `ProjectPinMiddleware`/`project-native` adapter 接管；旧 `projectResourceRoute` 的 server dispatcher 分支已删除，保留 persistent receipt/checkpoint、scan/Complete、idempotency 与 cancellation。
- [x] Project skill-selection（`GET/PUT /v1/projects/:id/skill-selection`）已由 `ProjectsModule` 的 `PROJECT_SKILL_SELECTION_PROVIDER`/`PROJECT_SKILL_INSTALLATION_CLIENT` 与 `ProjectPinMiddleware` 接管；旧 dispatcher 分支已删除，保留 native admission、项目二次授权、安装状态校验、幂等 receipt 与取消边界（`2dd93ca`）。
- [x] Project skill-installations（`/v1/projects/:id/skill-installations/**`）已由 `ProjectsModule` 的 `ProjectPinMiddleware`/`SKILL_AUTHORIZATION` 接管；旧 dispatcher project 分支已删除，package inspection 路径保持由 canonical package route 处理，保留 owner qualification、recheck 与取消边界（`d9a8a24`）。
- [x] Personal skill-installations（`/v1/skill-installations/**`）已由 `SkillsModule` 的 `SkillsMiddleware`/`SKILL_AUTHORIZATION`/`SKILL_INSTALLATION_CLIENT` 接管；旧 personal dispatcher 分支已删除，保留原 owner contract、Skill action admission 与错误闭集（`1153be7`）。
- [x] Managed personal Skill reads（`GET /v1/self/skills[/:skill_id[/versions]]`）已由 `SkillsModule` 的 `SkillsMiddleware` 接管；旧 dispatcher read 分支已删除，保留 projection、IAM enrichment、deadline 与错误映射（`7aa092b`）。
- [x] Browser-private Skill enable command（`/skill.v1.SkillOptionalService/SetSkillInstallationEnabled`）已由 `SkillsModule` 的 `SkillsMiddleware` 接管；旧 dispatcher 分支已删除，保留 owner ACK、错误闭集与 deadline（`2531941`）。
- [x] Skill usage（`POST /v1/skills/usage`）已由 `SkillsModule` 的 `SkillsMiddleware` 接管；`SKILL_USAGE_READER` 通过 `BFF_POOL` 调用既有 projection，旧 dispatcher 分支已删除，保留 admission、批量 refs、unavailable/zero 语义与 10 秒请求预算（`a75930e`）。
- [x] Personal Skill lifecycle（`POST /v1/self/skills/:id/versions`、`POST /withdraw`、`DELETE /v1/self/skills/:id`）已由 `SkillsModule` 的 `SKILL_DRAFT_CLIENT`/`SkillsMiddleware` 接管；旧 dispatcher 分支已删除，保留 action admission、严格路径别名拒绝、CAS/幂等、owner ACK/error 映射与生命周期预算（`e1a4f4d`）。
- [x] Skill draft creation（`POST /v1/skills/drafts`）已由 `SkillsModule` 的 `SKILL_DRAFT_CLIENT`/`SkillsMiddleware` 接管；旧 dispatcher 分支已删除，保留 create-draft action admission、精确路径/查询拒绝、请求体预算、幂等和 owner response projection（`e2365e5`）。
- [x] Skill draft mutations（`PATCH /v1/skills/:id/draft`、`POST /discard`、`POST /audience`）已由 `SkillsModule` 的 `SKILL_PRODUCT_CLIENT`/`SkillsMiddleware` 接管；旧 dispatcher 分支已删除，保留 action admission、strict input、command digest、owner error mapping 与 10 秒预算（`8a85548`）。
- [x] Skill catalog commands（`POST /v1/skills/:id/package-upload[/{complete}]`、`POST /validate`、`POST /publish`）已由 `SkillsModule` 的 `SKILL_DRAFT_CLIENT`/`SkillsMiddleware` 接管；旧 dispatcher 分支已删除，保留 action admission、严格路径、owner command projection、对象来源校验和预算边界（`9fde981`）。
- [x] Skill package-upload reference read（`GET /v1/skills/:id/package-upload`）已由 `SkillsModule` 的 `SKILL_DRAFT_CLIENT`/`SkillsMiddleware` 接管；旧 dispatcher 分支已删除，保留 user admission、owner reference projection、strict headers/query 和 10 秒预算（`6109daa`）。
- [x] Skill cover routes（`GET /v1/skills/:id/cover`、`GET/POST /cover-upload`、`POST /cover-upload/complete`）已由 `SkillsModule` 的 `SKILL_PRODUCT_CLIENT`/`SkillsMiddleware` 接管；旧 dispatcher 分支已删除，保留 fresh admission/recheck、action admission、对象来源校验、PNG/媒体字节验证和预算边界（`6784090`）。
- [x] Published Skill package read（`GET /v1/skills/:id/package`）已由 `SkillsModule` 的 `SKILL_PRODUCT_CLIENT`/`SkillsMiddleware` 接管；旧 dispatcher 分支已删除，保留 user admission、file_path 严格校验、owner bytes projection 和 10 秒预算（`ef1241c`）。
- [x] Skill admin routes（`GET/POST /v1/admin/skills/**`）已由 `SkillsModule` 的 `SKILL_ADMIN_CLIENT`/`SkillsMiddleware` 接管；旧 dispatcher 分支已删除，保留 admin action admission、专用 machine credential、owner ACK/projection 和 10 秒预算（`11ce200`）。
- [x] GitHub Skill preview（`POST /v1/skills/github/preview`）已由 `SkillsModule` 的 `SkillsMiddleware` 接管；旧 dispatcher 分支已删除，保留 preview 输入校验、GitHub immutable resolution、最终 session recheck 和依赖错误映射（`684fb00`）。
- [x] Browser local Skill import（`/browser/v1/skills/local-imports/**`）已由 `SkillsModule` 的 `SKILL_LOCAL_IMPORT_CLIENT`/`SkillsMiddleware` 接管；旧 dispatcher 分支已删除，保留双 action admission、四条 owner RPC、幂等/回放和完整 credential-set gating（`4b8b63d`）。
- [x] Personal Knowledge（`/v1/preferences/knowledge[/**]`、`/v1/preferences/knowledge-usage`）已由 `AccountModule` 的 `PERSONAL_KNOWLEDGE_REPOSITORY`/middleware 接管；旧 dispatcher 分支已删除，保留 tenant/subject admission、revision/CAS、limit/tombstone、usage 和 5 秒预算（`e8d7cf6`）。
- [x] 对与 LegacyRoutes 重叠的 Chat/AgentRuns path family 已增加负向 bypass；当前已迁移 path 由测试锁定不再进入 LegacyRoutes（`ba8ab60`）。
- [ ] 每迁移一批，从 `LegacyRoutesRuntime` 删除具体 path，并验证 adapter 不再接收该 path。
- [ ] route census 清零后删除 `legacy-routes.runtime.ts`、module、middleware、旧 dispatcher。
- [ ] 验证唯一 Nest listener 和唯一 `AppModule` composition root。

### G3：Repository / Service / Port 收敛

- [x] 为 `BffBusinessStore`、`BffApplicationServices`、`PostgresBffRepositories` 建立字段/方法/消费者清单。
- [x] 为 `src/application/ports/**` 逐项写 keep/move/merge/delete 及事务、锁、CAS、lease、outbox、owner evidence。
- [x] 首个 C-3 slice 已将 `PersonalizationProvider` 从 `BffApplicationServices` 移到 `BffBusinessStore.personalizationProvider` 的显式 raw-server seam；CAS/事务实现未复制。
- [x] Chat archive/share 首个 provider seam 已接入 `CHAT_SERVICE`，`ChatModule` 通过唯一 `BFF_DATABASE` 构造 `ChatApplicationService`；旧 `businessStore.services.chat` 仅作为 transitional raw-server fallback，待全部 Chat route cutover 后删除。
- [x] Project pin provider seam 已接入 `PROJECT_SERVICE`，`ProjectsModule` 通过唯一 `BFF_DATABASE` 构造 `ProjectService`；旧 `businessStore.services.projects` 仅作为 transitional raw-server fallback，待剩余 Project route cutover 后删除。
- [x] Project core-read provider 已扩展 deletion-status read；`ProjectService.deletion`/`ProjectRepository.projectDeletion` 继续作为唯一 owner，未新增 repository/service/receipt。
- [x] Project core-read provider 已扩展 rename command；`ProjectService.rename`/`ProjectRepository.renameProject` 继续作为唯一 owner，未新增 mutation framework 或第二 SQL writer。
- [x] Project core-read provider 已扩展 delete command；`ProjectService.delete`/`ProjectRepository.deleteProject` 继续作为唯一 owner，未新增 mutation framework 或第二 SQL writer。
- [x] Project core-read provider 已扩展 tasks read；`ProjectService.tasks`/`ProjectRepository.listTasks` 继续作为唯一 owner，未新增 repository/service/SQL writer（`e1f2b81`）。
- [x] Project resource-list provider 使用既有 `ProjectService.find` + `StorageUploadClient` owner seam；未新增资源 Repository、Storage transport 或 global store reader。
- [x] Project resource-read provider 使用窄 `ProjectResourceProjectReader.find` + 既有 `ProjectResourceAccessClient`/verified spool owner seam；未新增资源 Repository、Storage transport 或 global store reader。
- [x] Project resource-upload provider 使用窄 Project reader + `PostgresIdempotencyRepository` + 既有 Storage upload owner seam；未新增资源 Repository、Storage transport 或第二 receipt owner。
- [x] ScheduledTask read provider seam 已接入 `SCHEDULED_TASK_READ_SERVICE`，`ScheduledTasksModule` 通过唯一 `BFF_DATABASE` 构造 `PostgresScheduledTaskRepository` + Scheduler state reader；raw test composition 保持 `routeHandler` 旁路，避免改变 mutation fixture。
- [x] AgentRuns reader provider seam 已接入 `AGENT_RUNS_READER`，`AgentRunsModule` 通过唯一 `BFF_DATABASE` 构造 `PostgresAgentDispatchOutboxRepository`，同时提供 submitted-run 与 project-binding reader；不复制 outbox/SQL owner。
- [x] Agent dispatch/cancellation outbox worker lifecycle 已移入 `AgentDispatchModule`；repository、delivery、worker identity 与 disabled-agent branch 均为 feature-owned provider，旧 runtime 不再启动同一实例（`ba8ab60`）。
- [x] AG-UI projector lifecycle 已移入 `AguiModule`；canonical projection/consumer providers 与 Agent source reader 保持同一 owner boundary，旧 runtime 不再启动同一实例（`ba8ab60`）。
- [x] ScheduledTask outbox worker lifecycle 已移入 `ScheduledTasksModule`；Postgres scheduled repository 与 Scheduler delivery 只在该 feature provider graph 构造，旧 runtime 不再启动同一实例（`ba8ab60`）。
- [x] Project-scope release worker lifecycle 已移入 `ProjectsModule`；Postgres outbox、Storage release transport、bounded stop 与 storage-disabled branch 均保持同一 owner boundary（`ba8ab60`）。
- [x] Scheduled Agent worker lifecycle 已移入 `ScheduledTasksModule`；scheduled dispatch/terminal repository、bounded retry/concurrency、Agent source/delivery 与 shutdown ordering 保持同一 owner boundary（`ba8ab60`）。
- [x] Project-scoped Chat read provider seam 已接入 `CHAT_SERVICE` + `PROJECT_SERVICE`；不新增 Project Repository、Chat read service 或第二授权路径（`ba8ab60`）。
- [x] Scheduler callback provider seam 已接入 `SCHEDULED_TASK_SERVICE`、`SCHEDULER_DISPATCH_RECEIPTS` 与 `SCHEDULED_AGENT_DISPATCH_REPOSITORY`；不新增第二 receipt/task owner（`ba8ab60`）。
- [x] ScheduledTask mutation provider seam 已接入 `SCHEDULED_TASK_SERVICE` + `SCHEDULED_TASK_IDEMPOTENCY`；read/callback/mutation 共享 canonical repository 与持久 receipt（`ba8ab60`）。
- [x] Run display provider seam 已接入 `RUN_DISPLAY_PROVIDER`，由 `AGENT_RUNS_READER` 与 `CHAT_SERVICE` 组合；ChatModule 不再反向依赖 AgentRunsModule，消除循环 module graph。
- [x] Project skill-selection provider 已接入 `PROJECT_SKILL_SELECTION_PROVIDER` 与 `PROJECT_SKILL_INSTALLATION_CLIENT`；只暴露 ProjectService 窄读写与 Idempotency receipt，未复制 Project Repository 或第二 CAS owner。
- [x] Project MCP recommendations provider 已接入 `McpModule` 的 `PROJECT_MCP_RECOMMENDATIONS_PROVIDER`、`MCP_AUTHORIZATION` 与 candidate clients；保留 owner candidate validation、MCP read admission、CAS 和 client shutdown，不引入 global store reader。
- [x] Connector list（`GET /v1/connector.list`）已由 `McpModule` 的 `MCP_PERSONAL_CLIENT`/`ConnectorListMiddleware` 接管；入口在 native middleware 先完成 session 与 MCP read admission，再复用原 projection/分页/owner read，旧 dispatcher 分支已删除，保留 request-id、no-store、输入闭集、分页循环和 owner 缺失/拒绝错误语义（`418021f`）。
- [x] MCP provider/package admin（`/v1/admin/mcp/providers/**`、`/v1/admin/mcp/packages/**`）已由 `McpModule` 的 `MCP_PROVIDER_ADMIN_CLIENT`/`MCP_PACKAGE_ADMIN_CLIENT`/`McpAdminMiddleware` 接管；旧 dispatcher 分支删除，复用现有 catalog admission、platform-admin qualification、idempotency/body/deadline/cancellation、owner error projection 与 client shutdown（`b178828`）。
- [x] MCP project publication（`/browser/v1/mcp/**` project publication/pin/receipt）已由 `McpModule` 的 `MCP_PROJECT_PUBLICATION_CLIENT`/`McpProjectPublicationMiddleware` 接管；native adapter 保留 project scope recheck、MCP read/manage admission、receipt/CAS、原始 command digest、取消与 owner result validation，旧 dispatcher 分支删除（`9adb097`）。
- [x] App skill-bindings（`/v1/admin/open-apps/:app_id/skill-bindings[/:series_id]`）已由 `SkillsModule` 的 `APP_SKILL_BINDING_CLIENT`/`OPEN_APP_MANAGEMENT_ADMISSION`/`SkillsMiddleware` 接管；fresh operator registration、exact app/tenant binding、独立 catalog/projection credentials、CAS/idempotency 与 owner response validation 保持不变，旧 dispatcher 分支删除（`49511ae`）。
- [x] Skill specification reads（`/v1/skill.list`、`/skill.v1.SkillOptionalService/*`、`/skill.v1.SkillService/DownloadSkill`）已由 `SkillsModule` 的 `SKILL_LIST_ADMISSION`/`SKILL_SPECIFICATION_SOURCE`/`SKILL_DOWNLOAD_HANDLES`/`SkillsMiddleware` 接管；public identity recheck、private session admission、exact source projection、opaque download handle 与 response/error contract 保持不变，旧 dispatcher 分支删除（`dff1787`）。
- [x] 全部 Skill package inspection（`GET /v1/self/skills/:id/package`、`GET /v1/skill-installations/:id/package`、`GET /v1/projects/:id/skill-installations/:installation_id/package`）已由 SkillsModule/ProjectsModule 的 `SKILL_PACKAGE_INSPECTION_CLIENT` middleware 接管；strict path/query/header validation、current admission、exact project scope、owner projection 与 bounded package response 保持不变，旧 dispatcher 分支删除（`b610c92`）。
- [x] Exact Skill download POST (`/browser/v1/skill-installations/:id/download`、`/browser/v1/skills/:id/download`、`/browser/v1/skill-shares/:id/download`、`/browser/v1/projects/:id/skill-installations/:id/download`) 与 GET opaque handles (`/skill-downloads/:handle`) 已由 SkillsModule/ProjectsModule 的 exact source/native middleware 接管；installation/managed/share/project installation 均保留 source/revision 资格重读、项目 scope recheck、opaque handle 与 verified byte binding，`ExactSkillDownloadService` 支持 project-only feature source，旧 dispatcher 两类 Skill download 分支已删除（`6633306`、`da7f9be`、`9c04630`）。
- [x] C-3 Chat cleanup 先完成 `CHAT_SERVICE`/`CHAT_TURN_SERVICE` feature provider 接线与 raw/test fallback（`fb14159`），随后由 `a3fd669`、`4e76866` 删除 `BffBusinessStore`/`PostgresBffRepositories` 上的 ChatTurn/Chat 重复字段；不新增 Repository/Service/SQL owner。
- [x] Music cleanup 已由 `MusicModule`/`MusicMiddleware` 接管 `/v1/mori/**`；native adapter 复用原 `liveMoriBusiness`、admission、receipt 幂等、owner projection/SSE、取消与 late-admission fence，raw `createBffServer` 只复用同一 adapter，旧 `handleBffRequest` Mori 分支删除（`e3c2b2d`）。
- [x] Message regeneration cleanup 已由 `ChatModule`/`AgentDispatchModule` 接管；`CHAT_TURN_SERVICE` 与 `AGENT_DISPATCH_OUTBOX` 复用同一 Postgres outbox 实例和 stable-id owner，native adapter 保留 source-only input、fresh admission、bounded body、idempotency 与 final re-admission，raw dispatcher 兼容路径继续仅供 raw/test composition（`8b01a14`）。
- [x] Project skill-installations 复用 `SkillInstallationConnectClient` 与 `ProjectService.find`，通过 `SKILL_AUTHORIZATION` 保留写操作权限检查；未新增 Skill Repository、Project mutation writer 或 package route alias。
- [x] Personal skill-installations 将共享 `SkillInstallationConnectClient`/`SKILL_AUTHORIZATION` owner seam 收敛到 `SkillsModule`，ProjectsModule 仅消费其导出的窄 client；未保留第二 Platform client 或 personal route dispatcher。
- [x] Skill enable command 复用 `SkillsModule` 导出的 installation client 与 SessionAdmission；未复制 owner command、receipt 或新 Platform transport。
- [x] Skill usage 复用既有 `readSkillUsage` projection 与 PostgreSQL pool；未新增 Repository、Service、SQL owner 或第二错误协议。
- [x] Personal Skill lifecycle 复用既有 `CatalogConnectClient` 与三条 canonical route handler；未新增 Repository、Service、receipt 或 owner contract。
- [x] Skill draft creation 复用同一 `CatalogConnectClient` 与既有 `createSkillDraftRoute`；未新增 Repository、Service、receipt 或 owner contract。
- [x] Skill draft mutations 复用既有 `SkillProductConnectClient` 与 `skillDraftsRoute`，未新增 Repository、Service、receipt 或 owner contract。
- [x] Skill catalog commands 复用既有 `CatalogConnectClient` 与四条 canonical route handler，未新增 Repository、Service、receipt 或 owner contract。
- [x] Skill package-upload reference read 复用既有 `CatalogConnectClient` 与 `getSkillPackageUploadRoute`，未新增 Repository、Service、receipt 或 owner contract。
- [x] Skill cover routes 复用既有 `SkillProductConnectClient` 与 `skillCoverRoute`，未新增 Repository、Service、receipt 或 owner contract。
- [x] Published Skill package read 复用既有 `SkillProductConnectClient` 与 `publishedSkillPackageInspectionRoute`，未新增 Repository、Service、receipt 或 owner contract。
- [x] Skill admin routes 复用既有 `SkillAdminConnectClient` 与 `skillAdminRoute`，未新增 Repository、Service、receipt 或 owner contract。
- [x] GitHub Skill preview 复用既有 `GithubSkillImportClient` 与 `skillGithubPreviewRoute`，未新增 Repository、Service、receipt 或 owner contract。
- [x] GitHub Skill import (`POST /v1/skills/github/import`) 已由 `SkillsModule` `handleSkillGithubImportRequest` 接管；共享 `IdempotencyRepository` receipt 协议、immutable source、owner handoff 与 readmit 行为保持不变，旧 dispatcher 分支已移除。
- [x] AI Skill import (`POST /v1/skills/ai-import`) 已由 `SkillsModule` `handleSkillAiImportRequest` 接管；receipt handoff 使用窄 provider，Chat artifact association 通过 `SKILL_AI_ASSOCIATION` 跨 feature port 注入，旧 dispatcher 分支已移除，raw test composition 保留兼容 fallback。
- [x] Admin identity (`GET /v1/admin/identity/{members,invitations,roles}`) 已由 `AccountModule` `handleAdminIdentityRequest` 接管；tenant/administrator qualification、page query 和 IAM error mapping 保持不变，旧 dispatcher 分支已移除。
- [x] Billing admin (`POST /v1/admin/billing/credit-grants`, `/v1/admin/billing/metering/**`) 已由 `BillingModule` `handleBillingAdminRequest` 接管；administrator recheck、deadline、owner error mapping 与 body/header validation 保持不变，旧 dispatcher 分支已移除。
- [x] System admin (`/v1/admin/model-*`, `/v1/admin/model-providers/**`) 已由 `SystemModule` `handleSystemAdminRequest` 接管；administrator admission、strict request shape、deadline/cancellation 和 System owner mapping 保持不变，旧 dispatcher 分支已移除。
- [x] Chat move (`POST /v1/sessions/:id/move`) 已由 `ChatModule` `handleMoveSessionRequest` 接管；canonical conversation id、幂等 key、scope 语义、abort 与 move owner 结果保持不变，旧 dispatcher 分支已移除。
- [x] Skill share (`/v1/skill-shares/**`) 已由 `SkillsModule` `SKILL_SHARE_REPOSITORY`/`SKILL_SPECIFICATION_SOURCE` 与 `handleSkillShareRequest` 接管；validated public origin、owner inspection、creator revoke、current qualification 与旧 HTTP 行为保持不变，旧 dispatcher 分支已移除。
- [x] Browser local Skill import 复用既有 `LocalSkillImportConnectClient` 与 `localSkillImportRoute`，未新增 Repository、Service、receipt 或 owner contract。
- [x] Personal Knowledge 复用既有 `PostgresPersonalKnowledgeRepository` 与 `personalKnowledgeRoute`，未新增 Repository、Service、receipt 或 SQL owner。
- [x] C-3 Knowledge cleanup 已将 `personalKnowledge` 从 `BffApplicationServices` service aggregate 移到 `BffBusinessStore.personalKnowledge` transitional seam；AccountModule 继续拥有 canonical feature provider，未改变 SQL/事务 owner。
- [x] C-3 Skill usage cleanup 已将 `skillUsage` 从 `BffApplicationServices` service aggregate 移到 `BffBusinessStore.skillUsage` transitional seam；SkillsModule 继续拥有 canonical `SKILL_USAGE_READER` provider，未改变 projection SQL owner。
- [x] C-3 Skill AI association cleanup 已将 `skillAiAssociation` 从 `BffApplicationServices` service aggregate 移到 `BffBusinessStore.skillAiAssociation` transitional seam；GitHub/AI import 继续复用同一 artifact owner 查询。
- [x] C-3 Skill share cleanup 已将 `skillShares` 从 `BffApplicationServices` service aggregate 移到 `BffBusinessStore.skillShares` transitional seam；share/exact-download owner repository 未复制。
- [x] C-3 Public share cleanup 已将 `PublicShareApplicationService` 从 `BffApplicationServices` service aggregate 移到 `BffBusinessStore.publicShareService` transitional seam；ChatModule 继续拥有 canonical provider。
- [x] C-3 ScheduledTask cleanup 已删除 `BffBusinessStore.scheduledTaskService` seam；runtime snapshot、scheduler callback 与 live-bff authorization/create/update/delete/retry 统一读取 `services.scheduledTasks`。
- [x] C-3 Project cleanup 已删除 `BffBusinessStore.projectService` seam；Project/Chat authorization、resource、Skill-selection、MCP recommendation 与 live-bff project consumers 统一读取 `services.projects` 或 feature composition（`2cc1c1b`）。
- [ ] 继续移动有真实边界的 Port，不改行为；再合并单实现薄 Service/Repository。
- [ ] 旧 global wrapper 不再出现在生产 composition 后删除；反向 import census 为零。
- [ ] 检查无 BaseRepository、无空模块、无第二套 DTO/SQL/ORM owner、无 sibling 相对路径穿透。

### G4：C-4 清理与全量验证

- [ ] 删除旧兼容/fallback/evolution/dispatcher 测试、fixture、helper、脚本；保留独有安全与可靠性证据。
- [ ] 停写后串行执行 Root topology/diff-check、IAM owner gate、BFF owner gate、App owner gate、Agent owner gate。
- [ ] 将 pass/fail/skip/baseline/环境缺口写入证据文档；不把 skip 或 mock 写成通过。
- [ ] 复核 `git diff --check`、import census、route census、contract digest、唯一 listener/composition root。

### G5：A-01/A-02/A-07 开闸

- [ ] 仅当 G1～G4 全部通过且无未决设计/契约/数据 owner 冲突时建立 A-01 实施计划。
- [ ] A-02 只接 canonical AG-UI/snapshot/parts/RunDisplay，不新增解释事件或第二网络协议。
- [ ] A-07 先冻结 ProjectTask schema/authorization/concurrency/idempotency contract，再生成 App client，最后接页面；不直接 SQL 灌记录。

## 5. 闭环逻辑（每个 feature slice 必须重复）

```text
事实盘点
  → owner/边界决定
  → contract 或 red 行为测试
  → 最小 feature-local 实现
  → 从 LegacyRoutes/旧组合器移除具体入口
  → 反向 import/route census 为零
  → focused lint/typecheck/build/test
  → 停写后串行全量门禁
  → 更新 evidence、状态和下一依赖
```

任何一步缺证据，slice 仍为“进行中”，不得进入下一层删除。删除顺序固定为：先消费者切换，再行为验证，再删除旧入口和只服务旧入口的测试，最后删除全局组合器与无边界抽象。

## 6. “不要无意义代码”硬规则

1. 不把 LegacyRoutes 改名成 Controller；Controller 必须拥有真实输入/输出边界和对应业务 provider。
2. 不创建通用 `BaseRepository`、万能 `Service`、空 `Module`、重复 DTO、重复错误映射或第二套网络协议。
3. 不为满足架构测试制造只检查目录/字符串的测试；测试必须保护公开行为、契约或真实可靠性风险。
4. 不删除仍承载事务、CAS、lease、outbox、幂等、权限、取消、replay、恢复的边界；先迁移 owner，再删除包装。
5. 不保留无消费者的 alias/fallback/双读/双写；也不在消费者未切换时先删旧入口。
6. 不修改 Task B、无关 CURRENT backlog、生产数据、Schema、发布配置或 A-01/A-02/A-07 业务行为。

## 7. 当前停止线与下一步

> 更新（BFF `b610c92`）：admin identity、billing admin、system admin、Chat move、project skill-selection、project MCP recommendations、`GET /v1/connector.list`、MCP provider/package admin、MCP project publication、App skill-bindings、Skill specification reads、全部 Skill package inspection、project/personal skill-installations、managed personal Skill reads、Skill enable command、Skill usage、personal Skill lifecycle、Skill draft creation/mutations、Skill catalog commands/read/cover、published package read、Skill admin、GitHub preview/import、AI import、Skill share、local import、Personal Knowledge 已分别由 Projects/Skills/Mcp/Account feature middleware 接管，并从旧 dispatcher 分支移除。同时将 Knowledge repository、Skill usage reader、Skill AI association、Skill shares、Public share service、ScheduledTask service seam 从 `BffApplicationServices` service aggregate 迁到 named `BffBusinessStore` transitional seams，ScheduledTask live-bff authorization/create/update/delete/retry consumers 已优先使用 named seam；native chain 保留 mock/raw composition 的行为闭环，Chat artifact association 与 Skill specification source 通过窄 provider 注入。本轮 Nest architecture 17/17、BFF architecture 34/34、BFF mock contract 25/25、connector-list HTTP 5/5、MCP provider/package admin HTTP 12/12、MCP project publication HTTP 27/27、App skill-bindings/Open App management 12/12、Skill specification contract/focused 149/149、package inspection unit 47/47（4 个环境 skip）；停写后最新 `pnpm test` 为 2312 tests / 2295 pass / 15 fail / 2 skip，失败集中在既有 Artifact/Personal Storage Product HTTP、Project exact-download、Admin Web credential fixture 与 anonymous Share fixture，不作为 C-4 通过；other Skills route、剩余 Skills/MCP route、LegacyRoutes 退出及 global Port 收敛继续阻塞 A-01/A-02/A-07。

> 当前 C-3 反向消费者复核（BFF `5659b1d`）：`BffApplicationServices` 仍保留 `projects`、`scheduledTasks`、`chat`、`chatTurns` 四个兼容聚合字段，但 `BffBusinessStore` 不再重复暴露 Chat/ChatTurn/Project/ScheduledTask service 字段。生产源码仍有 `services.(projects|scheduledTasks|chat|chatTurns)` 引用，主要集中在 LegacyRoutes 兼容路径、Chat POST/Agent dispatch、exact-download/project fallback 与 integration fixtures。LegacyRoutes/createBffComposition/handleBffRequest 仍有生产引用，需继续按 owner seam 清零后再删除 aggregate 与 LegacyRoutes。


> 全量验证更新：最新 `pnpm test` 已在停写工作树上运行到终态：2312 tests / 2295 pass / 15 fail / 2 skip；native/admin/Skill specification focused paths均通过，但仍有 Artifact/Personal Storage Product HTTP、Project exact-download、Admin Web credential fixture、以及部分 user-admission anonymous Share fixture 失败。该结果确认当前全量门禁仍非绿，不能作为 C-4 通过；失败项继续按 owner baseline 单列，不删除断言、不放宽测试、不提前打开 A gate。

当前已完成问题整理、Goal/TODO 冻结、技术方案和 C-1.3 App native identity 第一闭环（adapter、SSR admission、session probe、BFF `/v1/me` proof），并完成 account profile read/update、account sessions、Team 的 native owner transport；profile-read contract/artifact/consumer cutover 已由 Root `c7af342` 固定。App native session read、issuer signout handoff 与 browser signout client 已脱离旧 RP runtime dependency。C-2 已将 IAM relay、current-user `/v1/me`、项目集合 `GET /v1/projects`、详情、instruction-revisions、deletion-status、rename、delete、resource-list、resource-read/download、resource-upload、resource-delete、skill-selection、MCP recommendations、public share projection 分别收敛到 feature middleware/provider；旧 dispatcher 仍保留其余 route families。C-3 personalization、Chat、Project pin、Project core-read（deletion-status/rename）、ScheduledTask read、AgentRuns reader/provider、Project resource receipt/provider、Project skill-selection 与 MCP recommendations provider seam 已建立；BFF 最新切片验证为 nest architecture 14/14、architecture 34/34、MCP focused 15/15，旧全量 baseline 仍单列。仍未完成的是完整 sign-in/tenant-switch/permission/revocation UI 收据、LegacyRoutes 全量退出、剩余 global Repository/Service/Port 收敛、App typecheck `onReconnect` baseline 与 C-4 跨 owner 停写后串行门禁；A-01/A-02/A-07 继续停写。下一步按 inventory 迁移 project skill-installations 与剩余 Chat/Agent/Scheduled/Skills/MCP route bundle，并继续拆 global provider；每个 bundle 完成 focused、architecture 与串行门禁后再扩展下一批。



## 9. 2026-10-31 direct Chat read cutover

- BFF child `0823d97` 将 `GET /v1/sessions`、`GET /v1/sessions/:id`、`GET /v1/sessions/:id/messages`、Message parts 与 Run process direct reads 接入 `ChatModule` 的 `handleChatBusinessReadRequest`；入口在 Nest `ChatMiddleware` 与 raw `createBffServer` 双链路注册。
- 新 route 只接收 direct/no-`project_ref` GET，先走 `authorizeUserRequest`，再走 `authorizeChatRequest` 的 owner recheck，最后复用 `liveChatBusiness` 的既有 envelope、cursor、read budget、取消和错误映射；`ChatBusinessProvider` 将 Chat/Project/ChatTurn/AG-UI 依赖从 `BffBusinessStore` 解耦为 feature-local seam。
- 验证：direct Chat read 2/2、BFF mock contract 25/25、Nest architecture 18/18、BFF architecture 34/34、`pnpm lint`、`pnpm typecheck`、`pnpm build`；串行全量 2316 tests / 2299 pass / 15 fail / 2 skip，15 项失败仍为既有 Artifact/Personal Storage Product HTTP、Project exact-download、Admin Web credential fixture 与 anonymous Share fixture。
- 下一步仍只推进 C-1.3/C-2/C-3：Chat POST/events/project scope、Agent/AG-UI route bundle 与剩余 global provider/Port；A-01/A-02/A-07 继续停写。
- `630efbf` 的 Chat bypass 只关闭已迁移路径对 LegacyRoutes 的消费，不改变 raw `createBffServer` 兼容入口；下一步仍是 Chat POST/events/project scope，再进入 Agent/AG-UI 与 global provider/Port census。
- `3961450` 将 direct title/delete/share 的 receipt owner 下沉到 ChatModule；下一步仍是 Chat POST/events/project scope，不能删除 `BffApplicationServices.chat` 或 Chat Repository。
- `76b9402` 将 direct events 的 projection/consumer/runtime provider 下沉到 AguiModule；下一步仍是 Chat POST 与 project-scoped events，再清理 Agent/AG-UI worker ownership。
- `ff14c86` 将 ProjectAccessModule 作为 Chat/Projects 共享 owner，关闭 project-scoped Chat mutation/event 的重复 service 风险；下一步聚焦 Chat POST messages。
- `ff14c86` 将 Chat POST 的 Skill installation client 提取为共享 owner；下一步转入 Agent dispatch worker、remaining run-control 与 global Port census。
- `a5b94c0` 将 run-control receipt/admission 下沉到 AgentRunsModule；下一步转入 Agent dispatch worker lifecycle、remaining session/run paths 与 global Port census。

### 2026-10-31 C-3 ChatTurn seam cleanup

- BFF child `a3fd669` 删除 `BffBusinessStore.chatTurnService` 与 `PostgresBffRepositories.chatTurnService`，因为 ChatTurn 已由 `AgentDispatchModule` 的 `CHAT_TURN_SERVICE` 提供，生产消费者已不再读取全局 seam。
- 先更新 architecture oracle 观察到预期失败，再删除字段并复跑：BFF architecture 34/34、`pnpm build`、`pnpm lint`、`pnpm typecheck` 全部通过。
- `BffApplicationServices.chatTurns` 仍是 transitional aggregate，待 Chat POST/Agent dispatch route cutover 后再按 provider census 删除，未提前删除真实 outbox owner。

### 2026-10-31 C-3 Chat service seam cleanup

- BFF child `4e76866` 删除 `BffBusinessStore.chatService` 与 `PostgresBffRepositories.chatService`；raw composition 改由 `BffApplicationServices.services.chat` 提供兼容读取，feature middleware 继续使用 `CHAT_SERVICE`。
- 该切片不删除 `BffApplicationServices.chat` 或 Chat Repository：Chat POST、events、project scope 和 LegacyRoutes 仍有真实消费者，保留 canonical application/repository owner，避免复制实现。
- 验证：BFF architecture 34/34、BFF mock/chat/direct-read focused 143/143、`pnpm build`、`pnpm lint`、`pnpm typecheck` 全部通过。

### 2026-10-31 Chat route provider handoff

- BFF child `9c1c674` 将旧 `handleBffRequest` 的 Chat authorization/live Chat 调用改为显式 `ChatBusinessProvider`，由 `CHAT_SERVICE`、`AgentDispatchModule` 的 `CHAT_TURN_SERVICE`、`PROJECT_SERVICE` 与 AG-UI consumer seam 组装；不再把完整 `BffBusinessStore` 作为 Chat route provider 传入。
- 该切片只收敛依赖边界，不改变 Chat POST/events/project scope 的路由归属；因此保留原幂等、项目访问、Agent dispatch 与 AG-UI 行为。
- 验证：BFF architecture 34/34、BFF mock/chat/direct-read focused 143/143、`pnpm build`、`pnpm lint`、`pnpm typecheck` 全部通过。

### 2026-10-31 Chat provider aggregate closure

- BFF child `f40f6a3` 删除 `ChatBusinessProvider.services` fallback；Chat authorization/live Chat 现在只接收具名 `chatService`、`chatTurnService`、`projectService` 与 `agUiConsumers`。
- 旧 Chat unit fixtures 同步改为具名 provider，避免测试继续把 global `BffApplicationServices` 当作 Chat route contract。
- 验证：Chat/BFF focused 230/230、BFF architecture 34/34、`pnpm build`、`pnpm lint`、`pnpm typecheck` 全部通过。

### 2026-10-31 Project provider aggregate closure

- BFF child `5659b1d` 删除 `BffBusinessStore.projectService` 与 `PostgresBffRepositories.projectService`。
- Project/Chat authorization、resource、MCP recommendation、skill-selection、live-bff 与 raw runtime 统一读取 `services.projects` 或 feature composition 的 `PROJECT_SERVICE`，不再把重复 Project service 字段作为 global locator。
- 验证：BFF architecture 34/34；BFF project/chat focused 193/193；`pnpm build`、`pnpm lint`、`pnpm typecheck` 全部通过。

### 2026-10-31 ScheduledTask provider aggregate closure

- BFF child `5659b1d` 删除 `BffBusinessStore.scheduledTaskService` 与 `PostgresBffRepositories.scheduledTaskService`。
- ScheduledTask read/runtime、live-bff mutation、Scheduler callback 统一读取 `services.scheduledTasks`；`ScheduledTasksModule` 的 `SCHEDULED_TASK_READ_SERVICE` 继续作为 native feature provider。
- 验证：BFF architecture 34/34、BFF mock/scheduler/scheduled focused 106/106、`pnpm build`、`pnpm lint`、`pnpm typecheck` 全部通过。

### 2026-10-31 Root governance gate recheck

- `python3 -m pytest scripts/tests -q`：1844 passed，502 subtests passed，3 skipped，2 failed。
- 失败为当前环境/已有治理基线：`test_serve_local_login.py::test_occupied_port_is_not_reused_or_terminated`；`test_w2_bff_storage_smoke.py::test_exact_object_cleanup_and_database_nonadoption` 因 `@aws-sdk/client-s3` 本地依赖缺失。
- 该结果不计为 C-4 通过；BFF focused/full 与 Root topology 证据保持单列，未扩散修复到本次 C-3 provider 清理范围。

### 2026-10-31 Account personalization provider closure

- BFF child `5659b1d` 删除 `BffBusinessStore.personalizationProvider` 与 `PostgresBffRepositories.personalizationProvider`。
- AccountModule 的 `PERSONALIZATION_PROVIDER` 已是 canonical provider；LegacyRoutes runtime 通过显式 `personalizationProvider` option 传入，raw composition 不再从 global store 读取。
- 验证：BFF architecture 34/34、Account/personalization/team/BFF focused 55/55、`pnpm build`、`pnpm lint`、`pnpm typecheck` 全部通过。

### 2026-10-31 Personal Knowledge feature-provider handoff

- BFF child `5659b1d` 为 `BffServerComposition` 增加 `personalKnowledgeRepository` seam；`LegacyRoutesRuntime` 从 AccountModule 注入 `PERSONAL_KNOWLEDGE_REPOSITORY` 并显式传给 transitional raw composition。
- raw Personal Knowledge route 不再只能从完整 `BffBusinessStore` 定位 Repository；`BffBusinessStore.personalKnowledge` 暂保作 raw/test fallback，删除门已明确。
- 验证：Nest runtime architecture 4/4、Personal Knowledge/BFF focused 28/28、`pnpm lint`、`pnpm typecheck`、`pnpm build` 全部通过。

### 2026-10-31 Skill usage feature-provider handoff

- BFF child `5659b1d` 为 `BffServerComposition` 增加 `skillUsageReader` seam；`LegacyRoutesModule` 导入 `SkillsModule`，`LegacyRoutesRuntime` 注入 `SKILL_USAGE_READER` 并显式传给 raw composition。
- raw Skill usage route 不再只能从完整 `BffBusinessStore` 定位 reader；`BffBusinessStore.skillUsage` 暂保 fallback，删除门已明确。
- 验证：Nest runtime architecture 5/5、Skill usage/BFF focused 29/29、`pnpm build`、`pnpm lint`、`pnpm typecheck` 全部通过。

### 2026-10-31 Skill association feature-provider handoff

- BFF child `5659b1d` 为 `BffServerComposition` 增加 `skillAiAssociation` seam；`LegacyRoutesRuntime` 从 SkillsModule 注入 `SKILL_AI_ASSOCIATION` 并显式传给 raw composition。
- raw AI Skill import 不再只能从完整 `BffBusinessStore` 定位 association reader；`BffBusinessStore.skillAiAssociation` 暂保 fallback，删除门已明确。
- 验证：Nest runtime architecture 5/5、AI/GitHub Skill focused 105/105、`pnpm build`、`pnpm lint`、`pnpm typecheck` 全部通过。

### 2026-10-31 Skill share feature-provider handoff

- BFF child `5659b1d` 为 `BffServerComposition` 增加 `skillShareRepository` seam；`LegacyRoutesRuntime` 从 SkillsModule 注入 `SKILL_SHARE_REPOSITORY` 并显式传给 raw composition。
- raw Skill share/exact-download route 不再只能从完整 `BffBusinessStore` 定位 share repository；`BffBusinessStore.skillShares` 暂保 fallback，删除门已明确。
- 验证：Nest runtime architecture 5/5、Skill share/exact-download/BFF focused 40/40、`pnpm build`、`pnpm lint`、`pnpm typecheck` 全部通过。

### 2026-10-31 Public Share feature-provider handoff

- BFF child `330e439` 为 `BffCompositionOptions` 增加 `publicShareService` seam；`LegacyRoutesModule` 导入 `ChatModule`，`LegacyRoutesRuntime` 注入 `PUBLIC_SHARE_SERVICE` 并显式传给 transitional raw composition。
- raw `GET /v1/shared/{shareId}` 继续复用 `composition.publicShareService`；`BffBusinessStore.publicShareService` 暂保为未迁移 raw/test composition fallback，删除门保持为 raw consumer 清零。
- 验证：Nest runtime architecture 5/5、Skill share/exact-download/BFF focused 40/40、`pnpm build`、`pnpm lint`、`pnpm typecheck` 全部通过。

### 2026-10-31 Scheduled current-read provider handoff

- BFF child `46bb5ac` 为 `BffCompositionOptions` 增加 `scheduledTaskReader` seam；`LegacyRoutesModule` 导入 `ScheduledTasksModule`，`LegacyRoutesRuntime` 注入 `SCHEDULED_TASK_READ_SERVICE` 并显式传给 transitional raw composition。
- current-read route 继续使用 `composition.scheduledTaskReader`；旧 `BffBusinessStore.services.scheduledTasks` reader 仅保留 raw/test composition fallback。ScheduledTask mutation/callback/outbox 仍未迁移，LegacyRoutes 不能删除。
- 验证：Nest runtime architecture 5/5、scheduler focused 38/38、`pnpm build`、`pnpm lint`、`pnpm typecheck` 全部通过。

### 2026-10-31 Chat/Project service provider handoff

- BFF child `d2b0bfe` 扩展 `LegacyRoutesModule` 的 feature imports，`LegacyRoutesRuntime` 注入 `CHAT_SERVICE`、`CHAT_TURN_SERVICE`、`PROJECT_SERVICE`，并通过 `BffCompositionOptions` 传入 transitional raw composition。
- Chat authorization/turn composition 优先使用 `composition.chatService`/`composition.chatTurnService`，Project owner 继续优先 `composition.projectService`；`BffApplicationServices` fallback 仅用于未迁移 raw/test consumers。
- 验证：Nest runtime/feature architecture 20/20、Chat+Scheduler focused 156/156、`pnpm build`、`pnpm lint`、`pnpm typecheck` 全部通过。

### 2026-10-31 Project skill-selection provider handoff

- BFF child `b9ac010` 将 `PROJECT_SKILL_SELECTION_PROVIDER` 从 `ProjectsModule` 注入 `LegacyRoutesRuntime`，并通过 `BffCompositionOptions.projectSkillSelectionProvider` 传给 raw server。
- `handleProjectSkillSelectionRequest` 优先使用 feature provider；旧 `projectSkillSelectionProvider(BffBusinessStore)` 仅保留 raw/test fallback。Exact Project download fixture failures仍按既有 baseline 记录，不因该 provider handoff 扩大范围。
- 验证：Nest runtime/feature architecture 20/20、Project pin/skill focused 12/12（exact Project download fixture failures 10 项）、`pnpm build`、`pnpm lint`、`pnpm typecheck` 全部通过。

### 2026-10-31 Project MCP recommendation provider handoff

- BFF child `1301269` 将 `PROJECT_MCP_RECOMMENDATIONS_PROVIDER` 从 `McpModule` 注入 `LegacyRoutesRuntime`，并通过 `BffCompositionOptions.projectMcpRecommendationsProvider` 传给 raw server。
- recommendation route 优先使用 `composition.projectMcpRecommendationsProvider`；`projectMcpRecommendationsProvider(BffBusinessStore)` 仅保留 raw/test fallback。MCP middleware/provider 已有独立 owner admission 与 client lifecycle。
- 验证：Nest runtime/feature architecture 20/20、MCP recommendation/publication focused 60/60、`pnpm build`、`pnpm lint`、`pnpm typecheck` 全部通过。

### 2026-10-31 Skill download/specification provider handoff

- BFF child `c8c3259` 将 `SKILL_EXACT_DOWNLOAD_SOURCE` 与 `SKILL_SPECIFICATION_SOURCE` 从 `SkillsModule` 注入 `LegacyRoutesRuntime`，并通过 `BffCompositionOptions` 传给 raw composition。
- exact Skill download 与 specification route 在生产 transitional chain 上优先使用 feature provider；`BffBusinessStore.skillShares`/usage 只保留 raw/test fallback，避免新增第二份业务实现。
- 验证：Nest runtime/feature architecture 20/20、Skill download/share/specification focused 60/60、`pnpm build`、`pnpm lint`、`pnpm typecheck` 全部通过。

### 2026-10-31 Migrated Chat path LegacyRoutes bypass

- BFF child `630efbf` adds `isMigratedChatRoute` coverage to `LegacyRoutesMiddleware`; public share, archive/shared tasks, direct Chat GET reads, feedback, regeneration and move now call `next()` without entering `LegacyRoutesRuntime`.
- Negative tests prove that Chat POST messages, events, title/delete/share and project-scoped reads remain on the transitional dispatcher until their own feature bundle is implemented.
- 验证：LegacyRoutes bypass 2/2、Nest runtime/feature architecture 20/20、Chat/feedback/regeneration focused 34/34、`pnpm lint`、`pnpm typecheck`、`pnpm build` 全部通过。

### 2026-10-31 Direct Chat mutation cutover

- BFF child `3961450` adds `CHAT_IDEMPOTENCY` and `handleChatMutationRequest` for direct no-`project_ref` PATCH title, DELETE session, and POST/DELETE share. It reuses `authorizeChatRequest`, `liveChatBusiness`, canonical mutation fingerprints, PostgreSQL receipts and process-local replay state.
- Negative coverage keeps project-scoped mutations, Chat POST messages, and events in the transitional dispatcher; raw `createBffServer` behavior is unchanged.
- 验证：direct Chat mutation 1/1、LegacyRoutes bypass 2/2、Nest runtime/feature architecture 20/20、BFF mock contract 25/25、`pnpm lint`、`pnpm typecheck`、`pnpm build` 全部通过。

### 2026-10-31 Direct Chat events cutover

- BFF child `76b9402` adds `AguiModule` providers for `AgUiProjectionService`, `PostgresAgUiConsumerRepository`, `AgUiSessionRuntime` and the source-projection active gate. `ChatModule` now handles direct no-`project_ref` `/v1/sessions/:id/events` through `liveAgentSession` and bypasses LegacyRoutes.
- Project-scoped events, Chat POST messages, and the LegacyRoutes projector worker remain transitional; this slice does not claim full Agent/AG-UI ownership deletion.
- 验证：本轮选定 AG-UI replay/runtime/SSE tests 全部通过、LegacyRoutes bypass 2/2、Nest runtime/feature architecture 20/20、BFF architecture 34/34、`pnpm lint`、`pnpm typecheck`、`pnpm build` 全部通过。

### 2026-10-31 Project-scoped Chat owner sharing

- BFF child `ff14c86` extracts `ProjectAccessModule` as the sole `PROJECT_SERVICE`/`PROJECT_SKILL_SELECTION_PROVIDER` owner and imports it into both `ProjectsModule` and `ChatModule`.
- Chat title/delete/share mutations and AG-UI events now accept `project_ref`, perform the existing Chat authorization/project owner recheck, and bypass LegacyRoutes without duplicating ProjectService or Repository ownership.
- 验证：project-scoped Chat mutation focused 1/1、LegacyRoutes bypass 2/2、Nest runtime/feature architecture 20/20、`pnpm lint`、`pnpm typecheck`、`pnpm build` 全部通过。

### 2026-10-31 Chat POST cutover

- BFF child `ff14c86` moves `POST /v1/sessions/:id/messages` into `ChatModule` and extracts `SkillInstallationAccessModule` as the shared installation client owner for Skills/Projects/Chat.
- The adapter preserves ChatTurn outbox commit, Project owner recheck, Skill installation qualification, idempotency receipt/replay, cancellation and canonical response semantics; LegacyRoutes no longer receives the Chat message POST.
- 验证：Chat message POST 1/1、BFF mock contract 25/25、LegacyRoutes bypass 3/3、Nest runtime/feature architecture 20/20、`pnpm lint`、`pnpm typecheck`、`pnpm build` 全部通过。

### 2026-10-31 Agent run-control cutover

- BFF child `a5b94c0` moves `POST /v1/sessions/:id/runs/:run/control` into `AgentRunsModule`. The feature adapter preserves Chat authorization, Project scope, durable idempotency, Agent receipt validation, queued-cancel startup bridge and cancellation budgets through `liveAgentSession`.
- LegacyRoutes no longer receives run-control POST; Agent dispatch worker lifecycle and remaining session/run paths remain transitional.
- 验证：Nest runtime/feature architecture 20/20、BFF architecture 34/34、LegacyRoutes bypass coverage、`pnpm lint`、`pnpm typecheck`、`pnpm build` 全部通过。

### 2026-11-01 C-4 validation cleanup

- Root `scripts/dev/serve_local_login.py` fixed the port-guard default capture; `test_serve_local_login.py` is now 61/61 and the full `python3 -m pytest scripts/tests` run is 1845 passed / 3 skipped / 1 environment failure.
- The remaining failure is `test_w2_bff_storage_smoke.py::test_exact_object_cleanup_and_database_nonadoption`, blocked by missing `@aws-sdk/client-s3` in the local Storage dependency graph. No test was weakened and no C-4 gate is marked green; install/lockfile ownership remains with the Storage owner.
