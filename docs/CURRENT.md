# Root 当前状态

状态日期：2026-09-23。Root 使用 remote-name Git submodule；可复现组合由本仓 `.gitmodules` 和精确 gitlink 定义。架构决策见 [设计](superpowers/specs/2026-09-20-kokoro-backend-closure-design.md)，执行状态见 [`task.md`](task.md)，实际命令与资源证据见 [`progress.md`](progress.md)。本文件只列当前能力与缺口，不用子仓测试代替跨仓验收。

## 当前组合

| 路径 | 锁定的子仓 main commit |
| --- | --- |
| `apps/kokoro-app` | `c3d81bf16fc62cef59ab33f6cc61a6677a38383c` |
| `apps/kokoro-mori` | `ca76c2e12861a2e4a6af3049f6df8c34b417c158` |
| `apps/kokoro-bff` | `ddb462e6ab3a7270a3dab248ba7ee887b0ec9ba2` |
| `apps/kokoro-agent` | `741c928dfc11313a25064a905d77d4ad371f5534` |
| `apps/kokoro-iam` | `f240bd7d5f542bb152c7eb929074c96b6c290ea8` |
| `apps/kokoro-system` | `c0a76a3a7614bf46ea6e665e523f24261862436f` |
| `apps/kokoro-billing` | `63e0ab6e61b397f23f7ab71f5d6dc9df3d6de0fa` |
| `apps/kokoro-capability` | `9c88d0d934387b590bc74dae0179a587292e0253` |
| `apps/kokoro-storage` | `f80917e98a1cd1fe196ce10b0aba6f8f67fdf205` |
| `apps/kokoro-scheduler` | `975dee59616a1e0eda609aa69283401344900d83` |
| `libs/kokoro-web-shared` | `0c4e87ace01340aaa07bc57935f1d98b8e77af14` |

Web 正式路径是 `apps/kokoro-app`，不是 `apps/kokoro/`。当前正式能力仓仍叫 `kokoro-capability`，尚未原子切换成 `kokoro-platform`；Mori 和 web-shared 不是本轮后端 runtime owner。子仓的 tests 不迁入 Root；各子仓测试留在各自仓库。`scripts/tests/` 只覆盖 Root 治理脚本和组合 runner 自身的测试；跨仓验收入口在 `scripts/e2e/`，证据清单在 `verification/`。

## 已落地的 owner 能力

- IAM 已提供真实 Code+S256、session admission 与测试专用 OIDC host；既有 `6bc9b19…` 将 17 个 Prisma model 固定到 `kokoro_iam` schema，fresh installer 与 readiness 不再依赖 `public` 或整库空白。Root 独立 Node24 `pnpm verify` 704/704、串行真实 integration 183/183；旧并行 fixture 的全局临时库计数竞态仍待单独修，不是应用数据库并发限制。本次 `f240bd7…` 仅收敛 Team 三个当前tenant窄读端点的设计文档，运行代码/OpenAPI/SDK未实现。
- BFF 已提供个人私有 Conversation/Project/ScheduledTask 权限、IAM admission、固定 `/iam` 原生 relay、Capability/Scheduler generated consumer。既有 `a4dbc33…` 使用 `kokoro_bff` schema；`1d1f427…` 将 relay policy 来源机械 re-pin 至 IAM `f240bd7…`；`ddb462e…` 在固定 end-session GET 的内部转发改用有界原生HTTP，避免Node fetch自动`sec-fetch-mode:cors`使IAM拒绝浏览器确认页。独立审查0 P0/P1/P2，Root Node22 `pnpm check` 标准255 pass/1既有skip、lint/typecheck/contract/build通过。没有 Team Product API。
- Web 已实现同源 issuer、三页交互及 Auth.js Code+S256/state/nonce 回调。`1ba0498…` 新增 HttpOnly Product Session、Redis 加密当前 refresh/双阶段 CAS、受控单次 refresh 与 active-current revoke；无 ID token hint 的 IAM logout 由浏览器 GET 确认页、签名窄 Path cookie 和 POST confirm 完成，未确认前只报告 pending。首次真实 HTTPS smoke 揭示 Product Cookie 的 Secure 错误依赖 `NODE_ENV=production`；`0e0ec3a…` 已按固定 HTTPS Web origin 修正。`c3d81bf…` 对旧 generation signout 增加Redis原子CAS，旧请求不删新会话、不吊销新refresh、不发同名清除cookie或issuer引导，并消费BFF `ddb462e…` policy来源。独立审查0 P0/P1/P2，Root Node22 contract **52/52**、architecture **32/32**、Vitest **1371/1371**、lint/typecheck/build 与 Playwright **6/6** 通过。固定 Web `c3d81bf…`/BFF `ddb462e…`/IAM `f240bd7…` 真HTTPS Product Session 流程已 **PASS**：callback→会话→单次refresh→旧代拒绝→当前revoke→IAM确认/issuer失效，自有资源 **0**。普通 BFF adapter Bearer、旧IAM直连删除及UI登出消费仍待后续切片。
- Root 已在同一个自有临时 PostgreSQL 数据库、同一账号运行 BFF 与 IAM 两个 installer，观察到 `kokoro_bff` 16 表、`kokoro_iam` 17 表、`public` 0 业务表、跨 owner FK 0，随后删除测试库。应用开发采用一个物理数据库和一套账号；其他数据 owner 的 schema 适配尚未据此宣称完成，不新增部署角色或长期子库。

## 本次 Root 集成边界

`verification/contracts/consumer-inventory.json` 固定 owner/consumer commit blob；Root `594358ba…` 首次同步 Web/BFF/IAM **149 处来源 tuple**，`0c829a0…` 跟进 Web HTTPS cookie pin，`a59bc736…` 已同步 Web **9**、BFF **137** 处来源 tuple 与 BFF `docs/API_CONTRACT.md` 新digest。不改变 16 条 edge 语义，现有状态仍为 **5 active / 11 broken / 1 illegal**；Web→IAM 旧直连仍是非法边，Web→BFF Product generated edge 尚未激活。checkpoint、policy、topology均PASS；compatibility按上述未闭环状态仍exit1。真HTTPS S1会话链已PASS，不外推为S2/Team/聊天整体闭环。

当前三仓固定pin的Root relay policy、w1b-iam checkpoint、topology均PASS；`scripts/tests` **597 passed / 108 subtests**，真HTTPS Product Session流程PASS且自有资源0。此证据不同于历史`519d5a9…`的RP-only **14/14**（成功回调仍受控503）和OIDC→BFF **15/15**，也不覆盖普通Product Bearer。最终runner/台账工作树修订待提交推送；提交后仍须复核main-only。本轮全仓compatibility继续 **5 active/11 broken/1 illegal**（exit1）；静态治理此前9仓 **130 violations / 0 unverified**（exit1），不因局部绿色测试而降级门禁。

## 下一条代码关键路径

1. S1真实HTTPS Product Session已在固定三仓SHA上通过；下一片先让 Web 普通 BFF adapter 使用在线会话的单一 Bearer，删除旧 IAM magic-link/team-session 直连、sealed envelope 和旧 identity header，并以真实受保护Product请求验收，不以S1登录PASS代替S2。
2. IAM Team 已过三设计文档门，下一片由IAM owner实现窄读runtime/Schema/OpenAPI/SDK，再让BFF发布Product projection，Web最后切换；默认个人私有、显式分享，不以成员资格开放私人聊天/文件。
3. 之后推进单一 AG-UI 聊天、Agent/Storage/System/Platform/Scheduler 各自 owner 闭环；Billing 最后。

旧全仓 `verify-ten-repository-full.sh` 和 `run_stage2_owner_health.py` 仍是只诊断退出的暂停入口；不以其替代逐仓代码门或已隔离的跨仓 smoke。
