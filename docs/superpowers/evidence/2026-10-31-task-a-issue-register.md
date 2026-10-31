# Task A 问题台账、目标与闭环规则（2026-10-31）

## 1. 文档定位与对齐关系

本台账把此前 Task A 的设计、盘点、执行计划和当前实现证据合并成一份可执行的事实表。它不替代既有裁决：

- 总设计：[Task A 清理与重构技术方案](../specs/2026-10-30-task-a-cleanup-refactor-design.md)
- 只读盘点：[Task A 清理与重构清单](../specs/2026-10-30-task-a-cleanup-inventory.md)
- 原执行顺序：[Task A 清理与重构执行计划](../plans/2026-10-30-task-a-cleanup-refactor-execution.md)
- 当前收敛方案：[C-1.3～C-4 收敛实施方案](../plans/2026-10-31-task-a-c1-c3-convergence.md)
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

本次继续推进后的精确停写 pins：BFF `fb14159`、IAM `e1f537b02cb326cfb3751316b1591fa82313f70a`、App `9cde5640`；BFF 已将 Health、IAM relay、`GET /v1/me`、项目集合/详情/revisions/deletion-status/rename/delete/resource-list/resource-delete、public share projection、`GET /v1/connector.list`、MCP provider/package admin、browser project publication、App skill-bindings、Skill specification reads、全部 Skill package inspection 与 exact Skill download POST source/middleware 移入 feature middleware/provider，并新增 `BffBusinessStore.projectService`、`chatService`、`chatTurnService` 命名 owner seams、`SKILL_EXACT_DOWNLOAD_SOURCE`/`PROJECT_EXACT_DOWNLOAD_SOURCE` feature seams；Root topology PASS，最新 exact-download HTTP/policy/unit 22/22、connector-list HTTP 5/5、MCP provider/package admin HTTP 12/12、MCP project publication HTTP 27/27、App skill-bindings/Open App management 12/12、Skill specification contract/focused 149/149、package inspection unit 47/47（4 个环境 skip），BFF mock contract 25/25，Nest architecture 17/17，BFF architecture 34/34。

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
| TA-C3-02 | `PostgresBffRepositories` 是服务定位器，`BffApplicationServices` 是全局聚合器。 | 组合根无法表达真实依赖，Repository/Service 无法按 owner 审计。 | BFF `fd27d8d` 删除 `BffBusinessStore`/`PostgresBffRepositories` 上重复的 `chatService`、`projectService` 字段，runtime 统一从 `services.chat/projects` 读取；复杂事务/CAS/lease/outbox/owner boundary 继续迁入具名 feature-local provider。 | 进行中 |
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
- [x] Project resource-list provider 使用既有 `ProjectService.find` + `StorageUploadClient` owner seam；未新增资源 Repository、Storage transport 或 global store reader。
- [x] Project resource-read provider 使用窄 `ProjectResourceProjectReader.find` + 既有 `ProjectResourceAccessClient`/verified spool owner seam；未新增资源 Repository、Storage transport 或 global store reader。
- [x] Project resource-upload provider 使用窄 Project reader + `PostgresIdempotencyRepository` + 既有 Storage upload owner seam；未新增资源 Repository、Storage transport 或第二 receipt owner。
- [x] ScheduledTask read provider seam 已接入 `SCHEDULED_TASK_READ_SERVICE`，`ScheduledTasksModule` 通过唯一 `BFF_DATABASE` 构造 `PostgresScheduledTaskRepository` + Scheduler state reader；raw test composition 保持 `routeHandler` 旁路，避免改变 mutation fixture。
- [x] AgentRuns reader provider seam 已接入 `AGENT_RUNS_READER`，`AgentRunsModule` 通过唯一 `BFF_DATABASE` 构造 `PostgresAgentDispatchOutboxRepository`，同时提供 submitted-run 与 project-binding reader；不复制 outbox/SQL owner。
- [x] Run display provider seam 已接入 `RUN_DISPLAY_PROVIDER`，由 `AGENT_RUNS_READER` 与 `CHAT_SERVICE` 组合；ChatModule 不再反向依赖 AgentRunsModule，消除循环 module graph。
- [x] Project skill-selection provider 已接入 `PROJECT_SKILL_SELECTION_PROVIDER` 与 `PROJECT_SKILL_INSTALLATION_CLIENT`；只暴露 ProjectService 窄读写与 Idempotency receipt，未复制 Project Repository 或第二 CAS owner。
- [x] Project MCP recommendations provider 已接入 `McpModule` 的 `PROJECT_MCP_RECOMMENDATIONS_PROVIDER`、`MCP_AUTHORIZATION` 与 candidate clients；保留 owner candidate validation、MCP read admission、CAS 和 client shutdown，不引入 global store reader。
- [x] Connector list（`GET /v1/connector.list`）已由 `McpModule` 的 `MCP_PERSONAL_CLIENT`/`ConnectorListMiddleware` 接管；入口在 native middleware 先完成 session 与 MCP read admission，再复用原 projection/分页/owner read，旧 dispatcher 分支已删除，保留 request-id、no-store、输入闭集、分页循环和 owner 缺失/拒绝错误语义（`418021f`）。
- [x] MCP provider/package admin（`/v1/admin/mcp/providers/**`、`/v1/admin/mcp/packages/**`）已由 `McpModule` 的 `MCP_PROVIDER_ADMIN_CLIENT`/`MCP_PACKAGE_ADMIN_CLIENT`/`McpAdminMiddleware` 接管；旧 dispatcher 分支删除，复用现有 catalog admission、platform-admin qualification、idempotency/body/deadline/cancellation、owner error projection 与 client shutdown（`b178828`）。
- [x] MCP project publication（`/browser/v1/mcp/**` project publication/pin/receipt）已由 `McpModule` 的 `MCP_PROJECT_PUBLICATION_CLIENT`/`McpProjectPublicationMiddleware` 接管；native adapter 保留 project scope recheck、MCP read/manage admission、receipt/CAS、原始 command digest、取消与 owner result validation，旧 dispatcher 分支删除（`9adb097`）。
- [x] App skill-bindings（`/v1/admin/open-apps/:app_id/skill-bindings[/:series_id]`）已由 `SkillsModule` 的 `APP_SKILL_BINDING_CLIENT`/`OPEN_APP_MANAGEMENT_ADMISSION`/`SkillsMiddleware` 接管；fresh operator registration、exact app/tenant binding、独立 catalog/projection credentials、CAS/idempotency 与 owner response validation 保持不变，旧 dispatcher 分支删除（`49511ae`）。
- [x] Skill specification reads（`/v1/skill.list`、`/skill.v1.SkillOptionalService/*`、`/skill.v1.SkillService/DownloadSkill`）已由 `SkillsModule` 的 `SKILL_LIST_ADMISSION`/`SKILL_SPECIFICATION_SOURCE`/`SKILL_DOWNLOAD_HANDLES`/`SkillsMiddleware` 接管；public identity recheck、private session admission、exact source projection、opaque download handle 与 response/error contract 保持不变，旧 dispatcher 分支删除（`dff1787`）。
- [x] 全部 Skill package inspection（`GET /v1/self/skills/:id/package`、`GET /v1/skill-installations/:id/package`、`GET /v1/projects/:id/skill-installations/:installation_id/package`）已由 SkillsModule/ProjectsModule 的 `SKILL_PACKAGE_INSPECTION_CLIENT` middleware 接管；strict path/query/header validation、current admission、exact project scope、owner projection 与 bounded package response 保持不变，旧 dispatcher 分支删除（`b610c92`）。
- [x] Exact Skill download POST (`/browser/v1/skill-installations/:id/download`、`/browser/v1/skills/:id/download`、`/browser/v1/skill-shares/:id/download`、`/browser/v1/projects/:id/skill-installations/:id/download`) 已由 SkillsModule/ProjectsModule 的 exact source 与 native middleware 接管；installation/managed/share/project installation 均保留 source/revision 资格重读、项目 scope recheck、opaque handle 与 verified byte binding，`ExactSkillDownloadService` 支持 project-only feature source；raw `handleBffRequest` fallback 与 GET handle route 仍待下一删除门（`6633306`）。
- [x] C-3 Chat cleanup 已在 `BffBusinessStore` 暴露 `chatService`/`chatTurnService`，Postgres composition 以同一既有 `BffApplicationServices` 实例填充 named seam；runtime、Chat authorization/live Chat、message regeneration 与 run-display raw adapter 优先读取 named seam，保留 raw/test fallback，不新增 Repository/Service/SQL owner（`fb14159`）。
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
- [x] C-3 ScheduledTask cleanup 已暴露命名的 `BffBusinessStore.scheduledTaskService` seam，并切换 runtime snapshot、scheduler callback 与 live-bff authorization/create/update/delete/retry 读取；兼容 fallback 保留至 aggregate zero-consumer proof。
- [x] C-3 Project cleanup 已暴露命名的 `BffBusinessStore.projectService` seam，并切换 Project/Chat authorization、resource、Skill-selection、MCP recommendation 与 live-bff project consumers；兼容 `services.projects` fallback 保留至 aggregate zero-consumer proof（`541c1e1`）。
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

> 当前 C-3 反向消费者复核（BFF `541c1e1`）：`BffApplicationServices` 仅剩 `projects`、`scheduledTasks`、`chat`、`chatTurns` 四个聚合字段；生产源码仍有 33 处 `services.(projects|scheduledTasks|chat|chatTurns)` 文本引用，其中 Project runtime/Project/Chat authorization/live-bff paths 已先优先读取 `BffBusinessStore.projectService`，ScheduledTask runtime/scheduler/live-bff mutation paths 已先优先读取 `BffBusinessStore.scheduledTaskService`，GitHub/AI import 与 Skill share 已改为 SkillsModule 的窄 receipt/association/specification providers，兼容 fallback 与 Postgres alias 仍保留至全部消费者切换。其余引用主要集中在 Projects、Chat/Agent message paths、exact-download/project fallback。LegacyRoutes/createBffComposition/handleBffRequest 仍有 24 处生产引用。下一批应按 owner seam 继续迁移剩余 33 个文本引用，再删除剩余 service aggregate 与 LegacyRoutes；本数字是本 checkout 的当前证据，不将迁移意图计为完成。


> 全量验证更新：最新 `pnpm test` 已在停写工作树上运行到终态：2312 tests / 2295 pass / 15 fail / 2 skip；native/admin/Skill specification focused paths均通过，但仍有 Artifact/Personal Storage Product HTTP、Project exact-download、Admin Web credential fixture、以及部分 user-admission anonymous Share fixture 失败。该结果确认当前全量门禁仍非绿，不能作为 C-4 通过；失败项继续按 owner baseline 单列，不删除断言、不放宽测试、不提前打开 A gate。

当前已完成问题整理、Goal/TODO 冻结、技术方案和 C-1.3 App native identity 第一闭环（adapter、SSR admission、session probe、BFF `/v1/me` proof），并完成 account profile read/update、account sessions、Team 的 native owner transport；profile-read contract/artifact/consumer cutover 已由 Root `c7af342` 固定。App native session read、issuer signout handoff 与 browser signout client 已脱离旧 RP runtime dependency。C-2 已将 IAM relay、current-user `/v1/me`、项目集合 `GET /v1/projects`、详情、instruction-revisions、deletion-status、rename、delete、resource-list、resource-read/download、resource-upload、resource-delete、skill-selection、MCP recommendations、public share projection 分别收敛到 feature middleware/provider；旧 dispatcher 仍保留其余 route families。C-3 personalization、Chat、Project pin、Project core-read（deletion-status/rename）、ScheduledTask read、AgentRuns reader/provider、Project resource receipt/provider、Project skill-selection 与 MCP recommendations provider seam 已建立；BFF 最新切片验证为 nest architecture 14/14、architecture 34/34、MCP focused 15/15，旧全量 baseline 仍单列。仍未完成的是完整 sign-in/tenant-switch/permission/revocation UI 收据、LegacyRoutes 全量退出、剩余 global Repository/Service/Port 收敛、App typecheck `onReconnect` baseline 与 C-4 跨 owner 停写后串行门禁；A-01/A-02/A-07 继续停写。下一步按 inventory 迁移 project skill-installations 与剩余 Chat/Agent/Scheduled/Skills/MCP route bundle，并继续拆 global provider；每个 bundle 完成 focused、architecture 与串行门禁后再扩展下一批。

