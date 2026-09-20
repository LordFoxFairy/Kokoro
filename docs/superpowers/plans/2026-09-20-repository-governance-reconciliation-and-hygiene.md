# Repository Governance Reconciliation and Hygiene Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 Root 静态审计与已批准的 Root/子仓事实对齐，并关闭不改变业务边界的逐仓卫生缺口；审计结果必须区分真实违规和未安装工具链导致的“未验证”。

**Architecture:** Root 继续是只读组合治理者：它使用显式 repository profile 描述各 owner 的 canonical schema、受管 OpenAPI、Node major 与源码角色，而不把每个仓硬塞进同一目录或 SQL 模式。各 child repository 单独提交最小卫生切片；Root 仅更新 gitlink、组合证据和治理测试。未激活的 Billing v2、Web→BFF 身份链、Agent/Billing 大重构仍是独立设计项目，不通过降低规则或兼容层伪装完成。

**Tech Stack:** Python 3 Root governance/pytest；pnpm/Node 22 或 24（按仓锁定）；Prisma/SQL-first schema；Go Scheduler。

## Global Constraints

- Root 路径与远端名固定为 `apps/kokoro-app`、`apps/kokoro-bff`、`apps/kokoro-agent`、`apps/kokoro-iam`、`apps/kokoro-system`、`apps/kokoro-billing`、`apps/kokoro-capability`、`apps/kokoro-storage`、`apps/kokoro-scheduler`；不恢复 `kokoro/` alias。
- Root 不保存子仓源代码、测试、lockfile 或机器 contract 的副本；每仓唯一 writer，Root 串行更新 submodule gitlink。
- SQL-first canonical schema 是 `database/schema.sql`；ORM-first canonical schema 是 `prisma/schema.prisma`。二者在同一 owner 中不得同时作为可编辑事实源；不恢复 migrations。
- Root 静态审核不安装依赖。缺少 `node_modules/typescript` 的结果标为 `unverified`，只有 `--require-installed-tools` 才成为失败；各 owner 的 `pnpm typecheck` 仍是完成证据。
- Web 与 BFF 固定 Node 22；IAM、System、Billing、Capability、Storage 固定 Node 24。`engines`、`.node-version`（如有）、Docker、CI 与 release workflow 必须同一 major。
- 首发 Billing HTTP contract 固定 `v1`。`contract/openapi/v2/openapi.yaml` 是待迁移/废弃目标，保持为真实审计项，不能放宽为任意 `/vN`。
- `src/generated/**` 为只读机器生成物，不纳入手写源码的 env/依赖/文件粒度规则；transport/RPC 可消费 wire types，业务 Domain/feature code 仍不可直接依赖 provider 或 generated wire type。
- 不使用 `git add .` 或 `git add -A`；每个 commit 仅暂存任务文件。最终 Root 和所有 submodule 仅保留 clean `main`。

---

## 放置表

| 项 | 结论 |
| --- | --- |
| Owner | Root `scripts/governance/` 是静态规则唯一 writer；每个 child 仅修改其 own metadata/config/documentation。 |
| 当前事实 | `verify-ten-repository-standard.py --format json` 在 Root `c6997a60` 报告 189 项；其中 ORM、vendor snapshot、generated、optional modules、Node 与未安装 TypeScript 有规则冲突。 |
| 目标职责 | 让 audit 只对已批准事实做严格检查，输出 `violations` 与 `unverified`，并关闭所有不涉及业务/contract 迁移的卫生缺口。 |
| 目录方案 | Root 规则留在 `scripts/governance/`（采用），不用新 top-level validator；计划留在既有 `docs/superpowers/plans/`（采用），不用在 Root 新建 task center。 |
| 粒度 | Profile、schema/contract discovery 与 TypeScript source-role 分类分别放在既有责任文件；不新增万能 parser module。 |
| 依赖 | Root 只读 submodule；child 只写自身文件。Root 不生成 child contract 或 schema。 |
| 数据/API | 不改变业务数据、wire request/response 或数据库 schema；仅明确 canonical 发现和 vendor contract 语义。 |
| 删除项 | 删除 BFF 无调用 `src/database/setup.ts`；删除 Web MCP CSS/JSX 的 compatibility class 名；移动 IAM 上游 snapshot 至 vendor 范围。 |
| 验证 | Root pytest/topology/main-only/JSON audit；每 child 执行其已声明的 formatter/lint/typecheck/contract/test/build，安装前后检查 lockfile diff 为零。 |

## Task 1: Profile 化 Root schema、OpenAPI 与 Node 规则

**Files:**
- Modify: `scripts/governance/ten_repository_standard.py`
- Modify: `scripts/governance/repository_checks.py`
- Modify: `scripts/governance/typescript_checks.py`
- Modify: `scripts/governance/contract_checks.py`
- Modify: `scripts/verify-ten-repository-standard.py`
- Test: `scripts/tests/test_ten_repository_standard.py`

**Interfaces:**
- Consumes: `RepositoryProfile`, each child `AGENTS.md`/`DATA_MODEL.md` canonical facts, `contract/README.md` provenance.
- Produces: `collect_failures()` returning only policy violations; JSON adds `unverified: [{repository, rule, detail}]`; `--require-installed-tools` treats unverified compiler resolution as non-zero.

- [ ] **Step 1: Add failing profile/discovery tests.**

```python
def test_orm_profile_uses_prisma_as_its_only_canonical_schema() -> None:
    profile = verifier.REPOSITORY_PROFILES["kokoro-capability"]
    assert profile.canonical_schema == "prisma/schema.prisma"
    assert profile.schema_kind == "prisma"


def test_owned_openapi_excludes_vendor_snapshot_and_accepts_root_json(tmp_path: Path) -> None:
    vendor = tmp_path / "contract" / "vendor" / "upstream.json"
    owned = tmp_path / "contract" / "openapi.json"
    vendor.parent.mkdir(parents=True)
    vendor.write_text('{"openapi":"3.1.0","paths":{}}', encoding="utf-8")
    owned.write_text('{"openapi":"3.1.0","paths":{}}', encoding="utf-8")
    assert verifier.owned_openapi_specs(tmp_path) == (owned,)


def test_missing_typescript_is_unverified_unless_requested(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(typescript_checks, "effective_ts_compiler_options", lambda _: (_ for _ in ()).throw(verifier.TypeScriptConfigError("missing")))
    failures, unverified = verifier.collect_audit()
    assert not [item for item in failures if item.rule == "typescript-configuration"]
    assert [item for item in unverified if item.rule == "typescript-configuration"]
```

- [ ] **Step 2: Run the focused test and confirm the pre-change behavior fails.**

Run: `python3 -m pytest scripts/tests/test_ten_repository_standard.py -q`  
Expected: FAIL because profiles lack `schema_kind`/`canonical_schema`, OpenAPI discovery is absent and audit has no unverified channel.

- [ ] **Step 3: Implement explicit profiles and strict discovery.**

```python
@dataclass(frozen=True)
class RepositoryProfile:
    kind: str
    requires_schema: bool
    redis_database: int | None
    canonical_schema: str | None = None
    schema_kind: Literal["none", "sql", "prisma"] = "none"
    node_major: int | None = None
    required_source_paths: tuple[str, ...] = ()
```

Set `kokoro-iam`, `kokoro-capability`, and `kokoro-storage` to `canonical_schema="prisma/schema.prisma", schema_kind="prisma"`; retain SQL profiles for BFF, Agent, System, Billing and Scheduler. Add `owned_openapi_specs(repository)` that accepts only `contract/**` files with top-level OpenAPI, excludes `contract/vendor/**`, and supports `contract/openapi.json`. Require one ORM schema, reject `prisma/migrations/` and a concurrent `database/schema.sql`; require existing owner `db:apply-schema`, `prisma:validate`, `prisma:generate` and a schema drift checker already declared by that repository’s technical design. Replace global Node string equality with profile Node-major consistency across manifest, `.node-version`, Docker `node:` image and `actions/setup-node` values. Continue to reject a divergent CI/release major.

Use a single path iterator for YAML and JSON OpenAPI version checks. It must accept only `/v1/...`, `/internal/v1/...`, probes and `/.well-known/...`; report Billing `/v2/...` as `http-versioning` with a “first-release v1 baseline” detail. Do not silently accept any version.

- [ ] **Step 4: Implement source-role classification without weakening business checks.**

```python
if relative_path.startswith("src/generated/"):
    continue
is_transport = (
    relative_path.startswith("src/transport/")
    or path.name.endswith((".routes.ts", ".controller.ts", ".rpc.ts", ".connect.ts", "-rpc.service.ts"))
)
is_process_service = relative_path.startswith(("src/database/", "src/integrations/"))
is_business_service = not is_transport and not is_process_service and (
    path.name.endswith((".service.ts", ".policy.ts"))
    or any(part in {"use-cases", "services", "commands"} for part in relative_parts[:-1])
)
```

Keep generated imports/provider imports forbidden in Domain and feature business services. Remove mandatory `src/modules/`; retain checks against technical directory names inside an actual business module and against retired global four-layer trees only when the target repository’s approved current design has declared them retired.

- [ ] **Step 5: Run Root rules and audit output.**

Run:
```bash
python3 -m pytest scripts/tests/test_ten_repository_standard.py -q
python3 scripts/verify-ten-repository-standard.py --format json > /tmp/kokoro-governance-reconciled.json
python3 scripts/verify-repository-topology.py
python3 scripts/verify-main-only.py
```
Expected: Root tests and topology/main-only PASS; JSON separates unverified TypeScript toolchains and no longer reports ORM/generated/vendor/module-container false positives. Billing v2, Web→IAM, Agent/Billing architecture and other real owner work remain violations.

- [ ] **Step 6: Commit Root policy slice.**

```bash
git add scripts/governance/ten_repository_standard.py scripts/governance/repository_checks.py scripts/governance/typescript_checks.py scripts/governance/contract_checks.py scripts/verify-ten-repository-standard.py scripts/tests/test_ten_repository_standard.py
git commit -m "fix(governance): align profiles with owner facts"
```

## Task 2: Normalize vendor contract provenance and contract metadata

**Files:**
- Move: `apps/kokoro-iam/contract/openapi/better-auth.v1.7.3.json` → `apps/kokoro-iam/contract/vendor/better-auth.v1.7.3.json`
- Create: `apps/kokoro-iam/contract/vendor/README.md`
- Modify: `apps/kokoro-iam/contract/README.md`
- Modify: `apps/kokoro-iam/scripts/generate-contracts.ts`
- Modify: `apps/kokoro-iam/test/contract/auth-kernel.test.ts`
- Modify: `apps/kokoro-scheduler/contract/README.md`

**Interfaces:**
- Consumes: IAM Better Auth generated snapshot and Scheduler canonical OpenAPI.
- Produces: `contract/vendor/` is explicitly read-only upstream material; `contract/README.md` declares owner, visibility, version, generation, breaking and provenance; Scheduler explains its generator.

- [ ] **Step 1: Write failing contract-location and README-field tests.**

```ts
expect(await readFile("contract/vendor/better-auth.v1.7.3.json", "utf8")).toContain('"openapi"');
expect(await readFile("contract/openapi/iam.internal.v1.json", "utf8")).toContain('"openapi"');
expect(contractReadme).toMatch(/visibility/i);
expect(contractReadme).toMatch(/generation/i);
expect(contractReadme).toMatch(/breaking/i);
```

- [ ] **Step 2: Move the snapshot and update its one generator/test owner.**

Use `git mv`. Change `generate-contracts.ts` to write exactly `contract/vendor/better-auth.v1.7.3.json`; preserve its deterministic output and test both that vendor snapshot and owned internal contract. In vendor README record the literal upstream package/source, `v1.7.3`, generation command, SHA-256, license and drift-only purpose. Do not add Kokoro operation extensions to an upstream snapshot.

- [ ] **Step 3: State contract provenance without fabricating release status.**

Add explicit IAM README headings/fields for `visibility` (owner internal plus Better Auth browser-private allowlist), `generation` (generator commands), and `breaking` (immutable baseline requirement). Add Scheduler `generation` description naming the canonical OpenAPI source/check command; do not modify the OpenAPI itself.

- [ ] **Step 4: Verify each owner.**

Run:
```bash
(cd apps/kokoro-iam && pnpm contract:check && pnpm contract:breaking)
(cd apps/kokoro-scheduler && ./scripts/contract-check && go test ./...)
```
Expected: both pass with no generated drift.

- [ ] **Step 5: Commit child slices and update only their Root gitlinks.**

```bash
(cd apps/kokoro-iam && git add contract/vendor/better-auth.v1.7.3.json contract/vendor/README.md contract/README.md scripts/generate-contracts.ts test/contract/auth-kernel.test.ts && git commit -m "docs(contract): classify Better Auth snapshot as vendor input")
(cd apps/kokoro-scheduler && git add contract/README.md && git commit -m "docs(contract): record OpenAPI generation")
git add apps/kokoro-iam apps/kokoro-scheduler
git commit -m "chore(root): advance contract hygiene submodules"
```

## Task 3: Apply pnpm build policy and runtime-major hygiene

**Files:**
- Modify: `apps/kokoro-app/pnpm-workspace.yaml`
- Modify: `apps/kokoro-bff/pnpm-workspace.yaml`
- Modify: `apps/kokoro-bff/test/source-start.test.mjs`
- Modify: `apps/kokoro-iam/pnpm-workspace.yaml`
- Modify: `apps/kokoro-billing/pnpm-workspace.yaml`
- Modify: `apps/kokoro-capability/pnpm-workspace.yaml`
- Modify: `apps/kokoro-capability/.github/workflows/release-image.yml`
- Modify: `apps/kokoro-storage/pnpm-workspace.yaml`
- Modify: `apps/kokoro-storage/.github/workflows/ci.yml`
- Modify: `apps/kokoro-storage/.github/workflows/release-image.yml`

**Interfaces:**
- Consumes: existing `allowBuilds` allowlists and each package/lockfile runtime pin.
- Produces: reviewed dependency build policy and a consistent Node major across manifest/image/CI/release.

- [ ] **Step 1: Add the explicit pnpm setting without broadening any allowlist.**

Every listed `pnpm-workspace.yaml` must contain:

```yaml
strictDepBuilds: true
allowBuilds:
```

Preserve the existing package keys under `allowBuilds:` byte-for-byte. Update BFF’s YAML exact-content test to expect `strictDepBuilds: true` before `allowBuilds:`.

- [ ] **Step 2: Align release/CI majors to the repository’s existing runtime.**

In Capability release CI, replace the literal `node-version: 22` with `node-version: 24.13.0`. In Storage CI and release CI, replace each literal `node-version: 22` with `node-version: 24.20.0`. Do not modify package `engines`, Docker image digests, lockfiles or application code.

- [ ] **Step 3: Verify frozen installation and owner gates.**

Run the relevant commands in each changed repository:

```bash
pnpm install --frozen-lockfile
pnpm lint
pnpm typecheck
pnpm test
pnpm build
```

Additionally run Web `pnpm contract && pnpm test:architecture && pnpm test:e2e`; BFF `pnpm contract:check`; IAM `pnpm contract:check`; Capability `pnpm contract:check && pnpm schema:check`; Storage `pnpm contract:check && pnpm test:architecture`. Confirm `git diff -- pnpm-lock.yaml` is empty after every install.

- [ ] **Step 4: Commit one repository at a time and then Root gitlinks.**

Use these exact commit subjects:

```text
chore(build): require reviewed dependency builds
ci(release): align capability Node runtime
ci(release): align storage Node runtime
chore(root): advance build hygiene submodules
```

Stage only the files listed for each repository and then only the corresponding `apps/kokoro-*` gitlinks in Root.

## Task 4: Remove dead BFF installer and Web compatibility naming

**Files:**
- Delete: `apps/kokoro-bff/src/database/setup.ts`
- Modify: `apps/kokoro-bff/test/architecture.test.ts`
- Modify: `apps/kokoro-app/src/ui/mcp/mcp-register-form.tsx`
- Modify: `apps/kokoro-app/src/ui/mcp/mcp-register-form.module.css`

**Interfaces:**
- Consumes: BFF’s actual `scripts/apply-schema.mjs` installer and existing MCP form DOM/module class bindings.
- Produces: no unused environment-reading installer; MCP form preserves rendered structure with neutral class names.

- [ ] **Step 1: Confirm deletion is behavior-preserving.**

```bash
rg -n "database/setup|setup\.ts" apps/kokoro-bff --glob '!test/architecture.test.ts'
```
Expected: no runtime caller. Replace the architecture test’s read/assertion of the deleted file with an assertion that `scripts/apply-schema.mjs` is the only schema-install entry.

- [ ] **Step 2: Rename only compatibility-marked form classes.**

Rename the same CSS-module key in both files (for example `compatibilityHint` to `registrationHint`); do not change style declarations, text, form validation, request body or tests.

- [ ] **Step 3: Run owner gates.**

```bash
(cd apps/kokoro-bff && pnpm lint && pnpm typecheck && pnpm contract:check && pnpm test && pnpm build)
(cd apps/kokoro-app && pnpm contract && pnpm test:architecture && pnpm lint && pnpm typecheck && pnpm test && pnpm build && pnpm test:e2e)
```

- [ ] **Step 4: Commit and advance Root gitlinks.**

```text
refactor(schema): remove unused BFF setup entry
refactor(mcp): remove compatibility naming
chore(root): advance source hygiene submodules
```

## Task 5: Record reconciled evidence and enforce the final phase-one gate

**Files:**
- Modify: `docs/CURRENT.md`
- Modify: `docs/REPOSITORY_STATUS.md`
- Modify: `docs/kokoro-handbook/decisions/ADR-032-root-submodule-composition-and-repository-identity.md`
- Test: `scripts/tests/test_ten_repository_standard.py`

**Interfaces:**
- Consumes: Task 1 audit JSON and pushed child `main` commits.
- Produces: truthful count of `violations`/`unverified`, exact child gitlinks and explicit next owner queue.

- [ ] **Step 1: Capture final audit evidence.**

```bash
python3 scripts/verify-ten-repository-standard.py --format json > /tmp/kokoro-phase-one-governance.json
python3 scripts/verify-repository-topology.py
python3 scripts/verify-main-only.py
python3 -m pytest scripts/tests -q
```

Record the actual count and list each remaining real owner category; do not describe unverified TypeScript compiler settings as passing.

- [ ] **Step 2: Update Root status docs.**

State that Root topology/main-only/Root Python tests are green only when commands actually pass. State that remaining owner work is: Web BFF-auth + UI split; BFF feature-first/formatter; Agent config/topology decision; IAM owned OpenAPI metadata + CI/release; Billing v1/M3; Capability P2/P5 + authorization split; Storage command type boundary. Link this plan as the current hygiene decision record.

- [ ] **Step 3: Commit Root evidence.**

```bash
git add docs/CURRENT.md docs/REPOSITORY_STATUS.md docs/kokoro-handbook/decisions/ADR-032-root-submodule-composition-and-repository-identity.md
git commit -m "docs(root): record reconciled owner quality queue"
```

## Task 6: Final integration review

**Files:**
- Review: full range from Root phase baseline through Task 5.

- [ ] **Step 1: Verify clean main-only state.**

```bash
git status --short
git branch --show-current
git submodule foreach --recursive 'test "$(git branch --show-current)" = main && test -z "$(git status --porcelain)"'
git branch -a
git submodule foreach --recursive 'git branch -a'
```
Expected: no status output; Root and every submodule are on `main`; no local or remote branch other than `main`.

- [ ] **Step 2: Run the full Root static suite.**

```bash
python3 scripts/verify-repository-topology.py
python3 scripts/verify-main-only.py
python3 -m pytest scripts/tests -q
python3 scripts/verify-ten-repository-standard.py --format json
```

Expected: topology/main-only/pytest PASS. The final structural audit has no reclassified false positives; remaining entries are a visible owner queue or `unverified` preconditions, not a false green.

- [ ] **Step 3: Push every child `main` before Root and verify remote alignment.**

```bash
for repo in apps/kokoro-app apps/kokoro-bff apps/kokoro-iam apps/kokoro-billing apps/kokoro-capability apps/kokoro-storage apps/kokoro-scheduler; do
  git -C "$repo" push origin main
  test "$(git -C "$repo" rev-parse HEAD)" = "$(git -C "$repo" rev-parse origin/main)"
done
git push origin main
test "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)"
```

