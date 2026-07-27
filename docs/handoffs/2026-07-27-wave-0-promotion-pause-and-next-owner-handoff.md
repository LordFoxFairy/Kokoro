# Wave 0 Promotion 暂停与下一负责人交接

> **本文件已结案，仅存史。** 暂停于 2026-07-27 解除并按 §8 恢复步骤执行完毕：runtime compatibility gate
> 5 场景全 pass、atomic promotion commit `0f30276`、干净 recursive clone 复现全绿、rollback 演练通过。
> **下面「禁止继续实现 / 尚未完成」等状态描述均已过期，不要据此行动。**
> 当前权威记录 = [Wave 0 收敛证据](../reports/evidence/wave-0/federated-repository-baseline.md)；
> 当前架构事实 = [架构梳理](../reports/2026-07-27-kokoro-architecture-survey.md)。

日期：2026-07-27  
原状态（已解除）：用户要求暂停；禁止继续实现、启动 Docker、提交 Root promotion 或推送 Root  
工作树：`/Users/nako/.config/superpowers/worktrees/Kokoro/feat/lordfoxfairy/wave-0-foundation`

本文件是短期执行交接，不替代 `docs/CODEBASE_MAP.md`、当前批准 Spec、Production Delivery Program 或相邻
`INDEX.md`。

## 1. 必须保留的系统边界

- Root 永久保留 `.gitmodules` 和四个 mode-`160000` gitlink；四个 `kokoro-*` 是独立仓库，独立拥有
  source、lock、CI、artifact、deploy、release 和 rollback。
- 跨仓只走版本化 HTTP/RPC/SSE/异步协议；禁止 sibling source import、共享进程内对象和跨服务私有 DB。
- 一个 Site 对应一个独立 Web Project/artifact；后端和 GA 共用，Platform 解析并强制 `siteId` 隔离。
- GA 只消费 opaque `namespace`；不得加入 `siteId/userId/workspaceId` 身份轴，也不得未经用户确认修改
  graph/checkpoint/control/terminal/handoff 语义。
- Root Infra 是唯一验证基础设施 authority。不得起 ad-hoc 容器；promotion 验证结束立即停止并删除测试容器，
  不删除 volumes、images 或开发数据。

## 2. Root 当前精确状态

- 分支：`feat/lordfoxfairy/wave-0-foundation`
- Root HEAD：`2a22bad397bde325816bd46c7c5950deb5f068b6`
- Root remote 仍为：`3799eea498527f5fdb012a0fe01222336e325966`
- Root 比 remote ahead 1；不要单独 push `2a22bad`，因为该 commit 的 HEAD gitlink 仍指向旧子仓，而新的
  architecture manifest 已要求新 INDEX。必须等原子 pin promotion commit 完成后一起 push。

`2a22bad feat(architecture): enforce root boundary governance` 已提交但未推送：

- 57-root architecture inventory；
- boundary/component INDEX coverage；
- fail-closed dependency checker；
- workspace package dependency 与 allowlist 对账；
- federated sibling source/config path 禁止；
- Root CI 接入 architecture tests、coverage 和 dependency entrypoint；
- 未包含任何 gitlink。

当前 **已暂存但未提交** 的候选 promotion 只有五个路径：

```text
config/repository/federated-repositories.json
kokoro-agent
kokoro-platform
kokoro-session
kokoro-web
```

不要 reset、unstage、checkout 或覆盖这五项。当前交接文档本身保持未提交，后续应在 promotion/evidence 收口时
纳入合适的 Root commit。

## 3. 四个子仓最终候选

| Repository | Branch | Final SHA | Recoverable ref | Remote CI |
|---|---|---|---|---|
| Agent | `codex/wave0-index-governance` | `e01b6eab3e4b8b9b1fc193c53590e3ca564c2b51` | `refs/tags/kokoro-wave0-foundation-2026-07-27-agent` | [30203330241](https://github.com/LordFoxFairy/kokoro-agent/actions/runs/30203330241) success |
| Platform | `codex/wave0-closeout-platform` | `fe5b755f7b1a98247f33e3318f4ade9c4ae87f18` | `refs/tags/kokoro-wave0-foundation-2026-07-27-platform` | [30203426690](https://github.com/LordFoxFairy/kokoro-platform/actions/runs/30203426690) success |
| Session | `codex/wave0-closeout-session` | `c24080c117aeafa3ec02db1700549057218baefa` | `refs/tags/kokoro-wave0-foundation-2026-07-27-session` | [30203819683](https://github.com/LordFoxFairy/kokoro-session/actions/runs/30203819683) success |
| Web | `codex/wave0-closeout-web` | `1934383ea4a72be9f2cc664af5de62b46c77c81c` | `refs/tags/kokoro-wave0-foundation-2026-07-27-web-2` | [30204922834](https://github.com/LordFoxFairy/kokoro-web/actions/runs/30204922834) success |

四个子仓工作树均 clean，HEAD 与各自 remote branch 一致；四个 annotated tag 的 peeled SHA 已远端核对。

Web 还有一个更早的 tag `kokoro-wave0-foundation-2026-07-27-web` 指向 `fdf73b5`。这是已发布的旧候选，
不得移动或删除；最终 manifest 已正确使用 `...-web-2`。

## 4. 本轮实际交付

### Agent

- 只增加 root/component architecture INDEX；无 GA runtime 语义修改。
- 主控复验：Ruff、Pyright、architecture tests `7/7`。

### Platform

- DDD seed 从错误的 `bootstrap` 移到 `interfaces/cli`；不放宽 allowlist。
- 子仓 CI 执行 repository gates、integration 和 deployment artifact build。
- Docker build context 精确保留运行时需要的 generated RPC contract mirror。
- Platform boundary INDEX 完整。
- 主控复验：lint、typecheck、repository/platform/workspace tests 共 `1,085` 通过。

### Session

- ESLint `10.8.0` / `@eslint/js 10.0.1`，普通 `npm test` 显式执行 repository contracts。
- `npm audit` 为 0 vulnerabilities；Session boundary INDEX 完整。
- 主控复验：lint、typecheck、repository contracts `4/4`，Vitest `372 passed / 27 skipped`。
- 未实现真实 Admission RPC；`legacy-admission-adapter.ts` 的 unknown/not_found 仍是后续 Wave 3 工作，不得误报完成。

### Web

- Next `16.2.12`、React/ReactDOM `19.2.8`、Auth.js beta.32、Nodemailer `9.0.3`、ESLint `9.39.5`、
  TypeScript `5.9.3`、Vitest `4.1.10`。
- Pro Components 使用支持 Ant Design 6 的 `3.1.14-5`，并完成 `ProCard` API 兼容修改。
- pnpm workspace overrides 关闭生产漏洞；production audit 无已知漏洞。
- pnpm 11 默认 24 小时发布隔离保留，仅为已评审的 Next `16.2.12` 包建立 exact-version
  `minimumReleaseAgeExclude`。见 [pnpm settings](https://pnpm.io/settings#minimumreleaseageexclude)。
- CI 按 pnpm 官方模式先运行 pinned `pnpm/action-setup`，再由 `setup-node` 建立 pnpm cache；避免 cache 初始化时
  pnpm 尚不存在。见 [pnpm CI guide](https://pnpm.io/continuous-integration#github-actions)。
- Web/User/Admin/i18n boundary INDEX 完整。
- 最终本地证据：repository `6/6`、i18n `12`、Admin `41`、User `485`（workspace 共 `538`），lint、
  typecheck、User build、Admin build 全通过。

Web 的两个历史失败 CI 应保留为诊断证据：

- `30204678382`：pnpm 11 minimum release age 阻止刚发布的 Next 安全补丁；已用 exact-version exception 修复。
- `30204813485`：`setup-node` 在 pnpm 安装前初始化 pnpm cache；已改为 pnpm 官方 action 顺序。
- `30204922834`：最终 SHA 的完整 CI success。

## 5. Root 已获得的最新静态证据

在当前 staged index pin 组合上，以下整条命令于暂停前 exit 0：

```bash
node --test scripts/architecture/*.test.mjs \
  scripts/repository/*.test.mjs \
  scripts/compatibility/*.test.mjs \
  scripts/foundation/check-evidence.test.mjs
node scripts/architecture/check-index-coverage.ts
node scripts/architecture/check-dependencies.ts
node scripts/repository/verify-federated-repositories.mjs --tree index --remote
node scripts/repository/check-generated-contracts.mjs
uv run python contract/check.py
uv run pytest contract/tests -q
git diff --check
```

结果：

- Node governance/architecture suite：`87/87`；
- INDEX coverage：`57 roots`；
- dependency boundaries：`57 roots, 13 internal package edges`；
- staged exact-pin + remote recoverable refs：4 repositories verified；
- generated contract mirrors：19 match；
- contract tests：`35/35`。

## 6. 当前 Docker 状态

暂停时 `docker ps -a` 为零容器；未启动任何 promotion runtime stack。没有删除 volume、image 或开发数据。

## 7. 尚未完成，不能宣称 Wave 0 exit

1. staged 四仓组合尚未运行本轮唯一一次 Root Infra runtime compatibility gate。
2. staged manifest/gitlink 尚未形成 atomic promotion commit。
3. 尚未生成最终 `config/repository/bom.json`。
4. 尚未从 clean recursive clone 重放 Root 与四子仓门禁。
5. Root feature branch 尚未 push，因而没有最终 Root remote CI evidence。
6. 尚未创建 Root BOM tag。
7. 尚未执行 promotion commit 的 rollback rehearsal。
8. `docs/reports/evidence/wave-0/federated-repository-baseline.md` 尚未写入最终收敛证据。

### Freeze tooling 的已知不一致

`freeze-snapshots.mjs` 当前仍服务旧 baseline：它要求 `expected-snapshots.json` 的旧四仓 commit，并使用一个共同
`archiveTag`；本轮 canonical manifest 使用每仓独立 `recoverableRef`。不要为了让 freezer 变绿而移动标签、伪造
expected baseline 或覆盖旧证据。下一负责人应二选一并补测试：

- 明确旧 freezer 只冻结历史 source baseline，promotion 以 federated manifest/verifier/BOM 为 authority；或
- 新增版本化 candidate-freeze 产物，从 `federated-repositories.json` 读取每仓 recoverableRef。

不要临时把四个独立 tag 改成 mutable 共用 tag。

## 8. 下一负责人恢复步骤

先只读核对，不要先改文件：

```bash
cd /Users/nako/.config/superpowers/worktrees/Kokoro/feat/lordfoxfairy/wave-0-foundation
git status --short --branch
git diff --cached --submodule=short
git submodule status
docker ps -a --format '{{.ID}}\t{{.Names}}\t{{.Status}}'
node scripts/repository/verify-federated-repositories.mjs --tree index --remote
```

预期：Root ahead 1；五个 staged path；四个 child HEAD 与本文件 SHA 相同；Docker 0 容器；index verifier pass。

随后顺序执行：

1. 独立 review staged manifest/gitlinks 与 `2a22bad` architecture range，修复所有 Critical/Important。
2. 从 `.github/workflows/contract.yml` 复用 fake CI env 和 Root Infra manager，运行一次 `full / ci-federated`
   compatibility gate，evidence 写入 ignored `tmp/`；必须在 `finally`/trap stop。
3. 验证后确认 `docker ps -a` 没有遗留 `kokoro-infra` 测试容器；只删除容器，不删 volumes/images。
4. runtime evidence pass 后提交 atomic candidate，例如：
   `build(repository): promote verified wave 0 pins`。
5. 立刻运行 HEAD-mode verifier；然后生成 BOM（引用该 promotion commit 与四个 exact pins、refs、protocol、
   contract/evidence digests）并补 schema/test。
6. 在 `mktemp -d` clean recursive clone 重放 gates；只删除已验证的临时 clone 目录。
7. 最终 review 后 push Root feature branch，等待精确 SHA 的 Root remote CI success。
8. 创建新的 annotated Root BOM tag，远端验证 tag object 和 peeled SHA；不得覆盖已有 tag。
9. 在第二个临时 clone 通过新 revert commit 演练 rollback，不推送 rehearsal。
10. 更新最终 evidence report；只有所有 exit gate 有新鲜证据才宣称 Wave 0 complete。

## 9. 暂停纪律

- 当前没有需要继续等待的命令；所有子代理已结束。
- 不要在默认项目目录的 `main` 重做这些工作。
- 不要修改 GA runtime。
- 不要把 payment/redeem、Site identity、Chat/Session 业务实现混入这个 promotion commit。
- Wave 0 真正退出后，按 Production Delivery Program 进入 Wave 1，再并行 Platform Identity/Site、Web Site
  artifact isolation 与 Session transport foundation。
