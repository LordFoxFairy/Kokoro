# Wave 0 Repository、Toolchain、Contract 与 Documentation Foundation Implementation Plan

> **2026-07-27 execution correction**：保留 `.gitmodules` 和四个 gitlink，四个子仓长期独立管理。
> Task 3 的 mechanical snapshot import 以及后续 single-root-lock / 删除子仓 lock/CI 的步骤全部取消，不得执行。
> 替代路径是：验证冻结 pin → 各子仓独立 feature worktree/lock/CI → root compatibility matrix 与跨仓 gate →
> 通过审核后只更新 root gitlink pin。已创建的 recovery tags/bundles 作为独立仓恢复锚点继续保留。

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将四个当前 gitlink 的精确快照导入根仓，并在不改变业务或 GA runtime 语义的前提下建立唯一根 workspace/lock、确定性 contract、INDEX/dependency governance、root CI、root Docker build 与可恢复证据链。

**Architecture:** Wave 0 是 protected clean-cut transaction，不是逐个可独立上线的小补丁。先冻结所有权、来源和可恢复锚，再机械导入；随后在同一隔离 worktree 中完成工具链兼容、原子 lock authority switch、contract/architecture governance、CI/Docker 和 fresh-clone certification。生产 Site Web Project 不属于根 workspace；`kokoro-web/apps/user` 仅是迁移期 reference source。

**Tech Stack:** Git 2.39+、Node.js 24.18.0、pnpm 11.17.0、TypeScript 5.9.3、Vitest 4.1.10、Zod 4.4.3、Next.js 16.2.11、React 19.2.8、Python 3.12.13、uv 0.11.32、Pydantic 2、PostgreSQL/MySQL（本 Wave 只跑当前实现）、MongoDB、Redis、S3-compatible storage、Docker、GitHub Actions。

---

## Plan status and hard gate

```yaml
planStatus: implementation-active
implementationAuthorized: true
gaRuntimeSemanticChangeAuthorized: false
blockingFact: null
```

仓库所有者已经确认根仓和四个来源仓均属于同一 Kokoro 项目拥有/控制、可合并的内部专有代码，Task 0 的
机器可读 attestation 已登记。Wave 0 可按本计划继续执行；`gaRuntimeSemanticChangeAuthorized` 仍为 false，且
tag push、bundle、gitlink 删除、snapshot import、root lock 生成或旧 remote 权限变更仍须通过各自后续任务门禁。

当前重验基线（2026-07-26；真正 cutover 前 Task 1 再计算）：

| Source | Commit | Tree | Archive SHA-256 | Files |
|---|---|---|---|---:|
| kokoro-agent | `18b394dc3df019244875e643c142c2b08b9db708` | `b06557b5876125f2a014bc6b9597bb7ac9a30780` | `670927a78d57bef29a4a11ff6782960ae117cc526b0c88af3a234154c0f78340` | 150 |
| kokoro-platform | `d30a16a782aca0fe131acbe8cbfbbd63fdf1b989` | `4093ce419d57089b5128ff1783a41fc6bc1733b8` | `d43330451610cfea414e9256dc640a09be2fcd727446ed99f01b000c885392c5` | 525 |
| kokoro-session | `4f4aa3defc5cce79be58c447d7f053c6204ef48f` | `55ea2b5d6c50eb172e5eb1cedf6b09f7b7526bca` | `32d8d5fd8db3cdae8a03e6d375cb66483be67abaf0ebe7da9cab438518218d7a` | 97 |
| kokoro-web | `f3936befb7ae4c219273ae9b7f4efb97cb6a1425` | `c88c4f29197fafb1158c561e1bfe8153d04e7fcc` | `202b99d74fd2720298d78df95b18f3372adf2f11c1a2751f712e8a84f0a9d047` | 329 |

当前基线门：Contract 17 outputs / 23 tests 通过；Session 362 tests、typecheck、lint 通过；Web user 484、Admin 25、
i18n 12 tests 和两 App typecheck 通过，但 i18n lint 找不到 ESLint；Platform DDD layout 因
`kokoro-site/src/bootstrap` 失败；Agent 当前被 uv 解析到 Python 3.14 且无 Mongo/Redis 服务，完整 suite 出错/等待，已人工中止。
这些都必须在 Task 1 evidence 中准确记录，不得写成绿色基线。

已确认根因（只诊断，尚未实施修复）：

- Platform：commit `3434245` 新增 `kokoro-site/src/bootstrap/seed-default-site.ts`，但自初始 DDD gate 起允许集合只含
  application/config/domain/infrastructure/interfaces。不是 Vitest 偶发；机械导入必须先保持该事实，随后 Task 6 把 seed
  composition entry 移入明确的 `interfaces/cli`（并更新 package script），而不是给所有模块宽泛放开 `bootstrap`。
- Web：`@kokoro/i18n` 声明 `eslint .`，但在 `node-linker=isolated` 下既无自身 ESLint devDependency，也无可继承的根工具
  package，因此 `.bin/eslint` 不存在；这由 Task 6 的根 catalog + leaf executable declaration修复。
- Agent：`requires-python >=3.11` 且无 exact `.python-version`，当前 uv venv 已解析为 Python 3.14；测试 fixture 又明确要求真实
  Redis/Mongo、不可达 fail-loud，故无服务运行产生大量 error并在 Mongo teardown等待。这不是 GA 语义失败；Task 1 必须用
  Python 3.11旧锁+隔离服务取得旧 corpus，Task 5再用3.12比较。

## File map

| Path | Responsibility |
|---|---|
| `config/repository/imported-snapshots.yaml` | 当前四个来源 commit/tree/archive/bundle/ownership attestation 真源 |
| `config/repository/toolchain-policy.yaml` | exact runtime、catalog、lock、legacy exception 与 registry policy |
| `config/repository/infrastructure-policy.yaml` | 每环境单 Infra、canonical identity、profiles、restart、test isolation、cleanup policy |
| `config/architecture/index-roots.yaml` | boundary/component root、owner、signals、verification、dependency policy |
| `package.json` / `pnpm-workspace.yaml` / `pnpm-lock.yaml` | 根 TS workspace 与唯一 lock authority |
| `pyproject.toml` / `uv.lock` / `.python-version` | 根 Python workspace 与唯一 lock authority |
| `.node-version` / `.npmrc` | Node/pnpm 与安装安全策略 |
| `contract/consumers.yaml` | source→generated output→consumer/owner/compatibility inventory |
| `scripts/repository/freeze-snapshots.mjs` | 导入前以 Node 标准库计算并校验 pin/tree/archive/file/origin/provenance |
| `scripts/repository/import-snapshots.mjs` | 导入前以 Node 标准库从 verified archive 机械替换 gitlink并验证 prefix tree |
| `scripts/foundation/check-toolchain.mjs` | 无安装依赖的 runtime/catalog/single-lock/lifecycle-codegen/registry policy |
| `scripts/foundation/check-evidence.mjs` | 无安装依赖的 evidence schema、digest、ref 和自引用防护 |
| `scripts/architecture/check-index-coverage.ts` | root discovery、INDEX/frontmatter/link/signal/diff gate |
| `scripts/architecture/check-dependencies.ts` | TypeScript resolver、public export、edge/cycle/declaration gate |
| `scripts/architecture/check-python-dependencies.py` | Python AST/src-layout/relative/namespace edge gate |
| `scripts/contract/check-consumers.ts` | inventory exact set、orphan、source impact、digest/golden gate |
| `docs/templates/INDEX.md` | 当前事实型 INDEX 模板 |
| `docs/reports/evidence/wave-0/evidence.yaml` | repo 内历史 commit 与外部 attestation 索引；不自引用最终 commit |
| `.github/workflows/ci.yml` | 根 required jobs，仅验证当前 commit |
| `.github/CODEOWNERS` | contract/lock/architecture/provenance/boundary owner review |
| `.dockerignore` / four existing Dockerfiles | root-context reproducible image builds |
| `docker-compose.infra.yml` / `scripts/infra/*` | 唯一 Infra lifecycle authority；所有 dev/CI/provision 入口复用 |
| `INDEX.md` + boundary `INDEX.md` files | 当前实现职责、公开边界、依赖、数据、运行与验证 |

## Chunk 1: Authorization、baseline and exact snapshot import

### Task 0: Fail-fast authorization gate

**Files:**
- Modify: `docs/superpowers/specs/2026-07-25-wave-0-repository-contract-foundation-design.md`
- Create after owner confirmation: `docs/reports/evidence/wave-0/ownership-attestation.yaml`
- Test: `docs/reports/evidence/wave-0/ownership-attestation.schema.json`

- [x] **Step 1: Record the owner decision without inventing a license**

  Required user statement: the root plus `kokoro-agent`、`kokoro-platform`、`kokoro-session`、`kokoro-web` source trees and
  histories are owned/controlled by the same Kokoro project and may be consolidated as internal proprietary source. If the answer
  is qualified or negative, stop and inventory third-party/differently-owned paths before any import.

- [x] **Step 2: Write the failing evidence-schema test**

  The schema must require `attestedBy`、`authority=repository-owner`、`attestedAt`、`attestationRef`、all five repositories and
  `licenseRef=LicenseRef-Kokoro-Internal-Proprietary`; placeholder values fail.

- [x] **Step 3: Validate the missing attestation fails**

  Run: `node scripts/foundation/check-evidence.mjs --require-ownership`

  Expected: FAIL `ownership_attestation_missing` before any state-changing task.

- [x] **Step 4: Add the owner-provided attestation reference and validate**

  Expected: PASS without copying private legal correspondence into the repository; store only an opaque approved reference.

- [x] **Step 5: Commit**

```bash
git add docs/reports/evidence/wave-0/ownership-attestation.yaml docs/reports/evidence/wave-0/ownership-attestation.schema.json
git commit -m "docs(provenance): attest source ownership"
```

### Task 0A: Establish the Infra authority before any real baseline

**Files:**
- Create: `config/repository/infrastructure-policy.yaml`
- Create: `scripts/infra/manager.mjs`, `scripts/infra/scope.mjs`, `scripts/infra/inventory.mjs`, tests
- Modify: `docker-compose.infra.yml`, `deploy/provision.sh`, `scripts/closure-up.py`
- Modify: root Infra commands/documentation that still use a non-canonical project name

- [ ] **Step 1: Write failing authority, resource and cleanup tests**

  Fixtures reject non-`kokoro-infra` official project names、Compose-auto-prefixed volume identity、missing profiles/health、dev
  auto-restart、mutable stateful image refs、whole-file secret fanout、package-owned stateful Compose、unguarded `FLUSHDB`、fixed shared
  test DB/bucket and cleanup without endpoint/prefix/lease validation. Inventory may inspect only Docker names/labels/digests/sizes.

- [ ] **Step 2: Implement one root manager without changing application/runtime semantics**

  Profiles are `platform`、`runtime`、`storage`、`model` and manager-composed `full`. Official project identity is fixed to
  `kokoro-infra`; network/volume names derive from an explicit environment scope, never Site. Local dev restart defaults off；production
  restart requires an explicit override. The manager reads the selected environment source only in the provisioning boundary, never logs
  values, and passes each process/container the minimum required variables.

- [ ] **Step 3: Implement leased logical test scopes**

  MySQL: per-run/per-context databases and restricted test user；Mongo: per-run DB；Redis: reserved DB 8–15 plus an exclusive lease until
  runtime key-prefix support exists；MinIO: per-run bucket/prefix and complete object/multipart/bucket cleanup. Every cleanup checks
  endpoint、`kokoro_test_<run>` prefix and lease token. Local stop never removes volumes；data destroy is not exposed as a normal test path.

- [ ] **Step 4: Inventory and refuse competing active authorities**

  Record the existing `kokoro`、`kokoro-infra`、`kokoro_dev_*` and `kokoro-platform_*` volume families without reading their contents.
  Refuse to start if another local stateful project is active. Do not delete/adopt volumes in this task.

- [ ] **Step 5: Re-run the manager tests and commit**

```bash
node --test scripts/infra/*.test.mjs
node scripts/infra/manager.mjs config
node scripts/infra/inventory.mjs --format summary
git add config/repository/infrastructure-policy.yaml scripts/infra docker-compose.infra.yml \
  deploy/provision.sh scripts/closure-up.py docs/superpowers
git commit -m "build(infra): establish canonical lifecycle authority"
```

### Task 1: Freeze the actual parent and baseline

**Files:**
- Create: `scripts/repository/freeze-snapshots.mjs`
- Create: `scripts/repository/freeze-snapshots.test.mjs`
- Create: `config/repository/expected-snapshots.json`
- Create: `config/repository/imported-snapshots.yaml`
- Create: `docs/reports/evidence/wave-0/pre-import-baseline.md`

- [ ] **Step 1: Write failing fixtures for drift and self-reference**

  Fixtures cover: gitlink pin differs from subrepo HEAD；tree/archive mismatch；dirty tracked worktree；unreachable archive ref；
  future/self commit field in provenance；missing ownership attestation；ignored files do not affect tracked count.

- [ ] **Step 2: Run the fixture test**

  Run: `node --test scripts/repository/freeze-snapshots.test.mjs`

  Expected: FAIL because the command does not yet exist.

- [ ] **Step 3: Implement the freezer as argv-only Git calls**

  It must execute and record exactly:

```text
git status --porcelain=v1
git ls-tree HEAD <repo>
git -C <repo> rev-parse HEAD
git -C <repo> rev-parse HEAD^{tree}
git -C <repo> remote get-url origin
git -C <repo> ls-files
git -C <repo> archive --format=tar <pin>
git ls-remote <origin> refs/heads/main refs/tags/<archive-tag>
```

  No shell-string interpolation in production code；hash raw tar bytes with Node `createHash("sha256")`；sort source IDs before
  canonical YAML output；never read `.env` or ignored worktree content.

- [ ] **Step 4: Run current package baselines through the root Infra authority**

  Use only root `docker-compose.infra.yml` with canonical project `kokoro-infra`; select the minimum required services and never start
  parallel stateful containers with `docker run`. Isolate tests using logical MySQL databases、Mongo databases、Redis namespace/keyspace
  and MinIO buckets/prefixes. Record exact current pass/fail, including Platform bootstrap layout and Web i18n lint failures. Agent
  baseline must run with its old lock and Python 3.11, not the developer's current Python 3.14. Inventory existing project/network/volume
  identities and resource use without reading data or deleting volumes. If an earlier ad-hoc run occurred, preserve it as a diagnosed
  baseline-process defect and re-run the required certification through the canonical authority before Wave 0 completion.

- [ ] **Step 5: Generate and review the provenance diff**

  Expected sources are the four rows in this plan unless the root pin changes. Any change requires updating Spec, plan baseline and
  reviewer approval; never accept `--update-expected` during cutover.

```bash
node scripts/repository/freeze-snapshots.mjs \
  --approved-spec-commit 31ed730a41ec79130ca530d6acbd3f3d9b445485 \
  --expected config/repository/expected-snapshots.json
```

- [ ] **Step 6: Commit**

```bash
git add scripts/repository/freeze-snapshots.mjs scripts/repository/freeze-snapshots.test.mjs \
  config/repository/expected-snapshots.json config/repository/imported-snapshots.yaml \
  docs/reports/evidence/wave-0/pre-import-baseline.md
git commit -m "build(repository): freeze source snapshots"
```

### Task 2: Create remote recovery anchors

**Files:**
- Modify: `config/repository/imported-snapshots.yaml`
- Create outside repo: four Git bundles in owner-approved protected storage
- Test: `scripts/repository/freeze-snapshots.test.mjs`

- [ ] **Step 1: Verify both locally-ahead repositories are remotely anchored**

  Platform and Web must be pushed to a protected archive tag before import. Agent/Session tags are also created for uniformity.

```bash
git -C <repo> tag kokoro-monorepo-cutover-2026-07-26 <pin>
git -C <repo> push origin refs/tags/kokoro-monorepo-cutover-2026-07-26
git ls-remote <origin> refs/tags/kokoro-monorepo-cutover-2026-07-26
```

- [ ] **Step 2: Create and verify external bundles**

```bash
git -C <repo> bundle create <approved-external-path>/<repo>.bundle kokoro-monorepo-cutover-2026-07-26
git bundle verify <approved-external-path>/<repo>.bundle
shasum -a 256 <approved-external-path>/<repo>.bundle
```

- [ ] **Step 3: Restore-test each bundle in a temporary directory**

  Clone from bundle, checkout the tag, verify commit/tree, then delete only the validated temporary directory. Record digest/ref/result,
  not the bundle itself, in provenance.

- [ ] **Step 4: Commit the receipts**

```bash
git add config/repository/imported-snapshots.yaml docs/reports/evidence/wave-0/pre-import-baseline.md
git commit -m "docs(provenance): record source recovery anchors"
```

### Task 3: Mechanical snapshot import

**Files:**
- Create: `scripts/repository/import-snapshots.mjs`
- Create: `scripts/repository/import-snapshots.test.mjs`
- Delete: `.gitmodules`
- Replace gitlinks with ordinary tracked trees: `kokoro-agent/`, `kokoro-platform/`, `kokoro-session/`, `kokoro-web/`

- [ ] **Step 1: Create an isolated worktree using `superpowers:using-git-worktrees`**

  Branch name: `feat/lordfoxfairy/wave-0-foundation`. Freeze writes to all four source mains for the cutover window.

- [ ] **Step 2: Write failing import transaction fixtures**

  Cover wrong archive hash、path traversal tar entry、dirty root、unexpected gitlink、partial staging、tree mismatch and cleanup on failure.

- [ ] **Step 3: Implement staging with `mktemp -d` and exact tar validation**

  The script accepts an explicit provenance path and `--dry-run`; it never copies the working trees and never deletes a broad/glob path.

- [ ] **Step 4: Run dry-run**

  Run: `node scripts/repository/import-snapshots.mjs --dry-run --provenance config/repository/imported-snapshots.yaml`

  Expected: PASS with four verified archives and no root change.

- [ ] **Step 5: Execute the import and stage only the transaction**

  Expected assertions:

```bash
staged_root_tree=$(git write-tree)
test "$(git rev-parse "$staged_root_tree:kokoro-agent")" = b06557b5876125f2a014bc6b9597bb7ac9a30780
test "$(git rev-parse "$staged_root_tree:kokoro-platform")" = 4093ce419d57089b5128ff1783a41fc6bc1733b8
test "$(git rev-parse "$staged_root_tree:kokoro-session")" = 55ea2b5d6c50eb172e5eb1cedf6b09f7b7526bca
test "$(git rev-parse "$staged_root_tree:kokoro-web")" = c88c4f29197fafb1158c561e1bfe8153d04e7fcc
test ! -f .gitmodules
test -z "$(git ls-files -s | awk '$1 == 160000 {print}')"
test -z "$(find kokoro-agent kokoro-platform kokoro-session kokoro-web -name .git -print -quit)"
git diff --check --cached
```

- [ ] **Step 6: Commit the exact import only**

```bash
git commit -m "chore(repository): import pinned source snapshots"
```

  Do not squash this mechanical commit. A later evidence commit records this already-existing SHA as
  `exactSnapshotImportCommit`; the import commit never contains its own hash.

## Chunk 2: Root workspace and runtime compatibility

### Task 4: Root runtime and policy scaffold

**Files:**
- Create: `package.json`, `pnpm-workspace.yaml`, `.node-version`, `.npmrc`
- Create: `pyproject.toml`, `.python-version`
- Create: `config/repository/toolchain-policy.yaml`
- Create: `scripts/foundation/check-toolchain.mjs`, `scripts/foundation/check-toolchain.test.mjs`
- Create: `.dockerignore`

- [ ] **Step 1: Write failing policy tests**

  Test exact runtime values, one root `packageManager`, allowed workspace paths, canonical registries, no Site Project nesting,
  no unapproved nested lock/workspace, lifecycle Prisma scripts and expiring legacy exceptions.

- [ ] **Step 2: Add the root manifest**

```json
{
  "name": "kokoro",
  "private": true,
  "packageManager": "pnpm@11.17.0",
  "engines": { "node": "24.18.0" },
  "scripts": {
    "check:foundation": "node scripts/foundation/check-toolchain.mjs && tsx scripts/architecture/check-index-coverage.ts && tsx scripts/architecture/check-dependencies.ts && python3 scripts/architecture/check-python-dependencies.py",
    "check:contract": "python3 contract/check.py && pytest -q contract/tests && tsx scripts/contract/check-consumers.ts",
    "codegen:legacy-prisma": "tsx scripts/foundation/generate-legacy-prisma.ts"
  },
  "devDependencies": {
    "tsx": "catalog:",
    "typescript": "catalog:",
    "vitest": "catalog:"
  }
}
```

- [ ] **Step 3: Add workspace/catalog policy**

  `pnpm-workspace.yaml` explicitly lists Platform composition/leaves、Session、Web reference apps/packages and uses exact catalog pins
  from Wave 0 Spec v1.3. Set `failIfNoMatch` behavior in scripts；do not use `--if-present` or unbounded `pnpm -r`.

- [ ] **Step 4: Add the non-package uv root**

```toml
[project]
name = "kokoro-workspace"
version = "0.0.0"
requires-python = ">=3.12,<3.13"
dependencies = []

[tool.uv]
package = false

[tool.uv.workspace]
members = ["kokoro-agent"]

[dependency-groups]
foundation = ["pyyaml", "pytest>=8"]
```

- [ ] **Step 5: Add `.dockerignore` before any root-context build**

  Exclude `.git`、`.env*` except examples、node_modules、`.venv`、cache、coverage、tmp、IDE、screenshots and DB volumes.
  Test the resulting Docker context manifest without reading `.env` contents.

- [ ] **Step 6: Run dependency-free policy tests and commit scaffold without locks**

  Generate any provisional root resolution only inside ignored `tmp/wave-0/` for Tasks 6-8. It is migration evidence, not a committed
  authority. The real root locks and nested-lock deletion occur together in Task 9.

```bash
node --test scripts/foundation/check-toolchain.test.mjs
git add package.json pnpm-workspace.yaml pyproject.toml .node-version .python-version .npmrc .dockerignore \
  config/repository/toolchain-policy.yaml scripts/foundation
git commit -m "build: scaffold root workspace policy"
```

### Task 5: Python 3.12 and GA zero-semantic-delta gate

**Files:**
- Modify: `kokoro-agent/pyproject.toml`
- Create: `scripts/agent/capture-runtime-corpus.py`
- Create: `scripts/agent/compare-runtime-corpus.py`
- Create: `scripts/agent/test_compare_runtime_corpus.py`
- Create: `docs/reports/evidence/wave-0/agent-runtime-baseline.json`
- Create later: root `uv.lock`

- [ ] **Step 1: Capture the old Python 3.11 + old lock corpus before deleting it**

  Through the canonical root Infra manager, ensure the shared `runtime` profile once and allocate a leased Redis DB/key scope plus a
  unique Mongo test DB; do not start isolated Redis/Mongo containers. Freeze seed、clock、IDs and fake model. Record graph selection、tool calls、HITL、checkpoint、memory、
  raw event kind/order/payload and terminal after normalization. Never include prompts containing secrets or real user data.

- [ ] **Step 2: Write comparator negative fixtures**

  Event reorder、tool arg change、checkpoint field loss、terminal change and namespace second axis must fail; timestamp/random-ID-only diff passes.

- [ ] **Step 3: Change only runtime targets**

  Set `requires-python = ">=3.12,<3.13"`、Pyright/Mypy 3.12 and `.python-version=3.12.13`. No non-generated
  `kokoro-agent/src` runtime source change is allowed in this task.

- [ ] **Step 4: Resolve root uv lock from old preference seed and canonical PyPI**

```bash
UV_NO_CONFIG=1 uv lock
UV_NO_CONFIG=1 uv lock --check
UV_NO_CONFIG=1 uv sync --all-packages --all-groups --locked
```

  Produce a direct/transitive old→new version/source/integrity report. Any GA dependency drift pauses before application and is reviewed.

- [ ] **Step 5: Run the new corpus and compare**

  Expected semantic diff: 0. If Python/dependency compatibility requires GA source behavior changes, stop and request user approval.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml uv.lock .python-version kokoro-agent/pyproject.toml scripts/agent \
  docs/reports/evidence/wave-0/agent-runtime-baseline.json
git commit -m "build(agent): pin Python 3.12 workspace"
```

### Task 6: TypeScript/test tooling compatibility

**Files:**
- Modify: all managed `package.json` files listed by `pnpm-workspace.yaml`
- Modify: TS/ESLint/Vitest configs under Platform、Session、Web
- Create: `scripts/foundation/tooling-compat.test.ts`

- [ ] **Step 1: Freeze current unit/type/lint behavior and known failures**

  Add explicit regression cases for Platform `bootstrap` classification and i18n ESLint resolution. Decide the current-truth fix:
  seed entry belongs under an approved application/bootstrap boundary or the architecture test explicitly models a bootstrap entry;
  do not weaken the test with a broad allowlist.

- [ ] **Step 2: Move shared tooling to exact root catalog pins**

  TypeScript 5.9.3、Vitest/coverage 4.1.10、Node types 24.13.3、ESLint 9.39.5、typescript-eslint 8.65.0、tsx 4.23.1、
  Prettier 3.9.6. Leaf manifests use `catalog:` and declare what their scripts actually execute.

- [ ] **Step 3: Make i18n and tsconfig packages independently verifiable**

  `@kokoro/i18n` gets resolvable ESLint and its 12 tests/typecheck/lint；`@kokoro/tsconfig` gets Node/Next compile fixtures and scripts.

- [ ] **Step 4: Run every package explicitly**

```bash
pnpm --filter kokoro-platform test
pnpm --filter kokoro-platform typecheck
pnpm --filter kokoro-session test
pnpm --filter kokoro-session typecheck
pnpm --filter @kokoro/web-user test
pnpm --filter @kokoro/admin-web test
pnpm --filter @kokoro/i18n test
```

- [ ] **Step 5: Commit**

```bash
git add package.json pnpm-workspace.yaml kokoro-platform kokoro-session kokoro-web scripts/foundation/tooling-compat.test.ts
git commit -m "build(ts): unify compiler and test tooling"
```

### Task 7: Next/React patch compatibility

**Files:**
- Modify: `kokoro-web/apps/user/package.json`, `kokoro-web/apps/admin/package.json`
- Modify as required: both App Next configs/tests
- Test: both App unit/type/lint/build and HTTP smoke

- [ ] **Step 1: Add build artifact/standalone-path assertions**

  Assert root tracing boundary and actual generated standalone server path. Do not assume old `apps/user/server.js` layout.

- [ ] **Step 2: Move Next/React to exact pins**

  Next/eslint-config-next 16.2.11、React/React DOM 19.2.8；run framework-facing tests before source compatibility changes.

- [ ] **Step 3: Apply only compatibility patches**

  No IA、auth、Session、billing or UI behavior changes. Each source change cites the failing framework test.

- [ ] **Step 4: Verify and commit**

```bash
pnpm --filter @kokoro/web-user test && pnpm --filter @kokoro/web-user typecheck && pnpm --filter @kokoro/web-user lint && pnpm --filter @kokoro/web-user build
pnpm --filter @kokoro/admin-web test && pnpm --filter @kokoro/admin-web typecheck && pnpm --filter @kokoro/admin-web lint && pnpm --filter @kokoro/admin-web build
git commit -am "build(web): pin Next and React patches"
```

### Task 8: Zod 4 wire-equivalence migration

**Files:**
- Modify: `contract/generate.py` and generated outputs only through generator
- Modify: managed package manifests and Zod-dependent source/config
- Delete: `zod-to-json-schema` usage/dependency
- Create: `contract/tests/fixtures/zod-wire-valid.json`, `contract/tests/fixtures/zod-wire-invalid.json`
- Create: `kokoro-platform/kokoro-platform-kit/test/json-schema-golden.test.ts`

- [ ] **Step 1: Freeze valid/invalid truth tables before upgrade**

  Cover strict unknown、optional/nullable、nested object、record key/value、discriminated union、bounds and stable Kokoro
  `ValidationError` status/code/path/issue code. Do not freeze raw Zod messages/issues.

- [ ] **Step 2: Upgrade Zod through the catalog and prove tests fail**

  Expected failures include one-argument `z.record` and old internal type APIs.

- [ ] **Step 3: Fix source schemas and generator only**

  Use Zod 4 native JSON Schema with explicit dialect/OpenAPI normalization. Hard-fail any representative request/body schema emitted as `{}`.

- [ ] **Step 4: Regenerate all 17 outputs twice**

```bash
python3 contract/generate.py
python3 contract/check.py
git diff --exit-code -- $(python3 contract/generate.py --list-outputs)
```

- [ ] **Step 5: Run cross-consumer and HTTP negative tests**

  All pre-upgrade accept/reject truth tables must match. If wire behavior changes, stop and move it to the owning business Wave.

- [ ] **Step 6: Commit**

```bash
git add contract kokoro-platform kokoro-session kokoro-web package.json pnpm-workspace.yaml
git commit -m "build(contract): migrate schemas to Zod 4"
```

### Task 9: Atomic lock authority switch

**Files:**
- Create: root `pnpm-lock.yaml`, root `uv.lock`
- Delete: nested `pnpm-lock.yaml`, `pnpm-workspace.yaml`, `package-lock.json`, `kokoro-agent/uv.lock`
- Modify: manifests/scripts/Dockerfiles/workflows that reference nested locks
- Create: `scripts/foundation/generate-legacy-prisma.ts`

- [ ] **Step 1: Write the failing single-authority test**

  It must fail while any managed nested lock/workspace/packageManager/lifecycle Prisma generate exists. Site Projects outside this workspace
  are out of scope and must not be classified as exemptions inside the monorepo.

- [ ] **Step 2: Generate root locks from migration seeds**

  Record every direct/transitive old→new version/source/integrity delta and reject unplanned drift.

- [ ] **Step 3: Replace implicit Prisma lifecycle hooks**

  Root `codegen:legacy-prisma` runs each current schema in fixed order with an obviously fake DSN, validates expected generated paths and
  leaves a clean second run. Wave 0 does not change Prisma schema or database behavior.

- [ ] **Step 4: Delete old authorities in the same staged set**

  Update all scripts/Docker/CI references before staging. No intermediate commit may be merged/cherry-picked.

- [ ] **Step 5: Verify frozen installs and clean regeneration**

```bash
pnpm install --frozen-lockfile
UV_NO_CONFIG=1 uv lock --check
UV_NO_CONFIG=1 uv sync --all-packages --all-groups --locked
pnpm run codegen:legacy-prisma
pnpm run codegen:legacy-prisma
git diff --exit-code -- pnpm-lock.yaml uv.lock kokoro-platform
```

- [ ] **Step 6: Commit the complete authority switch set**

```bash
git add -A
git commit -m "build: switch to root dependency authority"
```

## Chunk 3: Contract and architecture governance

### Task 10: Contract consumer inventory and digest

**Files:**
- Create: `contract/consumers.yaml`
- Create: `scripts/contract/check-consumers.ts`, `scripts/contract/check-consumers.test.ts`
- Modify: `contract/generate.py`, `contract/check.py`, `contract/README.md` generator source

- [ ] **Step 1: Write negative fixtures**

  Missing output、extra generated orphan、wrong owner/root、incomplete sourceImpact、path traversal、duplicate output、digest framing collision
  and nondeterministic generation must fail.

- [ ] **Step 2: Encode the 16 code + 1 documentation output inventory**

  Agent 5、Session 6、Web user 4、Hub 1、README 1. `sourceImpact` contains every exact source→output edge.

- [ ] **Step 3: Implement length-framed SHA-256 digests**

  Sort UTF-8 repo-relative paths, prefix unsigned 64-bit big-endian path/content lengths, hash raw bytes without newline normalization.
  Emit source、generator、inventory、output and bundle digests; add a golden fixture.

- [ ] **Step 4: Verify deterministic clean generation and commit**

```bash
pnpm exec vitest run scripts/contract/check-consumers.test.ts
python3 contract/check.py
python3 -m pytest contract/tests -q
pnpm exec tsx scripts/contract/check-consumers.ts
git diff --exit-code
git commit -am "build(contract): add consumer and digest governance"
```

### Task 11: INDEX inventory and coverage gate

**Files:**
- Create: `config/architecture/index-roots.yaml`
- Create: `docs/templates/INDEX.md`
- Create: `scripts/architecture/check-index-coverage.ts`, tests and fixtures
- Create: root `INDEX.md` and 19 other missing boundary INDEX files
- Modify: 28 existing INDEX files only to add accurate frontmatter/required current sections

- [ ] **Step 1: Encode 22 boundary + 26 component roots**

  Stable IDs、paths、kinds、owners、signals、dependency policy and argv verification. Auto-discovery must find package/project/process/
  Prisma/deploy roots and reject unregistered boundaries.

- [ ] **Step 2: Write failing coverage fixtures**

  Duplicate ID/path、missing INDEX/owner/section、bad relative link、expired/broad exemption、unregistered package/process/migration、
  root falsely covering child and public export change without INDEX update.

- [ ] **Step 3: Implement full and diff modes**

  Diff mode triggers only on public export、contract/schema、router/transport、migration、process/deploy、owner/dependency changes.

- [ ] **Step 4: Write current-truth INDEX files**

  Do not claim target architecture is implemented. `kokoro-web/INDEX.md` retains current Admin auth-schema Prisma reality and marks
  business mutations through platform-admin; Session billing and GA skills remain current until their own Waves.

- [ ] **Step 5: Verify and commit**

```bash
pnpm exec vitest run scripts/architecture/check-index-coverage.test.ts
pnpm exec tsx scripts/architecture/check-index-coverage.ts --mode full
git commit -am "docs(architecture): establish index governance"
```

### Task 12: Dependency direction gates

**Files:**
- Create: `scripts/architecture/check-dependencies.ts`, tests/fixtures
- Create: `scripts/architecture/check-python-dependencies.py`, tests/fixtures
- Modify: `config/architecture/index-roots.yaml` with precise expiring legacy edges

- [ ] **Step 1: Add all required negative fixtures**

  TS: deep import、deny edge、cycle、tsconfig alias、exports、barrel re-export、type-only、unresolved internal、generated package、
  nonliteral dynamic import. Python: relative/src-layout/namespace、illegal cross-boundary、cycle and unresolved internal.

- [ ] **Step 2: Implement TS resolution with TypeScript 5.9 Compiler API**

  Use owning tsconfig、`ts.resolveModuleName`、package exports/workspace/path alias. Any repo-looking unresolved import hard-fails.

- [ ] **Step 3: Implement Python resolution with stdlib AST**

  Explicit distribution→module and src-layout map; no `TYPE_CHECKING` escape for wrong runtime dependency direction.

- [ ] **Step 4: Register only precise ≤90-day legacy exceptions**

  Each has ID、edge、owner、reason、tracking、introduced、expiry、removeByWave. `--forbid-exemptions-through-wave 0` must be green at exit.

- [ ] **Step 5: Verify and commit**

```bash
pnpm exec vitest run scripts/architecture/check-dependencies.test.ts
python3 -m pytest scripts/architecture/tests -q
pnpm exec tsx scripts/architecture/check-dependencies.ts
python3 scripts/architecture/check-python-dependencies.py
git commit -am "build(architecture): enforce dependency boundaries"
```

## Chunk 4: Root commands、CI and Docker

### Task 13: Explicit root command orchestration

**Files:**
- Modify: root `package.json`
- Create: `scripts/verify/foundation.mjs`, `contract.mjs`, `platform.mjs`, `session.mjs`, `web-user.mjs`, `web-admin.mjs`, `agent.mjs`, `cross-runtime.mjs`, `images.mjs`
- Create: `scripts/verify/integration-runtime.mjs`
- Create: `scripts/verify/command-inventory.test.ts`

- [ ] **Step 1: Test every managed boundary has a required command**

  No `--if-present`、unbounded recursive execution、nested npm/npx、direct `.venv/bin` or real-provider secret requirement.

- [ ] **Step 2: Implement argv-based ordered runners**

  Each runner reports command/cwd/start/end/exit/report path and propagates signals; failure/skip is nonzero unless explicitly RC-external.

- [ ] **Step 3: Separate static commands from the single integration lifecycle**

  Platform/Session/Agent static runners never start Infra. `integration-runtime.mjs` is the only real-dependency runner: it acquires the
  canonical Infra lease、ensures minimum profiles、creates run-scoped MySQL/Mongo/Redis/MinIO resources、serially runs Platform、Session、
  Agent and fake-model cross-runtime gates, then cleans only the leased scope in `finally`. No runner may use a fixed shared DB、unguarded
  `FLUSHDB`、hard-coded old container name or package-owned compose file.

- [ ] **Step 4: Commit**

```bash
git add package.json scripts/verify
git commit -m "build: add explicit root verification commands"
```

### Task 14: Root required CI and CODEOWNERS

**Files:**
- Create: `.github/workflows/ci.yml`, `.github/CODEOWNERS`
- Delete: `.github/workflows/contract.yml` and nested Agent/Session/Web workflows in authority-switch set
- Create: `scripts/foundation/check-ci.ts`, tests

- [ ] **Step 1: Write CI policy tests**

  Reject remote sibling checkout、unpinned action SHA、mutable service image、Node22/Python3.11、pip/npm ci/npx、missing required job、
  silent skip and fork write cache.

- [ ] **Step 2: Add required jobs**

  `foundation`、`contract`、`ts-platform-static`、`ts-session-static`、`ts-web-user`、`ts-web-admin`、`python-agent-static`、
  `integration-runtime`、`images`、`security-foundation`. Static jobs must not declare service containers. `integration-runtime` starts
  exactly one root-managed Infra lifecycle, and self-hosted execution uses a concurrency group/lease. Pin actions and Infra/build images
  by digest with human-readable tag comments.

- [ ] **Step 3: Add CODEOWNERS consistency test**

  Root lock、contract、architecture policy/exceptions、provenance and every boundary INDEX owner must match manifest ownership.

- [ ] **Step 4: Verify workflow syntax and commit**

```bash
pnpm exec vitest run scripts/foundation/check-ci.test.ts
pnpm exec tsx scripts/foundation/check-ci.ts
git add -A .github scripts/foundation
git commit -m "ci: establish root required checks"
```

  GitHub ruleset changes and the no-op protection PR occur only after the branch workflow is green; they are external evidence, not
  repository code silently assumed successful.

### Task 15: Root-context Docker and bounded smoke

**Files:**
- Modify: `kokoro-agent/Dockerfile`, `kokoro-session/Dockerfile`, `kokoro-web/apps/user/Dockerfile`, `kokoro-platform/deploy/docker/Dockerfile`
- Modify: `docker-compose.infra.yml`, `docker-compose.app.yml`, `deploy/provision.sh`, `scripts/closure-up.py`, `scripts/verify-all.py`
- Modify: `scripts/e2e-v21-gate.py`, `scripts/chaos-verify.py`, `scripts/trace-verify.py`, `scripts/real-model-verify.py`
- Modify after snapshot import: `kokoro-platform/scripts/integration-dev.mjs` and Session/Agent integration fixtures that own DB/bucket cleanup
- Delete or downgrade to non-runnable pointer: `kokoro-platform/kokoro-litellm/docker-compose.example.yml`, `kokoro-platform/deploy/docker-compose.services.yml`
- Modify: root `.dockerignore`
- Create: `scripts/docker/check-context.mjs`, `scripts/docker/smoke.mjs`, tests
- Modify: `scripts/infra/manager.mjs`, `scripts/infra/scope.mjs`, `scripts/infra/inventory.mjs`, tests
- Modify: `config/repository/infrastructure-policy.yaml`

- [ ] **Step 1: Test Docker context contents before build**

  Fail if `.git`、`.env*`、node_modules、`.venv`、tmp、coverage、DB data or secret-like files enter context. Inspect names/digests only;
  do not print secret content.

- [ ] **Step 2: Write failing imported-consumer and Docker integration fixtures**

  Extend Task 0A gates across the now-imported packages: reject package-owned stateful Compose、fixed shared test DB/bucket、unguarded
  `FLUSHDB`、hard-coded old container names、test helpers that read shared dev env、incomplete MinIO cleanup and bypasses of the root manager.
  Docker context fixtures additionally reject secret/cache/local-data inclusion.

- [ ] **Step 3: Complete all imported consumers of the canonical Infra lifecycle**

  Preserve Task 0A's fixed identity/profiles and migrate every package/root verification entry to its lease/scope API. Pin remaining images,
  narrow per-service env, add missing production auth/health policy, remove or downgrade duplicate Compose authorities, and make Platform use
  separate context databases. Manager flow remains:

```text
inspect/refuse competing authority → ensure minimal services without recreate → wait real health
→ lease run scope → provision logical DB/key/bucket → run suites
→ cleanup only validated leased scope → local keep-or-stop / CI down --volumes for its ephemeral scope only
```

  Local `down` never deletes volumes. `destroy-data` is a separate exact-target command requiring inventory、backup/restore evidence and
  owner confirmation; do not implement a broad prune shortcut.

- [ ] **Step 4: Convert all builds to root context**

  Copy root manifests/workspace/lock + required leaf manifests first, frozen filtered install, then source. Agent uses Python 3.12.13;
  TS images use Node 24.18.0/pnpm 11.17.0. Existing process behavior remains unchanged.

- [ ] **Step 5: Fix Web standalone tracing from root**

  Assert the actual generated standalone manifest/path and run container HTTP readiness. Do not invent an Admin production Dockerfile.

- [ ] **Step 6: Build and smoke all roles through one Infra scope**

```bash
docker build -f kokoro-agent/Dockerfile .
docker build -f kokoro-session/Dockerfile .
docker build -f kokoro-web/apps/user/Dockerfile .
docker build -f kokoro-platform/deploy/docker/Dockerfile .
pnpm infra:config
pnpm verify:integration-runtime
docker compose -f docker-compose.app.yml config
pnpm exec node scripts/docker/smoke.mjs
```

- [ ] **Step 7: Commit**

```bash
git add .dockerignore docker-compose.infra.yml docker-compose.app.yml deploy scripts config/repository/infrastructure-policy.yaml \
  kokoro-*/Dockerfile kokoro-platform/deploy/docker/Dockerfile
git commit -m "build(docker): complete managed runtime integration"
```

## Chunk 5: Current docs、fresh clone and external verification

### Task 16: Current-fact documentation and ADR

**Files:**
- Create: `docs/kokoro-handbook/decisions/ADR-009-true-monorepo-snapshot-import.md`
- Modify: ADR-007 as superseded pointer
- Modify: `README.md`, `docs/README.md`, `docs/CURRENT.md`, `docs/CODEBASE_MAP.md`
- Modify: affected current INDEX/README files only after code exists

- [ ] **Step 1: Add documentation assertions to INDEX/link checker**

  Reject gitlink/submodule install instructions、floating remote CI、old lock commands、incorrect mirror counts and target-as-current claims.

- [ ] **Step 2: Write the ADR**

  Record pinned snapshot choice、alternatives、recovery tags/bundles、single authority、independent Site Project boundary、trade-offs and
  reversal. Do not copy external bundle paths containing private infrastructure details.

- [ ] **Step 3: Update current facts**

  Platform remains current legacy topology until Wave 1/2/5；Session commercial roles remain until Wave 3；GA provider/skills remain until
  approved Wave 5A/5B. Only repository/toolchain/contract/INDEX/CI facts become implemented.

- [ ] **Step 4: Verify links and commit**

```bash
pnpm exec tsx scripts/architecture/check-index-coverage.ts --mode full
git diff --check
git commit -am "docs: publish Wave 0 repository facts"
```

### Task 17: Fresh-clone certification and Wave evidence

**Files:**
- Create: `docs/reports/evidence/wave-0/evidence.yaml`
- Create: `docs/reports/evidence/wave-0/dependency-migration.json`
- Create: `docs/reports/2026-07-26-wave-0-completion-report.md`
- Modify: `scripts/foundation/check-evidence.mjs`

- [ ] **Step 1: Write evidence-schema and digest tests**

  Repo manifest may reference only parent/earlier `exactSnapshotImportCommit` and `implementationCommit`. It must not contain its own/future
  SHA. Final-head verification is an external immutable CI/signed attestation ref+digest.

- [ ] **Step 2: Create a `git clone --no-local` with an independent object database**

  Do not reuse source worktrees or local object alternates. Verify no submodule command is required.

- [ ] **Step 3: Run the complete required matrix in the fresh clone**

```text
foundation → contract → ts-platform → ts-session → ts-web-user → ts-web-admin
→ python-agent → cross-runtime → images → security-foundation
```

  Re-run codegen/locks twice and require `git diff --exit-code`. Record argv/cwd/tool versions/start/end/exit/report digest and CI URL.
  The matrix invokes exactly one `integration-runtime` lifecycle. Evidence records Infra manifest digest、canonical project、profiles、
  container/image digests、health results、lease/scope IDs、logical MySQL/Mongo/Redis/MinIO allocations and cleanup receipt without
  recording credentials. Static gates must prove they did not start Infra. At the end, no test DB/key/bucket scope or test container remains.

- [ ] **Step 4: Push the candidate branch and enable root branch protection**

  Add ten required checks and CODEOWNERS review. Push a no-op documentation PR and prove the ruleset cannot be bypassed. Store ruleset
  snapshot digest and PR URL in external evidence.

- [ ] **Step 5: Generate final external attestation**

  The CI artifact/signature records the actual final head commit and evidence digest. The repository manifest references the external
  attestation; it never tries to hash itself.

- [ ] **Step 6: Run main-worktree verification after integration**

  Re-run all gates from the integrated root checkout. Worker success or branch CI alone is insufficient.

- [ ] **Step 7: Commit evidence index and completion report**

```bash
git add docs/reports/evidence/wave-0 docs/reports/2026-07-26-wave-0-completion-report.md scripts/foundation/check-evidence.mjs
git commit -m "docs(evidence): certify Wave 0 foundation"
```

### Task 18: Retire old write authorities only after certification

**Files:**
- Modify external repository settings/readmes after approval
- Record receipts in external attestation and completion report

- [ ] **Step 1: Confirm all Wave 0 P0 exit gates are green**

  No open ownership、source、lock、contract、INDEX、CI、Docker、GA differential、fresh-clone or rollback issue.

- [ ] **Step 2: Exercise the revert bundle**

  In a disposable clone, reverse the review DAG, restore `.gitmodules`/gitlinks and verify archive tags/bundles. Never use reset on the
  working repository.

- [ ] **Step 3: Archive old repositories read-only**

  Update description/README to the root authority, preserve history/issues/releases, disable old CI/release/write permissions. Do not delete.

- [ ] **Step 4: Record receipts and run final audit**

  Verify no old build/test path reaches remote main and no documentation claims Wave 1+ behavior. Wave 1 may start only after this report.

## Final plan verification

Before execution handoff, the plan reviewer must confirm:

- [ ] every state-changing step is after ownership/LicenseRef attestation；
- [ ] current Web pin/tree/archive and both locally-ahead Platform/Web recovery anchors are used；
- [ ] no commit hash self-reference exists；
- [ ] root workspace does not absorb production Site Projects；
- [ ] snapshot import is mechanical and isolated from toolchain changes；
- [ ] root lock/Docker/CI/nested workflow deletion is one protected authority switch set；
- [ ] one root Infra authority exists per environment；project/network/volume identity、profiles、restart、health、lease、logical test
      isolation and non-destructive cleanup are enforced, and no package/ad-hoc second stateful stack remains；
- [ ] current baseline failures are visible and resolved/accepted before claiming regression-free；
- [ ] GA old/new corpus precedes old-lock deletion and semantic diff is zero；
- [ ] no real Provider/payment/production secret is required；
- [ ] fresh-clone, external attestation, rollback and main-worktree verification all exist。
