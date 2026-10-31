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
- ScheduledTask current-read route cutover：[Scheduled read evidence](2026-10-31-task-a-scheduled-read-cutover.md)
- AgentRuns internal route cutover：[AgentRuns evidence](2026-10-31-task-a-agent-runs-cutover.md)
- C-4 contract inverse 与全量复验：[C-4 evidence](2026-10-31-task-a-c4-contract-inverse.md)
- IAM native profile receipt：[native receipt evidence](2026-10-31-task-a-c1-3-native-receipt.md)
- 产品任务边界：[Task A workspace handoff](../../handoffs/2026-10-30-task-a-workspace-execution.md)

当前停写代码基线为 `f17bf828`；其后 Root `18b59a43`、`17d49259` 为文档同步，Root `f4202a5e` 固定 IAM profile-read owner，`c7af342b` 固定 BFF/App profile-read consumers。App 子仓 `dde9fa6`、BFF 子仓 `3ca1525`（含 `b3a9ab5`、`4e794ce`、`2ce0296`、`2df4bcc`、`caccdc9`、`a677cd2`、`6874034`、`ef1c53b`、`6de89c7`、`108a0bc`、`4667506`、`96806f4`、`39d5481`、`7f61218`、`2a504c0`）、IAM 子仓 `d461b82`（基于 `f4f1585`）已完成 profile-read 与 root-scoped issuer cookie cutover；BFF account native bundle（profile/sessions/team/me/personalization）、System runtime-manifest、Chat archive/share/feedback、Projects pin、ScheduledTask current-read、Agent internal admission/binding 与 run-display bundle 已由 feature middleware/adapter 接管，旧 `server.ts` 对应业务分支已移除；personalization、Chat、Project pin、ScheduledTask read 与 AgentRuns reader/provider 已从 global route dispatch 解耦，raw-server seam 使用显式 provider，partial test composition 仍保持兼容。native route HTTP fixtures 已切换到 build output，78 项 feedback/run-display/project-binding focused tests 全部通过；C-4 contract inverse 与 IAM 0.18/profile-read governance 已收敛，BFF 串行全量为 2309 tests / 2307 pass / 0 fail / 2 skip。IAM native profile read/update 与撤权集成 fixture 已在本地 PostgreSQL/Redis 上串行 12/12 通过；Root real IAM→BFF session smoke 7/7 已在 cookie cutover 后复验通过，OIDC smoke 42/42 仅为 cutover 前历史证据，需按新 cookie policy 重跑；真实跨 App→BFF→IAM native sign-in/sign-out/tenant-switch/revocation 旅程仍未形成。本台账只整理问题、目标、约束、TODO 和验收，不把 A-01/A-02/A-07 提前写入实现。

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
| TA-C2-01 | `src/modules/legacy-routes/legacy-routes.runtime.ts` 仍创建 `createBffComposition()` 并委派 `handleBffRequest`；剩余业务 path 仍在 `src/bootstrap/server.ts`。 | 业务事实仍由旧 dispatcher 持有，Nest feature graph 不是唯一运行边界。 | C-2/C-3 inventory 已冻结入口/route family；Account native bundle、System runtime-manifest、Chat archive/share/feedback、Projects pin、ScheduledTask current-read、Agent internal admission/binding 与 run-display 已切到 feature middleware/adapter，后续每条 path 迁移必须同时改 `server.ts`、feature graph 和 negative test。 | 盘点完成，Account/System/Chat/Projects/Scheduled/Agent route bundles 已迁移 |
| TA-C2-02 | 旧 `bootstrap/server.ts`、`bootstrap/runtime.ts` 与 global composition 路径仍有生产引用；`app.module.ts`、`main.ts`、shutdown provider 也在删除链上。 | 存在第二 composition root 和隐藏依赖。 | 先完成 feature provider cutover/import census，再删 dispatcher；反向搜索 `LegacyRoutes*`、`createBffComposition`、`handleBffRequest`、`createBffServer`。 | 未完成 |
| TA-C2-03 | 已有 feature module 仍有部分只声明 graph/ownership 的空壳风险。 | 机械建模块会增加无意义代码，掩盖未迁移行为。 | 每个 module 至少承接真实 route/provider/owner client；无 route、无 provider、无测试证据的模块不保留。 | 进行中 |

### 3.3 C-3 Repository / Service / Port

| ID | 当前问题 | 影响 | 闭环证据 | 状态 |
|---|---|---|---|---|
| TA-C3-01 | `BffBusinessStore` 同时承载 Chat、Project、Agent、Scheduler、AG-UI、Artifact 等事实。 | 巨型 Port 隐藏 owner 和依赖，导致运行时缺失分支。 | C-2/C-3 inventory 已完成字段/owner 候选；按 slice 拆 provider，旧 global Port 生产 import 为零。 | 盘点完成，迁移未完成 |
| TA-C3-02 | `PostgresBffRepositories` 是服务定位器，`BffApplicationServices` 是全局聚合器。 | 组合根无法表达真实依赖，Repository/Service 无法按 owner 审计。 | 复杂事务/CAS/lease/outbox/owner boundary 迁入具名 feature-local provider；personalization 已先脱离聚合器，剩余字段继续按 feature 迁移。 | 进行中 |
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
| TA-BASELINE-05 | BFF 停写后串行 `pnpm test` 已复验为 2309 tests / 2307 pass / 0 fail / 2 skip；本轮补齐 v28.18 Account profile inverse、IAM 0.18/profile-read governance 与 build-output fixture，contract inverse 不再漂移；message feedback/run display/project binding focused 为 78/78。 | C-4 BFF 全量门已收敛；2 个 skip 仍是受资源门禁保护的真实 PostgreSQL 条件测试，不计为通过，详见 C-4 evidence。 |

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
- [ ] 每迁移一批，从 `LegacyRoutesRuntime` 删除具体 path，并验证 adapter 不再接收该 path。
- [ ] route census 清零后删除 `legacy-routes.runtime.ts`、module、middleware、旧 dispatcher。
- [ ] 验证唯一 Nest listener 和唯一 `AppModule` composition root。

### G3：Repository / Service / Port 收敛

- [x] 为 `BffBusinessStore`、`BffApplicationServices`、`PostgresBffRepositories` 建立字段/方法/消费者清单。
- [x] 为 `src/application/ports/**` 逐项写 keep/move/merge/delete 及事务、锁、CAS、lease、outbox、owner evidence。
- [x] 首个 C-3 slice 已将 `PersonalizationProvider` 从 `BffApplicationServices` 移到 `BffBusinessStore.personalizationProvider` 的显式 raw-server seam；CAS/事务实现未复制。
- [x] Chat archive/share 首个 provider seam 已接入 `CHAT_SERVICE`，`ChatModule` 通过唯一 `BFF_DATABASE` 构造 `ChatApplicationService`；旧 `businessStore.services.chat` 仅作为 transitional raw-server fallback，待全部 Chat route cutover 后删除。
- [x] Project pin provider seam 已接入 `PROJECT_SERVICE`，`ProjectsModule` 通过唯一 `BFF_DATABASE` 构造 `ProjectService`；旧 `businessStore.services.projects` 仅作为 transitional raw-server fallback，待剩余 Project route cutover 后删除。
- [x] ScheduledTask read provider seam 已接入 `SCHEDULED_TASK_READ_SERVICE`，`ScheduledTasksModule` 通过唯一 `BFF_DATABASE` 构造 `PostgresScheduledTaskRepository` + Scheduler state reader；raw test composition 保持 `routeHandler` 旁路，避免改变 mutation fixture。
- [x] AgentRuns reader provider seam 已接入 `AGENT_RUNS_READER`，`AgentRunsModule` 通过唯一 `BFF_DATABASE` 构造 `PostgresAgentDispatchOutboxRepository`，同时提供 submitted-run 与 project-binding reader；不复制 outbox/SQL owner。
- [x] Run display provider seam 已接入 `RUN_DISPLAY_PROVIDER`，由 `AGENT_RUNS_READER` 与 `CHAT_SERVICE` 组合；ChatModule 不再反向依赖 AgentRunsModule，消除循环 module graph。
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

当前已完成问题整理、Goal/TODO 冻结、技术方案和 C-1.3 App native identity 第一闭环（adapter、SSR admission、session probe、BFF `/v1/me` proof），并完成 account profile read/update、account sessions、Team 的 native owner transport；profile-read contract/artifact/consumer cutover 已由 Root `c7af342b` 固定。新增真实 HTTPS native receipt 已验证 `/api/auth/session`、`/api/session/projects`、signout 401 与资源清理。C-2 Account/System/Chat/Projects/Scheduled/Agent route bundles 已分别由 BFF `96806f4`、`108a0bc`、`ef1c53b`、`6874034`、`a677cd2`、`caccdc9`、`2df4bcc` 切到 feature middleware/adapter，C-3 personalization、Chat、Project pin、ScheduledTask read 与 AgentRuns reader/provider seam 已建立，并完成 BFF build/typecheck/format/lint、architecture、profile/session/team/me/runtime-manifest/archive/share/project-pin/scheduled mutation/model-admission/bff mock focused 验证。仍未完成的是完整 sign-in/tenant-switch/permission/revocation UI 收据、LegacyRoutes 全量退出、剩余 global Repository/Service/Port 收敛和 C-4 停写后串行门禁；A-01/A-02/A-07 继续停写。下一步按 inventory 迁移剩余 Project/Chat/Agent/Scheduled/Skills/MCP route bundle，并继续拆 global provider；每个 bundle 完成 focused、package explicit-file-list、architecture 与串行门禁后再扩展下一批。

