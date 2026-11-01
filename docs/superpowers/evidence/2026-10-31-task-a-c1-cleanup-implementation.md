# Task A C-1 清理实施证据（2026-10-31）

## 范围

本阶段只执行已确认的 clean-slate 清理，不开始 BFF NestJS 收敛、Repository 重写或业务契约改造。

- BFF：删除全部 schema-evolution CLI、共享 evolution runner 与对应演进 integration tests；package 入口、architecture oracle、反馈/Project Pin 当前测试同步收敛。保留唯一 fresh-only `scripts/apply-schema.mjs` 与 canonical catalog 校验。
- App：删除 `cancelledRuns` HMR 迁移、Conversation hash URL 解析/规范化、无序 snapshot activity 的 synthetic fallback、legacy final proof folding；保留 canonical `runTerminalsById`、ordered public positions、durable final identity、localDraft 与 frozen execution facts。
- Agent：删除基于旧 `mcp/tools.py` source digest 的 `legacy_failed` 展示推断；保留 frozen recipe authority 和当前 journal/activity failure evidence。

## 子仓提交

- `apps/kokoro-bff` `bb4943f` — `refactor(bff): remove schema evolution compatibility`
- `apps/kokoro-app` `4da1c1b` — `refactor(app): remove retired conversation compatibility`
- `apps/kokoro-agent` `c761fad` — `refactor(agent): remove legacy display failure inference`

## 验证

### BFF

- `pnpm typecheck`：通过
- `pnpm build`：通过
- `pnpm lint`：通过
- `pnpm format:check`：通过
- `pnpm test`：2301 pass / 2 skip / 0 fail
- 真实 PostgreSQL 条件测试按资源门禁跳过；没有把 skip 记为通过

### App

- `pnpm lint`：通过
- 受影响 Vitest：6 files / 72 tests pass
- `pnpm typecheck`：仍有基线错误 `src/components/blocks/app-frame/app-frame-main-surface.tsx` 的 `onReconnect` 属性类型不匹配；该错误不由本 C-1 修改引入

### Agent

- `uv run ruff check src/kokoro_agent/application/run_display.py src/kokoro_agent/infrastructure/checkpoint_display.py tests/unit/chat/test_historical_mcp_display.py`：通过
- 受影响 display/contract/http 单测：130 pass

### App native runtime slice（子仓 `4c41104d`）

- `tests/ui/use-session-state.test.tsx`：79 pass；覆盖 native projection 直接 admission，确认不发 Product CSRF/refresh POST。
- archived/shared/session archive/share adapters 与 sign-in failure recovery focused：68 pass；验证 native admission 迁移不改变 legacy bearer fallback、最终 admission recheck、取消和错误闭集。
- `tests/server/product-bff.test.ts`、`tests/ui/product-auth-client.test.ts` 与相关 session tests：focused pass。
- touched-file ESLint：pass。
- `pnpm typecheck`：仍为既有 `src/components/blocks/app-frame/app-frame-main-surface.tsx:onReconnect` 类型错误。

### C-1.3 Native owner cutover slice（2026-10-31）

本轮只推进仍依赖 bearer 的三组 owner surface，不删除旧 Product Session/RP：

- IAM `108beedf`（runtime `6b26433`）：在现有 `InternalAuthGuard` 中增加显式 native owner 分支。BFF direct `session_admission` credential、allowlisted Cookie、固定 Origin 和 request id 通过后，IAM fresh-recheck issuer session、active tenant、membership、session id；account profile/session 使用 native 标记跳过 OAuth grant lookup，但保留 Product tenant、session、CAS、事务、Audit 和错误边界；Team 继续由 owner snapshot 复核角色权限。既有 bearer 分支保持不变。
- BFF `65cf2082`：`ownerSessionAuth` 只在 account profile/sessions/team 路由上把原生 allowlisted Cookie + 固定 Origin + fresh direct credential 传给 IAM；legacy bearer 仍只在未迁移 surface 使用，native 请求不制造空 bearer。IAM owner clients 的响应闭集、预算、取消、错误映射保持。
- App `4c41104d`：account profile update、account sessions、Team adapter 改用 `admittedProductSession` 与同一 native proof；native synthetic TTL 不参与身份快照比较，仍以每次 BFF admission 复核 subject/session/expiry。旧无 native cookie 的 Product Session fallback 保留在迁移边界内。

### C-1.3 focused verification

- IAM：`pnpm typecheck`、`pnpm lint`、`vitest run test/unit/internal-auth.guard.test.ts test/unit/account-profile/account-profile-service.test.ts test/unit/account-sessions/account-session-cursor.test.ts`，56 pass。
- BFF：`pnpm typecheck`、`pnpm lint`、`pnpm build`，以及 user-admission/account-profile/account-sessions/team focused tests，96 pass。
- App：`tests/server/account-profile-update.test.ts`、`tests/server/account-sessions.test.ts`、`tests/system/team-product-route.test.ts`，116 pass；touched route/native tests保持通过。

本 slice 尚未覆盖 App profile read 的 userinfo owner contract、sign-in/sign-out/tenant-switch/revocation 的真实旅程收据、旧 RP/Product Session 删除，也未开始 LegacyRoutes/global composition/Repository/Service/Port 清理；A-01/A-02/A-07 继续停写。

## 停止线

C-1 兼容清理的主仓复核补充（2026-10-31）：

- App 受影响 Vitest：7 files / 91 tests pass；受影响 ESLint：pass。
- Agent display/contract/http focused pytest：24 pass；ruff touched-file check：pass。
- BFF Nest foundation/feature graph gates：4 pass；typecheck/build/lint/format：pass。
- BFF `pnpm test` 曾在与并行 build 竞争时出现 dist 缺失、既有 contract fixture failures 和 pending tests；该结果不计为 C-1 全量通过，需在所有 BFF worker 停写后重跑。

C-1 旧兼容实现证据已固定；C-2 feature graph 已开始但 LegacyRoutes adapter、global composition 和大 Port 仍保留。C-3/C-4、C-1.3 auth cutover 未宣称完成。

## G0/C-2～C-4 复核（2026-10-31）

G0 设计门已由 reviewer 通过，IAM native-session artifact 已固定：

- `apps/kokoro-iam` `461a57ab486e1041d8d5c926103443e030f191fb`
- `contract/openapi/native-session-admission.v1.json`
- version `1.0.0`
- SHA-256 `5cf59df4b7bd9853edfd2eabb31afc236c0ec0db371f9737706fc129484fd83f`

BFF 收敛提交：

- `3f643ef`：Nest 唯一 runtime entry、AppModule、Config/Database/Redis/Lifecycle/Health/LegacyRoutes adapter。
- `cd4ffb1`：Account/Chat/AgentRuns/Projects/AG-UI/Skills/MCP/Billing/System/Music/ScheduledTasks canonical feature graph。
- `aacf1c5`：删除 global `PersonalizationRepository`，迁移为 AccountModule feature-local `PersonalizationProvider`/token。
- `a9bd12d`：刷新 Nest lockfile 后的八个 consumer manifest pin，并同步 R257 design path。

Root gitlink 已更新至 BFF `a9bd12da7b6ed0a8a128f4ee387a19ee15f49a17`；最新 Root integration commit 为 `3633bea2`。

### 新鲜验证

- BFF `pnpm format:check`：通过。
- BFF `pnpm lint`：通过。
- BFF `pnpm typecheck`：通过。
- BFF `pnpm build`：通过。
- BFF `pnpm test:architecture`：33/33 通过。
- BFF `pnpm test:nest-architecture`：4/4 通过。
- BFF contract governance / Platform / Storage focused gate：52/52 通过。
- BFF `pnpm test`：2301 pass / 2 skip / 0 fail；skip 为受资源门禁保护的真实 PostgreSQL 条件测试，未将 skip 计为通过。
- App native adapter/probe/adapters focused Vitest：8 files / 155 tests pass；ESLint focused pass；既有全仓 typecheck 的 `app-frame-main-surface.tsx:onReconnect` 错误仍为基线。
- Agent display/contract/http focused pytest：24 pass；ruff touched-file check pass。
- Root `python3 scripts/verify-repository-topology.py`：PASS。
- Root `git diff --check`：通过。

### 停写后 App 全量门禁复核（2026-10-31）

- `pnpm test`：362 files；6890 pass、2 skip、7 fail。失败集中在既有 process/activity UI 断言（`segment-process.test.tsx` 4、`process-activity-groups.test.tsx` 2）和 sign-out 页面文案契约 1；另有 stored-session fixture 因缺少 `KOKORO_TEST_REDIS_URL` 触发环境缺口。该结果不计为 App 全量通过，也不扩大 C-1.3 代码范围。
- native session focused/probe 测试保持通过；C-1.3 当前仍以 focused evidence 交付，待真实 IAM→BFF→App journey 收据和现有 App baseline 收敛后再关闭。

### 仍未越过的停写边界

C-1 compatibility cleanup、C-2 foundation/feature graph、C-3 personalization slice 和 C-4 default contract-pin/test gate 已交付；但 C-1.3 first-party native-session runtime cutover、LegacyRoutes 全量替换/旧 dispatcher 删除、其余 global Repository/Service/Port 拆分尚未完成。因此 A-01/A-02/A-07 继续保持未启动，不能把当前证据标记为 C-1～C-4 完整通过。

C-1.3 native-session runtime/consumer 已交付两段闭环（admission proof 与 account/Team owner proof），但尚未宣称全量 auth cleanup：

- IAM child `108beed`（runtime `6b26433`）：新增 `POST /internal/v1/native-session-admission/verify` controller/service/schema；并将 account profile/session 与 Team owner operations 接入显式 native proof 分支；独立 `kokoro-bff/session_admission` direct credential；严格 Cookie/Origin/Accept/body/duplicate-header 校验；fresh Better Auth session、active tenant、membership、role permissions 查询；native error closed set；生成 `contract/openapi/iam.internal.v1.json`。
- BFF child `65cf208`：新增受限 credential reader、native transport/client、Cookie allowlist、Origin 校验、AccountModule/runtime wiring 和 owner transport forwarding；配置 `KOKORO_BFF_IAM_SESSION_ADMISSION_CREDENTIAL_FILE` 与 `KOKORO_IAM_WEB_ORIGIN`。启用两项配置时用户准入不再发送浏览器 bearer；未迁移的独立 owner authorization consumers 仍保持 fail-closed。
- App child `d944ac3` + `f0ffd2d2` + `0bd1481c` + `de40f9c3` + `68813cd3`：为 `/api/session/*` 同源适配器增加 IAM native-session Cookie 投影；只转发 allowlisted IAM cookies、固定配置 Origin、request-id 与 web-bff service credential，过滤 Product/第三方 cookie，重复或空 native cookie fail-closed。`admittedProductSession` 在 native cookie 存在时改为通过 BFF `/v1/me` 获取当前 subject，并把 native cookie proof 传给后续 BFF owner calls，不再发送 bearer；App `/app` SSR shell 和 `/api/auth/session` probe 现在优先使用同一 native identity proof，native probe 不再发 Product CSRF/refresh POST，native sign-out 返回 IAM end-session relay；archived/shared task 与 session archive/share adapters 已切到同一 admission helper，sign-in failure recovery 也先检查 native proof，并有单测覆盖 native recovery redirect。当前仍保留 Product Session 作为无 native cookie 的过渡路径，account profile/sessions/team 等仍依赖 IAM bearer owner surface，尚未切换。
- Root integration `1c63b007`：同时 pin IAM `108beed`、BFF `65cf208` 与 App `4c41104d`。

本次主仓复核：BFF focused owner/native tests 96 pass，IAM focused native guard/account tests 56 pass，App account/profile/session/Team focused tests 116 pass；各自 typecheck/lint/build 通过。App 全仓 typecheck 仍仅有既有 `app-frame-main-surface.tsx:onReconnect` baseline。全量验证已在 worker 停写后重跑，dist 缺失的并行竞争结果不计入验收。

仍未完成：App 尚保留 account profile/sessions/team 等依赖 IAM bearer owner surface；旧 first-party RP/Product Session 删除、其余 App API route 切换、BFF LegacyRoutes 全量替换/旧 dispatcher 删除，以及剩余 global Repository/Service/Port 收敛仍在停写线之后。故 A-01/A-02/A-07 继续保持未启动，C-1～C-4 不标记为全部通过。

### Chat direct read cutover（2026-10-31）

BFF child `5659b1d` 将 direct/no-`project_ref` 的 Chat GET collection、session snapshot、message list、message parts 和 Run process reads 接入 `ChatModule`，同时在 Nest `ChatMiddleware` 与 raw `createBffServer` 注册 `handleChatBusinessReadRequest`。该 adapter 先执行 `authorizeUserRequest`，再执行 Chat owner recheck，最后复用 `liveChatBusiness` 的既有分页、cursor、read budget、取消、error envelope 和 request-id 语义；`ChatBusinessProvider` 让这些 reads 不再依赖全局 `BffBusinessStore`。Chat POST、events、project-scoped reads、AgentRuns/AG-UI 仍在下一 slice，LegacyRoutes/global composition 尚未删除。

验证：direct Chat read 2/2、BFF mock contract 25/25、Nest architecture 18/18、BFF architecture 34/34、`pnpm lint`、`pnpm typecheck`、`pnpm build`；停写后串行 `pnpm test` 为 2316 tests / 2299 pass / 15 fail / 2 skip，15 项失败仍为既有 Artifact/Personal Storage Product HTTP、Project exact-download、Admin Web credential fixture 与 anonymous Share fixture。

### Public Share provider handoff（2026-10-31）

BFF child `330e439` 将 `PublicShareApplicationService` 从隐式 `BffBusinessStore` 查找改为 `ChatModule` → `PUBLIC_SHARE_SERVICE` → `LegacyRoutesRuntime` → `BffCompositionOptions.publicShareService` 的显式链路。`GET /v1/shared/{shareId}` 已继续使用 `composition.publicShareService`，store 字段仅作为未迁移 raw/test composition fallback；本提交不宣称 LegacyRoutes 或 global composition 已删除。

验证：BFF build、lint、typecheck 通过；Nest runtime architecture 5/5；Skill share/exact-download focused 40/40。

### Scheduled current-read provider handoff（2026-10-31）

BFF child `46bb5ac` 将 `ScheduledTaskReadService` 从 transitional runtime 内部按 `BffBusinessStore.services.scheduledTasks` 组装，改为 `ScheduledTasksModule` → `SCHEDULED_TASK_READ_SERVICE` → `LegacyRoutesRuntime` → `BffCompositionOptions.scheduledTaskReader` 的显式链路。current-read route 继续复用 `composition.scheduledTaskReader`，mutation/callback/outbox 保持在未迁移清单中；本提交不宣称 ScheduledTasks 或 LegacyRoutes 完成删除。

验证：BFF build、lint、typecheck 通过；Nest runtime architecture 5/5；scheduler focused 38/38。

`814d3e6` 仅修正 Nest feature architecture 对 LegacyRoutes 扩展 imports 的精确断言，验证结果为 20/20；不改变运行时行为。
