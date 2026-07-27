# Federated Repository Governance Correction Implementation Plan

repositoryTopology: federated-submodules-v1

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Kokoro a reproducible superproject whose four permanently independent service repositories can be built, deployed, scaled, released, and rolled back independently while interoperating through versioned remote protocols.

**Architecture:** `kokoro-agent`, `kokoro-platform`, `kokoro-session`, and `kokoro-web` retain independent Git histories, locks, CI, artifacts, migrations, releases, deployment, scaling, and rollback. Cross-repository runtime interactions use versioned HTTP/RPC, SSE, or declared asynchronous command/event protocols; no child imports sibling source, shares in-process objects, or reaches through another service's database. Root owns only cross-repository contract sources, root-only tooling, Infra/integration orchestration, compatibility/BOM manifests, exact-pin verification, evidence, and reviewed gitlink promotion.

**Tech Stack:** Git submodules/gitlinks, GitHub Actions, Node.js 22 standard library tests, Python 3.11 with a root-only uv lock, pnpm 11, npm, uv, JSON/YAML contracts.

---

## Promotion protocol

1. A child commit passes its repository-local lock-driven CI.
2. The exact child commit is pushed to a named feature branch without force.
3. A new unique recoverable annotated tag is created only if the remote ref is absent; the peeled remote tag must equal the child commit. A tag is called protected/immutable only when hosted ruleset evidence is recorded; otherwise it is only a recoverable ref.
4. Root stages `.gitmodules`, gitlinks, manifests, generated contracts, and evidence. Proposed-tree verification reads mode-`160000` pins from the Git index, not old `HEAD`.
5. Root atomically commits the candidate combination, verifies it from a clean recursive clone, receives final review, pushes the feature branch, and waits for required root CI.
6. After remote CI is green, root creates and verifies a unique BOM tag pointing to that exact root commit. The BOM manifest maps all four child pins, recoverable refs, contract versions, protocols, and compatibility gates.
7. Rollback is a new Git revert of the root promotion commit, followed by recursive checkout and verification. Child releases remain independently recoverable. No branch or tag is force-updated.

## Chunk 1: Authoritative topology

### Task 1: Rewrite the active authority documents

**Files:**
- Create: `config/repository/authority-documents.json`
- Create: `scripts/repository/federated-governance.test.mjs`
- Modify: `docs/superpowers/specs/2026-07-25-wave-0-repository-contract-foundation-design.md`
- Modify: `docs/superpowers/plans/2026-07-26-wave-0-repository-contract-foundation-implementation-plan.md`
- Modify: `docs/superpowers/specs/2026-07-25-platform-web-session-target-architecture-design.md`
- Modify: `docs/superpowers/plans/2026-07-25-kokoro-production-delivery-program.md`
- Modify: `docs/kokoro-handbook/technical/01-repository-map.md`
- Modify: `docs/kokoro-handbook/decisions/ADR-007-kokoro-platform-submodule.md`
- Modify: `docs/CURRENT.md`
- Modify: `docs/CODEBASE_MAP.md`
- Modify: `README.md`

- [ ] **Step 1: Write the failing semantic governance test.**

  `authority-documents.json` explicitly inventories the current repository-topology authorities. The test requires every inventory member to carry `repositoryTopology: federated-submodules-v1`, requires `docs/CURRENT.md` to reference the canonical spec/plan/ADR, requires settled affirmative invariants, and rejects executable `git rm .gitmodules`, ordinary-tree import tasks, sibling `ref: main` checkout, or child lock/CI deletion. Fixtures prove that valid negations such as “不得删除 `.gitmodules`” pass and that omitting a current authority file fails.

- [ ] **Step 2: Run RED.**

  Run: `node --test scripts/repository/federated-governance.test.mjs`
  Expected: FAIL with the current contradictory authority documents.

- [ ] **Step 3: Rewrite—not banner—the active documents.**

  Required invariants:
  - `.gitmodules` plus exactly four mode-`160000` gitlinks are permanent;
  - independent repository boundaries exist for independent build/deploy/scale/release/rollback;
  - child repositories own their source, lock, CI, artifacts, migrations, release, and rollback;
  - root owns cross-repository contracts, root-only tooling, Infra/integration, compatibility/BOM manifests, exact pins, and promotion evidence;
  - Web→Session uses HTTP/SSE; Session↔Platform uses versioned internal HTTP/RPC; Session→Agent execution uses the declared asynchronous request/event transport; Agent→model gateway uses versioned HTTP; no cross-repository direct database access;
  - generated contract mirrors are committed consumer artifacts, not runtime filesystem coupling;
  - repository and deployment boundaries are related but not identical: a Platform module does not become a new Git repository merely because it can later deploy separately.

- [ ] **Step 4: Run GREEN and commit root documentation.**

  Run: `node --test scripts/repository/federated-governance.test.mjs && git diff --check`
  Expected: PASS and exit 0.

  Commit: `docs(architecture): make federated repositories authoritative`

## Chunk 2: Child lifecycle ownership

### Task 2A: Complete Agent repository CI without changing GA runtime

**Worktree:** `/Users/nako/.config/superpowers/worktrees/Kokoro/subrepos/kokoro-agent-wave1-ci`

**Files:**
- Create: `tests/repository/test_ci_workflow.py`
- Modify: `.github/workflows/ci.yml`

- [ ] Write a test requiring checkout, locked uv install, ruff, pyright, pytest, Redis, and Mongo services.
- [ ] Run RED: `uv run pytest tests/repository/test_ci_workflow.py -q`; expected failure is missing Mongo.
- [ ] Add only the missing CI service/configuration; do not touch Agent runtime or architecture.
- [ ] Run GREEN: `uv run pytest tests/repository/test_ci_workflow.py -q`.
- [ ] Run local gates: `uv run ruff check src tests && uv run pyright && uv run pytest -q`.
- [ ] Commit: `ci: provide complete runtime dependencies`.

### Task 2B: Establish Platform repository CI

**Worktree:** `/Users/nako/.config/superpowers/worktrees/Kokoro/subrepos/kokoro-platform-wave1`

**Files:**
- Create: `test/repository/ci-workflow.test.mjs`
- Create: `.github/workflows/ci.yml`

- [ ] Write a test requiring Node 22, Corepack with the repository's declared pnpm version, `pnpm install --frozen-lockfile`, lint/typecheck/unit gates, and a separately named child-local integration job.
- [ ] Run RED: `node --test test/repository/ci-workflow.test.mjs`; expected failure is missing workflow.
- [ ] Add CI. The unit job owns lint/typecheck/unit. The child-local integration job provisions only Platform's declared MySQL/Redis/Mongo/MinIO test dependencies and runs `pnpm test:integration`; it does not orchestrate Session/Agent/Web.
- [ ] Run GREEN: `node --test test/repository/ci-workflow.test.mjs`.
- [ ] Run local gates: `pnpm lint && pnpm typecheck && pnpm test`. Run `pnpm test:integration` only against a leased root Infra scope; failure or unavailable required dependency is reported, never silently skipped.
- [ ] Commit: `ci: establish independent platform gates`.

### Task 2C: Repair Web repository CI around its pnpm lock

**Worktree:** `/Users/nako/.config/superpowers/worktrees/Kokoro/subrepos/kokoro-web-wave1`

**Files:**
- Create: `test/repository/ci-workflow.test.mjs`
- Modify: `.github/workflows/ci.yml`
- Modify: `package.json`

- [ ] Write a test requiring a pinned `packageManager`, Node 22, Corepack/pnpm cache, frozen pnpm install, typecheck/lint/test/build, and forbidding `npm ci`.
- [ ] Run RED: `node --test test/repository/ci-workflow.test.mjs`; expected failure is npm-based workflow and missing `packageManager`.
- [ ] Apply the minimal workflow/package metadata correction.
- [ ] Run GREEN: `node --test test/repository/ci-workflow.test.mjs`.
- [ ] Run local gates: `pnpm -r lint && pnpm -r typecheck && pnpm -r test && pnpm --filter @kokoro/web-user build`.
- [ ] Commit: `ci: use the repository pnpm lock`.

### Task 2D: Certify the unchanged Session repository CI

**Worktree:** `/Users/nako/.config/superpowers/worktrees/Kokoro/subrepos/kokoro-session-wave1`

**Files:**
- Create only if an invariant is currently untested: `test/repository/ci-workflow.test.mjs`
- Otherwise record the no-change audit in the root federated manifest/evidence.

- [ ] Verify its workflow uses Node 22, npm cache, `npm ci`, typecheck, lint, tests, Redis, and Mongo, matching its tracked `package-lock.json`.
- [ ] Run: `npm ci && npm run typecheck && npm run lint && npm test`.
- [ ] If no code change is necessary, do not create a cosmetic commit; record the verified existing commit as the Session candidate pin.

### Task 2E: Review and publish child candidates

- [ ] Run independent spec-compliance review for Tasks 2A–2D, followed by code-quality/security review.
- [ ] Confirm each child worktree is clean and each `origin` equals its `.gitmodules` URL without printing credentials.
- [ ] Push only named feature branches, without force: `git push -u origin <branch>`.
- [ ] Allocate one new unique tag per changed child, e.g. `kokoro-wave1-federated-ci-2026-07-27-<repo>`; preflight with `git ls-remote --exit-code origin refs/tags/<tag>` and proceed only when return code is 2 (absent).
- [ ] Create annotated local tags, push each exact tag ref without force, and verify both advertised tag object and peeled `^{}` commit. Record them as `recoverableRef`, not immutable, unless separate hosted ruleset evidence is available.

## Chunk 3: Root exact-pin and compatibility governance

### Task 3A: Add proposed-tree federated manifest verification

**Files:**
- Modify: `.gitmodules` (remove all `branch` keys; allow only name/path/url)
- Create: `config/repository/federated-repositories.json`
- Create: `config/repository/compatibility-matrix.json`
- Create: `scripts/repository/verify-federated-repositories.mjs`
- Create: `scripts/repository/verify-federated-repositories.test.mjs`
- Modify: `scripts/repository/freeze-snapshots.mjs`
- Modify: `scripts/repository/freeze-snapshots.test.mjs`
- Create or modify: `scripts/repository/INDEX.md`

- [ ] Write RED fixtures for exact four-item inventory; strict schema; canonical `.gitmodules` without `branch`/`update`; path/url agreement; mode `160000`; HEAD and `--tree index` pin modes; child tracked-clean state; declared lock/workflow/artifact existence; exact recoverable tag equality including peeled annotated tags; branch refs rejected as recovery refs; changed existing tag rejected; protocol/contract-version declarations; and incompatible matrix combinations rejected.
- [ ] Run RED: `node --test scripts/repository/verify-federated-repositories.test.mjs scripts/repository/freeze-snapshots.test.mjs`.
- [ ] Implement using Node standard library only. Local verification is read-only. `--tree index` reads staged mode-`160000` entries. `--remote` uses `git ls-remote` only to prove exact advertised ref equality and never claims ruleset protection.
- [ ] Extend the freezer with the same proposed-index mode and canonical `.gitmodules` validation. Preserve approved pin/tree digests until the deliberate promotion step.
- [ ] Run GREEN: `node --test scripts/repository/*.test.mjs scripts/foundation/check-evidence.test.mjs`.

### Task 3B: Lock root-only tooling and replace floating root CI

**Files:**
- Create: `pyproject.toml`
- Create: `uv.lock`
- Modify: `.github/workflows/contract.yml`

- [ ] Root tooling lock contains only contract/governance tooling (`PyYAML`, `pytest`) and does not absorb any child dependency or lock.
- [ ] Root CI pins Python 3.11, installs with `uv sync --locked`, checks out `submodules: recursive`, runs exact-pin verification, contract checks, generator tests, and the pinned compatibility gate. It contains no sibling repository checkout and no `--remote` submodule update.
- [ ] Add static tests to `verify-federated-repositories.test.mjs` proving these workflow invariants.
- [ ] Run: `uv sync --locked && uv run python contract/check.py && uv run pytest contract/tests -q`.

### Task 3C: Add a deterministic pinned-combination runtime gate

**Files:**
- Create: `scripts/repository/run-pinned-compatibility.mjs`
- Create: `scripts/repository/run-pinned-compatibility.test.mjs`
- Modify: `scripts/e2e-v21-gate.py` only where it bypasses root Infra authority or assumes old container names.
- Modify: `config/repository/compatibility-matrix.json`

- [ ] Write RED tests proving the runner rejects a child HEAD not equal to the selected HEAD/index pins, contract/API version mismatch, missing required service, skipped required scenario, and evidence without all four repository SHAs.
- [ ] The runner invokes exact commands, captures exit codes, and writes sanitized JSON evidence under ignored `tmp/`; it never reads or prints secrets.
- [ ] Root-owned integration sequence:

  ```bash
  node scripts/infra/manager.mjs ensure --profiles full --scope ci-federated --mode ci --infra-env-file deploy/.env.dev
  node scripts/repository/run-pinned-compatibility.mjs --matrix config/repository/compatibility-matrix.json --tree index --evidence tmp/federated-compatibility.json
  node scripts/infra/manager.mjs stop --profiles full --scope ci-federated --mode ci --infra-env-file deploy/.env.dev
  ```

  The runner executes the deterministic LocalFake cross-service scenarios from `scripts/e2e-v21-gate.py`; required scenarios cannot be reported as SKIP. Cleanup runs in a `finally` path. The command never invokes a child compose file.

- [ ] Run unit GREEN first, then the real root-owned integration sequence. If required local Infra cannot be started, the gate remains incomplete rather than being described as passing.

### Task 3D: Commit the proposed root combination

- [ ] Checkout the reviewed child candidate commits in root submodules and stage `.gitmodules`, four gitlinks, manifests, contract mirrors, and evidence.
- [ ] Run `node scripts/repository/verify-federated-repositories.mjs --tree index --remote` and the freezer in `--tree index` mode.
- [ ] Commit the atomic candidate: `build(repository): promote verified federated pins`.
- [ ] Run HEAD-mode verification immediately after the commit.

## Chunk 4: Final review, clean clone, remote CI, BOM, rollback

### Task 4: Prove and publish the root BOM

- [ ] Run fresh independent spec-compliance and code-quality/security review over the final root range, including gitlinks, manifests, evidence, workflows, and documents; fix and re-review all Critical/Important findings.
- [ ] Create a temporary clone safely:

  ```bash
  CLONE_DIR=$(mktemp -d)
  git clone --no-local --recurse-submodules /Users/nako/.config/superpowers/worktrees/Kokoro/feat/lordfoxfairy/wave-0-foundation "$CLONE_DIR/Kokoro"
  git -C "$CLONE_DIR/Kokoro" submodule status --recursive
  node "$CLONE_DIR/Kokoro/scripts/repository/verify-federated-repositories.mjs" --tree head --remote
  ```

  Remove only the validated temporary clone directory after checks complete.

- [ ] In the clean clone run root governance/contract tests, all four child repository-local gates, and the deterministic root compatibility gate through root Infra authority.
- [ ] Push only `feat/lordfoxfairy/wave-0-foundation` without force. Verify the remote branch SHA equals local HEAD. Use GitHub required-check evidence (`gh run list`/`gh run watch` for that SHA when available); absence of remote CI evidence is incomplete, not green.
- [ ] Create `config/repository/bom.json` before the final commit if not already generated. It must map root commit candidate, all four exact pins, recoverable refs, protocols, contract versions, and evidence digests. Commit and rerun final review/CI if BOM content changes the root commit.
- [ ] Allocate a unique root BOM tag only after the final reviewed root commit and remote CI are green. Preflight absence, create annotated tag, push without force, and verify advertised plus peeled SHA equality. Never replace an existing tag.
- [ ] Exercise rollback in a second `mktemp -d` clone by creating a new revert commit of the promotion commit, initializing its restored submodules, and running HEAD-mode verifier/contract checks. Do not push the rollback rehearsal.
- [ ] Record exact commands, SHAs, refs, CI URLs/results, compatibility evidence digest, and rollback rehearsal in `docs/reports/evidence/wave-0/federated-repository-baseline.md`; do not record private paths or secrets.
- [ ] Completion requires: clean worktrees; four recoverable child pins; four valid independent CI definitions; exact root pin CI; pinned-combination runtime evidence; reviewed root commit; remote root CI evidence; verified BOM tag; and successful rollback rehearsal.
