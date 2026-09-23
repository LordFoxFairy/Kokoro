# Root 当前状态

状态：2026-09-23。Root 已采用 remote-name Git submodule 组合；可复现组合由 `.gitmodules` 与精确 gitlink SHA 定义，而不是同级 checkout 或工作目录约定。本轮后端闭环以 [批准设计](superpowers/specs/2026-09-20-kokoro-backend-closure-design.md) 为架构事实源，以 [Wave 1C 计划](superpowers/plans/2026-09-23-wave-1c-web-oidc-and-same-origin.md) 为当前执行计划，以 [`task.md`](task.md) 为唯一任务状态表，以 [`progress.md`](progress.md) 为唯一执行证据账。

## 当前已接收组合

W0B 已验收：Root 集成 `96d238bae1e23cbbfda66ea631e7e40c1176ef3b` 已推送，最终 SPEC/QUALITY 均 0/0/0；当时 Root + 11 个 submodule 的 main-only/clean、HEAD = origin/main = live main 审计通过。W1A 已由 Root `a7585a97a2bf34eff33f2d20af3a46779aca1884` 集成并推送。W1B BFF 两个owner代码切片及真实IAM↔BFF组合已验收；Web同源登录与完整W1仍未完成。下表为当前Root gitlink组合。

| Root 路径 | 子仓 SHA |
| --- | --- |
| `apps/kokoro-app` | `38683a5c2a46af3e9d604b5d7219a864684d5ad1` |
| `apps/kokoro-mori` | `ca76c2e12861a2e4a6af3049f6df8c34b417c158` |
| `apps/kokoro-bff` | `cd1c2600ea2a6e0716b07628822a49653964675a` |
| `apps/kokoro-agent` | `741c928dfc11313a25064a905d77d4ad371f5534` |
| `apps/kokoro-iam` | `b838853a81ff34bd0f7a079ccc75ba6abd61d1ec` |
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
- 用户已选开发应用单 PostgreSQL 数据库/单账号，owner 在同库使用独立 schema/连接 URL；现有部分 owner 仍限制 `public` 或整库空白安装，W1C-DB 代码切片未完成，不能把目标说成当前可运行事实。测试fixture的临时库只是测试隔离，应用并发访问同库不受此限制。
- Web `38683a5…` 仅完成 W1C-2 TECHNICAL_DESIGN/API_CONTRACT/DATA_MODEL 三文档门和最终来源pin修正；Auth.js、同源 `/iam` adapter、Product Session、全代理Bearer及浏览器E2E均未实现，`EDGE-WEB-BFF`/Web→IAM非法旁路状态未变。

## 当前已验证的代码与组合能力

- IAM `b838853…`（生产准入代码 `54d0d5f…`，其后为文档与test-owned HTTP联调fixture）：session admission OpenAPI/SDK0.2.0已验收；Root此前重跑701标准、174真实integration与release仓外consumer2项通过；W1C test-only Web OIDC host增加精确issuer JWKS→本地fixture映射后，Root独立Node24聚焦5/5并验证登录至带hint退出，资源零残留。BFF通过固定IAM artifact/generated client在线消费；准入只确认当前用户会话/成员，不替代BFF资源权限或Web登录。W1C经BFF的首次无session OAuth 正向链已由Root修后真HTTP 15/15证实，Web浏览器链仍未完成。
- Capability runtime `9c88d0d…`：显式typed监听地址，源码默认loopback、Docker显式wildcard；release空库先安装再persisted check；两个Serializable探针suite物理隔离，标准并行853测试通过、0跳过。
- BFF `cd1c260…`：已使用Capability、Scheduler与IAM固定artifact/generated client；Scheduler control、专用持久receipt/CAS和恢复链已接通。W1B代码增加IAM session bearer准入、Project/ScheduledTask/Chat按个人私有授权、Share撤销竞态拒绝；W1C新增精确 `/iam` 原生 relay policy/transport，并固定IAM最新test-owned来源，Node22标准248/248、contract25/25通过。当前pin真实IAM admission→BFF 7case及修后首次OAuth 15case已由Root独立复验；Web同源登录仍待后续切片。Storage旧HTTP/配置/parser/mock成功数据及孤儿200类型已删除；认证后的Library当前只返回明确503且零Storage socket，不等于Storage功能完成。
- Scheduler `975dee59…`：新键同名create冲突以409写入持久receipt并可重启重放；普通/race各139项的owner验收见progress。
- Artifact来源保持真实：BFF消费的Capability artifact仍来自`7f89a267…`，Scheduler artifact仍来自`92bf9e7e…`，与各自新runtime release的canonical contract字节相同；没有伪造重新生成。
- BFF `cd1c260…` pin上Root已重跑真实IAM准入→BFF 7/7、Capability→BFF 8/8、Scheduler→BFF 11/11、System/BFF/Agent HTTP组合PASS、首次无session OAuth 15/15，自有资源均清理；OAuth runner独立复审0 P1/P2、Root scripts 563/563及56 subtests，脚本提交待发布。三条旧owner smoke的用户准入是明确标记的固定wire stub，不是IAM事实源；Agent在Scheduler链仍是deterministic receipt stub。真实Agent执行、Storage与provider推理按后续Wave闭环。

## 当前验证证据

以下是W0B退出时的历史组合证据，不冒充W1B当前结果；W1B逐命令与资源快照见`docs/progress.md`：

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

BFF Library有意只声明403/503，Redocly报告1个无2xx的warning（exit0）；未为消除警告保留假200或放宽规则。Root仍以`w1b-iam.json`为精确**状态集合**门：5 active / 11 broken / 1 illegal；当前`cd1c260…`的真实IAM/BFF 7/7、Capability/BFF 8/8、Scheduler/BFF 11/11、System组合PASS及首次OAuth 15/15已复验；OAuth带hint logout的旧401由IAM测试host JWKS回环修复，无hint HTML确认分支仍待1J真实HTTP。Scheduler smoke使用本机唯一owned RFC1918 IPv4/32绑定response-drop proxy，BFF upstream仍loopback，未修改hosts/resolver或共享服务。

全仓静态差距仍是实际待办；历史W0B为112项/1 unverified，W1B本提交候选实测为130项/0 unverified（exit 1）；不得写成全仓质量门全绿。
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

1. Root 已有真实IAM/BFF、System/BFF/Agent、Capability/BFF及Scheduler/BFF隔离组合入口，位于`scripts/e2e/`。它们不等于全仓组合 runner；旧 `verify-ten-repository-full.sh` / `run_stage2_owner_health.py` 仍保持暂停且只诊断退出。
2. `EDGE-WEB-IAM-DIRECT` 仍是唯一非法旁路；剩余11个 broken edge 仍然是真实未完成项，不会因 owner pin 前移而自动激活。BFF→System即使有真实HTTP smoke，generated contract仍未完成，所以保持broken。
3. 全仓组合 E2E、发布镜像、生产组合 manifest 和 SLO 尚未验收；Root 静态治理或单个 smoke PASS 不冒充这些证据。
