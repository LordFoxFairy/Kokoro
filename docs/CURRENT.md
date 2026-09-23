# Root 当前状态

状态日期：2026-09-23。Root 使用 remote-name Git submodule；可复现组合由本仓 `.gitmodules` 和精确 gitlink 定义。架构决策见 [设计](superpowers/specs/2026-09-20-kokoro-backend-closure-design.md)，执行状态见 [`task.md`](task.md)，实际命令与资源证据见 [`progress.md`](progress.md)。本文件只列当前能力与缺口，不用子仓测试代替跨仓验收。

## 当前组合

| 路径 | 锁定的子仓 main commit |
| --- | --- |
| `apps/kokoro-app` | `c71aa3f5130ae52c7f76356ac38bdabaf551d4e9` |
| `apps/kokoro-mori` | `ca76c2e12861a2e4a6af3049f6df8c34b417c158` |
| `apps/kokoro-bff` | `a4dbc3339448c7ee8763b0f82d1c0ae4c213bf87` |
| `apps/kokoro-agent` | `741c928dfc11313a25064a905d77d4ad371f5534` |
| `apps/kokoro-iam` | `6bc9b190c359b8109238626ff689ce9839e858b5` |
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
- Web `c71aa3f…` 已实现同源 issuer GET、sign-in 与 tenant/consent 三页交互，并安装 Auth.js RP-only Code+S256/state/nonce callback。固定 issuer/client/callback/resource，token Basic、userinfo Bearer 与 JWKS 仅经 BFF；验证型 `client.callback` 检查 EdDSA ID token，Redis 一次消费 state。Node22 contract 52/52、architecture 32/32、标准 1339/1339、build 与 Playwright 6/6；真实 Next + 严格 BFF fixture 覆盖签名、重放、取消、超时和限额。验证成功仍受控 `503 product_session_unavailable`、无可用新 session；fixture 不等于真实 IAM 三服务或完整登录。
- Root 已在同一个自有临时 PostgreSQL 数据库、同一账号运行 BFF 与 IAM 两个 installer，观察到 `kokoro_bff` 16 表、`kokoro_iam` 17 表、`public` 0 业务表、跨 owner FK 0，随后删除测试库。应用开发采用一个物理数据库和一套账号；其他数据 owner 的 schema 适配尚未据此宣称完成，不新增部署角色或长期子库。

## 本次 Root 集成边界

`verification/contracts/consumer-inventory.json` 固定 owner/consumer commit blob；本次仅同步 Web 新 gitlink 的 9 处来源，不改变 16 条 edge 语义。现有状态仍为 **5 active / 11 broken / 1 illegal**；Web→IAM 旧直连仍是非法边，Web→BFF Product generated edge 尚未激活。五个 Root 跨仓 runner 继续将 BFF 应用 URL 定向 `kokoro_bff`，直接观测 SQL 显式限定 owner schema、`psql` 使用无应用 schema 参数的原 URL；System/Capability/Scheduler/IAM 自身 URL 不改。

当前组合已执行 Root checkpoint、policy、topology 与 main-only，均 PASS；Root `scripts/tests` **570 passed / 56 subtests**。固定新 pin 真实IAM准入→BFF **7/7**、首次OIDC→BFF **15/15**、Capability→BFF **8/8**、Scheduler→BFF **11/11**、System/BFF/Agent HTTP组合 **PASS**，各 runner 报告仅清理本次自有 PostgreSQL/Redis/进程。Scheduler 的两个直接观测SQL在本次补丁中已限定 `kokoro_bff` 并在发布后重跑11/11；一次诊断前的无细节瞬时FAIL记录在progress，不抹去。全仓静态治理当前仍为9仓 **130 violations / 0 unverified**（exit1），不因局部绿色测试而降级门禁。

## 下一条代码关键路径

1. Root 真实 HTTPS Web→BFF→IAM RP 组合：复用隔离 IAM/BFF host 与自有 PostgreSQL/Redis，跑浏览器同源登录至真实 IAM 签名回调，终态应为 `503 product_session_unavailable` 而非完成登录；验证重放/负例与无新 session。
2. Product Session 与所有 BFF adapter 的单一 Bearer：默认个人私有、显式分享；按调用点删除旧 IAM magic-link/team-session 直连、sealed envelope 和旧 identity header，不建兼容双轨。
3. Refresh CAS 与先 tombstone 后 revoke/end-session 的退出链。之后推进单一 AG-UI 聊天、Agent/Storage/System/Platform/Scheduler 各自 owner 闭环；Billing 最后。

旧全仓 `verify-ten-repository-full.sh` 和 `run_stage2_owner_health.py` 仍是只诊断退出的暂停入口；不以其替代逐仓代码门或已隔离的跨仓 smoke。
