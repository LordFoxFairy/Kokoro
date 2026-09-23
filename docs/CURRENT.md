# Root 当前状态

状态日期：2026-09-23。Root 使用 remote-name Git submodule；可复现组合由本仓 `.gitmodules` 和精确 gitlink 定义。架构决策见 [设计](superpowers/specs/2026-09-20-kokoro-backend-closure-design.md)，执行状态见 [`task.md`](task.md)，实际命令与资源证据见 [`progress.md`](progress.md)。本文件只列当前能力与缺口，不用子仓测试代替跨仓验收。

## 当前组合

| 路径 | 锁定的子仓 main commit |
| --- | --- |
| `apps/kokoro-app` | `5da730426faaca54a9f0003fa1e7fd99f4db6f00` |
| `apps/kokoro-mori` | `ca76c2e12861a2e4a6af3049f6df8c34b417c158` |
| `apps/kokoro-bff` | `eb7ded2386efd9a10905843a7a5aedff9ac72df6` |
| `apps/kokoro-agent` | `741c928dfc11313a25064a905d77d4ad371f5534` |
| `apps/kokoro-iam` | `65b0fd969989d4044fae640a8414d9c2dcf41c3b` |
| `apps/kokoro-system` | `c0a76a3a7614bf46ea6e665e523f24261862436f` |
| `apps/kokoro-billing` | `63e0ab6e61b397f23f7ab71f5d6dc9df3d6de0fa` |
| `apps/kokoro-capability` | `9c88d0d934387b590bc74dae0179a587292e0253` |
| `apps/kokoro-storage` | `f80917e98a1cd1fe196ce10b0aba6f8f67fdf205` |
| `apps/kokoro-scheduler` | `975dee59616a1e0eda609aa69283401344900d83` |
| `libs/kokoro-web-shared` | `0c4e87ace01340aaa07bc57935f1d98b8e77af14` |

Web 正式路径是 `apps/kokoro-app`，不是 `apps/kokoro/`。当前正式能力仓仍叫 `kokoro-capability`，尚未原子切换成 `kokoro-platform`；Mori 和 web-shared 不是本轮后端 runtime owner。子仓的 tests 不迁入 Root；各子仓测试留在各自仓库。`scripts/tests/` 只覆盖 Root 治理脚本和组合 runner 自身的测试；跨仓验收入口在 `scripts/e2e/`，证据清单在 `verification/`。

## 已落地的 owner 能力

- IAM 已提供真实 Code+S256、session admission 与测试专用 OIDC host；本次 `6bc9b19…` 将 17 个 Prisma model 固定到 `kokoro_iam` schema，fresh installer 与 readiness 不再依赖 `public` 或整库空白。Root 独立 Node24 `pnpm verify` 704/704、串行真实 integration 183/183；旧并行 fixture 的全局临时库计数竞态仍待单独修，不是应用数据库并发限制。
- BFF 已提供个人私有 Conversation/Project/ScheduledTask 权限、IAM admission、固定 `/iam` 原生 relay、Capability/Scheduler generated consumer。本次 `a4dbc33…` 使用 `kokoro_bff` schema 与 IAM `6bc9b19…` policy 来源；Root Node22 标准 253/253、contract 25/25、真实 schema 6/6、integration 37/37 已独立通过。
- Web 已实现同源 issuer GET、sign-in 与 tenant/consent 三页交互，并安装 Auth.js RP-only Code+S256/state/nonce callback。固定 issuer/client/callback/resource，token Basic、userinfo Bearer 与 JWKS 仅经 BFF；验证型 `client.callback` 检查 EdDSA ID token，Redis 一次消费 state。真实 HTTPS Web→BFF→IAM RP-only **14/14** 已在前一固定 pin 验证，成功仍受控 `503 product_session_unavailable`、无可用 Product Session。本次 Web/IAM 三文档及 ADR 已统一双阶段 CAS、单次 refresh、加密当前凭据与 pending logout 语义；BFF/Web policy provenance 已机械 re-pin，运行会话仍待代码实现。
- Root 已在同一个自有临时 PostgreSQL 数据库、同一账号运行 BFF 与 IAM 两个 installer，观察到 `kokoro_bff` 16 表、`kokoro_iam` 17 表、`public` 0 业务表、跨 owner FK 0，随后删除测试库。应用开发采用一个物理数据库和一套账号；其他数据 owner 的 schema 适配尚未据此宣称完成，不新增部署角色或长期子库。

## 本次 Root 集成边界

`verification/contracts/consumer-inventory.json` 固定 owner/consumer commit blob；本次同步 Web/BFF/IAM **149 处来源 tuple**，仅 BFF `docs/API_CONTRACT.md` 的 evidence digest 随文档变化，不改变 16 条 edge 语义。现有状态仍为 **5 active / 11 broken / 1 illegal**；Web→IAM 旧直连仍是非法边，Web→BFF Product generated edge 尚未激活。

前一固定 pin 的 Root checkpoint、policy、topology 与 main-only 均 PASS，Root+11 子仓只留 main 且本地/远端一致、工作树干净；Root `scripts/tests` **588 passed / 78 subtests**。Root `519d5a924b9b0d54a97edc760f82a965e366d1ea` 发布后，Web→BFF→IAM 真实 HTTPS RP-only 链 **14/14**，验证真实 Code+S256/token/userinfo/JWKS、回调重放和受控 `503 product_session_unavailable`，资源零残留；首次 OIDC→BFF **15/15**。本次三仓新 pin 的 Root 门与真实 HTTPS 尚待当前提交后复验，不能继承旧组合的测试结论。全仓静态治理此前为9仓 **130 violations / 0 unverified**（exit1），不因局部绿色测试而降级门禁。

## 下一条代码关键路径

1. Web Product Session 与所有 BFF adapter 的单一 Bearer：Web/IAM refresh 语义已统一但代码未实现；Team IAM→BFF→Web 窄契约仍待 owner-first 发布。默认个人私有、显式分享；按调用点删除旧 IAM magic-link/team-session 直连、sealed envelope 和旧 identity header，不建兼容双轨。
2. 双 CAS refresh 与退出链：先 tombstone；仅 active take 当前 refresh 后单次 revoke，pending 不发送可能已轮换旧 token。真实三仓 RP-only 回归是前置，不把当前受控 503 当完整登录。
3. 之后推进单一 AG-UI 聊天、Agent/Storage/System/Platform/Scheduler 各自 owner 闭环；Billing 最后。

旧全仓 `verify-ten-repository-full.sh` 和 `run_stage2_owner_health.py` 仍是只诊断退出的暂停入口；不以其替代逐仓代码门或已隔离的跨仓 smoke。
