# Root 当前状态

状态：2026-09-21。Root 已采用 remote-name Git submodule 组合；当前可复现组合由 `.gitmodules` 与精确 gitlink SHA 定义，而不是同级 checkout 或工作目录约定。本轮后端闭环以 [批准设计](superpowers/specs/2026-09-20-kokoro-backend-closure-design.md) 为架构事实源，以 [`task.md`](task.md) 为唯一任务状态表，以 [`progress.md`](progress.md) 为执行证据账；[Wave 0A 治理与契约门计划](superpowers/plans/2026-09-21-wave-0a-governance-and-contract-gates.md) 正在执行。Compatibility 红门和下述 110 项静态违规仍是未通过事实，不因 W0A 开始执行而改写为通过。

## 已锁定的组合

2026-09-20 的组合快照（Root 提升子仓后、文档记录前的 Root commit `9a498c81`）如下；本文件所在后续文档 commit 不改变这些 gitlink：

| Root 路径 | 子仓 SHA |
| --- | --- |
| `apps/kokoro-app` | `ce4e466c960c4b40a87a7be38b5a56f265f7a12f` |
| `apps/kokoro-mori` | `ca76c2e12861a2e4a6af3049f6df8c34b417c158` |
| `apps/kokoro-bff` | `f117a00a9c12649a762c975622da81ad8e3c59ec` |
| `apps/kokoro-agent` | `741c928dfc11313a25064a905d77d4ad371f5534` |
| `apps/kokoro-iam` | `35d868a410c06731362bd1e8bcc3e602d01875f8` |
| `apps/kokoro-system` | `c0a76a3a7614bf46ea6e665e523f24261862436f` |
| `apps/kokoro-billing` | `63e0ab6e61b397f23f7ab71f5d6dc9df3d6de0fa` |
| `apps/kokoro-capability` | `e576d38dd103c2fda4d6389385b3f04f82ddfc20` |
| `apps/kokoro-storage` | `f80917e98a1cd1fe196ce10b0aba6f8f67fdf205` |
| `apps/kokoro-scheduler` | `17c2de3e68ed75dbf3fa495643f6ad280e3c7112` |
| `libs/kokoro-web-shared` | `0c4e87ace01340aaa07bc57935f1d98b8e77af14` |

- Root 子仓路径严格使用远端仓名：Web 为 `apps/kokoro-app`，不存在 `kokoro/`、`apps/kokoro/` 或其他 alias；Mori 为 `apps/kokoro-mori`；共享前端包为 `libs/kokoro-web-shared`。
- 九个正式 runtime owner 仍是 `kokoro-app`、BFF、Agent、IAM、System、Billing、Capability、Storage、Scheduler；Mori 是独立前端产品，web-shared 是独立版本化库。
- Root 与每个 submodule 的本地和 `origin` 都只保留 `main`。每个 gitlink 锁定已推送的 commit；`.gitmodules branch=main` 仅是更新提示，不构成发布锁。
- 子仓的 tests 不迁入 Root。Root `scripts/tests/` 只覆盖 Root 治理脚本；跨仓行为测试将归 `verification/`，不重复子仓单测。

## 本轮已完成的治理整理

1. Root 的静态审计按 owner profile 区分 SQL-first/ORM-first canonical schema、已退役目录、Node major 与 owner OpenAPI；IAM 的 Better Auth 输入归入带来源说明的 `contract/vendor/`，不再伪装为 IAM 自有 OpenAPI。
2. IAM 与 Scheduler 的 contract 文档明确机器事实源和生成关系；Web、BFF、IAM、Billing、Capability、Storage 启用 `strictDepBuilds`，Capability/Storage release Node 与各自声明对齐。
3. BFF 删除未被生产入口使用的 `src/database/setup.ts`；`scripts/apply-schema.mjs` 是唯一 canonical SQL installer，architecture test 覆盖 direct schema read、literal import 与第二 installer 的回归。Web MCP 注册表单只把 CSS Module 的 `legacy*` 键同步改为 `serverEditor*`，无 DOM、行为或样式值变化。
4. 每项子仓变更先在子仓 `main` 验证并推送，再由 Root 提升 gitlink；本轮没有创建跨仓 workspace、共享 lockfile、共享 ORM schema 或可编辑 contract 副本。

## 当前验证证据

在上述组合快照上实际执行：

```text
python3 scripts/verify-repository-topology.py                 -> PASS
python3 scripts/verify-main-only.py                           -> PASS
python3 -m pytest scripts/tests -q                            -> 322 passed
python3 scripts/verify-ten-repository-standard.py --format json -> status FAIL: 110 violations, 1 unverified
```

最后一项是 owner 改造队列，不是成功门禁：它诚实地报告尚未完成的工程工作，绝不能写成“全仓质量门已绿”。`kokoro-system` 的 TypeScript 审计为 `unverified`，原因是缺少 `tsconfig.json` 或已安装 TypeScript，不能视为通过。

Root 的 OpenAPI 词法 preflight 也不是完整 YAML parser：带前导过度缩进空行的某类 malformed block scalar 仍可能绕过其词法确认；各 owner 的 canonical parser/linter 会拒绝当前这类坏契约。将 Root preflight 替换为依赖治理下的真实 parser 是独立后续任务，在完成前不得把 Root 词法检查当成 malformed-contract 的唯一证明。

## 明确的下一轮 owner 队列

| Owner | 当前实测缺口（按业务切片收敛） |
| --- | --- |
| Web | 直接 downstream owner 引用、BFF auth 边界，以及超大 UI/CSS 文件拆分与 TypeScript 严格配置。 |
| BFF | feature-first 组织、`format:check`、ES2024/strict TypeScript 配置。 |
| Agent | configuration boundary 与 retired Python layering/topology 决策。 |
| IAM | owned OpenAPI metadata、schema/CI/release、依赖方向、文件粒度与 TypeScript 配置。 |
| System | 补齐可审计的 TypeScript 配置/安装前置条件后再判断实际缺口。 |
| Billing | v1/M3 contract 决策、OpenAPI parsing、配置边界、文件粒度与 TypeScript 配置。 |
| Capability | P2/P5 能力边界、authorization split、依赖方向/粒度与 TypeScript 配置；`kokoro-capability`→`kokoro-platform` 的 clean-slate cutover 仍须独立 ADR。 |
| Storage | command type/wire boundary、owned OpenAPI metadata 与 TypeScript 配置。 |
| Scheduler | `/v1` contract versioning 收敛。 |

## 未闭合的组合工作

1. Root `verification/` 的跨仓 contract/integration/e2e/smoke runner 尚未重建；旧会清理共享基础设施的 runner 保持暂停。
2. 生产组合 tag、子仓 SHA、SDK 版本、image digest 和验证结果需要在首次正式组合发布时写入 release manifest。
3. 上述 owner 队列逐仓执行完整门禁；Root 静态治理 PASS 不冒充 live owner、外部 provider、发布镜像或 SLO 验收。
