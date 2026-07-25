---
artifact: wave-child-prd-and-architecture-spec
version: "1.0"
created: 2026-07-25
status: draft-awaiting-user-review
parent: 2026-07-25-platform-web-session-target-architecture-design.md
scope: wave-0-repository-toolchain-contract-documentation-foundation
implementationAuthorized: false
---

# Wave 0：Repository、Toolchain、Contract 与 Documentation Foundation

## 0. 文档定位与复审结论

本文是 Kokoro Production Delivery Program 的 Wave 0 子 PRD 与技术设计。它只建立后续 Wave 可以安全
依赖的工程地基，不重写 Platform、Web、Session 或 GA 的业务行为。

本文批准后才允许调用 `superpowers:writing-plans` 生成精确实施计划；在书面批准前，禁止删除 gitlink、
生成根 lock、迁移 Docker build context 或修改任何运行时代码。

建议复审顺序：§0、§2、§3、§4、§5、§6、§8、§11、§15、§18、§20。

本 Wave 的一句话结论：

> 将四个 pinned 子仓精确导入一个真正的 polyglot Monorepo，在不改变业务和 GA 行为的前提下，建立唯一
> workspace/lock、确定性 contract、根 CI、架构依赖门与当前事实型 INDEX；只有 fresh clone 能完全复现，
> 才允许关闭旧仓写入口。

### 0.1 已裁决事项

1. 采用 pinned snapshot import，不合并四套完整 Git 历史，不使用 subtree，不继续长期 submodule。
2. Wave 0 保留 `kokoro-agent/`、`kokoro-platform/`、`kokoro-session/`、`kokoro-web/` 路径；最终
   `apps/services/workers/packages` 移动留给对应领域 Wave，Wave 8 清零旧路径。
3. 根仓成为唯一写入、PR、CI、Release 和依赖锁事实源；旧 remote 只保留只读历史。
4. JavaScript/TypeScript 只允许根 pnpm workspace 与根 `pnpm-lock.yaml`；Python 只允许根 uv workspace
   与根 `uv.lock`。
5. 当前 wire contract 的语义和 17 个 generated outputs 保持不变；Wave 0 增加 consumer inventory、确定性 digest、
   orphan 检查和锁定依赖，不在本 Wave 引入第二套 JSON Schema/protobuf 真源。
6. INDEX 只描述已经存在的代码现实。目标架构继续由 Parent Spec 描述，不能提前把 Session billing、
   GA Skill/Provider 或 Platform PostgreSQL 写成“已经落地”。
7. 不引入 Turborepo/Nx。当前规模下 pnpm 原生 workspace、显式根任务和完整 CI 更容易证明；只有未来 CI
   时间达到已定义阈值，才通过独立 ADR 引入增量构建系统。
8. TypeScript 固定 5.9.3，不在生产地基中采用 2026-07-08 刚发布且尚无稳定编程 API 的 TypeScript 7。
9. Prisma 6/MySQL 是 Wave 1 前唯一有期限的 Foundation 例外；Prisma 7/PostgreSQL 18 与 Platform schema
   clean replacement 同波完成，禁止在 Wave 0 偷做数据迁移。
10. Wave 0 触及 GA 的仓库形态、Python 版本、lock、Docker 与 CI，但不触及 GA runtime 行为。
11. 整个 cutover 是一个 protected merge transaction：内部 review commits 允许分层，但禁止 partial merge、
    单独 cherry-pick 或 squash；`main` 只能看到全部 required gate 通过的最终 green head。

### 0.2 唯一需要所有者确认的法律事实

四个来源仓和根仓均没有受跟踪 License 文件。实施前必须由仓库所有者确认四仓代码属于同一 Kokoro
项目可合并的自有内部代码，并在 provenance 中登记为批准的内部 LicenseRef；Agent 不得猜测 MIT、Apache
或其他开源许可。若存在第三方或不同权属代码，Wave 0 在导入前停止。

## 1. PRD：问题、用户与价值

### 1.1 当前问题

当前根仓看似能联动四个目录，实质仍是四套仓库、四套依赖、浮动远端 CI 和本机隐式文件的拼装：

- 根 gitlink 固定了 commit，但根 contract CI 又 checkout 远端 `main`，验证对象不是同一个代码状态。
- Platform pinned commit 比远端 main 超前五个 commit，新机器无法从 origin 恢复当前根 pin。
- Session Dockerfile 依赖被 `.gitignore` 忽略的 `pnpm-lock.yaml` 和 `pnpm-workspace.yaml`；干净 clone
  无法复现本机构建。
- TS、Vitest、Zod、Node types、Node runtime、Python runtime 和 lockfile 分裂。
- 子仓 workflow 导入普通目录后不会被 GitHub 执行；不建根 CI 会静默丢失测试门。
- Contract 虽然已有单源和确定性生成器，但消费者路径硬编码、CI 注释错误、PyYAML/pytest 未锁、没有
  机器可读 consumer ownership。
- 根仓和 Platform 没有 INDEX；Web 根 INDEX、README、CURRENT、CODEBASE_MAP 已有客观失真。
- Docker build context 都从子目录开始，删除子 lock 后会绕过或看不到根 lock。

这些问题不先解决，后续 Platform、Session、Web、Commerce 和 Job 重写会在不同依赖图与非确定 CI 上
并行推进，任何“测试通过”都不能证明同一候选版本可上线。

### 1.2 目标用户

- 开发者和 Coding Agent：一次 clone、一次 install、根命令即可获得完整、受约束的代码图。
- 架构 Owner：可以机器发现 public root、越界 import、过期豁免和失真 INDEX。
- CI/Release：只验证当前 Monorepo commit，输出可追溯 lock、contract 和 import digest。
- 后续 Wave Owner：可以在稳定目录、单一 lock、明确 contract consumer 和真实验证入口上 clean replace。
- 运维：Docker 和 smoke build 不依赖本机 ignored 文件、子仓缓存或浮动 remote。

### 1.3 核心用户故事

| ID | 用户故事 | 优先级 |
|---|---|---|
| W0-US-01 | 作为开发者，我从 fresh clone 不运行 submodule 命令即可安装和验证整个项目 | P0 |
| W0-US-02 | 作为 Reviewer，我能证明导入目录与四个 pinned tree 字节来源一致 | P0 |
| W0-US-03 | 作为 CI，我只验证当前 commit，不从 sibling remote 拼装浮动代码 | P0 |
| W0-US-04 | 作为依赖维护者，我只修改根 catalog/lock 即可原子升级受控依赖 | P0 |
| W0-US-05 | 作为 contract owner，我能看到每个生成物、消费者、owner 和兼容策略 | P0 |
| W0-US-06 | 作为架构 owner，我能阻止 deep import、非法依赖、cycle 和过期豁免 | P0 |
| W0-US-07 | 作为代码 Agent，我能从最近 INDEX 读到当前真实边界和验证命令 | P0 |
| W0-US-08 | 作为运维，我能从根 context 构建现有镜像且不发送 secret/缓存到 daemon | P0 |
| W0-US-09 | 作为 GA owner，我能证明 Wave 0 前后 graph/prompt/tool/runtime 行为未改变 | P0 |

## 2. 当前事实基线

### 2.1 Git 与来源快照

设计调查基线 commit：`730c59747c987ea48b9e8d0c70653e601a2a88d9`。它不是未来机械导入的 parent；
批准 Spec、实施 Plan 与 provenance 形成后，真正 parent 按 §6.2 单独记录。

| Path | Origin | Pinned commit | Tree | Archive SHA-256 | Remote 状态 |
|---|---|---|---|---|---|
| `kokoro-agent` | `LordFoxFairy/kokoro-agent` | `18b394dc3df019244875e643c142c2b08b9db708` | `b06557b5876125f2a014bc6b9597bb7ac9a30780` | `670927a78d57bef29a4a11ff6782960ae117cc526b0c88af3a234154c0f78340` | 与 origin/main 一致 |
| `kokoro-platform` | `LordFoxFairy/kokoro-platform` | `d30a16a782aca0fe131acbe8cbfbbd63fdf1b989` | `4093ce419d57089b5128ff1783a41fc6bc1733b8` | `d43330451610cfea414e9256dc640a09be2fcd727446ed99f01b000c885392c5` | 本地超前 origin/main 5 commit |
| `kokoro-session` | `LordFoxFairy/kokoro-session` | `4f4aa3defc5cce79be58c447d7f053c6204ef48f` | `55ea2b5d6c50eb172e5eb1cedf6b09f7b7526bca` | `32d8d5fd8db3cdae8a03e6d375cb66483be67abaf0ebe7da9cab438518218d7a` | 与 origin/main 一致 |
| `kokoro-web` | `LordFoxFairy/kokoro-web` | `5a3a0c4cb72ba80ba19dd335824e504119f7ef4b` | `fa2286484ca485eb532fc0a4f9df990b5a24d677` | `284579091d5b62e5d49116099eb58d272879b0009578d9d281db7e0a59c42277` | 与 origin/main 一致 |

四个受跟踪工作树均干净，共约 1,101 个 tracked files、6.5 MB；无 nested gitlink、Git LFS 或 tracked
symlink。四个目录存在大量 ignored 本机文件，因此导入必须来自 `git archive <pinnedCommit>`，禁止直接
复制 working tree 后删除 `.git`。

### 2.2 工具链与 lock 岛

| Surface | 当前 | 问题 |
|---|---|---|
| Platform | pnpm 11.2.2、TS 5.9、Vitest 2、Zod 3、Node types 22、独立 pnpm lock | 与 Session/Web 测试栈分裂 |
| Session | package-lock + 本机 ignored pnpm lock/workspace、TS `^5.6`、Vitest 4、Zod 3、Node types 20 | 两套 lock 已真实解析出不同 tsx patch |
| Web | 独立 pnpm workspace/lock、Next 16.2.6、React 19.2.4、Vitest 4.1.7、Zod 3 | 根命令与 lock 不共享 |
| Agent | Python >=3.11、Pyright/Mypy 3.11、独立 uv lock、孤立 6 行 package-lock | 与目标 Python 3.12 分裂 |
| Root | 无 Node/Python manifest、版本文件或 lock | 无统一安装入口 |

### 2.3 Contract 基线

当前 `contract/spec/*.yaml` 是真实单源；`contract/generate.py` 生成 17 个 generated outputs：16 个代码
outputs（Agent 5、Session 6、Web 4、Hub 1）和 1 个 documentation output（`contract/README.md`）。基线验证为：

```text
python3 contract/check.py                 OK — 17 generated outputs
python3 -m pytest contract/tests -q       23 passed
```

保留优点：输出字节确定、Python 使用严格 Pydantic、TypeScript 使用严格 Zod、已有 golden test。

必须修复：consumer roots 硬编码；无 output ownership；CI 仍写 14 mirrors；Hub 已是消费者但 CI 未 checkout
Platform；Python 工具未锁；Zod 4 会破坏一参数 `z.record` 和部分旧类型 API。

### 2.4 INDEX 与文档基线

现有 28 份 INDEX：Agent 4、Session 4、Web 20、Platform 0、Root 0。Platform 有 8 个 package、多个
process/migration 入口却完全无局部架构地图；Web 有许多组件 INDEX，却缺两个 App deployable root INDEX。

客观失真包括：

- 根 README 仍称三仓/四仓独立 CI，引用不存在的 contract 和测试脚本。
- CURRENT 未指向 2026-07-25 Umbrella Spec 与 Production Program。
- docs README 仍禁止 PostgreSQL，与已批准目标冲突。
- CODEBASE_MAP 仍以 submodule、旧工具版本和旧 Web 分裂为事实。
- `kokoro-web/INDEX.md` 仍描述已消失的 Next/React 大版本分裂和业务 DB 直连。

仍准确描述现有代码、但与未来目标冲突的 INDEX 不得提前改写，例如 Session billing 和 GA skills；它们在
对应业务 Wave 与代码同波清理。

## 3. 目标、非目标与退出指标

### 3.1 目标

1. 单一、可追溯、可恢复的 Git 与 PR 权威。
2. 单一 pnpm workspace/lock 与单一 uv workspace/lock。
3. 当前所有 package、App、Service 与生成契约可从根安装、检查、测试和构建。
4. Contract source、consumer、generated output、digest 和兼容策略全部可机器审计。
5. 根 CI 不依赖远端 main、本机 ignored 文件、未锁 pip/npm/npx 或 nested workflow。
6. 建立最小但真实的 INDEX/dependency governance，不制造文档噪音。
7. 为后续 clean rewrite 建立 dependency exceptions 的期限与清理 Wave。
8. 在 Node 24/Python 3.12 上证明 GA、Session、Web、Platform 当前基线没有行为回归。

### 3.2 非目标

- 不修改 Site、Commerce、Credit、Payment、Subscription、Model 或 Session 状态机。
- 不移除 Session billing/Hub/Model 业务逻辑；属于 Wave 3。
- 不移动 GA Provider、Capability、Artifact 职责；属于 Wave 5。
- 不把 Platform 变为模块化 Core/PostgreSQL；属于 Wave 1/2。
- 不创建 Job、Artifact、Operation、Studio、Model Gateway 等空包或空 INDEX。
- 不移动至最终 `apps/services/workers/packages` 目录。
- 不建立发布到 npm/PyPI 的版本体系；所有 workspace package 当前均 private/internal。
- 不引入增量构建平台、Changesets、微服务框架或第二个 contract 仓库。
- 不运行真实付费模型测试作为普通 PR gate。

### 3.3 Wave 0 完成指标

| 指标 | 目标 |
|---|---|
| Gitlink | `160000` entry 为 0，`.gitmodules` 不存在，nested `.git` 为 0 |
| Fresh clone | `--no-local` clone 后不执行 submodule 命令即可完成所有 required gate |
| JS lock | 只有根 `pnpm-lock.yaml` 和根 `pnpm-workspace.yaml` |
| Python lock | 只有根 `uv.lock` |
| 其他 lock | `package-lock.json`、yarn/bun lock、nested pnpm/uv lock 为 0 |
| Package manager declaration | 只有根 `package.json#packageManager`；nested declaration 为 0 |
| Runtime | Node 24.18.0、pnpm 11.17.0、Python 3.12.13、uv 0.11.32 |
| TS policy | 受控 package 全部引用 catalog；无未批准 major/patch 漂移 |
| Contract | 16 个代码 outputs + 1 个文档 output 全、无 orphan、生成两次一致、digest 稳定 |
| INDEX | 首批 48 个受管 root 全登记；所有已有 INDEX 已登记；新增 boundary INDEX 完整 |
| Dependency | deep import、deny edge、cycle、过期豁免均阻断 CI |
| CI | 不 checkout sibling remote、不调用未锁 pip/npm ci/npx、不依赖嵌套 workflow |
| Docker | 四个当前受跟踪 Dockerfile 从根 context + 根 lock 构建 |
| GA 行为 | runtime source 行为 diff 为 0；Python 3.12 前后同一 suite 与 smoke 均通过 |

## 4. 方案比较与架构裁决

### 4.1 Repository 方案

| 方案 | 判断 | 原因 |
|---|---|---|
| Pinned snapshot import | 采用 | 精确保留当前 tree，切换最小，根 PR/lock/contract 可原子修改 |
| Git subtree full history | 拒绝 | 引入四套无关历史与 rename 噪音，且项目不再需要 pull/split |
| Git subtree squash | 拒绝 | 与 snapshot 结果近似，却错误暗示未来保持 subtree workflow |
| 继续 submodule | 拒绝 | 无法形成单 lock、单 PR、当前 commit CI 与统一 release provenance |
| filter-repo 合并历史 | 拒绝 | 收益低，历史冲突与审核成本高；旧 remote/bundle 已可追溯 |

### 4.2 工具链编排方案

采用 pnpm 原生 workspace + uv workspace + 显式根脚本：

- pnpm 原生提供 workspace protocol、catalog、单 shared lock、cycle failure、allowBuilds 和 frozen install。
- uv workspace 原生提供每 member 自己的 `pyproject.toml`、根单 lock 与 `--package` 运行。
- 当前约 15 个 TS package 和 1 个 Python package，全量 CI 成本尚低于引入 Turbo/Nx 的治理成本。
- 根任务按 package name/role 显式编排；不得使用无界 nested `pnpm -r` 或 `--if-present` 隐藏缺失脚本。
- 当 clean CI p95 超过 15 分钟或 package 数超过 40，再以独立 ADR 评估 affected graph/remote cache。

### 4.3 Contract 方案

采用“保留当前语义单源，补齐治理”，拒绝在 Foundation 同时迁移 contract 格式：

- 当前 YAML 是唯一 source，不增加相同 wire 的 JSON Schema/protobuf 副本。
- 新增 machine-readable consumer inventory，生成器 output set 必须与 inventory 完全相等。
- 新增 contract digest、orphan generated file scan、strict/optional/nullable 负向测试。
- Zod 4 只做等价生成迁移，必须证明生成前后 wire fixtures 与运行时拒绝语义一致。
- 后续新增内部 RPC 时按边界使用 protobuf；HTTP/browser JSON 使用 OpenAPI/JSON Schema。只有真实消费者出现时
  才建立该 source family，不预建空目录。
- 当前 custom YAML 在对应 runtime contract clean replacement 时删除，不保留永久兼容层。

## 5. 目标仓库与 Workspace 结构

Wave 0 退出时：

```text
Kokoro/
  INDEX.md
  package.json
  pnpm-workspace.yaml
  pnpm-lock.yaml
  pyproject.toml
  uv.lock
  .node-version
  .python-version
  .npmrc
  .dockerignore

  config/
    repository/
      imported-snapshots.yaml
      toolchain-policy.yaml
    architecture/
      index-roots.yaml

  contract/
    spec/
    consumers.yaml
    generate.py
    check.py
    tests/

  scripts/
    architecture/
      check-index-coverage.ts
      check-dependencies.ts
      check-python-dependencies.py
      check-toolchain.ts

  docs/reports/evidence/wave-0/
    evidence.yaml

  kokoro-agent/       # 普通目录，过渡路径
  kokoro-platform/    # 普通目录，过渡路径
  kokoro-session/     # 普通目录，过渡路径
  kokoro-web/         # 普通目录，过渡路径
```

规则：

- 不创建空 `apps/`、`services/`、`workers/`、`packages/`。
- `kokoro-platform/package.json` 保留为真实 Platform composition package，但删除其无界 `pnpm -r` 编排。
- `kokoro-web/package.json` 若仅承担旧 workspace 聚合命令则删除；根 package 接管其职责。
- root workspace 显式包含 Platform composition/leaves、Session、两个 Web App 和 Web shared packages。
- workspace 内部 package 依赖必须使用 `workspace:`，绝不回退 registry 同名包。
- 根 scripts 是开发和 CI 唯一正式入口；子 package 只定义自己的局部任务。

## 6. Pinned Snapshot Import 与 Provenance

### 6.1 导入前硬门

1. 根仓与四个来源仓 tracked worktree 全部 clean。
2. 来源 HEAD、根 gitlink pin、provenance commit 三者相等。
3. 对四个 pinned commit 创建统一归档 tag，并确保 remote 可解析。
4. `kokoro-platform/d30a16a` 必须先推送到归档 ref；不能只存在开发机 `.git`。
5. 每仓创建包含归档 tag 可达历史的离仓 Git bundle，记录 SHA-256；bundle 不提交根仓。
6. 记录 tree、archive digest、tracked file count、origin、License classification 和 baseline evidence。
7. 在独立根 worktree 实施；原四个来源 checkout 在 fresh clone gate 前保持不动。
8. 机械导入的直接 parent 与批准 Spec/Plan commit 已冻结；从设计调查基线到直接 parent 之间如发生任何
   gitlink pin、contract source 或来源 remote 变化，全部 provenance 与 baseline evidence 重做。

归档 ref 建议统一为：

```text
refs/tags/kokoro-monorepo-cutover-2026-07-25
```

Remote tag 必须受保护；若托管平台不支持不可变 tag，则以 bundle digest 和访问控制作为第二恢复锚。

### 6.2 Machine-readable provenance

`config/repository/imported-snapshots.yaml` 至少包含：

```yaml
schemaVersion: 1
designBaselineCommit: 730c59747c987ea48b9e8d0c70653e601a2a88d9
approvedSpecCommit: PENDING_REVIEW
cutoverParentCommit: PENDING_IMPLEMENTATION
cutoverCommit: PENDING_IMPLEMENTATION
cutoverRef: refs/tags/kokoro-monorepo-cutover-2026-07-25
sources:
  - id: kokoro-agent
    path: kokoro-agent
    origin: https://github.com/LordFoxFairy/kokoro-agent.git
    commit: 18b394dc3df019244875e643c142c2b08b9db708
    tree: b06557b5876125f2a014bc6b9597bb7ac9a30780
    archiveSha256: 670927a78d57bef29a4a11ff6782960ae117cc526b0c88af3a234154c0f78340
    archiveCommandVersion: 1
    trackedFileCount: 150
    licenseRef: LicenseRef-Kokoro-Internal-Proprietary
    ownershipAttestation:
      attestedBy: PENDING_REVIEW
      authority: repository-owner
      attestedAt: PENDING_REVIEW
      attestationRef: PENDING_REVIEW
      scope: source-tree-and-history
    archiveTag: kokoro-monorepo-cutover-2026-07-25
    bundleSha256: PENDING_IMPLEMENTATION
    bundleStorageRef: PENDING_IMPLEMENTATION
    bundleRetentionUntil: PENDING_IMPLEMENTATION
    bundleVerifiedAt: PENDING_IMPLEMENTATION
    bundleVerifiedBy: PENDING_IMPLEMENTATION
    bundleRestoreTestDigest: PENDING_IMPLEMENTATION
```

其他三仓使用 §2.1 冻结值。`approvedSpecCommit` 与 ownership attestation 在实施计划开始前清零；所有
`PENDING_IMPLEMENTATION` 在 import commit 前清零。Git tree hash 是内容权威，archive hash 只是传输证据。
Archive digest 的标准命令固定为来源仓同一 Git toolchain 下执行：

```bash
git --version
git -C <source> archive --format=tar <pinned-commit> | sha256sum
```

Provenance 记录 Git version、操作系统、命令版本与 stdout digest；不得因环境产生不同 archive bytes 就修改
tree 权威。Bundle 至少保留至 Wave 9 上线后 180 天，并在另一 checkout 实际 clone/checkout archive tag。

### 6.3 机械导入事务

1. 从每个 pinned commit 使用 `git archive` 输出到系统临时 staging。
2. 对 staging tar 计算并比对 §2.1 archive SHA-256。
3. 删除四个 gitlink 和 `.gitmodules`。
4. 将 staging tree 放回相同 `kokoro-*` 路径并 stage。
5. 写 tree 后验证每个 prefix tree 等于来源 `commit^{tree}`。
6. 机械 import commit 不包含格式化、依赖升级、ignored 文件、文档改写或源码移动。

导入 commit 后的强制断言：

```bash
test "$(git rev-parse HEAD:kokoro-agent)" = b06557b5876125f2a014bc6b9597bb7ac9a30780
test "$(git rev-parse HEAD:kokoro-platform)" = 4093ce419d57089b5128ff1783a41fc6bc1733b8
test "$(git rev-parse HEAD:kokoro-session)" = 55ea2b5d6c50eb172e5eb1cedf6b09f7b7526bca
test "$(git rev-parse HEAD:kokoro-web)" = fa2286484ca485eb532fc0a4f9df990b5a24d677
test ! -f .gitmodules
test -z "$(git ls-files -s | awk '$1 == 160000 {print}')"
test -z "$(find kokoro-agent kokoro-platform kokoro-session kokoro-web -name .git -print -quit)"
```

### 6.4 Remote 退休顺序

只有以下全部通过后才允许将旧仓 archive/read-only：

- 根仓 `--no-local` fresh clone 验证。
- 根 frozen pnpm/uv install。
- contract、TS、Python、integration、Web build、Docker build/smoke 全部通过。
- 新 root required checks 已配置到 branch protection。
- 归档 tag 与 bundle 在另一机器验证可恢复。
- 旧仓 README/description 指向根仓，旧 CI/Release/写权限关闭。

关闭旧仓不是删除旧仓；历史、issue 和 release evidence 保留只读。

## 7. 根工具链与版本策略

### 7.0 Compatibility patch 边界

工具链升级允许的 source change 仅限让既有行为在新 API/compiler/runtime 下继续成立：

- 不改变业务状态机、公开 HTTP/status/error、持久化格式、wire accept/reject、鉴权或幂等语义；
- 每个非生成 source diff 必须在 Evidence 中绑定升级前失败、最小修复、owner 与回归测试；
- 不允许借 lint/type error 顺手重命名领域、移动职责、重排事件或扩大输入；
- 若正确修复必须改变业务/contract 语义，当前 cutover 停止，将问题移入对应 Wave 子 Spec；
- GA 在此基础上仍执行 §13 的更严格用户通知与双环境行为对比。

唯一允许的公开技术边界 clean replacement 是把 Zod 原始 `error.issues/message` 替换为 Kokoro 自有、稳定的
`ValidationError` DTO（HTTP 400、`request.invalid`、规范化 field path、stable issue code）。第三方错误消息、
stack 或完整 issue shape 从此不是公开 contract；合法/非法输入集合必须保持不变。系统未上线，不保留 Zod 3
raw-error 兼容层。

### 7.1 冻结版本

| Family | Wave 0 pin | 策略 |
|---|---|---|
| Node.js | `24.18.0` | LTS exact patch；`.node-version`、CI、Docker 一致 |
| pnpm | `11.17.0` | `packageManager` exact；CI/Docker 同版本 |
| TypeScript | `5.9.3` | 成熟稳定线；全仓唯一 |
| Vitest | `4.1.10` | 全仓唯一 |
| Zod | `4.4.3` | 全仓唯一，做等价 runtime migration |
| `@types/node` | `24.13.3` | 全仓唯一 |
| Next.js / eslint-config-next | `16.2.11` | 两个 App 同 patch |
| React / React DOM | `19.2.8` | 两个 App 同 patch |
| Python | `3.12.13` | `>=3.12,<3.13` + `.python-version` exact |
| uv | `0.11.32` | CI/开发 pin exact |
| Prisma | `6.19.3` | Wave 1 前 named legacy catalog；禁止新增用法 |
| ESLint / `@eslint/js` | `9.39.5` | 全仓唯一稳定 major |
| typescript-eslint | `8.65.0` | 与 TS 5.9/ESLint 9 同组验证 |
| tsx | `4.23.1` | Node service dev/runtime tool |
| `@vitest/coverage-v8` | `4.1.10` | 与 Vitest exact patch 一致 |
| Prettier | `3.9.6` | 仅 formatting，不作架构 gate 替代品 |

这些 pin 是 2026-07-25 Foundation baseline，不是“永远不升级”。以后由单独 dependency PR 修改 catalog、
lock、SBOM 和完整验证；package 不得私自改 major/minor。

### 7.2 为什么暂不使用 TypeScript 7

TypeScript 7 是新的 Go 实现，性能方向正确，但 7.0 尚未提供稳定编程 API；typescript-eslint 等工具仍需要
旧 compiler API 并可能要求并行安装 TypeScript 6 compatibility package。Kokoro 当前依赖 ESLint、Next
tooling、Compiler API dependency scan，本 Wave 的目标是消除分裂，不是制造第二套 compiler。

升级条件：TypeScript 7 提供稳定 API，Next/typescript-eslint/编辑器主链正式支持，单一 compiler 可完成
typecheck、lint 与 dependency scan，并通过独立兼容矩阵。满足后单独 ADR，不混入业务 Wave。

### 7.3 根 pnpm policy

根 `pnpm-workspace.yaml` 承担：

- leaf/package inventory；
- default catalog 与 named `legacy-prisma6` catalog；
- `allowBuilds` 明确白名单；
- shared workspace lock；
- workspace cycle hard fail；
- strict peer dependency；
- 24 小时 minimum release age；
- exotic transitive dependency 阻断；
- isolated node linker；
- catalog 未使用项清理。

Canonical registries 固定为 npm 官方 registry 与 PyPI official simple index；lock generation/CI 使用显式、
干净配置，不读取开发机全局 `.npmrc`、uv/pip config。企业代理或地区镜像只能作为不写入 lock 的受控
transport cache，必须验证 upstream integrity，不能成为 committed source authority。

受控依赖包括 TypeScript、Vitest/coverage、Zod、Node types、Next、React、ESLint/typescript-eslint、tsx、
Prettier、Prisma。它们在 package manifest
中必须使用 `catalog:` 或批准的 named catalog；普通业务 adapter 依赖不机械进入 catalog。

Prisma 例外必须有 owner、reason、expiry、removeByWave=1。Wave 0 禁止新增 Prisma schema、Client import 或
MySQL-specific behavior。

### 7.4 根 uv policy

根 `pyproject.toml` 是 non-package workspace root：

- member 只有当前 `kokoro-agent`；
- root dependency group 拥有 contract/foundation 的 PyYAML、pytest 等工具；
- Agent 保留自己的 runtime/dev dependencies；
- 根 `uv.lock` 锁定所有 workspace dependency；
- Agent `requires-python`、Pyright、Mypy 统一 3.12；
- 安装统一使用 `uv sync --all-packages --all-groups --locked`；运行统一使用
  `uv run --no-sync --package kokoro-agent ...`；contract/foundation group 同样显式选择且 `--no-sync`；
- CI 另用 wheel/isolated smoke 防止 Agent 偷用只声明在 root 的 Python dependency。

当前 Agent lock 全部指向本机配置带入的 Aliyun mirror。根 lock 必须迁回 canonical PyPI source；迁移报告
区分“source URL 改变但 version/hash 相同”和“version/artifact hash 改变”，后者按 runtime drift 审核。

### 7.5 Atomic lock cutover

旧 lock 只可在本地迁移阶段作为解析证据，不能与根 lock 一起成为合并态权威。一个不可拆分的
`Authority Switch Set` 必须同时完成：

- 生成根 `pnpm-lock.yaml`、根 `uv.lock`；
- 删除 Platform/Web/Session nested pnpm workspace/lock；
- 删除 Session/Agent package-lock；
- 删除 Agent nested uv.lock；
- 更新 Docker、scripts 和 CI 不再读取子 lock；
- frozen install 与二次 lock check 后工作树无 diff。

所有 workspace package 的 Prisma `postinstall`/`prebuild` 隐式 codegen 同波删除。根 install 只安装依赖；
随后运行已锁、显式、固定顺序的 `codegen:legacy-prisma`，为每个现有 schema 注入明显假的非生产 DSN，
校验 expected output set，并要求第二次运行 working tree clean。CI、Docker 与本地使用同一入口；不得要求
真实数据库或 secret 才能完成 dependency install/codegen。

`Authority Switch Set` 在 review history 中优先保持为一个 commit；若因文件量必须拆分，它仍属于同一个
protected cutover PR，禁止 partial merge/cherry-pick，`main` 只接收最终 green head。

根 lock 不允许从空状态盲目重解：

- uv 以 Agent 旧 `uv.lock` 作为 preference seed，再加入 root workspace/Python 3.12 约束；
- pnpm 以三个 tracked lock 与 Session tracked package-lock 生成迁移输入，按 importer/snapshot 完整性合并；
- 生成 machine-readable `dependency-migration` evidence，逐 consumer 记录 direct/transitive package 的
  old→new version、source、integrity 和 reason；
- 除 runtime/catalog/Zod/Vitest/Node/Python 强制变化外，非计划 dependency drift 默认 hard fail；确需变化的
  每项有 owner、理由、compat test 和 expiry；
- 任一 GA runtime dependency version/source/integrity 漂移都视为 Agent 行为风险，在应用前单独通知用户，
  并通过 §13 的旧/新环境 deterministic corpus。

## 8. Contract Foundation

### 8.1 不变量

1. `contract/spec/` 是当前 wire 唯一 source。
2. Generated files 永不手改。
3. Generator 运行两次字节完全一致。
4. Consumer inventory 的 generated path set 与 generator build output set 必须相等。
5. 带 generated header、但不在 inventory 的 orphan 文件阻断 CI。
6. Source digest、generator version、output digest 可被 Release Evidence 引用。
7. Zod 4 migration 不改变字段 optional/nullable、strict unknown-field、enum 或 error semantics。
8. Agent/Session/Web/Hub 四类 consumer 必须在同一 commit 编译和测试。

Contract digest 算法固定为 SHA-256：按 repo-relative UTF-8 path bytes 升序，对每个 source、inventory、
generator 文件依次写入无符号 64-bit big-endian path length、path bytes、content length、原始 content bytes；
禁止换行归一化。Generator identity 使用 tracked `contract/generate.py` blob hash，schema/inventory version
分别进入 tuple。按同一算法分别输出 `sourceDigest`、`generatorDigest`、`consumerInventoryDigest`、
`generatedOutputDigest` 和包含前四者的 `contractBundleDigest`，写入 machine-readable JSON evidence。仓库保存
golden digest fixture，防止实现语言或拼接边界改变算法。

### 8.2 `contract/consumers.yaml`

每个 contract set 记录：

```yaml
schemaVersion: 1
contractSets:
  - id: runtime-wire-v1
    sources:
      - contract/spec/control.yaml
      - contract/spec/events.yaml
      - contract/spec/streams.yaml
      - contract/spec/http.yaml
      - contract/spec/storage.yaml
    producerOwners: [runtime-contract]
    compatibility: clean-replace-before-launch
    consumers:
      - package: kokoro-agent
        language: python
        generatedRoot: kokoro-agent/src/kokoro_agent/contract
        outputs: [__init__.py, control.py, events.py, storage.py, streams.py]
      - package: kokoro-session
        language: typescript
        generatedRoot: kokoro-session/src/contract
        outputs: [control.ts, http.ts, session-events.ts, storage.ts, streams.ts, wire-events.ts]
      - package: "@kokoro/web-user"
        language: typescript
        generatedRoot: kokoro-web/apps/user/src/contract
        outputs: [control.ts, event-names.ts, http.ts, session-events.ts]
      - package: "@kokoro/hub"
        language: typescript
        generatedRoot: kokoro-platform/kokoro-hub/src/contract
        outputs: [storage.ts]
    sourceImpact:
      contract/spec/control.yaml:
        - kokoro-agent/src/kokoro_agent/contract/control.py
        - kokoro-session/src/contract/control.ts
        - kokoro-web/apps/user/src/contract/control.ts
```

`contract/README.md` 仍由 generator 生成，因此作为 documentation output 独立登记。Generator docstring、
generated header 的正式再生成命令和 CI 中旧“3 repos/14 mirrors”文字必须同波改成根锁命令与 17 outputs，
不得留下独立仓入口。

`sourceImpact` 必须完整覆盖每个 source→output 精确边；示例只展示一个 source。Checker 用它计算 diff impact
roots，不能只依赖整个 contract-set 的粗粒度 consumer list。

### 8.3 Zod 4 等价迁移门

已知必须修改：一参数 `z.record`、移除/变更的内部 Zod type API，以及当前 Platform Kit 的
`zod-to-json-schema`。后者接收 Zod 4 schema 时可能静默生成 `{}`，现有只验证 OpenAPI path 的测试无法发现。
因此 Zod 4 migration 是全仓 schema migration，不只覆盖 17 个 contract outputs。实施必须：

- 先固定现有 valid/invalid golden fixtures；错误只冻结 Kokoro `ValidationError` DTO 的 status/code/path/
  stable issue code，不冻结 Zod 原始 message 或 issue object；
- 修改 generator source，再重生成，禁止手修 17 镜像；
- 对 strict unknown、optional vs nullable、nested object、record key/value、discriminated union 做负向测试；
- Session/Web/Hub 不得存在第二个 Zod major；
- 删除 `zod-to-json-schema`，统一使用 Zod 4 native JSON Schema，冻结输出 dialect 与 OpenAPI normalization；
- 每个 Platform HTTP package 保存 representative request/response schema golden，断言 required/optional、
  `additionalProperties`、number/string bounds 和 refs；任何 `{}` request/body schema hard fail；
- 对代表 endpoint 实际注入缺字段、额外字段、错误类型与越界值，证明 HTTP 拒绝语义未变化；
- `contract/check`、consumer compile、consumer unit、cross-runtime fixture 全过；
- 输出内容允许因 Zod 4 API 改变，但 wire accept/reject truth table 必须不变。

### 8.4 后续 contract 演进

Wave 0 只建立治理，不冻结未来业务 schema。后续 Wave：

- 同步 JSON/RPC contract 先改 source + compatibility fixtures；
- 逐 consumer 迁移必须在同一 Monorepo PR 内可见；
- 新内部 RPC 使用标准 IDL，但不要求浏览器 JSON 强行走 protobuf；
- source family 只在第一个真实 producer/consumer 出现时创建；
- clean replacement 后删除旧 source、生成物、imports 和 inventory entry。

## 9. INDEX 与 Architecture Governance

### 9.1 两级 root 模型

- `boundary root`：deployable、package、contract、持久化或运维边界，参与跨 root dependency gate。
- `component root`：已有局部 INDEX 的复杂内部组件，继承最近 boundary root 的跨界规则。

首批受管 boundary roots 共 22 个：

```text
.
contract
scripts
deploy
ops
kokoro-agent
kokoro-session
kokoro-platform
kokoro-platform/kokoro-platform-kit
kokoro-platform/kokoro-site
kokoro-platform/kokoro-user
kokoro-platform/kokoro-model
kokoro-platform/kokoro-credit
kokoro-platform/kokoro-payment
kokoro-platform/kokoro-hub
kokoro-platform/kokoro-platform-admin
kokoro-platform/kokoro-litellm
kokoro-web
kokoro-web/apps/user
kokoro-web/apps/admin
kokoro-web/packages/i18n
kokoro-web/packages/tsconfig
```

登记 26 个已有 component roots：Agent execution/hitl/skills/worker，Session billing/http/relay/store，以及
Web user 下现有 18 个 component INDEX。总计首批 48 roots。

规则：所有现存 INDEX 必须登记；不是所有目录都要 INDEX。自动发现新的 package、Python project、process、
Next App、Prisma schema/migration 或 deployment root 时，禁止被根 `.` 假覆盖，必须创建 boundary entry。

### 9.2 Manifest schema

`config/architecture/index-roots.yaml` 是机器 inventory。每个 entry 至少包含稳定 ID、path、kind、INDEX、
owners、boundary、language、signals、dependency policy 和 verification argv。

稳定 ID 不随目录移动；路径 repo-relative，不允许绝对路径或 `..`；verification 使用 argv 数组，禁止任意
shell string。豁免必须有唯一 ID、精确 scope、owner、reason、tracking、introduced/expiry、removeByWave。

豁免最长 90 天，14 天前 warning，到期 hard fail；禁止 `** -> **` 或永久全仓豁免。每个 Wave exit 使用
`--forbid-exemptions-through-wave N` 清零本 Wave 承诺删除的豁免。

### 9.3 INDEX 模板

每份 INDEX 使用固定 front matter：

```markdown
---
architectureIndex: 1
rootId: service.session
owners:
  - "@LordFoxFairy"
---
```

正文必有：职责、非职责、公开边界、调用方与依赖、数据所有权与事件、Runtime/安全、幂等/失败/恢复、
扩展位置与禁止依赖、当前有效陷阱、验证。

Manifest 拥有可机器验证的路径和命令；INDEX 解释语义。历史演进在 Git/ADR，不在“当前陷阱”长期保留。

### 9.4 `check-index-coverage.ts`

全量模式检查：

- YAML schema、ID/path/index 唯一性；
- root、INDEX、owner、signal、verification cwd 存在；
- 所有 INDEX 已登记；所有自动发现 boundary root 已登记；
- front matter 与 manifest 一致，必填章节完整；
- Markdown 相对链接存在；
- exemption 未过期且 scope/owner/tracking 完整；
- package/process/migration/deployment 不被根假覆盖。

Diff 模式只在 public export、contract/schema、router/transport、migration、process/deployment entry、owner、
dependency rule 或跨 root rename 改变时要求 INDEX 同 PR 更新。普通内部实现、测试、样式和文案不触发，
避免机械 touch 文档。

### 9.5 `check-dependencies.ts`

Wave 0 可可靠证明：

- TypeScript 使用 TypeScript 5.9 Compiler API 的 `ts.resolveModuleName`，按所属 tsconfig、package exports、
  workspace protocol、path alias 和 barrel re-export 解析静态 import/export、字面量 dynamic import、require；
- Python 使用 stdlib AST helper，明确处理 src-layout、relative import、distribution→module mapping 与 namespace；
- workspace declared dependency 与源码 import 对齐；
- 跨 package 只能走 public export，禁止 deep import；
- boundary edge 必须在 allowlist，跨 root cycle 阻断；
- type-only import 仍算架构 edge；
- 非字面量跨 root dynamic import 默认拒绝；
- generated/test/fixture exclusions 只能来自 manifest 分类。

所有看起来指向仓内 package/root、但 resolver 无法解析的 import 必须 hard fail，禁止当 external dependency
静默略过。`generated/`、Prisma client/package、`.next/`、fixtures、tests 等分类必须在 manifest 明确登记；
自动发现器不得把 generated Prisma `package.json` 升级为伪 boundary root。

负向 fixtures 除普通 deep import/cycle 外，必须包含 tsconfig alias、package exports、barrel re-export、
type-only、Python relative/src-layout/namespace、unresolved internal import、generated package 和非字面量 dynamic
import。脚本可调用成熟 resolver/graph library，但 `check-dependencies.ts` 保持统一 policy/报告入口。

脚本不能假装证明 HTTP/Redis/MCP、env 装配、反射插件或 raw SQL。它们由 contract consumer inventory、
integration test、INDEX owner review 和后续 Wave 的运行时 gate 证明。

## 10. 当前事实与目标事实的文档治理

Wave 0 必须重写：

- Root `README.md`：真实 Monorepo clone/install/verify/deploy 入口。
- Root `INDEX.md`：deployable、truth source、依赖方向、根命令。
- `docs/CURRENT.md`：Parent Spec、Production Program、launch/readiness reports 成为当前主线。
- `docs/README.md`：移除与已批准目标冲突的 PostgreSQL 禁令，明确目标未落地状态。
- `docs/CODEBASE_MAP.md`：普通目录 Monorepo、真实 package/deployable、根验证命令、INDEX 链接。
- `kokoro-web/INDEX.md`：移除失效版本分裂和业务 DB 直连描述。
- 新增缺失的 20 个 boundary/root INDEX，并登记已有 28 个。
- 新增 `.github/CODEOWNERS`，覆盖 root INDEX、architecture config/scripts、contract、所有 boundary INDEX 与
  exception 修改；manifest owner 与 CODEOWNERS path ownership 必须通过一致性 gate。
- ADR-007 标记 superseded；新增 true Monorepo snapshot import ADR。

Wave 0 不得重写成目标完成态：

- Platform README 仍可描述当前 MySQL/小进程实现，但必须降级为 current implementation 并链接目标 Spec。
- Session billing INDEX 继续描述当前代码，Wave 3 删除职责时同波更新。
- GA skills INDEX 继续描述当前代码，Wave 5 迁出时同波更新。
- 不能写“Platform 已 PostgreSQL”“Session 已无商业逻辑”“GA 已无 Provider”等假事实。

## 11. Root CI 设计

### 11.1 原则

- 一次 checkout 当前根 commit；禁止 sibling remote checkout。
- GitHub Actions 与第三方 action 固定 immutable commit SHA，并注释 release tag。
- Node/pnpm/Python/uv 使用 §7 精确版本。
- `pnpm install --frozen-lockfile`、`uv lock --check`、
  `uv sync --all-packages --all-groups --locked`；后续命令全部 `uv run --no-sync`。禁止未锁 `pip install`、
  `npm ci` 和 `npx`。
- 初始阶段全仓 gate，不做 affected skip；避免 dependency graph 尚未可信时漏测。
- `index-roots.yaml` 中每个 package/deployable 必须绑定至少一个 required job；CI 校验 coverage 无遗漏，
  `@kokoro/i18n` 运行自身 typecheck/test，`@kokoro/tsconfig` 以 compile fixtures 验证 Node/Next variants。
- required job 不把缺依赖、无 Docker daemon、无数据库或 silent skip 当成功。
- real-provider/付费测试只允许受控 manual/scheduled/RC，不在 fork PR 暴露 secret。

### 11.2 Required jobs

| Job | 内容 | 失败语义 |
|---|---|---|
| `foundation` | topology、single-lock、version、catalog、INDEX、dependency、dead path | 任一漂移阻断 |
| `contract` | generate check、golden、inventory、orphan、digest、二次生成 clean | 任一消费者漂移阻断 |
| `ts-platform` | Platform lint/typecheck/unit + current integration prerequisites | 无 skip |
| `ts-session` | Session lint/typecheck/unit + Redis/Mongo integration | 服务不可用失败 |
| `ts-web-user` | lint/typecheck/unit/build | build 不可省略 |
| `ts-web-admin` | lint/typecheck/unit/build + Auth Prisma generate | 不直连业务 DB |
| `python-agent` | Ruff、Pyright、pytest、wheel isolated smoke | Python 3.12 only |
| `cross-runtime` | fake-model Agent↔Session contract/E2E、namespace negative | 不走真实付费模型 |
| `images` | 四个当前 Dockerfile 根 context build + Platform 七 service/migration role + Session/Agent/Web bounded smoke | ignored 文件依赖失败 |
| `security-foundation` | secret、dependency、license、action pin、Docker context/SBOM scan | 无 silent allow |

Heavy chaos、trace、real model、load、DR 在后续 Wave/RC 运行。现有 `verify-all.py` 的 SKIP 汇总只能作本地
辅助，不能替代 required evidence。

### 11.3 Branch protection 与旧 CI 切换

根 CI 合并前先在 feature branch 验证 job；切换 main 时：

1. Root workflow 就绪。
2. 删除/禁用嵌套 Agent/Session/Web workflow 与旧 root contract remote checkout。
3. 新 required checks 加入 branch protection。
4. 旧 required check 名称移除。
5. 推一个 no-op documentation PR 证明 protection 不可绕过。

Ruleset 同时启用 CODEOWNERS review：修改 architecture policy/exception、contract source/inventory、root lock、
boundary INDEX 或 provenance 时，必须获得对应 owner approval。Ruleset/config snapshot 与 no-op PR 进入
Wave 0 Evidence，而不是只在人工 checklist 里声称完成。

## 12. Docker、Compose 与脚本入口

### 12.1 Root build context

单 root lock 意味着所有当前受跟踪 Dockerfile必须以仓库根为 context，通过 `-f` 选择 Dockerfile。每个
Dockerfile：

- 先 COPY 根 manifest、workspace、lock 与所需 leaf manifests；
- frozen filtered install；
- 再 COPY 目标 source；
- 生产 runtime 不依赖 package manager 写入 home；
- 不从 ignored 本机文件补 manifest；
- 现有 process behavior 不变。

根 `.dockerignore` 必须先于 context 切换建立，至少排除 `.git`、`.env*`（保留 example）、node_modules、
`.venv`、cache、coverage、tmp、IDE、截图、数据库卷和 local workspace。

### 12.2 Script 规则

- 所有正式命令从根执行并按 package name 过滤。
- 删除 `npm run`、`npm ci`、`npx`、直接 `.venv/bin/python` 与子 cwd lock 假设。
- Prisma generate 使用已锁 workspace binary；不得运行时下载。
- `codegen:legacy-prisma` 显式顺序覆盖所有当前 schema/生成目录，禁止 package lifecycle hook 隐式执行。
- Root package scripts 不使用 `--if-present` 隐藏缺失 gate。
- Platform composition package 只跑自身 source/test；不递归触发整个 workspace。
- Compose config 与 Docker build smoke 都属于 Wave 0 required evidence。

Web user Docker 显式设置并验证以根仓为 tracing 边界的 `outputFileTracingRoot`；测试不得假设 standalone
继续位于旧 `apps/user/server.js`。Build gate 解析真实 standalone manifest/路径，runtime image 按实际
`kokoro-web/apps/user/server.js` 或生成结果 COPY/CMD，并通过容器 HTTP readiness/smoke 证明。

### 12.3 Legacy deploy 声明

当前 Compose 与四个受跟踪 Dockerfile 仍是 MySQL、七个 Platform 小进程和旧 service topology；Admin
当前没有独立 Dockerfile。Wave 0 只使既有镜像从根 lock 可复现，
并明确标记为 pre-target/非 production topology；不得在本 Wave伪装完成 Platform 模块化 Core。真正 deployment
shape 在领域 Wave 与 Wave 8/9 收口。

## 13. GA 保护边界与通知

本 Wave 会改变 Agent 的 Python 3.11→3.12、root uv lock、Docker build context 和 CI，属于“Agent 打包/
运行环境”变更；实施前必须通知用户，但不需要重新讨论 GA 产品架构。

明确禁止修改：

- LangGraph/DeepAgents graph、prompt、assembly、tool、Handoff 和 effect 行为；
- opaque `namespace` 语义或新增 Site/User/Workspace 第二身份轴；
- Mongo checkpoint/memory 行为；
- Redis dispatch/event wire 语义；
- Model、Provider、Capability、Artifact 业务行为；
- GA runtime source 中为了 Python 3.12 以外的顺手重构。

允许的 Agent 变更只有：

- snapshot 进入根仓；
- `requires-python`、Pyright/Mypy target；
- root uv workspace/lock；
- Docker root context 和 Python 3.12 image；
- 根命令/CI/INDEX 路径；
- Zod 不涉及 Agent，contract Python 生成物必须保持等价。

GA 证明拆成两类，不能用 source diff 冒充行为证明：

1. 以机械 import commit 为 base，`kokoro-agent/src` 的非生成 runtime source diff 必须为空。
2. 在 Python 3.11 + 旧 Agent lock 与 Python 3.12 + 根 lock 上运行同一 deterministic fake-model corpus；固定
   seed、clock 和 IDs，规范化 timestamp/随机 ID 后，对比 graph selection、tool calls、HITL、checkpoint、
   memory、raw event kind/order/payload 和 terminal result；同时审计完整 uv dependency diff。

若 Python 3.12 或 dependency migration 暴露真实兼容问题，需要单独报告、最小修复、用户知情并追加测试，
不能静默夹带；若需要改变 GA runtime 语义，则停止 Wave 0 并另行复审。

## 14. Security 与 Supply Chain

- pnpm dependency build script 默认拒绝，只允许 `allowBuilds` 白名单。
- 根 lock 必须提交并 frozen；tarball integrity mismatch hard fail，不自动刷新 checksum。
- transitive exotic source 阻断；direct git/tar dependency 必须有 owner、commit/digest 和例外记录。
- 新发布 dependency 至少延迟 24 小时解析；紧急安全更新走双人 review 的显式例外。
- CI cache 只缓存 package manager store，不缓存 `node_modules`/`.venv` 作为构建事实；fork job 不写 trusted cache。
- Docker context 不含 secret、`.git`、本地 workspace 和数据库数据。
- Action 固定 commit SHA；Release Evidence 记录 action、runtime、lock 和 image digest。
- Node/Python/uv build base 与 Redis/Mongo/MySQL/MinIO 等 CI service image 均固定 immutable digest；人类可读
  tag 只作注释。更新 digest 必须走 dependency/security review，Evidence 记录 registry、platform 和 digest。
- Provenance bundle 存在访问控制存储，不进入 repo，不包含 secret 或本机 untracked 文件。
- Root dependency scanner 与 secret scanner 在 fresh clone 和 CI 都执行。

## 15. Cutover Series、事务边界与恢复

### 15.1 Reviewable commit series

所有节点位于同一个 protected cutover PR；下列是 review DAG，不是可独立 merge 的发布序列：

```text
provenance-freeze
  → exact-snapshot-import
    → workspace-scaffold
      → node-python-runtime-compat
        → ts-test-tooling-compat
          → next-react-framework-patches
            → zod4-schema-compat
              → authority-switch-set
                → contract-and-architecture-governance
                  → docs-and-evidence-finalization
```

1. `docs/provenance-freeze`：来源、attestation、archive ref、bundle evidence。
2. `repo/exact-snapshot-import`：只做四个 exact snapshot 与 gitlink/.gitmodules 切换。
3. `build/workspace-scaffold`：根 versions/manifests/policy/dockerignore；旧 lock 仅作为 branch 内迁移输入。
4. `build/node-python-runtime-compat`：Node/Python runtime compatibility 与旧/新 GA corpus。
5. `build/ts-test-tooling-compat`：TS/Node types/Vitest/ESLint/tsx/Prettier，独立取证。
6. `build/next-react-framework-patches`：Next/React patch 与两个 App build/HTTP smoke。
7. `build/zod4-schema-compat`：全仓 Zod 4/OpenAPI/contract 等价适配。
8. `build/authority-switch-set`：根 lock、nested lock/workspace 删除、root Docker/scripts、root CI、nested
   workflow 删除在同一原子切换 set 成立。
9. `contract-and-architecture-governance`：consumer/digest/orphan、48 roots、INDEX/dependency/CODEOWNERS。
10. `docs-and-evidence-finalization`：README/CURRENT/CODEBASE_MAP/ADR、fresh clone、Evidence manifest。

整个 PR 禁止 partial merge、单独 cherry-pick 和 squash；保留 mechanical import checkpoint 与 provenance
lineage。Branch 内中间 commit 不视为 release candidate，`main` 只能接收 final green head。合并前生成并
演练一个按 DAG 逆序的 revert bundle；不得宣称任一中间 toolchain/Zod commit 可在 main 上单独回退。

### 15.2 失败恢复

| 失败点 | 恢复 |
|---|---|
| Import 前 | 删除临时 staging/worktree；根和四来源不动 |
| Archive/tree digest 不匹配 | hard stop；不得 stage 或重算“新期望值”掩盖 |
| Mechanical import 后、workspace 前 | 保留未合并 branch 或 revert import commit；旧 remote 不退休 |
| Toolchain/Zod 失败 | 在未合并 cutover branch 按 DAG 修复/回退；不单独把中间状态送入 main |
| Root lock 失败 | 不提交半套 lock；保留旧 lock 仅在未合并 branch恢复分析 |
| CI/镜像失败 | main 不切 required check，旧 remote 保持 active |
| 合并后需回退 | 执行已演练 revert bundle，逆序恢复 Foundation/import 与 `.gitmodules`/gitlinks；禁止 reset |
| Remote 误归档 | 解除 archive 或从 bundle 恢复 archive tag，再恢复 gitlink |

Wave 0 不含 schema/data migration，因此 Git 拓扑回滚不与数据库回滚耦合。

### 15.3 并发写入冻结

从 provenance freeze 到 root fresh-clone gate 通过期间：

- 四个旧仓 main 禁止新写；紧急修复先提交来源仓、更新 pin/provenance 后重新开始 import。
- Root contract、lock、`.gitmodules`、workspace manifest、INDEX manifest 各自只有一个 owner。
- 并行 worker 只可在不重叠文件树工作；根 lock、contract source、barrel export 串行。

## 16. 验证策略

### 16.1 Pre-import baseline

- 四仓 clean/head/tree/remote reachability。
- 当前各仓真实 lint/typecheck/unit/integration/build。
- Contract 17 generated outputs/23 tests。
- GA fake-model worker、namespace negative、checkpoint/memory、contract suite。
- Docker/Compose 记录 current pass/fail；Session clean-checkout build failure登记为已知缺陷，不伪造 baseline pass。

### 16.2 Foundation static gates

- topology/no-gitlink/no-nested-git；
- single-lock/no-npm-yarn-bun/nested-workspace；
- single root `packageManager` declaration；
- exact runtime/catalog/exception；
- contract generate/inventory/orphan/digest；
- INDEX coverage/full+diff/dead link；
- TS/Python dependency direction/cycle/deep import；
- forbidden remote checkout/npm/npx/Node22/Python3.11/old commands scan；
- secret/context scan。

### 16.3 Language与功能 gates

| Surface | Static | Unit | Integration/Build | 负向 |
|---|---|---|---|---|
| Platform | ESLint/TS | 全 package tests | current MySQL integration + composition | illegal cross-package import |
| Session | ESLint/TS | relay/store/http/billing existing | Redis/Mongo/S3 relevant integration | missing ignored lock must not matter |
| Web user | ESLint/TS | 现有 component/engine | Next production build | contract invalid event |
| Web admin | ESLint/TS | 现有 Admin tests | Prisma generate + Next build | business DB deep import |
| Agent | Ruff/Pyright | full pytest | wheel + fake worker smoke | Site/User/Workspace second axis |
| Contract | generator static | 23+ golden | all consumers compile | unknown/nullable/idempotent generation |

### 16.4 Fresh-clone certification

最终证据必须来自与开发 checkout 不共享 Git object database 的 `--no-local` clone：

1. 不存在 `.gitmodules`，不运行 submodule update。
2. 安装固定 Node/pnpm/Python/uv。
3. frozen pnpm/uv install。
4. 重跑 lock/generator，`git diff --exit-code`。
5. 执行 required CI 等价命令。
6. 从 root context 构建镜像并 bounded smoke。
7. 验证旧 remote 不参与 build/test。
8. 保存 root commit、lock digest、contract digest、image digest 和报告索引。

### 16.5 `Wave0EvidenceManifest`

`docs/reports/evidence/wave-0/evidence.yaml` 是完成声明的机器入口，不把仓库外事实只留在人工勾选中。
至少记录：

```yaml
schemaVersion: 1
wave: 0
root:
  cutoverParentCommit: <sha>
  cutoverCommit: <sha>
  verifiedCommit: <sha>
digests:
  pnpmLock: <sha256>
  uvLock: <sha256>
  contract: <sha256>
  images: {}
commands: []
ci:
  runUrl: <url>
  requiredJobs: []
repositoryControls:
  rulesetSnapshotDigest: <sha256>
  codeownersDigest: <sha256>
  noOpProtectionPr: <url>
sourceArchives: []
dependencyMigration:
  report: <repo-relative-path>
security:
  secretScan: {}
  dependencyScan: {}
  licenseScan: {}
  sbom: {}
exceptions: []
```

每个 command entry 记录 argv、cwd、runtime/tool version、started/finished、exit status、report path/digest 和
CI run URL；每个外部 archive/bundle/ruleset evidence 记录 verifiedAt/By/reference。报告内不得复制 secret、
生产数据或完整环境变量。Manifest schema、引用文件、digest 与 completed status 由 `foundation` job 校验。

## 17. INDEX/Dependency 负向 Fixture 矩阵

| Gate | 必须通过 | 必须失败 |
|---|---|---|
| Root discovery | 48 个 root 唯一登记 | 新 package.json 无 boundary root |
| INDEX identity | rootId/owner/sections 对齐 | front matter 不匹配 |
| Links/signals | 路径存在 | 删除 process entry 但 INDEX 未改 |
| Diff trigger | 内部实现无需 touch INDEX | export/router/migration 改动未同步 INDEX |
| TS dependency | public export edge | deep import、deny edge、cycle |
| Python dependency | 合法包 import | 非法跨 boundary import |
| Dynamic import | 登记插件入口 | 非字面量跨 root import 无豁免 |
| Exception | 精确未过期并可见 | 过期、无 owner、宽泛 scope |
| Contract impact | source+consumer roots 同步 | source 改但 consumer INDEX 未同步 |
| CI source | 当前 root commit | workflow 含 sibling remote main |

## 18. Wave 0 交付物

### 18.1 Repository/Toolchain

- 四目录 ordinary tracked tree；`.gitmodules` 删除。
- `config/repository/imported-snapshots.yaml`。
- true Monorepo ADR、旧 ADR superseded。
- 根 Node/pnpm/Python/uv manifests、versions、locks、policies。
- nested lock/workspace/package-lock 清零。
- root scripts 与 root Docker context。

### 18.2 Contract

- `contract/consumers.yaml`。
- generator/check 的 inventory、orphan、digest gate。
- Zod 4 等价生成与跨 consumer evidence。
- 16 个代码 outputs 与 1 个文档 output 仍全部由 source 生成。

### 18.3 Architecture/Docs

- 根 INDEX、20 个缺失 boundary/root INDEX、28 个现有 INDEX 登记。
- `config/architecture/index-roots.yaml`。
- `docs/templates/INDEX.md`。
- `check-index-coverage.ts`、`check-dependencies.ts` 与 Python AST helper。
- CURRENT、README、CODEBASE_MAP、Web INDEX、ADR 更新。
- 精确、到期、绑定 Wave 的 legacy exemptions。

### 18.4 CI/Evidence

- 根 required CI jobs。
- nested workflow 与 floating remote checkout 删除。
- fresh-clone report、toolchain/lock/contract digest、Docker build/smoke report。
- `Wave0EvidenceManifest`、dependency migration diff、security/license/SBOM、ruleset/CODEOWNERS/no-op PR evidence。
- Wave 0 completion report 与仍开放的后续 Wave exception list。

## 19. 风险与缓解

| 风险 | 概率 | 影响 | 缓解 |
|---|---:|---:|---|
| Platform pin 远端不可达 | 已发生 | 高 | import 前 archive tag + external bundle hard gate |
| ignored 文件污染 import | 高 | 高 | 只使用 git archive，tree/digest 双验证 |
| Root lock 引发大量解析变化 | 高 | 高 | 分 family 升级、exact catalog、atomic cutover、consumer tests |
| Zod 4 改变 accept/reject | 中 | 高 | golden truth table、source-only regeneration、跨 consumer compile |
| Python 3.12 暴露兼容问题 | 中 | 高 | 独立 commit、完整 GA suite、非生成 runtime diff gate |
| Nested workflow 静默失效 | 必然 | 高 | 同一 cutover series 建 root CI、branch protection 验证 |
| Root Docker context 泄露 secret | 中 | 高 | `.dockerignore` 先行、context content test、secret scan |
| INDEX 数量造成维护噪音 | 中 | 中 | 两级 roots、signal-trigger diff、非机械建图 |
| Dependency checker 误称运行时图 | 中 | 高 | 明确证明边界，runtime 交给 contract/integration |
| Legacy exemption 永久化 | 中 | 高 | 90 天、removeByWave、expiry hard fail |
| TS7 过早采用产生双 compiler | 高 | 中 | 暂留 TS5.9，成熟后独立 ADR |
| 旧 remote 过早只读影响回滚 | 中 | 高 | fresh-clone/branch protection/bundle 恢复后才退休 |

## 20. 验收标准与 Go/No-Go

### 20.1 P0 Exit Checklist

- [ ] 所有者完成四来源代码权属/内部 LicenseRef 确认。
- [ ] Platform pinned commit 已存入 remote archive ref，四仓 bundle digest 已验证。
- [ ] 四个 imported prefix tree 与 §2.1 完全一致。
- [ ] gitlink、`.gitmodules`、nested `.git` 为 0。
- [ ] 根单 pnpm/uv lock 成立，其他 package manager lock 为 0。
- [ ] §7 exact versions 与 catalog/exception policy 全过。
- [ ] Zod 4 wire accept/reject truth table 与基线等价。
- [ ] Contract 16 个代码 outputs + 1 个文档 output、consumer inventory、orphan、digest、determinism 全过。
- [ ] 首批 48 roots 登记，所有 INDEX/links/signals/owners 全过。
- [ ] Dependency negative fixtures 与 exemption expiry gate 全过。
- [ ] `.github/CODEOWNERS` 与 manifest owner 一致，boundary/policy/exception owner review ruleset 已验证。
- [ ] Root required CI 只验证当前 commit且 branch protection 已生效。
- [ ] Platform/Session/Web/Admin/Agent/cross-runtime 全部 required evidence 无 silent skip。
- [ ] 所有 Dockerfile root context build/smoke，Compose config 通过。
- [ ] `--no-local` fresh clone certification 通过。
- [ ] README/CURRENT/CODEBASE_MAP/ADR/INDEX 不再把旧仓或未来目标写成错误事实。
- [ ] GA 非生成 runtime 行为 diff 为 0；Python 3.12 regression 为 0。
- [ ] `Wave0EvidenceManifest` schema/digest/reference 全过，secret/dependency/license/SBOM scan 无未接受 P0/P1。

任一 P0 未完成，Wave 0 状态保持 active，不能开始 Wave 1 业务实现。

### 20.2 No-Go 条件

- 来源 commit/tree/digest 任一无法验证。
- 未解决的代码权属或 License 不明确。
- Root lock 需要长期保留 nested lock 才能构建。
- 必须依赖 ignored/untracked 文件、旧 remote main 或未锁下载。
- Zod/Python 升级造成未解释的 contract/runtime 行为变化。
- required job 以 skip/mock 替代真实 integration/build。
- INDEX/Dependency gate 只能靠宽泛永久 exemption 通过。
- Root context 可能包含 secret 或本地数据。
- 旧 remote 已退休但根 fresh clone/rollback 尚未证明。

## 21. 后续 Wave 接口

Wave 0 输出给后续 Wave 的不是新业务 API，而是稳定工程契约：

- Wave 1：在 Platform boundary roots、单 lock、PostgreSQL/Prisma clean rewrite exception 上工作。
- Wave 2：扩展 Catalog/Commerce/Redeem contract，并清理对应 legacy Platform package。
- Wave 3：删除 Session billing/hub/model 职责与豁免，同波更新 INDEX。
- Wave 4：创建真实 Operation/Job/Artifact/Studio roots，出现代码后才登记。
- Wave 5：迁出 GA Provider/Capability/Artifact，任何 GA runtime 行为变更继续单独通知。
- Wave 6/7：按真实 deployable/package 新增 roots 和 runtime contract。
- Wave 8：移动到最终目录、清零 `kokoro-*`、legacy deploy、旧 source 和临时 exception。
- Wave 9：以同一根命令/INDEX verification/contract digest 生成 RC EvidenceBundle。

## 22. 复审门

书面复审需要确认：

1. 同意 pinned snapshot import 与旧 remote archive/read-only 策略。
2. 同意 §7 精确工具链版本及 TS 5.9 暂不升级 TS7 的裁决。
3. 同意 Contract 保持当前语义/source，Wave 0 只补 consumer/digest/orphan/Zod4 等价治理。
4. 同意 48-root 两级 INDEX 模型和最长 90 天 exception。
5. 确认四个来源仓是同一 Kokoro 项目的自有内部代码，可登记内部 LicenseRef。
6. 同意本 Wave 触及 Agent 打包/Python/Docker/CI，但不改变 GA runtime 行为。

批准后下一步：使用 `superpowers:writing-plans` 生成
`docs/superpowers/plans/2026-07-25-wave-0-repository-contract-foundation-implementation-plan.md`，再进入隔离
worktree 和 TDD/双阶段 review。本文本身不授权直接实施。
