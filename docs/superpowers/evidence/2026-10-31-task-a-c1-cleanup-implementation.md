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
- App C-1 focused Vitest：7 files / 91 tests pass；ESLint focused pass；既有全仓 typecheck 的 `app-frame-main-surface.tsx:onReconnect` 错误仍为基线。
- Agent display/contract/http focused pytest：24 pass；ruff touched-file check pass。
- Root `python3 scripts/verify-repository-topology.py`：PASS。
- Root `git diff --check`：通过。

### 仍未越过的停写边界

C-1 compatibility cleanup、C-2 foundation/feature graph、C-3 personalization slice 和 C-4 default contract-pin/test gate 已交付；但 C-1.3 first-party native-session runtime cutover、LegacyRoutes 全量替换/旧 dispatcher 删除、其余 global Repository/Service/Port 拆分尚未完成。因此 A-01/A-02/A-07 继续保持未启动，不能把当前证据标记为 C-1～C-4 完整通过。

C-1.3 native-session runtime/consumer 已交付第一闭环，但尚未宣称全量 auth cleanup：

- IAM child `2fbb96a`：新增 `POST /internal/v1/native-session-admission/verify` controller/service/schema；独立 `kokoro-bff/session_admission` direct credential；严格 Cookie/Origin/Accept/body/duplicate-header 校验；fresh Better Auth session、active tenant、membership、role permissions 查询；native error closed set；生成 `contract/openapi/iam.internal.v1.json`。
- BFF child `799b9e4`：新增受限 credential reader、native transport/client、Cookie allowlist、Origin 校验和 AccountModule/runtime wiring；配置 `KOKORO_BFF_IAM_SESSION_ADMISSION_CREDENTIAL_FILE` 与 `KOKORO_IAM_WEB_ORIGIN`。启用两项配置时用户准入不再发送浏览器 bearer；旧 bearer transport 仅保留给独立 owner authorization consumers，native 结果对这些未迁移调用以空 bearer fail-closed。
- Root integration `77921443`：同时 pin IAM `2fbb96a` 与 BFF `799b9e4`。

本次主仓复核：BFF format/lint/typecheck/build、native tests 3/3、Nest architecture 7/7、architecture 33/33、全量 `pnpm test` 2301 pass / 2 skip / 0 fail；IAM format/lint/typecheck/contract:check、unit 95 files / 1403 tests pass。全量验证已在 worker 停写后重跑，dist 缺失的并行竞争结果不计入验收。

仍未完成：App 同源 adapter/旧 first-party RP 删除、BFF LegacyRoutes 全量替换/旧 dispatcher 删除，以及剩余 global Repository/Service/Port 收敛。故 A-01/A-02/A-07 继续保持未启动，C-1～C-4 不标记为全部通过。
