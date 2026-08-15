# Independent Service Repository Extraction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract every Kokoro owner into a genuinely independent Git remote, make each repository own its configuration, provider contract, database, tests, reports, CI and dev entry, then reduce Root to operator bootstrap, gitlinks, release manifest and documentation.

**Architecture:** Extraction is a repository-topology program, not a business implementation program. Root automates secret-safe operator preflight, remote creation, clean snapshot extraction, environment allowlist injection and final pin promotion; every service writes and executes its detailed clean-replace plan inside its own remote. Provider contracts stay with providers, pair tests stay with consumers, and User Web/Admin Web each own their browser E2E.

**Tech Stack:** Git, GitHub CLI `gh`, Python 3.11+ standard library, Node.js 22+, pnpm 11.2.2, uv, PostgreSQL 18, Redis, Buf, each repository's existing TypeScript/Python test toolchain.

## Global Constraints

- Authority is [`436ee0d`](../../specs/2026-08-15-application-integrity-subrepository-gates-design.md), spec version 1.2.
- No shared quality, protocol, system-test or business-contract repository, Root service test suite or Root database is created.
- A root-shaped branch/worktree is only an extraction candidate. Independence requires a distinct object database, actual remote, CI, version, and fresh standalone clone/build/test.
- A missing target repository is `CREATE_REQUIRED` and is created by the reviewed bootstrap. Authentication, permission, owner-policy or name-conflict failures produce `BLOCKED`; scripts never guess a URL or report an unexecuted create/push as successful.
- Root `.env` is ignored and never committed. Root bootstrap reads it only as the operator input ledger and injects an explicit allowlist into each repository's own ignored `.env` and GitHub vars/secrets.
- Every repository owns `.env.example`, `config/environment.schema.json`, its ignored `.env`, and CI secret declarations. Service code never reads Root `.env` or Root-specific variable names.
- Initial test/report results are `NOT_STARTED`. Promotion is `CATALOG_FROZEN -> RED_RECORDED -> IMPLEMENTING -> EXECUTING -> REPORT_REVIEW -> APPROVE`.
- Clean replace means no migration of old data, double write, backfill, shadow schema, legacy adapter, old DTO bridge or old-path flag.
- Do not start an extraction task from the currently dirty Root or dirty Web candidate. Preserve unrelated work and start from reviewed committed SHAs in isolated worktrees/clones.

## Current Facts And Target Map

| Target repository | Reviewed extraction source | Current remote fact | Owner acceptance command |
|---|---|---|---|
| `kokoro-site` | `/private/tmp/kokoro-site-slice-a@2e1ac69` | origin is local `kokoro-platform` | `pnpm test && pnpm typecheck && pnpm lint && pnpm build` |
| `kokoro-iam` | `/private/tmp/kokoro-iam-slice-a@1ca2ced` | origin is local `kokoro-platform` | `pnpm test && pnpm typecheck && pnpm lint && pnpm build` |
| `kokoro-model` | `/private/tmp/kokoro-model-slice-a@400b6ad` | origin is local `kokoro-platform` | `pnpm check` |
| `kokoro-capability` | `/private/tmp/kokoro-capability-slice-a@ca0b3d4` | origin is local `kokoro-platform` | `pnpm check` |
| `kokoro-agent` | `/private/tmp/kokoro-agent-slice-a@5de3a2d` | independent GitHub remote exists; candidate is not yet the remote default pin | `uv run ruff check . && uv run pyright && uv run pytest` |
| `kokoro-chat` | `/private/tmp/kokoro-chat-slice-a@f0e15c8` | origin is local `kokoro-session` | `pnpm test && pnpm typecheck && pnpm lint && pnpm build` |
| `kokoro-storage` | `kokoro-platform/kokoro-hub/{src/infrastructure/packages/s3-package-store.ts,src/config/storage.ts,src/contract/storage.ts,test/unit/storage-config.test.ts}` plus approved new owner scaffolding | no independent candidate/remote evidenced | `NOT_DEFINED`; the repo-local plan must add `pnpm verify` |
| `kokoro-entitlement` | tracked source closure under `kokoro-platform/kokoro-credit/` excluding generated/cache/build output | no independent candidate/remote evidenced | `NOT_DEFINED`; the repo-local plan must add `pnpm verify` |
| `kokoro-payment` | tracked source closure under `kokoro-platform/kokoro-payment/` excluding generated/cache/build output | no independent candidate/remote evidenced | `NOT_DEFINED`; the repo-local plan must add `pnpm verify` |
| `kokoro-web-user` | committed `kokoro-web/apps/user` plus its workspace dependency closure | still part of `kokoro-web` | `NOT_DEFINED`; the repo-local plan must add `pnpm verify` and `pnpm verify:e2e` |
| `kokoro-web-admin` | committed `kokoro-web/apps/admin` plus its workspace dependency closure | still part of `kokoro-web` | `NOT_DEFINED`; the repo-local plan must add `pnpm verify` and `pnpm verify:e2e` |

Live GitHub audit at plan time: CLI identity is `LordFoxFairy`; `kokoro-agent` exists as private `main`; the other ten target names are absent and therefore `CREATE_REQUIRED`, not pre-approved.

## File Ownership After Extraction

Root may keep only `.env.example`, `.gitignore`, `.gitmodules`, `config/repositories/*.json`, `scripts/repositories/**`, repository gitlinks, release manifests, and docs/reports. `scripts/repositories/tests/**` tests topology automation only; it cannot contain service, RPC or browser assertions.

Every backend provider must own `.env.example`, `.github/workflows/ci.yml`, `config/environment.schema.json`, `contract/buf.yaml`, its exact Proto directory and breaking image, `database/migrations/`, `database/tests/`, `tests/catalog.json`, `scripts/dev`, `scripts/verify`, its exact plan and its exact report before advancing beyond `NOT_STARTED`.

User Web and Admin Web own the same config/report/CI/dev/verify surface, generated consumer clients, pair catalogs and their own browser E2E; they do not invent provider Proto or a business database.

| Repository | Provider Proto directory | Repo-local plan | Repo-local owner report |
|---|---|---|---|
| `kokoro-site` | `contract/proto/kokoro/site/v1/` | `docs/superpowers/plans/2026-08-15-site-clean-replace-implementation-plan.md` | `docs/reports/site-acceptance-report.json` |
| `kokoro-iam` | `contract/proto/kokoro/iam/v1/` | `docs/superpowers/plans/2026-08-15-iam-clean-replace-implementation-plan.md` | `docs/reports/iam-acceptance-report.json` |
| `kokoro-model` | `contract/proto/kokoro/model/v1/` | `docs/superpowers/plans/2026-08-15-model-clean-replace-implementation-plan.md` | `docs/reports/model-acceptance-report.json` |
| `kokoro-capability` | `contract/proto/kokoro/capability/v1/` | `docs/superpowers/plans/2026-08-15-capability-clean-replace-implementation-plan.md` | `docs/reports/capability-acceptance-report.json` |
| `kokoro-agent` | `contract/proto/kokoro/agent/v1/` | `docs/superpowers/plans/2026-08-15-agent-clean-replace-implementation-plan.md` | `docs/reports/agent-acceptance-report.json` |
| `kokoro-chat` | `contract/proto/kokoro/chat/v1/` | `docs/superpowers/plans/2026-08-15-chat-clean-replace-implementation-plan.md` | `docs/reports/chat-acceptance-report.json` |
| `kokoro-storage` | `contract/proto/kokoro/storage/v1/` | `docs/superpowers/plans/2026-08-15-storage-clean-replace-implementation-plan.md` | `docs/reports/storage-acceptance-report.json` |
| `kokoro-entitlement` | `contract/proto/kokoro/entitlement/v1/` | `docs/superpowers/plans/2026-08-15-entitlement-clean-replace-implementation-plan.md` | `docs/reports/entitlement-acceptance-report.json` |
| `kokoro-payment` | `contract/proto/kokoro/payment/v1/` | `docs/superpowers/plans/2026-08-15-payment-clean-replace-implementation-plan.md` | `docs/reports/payment-acceptance-report.json` |
| `kokoro-web-user` | none; consumer only | `docs/superpowers/plans/2026-08-15-web-user-clean-replace-implementation-plan.md` | `docs/reports/web-user-acceptance-report.json` |
| `kokoro-web-admin` | none; consumer only | `docs/superpowers/plans/2026-08-15-web-admin-clean-replace-implementation-plan.md` | `docs/reports/web-admin-acceptance-report.json` |

---

### Task 1: Secret-Safe Root Operator Preflight

**Files:**
- Reuse: `.env.example`, `.gitignore`
- Create: `scripts/repositories/__init__.py`, `scripts/repositories/config.py`, `scripts/repositories/preflight.py`
- Create: `scripts/repositories/tests/test_preflight.py`
- Create: `scripts/repositories/INDEX.md`
- Modify: `pyproject.toml` (`tool.pytest.ini_options.testpaths` adds `scripts/repositories/tests`)

**Interfaces:**
- Consumes: Root ignored `.env` keys exactly as committed in `.env.example`.
- Produces: `OperatorConfig.load(root: Path) -> OperatorConfig` and `run_preflight(config: OperatorConfig) -> PreflightResult`; JSON output contains only status, missing key names and missing executable names.

- [ ] **Step 1: Write the RED tests**

Test absent both `GH_TOKEN` and usable `gh auth`, relative `KOKORO_REPOSITORY_PARENT`, missing `gh`, an unignored `.env`, and marker secrets in all configured sensitive values. Also prove an empty `GH_TOKEN` is accepted when `gh auth status --hostname` succeeds. Assert stdout/stderr contains only missing names and never any marker value.

```bash
uv run pytest scripts/repositories/tests/test_preflight.py -q
```

Expected: RED because `scripts.repositories.preflight` does not exist.

- [ ] **Step 2: Implement strict config and machine checks**

`OperatorConfig` parses exactly the committed `.env.example` names: GitHub owner/host/visibility/default branch, optional `GH_TOKEN`, absolute repository parent, shared local PostgreSQL/Redis bootstrap endpoints and the IAM/Agent/Payment/Storage namespaced operator values. Remote bootstrap requires only the GitHub group plus repository parent; missing service values are reported per owning repository as `NOT_CONFIGURED` and do not masquerade as a passed service gate. Root topology checks require `git`, `git-filter-repo`, `gh`, `python3`, `node`, `corepack`, `pnpm` and `uv`; PostgreSQL, Redis, Buf and provider-specific tools are validated inside the owning repository and cannot block unrelated remote creation. Authentication uses `GH_TOKEN` or `gh auth status --hostname` and never echoes environment or argv values.

```bash
git check-ignore -q .env
! git ls-files --error-unmatch .env
uv run pytest scripts/repositories/tests/test_preflight.py -q
uv run python -m scripts.repositories.preflight --json
```

Expected: GREEN only on a configured machine; otherwise one secret-safe `BLOCKED` JSON result.

- [ ] **Step 3: Commit only topology bootstrap**

```bash
git add .env.example pyproject.toml scripts/repositories
git commit -m "chore(repository): add secret-safe extraction preflight"
```

### Task 2: Actual GitHub Remote Creation Gate

**Files:**
- Create: `config/repositories/services.json`
- Create: `scripts/repositories/remotes.py`
- Create: `scripts/repositories/tests/test_remotes.py`
- Create: `docs/reports/2026-08-15-independent-service-extraction-report.json`

**Interfaces:**
- Consumes: Task 1 `OperatorConfig`; target names from the table above.
- Produces: `ensure_remotes(config, manifest) -> tuple[RemoteReceipt, ...]`; each receipt records the URL returned by `gh repo view`, default branch, observed UTC time and `ls-remote` digest.

- [ ] **Step 1: Freeze all report rows as `NOT_STARTED` and write RED mutations**

Tests cover missing repo, permission denial, wrong owner/name, guessed URL, failed push, and a branch presented as a remote. No fixture may convert these to PASS.

```bash
uv run pytest scripts/repositories/tests/test_remotes.py -q
```

Expected: RED because no remote gate exists.

- [ ] **Step 2: Automate create-or-verify with `gh`**

For every target, call `gh repo view OWNER/NAME --json nameWithOwner,url,defaultBranchRef`; only a not-found response may lead to `gh repo create OWNER/NAME` using the configured visibility. Query again after creation, then run `git ls-remote --exit-code ACTUAL_URL`. Authentication/organization policy failure updates that row to `BLOCKED` and stops all push/submodule work.

```bash
uv run python -m scripts.repositories.preflight --json
uv run python -m scripts.repositories.remotes --manifest config/repositories/services.json --report docs/reports/2026-08-15-independent-service-extraction-report.json
uv run pytest scripts/repositories/tests/test_remotes.py -q
```

Expected: one verified existing remote plus ten created-and-reverified remotes; no URL is manually synthesized.

- [ ] **Step 3: Independent review and commit**

Reviewer compares every receipt to live `gh repo view`/`git ls-remote`, then changes only the remote gate to `APPROVE`.

```bash
git add config/repositories/services.json scripts/repositories/remotes.py scripts/repositories/tests/test_remotes.py docs/reports/2026-08-15-independent-service-extraction-report.json
git commit -m "chore(repository): approve independent remote inventory"
```

### Task 3: Reproducible Independent Snapshot Extraction

**Files:**
- Create: `scripts/repositories/extract.py`
- Create: `scripts/repositories/tests/test_extract.py`
- Create in each target: `docs/provenance/extraction.json`

**Interfaces:**
- Consumes: approved remote receipts, exact committed source SHA and an explicit tracked-path closure.
- Produces: `extract_repository(spec: ExtractionSpec) -> ExtractionReceipt`; the receipt binds source repository/SHA/tree, included paths, excluded generated/cache paths, initial target commit/tree and actual remote URL.

- [ ] **Step 1: Write extraction RED tests**

Reject dirty sources, a missing reviewed source commit/object, shared target `git-common-dir`, Platform/Session/Web origin after extraction, tracked `node_modules/dist/tmp/cache`, path escape, missing workspace dependency, and source-tree digest drift. A reviewed local candidate commit is allowed as an extraction input; only the pushed target receipt may claim remote durability.

```bash
uv run pytest scripts/repositories/tests/test_extract.py -q
```

Expected: RED because the extractor is absent.

- [ ] **Step 2: Extract each reviewed committed tree into its real remote**

For Site/IAM/Model/Capability/Chat, preserve the already-filtered candidate branch history and push only its reachable commits after proving the tree contains no aggregate-repository paths. Agent advances its existing independent remote from the reviewed candidate history. Storage/Entitlement/Payment and User/Admin are extracted in fresh temporary clones with `git-filter-repo` using an explicit path and workspace-dependency closure; the rewritten history is recorded in `docs/provenance/extraction.json` before push. No orphan snapshot, `git archive` flattening or inferred directory-name closure is accepted.

```bash
uv run python -m scripts.repositories.extract --manifest config/repositories/services.json --report docs/reports/2026-08-15-independent-service-extraction-report.json
uv run pytest scripts/repositories/tests/test_extract.py -q
```

Expected: eleven push receipts, or a fail-closed report with no claimed extraction.

- [ ] **Step 3: Prove independence from fresh clones**

For each actual URL, clone with `git clone --no-local`, assert `.git` is its own common dir, origin equals the receipt URL, HEAD/tree equal the receipt, excluded aggregate paths are absent, and the reachable history matches the extraction receipt. The test must prove history was retained, not require an orphan initial commit.

```bash
uv run python -m scripts.repositories.extract --verify-clones --manifest config/repositories/services.json --report docs/reports/2026-08-15-independent-service-extraction-report.json
```

Expected: GREEN for all repositories. A root-shaped candidate alone remains non-promotable.

### Task 4: Repository-Owned Configuration And Implementation Plans

**Files (in every independent repository):**
- Create: `.env.example`, `config/environment.schema.json`, `scripts/bootstrap-env`, `.github/workflows/ci.yml`, `tests/catalog.json`
- Create: the exact plan/report paths in the File Ownership table above
- Create in Root: `config/repositories/environment-mapping.json`, `scripts/repositories/bootstrap_env.py`, `scripts/repositories/tests/test_bootstrap_env.py`

**Interfaces:**
- Consumes: Root operator keys and each repository's schema entries `{name,type,required,sensitive,ci,purpose}`.
- Produces: `sync_environment(config, service_manifest) -> EnvironmentReceipt`; only explicitly mapped names reach the child ignored `.env` or `gh secret/variable set`.

- [ ] **Step 1: Write allowlist RED tests**

Reject undeclared variables, a sensitive value sent with `gh variable set`, schema/name mismatch, writing a child `.env` outside its clone, printing values, or any service code reference to Root `.env`/`KOKORO_REPOSITORY_PARENT`.

```bash
uv run pytest scripts/repositories/tests/test_bootstrap_env.py -q
```

Expected: RED before bootstrap exists.

- [ ] **Step 2: Freeze each repository's own plan and report skeleton**

Every repo-local plan uses writing-plans, contains its exact provider Proto/database/test/CI/dev work, and starts all catalog/report cases at `NOT_STARTED`. Root records only plan/report commit and SHA-256; it does not copy their contents into Root.

```bash
git -C "$KOKORO_REPOSITORY_PARENT/kokoro-site" grep -q 'NOT_STARTED' docs/reports/site-acceptance-report.json
git -C "$KOKORO_REPOSITORY_PARENT/kokoro-chat" grep -q 'NOT_STARTED' docs/reports/chat-acceptance-report.json
```

`bootstrap_env.py --check-plans` iterates the eleven exact plan/report paths frozen in `services.json`; any absent file, non-`NOT_STARTED` initial result or hash mismatch blocks only that repository.

- [ ] **Step 3: Implement schema-driven environment sync**

Root loads each committed schema, intersects it with `environment-mapping.json`, writes mode `0600` child `.env`, and configures only schema rows with `ci=true` through `gh secret set` or `gh variable set`. Child bootstrap reads only its local standard names.

```bash
uv run python -m scripts.repositories.bootstrap_env --manifest config/repositories/services.json --mapping config/repositories/environment-mapping.json
uv run pytest scripts/repositories/tests/test_bootstrap_env.py -q
```

Expected: GREEN receipts list key names and destinations, never values.

### Task 5: Per-Repository Ownership And `APPROVE`

**Files:**
- Modify only inside each service repository according to its repo-local plan.
- Update only that repository's catalog, acceptance report and CI.

**Interfaces:**
- Consumes: Task 4 repo-local plan and local environment schema.
- Produces: clean provider/consumer commit, `scripts/verify`/`pnpm verify`, dev entry, report digest and independent `APPROVE`.

- [ ] **Step 1: Execute each repository plan with strict RED/GREEN**

Providers must prove owned Proto/Buf breaking, independent logical database/migrations/roles, unit/fresh-DB/contract/admin tests, catalog, validator, CI and dev entry. User/Admin prove their generated consumers, CI and dev entry. No Root file is a test input.

- [ ] **Step 2: Verify from a new standalone clone**

```bash
git clone --no-local "$(uv run python -m scripts.repositories.remotes --print-url kokoro-agent)" /private/tmp/kokoro-agent-independent-review
cd /private/tmp/kokoro-agent-independent-review && uv sync --frozen && uv run ruff check . && uv run pyright && uv run pytest
```

For TypeScript repositories the exact clone command ends with `corepack pnpm install --frozen-lockfile && pnpm verify`. Each report records the real command, exit, commit/tree, environment identity and evidence hashes.

- [ ] **Step 3: Independent review each repository**

Review changes that repository alone from `NOT_STARTED` through its phase states to `APPROVE`. One owner approval does not promote another owner or a pair test.

### Task 6: Consumer-Owned Pair Tests And Separate Web E2E

**Files:**
- Create in `kokoro-iam`: `tests/pairs/PAIR-R-SITE-IAM-001/`, `docs/reports/PAIR-R-SITE-IAM-001.json`
- Create in `kokoro-chat`: `tests/pairs/PAIR-R-IAM-CHAT-001/`, `tests/pairs/PAIR-R-STORAGE-CHAT-001/`, `tests/pairs/PAIR-R-AGENT-CHAT-001/` and matching `docs/reports/*.json`
- Create in `kokoro-agent`: `tests/pairs/PAIR-R-MODEL-AGENT-001/`, `tests/pairs/PAIR-R-CAP-AGENT-001/`, `tests/pairs/PAIR-R-STORAGE-AGENT-001/`, `tests/pairs/PAIR-R-ENT-AGENT-001/` and matching `docs/reports/*.json`
- Create in `kokoro-payment`: `tests/pairs/RPC-PC-001/`, `tests/pairs/RPC-PC-002/`, `tests/pairs/RPC-PC-003/`, `tests/pairs/RPC-PC-004/` and matching `docs/reports/*.json`
- Create in `kokoro-web-user`: `tests/pairs/PAIR-R-WEBU-BACKEND-001/`, `docs/reports/PAIR-R-WEBU-BACKEND-001.json`
- Create in `kokoro-web-admin`: `tests/pairs/PAIR-R-WEBA-BACKEND-001/`, `docs/reports/PAIR-R-WEBA-BACKEND-001.json`
- Create in User Web: `tests/e2e/user/`, `docs/reports/user-web-e2e.json`
- Create in Admin Web: `tests/e2e/admin/`, `docs/reports/admin-web-e2e.json`

**Interfaces:**
- Consumes: two owner reports at `APPROVE`, provider descriptor commit/digest, generated client and real dev entries.
- Produces: consumer-local `scripts/verify-pair PAIR_ID` and Web-local `scripts/verify-e2e --run 1|2`.

- [ ] **Step 1: Freeze pair reports as `NOT_STARTED`**

IAM owns Site-IAM; Chat owns IAM-Chat, Storage-Chat and Agent-Chat; Agent owns Model-Agent, Capability-Agent, Storage-Agent and Entitlement-Agent; Payment owns the four Payment-Credit cases; User Web/Admin Web own their separate backend pairs.

- [ ] **Step 2: Record RED before real pair wiring**

```bash
./scripts/verify-pair PAIR-R-IAM-CHAT-001
```

Expected: RED until both independent real processes, databases and pinned generated client are used. Mocks, direct handlers and shared SQL cannot satisfy the command.

- [ ] **Step 3: Approve pairs, then run two fresh browser rounds per Web repo**

```bash
pnpm verify:pair
pnpm verify:e2e -- --run 1
pnpm verify:e2e -- --run 2
```

User Web owns user/billing/replay/tenant/fresh/evidence IDs; Admin Web owns admin/delete-restart/replay/tenant/fresh/evidence IDs. Each repo independently derives parity, receives review, and reaches `APPROVE`.

### Task 7: Atomic Root Gitlink And Release Promotion

**Files:**
- Modify: `.gitmodules`
- Create: `config/repositories/release-manifest.json`, `scripts/repositories/promote.py`, `scripts/repositories/tests/test_promote.py`
- Modify: `docs/reports/2026-08-15-independent-service-extraction-report.json`, `docs/CODEBASE_MAP.md`
- Add gitlinks: all eleven independent repositories
- Remove gitlinks after replacement: `kokoro-platform`, `kokoro-session`, `kokoro-web`

**Interfaces:**
- Consumes: actual remote receipts, eleven owner `APPROVE` reports, all pair/Web `APPROVE` reports and clean remote commits.
- Produces: exact gitlinks and release manifest binding repository URL, commit, tree, provider-contract digest, report revision/hash and verify command.

- [ ] **Step 1: Write promotion RED tests**

Reject local URLs, branch refs, unreachable commits, dirty clones, report states below `APPROVE`, digest drift, missing User/Admin split, old aggregate gitlinks and any Root service authority.

```bash
uv run pytest scripts/repositories/tests/test_promote.py -q
```

Expected: RED before promotion tooling exists.

- [ ] **Step 2: Stage gitlinks mechanically**

`promote.py` uses actual receipt URLs and exact reviewed commits, runs `git submodule add`, checks out detached pins, removes old aggregate gitlinks only after replacements exist, then writes the release manifest. It refuses a dirty Root.

```bash
uv run python -m scripts.repositories.promote --manifest config/repositories/services.json --report docs/reports/2026-08-15-independent-service-extraction-report.json --check
uv run python -m scripts.repositories.promote --manifest config/repositories/services.json --report docs/reports/2026-08-15-independent-service-extraction-report.json --apply
git submodule status
```

Expected: eleven exact reachable independent gitlinks and no Platform/Session/Web aggregate gitlink.

### Task 8: Delete Root Central Service Authority Last

**Files:**
- Delete tracked authority after replacement proof: `contract/`, `database/`, `scripts/contract/`, `scripts/database/`, tracked `scripts/e2e/`, `.github/workflows/contract.yml`
- Gate but do not automatically delete current untracked work under `scripts/slice_a/` and `scripts/tests/`; its owning lanes must first promote every retained file into the correct independent repository and remove the Root copies through a separately reviewed change. This plan never authorizes `git clean`.
- Delete if no remaining Root caller: contract-only entries from `pyproject.toml`, `uv.lock`, `package.json`, `pnpm-lock.yaml`, `pnpm-workspace.yaml`
- Preserve: `scripts/repositories/**`, `.env.example`, gitlinks, release manifest and docs

**Interfaces:**
- Consumes: Task 7 staged topology and release manifest with every required approval.
- Produces: meta-only Root with no service Proto, generated client, DDL, ORM schema, service test or browser test authority.

- [ ] **Step 1: Prove deletion is still RED before promotion**

```bash
test ! -e contract && test ! -e database
```

Expected: RED until every replacement is independently `APPROVE` and pinned.

- [ ] **Step 2: Remove centralized authority and verify ownership**

```bash
git rm -r contract database scripts/contract scripts/database scripts/e2e .github/workflows/contract.yml
git ls-files | rg '^(contract/|database/|scripts/(contract|database|e2e|slice_a|tests)/)' && exit 1 || true
test ! -e scripts/slice_a
test ! -e scripts/tests
git diff --check
```

Remove Root lock/tool manifests only when `git grep` proves repository bootstrap has no dependency on them. Run every pinned repository's public verify command from the release manifest; Root does not re-host their tests.

- [ ] **Step 3: Independent final review and atomic Root commit**

Reviewer verifies fresh `git clone --recurse-submodules` resolves all pins, every URL is the actual independent remote, every report is `APPROVE`, Root `.env` is absent from Git, and no deleted authority remains.

```bash
git add .gitmodules .env.example config/repositories scripts/repositories docs/CODEBASE_MAP.md docs/reports
git add -u
git diff --cached --check
git commit -m "refactor(repository): promote independent service ownership"
```

The final Root report moves from `REPORT_REVIEW` to `APPROVE` only after that clean-clone review. Until then extraction and overall application promotion remain unapproved.
