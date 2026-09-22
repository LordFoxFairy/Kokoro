# Root 当前状态

状态：2026-09-21。Root 已采用 remote-name Git submodule 组合；可复现组合由 `.gitmodules` 与精确 gitlink SHA 定义，而不是同级 checkout 或工作目录约定。本轮后端闭环以 [批准设计](superpowers/specs/2026-09-20-kokoro-backend-closure-design.md) 为架构事实源，以 [Wave 0B 计划](superpowers/plans/2026-09-21-wave-0b-hard-link-closure.md) 为当前执行计划，以 [`task.md`](task.md) 为唯一任务状态表，以 [`progress.md`](progress.md) 为唯一执行证据账。

## 当前已接收组合

下表是 W0B-7I 通过独立 SPEC/QUALITY 审查和 Root 普通 index 门禁后的组合；本文件所在集成 commit 的 gitlink 是冻结事实源，工作区 checkout 本身不是组合证据。

| Root 路径 | 子仓 SHA |
| --- | --- |
| `apps/kokoro-app` | `ce4e466c960c4b40a87a7be38b5a56f265f7a12f` |
| `apps/kokoro-mori` | `ca76c2e12861a2e4a6af3049f6df8c34b417c158` |
| `apps/kokoro-bff` | `2ed792586e89c035155938078d9b07f33af95abd` |
| `apps/kokoro-agent` | `741c928dfc11313a25064a905d77d4ad371f5534` |
| `apps/kokoro-iam` | `35d868a410c06731362bd1e8bcc3e602d01875f8` |
| `apps/kokoro-system` | `c0a76a3a7614bf46ea6e665e523f24261862436f` |
| `apps/kokoro-billing` | `63e0ab6e61b397f23f7ab71f5d6dc9df3d6de0fa` |
| `apps/kokoro-capability` | `7f89a267d745cbb9870f52d6edb23dec1a3c469b` |
| `apps/kokoro-storage` | `f80917e98a1cd1fe196ce10b0aba6f8f67fdf205` |
| `apps/kokoro-scheduler` | `92bf9e7e6724c591bab4b7fa27f08d694b59a67e` |
| `libs/kokoro-web-shared` | `0c4e87ace01340aaa07bc57935f1d98b8e77af14` |

- Root 子仓路径严格使用远端仓名：Web 为 `apps/kokoro-app`，不存在 `kokoro/`、`apps/kokoro/` 或其他 alias；Mori 为 `apps/kokoro-mori`；共享前端包为 `libs/kokoro-web-shared`。
- 九个正式 runtime owner 仍是 `kokoro-app`、BFF、Agent、IAM、System、Billing、Capability、Storage、Scheduler；Mori 是独立前端产品，web-shared 是独立版本化库。
- Root 与每个 submodule 的本地和 `origin` 都只保留 `main`。每个 gitlink 锁定已推送的 commit；`.gitmodules branch=main` 仅是更新提示，不构成发布锁。
- 子仓的 tests 不迁入 Root。Root `scripts/tests/` 只覆盖 Root 治理脚本；跨仓行为测试将归 `verification/`，不重复子仓单测。

## 本轮已完成的治理与 owner 修复

1. Root 的静态审计按 owner profile 区分 SQL-first/ORM-first canonical schema、已退役目录、Node major 与 owner OpenAPI；IAM 的 Better Auth 输入归入带来源说明的 `contract/vendor/`，不再伪装为 IAM 自有 OpenAPI。
2. Capability owner release `7f89a267…` 固定四个 `/v1/*` projection；BFF release `2ed79258…` 已通过 generated consumer 和真实进程 smoke 集成，`EDGE-BFF-CAPABILITY` 已激活。
3. Scheduler owner release `92bf9e7e…` 在不新增 API shape 或 Schema 的前提下锁定 `schedule_not_found` / `schedule_already_exists`、RFC3339Nano 样本和 opaque idempotency key 逐字传递；W0B-7I 只前移 owner pin，不激活 Scheduler edge。
4. IAM 与 Scheduler 的 contract 文档明确机器事实源和生成关系；Web、BFF、IAM、Billing、Capability、Storage 启用 `strictDepBuilds`，Capability/Storage release Node 与各自声明对齐。
5. BFF 删除未被生产入口使用的 `src/database/setup.ts`；`scripts/apply-schema.mjs` 是唯一 canonical SQL installer，architecture test 覆盖 direct schema read、literal import 与第二 installer 的回归。Web MCP 注册表单只把 CSS Module 的 `legacy*` 键同步改为 `serverEditor*`，无 DOM、行为或样式值变化。
6. 每项子仓变更先在子仓 `main` 验证并推送，再由 Root 提升 gitlink；本轮没有创建跨仓 workspace、共享 lockfile、共享 ORM schema 或可编辑 contract 副本。

## 当前验证证据

W0B-7I 在上述七文件集成切片上通过独立 SPEC/QUALITY 审查（0/0/0），Root 精确暂存后以普通 index 实际执行：

```text
python3 scripts/verify-repository-topology.py                 -> PASS
python3 scripts/verify-contract-checkpoint.py --expected verification/contracts/checkpoints/w0b-capability.json -> PASS; 2 active / 14 broken / 1 illegal
python3 -m pytest scripts/tests -q                            -> 432 passed
python3 scripts/verify-ten-repository-standard.py --format json -> status FAIL: 109 violations, 1 unverified
```

最后一项是 owner 改造队列，不是成功门禁：它诚实地报告尚未完成的工程工作，绝不能写成“全仓质量门已绿”。`kokoro-system` 的 TypeScript 审计为 `unverified`，原因是缺少 `tsconfig.json` 或已安装 TypeScript，不能视为通过。

Root 的 OpenAPI 词法 preflight 也不是完整 YAML parser：带前导过度缩进空行的某类 malformed block scalar 仍可能绕过其词法确认；各 owner 的 canonical parser/linter 会拒绝当前这类坏契约。将 Root preflight 替换为依赖治理下的真实 parser 是独立后续任务，在完成前不得把 Root 词法检查当成 malformed-contract 的唯一证明。

## 明确的下一轮 owner 队列

| Owner | 当前实测缺口（按业务切片收敛） |
| --- | --- |
| Web | 直接 downstream owner 引用、BFF auth 边界，以及超大 UI/CSS 文件拆分与 TypeScript 严格配置。 |
| BFF | feature-first 组织与 ES2024/strict TypeScript 配置；`format:check` 已实现，不再是当前缺口。 |
| Agent | configuration boundary 与 retired Python layering/topology 决策。 |
| IAM | owned OpenAPI metadata、schema/CI/release、依赖方向、文件粒度与 TypeScript 配置。 |
| System | 补齐可审计的 TypeScript 配置/安装前置条件后再判断实际缺口。 |
| Billing | v1/M3 contract 决策、OpenAPI parsing、配置边界、文件粒度与 TypeScript 配置。 |
| Capability | P2/P5 能力边界、authorization split、依赖方向/粒度与 TypeScript 配置；`kokoro-capability`→`kokoro-platform` 的 clean-slate cutover 仍须独立 ADR。 |
| Storage | command type/wire boundary、owned OpenAPI metadata 与 TypeScript 配置。 |
| Scheduler | owner 稳定错误与幂等边界证据已修复；BFF control/receiver consumer 与双向真实 smoke 仍待 W0B-8..11。 |

## 未闭合的组合工作

1. Root 已有两个只清理本次所有资源的安全真实进程入口：`scripts/e2e/run_system_owner_smoke.py` 与 `scripts/e2e/run_capability_bff_smoke.py`。它们不等于全仓组合 runner；旧 `verify-ten-repository-full.sh` / `run_stage2_owner_health.py` 仍保持暂停且只诊断退出。
2. `EDGE-WEB-IAM-DIRECT` 仍是唯一非法旁路；未处理的 broken edge 仍然是真实未完成项，不会因 owner pin 前移而自动激活。
3. 全仓组合 E2E、发布镜像、生产组合 manifest 和 SLO 尚未验收；Root 静态治理或单个 smoke PASS 不冒充这些证据。
