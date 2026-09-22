# Root 当前状态

状态：2026-09-22。Root 已采用 remote-name Git submodule 组合；可复现组合由 `.gitmodules` 与精确 gitlink SHA 定义，而不是同级 checkout 或工作目录约定。本轮后端闭环以 [批准设计](superpowers/specs/2026-09-20-kokoro-backend-closure-design.md) 为架构事实源，以 [Wave 0B 计划](superpowers/plans/2026-09-21-wave-0b-hard-link-closure.md) 为当前执行计划，以 [`task.md`](task.md) 为唯一任务状态表，以 [`progress.md`](progress.md) 为唯一执行证据账。

## 当前已接收组合

下表是 W0B-11/15 已通过最终 SPEC/QUALITY 审查的组合（两者均 0/0/0）；子仓已完成 Root owner 复验和推送。Root 集成提交、推送及全仓 main-only/clean 审计结果见 task/progress；本文件所在集成 commit 的 gitlink 是冻结事实源，工作区 checkout 本身不是组合证据。

| Root 路径 | 子仓 SHA |
| --- | --- |
| `apps/kokoro-app` | `ce4e466c960c4b40a87a7be38b5a56f265f7a12f` |
| `apps/kokoro-mori` | `ca76c2e12861a2e4a6af3049f6df8c34b417c158` |
| `apps/kokoro-bff` | `c5e9b3cc8eb134ff72e37f56ac1f95ebec4f42e7` |
| `apps/kokoro-agent` | `741c928dfc11313a25064a905d77d4ad371f5534` |
| `apps/kokoro-iam` | `35d868a410c06731362bd1e8bcc3e602d01875f8` |
| `apps/kokoro-system` | `c0a76a3a7614bf46ea6e665e523f24261862436f` |
| `apps/kokoro-billing` | `63e0ab6e61b397f23f7ab71f5d6dc9df3d6de0fa` |
| `apps/kokoro-capability` | `9c88d0d934387b590bc74dae0179a587292e0253` |
| `apps/kokoro-storage` | `f80917e98a1cd1fe196ce10b0aba6f8f67fdf205` |
| `apps/kokoro-scheduler` | `975dee59616a1e0eda609aa69283401344900d83` |
| `libs/kokoro-web-shared` | `0c4e87ace01340aaa07bc57935f1d98b8e77af14` |

- Root 子仓路径严格使用远端仓名：Web 为 `apps/kokoro-app`，不存在 `kokoro/`、`apps/kokoro/` 或其他 alias；Mori 为 `apps/kokoro-mori`；共享前端包为 `libs/kokoro-web-shared`。
- 九个正式 runtime owner 仍是 `kokoro-app`、BFF、Agent、IAM、System、Billing、Capability、Storage、Scheduler；Mori 是独立前端产品，web-shared 是独立版本化库。
- Root 与每个 submodule 的本地和 `origin` 都只保留 `main`。每个 gitlink 锁定已推送的 commit；`.gitmodules branch=main` 仅是更新提示，不构成发布锁。
- 子仓的 tests 不迁入 Root。Root `scripts/tests/` 只覆盖 Root 治理脚本；跨仓行为测试将归 `verification/`，不重复子仓单测。

## 当前已验证的代码与组合能力

- Capability runtime `9c88d0d…`：显式typed监听地址，源码默认loopback、Docker显式wildcard；release空库先安装再persisted check；两个Serializable探针suite物理隔离，标准并行853测试通过、0跳过。
- BFF `c5e9b3c…`：已使用Capability与Scheduler固定artifact/generated client；Scheduler control、专用持久receipt/CAS和恢复链已接通。Storage旧HTTP/配置/parser/mock成功数据及孤儿200类型已删除；认证后的Library当前只返回明确503且零Storage socket，不等于Storage功能完成。
- Scheduler `975dee59…`：新键同名create冲突以409写入持久receipt并可重启重放；普通/race各139项的owner验收见progress。
- Artifact来源保持真实：BFF消费的Capability artifact仍来自`7f89a267…`，Scheduler artifact仍来自`92bf9e7e…`，与各自新runtime release的canonical contract字节相同；没有伪造重新生成。
- Root最终Capability/BFF真实进程smoke8/8；Scheduler/BFF真实进程smoke11/11，覆盖真实owner409、RFC3339小数、重复重放、身份冲突、response-unknown与BFF重启后重试。Agent仍是deterministic receipt stub，真实Agent闭环留W4；Storage/IAM/provider readiness替身也不算真实owner验收。

## 当前验证证据

本次已审查组合的实际结果（Root 提交后审计见 task/progress）：

```text
python3 scripts/verify-repository-topology.py -> PASS
python3 scripts/verify-contract-checkpoint.py --expected verification/contracts/checkpoints/w0b-exit.json -> PASS; 4 active / 12 broken / 1 illegal
python3 -m pytest scripts/tests -q -> 495 passed（最终激活组合）
Capability owner -> 75 files / 853 passed / 0 failed / 0 skipped
BFF owner -> unit199 / contract21 / architecture25 / schema4 / integration35，均0失败/0跳过
Capability/BFF real smoke -> 8 passed，全部本次资源回收
Scheduler/BFF real smoke -> 11 passed，全部本次资源回收
python3 scripts/verify-ten-repository-standard.py --format json -> FAIL: 112 violations / 1 unverified
```

BFF Library有意只声明403/503，Redocly报告1个无2xx的warning（exit0）；未为消除警告保留假200或放宽规则。
本机hostname此前仅解析私网导致Scheduler smoke在资源创建前失败；本次解析已包含127.0.0.1，严格loopback门和完整11case通过。
未修改hosts/resolver或扩展listener/CIDR；这不是对旧失败结果的改写。

全仓112项静态差距与System TypeScript配置未验证仍是实际待办；不得写成全仓质量门全绿。
Root OpenAPI词法preflight也不等于完整YAML parser，带异常空行缩进的某类malformed block scalar边界仍由owner canonical parser/linter兜底，后续替换需正式依赖治理。

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
| Scheduler | owner/control/receiver与双向真实smoke已验证；真实Agent投递/授权闭环与全仓release验收仍待后续Wave。 |

## 未闭合的组合工作

1. Root 已有System、Capability/BFF及Scheduler/BFF三个隔离真实进程入口，位于`scripts/e2e/`。它们不等于全仓组合 runner；旧 `verify-ten-repository-full.sh` / `run_stage2_owner_health.py` 仍保持暂停且只诊断退出。
2. `EDGE-WEB-IAM-DIRECT` 仍是唯一非法旁路；剩余12个 broken edge 仍然是真实未完成项，不会因 owner pin 前移而自动激活。
3. 全仓组合 E2E、发布镜像、生产组合 manifest 和 SLO 尚未验收；Root 静态治理或单个 smoke PASS 不冒充这些证据。
